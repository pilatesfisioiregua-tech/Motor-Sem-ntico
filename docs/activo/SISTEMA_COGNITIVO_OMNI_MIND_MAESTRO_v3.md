# SISTEMA COGNITIVO OMNI-MIND v3 — DOCUMENTO MAESTRO

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-16
**Versión:** 3.0
**Supersede:** SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md y todos los documentos satélite de actualizaciones (ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md, ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md, CONCLUSIONES_EXP4_SESION_11MAR.md, ARQUITECTURA_MECANISMOS_MULTI_MODELO.md, MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md)

---

## §0. POR QUÉ EXISTE ESTA VERSIÓN

El Maestro v2 fue escrito sesión 09-mar y parcheado hasta 13-mar. Acumuló 47 cambios en §0, secciones especulativas mezcladas con datos empíricos, y componentes deprecados listados como activos. 10 experimentos completados entre 09-mar y 16-mar produjeron datos que invalidan algunas decisiones y validan otras. Este documento reescribe desde cero con una regla: cada afirmación se etiqueta con su nivel de certeza.

**Niveles de certeza:**
- **✅ VALIDADO** — dato empírico de experimentos o cartografía
- **🔧 DISEÑADO** — arquitectura definida, sin implementación
- **⬜ HORIZONTE** — concepto con potencial, sin datos

---

## §1. QUÉ ES OMNI-MIND

Un sistema cognitivo que percibe gaps en cualquier caso, compila un programa de preguntas para cerrarlos, ejecuta ese programa con un enjambre de modelos OS, verifica el cierre, y aprende de cada ejecución.

### §1.1 El principio central ✅

**El prompt del agente no tiene instrucciones imperativas. Es exclusivamente una red de preguntas.** La inteligencia emerge de la estructura de preguntas, no de instrucciones al modelo. No le dices al agente "analiza como financiero" — le das la red de preguntas de INT-07 y el agente no puede hacer otra cosa que operar financieramente.

Las preguntas son el sistema operativo interno del agente — la lente a través de la cual mira y procesa. Validado en 54 análisis × 3 casos × 18 inteligencias donde cada red de preguntas produce un vocabulario de percepción diferente y objetos exclusivos no visibles para otras inteligencias.

El prompt tiene DOS partes:
1. **Parte imperativa (álgebra L0):** EXTRAER→CRUZAR→LENTES→INTEGRAR→ABSTRAER→FRONTERA — secuencia fija de procesamiento que estructura cómo el agente recorre cualquier caso.
2. **Preguntas por paso (L1/L2):** contenido específico de cada inteligencia que determina QUÉ percibe en cada paso. Estas preguntas son las que el Gestor compila, poda y mejora.

### §1.2 Los componentes

```
LA MATRIZ (3L × 7F × 18INT × preguntas)         → §2
  = el producto, el prompt, el algoritmo

EL GESTOR DE LA MATRIZ (mira hacia dentro)        → §6
  = mantiene, poda, mejora y compila la Matriz
  = alimenta a TODOS los consumidores

EL MOTOR vN (mira hacia fuera)                    → §5
  = ejecuta la Matriz sobre casos reales
  = genera datapoints de efectividad para el Gestor

EL ENJAMBRE DE MODELOS OS                         → §4
  = red neuronal cuyos nodos son LLMs
  = la Matriz es su matriz de pesos
  = el Gestor es su algoritmo de entrenamiento

EL ÁLGEBRA DEL CÁLCULO SEMÁNTICO                  → §3
  = el compilador que ensambla preguntas en prompts

EL PIPELINE                                        → §5
  = percibir gaps → compilar prompt → ejecutar → verificar cierre

LOS REACTORES                                      → §7
  = la fábrica que llena y enriquece la Matriz
```

### §1.3 Los dos loops ✅

```
LOOP RÁPIDO — Motor vN (cadencia: segundos a minutos)
  Caso entra → ejecuta con Matriz actual → registra efectividad → siguiente caso
  Mira HACIA FUERA: opera sobre casos de usuarios

LOOP LENTO — Gestor de la Matriz (cadencia: horas/días)
  Cada N ejecuciones → analiza patrones → poda/mejora → recompila programas
  Mira HACIA DENTRO: opera sobre la Matriz misma

El Motor NO se reconfigura en caliente. Ejecuta con lo que tiene.
El Gestor revisa periódicamente y le entrega una Matriz mejorada.
```

### §1.4 El enjambre como red neuronal ✅ (Principio 32)

El enjambre no es un pipeline — es una red neuronal cuyos nodos son LLMs.

| Propiedad | Red neuronal clásica | Enjambre OMNI-MIND |
|-----------|---------------------|-------------------|
| Nodo | función de activación | LLM completo (V3.2, R1, Cogito) |
| Peso de conexión | float aprendido por backprop | tasa_media_cierre de modelo→celda (datos Gestor) |
| Capa oculta | representación intermedia | ronda de estigmergia (output parcial → siguiente ronda) |
| Forward pass | input → capas → output (ms) | pregunta → rondas de enjambre → síntesis (segundos) |
| Backpropagation | gradiente del error | feedback: ¿la respuesta cerró el gap? |
| Topología | fija por arquitectura | dinámica por input — la Matriz decide qué conexiones se activan |

**6 implicaciones:**
1. No se diseña el enjambre — se entrena (datos de efectividad, no decisión humana). ✅ GPT-OSS es motor en pizarra (119 contribuciones) pero esponja en evaluación (0 aportes únicos). El mismo nodo cambia de peso según el mecanismo.
2. La topología es dinámica por input — el campo de gradientes determina qué nodos se activan. Una pregunta financiera activa una sub-red; una pregunta de diseño activa otra.
3. Las rondas de estigmergia son capas ocultas — Exp 4.3: 425 conexiones emergentes que ningún nodo individual habría producido. Eso es exactamente lo que hacen las capas ocultas: crear features no presentes en los datos de entrada.
4. Cada exocortex es una red con topología propia — mismos nodos disponibles, diferentes pesos entrenados por datos de efectividad de su dominio.
5. Scaling = topología, no volumen — Exp 4: 12 modelos, valor concentrado en 2-3 nodos. Añadir nodos sin ajustar topología = ruido.
6. El moat es la red entrenada — miles de datapoints de efectividad que dicen "para este patrón de gaps, esta combinación produce el mejor cierre". Esa es la propiedad intelectual.

Dato empírico: sesión 13-mar, primera ejecución con estigmergia produjo 3+ referencias cruzadas entre modelos. Coste: $0.009.

### §1.5 Tres conceptos fundamentales ✅

#### INTELIGENCIA = qué ves (y qué no puedes ver)

Un sistema de percepción con objetos propios, operaciones propias y un punto ciego estructural. Hay 18 (hoy — evolucionable). Cada una es un "vocabulario de percepción" diferente.

9 categorías empíricas (derivadas de 34 chats de cartografía):

| # | Categoría | INTs | Qué comparten |
|---|-----------|------|---------------|
| 1 | Cuantitativa | 01 (Lógica), 02 (Computacional), 07 (Financiera) | Operan sobre lo medible |
| 2 | Sistémica | 03 (Estructural), 04 (Ecológica) | Mapean relaciones entre partes |
| 3 | Posicional | 05 (Política), 06 (Estratégica) | Ven actores, movimientos, poder |
| 4 | Interpretativa | 08 (Social), 09 (Lingüística), 12 (Narrativa) | Interpretan sentido humano |
| 5 | Corporal-Perceptual | 10 (Cinestésica), 15 (Estética) | Perciben forma encarnada |
| 6 | Espacial | 11 (Espacial) | Topología visual |
| 7 | Expansiva | 13 (Divergente), 14 (Prospectiva) | Abren espacio de opciones |
| 8 | Operativa | 16 (Constructiva) | Construye |
| 9 | Contemplativa-Existencial | 17 (Contemplativa), 18 (Existencial) | Significado último |

**6 irreducibles** (no sustituibles por combinación): INT-01, 02, 06, 08, 14, 16.

**Para el MVP:** se opera con las 6 irreducibles. Las otras 12 se activan bajo demanda por el Gestor cuando los datos muestran que aportan valor diferencial en un dominio específico. Esto NO es "reducir a 6" — es priorizar la activación.

Catálogo completo de firmas, preguntas y propiedades: META_RED_INTELIGENCIAS_CR0.md y OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md.

#### PENSAMIENTO = cómo procesas lo que percibes

17 tipos en tres familias:

**Interno (10):** percepción, causalidad, abstracción, síntesis, discernimiento, metacognición, consciencia epistemológica, auto-diagnóstico, convergencia, dialéctica.

**Lateral (7):** analogía, contrafactual, abducción, provocación, reencuadre, destrucción creativa, creación.

**Inter-álgebra (4):** fusión, composición, diferencial, lectura cruzada.

Los tipos de pensamiento hoy se activan implícitamente por las preguntas — la formulación de una pregunta determina qué tipo de procesamiento provoca. La selección explícita de pensamiento como parámetro configurable queda en §13 Horizonte.

#### MODO = para qué estás mirando

6 modos: ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR. No toda inteligencia opera bien en todos los modos. Los modos determinan la orientación del procesamiento: ANALIZAR descompone, PERCIBIR mapea, MOVER genera acción, SENTIR registra señales cualitativas, GENERAR abre opciones, ENMARCAR redefine el marco.

#### Combinatoria

```
Configuración de un paso = Inteligencia × Pensamiento × Modo
Espacio teórico: 18 × 17 × 6 = 1.836
Espacio útil estimado: ~180 (acotado por compatibilidad y gradientes)
```

MVP: el motor selecciona inteligencia + modo. Pensamiento se activa implícitamente por las preguntas. Selección explícita de los tres = v2+.

### §1.6 Relación con el Motor v3.3 ✅

| Pieza v3.3 | Dónde va |
|------------|----------|
| 7 primitivas sintácticas (Prisma Semántico) | Capa 0: Detector de Huecos — migran a OS |
| 4 isomorfismos | Las 4 lentes de INT-03 |
| Calculadora gaps id↔ir | Código puro dentro de INT-03 |
| Patrón de pipeline por capas | La meta-red de 6 pasos |
| Motor-orquestador (fan-out 7 primitivas) | Pipeline principal del Motor vN — migra a OS |

El v3.3 entero se encapsula como INT-03 dentro del motor semántico.

**Chief of Staff → ELIMINADO.** El Motor v3.3 + la Matriz 3L×7F reemplazan la funcionalidad diagnóstica del Chief. Se eliminan: pipeline dual superficial/profundo, 9 modos conversacionales, 24 agentes específicos. Se conservan como patrones: estigmergia, cola priorizada, persistencia, detección de contradicciones. Ver §8.3.

### §1.7 Tres niveles de estabilidad ✅

```
INVARIANTE (L0 — no se toca):
  3 Lentes:    Salud / Sentido / Continuidad
  7 Funciones: Conservar / Captar / Depurar / Distribuir / Frontera / Adaptar / Replicar
  8 Operaciones sintácticas (Marco Lingüístico)
  Álgebra del cálculo semántico
  → Esto es gramática. Se falsifica solo si se encuentra: 4ª lente irreducible,
    8ª función, 9ª operación.

ESTABLE PERO EVOLUCIONABLE (L1 — cambia con evidencia empírica):
  18 inteligencias (hoy) → puede ser 16 o 21 con datos reales
  17 tipos de pensamiento
  6 modos
  → Esto es vocabulario. Crece o se poda.

VARIABLE (L2 — cambia con cada ejecución):
  Preguntas dentro de cada celda
  Scores de efectividad
  Cobertura por dominio
  Asignación modelo→celda
  → Esto es contenido. Se llena, se mejora, se descarta.
```

---

## §2. LA MATRIZ — 3L × 7F × 18INT

### §2.1 Invariantes L0 (no se tocan)

**3 Lentes:**
- **Salud:** ¿Funciona?
- **Sentido:** ¿Tiene dirección?
- **Continuidad:** ¿Sobrevive más allá del sistema?

**7 Funciones:**
- **F1 Conservar:** mantener lo que funciona
- **F2 Captar:** incorporar recursos y señales
- **F3 Depurar:** eliminar lo que sobra o daña
- **F4 Distribuir:** asignar recursos donde hacen falta
- **F5 Frontera:** definir qué está dentro y qué fuera
- **F6 Adaptar:** cambiar en respuesta al entorno
- **F7 Replicar:** reproducir lo que funciona en otro contexto

**8 Operaciones sintácticas** (Marco Lingüístico) — ver §2.2.

Esto es gramática. Se falsifica solo si se encuentra: 4ª lente irreducible, 8ª función, 9ª operación.

Documentos fuente L0: L0_7_FUNCIONES_NUCLEARES.md, L0_5_MECANISMO_UNIVERSAL_VINCULACION.md, ALGEBRA_CALCULO_SEMANTICO_CR0.md.

### §2.2 Gramática generativa — Las 8 operaciones sintácticas (L0)

Cada pregunta se construye desde raíces de dominio × operaciones. Las raíces son invariantes (L0), las manifestaciones son derivadas (L2).

| # | Operación | Qué detecta | Ejemplo |
|---|-----------|-------------|---------|
| 1 | Modificación | Cualidades, grado | "¿Cuán frágil es la solvencia?" |
| 2 | Predicación | Estado o acción | "¿El sistema ES solvente?" / "¿ESTRUCTURA?" |
| 3 | Complementación | Instrumento, modo | "¿CON QUÉ observa?" |
| 4 | Transitividad | Objeto de la acción | "¿SOBRE QUÉ actúa?" |
| 5 | Subordinación | Causa, condición, creencias | "¿PORQUE qué?" / "¿Qué ASUME?" |
| 6 | Cuantificación | Alcance, límites | "¿CUÁNTO?" / "¿TODO o ALGUNO?" |
| 7 | Conexión | Tipo de acople | "¿Y/PERO/AUNQUE/PORQUE/SI/PARA?" |
| 8 | Transformación | Cambio de categoría | verbo→sustantivo, estado→cualidad |

**6 tipos de acople (Operación 7):**

| Conjunción | Tipo | Diagnóstico |
|------------|------|------------|
| Y | Sinergia | Salud |
| PERO | Tensión | Fricción activa |
| AUNQUE | Concesión | Grieta |
| PORQUE | Causalidad | Cadena causal |
| SI | Condicionalidad | Fragilidad |
| PARA | Finalidad | Dirección |

**Raíz pre-categorial × Operación — el mismo concepto se manifiesta según la operación aplicada:**
```
EQUILIBRI- × predicación_estado → "¿está en equilibrio?"
EQUILIBRI- × modificación       → "¿es equilibrado?"
EQUILIBRI- × predicación_acción → "¿equilibra?"
EQUILIBRI- × complementación    → "¿opera con equilibrio?"
EQUILIBRI- × subordinación      → "¿debe mantener equilibrio?"
```

**Tres niveles de preguntas:**
- **Nivel 1 — Fijas (hoy):** 18 redes escritas a mano. Funcionan. Se usan en MVP.
- **Nivel 2 — Generadas (v2):** 8 operaciones × raíces de dominio → preguntas para cualquier dominio sin cartografía manual.
- **Nivel 3 — Evolucionadas (meta-motor):** 17 pensamientos × preguntas → preguntas mejores.

**5 falacias aritméticas detectables:**

