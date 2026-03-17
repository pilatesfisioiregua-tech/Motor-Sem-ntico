# SISTEMA COGNITIVO OMNI-MIND — Documento Maestro v2

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-09
**Origen:** Evolución del Diseño Motor Semántico v1, integración con Sistema Nervioso (Supabase)
**Supersede:** DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md

---

## 1. QUÉ ES

Un organismo cognitivo que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas fijos — es un sistema vivo que compila un programa cognitivo nuevo para cada interacción, navega un espacio de preguntas adaptativamente, y acumula conocimiento estructurado con cada uso.

Tiene dos subsistemas integrados:

```
SISTEMA NERVIOSO (Supabase)
  Percibe: parsea input, detecta intención, acumula contexto
  Coordina: estigmergia entre agentes, cola de mejoras, semillas
  Evoluciona: telemetría, propiocepción, mejora continua
  Conversa: Chief of Staff, interfaz con el usuario

MOTOR COGNITIVO (fly.io)
  Diagnostica: mapea el input a la Matriz 3L×7F
  Razona: ejecuta inteligencias sobre celdas prioritarias
  Aprende: reactor v2 invierte documentos, reactor v1 amplifica datos
  Evalúa: scorer + verificación de cobertura funcional
```

El Motor Cognitivo es el cerebro profundo. El Sistema Nervioso es la interfaz y coordinación. Juntos forman un organismo.

**Lo que cambia respecto a v1:** El routing deja de ser "qué inteligencia aplico" y pasa a ser "qué necesidades funcionales tiene este sistema y quién las cubre". La Matriz 3L×7F es el esquema que unifica percepción, razonamiento, almacenamiento y aprendizaje.

---

## 2. LA MATRIZ — 3 LENTES × 7 FUNCIONES × 18 INTELIGENCIAS

### El esquema central

Todo lo que el sistema percibe, analiza, almacena y aprende se organiza en una estructura de tres dimensiones:

```
DIMENSIÓN 1 — 3 LENTES (para qué):
  Salud:       ¿El sistema funciona?
  Sentido:     ¿El sistema tiene dirección?
  Continuidad: ¿El patrón sobrevive más allá del sistema?

DIMENSIÓN 2 — 7 FUNCIONES (qué necesita):
  F1 Conservar:   Mantener forma contra fuerzas
  F2 Captar:      Meter lo que necesita
  F3 Depurar:     Sacar lo que sobra
  F4 Distribuir:  Repartir donde y cuando toca
  F5 Frontera:    Distinguir propio de ajeno
  F6 Adaptar:     Responder al cambio
  F7 Replicar:    Copiar el patrón

DIMENSIÓN 3 — 18 INTELIGENCIAS (quién lo ve):
  INT-01 a INT-18, cada una con su firma, objetos exclusivos y punto ciego
```

Esto produce una estructura de **378 posiciones** (3 × 7 × 18). Cada pregunta, cada hallazgo, cada efecto conocido tiene coordenadas exactas en este espacio.

### Las 21 celdas como campo de gradientes

Cada celda NO es on/off. Tiene un **grado** (0.0-1.0) que mide cuánto está cubierta esa función en esa lente para el caso en cuestión. Y ese grado tiene un **objetivo** que depende del contexto — no todas las celdas necesitan estar al máximo para todos los casos.

```
               Salud              Sentido             Continuidad
            actual→objetivo    actual→objetivo      actual→objetivo
F1 Conservar  0.7 → 0.9         0.2 → 0.8           0.1 → 0.5
F2 Captar     0.8 → 0.9         0.3 → 0.7           0.0 → 0.3
F3 Depurar    0.2 → 0.9         0.1 → 0.8           0.0 → 0.4
F4 Distribuir 0.5 → 0.8         0.4 → 0.7           0.1 → 0.5
F5 Frontera   0.3 → 0.9         0.1 → 0.9           0.2 → 0.6
F6 Adaptar    0.6 → 0.8         0.3 → 0.7           0.1 → 0.5
F7 Replicar   0.4 → 0.6         0.2 → 0.5           0.0 → 0.8
```

La **diferencia** entre grado actual y objetivo es el **gradiente** — la fuerza que dirige la interacción. El sistema no reacciona a "celdas débiles". Empuja activamente hacia el grado objetivo en cada celda. Las celdas con mayor gap reciben más atención.

### Relaciones entre lentes

Las 3 lentes NO son independientes. Se condicionan mutuamente:

- **Salud sin Sentido** = sistema que funciona pero no va a ningún sitio. La Salud es frágil porque bajo presión no hay dirección que la sostenga.
- **Sentido sin Salud** = dirección sin capacidad de ejecutar. Visión que nunca aterriza.
- **Sentido sin Continuidad** = dirección que muere contigo. No sobrevive.
- **Continuidad sin Sentido** = replicar sin propósito. Copiar vacío.

El diagnóstico ve estas dependencias. Si Salud está alta pero Sentido está a cero, la evaluación real de Salud baja — porque es una Salud sostenida solo por inercia, no por dirección.

### Relaciones entre funciones

Las 7 funciones también tienen dependencias:

- **F2 Captar sin F3 Depurar** = acumular basura. Todo entra, nada sale.
- **F4 Distribuir sin F5 Frontera** = repartir a quien no toca. Fugas.
- **F1 Conservar sin F6 Adaptar** = rigidez. Mantiene forma pero se rompe ante cambio.
- **F7 Replicar sin F5 Frontera** = copiar sin saber qué es esencial y qué no. Replicar ruido.

El diagnóstico detecta estas dinámicas. Una función puede tener grado alto pero ser frágil porque su función complementaria está baja.

### Cada inteligencia cubre TODA la matriz

No es "INT-07 solo vive en Captar×Salud". Cada inteligencia tiene algo que decir sobre CADA una de las 21 celdas desde su lente particular:

