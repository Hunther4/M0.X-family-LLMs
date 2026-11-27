# -*- coding: utf-8 -*-
"""Dataset de análisis de textos, retórica, falacias y argumentación (sin fluff)."""

ANALYSIS_SAMPLES = [
    {
        "user": "Analiza el siguiente argumento e identifica la falacia lógica cometida:\n«No deberíamos aprobar la ley que incentiva el uso de vehículos eléctricos urbanos. Si subsidiamos esos autos, la gente dejará de usar el transporte público por completo; al colapsar el metro y los autobuses, las ciudades se llenarán de cables y baterías por doquier, se agotará la red eléctrica nacional y terminaremos en apagones constantes que destruirán la economía del país».",
        "assistant": r"""El argumento incurre en la **falacia de la pendiente resbaladiza** (*slippery slope*), complementada con rasgos de **reducción al absurdo espuria**.

### Mecanismo de la falacia
La falacia consiste en afirmar que la adopción de una medida inicial moderada (incentivar el uso de vehículos eléctricos) desencadenará inexorablemente una cadena sucesiva y desastrosa de eventos catastróficos (abandono total del transporte público $\to$ colapso de infraestructuras $\to$ colapso de la red eléctrica $\to$ ruina económica nacional), sin aportar **ninguna evidencia causal o empírica** que demuestre que cada eslabón de la cadena conduce necesariamente al siguiente.

### Puntos de ruptura causal en el argumento
1. **Falso encadenamiento necesario**: La adopción de subsidios para autos eléctricos urbanos no implica el cese automático ni total del uso de redes de metro y autobuses; coexisten como modos complementarios de transporte.
2. **Exageración de magnitudes**: Asume que la demanda energética superará instantáneamente la capacidad de generación y distribución nacional, omitiendo la regulación de tarifas horarias de carga nocturna y el refuerzo progresivo de redes.
3. **Salto a la catástrofe final**: El paso de una política de electromovilidad a la «destrucción de la economía por apagones» es una inferencia ilegítima basada en el miedo y no en proyecciones macroeconómicas o energéticas contrastables."""
    },
    {
        "user": "Explica la diferencia técnica entre metáfora, metonimia y sinécdoque con un ejemplo de cada una.",
        "assistant": r"""Estas tres figuras de traslación semántica (tropos) sustituyen un término propio por uno figurado, pero operan sobre principios lógicos y asociativos completamente distintos:

### 1. Metáfora (Relación de analogía o semejanza)
- **Principio**: Opera en el eje paradigmático o de selección. Sustituye un término real por uno imaginario basándose en una relación de **semejanza cualitativa, estructural o perceptual** entre dos dominios conceptuales distintos que no tienen contacto físico ni contigüidad.
- **Ejemplo**: *«Las perlas de tu boca»* (semejanza de blancura, brillo y alineación entre perlas y dientes; pertenecen a reinos conceptuales disjuntos).

### 2. Metonimia (Relación de contigüidad causal, temporal o espacial)
- **Principio**: Opera en el eje sintagmático o de combinación. Sustituye un término por otro perteneciente al mismo campo semántico, basándose en una relación de **contigüidad real objetiva**:
  - *Causa por efecto*: «Vivir de su trabajo» (de los frutos/dinero del trabajo).
  - *Autor por obra*: «Subastaron un Picasso» (subastaron un cuadro pintado por Picasso).
  - *Continente por contenido*: «Bebió una copa de vino» (bebió el líquido contenido en la copa).
  - *Instrumento por agente*: «Es el mejor pincel del taller» (es el pintor más hábil).

### 3. Sinécdoque (Relación cuantitativa de inclusión)
- **Principio**: Es una especie particular de metonimia basada estrictamente en una **relación de inclusión cuantitativa o jerárquica** (cuanto-cuantitativa):
  - *La parte por el todo*: «Cien cabezas de ganado» (cien animales enteros), «Faltan brazos para la cosecha» (faltan trabajadores completos).
  - *El todo por la parte*: «La ciudad celebró el campeonato» (los ciudadanos que salieron a la calle, no la infraestructura urbana).
  - *Género por especie*: «El mortal teme a la muerte» (el ser humano en particular)."""
    },
    {
        "user": "¿En qué consiste la falacia del hombre de paja (*straw man*) y cómo se desmonta formalmente en un debate?",
        "assistant": r"""La **falacia del hombre de paja** es una estratagema argumentativa deshonesta que consiste en distorsionar, simplificar en exceso, exagerar o caricaturizar deliberadamente la postura real de un oponente, para luego atacar y demoler esa versión deformada (el «hombre de paja») en lugar del argumento original sustentado por el interlocutor.

### Esquema lógico formal
1. El interlocutor A sostiene la postura $P$.
2. El interlocutor B reformula $P$ como $P'$, donde $P'$ es una versión extrema, absurda o insostenible de $P$.
3. El interlocutor B refuta enérgicamente $P'$.
4. B concluye falazmente que ha derrotado la postura original $P$.

### Ejemplo clásico
- **Postura real A**: «Deberíamos regular de manera más estricta los límites de emisión de partículas diésel en el centro urbano para reducir afecciones respiratorias infantiles».
- **Hombre de paja B**: «Mi oponente quiere prohibir el derecho a circular libremente por la ciudad, confiscar los vehículos de las familias trabajadoras y obligar a todos a ir en bicicleta bajo la lluvia».

### Protocolo para desmontarla formalmente
1. **Evidenciar la discrepancia textual**: Citar textualmente la afirmación propia original frente a la tergiversación formulada por el oponente.
2. **Denunciar explícitamente el cambio de objeto**: Señalar que el adversario ha respondido a una proposición inventada por él mismo y no a la tesis sometida a discusión.
3. **Reconducir la carga de la prueba**: Exigir al oponente que defina y refute los méritos técnicos específicos de la proposición real antes de concederle validez a su réplica."""
    },
    {
        "user": "Analiza el siguiente texto e identifica la tesis principal, los dos argumentos de soporte y la conclusión:\n«La preservación de los bosques tropicales primarios no puede concebirse únicamente como una causa ética de conservación biológica; constituye un imperativo económico global. En primer lugar, los bosques albergan reservas genéticas irremplazables de las cuales dependen sectores industriales críticos, desde la síntesis de fármacos hasta la biotecnología agrícola de resistencia a plagas. En segundo lugar, actúan como sumideros masivos de carbono cuya degradación liberaría gigatoneladas de dióxido de carbono a la atmósfera, provocando perturbaciones climáticas extremas cuyos costes de mitigación e indemnización desbordarían las capacidades fiscales de los Estados. Por consiguiente, destinar fondos multilaterales a la protección de estas áreas debe registrarse en las cuentas públicas como una inversión estratégica de reducción de riesgos sistémicos y no como un gasto asistencial».",
        "assistant": r"""### Análisis estructural del texto

1. **Tesis Principal**:
   La preservación de los bosques tropicales primarios no es meramente un deber ético-conservacionista, sino un **imperativo de seguridad económica y financiera global**.

2. **Argumentos de Soporte**:
   - **Argumento 1 (Capital biotecnológico y farmacológico)**: Los bosques primarios constituyen reservorios irremplazables de diversidad genética que alimentan directamente cadenas de valor industriales de alto impacto económico, en particular el desarrollo de nuevos medicamentos y la ingeniería agronómica frente a patógenos.
   - **Argumento 2 (Prevención de riesgo macroeconómico y pasivos climáticos)**: La deforestación de estos ecosistemas liberaría volúmenes colosales de $CO_2$ almacenado, detonando eventos climáticos extremos cuyos daños materiales y costes de adaptación superarían con creces los recursos presupuestarios de los Estados (evitación de pérdidas catastróficas).

3. **Conclusión**:
   La asignación de financiamiento multilateral para la protección de bosques tropicales primarios debe reclasificarse contable y políticamente como una **inversión estratégica en cobertura de riesgos sistémicos globales**, abandonando el marco conceptual de gasto benéfico o asistencial."""
    },
    {
        "user": "¿Cuál es la diferencia entre antítesis, oxímoron y paradoja en análisis literario y retórico?",
        "assistant": r"""Aunque las tres figuras retóricas explotan la confrontación de ideas opuestas, operan en niveles sintácticos y lógicos de complejidad creciente:

### 1. Antítesis (Nivel sintáctico-conceptual)
- **Definición**: Yuxtaposición o contraposición de dos palabras, frases o sintagmas de significados opuestos en oraciones o versos contiguos, sin que exista contradicción lógica en la realidad.
- **Estructura**: Mantiene la coherencia lógica formal; simplemente resalta el contraste entre dos realidades distintas.
- **Ejemplo**: *«Es tan corto el amor y es tan largo el olvido»* (Pablo Neruda). Corto y largo se oponen paralelamente sin violentar el sentido de la verdad.

### 2. Oxímoron (Nivel semántico-sintagmático estrecho)
- **Definición**: Unión íntima, en un único sintagma (habitualmente un sustantivo acompañado de un adjetivo contradictorio o incompatible), de dos conceptos que se excluyen mutuamente según su significado literal.
- **Estructura**: Fusión directa e inmediata de contrarios en una o dos palabras.
- **Ejemplo**: *«Fuego helado»*, *«Un silencio elocuente»*, *«Luz oscura»*, *«Copia original»*.

### 3. Paradoja (Nivel lógico-discursivo amplio)
- **Definición**: Expresión o enunciado aparentemente absurdo, contradictorio o imposible según el sentido común o la lógica tradicional, pero que tras un análisis reflexivo profundo encierra una verdad válida, reveladora o filosóficamente consistente.
- **Estructura**: Implica una proposición completa o un pensamiento discursivo complejo.
- **Ejemplo**: *«Solo sé que no sé nada»* (Sócrates), o *«Vivo sin vivir en mí, y tan alta vida espero, que muero porque no muero»* (Santa Teresa de Jesús). La contradicción entre morir y desear la vida se disuelve en el marco trascendente de la fe mística."""
    },
    {
        "user": "Explica la falacia ad hominem circunstancial frente al ad hominem abusivo con un ejemplo para cada una.",
        "assistant": r"""El argumento *ad hominem* (ataque a la persona) es una falacia informal que rechaza una tesis atacando alguna característica personal del proponente en lugar de refutar la validez lógica o fáctica de su argumento. Presenta dos modalidades principales:

### 1. Ad Hominem Abusivo (Directo)
- **Mecanismo**: Descalifica la tesis mediante insultos directos, descalificaciones morales, intelectuales o de carácter dirigidas contra el interlocutor, las cuales son irrelevantes para la verdad objetiva de la proposición.
- **Ejemplo**:
  - *Postura*: «El informe del economista demuestra con datos estadísticos auditados que la deuda pública superará el límite sostenible el próximo trimestre».
  - *Ataque abusivo*: «Ese análisis carece de validez porque ese economista es una persona arrogante, amargada y con pésimo carácter personal».
  - *Fallo lógico*: La soberbia o simpatía del autor no altera la veracidad matemática de las series temporales de la deuda.

### 2. Ad Hominem Circunstancial (Indirecto o por conflicto de interés)
- **Mecanismo**: No ataca directamente la dignidad de la persona, sino sus **circunstancias personales, vínculos laborales, ideológicos, religiosos o intereses financieros**, sugiriendo que su postura es necesariamente falsa o no meritoria por estar 'contaminada' por su conveniencia personal.
- **Ejemplo**:
  - *Postura*: «El ingeniero ambiental ha demostrado con mediciones espectrométricas que el nuevo filtro cerámico reduce las emisiones de azufre en un 90%».
  - *Ataque circunstancial*: «Por supuesto que concluye eso, si trabaja para una empresa del sector metalúrgico que vende dichos filtros; su informe es automáticamente falso».
  - *Fallo lógico*: Si bien el interés económico exige un control metodológico riguroso y replicación independiente, el conflicto de interés por sí mismo **no convierte en falsa una medición técnica verificable**."""
    },
    {
        "user": "¿En qué consiste el modelo de argumentación de Stephen Toulmin y cuáles son sus seis elementos?",
        "assistant": r"""En *Los usos de la argumentación* (1958), el filósofo británico Stephen Toulmin propuso un modelo estructural práctico para evaluar la validez de los argumentos en el discurso real (derecho, ciencia, ética), superando la rigidez del silogismo formal aristotélico.

El modelo articula seis componentes interconectados:

```
[Datos / Evidencia] ------------> por tanto ------------> [Aserción / Conclusión]
        |                                                       |
     debido a                                                a menos que
        |                                                       |
   [Garantía]                                              [Reserva]
        |
  soportada por
        |
   [Respaldo]
```

### Los seis elementos constitutivos

1. **Aserción o Tesis (*Claim*)**:
   Es la conclusión o afirmación que se pretende defender y que requiere ser aceptada por el auditorio.
2. **Evidencia o Datos (*Data / Grounds*)**:
   Hechos empíricos, observaciones, estadísticas o información verificable que fundamentan de manera directa la aserción.
3. **Garantía (*Warrant*)**:
   Regla, principio, ley natural o justificación conceptual que autoriza el paso lógico legítimo desde los datos hacia la aserción («Si ocurre X dato, se sigue justificadamente Y conclusión»).
4. **Respaldo (*Backing*)**:
   Cuerpo de conocimiento explícito, teoría científica, jurisprudencia, normas jurídicas o estudios estadísticos que otorgan solidez y credibilidad a la garantía.
5. **Cualificador modal (*Qualifier*)**:
   Término adverbial o modal que explicita el grado de fuerza o certeza con el que se sostiene la conclusión (*probablemente, con alta certeza, presumiblemente*).
6. **Reserva o Excepción (*Rebuttal*)**:
   Condiciones excepcionales o circunstancias específicas bajo las cuales la garantía dejaría de operar y la conclusión no resultaría válida."""
    },
    {
        "user": "Analiza el siguiente texto e identifica la falacia cometida:\n«El sospechoso afirma que no estuvo presente en el lugar del robo a las 22:00 horas porque se encontraba cenando en un restaurante a cinco kilómetros de allí. Sin embargo, no ha presentado el ticket fiscal de consumo ni testigos que confirmen haberlo visto cenar en ese local. Por consiguiente, queda probado más allá de toda duda que estuvo en el lugar del robo y es culpable del delito».",
        "assistant": r"""El razonamiento incurre de forma manifiesta en la **falacia de apelación a la ignorancia** (*argumentum ad ignorantiam*), combinada en el ámbito jurídico con una **inversión ilegítima de la carga de la prueba**.

### Análisis de la incorrección lógica
1. **Estructura del error**: Consiste en sostener que una proposición es definitivamente verdadera (o probada) por el mero hecho de que no se ha demostrado de manera concluyente su contraria:
   - Premisa: «No se ha demostrado documentalmente que el sospechoso estuviera cenando en el restaurante».
   - Inferencia falaz: «Por lo tanto, queda probado que estaba en la escena del crimen y es culpable».
2. **Ausencia de prueba $\neq$ Prueba de ausencia**: Que un individuo no pueda probar dónde se encontraba a una hora determinada solo acredita una falta de información o laguna probatoria; en modo alguno constituye evidencia positiva de que se hallara en otro sitio específico cometiendo un delito.
3. **Inversión de la carga procesal (Presunción de inocencia)**: En lógica jurídica y derecho penal, quien formula la imputación de culpabilidad asume la carga inexcusable de aportar pruebas materiales directas de cargo. Transferir al imputado la exigencia de acreditar su inocencia bajo apercibimiento de declararlo culpable convierte la ignorancia en prueba incriminatoria."""
    },
    {
        "user": "¿Qué es la elipsis en redacción y estilística y cómo contribuye a la cohesión textual sin generar ambigüedad?",
        "assistant": r"""La **elipsis** es un mecanismo sintáctico y estilístico de cohesión textual que consiste en la omisión deliberada de uno o varios elementos oracionales (palabras o sintagmas) que se encuentran sintáctica y semánticamente presentes en la estructura profunda, pero que se omiten en la superficie discursiva por ser inequívocamente deducibles a partir del contexto previo o situacional.

### Tipos fundamentales
- **Elipsis nominal**: Omisión del sustantivo o núcleo del sintagma nominal:
  - *Ejemplo*: «Compró tres libros técnicos y leyó dos [libros técnicos] en una semana».
- **Elipsis verbal**: Omisión del verbo ya mencionado en la proposición anterior:
  - *Ejemplo*: «La física estudia las leyes de la materia; la sociología [estudia], los fenómenos colectivos».

### Contribución a la cohesión y economía verbal
1. **Eliminación de redundancias mecánicas**: Evita la fatiga lectora y la monotonía sintáctica provocada por la reiteración abusiva de términos idénticos en periodos oracionales cercanos.
2. **Agilidad y tensión rítmica**: Concentra la atención semántica en la información nueva (*rema*) al eliminar la información ya conocida y compartida (*tema*).

### Reglas para evitar la ambigüedad
- **Recuperabilidad unívoca**: El elemento elidido debe haber aparecido de forma inmediata y gramaticalmente compatible en el segmento precedente. Si existen múltiples antecedentes posibles con diferentes números, géneros o casos sintácticos, la elipsis genera anfibología (doble sentido) y debe resolverse reponiendo el término o empleando un pronombre demostrativo anafórico."""
    },
    {
        "user": "¿En qué consiste la falacia de petición de principio (*petitio principii*) y cómo se manifiesta en el razonamiento circular?",
        "assistant": r"""La **petición de principio** (*petitio principii*), conocida comúnmente como **razonamiento circular** (*circulus in probando*), es una falacia lógica formal o pragmática en la cual la conclusión que se pretende fundamentar o demostrar ya está asumida, implícita o explícitamente, dentro de las premisas que supuestamente deben probarla.

### Estructura formal
$$\begin{aligned}
P &\to Q \\
Q &\to P \\
\hline
\therefore P
\end{aligned}$$

El argumento no avanza epistemológicamente: no aporta evidencia externa independiente, sino que se limita a parafrasear la afirmación inicial presentándola como su propia justificación.

### Ejemplos analíticos
1. **Enunciado**: «Debemos obedecer ciegamente las directrices del manual porque el propio manual establece en su primer artículo que todas sus normas son obligatorias e infalibles».
   - *Fallo*: La autoridad del manual no puede derivarse de la autoridad que el propio manual se autoatribuye; requiere una fuente externa de legitimidad.
2. **Enunciado**: «La economía de libre mercado absoluta es el sistema más eficiente porque ningún otro modelo distribuye los recursos con tanta eficiencia».
   - *Fallo*: La premisa y la conclusión son enunciados idénticos revestidos con diferente ropaje léxico; no hay demostración factual de eficiencia.

### Criterio de identificación
Para desenmascarar una petición de principio, basta con formular la pregunta: *«¿Qué evidencia independiente valida la premisa básica que no asuma de antemano que la conclusión ya es verdadera?»*. Si la única prueba de la premisa es la propia conclusión, el razonamiento es circular y epistemológicamente nulo."""
    }
]

