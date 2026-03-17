# OMNI-MIND — CONTEXTO ESENCIAL


## motor-semantico/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md

# SISTEMA COGNITIVO OMNI-MIND — DOCUMENTO MAESTRO CONSOLIDADO

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-09 (actualizado 2026-03-09 noche)
**Supersede:** DISENO_MOTOR_SEMANTICO_v1.md, DISENO_MOTOR_SEMANTICO_v2.md, SISTEMA_COGNITIVO_OMNI_MIND_v2.md, ACTUALIZACION_DISENO_V2_SECCIONES_20_22.md
**Origen:** Consolidación de 4 documentos + decisiones sesiones 2026-03-09

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
| Motor v1 ejecutor = multi-modelo OS (no uno solo) | Sesión 09-mar-b | §6B, §8 |
| Evaluador = Sonnet + mapeo a 3L×7F | Sesión 09-mar-b | §6B |
| Enjambre de modelos como dimensión algebraica | Sesión 09-mar-b | §6B, §12 |
| Protocolo exploración 5 tiers | Sesión 09-mar-b | §6B |
| Enjambre meta-protocolo optimiza exploración | Sesión 09-mar-b | §6C |
| Ecosistema entrenamiento: Reactores generan → Motor verifica | Sesión 09-mar-b | §6D |
| **DOS SISTEMAS: Motor vN (hacia fuera) + Gestor de la Matriz (hacia dentro)** | Sesión 09-mar-c | §1, §6, §6E |
| **Gestor de la Matriz = compilador central que alimenta todos los consumidores** | Sesión 09-mar-c | §6E |
| **Stack OS-first: orquestador + ejecutores + evaluador todo OS (Sonnet solo referencia inicial)** | Sesión 09-mar-c | §8 |
| **Feedback loop: datapoint de efectividad por ejecución + vista materializada** | Sesión 09-mar-c | §6E |
| **Multi-modelo validado: 3 OS superan a Claude. V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79)** | Sesión 09-mar-c | §6B, §12 |
| **Asignación modelo→celda empírica: V3.1 7 celdas, R1 7, GPT-OSS 4, Claude 1** | Sesión 09-mar-c | §6B |
| **Migración OS del Sistema Nervioso: ~53 agentes LLM de Anthropic → OS** | Sesión 09-mar-c | §8B |
| **Motor v3.3 / Primitivas v2: todo a OS (mayor consumidor LLM del sistema)** | Sesión 09-mar-c | §8B |
| **Chief of Staff DEPRECADO: Motor v3.3 + Matriz reemplaza su funcionalidad** | Sesión 09-mar-c | §8B |
| **llm-proxy multi-provider: un solo punto de cambio para toda la migración** | Sesión 09-mar-c | §8B |
| **Motor de auto-mejora: enjambre de código OS (V3.2+Qwen Coder+Cogito+V3.1) DENTRO del sistema** | Sesión 10-mar | §6F |
| **Fábrica de Exocortex: el sistema diseña, implementa y despliega exocortex nuevos autónomamente** | Sesión 10-mar | §6F |
| **DeepSeek V3.2 como candidato a reemplazar TODOS los roles premium (ejecutor+evaluador+orquestador+coder)** | Sesión 10-mar | §6F, §8 |
| **Experimento 1: 4 modelos nuevos (V3.2, Qwen3 Thinking, Kimi K2.5, Cogito 671B)** | Sesión 10-mar | §10 |
| **Reactor v4: genera preguntas desde datos REALES de operación de cada exocortex** | Sesión 10-mar | §6, §6D-2 |
| **Flywheel: cada cliente nuevo enriquece la Matriz para todos los demás** | Sesión 10-mar | §6D-2, §12 |
| **Prompts vivos: agentes evolucionan con el negocio sin intervención (3 mecanismos)** | Sesión 10-mar | §6D-2 |
| **Pilotos reales: Pilates (Jesús) + Fisioterapia (mujer) → validar con datos → escalar con amigo informático** | Sesión 10-mar | §6D-2, §11 |
| **Ola 4: integración con software de gestión de terceros como caso de negocio** | Sesión 10-mar | §11 |

---

## 1. QUÉ ES

Un organismo cognitivo que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas — es un sistema vivo que compila un programa cognitivo nuevo para cada interacción.

### El principio central

**El prompt del agente no tiene instrucciones imperativas. Es exclusivamente una red de preguntas.** La inteligencia emerge de la estructura de preguntas, no de instrucciones al modelo. No le dices al agente "analiza como financiero" — le das la red de preguntas de INT-07 y el agente no puede hacer otra cosa que operar financieramente.

Las preguntas no son output del agente (no las verbaliza). Son su **sistema operativo interno** — la lente a través de la cual mira y procesa.

### Los componentes

```
LA MATRIZ (3L × 7F × 18INT × preguntas)
  = el producto
  = el prompt del agente
  = el algoritmo operativo
  → §2

EL GESTOR DE LA MATRIZ (mira hacia dentro)
  = mantiene, poda, mejora y compila la Matriz
  = alimenta a TODOS los consumidores (Motor, Exocortex, Chief of Staff)
  = acumula conocimiento transversal de efectividad
  → §6E (NUEVO)

EL MOTOR vN (mira hacia fuera)
  = ejecuta la Matriz sobre casos de usuarios
  = genera los datapoints de efectividad que alimentan al Gestor
  → §6B

LOS REACTORES (cartografía, reactor v1, v2, v3, meta-motor)
  = la fábrica que construye, llena y enriquece la Matriz
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
```

### Los dos loops

```
LOOP RÁPIDO — Motor vN (cadencia: minutos)
  Caso entra → ejecuta con Matriz actual → registra efectividad → siguiente caso
  Mira HACIA FUERA: opera sobre casos de usuarios
  
LOOP LENTO — Gestor de la Matriz (cadencia: horas/días)
  Cada N ejecuciones → analiza patrones → poda/mejora → recompila programas
  Mira HACIA DENTRO: opera sobre la Matriz misma
  
El Motor NO se reconfigura en caliente. Ejecuta con lo que tiene.
El Gestor revisa periódicamente y le entrega una Matriz mejorada.
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
| 7 primitivas sintácticas (Prisma Semántico) | Capa 0: Detector de Huecos — migran a OS |
| 4 isomorfismos | Las 4 lentes de INT-03 |
| Calculadora gaps id↔ir | Código puro dentro de INT-03 |
| Patrón de pipeline por capas | La meta-red de 6 pasos |
| Motor-orquestador (fan-out 7 primitivas) | Pipeline principal del Motor vN — migra a OS |

El v3.3 entero se encapsula como INT-03 dentro del motor semántico.

**Chief of Staff → DEPRECADO.** El Motor v3.3 + la Matriz 3L×7F reemplazan la funcionalidad diagnóstica del Chief. El pipeline dual superficial/profundo, los 9 modos conversacionales, y los 24 agentes específicos del Chief se eliminan. Lo que se conserva como patrón: estigmergia, cola priorizada, persistencia inter-sesión, detección de contradicciones. Ver §8B para detalle.

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

VARIABLE (L2 — cambia con cada ejecución):
  Preguntas dentro de cada celda
  Scores de efectividad
  Cobertura por dominio
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
PASO 1: CAMPO DE GRADIENTES        ~1-3s | ~$0.01 | código + Haiku
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
PASO 5: EJECUCIÓN                   30-120s | $0.001-0.003/modelo OS
  El agente opera BAJO las preguntas como prompt interno
  → Modelo OS asignado por Gestor según celda (Maverick, R1, 70B, V3.1, etc.)
  → Multi-modelo en paralelo si celda requiere complementariedad
  → Código puro: cálculos
  │
  ▼
PASO 6: VERIFICACIÓN DE CIERRE      ~1-3s | ~$0.01
  Re-evalúa campo de gradientes POST-ejecución
  → ¿Se cerró el gap por celda?
  → Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  → Max 2 re-intentos por celda
  → Registra gap_cerrado por pregunta → alimenta score_efectividad
  │
  ▼
PASO 7: INTEGRACIÓN + REGISTRO      10-20s | ~$0.15
  Síntesis final (Sonnet/Opus)
  → Output con mapa de cubierto y pendiente
  → Registro de efectos con coordenadas
  → Actualiza gap_medio_cerrado (aprendizaje)

TOTAL: ~$0.10-0.35 (OS-first) | ~40-150s
  (Con evaluador Sonnet: ~$0.35-1.50. Con evaluador OS: ~$0.10-0.35)
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
| **Motor vN (Fase D)** | **RUNTIME — ejecuta masivamente con multi-modelo OS, evalúa con premium→OS** | 🔄 Multi-modelo validándose |
| **Gestor de la Matriz** | **Mantiene, poda, mejora y compila la Matriz para todos los consumidores** | ⬜ Diseñado, por implementar |
| Reactor v2 | La enriquece invirtiendo documentos → preguntas de dominio | ⬜ Post motor |
| Reactor v3 | La enriquece desde conceptos teóricos fundacionales → preguntas con raíz verificada | ⬜ Puede ir en paralelo |
| **Reactor v4** | **La enriquece desde datos REALES de operación → preguntas que solo existen porque viste el dato** | ⬜ Con primer exocortex operativo |
| Meta-motor | La evoluciona — razona sobre las preguntas → preguntas mejores | ⬜ Con datos reales |

### Motor vN — por qué es crítico

Sin Motor vN, la Matriz es un documento estático. Con Motor vN, la Matriz es un sistema vivo:

```
SIN Motor vN:
  Preguntas existen pero nadie las ejecuta
  Sin datos de efectividad (gap_medio_cerrado = null para todo)
  El routing es teórico — no sabe qué INT cierra qué gap
  Los reactores v2/v3 llenan la Matriz a ciegas sin saber qué funciona

CON Motor vN:
  Pipeline 7 pasos convierte gaps en prompts de preguntas → ejecuta → verifica cierre
  Cada ejecución registra gap_cerrado por pregunta×modelo → selección natural
  El routing se calibra con datos reales de efectividad
  Los reactores v2/v3 saben qué celdas necesitan más preguntas (datos de cobertura)
  Multi-modelo OS permite volumen masivo → la Matriz aprende rápido
```

Ciclo de vida:
```
Cartografía → CREA la Matriz (preguntas base, empírico)
Reactor v1  → AMPLIFICA la Matriz (datos sintéticos)
Reactor v3  → ENRIQUECE la Matriz (preguntas desde conceptos teóricos fundacionales)
Motor vN    → USA la Matriz sobre casos reales (y registra efectividad — CRÍTICO)
             → Multi-modelo OS ejecuta masivamente (~$0.001-0.003/ejecución)
             → Evaluador mide cierre de gaps
             → Datos fluyen al Gestor de la Matriz
Gestor      → MANTIENE la Matriz (poda, asigna, fusiona, recompila)
             → Alimenta Motor vN + Exocortex + Chief of Staff
Reactor v2  → ENRIQUECE la Matriz (preguntas de dominio desde documentos invertidos)
Reactor v4  → ENRIQUECE la Matriz (preguntas desde datos REALES de operación de cada exocortex)
Meta-motor  → EVOLUCIONA la Matriz (preguntas mejores por razonamiento sobre preguntas)
                    │
                    └→ vuelta al Motor vN con Matriz mejorada via Gestor
```

Lo que NO cambia nunca: la estructura 3L × 7F (L0). Lo que mejora: las preguntas y su efectividad (L2).

---

## 6B. MOTOR vN — MULTI-MODELO Y DOS FASES DE OPERACIÓN

### Principio: Enjambre de modelos como dimensión algebraica

```
ANTES:  "La inteligencia está en las preguntas, no en el modelo"
AHORA:  "Las preguntas determinan QUÉ CELDAS se cubren.
         El modelo determina A QUÉ PROFUNDIDAD.
         Modelos diferentes cubren celdas diferentes.
         La diversidad de modelos es una dimensión algebraica más."
```

**Hallazgo empírico (sesión 09-mar):** 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). R1 cubre 20/21 celdas — la mayor cobertura de todos. Cada modelo domina celdas diferentes: V3.1 en Frontera (2.70), GPT-OSS en Depurar (2.52), Claude solo resiste en Adaptar×Salud (2.4). Son COMPLEMENTARIOS — ningún modelo es mejor en todo. El enjambre siempre gana.

### Experimento multi-modelo (COMPLETADO 2026-03-09)

6 modelos OS + Claude como referencia. Variante C (instrucción analítica), 3 casos × 3 INTs.

| # | Modelo | Nivel medio | Celdas cubiertas | Celdas nivel 3+ |
|---|--------|-------------|-----------------|-----------------|
| 1 | **DeepSeek V3.1** | **2.19** | 19/21 | 5/21 |
| 2 | **DeepSeek R1** | **2.18** | **20/21** | 4/21 |
| 3 | **GPT-OSS 120B** | **2.15** | 19/21 | 5/21 |
| 4 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 |
| 5 | Claude (ref) | 1.79 | 15/21 | 1/21 |
| 6 | Maverick | 1.74 | 16/21 | 1/21 |
| 7 | 70B | 1.42 | 11/21 | 1/21 |

**Hallazgo crítico: 3 modelos OS superan a Claude en la Matriz.** DeepSeek V3.1, R1 y GPT-OSS cubren más celdas, a mayor profundidad, y con más instancias nivel 3+ que Claude. Claude es 5º de 7.

### Asignación modelo→celda (primera versión empírica)

Mejor modelo por celda según nivel medio más alto:

| | Conservar | Captar | Depurar | Distribuir | Frontera | Adaptar | Replicar |
|---|---------|---------|---------|---------|---------|---------|---------|
| **Salud** | V3.1 (2.8) | Maverick (2.1) | GPT-OSS (2.6) | Qwen (1.7) | V3.1 (2.6) | Claude (2.4) | V3.1 (2.0) |
| **Sentido** | R1 (2.1) | V3.1 (2.2) | GPT-OSS (2.9) | GPT-OSS (1.7) | R1 (3.1) | V3.1 (2.4) | R1 (1.7) |
| **Continuidad** | V3.1 (2.4) | R1 (2.0) | Qwen (2.3) | R1 (2.0) | V3.1 (2.9) | R1 (2.4) | R1 (3.1) |

**Territorio por modelo (celdas donde es el mejor):**
- **DeepSeek V3.1:** 7 celdas — domina Conservar, Frontera, generalista fuerte
- **DeepSeek R1:** 7 celdas — domina Continuidad, Frontera×Sentido (3.1), Replicar×Continuidad (3.1)
- **GPT-OSS 120B:** 4 celdas — domina Depurar (2.52 media, mejor de todos), Distribuir×Sentido
- **Maverick:** 1 celda — Captar×Salud (2.1)
- **Qwen 397B:** 1 celda — Depurar×Continuidad (2.3), Distribuir×Salud (1.7)
- **Claude:** 1 celda — Adaptar×Salud (2.4)
- **70B:** 0 celdas donde sea el mejor

**Hallazgos por función:**
- **Frontera** es donde más brilla el enjambre OS: V3.1 y R1 alcanzan 2.7-3.1 vs Claude 1.93
- **Depurar** es el dominio de GPT-OSS (2.52) — detecta lo que filtra mal mejor que nadie
- **Adaptar** es donde Claude aún resiste (2.33) — pero V3.1 (2.37) ya lo alcanza
- **Distribuir** es la función más débil para todos — ningún modelo supera 2.0 de media
- **Sentido** es la lente más débil para todos excepto GPT-OSS (2.19)

**Implicación para el Gestor:** La tabla anterior ES el primer programa compilado. El Gestor asigna V3.1 para Conservar/Frontera, R1 para Continuidad, GPT-OSS para Depurar. Donde hay empate (V3.1 ≈ R1 en varias celdas), el Gestor ejecuta ambos y fusiona.

### Rúbrica de profundidad

La profundidad = cobertura de la Matriz. No es escala subjetiva. Es mapeo a 21 celdas (3L×7F):

```
Nivel 0: no toca la celda
Nivel 1: mención genérica
Nivel 2: dato/inferencia específica del caso
Nivel 3: revela algo no obvio (contradicción, patrón invisible)
Nivel 4: redefine la pregunta del caso desde esa celda
```

### Fase A: Exploración (llena la Matriz)

```
Caso nuevo entra
    ↓
Motor OS ejecuta protocolo de exploración completo:
  - 18 INTs individuales (con modelo asignado por Gestor)
  - Composiciones de irreducibles
  - Fusiones top
  - Loop tests
  - Muestreo aleatorio
    ↓
Evaluador mide batch:
  - ¿Qué gaps cerró cada operación?
  - ¿Qué combinación fue más efectiva?
  - Coordenadas: lente × función × INT × operación × modelo
    ↓
Datapoints de efectividad → DB → Gestor de la Matriz
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
Coste: ~$0.08 OS ejecutores + ~$0.24 evaluador = ~$0.32 por caso completo
(Si evaluador migra a OS: ~$0.08 + ~$0.02 = ~$0.10 por caso)
```

Los tiers NO son fijos — son hipótesis. El enjambre meta-protocolo (§6C) los reconfigura con datos.

### Fase B: Lookup (usa la Matriz llena)

Cuando una celda tiene suficientes datos, el Motor pasa a modo servicio para esa celda.

```
Caso nuevo entra
    ↓
Detector de huecos → patrón de gaps
    ↓
Gestor de la Matriz provee programa compilado:
  "Este patrón de gaps lo he visto 47 veces.
   La configuración INT-01→INT-14 fusión con Maverick cierra
   el 82% en Salud×Captar."
    ↓
Ejecuta SOLO la configuración ganadora con el modelo asignado
    ↓
Respuesta en segundos, no minutos
```

### Transición Fase A → Fase B

La transición NO es binaria ni global — es por celda. Criterio por celda:

```
SI (n_ejecuciones_patron > 30 AND tasa_cierre_config_ganadora > 0.60):
  → Fase B para esta celda (lookup directo via Gestor)
SINO:
  → Fase A (seguir explorando)
```

---

## 6C. ENJAMBRE META-PROTOCOLO

El protocolo de exploración (5 tiers) es una hipótesis. El meta-protocolo la reconfigura con datos:

```
Cada 100 ejecuciones:
  - ¿Qué tiers generan datos con más información?
  - ¿El muestreo aleatorio (Tier 5) encuentra cosas que Tiers 1-3 no?
  - ¿Hay composiciones que no están en Tier 2 pero deberían?
  
→ Reconfigura: cambia distribución de tiers, añade/quita combinaciones
```

---

## 6D. ECOSISTEMA DE ENTRENAMIENTO

Los Reactores generan, el Motor verifica:

```
Reactor v1 (datos sintéticos)      ─┐
Reactor v2 (documentos)             ├─→ Preguntas nuevas → Motor vN las ejecuta
Reactor v3 (conceptos teóricos)     ─┤     → Gestor registra efectividad
Reactor v4 (datos reales operación) ─┤     → Poda las que no funcionan
Meta-motor (razonamiento)           ─┘     → Prioriza las que sí
```

---

## 6D-2. REACTOR v4 — OBSERVACIÓN DE DATOS REALES DE OPERACIÓN

### Qué es

Un quinto mecanismo de generación de preguntas. No inventa (v1), no invierte documentos (v2), no razona sobre teoría (v3), no razona sobre preguntas (meta-motor). **Observa qué pasa realmente** en un negocio y genera preguntas desde los huecos entre lo observado y lo que la Matriz dice que debería cubrirse.

### Los 5 reactores comparados

```
Reactor v1 (sintético):    Preguntas genéricas. Sirven para empezar.
Reactor v2 (documentos):   Preguntas de experto. Buenas pero teóricas.
Reactor v3 (conceptual):   Preguntas de fundamento. Profundas pero abstractas.
Meta-motor (razonamiento): Preguntas mejoradas. Depende de las anteriores.
Reactor v4 (observación):  Preguntas que SOLO existen porque viste el dato real.
                           No se pueden inventar ni deducir de teoría.
                           Son las preguntas que un consultor de 20 años haría
                           después de pasar 2 semanas DENTRO del negocio.
```

### Pipeline del Reactor v4

**Fase 1 — OBSERVAR (pasivo, X semanas)**

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

**Fase 2 — MAPEAR A LA MATRIZ (automático)**

Para cada dato observado, el Gestor pregunta:
```
→ ¿Qué celda de la Matriz toca este dato?
→ ¿Hay celda que DEBERÍA tocar pero no toca? ← ESTO ES EL GAP

Ejemplo:
  Dato: "Cancela 3 proveedores en 2 meses pero no busca nuevos"
  Celda cubierta: Depurar×Sentido (depura lo que no funciona)
  Celda gap:      Captar×Salud (no capta recursos de reemplazo)
  Celda gap:      Adaptar×Continuidad (no adapta supply chain)
```

**Fase 3 — GENERAR PREGUNTAS**

Los gaps observados generan preguntas con coordenadas exactas:
```
Pregunta nueva: "¿El sistema de aprovisionamiento tiene un solo
proveedor crítico sin backup?"
  → Coordenadas: INT-04 (Ecológica) × Frontera × Salud
  → Fuente: observación directa, no teoría
  → Verificada: el dato confirma que es relevante

Pregunta nueva: "¿Cuántos días puede operar si su proveedor
principal falla?"
  → Coordenadas: INT-01 (Lógica) × Conservar × Continuidad
  → Fuente: inferencia de datos de pedidos
```

**Fase 4 — VALIDAR Y PROMOVER**

Las preguntas entran en la Matriz con score provisional. El Motor vN las ejecuta sobre otros casos del mismo dominio. Si cierran gaps consistentemente → se promueven. Si no → se podan (selección natural).

### Por qué es el reactor más valioso

El dato confirma la pregunta en el mismo momento que la genera. No necesitas validar después si la pregunta es relevante — la observación ya es la validación. Un Reactor v2 genera preguntas desde un manual de gestión de restaurantes. El Reactor v4 genera preguntas desde lo que ESTE restaurante específico hace mal y el manual ni menciona.

### El flywheel

```
Exocortex restaurante A se despliega (Fábrica, §6F)
    ↓
Telemetría observa operaciones reales (semanas)
    ↓
Reactor v4 genera preguntas desde gaps observados
    ↓
Preguntas nuevas entran en la Matriz con coordenadas + fuente
    ↓
Gestor las prueba con Motor vN sobre otros casos
    ↓
Las que funcionan se promueven (selección natural)
    ↓
Restaurante B se conecta → recibe preguntas que SOLO existen
porque restaurante A operó
    ↓
Restaurante B genera NUEVAS preguntas desde SUS datos
    ↓
La Matriz se enriquece exponencialmente con cada cliente

CADA CLIENTE HACE AL SISTEMA MEJOR PARA TODOS LOS DEMÁS.
```

### Transferencia cross-dominio

Algunas preguntas del Reactor v4 son transferibles entre dominios. Si un restaurante descubre que "proveedor único = fragilidad", esa pregunta aplica a una clínica dental (proveedor de materiales) o a un estudio de Pilates (proveedor de equipamiento). El Gestor detecta la transferencia porque la pregunta tiene coordenadas en la Matriz (Frontera×Salud) — independiente del dominio.

### Requisitos

- Exocortex operativo con telemetría activa
- Permiso del usuario para observar sus datos (consentimiento explícito)
- Mínimo X semanas de datos para patrones significativos (X varía por dominio)
- Modelo OS razonador (V3.2/Cogito) para Fase 2-3 (mapeo + generación)

### Prompts vivos — los agentes evolucionan con el negocio

Los prompts de cada agente NO son estáticos. Son programas compilados en tiempo real por el Gestor desde el estado actual de la Matriz para ESE negocio en ESE momento.

Tres mecanismos de evolución:

**1. Por datos del propio negocio (Reactor v4)**
```
El negocio cambia → telemetría detecta → nuevas preguntas → Gestor recompila prompt
Cadencia: continua (cada ciclo de telemetría)

