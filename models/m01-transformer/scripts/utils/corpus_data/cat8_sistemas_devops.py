r"""Categoría 8: Sistemas Operativos, Infraestructura, DevOps y Redes."""

def get_samples():
    samples = []

    muestras = [
        ("¿Cómo crear un archivo de servicio en systemd para ejecutar un proceso de fondo en Linux?",
         "Creación de servicio en systemd.",
         """Crear el archivo de configuración en `/etc/systemd/system/mi_servicio.service`:

```ini
[Unit]
Description=Servicio de Inferencia M0.1
After=network.target

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/m01-servicio
ExecStart=/opt/m01-servicio/venv/bin/python main.py
Restart=always
RestartSec=5s
Environment="PYTHONUNBUFFERED=1"
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

Habilitar e iniciar el servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mi_servicio.service
```"""),

        ("¿Cómo funciona el OOM Killer (Out of Memory Killer) de Linux y cómo proteger un proceso crítico?",
         "Mecanismo de OOM Killer en Linux.",
         """Cuando la memoria física y el espacio de intercambio (*swap*) se agotan por completo, el kernel invoca al OOM Killer para terminar procesos y evitar un pánico del kernel:

1. **Cálculo de penalización (`oom_score`)**:
   El kernel calcula una puntuación basada en el porcentaje de RAM ocupada por el proceso y su tiempo de vida.
2. **Ajuste de protección (`oom_score_adj`)**:
   Se puede modificar el valor en `/proc/<PID>/oom_score_adj` (rango de -1000 a 1000):
   - `-1000`: Inmunidad total; el kernel nunca terminará este proceso por OOM.
   - `1000`: Máxima prioridad de terminación.

Para fijar la inmunidad en tiempo de ejecución:
```bash
echo -1000 | sudo tee /proc/<PID>/oom_score_adj
```"""),

        ("¿Cuál es la diferencia entre buffers y cache en la salida del comando `free -m` en Linux?",
         "Buffers vs Cache en memoria de Linux.",
         """- **Buffers (Búferes)**:
  - Memoria asignada por el kernel para almacenar metadatos del sistema de archivos y bloques de datos crudos en tránsito hacia o desde dispositivos de bloque (disco).
  - Gestiona operaciones de E/S temporales.
- **Cache (Page Cache)**:
  - Memoria utilizada para retener en RAM páginas completas de archivos leídos recientemente desde el almacenamiento secundario.
  - Si un proceso vuelve a leer el mismo archivo, se sirve instantáneamente desde la Page Cache sin acceder al disco.
  - El kernel libera esta memoria de forma transparente si los procesos de usuario requieren memoria anónima activa."""),

        ("Explica cómo afinar el proceso de Autovacuum en PostgreSQL para tablas con alto volumen de escrituras.",
         "Ajuste de Autovacuum en PostgreSQL.",
         """El proceso de Autovacuum limpia tuplas muertas (*dead tuples*) generadas por `UPDATE` y `DELETE`. Para tablas críticas con alta tasa de inserción/actualización:

```sql
ALTER TABLE transacciones SET (
    autovacuum_vacuum_scale_factor = 0.05,  -- Iniciar vacuum al modificar el 5% de filas (por defecto es 20%)
    autovacuum_vacuum_threshold = 1000,     -- Umbral minimo de 1000 tuplas muertas
    autovacuum_vacuum_cost_limit = 1000,    -- Incrementar presupuesto de E/S por ciclo
    autovacuum_vacuum_cost_delay = 2        -- Reducir pausa entre ciclos de limpieza
);
```
Esto previene el crecimiento desmedido (*bloat*) de la tabla y mantiene los índices compactos sin degradar consultas concurrentes."""),

        ("¿Cómo utilizar `git bisect` para localizar el commit que introdujo un error en el proyecto?",
         "Depuración con git bisect.",
         """1. Iniciar la sesión de búsqueda binaria:
```bash
git bisect start
```
2. Marcar el commit actual (con el fallo) como defectuoso:
```bash
git bisect bad
```
3. Indicar un commit previo conocido que funcionaba correctamente:
```bash
git bisect good v1.0.0
```
4. Git colocará el árbol de trabajo en el commit intermedio. Probar el código o ejecutar pruebas automáticas:
   - Si funciona: `git bisect good`
   - Si falla: `git bisect bad`
5. Al finalizar, Git identificará el commit exacto causante de la regresión. Salir con:
```bash
git bisect reset
```"""),

        ("¿Cómo funciona el cifrado autenticado AES-GCM frente a AES-CBC?",
         "AES-GCM frente a AES-CBC.",
         """- **AES-CBC (Cipher Block Chaining)**:
  - Cifra bloques encadenando la salida previa con la siguiente mediante XOR.
  - Proporciona **únicamente confidencialidad**; no garantiza integridad ni autenticidad.
  - Vulnerable a ataques de oráculo de relleno (*Padding Oracle Attacks*) si no se combina manualmente con HMAC (Encrypt-then-MAC).
- **AES-GCM (Galois/Counter Mode)**:
  - Cifrado en modo contador combinado con multiplicación en cuerpos de Galois para generar una etiqueta de autenticación (*Auth Tag*).
  - Proporciona **Cifrado Autenticado con Datos Asociados (AEAD)**: garantiza confidencialidad, integridad y autenticidad en una sola pasada.
  - Altamente paralelizable por hardware mediante instrucciones AES-NI en procesadores modernos."""),

        ("Escribe un Docker Compose para desplegar un entorno con FastAPI, PostgreSQL y Redis.",
         "Docker Compose para FastAPI, Postgres y Redis.",
         """```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:clave_segura@db:5432/m01_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: clave_segura
      POSTGRES_DB: m01_db
    volumes:
      - datos_pg:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  datos_pg:
```"""),

        ("¿Qué es y cómo opera el algoritmo de Jitter en reintentos de red?",
         "Reintentos con retroceso y Jitter.",
         r"""Cuando un servicio central colapsa y miles de clientes reintentan simultáneamente con intervalos exponenciales fijos ($2^k$), los reintentos convergen en ráfagas sincronizadas que vuelven a tumbar al servidor (*efecto manada*).

**Jitter** introduce una perturbación aleatoria al tiempo de espera:
$$\text{Espera} = \text{random}(0, \min(M, R_{\text{base}} \times 2^{\text{intento}}))$$
o mediante *Decorrelated Jitter*:
$$T_i = \min(M, \text{random}(R_{\text{base}}, T_{i-1} \times 3))$$
Esto distribuye las solicitudes de reintento uniformemente a lo largo del tiempo, suavizando la carga sobre el servicio receptor."""),

        ("¿Cómo optimizar parámetros de red en Linux para un servidor con alto volumen de conexiones TCP?",
         "Afinación de TCP en Linux.",
         """Añadir las siguientes directivas a `/etc/sysctl.conf`:

```ini
# Incrementar el limite de conexiones en espera (backlog)
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Reutilizar sockets en estado TIME_WAIT para conexiones salientes
net.ipv4.tcp_tw_reuse = 1

# Reducir tiempo de retencion de conexiones cerradas
net.ipv4.tcp_fin_timeout = 15

# Rangos de puertos efimeros
net.ipv4.ip_local_port_range = 1024 65535

# Tamano maximo de buffers de recepcion y envio
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
```
Aplicar inmediatamente con `sudo sysctl -p`."""),

        ("¿Cuál es la diferencia entre sondas Liveness y Readiness en Kubernetes?",
         "Liveness Probe vs Readiness Probe en Kubernetes.",
         """- **Liveness Probe (Sonda de Vida)**:
  - Determina si el contenedor sigue en ejecución activa o se encuentra en un estado irrecuperable (ej. deadlock total).
  - Si la sonda falla reiteradamente, Kubernetes **reinicia el contenedor**.
- **Readiness Probe (Sonda de Disponibilidad)**:
  - Determina si el contenedor está listo para recibir tráfico de la red (ej. si ya cargó modelos en memoria o completó migraciones).
  - Si la sonda falla, Kubernetes **retira la dirección IP del Pod del balanceador del Servicio**, impidiendo que le lleguen peticiones sin reiniciar el contenedor."""),

        ("¿Cómo se configuran límites de CPU y memoria en Linux mediante cgroups v2?",
         "Límites con cgroups v2.",
         """En cgroups v2, la jerarquía se gestiona como un árbol unificado en `/sys/fs/cgroup/`:

1. Crear un grupo de control:
   ```bash
   sudo mkdir /sys/fs/cgroup/m01_servicio
   ```
2. Establecer límite estricto de memoria (ej. 2 GB):
   ```bash
   echo "2G" | sudo tee /sys/fs/cgroup/m01_servicio/memory.max
   ```
3. Establecer límite de CPU (ej. 2 núcleos completos = 200,000 microsegundos por período de 100,000):
   ```bash
   echo "200000 100000" | sudo tee /sys/fs/cgroup/m01_servicio/cpu.max
   ```
4. Asociar el proceso en ejecución al cgroup:
   ```bash
   echo "<PID>" | sudo tee /sys/fs/cgroup/m01_servicio/cgroup.procs
   ```"""),

        ("¿Cómo configurar PgBouncer para multiplexar conexiones a PostgreSQL en modo transacción?",
         "Configuración de PgBouncer.",
         """En el archivo `pgbouncer.ini`:

```ini
[databases]
m01_db = host=127.0.0.1 port=5432 dbname=m01_db

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt

# Modo de agrupamiento por transaccion (Transaction Pooling)
pool_mode = transaction

# Limites de conexion
max_client_conn = 10000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
```
**Efecto**: Miles de clientes concurrentes comparten un conjunto fijo de 25 conexiones reales a PostgreSQL; cada conexión se devuelve al pool en cuanto finaliza cada bloque `COMMIT` o `ROLLBACK`."""),

        ("¿Qué diferencia hay entre RAID 5, RAID 6 y RAID 10?",
         "Comparativa de niveles RAID.",
         """- **RAID 5**:
  - Paridad distribuida en todos los discos.
  - Tolera la falla de **1 disco**.
  - Capacidad útil: $(N - 1) \times \text{capacidad}$.
  - Penalización de escritura por cálculo de paridad (*write penalty* de 4 operaciones de E/S).
- **RAID 6**:
  - Doble paridad distribuida.
  - Tolera la falla de hasta **2 discos simultáneos**.
  - Capacidad útil: $(N - 2) \times \text{capacidad}$.
- **RAID 10 (1+0)**:
  - Espejado (*mirroring*) combinado con seccionamiento (*striping*).
  - Tolera múltiples fallas de disco siempre que no pertenezcan al mismo sub-espejo.
  - Capacidad útil: $N / 2$.
  - Máximo rendimiento de E/S en lecturas y escrituras aleatorias al no computar paridad."""),

        ("¿Cómo recuperar un commit perdido en Git tras un `git reset --hard` accidental?",
         "Recuperación con git reflog.",
         """1. Consultar el historial de referencias de Git (reflog) para ver todas las posiciones previas de HEAD:
```bash
git reflog
```
2. Identificar el identificador SHA del commit previo a la ejecución del reset (por ejemplo, `HEAD@{1}` o `a1b2c3d`).
3. Crear una nueva rama apuntando directamente a ese commit recuperado:
```bash
git checkout -b rama-recuperada a1b2c3d
```
El estado del proyecto quedará completamente restaurado sin pérdida de historial."""),

        ("Explica la diferencia entre permisos especiales SUID, SGID y Sticky Bit en Linux.",
         "Permisos especiales SUID, SGID y Sticky Bit.",
         """- **SUID (*Set User ID*, bit 4000)**:
  - Aplicado a archivos ejecutables.
  - El proceso se ejecuta con los privilegios del **propietario del archivo**, no del usuario que lo invoca (ej. `/usr/bin/passwd`).
- **SGID (*Set Group ID*, bit 2000)**:
  - En ejecutables: Corre con los privilegios del grupo propietario.
  - En directorios: Los archivos nuevos creados heredan automáticamente el grupo del directorio padre.
- **Sticky Bit (bit 1000)**:
  - Aplicado a directorios (ej. `/tmp`).
  - Solo el propietario de un archivo (o root) puede eliminarlo o renombrarlo, impidiendo que otros usuarios borren archivos ajenos en directorios compartidos."""),

        ("¿Cómo asegurar un servidor SSH en producción contra accesos no autorizados?",
         "Fortalecimiento de SSH (Hardening).",
         """Modificar `/etc/ssh/sshd_config`:

```ini
# Deshabilitar autenticacion por contrasena (solo llaves publicas Ed25519)
PasswordAuthentication no
PubkeyAuthentication yes

# Prohibir inicio de sesion directo como root
PermitRootLogin no

# Limitar intentos maximos de autenticacion por sesion
MaxAuthTries 3

# Desactivar reenvio de puertos no requeridos
AllowAgentForwarding no
AllowTcpForwarding no
X11Forwarding no

# Cambiar puerto predeterminado (opcional para reducir ruido en logs)
Port 2222
```
Reiniciar el daemon de forma segura:
```bash
sudo sshd -t && sudo systemctl restart sshd
```"""),

        ("¿Cómo diagnosticar una alta latencia de resolución DNS en un servidor Linux?",
         "Diagnóstico de resolución DNS en Linux.",
         """1. Medir el tiempo de respuesta con `dig`:
```bash
dig @127.0.0.53 midominio.com +stats | grep "Query time"
```
2. Inspeccionar la configuración de servidores de nombres en `/etc/resolv.conf`:
   - Verificar si apunta a `systemd-resolved` o a servidores inaccesibles.
3. Evaluar el estado de `systemd-resolved`:
   ```bash
   resolvectl status
   ```
4. Limpiar la caché local de DNS para descartar entradas obsoletas:
   ```bash
   sudo resolvectl flush-caches
   ```
5. Comprobar si existe ordenamiento ineficiente en `/etc/nsswitch.conf` (`hosts: files dns`)."""),

        ("¿Cuál es la diferencia entre almacenamiento de bloques, de archivos y de objetos?",
         "Almacenamiento: Bloques vs Archivos vs Objetos.",
         """- **Almacenamiento de Bloques (*Block Storage*, ej. EBS, iSCSI)**:
  - Expone volúmenes crudos divididos en bloques de tamaño fijo.
  - Máximo rendimiento y mínima latencia; ideal para sistemas de archivos de SO y bases de datos relacionales.
- **Almacenamiento de Archivos (*File Storage*, ej. NFS, SMB)**:
  - Expone un sistema de archivos jerárquico compartido accesible concurrentemente por múltiples clientes a través de la red.
- **Almacenamiento de Objetos (*Object Storage*, ej. S3, MinIO)**:
  - Estructura plana accesible vía API REST (HTTP).
  - Almacena el dato junto con metadatos extendidos y un identificador global único.
  - Altamente escalable de forma ilimitada a bajo costo; óptimo para copias de seguridad, artefactos y modelos entrenados."""),

        ("¿Cómo opera el despliegue Blue-Green frente al despliegue Canary?",
         "Estrategias de despliegue: Blue-Green vs Canary.",
         """- **Blue-Green Deployment**:
  - Mantiene dos entornos de producción idénticos: Azul (versión activa) y Verde (versión nueva inactiva).
  - Se despliega y valida en Verde; luego el balanceador conmuta el 100% del tráfico instantáneamente.
  - Reversión inmediata (*rollback*) en caso de anomalías conmutando de regreso a Azul.
- **Canary Deployment**:
  - Introduce la versión nueva a un porcentaje mínimo de usuarios reales (ej. 2% o 5%) mientras el 95% restante sigue en la versión estable.
  - Se monitorean métricas de error y latencia; si son estables, el porcentaje de tráfico se incrementa progresivamente hasta alcanzar el 100%."""),

        ("Escribe una regla de Firewall con iptables para bloquear paquetes mal formados y ataques de escaneo de puertos SYN-FIN.",
         "Reglas de iptables contra escaneo de puertos.",
         """```bash
# Bloquear paquetes TCP con combinaciones invalidas de flags (SYN-FIN scan)
sudo iptables -A INPUT -p tcp --tcp-flags SYN,FIN SYN,FIN -j DROP

# Bloquear paquetes NULL scan (sin ningun flag activo)
sudo iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Bloquear paquetes XMAS scan (flags FIN, PSH, URG activos)
sudo iptables -A INPUT -p tcp --tcp-flags ALL FIN,PSH,URG -j DROP

# Aceptar paquetes pertenecientes a conexiones ya establecidas
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```""")
    ]

    for q, th, resp in muestras:
        samples.append({
            "user": q,
            "think": f"""Consulta de sistemas/infraestructura: {th}
Contexto: Administración de sistemas, redes y DevOps.
Respuesta: Técnica, precisa y directa.""",
            "response": resp
        })

    return samples
