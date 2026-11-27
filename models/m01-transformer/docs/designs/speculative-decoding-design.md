# Design: Speculative Decoding for M0.1

## Technical Approach

Add a draft-verify speculative decode loop that proposes K tokens via a lightweight 4-layer draft model, verifies all K+1 positions in a single main-model forward pass, and accepts the longest prefix matching the target distribution. This turns K serial memory-bandwidth-bound forward passes into 1 serial + 1 parallel pass, yielding 2-3x speedup with zero quality loss. The draft model shares vocabulary embeddings and output projection with the main TransformerLM, saving ~21M parameters and ensuring logit compatibility for acceptance testing.

## Architecture Decisions

### Decision 1: Draft Model Architecture

| Option | Tradeoff | Decision |
|--------|----------|----------|
| 4-layer, shares embeddings | ~10M params, O(1) weight load, logit-compatible | **Chosen** |
| Separate full model | Doubles memory, no logit compatibility | Rejected |
| 2-layer tiny model | Faster draft but lower acceptance rate | Rejected |
| Distilled draft | Better acceptance but requires training pipeline | Rejected |

Rationale: The 4-layer draft reuses TransformerLM embedding and output_head via weight tying. Draft logits live in the same logit space as main logits. The 4-layer stack is 1/3 the main model depth, giving ~3x faster draft forward passes.

### Decision 2: MLA Cache Rollback Strategy

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Truncation (decrement _seq_len) | O(1), zero data movement, slot overwrite | **Chosen** |
| Copy-before-mutate snapshot | O(K) memory, clean rollback, wastes bandwidth | Rejected |
| Lazy reconstruction | Complex, error-prone, no benefit for MLA | Rejected |

Rationale: MLAKVCache already writes latent/rope tensors at _seq_len offset positions. Truncation simply decrements _seq_len, and subsequent append() calls overwrite the rejected slots. No data movement, no copying.

### Decision 3: Verification Algorithm

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Token-level acceptance (greedy compare) | Simple, deterministic, zero quality loss | **Chosen** |
| Distribution-level (KL divergence) | Softer, higher acceptance, but nondeterministic | Rejected |
| Reject-sampling (standard speculative) | Theoretical optimal, but temperature complicates | Rejected |

Rationale: For greedy decode (temperature=0), compare draft token ID against main model argmax. For sampling (temperature>0), resample from main logits at the first rejection point. Matches spec requirement: output identical to generate() for same prompt and seed.

### Decision 4: Configuration Interface

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Extend M01Config dataclass | Unified config, YAML-compatible, backward-compatible | **Chosen** |
| Separate SpeculativeConfig | Cleaner separation, but two config objects to pass | Rejected |
| Runtime kwargs only | Flexible, but no YAML persistence | Rejected |

### Decision 5: Metrics Collection

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Extend GenerationMetrics | Single metrics object, backward-compatible | **Chosen** |
| Separate SpeculativeMetrics | Clean separation, but two objects to pass | Rejected |

## Architecture Overview

```
speculative_generate() -- src/inference/speculative.py

  DraftModel (4 layers)       TransformerLM (12 layers)     MLAKVCache (per layer)
  - Shares embedding          - Main model                   - .latent
  - Shares output_head        - Forward pass (K+1 tokens)    - .rope
  - Own: 4 blocks, 1 norm                                 - ._seq_len
                                                          - .truncate()

  GenerationMetrics
  - .accepted_tokens, .draft_tokens, .acceptance_rate
```

## Data Flow

```
Prompt (str) -> encode() -> prompt_ids
    |
    v
Build MLA caches (main: n_layers, draft: 4)
Prefill both models
    |
    v
+-- Speculative Decode Loop -----------------------------------------+
|                                                                    |
|  [1] DRAFT PHASE (K serial forward passes, ~3x faster)            |
|      draft_model(token, draft_caches) -> draft_logits              |
|      sample(draft_logits) -> draft_token                           |
|      repeat K times -> draft_tokens[0..K-1]                        |
|                                                                    |
|  [2] VERIFY PHASE (1 parallel forward pass)                        |
|      main_model(draft_tokens, main_caches) -> main_logits          |
|      Shape: (1, K+1, vocab_size)                                  |
|                                                                    |
|  [3] ACCEPTANCE (token-by-token)                                   |
|      for i in 0..K:                                               |
|        if draft[i] == argmax(main[i]): accept draft[i]            |
|        else: resample from main[i], truncate by (K-i), break     |
|      if all accepted: sample from main[K] as bonus                 |
|                                                                    |
|  [4] CACHE UPDATE                                                  |
|      Accepted: cache.append()   Rejected: cache.truncate(n)       |
|                                                                    |
|  [5] METRICS: accepted_tokens += n_accepted, draft_tokens += K    |
+--------------------------------------------------------------------+
    |
    v
decode(generated) -> output str
```

## Algorithm Pseudocode

