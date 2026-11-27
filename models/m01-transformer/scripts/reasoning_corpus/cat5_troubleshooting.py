"""
Categoría 5: Troubleshooting y resolución de averías técnicas (20 escenarios)
Bloques <think> concisos de 30-80 tokens de retrospectiva contextual e hipótesis de diagnóstico.
"""

SCENARIOS_CAT5 = [
    {
        "user": "En nuestro backend en producción (Django + Gunicorn tras Nginx), cada día a las 14:00 se disparan errores 504 Gateway Timeout durante la sincronización de inventario. La base de datos es PostgreSQL. ¿Cómo diagnosticar la causa raíz y resolver los timeouts?",
        "think": "Contexto: Errores 504 en Nginx por sincronización pesada en Django a las 14:00.\nEvaluación: Tarea síncrona bloquea workers de Gunicorn o genera bloqueos exclusivos en PostgreSQL.\nConclusión: Mover sincronización a tarea asíncrona (Celery) con escrituras en lotes pequeños.",
        "assistant": """El error 504 Gateway Timeout significa que **Nginx esperó una respuesta de Gunicorn durante más tiempo del configurado en `proxy_read_timeout` (por defecto 60 segundos) y cortó la conexión**. Sigue este plan estructurado:

### 1. Diagnóstico Inmediato en Producción
1. **Inspeccionar Bloqueos en PostgreSQL durante las 14:00:**
   Ejecuta en la consola de PostgreSQL:
   ```sql
   SELECT pid, now() - query_start AS duracion, query, state, wait_event_type, wait_event
   FROM pg_stat_activity
   WHERE state != 'idle' ORDER BY duracion DESC;
   ```
   Comprueba si la sincronización ejecuta `UPDATE` o `INSERT` masivos adquiriendo bloqueos exclusivos (`ExclusiveLock`) que congelan las lecturas de los usuarios comunes.

2. **Revisar Saturación de Workers en Gunicorn:**
   - Si la sincronización se lanza como una petición HTTP síncrona desde una vista web, esa petición secuestra un worker durante minutos. Si tienes 4 workers configurados, con 4 sincronizaciones concurrentes **Gunicorn se queda con cero workers disponibles para atender a usuarios reales**, acumulando peticiones en el socket hasta expirar.

### 2. Solución Arquitectónica Definitiva
- **Desacoplar la Sincronización a Segundo Plano (Celery / RQ):**
  - Nunca ejecutes tareas de sincronización masiva dentro del ciclo de solicitud/respuesta HTTP.
  - Traslada el proceso a un worker asíncrono desacoplado de la API web.
- **Procesamiento por Lotes Atómicos (Batching):**
  - Divide las actualizaciones en bloques de 500 a 1.000 registros usando `bulk_update(..., batch_size=500)`.
  - Envuelve cada lote en su propia microtransacción atómica (`transaction.atomic()`) para liberar bloqueos de fila de inmediato y evitar saturar el WAL de PostgreSQL."""
    },
    {
        "user": "Nuestro microservicio en Node.js se bloquea diariamente con el error 'FATAL ERROR: Ineffective mark-compacts near heap limit Allocation failed - JavaScript heap out of memory'. La memoria crece de 180 MB a 1,4 GB en 24 horas. ¿Cómo cazar la fuga de memoria exacta?",
        "think": "Contexto: Caída recurrente por Heap Out of Memory en servicio Node.js en 24 horas.\nEvaluación: Crecimiento lineal indica retención de objetos en arrays/mapas globales o listeners huérfanos.\nConclusión: Generar y comparar dos Heap Snapshots con Chrome DevTools o clinic.js.",
        "assistant": """El error confirma que el recolector de basura de V8 no puede liberar memoria suficiente y el proceso alcanza el techo máximo configurado. Para cazar la fuga exacta sin adivinar:

### 1. Generar Heap Snapshots Comparativos en Entorno de Pruebas
1. Arranca tu aplicación Node.js habilitando el inspector de depuración:
   ```bash
   node --inspect=0.0.0.0:9229 dist/index.js
   ```
2. Abre Google Chrome en tu ordenador y navega a `chrome://inspect`. Pulsa en *Open dedicated DevTools for Node*.
3. En la pestaña **Memory**:
   - Selecciona **Heap snapshot** y pulsa *Take snapshot* nada más arrancar (Snapshot 1: Estado base limpio).
4. Ejecuta un script de pruebas de carga que simule 5.000 peticiones a los endpoints de la API (con herramientas como `autocannon` o `k6`).
5. Toma un segundo Heap Snapshot (Snapshot 2).

### 2. Analizar la Comparativa (Comparison View)
- Cambia la vista de visualización del Snapshot 2 de *Summary* a **Comparison** contra el Snapshot 1.
- Ordena la tabla por la columna **Size Delta** o **# Delta**:
  - Si ves que la clase `(closure)`, `Object` o `Array` tiene un Delta positivo de miles de instancias, despliega el árbol.
  - Al pulsar sobre un objeto retenido, la ventana inferior **Retainers** te mostrará la cadena exacta de referencias que impide al recolector de basura destruirlo (por ejemplo: una variable global `cache[id] = data` o un `eventEmitter.on('finish', ...)` que nunca fue desuscrito)."""
    },
    {
        "user": "Una consulta de reporting en PostgreSQL que agregaba ventas mensuales tardaba 45 ms. Tras crecer la tabla a 8 millones de filas, la misma consulta tarda ahora 28 segundos y satura la CPU. ¿Cómo interpretar el EXPLAIN ANALYZE y corregir la regresión?",
        "think": "Contexto: Regresión crítica de 45 ms a 28 s en consulta de agregación en PostgreSQL.\nEvaluación: El planificador ejecuta un Sequential Scan masivo o un Hash Aggregate en disco por falta de índice o memoria.\nConclusión: Ejecutar EXPLAIN (ANALYZE, BUFFERS) y añadir índice compuesto o aumentar work_mem.",
        "assistant": """Para erradicar la lentitud de 28 segundos, el primer paso es ejecutar la consulta precedida de:
```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT tienda_id, SUM(total) 
FROM ventas 
WHERE fecha >= '2024-01-01' AND estado = 'COMPLETADA'
GROUP BY tienda_id;
```

### 1. Señales de Alarma a Buscar en la Salida
1. **`Seq Scan on ventas (cost=... rows=... actual time=... rows=8000000)`:**
   - Significa que PostgreSQL está leyendo los 8 millones de registros uno por uno desde el disco porque no tiene un índice adecuado para filtrar por `fecha` y `estado`.
2. **`Buffers: shared read=...` muy elevado:**
   - La base de datos tiene que acudir a disco continuo en lugar de memoria RAM (*shared buffers*).
3. **`Sort Method: external merge Disk` o `Batches: > 1` en el HashAggregate:**
   - La agregación no cabe en la memoria de trabajo temporal (`work_mem`) y PostgreSQL escribe archivos temporales en disco, hundiendo el rendimiento.

### 2. La Solución Técnica
1. **Crear un Índice Compuesto Cubriente (*Covering Index*):**
   Crea un índice que contenga las columnas del filtro y las de la agregación:
   ```sql
   CREATE INDEX CONCURRENTLY idx_ventas_reporte 
   ON ventas (estado, fecha) 
   INCLUDE (tienda_id, total);
   ```
   Al utilizar `INCLUDE`, PostgreSQL realiza un **Index Only Scan**: lee exclusivamente las páginas compactas del índice sin tocar la tabla principal en disco, devolviendo la consulta a **menos de 30 milisegundos**.
2. **Ajuste de `work_mem` para la sesión:**
   Si la agregación es pesada, aumenta temporalmente la memoria de la consulta: `SET work_mem = '64MB';`."""
    },
    {
        "user": "Uno de nuestros contenedores Docker en AWS ECS se reinicia aleatoriamente 2 o 3 veces al día. En los logs de eventos del clúster aparece el mensaje: 'Task stopped at: ... exit code 137'. ¿Qué significa exactamente el código 137 y cómo solucionarlo?",
        "think": "Contexto: Contenedor en ECS se reinicia aleatoriamente con exit code 137.\nEvaluación: Exit code 137 = 128 + 9 (SIGKILL enviado por el kernel de Linux por OOM Killer al superar límite de memoria).\nConclusión: Diagnosticar con CloudWatch Container Insights y redimensionar memoria o corregir fuga en código.",
        "assistant": """En sistemas Linux y Docker, el código de salida **137** tiene un significado matemático estricto: **128 + 9 (Señal SIGKILL)**. Significa que el proceso fue terminado forzosamente de forma instantánea por el núcleo del sistema operativo a través del **OOM Killer (Out Of Memory Killer)**:

### 1. La Causa Raíz
- Tu tarea en ECS tiene un límite de memoria estricto (*hard memory limit*) configurado en la definición de la tarea (ej. 1024 MB).
- Cuando tu aplicación intenta reservar 1 megabyte adicional por encima de ese límite, el kernel de Linux no permite paginación y envía inmediatamente una señal destructiva `kill -9` para evitar que el contenedor corrompa la memoria del host.

### 2. Protocolo de Resolución
1. **Confirmar el evento OOM en AWS CloudWatch:**
   - Ve a CloudWatch > ECS Container Insights > Métrica `MemoryUtilization`.
   - Verás una curva que asciende progresivamente hasta tocar el 100%, momento exacto en el que la métrica cae a cero (el reinicio).
2. **Determinar si es una Fuga o un Pico Puntual:**
   - *Si la memoria sube lentamente a lo largo de horas:* Tienes una **fuga de memoria (*memory leak*)** en el código (objetos no liberados).
   - *Si la memoria se mantiene al 30% y de repente salta al 100% en 1 segundo:* Ocurre cuando un usuario solicita una exportación masiva de datos (ej. un Excel de 500.000 filas generado directamente en memoria RAM en lugar de utilizar streams).
3. **Acciones Correctivas:**
   - Aumenta temporalmente el límite de memoria en el Task Definition para estabilizar producción mientras se corrige el código.
   - Refactoriza cualquier endpoint de exportación o lectura de base de datos para utilizar **lecturas paginadas o flujos en streaming (Node.js Streams / Python Generators)** sin almacenar datasets completos en la RAM."""
    },
    {
        "user": "Al realizar peticiones desde nuestra aplicación frontend en `app.midominio.com` contra la API en `api.midominio.com`, el navegador bloquea la llamada con el error: 'Access to fetch at ... has been blocked by CORS policy: Response to preflight request doesn't pass access control check: It does not have HTTP ok status'. ¿Cómo resolver este fallo de CORS?",
        "think": "Contexto: Bloqueo de CORS en petición preflight OPTIONS entre subdominios.\nEvaluación: El navegador envía OPTIONS automático que el backend responde con 401, 403 o 404 en lugar de 200/204 con cabeceras Access-Control.\nConclusión: Configurar el backend o proxy inverso para responder a OPTIONS con estado 204 y cabeceras Access-Control correctas.",
        "assistant": """El error especifica que la **petición previa de comprobación (*preflight OPTIONS*) falló antes de que la petición real (POST, PUT o GET con cabeceras custom) pudiera enviarse**:

### 1. Qué es el Preflight OPTIONS y por qué Falla
- Cuando una llamada frontend incluye cabeceras personalizadas (como `Authorization: Bearer ...`) o métodos que modifican datos, el navegador envía automáticamente una petición preliminar con el método `OPTIONS` para preguntar al servidor si autoriza la comunicación entre diferentes orígenes.
- El error ocurre porque **vuestro middleware de autenticación en el backend está interceptando la petición OPTIONS y devolviendo un 401 Unauthorized o 403 Forbidden** (porque la petición previa no incluye el token de usuario), o el enrutador devuelve un 404.

### 2. Configuración Correcta en el Servidor (Nginx / Express / FastAPI)
1. **Permitir peticiones OPTIONS sin exigir autenticación:**
   - Las peticiones OPTIONS deben responderse **siempre con código HTTP 204 No Content o 200 OK**, sin pasar por los filtros de login.
2. **Cabeceras HTTP de Respuesta Obligatorias:**
   El backend debe devolver en la respuesta al preflight:
   ```http
   Access-Control-Allow-Origin: https://app.midominio.com
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
   Access-Control-Allow-Headers: Authorization, Content-Type, Accept
   Access-Control-Allow-Credentials: true
   Access-Control-Max-Age: 86400
   ```
   *(Nota: `Access-Control-Max-Age` permite al navegador cachear la autorización de CORS durante 24 horas para no repetir la llamada previa en cada clic).*
3. **No uses comodín con credenciales:** Si envías cookies o `Authorization`, `Access-Control-Allow-Origin` no puede ser `*`; debe especificar el dominio exacto."""
    },
    {
        "user": "Cuando me conecto por SSH a un servidor Linux remoto en la nube, la sesión se congela por completo si dejo la terminal inactiva durante 3 minutos, o cuando ejecuto un comando que vuelca mucho texto rápido (como `cat archivo_grande.log`). El cursor se queda colgado y tengo que cerrar la ventana del terminal. ¿Cuál es el problema?",
        "think": "Contexto: Sesión SSH que se congela por inactividad o al imprimir texto masivo en servidor remoto.\nEvaluación: Cortafuegos o routers NAT intermedios descartan conexiones inactivas, o fallo de MTU/MSS en paquetes grandes.\nConclusión: Configurar ServerAliveInterval en el cliente SSH y ajustar MTU de la interfaz de red.",
        "assistant": """Estás sufriendo dos problemas de red habituales que provocan el bloqueo de sesiones SSH:

### 1. Bloqueo por Inactividad (Timeout de la Tabla NAT)
- **Causa:** Los cortafuegos y routers intermedios mantienen una tabla de traducción de direcciones (*NAT table*). Si no ven tráfico en una conexión TCP durante unos minutos, **eliminan silenciosamente la conexión sin avisar**. Al volver a teclear, tus paquetes se envían a la nada y la terminal se congela.
- **Solución en tu máquina local:** Añade a tu archivo `~/.ssh/config`:
  ```ssh
  Host *
      ServerAliveInterval 30
      ServerAliveKeepAlive 3
  ```
  Esto envía un paquete de latido (*heartbeat*) invisible cada 30 segundos, manteniendo vivo el túnel en los cortafuegos intermedios.

### 2. Bloqueo al Volcar Mucho Texto (Problema de MTU / Fragmentación TCP)
- **Causa:** Cuando ejecutas `cat archivo.log`, SSH envía paquetes TCP al tamaño máximo de la unidad de transmisión (**MTU**, habitualmente 1500 bytes). Si en el camino de la red (túnel VPN, Wi-Fi o proveedor cloud) hay un tramo con un MTU inferior (ej. 1420 bytes) y el cortafuegos bloquea los paquetes ICMP de fragmentación (*Path MTU Discovery Black Hole*), **los paquetes grandes se descartan silenciosamente y la sesión se bloquea al instante**.
- **Solución:** Reduce el MTU en tu tarjeta de red a 1400 bytes o configura en el router / servidor el ajuste de MSS clamping:
  ```bash
  # En el cliente Linux:
  sudo ip link set dev eth0 mtu 1400
  ```"""
    },
    {
        "user": "Tras realizar un `git merge` entre la rama `develop` y una rama de funcionalidad, se produjeron conflictos en un archivo binario `.sqlite` de pruebas y en el archivo `package-lock.json`. Un desarrollador intentó resolverlos a mano y ahora `git status` muestra un árbol roto y `npm install` falla con errores de integridad. ¿Cómo limpiar el desastre y resolver el conflicto correctamente?",
        "think": "Contexto: Conflicto corrupto en Git en archivo binario y package-lock tras merge fallido.\nEvaluación: Intentar editar binarios o locks manualmente corrompe los hashes y el árbol de dependencias.\nConclusión: Abortar merge o recuperar versiones limpias con git checkout --ours/--theirs y regenerar lockfile.",
        "assistant": """Nunca se resuelven conflictos en archivos binarios ni en `package-lock.json` mediante editores de texto, ya que Git inserta marcadores de texto (`<<<<<<<`, `=======`) que destruyen la estructura interna del archivo. Sigue estos pasos para sanear el repositorio:

### 1. Opción Rápida: Si el Merge Aún no se ha Confirmado (Commit)
Si aún estás en estado de merge conflictivo, aborta la operación para volver al estado limpio previo:
```bash
git merge --abort
```

### 2. Resolución Quirúrgica de los Archivos en Conflicto
Vuelve a lanzar el merge y resuelve cada archivo según su naturaleza:

1. **Para el archivo binario (`.sqlite` o imágenes):**
   Un archivo binario no se puede mezclar; debes elegir explícitamente si te quedas con tu versión (`ours`) o con la versión que viene de la otra rama (`theirs`):
   ```bash
   # Quedarte con tu versión local:
   git checkout --ours -- ruta/a/base_pruebas.sqlite
   # O quedarte con la versión de la rama entrante:
   git checkout --theirs -- ruta/a/base_pruebas.sqlite
   git add ruta/a/base_pruebas.sqlite
   ```

2. **Para `package-lock.json`:**
   La forma oficial y limpia de resolverlo es pedir a npm que regenere el árbol criptográfico a partir de los `package.json` ya combinados:
   ```bash
   # Elimina el lockfile corrupto y vuélvelo a construir:
   rm package-lock.json
   npm install
   git add package-lock.json package.json
   ```

3. **Finalizar el Merge:**
   ```bash
   git commit -m "Merge branch 'feature' resuelto limpiamente"
   ```"""
    },
    {
        "user": "Certbot falla al intentar renovar automáticamente el certificado SSL Let's Encrypt de nuestro servidor Nginx con el error: 'Certbot failed to authenticate some domains (http-01): Fetching http://midominio.com/.well-known/acme-challenge/...: Timeout during connect (likely firewall problem)'. La web abre bien por HTTPS. ¿Cuál es el problema?",
        "think": "Contexto: Fallo de renovación de certificado SSL por timeout en reto HTTP-01 con web operativa en HTTPS.\nEvaluación: El reto HTTP-01 valida conectándose por HTTP en el puerto 80; el cortafuegos solo tiene abierto el 443.\nConclusión: Abrir el puerto 80 en el grupo de seguridad y permitir redirección en Nginx.",
        "assistant": """El error de Certbot se debe a que **el puerto 80 (HTTP) está bloqueado en el cortafuegos de tu proveedor de la nube o en el sistema operativo**:

### 1. El Funcionamiento del Reto HTTP-01 de Let's Encrypt
- Para verificar que eres el dueño legítimo del dominio, los servidores de validación de Let's Encrypt intentan conectarse obligatoriamente por **HTTP estándar en el puerto 80** a la ruta temporal `http://midominio.com/.well-known/acme-challenge/archivo_temporal`.
- Aunque tu página web funcione perfectamente por HTTPS en el puerto 443, **si el puerto 80 está cerrado, la validación expira por timeout y la renovación falla**.

### 2. Solución en 2 Pasos
1. **Abrir el Puerto 80 en el Cortafuegos de la Nube:**
   - En la consola de tu proveedor (AWS Security Groups, Cloudflare, DigitalOcean o Hetzner Firewall), añade una regla de entrada (*Inbound Rule*):
     - **Tipo:** HTTP
     - **Puerto:** 80
     - **Origen:** 0.0.0.0/0 (Cualquier IP pública)
   - En el servidor Linux, abre el firewall local: `sudo ufw allow 80/tcp`.

2. **Configurar Nginx para no Romper el Reto:**
   Asegúrate de que tu bloque de Nginx en el puerto 80 redirija al 443 pero permita leer la carpeta de verificación:
   ```nginx
   server {
       listen 80;
       server_name midominio.com;

       location /.well-known/acme-challenge/ {
           root /var/www/certbot;
       }

       location / {
           return 301 https://$host$request_uri;
       }
   }
   ```
3. Ejecuta de nuevo `sudo certbot renew` y la renovación se completará con éxito en 5 segundos."""
    },
    {
        "user": "En nuestra plataforma de streaming de eventos, el desfase de consumidores (*consumer lag*) en un topic crítico de Apache Kafka con 4 particiones se dispara durante las horas pico de 200 mensajes a más de 800.000 mensajes acumulados. El grupo de consumidores consta de 4 instancias en Go. ¿Cómo diagnosticar el cuello de botella?",
        "think": "Contexto: Acumulación masiva de 800.000 mensajes de lag en Kafka con 4 particiones y 4 consumidores.\nEvaluación: Añadir más consumidores no ayudará porque hay solo 4 particiones; los consumidores están bloqueados por I/O síncrono.\nConclusión: Incrementar particiones del topic y paralelizar procesamiento interno con lotes o workers en Go.",
        "assistant": """El *consumer lag* significa que la velocidad de producción de mensajes supera la capacidad de procesamiento de tus consumidores. En Kafka existe una regla física fundamental: **un consumidor individual solo puede leer de una partición a la vez**.

### 1. El Límite de las 4 Particiones
- Al tener exactamente 4 particiones y 4 instancias del consumidor, **añadir un quinto consumidor en Go no servirá de nada**: la quinta instancia se quedará ociosa (*idle*) sin recibir tráfico.
- Si cada mensaje tarda en procesarse 25 ms (por ejemplo esperando una llamada a base de datos externa), 4 consumidores solo pueden procesar como máximo 160 mensajes por segundo combinados. Si en hora punta entran 2.000 eventos/s, el lag crecerá en cientos de miles de mensajes por hora matemáticamente.

### 2. Dónde Está el Freno: Diagnóstico de la Lógica del Consumidor
- ¿Está el consumidor de Go ejecutando una llamada a base de datos o API HTTP por cada mensaje individual de forma síncrona?
- **El cuello de botella es la latencia de I/O por mensaje individual.**

### 3. Plan de Mitigación Inmediato
1. **Aumentar el Número de Particiones del Topic:**
   - Escala el topic de Kafka de 4 a **16 o 32 particiones**:
     ```bash
     kafka-topics.sh --alter --topic eventos-streaming --partitions 16 --bootstrap-server localhost:9092
     ```
   - Ahora puedes desplegar 16 instancias de tus consumidores en Go para multiplicar por 4 la capacidad de absorción paralela.
2. **Procesamiento por Lotes y Goroutines en el Consumidor:**
   - Modifica el consumidor para leer mensajes en bloques (*batch*) de 100 elementos y utilizar `bulk insert` hacia la base de datos de destino.
   - Procesa los mensajes concurrentemente con un pool de goroutines internas antes de confirmar el *offset* (`commit`)."""
    },
    {
        "user": "Un microservicio en Python procesa logs de texto usando expresiones regulares. De forma aleatoria, cuando recibe una línea de log específica, el proceso clava un núcleo de CPU al 100% durante 15 minutos congelando el contenedor. Con líneas normales tarda 2 milisegundos. ¿Cómo diagnosticar y corregir este problema?",
        "think": "Contexto: Proceso Python bloquea CPU al 100% durante 15 minutos ante ciertas líneas de texto en regex.\nEvaluación: Patrón de backtracking catastrófico en expresiones regulares con cuantificadores anidados ambiguos.\nConclusión: Identificar patrones anidados peligrosos y reescribir con regex atómica o utilizar el motor Google re2.",
        "assistant": """Este síntoma es un caso de libro de **backtracking catastrófico (Catastrophic Backtracking)** en el motor de expresiones regulares tradicional de Python (`re`):

### 1. El Mecanismo del Fallo Algorítmico
- El módulo estándar `re` de Python utiliza un motor de autómatas no deterministas (*NFA*).
- Cuando una expresión regular contiene **cuantificadores ambiguos anidados o solapados** (por ejemplo: `(a+)+$`, `([a-zA-Z0-9]+)*=` o `.*(foo|bar).*`), y se le introduce un texto largo que casi coincide pero falla en el último carácter:
- El motor intenta **todas las combinaciones exponenciales posibles de partición de caracteres** antes de decidir que no encaja. Para un texto de solo 40 caracteres, el número de permutaciones evaluadas supera los miles de millones, congelando la CPU con complejidad temporal `O(2^N)`.

### 2. Cómo Detectar la Expresión Culpable
1. Extrae la línea de log conflictiva que causó el cuelgue.
2. Pasa tus expresiones regulares por herramientas como **regex101.com** (seleccionando el motor Python): la herramienta te alertará en rojo con el aviso *"Catastrophic backtracking detected (>100.000 steps)"*.

### 3. Las Dos Soluciones Definitivas
1. **Sustituir el módulo `re` por `google-re2`:**
   - Instala la librería oficial de Google: `pip install google-re2`.
   - `re2` utiliza autómatas finitos deterministas (DFA) que **garantizan tiempo lineal de ejecución `O(N)` en cualquier escenario**, haciendo matemáticamente imposible el backtracking catastrófico o ataques de denegación de servicio por ReDoS.
2. **Reescribir la expresión regular:**
   - Elimina cuantificadores anidados y utiliza clases de caracteres disjuntas (evita usar `.*` combinado con grupos repetidos)."""
    },
    {
        "user": "En nuestro servidor Redis en producción, las aplicaciones backend han empezado a recibir el error: 'OOM command not allowed when used memory > maxmemory'. Los dashboards muestran que Redis ha alcanzado los 8 GB asignados. ¿Cómo recuperar el servicio y qué directivas de configuración ajustar?",
        "think": "Contexto: Redis bloquea escrituras con error OOM al alcanzar el límite de 8 GB de memoria.\nEvaluación: Falta política de desalojo (eviction policy) o las claves no tienen TTL configurado.\nConclusión: Configurar política allkeys-lru y purgar claves huérfanas con redis-cli.",
        "assistant": """Este error ocurre porque Redis ha llenado los 8 GB asignados en la directiva `maxmemory` y la política de desalojo configurada por defecto es `noeviction` (que rechaza cualquier comando que consuma memoria adicional como `SET`, `HSET` o `LPUSH`):

### 1. Recuperación Inmediata del Servicio
Conéctate a la consola de Redis con `redis-cli` y ejecuta:

1. **Consultar la memoria y la política actual:**
   ```redis
   INFO memory
   CONFIG GET maxmemory-policy
   ```
2. **Cambiar la política de desalojo en caliente (sin reiniciar):**
   Si usas Redis como caché, permite que Redis elimine automáticamente las claves menos utilizadas recientemente para hacer hueco:
   ```redis
   CONFIG SET maxmemory-policy allkeys-lru
   ```
   En cuanto ejecutes este comando, Redis purgará en milisegundos las claves antiguas y las escrituras volverán a funcionar inmediatamente.

### 2. Diagnóstico de qué está Devorando la Memoria
Para descubrir qué aplicación o módulo está llenando los 8 GB:
```bash
# Analizar qué tipos de claves ocupan más memoria:
redis-cli --bigkeys

# O escanear patrones de claves con memoria pesada:
redis-cli --memkeys
```

### 3. Reglas de Configuración Preventiva
- **TTL Obligatorio en Caché:** Toda clave de caché debe crearse con un tiempo de expiración (ej. `SET key value EX 3600`). Sin TTL, las claves quedan huérfanas eternamente.
- **Diferenciar Caché de Persistencia:** Si usas Redis para colas (Celery/BullMQ) o datos que no pueden perderse, no uses `allkeys-lru`; debes aprovisionar más RAM o utilizar una instancia separada exclusiva para datos permanentes."""
    },
    {
        "user": "Nuestra aplicación web utiliza WebSockets para actualizar cotizaciones financieras en tiempo real. Los usuarios nos reportan que la conexión se corta exactamente cada 60 segundos, forzando a la app a reconectar continuamente. El backend está en Go y tenemos Nginx y un balanceador AWS ALB al frente. ¿Por qué se corta a los 60 segundos?",
        "think": "Contexto: Desconexión de WebSockets exactamente a los 60 segundos tras Nginx y AWS ALB.\nEvaluación: El timeout de inactividad de Nginx (proxy_read_timeout) o del balanceador ALB está fijado en 60 s.\nConclusión: Ajustar proxy_read_timeout en Nginx a 3600 s e implementar ping/pong de latido cada 25 s.",
        "assistant": """La desconexión a los 60 segundos exactos es la firma inequívoca de un **timeout de inactividad de conexión TCP configurado por defecto en Nginx (`proxy_read_timeout`) o en el balanceador de carga AWS ALB**:

### 1. La Causa Raíz
- Una conexión WebSocket es un túnel TCP persistente. Sin embargo, para los proxies intermedios (Nginx y AWS ALB), si no circula ningún paquete de datos en el túnel durante 60 segundos, consideran que la conexión está muerta y envían un paquete `TCP FIN/RST` para cerrar el socket y liberar recursos.

### 2. Solución en Dos Frentes

1. **Aumentar los Timeouts en Nginx:**
   En el bloque `location` de tu configuración de Nginx donde manejas el proxy hacia los WebSockets, añade:
   ```nginx
   location /ws/ {
       proxy_pass http://backend_go;
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";

       # Evitar el corte a los 60 segundos:
       proxy_read_timeout 3600s;
       proxy_send_timeout 3600s;
   }
   ```
   En AWS ALB, ve a la configuración de atributos del balanceador y eleva el *Idle timeout* de 60 segundos a 300 segundos.

2. **La Solución Robusta Definitiva: Ping/Pong Heartbeats**
   No dependas únicamente de subir timeouts infinitos. Configura en tu backend de Go un latido periódico de control:
   - Envía un frame estándar de WebSocket **`Ping` cada 25 o 30 segundos**.
   - El cliente responderá automáticamente con un frame `Pong`.
   - Este tráfico mínimo de 2 bytes mantiene activo el canal en todos los routers, proxies y redes móviles del mundo sin desconexiones."""
    },
    {
        "user": "Al abrir una pantalla de un panel en React, la pestaña de Google Chrome se congela por completo, el ventilador del ordenador se acelera y tras 10 segundos aparece la pantalla de error 'La página no responde'. En la consola de desarrollo alcanzamos a ver miles de renders antes del bloqueo. ¿Cómo localizar el bucle infinito en el componente?",
        "think": "Contexto: Bloqueo de navegador por bucle infinito de re-renderizado en componente React.\nEvaluación: Modificación de estado dentro de useEffect sin dependencias o con objetos creados en el render.\nConclusión: Auditar dependencias del useEffect y verificar mutaciones de estado incondicionales.",
        "assistant": """Un cuelgue completo de la pestaña con miles de renders ocurre cuando **un cambio de estado dentro de un componente dispara un nuevo renderizado que vuelve a ejecutar inmediatamente la misma actualización de estado**:

### 1. Los Dos Errores Culpables Más Frecuentes
1. **Modificar el Estado dentro de `useEffect` con Dependencias Inestables:**
   ```jsx
   // ERROR TÍPICO:
   useEffect(() => {
     const nuevosFiltros = { activo: true }; // Objeto nuevo creado en cada ciclo
     setFiltros(nuevosFiltros);
   }, [filtros]); // Como filtros cambió, se re-ejecuta el useEffect -> Bucle infinito
   ```
2. **Ejecutar la Función en el JSX en lugar de Pasarla como Callback:**
   ```jsx
   // ERROR GARRAFAL:
   <button onClick={setContador(contador + 1)}>Pulsar</button>
   // Esto ejecuta setContador DURANTE el render, no al hacer clic.
   // Corrección:
   <button onClick={() => setContador(contador + 1)}>Pulsar</button>
   ```

### 2. Cómo Diagnosticar el Archivo Exacto
1. Abre el archivo del componente sospechoso y revisa los `useEffect`.
2. **La Prueba del console.trace():** Añade al principio del cuerpo de tu componente:
   ```jsx
   console.log('Renderizando componente X', new Date().toISOString());
   ```
3. Si la consola se inunda con cientos de líneas por segundo, revisa qué variable de estado (`useState`) se está actualizando sin una condición de salida estricta.
4. **Objetos y Arrays como Dependencias:** Si pasas arrays u objetos al array de dependencias `[datos]`, recuerda que en JavaScript `{}` !== `{}` por referencia de memoria. Memorízalos con `useMemo` o pasa valores primitivos como `[datos.id]`."""
    },
    {
        "user": "En nuestro clúster de Kubernetes en AWS EKS, los pods resuelven perfectamente los servicios internos (`mi-servicio.default.svc.cluster.local`), pero cualquier llamada a dominios externos de internet (como `api.stripe.com` o `api.github.com`) falla intermitentemente con el error 'getaddrinfo EAI_AGAIN'. ¿Cómo diagnosticar y solucionar CoreDNS?",
        "think": "Contexto: Fallo de resolución DNS para dominios externos en pods de Kubernetes con error EAI_AGAIN.\nEvaluación: Sobrecarga o agotamiento de réplicas en CoreDNS o límites de consultas DNS en la VPC de AWS.\nConclusión: Escalar réplicas de CoreDNS, habilitar NodeLocal DNSCache y revisar ConfigMap.",
        "assistant": """El error `EAI_AGAIN` es un fallo temporal de timeout en la resolución de nombres DNS. Si la resolución interna funciona pero la externa falla en EKS, la causa se encuentra en la **saturación de CoreDNS o en los límites de throttling del resolver de AWS VPC (Route 53 Resolver)**:

### 1. Diagnóstico de CoreDNS
1. **Revisar los logs y métricas de CoreDNS:**
   ```bash
   kubectl logs -n kube-system -l k8s-app=kube-dns --tail=100
   ```
   Busca errores de timeout (`i/o timeout`) o denegaciones contra los servidores upstream.
2. **Comprobar si CoreDNS está infradimensionado:**
   ```bash
   kubectl get deployment coredns -n kube-system
   ```
   Si tienes 50 pods en el clúster pero CoreDNS solo tiene **2 réplicas por defecto**, cada pod bombardeando con consultas DNS satura los dos únicos pods de CoreDNS.

### 2. El Límite Oculto de AWS VPC (1024 paquetes/s por interfaz)
- AWS impone un límite estricto de **1.024 consultas DNS por segundo por interfaz de red (ENI)** hacia la IP `.2` del VPC resolver. Si tus pods superan ese umbral, AWS descarta los paquetes silenciosamente causando los timeouts `EAI_AGAIN`.

### 3. Solución Arquitectónica Definitiva
1. **Instalar NodeLocal DNSCache (Recomendado oficialmente por Kubernetes):**
   - Despliega un DaemonSet de caché DNS en cada nodo del clúster. Las consultas de los pods se resuelven en la memoria del propio nodo físico mediante una IP de bucle invertido (`169.254.20.10`), eliminando el 90% del tráfico hacia CoreDNS y evitando el límite de AWS VPC.
2. **Escalar CoreDNS con Autoescalador Horizontal:**
   - Asegura al menos 1 réplica de CoreDNS por cada 15-20 nodos en el clúster."""
    },
    {
        "user": "El servidor que aloja nuestra base de datos MySQL en Linux muestra la CPU al 85% de uso, pero al abrir `top` vemos que `us` (user) es solo del 5% y `wa` (iowait) está al 80%. Las consultas transaccionales se han congelado. ¿Qué significa un iowait del 80% y cómo desbloquear el servidor?",
        "think": "Contexto: MySQL con CPU bloqueada al 80% por iowait (wa) y rendimiento congelado.\nEvaluación: La CPU no calcula; pasa el 80% del tiempo esperando operaciones de lectura/escritura en disco.\nConclusión: Localizar procesos saturando I/O con iotop/iostat y optimizar dirty pages o escalado de IOPS.",
        "assistant": """Un `wa` (*iowait*) del 80% en `top` significa que **la CPU no tiene trabajo de cálculo, sino que pasa el 80% de sus ciclos completamente ociosa esperando a que el disco duro termine de leer o escribir bloques de datos**:

### 1. Diagnóstico Inmediato del Almacenamiento
1. **Inspeccionar qué proceso satura el disco:**
   Ejecuta en la terminal como root:
   ```bash
   sudo iotop -oPa
   ```
   Verás en tiempo real qué PID de MySQL o proceso en segundo plano (backups, volcados mysqldump, swaps) está devorando el ancho de banda del disco.
2. **Comprobar saturación del dispositivo de bloques con `iostat`:**
   ```bash
   iostat -xz 1 5
   ```
   Fíjate en la última columna **`%util`**: si marca el **100%**, el disco ha alcanzado su límite físico de operaciones por segundo (**IOPS**) o ancho de banda en MB/s.

### 2. Causas Habituales en MySQL
1. **Límite de IOPS en la Nube (AWS EBS gp2/gp3):** Si tienes un disco EBS en AWS con solo 3.000 IOPS base y la base de datos exige 6.000 IOPS, el disco se estrangula (*throttling*). Aumenta los IOPS provisionados en la consola de AWS sin reiniciar.
2. **Falta de Memoria en el Buffer Pool de InnoDB:**
   - Si `innodb_buffer_pool_size` está configurado en un valor ridículo (ej. 1 GB en una máquina de 16 GB), MySQL no puede mantener las tablas e índices en memoria RAM y tiene que ir al disco físico en cada `SELECT`.
   - **Ajuste:** Configura `innodb_buffer_pool_size` al **70%-75% de la memoria RAM total** del servidor.
3. **Escrituras Masivas de Logs de Redo:** Configura `innodb_flush_log_at_trx_commit = 2` para mitigar las escrituras sincronizadas a disco por cada microtransacción."""
    },
    {
        "user": "Los usuarios de nuestra app de Android reportan que al pulsar en el botón de 'Sincronizar Datos', la pantalla se congela y aparece el diálogo del sistema 'La aplicación no responde (ANR)'. ¿Cuál es la causa técnica en el código de Android y cómo corregirla?",
        "think": "Contexto: Error ANR en Android al pulsar botón de sincronización de datos.\nEvaluación: Ejecución de operaciones bloqueantes de red o base de datos en el Main Thread (UI Thread) superando 5 segundos.\nConclusión: Trasladar la tarea a corrutinas de Kotlin en Dispatchers.IO o WorkManager.",
        "assistant": """El diálogo **ANR (Application Not Responding)** es una protección estricta del sistema operativo Android: se dispara automáticamente cuando **el hilo principal (*Main Thread / UI Thread*) se bloquea durante más de 5 segundos sin poder pintar fotogramas ni responder a toques en pantalla**:

### 1. La Causa Raíz
- En Android, el hilo principal es responsable exclusivo de dibujar la interfaz gráfica a 60/120 fps y gestionar las pulsaciones de usuario.
- Si dentro del listener de un botón (`button.setOnClickListener { ... }`) ejecutas una operación de red HTTP, una consulta pesada a SQLite/Room o un procesamiento de imágenes grande, **el hilo principal se congela esperando los datos del servidor**. Al pasar 5 segundos, el sistema concluye que la app ha muerto y muestra el error ANR.

### 2. La Solución Moderna: Corrutinas de Kotlin en `Dispatchers.IO`
Nunca ejecutes trabajo pesado en el hilo de interfaz. Despáchalo al hilo de entrada/salida (*I/O Thread*):

```kotlin
// EN TU VIEWMODEL O CONTROLADOR:
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

fun sincronizarDatos() {
    viewModelScope.launch {
        // 1. Mostrar spinner de carga en el UI Thread
        _estadoCarga.value = true

        try {
            // 2. Mover la ejecución pesada al pool de hilos de I/O en segundo plano:
            val resultado = withContext(Dispatchers.IO) {
                apiServicio.descargarDatosPesados() // Operación de red segura
            }
            // 3. De vuelta al Main Thread automáticamente para pintar los datos:
            _datos.value = resultado
        } finally {
            _estadoCarga.value = false
        }
    }
}
```

Para sincronizaciones en segundo plano que deban continuar aunque el usuario cierre la app, utiliza la librería oficial **WorkManager**."""
    },
    {
        "user": "Nuestro pipeline de CI/CD en GitLab falla de forma intermitente un 30% de las veces en el paso de `npm install` con errores de checksum mismatch o dependencias no resueltas, a pesar de que el código no ha cambiado. ¿Cómo lograr compilaciones deterministas y reproducibles?",
        "think": "Contexto: Fallos intermitentes de build en CI/CD por dependencias npm no reproducibles.\nEvaluación: Uso de npm install en lugar de npm ci, o ausencia de package-lock.json versionado en Git.\nConclusión: Sustituir por npm ci y asegurar package-lock.json congelado en el repositorio.",
        "assistant": """El fallo intermitente en CI/CD se debe a un error metodológico clásico: **utilizar `npm install` en entornos automatizados en lugar del comando determinista `npm ci`**:

### 1. La Diferencia Crítica entre `npm install` y `npm ci`
- **`npm install`:** Está pensado para desarrollo humano. Si las dependencias en `package.json` usan rangos semánticos flexibles (como `^1.2.0` o `~2.1.0`), `npm install` intenta buscar versiones nuevas compatibles en el registro público. Si una subdependencia de terceros publica una versión con un bug el martes a las 11:00, tu build fallará aunque nadie haya tocado tu código.
- **`npm ci` (Clean Install):** Diseñado específicamente para entornos de CI/CD. **Ignora los rangos de `package.json` y se rige al 100% por el árbol exacto del archivo `package-lock.json`**. Si el hash criptográfico no coincide byte por byte, la compilación se detiene.

### 2. Reglas para Blindar el Pipeline
1. **Sustituye en tu script de CI:**
   ```yaml
   # ANTES:
   - npm install
   # AHORA:
   - npm ci
   ```
2. **Verifica que `package-lock.json` esté en Git:** Comprueba que `.gitignore` no esté ignorando por error el archivo `package-lock.json`.
3. **Caché de Descargas de NPM:** Configura la caché de CI sobre la carpeta `~/.npm` para evitar depender de la conexión de red con el registro de npm en cada commit, acelerando el paso de build en un 60%."""
    },
    {
        "user": "En un clúster de Kubernetes en AWS, al reprogramar un pod con base de datos en otro nodo trabajador, el nuevo pod se queda atascado indefinidamente en estado `ContainerCreating`. El comando `kubectl describe pod` arroja el error: 'Warning FailedAttachVolume: Multi-Attach error for volume ... Volume is already exclusively attached to one node'. ¿Cómo desatascar el volumen?",
        "think": "Contexto: Pod atascado en ContainerCreating por Multi-Attach error en volumen EBS de AWS.\nEvaluación: Los volúmenes EBS gp2/gp3 son ReadWriteOnce (RWO); AWS no permite conectar el volumen a dos nodos a la vez mientras el nodo previo no lo libere.\nConclusión: Forzar detach del volumen EBS en la consola/CLI de AWS o eliminar el VolumeAttachment huérfano.",
        "assistant": """Este error clásico ocurre porque los volúmenes de disco **AWS EBS estándar (gp2/gp3/io2) tienen modo de acceso `ReadWriteOnce (RWO)`**: solo pueden estar físicamente conectados a una única máquina virtual EC2 a la vez:

### 1. Por qué Ocurre el Bloqueo
- Cuando el nodo de Kubernetes anterior falló o entró en estado *NotReady*, el controlador de AWS no pudo desmontar limpiamente el disco EBS del nodo antiguo.
- El programador (*scheduler*) de Kubernetes levantó el pod sustituto en un **nuevo nodo físico**.
- Cuando el nuevo nodo intenta conectar el disco EBS, la API de AWS rechaza la petición porque la consola de AWS aún registra que el disco pertenece al nodo antiguo, bloqueando el pod en `ContainerCreating`.

### 2. Cómo Desatascarlo en 2 Minutos
1. **Localizar el recurso VolumeAttachment huérfano en Kubernetes:**
   ```bash
   kubectl get volumeattachment | grep <id-del-volumen-ebs>
   ```
2. **Eliminar el enlace huérfano:**
   ```bash
   kubectl delete volumeattachment <nombre-del-volume-attachment>
   ```
3. **Si el volumen sigue atascado en AWS:**
   - Abre la consola de AWS EC2 > Volumes > Busca el ID del volumen (`vol-0123456789abcdef`).
   - Verás que el estado es *in-use* asociado a la instancia antigua.
   - Pulsa **Actions > Force Detach Volume**.
   - En menos de 10 segundos, el nuevo nodo de Kubernetes detectará el disco libre, lo conectará al pod y el contenedor pasará inmediatamente a estado `Running`."""
    },
    {
        "user": "En un servidor Linux en producción que gestiona miles de conexiones HTTP, las nuevas conexiones empiezan a rechazarse de golpe con el error en los logs: 'socket() failed (24: Too many open files)'. El servidor tiene memoria RAM y CPU de sobra. ¿Cómo solucionar y hacer permanente este límite?",
        "think": "Contexto: Error Too many open files en servidor Linux saturando conexiones de red.\nEvaluación: El límite de descriptores de archivo por proceso (ulimit -n) o del sistema (fs.file-max) ha sido superado.\nConclusión: Incrementar nofile en limits.conf y ajustar LimitNOFILE en el servicio systemd.",
        "assistant": """En sistemas Unix, **todo es un archivo**: cada socket de red TCP, cada archivo en disco y cada conexión de base de datos consume un descriptor de archivo (*File Descriptor / FD*). El error indica que el proceso ha alcanzado el límite máximo permitido por el sistema operativo:

### 1. Diagnóstico del Límite Actual
Comprueba el límite de descriptores para el usuario del servicio (ej. `www-data` o `nginx`):
```bash
# Ver límite suave y duro actual:
ulimit -n
# Ver descriptores abiertos actualmente por el proceso (sustituye PID):
ls -1 /proc/<PID>/fd | wc -l
```
En muchas distribuciones Linux, el límite por defecto viene fijado en unos ridículos **1.024 descriptores**, lo que colapsa cualquier servidor web al recibir más de 1.000 usuarios concurrentes.

### 2. Solución Definitiva en 2 Pasos
1. **Configuración en el Servicio de Systemd (Recomendado para Nginx / Node / Docker):**
   Los servicios gestionados por Systemd ignoran `limits.conf`. Debes editar la unidad del servicio:
   ```bash
   sudo systemctl edit nginx
   ```
   Añade en el archivo de reemplazo:
   ```ini
   [Service]
   LimitNOFILE=65535
   ```
   Recarga y reinicia:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart nginx
   ```

2. **Ajuste Global a Nivel de Sistema Operativo:**
   En `/etc/security/limits.conf` añade al final:
   ```text
   * soft nofile 65535
   * hard nofile 65535
   ```
   Y en `/etc/sysctl.conf`: `fs.file-max = 2097152` para asegurar que el kernel acepte millones de conexiones simultáneas sin inmutarse."""
    },
    {
        "user": "Bajo campañas de publicidad con picos repentinos de 4.000 peticiones por segundo, nuestro proxy Nginx empieza a rechazar peticiones con el error en error.log: 'connect() to 127.0.0.1:8000 failed (111: Connection refused)' y los clientes ven errores 'Connection reset by peer'. ¿Qué parámetro del kernel y de Nginx está saturado?",
        "think": "Contexto: Caídas por Connection refused y reset by peer en Nginx bajo picos de 4.000 req/s.\nEvaluación: El backlog de la cola de conexiones TCP del kernel (somaxconn) o worker_connections en Nginx se satura.\nConclusión: Aumentar net.core.somaxconn en el kernel y worker_connections y backlog en Nginx.",
        "assistant": """El error `Connection refused` contra `127.0.0.1:8000` significa que **el socket de escucha de tu backend (Gunicorn, Node, Puma) ha llenado por completo su cola de conexiones pendientes (*TCP listen backlog*)** y el sistema operativo rechaza las nuevas conexiones antes de que la aplicación pueda aceptarlas:

### 1. Los Dos Cuellos de Botella Clave

1. **La Cola de Conexiones TCP del Núcleo Linux (`somaxconn`):**
   Por defecto, el kernel de Linux limita la cola de espera de sockets a solo 128 o 4096 conexiones pendientes. Con una ráfaga de 4.000 peticiones por segundo, la cola se llena en 50 milisegundos.
2. **El Límite de `worker_connections` en Nginx:**
   Si cada worker de Nginx solo tiene asignadas 512 o 1024 conexiones, se queda sin slots libres para mantener la conexión con el cliente y con el backend simultáneamente.

### 2. Configuración de Alto Rendimiento en 3 Pasos
1. **Aumentar la Cola TCP en el Kernel de Linux:**
   Edita `/etc/sysctl.conf` y añade:
   ```ini
   # Elevar la cola de conexiones entrantes pendientes:
   net.core.somaxconn = 65535
   net.ipv4.tcp_max_syn_backlog = 65535
   ```
   Aplica los cambios inmediatamente con: `sudo sysctl -p`.

2. **Optimizar `nginx.conf`:**
   ```nginx
   events {
       worker_connections 8192;
       use epoll;
       multi_accept on;
   }
   ```

3. **Aumentar el Backlog en el Servidor de Aplicaciones:**
   - Si usas Gunicorn: `gunicorn --backlog 4096 ...`
   - Si usas Node.js: `server.listen(8000, 4096)`
   Con estos tres ajustes combinados, el servidor absorberá picos de decenas de miles de conexiones concurrentes sin volver a rechazar un solo paquete."""
    }
]