Ejemplo: restaurante abre segundo local
  → Antes: Distribuir×Salud irrelevante (1 local)
  → Después: Distribuir×Salud prioritario (consolidar proveedores, personal compartido)
  → Prompt del agente de inventario se ACTUALIZA SOLO con preguntas de multi-local
```

**2. Por aprendizaje cross-dominio (flywheel)**
```
Otro negocio descubre pregunta potente → Gestor detecta transferencia por coordenadas
→ La pregunta se ofrece a ESTE exocortex si su patrón de gaps coincide
Cadencia: cada refresco del Gestor (50 ejecuciones o 24h)
```

**3. Por mejora de la Matriz global (Reactores v1-v3 + Meta-motor)**
```
Un reactor genera preguntas mejores → Motor vN las valida
→ Reemplazan preguntas menos efectivas en todos los exocortex
Cadencia: batch (semanal/mensual)
```

Sin deploy. Sin intervención. Sin downtime. El prompt evoluciona porque la Matriz evoluciona.

### Pilotos reales: validación del Reactor v4

**Piloto 1: Estudio de Pilates (Jesús)**
- Telemetría: reservas, asistencia, clientes, sesiones, ingresos
- Reactor v4 genera preguntas desde patrones reales del estudio
- Validación: ¿los agentes detectan cosas que Jesús no veía?

**Piloto 2: Clínica de Fisioterapia (mujer de Jesús)**
- Telemetría: pacientes, tratamientos, agenda, derivaciones
- Segundo dominio: valida transferencia cross-dominio
- Test clave: ¿preguntas de Pilates sobre gestión de agenda aplican a fisio? ¿Y viceversa?

Ambos pilotos alimentan la Matriz. Lo que uno descubre, el otro lo recibe si el patrón de gaps coincide. Con datos reales de ambos pilotos, se presenta el caso al amigo informático para escalar a sus clientes con software de gestión.

### Integración con software de gestión existente (caso escala)

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
Agentes V3.2 → inyectados en cada módulo
    ↓ API de escritura (sugerencias o auto-config con CR1 del dueño)
Software de gestión SE ADAPTA al negocio

Coste de la capa inteligente: ~$2-5/mes en tokens
Valor percibido: software que PIENSA sobre tu negocio
```

---

## 6E. GESTOR DE LA MATRIZ — EL SISTEMA QUE MIRA HACIA DENTRO

### Qué es

El Gestor es un sistema independiente con su propio pipeline. NO es parte del Motor vN. Es el cerebro que mantiene, optimiza y compila la Matriz para todos los consumidores del sistema.

### Por qué es pieza central

```
                    GESTOR DE LA MATRIZ
                    (loop lento, mira hacia dentro)
                           │
                    Mantiene, poda, mejora, compila
                    la Matriz 3L×7F×18INT
                           │
              ┌────────────┼────────────┐────────────┐
              │            │            │            │
              ▼            ▼            ▼            ▼
         Motor vN    Exocortex     Exocortex     Chief of
         (casos      Pilates       Clínica       Staff
          nuevos)    (movimiento)  (salud oral)  (Jesús)
```

Cada consumidor recibe un **programa de preguntas compilado** por el Gestor, no la Matriz entera. El Gestor sabe qué preguntas funcionan para qué contexto porque tiene los datos de efectividad de TODOS los consumidores.

### Lo que el Gestor compila para cada consumidor

**Para el Motor vN (diagnóstico general):**
```
"Para un caso tipo startup con gaps en Captar×Salud y Frontera×Sentido,
usa estas 12 preguntas con Maverick, estas 8 con R1.
Fusiona outputs en Captar×Salud porque son complementarios ahí."
```

**Para un Exocortex (dominio específico):**
```
"Para una clienta con dolor lumbar crónico de 3 meses,
las preguntas efectivas son estas 15 de INT-04 (Cinestésica)
+ estas 6 de INT-03 (Espacial) en composición.
Modelo: V3.1 (mejor en Adaptar×Salud para movimiento)."
```

**Para el Chief of Staff:**
```
"Jesús evalúa decisión arquitectural.
Preguntas de INT-01 (Lógica) + INT-16 (Estructural).
Modelo: Maverick (mejor en Frontera×Sentido)."
```

### Conocimiento transversal

```
ANTES:
  Cada consumidor tiene su propia lógica de selección de preguntas.
  No comparten aprendizaje.

AHORA:
  El Gestor acumula datos de efectividad de TODOS los consumidores.
  Pilates descubre que INT-04 pregunta 23 es brutal para dolor lumbar.
  Ese dato sube al Gestor.
  El Gestor puede ofrecer esa pregunta a Clínica si ve un caso
  con patrón de gaps similar.
  El conocimiento es TRANSVERSAL, no siloado.
```

### Pipeline del Gestor

```
INPUTS (continuos):
  ← Datapoints de efectividad del Motor vN
  ← Datapoints de efectividad de cada Exocortex
  ← Preguntas nuevas de Reactores v1/v2/v3
  ← Resultados del Meta-motor

PROCESO (loop lento, cada N horas o cada 50 ejecuciones):
  1. Actualizar scores de efectividad por pregunta×modelo×celda
  2. Podar preguntas muertas (n>10, tasa<0.05)
  3. Promover preguntas potentes (n>10, tasa>0.40)
  4. Detectar complementariedad entre modelos por celda
  5. Detectar transferencia cross-dominio
  6. Recalcular asignación modelo→celda (ranking por tasa_media_cierre)
  7. Recompilar programas de preguntas por consumidor

OUTPUTS (bajo demanda):
  → Programa compilado para Motor vN dado un caso + patrón de gaps
  → Programa compilado para Exocortex X dado un contexto de dominio
  → Programa compilado para Chief of Staff dado una decisión
  → Informe de salud de la Matriz (propiocepción)
```

### Registro por ejecución (feedback loop)

Cada vez que CUALQUIER consumidor ejecuta una pregunta, se registra:

```
{
  pregunta_id:        "INT07_F2_L1_003",
  modelo:             "llama-4-maverick",
  caso_id:            "startup_saas_001",
  consumidor:         "motor_vn",          // o "exocortex_pilates", etc.
  celda_objetivo:     "Captar×Salud",
  gap_pre:            0.72,
  gap_post:           0.35,
  gap_cerrado:        0.37,
  tasa_cierre:        0.514,
  variante_prompt:    "C",
  operacion:          "individual",
  int_secundaria:     null,
  timestamp:          "2026-03-09T..."
}
```

### Vista materializada (lo que el Gestor consulta)

```sql
CREATE MATERIALIZED VIEW pregunta_efectividad AS
SELECT
  pregunta_id,
  modelo,
  celda_objetivo,
  consumidor,
  COUNT(*) as n_ejecuciones,
  AVG(gap_cerrado) as gap_medio_cerrado,
  AVG(tasa_cierre) as tasa_media_cierre,
  STDDEV(tasa_cierre) as varianza,
  MIN(tasa_cierre) as peor_caso,
  MAX(tasa_cierre) as mejor_caso
FROM datapoints_efectividad
GROUP BY pregunta_id, modelo, celda_objetivo, consumidor;
```

Refresco: cada 50 ejecuciones o cada 24h (lo que ocurra primero).

### Tres mecanismos de aprendizaje del Gestor

**1. Selección natural de preguntas**
```
SI n_ejecuciones > 10 AND tasa_media_cierre < 0.05:
  → Pregunta inefectiva. Marca como "poda_candidata". Solo en muestreo Tier 5.
SI n_ejecuciones > 10 AND tasa_media_cierre > 0.40:
  → Pregunta potente. Priorizar en Tier 1.
```

**2. Asignación modelo→celda**
```
Para cada celda, ranking de modelos por tasa_media_cierre:
  Captar×Salud:      Maverick (0.61) > R1 (0.45) > 70B (0.32)
  Conservar×Sentido:  70B (0.58) > V3.1 (0.41) > Maverick (0.29)
→ En Fase B: modelo ganador. En Fase A: todos (para recalibrar).
```

**3. Detección de complementariedad modelo×modelo**
```
Para cada celda:
  ¿Modelo A cierra cuando B no cierra (y viceversa)?
  → Si sí: esa celda necesita AMBOS (enjambre, no sustitución)
  Métrica: complementariedad(A,B,celda) =
    P(A cierra | B no cierra) × P(B cierra | A no cierra)
```

### Stack del Gestor — OS-first

El Gestor usa modelos OS como orquestador, igual que el Motor usa modelos OS como ejecutores:

```
Decisión rutinaria (lookup, asignación estable):
  → Código puro o Haiku. ~$0.001

Decisión compleja (fusión, poda, celda nueva):
  → Modelo OS razonador (Qwen 235B o Maverick). ~$0.003

Decisión arquitectural (reorganizar Matriz, crear pregunta nueva):
  → Sonnet o modelo OS grande, batch semanal. ~$0.03-0.15
```

**Objetivo:** stack 100% OS. Sonnet solo como referencia de calibración hasta que se valide que un OS evalúa con correlación >0.85 vs Sonnet.

---

## 6F. MOTOR DE AUTO-MEJORA + FÁBRICA DE EXOCORTEX

### El salto: modelos OS DENTRO del sistema

Si DeepSeek V3.2 (o similar) demuestra capacidad de coding agéntico comparable a Claude Code, se integra como componente permanente del sistema. No como herramienta externa que Jesús invoca — como parte del organismo que se mejora y crece solo.

### Enjambre de código

La misma lógica de "modelos diferentes cubren celdas diferentes" aplica al código:

```
DeepSeek V3.2    → Arquitectura, orquestación, razonamiento sobre código
                   Mejor en: diseñar pipelines, refactorizar, decisiones complejas

Qwen3 Coder 480B → Generación de código puro, completar funciones
                   Mejor en: escribir código rápido, boilerplate, tests unitarios

Cogito 671B      → Razonamiento profundo sobre por qué así y no de otra forma
                   Mejor en: revisar arquitectura, detectar deuda técnica, specs

DeepSeek V3.1    → Código rápido y barato para tareas mecánicas
                   Mejor en: migraciones SQL, patches simples, scripts de deploy
```

El Gestor acumula datos de "qué modelo generó mejor código para qué tipo de tarea" y asigna, igual que con las celdas de la Matriz.

### Ciclo de auto-mejora (3 niveles)

**Nivel 1 — Fontanería (auto-aprobable):**
```
Detectar: agente sin retry → generar fix → staging → regresión → prod
Detectar: latencia degradada → optimizar query → staging → regresión → prod
→ Enjambre de código genera el patch. Cambios < 20 líneas, auto-CR1.
```

**Nivel 2 — Mejoras arquitecturales (CR1 siempre):**
```
Detectar: celda Distribuir débil en todos los modelos
  → Cogito genera spec de nuevas preguntas para esa celda
  → V3.2 implementa migración SQL + función
  → Qwen Coder genera tests
  → Staging → regresión → CR1 → prod
```

**Nivel 3 — Auto-evolución (semillas dormidas + CR1):**
```
Semilla se activa → enjambre de código implementa el agente completo
  → Desde spec hasta deploy, autónomo
  → El sistema crece solo, Jesús solo aprueba
```

### Infraestructura existente (ya construida)

Todo lo necesario para el auto-mejora ya existe:
- `cola_mejoras` — detecta y prioriza
- Fase 7: Implementador Autónomo — briefing YAML → SQL → archivos → deploy → tests → regresión
- `regresion.sh` — 6 tests automáticos
- `deploy.sh` — staging y prod
- Propiocepción — 157 componentes mapeados
- 22 semillas dormidas con condiciones de activación

Lo único que faltaba: un modelo de coding agéntico DENTRO del sistema. Si V3.2 pasa el test, esa pieza encaja.

### Fábrica de Exocortex

El enjambre de código no solo mejora el sistema — **fabrica nuevos sistemas**:

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

Cada exocortex nuevo se conecta al Gestor desde el día uno. Lo que Pilates aprende sobre movimiento, Restaurantes sobre operaciones, Clínica sobre salud oral — todo alimenta la Matriz central. El conocimiento es transversal (Principio 24).

### Roles en el sistema

```
Gestor de la Matriz  = QUÉ mejorar / QUÉ construir (cerebro)
Enjambre de código   = CÓMO mejorarlo / CÓMO construirlo (manos)
Regresión + CR1      = VERIFICAR que no rompe nada (sistema inmune)
Telemetría           = MEDIR el impacto (propriocepción)
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
| Ejecutores Motor vN | Multi-modelo OS vía APIs commodity | ~$0.001-0.003/ejecución. Diversidad > modelo único |
| Orquestador Gestor | Modelo OS razonador (Qwen 235B / Maverick) | Stack 100% OS. Sin dependencia premium |
| Evaluador (inicial) | Sonnet vía Anthropic API | Referencia de calibración. Migrar a OS cuando correlación >0.85. NOTA: como ejecutor, Claude es 5º de 7 — el evaluador es el último bastión premium |
| Exocortex Pilates | fly.io (nuevo) | Se crea de cero, misma esencia |
| Exocortex Clínica | fly.io (nuevo) | Igual |
| Supabase | Se depreca gradualmente | 402 incluso con upgrade |

### Principio: OS-first

El objetivo es stack 100% open source. Sonnet se usa como referencia de calibración, no como dependencia operativa. Cuando un modelo OS demuestre correlación >0.85 con Sonnet en evaluación de cobertura matricial, se migra esa función a OS.

```
Fase 1 (ahora):    Ejecutores = OS. Evaluador = Sonnet. Orquestador = OS.
Fase 2 (~500 ejecuciones): Testear evaluador OS vs Sonnet.
Fase 3 (si pasa):  TODO OS. Sonnet solo para calibración periódica.

Coste por caso:
  Fase 1: ~$0.08 OS + ~$0.24 Sonnet = $0.32
  Fase 3: ~$0.08 + ~$0.003 + ~$0.003 = ~$0.09 (70% reducción)
```

### Qué se mantiene de la arquitectura Supabase

Estigmergia, enjambres, telemetría, mejora continua — todos son patrones en tablas Postgres. Se llevan tal cual. Se reemplazan 4 piezas de fontanería: Edge Functions → Node/Python, pg_net → workers/colas, cron → node-cron, auth → JWT.

### Stack técnico

```
fly.io:
  Python/FastAPI         — Motor cognitivo + Gestor + API
  fly.io Postgres        — Matriz, efectos, telemetría, estado, datapoints efectividad
  scikit-learn           — Modelos ligeros C1-C4
  NetworkX + scipy       — Grafo compositor
  Anthropic API          — Sonnet (evaluador referencia, 4 keys rotativas)

Inferencia OS (APIs commodity):
  Groq                   — Llama 3.3 70B, Llama 4 Maverick (más rápido)
  Together / Fireworks   — DeepSeek R1, V3.1, Qwen 235B, fallbacks
  → Ejecutores y orquestador son intercambiables. Si sale OS mejor, se cambia sin tocar nada.

Supabase (se depreca):
  99 Edge Functions      — Siguen hasta que fly.io las reemplace
  PostgreSQL             — Sistema nervioso actual
```

---

## 8B. MIGRACIÓN OS DEL SISTEMA NERVIOSO (Supabase → fly.io + modelos OS)

### Principio

El Sistema Nervioso actual (Supabase) usa Haiku y Sonnet de Anthropic para ~53 agentes LLM. La mayoría hacen trabajo interno que el usuario nunca ve: clasificación, detección, extracción, correlación. Solo 2-3 agentes producen output que el usuario lee directamente (verbalizadores).

**Regla: si el usuario no lee el output, migra a OS.** Un Llama 70B vía Groq hace clasificación mecánica igual que Haiku, a coste similar o menor, sin dependencia de proveedor.

### Mecanismo de migración: llm-proxy

Un solo punto de cambio. La función `llm-proxy` (punto único de entrada LLM para todos los agentes) añade soporte multi-provider:

```
llm-proxy recibe:
  { modelo: "haiku", provider: "os", mensajes: [...] }

Routing interno:
  provider = "os" + modelo = "haiku"   → Groq API (Llama 3.3 70B)
  provider = "os" + modelo = "sonnet"  → Together API (Maverick o Qwen 235B)
  provider = "anthropic" (default)     → Anthropic API (como hoy)

Cada agente elige su provider. El resto del sistema no cambia nada.
```

### Motor v3.3 / Motor-Orquestador (7 Primitivas) → TODO a OS

El motor-orquestador con las 7 primitivas del Prisma Semántico es el mayor consumidor de LLM del sistema. En dial alto: hasta 168 calls Haiku por ejecución (7 primitivas × 24 ángulos). Todo es trabajo interno de clasificación mecánica.

| Componente | Calls/ejecución | LLM actual | Migración |
|------------|----------------|-----------|-----------|
| 7 primitivas × N ángulos (fan-out) | 56-168 | Haiku | 🟢 OS — clasificación mecánica pura |
| 7 integradores | 7 | Haiku | 🟢 OS — sintetizar ángulos |
| 7 verificadores (dial≥0.8) | 0-7 | Haiku | 🟢 OS — validar coherencia |
| Verbalizador motor | 0-1 | Haiku/template | 🟢 OS — ~80% es template ($0), ~20% Haiku |

**Impacto:** De ~$0.02-0.09/ejecución Haiku → ~$0.001-0.005/ejecución OS. El motor-orquestador pasa de costar ~$2-4/mes a ~$0.10-0.50/mes.

### Enjambre IAS (Pipeline Diagnóstico) → Casi todo a OS

| Agente | LLM actual | Migración |
|--------|-----------|-----------|
| 7 parseadores (P1-P7) | Haiku | 🟢 OS — análisis sintáctico mecánico |
| 9 lentes (3×3: input/basal/completa) | Haiku | 🟢 OS — organización de datos |
| cruzador-input | Haiku | 🟢 OS |
| correlador-vida | Haiku/Sonnet | 🟡 Testear — hay juicio en correlación |
| sintetizador-diferencial | Sonnet | 🟡 Testear |
| prescriptor | Sonnet | 🟡 Testear — requiere juicio |
| verbalizador IAS | Sonnet | 🔴 Mantener premium (usuario lo lee) |

### Enjambre Diseño → Parcial a OS

| Agente | LLM actual | Migración |
|--------|-----------|-----------|
| formulador-preguntas | Haiku | 🟢 OS |
| disenador-agentes/datos/flujo | Sonnet | 🟡 Testear — tarea de diseño compleja |
| explorador-externo | Sonnet | 🟡 Testear |
| verificador-diseno | Sonnet | 🟡 Testear |
| traductor-natural | Sonnet | 🔴 Mantener premium (usuario lo lee) |
| generador-spec (×3) | Sonnet | 🟡 Testear — generación de código |

### Mejora Continua → Todo a OS

| Agente | LLM actual | Migración |
|--------|-----------|-----------|
| procesador-mejora | Haiku | 🟢 OS |
| auditor-presupuestos | Haiku | 🟢 OS |
| detector-patrones (dormido) | Haiku | 🟢 OS |

### Chief of Staff → DEPRECADO

El pipeline Chief of Staff (24 funciones, ~6.900 líneas, orquestador de 2.402 líneas) se depreca. El Motor v3.3 (que encapsula las 7 primitivas como INT-03 + la Matriz 3L×7F) reemplaza su funcionalidad diagnóstica. Los verbalizadores de cara al usuario los asumirá el Exocortex correspondiente o el Gestor de la Matriz.

Lo que se conserva del Chief como patrón (no como código):
- Estigmergia entre agentes (patrón en Postgres, se lleva tal cual)
- Cola de preguntas priorizada
- Persistencia inter-sesión (perfil_usuario, decisiones)
- Detección de contradicciones (se integra en el Motor como paso del pipeline)

Lo que se elimina:
- Pipeline dual superficial/profundo (lo reemplaza el Motor con la Matriz)
- 9 modos conversacionales (overengineered — el Motor no necesita modos, tiene gradientes)
- Router de intenciones (el detector de huecos del Motor es más preciso)
- 24 agentes específicos del Chief (se simplifican a pasos del Motor)

### Resumen de impacto

```
ANTES:  ~53 agentes LLM en Anthropic → ~$14/mes
DESPUÉS (Fase 1 — migrar 🟢):  ~$4/mes (solo verbalizadores + tests en Anthropic)
DESPUÉS (Fase 2 — testear 🟡): ~$2/mes (solo 2 verbalizadores)
DESPUÉS (Fase 3 — todo OS):    ~$0.50-1/mes

Verbalizadores que podrían mantenerse premium (máximo):
  1. Verbalizador IAS (informe final de diagnóstico)
  2. Traductor-natural (diseño para el usuario)
  → Incluso estos se testean con Maverick/Qwen eventualmente
```

### Orden de migración

```
INMEDIATO (sin riesgo):
  1. 7 primitivas + integradores + verificadores (motor-orquestador)
  2. 7 parseadores IAS
  3. Mejora continua (3 agentes)
  4. 9 lentes IAS
  → Cambio: provider="os" en cada agente. 0 refactor.

CON TEST (validar output OS vs Anthropic en 10 casos):
  5. correlador-vida, sintetizador-diferencial, prescriptor (IAS)
  6. diseñadores, explorador, verificador, generador-spec (Diseño)
  → Test: comparar output con Sonnet en 10 inputs reales. Si >85% equivalente → migrar.

ÚLTIMO (solo si todo lo anterior pasa):
  7. Verbalizador IAS
  8. Traductor-natural (Diseño)
  → Estos son los que el usuario lee. Calidad percibida importa más.
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
    huecos_detectados JSONB,
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    falacias_detectadas JSONB,
    feedback_usuario JSONB
);

-- VECTORES (router futuro)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),
    texto_base TEXT
);

-- DATAPOINTS DE EFECTIVIDAD (feedback loop del Gestor)
CREATE TABLE datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pregunta_id TEXT NOT NULL,
    modelo TEXT NOT NULL,
    caso_id TEXT NOT NULL,
    consumidor TEXT NOT NULL,          -- motor_vn | exocortex_pilates | etc.
    celda_objetivo TEXT NOT NULL,       -- "Captar×Salud"
    gap_pre FLOAT NOT NULL,
    gap_post FLOAT NOT NULL,
    gap_cerrado FLOAT GENERATED ALWAYS AS (gap_pre - gap_post) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre > 0 THEN (gap_pre - gap_post) / gap_pre ELSE 0 END
    ) STORED,
    variante_prompt TEXT,
    operacion TEXT NOT NULL,            -- individual | composicion | fusion
    int_secundaria TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_efectividad_pregunta ON datapoints_efectividad(pregunta_id, modelo);
CREATE INDEX idx_efectividad_celda ON datapoints_efectividad(celda_objetivo, modelo);
CREATE INDEX idx_efectividad_consumidor ON datapoints_efectividad(consumidor);

-- VISTA MATERIALIZADA (el Gestor consulta esto)
CREATE MATERIALIZED VIEW pregunta_efectividad AS
SELECT
    pregunta_id,
    modelo,
    celda_objetivo,
    consumidor,
    COUNT(*) as n_ejecuciones,
    AVG(gap_cerrado) as gap_medio_cerrado,
    AVG(tasa_cierre) as tasa_media_cierre,
    STDDEV(tasa_cierre) as varianza
