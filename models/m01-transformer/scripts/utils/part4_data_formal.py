# -*- coding: utf-8 -*-
"""Dataset de redacción formal, dictámenes técnicos y comunicación institucional (sin fluff)."""

FORMAL_SAMPLES = [
    {
        "user": "Reescribe el siguiente correo electrónico informal a un registro formal y ejecutivo adecuado para la dirección general:\n«Hola gente, les aviso que el servidor de pagos se cayó de nuevo hoy a la mañana porque la base de datos no aguantó el tráfico del hot sale. Ya lo levantamos atándolo con alambre, pero si no compramos más máquinas o no cambiamos el código viejo, esto va a volver a reventar el fin de semana y vamos a perder un montón de plata. Avísenme qué hacemos».",
        "assistant": r"""**Asunto**: Reporte de incidencia crítica en pasarela de pagos y propuesta de remediación estructural

**Para**: Dirección General de Operaciones y Tecnología  
**De**: Responsable de Infraestructura y Servicios Críticos  
**Fecha**: 15 de noviembre de 2026  

Estimada Dirección:

Por medio de la presente, cumplo con elevar el informe de la incidencia técnica registrada el día de la fecha durante el horario pico del evento comercial:

1. **Diagnóstico de la Incidencia**: A las 09:15 h, la plataforma de procesamiento de pagos experimentó una interrupción de servicio de 28 minutos provocada por la saturación de conexiones concurrentes en el clúster principal de base de datos, al superarse el umbral de capacidad proyectado.
2. **Mitigación Inmediata**: El equipo de guardia ejecutó el reinicio controlado de instancias y habilitó un aprovisionamiento temporal de memoria caché, restableciéndose la operatividad total a las 09:43 h.
3. **Riesgo Operativo Remanente**: La arquitectura actual presenta una limitación estructural de escalabilidad vertical ante picos de demanda sostenida. De no adoptarse medidas de fondo, existe una probabilidad alta de recurrencia durante las próximas 72 horas.
4. **Plan de Acción Recomendado**:
   - Escalado horizontal inmediato de dos nodos adicionales de lectura en la base de datos (plazo estimado: 4 horas).
   - Optimización de las consultas transaccionales de mayor latencia identificadas en el log de auditoría.

Quedo a su disposición para coordinar la ejecución del plan de contingencia."""
    },
    {
        "user": "Redacta el modelo formal de un acta de reunión extraordinaria de Directorio que aprueba la contratación de un crédito bancario para inversión de capital.",
        "assistant": r"""**ACTA DE REUNIÓN EXTRAORDINARIA DE DIRECTORIO Nº 14/2026**
**INVERSIONES GLOBALES S.A.**

En la ciudad de Madrid, a las diez horas del día 15 de noviembre de 2026, se reúnen en la sede social de la compañía los miembros del Directorio que suscriben al pie, bajo la presidencia de Dña. Elena Morales Ramos y con la asistencia del Secretario del Directorio D. Carlos Vega Fuentes.

Comprobada la existencia de quórum reglamentario con la totalidad de los directores presentes, la Sra. Presidenta declara válidamente abierta la sesión y expone el único punto del Orden del Día:

**ORDEN DEL DÍA**:
Aprobación y suscripción de contrato de financiamiento bancario a largo plazo para adquisición de maquinaria industrial y ampliación de planta operativa.

**DELIBERACIÓN Y ACUERDOS**:
Tras la presentación del informe técnico-financiero elaborado por la Dirección de Finanzas y el dictamen legal emitido por la Asesoría Jurídica externa, el Directorio, tras amplio debate y por **unanimidad de votos**, adopta las siguientes resoluciones:

1. **PRIMERO**: Aprobar en todos sus términos la contratación de una línea de crédito de inversión productiva con la entidad Banco Mercantil por un importe principal de hasta 2.500.000 € (dos millones quinientos mil euros), a un plazo de amortización de sesenta (60) meses y una tasa de interés nominal anual fija del 4,25%.
2. **SEGUNDO**: Facultar con plenos poderes al Director General, D. Roberto Méndez Silva, para que en nombre y representación de la sociedad suscriba los contratos públicos o privados, pólizas de crédito y garantías que resulten menester para el perfeccionamiento de dicha operación.
3. **TERCERO**: Facultar al Secretario del Directorio para protocolizar y elevar a público los acuerdos adoptados en la presente sesión.

No habiendo más asuntos que tratar, se levanta la sesión a las once horas y treinta minutos, previa redacción, lectura y firma de la presente acta en señal de conformidad de todos los asistentes."""
    },
    {
        "user": "Elabora una carta formal de renuncia irrevocable a un cargo gerencial cumpliendo los requisitos formales y preaviso legal.",
        "assistant": r"""**Lugar y Fecha**: Santiago de Chile, 15 de noviembre de 2026

**A la atención de**:  
D. Andrés Bustamante Correa  
Director de Recursos Humanos  
Consorcio Industrial del Sur S.A.  
Presente  

**REF**: Notificación formal de renuncia voluntaria e irrevocable

De mi consideración:

Por medio de la presente, comunico formalmente a usted y al Directorio de la empresa mi decisión voluntaria e irrevocable de renunciar al cargo de **Gerente de Operaciones y Logística** que he venido desempeñando en la compañía.

En estricto cumplimiento de lo estipulado en la legislación laboral vigente y en mi contrato de trabajo, pongo a su disposición el **preaviso legal de treinta (30) días corridos**, por lo que mi último día efectivo de labores en la institución será el próximo **15 de diciembre de 2026**.

Durante este período de transición, manifiesto mi total disposición para coordinar la entrega ordenada y documentada de mi cargo, el traspaso de responsabilidades pendientes y la inducción de la persona que sea designada para asumir mis funciones, a efectos de asegurar la continuidad ininterrumpida de las operaciones.

Agradezco sinceramente la confianza depositada en mi persona durante estos cinco años de trayectoria profesional, así como el respaldo institucional brindado por el equipo directivo.

Le solicito se sirva ordenar la liquidación de mis haberes y beneficios sociales conforme a derecho para la fecha de término indicada.

Atentamente,

________________________________________  
**Ignacio Larraín Valdés**  
RUT: 12.345.678-9  
Gerente de Operaciones y Logística"""
    },
    {
        "user": "Redacta un informe de causa raíz (RCA) tras la indisponibilidad de una pasarela API corporativa.",
        "assistant": r"""# INFORME DE ANÁLISIS DE CAUSA RAÍZ (RCA)
**Incidente ID**: INC-2026-8841  
**Servicio Afectado**: API Gateway Corporativo (api.empresa.internal)  
**Severidad**: P1 (Crítico)  
**Duración de la Interrupción**: 42 minutos (11:04 UTC – 11:46 UTC)  
**Líder Técnico de Incidentes**: Equipo de Ingeniería de Plataforma  

---

### 1. Resumen Ejecutivo
El 14 de noviembre de 2026 a las 11:04 UTC, el API Gateway central experimentó una degradación total de servicio que resultó en el rechazo del 100% de las solicitudes entrantes con código HTTP 502 (Bad Gateway). El servicio fue restaurado a las 11:46 UTC mediante el despliegue de una configuración de revocación y ajuste de parámetros de socket.

### 2. Cronología de los Eventos
- **10:55 UTC**: Se aplica en producción el cambio `CFG-4491` para reducir los tiempos de timeout en conexiones upstream de 60 s a 2 s.
- **11:04 UTC**: Se acumulan hilos bloqueados en el pool de conexiones worker; la cola de espera de sockets alcanza el límite de kernel (`somaxconn`). Comienzan los fallos HTTP 502.
- **11:12 UTC**: El sistema de telemetría dispara alerta P1 por tasa de error > 15%. Se convoca la sala de crisis técnica.
- **11:28 UTC**: Se aísla el commit de configuración `CFG-4491` como factor desencadenante.
- **11:35 UTC**: Se inicia la reversión progresiva (*canary rollback*) del parámetro.
- **11:46 UTC**: Se completa el reinicio escalonado de los contenedores proxy. Telemetría confirma latencias dentro de SLA (< 45 ms) y tasa de error 0.00%.

### 3. Análisis de Causa Raíz (Método de los 5 Porqués)
1. **¿Por qué falló el Gateway?** Los workers agotaron el pool de descriptores de archivo disponibles para conexiones de red.
2. **¿Por qué se agotaron los descriptores?** Cientos de solicitudes concurrentes quedaron en estado `TIME_WAIT` al cerrarse abruptamente por el timeout de 2 segundos.
3. **¿Por qué se fijó el timeout en 2 segundos?** Se buscaba liberar recursos ante servicios lentos sin evaluar la latencia de servicios batch subordinados.
4. **¿Por qué no se detectó el impacto en pruebas previas?** El entorno de preproducción no cuenta con carga sintética concurrente equivalente al tráfico real.
5. **Causa Raíz Fundamental**: Ausencia de una compuerta automatizada de pruebas de estrés y validación de impacto arquitectónico para cambios de configuración a nivel de red.

### 4. Acciones Correctivas y Preventivas
- **Inmediata (Completada)**: Reversión del parámetro a 30 segundos y desacople de microservicios batch.
- **Mediano Plazo (Plazo: 10 días)**: Implementar circuit breakers automáticos a nivel de gateway para aislar endpoints upstream degradados.
- **Estructural (Plazo: 30 días)**: Integrar pruebas automatizadas de inyección de carga previa al despliegue en entornos de staging."""
    },
    {
        "user": "Reescribe el siguiente texto administrativo a un dictamen formal de disconformidad técnica en un proceso de licitación pública:\n«Miramos la oferta de la empresa competidora y la verdad no entendemos cómo la aceptaron. Los servidores que ofrecen no tienen los discos duros que pedía el pliego y además la garantía que dan es de dos años en vez de tres. Si les dan la licitación a ellos es un error grave y vamos a protestar porque nos parece injusto».",
        "assistant": r"""**ESCRITO DE DISCONFORMIDAD Y OBSERVACIONES TÉCNICAS A LA OFERTA PRESENTADA EN LA LICITACIÓN PÚBLICA Nº 08/2026**

**Al Órgano de Contratación**:  
Comisión Evaluadora de Contrataciones  
Ministerio de Modernización y Servicios Públicos  

D. Fernando Morales Ortiz, en representación legal de **Sistemas Avanzados de Computación S.A.**, debidamente acreditado en el expediente de la Licitación Pública Nº 08/2026, comparece y respetuosamente expone:

Que habiendo tomado conocimiento del informe preliminar de evaluación de ofertas técnicas, formula formal **disconformidad técnica** respecto a la proposición presentada por la mercantil **Tecnologías Integradas S.L.**, con base en los siguientes fundamentos de derecho y de hecho:

1. **Incumplimiento de la cláusula técnica 4.2 (Almacenamiento masivo)**: El Pliego de Prescripciones Técnicas Particulares (PPTP) exige expresamente que las unidades servidoras suministradas dispongan de unidades de almacenamiento de estado sólido NVMe empresariales con tecnología de protección contra pérdida de energía (PLP). La oferta analizada consigna unidades SATA convencionales de gama comercial, lo que vulnera el principio de equivalencia técnica y compromete la integridad operativa de los datos.
2. **Incumplimiento del plazo mínimo de garantía (Cláusula 8.1)**: El pliego rector establece como requisito indispensable no subsanable una cobertura de garantía técnica y soporte in situ por un término mínimo de treinta y seis (36) meses. La oferta cuestionada limita su compromiso a veinticuatro (24) meses, configurándose un incumplimiento flagrante de una condición técnica esencial de la convocatoria.

**PETICIÓN**:  
En virtud de lo expuesto, solicita a esa Comisión Evaluadora que tenga por presentado este escrito, proceda a la revisión de los extremos señalados y, de conformidad con lo preceptuado en la normativa de contratación del sector público, **declare la exclusión técnica** de la oferta formulada por Tecnologías Integradas S.L. por inobservancia estricta de las prescripciones técnicas vinculantes."""
    },
    {
        "user": "Elabora una comunicación corporativa formal dirigida a usuarios para informar sobre una ventana de mantenimiento programado de infraestructura tecnológica.",
        "assistant": r"""**COMUNICADO INSTITUCIONAL: VENTANA DE MANTENIMIENTO PROGRAMADO**

**Destinatarios**: Clientes corporativos y usuarios de la plataforma digital  
**Emisor**: Dirección de Operaciones Tecnológicas  
**Fecha de emisión**: 15 de noviembre de 2026  
**Referencia**: Actualización de infraestructura central y optimización de seguridad  

Estimados usuarios:

Les informamos que, en el marco de nuestro plan continuo de modernización y fortalecimiento de la infraestructura tecnológica, se llevará a cabo una **ventana de mantenimiento programado** el próximo **domingo 22 de noviembre de 2026**, en el horario comprendido entre las **01:00 h y las 05:00 h (UTC-3)**.

### Alcance y afectación del servicio:
- Durante dicho intervalo de cuatro (4) horas, los servicios de banca en línea, transferencias interbancarias y acceso a la API corporativa permanecerán **temporalmente suspendidos**.
- Las operaciones con tarjetas de crédito y débito físicas en puntos de venta y cajeros automáticos funcionarán con normalidad bajo contingencia operativa.

### Objetivo de la intervención:
La ventana técnica permitirá la instalación de parches críticos de seguridad a nivel de firmware y la migración de enlaces de fibra óptica a una arquitectura redundante de alta disponibilidad.

Les recomendamos anticipar sus operaciones transaccionales para evitar inconvenientes. Nuestro equipo de soporte permanecerá activo a través de los canales de atención de guardia.

Agradecemos su comprensión y colaboración en este proceso indispensable para la robustez del servicio."""
    },
    {
        "user": "Redacta el modelo formal de una cláusula contractual de resolución por incumplimiento y penalidad por mora en un contrato de desarrollo de software.",
        "assistant": r"""**CLÁUSULA DÉCIMA: PENALIZACIONES POR MORA Y RESOLUCIÓN CONTRACTUAL POR INCUMPLIMIENTO**

**10.1. Penalización por mora en la entrega**:  
Si el PROVEEDOR no entregare los entregables correspondientes a cada hito en los plazos perentorios calendarizados en el Anexo I, el CLIENTE tendrá derecho a aplicar una penalidad dineraria por mora equivalente al **0,5% (cero coma cinco por ciento)** del valor total del hito devengado por cada día natural de retraso injustificado, hasta un límite máximo del **15% (quince por ciento)** del importe total del contrato. Dichas penalidades serán deducidas directamente de las facturas pendientes de abono al PROVEEDOR o ejecutadas contra la garantía de fiel cumplimiento.

**10.2. Resolución por incumplimiento grave**:  
Cualquiera de las PARTES podrá resolver el presente Contrato de pleno derecho, sin necesidad de declaración judicial previa, mediante notificación fehaciente remitida por burofax o conducto notarial con al menos quince (15) días naturales de antelación, en los siguientes supuestos:
a) Si el PROVEEDOR alcanzare el tope máximo del 15% fijado para las penalidades por mora sin haber completado satisfactoriamente las pruebas de aceptación técnica del hito.  
b) Por el incumplimiento culpable de cualquiera de las obligaciones esenciales estipuladas en el presente contrato, en particular las relativas a confidencialidad, protección de datos de carácter personal y titularidad de los derechos de propiedad intelectual.  
c) Por la declaración en concurso de acreedores, insolvencia legal o disolución de cualquiera de las partes.

**10.3. Efectos de la resolución**:  
En caso de resolución del contrato imputable al PROVEEDOR, este vendrá obligado a hacer entrega inmediata al CLIENTE de la totalidad del código fuente desarrollado hasta la fecha, documentación técnica de arquitectura y artefactos del repositorio, sin perjuicio de la indemnización por los daños y perjuicios directos que el incumplimiento hubiere ocasionado."""
    },
    {
        "user": "Redacta un dictamen formal de viabilidad técnica sobre la migración de un sistema monolítico legado a una arquitectura de microservicios orientada a eventos.",
        "assistant": r"""**DICTAMEN TÉCNICO DE VIABILIDAD ARQUITECTÓNICA**

**Para**: Comité de Dirección y Transformación Digital  
**De**: Departamento de Arquitectura de Sistemas y Gobierno de Datos  
**Asunto**: Evaluación de viabilidad de migración de Monolito Central a Microservicios Event-Driven  
**Dictamen Nº**: ARCH-2026-03  

---

### 1. Objeto del Dictamen
Emitir pronunciamiento técnico vinculante sobre la factibilidad, riesgos e impacto operativo del proyecto de descomposición del sistema de gestión central (desarrollado en arquitectura monolítica con base de datos compartida) hacia una topología de microservicios distribuidos orientada a eventos mediante un bus Apache Kafka.

### 2. Análisis de Viabilidad

1. **Viabilidad Técnica (Favorable Condicionada)**:
   - *Acoplamiento funcional*: El código actual presenta un alto grado de dependencia transversal a nivel de esquema de base de datos relacional. La descomposición directa («big bang») es inviable; debe implementarse el patrón de estrangulamiento (*Strangler Fig Pattern*) sobre un horizonte de 18 meses.
   - *Consistencia de datos*: Se concluye que las transacciones distribuidas ACID no deben mantenerse en la arquitectura de destino; el negocio debe validar formalmente la transición hacia modelos de consistencia eventual mediante el patrón Saga orquestado.

2. **Viabilidad Operativa y de Capital Humano (Crítica)**:
   - El equipo de ingeniería actual carece de experiencia operativa demostrable en despliegues con Kubernetes, observabilidad distribuida (OpenTelemetry) y depuración de eventos desordenados.
   - Es condición *sine qua non* la capacitación previa del 100% del personal asignado y la contratación de dos perfiles senior especializados en ingeniería de confiabilidad de sitios (SRE).

### 3. Conclusión y Dictamen
Se emite **DICTAMEN FAVORABLE CONDICIONADO**. Se autoriza el inicio de la Fase I (Prueba de Concepto sobre el módulo periférico de facturación electrónica), supeditando la migración del núcleo transaccional a la superación de los hitos de telemetría, auditoría de eventos y capacitación técnica del equipo."""
    }
]

