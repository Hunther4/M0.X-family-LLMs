"""
Categoría 4: Comparaciones técnicas de opciones (A vs B) (20 escenarios)
Bloques <think> concisos de retrospectiva contextual y evaluación comparativa.
"""

SCENARIOS_CAT4 = [
    {
        "user": "Estamos diseñando una plataforma SaaS que recopilará telemetría de 50.000 sensores IoT (temperatura, ubicación, estado cada 10 s) y además gestionará facturación, usuarios y permisos corporativos. El equipo debate entre PostgreSQL (con TimescaleDB) y MongoDB. ¿Cuál es la elección arquitectónica superior?",
        "think": "Contexto: Plataforma que combina alta ingesta de series temporales IoT con facturación relacional ACID.\nEvaluación: MongoDB almacena documentos flexibles pero sufre en transacciones ACID complejas; PostgreSQL con TimescaleDB gestiona series temporales y negocio relacional en un solo motor.\nConclusión: Elegir PostgreSQL con extensión TimescaleDB.",
        "assistant": """Para un sistema que combina **series temporales intensivas (IoT) con facturación y control de accesos corporativo**, la elección indiscutible es **PostgreSQL con la extensión TimescaleDB**:

### 1. La Trampa de Elegir MongoDB
- Aunque MongoDB gestiona bien esquemas dinámicos JSON, la gestión de suscripciones, pagos, facturas y auditorías contables requiere garantías **ACID estrictas, integridad referencial y claves foráneas**. Las transacciones multidocumento en Mongo tienen penalizaciones de rendimiento notables.
- La compresión de series temporales en MongoDB es significativamente menos eficiente que en motores especializados, lo que multiplicará vuestro coste de almacenamiento en disco a medida que crezca el histórico de sensores.

### 2. Por qué PostgreSQL + TimescaleDB es Superior
- **Un Solo Motor Operativo:** Evitáis el dolor de sincronizar dos bases de datos distintas (una para negocio y otra para telemetría).
- **Hypertables y Compresión Automática:** TimescaleDB particiona automáticamente las tablas temporales en bloques (*chunks*) por tiempo y espacio. Aplica compresión columnar que **reduce el tamaño de los datos IoT entre un 90% y un 95%**, acelerando las consultas de agregación analítica de forma brutal.
- **SQL Estándar:** Vuestro equipo puede cruzar la telemetría del sensor directamente con la tabla de clientes mediante un simple `JOIN` SQL estándar sin duplicar datos."""
    },
    {
        "user": "Nuestra aplicación móvil de medios y contenidos editoriales consume actualmente una API REST con 25 endpoints. El equipo de frontend propone migrar a GraphQL para resolver el problema de sobre-recuperación de datos (over-fetching). El equipo de backend teme por la complejidad de caché y seguridad. ¿Compensa dar el salto a GraphQL?",
        "think": "Contexto: App editorial debatiendo migración de REST a GraphQL para evitar over-fetching.\nEvaluación: GraphQL flexibiliza consultas en cliente pero destruye la caché HTTP estándar (CDN) y añade complejidad n+1.\nConclusión: Mantener REST optimizando endpoints con payloads específicos o sparse fieldsets.",
        "assistant": """En una aplicación de medios y contenidos editoriales, **NO compensa migrar a GraphQL**. Resolver el *over-fetching* introduciendo GraphQL suele generar problemas mucho más graves para vuestro caso de uso:

### 1. La Destrucción de la Caché en CDN
- Las aplicaciones editoriales tienen un patrón de tráfico de **alta lectura y poca escritura** (miles de usuarios leyendo las mismas noticias).
- Con **REST**, las peticiones `GET /api/articulos/123` se cachean trivialmente en CDNs perimetrales (Cloudflare, Fastly) y en el navegador mediante cabeceras estándar `Cache-Control`. El 90% del tráfico ni siquiera toca vuestros servidores.
- Con **GraphQL**, casi todas las peticiones se realizan por `POST` contra un único endpoint `/graphql`. Cachear respuestas dinámicas exige configuraciones complejas en la capa de aplicación o el uso de *Persisted Queries*, perdiendo la simplicidad de la web.

### 2. Sobrecarga de Backend y Problema N+1
- Las consultas anidadas flexibles de GraphQL permiten que un frontend despistado solicite relaciones profundas que colapsen la base de datos con el problema de consultas N+1 salvo que implementes *DataLoaders* en cada resolver.

### 3. La Solución Limpia sin GraphQL
Mantened REST y aplicad **Sparse Fieldsets** o endpoints especializados para móviles:
- Permitid parámetros como `/api/articulos?fields=id,titulo,portada,autor` para enviar solo lo que la pantalla necesita. Reduciréis el consumo de datos móviles sin hipotecar vuestra arquitectura."""
    },
    {
        "user": "Tenemos una arquitectura de microservicios contenerizados en Docker con tráfico muy variable (picos repentinos de tráfico diurno y casi cero por la noche). Estamos decidiendo entre desplegar en AWS ECS con Fargate o en Google Cloud Run. ¿Cuáles son las diferencias críticas de coste y latencia?",
        "think": "Contexto: Microservicios en contenedores con tráfico muy variable evaluando AWS ECS Fargate vs Cloud Run.\nEvaluación: Fargate tarda 40-70 s en escalar y cobra por contenedor activo continuo; Cloud Run escala a cero y arranca en milisegundos.\nConclusión: Google Cloud Run es superior para tráfico elástico e intermitente.",
        "assistant": """Para cargas de trabajo con **tráfico altamente fluctuante y periodos de inactividad nocturna**, **Google Cloud Run supera claramente a AWS ECS con Fargate**:

### 1. Escala a Cero Real (Scale-to-Zero) y Costes
- **AWS ECS Fargate:** No escala a cero por petición HTTP. Debes tener como mínimo 1 tarea corriendo permanentemente (coste fijo 24/7). Además, Fargate factura por segundo con un mínimo de 1 minuto, independientemente de que lleguen peticiones o no.
- **Google Cloud Run:** Implementa un verdadero modelo serverless por petición: **si no hay peticiones entrantes, las instancias se apagan por completo y el coste es estrictamente 0 €**. Solo pagas por los milisegundos exactos que tarda en procesarse cada solicitud.

### 2. Velocidad de Escalado y Arranque en Frío (*Cold Starts*)
- **Fargate:** Cuando se produce un pico de tráfico, aprovisionar una nueva tarea en ECS tarda entre **45 y 90 segundos** (arranque de VM subyacente, descarga de imagen y registro en el balanceador de carga ALB). Los usuarios experimentarán tiempos de espera si el tráfico crece en ráfagas.
- **Cloud Run:** Aprovecha la tecnología de micro-VMs gVisor de Google. Puede instanciar un contenedor nuevo en **menos de 400 a 800 milisegundos** y escalar de 0 a 500 instancias casi de forma instantánea.

### 3. Veredicto
Si no estáis atados contractualmente al ecosistema de AWS, **Google Cloud Run** reducirá vuestra factura a una fracción y absorberá los picos de tráfico con mayor soltura."""
    },
    {
        "user": "Estamos seleccionando el motor de almacenamiento en caché para una plataforma web con 100.000 usuarios concurrentes. Necesitamos gestionar sesiones de usuario, contadores de visitas en tiempo real y listas de clasificación (leaderboards). El equipo debate entre Redis y Memcached. ¿Cuál se ajusta mejor?",
        "think": "Contexto: Caché distribuida para sesiones, contadores en tiempo real y leaderboards.\nEvaluación: Memcached es un almacén simple de clave-valor multihilo; Redis ofrece estructuras de datos ricas (Sorted Sets) y persistencia.\nConclusión: Redis es la única opción que soporta leaderboards y tipos complejos de forma nativa.",
        "assistant": """Para este conjunto de requerimientos, **la elección obligada es Redis**. Memcached queda descartado por sus limitaciones estructurales:

### 1. La Razón Decisiva: Estructuras de Datos Nativas
- **Leaderboards (Tablas de Clasificación):** Redis incorpora de forma nativa la estructura **Sorted Sets (ZSET)**. Te permite insertar puntuaciones de usuarios y consultar el Top 100 o el rango de un usuario con complejidad logarítmica `O(log(N))` mediante comandos directos como `ZREVRANGE` o `ZRANK`. En Memcached tendrías que descargar un array masivo al servidor de aplicaciones, ordenarlo en memoria y volver a subirlo serializado, provocando colapsos de concurrencia.
- **Contadores Atómicos:** Redis ofrece operaciones atómicas seguras (`INCR`, `HINCRBY`) ideales para métricas en vivo.

### 2. Persistencia y Recuperación de Sesiones
- Si un nodo de caché se reinicia, **Memcached pierde el 100% de los datos** en memoria, lo que cerraría la sesión simultáneamente a tus 100.000 usuarios y enviaría una avalancha de autenticaciones directas contra tu base de datos principal (*cache stampede*).
- **Redis** soporta persistencia RDB y AOF, permitiendo reiniciar el servicio o migrar nodos sin perder las sesiones activas.

### 3. Cuándo se Usaría Memcached
Memcached solo se prefiere en arquitecturas muy simples de almacenamiento masivo de objetos estáticos serializados (ej. fragmentos de HTML) donde se necesita exprimir procesamiento multihilo puro en una única máquina gigante."""
    },
    {
        "user": "Nuestra corporación bancaria exige eliminar el demonio de Docker de los servidores de desarrollo y producción para cumplir con políticas estrictas de seguridad (prohibir procesos corriendo como root). El equipo de infraestructura propone adoptar Podman. ¿Qué impacto real tiene frente a Docker y qué fricciones debemos anticipar?",
        "think": "Contexto: Migración corporativa de Docker a Podman motivada por seguridad rootless.\nEvaluación: Podman ejecuta sin demonio central ni privilegios de root pero presenta pequeñas fricciones en Docker Compose y sockets de CI.\nConclusión: Adoptar Podman configurando subuid/subgid y compatibilidad con podman-docker.",
        "assistant": """La transición de Docker a Podman es una de las decisiones más acertadas en entornos corporativos con estrictas políticas de cumplimiento de seguridad:

### 1. Ventajas de Seguridad de Podman
- **Arquitectura sin Demonio (*Daemonless*):** Docker utiliza un demonio central (`dockerd`) que corre obligatoriamente como `root`. Si un atacante compromete el demonio o el socket `/var/run/docker.sock`, obtiene control total de la máquina anfitriona. Podman utiliza el estándar OCI (*runC / crun*): cada contenedor es un proceso hijo directo del usuario que lo lanza.
- **Rootless por Defecto:** Un usuario sin privilegios puede crear y ejecutar contenedores. Si un contenedor se ve vulnerado, el atacante queda atrapado en el espacio de nombres de usuario (*user namespace*) sin privilegios sobre el sistema anfitrión.

### 2. Fricciones Reales a Anticipar y Soluciones
1. **Mapeo de Puertos Privilegiados (<1024):**
   - Un usuario no-root en Linux no puede escuchar en el puerto 80 o 443 por defecto.
   - *Solución:* Ajustar en `/etc/sysctl.conf` el parámetro `net.ipv4.ip_unprivileged_port_start=80`.
2. **Pipelines de CI/CD (Docker-in-Docker):**
   - Si vuestros scripts de CI ejecutan `docker build` dentro de un contenedor, con Podman debéis habilitar el servicio de socket compatible con Docker (`systemctl --user enable --now podman.socket`).
3. **Docker Compose:**
   - Instala `podman-compose` o utiliza directamente Docker Compose apuntando la variable de entorno `DOCKER_HOST` al socket de usuario de Podman.

En la práctica diaria, el alias `alias docker=podman` hace que el 98% de los comandos y Dockerfiles funcionen de forma idéntica y transparente."""
    },
    {
        "user": "Estamos seleccionando el servidor web y proxy inverso para una flota de 15 microservicios web. Dudamos entre el clásico Nginx y el moderno Caddy. ¿Qué ventajas prácticas aporta Caddy y en qué escenarios sigue reinando Nginx?",
        "think": "Contexto: Elección de proxy inverso entre Nginx y Caddy para 15 microservicios.\nEvaluación: Caddy gestiona TLS automático con Let's Encrypt y configuración ultra limpia; Nginx ofrece rendimiento bruto probado y módulos C maduros.\nConclusión: Caddy para equipos ágiles que buscan cero fricción de certificados; Nginx para tráfico masivo extremo.",
        "assistant": """La comparativa entre Nginx y Caddy enfrenta al **estándar histórico de rendimiento en C** frente a la **experiencia de desarrollo moderna en Go**:

### 1. La Gran Ventaja de Caddy: Certificados HTTPS Automáticos
- **Caddy** automatiza de forma nativa la obtención, instalación y renovación periódica de certificados SSL/TLS con Let's Encrypt o ZeroSSL. No necesitas instalar `certbot`, configurar crons externos ni preocuparte jamás por la caducidad de un certificado.
- **Sintaxis de Configuración Limpia (Caddyfile):** Lo que en Nginx exige 35 líneas de configuración con bloques `upstream`, cabeceras de proxy y certificados, en Caddy se resuelve en 4 líneas:
  ```caddyfile
  api.empresa.com {
      reverse_proxy localhost:8080
  }
  ```

### 2. Dónde Sigue Siendo Insuperable Nginx
- **Rendimiento Extremo y Huella de Memoria:** Nginx está escrito en C sobre arquitectura event-driven con uso de memoria estático (<20 MB). Soporta cientos de miles de conexiones concurrentes por máquina sin pausas de recolección de basura (*GC pauses*). Caddy consume más memoria base (50-100 MB).
- **Ecosistema de Módulos y OpenResty:** Si necesitas ejecutar scripts Lua en el proxy, balanceo de carga con algoritmos exóticos o integraciones WAF complejas (ModSecurity), Nginx dispone de una madurez inalcanzable.

### 3. Veredicto
- Elige **Caddy** para arquitecturas cloud, microservicios estándar y APIs donde el tiempo de configuración y la automatización de certificados ahorren semanas de trabajo operativo.
- Elige **Nginx** en nodos perimetrales de tráfico masivo extremo (>100.000 req/s) o cuando la huella de memoria sea un recurso crítico."""
    },
    {
        "user": "Nuestra arquitectura de microservicios bancarios debe implementar comunicación asíncrona para notificaciones, pagos y liquidaciones. El equipo debate entre Apache Kafka y RabbitMQ. ¿Cuál es el criterio técnico fundamental para elegir uno u otro?",
        "think": "Contexto: Elección de broker de mensajería para banco entre Kafka y RabbitMQ.\nEvaluación: RabbitMQ es un broker de colas inteligente con enrutamiento flexible pero efímero; Kafka es un log distribuido inmutable rejugable.\nConclusión: Kafka si se requiere auditoría y rejugabilidad de eventos; RabbitMQ para colas complejas de tareas puntuales.",
        "assistant": """La diferencia fundamental entre Apache Kafka y RabbitMQ no es el rendimiento, sino su **modelo conceptual de gestión de mensajes**:

### 1. El Concepto Clave: Cola de Mensajes vs. Log Distribuido Inmutable
- **RabbitMQ (Broker Inteligente / Consumidor Tonto):**
  - Es una **cola de mensajes tradicional**. El broker enruta los mensajes con reglas complejas (direct, fanout, topic) a las colas correspondientes.
  - Cuando un consumidor procesa un mensaje y envía el acuse de recibo (*ACK*), **el mensaje se destruye y desaparece de la cola**.
- **Apache Kafka (Broker Tonto / Consumidor Inteligente):**
  - Es un **log de eventos secuencial, distribuido y persistente**. Los mensajes se escriben en disco y no se borran tras ser leídos; se conservan según una política de retención (días, meses o para siempre).
  - Cada consumidor mantiene su propio puntero (*offset*) y puede rebobinar en el tiempo para volver a leer eventos pasados.

### 2. Matriz de Decisión para Banca

| Criterio | RabbitMQ | Apache Kafka |
| :--- | :--- | :--- |
| **Enrutamiento complejo** | **Excelente** (Exchanges AMQP avanzados) | Básico (por clave de partición a topic) |
| **Auditoría y Reprocesamiento** | Imposible (el mensaje se elimina al leerlo) | **Nativo** (Puedes volver a procesar todas las transacciones del año) |
| **Tolerancia a Caídas de Consumidores** | La cola se llena en memoria | El log en disco absorbe terabytes sin inmutarse |
| **Complejidad Operativa** | **Baja-Media** (Muy fácil de operar) | Alta (Requiere clúster KRaft o Zookeeper) |

### 3. Veredicto
- Para **liquidaciones contables, pagos y pistas de auditoría financiera**: **Apache Kafka** es insustituible porque permite reproducir transacciones en caso de fallo contable (*Event Sourcing*).
- Para **notificaciones transaccionales a usuarios (envío de SMS, emails, avisos push)**: **RabbitMQ** es mucho más simple y rápido de mantener."""
    },
    {
        "user": "Tenemos que construir un microservicio de ingesta de datos de alta velocidad que recibirá 15.000 peticiones JSON concurrentes por segundo procedentes de pasarelas de pago. El equipo duda entre desarrollarlo en Python con FastAPI o en Go con Gin/Fiber. ¿Qué métricas justifican el cambio a Go?",
        "think": "Contexto: Microservicio de ingesta de 15.000 req/s evaluando FastAPI vs Go.\nEvaluación: FastAPI es asíncrono pero el GIL de Python y el coste de serialización saturan CPU; las goroutines de Go escalan de forma masiva.\nConclusión: Go es la elección arquitectónica obligada para procesar 15k req/s con bajo coste de cómputo.",
        "assistant": """Para procesar **15.000 peticiones JSON concurrentes por segundo**, la elección técnica debe ser **Go**. Aunque FastAPI es un framework asíncrono excelente, la física de la ejecución de Python hace inviable ese volumen sin una flota sobredimensionada de servidores:

### 1. Comparativa de Rendimiento y Recursos

| Métrica | Python (FastAPI + Uvicorn) | Go (Gin / Fiber / Chi) |
| :--- | :--- | :--- |
| **Concurrencia real** | Limitada por proceso (GIL); exige 1 worker por CPU core | **Goroutines nativas** (2 KB de RAM por hilo, multiplexado masivo) |
| **Rendimiento por instancia** | ~2.500 - 3.500 req/s por contenedor multi-worker | **25.000 - 45.000 req/s** por contenedor |
| **Consumo de Memoria RAM** | ~150 - 250 MB por worker | **~15 - 30 MB en total** |
| **Serialización JSON** | Lenta (sobrecarga de validación Pydantic en runtime) | Ultra-rápida (compilado estático nativo) |
| **Coste en Infraestructura Cloud** | Exige 8 a 10 instancias EC2 grandes | **1 o 2 instancias medianas** bastan |

### 2. El Impacto de las Goroutines
- En Python, una petición que espera I/O bloquea el bucle de eventos (*event loop*) si se ejecutan transformaciones de datos intermedias en CPU.
- En Go, las peticiones se atienden en goroutines ultraligeras distribuidas por el planificador interno de Go entre todos los núcleos de CPU disponibles, garantizando una latencia p99 inferior a **8 milisegundos**.

### 3. Veredicto
Utiliza **FastAPI** para APIs con lógica de negocio compleja, integración con modelos de machine learning o paneles administrativos. Pero para un **pipeline de ingesta bruta de alta velocidad**, Go te ahorrará miles de euros en facturas cloud y garantizará estabilidad absoluta."""
    },
    {
        "user": "Estamos iniciando una gran aplicación corporativa en React y Next.js. El equipo de diseño aboga por Styled-Components / Emotion (CSS-in-JS), mientras que los desarrolladores senior defienden Tailwind CSS. ¿Cuál es el impacto en rendimiento y arquitectura?",
        "think": "Contexto: Proyecto grande en Next.js debatiendo entre CSS-in-JS (Styled Components) y Tailwind CSS.\nEvaluación: CSS-in-JS tradicional es incompatible con React Server Components e incrementa el tamaño del bundle JS; Tailwind genera CSS atómico compilado en build.\nConclusión: Tailwind CSS es la opción correcta para el ecosistema moderno de Next.js.",
        "assistant": """En el ecosistema moderno de React y Next.js (App Router), la elección indiscutible es **Tailwind CSS**. Adoptar librerías CSS-in-JS tradicionales como Styled-Components o Emotion supone un paso atrás en rendimiento y compatibilidad:

### 1. La Incompatibilidad Crítica con React Server Components (RSC)
- Las librerías de CSS-in-JS como `styled-components` dependen del contexto de React en tiempo de ejecución en el cliente para inyectar etiquetas `<style>` en el DOM.
- **Son incompatibles con los componentes de servidor (RSC):** Te obligan a marcar prácticamente todos los componentes con `'use client'`, deshabilitando la mayor ventaja arquitectónica de Next.js (el renderizado en servidor sin JavaScript en el cliente).

### 2. Rendimiento en el Navegador y Tamaño del Bundle
- **Styled-Components:** Cada render recalcula clases y genera estilos en JavaScript en tiempo de ejecución, lo que satura el hilo principal del navegador en páginas con cientos de componentes.
- **Tailwind CSS:** Se compila **100% en tiempo de compilación (build-time)**. Escanea tu código y genera una única hoja de estilos CSS estática ultra-optimizada (habitualmente <15 KB gzippeada). No añade ni un solo byte de JavaScript al paquete final.

### 3. Mantenimiento y Sistema de Diseño
- Tailwind estandariza el diseño mediante una escala coherente de espaciados, colores y tipografías en el archivo `tailwind.config.ts`, evitando que cada programador invente valores arbitrarios de píxeles o márgenes en estilos sueltos."""
    },
    {
        "user": "Vamos a crear un portal administrativo interno para 200 empleados de una aseguradora (paneles de gestión, tablas de datos y formularios). El equipo debate si usar Next.js con Server-Side Rendering o una SPA tradicional construida con Vite + React. ¿Qué arquitectura es más eficiente?",
        "think": "Contexto: Portal administrativo interno corporativo para 200 empleados.\nEvaluación: SSR aporta SEO y carga pública que aquí no importan; una SPA en Vite es más barata de alojar y rápida de iterar.\nConclusión: Vite + React SPA servida desde CDN/S3 estático.",
        "assistant": """Para un portal administrativo privado de uso interno para 200 empleados, **Vite + React (SPA tradicional) es una arquitectura mucho más sencilla, económica y adecuada que Next.js**:

### 1. Por qué Next.js (SSR) Aporta Poco en una Intranet
- **SEO Inexistente:** Las páginas están detrás de un login privado con credenciales corporativas; los motores de búsqueda de Google tienen el acceso bloqueado, por lo que el renderizado en servidor por posicionamiento es irrelevante.
- **Alojamiento y Coste de Servidores:** Next.js con SSR exige un servidor Node.js corriendo 24/7 (en ECS, Vercel o EC2) con autoescalado y parches de seguridad continuos.
- **Complejidad Innecesaria:** Manejar cookies de servidor, revalidaciones de caché y límites de cliente/servidor añade fricción al equipo para construir simples pantallas CRUD.

### 2. Las Ventajas de Vite + React SPA
- **Alojamiento Estático Ultra-Barato:** Una SPA compilada son solo archivos planos (`index.html`, `bundle.js`, `style.css`). Se pueden alojar en un bucket **AWS S3 con CloudFront o Cloudflare Pages por céntimos al mes**, con disponibilidad del 99,99% y cero mantenimiento de servidores.
- **Experiencia de Usuario en Gestión de Datos:** Una vez cargada la app la primera vez, la navegación entre pantallas, filtrado de tablas y envío de formularios es instantánea y no requiere descargas adicionales del servidor.
- **Velocidad de Desarrollo:** El entorno local de Vite con HMR (*Hot Module Replacement*) arranca en milisegundos y permite iterar pantallas administrativas con librerías como TanStack Table y Shadcn UI a máxima velocidad."""
    },
    {
        "user": "Nuestros microservicios internos necesitan intercambiar datos bidireccionales y flujos de eventos entre servicios de streaming de audio. El equipo técnico debate entre utilizar gRPC sobre HTTP/2 o WebSockets. ¿Cuál es el protocolo adecuado para la comunicación servicio a servicio?",
        "think": "Contexto: Comunicación bidireccional y streaming entre microservicios de backend.\nEvaluación: WebSockets carece de tipado estricto y multiplexación de llamadas; gRPC ofrece buffers binarios compactos con contratos Protobuf.\nConclusión: gRPC es la elección idónea para comunicación interna entre microservicios.",
        "assistant": """Para la comunicación interna **servicio a servicio en el backend**, **gRPC es categóricamente superior a WebSockets**:

### 1. El Contrato Estricto con Protocol Buffers
- **gRPC** utiliza **Protobuf**: un formato binario fuertemente tipado. El contrato de la interfaz se define en archivos `.proto` a partir de los cuales se autogenera el código del cliente y del servidor en cualquier lenguaje (Go, Python, Java). No hay riesgo de desajustes de nombres de campos o tipos en runtime.
- **WebSockets** es solo un protocolo de transporte de bajo nivel. No impone ningún formato a los datos: debes implementar manualmente la serialización JSON, validaciones de esquemas y control de versiones de endpoints.

### 2. Eficiencia y Multiplexación HTTP/2
- gRPC corre sobre **HTTP/2**: permite multiplexar cientos de llamadas y streams bidireccionales simultáneos sobre una **única conexión TCP persistente**. La cabecera se comprime con HPACK y el payload binario es entre un 60% y un 80% más pequeño que el JSON equivalente en WebSockets.
- Soporta de forma nativa los 4 patrones de comunicación: Unario (petición/respuesta simple), Server Streaming, Client Streaming y Streaming Bidireccional.

### 3. Cuándo se Emplea WebSockets
WebSockets es el estándar para la comunicación entre **el navegador web del cliente final y el servidor**, donde los navegadores tienen soporte limitado para gRPC nativo sin proxies intermedios (como gRPC-Web). Pero en el backend privado, gRPC es el estándar de la industria."""
    },
    {
        "user": "Estamos desarrollando una aplicación de escritorio para analistas financieros que debe consultar y agregar millones de registros históricos localmente en la máquina del usuario sin requerir un servidor de base de datos. Dudamos entre embeber SQLite o DuckDB. ¿Cuál ofrece mejor rendimiento para análisis OLAP?",
        "think": "Contexto: Motor de base de datos embebido local para análisis de millones de registros financieros.\nEvaluación: SQLite es un motor transaccional por filas (OLTP); DuckDB es un motor columnar vectorizado (OLAP) optimizado para analítica.\nConclusión: DuckDB es órdenes de magnitud más rápido en agregaciones y consultas analíticas locales.",
        "assistant": """Para consultas analíticas y agregaciones masivas sobre millones de registros en local, **DuckDB es abrumadoramente superior a SQLite**:

### 1. Almacenamiento Columnar vs. Orientado a Filas (OLAP vs. OLTP)
- **SQLite (Orientado a Filas):** Almacena los registros completos fila por fila. Si ejecutas una consulta tipo `SELECT AVG(precio), SUM(volumen) FROM transacciones WHERE fecha > '2023-01-01'`, SQLite tiene que leer de disco todas las columnas de cada fila (nombres, descripciones, cuentas), saturando el ancho de banda de memoria.
- **DuckDB (Almacenamiento Columnar):** Diseñado específicamente para analítica (el "SQLite para OLAP"). Almacena cada columna por separado en bloques contiguos. Para calcular el promedio de precios, **solo lee los bytes de la columna precio**, ignorando todo lo demás.

### 2. Ejecución Vectorizada y Paralelismo Multihilo
- DuckDB procesa los datos en bloques vectorizados utilizando instrucciones SIMD de la CPU moderna y aprovecha automáticamente todos los núcleos de CPU de la máquina.
- Consultas analíticas pesadas (sumas, agrupaciones `GROUP BY`, joins complejos de millones de filas) que en SQLite tardan 40 segundos, **en DuckDB se resuelven en menos de 400 milisegundos**.

### 3. Integración Nativa con Formatos Modernos
- DuckDB puede consultar directamente archivos locales **Parquet, CSV y JSON sin necesidad de importarlos previamente** a la base de datos.
- Utiliza **SQLite** si tu aplicación realiza escrituras individuales concurrentes frecuentes (un almacén transaccional); utiliza **DuckDB** para exploración analítica intensiva."""
    },
    {
        "user": "Nuestra plataforma de e-commerce con 120.000 productos necesita renovar su motor de búsqueda interno. El catálogo exige búsqueda tolerante a erratas, filtrado por categorías y facetas de precios en tiempo real. Estamos entre Elasticsearch y Meilisearch. ¿Cuál deberíamos adoptar?",
        "think": "Contexto: Buscador para catálogo de 120.000 productos con búsqueda instantánea y tolerancia a fallos.\nEvaluación: Elasticsearch es un monstruo de recursos diseñado para petabytes y logs; Meilisearch está optimizado para búsqueda instantánea en comercio con mínima configuración.\nConclusión: Meilisearch por velocidad de integración, tolerancia a erratas nativa y bajo consumo de memoria.",
        "assistant": """Para un catálogo de 120.000 productos de comercio electrónico, **Meilisearch es la elección perfecta**:

### 1. El Sobredimensionamiento de Elasticsearch
- Elasticsearch es una herramienta industrial colosal diseñada para procesar terabytes de logs distribuidos en clústeres empresariales masivos.
- Exige una máquina dedicada con JVM (Java) de al menos 4 a 8 GB de RAM solo para arrancar, y su configuración para conseguir una búsqueda con tolerancia a erratas (*fuzzy matching*) y ordenación por relevancia comercial requiere semanas de tuning de analizadores y tokenizadores complejos.

### 2. La Magia de Meilisearch para E-commerce
- **Búsqueda Instantánea mientras Escribes (*Search-as-you-type*):** Escrito en Rust, responde consultas en menos de **15 milisegundos**, devolviendo resultados en vivo conforme el cliente teclea en el buscador.
- **Tolerancia a Erratas Nativa:** Corrige automáticamente faltas tipográficas (*typos*) sin necesidad de configurar diccionarios complejos.
- **Filtros y Facetas Inmediatos:** Configurar filtrado por marca, rango de precios o disponibilidad de stock se define en 3 líneas de configuración.
- **Consumo de Recursos Ridículo:** Para 120.000 productos, el índice completo de Meilisearch ocupa menos de 400 MB de RAM y arranca en un binario ligero sin dependencias.

### 3. Veredicto
Reserva **Elasticsearch** si gestionas decenas de millones de documentos con análisis de logs a escala masiva. Para experiencia de búsqueda de usuario en una tienda online, **Meilisearch** te proporcionará una experiencia superior al nivel de Amazon en una tarde de trabajo."""
    },
    {
        "user": "El equipo de ingeniería de infraestructura debate sobre qué herramienta estandarizar para Infraestructura como Código (IaC): el veterano Terraform con lenguaje declarativo HCL, o Pulumi utilizando lenguajes de programación estándar como TypeScript o Python. ¿Qué ventajas y riesgos presenta cada enfoque?",
        "think": "Contexto: Estandarización de IaC entre Terraform (HCL) y Pulumi (TypeScript/Python).\nEvaluación: HCL limita la lógica compleja pero garantiza consistencia declarativa; Pulumi permite testing unitario y bucles reales pero puede descontrolarse si no hay disciplina.\nConclusión: Terraform/OpenTofu para estabilidad y ecosistema; Pulumi si los desarrolladores de producto gestionan su propia infra.",
        "assistant": """La elección entre Terraform y Pulumi se reduce a una disyuntiva cultural: **lenguaje declarativo de dominio específico (HCL) vs. programación imperativa completa con lenguajes reales**:

### 1. Terraform (HCL)
- **Ventajas:**
  - **El Estándar de la Industria:** Prácticamente cualquier módulo, proveedor de nube o servicio de terceros tiene un provider mantenido y documentado para Terraform / OpenTofu.
  - **Legibilidad y Seguridad Declarativa:** Al ser un lenguaje limitado sin bucles arbitrarios ni lógica imperativa compleja, es fácil auditar exactamente qué recursos se van a crear sin efectos secundarios ocultos.
- **Desventajas:**
  - El lenguaje HCL se vuelve enrevesado e inflexible cuando necesitas crear infraestructura condicional compleja o compartir utilidades lógicas entre proyectos.

### 2. Pulumi (TypeScript / Python / Go)
- **Ventajas:**
  - **Poder de Expresión Real:** Puedes usar bucles `for`, clases, paquetes de npm o pip, y crear abstracciones reutilizables con autocompletado en tu IDE.
  - **Pruebas Unitarias Reales:** Permite escribir tests de infraestructura con frameworks estándar (Jest, PyTest) antes de aplicar cambios en la nube.
- **Riesgos:**
  - Al disponer de un lenguaje de programación completo, desarrolladores inexpertos pueden introducir llamadas a APIs externas en medio de la definición de infraestructura o crear arquitecturas opacas difíciles de depurar.

### 3. Criterio de Elección
- Si vuestro equipo de infraestructura está formado por **ingenieros de sistemas y DevOps dedicados**, elegid **Terraform / OpenTofu**.
- Si la infraestructura la definen y mantienen **los propios desarrolladores de software de producto (*Full-Cycle Developers*)**, **Pulumi con TypeScript** les permitirá sentirse como en casa sin cambiar de lenguaje mental."""
    },
    {
        "user": "Estamos evaluando migrar nuestros pipelines de CI/CD de una instancia autogestionada de GitLab CI a GitHub Actions en la nube para un equipo de 30 ingenieros que ya aloja el código en GitHub. ¿Qué diferencias operativas y de coste debemos sopesar?",
        "think": "Contexto: Migración de pipelines de CI/CD de GitLab autogestionado a GitHub Actions en la nube.\nEvaluación: GitLab self-hosted exige mantener servidores y parches; GitHub Actions cloud elimina mantenimiento pero cobra por minuto de runner.\nConclusión: Migrar a GitHub Actions utilizando runners autogestionados para tareas pesadas.",
        "assistant": """Si vuestro repositorio de código ya reside en GitHub, **migrar a GitHub Actions es el paso lógico para consolidar la operativa y eliminar la sobrecarga de mantenimiento de servidores**:

### 1. Eliminación del Mantenimiento de Infraestructura de CI
- Mantener una instancia propia de GitLab exige parchear vulnerabilidades del servidor web, actualizar bases de datos PostgreSQL, mantener el almacenamiento de artefactos y vigilar la salud de los servidores de ejecución (*runners*).
- Con **GitHub Actions en la nube**, el control plane y la orquestación están 100% gestionados por GitHub con disponibilidad garantizada.

### 2. Comparativa de Costes y Tiempos
- **El Ecosistema de Acciones:** El marketplace de GitHub Actions cuenta con miles de integraciones mantenidas oficialmente (ej. `actions/checkout`, `aws-actions/configure-aws-credentials`) que reducen cientos de líneas de scripts YAML a un simple paso reutilizable.
- **Control de Facturación por Minuto:** GitHub ofrece 2.000 a 3.000 minutos mensuales gratuitos según el plan, pero factura por minuto adicional en sus runners compartidos (especialmente costosos en runners de macOS o máquinas grandes con GPU).

### 3. La Estrategia Híbrida Inteligente
- Utiliza **Runners gestionados por GitHub** para el 80% de los workflows rápidos (linting, tests unitarios, análisis estático).
- Si tenéis compilaciones Docker pesadas o suites de tests E2E que consumen miles de minutos, levantad **GitHub Actions Self-Hosted Runners** efímeros sobre instancias puntuales en vuestra propia nube (ej. con Actions Runner Controller sobre Kubernetes) para mantener el coste a raya."""
    },
    {
        "user": "Para monitorizar una plataforma de microservicios con 40 contenedores en producción, dudamos entre desplegar el stack de código abierto Prometheus + Grafana autogestionado o contratar la plataforma SaaS Datadog. ¿Cuál es el punto de inflexión del coste frente al esfuerzo operativo?",
        "think": "Contexto: Elección de plataforma de observabilidad entre Prometheus+Grafana autogestionado y Datadog SaaS.\nEvaluación: Prometheus exige almacenar métricas y configurar agentes propios; Datadog es instantáneo pero su facturación por host/métrica se dispara sin control.\nConclusión: Datadog para arrancar rápido si hay presupuesto; Prometheus/Grafana (o Grafana Cloud) al superar 30 hosts.",
        "assistant": """La disyuntiva entre Prometheus+Grafana y Datadog es el dilema clásico entre **tiempo de ingeniería frente a factura económica exponencial**:

### 1. El Peligro Oculto de la Facturación de Datadog
- Datadog es la herramienta de observabilidad más pulida del mercado: instalas su agente y en 10 minutos tienes dashboards automáticos, trazas APM y detección de anomalías.
- **La trampa del coste:** Datadog factura por host ($15 a $23/mes), pero añade cobros agresivos por métricas personalizadas (*custom metrics*), volumen de trazas APM ingeridas y gigabytes de logs indexados. Para 40 contenedores, una factura mal configurada puede dispararse con facilidad de 800 € a más de **3.500 € al mes sin previo aviso**.

### 2. La Solidez de Prometheus + Grafana
- **Estándar Universal:** Prácticamente cualquier librería de software y servicio cloud expone un endpoint `/metrics` en formato Prometheus de forma nativa.
- **Coste de Licencia Cero:** El software es 100% libre. Solo pagas la máquina virtual o el disco donde almacenas la base de datos temporal (*TSDB*).
- **Esfuerzo de Mantenimiento:** Exige que vuestro equipo diseñe los dashboards en Grafana, configure las reglas de alertas en Alertmanager y gestione la retención en disco (o utilice Cortex/Thanos para almacenamiento a largo plazo).

### 3. Veredicto y Alternativa Óptima
- Si contáis con presupuesto holgado y queréis arrancar sin dedicar tiempo de ingenieros: probad **Datadog fijando topes estrictos de consumo de métricas**.
- **La mejor opción intermedia:** Utilizad **Grafana Cloud** o **VictoriaMetrics**. Mantienes el estándar abierto de Prometheus sin la complejidad de operar la base de datos tú mismo y con un coste hasta 4 veces más bajo que Datadog."""
    },
    {
        "user": "En nuestra aplicación web de banca online debatimos el sistema de autenticación: utilizar tokens JWT totalmente stateless almacenados en localStorage/cookies o sesiones tradicionales en servidor con identificador de sesión en cookie HttpOnly respaldadas por Redis. ¿Cuál ofrece mejor seguridad y control?",
        "think": "Contexto: Autenticación web en banca decidiendo entre JWT stateless y sesiones en servidor con Redis.\nEvaluación: Los JWT stateless no se pueden revocar instantáneamente ante compromiso de cuenta; las sesiones en Redis ofrecen revocación atómica inmediata.\nConclusión: Sesiones en servidor con cookies HttpOnly seguras respaldadas por Redis.",
        "assistant": """En un entorno crítico como banca online o servicios transaccionales, **las sesiones tradicionales en servidor respaldadas por Redis superan rotundamente a los tokens JWT stateless**:

### 1. La Falla Fundamental de los JWT Stateless: La Imposibilidad de Revocación
- Un token JWT autofirmado contiene los permisos del usuario dentro de su firma criptográfica y es válido hasta que expire su fecha (`exp`).
- Si un usuario denuncia el robo de su teléfono, pulsa *"Cerrar sesión en todos los dispositivos"*, o un administrador bloquea a un empleado despedido, **el JWT sigue siendo 100% válido hasta que caduque**. No puedes invalidarlo sin mantener una lista negra en base de datos, lo que destruye el propósito de que fuera *stateless*.

### 2. Riesgos de Seguridad en el Navegador
- Guardar tokens JWT en `localStorage` deja la sesión expuesta a cualquier ataque de **Cross-Site Scripting (XSS)**: un script inyectado puede leer el token y exfiltrarlo en segundos.
- Si se almacena en una cookie segura con flags `HttpOnly`, `Secure` y `SameSite=Strict`, JavaScript no puede leer la cookie, pero entonces estás usando cookies exactamente como en el modelo tradicional de sesiones.

### 3. La Robustez de las Sesiones con Redis
- El navegador solo almacena una cookie opaca con un ID de sesión criptográfico aleatorio.
- Todos los datos de la sesión residen en Redis con un tiempo de expiración (TTL).
- Si se detecta un fraude, una simple orden `DEL session:usuario_123` en Redis **destruye el acceso del atacante en menos de 1 milisegundo en todas las sesiones activas**."""
    },
    {
        "user": "Nuestra plataforma global de mensajería procesa 200 millones de escrituras diarias distribuidas en tres continentes. Necesitamos una base de datos NoSQL con latencia de escritura ultra-baja y tolerancia a particiones de red. ¿Elegimos Apache Cassandra autogestionado o Amazon DynamoDB con Global Tables?",
        "think": "Contexto: Base de datos NoSQL para 200M escrituras diarias distribuidas globalmente.\nEvaluación: Cassandra ofrece soberanía multi-cloud pero exige un equipo especializado de operaciones de clúster; DynamoDB es serverless pero genera lock-in en AWS.\nConclusión: DynamoDB con Global Tables si el stack está en AWS; Cassandra solo ante exigencia multi-cloud.",
        "assistant": """Para absorber 200 millones de escrituras diarias distribuidas en varios continentes, la decisión se basa en **coste de ingeniería de operaciones frente a dependencia de proveedor (vendor lock-in)**:

### 1. Apache Cassandra (Soberanía y Máximo Rendimiento de Escritura)
- **Ventajas:**
  - Diseñada para escrituras masivas: escribe secuencialmente en un archivo de registro (*CommitLog*) y en memoria (*Memtable*), respondiendo escrituras en <2 milisegundos.
  - Arquitectura sin nodo maestro (*masterless*): todos los nodos son idénticos; puedes perder varios servidores en un datacenter sin interrupción de servicio.
  - Portabilidad total: puedes desplegar nodos en AWS, Google Cloud y servidores físicos propios simultáneamente.
- **Riesgos:**
  - Operar un clúster global de Cassandra es una tarea titánica: exige ingenieros especializados para gestionar compactaciones de disco (*compaction*), afinado de la JVM y reparaciones anti-entropía.

### 2. Amazon DynamoDB con Global Tables (Cero Mantenimiento Operativo)
- **Ventajas:**
  - Totalmente administrado: replicación multirregión activa-activa totalmente automática con resolución de conflictos basada en marcas de tiempo.
  - No requiere aprovisionar servidores, vigilar particiones ni actualizar sistemas operativos.
- **Riesgos:**
  - Dependencia absoluta del ecosistema de AWS y costes que pueden dispararse si los patrones de acceso no están bien optimizados en capacidad bajo demanda.

### 3. Veredicto
Si vuestra empresa ya opera en AWS y no cuenta con un equipo dedicado de ingenieros de bases de datos, **DynamoDB Global Tables** os ahorrará meses de dolores de cabeza operativos. Si necesitáis despliegues multi-nube independientes, optad por **Cassandra**."""
    },
    {
        "user": "Para el nuevo sistema de autenticación de nuestra app web y móvil, el equipo debate si implementar Passkeys (WebAuthn / FIDO2) o mantener el sistema clásico de contraseña robusta con segundo factor por TOTP (Google Authenticator). ¿Compensa dar el salto directo a Passkeys?",
        "think": "Contexto: Elección de autenticación entre Passkeys (FIDO2) y contraseña con 2FA TOTP.\nEvaluación: Passkeys elimina contraseñas y es inmune a phishing; requiere estrategia de recuperación para dispositivos extraviados.\nConclusión: Adoptar Passkeys como método primario manteniendo TOTP como respaldo alternativo.",
        "assistant": """La adopción de **Passkeys (WebAuthn / FIDO2) es el mayor salto en seguridad de autenticación de la última década**. Compensa rotundamente adoptarlo como método de acceso primario:

### 1. La Inmunidad contra el Phishing
- Las contraseñas tradicionales y los códigos de 6 dígitos (TOTP o SMS) son vulnerables a páginas falsas (*phishing* con proxies inversos tipo Evilginx) donde el usuario introduce sus credenciales sin saber que se las entrega al atacante.
- **Passkeys utiliza criptografía asimétrica vinculada al dominio criptográfico:** El navegador o el teléfono solo firma el desafío criptográfico si el origen web coincide exactamente con el dominio registrado. Es físicamente imposible ser engañado por una web de phishing.

### 2. Experiencia de Usuario sin Fricción
- El usuario inicia sesión en 1 segundo usando su **huella dactilar, reconocimiento facial (FaceID/TouchID) o el PIN de su dispositivo**. No hay que memorizar contraseñas complejas ni abrir una app secundaria para copiar códigos numéricos.
- Las passkeys se sincronizan automáticamente en la nube segura del usuario (iCloud Keychain, Google Password Manager o gestores como 1Password).

### 3. La Estrategia Híbrida de Transición
No elimines de golpe los métodos antiguos:
- Ofrece **Passkeys como la opción recomendada y preferente de acceso en un solo clic**.
- Mantén la combinación de contraseña + TOTP como mecanismo secundario de contingencia para usuarios con dispositivos antiguos o entornos que no soporten WebAuthn."""
    },
    {
        "user": "Nuestra base de código en TypeScript y React cuenta con 600 tests unitarios en Jest. Las pruebas tardan más de 2 minutos en ejecutarse en local y en CI. El equipo propone migrar la suite a Vitest. ¿Qué beneficios reales aporta y qué compatibilidad tiene con Jest?",
        "think": "Contexto: Suite de 600 tests en TypeScript tardando más de 2 minutos con Jest.\nEvaluación: Jest transpila con ts-jest o Babel de forma lenta; Vitest utiliza el pipeline nativo de Vite con esbuild en paralelo.\nConclusión: Migrar a Vitest para reducir tiempos de ejecución a una cuarta parte con cambios mínimos en tests.",
        "assistant": """La migración de Jest a **Vitest** es una de las optimizaciones con mayor impacto inmediato en la productividad diaria de un equipo de TypeScript:

### 1. Por qué Jest es Lento en TypeScript
- Jest fue diseñado antes de la era de los empaquetadores modernos. Para entender código TypeScript, depende de plugins como `ts-jest` o `babel-jest`, que compilan y transforman cada archivo individualmente en procesos lentos antes de ejecutar las aserciones.
- En suites medianas, el 70% del tiempo se consume en la fase de transpilación previa, no en comprobar las aserciones.

### 2. La Velocidad de Vitest
- **Motor Basado en Vite y Esbuild:** Vitest aprovecha la misma canalización de módulos que Vite y compila el código TypeScript usando **esbuild**, un compilador escrito en Go que procesa código entre 10 y 50 veces más rápido que TypeScript puro.
- **Ejecución en Paralelo Nativa:** Ejecuta los tests en hilos de trabajo paralelos (*worker threads*) con un uso eficiente de memoria y soporte nativo de ESM (*ECMAScript Modules*).
- **Reducción de Tiempo:** Una suite de 600 tests que en Jest tarda 120 segundos suele completarse en Vitest en **menos de 25 segundos**.

### 3. Compatibilidad Directa con Jest
- Vitest fue diseñado expresamente como un sustituto directo (*drop-in replacement*) de la API de Jest:
  - Las funciones globales `describe()`, `it()`, `test()`, `expect()`, `vi.fn()` (`jest.fn()`) y `vi.spyOn()` tienen la misma sintaxis.
  - En la mayoría de los proyectos, la migración solo requiere cambiar la configuración en `vite.config.ts` y sustituir las importaciones de mocks, completándose en un par de jornadas de trabajo."""
    }
]
