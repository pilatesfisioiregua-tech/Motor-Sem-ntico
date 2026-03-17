# SISTEMA COGNITIVO OMNI-MIND — DOCUMENTO MAESTRO CONSOLIDADO

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-09
**Supersede:** DISENO_MOTOR_SEMANTICO_v1.md, DISENO_MOTOR_SEMANTICO_v2.md, SISTEMA_COGNITIVO_OMNI_MIND_v2.md, ACTUALIZACION_DISENO_V2_SECCIONES_20_22.md
**Origen:** Consolidación de 4 documentos + decisiones sesión 2026-03-09

---

## 0. CAMBIOS DE ESTA VERSIÓN

| Cambio | Origen | Sección |
|--------|--------|---------|
| Prompt del agente = red de preguntas, no instrucciones imperativas | Sesión 09-mar | §1, §4 |
| Motores = fábrica que construye/mejora la Matriz. No son producto. | Sesión 09-mar | §1, §6 |
| 3 niveles de estabilidad: L0 invariante / L1 evolucionable / L2 variable | Sesión 09-mar | §1C |
| Infra: todo en fly.io. Supabase se depreca gradualmente | Sesión 09-mar | §8 |
| Integración Marco Lingüístico: 8 operaciones + gramática generativa | Sesión 09-mar | §1D |
| Capa 0: Detector de Huecos (7 primitivas + 8 operaciones) | Sesión 09-mar | §4 |
| Heurístico para selección macro, probabilístico gradual con datos | Sesión 09-mar | §4 |
| Álgebra del cálculo semántico = compilador de prompts de preguntas | Sesión 09-mar | §3 |
| Motor v1 ejecutor = modelo open source (Llama 3.1 70B vía Groq) | Sesión 09-mar-b | §4, §6B, §8 |
| Evaluador premium = Sonnet/Opus solo para scoring con coordenadas | Sesión 09-mar-b | §4, §6B |
| Motor v1 en dos fases: Fase A exploración exhaustiva → Fase B lookup | Sesión 09-mar-b | §6B |
| Protocolo de exploración con 5 tiers | Sesión 09-mar-b | §6B |
| Tabla configuraciones_efectivas para lookup por patrón de gaps | Sesión 09-mar-b | §9 |
| Enjambre meta-protocolo: optimiza el protocolo de exploración | Sesión 09-mar-b | §6C |
| Evolución L1 dirigida por datos: añadir/podar INTs con evidencia | Sesión 09-mar-b | §6C |
| Arquitectura 4 capas del Motor v1 | Sesión 09-mar-b | §6B |
| Ecosistema de entrenamiento: Reactores generan → Motor verifica | Sesión 09-mar-b | §6D |

---

## 1. QUÉ ES

Un organismo cognitivo que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas — es un sistema vivo que compila un programa cognitivo nuevo para cada interacción.

### El principio central

**El prompt del agente no tiene instrucciones imperativas. Es exclusivamente una red de preguntas.** La inteligencia emerge de la estructura de preguntas, no de instrucciones al modelo. No le dices al agente "analiza como financiero" — le das la red de preguntas de INT-07 y el agente no puede hacer otra cosa que operar financieramente.

Las preguntas no son output del agente (no las verbaliza). Son su **sistema operativo interno** — la lente a través de la cual mira y procesa.

**El LLM es intercambiable. La Matriz es permanente.** Si un modelo open source cierra gaps operando bajo las preguntas correctas, la Matriz funciona independientemente del modelo. Esto es la validación más fuerte del sistema.

### Los componentes

```
LA MATRIZ (3L × 7F × 18INT × preguntas)
  = el producto
  = el prompt del agente
  = el algoritmo operativo
  → §2

LOS MOTORES (cartografía, reactor v1, reactor v2, reactor v3, meta-motor)
  = la fábrica que construye, llena y mejora la Matriz
  → §6

EL ÁLGEBRA DEL CÁLCULO SEMÁNTICO
  = el compilador que ensambla las preguntas en prompts ejecutables
  → §3

LAS 8 OPERACIONES SINTÁCTICAS (Marco Lingüístico)
  = la gramática de cada pregunta individual
  → §1D

EL PIPELINE
  = la secuencia de ejecución: percibir gaps → compilar prompt → ejecutar → verificar cierre
  → §4

EL ECOSISTEMA DE ENTRENAMIENTO
  = ciclo cerrado: Reactores generan preguntas → Motor ejecuta masivamente (OS) → Evaluador puntúa (premium) → Matriz aprende
  → §6D
```

---

## 1A. TRES CONCEPTOS FUNDAMENTALES

### INTELIGENCIA = qué ves (y qué no puedes ver)

Un sistema de percepción con objetos propios, operaciones propias y un punto ciego estructural. Hay 18 (hoy — evolucionable). Cada una es un "vocabulario de percepción" diferente.

9 categorías empíricas (derivadas de 34 chats de cartografía):

| # | Categoría | Inteligencias | Qué comparten |
|---|-----------|---------------|---------------|
| 1 | Cuantitativa | INT-01, INT-02, INT-07 | Operan sobre lo medible |
| 2 | Sistémica | INT-03, INT-04 | Mapean relaciones entre partes |
| 3 | Posicional | INT-05, INT-06 | Ven actores, movimientos, poder |
| 4 | Interpretativa | INT-08, INT-09, INT-12 | Interpretan sentido humano |
| 5 | Corporal-Perceptual | INT-10, INT-15 | Perciben forma encarnada |
| 6 | Espacial | INT-11 | Topología visual |
| 7 | Expansiva | INT-13, INT-14 | Abren espacio de opciones |
| 8 | Operativa | INT-16 | Construye |
| 9 | Contemplativa-Existencial | INT-17, INT-18 | Significado último |

6 irreducibles (no sustituibles por combinación): INT-01, INT-02, INT-06, INT-08, INT-14, INT-16.

Catálogo completo de firmas, preguntas y propiedades: ver META_RED_INTELIGENCIAS_CR0.md y OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md.

### PENSAMIENTO = cómo procesas lo que percibes

17 tipos en tres familias:

