"""Categoría 2: Arquitectura Técnica MoE, MLA, RoPE y Optimización de M0.1."""

def get_samples():
    samples = []

    samples.append({
        "user": "¿Cómo se calculan las dimensiones del vector latente en Multi-head Latent Attention (MLA)?",
        "think": """El usuario solicita la deducción dimensional del vector latente en MLA.
Contexto: Configuración de M0.1 (d_model=640, mla_kv_c_dim=128, rope_dim=16).
Respuesta: Desglose matemático de proyecciones ascendentes y descendentes de KV.""",
        "response": """En M0.1, la atención MLA proyecta la representación oculta $x_t \in \mathbb{R}^{d_{model}}$ ($d_{model} = 640$) a un espacio latente comprimido de claves y valores:

1. Proyección hacia abajo (compresión):
   $$c^{KV}_t = W_{DKV} x_t, \quad W_{DKV} \in \mathbb{R}^{d_{c} \times d_{model}}$$
   donde la dimensión latente comprimida es $d_c = \text{mla\_kv\_c\_dim} = 128$.

2. Desacoplamiento posicional:
   Se extrae de forma paralela un vector para codificación rotatoria (p-RoPE):
   $$k^R_t = \text{RoPE}(W_{KR} x_t), \quad k^R_t \in \mathbb{R}^{d_{R}}, \quad d_{R} = 16$$

3. Almacenamiento en caché:
   Solo se retiene en memoria la concatenación $[c^{KV}_t, k^R_t]$, requiriendo únicamente $128 + 16 = 144$ escalares por token por capa almacenada."""
    })

    samples.append({
        "user": "¿Por qué M0.1 utiliza top-k=1 en lugar de top-k=2 en sus capas MoE?",
        "think": """Pregunta sobre la decisión de enrutamiento top-k=1 en M0.1.
Contexto: Eficiencia en inferencia local compacta (~100M) complementada por 1 experto compartido constante.
Respuesta: Explicar equilibrio entre costo computacional, ancho de banda y rol del experto compartido.""",
        "response": """La selección de `moe_top_k: 1` responde a tres factores de diseño para inferencia local eficiente:

1. Reducción de FLOPs y ancho de banda de memoria:
   Activar un único experto enrutado por token minimiza la cantidad de multiplicaciones de matrices en la capa feed-forward.
2. Complementariedad con el experto compartido:
   Dado que M0.1 incluye un experto compartido permanente (`num_shared_experts: 1`), cada token ya es procesado concurrentemente por dos redes feed-forward (1 compartida + 1 enrutada).
3. Evitar fragmentación de gradientes:
   En un modelo compacto con 4 expertos enrutados, top-1 evita dispersar la masa de probabilidad entre múltiples expertos, fortaleciendo la especialización funcional de cada bloque."""
    })

    samples.append({
        "user": "¿Qué ventaja tiene d_ff_shared=448 frente a d_ff_routed=784 en las capas feed-forward?",
        "think": """Consulta sobre la asimetría dimensional entre experto compartido y enrutado.
Contexto: configs/base.yaml (d_ff_shared=448, d_ff_routed=784).
Respuesta: Justificar la dimensión compacta para sintaxis general y la mayor capacidad para especialización.""",
        "response": """La asimetría entre `d_ff_shared = 448` y `d_ff_routed = 784` optimiza el reparto paramétrico:

- **Experto compartido ($d_{ff} = 448$)**: Procesa información invariante, conectores gramaticales y patrones universales de sintaxis, tareas que requieren menor capacidad dimensional dedicada.
- **Expertos enrutados ($d_{ff} = 784$)**: Poseen mayor capacidad paramétrica (~75% más dimensiones intermedias) para almacenar conocimiento semántico profundo, resolución algorítmica y patrones de código complejos."""
    })

    samples.append({
        "user": "¿Cómo interactúa el clamping de SwiGLU con la estabilidad de los gradientes durante la fase de decay en WSD?",
        "think": """Pregunta técnica sobre la interacción de SwiGLU limit=10.0 con la fase de decay en WSD.
Contexto: Durante el decaimiento acelerado de LR, gradientes inestables pueden inducir colapso o divergencia de pesos.
Respuesta: Explicar cómo la cota superior previene gradientes desproporcionados al reducir el learning rate.""",
        "response": """Durante la fase de decaimiento (Decay) del planificador WSD, la tasa de aprendizaje desciende rápidamente. En esta transición, cualquier activación divergente puede alterar bruscamente los acumuladores de segundo momento del optimizador.

El clamping a 10.0 (`swiglu_limit: 10.0`) asegura que:
1. La salida de la compuerta SwiGLU permanezca acotada en $[-10, 10]$, impidiendo gradientes excesivos hacia las matrices de proyección previa.
2. Las actualizaciones de los pesos se mantengan estables y proporcionales a la tasa de aprendizaje decreciente, consolidando las representaciones sin desajustes abruptos."""
    })

    samples.append({
        "user": "¿Cuál es la función del parámetro initializer_range: 0.02 en base.yaml?",
        "think": """Consulta sobre inicialización de pesos en M0.1.
Contexto: Desviación estándar 0.02 para distribución normal truncada al inicializar proyecciones lineales y embeddings.
Respuesta: Detallar prevención de explosión o anulación de varianza en capas transformadoras profundas.""",
        "response": """El parámetro `initializer_range: 0.02` define la desviación estándar ($\sigma = 0.02$) de la distribución normal truncada con la que se inicializan los pesos de las capas lineales y de incrustación.

Este valor preserva la varianza unitaria de la corriente residual a través de las 12 capas del modelo en el paso inicial de entrenamiento, evitando que las activaciones converjan a cero o diverjan antes de que actúen las normalizaciones RMSNorm."""
    })

    # Bloque de muestras técnicas adicionales de arquitectura
    muestras_arquitectura = [
        ("¿Por qué M0.1 prescinde de sesgos (bias) en la mayoría de sus capas lineales?",
         "Eliminación de vectores bias.",
         "Prescindir de bias reduce el número total de parámetros, optimiza la utilización de núcleos tensoriales en GPU y mejora la estabilidad del entrenamiento al no introducir desplazamientos estáticos en las activaciones previas a RMSNorm."),

        ("¿Cómo se distribuyen los 4 macro-expertos de M0.1?",
         "Especialización funcional de los 4 macro-expertos.",
         "Durante el entrenamiento guiado por datos, los 4 expertos enrutados tienden a especializarse en macro-áreas funcionales: 1) Sintaxis y generación de código, 2) Razonamiento lógico y deductivo, 3) Hechos y conocimiento estructurado, y 4) Búsqueda y grounding contextual."),

        ("¿Qué normalización utiliza M0.1 y por qué no LayerNorm estándar?",
         "RMSNorm vs LayerNorm.",
         "M0.1 utiliza RMSNorm (Root Mean Square Normalization). Al prescindir del cálculo de la media empírica y enfocarse únicamente en la raíz cuadrática media, reduce el costo computacional entre un 10% y 50% por capa de normalización sin afectar la estabilidad del gradiente."),

        ("¿Cómo funciona el mecanismo de atención con cross-layer KV reuse durante la generación autoregresiva?",
         "Decodificación autorregresiva con KV compartido.",
         "En el paso $t$, la capa par $2k$ computa y almacena el estado latente KV en el búfer circular. La capa impar $2k+1$ lee directamente el puntero al búfer de la capa previa sin invocar kernels de proyección descendente de KV, ahorrando accesos a DRAM."),

        ("¿Cuál es la ventaja de la función de activación SiLU dentro de SwiGLU?",
         "Ventaja de SiLU en SwiGLU.",
         "SiLU ($x \cdot \sigma(x)$) es una función diferenciable continua y no monotónica con gradiente suave para entradas negativas, lo que previene el problema de neuronas muertas común en ReLU y facilita un flujo continuo de gradiente en expertos MoE."),

        ("¿Qué relación guarda el factor de rotación parcial 0.25 con la extrapolación de contexto?",
         "Factor p-RoPE 0.25 y longitud de contexto.",
         "Al aplicar rotación solo a 16 de las 64 dimensiones del cabezal, la dispersión angular acumulada en secuencias de hasta 32K tokens afecta a una fracción mínima del espacio representacional, permitiendo retener correlaciones de largo alcance con menor interferencia destructiva."),

        ("¿Cómo opera el balanceador de carga cuando un experto se satura?",
         "Manejo de desbalance en enrutamiento MoE.",
         "La pérdida auxiliar de balanceo penaliza de forma cuadrática la concentración excesiva de masa de enrutamiento en un solo experto, forzando a la red de compuerta a distribuir tokens hacia los expertos alternativos para optimizar la utilización del hardware."),

        ("¿Qué diferencia hay entre el optimizador Muon y Shampoo?",
         "Muon vs Shampoo.",
         "Shampoo mantiene matrices completas de precondicionamiento kroneckeriano para filas y columnas, lo que acarrea alta sobrecarga de cómputo y memoria. Muon reemplaza los precondicionadores pesados por una ortogonalización directa del momentum mediante iteraciones de Newton-Schulz, logrando convergencia similar a una fracción del costo."),

        ("¿Por qué se prefiere un scheduler WSD sobre un decaimiento lineal clásico?",
         "WSD frente a decaimiento lineal.",
         "El decaimiento lineal reduce la tasa de aprendizaje continuamente desde el inicio, limitando la exploración en etapas intermedias. WSD mantiene el ritmo máximo constante en el 80% del proceso, acumulando mayor conocimiento antes de condensar la pérdida en el decaimiento final."),

        ("¿Qué efecto tiene la dimensión mla_rope_dim: 16?",
         "Dimensión desacoplada de RoPE.",
         "Define que 16 canales de cada cabezal están dedicados exclusivamente a proyectar y rotar coordenadas posicionales, manteniéndose desacoplados del vector de compresión latente de contenido de 128 dimensiones."),

        ("¿Por qué M0.1-Mini tiene solo 2 expertos enrutados?",
         "Diseño compacto de M0.1-Mini.",
         "Dos expertos enrutados permiten capturar biparticiones temáticas fundamentales (ej. código vs lenguaje natural) manteniendo un consumo de VRAM y memoria de pesos mínimo, ideal para inferencia en hardware edge."),

        ("¿Cómo influye el tamaño de lote efectivo con grad_accum_steps: 4?",
         "Acumulación de gradientes.",
         "Con `batch_size: 8` y `grad_accum_steps: 4`, el tamaño de lote efectivo es de 32 secuencias por actualización de parámetros, estabilizando la estimación del gradiente del enrutador MoE sin saturar la memoria GPU."),

        ("¿Cuál es el rol de weight_decay: 0.1 en AdamW?",
         "Regularización por decaimiento de pesos.",
         "Aplica una penalización proporcional directa a los pesos sin interferir en los acumuladores de momentum ni en la varianza móvil, evitando que los parámetros de escala y normalización crezcan indefinidamente."),

        ("¿Qué ventaja computacional aporta la atención latente en la etapa de prefill?",
         "MLA en fase de prefill.",
         "Durante el prefill de contextos extensos (ej. 8K-32K tokens), la compresión latente reduce el tamaño de las matrices intermedias que deben persistirse en memoria de trabajo de la GPU para las capas posteriores."),

        ("¿Qué sucede si se desactiva el experto compartido en M0.1?",
         "Impacto de remover el experto compartido.",
         "Los expertos enrutados se ven obligados a reaprender sintaxis básica, puntuación y estructuras repetitivas, reduciendo su capacidad efectiva para especializarse en dominios técnicos y degradando la coherencia general del modelo."),

        ("¿Por qué se utiliza beta2: 0.95 en el optimizador AdamW en lugar de 0.999?",
         "Configuración de beta2 en Transformers.",
         "Un `beta2` de 0.95 otorga menor persistencia a la memoria histórica de gradientes al cuadrado, permitiendo que el optimizador se adapte más rápidamente a cambios en la distribución de datos propios de arquitecturas MoE."),

        ("¿Cómo afecta el context_length: 32768 a la memoria requerida durante entrenamiento?",
         "Entrenamiento con contexto largo.",
         "Aunque el contexto máximo del modelo es 32K, durante el preentrenamiento base se utiliza `seq_len: 1024` para maximizar el throughput de muestras, escalando posteriormente a contextos mayores en fases de alineación y fine-tuning."),

        ("¿Por qué M0.1 no utiliza dropout en sus capas de atención o feed-forward?",
         "Cero dropout (dropout: 0.0).",
         "En modelos autorregresivos preentrenados sobre corpus masivos, el dropout ralentiza la convergencia y degrada la precisión numérica en cálculos de precisión reducida (FP16/BF16). La regularización se asegura mediante weight decay y balanceo MoE."),

        ("¿Cómo se inicializa el router gating en M0.1?",
         "Inicialización del router gating.",
         "Se inicializa con pesos pequeños extraídos de una distribución normal con media cero, asegurando que al inicio todos los expertos tengan probabilidades de asignación equiprobables antes de aprender especialización."),

        ("¿Cuál es la función del parámetro moe_collapse_consecutive_steps: 50?",
         "Monitoreo de colapso de expertos.",
         "Si durante 50 pasos continuos un experto recibe un porcentaje inferior al 30% de su cuota esperada, el sistema de entrenamiento emite una alerta métrica para diagnosticar posibles problemas en la compuerta o en la tasa de aprendizaje.")
    ]

    for q, th, resp in muestras_arquitectura:
        samples.append({
            "user": q,
            "think": f"""Pregunta sobre arquitectura: {th}
Contexto: M0.1 base.yaml, especificaciones MoE/MLA.
Respuesta: Técnica, precisa y directa.""",
            "response": resp
        })

    # Muestras contextuales de diálogo en arquitectura
    dialogos_arq = [
        ("Explícame el flujo completo de un token al pasar por una capa MoE de M0.1.",
         "Flujo de pase hacia adelante en una capa MoE de M0.1.",
         """1. La activación de entrada normalizada pasa por la red de compuerta ($W_g$), generando logits para los 4 expertos enrutados.
2. Se evalúa la función `sqrtsoftplus` normalizada para obtener las probabilidades de enrutamiento.
3. Se selecciona el experto de mayor puntuación (Top-1).
4. El token es computado por el experto seleccionado mediante SwiGLU con clamping a 10.0.
5. Concurrentemente, el token es procesado por el experto compartido.
6. La salida final de la capa es la suma de la salida del experto compartido más la salida del experto enrutado escalada por su probabilidad."""),

        ("¿En qué se diferencia el cálculo de Key en MLA respecto a la atención estándar?",
         "Diferencias en la formación de Claves (Key) en MLA.",
         "En atención estándar, la clave $K$ se proyecta directamente de la entrada como $K = W_K x$. En MLA, la clave se reconstruye proyectando hacia arriba el vector latente comprimido ($K^C = W_{UK} c^{KV}$) y concatenándole el vector posicional rotado ($k^R = \text{RoPE}(W_{KR} x)$), preservando identidad semántica y posición relativa de forma compacta."),

        ("¿Por qué el optimizador Muon acelera la convergencia en capas lineales densas?",
         "Aceleración de convergencia por Muon.",
         "Muon normaliza los valores singulares de la matriz de actualización mediante la iteración de Newton-Schulz, logrando que el gradiente actualice todas las direcciones del espacio latente con igual intensidad espectral. Esto previene que unos pocos componentes principales dominen el aprendizaje, favoreciendo una convergencia equilibrada en menos pasos."),

        ("¿Cómo previene Cross-Layer KV Reuse el cuello de botella de memoria en GPUs con bus estrecho?",
         "Optimización de bus de memoria mediante Cross-Layer KV Reuse.",
         "En GPUs de consumo con buses de memoria de 128 o 192 bits, el cuello de botella durante la inferencia es la transferencia de KV cache desde la VRAM global a la memoria compartida del chip (*SRAM*). Al compartir KV entre pares de capas, las lecturas a DRAM se reducen a la mitad, incrementando la tasa de tokens por segundo."),

        ("¿Cuál es la relación entre el número de cabezales (10) y la dimensión del modelo (640)?",
         "Cálculo de la dimensión del cabezal.",
         "La dimensión de cada cabezal de atención es $d_{head} = d_{model} / n_{heads} = 640 / 10 = 64$. Una dimensión de cabezal de 64 es óptima para la compatibilidad con kernels de atención acelerada por hardware (como FlashAttention o SDPA) en alineaciones de memoria de 128 bytes.")
    ]

    for q, th, resp in dialogos_arq:
        samples.append({
            "user": q,
            "think": f"""Pregunta sobre: {th}
Contexto: Arquitectura interna de M0.1.
Respuesta: Explicación estructurada y formal en español neutro.""",
            "response": resp
        })

    # Completar hasta 55 muestras en categoría 2
    extras = [
        ("¿Qué formato numérico se utiliza para almacenar los pesos del modelo en disco?",
         "Almacenamiento de pesos.",
         "Los checkpoints se guardan en tensores serializados de PyTorch (`.pt`) en precisión de punto flotante de 16 bits (FP16 o BF16), optimizando el espacio en almacenamiento y la velocidad de carga a memoria."),
        ("¿Qué papel juega el parámetro max_norm: 1.0 en el entrenamiento?",
         "Recorte de gradientes (gradient clipping).",
         "Aplica recorte de gradientes (gradient clipping) escalando el vector global de gradientes si su norma euclidiana excede 1.0, lo que previene explosiones numéricas en transiciones bruscas de datos."),
        ("¿Cómo afecta d_model=640 a la eficiencia de cómputo en arquitecturas compactas?",
         "Selección de d_model=640.",
         "Un $d_{model}$ de 640 es múltiplo de potencias de 2 y de las dimensiones de warp (32 y 64), garantizando alineación óptima en las unidades de cálculo tensorial de GPUs sin desperdicio de memoria por padding."),
        ("¿Se utiliza sesgo inductivo posicional absoluto en M0.1?",
         "Ausencia de embeddings posicionales absolutos.",
         "No. M0.1 no emplea matrices de embeddings posicionales absolutos como los Transformers originales; la noción de distancia se infiere exclusivamente de forma relativa mediante Partial RoPE."),
        ("¿Qué ocurre si el scheduler supera los max_steps configurados?",
         "Finalización del planificador de entrenamiento.",
         "Al alcanzar `max_steps: 10000`, la tasa de aprendizaje se congela en el valor mínimo (`min_lr_ratio * max_lr`), permitiendo continuar pasos de evaluación o guardar el checkpoint final consolidado."),
        ("¿Por qué se eligen 2 capas densas iniciales antes de los bloques MoE?",
         "Capas densas iniciales (num_dense_layers: 2).",
         "Las dos primeras capas del modelo son densas convencionales para asentar representaciones léxicas y sintácticas primarias antes de que el enrutador comience a bifurcar tokens entre expertos especializados."),
        ("¿Cómo interactúa la compresión MLA con los mecanismos de atención causal?",
         "Atención causal con compresión MLA.",
         "La máscara causal triangular inferior se aplica directamente sobre la matriz de afinidad $Q K^T / \sqrt{d}$, asegurando que ningún token atienda a representaciones latentes futuras."),
        ("¿Cómo se calcula la perplejidad durante la validación periódica?",
         "Cálculo de perplejidad en validación.",
         "Se computa como la exponencial del valor medio de entropía cruzada ($\text{PPL} = \exp(\mathcal{L}_{CE})$) sobre el conjunto de validación en tokens predichos."),
        ("¿Por qué el parámetro beta1 es 0.9 en el optimizador?",
         "Momento de primer orden en AdamW.",
         "Un factor de momentum `beta1: 0.9` es el estándar en arquitecturas de lenguaje para promediar la dirección del gradiente en los últimos ~10 pasos, suavizando el ruido de lotes pequeños."),
        ("¿Cómo se implementa el SwiGLU clamping en código PyTorch?",
         "Implementación de SwiGLU clamping.",
         "En la pasada hacia adelante, tras computar la compuerta bilineal `(x @ W1) * silu(x @ W2)`, se aplica `torch.clamp(act, -10.0, 10.0)` antes de la proyección final con `W3`.")
    ]

    for q, th, resp in extras:
        samples.append({
            "user": q,
            "think": f"""Pregunta de arquitectura: {th}
Contexto: M0.1 especificaciones técnicas.
Respuesta: Directa, técnica y sobria.""",
            "response": resp
        })

    return samples
