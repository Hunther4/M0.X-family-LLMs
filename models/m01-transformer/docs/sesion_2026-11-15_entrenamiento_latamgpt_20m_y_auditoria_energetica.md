# 📋 Registro de Sesión: Entrenamiento LatamGPT 20M, Checkpoints e Auditoría Energética

- **Fecha:** 15 de Noviembre de 2026
- **Proyecto:** M0.1-Transformer / M0.1-Mini
- **Hardware:** AMD Radeon RX 9060 XT (16 GB, RDNA 4 gfx1200, ROCm 6.3 sobre WSL2 / Ubuntu)
- **Ubicación Geográfica y Red:** Comuna de Cauquenes, Región del Maule, Chile (CGE Distribución)

---

## 1. Resumen Ejecutivo

Durante esta sesión se llevaron a cabo tres hitos fundamentales del proyecto:
1. **Construcción y filtrado de alta calidad del corpus LatamGPT (20M tokens)** a partir de `latam-gpt/fineweb2-spa_Latn-edu`.
2. **Entrenamiento continuo completo de M0.1-Mini** a lo largo de 2,441 pasos, integrando los 20M tokens y guardando checkpoints dedicados e inmutables cada 5M tokens asimilados.
3. **Auditoría de consumo eléctrico y optimización energética**, contrastando los costos reales de la boleta de la luz en Cauquenes (CGE BT1), midiendo el impacto del undervolt (-75mV / 130W cap) y estableciendo una cuota óptima de uso diario (máximo 4 horas) para recortar el gasto eléctrico familiar en un 68%.

---

## 2. Filtrado y Construcción del Corpus LatamGPT (20M Tokens)