- **Interno** (10): percepción, causalidad, abstracción, síntesis, discernimiento, metacognición, consciencia epistemológica, auto-diagnóstico, convergencia, dialéctica
- **Lateral** (7): analogía, contrafactual, abducción, provocación, reencuadre, destrucción creativa, creación
- **Inter-álgebra** (4): fusión, composición, diferencial, lectura cruzada

### MODO = para qué estás mirando

6 modos: ANALIZAR, PERCIBIR, MOVER, SENTIR, GENERAR, ENMARCAR. No toda inteligencia opera bien en todos los modos.

### Combinatoria

```
Configuración de un paso = Inteligencia × Pensamiento × Modo
Espacio teórico: 18 × 17 × 6 = 1.836
Espacio útil: ~180 (acotado por compatibilidad y gradientes)
```

MVP: motor selecciona inteligencia + modo. Pensamiento se activa implícitamente por las preguntas. Selección explícita de los tres en v2+.

---

## 1B. RELACIÓN CON EL MOTOR v3.3

| Pieza v3.3 | Dónde va |
|------------|----------|
| 7 primitivas sintácticas | Capa 0: Detector de Huecos |
| 4 isomorfismos | Las 4 lentes de INT-03 |
| Calculadora gaps id↔ir | Código puro dentro de INT-03 |
| Patrón de pipeline por capas | La meta-red de 6 pasos |

El v3.3 entero se encapsula como INT-03 dentro del motor semántico.

---

## 1C. TRES NIVELES DE ESTABILIDAD

```
INVARIANTE (L0 — no se toca):
  3 Lentes:    Salud / Sentido / Continuidad
  7 Funciones: Conservar / Captar / Depurar / Distribuir / Frontera / Adaptar / Replicar
  8 Operaciones sintácticas (Marco Lingüístico)
  Álgebra del cálculo semántico
  → Esto es gramática. No cambia.
  → Se falsifica solo si se encuentra: 4ª lente irreducible, 8ª función, 9ª operación.

ESTABLE PERO EVOLUCIONABLE (L1 — cambia con evidencia empírica):
  18 inteligencias (hoy) → puede ser 16 o 21 con datos reales
  17 tipos de pensamiento
  6 modos
  → Esto es vocabulario. Crece o se poda.
  → El Motor v1 en Fase A genera la evidencia empírica para decidir.

VARIABLE (L2 — cambia con cada ejecución):
  Preguntas dentro de cada celda
  Scores de efectividad
  Cobertura por dominio
  Configuraciones óptimas por patrón de gaps
  Protocolo de exploración (tiers)
  → Esto es contenido. Se llena, se mejora, se descarta.
```

---

## 1D. GRAMÁTICA GENERATIVA — MARCO LINGÜÍSTICO

### Las 8 operaciones primitivas

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

### 6 tipos de acople

| Conjunción | Tipo | Diagnóstico |
|------------|------|------------|
| Y | Sinergia | Salud |
| PERO | Tensión | Fricción activa |
| AUNQUE | Concesión | Grieta |
| PORQUE | Causalidad | Cadena causal |
| SI | Condicionalidad | Fragilidad |
| PARA | Finalidad | Dirección |

### Raíz pre-categorial × Operación

El mismo concepto se manifiesta según la operación aplicada:
```
EQUILIBRI- × predicación_estado → "¿está en equilibrio?"
EQUILIBRI- × modificación       → "¿es equilibrado?"
EQUILIBRI- × predicación_acción → "¿equilibra?"
EQUILIBRI- × complementación    → "¿opera con equilibrio?"
EQUILIBRI- × subordinación      → "¿debe mantener equilibrio?"
```

### Tres niveles de preguntas

**Nivel 1 — Fijas (hoy):** 18 redes escritas a mano. Funcionan. Se usan en MVP.
**Nivel 2 — Generadas (v2):** 8 operaciones × raíces de dominio → preguntas para cualquier dominio sin cartografía manual.
**Nivel 3 — Evolucionadas (meta-motor):** 17 pensamientos × preguntas → preguntas mejores.

### Falacias aritméticas

| Falacia | Error | Corrección |
|---------|-------|------------|
| Conducta → Valor | Predicación como Modificación | Pred → Sub_asertiva → Mod |
| Optimización sin finalidad | Transformación sin Sub final | Tr + Sub_final(PARA qué) |
| Creencia como Regla | Sub_asertiva como Sub_deóntica | Distinguir "creo" de "debe" |
| Cualidad como Función | Modificación como Predicación | "Es innovador" ≠ "innova" |
| Verbo sin objeto | Predicación sin Transitividad | Función declarada sin definir |

### Mapeo primitivas v3.3 ↔ operaciones Marco

| Primitiva v3.3 | Operación Marco |
|----------------|-----------------|
| Sustantivizar | Transformación → sustantivo |
| Adjetivar | Modificación |
| Adverbializar | Complementación |
| Verbo | Predicación |
| Preposicionar | Transitividad + Subordinación |
| Conjuntar | Conexión |
| Sujeto-predicado | Predicación + Cuantificación |

---

## 2. LA MATRIZ — 3L × 7F × 18INT

### El esquema central

```
DIMENSIÓN 1 — 3 LENTES (para qué):
  Salud:       ¿Funciona?
  Sentido:     ¿Tiene dirección?
  Continuidad: ¿Sobrevive más allá del sistema?

DIMENSIÓN 2 — 7 FUNCIONES (qué necesita):
  F1 Conservar / F2 Captar / F3 Depurar / F4 Distribuir
  F5 Frontera / F6 Adaptar / F7 Replicar

DIMENSIÓN 3 — 18 INTELIGENCIAS (quién lo ve):
  INT-01 a INT-18
```

378 posiciones (3 × 7 × 18). Cada pregunta tiene coordenadas exactas.

### Las 21 celdas como campo de gradientes

Cada celda tiene grado actual (0.0-1.0), grado objetivo (contextual), y gap = objetivo - actual. El gap genera la fuerza que dirige la ejecución. Mayor gap = más prioridad.

### Dependencias entre lentes

- Salud sin Sentido = funciona pero sin dirección (frágil)
- Sentido sin Salud = visión sin capacidad de ejecutar
- Continuidad sin Sentido = replicar vacío

### Dependencias entre funciones

