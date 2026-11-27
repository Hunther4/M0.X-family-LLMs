r"""Categoría 5: Matemáticas, Machine Learning, Cuantización y Optimización Numérica."""

def get_samples():
    samples = []

    samples.append({
        "user": "¿Cómo se calcula analíticamente la pérdida de entropía cruzada en un modelo de lenguaje autorregresivo?",
        "think": """El usuario solicita la deducción analítica de Cross-Entropy Loss para modelado autorregresivo.
Contexto: Probabilidad condicional de la secuencia y log-verosimilitud negativa.
Respuesta: Formulación matemática rigurosa con logit softmax y promedio por token.""",
        "response": """Para una secuencia de $T$ tokens $y = (y_1, y_2, \dots, y_T)$, la probabilidad conjunta autorregresiva se factoriza según la regla de la cadena:
$$P(y) = \prod_{t=1}^T P(y_t \mid y_{<t})$$

La pérdida de entropía cruzada $\mathcal{L}_{CE}$ es la log-verosimilitud negativa promedio por token:
$$\mathcal{L}_{CE} = - \frac{1}{T} \sum_{t=1}^T \log P(y_t \mid y_{<t})$$

Dado el vector de logits no normalizados $z_t \in \mathbb{R}^V$ emitido por la capa de salida para el paso $t$, la probabilidad del token objetivo $y_t$ se obtiene mediante el operador softmax:
$$P(y_t \mid y_{<t}) = \frac{\exp(z_{t, y_t})}{\sum_{v=1}^V \exp(z_{t, v})}$$

Sustituyendo en la expresión de pérdida:
$$\mathcal{L}_{CE} = \frac{1}{T} \sum_{t=1}^T \left( \log \sum_{v=1}^V \exp(z_{t, v}) - z_{t, y_t} \right)$$
En la práctica computacional se utiliza la formulación numéricamente estable *LogSumExp* restando el logit máximo $\max_v z_{t, v}$ para evitar desbordamiento numérico (*overflow*)."""
    })

    samples.append({
        "user": "¿Cómo se cuantiza un tensor de pesos FP32 a INT8 de manera simétrica?",
        "think": """El usuario solicita el algoritmo y formulación matemática para cuantización simétrica INT8.
Contexto: Escalado absoluto con rango [-127, 127] sin punto cero (zero-point = 0).
Respuesta: Ecuación del factor de escala, redondeo y des-cuantización.""",
        "response": """La cuantización uniforme simétrica a INT8 mapea los valores en punto flotante al intervalo discreto $[-127, 127]$ fijando el punto cero (*zero-point*) en 0:

1. Determinación del valor absoluto máximo:
   $$\alpha = \max_{i} |W_i|$$

2. Cálculo del factor de escala (*scale factor* $S$):
   $$S = \frac{\alpha}{127}$$

3. Mapeo y redondeo al entero más cercano:
   $$W_{\text{INT8}} = \text{clamp}\left( \left\lfloor \frac{W}{S} \right\rceil, -127, 127 \right)$$

4. Reconstrucción aproximada (*dequantization*):
   $$\hat{W} = W_{\text{INT8}} \times S$$

**Ventaja computacional**: Al no requerir un término aditivo de desplazamiento (*zero-point*), la multiplicación de matrices en enteros (`W_int8 @ x_int8`) se reduce a un producto punto puro en hardware, prescindiendo de sumas residuales compensatorias."""
    })

    samples.append({
        "user": "¿Por qué el factor de escala en la atención de producto punto es 1 / sqrt(d_k)?",
        "think": """Deducción matemática del factor 1 / sqrt(d_k) en Scaled Dot-Product Attention.
Contexto: Varianza de la suma de variables aleatorias independientes en el producto punto de Q y K.
Respuesta: Demostración de cómo se preserva la varianza unitaria para evitar saturación de softmax.""",
        "response": """Sea $q \in \mathbb{R}^{d_k}$ y $k \in \mathbb{R}^{d_k}$ vectores de consulta y clave cuyas componentes son variables aleatorias independientes con media 0 y varianza 1:
$$\mathbb{E}[q_i] = 0, \quad \text{Var}(q_i) = 1, \quad \mathbb{E}[k_i] = 0, \quad \text{Var}(k_i) = 1$$

El producto punto escalar es la suma de $d_k$ términos independientes:
$$s = q^T k = \sum_{i=1}^{d_k} q_i k_i$$

Calculando la media y varianza de $s$:
- Media: $\mathbb{E}[s] = \sum_{i=1}^{d_k} \mathbb{E}[q_i] \mathbb{E}[k_i] = 0$
- Varianza:
  $$\text{Var}(s) = \sum_{i=1}^{d_k} \text{Var}(q_i k_i) = \sum_{i=1}^{d_k} \left( \mathbb{E}[q_i^2] \mathbb{E}[k_i^2] - (\mathbb{E}[q_i]\mathbb{E}[k_i])^2 \right) = \sum_{i=1}^{d_k} (1 \cdot 1 - 0) = d_k$$

Sin escalamiento, para dimensiones grandes (ej. $d_k = 64$ o $128$), la magnitud típica de $s$ crece proporcionalmente a $\sqrt{d_k}$. Valores elevados saturan la función exponencial del softmax en regiones donde su gradiente es prácticamente cero. Al dividir por $\sqrt{d_k}$:
$$\text{Var}\left( \frac{q^T k}{\sqrt{d_k}} \right) = \frac{\text{Var}(q^T k)}{d_k} = \frac{d_k}{d_k} = 1$$
Se preserva la varianza unitaria, manteniendo un flujo de gradientes adecuado."""
    })

    samples.append({
        "user": "¿Cuál es la relación matemática exacta entre la perplejidad (PPL) y la entropía cruzada?",
        "think": """Relación analítica entre Perplejidad y función de pérdida Cross-Entropy.
Contexto: Exponenciación de la pérdida promedio en base e (o base 2 según la unidad de información).
Respuesta: Demostración directa y su significado como tamaño efectivo del vocabulario equivalente.""",
        "response": """La perplejidad ($\text{PPL}$) es la exponencial de la pérdida de entropía cruzada media por token $\mathcal{L}_{CE}$:
$$\text{PPL} = \exp(\mathcal{L}_{CE})$$

### Deducción:
Dada la probabilidad conjunta del corpus bajo el modelo $P(y_1, \dots, y_T)$:
$$\text{PPL} = P(y_1, \dots, y_T)^{-\frac{1}{T}} = \left( \prod_{t=1}^T P(y_t \mid y_{<t}) \right)^{-\frac{1}{T}}$$

Tomando el logaritmo natural y aplicando propiedades exponenciales:
$$\ln(\text{PPL}) = - \frac{1}{T} \sum_{t=1}^T \ln P(y_t \mid y_{<t}) = \mathcal{L}_{CE}$$
$$\text{PPL} = e^{\mathcal{L}_{CE}}$$

### Interpretación analítica
Una perplejidad de valor $K$ indica que, en cada paso de predicción, el modelo tiene un grado de incertidumbre estadístico equivalente a tener que elegir uniformemente al azar entre $K$ opciones equiprobables."""
    })

    muestras_ml = [
        ("¿Cómo se calcula el gradiente del router MoE mediante retropropagación?",
         "Backpropagation en el router MoE.",
         """Sea $y = \sum_{i=1}^E s_i(x) \cdot \text{Exp}_i(x)$ la salida de la capa MoE con respecto a las puntuaciones normalizadas $s_i(x)$.

Por la regla de la cadena, el gradiente de la función de costo $\mathcal{L}$ respecto al logit $h_i$ antes de la función de activación del router es:
$$\frac{\partial \mathcal{L}}{\partial h_i} = \sum_{j=1}^E \frac{\partial \mathcal{L}}{\partial y} \cdot \text{Exp}_j(x) \cdot \frac{\partial s_j}{\partial h_i}$$

Cuando se emplea selección discontinua (como Top-1), el gradiente fluye a través del camino del experto activado, mientras que la pérdida auxiliar de balanceo introduce un gradiente directo sobre el vector de compuerta $W_g$ para regularizar la distribución de masa probabilística."""),

        ("¿Qué es FlashAttention y cómo reduce la complejidad espacial de O(N^2) a O(N)?",
         "Mecanismo de FlashAttention.",
         """FlashAttention reestructura el cálculo de atención sin materializar en memoria HBM la matriz intermedia de afinidad $S = Q K^T$ ($N \times N$ elementos):
1. **Tiling (Fragmentación)**: Carga bloques rectangulares de $Q$, $K$ y $V$ a la memoria ultrarrápida compartida del procesador (*SRAM*).
2. **Softmax incremental (Online Softmax)**: Calcula las estadísticas de normalización ($\max$ y $\sum e^x$) sobre la marcha de forma iterativa entre bloques sucesivos.
3. **Recomputación en pasada hacia atrás**: En lugar de guardar la matriz $N \times N$ para calcular gradientes, recomputa los bloques necesarios en SRAM durante el backward pass, transformando el consumo de memoria global de $O(N^2)$ a $O(N)$."""),

        ("Explica la formulación matemática de RMSNorm frente a LayerNorm.",
         "RMSNorm vs LayerNorm matemático.",
         """En **LayerNorm**:
$$y = \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} \odot \gamma + \beta, \quad \mu = \frac{1}{d}\sum_{i=1}^d x_i, \quad \sigma^2 = \frac{1}{d}\sum_{i=1}^d (x_i - \mu)^2$$

En **RMSNorm**:
$$y = \frac{x}{\text{RMS}(x)} \odot \gamma, \quad \text{RMS}(x) = \sqrt{\frac{1}{d} \sum_{i=1}^d x_i^2 + \epsilon}$$

RMSNorm asume que la propiedad de invariancia de escala es el factor determinante para el éxito de la normalización, prescindiendo del cómputo de centrado respecto a la media $\mu$ y del vector aditivo de sesgo $\beta$."""),

        ("¿Qué es la divergencia de Kullback-Leibler y cómo se utiliza en destilación de modelos?",
         "Divergencia KL en destilación.",
         """La divergencia KL mide la pérdida de información al aproximar una distribución objetivo $P$ (modelo maestro) mediante una distribución $Q$ (modelo alumno):
$$D_{KL}(P \parallel Q) = \sum_{x \in \mathcal{X}} P(x) \log\left( \frac{P(x)}{Q(x)} \right)$$

En destilación de conocimiento, se suavizan los logits con una temperatura $T$ ($p_i = \text{softmax}(z_i^T / T)$) y la función de pérdida penaliza la discrepancia entre las distribuciones suaves del maestro y del alumno, permitiendo transferir probabilidades de tokens alternativos ("conocimiento oscuro")."""),

        ("¿Por qué el optimizador AdamW desvincula el decaimiento de pesos del gradiente adaptativo?",
         "Desacoplamiento de Weight Decay en AdamW.",
         """En la formulación original de Adam con regularización $L_2$, el término de penalización $\lambda \theta$ se sumaba directamente al gradiente $g_t$. Al dividirse por $\sqrt{v_t}$ (la raíz de la varianza histórica), los parámetros con gradientes frecuentes recibían una penalización efectiva menor que aquellos con gradientes infrecuentes.

AdamW desacopla la regularización aplicándola directamente al valor del parámetro en cada paso:
$$\theta_{t} = \theta_{t-1} - \eta \lambda \theta_{t-1} - \frac{\eta}{\sqrt{\hat{v}_t} + \epsilon} \hat{m}_t$$
garantizando una tasa de decaimiento homogénea independientemente de la magnitud de la varianza del gradiente."""),

        ("¿Cómo opera el algoritmo de cuantización AWQ (Activation-aware Weight Quantization)?",
         "Principios de AWQ.",
         """AWQ protege el 1% de pesos más destacados (*salient weights*) identificados por la magnitud media de las activaciones que atraviesan dichos canales:
1. No todos los pesos tienen el mismo impacto; los canales con activaciones de gran magnitud dominan la precisión.
2. En lugar de mantener esos pesos en FP16 mixtos, AWQ escala matemáticamente los canales salientes por un factor $s > 1$ y escala inversamente la activación por $1/s$:
$$W' = W \cdot \text{diag}(s), \quad X' = \text{diag}(s)^{-1} \cdot X$$
3. Al cuantizar $W'$ a INT4, el error de redondeo relativo sobre los pesos salientes se reduce drásticamente sin modificar la arquitectura física en inferencia."""),

        ("Demuestra por qué el determinante de una matriz ortogonal es siempre +1 o -1.",
         "Propiedad del determinante en matrices ortogonales.",
         """Por definición, una matriz $Q \in \mathbb{R}^{n \times n}$ es ortogonal si satisface $Q^T Q = I$.

Aplicando la propiedad multiplicativa del determinante $\det(A B) = \det(A)\det(B)$:
$$\det(Q^T Q) = \det(Q^T) \det(Q) = \det(I) = 1$$

Dado que el determinante de una matriz es idéntico al de su transpuesta ($\det(Q^T) = \det(Q)$):
$$(\det(Q))^2 = 1 \implies \det(Q) = \pm 1$$

Si $\det(Q) = 1$, la transformación corresponde a una rotación pura; si $\det(Q) = -1$, involucra una rotación combinada con una reflexión."""),

        ("¿Cuál es la diferencia entre el error cuadrático medio (MSE) y la pérdida de Huber?",
         "Pérdida de Huber frente a MSE.",
         """- **MSE**: $\mathcal{L}_{\text{MSE}}(y, \hat{y}) = \frac{1}{2}(y - \hat{y})^2$. Penaliza de manera cuadrática todos los errores; es fuertemente sensible a valores atípicos (*outliers*), cuyos gradientes crecen linealmente con el error.
- **Pérdida de Huber**: Combina comportamiento cuadrático para errores pequeños y lineal para errores grandes:
$$\mathcal{L}_\delta(a) = \begin{cases} \frac{1}{2}a^2 & \text{si } |a| \le \delta \\ \delta (|a| - \frac{1}{2}\delta) & \text{en otro caso} \end{cases}$$
donde $a = y - \hat{y}$. Ofrece diferenciabilidad suave en el origen y robustez ante observaciones anómalas."""),

        ("¿Cómo se calcula el número de parámetros de una capa lineal con dimensiones de entrada M y salida N?",
         "Conteo de parámetros en capa lineal.",
         """Para una transformación afín $y = x W^T + b$ con $x \in \mathbb{R}^M$ y $y \in \mathbb{R}^N$:
- Matriz de pesos $W$: $N \times M$ elementos.
- Vector de sesgo (*bias*) $b$: $N$ elementos (si está habilitado; en M0.1 suele ser 0).
- Total de parámetros: $M \times N + N$ (o exactamente $M \times N$ si `bias=False`)."""),

        ("¿Qué es la condición de Lipschitz y por qué es relevante en redes generativas o normalizaciones?",
         "Constante de Lipschitz en redes neuronales.",
         """Una función $f: \mathbb{R}^n \to \mathbb{R}^m$ es $L$-Lipschitz continua si existe una constante finita $L \ge 0$ tal que:
$$\|f(x) - f(y)\| \le L \|x - y\|, \quad \forall x, y$$
En redes neuronales, acotar la constante de Lipschitz ($L \le 1$) mediante normalización espectral o penalización de gradiente previene la explosión de gradientes y garantiza que variaciones minúsculas en la entrada no induzcan divergencias incontroladas en las capas profundas.""")
    ]

    for q, th, resp in muestras_ml:
        samples.append({
            "user": q,
            "think": f"""Consulta matemática/ML: {th}
Contexto: Teoría de optimización y arquitecturas neuronales.
Respuesta: Ecuaciones formales, rigor matemático y conclusiones concisas.""",
            "response": resp
        })

    return samples
