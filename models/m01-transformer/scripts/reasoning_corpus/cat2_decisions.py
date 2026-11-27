"""
Categoría 2: Toma de decisiones personales, profesionales y estratégicas (20 escenarios)
Bloques <think> concisos de 30-80 tokens de retrospectiva y evaluación sintética.
"""

SCENARIOS_CAT2 = [
    {
        "user": "Soy ingeniero de software con 6 años de experiencia y tengo dos ofertas: \n- Oferta A (Banco tradicional): 58.000 € fijos + 5.000 € bonus, 3 días presenciales en Madrid (45 min trayecto). Stack: Java 8 legado con Oracle.\n- Oferta B (Startup Serie A B2B): 46.000 € fijos + stock options estimadas en 12.000 € a 4 años, 100% remoto. Stack: Go, FastAPI, Kafka, Kubernetes en AWS.\nValoro proyección a 5 años, equilibrio y salario neto. ¿Qué decido?",
        "think": "Contexto: Ingeniero evaluando banco tradicional de stack obsoleto vs startup remota cloud-native.\nEvaluación: El banco paga más hoy pero devalúa el CV; el stack moderno de la startup multiplica el valor futuro.\nConclusión: Elegir startup B negociando ajuste salarial base.",
        "assistant": """Para un ingeniero con 6 años de experiencia, esta decisión no es entre salarios presentes, sino entre **liquidez inmediata vs. valor de mercado a 5 años**:

### 1. Comparativa Económica Real (Ajustada a Costes)
- **Oferta A (Banco):** ~3.400 € netos/mes (en 12 pagas).
  - *Costes ocultos:* 3 días semanales de oficina = 18 horas al mes perdidas en metro/coche. Gastos de transporte y comidas restan ~180 € netos/mes.
  - *Sueldo real disponible:* ~3.220 € netos/mes.
- **Oferta B (Startup):** ~2.720 € netos/mes. Las stock options deben considerarse 0 € en tu presupuesto diario.
  - *Diferencia real en mano:* Unos **500 € netos mensuales** a favor del banco.

### 2. El Riesgo Decisivo: Obsolescencia Tecnológica
- **En el Banco A:** Trabajar con Java 8 y bases de datos relacionales tradicionales congela tu perfil. Dentro de 4 años tu capacidad de competir por salarios de >80k € será mínima.
- **En la Startup B:** Diseñar microservicios con **Go, Kafka, Docker, Kubernetes y AWS** te sitúa en el percentil superior del mercado europeo. Tras 2 años demostrables en este entorno, tu caché internacional alcanzará los **75.000 € - 90.000 €** en remoto.

### 3. Veredicto y Recomendación de Acción
**Elige la Oferta B (Startup)** pero negociando antes de firmar:
- Comunica a la startup: *"La oportunidad técnica con Go y Kubernetes es mi prioridad, pero tengo una oferta competidora en 63.000 €. Si podéis ajustar el base a 49.000 € o incluir un bonus de firma de 3.000 €, firmo hoy con vosotros"*.
- Recuperarás 200 horas de transporte al año y construirás un perfil técnico de primer nivel."""
    },
    {
        "user": "Tengo 32 años, pago 900 € de alquiler y tengo 65.000 € ahorrados. Puedo comprar un piso de 210.000 € con hipoteca fija al 2,85% a 30 años (cuota de 695 €/mes), pero la entrada (20%) más gastos (10%) absorben 63.000 €, dejándome con solo 2.000 € de saldo. La alternativa es seguir de alquiler e invertir 50.000 € en MSCI World con 300 €/mes. ¿Qué me conviene?",
        "think": "Contexto: Compra de piso consumiendo el 97% del ahorro líquido vs alquiler con inversión indexada.\nEvaluación: La hipoteca fija es atractiva pero descapitalizarse a 2.000 € genera riesgo de ruina.\nConclusión: Posponer compra 6-9 meses para acumular colchón o negociar hipoteca al 85%.",
        "assistant": """Aunque la hipoteca fija al 2,85% es financieramente ventajosa a largo plazo frente al alquiler, **descapitalizarte al 97% es una temeridad financiera**:

### 1. El Riesgo Crítico de Quedarse con 2.000 €
- Comprar una vivienda exige afrontar el primer mes suministros, mudanza, seguro de hogar/vida e imprevistos comunitarios.
- Con solo 2.000 € en cuenta, cualquier avería doméstica, reparación del coche o baja médica temporal te empujaría al impago inmediato o al endeudamiento con créditos caros.
- **Regla inquebrantable:** Nunca compres una vivienda sin retener un **fondo de emergencia intocable de 8.000 € a 10.000 €** (6 meses de gastos).

### 2. Comparativa de Costes Mensuales Reales
- **Alquiler:** 900 €/mes cerrados (el propietario cubre IBI, seguro estructural y comunidad).
- **Vivienda propia:** 695 € (cuota) + 70 € (comunidad) + 40 € (IBI) + 45 € (seguros) + 75 € (mantenimiento anual prorrateado) = **~925 €/mes reales**.

### 3. Veredicto y Hoja de Ruta
No compres hoy en estas condiciones de liquidez:
1. **Pausa la compra entre 6 y 9 meses:** Continúa de alquiler ahorrando al máximo hasta alcanzar **75.000 € totales**.
2. **Alternativa inmediata:** Consulta con un broker hipotecario la opción de financiar al **85% o 90%**. Aportar 42.000 € en lugar de 63.000 € te permitiría comprar la vivienda reteniendo 23.000 € seguros en el banco."""
    },
    {
        "user": "Somos un SaaS B2B logístico con 60 clientes y 400k € de ARR. Los clientes nos exigen un módulo de analítica y dashboards con exportación a PDF. Desarrollarlo internamente costaría 4 meses de 2 ingenieros senior (45.000 €). Licenciar una herramienta embebida de terceros cuesta 12.000 €/año + 30 €/cliente/mes y se integra en 3 semanas con 1 dev. ¿Qué opción elegimos?",
        "think": "Contexto: SaaS B2B sopesando desarrollo in-house de analítica vs integrar solución embebida.\nEvaluación: El core del negocio es la logística, no renderizar PDFs; desarrollar in-house paraliza el roadmap.\nConclusión: Adoptar solución embebida de terceros y monetizarla como add-on.",
        "assistant": """Para un SaaS B2B de vuestro tamaño, **la decisión acertada es licenciar la solución embebida de terceros (Opción B)**:

### 1. El Coste de Oportunidad de Ingeniería (Core vs. Context)
- Vuestra ventaja competitiva reside en los algoritmos de enrutamiento y la operativa logística. Construir un motor de gráficos interactivos con filtros multitenant y renderizado a PDF no os diferencia en el mercado.
- Bloquear a 2 desarrolladores senior durante un cuatrimestre paraliza por completo el avance de vuestro producto principal.

### 2. Retorno Financiero y Estrategia de Monetización
- El error habitual es considerar los 30 €/cliente/mes como un coste a asumir por vuestro margen:
  - Empaquetad el módulo como un **Add-On de Analítica Avanzada & Business Intelligence a 89 €/mes por cliente**.
  - Si 30 de vuestros 60 clientes lo contratan, ingresaréis 2.670 €/mes frente a un coste variable de 900 €/mes, generando **beneficio neto desde el primer mes**.

### 3. Conclusión
Integrad la herramienta en 3 semanas, responded de inmediato a la demanda del mercado y continuad enfocando vuestro talento de desarrollo en la logística."""
    },
    {
        "user": "He heredado 45.000 € limpios. Tengo hipoteca variable al 4,10% (Euríbor + 0,85%) con 85.000 € pendientes a 18 años (550 €/mes). Ya tengo fondo de reserva de 12.000 €. ¿Amortizo de golpe la hipoteca o invierto los 45.000 € en fondos indexados globales al MSCI World?",
        "think": "Contexto: Herencia de 45.000 € dudando entre liquidar hipoteca al 4,10% o invertir a largo plazo.\nEvaluación: El 4,10% hipotecario es rentabilidad libre de riesgo y de impuestos; la renta variable ofrece más a 18 años pero con volatilidad.\nConclusión: Estrategia equilibrada 50/50: amortizar 22.500 € a plazo e indexar 22.500 €.",
        "assistant": """Al disponer ya de un fondo de emergencia de 12.000 € y empleo estable, puedes maximizar el rendimiento de esta herencia combinando seguridad matemática y rentabilidad futura:

### 1. La Rentabilidad Sin Riesgo de la Hipoteca
- Al estar al **4,10% de interés variable**, amortizar hipoteca te proporciona un **4,10% neto garantizado y libre de impuestos**.
- Para obtener un 4,10% limpio en cualquier producto bancario seguro, necesitarías un depósito superior al **5,05% TAE bruto** por la retención fiscal del ahorro.
- Si amortizas, elige siempre **reducir plazo**: te ahorrarás casi el doble de intereses acumulados que reduciendo cuota.

### 2. El Crecimiento Compuesto del MSCI World
- Históricamente, la inversión global indexada promedia un **7% a 8% anual** en horizontes superiores a 15 años. A 18 años vista, destinar el 100% al ladrillo te privaría del motor de acumulación patrimonial para tu jubilación.

### 3. Veredicto: Estrategia Híbrida 50/50
- **Amortiza 22.500 € reduciendo plazo:** Recortarás unos 6 años de hipoteca y te ahorrarás más de 11.000 € directos en intereses futuros.
- **Invierte 22.500 € en MSCI World:** Aportando en 6-10 mensualidades mediante DCA para mitigar la volatilidad a corto plazo. A los 58 años ese capital rondará los **65.000 € a 75.000 €** de patrimonio líquido."""
    },
    {
        "user": "Nuestro equipo de ingeniería crecerá de 18 a 45 personas en 18 meses. Tenemos 12 repositorios (polyrepo) en TypeScript: 4 frontends React, 5 servicios NestJS y 3 paquetes npm privados. Hay constantes desajustes de versiones y PRs cruzadas. ¿Migramos a un Monorepo con Turborepo/Nx o mantenemos repos separados?",
        "think": "Contexto: Escalado de equipo técnico con 12 repositorios TypeScript sufriendo desajustes de versiones.\nEvaluación: Polyrepo multiplica la fricción de dependencias; monorepo permite refactors atómicos con caché remoto.\nConclusión: Migrar a Monorepo con pnpm y Turborepo por fases.",
        "assistant": """Con un crecimiento previsto de 18 a 45 ingenieros y una base 100% TypeScript, **la migración a Monorepo es imprescindible**. El modelo multirepo actual colapsará en cuanto se incorporen 10 personas más:

### 1. Ventajas Clave frente a la Situación Actual
- **Fin del infierno de versiones en npm:** Las 3 librerías compartidas pasan a consumirse directamente como paquetes de workspace local. Modificar un componente actualiza al instante las aplicaciones dependientes sin compilar ni publicar paquetes en el registro.
- **Pull Requests atómicas:** Una única PR contendrá el cambio en el DTO de NestJS y su consumo en el frontend de React, eliminando dependencias de despliegues secuenciales.

### 2. Respuesta a los Tiempos de CI (Affected & Remote Cache)
- La preocupación de DevOps se resuelve con dos mecanismos de **Turborepo** o **Nx**:
  1. **Análisis de afectados (`affected`):** En cada commit solo se compilan y testean los paquetes que han sufrido cambios o dependen de ellos.
  2. **Caché remoto distribuido (S3 o cloud):** Si el código ya fue compilado previamente por otro compañero o en otra rama, el resultado se descarga en milisegundos.

### 3. Recomendación de Adopción
Optad por **pnpm workspaces + Turborepo**: ofrece la menor curva de aprendizaje del mercado y permite completar la migración de librerías y frontends en menos de 4 semanas."""
    },
    {
        "user": "Nuestro e-commerce factura 4M €/año con 2,5M de visitas/mes sobre AWS ECS Fargate (2.400 €/mes de cómputo). DevOps propone migrar a Kubernetes autogestionado (EKS + Karpenter) para ahorrar 1.200 €/mes. Solo tenemos 1 DevOps y 6 programadores de producto. ¿Compensa la migración?",
        "think": "Contexto: E-commerce de 4M € facturación evaluando migración a Kubernetes con solo 1 ingeniero de DevOps.\nEvaluación: Ahorrar 1.200 €/mes añade complejidad crítica y obliga a contratar otro DevOps.\nConclusión: Quedarse en ECS Fargate activando Compute Savings Plans.",
        "assistant": """La respuesta es tajante: **NO compensa migrar a Kubernetes**. Sería una decisión de sobreingeniería destructiva para vuestro equipo:

### 1. La Falacia del Ahorro de 1.200 € al Mes
- Ahorrar 14.400 € al año en cómputo te obligará a asumir el coste de operar Kubernetes (upgrades obligatorios de versión cada 4 meses, gestión de nodos, redes CNI y controladores).
- **El riesgo del "Bus Factor = 1":** Si vuestro único DevOps enferma o dimite, ninguno de los 6 programadores sabrá depurar un problema de red de pods o de kubelet en mitad de una caída de ventas. Contratar a un segundo DevOps de respaldo os costaría más de 65.000 € al año, destruyendo cualquier ahorro.

### 2. Cómo Obtener el Mismo Ahorro Mañana sin Obras
- **Compute Savings Plans en AWS:** Contrata un compromiso de uso de 1 o 3 años para Fargate. Recibirás un **descuento inmediato de entre el 25% y el 40%** sobre la factura actual de computación con un solo clic.
- **Fargate Spot en staging y workers:** Configura las tareas en segundo plano no críticas sobre Fargate Spot con un 70% de descuento.

Mantened ECS Fargate: es un servicio totalmente gestionado que permite al equipo centrarse en maximizar la conversión de ventas."""
    },
    {
        "user": "Somos una agencia digital de 12 personas con facturación de 450k €/año. Sufrimos oscilaciones graves de ingresos alternando meses de sobrecarga con meses de sequía comercial. ¿Elegimos Estrategia A (volumen low-cost a 3.500 €/web con comercial agresivo) o Estrategia B (boutique de alto ticket a 25.000 € + retainer mensual de 2.000 €)?",
        "think": "Contexto: Agencia digital de 12 personas con ingresos inestables evaluando volumen vs alto ticket con retainers.\nEvaluación: Modelo de volumen requiere captación masiva insostenible; retainers estabilizan flujo de caja.\nConclusión: Adoptar posicionamiento boutique con contratos de retención obligatorios.",
        "assistant": """Para una estructura de 12 personas, la **Estrategia A (Volumen Low-Cost) es una trampa de agotamiento**. Competir en precios de 3.500 € os enfrentaría a agencias offshore y freelancers, exigiendo cerrar 15 clientes nuevos todos los meses.

### 1. La Solución Estructural: Ingresos Recurrentes (MRR)
La montaña rusa de ingresos no se cura vendiendo más webs sueltas, sino **garantizando cobros mensuales fijos que paguen las nóminas el día 1 de cada mes**:
- **Meta con Estrategia B (Alto Ticket + Retainers):**
  - 6 a 8 proyectos de implantación al año a un promedio de **26.000 €** = ~180.000 €/año.
  - 10 a 12 clientes en **retainers de optimización y desarrollo continuo de 2.000 € a 2.500 €/mes** = **~300.000 €/año asegurados**.
  - Ingresos totales superiores a 480.000 €, pero con el 60% cubierto de forma predecible y con clientes satisfechos.

### 2. Plan de Transición en 3 Pasos
1. **Especialización vertical:** Posiciona la agencia como experta en un nicho de alto valor (ej. Shopify Plus para marcas de moda o plataformas B2B en Webflow).
2. **Retainer obligatorio:** No aceptes proyectos de desarrollo web sin vincular un contrato mínimo de 6 meses de acompañamiento CRO y soporte continuo.
3. **Elevación escalonada del precio mínimo:** Fija el suelo de entrada en 10.000 € el primer trimestre y súbelo a 20.000 € en 6 meses."""
    },
    {
        "user": "Nuestra startup en fase semilla (4 desarrolladores) tiene que construir el MVP de una plataforma de contratación laboral. El CTO propone arrancar directamente con 6 microservicios comunicados por gRPC y eventos en Kafka. El lead dev defiende un monolito modular en Django o Rails. ¿Qué arquitectura inicial elegimos?",
        "think": "Contexto: Startup de 4 personas decidiendo entre microservicios con Kafka vs monolito modular para un MVP.\nEvaluación: Microservicios en fase semilla añaden sobrecarga de red y despliegues sin límites de dominio claros.\nConclusión: Construir monolito modular bien estructurado y desacoplar solo cuando el modelo madure.",
        "assistant": """Para un equipo de 4 personas construyendo un MVP, **adoptar microservicios con Kafka es un error crítico de sobreingeniería**. La elección indiscutible es un **Monolito Modular**:

### 1. Por qué los Microservicios Fracasan en Fase Semilla
- En la fase inicial los límites del modelo de negocio cambian cada dos semanas según el feedback de los primeros clientes.
- Si defines 6 microservicios prematuramente, tus límites de dominio serán erróneos, obligándote a realizar transacciones distribuidas complejas y refactors de red continuos.
- La sobrecarga de desplegar, monitorizar y trazar 6 servicios independientes absorberá más del 40% del tiempo de vuestros 4 ingenieros.

### 2. La Potencia del Monolito Modular
- Diseña una única aplicación (en Django, NestJS o Ruby on Rails) estructurada en **módulos estrictamente desacoplados en carpetas** (ej. `auth/`, `job_postings/`, `applications/`, `billing/`), interactuando mediante interfaces internas limpias.
- Tiempos de despliegue en un solo contenedor, base de datos única con integridad referencial ACID garantizada y desarrollo local inmediato sin necesidad de clústeres locales.

### 3. Regla de Extracción Futura
Solo cuando un módulo específico requiera un escalado independiente extremo o sea gestionado por un equipo propio de 5 ingenieros, se extrae como microservicio independiente."""
    },
    {
        "user": "Necesito un vehículo para mi actividad comercial como autónomo (recorro 30.000 km/año visitando clientes en zonas urbanas con restricciones medioambientales y autovía). Dudo entre comprar un híbrido nuevo no enchufable (28.000 € al contado), un renting a 4 años (460 €/mes todo incluido) o un diésel de ocasión con etiqueta C (14.000 €). ¿Qué opción es más rentable?",
        "think": "Contexto: Autónomo que recorre 30.000 km/año con acceso a zonas urbanas restringidas.\nEvaluación: Diésel C sufrirá restricciones urbanas y desgaste severo en 4 años; renting desgrava IRPF/IVA íntegro.\nConclusión: Renting de híbrido con etiqueta ECO por optimización fiscal y protección ante averías.",
        "assistant": """Al recorrer **30.000 km anuales como autónomo** y necesitar acceso a zonas de bajas emisiones (ZBE), la opción más inteligente y rentable es el **Renting de un vehículo híbrido con etiqueta ECO**:

### 1. Ventajas Fiscales Inmediatas del Renting
- Para un profesional autónomo cuya actividad exige desplazamientos, la cuota de renting (460 €/mes) es un **gasto deducible al 100% en IRPF y con deducción del 50% al 100% del IVA** soportado.
- Al comprar al contado o financiar, la amortización contable es lenta y asumes el IVA de golpe sin poder deducirlo íntegramente con la misma agilidad de flujo de caja.

### 2. Blindaje ante el Desgaste por Alto Kilometraje
- A 30.000 km/año, en 4 años el vehículo acumulará 120.000 km.
- Con el renting, **el cambio de 8 neumáticos, el seguro a todo riesgo, los impuestos y todas las revisiones mecánicas están cubiertos** en la cuota fija mensual, eliminando cualquier sorpresa financiera.
- La compra del coche usado diésel etiqueta C te expondrá a averías caras (filtro de partículas, inyectores) y a crecientes restricciones de circulación en centros urbanos."""
    },
    {
        "user": "Tenemos un producto SaaS de facturación electrónica validado con 15 clientes piloto que pagan 50 €/mes. Tenemos la oportunidad de levantar una ronda pre-semilla de 200.000 € cediendo el 18% de equity a un fondo de capital riesgo, o mantenernos en bootstrapping autofinanciando el crecimiento con servicios de consultoría. ¿Qué vía de financiación elegimos?",
        "think": "Contexto: SaaS validado con 15 clientes debatiendo entre ronda de 200k € por 18% o bootstrapping con consultoría.\nEvaluación: 200k € proporcionan runway para dedicarse al producto; la consultoría distrae y alarga el desarrollo.\nConclusión: Levantar la ronda fijando objetivos claros de crecimiento para alcanzar Serie A.",
        "assistant": """Habiendo validado que 15 clientes pagan por el producto, la elección acertada es **aceptar la ronda pre-semilla de 200.000 € por el 18% de equity**:

### 1. El Peligro Oculto del Bootstrapping con Consultoría
- Financiar un SaaS haciendo proyectos de consultoría a medida es la causa número uno de estancamiento de producto: los fundadores dedican el 80% de su tiempo a apagar fuegos de los clientes de consultoría para pagar las nóminas del mes, dejando el SaaS desatendido.
- El mercado del software se mueve a gran velocidad: retrasar la maduración comercial 18 meses permite que competidores con capital capturen la cuota de mercado.

### 2. El Impulso de los 200.000 €
- Una valoración pre-money de ~900.000 € por el 18% es razonable para vuestra fase.
- Esos 200.000 € os otorgan un **runway de 14 a 16 meses** para contratar a un segundo desarrollador y dedicaros al 100% a la captación de clientes de facturación.
- Estableced como único hito pasar de los 750 € de MRR actuales a **10.000 € - 15.000 € de MRR en 12 meses**, momento en el cual podréis levantar una ronda Serie A con valoraciones mucho mayores."""
    },
    {
        "user": "Nuestra plataforma e-commerce de moda recibe 1.200 tickets de soporte al mes. Tenemos la opción de subcontratar la atención al cliente de primer nivel a una agencia externa offshore por 1.800 €/mes o contratar a 2 agentes internos en remoto a media jornada por 2.400 €/mes en total. ¿Qué camino garantiza mejor equilibrio entre coste y satisfacción?",
        "think": "Contexto: E-commerce de moda evaluando soporte offshore low-cost vs equipo interno a media jornada.\nEvaluación: Soporte externo responde con guiones genéricos dañando fidelización; personal interno conoce el producto.\nConclusión: Contratar agentes internos remotos priorizando resolución en primer contacto.",
        "assistant": """En el comercio electrónico de moda, la atención al cliente es una herramienta directa de retención y recompra, no un mero centro de coste. **Debéis optar por los 2 agentes internos en remoto (2.400 €/mes)**:

### 1. Por qué el Soporte Offshore Low-Cost Fracasa en Moda
- Los proveedores offshore basan su modelo en volumen y tiempo medio de atención (AHT): sus operadores responden con plantillas rígidas sin empatía y escalan cualquier duda no estándar, generando frustración en el comprador.
- En moda, resolver dudas sobre tallajes, devoluciones o incidencias logísticas con calidez humana convierte un cliente descontento en un cliente fiel de por vida.

### 2. Mayor Retorno por Solo 600 € Más al Mes
- Dos empleados internos conocen el catálogo a fondo, utilizan el tono de voz de vuestra marca y detectan patrones de errores de fabricación o tallaje que transmiten directamente al equipo de compras.
- Una mejora del 5% en la tasa de retención de clientes gracias a un excelente servicio posventa compensa con creces la diferencia económica de 600 € mensuales."""
    },
    {
        "user": "Tengo 26 años, soy graduado en Administración y Dirección de Empresas y quiero reorientar mi carrera hacia el análisis de datos corporativo. Dudo entre matricularme en un máster oficial presencial de 14.000 € en una escuela de negocios de prestigio o realizar certificaciones técnicas (Google Data Analytics, AWS Cloud Practitioner, Power BI Data Analyst) y proyectos públicos en GitHub invirtiendo menos de 1.000 €. ¿Qué ruta formativa tiene mejor ROI?",
        "think": "Contexto: Graduado en ADE buscando pivotar a análisis de datos mediante máster de 14k € vs certificaciones y portfolio.\nEvaluación: El máster aporta networking pero cuesta 14 veces más; las empresas técnicas evalúan habilidades demostrables.\nConclusión: Certificaciones técnicas oficiales combinadas con portfolio de proyectos reales en GitHub.",
        "assistant": """Para orientar tu carrera hacia el análisis de datos desde una titulación previa como ADE, **la ruta de certificaciones técnicas + portfolio público ofrece un retorno de inversión (ROI) inmensamente superior**:

### 1. Qué Busca Realmente el Mercado en Datos
- En el sector de los datos, los procesos de selección técnicos se basan en pruebas prácticas de SQL, Python y modelado en herramientas de BI. Un diploma de 14.000 € sin soltura técnica real no garantiza superar la criba.
- Tu titulación en ADE ya te otorga la mitad de lo que buscan las empresas: **entendimiento del negocio, finanzas y KPIs comerciales**. Solo necesitas demostrar tu solvencia con las herramientas analíticas.

### 2. Plan de Acción Técnico (Coste < 800 €)
1. **Certificaciones oficiales de valor:**
   - **Microsoft PL-300 (Power BI Data Analyst):** Demuestra capacidad de modelado DAX y dashboards ejecutivos en el estándar empresarial europeo (~165 €).
   - **SQL Avanzado & Python for Data Science:** Cursos especializados en plataformas como Coursera o Datacamp (~200 €).
2. **Construcción de un Portfolio en GitHub y Power BI Service:**
   - Desarrolla 3 proyectos completos de análisis con datos reales de e-commerce o logística: desde la extracción con SQL, limpieza con Pandas hasta el cuadro de mando final.
   - Enlace directo a tu portfolio interactivo en la cabecera de tu LinkedIn. Tendrás contrataciones en menos de 6 meses ahorrándote más de 13.000 €."""
    },
    {
        "user": "Quiero abrir un negocio de comida asiática rápida (noodles y baos). Tengo dos opciones de local: un establecimiento de 110 m² con licencia de restaurante a pie de calle en zona peatonal céntrica (alquiler de 3.200 €/mes + 40.000 € de traspaso), o una dark kitchen de 35 m² en un polígono cercano a la ciudad especializada solo en delivery (alquiler de 850 €/mes y cero traspaso). ¿Qué modelo minimiza riesgos?",
        "think": "Contexto: Emprendimiento gastronómico comparando local comercial céntrico con traspaso vs dark kitchen de delivery.\nEvaluación: Delivery exclusivo depende de comisiones del 30% de plataformas; local céntrico ofrece venta directa de alto margen.\nConclusión: Local céntrico con menú optimizado para llevar y consumo rápido en sala.",
        "assistant": """Para un concepto de comida rápida como noodles y baos, **el local a pie de calle en zona peatonal ofrece un modelo de negocio mucho más resiliente y rentable a medio plazo**:

### 1. La Trampa de las Dark Kitchens
- Una dark kitchen depende al 100% de los algoritmos de plataformas como Glovo o UberEats, que cobran entre un **25% y un 35% de comisión sobre cada pedido**.
- Como no tienes escaparate a pie de calle ni tránsito de peatones, debes gastar miles de euros mensuales en publicidad digital y promociones en la app para que los clientes te descubran. Si la plataforma sube tarifas o modifica el algoritmo, tu facturación puede desplomarse de la noche a la mañana.

### 2. La Fortaleza del Local Céntrico Peatonal
- Los noodles y baos son productos de impulso y consumo rápido con márgenes brutos excelentes (>70%).
- El flujo peatonal diario es tu principal canal de captación gratuito. Puedes combinar tres fuentes de ingresos simultáneas: **consumo rápido en barra, recogida en local (take away) sin comisiones a terceros, y delivery complementario**.
- Los 3.200 € de alquiler quedan rápidamente amortizados con la venta directa al público de oficinas y jóvenes en horario de almuerzo y cena."""
    },
    {
        "user": "Nuestra consultora de software (25 empleados) estudia implantar la semana laboral de 4 días (32 horas) manteniendo el 100% del salario. Los socios temen una caída proporcional del 20% en la facturación facturable. ¿Es viable implantarla y bajo qué condiciones?",
        "think": "Contexto: Consultora tecnológica evaluando semana de 4 días y 32h sin reducción salarial.\nEvaluación: Mantener procesos antiguos con menos horas baja entregas; recortar reuniones y automatizar recupera la productividad.\nConclusión: Prueba piloto de 6 meses condicionada a métricas de entrega y eliminación de tiempos muertos.",
        "assistant": """La semana de 4 días es perfectamente viable en consultoría de software, pero **solo si se rediseña radicalmente la forma de trabajar**. No se trata de hacer lo mismo en menos tiempo, sino de eliminar las ineficiencias crónicas:

### 1. Cómo Mantener la Facturación sin Caídas
- Los estudios demuestran que los desarrolladores solo pasan entre 2,5 y 3 horas al día en concentración profunda (*Deep Work*); el resto se diluye en reuniones redundantes, cambios de contexto y mensajes en Slack.
- **Protocolo de choque previo:**
  - Prohibición de reuniones internas los lunes y viernes.
  - Reducción del tiempo estándar de las reuniones a 25 minutos con orden del día obligatorio.
  - Comunicación asíncrona por defecto para actualizaciones de estado.

### 2. Diseño del Plan Piloto Seguro (6 Meses)
1. **Pacto de productividad mutuo:** Se establece una prueba reversible de 6 meses donde la plantilla se compromete a mantener los hitos y entregas acordadas con los clientes.
2. **Rotación para cobertura de soporte:** Divide al equipo en dos turnos (unos descansan el viernes y otros el lunes) para garantizar atención ininterrumpida a los clientes los 5 días hábiles de la semana.
3. **Métricas de éxito:** Si al cabo de 6 meses la satisfacción de clientes y los sprints completados se mantienen estables, la política se consolida definitivamente, convirtiéndoos en un imán para captar el mejor talento del sector."""
    },
    {
        "user": "Nuestra empresa opera una plataforma transaccional con servidores físicos propios en un centro de datos en régimen de colocation (coste: 2.100 €/mes entre rack y enlaces). Los servidores tienen 5 años y exigen una renovación de hardware de 45.000 €. El equipo técnico propone migrar al 100% a la nube pública (AWS/GCP), pero las cotizaciones estiman unos 3.400 €/mes. ¿Renovamos el hardware o migramos a cloud?",
        "think": "Contexto: Infraestructura física amortizada de 5 años evaluando renovación de 45k € vs migración a nube a 3.400 €/mes.\nEvaluación: Cargas de trabajo predecibles y estables son mucho más económicas en hardware propio que en cloud pública.\nConclusión: Renovar hardware en colocation adoptando virtualización moderna para amortizar a 5 años.",
        "assistant": """Si vuestra carga transaccional es **predecible, constante y no sufre picos estacionales extremos del 500%**, la decisión más rentable es **renovar el hardware en colocation**:

### 1. Análisis Financiero a 5 Años

| Modelo | Inversión Inicial (CapEx) | Coste Mensual (OpEx) | Coste Total a 5 Años (60 Meses) |
| :--- | :--- | :--- | :--- |
| **Renovación Servidores Propios** | 45.000 € (Amortizable) | 2.100 €/mes (Colocation) | **171.000 €** |
| **Migración 100% Cloud (AWS/GCP)** | ~10.000 € (Migración) | 3.400 €/mes base + tráfico | **~214.000 € a 240.000 €** |

- En la nube pública se paga un sobreprecio elevado por la flexibilidad y la elasticidad horaria. Si tenéis servidores corriendo 24/7 al 60% de capacidad fija, la nube siempre resulta significativamente más cara debido a los costes no computados de transferencia de salida de datos (egress data fees) y almacenamiento persistente.

### 2. Estrategia Híbrida Recomendada
- Adquirid los nuevos servidores en rack utilizando virtualizadores modernos (Proxmox VE o VMware) para optimizar recursos.
- Utilizad la nube pública exclusivamente como respaldo secundario para copias de seguridad remotas en almacenamiento frío (S3 Glacier) y entorno de recuperación ante desastres."""
    },
    {
        "user": "Tenemos una idea de producto digital para gestión de citas médicas. Llevamos 3 meses desarrollando y la funcionalidad principal de reservas funciona bien, pero faltan módulos secundarios (historial clínico, facturación automática, recordatorios WhatsApp). El equipo de diseño pide 2 meses más para pulir la UX. ¿Lanzamos el MVP ya o esperamos?",
        "think": "Contexto: Producto digital de reservas médicas con funcionalidad core lista dudando entre lanzar o posponer 2 meses.\nEvaluación: Retrasar el lanzamiento retrasa la validación real con usuarios; los módulos secundarios pueden ser innecesarios.\nConclusión: Lanzar el MVP de inmediato con la funcionalidad core de reservas y captar feedback directo.",
        "assistant": """**Debéis lanzar el MVP inmediatamente**. Posponer el lanzamiento dos meses más para perfeccionar funcionalidades secundarias es el error más recurrente y destructivo en el desarrollo de software:

### 1. La Regla del Producto Mínimo Viable
- El objetivo de un MVP no es impresionar al mercado con un producto acabado, sino **validar la hipótesis central de negocio**: ¿están las clínicas dispuestas a gestionar sus citas con vuestra herramienta?
- Si los médicos o recepcionistas no utilizan vuestro sistema de reservas, de nada servirá haber dedicado dos meses a programar la facturación o la integración con WhatsApp.

### 2. El Peligro del Perfeccionismo sin Usuarios Reales
- La interfaz perfecta no existe hasta que choca con usuarios reales. Al poner el producto en manos de 5 clínicas piloto la próxima semana:
  - Descubriréis qué botones no entienden en menos de 48 horas.
  - Sabréis qué módulos secundarios necesitan con urgencia real y cuáles de vuestras ideas preconcebidas no les interesaban en absoluto.
- Abrid acceso a las primeras clínicas ofreciéndoles un precio promocional vitalicio a cambio de su feedback semanal."""
    },
    {
        "user": "Tengo que contratar un seguro de salud privado familiar (2 adultos y 1 bebé). Nos ofrecen dos modalidades en la misma aseguradora: póliza sin copago por 175 €/mes, o póliza con copago de 5 € por consulta de especialista y 10 € por urgencia médica por 115 €/mes. Históricamente vamos al médico unas 6-8 veces al año en total. ¿Qué opción es más conveniente?",
        "think": "Contexto: Elección de seguro de salud familiar comparando opción sin copago (175 €) vs con copago (115 €).\nEvaluación: La diferencia es de 60 €/mes (720 €/año); con 8 visitas anuales el copago no superará los 70 €.\nConclusión: Elegir póliza con copago ahorrando más de 650 € netos al año.",
        "assistant": """Para vuestro perfil de uso familiar habitual, la **modalidad con copago (115 €/mes)** es con diferencia la opción financieramente más inteligente:

### 1. Las Matemáticas del Seguro
- **Diferencia de prima fija:** 175 € - 115 € = **60 € de ahorro al mes (720 € al año garantizados)**.
- **Simulación con vuestro consumo estimado (incluso duplicándolo por el bebé):**
  - Revisiones pediátricas y especialistas: 10 visitas al año x 5 € = 50 €.
  - 2 visitas a urgencias al año x 10 € = 20 €.
  - Gasto total anual en copagos: **~70 € al año**.
- **Ahorro neto para la familia:** 720 € - 70 € = **~650 € limpios de ahorro al año en vuestro bolsillo**.

### 2. Tranquilidad ante Imprevistos Graves
- La póliza con copago ofrece exactamente las **mismas coberturas hospitalarias, quirúrgicas y tratamientos oncológicos** que la póliza sin copago. En caso de hospitalización o cirugía mayor, los copagos no aplican o tienen un tope máximo anual fijado por ley. Estáis 100% protegidos ahorrando más de 50 € cada mes."""
    },
    {
        "user": "Nuestra plataforma web principal está construida sobre un monolito legado de PHP 7.1 con 8 años de parches y deuda técnica severa. Añadir funcionalidades nuevas es lento y frustrante. La dirección técnica debate entre paralizar desarrollos nuevos durante 6 meses para reescribir todo desde cero en Go/Node, o adoptar un patrón de estrangulamiento gradual (Strangler Fig). ¿Qué camino reduce el riesgo de fracaso?",
        "think": "Contexto: Monolito de PHP legado con deuda técnica debatiendo entre reescritura total vs patrón Strangler Fig.\nEvaluación: Las reescrituras desde cero casi siempre superan plazos y fallan en reproducir casos esquina.\nConclusión: Aplicar el patrón Strangler Fig migrando endpoints detrás de un API Gateway.",
        "assistant": """En ingeniería de software existe una lección histórica bien documentada: **las reescrituras totales desde cero (Greenfield) fracasan o duplican sus plazos en más del 80% de las ocasiones**. La elección inequívoca es el **patrón Strangler Fig (Migración por Estrangulamiento)**:

### 1. Por qué la Reescritura desde Cero es una Trampa
- El monolito de 8 años contiene cientos de reglas de negocio tácitas, correcciones de casos límite (*edge cases*) y adaptaciones fiscales que nadie documentó. Replicarlas todas desde cero en un proyecto paralelo es prácticamente imposible.
- Paralizar el desarrollo de negocio durante 6 meses (que en la realidad siempre se convierten en 12 o 15 meses) deja a vuestra empresa vulnerable mientras la competencia sigue lanzando novedades al mercado.

### 2. Cómo Implementar el Patrón Strangler Fig con Cero Riesgo
1. **Colocar un API Gateway o Proxy Inverso (Nginx/Traefik) al frente:** Todas las peticiones de los usuarios entran por el proxy y se dirigen por defecto al viejo monolito de PHP.
2. **Extraer un primer dominio acotado y de bajo riesgo:** Implementa en la nueva tecnología (ej. Go o Node) un módulo aislado, como el servicio de notificaciones o el catálogo de lectura.
3. **Reenrutar el tráfico en el Gateway:** Configura el proxy para que las rutas de ese módulo específico se desvíen al nuevo servicio sin que el usuario note ningún cambio.
4. **Migración progresiva:** El monolito va reduciéndose paso a paso mientras el negocio continúa operando y generando ingresos."""
    },
    {
        "user": "Soy consultor independiente de ciberseguridad. Actualmente cobro mis servicios a 70 €/hora, pero los clientes regatean los partes horarios y me siento atrapado en un techo de ingresos lineal. ¿Me conviene pasar a cobrar por precio cerrado por hito o por valor aportado (Value-Based Pricing)? ¿Cómo ejecutar la transición?",
        "think": "Contexto: Consultor de ciberseguridad cobrando por horas con techo salarial y conflicto de partes de tiempo.\nEvaluación: Cobrar por hora penaliza la experiencia y rapidez; pricing por valor alinea incentivos con el cliente.\nConclusión: Transicionar a presupuestos cerrados basados en valor y auditorías paquetizadas.",
        "assistant": """Cobrar por horas penaliza directamente tu pericia: cuanto más rápido y eficiente resuelves un problema de seguridad, menos dinero ganas. **Debes transicionar a precios basados en valor aportado y paquetes cerrados**:

### 1. La Incoherencia de la Tarifa Horaria
- A un cliente no le interesa cuántas horas tardas en auditar su red; le interesa tener la certeza de que no sufrirá un secuestro por ransomware que paralice su fábrica con pérdidas de 200.000 €.
- Al presupuestar por horas, sitúas la conversación en el esfuerzo de trabajo en lugar de en el impacto económico de tu intervención.

### 2. Estrategia de Paquetización por Valor
1. **Paquetes estandarizados de entrada:**
   - En lugar de *"auditoría a 70 €/hora"*, vende un *"Diagnóstico de Vulnerabilidades Perimetrales y Cumplimiento Normativo"* cerrado a **2.800 €**. Si gracias a tus scripts automatizados lo ejecutas en 12 horas, tu tarifa efectiva sube a más de 230 €/hora sin que el cliente pestañee.
2. **Propuestas basadas en valor para proyectos complejos:**
   - Si una empresa te contrata para blindar su pasarela de pagos antes de salir a bolsa, una tarifa de **15.000 € cerrados** resulta económica para un riesgo corporativo millonario.
3. **Retainers mensuales de monitorización:** Ofrece acompañamiento preventivo continuo por una cuota fija de 1.200 €/mes para generar ingresos predecibles."""
    },
    {
        "user": "Somos dos socios cofundadores de una empresa de base tecnológica de analítica para el sector agrario. Necesitamos 75.000 € para comprar maquinaria de sensores y contratar a un agrónomo. Tenemos dos alternativas: ceder el 22% del capital a un inversor privado local que no aporta contactos sectoriales, o solicitar un préstamo participativo ENISA Jóvenes Emprendedores sin avales personales a 5 años con 1 año de carencia. ¿Cuál es la mejor opción de financiación?",
        "think": "Contexto: Startup agrotech necesitando 75.000 € debatiendo entre ceder el 22% a inversor o préstamo ENISA.\nEvaluación: Ceder el 22% por 75k valora la empresa en solo 340k sin aportar smart money; ENISA no diluye.\nConclusión: Solicitar préstamo ENISA preservando el capital y la gobernanza de los socios.",
        "assistant": """Para obtener 75.000 € en vuestra fase, **la opción inequívoca es el préstamo participativo ENISA Jóvenes Emprendedores**:

### 1. La Destrucción de Valor de Ceder el 22%
- Vender el 22% de vuestra empresa por solo 75.000 € implica aceptar una valoración post-money de apenas **340.000 €**.
- En fases tempranas, perder un 22% con un inversor que no aporta contactos estratégicos ni valor añadido (*dumb money*) hipoteca futuras rondas de financiación: los fondos de capital riesgo exigen que los fundadores conserven el control mayoritario del capital.

### 2. Por qué ENISA es la Financiación Estrella
- **Sin dilución de capital:** No entregáis ni una sola acción; el 100% de la empresa sigue en vuestras manos.
- **Sin avales personales ni hipotecas:** A diferencia del crédito bancario tradicional, la garantía es el propio proyecto empresarial. Si el negocio quiebra, no respondes con tu patrimonio personal ni el de tu familia.
- **Condiciones inmejorables:** Ofrece 1 año de carencia total (no pagas cuota de amortización durante 12 meses) y amortización a 5 años a un tipo de interés competitivo ligado a resultados. Solicita ENISA y conserva el control de tu empresa."""
    }
]