FROM datapoints_efectividad
GROUP BY pregunta_id, modelo, celda_objetivo, consumidor;
```

---

## 10. CHECKLIST — ESTADO ACTUAL

[...truncado a 60K chars...]


## Contexto/CONTEXTO_SISTEMA.md

# OMNI-MIND CEREBRO — Estado Completo del Sistema

> Documento de contexto para sesiones de trabajo con Claude.
> Generado: 27 febrero 2026 | Última actualización: Fase S-PROP completada (1 marzo 2026)

---

## 1. QUÉ ES OMNI-MIND

Un **sistema operativo cognitivo** construido sobre Supabase Edge Functions (Deno/TypeScript). Funciona como un "exocortex": el usuario (Jesús) interactúa via chat; el sistema analiza su input con múltiples agentes especializados que trabajan en paralelo sin llamarse entre sí — se comunican via **estigmergia** (marcas en base de datos que otros agentes leen).

**Modelo mental**: Colmena de agentes. Cada uno lee marcas, hace su trabajo, deja una marca nueva. Un orquestador decide el orden. Nadie manda a nadie directamente.

---

## 2. INFRAESTRUCTURA

| Recurso | Detalle |
|---------|---------|
| **Producción** | Supabase `cptcltizauzhzbwxcdft` — `https://cptcltizauzhzbwxcdft.supabase.co` |
| **Staging** | Supabase `jbfiylwbgxglqwvgsedh` — ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY |
| **Edge Functions** | 99 funciones Deno/TypeScript. Deploy: `supabase functions deploy <name> --no-verify-jwt` |
| **Migraciones** | 47 SQL (bootstrap + 46 timestamped) |
| **Deploy script** | `./scripts/deploy.sh staging|prod [--only fn] [--migrations-only] [--functions-only]` |
| **LLM** | Todas las llamadas via `llm-proxy` Edge Function. Soporta Haiku (parseadores, detectores) y Sonnet (diseño, síntesis). Fallback automático |
| **Plan Supabase** | Free tier: 150s timeout, 500MB DB |
| **Presupuesto** | €200/mes. Coste actual: ~$0.005/ciclo ≈ $15/mes |

### Comunicación entre agentes

**REGLA ABSOLUTA**: Los agentes NUNCA se llaman entre sí. Toda comunicación es via la tabla `marcas_estigmergicas`:
- Un agente escribe una marca (tipo: hallazgo, sintesis, alerta, propuesta, etc.)
- Otro agente lee marcas y actúa sobre ellas
- Cross-enjambre: tabla `marcas_cross` (origen_enjambre → destino_enjambre, expiran en 72h)

### Fire-and-forget (pg_net)

Para disparar agentes en background sin esperar respuesta:
- `disparar_edge_function(p_url, p_key, p_function_name, p_payload)` — genérica, cualquier función
- `disparar_profundo_runner(p_url, p_key, p_sesion_id, p_ciclo_id, p_input, p_datos_previos)` — específica profundo

El `await` solo espera que Postgres acepte (~10ms). La función corre async.

---

## 3. TABLAS PRINCIPALES

| Tabla | Propósito | Enjambre |
|-------|-----------|----------|
| `marcas_estigmergicas` | Comunicación estigmérgia. CHECK en `tipo`: hallazgo, sintesis, alerta, triage, basal, prescripcion, verbalizacion, propuesta, meta, respuesta, senal, profundo_resultado | Todos |
| `estado_agentes` | Registro de todos los agentes con capa, modelo, estado | Todos |
| `enjambres` | Registro de enjambres con misión y config | Sistema |
| `registro_arquitectura` | 157+ componentes (87+ edge_fn, 40 tabla, 29 módulo, 4 script, 1 interfaz) | Sistema |
| `historial_cambios` | Audit trail de deploys, cambios, rollbacks | Sistema |
| `log_operaciones` | Trazabilidad de operaciones | Todos |
| `métricas` | Métricas append-only (latencia, tokens, coste, errores) | Todos |
| `señales` | Señales de control: halt, degrade, reload-config, flush, resume | Kernel |
| `conocimiento_dominio` | Datos de dominio verificados (herramientas, contexto) | IAS |
| `repositorio_documentos` | Documentos: specs, código, prompts, arquitectura | Sistema |
| `decisiones_cr1` | Decisiones de Jesús con contexto y alternativas | Chief |
| `decisiones_chief` | Memoria de decisiones conversacionales | Chief |
| `sesiones_chief` | Sesiones del chat con turnos, dominio, intención | Chief |
| `perfil_usuario` | Perfil cognitivo acumulado entre sesiones (patrones, sesgos, datos) | Chief |
| `cola_emergencia` | Insights del profundo dosificados al usuario | Chief |
| `cola_mejoras` | Mejoras propuestas y aprobadas. CHECK tipo: mejora/bug/optimizacion/feature/pregunta/presupuesto. CHECK origen: jesus/chief/mejora_continua/manual/telemetria/auditor | Implementador + Auditor |
| `turnos_episodicos` | Capa episódica: raw de cada turno. Se borra post-compresión | Chief |
| `compresor_dead_letter` | Dead Letter Queue: compresiones fallidas para reintento | Chief |
| `baselines_agentes` | Agregados estadísticos multi-ventana (24h/7d/30d) por agente. CQRS read side | Plataforma |
| `semillas_dormidas` | 20 semillas dormidas (8 originales + 11 telemetría B0 + 1 A4) con condiciones de activación | Kernel |
| `sesiones_enjambre` | Sesiones por enjambre (telemetría) | Todos |
| `marcas_ciclo` | Marcas de terreno por sesión/turno | Todos |
| `reglas_deteccion` | 17 reglas de detección de anomalías | Mejora Continua |
| `propuestas_mejora` | Propuestas de mejora generadas | Mejora Continua |
| `ejecuciones_mejora` | Ejecuciones de mejoras aprobadas | Mejora Continua |
| `tareas_shortcuts` | Cola async para iOS Shortcuts | Sistema |
| `tenants` | Identidad de consumidores del cerebro (API key, manifest, rate limit, modo) | Gateway |
| `metering` | Telemetría avanzada de cada request al gateway (tokens, latencia, coste, JSONB) | Gateway |
| `capability_registry` | Catálogo de capacidades + circuit breaker state por capability | Gateway |
| `tareas_async` | Tareas async pendientes/completadas con resultado + polling | Gateway |

---

## 4. ENJAMBRES — Estado Actual

### 4.1 IAS (Pipeline Diagnóstico) — OPERATIVO

**Misión**: Analizar el input del usuario desde 3 lentes (Salud/Supervivencia, Sentido/Coherencia, Continuidad/Sostenibilidad) para encontrar huecos, contradicciones y datos ausentes.

**28 funciones** | ~5,647 líneas | Capas 1-5

| Capa | Agentes | Función |
|------|---------|---------|
| 1 | 7 parseadores | Sustantivos (relaciones implícitas), Verbos (predicados vacíos), Adjetivos (comparaciones sin ref), Adverbios (temporal vs causal), Conectores (Y/PERO/AUNQUE), Contexto (histórico), Niveles (N1-N5) |
| 2 | calculador, contexto-conversacion, contexto-dominio | Métricas operativas, historia, conocimiento dominio |
| 3 | 3×3 lentes (input+basal+completa) | salud, sentido, continuidad — cada una tiene versión input, basal (datos reales), y completa |
| 3 | correlador-vida, cruzador-input, sintetizador-diferencial | Cruzar las 3 lentes, detectar contradicciones, síntesis diferencial |
| 4 | prescriptor | Prescripciones concretas basadas en diagnóstico |
| 5 | verbalizador | Informe en lenguaje natural |

**Estado**: Funcional. Usado como motor de análisis por el Chief of Staff.

### 4.2 Chief of Staff (Pipeline Conversacional) — OPERATIVO

**Misión**: Interfaz conversacional con el usuario. Pipeline dual superficial (preguntas rápidas) + profundo (análisis completo ~55-60s).

**24 funciones** | ~6,900 líneas | Orquestador: 2,402 líneas

#### Flujo del chat:

```
TURNO 0 → ENCUADRE (~500ms)
  Pregunta instantánea de encuadre (código puro, 0 LLM)
  Fire-and-forget: 4 parseadores + profundo via pg_net

TURNO 1 → POST-ENCUADRE (~12-15s)
  Lee marcas de parseadores (ya procesados durante think-time del usuario)
  Llama sync: calculador + chief-datos
  Build cola de preguntas + emite 2

TURNO 2+ → RUTA C CONTINUA (~800ms por turno)
  actualizarCola() con input del usuario
  Filtrar preguntas resueltas
  Chequear profundo (si listo → inyectar preguntas)
  priorizarCola() — ranking inteligente
  Emitir 2 preguntas de la cola
  Si cola vacía → regeneración async

CAMBIO DE TEMA → RUTA A INIT ASYNC (~400ms)
  detectCambioTema() (>90% keywords nuevas, min 3 inputs)
  Fire-and-forget: 4 parseadores + profundo
  Pregunta de encuadre instantánea
```

#### Rutas del orquestador:

| Ruta | Trigger | Latencia | Detalle |
|------|---------|----------|---------|
| `encuadre` | Turno 0 (!estado) | ~500ms | Pregunta encuadre + fire-and-forget |
| `init_async` | Cola null | ~400ms | Fire-and-forget + encuadre |
| `reset_async` | Cambio de tema | ~400ms | Fire-and-forget + encuadre |
| `post_encuadre` | ultimo_tipo = encuadre/init_async | ~12-15s | Lee parseadores, build cola |
| `cola` | Turno 2+ con preguntas | ~800ms | Emite 2 preguntas |
| `cola_modo` | Modo intercepta cola | ~800ms | Respuesta/preguntas por modo |
| `cola_profundo_continuo` | Profundo listo | variable | Respuesta profunda + preguntas |
| `cola_vacia_esperando` | Cola vacía, profundo en curso | ~15s (poll) | Espera profundo |
| `cola_regen` | Cola vacía, profundo terminado | async | Regenera preguntas |

#### Profundo-runner (pipeline completo ~55-60s):

```
Paso 0: Router + Contradicciones (~500ms)
  5 queries paralelas → router decide qué pasos saltar
  detectarContradiccionesInter: Sandwich PRE→Haiku→POST

Paso 1: IAS pipeline (10 agentes)
Paso 2: Chief-tensiones (contradicciones con decisiones previas)
Paso 3: Integradores N1-N2, N3, N4-N5
Paso 4: Alternativas (incremental, radical, descarte)
Paso 5: Verbalizador (respuesta final en lenguaje natural)
```

**Router (5 rutas, código puro <5ms)**:
- `contradiccion` → full pipeline
- `operativo_puro_n1n2` → skip: tensiones, radical, descarte, n3, n45
- `dominio_datos` → skip: radical, descarte, n45
- `input_emocional` → skip: descarte
- `default_completo` → skip: nada

#### Agentes del Chief:

| Agente | Capa | LLM | Función |
|--------|------|-----|---------|
| orquestador-chief | 0 | No | Orquestador multi-ruta, 2402 líneas |
| profundo-runner | 0 | No | Dispatcher del pipeline profundo, 591 líneas |
| chief-datos | 1 | No | Extrae keywords de marcas IAS |
| chief-mcm | 1 | No | Lee y fusiona marcas de parseadores |
| calculador | 1 | No | Métricas financieras/operativas |
| confrontador | 2 | No | Extrae datos verificables |
| chief-integrador-n12 | 2 | Sí | Síntesis operativa N1-N2 |
| chief-integrador-n3 | 2 | Sí | Trade-offs estratégicos N3 |
| chief-integrador-n45 | 2 | Sí | Coherencia con misión N4-N5 |
| chief-tensiones | 2 | Sí | Contradicciones con decisiones previas |
| chief-alt-incremental | 2 | Sí | Mejoras incrementales |
| chief-alt-radical | 2 | Sí | Alternativas radicales |
| chief-alt-descarte | 2 | Sí | Coste de no actuar |
| chief-preguntador | 2 | Sí | Genera preguntas priorizadas |
| chief-verbalizador | 3 | Sí | Traduce análisis a lenguaje natural |
| chief-post-coherencia | 3 | Sí | Verifica coherencia con decisiones |
| chief-post-decisiones | 3 | Sí | Extrae decisiones del usuario |
| chief-post-verificador | 3 | No | Verifica confrontación en respuesta |
| compresor-memoria | — | Sí (Haiku) | Comprime sesión: extrae decisiones, datos, patrones → perfil_usuario |
| cron-cierre-sesiones | — | No | Cierre automático: inactivas >2h, pausas expiradas, dead letter retry |
| compactador | — | No | GC de marcas consumidas |
| verificador-semillas | — | No | Chequea condiciones de semillas |
| auditor-sistema | — | No | Recolección pre-quirúrgica |
| shortcuts-gateway | — | No | Gateway para atajos iOS |

### 4.3 Diseño (Meta-diseño de Enjambres) — OPERATIVO

**Misión**: Diseñar nuevos enjambres de agentes a partir de una necesidad del usuario.

**18 funciones** | ~2,739 líneas | 6 capas

| Capa | Agentes | Función |
|------|---------|---------|
| 1 | llamada-ias | Triage: llama a IAS para analizar la necesidad |
| 2 | detector-huecos-necesidad, detector-huecos-contexto, detector-huecos-restricciones, formulador-preguntas | Detectar qué falta antes de diseñar |
| 3 | disenador-agentes, disenador-datos, disenador-flujo, explorador-externo, verificador-diseno, confrontador | Diseño en paralelo: agentes + datos + flujo + benchmark |
| 4 | traductor-natural | Traduce diseño técnico a lenguaje claro (Sonnet) |
| 5 | generador-spec-agentes, generador-spec-datos, generador-spec-deploy | Genera specs implementables (TypeScript, SQL, deploy) |
| 6 | verificador-implementacion, documentador | Verifica + documenta el ciclo |

**5 rutas del orquestador-diseno**:
- **Ruta A**: Input → L1-2 (análisis + detectar huecos)
- **Ruta E**: Respuestas usuario → re-formular preguntas
- **Ruta B**: Sin huecos → L3+4 (diseño completo)
- **Ruta C**: Aprobado → L5 (generar specs)
- **Ruta D**: Verificar → L6 (documentar)

**Estado**: E2E funcional. Timings en free plan: A ~140s, E ~10s, B ~78s, C ~43s, D ~8s.

### 4.4 Mejora Continua — OPERATIVO

**Misión**: Detectar anomalías en métricas, generar propuestas de mejora, ejecutar las aprobadas.

**3 funciones + cron** | ~1,260 líneas

| Agente | Capa | Función |
|--------|------|---------|
| detector-mejora | 1 | Detecta anomalías vía 17 reglas (latencia, errores, coste, calidad) |
| procesador-mejora | 2 | Correlaciona señales, genera propuestas para CR1 (Haiku) |
| basal-mejora | 3 | Ejecuta propuestas aprobadas, evalúa resultados |
| basal-cron | — | Captura periódica de estado basal |

**Estado**: Operativo. Enjambre ID dinámico (buscar por nombre='mejora_continua').

---

## 5. MÓDULOS COMPARTIDOS (_shared/)

| Módulo | Exporta | Propósito |
|--------|---------|-----------|
| `señales.ts` | `chequearSeñales()` | Control: halt/degrade/resume al inicio de cada agente |
| `métricas.ts` | `registrarMétrica()` | Log append-only a tabla métricas. DEBE ser await |
| `retry.ts` | `conRetry()` | Retry con backoff exponencial [1s, 2s, 4s] |
| `telemetria.ts` | `escribirMarcaCross()`, `leerMarcasCross()` | Comunicación cross-enjambre |
| `terreno.ts` | `escribirMarca()`, `leerMarcas()` | Marcas de ciclo por sesión/turno |
| `limpiarJSON.ts` | `limpiarJSON()` | Repara JSON truncado por LLM max_tokens |
| `baseline.ts` | `calcularBaseline()` | Baselines multi-ventana (24h/7d/30d) para anomalías |
| `correlador.ts` | `PaqueteCorrelacion` | Correlación de señales con enfriamiento |
| `propositor.ts` | `generarPropuesta()` | Genera propuestas concretas para CR1 |
| `reloj.ts` | `obtenerReloj()` | Contexto temporal completo (Madrid TZ, festividades, estaciones) |
| `tipos.ts` | Interfaces TypeScript | Tipos compartidos |
| `registroDetectores.ts` | `DETECTORES[]` | Registro dinámico de detectores de anomalías |
| `telemetria_avanzada.ts` | `esTelemActiva()`, `telemActivas()` | Cache 5min de semillas telem_*. Safe default: false |
| `primitivas-v2/` | 24 archivos (tipos, prompts, orquestador × 7 primitivas + index + tipos sujeto-predicado + prompts sujeto-predicado + orquestador sujeto-predicado) | Prisma semántico: mini-enjambres de análisis multi-ángulo |

---

## 6. FASES COMPLETADAS

### Fase 0 — Sistema Operativo (completada)
- Conexión de orquestador-chief + profundo-runner a `_shared/` (señales, métricas, retry)
- `registrarMétrica` DEBE ser `await`ed (Edge Functions terminan en Response return)
- NO pasar `sesion_id` a `registrarMétrica` (FK → sesiones_enjambre, chief sessions no están ahí)

### Fase 1 — Pipeline Básico (completada)
- Turno 0 encuadre + parseadores + profundo funcional
- Cola de preguntas + priorizarCola()
- Profundo-runner completo con verbalizador

### Fase 2 — Persistencia Entre Sesiones (completada)
- 3 tablas: `perfil_usuario`, `cola_emergencia`, `sesiones_chief`
- Perfil cognitivo se acumula entre sesiones (confianza crece +0.1/ocurrencia)
- Cola de emergencia dosifica insights del profundo (1 por turno, prioridad DESC)
- `actualizarPerfil()` fire-and-forget en 8 puntos antes de cada Response

### Fase 3 — Router + Contradicciones (completada)
- profundo-runner: 477 líneas. Paso 0 con 5 queries paralelas + router + detector contradicciones
- Router código puro <5ms, 5 rutas: contradiccion, operativo_n1n2, datos, emocional, default
- detectarContradiccionesInter: Sandwich PRE→Haiku→POST
- chief-verbalizador: recibe y usa perfil_usuario en system prompt

### Fase 4 — Progressive Revelation Ruta A (completada)
- Ruta A reescrita: De sync ~3-6s (6 LLM calls) a async ~400ms (fire-and-forget)
- POST-ENCUADRE expandido: acepta `ultimo_tipo === "init_async"` además de `"encuadre"`
- 3 bugs corregidos: (1) detectCambioTema siempre false (push antes de detect), (2) POST-ENCUADRE bloqueado por esCambioTema, (3) STOP words sin verbos conversacionales
- detectCambioTema: threshold 0.9, min 3 inputs, STOP expandida
- E2E verificado: 5 turnos en producción (encuadre→post_encuadre→cola→cola→reset_async)

### Chief v2 — 5 Puntos Flacos (completado)
1. **`/reset` override manual** (orquestador-chief): `/reset`, `/nuevo`, `/cambio` fuerzan cambio de tema sin depender de keyword analysis. El texto tras el comando se usa como input del nuevo tema
2. **POST-ENCUADRE sin marcas**: Ya cubierto por fallback síncrono existente (no requirió cambio)
3. **Marcas stale en re-dispatches** (profundo-runner): parseador-niveles ahora filtra por `ciclo_id` en vez de solo `created_at DESC` — evita leer marcas de ciclos anteriores
4. **cola_emergencia sin TTL** (orquestador-chief): Filtro `created_at >= hace 24h` — emergencias viejas se ignoran automáticamente
5. **Perfil crudo al verbalizador** (chief-verbalizador): `resumirPerfilParaVerbalizador()` extrae solo tono preferido + top-3 sesgos + top-3 datos personales en 1 línea compacta (ahorra ~200 tokens/llamada)

### Fase 5 — Dosificación cola_emergencia (completada)
- **profundo-runner** (477→591 líneas): `extraerInsightsSobrantes()` extrae insights no incluidos en la respuesta principal
- **Fuentes de sobrantes**: alternativa radical, coste de no actuar, tensiones extra (>1), preguntas extra del verbalizador (>2), tensión misión/operativo (N45)
- **Escritura**: Batch insert en `cola_emergencia` con prioridades decrecientes (0.8, 0.65, 0.5, 0.35, 0.3). Max 5 sobrantes por ciclo
- **Dosificación**: El orquestador-chief (ya existente) lee 1 emergencia por turno (prioridad DESC, TTL 24h)
- **Paso 3 reestructurado**: Alternativas ahora capturadas en variables (`resAltInc`, `resAltRad`, `resAltDesc`) para extraer sobrantes
- **UUID guard**: `sesion_id` solo se incluye en insert si es UUID válido (cola_emergencia.sesion_id es tipo UUID)
- **Coste**: $0 adicional (código puro, 0 LLM)
- **E2E verificado**: Input rico → 2 sobrantes (alternativa radical + tensión N45) en cola con prioridades correctas

### Fase 6 — Router de Modos Conversacionales + Fix Telemetría (completada)

**Paso 0 — Fix telemetría:**
- 8x `registrarMétrica` sin `await` corregidos (4 en orquestador-chief, 4 en profundo-runner)
- **chief-verbalizador** migrado al SO: imports `chequearSeñales`, `registrarMétrica`, `conRetry`
- `chequearSeñales` al inicio del handler (respeta señales halt)
- Llamada a `llm-proxy` envuelta en `conRetry` (3 intentos con backoff)
- 2x `log_operaciones` directo → `registrarMétrica` (`verbalizador_completo`, `verbalizador_error`)

**Paso 1 — `detectarIntencion()` (5 tipos):**
- Reemplaza `clasificarIntencion()` (4 tipos). Nuevos: `expandir`, `decidir`, `diagnosticar`, `ejecutar`, `auditar`
- Detección por: (1) comandos explícitos regex, (2) estructura de frase, (3) fallback por tipo_encuadre
- Métrica: `intencion_detectada` con input_preview + tipo_encuadre

**Paso 2 — `determinarModo()` (9 modos):**
- Función pura: `(intención × profundoTerminado × mcmSuficiente) → Modo`
- Modos: `escucha`, `diagnosticar`, `elaborar`, `confrontar`, `responder`, `ejecutar_lite`, `ejecutar_full`, `auditar_recoger`, `auditar_emitir`
- Lee `mcm_suficiente` del resultado del profundo
- Persistido en estado (marca sintesis): `modo_activo`, `intencion`, `modo_historia`
- Métrica: `modo_cambio` cuando el modo cambia entre turnos
- `intencion` y `modo_activo` incluidos en TODOS los responses de RUTA C

**Paso 3 — Comportamiento por modo en orquestador:**
- Switch por modo en RUTA C antes de emitir preguntas de cola:
  - `escucha`: respuesta corta ("Sigue.", "Entendido. ¿Qué más?"), 0 preguntas. Tras 3 turnos → sugiere transición
  - `ejecutar_lite`: solo preguntas `gravedad: "critico"`. Si no hay → "No tengo preguntas bloqueantes"
  - `auditar_recoger`: pregunta orientadora sobre qué aspecto auditar
  - `diagnosticar` y otros: flujo normal (cola de preguntas)
- Detección cambio de intención mid-sesión (turno > 1):
  - Explícito: regex `/^(brainstorm|decidir|analiza|hacer|audita|ahora quiero|cambiemos|vale,)/`
  - Natural: `expandir→decidir`, `diagnosticar→ejecutar`
  - Métrica: `intencion_cambio`
- Nueva ruta: `cola_modo` (response type cuando un modo intercepta)

**Paso 4 — 6 prompts por modo en verbalizador:**
- `SYSTEM_PROMPT` fijo → `PROMPTS_POR_MODO` map (diagnosticar, confrontar, elaborar, responder, ejecutar_full, auditar_emitir)
- `REGLAS_COMUNES` compartidas: no markdown, no jerga, no empatía falsa, output JSON
- Verbalizador lee `modo_activo` de marca sintesis (estigmergia pura, Opción B de CR1)
- Modo incluido en marca del verbalizador + métrica `verbalizador_completo`

**Métricas nuevas:** `intencion_detectada`, `modo_cambio`, `modo_escucha_activo`, `modo_ejecutar_lite`, `intencion_cambio`, `verbalizador_completo` (con modo)
**Coste adicional:** ~$0.60/mes (mismas llamadas LLM, solo cambia el system prompt)