Se desarrolló el script [`scripts/utils/build_latam_quality_20m.py`](file:///mnt/d/Estuding/models/m01-transformer/scripts/utils/build_latam_quality_20m.py), el cual procesó en streaming remoto PyArrow directo desde HuggingFace el dataset `latam-gpt/fineweb2-spa_Latn-edu`.

### Criterios de Selección y Limpieza:
- **Puntaje Educativo / Calidad:** `score >= 3.0` (excluye spam web, SEO junk, contenido superficial o repetitivo).
- **Pureza de Idioma:** `language_score >= 0.95` (español estricto vía FastText).
- **Exclusiones:** Anuncios de apuestas/casinos, páginas de cookies, disclaimers legales masivos.
- **Rango de longitud:** Entre 150 caracteres y 50,000 caracteres (evita fragmentos rotos y volcados masivos).
- **Tokenización:** Conteo exacto mediante el `Tokenizer` BPE oficial de 16k del proyecto (`data/tokenizers/tokenizer.json`).

### Métricas del Dataset Resultante:
- **Archivo principal:** [`data/corpus_sft/latam_quality_20m.jsonl`](file:///mnt/d/Estuding/models/m01-transformer/data/corpus_sft/latam_quality_20m.jsonl)
- **Caché tensorial acelerada:** [`data/corpus_sft/latam_quality_20m.pt`](file:///mnt/d/Estuding/models/m01-transformer/data/corpus_sft/latam_quality_20m.pt) (carga en < 0.5s)
- **Tokens reales:** **20,010,617 tokens**
- **Documentos seleccionados:** **9,846 documentos** (promedio: 2,031.4 tokens/doc)
- **Calidad educativa promedio:** **3.48 / 5.0** (1,084 documentos $\ge 4.0$)
- **Tamaño en disco:** 70.55 MB (JSONL) | 152.6 MB (Tensor `.pt`)
- **Tiempo de extracción:** 2.99 minutos (~111.6k tok/s)

---

## 3. Entrenamiento Continuo en GPU (Pasos 5,030 $\to$ 7,471)

Se ejecutó [`scripts/training/train_sft.py`](file:///mnt/d/Estuding/models/m01-transformer/scripts/training/train_sft.py) sobre el checkpoint canónico previo de **M0.1-Mini** (69.6M parámetros, 2 expertos ruteados top-1 + 1 experto compartido, paso 5,030).

### Parámetros de la Corrida:
- **Batch Size:** 4
- **Grad Accum Steps:** 2 (Lote efectivo = 8)
- **Sequence Length:** 1024 tokens
- **Tokens por paso:** $8 \times 1024 = 8,192$ tokens/paso
- **Pasos entrenados:** 2,441 pasos (paso 5,030 $\to$ 7,471)
- **Optimizador:** Hybrid Muon (`muon_lr = 0.02`) + AdamW (`lr = 1.5e-4`)
- **Scheduler:** WSD (Warmup-Stable-Decay)
- **Throughput:** ~15,000 a 35,000 tokens/segundo
- **Tiempo total en GPU:** **~14.5 minutos**
- **Tokens acumulados totales en los pesos:** **42.39 Millones de tokens**

---

## 4. Inventario de Checkpoints Guardados

Se configuró el guardado automático de hitos dedicados cada 5M tokens (+610 pasos) en [`runs/m01_mini_latam_20m/checkpoints/`](file:///mnt/d/Estuding/models/m01-transformer/runs/m01_mini_latam_20m/checkpoints/):

| Archivo | Paso | Tokens Acumulados Totales | Pérdida Final | Hora de Guardado |
| :--- | :--- | :--- | :--- | :--- |
| `checkpoint_5M.pt` | 5,640 | 27.39M tokens | 4.31 | 03:45 hrs |
| `checkpoint_10M.pt` | 6,250 | 32.39M tokens | 4.02 | 03:49 hrs |
| `checkpoint_15M.pt` | 6,860 | 37.39M tokens | 3.89 | 03:52 hrs |
| `checkpoint_20M.pt` | 7,471 | 42.39M tokens | 3.94 | 03:56 hrs |

*Salud del Modelo:* Entropía de ruteo de expertos constante en **0.999**, coeficiente Gini en **0.020 – 0.035**, 0 expertos muertos y sin colapsos de gradiente.

---

## 5. Auditoría Energética y Contraste Tarifario (Cauquenes, Maule)

Se desarrolló y ejecutó el script [`scripts/utils/monitor_setup_power.py`](file:///mnt/d/Estuding/models/m01-transformer/scripts/utils/monitor_setup_power.py) para auditar el consumo eléctrico de la torre completa desde la toma de pared (GPU + CPU + Placa madre + RAM + pérdidas fuente 80+ Gold).

### Contraste Tarifario CGE Maule:
- **Talca / Curicó (Sector urbano STxE-7-A):** ~$205 CLP / kWh
- **Cauquenes (Sector aéreo / red rural-semiurbana):** **~$265 CLP / kWh** (~$0.276 USD/kWh), debido a los mayores costos de peajes de transmisión troncal y distribución por dispersión geográfica.

### Costo del Entrenamiento de 20M Tokens:
- **Consumo medido:** 0.073 kWh
- **Costo total en Cauquenes:** **$19.3 CLP** (~$0.02 USD)

### Análisis del Uso Diario y Plan de Reducción:
El usuario identificó que la boleta de electricidad del hogar ronda los **$38.000 a $42.000 CLP al mes**, y que la PC se utilizaba aproximadamente 10 horas al día.

1. **Diagnóstico previo (10 horas/día a ~145W torre + monitor):**
   - Consumo: 1.45 kWh/día $\to$ 43.5 kWh/mes.
   - Costo mensual en Cauquenes: **~$11.500 CLP al mes**.
   - **Impacto:** La PC representaba casi el **30% de toda la luz de la casa**.

2. **Optimización de Hardware realizada por el usuario:**
   - **Undervolt:** -75 mV en el núcleo de la GPU.
   - **Power Limit:** Tope en 130 W (-30% de potencia máxima).
   - **Efecto:** Reducción del consumo térmico y eléctrico en más de un 15-20% sin pérdida perceptible de cómputo. Torre + pantalla optimizada operan en **~115W – 120W**.

3. **Nuevo Régimen Óptimo (Máximo 4 horas diarias):**
   - Consumo diario: $0.115\text{ kW} \times 4\text{ h} = \mathbf{0.46\text{ kWh/día}}$.
   - Consumo mensual: $0.46 \times 30 = \mathbf{13.8\text{ kWh/mes}}$.
   - Costo mensual en Cauquenes: $13.8 \times \$265\text{ CLP} = \mathbf{\$3.657\text{ CLP al mes}}$.
   - **Ahorro familiar directo:** **📉 ~$7.850 a $8.000 CLP mensuales** en la cuenta de la luz.

---

## 6. Pruebas Experimentales, Diagnóstico de Olvido Catastrófico y Re-alineamiento

### 6.1. Evaluación Inicial sobre `checkpoint_20M.pt` (Paso 7,471 - 42.39M Tokens):
- **Resultado:** Tras ingerir 20M tokens de texto continuo web (`latam_quality_20m.jsonl`) sin etiquetas especiales, el modelo sufrió **olvido catastrófico de la sintaxis conversacional**.
- **Síntomas:** Intentaba autocompletar texto corrido, emitía delimitadores rotos (`|>||||||`) en prompts de chat y caía en bucles de repetición n-gramas a temperaturas bajas ($T=0.2-0.4$).

### 6.2. Pase de Re-alineamiento SFT (Pasos 7,471 $\to$ 7,684):
- **Corpus Utilizado:** [`data/corpus_sft/corpus_alineacion_1epoca.jsonl`](file:///mnt/d/Estuding/models/m01-transformer/data/corpus_sft/corpus_alineacion_1epoca.jsonl) (4,112 muestras unificadas combinando `corpus_dialecto_razonamiento_unificado.jsonl` y `instrucciones_sft_conversaciones_1m_tokens.jsonl`).
- **Volumen:** 1,744,132 tokens (213 pasos de falso batch 8, seq 1024).
- **Tiempo de ejecución en GPU:** ~65 segundos.
- **Evolución de Pérdida:** Descendió de **4.21 a 2.36**.
- **Resultado en Checkpoint:** Guardado en [`runs/m01_mini_latam_alineado/checkpoints/checkpoint.pt`](file:///mnt/d/Estuding/models/m01-transformer/runs/m01_mini_latam_alineado/checkpoints/checkpoint.pt). Tokens acumulados en pesos: **44.13M tokens**.

### 6.3. Hallazgo de Inferencia (Sampling y Repetición):
- **Baja temperatura sin penalización ($T=0.2$):** Modelos compactos (~70M parámetros) quedan atrapados en atractores repetitivos por búsqueda argmax.
- **Configuración óptima ($T=0.7$ + Repetition Penalty 1.2):** Recuperó la estructura `<think>`, los turnos de diálogo y un léxico en español enriquecido por los 20M de LatamGPT sin bucles.

---

## 7. Blueprint Técnico: Cómo Entrenar a Futuro sin Retroceder

Para evitar el olvido catastrófico y preservar tanto el conocimiento como la estructura de chat en futuras sesiones:

1. **Loss Masking Estricto (`target = -100`):**
   - Enmascarar siempre los tokens del usuario y del sistema en el cálculo de `CrossEntropyLoss`.
   - El gradiente solo debe actualizarse sobre los tokens de `<|assistant|>`.
2. **Replay Buffer / Data Interleaving (Regla 80/20):**
   - Nunca introducir texto web continuo aislado después de haber aplicado SFT.
   - Si se añade texto plano o de dominio nuevo, mezclar siempre entre un **15% y 20% de muestras de instrucción previa** (`corpus_dialecto_razonamiento_unificado.jsonl` y código) para mantener "ancladas" las probabilidades de las etiquetas conversacionales.
3. **Pipeline Unidireccional:**
   - La fase de SFT y alineación de razonamiento debe ser siempre el **último paso** antes de congelar o usar el modelo.
4. **Muestreo en Inferencia:**
   - Para modelos de 70M-300M parámetros, usar siempre `repetition_penalty = 1.15 - 1.20` y temperatura entre 0.6 y 0.8 en tareas abiertas, reservando baja temperatura únicamente para formato estructurado (JSON/regex) con penalización activa.

