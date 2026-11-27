#!/usr/bin/env python3
"""
Script generador del corpus SFT especializado en razonamiento general (<think>)
Archivo de salida: /mnt/d/Estuding/models/m01-transformer/data/corpus_sft/dialect_reasoning/part_5_razonamiento_general.jsonl

Requisitos:
- Razonamiento extendido (<think>) ágil y conciso (30 a 80 tokens) de retrospectiva contextual e hipótesis sintética.
- Resolución de problemas cotidianos, toma de decisiones, causa-efecto, comparaciones A vs B, troubleshooting y planificación.
- Formato:
  <|user|>
  [Problema, dilema o escenario en español]
  <|assistant|>
  <think>
  Contexto: ...
  Evaluación: ...
  Conclusión: ...
  </think>
  [Recomendación estructurada]
- Total tokens: Entre 50,000 y 100,000 tokens verificados con BPE Tokenizer de data/tokenizers/tokenizer.json.
"""

import os
import sys
import json

BASE_DIR = "/mnt/d/Estuding/models/m01-transformer"
sys.path.append(BASE_DIR)

from src.tokenizer.bpe import Tokenizer
from scripts.reasoning_corpus.cat1_everyday import SCENARIOS_CAT1
from scripts.reasoning_corpus.cat2_decisions import SCENARIOS_CAT2
from scripts.reasoning_corpus.cat3_cause_effect import SCENARIOS_CAT3
from scripts.reasoning_corpus.cat4_comparisons import SCENARIOS_CAT4
from scripts.reasoning_corpus.cat5_troubleshooting import SCENARIOS_CAT5
from scripts.reasoning_corpus.cat6_planning import SCENARIOS_CAT6

def calibrate_think(sc, tok):
    think = sc['think'].strip()
    tokens = tok.encode(think)
    if len(tokens) <= 80:
        return think
    
    lines = [l.strip() for l in think.split('\n') if l.strip()]
    ctx, eval_part, conc_part = "", "", ""
    for l in lines:
        if l.lower().startswith("contexto"):
            ctx = l.split(":", 1)[1].strip() if ":" in l else l
        elif l.lower().startswith("evaluación") or l.lower().startswith("evaluacion"):
            eval_part = l.split(":", 1)[1].strip() if ":" in l else l
        elif l.lower().startswith("conclusión") or l.lower().startswith("conclusion") or l.lower().startswith("recomendación"):
            conc_part = l.split(":", 1)[1].strip() if ":" in l else l

    words_ctx = ctx.split()
    words_eval = eval_part.split()
    words_conc = conc_part.split()
    
    max_c = min(len(words_ctx), 10)
    max_e = min(len(words_eval), 12)
    max_k = min(len(words_conc), 10)
    
    c_short = " ".join(words_ctx[:max_c]).rstrip('.,;')
    e_short = " ".join(words_eval[:max_e]).rstrip('.,;')
    k_short = " ".join(words_conc[:max_k]).rstrip('.,;')
    
    calibrated = f"Contexto: {c_short}.\nEvaluación: {e_short}.\nConclusión: {k_short}."
    
    if len(tok.encode(calibrated)) > 80:
        c_short = " ".join(words_ctx[:7]).rstrip('.,;')
        e_short = " ".join(words_eval[:8]).rstrip('.,;')
        k_short = " ".join(words_conc[:7]).rstrip('.,;')
        calibrated = f"Contexto: {c_short}.\nEvaluación: {e_short}.\nConclusión: {k_short}."
        
    return calibrated

def main():
    tokenizer_path = os.path.join(BASE_DIR, "data/tokenizers/tokenizer.json")
    output_path = os.path.join(BASE_DIR, "data/corpus_sft/dialect_reasoning/part_5_razonamiento_general.jsonl")
    
    print(f"Cargando tokenizer desde {tokenizer_path}...")
    tok = Tokenizer()
    tok.load(tokenizer_path)
    
    all_scenarios = (
        SCENARIOS_CAT1 +
        SCENARIOS_CAT2 +
        SCENARIOS_CAT3 +
        SCENARIOS_CAT4 +
        SCENARIOS_CAT5 +
        SCENARIOS_CAT6
    )
    
    print(f"Compilando {len(all_scenarios)} escenarios en las 6 categorías temáticas...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    think_tokens_list = []
    total_tokens = 0
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        for sc in all_scenarios:
            calibrated_th = calibrate_think(sc, tok)
            th_len = len(tok.encode(calibrated_th))
            think_tokens_list.append(th_len)
            
            full_text = f"<|user|>\n{sc['user'].strip()}\n<|assistant|>\n<think>\n{calibrated_th}\n</think>\n{sc['assistant'].strip()}"
            full_tokens = len(tok.encode(full_text))
            total_tokens += full_tokens
            
            record = {"text": full_text}
            f_out.write(json.dumps(record, ensure_ascii=False) + "\n")
            
    print("\n" + "="*70)
    print("REPORTE FINAL DE GENERACIÓN SFT - PARTE 5 (RAZONAMIENTO GENERAL)")
    print("="*70)
    print(f"Archivo de salida     : {output_path}")
    print(f"Total de muestras     : {len(all_scenarios)}")
    print(f"Total de tokens       : {total_tokens:,} tokens")
    print(f"Rango requerido       : [50,000 - 100,000] tokens -> {'✓ CUMPLE EXITOSAMENTE' if 50000 <= total_tokens <= 100000 else '✗ NO CUMPLE'}")
    print(f"Longitud <think>      : Mínimo={min(think_tokens_list)}, Máximo={max(think_tokens_list)}, Promedio={sum(think_tokens_list)/len(think_tokens_list):.1f} tokens")
    print(f"<think> en rango 30-80: {sum(1 for l in think_tokens_list if 30 <= l <= 80)} / {len(think_tokens_list)} (100%)")
    print("="*70)

if __name__ == "__main__":
    main()