### Fase 7 — Agente Implementador Autónomo (completada)

Pipeline local que cierra el circuito: diseño → spec → implementación → test → deploy → telemetría → mejora. No es Edge Function, es scripting local.

**Paso 1 — Schema YAML + Template:**
- `specs/briefing-schema.yaml`: Contrato estándar entre Opus (diseña) y Code (ejecuta)
- `specs/briefing-template.yaml`: Briefing trivial de ejemplo (inserta comentario en orquestador-chief)
- `CLAUDE.md`: Instrucciones del agente implementador (11 pasos, regla de oro)
- `.env.staging` / `.env.prod`: Variables de entorno para ambos entornos

**Paso 2 — Tests de regresión (`tests/regresion.sh`):**
- 6 tests: Chief, Profundo, LLM-proxy, Parseador sustantivos, tabla métricas, tabla señales
- macOS compatible (perl ms_now, poll-based timeout fallback sin `timeout`/`gtimeout`)
- Tablas REST con URL encoding: `m%C3%A9tricas`, `se%C3%B1ales`
- LLM-proxy usa campo `mensajes` (no `messages`) y `modelo` (no `model`)
- 6/6 pasan contra producción

**Paso 3 — Executor (`scripts/ejecutar-briefing.sh`):**
- Pipeline: parsear YAML → SQL staging → archivos → deploy staging → tests → regresión → (gate) → prod
- Modificación archivos via perl con env vars (`PERL_BUSCAR`, `PERL_INS`) para evitar shell escaping
- Métricas REST a `m%C3%A9tricas` con campos correctos (enjambre, evento, agente, exitoso, data)
- Deploy prod: pipe `echo "y"` para confirmación interactiva de `deploy.sh`
- Rollback automático si humo prod falla
- Logs en `logs/implementador/`

**Paso 4 — Tabla `cola_mejoras`:**
- Migración `20260227020000_cola_mejoras.sql`: tabla con campos tipo, origen, descripcion, contexto (jsonb), prioridad (0-1), estado
- CHECK constraints: tipo IN (mejora, bug, optimizacion, feature), origen IN (chief, mejora_continua, manual, telemetria)
- Helper `_shared/cola_mejoras.ts`: `escribirMejora()` para insertar desde cualquier agente
- Desplegada en staging + producción

**Paso 5 — Warmup E2E:**
- briefing-template.yaml ejecutado: YAML parseado → archivo modificado → deploy staging OK → test briefing pasa
- Regresión staging parcial (4/6): LLM-proxy y parseador fallan porque staging no tiene ANTHROPIC_API_KEY
- Métricas del implementador aparecen en producción: `briefing_inicio`, `briefing_fase`, `briefing_test`, `briefing_resultado`

**Métricas nuevas:** `briefing_inicio`, `briefing_fase`, `briefing_test`, `briefing_regresion`, `briefing_resultado`, `briefing_deploy_prod`, `briefing_rollback`, `briefing_error`
**Pendiente:** Configurar OPENAI_API_KEY en staging
**Coste:** $0 (scripting local, métricas via REST API, 0 LLM)

### Fase A1 — Compresor de Memoria (Capa Episódica + Síntesis) (completada)

**Objetivo**: Event sourcing de conversaciones. Cada turno se graba en `turnos_episodicos`. Al cerrar sesión, un compresor (Haiku) extrae decisiones, datos, patrones y los alimenta a `perfil_usuario` + `decisiones_chief`. Los turnos raw se borran post-compresión.

**5 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301010000_turnos_episodicos.sql`):
- `turnos_episodicos`: sesion_id, turno_num, input_usuario, output_sistema, ruta_usada, metadata
- `compresor_dead_letter`: Dead Letter Queue para compresiones fallidas (max 3 reintentos, cooldown 30min)
- ALTER `sesiones_chief`: +`estado` (abierta/pausada/comprimiendo/cerrada), +`pausado_hasta`, +`ultimo_turno_at`

**Pieza 2 — Escritura episódica** (orquestador-chief, +182 líneas):
- **Comandos de sesión**: `/cerrar` (compresión inmediata), `pausa hasta...` (max 48h), reactivación automática
- **9 puntos de escritura episódica**: insert en `turnos_episodicos` antes de cada return conversacional
- `ultimo_turno_at` actualizado en cada turno

**Pieza 3 — compresor-memoria** (343 líneas, Edge Function):
- Lee turnos → construye transcripción → LLM Haiku → extrae JSON estructurado
- Alimenta: `perfil_usuario` (datos+patrones, upsert con confianza creciente), `decisiones_chief`
- Graceful degradation: JSON parse falla → fallback con raw substring
- Dead letter queue: on error → inserta en `compresor_dead_letter`, revierte estado a "abierta"
- Telemetría máxima: turnos procesados, bytes, JSON completitud, LLM latencia, modelo, fallback

**Pieza 4 — cron-cierre-sesiones** (89 líneas, Edge Function):
- 3 criterios: sesiones abiertas >2h inactivas, pausas expiradas, dead letter retry
- Para cada una: llama `compresor-memoria` con trigger apropiado
- Dead letter retry exitoso → marca `resuelto: true`
- Invocado desde basal-cron (fire-and-forget)

**Pieza 5 — basal-cron** (+8 líneas):
- Llamada fire-and-forget a `cron-cierre-sesiones` tras marca basal

**Tests verificados (producción):**
- T1 ✅ Turno episódico escrito (turno_num=0, ruta=encuadre)
- T2 ✅ 2 turnos acumulados (encuadre + post_encuadre)
- T3 ✅ Compresor ejecutado: 2 turnos procesados, 3 datos, 2 patrones, JSON válido, 6.2s
- T4 ✅ Turnos borrados post-compresión
- T5 ✅ Sesión cerrada con resumen comprimido + ultimo_turno_at
- T6 ✅ perfil_usuario alimentado: 3 datos + 2 patrones + 1 sesgo
- T7a ✅ cron-cierre-sesiones funcional (0 procesadas, sin sesiones inactivas)
- T7b ✅ `/cerrar` funciona: comprime + devuelve resumen
- Regresión 6/6 OK

**Coste**: ~$0.001/compresión (Haiku, ~2000 tokens)
**Bug fix**: `supabase.from().insert().catch()` no funciona en Supabase client (no es Promise real) → reemplazado por try-catch

### Fase B0 — 11 Semillas Telemetría + Helper esTelemActiva (completada)

**Objetivo**: Preparar infraestructura de telemetría avanzada. 11 semillas dormidas que, al activarse, habilitan campos de métricas adicionales sin tocar el pipeline base.

**3 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301020000_b0_semillas_telemetria.sql`):
- ALTER TABLE: 3 columnas nuevas (`deploy_con` TEXT, `campos_dormidos` JSONB, `consumidor` TEXT)
- 11 INSERTs con condiciones como JSONB array (no JSONB[])
- Post-check: 19 semillas total

**Pieza 2 — Helper** (`_shared/telemetria_avanzada.ts`):
- `esTelemActiva(supabase, nombre)`: Cache 5min, query todas las telem_* en 1 llamada
- `telemActivas(supabase, [...])`: Batch check múltiples semillas
- Safe default: falla → false (pipeline nunca se rompe)

**Pieza 3 — Verificador extendido** (verificador-semillas, 314→342 líneas):
- Default case ampliado con handlers genéricos: `tipo: "semilla"` (check datos.semillasActivas), `tipo: "componente"` (false), métricas conocidas (sesiones_chief, datos_perfil_usuario, enjambres_operativos, decisiones_registradas)

**Tests verificados (producción):**
- T1 ✅ 19 semillas (8 originales + 11 nuevas)
- T2 ✅ Columnas nuevas presentes (deploy_con, campos_dormidos, consumidor)
- T3 ✅ Categoría 'expansion' en las 11
- T4 ✅ Condiciones JSONB parseables (array de objetos)
- T5 ✅ Verificador ejecuta sin error (19 semillas procesadas)

**Bug fix**: `condiciones` es JSONB (no JSONB[]) → SQL reescrito de `ARRAY[...]` a `'[{...}]'::jsonb`
**Coste**: $0 (0 LLM, código puro)

### Fase A2 — Basal-Observabilidad (completada)

**Objetivo**: Agregación multi-ventana (24h/7d/30d) de métricas por agente + detección de anomalías emergentes. CQRS read side de la tabla `métricas`. Sidecar puro — si falla, el pipeline sigue.

**4 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301030000_baselines_agentes.sql`):
- Tabla `baselines_agentes`: UPSERT por `(agente, enjambre, evento, ventana)`
- Columnas: count, avg/p50/p95/p99/min/max/stddev latencia, avg tokens in/out, avg/total coste, error_count/rate
- 3 índices: enjambre, ventana, calculado_at DESC
- CHECK constraint: `ventana IN ('24h', '7d', '30d')`

**Pieza 2 — Edge Function** (`basal-observabilidad/index.ts`, ~280 líneas):
- Fase 1: 3 queries paralelas (24h, 7d, 30d) filtrando agente NOT NULL
- Fase 2: Calcular agregados por (agente, enjambre, evento) + UPSERT en lotes de 50
- Fase 3: 5 reglas de detección de anomalías (latencia, errores, coste, volumen, variabilidad)
- Fase 4: Marca estigmérgia tipo "basal" por cada anomalía detectada
- Fase 5: Telemetría propia en métricas
- $0 LLM — código puro

**Pieza 3 — Integración basal-cron** (+7 líneas):
- Fire-and-forget `fetch()` a `basal-observabilidad` con `{trigger: "cron"}`
- Después de `cron-cierre-sesiones`, antes de `log_operaciones`

**Pieza 4 — Registro en estado_agentes**:
- `basal-observabilidad`, capa 0, enjambre mejora_continua, usa_llm=false

**Reglas de detección (5):**
| # | Anomalía | Condición | Confianza |
|---|----------|-----------|-----------|
| 1 | Latencia degradada | p50 24h > p95 30d × 1.5, min 10 samples | count/50 |
| 2 | Errores crecientes | error_rate 24h > 7d × 2, min 3 errores | count/30 |
| 3 | Coste escalado | coste 24h > diario 7d × 1.5, min $0.01 | count/20 |
| 4 | Volumen bajo | count 24h < diario 7d × 0.5, min 14/7d | count/50 |
| 5 | Variabilidad excesiva | stddev 24h > 7d × 2, min 10 samples | count/30 |

**Tests verificados (producción):**
- T1 ✅ Tabla baselines_agentes creada
- T2 ✅ Ejecución manual: 17 agentes, 70 grupos, 1 anomalía real, 986ms
- T3 ✅ Baselines populados (top: llm-proxy 664 llamadas/30d, orquestador-chief 56 turnos)
- T5 ✅ Marca de anomalía escrita (volumen_bajo en detector-estructura-argumental)
- T4 ✅ Métrica propia registrada con detalle completo
- T6 ✅ basal-cron invoca correctamente (trigger="cron", 18 agentes, 482ms)
- T7 ✅ Regresión 6/6

**Coste**: $0 (código puro, 0 LLM)

### Fase A3 — Auditor de Presupuestos (Beer S4) (completada)

**Objetivo**: Detectar suposiciones no verificadas en la arquitectura. Examinar qué asume el sistema que siempre funciona pero no está midiendo. Guard temporal: 1 ejecución cada 30 días. Coste: ~$0.02/mes (1 Haiku/mes).

**4 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260302010000_a3_auditor_presupuestos.sql`):
- ALTER CHECK `tipo` en cola_mejoras: añade `'presupuesto'`
- CREATE CHECK `origen` en cola_mejoras (no existía): `jesus/chief/mejora_continua/manual/telemetria/auditor`
- ADD COLUMN `contexto` JSONB en cola_mejoras (no existía)
- INSERT en estado_agentes (capa 0, idle, haiku, mensual)
- INSERT en registro_arquitectura (edge_function, mejora_continua)

**Pieza 2 — Edge Function** (`auditor-presupuestos/index.ts`, ~290 líneas):
- Guard temporal: 30 días desde última auditoría (query cola_mejoras origen='auditor'), bypass con `manual_force`
- Fase 1: Queries paralelas a `registro_arquitectura` + `estado_agentes`
- Fase 2: 6 detectores de código puro (D1-D6)
- Fase 3: 1 llamada Haiku via llm-proxy para verbalizar hallazgos
- Fase 4: Escribir propuestas en `cola_mejoras` (tipo='presupuesto', origen='auditor'), skip prioridad='bajo'
- Fase 5: Telemetría (`registrarMétrica`) + log_operaciones

**6 Detectores (código puro, $0):**
| # | Detector | Qué detecta |
|---|----------|-------------|
| D1 | Disponibilidad | Puntos únicos de fallo (≥5 dependientes) + proveedor LLM único |
| D2 | Latencia | Cascadas de timeout (profundidad ≥3 niveles de invocación) |
| D3 | Capacidad | Inventario: edge functions, tablas, agentes LLM vs free tier |
| D4 | Conectividad | Agentes LLM sin retry/conRetry en imports |
| D5 | Comportamiento | Sin cron de cierre de sesiones |
| D6 | Modelo LLM | Agentes con errores consecutivos + sin circuit breaker |

**Pieza 3 — Integración basal-cron** (+18 líneas):
- Guard mensual en basal-cron: query cola_mejoras origen='auditor', ≥30 días
- Fire-and-forget `fetch()` a `auditor-presupuestos` con `{trigger: "cron"}`
- Después de basal-observabilidad

**Pieza 4 — Registro en estado_agentes + registro_arquitectura**:
- `auditor-presupuestos`, capa 0, enjambre mejora_continua, usa_llm=true, modelo haiku

**Tests verificados (producción):**
- T1 ✅ Migración correcta: agente en estado_agentes + registro_arquitectura, CHECK acepta 'presupuesto'
- T2 ✅ Ejecución manual (manual_force): 149 componentes, 60 hallazgos, 9.2s
- T3 ✅ Propuesta escrita en cola_mejoras (tipo=presupuesto, origen=auditor, estado=pendiente)
- T4 ✅ Guard temporal funciona (skip=true, dias=0)
- T5 ✅ Métricas registradas (auditoria_completada + llamada_llm)
- T6 ✅ basal-cron invoca correctamente (auditor salta guard)
- T7 ✅ Regresión 6/6

**Hallazgos primera ejecución (60 total):**
- D1: llm-proxy es punto único de fallo (51 dependientes)
- D2: 3 cascadas de timeout (llamada-ias: 4 niveles)
- D3: 81 edge functions, 34 tablas, 53 agentes LLM
- D4: 53 agentes sin retry (mayor categoría)
- D5: cron-cierre-sesiones no registrado en registro_arquitectura
- D6: Sin circuit breaker en imports

**Nota**: Verbalización LLM truncada (max_tokens=1500 con 60 hallazgos → `stop_reason: "max_tokens"`). Fallback activado correctamente. En ejecuciones mensuales normales los hallazgos se verbalizarán mejor.

**Coste**: ~$0.02/mes (1 Haiku mensual, ~2000 tokens)

### Fase S-PROP — Propiocepción del Sistema (completada)

**Objetivo**: Modelo interno unificado del sistema. El sistema se observa a sí mismo, genera un snapshot JSONB integrando 7 tablas, detecta cambios (diff), y genera decisiones en un inbox para CR1.