| Falacia | Error | Corrección |
|---------|-------|------------|
| Conducta → Valor | Predicación como Modificación | Pred → Sub_asertiva → Mod |
| Optimización sin finalidad | Transformación sin Sub final | Tr + Sub_final(PARA qué) |
| Creencia como Regla | Sub_asertiva como Sub_deóntica | Distinguir "creo" de "debe" |
| Cualidad como Función | Modificación como Predicación | "Es innovador" ≠ "innova" |
| Verbo sin objeto | Predicación sin Transitividad | Función declarada sin definir |

**Mapeo primitivas v3.3 ↔ operaciones Marco:**

| Primitiva v3.3 | Operación Marco |
|----------------|-----------------|
| Sustantivizar | Transformación → sustantivo |
| Adjetivar | Modificación |
| Adverbializar | Complementación |
| Verbo | Predicación |
| Preposicionar | Transitividad + Subordinación |
| Conjuntar | Conexión |
| Sujeto-predicado | Predicación + Cuantificación |

### §2.3 Inteligencias L1 (evolucionable con datos) ✅

18 inteligencias validadas en cartografía (54 análisis, 18 loop tests no-idempotentes 18/18, 8 propiedades algebraicas testeadas). Agrupadas en 9 categorías empíricas — ver tabla en §1.5.

### §2.4 Contenido variable L2

- Preguntas dentro de cada celda (hoy ~27 por inteligencia de cartografía)
- Scores de efectividad (gap_medio_cerrado por pregunta×modelo)
- Cobertura por dominio
- Asignación modelo→celda

La Matriz es un campo de gradientes, no un mapa estático. Cada celda tiene grado_actual, grado_objetivo y gap. Los gaps dirigen la ejecución.

### §2.5 Propiedades de la Matriz como campo activo

| Función | Cómo |
|---------|------|
| Campo de fuerza | Los gaps (objetivo − actual) generan la fuerza que dirige qué preguntas ejecutar, qué inteligencias activar, cuánta profundidad aplicar |
| Banco de preguntas con coordenadas | Cada pregunta ubicada en inteligencia × lente × función. El compilador no elige "preguntas de INT-07" — elige "preguntas que cubren Depurar×Sentido" y filtra por inteligencia |
| Base de datos de efectos | Cada ejecución registra qué celdas llenó y cuánto cerró el gap. Después de 1000 ejecuciones, el sistema sabe que INT-07 cierra Captar×Salud con efectividad 0.85 pero Replicar×Continuidad con 0.12 |
| Detector de puntos ciegos | Celdas donde ninguna inteligencia cierra el gap consistentemente = huecos reales de la Meta-Red. Verificable por datos, no por opinión |
| Esquema de inversión de documentos | El Reactor v2 ubica cada pregunta extraída de un paper en la Matriz. Las celdas vacías del paper son sus puntos ciegos |
| Verificador de cierre | La evaluación no es "¿se ejecutaron las preguntas?" sino "¿se cerró el gap?". Si después de ejecutar INT-07 sobre Depurar×Sentido el grado sigue igual, la pregunta falló |

**Dependencias entre lentes:**
- Salud sin Sentido = funciona pero sin dirección (frágil)
- Sentido sin Salud = visión sin capacidad de ejecutar
- Continuidad sin Sentido = replicar vacío

**Dependencias entre funciones:**
- F2 Captar sin F3 Depurar = acumular basura
- F4 Distribuir sin F5 Frontera = fugas
- F1 Conservar sin F6 Adaptar = rigidez
- F7 Replicar sin F5 Frontera = replicar ruido

### §2.6 Cada inteligencia cubre TODA la Matriz ✅

No es "INT-07 solo vive en Captar×Salud". Cada inteligencia tiene algo que decir sobre CADA una de las 21 celdas desde su lente particular. Ejemplo con INT-07 (Financiera):

```
Conservar × Salud:        ¿La estructura financiera aguanta las fuerzas actuales?
Conservar × Sentido:      ¿El modelo de negocio refleja la misión?
Conservar × Continuidad:  ¿El modelo financiero sobrevive si tú desapareces?
Captar × Salud:           ¿Los ingresos cubren los costes reales?
Captar × Sentido:         ¿Ganas dinero haciendo lo que importa?
Captar × Continuidad:     ¿La fuente de ingresos es replicable?
Depurar × Salud:          ¿Qué costes te están matando?
Depurar × Sentido:        ¿Qué gastos traicionan tu propósito?
Depurar × Continuidad:    ¿Qué estás reteniendo que impide escalar?
... (21 preguntas mínimo por inteligencia)
```

Esto produce el banco de preguntas real: 21 × 18 = **378 preguntas de coordenada** como mínimo. Con niveles profundo y experto, el banco crece a miles de preguntas, todas con coordenadas.

### §2.7 Propiedades algebraicas ✅

Confirmadas empíricamente en cartografía (34 chats, 8 tests):

| Propiedad | Resultado | Implicación |
|-----------|-----------|-------------|
| Conmutatividad fusión | Parcial (~25%, P01) | El orden de fusión afecta el framing |
| Asociatividad composición | Falsa (P03) | Dirección canónica: formal→humana. (A→B)→C ≠ A→(B→C) |
| Distributividad izquierda | ~70% factorizable (P04) | A→(B|C) ≈ (A→B)|(A→C) con ~30% pérdida emergente |
| Distributividad derecha | Falsa (P05) | (B|C)→A tiene valor irreducible. Nunca factorizar |
| No-idempotencia | 18/18 confirmada (P06) | 2ª pasada SIEMPRE añade valor |
| Saturación óptima | n=2 (P07) | 3ª pasada aporta 10-15%, no justifica coste |
| Clausura | output ∈ input (P08) | Cualquier output puede alimentar otra INT |
| Secuencia lineal vs agrupada | Lineal gana | No factorizar composiciones |

---

## §3. EL ÁLGEBRA — COMPILADOR DE PROMPTS

### §3.1 Qué hace

Toma un input (caso, pregunta, situación) + el campo de gradientes de la Matriz → compila un programa de preguntas ejecutable. El programa especifica: qué inteligencias activar, en qué orden, con qué operaciones, a qué modelo asignar cada paso.

### §3.2 Las 8 operaciones del álgebra ✅

Las operaciones algebraicas son operaciones de ensamblaje de redes de preguntas:

**1. Fusión ∫(A|B) — como suma:**
Dos o más inteligencias operan en paralelo sobre el MISMO input. Producen perspectivas independientes.
```
Prompt = [preguntas de A] + [preguntas de B] en paralelo
```
Conmutativa (sí), asociativa (sí), inverso (no — contribución marginal como sustituto).

**2. Composición A→B — como multiplicación:**
Una inteligencia opera sobre el output de otra. Produce mecanismo (nivel 3).
```
Prompt = [preguntas de A], luego [preguntas de B sobre output de A]
```
No conmutativa (A→B ≠ B→A siempre), asociativa en secuencia ((A→B)→C = A→(B→C) formalmente, pero empíricamente lineal gana). Distributiva por la izquierda (A→(B|C) ≈ (A→B)|(A→C) con ~30% pérdida). NO distributiva por la derecha ((B|C)→A tiene valor irreducible del cruce).

**3. Integración ∫ — como sumatorio Σ:**
Un agente mira TODAS las perspectivas de una fusión simultáneamente. Produce CRUCE: conexiones entre perspectivas que ninguna ve sola.
```
Prompt = [preguntas que emergen al cruzar las anteriores]
```
No es suma (eso es fusión). No es composición (no hay secuencia). Es reducción.

**4. Diferencial A-B — como resta:**
Lo que A ve que B NO puede ver. Mide el valor único de cada inteligencia.
```
Prompt = [preguntas que A tiene y B no puede tener]
```
No conmutativa, no asociativa, A-A = ∅, distributiva sobre fusión: A-(B|C) = (A-B) ∩ (A-C).

**5. Loop test A→A — recursión:**
Mismas preguntas sobre su propio output. No idempotente (18/18). Satura en n=2.
```
Prompt = [mismas preguntas sobre su propio output]
```

**6. Contribución marginal — sustituto del inverso:**
```
∫(A|B|C) vs ∫(A|B) → diferencia = contribución marginal de C
```
Si quitas un elemento de la fusión y la integración apenas cambia, ese elemento es redundante.

**7. Factorización izquierda — optimización de coste:**
```
SIN FACTORIZAR:                    FACTORIZADO:
  A→B      (2 calls)              A→(B|C|D)
  A→C      (2 calls)              = 1×A + 3 paralelo
  A→D      (2 calls)              = 4 calls (vs 6)
  = 6 calls total
```
Ahorra ~30% pero pierde ~30% de emergencia. Aceptable para ahorro, no para pares TOP.

**8. Cruce derecho — prohibido factorizar:**
```
(B|C)→A ≠ (B→A) | (C→A)
```
En (B|C)→A, el agente A ve la fusión junta y puede cruzar. En (B→A)|(C→A), ve cada una por separado. La circularidad del diagnóstico integrado solo aparece cuando operan juntas. ✅ Validado: ~30% de contenido emergente no recuperable por suma (09_DISTRIBUTIVIDAD_STARTUP_SAAS.md).

**Tabla resumen:**

```
OPERACIÓN     SÍMBOLO   CONMUT.  ASOC.  INVERSO    DISTRIB.
──────────────────────────────────────────────────────────────
Fusión          |       Sí       Sí     No*        —
Composición     →       No       Sí**   No         → sobre | (izq, ~70%)
Integración     ∫       N/A      N/A    No         N/A
Diferencial     -       No       No     A-A=∅      - sobre | (∩)
Loop            →→      N/A      N/A    N/A        N/A

*   Contribución marginal como sustituto medible
**  Empíricamente: secuencia lineal > reagrupada
```

### §3.3 Las 13 reglas del compilador ✅

Derivadas empíricamente de 34 chats de cartografía:

**Selección (Router):**
1. **Núcleo irreducible:** Siempre 1 cuantitativa (INT-01/02) + 1 humana (INT-08/17) + INT-16 constructiva.
2. **Máximo diferencial:** Priorizar eje cuantitativo-existencial (INT-01×08, INT-02×17, INT-07×17). Máxima complementariedad = máxima distancia perceptual entre categorías.
3. **Presupuesto:** 4-5 inteligencias por análisis. <3 = puntos ciegos. >6 = ruido.

**Orden:**
4. **Formal primero:** Inteligencia más formal/distante primero, más humana/cercana después.
5. **No reorganizar:** (A→B)→C supera A→(B→C). Secuencia lineal.
6. **Fusiones con cuidado:** Orden afecta framing. Primero la más alineada con el sujeto.

**Profundidad:**
7. **Loop test siempre:** 2 pasadas por defecto. La 2ª produce hallazgos genuinos 18/18.
8. **No tercera pasada:** n=3 no justifica coste (excepto calibración del método).

**Paralelización:**
9. **Fusiones ~70% factorizables:** A→(B|C) como (A→B)|(A→C) perdiendo ~30%.
10. **Cruce previo no factorizable:** (B|C)→A tiene valor irreducible.

**Patrones universales:**
11. **Marco binario universal:** En 3/3 casos, falsa dicotomía. Primera acción: INT-14 (ampliar) + INT-01 (filtrar).
12. **Conversación pendiente universal:** 16/18 inteligencias identifican conversación no tenida como prioridad.
13. **Outputs como inputs:** Cada pasada genera inputs de mayor densidad informativa para la siguiente.

---

## §4. EL ENJAMBRE — MODELOS Y MECANISMOS

### §4.1 Mapa de modelos (marzo 2026) ✅

**Mesa de producción validada (Exp 4.1):**

| Rol | Modelo | Por qué | Coste |
|-----|--------|---------|-------|
| Ejecutor principal | V3.2-chat | 97.9% cobertura con V3.1 (Exp 4.1) | ~$0.27/M in |
| Ejecutor complementario | V3.1 | 7 celdas donde es el mejor (Conservar, Frontera) | ~$0.27/M in |
| Razonador profundo | R1 | 100% cobertura mesa (Exp 4.1), Frontera×Sentido 3.1 | ~$0.55/M in |
| Sintetizador | Cogito 671B | #1 sin discusión (Exp 4.2): 3.6 conexiones/output, 47s | ~$0.50/M in |

**Modelos por roles adicionales:**

| Rol | Modelo | Evidencia |
|-----|--------|-----------|
| Motor pizarra | GPT-OSS | 119 contribuciones Exp 4.3 (mayor contribuidor) |
| Evaluador | Consenso panel (V3.2+V3.1+R1) | Sonnet descartada como referencia (0 aportes únicos Exp 4) |
| Coding agéntico | V3.2 + Kimi-Dev | V3.2: 80% test coding (4/5). Kimi-Dev: #1 SWE-bench patches |
| Fontanería barata | GPT-OSS 120B / MiMo-V2-Flash | $0.10-0.60/M. Clasificación, extracción, routing |

**Descartados de pipelines automatizados:**
- Opus: 0 aportes únicos, $75/M. Solo en chat manual ($0).
- Sonnet: 0 aportes únicos. No es referencia de evaluación.

**Leaderboard OS marzo 2026 (contexto de mercado):**

| Tier | Modelos | Params | Benchmark destacado |
|------|---------|--------|---------------------|
| S — Frontier | GLM-5, Kimi K2.5, MiniMax M2.5, V3.2, Step-3.5-Flash, Qwen 3.5 | 196B-1T | SWE 77-80, AIME 89-97, Arena top 5 |
| A — Excelentes | GLM-4.7, MiMo-V2-Flash, R1, Qwen3-235B | 235-671B | LiveCode 80-85, AIME 94-97 |
| B — Producción | GPT-OSS 120B, Mistral Large, Nemotron Ultra/Super | 49-675B | MATH 97 (Nemotron Super en 49B) |
| C — Nicho | GPT-OSS 20B, Maverick, Gemma 3, Nemotron Nano | 27-400B | Edge deployment, 1M ctx |
| Coding | Qwen3-Coder 480B, Qwen3-Coder-Next 80B, Kimi-Dev 72B | 72-480B | SOTA agentic coding, #1 SWE patches |

