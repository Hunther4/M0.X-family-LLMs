"""
Categoría 1: Problemas cotidianos y organización práctica (20 escenarios)
Bloques <think> concisos de 30-80 tokens según pauta.
"""

SCENARIOS_CAT1 = [
    {
        "user": "Tuvimos un gasto médico imprevisto de 1.800 € financiado al 19% TAE. Nuestros ingresos familiares son 2.600 €/mes y los gastos fijos 1.950 €. Solo quedan 400 € en cuenta. ¿Cómo reestructurar el presupuesto para liquidar la deuda sin asfixiarnos?",
        "think": "Contexto: Deuda de 1.800 € al 19% con margen de 650 €.\nEvaluación: Abonar 500 €/mes liquida en 4 meses y reserva 150 €.\nConclusión: Amortización rápida protegiendo liquidez.",
        "assistant": """Para liquidar esta deuda de 1.800 € de forma rápida y segura sin comprometer tu subsistencia, aplica este plan estructurado:

### 1. Refinanciación Inmediata (Prioridad Alta)
- **Anticipo de nómina:** Solicita a tu empresa un anticipo sin intereses a descontar en 6 mensualidades. Cancelarías la tarjeta de inmediato eliminando el 19% TAE.
- **Transferencia de saldo:** Si no es viable, busca una tarjeta con promoción al 0% en traspaso de saldo durante 6 a 12 meses.

### 2. Plan de Choque con tus 650 € de Margen
Con 2.600 € de ingresos y 1.950 € de gastos fijos dispones de **650 € libres al mes**:
- **Amortización a la tarjeta:** 500 €/mes estrictos.
- **Reserva de emergencia:** 150 €/mes en cuenta separada para evitar nuevos endeudamientos ante imprevistos menores.
- **Saldo actual:** Conserva 250 € de los 400 € actuales como suelo de seguridad y usa 150 € para una amortización inicial inmediata.

### 3. Plazos y Ahorro
- Con pagos de 500 € mensuales, la deuda quedará totalmente saldada en **3 meses y medio**.
- Pagarás menos de 60 € en intereses totales, frente a los más de 550 € que costaría abonar las cuotas mínimas."""
    },
    {
        "user": "La factura del agua ha subido un 70% este bimestre sin cambios de hábito en casa. Sospecho una fuga oculta o goteo continuo. ¿Cómo diagnosticar el origen sin romper paredes ni contratar de inmediato a un fontanero?",
        "think": "Contexto: Aumento del 70% en factura de agua sin consumo visible.\nEvaluación: Fuga pasiva en cisterna o válvula de seguridad del termo.\nConclusión: Test de contador estático y colorante en inodoros.",
        "assistant": """Para localizar el origen del sobreconsumo de agua sin romper nada ni incurrir en gastos, sigue este protocolo de diagnóstico en 4 pasos:

### 1. La Prueba del Contador Estático
1. Cierra todos los grifos y asegúrate de que electrodomésticos como lavadora o lavavajillas estén apagados.
2. Fotografía el contador de agua registrando todos los dígitos y la rueda pequeña de flujo.
3. Deja pasar **45 minutos sin usar agua**.
4. Vuelve a revisar: si el contador avanzó, hay una fuga activa dentro de tu instalación.

### 2. Prueba del Colorante en Cisternas (Causa del 80% de los casos)
1. Vierte unas gotas de colorante alimentario o café concentrado en el depósito de cada inodoro.
2. No tires de la cadena y espera 20 minutos.
3. Si el agua de la taza se tiñe, la junta de descarga está desgastada y deja escapar agua continuamente hacia el desagüe.

### 3. Inspección de Caldera o Termo
- Revisa la válvula de seguridad (pieza de latón con pequeña palanca). Si gotea agua caliente hacia el desagüe, tiene acumulación de cal y no cierra herméticamente.

### 4. Aislamiento por Llaves de Escuadra
- Cierra las llaves de paso individuales bajo lavabos y sanitarios. Si el contador se detiene, abre una a una para identificar el punto exacto de fuga."""
    },
    {
        "user": "Tengo que mudarme de Madrid a Valencia (360 km) en un mes con cama, escritorio, sofá de 2 plazas, mesa y 15 cajas. Mi presupuesto máximo es de 450 €. Las empresas tradicionales piden más de 900 €. ¿Cuál es la estrategia logística más viable?",
        "think": "Contexto: Mudanza de 360 km con tope de 450 € frente a presupuestos de 900 €.\nEvaluación: Furgoneta alquilada ida/vuelta 24h resulta más barata que el grupaje.\nConclusión: Alquiler 24h en origen + regreso en tren low-cost.",
        "assistant": """Para realizar esta mudanza por debajo de 450 €, la opción más rentable consiste en alquilar una furgoneta devolviéndola en el punto de origen:

### Estrategia Recomendada: Furgoneta 24h Ida y Vuelta + Tren Low-Cost
Las empresas de alquiler cobran un recargo de 150-250 € si entregas el vehículo en otra ciudad. Evítalo devolviéndola en Madrid:

1. **Alquiler de furgoneta grande (12-14 m³, tipo Renault Master L2H2/L3H2):**
   - Tarifa de 24 horas entre semana con 800 km incluidos: **120 € - 140 €**.
2. **Combustible (720 km ida y vuelta en A-3 sin peajes):**
   - Consumo medio de 9,5 L/100 km a 1,45 €/L diésel: **~99 €**.
3. **Regreso a Valencia en alta velocidad low-cost:**
   - Billete de Iryo, Ouigo o Avlo tras devolver la furgoneta en Madrid: **15 € - 25 €**.
4. **Material de embalaje y cinchas de amarre:** **30 €**.

- **Gasto total estimado:** **~270 € a 295 €** (ahorras más de 150 € sobre tu tope de 450 €).

### Alternativa sin Conducir (Grupaje en Retorno)
Publica tu carga en plataformas de transportistas como **Shiply** o **Anyvan**. Los transportistas que regresan de Madrid a la costa con espacio vacío en camión suelen presupuestar traslados de 10-12 m³ por **360 € a 420 €** a pie de calle."""
    },
    {
        "user": "Debo desplazarme diariamente 44 km en total (22 km ida y 22 km vuelta) para trabajar. Dudo entre transporte público (75 min por trayecto), scooter de 125cc de segunda mano, o bicicleta eléctrica (70% carril bici). Valoro coste, tiempo y seguridad.",
        "think": "Contexto: Desplazamiento de 44 km diarios analizando coste, tiempo y riesgo.\nEvaluación: E-bike exige >2h diarias de pedaleo; metro pierde 2,5h; moto ahorra 95 min/día.\nConclusión: Scooter 125cc con transporte público en días de lluvia.",
        "assistant": """Analizando las tres opciones para un recorrido interurbano de **44 km diarios**:

### Comparativa Rápida

| Medio | Tiempo diario total | Coste mensual real | Seguridad y fatiga |
| :--- | :--- | :--- | :--- |
| **Transporte público** | 2 h 30 min (150 min) | **50 € - 65 €** (Abono) | Máxima seguridad, pero 12,5 h semanales perdidas |
| **Scooter 125cc** | **55 min (ahorra 95 min/día)** | ~140 € (Gasolina, seguro, mant.) | Riesgo moderado; vulnerabilidad al clima |
| **Bicicleta eléctrica** | 2 h 15 min | ~45 € (Amortización y luz) | Agotador en 44 km; 30% del tramo sin carril bici |

### Veredicto y Recomendación
1. **Descartar la bicicleta eléctrica:** Recorrer 44 km al día con asistencia a 25 km/h exige pedalear más de dos horas diarias. El 30% del tramo sin carril segregado supone un riesgo vial inaceptable.
2. **Elección principal (Scooter 125cc de 4 tiempos):** Te devuelve **8 horas libres a la semana**. El sobrecoste neto respecto al abono de transporte es de unos 80 €/mes (apenas 2,5 € por hora de vida recuperada). Modelos como Honda PCX o Kymco Agility ofrecen consumos inferiores a 2,6 L/100 km.
3. **Estrategia combinada:** Utiliza la scooter el 85% de los días secos y recurre a un billete de transporte público en jornadas de lluvia intensa o heladas."""
    },
    {
        "user": "En invierno la factura de gas de nuestro piso antiguo de techos altos (3m) se disparó a 260 € y sigue haciendo frío. Estamos de alquiler y no podemos hacer obras. ¿Qué medidas de bajo coste podemos aplicar para mejorar el calor y bajar el gasto?",
        "think": "Contexto: Factura de gas de 260 € en piso alquilado con techos altos.\nEvaluación: Fugas en ventanas y convección al techo enfrían la estancia.\nConclusión: Burletes, paneles reflectantes en radiadores y caldera a 60 °C.",
        "assistant": """En techos de 3 metros el volumen de aire aumenta un 25% y el calor se acumula arriba. Al estar en alquiler, puedes recortar un **25% a 30% de la factura** invirtiendo menos de 50 € con estas medidas reversibles:

### 1. Optimización de Radiadores (Inversión: ~20 €)
- **Instala láminas reflectantes traseras:** Coloca film aislante metalizado detrás de cada radiador pegado al muro exterior. Reflejará el calor infrarrojo hacia el centro de la habitación en lugar de calentar la fachada.
- **Purga de aire:** Púrgalos con una llave cuadrada hasta que salga agua continua sin gorgoteos; el aire atrapado impide calentar la mitad superior.

### 2. Eliminación de Corrientes Frías (Inversión: ~15 €)
- **Burletes de caucho perfil D/P:** Colócalos en todos los marcos de ventanas y puertas de balcones para sellar rendijas de aire exterior.
- **Bajo puertas:** Instala burletes adhesivos de cepillo en la puerta principal y puertas que den a zonas frías o galerías.

### 3. Regulación de la Caldera
- **Temperatura de impulsión:** Si tu caldera es de condensación, gradúa el agua de calefacción entre **58 °C y 62 °C**. Si supera 65 °C deja de condensar y pierde hasta un 15% de eficiencia.
- **Zonificación:** Cierra las llaves de radiadores en estancias desocupadas y mantén sus puertas cerradas. Cortinas gruesas hasta el suelo frenan el enfriamiento perimetral."""
    },
    {
        "user": "Tengo 34 años y trabajo en turnos rotativos (mañanas 06-14, tardes 14-22, noches 22-06). Sufro insomnio severo, problemas gástricos y fatiga al cambiar de turno. ¿Cómo estructurar un protocolo circadiano para descansar?",
        "think": "Contexto: Alteración circadiana por turnos rotativos de mañana, tarde y noche.\nEvaluación: Luz matutina y comidas nocturnas desincronizan el reloj biológico.\nConclusión: Gafas oscuras post-turno, ayuno nocturno y ajuste de melatonina.",
        "assistant": """El trabajo en turnos rotativos desajusta el reloj cerebral (gobernado por la luz) respecto a los relojes periféricos digestivos. Aplica este protocolo científico para mitigar el impacto:

### 1. Gestión Lumínica en el Turno de Noche
- **Salida a las 06:00 AM:** Ponte **gafas de sol oscuras polarizadas** antes de cruzar la puerta exterior del centro de trabajo. La luz solar matutina bloquea de inmediato la producción de melatonina e impide el sueño diurno profundo.
- **Entorno de descanso:** Dormitorio en oscuridad absoluta (antifaz opaco y persiana bajada), temperatura a 19 °C y tapones de silicona o ruido blanco constante.

### 2. Crononutrición y Protección Gástrica
- **Durante la noche (00:00 a 06:00):** La motilidad intestinal se detiene. **No consumas comidas copiosas ni carbohidratos simples**. Toma únicamente frutos secos crudos o infusiones tibias.
- **Corta la cafeína a las 02:00 AM:** El café ingerido en las últimas 4 horas de turno retrasará la conciliación del sueño durante el día.

### 3. Transición al Salir del Ciclo Nocturno
- Tras la última noche, **no duermas 8 horas de día**. Duerme un bloque corto de 4 horas (de 08:00 a 12:00), levántate, exponte a la luz natural del mediodía y acuéstate a las 23:00 para reiniciar el ciclo.
- **Suplementación:** Melatonina de liberación combinada (1 mg) 30 minutos antes del descanso diurno y 250 mg de bisglicinato de magnesio."""
    },
    {
        "user": "En invierno aparecen manchas oscuras de moho en las esquinas del techo y las ventanas gotean condensación en las habitaciones orientadas al norte. Carpintería de aluminio básica con climalit pero sin rotura de puente térmico en 80 m² con 4 personas. ¿Cómo resolverlo sin disparar la luz?",
        "think": "Contexto: Moho y condensación en vivienda habitada por 4 personas.\nEvaluación: Aire húmedo alcanza punto de rocío en paramentos fríos.\nConclusión: Ventilación por choque térmico y control de vapor en duchas.",
        "assistant": """El moho surge cuando el vapor interior encuentra superficies a menos de 13 °C (punto de rocío). Para erradicarlo y mantener la humedad relativa por debajo del 55%:

### 1. Limpieza y Tratamiento Fungicida Inmediato
- **Nunca limpies moho en seco:** Esparce esporas por toda la casa. Pulveriza agua con lejía al 20% o limpiador específico con cloro activo.
- Deja actuar 15 minutos, limpia con bayeta húmeda con mascarilla FFP2 y repinta esas esquinas con **pintura anticondensación con microesferas de cerámica** para elevar 2 °C la temperatura superficial de la pared.

### 2. Protocolo de Ventilación por Choque Térmico (Coste cero)
- Deja de ventilar con ventanas entreabiertas durante horas: solo enfría los tabiques y empeora el problema.
- Abre **todas las ventanas de par en par durante 6 a 8 minutos, 3 veces al día**.
- Se produce una renovación total del volumen de aire sin enfriar los muros. El aire exterior invernal, al calentarse a 20 °C dentro, reduce drásticamente su humedad relativa a menos del 45%.

### 3. Control de Focos de Vapor
- **Duchas:** Cierra siempre la puerta del baño y ventila hacia el exterior durante 15 minutos antes de abrirla al pasillo.
- **Ropa:** Prohibido secar prendas en radiadores o habitaciones cerradas sin deshumidificador.
- Coloca un termohigrómetro digital (menos de 10 €): si la humedad supera el 58%, ejecuta un choque de ventilación puntual."""
    },
    {
        "user": "Tengo 2.500 fotos y vídeos dispersos entre dos discos duros externos, un portátil viejo y la memoria del móvil. Quiero diseñar un sistema de copias de seguridad personal seguro siguiendo la regla 3-2-1 con presupuesto inferior a 150 € iniciales. ¿Cómo estructurarlo?",
        "think": "Contexto: Archivos multimedia dispersos sin respaldo 3-2-1 con 150 € de tope.\nEvaluación: Soportes físicos aislados arriesgan avería o extravío.\nConclusión: Consolidar en disco externo de 2 TB y backup cifrado en nube.",
        "assistant": """Para blindar tus recuerdos bajo el estándar profesional **3-2-1** (3 copias de los datos, en 2 soportes distintos, 1 de ellas fuera de casa) con menos de 150 €:

### 1. La Arquitectura 3-2-1
- **Copia 1 (Datos de trabajo/origen):** El almacenamiento interno de tu portátil u ordenador de uso diario consolidado.
- **Copia 2 (Copia local física redundante):** Disco duro externo de 2 TB (Western Digital My Passport o Seagate Basic: ~65 €).
- **Copia 3 (Copia remota fuera de casa):** Almacenamiento en la nube (Google Drive 2 TB por ~99 €/año o Microsoft 365 con 1 TB de OneDrive por ~69 €/año).

### 2. Plan de Consolidación y Limpieza (Paso a Paso)
1. **Unificación centralizada:** Conecta los discos y el móvil al ordenador y vuelca todo en una única carpeta maestra llamada `FOTOS_CONSOLIDADAS`.
2. **Deduplicación automática:** Ejecuta una herramienta gratuita de código abierto como **Czkawka** o **DupeGuru**. Analizará los hashes SHA-256 de las fotos y eliminará duplicados idénticos liberando decenas de gigabytes.
3. **Estructura lógica de carpetas:** Organiza por año y mes: `AAAA/AAAA-MM_NombreEvento` (ej. `2024/2024-08_VacacionesAsturias`).

### 3. Automatización de las Copias
- **Copia local:** Utiliza **FreeFileSync** (gratuito) para programar una sincronización en espejo hacia el disco duro externo cada domingo.
- **Copia remota:** Configura la app de escritorio de tu nube para subir automáticamente esa carpeta con cifrado activo. Tus archivos quedarán protegidos contra robo, fuego o rotura física de hardware."""
    },
    {
        "user": "Teletrabajo 8 horas diarias y sufro dolor lumbar y cervical al final de la jornada. Trabajo con un portátil sobre la mesa del comedor y una silla básica. Tengo un presupuesto ajustado de 180 € para adaptar ergonómicamente mi puesto. ¿Qué elementos comprar y cómo distribuirlos?",
        "think": "Contexto: Dolor cervical y lumbar por teletrabajar con portátil en mesa común.\nEvaluación: Mirar hacia abajo flexiona el cuello y falta apoyo en columna.\nConclusión: Soporte de portátil, teclado/ratón externo y cojín lumbar con reposapiés.",
        "assistant": """El origen de tu dolor es biomecánico: mirar hacia abajo a la pantalla del portátil sobrecarga las vértebras cervicales con una presión equivalente a 20 kg, y la silla sin soporte aplana la curvatura lordótica lumbar. Con **180 € de presupuesto**, la distribución óptima de compras es:

### 1. Elementos Ergonómicos Clave (Desglose de compras)
1. **Soporte elevador para portátil regulable en altura (aluminio):** **~25 €**. Eleva la parte superior de la pantalla justo a la altura de tus ojos.
2. **Teclado externo compacto y ratón ergonómico vertical:** **~45 €** (ej. Anker vertical + Logitech K380). Permite mantener los antebrazos apoyados en ángulo de 90° sin encorvar hombros.
3. **Cojín lumbar ergonómico de espuma viscoelástica con memoria:** **~25 €**. Corrige la postura en tu silla actual forzando a la pelvis a mantenerse vertical.
4. **Reposapiés inclinable ajustable:** **~25 €**. Garantiza que las plantas de los pies queden planas si la mesa del comedor queda demasiado alta.
5. **Colirio lubricante y lámpara flexo cálida indirecta hacia la pared:** **~20 €**. Reduce la fatiga ocular que te hace inclinar el cuello hacia la pantalla.
*Gasto total acumulado: ~140 € (te sobran 40 €).*

### 2. Calibración Ergonómica del Puesto
- **Altura de pantalla:** El tercio superior del monitor debe quedar exactamente en tu línea horizontal de visión sin bajar la barbilla.
- **Brazos y hombros:** Codos en ángulo de 90° con antebrazos descansando sobre la mesa; hombros relajados sin encogimiento.
- **Piernas:** Rodillas en 90° alineadas o ligeramente por debajo de las caderas, con pies completamente apoyados en el suelo o reposapiés.
- **Regla 50-10:** Levántate 2 minutos cada 50 minutos para caminar y estirar los flexores de cadera."""
    },
    {
        "user": "Tengo 8.000 € en cuenta corriente perdiendo valor frente a la inflación y quiero constituir un fondo de emergencia accesible. Dudo entre cuenta remunerada líquida, depósito bancario a 12 meses o fondo monetario. ¿Cuál es la estructura óptima para no asumir riesgo y tener liquidez inmediata?",
        "think": "Contexto: Creación de fondo de emergencia de 8.000 € protegiendo liquidez y capital.\nEvaluación: El depósito penaliza rescates urgentes; la cuenta remunerada es inmediata.\nConclusión: 5.000 € en cuenta remunerada y 3.000 € en fondo monetario.",
        "assistant": """Un fondo de emergencia tiene una misión prioritaria: **preservar el capital y garantizar liquidez inmediata**, no maximizar rendimientos a costa de inmovilizar el dinero.

### Comparativa de Opciones para Fondo de Emergencia

| Vehículo | Rendimiento Típico | Liquidez | Riesgo y Garantía | Idoneidad para Emergencias |
| :--- | :--- | :--- | :--- | :--- |
| **Cuenta Remunerada** | 2,5% - 3,5% TAE | **Inmediata (en segundos)** | Garantizada por FGD (hasta 100k €) | **Excelente (100% líquida)** |
| **Depósito a Plazo Fijo** | 3,0% - 3,7% TAE | Bloqueada o penalizada | Garantizada por FGD | Regular (Penaliza cancelación) |
| **Fondo Monetario** | Euríbor a corto plazo (~3,6%) | 24 - 48 horas laborables | Sin FGD, pero activos de deuda soberana ultra-seguros | Muy buena (Ventaja fiscal por traspaso) |

### Estructura Óptima en 2 Tramos para tus 8.000 €
No coloques todo en una sola alternativa; segmenta según velocidad de necesidad:

1. **Tramo 1: Liquidez Instantánea (5.000 € en Cuenta Remunerada al 3% - 3,5% TAE):**
   - Entidades como Trade Republic, Bankinter, Renault Bank o Sabadell.
   - Disponibilidad 24/7 mediante transferencia o tarjeta ante una avería de coche o urgencia doméstica.
2. **Tramo 2: Rendimiento Estable (3.000 € en Depósito Cancelable sin penalización o Fondo Monetario):**
   - Si eliges fondo monetario (ej. Groupama Trésorerie o DWS Floating Rate), no tributas por los intereses generados si en el futuro decides traspasarlo a fondos indexados.
   - Generarás unos **260 € a 280 € limpios al año** manteniendo la seguridad total de tu patrimonio de seguridad."""
    },
    {
        "user": "En mi huerto urbano en macetas tengo una plaga severa de pulgón negro y cochinilla algodonosa en tomates y albahaca. No quiero usar insecticidas químicos sintéticos porque consumimos las hojas directamente. ¿Qué tratamiento biológico y mecánico es el más eficaz?",
        "think": "Contexto: Plaga de pulgón y cochinilla en plantas comestibles de balcón.\nEvaluación: Los químicos sintéticos dejan residuos tóxicos; el jabón degrada la cutícula del insecto.\nConclusión: Limpieza manual con alcohol y rociado de jabón potásico con neem.",
        "assistant": """La cochinilla algodonosa y el pulgón debilitan la planta succionando savia y segregando melaza. Para erradicarlos de cultivos comestibles sin tóxicos persistentes, aplica este protocolo en 3 fases:

### 1. Ataque Mecánico Inicial (Día 1)
- **Eliminación focalizada de cochinilla:** La cochinilla segrega una capa de cera algodonosa impermeable. Moja un bastoncillo de algodón en **alcohol etílico de 70°** y retira manualmente una por una las masas blancas visibles en axilas y envés de las hojas. El alcohol disuelve la cutícula cerosa al contacto y las deshidrata al instante.
- **Lavado a presión de pulgón:** Con un pulverizador de agua a chorro directo o con la manguera, enjuaga los tallos de albahaca para desalojar mecánicamente las colonias de pulgón.

### 2. Pulverización Biológica: Jabón Potásico + Aceite de Neem
Esta combinación sinérgica es el estándar de oro en agricultura orgánica:
- **Fórmula:** En 1 litro de agua tibia disuelve:
  - 10 ml de **Jabón Potásico** líquido (disuelve el exoesqueleto blando del insecto por contacto).
  - 5 ml de **Aceite de Neem** virgen (actúa como disruptor hormonal y antialimentario bloqueando la muda y reproducción).
- **Modo de aplicación:** Pulveriza profusamente a última hora de la tarde (nunca a pleno sol, para evitar quemaduras por efecto lupa) incidiendo en el **envés de las hojas** y brotes tiernos.
- **Frecuencia:** Repite cada 4 días durante dos semanas hasta cortar el ciclo reproductivo de larvas emergentes.

### 3. Prevención y Seguridad Alimentaria
- Tras aplicar el tratamiento, basta con esperar un plazo de seguridad de **48 horas y lavar con agua las hojas** antes de consumirlas; el jabón potásico y el neem son inocuos para humanos y animales domésticos."""
    },
    {
        "user": "La batería de mi smartphone Android tiene 2 años de uso y su salud estimada ha caído al 81%. Se descarga a media tarde y no quiero gastarme 800 € en un móvil nuevo. ¿Cómo maximizar la autonomía diaria y qué pautas seguir para no acelerar la degradación?",
        "think": "Contexto: Batería degradada al 81% en móvil funcional sin desear comprar nuevo.\nEvaluación: Cambiar la batería oficial cuesta poco; ajustes de pantalla reducen descarga.\nConclusión: Sustitución de celda oficial y límites de carga al 85%.",
        "assistant": """Un 81% de salud de batería indica que las celdas de iones de litio han superado unos 600 ciclos de carga y su resistencia interna ha aumentado, lo que provoca caídas bruscas de voltaje. Tienes dos líneas de actuación:

### 1. La Solución Definitiva: Reemplazo de Batería (~40 € - 65 €)
- No compres un móvil nuevo si el terminal funciona fluido: acude a un servicio técnico oficial o taller especializado y solicita un **cambio de batería original**.
- Por menos del 8% del coste de un teléfono nuevo, tu smartphone recuperará el 100% de su autonomía y rendimiento máximo por 2 o 3 años más.

### 2. Medidas Inmediatas de Ahorro Energético (Configuración del Sistema)
- **Frecuencia de refresco dinámica:** Si la pantalla está fija a 120 Hz, cámbiala a 60 Hz estándar o modo dinámico (ahorra entre un 15% y un 20% de batería al día).
- **Tema oscuro en paneles AMOLED:** En pantallas OLED los píxeles negros están completamente apagados y consumen cero energía. Activa el modo oscuro en el sistema y en aplicaciones de alta lectura.
- **Desactivar búsqueda en segundo plano:** Ve a Ajustes > Conectividad y desactiva la "Búsqueda permanente de redes Wi-Fi y dispositivos Bluetooth cercanos".
- **Restricción de apps vampiro:** En Ajustes de Batería, identifica qué apps consumen en segundo plano (redes sociales, widgets) y márcalas en "Restricción en segundo plano / suspensión profunda".

### 3. Pautas para no Degradar la Celda de Litio
- **Regla del 20% - 80%:** Evita que el móvil baje del 15% y desconéctalo al llegar al 85%. Los extremos de carga generan estrés químico por alto voltaje en los electrodos.
- **Evita el sobrecalentamiento:** No uses juegos pesados ni GPS mientras el móvil se carga con carga rápida."""
    },
    {
        "user": "Una familia de 3 personas tiramos comida casi todas las semanas (verduras marchitas en el cajón, sobras olvidadas en la nevera). ¿Qué método de organización de menús y nevera podemos implantar para reducir el desperdicio alimentario a cero?",
        "think": "Contexto: Desperdicio sistemático de alimentos en familia de tres miembros.\nEvaluación: Comprar sin revisar despensa y falta de visibilidad en nevera causan pérdidas.\nConclusión: Menú inverso según caducidades, regla FIFO y bandeja de consumo prioritario.",
        "assistant": """El 90% del desperdicio doméstico se debe a comprar sin planificar y a la falta de visibilidad en el frigorífico. Aplica este sistema de 3 fases para reducirlo a cero:

### 1. La Planificación Inversa de Menús (Antes de comprar)
1. **Auditoría de despensa de 5 minutos:** Antes de hacer la lista de la compra, abre la nevera y el congelador. El menú semanal debe empezar por los ingredientes que van a caducar esta semana.
2. **Menú de 5 días (no de 7):** Planifica comidas solo de lunes a viernes. Deja sábado y domingo libres para consumir sobras acumuladas o comidas fuera improvisadas.
3. **Lista cerrada por categorías:** Compra solo lo necesario para ese menú. Si una receta pide apio, planifica una crema de verduras para aprovechar el resto del manojo.

### 2. Organización Visual de la Nevera (Regla FIFO)
- **First In, First Out (Lo primero que entra es lo primero que sale):** Al colocar la compra nueva, pasa los yogures y verduras antiguas al frente y coloca lo recién comprado detrás.
- **Caja de 'Cómeme Primero':** Reserva un taper o bandeja transparente en el estante central con una etiqueta visible. Pon allí quesos abiertos, restos de carne cocinada y verduras sueltas. Cualquier merienda o almuerzo rápido debe salir de esa caja.
- **Conservación adecuada de vegetales:** No laves las hojas verdes antes de guardarlas; envuélvelas en papel absorbente dentro de un recipiente hermético en el cajón de verduras para evitar que la humedad las pudra.

### 3. El Día de 'Reciclaje Gastronómico'
- Designa el **jueves por la noche como cena de aprovechamiento**:
  - Salteado wok con todos los restos de verduras y arroz blanco.
  - Tortilla de verduras o revuelto con tacos de embutido.
  - Quiche casera o empanada rápida con restos de pollo asado.
- Si ves que no vas a consumir un plato cocinado en 48 horas, mételo de inmediato en porciones individuales al congelador con fecha etiquetada."""
    },
    {
        "user": "Tengo 29 años, trabajo 40 horas semanales a jornada completa y he decidido empezar un máster universitario online de 60 créditos ECTS que exige unas 15-20 horas de estudio semanales. ¿Cómo diseñar un calendario sostenible para no quemarme al segundo mes?",
        "think": "Contexto: Compatibilizar empleo a jornada completa con máster exigente de 60 ECTS.\nEvaluación: Estudiar tras la jornada agota; concentrar en fines de semana destruye el descanso.\nConclusión: Bloques matutinos de estudio antes de trabajar y domingo libre de desconexión.",
        "assistant": """Afrontar 60 horas semanales de actividad combinada (40 laborales + 18 académicas) sin sufrir burnout requiere **proteger la energía mental**, no solo gestionar el reloj:

### 1. La Estrategia del Bloque Matutino (Energía Fresca)
- Intentar estudiar 3 horas seguidas después de las 19:00 tras 8 horas de oficina resulta en baja retención y frustración por fatiga de decisiones.
- **Despierta 75 minutos antes:** De 06:45 a 08:00 ejecuta **1 hora de estudio profundo (Deep Work)** con el cerebro descansado y sin notificaciones de trabajo.
- De lunes a jueves: 1 hora diaria a primera hora = **4 horas de avance de máxima calidad a la semana**.

### 2. Calendario Semanal Sostenible (Bloques de Trabajo)

| Franja | Lunes a Jueves | Viernes | Sábado | Domingo |
| :--- | :--- | :--- | :--- | :--- |
| **Mañana (07:00 - 08:00)** | 1 h Estudio / Lecturas | Libre | **08:30 - 13:30 (5 h intensivas con pausas)** | **Libre (Recuperación total)** |
| **Tarde laboral** | Jornada de trabajo | Jornada de trabajo | Tarde libre / Social | Libre / Ocio / Familia |
| **Noche (20:30 - 21:30)** | 1 h Tareas ligeras o foros | Libre / Desconexión | Noche libre | Organización semanal (30 min) |

- **Total horas semanales:** 4 h (mañanas L-J) + 4 h (noches L-J) + 5 h (sábado mañana) = **13 a 15 horas reales y productivas**.

### 3. La Regla Sagrada del Domingo de Desconexión
- **El domingo no se toca el máster ni el trabajo:** El cerebro necesita un ciclo completo de recuperación cognitiva para evitar la apatía y el agotamiento crónico.
- Si una entrega urgente exige trabajar un domingo de forma excepcional, compensa descansando la tarde del viernes."""
    },
    {
        "user": "Vivimos en un primer piso sobre una calle peatonal con terrazas de bares que generan ruido constante de voces y risas hasta las 00:30. Tenemos ventanas de doble acristalamiento estándar pero el ruido se cuela de forma molesta en el salón y dormitorio. ¿Cómo mitigar el ruido con medidas no invasivas?",
        "think": "Contexto: Ruido aéreo de terrazas que entra en vivienda con ventanas dobles.\nEvaluación: El cajón de persiana y rendijas actúan como puente acústico directo.\nConclusión: Forrado fonoabsorbente de cajones, burletes de presión y cortinas densas.",
        "assistant": """En un primer piso sobre bares, el ruido de voces es **ruido aéreo de media frecuencia (500 Hz a 2000 Hz)**. Si las ventanas ya son de doble cristal, el sonido no entra atravesando la pared, sino por los dos puntos más débiles de la fachada:

### 1. El Cajón de la Persiana (El coladero acústico principal)
El 60% del ruido exterior suele colarse por el hueco hueco de la persiana, que actúa como una caja de resonancia directa:
1. Abre la tapa del cajón de la persiana.
2. Forra el interior con una combinación de **lámina viscoelástica de alta densidad (tipo Tecsound o acústica pesada) pegada a un panel de espuma absorbente piramidal o lana de roca flexible**.
3. Sella la ranura por donde entra la cinta de la persiana con un pasacintas acústico con cepillo hermético.

### 2. Estanqueidad de los Cierres de Ventana
El sonido se comporta como el agua: por una rendija de 1 milímetro se cuela el 40% del ruido:
- Si las ventanas son correderas, su aislamiento acústico es intrínsecamente bajo. Sustituye los cepillos desgastados de las guías por burletes nuevos de felpa de alta densidad.
- Si son abatibles u oscilobatientes, ajusta los bulones de cierre con una llave Allen para aumentar la presión de la hoja contra el marco e instala un burlete perimetral de silicona tubular.

### 3. Cortinas Fonoabsorbentes Pesadas
- Instala cortinas técnicas multicapa de alto gramaje (más de 600 g/m² con forro de terciopelo o tejido fonoabsorbente denso).
- Deben cubrir desde el techo hasta rozar el suelo y desbordar 15 cm a cada lado del hueco de la ventana. Reducen la reverberación interna y amortiguan entre 4 y 7 dB del murmullo de fondo."""
    },
    {
        "user": "He notado que la ropa sale de la lavadora con olor a humedad y en ocasiones con pequeñas manchas grisáceas, a pesar de que uso detergente y suavizante de marca. La lavadora tiene 3 años. ¿Cómo puedo sanearla a fondo y eliminar la causa raíz del problema?",
        "think": "Contexto: Mal olor y manchas grises en ropa lavada en máquina de 3 años.\nEvaluación: Lavados fríos y suavizante crean moho en goma y tambor.\nConclusión: Ciclo a 90 °C con percarbonato, purga de filtro y secado de puerta.",
        "assistant": """El olor a humedad y los residuos grisáceos son causados por la proliferación de un **biofilm bacteriano y hongos** acumulados en la goma del tambor y el circuito de desagüe, provocado habitualmente por lavar siempre en frío (<30 °C) y abusar del suavizante:

### 1. Protocolo de Choque de Limpieza Profunda
1. **Limpieza manual de la goma del fuelle:**
   - Separa con los dedos los pliegues de la goma de la puerta. Encontrarás agua estancada y lodo negro de moho.
   - Limpia enérgicamente con una bayeta empapada en lejía concentrada o peróxido de hidrógeno y retira restos de monedas, pelos o pelusas atrapados.
2. **Desinfección térmica a 90 °C:**
   - Vierte 3 cucharadas soperas de **percarbonato de sodio** directamente en el tambor vacío (o 1 litro de vinagre de limpieza al 10% de acidez).
   - Programa un **ciclo largo de algodón a 90 °C** sin carga de ropa. El agua hirviendo disuelve las grasas adheridas a la cruceta del tambor y el percarbonato esteriliza todo el circuito interno.
3. **Purga del filtro inferior:**
   - Coloca una bandeja y una toalla en el suelo bajo la tapa inferior de la lavadora.
   - Desenrosca el filtro, drena el agua residual y enjuaga la hélice de la bomba bajo el grifo retirando cualquier obstrucción.

### 2. Cambios de Hábito para que no Reaparezca
- **Deja la puerta y el cajetín abiertos siempre tras cada lavado:** La humedad no puede evaporarse con la puerta cerrada.
- **Reduce el suavizante:** El suavizante está formulado con grasas animales o sintéticas que se adhieren a las paredes plásticas de la cuba; sustitúyelo por 30 ml de vinagre de manzana o ácido cítrico en el cajetín de aclarado (suaviza la ropa sin dejar olor ni engrasar el tambor).
- **Ejecuta un lavado caliente mensual:** Realiza al menos un lavado al mes de toallas o sábanas a 60 °C para esterilizar el electrodoméstico de manera regular."""
    },
    {
        "user": "Quiero deshacerme de la mitad de mis pertenencias antes de mudarme de un piso de 90 m² a uno de 45 m², pero me paraliza el apego emocional a objetos, libros y ropa sin usar. ¿Qué metodología sistemática puedo aplicar para depurar pertenencias sin arrepentirme?",
        "think": "Contexto: Mudanza reduciendo espacio a la mitad bloqueada por apego a objetos.\nEvaluación: Decidir elemento por elemento satura la voluntad sin reglas claras.\nConclusión: Caja de cuarentena temporal a 6 meses y regla de uso anual.",
        "assistant": """Reducir el espacio físico a la mitad exige pasar de un enfoque reactivo a un **algoritmo de decisión desapegado**:

### 1. La Técnica de la 'Caja de Cuarentena' (Eliminar la ansiedad de pérdida)
- Para objetos con carga emocional o dudas intensas (ropa cara que no usas, recuerdos de viajes, libros especiales):
  - Mételos en una caja de cartón cerrada, precíntala y escribe con rotulador la **fecha dentro de 6 meses**.
  - Si en 6 meses no has necesitado abrir la caja para buscar algo específico, queda demostrado empíricamente que tu vida funciona perfectamente sin ellos. Dónala o regálala directamente sin volver a revisar el interior.

### 2. Algoritmo de Decisión en 4 Filtros Rígidos
Toma cada objeto y pásalo por este árbol de decisión binario:
1. **Filtro de temporalidad:** ¿Lo he utilizado en los últimos 12 meses? Si la respuesta es no, se va. Las excepciones climáticas no aplican si han pasado 4 estaciones completas.
2. **Filtro de sustituibilidad (Regla 20/20):** Si puedo reemplazarlo en menos de 20 minutos por menos de 20 euros cuando realmente me haga falta en el futuro, no merece ocupar metros cuadrados en un piso de 45 m².
3. **Filtro de duplicidad:** Quédate con tu mejor ejemplar de cada categoría (un juego de toallas favorito, tus dos sartenes más polivalentes) y elimina copias redundantes.

### 3. Digitalización de Recuerdos Emocionales
- El valor emocional está en el recuerdo mental, no en el plástico o papel:
  - Fotografía con buena luz cuadernos del colegio, cartas, diplomas o trofeos.
  - Guárdalos en un álbum digital de alta resolución en la nube. Ocupan cero metros cuadrados y podrás verlos siempre que quieras sin acumular polvo."""
    },
    {
        "user": "Tengo 3 horas libres cada sábado y quiero preparar comidas para los almuerzos de lunes a viernes (batch cooking) para una persona, con presupuesto de 25 € semanales, alto en proteínas y sin que la comida quede reseca el jueves. ¿Qué plan de cocina y menú estructurar?",
        "think": "Contexto: Cocinar 5 almuerzos ricos en proteína con 25 € y 3h disponibles.\nEvaluación: Carnes a la plancha se resecan rápido; guisos en salsa retienen jugosidad.\nConclusión: Cocinado simultáneo al horno de contramuslos con verduras y legumbres salteadas.",
        "assistant": """Para que la comida aguante fresca, jugosa y rica de lunes a viernes sin resecare, la clave reside en cocinar con **salsas, humedad y guisos en lugar de carnes a la plancha**.

### 1. Menú Semanal (Presupuesto total: ~22 €)
- **Base de proteína:** 1 kg de contramuslos de pollo deshuesados (~6 €) + 2 botes de garbanzos cocidos (~1,80 €) + 6 huevos camperos (~1,80 €) + 2 latas de atún en aceite de oliva (~2,20 €).
- **Base de carbohidratos complejos:** Arroz integral y patatas medianas (~3 €).
- **Vegetales:** Bandeja de champiñones, calabacines, cebollas y pimientos rojos (~7 €).

### 2. Plan de Cocinado en Paralelo (2 horas y media de ejecución)
- **Minuto 0 a 15 (Encendido y corte):** Precalienta el horno a 200 °C. Corta los calabacines, cebollas y pimientos en cubos medianos.
- **Minuto 15 a 60 (Horno en dos alturas):**
  - *Bandeja 1:* Los contramuslos de pollo marinados con aceite, pimentón dulce, ajo en polvo y salsa de tomate triturado (quedan tiernos y no se resecan en toda la semana).
  - *Bandeja 2:* Las verduras troceadas con un chorrito de aceite de oliva y sal.
- **Minuto 20 a 50 (Fuegos):**
  - *Fuego 1:* Cuece 300 g de arroz integral en abundante agua con laurel.
  - *Fuego 2:* Saltea en sartén amplia los garbanzos escurridos con champiñones laminados y tacos de jamón serrano.

### 3. Distribución de los 5 Almuerzos en Tapers
- **Lunes y Martes (En nevera):**
  - *Lunes:* Pollo guisado al horno con arroz integral y verduras asadas.
  - *Martes:* Salteado tibio de garbanzos con champiñones y huevo pochado/cocido.
- **Miércoles, Jueves y Viernes (Congelador -> Nevera la noche anterior):**
  - *Miércoles:* Contramuslos de pollo deshilachados con pimientos asados y patata asada aplastada.
  - *Jueves:* Garbanzos salteados con atún y verduras al horno.
  - *Viernes:* Arroz salteado con pollo, verduras y salsa de soja.
- **Conservación:** Todo plato con salsa y contramuslo conserva la jugosidad íntegra tras 5 días o al descongelarse en microondas con tapa perforada."""
    },
    {
        "user": "Mi hijo adolescente pasa más de 6 horas diarias frente a pantallas jugando videojuegos y viendo vídeos cortos, lo que ha provocado una caída notable en sus calificaciones y apatía general. Cuando intentamos limitar el móvil se generan discusiones violentas. ¿Cómo diseñar un plan de desconexión consensuado sin que se convierta en una guerra diaria?",
        "think": "Contexto: Exceso de pantallas en adolescente con conflicto familiar y bajo rendimiento.\nEvaluación: Prohibición tajante desata hostilidad; faltan límites técnicos pactados.\nConclusión: Desconexión automática en router, estación de carga externa y deporte presencial.",
        "assistant": """El uso compulsivo de vídeos cortos y videojuegos activa bucles de dopamina diseñados para ser adictivos. Abordarlo desde la confrontación y el castigo unilateral casi siempre fracasa. Aplica esta estrategia de mediación y arquitectura del entorno:

### 1. Cambiar la Dinámica: De la Guerra al Pacto Consensuado
- **Conversación en momento de calma (no tras un conflicto):** Siéntate con él un fin de semana fuera de casa. Reconoce que las plataformas están diseñadas para enganchar y pregúntale cómo se siente con sus notas y su energía diaria.
- **Establecer un contrato familiar mutuo:** Las reglas deben aplicar a todos los miembros del hogar, incluidos los adultos (los padres tampoco pueden mirar el móvil en la mesa).

### 2. Modificaciones Ambientales Físicas (Cero fricción de discusión)
- **Zona de carga centralizada fuera del dormitorio:** A las 22:00 todos los móviles y consolas se depositan en una estación de carga común en el pasillo o salón. El móvil jamás duerme en la mesilla del dormitorio (compra un despertador analógico de 5 €).
- **Automatización técnica de cortes:** Configura en el router el apagado automático del Wi-Fi para sus dispositivos a una hora fijada de común acuerdo, o usa el control parental del sistema (Family Link / Apple Screen Time) con límites de tiempo prefijados por aplicación. Cuando la desconexión la ejecuta el software de forma automática, desaparece la discusión directa entre personas.

### 3. Sustitución de Actividades (Llenar el vacío dopaminérgico)
- Si eliminas 3 horas de pantallas sin ofrecer alternativa, el adolescente experimenta un síndrome de abstinencia y aburrimiento insoportable.
- Apúntalo a un deporte colectivo o actividad presencial que le entusiasme (artes marciales, baloncesto, escalada, robótica) que ocupe las tardes con interacción humana cara a cara."""
    },
    {
        "user": "Tengo que organizar las vacaciones familiares de verano de 10 días para 4 personas (dos adultos y dos niños de 8 y 11 años) con un presupuesto estricto de 1.600 € en total. Queremos naturaleza, playa y actividades culturales sin arruinarnos en comidas fuera. ¿Cómo planificar el destino, alojamiento y logística?",
        "think": "Contexto: Vacaciones de 10 días para familia de 4 con 1.600 € de tope total.\nEvaluación: Hoteles y restaurantes disparan el gasto; apartamento con cocina ahorra 700 €.\nConclusión: Costa secundaria en bungalow o casa rural con cocina propia y picnics.",
        "assistant": """Para disfrutar de 10 días inolvidables con 4 miembros por **1.600 € (160 €/día para toda la familia)**, la clave matemática es controlar el alojamiento con cocina y evitar la hostelería de playa masificada:

### 1. Elección del Destino Estratégico (Segunda línea de costa)
- Evita los puntos turísticos masificados (Costa del Sol, Baleares, Levante masivo).
- **Destinos recomendados:** La costa de Asturias/Cantabria interior (a 15-20 minutos de la playa) o la Costa da Morte y rías altas en Galicia, o el interior de Castellón/Tarragona. Te permiten alternar excursiones de montaña, calas naturales y pueblos históricos con precios locales reales.

### 2. Alojamiento con Cocina (Presupuesto: 750 € a 850 €)
- **Bungalow en camping familiar o apartamento en pueblo a 15 km del mar:**
  - El alquiler de un apartamento vacacional de 2 dormitorios o mobil-home equipado con cocina cuesta unos **75 € - 85 €/noche** si se reserva con antelación en junio o primera quincena de julio.
  - Disponer de cocina propia ahorra más de 700 € en comidas respecto a un hotel.

### 3. Distribución del Presupuesto (1.600 € cerrados)
- **Alojamiento (10 noches):** **800 €**.
- **Transporte (combustible coche particular + peajes para ~1.200 km):** **220 €**.
- **Alimentación (compra en supermercado local + desayunos y cenas en casa):** **350 €**.
- **Comidas fuera puntuales (menú del día o tapas en pueblos locales, 3 ocasiones):** **130 €**.
- **Entradas culturales y actividades (castillos, museos naturales, kayak):** **100 €**.
*Total: 1.600 €.*

### 4. Logística de Actividades Gratuitas
- Prepara pic-nic de playa con bocadillos caseros, fruta y agua fresca en nevera portátil: los niños comen en la arena encantados y eliminas el gasto inflado de los chiringuitos.
- Consulta las webs de los ayuntamientos locales para rutas de senderismo señalizadas y visitas a cuevas o fortificaciones con acceso libre."""
    }
]