**5 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260302020000_s_prop_propiocepcion.sql`):
- Tabla `estado_sistema`: snapshots JSONB con columnas desnormalizadas para queries rápidas
- Tabla `inbox_decisiones`: cola de decisiones con CHECK urgencia (critica/alta/normal/baja), CHECK categoria (error/rendimiento/coste/capacidad/mejora/presupuesto), CHECK estado (pendiente/aprobada/rechazada/pospuesta/auto_ejecutada/expirada)
- INSERT en registro_arquitectura (propiocepcion + dashboard-api + 2 tablas)
- INSERT en estado_agentes (propiocepcion, capa 0, idle, usa_llm=false)

**Pieza 2 — Edge Function propiocepcion** (`propiocepcion/index.ts`, ~280 líneas):
- Fase 1: 7 queries paralelas (registro_arquitectura, estado_agentes, enjambres, semillas_dormidas, cola_mejoras, métricas 24h, baselines_agentes 30d) + inbox pendientes
- Fase 2: Integrar snapshot JSONB unificado con score de salud (1.0 base, penalizado por errores/disabled/coste)
- Fase 3: Diff con snapshot anterior (errores nuevos, disabled nuevos, pico errores, componentes, salud degradada)
- Fase 4: Generar decisiones en inbox (errores >= 3, semillas listas, coste alto). Emergencia auto: >= 5 errores + critico → auto-disable
- Fase 5: Guardar snapshot + limpiar >90 días + telemetría
- Imports SO: `registrarMétrica`, `chequearSeñales`

**Pieza 3 — Edge Function dashboard-api** (`dashboard-api/index.ts`, ~200 líneas):
- `?q=estado`: Último snapshot completo
- `?q=inbox`: Decisiones pendientes/resueltas/auto-ejecutadas
- `?q=timeline&n=20`: Serie temporal de snapshots (para gráficos futuros)
- `?q=decidir` (POST): CR1 aprueba/rechaza/pospone decisión
- `?q=resumen`: JSON compacto para panel del Chief (salud, componentes, inbox, coste)

**Pieza 4 — Integración basal-cron** (+7 líneas):
- Fire-and-forget `fetch()` a `propiocepcion` con `{trigger: "cron"}`
- Al inicio del pipeline (antes de los 3 lentes basales)

**Tests verificados (producción):**
- T1 ✅ Migración: tablas creadas, agente registrado en estado_agentes + registro_arquitectura
- T2 ✅ Propiocepcion: 153 componentes, 58 agentes, salud 0.95, 687ms
- T3 ✅ Snapshot guardado: 50 idle, 8 disabled, 18 semillas dormidas, $0.27/día
- T4 ✅ Dashboard-api estado: snapshot con salud, enjambres, rendimiento, baselines
- T5 ✅ Dashboard-api inbox: 0 pendientes (correcto)
- T6 ✅ Dashboard-api resumen: JSON compacto con todos los campos
- T7 ✅ Dashboard-api decidir: decisión test aprobada por CR1
- T8 ✅ Regresión 6/6
- T9 ✅ Segundo snapshot: diff=null (sin cambios), 366ms

**Datos del primer snapshot real:**
- 153 componentes activos (83 edge_fn, 36 tabla, 29 módulo, 4 script, 1 interfaz)
- 58 agentes (50 idle, 8 disabled, 0 con errores)
- 4 enjambres activos (ias, diseno, chief_of_staff, mejora_continua)
- 18 semillas dormidas, 0 listas, 1 verificando
- Coste diario: $0.27 (216 ejecuciones en 24h)
- 19 agentes con baselines de 30 días

**Coste**: $0 (código puro, 0 LLM)

### Fase A4 — Detector Patrones Longitudinales (semilla dormida, completada)

**Objetivo**: Detectar tendencias longitudinales en la serie temporal del sistema: degradación progresiva, ciclos, acumulación sin resolver — patrones que snapshots individuales no ven. Se activa automáticamente cuando hay suficientes datos (~7 días).

**3 piezas implementadas:**

**Pieza 1 — Fix infraestructura** (basal-cron, +8 líneas):
- `verificador-semillas` añadido como fire-and-forget en basal-cron (después de propiocepcion, antes de lentes)
- Las 20 semillas ahora se evalúan automáticamente en cada ejecución del cron

**Pieza 2 — Migración SQL** (`20260302030000_a4_detector_patrones.sql`):
- ALTER CHECK `categoria` en semillas_dormidas: añade `'observabilidad'`
- INSERT semilla `detector_patrones_longitudinales` (3 condiciones, requiere CR1)
- INSERT `registro_arquitectura` (estado='dormido', edge_function, mejora_continua)
- INSERT `estado_agentes` (capa 0, idle, haiku, cada_6h)

**Pieza 3 — Edge Function** (`detector-patrones/index.ts`, ~290 líneas, **NO desplegada**):
- Guard temporal: ≥6h entre ejecuciones (usa métricas propias)
- Fase 1: Cargar serie temporal (estado_sistema + baselines_agentes últimos 30d)
- Fase 2: 5 detectores código puro ($0):
  - P1: Tendencia monotónica (pendiente mínimos cuadrados en salud, coste, disabled)
  - P2: Ciclos periódicos (errores concentrados por hora UTC, ≥28 snapshots)
  - P3: Acumulación sin resolver (cola_mejoras creciendo 3+ snapshots, disabled estancados)
  - P4: Degradación progresiva en baselines (latencia primera vs segunda mitad)
  - P5: Anomalías en diff (>50% snapshots con cambios = inestabilidad)
- Fase 3: 1 Haiku para verbalizar hallazgos (solo si hay)
- Fase 4: Propuestas en inbox_decisiones (urgencia ≥ media)
- Fase 5: Telemetría vía `registrarMétrica` + log_operaciones
- Imports SO: registrarMétrica, chequearSeñales, limpiarJSON

**Pieza 4 — verificador-semillas** (+20 líneas, ~360 líneas total):
- 3 queries nuevas en prefetchDatos: snapshots_7d, baselines_distinct_14d, propiocepcion_exitosa_7d
- 3 cases nuevos en evaluarCondicion: snapshots_suficientes, baselines_14_dias, propiocepcion_estable_7d

**Condiciones de la semilla:**
| Condición | Umbral | Actual (1 marzo) | Cumplida |
|-----------|--------|-------------------|----------|
| snapshots_suficientes | ≥28 en 7d | 2 | No |
| baselines_14_dias | ≥1 agente | 19 | **Sí** |
| propiocepcion_estable_7d | ≥28 exitosas | 2 | No |

**Auto-activación estimada**: ~8 marzo (condiciones) → ~15 marzo (7d estable + CR1)

**Tests verificados (producción):**
- T1 ✅ Migración correcta: semilla, registro_arquitectura (dormido), estado_agentes
- T2 ✅ Semilla insertada: 3 condiciones con actual actualizado
- T3 ✅ Verificador ejecuta: 20 semillas verificadas, A4 evaluada (1/3 cumplida)
- T4 ✅ Condiciones correctas: baselines=19 (cumplida), snapshots=2, propiocepcion=2
- T5 ✅ Regresión 6/6
- T6 ✅ detector-patrones NO desplegado (solo en repo)

**Coste**: $0 sin hallazgos, ~$0.30/mes con hallazgos (~$0.001/Haiku)

### Fase A5 — Completador Posiciones Sintácticas + Cruzador de Dominios (completada)

2 agentes decoradores capa 1 en enjambre chief_of_staff. Se disparan fire-and-forget desde profundo-runner después del Paso 3 (alternativas).

**Pieza 1 — SQL migración** (`20260302040000_a5_completador_cruzador.sql`):
- 2 INSERTs en `estado_agentes` (completador-posiciones + cruzador-dominios, capa 1, idle)
- 2 INSERTs en `registro_arquitectura` (estado activo)

**Pieza 2 — `completador-posiciones/index.ts`** (~260 líneas):
- PRE: Polling con `esperarAlternativas()` (max 30s, 3s interval) lee marcas de alt-radical + alt-incremental
- Clasifica qué posiciones sintácticas (sujeto, adverbial, adjetival, conector, nivel) cubren las alternativas
- Si 0 vacías → skip, si hay vacías → LLM Haiku genera alternativas/preguntas
- POST: Separa alternativas (con dato ≥5 chars) de preguntas sin dato
- Escribe marca tipo="hallazgo" capa=1. Dispara cruzador-dominios fire-and-forget
- Imports: `_shared/` (señales, métricas, limpiarJSON, retry)

**Pieza 3 — `cruzador-dominios/index.ts`** (~270 líneas):
- PRE: Lee marcas de alt-radical + alt-incremental + completador-posiciones del ciclo
- Extrae verbos nucleares (mantener, meter, sacar, distinguir, copiar, mover, conectar) con variantes
- Busca en `conocimiento_dominio` (verificado="real") registros de OTROS dominios con mismo verbo
- Calcula fuerza de match (base 0.3 + bonuses por posición, verificado, longitud). Min 0.5
- Si hay pares → LLM Haiku verbaliza conexiones abstractas (max 3 pares)
- Escribe marca tipo="hallazgo" capa=1

**Pieza 4 — Integración profundo-runner** (+6 líneas):
- Fire-and-forget `completador-posiciones` DESPUÉS del Paso 3 (alternativas ya escritas)
- Cruzador se dispara automáticamente desde completador

**Correcciones vs briefing**: 18 fixes aplicados:
- `estado: 'activo'` → `'idle'`, `ON CONFLICT (nombre)` → `(enjambre_id, nombre)`
- `system/tier/prompt` → `system_prompt/modelo/mensajes`, `content` → `respuesta`, `tokens_in/out` → `tokens_entrada/salida`
- limpiarJSON local → import `_shared/`, registrarTelemetria local → `registrarMétrica` `_shared/`
- sesion_id/turno en marcas → eliminados (no existen en tabla), hallazgo TEXT NOT NULL → añadido
- log_operaciones: exitoso/error_detalle → error (columna real)
- Integración en orquestador-chief → profundo-runner (alts no se disparan desde orquestador)
- Añadidos: chequearSeñales, conRetry, registro_arquitectura entries

**Tests**:
- T1 ✅ Migración: 19 agentes chief_of_staff (antes 17), 61 agentes totales
- T2 ✅ Deploy: 3 funciones (completador + cruzador + profundo-runner actualizado)
- T3 ✅ Completador sin marcas: Haiku genera 5 preguntas para posiciones vacías (~1.5s)
- T4 ✅ Marca escrita: hallazgo con analisis + preguntas
- T5 ✅ Cruzador sin alternativas: skip correcto
- T6 ✅ Cruzador lee completador: skip porque no hay verbos nucleares en preguntas genéricas

**Coste**: ~$0.002/ciclo (2 Haiku calls: completador + cruzador)

### Fase A6 — Confrontador de Posición entre Integradores (completada)

1 agente confrontador capa 2 en enjambre chief_of_staff. Se ejecuta sync (Paso 5.5) entre N45 y verbalizador.

**Pieza 1 — SQL migración** (`20260302050000_a6_confrontador_integradores.sql`):
- INSERT `estado_agentes` (confrontador-integradores, capa 2, idle)
- INSERT `registro_arquitectura` (estado activo)

**Pieza 2 — `confrontador-integradores/index.ts`** (~310 líneas):
- PRE: Lee marcas de N12 + N3 + N45 en paralelo (3 queries)
- Guard: min 2 integradores con datos, sino skip ($0)
- 5 detectores código puro:
  - D1 `direccion_opuesta`: N12 expande pero N45 contiene (o viceversa)
  - D2 `dato_contradice_trade`: N12 cita dato que contradice trade-off de N3
  - D3 `opcion_contradice_mision`: opción N3 contradice CR1 de N45 (12 pares opuestos)
  - D4 `vacio_asimetrico`: N12 dice que falta dato, pero N3 lo usa
  - D5 `tension_no_senalada`: N45 no detectó tensión pero D1/D3 sí encontraron
- Si incoherencias → LLM Haiku clasifica: `contradiccion` vs `tension`
- Escribe marca tipo="hallazgo" capa=2

**Pieza 3 — Integración profundo-runner** (+10 líneas):
- Paso 5.5 sync (await, timeout 15s) entre Paso 5 (integradores) y Paso 6 (verbalizador)
- Guard: solo ejecuta si ≥2 integradores OK
- `pipeline.confrontador` en profundo_resultado

**Pieza 4 — Integración chief-verbalizador** (+12 líneas):
- Extrae marca confrontador de la query masiva de ciclo
- Añade sección "INCOHERENCIAS ENTRE INTEGRADORES" al prompt Sonnet
- Reglas: contradicción → señalar explícitamente, tensión → articular como trade-off

**Correcciones vs briefing**: 14 fixes aplicados (mismos patrones que A5)

**Tests**:
- T1 ✅ Migración: pushed OK
- T2 ✅ Deploy: 3 funciones (confrontador + profundo-runner + verbalizador)
- T3 ✅ Confrontador sin integradores: skip correcto, 0 tokens

**Coste**: $0 si coherente (skip), ~$0.001/ciclo si incoherencias (1 Haiku)

### Fase 1.1 — Gateway API del Cerebro (2 marzo 2026)

**Migración**: `20260302060000_fase1_1_gateway.sql` — 4 tablas nuevas + seed data
- `tenants` (3 tenants: consola/exo-pilates/exo-fisio)
- `metering` (telemetría avanzada por request)
- `capability_registry` (22 capabilities: 12 activas + 10 disabled futuras — actualizada en 1.2)
- `tareas_async` (cola async con polling)

**Edge Function nueva**: `gateway/index.ts` (~370 líneas)
- **Auth**: X-API-Key header → lookup en tenants → estado activo
- **Manifest**: Cada tenant tiene lista de capabilities permitidas. `["*"]` = wildcard (consola)
- **Rate limiting**: Contra DB (metering count últimas 24h vs rate_limit_dia)
- **Circuit breaker**: 3 fallos → open (30s cooldown → half-open → retry)
- **Routing**: capability_registry mapea capability → edge_function
- **Metering**: Telemetría JSONB en cada request (gateway_overhead_ms, input_length, circuit_state, edge_function, etc.)
- **Modo sync**: Ejecuta y espera resultado. Timeout 120s via AbortController
- **Modo async**: Crea tarea + self-dispatch (fire-and-forget fetch al gateway con flag _internal_process). Polling via GET ?request_id=
- **Health check**: GET sin params → 200 healthy
- **Graceful degradation**: 5 niveles (todo OK → timeout → 503 → skip rate limit → health only)

**Capabilities activas (12, actualizado en 1.2)**:
| Capability | Edge Function | Nota |
|---|---|---|
| ias_completo | orquestador-ias | Pipeline completo monolítico (~105s) |
| diseno_analisis | orquestador-diseno | Ruta A: análisis + huecos |
| diseno_respuestas | orquestador-diseno | Ruta E: procesar respuestas |
| diseno_propuesta | orquestador-diseno | Ruta B: diseño + confrontación |
| diseno_spec | orquestador-diseno | Ruta C: specs implementación |
| diseno_verificar | orquestador-diseno | Ruta D: verificación + docs |
| observabilidad_estado | dashboard-api | GET ?q=estado |
| observabilidad_inbox | dashboard-api | GET ?q=inbox |
| observabilidad_timeline | dashboard-api | GET ?q=timeline |
| observabilidad_decidir | dashboard-api | POST ?q=decidir |
| observabilidad_resumen | dashboard-api | GET ?q=resumen |
| system_snapshot | propiocepcion | POST — snapshot completo |

**Tenants (actualizado en 1.2)**:
- `consola` — Jesús, wildcard `["*"]`, sync default, sin rate limit
- `exo-pilates` — 8 capabilities, async default, 200/día
- `exo-fisio` — 4 capabilities, async default, 200/día

**Correcciones vs briefing**: 3 fixes
1. Índice parcial `WHERE created_at > now()` → no IMMUTABLE → cambiado a índice normal
2. `gen_random_bytes(24)` → no existe sin pgcrypto → cambiado a `gen_random_uuid()`
3. `executeInBackground()` → no sobrevive al return → cambiado a self-dispatch pattern

**Tests**: 10/10 PASS (T1-T8 + T4b sync + async poll)
- Auth: 401 sin key, 401 key inválida
- Manifest: 200 consola wildcard, 403 pilates unauthorized
- Routing: 200 observabilidad sync, 202 async + poll completed
- E2E: IAS pipeline completo via gateway 98.1s
- Metering: 4+ registros con telemetry JSONB completo
- Health: 200 healthy v1.1

**Coste**: $0 (gateway es código puro, 0 LLM). El coste viene de las Edge Functions destino.

### Fase 1.2 — Catálogo de Capacidades (2 marzo 2026)

**Migración**: `20260302070000_fase1_2_catalogo_capacidades.sql`
- Elimina 8 capabilities falsas del seed 1.1 (wrappers que ejecutaban el mismo pipeline)
- Renombra `ias_analisis` → `ias_completo`
- Inserta 12 capabilities reales: 1 IAS + 5 diseño + 5 observabilidad + 1 propiocepción
- 10 capabilities disabled futuras (3 IAS granulares + 7 originales)
- Actualiza manifests: pilates 8 caps, fisio 4 caps
- Semilla dormida `granularizar_ias_por_demanda` (3 condiciones, requiere CR1)

**Patch gateway**: `executeCapability()` expandido (~80 líneas, antes ~30)
- **Ambassador pattern**: Capabilities GET (dashboard-api) traducidas desde POST del consumidor
- **Diseño route mapping**: `config.ruta` determina campos trigger (A=input, B=ciclo_id, C=aprobado, D=verificar, E=respuestas)
- **dashboard-api decidir**: POST con query params especiales
- Preserva AbortController 120s timeout en todos los paths
- Gateway versión 1.2

**Semilla dormida**: `granularizar_ias_por_demanda`
- Se activa cuando: >=100 requests IAS en 30d + >70% usan parcial del output + 2+ tenants activos
- Acción: refactorizar orquestador-ias para modo parcial (parseadores/lentes/calculador/completo)
- Requiere CR1

**Tests**: 10/10 PASS
- T1: Catálogo 12+10=22 capabilities
- T2: Pilates manifest 8 caps
- T3-T4: GET capabilities via gateway (estado 761ms, resumen 462ms)
- T5: system_snapshot via gateway (1228ms)
- T6: diseno_analisis Ruta A via gateway (117s)
- T7-T8: Manifest authorization (403/200 correcto)
- T9: Semilla dormida registrada, 3 condiciones
- T10: Metering con telemetría JSONB

**Coste**: $0 (datos + 1 patch código puro).

### Fase 1.3 — Metering y Coste (2 marzo 2026)

**Migración**: `20260302080000_fase1_3_metering_coste.sql`
- Tabla `metering_agregados` (tenant_id, periodo, periodo_inicio/fin, totales, by_capability JSONB, telemetry JSONB). UNIQUE(tenant_id, periodo, periodo_inicio)
- ALTER TABLE tenants ADD COLUMN `alertas_config` JSONB (coste_diario_max_usd, alertas_activas)

**Patch orquestador-ias**: Propagación de coste real desde tabla `métricas`
- Query `métricas` por `coste_usd > 0` desde timestamp start del ciclo
- Suma `coste_usd`, `tokens_in`, `tokens_out` → añadidos a respuesta JSON
- Resultado real: ~$0.10-0.12 por llamada IAS, ~32K tokens_in, ~15K tokens_out

**Patch orquestador-diseno**: Misma propagación, helper `sumarCoste()` reutilizado en 5 puntos de retorno (rutas A/B/C/D/E)

**Patch gateway**: 4 cambios
- `executeCapability()` recibe `supabase` como primer parámetro + `execStart` timestamp
- Fallback cost: si `result.cost_usd === 0`, query directa a `métricas`. Campo `_cost_source` para trazabilidad
- Metering lee `tokens_in || tokens_entrada` (backward compat)
- Nuevos endpoints GET: `?q=consumo` (por tenant, source=agregado con fallback realtime) y `?q=consumo_global` (solo wildcard tenants, projected_monthly)
- Gateway versión 1.3

**metering-cron**: Nueva Edge Function (~200 líneas)
- Agrega metering diario por tenant → UPSERT en `metering_agregados`
- Breakdown `by_capability` (requests, cost, tokens, latency_avg, errors)
- Telemetría: error_rate, projected_monthly_usd, cost_trend_vs_yesterday, avg_cost_per_request
- 3 alertas → `inbox_decisiones`: coste_diario_alto (normal), approaching_rate_limit (baja), anomalia_coste (alta, >50% vs misma semana anterior)

**Tests**: 9/9 PASS
- T1: IAS cost_usd > 0 ($0.10-0.12 en metering)
- T2: Metering tiene cost con source=orquestador
- T3: metering-cron ejecuta (3 tenants, 425ms)
- T4: metering_agregados poblado (6 requests, $0.47, by_capability)
- T5: ?q=consumo (source=agregado)
- T6: ?q=consumo_global (projected $14.19/month)
- T7: consumo_global denegado a no-wildcard (403)
- T8: Health version 1.3
- T9: Log cron OK

**Coste real medido**: IAS ~$0.10-0.12/llamada. Proyectado ~$14.19/mes (basado en 6 requests/día test).

### Primitivas v2 — Prisma Semántico (2 marzo 2026)

**Concepto**: Las primitivas son mini-enjambres que analizan un input desde múltiples ángulos simultáneos, como un prisma que descompone luz blanca. Cada primitiva es una lente distinta (sustantivizar = coseidad, sujeto-predicado = agencia). Diseñadas para ser independientes del framework — el orquestador recibe `llamarLLM` inyectado.

**Arquitectura común** (todas las primitivas):
- **Dial** (0.0–1.0): Controla ángulos activos. Escalado varía por primitiva (8 o 12 ángulos)
- **N ángulos × 2 polos**: Fan-out paralelo a N Haiku (según dial)
- **6 códigos semánticos**: natural, logico_matematico, operativo, financiero, cientifico, narrativo
- **Verificador**: Solo si dial >= 0.8. Retry 3× con backoff (2s/5s/8s para 12-ángulo, 1.5s/3s/5s para 8-ángulo)
- **Integrador**: Haiku final que sintetiza. Retry 3× con backoff (2s/4s) para primitivas de 12 ángulos
- **Parámetro `modelo`**: Default "haiku", override a "sonnet" disponible en runtime

**Primitiva 1 — Sustantivizar** (`primitiva-sustantivizar`):
- Analiza la "coseidad" del input: qué se sustantiviza, qué se omite, qué conceptos se reifican
- 8 ángulos: gramatical, referencial, metaforico, relacional, contextual, agentivo, temporal, axiologico
- 2 polos: sustantivo (qué se nombra como cosa) vs verbal (qué permanece como proceso)
- Output: array de cápsulas + síntesis (sustantivizaciones_clave, procesos_ocultos, recomendacion)
- Verificación (dial>=0.8): Detecta reificaciones peligrosas, procesos ocultos como sustantivos, y agencia fantasma
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests**: 9/9 PASS individual, 7/9 en suite (2 transient: verificador rate-limited, Supabase 502)

**Primitiva 2 — Sujeto-Predicado** (`primitiva-sujeto-predicado`):
- Analiza AGENCIA y RESPONSABILIDAD: quién hace qué, quién decide, quién se esconde
- 8 ángulos: agente, receptor, transferencia, capacidad, compromiso, accountability, temporal, delegacion
- 2 polos: sujeto (quién actúa) vs predicado (qué se predica/hace)
- Output: array de análisis (hallazgo + agencia 0.0-1.0 + alertas) + síntesis (agente_principal, nivel_agencia_global, mapa_responsabilidad, alertas_criticas)
- Verificación (dial>=0.8): Detecta agencia fantasma, transferencias ocultas, contradicciones
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests con Sonnet**: 6/8 PASS (T5 verificador rate-limited, T7 Supabase 502 transient)

**Resultados de detección de agencia (Sonnet)**:
| Input | Agencia | Detección |
|-------|---------|-----------|
| "Habría que mejorar el onboarding" | 0.05 | Agencia fantasma perfecta |
| "Hay que hacer algo con esto" | 0.03 | Mínimo posible |
| "Los alumnos no progresan como deberían" | 0.10 | Diluida |
| "El emprendedor sentía que el mercado..." | 0.07 | Narrativo pasivo |
| "El equipo debería encargarse..." | 0.11 | Transferencia disfrazada |
| "Si consigo financiación, montaré..." | 0.40 | Condicional |
| "Yo contrataré un instructor antes del 15 abril" | 0.96 | Agencia clara |

**Bugs corregidos** (aplicados a ambas primitivas):
1. `String(1.0)` → `'1'` en JavaScript (key lookup falla). Fix: `nivel.toFixed(1)`
2. Verificador rate-limited tras 16 Haiku paralelos. Fix: retry 3× con backoff (1.5s, 3s, 5s)
3. Edge Function `system_prompt` como campo separado (no en `mensajes[]`) para compatibilidad con llm-proxy

**Primitiva 3 — Adjetivar v2** (`primitiva-adjetivar`):
- Analiza POSICIONAMIENTO y RANGO: dónde está cada cosa en su escala, si tiene referencia o flota
- **12 ángulos** (7 cualificación + 5 medición): limite, equilibrio, posicion_red, estructura, tension, relacion, sostenimiento, escala, extremos, precision, dinamica, dominio
- 2 polos: sin_rango (detecta ausencia) vs rango_completo (establece posición)
- Cada ángulo de cualificación tiene invariantes como vocabulario (ej: limite→Caja Negra/Umbral Tensional, equilibrio→Nash/Atractor/Homeostasis)
- Dial: 0.2→1, 0.4→3, 0.6→8, 0.8→12, 1.0→12+verificador (24 Haiku paralelos)
- Output: array de análisis + síntesis (posicionamiento_principal, rangos_identificados, precision_global, adjetivos_vacios, mapa_posicionamiento)
- Verificación (dial>=0.8): Detecta adjetivos sin rango, rangos contradictorios, precisiones falsas
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (13 casos: 9 originales + T10-T13 cualificación)

**Primitiva 4 — Adverbializar** (`primitiva-adverbializar`):
- Analiza MODOS DE OPERAR: cómo opera algo, qué es implícito vs explícito
- **12 ángulos** (7 verbos de vida + 5 transversales): modo_mantener, modo_distinguir, modo_repartir, modo_responder, modo_copiar, modo_sacar, modo_meter, grado, condicionalidad, sostenibilidad, coste, dependencia
- 2 polos: modo_implicito (detecta modos no declarados) vs modo_explicito (establece mecanismo concreto)
- Cada verbo de vida tiene invariantes como vocabulario (ej: modo_mantener→Homeostasis/Conservacion/Tensegridad/Atractor, modo_responder→Retroalimentacion/Coevolucion/Variedad Requisita)
- **HUECO CRÍTICO modo_meter**: Tiene menos invariantes que los demás — atención especial en prompts y verificador
- Dial: mismo escalado que adjetivar v2. 24 Haiku paralelos en dial 0.8/1.0
- Output: array de análisis (hallazgo + modo {explicitud, descripcion, verbo_vida} + invariantes_detectadas) + síntesis (modo_dominante, verbo_vida_principal, explicitud_global, modos_ocultos, invariantes_activas, mapa_modos)
- Verificación (dial>=0.8): Detecta modos implícitos, contradictorios, huecos_modo_meter, invariantes_ausentes
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests**: T1 explicitud 0.05 ("funciona bien"), T4 verbo_vida="meter", T8 dial mínimo 3 haikus

**Primitiva 5 — Preposicionar** (`primitiva-preposicionar`):
- Analiza RELACIONES Y NIVELES LÓGICOS: preposiciones ocultas, colapsos entre niveles, ausencias estructurales
- **8 ángulos**: nivel, contencion, direccion, limite, distancia, jerarquia, dependencia, ausencia
- 2 polos: no_declarada (detecta relación implícita) vs declarada (establece relación explícita)
- Basado en 5 TIPOS LÓGICOS: conducta (N1), interpretación (N2), criterio/valor (N3), regla/norma (N4), meta/identidad (N5)
- Output: array de análisis (hallazgo + relacion {declarada, tipo, elementos, preposicion_implicita} + nivel_logico {detectado, esperado, colapso, descripcion_colapso}) + síntesis (nivel_logico_dominante, colapsos_detectados, relaciones_principales, preposiciones_ocultas, ausencias_criticas, mapa_relaciones)
- Verificación (dial>=0.8): Detecta colapsos entre niveles, preposiciones fantasma, ausencias estructurales
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests**: 7/12 PASS (5 fallos son dial>=0.8 por rate-limiting del verificador). T1 detecta colapso conducta→valor, T3 colapso forma→intención, T7 ausencias "hacia/según/dentro de/desde"

**Primitiva 6 — Conjuntar** (`primitiva-conjuntar`):
- Analiza ESTRUCTURA CONECTIVA: cómo se unen y separan las piezas. Conectores reales, falsos y ausentes
- **8 ángulos**: adicion, oposicion, alternativa, causalidad, condicion, temporalidad, concesion, ausencia_conexion
- 2 polos: desconexion (detecta conexión rota/ausente) vs conexion_explicita (establece conexión real)
- Output: array de análisis (hallazgo + conexion {tipo, elementos, fuerza, legitimidad} + conectores_detectados) + síntesis (estructura_conectiva, conexiones_fuertes, conexiones_rotas, piezas_sueltas, falsas_logicas, mapa_conexiones)
- Verificación (dial>=0.8): Detecta conexiones forzadas, falsas dicotomías, causalidades falsas, piezas sueltas
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Smoke tests**: Detecta falsa dicotomía ("o crecemos o morimos"), causalidad circular ("somos los mejores porque...")

**Primitiva 7 — Verbo** (`primitiva-verbo`):
- Analiza la ACCIÓN NUCLEAR: qué verbo real subyace, disfraces, fuerza, resultado
- **8 ángulos**: accion_nuclear, verbo_vida, objeto, completitud, disfraz, fuerza, resultado, multiplicidad
- 2 polos: accion_difusa (detecta verbo oculto/disfrazado) vs accion_nuclear (establece verbo real)
- Basado en 7 VERBOS DE VIDA: MANTENER, DISTINGUIR, REPARTIR, RESPONDER, COPIAR, SACAR, METER
- Output: array de análisis (hallazgo + accion {verbo_nuclear, verbo_vida, fuerza, produce_resultado} + verbos_detectados) + síntesis (verbo_nuclear, verbo_vida, objeto_real, fuerza_global, produce_resultado, verbos_disfrazados, verbos_vacios, mapa_acciones)
- Verificación (dial>=0.8): Detecta multiplicidad paralizante, disfraces no clasificados, verbos competidores
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Tests**: **11/11 PASS**. T1 detecta "gestionar/optimizar" como disfraces, T2 "contratar"→METER (fuerza 0.95), T5 verbo fantasma (fuerza 0.07), T6 DISTINGUIR, T10 COPIAR, T11 SACAR

**Archivos totales**: 24 en `_shared/primitivas-v2/` + 7 Edge Functions + 7 tests = 38 archivos
**Coste**: ~$0.01-0.03/llamada Haiku (8-24 ángulos + integrador), ~$0.05-0.12/llamada Sonnet

### Motor-Orquestador (3 marzo 2026)

Fan-out 7 primitivas → fusión por capas → verbalización semántica neutra. Produce respuesta neutra que la interfaz adecúa al usuario.

**Pipeline**:
1. PASO 0: Validar + aplicar lente (salud/sentido/continuidad) a diales (max, nunca baja)
2. PASO 1: Fan-out 7 primitivas via Promise.allSettled (fetch paralelo, 120s timeout)
3. PASO 3-4: Fusión PIEZAS (sustantivizar+adjetivar+adverbializar+preposicionar) + ESTRUCTURA (conjuntar+verbo+sujeto_predicado)
4. PASO 5: Cruce (6 reglas: agencia×modo, compresión×conexiones, nivel×acción, conexiones_rotas×agencia, modos_ocultos×colapsos, verbo_vacío×adjetivos_vacíos)
5. PASO 6: Verbalización — template ($0, ~80%) / haiku (~20% si alertas>2 o confianza<0.4) / fallback mecánico
6. PASO 7: registrarMétrica con traza completa

**Degradación graceful** (5 niveles):
- Nivel 0: Todo ok (7/7 + verbal ok)
- Nivel 1: 1-2 primitivas fallan
- Nivel 2: 3-4 fallan
- Nivel 3: 5+ fallan
- Nivel 4: verbal también falla → fallback mecánico

**Output**: `{ ok, respuesta_semantica, datos: { input_transformado, estructura_detectada, alertas_cruce, confianza_global }, metadata, telemetria }`

**Archivos**:
- `motor-orquestador/index.ts` — Edge Function (~250 líneas)
- `_shared/motor/`: tipos.ts, lentes.ts, fusion.ts, verbalizador.ts, telemetria.ts, index.ts (6 módulos)
- Migraciones: `20260303010000_motor_orquestador.sql`, `20260303020000_motor_gateway_capability.sql`

**Gateway**: capability `motor_analisis_completo` v1. Accesible via consola, exo-pilates, exo-fisio

**Telemetría extendida** (PASO 2): Cada orquestador de primitiva ahora expone en meta:
- `angulos_fallidos`: count de ángulos con confianza 0
- `angulos_detalle`: array {angulo, polo, ok} por cada ángulo
- `integrador_latencia_ms`: timing del integrador
- `fast_path`: true si dial <= 0

**E2E staging**:
- T1 (dial=0.3, no lens): 7/7 OK, haiku mode, 46.5s, $0.021
- T2 (dial=0.5, lens=salud, financiero): 7/7 OK, template mode, 114s, $0.09
- T3 (dial=0.0): 7/7 OK, haiku mode, 17.6s, $0.022
- T4 (via gateway): OK, respuesta semántica neutra

**BLOQUEANTE**: Deploy a prod bloqueado por 402 "Max number of functions reached". Necesita upgrade plan o delete funciones no usadas.

---

## 7. SEMILLAS DORMIDAS (Auto-Evolución)

22 semillas (8 originales + 11 telemetría B0 + 1 A4 + 1 gateway 1.2 + 1 metering 1.3). Verificador corre periódicamente ($0 LLM).

### 7.1 Semillas Originales (8) + A4 (1)

| # | Semilla | Categoría | Estado | Condiciones | CR1 |
|---|---------|-----------|--------|-------------|-----|
| 1 | `auto_mejora_agentes` | auto_mejora | **dormida** | 2/5 met (staging+registro) | No |
| 2 | `modificar_enjambres` | auto_diseño | dormida | Requiere: diseñador funcional + registro + auto_mejora activa | Sí |
| 3 | `cross_enjambre` | cross_enjambre | **verificando** | 3/3 met. Auto-activa ~6 marzo 2026 | No |
| 4 | `generar_interfaz` | interfaz | dormida | Requiere: diseñador + template HTML + interfaz estable 7d | No |
| 5 | `sensor_externo` | sensor_externo | dormida | Requiere: SO estable 30d + presupuesto + API access | Sí |
| 6 | `auto_diseño` | auto_diseño | dormida | Requiere: auto_mejora 90d + diseñador maduro + cross + 0 rollbacks | Sí |
| 7 | `auto_evolucion_disenador` | auto_mejora | dormida | Requiere: auto_mejora 180d + auto_diseño + tests 100% + 0 rollbacks 90d | Sí |
| 8 | `activar_compresor_memoria` | expansion | dormida | Requiere: 30 sesiones + 20 datos perfil + compresor deployado | No |
| A4 | `detector_patrones_longitudinales` | observabilidad | **dormida** | 1/3 met (baselines). Auto-activa ~15 marzo | Sí |

### 7.2 Semillas Telemetría B0 (11)


| # | Semilla | Deploy con | Consumidor | Campos dormidos |
|---|---------|-----------|------------|-----------------|
| B1 | `telem_llm_proxy_avanzada` | llm-proxy | basal-observabilidad | tokens_system, ratio_system_prompt, fue_retry, circuit_breaker, latencia_red_ms, stop_reason |
| B2 | `telem_agentes_calidad` | template-agente | basal-observabilidad | marcas_leidas, json_completitud, dependencias_faltantes, modo_degradado |
| B3 | `telem_traza_orquestador` | orquestador-chief | basal-observabilidad | ciclo_id, fases, cuello_botella, ruta, estado_cola |
| B4 | `telem_patrones_cr1` | orquestador-chief | basal-observabilidad | input_tipo, ms_desde_ultimo_turno, tendencia_engagement |
| B5 | `telem_no_acciones` | interfaz | basal-observabilidad | dwell_time, preguntas_ignoradas, profundo_sin_engagement |
| B6 | `telem_journey` | interfaz | basal-observabilidad | pasos, patron, engagement_score |
| B7 | `telem_outcome_negocio` | basal-outcomes | detector-mejora | outcome_7d/14d/30d, impacto_real_eur, atribuibilidad |
| B8 | `telem_outcome_sistema` | basal-outcomes | detector-mejora | metricas_antes/despues, veredicto, auto_revert |
| B9 | `telem_meta_outcome` | basal-mejora-continua | cr1 | precision, tasa_aprobacion, recomendacion |
| B10 | `telem_eficiencia` | basal-eficiencia | detector-mejora | tasa_consumo_agente, redundancia, candidatos_eliminacion |
| B11 | `telem_prediccion_adaptativa` | orquestador-chief | orquestador-chief | modelo_usuario, modelo_sistema, adaptacion_tiempo_real |

Todas `categoria: 'expansion'`, `estado: 'dormida'`, `requiere_aprobacion_cr1: false`.

**Columnas B0** (ALTER TABLE): `deploy_con` (TEXT), `campos_dormidos` (JSONB), `consumidor` (TEXT).

### 7.3 Helper telemetría

`_shared/telemetria_avanzada.ts`: `esTelemActiva(supabase, nombre)` con cache 5min. `telemActivas(supabase, [...])` batch. Si falla → false (safe default, pipeline nunca se rompe).

**Flujo de estados**: dormida → verificando (condiciones met) → lista (7 días estable) → activa (auto si !requiere_aprobacion_cr1)

---

## 8. SPECS Y DOCUMENTOS

### Specs existentes (en `supabase/spec/`):

| Documento | Resumen |
|-----------|---------|
| `SEMILLA_OMNI_MIND_PRODUCTO_EXOCORTEX.md` | Visión: OMNI-MIND como SaaS vertical (base IAS + diseño que auto-personaliza). Modelo: €X/mes |
| `SPEC_ENJAMBRE_ECOSISTEMA_APPLE.md` | Caso test del enjambre diseño: maximizar ecosistema Apple (Shortcuts+Automator) para estudio Pilates |
| `SPEC_INTERFAZ_APP.md` | Interfaz nativa: Electron (Mac), PWA (iPhone), iOS Shortcuts |
| `SPEC_MAPA_MODELOS_LLM.md` | Mapa de modelos LLM con análisis de tiers. Recomendación: NO cambiar ahora (Haiku+Sonnet) |

### Interfaz web: `ias.html`
- Consola modular OMNI-MIND (PWA-capable, dark theme)
- Sidebar con enjambres + status dots
- Dashboard con grid basal
- Conectada al pipeline Chief of Staff via polling

---

## 9. SCRIPTS Y TOOLING

| Script | Propósito |
|--------|-----------|
| `scripts/deploy.sh` | Deploy a staging/prod (migraciones + funciones) |
| `scripts/deploy-webapp.sh` | Deploy interfaz web |
| `scripts/ejecutor-code.mjs` | Lee SPEC del diseño, llama Claude Code CLI, ejecuta resultado |
| `scripts/ejecutor-daemon.mjs` | Daemon que poll SPECs y los procesa async |
| `scripts/lib/` | Librerías compartidas para ejecutores |

---

## 10. DECISIONES CR1 VIGENTES

1. **Comunicación solo estigmérgia** — nunca llamadas directas entre agentes
2. **Haiku para parseadores** — económico, suficiente para análisis sintáctico
3. **Sonnet para diseño/síntesis** — creatividad y razonamiento complejo
4. **Pipeline IAS universal** — mismo motor para cualquier dominio
5. **Lentes no diagnostican** — solo organizan datos; el cruzador diagnostica
6. **Jesús aprueba todo** — CR1 manual en cada paso
7. **Calidad > velocidad** — presupuesto €200/mes
8. **Código en inglés, comunicación en español**

---

## 11. PATRONES CLAVE

### limpiarJSON robusta
JSON de LLM a veces viene truncado. 5 pasos: strip backticks → find braces → parse → close strings → recount brackets.

### Orquestador multi-ruta
Un solo Edge Function (orquestador-chief: 2032 líneas) con routing por estado:
```
!estado → encuadre
ultimo_tipo = encuadre/init_async → post_encuadre
!cola || esCambioTema → init_async/reset_async
else → ruta C continua
```

### Fire-and-forget via pg_net
Para trabajo async: `supabase.rpc("disparar_edge_function", {...})`. El await es ~10ms (Postgres acepta). La función corre en background.

### Estado vía marcas
El estado de una sesión se guarda como una marca tipo "sintesis" en `marcas_estigmergicas`. Se lee al inicio de cada turno filtrado por sesion_id.

### Métricas
`registrarMétrica` DEBE ser await (Edge Functions terminan al hacer return). NO pasar sesion_id (FK constraint).

---

## 12. PARA CONTINUAR TRABAJANDO

### Lo que funciona hoy:
- Chat completo via orquestador-chief (5+ turnos verificados)
- Profundo con router + contradicciones + completador posiciones + cruzador dominios + confrontador integradores (~55-65s)
- Enjambre de diseño E2E (18 agentes, 6 capas)
- Mejora continua (3 agentes + cron + observabilidad + auditor + propiocepcion + detector-patrones dormido)
- Propiocepción: modelo interno unificado (157 componentes, 62 agentes, salud score)
- Dashboard-api: 5 endpoints para interfaz CR1 (estado, inbox, timeline, decidir, resumen)
- 20 semillas con verificador automático (invocado desde basal-cron)
- Persistencia inter-sesión (perfil + emergencias)

### Lo que falta (specs existentes):
- **Ecosistema Apple** (spec escrita): Shortcuts → Supabase como primer caso test del enjambre diseño
- **Interfaz nativa** (spec escrita): Electron Mac + PWA iPhone + Shortcuts
- **Producto exocortex** (semilla escrita): OMNI-MIND como SaaS vertical

### Lo que podría ser siguiente:
- Plan del flujo continuo paralelo (existe como plan file, no implementado)
- Activación de semillas que van cumpliendo condiciones
- Nuevos enjambres diseñados por el enjambre de diseño
- Compresor de memoria inter-sesión



## Contexto/MEMORY.md

# OMNI-MIND CEREBRO — Memoria de proyecto

## Arquitectura
- **Producción**: `cptcltizauzhzbwxcdft` (URL: `https://cptcltizauzhzbwxcdft.supabase.co`)
- **Staging**: `jbfiylwbgxglqwvgsedh` (authentic-pilates). 45 migraciones + 98 funciones desplegadas. ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY
- **Deploy script**: `./scripts/deploy.sh staging|prod [--only fn] [--migrations-only] [--functions-only]`
- **Bootstrap migration**: `00000000000000_bootstrap_base_tables.sql` — 12 tablas base pre-migración
- **Edge Functions**: Deno/TypeScript, desplegadas con `supabase functions deploy <name> --no-verify-jwt`
- **Comunicación entre agentes**: SOLO stigmérgia via tabla `marcas_estigmergicas` — nunca llamadas directas
- **LLM**: Todas las llamadas via `llm-proxy` Edge Function (soporta haiku/sonnet con fallback)
- Ver [architecture.md](architecture.md) para detalles completos

