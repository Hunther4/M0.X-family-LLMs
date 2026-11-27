"""
Categoría 6: Planificación de tareas paso a paso (16 escenarios)
Bloques <think> concisos de retrospectiva contextual y síntesis metodológica.
"""

SCENARIOS_CAT6 = [
    {
        "user": "Tenemos una tabla `usuarios` en PostgreSQL con 40 millones de registros y 150 GB de datos en producción. Necesitamos añadir una nueva columna `identificador_fiscal` que sea `NOT NULL` con un valor por defecto calculado y un índice único, sin bloquear las lecturas ni escrituras de los usuarios (Zero Downtime). ¿Cuál es el plan de migración paso a paso?",
        "think": "Contexto: Alteración de esquema en tabla crítica de 40M filas sin provocar paradas de servicio.\nEvaluación: Ejecutar ALTER TABLE con NOT NULL bloquea la tabla completa durante horas; se requiere patrón expand-contract.\nConclusión: Plan en 4 fases: añadir columna nullable, backfill en lotes, índice concurrente y validación de restricción.",
        "assistant": """Modificar directamente una tabla de 40 millones de filas con `ALTER TABLE usuarios ADD COLUMN ... NOT NULL` bloquearía la tabla con un bloqueo exclusivo (`AccessExclusiveLock`) durante decenas de minutos, congelando todo el servicio. Sigue este **plan de migración en 4 fases (Patrón Expand/Contract)**:

### Fase 1: Añadir Columna Permitiendo Nulos (Tiempo: < 1 segundo)
Añade la columna sin restricciones estrictas para que no bloquee escrituras:
```sql
ALTER TABLE usuarios ADD COLUMN identificador_fiscal VARCHAR(50);
```

### Fase 2: Relleno de Datos en Segundo Plano por Lotes (*Backfill*)
No actualices los 40 millones de registros en una sola consulta. Ejecuta un script en segundo plano que actualice bloques de **5.000 filas cada vez con pausas**:
```sql
-- Ejecutar en bucle iterando por bloques de ID:
UPDATE usuarios 
SET identificador_fiscal = CONCAT('ES-', id) 
WHERE id BETWEEN 1 AND 5000 AND identificador_fiscal IS NULL;
-- Esperar 100 ms entre lotes para no saturar I/O ni replicación.
```
*(Simultáneamente, despliega la nueva versión de tu backend para que empiece a escribir en la nueva columna en cualquier registro nuevo).*

### Fase 3: Crear el Índice Único de Forma Concurrente
Nunca uses `CREATE UNIQUE INDEX` estándar (bloquearía escrituras). Utiliza:
```sql
CREATE UNIQUE INDEX CONCURRENTLY idx_usuarios_identificador_fiscal 
ON usuarios (identificador_fiscal);
```
La cláusula `CONCURRENTLY` crea el índice en segundo plano sin bloquear transacciones de usuarios activos.

### Fase 4: Aplicar la Restricción NOT NULL sin Escanear la Tabla
En PostgreSQL moderno, aplica una restricción de comprobación primero y valida después:
```sql
-- 1. Añadir restricción sin validar datos antiguos (adquisición instantánea):
ALTER TABLE usuarios 
ADD CONSTRAINT check_identificador_fiscal_not_null 
CHECK (identificador_fiscal IS NOT NULL) NOT VALID;

-- 2. Validar en segundo plano sin bloqueos:
ALTER TABLE usuarios 
VALIDATE CONSTRAINT check_identificador_fiscal_not_null;
```
La migración se completa con **cero milisegundos de tiempo de inactividad**."""
    },
    {
        "user": "Nuestra plataforma de pagos opera en AWS en la región `eu-west-1` (Irlanda). Queremos realizar nuestro primer simulacro anual de Recuperación ante Desastres (DRP) simulando una caída total de la región y conmutando (failover) a `eu-central-1` (Fráncfort). Tenemos RTO < 30 min y RPO < 5 min. ¿Cómo estructurar el plan de ejecución y verificación paso a paso?",
        "think": "Contexto: Simulacro de failover regional en AWS con objetivos estrictos RTO < 30m y RPO < 5m.\nEvaluación: Un corte no controlado en producción arriesga corrupción de datos; se debe aislar el simulacro con ventanas controladas.\nConclusión: Plan estructurado en 5 etapas: preparación previa, drenaje de tráfico, promoción de BD, cambio de DNS y retorno ordenado.",
        "assistant": """Para ejecutar un simulacro de Disaster Recovery (DRP) sin causar pérdidas accidentales de datos en una plataforma financiera, sigue este plan sistemático de 5 etapas:

### 1. Fase Previa de Preparación (T - 7 Días)
- **Verificación del Lag de Replicación:** Comprueba que la réplica de lectura en Fráncfort (`Aurora Global Database` o réplica cruzada) tenga un retardo (*replication lag*) inferior a **1 segundo** para garantizar que cumples holgadamente el RPO < 5 minutos.
- **Auditoría de Secretos y Parámetros:** Verifica que las variables de entorno, claves de KMS y certificados en `eu-central-1` estén sincronizados con la región principal.
- **Reducción del TTL de DNS (T - 24 Horas):** Reduce el TTL de los registros en Route 53 a **60 segundos** para que la propagación del cambio de tráfico sea casi instantánea durante el simulacro.

### 2. Ejecución del Corte (Ventana de Mantenimiento / Simulación)
1. **Minuto 0:** Bloquea las escrituras entrantes en el API Gateway principal activando una pantalla estática de mantenimiento.
2. **Minuto 3:** Espera a que el lag de replicación de base de datos caiga a 0 milisegundos exactos.
3. **Minuto 5 (Promoción de Base de Datos):** Promueve el clúster de Fráncfort (`eu-central-1`) a clúster de escritura principal primario.
4. **Minuto 10 (Arranque de Cómputo):** Escala las tareas de backend (ECS/EKS) en Fráncfort para que verifiquen la conexión con la base de datos promovida.
5. **Minuto 15 (Conmutación de Tráfico):** Actualiza el enrutamiento de Route 53 mediante la política de *Failover* apuntando los dominios al balanceador ALB de Fráncfort.

### 3. Verificación de Salud en Destino (Minuto 16 a 25)
- Ejecuta una batería automatizada de pruebas sintéticas E2E (*Smoke Tests*):
  - Creación de una transacción de prueba.
  - Consulta de saldos y emisión de webhooks.
  - Verificación de latencias y ausencia de errores 5xx.

### 4. Retorno Ordenado (Failback)
- Reconfigura la replicación inversa para que los datos generados durante la prueba en Fráncfort viajen de vuelta a Irlanda antes de restaurar el tráfico original.
- Documenta el tiempo real empleado frente al RTO objetivo."""
    },
    {
        "user": "Tenemos una aplicación bancaria monolítica con 10 años de antigüedad que procesa préstamos, cuentas y tarjetas. Queremos desacoplar el módulo de tarjetas a un microservicio independiente utilizando el patrón Strangler Fig. ¿Cómo diseñar la hoja de ruta en 4 fases sin interrumpir el negocio?",
        "think": "Contexto: Desacoplar módulo de tarjetas de un monolito bancario mediante patrón Strangler Fig.\nEvaluación: Cortar la base de datos de golpe rompe integridad; se requiere enrutamiento perimetral y sincronización dual.\nConclusión: Hoja de ruta en 4 fases: capa de interceptación, implementación paralela, shadow traffic y corte definitivo.",
        "assistant": """El patrón Strangler Fig (Estrangulamiento) permite extraer el módulo de tarjetas reemplazando gradualmente sus funciones sin acometer una reescritura traumática. Aplica esta hoja de ruta en 4 fases:

### Fase 1: Interceptación Perimetral (Día 1 a Semana 3)
1. Despliega un **API Gateway (Kong, Traefik o AWS API Gateway)** por delante del monolito existente.
2. Todo el tráfico web y móvil apunta ahora al Gateway, que inicialmente reenvía el 100% de las peticiones hacia el viejo monolito de forma transparente.
3. Define los contratos de API y eventos para el nuevo servicio de tarjetas utilizando especificaciones OpenAPI.

### Fase 2: Implementación del Nuevo Servicio y Sincronización de Datos (Semanas 4 a 8)
1. Desarrolla el microservicio de tarjetas con su **propia base de datos independiente**.
2. **Estrategia de Doble Escritura / CDC (Change Data Capture):**
   - Configura una herramienta de captura de cambios como **Debezium sobre la base de datos del monolito**.
   - Cada vez que se crea o modifica una tarjeta en el monolito, Debezium publica el evento en Kafka y el nuevo microservicio actualiza su base de datos en tiempo real, garantizando paridad total de datos.

### Fase 3: Pruebas en la Sombra (*Shadow Traffic* / Dark Launching) (Semanas 9 a 11)
1. Configura el API Gateway para que clone las peticiones entrantes de tarjetas:
   - La petición real sigue atendiéndose por el viejo monolito (la respuesta vuelve al usuario).
   - Una copia idéntica y asíncrona se envía al nuevo microservicio.
2. Compara automáticamente las respuestas de ambos sistemas: tiempos de respuesta, códigos HTTP y datos devueltos hasta constatar un **100% de paridad sin errores**.

### Fase 4: Corte Definitivo y Poda del Monolito (Semana 12)
1. Cambia la regla del API Gateway: las rutas `/api/tarjetas/*` se enrutan directamente al nuevo microservicio como fuente de la verdad.
2. Elimina el código huérfano de tarjetas en el monolito y desactiva las tablas antiguas."""
    },
    {
        "user": "Tengo 32 años, corro 10 km dos veces por semana a ritmo suave y quiero preparar mi primer maratón de 42 km dentro de 6 meses (24 semanas). ¿Cómo estructurar un plan de entrenamiento y nutrición progresivo evitando lesiones por sobreuso?",
        "think": "Contexto: Corredor amateur de 10 km preparando su primer maratón de 42 km en 24 semanas.\nEvaluación: Aumentar volumen semanal rápido genera fascitis o periostitis; la clave es la progresión del 10% y tiradas largas en Z2.\nConclusión: Periodización en 4 bloques de 6 semanas con descarga cada 4 semanas, fuerza y nutrición intra-carrera.",
        "assistant": """Pasar de 20 km semanales a completar 42 km exige **periodización fisiológica estricta para adaptar tendones y articulaciones**, no solo pulmones. Estructura tus 24 semanas en este macrociclo:

### 1. Los 4 Bloques de Entrenamiento (Mesociclos)
- **Bloque 1: Construcción de Base Aeróbica (Semanas 1 a 6):**
  - Frecuencia: 3 días de carrera + 2 días de fuerza en gimnasio (sentadillas, zancadas, gemelos y core: **innegociables para evitar el colapso de cadera**).
  - Volumen: Pasa de 25 km a 38 km semanales. La tirada larga del fin de semana sube de 12 km a 18 km a ritmo muy cómodo en Zona 2 (pudiendo hablar en frases completas).
- **Bloque 2: Sobrecarga Progresiva y Ritmo Maratón (Semanas 7 a 14):**
  - Frecuencia: 4 días de carrera + 1 día de fuerza.
  - Introduce 1 sesión semanal de cambios de ritmo o series largas (ej. 4 x 2.000 m a ritmo de media maratón).
  - Las tiradas largas de domingo progresan: 20 km -> 22 km -> 26 km. Aplica una **semana de descarga (reduciendo volumen un 30%) cada 4 semanas**.
- **Bloque 3: Fase Específica y Tiradas Clave (Semanas 15 a 21):**
  - Pico de kilometraje: 55 km a 65 km semanales.
  - Ejecuta dos tiradas máximas de **30 km y 32 km** (Semanas 18 y 20) para entrenar la tolerancia al vaciado de glucógeno y probar la suplementación digestiva.
- **Bloque 4: Tapering / Descarga Previa (Semanas 22 a 24):**
  - Semana 22: -25% de volumen. Semana 23: -50%. Semana 24 (carrera): Solo trotes ligeros de 20 minutos con rectas.

### 2. Estrategia Nutricional y Digestiva
- **Entrenamiento del Estómago:** El maratón se pierde en el estómago. En las tiradas de más de 90 minutos debes ingerir **40 g a 60 g de carbohidratos por hora** (geles energéticos con agua cada 30-40 minutos). Nunca estrenes geles el día de la prueba.
- **Semana Previa:** Carga progresiva de hidratos los 3 días previos (7-8 g de carbohidrato por kilo de peso corporal) y reducción de fibra para evitar paradas gastrointestinales."""
    },
    {
        "user": "Nuestra plataforma fintech sufrió una caída crítica de 45 minutos durante el día de ayer, impidiendo pagos con tarjeta. La dirección exige un informe post-mortem inmediato. ¿Cómo estructurar un post-mortem sin culpables (Blameless Post-Mortem) y un plan de acción para que el incidente no se repita jamás?",
        "think": "Contexto: Caída crítica de 45 minutos en pasarela de pagos fintech requiriendo post-mortem blameless.\nEvaluación: Buscar culpables individuales oculta las fallas sistémicas; se necesita análisis de causa raíz con 5 Porqués y acciones correctivas.\nConclusión: Estructurar informe en cronología, causa raíz sistémica, impacto de negocio y acciones preventivas con responsables.",
        "assistant": """El principio fundamental de un **Blameless Post-Mortem (Post-Mortem sin Culpables)** es asumir que las personas actúan de buena fe con la información disponible. Si un ingeniero pudo pulsar un botón y tumbar el sistema, **la culpa no es del ingeniero, sino de la arquitectura que permitía cometer ese fallo sin barreras de seguridad**:

### 1. Estructura Oficial del Informe Post-Mortem
1. **Resumen Ejecutivo y Métricas de Impacto:**
   - Fecha y ventana de afectación: 14:15 a 15:00 UTC (45 minutos de duración).
   - Impacto en clientes: 12.400 intentos de pago fallidos; 180.000 € en volumen de transacciones rechazadas temporalmente.
   - Severidad: P1 / Sev-1 (Interrupción total del servicio principal).
2. **Cronología Minuto a Minuto (*Timeline*):**
   - *14:10:* El equipo de infraestructura aplica un cambio en la configuración del cortafuegos.
   - *14:15:* Las alertas de Prometheus disparan la alarma por subida del ratio de errores 5xx en el checkout.
   - *14:22:* El equipo de guardias confirma la pérdida de conectividad con el procesador bancario.
   - *14:38:* Se identifica que la regla de firewall bloqueó el rango de IPs del proveedor de pagos.
   - *14:45:* Se ejecuta el rollback de la regla de red.
   - *15:00:* Tráfico restablecido al 100% y alertas normalizadas.

### 2. Análisis de Causa Raíz (Técnica de los 5 Porqués)
- *¿Por qué cayeron los pagos?* Porque se bloquearon las IPs de salida hacia el banco.
- *¿Por qué se bloquearon?* Porque se desplegó una regla de red errónea en producción.
- *¿Por qué se desplegó?* Porque se aplicó de forma manual directamente en la consola sin pasar por pipeline.
- *¿Por qué se aplicó manual?* Porque no existía una regla en Terraform que gestionara esa lista de permitidos.
- *¿Por qué no se probó antes?* Porque no existe un entorno de preproducción con pruebas sintéticas de pasarela conectadas.

### 3. Plan de Acciones Correctivas (*Action Items*) con Dueño y Fecha
- **Acción 1 (Prevención):** Codificar el 100% de las reglas de seguridad perimetral en Terraform con validaciones automáticas. (Responsable: DevOps Lead / Plazo: 7 días).
- **Acción 2 (Detección):** Crear una sonda sintética que simule un pago real de 1 céntimo cada 60 segundos y alerte si falla en menos de 2 minutos. (Responsable: QA Lead / Plazo: 4 días).
- **Acción 3 (Mitigación):** Redundancia con pasarela secundaria: si la pasarela primaria falla 3 veces seguidas, el backend conmuta automáticamente el cobro a un proveedor alternativo."""
    },
    {
        "user": "Somos una empresa SaaS B2B de 35 empleados que gestiona datos de clientes europeos. Varios clientes enterprise nos exigen obtener la certificación ISO/IEC 27001 para firmar contratos. Tenemos 9 meses de plazo. ¿Cómo diseñar la hoja de ruta paso a paso para superar la auditoría a la primera?",
        "think": "Contexto: Empresa SaaS de 35 empleados preparando certificación ISO 27001 en 9 meses.\nEvaluación: ISO 27001 no es solo técnica sino de procesos y gestión de riesgos documentados (SGSI).\nConclusión: Plan en 5 etapas: alcance y gap analysis, análisis de riesgos, implantación de controles, auditoría interna y auditoría formal.",
        "assistant": """La certificación ISO/IEC 27001 no es un examen técnico puntual, sino la demostración de que posees un **Sistema de Gestión de Seguridad de la Información (SGSI)** vivo, documentado y controlado. Sigue esta hoja de ruta en 5 fases para 9 meses:

### Meses 1 y 2: Definición de Alcance y Análisis de Brechas (*Gap Analysis*)
1. **Definir el Alcance del SGSI:** Acota el perímetro de certificación exclusivamente a la plataforma SaaS y su infraestructura de soporte (no certifiques procesos corporativos no vinculados).
2. **Análisis de Brechas:** Compara tu estado actual contra los 93 controles del Anexo A de la norma ISO 27001:2022 para identificar qué políticas y configuraciones te faltan.
3. **Compromiso de Dirección:** Aprobación de la Política General de Seguridad de la Información firmada por el CEO.

### Meses 3 y 4: Evaluación y Tratamiento de Riesgos
1. **Inventario de Activos de Información:** Identifica bases de datos, código fuente, servidores cloud, credenciales y dispositivos de empleados.
2. **Matriz de Riesgos:** Evalúa probabilidad e impacto para amenazas (fugas de datos, secuestro ransomware, phishing a empleados, caídas de AWS).
3. **Declaración de Aplicabilidad (SoA - *Statement of Applicability*):** Documenta formalmente cuáles de los 93 controles aplican a tu empresa y justifica la exclusión de los que no procedan.

### Meses 5 y 6: Implantación Práctica de Controles y Evidencias
- **Técnicos:** Autenticación MFA obligatoria en todas las cuentas corporativas, cifrado en reposo y en tránsito, gestión de parches en menos de 14 días y backups inmutables probados.
- **Organizativos:** Formación obligatoria en ciberseguridad para todos los empleados, acuerdos de confidencialidad (NDA), proceso formal de onboarding/offboarding y gestión documentada de accesos con principio de mínimo privilegio.

### Mes 7: Auditoría Interna Obligatoria
- Contrata a un auditor externo independiente o consultora especializada para que ejecute una **auditoría interna simulada**. Emitirá un informe con no conformidades menores que deberéis subsanar antes del examen real.

### Meses 8 y 9: Auditoría de Certificación (Fase 1 y Fase 2)
- **Fase 1 (Revisión Documental):** La entidad certificadora oficial (AENOR, BSI, SGS, TÜV) revisa tus políticas, el SoA y el análisis de riesgos.
- **Fase 2 (Auditoría In Situ / Evidencias):** El auditor entrevista a desarrolladores y directivos y comprueba evidencias reales en la consola de AWS y GitHub. Superada la Fase 2, se emite el certificado oficial con validez por 3 años."""
    },
    {
        "user": "Durante la actualización mayor de versión de nuestro clúster de Kubernetes en producción (de 1.27 a 1.28), dos nodos han entrado en estado NotReady y el ingress-controller se ha roto, dejando la web inaccesible. Necesito un procedimiento de rollback escalonado de emergencia para restaurar el servicio de inmediato sin perder datos.",
        "think": "Contexto: Fallo crítico en actualización de versión de Kubernetes dejando el ingress caído y nodos en NotReady.\nEvaluación: Un rollback de control-plane no siempre es soportado en caliente; restaurar el tráfico exige priorizar la capa de red y cargas de trabajo.\nConclusión: Plan de contingencia: restaurar ingress controller anterior, aislar nodos corruptos y recuperar estado etcd previo.",
        "assistant": """En una emergencia durante un upgrade de Kubernetes, la prioridad absoluta es **restaurar el enrutamiento de red de los usuarios antes de intentar reparar los nodos rotos**. Ejecuta este procedimiento de contingencia en 4 pasos:

### 1. Desviar el Tráfico al Nivel Superior (DNS / Balanceador de Carga)
- Si dispones de un entorno secundario o réplica previa, cambia el registro de DNS o el balanceador externo para desviar a los usuarios fuera del clúster afectado mientras estabilizas.

### 2. Restauración Rápida del Ingress Controller
El fallo del ingress suele deberse a la deprecación de APIs en la versión 1.28 o a la incompatibilidad del webhook de admisión:
1. **Desactivar temporalmente el Webhook de Validación del Ingress:**
   Si el webhook de admisión está bloqueando la creación de pods:
   ```bash
   kubectl delete validatingwebhookconfiguration ingress-nginx-admission
   ```
2. **Hacer Rollback del Deployment del Ingress:**
   ```bash
   kubectl rollout undo deployment/ingress-nginx-controller -n ingress-nginx
   ```
   Comprueba de inmediato con `kubectl get pods -n ingress-nginx` que los controladores vuelvan a estar en estado `Running`.

### 3. Aislar los Nodos en Estado NotReady (*Cordon & Drain*)
Evita que el planificador siga enviando tráfico o pods a las máquinas con versiones inconsistentes:
```bash
# Marcar nodos corruptos como no programables:
kubectl cordon <nodo-defectuoso-1> <nodo-defectuoso-2>

# Drenar los pods de forma segura hacia los nodos sanos:
kubectl drain <nodo-defectuoso-1> --ignore-daemonsets --delete-emptydir-data --force
```

### 4. Recuperación del Control Plane (Si el Clúster Está Roto a Nivel Global)
- En clústeres administrados como AWS EKS o GKE, el control plane no admite downgrade directo de versión. Si el clúster es irrecuperable:
  1. Aprovisiona un clúster limpio en la versión 1.27 estable mediante tu script de Terraform/IaC en una subred paralela.
  2. Restaura los despliegues y secretos aplicando tus manifiestos de GitOps (ArgoCD/Flux).
  3. Restaura el volumen persistente de base de datos a partir del último Snapshot de EBS previo al inicio de la ventana de actualización."""
    },
    {
        "user": "Nuestra empresa manufacturera sufrió un ataque simulado de ciberseguridad y descubrimos que nuestras copias de seguridad en NAS locales son vulnerables a ser cifradas o borradas por un malware tipo ransomware con privilegios de administrador. ¿Cómo diseñar una arquitectura de backups inmutables (WORM) siguiendo las mejores prácticas?",
        "think": "Contexto: Copias de seguridad vulnerables a ser borradas por ransomware con credenciales de dominio.\nEvaluación: Si el atacante compromete Active Directory, destruye los NAS en red; se requiere inmutabilidad criptográfica fuera de banda.\nConclusión: Implantar regla 3-2-1-1-0 con almacenamiento Object Lock en modo Compliance y air-gap lógico.",
        "assistant": """El ransomware moderno no solo cifra archivos; busca activamente el software de copias de seguridad (Veeam, Commvault) y utiliza credenciales de administrador comprometidas para vaciar los repositorios antes de atacar. Para blindarte, debes implantar una **arquitectura de almacenamiento inmutable WORM (Write Once, Read Many)**:

### 1. La Nueva Regla de Respaldo: 3-2-1-1-0
- **3** copias de tus datos críticos.
- **2** soportes tecnológicos distintos (ej. disco rápido local + almacenamiento en la nube).
- **1** copia fuera de la empresa (*off-site*).
- **1 copia INMUTABLE (Protegida criptográficamente contra borrado).**
- **0** errores verificados mediante restauraciones automatizadas periódicas.

### 2. Implementación de Inmutabilidad con Object Lock
1. **Almacenamiento en la Nube con S3 Object Lock en Modo Compliance:**
   - Configura un bucket en AWS S3 o Wasabi con **S3 Object Lock activado en modo `COMPLIANCE` (Cumplimiento Estricto) con retención de 30 días**.
   - En modo Compliance, **ni siquiera el usuario `root` de AWS con todas las contraseñas puede borrar o sobreescribir un archivo antes de que expiren los 30 días**. Ni un atacante, ni un empleado descontento ni el soporte técnico del proveedor pueden alterar las copias.
2. **Repositorio Local Inmutable con Linux Hardened Repository:**
   - Despliega un servidor físico con Ubuntu/RHEL dedicado exclusivamente a Veeam con el demonio de inmutabilidad activado sobre el sistema de archivos XFS.
   - Deshabilita el acceso SSH tras la configuración y **no unas ese servidor al dominio de Active Directory de la empresa**. Si el dominio corporativo cae comprometido, el servidor de backup no comparte credenciales.

### 3. Cuentas de Almacenamiento Fuera de Banda (*Out-of-Band*)
- La cuenta de la nube donde residen los backups debe pertenecer a una suscripción cloud completamente separada de la red productiva, con un factor de doble autenticación (MFA por token físico FIDO2) en manos exclusivas de la dirección general."""
    },
    {
        "user": "Nuestra empresa de 120 empleados gestiona sus accesos con un Active Directory local (On-Premise) antiguo sin segundo factor de autenticación. Queremos migrar toda la gestión de identidades a Okta o Azure AD (Microsoft Entra ID) con SSO y MFA obligatorio para Google Workspace, Slack y Salesforce. ¿Cuál es el plan de despliegue por fases?",
        "think": "Contexto: Migración de Active Directory local a proveedor de identidad cloud con SSO y MFA en 120 usuarios.\nEvaluación: Cortar accesos en un solo día genera caos de logins y bloqueo de productividad; requiere enfoque híbrido provisional.\nConclusión: Despliegue en 4 fases: sincronización de directorio, habilitación gradual de MFA, configuración de SSO por app y corte de contraseñas locales.",
        "assistant": """Una migración de identidades mal coordinada puede bloquear el acceso a los correos y CRM de toda la empresa a las 09:00 de un lunes. Sigue este plan de despliegue seguro en 4 etapas:

### Fase 1: Sincronización de Directorio Híbrido (Semanas 1 a 3)
1. Instala el agente de sincronización (**Okta AD Agent** o **Microsoft Entra Connect**) en un servidor miembro de tu dominio local.
2. Configura la importación unidireccional de usuarios y grupos de unidades organizativas (OU) clave hacia la nube.
3. Estandariza el formato del nombre principal de usuario (*UPN*) para que coincida exactamente con la dirección de correo corporativa de cada empleado (ej. `nombre.apellido@empresa.com`).

### Fase 2: Campaña Gradual de Registro de MFA (Semanas 4 y 5)
1. **Nunca obligues a usar MFA sin periodo de registro previo.**
2. Envía una comunicación oficial con una guía paso a paso y habilita un plazo de 10 días laborables para que los empleados configuren la app autenticadora (**Okta Verify** o **Microsoft Authenticator**) mediante notificaciones push.
3. Monitorea el panel de adopción hasta que el **95% de la plantilla haya registrado su segundo factor**. El día 11, activa la regla de política de acceso condicional: denegar el login si no se utiliza MFA.

### Fase 3: Integración de Aplicaciones en Modo Dual (Semanas 6 y 7)
Conecta las aplicaciones empresariales una por una mediante el protocolo **SAML 2.0 / OIDC**:
- *App 1:* Google Workspace.
- *App 2:* Slack.
- *App 3:* Salesforce.
- Configura inicialmente el acceso en **modo dual**: los usuarios pueden entrar con SSO desde el portal de Okta o con su contraseña anterior mientras se acostumbran.

### Fase 4: Aplicación Estricta de SSO y Desconexión (Semana 8)
1. En los paneles de administración de Google, Slack y Salesforce, activa la casilla **"Requerir SSO de forma obligatoria"** para deshabilitar las contraseñas locales de las aplicaciones.
2. Los empleados ahora inician sesión en un único portal centralizado con MFA y acceden a todas sus herramientas con un solo clic."""
    },
    {
        "user": "Vamos a sustituir el proveedor de procesamiento de pagos con tarjeta de crédito de nuestra tienda online por una nueva pasarela que ofrece un 0,4% menos de comisión por transacción. Manejamos 8.000 transacciones diarias. ¿Cómo planificar el despliegue progresivo para verificar que no hay pérdida de conversiones ni fallos técnicos?",
        "think": "Contexto: Sustitución de pasarela de pago para 8.000 transacciones diarias con riesgo de caídas de conversión.\nEvaluación: Cambiar el 100% de golpe arriesga millones en facturación ante bugs de integración; se requiere canary deployment con split de tráfico.\nConclusión: Rollout progresivo (1% -> 10% -> 50% -> 100%) monitorizando tasa de autorización y cobros duplicados.",
        "assistant": """Cambiar una pasarela de pago que procesa 8.000 transacciones al día de golpe es un riesgo empresarial inadmisible. Aplica este **plan de despliegue canary con enrutamiento dinámico en 4 fases**:

### 1. Preparación Arquitectónica: Abstracción de Pasarela
- Tu código backend debe interactuar con una interfaz abstracta común (`IPaymentGateway`), implementando dos adaptadores intercambiables: `PasarelaAntiguaAdapter` y `PasarelaNuevaAdapter`.
- Utiliza una herramienta de indicadores de funcionalidad (*Feature Flags*, como LaunchDarkly o Unleash) para dirigir el tráfico porcentualmente sin desplegar código nuevo.

### 2. Cronograma de Rollout Progresivo

| Fase | Tráfico Asignado | Duración | Criterio de Pase a Siguiente Fase |
| :--- | :--- | :--- | :--- |
| **Fase 0 (Interna)** | Solo compras de empleados y QA | 48 horas | 100% de liquidación contable correcta |
| **Fase 1 (Canary 1%)** | ~80 pedidos/día de usuarios reales | 24 horas | Tasa de error < 0,1%; webhooks recibidos sin lag |
| **Fase 2 (Rampa 10%)** | ~800 pedidos/día | 48 horas | Tasa de autorización bancaria equivalente a la pasarela antigua |
| **Fase 3 (Split 50/50)** | 4.000 pedidos/día | 3 días | Revisión de devoluciones, antifraude y tiempos de respuesta |
| **Fase 4 (100% Final)** | Tráfico total | Permanente | Apagado de la pasarela antigua tras 30 días |

### 3. Las Tres Métricas Críticas de Aborto Inmediato (Circuit Breaker)
Configura una alerta automatizada que haga **rollback automático instantáneo a la pasarela antigua** si se detecta cualquiera de estas condiciones:
1. **Caída de la Tasa de Aprobación (*Authorization Rate*):** Si la tasa de éxito de tarjetas válidas cae más de un 1,5% respecto al histórico habitual.
2. **Latencia del Checkout:** Si el tiempo de respuesta del webhook bancario supera los 3,5 segundos.
3. **Pico de Reclamaciones:** Si se detecta cualquier cobro duplicado en cuenta de clientes."""
    },
    {
        "user": "Nuestra plataforma de e-commerce prevé multiplicar su tráfico habitual por 8 durante la semana del Black Friday (esperamos 150 compras por minuto en horas pico). Tenemos 6 semanas para preparar y estresar el sistema. ¿Cómo diseñar un plan de pruebas de carga y optimización integral paso a paso?",
        "think": "Contexto: Preparación técnica y pruebas de estrés para pico de x8 de tráfico en Black Friday en 6 semanas.\nEvaluación: Estresar solo la home no sirve; los cuellos de botella reales ocurren en el stock de base de datos y pasarela de pago.\nConclusión: Plan de 6 semanas: benchmarking de cuellos de botella con k6, optimización de caché perimetral, simulacro de estrés y congelación de código.",
        "assistant": """El 90% de las plataformas de e-commerce que colapsan en Black Friday no caen por la cantidad de visitas en portada, sino por **contención de escrituras en la base de datos durante el decremento de stock y bloqueos en pasarela**. Sigue este plan de preparación en 6 semanas:

### Semanas 1 y 2: Modelado de Escenarios Realistas y Benchmarking
1. **No pruebes solo tráfico estático:** Diseña scripts de pruebas de carga con herramientas modernas como **k6** o **Locust** que simulen el comportamiento real del comprador:
   - 70% navegando catálogo y fichas de producto (lectura intensiva).
   - 20% añadiendo al carrito y aplicando cupones.
   - 10% completando el checkout de pago (escritura en base de datos).
2. **Prueba de Carga Inicial en Entorno Espejo:** Identifica a partir de qué volumen exacto de peticiones concurrentes empiezan a degradarse los tiempos de respuesta (*Breaking Point*).

### Semanas 3 y 4: Eliminación de Cuellos de Botella Críticos
1. **Blindaje de la Capa de Caché Perimetral (CDN):**
   - Configura Cloudflare o Fastly para cachear las páginas de producto, imágenes y respuestas JSON del catálogo con `stale-while-revalidate`. El 85% del tráfico no debe tocar vuestros servidores.
2. **Optimización de Base de Datos para el Checkout:**
   - Desacopla tareas no esenciales fuera de la transacción de compra: el envío del correo de confirmación de pedido y la sincronización con el ERP deben enviarse a una cola asíncrona (RabbitMQ/SQS), no ejecutarse durante el pago.
   - Aumenta el pool de conexiones de base de datos (`pgBouncer` o `ProxySQL`).

### Semana 5: El Simulacro de Choque (*Stress & Chaos Test*)
- Ejecuta una prueba de estrés al **150% del tráfico pico previsto** (225 compras/minuto) durante 45 minutos seguidos.
- Simula caídas de un nodo de base de datos o retrasos en la pasarela para verificar que la aplicación degrada suavemente en lugar de colapsar por completo.

### Semana 6: Congelación Estricta de Código (*Code Freeze*)
- A 7 días de la campaña, **queda terminantemente prohibido desplegar nuevas funcionalidades de producto o refactors**. Solo se permiten parches críticos de seguridad aprobados por el director técnico."""
    },
    {
        "user": "Nuestra empresa tecnológica en remoto contrata a 4 ingenieros de software senior el próximo mes. Queremos diseñar un plan de onboarding estructurado de 30-60-90 días que les permita ser productivos, autónomos e integrarse en el equipo sin frustración. ¿Cómo desglosar los objetivos y entregables por fases?",
        "think": "Contexto: Plan de onboarding en remoto de 30-60-90 días para desarrolladores senior.\nEvaluación: Dejar al senior sin guía genera desconexión; un plan estructurado por hitos medibles fomenta la autonomía progresiva.\nConclusión: Estructurar en 3 fases: comprender y primer deploy (día 30), autonomía y liderazgo de features (día 60), e impacto arquitectónico y mentoría (día 90).",
        "assistant": """Para un desarrollador senior en un equipo remoto, un onboarding exitoso no consiste en vigilarlo, sino en **despejar el camino administrativo y técnico para que su experiencia aporte valor desde el primer sprint**. Estructura el plan en tres etapas:

### Primeros 30 Días: Absorción de Contexto y Primer Despliegue (*First Value*)
- **Objetivo Principal:** Conocer la arquitectura, los procesos de despliegue y la cultura del equipo.
- **Entregables Clave:**
  - *Día 1:* Accesos listos en el gestor de contraseñas, repositorio clonado y entorno de desarrollo local funcionando gracias a scripts automatizados (`docker compose up`).
  - *Asignación de un Onboarding Buddy:* Un compañero senior asignado para resolver dudas rápidas en Slack sin sensación de molestar.
  - *Semana 1:* **Lanzar su primer commit a producción**: un cambio menor (un bugfix pequeño o un test unitario) para validar de punta a punta el pipeline de CI/CD.
  - *Día 30:* Haber completado 2 tareas estándar de sprint y documentado mejoras en la guía de instalación del proyecto.

### Días 31 a 60: Autonomía y Liderazgo de Funcionalidades (*Contribution*)
- **Objetivo Principal:** Diseñar y liderar el desarrollo de una funcionalidad mediana de principio a fin.
- **Entregables Clave:**
  - Redactar su primer Documento de Diseño Técnico (RFC) proponiendo la arquitectura para un nuevo endpoint o módulo.
  - Participar activamente en las revisiones de código (*Code Reviews*) de sus compañeros aportando criterio senior.
  - Resolver incidencias de soporte de segundo nivel de forma autónoma.

### Días 61 a 90: Impacto Estratégico y Propuestas de Mejora (*Impact*)
- **Objetivo Principal:** Detectar deuda técnica estructural y proponer mejoras que beneficien a todo el departamento.
- **Entregables Clave:**
  - Presentar una sesión técnica interna (*Tech Talk*) sobre una buena práctica o patrón de diseño.
  - Liderar la integración con un servicio externo o una refactorización de rendimiento.
  - Reunión de cierre de 90 días con el Engineering Manager para consensuar sus objetivos de carrera anuales."""
    },
    {
        "user": "Tenemos una plataforma web monolítica antigua que procesó compras durante 6 años. La nueva plataforma ya está operativa al 100%, pero por normativa legal y fiscal debemos conservar el histórico de facturación, contratos y pedidos durante 6 años sin mantener los servidores antiguos encendidos (que cuestan 950 €/mes en licencias y hosting). ¿Cuál es el plan para apagar y desmantelar el sistema garantizando cumplimiento legal?",
        "think": "Contexto: Desmantelamiento seguro de software legado ahorrando 950 €/mes y cumpliendo normativa fiscal de 6 años.\nEvaluación: Apagar sin exportación estructurada arriesga sanciones de Hacienda; mantener el servidor encendido desperdicia 11.000 €/año.\nConclusión: Plan en 4 etapas: exportación inmutable a almacenamiento frío, verificación de auditoría, apagado de instancias y custodia de claves.",
        "assistant": """Mantener servidores legados encendidos solo para consultar facturas antiguas es un desperdicio financiero (más de 11.000 €/año) y una brecha de seguridad grave (sistemas no parcheados). Sigue este **plan de desmantelamiento y archivado seguro**:

### 1. Extracción Estructurada de Datos y Evidencias Fiscales
1. **Volcado Completo de la Base de Datos:**
   - Genera un volcado completo de la base de datos en formato SQL estándar y en formato binario nativo:
     ```bash
     pg_dump -Fc base_legada > base_legada_archivo_$(date +%F).dump
     ```
2. **Exportación a Formatos Planos Universales e Inmutables:**
   - Las autoridades tributarias y los auditores exigen formatos accesibles sin software propietario: exporta las tablas de facturación, clientes y pagos a archivos **CSV estándar y JSON Lines** comprimidos.
3. **Generación de PDFs de Facturas con Hash Criptográfico:**
   - Asegúrate de que todas las facturas históricas estén generadas en formato **PDF/A (estándar de preservación a largo plazo)** y calcula un archivo de manifiesto con los hashes SHA-256 de cada archivo para garantizar su inalterabilidad jurídica ante un peritaje judicial.

### 2. Custodia en Almacenamiento Frío Ultra-Barato (AWS S3 Glacier)
- Sube el paquete completo de datos cifrado con AES-256 a un bucket en **AWS S3 Glacier Flexible Retrieval** o **Deep Archive**.
- Para un archivo de 200 GB, el coste de custodia pasa de **950 € al mes a menos de 0,30 € al mes (ahorras más de 11.300 € limpios al año)**.
- Activa una directiva de retención automática que elimine los datos transcurridos exactamente 6 años y 1 día.

### 3. Protocolo de Apagado Físico y Desmantelamiento
1. **Revocación de Credenciales:** Elimina accesos de API, certificados SSL y apaga las interfaces de red de los servidores.
2. **Copia de Imagen de Disco (AMI / Snapshot):** Crea un snapshot completo del disco del sistema operativo antes de borrar la máquina.
3. **Destrucción de la Instancia:** Elimina los servidores virtuales y da de baja las licencias de software propietario asociadas."""
    },
    {
        "user": "Queremos implementar Despliegue Continuo (CD) totalmente automatizado para que cada commit mergeado a `main` se despliegue a producción sin intervención humana. El equipo teme introducir bugs graves a los usuarios. ¿Cómo diseñar una canalización de despliegue Canary con métricas de salud y rollback automatizado?",
        "think": "Contexto: Implementación de Continuous Deployment seguro con despliegues Canary automatizados.\nEvaluación: Desplegar el 100% de golpe sin validación manual genera riesgo de caídas; un despliegue Canary con análisis de métricas mitiga el riesgo.\nConclusión: Canalización en 4 pasos: pipeline de validación previa, canary progresivo (Argo Rollouts), monitorización de errores HTTP y rollback automático por webhook.",
        "assistant": """El Despliegue Continuo (CD) seguro no se logra añadiendo aprobaciones manuales de jefes de equipo, sino **construyendo barreras automatizadas de verificación de métricas en tiempo real**. Implementa esta canalización Canary con herramientas como **Argo Rollouts** o **Flagger**:

### 1. El Filtro Previo de Integración Continua (CI)
Antes de tocar producción, el pipeline de CI debe ejecutar de forma obligatoria y estricta:
- 100% de tests unitarios y de integración pasando en verde.
- Análisis estático de seguridad (SAST) y escaneo de vulnerabilidades en la imagen Docker con Trivy.
- Despliegue efímero en un entorno de pruebas (*Preview Environment*) con ejecución de tests sintéticos E2E.

### 2. La Mecánica del Despliegue Canary Progresivo
Cuando el nuevo contenedor se aprueba, se despliega junto a la versión antigua dividiendo el tráfico en la capa de red:

```yaml
# ESTRATEGIA DE CANARY CON ARGO ROLLOUTS:
strategy:
  canary:
    steps:
      - setWeight: 5    # 1. Enviar el 5% del tráfico a la nueva versión
      - pause: {duration: 10m} # Esperar 10 minutos analizando métricas
      - setWeight: 25   # 2. Subir al 25% del tráfico si las métricas son óptimas
      - pause: {duration: 20m}
      - setWeight: 50   # 3. Subir al 50%
      - pause: {duration: 15m}
      # 4. Promoción automática al 100% y retirada de la versión antigua
```

### 3. Las Métricas de Análisis Automático (*Rollback Triggers*)
Durante cada pausa, el controlador de Canary consulta a tu servidor de métricas (Prometheus o Datadog). Si se detecta cualquiera de estas condiciones en la versión nueva:
1. **Ratio de errores HTTP 5xx superior al 0,5%**.
2. **Latencia percentil 95 (p95) superior a 350 milisegundos**.
El sistema **cancela el despliegue de forma instantánea en menos de 10 segundos**, redirigiendo el 100% del tráfico a la versión antigua sin que ningún ingeniero tenga que despertar por la noche."""
    },
    {
        "user": "Tengo 3 deudas acumuladas por un total de 18.500 €: \n1) Tarjeta de crédito revolving: 3.500 € al 21% TAE (cuota mínima de 120 €/mes).\n2) Préstamo personal para coche: 11.000 € al 7,5% TAE (cuota de 260 €/mes).\n3) Deuda con familiar: 4.000 € al 0% de interés (acordado devolver 150 €/mes).\nDispongo de un margen total de 750 € al mes para pagar deudas. ¿Qué plan sistemático debo seguir combinando el método avalancha y bola de nieve para liquidar todo lo antes posible?",
        "think": "Contexto: Liquidación de 18.500 € de deudas con 750 € de presupuesto mensual libre.\nEvaluación: Pagar todas por igual prolonga el interés abusivo del 21%; el método avalancha ahorra dinero y la bola de nieve da motivación.\nConclusión: Plan híbrido: pagar mínimos de las deudas baratas y concentrar el excedente de 220 € en la tarjeta al 21%.",
        "assistant": """Para liquidar 18.500 € con un presupuesto mensual de 750 €, la estrategia óptima es aplicar el **Método Avalancha Estricto**: la tarjeta al 21% TAE es una fuga masiva de dinero que devora casi 60 € en intereses todos los meses si no se ataca con agresividad:

### 1. El Desglose Mensual Inicial
Tus compromisos mínimos actuales suman **530 € al mes**:
- Préstamo coche: 260 €
- Tarjeta revolving: 120 € (mínimo)
- Familiar: 150 €
- **Presupuesto disponible: 750 €/mes -> Excedente de ataque directo: 220 € libres al mes.**

### 2. Plan de Ataque en 3 Fases Consecutivas

#### Fase 1: Aniquilación de la Tarjeta al 21% (Meses 1 a 11)
- Paga los 260 € del coche y los 150 € del familiar.
- **Concentra todo el excedente en la tarjeta:** 120 € (mínimo) + 220 € (excedente) = **340 € mensuales directos a la tarjeta**.
- En **11 meses**, la deuda más tóxica queda **100% liquidada**. Habrás eliminado el 21% de interés de tu vida y liberado 340 € adicionales en tu flujo de caja.

#### Fase 2: Amortización Acelerada del Coche al 7,5% (Meses 12 a 24)
- Ahora tu capacidad de pago para el coche pasa de 260 € a **600 € mensuales** (los 260 € anteriores + los 340 € que antes se comía la tarjeta).
- El saldo del préstamo del coche (que rondará los 8.500 € tras un año de cuotas normales) se extingue en apenas **14 meses adicionales**.

#### Fase 3: Cancelación del Préstamo Familiar (Meses 25 a 27)
- Te quedan unos 2.000 € de deuda familiar. Ahora dispones de **750 € limpios al mes**: saldas la deuda con tu pariente en solo **3 meses**, recuperando la paz mental absoluta.
- **Resultado final:** En **27 meses (poco más de 2 años)** habrás eliminado 18.500 € de deuda y dispondrás de 750 € al mes para empezar a invertir."""
    },
    {
        "user": "Tenemos una flota de 25 servidores virtuales con Ubuntu Server 22.04 LTS en producción. Necesitamos diseñar e implementar un plan de endurecimiento de seguridad (Hardening) siguiendo las recomendaciones del estándar CIS Benchmark. ¿Cuáles son las 6 medidas críticas prioritarias a implantar?",
        "think": "Contexto: Hardening de 25 servidores Linux de producción siguiendo el estándar CIS Benchmark.\nEvaluación: El acceso por contraseña, puertos innecesarios y permisos débiles son los vectores de intrusión primarios.\nConclusión: Protocolo en 6 medidas: llaves SSH sin root, firewall UFW estricto, fail2ban, permisos de kernel en sysctl, actualizaciones desatendidas y auditoría auditd.",
        "assistant": """El estándar CIS Benchmark (Center for Internet Security) es el referente global para securizar sistemas operativos. Para 25 servidores en producción, aplica este plan de endurecimiento en 6 medidas prioritarias automatizables mediante Ansible:

### 1. Blindaje del Acceso SSH
Edita `/etc/ssh/sshd_config` y refuerza las directivas:
- `PermitRootLogin no` (prohíbe el login directo como superusuario; obliga a usar un usuario con `sudo`).
- `PasswordAuthentication no` (elimina el acceso por contraseña; solo se permite acceso por clave pública criptográfica ED25519 o RSA de 4096 bits).
- `MaxAuthTries 3` y `ClientAliveInterval 300`.

### 2. Cortafuegos Perimetral Estricto (Principio de Denegación por Defecto)
Configura UFW o iptables para denegar todo el tráfico entrante salvo lo estrictamente necesario:
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # O tu puerto SSH custom
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### 3. Protección contra Ataques de Fuerza Bruta (Fail2ban)
Instala y activa `fail2ban`. Tras 3 intentos fallidos de autenticación SSH, bloquea la IP del atacante mediante reglas en iptables durante 24 horas.

### 4. Endurecimiento de Parámetros de Red del Núcleo (`sysctl`)
En `/etc/sysctl.d/99-security.conf` activa la protección contra ataques de spoofing y paquetes maliciosos:
```ini
# Ignorar peticiones ICMP broadcast:
net.ipv4.icmp_echo_ignore_broadcasts = 1
# Bloquear enrutamiento de origen:
net.ipv4.conf.all.accept_source_route = 0
# Mitigar ataques SYN Flood:
net.ipv4.tcp_syncookies = 1
# Desactivar reenvío de paquetes si no es un router:
net.ipv4.ip_forward = 0
```
Aplica con `sudo sysctl --system`.

### 5. Actualizaciones Automáticas de Seguridad
Habilita el paquete `unattended-upgrades` para que el sistema operativo instale automáticamente parches de seguridad críticos del kernel y librerías todos los días sin intervención manual.

### 6. Auditoría Continua con `auditd`
Activa el demonio de auditoría del kernel (`auditd`) para registrar cualquier modificación en archivos críticos del sistema como `/etc/passwd`, `/etc/shadow` o llamadas al sistema de elevación de privilegios `execve`."""
    }
]