ANALYSIS_SAMPLES.extend([
    {
        "user": "¿Cuál es la distinción precisa entre las falacias causales 'post hoc ergo propter hoc' y 'cum hoc ergo propter hoc'?",
        "assistant": r"""Ambas son falacias informales de **falsa causa** que confunden la correlación temporal o estadística con una relación causal unívoca, pero difieren en la disposición temporal de los eventos analizados:

### 1. Post hoc ergo propter hoc («Después de esto, por lo tanto a causa de esto»)
- **Mecanismo**: Infiere erróneamente que, como el evento B ocurrió cronológicamente después del evento A, A debe ser necesariamente la causa generadora de B.
- **Error lógico**: La mera sucesión temporal no prueba causalidad. Omite la coincidencia aleatoria o la existencia de variables intervinientes independientes.
- **Ejemplo**: «El paciente tomó un suplemento de hierbas el martes y el jueves desapareció su resfriado común; por tanto, el suplemento curó el virus». (Ignora el curso fisiológico natural autolimitado del sistema inmunitario).

### 2. Cum hoc ergo propter hoc («Junto con esto, por lo tanto a causa de esto»)
- **Mecanismo**: Afirma que dos eventos simultáneos o dos variables continuas estadísticamente correlacionadas ($r \approx 1.0$) guardan una relación causal directa entre sí.
- **Error lógico**: Ignora el principio estadístico fundamental: **«correlación no implica causalidad»**. Suele pasar por alto:
  1. *Causalidad inversa*: B podría estar causando A.
  2. *Variable de confusión oculta (tercer factor)*: Una variable C no medida causa simultáneamente a A y a B.
  3. *Correlación espuria pura*: Coincidencia matemática sin nexo físico en grandes conjuntos de datos.
- **Ejemplo**: «Existe una correlación estadística positiva casi perfecta entre el incremento en las ventas de helados y el número de ahogamientos en playas; por tanto, comer helado provoca que la gente se ahogue». (La variable oculta común es la temperatura ambiental del verano)."""
    },
    {
        "user": "¿Qué es un falso dilema (o falsa dicotomía) y cómo se evidencia en discursos políticos o corporativos?",
        "assistant": r"""La **falsa dicotomía** o **falso dilema** es una falacia informal que reduce artificiosamente un espectro complejo y multifacético de posibilidades a únicamente **dos opciones antagónicas y mutuamente excluyentes**, obligando al receptor a elegir una de ellas bajo la presunción falsa de que no existen alternativas intermedias o terceras vías.

### Esquema lógico
$$\begin{aligned}
P \lor Q \\
\neg P \\
\hline
\therefore Q
\end{aligned}$$
La estructura del silogismo disyuntivo es formalmente válida, pero el argumento es **materialmente falso** porque la premisa disyuntiva inicial ($P \lor Q$) excluye indebidamente opciones como $R, S$ o una combinación matizada de $P$ y $Q$.

### Manifestaciones típicas

1. **En el discurso político e institucional**:
   - *Enunciado*: «O aumentamos drásticamente el presupuesto militar sin restricciones de gasto, o dejamos al país indefenso ante una invasión inminente».
   - *Alternativas omitidas*: Reestructuración operativa de fuerzas existentes, modernización tecnológica de precisión, fortalecimiento de tratados diplomáticos multilaterales o auditoría del gasto en defensa.
2. **En el ámbito corporativo y de gestión**:
   - *Enunciado*: «O recortamos los salarios del personal un 15% este mes, o la empresa quebrará irremediablemente el próximo trimestre».
   - *Alternativas omitidas*: Renegociación de pasivos con acreedores financieros, postergación de inversiones de capital (CapEx), optimización de gastos operativos generales o aportación de capital por socios."""
    },
    {
        "user": "Explica la diferencia entre denotación y connotación en semántica lingüística.",
        "assistant": r"""En la semántica del lenguaje natural, la **denotación** y la **connotación** constituyen los dos niveles fundamentales de significación que operan en los términos y enunciados:

### 1. Denotación (Significado literal o de referencia)
- **Definición**: Es el significado objetivo, primario, cognitivo y explícito de una palabra, universalmente compartido por todos los hablantes competentes de una lengua y codificado en los diccionarios normativos.
- **Carácter**: Estable, unívoco, desprovisto de carga afectiva o valorativa, y estrechamente ligado al referente objetivo del mundo.
- **Ejemplo**: La palabra *«otoño»* denota estrictamente: «Estación del año comprendida entre el verano y el invierno, que en el hemisferio norte se extiende desde el equinoccio de septiembre hasta el solsticio de diciembre».

### 2. Connotación (Significado evocativo o secundario)
- **Definición**: Conjunto de significados secundarios, figurados, afectivos, simbólicos, ideológicos o culturales que se superponen al significado denotativo según el contexto cultural, social o subjetivo del hablante o receptor.
- **Carácter**: Variable, plurívoco, dinámico y contextualmente dependiente.
- **Ejemplo**: En la literatura y el habla cotidiana, *«otoño»* connota frecuentemente: madurez, declive vital, melancolía, vejez, tránsito hacia el final o pérdida de la vitalidad juvenil.

La denotación asegura la inteligibilidad básica y técnica de la comunicación (indispensable en textos jurídicos y científicos), mientras que la connotación aporta riqueza expresiva, persuasión y profundidad estética (dominante en la literatura, la poesía y la publicidad)."""
    },
    {
        "user": "¿Cómo se diferencian la anáfora, la catáfora y la deixis en los mecanismos de cohesión referencial?",
        "assistant": r"""Estos tres mecanismos endofóricos y exofóricos garantizan la continuidad y cohesión referencial dentro de un texto, pero difieren en la dirección y el plano espacial o temporal en que sitúan a su referente:

### 1. Anáfora (Referencia retrospectiva)
- **Dirección**: Señala hacia un elemento que ya ha sido mencionado explícitamente en el texto precedente (**antecedente**).
- **Función**: Evita la repetición léxica manteniendo activo el foco de atención discursivo.
- **Ejemplo**: *«El tribunal dictó la **sentencia** esta mañana; **esta** [anáfora] provocó el rechazo de los acusados»*.

### 2. Catáfora (Referencia prospectiva)
- **Dirección**: Anticipa un elemento léxico o una proposición que aún no ha sido formulada en el texto y que aparecerá inmediatamente después (**consecuente**).
- **Función**: Genera expectativa rítmica y organiza sintácticamente enumeraciones complejas.
- **Ejemplo**: *«Solo te diré **esto** [catáfora]: **el proyecto fue cancelado por falta de liquidez**»*.

### 3. Deixis (Referencia exofórica situacional)
- **Dirección**: No señala a otro elemento dentro del texto lingüístico, sino directamente a los componentes del **contexto pragmático extralingüístico** (el emisor, el receptor, el espacio o el momento de la enunciación).
- **Tipos principales**:
  - *Deixis personal*: Pronombres que identifican a los interlocutores (*yo, tú, nosotros*).
  - *Deixis espacial*: Adverbios y demostrativos que sitúan respecto a la proximidad física del emisor (*aquí, ahí, allí, este, aquel*).
  - *Deixis temporal*: Marcadores que toman como punto cero el instante de la emisión verbal (*hoy, ayer, ahora, el mes próximo*)."""
    },
    {
        "user": "¿En qué consiste la falacia de apelación a la autoridad (*argumentum ad verecundiam*) y cuándo un argumento de autoridad es legítimo?",
        "assistant": r"""El *argumentum ad verecundiam* consiste en dar por demostrada la veracidad de una afirmación únicamente sobre la base de que ha sido enunciada por una figura famosa, de prestigio o de autoridad, sustituyendo la evidencia objetiva por el respeto o sumisión reverencial a dicha personalidad.

### Cuándo deviene en falacia
Incurre en falacia cuando se cumple alguna de las siguientes condiciones:
1. **Autoridad fuera de campo (Transferencia indebida)**: Se cita el testimonio de un experto reconocido en un área para validar una tesis en una disciplina enteramente ajena (ej. citar la opinión sobre economía monetaria de un premio Nobel de física teórica).
2. **Consenso inexistente en la disciplina**: Se apela a un especialista aislado en una materia donde no existe consenso científico consolidado, ignorando la controversia interna o la evidencia mayoritaria opuesta.
3. **Falta de imparcialidad o sesgo de interés**: La autoridad citada tiene un interés financiero, político o personal directo en la conclusión que defiende.
4. **Infalibilidad dogmática**: Se presenta la opinión del experto como verdad revelada incuestionable, cerrando el debate ante la presentación de datos empíricos contradictorios.

### Criterios de legitimidad de un argumento de autoridad
Un argumento basado en el testimonio experto es metodológicamente legítimo si:
- El experto posee competencia y reconocimiento formal acreditado en el campo específico de discusión.
- Sus conclusiones están respaldadas por datos contrastables y revisiones por pares (*peer review*).
- Existe consenso representativo dentro de la comunidad científica o técnica correspondiente."""
    },
    {
        "user": "Analiza las diferencias expresivas y sintácticas entre el asíndeton y el polisíndeton.",
        "assistant": r"""El **asíndeton** y el **polisíndeton** son figuras retóricas de construcción sintáctica que manipulan la presencia o ausencia de nexos coordinantes (conjunciones copulativas o disyuntivas) entre elementos oracionales:

### 1. Asíndeton (Omisión de conjunciones)
- **Estructura**: Supresión total de conjunciones copulativas entre palabras, sintagmas o proposiciones contiguas, sustituyéndolas por pausas breves graficadas con comas o puntos y comas.
- **Efecto estético y rítmico**:
  - Acelera intensamente el tempo narrativo, transmitiendo dinamismo, inmediatez, vértigo, premura o desenlace fulgurante.
  - Genera una sensación de enumeración abierta, caótica o de impacto arrollador.
- **Ejemplo canónico**: *«Veni, vidi, vici»* (Julio César: «Llegué, vi, vencí»).

### 2. Polisíndeton (Reiteración de conjunciones)
- **Estructura**: Repetición insistente y deliberada de la misma conjunción coordinante (típicamente *«y»*, *«ni»*) uniendo cada uno de los elementos de la serie sintáctica.
- **Efecto estético y rítmico**:
  - Ralentiza conscientemente la lectura, otorgando un compás pausado, grave, ceremonial o litúrgico a la elocución.
  - Enfatiza individualmente el peso conceptual de cada término enumerado, sugiriendo abundancia, acumulación inagotable o agobio.
- **Ejemplo canónico**: *«Y ríe, y llora, y tiembla, y sufre, y espera»*."""
    },
    {
        "user": "¿Cómo se clasifican y estructuran los conectores discursivos en la argumentación formal?",
        "assistant": r"""Los **conectores discursivos** (o marcadores textuales) son enlaces invariables que guían las inferencias del lector estableciendo relaciones lógico-semánticas explícitas entre oraciones y párrafos. En la argumentación formal se clasifican en cuatro grandes familias:

### 1. Conectores Contraargumentativos y de Concesión
Modifican, limitan o neutralizan el valor argumentativo del segmento previo:
- **De contraste u oposición restrictiva**: *Sin embargo, no obstante, en cambio, por el contrario, ahora bien*.
- **De concesión (aceptan una premisa pero mantienen la conclusión principal)**: *A pesar de que, si bien, aun cuando, con todo*.
- **De exclusión absoluta**: *Sino, antes bien*.

### 2. Conectores Consecutivos e Iliciativos
Indican que el enunciado posterior es la deducción lógica, resultado o consecuencia necesaria de lo expuesto:
- *Por consiguiente, por lo tanto, en consecuencia, de ahí que, ergo, por ende, de modo que*.

### 3. Conectores Causales
Introducen la causa, justificación o premisa empírica que sustenta la afirmación previa:
- *Puesto que, dado que, ya que, en virtud de que, merced a, toda vez que*.

### 4. Conectores Explicativos y de Reformulación
Aclaran, precisan o recapitulan un argumento anterior para optimizar la recepción:
- **Explicativos**: *Es decir, esto es, a saber, o sea*.
- **De rectificación o precisión**: *Mejor dicho, más exactamente*.
- **Recapitulativos o conclusivos**: *En síntesis, en resumen, en definitiva, en suma*."""
    }
])
