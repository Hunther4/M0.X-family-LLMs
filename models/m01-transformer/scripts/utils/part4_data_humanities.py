# -*- coding: utf-8 -*-
"""Dataset de humanidades, filosofía, derecho, economía y lingüística (sin fluff)."""

HUMANITIES_SAMPLES = [
    {
        "user": "¿Cuál es la diferencia entre dolo y culpa en el derecho penal contemporáneo?",
        "assistant": r"""En el derecho penal, la distinción entre **dolo** y **culpa** (o imprudencia) delimita el elemento subjetivo del tipo penal, determinando el reproche de culpabilidad y la gravedad punitiva:

### 1. El Dolo
El dolo concurre cuando el autor realiza la conducta típica con **conocimiento** (elemento cognoscitivo o intelectivo) y **voluntad** (elemento volitivo) de realizar los elementos del tipo penal.
- **Dolo directo de primer grado**: El autor busca y persigue intencionadamente la producción del resultado delictivo como meta directa de su acción (ej. disparar al corazón con el fin de matar).
- **Dolo directo de segundo grado (de consecuencias necesarias)**: El autor no persigue directamente el resultado adicional, pero sabe con certeza práctica que este se producirá indefectiblemente como consecuencia necesaria de su acción principal (ej. colocar una bomba en un avión para destruir una mercancía, asumiendo la muerte segura de los pasajeros).
- **Dolo eventual**: El autor se representa el resultado lesivo como una posibilidad probable o altamente verosímil y, pese a ello, continúa con su acción aceptando, consintiendo o conformándose con su eventual producción.

### 2. La Culpa (Imprudencia)
Existe culpa cuando el autor produce el resultado lesivo sin intención deliberada, como consecuencia directa de la **infracción del deber objetivo de cuidado** exigible en el tráfico jurídico:
- **Culpa consciente (o con representación)**: El sujeto prevé la posibilidad de que el resultado lesivo acontezca, pero confía imprudentemente en que este no ocurrirá o en que sus habilidades evitarán el daño. Se diferencia del dolo eventual en que aquí el autor no acepta ni consiente la lesión del bien jurídico.
- **Culpa inconsciente (sin representación)**: El autor ni siquiera se representa el peligro de su conducta, pese a que según el estándar medio de diligencia debida debía haberlo previsto y evitado."""
    },
    {
        "user": "Explica la diferencia jurídica y práctica entre prescripción extintiva y caducidad.",
        "assistant": r"""Tanto la **prescripción extintiva** como la **caducidad** son instituciones jurídicas basadas en la inacción durante el transcurso del tiempo, pero poseen naturalezas dogmáticas y efectos procesales profundamente divergentes:

| Parámetro | Prescripción Extintiva | Caducidad |
| :--- | :--- | :--- |
| **Objeto de extinción** | Extingue la **acción procesal** para exigir judicialmente el cumplimiento; subsiste la obligación como deber moral/natural. | Extingue de raíz el **derecho subjetivo sustantivo** y la potestad jurídica misma. |
| **Interrupción** | **Admite interrupción**: Un acto de reclamación judicial, extrajudicial o reconocimiento de deuda reinicia el cómputo del plazo desde cero. | **No admite interrupción**: El plazo es fatal y preclusivo; solo se detiene con el ejercicio formal y efectivo del derecho. |
| **Apreciación judicial** | **A instancia de parte**: El juez no puede declararla de oficio; el demandado debe alegarla y oponerla expresamente como excepción procesal. | **De oficio**: El órgano jurisdiccional debe apreciarla y declararla obligatoriamente, aun sin petición de las partes. |
| **Renunciabilidad** | Se puede renunciar a la prescripción ya ganada (art. 1935 Código Civil), aunque no al derecho a prescribir a futuro. | Irrenunciable por las partes, al estar ligada al orden público y a la seguridad jurídica colectiva. |
| **Ámbito típico** | Derechos de crédito y obligaciones patrimoniales personales y reales. | Acciones potestativas, plazos procesales, recursos administrativos e impugnaciones de filiación o acuerdos sociales. |"""
    },
    {
        "user": "¿Qué postula la deontología kantiana frente al utilitarismo de Bentham y Mill en ética normativa?",
        "assistant": r"""La **deontología kantiana** y el **utilitarismo** representan los dos paradigmas contrapuestos más influyentes de la ética normativa moderna:

### Deontología kantiana (Ética del deber)
- **Principio rector**: La moralidad de una acción radica intrínsecamente en la **máxima que la guía** y en el cumplimiento estricto del deber por respeto a la ley moral, con total independencia de las consecuencias empíricas que deriven de ella.
- **Imperativo Categórico**: Formulado por Immanuel Kant en dos variantes fundamentales:
  1. *Fórmula de la ley universal*: «Obra solo según una máxima tal que puedas querer al mismo tiempo que se torne ley universal».
  2. *Fórmula de la humanidad*: «Obra de tal modo que uses a la humanidad, tanto en tu persona como en la de cualquier otro, siempre como un fin y nunca meramente como un medio».
- **Carácter absoluto**: Existen prohibiciones morales inviolables (ej. mentir o traicionar a un inocente es moralmente ilícito siempre, incluso si mentir evitara una tragedia mayor).

### Utilitarismo clásico (Ética consecuencialista)
- **Principio rector**: El valor moral de una acción depende exclusivamente del **balance neto de sus consecuencias**.
- **Principio de utilidad (Bentham y Mill)**: Una acción es moralmente correcta si promueve la mayor cantidad neta de felicidad o bienestar para el mayor número de personas afectadas («la máxima felicidad para el mayor número»).
- **Flexibilidad instrumental**: Ningún acto es intrínsecamente erróneo per se. Si una conducta aparentemente reprobable (como quebrar una promesa o sacrificar un recurso minoritario) maximiza el bienestar colectivo neto de forma demostrable, deviene en el curso de acción éticamente imperativo."""
    },
    {
        "user": "¿Cómo se define la eficiencia de Pareto y en qué se distingue del criterio de Kaldor-Hicks en economía del bienestar?",
        "assistant": r"""En la economía del bienestar, ambos criterios evalúan la deseabilidad y eficiencia de una reasignación de recursos en una sociedad:

### 1. Óptimo y Mejora de Pareto
- **Mejora de Pareto**: Una asignación de recursos es superior a otra si al menos un individuo mejora su nivel de utilidad o bienestar sin que ningún otro empeore.
- **Óptimo de Pareto**: Es un estado en el que resulta físicamente imposible reasignar los recursos para hacer que alguien mejore sin empeorar simultáneamente la situación de al menos otra persona.
- **Limitación práctica**: Exige unanimidad estricta. Cualquier política económica del mundo real (ej. una reforma fiscal, apertura comercial o construcción de una autopista) genera ganadores y perdedores; por tanto, prácticamente ninguna política pública constituye una mejora paretiana estricta.

### 2. Criterio de Kaldor-Hicks (Mejora potencial de Pareto)
- **Definición**: Una reasignación es eficiente en el sentido de Kaldor-Hicks si aquellos que se benefician obtienen una ganancia neta lo suficientemente cuantiosa como para que **pudieran hipotéticamente compensar** a los perjudicados y aun así conservar un beneficio neto residual.
- **Distinción clave**: **No exige que la compensación económica ocurra de facto**. Basta con que la ganancia agregada total supere la pérdida agregada ($\sum \Delta U_{ganadores} > \sum |\Delta U_{perdedores}|$).
- **Uso económico**: Constituye el fundamento teórico del **análisis coste-beneficio** empleado en la evaluación de políticas públicas e infraestructuras por los gobiernos."""
    },
    {
        "user": "¿Qué diferencia estableció Ferdinand de Saussure entre significante, significado y el signo lingüístico?",
        "assistant": r"""En su *Curso de lingüística general* (1916), Ferdinand de Saussure sentó las bases de la semiótica moderna al definir el **signo lingüístico** como una entidad psíquica biplánica, compuesta por dos caras indisociables:

```
Signo Lingüístico = Significante (Imagen acústica) / Significado (Concepto)
```

### Componentes estructurales
1. **El Significante**: Es la huella psíquica del sonido; la **imagen acústica** o representación mental de la cadena de fonemas (no el sonido físico material que viaja por el aire, sino su registro mental en la lengua). Ejemplo: la secuencia fonológica mental $/m-e-s-a/$.
2. **El Significado**: Es la **representación conceptual** o idea abstracta asociada en la mente a dicho significante. Ejemplo: el concepto abstracto de «mueble compuesto por un tablero horizontal sostenido por pies o soportes».
3. **El Referente (Excluido por Saussure)**: Es el objeto físico empírico de la realidad extralingüística (la mesa de madera real). Saussure insistió en que el signo une un concepto con una imagen acústica dentro del sistema mental de la lengua, no una palabra con una cosa real del mundo exterior.

### Principios rectores del signo saussureano
- **Arbitrariedad**: No existe ninguna relación natural, causal ni motivada entre el significante y el significado. Que al concepto «perro» le corresponda el significante */p-e-r-o/* en español, *dog* en inglés o *chien* en francés es una convención social pura.
- **Linealidad del significante**: Los elementos fónicos se despliegan necesariamente en una dimensión temporal sucesiva (una línea temporal o espacial en la escritura), imposibilitando pronunciar dos fonemas al mismo tiempo.
- **Inmutabilidad y mutabilidad**: Sincrónicamente, el signo es inmutable (el hablante individual no puede alterar caprichosamente las convenciones de su comunidad); diacrónicamente, el signo es mutable (el uso colectivo a lo largo del tiempo transforma significantes y significados)."""
    },
    {
        "user": "¿Qué es la trampa de la liquidez según John Maynard Keynes y por qué inutiliza la política monetaria convencional?",
        "assistant": r"""La **trampa de la liquidez** es una situación macroeconómica en la que la tasa de interés nominal de corto plazo cae a un nivel cercano a cero (el límite inferior cero o *zero lower bound*), provocando que la demanda de dinero por motivo especulación se vuelva infinitamente elástica.

### Mecanismo de transmisión convencional
En condiciones ordinarias, cuando el banco central implementa una política monetaria expansiva:
1. Compra bonos en operaciones de mercado abierto, inyectando reservas al sistema bancario.
2. La mayor oferta de dinero reduce las tasas de interés nominales.
3. El menor coste del crédito incentiva el gasto en inversión corporativa y el consumo privado durable, estimulando la demanda agregada.

### Ocurrencia de la trampa
En una recesión profunda o deflación severa:
1. Los tipos de interés nominales tocan su límite técnico inferior ($0\%$).
2. Los precios de los bonos se sitúan en su techo máximo, lo que genera en los inversores la expectativa unánime de que las tasas de interés solo pueden subir en el futuro (y el precio de los bonos caer).
3. En consecuencia, el costo de oportunidad de mantener dinero en efectivo es nulo y el riesgo de sufrir pérdidas de capital en renta fija es elevado.
4. Cualquier incremento adicional en la base monetaria es absorbido pasivamente por familias y bancos comerciales como saldos ociosos de liquidez, sin traducirse en nuevo crédito, inversión ni consumo.

### Consecuencia de política económica
La política monetaria convencional pierde toda efectividad operativa (equivalente a «empujar una cuerda»). Para salir de la trampa de la liquidez, Keynes postuló la primacía de la **política fiscal expansiva directa** (gasto público en obras e inversión estatal directa), la cual inyecta demanda agregada real a la economía sin depender del canal crediticio bancario privado."""
    },
    {
        "user": "¿En qué consiste el velo de la ignorancia de John Rawls y qué principios de justicia deduce de él?",
        "assistant": r"""En su obra *Teoría de la justicia* (1971), John Rawls propone el **velo de la ignorancia** como un dispositivo conceptual dentro de un experimento mental contractualista denominado la **posición original**.

### El dispositivo del velo de la ignorancia
Rawls imagina a individuos racionales y libres encargados de diseñar las reglas e instituciones básicas que estructurarán su sociedad futura, pero colocados bajo un velo que les oculta deliberadamente sus circunstancias personales:
- Desconocen su clase social, estatus socioeconómico y riqueza.
- Desconocen sus talentos innatos, inteligencia y capacidades físicas.
- Desconocen su raza, sexo, etnia, religión o concepción personal del bien.

Al ignorar si nacerán millonarios o en la indigencia extrema, con talentos sobresalientes o con discapacidades severas, los individuos actuarán bajo la regla decisional del **maximin** (maximizar el bienestar de la peor situación posible), evitando adoptar esquemas utilitaristas que sacrifiquen a minorías vulnerables.

### Los dos principios de justicia resultantes

1. **Principio de igual libertad**:
   Cada persona debe tener un derecho igual al sistema total más extenso de libertades básicas fundamentales (de expresión, conciencia, asociación y voto) compatible con un esquema similar de libertades para todos. Posee prioridad léxica estricta sobre el segundo principio.
2. **Principio de la diferencia y equitativa igualdad de oportunidades**:
   Las desigualdades económicas y sociales solo son justificables si satisfacen dos condiciones:
   - **Equitativa igualdad de oportunidades**: Los cargos y posiciones deben estar abiertos a todos bajo condiciones de auténtica igualdad de oportunidades formativas y laborales.
   - **Principio de la diferencia**: Las desigualdades socioeconómicas existentes deben estructurarse de tal manera que redunden en el **mayor beneficio posible para los miembros menos aventajados** de la sociedad."""
    },
    {
        "user": "¿Cómo se define la anomia social según Émile Durkheim y en qué difiere la reformulación de Robert K. Merton?",
        "assistant": r"""El concepto de **anomia** (del griego *a-* [sin] y *nomos* [norma o ley]) designa un estado de desintegración o quiebre en la efectividad reguladora de las normas sociales sobre la conducta individual.

### 1. La anomia según Émile Durkheim
- **Origen**: Introducida en *La división del trabajo social* (1893) y desarrollada en *El suicidio* (1897).
- **Enfoque**: Crisis de regulación moral provocada por transformaciones económicas rápidas o desreguladas (industrialización abrupta o crisis financieras).
- **Mecanismo**: Los deseos y apetitos humanos son potencialmente ilimitados; solo la sociedad y sus normas morales colectivas pueden fijar un límite aceptable a las expectativas individuales. Cuando la sociedad entra en crisis y las normas se debilitan, los individuos experimentan una discrepancia dolorosa entre sus deseos infinitos y la imposibilidad de satisfacerlos, derivando en frustración existencial crónica y un incremento del **suicidio anómico**.

### 2. La anomia según Robert K. Merton
- **Origen**: Enunciada en *Estructura social y anomia* (1938).
- **Enfoque**: Desajuste estructural permanente entre la estructura cultural y la estructura social de oportunidades.
- **Mecanismo**: La cultura impone **metas legítimas** universales a toda la población (ej. el éxito económico y el ascenso social del sueño americano), pero la estructura de clases restringe severamente el acceso a los **medios legítimos institucionalizados** (educación formal, capital, empleos bien remunerados) para los estratos subalternos.
- **Tipología de adaptaciones individuales**:
  1. *Conformidad*: Acepta metas y medios legítimos.
  2. *Innovación*: Acepta las metas de éxito pero recurre a medios ilegítimos o delictivos (delincuencia instrumental).
  3. *Ritualismo*: Abandona las metas ambiciosas pero cumple rígidamente las normas burocráticas cotidianas.
  4. *Retraimiento*: Rechaza tanto metas como medios (marginalidad, adicción).
  5. *Rebelión*: Rechaza las metas y medios vigentes para sustituirlos por un nuevo orden social."""
    },
    {
        "user": "¿Qué explica la paradoja del valor (diamantes y agua) y cómo fue resuelta por la teoría de la utilidad marginal?",
        "assistant": r"""La **paradoja del valor** (o paradoja del agua y los diamantes), formulada célebremente por Adam Smith en *La riqueza de las naciones* (1776), planteaba una contradicción aparente:

> ¿Por qué el agua, que es indispensable para el sustento de la vida humana, tiene un precio de mercado prácticamente insignificante, mientras que los diamantes, que son prescindibles y ornamentales, alcanzan precios exorbitantes?

La economía clásica intentó explicarlo distinguiendo entre **valor de uso** (altísimo en el agua, bajo en diamantes) y **valor de cambio**, pero carecía del instrumental teórico para unificarlos formalmente.

### La solución marginalista (Menger, Jevons y Walras, 1870s)
La paradoja fue resuelta por la **teoría de la utilidad marginal**, la cual demostró que el precio de un bien no depende de su utilidad global o total, sino de su **utilidad marginal**: el valor subjetivo atribuido a la **última unidad adicional consumida o disponible** de dicho bien.

1. **El caso del agua**:
   - Posee una utilidad total colosal, pero su abundancia relativa en el medio es inmensa.
   - Dado que los primeros litros se destinan a necesidades vitales (hidratación), los siguientes al aseo y los últimos al riego o limpieza suntuaria, la **última unidad disponible** satisface una necesidad secundaria de muy bajo valor subjetivo.
   - En consecuencia, la **utilidad marginal** del agua es sumamente baja, lo que determina su precio de mercado reducido.

2. **El caso de los diamantes**:
   - Poseen una utilidad total mucho menor para la supervivencia, pero su escasez física absoluta es extrema.
   - Cada unidad disponible satisface usos altamente selectivos y no existe abundancia de unidades adicionales.
   - En consecuencia, la **utilidad marginal** del diamante es extremadamente elevada, justificando su elevado precio de equilibrio."""
    },
    {
        "user": "¿En qué consiste el principio de proporcionalidad en el control constitucional de leyes y actos estatales?",
        "assistant": r"""El **principio de proporcionalidad** es una técnica argumentativa y metodológica de rango constitucional (de matriz doctrinal alemana, extendida a nivel global) empleada por tribunales constitucionales para determinar si una ley o acto estatal que limita un derecho fundamental es legítimo o inconstitucional.

Se aplica mediante un examen escalonado de **tres juicios o subprincipios sucesivos y preclusivos**:

### 1. Juicio de Idoneidad (o Adecuación)
- Evalúa si la medida limitativa adoptada por el legislador o la autoridad es empíricamente apta y conducente para alcanzar el **fin constitucionalmente legítimo** que persigue.
- *Criterio*: Si la restricción del derecho no sirve en absoluto para alcanzar el objetivo pretendido, es calificada de inidónea y declarada inconstitucional de inmediato.

### 2. Juicio de Necesidad (Regla del medio menos restrictivo)
- Examina si existe otra medida alternativa igualmente eficaz para satisfacer el mismo objetivo constitucional pero que resulte **menos lesiva o gravosa** para el derecho fundamental restringido.
- *Criterio*: Si el Estado disponía de un mecanismo menos restrictivo con idéntica eficacia, la medida fracasa en el juicio de necesidad por imponer un sacrificio prescindible.

### 3. Juicio de Proporcionalidad en Sentido Estricto (Ponderación)
- Formulado como la ley de ponderación de Robert Alexy: «Cuanto mayor sea el grado de no satisfacción o afectación de un derecho fundamental, tanto mayor debe ser la importancia de la satisfacción del fin constitucional contrapuesto».
- *Criterio*: Requiere un balance costo-beneficio de derechos en pugna. El beneficio social o la protección del bien colectivo logrado por la medida debe compensar y superar con creces el daño infligido al núcleo del derecho fundamental afectado."""
    },
    {
        "user": "¿Qué es un equilibrio de Nash y cómo se evidencia formalmente en el dilema del prisionero?",
        "assistant": r"""En teoría de juegos no cooperativos, un **equilibrio de Nash** (formulado por John Nash en 1950) es un perfil de estrategias $(s_1^*, s_2^*, \dots, s_n^*)$ en el que ningún jugador tiene incentivos unilaterales para cambiar su estrategia elegida, asumiendo que las estrategias de todos los demás competidores se mantienen constantes.

Matemáticamente, para cada jugador $i$:
$$u_i(s_i^*, s_{-i}^*) \ge u_i(s_i, s_{-i}^*) \quad \forall s_i \in S_i$$

### Aplicación al Dilema del Prisionero
Dos sospechosos (A y B) son detenidos incomunicados por un delito grave. La fiscalía carece de pruebas concluyentes y ofrece el siguiente pacto individual:
- Si ambos confiesan (delatan), reciben 5 años de prisión cada uno.
- Si uno confiesa y el otro calla (coopera con su cómplice), el que confiesa queda libre (0 años) y el que calla recibe 10 años.
- Si ambos guardan silencio (cooperan mutuamente), solo pueden ser condenados por una falta menor a 1 año cada uno.

#### Matriz de pagos (Años de condena: menor es preferible)
- A Confiesa, B Confiesa: $(-5, -5)$
- A Confiesa, B Calla: $(0, -10)$
- A Calla, B Confiesa: $(-10, 0)$
- A Calla, B Calla: $(-1, -1)$

### Deducción del equilibrio
1. Si B calla, la mejor respuesta de A es confesar ($0 > -1$). Si B confiesa, la mejor respuesta de A sigue siendo confesar ($-5 > -10$). Por tanto, **confesar es una estrategia estrictamente dominante** para el jugador A.
2. Por simetría perfecta, confesar es también la estrategia dominante para el jugador B.
3. El único perfil donde ninguno de los dos puede mejorar su resultado individualmente cambiando su decisión de forma unilateral es **(Confesar, Confesar)** con un pago de $(-5, -5)$. Este es el **Equilibrio de Nash**.

**La paradoja central**: El equilibrio de Nash resultante es **ineficiente en el sentido de Pareto**, ya que ambos jugadores obtendrían un resultado sustancialmente mejor $(-1, -1)$ cooperando mutuamente en silencio, pero la racionalidad individual no vinculante los conduce inevitablemente al resultado subóptimo."""
    },
    {
        "user": "¿Cuál es la distinción teórica y práctica entre moral, ética y deontología profesional?",
        "assistant": r"""Aunque en el habla coloquial suelen emplearse indistintamente, en filosofía práctica y teoría del derecho corresponden a tres planos normativos de diferente fundamentación y alcance:

### 1. La Moral
- **Naturaleza**: Conjunto empírico de normas, valores, costumbres y creencias transmitidas social, cultural o religiosamente que orientan la conducta cotidiana de una comunidad determinada.
- **Origen y validación**: Externo e histórico. Se adquiere mediante la socialización y tradición; califica los actos como «buenos» o «malos» según el consenso tácito de un grupo social concreto.
- **Ámbito**: Colectivo, espontáneo y fáctico.

### 2. La Ética (Filosofía moral)
- **Naturaleza**: Disciplina filosófica que somete a reflexión crítica, racional y sistemática los fundamentos normativos de las diversas morales.
- **Origen y validación**: Interno, autónomo y deliberativo. No se limita a acatar una costumbre dada, sino que investiga *por qué* una norma es justa, analizando principios universales de justicia, deber y bienestar (ej. utilitarismo, kantismo, ética de la virtud).
- **Ámbito**: Teórico, reflexivo y de fundamentación conceptual.

### 3. La Deontología Profesional
- **Naturaleza**: Conjunto explícito de deberes, estándares técnicos y reglas éticas obligatorias que rigen el ejercicio de una profesión reglamentada (ej. medicina, abogacía, periodismo, ingeniería).
- **Origen y validación**: Colegiado e institucional. Queda codificada formalmente en los **códigos deontológicos** aprobados por colegios profesionales o corporaciones de derecho público.
- **Carácter coercitivo**: A diferencia de la moral o la ética reflexiva, la deontología posee fuerza sancionatoria corporativa interna (inhabilitación, suspensión de matrícula profesional o amonestaciones públicas disciplinarias ante faltas cometidas)."""
    },
    {
        "user": "¿Cómo opera la teoría de los actos de habla formulada por J. L. Austin y John Searle?",
        "assistant": r"""En *Cómo hacer cosas con palabras* (1962), John L. Austin rompió con la falacia descriptiva del positivismo lógico, demostrando que el lenguaje humano no sirve exclusivamente para describir estados de cosas del mundo (oraciones constatativas verdaderas o falsas), sino para **ejecutar acciones sociales reales** (oraciones realizativas o performativas).

### Los tres niveles simultáneos del acto de habla (Austin)
Al emitir cualquier enunciado, el hablante ejecuta simultáneamente tres actos constitutivos:

1. **Acto Locutivo**: Es el acto físico y sintáctico de emitir sonidos articulados organizados según las reglas gramaticales y semánticas de una lengua (el significado literal de decir algo).
2. **Acto Ilocutivo**: Es la **fuerza ilocutiva** o la acción comunicativa que se realiza efectivamente *al* hablar (ej. prometer, advertir, amenazar, ordenar, declarar o bautizar).
3. **Acto Perlocutivo**: Son los efectos psicológicos o consecuencias conductuales reales provocadas en el oyente o en el entorno *por* haber emitido el mensaje (ej. convencer, asustar, persuadir o indignar).

### Taxonomía de actos ilocutivos de John Searle (1969)
Searle sistematizó las fuerzas ilocutivas en cinco categorías según su dirección de ajuste (palabras-a-mundo o mundo-a-palabras):

- **Asertivos**: Comprometen al hablante con la veracidad de la proposición expresada (*afirmar, describir, concluir*). Dirección: palabras-a-mundo.
- **Directivos**: Intentan que el oyente realice una acción futura (*ordenar, suplicar, solicitar, prohibir*). Dirección: mundo-a-palabras.
- **Compromisivos**: Comprometen al propio hablante a ejecutar una acción futura (*prometer, jurar, garantizar*). Dirección: mundo-a-palabras.
- **Expresivos**: Manifiestan el estado afectivo o psicológico del hablante frente a una situación dada (*agradecer, felicitar, disculparse*). Sin dirección de ajuste.
- **Declarativos**: Modifican instantáneamente el estatus o la realidad institucional del mundo en virtud de la autoridad institucional del emisor (*declarar la guerra, casar legalmente, despedir a un empleado, emitir sentencia penal*). Dirección: dual simultánea (palabras-mundo y mundo-palabras)."""
    },
    {
        "user": "¿Cuál es la formulación de la ventaja comparativa de David Ricardo y por qué supera a la ventaja absoluta de Adam Smith?",
        "assistant": r"""En el comercio internacional, Adam Smith formuló en 1776 el principio de la **ventaja absoluta**, según el cual un país debe exportar aquellos bienes que produce con menores costes absolutos en horas de trabajo que sus socios comerciales, e importar aquellos donde sus costes absolutos son mayores.

Sin embargo, este modelo dejaba una interrogante crítica: ¿qué ocurre si un país es menos productivo de forma absoluta en **todos** los sectores económicos respecto a otra nación desarrollada? Según Smith, no podría comerciar ventajosamente.

### La Teoría de la Ventaja Comparativa de David Ricardo (1817)
David Ricardo demostró que el comercio internacional es mutuamente beneficioso incluso si un país posee una desventaja absoluta en la producción de todos los bienes, siempre que se especialice en el bien donde posee el **menor coste de oportunidad relativo**.

### Formalización numérica clásica (Inglaterra y Portugal)
Horas de trabajo necesarias para producir una unidad de bien:

| País | Paño (unidad) | Vino (unidad) | Coste de oportunidad de 1 Vino | Coste de oportunidad de 1 Paño |
| :--- | :--- | :--- | :--- | :--- |
| **Inglaterra** | 100 h | 120 h | $1.2$ unidades de Paño | $0.83$ unidades de Vino |
| **Portugal** | 90 h | 80 h | $0.89$ unidades de Paño | $1.125$ unidades de Vino |

- **Ventaja absoluta**: Portugal posee ventaja absoluta en ambos sectores, pues produce tanto el paño (90 h vs 100 h) como el vino (80 h vs 120 h) con menos horas de trabajo.
- **Ventaja comparativa**:
  - En Portugal, producir 1 unidad de vino cuesta renunciar a $80/90 = 0.89$ unidades de paño.
  - En Inglaterra, producir 1 unidad de vino cuesta renunciar a $120/100 = 1.2$ unidades de paño.
  - Como el coste de oportunidad del vino en Portugal es menor ($0.89 < 1.2$), Portugal tiene **ventaja comparativa en vino**.
  - A su vez, el coste de producir paño en Inglaterra es renunciar a $100/120 = 0.83$ de vino, mientras en Portugal es $90/80 = 1.125$. Inglaterra tiene **ventaja comparativa en paño**.

### Conclusión económica
Si Portugal se especializa exclusivamente en vino e Inglaterra en paño e intercambian a una relación de precios intermedia (ej. 1 vino por 1 paño), la producción total mundial se incrementa y ambos países consumen fuera de su frontera de posibilidades de producción individual."""
    },
    {
        "user": "¿Qué es el concepto de falsacionismo de Karl Popper y cómo critica el inductivismo tradicional?",
        "assistant": r"""En *La lógica de la investigación científica* (1934), Karl Popper formuló el **falsacionismo** (o racionalismo crítico) como criterio de demarcación para distinguir las ciencias empíricas de la pseudociencia y la metafísica, desmantelando la epistemología inductivista tradicional sostenida por el Círculo de Viena.

### La crítica al inductivismo (El problema de Hume)
El inductivismo asume que la acumulación reiterada de observaciones singulares favorables permite inferir enunciados universales o leyes científicas verdaderas:
- *Premisa*: «El cisne 1 es blanco, el cisne 2 es blanco, el cisne $n$ es blanco».
- *Conclusión inductiva*: «Todos los cisnes son blancos».
Popper evidenció la asimetría lógica insoslayable: **ninguna cantidad finita de observaciones favorables puede verificar o demostrar la verdad definitiva de una ley universal**, puesto que basta con una sola observación contradictoria (el avistamiento de un cisne negro) para refutarla de forma concluyente.

### El principio de falsabilidad
Para Popper, una teoría no adquiere estatus científico por acumular confirmaciones empíricas retrospectivas (lo cual hacen fácilmente disciplinas dogmáticas reinterpretando cualquier hecho posterior), sino por ser **falsable**:

1. **Condición de cientificidad**: Una hipótesis debe realizar predicciones de alto riesgo conceptual y definir con precisión qué observaciones empíricas potenciales están prohibidas por la teoría.
2. **Asimetría del Modus Tollens**: La falsación opera mediante la regla lógica deductiva estricta del *modus tollens*:
   $$\begin{aligned}
   T &\to P \\
   \neg P \\
   \hline
   \therefore \neg T
   \end{aligned}$$
   Si la teoría $T$ predice $P$ y experimentalmente se observa $\neg P$, la teoría queda formalmente refutada.
3. **Carácter provisional del conocimiento**: Las teorías que sobreviven a pruebas experimentales rigurosas no quedan «verificadas» ni demostradas como verdades inmutables; solo se consideran temporalmente **corroboradas** hasta que una nueva prueba experimental demuestre sus límites explicativos."""
    }
]

