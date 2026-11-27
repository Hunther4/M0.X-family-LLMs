"""LossPipeline: Composable, Model-Agnostic Loss Pipeline."""

from typing import Dict, List, Any, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F


class BaseLoss(nn.Module):
    """Base interface for individual loss terms."""

    def __init__(self, name: str, weight: float = 1.0) -> None:
        super().__init__()
        self.name = name
        self.weight = weight

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        raise NotImplementedError


class CrossEntropyLossTerm(BaseLoss):
    """Standard Causal Cross-Entropy Loss."""

    def __init__(self, vocab_size: int, weight: float = 1.0, ignore_index: int = 0) -> None:
        super().__init__("CrossEntropy", weight)
        self.vocab_size = vocab_size
        self.ignore_index = ignore_index

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        shift_logits = logits.view(-1, self.vocab_size)
        shift_targets = targets.view(-1)
        return F.cross_entropy(shift_logits, shift_targets, ignore_index=self.ignore_index)


class FusedChunkedCrossEntropyLossTerm(BaseLoss):
    """Fused Chunked Cross-Entropy Loss Term.

    Consumes model hidden states and tied embedding weights, projecting in chunks
    to compute cross-entropy loss with online LogSumExp without materializing
    full-vocabulary logits in VRAM.
    """

    def __init__(
        self,
        weight: float = 1.0,
        ignore_index: int = -100,
        chunk_size: int = 2048,
        embedding_weight: Optional[torch.Tensor] = None,
    ) -> None:
        super().__init__("FusedChunkedCrossEntropy", weight)
        self.ignore_index = ignore_index
        self.chunk_size = chunk_size
        self.embedding_weight = embedding_weight

    def forward(
        self,
        hidden_states_or_logits: torch.Tensor,
        targets: torch.Tensor,
        model: Optional[nn.Module] = None,
    ) -> torch.Tensor:
        W = self.embedding_weight
        if W is None and model is not None:
            if hasattr(model, "get_embedding_weight"):
                W = model.get_embedding_weight()
            elif hasattr(model, "embedding_weight"):
                W = model.embedding_weight
            elif hasattr(model, "embedding"):
                if hasattr(model.embedding, "embedding") and hasattr(model.embedding.embedding, "weight"):
                    W = model.embedding.embedding.weight
                elif hasattr(model.embedding, "weight"):
                    W = model.embedding.weight
            elif hasattr(model, "get_input_embeddings"):
                W = model.get_input_embeddings().weight
            elif hasattr(model, "output_head") and hasattr(model.output_head, "weight"):
                W = model.output_head.weight

        if W is None:
            return F.cross_entropy(
                hidden_states_or_logits.view(-1, hidden_states_or_logits.shape[-1]),
                targets.view(-1),
                ignore_index=self.ignore_index,
            )

        if hidden_states_or_logits.shape[-1] == W.shape[0] and hidden_states_or_logits.shape[-1] != W.shape[1]:
            return F.cross_entropy(
                hidden_states_or_logits.view(-1, W.shape[0]),
                targets.view(-1),
                ignore_index=self.ignore_index,
            )

        from src.transformer.fused_cross_entropy import fused_chunked_cross_entropy
        return fused_chunked_cross_entropy(
            hidden_states=hidden_states_or_logits,
            weight=W,
            targets=targets,
            ignore_index=self.ignore_index,
            chunk_size=self.chunk_size,
        )


class RouterAuxLossTerm(BaseLoss):
    """Router Auxiliary Load Balancing Loss."""

    def __init__(self, weight: float = 1.0) -> None:
        super().__init__("RouterAuxLoss", weight)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        if model is not None and hasattr(model, "get_aux_loss"):
            return model.get_aux_loss()
        return torch.tensor(0.0, device=targets.device)


class RouterZLossTerm(BaseLoss):
    """DeepSeek Router Z-Loss penalizing large gate logits."""

    def __init__(self, weight: float = 0.001) -> None:
        super().__init__("RouterZLoss", weight)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        if model is not None and hasattr(model, "get_z_loss"):
            return model.get_z_loss()
        return torch.tensor(0.0, device=targets.device)


class LabelSmoothingTerm(BaseLoss):
    """Label Smoothing Cross Entropy Loss."""

    def __init__(self, vocab_size: int, smoothing: float = 0.1, weight: float = 1.0) -> None:
        super().__init__("LabelSmoothing", weight)
        self.vocab_size = vocab_size
        self.smoothing = smoothing

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        shift_logits = logits.view(-1, self.vocab_size)
        shift_targets = targets.view(-1)
        return F.cross_entropy(shift_logits, shift_targets, label_smoothing=self.smoothing)


class LossPipeline(nn.Module):
    """Composable Loss Manager that aggregates multiple weighted loss terms dynamically."""

    def __init__(self, terms: Optional[List[BaseLoss]] = None) -> None:
        super().__init__()
        self.terms = nn.ModuleList(terms or [])
        self.last_breakdown: Dict[str, float] = {}

    def register(self, loss_term: BaseLoss) -> None:
        """Dynamically register a new loss term into the pipeline."""
        self.terms.append(loss_term)

    def forward(self, logits: torch.Tensor, targets: torch.Tensor, model: Optional[nn.Module] = None) -> torch.Tensor:
        total_loss = torch.tensor(0.0, device=targets.device)
        self.last_breakdown.clear()

        for term in self.terms:
            val = term(logits, targets, model=model)
            weighted_val = val * term.weight
            total_loss = total_loss + weighted_val
            self.last_breakdown[term.name] = weighted_val.item()

        self.last_breakdown["Total"] = total_loss.item()
        return total_loss