- F2 Captar sin F3 Depurar = acumular basura
- F4 Distribuir sin F5 Frontera = fugas
- F1 Conservar sin F6 Adaptar = rigidez
- F7 Replicar sin F5 Frontera = replicar ruido

### Cada inteligencia cubre TODA la Matriz

No es "INT-07 solo vive en Captar×Salud". Cada inteligencia tiene algo que decir sobre cada celda desde su lente. 21 × 18 = 378 preguntas de coordenada mínimo.

### La Matriz como campo activo

| Función | Cómo |
|---------|------|
| Campo de fuerza | Gaps dirigen qué preguntas ejecutar |
| Banco de preguntas con coordenadas | Cada pregunta ubicada en inteligencia × lente × función |
| DB de efectos | Cada ejecución registra qué celdas llenó y cuánto |
| Detector de puntos ciegos | Celdas donde ninguna INT cierra el gap = huecos reales |
| Esquema de inversión de documentos | Reactor v2 ubica cada pregunta extraída en la Matriz |
| Verificador de cierre | ¿Se cerró el gap? Si no → escalar |
| Lookup de configuraciones | Patrón de gaps → configuración óptima histórica (§6B) |

---

## 3. EL ÁLGEBRA = COMPILADOR DE PROMPTS

Las operaciones algebraicas son **operaciones de ensamblaje de redes de preguntas:**

```
Fusión ∫(A|B):     Prompt = [preguntas de A] + [preguntas de B] en paralelo
Composición A→B:   Prompt = [preguntas de A], luego [preguntas de B sobre output de A]
Diferencial A-B:   Prompt = [preguntas que A tiene y B no puede tener]
Integración ∫:     Prompt = [preguntas que emergen al cruzar las anteriores]
Loop test A→A:     Prompt = [mismas preguntas sobre su propio output]
```

### Propiedades confirmadas (34 chats cartografía)

| Propiedad | Resultado | Implicación para el compilador |
|-----------|-----------|-------------------------------|
| Composición NO conmutativa | A→B ≠ B→A siempre | Formal primero → humano después |
| NO asociativa | (A→B)→C ≠ A→(B→C) | Secuencia lineal, no reorganizar |
| Fusión parcialmente conmutativa | ~25% | Orden de fusión afecta framing |
| No idempotente | 18/18 | Loop test siempre justificado. 2 pasadas óptimo |
| Saturación en n=2 | 3ª pasada aporta 10-15% | No hacer 3ª excepto calibración |
| Clausura | output ∈ input | Cualquier output puede alimentar otra INT |
| Distributividad izq ~70% | Pierde ~30% al factorizar | Aceptable para ahorro, no para pares TOP |
| Distributividad der PROHIBIDA | Valor irreducible del cruce | Nunca factorizar |

### 13 reglas del compilador

**Selección:** (1) Núcleo irreducible: 1 cuantitativa + 1 humana + INT-16. (2) Máximo diferencial entre categorías. (3) Sweet spot: 4-5 inteligencias.

**Orden:** (4) Formal primero. (5) No reorganizar secuencia. (6) Fusiones: primero la más alineada con el sujeto.

**Profundidad:** (7) 2 pasadas por defecto. (8) No tercera pasada.

**Paralelización:** (9) Fusiones izquierda paralelizables al ~70%. (10) Cruce derecho no factorizable.

**Patrones universales:** (11) Marco binario es universal → INT-14+INT-01 primero. (12) Conversación pendiente es universal. (13) Infrautilización antes de expansión.

---

## 4. PIPELINE — FLUJO DE UNA EJECUCIÓN

### Arquitectura de modelos: OS ejecuta, premium evalúa

```
PRINCIPIO: La inteligencia está en las preguntas, no en el modelo.
           Si un modelo OS cierra gaps bajo las preguntas correctas,
           la Matriz funciona. El modelo es commodity.

EJECUTOR (modelo open source — Llama 3.1 70B vía Groq/Together/Fireworks):
  → Pasos 5 (ejecución bajo preguntas)
  → Coste: ~$0.001 por ejecución
  → Ventaja: volumen masivo — miles de ejecuciones viables

EVALUADOR (Sonnet/Opus — Anthropic API):
  → Pasos 6-7 (verificación de cierre + scoring con coordenadas)
  → Coste: ~$0.03 por evaluación
  → Ratio: 10 ejecuciones OS → 1 evaluación premium (batch)

CÓDIGO PURO (sin LLM):
  → Pasos 0, 3, 4 (detector huecos, composición, ensamblaje)
  → Coste: $0

LIGERO (Haiku o modelo OS pequeño):
  → Pasos 1-2 (campo gradientes, routing)
  → Coste: ~$0.001
```

### Selección de preguntas: heurístico + probabilístico gradual

| Decisión | Mecanismo | Por qué |
|----------|-----------|---------|
| Qué celdas priorizar | Heurístico: gaps como datos | Gap mayor = más prioridad. Determinista |
| 13 reglas del compilador | Heurístico: restricciones duras | Empírico de cartografía |
| Dependencias lentes/funciones | Heurístico: estructurales | Captar sin Depurar = basura. Siempre |
| Qué INT cierra mejor un gap | Heurístico → probabilístico con datos | Sin datos: reglas. Con 100+ ejecuciones: Bayesian update |
| Qué preguntas de una celda incluir | El LLM opera bajo la red completa | Las preguntas SON el prompt |
| Escalar a profunda vs repetir base | Heurístico → expected value con datos | P(cierre|base) vs P(cierre|profunda) × coste |
| Detección de falacias | Heurístico: binario | Errores de tipo — o lo es o no |

### El pipeline (7 pasos)

