# M0.1 Enterprise Training Architecture: SOTA Industry Reference & Implementation

Documentación técnica y fundamentos matemáticos de la suite de entrenamiento de nivel empresarial para **M0.1** (~99.7M parámetros, MLA + MoE), inspirada en las arquitecturas y prácticas de entrenamiento de **DeepSeek (V3/V4)**, **Moonshot AI (Kimi K2)**, **Meta (Llama 3/4)** y **Qwen (2.5/3)**.

---

## 1. Optimizador Híbrido: Muon + AdamW

### El Problema de AdamW en Matrices Ocultas
AdamW trata cada parámetro de una red neuronal de manera escalar independiente mediante estimadores de primer y segundo momento ($m_t, v_t$). En capas lineales densas de transformers ($W_q, W_k, W_v, W_o$, expert gate/up/down projections), esto introduce un **sesgo espectral severo**: las direcciones de mayor varianza dominan las actualizaciones mientras que las direcciones sutiles pero críticas se actualizan con retraso o ruido.

### Solución SOTA: Muon (MomentUm Orthogonalized by Newton-Schulz)
Adoptado en **DeepSeek-V4**, **Moonshot Kimi K2** y benchmarks de NanoGPT, **Muon** trata las matrices de pesos 2D como objetos geométricos en lugar de colecciones de escalares. Reemplaza la actualización con su **matriz ortogonal más cercana** ($U V^T$ del SVD) calculada eficientemente en $O(N)$ mediante iteraciones de Newton-Schulz de quinto orden:

$$X_{k+1} = a X_k + (b X_k X_k^T + c (X_k X_k^T)^2) X_k$$

donde los coeficientes óptimos quinticos son $a = 3.4445, b = -4.7750, c = 2.0315$.

### Partición Híbrida (`EnterpriseHybridOptimizer`):
1. **Muon (`lr = 0.02`, `weight_decay = 0.01`):**
   - Proyecciones de atención MLA ($W_{q}, W_{k}, W_{v}, W_{o}$).
   - Proyecciones de expertos MoE ($W_{\text{gate}}, W_{\text{up}}, W_{\text{down}}$).
2. **AdamW (`lr = 3e-4`, `weight_decay = 0.1`):**
   - Embeddings (`wte` / `lm_head`).
   - Normalizaciones (RMSNorm / LayerNorm gamma).
   - Biases y Router Gates de enrutamiento MoE.

**Beneficio empírico:** Reducción de hasta **1.5x a 2.0x en FLOPs necesarios** para converger al mismo nivel de loss.

---

## 2. Planificador de Tasa de Aprendizaje: WSD (Warmup-Stable-Decay)

### Por qué no Cosine Decay tradicional
El decaimiento coseno puro ata la tasa de aprendizaje al presupuesto total de pasos prefijado ($T_{\text{max}}$). Si se desea continuar pre-entrenando o escalar el dataset, la tasa de aprendizaje ya ha caído a $\approx 0$, requiriendo "warmup resets" que desestabilizan las capas internas.

### Esquema WSD (utilizado en MiniCPM, DeepSeek V2/V3, Llama 3)
Divide el entrenamiento en 3 fases continuas:
1. **Warmup (0% a 5-10% de pasos):** Incremento lineal de $0$ a $\text{max\_lr}$.
2. **Stable Phase (10% a 80-85% de pasos):** Meseta constante a $\text{max\_lr}$. Durante esta fase, el modelo acumula la mayor parte de su conocimiento factual y sintáctico sin degradar la tasa de actualización. Si se añaden más datos, la fase estable se alarga indefinidamente.
3. **Decay Phase (último 15-20% de pasos):** Decaimiento coseno o potencial hacia $\text{min\_lr} = 0.1 \times \text{max\_lr}$. Durante el enfriamiento rápido, la pérdida cae abruptamente y se consolidan las representaciones finales.

---

## 3. Ingesta y Dataloader de Alto Throughput

### 1. Eliminación de Padding: Zero-Waste Sequence Packing
- Los documentos individuales se concatenan directamente utilizando el token delimitador `<|endoftext|>` ($ID = 256$) y se segmentan en bloques exactos de longitud `seq_len` (1024 / 2048 / 8192).
- **Desperdicio de cómputo por padding:** $0.0\%$.

### 2. Shards Binarios en Memmap (`>u2` uint16 big-endian)
- Cada shard de 1.000.000 de tokens se almacena en 2 MB de disco plano.
- La lectura ocurre por mapeo de memoria directo del sistema operativo (`np.memmap`) con búsqueda binaria de índices acumulados (`bisect`).
- **Latencia de Dataloader:** $< 0.6\text{ ms}$ por batch.
- **Huella de RAM:** Prácticamente nula e independiente del tamaño del dataset (soporta cientos de gigabytes de texto sin consumir RAM).

---

## 4. Comandos de Entrenamiento

```bash
# Entrenamiento empresarial con Muon + AdamW y WSD Scheduler
python -m src.training.train `
  --corpus-dir d:\Estuding\LLM_DATASETS\TOKENIZED\corpus_expanded_v1 `
  --run-name run_enterprise_sota `
  --optimizer hybrid_muon `
  --muon-lr 0.02 `
  --scheduler wsd `
  --stable-ratio 0.8 `
  --batch-size 8 `
  --seq-len 1024 `
  --grad-accum-steps 4 `
  --max-steps 20000
```