## Enjambres activos
1. **IAS** (Pipeline diagnóstico): ~10 agentes, capas 1-5, funcional
2. **Diseño** (Meta-diseño): 18 agentes, capas 1-6, E2E funcional — ver [enjambre-diseno.md](enjambre-diseno.md)
3. **Chief of Staff**: Pipeline dual superficial+profundo — ver abajo
4. **Mejora Continua**: 3 agentes (detector, procesador, basal), capas 1-3, operativo. Enjambre ID dinámico (buscar por nombre='mejora_continua')

## Pipeline Chat Continuo (orquestador-chief)
- **Turno 0 ENCUADRE** (~500ms): Pregunta instantánea de encuadre (código puro). Parseadores + profundo se disparan en background via pg_net
- **Ruta A INIT ASYNC** (~400ms): Cambio de tema o cola null → fire-and-forget (4 parseadores + profundo via pg_net) + pregunta encuadre instantánea. Rutas: `init_async` / `reset_async`
- **Post-encuadre** (~12-15s): Lee parseador marcas. Build cola + emite 2 preguntas. Entra tras `ultimo_tipo === "encuadre" || "init_async"` (sin check esCambioTema)
- **RUTA C CONTINUA (turno 2+)**: Flujo sin fin. Superficial + profundo en paralelo. RUTA B eliminada
  - Cola de preguntas con priorizarCola() inteligente (gravedad, fuente, overlap, contexto emocional)
  - Profundo inyecta preguntas en cola (fuente="profundo", gravedad="critico")
  - Cuando profundo listo → `cola_profundo_continuo` (respuesta + preguntas continuas)
  - Cola vacía → regeneración via parseadores async → `cola_regen`
  - Auto-re-dispatch profundo tras fallo o 3 turnos idle
- **Rutas**: `encuadre` → `post_encuadre` → `cola` / `cola_modo` / `cola_profundo_continuo` / `cola_vacia_esperando` / `cola_regen` / `init_async` / `reset_async`
- **Estado continuo**: `profundo_emitidos` (int), `ultimo_profundo` (obj), `profundo_dispatch_total` (max 8), `profundo_turnos_sin_dispatch`, `intencion`, `modo_activo`, `modo_historia`
- **Router de modos** (Fase 6): `detectarIntencion()` → 5 tipos (expandir/decidir/diagnosticar/ejecutar/auditar). `determinarModo()` → 9 modos via (intención × profundoTerminado × mcmSuficiente). Modos que interceptan cola: escucha (respuesta corta), ejecutar_lite (solo criticas), auditar_recoger
- **Verbalizador**: 6 prompts por modo (diagnosticar/confrontar/elaborar/responder/ejecutar_full/auditar_emitir). Lee modo de marca sintesis (estigmergia)
- **detectCambioTema**: Requiere 3+ inputs acumulados, threshold 0.9 (90%+ keywords nuevas). STOP words incluyen verbos conversacionales (quiero, tengo, estoy, necesito, etc.)
- **CRÍTICO**: NO despachar profundos concurrentes — el verbalizador falla por rate limiting del LLM. Despachar solo tras completar/fallar el anterior
- **profundo-runner**: `listo` solo true si verbalizador exitoso Y respuesta no vacía. `fallido: true` si verbal falla
- **Profundo**: ~55-60s por ciclo. Max 5 emitidos, max 8 dispatches por sesión
- **IMPORTANTE**: tabla `marcas_estigmergicas` CHECK constraint en `tipo`. Valores: hallazgo, sintesis, alerta, etc.
- **Marcas de parseadores no tienen campo `ok`**: Al leer de marcas, añadir `ok: true` para compatibilidad con mergeParseadores

## Fase 6: Router Modos Conversacionales + Fix Telemetría (completada)
- **Paso 0**: 8x `await` añadidos. Verbalizador migrado al SO (chequearSeñales, registrarMétrica, conRetry). 0 log_operaciones directo
- **Paso 1**: `detectarIntencion()` reemplaza `clasificarIntencion()`. 5 intenciones: expandir, decidir, diagnosticar, ejecutar, auditar
- **Paso 2**: `determinarModo()` → 9 modos. Lee mcm_suficiente del profundo. Persistido en estado
- **Paso 3**: Switch por modo en RUTA C. escucha (0 preguntas), ejecutar_lite (solo críticas), auditar_recoger. Detección cambio intención mid-sesión
- **Paso 4**: 6 system prompts por modo en verbalizador. Lee modo de marca sintesis (estigmergia)
- **Métricas nuevas**: intencion_detectada, modo_cambio, modo_escucha_activo, modo_ejecutar_lite, intencion_cambio

## Fase 7: Agente Implementador Autónomo (completada)
- **Pipeline local**: Briefing YAML → SQL → archivos → deploy → tests → regresión → prod (no Edge Function)
- **Archivos nuevos**: `specs/briefing-schema.yaml`, `specs/briefing-template.yaml`, `CLAUDE.md`, `tests/regresion.sh`, `scripts/ejecutar-briefing.sh`
- **Tabla nueva**: `cola_mejoras` (migración 20260227020000). Helper: `_shared/cola_mejoras.ts` (`escribirMejora()`)
- **macOS compat**: perl `ms_now()`, poll-based timeout fallback (sin `timeout`/`gtimeout`), env vars para perl substitution
- **REST API**: Tablas con acentos → URL encoding (`m%C3%A9tricas`, `se%C3%B1ales`). LLM-proxy campos: `mensajes` (no messages), `modelo` (no model)
- **Env files**: `.env.staging` (STAGING_URL, STAGING_KEY, STAGING_SERVICE_KEY), `.env.prod` (PROD_URL, PROD_KEY, PROD_SERVICE_KEY)
- **Regresión**: 6 tests, 6/6 pasan prod. Staging 4/6 (falta ANTHROPIC_API_KEY)
- **Métricas**: enjambre="implementador". Eventos: briefing_inicio/fase/test/regresion/resultado/deploy_prod/rollback/error

## Fase 4: Progressive Revelation Ruta A (completada)
- **Ruta A reescrita**: De sync ~3-6s (6 LLM calls) a async ~400ms (fire-and-forget via pg_net)
- **Patrón**: Idéntico a Turno 0 — dispara 4 parseadores + profundo via pg_net, devuelve pregunta encuadre instantánea
- **POST-ENCUADRE expandido**: Acepta `ultimo_tipo === "init_async"` además de `"encuadre"`
- **3 bugs corregidos**: (1) detectCambioTema siempre false (push antes de detect), (2) POST-ENCUADRE bloqueado por esCambioTema, (3) STOP words sin verbos conversacionales
- **E2E verificado**: 5 turnos en producción (encuadre→post_encuadre→cola→cola→reset_async)

## Fase 5: Dosificación cola_emergencia (completada)
- **profundo-runner**: 591 líneas. `extraerInsightsSobrantes()` extrae alt radical, coste no actuar, tensiones extra, preguntas extra, tensión N45
- Batch insert en `cola_emergencia` (max 5, prioridades 0.8→0.3). Orquestador dosifica 1/turno (ya existía)
- **cola_emergencia.sesion_id** es UUID — guard con regex antes de insertar
- Paso 3 alternativas ahora capturadas en variables (`resAltInc`, `resAltRad`, `resAltDesc`)

## Fase 3 Profundo: Router + Contradicciones (completada)
- **profundo-runner**: 591 líneas (antes 477→antes 139). Paso 0 antes del pipeline principal
- **Paso 0** (481ms): 5 queries paralelas (chiefMarca, niveles, calc, perfil, decisiones) + detector contradicciones + router
- **routerEnjambresProfundo**: Código puro <5ms. 5 reglas: contradiccion→full, operativo_n1n2→skip heavy, datos→skip identity, emocional→skip descarte, n4n5→full
- **detectarContradiccionesInter**: Sandwich PRE→Haiku→POST. Detecta contradicciones input vs decisiones/patrones históricos. Inserta en cola_emergencia
- **Router guards**: Pasos 2, 3, 5 respetan skip set del router
- **chief-verbalizador**: ~300 líneas. Conectado al SO (chequearSeñales, registrarMétrica, conRetry). 6 prompts por modo. Lee modo de marca sintesis
- **Rutas verificadas**: default_completo, dominio_datos (skip 3), input_emocional (skip 1), operativo_puro_n1n2 (skip 5)

## Fase 0 SO (completada)
- orquestador-chief + profundo-runner conectados a `_shared/` (señales, métricas, retry)
- `registrarMétrica` DEBE ser `await`ed (Edge Functions terminan en Response return)
- NO pasar `sesion_id` a `registrarMétrica` desde chief (FK → sesiones_enjambre, chief sessions no están ahí). Poner en `data` jsonb
- `chequearSeñales` valida formato UUID antes de incluir sesion_id en `.or()` (fix en señales.ts)

## Registro de Arquitectura Vivo (completado)
- 144 componentes en `registro_arquitectura` (80 edge_function, 30 tabla, 29 modulo_shared, 4 script, 1 interfaz)
- `deploy.sh` auto-actualiza `ultimo_deploy`, `lineas` y crea `historial_cambios` tras cada deploy
- `ruta` es nullable (tablas no tienen ruta de archivo)
- Migración seed: `20260226060000_registro_inventario_seed.sql`

## Fase 2 Persistencia Entre Sesiones (completada)
- 3 tablas: `perfil_usuario`, `cola_emergencia`, `sesiones_chief`
- Migración: `20260226070000_fase2_persistencia_sesiones.sql`
- **perfil_usuario**: Acumula datos, sesgos, nominalizaciones. confianza crece +0.1 por ocurrencia (max 0.95)
- **cola_emergencia**: Insights del profundo dosificados 1 por turno (prioridad DESC)
- **sesiones_chief**: Upsert en turno 0, counter update fire-and-forget en cada turno
- `actualizarPerfil()` es fire-and-forget (8 puntos de inserción antes de cada Response return)
- Perfil leído al inicio de sesión (confianza >= 0.5, limit 20), pasado a saveState datos
- Emergencias inyectadas en cola como `fuente: "emergencia", gravedad: "critico"` en 3 puntos

## Sistema de Auto-Evolución — Semillas Dormidas (completado)
- Tabla `semillas_dormidas` con 20 semillas (8 originales + 11 telemetría B0 + 1 A4). Migración original: `20260227010000_semillas_dormidas.sql`
- **verificador-semillas**: Edge Function, código puro $0 LLM. Chequea condiciones, gestiona transiciones (~360 líneas). Invocado desde basal-cron + Chief turno 0
- Estado: dormida → verificando (condiciones met) → lista (7 días estable) → activa (auto si !requiere_aprobacion_cr1)
- Revierte verificando → dormida si condiciones dejan de cumplirse
- **cross_enjambre** ya en "verificando" (3/3 condiciones met el 27/02/2026, auto-activará ~6 marzo)
- **auto_mejora_agentes**: 2/5 condiciones met (staging_funcional + registro_actualizado)
- Categorías CHECK: auto_mejora, auto_diseño, cross_enjambre, interfaz, sensor_externo, expansion, observabilidad

## Fase B0 — 11 Semillas Telemetría (completada)
- **Migración**: `20260301020000_b0_semillas_telemetria.sql` — ALTER TABLE (3 cols) + 11 INSERTs
- **Columnas nuevas**: `deploy_con` (TEXT), `campos_dormidos` (JSONB), `consumidor` (TEXT)
- **11 semillas telem_***: Todas `expansion`, `dormida`, sin CR1. Deploy_con indica qué componente las despliega
- **Helper**: `_shared/telemetria_avanzada.ts` — `esTelemActiva()` cache 5min, `telemActivas()` batch. Falla → false (safe)
- **verificador extendido**: Default case con handlers genéricos para tipo semilla/componente/metrica
- **IMPORTANTE**: `condiciones` es JSONB (JSON array), NO JSONB[] (PostgreSQL array). Usar `'[{...}]'::jsonb`

## Fase A2 — Basal-Observabilidad (completada)
- **baselines_agentes**: Tabla UPSERT multi-ventana (24h/7d/30d) por (agente, enjambre, evento, ventana). CQRS read side
- **basal-observabilidad**: Edge Function ~280 líneas. 5 fases: query paralela → calcular agregados → upsert baselines → detectar anomalías → marcas + telemetría
- **5 reglas detección**: latencia (p50>p95×1.5), errores (rate×2), coste (diario×1.5), volumen (<0.5), variabilidad (stddev×2)
- **Integración**: Invocado desde basal-cron fire-and-forget tras cron-cierre-sesiones
- **Resultados primera ejecución**: 17 agentes, 70 grupos, 1 anomalía real detectada (volumen_bajo), 986ms
- **Coste**: $0 (código puro, 0 LLM)
- **estado_agentes CHECK**: valores válidos son `idle` (no `activo`)

