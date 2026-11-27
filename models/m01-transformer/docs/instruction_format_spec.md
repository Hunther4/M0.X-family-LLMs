# ESPECIFICACIÓN TÉCNICA DE FORMATO DE INSTRUCCIÓN Y ALINEACIÓN SFT EN M0.1

## 1. Problema Actual y Diagnóstico
Durante la inferencia sin formateo explícito, si se envía una entrada en texto plano al modelo (por ejemplo `"¿Quién eres?"`), el modelo tiende a continuar el texto como si fuera un documento plano de Wikipedia o código fuente (ejemplo: `"¿Quién eres? En 1999..."`).

Para resolver esto y lograr que **M0.1 responda como un asistente conversacional directo sin requerir que el usuario escriba `<|user|>` y `<|assistant|>` manualmente en cada prompt**, se establece la presente especificación de alineación para la siguiente fase de entrenamiento SFT.

---

## 2. Definición de Tokens Especiales y Formato Canónico de Diálogo

El tokenizer y el pipeline de datos utilizarán el esquema de plantilla de chat estándar:

- **Token de Usuario:** `<|user|>`
- **Token de Asistente:** `<|assistant|>`
- **Token de Fin de Turno:** `<|endoftext|>` o `\n`

### Estructura Canónica de Muestra SFT:
```text
<|user|>
{pregunta_o_instruccion_del_usuario}
<|assistant|>
{respuesta_analitica_de_M0.1}
```

---

## 3. Integración Automática en la Inferencia (CLI e Interfaz)

El módulo de inferencia (`src/inference/cli.py` y `src/inference/generate.py`) envolverá automáticamente cualquier entrada de texto plano enviada por el usuario antes de tokenizar y pasar al modelo:

### Transformación de Prompt en Inferencia:
```python
def format_chat_prompt(raw_prompt: str) -> str:
    """Envuelve automáticamente el prompt en las etiquetas de diálogo si no las posee."""
    if "<|user|>" not in raw_prompt:
        return f"<|user|>\n{raw_prompt.strip()}\n<|assistant|>\n"
    return raw_prompt
```

Esto garantiza que el usuario solo escriba:
`¿Qué son los principios SOLID?`
Y el motor lo transforme internamente a:
`<|user|>\n¿Qué son los principios SOLID?\n<|assistant|>\n`

---

## 4. Pipeline de Entrenamiento SFT con Loss Masking Puro (Fase 2)

Para fijar este comportamiento de forma nativa en los pesos del modelo:

1. **Máscara de Pérdida en `<|user|>` (`ignore_index = 0` / `-100`):**
   - Durante el cálculo de `CrossEntropyLoss`, **no se calcula pérdida** sobre los tokens del prompt del usuario (`<|user|>\n...`).
   - Únicamente se calcula el gradiente sobre la respuesta generada por el asistente (`<|assistant|>\n...`).

2. **Beneficios de la Máscara de Pérdida:**
   - Evita que el modelo memorice la forma de preguntar del usuario.
   - Maximiza el aprendizaje de la estructura de respuesta, concisión y precisión técnica.
   - El modelo aprende a detenerse al terminar la respuesta sin autocompletar nuevos turnos ficticios.

---

## 5. Plan de Ejecución del Próximo Corpus SFT
1. Compilar el dataset instructivo unificado `data/corpus_sft/corpus_sft_1m.jsonl` con el formato `<|user|>` / `<|assistant|>`.
2. Aplicar la función `format_chat_prompt` en `src/inference/cli.py`.
3. Ejecutar la pasada de alineación con máscara de pérdida pura en la GPU AMD (RX 9060 XT) a `batch_size = 6` (~10.6 GB VRAM).
