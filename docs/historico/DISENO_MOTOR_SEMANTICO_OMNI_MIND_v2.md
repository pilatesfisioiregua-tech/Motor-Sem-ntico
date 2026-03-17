# DISEÑO MOTOR SEMÁNTICO OMNI-MIND v2 — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-08
**Origen:** v1 (sesión Opus) + decisiones de infraestructura + integración Marco Lingüístico
**Cambios vs v1:** Secciones nuevas 1B, 1C, 1D marcadas con [NUEVO]. Secciones modificadas marcadas con [ACTUALIZADO]. Rest idéntico a v1.
**Dependencias:** PROTOCOLO_CARTOGRAFIA_META_RED_v1.md, META_RED_INTELIGENCIAS_CR0.md, TABLA_PERIODICA_INTELIGENCIA_CR0.md, ALGEBRA_CALCULO_SEMANTICO_CR0.md, MARCO_LINGUISTICO_COMPLETO.pdf

---

## 1. VISIÓN

Un motor que recibe cualquier input en lenguaje natural y genera automáticamente el algoritmo óptimo de inteligencias para procesarlo. No tiene programas fijos — compila un programa nuevo para cada petición desde las primitivas de la Meta-Red.

```
MOTOR v3.3 (actual):
  1 álgebra fija (Estructural) × 4 isomorfismos fijos
  $0.91 | ~293s | programa hardcoded

MOTOR SEMÁNTICO (objetivo):
  N álgebras seleccionadas × operaciones óptimas × modelos híbridos
  ~$0.35-1.50 | ~30-120s | programa generado ad-hoc
```

El motor es infraestructura neutra. Lo que cambia es qué se construye encima:
- Exocortex CEO → analiza decisiones estratégicas
- Exocortex Financiero → analiza y genera para departamentos financieros
- Chat de contenido → genera textos con las inteligencias óptimas para el tema
- Cualquier vertical → mismo motor, distinta selección de inteligencias

---

## 1B. TRES CONCEPTOS FUNDAMENTALES [NUEVO]

El motor opera con tres niveles que se combinan multiplicativamente.

### INTELIGENCIA = qué ves (y qué no puedes ver)

Un sistema de percepción con objetos propios, operaciones propias y un punto ciego estructural. Hay 18 inteligencias, cada una es un "vocabulario de percepción" diferente.

Ejemplo: INT-07 Financiera *ve* flujos, apalancamiento, asimetría de payoffs. *No puede ver* lo que no tiene precio. Esa limitación es lo que la hace útil — ve lo financiero con precisión que ninguna otra tiene, precisamente porque ignora todo lo demás.

Las 18 inteligencias se agrupan en 9 categorías empíricas (derivadas de comportamiento real en 34 chats de cartografía):

| # | Categoría | Inteligencias | Qué comparten |
|---|-----------|---------------|---------------|
| 1 | Cuantitativa | INT-01, INT-02, INT-07 | Operan sobre lo medible |
| 2 | Sistémica | INT-03, INT-04 | Mapean relaciones entre partes |
| 3 | Posicional | INT-05, INT-06 | Ven actores, movimientos, poder |
| 4 | Interpretativa | INT-08, INT-09, INT-12 | Interpretan sentido humano |
| 5 | Corporal-Perceptual | INT-10, INT-15 | Perciben forma encarnada |
| 6 | Espacial | INT-11 | Topología visual (suficientemente distinta) |
| 7 | Expansiva | INT-13, INT-14 | Abren espacio de opciones |
| 8 | Operativa | INT-16 | Construye (única en su función) |
| 9 | Contemplativa-Existencial | INT-17, INT-18 | Operan sobre significado último |

Las categorías sirven para el router: máximo diferencial = combinar inteligencias de categorías *diferentes*. Intra-cluster = redundancia.

### PENSAMIENTO = cómo procesas lo que percibes

Una operación que se ejecuta dentro de una inteligencia o entre inteligencias. Hay 17 tipos en tres familias:

**Interno** (10 tipos — dentro de una álgebra):