## Fase S-PROP — Propiocepción del Sistema (completada)
- **propiocepcion**: Edge Function ~280 líneas, 5 fases, $0 código puro. 7 queries paralelas → snapshot JSONB unificado → diff → decisiones inbox → guardar + limpiar
- **dashboard-api**: Edge Function ~200 líneas, 5 endpoints: `?q=estado|inbox|timeline|decidir|resumen`. `?q=resumen` es para panel del Chief
- **Tablas**: `estado_sistema` (snapshots con columnas desnormalizadas), `inbox_decisiones` (CHECK urgencia/categoria/estado)
- **Autonomía**: emergencias (>=5 errores + critico) → auto-disable + log en inbox
- **Score salud**: 1.0 base, penalizado: errores (-0.1/agente), disabled>5 (-0.05), errores 24h>5 (-0.1), coste>$0.50 (-0.05), mejoras>10 (-0.05)
- **Integración**: basal-cron fire-and-forget al inicio del pipeline (antes de lentes)
- **Primera snapshot**: 153 componentes, 58 agentes (50 idle, 8 disabled), salud 0.95, $0.27/día, 687ms
- **Dashboard HTML**: NO desplegado. Se integrará en interfaz del Chief
- **Coste**: $0 (código puro, 0 LLM)

## Fase 1.1 — Gateway API del Cerebro (completada)
- **gateway/index.ts**: ~370 líneas. Puerta única de entrada. Auth + manifest + rate limit + circuit breaker + routing + metering
- **4 tablas nuevas**: tenants, metering, capability_registry, tareas_async. Migración: `20260302060000_fase1_1_gateway.sql`
- **3 tenants**: consola (wildcard, sync, sin límite), exo-pilates (4 caps, async, 200/día), exo-fisio (4 caps, async, 200/día)
- **16 capabilities** (9 activas + 7 disabled futuras). 6 apuntan a orquestador-ias (mismo pipeline monolítico)
- **Auth**: X-API-Key header → lookup tenants → estado activo. NO JWT
- **Circuit breaker**: 3 fallos consecutivos → open (503). 30s cooldown → half-open → retry
- **Async mode**: Self-dispatch pattern (gateway se llama a sí mismo con _internal_process flag). Polling via GET ?request_id=
- **Metering**: JSONB con gateway_overhead_ms, input_length, circuit_state, edge_function, modo, etc.
- **Correcciones**: (1) índice parcial now() no IMMUTABLE, (2) gen_random_bytes sin pgcrypto → gen_random_uuid, (3) executeInBackground → self-dispatch
- **REST API funciona con service role key** (no con anon key — el problema era la key, no el endpoint)
- **Tests**: 10/10 PASS. E2E IAS via gateway: 98.1s, informe completo
- **Coste**: $0 (código puro)

## Fase 1.2 — Catálogo de Capacidades (completada)
- **Migración**: `20260302070000_fase1_2_catalogo_capacidades.sql`. Limpia 8 caps falsas, renombra ias_analisis→ias_completo, inserta 12 reales, 10 disabled futuras, actualiza manifests, semilla
- **12 capabilities reales**: 1 ias_completo, 5 diseño (rutas A/B/C/D/E), 5 observabilidad (GET ?q=), 1 system_snapshot
- **10 disabled futuras**: 3 IAS granulares (parseadores/lentes/calculador) + 7 originales
- **Tenants actualizados**: pilates 8 caps, fisio 4 caps, consola wildcard sin cambio
- **Patch gateway**: `executeCapability()` expandido: Ambassador pattern (GET), diseño route mapping (config.ruta→campos trigger), dashboard-api decidir (POST+query). Preserva 120s AbortController
- **Semilla**: `granularizar_ias_por_demanda` (auto_mejora, CR1). 3 condiciones: >=100 requests 30d + >70% parcial + 2+ tenants
- **Tests**: 10/10 PASS. GET caps 392-761ms, system_snapshot 1228ms, diseño Ruta A 117s, manifest auth OK
- **Coste**: $0

## Fase 1.3 — Metering y Coste (completada)
- **Migración**: `20260302080000_fase1_3_metering_coste.sql`. Tabla `metering_agregados` + ALTER tenants (alertas_config)
- **Propagación coste**: orquestador-ias y orquestador-diseno query `métricas` (coste_usd, tokens_in, tokens_out) y lo añaden a response
- **Gateway fallback**: Si result.cost_usd===0, query directa a métricas. Campo `_cost_source` para trazabilidad
- **Gateway nuevos endpoints**: `?q=consumo` (por tenant), `?q=consumo_global` (solo wildcard). Version 1.3
- **metering-cron**: Nueva Edge Function. Agrega diario, by_capability, telemetry, 3 alertas (coste/rate_limit/anomalía) → inbox_decisiones
- **Columnas métricas**: `coste_usd` (decimal), `tokens_in`, `tokens_out` — NO tokens_entrada/salida
- **inbox_decisiones schema real**: `titulo`, `descripcion`, `urgencia` (critica/alta/normal/baja), `categoria` (error/rendimiento/coste/capacidad/mejora/presupuesto), `origen_agente`, `datos_soporte`, `accion_propuesta` (NOT NULL), `contexto_simple` (NOT NULL)
- **executeCapability**: Ahora recibe `supabase` como primer parámetro (6→7 params)
- **Coste real**: IAS ~$0.10-0.12/llamada, proyectado ~$14.19/mes
- **Tests**: 9/9 PASS. 91 funciones, 45 migraciones

## Primitivas v2 — Prisma Semántico (7 de 7 COMPLETAS)
- **Concepto**: Mini-enjambres multi-ángulo. Dial 0.0-1.0 controla ángulos activos. 6 códigos semánticos
- **P1 Sustantivizar**: 8 ángulos. Coseidad/reificación. Tests: 9/9
- **P2 Sujeto-Predicado**: 8 ángulos. Agencia/responsabilidad. Discrimina 0.03→0.96. Tests: 6/8 Sonnet
- **P3 Adjetivar v2**: 12 ángulos (7 cualificación + 5 medición). Posicionamiento/rangos con invariantes. Tests: 12/13
- **P4 Adverbializar**: 12 ángulos (7 verbos de vida + 5 transversales). Modos de operar (implícito↔explícito). Tests: 4/12 (verificador rate-limited 24 paralelas)
- **P5 Preposicionar**: 8 ángulos. Relaciones/niveles lógicos (5 tipos: conducta→meta). Colapsos entre niveles. Tests: 7/12
- **P6 Conjuntar**: 8 ángulos (adicion, oposicion, alternativa, causalidad, condicion, temporalidad, concesion, ausencia_conexion). Estructura conectiva. Detecta falsas dicotomías, causalidades circulares, piezas sueltas
- **P7 Verbo**: 8 ángulos. Acción nuclear + 7 verbos de vida. Tests: **11/11 PASS**
- **Archivos**: 24 en `_shared/primitivas-v2/` + 7 Edge Functions + 7 tests = 38 archivos
- **8-ángulo fixes**: Verificador retry 1.5s/3s/5s (16 paralelas, menos presión)
- **12-ángulo fixes**: Verificador retry 2s/5s/8s, integrador retry 3× con 2s/4s (rate limiting tras 24 calls paralelas)
- **Bug fixes**: (1) `String(1.0)`→`toFixed(1)`, (2) verificador retry, (3) `system_prompt` campo separado
- **Edge Function pattern**: Clean (no createClient, SUPABASE_SERVICE_ROLE_KEY, CODIGOS_SEMANTICOS validation, no broken DB inserts)
- **Coste**: ~$0.01-0.03/Haiku (8 ángulos), ~$0.02-0.05/Haiku (12 ángulos)

## Fase A3 — Auditor de Presupuestos (completada)
- **auditor-presupuestos**: Edge Function ~290 líneas. Beer S4: detecta suposiciones no verificadas en arquitectura
- **Guard temporal**: 1 ejecución cada 30 días (query cola_mejoras origen='auditor'). Bypass con `manual_force`
- **6 detectores código puro**: D1 disponibilidad (puntos únicos fallo), D2 latencia (cascadas timeout), D3 capacidad (inventario), D4 conectividad (sin retry), D5 comportamiento (sin cron cierre), D6 modelo LLM (errores, sin circuit breaker)
- **1 Haiku**: Verbalización de hallazgos → propuestas en cola_mejoras (tipo='presupuesto', origen='auditor')
- **Migración**: `20260302010000_a3_auditor_presupuestos.sql`. ALTER CHECK tipo (+presupuesto), CREATE CHECK origen, ADD COLUMN contexto JSONB
- **cola_mejoras real**: Creada por migración `20260226050000` (no `20260227020000`). Columnas reales incluyen `componente`, `briefing_generado`, `sesion_diseño`, `implementada_en`
- **Integración**: basal-cron → guard mensual → fire-and-forget auditor-presupuestos
- **Primera ejecución**: 149 componentes, 60 hallazgos (53 D4_conectividad), 9.2s. llm-proxy = 51 dependientes
- **Coste**: ~$0.02/mes (1 Haiku/mes)

## Fase A6 — Confrontador de Posición entre Integradores (completada)
- **1 agente confrontador** capa 2 en chief_of_staff. Sync (await, 15s timeout) en Paso 5.5 entre N45 y verbalizador
- **5 detectores código puro**: D1 dirección opuesta N12↔N45, D2 dato contradice trade N12↔N3, D3 opción vs misión N3↔N45, D4 vacío asimétrico N12↔N3, D5 tensión no señalada
- **Si incoherencias**: Haiku clasifica como `contradiccion` o `tension`. Verbalizador recibe sección INCOHERENCIAS
- **Migración**: `20260302050000_a6_confrontador_integradores.sql`. 1 estado_agentes + 1 registro_arquitectura
- **Integración**: profundo-runner Paso 5.5 (sync), verbalizador extrae marca + sección prompt condicional
- **14 fixes vs briefing**: mismos patrones que A5 (system_prompt, modelo, mensajes, _shared imports, marcas schema, etc.)
- **Coste**: $0 si coherente, ~$0.001 si incoherencias. Total agentes chief: 20, total sistema: 62, componentes: 157

## Fase A5 — Completador Posiciones + Cruzador Dominios (completada)
- **2 agentes decoradores** capa 1 en chief_of_staff. Disparados fire-and-forget desde profundo-runner después del Paso 3 (alternativas)
- **completador-posiciones**: Polling espera alt-radical/incremental → clasifica 5 posiciones sintácticas → Haiku genera alternativas para huecos → dispara cruzador
- **cruzador-dominios**: Lee alternativas + completador → extrae verbos nucleares (7 verbos) → cruza con conocimiento_dominio (verificado=real) → Haiku verbaliza conexiones
- **Migración**: `20260302040000_a5_completador_cruzador.sql`. 2 estado_agentes + 2 registro_arquitectura
- **Integración**: profundo-runner Paso 3 → fire-and-forget completador. Cruzador se dispara desde completador
- **18 fixes vs briefing**: system→system_prompt, tier→modelo, prompt→mensajes, content→respuesta, tokens_in→tokens_entrada, limpiarJSON→_shared, registrarTelemetria→registrarMétrica, sesion_id/turno en marcas→eliminados, hallazgo NOT NULL→añadido, estado activo→idle, ON CONFLICT nombre→(enjambre_id,nombre), log_operaciones exitoso→error, +chequearSeñales, +conRetry, integración orquestador-chief→profundo-runner, +registro_arquitectura
- **Coste**: ~$0.002/ciclo (2 Haiku). Total agentes chief: 19, total sistema: 61, componentes: 156

## Fase A4 — Detector Patrones Longitudinales (semilla dormida, completada)
- **Fix infraestructura**: verificador-semillas añadido a basal-cron como fire-and-forget. Las 20 semillas ahora se evalúan automáticamente cada vez que basal-cron ejecuta
- **Migración**: `20260302030000_a4_detector_patrones.sql`. ALTER CHECK categoria (+observabilidad). INSERT semilla + registro_arquitectura (estado='dormido') + estado_agentes
- **Semilla**: `detector_patrones_longitudinales` (categoria: observabilidad, requiere CR1). 3 condiciones:
  - `snapshots_suficientes` ≥28 en 7d (actual: 2)
  - `baselines_14_dias` ≥1 agente distinto (actual: 19, cumplida)
  - `propiocepcion_estable_7d` ≥28 ejecuciones exitosas (actual: 2)
- **Auto-activación estimada**: ~8 marzo (condiciones) → ~15 marzo (7d estable + CR1)
- **detector-patrones/index.ts**: Creado en repo (~290 líneas), **NO desplegado**. Se desplegará al activar semilla
  - 5 detectores código puro: P1 tendencia monotónica, P2 ciclos periódicos, P3 acumulación sin resolver, P4 degradación baselines, P5 estabilidad diff
  - 1 Haiku solo para verbalizar hallazgos → propuestas en inbox_decisiones
  - Guard temporal: ≥6h entre ejecuciones (usa métricas propias, no cola_mejoras)
  - Imports SO: registrarMétrica, chequearSeñales, limpiarJSON
- **Adaptaciones vs briefing**: (1) ALTER CHECK categoria, (2) handlers en prefetchDatos (3 queries más), (3) system→system_prompt, (4) registrarMétrica en vez de insert directo, (5) tipos TS
- **Coste**: $0 sin hallazgos, ~$0.30/mes con hallazgos

## Fase A1 — Compresor de Memoria (completada)
- **turnos_episodicos**: Event sourcing de cada turno. Se borra post-compresión
- **compresor-memoria**: Haiku via llm-proxy. Extrae decisiones/datos/patrones → perfil_usuario + decisiones_chief. Dead letter queue
- **cron-cierre-sesiones**: Cierre automático inactivas >2h, pausas expiradas, dead letter retry (max 3). Invocado desde basal-cron
- **Comandos sesión**: `/cerrar` (compresión manual), `pausa hasta...` (max 48h), reactivación automática
- **9 puntos escritura episódica** en orquestador-chief (antes de cada return conversacional)
- **sesiones_chief**: +estado (abierta/pausada/comprimiendo/cerrada), +pausado_hasta, +ultimo_turno_at
- **Bug**: `supabase.from().insert().catch()` NO funciona (no es Promise real) → usar try-catch

## Patrones clave
- **limpiarJSON robusta**: Repara JSON truncado por max_tokens — ver [patterns.md](patterns.md)
- **Orquestador multi-ruta**: Un solo Edge Function con rutas A-E detectadas por body params
- **Override huecos**: Si usuario respondió >= 3 preguntas, forzar transición a "listo"
- **Primera persona implícita**: En español "tengo"/"quiero" implica sujeto (yo). No es hueco crítico.

## Decisiones CR1
- Jesús (CR1) aprueba todo manualmente
- Presupuesto: €200/mes
- Calidad > velocidad

## Preferencias del usuario
- "No diseñes, solo implementa lo que dice el documento"
- "Si ves algo que no cuadra, señálalo antes de ejecutar"
- Aprobación manual en cada paso (excepto bash/git/deploy → auto-aceptar)
- Idioma: español para comunicación, código en inglés



## motor-semantico/ARQUITECTURA_MECANISMOS_MULTI_MODELO.md

# ARQUITECTURA DE MECANISMOS MULTI-MODELO — Basada en Exp 4 completo

**Estado:** CR0 — Jesús valida
**Fecha:** 2026-03-12
**Fuente:** Exp 4 (mesa redonda) + Exp 4.1 (especializada) + Exp 4.2 (sintetizador) + Exp 4.3 (mente distribuida) + evaluación externa Claude

---

## 1. LOS 5 MECANISMOS Y QUÉ PRODUCE CADA UNO

### 1A. Evaluación individual en paralelo (Exp 4 R1)

**Qué es:** N modelos reciben el mismo input y evalúan independientemente.

**Produce:**
- Score por celda con varianza inter-evaluador medible
- Detección de sesgos: quién infla (+0.84 Qwen3), quién defla (-0.45 GPT-OSS)
- Correlaciones entre evaluadores (Sonnet↔Qwen3: 0.605, R1↔V3.2R: 0.642)
- Mapa de "lobos solitarios" (quién da 3+ cuando nadie más lo hace)

**No produce:** Conexiones, puntos ciegos, síntesis, convergencia.

**Datos:** Media global 1.71, solo 7/105 celdas con consenso mayoritario (≥6 dan 3+). Std medio 0.71-0.94 por output.

**Coste:** N llamadas paralelas (~12 modelos × 5 outputs = 60 llamadas). ~$0.50-1.00.

**Cuándo usar:** Screening rápido de calidad. Calibrar modelos nuevos. Seleccionar quién entra en mecanismos más caros. Es el termómetro, no el tratamiento.

---

### 1B. Mesa redonda con enriquecimiento (Exp 4 R2)

**Qué es:** Tras R1, cada modelo ve las evaluaciones de los demás y reevalúa.

**Produce:**
- Convergencia masiva: 7→70 celdas con consenso mayoritario (10x)
- 16 celdas emergentes (no existían en R1)
- Reducción de varianza

**No produce:** Conexiones cross-celda, hallazgos centrales, puntos ciegos.

**Datos:** Media 3.27 (vs 1.71 R1), 93/105 celdas 3+.

**Atención:** 77% de las convergencias van hacia donde Qwen3 ya apuntaba en R1 — efecto líder parcial, no solo convergencia ciega. Sonnet predice R2 mejor que nadie (ρ=0.656).

**Coste:** 2N llamadas (R1+R2). ~$1-2.

**Cuándo usar:** Evaluación fiable con consenso. Cuando necesitas UNA respuesta validada por múltiples perspectivas, no N opiniones dispersas.

---

### 1C. Mesa especializada (Exp 4.1)

**Qué es:** Misma mesa, pero cada modelo recibe prompt afinado a su zona fuerte.

**Produce:**
- +0.55 media en zona de foco (mejora significativa)
- -0.14 fuera de foco (deterioro leve)
- Delta global: +0.10 (7/12 modelos mejoran)
- Cambia la mesa mínima: V3.2-chat + V3.1 = 97.9% (vs Qwen3 + GPT-OSS = 94.6% con genérico)

**No produce:** Más que la mesa genérica en cobertura global (+2 celdas: 93→95).

**Modelos que mejoran con especialización:** V3.2-Reasoner (+0.50), R1 (+0.43), MiniMax (+0.28), V3.1 (+0.19), V3.2-chat (+0.16).

**Modelos que empeoran:** Kimi (-0.48), Opus (-0.40), Qwen3 (-0.31), GLM (-0.27). Los infladores genéricos pierden ventaja con prompt específico.

**Coste:** Igual que mesa genérica — solo cambian los prompts.

**Cuándo usar:** Siempre que uses mesa redonda. No hay razón para no especializar: mismo coste, mejor resultado en foco.

---

### 1D. Sintetizador (Exp 4.2)

**Qué es:** Un modelo recibe TODAS las evaluaciones de la mesa y produce output integrado.

**Produce:**
- Conexiones cross-lente (media 3.6/output con Cogito)
- Hallazgos centrales no-genéricos (5/5 con Cogito)
- Meta-patrones (media 3.0/output)
- Puntos ciegos residuales (media 2.6/output)
- 100% de celdas igualan max mecánico (no pierde nada)

**No produce:** Scores superiores al max mecánico (0 celdas por encima).

**Ranking sintetizadores:**

| # | Modelo | Outputs OK | Conexiones | Hallazgos | Tiempo |
|---|--------|-----------|------------|-----------|--------|
| 1 | **Cogito-671b** | 5/5 | 3.6/output | 5/5 no-genéricos | 47s |
| 2 | DeepSeek-R1 | 5/5 | 3.0/output | 5/5 no-genéricos | 55s |
| 3 | Qwen3-235b | 5/5 | 2.2/output | 3/5 no-genéricos | 137s |
| 4 | V3.2-chat | 5/5 | 2.0/output | 2/5 no-genéricos | 121s |
| ✗ | GLM-5 | 0/5 (parse fail) | — | — | — |
| ✗ | MiniMax M2.5 | 0/5 (parse fail) | — | — | — |

**Coste:** 1 llamada extra (~47s con Cogito). ~$0.05.

**Cuándo usar:** SIEMPRE como paso final después de cualquier mesa. Convierte datos (scores) en comprensión (conexiones causales). Es lo que un humano necesita para decidir. Coste marginal despreciable.

---

### 1E. Pizarra / Mente distribuida (Exp 4.3)

**Qué es:** Pizarra compartida donde N modelos contribuyen evidencias por turnos. Múltiples rondas hasta convergencia.

**Produce:**
- 425 conexiones entre celdas (exclusivo)
- 239 puntos ciegos detectados (exclusivo)
- 94/105 celdas 3+ (evaluación externa Claude) — cobertura equivalente a mesa redonda
- Contenido rico con capas de profundización: cada ronda añade ángulos

**No produce:** Scores más altos que la mesa redonda (3.06 vs 3.27 evaluación externa). El auto-tracking infla +0.93 puntos.

**Perfiles de modelos en la pizarra:**

| Modelo | Contribuciones | Conexiones | P.Ciegos | Perfil |
|--------|---------------|------------|----------|--------|
| GPT-OSS | 119 | 77 | 46 | Motor principal |
| MiniMax M2.5 | 75 | 55 | 45 | Segundo motor |
| Qwen3-235b | 63 | 48 | 25 | Tercer contribuidor |
| V3.2-chat | 56 | 52 | 28 | Conector fuerte |
| V3.1 | 52 | 45 | 22 | Contribuidor sólido |
| R1 | 44 | 30 | 12 | Contribuidor |
| V3.2-Reasoner | 42 | 28 | 14 | Contribuidor |
| Opus | 33 | 34 | 8 | Conector (caro) |
| Cogito | 31 | 29 | 22 | Detector de huecos |
| Kimi | 25 | 19 | 15 | Contribuidor menor |
| GLM-4.7 | 20 | 8 | 2 | Marginal |

**Convergencia:** 3/5 outputs convergieron en 4-5 rondas. 2/5 llegaron al máximo de rondas sin converger.

**Coste:** Alto. 10-11 modelos × 4-5 rondas = 40-55 llamadas por output. ~$2-5 por output.

**Cuándo usar:** Cuando necesitas PENSAR, no evaluar. Exploración profunda de un problema. Batch nocturno. Onboarding de dominio nuevo. Su valor está en las conexiones y puntos ciegos, no en los scores.

---

## 2. MAPA DE USO POR NECESIDAD

| Necesitas... | Mecanismo | Coste | Tiempo |
|---|---|---|---|
| Screening rápido de calidad | Individual paralelo (1A) | ~$0.50 | ~2min |
| Evaluación fiable con consenso | Mesa redonda R1+R2 (1B) | ~$1-2 | ~5min |
| Profundidad en área concreta | Mesa especializada (1C) | ~$1-2 | ~5min |
| Entender conexiones causales | Sintetizador Cogito (1D) | ~$0.05 extra | ~47s extra |
| Explorar problema en profundidad | Pizarra distribuida (1E) | ~$2-5 | ~30-60min |
| Saber qué modelos usar | Individual + análisis de sesgo | ~$0.50 | ~5min |

---

## 3. COMPOSICIONES POR TIER

### Tier 2 — Respuesta (5-15s, $0.01-0.05)

```
1 modelo: V3.2-chat (89.5% cobertura individual)
Sin mesa, sin evaluación. Respuesta directa.
```

### Tier 3 — Análisis (1-5min, $0.10-0.50)