```
INPUT
  │
  ▼
PASO 0: DETECTOR HUECOS           ~200ms | $0 | código puro
  7 primitivas + 8 operaciones sintácticas
  → Qué falta en el input
  → Señales para el campo de gradientes
  → Falacias aritméticas en el input
  │
  ▼
PASO 1: CAMPO DE GRADIENTES        ~1-3s | ~$0.001 | código + modelo OS pequeño
  Para cada celda (21):
  → grado_actual, grado_objetivo, gap
  → Dependencias entre lentes y funciones
  → Output: campo de 21 gradientes ordenados por gap
  │
  ▼
PASO 2: ROUTING POR GRADIENTE      ~500ms | ~$0.001 | modelos ligeros + fallback Sonnet
  Para cada celda con gap > 0.3:
  → ¿Qué INT cierra ESTE gap con más efectividad?
  → Top 3-5 inteligencias por impacto total
  │
  ▼
PASO 3: COMPOSICIÓN                 ~200ms | $0 | NetworkX/código puro
  → Álgebra ensambla red de preguntas (fusión, composición, etc.)
  → 13 reglas como restricciones duras
  → Dependencias informan secuencia
  │
  ▼
PASO 4: ENSAMBLAJE DEL PROMPT       ~100ms | $0 | código puro
  Para cada celda objetivo:
  → Preguntas de esa coordenada (INT × lente × función)
  → Priorizadas por gap_medio_cerrado (dato acumulado)
  → La red de preguntas resultante ES el prompt
  → No hay texto imperativo. Solo preguntas.
  │
  ▼
PASO 5: EJECUCIÓN                   5-30s | ~$0.001 | modelo OS (Llama 3.1 70B)
  El agente opera BAJO las preguntas como prompt interno
  → Modelo OS para ejecución masiva (Fase A exploración)
  → Sonnet/Opus para ejecución premium (Fase B servicio)
  → Código puro: cálculos
  │
  ▼
PASO 6: VERIFICACIÓN DE CIERRE      ~3-10s | ~$0.03 | Sonnet (evaluador premium)
  Re-evalúa campo de gradientes POST-ejecución
  → ¿Se cerró el gap por celda?
  → Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  → Max 2 re-intentos por celda
  → Registra gap_cerrado por pregunta → alimenta score_efectividad
  → En Fase A: batch de 10 ejecuciones → 1 evaluación
  │
  ▼
PASO 7: INTEGRACIÓN + REGISTRO      10-20s | ~$0.03 | Sonnet
  Síntesis final
  → Output con mapa de cubierto y pendiente
  → Registro de efectos con coordenadas
  → Actualiza gap_medio_cerrado (aprendizaje)
  → Actualiza configuraciones_efectivas (patrón → configuración ganadora)

TOTAL FASE A (exploración): ~$0.04 por ciclo completo | ~$4 por 100 ciclos
TOTAL FASE B (servicio):    ~$0.10-0.50 por consulta (solo configuración ganadora)
```

### 4 modos (configuraciones del mismo pipeline)

| Modo | Campo | INTs típicas | Latencia | Coste |
|------|-------|-------------|----------|-------|
| Análisis | 21 celdas completo | 3-5 por gradientes | 40-150s | $0.50-1.50 |
| Conversación | Solo celdas que el turno toca | 1-2 rápido | 5-20s | $0.05-0.15 |
| Generación | Orientado al output deseado | Creativas: 14,15,09,12 | 30-90s | $0.30-0.80 |
| Confrontación | Busca gaps que la propuesta ignora | Frontera: 17,18,06 | 30-90s | $0.30-0.80 |

---

## 5. AUTO-DIAGNÓSTICO — LA MATRIZ SOBRE SÍ MISMA

El sistema usa la misma Matriz 3L×7F para verse a sí mismo. Las celdas del sistema tienen grado, objetivo y gap — igual que las del usuario. La mejora continua se dirige por gaps, no por intuición.

Convergencia: cuando una celda del usuario está débil Y la celda equivalente del sistema también → doble riesgo: "no puedo cubrir un gap del usuario que es mi propio gap".

---

## 6. LOS MOTORES = FÁBRICA DE LA MATRIZ

Los motores no son el producto. Son la maquinaria que construye, llena y mejora la Matriz.

| Motor | Qué hace con la Matriz | Estado |
|-------|----------------------|--------|
| Cartografía (Fase A) | La llenó por primera vez — 18 INT × 3 casos × preguntas fijas | ✅ Completada |
| Reactor v1 (Fase B) | La amplifica con datos sintéticos → 1.183 datapoints | ✅ Completada |
| Modelos ligeros (Fase C) | Entrenan sobre datos de B para routing/scoring eficiente | 🔄 C3,C4 pasan. C1,C2 mejorando |
| **Motor v1 (Fase D)** | **RUNTIME — ejecuta masivamente con modelo OS, evalúa con premium** | ⬜ Siguiente |
| Reactor v2 | La enriquece invirtiendo documentos → preguntas de dominio | ⬜ Post motor |
| Reactor v3 | La enriquece desde conceptos teóricos fundacionales → preguntas con raíz verificada | ⬜ Puede ir en paralelo |
| Meta-motor | La evoluciona — razona sobre las preguntas → preguntas mejores | ⬜ Con datos reales |

### Motor v1 — por qué es crítico

Sin Motor v1, la Matriz es un documento estático. Con Motor v1, la Matriz es un sistema vivo:

```
SIN Motor v1:
  Preguntas existen pero nadie las ejecuta
  Sin datos de efectividad (gap_medio_cerrado = null para todo)
  El routing es teórico — no sabe qué INT cierra qué gap
  Los reactores v2/v3 llenan la Matriz a ciegas sin saber qué funciona

CON Motor v1:
  Pipeline 7 pasos convierte gaps en prompts de preguntas → ejecuta → verifica cierre
  Cada ejecución registra gap_cerrado por pregunta → selección natural
  El routing se calibra con datos reales de efectividad
  Los reactores v2/v3 saben qué celdas necesitan más preguntas (datos de cobertura)
  El modelo OS permite volumen masivo → la Matriz aprende rápido
```

Motor v1 genera los datos que hacen que todo lo demás funcione: routing probabilístico, poda de preguntas inefectivas, priorización por efectividad real. Es la pieza que convierte la Matriz de banco de preguntas en sistema que aprende.

Ciclo de vida:
```
Cartografía → CREA la Matriz (preguntas base, empírico)
Reactor v1  → AMPLIFICA la Matriz (datos sintéticos)
Reactor v3  → ENRIQUECE la Matriz (preguntas desde conceptos teóricos fundacionales)
Motor v1    → USA la Matriz sobre casos reales (y registra efectividad — CRÍTICO)
             → Modelo OS ejecuta masivamente (~$0.001/ejecución)
             → Sonnet evalúa batch (~$0.03/evaluación)
             → Ratio 10:1 → datos masivos a bajo coste
Reactor v2  → ENRIQUECE la Matriz (preguntas de dominio desde documentos invertidos)
Meta-motor  → EVOLUCIONA la Matriz (preguntas mejores por razonamiento sobre preguntas)
                    │
                    └→ vuelta al Motor v1 con Matriz mejorada
```