HUMANITIES_SAMPLES.extend([
    {
        "user": "¿Qué diferencia la inflación por demanda de la inflación por costes y qué implicaciones tiene para la política monetaria?",
        "assistant": r"""La **inflación** (aumento sostenido y generalizado del nivel de precios) puede originarse por perturbaciones en lados opuestos del equilibrio macroeconómico:

### 1. Inflación por Demanda (*Demand-Pull*)
- **Causa**: Se origina cuando la demanda agregada ($DA = C + I + G + X - M$) crece a un ritmo superior a la capacidad productiva de pleno empleo de la economía (brecha del producto positiva, $Y > Y^*$).
- **Mecanismo**: El exceso de gasto presiona al alza los precios relativos al competir los compradores por una oferta agregada inelástica a corto plazo.
- **Diagnóstico y política**: Responde favorablemente a la **política monetaria contractiva** (alza de tipos de interés, reducción de crédito) y disciplina fiscal, las cuales reducen el gasto agregado y restablecen el equilibrio de precios sin provocar desempleo estructural.

### 2. Inflación por Costes (*Cost-Push*) o Choque de Oferta
- **Causa**: Provocada por aumentos abruptos en los costes de producción esenciales (insumos energéticos importados como el petróleo, minerales críticos, alzas salariales no asociadas a productividad, o depreciaciones cambiarias severas).
- **Mecanismo**: La curva de oferta agregada a corto plazo se desplaza hacia la izquierda ($OA \leftarrow$), encareciendo los bienes y reduciendo simultáneamente el nivel de producción real.
- **El dilema de la política monetaria**:
  - Si el banco central sube las tasas para frenar la inflación, deprime aún más la actividad económica, agravando la recesión y el desempleo (**estanflación**).
  - Si baja las tasas para evitar la recesión, alimenta la espiral de inflación y desancla las expectativas de precios."""
    },
    {
        "user": "¿En qué consiste el principio de legalidad y el mandato de tipicidad en el derecho penal?",
        "assistant": r"""El **principio de legalidad**, sintetizado en el aforismo latino de Feuerbach *«Nullum crimen, nulla poena sine praevia lege»*, es la garantía medular del Estado de derecho que protege la libertad individual frente a la arbitrariedad punitiva estatal.

Se descompone en cuatro exigencias constitucionales estrictas:

1. **Lex previa (Prohibición de retroactividad)**:
   Nadie puede ser sancionado penalmente por acciones u omisiones que en el momento de producirse no constituyan delito según la ley vigente. Solo se admite la retroactividad de la ley penal cuando esta resulte favorable al reo (*principio pro reo*).
2. **Lex scripta (Reserva de ley estricta)**:
   La creación de figuras delictivas y la asignación de penas o medidas de seguridad debe realizarse exclusivamente mediante normas con rango formal de ley aprobadas por el parlamento, vedándose la regulación punitiva mediante reglamentos o decretos administrativos independientes.
3. **Lex stricta (Mandato de tipicidad y prohibición de analogía in malam partem)**:
   - Exige que el legislador describa con la mayor precisión, claridad y exhaustividad posible la conducta prohibida (**mandato de determinación o taxatividad**), evitando tipos penales vagos o cláusulas generales abiertas.
   - Prohíbe categóricamente al juez aplicar una norma penal a un supuesto no previsto literalmente en el texto legal por mera similitud o analogía desfavorable al imputado.
4. **Lex certa (Seguridad jurídica)**:
   El ciudadano debe tener la certeza previa e inequívoca de cuáles conductas son penalmente relevantes antes de actuar en sociedad."""
    },
    {
        "user": "¿Cuáles son los tres tipos puros de dominación legítima según Max Weber?",
        "assistant": r"""En *Economía y sociedad* (1922), Max Weber clasificó la **dominación** (la probabilidad de encontrar obediencia voluntaria a un mandato determinado) según el fundamento último que sustenta su **pretensión de legitimidad**:

### 1. Dominación Racional-Legal
- **Fundamento de legitimidad**: Creencia en la validez intrínseca del orden jurídico formal, positivo y estatutario, y en el derecho de los gobernantes designados conforme a derecho a dictar órdenes.
- **Sujeto de obediencia**: El ciudadano no obedece a la persona del gobernante por su rango personal, sino a la **ley impersonal y abstracta**. La autoridad misma está limitada por la norma jurídica.
- **Aparato administrativo típico**: La **burocracia moderna**, caracterizada por jerarquía funcional reglada, competencias delimitadas, archivo documental escrito y funcionarios profesionales asalariados seleccionados por mérito técnico.

### 2. Dominación Tradicional
- **Fundamento de legitimidad**: Creencia sacra en la santidad de las tradiciones y costumbres heredadas del pasado inmemorial, y en la legitimidad del señor investido de poder tradicional.
- **Sujeto de obediencia**: Se obedece a la persona del señor en virtud de la lealtad personal o piedad filial heredada. Las decisiones se basan en el arbitrio personal, la equidad informal o la costumbre inveterada.
- **Aparatos administrativos típicos**: El patrimonialismo, el feudalismo y el patriarcalismo dinástico.

### 3. Dominación Carismática
- **Fundamento de legitimidad**: Devoción extraordinaria, afectiva y personal hacia el heroísmo, la santidad, el magnetismo o las cualidades excepcionales ejemplares de un líder.
- **Sujeto de obediencia**: Reconocimiento directo e incondicional por parte de los discípulos o seguidores que acreditan los dones carismáticos del profeta, líder militar o estadista revolucionario.
- **Naturaleza**: Inestable y disruptiva; carece de reglas formales o precedentes.
- **Transformación**: Para perdurar tras la desaparición del líder, debe experimentar un proceso de **rutinización del carisma** hacia formas tradicionales o racional-legales."""
    },
    {
        "user": "¿Cuáles son las seis funciones del lenguaje según Roman Jakobson y a qué factor de la comunicación se asocian?",
        "assistant": r"""En su modelo estructuralista de la comunicación (1960), Roman Jakobson postuló que todo acto verbal involucra seis factores constitutivos, cada uno de los cuales determina una **función predominante del lenguaje**:

| Factor de la Comunicación | Función Lingüística | Propósito Central y Manifestación |
| :--- | :--- | :--- |
| **Contexto / Referente** | **Referencial (o Denotativa)** | Transmitir información objetiva y verificable sobre el mundo exterior. Uso de oraciones enunciativas y modo indicativo (ej. «El agua hierve a 100 °C»). |
| **Emisor** | **Emotiva (o Expresiva)** | Expresar la actitud subjetiva, emociones, valoraciones o estados anímicos del hablante. Uso de interjecciones, exclamaciones y adjetivación valorativa. |
| **Receptor** | **Conativa (o Apelativa)** | Influir directamente en la conducta, pensamiento o actitud del oyente. Empleo predominante del modo imperativo, vocativos y preguntas retóricas. |
| **Canal (Contacto)** | **Fática (o de Contacto)** | Iniciar, verificar, prolongar o interrumpir el canal físico y psíquico de la comunicación (ej. «¿Me escuchas?», «Hola», «Ajá», «Buenos días»). |
| **Código** | **Metalingüística** | Hablar sobre el propio código lingüístico para aclarar significados, gramática o normas léxicas (ej. «La palabra 'casa' es un sustantivo femenino»). |
| **Mensaje** | **Poética (o Estética)** | Centrar la atención en la forma, ritmo, cadencia y textura del propio mensaje artístico o estilístico (figuras retóricas, rimas, aliteraciones). |

En un enunciado real confluyen múltiples funciones simultáneas, pero una de ellas opera como jerárquicamente dominante."""
    },
    {
        "user": "¿Qué diferencia a la validez lógica de la verdad material y de la solidez argumentativa?",
        "assistant": r"""En lógica formal y teoría de la argumentación, estos tres términos evalúan propiedades completamente distintas de los enunciados y razonamientos:

### 1. Validez Lógica
- **Propiedad de**: Exclusivamente de la **estructura formal del argumento deductivo**, nunca de proposiciones aisladas.
- **Definición**: Un argumento es formalmente válido si su estructura lógica garantiza que es formalmente imposible que la conclusión sea falsa si todas sus premisas fuesen verdaderas.
- **Independencia fáctica**: Un argumento puede ser perfectamente válido aunque todas sus premisas sean materialmente absurdas o falsas en el mundo empírico:
  - *Premisa 1*: Todos los reptiles vuelan.
  - *Premisa 2*: Las ranas son reptiles.
  - *Conclusión*: Las ranas vuelan.
  *(Estructura perfectamente válida: Todo A es B; C es A; por tanto C es B).*

### 2. Verdad Material
- **Propiedad de**: Las **proposiciones o premisas individuales**, nunca del argumento como estructura.
- **Definición**: Una proposición es materialmente verdadera si se corresponde con los hechos empíricos contrastables de la realidad o con las convenciones formales del sistema.
  - *Enunciado*: «París es la capital de Francia» (Materialmente verdadero).
  - *Enunciado*: «La Luna está hecha de silicio metálico líquido» (Materialmente falso).

### 3. Solidez Argumentativa (*Soundness*)
- **Propiedad de**: Un argumento deductivo completo en el que convergen la corrección formal y la contrastación empírica.
- **Definición**: Un argumento es **sólido** si y solo si satisface dos condiciones conjuntas:
  1. Su estructura deductiva es **lógicamente válida**.
  2. Todas sus premisas constitutivas son **materialmente verdaderas** en la realidad.
- Si un argumento es sólido, su conclusión está garantizada como materialmente verdadera."""
    },
    {
        "user": "¿Qué describe la hipótesis de la tasa natural de desempleo y cómo modifica la curva de Phillips?",
        "assistant": r"""La **curva de Phillips originaria** (A. W. Phillips, 1958) postulaba una relación empírica inversa y estable entre la inflación salarial y el desempleo: los gobiernos podían elegir permanentemente menos desempleo a cambio de tolerar una mayor inflación mediante políticas fiscales y monetarias expansivas.

### La crítica de Milton Friedman y Edmund Phelps (1968)
Friedman y Phelps demostraron que esta relación de intercambio solo opera a **corto plazo** debido a la **ilusión monetaria transitoria**. Introdujeron el concepto de la **tasa natural de desempleo** (o NAIRU, *tasa de desempleo no aceleradora de la inflación*).

### Dinámica temporal y expectativas adaptativas

1. **Corto plazo**:
   - Una inyección monetaria imprevista eleva la demanda agregada y los precios.
   - Las empresas perciben ingresos mayores y contratan más personal; los trabajadores aceptan empleo porque los salarios nominales han subido, sin percatarse de que el poder adquisitivo real no ha crecido.
   - El desempleo cae temporalmente por debajo de su nivel natural ($u < u_n$) a costa de mayor inflación.

2. **Largo plazo (Ajuste de expectativas)**:
   - Al cabo de un tiempo, los trabajadores perciben que los precios al consumidor han subido, eliminando la ilusión monetaria.
   - En las siguientes negociaciones colectivas, exigen alzas salariales proporcionales a la inflación esperada ($\pi^e$).
   - Los costes reales de producción aumentan para las empresas, revirtiendo la contratación.
   - El desempleo retorna a su **tasa natural ($u_n$)**, pero la economía queda estancada con un nivel de inflación permanentemente más alto.

### Conclusión sobre la curva de Phillips a largo plazo
A largo plazo, la curva de Phillips es una **línea recta completamente vertical** al nivel de la tasa natural de desempleo. La política monetaria es neutral en el largo plazo: no puede reducir el desempleo estructural y únicamente determina la tasa de inflación."""
    },
    {
        "user": "¿Cómo se diferencian el arbitraje, la mediación y la conciliación en los métodos alternativos de resolución de conflictos?",
        "assistant": r"""Los Métodos Alternativos de Solución de Conflictos (MASC) ofrecen vías extrajudiciales de resolución de disputas jurídicas que varían sustancialmente en el rol del tercero interviniente y en el carácter vinculante del acuerdo:

| Criterio | Mediación | Conciliación | Arbitraje |
| :--- | :--- | :--- | :--- |
| **Rol del tercero neutral** | **Facilitador pasivo**: Canaliza el diálogo, reestablece la comunicación y ayuda a las partes a encontrar su propia solución. | **Proponente activo**: Facilita la comunicación y tiene la potestad legal de proponer fórmulas de arreglo y soluciones equitativas concretas. | **Juez privado (Árbitro)**: Dirime la controversia juzgando las pruebas y argumentos como un tribunal formal. |
| **Poder de decisión** | Exclusivo de **las partes**. El mediador no puede imponer ni proponer decisiones. | Exclusivo de **las partes**. La fórmula propuesta por el conciliador puede ser libremente aceptada o rechazada. | Exclusivo del **árbitro** o tribunal arbitral; se sustrae a la voluntad de las partes una vez iniciado. |
| **Naturaleza del resultado** | Acuerdo transaccional contractual privado. | Acta de conciliación formal. | **Laudo arbitral**. |
| **Eficacia y ejecutabilidad** | Requiere elevación a escritura pública o homologación judicial para tener fuerza ejecutiva plena. | Posee mérito ejecutivo y hace tránsito a **cosa juzgada** directa por ministerio de la ley. | Equivale jurídicamente a una **sentencia judicial firme**; es de obligado acatamiento y ejecutable ante juzgados ordinarios. |
| **Vía de impugnación** | Acción de nulidad de contratos por vicios del consentimiento. | Acción de nulidad procesal/sustantiva. | Recurso extraordinario de **anulación de laudo** tasado estrictamente por causales formales (no revisión de fondo). |"""
    },
    {
        "user": "¿Qué conceptualiza Pierre Bourdieu mediante las nociones de habitus, campo y capital?",
        "assistant": r"""En su sociología de la práctica, Pierre Bourdieu formuló una teoría relacional para superar la dicotomía tradicional entre el subjetivismo fenomenológico y el objetivismo estructuralista. Su aparato teórico se articula mediante la relación:

$$\text{Práctica} = [(\text{Habitus}) \times (\text{Capital})] + \text{Campo}$$

### 1. El Habitus
- **Definición**: Estructuras estructuradas predispuestas a funcionar como estructuras estructurantes.
- **Naturaleza**: Conjunto duradero y transferible de esquemas de percepción, apreciación y acción internalizados por el individuo mediante la socialización temprana en una clase social determinada.
- **Función**: Funciona como un «sentido del juego» inconsciente que genera prácticas sociales acordes a la posición objetiva de clase sin requerir un cálculo racional deliberado.

### 2. El Campo
- **Definición**: Espacio social específico, estructurado y autónomo de relaciones de fuerza objetivas (ej. el campo artístico, académico, político, económico o jurídico).
- **Lógica de funcionamiento**: Cada campo posee sus propias reglas de juego internas, su valor fundamental en disputa (*illusio*) y una distribución asimétrica de posiciones entre agentes dominantes (que buscan conservar el orden) y recién llegados (que intentan subvertirlo).

### 3. Las Formas del Capital
El capital es el recurso escaso y socialmente valorado que otorga poder y determina la posición relativa de un agente dentro del campo:
- **Capital económico**: Recursos monetarios, patrimonio y activos financieros directamente convertibles en dinero.
- **Capital cultural**: Se manifiesta en tres estados:
  - *Incorporado*: Disposiciones mentales, lenguaje cultivated y gustos estéticos adquiridos (el habitus).
  - *Objetivado*: Bienes materiales culturales (obras de arte, libros, instrumentos).
  - *Institucionalizado*: Títulos académicos, certificaciones y credenciales educativas oficiales.
- **Capital social**: Red duradera de relaciones, contactos útiles, pertenencias a grupos selectos y redes de influencia recíproca.
- **Capital simbólico**: El reconocimiento, legitimidad, prestigio o honor social atribuido a las otras formas de capital cuando son percibidas como naturales y legítimas."""
    }
])
