"""Script para construir el Corpus Especializado en Java 21+ LTS para M0.1.

Cubre exhaustivamente las características modernas de Java 21+ LTS:
1. Virtual Threads (Project Loom): Thread.ofVirtual(), Executors.newVirtualThreadPerTaskExecutor(), Structured Concurrency, ScopedValue, mitigación de carrier thread pinning.
2. Pattern Matching for switch: Guardas 'when', switch exhaustivo sobre jerarquías sealed, case null, dominancia.
3. Record Patterns & Deconstruction: Records anidados desglosados en pattern matching (switch e instanceof), generic records.
4. Sequenced Collections: SequencedCollection, SequencedSet, SequencedMap, getFirst(), getLast(), reversed().
5. Unnamed Patterns and Variables: Uso idiomático de '_' en catch, lambdas, try-with-resources y deconstrucción de patrones.
6. Sealed Interfaces y Classes: Modelado de tipos algebraicos (ADT), Result/Either pattern, invariantes de dominio DDD.
7. APIs Modernas: HttpClient asíncrono (HTTP/2), Streams avanzados (Collectors.teeing), Text Blocks (\"\"\"), Foreign Function & Memory API (FFM).

Cada entrada incluye formato de instrucción/respuesta (Q&A de arquitectura) y completado de código idiomático y tipado.
Compatible con JsonlDataset y PackedSequenceIterator.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Resolver raíz del repositorio
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUT_DIR = REPO_ROOT / "data" / "corpus_code"
OUTPUT_FILE = OUTPUT_DIR / "codigo_java21_moderno_50k_tokens.jsonl"
LEGACY_OUTPUT_FILE = OUTPUT_DIR / "java21_modern.jsonl"
TOKENIZER_PATH = REPO_ROOT / "data" / "tokenizers" / "tokenizer.json"

DEFAULT_SYSTEM_PROMPT = (
    "Eres M0.1, una IA especializada en ingeniería de software, arquitectura de sistemas "
    "y programación moderna en Java 21+ LTS. Tu objetivo es proporcionar explicaciones rigurosas, "
    "código idiomático, fuertemente tipado y libre de obsolescencias de versiones anteriores de Java."
)


def create_record(
    prompt: str,
    response: str,
    category: str,
    task_type: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> Dict[str, Any]:
    """Crea una entrada compatible con JsonlDataset y herramientas de entrenamiento."""
    conversation = f"<|user|>\n{prompt.strip()}\n<|assistant|>\n{response.strip()}"
    return {
        "system": system_prompt,
        "conversation": conversation,
        "metadata": {
            "language": "java",
            "version": "21+",
            "category": category,
            "type": task_type,
        },
    }


def get_virtual_threads_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 1: Q&A - Arquitectura de Virtual Threads
    entries.append(
        create_record(
            prompt=(
                "Explica la arquitectura interna de los Virtual Threads en Java 21 (Project Loom). "
                "¿En qué se diferencian de los Platform Threads del sistema operativo a nivel de memoria "
                "y planificación, y por qué está terminantemente desaconsejado agruparlos en un pool de hilos?"
            ),
            response=(
                "### Arquitectura Interna de Virtual Threads en Java 21\n\n"
                "Los **Virtual Threads** (JEP 444) representan una implementación ligera de hilos gestionados "
                "por la Java Virtual Machine (JVM) en lugar de mapearse de manera 1:1 con hilos del kernel del sistema operativo.\n\n"
                "#### 1. Diferencias de Memoria y Planificación\n"
                "- **Platform Threads (Hilos de Plataforma):** Son envoltorios directos sobre hilos del SO (`pthread` en Linux). "
                "Cada uno reserva típicamente entre **1 MB y 2 MB** de memoria contigua para su stack en el espacio de memoria nativa. "
                "El scheduler del SO se encarga de cambiar de contexto entre ellos, lo que involucra transiciones de anillo de kernel costosas.\n"
                "- **Virtual Threads:** Son instancias de `java.lang.Thread` cuya pila de llamadas (stack frames) reside en la **memoria heap** "
                "de la JVM y crece dinámicamente según la necesidad (comenzando en tan solo unos cientos de bytes). Se ejecutan montados sobre "
                "un grupo reducido de hilos de plataforma llamados **Carrier Threads**, gestionados internamente por un `ForkJoinPool` en modo FIFO.\n"
                "- **Mecanismo de Desmontaje (Continuation):** Cuando un hilo virtual realiza una operación de I/O bloqueante (ej. lectura de socket, "
                "`Thread.sleep()`), la JVM preserva su stack frame en el heap y **desmonta** el hilo virtual del Carrier Thread, permitiendo que "
                "este último ejecute inmediatamente otro hilo virtual listo para procesar.\n\n"
                "#### 2. ¿Por qué NUNCA se debe usar un Thread Pool con Virtual Threads?\n"
                "En Java clásico, los pools de hilos (`ThreadPoolExecutor`) se creaban porque los hilos del SO son escasos y costosos de crear. "
                "Con los Virtual Threads, el paradigma cambia radicalmente:\n"
                "1. **Costo de creación despreciable:** Crear un hilo virtual cuesta casi lo mismo que instanciar un objeto ordinario.\n"
                "2. **Diseño 'Thread-per-request':** Cada tarea independiente debe tener su propio hilo virtual efímero que nace, ejecuta la tarea y muere.\n"
                "3. **Fugas de estado:** El pooling de hilos virtuales puede causar retención accidental de memoria en `ThreadLocal` y pérdida de aislamiento.\n"
                "4. **API recomendada:** Se debe utilizar `Executors.newVirtualThreadPerTaskExecutor()` administrado con `try-with-resources`."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 2: Code Completion - Orquestador con newVirtualThreadPerTaskExecutor
    entries.append(
        create_record(
            prompt=(
                "Implementa un servicio de backend en Java 21 que consulte en paralelo tres APIs externas "
                "(inventario, precios y calificaciones) para componer un `ProductAggregate`. "
                "Debes usar `Executors.newVirtualThreadPerTaskExecutor()` con la sintaxis de bloque `try-with-resources` "
                "y garantizar tiempos límite (timeouts) sin bloquear hilos de plataforma."
            ),
            response=(
                "Aquí tienes la implementación completa e idiomática en Java 21:\n\n"
                "```java\n"
                "package com.m01.aggregation.service;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.time.Duration;\n"
                "import java.util.concurrent.*;\n\n"
                "public final class ProductAggregationService {\n\n"
                "    public record InventoryStatus(String sku, int stockAvailable) {}\n"
                "    public record PriceQuote(String sku, BigDecimal price, String currency) {}\n"
                "    public record ProductRating(String sku, double averageScore, int totalReviews) {}\n"
                "    public record ProductAggregate(\n"
                "        String sku,\n"
                "        InventoryStatus inventory,\n"
                "        PriceQuote pricing,\n"
                "        ProductRating rating\n"
                "    ) {}\n\n"
                "    private final ExternalApiClient client;\n\n"
                "    public ProductAggregationService(ExternalApiClient client) {\n"
                "        this.client = client;\n"
                "    }\n\n"
                "    public ProductAggregate aggregateProduct(String sku, Duration timeout) {\n"
                "        // En Java 21, ExecutorService implementa AutoCloseable.\n"
                "        // El cierre del try-with-resources bloquea hasta que todas las tareas en el executor concluyan o sean interrumpidas.\n"
                "        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {\n"
                "            Future<InventoryStatus> inventoryFuture = executor.submit(() -> client.fetchInventory(sku));\n"
                "            Future<PriceQuote> priceFuture = executor.submit(() -> client.fetchPrice(sku));\n"
                "            Future<ProductRating> ratingFuture = executor.submit(() -> client.fetchRating(sku));\n\n"
                "            long timeoutMs = timeout.toMillis();\n"
                "            InventoryStatus inventory = inventoryFuture.get(timeoutMs, TimeUnit.MILLISECONDS);\n"
                "            PriceQuote price = priceFuture.get(timeoutMs, TimeUnit.MILLISECONDS);\n"
                "            ProductRating rating = ratingFuture.get(timeoutMs, TimeUnit.MILLISECONDS);\n\n"
                "            return new ProductAggregate(sku, inventory, price, rating);\n"
                "        } catch (TimeoutException e) {\n"
                "            throw new IllegalStateException(\"Tiempo de espera agotado al consultar servicios remotos para SKU: \" + sku, e);\n"
                "        } catch (ExecutionException e) {\n"
                "            throw new RuntimeException(\"Error en la ejecución de tareas concurrentes: \" + e.getCause().getMessage(), e.getCause());\n"
                "        } catch (InterruptedException e) {\n"
                "            Thread.currentThread().interrupt();\n"
                "            throw new RuntimeException(\"Operación interrumpida durante la agregación\", e);\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave de Java 21:\n"
                "1. `Executors.newVirtualThreadPerTaskExecutor()` crea un hilo virtual dedicado por cada tarea enviada.\n"
                "2. La interfaz `ExecutorService` extiende `AutoCloseable` desde Java 19+, lo que permite invocar implícitamente `close()` al salir del bloque `try`, "
                "asegurando la cancelación y espera limpia de tareas huérfanas."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 3: Q&A - Carrier Thread Pinning
    entries.append(
        create_record(
            prompt=(
                "¿Qué es el fenómeno de 'Carrier Thread Pinning' en Java 21 y por qué los bloques `synchronized` "
                "pueden degradar severamente el rendimiento de una aplicación que utiliza Virtual Threads? "
                "¿Cuál es la alternativa idiomática recomendada?"
            ),
            response=(
                "### El Fenómeno de Carrier Thread Pinning en Java 21\n\n"
                "#### 1. ¿Qué es el Pinning?\n"
                "Se produce **Carrier Thread Pinning** cuando un Virtual Thread queda 'anclado' a su Carrier Thread (el hilo de plataforma subyacente "
                "del `ForkJoinPool`) e **impide que la JVM lo desmonte** al encontrarse con una operación de bloqueo I/O o de sincronización.\n\n"
                "Cuando ocurre el anclaje:\n"
                "- Si el Virtual Thread realiza una lectura de red lenta o una consulta a base de datos, el Carrier Thread queda completamente bloqueado en el SO.\n"
                "- Si se agotan los Carrier Threads del pool, no se pueden atender otros miles de Virtual Threads en cola, provocando contención severa y latencia masiva.\n\n"
                "#### 2. Causas Principales del Pinning\n"
                "1. **Monitores intrínsecos (`synchronized`):** Si un Virtual Thread bloquea un cerrojo con `synchronized (lock)` o un método sincronizado "
                "y dentro realiza una operación I/O bloqueante, la estructura de la JVM no puede desasociar la pila nativa del carrier thread.\n"
                "2. **Métodos nativos (JNI) o Foreign Memory:** Ejecución de código nativo C/C++ que realiza llamadas de sistema bloqueantes.\n\n"
                "#### 3. Diagnóstico en Producción\n"
                "Se puede detectar ejecutando la JVM con la bandera de diagnóstico:\n"
                "```bash\n"
                "-Djdk.tracePinnedThreads=full\n"
                "```\n"
                "Esto imprimirá la traza completa de la pila cuando un hilo virtual quede anclado a un carrier thread.\n\n"
                "#### 4. Solución Idiomática: `ReentrantLock`\n"
                "En Java 21, la implementación de `java.util.concurrent.locks.ReentrantLock` y `ReentrantReadWriteLock` fue refactorizada "
                "para cooperar con el mecanismo de continuaciones de Loom. Cuando un Virtual Thread espera un `ReentrantLock`, la JVM desmonta "
                "el hilo de forma transparente sin anclar el Carrier Thread."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 4: Code Completion - ReentrantLock vs Synchronized en Virtual Threads
    entries.append(
        create_record(
            prompt=(
                "Refactoriza la siguiente clase legada de Java 8 que sufre de Carrier Thread Pinning "
                "hacia una versión de Java 21 optimizada para Virtual Threads utilizando `ReentrantLock` y `Condition`:\n\n"
                "```java\n"
                "public class LegacyBoundedBuffer<T> {\n"
                "    private final Object[] buffer;\n"
                "    private int count, putIndex, takeIndex;\n"
                "    public LegacyBoundedBuffer(int capacity) { buffer = new Object[capacity]; }\n"
                "    public synchronized void put(T x) throws InterruptedException {\n"
                "        while (count == buffer.length) wait();\n"
                "        buffer[putIndex] = x;\n"
                "        if (++putIndex == buffer.length) putIndex = 0;\n"
                "        count++;\n"
                "        notifyAll();\n"
                "    }\n"
                "    public synchronized T take() throws InterruptedException {\n"
                "        while (count == 0) wait();\n"
                "        T x = (T) buffer[takeIndex];\n"
                "        if (++takeIndex == buffer.length) takeIndex = 0;\n"
                "        count--;\n"
                "        notifyAll();\n"
                "        return x;\n"
                "    }\n"
                "}\n"
                "```"
            ),
            response=(
                "Aquí está la refactorización idiomática para Java 21 sin riesgo de Carrier Thread Pinning:\n\n"
                "```java\n"
                "package com.m01.concurrency;\n\n"
                "import java.util.Objects;\n"
                "import java.util.concurrent.locks.Condition;\n"
                "import java.util.concurrent.locks.ReentrantLock;\n\n"
                "public final class ModernBoundedBuffer<T> {\n"
                "    private final Object[] items;\n"
                "    private final ReentrantLock lock = new ReentrantLock();\n"
                "    private final Condition notFull = lock.newCondition();\n"
                "    private final Condition notEmpty = lock.newCondition();\n\n"
                "    private int count = 0;\n"
                "    private int putIndex = 0;\n"
                "    private int takeIndex = 0;\n\n"
                "    public ModernBoundedBuffer(int capacity) {\n"
                "        if (capacity <= 0) {\n"
                "            throw new IllegalArgumentException(\"La capacidad debe ser estrictamente positiva: \" + capacity);\n"
                "        }\n"
                "        this.items = new Object[capacity];\n"
                "    }\n\n"
                "    public void put(T item) throws InterruptedException {\n"
                "        Objects.requireNonNull(item, \"El elemento no puede ser nulo\");\n"
                "        lock.lockInterruptibly();\n"
                "        try {\n"
                "            while (count == items.length) {\n"
                "                notFull.await(); // Desmonta el virtual thread sin anclar el carrier\n"
                "            }\n"
                "            items[putIndex] = item;\n"
                "            if (++putIndex == items.length) putIndex = 0;\n"
                "            count++;\n"
                "            notEmpty.signal(); // Señalización dirigida a consumidores\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    @SuppressWarnings(\"unchecked\")\n"
                "    public T take() throws InterruptedException {\n"
                "        lock.lockInterruptibly();\n"
                "        try {\n"
                "            while (count == 0) {\n"
                "                notEmpty.await(); // Desmonta el virtual thread de forma cooperativa\n"
                "            }\n"
                "            T item = (T) items[takeIndex];\n"
                "            items[takeIndex] = null; // Favorece la recolección de basura\n"
                "            if (++takeIndex == items.length) takeIndex = 0;\n"
                "            count--;\n"
                "            notFull.signal(); // Señalización dirigida a productores\n"
                "            return item;\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public int size() {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            return count;\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Mejoras de Arquitectura:\n"
                "1. **Cero Pinning:** `ReentrantLock` desasocia el hilo virtual de su hilo de transporte durante `await()` y `lockInterruptibly()`.\n"
                "2. **Condiciones Separadas (`notFull` y `notEmpty`):** En lugar de `notifyAll()`, que despierta innecesariamente a todos los hilos produciendo el efecto estampida (thundering herd), se señaliza únicamente a la condición interesada.\n"
                "3. **Higiene de Memoria:** Limpia las referencias en `items[takeIndex] = null` para evitar retención innecesaria de objetos en el Heap."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 5: Q&A - Structured Concurrency y Scoped Values
    entries.append(
        create_record(
            prompt=(
                "Describe la propuesta de 'Structured Concurrency' (JEP 453) y 'Scoped Values' (JEP 446) en Java 21+. "
                "¿Cómo resuelven el problema de hilos huérfanos y la ineficiencia de los `ThreadLocal` tradicionales?"
            ),
            response=(
                "### Concurrencia Estructurada y Scoped Values en Java Moderno\n\n"
                "#### 1. Structured Concurrency (`StructuredTaskScope`)\n"
                "En el modelo no estructurado (`CompletableFuture`, `ExecutorService` asíncrono), las subtareas no están acotadas a la estructura léxica del código. "
                "Si una tarea falla o se cancela, otras tareas secundarias continúan ejecutándose en segundo plano consumiendo CPU y red (**hilos huérfanos**).\n\n"
                "**Concurrencia Estructurada** trata a un grupo de subtareas como una única unidad atómica de trabajo con dos políticas principales:\n"
                "1. `StructuredTaskScope.ShutdownOnFailure`: Ejecuta tareas concurrentes en paralelo. Si una falla, cancela inmediatamente a todas las demás y propaga la excepción.\n"
                "2. `StructuredTaskScope.ShutdownOnSuccess`: Devuelve el resultado de la primera tarea que complete exitosamente (ej. consulta redundante a múltiples servidores) y cancela las restantes.\n\n"
                "#### 2. Scoped Values (`ScopedValue<T>`) vs `ThreadLocal<T>`\n"
                "`ThreadLocal` tiene serias desventajas en entornos con millones de Virtual Threads:\n"
                "- **Mutabilidad ilimitada:** Cualquier método intermedio puede modificar un `ThreadLocal`, rompiendo la predictibilidad.\n"
                "- **Fuga de memoria:** El ciclo de vida de los valores puede superar la necesidad real si el hilo no se limpia.\n"
                "- **Copia costosa en herencia:** `InheritableThreadLocal` clona el mapa completo de variables cada vez que se crea un hilo nuevo.\n\n"
                "`ScopedValue` soluciona esto:\n"
                "- **Inmutable:** Una vez ligado con `ScopedValue.where(KEY, value).run(...)`, el valor no cambia durante el alcance léxico.\n"
                "- **Ciclo de vida determinista:** Al salir del bloque `run()` o `call()`, el valor queda automáticamente fuera de alcance.\n"
                "- **Compartición sin costo:** Múltiples millones de Virtual Threads pueden heredar `ScopedValue` con punteros de lectura eficientes en memoria sin copias profundas."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 6: Code Completion - Thread.ofVirtual Factory
    entries.append(
        create_record(
            prompt=(
                "Escribe un componente `WorkerPoolFactory` en Java 21 que configure una `ThreadFactory` "
                "personalizada para Virtual Threads usando `Thread.ofVirtual()`. Debe configurar prefijos de nombres "
                "de hilo (`worker-vt-1`, `worker-vt-2`), deshabilitar la herencia de ThreadLocals por optimización "
                "y registrar un manejador de excepciones no capturadas (`UncaughtExceptionHandler`)."
            ),
            response=(
                "Aquí tienes la implementación idiomática usando la API fluida `Thread.ofVirtual()` de Java 21:\n\n"
                "```java\n"
                "package com.m01.concurrency;\n\n"
                "import java.lang.Thread.UncaughtExceptionHandler;\n"
                "import java.util.concurrent.ThreadFactory;\n"
                "import java.util.logging.Level;\n"
                "import java.util.logging.Logger;\n\n"
                "public final class WorkerPoolFactory {\n\n"
                "    private static final Logger LOGGER = Logger.getLogger(WorkerPoolFactory.class.getName());\n\n"
                "    private WorkerPoolFactory() {}\n\n"
                "    public static ThreadFactory createVirtualThreadFactory(String prefix) {\n"
                "        UncaughtExceptionHandler exceptionHandler = (thread, throwable) -> {\n"
                "            LOGGER.log(Level.SEVERE,\n"
                "                \"Excepción no capturada en hilo virtual [\" + thread.getName() + \"]: \" + throwable.getMessage(),\n"
                "                throwable);\n"
                "        };\n\n"
                "        return Thread.ofVirtual()\n"
                "            .name(prefix, 1) // Genera prefijo-1, prefijo-2, ...\n"
                "            .inheritInheritableThreadLocals(false) // Optimización de memoria al descartar copias de contexto innecesarias\n"
                "            .uncaughtExceptionHandler(exceptionHandler)\n"
                "            .factory();\n"
                "    }\n\n"
                "    public static Thread startVirtualTask(String name, Runnable task) {\n"
                "        return Thread.ofVirtual()\n"
                "            .name(name)\n"
                "            .start(task);\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Detalles de Diseño:\n"
                "- `.name(prefix, 1)` asigna nombres autoincrementales a los hilos virtuales, facilitando enormemente el volcado de hilos (thread dump) y diagnóstico con `jcmd`.\n"
                "- `.inheritInheritableThreadLocals(false)` previene la copia innecesaria de mapas de `InheritableThreadLocal`, reduciendo el footprint de memoria."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )
    return entries


def get_pattern_matching_switch_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 7: Q&A - Pattern Matching for switch y Exhaustividad
    entries.append(
        create_record(
            prompt=(
                "Analiza la evolución de la sentencia `switch` en Java 21 (JEP 440 y JEP 441). "
                "Explica qué es un switch exhaustivo sobre una jerarquía `sealed`, cómo funcionan las guardas `when` "
                "y por qué omitir la cláusula `default` es una buena práctica en dominios cerrados."
            ),
            response=(
                "### Pattern Matching for switch en Java 21\n\n"
                "En Java 21, la instrucción y expresión `switch` maduró definitivamente como una herramienta de alto nivel para manipulación "
                "de tipos algebraicos (Pattern Matching for switch - JEP 441).\n\n"
                "#### 1. Exhaustividad en Jerarquías `sealed`\n"
                "Cuando un `switch` evalúa una interfaz o clase `sealed` cuyos subtipos permitidos están declarados explícitamente (`permits A, B, C`), "
                "el compilador de Java realiza un análisis de cobertura total (**exhaustiveness analysis**):\n"
                "- Si se cubren todos los subtipos posibles, el compilador no exige una cláusula `default`.\n"
                "- Si en el futuro un desarrollador añade un nuevo subtipo a la jerarquía (`permits A, B, C, D`), cualquier `switch` que no lo contemple "
                "fallará inmediatamente en **tiempo de compilación** con un error de compilación.\n\n"
                "#### 2. ¿Por qué NO usar `default` en dominios `sealed`?\n"
                "Usar `default: throw new IllegalArgumentException(...)` en una jerarquía sellada destruye la comprobación en tiempo de compilación. "
                "Si se añade un nuevo estado al dominio, el error se manifestará en producción en tiempo de ejecución en lugar de obligar al programador "
                "a manejarlo durante la compilación.\n\n"
                "#### 3. Guardas `when`\n"
                "Las guardas `when` permiten incorporar condiciones booleanas directamente en el selector del patrón:\n"
                "```java\n"
                "case Order o when o.totalAmount().compareTo(THRESHOLD) > 0 -> processHighPriority(o);\n"
                "case Order o -> processStandard(o);\n"
                "```\n"
                "El compilador comprueba la **dominancia**: el caso más específico con la guarda `when` debe posicionarse obligatoriamente "
                "antes del caso genérico sin guarda, de lo contrario se emitirá un error de compilación por código inalcanzable."
            ),
            category="pattern_matching",
            task_type="architecture_qa",
        )
    )

    # Entry 8: Code Completion - Motor de Facturación con switch y guardas 'when'
    entries.append(
        create_record(
            prompt=(
                "Diseña un sistema de cálculo de tarifas mensuales en Java 21 para una plataforma SaaS. "
                "Define una jerarquía sellada `BillingPlan` con implementaciones `FreePlan`, `ProPlan` y `EnterprisePlan`. "
                "Implementa un método `calculateMonthlyCharge` que use una expresión `switch` con guardas `when` "
                "para aplicar descuentos por volumen de usuarios y planes anuales, asegurando exhaustividad sin cláusula `default`."
            ),
            response=(
                "Aquí tienes la implementación con jerarquías `sealed` y expresiones `switch` exhaustivas en Java 21:\n\n"
                "```java\n"
                "package com.m01.billing;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.math.RoundingMode;\n"
                "import java.util.Objects;\n\n"
                "public final class BillingService {\n\n"
                "    public sealed interface BillingPlan permits FreePlan, ProPlan, EnterprisePlan {}\n\n"
                "    public record FreePlan() implements BillingPlan {}\n\n"
                "    public record ProPlan(\n"
                "        int activeSeats,\n"
                "        boolean annualCommitment\n"
                "    ) implements BillingPlan {\n"
                "        public ProPlan {\n"
                "            if (activeSeats <= 0) throw new IllegalArgumentException(\"Las plazas activas deben ser positivas\");\n"
                "        }\n"
                "    }\n\n"
                "    public record EnterprisePlan(\n"
                "        int activeSeats,\n"
                "        boolean dedicatedSupport,\n"
                "        BigDecimal negotiatedDiscount\n"
                "    ) implements BillingPlan {\n"
                "        public EnterprisePlan {\n"
                "            Objects.requireNonNull(negotiatedDiscount, \"El descuento no puede ser nulo\");\n"
                "            if (activeSeats <= 0) throw new IllegalArgumentException(\"Las plazas activas deben ser positivas\");\n"
                "        }\n"
                "    }\n\n"
                "    public record InvoiceBreakdown(String planName, BigDecimal totalAmount, String discountReason) {}\n\n"
                "    public InvoiceBreakdown calculateMonthlyCharge(BillingPlan plan) {\n"
                "        Objects.requireNonNull(plan, \"El plan de facturación es requerido\");\n\n"
                "        // Switch exhaustivo sobre jerarquía sellada sin necesidad de cláusula default\n"
                "        return switch (plan) {\n"
                "            case FreePlan _ -> \n"
                "                new InvoiceBreakdown(\"Free\", BigDecimal.ZERO, \"Sin costo para nivel inicial\");\n\n"
                "            case ProPlan p when p.annualCommitment() && p.activeSeats() >= 20 -> {\n"
                "                BigDecimal base = BigDecimal.valueOf(p.activeSeats()).multiply(BigDecimal.valueOf(25.00));\n"
                "                BigDecimal discounted = base.multiply(BigDecimal.valueOf(0.80)).setScale(2, RoundingMode.HALF_UP);\n"
                "                yield new InvoiceBreakdown(\"Pro (Anual + Alto Volumen)\", discounted, \"20% descuento por compromiso anual y >20 plazas\");\n"
                "            }\n\n"
                "            case ProPlan p when p.annualCommitment() -> {\n"
                "                BigDecimal base = BigDecimal.valueOf(p.activeSeats()).multiply(BigDecimal.valueOf(28.00));\n"
                "                BigDecimal discounted = base.multiply(BigDecimal.valueOf(0.90)).setScale(2, RoundingMode.HALF_UP);\n"
                "                yield new InvoiceBreakdown(\"Pro (Anual)\", discounted, \"10% descuento por suscripción anual\");\n"
                "            }\n\n"
                "            case ProPlan p -> {\n"
                "                BigDecimal total = BigDecimal.valueOf(p.activeSeats()).multiply(BigDecimal.valueOf(32.00));\n"
                "                yield new InvoiceBreakdown(\"Pro (Mensual estándar)\", total, \"Tarifa regular por plaza\");\n"
                "            }\n\n"
                "            case EnterprisePlan e when e.dedicatedSupport() -> {\n"
                "                BigDecimal seatCost = BigDecimal.valueOf(e.activeSeats()).multiply(BigDecimal.valueOf(50.00));\n"
                "                BigDecimal supportCost = BigDecimal.valueOf(500.00);\n"
                "                BigDecimal subtotal = seatCost.add(supportCost);\n"
                "                BigDecimal finalTotal = subtotal.subtract(e.negotiatedDiscount()).max(BigDecimal.ZERO);\n"
                "                yield new InvoiceBreakdown(\"Enterprise (Con Soporte VIP)\", finalTotal, \"Soporte dedicado incluido con descuento negociado\");\n"
                "            }\n\n"
                "            case EnterprisePlan e -> {\n"
                "                BigDecimal seatCost = BigDecimal.valueOf(e.activeSeats()).multiply(BigDecimal.valueOf(45.00));\n"
                "                BigDecimal finalTotal = seatCost.subtract(e.negotiatedDiscount()).max(BigDecimal.ZERO);\n"
                "                yield new InvoiceBreakdown(\"Enterprise (Estándar)\", finalTotal, \"Descuento corporativo aplicado\");\n"
                "            }\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Aspectos Clave de Compilación:\n"
                "1. **Garantía en Tiempo de Compilación:** Al no incluir `default`, si se agrega `record CustomPlan() implements BillingPlan`, el compilador detendrá la construcción hasta que se maneje ese caso.\n"
                "2. **Dominancia Estricta:** Las ramas con `when p.annualCommitment() && p.activeSeats() >= 20` preceden a las de `when p.annualCommitment()`, y estas a su vez preceden al caso general `ProPlan p`."
            ),
            category="pattern_matching",
            task_type="code_completion",
        )
    )

    # Entry 9: Q&A - Manejo de null en Switch y Dominancia
    entries.append(
        create_record(
            prompt=(
                "¿Cómo maneja Java 21 el valor `null` dentro de una instrucción o expresión `switch`? "
                "Compara este comportamiento con las versiones clásicas de Java y explica las reglas de dominancia con `case null, default`."
            ),
            response=(
                "### Manejo de `null` y Reglas de Dominancia en Java 21\n\n"
                "#### 1. Comportamiento Histórico (Java <= 17)\n"
                "En Java clásico, evaluar una variable nula en un switch lanzaba un `NullPointerException` de forma inmediata e ineludible al inicio de la evaluación:\n"
                "```java\n"
                "String s = null;\n"
                "switch (s) { // ¡Lanza NullPointerException antes de evaluar ningún case!\n"
                "    case \"A\" -> System.out.println(\"A\");\n"
                "    default -> System.out.println(\"Otro\");\n"
                "}\n"
                "```\n\n"
                "#### 2. Soporte Explícito de `null` en Java 21\n"
                "Java 21 introduce etiquetas de caso explícitas para valores nulos:\n"
                "- `case null -> ...`: Captura específicamente la referencia nula de forma segura sin lanzar excepción.\n"
                "- `case null, default -> ...`: Combina en una sola rama tanto la ausencia de valor (`null`) como cualquier valor que no coincida con los patrones previos.\n\n"
                "#### 3. Reglas de Dominancia (Dominance Rules)\n"
                "El compilador prohíbe que un patrón más general preceda a un patrón más específico:\n"
                "1. Si se coloca un patrón de tipo totalizador (como `Object o`), este domina sobre `String s` y sobre `case null`. Por ello, `String s` debe ubicarse antes que `Object o`.\n"
                "2. Si se define `case null`, debe ubicarse antes de cualquier patrón totalizador incondicional.\n"
                "3. Si un switch incluye `case null, default ->`, dicha etiqueta debe ser la última del bloque."
            ),
            category="pattern_matching",
            task_type="architecture_qa",
        )
    )

    # Entry 10: Code Completion - Validador de Eventos Webhook con Null Handling
    entries.append(
        create_record(
            prompt=(
                "Escribe un procesador de webhooks seguro en Java 21 que gestione eventos entrantes de pasarelas de pago. "
                "Define una jerarquía sellada `WebhookEvent` con eventos `PaymentReceived`, `ChargebackInitiated` y `DisputeResolved`. "
                "Maneja explícitamente `case null` y utiliza pattern matching con `when` para descartar eventos con firmas inválidas."
            ),
            response=(
                "Aquí tienes la implementación con manejo seguro de `case null` y verificación de integridad criptográfica:\n\n"
                "```java\n"
                "package com.m01.webhooks;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.time.Instant;\n\n"
                "public final class WebhookProcessor {\n\n"
                "    public sealed interface WebhookEvent permits PaymentReceived, ChargebackInitiated, DisputeResolved {\n"
                "        String eventId();\n"
                "        Instant timestamp();\n"
                "        String signature();\n"
                "    }\n\n"
                "    public record PaymentReceived(String eventId, Instant timestamp, String signature, BigDecimal amount, String currency) implements WebhookEvent {}\n"
                "    public record ChargebackInitiated(String eventId, Instant timestamp, String signature, String reasonCode, BigDecimal disputeAmount) implements WebhookEvent {}\n"
                "    public record DisputeResolved(String eventId, Instant timestamp, String signature, boolean accepted) implements WebhookEvent {}\n\n"
                "    public enum ProcessStatus { PROCESSED, INVALID_SIGNATURE, SUSPICIOUS, REJECTED }\n\n"
                "    public record ProcessingResult(ProcessStatus status, String auditMessage) {}\n\n"
                "    private boolean verifySignature(String signature) {\n"
                "        return signature != null && signature.startsWith(\"sha256=\") && signature.length() == 71;\n"
                "    }\n\n"
                "    public ProcessingResult process(WebhookEvent event) {\n"
                "        return switch (event) {\n"
                "            case null -> \n"
                "                new ProcessingResult(ProcessStatus.REJECTED, \"Cuerpo del webhook nulo o malformado\");\n\n"
                "            case WebhookEvent e when !verifySignature(e.signature()) -> \n"
                "                new ProcessingResult(ProcessStatus.INVALID_SIGNATURE, \"Firma HMAC no válida para evento: \" + e.eventId());\n\n"
                "            case PaymentReceived p when p.amount().compareTo(BigDecimal.valueOf(100_000)) > 0 -> \n"
                "                new ProcessingResult(ProcessStatus.SUSPICIOUS, \"Pago mayor a 100K transferido a revisión antifraude manual: \" + p.eventId());\n\n"
                "            case PaymentReceived p -> \n"
                "                new ProcessingResult(ProcessStatus.PROCESSED, \"Pago abonado satisfactoriamente por \" + p.amount() + \" \" + p.currency());\n\n"
                "            case ChargebackInitiated c -> \n"
                "                new ProcessingResult(ProcessStatus.PROCESSED, \"Contracargo registrado. Motivo: \" + c.reasonCode() + \", monto: \" + c.disputeAmount());\n\n"
                "            case DisputeResolved d -> \n"
                "                new ProcessingResult(ProcessStatus.PROCESSED, \"Disputa finalizada. Resultado favorable: \" + d.accepted());\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "- `case null ->`: Protege contra `NullPointerException` sin necesidad de verificaciones `if (event == null)` periféricas.\n"
                "- `case WebhookEvent e when !verifySignature(e.signature())`: Filtro de seguridad prioritario que intercepta cualquier evento no firmado antes de inspeccionar subtipos particulares."
            ),
            category="pattern_matching",
            task_type="code_completion",
        )
    )

    return entries


def get_record_patterns_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 11: Q&A - Record Patterns y Desestructuración Anidada
    entries.append(
        create_record(
            prompt=(
                "Explica qué son los Record Patterns en Java 21 (JEP 440). ¿Cómo facilitan la desestructuración "
                "de tipos producto (records) y de qué manera interactúan con la jerarquía de tipos y la seguridad en tiempo de compilación?"
            ),
            response=(
                "### Record Patterns y Desestructuración en Java 21\n\n"
                "Los **Record Patterns** permiten descomponer una instancia de un `record` en sus componentes individuales directamente "
                "en las cláusulas `instanceof` y `switch` sin necesidad de invocar métodos accesores explícitos (`point.x()`, `point.y()`).\n\n"
                "#### 1. Sintaxis Básica y Desestructuración Anidada\n"
                "Consideremos un modelo de coordenadas:\n"
                "```java\n"
                "public record Point(int x, int y) {}\n"
                "public record ColoredPoint(Point point, Color color) {}\n"
                "```\n"
                "- **Clásico (Java 16-17):**\n"
                "```java\n"
                "if (obj instanceof ColoredPoint cp) {\n"
                "    Point p = cp.point();\n"
                "    int x = p.x();\n"
                "}\n"
                "```\n"
                "- **Con Record Patterns (Java 21):**\n"
                "```java\n"
                "if (obj instanceof ColoredPoint(Point(int x, int y), Color color)) {\n"
                "    System.out.println(\"X: \" + x + \", Color: \" + color);\n"
                "}\n"
                "```\n"
                "El compilador extrae automáticamente las variables de componentes locales (`x`, `y`, `color`) en el ámbito del bloque.\n\n"
                "#### 2. Ventajas Arquitectónicas\n"
                "1. **Código declarativo y libre de boilerplate:** El código expresa exactamente la forma de los datos esperados en lugar de pasos de navegación imperativa.\n"
                "2. **Seguridad y compatibilidad binaria:** Si la definición del record cambia (por ejemplo, se añade una coordenada `z`), el patrón desestructurador no compilará, forzando la actualización sincronizada en todos los consumidores.\n"
                "3. **Inferencia con `var`:** Se puede utilizar `var` dentro del patrón (`ColoredPoint(Point(var x, var y), var color)`), preservando la tipificación estricta del compilador."
            ),
            category="record_patterns",
            task_type="architecture_qa",
        )
    )

    # Entry 12: Code Completion - Motor Geométrico con Deconstrucción Anidada
    entries.append(
        create_record(
            prompt=(
                "Implementa un evaluador geométrico en Java 21 para un motor de renderizado 2D. "
                "Define records para `Point(double x, double y)`, `Circle(Point center, double radius)` "
                "y `Rectangle(Point topLeft, Point bottomRight)`. Escribe un método `detectProximity` "
                "que desestructure las figuras anidadas en un `switch` con guardas `when` para alertar colisiones de proximidad."
            ),
            response=(
                "Aquí tienes la implementación completa utilizando deconstrucción anidada de records en Java 21:\n\n"
                "```java\n"
                "package com.m01.geometry;\n\n"
                "public final class GeometryEngine {\n\n"
                "    public record Point(double x, double y) {\n"
                "        public double distanceTo(Point other) {\n"
                "            double dx = this.x - other.x();\n"
                "            double dy = this.y - other.y();\n"
                "            return Math.hypot(dx, dy);\n"
                "        }\n"
                "    }\n\n"
                "    public sealed interface Shape permits Circle, Rectangle {}\n\n"
                "    public record Circle(Point center, double radius) implements Shape {\n"
                "        public Circle {\n"
                "            if (radius <= 0) throw new IllegalArgumentException(\"Radio inválido: \" + radius);\n"
                "        }\n"
                "    }\n\n"
                "    public record Rectangle(Point topLeft, Point bottomRight) implements Shape {\n"
                "        public Rectangle {\n"
                "            if (bottomRight.x() <= topLeft.x() || topLeft.y() <= bottomRight.y()) {\n"
                "                throw new IllegalArgumentException(\"Coordenadas de rectángulo inconsistentes\");\n"
                "            }\n"
                "        }\n"
                "    }\n\n"
                "    public record CollisionWarning(boolean critical, String description) {}\n\n"
                "    public CollisionWarning evaluateThreat(Shape shape, Point targetLocation, double proximityThreshold) {\n"
                "        return switch (shape) {\n"
                "            // Desestructuración anidada directa de Circle y su Point central\n"
                "            case Circle(Point(double cx, double cy), double r) \n"
                "                when targetLocation.distanceTo(new Point(cx, cy)) <= (r + proximityThreshold) -> {\n"
                "                    double dist = targetLocation.distanceTo(new Point(cx, cy));\n"
                "                    boolean isDirectHit = dist <= r;\n"
                "                    yield new CollisionWarning(isDirectHit, \n"
                "                        \"Círculo en (\" + cx + \",\" + cy + \") en rango crítico. Distancia centro: \" + dist);\n"
                "                }\n\n"
                "            case Circle(Point(var cx, var cy), var _) -> \n"
                "                new CollisionWarning(false, \"Círculo en (\" + cx + \",\" + cy + \") fuera del umbral de alerta\");\n\n"
                "            // Desestructuración anidada de dos puntos en Rectangle\n"
                "            case Rectangle(Point(double x1, double y1), Point(double x2, double y2)) \n"
                "                when targetLocation.x() >= (x1 - proximityThreshold) && targetLocation.x() <= (x2 + proximityThreshold) &&\n"
                "                     targetLocation.y() <= (y1 + proximityThreshold) && targetLocation.y() >= (y2 - proximityThreshold) -> {\n"
                "                    boolean inside = targetLocation.x() >= x1 && targetLocation.x() <= x2 &&\n"
                "                                     targetLocation.y() <= y1 && targetLocation.y() >= y2;\n"
                "                    yield new CollisionWarning(inside, \n"
                "                        \"Rectángulo bounds [\" + x1 + \",\" + y1 + \" a \" + x2 + \",\" + y2 + \"] bajo proximidad\");\n"
                "                }\n\n"
                "            case Rectangle(Point(var x1, var _), Point(var x2, var _)) -> \n"
                "                new CollisionWarning(false, \"Rectángulo en rango seguro horizontal: \" + x1 + \" a \" + x2);\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Relevantes de Java 21:\n"
                "1. `case Circle(Point(double cx, double cy), double r)` deconstruye simultáneamente el círculo y su punto central sin invocar `shape.center().x()`.\n"
                "2. Uso de variables no nombradas `_` en `case Circle(Point(var cx, var cy), var _)` para componentes no requeridos."
            ),
            category="record_patterns",
            task_type="code_completion",
        )
    )

    # Entry 13: Code Completion - CQRS / Event Sourcing con Deconstrucción
    entries.append(
        create_record(
            prompt=(
                "Diseña un manejador de eventos financieros en una arquitectura CQRS en Java 21. "
                "Crea records anidados para `AccountId(String iban)`, `Money(BigDecimal amount, String currency)` "
                "y eventos `FundsTransferred(AccountId origin, AccountId destination, Money money)` "
                "y `AccountFrozen(AccountId account, String reason)`. Implementa un auditor que desestructure los records "
                "y rechace transacciones entre cuentas de divisas diferentes o con IBANs no válidos."
            ),
            response=(
                "Aquí tienes la implementación del agregador de eventos con deconstrucción exhaustiva en Java 21:\n\n"
                "```java\n"
                "package com.m01.banking.events;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.util.Objects;\n\n"
                "public final class FinancialEventAuditor {\n\n"
                "    public record AccountId(String iban) {\n"
                "        public AccountId {\n"
                "            Objects.requireNonNull(iban, \"IBAN no puede ser nulo\");\n"
                "            if (iban.length() < 15) throw new IllegalArgumentException(\"IBAN inválido por longitud: \" + iban);\n"
                "        }\n"
                "    }\n\n"
                "    public record Money(BigDecimal amount, String currency) {\n"
                "        public Money {\n"
                "            Objects.requireNonNull(amount, \"Monto no puede ser nulo\");\n"
                "            Objects.requireNonNull(currency, \"Moneda no puede ser nula\");\n"
                "            if (amount.compareTo(BigDecimal.ZERO) <= 0) {\n"
                "                throw new IllegalArgumentException(\"El monto de transferencia debe ser positivo: \" + amount);\n"
                "            }\n"
                "        }\n"
                "    }\n\n"
                "    public sealed interface DomainEvent permits FundsTransferred, AccountFrozen {}\n\n"
                "    public record FundsTransferred(AccountId origin, AccountId destination, Money money) implements DomainEvent {}\n"
                "    public record AccountFrozen(AccountId account, String reason) implements DomainEvent {}\n\n"
                "    public record AuditResult(boolean approved, String memo) {}\n\n"
                "    public AuditResult auditEvent(DomainEvent event, String nationalBankCurrency) {\n"
                "        return switch (event) {\n"
                "            // Deconstrucción profunda: extrae origin Iban, destination Iban, monto y moneda\n"
                "            case FundsTransferred(\n"
                "                AccountId(String srcIban),\n"
                "                AccountId(String dstIban),\n"
                "                Money(BigDecimal amt, String curr)\n"
                "            ) when !curr.equalsIgnoreCase(nationalBankCurrency) -> {\n"
                "                yield new AuditResult(false, \n"
                "                    \"Transferencia rechazada: Moneda extranjera no liquidable \" + curr + \" entre \" + srcIban + \" y \" + dstIban);\n"
                "            }\n\n"
                "            case FundsTransferred(\n"
                "                AccountId(String srcIban),\n"
                "                AccountId(String dstIban),\n"
                "                Money(BigDecimal amt, _)\n"
                "            ) when srcIban.equals(dstIban) -> {\n"
                "                yield new AuditResult(false, \"Rechazada: Origen y destino idénticos: \" + srcIban);\n"
                "            }\n\n"
                "            case FundsTransferred(\n"
                "                AccountId(String srcIban),\n"
                "                AccountId(String dstIban),\n"
                "                Money(BigDecimal amt, String curr)\n"
                "            ) -> {\n"
                "                yield new AuditResult(true, \n"
                "                    \"Transferencia aprobada por \" + amt + \" \" + curr + \" desde \" + srcIban + \" hacia \" + dstIban);\n"
                "            }\n\n"
                "            case AccountFrozen(AccountId(String iban), String reason) -> {\n"
                "                yield new AuditResult(true, \"Cuenta congelada registrada para auditoría legal: \" + iban + \". Causa: \" + reason);\n"
                "            }\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Beneficios de la Deconstrucción Profunda:\n"
                "- No hay llamadas intermedias `event.origin().iban()` ni comprobaciones complejas de null.\n"
                "- En `Money(BigDecimal amt, _)`, el carácter de variable no nombrada `_` omite la moneda cuando no es relevante para la guarda."
            ),
            category="record_patterns",
            task_type="code_completion",
        )
    )

    return entries


def get_sequenced_collections_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 14: Q&A - Sequenced Collections JEP 431
    entries.append(
        create_record(
            prompt=(
                "Describe la nueva jerarquía de Sequenced Collections introducida en Java 21 (JEP 431). "
                "¿Qué deficiencias históricas del Java Collections Framework resuelve y cómo funciona la vista `.reversed()` "
                "en términos de complejidad temporal y consumo de memoria?"
            ),
            response=(
                "### Sequenced Collections en Java 21 (JEP 431)\n\n"
                "#### 1. La Deficiencia Histórica en el Java Collections Framework\n"
                "Durante más de dos décadas, Java no contó con un tipo común para representar una colección con un orden de encuentro bien definido. "
                "Acceder al primer o último elemento requería sintaxis completamente dispares e incoherentes:\n"
                "- `List`: `list.get(0)` y `list.get(list.size() - 1)` (pero falla si está vacía con `IndexOutOfBoundsException`).\n"
                "- `Deque`: `deque.getFirst()` y `deque.getLast()`.\n"
                "- `SortedSet`: `sortedSet.first()` y `sortedSet.last()`.\n"
                "- `LinkedHashSet`: Requería iterar manualmente `set.iterator().next()` para obtener el primer elemento, y recorrer toda la colección para el último.\n\n"
                "#### 2. Las Nuevas Interfaces Unificadas\n"
                "Java 21 introduce tres interfaces clave en el paquete `java.util`:\n"
                "1. `SequencedCollection<E>`: Extiende `Collection<E>`. Métodos clave:\n"
                "   - `addFirst(E)`, `addLast(E)`\n"
                "   - `getFirst()`, `getLast()`\n"
                "   - `removeFirst()`, `removeLast()`\n"
                "   - `SequencedCollection<E> reversed()`\n"
                "2. `SequencedSet<E>`: Extiende `Set<E>` y `SequencedCollection<E>`. Implementado por `LinkedHashSet`, `TreeSet`.\n"
                "3. `SequencedMap<K, V>`: Extiende `Map<K, V>`. Métodos clave:\n"
                "   - `firstEntry()`, `lastEntry()`\n"
                "   - `pollFirstEntry()`, `pollLastEntry()`\n"
                "   - `putFirst(K, V)`, `putLast(K, V)`\n"
                "   - `SequencedMap<K, V> reversed()`\n"
                "   - `SequencedSet<K> sequencedKeySet()`\n\n"
                "#### 3. Complejidad y Semántica de `.reversed()`\n"
                "- **Complejidad Temporal:** $O(1)$. No clona ni copia los datos en un nuevo array.\n"
                "- **Consumo de Memoria:** $O(1)$. Devuelve una vista envoltorio (reverse-ordered view) que delega en la colección original.\n"
                "- **Mutabilidad Reflejada:** Las modificaciones realizadas en la vista invertida se reflejan inmediatamente en la colección original y viceversa."
            ),
            category="sequenced_collections",
            task_type="architecture_qa",
        )
    )

    # Entry 15: Code Completion - LRU Cache con SequencedMap
    entries.append(
        create_record(
            prompt=(
                "Implementa una caché LRU (Least Recently Used) genérica y thread-safe en Java 21 "
                "aprovechando las capacidades de `SequencedMap` (`LinkedHashMap`) con `firstEntry()`, `pollFirstEntry()` y `putLast()`. "
                "La caché debe mantener un límite estricto de elementos y soportar acceso reverso."
            ),
            response=(
                "Aquí tienes la implementación limpia de una caché LRU aprovechando `SequencedMap` en Java 21:\n\n"
                "```java\n"
                "package com.m01.cache;\n\n"
                "import java.util.LinkedHashMap;\n"
                "import java.util.Map;\n"
                "import java.util.Objects;\n"
                "import java.util.Optional;\n"
                "import java.util.SequencedMap;\n"
                "import java.util.concurrent.locks.ReentrantLock;\n\n"
                "public final class ModernLruCache<K, V> {\n\n"
                "    private final int maxCapacity;\n"
                "    private final SequencedMap<K, V> store;\n"
                "    private final ReentrantLock lock = new ReentrantLock();\n\n"
                "    public ModernLruCache(int maxCapacity) {\n"
                "        if (maxCapacity <= 0) {\n"
                "            throw new IllegalArgumentException(\"La capacidad debe ser mayor a 0: \" + maxCapacity);\n"
                "        }\n"
                "        this.maxCapacity = maxCapacity;\n"
                "        // LinkedHashMap conserva orden de encuentro secuencial\n"
                "        this.store = new LinkedHashMap<>(maxCapacity, 0.75f, false);\n"
                "    }\n\n"
                "    public void put(K key, V value) {\n"
                "        Objects.requireNonNull(key, \"La clave no puede ser nula\");\n"
                "        Objects.requireNonNull(value, \"El valor no puede ser nulo\");\n\n"
                "        lock.lock();\n"
                "        try {\n"
                "            // Si la clave existe, removemos para reinsertar al final (más reciente)\n"
                "            store.remove(key);\n\n"
                "            // Expulsar el elemento menos recientemente usado si se alcanzó el límite\n"
                "            if (store.size() >= maxCapacity) {\n"
                "                Map.Entry<K, V> evicted = store.pollFirstEntry(); // Java 21 SequencedMap API\n"
                "                // Opcional: registrar telemetría del elemento expulsado\n"
                "            }\n\n"
                "            store.putLast(key, value); // Java 21 SequencedMap API: sitúa el elemento al final\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public Optional<V> get(K key) {\n"
                "        Objects.requireNonNull(key, \"La clave no puede ser nula\");\n"
                "        lock.lock();\n"
                "        try {\n"
                "            V value = store.remove(key);\n"
                "            if (value != null) {\n"
                "                store.putLast(key, value); // Refresca posición como más recientemente usado\n"
                "                return Optional.of(value);\n"
                "            }\n"
                "            return Optional.empty();\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public Optional<Map.Entry<K, V>> peekLeastRecent() {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            return Optional.ofNullable(store.firstEntry()); // Inspecciona la cabeza sin remover\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public Optional<Map.Entry<K, V>> peekMostRecent() {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            return Optional.ofNullable(store.lastEntry()); // Inspecciona la cola sin remover\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Métodos Nativos de Java 21 Utilizados:\n"
                "- `store.pollFirstEntry()`: Elimina y retorna de forma atómica la entrada más antigua sin necesidad de crear un iterador manual.\n"
                "- `store.putLast(k, v)`: Garantiza que la entrada se agregue explícitamente en la última posición del orden secuencial.\n"
                "- `store.firstEntry()` / `store.lastEntry()`: Lectura directa de extremos en $O(1)$."
            ),
            category="sequenced_collections",
            task_type="code_completion",
        )
    )

    # Entry 16: Code Completion - Pipeline con reversed()
    entries.append(
        create_record(
            prompt=(
                "Crea un servicio de auditoría de transacciones en Java 21 que reciba una `SequencedCollection<Transaction>` "
                "y aplique un procesamiento bidireccional. Debe calcular la suma acumulativa cronológica normal "
                "y simultáneamente evaluar una regla de detección de anomalías procesando en reversa con `.reversed()`."
            ),
            response=(
                "Aquí tienes la implementación utilizando `SequencedCollection` y vistas invertidas `.reversed()` en Java 21:\n\n"
                "```java\n"
                "package com.m01.audit;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.time.Instant;\n"
                "import java.util.ArrayList;\n"
                "import java.util.List;\n"
                "import java.util.SequencedCollection;\n\n"
                "public final class TransactionAuditPipeline {\n\n"
                "    public record Transaction(String id, BigDecimal amount, Instant timestamp, String clientIp) {}\n\n"
                "    public record AuditSummary(\n"
                "        BigDecimal totalTurnover,\n"
                "        Transaction mostRecent,\n"
                "        Transaction oldest,\n"
                "        List<String> suspiciousAlerts\n"
                "    ) {}\n\n"
                "    public AuditSummary auditBatch(SequencedCollection<Transaction> transactions) {\n"
                "        if (transactions.isEmpty()) {\n"
                "            throw new IllegalArgumentException(\"El lote de transacciones no puede estar vacío\");\n"
                "        }\n\n"
                "        // Java 21 getFirst() y getLast() garantizados por SequencedCollection\n"
                "        Transaction oldest = transactions.getFirst();\n"
                "        Transaction newest = transactions.getLast();\n\n"
                "        BigDecimal total = BigDecimal.ZERO;\n"
                "        for (Transaction tx : transactions) {\n"
                "            total = total.add(tx.amount());\n"
                "        }\n\n"
                "        // Análisis en orden inverso (del más reciente al más antiguo) usando la vista O(1) reversed()\n"
                "        List<String> alerts = new ArrayList<>();\n"
                "        SequencedCollection<Transaction> reverseView = transactions.reversed();\n"
                "        \n"
                "        int rapidBursts = 0;\n"
                "        Instant lastSeenTime = null;\n"
                "        for (Transaction tx : reverseView) {\n"
                "            if (lastSeenTime != null) {\n"
                "                long diffSeconds = Math.abs(lastSeenTime.getEpochSecond() - tx.timestamp().getEpochSecond());\n"
                "                if (diffSeconds < 2) {\n"
                "                    rapidBursts++;\n"
                "                    if (rapidBursts >= 3) {\n"
                "                        alerts.add(\"Alerta de ráfaga: Múltiples transacciones en < 2 segundos detectadas cerca de ID: \" + tx.id());\n"
                "                    }\n"
                "                } else {\n"
                "                    rapidBursts = 0;\n"
                "                }\n"
                "            }\n"
                "            lastSeenTime = tx.timestamp();\n"
                "        }\n\n"
                "        return new AuditSummary(total, newest, oldest, alerts);\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave de Java 21:\n"
                "- `transactions.getFirst()` y `transactions.getLast()` sustituyen a las viejas convenciones verbosas `get(0)` o `get(size - 1)`.\n"
                "- `transactions.reversed()` no invierte la lista in situ ni clona el array; proporciona una vista bidireccional instantánea."
            ),
            category="sequenced_collections",
            task_type="code_completion",
        )
    )

    return entries


def get_unnamed_patterns_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 17: Q&A - Unnamed Patterns and Variables JEP 443 / 456
    entries.append(
        create_record(
            prompt=(
                "Explica el concepto y propósito de las 'Variables y Patrones No Nombrados' (Unnamed Patterns and Variables, `_`) "
                "en Java 21+. ¿En qué contextos léxicos están permitidos y cómo contribuyen a la legibilidad y mantenimiento del código?"
            ),
            response=(
                "### Unnamed Patterns and Variables (`_`) en Java 21+\n\n"
                "El uso del guion bajo (`_`) como identificador especial (JEP 443 en Java 21 preview, JEP 456 final en Java 22) "
                "formaliza la intención explícita del programador de **descartar un valor o variable innecesaria**.\n\n"
                "En versiones previas, los desarrolladores usaban nombres como `ignored`, `unused` o `e`, los cuales contaminaban "
                "el espacio de nombres local y generaban advertencias del linter.\n\n"
                "#### Contextos Permitidos para `_`:\n\n"
                "1. **Captura de Excepciones:**\n"
                "```java\n"
                "try {\n"
                "    return Integer.parseInt(str);\n"
                "} catch (NumberFormatException _) { // Excepción ignorada intencionalmente\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "2. **Parámetros de Lambdas y Métodos:**\n"
                "```java\n"
                "map.computeIfAbsent(key, _ -> fetchFromRemoteSource(key));\n"
                "biFunction.apply(activeUser, _);\n"
                "```\n\n"
                "3. **Recursos en try-with-resources:**\n"
                "```java\n"
                "try (var _ = acquireResourceLock()) {\n"
                "    executeCriticalSection();\n"
                "}\n"
                "```\n\n"
                "4. **Patrones de Records (Record Patterns):**\n"
                "```java\n"
                "if (obj instanceof Order(String id, _, BigDecimal total)) {\n"
                "    // Solo interesan el ID y el total, se ignora el cliente o fecha\n"
                "}\n"
                "```\n\n"
                "5. **Bucles For Tradicionales o Mejorados:**\n"
                "```java\n"
                "for (Order _ : pendingOrders) {\n"
                "    totalPendingCount++;\n"
                "}\n"
                "```\n\n"
                "#### Regla de Oro del Compilador:\n"
                "Una variable declarada como `_` **no puede ser leída jamás**. `System.out.println(_)` provocará un error de compilación. "
                "Además, se pueden declarar múltiples `_` en el mismo ámbito sin colisión de nombres."
            ),
            category="unnamed_patterns",
            task_type="architecture_qa",
        )
    )

    # Entry 18: Code Completion - Refactorización Idiomática con '_'
    entries.append(
        create_record(
            prompt=(
                "Refactoriza la siguiente clase utilitaria en Java 21 eliminando todas las variables no utilizadas "
                "mediante el uso idiomático de variables no nombradas `_` en bloques `catch`, lambdas `Map.computeIfAbsent` "
                "y deconstrucción de records:\n\n"
                "```java\n"
                "public class LegacyParser {\n"
                "    public record UserProfile(String id, String email, String passwordHash, int age) {}\n"
                "    public static int parseOrDefault(String s, int def) {\n"
                "        try {\n"
                "            return Integer.parseInt(s);\n"
                "        } catch (NumberFormatException ignored) {\n"
                "            return def;\n"
                "        }\n"
                "    }\n"
                "    public static void printSummary(Object o) {\n"
                "        if (o instanceof UserProfile) {\n"
                "            UserProfile u = (UserProfile) o;\n"
                "            System.out.println(u.id() + \" -> \" + u.email());\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```"
            ),
            response=(
                "Aquí tienes la refactorización idiomática en Java 21 aplicando patrones y variables no nombradas (`_`):\n\n"
                "```java\n"
                "package com.m01.parser;\n\n"
                "import java.util.Map;\n"
                "import java.util.Objects;\n"
                "import java.util.concurrent.ConcurrentHashMap;\n\n"
                "public final class ModernParser {\n\n"
                "    public record UserProfile(String id, String email, String passwordHash, int age) {\n"
                "        public UserProfile {\n"
                "            Objects.requireNonNull(id);\n"
                "            Objects.requireNonNull(email);\n"
                "        }\n"
                "    }\n\n"
                "    private final Map<String, Integer> cache = new ConcurrentHashMap<>();\n\n"
                "    public static int parseOrDefault(String rawNumber, int defaultValue) {\n"
                "        if (rawNumber == null || rawNumber.isBlank()) {\n"
                "            return defaultValue;\n"
                "        }\n"
                "        try {\n"
                "            return Integer.parseInt(rawNumber.strip());\n"
                "        } catch (NumberFormatException _) { // Variable de excepción no nombrada idiomática\n"
                "            return defaultValue;\n"
                "        }\n"
                "    }\n\n"
                "    public int getOrCalculateScore(String userId) {\n"
                "        // Lambda con parámetro no nombrado: la clave 'userId' ya está en el ámbito léxico\n"
                "        return cache.computeIfAbsent(userId, _ -> computeRemoteScore(userId));\n"
                "    }\n\n"
                "    public static String extractPublicBadge(Object obj) {\n"
                "        // Deconstrucción con componentes no nombrados: passwordHash y age se descartan\n"
                "        if (obj instanceof UserProfile(String id, String email, _, _)) {\n"
                "            return \"Usuario verificado: [\" + id + \"] con email: \" + email;\n"
                "        }\n"
                "        return \"Tipo de identidad no compatible\";\n"
                "    }\n\n"
                "    private static int computeRemoteScore(String userId) {\n"
                "        return userId.hashCode() & 0x7FFFFFFF % 100;\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Mejoras Clave:\n"
                "1. `catch (NumberFormatException _)`: Expresa directamente que no se requiere inspeccionar el objeto excepción.\n"
                "2. `computeIfAbsent(userId, _ -> ...)`: Elimina el parámetro redundante de la función constructora.\n"
                "3. `UserProfile(String id, String email, _, _)`: Documenta sin ambigüedad que `passwordHash` y `age` no deben vincularse a variables locales, mejorando la seguridad y reduciendo el footprint del stack."
            ),
            category="unnamed_patterns",
            task_type="code_completion",
        )
    )

    return entries


def get_sealed_hierarchies_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 19: Q&A - Sealed Classes y Tipos Algebraicos (ADTs)
    entries.append(
        create_record(
            prompt=(
                "¿Cómo se modelan los Tipos Algebraicos de Datos (Algebraic Data Types - ADTs) en Java 21 "
                "utilizando clases e interfaces `sealed` combinadas con `record`? "
                "Explica la distinción entre tipos suma (Sum Types) y tipos producto (Product Types), "
                "y cómo esta combinación supera al patrón Visitor clásico."
            ),
            response=(
                "### Modelado de Tipos Algebraicos (ADTs) en Java 21\n\n"
                "En el álgebra de tipos orientada a lenguajes funcionales y modernos:\n"
                "- **Product Types (Tipos Producto):** Representan una tupla o conjunto de datos donde el espacio de valores es el producto cartesiano de sus campos. En Java 21 se modelan mediante **`record`**.\n"
                "- **Sum Types (Tipos Suma / Co-productos):** Representan una elección cerrada y discriminada entre varias alternativas posibles (A o B o C). En Java 21 se modelan mediante **`sealed interface`** o **`sealed class`** con cláusula `permits`.\n\n"
                "#### Superación del Patrón Visitor Clásico\n"
                "Históricamente, en lenguajes orientados a objetos como Java 8, para aplicar operaciones sobre una jerarquía de clases polimórfica sin modificar las clases base "
                "se empleaba el **Patrón Visitor** (`accept(Visitor v)`, `visit(Circle c)`). Sin embargo, el patrón Visitor presenta graves inconvenientes:\n"
                "1. Extrema verbosidad y dificultad para devolver valores tipados sin envoltorios complejos.\n"
                "2. Dificultad para manejar excepciones verificadas.\n"
                "3. Ruptura de encapsulamiento y alta rigidez.\n\n"
                "Con `sealed` y `switch` exhaustivo en Java 21:\n"
                "- Nuevas operaciones se añaden simplemente como funciones puras con un `switch` que deconstruye los registros.\n"
                "- Si se añade una nueva variante a la jerarquía `sealed`, el compilador localiza todos los switches afectados automáticamente.\n"
                "- El código es plano, comprensible y optimizable por el compilador JIT (C2)."
            ),
            category="sealed_classes",
            task_type="architecture_qa",
        )
    )

    # Entry 20: Code Completion - Tipo Funcional Result<T, E>
    entries.append(
        create_record(
            prompt=(
                "Implementa un tipo funcional seguro `Result<T, E>` en Java 21 usando una interfaz `sealed` "
                "con las variantes `Ok<T>` y `Err<E>`. Añade métodos funcionales `map`, `flatMap` "
                "y un método `fold` basado en pattern matching exhaustivo para eliminar la necesidad de lanzar excepciones."
            ),
            response=(
                "Aquí tienes la implementación completa y canónica del tipo funcional `Result<T, E>` en Java 21:\n\n"
                "```java\n"
                "package com.m01.functional;\n\n"
                "import java.util.Objects;\n"
                "import java.util.function.Consumer;\n"
                "import java.util.function.Function;\n\n"
                "public sealed interface Result<T, E> permits Result.Ok, Result.Err {\n\n"
                "    record Ok<T, E>(T value) implements Result<T, E> {\n"
                "        public Ok {\n"
                "            Objects.requireNonNull(value, \"El valor de Ok no puede ser nulo\");\n"
                "        }\n"
                "    }\n\n"
                "    record Err<T, E>(E error) implements Result<T, E> {\n"
                "        public Err {\n"
                "            Objects.requireNonNull(error, \"El error de Err no puede ser nulo\");\n"
                "        }\n"
                "    }\n\n"
                "    static <T, E> Result<T, E> ok(T value) {\n"
                "        return new Ok<>(value);\n"
                "    }\n\n"
                "    static <T, E> Result<T, E> err(E error) {\n"
                "        return new Err<>(error);\n"
                "    }\n\n"
                "    default boolean isSuccess() {\n"
                "        return this instanceof Ok<T, E>;\n"
                "    }\n\n"
                "    default <R> Result<R, E> map(Function<? super T, ? extends R> mapper) {\n"
                "        Objects.requireNonNull(mapper);\n"
                "        return switch (this) {\n"
                "            case Ok<T, E>(T value) -> new Ok<>(mapper.apply(value));\n"
                "            case Err<T, E>(E error) -> new Err<>(error);\n"
                "        };\n"
                "    }\n\n"
                "    default <R> Result<R, E> flatMap(Function<? super T, Result<R, E>> mapper) {\n"
                "        Objects.requireNonNull(mapper);\n"
                "        return switch (this) {\n"
                "            case Ok<T, E>(T value) -> mapper.apply(value);\n"
                "            case Err<T, E>(E error) -> new Err<>(error);\n"
                "        };\n"
                "    }\n\n"
                "    default <R> R fold(Function<? super T, ? extends R> onSuccess, Function<? super E, ? extends R> onFailure) {\n"
                "        Objects.requireNonNull(onSuccess);\n"
                "        Objects.requireNonNull(onFailure);\n"
                "        return switch (this) {\n"
                "            case Ok<T, E>(T val) -> onSuccess.apply(val);\n"
                "            case Err<T, E>(E err) -> onFailure.apply(err);\n"
                "        };\n"
                "    }\n\n"
                "    default void ifSuccess(Consumer<? super T> action) {\n"
                "        if (this instanceof Ok<T, E>(T val)) {\n"
                "            action.accept(val);\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Ejemplo de Uso Práctico:\n"
                "```java\n"
                "Result<Double, String> divide(double a, double b) {\n"
                "    return (b == 0.0) ? Result.err(\"División por cero\") : Result.ok(a / b);\n"
                "}\n\n"
                "String output = divide(10.0, 2.0)\n"
                "    .map(res -> res * 100)\n"
                "    .fold(\n"
                "        success -> \"Resultado calculado: \" + success,\n"
                "        failure -> \"Fallo en cálculo: \" + failure\n"
                "    );\n"
                "```\n\n"
                "Esta abstracción elimina los costes ocultos de inicialización y desenrollado de trazas de pila (stack unwinding) que implican las excepciones tradicionales en Java."
            ),
            category="sealed_classes",
            task_type="code_completion",
        )
    )

    # Entry 21: Code Completion - Árbol de Expresiones Aritméticas (AST)
    entries.append(
        create_record(
            prompt=(
                "Implementa un evaluador de expresiones matemáticas (AST) en Java 21 modelado con una interfaz sellada `Expr`. "
                "Soporta constantes numéricas, suma, multiplicación y negación. Implementa un método `evaluate` "
                "y un método `toInfixNotation` que formatee la expresión matemáticamente utilizando un switch exhaustivo."
            ),
            response=(
                "Aquí tienes la implementación del AST con tipos algebraicos en Java 21:\n\n"
                "```java\n"
                "package com.m01.ast;\n\n"
                "public final class ExpressionEngine {\n\n"
                "    public sealed interface Expr permits Constant, Add, Multiply, Negate {}\n\n"
                "    public record Constant(double value) implements Expr {}\n"
                "    public record Add(Expr left, Expr right) implements Expr {}\n"
                "    public record Multiply(Expr left, Expr right) implements Expr {}\n"
                "    public record Negate(Expr operand) implements Expr {}\n\n"
                "    public static double evaluate(Expr expr) {\n"
                "        return switch (expr) {\n"
                "            case Constant(double v) -> v;\n"
                "            case Add(Expr l, Expr r) -> evaluate(l) + evaluate(r);\n"
                "            case Multiply(Expr l, Expr r) -> evaluate(l) * evaluate(r);\n"
                "            case Negate(Expr op) -> -evaluate(op);\n"
                "        };\n"
                "    }\n\n"
                "    public static String toInfixNotation(Expr expr) {\n"
                "        return switch (expr) {\n"
                "            case Constant(double v) -> (v == (long) v) ? String.format(\"%d\", (long) v) : String.valueOf(v);\n"
                "            case Add(Expr l, Expr r) -> \"(\" + toInfixNotation(l) + \" + \" + toInfixNotation(r) + \")\";\n"
                "            case Multiply(Expr l, Expr r) -> toInfixNotation(l) + \" * \" + toInfixNotation(r);\n"
                "            case Negate(Expr op) -> \"-\" + toInfixNotation(op);\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Simplicidad de Mantenimiento:\n"
                "Tanto `evaluate` como `toInfixNotation` son métodos de apenas 5 líneas cada uno gracias a la deconstrucción directa de records en el switch sin casteos ni `instanceof` verbosos."
            ),
            category="sealed_classes",
            task_type="code_completion",
        )
    )

    return entries


def get_modern_apis_entries() -> List[Dict[str, Any]]:
    entries = []

    # Entry 22: Q&A - Text Blocks y Formateo Limpio
    entries.append(
        create_record(
            prompt=(
                "Describe la semántica de los Text Blocks (`\"\"\"`) en Java moderno. "
                "Explica el algoritmo de eliminación de sangría incidental (stripIndent), el uso de caracteres de escape "
                "como `\\` (continuación de línea) y `\\s` (preservación de espacio en blanco final), "
                "y cómo combinarlos de forma segura con `.formatted(...)`."
            ),
            response=(
                "### Semántica de Text Blocks (`\"\"\"`) en Java Moderno\n\n"
                "Los **Text Blocks** introducen literales de cadena multilínea que eliminan la necesidad de concatenaciones con `+` y caracteres de escape `\\n` continuos.\n\n"
                "#### 1. Algoritmo de Sangría Incidental (`stripIndent`)\n"
                "La JVM inspecciona todas las líneas no vacías del bloque de texto y calcula el **prefijo común de espacios en blanco** (sangría incidental). "
                "Posteriormente, elimina esa cantidad de espacios al inicio de cada línea, preservando únicamente la sangría esencial relativa.\n"
                "La posición de las tres comillas de cierre (`\"\"\"`) determina dónde termina la sangría incidental:\n"
                "```java\n"
                "String html = \"\"\"\n"
                "              <html>\n"
                "                  <body>OK</body>\n"
                "              </html>\n"
                "              \"\"\"; // Al alinearse con <html>, <html> no tiene sangría.\n"
                "```\n\n"
                "#### 2. Escapes Especiales Modernos\n"
                "- **`\\` (Línea continua):** Suprime el salto de línea en el código fuente, permitiendo redactar sentencias SQL o cadenas muy largas sin partir la cadena en tiempo de ejecución.\n"
                "- **`\\s` (Espacio explícito):** Evita que el compilador descarte los espacios en blanco que se encuentren al final de una línea.\n\n"
                "#### 3. Interpolación con `.formatted(...)`\n"
                "El método `String.formatted(Object... args)` es un método de instancia que reemplaza a `String.format(template, args)` de manera fluida y legible para consultas SQL, payloads JSON o plantillas de correo."
            ),
            category="modern_apis",
            task_type="architecture_qa",
        )
    )

    # Entry 23: Code Completion - HttpClient Asíncrono con HTTP/2 y Text Blocks
    entries.append(
        create_record(
            prompt=(
                "Implementa un cliente API REST asíncrono en Java 21 utilizando `java.net.http.HttpClient` configurado para HTTP/2. "
                "Debe enviar un payload JSON construido con Text Blocks (`\"\"\"`) a un endpoint `/v1/orders`, "
                "manejar la respuesta asíncronamente con `CompletableFuture`, y verificar códigos de estado HTTP."
            ),
            response=(
                "Aquí tienes la implementación completa del cliente HTTP/2 asíncrono en Java 21:\n\n"
                "```java\n"
                "package com.m01.http;\n\n"
                "import java.net.URI;\n"
                "import java.net.http.HttpClient;\n"
                "import java.net.http.HttpRequest;\n"
                "import java.net.http.HttpResponse;\n"
                "import java.time.Duration;\n"
                "import java.util.concurrent.CompletableFuture;\n\n"
                "public final class ModernOrderApiClient {\n\n"
                "    private final HttpClient httpClient;\n"
                "    private final String baseUrl;\n\n"
                "    public ModernOrderApiClient(String baseUrl) {\n"
                "        this.baseUrl = baseUrl;\n"
                "        this.httpClient = HttpClient.newBuilder()\n"
                "            .version(HttpClient.Version.HTTP_2)\n"
                "            .connectTimeout(Duration.ofSeconds(5))\n"
                "            .followRedirects(HttpClient.Redirect.NORMAL)\n"
                "            .build();\n"
                "    }\n\n"
                "    public record OrderCreationResponse(int statusCode, String responseBody, boolean success) {}\n\n"
                "    public CompletableFuture<OrderCreationResponse> submitOrderAsync(\n"
                "        String customerId,\n"
                "        String sku,\n"
                "        int quantity,\n"
                "        double unitPrice\n"
                "    ) {\n"
                "        // Construcción limpia de payload JSON mediante Text Block y formatted\n"
                "        String jsonPayload = \"\"\"\n"
                "        {\n"
                "            \"customerId\": \"%s\",\n"
                "            \"item\": {\n"
                "                \"sku\": \"%s\",\n"
                "                \"quantity\": %d,\n"
                "                \"unitPrice\": %.2f\n"
                "            },\n"
                "            \"channel\": \"API_V21\"\n"
                "        }\n"
                "        \"\"\".formatted(customerId, sku, quantity, unitPrice);\n\n"
                "        HttpRequest request = HttpRequest.newBuilder()\n"
                "            .uri(URI.create(baseUrl + \"/v1/orders\"))\n"
                "            .timeout(Duration.ofSeconds(10))\n"
                "            .header(\"Content-Type\", \"application/json\")\n"
                "            .header(\"Accept\", \"application/json\")\n"
                "            .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))\n"
                "            .build();\n\n"
                "        return httpClient\n"
                "            .sendAsync(request, HttpResponse.BodyHandlers.ofString())\n"
                "            .thenApply(response -> {\n"
                "                boolean isSuccess = response.statusCode() >= 200 && response.statusCode() < 300;\n"
                "                return new OrderCreationResponse(response.statusCode(), response.body(), isSuccess);\n"
                "            });\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "- `HttpClient` nativo de Java elimina dependencias externas pesadas como Apache HttpClient para operaciones asíncronas.\n"
                "- `sendAsync` es totalmente compatible con el modelo reactivo de `CompletableFuture` y coopera eficientemente con Virtual Threads."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 24: Code Completion - Streams Avanzados con Collectors.teeing()
    entries.append(
        create_record(
            prompt=(
                "Implementa un cálculo analítico en Java 21 sobre una lista de transacciones financieras "
                "que requiera computar simultáneamente el promedio y la suma total de montos en una única pasada del Stream. "
                "Utiliza `Collectors.teeing()` para evitar recorrer la colección dos veces."
            ),
            response=(
                "Aquí tienes la implementación en un único recorrido con `Collectors.teeing()` en Java 21:\n\n"
                "```java\n"
                "package com.m01.analytics;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.math.RoundingMode;\n"
                "import java.util.List;\n"
                "import java.util.Objects;\n"
                "import java.util.stream.Collectors;\n\n"
                "public final class StreamAnalyticsService {\n\n"
                "    public record SaleItem(String id, BigDecimal price, int quantity) {\n"
                "        public BigDecimal totalRevenue() {\n"
                "            return price.multiply(BigDecimal.valueOf(quantity));\n"
                "        }\n"
                "    }\n\n"
                "    public record FinancialStats(\n"
                "        BigDecimal totalTurnover,\n"
                "        double averageTicketValue,\n"
                "        long count\n"
                "    ) {}\n\n"
                "    public FinancialStats analyzeSales(List<SaleItem> items) {\n"
                "        Objects.requireNonNull(items, \"La lista de ventas no puede ser nula\");\n"
                "        if (items.isEmpty()) {\n"
                "            return new FinancialStats(BigDecimal.ZERO, 0.0, 0);\n"
                "        }\n\n"
                "        // Collectors.teeing fusiona dos recolectores concurrentes sobre el mismo flujo de datos\n"
                "        return items.stream().collect(\n"
                "            Collectors.teeing(\n"
                "                // Primer recolector: Suma total de facturación\n"
                "                Collectors.reducing(BigDecimal.ZERO, SaleItem::totalRevenue, BigDecimal::add),\n"
                "                // Segundo recolector: Promedio de ticket monetario\n"
                "                Collectors.averagingDouble(item -> item.totalRevenue().doubleValue()),\n"
                "                // Función fusionadora de ambos resultados en el record destino\n"
                "                (sum, avg) -> new FinancialStats(sum.setScale(2, RoundingMode.HALF_UP), avg, items.size())\n"
                "            )\n"
                "        );\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Eficiencia:\n"
                "`Collectors.teeing()` bifurca cada elemento hacia ambos colectores en el mismo ciclo, garantizando complejidad temporal $O(N)$ y mínima presión en la caché L1/L2 de la CPU."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 25: Q&A - Foreign Function & Memory API (FFM - JEP 454)
    entries.append(
        create_record(
            prompt=(
                "Explica la arquitectura y beneficios de la Foreign Function & Memory API (FFM API, JEP 454) en Java 21+. "
                "¿Cómo reemplaza a `sun.misc.Unsafe` y JNI para la gestión de memoria fuera del Heap (`off-heap`) y llamadas a bibliotecas nativas C?"
            ),
            response=(
                "### Foreign Function & Memory API (FFM) en Java 21+\n\n"
                "Durante décadas, la interoperabilidad con código nativo y la asignación de memoria fuera del heap (off-heap) "
                "dependían de dos herramientas frágiles y riesgosas:\n"
                "1. **JNI (Java Native Interface):** Extremadamente lenta, exigía escribir código C 'pegamento' (`glue code`), "
                "provocaba penalizaciones al cruzar la frontera JVM/nativo y cualquier error provocaba un crash irrecuperable de la JVM (`SIGSEGV`).\n"
                "2. **`sun.misc.Unsafe`:** Permitía manipular memoria de bajo nivel sin barreras de seguridad, pero sin gestión de ciclo de vida determinista.\n\n"
                "#### Conceptos Fundamentales de FFM (JEP 454)\n"
                "1. **`MemorySegment`:** Abstracción segura que modela una región contigua de memoria (ya sea en el heap o fuera del heap). "
                "Cada acceso cuenta con límites espaciales estrictos (`bounds checking`) para evitar desbordamientos de búfer.\n"
                "2. **`Arena`:** Controla el ciclo de vida temporal y la liberación determinista de los segmentos de memoria:\n"
                "   - `Arena.ofConfined()`: Memoria ligada a un solo hilo de ejecución. Al invocar `arena.close()`, se libera toda la memoria inmediatamente de forma determinista.\n"
                "   - `Arena.ofShared()`: Memoria compartida de forma concurrente y segura entre múltiples hilos.\n"
                "   - `Arena.ofAuto()`: El ciclo de vida de la memoria es gestionado por el Garbage Collector cuando el segmento se vuelve inalcanzable.\n"
                "3. **`Linker` y `SymbolLookup`:** Permite vincular funciones nativas de bibliotecas del sistema (ej. `strlen` de C o librerías de BLAS/CUDA) "
                "directamente desde código Java en tiempo de ejecución sin compilar código intermedio C."
            ),
            category="modern_apis",
            task_type="architecture_qa",
        )
    )

    # Entry 26: Code Completion - MemorySegment y Arena en FFM API
    entries.append(
        create_record(
            prompt=(
                "Escribe un componente en Java 21 que reserve un bloque de memoria off-heap nativa utilizando "
                "`Arena.ofConfined()` y `MemorySegment`. Debe escribir una matriz de enteros, calcular su suma "
                "con `ValueLayout.JAVA_INT`, y garantizar la liberación determinista de memoria mediante `try-with-resources`."
            ),
            response=(
                "Aquí tienes la implementación idiomática usando la API FFM de Java 21:\n\n"
                "```java\n"
                "package com.m01.nativemem;\n\n"
                "import java.lang.foreign.Arena;\n"
                "import java.lang.foreign.MemorySegment;\n"
                "import java.lang.foreign.ValueLayout;\n\n"
                "public final class NativeOffHeapBuffer {\n\n"
                "    public static long calculateOffHeapSum(int[] values) {\n"
                "        // Arena implementa AutoCloseable; al salir del bloque try se desasigna toda la memoria nativa\n"
                "        try (Arena arena = Arena.ofConfined()) {\n"
                "            long byteSize = (long) values.length * ValueLayout.JAVA_INT.byteSize();\n"
                "            MemorySegment segment = arena.allocate(byteSize, ValueLayout.JAVA_INT.byteAlignment());\n\n"
                "            // Escritura en memoria nativa con verificación de límites\n"
                "            for (int i = 0; i < values.length; i++) {\n"
                "                long offset = (long) i * ValueLayout.JAVA_INT.byteSize();\n"
                "                segment.set(ValueLayout.JAVA_INT, offset, values[i]);\n"
                "            }\n\n"
                "            // Lectura y cómputo acumulativo\n"
                "            long sum = 0;\n"
                "            for (int i = 0; i < values.length; i++) {\n"
                "                long offset = (long) i * ValueLayout.JAVA_INT.byteSize();\n"
                "                sum += segment.get(ValueLayout.JAVA_INT, offset);\n"
                "            }\n\n"
                "            return sum;\n"
                "        } // Memoria nativa liberada aquí de inmediato sin esperar al Garbage Collector\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Seguridad Garantizada:\n"
                "- Si se intenta acceder a un offset superior a `byteSize`, la JVM lanza `IndexOutOfBoundsException` en lugar de provocar un `segmentation fault` de Linux.\n"
                "- Si se intenta leer el segmento fuera del bloque `try`, la JVM detecta que la `Arena` está cerrada y arroja `IllegalStateException`."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    return entries


def get_additional_deep_entries() -> List[Dict[str, Any]]:
    """Genera entradas complementarias para consolidar un corpus denso y de cobertura exhaustiva."""
    entries = []

    # Entry 27: Structured Concurrency ShutdownOnFailure en Microservicios
    entries.append(
        create_record(
            prompt=(
                "Implementa un orquestador de reservas de viajes en Java 21 que consulte simultáneamente "
                "un servicio de vuelos y un servicio de hoteles utilizando `StructuredTaskScope.ShutdownOnFailure`. "
                "Si la reserva de vuelos falla, la reserva del hotel debe cancelarse inmediatamente "
                "para evitar inconsistencias distributivas."
            ),
            response=(
                "Aquí tienes la implementación completa utilizando Structured Concurrency en Java 21:\n\n"
                "```java\n"
                "package com.m01.travel.orchestrator;\n\n"
                "import java.util.concurrent.StructuredTaskScope;\n"
                "import java.util.concurrent.StructuredTaskScope.Subtask;\n"
                "import java.util.function.Supplier;\n\n"
                "public final class TravelBookingOrchestrator {\n\n"
                "    public record FlightBooking(String flightId, String confirmationCode) {}\n"
                "    public record HotelBooking(String hotelId, String roomReservationId) {}\n"
                "    public record TravelPackage(FlightBooking flight, HotelBooking hotel) {}\n\n"
                "    public interface FlightService {\n"
                "        FlightBooking bookFlight(String customerId, String origin, String destination);\n"
                "    }\n\n"
                "    public interface HotelService {\n"
                "        HotelBooking bookHotel(String customerId, String city);\n"
                "    }\n\n"
                "    private final FlightService flightService;\n"
                "    private final HotelService hotelService;\n\n"
                "    public TravelBookingOrchestrator(FlightService flightService, HotelService hotelService) {\n"
                "        this.flightService = flightService;\n"
                "        this.hotelService = hotelService;\n"
                "    }\n\n"
                "    public TravelPackage bookCompleteTrip(String customerId, String origin, String city) throws Exception {\n"
                "        // Concurrencia estructurada: el ciclo de vida de ambas tareas concurrentes queda restringido a este bloque\n"
                "        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {\n"
                "            Subtask<FlightBooking> flightSubtask = scope.fork(() -> flightService.bookFlight(customerId, origin, city));\n"
                "            Subtask<HotelBooking> hotelSubtask = scope.fork(() -> hotelService.bookHotel(customerId, city));\n\n"
                "            scope.join(); // Espera a que ambas tareas concluyan o a que la primera falle\n"
                "            scope.throwIfFailed(ex -> new RuntimeException(\"Fallo en la reserva del viaje, revirtiendo operaciones: \" + ex.getMessage(), ex));\n\n"
                "            // Ambos subtasks completaron con éxito\n"
                "            return new TravelPackage(flightSubtask.get(), hotelSubtask.get());\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Beneficios de `ShutdownOnFailure`:\n"
                "1. Si `flightService.bookFlight` arroja una excepción, `scope` envía una interrupción instantánea al hilo que ejecutaba `hotelService.bookHotel`.\n"
                "2. Cero hilos huérfanos ejecutando llamadas remotas en background cuando ya se sabe que el paquete no podrá completarse."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 28: Pattern Matching con Genéricos y Tipos Complejos
    entries.append(
        create_record(
            prompt=(
                "¿Cómo gestiona el compilador de Java 21 el Pattern Matching sobre tipos genéricos y la inferencia "
                "de argumentos de tipo en registros genéricos? Proporciona un ejemplo con un contenedor `record Box<T>(T value)`."
            ),
            response=(
                "### Pattern Matching sobre Tipos Genéricos en Java 21\n\n"
                "En Java clásico, la eliminación de tipos (Type Erasure) impedía realizar comprobaciones exactas sobre parámetros de tipo genéricos "
                "(`instanceof List<String>` no era permitido). En Java 21, el compilador realiza deducción estática de tipos en Record Patterns genéricos:\n\n"
                "```java\n"
                "package com.m01.generics;\n\n"
                "public final class GenericPatternMatcher {\n\n"
                "    public record Box<T>(T content) {}\n\n"
                "    public static String inspectBox(Box<?> box) {\n"
                "        return switch (box) {\n"
                "            case Box(String s) -> \"Caja con texto: '\" + s.toUpperCase() + \"' (Longitud: \" + s.length() + \")\";\n"
                "            case Box(Integer i) -> \"Caja con entero: \" + (i * 2);\n"
                "            case Box(Double d) -> \"Caja con decimal: \" + String.format(\"%.2f\", d);\n"
                "            case Box(null) -> \"Caja conteniendo un valor nulo\";\n"
                "            case Box<?> b -> \"Caja con objeto genérico no clasificado: \" + b.content();\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "#### Aspectos Clave:\n"
                "1. `case Box(String s)`: El compilador verifica dinámicamente que `content` no solo sea no nulo sino una instancia de `String`, vinculando `s` directamente con tipo estricto `String` sin requerir casts `(String) box.content()`.\n"
                "2. `case Box(null)`: Distingue cuando la caja existe pero su contenido interno es nulo."
            ),
            category="record_patterns",
            task_type="architecture_qa",
        )
    )

    # Entry 29: Code Completion - SequencedMap para Auditoría de Sesiones Expirables
    entries.append(
        create_record(
            prompt=(
                "Implementa un gestor de sesiones de usuario en Java 21 que almacene las sesiones ordenadas cronológicamente "
                "usando `SequencedMap`. El gestor debe permitir invalidar sesiones inactivas a partir del elemento más antiguo "
                "mediante `pollFirstEntry()` y refrescar la posición de sesiones activas usando `putLast()`."
            ),
            response=(
                "Aquí tienes la implementación del administrador de sesiones en Java 21:\n\n"
                "```java\n"
                "package com.m01.security.session;\n\n"
                "import java.time.Duration;\n"
                "import java.time.Instant;\n"
                "import java.util.*;\n"
                "import java.util.concurrent.locks.ReentrantLock;\n\n"
                "public final class SequencedSessionManager {\n\n"
                "    public record UserSession(String sessionId, String userId, Instant lastAccessTime, Map<String, String> attributes) {}\n\n"
                "    private final SequencedMap<String, UserSession> activeSessions = new LinkedHashMap<>();\n"
                "    private final ReentrantLock lock = new ReentrantLock();\n"
                "    private final Duration maxIdleTime;\n\n"
                "    public SequencedSessionManager(Duration maxIdleTime) {\n"
                "        this.maxIdleTime = maxIdleTime;\n"
                "    }\n\n"
                "    public void recordAccess(String sessionId, String userId) {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            UserSession existing = activeSessions.remove(sessionId);\n"
                "            Map<String, String> attrs = (existing != null) ? existing.attributes() : new HashMap<>();\n"
                "            UserSession updated = new UserSession(sessionId, userId, Instant.now(), attrs);\n"
                "            activeSessions.putLast(sessionId, updated); // Se desplaza al final como la más reciente\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public int purgeExpiredSessions() {\n"
                "        Instant threshold = Instant.now().minus(maxIdleTime);\n"
                "        int purged = 0;\n"
                "        lock.lock();\n"
                "        try {\n"
                "            // Mientras el elemento más antiguo de la cola haya expirado, lo extraemos en O(1)\n"
                "            while (!activeSessions.isEmpty()) {\n"
                "                Map.Entry<String, UserSession> oldest = activeSessions.firstEntry();\n"
                "                if (oldest.getValue().lastAccessTime().isBefore(threshold)) {\n"
                "                    activeSessions.pollFirstEntry(); // Remueve la cabeza secuencial de inmediato\n"
                "                    purged++;\n"
                "                } else {\n"
                "                    break; // Las sesiones posteriores son más recientes y no han expirado\n"
                "                }\n"
                "            }\n"
                "            return purged;\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public Optional<UserSession> getSession(String sessionId) {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            return Optional.ofNullable(activeSessions.get(sessionId));\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Eficiencia Algorítmica:\n"
                "Al estar las sesiones ordenadas temporalmente en el `SequencedMap`, el método `purgeExpiredSessions()` solo necesita inspeccionar los primeros nodos; en cuanto encuentra una sesión válida, finaliza el ciclo en lugar de evaluar todas las entradas $O(N)$."
            ),
            category="sequenced_collections",
            task_type="code_completion",
        )
    )

    # Entry 30: Q&A - Scoped Values vs InheritableThreadLocal en Microservicios
    entries.append(
        create_record(
            prompt=(
                "Compara en profundidad `ScopedValue` (JEP 446) frente a `InheritableThreadLocal` en arquitecturas "
                "de microservicios con Java 21+. ¿Cómo afecta la propagación de contexto de trazabilidad (ej. TraceId, SpanId) "
                "al rendimiento y huella de memoria cuando se crean millones de Virtual Threads?"
            ),
            response=(
                "### ScopedValue vs InheritableThreadLocal en Escala Masiva\n\n"
                "#### 1. El Problema con `InheritableThreadLocal`\n"
                "En microservicios distribuidos, es común propagar identificadores de trazabilidad (`TraceId`, `TenantId`, `SecurityContext`). "
                "Cuando se usaba `InheritableThreadLocal`:\n"
                "- Cada vez que se generaba un nuevo hilo, la JVM realizaba una copia superficial o profunda del mapa de variables hacia el nuevo hilo.\n"
                "- En un servidor que gestiona **1,000,000 de Virtual Threads**, si cada hilo hereda un mapa con 5 variables de contexto, se asignan millones de entradas adicionales en el Heap, provocando recolecciones de basura frecuentes (GC pauses).\n"
                "- Los valores en `ThreadLocal` son mutables por naturaleza, lo que abre la puerta a que una subtarea corrompa el contexto del hilo padre.\n\n"
                "#### 2. La Arquitectura de `ScopedValue`\n"
                "- **Inmutabilidad y Visibilidad Delimitada:** Un `ScopedValue` se vincula a una invocación léxica mediante `ScopedValue.where(TRACE_ID, \"abc\").run(...)`. Una vez vinculado, no puede ser modificado dentro de ese bloque.\n"
                "- **Compartición Directa:** Cuando un Virtual Thread dentro del bloque ejecuta subtareas estructuradas (`StructuredTaskScope`), los hilos hijos comparten una referencia al mismo marco de enlace sin clonar ninguna tabla hash.\n"
                "- **Reclamación Instantánea:** Al retornar del método, la vinculación se descarta de la pila sin intervención prolongada del recolector de basura."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 31: Code Completion - ScopedValue con TraceId Context
    entries.append(
        create_record(
            prompt=(
                "Escribe un middleware de seguridad y trazabilidad en Java 21 utilizando `ScopedValue` "
                "para propagar de forma inmutable un `SecurityContext(String userId, String tenantId, String traceId)` "
                "a través de múltiples capas de servicio sin pasarlo como argumento en cada método."
            ),
            response=(
                "Aquí tienes la implementación idiomática usando `ScopedValue` de Java 21:\n\n"
                "```java\n"
                "package com.m01.security.context;\n\n"
                "import java.util.Objects;\n"
                "import java.util.concurrent.Callable;\n\n"
                "public final class SecurityContextHolder {\n\n"
                "    public record SecurityContext(String userId, String tenantId, String traceId) {\n"
                "        public SecurityContext {\n"
                "            Objects.requireNonNull(userId, \"userId no puede ser nulo\");\n"
                "            Objects.requireNonNull(tenantId, \"tenantId no puede ser nulo\");\n"
                "            Objects.requireNonNull(traceId, \"traceId no puede ser nulo\");\n"
                "        }\n"
                "    }\n\n"
                "    // Declaración estática del ScopedValue\n"
                "    public static final ScopedValue<SecurityContext> CURRENT_CONTEXT = ScopedValue.newInstance();\n\n"
                "    private SecurityContextHolder() {}\n\n"
                "    public static <T> T runInContext(SecurityContext context, Callable<T> task) throws Exception {\n"
                "        // Vinculación inmutable en el ámbito léxico de ejecución\n"
                "        return ScopedValue.where(CURRENT_CONTEXT, context).call(task);\n"
                "    }\n\n"
                "    public static void runInContext(SecurityContext context, Runnable task) {\n"
                "        ScopedValue.where(CURRENT_CONTEXT, context).run(task);\n"
                "    }\n\n"
                "    public static SecurityContext current() {\n"
                "        if (!CURRENT_CONTEXT.isBound()) {\n"
                "            throw new IllegalStateException(\"No existe un SecurityContext activo en el hilo actual\");\n"
                "        }\n"
                "        return CURRENT_CONTEXT.get();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Consumo en la Capa de Negocio:\n"
                "```java\n"
                "public class OrderProcessingService {\n"
                "    public void createOrder(String orderId) {\n"
                "        // Lectura limpia sin contaminar las firmas de los métodos\n"
                "        SecurityContext ctx = SecurityContextHolder.current();\n"
                "        System.out.println(\"Procesando pedido [\" + orderId + \"] para tenant: \" + ctx.tenantId() + \" (Trace: \" + ctx.traceId() + \")\");\n"
                "    }\n"
                "}\n"
                "```"
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 32: Code Completion - Math.clamp y APIs Utilitarias en Java 21
    entries.append(
        create_record(
            prompt=(
                "Implementa un normalizador de señales y métricas en Java 21 utilizando el método estandarizado `Math.clamp()` "
                "y deconstrucción de registros. Modela rangos de tolerancia y procesa telemetría asegurando que los valores "
                "queden restringidos a rangos mínimos y máximos de forma idiomática."
            ),
            response=(
                "Aquí tienes la implementación usando `Math.clamp()` introducido en Java 21:\n\n"
                "```java\n"
                "package com.m01.telemetry;\n\n"
                "public final class TelemetryNormalizer {\n\n"
                "    public record SensorReading(String sensorId, double rawVoltage, double temperatureCelsius) {}\n"
                "    public record NormalizedMetrics(String sensorId, double clampedVoltage, double clampedTemp, boolean wasAdjusted) {}\n\n"
                "    private static final double MIN_VOLTAGE = 0.0;\n"
                "    private static final double MAX_VOLTAGE = 5.0;\n"
                "    private static final double MIN_TEMP = -40.0;\n"
                "    private static final double MAX_TEMP = 125.0;\n\n"
                "    public static NormalizedMetrics normalize(SensorReading reading) {\n"
                "        // Math.clamp en Java 21 sustituye a Math.min(Math.max(val, min), max)\n"
                "        double cleanVoltage = Math.clamp(reading.rawVoltage(), MIN_VOLTAGE, MAX_VOLTAGE);\n"
                "        double cleanTemp = Math.clamp(reading.temperatureCelsius(), MIN_TEMP, MAX_TEMP);\n\n"
                "        boolean adjusted = (cleanVoltage != reading.rawVoltage()) || (cleanTemp != reading.temperatureCelsius());\n\n"
                "        return new NormalizedMetrics(reading.sensorId(), cleanVoltage, cleanTemp, adjusted);\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Claridad Semántica:\n"
                "`Math.clamp(value, min, max)` expresa directamente la intención matemática, optimiza la generación de instrucciones nativas SIMD/x86 y elimina errores comunes de inversión entre `Math.min` y `Math.max`."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    return entries


def get_advanced_enterprise_entries() -> List[Dict[str, Any]]:
    """Entradas avanzadas de nivel de arquitectura empresarial para Java 21+."""
    entries = []

    # Entry 33: Q&A - Database Connection Pooling y Virtual Threads
    entries.append(
        create_record(
            prompt=(
                "En una aplicación basada en Virtual Threads (Project Loom) en Java 21, ¿debería configurarse "
                "el pool de conexiones a la base de datos (ej. HikariCP) para admitir miles de conexiones simultáneas "
                "igualando el número de Virtual Threads? Explica las consecuencias sobre el motor de base de datos "
                "y cuál es el patrón de diseño adecuado para gobernar el acceso concurrente a I/O limitado."
            ),
            response=(
                "### Database Connection Pooling y Virtual Threads en Java 21\n\n"
                "#### 1. El Error Común: Escalar Conexiones al Número de Hilos Virtuales\n"
                "Con los Virtual Threads, es trivial tener **100,000 hilos concurrentes**. Sin embargo, configurar "
                "un pool de conexiones como **HikariCP con 10,000 o 100,000 conexiones hacia PostgreSQL o MySQL es catastrófico**:\n"
                "- **Saturación de Hardware del SGBD:** Los motores de base de datos relacionales utilizan procesos o hilos pesados del SO. "
                "Cada conexión consume memoria de buffer dedicada, memoria de ordenamiento y causa contención de bloqueos (lock contention) a nivel de páginas y transacciones.\n"
                "- **Fórmula de Sizing de HikariCP:** La regla empírica clásica sigue siendo válida: `conexiones = (cores_cpu * 2) + disco_spindles` "
                "(típicamente entre 20 y 50 conexiones para un servidor de base de datos).\n\n"
                "#### 2. El Cuello de Botella: Contención de Adquisición\n"
                "Si 50,000 Virtual Threads compiten simultáneamente por adquirir 30 conexiones de HikariCP:\n"
                "- El pool puede sufrir de tiempos de espera (`ConnectionTimeoutException`).\n"
                "- Si el driver JDBC utiliza sincronización interna obsoleta (`synchronized`), podría provocar **Carrier Thread Pinning** prolongado.\n\n"
                "#### 3. Patrón de Diseño Recomendado: Limitación por Semáforo (`Semaphore`)\n"
                "Para proteger tanto a la base de datos como al pool, se debe emplear un `Semaphore` o una cola de solicitudes "
                "delante de la capa de acceso a datos:\n"
                "1. Los hilos virtuales esperan en el semáforo mediante `semaphore.acquire()`. En Java 21, `Semaphore` desasocia cooperativamente "
                "el hilo virtual de su Carrier Thread sin anclar la CPU nativa.\n"
                "2. Solo los hilos con permiso concedido solicitan una conexión al pool HikariCP, garantizando adquisición inmediata sin timeouts."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 34: Code Completion - ThrottledDatabaseWorker con Semaphore
    entries.append(
        create_record(
            prompt=(
                "Implementa un componente `ThrottledDatabaseWorker` en Java 21 que ejecute consultas masivas en paralelo "
                "usando Virtual Threads y `Executors.newVirtualThreadPerTaskExecutor()`. "
                "Aplica un `Semaphore` para limitar el número máximo de consultas concurrentes a la base de datos "
                "y evitar la saturación del pool de conexiones sin anclar los hilos de transporte (carrier threads)."
            ),
            response=(
                "Aquí tienes la implementación robusta y cooperativa para Java 21:\n\n"
                "```java\n"
                "package com.m01.persistence;\n\n"
                "import java.sql.Connection;\n"
                "import java.sql.PreparedStatement;\n"
                "import java.sql.ResultSet;\n"
                "import java.util.List;\n"
                "import java.util.Objects;\n"
                "import java.util.concurrent.*;\n"
                "import javax.sql.DataSource;\n\n"
                "public final class ThrottledDatabaseWorker {\n\n"
                "    public record UserRecord(long id, String username, String email) {}\n\n"
                "    private final DataSource dataSource;\n"
                "    private final Semaphore queryThrottler;\n\n"
                "    public ThrottledDatabaseWorker(DataSource dataSource, int maxConcurrentDbQueries) {\n"
                "        this.dataSource = Objects.requireNonNull(dataSource);\n"
                "        // El Semaphore en Java 21 no provoca Carrier Pinning durante el bloqueo\n"
                "        this.queryThrottler = new Semaphore(maxConcurrentDbQueries, true);\n"
                "    }\n\n"
                "    public List<UserRecord> fetchUsersBatch(List<Long> userIds) {\n"
                "        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {\n"
                "            List<Future<UserRecord>> futures = userIds.stream()\n"
                "                .map(id -> executor.submit(() -> queryUserByIdWithThrottle(id)))\n"
                "                .toList();\n\n"
                "            return futures.stream()\n"
                "                .map(f -> {\n"
                "                    try {\n"
                "                        return f.get();\n"
                "                    } catch (Exception e) {\n"
                "                        throw new RuntimeException(\"Error al obtener usuario: \" + e.getMessage(), e);\n"
                "                    }\n"
                "                })\n"
                "                .toList();\n"
                "        }\n"
                "    }\n\n"
                "    private UserRecord queryUserByIdWithThrottle(long userId) throws Exception {\n"
                "        queryThrottler.acquire(); // Espera cooperativa de Virtual Thread\n"
                "        try (Connection conn = dataSource.getConnection();\n"
                "             PreparedStatement ps = conn.prepareStatement(\n"
                "                 \"SELECT id, username, email FROM app_users WHERE id = ?\")) {\n"
                "            ps.setLong(1, userId);\n"
                "            try (ResultSet rs = ps.executeQuery()) {\n"
                "                if (rs.next()) {\n"
                "                    return new UserRecord(rs.getLong(\"id\"), rs.getString(\"username\"), rs.getString(\"email\"));\n"
                "                }\n"
                "                throw new IllegalStateException(\"Usuario no encontrado: \" + userId);\n"
                "            }\n"
                "        } finally {\n"
                "            queryThrottler.release();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "1. `queryThrottler.acquire()` asegura que jamás se abran más de `maxConcurrentDbQueries` conexiones JDBC a la vez.\n"
                "2. Mientras los Virtual Threads esperan un permiso en el semáforo, son desmontados de sus hilos de transporte (carrier threads), manteniendo la CPU al 100% de disponibilidad para otras tareas."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 35: Code Completion - Máquina de Estados Finita (FSM) con Sealed Interfaces y Switch
    entries.append(
        create_record(
            prompt=(
                "Implementa una Máquina de Estados Finita (FSM) para el ciclo de vida de un pedido en comercio electrónico "
                "utilizando interfaces `sealed`, `record` y expresiones `switch` exhaustivas en Java 21. "
                "Modela los estados `PendingPayment`, `Authorized`, `InTransit`, `Delivered` y `Cancelled`, "
                "y los eventos `PaymentApproved`, `PaymentDeclined`, `Dispatched`, `DeliveredConfirmed` y `CustomerCancel`."
            ),
            response=(
                "Aquí tienes la implementación declarativa de la máquina de estados en Java 21:\n\n"
                "```java\n"
                "package com.m01.order.fsm;\n\n"
                "import java.time.Instant;\n\n"
                "public final class OrderStateMachine {\n\n"
                "    // Jerarquía sellada para Estados de la Orden\n"
                "    public sealed interface OrderState permits PendingPayment, Authorized, InTransit, Delivered, Cancelled {}\n\n"
                "    public record PendingPayment(String orderId, double amount) implements OrderState {}\n"
                "    public record Authorized(String orderId, String authorizationCode) implements OrderState {}\n"
                "    public record InTransit(String orderId, String trackingNumber, Instant departureTime) implements OrderState {}\n"
                "    public record Delivered(String orderId, Instant deliveryTime, String recipientSignature) implements OrderState {}\n"
                "    public record Cancelled(String orderId, String reason, Instant cancelledAt) implements OrderState {}\n\n"
                "    // Jerarquía sellada para Eventos de Dominio\n"
                "    public sealed interface OrderEvent permits PaymentApproved, PaymentDeclined, Dispatched, DeliveryConfirmed, CustomerCancel {}\n\n"
                "    public record PaymentApproved(String authCode) implements OrderEvent {}\n"
                "    public record PaymentDeclined(String reason) implements OrderEvent {}\n"
                "    public record Dispatched(String trackingNumber) implements OrderEvent {}\n"
                "    public record DeliveryConfirmed(String signature) implements OrderEvent {}\n"
                "    public record CustomerCancel(String reason) implements OrderEvent {}\n\n"
                "    // Función de transición pura y exhaustiva\n"
                "    public static OrderState transition(OrderState currentState, OrderEvent event) {\n"
                "        return switch (currentState) {\n"
                "            case PendingPayment p -> switch (event) {\n"
                "                case PaymentApproved pa -> new Authorized(p.orderId(), pa.authCode());\n"
                "                case PaymentDeclined pd -> new Cancelled(p.orderId(), \"Pago rechazado: \" + pd.reason(), Instant.now());\n"
                "                case CustomerCancel cc  -> new Cancelled(p.orderId(), \"Cancelado por cliente: \" + cc.reason(), Instant.now());\n"
                "                case Dispatched _, DeliveryConfirmed _ -> \n"
                "                    throw new IllegalStateException(\"Evento inválido para estado PendingPayment: \" + event);\n"
                "            };\n\n"
                "            case Authorized a -> switch (event) {\n"
                "                case Dispatched d      -> new InTransit(a.orderId(), d.trackingNumber(), Instant.now());\n"
                "                case CustomerCancel cc -> new Cancelled(a.orderId(), \"Cancelación con reembolso: \" + cc.reason(), Instant.now());\n"
                "                default -> throw new IllegalStateException(\"Evento inválido en estado Authorized: \" + event);\n"
                "            };\n\n"
                "            case InTransit it -> switch (event) {\n"
                "                case DeliveryConfirmed dc -> new Delivered(it.orderId(), Instant.now(), dc.signature());\n"
                "                default -> throw new IllegalStateException(\"No se puede alterar estado durante el tránsito: \" + event);\n"
                "            };\n\n"
                "            case Delivered d -> throw new IllegalStateException(\"El pedido ya ha sido entregado; estado terminal alcanzado.\");\n"
                "            case Cancelled c -> throw new IllegalStateException(\"El pedido ya fue cancelado; estado terminal alcanzado.\");\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Ventajas sobre el Patrón State Tradicional de GoF:\n"
                "1. **Inmutabilidad y Pureza Funcional:** Cada transición devuelve un nuevo estado inmutable sin mutar variables internas.\n"
                "2. **Auditoría Fácil:** Las reglas de transición están centralizadas en una función visible y testeable de manera unitaria."
            ),
            category="pattern_matching",
            task_type="code_completion",
        )
    )

    # Entry 36: Code Completion - Desestructuración de Respuesta API Genérica Anidada
    entries.append(
        create_record(
            prompt=(
                "Implementa un deserializador y procesador de respuestas API genéricas en Java 21. "
                "Define `record ApiResponse<T>(Header header, T body)`, `record Header(int status, String traceId)` "
                "y modelos de cuerpo `UserPayload(String username, String role)` y `ErrorPayload(String message, String code)`. "
                "Escribe un método que desestructure la respuesta usando record patterns anidados."
            ),
            response=(
                "Aquí tienes la implementación con deconstrucción de registros anidados genéricos en Java 21:\n\n"
                "```java\n"
                "package com.m01.api.client;\n\n"
                "public final class ApiResponseProcessor {\n\n"
                "    public record Header(int status, String traceId) {}\n"
                "    public record ApiResponse<T>(Header header, T body) {}\n\n"
                "    public record UserPayload(String username, String role) {}\n"
                "    public record ErrorPayload(String message, String code) {}\n\n"
                "    public sealed interface ProcessOutcome permits SuccessOutcome, FailureOutcome {}\n"
                "    public record SuccessOutcome(String userGreeting, String trace) implements ProcessOutcome {}\n"
                "    public record FailureOutcome(int httpStatus, String errorDetail, String trace) implements ProcessOutcome {}\n\n"
                "    public static ProcessOutcome handleResponse(ApiResponse<?> response) {\n"
                "        return switch (response) {\n"
                "            // Desestructuración anidada directa de Header y UserPayload\n"
                "            case ApiResponse(Header(int st, String trace), UserPayload(String user, String role))\n"
                "                when st >= 200 && st < 300 -> {\n"
                "                    String greeting = \"Bienvenido \" + user + \" (Rol: \" + role.toUpperCase() + \")\";\n"
                "                    yield new SuccessOutcome(greeting, trace);\n"
                "                }\n\n"
                "            // Desestructuración anidada de ErrorPayload\n"
                "            case ApiResponse(Header(int st, String trace), ErrorPayload(String msg, String errCode)) -> {\n"
                "                String detail = \"Error [\" + errCode + \"]: \" + msg;\n"
                "                yield new FailureOutcome(st, detail, trace);\n"
                "            }\n\n"
                "            // Caso de fallback para cuerpos no reconocidos\n"
                "            case ApiResponse(Header(int st, String trace), Object body) -> {\n"
                "                yield new FailureOutcome(st, \"Cuerpo de respuesta no soportado: \" + body, trace);\n"
                "            }\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Potencia del Compilador:\n"
                "- El compilador extrae `st`, `trace`, `user` y `role` en un único paso sin casteos `(UserPayload) response.body()`.\n"
                "- La cláusula `when st >= 200 && st < 300` condiciona la coincidencia según el código HTTP del encabezado."
            ),
            category="record_patterns",
            task_type="code_completion",
        )
    )

    # Entry 37: Code Completion - Rate Limiter Deslizante con SequencedCollection
    entries.append(
        create_record(
            prompt=(
                "Implementa un limitador de tasa de peticiones (Sliding Window Rate Limiter) en Java 21 "
                "utilizando un `ArrayDeque<Instant>` tratado como `SequencedCollection<Instant>`. "
                "Aprovecha métodos como `addLast()`, `getFirst()` y `removeFirst()` para descartar marcas de tiempo "
                "expiradas de manera thread-safe con `ReentrantLock`."
            ),
            response=(
                "Aquí tienes la implementación idiomática del limitador de tasa en Java 21:\n\n"
                "```java\n"
                "package com.m01.ratelimit;\n\n"
                "import java.time.Duration;\n"
                "import java.time.Instant;\n"
                "import java.util.ArrayDeque;\n"
                "import java.util.SequencedCollection;\n"
                "import java.util.concurrent.locks.ReentrantLock;\n\n"
                "public final class SlidingWindowRateLimiter {\n\n"
                "    private final int maxRequests;\n"
                "    private final Duration windowDuration;\n"
                "    private final SequencedCollection<Instant> timestamps;\n"
                "    private final ReentrantLock lock = new ReentrantLock();\n\n"
                "    public SlidingWindowRateLimiter(int maxRequests, Duration windowDuration) {\n"
                "        if (maxRequests <= 0) throw new IllegalArgumentException(\"maxRequests debe ser positivo\");\n"
                "        this.maxRequests = maxRequests;\n"
                "        this.windowDuration = windowDuration;\n"
                "        this.timestamps = new ArrayDeque<>(maxRequests);\n"
                "    }\n\n"
                "    public boolean tryAcquire() {\n"
                "        Instant now = Instant.now();\n"
                "        Instant windowStart = now.minus(windowDuration);\n\n"
                "        lock.lock();\n"
                "        try {\n"
                "            // Remueve las marcas de tiempo anteriores a la ventana deslizante\n"
                "            while (!timestamps.isEmpty() && timestamps.getFirst().isBefore(windowStart)) {\n"
                "                timestamps.removeFirst(); // API SequencedCollection\n"
                "            }\n\n"
                "            if (timestamps.size() < maxRequests) {\n"
                "                timestamps.addLast(now); // API SequencedCollection\n"
                "                return true;\n"
                "            }\n"
                "            return false;\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n\n"
                "    public int currentLoad() {\n"
                "        lock.lock();\n"
                "        try {\n"
                "            return timestamps.size();\n"
                "        } finally {\n"
                "            lock.unlock();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave de Java 21:\n"
                "- La referencia a `SequencedCollection<Instant>` desacopla la lógica interna del tipo de implementación subyacente.\n"
                "- `timestamps.getFirst()` y `timestamps.removeFirst()` proporcionan una interfaz limpia de cola sin depender de métodos legacy."
            ),
            category="sequenced_collections",
            task_type="code_completion",
        )
    )

    # Entry 38: Code Completion - Parser de Logs con '_' y Multi-catch
    entries.append(
        create_record(
            prompt=(
                "Crea un procesador de líneas de log estructuradas de alto rendimiento en Java 21. "
                "Utiliza variables no nombradas `_` para ignorar campos irrelevantes, excepciones en bloque multi-catch "
                "y lambdas de transformación de métricas."
            ),
            response=(
                "Aquí tienes la implementación limpia con variables no nombradas (`_`) en Java 21:\n\n"
                "```java\n"
                "package com.m01.logging;\n\n"
                "import java.time.Instant;\n"
                "import java.time.format.DateTimeParseException;\n"
                "import java.util.Optional;\n"
                "import java.util.regex.Pattern;\n\n"
                "public final class StructuredLogParser {\n\n"
                "    public record LogEntry(Instant timestamp, String level, String message, int responseTimeMs) {}\n\n"
                "    private static final Pattern LOG_DELIMITER = Pattern.compile(\"\\\\|\");\n\n"
                "    public static Optional<LogEntry> parseLine(String line) {\n"
                "        if (line == null || line.isBlank()) {\n"
                "            return Optional.empty();\n"
                "        }\n\n"
                "        String[] parts = LOG_DELIMITER.split(line.strip());\n"
                "        if (parts.length < 5) {\n"
                "            return Optional.empty();\n"
                "        }\n\n"
                "        // Formato esperado: [TIMESTAMP]|[LEVEL]|[THREAD_NAME]|[MESSAGE]|[LATENCY_MS]\n"
                "        // THREAD_NAME en parts[2] es descartado intencionalmente\n"
                "        try {\n"
                "            Instant timestamp = Instant.parse(parts[0].strip());\n"
                "            String level = parts[1].strip();\n"
                "            String message = parts[3].strip();\n"
                "            int latencyMs = Integer.parseInt(parts[4].strip());\n\n"
                "            return Optional.of(new LogEntry(timestamp, level, message, latencyMs));\n"
                "        } catch (DateTimeParseException | NumberFormatException _) { // Excepción ignorada idiomáticamente con '_'\n"
                "            return Optional.empty();\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Cumplimiento Idiomático:\n"
                "El bloque `catch (DateTimeParseException | NumberFormatException _)` indica explícitamente al compilador y al equipo de desarrollo "
                "que cualquier línea corrupta debe retornar `Optional.empty()` sin necesidad de inspeccionar ni loguear la excepción."
            ),
            category="unnamed_patterns",
            task_type="code_completion",
        )
    )

    # Entry 39: Code Completion - Agregado DDD con Sealed Domain Errors
    entries.append(
        create_record(
            prompt=(
                "Modela una cuenta bancaria en Java 21 siguiendo los principios de Domain-Driven Design (DDD). "
                "Define una jerarquía sellada `DomainError` con errores tipados `InsufficientBalance`, `AccountFrozen` "
                "y `DailyLimitExceeded`. Implementa la operación `withdraw` devolviendo un `Result<Account, DomainError>` "
                "sin arrojar excepciones de control de flujo."
            ),
            response=(
                "Aquí tienes la implementación completa del agregado bancario con errores de dominio sellados en Java 21:\n\n"
                "```java\n"
                "package com.m01.domain.banking;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.util.Objects;\n\n"
                "public final class BankAccountAggregate {\n\n"
                "    // Errores de dominio cerrados y fuertemente tipados\n"
                "    public sealed interface DomainError permits InsufficientBalance, AccountFrozen, DailyLimitExceeded {}\n\n"
                "    public record InsufficientBalance(BigDecimal requested, BigDecimal available) implements DomainError {}\n"
                "    public record AccountFrozen(String reason) implements DomainError {}\n"
                "    public record DailyLimitExceeded(BigDecimal requested, BigDecimal remainingLimit) implements DomainError {}\n\n"
                "    // Tipo de retorno funcional cerrado\n"
                "    public sealed interface Result<T, E> permits Result.Success, Result.Failure {\n"
                "        record Success<T, E>(T value) implements Result<T, E> {}\n"
                "        record Failure<T, E>(E error) implements Result<T, E> {}\n"
                "    }\n\n"
                "    public record BankAccount(\n"
                "        String accountId,\n"
                "        BigDecimal balance,\n"
                "        BigDecimal dailyLimitRemaining,\n"
                "        boolean isFrozen\n"
                "    ) {\n"
                "        public Result<BankAccount, DomainError> withdraw(BigDecimal amount) {\n"
                "            Objects.requireNonNull(amount, \"El monto de retiro no puede ser nulo\");\n"
                "            if (amount.compareTo(BigDecimal.ZERO) <= 0) {\n"
                "                throw new IllegalArgumentException(\"El monto debe ser estrictamente positivo\");\n"
                "            }\n\n"
                "            if (isFrozen) {\n"
                "                return new Result.Failure<>(new AccountFrozen(\"La cuenta está bloqueada por compliance\"));\n"
                "            }\n"
                "            if (amount.compareTo(dailyLimitRemaining) > 0) {\n"
                "                return new Result.Failure<>(new DailyLimitExceeded(amount, dailyLimitRemaining));\n"
                "            }\n"
                "            if (amount.compareTo(balance) > 0) {\n"
                "                return new Result.Failure<>(new InsufficientBalance(amount, balance));\n"
                "            }\n\n"
                "            BankAccount updated = new BankAccount(\n"
                "                accountId,\n"
                "                balance.subtract(amount),\n"
                "                dailyLimitRemaining.subtract(amount),\n"
                "                false\n"
                "            );\n"
                "            return new Result.Success<>(updated);\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Beneficios para Arquitectura Empresarial:\n"
                "1. **Cero Excepciones para Lógica de Negocio:** Las fallas de dominio no incurren en la penalización de rendimiento del llenado de stacktraces.\n"
                "2. **Pattern Matching en el Consumidor:** El controlador HTTP o servicio REST evalúa `switch (result)` y genera los códigos de respuesta (400, 403, 422) de forma exhaustiva."
            ),
            category="sealed_classes",
            task_type="code_completion",
        )
    )

    # Entry 40: Code Completion - Resilient HTTP Client con Retries y Virtual Threads
    entries.append(
        create_record(
            prompt=(
                "Implementa un cliente HTTP resiliente en Java 21 que ejecute reintentos automáticos "
                "con retroceso exponencial (exponential backoff y jitter) en caso de errores de red o códigos HTTP 503/504. "
                "Asegúrate de que las pausas con `Thread.sleep()` se ejecuten de manera no bloqueante en Virtual Threads."
            ),
            response=(
                "Aquí tienes la implementación del cliente HTTP con reintentos idiomáticos en Java 21:\n\n"
                "```java\n"
                "package com.m01.http.resilience;\n\n"
                "import java.io.IOException;\n"
                "import java.net.URI;\n"
                "import java.net.http.HttpClient;\n"
                "import java.net.http.HttpRequest;\n"
                "import java.net.http.HttpResponse;\n"
                "import java.time.Duration;\n"
                "import java.util.concurrent.ThreadLocalRandom;\n\n"
                "public final class ResilientHttpClient {\n\n"
                "    private final HttpClient client;\n"
                "    private final int maxRetries;\n"
                "    private final Duration baseDelay;\n\n"
                "    public ResilientHttpClient(int maxRetries, Duration baseDelay) {\n"
                "        this.maxRetries = maxRetries;\n"
                "        this.baseDelay = baseDelay;\n"
                "        this.client = HttpClient.newBuilder()\n"
                "            .version(HttpClient.Version.HTTP_2)\n"
                "            .connectTimeout(Duration.ofSeconds(4))\n"
                "            .build();\n"
                "    }\n\n"
                "    public HttpResponse<String> executeWithRetry(URI uri) throws InterruptedException, IOException {\n"
                "        HttpRequest request = HttpRequest.newBuilder()\n"
                "            .uri(uri)\n"
                "            .timeout(Duration.ofSeconds(6))\n"
                "            .header(\"Accept\", \"application/json\")\n"
                "            .GET()\n"
                "            .build();\n\n"
                "        int attempt = 0;\n"
                "        while (true) {\n"
                "            try {\n"
                "                attempt++;\n"
                "                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());\n"
                "                int statusCode = response.statusCode();\n"
                "                if (statusCode < 500 && statusCode != 429) {\n"
                "                    return response; // Éxito o error del cliente (no reintentable)\n"
                "                }\n"
                "                if (attempt > maxRetries) {\n"
                "                    return response;\n"
                "                }\n"
                "            } catch (IOException e) {\n"
                "                if (attempt > maxRetries) throw e;\n"
                "            }\n\n"
                "            // Cálculo de retroceso exponencial con jitter\n"
                "            long backoffMs = baseDelay.toMillis() * (1L << (attempt - 1));\n"
                "            long jitter = ThreadLocalRandom.current().nextLong(50, 200);\n"
                "            long totalSleepMs = backoffMs + jitter;\n\n"
                "            // En Java 21, Thread.sleep() desmonta el Virtual Thread del Carrier Thread\n"
                "            Thread.sleep(Duration.ofMillis(totalSleepMs));\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Comportamiento en Loom:\n"
                "`Thread.sleep(Duration)` en Java 21 es una operación nativa adaptada que no consume recursos de CPU ni bloquea el Carrier Thread del sistema operativo."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 41: Code Completion - MemoryLayout y GroupLayout en FFM API
    entries.append(
        create_record(
            prompt=(
                "Diseña un decodificador de encabezados de paquetes de red binarios en Java 21 utilizando "
                "la API Foreign Function & Memory (FFM). Define un `GroupLayout` que represente la estructura C:\n"
                "```c\n"
                "struct PacketHeader {\n"
                "    uint32_t magic;\n"
                "    uint16_t version;\n"
                "    uint16_t payloadLength;\n"
                "    uint64_t timestampNs;\n"
                "};\n"
                "```\n"
                "Escribe un método que lea un `MemorySegment` y extraiga los campos de manera tipada y segura."
            ),
            response=(
                "Aquí tienes la implementación usando `MemoryLayout` y VarHandles nativos en Java 21:\n\n"
                "```java\n"
                "package com.m01.network.binary;\n\n"
                "import java.lang.foreign.*;\n"
                "import java.lang.invoke.VarHandle;\n\n"
                "public final class BinaryPacketDecoder {\n\n"
                "    public record PacketHeader(int magic, short version, short payloadLength, long timestampNs) {}\n\n"
                "    // Definición del GroupLayout equivalente a la estructura struct C con alineamiento nativo\n"
                "    public static final GroupLayout PACKET_HEADER_LAYOUT = MemoryLayout.structLayout(\n"
                "        ValueLayout.JAVA_INT.withName(\"magic\"),\n"
                "        ValueLayout.JAVA_SHORT.withName(\"version\"),\n"
                "        ValueLayout.JAVA_SHORT.withName(\"payloadLength\"),\n"
                "        ValueLayout.JAVA_LONG.withName(\"timestampNs\")\n"
                "    );\n\n"
                "    private static final VarHandle MAGIC_HANDLE =\n"
                "        PACKET_HEADER_LAYOUT.varHandle(MemoryLayout.PathElement.groupElement(\"magic\"));\n"
                "    private static final VarHandle VERSION_HANDLE =\n"
                "        PACKET_HEADER_LAYOUT.varHandle(MemoryLayout.PathElement.groupElement(\"version\"));\n"
                "    private static final VarHandle LENGTH_HANDLE =\n"
                "        PACKET_HEADER_LAYOUT.varHandle(MemoryLayout.PathElement.groupElement(\"payloadLength\"));\n"
                "    private static final VarHandle TIMESTAMP_HANDLE =\n"
                "        PACKET_HEADER_LAYOUT.varHandle(MemoryLayout.PathElement.groupElement(\"timestampNs\"));\n\n"
                "    public static PacketHeader decode(MemorySegment segment) {\n"
                "        if (segment.byteSize() < PACKET_HEADER_LAYOUT.byteSize()) {\n"
                "            throw new IllegalArgumentException(\"Segmento insuficiente para encabezado de paquete: \" + segment.byteSize());\n"
                "        }\n\n"
                "        int magic = (int) MAGIC_HANDLE.get(segment, 0L);\n"
                "        short version = (short) VERSION_HANDLE.get(segment, 0L);\n"
                "        short length = (short) LENGTH_HANDLE.get(segment, 0L);\n"
                "        long timestampNs = (long) TIMESTAMP_HANDLE.get(segment, 0L);\n\n"
                "        return new PacketHeader(magic, version, length, timestampNs);\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Seguridad y Rendimiento:\n"
                "- Los `VarHandle` calculan los offsets y padding en tiempo de compilación/inicio de JVM sin overhead en ejecución.\n"
                "- Si el segmento apunta a memoria inválida o es menor a 16 bytes, se produce un error seguro en la JVM sin provocar un crash de proceso."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 42: Code Completion - Structured Concurrency con ShutdownOnSuccess (Racing)
    entries.append(
        create_record(
            prompt=(
                "Implementa un resolvedor de DNS / CDN de alta disponibilidad en Java 21 que consulte simultáneamente "
                "tres servidores redundantes en paralelo utilizando `StructuredTaskScope.ShutdownOnSuccess`. "
                "El sistema debe devolver la respuesta del primer servidor que conteste con éxito y cancelar "
                "inmediatamente las consultas restantes para minimizar latencia y consumo de ancho de banda."
            ),
            response=(
                "Aquí tienes la implementación utilizando `ShutdownOnSuccess` de Structured Concurrency en Java 21:\n\n"
                "```java\n"
                "package com.m01.network.racing;\n\n"
                "import java.time.Duration;\n"
                "import java.util.concurrent.StructuredTaskScope;\n"
                "\n"
                "public final class FastDnsResolver {\n\n"
                "    public record DnsResponse(String resolvedIp, String serverNode, long latencyMs) {}\n\n"
                "    public interface RemoteDnsProvider {\n"
                "        DnsResponse resolve(String hostname) throws Exception;\n"
                "    }\n\n"
                "    private final RemoteDnsProvider primaryServer;\n"
                "    private final RemoteDnsProvider secondaryServer;\n"
                "    private final RemoteDnsProvider edgeServer;\n\n"
                "    public FastDnsResolver(RemoteDnsProvider primary, RemoteDnsProvider secondary, RemoteDnsProvider edge) {\n"
                "        this.primaryServer = primary;\n"
                "        this.secondaryServer = secondary;\n"
                "        this.edgeServer = edge;\n"
                "    }\n\n"
                "    public DnsResponse resolveFastest(String hostname) throws Exception {\n"
                "        // ShutdownOnSuccess implementa la política 'First to finish wins'\n"
                "        try (var scope = new StructuredTaskScope.ShutdownOnSuccess<DnsResponse>()) {\n"
                "            scope.fork(() -> primaryServer.resolve(hostname));\n"
                "            scope.fork(() -> secondaryServer.resolve(hostname));\n"
                "            scope.fork(() -> edgeServer.resolve(hostname));\n\n"
                "            scope.join(); // Espera a que al menos un subtask complete con éxito\n"
                "            return scope.result(); // Devuelve el primer resultado y cancela los hilos de los otros 2 servidores\n"
                "        }\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "- En cuanto el primer servidor responde, `ShutdownOnSuccess` emite una señal de interrupción inmediata a los otros dos subtasks.\n"
                "- Esto reduce la latencia percibida al percentil $P_{min}$ de los tres nodos."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )
    return entries


def get_expert_showcase_entries() -> List[Dict[str, Any]]:
    """Entradas adicionales de nivel experto para completar 50+ muestras densas."""
    entries = []

    # Entry 43: Q&A - Generational ZGC y Virtual Threads en Java 21
    entries.append(
        create_record(
            prompt=(
                "Analiza el impacto de Generational ZGC (JEP 439) introducido en Java 21 cuando se combina "
                "con cargas masivas de Virtual Threads (Project Loom). ¿Por qué la separación generacional "
                "es crítica para aplicaciones con alta tasa de asignación de continuaciones efímeras en el Heap?"
            ),
            response=(
                "### Generational ZGC (JEP 439) y Virtual Threads en Java 21\n\n"
                "#### 1. La Tasa de Asignación con Virtual Threads\n"
                "En una aplicación que gestiona cientos de miles de solicitudes simultáneas con Virtual Threads:\n"
                "- Cada vez que un hilo virtual se suspende o finaliza su tarea, su marco de pila (stack frame en el Heap) "
                "se vuelve basura (**garbage**) en cuestión de microsegundos o milisegundos.\n"
                "- Esto produce una **tasa de asignación (allocation rate)** extremadamente alta de objetos de vida muy corta (young generation).\n\n"
                "#### 2. La Limitación de ZGC Clásico (Single-Generation)\n"
                "En Java 17, ZGC trataba toda la memoria como un único espacio plano sin distinguir entre objetos jóvenes y longevos. "
                "Bajo cargas intensivas de Loom, ZGC debía escanear todo el heap continuamente, arriesgándose a sufrir 'Allocation Stall' "
                "(cuando los hilos asignan memoria más rápido de lo que el recolector concurrente puede reclamar).\n\n"
                "#### 3. El Avance de Generational ZGC en Java 21 (`-XX:+UseZGC -XX:+ZGenerational`)\n"
                "1. **Hipótesis Generacional Débil:** La gran mayoría de los objetos (incluidas las pilas de los Virtual Threads efímeros) mueren jóvenes.\n"
                "2. **Colecciones Frecuentes de Young Gen:** Generational ZGC recolecta la generación joven en ciclos concurrentes de menos de 1 milisegundo "
                "sin necesidad de tocar los objetos de larga vida (cachés, pools de conexiones).\n"
                "3. **Pausas sub-milisegundo sostenidas:** Permite alcanzar latencias de parada de mundo (`Stop-The-World`) inferiores a 1 ms incluso con "
                "heaps de cientos de gigabytes y millones de Virtual Threads activos."
            ),
            category="virtual_threads",
            task_type="architecture_qa",
        )
    )

    # Entry 44: Code Completion - Parser/Evaluador AST JSON con Sealed Types y Pattern Matching
    entries.append(
        create_record(
            prompt=(
                "Diseña un modelo de datos inmutable para representar un documento JSON completo en Java 21 "
                "usando una jerarquía sellada `JsonValue` (`JsonObject`, `JsonArray`, `JsonString`, `JsonNumber`, `JsonBoolean`, `JsonNull`). "
                "Implementa una función `extractQuery` que busque valores anidados en un `JsonObject` "
                "utilizando switch exhaustivo y deconstrucción de registros."
            ),
            response=(
                "Aquí tienes la implementación completa del AST JSON con tipos algebraicos en Java 21:\n\n"
                "```java\n"
                "package com.m01.json.ast;\n\n"
                "import java.util.List;\n"
                "import java.util.Map;\n"
                "import java.util.Optional;\n\n"
                "public final class JsonAstEngine {\n\n"
                "    // Jerarquía sellada que modela las especificaciones RFC 8259 de JSON\n"
                "    public sealed interface JsonValue permits JsonObject, JsonArray, JsonString, JsonNumber, JsonBoolean, JsonNull {}\n\n"
                "    public record JsonObject(Map<String, JsonValue> members) implements JsonValue {}\n"
                "    public record JsonArray(List<JsonValue> elements) implements JsonValue {}\n"
                "    public record JsonString(String value) implements JsonValue {}\n"
                "    public record JsonNumber(double value) implements JsonValue {}\n"
                "    public record JsonBoolean(boolean value) implements JsonValue {}\n"
                "    public record JsonNull() implements JsonValue {}\n\n"
                "    public static Optional<String> extractNestedString(JsonValue root, String parentKey, String childKey) {\n"
                "        return switch (root) {\n"
                "            case JsonObject(var members) -> {\n"
                "                JsonValue child = members.get(parentKey);\n"
                "                yield switch (child) {\n"
                "                    case JsonObject(var subMembers) -> switch (subMembers.get(childKey)) {\n"
                "                        case JsonString(String str) -> Optional.of(str);\n"
                "                        case null, default -> Optional.empty();\n"
                "                    };\n"
                "                    case null, default -> Optional.empty();\n"
                "                };\n"
                "            }\n"
                "            case JsonArray _, JsonString _, JsonNumber _, JsonBoolean _, JsonNull _ -> Optional.empty();\n"
                "        };\n"
                "    }\n\n"
                "    public static String serializeCompact(JsonValue value) {\n"
                "        return switch (value) {\n"
                "            case JsonNull _ -> \"null\";\n"
                "            case JsonBoolean(boolean b) -> String.valueOf(b);\n"
                "            case JsonNumber(double n) -> (n == (long) n) ? String.valueOf((long) n) : String.valueOf(n);\n"
                "            case JsonString(String s) -> \"\\\"\" + s.replace(\"\\\"\", \"\\\\\\\"\") + \"\\\"\";\n"
                "            case JsonArray(var list) -> {\n"
                "                List<String> items = list.stream().map(JsonAstEngine::serializeCompact).toList();\n"
                "                yield \"[\" + String.join(\",\", items) + \"]\";\n"
                "            }\n"
                "            case JsonObject(var map) -> {\n"
                "                List<String> entries = map.entrySet().stream()\n"
                "                    .map(e -> \"\\\"\" + e.getKey() + \"\\\":\" + serializeCompact(e.getValue()))\n"
                "                    .toList();\n"
                "                yield \"{\" + String.join(\",\", entries) + \"}\";\n"
                "            }\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "1. `JsonAstEngine.serializeCompact` es una función completamente exhaustiva que nunca puede olvidar serializar un tipo JSON.\n"
                "2. En `case JsonArray _, JsonString _ ->`, las variables no nombradas `_` descartan componentes sin crear nombres ficticios."
            ),
            category="sealed_classes",
            task_type="code_completion",
        )
    )

    # Entry 45: Code Completion - Generador Dinámico de Consultas SQL con Text Blocks
    entries.append(
        create_record(
            prompt=(
                "Implementa un constructor de consultas analíticas SQL en Java 21 utilizando Text Blocks (`\"\"\"`) "
                "con sangría stripping e interpolación `.formatted()`. Modela cláusulas con Common Table Expressions (CTE) "
                "y funciones de ventana (Window Functions) de forma tipada y legible."
            ),
            response=(
                "Aquí tienes la implementación con Text Blocks idiomáticos en Java 21:\n\n"
                "```java\n"
                "package com.m01.sql.builder;\n\n"
                "import java.util.Objects;\n\n"
                "public final class AnalyticQueryBuilder {\n\n"
                "    public record QueryFilter(String tenantId, int year, double minRevenueThreshold, int limit) {}\n\n"
                "    public static String buildTopCustomersCteQuery(QueryFilter filter) {\n"
                "        Objects.requireNonNull(filter, \"El filtro de consulta no puede ser nulo\");\n\n"
                "        // Text Block con sangría preservada y escape de continuación '\\'\n"
                "        return \"\"\"\n"
                "        WITH RankedOrders AS (\n"
                "            SELECT \n"
                "                customer_id,\n"
                "                SUM(amount) AS total_revenue,\n"
                "                COUNT(id) AS order_count,\n"
                "                DENSE_RANK() OVER (ORDER BY SUM(amount) DESC) as revenue_rank\n"
                "            FROM sales_orders\n"
                "            WHERE tenant_id = '%s' \n"
                "              AND EXTRACT(YEAR FROM order_date) = %d\n"
                "            GROUP BY customer_id\n"
                "            HAVING SUM(amount) >= %.2f\n"
                "        )\n"
                "        SELECT \n"
                "            c.id AS customer_id,\n"
                "            c.company_name,\n"
                "            ro.total_revenue,\n"
                "            ro.order_count,\n"
                "            ro.revenue_rank\n"
                "        FROM RankedOrders ro\n"
                "        INNER JOIN customers c ON c.id = ro.customer_id\n"
                "        WHERE ro.revenue_rank <= %d\n"
                "        ORDER BY ro.revenue_rank ASC;\n"
                "        \"\"\".formatted(\n"
                "            filter.tenantId(),\n"
                "            filter.year(),\n"
                "            filter.minRevenueThreshold(),\n"
                "            filter.limit()\n"
                "        ).stripIndent();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Beneficios de Text Blocks:\n"
                "- Se copia y pega directamente desde clientes SQL (DBeaver, DataGrip) sin añadir `\\n\" +` en cada línea.\n"
                "- `.stripIndent()` remueve el prefijo de indentación izquierda coincidente, garantizando cadenas limpias para logging y auditoría."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 46: Q&A - Stream.takeWhile vs Stream.dropWhile vs iterate
    entries.append(
        create_record(
            prompt=(
                "Explica las mejoras de flujo de datos en el Stream API moderno de Java (Java 9 hasta 21): "
                "`takeWhile()`, `dropWhile()` y `Stream.iterate(seed, predicate, next)`. "
                "¿Por qué `takeWhile` es superior al método `filter` cuando se procesan secuencias ordenadas en tiempo real?"
            ),
            response=(
                "### Operaciones de Cortocircuito en Streams Modernos de Java\n\n"
                "#### 1. `takeWhile()` vs `filter()`\n"
                "Consideremos un Stream infinito o de gran volumen que emite eventos ordenados por marca temporal:\n"
                "- **`filter(predicate)`:** Es una operación **no cortocircuitante** para la terminación del flujo. "
                "Aunque encuentre elementos que no cumplen la condición, continuará examinando y evaluando **cada uno de los elementos restantes** "
                "del stream hasta el final.\n"
                "- **`takeWhile(predicate)`:** Es una operación de **cortocircuito estricto** (`short-circuiting`). En cuanto encuentra el **primer elemento** "
                "que evalúa a `false`, aborta inmediatamente el stream y finaliza el consumo de la fuente de datos.\n\n"
                "```java\n"
                "// Si el stream tiene 1,000,000 de números ordenados:\n"
                "stream.takeWhile(n -> n < 100); // Se detiene exactamente en el elemento 100.\n"
                "stream.filter(n -> n < 100);    // Evalúa los 1,000,000 de elementos innecesariamente.\n"
                "```\n\n"
                "#### 2. `dropWhile()`\n"
                "Descarta de forma eficiente los elementos iniciales mientras se cumpla el predicado. En cuanto un elemento falla la condición, "
                "permite el paso ininterrumpido de todos los elementos posteriores sin volver a evaluar el predicado.\n\n"
                "#### 3. `Stream.iterate(seed, predicate, next)`\n"
                "Reemplaza el bucle `for` imperativo tradicional por un generador funcional seguro con condición de parada explícita:\n"
                "```java\n"
                "// Generación de potencias de 2 inferiores a 1024:\n"
                "List<Integer> powers = Stream.iterate(1, n -> n < 1024, n -> n * 2).toList();\n"
                "```"
            ),
            category="modern_apis",
            task_type="architecture_qa",
        )
    )

    # Entry 47: Code Completion - Pipeline con SequencedSet y reversed()
    entries.append(
        create_record(
            prompt=(
                "Implementa un servicio de historial de navegación de usuario en Java 21 utilizando `LinkedHashSet` "
                "como un `SequencedSet<String>`. Debe mantener las URLs visitadas sin duplicados, desplazar URLs repetidas "
                "al final (más recientes) y permitir exportar el historial en orden inverso (de la última a la primera) "
                "usando `.reversed()` sin clonar la colección."
            ),
            response=(
                "Aquí tienes la implementación utilizando `SequencedSet` en Java 21:\n\n"
                "```java\n"
                "package com.m01.browser.history;\n\n"
                "import java.util.LinkedHashSet;\n"
                "import java.util.List;\n"
                "import java.util.Objects;\n"
                "import java.util.SequencedSet;\n\n"
                "public final class BrowsingHistoryService {\n\n"
                "    private final SequencedSet<String> history = new LinkedHashSet<>();\n"
                "    private final int maxEntries;\n\n"
                "    public BrowsingHistoryService(int maxEntries) {\n"
                "        this.maxEntries = maxEntries;\n"
                "    }\n\n"
                "    public synchronized void recordVisit(String url) {\n"
                "        Objects.requireNonNull(url, \"La URL no puede ser nula\");\n"
                "        \n"
                "        // Si ya existía, removemos para asegurar que re-ingrese en la posición más reciente\n"
                "        history.remove(url);\n"
                "        \n"
                "        if (history.size() >= maxEntries) {\n"
                "            history.removeFirst(); // Elimina la URL más antigua en O(1) vía SequencedSet\n"
                "        }\n"
                "        \n"
                "        history.addLast(url); // Añade al final de la secuencia\n"
                "    }\n\n"
                "    public synchronized List<String> getChronologicalHistory() {\n"
                "        return List.copyOf(history);\n"
                "    }\n\n"
                "    public synchronized List<String> getRecentFirstHistory() {\n"
                "        // history.reversed() es una vista en O(1) de SequencedSet\n"
                "        return List.copyOf(history.reversed());\n"
                "    }\n\n"
                "    public synchronized String getMostRecentUrl() {\n"
                "        return history.isEmpty() ? null : history.getLast();\n"
                "    }\n\n"
                "    public synchronized String getOldestUrl() {\n"
                "        return history.isEmpty() ? null : history.getFirst();\n"
                "    }\n\n"
                "    public synchronized int size() {\n"
                "        return history.size();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Relevantes de SequencedSet:\n"
                "- Combina la garantía de no duplicidad de `Set<E>` con el acceso directo a los extremos `getFirst()`, `getLast()`, `addLast()` y `removeFirst()`.\n"
                "- `history.reversed()` proporciona la vista en reversa instantánea sin duplicar el conjunto ni reordenar elementos."
            ),
            category="sequenced_collections",
            task_type="code_completion",
        )
    )

    # Entry 48: Code Completion - Concurrencia Estructurada con Logging Contextual
    entries.append(
        create_record(
            prompt=(
                "Implementa un despachador de reportes ejecutivos en Java 21 que combine `StructuredTaskScope.ShutdownOnFailure` "
                "con `ScopedValue` para propagar de forma inmutable un `ReportContext(String companyId, String quarter, String requestedBy)` "
                "hacia las tareas concurrentes que generan reportes financieros, de inventario y de recursos humanos."
            ),
            response=(
                "Aquí tienes la integración sinérgica entre Structured Concurrency y Scoped Values en Java 21:\n\n"
                "```java\n"
                "package com.m01.reports;\n\n"
                "import java.util.concurrent.StructuredTaskScope;\n"
                "import java.util.concurrent.StructuredTaskScope.Subtask;\n"
                "\n"
                "public final class ExecutiveReportGenerator {\n\n"
                "    public record ReportContext(String companyId, String quarter, String requestedBy) {}\n"
                "    public record FinancialSection(String data) {}\n"
                "    public record InventorySection(String data) {}\n"
                "    public record HrSection(String data) {}\n"
                "    public record CompleteExecutiveReport(\n"
                "        ReportContext context,\n"
                "        FinancialSection finance,\n"
                "        InventorySection inventory,\n"
                "        HrSection hr\n"
                "    ) {}\n\n"
                "    public static final ScopedValue<ReportContext> REPORT_CTX = ScopedValue.newInstance();\n\n"
                "    public CompleteExecutiveReport generateReport(ReportContext ctx) throws Exception {\n"
                "        // Vinculación léxica inmutable del contexto en el ScopedValue\n"
                "        return ScopedValue.where(REPORT_CTX, ctx).call(() -> {\n"
                "            try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {\n"
                "                Subtask<FinancialSection> financeTask = scope.fork(this::fetchFinance);\n"
                "                Subtask<InventorySection> inventoryTask = scope.fork(this::fetchInventory);\n"
                "                Subtask<HrSection> hrTask = scope.fork(this::fetchHr);\n\n"
                "                scope.join(); // Espera a todos los subtasks o al primer fallo\n"
                "                scope.throwIfFailed(); // Propaga excepción si algún subtask falló\n\n"
                "                return new CompleteExecutiveReport(\n"
                "                    REPORT_CTX.get(),\n"
                "                    financeTask.get(),\n"
                "                    inventoryTask.get(),\n"
                "                    hrTask.get()\n"
                "                );\n"
                "            }\n"
                "        });\n"
                "    }\n\n"
                "    private FinancialSection fetchFinance() {\n"
                "        ReportContext ctx = REPORT_CTX.get(); // Heredado automáticamente sin clonación de hilos\n"
                "        return new FinancialSection(\"Finanzas para \" + ctx.companyId() + \" en \" + ctx.quarter());\n"
                "    }\n\n"
                "    private InventorySection fetchInventory() {\n"
                "        ReportContext ctx = REPORT_CTX.get();\n"
                "        return new InventorySection(\"Inventario auditado por \" + ctx.requestedBy());\n"
                "    }\n\n"
                "    private HrSection fetchHr() {\n"
                "        ReportContext ctx = REPORT_CTX.get();\n"
                "        return new HrSection(\"Planilla aprobada para \" + ctx.companyId());\n"
                "    }\n\n"
                "}\n"
                "```\n\n"
                "### Sinergia de Java 21:\n"
                "- Los hilos virtuales creados por `scope.fork()` acceden de forma nativa a `REPORT_CTX.get()` sin necesidad de clonar diccionarios `ThreadLocal`.\n"
                "- Si `fetchFinance()` falla, `ShutdownOnFailure` cancela inmediatamente a `fetchInventory()` y `fetchHr()`."
            ),
            category="virtual_threads",
            task_type="code_completion",
        )
    )

    # Entry 49: Code Completion - CQRS Command Dispatcher con Pattern Matching
    entries.append(
        create_record(
            prompt=(
                "Implementa un enrutador de comandos CQRS en Java 21 utilizando una jerarquía sellada `Command` "
                "con implementaciones para `CreateAccount(String holderName, String currency)`,\n"
                "`DepositFunds(String accountId, BigDecimal amount)` y `CloseAccount(String accountId, String reason)`. "
                "Escribe un método `dispatch` que procese cada comando de forma exhaustiva mediante `switch` y record patterns."
            ),
            response=(
                "Aquí tienes la implementación del despachador de comandos CQRS en Java 21:\n\n"
                "```java\n"
                "package com.m01.cqrs.dispatcher;\n\n"
                "import java.math.BigDecimal;\n"
                "import java.time.Instant;\n"
                "import java.util.Objects;\n\n"
                "public final class CommandDispatcher {\n\n"
                "    public sealed interface Command permits CreateAccount, DepositFunds, CloseAccount {}\n\n"
                "    public record CreateAccount(String holderName, String currency) implements Command {\n"
                "        public CreateAccount {\n"
                "            Objects.requireNonNull(holderName, \"Nombre del titular requerido\");\n"
                "            Objects.requireNonNull(currency, \"Moneda requerida\");\n"
                "        }\n"
                "    }\n\n"
                "    public record DepositFunds(String accountId, BigDecimal amount) implements Command {\n"
                "        public DepositFunds {\n"
                "            Objects.requireNonNull(accountId);\n"
                "            if (amount.compareTo(BigDecimal.ZERO) <= 0) {\n"
                "                throw new IllegalArgumentException(\"El depósito debe ser positivo: \" + amount);\n"
                "            }\n"
                "        }\n"
                "    }\n\n"
                "    public record CloseAccount(String accountId, String reason) implements Command {}\n\n"
                "    public record CommandResult(boolean success, String executionMessage, Instant executedAt) {}\n\n"
                "    public CommandResult dispatch(Command command) {\n"
                "        // Switch exhaustivo que garantiza que ningún comando nuevo quede sin manejar\n"
                "        return switch (command) {\n"
                "            case CreateAccount(String holder, String curr) -> {\n"
                "                String generatedId = \"ACC-\" + Math.abs(holder.hashCode()) + \"-\" + curr;\n"
                "                yield new CommandResult(true, \"Cuenta creada para \" + holder + \" con ID: \" + generatedId, Instant.now());\n"
                "            }\n\n"
                "            case DepositFunds(String id, BigDecimal amt) when amt.compareTo(BigDecimal.valueOf(1_000_000)) >= 0 -> {\n"
                "                yield new CommandResult(true, \"Depósito de alto volumen registrado por \" + amt + \" en cuenta: \" + id, Instant.now());\n"
                "            }\n\n"
                "            case DepositFunds(String id, BigDecimal amt) -> {\n"
                "                yield new CommandResult(true, \"Depósito regular acreditado por \" + amt + \" en cuenta: \" + id, Instant.now());\n"
                "            }\n\n"
                "            case CloseAccount(String id, String reason) -> {\n"
                "                yield new CommandResult(true, \"Cuenta cerrada: \" + id + \". Razón: \" + reason, Instant.now());\n"
                "            }\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Arquitectura Limpia:\n"
                "El compilador comprueba la exhaustividad del dominio cerrado `Command`. La adición de un nuevo comando obligará a registrar su respectivo manejador."
            ),
            category="pattern_matching",
            task_type="code_completion",
        )
    )

    # Entry 50: Q&A - SequencedMap sequencedKeySet y sequencedValues
    entries.append(
        create_record(
            prompt=(
                "Describe la utilidad y comportamiento de los métodos `sequencedKeySet()`, `sequencedValues()` "
                "y `sequencedEntrySet()` en la interfaz `SequencedMap` de Java 21 (JEP 431). "
                "¿Por qué facilitan operaciones de ordenamiento sin requerir copias temporales a listas?"
            ),
            response=(
                "### Métodos Sequenced en `SequencedMap` de Java 21\n\n"
                "Antes de Java 21, para acceder a las claves o valores de un `LinkedHashMap` en orden inverso, "
                "era obligatorio copiar toda la colección a un `ArrayList` intermedio y utilizar `Collections.reverse(list)`:\n"
                "```java\n"
                "// Código legacy ineficiente (O(N) tiempo y O(N) espacio):\n"
                "List<String> keys = new ArrayList<>(linkedMap.keySet());\n"
                "Collections.reverse(keys);\n"
                "```\n\n"
                "#### La Solución en Java 21\n"
                "La interfaz `SequencedMap<K, V>` proporciona:\n"
                "1. `SequencedSet<K> sequencedKeySet()`: Devuelve un `SequencedSet` que conserva el orden del mapa y soporta `.reversed()`, `getFirst()` y `getLast()`.\n"
                "2. `SequencedCollection<V> sequencedValues()`: Devuelve una `SequencedCollection` de los valores, posibilitando la iteración en reversa directa mediante `.reversed()`.\n"
                "3. `SequencedSet<Map.Entry<K, V>> sequencedEntrySet()`: Permite navegar el conjunto de entradas directamente desde los extremos.\n\n"
                "#### Eficiencia:\n"
                "Todas estas vistas son $O(1)$ en tiempo de creación y no reservan memoria adicional para elementos, "
                "lo que reduce la presión en el Garbage Collector."
            ),
            category="sequenced_collections",
            task_type="architecture_qa",
        )
    )

    # Entry 51: Code Completion - Streaming NDJSON con HttpClient y Virtual Threads
    entries.append(
        create_record(
            prompt=(
                "Implementa un consumidor de streaming de datos en tiempo real (NDJSON / newline-delimited JSON) "
                "en Java 21 utilizando `java.net.http.HttpClient` y `HttpResponse.BodyHandlers.ofLines()`. "
                "Procesa cada línea asíncronamente en un Virtual Thread usando `Thread.ofVirtual().start()`."
            ),
            response=(
                "Aquí tienes la implementación del consumidor reactivo de líneas en Java 21:\n\n"
                "```java\n"
                "package com.m01.streaming.ndjson;\n\n"
                "import java.io.IOException;\n"
                "import java.net.URI;\n"
                "import java.net.http.HttpClient;\n"
                "import java.net.http.HttpRequest;\n"
                "import java.net.http.HttpResponse;\n"
                "import java.time.Duration;\n"
                "import java.util.concurrent.atomic.AtomicLong;\n"
                "import java.util.function.Consumer;\n"
                "import java.util.stream.Stream;\n\n"
                "public final class NdjsonStreamConsumer {\n\n"
                "    private final HttpClient client;\n"
                "    private final AtomicLong processedCount = new AtomicLong(0);\n\n"
                "    public NdjsonStreamConsumer() {\n"
                "        this.client = HttpClient.newBuilder()\n"
                "            .version(HttpClient.Version.HTTP_2)\n"
                "            .connectTimeout(Duration.ofSeconds(5))\n"
                "            .build();\n"
                "    }\n\n"
                "    public void consumeStream(URI streamUri, Consumer<String> lineProcessor) throws IOException, InterruptedException {\n"
                "        HttpRequest request = HttpRequest.newBuilder()\n"
                "            .uri(streamUri)\n"
                "            .header(\"Accept\", \"application/x-ndjson\")\n"
                "            .GET()\n"
                "            .build();\n\n"
                "        // ofLines() transmite la respuesta HTTP como un Stream reactivo de líneas delimitadas por '\\n'\n"
                "        HttpResponse<Stream<String>> response = client.send(request, HttpResponse.BodyHandlers.ofLines());\n\n"
                "        if (response.statusCode() != 200) {\n"
                "            throw new IllegalStateException(\"Error de stream HTTP: \" + response.statusCode());\n"
                "        }\n\n"
                "        try (Stream<String> lines = response.body()) {\n"
                "            lines.forEach(line -> {\n"
                "                if (!line.isBlank()) {\n"
                "                    // Despacho de cada evento a un Virtual Thread efímero\n"
                "                    Thread.ofVirtual()\n"
                "                        .name(\"ndjson-worker-\", processedCount.incrementAndGet())\n"
                "                        .start(() -> lineProcessor.accept(line.strip()));\n"
                "                }\n"
                "            });\n"
                "        }\n"
                "    }\n\n"
                "    public long getProcessedCount() {\n"
                "        return processedCount.get();\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Puntos Clave:\n"
                "- `BodyHandlers.ofLines()` evita almacenar en memoria búfer respuestas completas gigantescas.\n"
                "- Cada línea es procesada concurrentemente por un Virtual Thread sin saturar el pool del sistema operativo."
            ),
            category="modern_apis",
            task_type="code_completion",
        )
    )

    # Entry 52: Code Completion - Contexto de Autorización Multinivel con Record Patterns
    entries.append(
        create_record(
            prompt=(
                "Implementa un evaluador de políticas de autorización multinivel en Java 21. "
                "Define records anidados para `Role(String name, int securityLevel)`,\n"
                "`User(String id, String username, Role role)` y `AuthContext(User user, String ipAddress, boolean mfaVerified)`. "
                "Implementa el método `authorizeAction` usando Record Patterns anidados y guardas `when` para validar acceso a operaciones críticas."
            ),
            response=(
                "Aquí tienes la implementación del motor de autorización con deconstrucción multinivel en Java 21:\n\n"
                "```java\n"
                "package com.m01.security.rbac;\n\n"
                "public final class AuthorizationPolicyEngine {\n\n"
                "    public record Role(String name, int securityLevel) {}\n"
                "    public record User(String id, String username, Role role) {}\n"
                "    public record AuthContext(User user, String ipAddress, boolean mfaVerified) {}\n\n"
                "    public enum AccessDecision { GRANTED, DENIED_NO_MFA, DENIED_INSUFFICIENT_PRIVILEGES, DENIED_ANONYMOUS }\n\n"
                "    public static AccessDecision authorizeAction(AuthContext context, int requiredLevel) {\n"
                "        return switch (context) {\n"
                "            case null -> AccessDecision.DENIED_ANONYMOUS;\n\n"
                "            // Nivel de seguridad alto requiere verificación MFA obligatoria\n"
                "            case AuthContext(User(_, _, Role(_, int lvl)), _, boolean mfa) \n"
                "                when lvl >= requiredLevel && requiredLevel >= 3 && !mfa -> \n"
                "                    AccessDecision.DENIED_NO_MFA;\n\n"
                "            // Nivel suficiente y MFA satisfecho\n"
                "            case AuthContext(User(_, _, Role(_, int lvl)), _, _) \n"
                "                when lvl >= requiredLevel -> \n"
                "                    AccessDecision.GRANTED;\n\n"
                "            // Nivel insuficiente\n"
                "            case AuthContext(User(_, _, Role(_, int lvl)), _, _) -> \n"
                "                AccessDecision.DENIED_INSUFFICIENT_PRIVILEGES;\n"
                "        };\n"
                "    }\n"
                "}\n"
                "```\n\n"
                "### Ventajas de los Record Patterns:\n"
                "- Se desestructura a tres niveles de profundidad (`AuthContext` -> `User` -> `Role`) en una sola línea.\n"
                "- Las variables no requeridas (`id`, `username`, `name`, `ipAddress`) se sustituyen con variables no nombradas `_`."
            ),
            category="record_patterns",
            task_type="code_completion",
        )
    )

    return entries


def build_all_entries() -> List[Dict[str, Any]]:
    all_entries = []
    all_entries.extend(get_virtual_threads_entries())
    all_entries.extend(get_pattern_matching_switch_entries())
    all_entries.extend(get_record_patterns_entries())
    all_entries.extend(get_sequenced_collections_entries())
    all_entries.extend(get_unnamed_patterns_entries())
    all_entries.extend(get_sealed_hierarchies_entries())
    all_entries.extend(get_modern_apis_entries())
    all_entries.extend(get_additional_deep_entries())
    all_entries.extend(get_advanced_enterprise_entries())
    all_entries.extend(get_expert_showcase_entries())
    return all_entries


def main():
    print("=" * 70)
    print("CONSTRUCTOR DEL CORPUS JAVA 21+ LTS PARA M0.1")
    print("=" * 70)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    entries = build_all_entries()
    print(f"[*] Total de entradas generadas: {len(entries)}")

    # Escribir archivo JSONL
    print(f"[*] Escribiendo dataset en: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # Mantener enlace simbólico para compatibilidad retroactiva
    if LEGACY_OUTPUT_FILE.is_symlink() or not LEGACY_OUTPUT_FILE.exists():
        if LEGACY_OUTPUT_FILE.is_symlink():
            LEGACY_OUTPUT_FILE.unlink()
        LEGACY_OUTPUT_FILE.symlink_to(OUTPUT_FILE.name)

    file_size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"[+] Archivo generado exitosamente ({file_size_kb:.2f} KB)")

    # Verificación con Tokenizer de 16k
    if not TOKENIZER_PATH.exists():
        print(f"[!] ADVERTENCIA: No se encontró el tokenizer en {TOKENIZER_PATH}")
        return

    print("\n[*] Cargando Tokenizer canónico de 16k...")
    from src.tokenizer.bpe import Tokenizer
    tokenizer = Tokenizer()
    tokenizer.load(str(TOKENIZER_PATH))
    vocab_size = len(tokenizer.vocab)
    print(f"[+] Tokenizer cargado con éxito. Tamaño de vocabulario: {vocab_size} tokens")

    print("[*] Verificando tokenización e integridad de cada entrada...")
    total_tokens = 0
    token_counts = []
    unique_tokens = set()

    for idx, entry in enumerate(entries):
        text_to_tokenize = f"{entry['system']}\n{entry['conversation']}"
        tokens = tokenizer.encode(text_to_tokenize)
        count = len(tokens)
        total_tokens += count
        token_counts.append(count)
        unique_tokens.update(tokens)

        # Verificación de decodificación para integridad
        decoded = tokenizer.decode(tokens)
        if len(decoded) < len(text_to_tokenize) * 0.8:
            print(f"[!] ADVERTENCIA en entrada {idx}: longitud decodificada anómala.")

    avg_tokens = total_tokens / max(len(entries), 1)
    min_tokens = min(token_counts) if token_counts else 0
    max_tokens = max(token_counts) if token_counts else 0

    print("=" * 70)
    print("MÉTRICAS DEL CORPUS JAVA 21+ LTS:")
    print(f"  - Total de registros: {len(entries)}")
    print(f"  - Total de tokens: {total_tokens:,}")
    print(f"  - Promedio de tokens por registro: {avg_tokens:.1f}")
    print(f"  - Rango de tokens: [{min_tokens} .. {max_tokens}]")
    print(f"  - Tokens únicos utilizados del vocabulario 16k: {len(unique_tokens):,} / {vocab_size:,}")
    print("=" * 70)

    # Verificación de compatibilidad con JsonlDataset
    print("\n[*] Validando compatibilidad con JsonlDataset...")
    from src.training.datasets import JsonlDataset
    dataset = JsonlDataset(
        tokenizer=tokenizer,
        paths=[str(OUTPUT_FILE)],
        seq_len=256,
        max_lines_per_shard=1000,
    )
    print(f"[+] JsonlDataset cargado correctamente. Muestras sliding-window: {len(dataset)}")

    # Verificación de compatibilidad con PackedSequenceIterator
    print("\n[*] Validando compatibilidad con PackedSequenceIterator...")
    from src.training.sequence_packing import PackedSequenceIterator

    def doc_token_stream():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line)
                yield tokenizer.encode(f"{data['system']}\n{data['conversation']}")

    packer = PackedSequenceIterator(doc_token_stream(), seq_len=1024, eot_id=256)
    packed_samples = 0
    for input_ids, target_ids, attn_mask in packer:
        packed_samples += 1
        assert input_ids.shape == (1024,), f"Shape inválido: {input_ids.shape}"
        assert target_ids.shape == (1024,), f"Shape inválido: {target_ids.shape}"
        assert attn_mask.shape == (1024, 1024), f"Mask inválido: {attn_mask.shape}"
        if packed_samples >= 5:
            break

    print(f"[+] PackedSequenceIterator validado con éxito. Procesó {packed_samples} bloques empaquetados de 1024 tokens sin desperdicio.")
    print("=" * 70)
    print("VERIFICACIÓN COMPLETA: CORPUS LISTO PARA PREENTRENAMIENTO Y SFT DE M0.1")
    print("=" * 70)


if __name__ == "__main__":
    main()