| # | Pensamiento | Pregunta | Expresión formal |
|---|-------------|----------|-----------------|
| T01 | Percepción | ¿Qué forma tiene? | iso(S) |
| T02 | Causalidad | ¿Por qué esta forma? | B(iso(S)) |
| T03 | Abstracción | ¿Qué se repite? | iso²(S) |
| T04 | Síntesis | ¿Qué conecta todo? | ∫(isos) |
| T05 | Discernimiento | ¿Qué es único de cada mirada? | A−B |
| T06 | Metacognición | ¿Qué no puedo ver? | crítico(X) |
| T07 | Consciencia epistemológica | ¿Qué forma tiene mi pensamiento? | iso(M) |
| T08 | Auto-diagnóstico | ¿Por qué pienso así? | B(iso(M)) |
| T09 | Convergencia | ¿Qué esencia comparten mis explicaciones? | ∫(M₁|M₂) |
| T10 | Dialéctica | ¿Qué veo tras que otros transformaron mi mirada? | A→B→C→A' |

**Lateral** (7 tipos — cruza el perímetro):

| # | Pensamiento | Qué rompe |
|---|-------------|-----------|
| T11 | Analogía | Perímetro del dominio |
| T12 | Contrafactual | Fijeza de los datos |
| T13 | Abducción | Dirección del razonamiento |
| T14 | Provocación | Coherencia del sistema |
| T15 | Reencuadre | Clase de herramienta |
| T16 | Destrucción creativa | El marco entero |
| T17 | Creación | La premisa de análisis |

**Inter-álgebra** (4 tipos — opera entre inteligencias):

| Expresión | Pensamiento | Qué produce |
|-----------|-------------|-------------|
| ∫(A \| B)(caso) | Síntesis multi-inteligencia | Lo que emerge al cruzar dos sistemas |
| A − B | Complementariedad | Qué puede ver A que B no puede |
| A → B | Meta-explicación | Por qué el razonamiento de A produce la forma que B detecta |
| A(output_B) | Lectura cruzada | Una inteligencia leyendo el output de otra |

### MODO = para qué estás mirando

La postura desde la que operas. Hay 6:

| Modo | Descripción | Inteligencias naturales |
|------|-------------|------------------------|
| ANALIZAR | Descomponer, demostrar, medir | INT-01, INT-02, INT-07 |
| PERCIBIR | Ver patrones, detectar forma | INT-03, INT-04, INT-15 |
| MOVER | Actuar, posicionar, construir | INT-05, INT-16, INT-10 |
| SENTIR | Empatizar, intuir, habitar | INT-08, INT-10, INT-18 |
| GENERAR | Crear, imaginar, proyectar | INT-14, INT-12, INT-13 |
| ENMARCAR | Nombrar, negociar, dar sentido | INT-09, INT-06, INT-17 |

No toda inteligencia opera bien en todos los modos. INT-07 analiza naturalmente, genera forzadamente. INT-18 siente naturalmente, analiza contra natura.

### Cómo se combinan

```
Configuración de un paso = Inteligencia × Pensamiento × Modo

INT-07 (Financiera) × T12 (Contrafactual) × ANALIZAR
= "¿Qué pasa con el flujo de caja si los ingresos caen un 30%?"

INT-08 (Social) × T01 (Percepción) × SENTIR  
= "¿Qué emoción domina esta persona que nadie nombra?"

INT-14 (Divergente) × T14 (Provocación) × GENERAR
= "¿Y si hace exactamente lo contrario de lo que planea?"
```

Espacio teórico: 18 × 17 × 6 = 1.836 configuraciones/paso.
Espacio útil (acotado por compatibilidad y redundancia): ~180.

**Para el MVP:** el motor selecciona inteligencia + modo. Los tipos de pensamiento se activan implícitamente por las preguntas de cada red. En v2, el compilador selecciona los tres explícitamente.

---

## 1C. RELACIÓN CON EL MOTOR v3.3 [NUEVO]

El Motor v3.3 usa 1 álgebra (Estructural/IAS) con 4 isomorfismos fijos y 7 primitivas sintácticas. El motor semántico usa 18 álgebras con operaciones dinámicas.

**Lo que se reusa del v3.3:**

| Pieza v3.3 | Dónde va en el motor semántico |
|------------|-------------------------------|
| 7 primitivas sintácticas (sustantivizar, adjetivar, etc.) | Capa 0: Detector de Huecos (pre-filtro antes del router) |
| 4 isomorfismos (contenedores, circuitos, tablero, control) | Las 4 lentes de INT-03 Estructural |
| Calculadora de gaps id↔ir | Código puro dentro de INT-03, $0 |
| Patrón de pipeline por capas (parsear → cruzar → proyectar → integrar) | La meta-red de 6 pasos que usan las 18 inteligencias |

