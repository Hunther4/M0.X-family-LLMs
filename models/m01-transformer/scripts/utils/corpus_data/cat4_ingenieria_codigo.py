r"""Categoría 4: Ingeniería de Software, Código, Algoritmos y Sistemas."""

def get_samples():
    samples = []

    samples.append({
        "user": "Escribe una función en Python para encontrar el elemento mayoritario en una lista en tiempo O(N) y espacio O(1).",
        "think": """El usuario solicita encontrar el elemento mayoritario (> N/2 apariciones) con restricciones O(N) tiempo y O(1) memoria.
Contexto: Algoritmo de votación de Boyer-Moore.
Respuesta: Implementación directa con tipos, validación y análisis de complejidad.""",
        "response": """```python
from typing import List

def elemento_mayoritario(numeros: List[int]) -> int:
    \"\"\"Encuentra el elemento con mas de n/2 apariciones mediante el algoritmo de Boyer-Moore.
    
    Complejidad: Tiempo O(N), Espacio O(1).
    \"\"\"
    candidato = 0
    conteo = 0

    for num in numeros:
        if conteo == 0:
            candidato = num
            conteo = 1
        elif num == candidato:
            conteo += 1
        else:
            conteo -= 1

    return candidato
```

### Funcionamiento
El algoritmo descarta parejas de elementos distintos de forma compensada. Si un elemento aparece más de $N/2$ veces, su conteo neto prevalecerá tras procesar la totalidad de la lista."""
    })

    samples.append({
        "user": "¿Cómo resuelvo un segmentation fault provocado por un puntero colgante (dangling pointer) en C++?",
        "think": """El usuario consulta cómo depurar y solucionar un fallo de segmentación por puntero colgante en C++.
Contexto: Gestión manual de memoria y buenas prácticas con RAII y punteros inteligentes.
Respuesta: Explicar el origen del fallo y proveer solución moderna con `std::unique_ptr` o `std::shared_ptr`.""",
        "response": """Un puntero colgante (*dangling pointer*) apunta a una dirección de memoria desasignada. Acceder a él produce comportamiento indefinido o *segmentation fault*.

### 1. Causa típica con punteros crudos
```cpp
int* crear_entero() {
    int valor = 42;
    return &valor; // ERROR: La variable en la pila se destruye al retornar
}
```

### 2. Solución con semántica de propiedad (RAII y Punteros Inteligentes)
Reemplazar punteros manuales por `std::unique_ptr` para propiedad exclusiva con liberación determinista:

```cpp
#include <memory>
#include <iostream>

std::unique_ptr<int> crear_entero_seguro() {
    return std::make_unique<int>(42); // Memoria alojada en el monticulo, liberada automaticamente
}

int main() {
    auto ptr = crear_entero_seguro();
    std::cout << *ptr << std::endl;
    // La memoria se libera de forma determinista al salir del ambito de ptr
    return 0;
}
```

### Reglas de prevención
- Asignar `nullptr` inmediatamente tras invocar `delete` si se usan punteros crudos legados.
- Emplear `std::unique_ptr` o `std::shared_ptr`/`std::weak_ptr` para evitar accesos a objetos destruidos."""
    })

    samples.append({
        "user": "¿Cómo configuro un pool de conexiones con asyncpg en Python para una API FastAPI?",
        "think": """El usuario solicita configurar un pool de conexiones con asyncpg en FastAPI para alta concurrencia.
Contexto: Ciclo de vida `lifespan` de FastAPI y administración eficiente de conexiones a PostgreSQL.
Respuesta: Código ejecutable con context manager asíncrono y buenas prácticas.""",
        "response": """```python
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
import asyncpg

DATABASE_URL = "postgresql://usuario:clave@localhost:5432/basedatos"

@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    # Inicializacion del pool al arrancar el servidor
    app.state.pool = await asyncpg.create_pool(
        dsn=DATABASE_URL,
        min_size=5,
        max_size=20,
        max_queries=50000,
        timeout=10.0
    )
    yield
    # Cierre controlado de todas las conexiones al apagar
    await app.state.pool.close()

app = FastAPI(lifespan=ciclo_de_vida)

@app.get("/usuarios/{usuario_id}")
async def obtener_usuario(usuario_id: int, request: Request):
    pool: asyncpg.Pool = request.app.state.pool
    async with pool.acquire() as conexion:
        fila = await conexion.fetchrow(
            "SELECT id, nombre, email FROM usuarios WHERE id = $1", 
            usuario_id
        )
        if not fila:
            return {"error": "Usuario no encontrado"}
        return dict(fila)
```"""
    })

    samples.append({
        "user": "Explica la diferencia entre `Arc` y `Rc` en Rust.",
        "think": """Consulta sobre tipos de punteros de conteo de referencias en Rust: Arc vs Rc.
Contexto: Concurrencia, atomicidad y sobrecarga en memoria.
Respuesta: Comparativa precisa de seguridad de hilos y costo de operaciones atómicas.""",
        "response": """La diferencia reside en la seguridad entre hilos (*thread safety*) y la atomicidad del contador de referencias:

- **`Rc<T>` (Reference Counted)**:
  - Diseñado exclusivamente para escenarios de un solo hilo (*single-threaded*).
  - Incrementa y decrementa el contador mediante operaciones aritméticas estándar no atómicas.
  - No implementa los traits `Send` ni `Sync`. El compilador impide pasarlo entre hilos.
  - Ofrece menor sobrecarga computacional al no involucrar barreras de memoria ni instrucciones atómicas de CPU.

- **`Arc<T>` (Atomically Reference Counted)**:
  - Diseñado para escenarios multihilo (*multi-threaded*).
  - Utiliza operaciones atómicas a nivel de hardware (instrucciones tipo *fetch-and-add*) para actualizar el contador.
  - Implementa `Send` y `Sync` si el tipo interno `T` los implementa.
  - Introduce una pequeña sobrecarga de latencia debido a la sincronización de caché entre núcleos del procesador."""
    })

    samples.append({
        "user": "Escribe una consulta SQL con Window Functions para obtener los 3 empleados con mayor salario por departamento.",
        "think": """El usuario solicita obtener el top-3 de salarios por departamento usando funciones de ventana en SQL.
Contexto: `DENSE_RANK()` sobre particiones en PostgreSQL / SQL estándar.
Respuesta: Consulta SQL optimizada mediante CTE (Common Table Expression).""",
        "response": """```sql
WITH empleados_clasificados AS (
    SELECT 
        id,
        nombre,
        departamento_id,
        salario,
        DENSE_RANK() OVER (
            PARTITION BY departamento_id 
            ORDER BY salario DESC
        ) AS posicion
    FROM empleados
)
SELECT 
    id,
    nombre,
    departamento_id,
    salario,
    posicion
FROM empleados_clasificados
WHERE posicion <= 3
ORDER BY departamento_id, posicion;
```

### Justificación técnica
Se utiliza `DENSE_RANK()` en lugar de `ROW_NUMBER()` para asegurar que empleados con salarios idénticos compartan la misma posición jerárquica sin omitir puestos posteriores."""
    })

    muestras_codigo = [
        ("¿Cómo optimizar el uso de memoria en una clase de Python que instancia millones de objetos?",
         "Optimización de memoria en Python mediante __slots__.",
         """Definir `__slots__` en la clase para suprimir la creación del diccionario dinámico `__dict__` por instancia:

```python
class Coordenada:
    __slots__ = ('x', 'y', 'z')
    
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z
```

Esto reduce el consumo de memoria de ~150 bytes por instancia a únicamente 48 bytes, eliminando la sobrecarga del mapa hash interno."""),

        ("¿Cuál es la diferencia entre mutex y semáforo en sistemas operativos?",
         "Mutex frente a semáforo.",
         """- **Mutex (Mutual Exclusion)**: Primitiva de bloqueo con concepto estricto de propiedad; únicamente el hilo que adquirió el bloqueo tiene autorización para liberarlo (capacidad binaria 1).
- **Semáforo**: Mecanismo de señalización basado en un contador entero no negativo. Permite controlar el acceso concurrente a un conjunto finito de recursos ($N \ge 1$) y cualquier hilo puede invocar la señal de liberación (`signal` / `V`)."""),

        ("Implementa un generador en Python para procesar un archivo de texto de 50 GB línea por línea sin desbordar la memoria RAM.",
         "Lectura eficiente de archivos de gran tamaño con generadores.",
         """```python
from typing import Iterator

def procesar_archivo_gigante(ruta_archivo: str) -> Iterator[str]:
    \"\"\"Lee un archivo secuencialmente linea por linea con huella de RAM minima.\"\"\"
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        for linea in archivo:
            # Procesar o transformar la linea sin acumular en listas
            linea_limpia = linea.strip()
            if linea_limpia:
                yield linea_limpia
```

Al utilizar el iterador nativo de `open()`, Python gestiona un búfer interno de lectura (típicamente de 8 KB a 64 KB), manteniendo el consumo de memoria constante independientemente del tamaño del archivo en disco."""),

        ("¿Cómo evitar inyecciones SQL en Node.js con pg?",
         "Prevención de inyección SQL mediante consultas parametrizadas.",
         """Utilizar consultas parametrizadas suministrando los argumentos en un arreglo desacoplado de la sentencia:

```javascript
import pg from 'pg';
const { Pool } = pg;
const pool = new Pool();

async function buscarUsuarioPorEmail(email) {
  // Correcto: $1 es un marcador de posicion que el motor de PostgreSQL escapa
  const consulta = 'SELECT id, nombre FROM usuarios WHERE email = $1';
  const valores = [email];
  
  const resultado = await pool.query(consulta, valores);
  return resultado.rows[0];
}
```
Nunca concatenar variables directamente en la cadena SQL mediante interpolación de cadenas o `+`."""),

        ("¿Qué es un árbol B+ y por qué se utiliza en los motores de bases de datos relacionales?",
         "Estructura de datos Árbol B+ en almacenamiento de bases de datos.",
         """El árbol B+ es una estructura balanceada de búsqueda multi-vía optimizada para almacenamiento secundario (disco/SSD):

1. **Alta ramificación (*fan-out*)**: Cada nodo contiene cientos de claves por página (bloque de 4 KB u 8 KB), lo que reduce la altura del árbol a 3 o 4 niveles incluso para millones de registros.
2. **Hojas enlazadas bidireccionalmente**: Todos los datos reales o punteros a filas residen exclusivamente en los nodos hoja, los cuales forman una lista doblemente enlazada óptima para recorridos de rangos (`BETWEEN`, `>`, `<`).
3. **Lecturas secuenciales**: Los nodos internos actúan únicamente como guía de enrutamiento rápido en memoria RAM."""),

        ("Escribe un script en Bash para respaldar una base de datos MySQL comprimida y eliminar respaldos con más de 7 días.",
         "Script de respaldo automatizado en Bash.",
         """```bash
#!/usr/bin/env bash
set -euo pipefail

DESTINO="/var/backups/mysql"
FECHA="$(date +%Y%m%d_%H%M%S)"
DB_NOMBRE="mi_base_datos"
ARCHIVO="${DESTINO}/${DB_NOMBRE}_${FECHA}.sql.gz"

mkdir -p "${DESTINO}"

# Exportacion y compresion al vuelo
mysqldump --single-transaction --quick "${DB_NOMBRE}" | gzip -9 > "${ARCHIVO}"

# Eliminacion de respaldos con antiguedad superior a 7 dias
find "${DESTINO}" -type f -name "${DB_NOMBRE}_*.sql.gz" -mtime +7 -delete
```"""),

        ("¿Cómo funciona el Event Loop en Node.js?",
         "Fases del Event Loop en Node.js.",
         """El bucle de eventos (*Event Loop*) procesa operaciones asíncronas en un único hilo principal a través de fases ordenadas:

1. **Timers**: Ejecuta callbacks programados por `setTimeout` y `setInterval`.
2. **Pending callbacks**: Procesa callbacks de operaciones de E/S diferidas por el sistema operativo.
3. **Idle, prepare**: Uso interno de libuv.
4. **Poll**: Recupera nuevos eventos de E/S de sockets y descriptores; bloquea si no hay tareas pendientes.
5. **Check**: Ejecuta callbacks registrados mediante `setImmediate()`.
6. **Close callbacks**: Maneja eventos de cierre de recursos (ej. `socket.on('close')`).

Las microtareas (`process.nextTick()` y resolución de promesas `Promise.then`) se ejecutan de forma prioritaria inmediatamente después de completar cada operación antes de cambiar de fase."""),

        ("Implementa búsqueda binaria recursiva en Python con tipado.",
         "Algoritmo de búsqueda binaria.",
         """```python
from typing import Sequence, Optional

def busqueda_binaria(arreglo: Sequence[int], objetivo: int, inicio: int = 0, fin: Optional[int] = None) -> int:
    \"\"\"Retorna el indice del elemento o -1 si no existe. Complejidad: O(log N).\"\"\"
    if fin is None:
        fin = len(arreglo) - 1

    if inicio > fin:
        return -1

    medio = inicio + (fin - inicio) // 2

    if arreglo[medio] == objetivo:
        return medio
    elif arreglo[medio] > objetivo:
        return busqueda_binaria(arreglo, objetivo, inicio, medio - 1)
    else:
        return busqueda_binaria(arreglo, objetivo, medio + 1, fin)
```"""),

        ("¿Qué es un Circuit Breaker en microservicios y qué estados posee?",
         "Patrón Circuit Breaker.",
         """El patrón Cortacircuito (*Circuit Breaker*) previene fallos en cascada aislando llamadas hacia servicios degradados:

1. **Closed (Cerrado)**: Operación normal; las solicitudes fluyen al servicio externo. Se monitorea la tasa de fallos.
2. **Open (Abierto)**: Al superar el umbral de errores (ej. 50% de timeouts), las solicitudes fallan de inmediato localmente sin contactar la red (*fail-fast*), protegiendo al servicio de destino.
3. **Half-Open (Semi-abierto)**: Tras un intervalo de enfriamiento, se permite el paso de una cantidad mínima de solicitudes de sondeo. Si responden con éxito, regresa a *Closed*; si fallan, retorna a *Open*."""),

        ("¿Cuál es la diferencia entre proceso e hilo a nivel de kernel?",
         "Procesos frente a hilos en el kernel de Linux.",
         """- **Proceso**: Entidad de ejecución con su propio espacio de direcciones virtuales, tabla de descriptores de archivos, mapa de memoria y credenciales aisladas. Su creación (`fork`) requiere duplicar estructuras de control de memoria (vía *copy-on-write*).
- **Hilo (Thread)**: Unidad de planificación dentro de un proceso. Comparte el mismo espacio de direcciones, descriptores de archivo y memoria global con los demás hilos del mismo proceso, pero posee su propia pila (*stack*) de ejecución y conjunto de registros de CPU."""),

        ("Implementa el algoritmo de Token Bucket para limitación de tasa (rate limiting) en Python.",
         "Algoritmo Token Bucket en Python.",
         """```python
import time

class TokenBucket:
    def __init__(self, capacidad: int, tasa_recarga_por_segundo: float):
        self.capacidad = float(capacidad)
        self.tokens = float(capacidad)
        self.tasa_recarga = tasa_recarga_por_segundo
        self.ultimo_tiempo = time.monotonic()

    def consumir(self, cantidad: int = 1) -> bool:
        ahora = time.monotonic()
        tiempo_transcurrido = ahora - self.ultimo_tiempo
        self.ultimo_tiempo = ahora

        # Recargar tokens proporcionalmente al tiempo transcurrido
        self.tokens = min(self.capacidad, self.tokens + tiempo_transcurrido * self.tasa_recarga)

        if self.tokens >= cantidad:
            self.tokens -= cantidad
            return True
        return False
```"""),

        ("¿Cómo usar asyncio.TaskGroup en Python 3.11+ frente a asyncio.gather?",
         "asyncio.TaskGroup vs asyncio.gather.",
         """`TaskGroup` proporciona concurrencia estructurada mediante un gestor de contexto asíncrono. Si alguna subtarea falla con una excepción, cancela automáticamente las demás tareas pendientes del grupo y propaga un `ExceptionGroup`:

```python
import asyncio

async def tarea(id_tarea: int):
    await asyncio.sleep(0.5)
    return id_tarea * 10

async def principal():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(tarea(1))
        t2 = tg.create_task(tarea(2))
    
    # Ambas tareas completadas de forma determinista
    print(t1.result(), t2.result())

asyncio.run(principal())
```"""),

        ("Escribe un ejemplo de discriminación de uniones (Discriminated Unions) en TypeScript estricto.",
         "Discriminated Unions en TypeScript.",
         """```typescript
type EstadoRespuesta = 
  | { estado: 'exito'; datos: string[]; timestamp: number }
  | { estado: 'error'; mensaje: string; codigoError: number }
  | { estado: 'cargando' };

function procesarRespuesta(res: EstadoRespuesta): string {
  switch (res.estado) {
    case 'exito':
      return `Datos recibidos: ${res.datos.length} elementos`;
    case 'error':
      return `Fallo [${res.codigoError}]: ${res.mensaje}`;
    case 'cargando':
      return 'Operacion en curso...';
  }
}
```"""),

        ("¿Qué es un índice invertido y cómo se implementa para búsqueda básica en Python?",
         "Índice invertido en Python.",
         """```python
from collections import defaultdict
from typing import Dict, List, Set

class IndiceInvertido:
    def __init__(self):
        self.indice: Dict[str, Set[int]] = defaultdict(set)

    def agregar_documento(self, doc_id: int, texto: str) -> None:
        for palabra in texto.lower().split():
            self.indice[palabra].add(doc_id)

    def buscar(self, termino: str) -> Set[int]:
        return self.indice.get(termino.lower(), set())

    def buscar_interseccion(self, terminos: List[str]) -> Set[int]:
        if not terminos:
            return set()
        resultado = self.buscar(terminos[0]).copy()
        for t in terminos[1:]:
            resultado &= self.buscar(t)
        return resultado
```"""),

        ("¿Cómo funciona la semántica de movimiento (Move Semantics) en C++?",
         "Semántica de movimiento en C++.",
         """La semántica de movimiento transfiere la propiedad de los recursos asignados en el montículo (*heap*) desde un objeto temporal (*rvalue*) hacia un nuevo objeto receptor, evitando copias profundas de memoria:

```cpp
#include <vector>
#include <utility>

std::vector<int> origen = {1, 2, 3, 4, 5};
// Transfiere el puntero al bufer interno; origen queda en estado vacio o valido pero indefinido
std::vector<int> destino = std::move(origen);
```
Se apoya en referencias a rvalue (`Type&&`) y en el constructor de movimiento `Clase(Clase&& otro) noexcept`."""),

        ("¿Cómo manejar errores de forma idiomática en Rust con `Result` y el operador `?`?",
         "Manejo de errores idiomático en Rust.",
         """```rust
use std::fs::File;
use std::io::{self, Read};

fn leer_contenido(ruta: &str) -> Result<String, io::Error> {
    let mut archivo = File::open(ruta)?; // Propaga el error inmediatamente si open falla
    let mut buffer = String::new();
    archivo.read_to_string(&mut buffer)?; // Propaga si la lectura falla
    Ok(buffer)
}
```

El operador `?` desempaqueta el valor si la variante es `Ok(T)`, o retorna anticipadamente la función con `Err(From::from(e))` si es un error."""),

        ("¿Qué es un generador de números pseudoaleatorios criptográficamente seguro (CSPRNG)?",
         "CSPRNG vs PRNG estándar.",
         """Un CSPRNG satisface dos propiedades formales:
1. **Pasa la prueba del siguiente bit**: Conociendo los primeros $k$ bits emitidos, ningún algoritmo en tiempo polinomial puede predecir el bit $k+1$ con probabilidad significativamente superior a 0.5.
2. **Resistencia a compromiso de estado**: Si el estado interno se ve comprometido, es computacionalmente inviable reconstruir la secuencia previa de números generados.
En Linux se accede mediante la llamada al sistema `getrandom()` o `/dev/urandom`."""),

        ("¿Cómo evitar la estampida de caché (Cache Stampede) en sistemas de alto tráfico?",
         "Prevención de Cache Stampede.",
         """1. **Bloqueo distribuido (*Mutual Exclusion*)**: Solo el primer proceso que detecta la expiración adquiere un bloqueo (ej. vía Redis `SET NX`) para recalcular el valor; los demás esperan o sirven el valor expirado transitoriamente.
2. **Expiración anticipada probabilística (Algoritmo XFetch)**: Recalcula el valor en segundo plano antes de la expiración real con probabilidad que crece a medida que se acerca el TTL:
$$\Delta \cdot \beta \cdot \ln(\text{rand}()) > \text{TTL} - \text{tiempo\_restante}$$
3. **Calentamiento periódico (*Background Refresh*)**: Un proceso en segundo plano actualiza la caché asíncronamente antes de su vencimiento."""),

        ("Escribe un script en Python para calcular la distancia de Levenshtein entre dos cadenas.",
         "Algoritmo de distancia de Levenshtein.",
         """```python
def distancia_levenshtein(s1: str, s2: str) -> int:
    \"\"\"Calcula el numero minimo de inserciones, eliminaciones o sustituciones. O(M*N).\"\"\"
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

    return dp[m][n]
```"""),

        ("¿Qué es un Deadlock y qué diferencia tiene con un Livelock?",
         "Deadlock frente a Livelock.",
         """- **Deadlock**: Dos o más procesos se encuentran en suspensión permanente esperando recursos retenidos entre sí; no consumen ciclos de CPU.
- **Livelock**: Dos o más procesos cambian de estado continuamente en respuesta a las acciones del otro (como cortesías mutuas de cesión de paso), pero sin progresar en la tarea útil; continúan consumiendo activamente ciclos de CPU.""")
    ]

    for q, th, resp in muestras_codigo:
        samples.append({
            "user": q,
            "think": f"""Consulta técnica: {th}
Contexto: Desarrollo de software, algoritmos e ingeniería de sistemas.
Respuesta: Código limpio, tipado y análisis directo.""",
            "response": resp
        })

    return samples