```
INT-07 (Financiera) sobre las 21 celdas:

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

Esto produce el banco de preguntas real: 21 × 18 = **378 preguntas de coordenada** como mínimo, cada una ubicada exactamente en la Matriz. Con niveles profundo y experto, el banco crece a miles de preguntas, todas con coordenadas.

### La Matriz como campo activo

La Matriz no es un mapa estático que se consulta. Es un **campo de gradientes** que dirige la interacción:

**Como campo de fuerza:** Los gaps (diferencia actual→objetivo) generan la fuerza que dirige qué preguntas ejecutar, qué inteligencias activar, y cuánta profundidad aplicar. La interacción fluye hacia donde el gap es mayor.

**Como banco de preguntas con coordenadas:** Cada pregunta tiene posición exacta (inteligencia × lente × función). El compilador no elige "preguntas de INT-07" — elige "preguntas que cubren Depurar×Sentido" y filtra por inteligencia.

**Como base de datos de efectos:** Cada ejecución registra qué celdas llenó y cuánto cerró el gap. Después de 1000 ejecuciones, el sistema sabe que INT-07 cierra Captar×Salud con efectividad 0.85 pero Replicar×Continuidad con 0.12. Conocimiento estructurado.

**Como detector de puntos ciegos:** Celdas donde ninguna inteligencia cierra el gap consistentemente = huecos reales de la Meta-Red. Verificable por datos, no por opinión.

**Como esquema de inversión de documentos:** El Reactor v2 ubica cada pregunta extraída de un paper en la Matriz. Las celdas vacías del paper son sus puntos ciegos. Las preguntas generadas desde esas celdas son lo que el paper no pregunta.

**Como verificador de cierre:** La evaluación no es "¿se ejecutaron las preguntas?" sino "¿se cerró el gap?". Si después de ejecutar INT-07 sobre Depurar×Sentido el grado sigue igual, la pregunta falló. Escalar: otra inteligencia, otra profundidad, otra formulación.

### Implementación de la Matriz en DB

```sql
-- Banco de preguntas con coordenadas
CREATE TABLE preguntas_matriz (
  id TEXT PRIMARY KEY,
  inteligencia TEXT NOT NULL,      -- INT-01..INT-18
  lente TEXT NOT NULL,             -- salud | sentido | continuidad
  funcion TEXT NOT NULL,           -- F1..F7
  pensamiento TEXT,                -- T01..T17 (opcional)
  modo TEXT,                       -- analizar|percibir|mover|sentir|generar|enmarcar
  nivel TEXT DEFAULT 'base',       -- base | profunda | experta
  sub_dominio TEXT,                -- null para base, específico para profunda/experta
  texto TEXT NOT NULL,
  fuente TEXT,                     -- cartografia | sintetico | reactor_v2 | experto
  score_efectividad FLOAT,        -- se actualiza con uso real
  gap_medio_cerrado FLOAT         -- cuánto gap cierra esta pregunta en promedio
);