El v3.3 entero se encapsula como INT-03 dentro del motor semántico. No se tira — se reduce a una inteligencia más de 18.

---

## 1D. GRAMÁTICA GENERATIVA DE PREGUNTAS — MARCO LINGÜÍSTICO [NUEVO]

### El descubrimiento

Las 18 inteligencias tienen redes de preguntas escritas a mano (Capa 1 de preguntas de contenido). El Marco Lingüístico (MARCO_LINGUISTICO_COMPLETO.pdf) demuestra que estas preguntas NO son arbitrarias — están construidas con 8 operaciones sintácticas universales. Las mismas operaciones que usa el lenguaje para construir oraciones, el motor las usa para construir preguntas.

### Las 8 operaciones primitivas (Aritmética Sintáctica)

| # | Operación | Input → Output | Qué detecta | Ejemplo motor |
|---|-----------|---------------|-------------|---------------|
| 1 | **Modificación** | adj + sust → sust' | Cualidades, grado | "¿Cuán frágil es la solvencia?" |
| 2 | **Predicación** | sust + verbo → oración | Estado o acción | "¿El sistema ES solvente?" / "¿El sistema ESTRUCTURA?" |
| 3 | **Complementación** | adv + verbo → verbo' | Instrumento, modo | "¿CON QUÉ instrumento observa?" |
| 4 | **Transitividad** | verbo + sust → predicado | Objeto de la acción | "¿SOBRE QUÉ actúa?" (verbo sin objeto = hueco) |
| 5 | **Subordinación** | oración + oración → oración' | Causa, condición, creencias | "¿PORQUE qué?" / "¿SI qué cambiaría?" / "¿Qué ASUME?" |
| 6 | **Cuantificación** | det + sust → sust_acotado | Alcance, límites | "¿CUÁNTO?" / "¿TODO o ALGUNO?" |
| 7 | **Conexión** | X + conj + X → X' | Tipo de acople | "¿Y/PERO/AUNQUE/PORQUE/SI/PARA?" |
| 8 | **Transformación** | X → Y | Cambio de categoría | verbo→sustantivo, estado→cualidad |

### Propiedades algebraicas de las operaciones

- Modificación: idempotente para mismo adjetivo, apilable para distintos
- Predicación: no conmutativa ("el sistema estructura" ≠ "¿estructura el sistema?")
- Conexión Y: conmutativa ("estructura y regulación" = "regulación y estructura")
- Conexión PORQUE: no conmutativa (causalidad tiene dirección)
- Conexión PERO: no asociativa ("(A pero B) pero C" ≠ "A pero (B pero C)")
- Transformación: no involutiva (pierde información: "rigor"→"rigorizar" no existe)

### Los 6 tipos de acople (Conexión tipificada)

| Conjunción | Tipo de acople | Qué revela | Diagnóstico |
|------------|---------------|------------|-------------|
| Y | Sinergia | Ambas operan juntas | Salud |
| PERO | Tensión | Una limita a la otra | Fricción activa |
| AUNQUE | Concesión | Tolera algo que no debería | Grieta |
| PORQUE | Causalidad | Dependencia dirigida | Cadena causal |
| SI | Condicionalidad | Requiere condición | Fragilidad |
| PARA | Finalidad | Orientación | Dirección |

Diagnóstico por perfil: Dominado por condicionales = rígido. Dominado por concesivas = fugas. Sin causales = sin dirección.

### Las 9 capas del sistema (constituyentes sintácticos)

Cada capa de un sistema corresponde a un constituyente sintáctico distinto:

| # | Capa | Categoría gramatical | Pregunta | Verbo existencial |
|---|------|---------------------|----------|-------------------|
| 1 | LENTES | Atributo de estado | ¿En qué estado está? | ESTAR |
| 2 | CUALIDADES | Adjetivo predicativo | ¿Cómo es? | SER |
| 3 | CREENCIAS | Subordinada asertiva | ¿Qué asume? | ASUMIR |
| 4 | REGLAS | Modal deóntico | ¿Qué debe hacer? | DEBER |
| 5 | FUNCIONES | Verbo de acción | ¿Qué hace? | HACER |
| 6 | OPERADORES | Complemento circunstancial | ¿Con qué observa? | OBSERVAR |
| 7 | CONTEXTO | Circunstancial lugar/tiempo | ¿Dónde/cuándo opera? | — |
| 8 | ROLES | Pronombre/deíctico | ¿Quién hace qué? | — |
| 9 | ACOPLES | Conjunción | ¿Cómo se vinculan las piezas? | — |