Lo que NO cambia nunca: la estructura 3L × 7F (L0). Lo que mejora: las preguntas y su efectividad (L2).

---

## 6B. MOTOR v1 — DOS FASES DE OPERACIÓN

### Fase A: Exploración (llena la Matriz)

El Motor v1 arranca en modo exploración. Ejecuta todas las operaciones algebraicas sobre cada caso, registra qué cierra gaps y qué no.

```
Caso nuevo entra
    ↓
Motor OS ejecuta protocolo de exploración completo:
  - 18 INTs individuales
  - Composiciones de irreducibles
  - Fusiones top
  - Loop tests
  - Muestreo aleatorio
    ↓
Sonnet evalúa batch:
  - ¿Qué gaps cerró cada operación?
  - ¿Qué combinación fue más efectiva?
  - Coordenadas: lente × función × INT × operación
    ↓
Matriz registra TODO con score de efectividad
    ↓
Tabla configuraciones_efectivas se llena
```

### Protocolo de exploración (5 tiers)

```
Tier 1 (siempre):  18 INTs individuales sobre el caso
Tier 2 (siempre):  6 irreducibles en composición = 30 pares (A→B y B→A)
Tier 3 (siempre):  TOP 10 fusiones derivadas de Cartografía
Tier 4 (siempre):  Loop test sobre top 3 resultados de Tiers 1-3
Tier 5 (muestreo): 10% de combinaciones restantes seleccionadas aleatoriamente

Total: ~70-80 ejecuciones por caso
Coste: ~$0.08 OS + ~$0.24 Sonnet (batch 10:1) = ~$0.32 por caso completo
```

Los tiers NO son fijos — son hipótesis. El enjambre meta-protocolo (§6C) los reconfigura con datos.

### Fase B: Lookup (usa la Matriz llena)

Cuando una celda tiene suficientes datos, el Motor pasa a modo servicio para esa celda.

```
Caso nuevo entra
    ↓
Detector de huecos → patrón de gaps
    ↓
Lookup en configuraciones_efectivas:
  "Este patrón de gaps lo he visto 47 veces.
   La configuración INT-01→INT-14 fusión cierra
   el 82% en Salud×Captar."
    ↓
Ejecuta SOLO la configuración ganadora
    ↓
Respuesta en segundos, no minutos
```

### Transición Fase A → Fase B

La transición NO es binaria ni global — es por celda. Criterio por celda:

```
SI (n_ejecuciones_patron > 30 AND tasa_cierre_config_ganadora > 0.60):
  → Fase B para esta celda (lookup directo)
SINO:
  → Fase A (seguir explorando)
```

Algunas celdas estarán en Fase B con 50 casos mientras otras siguen explorando con 200.

### Arquitectura 4 capas del Motor v1

```
CAPA 1: EJECUTOR (modelo OS — Llama 3.1 70B vía Groq)
  → Ejecuta protocolo de exploración sobre casos
  → Genera datos brutos
  → Coste: ~$0.001/ejecución

CAPA 2: EVALUADOR (Sonnet — Anthropic API)
  → Scoring con coordenadas exactas (lente × función × INT)
  → Registra en Matriz: gap_cerrado, score_efectividad
  → Batch 10 ejecuciones → 1 evaluación
  → Coste: ~$0.03/evaluación

CAPA 3: META-PROTOCOLO (enjambre — ver §6C)
  → Analiza patrones en configuraciones_efectivas
  → Reestructura tiers del protocolo de exploración
  → Propone añadir/podar INTs (CR0 → Jesús cierra)
  → Se activa a partir del caso 50

CAPA 4: LOOKUP (código puro — $0)
  → Cuando hay datos suficientes, respuesta directa
  → Sin LLM, solo pattern matching sobre DB
  → Fase B: respuesta en milisegundos
```

### Riesgo y mitigación

Si el modelo OS es demasiado débil, la mayoría de ejecuciones no cierran gaps → se entrena la Matriz sobre fracasos. Mitigación:

```
1. Arrancar con Llama 3.1 70B (mínimo viable)
2. Si tasa_cierre < 15% tras 50 casos → escalar a modelo OS más grande
3. Las preguntas que cierran gaps INCLUSO con modelo débil = las más robustas
   → Esto es dato valioso: robustez de preguntas independiente de modelo
```

---

## 6C. ENJAMBRE META-PROTOCOLO

### Qué es

Un enjambre cuya función específica es optimizar la asignación de compute de exploración. No opera sobre las preguntas (eso es el meta-motor) sino sobre el **protocolo de exploración mismo**.

### Qué hace

```
Observa resultados de N casos →

PROMOCIÓN:
  "Tier 5 descubrió que INT-13×INT-06 cierra gaps en
   Continuidad×Frontera que ningún Tier 1-4 cubre.
   → Promocionar a Tier 3."

DEGRADACIÓN:
  "Tier 2: las composiciones INT-10→INT-12 nunca cierran nada.
   → Degradar a Tier 5 (muestreo)."

AJUSTE DE PROFUNDIDAD:
  "Loop test sobre top 3 es insuficiente.
   Loop test sobre top 5 cierra 18% más.
   → Expandir Tier 4."

EVOLUCIÓN L1 (propuesta CR0):
  "INT-15 (Cinestésica) no cierra gaps en ningún contexto
   no-corporal tras 100 casos.
   → Proponer poda a Jesús."

  "Patrón recurrente: gaps en Sentido×Adaptar que ninguna
   INT cubre. ¿Falta una inteligencia?
   → Proponer investigación a Jesús."
```

### Cuándo se activa

```
Caso 0-49:    Protocolo fijo (tiers iniciales). Acumula datos.
Caso 50:      Primera ejecución del meta-protocolo. Re-evalúa tiers.
Cada 50 casos: Re-evaluación periódica.
Evento:       Si tasa_cierre global cae >10% entre ciclos → trigger inmediato.
```

### Output