```python
def speculative_generate(
    model, draft_model, tokenizer, prompt, max_gen_len,
    K=4, temperature=1.0, top_k=None, top_p=None,
    device=None, metrics=None,
):
    prompt_ids = tokenizer.encode(prompt)
    main_caches = [build_attention_cache(config, device, dtype)
                   for _ in range(n_layers)]
    draft_caches = [build_attention_cache(draft_config, device, dtype)
                    for _ in range(4)]

    # Prefill both models
    model(torch.tensor([prompt_ids]), main_caches)
    draft_model(torch.tensor([prompt_ids]), draft_caches)

    generated = list(prompt_ids)
    current_id = prompt_ids[-1]

    while len(generated) < prompt_len + max_gen_len:
        # Draft: K serial forward passes
        draft_tokens = []
        for _ in range(K):
            x = torch.tensor([[current_id]])
            logits = draft_model(x, draft_caches)
            next_id = sample(logits[0, -1], temperature, top_k, top_p)
            draft_tokens.append(next_id)
            current_id = next_id

        # Verify: 1 parallel forward pass on K+1 positions
        verify_input = torch.tensor([[generated[-1]] + draft_tokens])
        main_logits = model(verify_input, main_caches)

        # Accept/reject
        n_accepted = 0
        for i in range(K):
            main_next = (main_logits[0, i].argmax().item()
                         if temperature == 0
                         else sample(main_logits[0, i], temperature, top_k, top_p))
            if main_next == draft_tokens[i]:
                n_accepted += 1
                generated.append(draft_tokens[i])
            else:
                resampled = sample(main_logits[0, i], temperature, top_k, top_p)
                generated.append(resampled)
                for cache in draft_caches:
                    cache.truncate(K - i)
                break
        else:
            extra = sample(main_logits[0, K], temperature, top_k, top_p)
            generated.append(extra)

        current_id = generated[-1]
        if current_id == eos_id:
            break
        if metrics:
            metrics.accepted_tokens += n_accepted
            metrics.draft_tokens += K

    return tokenizer.decode(generated)
```

## MLA Cache Truncation

Add truncate(n) to MLAKVCache:

```python
def truncate(self, n: int) -> None:
    """Roll back n tokens. O(1) -- no data movement."""
    if n < 0:
        raise ValueError("Cannot truncate negative tokens")
    if self._seq_len - n < 0:
        raise ValueError(f"Cannot truncate {n} tokens from {self._seq_len}")
    self._seq_len -= n
```

Boundary cases: truncate(0) is no-op, truncate(seq_len) empties cache, truncate(seq_len+1) raises ValueError.

## Memory Layout

Per-token MLA cache cost: ~1.1 KB per token per layer (latent 512B + rope 640B).
Draft model weights: ~40 MB (4 layers, shared embeddings).
Main model weights: ~400 MB (12 layers).
Total during speculative decode: ~440 MB weights + ~17.6 KB/token caches.

## Performance

Speedup = 3K / (K + 3) at 100% acceptance. K=4: 1.71x, K=6: 2.0x, K=8: 2.18x.
With alpha=0.8 acceptance: K=4 yields 1.37x effective speedup.
Bottlenecks: draft forward pass (memory-bandwidth-bound), verification overhead (K+1 attention), device synchronization.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| src/inference/speculative.py | Create | DraftModel, SpeculativeDecoder, speculative_generate() |
| src/transformer/kv_cache.py | Modify | Add truncate() to MLAKVCache, KVCache, HybridKVCache |
| src/transformer/config.py | Modify | Add draft_model_path, speculation_depth, draft_acceptance_threshold |
| src/inference/generate.py | Modify | Delegate to speculative_generate() when draft_model provided |
| tests/test_speculative.py | Create | Unit tests for DraftModel, cache truncation, decode loop |

## Interfaces

DraftModel: forward(token_ids, kv_caches) -> logits. load(draft_path, main_model) -> DraftModel.
SpeculativeDecoder: generate(tokenizer, prompt, max_gen_len, ...) -> str.
MLAKVCache.truncate(n: int) -> None.
GenerationMetrics: new fields accepted_tokens, draft_tokens, computed acceptance_rate.
M01Config: new fields draft_model_path (str|None), speculation_depth (int=4), draft_acceptance_threshold (float=0.8).

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | DraftModel loads and runs | Create mini model, verify logits shape |
| Unit | Weight sharing | Assert embedding.weight is same tensor |
| Unit | MLAKVCache.truncate() | Test truncate(0), truncate(N), truncate(N+1) raises |
| Unit | acceptance_rate property | Verify with mock data |
| Unit | M01Config defaults | Assert defaults match spec |
| Integration | Output matches generate() | Same seed, assert identical output |
| Integration | All tokens accepted | Mock main to always match draft |
| Integration | Partial rejection | Mock main to mismatch at position 2 |
| Integration | Fallback when draft_model=None | Assert delegates to generate() |
| E2E | Real model speculative decode | Load checkpoints, verify speedup |
| E2E | Metrics populated | Run decode, verify metrics fields |

## Migration / Rollout

No migration required. Purely additive change: new files, optional config fields with defaults, existing generate() unchanged.

## Open Questions

- Draft model checkpoint format: full TransformerLM state_dict with 4 layers, or custom format?
- Should DraftModel be a separate class or a factory function on TransformerLM?
- Early exit strategy: if acceptance_rate drops below draft_acceptance_threshold, should we disable speculation for remaining tokens?