### Las falacias aritméticas (errores de tipo lógico)

Errores que el motor puede detectar en el input o en su propio output:

| Falacia | Operación incorrecta | Corrección |
|---------|---------------------|------------|
| Conducta → Valor | Predicación tratada como Modificación | Pred → Sub_asertiva → Mod |
| Optimización sin finalidad | Transformación sin Subordinación final | Tr + Sub_final(PARA qué) |
| Fricción = Fallo | Conexión PERO asumida como error | Evaluar si PERO es funcional |
| Creencia como Regla | Sub_asertiva confundida con Sub_deóntica | Distinguir "creo que X" de "X debe ser" |
| Cualidad como Función | Modificación confundida con Predicación | "Es innovador" ≠ "innova" |
| Verbo sin objeto | Predicación sin Transitividad | Función declarada pero no definida |

### Raíz pre-categorial × Sufijo como operación

El hallazgo más potente del Marco: la raíz es pre-categorial. No es verbo, ni sustantivo, ni adjetivo. El sufijo determina en qué tipo se manifiesta.

```
EQUILIBRI- (raíz pura)
  + -ar   → equilibrar   (verbo/función)     → "¿El sistema EQUILIBRA?"
  + -o    → equilibrio    (sustantivo/recurso) → "¿Tiene EQUILIBRIO?"
  + -ado  → equilibrado   (adjetivo/estado)    → "¿Está EQUILIBRADO?"
  + -mente→ equilibradamente (adverbio/operador) → "¿Opera CON equilibrio?"
```

### Implicación para el motor: 3 niveles de preguntas

**Nivel 1 — Preguntas fijas (hoy):**
Las 18 redes de preguntas escritas a mano en la Capa 1 de contenido. Funcionan. Se usan en el MVP.

**Nivel 2 — Preguntas generadas por operación (v2):**
Las 8 operaciones × raíces de dominio generan preguntas nuevas para cualquier dominio sin cartografía manual.

```
INTELIGENCIA = RAÍCES DE DOMINIO × 8 OPERACIONES

INT-07 Financiera:
  Raíces: flujo, riesgo, valor, margen, deuda, opcionalidad
  × Predicación: "¿El flujo ES positivo?" 
  × Transitividad: "¿El flujo DEPENDE DE quién?"
  × Subordinación: "¿PORQUE qué el margen es bajo?"
  × Cuantificación: "¿CUÁNTO riesgo?"
  × Conexión: "Flujo positivo PERO deuda alta"
  → genera TODAS las preguntas financieras posibles
```

**Nivel 3 — Meta-preguntas (meta-motor, v3+):**
Los 17 tipos de pensamiento aplicados a las preguntas mismas (sección 21 de v1, reactor v2).

### Relación con la Capa 0 (Detector de Huecos)

Las 7 primitivas del v3.3 y las 8 operaciones del Marco son el mismo fenómeno visto desde dos ángulos:

| Primitiva v3.3 | Operación Marco | Qué detecta |
|----------------|-----------------|-------------|
| Sustantivizar | Transformación → sustantivo | Qué nombres faltan |
| Adjetivar | Modificación | Qué cualificaciones faltan |
| Adverbializar | Complementación | Cómo opera realmente |
| Verbo | Predicación | Qué acción nuclear hay |
| Preposicionar | Transitividad + Subordinación | Qué relaciones faltan |
| Conjuntar | Conexión | Qué acoples asume sin verificar |
| Sujeto-predicado | Predicación + Cuantificación | Quién tiene poder |

La Capa 0 del motor usa ambas perspectivas: las primitivas detectan huecos en el input, las operaciones clasifican qué tipo de hueco es para informar al router.

---

## 2. ARQUITECTURA — 4 CAPAS (pipeline: 7 subcapas) [ACTUALIZADO]

### Las 4 capas conceptuales

