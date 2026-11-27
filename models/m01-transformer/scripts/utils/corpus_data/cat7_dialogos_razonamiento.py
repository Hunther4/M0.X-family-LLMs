r"""Categoría 7: Diálogos de Razonamiento Estructurado y Algoritmos."""

def get_samples():
    samples = []

    muestras = [
        ("Dado un arreglo de intervalos cerrados, fusiona todos los intervalos que se solapen.",
         "Fusión de intervalos solapados.",
         """```python
from typing import List

def fusionar_intervalos(intervalos: List[List[int]]) -> List[List[int]]:
    \"\"\"Fusiona intervalos solapados en tiempo O(N log N) y espacio O(N).\"\"\"
    if not intervalos:
        return []

    # Ordenar por el extremo inicial
    intervalos.sort(key=lambda x: x[0])
    fusionados: List[List[int]] = [intervalos[0]]

    for actual in intervalos[1:]:
        ultimo = fusionados[-1]
        if actual[0] <= ultimo[1]:
            # Existe solapamiento: extender el extremo final
            ultimo[1] = max(ultimo[1], actual[1])
        else:
            fusionados.append(actual)

    return fusionados
```"""),

        ("¿Cómo verificar si un árbol binario es un Árbol Binario de Búsqueda (BST) válido en Python?",
         "Validación de Árbol Binario de Búsqueda.",
         """```python
from typing import Optional

class NodoArbol:
    def __init__(self, val: int = 0, izq: Optional['NodoArbol'] = None, der: Optional['NodoArbol'] = None):
        self.val = val
        self.izq = izq
        self.der = der

def es_bst_valido(raiz: Optional[NodoArbol], min_val: float = float('-inf'), max_val: float = float('inf')) -> bool:
    \"\"\"Valida si cada nodo respeta las cotas estrictas (min_val < nodo.val < max_val). O(N).\"\"\"
    if not raiz:
        return True

    if not (min_val < raiz.val < max_val):
        return False

    return (es_bst_valido(raiz.izq, min_val, raiz.val) and 
            es_bst_valido(raiz.der, raiz.val, max_val))
```"""),

        ("Encuentra los K elementos más frecuentes en una lista en tiempo O(N log K).",
         "Top K elementos más frecuentes mediante Heap.",
         """```python
import heapq
from collections import Counter
from typing import List

def top_k_frecuentes(nums: List[int], k: int) -> List[int]:
    \"\"\"Retorna los k elementos mas comunes utilizando un monticulo minimo. O(N log K).\"\"\"
    conteos = Counter(nums)
    # Mantener un monticulo de tamano k con tuplas (frecuencia, elemento)
    return heapq.nlargest(k, conteos.keys(), key=conteos.get)
```"""),

        ("¿Cómo invertir una lista simplemente enlazada de forma iterativa?",
         "Inversión de lista enlazada iterativa.",
         """```python
from typing import Optional

class Nodo:
    def __init__(self, valor: int = 0, siguiente: Optional['Nodo'] = None):
        self.valor = valor
        self.siguiente = siguiente

def invertir_lista(cabeza: Optional[Nodo]) -> Optional[Nodo]:
    \"\"\"Invierte punteros en O(N) tiempo y O(1) memoria auxiliar.\"\"\"
    previo = None
    actual = cabeza

    while actual:
        siguiente_temporal = actual.siguiente
        actual.siguiente = previo
        previo = actual
        actual = siguiente_temporal

    return previo
```"""),

        ("Implementa el patrón Singleton en Python que sea seguro para entornos multihilo.",
         "Singleton thread-safe en Python.",
         """```python
import threading
from typing import Any

class SingletonSeguro:
    _instancia = None
    _bloqueo = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any):
        # Primer chequeo rapido sin bloqueo (Double-Checked Locking)
        if cls._instancia is None:
            with cls._bloqueo:
                if cls._instancia is None:
                    cls._instancia = super().__new__(cls)
        return cls._instancia
```"""),

        ("¿Cuál es la diferencia entre 3NF y BCNF en normalización de bases de datos?",
         "3NF frente a Forma Normal de Boyce-Codd (BCNF).",
         """- **Tercera Forma Normal (3NF)**:
  - Está en 2NF.
  - Ningún atributo no primario depende transitivamente de la clave primaria.
  - Formalmente: Para toda dependencia funcional $X \to Y$, $X$ es una superclave O $Y$ es un atributo primo (parte de alguna clave candidata).
- **Forma Normal de Boyce-Codd (BCNF)**:
  - Versión más estricta de 3NF.
  - Para **toda** dependencia funcional $X \to Y$, $X$ **debe ser necesariamente una superclave**.
  - BCNF elimina anomalías donde un atributo primo depende de un atributo no superclave."""),

        ("Explica cómo funciona el apretón de manos (handshake) en TLS 1.3 frente a TLS 1.2.",
         "Handshake en TLS 1.3 vs TLS 1.2.",
         """- **TLS 1.2 (2 RTT)**:
  1. Cliente envía `ClientHello`.
  2. Servidor responde con `ServerHello`, Certificado e intercambio de claves.
  3. Cliente verifica, genera clave pre-maestra y envía `Finished`.
  4. Servidor responde `Finished`. (Requiere 2 viajes de ida y vuelta para iniciar datos cifrados).
- **TLS 1.3 (1 RTT / 0-RTT)**:
  1. El cliente envía `ClientHello` junto con sus conjeturas de parámetros de clave Diffie-Hellman (`Key Share`) en el primer mensaje.
  2. El servidor responde con su parte de la clave, certificado y `Finished`.
  3. Los datos de aplicación comienzan a transmitirse inmediatamente tras 1 RTT (o 0-RTT con tickets de sesión previos)."""),

        ("¿Cómo funciona la multiplexación en HTTP/2?",
         "Multiplexación en HTTP/2.",
         """En HTTP/1.1 cada solicitud requería una conexión TCP independiente o sufría de bloqueo de cabeza de línea (*Head-of-Line Blocking* a nivel de aplicación).

En **HTTP/2**:
- Se utiliza una **única conexión TCP persistente** entre cliente y servidor.
- La comunicación se divide en **tramas binarias** (*binary frames*) organizadas en **flujos lógicos independientes** (*streams*).
- Las tramas de múltiples solicitudes y respuestas se intercalan libremente en el mismo canal y se reensamblan en el receptor mediante el identificador de stream (`Stream ID`), eliminando esperas secuenciales."""),

        ("¿Cómo evitar bloqueos mutuos de canales en Go?",
         "Prevención de channel deadlocks en Go.",
         """1. **Garantizar emisores y receptores activos**: Un canal sin búfer bloquea al emisor hasta que un receptor esté listo, y viceversa.
2. **Uso de canales con búfer adecuado**:
   ```go
   ch := make(chan int, 1) // Buffer de 1 elemento evita bloqueo inmediato
   ```
3. **Cláusula `select` con `default` para operaciones no bloqueantes**:
   ```go
   select {
   case ch <- valor:
       // Enviado exitosamente
   default:
       // Canal saturado, ejecutar contingencia sin suspender goroutine
   }
   ```
4. **Cerrar canales solo desde la goroutine emisora**."""),

        ("¿Cómo implementar un Pool de Conexiones HTTP reutilizable en Python con `httpx`?",
         "Pool de conexiones con httpx.",
         """```python
import httpx
from contextlib import asynccontextmanager

# Cliente asincrono configurado con pool de transporte persistente
LIMITES = httpx.Limits(max_keepalive_connections=50, max_connections=100, keepalive_expiry=30.0)
TIMEOUT = httpx.Timeout(10.0, connect=5.0)

async def cliente_http_persistente():
    async with httpx.AsyncClient(limits=LIMITES, timeout=TIMEOUT) as cliente:
        respuesta = await cliente.get("https://api.ejemplo.com/datos")
        return respuesta.json()
```"""),

        ("¿Qué es un árbol de decisión y cómo se calcula la Ganancia de Información mediante Entropía?",
         "Árbol de decisión y Ganancia de Información.",
         """La Ganancia de Información $IG(T, a)$ mide la reducción en la entropía del conjunto $T$ tras particionarlo por el atributo $a$:

1. **Entropía del conjunto base $T$**:
   $$H(T) = - \sum_{i=1}^C p_i \log_2 p_i$$
2. **Entropía condicional ponderada**:
   $$H(T \mid a) = \sum_{v \in \text{valores}(a)} \frac{|T_v|}{|T|} H(T_v)$$
3. **Ganancia de Información**:
   $$IG(T, a) = H(T) - H(T \mid a)$$
El algoritmo (como ID3 o C4.5) selecciona el atributo $a$ que maximice $IG(T, a)$ en cada bifurcación."""),

        ("¿Cómo depurar un proceso de Node.js que satura el 100% de CPU?",
         "Depuración de CPU en Node.js.",
         """1. Iniciar la aplicación con el profiler V8 integrado:
```bash
node --prof app.js
```
2. Procesar el archivo de registro generado tras la prueba de estrés:
```bash
node --prof-process isolate-0x...-v8.log > resultado_perfil.txt
```
3. Alternativamente, conectar el inspector remoto con `node --inspect app.js` y abrir `chrome://inspect` en el navegador para capturar un *CPU Profile* en tiempo real, identificando funciones síncronas bloqueantes en el *Flame Graph*."""),

        ("¿Cuál es la diferencia entre autenticación basada en sesiones y JWT?",
         "Sesiones con estado vs JWT sin estado.",
         """- **Sesiones con estado (*Stateful*)**:
  - El servidor genera un `session_id` que guarda en base de datos o Redis y lo envía como cookie HTTP-only al cliente.
  - Permite revocación instantánea de sesiones en el backend.
  - Demanda almacenamiento centralizado compartido entre réplicas del servidor.
- **JWT (*Stateless*)**:
  - El token contiene la firma criptográfica y las declaraciones (*claims*) en base64.
  - El servidor valida la firma matemáticamente sin consultar bases de datos en cada petición.
  - Dificulta la revocación inmediata antes de la fecha de expiración (`exp`), requiriendo listas negras en memoria."""),

        ("Escribe una función en C++ para calcular el producto punto de dos vectores con instrucciones manuales.",
         "Producto punto de vectores en C++.",
         """```cpp
#include <vector>
#include <numeric>
#include <stdexcept>

double producto_punto(const std::vector<double>& a, const std::vector<double>& b) {
    if (a.size() != b.size()) {
        throw std::invalid_argument("Las dimensiones de los vectores deben coincidir.");
    }

    double acumulador = 0.0;
    const size_t n = a.size();

    // Bucle lineal optimizable por vectorizacion del compilador (SIMD)
    for (size_t i = 0; i < n; ++i) {
        acumulador += a[i] * b[i];
    }

    return acumulador;
}
```"""),

        ("¿Cómo funciona el protocolo Gossip en clústeres distribuidos (e.g. Cassandra / Consul)?",
         "Protocolo Gossip en sistemas distribuidos.",
         """El protocolo Gossip es un mecanismo descentralizado de difusión epidémica:
1. Periódicamente (cada $T$ milisegundos), cada nodo selecciona al azar un subconjunto de $k$ nodos conocidos del clúster.
2. Les transmite su estado actual, información de membresía y marcas de tiempo (*timestamps* o números de versión).
3. Los nodos receptores combinan la información más reciente y la retransmiten en el siguiente ciclo.
4. **Propiedad**: La información converge en todo el clúster con complejidad de tiempo $O(\log N)$, exhibiendo alta resiliencia ante caídas de nodos individuales sin coordinadores centrales."""),

        ("¿Qué es un ataque Man-in-the-Middle (MitM) y cómo lo previene HTTPS con HSTS?",
         "MitM y HSTS.",
         """En un ataque MitM, un atacante intercepta la comunicación entre el cliente y el servidor, pudiendo suplantar identidades o alterar paquetes.

**Prevención mediante HTTPS + HSTS (HTTP Strict Transport Security)**:
- HTTPS cifra el canal mediante TLS e intercambia certificados validados por Autoridades Certificadoras (CA).
- El encabezado `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload` instruye al navegador a comunicarse **exclusivamente** mediante HTTPS, rechazando conexiones HTTP inseguras e impidiendo que el usuario ignore advertencias de certificados inválidos (eliminando el vector de degradación SSL Stripping)."""),

        ("¿Cómo se calcula la matriz de covarianza de un conjunto de datos?",
         "Cálculo de la matriz de covarianza.",
         """Dado un conjunto de datos centrado $X \in \mathbb{R}^{N \times D}$ con $N$ observaciones y $D$ variables, donde $\mathbb{E}[X] = 0$:

La matriz de covarianza muestral $\Sigma \in \mathbb{R}^{D \times D}$ se calcula como:
$$\Sigma = \frac{1}{N - 1} X^T X$$

El elemento $\Sigma_{i, j}$ representa la covarianza entre la variable $i$ y la variable $j$:
$$\Sigma_{i, j} = \frac{1}{N - 1} \sum_{k=1}^N x_{k, i} x_{k, j}$$
Los elementos de la diagonal principal $\Sigma_{i, i}$ son las varianzas de cada variable individual."""),

        ("¿Cómo programar un cron job en Linux para ejecutar un script cada medianoche?",
         "Configuración de cron job en Linux.",
         """Editar el archivo crontab del usuario:
```bash
crontab -e
```
Añadir la siguiente línea de programación:
```cron
0 0 * * * /opt/scripts/tarea_mantenimiento.sh >> /var/log/mantenimiento.log 2>&1
```
Estructura:
- `0`: Minuto 0
- `0`: Hora 0 (medianoche)
- `*`: Todos los días del mes
- `*`: Todos los meses
- `*`: Todos los días de la semana
- `2>&1`: Redirige tanto la salida estándar como los errores al archivo de registro."""),

        ("¿Qué diferencia hay entre una clave primaria y un índice único en bases de datos relacionales?",
         "Primary Key vs Unique Index.",
         """- **Clave Primaria (Primary Key)**:
  - Identificador único de fila en la tabla.
  - Solo puede existir **una** clave primaria por tabla.
  - **No permite valores `NULL`** bajo ninguna circunstancia.
  - Generalmente crea de forma automática el índice agrupado (*Clustered Index*) de la tabla.
- **Índice Único (Unique Index / Constraint)**:
  - Garantiza unicidad sobre una o más columnas secundarias.
  - Pueden existir **múltiples** índices únicos en la misma tabla.
  - En el estándar SQL permite valores `NULL` (en PostgreSQL, múltiples filas pueden contener `NULL` a menos que se defina `NULLS NOT DISTINCT`)."""),

        ("¿Cómo estructurar un pipeline de preprocesamiento de texto para tokenización BPE?",
         "Preprocesamiento de texto para BPE.",
         """1. **Normalización Unicode**: Aplicar normalización NFC o NFKC para unificar representaciones de acentos y caracteres combinados.
2. **Preservación de caracteres en español**: Mantener diacríticos (á, é, í, ó, ú, ü, ñ) y signos de apertura (¿, ¡) sin eliminarlos ni transliterarlos a ASCII.
3. **Pre-tokenización por expresiones regulares (Regex split)**:
   Dividir el flujo continuo en trozos léxicos (palabras, contracciones y puntuación) empleando una regla regex estilo GPT-2:
   ```regex
   's|'t|'re|'ve| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+
   ```
4. **Codificación de bytes UTF-8**: Mapear cada trozo a su secuencia de bytes base antes de iniciar el conteo incremental de pares para fusiones (*merges*).""")
    ]

    for q, th, resp in muestras:
        samples.append({
            "user": q,
            "think": f"""Consulta técnica: {th}
Contexto: Razonamiento estructurado y resolución rigurosa.
Respuesta: Directa, concisa y en español neutro.""",
            "response": resp
        })

    return samples