El meta-protocolo produce propuestas CR0 (Jesús cierra):
- Cambios en tiers (qué se promociona, degrada, añade)
- Propuestas de poda/adición de INTs (cambio L1)
- Alertas de anomalías (caídas bruscas de efectividad)

---

## 6D. ECOSISTEMA DE ENTRENAMIENTO

### El ciclo cerrado

```
REACTORES (generan preguntas):
  Reactor v1 → datos sintéticos (score_efectividad = null)
  Reactor v3 → preguntas desde conceptos teóricos (score_efectividad = null)
  Reactor v2 → preguntas invertidas de documentos (score_efectividad = null)
       ↓
MOTOR v1 (verifica efectividad):
  Ejecuta masivamente con modelo OS bajo las preguntas generadas
  → Las preguntas de Reactores se ponen a prueba
  → Se registra gap_cerrado real por pregunta
       ↓
EVALUADOR (puntúa):
  Sonnet/Opus evalúa resultados batch
  → score_efectividad se llena con datos reales
  → Preguntas que no cierran gaps → se podan o refinan
       ↓
MATRIZ (aprende):
  → Selección natural de preguntas (las que cierran sobreviven)
  → Configuraciones óptimas por patrón de gaps
  → Las preguntas más robustas = las que cierran con modelo débil
       ↓
META-PROTOCOLO (optimiza):
  → Ajusta tiers de exploración
  → Propone cambios L1 (INTs)
       ↓
  └→ vuelta a Reactores con señales de qué celdas necesitan más preguntas
```

### Lo que se entrena simultáneamente

```
1. LA MATRIZ:        qué preguntas cierran qué gaps (L2)
2. EL MOTOR:         qué configuraciones son óptimas por contexto (L2)
3. LAS INTs:         cuáles son irreducibles y cuáles son ruido (L1)
4. EL PROTOCOLO:     qué explorar y con qué prioridad (L2)
5. LOS REACTORES:    qué celdas necesitan más preguntas (feedback loop)
```

### Coste estimado del ecosistema

```
100 casos × protocolo completo:
  Motor OS:    100 × 75 ejecuciones × $0.001 = $7.50
  Evaluador:   100 × 8 evaluaciones × $0.03  = $24.00
  Total:       ~$31.50 por 100 casos completos

1.000 casos:  ~$315
  → Suficiente para llenar configuraciones_efectivas
  → Suficiente para primer ciclo de meta-protocolo (3-4 veces)
  → Suficiente para primera propuesta de poda/adición L1
```

---

## 7. PROFUNDIDAD PROGRESIVA

```
NIVEL BASE (~50 preguntas): Genéricas. Origen: Cartografía.
NIVEL PROFUNDA (~150, por sub-dominio): Especialista. Origen: Reactor v2 + Claude.
NIVEL EXPERTA (~300+, por sub-dominio): 20 años experiencia. Origen: Manuales invertidos.
```

---

## 8. INFRAESTRUCTURA

### Decisiones cerradas (CR1 2026-03-09)

| Decisión | Elegido | Razón |
|----------|---------|-------|
| Motor + DB | fly.io Postgres + pgvector | Colocalizada, sin dependencias externas |
| Ejecutor Motor v1 | Modelo OS (Llama 3.1 70B) vía Groq/Together/Fireworks | ~$0.001/ejecución. Volumen masivo viable |
| Evaluador Motor v1 | Sonnet vía Anthropic API | Scoring premium con coordenadas. Batch 10:1 |
| Exocortex Pilates | fly.io (nuevo) | Se crea de cero, misma esencia |
| Exocortex Clínica | fly.io (nuevo) | Igual |
| Supabase | Se depreca gradualmente | 402 incluso con upgrade |

### Qué se mantiene de la arquitectura Supabase

Estigmergia, enjambres, telemetría, mejora continua — todos son patrones en tablas Postgres. Se llevan tal cual. Se reemplazan 4 piezas de fontanería: Edge Functions → Node/Python, pg_net → workers/colas, cron → node-cron, auth → JWT.

### Stack técnico

```
fly.io:
  Python/FastAPI         — Motor cognitivo + API
  fly.io Postgres        — Matriz, efectos, telemetría, estado
  scikit-learn           — Modelos ligeros C1-C4
  NetworkX + scipy       — Grafo compositor
  Anthropic API          — Sonnet, Opus (evaluador premium, 4 keys rotativas)

Inferencia OS (APIs commodity):
  Groq                   — Llama 3.1 70B (ejecutor principal, más rápido)
  Together / Fireworks   — Fallback / modelos alternativos
  → El ejecutor es intercambiable. Si sale un OS mejor, se cambia sin tocar nada.

Supabase (se depreca):
  99 Edge Functions      — Siguen hasta que fly.io las reemplace
  PostgreSQL             — Sistema nervioso actual
```

---

## 9. ESQUEMA DB (fly.io Postgres)