```
┌─────────────────────────────────────────────────┐
│  CAPA 4: INTERFAZ                               │
│  Chat / API / Exocortex                         │
│  Recibe input del usuario, devuelve output       │
├─────────────────────────────────────────────────┤
│  CAPA 3: EJECUCIÓN                              │
│  LLMs (Haiku/Sonnet/Opus) + Calculadoras +      │
│  Simuladores — ejecuta los prompts generados     │
├─────────────────────────────────────────────────┤
│  CAPA 2: COMPILADOR                             │
│  Detector Huecos + Router + Compositor +         │
│  Generador — compila el algoritmo óptimo         │
├─────────────────────────────────────────────────┤
│  CAPA 1: BASE DE DATOS DE EFECTOS               │
│  Cartografía + Marco Lingüístico + Datos reales  │
│  El conocimiento de qué produce cada combinación │
└─────────────────────────────────────────────────┘
```

### El pipeline de ejecución (7 subcapas)

```
INPUT (texto del usuario)
         │
         ▼
┌─────────────────────────┐
│  CAPA 0: DETECTOR HUECOS│  ~200ms | $0
│  7 primitivas + 8 ops   │
│  → Qué falta en el input│
│  → Huecos informan router│
│  → Falacias aritméticas │
│  (código puro)          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 1: ROUTING        │  ~2-5s | ~$0.02-0.05
│  Sonnet (MVP) o embeds  │
│  → Top-K inteligencias  │
│  → Informado por huecos │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 2: COMPOSICIÓN    │  ~100ms | $0
│  Grafo en memoria       │
│  → Algoritmo óptimo     │
│  → 13 reglas compilador │
│  (NetworkX/código puro) │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 3: GENERACIÓN     │  ~50ms | $0
│  Meta-Red + 8 operaciones│
│  → Prompts exactos      │
│  → Cada pregunta = op   │
│  (código puro)          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 4: EJECUCIÓN      │  30-120s | $0.30-0.80
│  Haiku: extracción      │
│  Sonnet: integración    │
│  Opus: frontera         │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 5: EVALUACIÓN     │  ~50ms | $0
│  Scorer heurístico      │
│  + Detección falacias   │
│  Si score < umbral:     │
│    → relanzar           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 6: INTEGRACIÓN    │  10-20s | ~$0.10-0.20
│  Sonnet: síntesis final │
│  → Output al usuario    │
│  → Log para telemetría  │
└─────────────────────────┘

TOTAL: ~$0.35-1.00 | ~40-150s
```

---

## 3. INFRAESTRUCTURA [ACTUALIZADO]

### Decisiones cerradas (CR1 2026-03-08)

| Decisión | Elegido | Razón |
|----------|---------|-------|
| Motor + DB | **fly.io Postgres + pgvector** | Colocalizada, sin dependencias externas |
| Exocortex Pilates | **fly.io (nuevo)** | Se crea de cero, misma esencia (estigmergia), sin límite funciones |
| Exocortex Clínica | **fly.io (nuevo)** | Igual |
| Supabase | **Se depreca gradualmente** | 402 incluso con upgrade. El cerebro viejo sigue hasta que los nuevos lo reemplacen |

### Qué se mantiene de la arquitectura Supabase

| Patrón | Se lleva a fly.io | Cómo |
|--------|-------------------|------|
| Estigmergia | Tabla `marcas_estigmergicas` | Mismo esquema en Postgres fly.io |
| Enjambres | Tabla `enjambres` + `estado_agentes` | Mismo esquema |
| Telemetría | Tabla `métricas` | Mismo esquema |
| Mejora continua | Tablas `reglas_deteccion`, `propuestas_mejora` | Mismo esquema |
| Fire-and-forget | pg_net (Supabase-specific) | Workers/colas en fly.io |
| Cron integrado | Supabase cron | node-cron o cron de Linux |
| Auth | Supabase Auth | JWT si se necesita |

El 95% se lleva tal cual. Se reemplazan 4 piezas de fontanería.

### Stack técnico completo

```
INFRAESTRUCTURA:
  fly.io               — Motor + Exocortex + todo
  fly.io Postgres      — DB motor (efectos, inteligencias, Marco, telemetría)
                       — DB exocortex (marcas, agentes, estado)

MODELOS LLM:
  Anthropic API        — Haiku, Sonnet, Opus (4 keys rotativas)

MODELOS NO-LLM (v2):
  Voyage API           — Embeddings
  scikit-learn         — Clasificador, Scorer
  NetworkX + scipy     — Grafo compositor
  numpy                — Calculadoras

INTERFAZ:
  API REST             — Motor expone endpoints
  Por decidir          — Chat/app que consume la API

DATOS:
  Meta-Red             — 18 inteligencias como redes de preguntas
  Marco Lingüístico    — 8 operaciones, 9 capas, 6 acoples, falacias (JSON en DB)
  DB de efectos        — Cartografía + datos reales (crece)
  Estado usuario       — Contexto acumulado por usuario
```

