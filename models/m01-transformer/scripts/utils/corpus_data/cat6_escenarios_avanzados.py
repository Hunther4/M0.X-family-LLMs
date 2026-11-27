r"""Categoría 6: Escenarios Avanzados de Ingeniería, Arquitectura de Sistemas y Depuración."""

def get_samples():
    samples = []

    muestras = [
        ("¿Cómo diagnosticar una fuga de memoria en un servicio en producción escrito en Python?",
         "Diagnóstico de fuga de memoria en Python.",
         """1. **Captura y comparación de instantáneas con `tracemalloc`**:
```python
import tracemalloc

tracemalloc.start()
# Capturar estado inicial
snap1 = tracemalloc.take_snapshot()

# Ejecutar carga de trabajo representativa
snap2 = tracemalloc.take_snapshot()

# Comparar diferencias de asignacion
diferencias = snap2.compare_to(snap1, 'lineno')
for stat in diferencias[:10]:
    print(stat)
```
2. **Inspección de referencias circulares con `gc` y `objgraph`**:
   - `gc.collect()` para forzar una recolección manual.
   - Si la memoria persiste alta, utilizar `objgraph.show_most_common_types()` para identificar clases con acumulación no recolectada.
3. **Paginación y fragmentación**:
   - Verificar si el acumulador de `malloc` (glibc) retiene páginas que no devuelve al sistema operativo mediante `ctypes.CDLL('libc.so.6').malloc_trim(0)`."""),

        ("Diseña una arquitectura de ingesta de eventos de telemetría a escala de 100,000 eventos por segundo.",
         "Diseño de arquitectura de ingesta de eventos a escala.",
         """1. **Capa de Borde y Balanceo (Edge Layer)**:
   - Balanceadores de carga capa 4 (L4, e.g. HAProxy / AWS NLB) terminando conexiones TCP/TLS de forma persistente.
2. **Capa de Ingesta Ligera (API Gateways)**:
   - Microservicios en Go o Rust (consumo mínimo de memoria y alta tasa de E/S asíncrona) que validan esquemas compactos en Protobuf o JSON.
3. **Búfer de Mensajería Distribuida (Streaming Bus)**:
   - Clúster de Apache Kafka o Apache Pulsar con particionado por clave de dispositivo (`device_id`) para garantizar orden y paralelismo horizontal.
4. **Capa de Procesamiento en Tiempo Real**:
   - Procesadores de flujo (Apache Flink o Kafka Streams) ejecutando agregaciones en ventanas temporales (*tumbling/sliding windows*).
5. **Almacenamiento de Series Temporales (Sink)**:
   - Inserción por lotes en bases de datos analíticas columnarizadas (ClickHouse, TimescaleDB o Apache Pinot)."""),

        ("¿Cómo optimizar un Dockerfile multi-etapa utilizando montajes de caché (`--mount=type=cache`)?",
         "Optimización de Dockerfiles con montajes de caché.",
         """```dockerfile
# syntax=docker/dockerfile:1.4
FROM python:3.11-slim AS constructor

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Reutiliza la cache de pip entre construcciones sucesivas sin guardarla en la imagen final
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

COPY --from=constructor /install /usr/local
COPY . .

USER 10001:10001
CMD ["python", "main.py"]
```"""),

        ("Explica cómo funciona la indexación B-tree en PostgreSQL ante una consulta con múltiples condiciones `WHERE a = 1 AND b > 10`.",
         "Evaluación de índices B-tree compuestos en PostgreSQL.",
         """En un índice compuesto `(a, b)`:
1. El motor de PostgreSQL desciende por el árbol buscando directamente el valor exacto `a = 1`.
2. Una vez localizado el bloque de hojas con `a = 1`, evalúa la condición de rango `b > 10` de forma secuencial sobre esa subclave ordenada sin necesidad de retroceder ni escanear ramas irrelevantes.
3. Si el índice fuera `(b, a)` en su lugar, el rango `b > 10` obligaría a revisar múltiples subárboles para verificar `a = 1`, resultando en un costo de E/S significativamente mayor."""),

        ("¿Cómo funciona el protocolo Raft para consenso distribuido y cuáles son sus estados principales?",
         "Protocolo de consenso distribuido Raft.",
         """Raft descompone el consenso en tres subproblemas independientes y gestiona tres estados por nodo:
- **Estados**:
  1. **Leader (Líder)**: Atiende las solicitudes de los clientes, añade entradas a su registro y las replica a los seguidores. Emite latidos periódicos (*heartbeats*).
  2. **Follower (Seguidor)**: Responde pasivamente a solicitudes de RPC de líderes y candidatos. Si el temporizador de elección expira sin recibir latidos, pasa a candidato.
  3. **Candidate (Candidato)**: Inicia una elección incrementando el término actual (*term*), votando por sí mismo y solicitando votos a los demás nodos. Si obtiene mayoría ($N/2 + 1$), asciende a líder."""),

        ("Implementa un Decorador en Python para reintentos con retroceso exponencial (Exponential Backoff).",
         "Decorador de reintentos con exponential backoff en Python.",
         """```python
import time
import functools
import logging
from typing import Callable, Type, Tuple

def reintentar_con_backoff(
    intentos_maximos: int = 3,
    retraso_base: float = 1.0,
    factor: float = 2.0,
    excepciones: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    def decorador(funcion: Callable) -> Callable:
        @functools.wraps(funcion)
        def envoltorio(*args, **kwargs):
            retraso = retraso_base
            for intento in range(1, intentos_maximos + 1):
                try:
                    return funcion(*args, **kwargs)
                except excepciones as e:
                    if intento == intentos_maximos:
                        raise e
                    logging.warning(f"Intento {intento} fallo: {e}. Reintentando en {retraso:.2f}s...")
                    time.sleep(retraso)
                    retraso *= factor
        return envoltorio
    return decorador
```"""),

        ("¿Qué es un socket UNIX frente a un socket TCP local (127.0.0.1) y qué ventajas ofrece?",
         "Socket de dominio UNIX vs socket TCP loopback.",
         """- **Socket de Dominio UNIX (UDS - AF_UNIX)**:
  - Mecanismo de Comunicación Entre Procesos (IPC) bidireccional gestionado enteramente en el kernel a través del sistema de archivos.
  - Omite por completo la pila de red (sin cálculo de sumas de verificación TCP/IP, sin segmentación de paquetes, sin números de secuencia).
  - Emplea transferencia directa de buffers de memoria en el kernel, logrando mayor ancho de banda y latencia sustancialmente menor (~50% menor sobrecarga que TCP loopback).
- **Socket TCP Local (AF_INET 127.0.0.1)**:
  - Atraviesa la interfaz de bucle invertido (*loopback*), requiriendo encapsulación completa de paquetes IP y control de flujo TCP."""),

        ("Escribe una especificación OpenAPI 3.0 en YAML para un endpoint de autenticación JWT.",
         "Especificación OpenAPI 3.0 para autenticación JWT.",
         """```yaml
openapi: 3.0.3
info:
  title: API de Autenticacion M0.1
  version: 1.0.0
paths:
  /api/v1/auth/login:
    post:
      summary: Iniciar sesion y obtener token JWT
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [usuario, clave]
              properties:
                usuario:
                  type: string
                  example: operador_local
                clave:
                  type: string
                  format: password
      responses:
        '200':
          description: Autenticacion exitosa
          content:
            application/json:
              schema:
                type: object
                properties:
                  token_acceso:
                    type: string
                  tipo_token:
                    type: string
                    example: Bearer
                  expira_en_segundos:
                    type: integer
                    example: 3600
        '401':
          description: Credenciales invalidas
```"""),

        ("¿Cómo funciona el reclector de basura (Garbage Collector) generacional de Python?",
         "Recolector de basura generacional en CPython.",
         """CPython utiliza principalmente **conteo de referencias**: cuando el contador de un objeto llega a 0, se desasigna de inmediato.

Para resolver **referencias circulares**, incorpora un recolector generacional cíclico:
1. **Tres generaciones (G0, G1, G2)**: Los objetos nuevos se colocan en G0. Si sobreviven a una recolección, se promueven a G1 y posteriormente a G2.
2. **Frecuencia de inspección**: G0 se examina frecuentemente; G2 se inspecciona con menor periodicidad.
3. **Detección de ciclos**: El recolector aísla temporalmente los objetos de una generación, resta a cada objeto las referencias provenientes de los demás miembros del grupo analizado y libera aquellos cuyo conteo residual sea 0."""),

        ("¿Qué es un archivo Core Dump en Linux y cómo se habilita para depurar un binario colapsado?",
         "Generación y análisis de Core Dumps en Linux.",
         """Un *Core Dump* es una copia exacta del espacio de memoria virtual y el estado de los registros de un proceso en el instante en que colapsó (ej. por `SIGSEGV` o `SIGABRT`):
1. **Habilitar tamaño ilimitado en la sesión**:
   ```bash
   ulimit -c unlimited
   ```
2. **Configurar patrón de ruta en `/proc/sys/kernel/core_pattern`**:
   ```bash
   sudo sysctl -w kernel.core_pattern=/tmp/core-%e-%p-%t
   ```
3. **Inspeccionar con GDB**:
   ```bash
   gdb ./mi_binario /tmp/core-mi_binario-12345-1680000000
   (gdb) bt full
   ```
   El comando `bt full` (*backtrace*) muestra la traza de llamadas y los valores de las variables locales al momento del fallo."""),

        ("¿Cómo mitigar ataques de denegación de servicio (DoS) por agotamiento de conexiones en Nginx?",
         "Mitigación de DoS en Nginx.",
         """```nginx
http {
    # Limitar zona de conexiones simultaneas por direccion IP
    limit_conn_zone $binary_remote_addr zone=conexiones_ip:10m;
    
    # Limitar tasa de solicitudes (10 peticiones/segundo)
    limit_req_zone $binary_remote_addr zone=tasa_ip:10m rate=10r/s;

    server {
        listen 80;

        # Aplicar limites
        limit_conn conexiones_ip 20;
        limit_req zone=tasa_ip burst=20 nodelay;

        # Reducir tiempos de espera para liberar conexiones inactivas
        client_body_timeout 10s;
        client_header_timeout 10s;
        keepalive_timeout 15s;
        send_timeout 10s;
    }
}
```"""),

        ("¿Cómo implementar un Pipeline CI/CD en GitHub Actions para pruebas automatizadas en Python?",
         "Pipeline CI en GitHub Actions para Python.",
         """```yaml
name: Integracion Continua

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  pruebas:
    runs-on: ubuntu-latest
    steps:
      - name: Descargar repositorio
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Instalar dependencias
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov ruff

      - name: Analisis estatico con Ruff
        run: ruff check .

      - name: Ejecucion de pruebas unitarias
        run: pytest --cov=src tests/
```"""),

        ("¿Cuál es la diferencia entre un índice Clustered y Non-Clustered en motores de bases de datos?",
         "Índice agrupado (Clustered) frente a no agrupado (Non-Clustered).",
         """- **Índice Agrupado (*Clustered Index*)**:
  - Dicta el orden físico de almacenamiento de las filas en las páginas del disco.
  - Los nodos hoja del árbol B+ contienen directamente las filas de datos completas.
  - Solo puede existir **uno** por tabla (frecuentemente la clave primaria).
- **Índice No Agrupado (*Non-Clustered Index*)**:
  - Estructura desacoplada del orden físico de los datos.
  - Los nodos hoja contienen las columnas indexadas y un puntero (*Row Locator* o clave primaria) a la fila en el almacenamiento base.
  - Pueden existir múltiples índices no agrupados por tabla."""),

        ("Explica la diferencia entre sincronización basada en memoria compartida y paso de mensajes en sistemas concurrentes.",
         "Memoria compartida vs paso de mensajes.",
         """- **Memoria Compartida**:
  - Los hilos acceden y modifican las mismas direcciones de memoria física.
  - Comunicación a través de variables compartidas; requiere sincronización manual explícita (mutex, semáforos, barreras) para evitar condiciones de carrera.
  - Alto rendimiento pero proclive a deadlocks y bugs de contención de memoria.
- **Paso de Mensajes (e.g. Canales en Go / Modelo de Actores en Erlang)**:
  - Los procesos o hilos son independientes y no comparten estado en memoria.
  - La sincronización se produce al enviar y recibir mensajes estructurados por canales o colas.
  - Filosofía: *«No te comuniques compartiendo memoria; comparte memoria comunicándote»*."""),

        ("¿Cómo configurar swapiness en Linux para optimizar un servidor de base de datos?",
         "Configuración de vm.swappiness en Linux.",
         """Para servidores de bases de datos (PostgreSQL, MySQL, Redis), se recomienda un valor bajo de `vm.swappiness` (entre 1 y 10) para evitar que el sistema traslade páginas de datos activas al espacio swap antes de agotar la RAM:

1. **Verificar valor actual**:
   ```bash
   cat /proc/sys/vm/swappiness
   ```
2. **Ajuste temporal en caliente**:
   ```bash
   sudo sysctl -w vm.swappiness=10
   ```
3. **Persistir el cambio en reinicios**:
   Añadir la siguiente línea a `/etc/sysctl.conf` o a `/etc/sysctl.d/99-swappiness.conf`:
   ```ini
   vm.swappiness = 10
   ```
   Aplicar con `sudo sysctl -p`."""),

        ("¿Cómo funciona el protocolo TCP Slow Start?",
         "TCP Slow Start y control de congestión.",
         """El arranque lento (*Slow Start*) es la fase inicial del control de congestión en TCP:
1. Comienza con una ventana de congestión pequeña ($CWND = 1 \text{ a } 10 \text{ MSS}$).
2. Por cada paquete confirmado exitosamente con un `ACK`, el emisor incrementa la $CWND$ en un segmento, duplicando la ventana por cada tiempo de ida y vuelta (*Round Trip Time*, RTT) (crecimiento exponencial: $1 \to 2 \to 4 \to 8 \dots$).
3. Continúa hasta alcanzar el umbral de arranque lento (*ssthresh*), punto en el que pasa a la fase de **Evitación de Congestión** (*Congestion Avoidance*), donde el crecimiento se torna lineal (+1 segmento por RTT)."""),

        ("¿Qué es la inversión de prioridades en sistemas de tiempo real y cómo se resuelve?",
         "Inversión de prioridades y protocolo de herencia de prioridad.",
         """La inversión de prioridades ocurre cuando una tarea de alta prioridad se ve indirectamente bloqueada por una tarea de baja prioridad que retiene un recurso compartido, mientras una tarea de prioridad media desaloja a la tarea baja impidiéndole liberar el recurso.

**Solución formal: Protocolo de Herencia de Prioridad (*Priority Inheritance Protocol*)**:
- Cuando una tarea de alta prioridad intenta adquirir un bloqueo en manos de una tarea de baja prioridad, la tarea de baja prioridad hereda temporalmente la prioridad más alta mientras sostenga dicho bloqueo.
- Esto impide que tareas intermedias la desalojen, permitiéndole finalizar rápidamente la sección crítica y ceder el control a la tarea de alta prioridad."""),

        ("Implementa un verificador de paréntesis balanceados en C++ usando `std::stack`.",
         "Verificador de paréntesis balanceados en C++.",
         """```cpp
#include <iostream>
#include <stack>
#include <string>
#include <unordered_map>

bool estan_parentesis_balanceados(const std::string& expresion) {
    std::stack<char> pila;
    const std::unordered_map<char, char> pares = {
        {')', '('},
        {']', '['},
        {'}', '{'}
    };

    for (char c : expresion) {
        if (c == '(' || c == '[' || c == '{') {
            pila.push(c);
        } else if (pares.count(c)) {
            if (pila.empty() || pila.top() != pares.at(c)) {
                return false;
            }
            pila.pop();
        }
    }
    return pila.empty();
}
```"""),

        ("¿Cómo estructurar un proyecto en Go según las convenciones estándar de la comunidad?",
         "Estructura estándar de proyectos en Go.",
         """```text
mi-proyecto/
├── cmd/
│   └── servidor/
│       └── main.go       # Punto de entrada de la aplicacion
├── internal/             # Codigo privado no exportable a otros modulos
│   ├── dominio/          # Entidades y logica de negocio pura
│   ├── repositorio/      # Acceso a base de datos y persistencia
│   └── servicio/         # Casos de uso y coordinacion
├── pkg/                  # Codigo publico reutilizable por terceros
├── api/                  # Especificaciones OpenAPI / Protobuf
├── go.mod
└── go.sum
```"""),

        ("¿Qué es un ataque de inyección de comandos en el sistema operativo y cómo se previene en Python?",
         "Prevención de inyección de comandos en Python.",
         """Ocurre cuando entradas externas no saneadas se pasan a una shell del sistema operativo (como `os.system` o `shell=True` en `subprocess`).

```python
import subprocess
from typing import List

# VULNERABLE:
# os.system(f"ping -c 1 {ip_usuario}") # Si ip_usuario es "127.0.0.1; rm -rf /"

# SEGURO: Pasar argumentos como lista y mantener shell=False (por defecto)
def ping_seguro(direccion_ip: str) -> int:
    comando: List[str] = ["ping", "-c", "1", direccion_ip]
    resultado = subprocess.run(comando, capture_output=True, text=True, check=False)
    return resultado.returncode
```""")
    ]

    for q, th, resp in muestras:
        samples.append({
            "user": q,
            "think": f"""Consulta técnica: {th}
Contexto: Ingeniería de software, depuración y arquitectura.
Respuesta: Directa, precisa y rigurosa en español neutro.""",
            "response": resp
        })

    return samples