```sql
-- INTELIGENCIAS
CREATE TABLE inteligencias (
    id TEXT PRIMARY KEY,
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

-- GRAFO COMPOSITOR
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

-- BANCO DE PREGUNTAS CON COORDENADAS
CREATE TABLE preguntas_matriz (
    id TEXT PRIMARY KEY,
    inteligencia TEXT NOT NULL,
    lente TEXT NOT NULL,
    funcion TEXT NOT NULL,
    pensamiento TEXT,
    modo TEXT,
    nivel TEXT DEFAULT 'base',
    sub_dominio TEXT,
    texto TEXT NOT NULL,
    fuente TEXT,
    score_efectividad FLOAT,
    gap_medio_cerrado FLOAT
);

-- MARCO LINGÜÍSTICO
CREATE TABLE operaciones_sintacticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    input_tipo TEXT NOT NULL,
    output_tipo TEXT NOT NULL,
    propiedad_clave TEXT NOT NULL,
    pregunta_detectora TEXT NOT NULL,
    propiedades_algebraicas JSONB
);

CREATE TABLE tipos_acople (
    id SERIAL PRIMARY KEY,
    conjuncion TEXT UNIQUE NOT NULL,
    tipo TEXT NOT NULL,
    diagnostico TEXT NOT NULL
);

CREATE TABLE falacias_aritmeticas (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL,
    operacion_incorrecta TEXT NOT NULL,
    correccion TEXT NOT NULL
);

-- CAMPO DE GRADIENTES
CREATE TABLE campo_gradientes (
    ejecucion_id TEXT PRIMARY KEY,
    input_texto TEXT,
    gradientes JSONB NOT NULL,
    dependencias_lentes JSONB,
    dependencias_funciones JSONB,
    top_gaps JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- EFECTOS CON COORDENADAS
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

-- EJECUCIONES (telemetría)
CREATE TABLE ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    modelo_ejecutor TEXT,              -- NUEVO: qué modelo OS ejecutó
    huecos_detectados JSONB,
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,
    feedback_usuario JSONB,
    fase TEXT DEFAULT 'A'              -- NUEVO: 'A' exploración / 'B' lookup
);

-- CONFIGURACIONES EFECTIVAS POR PATRÓN DE GAPS (NUEVO)
CREATE TABLE configuraciones_efectivas (
    id SERIAL PRIMARY KEY,
    patron_gaps JSONB NOT NULL,        -- fingerprint del campo de gradientes
    configuracion JSONB NOT NULL,      -- INTs + operación + orden
    contexto_tipo TEXT,                -- dominio/sector si aplica
    tasa_cierre FLOAT,                -- % gaps cerrados
    n_ejecuciones INT DEFAULT 1,      -- cuántas veces probada
    gap_medio_cerrado FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- PROTOCOLO DE EXPLORACIÓN (NUEVO)
CREATE TABLE protocolo_tiers (
    id SERIAL PRIMARY KEY,
    tier INT NOT NULL,                 -- 1-5
    descripcion TEXT NOT NULL,
    configuraciones JSONB NOT NULL,    -- lista de operaciones en este tier
    activo BOOLEAN DEFAULT TRUE,
    version INT DEFAULT 1,             -- incrementa con cada ajuste del meta-protocolo
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- HISTORIAL META-PROTOCOLO (NUEVO)
CREATE TABLE meta_protocolo_log (
    id SERIAL PRIMARY KEY,
    caso_trigger INT NOT NULL,         -- número de caso que disparó la re-evaluación
    cambios JSONB NOT NULL,            -- promociones, degradaciones, ajustes
    propuestas_l1 JSONB,              -- propuestas de poda/adición de INTs (CR0)
    metricas_antes JSONB NOT NULL,
    metricas_despues JSONB,
    aprobado_por TEXT,                 -- null = pendiente, 'jesus' = CR1
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- VECTORES (router futuro)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);
```

---

## 10. CHECKLIST — ESTADO ACTUAL

### Fase A: Cartografía ✅
- [x] 18 INT × 3 casos = 54 análisis completos
- [x] Loop tests (P06): 18/18 no idempotentes
- [x] Saturación (P07): n=2 óptimo confirmado
- [x] 3 matrices de diferenciales
- [x] TOP 10 pares complementarios por caso
- [x] 8 propiedades algebraicas testeadas
- [x] 13 reglas para el compilador derivadas
- [x] OUTPUT_FINAL compilado

### Fase B: Datos sintéticos ✅
- [x] B1: 200 casos × 10 dominios
- [x] B2: 540 peticiones → inteligencias
- [x] B3: 300 datapoints composición
- [x] B4: 180 outputs scoring
- [x] Total: 1.183 datapoints, $1.99

### Fase C: Modelos ligeros 🔄
- [x] C3 Compositor: frecuencias de orden — PASA
- [x] C4 Scorer: Ridge 9 features, Pearson 0.81 — PASA
- [ ] C1 Router: TF-IDF + centroides, 77.8% (iterando, fallback Sonnet)
- [ ] C2 Clasificador: RF, F1 53% (pasa ajustado, fallback Sonnet)

### Decisiones infraestructura ✅
- [x] DB del motor → fly.io Postgres + pgvector
- [x] Todo en fly.io, Supabase se depreca
- [x] Arquitectura enjambres/estigmergia se lleva tal cual
- [x] Motor v1 ejecutor = modelo OS (Llama 3.1 70B vía Groq)
- [x] Motor v1 evaluador = Sonnet (Anthropic API, batch 10:1)

### Modelo conceptual ✅
- [x] Prompt del agente = red de preguntas
- [x] Motores = fábrica de la Matriz
- [x] Álgebra = compilador de prompts
- [x] 8 operaciones = gramática de preguntas
- [x] 3 niveles estabilidad: L0/L1/L2
- [x] Heurístico macro + probabilístico gradual
- [x] Motor v1 en dos fases: exploración (A) → lookup (B)
- [x] Ecosistema de entrenamiento: Reactores generan → Motor verifica
- [x] Enjambre meta-protocolo sobre tiers de exploración

### Fase D: Motor v1 MVP ⬜ SIGUIENTE
- [ ] Pipeline end-to-end en fly.io
- [ ] Capa 0 (detector huecos) funcional
- [ ] Campo de gradientes sobre input
- [ ] Router por gradiente (modelos ligeros + fallback Sonnet)
- [ ] Compositor con 13 reglas
- [ ] Red de preguntas como prompt del agente
- [ ] Integración Groq API (Llama 3.1 70B) como ejecutor
- [ ] Integración Anthropic API (Sonnet) como evaluador batch
- [ ] Protocolo de exploración 5 tiers implementado
- [ ] Tabla configuraciones_efectivas operativa
- [ ] Tabla protocolo_tiers con tiers iniciales
- [ ] Verificación de cierre de gaps
- [ ] 4 modos funcionando
- [ ] Test E2E con 3 casos de cartografía
- [ ] Telemetría en DB
- [ ] Transición automática Fase A → B por celda

### Fase D2: Meta-protocolo ⬜ CASO 50+
- [ ] Enjambre meta-protocolo activado
- [ ] Primer ciclo de re-evaluación de tiers
- [ ] Primera propuesta L1 (poda/adición INTs) generada

### Fase E: Chat funcional ⬜ DESPUÉS
- [ ] Chief of Staff usa Matriz para conversar
- [ ] Estado persistente con mapa 3L×7F del usuario
- [ ] Datos reales alimentan re-entrenamiento