---

## 4-9. FASES A-F

[Sin cambios respecto a v1. Las fases A (Cartografía, completada), B (Datos sintéticos), C (Entrenamiento), D (Motor v1), E (Interfaz/Exocortex), F (Pilotos) mantienen la misma descripción, sub-fases, outputs esperados y criterios de cierre.]

**Excepción — Fase D pipeline: ver sección 2 actualizada con Capa 0.**

**Excepción — Fase D DB: ver sección de esquema DB actualizada abajo.**

---

## 10-14. MODELOS, STACK, DEPENDENCIAS, TEMPORAL, PRESUPUESTO

[Sin cambios respecto a v1, excepto que donde dice "Supabase PostgreSQL" ahora dice "fly.io Postgres".]

---

## 15. ESQUEMA DE BASE DE DATOS [ACTUALIZADO]

### DB Motor (fly.io Postgres)

```sql
-- ==========================================
-- INTELIGENCIAS Y META-RED
-- ==========================================

CREATE TABLE inteligencias (
    id TEXT PRIMARY KEY,              -- 'INT-01', 'INT-02', ...
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,          -- 'cuantitativa', 'sistémica', etc. (9 categorías)
    firma TEXT NOT NULL,
    punto_ciego TEXT NOT NULL,
    objetos_exclusivos TEXT[],
    raices_dominio TEXT[],            -- [NUEVO] raíces pre-categoriales de esta inteligencia
    preguntas JSONB NOT NULL,         -- red completa de preguntas por paso
    modos_naturales TEXT[],           -- [NUEVO] modos donde opera bien: ['analizar','percibir',...]
    modos_forzados TEXT[]             -- [NUEVO] modos donde opera mal
);

CREATE TABLE aristas_grafo (
    id SERIAL PRIMARY KEY,
    origen TEXT REFERENCES inteligencias(id),
    destino TEXT REFERENCES inteligencias(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('composicion', 'fusion', 'diferencial')),
    peso FLOAT NOT NULL,
    direccion_optima TEXT,
    hallazgo_emergente TEXT,
    UNIQUE(origen, destino, tipo)
);

-- Vectores para router futuro (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);

-- ==========================================
-- MARCO LINGÜÍSTICO (datos operativos)
-- ==========================================

-- Las 8 operaciones primitivas
CREATE TABLE operaciones_sintacticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,      -- 'modificacion', 'predicacion', etc.
    input_tipo TEXT NOT NULL,         -- 'adj + sust', 'sust + verbo', etc.
    output_tipo TEXT NOT NULL,
    propiedad_clave TEXT NOT NULL,    -- 'filtra/especifica', 'genera valor de verdad', etc.
    pregunta_detectora TEXT NOT NULL, -- '¿Cómo es?', '¿Qué hace?', etc.
    propiedades_algebraicas JSONB     -- idempotente, conmutativa, etc.
);

-- Las 9 capas del sistema (constituyentes sintácticos)
CREATE TABLE capas_sistema (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,      -- 'lentes', 'cualidades', 'creencias', etc.
    categoria_gramatical TEXT NOT NULL,
    pregunta TEXT NOT NULL,           -- '¿En qué estado está?', '¿Cómo es?', etc.
    verbo_existencial TEXT,           -- 'ESTAR', 'SER', 'HACER', etc.
    operacion_primaria TEXT REFERENCES operaciones_sintacticas(nombre)
);

-- Los 6 tipos de acople
CREATE TABLE tipos_acople (
    id SERIAL PRIMARY KEY,
    conjuncion TEXT UNIQUE NOT NULL,  -- 'Y', 'PERO', 'AUNQUE', 'PORQUE', 'SI', 'PARA'
    tipo TEXT NOT NULL,               -- 'sinergia', 'tension', 'concesion', etc.
    diagnostico TEXT NOT NULL         -- qué revela este tipo de acople
);

-- Falacias aritméticas (errores de tipo lógico)
CREATE TABLE falacias_aritmeticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    operacion_incorrecta TEXT NOT NULL,
    correccion TEXT NOT NULL,
    ejemplo TEXT
);

-- Mapeo sufijo → operación → capa (para Capa 0)
CREATE TABLE sufijos_operaciones (
    id SERIAL PRIMARY KEY,
    sufijo TEXT NOT NULL,             -- '-ar', '-oso', '-ado', '-mente', '-ción', etc.
    transforma_en TEXT NOT NULL,      -- 'verbo', 'adjetivo_propiedad', 'adjetivo_estado', etc.
    capa_destino TEXT REFERENCES capas_sistema(nombre)
);

-- ==========================================
-- TELEMETRÍA Y RETROALIMENTACIÓN
-- ==========================================

CREATE TABLE ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    huecos_detectados JSONB,          -- [NUEVO] output de Capa 0
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,        -- [NUEVO] falacias encontradas por Capa 5
    feedback_usuario JSONB
);
```