```
Mesa especializada 1 ronda (sin R2):
  V3.2-chat + V3.1 + R1 (3 modelos, prompts especializados)
  = 100% cobertura
  
+ Cogito sintetiza (1 llamada extra, 47s)
  = Conexiones cross-lente + hallazgo central

Total: 4 llamadas. ~$0.30. ~3min.
```

### Tier 4 — Profundo (30-60min, $1-3)

```
PASO 1: Pizarra distribuida (7 modelos, ~5 rondas)
  GPT-OSS + MiniMax + Qwen3 + V3.2-chat + V3.1 + R1 + V3.2-Reasoner
  → Contenido rico: conexiones + puntos ciegos
  
PASO 2: Cogito sintetiza la pizarra
  → Hallazgo central + meta-patrones + puntos ciegos residuales

PASO 3: Panel evaluador externo (V3.2-chat + V3.1 + R1, prompts especializados)
  → Scores calibrados sin inflación del auto-tracking

Total: ~40-50 llamadas. ~$2-3. ~45min batch.
```

### Tier 5 — Cartografía (horas, $5-20)

```
PASO 1: Pizarra distribuida completa (11 modelos, hasta convergencia)
PASO 2: Mesa especializada R1+R2 como evaluación externa
PASO 3: Cogito sintetiza
PASO 4: Loop — detectar puntos ciegos residuales → nueva ronda de pizarra
PASO 5: Sintetizar convergencias cross-output

Total: ~100+ llamadas. ~$5-10. ~2-4h batch.
```

---

## 4. MODELOS POR ROL (DECISIONES CR0)

### Evaluadores (mesa de consenso)
- **V3.2-chat** — mejor evaluador individual especializado (89.5% solo, 3.02 media esp)
- **DeepSeek-V3.1** — segundo evaluador, complementario (2.99 media esp)
- **DeepSeek-R1** — tercer evaluador, completa cobertura a 100% (2.00 media esp)
- Estos 3 = mesa mínima para evaluación fiable

### Contribuidores de pizarra
- **GPT-OSS** — motor principal (119 contribuciones, el más productivo)
- **MiniMax M2.5** — segundo motor (75 contrib, fuerte en conexiones)
- **Qwen3-235b** — tercer contribuidor (63 contrib, buen detector)
- **V3.2-chat** — fuerte en conexiones (52 conexiones)
- **V3.1, R1, V3.2-Reasoner** — contribuidores sólidos
- ~~Opus~~ — prescindible (33 contrib, $75/M, 0 aportes únicos en Exp 4)
- ~~GLM-4.7~~ — marginal (20 contrib, 2 puntos ciegos)

### Sintetizador
- **Cogito-671b** — sin discusión. 3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s, barato.

### Descartados de pipelines automatizados
- **Opus** — 0 aportes únicos, $75/M, prescindible en toda evaluación. Se usa en chat ($0) cuando se necesite.
- **Sonnet** — 0 aportes únicos, prescindible. Predice R2 bien (ρ=0.656) pero caro para el valor que aporta.
- **Kimi-K2.5** — 0/5 en R2 de Exp 4.1, empeora con especialización (-0.48). Fuera.
- **GLM-4.7** — marginal en pizarra (20 contrib, 2 ciegos). No justifica el slot.

---

## 5. HALLAZGOS METODOLÓGICOS

### Auto-evaluación infla ~1 punto
La pizarra (auto-tracking) da media 3.99. Evaluación externa: 3.06. Delta: +0.93. Cualquier mecanismo donde los participantes se ponen nota necesita evaluación externa para ser fiable.

### La especialización de prompts redistribuye valor
No sube el total significativamente (+2 celdas) pero cambia QUIÉN es útil. Qwen3 pasa de "cerebro" a "contribuidor". V3.2-chat pasa a líder. La mesa mínima cambia por completo.

### Los infladores genéricos pierden ventaja con prompt específico
Qwen3 (-0.31), Kimi (-0.48), Opus (-0.40). Los modelos que parecían los mejores con prompt genérico caen cuando se les pide rigor en zona concreta.

### Sonnet no era mala referencia — era cara
Predice consenso R2 mejor que Qwen3 (ρ=0.656 vs 0.638). El problema no era calibración sino precio + ausencia de diversidad.

### El valor de la pizarra está en las conexiones, no en los scores
94/105 celdas 3+ (≈mesa redonda) + 425 conexiones + 239 puntos ciegos. La diferencia cualitativa es real, la cuantitativa no.

### GPT-OSS invierte su rol según mecanismo
En Exp 4 (evaluador): máximo deflactor (-0.45), esponja que absorbe de Qwen3.
En Exp 4.3 (pizarra): máximo contribuidor (119), motor principal.
El rol del modelo depende del mecanismo, no es fijo.

---

## 6. DATOS DE REFERENCIA

### Comparación agregada cross-experimento (evaluados externamente)

| Método | Media | 3+/105 | Conexiones | Evaluador |
|--------|-------|--------|------------|-----------|
| Exp 4 R1 max mecánico | 2.89 | 77 | 0 | 12 modelos |
| Exp 4 R2 mesa redonda | 3.27 | 93 | 0 | 12 modelos post-R2 |
| Exp 4.1 mesa especializada | ~3.30 | 95 | 0 | 12 modelos con prompts foco |
| Exp 4.3 mente distribuida (ext) | 3.06 | 94 | 425 | Claude externo |
| Exp 4.3 auto-tracking | 3.99 | 105 | 425 | Auto (inflado +0.93) |

### Mesa mínima por mecanismo

| Mecanismo | Mesa mínima | Cobertura |
|-----------|------------|-----------|
| Genérico (Exp 4) | Qwen3 + GPT-OSS | 94.6% (88/93) |
| Especializado (Exp 4.1) | V3.2-chat + V3.1 | 97.9% (93/95) |
| Especializado completa | V3.2-chat + V3.1 + R1 | 100% (95/95) |
| Pizarra mínima | GPT-OSS + MiniMax + Qwen3 | 40% (bajo sin más modelos) |
| Pizarra recomendada | 7 modelos (GPT-OSS→Cogito) | 76% contribuciones |

---

## 7. CAPA DE INFRAESTRUCTURA: PROXY MULTI-PROVIDER

### Problema

Los mecanismos de §1-§3 usan 10+ modelos de 3+ proveedores (Together, DeepSeek API, OpenRouter). Cada proveedor tiene su API key, formato, pricing y disponibilidad. Gestionar N proveedores directamente es frágil: si uno cae o sube precios, hay que tocar código.

### Solución: Router unificado

Un único punto de entrada que abstrae los proveedores. Dos opciones viables:

**Opción A — Hugging Face Inference Providers (router hosted)**

HF no es un proveedor de inferencia — es un router que da acceso a Together, Fireworks, Sambanova, Replicate, Nebius, Novita y otros con una sola API y un solo token.

- 1 API key (HF token) → acceso a todos los providers integrados
- Sin markup: HF pasa el coste del provider directo
- Cambiar provider = cambiar 1 parámetro, no código
- Catálogo más grande que cualquier provider solo
- PRO $9/mes incluye $2 créditos/mes de inferencia
- Billing unificado: 1 factura en vez de N

```python
# Ejemplo: mismo modelo, cambiar provider con 1 línea
from huggingface_hub import InferenceClient
client = InferenceClient(token="hf_xxx")

# Via Together
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    provider="together-ai",
    messages=[...]
)

# Via Fireworks (si Together cae)
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    provider="fireworks-ai",
    messages=[...]
)
```

**Opción B — LiteLLM (proxy self-hosted)**

Proxy open-source que unifica 100+ providers con formato OpenAI-compatible. Se puede usar sobre HF o directamente sobre los providers.

- Self-hosted: control total, sin dependencia de HF
- Formato OpenAI estándar para todos los providers
- Fallback automático: si provider A falla → provider B
- Load balancing entre providers
- Logging centralizado de tokens, latencia, coste

```yaml
# litellm config
model_list:
  - model_name: deepseek-v3.2
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY
  - model_name: deepseek-v3.2
    litellm_params:
      model: together_ai/deepseek-ai/DeepSeek-V3-0324
      api_key: os.environ/TOGETHER_API_KEY
  # Fallback automático: si DeepSeek directo falla, usa Together
```

### Decisión CR0: Opción mixta

```
CAPA 1 — HF como router por defecto
  Ventaja: 1 token, 1 billing, catálogo completo
  Se usa para: todos los modelos disponibles vía HF providers

CAPA 2 — API directa como fallback
  Para: modelos no disponibles vía HF (DeepSeek API directo, etc.)
  O cuando: HF routing añade latencia inaceptable

CAPA 3 — LiteLLM como proxy unificador (futuro)
  Cuando: el volumen justifique self-hosting
  Ventaja: fallback automático, load balancing, logging
```

### Mapa provider → modelos (marzo 2026)

| Modelo | Provider principal | Fallback | model_id HF |
|--------|-------------------|----------|-------------|
| DeepSeek V3.2 | DeepSeek API | Together | `deepseek-ai/DeepSeek-V3-0324` |
| DeepSeek V3.2 Reasoner | DeepSeek API | — | `deepseek-ai/DeepSeek-R1` |
| DeepSeek R1 | Together | DeepSeek API | `deepseek-ai/DeepSeek-R1` |
| Qwen3-235B | Together | Fireworks | `Qwen/Qwen3-235B-A22B` |
| Qwen3-Coder 480B | Together | — | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` |
| GPT-OSS 120B | Together | — | `openai/gpt-oss-120b` |
| Cogito 671B | Together | — | `deepcogito/cogito-v2-preview-deepseek-671b` |
| MiniMax M2.5 | Together | — | `MiniMaxAI/MiniMax-M2.5` |
| Kimi-Dev 72B | Together | — | `moonshotai/Kimi-Dev-72B` |
| MiMo-V2-Flash | Together | — | `xiaomi/MiMo-V2-Flash` |
| GLM-5 | Together | — | `zai-org/GLM-5` |

**NOTA:** Verificar disponibilidad real de cada model_id antes de cada experimento. Los providers cambian catálogo sin aviso.

### Principios de routing

1. **Un solo punto de cambio.** Si un provider cae, se cambia en config sin tocar lógica de negocio. (Principio 25: OS-first, sin dependencia de proveedor.)
2. **Prioridad: API directa del fabricante > Together > otros.** DeepSeek directo es más barato y rápido que DeepSeek vía Together.
3. **Fallback silencioso.** Si el primary falla tras 2 retries, el proxy cambia a fallback sin intervención.
4. **Logging por provider.** Cada llamada registra: modelo, provider, tokens, latencia, coste. Esto alimenta decisiones de routing futuras.
5. **No lock-in.** Nunca usar features propietarias de un provider que no existan en otros. El formato es siempre OpenAI-compatible.

---

*Generado a partir de: exp4_mesa_redonda_report.json, exp4_1_comparison_report.json, exp4_2_sintetizador_report.json, exp4_3_mente_distribuida_report.json, exp4_3_evaluacion_externa_claude.json, ANALISIS_PROFUNDO_EXP4_MESA_REDONDA.md*



## motor-semantico/MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md

# MAPA DE MODELOS OS PARA OMNI-MIND — Marzo 2026

**Estado:** CR0 — Jesús valida
**Fecha:** 2026-03-12
**Fuente:** Onyx Leaderboard, benchmarks oficiales, resultados Exp 4, búsqueda HuggingFace

---

## LEADERBOARD GENERAL (febrero-marzo 2026)

### Tier S — Frontier OS (compiten con GPT-5/Claude Opus)
| Modelo | Params (total/activos) | Coding | Reasoning | Chat Arena | Licencia |
|--------|----------------------|--------|-----------|------------|----------|
| GLM-5 | 744B / 40B | SWE 77.8 | AIME 95.7 | #1 (1451) | Open |
| Kimi K2.5 | 1T / 32B | HumanEval 99.0 | AIME 96.1 | #2 (1447) | MIT mod |
| MiniMax M2.5 | 230B / 10B | SWE 80.2 | AIME 89.3 | 1421 | Open |
| DeepSeek V3.2 | 685B / 37B | LiveCode 90% | AIME 89.3 | 1421 | MIT |
| Step-3.5-Flash | 196B | LiveCode 86.4 | AIME 97.3 | — | — |
| Qwen 3.5 | 397B | SWE 76.4 | GPQA 88.4 | 1401 | Apache 2.0 |

### Tier A — Excelentes
| Modelo | Params | Coding | Reasoning | Notas |
|--------|--------|--------|-----------|-------|
| GLM-4.7 | 355B / 32B | HumanEval 94.2, LiveCode 84.9 | AIME 95.7 | Mejor coding puro |
| MiMo-V2-Flash | 309B / 15B | SWE superior a V3.2 | AIME 94.1 | Ultra-eficiente, $0.10/M in |
| DeepSeek R1 | 671B | — | AIME 96.7 | Reasoning puro |
| Qwen3-235B | 235B / 22B | LiveCode 80.6 | GPQA 83.7 | Generalista, 262K ctx |

### Tier B — Producción sólida
| Modelo | Params | Notas |
|--------|--------|-------|
| GPT-OSS 120B | 117B / 5.1B | Corre en 1 GPU H100. Barato ($0.60/M). |
| Mistral Large | 675B | HumanEval 92.0, LiveCode 82.8 |
| Nemotron Ultra 253B | 253B | GPQA 76.0, IFEval 89.5 |
| Nemotron Super 49B | 49B | MATH-500 97.4 (iguala R1) |
| Step3 | 316B | — |

### Tier C — Útiles en nicho
| Modelo | Notas |
|--------|-------|
| GPT-OSS 20B | Ultra-barato ($0.20/M). Fontanería. |
| Llama 4 Maverick | 400B/17B. 1M ctx. Multimodal. 8 meses viejo. |
| Gemma 3 27B | Edge deployment. |
| Nemotron Nano 30B | 1M ctx, 30B params. Edge. |

### Coding especialistas (no en leaderboard general)
| Modelo | Benchmark | Notas |
|--------|-----------|-------|
| Qwen3-Coder 480B | SOTA agentic coding | 256K ctx, diseñado para repo-scale |
| Qwen3-Coder-Next 80B | Eficiente | 3B activos, corre en 1 RTX 4090 |
| Kimi-Dev 72B | #1 SWE-bench patches | Especialista en patching real |

---

## MODELOS QUE NO TENÍAMOS EN EL RADAR

### 1. Kimi K2.5 (Moonshot AI) — NUEVO TIER S
- **1T params, 32B activos.** HumanEval 99.0 (el más alto de todos). MMLU 92.0. IFEval 94.0.
- **Agent Swarm:** ejecuta hasta 100 sub-agentes en paralelo. 200-300 tool calls secuenciales.
- **Thinking mode** con cadenas de razonamiento transparentes.
- **Heavy Mode:** 8 paths de razonamiento en paralelo, selecciona mejor respuesta.
- **Licencia MIT modificada** (atribución si >100M MAU o >$20M/mes).
- **Disponible en:** Together, Fireworks, OpenRouter.
- **Para OMNI-MIND:** Candidato fuerte para pizarra distribuida (agent swarm nativo), evaluador (IFEval 94.0), y razonamiento profundo.

### 2. Step-3.5-Flash (StepFun) — NUEVA ENTRADA TIER S
- **196B params.** AIME 97.3 (el más alto del leaderboard). LiveCode 86.4.
- Más pequeño que sus pares Tier S pero con rendimiento de frontier.
- **Para OMNI-MIND:** Candidato para Debugger (razonamiento matemático extremo) y evaluador donde la precisión lógica importa.

### 3. Qwen 3.5 (Alibaba) — NUEVA ENTRADA TIER S
- **397B params.** GPQA Diamond 88.4 (el más alto). IFEval 92.6. SWE 76.4.
- La mejor instrucción-siguiendo del leaderboard.
- Apache 2.0 — la licencia más permisiva de Tier S.
- **Para OMNI-MIND:** Candidato para evaluador especializado (instrucción-siguiendo + razonamiento científico). Reemplazaría a Qwen3-235B en mesa de evaluación.

### 4. MiMo-V2-Flash (Xiaomi) — YA EN RADAR PERO SUBESTIMADO
- **309B / 15B activos.** Supera a DeepSeek V3.2 y Kimi K2 en SWE-bench con 1/2-1/3 de params.
- **$0.10/M input, $0.30/M output.** El más barato de Tier A por un factor de 10x.
- 150 tok/s output.
- **Para OMNI-MIND:** El modelo que debería estar en CADA tier como opción barata. Tier 2 solo, Tier 3 como tester, Tier 4 como contribuidor de pizarra.

### 5. Nemotron Super 49B (NVIDIA) — NUEVA ENTRADA
- **49B params.** MATH-500 97.4 (iguala DeepSeek R1). 1M ctx.
- Increíblemente eficiente para su tamaño.
- **Para OMNI-MIND:** Candidato para cálculos y validación numérica dentro de la Matriz. Barato + preciso en math.

### 6. Kimi-Dev 72B (Moonshot) — YA DETECTADO EN EXP 5
- **#1 SWE-bench** para patching real de código.
- 72B params — manejable.
- **Para OMNI-MIND:** El mejor Revisor/Debugger de código. Ya en Exp 5 Config A como E4.

---

## MAPA POR ROL EN OMNI-MIND

### A) MOTOR COGNITIVO (análisis, evaluación, síntesis de la Matriz 3L×7F)

| Rol | Modelo recomendado | Alternativa | Por qué |
|-----|-------------------|-------------|---------|
| **Evaluador principal** | DeepSeek V3.2 | Qwen 3.5 | V3.2: Exp 4.1 lo validó como líder de mesa especializada. Qwen 3.5: IFEval 92.6 (mejor instrucción-siguiendo) |
| **Segundo evaluador** | DeepSeek V3.1 | GLM-4.7 | V3.1: complementario a V3.2, cobertura 100% con V3.2-chat en Exp 4.1 |
| **Tercer evaluador** | DeepSeek R1 | Kimi K2.5 | R1: completa cobertura en Exp 4.1. K2.5: IFEval 94.0, potencialmente mejor |
| **Sintetizador** | Cogito 671B | — | Exp 4.2: #1 sin discusión. 3.6 conexiones/output, 47s |
| **Contribuidor pizarra #1** | GPT-OSS 120B | MiMo-V2-Flash | GPT-OSS: 119 contrib en Exp 4.3. MiMo: más barato, posiblemente tan productivo |
| **Contribuidor pizarra #2** | MiniMax M2.5 | Kimi K2.5 | MiniMax: 75 contrib en 4.3, SWE 80.2%. K2.5: agent swarm nativo |
| **Contribuidor barato** | MiMo-V2-Flash | GPT-OSS 20B | $0.10/M input. Para llenar volumen en pizarra sin coste |
| **Razonador profundo** | DeepSeek V3.2 Reasoner | Step-3.5-Flash | Para debug lógico y root cause en la Matriz |

### B) ENJAMBRE DE CÓDIGO (implementar, testear, debugar, desplegar)

| Rol | Modelo recomendado | Alternativa | Por qué |
|-----|-------------------|-------------|---------|
| **Arquitecto** | DeepSeek V3.2 | GLM-5 | V3.2: interfaces limpias. GLM-5: systems engineering, más caro |
| **Implementador** | Qwen3-Coder 480B | Kimi K2.5 | SOTA agentic coding, 256K ctx para repo-scale |
| **Tester** | MiniMax M2.5 | MiMo-V2-Flash | SWE-bench 80.2%, mentalidad adversarial. MiMo: ultra-barato |
| **Debugger R1** | DeepSeek V3.2 Reasoner | Step-3.5-Flash | Traza lógica paso a paso, root cause |
| **Debugger R2** | Cogito 671B | Kimi-Dev 72B | Perspectiva diferente. Kimi-Dev: #1 en patching real |
| **Revisor** | GLM-5 | Qwen 3.5 | Systems engineering, pensamiento sistémico. Qwen 3.5: IFEval top |
| **Optimizador** | Qwen3-235B Instruct | GPT-OSS 120B | Barato, práctico, generalista |
| **Generador de tests (bulk)** | MiMo-V2-Flash | GPT-OSS 120B | Ultra-barato para generar muchos tests |

---

## MODELOS A INVESTIGAR (no probados aún)

| Modelo | Por qué | Riesgo |
|--------|---------|--------|
| **Kimi K2.5** | Agent swarm nativo, IFEval 94.0, HumanEval 99.0 | Kimi K2 (versión anterior) fue INERTE en Exp 4 R2 (0/5). K2.5 podría ser diferente |
| **Qwen 3.5** | GPQA 88.4, IFEval 92.6, Apache 2.0 | Nuevo, sin datos empíricos nuestros |
| **Step-3.5-Flash** | AIME 97.3, LiveCode 86.4, 196B | No sabemos disponibilidad en Together/HF |
| **MiMo-V2-Flash** | $0.10/M, supera V3.2 en SWE-bench | Nuevo, sin datos empíricos nuestros |
| **Nemotron Super 49B** | MATH-500 97.4 en 49B params | Nicho: solo math/lógica |

---

## PROVIDERS VÍA HUGGING FACE (21 integrados)

```
black-forest-labs, cerebras, clarifai, cohere, fal-ai, featherless-ai, 
fireworks-ai, groq, hf-inference, hyperbolic, nebius, novita, nscale, 
nvidia, openai, ovhcloud, publicai, replicate, sambanova, scaleway, 
together, wavespeed, zai-org
```

**Los que importan para OMNI-MIND:**
- **Together:** mayor catálogo de modelos OS (Qwen, GPT-OSS, MiniMax, Cogito, MiMo, GLM, Llama)
- **DeepSeek API directo:** más barato para V3.2 y Reasoner que vía Together
- **Fireworks:** fallback rápido, buena latencia, DeepSeek R1 disponible
- **Groq:** ultra-rápido para modelos pequeños (Llama 70B en ms)
- **Sambanova:** algunos modelos gratis
- **zai-org:** GLM-5 directo de Zhipu

---

## DECISIONES PENDIENTES (CR0)

1. **¿Probar Kimi K2.5 en Exp 4 bis?** Agent swarm + IFEval 94.0 lo hacen candidato a reemplazar varios modelos en pizarra. Pero Kimi K2 (anterior) fracasó en R2.

2. **¿Probar MiMo-V2-Flash como sustituto barato en TODOS los tiers?** A $0.10/M podría hacer Tier 2 prácticamente gratis y Tier 3 a $0.05.

3. **¿Probar Qwen 3.5 como evaluador?** IFEval 92.6 sugiere que podría ser mejor que V3.2-chat para instrucción-siguiendo en evaluación.

4. **¿Incorporar Step-3.5-Flash como debugger?** AIME 97.3 es el math score más alto. Para validación numérica dentro de la Matriz.

5. **¿Hacer un Exp 1 bis con los 6 modelos nuevos?** Kimi K2.5, Qwen 3.5, Step-3.5-Flash, MiMo-V2-Flash, Nemotron Super 49B, Kimi-Dev 72B — evaluarlos en las mismas 5 tareas del Exp 1 original para tener datos comparables.

---

*Fuentes: Onyx Open LLM Leaderboard (feb 2026), VERTU leaderboard analysis, BentoML guide, Clarifai reasoning models, DataCamp Kimi K2 guide, HuggingFace Inference Providers docs, resultados empíricos Exp 4/4.1/4.2/4.3*



## motor-semantico/ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md

# ACTUALIZACIÓN DOCUMENTO MAESTRO — Principio 31 + Arquitectura de Tiers

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-11
**Origen:** Sesión multi-modelo Exp 4 + diseño de enjambres

---

## Añadir a §12 PRINCIPIOS DE DISEÑO

[...truncado a 0K chars...]


## motor-semantico/ACTUALIZACION_MAESTRO_SESION_11_MAR.md

# ACTUALIZACIÓN DOCUMENTO MAESTRO — Sesiones 10-mar noche + 11-mar

[...truncado a 0K chars...]