### Fase F: Pilotos + Reactor v2 ⬜ DESPUÉS
- [ ] Uso real genera datos reales
- [ ] Reactor v2 invierte documentos técnicos
- [ ] Re-entrenamiento con datos reales
- [ ] Meta-motor como ciclo semanal

### Reactor v3: Generación Conceptual ⬜ PUEDE IR EN PARALELO
- [ ] Validar mecanismo con categoría no-obvia (Contemplativa o Corporal-Perceptual)
- [ ] Ejecutar 9 categorías (~$10-18)
- [ ] Poblar Matriz con ~3.000-5.000 preguntas con coordenadas + fuente teórica
- [ ] Identificar preguntas inter-celda y patrones diagnósticos
- [ ] Ejemplo validado: Sistémica (ver EJEMPLO_GENERACION_CONCEPTUAL_SISTEMICA.md)

---

## 11. ROADMAP — ORDEN DE IMPLEMENTACIÓN

### Ola 1 — Ahora (paralelo)
- **Motor v1 MVP en fly.io** — pipeline end-to-end con ejecutor OS + evaluador premium. Fase A exploración desde día 1.
- **Reactor v3 conceptual** — poblar Matriz con preguntas desde fundamentos teóricos (~$10-18)
- **Fase B1 abducción manuales** — cuando Jesús suba los manuales fisio/pilates

### Ola 1.5 — Motor aprende (caso 50+)
- Meta-protocolo se activa y re-evalúa tiers
- Primeras configuraciones_efectivas con datos suficientes → celdas pasan a Fase B
- Primera propuesta L1 (poda/adición INTs)
- Reactores reciben feedback: qué celdas necesitan más preguntas

### Ola 2 — Motor funcional
- Integrar preguntas nivel 2-3 de manuales
- Exocortex Pilates como primer tenant
- Exocortex Clínica como segundo tenant

### Ola 3 — Retroalimentación
- Datos reales refinan router y compositor
- Reactor v2 con documentos técnicos
- Meta-motor con datos reales
- Modelos ligeros re-entrenados con datos de producción

---

## 12. PRINCIPIOS DE DISEÑO

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es intercambiable. La Matriz es permanente.
2. **Percibir antes de razonar.** Campo de gradientes primero. Sin saber qué funciones están débiles, el routing es ciego.
3. **Cada modelo hace lo que mejor sabe.** LLMs para generar. Embeddings para buscar. Grafos para optimizar. Código para calcular. OS para volumen. Premium para evaluar.
4. **El motor no tiene opinión.** Selecciona preguntas, ejecuta, devuelve lo que emerge.
5. **Empujar, no reaccionar.** El sistema mide el gap, empuja hacia objetivo, verifica cierre. Si no cierra, escala.
6. **Las lentes y funciones no son independientes.** El diagnóstico ve las dependencias.
7. **Menos es más.** 4 inteligencias sobre gaps grandes > 18 sobre todo.
8. **Retroalimentación con coordenadas.** Cada ejecución registra qué gaps cerró. Selección natural de preguntas.
9. **Profundidad progresiva.** Base para todo. Profunda donde el dominio requiere. Experta con uso real.
10. **Las 8 operaciones son gramática, no diccionario.** Se generan preguntas desde raíces × operaciones.
11. **La raíz es invariante, el sufijo es operación.** El motor opera sobre raíces — las manifestaciones son derivadas.
12. **La patología no es la cantidad de errores, es la conectividad.** Errores encadenados = patología. Aislados = señales.
13. **Las preguntas son el combustible.** Los datos se agotan. Las preguntas generan datos infinitamente.
14. **Todo texto experto es preguntas comprimidas.** El Reactor v2 las recupera.
15. **Las preguntas se pueden razonar.** El meta-motor las evoluciona.
16. **La Matriz es el esqueleto.** Unifica percepción, razonamiento, almacenamiento y aprendizaje.
17. **El sistema se ve a sí mismo.** Propiocepción con la misma resolución que usa para el usuario.
18. **Volumen barato antes que calidad cara.** Modelo OS ejecuta masivamente. Premium solo evalúa. Los datos mandan.
19. **El protocolo se entrena a sí mismo.** El enjambre meta-protocolo optimiza la exploración con datos, no con intuición.
20. **Robustez > rendimiento pico.** Preguntas que cierran gaps con modelo débil son más valiosas que las que solo funcionan con modelo fuerte.

---

## 13. RELACIÓN CON OTROS DOCUMENTOS

| Documento | Relación | Estado |
|-----------|----------|--------|
| **Este documento** | Fuente de verdad del sistema completo | Activo |
| META_RED_INTELIGENCIAS_CR0.md | 18 inteligencias como redes de preguntas | Fuente L1 |
| TABLA_PERIODICA_INTELIGENCIA_CR0.md | 18 álgebras con firmas y puntos ciegos | Fuente L1 |
| ALGEBRA_CALCULO_SEMANTICO_CR0.md | Operaciones del cálculo semántico | Fuente L0 |
| MARCO_LINGUISTICO_COMPLETO.pdf | 8 operaciones + gramática generativa | Fuente L0 |
| OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md | Resultados de 34 chats de cartografía | Fuente datos |
| PROTOCOLO_CARTOGRAFIA_META_RED_v1.md | Protocolo de ejecución de cartografía | Referencia |
| L0_7_FUNCIONES_NUCLEARES.md | Las 7F + 3L que generan la Matriz | Fuente L0 |
| L0_5_MECANISMO_UNIVERSAL_VINCULACION.md | Mecanismo universal de mapas | Fuente L0 |
| SPEC_REACTOR_V1.md | Spec del generador de datos sintéticos | Implementación |
| EJEMPLO_GENERACION_CONCEPTUAL_SISTEMICA.md | Mecanismo validado de generación conceptual | Referencia |
| CONTEXTO_SISTEMA.md | Estado de implementación Supabase | L2 (se depreca) |
| MEMORY.md | Estado operativo del sistema nervioso | L2 (operativo) |

**Documentos que este reemplaza (no borrar, mantener como histórico):**
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md
- SISTEMA_COGNITIVO_OMNI_MIND_v2.md
- ACTUALIZACION_DISENO_V2_SECCIONES_20_22.md

---

**FIN DOCUMENTO MAESTRO CONSOLIDADO — CR0**