FORMAL_SAMPLES.extend([
    {
        "user": "Redacta el modelo formal de un recurso de reposición potestativo contra una sanción administrativa tributaria municipal.",
        "assistant": r"""**A LA DIRECCIÓN GENERAL DE TRIBUTOS Y RECAUDACIÓN**
**AYUNTAMIENTO DE MADRID**

D. Alejandro Carrillo Sanz, mayor de edad, con NIF 09.876.543-K, actuando en su propio nombre y derecho, con domicilio a efectos de notificaciones en la calle Alcalá nº 142, 3º Dcha., 28009 Madrid, ante ese órgano administrativo comparece y, como mejor proceda en Derecho, **DICE**:

Que con fecha 28 de octubre de 2026 le ha sido notificada la Resolución Administrativa Sancionadora con número de expediente `SANC-2026-9042`, por la cual se impone una sanción tributaria de 1.850,00 € por supuesta omisión de declaración catastral.

Que no estando conforme con dicha resolución por estimarla lesiva a sus derechos e infundada en Derecho, dentro del plazo legal de un mes computado desde la notificación, interpone formal **RECURSO POTESTATIVO DE REPOSICIÓN**, al amparo de lo dispuesto en los artículos 123 y 124 de la Ley 39/2015 del Procedimiento Administrativo Común, con base en las siguientes:

**ALEGACIONES**:

**PRIMERA.- Vicio de nulidad por indefensión material y falta de motivación**: La resolución impugnada adolece de una descripción fáctica concreta de la conducta imputada, limitándose a citar genéricamente artículos de la ordenanza fiscal municipal, impidiendo a esta parte conocer los fundamentos técnicos de la liquidación y vulnerando el artículo 35 de la Ley 39/2015.

**SEGUNDA.- Acreditación documental del cumplimiento en plazo**: Consta en el asiento registral telemático con número de registro de entrada `REG-2026-3312`, fechado el 14 de marzo de 2026 (Anexo I), la presentación en tiempo y forma del modelo tributario 900-N de alteración de bienes inmuebles, desvirtuándose la supuesta omisión imputada.

**SOLICITA**:  
Tenga por presentado este escrito, se sirva admitirlo a trámite junto con los documentos adjuntos y, previos los trámites pertinentes, dicte resolución estimatoria del presente recurso revocando y dejando sin efecto en su totalidad la sanción tributaria impuesta."""
    },
    {
        "user": "Redacta una cláusula contractual formal de confidencialidad y no divulgación (NDA) bilateral para un consorcio tecnológico.",
        "assistant": r"""**CLÁUSULA SÉPTIMA: CONFIDENCIALIDAD, SECRETO PROFESIONAL Y NO DIVULGACIÓN**

**7.1. Definición de Información Confidencial**:  
A los efectos del presente Contrato, tendrá la consideración de Información Confidencial toda información técnica, operativa, comercial, financiera, algoritmos, diagramas de arquitectura de software, especificaciones de producto, bases de datos o código fuente transmitida directa o indirectamente por cualquiera de las PARTES (la «Parte Emisora») a la otra PARTE (la «Parte Receptora»), ya sea de forma verbal, escrita, gráfica o por soporte electrónico, debidamente identificada como confidencial o cuya naturaleza reserve razonablemente tal condición.

**7.2. Obligaciones de la Parte Receptora**:  
La Parte Receptora se obliga expresamente a:
a) Custodiar la Información Confidencial con al menos el mismo grado de diligencia y estándares de seguridad que emplea para proteger su propia información de análoga importancia, y nunca inferior a un estándar razonable de diligencia mercantil.  
b) Utilizar la Información Confidencial única y exclusivamente para los fines previstos en la ejecución del presente proyecto consorciado.  
c) Limitar el acceso a dicha información estrictamente a aquellos administradores, directivos, empleados y asesores profesionales que requieran conocerla para la ejecución del Contrato (*need to know*), asegurando que se encuentren vinculados por compromisos contractuales de confidencialidad no menos restrictivos.  
d) No divulgar, copiar, reproducir ni transferir la información a terceras partes no autorizadas sin el consentimiento previo, expreso y por escrito de la Parte Emisora.

**7.3. Excepciones**:  
Las obligaciones estipuladas no serán aplicables a aquella información que: (i) sea de dominio público sin mediar quebrantamiento del presente acuerdo; (ii) estuviera legalmente en posesión de la Parte Receptora con anterioridad a su divulgación; (iii) haya sido recibida de un tercero de buena fe sin deber de reserva; o (iv) deba ser revelada por requerimiento judicial o regulatorio firme, previa notificación formal inmediata a la Parte Emisora.

**7.4. Vigencia y consecuencias**:  
El deber de confidencialidad permanecerá en vigor durante la vigencia del contrato y por un período improrrogable de **cinco (5) años** tras su terminación por cualquier causa, facultando el incumplimiento a la reclamación judicial de los daños y perjuicios y lucro cesante acreditados."""
    },
    {
        "user": "Redacta el modelo formal de una notificación de brecha de seguridad de datos personales ante la autoridad reguladora de control (RGPD).",
        "assistant": r"""**COMUNICACIÓN FORMAL DE INCIDENCIA DE SEGURIDAD Y BRECHA DE DATOS PERSONALES**
*(De conformidad con el artículo 33 del Reglamento General de Protección de Datos - RGPD 2016/679)*

**A la atención de**:  
Agencia Española de Protección de Datos (AEPD)  
Dirección de Inspección y Registro de Brechas  

---

### 1. Datos del Responsable del Tratamiento
- **Denominación Social**: Plataforma Financiera Segura S.A.
- **NIF**: A-28765432
- **Delegado de Protección de Datos (DPO)**: D. Martín Salazar Vega (dpo@financierasegura.es)

### 2. Naturaleza y Cronología del Incidente
- **Fecha y hora de detección**: 14 de noviembre de 2026, a las 16:30 h (UTC+1).
- **Origen de la brecha**: Acceso ilegítimo a un bucket de almacenamiento en la nube debido a un error de configuración de permisos tras una actualización de infraestructura.
- **Tipología de la brecha**: Quiebra de confidencialidad y disponibilidad temporal de copias de seguridad analíticas.

### 3. Categorías y Volumen de Datos Afectados
- **Número aproximado de interesados afectados**: 4.250 usuarios registrados.
- **Categorías de datos concernidas**: Datos identificativos (nombres completos, números de documento de identidad y correos electrónicos corporativos).
- **Datos especialmente protegidos**: No consta acceso ni afectación a contraseñas (cifradas en reposo mediante hash Argon2id), datos de tarjetas bancarias, biometría ni categorías especiales del art. 9 del RGPD.

### 4. Posibles Consecuencias para los Titulares
Riesgo moderado de recepción de comunicaciones de suplantación de identidad (*phishing*) dirigidas a las direcciones de correo electrónico expuestas.

### 5. Medidas Correctivas Adoptadas
1. **Contención inmediata**: A las 17:05 h (35 minutos tras la detección), se revocaron las credenciales de acceso público y se aislaron las reglas de firewall perimetral.
2. **Mitigación y remediación**: Se ejecutó una auditoría forense digital que confirmó la descarga de una única tabla de auditoría desactualizada y se reforzó la política de cifrado simétrico AES-256 en reposo.
3. **Comunicación a interesados**: Se ha preparado el canal informativo directo individualizado conforme al art. 34 del RGPD para alertar a los usuarios concernidos."""
    },
    {
        "user": "Redacta un acta formal de entrega y recepción definitiva de un desarrollo de infraestructura tecnológica.",
        "assistant": r"""**ACTA DE ENTREGA, PRUEBAS DE ACEPTACIÓN Y RECEPCIÓN DEFINITIVA DE SERVICIOS**
**EXPEDIENTE TÉCNICO: PROY-2026-CLOUD-CORE**

En la ciudad de Bogotá D.C., a los 15 días del mes de noviembre de 2026, se constituyen en las instalaciones corporativas:

- **Por la entidad CONTRATANTE**: Dña. Claudia Morales Peña, Gerente de Infraestructura de Telecomunicaciones del Estado.
- **Por la empresa CONTRATISTA**: D. Javier Gómez Rueda, Director de Proyectos de Infraestructuras Digitales Avanzadas S.A.S.

Ambas partes proceden a la formalización de la presente acta con base en los siguientes extremos:

### 1. Objeto de la Entrega
La recepción definitiva y puesta en producción del proyecto *«Despliegue y Configuración de Infraestructura de Nube Híbrida y Redundancia de Centros de Datos»*, en estricta conformidad con el Pliego de Prescripciones Técnicas y el cronograma de ejecución pactado en el Contrato Nº CT-2025-412.

### 2. Verificación de Ensayos y Pruebas de Aceptación (FAT/SAT)
Entre los días 1 y 12 de noviembre de 2026, la Comisión de Seguimiento Técnico supervisó la batería de pruebas de carga, conmutación automática por fallo (*failover*) y ciberseguridad, certificando:
- Latencia de replicación intercentro inferior a 8 milisegundos en condiciones de carga nominal.
- Conmutación automática de tráfico de servicios críticos ejecutada satisfactoriamente en 14 segundos (RTO comprometido < 30 s).
- Entrega exhaustiva de la documentación técnica de arquitectura, manuales operativos de administración y código de automatización (Terraform/Ansible) en el repositorio oficial.

### 3. Conformidad y Recepción
La entidad CONTRATANTE manifiesta su **TOTAL CONFORMIDAD** con los entregables e hitos presentados, declarando formalmente la **RECEPCIÓN DEFINITIVA Y ACEPTACIÓN TÉCNICA** del proyecto sin reservas ni objeciones pendientes.

### 4. Período de Garantía
A partir de la fecha de suscripción del presente documento, entra en vigencia el período de garantía técnica y soporte de nivel 3 comprometido por el CONTRATISTA, por una duración improrrogable de doce (12) meses.

En constancia de lo acordado, suscriben la presente acta en dos ejemplares originales de idéntico tenor y efecto legal."""
    },
    {
        "user": "Reescribe el siguiente informe informal de desempeño laboral a una evaluación técnica y formal para el comité de talento:\n«Hola, les escribo para decirles que Lucas rindió re bien este año en el equipo. Le puso muchas ganas, aprendió a programar en Go súper rápido y cuando se prendió fuego el servidor el mes pasado vino un sábado a la noche y lo arregló sin quejarse. Es medio desordenado con la documentación de sus tareas en Jira y a veces habla poco en las reuniones generales, pero la verdad que su laburo técnico es impecable y creo que merece un ascenso a Senior».",
        "assistant": r"""**INFORME DE EVALUACIÓN DE DESEMPEÑO TÉCNICO Y PROPUESTA DE PROMOCIÓN PROFESIONAL**

**Colaborador Evaluado**: Lucas Benítez  
**Posición Actual**: Ingeniero de Software Semi-Senior (Backend)  
**Evaluador**: Líder Técnico de Equipo  
**Órgano Destinatario**: Comité de Talento y Desarrollo Organizacional  
**Período de Evaluación**: Ejercicio Anual 2026  

---

### 1. Competencias Técnicas y Rendimiento Operativo
- **Capacidad de aprendizaje y adaptabilidad tecnológica**: Durante el presente ejercicio, demostró una curva de asimilación destacada al dominar el ecosistema Go en menos de ocho semanas, implementando componentes de alta concurrencia que redujeron el consumo de memoria del backend en un 35%.
- **Resolución de incidentes críticos y compromiso corporativo**: Ante la degradación severa de infraestructura registrada el pasado mes de octubre, lideró de forma autónoma el diagnóstico y despliegue del parche correctivo durante un intervalo no laboral crítico, restableciendo los servicios productivos y mitigando el impacto financiero en los acuerdos de nivel de servicio (SLA).

### 2. Oportunidades de Mejora y Habilidades Blandas
- **Rigor metodológico y trazabilidad**: Se observa una inconsistencia periódica en la actualización documental de artefactos y tickets de seguimiento en Jira, aspecto que requiere mayor estandarización para optimizar la gobernanza de proyectos del área.
- **Comunicación y visibilidad en foros transversales**: Conviene potenciar su participación activa y asertiva en reuniones plenarias interdepartamentales, facilitando la socialización de sus criterios de diseño técnico.

### 3. Recomendación del Evaluador
En consideración a su alta solvencia técnica, autonomía demostrada y fiabilidad ante escenarios de contingencia, se emite recomendación **FAVORABLE** para su promoción a la categoría de **Ingeniero de Software Senior**, supeditando su consolidación a la consecución de los objetivos de mejora metodológica definidos."""
    },
    {
        "user": "Redacta una carta formal de notificación fehaciente por suspensión de servicios debida a mora reiterada en el pago de facturas corporativas.",
        "assistant": r"""**COMUNICACIÓN NOTIFICATORIA FEHACIENTE POR SUSPENSIÓN PREVENTIVA DE SUMINISTRO**

**Ciudad y Fecha**: Madrid, 15 de noviembre de 2026  
**Remitente**: Telecomunicaciones y Conectividad Corporativa S.A.  
**Destinatario**:  
A la atención del Representante Legal  
Servicios Comerciales del Norte S.L.  
Paseo de la Castellana nº 200, 28046 Madrid  

**REF**: Requerimiento formal de pago fehaciente y preaviso de corte de servicio de enlaces dedicados de datos (Contrato Nº TEL-2024-88)

De nuestra consideración:

Nos dirigimos a ustedes a fin de requerirles de manera fehaciente el pago de las obligaciones dinerarias vencidas y exigibles derivadas del contrato de referencia, correspondientes a las facturas que a continuación se detallan:

- Factura Nº FC-2026-1102 (Vto: 31/08/2026): 4.120,50 €
- Factura Nº FC-2026-1289 (Vto: 30/09/2026): 4.120,50 €
- Factura Nº FC-2026-1475 (Vto: 31/10/2026): 4.120,50 €
- **Total Principal Vencido e Impagado**: **12.361,50 €** (doce mil trescientos sesenta y un euros con cincuenta céntimos).

Habiendo resultado infructuosas las gestiones de cobro por los canales administrativos habituales, les notificamos que disponen de un plazo improrrogable de **diez (10) días hábiles**, a contar desde la recepción de la presente, para proceder a la regularización íntegra de la deuda mediante ingreso bancario en la cuenta institucional de la compañía.

Transcurrido dicho término sin verificarse el abono fehaciente, procederemos a la **suspensión cautelar inmediata del suministro de telecomunicaciones y enlaces troncales**, de conformidad con lo pactado en la Cláusula 12.3 del contrato suscrito, iniciando simultáneamente las acciones judiciales pertinentes para la reclamación del principal, intereses de demora comercial devengados y costas procesales.

Atentamente,

________________________________________  
**Dirección de Asesoría Jurídica y Gestión de Cobro**  
Telecomunicaciones y Conectividad Corporativa S.A."""
    }
])