-- Efectos registrados con coordenadas
CREATE TABLE efectos_matriz (
  id SERIAL PRIMARY KEY,
  ejecucion_id TEXT NOT NULL,
  inteligencia TEXT NOT NULL,
  lente TEXT NOT NULL,
  funcion TEXT NOT NULL,
  hallazgo TEXT,
  grado_antes FLOAT,              -- grado de la celda antes de ejecutar
  grado_despues FLOAT,            -- grado de la celda después de ejecutar
  gap_cerrado FLOAT,              -- cuánto se cerró el gap (objetivo - antes) vs (objetivo - despues)
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campo de gradientes por ejecución (21 celdas × 3 valores cada una)
CREATE TABLE campo_gradientes (
  ejecucion_id TEXT PRIMARY KEY,
  input_texto TEXT,
  -- Cada celda tiene: actual, objetivo, gap
  gradientes JSONB NOT NULL,      -- [{lente, funcion, actual, objetivo, gap}] × 21
  -- Relaciones entre lentes detectadas
  dependencias_lentes JSONB,      -- ej: {"salud_fragil_por_sentido_bajo": true}
  -- Relaciones entre funciones detectadas
  dependencias_funciones JSONB,   -- ej: {"captar_sin_depurar": true}
  -- Top gaps ordenados (dirigen la ejecución)
  top_gaps JSONB,                 -- [{lente, funcion, gap}] ordenados por gap desc
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 3. ARQUITECTURA — 5 CAPAS

```
┌──────────────────────────────────────────────────────────┐
│  CAPA 5: INTERFAZ                                        │
│  Chief of Staff + Chat + API + Gateway                   │
│  Recibe input, devuelve output, acumula contexto         │
│  [Sistema Nervioso — Supabase]                           │
├──────────────────────────────────────────────────────────┤
│  CAPA 4: PERCEPCIÓN                                      │
│  Campo de gradientes sobre el input                      │
│  21 celdas × (actual, objetivo, gap)                     │
│  Detecta dependencias entre lentes y funciones           │
│  Los gaps dirigen la ejecución activamente               │
│  [Código puro + Haiku]                                   │
├──────────────────────────────────────────────────────────┤
│  CAPA 3: COMPILADOR                                      │
│  Router (qué inteligencias cubren las celdas débiles)    │
│  Compositor (en qué orden, con qué operaciones)          │
│  Selector de preguntas (navega la Matriz)                │
│  [Modelos ligeros + fallback Sonnet]                     │
├──────────────────────────────────────────────────────────┤
│  CAPA 2: EJECUCIÓN                                       │
│  LLMs ejecutan preguntas seleccionadas                   │
│  Modelo ejecutor empuja activamente hacia grado objetivo │
│  Navega la Matriz adaptativamente según gradientes       │
│  Verifica cierre de gaps en tiempo real                  │
│  [Haiku/Sonnet/Opus + Calculadoras + Simuladores]        │
├──────────────────────────────────────────────────────────┤
│  CAPA 1: CONOCIMIENTO                                    │
│  La Matriz 3L×7F×18INT como esquema                      │
│  Banco de preguntas con coordenadas                      │
│  Efectos registrados por celda                           │
│  Datos de cobertura acumulados                           │
│  [PostgreSQL — Supabase]                                 │
└──────────────────────────────────────────────────────────┘
```

### Diferencias con v1

| Aspecto | v1 | v2 |
|---------|----|----|
| Capa 1 | Lista plana de efectos | Matriz 3L×7F×18INT como campo de gradientes |
| Routing | "Qué inteligencia es relevante" | "Qué gaps son mayores y quién los cierra" |
| Ejecución | Preguntas fijas por inteligencia | Agente activo que empuja hacia grado objetivo |
| Evaluación | Score genérico | Verificación de cierre de gaps por celda |
| Percepción | No existía | Campo de gradientes + dependencias entre lentes/funciones |
| Aprendizaje | Datos planos | Efectos con gap_cerrado → selección natural de preguntas |
| Cobertura INT | Cada INT cubre sus preguntas genéricas | Cada INT cubre las 21 celdas desde su lente |

---

## 4. PIPELINE — FLUJO DE UNA EJECUCIÓN

El pipeline es **activo**, no reactivo. No espera a ver qué sale — empuja hacia grados objetivo y verifica que los gaps se cierran.

```
INPUT (texto del usuario)
         │
         ▼
┌─────────────────────────────────┐
│  PASO 1: CAMPO DE GRADIENTES    │  ~1-3s | ~$0.01
│  Código puro + Haiku             │
│                                  │
│  Para cada celda (21):           │
│  → grado_actual: ¿cuánto cubre  │
│    el input esta función×lente?  │
│  → grado_objetivo: dado el      │
│    contexto, ¿cuánto debería?   │
│  → gap = objetivo - actual       │
│                                  │
│  Detecta dependencias:           │
│  → entre lentes (salud sin       │
│    sentido = salud frágil)       │
│  → entre funciones (captar sin   │
│    depurar = acumular basura)    │
│                                  │
│  Output: campo de 21 gradientes  │
│  ordenados por gap descendente   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 2: ROUTING POR GRADIENTE  │  ~500ms | ~$0.001
│  Modelos ligeros C1+C2          │
│  + fallback Sonnet si divergen  │
│                                  │
│  Para cada celda con gap > 0.3:  │
│  → ¿Qué inteligencias cierran   │
│    ESTE gap con más efectividad? │
│  → Dato empírico: gap_medio_    │
│    cerrado por INT por celda     │
│                                  │
│  → Top 3-5 inteligencias        │
│    priorizadas por impacto       │
│    total sobre los gaps          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 3: COMPOSICIÓN             │  ~200ms | $0
│  Grafo C3 + solver              │
│  → Orden que maximiza cierre    │
│    de gaps (no genérico)         │
│  → Operaciones (fusión/comp.)   │
│  → Selección de pensamiento     │
│    y modo por paso              │
│  → Las dependencias entre        │
│    lentes/funciones informan     │
│    la secuencia                  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 4: SELECCIÓN DE PREGUNTAS  │  ~100ms | $0
│  Navega la Matriz               │
│                                  │
│  Para cada celda objetivo:       │
│  → Preguntas de ESA coordenada   │
│    (inteligencia×lente×función) │
│  → Priorizadas por               │
│    gap_medio_cerrado (dato real) │
│  → Nivel según dominio + budget  │
│                                  │
│  El ejecutor recibe:             │
│  - preguntas prioritarias        │
│  - mapa de gaps como contexto    │
│  - acceso a Matriz completa      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 5: EJECUCIÓN ACTIVA       │  30-120s | $0.30-0.80
│                                  │
│  El modelo ejecutor NO ejecuta   │
│  preguntas pasivamente.          │
│  EMPUJA hacia grado objetivo:    │
│                                  │
│  → Ejecuta preguntas prioritarias│
│  → Si una pregunta no cierra gap │
│    → cambia de ángulo            │
│    → tira de otra celda          │
│    → sube de nivel (profunda)    │
│  → Tiene el campo de gradientes  │
│    como brújula                  │
│                                  │
│  Haiku: extracción rápida        │
│  Sonnet: integración + gaps      │
│  Opus: navegación adaptativa     │
│  Código: cálculos puros          │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 6: VERIFICACIÓN DE CIERRE │  ~1-3s | ~$0.01
│                                  │
│  Re-evalúa el campo de           │
│  gradientes POST-ejecución:      │
│                                  │
│  Para cada celda objetivo:       │
│  → grado_nuevo vs grado_antes   │
│  → ¿Se cerró el gap?            │
│                                  │
│  Si gaps > 0.3 persisten:        │
│  → Escalar: otra INT, otra       │
│    profundidad, otra formulación │
│  → Max 2 re-intentos por celda  │
│                                  │
│  Registra: gap_cerrado por       │
│  pregunta → alimenta             │
│  score_efectividad en la Matriz  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 7: INTEGRACIÓN + REGISTRO │  10-20s | ~$0.15
│  Opus/Sonnet: síntesis final    │
│                                  │
│  → Output al usuario con mapa   │
│    de lo cubierto y lo pendiente │
│  → Registro de efectos con      │
│    coordenadas + gaps cerrados  │
│  → Actualiza gap_medio_cerrado  │
│    por pregunta (aprendizaje)   │
│  → Feedback loop                │
└─────────────────────────────────┘

TOTAL: ~$0.35-1.50 | ~40-150s
```

### El modelo ejecutor como agente activo

En el Paso 5, el modelo ejecutor (Opus en modo profundo) no recibe una lista cerrada de preguntas para ejecutar pasivamente. Recibe:

1. Las preguntas prioritarias (de las celdas con mayor gap)
2. El campo de gradientes completo como brújula
3. Acceso a la Matriz completa para esas inteligencias
4. Las dependencias entre lentes y funciones detectadas

Esto permite que Opus opere como **agente activo**, no como ejecutor pasivo:

- Si una pregunta no cierra el gap → cambia de ángulo dentro de la misma celda
- Si descubre que el problema real está en otra celda → navega hacia ella
- Si detecta una dependencia (Salud frágil porque Sentido bajo) → prioriza Sentido aunque el gap de Salud sea mayor
- Si el nivel base no cierra el gap → escala a profunda sin esperar a la verificación

La diferencia es fundamental: el sistema no "ejecuta preguntas y mira qué sale". El sistema **empuja hacia el grado objetivo** y se adapta en tiempo real.

### Verificación de cierre vs evaluación genérica

En v1, la evaluación era: "¿el output tiene buena calidad?" (score genérico).

En v2, la verificación es: "¿se cerraron los gaps?" — medición específica, por celda, con antes y después. Eso produce datos de efectividad por pregunta que retroalimentan la Matriz. Después de 1000 ejecuciones, cada pregunta tiene un `gap_medio_cerrado` empírico. Las preguntas que no cierran gaps se degradan. Las que cierran gaps se priorizan. Selección natural en el banco de preguntas.

---

## 5. MODOS DE OPERACIÓN

Los modos NO son programas diferentes. Son configuraciones del mismo pipeline:

```
MODO ANÁLISIS:
  Input = caso/situación
  Campo de gradientes completo (21 celdas)
  3-5 inteligencias, empuja hacia grado objetivo
  Verificación de cierre por celda
  Output = diagnóstico con gaps cerrados y gaps pendientes
  Latencia: 40-150s | Coste: $0.50-1.50

MODO CONVERSACIÓN:
  Input = turno de chat
  Campo parcial (solo celdas que el turno toca)
  1-2 inteligencias, nivel base
  Output = respuesta informada + señal si detecta gap grande
  Latencia: 5-20s | Coste: $0.05-0.15

MODO GENERACIÓN:
  Input = briefing/tema
  Campo orientado al output deseado (qué necesita el contenido)
  Inteligencias creativas (INT-14, INT-15, INT-09, INT-12)
  Output = contenido generado con cobertura funcional verificada
  Latencia: 30-90s | Coste: $0.30-0.80

MODO CONFRONTACIÓN:
  Input = propuesta/plan
  Campo busca gaps que la propuesta ignora
  Inteligencias de frontera (INT-17, INT-18, INT-06)
  Output = gaps no cubiertos + dependencias peligrosas + alternativas
  Latencia: 30-90s | Coste: $0.30-0.80
```

---

## 6. TRES CAPAS DE PRIMITIVAS

El compilador selecciona tres cosas por cada paso de ejecución:

```
CAPA 1: INTELIGENCIA  — con qué lente mirar (18 álgebras)
CAPA 2: PENSAMIENTO   — cómo pensar con esa lente (17 tipos: T01-T17)
CAPA 3: MODO          — en qué modo operar (6 modos)
```

Más la dimensión funcional:

```
CAPA 0: GRADIENTES — qué gaps cerrar y con qué fuerza (campo 3L×7F)
```

Una instrucción completa al ejecutor:

```json
{
  "paso": 1,
  "gaps_objetivo": [
    {"celda": "depurar×salud", "actual": 0.2, "objetivo": 0.9, "gap": 0.7},
    {"celda": "frontera×sentido", "actual": 0.1, "objetivo": 0.9, "gap": 0.8}
  ],
  "dependencias": ["salud_fragil_por_sentido_bajo"],
  "inteligencia": "INT-07",
  "pensamiento": ["T01", "T02", "T12"],
  "modo": "ANALIZAR",
  "nivel": "profunda",
  "sub_dominio": "startup_early_stage",
  "acceso_matriz": true
}
```

Esto dice: cierra los gaps de Depurar×Salud (0.7) y Frontera×Sentido (0.8) usando Financiera en modo análisis, sabiendo que la Salud es frágil porque Sentido está bajo. Prioriza Frontera×Sentido (gap mayor). Si no cierras, escala o navega.

Espacio combinatorio útil estimado: ~180 configuraciones por paso (18 INT × ~5 pensamientos × ~2 modos naturales), filtrado por las celdas objetivo. Mucho más expresivo que solo inteligencias, pero acotado por la necesidad funcional.

---

## 7. PROFUNDIDAD PROGRESIVA

3 niveles de preguntas por inteligencia:

```
NIVEL BASE (~50 preguntas):
  Genéricas. Funcionan para cualquier caso.
  Origen: Cartografía Fase A.

NIVEL PROFUNDA (~150 preguntas, por sub-dominio):
  Preguntas de especialista.
  Origen: Claude genera + Reactor v2 invierte papers + expertos revisan.

NIVEL EXPERTA (~300+ preguntas, por sub-dominio):
  Preguntas de 20 años de experiencia.
  Origen: Reactor v2 invierte manuales técnicos + uso real señala déficit.
```

El compilador decide el nivel como parte del algoritmo, usando dominio detectado + presupuesto + historial del usuario.

---

## 8. AUTO-DIAGNÓSTICO — LA MATRIZ DEL SISTEMA SOBRE SÍ MISMO

### El principio

El sistema usa la misma lente para verse a sí mismo que para ver al usuario. La Matriz 3L×7F no solo organiza el análisis de inputs externos — organiza el análisis del propio sistema. Observador = Sistema (Invariante 3 del ADN OMNI).

### La Matriz del sistema

```
EL SISTEMA COGNITIVO TIENE SU PROPIA MATRIZ 3L×7F:

               Salud                    Sentido                   Continuidad
               (¿funciono?)             (¿voy en la dirección     (¿sobrevivo sin
                                         correcta?)                intervención manual?)

F1 Conservar   Uptime, circuit          ¿Las mejoras mantienen    ¿El sistema sobrevive
               breakers, infra          la dirección del diseño   si nadie lo toca 3 meses?
               aguanta carga            o derivan?

F2 Captar      ¿Telemetría completa?    ¿Los datos que capta      ¿Puede captar de fuentes
               ¿Ingesta datos reales    son los que necesita       nuevas sin intervención
               suficientes?             para mejorar?              manual?

F3 Depurar     ¿Elimina componentes     ¿Descarta mejoras que     ¿Poda preguntas
               rotos? ¿Dead letter      no alinean con la         inefectivas?
               queue funciona?          arquitectura?             ¿Selección natural activa?

F4 Distribuir  ¿Haiku donde barato,     ¿La energía va a lo       ¿Distribuye conocimiento
               Opus donde vale?         que más impacta o         entre componentes o
               ¿Recursos donde tocan?   se dispersa?              lo siloa?

F5 Frontera    ¿Distingue input         ¿Sabe qué es su trabajo   ¿La API/gateway protege
               válido de ruido?         y qué no? ¿Rechaza        el núcleo al escalar a
               ¿Gateway protege?        lo que no toca?            multi-tenant?

F6 Adaptar     ¿Se adapta a fallos?     ¿Las adaptaciones          ¿Puede incorporar
               ¿Fallbacks funcionan?    respetan los principios    inteligencias nuevas
               ¿Degradación graceful?   o los erosionan?           sin rediseño?

F7 Replicar    ¿Patrones exitosos se    ¿Replica lo esencial       ¿Documentación suficiente
               replican entre agentes?  o copia partes             para reconstruir
               ¿Templates funcionan?    degeneradas?               desde cero?
```

Cada celda tiene grado actual, grado objetivo y gap — igual que la Matriz para usuarios. Las mejoras del sistema se dirigen por los gaps de esta Matriz, no por intuición ni por "lo que parece urgente".

### Cómo alimenta la mejora continua

```
ANTES (mejora continua genérica):
  Detectar anomalías → proponer fixes → ejecutar

AHORA (mejora continua por gradientes):
  Medir campo de gradientes del sistema (21 celdas)
  → Identificar celdas con mayor gap
  → Proponer mejoras que cierren ESOS gaps
  → Ejecutar mejora
  → Re-medir campo: ¿se cerró el gap?
  → Si no → escalar o cambiar enfoque
```

La cola de mejoras se enriquece con coordenadas:

```json
{
  "tipo": "mejora",
  "celda_sistema": "depurar×sentido",
  "gap": 0.6,
  "descripcion": "El sistema no descarta mejoras que no alinean con la arquitectura. 3 de las últimas 5 propuestas aprobadas eran features que no mapean a ningún principio de diseño.",
  "propuesta": "Añadir filtro: toda propuesta de mejora debe mapear a un principio o a una celda de la Matriz. Si no mapea, se rechaza automáticamente."
}
```

### Cómo alimenta la propiocepción

La propiocepción deja de ser "157 componentes con health score" y pasa a ser "21 celdas del sistema con grado, objetivo y gap". Mucho más accionable:

- **Mapa de competencia por celda de usuario:** cuántas preguntas tiene la Matriz por celda, qué score medio, qué gap_medio_cerrado. Las celdas con pocas preguntas y score bajo = el sistema sabe que ahí es débil.

- **Mapa de salud del sistema por celda propia:** las 21 celdas del sistema con grados actuales. El verificador de semillas chequea estas celdas como condiciones de activación.

- **Convergencia:** Cuando una celda del usuario está débil Y la celda equivalente del sistema también está débil = doble riesgo. El sistema no puede cubrir un gap del usuario que es también su propio gap.

---

## 9. SISTEMA NERVIOSO — COMPONENTES INTEGRADOS

Los siguientes componentes del sistema nervioso (Supabase) se integran en el organismo, todos alimentados por la Matriz:

### 9.1 Telemetría + Baselines

Observabilidad universal. Métricas append-only de latencia, tokens, coste, errores. Baselines multi-ventana (24h/7d/30d) por agente.

**Extensión v2:** Las métricas se organizan por celdas de la Matriz del sistema. No es "latencia del router" sino "¿Distribuir×Salud del sistema está en grado suficiente?". La telemetría alimenta los grados de las celdas del sistema automáticamente.

### 9.2 Mejora Continua

3 agentes: detector de anomalías, generador de propuestas, ejecutor de mejoras. Cola de mejoras con tipos y coordenadas.

**Extensión v2:** El detector opera sobre el campo de gradientes del sistema. Detecta: gaps del sistema que crecen (degradación), dependencias rotas (Captar×Salud alto pero Depurar×Salud bajo = acumulando sin depurar), y celdas del sistema que ningún componente cubre. Las propuestas llevan coordenada de celda para que se pueda verificar si la mejora cerró el gap.

### 9.3 Semillas Dormidas + Verificador

22 semillas con condiciones de activación. Verificador automático ($0 LLM). Estados: dormida → verificando → lista → activa.

**Extensión v2:** Las condiciones de activación se expresan como grados de celdas del sistema. Ejemplo: "Activar Reactor v2 cuando Captar×Continuidad del sistema alcance grado > 0.7" (= el sistema puede captar de fuentes nuevas sin intervención). Las semillas dejan de tener condiciones ad-hoc y pasan a tener coordenadas en la Matriz del sistema.

### 9.4 Propiocepción

Registro de arquitectura + modelo interno unificado.

**Extensión v2:** La propiocepción es la Matriz del sistema. El mapa de competencia (por celda de usuario) + el mapa de salud (por celda del sistema). El sistema se ve a sí mismo con la misma resolución con la que ve al usuario. Cuando una celda de usuario tiene gap alto y la celda equivalente del sistema también tiene gap alto → señal de alarma: "no puedo cubrir este gap del usuario porque yo mismo tengo ese gap".

### 9.5 Estigmergia

Comunicación entre agentes via marcas en base de datos. Sin llamadas directas.

Se mantiene tal cual. Es el patrón de coordinación del organismo.

### 9.6 Gateway

Tenants, metering, circuit breaker, tareas async. Capa de acceso multi-tenant.

Se mantiene. Alimenta celdas de Frontera×Salud y Frontera×Continuidad del sistema.

### 9.7 Persistencia Inter-Sesión

Perfil de usuario acumulado, cola de emergencias, compresor de memoria.

**Extensión v2:** El perfil del usuario incluye su campo de gradientes personal — qué funciones están típicamente débiles en sus consultas, qué lentes domina, dónde tiene gaps recurrentes. Esto permite que el sistema anticipe en vez de diagnosticar desde cero cada vez.

---

## 10. REACTOR v2 — INVERSIÓN DE DOCUMENTOS

### Qué es

Un pipeline que toma documentos técnicos (papers, tesis, manuales, casos) y los invierte: extrae las preguntas implícitas que el texto responde, las ubica en la Matriz, y detecta las preguntas que el texto NO hace.

### Arquitectura

```
DOCUMENTO (paper, tesis, manual, caso)
         │
         ▼
┌─────────────────────────────────┐
│  PASO 1: CHUNKING               │  Código puro, $0
│  Documento → chunks ~1000 tokens │
│  Detecta estructura del texto   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 2: INVERSIÓN — CASCADA    │
│                                  │
│  2a. Haiku (todos los chunks)    │  ~$0.001/chunk
│      Preguntas explícitas        │
│      ~60% de las preguntas       │
│                                  │
│  2b. Sonnet (todos los chunks)   │  ~$0.01/chunk
│      Revisa + añade implícitas   │
│      +30% preguntas              │
│      + campo profundidad_restante│
│                                  │
│  2c. Opus (selectivo — ~20%)     │  ~$0.05/chunk
│      Solo chunks con señal       │
│      Meta-preguntas, conexiones  │
│      +5-8% preguntas profundas   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 3: GATE OPUS (Opción C)   │  Código puro + Sonnet
│                                  │
│  Score código puro (4 señales):  │
│  - inteligencias >= 3    (+0.3)  │
│  - sonnet señaló límite  (+0.3)  │
│  - tensión textual       (+0.2)  │
│  - baja superposición    (+0.2)  │
│                                  │
│  score > 0.7 → OPUS directo     │
│  score < 0.3 → PARAR            │
│  0.3-0.7 → profundidad_restante │
│             de Sonnet desempata  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 4: CLASIFICACIÓN           │
│                                  │
│  Cada pregunta extraída →        │
│  - Inteligencia (C2 + fallback)  │
│  - Lente (salud/sentido/cont.)   │
│  - Función (F1-F7)              │
│  - Coordenadas en la Matriz      │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 5: DETECCIÓN DE HUECOS    │
│                                  │
│  Mapear 21 celdas del documento  │
│  Celdas llenas = lo que cubre    │
│  Celdas vacías = puntos ciegos   │
│  → GENERAR preguntas ausentes    │
│    desde las celdas vacías       │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 6: DETECCIÓN ESTRUCTURAL   │
│                                  │
│  ¿Las preguntas siguen           │
│  EXTRAER→CRUZAR→LENTES→         │
│  INTEGRAR→ABSTRAER→FRONTERA?     │
│  ¿O tienen otra estructura?      │
│  → Testea hipótesis de           │
│    universalidad del protocolo   │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  PASO 7: INTEGRACIÓN EN MATRIZ   │
│                                  │
│  Preguntas nuevas → banco con    │
│  coordenadas y fuente            │
│  Score efectividad = null        │
│  (se actualiza con uso real)     │
└─────────────────────────────────┘

COSTE POR DOCUMENTO (~50 chunks):
  Sin Opus:           ~$0.55/doc
  Con Opus selectivo: ~$1.05/doc
  100 documentos:     ~$105 total
```

### Fuentes de documentos por inteligencia

```
INT-01 Lógico-Matemática:  arXiv math (optimización, decisión bajo incertidumbre)
INT-02 Computacional:       arXiv cs (algoritmos, complejidad, sistemas)
INT-03 Estructural:         Papers de systems thinking, cibernética
INT-04 Ecológica:           Papers de ecología de sistemas, resiliencia
INT-05 Estratégica:         HBR cases, papers de estrategia corporativa
INT-06 Política:            arXiv econ (teoría de juegos), casos negociación
INT-07 Financiera:          SSRN, SEC filings, IFRS, corporate finance
INT-08 Social:              Papers de psicología social, dinámica de grupos
INT-09 Lingüística:         Papers de pragmática, análisis del discurso
INT-10 Cinestésica:         PubMed (biomecánica, fisiología), protocolos
INT-11 Espacial:            Papers de diseño, arquitectura, visualización
INT-12 Narrativa:           Estudios narratológicos, guiones documentados
INT-13 Prospectiva:         Papers de futures studies, scenario planning
INT-14 Divergente:          Papers de creatividad, design thinking, TRIZ
INT-15 Estética:            Papers de diseño, filosofía del arte
INT-16 Constructiva:        Papers de project management, ingeniería
INT-17 Existencial:         Filosofía existencialista, psicología humanista
INT-18 Contemplativa:       Papers de mindfulness, fenomenología
```

Objetivo: 5-10 documentos por inteligencia como semilla inicial. ~100 documentos totales.

---

## 11. META-MOTOR — RAZONAMIENTO SOBRE PREGUNTAS

### El salto de nivel lógico

Los 17 tipos de razonamiento no solo operan sobre datos — operan sobre las preguntas mismas:

```
NIVEL 1 (actual):   Razonamiento(datos)     → hallazgos
NIVEL 2 (nuevo):    Razonamiento(preguntas) → preguntas mejores
```

### Qué produce

```
INPUT:  Set existente de preguntas de la Matriz
OUTPUT:
  1. Preguntas nuevas que no existían (T17 Creación)
  2. Preguntas optimizadas (T15 Reencuadre)
  3. Preguntas eliminadas por redundancia (T05 Discernimiento)
  4. Preguntas raíz generadoras de cascada (T02 Causalidad)
  5. Preguntas transferidas entre dominios (T11 Analogía)
  6. Anti-preguntas que destruyen supuestos (T12 Contrafactual)
  7. Meta-patrones de preguntas efectivas (T03 Abstracción)
```

### Impacto en el reactor

```
REACTOR v1:  Preguntas fijas → datos → modelos → más datos
             Las preguntas no cambian. Los datos crecen.

REACTOR v2:  Documentos → preguntas nuevas → datos nuevos → modelos
             Las preguntas crecen desde conocimiento externo.

META-MOTOR:  Preguntas → razonamiento sobre preguntas → preguntas mejores
             Las preguntas evolucionan por razonamiento propio.
```

Tres mecanismos complementarios de amplificación.

Coste: ~$0.10-0.20 por ciclo de meta-razonamiento (1 call Opus). Un ciclo semanal = ~$1/mes.

---

## 12. MODELOS LIGEROS (Fase C)

4 modelos entrenados con datos del Reactor v1 (1,183 datapoints sintéticos):

| Modelo | Tipo | Función | Criterio | Estado |
|--------|------|---------|----------|--------|
| C1 Router | TF-IDF + centroides B2 | Input → top-K inteligencias | top-3 acc >80% | 77.8% (iterando) |
| C2 Clasificador | RF sobre B2 | Texto → inteligencia single-label | F1 macro >0.50 | 53% (pasa ajustado) |
| C3 Compositor | Frecuencias de orden | Par → dirección óptima | 3/3 test cases | PASA |
| C4 Scorer | Ridge 9 features | Output → score calidad | Pearson >0.70 | 0.81 PASA |

Los modelos ligeros son optimización, no habilitación. El sistema funciona con fallback a Sonnet en routing ($0.18/ejecución). Los modelos ligeros reducen coste y latencia cuando funcionan; Sonnet cubre cuando no.

Con datos reales (post Fase E), los modelos se re-entrenan y mejoran significativamente. Los datos sintéticos son bootstrapping.

---

## 13. STACK TÉCNICO

```
MOTOR COGNITIVO (fly.io):
  Python/FastAPI        — Pipeline, API
  scikit-learn          — Modelos ligeros C1-C4
  NetworkX + scipy      — Grafo compositor
  numpy                 — Calculadoras
  Anthropic API         — Haiku, Sonnet, Opus

SISTEMA NERVIOSO (Supabase):
  Edge Functions (Deno) — 99 funciones
  PostgreSQL            — Matriz, estado, telemetría, marcas
  pg_net                — Fire-and-forget async

COORDINACIÓN:
  Supabase PostgreSQL   — Fuente de verdad para la Matriz
  fly.io lee/escribe    — Via API REST de Supabase
  Estigmergia           — Marcas entre agentes

INTERFAZ:
  HTML standalone       — Chat (PWA-capable)
  API REST              — Para integraciones
  Gateway               — Multi-tenant con metering
```

---

## 14. ROADMAP — ESTADO ACTUAL Y SIGUIENTE

```
FASE A: Cartografía                    ✅ COMPLETADA
  18 INT × 3 casos, loop tests, propiedades P01-P11

FASE B: Datos sintéticos              ✅ COMPLETADA
  1,183 items, $1.99, 4 JSONs en data/sinteticos/

FASE C: Modelos ligeros               🔄 EN CURSO
  C3 y C4 pasan. C1 y C2 mejorando.
  Criterio ajustado: C2 F1 >0.50 (rol complementario).

FASE D: Integración en pipeline       ⬜ SIGUIENTE
  → Cerrar C1/C2 con fallback Sonnet
  → Integrar diagnóstico 7F como paso 1
  → Migrar banco de preguntas a Matriz (coordenadas 3L×7F)
  → Pipeline end-to-end con routing por celdas

FASE E: Chat funcional                ⬜ DESPUÉS
  → Chief of Staff usa la Matriz para conversar
  → Estado persistente con mapa 3L×7F del usuario
  → Datos reales alimentan re-entrenamiento

FASE F: Pilotos + Reactor v2          ⬜ DESPUÉS
  → Uso real genera datos reales
  → Reactor v2 invierte documentos técnicos
  → Re-entrenamiento de modelos con datos reales
  → Meta-motor como ciclo semanal
```

### Dependencias

```
Cartografía ──→ Sintéticos ──→ Modelos ligeros
                                     │
                                     ▼
                              Integración + Matriz ◄── Diseño 7F
                                     │
                                     ▼
                              Chat funcional
                                     │
                                     ▼
                              Pilotos + Reactor v2
                                     │
                                     └──→ Datos reales → Re-entrena → Mejora
                                     └──→ Papers invertidos → Enriquece Matriz
                                     └──→ Meta-motor → Evoluciona preguntas
```

---

## 15. PRESUPUESTO

### Coste por ejecución

```
MODO CONVERSACIÓN:  ~$0.05-0.15  (routing rápido, 1-2 INT, base)
MODO ANÁLISIS:      ~$0.50-1.50  (diagnóstico 7F + 3-5 INT + evaluación)
MODO CONFRONTACIÓN: ~$0.30-0.80  (frontera + celdas ignoradas)
MODO GENERACIÓN:    ~$0.30-0.80  (creativas + integración)
```

### Coste recurrente

```
Ejecuciones motor:     ~$1/ejecución × volumen
Re-entrenamiento:      ~$20/mes
Reactor v2 (100 docs): ~$105 (puntual)
Meta-motor:            ~$1/mes (semanal)
Telemetría + infra:    ~$10/mes (Supabase free + fly.io)
```

### Presupuesto total: €200/mes (decisión CR1 vigente)

---

## 16. RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Diagnóstico 7F impreciso | Celdas mal identificadas → routing erróneo | Haiku diagnostica, Sonnet verifica en caso ambiguo. Datos reales calibran. |
| Matriz demasiado granular | 378 posiciones, muchas vacías | Empezar con las 21 celdas (3L×7F). Dimensión INT se añade con uso. |
| Modelo ejecutor no navega bien | Opus ignora la Matriz y ejecuta genérico | Prompt engineering riguroso + evaluación de cobertura como métrica. |
| Reactor v2 genera preguntas de baja calidad | Ruido en la Matriz | Cascada H→S→O filtra. Score de efectividad se actualiza con uso real. Preguntas con score <0.3 se archivan. |
| Latencia > 150s en análisis | UX pobre | Streaming parcial + diagnóstico 7F como respuesta rápida mientras el profundo trabaja. |
| Complejidad de integración Supabase↔fly.io | Fallos de coordinación | La Matriz vive en Supabase (fuente de verdad). fly.io solo lee/escribe via API. |

---

## 17. PRINCIPIOS DE DISEÑO

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es intercambiable. La Matriz es permanente.

2. **Percibir antes de razonar.** Diagnóstico 7F primero. Sin saber qué funciones están débiles, el routing es ciego.

3. **Cada modelo hace lo que mejor sabe.** LLMs para generar y sintetizar. Embeddings para buscar. Grafos para optimizar. Código para calcular.

4. **El motor no tiene opinión.** Selecciona preguntas, ejecuta, devuelve lo que emerge. No prescribe.

5. **Empujar, no reaccionar.** El sistema no espera a ver qué sale. Mide el gap, empuja hacia el grado objetivo, y verifica que se cerró. Si no se cerró, escala. La diferencia entre actual y objetivo es la fuerza que dirige todo.

6. **Las lentes y funciones no son independientes.** Salud sin Sentido es frágil. Captar sin Depurar es acumular basura. El diagnóstico ve las dependencias, no solo los grados aislados.

7. **Menos es más.** 4 inteligencias sobre gaps grandes > 18 inteligencias sobre todo. Los gradientes son la herramienta de poda.

8. **Retroalimentación con coordenadas.** Cada ejecución registra qué gaps cerró. Las preguntas que cierran gaps se priorizan. Las que no, se degradan. Selección natural en el banco de preguntas.

8. **Profundidad progresiva.** Base para todo. Profunda donde el dominio lo requiere. Experta donde el uso real muestra déficit.

9. **Tres capas de primitivas.** Inteligencia × Pensamiento × Modo, filtradas por celdas objetivo. Expresividad multiplicativa.

10. **Si no hay registro, no existe.** Cada implementación genera checklist + documento. El contexto fresco es irremplazable.

11. **Las preguntas son el combustible, no los datos.** Los datos se agotan. Las preguntas generan datos nuevos infinitamente.

12. **Todo texto experto es preguntas comprimidas.** El Reactor v2 las recupera. Cada documento procesado enriquece la Matriz con conocimiento que tardó décadas en cristalizar.

13. **Las preguntas se pueden razonar.** Los mismos tipos de pensamiento que operan sobre datos operan sobre preguntas. El meta-motor evoluciona las preguntas.

14. **La Matriz es el esqueleto.** Unifica percepción (diagnóstico 7F), razonamiento (inteligencias sobre celdas), almacenamiento (efectos con coordenadas) y aprendizaje (reactor + meta-motor). Un esquema, cuatro funciones.

15. **El sistema se ve a sí mismo.** Propiocepción + mapa de competencia por celda. Sabe dónde es fuerte y dónde es débil.

16. **Implementación sobre referencia.** CONTEXTO_SISTEMA.md describe cómo están implementadas las tripas. Este documento describe qué ES el sistema. Si la implementación cambia, este documento no cambia. L0 gobierna L2.

---

## 18. GLOSARIO

| Término | Definición |
|---------|------------|
| Matriz | Estructura 3L×7F×18INT (378 posiciones) que organiza todo el conocimiento del sistema |
| Celda | Una posición en la Matriz (ej: Depurar×Salud). Tiene grado actual, grado objetivo y gap |
| Campo de gradientes | Las 21 celdas con sus gaps. La fuerza que dirige toda la ejecución |
| Gap | Diferencia entre grado actual y objetivo de una celda. Mayor gap = más fuerza = más prioridad |
| Grado | Medida 0.0-1.0 de cuánto está cubierta una función×lente. No es binario |
| Grado objetivo | Cuánto DEBERÍA estar cubierta una celda dado el contexto. No siempre es 1.0 |
| Dependencia entre lentes | Salud sin Sentido = Salud frágil. Las lentes se condicionan mutuamente |
| Dependencia entre funciones | Captar sin Depurar = acumular basura. Las funciones tienen interdependencias |
| Routing por gradiente | Selección de inteligencias basada en qué gaps necesitan cerrarse y quién los cierra |
| Ejecución activa | El modelo ejecutor empuja hacia grado objetivo, no ejecuta pasivamente |
| Verificación de cierre | Evaluación post-ejecución: ¿se cerró el gap? No "¿fue bueno el output?" |
| gap_medio_cerrado | Dato empírico por pregunta: cuánto cierra el gap en promedio. Selección natural |
| Reactor v1 | Generador de datos sintéticos desde la cartografía (completado) |
| Reactor v2 | Inversor de documentos externos con cascada H→S→O |
| Meta-motor | Razonamiento sobre preguntas para evolucionar la Matriz |
| Sistema Nervioso | Subsistema Supabase: percepción, coordinación, evolución |
| Motor Cognitivo | Subsistema fly.io: diagnóstico profundo, razonamiento multi-inteligencia |
| Gate Opus | Mecanismo código+Sonnet que decide si escalar un chunk a Opus |
| Mapa de competencia | Propiocepción de la Matriz: cuántas preguntas/ejecuciones/score por celda |

---

## 19. RELACIÓN CON OTROS DOCUMENTOS

| Documento | Relación | Nivel |
|-----------|----------|-------|
| Este documento | Qué ES el sistema, cómo encaja todo | L0/L1 |
| CONTEXTO_SISTEMA.md | Cómo están implementadas las tripas en Supabase | L2 (implementación) |
| SPEC_REACTOR_V1.md | Spec del generador de datos sintéticos | L2 (implementación) |
| PROTOCOLO_CARTOGRAFIA_META_RED_v1.md | Protocolo de la cartografía (Fase A) | L2 (completado) |
| META_RED_INTELIGENCIAS_CR0.md | Las 18 inteligencias como redes de preguntas | L1 (fuente) |
| L0_ADN_MODELO_OMNI.md | Los 7 invariantes del modelo OMNI | L0 (fundamento) |
| L0.7_FUNCIONES_NUCLEARES.md | Las 7F + 3L que generan la Matriz | L0 (fundamento) |
| L0.5_MECANISMO_UNIVERSAL_VINCULACION.md | El mecanismo universal de construcción de mapas | L0 (meta-fundamento) |
| MEMORY.md | Estado operativo del Sistema Nervioso | L2 (operativo) |

---

**FIN SISTEMA COGNITIVO OMNI-MIND — DOCUMENTO MAESTRO v2 — CR0**