---

## 16-18. FILTRO, PROFUNDIDAD PROGRESIVA, PREGUNTAS POR NIVEL

[Sin cambios respecto a v1.]

---

## 19. PROTOCOLO DE DOCUMENTACIÓN Y CHECKLIST

[Sin cambios respecto a v1.]

---

## 20. REACTOR SEMÁNTICO

[Sin cambios respecto a v1.]

---

## 21. META-MOTOR — RAZONAMIENTO SOBRE PREGUNTAS [ACTUALIZADO]

### Conexión con el Marco Lingüístico

El meta-motor de v1 proponía que los 17 tipos de pensamiento operasen sobre preguntas. El Marco Lingüístico aporta el **mecanismo concreto**: las 8 operaciones aplicadas a las preguntas mismas.

```
REACTOR v1 (sección 20):
  Preguntas fijas → datos → modelos → más datos
  Las preguntas no cambian. Los datos crecen.

REACTOR v2 (con Marco):
  Raíces × 8 operaciones → preguntas → datos
  → 17 pensamientos × preguntas → preguntas mejores
  → raíces × 8 ops refinadas → preguntas aún mejores
  Las preguntas TAMBIÉN evolucionan. Doble amplificación.
```

El Marco da la gramática generativa. Los 17 pensamientos dan los meta-operadores. Juntos = reactor v2 completo.

---

## 22. PRINCIPIOS DE DISEÑO [ACTUALIZADO]

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es interchangeable. La Meta-Red es permanente.

2. **Cada modelo hace lo que mejor sabe.** LLMs para generar y sintetizar. Embeddings para buscar. Grafos para optimizar. Código para calcular.

3. **El motor no tiene opinión.** Selecciona inteligencias, ejecuta preguntas, devuelve lo que emerge. No prescribe.

4. **Menos es más.** 4 inteligencias bien seleccionadas > 18 mal combinadas. El diferencial es la herramienta de poda.

5. **Retroalimentación continua.** Cada ejecución es un datapoint.

6. **Validación antes de expansión.** No añadir inteligencias, dominios ni features hasta que lo existente demuestre valor con datos reales.

7. **Profundidad progresiva.** Base para todo. Profunda donde el dominio lo requiere. Experta donde el uso real demuestra déficit.

8. **Tres capas de primitivas.** Inteligencia × Pensamiento × Modo. La expresividad es multiplicativa, no aditiva.

9. **No adivinar, preguntar.** Cuando el input es ambiguo, el motor genera las preguntas que le faltan.

10. **Si no hay registro, no existe.** Cada implementación genera checklist + documento de registro.

11. **Las preguntas son el combustible, no los datos.** Los datos se agotan. Las preguntas generan datos nuevos infinitamente.

12. **Todo texto experto es preguntas comprimidas.** La abducción las recupera.

13. **Las preguntas se pueden razonar.** Los mismos tipos de pensamiento operan sobre preguntas. El meta-motor las evoluciona.

14. **[NUEVO] Las 8 operaciones son la gramática, no el diccionario.** No se necesitan listas cerradas de preguntas por inteligencia. Se necesita dominar las 8 operaciones generativas. Los elementos se GENERAN desde raíces × operaciones.

15. **[NUEVO] La raíz es invariante, el sufijo es operación.** El mismo concepto se manifiesta como estado, cualidad, acción, instrumento según qué operación apliques. El motor opera sobre raíces — las manifestaciones son derivadas.

16. **[NUEVO] La patología no es la cantidad de errores, es la conectividad.** Errores aislados = señales. Errores encadenados = patología. La Capa 5 busca cadenas, no puntos.

---

**FIN DISEÑO MOTOR SEMÁNTICO OMNI-MIND v2 — CR0**
