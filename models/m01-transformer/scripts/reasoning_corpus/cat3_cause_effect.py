"""
Categoría 3: Análisis causa-efecto y diagnósticos empíricos (20 escenarios)
Bloques <think> concisos de 30-80 tokens de retrospectiva contextual e hipótesis sintética.
"""

SCENARIOS_CAT3 = [
    {
        "user": "Tras rediseñar nuestra web corporativa hace 3 semanas, el tráfico orgánico de Google ha caído un 45%. Mantuvimos las mismas URLs en casi todas las páginas y la web carga más rápido. Search Console muestra una pérdida generalizada de posiciones. ¿Cuál puede ser la causa raíz y cómo diagnosticarla?",
        "think": "Contexto: Caída del 45% en tráfico orgánico tras rediseño web con URLs estables.\nEvaluación: Pérdida involuntaria de encabezados H1/H2, etiquetas canonical incorrectas o bloqueo en robots.txt/noindex.\nConclusión: Auditar indexación en Search Console y comparar HTML renderizado pre/post rediseño.",
        "assistant": """Una caída del 45% tras un rediseño que conservó las URLs suele deberse a problemas de **renderizado del contenido o modificaciones críticas en metadatos y enlaces internos**. Aplica este diagnóstico sistemático:

### 1. Comprobación Inmediata de Indexación en Search Console
- **Revisa la sección 'Páginas / Cobertura':** Comprueba si se ha disparado el número de páginas *"Rastreadas: actualmente sin indexar"* o *"Excluidas por etiqueta noindex"*.
- **Inspección de URLs clave:** Pasa la URL principal y las 5 categorías más importantes por la herramienta de inspección de URL en vivo y revisa el **HTML renderizado**:
  - Si el nuevo diseño se construyó con un framework SPA (React/Vue) sin Server-Side Rendering (SSR), el bot de Google puede estar viendo una página en blanco sin el texto de los artículos.

### 2. Causas Raíz Más Frecuentes en Rediseños
1. **Destrucción de Enlazado Interno (Arquitectura de Silos):** Al simplificar el menú de navegación o el pie de página, muchas URLs profundas que antes recibían autoridad (*PageRank interno*) quedan ahora a más de 4 clics de la portada.
2. **Eliminación o Dilución de Contenido Textual:** A menudo los rediseños modernos reducen texto para hacerlo "más visual", eliminando encabezados `<h1>` y `<h2>` y párrafos descriptivos ricos en palabras clave semánticas.
3. **Etiquetas Canónicas (Canonical Tags) Mal Apuntadas:** Verifica que las etiquetas `<link rel="canonical">` no estén apuntando todas a la home o a URLs con protocolo HTTP o subdominios de pruebas (staging).
4. **Residuos de Staging:** Comprueba que en la cabecera HTTP no haya quedado activa la directiva `X-Robots-Tag: noindex` introducida en el entorno de desarrollo."""
    },
    {
        "user": "En los últimos 6 meses, 5 de los 8 técnicos del departamento de soporte y QA han presentado su baja voluntaria en nuestra empresa de software. La dirección cree que se debe únicamente a que las empresas competidoras pagan un 10% más de salario. ¿Cómo diagnosticar si el salario es la causa real o síntoma de problemas organizativos más profundos?",
        "think": "Contexto: Pérdida del 60% de la plantilla técnica en soporte y QA en un semestre.\nEvaluación: El salario suele ser detonante superficial; la sobrecarga y falta de progresión provocan el éxodo.\nConclusión: Ejecutar entrevistas de salida neutrales y auditar volumen de horas extras y bloqueos de producto.",
        "assistant": """Atribuir una fuga del 60% del equipo exclusivamente a una brecha salarial del 10% es un sesgo directivo habitual para eludir responsabilidades de gestión. En roles de QA y soporte, el abandono masivo responde casi siempre a **agotamiento operativo (burnout) y falta de reconocimiento**:

### 1. Indicadores Operativos a Auditar
- **Volumen de tickets por persona y deuda técnica:** Si el equipo de desarrollo lanza versiones con bugs recurrentes que soporte debe amortiguar cara al cliente sin herramientas para solucionarlos, la frustración psicológica es insoportable.
- **Horas extras encubiertas y guardias no compensadas:** Revisa las horas reales de trabajo: ¿estaban respondiendo incidencias fuera de horario por WhatsApp o guardias de fin de semana mal remuneradas?
- **Techo de carrera inexistente:** ¿Se percibe a QA y soporte como un "callejón sin salida" en la empresa, sin posibilidad de promocionar a desarrollo, producto o gestión técnica?

### 2. Protocolo de Diagnóstico Objetivo
1. **Entrevistas de salida anónimas o externalizadas:** Las entrevistas hechas por Recursos Humanos a menudo recogen la respuesta diplomática *"me voy por más dinero"* para no quemar puentes. Utiliza un mediador neutral o un formulario anónimo post-salida enfocado en cultura y liderazgo.
2. **Entrevistas de retención (*Stay Interviews*) con los 3 técnicos que se quedan:** Pregúntales directamente: *"¿Qué es lo que más te frustra en tu día a día?"* y *"¿Qué cambiarías mañana para trabajar con tranquilidad?"*.
3. **Acción correctora:** Si la causa es la carga de bugs, involucra a desarrollo en guardias rotativas para alinear la calidad del código con la experiencia de soporte."""
    },
    {
        "user": "Tengo una cafetera espresso manual en casa. Utilizo café de especialidad recién tostado y molido en el momento, pero el café sale excesivamente amargo, astringente, deja la lengua seca y apenas tiene crema. ¿Qué variables de extracción están fallando y cómo corregirlas?",
        "think": "Contexto: Extracción de espresso amargo, astringente y seco en cafetera doméstica.\nEvaluación: Amargor y sequedad son síntomas clásicos de sobreextracción o canalización por molido irregular.\nConclusión: Engrosar punto de molido, reducir ratio y verificar temperatura del agua a 92 °C.",
        "assistant": """El sabor amargo, la astringencia y la sequedad en boca son los síntomas universales de la **sobreextracción**: el agua ha disuelto los compuestos pesados y desagradables del grano que solo deben salir al final. Aplica estos ajustes en orden:

### 1. Variables Físicas de la Extracción
1. **Punto de Molido Demasiado Fino:**
   - Si las partículas son microscópicas, el agua tarda demasiado en atravesar la pastilla o fluye a través de micro-grietas creadas por la presión (*channeling*).
   - **Corrección:** Engrosa ligeramente el molido (1 o 2 puntos en tu molino).
2. **Tiempo de Extracción Prolongado:**
   - Para un espresso doble estándar (ratio 1:2, ej. 18 g de café molido para obtener 36 g de bebida líquida en taza), el tiempo de extracción debe oscilar entre **25 y 30 segundos**.
   - Si tu extracción tarda más de 35 segundos, estás sobreextrayendo.
3. **Temperatura Excesiva del Agua:**
   - El agua por encima de 94 °C quema los aceites aromáticos del café y potencia los fenoles amargos. Purga un poco de agua caliente por el grupo antes de encajar el portafiltros para estabilizar la temperatura en unos **91 °C - 93 °C**.

### 2. Técnica de Prensado (Distribución en Portafiltro)
- Si el agua genera canalizaciones (*channeling*), una parte del café queda sin extraer y otra completamente achicharrada, dando amargor sin crema.
- Utiliza una herramienta de agujas finas (WDT) para desarmar grumos de café en la cesta antes de prensar de manera completamente horizontal y uniforme."""
    },
    {
        "user": "Al acelerar con mi coche de gasolina subiendo pendientes o al pisar a fondo en marchas largas a bajas revoluciones, se escucha un tintineo metálico agudo en el vano motor (como canicas chocando). Al soltar ligeramente el pedal del acelerador el ruido desaparece. ¿A qué se debe y qué riesgo tiene?",
        "think": "Contexto: Ruido metálico de canicas en motor gasolina bajo carga a bajas RPM.\nEvaluación: Síntoma de detonación prematura o picado de bielas por octanaje bajo o carbonilla.\nConclusión: Usar gasolina de mayor octanaje y revisar sensor de picado y bujías de inmediato.",
        "assistant": """Ese tintineo metálico característico es **detonación prematura o picado de bielas (*engine knock*)**: una anomalía de combustión extremadamente destructiva que debes corregir de inmediato.

### 1. Explicación Mecánica del Fenómeno
- En condiciones normales, la bujía genera una chispa controlada que crea un frente de llama que empuja suavemente el pistón.
- Al acelerar a fondo en marchas largas a bajas revoluciones (alta carga de motor), la mezcla de aire y combustible se calienta tanto en la cámara de combustión que **autoigniciona espontáneamente antes de tiempo**.
- La explosión choca violentamente contra la cabeza del pistón mientras este aún está subiendo, provocando ondas de choque que hacen resonar los componentes mecánicos con ese sonido de canicas.

### 2. Causas Frecuentes
1. **Combustible con Octanaje Insuficiente:** Si el motor tiene alta compresión o turbo y se le echa gasolina de 95 octanos de baja calidad, el combustible detona por compresión.
2. **Acumulación de Carbonilla en la Cámara:** La carbonilla en las válvulas y pistones forma puntos incandescentes que actúan como bujías calientes encendiendo la mezcla antes de tiempo.
3. **Fallo en el Sensor de Picado (*Knock Sensor*) o Avance de Encendido:** El sensor no está retrasando el encendido automáticamente al detectar la presión.
4. **Bujías Incorrectas o de Grado Térmico Inadecuado.**

### 3. Plan de Acción Urgente
- **Prueba inmediata:** Llena el depósito con **gasolina de 98 octanos**. Si el ruido desaparece, confirma que el octanaje o la carbonilla estaban provocando la detonación.
- **Visita al taller:** Si el picado persiste, el pistón puede perforarse o romperse un segmento en cuestión de semanas."""
    },
    {
        "user": "Tengo un limonero plantado en una maceta grande en mi terraza. En las últimas semanas las hojas nuevas nacen de color amarillo pálido, pero los nervios de las hojas se mantienen de color verde oscuro intenso. ¿Qué deficiencia o problema de riego sufre la planta?",
        "think": "Contexto: Hojas jóvenes amarillas con nervaduras verdes en limonero en maceta.\nEvaluación: Síntoma patognomónico de clorosis férrica provocada por bloqueo de hierro o pH alcalino.\nConclusión: Aplicar quelato de hierro EDDHA y regular el pH del agua de riego.",
        "assistant": """El patrón visual que describes (hojas jóvenes amarillas con las nervaduras perfectamente verdes) es el síntoma inequívoco de **clorosis férrica (deficiencia de hierro)** en los cítricos:

### 1. Por qué Ocurre en Maceta
El hierro es imprescindible para que la planta sintetice la clorofila. Aunque la tierra contenga hierro, el limonero no puede absorberlo por dos motivos habituales:
1. **Agua de Riego Dura / Alcalina (Exceso de Cal):** Regar con agua del grifo rica en cal eleva progresivamente el pH del sustrato por encima de 7,5. En suelos alcalinos, el hierro precipita en forma insoluble que las raíces no pueden captar.
2. **Exceso de Humedad o Asfixia Radicular:** Si el drenaje de la maceta es deficiente, las raíces carecen de oxígeno y pierden la capacidad de bombear nutrientes.

### 2. Tratamiento de Choque Inmediato
- **Aplicar Quelato de Hierro (EDDHA):**
  - No compres sulfato de hierro simple: en tierras alcalinas no funciona.
  - Adquiere **quelato de hierro con agente quelante EDDHA** (polvo granular rojo oscuro soluble en agua). El quelato protege la molécula de hierro para que sea absorbible incluso en aguas muy calcáreas.
  - Disuelve 5 g en una regadera con agua y aplícalo directamente sobre la tierra húmeda al atardecer.

### 3. Mantenimiento Preventivo
- **Acidificar el agua de riego:** Añade unas gotas de vinagre o ácido cítrico al agua del grifo antes de regar (el pH ideal para el limonero es de 6,0 a 6,5).
- Comprueba que el agujero inferior de la maceta drene con soltura sin platos con agua estancada bajo la base."""
    },
    {
        "user": "Hemos rediseñado la pantalla de pago (checkout) de nuestro e-commerce y la tasa de abandono en el último paso se ha disparado del 42% al 74%. En las grabaciones de sesión en Hotjar vemos usuarios que hacen clics repetidos en el botón de pagar pero la página no avanza. ¿Cómo aislar la causa técnica?",
        "think": "Contexto: Aumento drástico de abandono en checkout con clics de frustración en botón de pago.\nEvaluación: Errores silenciosos de JavaScript en validación de campos o bloqueo en el iframe de la pasarela.\nConclusión: Revisar consola de errores JS, verificar eventos en red HTTP y depurar campos ocultos obligatorios.",
        "assistant": """Los clics repetitivos en un botón sin respuesta visual (*rage clicks*) evidencian un **fallo técnico en el cliente (JavaScript) o un error de validación silencioso**:

### 1. Diagnóstico Técnico en 3 Pasos
1. **Auditar Errores en la Consola de JavaScript:**
   - Abre la herramienta de desarrollo del navegador (F12) en la pestaña *Console* y realiza una compra de prueba.
   - Si aparece un error tipo `Uncaught TypeError: Cannot read properties of undefined` al pulsar el botón, el script de la pasarela (Stripe, Redsys, PayPal) se rompe antes de enviar la petición.
2. **Inspección de la Pestaña de Red (Network):**
   - Pulsa el botón de pago y observa si se genera alguna petición HTTP:
     - Si **no sale ninguna petición**: el formulario no se envía porque una validación HTML5 en un campo oculto (ej. un campo de código postal o provincia no visible en móviles) está bloqueando el submit sin mostrar mensaje de error.
     - Si sale la petición y devuelve un código **400 Bad Request o 422 Unprocessable Entity**: el backend está rechazando los datos formateados del nuevo formulario.
3. **Prueba de Compatibilidad en Dispositivos Reales:**
   - El 80% de estos bloqueos ocurren en navegadores móviles específicos (Safari en iOS o navegadores integrados de Instagram/TikTok) donde el iframe de la tarjeta de crédito no carga por restricciones de cookies de terceros o políticas CSP (*Content Security Policy*).

### 2. Solución Inmediata
- Corrige la validación para que cualquier campo requerido erróneo se resalte en rojo con scroll automático y mensaje visible.
- Añade un estado de carga (*spinner*) en el botón de compra para impedir pulsaciones duplicadas."""
    },
    {
        "user": "Al conectar mi ordenador portátil mediante un único cable USB-C a un monitor externo 4K con soporte de carga Power Delivery (65W), el portátil se apaga de golpe al cabo de unos minutos si abro un programa pesado de edición de vídeo. Con su cargador original de pared nunca se apaga. ¿Cuál es el problema?",
        "think": "Contexto: Portátil se apaga bajo carga pesada alimentado por USB-C Power Delivery de 65W.\nEvaluación: El monitor suministra 65W pero la GPU/CPU combinadas exigen más potencia, drenando y protegiendo el circuito.\nConclusión: Déficit de potencia eléctrica que activa la protección térmica o por subvoltaje de la batería.",
        "assistant": """El apagado repentino se debe a un **déficit severo de suministro eléctrico que activa la protección de sobrecorriente o subvoltaje del portátil**:

### 1. El Déficit Energético de los 65W
- Tu monitor suministra un máximo de **65W mediante USB-C Power Delivery**.
- En reposo o navegación web ligera, un portátil moderno consume entre 15W y 30W, por lo que el monitor alimenta y carga el equipo sin problema.
- Sin embargo, al renderizar vídeo, **la CPU y la tarjeta gráfica dedicada (GPU) se activan a máxima potencia, exigiendo entre 85W y 130W combinados** (por eso su cargador original de fábrica tiene mayor potencia).

### 2. Por qué se Apaga en Lugar de Funcionar más Lento
1. **Caída del circuito de batería híbrida:** Cuando la demanda (100W) supera lo que entrega el cable USB-C (65W), el portátil toma los 35W restantes de la batería interna.
2. **Activación de la protección:** Si la batería no puede compensar el pico instantáneo de amperaje con la velocidad requerida, o si la línea de 20V del puerto USB-C del monitor experimenta una caída de voltaje (*voltage drop*) por calentamiento del controlador del monitor, la placa base del portátil corta la energía en milisegundos para evitar quemar los MOSFETs.

### 3. Solución Definitiva
- **Conecta el cargador original del portátil a la corriente simultáneamente:** El portátil tomará la energía principal del cargador nativo de alta potencia y utilizará el cable USB-C exclusivamente para transferir la señal de vídeo al monitor 4K."""
    },
    {
        "user": "Durante el cierre contable de fin de mes, nuestra base de datos PostgreSQL experimenta decenas de errores 'deadlock detected' en la tabla de facturación y saldos de clientes, abortando procesos batch y transacciones de clientes. ¿Cuál es la causa arquitectónica de estos bloqueos mutuos y cómo erradicarlos?",
        "think": "Contexto: Bloqueos mutuos (deadlocks) recurrentes en PostgreSQL durante transacciones masivas de cierre.\nEvaluación: Procesos concurrentes adquieren bloqueos de fila o tabla en orden inverso.\nConclusión: Estandarizar el orden estricto de actualización por clave primaria en todas las transacciones.",
        "assistant": """Los bloqueos mutuos (*deadlocks*) en PostgreSQL no ocurren por falta de recursos de hardware, sino por un fallo en la **concurrencia de la lógica de negocio: transacciones concurrentes adquieren bloqueos en orden inconsistente**:

### 1. Cómo se Genera el Deadlock
- **Transacción A (Proceso Batch de Cierre):** Bloquea la fila del Cliente 101 y a continuación intenta actualizar la del Cliente 202.
- **Transacción B (Pago puntual de cliente):** Bloquea concurrentemente la fila del Cliente 202 y a continuación intenta actualizar la del Cliente 101.
- Ambas transacciones quedan congeladas esperando mutuamente a que la otra libere el recurso. Tras alcanzar el parámetro `deadlock_timeout` (por defecto 1 segundo), PostgreSQL interviene matando y revirtiendo una de las dos con el error *deadlock detected*.

### 2. La Regla de Oro para Eliminarlos: Ordenación Determinista
Cualquier proceso que actualice múltiples registros debe **ordenar las filas por su identificador primario antes de tocarlas**:
- Si tanto el proceso batch como las transacciones individuales bloquean los registros siempre en orden ascendente (`ORDER BY id ASC`), la Transacción B esperará pacientemente en cola detrás de la Transacción A, eliminando la posibilidad física de un abrazo mortal.

```sql
-- En tus sentencias de actualización en lote o bloqueos previos:
SELECT id FROM clientes 
WHERE id IN (101, 202, 305) 
ORDER BY id ASC 
FOR UPDATE;
```

### 3. Medidas Complementarias
- **Transacciones Cortas:** No mantengas transacciones abiertas mientras ejecutas peticiones HTTP a pasarelas de pago o generas informes pesados. Abre la transacción, actualiza las filas y haz `COMMIT` de inmediato.
- **Desacoplar Reportes Pesados:** Las consultas de reporting contable deben ejecutarse con nivel de aislamiento de lectura o directamente sobre una réplica de solo lectura."""
    },
    {
        "user": "La conexión Wi-Fi de mi casa funciona con 300 Mbps en el salón y despacho durante todo el día, pero a partir de las 22:00 la velocidad cae a menos de 5 Mbps y sufre microcortes constantes exclusivamente en el dormitorio principal. ¿Qué puede estar provocando esta anomalía nocturna?",
        "think": "Contexto: Caída nocturna de velocidad Wi-Fi exclusiva en el dormitorio a partir de las 22:00.\nEvaluación: Saturación de canal Wi-Fi por vecinos o interferencias electromagnéticas de electrodomésticos.\nConclusión: Escanear frecuencias de 2.4/5 GHz y cambiar a canal limpio o instalar punto de acceso cableado.",
        "assistant": """Una degradación que ocurre **siempre a la misma hora y en una estancia concreta** no es una avería del router, sino una interferencia externa periódica:

### 1. Hipótesis Causales Principales
1. **Saturación del Canal Wi-Fi en 2.4 GHz por Vecinos:**
   - La banda de 2.4 GHz solo tiene 3 canales que no se solapan (1, 6 y 11). A las 22:00 la densidad de uso en el edificio alcanza su punto álgido (vecinos viendo streaming en dormitorios contiguos a tu pared). La colisión de paquetes destruye el rendimiento.
2. **Interferencia Electromagnética en la Pared del Dormitorio:**
   - ¿Hay al otro lado de la pared del dormitorio un electrodoméstico que se active por la noche (termo eléctrico temporizado, radiador eléctrico, base de carga inalámbrica de mala calidad o vigilabebés)? Los motores y transformadores generan ruido electromagnético que bloquea la radiofrecuencia.
3. **Atenuación Física por Puertas Cerradas:**
   - Si cierras las puertas del pasillo al acostarte, la señal de alta frecuencia (5 GHz) no atraviesa tabiques macizos con facilidad.

### 2. Protocolo de Diagnóstico y Solución
- **Descarga una app analizadora de Wi-Fi (como WiFi Analyzer en Android o inSSIDer en PC):** Sitúate en el dormitorio a las 22:15 y escanea qué canales están saturados.
- **Separar bandas (SSID dedicado):** Configura en el router dos redes separadas: `MiRed_2.4G` y `MiRed_5G`. Conecta tu móvil del dormitorio a la banda de **5 GHz** (mucho más inmune a interferencias vecinales).
- **Fijar canal manual:** Si el router está en canal automático, cambia manualmente a un canal poco congestionado."""
    },
    {
        "user": "Llevo tres intentos haciendo pan casero con masa madre natural. La masa fermenta bien en el primer levado (dobla su volumen en 4 horas), pero tras formar el pan y ponerlo en el banneton para la segunda fermentación, la masa se aplana, pierde tensión, no sube y al meterla al horno queda densa y sin greña. ¿Qué estoy haciendo mal?",
        "think": "Contexto: Masa de pan de masa madre se desinfla y pierde tensión en la segunda fermentación.\nEvaluación: Sobrefermentación enzimática que degrada la red de gluten o falta de tensión en el formado.\nConclusión: Reducir tiempo de segunda fermentación y meter al horno cuando aún conserve elasticidad.",
        "assistant": """El colapso de la masa en la segunda fermentación es el síntoma clásico de la **sobrefermentación (la masa se ha pasado de punto)**:

### 1. Mecanismo Físico del Colapso
- Durante la fermentación, las levaduras producen gas carbónico y las bacterias ácidas y enzimas (*proteasas*) degradan las cadenas de gluten.
- Si la fermentación se prolonga demasiado tiempo, la acidez excesiva **destruye la malla elástica de gluten**. El gas atrapado ya no encuentra paredes de contención que lo sujeten: la masa pierde tensión, se licúa, se desparrama sobre la bandeja y en el horno no tiene fuerza para expandirse.

### 2. El Test del Dedo (*Poke Test*) para Hornear a Tiempo
No te fíes del reloj; la temperatura ambiente cambia la velocidad biológica de las levaduras:
- **Prueba del dedo:** Presiona suavemente la masa con la yema del dedo enharinado unos 2 centímetros:
  - *Si rebota inmediatamente al 100%:* Falta fermentación.
  - *Si vuelve despacio y deja una leve hendidura visible:* **Punto perfecto para entrar al horno**.
  - *Si el hoyo se queda hundido y la masa tiembla como gelatina desinflándose:* Está sobrefermentada.

### 3. Ajustes Prácticos
1. **Segunda fermentación en frío (Retardo en nevera a 4 °C):** Tras formar el pan con buena tensión superficial, mételo en el banneton directo a la nevera durante 10-12 horas. El frío ralentiza las enzimas pero conserva la estructura del gluten y facilita el corte de la greña.
2. **Horneado con vapor:** Los primeros 15 minutos en el horno deben tener vapor abundante para mantener la corteza elástica y permitir la expansión del pan."""
    },
    {
        "user": "Al revisar los neumáticos delanteros de mi coche veo que el dibujo en el centro y exterior está en buen estado (unos 5 mm), pero la banda de rodadura en el hombro interior está casi en los alambres. Las presiones de inflado siempre han sido las recomendadas. ¿Qué anomalía mecánica está provocando este desgaste asimétrico?",
        "think": "Contexto: Desgaste severo en el hombro interior de neumáticos delanteros con presiones correctas.\nEvaluación: Desalineación geométrica por caída negativa excesiva o divergencia en dirección.\nConclusión: Alinear dirección ajustando convergencia y verificar holguras en rótulas y silentblocks.",
        "assistant": """Un desgaste acelerado concentrado exclusivamente en el borde interior del neumático se debe a un **desajuste en la geometría de la suspensión y dirección del vehículo**:

### 1. Causas Mecánicas Principales
1. **Divergencia Excesiva de las Ruedas (*Toe-out*):**
   - Es la causa más frecuente: las ruedas delanteras apuntan ligeramente hacia afuera en lugar de rodar paralelas hacia el frente. Al circular en línea recta, el coche va literalmente "arrastrando" el hombro interior de la goma contra el asfalto.
2. **Caída Negativa Excesiva (*Negative Camber*):**
   - La parte superior de la rueda está inclinada hacia el centro del vehículo, apoyando la mayor parte del peso sobre el flanco interior.
3. **Holgura en Silentblocks o Rótulas de Suspensión:**
   - Un bordillazo fuerte o baches pronunciados desgastan los tacos de goma del trapecio o la rótula de dirección, modificando las cotas dinámicas en aceleración.

### 2. Plan de Reparación Inmediato
- **No pongas neumáticos nuevos antes de alinear:** Si montas ruedas nuevas sin corregir las cotas mecánicas, destrozarás las gomas nuevas en menos de 5.000 km.
- **Acude a un taller de neumáticos y pide:**
  1. *Inspección visual de rótulas, bieletas y brazos de suspensión* para descartar piezas dobladas o con juego.
  2. *Alineación completa de dirección en banco láser 3D* para corregir la convergencia y caídas a los valores de fábrica."""
    },
    {
        "user": "En mi impresora 3D FDM, las impresiones de piezas de más de 8 cm de altura sufren un desplazamiento horizontal brusco de capas (layer shifting) a lo largo del eje Y. La pieza continúa imprimiéndose desfasada 4 mm hacia un lado. ¿Cómo diagnosticar y corregir este fallo mecánico?",
        "think": "Contexto: Desplazamiento repentino de capas en el eje Y en impresiones 3D de piezas altas.\nEvaluación: Correa del eje Y destensada, sobrecalentamiento del driver paso a paso o enganche de cables.\nConclusión: Tensar correa del eje Y, regular corriente Vref del driver y despejar recorrido de la cama.",
        "assistant": """El desplazamiento de capas (*layer shifting*) ocurre cuando el motor paso a paso del eje Y pierde pasos mecánicos mientras la placa controladora cree que sigue en la posición correcta:

### 1. Causas Raíz y Cómo Verificarlas
1. **Tensión Incorrecta de la Correa del Eje Y:**
   - Si la correa está floja, salta sobre los dientes de la polea durante aceleraciones bruscas. Si está excesivamente tensa, ejerce resistencia sobre el rodamiento del motor.
   - *Verificación:* Al pulsar la correa con el dedo debe tener la tensión de una cuerda grave de guitarra, sin holguras.
2. **Sobrecalentamiento del Driver del Motor Paso a Paso:**
   - A partir de cierta altura, tras horas de impresión continua, el chip driver en la placa base (ej. TMC2209) se calienta. Al alcanzar la protección térmica, el driver se apaga durante 200 milisegundos para no quemarse, perdiendo pasos al instante.
   - *Verificación:* Comprueba si el ventilador que refrigera la electrónica interna de la impresora está sucio o apagado.
3. **Enganche de Cables o Colisión Física:**
   - En piezas altas, el haz de cables de la cama caliente o del cabezal puede rozar con el chasis trasero bloqueando el recorrido de la cama.

### 2. Protocolo de Ajuste
- Aprieta el prisionero metálico de la polea dentada del motor del eje Y (a veces gira el eje del motor pero la polea patina).
- Reduce la aceleración del eje Y en el programa laminador (Cura/PrusaSlicer) de 1000 mm/s² a **500 mm/s²**.
- Verifica que las ruedas excéntricas de la guía de la cama no tengan holgura ni puntos duros al moverla manualmente con la impresora apagada."""
    },
    {
        "user": "En una vivienda unifamiliar de dos plantas, la presión del agua en la planta baja es excelente (grifos de cocina y jardín con mucho caudal), pero en los platos de ducha de la segunda planta el agua sale con un hilo débil que no llega a activar el encendido de la caldera de gas. ¿Cuál es el origen y la solución?",
        "think": "Contexto: Pérdida crítica de presión en duchas de planta alta sin encender caldera de gas.\nEvaluación: Pérdida de carga estática combinada con calcificación en filtros de alcachofa o tubería.\nConclusión: Descalcificar difusores, revisar llave de paso de planta alta o instalar grupo de presión.",
        "assistant": """La pérdida de presión selectiva en la planta alta se debe a la **pérdida de presión estática por altura combinada con una restricción de caudal localizada**:

### 1. Física de la Altura y Calentadores de Gas
- Por cada 10 metros de elevación se pierde 1 bar de presión solo por gravedad. Una segunda planta supone unos 3-4 metros de subida (~0,35 bar menos que en planta baja).
- Las calderas y calentadores de gas incorporan una membrana presostática o sensor de flujo que exige un **caudal mínimo de arranque (habitualmente entre 2,5 y 3 litros por minuto)**. Si el caudal cae por debajo de ese umbral, la caldera no enciende por seguridad.

### 2. Diagnóstico Paso a Paso
1. **Calcificación en la alcachofa de la ducha y filtros de grifería:**
   - Es la causa más común: desenrosca la alcachofa de la ducha y abre el flexo directamente. Si el caudal aumenta notablemente y la caldera enciende, el problema es simplemente acumulación de cal en los microporos de la alcachofa. Sumérgela en vinagre caliente durante 1 hora.
2. **Llave de Corte de Sector en Planta Alta Parcialmente Cerrada:**
   - Revisa la llave de paso empotrada en el distribuidor de la segunda planta: a veces tras una reparación anterior queda abierta solo al 50%.
3. **Si el problema es general en toda la planta alta:**
   - Si la presión de red de la compañía suministradora es inferior a 2 bar, la presión residual arriba es insuficiente. La solución técnica definitiva es intercalar un **pequeño grupo de presión doméstico silencioso con presostato electrónico (bomba de apoyo)** a la entrada de la vivienda."""
    },
    {
        "user": "Nuestra tienda online de vajillas de cerámica artesanal ha visto aumentar las reclamaciones por roturas durante el transporte del 2% al 11% en los últimos 2 meses. No hemos cambiado de empresa de mensajería y seguimos usando cajas de cartón con plástico de burbujas. ¿Cómo diagnosticar la causa oculta del incremento de roturas?",
        "think": "Contexto: Incremento de roturas de cerámica en envíos del 2% al 11% sin cambiar transportista aparente.\nEvaluación: Cambio de calidad en el gramaje del cartón, burbuja desinflada o falta de inmovilización interna.\nConclusión: Prueba de caída interna, auditar espesor de cajas suministradas y empaquetado doble caja.",
        "assistant": """Cuando las roturas se quintuplican utilizando el mismo transportista, la causa raíz se encuentra en **cambios sutiles en la calidad de los consumibles de embalaje o en la técnica de amortiguación**:

### 1. Causas Ocultas Habituales
1. **Degradación del Proveedor de Cajas (Gramaje del Cartón):**
   - Comprueba si el último lote de cajas de cartón es de canal simple en lugar de canal doble, o si el papel exterior es reciclado de bajo gramaje. Las cajas baratas ceden bajo el apilamiento en los camiones de reparto, transmitiendo la presión directamente a la cerámica.
2. **El Error del Plástico de Burbujas Suelto:**
   - Envolver una taza en plástico de burbujas no sirve de nada si dentro de la caja queda aire libre. Si el objeto puede deslizarse o chocar contra las paredes de la caja ante una deceleración brusca, la cerámica se quiebra por inercia.
3. **Impacto por Choque Cerámica con Cerámica:**
   - Platos apilados sin láminas intermedias de espuma amortiguadora chocan entre sí cuando el paquete sufre vibraciones en la cinta clasificadora de la paquetería.

### 2. Protocolo de Diagnóstico Inmediato
- **La Prueba de la Caída y el Agitado (*Drop Test*):** Empaqueta un paquete como de costumbre, ciérralo y agítalo enérgicamente. **No debe sonar absolutamente nada ni sentirse desplazamiento interior**. Déjalo caer desde 1 metro de altura sobre suelo de hormigón. Si se rompe, el embalaje no es apto para paquetería estándar.
- **La Solución Estándar (Doble Caja):** Introduce la cerámica amortiguada en una caja interna y colócala dentro de una caja exterior con 5 cm de chips de relleno biodegradable o papel kraft prensado perimetral."""
    },
    {
        "user": "Nuestro microservicio en Node.js y Express corre estable en producción tras ser reiniciado, pero tras 48-72 horas de ejecución continua, los tiempos de respuesta de los endpoints se degradan de 30 ms a más de 3.000 ms y la memoria RAM del contenedor sube de 200 MB a 1,8 GB hasta reiniciarse por Out of Memory. ¿Qué patrón de fuga de memoria es el más probable?",
        "think": "Contexto: Fuga de memoria progresiva en Node.js degradando latencia tras 48h hasta colapso OOM.\nEvaluación: EventListeners no desuscritos, caches en memoria sin política de desalojo o closures retenidos.\nConclusión: Generar heap dump comparativo e inspeccionar arrays globales o caches estáticas sin TTL.",
        "assistant": """Este comportamiento describe el patrón de libro de una **fuga de memoria (*memory leak*) con sobrecarga del recolector de basura (Garbage Collector)**:

### 1. Por qué la Latencia se Dispara antes del Reinicio
- A medida que el montón de memoria (*heap*) se satura cerca del límite (1,8 GB), el motor V8 de Node.js entra en pánico y ejecuta ciclos completos de recolección de basura (*Mark-Sweep-Compact*) cada vez más agresivos.
- Como la recolección detiene el hilo de ejecución principal de Node.js (*Stop-The-World*), la aplicación congela las peticiones entrantes durante segundos, disparando la latencia de 30 ms a más de 3.000 ms.

### 2. Patrones Culpables Más Frecuentes en Node.js
1. **Caché en Memoria sin Límite (Objetos Globales):** Guardar tokens de sesión, peticiones o datos de usuario en un simple objeto JavaScript `const cache = {}` sin TTL (tiempo de vida) ni límite de claves (LRU cache). Cada petición nueva agranda el objeto indefinidamente.
2. **Listeners de Eventos no Eliminados:** Registrar oyentes con `emitter.on('data', handler)` en funciones que se ejecutan en cada petición HTTP sin hacer nunca `emitter.off()`.
3. **Closures que Retienen Contexto:** Funciones anónimas o callbacks que capturan variables de gran tamaño en su ámbito léxico impidiendo que el GC las destruya.

### 3. Procedimiento para Capturar la Causa Raíz
1. Arranca Node.js con el flag `--inspect`.
2. Conecta Chrome DevTools (`chrome://inspect`) y toma un **Heap Snapshot** al reiniciar (estado base).
3. Tras 24 horas toma un segundo Heap Snapshot y pulsa la vista **Comparison**.
4. Ordena por *Size Delta*: verás exactamente qué clase u objeto (ej. `Array`, `Closure`, `Object`) ha crecido en miles de instancias retenidas."""
    },
    {
        "user": "La factura de electricidad de nuestro piso habitual se ha multiplicado por tres en octubre y noviembre respecto al mismo periodo del año pasado, pasando de 65 € a 195 €. No usamos radiadores eléctricos ni aire acondicionado y la tarifa sigue siendo la misma. ¿Cómo auditar el cuadro eléctrico para pillar al electrodoméstico culpable?",
        "think": "Contexto: Factura eléctrica triplicada en otoño sin uso de climatización aparente.\nEvaluación: Resistencia eléctrica encendida permanentemente por fallo en termostato de termo o suelo radiante.\nConclusión: Comprobación de potencia instantánea en contador digital bajando magnetotérmicos uno a uno.",
        "assistant": """Un salto de 130 € al mes sin climatización equivale a un **consumo fantasma continuo de entre 1.000W y 1.500W funcionando las 24 horas del día**. En el 95% de los hogares, el culpable es una **resistencia eléctrica con el termostato averiado**:

### 1. El Sospechoso Número Uno: El Termo Eléctrico
- Si el termostato del termo de agua caliente se estropea (quedando pegado en posición cerrada) o acumula una costra gruesa de cal sobre la vaina sensora, **la resistencia eléctrica de 1.500W no se apaga jamás**.
- Si además la válvula de seguridad gotea hacia el desagüe, el termo expulsa agua caliente continuamente y calienta agua fría sin parar, devorando más de 30 kWh al día de forma silenciosa.

### 2. Protocolo de Aislamiento en el Cuadro Eléctrico (En 10 Minutos)
1. **Accede al contador digital de la compañía eléctrica:**
   - La luz roja parpadea más rápido cuanto más consumo hay. En la pantalla LCD pulsa el botón frontal hasta llegar al menú `Potencia Actual (kW)`.
2. **Medición base:**
   - Observa la potencia instantánea. Si marca por ejemplo **1,6 kW** sin nada encendido, confirma el drenaje masivo activo.
3. **Prueba de corte secuencial en el cuadro eléctrico:**
   - Baja todos los interruptores magnetotérmicos (PIAs) del cuadro de casa. El consumo en el contador debe caer a 0,0 kW.
   - Sube uno por uno esperando 10 segundos en cada uno:
     - El interruptor que al subirlo haga saltar instantáneamente la lectura del contador de 0,1 kW a 1,5 kW te indicará exactamente qué circuito de la casa está causando el desfalco (termo, enchufes de cocina, o suelo radiante encendido por error)."""
    },
    {
        "user": "En mi huerto urbano, los tomates crecen con buen tamaño pero al empezar a madurar desarrollan una mancha negra, aplastada y coriácea en la base opuesta al tallo (el 'culo' del tomate), arruinando la cosecha. ¿Es un hongo infeccioso o una deficiencia de nutrientes?",
        "think": "Contexto: Manchas negras hundidas en la base del tomate en huerto de macetas.\nEvaluación: Síntoma de necrosis apical o podredumbre peduncular provocada por déficit de calcio móvil.\nConclusión: No es un hongo; se corrige estabilizando el riego para permitir la absorción de calcio.",
        "assistant": """Este problema no es una enfermedad fúngica ni una plaga bacteriana; es un desorden fisiológico conocido como **podredumbre apical o necrosis apical (*blossom end rot*)**, comúnmente llamado el 'culo negro' del tomate:

### 1. La Causa Raíz Real: Estrés Hídrico y Calcio
- La mancha negra se produce por la **falta de calcio en las células distales del fruto** en el momento de su crecimiento rápido. Sin calcio, las paredes celulares colapsan y se necrosan.
- **La paradoja:** El 90% de las veces la tierra sí tiene calcio abundante, pero **la planta no puede transportarlo por fluctuaciones en el riego**.
- El calcio es un nutriente pesado que solo se desplaza por el flujo de transpiración del agua. Si el sustrato de la maceta se seca por completo y luego se riega en exceso, el flujo hídrico se interrumpe y las puntas de los tomates quedan desabastecidas.

### 2. Tratamiento y Corrección
1. **Estabilizar la Humedad del Sustrato:** Riega con regularidad manteniendo una humedad constante como una esponja escurrida, evitando alternar entre tierra seca cuarteada y tierra empapada.
2. **Acolchado o *Mulching*:** Cubre la superficie de la maceta con 3 cm de paja, corteza de pino o restos secos para frenar la evaporación del agua por el sol.
3. **Aporte de Calcio:** Si el agua de tu zona es muy blanda o la tierra muy ácida, añade un fertilizante foliar con nitrato de calcio o enmienda de caliza dolomítica. Retira los tomates afectados para que la planta no gaste energía en ellos."""
    },
    {
        "user": "Al frenar con el coche a muy baja velocidad (por ejemplo al detenerse en un semáforo a menos de 20 km/h pisando suavemente), los frenos delanteros emiten un chirrido agudo muy molesto. Al frenar con fuerza a alta velocidad no suena nada. Las pastillas tienen solo 6 meses. ¿Por qué chirrían?",
        "think": "Contexto: Chirrido agudo en frenos delanteros exclusivamente a baja velocidad y frenada suave.\nEvaluación: Microvibraciones armónicas entre el dorso de la pastilla y el pistón de la pinza de freno.\nConclusión: Cristalización superficial de pastilla y falta de pasta de cobre/antivibración en la placa de apoyo.",
        "assistant": """El chirrido agudo a baja velocidad no significa necesariamente que los frenos estén gastados; es una **resonancia armónica acústica (vibración de alta frecuencia)** entre la pastilla de freno y la pinza:

### 1. Por qué Suena a Baja Velocidad y no en Frenadas Fuertes
- Al frenar con suavidad a baja velocidad, la pastilla roza el disco de acero con poca presión, permitiendo que la pastilla vibre microscópicamente a miles de hercios dentro del soporte de la pinza, emitiendo ese silbido agudo.
- Al frenar con fuerza, la enorme presión hidráulica del pistón inmoviliza la pastilla contra el disco, suprimiendo la vibración.

### 2. Causas Principales
1. **Cristalización de la Superficie de la Pastilla:** Tras un uso urbano repetitivo con frenadas muy suaves, la resina de fricción se endurece formando una capa vitrificada pulida como cristal que resbala y chilla.
2. **Falta de Pasta Antivibratoria en el Dorso:** Al cambiar las pastillas hace 6 meses, no se aplicó grasa de cobre o pasta cerámica en la placa metálica posterior donde apoya el pistón.
3. **Ausencia de Láminas Antirruido (*shims*):** Chapas metálicas delgadas que absorben la resonancia mecánica.

### 3. Solución Rápida
- **Desglasar las pastillas:** En un lugar seguro sin tráfico, realiza un par de frenadas firmes y progresivas de 80 km/h a 20 km/h para decapar la capa superficial vitrificada.
- **En el taller:** Desmontar pastillas, lijar suavemente el compuesto, limpiar el polvo de freno acumulado y aplicar **pasta cerámica en los puntos de contacto posteriores**."""
    },
    {
        "user": "En nuestro software SaaS B2B con prueba gratuita de 14 días y suscripción mensual, la tasa de cancelación (*churn rate*) no ocurre durante los primeros días, sino que se concentra masivamente en el día 28 tras registrar la tarjeta. ¿Por qué ocurre este patrón de abandono retrasado y cómo mitigarlo?",
        "think": "Contexto: Cancelaciones concentradas en el día 28 tras el primer cobro en SaaS B2B.\nEvaluación: Usuarios que olvidaron cancelar la prueba ven el cobro en el extracto y reaccionan antes del segundo mes.\nConclusión: Falta de valor percibido en onboarding; implantar notificaciones previas y métricas de activación.",
        "assistant": """El patrón de cancelación masiva en el **día 28** es el síntoma inequívoco del **usuario pasivo que olvidó cancelar la prueba y reacciona al ver el cargo en el extracto bancario**:

### 1. El Ciclo de la Cancelación Fantasma
- El usuario introdujo su tarjeta para iniciar los 14 días de prueba. Al expirar el día 14, se ejecutó el cobro del primer mes de suscripción.
- Durante las semanas 3 y 4 el cliente apenas utilizó el software (*falta de activación real*).
- Hacia el día 28, o bien revisa sus movimientos bancarios o recibe el aviso de renovación del mes siguiente, y cancela inmediatamente para no asumir un segundo pago de una herramienta que no ha integrado en su operativa diaria.

### 2. Dónde Está la Causa Raíz
El problema no reside en el precio ni en la pantalla de cancelación; reside en el **onboarding deficiente durante los primeros 7 días**:
- El cliente nunca alcanzó el momento de satisfacción (*Aha! Moment*). Si en las primeras 48 horas el usuario no conecta sus datos o no ve un resultado tangible, la cuenta queda abandonada aunque pague el primer ciclo por inercia.

### 3. Estrategia de Mitigación
1. **Monitorización de Métricas de Activación Temprana:** Si una cuenta de pago no realiza ninguna acción clave en los 5 días posteriores al cobro, activa un correo personalizado o una llamada de soporte proactiva ofreciendo ayuda para configurar la plataforma.
2. **Correos de 'Resumen de Valor':** Envía un informe semanal automático mostrando las horas ahorradas o los datos procesados por la herramienta durante el mes."""
    },
    {
        "user": "El comando `df -h` en un servidor Ubuntu Linux muestra que la partición raíz `/` (80 GB) está al 100% de capacidad y el sistema bloquea escrituras. Sin embargo, al ejecutar `du -sh /*` para localizar los archivos grandes, la suma de todos los directorios apenas alcanza 18 GB. ¿Dónde están los 62 GB desaparecidos y cómo liberarlos de inmediato?",
        "think": "Contexto: Discrepancia de 62 GB entre df (100% ocupado) y du (18 GB reales) en Linux.\nEvaluación: Archivos gigantes eliminados con rm pero retenidos por procesos activos que mantienen su descriptor abierto.\nConclusión: Localizar procesos con lsof +L1 y reiniciar los demonios culpables para liberar espacio.",
        "assistant": """Esta discrepancia clásica en Linux ocurre cuando **archivos de gran tamaño (habitualmente logs) han sido borrados con `rm`, pero un proceso activo aún mantiene abierto su descriptor de archivo**:

### 1. La Explicación del Núcleo de Linux
- En sistemas Unix, borrar un archivo con `rm archivo.log` solo elimina el enlace en el directorio (*dentry*).
- Si un demonio (como Nginx, Apache, MySQL o un script de Python) sigue teniendo el archivo abierto para escribir, el núcleo **no libera los bloques de disco hasta que el proceso finaliza o se reinicia**.
- Por eso `du` (que recorre el árbol de directorios) no encuentra el archivo y suma solo 18 GB, mientras que `df` (que consulta directamente los bloques ocupados del sistema de archivos) reporta que el disco sigue al 100%.

### 2. Cómo Diagnosticar y Solucionar en 3 Minutos
1. **Localizar los archivos borrados que retienen espacio:**
   Ejecuta en la terminal como root:
   ```bash
   lsof +L1 | grep deleted
   # o alternativamente:
   lsof / | grep '(deleted)' | sort -nr -k 7 | head -10
   ```
   Verás en la columna de tamaño archivos de gigabytes marcados como `(deleted)` junto al nombre del proceso y su **PID**.

2. **Liberar el espacio sin reiniciar el servidor:**
   - La mejor solución es **reiniciar suavemente el servicio responsable** para que cierre el descriptor:
     ```bash
     systemctl reload nginx  # o restart
     ```
   - Si no puedes reiniciar el servicio de inmediato, vacía el descriptor directamente a través del sistema `/proc` usando su PID y el número de descriptor de archivo (FD):
     ```bash
     : > /proc/<PID>/fd/<FD>
     ```
   El espacio de 62 GB se liberará al instante en `df -h`."""
    }
]