**No probados en nuestros tests (candidatos Exp futuros):**
- Kimi K2.5 (1T params, 32B activos, agent swarm nativo — ejecuta hasta 100 sub-agentes en paralelo, IFEval 94.0, HumanEval 99.0, MIT mod)
- Qwen 3.5 (397B, GPQA Diamond 88.4, IFEval 92.6, Apache 2.0 — la licencia más permisiva de Tier S)
- Step-3.5-Flash (AIME 97.3 — el más alto del leaderboard, 196B, LiveCode 86.4)
- GLM-5 (SWE 77.8, #1 Arena 1451, 744B/40B activos)
- MiMo-V2-Flash (309B/15B activos, $0.10/M in — 10x más barato que Tier A, supera V3.2 en SWE-bench)
- Nemotron Super 49B (MATH-500 97.4 — iguala R1 en 49B params, 1M ctx)

**Asignación modelo→celda (Exp 1 completo, 12 modelos):** ✅

Mejor modelo por celda según nivel medio más alto:

| | Conservar | Captar | Depurar | Distribuir | Frontera | Adaptar | Replicar |
|---|---------|--------|---------|---------|---------|---------|---------|
| **Salud** | V3.1 (2.8) | Maverick (2.1) | GPT-OSS (2.6) | Qwen3 Think (2.1) | V3.1 (2.6) | Kimi (2.7) | V3.1 (2.0) |
| **Sentido** | Cogito (2.3) | V3.2R (2.7) | GPT-OSS (2.9) | GPT-OSS (1.7) | **Cogito (3.4)** | V3.1 (2.4) | R1 (1.7) |
| **Continuidad** | V3.1 (2.4) | Qwen3 Think (2.2) | Qwen3.5 (2.3) | Qwen3 Think (2.2) | V3.1 (2.9) | V3.2R (2.8) | R1 (3.1) |

**Territorio por modelo (celdas donde es el mejor):**
- **DeepSeek V3.1:** 6 celdas — domina Conservar, Frontera×Salud/Continuidad
- **DeepSeek R1:** 2 celdas — Replicar×Continuidad (3.1), fuerte en Continuidad general
- **GPT-OSS 120B:** 3 celdas — domina Depurar (2.52 media, mejor de todos), Distribuir×Sentido
- **Cogito 671B:** 2 celdas — **Frontera×Sentido (3.4)** = score más alto de cualquier celda de Sentido
- **V3.2-Reasoner:** 2 celdas — Captar×Sentido (2.7), Adaptar×Continuidad (2.8)
- **Kimi K2.5:** 1 celda — Adaptar×Salud (2.7)
- **Qwen3 Thinking:** 3 celdas — Distribuir×Salud/Continuidad, Captar×Continuidad
- **Maverick:** 1 celda — Captar×Salud (2.1)
- **Claude:** 0 celdas donde sea el mejor (10º de 12)
- **V3.2-chat, Qwen3.5, 70B:** 0 celdas donde sean el mejor

Se recalcula con primer lote de ejecuciones reales. Exp 4.1 actualizó mesa a V3.2+V3.1+R1.

**Hallazgos por función:**
- **Frontera** es donde más brilla el enjambre OS: V3.1 y R1 alcanzan 2.7-3.1 vs Claude 1.93
- **Depurar** es el dominio de GPT-OSS (2.52) — detecta lo que filtra mal mejor que nadie
- **Adaptar** es donde Claude aún resiste (2.33) — pero V3.1 (2.37) ya lo alcanza
- **Distribuir** es la función más débil para todos — ningún modelo supera 2.0 de media
- **Sentido** es la lente más débil para todos excepto GPT-OSS (2.19)

### §4.2 Sesgos por modelo ✅ (Exp 4 + Exp 10)

| Modelo | Sesgo | Dato | Implicación |
|--------|-------|------|-------------|
| Qwen3-235B | Inflador severo | +0.93 puntos vs evaluación externa (Exp 4.3). +0.84 en R1 individual. 17 inflaciones de 31 únicos | Con especialización BAJA rendimiento (-0.31 en Exp 4.1). No es "cerebro" — es inflador |
| GPT-OSS | Deflator leve | -0.45 vs media (Exp 4 R1) | Pero mayor contribuidor en pizarra (119). Roles diferentes = sesgos diferentes |
| R1 | Conservador | Scores estables, baja varianza | Fiable como evaluador. 100% cobertura mesa |
| V3.2-chat | Neutro | +0.16 con especialización (Exp 4.1) | Generalista sólido, mejora con foco |
| Cogito | Neutro-alto | 6 inflaciones = 0 netos en Exp 4. Pero 3.6 conexiones/output como sintetizador | Inflador como evaluador, sintetizador genuino |
| Kimi | Deteriora con foco | -0.48 con especialización (Exp 4.1). Inerte en R2 (formato/timeout) | No usar en mesa redonda |
| Modelos con poco contexto | Más destructivos | Exp 10: R1, Step, Nemotron con ~45k tokens recomiendan eliminar componentes validados. GPT-OSS con 225k tokens es más conservador | "Dunning-Kruger del enjambre": menos ves, más seguro estás de que lo que no ves no importa |

**Corrección Principio 33:** Ponderar votos por nivel de contexto en futuros enjambres de diseño. Un modelo con 45k tokens no anula evidencia de 34 chats empíricos.

### §4.3 Los 5 mecanismos multi-modelo ✅

Validados en Exp 4 completo (4 sub-experimentos + evaluación externa):

**1. Evaluación individual en paralelo (Exp 4 R1)**
- N modelos evalúan independientemente el mismo input
- Produce: scores con varianza (std 0.71-0.94), detección de sesgos, mapa de infladores/defladores, correlaciones entre evaluadores (Sonnet↔Qwen3: 0.605, R1↔V3.2R: 0.642)
- No produce: conexiones, puntos ciegos, síntesis
- Datos: media global 1.71, solo 7/105 celdas con consenso mayoritario (≥6 dan 3+)
- Coste: ~$0.50-1.00 (12 modelos × 5 outputs)
- Uso: screening, calibración de modelos nuevos. Es el termómetro, no el tratamiento

**2. Mesa redonda con enriquecimiento (Exp 4 R2)**
- Tras R1, cada modelo ve las evaluaciones de los demás y reevalúa
- Produce: convergencia 7→70 celdas consenso (10x), +16 celdas emergentes que no existían en R1, reducción de varianza. Media 3.27 (vs 1.71 R1), 93/105 celdas 3+
- Atención: 77% convergencias hacia donde Qwen3 apuntaba en R1 — efecto líder parcial. Sonnet predice R2 mejor que nadie (ρ=0.656)
- Coste: ~$1-2

**3. Mesa especializada (Exp 4.1)**
- Misma mesa, cada modelo recibe prompt afinado a su zona fuerte
- Produce: +0.55 media en zona de foco, -0.14 fuera de foco. Delta global +0.10. Cambia mesa mínima: V3.2-chat + V3.1 = 97.9% (vs Qwen3 + GPT-OSS = 94.6% con genérico)
- Modelos que mejoran: V3.2R (+0.50), R1 (+0.43), MiniMax (+0.28), V3.1 (+0.19), V3.2-chat (+0.16)
- Modelos que empeoran con especialización: Kimi (-0.48), Opus (-0.40), Qwen3 (-0.31), GLM (-0.27). Los infladores genéricos pierden ventaja con prompt específico
- Coste: igual (solo cambian prompts). Usar SIEMPRE sobre genérica

**4. Sintetizador (Exp 4.2)**
- Un modelo recibe TODAS las evaluaciones y produce output integrado
- Cogito: 3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s, 100% celdas igualan max mecánico
- Ranking sintetizadores:

| # | Modelo | Conexiones/output | Hallazgos no-genéricos | Tiempo |
|---|--------|-------------------|------------------------|--------|
| 1 | **Cogito-671b** | 3.6 | 5/5 | 47s |
| 2 | R1 | 3.0 | 5/5 | 55s |
| 3 | Qwen3-235b | 2.2 | 3/5 | 137s |
| 4 | V3.2-chat | 2.0 | 2/5 | 121s |
| ✗ | GLM-5 | — | parse fail 0/5 | — |
| ✗ | MiniMax M2.5 | — | parse fail 0/5 | — |

- Coste: $0.03-0.10 adicional. Usar SIEMPRE como paso final de cualquier mesa

**5. Mente distribuida / Pizarra (Exp 4.3)**
- Pizarra compartida, micro-rondas, convergencia emergente
- Produce: 425 conexiones + 239 puntos ciegos (valor exclusivo). 94/105 celdas 3+ (evaluación externa)
- Perfiles en la pizarra:

| Modelo | Contribuciones | Conexiones | P.Ciegos | Perfil |
|--------|---------------|------------|----------|--------|
| GPT-OSS | 119 | 77 | 46 | Motor principal |
| MiniMax M2.5 | 75 | 55 | 45 | Segundo motor |
| Qwen3-235b | 63 | 48 | 25 | Tercer contribuidor |
| V3.2-chat | 56 | 52 | 28 | Conector fuerte |
| V3.1 | 52 | 45 | 22 | Contribuidor sólido |
| R1 | 44 | 30 | 12 | Contribuidor |
| Cogito | 31 | 29 | 22 | Detector de huecos |
| Opus | 33 | 34 | 8 | Conector (caro: $75/M) |
| GLM-4.7 | 20 | 8 | 2 | Marginal |

- Convergencia: 3/5 outputs en 4-5 rondas. 2/5 al máximo sin converger
- Auto-tracking infla +0.93 puntos. Evaluación externa: media 3.06 (vs auto 3.99)
- NO bate a mesa redonda en scores (3.06 vs 3.27). SÍ produce valor exclusivo (conexiones, puntos ciegos)
- Coste: $2-5 por output. Uso: solo Tier 4-5 (batch nocturno, cartografía)

**Comparación agregada cross-experimento (evaluación externa):**

| Método | Media | 3+/105 celdas | Conexiones | Evaluador |
|--------|-------|--------|------------|-----------|
| Exp 4 R1 max mecánico | 2.89 | 77 | 0 | 12 modelos individual |
| Exp 4 R2 mesa redonda | 3.27 | 93 | 0 | 12 modelos post-R2 |
| Exp 4.1 mesa especializada | ~3.30 | 95 | 0 | 12 modelos prompts foco |
| Exp 4.3 mente distribuida (ext) | 3.06 | 94 | 425 | Claude externo |
| Exp 4.3 auto-tracking | 3.99 | 105 | 425 | Auto (inflado +0.93) |

**Mesa mínima por mecanismo:**

| Mecanismo | Mesa mínima | Cobertura |
|-----------|------------|-----------|
| Genérico (Exp 4) | Qwen3 + GPT-OSS | 94.6% |
| Especializado (Exp 4.1) | V3.2-chat + V3.1 | 97.9% |
| Especializado completa | V3.2-chat + V3.1 + R1 | 100% |
| Pizarra recomendada | 7 modelos (GPT-OSS→Cogito) | 76% contribuciones |

**Composiciones operativas por tier:**

Tier 2 (respuesta): 1 modelo: V3.2-chat (89.5% cobertura individual). Sin mesa, respuesta directa.

Tier 3 (análisis): Mesa especializada 1 ronda (sin R2). V3.2-chat + V3.1 + R1 = 100% cobertura. + Cogito sintetiza (47s extra). Total: 4 llamadas, ~$0.30, ~3min.

Tier 4 (profundo): Paso 1: pizarra distribuida (7 modelos, ~5 rondas) → contenido rico. Paso 2: Cogito sintetiza → hallazgo central + meta-patrones. Paso 3: panel evaluador externo (V3.2+V3.1+R1 especializados) → scores calibrados. Total: ~40-50 llamadas, ~$2-3, ~45min batch.

Tier 5 (cartografía): Pizarra completa (11 modelos hasta convergencia) → mesa especializada R1+R2 → Cogito sintetiza → loop detección puntos ciegos → nueva ronda. Total: ~100+ llamadas, ~$5-10, ~2-4h batch.

**Hallazgos metodológicos clave:**
- Auto-evaluación infla ~1 punto. Siempre usar evaluación externa para scores fiables.
- La especialización redistribuye valor pero no sube el total significativamente (+2 celdas). Cambia QUIÉN es útil.
- GPT-OSS invierte su rol según mecanismo: máximo deflactor en evaluación (-0.45), máximo contribuidor en pizarra (119). El rol del modelo depende del mecanismo, no es fijo.

### §4.4 Los 5 tiers de enjambre ✅ (Principio 31)

**Rápido y profundo no existe. 5 velocidades para 5 contextos.**

```
TIER 1 — REFLEJO
  Latencia:  milisegundos     Coste:  $0
  Enjambre:  ninguno — código puro
  Mecanismo: Lookup en Matriz precompilada
  Cuándo:    "Este patrón lo he visto 47 veces"

TIER 2 — RESPUESTA
  Latencia:  5-15 segundos    Coste:  $0.01-0.05
  Enjambre:  1 modelo OS barato (GPT-OSS / MiMo)
  Mecanismo: Modelo + programa compilado por Gestor
  Cuándo:    Interacción normal de conversación

TIER 3 — ANÁLISIS
  Latencia:  1-5 minutos      Coste:  $0.10-0.50
  Enjambre:  3-5 modelos paralelo (V3.2+V3.1+R1)
  Mecanismo: Mini-mesa rápida (1 ronda, sin enriquecimiento)
  Cuándo:    Decisión importante, usuario puede esperar

TIER 4 — PROFUNDO
  Latencia:  30-60 minutos    Coste:  $0.50-2.00
  Enjambre:  Mente distribuida (7+ modelos, pizarra, micro-rondas)
  Mecanismo: Pizarra → Cogito sintetiza → panel evaluador
  Cuándo:    Batch nocturno. Briefing matutino. Análisis semanal.

TIER 5 — CARTOGRAFÍA
  Latencia:  horas a días     Coste:  $5-20
  Enjambre:  Exploración completa (18 INTs × composiciones × loops)
  Mecanismo: Protocolo exploración + mente distribuida
  Cuándo:    Onboarding cliente nuevo. Auditoría anual.
```

Decisión de tier:
```
¿Respuesta precompilada en Matriz? → TIER 1
¿Conversación normal?              → TIER 2
¿Análisis o decisión?              → TIER 3
¿Proceso batch (nadie espera)?     → TIER 4
¿Dominio nuevo?                    → TIER 5
```

### §4.5 Protocolo de exploración (5 tiers internos) 🔧

```
Tier 1 (siempre):  18 INTs individuales sobre el caso
Tier 2 (siempre):  6 irreducibles en composición = 30 pares (A→B y B→A)
Tier 3 (siempre):  TOP 10 fusiones derivadas de Cartografía
Tier 4 (siempre):  Loop test sobre top 3 resultados de Tiers 1-3
Tier 5 (muestreo): 10% de combinaciones restantes seleccionadas aleatoriamente

Total: ~70-80 ejecuciones por caso
Coste: ~$0.08 OS ejecutores + ~$0.02 evaluador OS = ~$0.10 por caso completo
```

Los tiers NO son fijos — son hipótesis. El enjambre meta-protocolo los reconfigura con datos (cada 100 ejecuciones: ¿qué tiers generan más información? ¿El muestreo aleatorio encuentra cosas que Tiers 1-3 no?).

### §4.6 Dos fases de operación ✅

**Fase A: Exploración (llena la Matriz)**
```
Caso nuevo entra → Motor OS ejecuta protocolo completo (§4.5)
→ Evaluador mide: ¿qué gaps cerró cada operación?
→ Datapoints de efectividad → DB → Gestor
→ Tabla configuraciones_efectivas se llena
```

**Fase B: Lookup (usa la Matriz llena)**
```
Caso nuevo entra → Detector de huecos → patrón de gaps
→ Gestor provee programa compilado: "Este patrón lo he visto 47 veces.
   INT-01→INT-14 fusión con V3.2 cierra 82% en Salud×Captar."
→ Ejecuta SOLO la configuración ganadora
→ Respuesta en segundos, no minutos
```

**Transición A→B:** por celda, no global. Criterio:
```
SI (n_ejecuciones_patron > 30 AND tasa_cierre_config_ganadora > 0.60):
  → Fase B para esta celda (lookup directo via Gestor)
SINO:
  → Fase A (seguir explorando)
```

---

## §5. EL PIPELINE — MOTOR vN

### §5.1 Arquitectura 🔧

El Motor mira hacia fuera. Recibe caso → ejecuta Matriz → devuelve resultado → registra efectividad.

7 pasos (simplificable a 4 para Tier 1-2):

```
PASO 1 — DETECTOR DE HUECOS           ~200ms | $0 | código puro
  Input: caso en lenguaje natural
  7 primitivas + 8 operaciones sintácticas
  Output: campo de gradientes (qué funciones×lentes tienen gap)
  Detecta: falacias aritméticas en el input

PASO 2 — ROUTER                        ~500ms-3s | ~$0.001 | reglas + modelo OS
  Input: campo de gradientes
  Para cada celda con gap > 0.3:
    ¿Qué INT cierra ESTE gap con más efectividad?
  Output: selección de INTs + orden + modelos asignados
  Usa: 13 reglas compilador + asignación modelo→celda del Gestor
  Tier 1-2: reglas heurísticas. Tier 3+: modelo OS ligero

PASO 3 — COMPOSITOR                    ~200ms | $0 | NetworkX/código puro
  Input: INTs seleccionadas + orden
  Output: prompt compilado (red de preguntas)
  Álgebra ensambla red: fusión, composición, etc.
  13 reglas como restricciones duras
  Dependencias lentes/funciones informan secuencia

PASO 4 — EJECUTOR                      30-120s | $0.001-0.003/modelo OS
  Input: prompt compilado
  Output: respuestas por modelo×inteligencia
  1 modelo (Tier 2), 3-5 (Tier 3), 7+ (Tier 4)
  Modelo OS asignado por Gestor según celda
  Multi-modelo en paralelo si celda requiere complementariedad

PASO 5 — EVALUADOR                     ~1-3s | ~$0.01
  Input: respuestas + gaps originales
  Re-evalúa campo de gradientes POST-ejecución
  Output: scores de cierre de gap, falacias detectadas
  Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  Max 2 re-intentos por celda
  Panel V3.2+V3.1+R1 o Cogito (no Sonnet)

PASO 6 — INTEGRADOR                    10-20s | ~$0.05
  Input: respuestas evaluadas
  Output: narrativa + JSON estructurado
  Cogito como sintetizador (#1, 3.6 conexiones/output)

PASO 7 — REGISTRADOR                   ~100ms | $0 | código puro
  Input: todo lo anterior
  Output: datapoint en datapoints_efectividad → alimenta Gestor
  Registra gap_cerrado por pregunta×modelo con coordenadas

TOTAL: ~$0.10-0.35 (OS-first) | ~40-150s
```

Simplificación: Tier 1 = paso 1 (lookup). Tier 2 = pasos 1-4-7. Tier 3 = 1-2-3-4-5-7. Tier 4-5 = pipeline completo con rondas.

### §5.2 4 modos (configuraciones del mismo pipeline)

| Modo | Campo | INTs típicas | Latencia | Coste |
|------|-------|-------------|----------|-------|
| Análisis | 21 celdas completo | 3-5 por gradientes | 40-150s | $0.50-1.50 |
| Conversación | Solo celdas que el turno toca | 1-2 rápido | 5-20s | $0.05-0.15 |
| Generación | Orientado al output deseado | Creativas: 14,15,09,12 | 30-90s | $0.30-0.80 |
| Confrontación | Busca gaps que la propuesta ignora | Frontera: 17,18,06 | 30-90s | $0.30-0.80 |

### §5.3 Auto-diagnóstico — La Matriz sobre sí misma ✅

El sistema usa la misma Matriz 3L×7F para verse a sí mismo. Las celdas del sistema tienen grado, objetivo y gap — igual que las del usuario. La mejora continua se dirige por gaps, no por intuición.

Convergencia: cuando una celda del usuario está débil Y la celda equivalente del sistema también → doble riesgo: "no puedo cubrir un gap del usuario que es mi propio gap".

### §5.4 Estado de implementación

| Componente | Estado |
|------------|--------|
| Motor Semántico v1 MVP en fly.io | ✅ 3 casos validados, 8.5-9.5/10 |
| Detector de huecos | 🔧 Diseñado |
| Router | ✅ Parcial (Sonnet fallback) |
| Compositor | ✅ NetworkX + 13 reglas |
| Ejecutor multi-modelo | ✅ 6+ modelos OS paralelo |
| Evaluador consenso | ✅ Panel > Sonnet individual (Exp 4) |
| Integrador Cogito | ✅ #1 sin discusión (Exp 4.2) |
| Registrador | 🔧 Schema diseñado |

---

## §6. EL GESTOR DE LA MATRIZ

### §6.1 Qué es 🔧

El sistema que mira hacia dentro. Mantiene, poda, mejora y recompila la Matriz. Es el algoritmo de entrenamiento de la red neuronal.

Sin Gestor = forward pass con pesos fijos (pipeline estático). Con Gestor = cada ejecución ajusta topología (sistema que aprende).

**Estado: DISEÑADO, POR IMPLEMENTAR. Cuello de botella principal. Prioridad #1 del roadmap.**

```
                    GESTOR DE LA MATRIZ
                    (loop lento, mira hacia dentro)
                           │
                    Mantiene, poda, mejora, compila
                    la Matriz 3L×7F×18INT
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         Motor vN    Exocortex     Exocortex
         (casos      Pilates       Clínica
          nuevos)    (movimiento)  (salud oral)
```

Cada consumidor recibe un **programa de preguntas compilado** por el Gestor, no la Matriz entera. El Gestor sabe qué preguntas funcionan para qué contexto porque tiene los datos de efectividad de TODOS los consumidores.

### §6.2 Pipeline del Gestor (10 pasos) 🔧

```
INPUTS (continuos):
  ← Datapoints de efectividad del Motor vN
  ← Datapoints de efectividad de cada Exocortex
  ← Preguntas nuevas de Reactores v1/v2/v3/v4
  ← Resultados del Meta-motor

PROCESO (loop lento, cada 50 ejecuciones o cada 24h):
  -- Sobre la Matriz --
  1. Actualizar scores de efectividad por pregunta×modelo×celda
  2. Podar preguntas muertas (n>10, tasa<0.05)
  3. Promover preguntas potentes (n>10, tasa>0.40)
  4. Detectar complementariedad entre modelos por celda
  5. Detectar transferencia cross-dominio
  6. Recalcular asignación modelo→celda (ranking por tasa_media_cierre)
  7. Recompilar programas de preguntas por consumidor
  -- Sobre la Knowledge Base (Fase 2+) --
  8. Marcar chunks obsoletos (documento reemplazado → relevancia=0.1)
  9. Detectar contradicciones entre scopes (chief dice X, sistema dice Y)
  10. Expirar chunks L2 con caduca_at < now()
  -- Check de escala --
  SI total_tokens_contexto > 50000: alerta("Migrar a pgvector")

OUTPUTS (bajo demanda):
  → Programa compilado para Motor vN dado caso + patrón de gaps
  → Programa compilado para Exocortex X dado contexto de dominio
  → Informe de salud de la Matriz (propiocepción)
  → Log de acciones en log_gestor
```

### §6.3 Tres mecanismos de aprendizaje 🔧

**1. Selección natural de preguntas:**
```
SI n_ejecuciones > 10 AND tasa_media_cierre < 0.05:
  → Pregunta inefectiva. Marca "poda_candidata". Solo en muestreo Tier 5.
SI n_ejecuciones > 10 AND tasa_media_cierre > 0.40:
  → Pregunta potente. Priorizar en Tier 1.
```

**2. Asignación modelo→celda:**
Ranking por tasa_media_cierre. Datos iniciales de Exp multi-modelo (09-mar) — ver tabla completa §4.1. Se recalcula con primer lote de ejecuciones reales. En Fase B: modelo ganador. En Fase A: todos (para recalibrar).

**3. Complementariedad modelo×modelo:**
```
Para cada celda:
  ¿Modelo A cierra cuando B no cierra (y viceversa)?
  Si sí: esa celda necesita AMBOS (enjambre, no sustitución)
  Métrica: complementariedad(A,B,celda) =
    P(A cierra | B no cierra) × P(B cierra | A no cierra)
```

### §6.4 Lo que compila por consumidor 🔧

El Gestor NO expone la Matriz. Compila un "programa" por consumidor:

**Para el Motor vN (diagnóstico general):**
```
"Para un caso tipo startup con gaps en Captar×Salud y Frontera×Sentido,
usa estas 12 preguntas con V3.2, estas 8 con R1.
Fusiona outputs en Captar×Salud porque son complementarios ahí."
```

**Para un Exocortex (dominio específico):**
```
"Para una clienta con dolor lumbar crónico de 3 meses,
las preguntas efectivas son estas 15 de INT-04 (Cinestésica)
+ estas 6 de INT-03 (Espacial) en composición.
Modelo: V3.1 (mejor en Adaptar×Salud para movimiento)."
```

Principio 23: el Gestor compila, los consumidores ejecutan. Ningún consumidor selecciona preguntas por su cuenta.

### §6.5 Registro por ejecución (feedback loop) 🔧

Cada vez que CUALQUIER consumidor ejecuta una pregunta:

```json
{
  "pregunta_id":        "INT07_F2_L1_003",
  "modelo":             "deepseek-v3.2-chat",
  "caso_id":            "startup_saas_001",
  "consumidor":         "motor_vn",
  "celda_objetivo":     "Captar×Salud",
  "gap_pre":            0.72,
  "gap_post":           0.35,
  "gap_cerrado":        0.37,
  "tasa_cierre":        0.514,
  "operacion":          "individual",
  "timestamp":          "2026-03-09T..."
}
```

### §6.6 Schema DB completo — fly.io Postgres 🔧

23 tablas + 1 vista materializada. Cada una con propósito concreto. Organización por grupo funcional:

```
fly.io Postgres
│
├── MATRIZ (el producto) ─────────────── 7 tablas
├── GESTOR (el cerebro) ─────────────── 3 tablas
├── REACTORES (la fábrica) ──────────── 1 tabla
├── CONFIGURACIÓN (los dials) ───────── 2 tablas
├── TELEMETRÍA (los sensores) ───────── 3 tablas
├── MEJORA CONTINUA (sistema inmune) ── 3 tablas
├── CONSUMIDORES (los clientes) ─────── 3 tablas
├── COMUNICACIÓN (sistema nervioso) ─── 1 tabla
├── CONTEXTO (memoria — Fase 2+) ────── 1 tabla (cuando escale)
└── VISTA MATERIALIZADA ─────────────── 1 vista
```

#### GRUPO 1 — MATRIZ (el producto)

```sql
CREATE TABLE inteligencias (
    id TEXT PRIMARY KEY,              -- "INT-07"
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    firma TEXT NOT NULL,
    punto_ciego TEXT NOT NULL,
    objetos_exclusivos TEXT[],
    raices_dominio TEXT[],
    preguntas JSONB NOT NULL,
    modos_naturales TEXT[],
    modos_forzados TEXT[]
);

CREATE TABLE preguntas_matriz (
    id TEXT PRIMARY KEY,              -- "INT07_F2_L1_003"
    inteligencia TEXT NOT NULL,
    lente TEXT NOT NULL,
    funcion TEXT NOT NULL,
    pensamiento TEXT,
    modo TEXT,
    nivel TEXT DEFAULT 'base',        -- base / profunda / experta
    sub_dominio TEXT,
    texto TEXT NOT NULL,
    fuente TEXT,                       -- cartografia / reactor_v1 / reactor_v2 / reactor_v4
    score_efectividad FLOAT,
    gap_medio_cerrado FLOAT
);

CREATE TABLE aristas_grafo (
    id SERIAL PRIMARY KEY,
    origen TEXT REFERENCES inteligencias(id),
    destino TEXT REFERENCES inteligencias(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('composicion','fusion','diferencial')),
    peso FLOAT NOT NULL,
    direccion_optima TEXT,
    hallazgo_emergente TEXT,
    UNIQUE(origen, destino, tipo)
);

CREATE TABLE operaciones_sintacticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,       -- 'modificacion', 'predicacion', etc.
    input_tipo TEXT NOT NULL,
    output_tipo TEXT NOT NULL,
    propiedad_clave TEXT NOT NULL,
    pregunta_detectora TEXT NOT NULL,
    propiedades_algebraicas JSONB
);

CREATE TABLE datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pregunta_id TEXT NOT NULL,
    modelo TEXT NOT NULL,
    caso_id TEXT NOT NULL,
    consumidor TEXT NOT NULL,
    celda_objetivo TEXT NOT NULL,
    gap_pre FLOAT NOT NULL,
    gap_post FLOAT NOT NULL,
    gap_cerrado FLOAT GENERATED ALWAYS AS (gap_pre - gap_post) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre > 0 THEN (gap_pre - gap_post) / gap_pre ELSE 0 END
    ) STORED,
    operacion TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE efectos_matriz (
    id SERIAL PRIMARY KEY,
    ejecucion_id TEXT NOT NULL,
    inteligencia TEXT NOT NULL,
    lente TEXT NOT NULL,
    funcion TEXT NOT NULL,
    hallazgo TEXT,
    grado_antes FLOAT,
    grado_despues FLOAT,
    gap_cerrado FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);
```

#### GRUPO 2 — GESTOR (el cerebro)

```sql
CREATE TABLE campo_gradientes (
    ejecucion_id TEXT PRIMARY KEY,
    input_texto TEXT,
    gradientes JSONB NOT NULL,         -- {celda: {actual, objetivo, gap}}
    dependencias_lentes JSONB,
    dependencias_funciones JSONB,
    top_gaps JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Caché de programas compilados por patrón de gaps
-- Sin esta tabla, cada ejecución recompila desde cero
-- Es la diferencia entre Fase A (explorar) y Fase B (lookup)
CREATE TABLE programas_compilados (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,           -- "motor_vn" | "exocortex:pilates"
    patron_gaps JSONB NOT NULL,         -- {celda: gap} que triggereó esta compilación
    programa JSONB NOT NULL,            -- {pasos: [{int, preguntas, modelo, orden}]}
    version INT NOT NULL,
    tasa_cierre_media FLOAT,            -- rendimiento acumulado
    n_ejecuciones INT DEFAULT 0,
    activo BOOLEAN DEFAULT true,
    compilado_at TIMESTAMPTZ DEFAULT NOW(),
    reemplazado_at TIMESTAMPTZ          -- null si es el vigente
);

-- Campo de gradientes ACUMULADO por consumidor/usuario
-- Evoluciona con el tiempo: primera vez gaps por todo,
-- después de 10 sesiones solo 3 celdas débiles
CREATE TABLE perfil_gradientes (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,           -- "exocortex:pilates"
    usuario_id TEXT,                    -- si múltiples usuarios por exocortex
    gradientes JSONB NOT NULL,          -- {celda: {actual, objetivo, gap, n_ejecuciones}}
    version INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Query más valiosa del sistema:**
```sql
-- "Dame el mejor programa para este patrón de gaps"
SELECT programa, tasa_cierre_media, n_ejecuciones
FROM programas_compilados
WHERE consumidor = $1 AND activo = true
  AND patron_gaps @> $2
ORDER BY tasa_cierre_media DESC LIMIT 1;

-- Si n_ejecuciones > 30 AND tasa > 0.60 → Fase B (lookup, ms)
-- Si no → Fase A (explorar)
```

#### GRUPO 3 — REACTORES (la fábrica)

```sql
-- Datos crudos de operación antes de convertirse en preguntas
-- El Reactor v4 observa → escribe aquí → genera preguntas → INSERT en preguntas_matriz
CREATE TABLE observaciones_reactor (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,           -- "exocortex:pilates"
    tipo_dato TEXT NOT NULL,            -- "cancelacion" | "reserva" | "review" | "transaccion"
    dato JSONB NOT NULL,                -- {fecha, cliente, sesion, motivo...}
    celdas_detectadas TEXT[],           -- ["Captar×Salud", "Depurar×Salud"]
    celdas_gap TEXT[],                  -- celdas que DEBERÍA tocar pero no toca
    pregunta_generada_id TEXT,          -- FK a preguntas_matriz si generó pregunta
    procesado BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### GRUPO 4 — CONFIGURACIÓN (los dials)

```sql
CREATE TABLE config_modelos (
    id SERIAL PRIMARY KEY,
    rol TEXT NOT NULL,                  -- "ejecutor" | "sintetizador" | "evaluador" | "coder"
    modelo TEXT NOT NULL,               -- "deepseek-v3.2-chat"
    provider TEXT NOT NULL,             -- "openrouter" | "deepseek" | "together"
    tier_min INT DEFAULT 1,
    tier_max INT DEFAULT 5,
    coste_input_per_m FLOAT,
    coste_output_per_m FLOAT,
    activo BOOLEAN DEFAULT true,
    notas TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE config_enjambre (
    id SERIAL PRIMARY KEY,
    tier INT NOT NULL,                  -- 1-5
    modelos TEXT[] NOT NULL,            -- ["v3.2-chat", "v3.1", "r1"]
    mecanismo TEXT NOT NULL,            -- "lookup" | "individual" | "mesa" | "pizarra"
    rondas INT DEFAULT 1,
    sintetizador TEXT,                  -- "cogito" | null
    evaluador_externo BOOLEAN DEFAULT false,
    coste_estimado FLOAT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### GRUPO 5 — TELEMETRÍA (los sensores)

```sql
CREATE TABLE ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    huecos_detectados JSONB,
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,
    feedback_usuario JSONB
);

CREATE TABLE metricas (
    id SERIAL PRIMARY KEY,
    componente TEXT NOT NULL,           -- "motor_vn" | "gestor" | "reactor_v4"
    evento TEXT NOT NULL,               -- "ejecucion" | "compilacion" | "poda"
    datos JSONB NOT NULL,               -- {latencia_ms, tokens_in, tokens_out, coste_usd, error...}
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE señales (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,                 -- "alerta" | "umbral" | "anomalia"
    severidad TEXT NOT NULL,            -- "info" | "warning" | "critical"
    mensaje TEXT NOT NULL,
    datos JSONB,
    resuelta BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### GRUPO 6 — MEJORA CONTINUA (sistema inmune)

```sql
CREATE TABLE cola_mejoras (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,                 -- "fontaneria" | "arquitectural" | "auto-evolucion"
    descripcion TEXT NOT NULL,
    prioridad INT DEFAULT 5,
    estado TEXT DEFAULT 'pendiente',    -- "pendiente" | "en_curso" | "cr1" | "cerrada"
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE propuestas_mejora (
    id SERIAL PRIMARY KEY,
    cola_mejora_id INT REFERENCES cola_mejoras(id),
    propuesta JSONB NOT NULL,           -- {cambios, justificacion, impacto_estimado}
    nivel TEXT NOT NULL,                -- "auto" (fontanería) | "cr1" (arquitectural)
    aprobada BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE reglas_deteccion (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    condicion JSONB NOT NULL,           -- {metrica, operador, umbral}
    accion TEXT NOT NULL,               -- "crear_mejora" | "señal" | "escalar"
    activa BOOLEAN DEFAULT true
);
```

#### GRUPO 7 — CONSUMIDORES (los clientes)

```sql
CREATE TABLE exocortex_estado (
    id TEXT PRIMARY KEY,                -- "exocortex:pilates"
    nombre TEXT NOT NULL,
    dominio TEXT NOT NULL,              -- "movimiento" | "salud_oral" | "restauracion"
    config JSONB,                       -- config específica del dominio
    programa_activo_id INT,             -- FK a programas_compilados
    activo BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE perfiles_usuario (
    id SERIAL PRIMARY KEY,
    consumidor TEXT NOT NULL,
    usuario_id TEXT,
    perfil JSONB NOT NULL,              -- contexto acumulado, preferencias, historial
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE decisiones (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,                 -- "cr0" | "cr1"
    descripcion TEXT NOT NULL,
    contexto JSONB,
    decidido_por TEXT DEFAULT 'jesus',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### GRUPO 8 — COMUNICACIÓN (sistema nervioso)

```sql
CREATE TABLE marcas_estigmergicas (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL,                 -- "hallazgo" | "sintesis" | "alerta" | "señal"
    origen TEXT NOT NULL,               -- qué agente la creó
    contenido JSONB NOT NULL,
    consumida BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### GRUPO 9 — CONTEXTO / MEMORIA (Fase 2+, cuando escale)

```sql
-- Se activa cuando archivos .md de contexto superen 50k tokens
-- El Gestor avisa automáticamente
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    scope TEXT NOT NULL,                -- "sistema" | "chief" | "dominio" | "exocortex:pilates"
    documento TEXT,                     -- "MAESTRO_v3.md" | "manual_pilates.pdf"
    seccion TEXT,                       -- "§4.3"
    tipo TEXT NOT NULL,                 -- "arquitectura" | "decision" | "datos" | "hallazgo" | "dominio"
    nivel TEXT,                         -- "L0" | "L1" | "L2"
    texto TEXT NOT NULL,
    embedding vector(1024),
    relevancia FLOAT DEFAULT 1.0,       -- el Gestor puede subir/bajar peso
    caduca_at TIMESTAMPTZ,              -- datos L2 pueden expirar
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kb_embedding ON knowledge_base
  USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_kb_scope ON knowledge_base(scope);
CREATE INDEX idx_kb_scope_tipo ON knowledge_base(scope, tipo);
```

#### LOG DEL GESTOR (auditoría de decisiones automáticas)

```sql
CREATE TABLE log_gestor (
    id SERIAL PRIMARY KEY,
    accion TEXT NOT NULL,               -- "poda" | "promocion" | "reasignacion" | "recompilacion"
    detalle JSONB NOT NULL,             -- {pregunta_id, motivo, valor_antes, valor_despues}
    nivel TEXT NOT NULL,                -- "auto" | "cr1"
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### VISTA MATERIALIZADA (lo que el Gestor consulta)

```sql
CREATE MATERIALIZED VIEW pregunta_efectividad AS
SELECT
  pregunta_id, modelo, celda_objetivo, consumidor,
  COUNT(*) as n_ejecuciones,
  AVG(gap_cerrado) as gap_medio_cerrado,
  AVG(tasa_cierre) as tasa_media_cierre,
  STDDEV(tasa_cierre) as varianza,
  MIN(tasa_cierre) as peor_caso,
  MAX(tasa_cierre) as mejor_caso
FROM datapoints_efectividad
GROUP BY pregunta_id, modelo, celda_objetivo, consumidor;
-- Refresco: cada 50 ejecuciones o cada 24h
```

#### Memoria del sistema — Fase 1 (archivos .md) vs Fase 2 (pgvector)

**Fase 1 (mes 1-3):** el conocimiento del sistema (Maestro, álgebra, resultados de experimentos, contexto de dominio) vive en archivos .md compilados en `contexto/`, inyectados directo en prompts. ~70-80k tokens totales caben en contexto de los modelos OS (128-256k). Cero infraestructura extra.

```
contexto/
  sistema.md           ← Maestro v3 comprimido (~5k tokens)
  reglas.md            ← 13 reglas + propiedades algebraicas
  modelos.md           ← tabla modelo→celda + sesgos
  dominio_pilates.md   ← conocimiento acumulado
  dominio_fisio.md     ← conocimiento acumulado
  chief_decisions.md   ← decisiones CR1 acumuladas
```

**Fase 2 (cuando el Gestor avise):** check automático en loop lento:
```python
if total_tokens_contexto > 50000:
    alerta("Contexto supera 50k tokens. Migrar a pgvector. CR0.")
```
Se activa tabla `knowledge_base`. Misma interfaz `remember()`, diferente backend.

### §6.7 Conocimiento transversal 🔧

El Gestor acumula datos de efectividad de TODOS los consumidores. Lo que Pilates descubre sobre dolor lumbar sube al Gestor. Si Clínica presenta un caso con patrón de gaps similar, el Gestor le ofrece esas preguntas. El conocimiento es transversal, no siloado (Principio 24).

---

## §7. LOS REACTORES

### §7.1 Estado del ecosistema

| Reactor | Función | Estado |
|---------|---------|--------|
| Cartografía | Crea la Matriz (preguntas base) | ✅ 54 análisis, 18 INTs |
| v1 Sintético | Amplifica con datos sintéticos | ✅ 1.183 datapoints, $1.99 |
| v2 Inversor | Enriquece desde documentos técnicos | 🔧 Spec hecha |
| v3 Conceptual | Enriquece desde fundamentos teóricos | 🔧 1 ejemplo validado |
| v4 Datos reales | Enriquece desde telemetría de operación | 🔧 Diseñado |
| Meta-motor | Evoluciona (preguntas sobre preguntas) | ⬜ Horizonte |

### §7.2 Priorización y ecosistema

Reactor v4 (datos reales) > v2 (documentos) > v3 (teórico) > Meta-motor. El flywheel se activa con v4 cuando el primer exocortex esté desplegado.

**Ciclo de vida de la Matriz:**
```
Cartografía → CREA la Matriz (preguntas base, empírico)
Reactor v1  → AMPLIFICA la Matriz (datos sintéticos)
Reactor v3  → ENRIQUECE la Matriz (preguntas desde conceptos teóricos)
Motor vN    → USA la Matriz sobre casos reales (y registra efectividad — CRÍTICO)
             → Multi-modelo OS ejecuta masivamente (~$0.001-0.003/ejecución)
             → Evaluador mide cierre de gaps
             → Datos fluyen al Gestor
Gestor      → MANTIENE la Matriz (poda, asigna, fusiona, recompila)
             → Alimenta Motor vN + cada Exocortex
Reactor v2  → ENRIQUECE (preguntas de dominio desde documentos invertidos)
Reactor v4  → ENRIQUECE (preguntas desde datos REALES de operación)
Meta-motor  → EVOLUCIONA (preguntas mejores por razonamiento sobre preguntas)
                    │
                    └→ vuelta al Motor vN con Matriz mejorada via Gestor
```

**Ecosistema de entrenamiento — los Reactores generan, el Motor verifica:**
```
Reactor v1 (datos sintéticos)      ─┐
Reactor v2 (documentos)             ├─→ Preguntas nuevas → Motor vN las ejecuta
Reactor v3 (conceptos teóricos)     ─┤     → Gestor registra efectividad
Reactor v4 (datos reales operación) ─┤     → Poda las que no funcionan
Meta-motor (razonamiento)           ─┘     → Prioriza las que sí
```

Lo que NO cambia nunca: la estructura 3L × 7F (L0). Lo que mejora: las preguntas y su efectividad (L2).

### §7.3 Reactor v2 — Inversor de documentos 🔧

**Qué hace:** toma un documento técnico (manual, paper, guía) y extrae las preguntas implícitas, mapeándolas a coordenadas de la Matriz.

**Arquitectura:**
```
DOCUMENTO TÉCNICO (paper, tesis, manual, caso documentado)
    ↓
AGENTE INVERSOR (Haiku/OS)
  "¿Qué preguntas está respondiendo este texto?"
  Extrae 200-500 preguntas implícitas por documento
    ↓
CLASIFICADOR (Embeddings + modelo)
  "¿A qué inteligencia(s) pertenece cada pregunta?"
  Mapea pregunta → INT-XX + confianza 0-1
    ↓
DETECTOR DE PATRONES ESTRUCTURALES (código + OS)
  "¿Las preguntas siguen la misma secuencia que la cartografía?"
    ↓
OUTPUT:
  1. Preguntas nuevas etiquetadas (enriquecen niveles 2-3)
  2. Patrones estructurales (confirman/refutan esqueleto)
  3. Preguntas huérfanas (no caben en ninguna INT → ¿candidatas a INT-19?)
  4. Datos de entrenamiento frescos para re-entrenar router
```

**Hipótesis a validar (3 resultados posibles):**

Hipótesis A (universalidad): Las preguntas de expertos en documentos reales siguen EXTRAER→CRUZAR→LENTES→INTEGRAR. La secuencia es invariante del dominio.

Hipótesis B (artefacto): Los papers NO siguen esa secuencia — van directo a LENTES sin EXTRAER ni CRUZAR. La secuencia de la cartografía es un artefacto del diseño del protocolo.

Hipótesis C (parcial): Las cuantitativas (INT-01, 02, 07) sí siguen EXTRAER→CRUZAR→LENTES. Las interpretativas (INT-08, 12, 17) tienen otra estructura. Hay familias de esqueletos, no uno universal.

Cualquiera de los 3 resultados es valioso: A confirma para escalar, B fuerza rediseño, C revela que el motor necesita esqueletos diferentes por categoría.

**Fuentes de documentos por inteligencia:**
```
INT-01: arXiv math (optimización, decisión bajo incertidumbre)
INT-02: arXiv cs (algoritmos, complejidad, sistemas)
INT-03: Papers de systems thinking, cibernética
INT-04: Papers de ecología de sistemas, resiliencia
INT-05: HBR cases, papers de estrategia corporativa
INT-06: arXiv econ (teoría de juegos), casos de negociación
INT-07: SSRN, SEC filings, papers de corporate finance
INT-08: Papers de psicología social, dinámica de grupos
INT-09: Papers de pragmática, análisis del discurso
INT-10: PubMed (biomecánica, fisiología), protocolos clínicos
INT-11: Papers de diseño, arquitectura, visualización
INT-12: Estudios narratológicos, guiones documentados
INT-13: Papers de futures studies, scenario planning
INT-14: Papers de creatividad, design thinking, TRIZ
INT-15: Papers de diseño, filosofía del arte, crítica
INT-16: Papers de project management, ingeniería de sistemas
INT-17: Filosofía existencialista, psicología humanista
INT-18: Papers de mindfulness, fenomenología, contemplativas
```
Objetivo: 5-10 documentos por inteligencia como semilla inicial (~100 documentos totales).

### §7.4 Reactor v3 — Generación conceptual 🔧

**Qué hace:** genera preguntas desde fundamentos teóricos. No invierte documentos existentes — crea preguntas que ningún manual contendría, derivadas de las 9 categorías de la Meta-Red.

**Estado:** 1 ejemplo validado (categoría Sistémica). 8 categorías restantes por ejecutar. Coste estimado: ~$10-18 total. Produce ~3.000-5.000 preguntas con coordenadas + fuente teórica.

### §7.5 Reactor v4 — Datos reales de operación 🔧

El reactor más valioso. No inventa (v1), no invierte documentos (v2), no razona sobre teoría (v3). **Observa qué pasa realmente** en un negocio y genera preguntas desde los huecos entre lo observado y lo que la Matriz dice que debería cubrirse.

Son las preguntas que un consultor de 20 años haría después de pasar 2 semanas DENTRO del negocio.

**Pipeline:**

**Fase 1 — OBSERVAR (pasivo, X semanas):**
La telemetría del exocortex lee datos reales de operación:
```
→ Transacciones (qué se vende, cuándo, cuánto)
→ Reservas y cancelaciones (patrones temporales)
→ Proveedores (pedidos, costes, frecuencia, dependencias)
→ Personal (turnos, rotación, absentismo)
→ Reviews online (qué dicen los clientes)
→ Interacciones con el exocortex (qué pregunta el usuario, qué ignora)
→ Cualquier dato que el negocio genere digitalmente
```
Output: datos crudos con patrones temporales.

**Fase 2 — MAPEAR A LA MATRIZ (automático):**
Para cada dato observado, el Gestor pregunta: ¿qué celda toca? ¿Hay celda que DEBERÍA tocar pero no toca? ← ESTO ES EL GAP.
```
Dato: "Cancela 3 proveedores en 2 meses pero no busca nuevos"
  Celda cubierta: Depurar×Sentido (depura lo que no funciona)
  Celda gap:      Captar×Salud (no capta recursos de reemplazo)
  Celda gap:      Adaptar×Continuidad (no adapta supply chain)
```
Modelo OS razonador (V3.2/Cogito) para mapeo + generación.

**Fase 3 — GENERAR PREGUNTAS:**
Los gaps observados generan preguntas con coordenadas exactas:
```
Pregunta: "¿El sistema de aprovisionamiento tiene un solo proveedor
           crítico sin backup?"
  → Coordenadas: INT-04 (Ecológica) × Frontera × Salud
  → Fuente: observación directa, no teoría
  → Verificada: el dato confirma que es relevante

Pregunta: "¿Cuántos días puede operar si su proveedor principal falla?"
  → Coordenadas: INT-01 (Lógica) × Conservar × Continuidad
  → Fuente: inferencia de datos de pedidos
```
El dato confirma la pregunta en el mismo momento que la genera. No necesitas validar después.

**Fase 4 — VALIDAR Y PROMOVER:**
Las preguntas entran con score provisional. El Motor vN las ejecuta sobre otros casos del mismo dominio. Si cierran gaps → se promueven. Si no → se podan (selección natural).

**Pilotos reales (validación del Reactor v4):**

Piloto 1 — Estudio de Pilates (Jesús):
- Telemetría: reservas, asistencia, clientes, sesiones, ingresos
- Reactor v4 genera preguntas desde patrones reales del estudio
- Validación: ¿los agentes detectan cosas que Jesús no veía?

Piloto 2 — Clínica de Fisioterapia (mujer de Jesús):
- Telemetría: pacientes, tratamientos, agenda, derivaciones
- Segundo dominio: valida transferencia cross-dominio
- Test clave: ¿preguntas de Pilates sobre gestión de agenda aplican a fisio?

Ambos pilotos alimentan la Matriz. Lo que uno descubre, el otro lo recibe si el patrón de gaps coincide.

**Integración con software de gestión existente (caso escala):**

El Reactor v4 no requiere software propio. Se conecta al software que el negocio YA usa:
```
Software de gestión existente (TPV, ERP, CRM)
    ↓ API de lectura
Capa de telemetría (fly.io)
    ↓
Reactor v4 → detecta gaps
    ↓
Gestor → compila prompts por módulo
    ↓
Agentes OS → inyectados en cada módulo
    ↓ API de escritura (sugerencias o auto-config con CR1 del dueño)
Software de gestión SE ADAPTA al negocio

Coste de la capa inteligente: ~$2-5/mes en tokens
Valor percibido: software que PIENSA sobre tu negocio
```

### §7.6 El flywheel ✅ (Principio 29)

```
Exocortex A se despliega
  → Telemetría observa operaciones reales
  → Reactor v4 genera preguntas desde gaps observados
  → Preguntas entran en la Matriz con coordenadas + fuente
  → Gestor las prueba con Motor vN sobre otros casos
  → Las que funcionan se promueven (selección natural)
  → Exocortex B se conecta → recibe preguntas que SOLO existen
    porque Exocortex A operó
  → B genera NUEVAS preguntas desde SUS datos
  → La Matriz se enriquece exponencialmente con cada cliente

CADA CLIENTE HACE AL SISTEMA MEJOR PARA TODOS LOS DEMÁS.
```

**Transferencia cross-dominio:** preguntas con coordenadas en la Matriz (e.g., Frontera×Salud) son transferibles entre dominios. Si un restaurante descubre "proveedor único = fragilidad", esa pregunta aplica a clínica dental (materiales) o estudio de pilates (equipamiento).

### §7.7 Prompts vivos 🔧

Los prompts de cada agente NO son estáticos. Son programas compilados en tiempo real por el Gestor.

**3 mecanismos de evolución:**

1. **Por datos del propio negocio (Reactor v4):** El negocio cambia → telemetría detecta → nuevas preguntas → Gestor recompila prompt. Cadencia: continua.
2. **Por aprendizaje cross-dominio (flywheel):** Otro negocio descubre pregunta potente → Gestor detecta transferencia por coordenadas. Cadencia: cada refresco del Gestor (50 ejecuciones o 24h).
3. **Por mejora de la Matriz global (Reactores v1-v3):** Un reactor genera preguntas mejores → Motor vN las valida → reemplazan las menos efectivas. Cadencia: batch semanal/mensual.

Sin deploy. Sin intervención. Sin downtime.

---

## §8. INFRAESTRUCTURA

### §8.1 Stack

| Qué | Tecnología | Estado |
|-----|-----------|--------|
| Motor | Python, FastAPI, fly.io | ✅ |
| DB | PostgreSQL + pgvector (fly.io Amsterdam) | ✅ |
| Legacy | Supabase (99 Edge Functions, Deno) | ⚠️ Por migrar |
| Modelos | OpenRouter + DeepSeek API | ✅ |
| Embeddings | Voyage AI (fallback TF-IDF) | ✅ |
| Repo | Local git, sin remote | ⚠️ |

**Providers de inferencia OS:**
- **Together:** mayor catálogo (Qwen, GPT-OSS, MiniMax, Cogito, MiMo, GLM, Llama)
- **DeepSeek API directo:** más barato para V3.2 y Reasoner que vía Together
- **Fireworks:** fallback rápido, buena latencia, R1 disponible
- **Groq:** ultra-rápido para modelos pequeños (Llama 70B en ms)
- **OpenRouter:** punto único multi-provider, útil para candidatos nuevos

**Principio OS-first:**
```
Fase 1 (ahora):    Ejecutores = OS. Evaluador = consenso OS. Orquestador = OS.
Fase 2 (~500 ejecuciones): Testear evaluador OS vs Sonnet.
Fase 3 (si pasa):  TODO OS. Sonnet solo para calibración periódica.

Coste por caso:
  Fase 1: ~$0.08 OS + ~$0.02 evaluador OS = ~$0.10
  (Con Sonnet evaluador: ~$0.08 + ~$0.24 = ~$0.32)
```

**Stack del Gestor:**
```
Decisión rutinaria (lookup, asignación estable):
  → Código puro o modelo barato. ~$0.001

Decisión compleja (fusión, poda, celda nueva):
  → Modelo OS razonador (V3.2 o Qwen). ~$0.003

Decisión arquitectural (reorganizar Matriz, crear pregunta nueva):
  → Modelo OS grande, batch semanal. ~$0.03-0.15
```

**Qué se mantiene de Supabase como patrón (no como código):**
Estigmergia, enjambres, telemetría, mejora continua — todos son patrones en tablas Postgres. Se llevan tal cual. Se reemplazan 4 piezas de fontanería: Edge Functions → Python, pg_net → workers/colas, cron → node-cron, auth → JWT.

### §8.2 Migración Supabase → fly.io

99 Edge Functions. NO trivial. Estimación: 3-6 meses reescritura gradual.

Estrategia: gradual, no big bang. Motor vN ya en fly.io. Legacy se migra por fases:

**~53 agentes LLM clasificados por riesgo de migración:**

**Fase 1 — 🟢 Sin riesgo (~30 agentes, migración inmediata):**

Motor-orquestador (mayor consumidor LLM — hasta 168 calls Haiku/ejecución):
- 7 primitivas × N ángulos (fan-out): 56-168 calls/ejecución → 🟢 clasificación mecánica pura
- 7 integradores: sintetizar ángulos → 🟢
- 7 verificadores (dial≥0.8): validar coherencia → 🟢
- 1 verbalizador motor: ~80% template ($0), ~20% Haiku → 🟢
- Impacto: de ~$0.02-0.09/ejecución Haiku → ~$0.001-0.005/ejecución OS

Enjambre IAS (Pipeline Diagnóstico):
- 7 parseadores (P1-P7): análisis sintáctico mecánico → 🟢
- 9 lentes (3×3: input/basal/completa): organización de datos → 🟢
- 1 cruzador-input → 🟢

Mejora Continua:
- 1 procesador-mejora → 🟢
- 1 auditor-presupuestos → 🟢
- 1 detector-patrones (dormido) → 🟢

Enjambre Diseño:
- 1 formulador-preguntas → 🟢

Cambio: `provider="os"` en cada agente via llm-proxy. 0 refactor.

**Fase 2 — 🟡 Testear (~12 agentes, comparar OS vs Anthropic en 10 inputs):**

Enjambre IAS:
- 1 correlador-vida (Haiku/Sonnet) → 🟡 hay juicio en correlación
- 1 sintetizador-diferencial (Sonnet) → 🟡
- 1 prescriptor (Sonnet) → 🟡 requiere juicio

Enjambre Diseño:
- 3 diseñadores (agentes/datos/flujo, Sonnet) → 🟡 tarea de diseño compleja
- 1 explorador-externo (Sonnet) → 🟡
- 1 verificador-diseño (Sonnet) → 🟡
- 3 generadores-spec (Sonnet) → 🟡 generación de código

Test: comparar output con Sonnet en 10 inputs reales. Si >85% equivalente → migrar.

**Fase 3 — 🔴 Último (2 verbalizadores):**
- 1 verbalizador IAS (informe final de diagnóstico) → 🔴 usuario lo lee
- 1 traductor-natural (diseño para el usuario) → 🔴 calidad percibida importa

Incluso estos se testean con V3.2/Qwen eventualmente.

**Impacto económico:**
```
ANTES:  ~53 agentes en Anthropic → ~$14/mes
FASE 1: ~$4/mes (solo verbalizadores + tests)
FASE 2: ~$2/mes (solo 2 verbalizadores)
FASE 3: ~$0.50-1/mes (todo OS)
```

**Motor v3.3 / Motor-Orquestador:** El mayor consumidor LLM del sistema. En dial alto: hasta 168 calls Haiku por ejecución (7 primitivas × 24 ángulos). Todo clasificación mecánica. De ~$0.02-0.09/ejecución Haiku → ~$0.001-0.005/ejecución OS.

**llm-proxy:** un solo punto de cambio. Routing multi-provider:
```
provider="os" + modelo="haiku"   → Groq API (Llama 70B)
provider="os" + modelo="sonnet"  → Together API (V3.2 o Qwen)
provider="anthropic" (default)   → Anthropic API
```

### §8.3 Chief of Staff: ELIMINADO

24 agentes + 9 modos + pipeline dual → eliminados. Motor vN + Gestor + Matriz reemplazan funcionalidad.

**Lo que se conserva como patrón (no como código):**
- Estigmergia entre agentes (patrón en Postgres, se lleva tal cual)
- Cola de preguntas priorizada
- Persistencia inter-sesión (perfil_usuario, decisiones)
- Detección de contradicciones (se integra en el Motor como paso del pipeline)

**Lo que se elimina:**
- Pipeline dual superficial/profundo (la Matriz con gradientes es más precisa)
- 9 modos conversacionales (overengineered — el Motor tiene gradientes, no modos)
- Router de intenciones (el detector de huecos del Motor es más preciso)
- 24 agentes específicos del Chief

### §8.4 Enjambre de código 🔧

La misma lógica de "modelos diferentes cubren celdas diferentes" aplica al código:

```
DeepSeek V3.2    → Arquitectura, orquestación, razonamiento sobre código
                   Mejor en: diseñar pipelines, refactorizar, decisiones complejas

Qwen3-Coder 480B → Generación de código puro, completar funciones
                   Mejor en: escribir código rápido, boilerplate, tests unitarios
                   256K ctx, diseñado para repo-scale

Cogito 671B      → Razonamiento profundo sobre por qué así y no de otra forma
                   Mejor en: revisar arquitectura, detectar deuda técnica, specs

DeepSeek V3.1    → Código rápido y barato para tareas mecánicas
                   Mejor en: migraciones SQL, patches simples, scripts de deploy

Kimi-Dev 72B     → #1 SWE-bench para patching real de código
                   Mejor en: fixes, debugging real, patches
```

El Gestor acumula datos de "qué modelo generó mejor código para qué tipo de tarea" y asigna, igual que con las celdas de la Matriz.

### §8.5 Auto-mejora — 3 niveles 🔧

**Nivel 1 — Fontanería (auto-aprobable):**
```
Detectar: agente sin retry → generar fix → staging → regresión → prod
Detectar: latencia degradada → optimizar query → staging → regresión → prod
Cambios < 20 líneas, auto-CR1.
```

**Nivel 2 — Mejoras arquitecturales (CR1 siempre):**
```
Detectar: celda Distribuir débil en todos los modelos
  → Cogito genera spec de nuevas preguntas
  → V3.2 implementa migración SQL + función
  → Qwen Coder genera tests
  → Staging → regresión → CR1 → prod
```

**Nivel 3 — Auto-evolución (semillas dormidas + CR1):**
```
Semilla se activa → enjambre de código implementa agente completo
  → Desde spec hasta deploy, autónomo
  → El sistema crece solo, Jesús solo aprueba
```

Infraestructura existente: `cola_mejoras` (detecta/prioriza), implementador autónomo (YAML→SQL→deploy→tests→regresión), `regresion.sh` (6 tests), `deploy.sh` (staging/prod), propiocepción (157 componentes), 22 semillas dormidas.

### §8.6 Fábrica de Exocortex ⬜

El enjambre de código no solo mejora el sistema — fabrica nuevos sistemas:

```
Input: "Necesito un exocortex para gestión de restaurantes"

1. Gestor evalúa qué preguntas de la Matriz transfieren a restauración
2. Reactor v2 invierte documentos del sector → preguntas de dominio
3. Enjambre de código DISEÑA e IMPLEMENTA el exocortex:
   → Cogito: spec arquitectural
   → V3.2: pipeline + gateway + integración con Gestor
   → Qwen Coder: Edge Functions / endpoints
   → V3.1: migraciones SQL + deploy scripts
4. Auto-deploy a staging → regresión → CR1 → prod

Tiempo: horas, no semanas. Coste: ~$0.50-2 en tokens.
Intervención humana: solo CR1 al final.
```

Cada exocortex nuevo se conecta al Gestor desde el día uno. Lo que Pilates aprende sobre movimiento, Restaurantes sobre operaciones, Clínica sobre salud oral — todo alimenta la Matriz central (Principio 24).

Roles en el sistema:
```
Gestor de la Matriz  = QUÉ mejorar / QUÉ construir (cerebro)
Enjambre de código   = CÓMO mejorarlo / CÓMO construirlo (manos)
Regresión + CR1      = VERIFICAR que no rompe nada (sistema inmune)
Telemetría           = MEDIR el impacto (propiocepción)
```

### §8.7 Rúbrica de profundidad ✅

La profundidad = cobertura de la Matriz. No es escala subjetiva. Es mapeo a 21 celdas (3L×7F):

```
Nivel 0: no toca la celda
Nivel 1: mención genérica
Nivel 2: dato/inferencia específica del caso
Nivel 3: revela algo no obvio (contradicción, patrón invisible)
Nivel 4: redefine la pregunta del caso desde esa celda
```

Esta rúbrica se usa en: evaluación de modelos (Exp 4), evaluación de efectividad de preguntas (Gestor), verificación de cierre de gaps (Pipeline paso 5).

---

## §9. RESULTADOS EMPÍRICOS — 10 EXPERIMENTOS

### §9.1 Resumen ejecutivo

| Exp | Qué testea | Resultado clave | Estado |
|-----|------------|-----------------|--------|
| Multi-modelo + Exp 1 | 12 modelos OS en Matriz | V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) top 3. V3.2-chat 6/21 celdas 3+ (más profundo). Claude 10º de 12 | ✅ |
| Exp 1 (nuevos modelos) | V3.2, Qwen3, Kimi, Cogito | V3.2-chat: 80% coding (4/5). Cogito: 3.4 Frontera×Sentido. Kimi K2 inerte en R2 | ✅ |
| Exp 1 bis (6 modelos nuevos) | Kimi K2.5, Qwen 3.5, Step-3.5, MiMo, Nemotron, Kimi-Dev | Disponibilidad verificada. Tests pendientes | ✅ |
| Exp 2 (evaluadores) | 7/11 modelos como evaluadores | 5/7 deflatan vs Sonnet. Sonnet es mala referencia. Correlación Sonnet↔Qwen3: 0.605 | ✅ |
| Exp 3 (código) | 10 modelos × 5 tareas coding | Mapa de capacidad por modelo. V3.2: 4/5 general, falla en lógica dominio | ✅ |
| Exp 4 (mesa redonda) | 12 modelos, 2 rondas | R1→R2: 7→70 celdas consenso (10x). +16 celdas 3+ emergentes. Qwen3 inflador (+0.93). 6/8 absorben de Qwen3. Perfiles: COMPLETO / ESPONJA / ABSORBENTE / INERTE | ✅ |
| Exp 4.1 (especializada) | Prompts por fortaleza | +0.55 en foco, -0.14 fuera. V3.2+V3.1 = 97.9% cobertura. Infladores (Qwen, Kimi, Opus) BAJAN con especialización. Usar SIEMPRE | ✅ |
| Exp 4.2 (sintetizador) | ¿Quién integra mejor? | Cogito #1 (3.6 conexiones, 5/5 no-genéricos, 47s). R1 #2 (3.0, 55s). GLM y MiniMax: parse fail | ✅ |
| Exp 4.3 (pizarra) | Mente distribuida | 425 conexiones, 239 puntos ciegos. GPT-OSS motor (119 contrib). Auto-tracking infla +0.93. Evaluación externa 3.06 vs auto 3.99. No bate mesa en scores, SÍ en valor exclusivo | ✅ |
| Exp 5 (cadena montaje) | ¿Pipeline OS reemplaza Code? | 8 configs × 5 tareas | ✅ |
| Exp 5b | Variantes de cadena | Datos complementarios | ✅ |
| Exp 6 (agente código) | Agente coding autónomo | 460 líneas, 99% tests. Cadena de montaje funciona | ✅ |
| Exp 7 (Chief 8 componentes) | Chief con componentes OS | 4 fallos identificados, Chief deprecado | ✅ |
| Exp 8 (auditoría) | Estado completo del sistema | 6 decisiones CR0 pendientes identificadas | ✅ |
| Exp 9 | Completado sesión anterior | Datos integrados | ✅ |
| Exp 10 (roadmap enjambre) | 7 modelos diseñan roadmap | Sesgo de contexto severo: modelos con 45k tokens más destructivos que los de 225k. "Dunning-Kruger del enjambre". Señales válidas extraídas con corrección | ✅ |

### §9.2 Datos del experimento multi-modelo completo (Exp 1) ✅

12 modelos evaluados en cobertura matricial. Variante C (instrucción analítica), 3 casos × 3 INTs.

| # | Modelo | Nivel medio | Celdas cubiertas | Celdas nivel 3+ |
|---|--------|-------------|-----------------|-----------------|
| 1 | **DeepSeek V3.1** | **2.19** | 19/21 | 5/21 |
| 2 | **DeepSeek R1** | **2.18** | **20/21** | 4/21 |
| 3 | **GPT-OSS 120B** | **2.15** | 19/21 | 5/21 |
| 4 | **V3.2-chat** | **2.12** | 18/21 | **6/21** |
| 5 | V3.2-Reasoner | 2.00 | 17/21 | 3/21 |
| 6 | Cogito 671B | 1.98 | 18/21 | 2/21 |
| 7 | Qwen3 Thinking | 1.95 | 19/21 | 2/21 |
| 8 | Kimi K2.5 | 1.87 | 18/21 | 1/21 |
| 9 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 |
| 10 | Claude (ref) | 1.79 | 15/21 | 1/21 |
| 11 | Maverick | 1.74 | 16/21 | 1/21 |
| 12 | 70B | 1.42 | 11/21 | 1/21 |

Hallazgos clave Exp 1:
1. 3 modelos OS superan a Claude. Claude es 10º de 12.
2. V3.2-chat tiene 6/21 celdas nivel 3+ — más insights no obvios que todos. Nivel medio 4º pero más profundo donde importa.
3. Cogito Frontera×Sentido = 3.4 — score más alto de cualquier modelo en cualquier celda de Sentido. Candidato a cerebro profundo.
4. 9 modelos diferentes ganan celdas en Tabla 3. Ningún modelo domina. El enjambre siempre gana.
5. Sentido sigue siendo la lente más difícil para todos.
6. V3.2 Reasoner corregido — bug en reasoning_content vs content. Fix: leer content primero, si vacío leer reasoning_content.

El benchmark que importa no es HumanEval ni Arena — es cobertura de la Matriz 3L×7F bajo las mismas preguntas.

### §9.3 Datos del Exp 2 — Evaluadores OS ✅

7/11 modelos testeados como evaluadores vs Sonnet como referencia.

| Modelo | Spearman | Bias vs Sonnet | F1(3+) | Nota |
|--------|----------|----------------|--------|------|
| GLM-4.7 | 0.464 | +0.14 | 0.000 | Solo 1/5 outputs parseados |
| V3.2 Chat | 0.426 | -0.46 | 0.103 | Deflata vs Sonnet |
| Qwen3-235B | 0.373 | +0.54 | 0.578 | Infla, pero detecta insights |
| GPT-OSS | 0.280 | -0.74 | 0.348 | Fuerte deflación |
| R1 | 0.247 | -0.62 | 0.293 | Deflata |
| V3.1 | 0.220 | -0.34 | 0.190 | Deflata |
| M2.5 | 0.208 | -0.44 | 0.279 | Deflata |

Conclusión: Ningún modelo OS alcanza Spearman ≥ 0.85 vs Sonnet. Pero 5/7 deflatan → Sonnet posiblemente infla, no que OS evalúe mal. La referencia es el problema.

Decisión: no hay gold standard. La verdad es el consenso entre evaluadores. Mesa redonda (Exp 4) como protocolo de evaluación.

### §9.4 Perfiles de modelos en mesa redonda (Exp 4) ✅

| Perfil | Modelos | Comportamiento |
|--------|---------|----------------|
| **COMPLETO** | Qwen3-235B, Cogito | Aportan perspectivas propias + absorben de otros |
| **ESPONJA** | GPT-OSS, Opus, V3.2 Chat | Absorben todo (mejoran en R2), aportan 0 nuevo |
| **ABSORBENTE** | V3.1, GLM-4.7, Kimi | Absorben parcial, no aportan |
| **INERTE** | Sonnet, R1, V3.2R, M2.5 | No participaron en R2 (formato/timeout) |

Datos clave:
- Qwen3-235B: 31 únicos (17 inflación = 14 netos). Nivel medio R2=3.19. "Rey de la mesa" pero inflador
- Cogito: 6 únicos (6 inflación = 0 netos genuinos). 10 ángulos propios. 5.4% pérdida sin él
- Opus: 0 aportes únicos, 0% pérdida sin él. $75/M. FUERA de pipelines automatizados
- Sonnet: 0 aportes únicos. Mala referencia confirmada
- GPT-OSS: #1 en ranking por absorción (82 celdas) pero 0 aportes propios. Esponja útil

Mesa mínima con genérico: GPT-OSS + Qwen3-235B = 94.6% del valor (~$1.60/M).
Mesa mínima con especializado: V3.2-chat + V3.1 = 97.9% del valor — MEJOR y SIN inflador.

### §9.5 Hallazgos que cambian decisiones

**H1.** 3 modelos OS superan a Claude en la Matriz. Claude es 10º de 12. El benchmark que importa no es HumanEval — es cobertura de la Matriz 3L×7F. (Exp 1)

**H2.** La especialización de prompts siempre mejora. Mismo coste, mejor resultado en foco. V3.2-chat + V3.1 = 97.9% cobertura. Los infladores genéricos (Qwen3, Kimi, Opus) PIERDEN rendimiento con especialización — su ventaja era genérica, no real. Usar SIEMPRE sobre genérica. (Exp 4.1)

**H3.** Cogito es el sintetizador sin discusión. 3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s. Coste marginal: $0.03-0.10. Usar SIEMPRE como paso final de cualquier mesa. (Exp 4.2)

**H4.** La pizarra produce valor exclusivo (425 conexiones, 239 puntos ciegos) pero no bate a mesa en scores (3.06 vs 3.27). Auto-tracking infla +0.93 puntos — siempre usar evaluación externa. Es para Tier 4-5, no para interacción. (Exp 4.3)

**H5.** Sonnet no es referencia fiable de evaluación. 0 aportes únicos en Exp 4. Opus igual: 0 aportes, $75/M. Usar consenso de panel (V3.2+V3.1+R1), no modelo individual premium. (Exp 2 + Exp 4)

**H6.** Qwen3 infla +0.93 puntos. No es "cerebro" — es inflador. Con especialización BAJA rendimiento (-0.31). 17 inflaciones de 31 únicos en Exp 4. En pizarra: 63 contribuciones, tercer contribuidor — pero su influencia desproporcionada en mesa redonda (6/8 modelos absorben principalmente de él) distorsiona la convergencia. (Exp 4 + 4.1)

**H7.** V3.2 como coder: 80% (4/5 tests). Falla en lógica de dominio (mapeo Matriz→INT). Funciona en enjambre, no solo. Kimi-Dev complementa como #1 en patching real. (Exp 1 + Exp 5)

**H8.** Agente de coding OS: 460 líneas, 99% tests. La cadena de montaje funciona. El enjambre de código es viable como componente permanente del sistema. (Exp 6)

**H9.** Exp 10 — "Dunning-Kruger del enjambre": modelos con contexto compacto (~45k tokens: R1, Step, Nemotron) recomiendan eliminar componentes validados empíricamente (18 inteligencias, álgebra). Modelos con contexto completo (95-225k tokens: Kimi, V3.2, GPT-OSS) son más conservadores y precisos. La síntesis (Cogito) da peso igual a todos → amplifica el sesgo de los que menos saben. Corrección: ponderar votos por nivel de contexto (Principio 33). (Exp 10)

### §9.6 Señales válidas del Exp 10 (corregidas)

Lo que el enjambre señala correctamente, filtrado de ruido:
1. Eliminar Chief — ya decidido, ejecutar
2. Motor vN + Gestor = prioridad — ya priorizado
3. Reactor v4 > v3 — ya decidido
4. Pilotos reales antes de escalar — Principio 30
5. Vender el output, no la Matriz — marketing ≠ arquitectura
6. Migración Supabase más costosa de lo presupuestado — dato real de Kimi (225k contexto)

Lo que el enjambre dice INCORRECTAMENTE (sesgo de contexto):
- "18 inteligencias = pseudociencia" → Falso (54 análisis empíricos, 18/18 no-idempotentes). Dicho por modelos con 45k tokens que no vieron los resultados.
- "Álgebra = innecesaria" → Falso (13 reglas derivadas empíricamente de 8 propiedades testeadas en 34 chats). Dicho por modelos que no vieron la cartografía.
- "Reducir a 6" → Parcialmente correcto para MVP (ya decidido en §2.3), incorrecto como decisión permanente.

### §9.7 Datos del Exp 10 por modelo

| Modelo | Contexto | Tokens in | Latencia | Calidad de recomendaciones |
|--------|----------|-----------|----------|----------------------------|
| Kimi K2.5 | full (95k) | 128-137k | 126-130s | Conservador, preciso en estimación de migración Supabase |
| V3.2-chat | full (95k) | 129k | 202s | Equilibrado, reconoce valor de componentes existentes |
| GPT-OSS | max (225k) | 238-245k | 76-88s | El más informado, recomendaciones proporcionadas al contexto |
| R1 | compact (45k) | 66k | 83s | Agresivo en simplificación, rechaza componentes que no vio |
| Step 3.5 | compact (45k) | 66k | 27s | Rápido pero destructivo, quiere eliminar álgebra |
| Nemotron | compact (45k) | 67k | 32s | Similar a R1, reduce por no entender |
| Qwen3 | full (95k) | error | error | No completó ninguna ronda |
| Cogito (síntesis) | — | 22k | 20s | Da peso igual a todos → amplifica sesgo de contexto |

---

## §10. CHECKLIST — ESTADO ACTUAL

### Fundamentos ✅
- [x] 3L × 7F × 18INT definidos y validados
- [x] 8 operaciones sintácticas (Marco Lingüístico)
- [x] Álgebra del cálculo semántico (8 propiedades, 13 reglas)
- [x] 3 niveles estabilidad: L0/L1/L2
- [x] Prompt del agente = red de preguntas
- [x] Dos sistemas: Motor (fuera) + Gestor (dentro)

### Cartografía + Datos ✅
- [x] 54 análisis (18 INT × 3 casos)
- [x] 18/18 loop tests no-idempotentes
- [x] Saturación n=2 confirmada
- [x] OUTPUT_FINAL compilado
- [x] 1.183 datapoints sintéticos ($1.99)

### Multi-modelo ✅
- [x] 10+ modelos evaluados empíricamente
- [x] Mesa de producción definida: V3.2+V3.1+R1+Cogito
- [x] 5 mecanismos multi-modelo validados (Exp 4 completo)
- [x] 5 tiers de enjambre diseñados (Principio 31)
- [x] Asignación modelo→celda empírica (Tabla §4.1)
- [x] Prompts especializados > genéricos (Exp 4.1)
- [x] Sintetizador = Cogito (Exp 4.2)
- [x] Pizarra funcional para Tier 4 (Exp 4.3)
- [x] Agente de coding OS: 460 líneas, 99% (Exp 6)
- [x] Exp 10 completado (roadmap enjambre, señales extraídas)

### Motor vN 🔧 EN CURSO
- [x] MVP desplegado en fly.io
- [x] 3 casos validados (8.5-9.5/10)
- [ ] Detector de huecos funcional
- [ ] Campo de gradientes sobre input
- [ ] Router por gradiente (modelo OS)
- [ ] Red de preguntas como prompt del agente
- [ ] Verificación de cierre de gaps
- [ ] Telemetría en DB

### Gestor ⬜ POR IMPLEMENTAR (PRIORIDAD #1)
- [x] Arquitectura diseñada
- [x] 3 mecanismos de aprendizaje definidos
- [x] Pipeline del Gestor definido (7 pasos)
- [x] Schema BD completo: 23 tablas + 1 vista materializada (§6.6)
- [x] Programas compilados diseñados (caché Fase A→B)
- [x] Perfil gradientes por consumidor diseñado
- [x] Log de auditoría del Gestor diseñado
- [ ] Crear schema en fly.io Postgres (migrations)
- [ ] Seed desde JSONs cartografía + Exp 4
- [ ] Compilador de programas funcional

### Base de datos 🔧
- [x] Schema 23 tablas diseñado (9 grupos funcionales)
- [x] Vista materializada pregunta_efectividad diseñada
- [x] Memoria del sistema: Fase 1 archivos .md, Fase 2 pgvector (auto-aviso)
- [x] Tablas config (modelos + enjambre) diseñadas
- [x] Observaciones Reactor v4 diseñadas
- [ ] Ejecutar migrations en fly.io Postgres
- [ ] Seed inteligencias + preguntas + grafo + marco
- [ ] Seed config_modelos + config_enjambre desde Exp 4
- [ ] Archivos contexto/ compilados

### Infraestructura 🔧
- [x] fly.io operativo
- [x] PostgreSQL + pgvector
- [x] OpenRouter + DeepSeek API
- [ ] Migración Supabase Fase 1 (~30 agentes 🟢)
- [ ] Migración Supabase Fase 2 (~12 agentes 🟡)
- [ ] Migración Supabase Fase 3 (2 verbalizadores 🔴)
- [ ] Remote git configurado

### Pilotos ⬜ POR INICIAR
- [ ] Exocortex Pilates conectado
- [ ] Exocortex Fisioterapia conectado
- [ ] Reactor v4 activo con datos reales
- [ ] Flywheel validado (transferencia cross-dominio)
- [ ] Interfaz usuario mínima

---

## §11. ROADMAP — ORDEN DE IMPLEMENTACIÓN

### Fase 0: Cirugía (semanas 1-4)

**Objetivo:** base operativa limpia. Una plataforma, un pipeline, sin contradicciones.

| Qué | Por qué | Tiempo | Coste |
|-----|---------|--------|-------|
| Eliminar Chief of Staff (24 agentes) | Contradicción arquitectónica activa | 3 días | €0 |
| Gestor de Matriz básico: tabla efectividad + vista materializada | Sin Gestor no hay aprendizaje | 2 semanas | €0 (código) |
| Motor vN: detector huecos + router + ejecutor multi-modelo | Pipeline end-to-end funcional | 2 semanas | $50/mes tokens |
| Decisión Supabase: migrar tablas críticas (Matriz, datapoints) a fly.io | Una infra, no dos | 1 semana | €150/mes fly.io |

**Entregable:** sistema que recibe caso → detecta gaps → ejecuta con 3 modelos OS → registra efectividad. Sin interfaz bonita. CLI o API.

### Fase 1: MVP con pilotos (meses 1-3)

**Objetivo:** validar con datos reales. Principio 30: come tu propia comida primero.

| Qué | Por qué | Tiempo | Coste |
|-----|---------|--------|-------|
| Pipeline 7 pasos completo | Motor vN end-to-end con evaluador y registrador | 3 semanas | $100/mes |
| Compilador del Gestor | Asigna modelos por celda con datos Exp 4 | 2 semanas | €0 |
| Exocortex Pilates: conectar datos reales (reservas, clientes) | Primer consumidor real del Gestor | 1 semana | $20/mes |
| Exocortex Fisioterapia: conectar datos (agenda, pacientes) | Segundo dominio → validar transferencia cross-dominio | 1 semana | $20/mes |
| Interfaz mínima (chat CLI o web básica) | Poder USAR el sistema, no solo probarlo | 4 semanas | €2-5K dev |
| Reactor v4 básico: observar operaciones reales | Primeras preguntas generadas desde datos reales | 2 semanas | $20/mes |

**Entregable:** Jesús usa el sistema en su estudio de Pilates y su mujer lo usa en la clínica. El sistema detecta cosas que no veían. Los datos alimentan el Gestor.

**Métricas de validación:**
- ≥40% de preguntas generadas cierran gaps reales
- Jesús usa el sistema ≥3x/semana
- ≥1 hallazgo genuino que Jesús no habría visto sin el sistema
- Transferencia cross-dominio: ≥1 pregunta de Pilates útil en Fisio (o viceversa)

### Fase 2: Producto vendible (meses 4-6)

**Objetivo:** algo que un tercero pagaría por usar.

| Qué | Por qué | Tiempo | Coste |
|-----|---------|--------|-------|
| Interfaz web (dashboard + chat) | Usuarios no técnicos | 6 semanas | €5-8K |
| Migración Supabase Fase 1 (~30 agentes) | Reducir deuda técnica | 4 semanas | €0 |
| Auto-mejora nivel 1: fontanería (retry, latencia, patches) | El sistema se mantiene solo | 3 semanas | €0 |
| Modelo de precios: €99/mes básico, €299/mes premium | Validar willingness to pay | 1 semana | €0 |
| Integración TPV/Calendario | Datos de negocio fluyen al sistema | 2 semanas | €500 |
| Presentar resultados reales a terceros | Demostrar valor con datos de Pilates/Fisio | - | €0 |

**Entregable:** producto que un dueño de negocio puede usar. Con datos reales de 2 pilotos como evidencia.

**Condición de éxito:** ≥3 clientes pagando al final del mes 6. Si <3 → pivotar a API para devs.

### Fase 3: Escala controlada (meses 7-12)

**Objetivo:** validar que el flywheel funciona con terceros.

| Qué | Por qué | Tiempo |
|-----|---------|--------|
| Migración Supabase Fase 2-3 | Stack limpio | 3-6 meses |
| Auto-mejora nivel 2: arquitectural (el sistema propone mejoras, CR1 aprueba) | Reducir carga de mantenimiento | Continuo |
| Reactor v2: invertir documentos de 5 verticales | Poblar Matriz con conocimiento de dominio | 3 semanas |
| Integración con software de gestión del amigo informático | Escalar a clientes de terceros | 2 meses |
| Enjambre de código integrado (V3.2+Qwen Coder+Cogito+V3.1+Kimi-Dev) | El sistema implementa sus propias mejoras | 1 mes |
| Programa socios (30% rev share) | Modelo de escala | 1 mes |

**Condición de éxito:** ≥10 clientes pagando. Flywheel demostrado: datos de cliente A mejoran servicio de cliente B.

### Costes estimados

| Fase | Infra/mes | Desarrollo | Tokens/mes | Total |
|------|-----------|------------|-----------|-------|
| 0 - Cirugía (1 mes) | €150 | €0 | $50 | ~€200 |
| 1 - MVP (3 meses) | €450 | €2-5K | $140 | ~€3-6K |
| 2 - Producto (3 meses) | €450 | €5-8K | $200 | ~€6-9K |
| 3 - Escala (6 meses) | €900 | €5K | $300 | ~€6K |
| **Total Año 1** | **~€2K** | **€12-18K** | **~$700** | **€15-24K** |

---

## §12. PRINCIPIOS DE DISEÑO

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es intercambiable. La Matriz es permanente. ✅ 3 modelos OS superan a Claude bajo las mismas preguntas.
2. **Percibir antes de razonar.** Campo de gradientes primero. Sin saber qué funciones están débiles, el routing es ciego.
3. **Cada herramienta hace lo que mejor sabe.** LLMs generan. Embeddings buscan. Grafos optimizan. Código calcula.
4. **El motor no tiene opinión.** Selecciona preguntas, ejecuta, devuelve lo que emerge.
5. **Empujar, no reaccionar.** Mide gap → empuja hacia objetivo → verifica cierre.
6. **Las lentes y funciones no son independientes.** Salud sin Sentido = frágil. Captar sin Depurar = acumulando basura.
7. **Menos es más.** 4 inteligencias sobre gaps grandes > 18 sobre todo.
8. **Retroalimentación con coordenadas.** Cada ejecución registra qué gaps cerró. Selección natural.
9. **Profundidad progresiva.** Base para todo. Profunda donde requiere. Experta con uso real.
10. **Las 8 operaciones son gramática, no diccionario.** Se generan preguntas desde raíces × operaciones.
11. **La raíz es invariante, el sufijo es operación.** El motor opera sobre raíces.
12. **Patología = conectividad, no cantidad.** Errores encadenados = patología. Aislados = señales.
13. **Las preguntas son combustible infinito.** Los datos se agotan. Las preguntas generan datos.
14. **Todo texto experto es preguntas comprimidas.** El Reactor v2 las recupera.
15. **Las preguntas se pueden razonar.** El meta-motor las evoluciona.
16. **La Matriz es el esqueleto.** Unifica percepción, razonamiento, almacenamiento y aprendizaje.
17. **El sistema se ve a sí mismo.** Propiocepción con la misma resolución que usa para el usuario.
18. **Volumen barato antes que calidad cara.** OS masivamente. Premium solo evalúa (y se reemplaza).
19. **El protocolo se entrena a sí mismo.** Meta-protocolo optimiza con datos, no intuición.
20. **Robustez > rendimiento pico.** Preguntas que cierran gaps con modelo débil > las que solo funcionan con fuerte.
21. **Modelos diferentes cubren celdas diferentes.** Diversidad de modelos = dimensión algebraica. ✅ V3.1 domina Frontera, GPT-OSS domina Depurar, R1 domina Continuidad.
22. **Dos loops, dos cadencias.** Motor (minutos, fuera, ejecuta). Gestor (horas, dentro, optimiza).
23. **El Gestor compila, los consumidores ejecutan.** Nadie selecciona preguntas por su cuenta.
24. **Conocimiento transversal > siloado.** Lo que Pilates descubre puede aplicar a Clínica si el patrón de gaps es similar.
25. **OS-first.** Stack 100% open source como objetivo. Dependencia premium = fragilidad.
26. **Si el usuario no lo lee, migra a OS.** Trabajo interno no necesita premium.
27. **El sistema se mejora a sí mismo.** Enjambre de código implementa mejoras. Jesús aprueba (CR1).
28. **Cada cliente hace al sistema mejor para todos.** Reactor v4 + Gestor = flywheel.
29. **Come tu propia comida primero.** Pilotar con negocios propios antes de vender.
30. **Rápido y profundo no existe.** 5 velocidades para 5 contextos. La calidad no se negocia — se agenda. ✅ Exp 4 = Tier 4 (batch nocturno).
31. **El enjambre es una red neuronal de LLMs.** La Matriz = pesos. El Gestor = entrenamiento. Los modelos son fungibles. La topología es el producto. ✅ Estigmergia validada con referencias cruzadas entre modelos.
32. **Ponderar votos por nivel de contexto.** Un modelo con 45k tokens de contexto no anula evidencia de 34 chats empíricos. ✅ Exp 10: "Dunning-Kruger del enjambre" confirmado — modelos con menos contexto recomiendan eliminar lo que no vieron.

---

## §13. HORIZONTE (sin fechas, sin plan)

Conceptos con potencial que aún no tienen datos empíricos. Se activan cuando la evidencia lo justifique.

**Fábrica de Exocortex autónoma:** el sistema diseña, implementa y despliega exocortex nuevos sin intervención. Pipeline: Gestor evalúa preguntas transferibles → Reactor v2 invierte documentos del sector → enjambre de código diseña e implementa (Cogito spec, V3.2 pipeline, Qwen Coder endpoints, V3.1 migraciones) → auto-deploy staging → regresión → CR1 → prod. Tiempo estimado por exocortex: horas, coste ~$0.50-2 en tokens. Requiere: enjambre de código validado + Gestor funcional + pipeline staging/regresión. Estimación: post Fase 2.

**Auto-evolución nivel 3:** el sistema modifica su propia arquitectura, no solo sus parámetros. Requiere: confianza en base estable + control CR1 robusto. Riesgo: un sistema que se modifica solo sin control humano no es vendible.

**Meta-motor:** razonamiento sobre preguntas para generar preguntas que ningún humano formularía (17 tipos de pensamiento aplicados a las preguntas mismas). Requiere: Gestor funcional + datos de efectividad suficientes para que el meta-razonamiento tenga input útil.

**Reactor v3 a escala:** 9 categorías de generación conceptual (~$10-18). 1 ejemplo validado (Sistémica). Genera preguntas desde fundamentos teóricos. Menor prioridad que v4 (datos reales). Produce ~3.000-5.000 preguntas con coordenadas + fuente teórica.

**17 tipos de pensamiento como selección explícita:** hoy los tipos de pensamiento se activan implícitamente por las preguntas. Selección explícita de Inteligencia × Pensamiento × Modo como configuración de un paso. Espacio teórico: 18 × 17 × 6 = 1.836 configuraciones. Espacio útil estimado: ~180.

**Profundidad progresiva de preguntas:**
```
NIVEL BASE (~50 preguntas):    Genéricas. Origen: Cartografía.
NIVEL PROFUNDA (~150/sub-dominio): Especialista. Origen: Reactor v2 + documentos.
NIVEL EXPERTA (~300+/sub-dominio): 20 años experiencia. Origen: Manuales invertidos.
```

---

## §14. DOCUMENTOS RELACIONADOS

| Documento | Relación | Estado |
|-----------|----------|--------|
| **Este documento** | Fuente de verdad v3 | Activo |
| META_RED_INTELIGENCIAS_CR0.md | 18 inteligencias como redes de preguntas | L1 |
| TABLA_PERIODICA_INTELIGENCIA_CR0.md | 18 álgebras con firmas y puntos ciegos | L1 |
| ALGEBRA_CALCULO_SEMANTICO_CR0.md | Operaciones del cálculo semántico | L0 |
| OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md | Resultados de 34 chats de cartografía | Datos |
| L0_7_FUNCIONES_NUCLEARES.md | Las 7F + 3L que generan la Matriz | L0 |
| L0_5_MECANISMO_UNIVERSAL_VINCULACION.md | Mecanismo universal de mapas | L0 |
| ARQUITECTURA_MECANISMOS_MULTI_MODELO.md | 5 mecanismos validados (Exp 4) | Datos |
| MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md | Leaderboard + roles empíricos | L2 |
| CONTEXTO_SISTEMA.md | Estado legacy Supabase | L2 (deprecándose) |
| MEMORY.md | Estado operativo sistema nervioso | L2 |

**Documentos que este reemplaza (mantener como histórico):**
- SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md
- ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md
- ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md
- CONCLUSIONES_EXP4_SESION_11MAR.md
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md
- SISTEMA_COGNITIVO_OMNI_MIND_v2.md
- ACTUALIZACION_DISENO_V2_SECCIONES_20_22.md

---

**FIN DOCUMENTO MAESTRO v3 — CR0**
