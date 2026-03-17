# OMNI-MIND — CONTEXTO COMPLETO


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

### Modelo conceptual ✅
- [x] Prompt del agente = red de preguntas
- [x] Motores = fábrica de la Matriz
- [x] Álgebra = compilador de prompts
- [x] 8 operaciones = gramática de preguntas
- [x] 3 niveles estabilidad: L0/L1/L2
- [x] Heurístico macro + probabilístico gradual
- [x] Dos sistemas: Motor vN (hacia fuera) + Gestor (hacia dentro)
- [x] Multi-modelo OS como dimensión algebraica
- [x] Gestor como compilador central para todos los consumidores
- [x] Stack OS-first

### Fase D: Motor vN MVP 🔄 EN CURSO
- [x] Multi-modelo OS validado (6 modelos ejecutados + Claude referencia)
- [x] 3 modelos OS superan a Claude: V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79)
- [x] R1 cubre 20/21 celdas — mayor cobertura de todos los modelos
- [x] Asignación modelo→celda empírica: V3.1 domina 7 celdas, R1 domina 7, GPT-OSS domina 4
- [x] Rúbrica de profundidad diseñada (4 niveles × 21 celdas)
- [x] Protocolo exploración 5 tiers diseñado
- [x] Evaluaciones cobertura completas (6 modelos + Claude, Tabla 3 = primer programa compilado)
- [ ] Pipeline end-to-end en fly.io
- [ ] Capa 0 (detector huecos) funcional
- [ ] Campo de gradientes sobre input
- [ ] Router por gradiente (modelo OS + fallback Sonnet)
- [ ] Compositor con 13 reglas
- [ ] Red de preguntas como prompt del agente
- [ ] Verificación de cierre de gaps
- [ ] 4 modos funcionando
- [ ] Test E2E con 3 casos de cartografía
- [ ] Telemetría en DB

### Gestor de la Matriz ⬜ DISEÑADO, POR IMPLEMENTAR
- [x] Arquitectura dos sistemas (Motor hacia fuera / Gestor hacia dentro)
- [x] Feedback loop diseñado (datapoints efectividad + vista materializada)
- [x] 3 mecanismos de aprendizaje (selección natural, asignación modelo→celda, complementariedad)
- [x] Pipeline del Gestor definido (7 pasos)
- [x] Compilación de programas por consumidor diseñada
- [x] Stack OS-first decidido
- [ ] Implementación tabla datapoints_efectividad
- [ ] Implementación vista materializada
- [ ] Orquestador OS (Qwen 235B / Maverick) funcional
- [ ] Test evaluador OS vs Sonnet (correlación >0.85)
- [ ] Compilador de programas por consumidor funcional

### Migración OS Sistema Nervioso ⬜ DISEÑADO, POR IMPLEMENTAR
- [x] Auditoría completa: ~53 agentes LLM clasificados (🟢/🟡/🔴)
- [x] Mecanismo: llm-proxy multi-provider (un solo punto de cambio)
- [x] Chief of Staff marcado como DEPRECADO (Motor v3.3 lo reemplaza)
- [ ] Fase 1: migrar ~30 agentes 🟢 (primitivas, parseadores, mejora continua, lentes)
- [ ] Fase 2: testear ~12 agentes 🟡 (correladores, diseñadores, prescriptor)
- [ ] Fase 3: evaluar 2 verbalizadores 🔴 (IAS, Diseño) con OS

### Experimentos en curso 🔄
- [x] Experimento multi-modelo original: 6 OS + Claude completado
- [x] Qwen3 235B Thinking: ejecutado, pendiente evaluación
- [x] Kimi K2.5: ejecutado, pendiente evaluación
- [ ] Cogito v2.1 671B: en ejecución
- [ ] DeepSeek V3.2 chat + reasoner: pendiente (necesita API key)
- [ ] Evaluación cobertura matricial de los 4 nuevos modelos
- [ ] Test coding agéntico V3.2 (Parte B del Experimento 1)
- [ ] Experimento 2: Cogito como cerebro profundo (evaluador, orquestador, Chief, verbalizador)

### Motor de Auto-Mejora + Fábrica de Exocortex ⬜ DISEÑADO
- [x] Enjambre de código diseñado (V3.2+Qwen Coder+Cogito+V3.1)
- [x] 3 niveles de auto-mejora definidos (fontanería/arquitectural/auto-evolución)
- [x] Fábrica de Exocortex diseñada (Gestor→Enjambre→Staging→CR1→Prod)
- [x] Infraestructura existente: cola_mejoras, implementador autónomo, regresión, deploy, propiocepción
- [ ] Validar V3.2 como coder agéntico (Experimento 1 Parte B)
- [ ] Validar Qwen3 Coder 480B como generador de código
- [ ] Integrar enjambre de código en pipeline de auto-mejora
- [ ] Primer exocortex fabricado por el sistema (Pilates — estudio de Jesús)
- [ ] Segundo exocortex (Fisioterapia — clínica de la mujer de Jesús)

### Fase E: Exocortex funcional ⬜ DESPUÉS
- [ ] Exocortex Pilates usa Matriz via Gestor para conversar
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

### Reactor v4: Observación de Datos Reales ⬜ CON PRIMER EXOCORTEX
- [ ] Telemetría de exocortex captura datos de operación del negocio
- [ ] Mapeo automático datos→celdas de la Matriz (Gestor)
- [ ] Generación de preguntas desde gaps observados
- [ ] Validación: preguntas del Reactor v4 cierran gaps que v1-v3 no cubren
- [ ] Prompts vivos: agentes se actualizan cuando el Gestor recompila
- [ ] Transferencia cross-dominio: pregunta de Pilates aplica a Fisio
- [ ] Flywheel: segundo piloto recibe preguntas del primero

### Pilotos reales ⬜ OLA 2
- [ ] Piloto 1: Exocortex Pilates conectado a datos reales del estudio de Jesús
- [ ] Piloto 2: Exocortex Fisioterapia conectado a datos reales de la clínica
- [ ] Validar: agentes detectan cosas que los dueños no veían
- [ ] Validar: transferencia cross-dominio Pilates↔Fisio funciona
- [ ] Validar: prompts evolucionan cuando el negocio cambia
- [ ] Recopilar datos para presentar caso real al amigo informático
- [ ] Ola 4: integrar con software de gestión del amigo, escalar a sus clientes

---

## 11. ROADMAP — ORDEN DE IMPLEMENTACIÓN

### Ola 1 — Ahora (paralelo)
- **Gestor de la Matriz** — tabla de efectividad + vista materializada + compilador de programas
  - Se construye PRIMERO para que cada consumidor nuevo se enchufe desde el día uno
  - Asignación modelo→celda empírica YA DISPONIBLE (Tabla 3 del coverage report)
- **Motor vN MVP en fly.io** — pipeline end-to-end que USA la Matriz via Gestor
- ~~Completar multi-modelo~~ ✅ 6 modelos evaluados. V3.1/R1/GPT-OSS top 3.
- **Migración OS Fase 1** — llm-proxy multi-provider + migrar ~30 agentes 🟢 (primitivas, parseadores, lentes, mejora continua)
- **Reactor v3 conceptual** — poblar Matriz con preguntas desde fundamentos teóricos (~$10-18)

### Ola 2 — Motor funcional + primeros pilotos reales
- Test evaluador OS vs Sonnet (objetivo: correlación >0.85 → migrar a OS)
- **Migración OS Fase 2** — testear ~12 agentes 🟡 con OS vs Anthropic en 10 inputs reales
- **Integrar enjambre de código** en pipeline de auto-mejora (V3.2+Qwen Coder+Cogito+V3.1)
- **PILOTO 1: Exocortex Pilates** (estudio de Jesús) — primer consumidor real del Gestor
  - Conectar telemetría a datos reales del estudio (reservas, clientes, sesiones)
  - Reactor v4 observa operaciones reales
  - Agentes con prompts compilados por el Gestor
  - Medir: ¿los agentes detectan cosas que Jesús no veía?
- **PILOTO 2: Exocortex Fisioterapia** (clínica de la mujer de Jesús) — segundo consumidor
  - Segundo dominio diferente: valida transferencia cross-dominio
  - ¿Las preguntas de Pilates sobre gestión de agenda aplican a fisio?
  - ¿Las preguntas de fisio sobre pacientes crónicos aplican a Pilates?
- Integrar preguntas nivel 2-3 de manuales (Fase B1 abducción)

### Ola 3 — Retroalimentación + autonomía
- Datos reales de ambos pilotos refinan la Matriz via Gestor (feedback transversal)
- **Reactor v4 activo** — telemetría genera preguntas desde datos reales de operación
- **Flywheel validado** — Pilates y Fisio se enriquecen mutuamente via la Matriz
- **Prompts vivos** — los agentes evolucionan con el negocio sin intervención manual
- **Migración OS Fase 3** — evaluar verbalizadores con OS. Si pasan → stack 100% OS
- **Auto-mejora nivel 2 activa** — el sistema propone + implementa mejoras arquitecturales, CR1 aprueba
- Reactor v2 con documentos técnicos
- Meta-motor con datos reales
- Modelos ligeros re-entrenados con datos de producción
- **Semillas dormidas se activan** — auto-evolución con enjambre de código

### Ola 4 — Escala: caso de negocio real con terceros
- **Con datos reales de Piloto 1 y 2**, presentar resultados al amigo informático
  - Demostrar: el sistema detectó X gaps reales, generó Y preguntas útiles, ahorró Z horas
  - Demostrar: transferencia cross-dominio funcionó entre Pilates y Fisio
  - Demostrar: prompts evolucionaron solos cuando el negocio cambió
- **Integración con software de gestión del amigo**
  - Capa de telemetría que lee datos del software existente via API
  - Agentes V3.2 inyectados en cada módulo con prompt compilado por el Gestor
  - Reactor v4 observa datos de clientes del amigo
- **Fábrica de Exocortex** para generar conectores por tipo de software
  - Enjambre de código genera conector nuevo por cada software diferente
  - Cada negocio conectado alimenta la Matriz central
- **Modelo de negocio**: capa inteligente a €50-200/mes por negocio, coste ~$2-5/mes en tokens, margen >90%

---

## 12. PRINCIPIOS DE DISEÑO

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es intercambiable. La Matriz es permanente. Validado empíricamente: 3 modelos OS superan a Claude operando bajo las mismas preguntas.
2. **Percibir antes de razonar.** Campo de gradientes primero. Sin saber qué funciones están débiles, el routing es ciego.
3. **Cada modelo hace lo que mejor sabe.** LLMs para generar. Embeddings para buscar. Grafos para optimizar. Código para calcular.
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
18. **Volumen barato antes que calidad cara.** Modelo OS ejecuta masivamente. Premium solo evalúa (y se reemplaza cuando OS lo alcance). Los datos mandan.
19. **El protocolo se entrena a sí mismo.** El enjambre meta-protocolo optimiza la exploración con datos, no con intuición.
20. **Robustez > rendimiento pico.** Preguntas que cierran gaps con modelo débil son más valiosas que las que solo funcionan con modelo fuerte.
21. **Modelos diferentes cubren celdas diferentes.** La diversidad de modelos es una dimensión algebraica más. Dato empírico: V3.1 domina Frontera (2.70), GPT-OSS domina Depurar (2.52), R1 domina Continuidad. Ningún modelo es el mejor en todo — el enjambre siempre gana.
22. **Dos loops, dos cadencias.** Motor vN (minutos, hacia fuera, ejecuta). Gestor de la Matriz (horas/días, hacia dentro, optimiza). No mezclar.
23. **El Gestor compila, los consumidores ejecutan.** Ningún consumidor (Motor, Exocortex, Chief of Staff) selecciona preguntas por su cuenta. Todos reciben programas compilados del Gestor.
24. **Conocimiento transversal > siloado.** Lo que Pilates descubre sobre dolor lumbar puede aplicar a Clínica si el patrón de gaps es similar. El Gestor lo detecta.
25. **OS-first.** El objetivo es stack 100% open source. Dependencia de proveedor premium = fragilidad. Se mide, no se asume.
26. **Si el usuario no lo lee, migra a OS.** Trabajo interno (clasificación, detección, extracción, correlación) no necesita modelo premium. Solo los verbalizadores de cara al usuario justifican premium — y esos también se testean.
27. **El sistema se mejora a sí mismo.** El enjambre de código (V3.2+Qwen Coder+Cogito+V3.1) implementa mejoras detectadas por el Gestor. Jesús aprueba (CR1), no implementa.
28. **El sistema fabrica sus propios hijos.** Cada exocortex nuevo se diseña, implementa y despliega por el enjambre de código. Cada hijo alimenta la Matriz central. El conocimiento crece con cada vertical.
29. **Cada cliente hace al sistema mejor para todos los demás.** El Reactor v4 genera preguntas desde datos reales de operación. Lo que un restaurante enseña sobre proveedores aplica a una clínica. Las preguntas tienen coordenadas en la Matriz — la transferencia cross-dominio es automática.
30. **Come tu propia comida primero.** Pilotar con negocios propios (Pilates, Fisioterapia) antes de vender a terceros. Con datos reales, no con teoría. Si no funciona para ti, no funciona para nadie.

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
| MULTI_MODEL_COVERAGE_REPORT.md | Resultados completos multi-modelo: 6 OS + Claude, Tabla 3 = asignación modelo→celda | Fuente datos |
| CONTEXTO_SISTEMA.md | Estado de implementación Supabase | L2 (se depreca) |
| MEMORY.md | Estado operativo del sistema nervioso | L2 (operativo) |

**Documentos que este reemplaza (no borrar, mantener como histórico):**
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md
- DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md
- SISTEMA_COGNITIVO_OMNI_MIND_v2.md
- ACTUALIZACION_DISENO_V2_SECCIONES_20_22.md

---

**FIN DOCUMENTO MAESTRO CONSOLIDADO — CR0**



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

**31. Rápido y profundo no existe.** Existen 5 velocidades para 5 contextos. Intentar profundidad en tiempo real es el error — genera respuestas mediocres con apariencia de profundidad. El sistema elige la cadencia correcta para el momento: reflejo para lo inmediato, batch nocturno para lo profundo. La calidad no se negocia — se agenda.

---

## Añadir a §4 PIPELINE o crear nueva §4B: ARQUITECTURA DE TIERS

### 5 tiers de enjambre: velocidad × profundidad × coste

```
TIER 1 — REFLEJO
  Latencia:     milisegundos
  Coste:        $0
  Enjambre:     ninguno — código puro
  Mecanismo:    Lookup en Matriz precompilada por el Gestor
  Cuándo:       "Este patrón lo he visto 47 veces"
  Ejemplo:      Usuario pregunta horario → tabla precalculada
  Profundidad:  0 (ejecución, no análisis)

TIER 2 — RESPUESTA
  Latencia:     5-15 segundos
  Coste:        $0.01-0.05
  Enjambre:     1 modelo OS barato (GPT-OSS / Qwen3-Coder-Next)
  Mecanismo:    Modelo + programa compilado por el Gestor
  Cuándo:       Interacción normal de conversación
  Ejemplo:      "¿Cómo van las reservas esta semana?"
  Profundidad:  Base (nivel 1-2 de la Matriz)

TIER 3 — ANÁLISIS
  Latencia:     1-5 minutos
  Coste:        $0.10-0.50
  Enjambre:     3-5 modelos en paralelo, cada uno su ángulo
  Mecanismo:    Mini-mesa redonda rápida (1 ronda, sin enriquecimiento)
  Cuándo:       Decisión importante, el usuario puede esperar
  Ejemplo:      "¿Debería abrir sábados?" → 3 modelos × 3 lentes
  Profundidad:  Media (nivel 2-3, algunos insights)

TIER 4 — PROFUNDO
  Latencia:     30-60 minutos
  Coste:        $0.50-2.00
  Enjambre:     Mente distribuida completa (10 modelos, micro-rondas, pizarra)
  Mecanismo:    Exp 4.3 — pizarra compartida con convergencia
  Cuándo:       Batch nocturno. Briefing matutino. Análisis semanal.
  Ejemplo:      Datos del día → 10 modelos procesan a las 2am → briefing a las 8am
  Profundidad:  Alta (nivel 3-4, conexiones cross-celda, puntos ciegos)

TIER 5 — CARTOGRAFÍA
  Latencia:     horas a días
  Coste:        $5-20
  Enjambre:     Exploración completa (18 INTs × composiciones × loops)
  Mecanismo:    Protocolo de exploración 5 tiers (§6B) + mente distribuida
  Cuándo:       Onboarding cliente nuevo. Auditoría anual. Nuevo dominio.
  Ejemplo:      Primer análisis completo de un negocio nuevo
  Profundidad:  Máxima (mapa 3L×7F completo con todas las conexiones)
```

### Cómo el Motor decide qué tier activar

```
Input entra
    ↓
¿Hay respuesta precompilada en la Matriz?
  SÍ → TIER 1 (reflejo, $0, ms)
  NO ↓

¿Es conversación normal (turno de chat, pregunta directa)?
  SÍ → TIER 2 (1 modelo, $0.01, 10s)
  NO ↓

¿El usuario pide análisis o decisión?
  SÍ → TIER 3 (3-5 modelos, $0.30, 3min)
  NO ↓

¿Es proceso batch (no hay usuario esperando)?
  SÍ → TIER 4 (mente distribuida, $1, 45min)
  NO ↓

¿Es exploración de dominio nuevo?
  SÍ → TIER 5 (cartografía completa, $10, horas)
```

### Relación con loops existentes

```
LOOP RÁPIDO (Motor vN):     Tier 1 + Tier 2 (cadencia: segundos)
LOOP MEDIO (análisis):       Tier 3 (cadencia: minutos, bajo demanda)
LOOP LENTO (Gestor):         Tier 4 (cadencia: horas, batch)
LOOP PROFUNDO (Reactores):   Tier 5 (cadencia: días, onboarding/auditoría)
```

### Cada tier tiene su enjambre

| Tier | Modelos típicos | Por qué estos |
|------|----------------|---------------|
| 1 | Ninguno (código puro) | Velocidad máxima, coste cero |
| 2 | GPT-OSS o Qwen3-Coder-Next | Baratos, rápidos, suficientes para respuesta directa |
| 3 | V3.2 Chat + Cogito + R1 | Balance profundidad/velocidad, cada uno aporta ángulo diferente |
| 4 | 10 modelos OS (pizarra Exp 4.3) | Máxima diversidad de perspectivas, convergencia por micro-rondas |
| 5 | 10 modelos + composiciones + loops | Todo el arsenal, exploración exhaustiva |

Los modelos de cada tier se configuran en el Gestor (no hardcoded). El Gestor compila el enjambre óptimo por tier basándose en datos de efectividad (Principio 23: el Gestor compila, los consumidores ejecutan).

---

## Tabla de cambios para §0

| Cambio | Origen | Sección |
|--------|--------|---------|
| **Principio 31: Rápido y profundo no existe. 5 velocidades para 5 contextos.** | Sesión 11-mar | §12 |
| **5 tiers de enjambre: reflejo / respuesta / análisis / profundo / cartografía** | Sesión 11-mar | §4B (nueva) |
| **Mente distribuida (pizarra) como primitiva de Tier 4** | Sesión 11-mar (Exp 4.3) | §4B, §6E |
| **Mesa redonda de acumulación como alternativa a evaluación ciega** | Sesión 11-mar (Exp 4) | §6B |
| **Prompts especializados por modelo según fortaleza empírica** | Sesión 11-mar (Exp 4.1) | §6B |
| **Sintetizador como paso final de la mente distribuida** | Sesión 11-mar (Exp 4.2) | §4B |



## motor-semantico/ACTUALIZACION_MAESTRO_SESION_11_MAR.md

# ACTUALIZACIÓN DOCUMENTO MAESTRO — Sesiones 10-mar noche + 11-mar

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-11
**Instrucción:** Incorporar al SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md

---

## §0 — AÑADIR A TABLA DE CAMBIOS

| Cambio | Origen | Sección |
|--------|--------|---------|
| **Exp 1 COMPLETADO: 12 modelos evaluados en cobertura matricial** | Sesión 10-mar-noche | §10 |
| **Ranking final: V3.1 (2.19), R1 (2.18), GPT-OSS (2.15), V3.2 Chat (2.12), Claude 10º de 12** | Sesión 10-mar-noche | §6B |
| **V3.2 Chat tiene 6/21 celdas nivel 3+ — más insights no obvios que todos** | Sesión 10-mar-noche | §6B |
| **V3.2 Reasoner bug fix: reasoning_content vs content vacío** | Sesión 10-mar-noche | §6B |
| **V3.2 como coder: 80% (4/5 tests). Falla regla 11 y mapeo Matriz→INT** | Sesión 10-mar-noche | §6F |
| **Test set evaluador listo: 5 outputs + 5 eval Sonnet referencia** | Sesión 10-mar-noche | §10 |
| **9 modelos diferentes ganan celdas en Tabla 3 — ninguno domina** | Sesión 10-mar-noche | §6B |
| **Cogito Frontera×Sentido = 3.4 — score más alto de cualquier celda de Sentido** | Sesión 10-mar-noche | §6B |
| **Sentido sigue siendo la lente más difícil para todos** | Sesión 10-mar-noche | §6B |
| **Exp 2 ejecutado parcial: 7/11 modelos OS como evaluadores. Mejor Spearman=0.464 (insuficiente)** | Sesión 11-mar | §10 |
| **Evaluación OS insuficiente con referencia Sonnet. Pero Sonnet (10º ejecutor) puede ser mala referencia** | Sesión 11-mar | §10 |
| **5/7 modelos OS deflactan vs Sonnet → Sonnet posiblemente infla scores** | Sesión 11-mar | §10 |
| **Decisión: no hay gold standard. La verdad es el consenso entre evaluadores.** | Sesión 11-mar | §6B |
| **Mesa Redonda (Exp 4): 12 modelos evalúan → ven lo de los demás → enriquecen. Acumulación, no debate.** | Sesión 11-mar | §6B, §4B |
| **Mesa Redonda Especializada (Exp 4.1): cada modelo con prompt afinado a su fortaleza empírica** | Sesión 11-mar | §6B |
| **Sintetizador (Exp 4.2): un modelo integra las 12 perspectivas en output coherente** | Sesión 11-mar | §4B |
| **Mente Distribuida (Exp 4.3): pizarra compartida, micro-rondas, 12 modelos = 1 cerebro** | Sesión 11-mar | §4B |
| **Cadena de Montaje (Exp 5): pipeline industrial de código con 5 estaciones especializadas** | Sesión 11-mar | §6F |
| **Principio 31: Rápido y profundo no existe. 5 velocidades para 5 contextos.** | Sesión 11-mar | §12, §4B |
| **5 tiers de enjambre: reflejo ($0, ms) / respuesta ($0.01, 10s) / análisis ($0.30, 3min) / profundo ($1, 45min) / cartografía ($10, horas)** | Sesión 11-mar | §4B |
| **Opus se ejecuta manualmente en claude.ai ($0 API). No se incluye en pipelines automatizados.** | Sesión 11-mar | §8 |
| **Modelos de código disponibles: Qwen3-Coder 480B, Qwen3-Coder-Next 80B, MiniMax M2.5, GLM-5** | Sesión 11-mar | §6F |
| **Enjambre de evaluadores: 12 modelos OS (Together + DeepSeek), no hay gold standard** | Sesión 11-mar | §6B |

---

## §6B — AÑADIR: RESULTADOS EXP 1 COMPLETO (12 modelos)

### Ranking final multi-modelo (Tabla 4) — 12 modelos evaluados

| # | Modelo | Nivel medio | Celdas cubiertas | Celdas 3+ |
|---|--------|-------------|-----------------|-----------|
| 1 | DeepSeek V3.1 | 2.19 | 19/21 | 5/21 |
| 2 | DeepSeek R1 | 2.18 | 20/21 | 4/21 |
| 3 | GPT-OSS 120B | 2.15 | 19/21 | 5/21 |
| 4 | DS-V3.2 Chat | 2.12 | 18/21 | **6/21** |
| 5 | DS-V3.2 Reasoner | 2.00 | 17/21 | 3/21 |
| 6 | Cogito 671B | 1.98 | 18/21 | 2/21 |
| 7 | Qwen3 Thinking | 1.95 | 19/21 | 2/21 |
| 8 | Kimi K2.5 | 1.87 | 18/21 | 1/21 |
| 9 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 |
| 10 | Claude (ref) | 1.79 | 15/21 | 1/21 |
| 11 | Maverick | 1.74 | 16/21 | 1/21 |
| 12 | 70B | 1.42 | 11/21 | 1/21 |

### Hallazgos clave Exp 1

1. **3 modelos OS superan a Claude.** V3.1, R1, GPT-OSS. Claude es 10º de 12.
2. **V3.2 Chat tiene 6/21 celdas nivel 3+** — más insights no obvios que todos. Nivel medio 4º pero más profundo donde importa.
3. **Cogito Frontera×Sentido = 3.4** — score más alto de cualquier modelo en cualquier celda de Sentido. Candidato a cerebro profundo.
4. **9 modelos diferentes ganan celdas.** Ningún modelo domina. El enjambre siempre gana.
5. **Sentido sigue siendo la lente más difícil para todos.**
6. **V3.2 Reasoner corregido** — bug en reasoning_content vs content. Fix: leer content primero, si vacío leer reasoning_content.

### Asignación modelo→celda actualizada (Tabla 3)

| | Conservar | Captar | Depurar | Distribuir | Frontera | Adaptar | Replicar |
|---|---------|---------|---------|---------|---------|---------|---------|
| **Salud** | V3.1 (2.8) | Maverick (2.1) | GPT-OSS (2.6) | Qwen3 Think (2.1) | V3.1 (2.6) | Kimi (2.7) | V3.1 (2.0) |
| **Sentido** | Cogito (2.3) | V3.2 Reas (2.7) | GPT-OSS (2.9) | GPT-OSS (1.7) | **Cogito (3.4)** | V3.1 (2.4) | R1 (1.7) |
| **Continuidad** | V3.1 (2.4) | Qwen3 Think (2.2) | Qwen3.5 (2.3) | Qwen3 Think (2.2) | V3.1 (2.9) | V3.2 Reas (2.8) | R1 (3.1) |

---

## §6B — AÑADIR: EVALUACIÓN MULTI-MODELO (Exp 2)

### Resultados Exp 2 (parcial: 7/11 modelos)

Todos medidos vs Sonnet como referencia. **Dato importante: Sonnet fue 10º como ejecutor, su evaluación puede no ser buen benchmark.**

| Modelo | Spearman | Bias | F1(3+) | Nota |
|--------|----------|------|--------|------|
| GLM-4.7 | 0.464 | +0.14 | 0.000 | Solo 1/5 outputs parseados |
| V3.2 Chat | 0.426 | -0.46 | 0.103 | Deflacta vs Sonnet |
| Qwen3-235B | 0.373 | +0.54 | 0.578 | Infla, pero detecta insights |
| GPT-OSS | 0.280 | -0.74 | 0.348 | Fuerte deflación |
| R1 | 0.247 | -0.62 | 0.293 | Deflacta |
| V3.1 | 0.220 | -0.34 | 0.190 | Deflacta |
| M2.5 | 0.208 | -0.44 | 0.279 | Deflacta |

**Conclusión Exp 2:** Ningún modelo OS alcanza Spearman ≥ 0.85 vs Sonnet. Pero 5/7 deflactan — sugiere que Sonnet infla scores, no que los OS evalúen mal. La referencia es el problema, no los evaluadores.

**Decisión:** No hay gold standard. La verdad es el consenso entre todos. Mesa redonda (Exp 4) como protocolo de evaluación.

### Modelos que faltaron en Exp 2
- Cogito 671B, V3.2 Reasoner, Kimi K2.5, MiniMax M1 — no ejecutados
- R1, M2.5, GLM-4.7 — parciales (no completaron los 5 outputs)

---

## §4B — NUEVA SECCIÓN: ARQUITECTURA DE TIERS

### Principio: Rápido y profundo no existe

5 velocidades para 5 contextos. La calidad no se negocia — se agenda.

```
TIER 1 — REFLEJO (ms, $0)
  Código puro. Lookup en Matriz precompilada.
  "Este patrón lo he visto 47 veces"

TIER 2 — RESPUESTA (5-15s, $0.01-0.05)
  1 modelo OS barato. 80% de interacciones.

TIER 3 — ANÁLISIS (1-5 min, $0.10-0.50)
  3-5 modelos en paralelo. Decisiones importantes.

TIER 4 — PROFUNDO (30-60 min, $0.50-2.00)
  Mente distribuida. Batch nocturno. Briefing matutino.

TIER 5 — CARTOGRAFÍA (horas/días, $5-20)
  Exploración completa. Onboarding. Auditoría anual.
```

### Relación con loops

```
LOOP RÁPIDO (Motor vN):     Tier 1 + Tier 2 (segundos)
LOOP MEDIO (análisis):       Tier 3 (minutos, bajo demanda)
LOOP LENTO (Gestor):         Tier 4 (horas, batch nocturno)
LOOP PROFUNDO (Reactores):   Tier 5 (días, onboarding)
```

### Enjambre por tier

| Tier | Modelos típicos | Por qué |
|------|----------------|---------|
| 1 | Ninguno (código) | Velocidad máxima |
| 2 | GPT-OSS / Qwen3-Coder-Next | Baratos, rápidos |
| 3 | V3.2 Chat + Cogito + R1 | Balance profundidad/velocidad |
| 4 | 10 modelos OS (pizarra) | Máxima diversidad |
| 5 | 10 modelos + composiciones + loops | Todo el arsenal |

### Mecanismos de Tier 4 — Tres variantes diseñadas

**A) Mesa Redonda (Exp 4):** 12 modelos evalúan → ven lo de los demás → enriquecen. Acumulación de perspectivas. Output = unión de visiones.

**B) Mesa Especializada (Exp 4.1):** Igual que A pero cada modelo con prompt afinado a su fortaleza empírica (Cogito→Sentido, R1→Continuidad, GPT-OSS→Depurar, etc.)

**C) Mente Distribuida (Exp 4.3):** Pizarra compartida + micro-rondas. Cada modelo contribuye diffs, no evaluaciones completas. Más barato y rápido que A/B. Los 12 modelos operan como áreas de un mismo cerebro.

**Sintetizador (Exp 4.2):** Después de A, B, o C, un modelo integra las perspectivas en output coherente. Conecta celdas, identifica meta-patrones, detecta puntos ciegos residuales.

---

## §6F — AÑADIR: ENJAMBRE DE CÓDIGO (Exp 3 + Exp 5)

### Modelos de código disponibles (todos en Together + DeepSeek)

| Modelo | model_id | Perfil |
|--------|----------|--------|
| Qwen3-Coder 480B | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | Especialista código. 256K context. $2/M. |
| Qwen3-Coder-Next 80B | `Qwen/Qwen3-Coder-Next-FP8` | Ultra-eficiente. 3B activos. $1.20/M. |
| MiniMax M2.5 | `MiniMaxAI/MiniMax-M2.5` | 80.2% SWE-Bench. 10B activos. $1.20/M. |
| GLM-5 | `zai-org/GLM-5` | Systems engineering. 744B. $3.20/M. |
| V3.2 Chat | `deepseek-chat` | 80% en test de Exp 1. Barato. $1.10/M. |

### Resultado V3.2 como coder (Exp 1 Parte B)
- 4/5 tests pasan (80%). Código OOP limpio, ejecutable.
- Falla: regla 11 (orden INT-14/INT-01) y mapeo Matriz→Inteligencias.
- Veredicto: funcional como esqueleto pero necesita supervisión en lógica de dominio.

### Cadena de Montaje (Exp 5) — Proceso industrial de código

5 estaciones especializadas:
```
ARQUITECTO → IMPLEMENTADOR → TESTER → REVISOR → OPTIMIZADOR
```

6 configuraciones probándose con diferentes modelos por estación. Hipótesis: la cadena supera al modelo solo (>95% tasa éxito).

---

## §8 — AÑADIR: OPUS MANUAL

**Opus no se incluye en pipelines automatizados.** Se ejecuta manualmente en claude.ai ($0 API). Los resultados se cargan como archivo JSON si se necesitan. Esto ahorra ~75% del coste de los experimentos que incluían Opus.

---

## §10 — REEMPLAZAR: ESTADO DE EXPERIMENTOS

### Exp 1 — Multi-modelo cobertura matricial ✅ COMPLETADO
- 12 modelos evaluados en cobertura matricial
- Ranking final: V3.1, R1, GPT-OSS top 3. Claude 10º.
- V3.2 Chat: 6/21 celdas nivel 3+ (más profundo puntualmente)
- V3.2 Reasoner: bug fix aplicado (reasoning_content vs content)
- V3.2 como coder: 4/5 tests (80%), falla lógica de dominio
- Test set evaluador preparado: 5 outputs + 5 eval Sonnet

### Exp 2 — Enjambre de evaluadores OS 🔄 PARCIAL
- 7/11 modelos testeados. Mejor Spearman=0.464 (insuficiente)
- 5/7 modelos deflactan vs Sonnet → Sonnet posiblemente infla
- Faltaron: Cogito, V3.2 Reasoner, Kimi, MiniMax M1
- Conclusión: referencia (Sonnet) es el problema. Evaluación ciega insuficiente.
- Decisión: pasar a mesa redonda (Exp 4) para evaluación por consenso

### Exp 3 — Enjambre de código ⬜ PROMPT LISTO
- 10 modelos × 5 tareas de dificultad progresiva
- Incluye Qwen3-Coder 480B, Qwen3-Coder-Next 80B, MiniMax M2.5, GLM-5
- Análisis de pares generador+revisor

### Exp 4 — Mesa Redonda (acumulación de perspectivas) 🔄 CORRIENDO
- 12 modelos OS (sin Opus API). Opus manual en claude.ai.
- Ronda 1: evaluación ciega (reutiliza datos Exp 2 + completa faltantes)
- Ronda 2: enriquecimiento (cada modelo ve las 11 evals de los demás, SUMA lo que falta)
- No es debate — es acumulación. Cada modelo aporta su ángulo.
- Tiempo estimado: 1-2 horas (Tier 4 batch)

### Exp 4.1 — Mesa Especializada ⬜ POST EXP 4
- Igual que Exp 4 pero cada modelo con prompt afinado a su fortaleza empírica
- Compara genérico vs especializado: ¿cuánto más profundo llega?

### Exp 4.2 — Sintetizador ⬜ POST EXP 4
- 6 modelos OS candidatos a sintetizador
- Reciben las 12 perspectivas y producen output integrado
- Mide: conexiones cross-celda, hallazgo central, puntos ciegos residuales

### Exp 4.3 — Mente Distribuida ⬜ POST EXP 4
- Pizarra compartida + micro-rondas
- 10 modelos activos + Sonnet pre-cargado
- Cada modelo contribuye diffs, no evaluaciones completas
- Más barato (~$0.50-1.50) y más rápido (15-30min) que Exp 4
- Perfila cada modelo: sembrador, profundizador, conector, detector de huecos
- Determina la "mente mínima" (menor nº modelos con ≥90% del valor)

### Exp 5 — Cadena de Montaje (código) ⬜ PROMPT LISTO
- 5 estaciones: Arquitecto → Implementador → Tester → Revisor → Optimizador
- 6 configuraciones con diferentes modelos por estación
- Compara con Exp 3 (modelo solo vs par vs cadena)

---

## §12 — AÑADIR: PRINCIPIO 31

31. **Rápido y profundo no existe.** Existen 5 velocidades para 5 contextos. Intentar profundidad en tiempo real es el error — genera respuestas mediocres con apariencia de profundidad. El sistema elige la cadencia correcta para el momento: reflejo para lo inmediato, batch nocturno para lo profundo. La calidad no se negocia — se agenda.

---

## §13 — AÑADIR A TABLA DE DOCUMENTOS

| Documento | Relación | Estado |
|-----------|----------|--------|
| ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md | Principio 31 + 5 tiers de enjambre | CR0 (incorporado aquí) |
| PROMPT_CODE_EXP2_ENJAMBRE_EVALUADORES.md | Prompt para Code: 12 modelos evaluadores | Ejecutado parcial |
| PROMPT_CODE_EXP3_ENJAMBRE_CODIGO.md | Prompt para Code: 10 modelos × 5 tareas código | Pendiente |
| PROMPT_CODE_EXP4_MESA_REDONDA.md | Prompt para Code: mesa redonda 12 modelos | Corriendo |
| PROMPT_CODE_EXP4_1_MESA_ESPECIALIZADA.md | Prompt para Code: prompts por fortaleza | Pendiente |
| PROMPT_CODE_EXP4_2_SINTETIZADOR.md | Prompt para Code: quién escribe output final | Pendiente |
| PROMPT_CODE_EXP4_3_MENTE_DISTRIBUIDA.md | Prompt para Code: pizarra compartida | Pendiente |
| PROMPT_CODE_EXP5_CADENA_MONTAJE.md | Prompt para Code: pipeline industrial código | Pendiente |

---

**FIN ACTUALIZACIÓN — CR0**



## motor-semantico/ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md

# ACTUALIZACIÓN DOCUMENTO MAESTRO — Principio 32: Enjambre como Red Neuronal

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-13
**Origen:** Sesión diseño Chief OS Chat + estigmergia validada empíricamente

---

## Añadir a §12 PRINCIPIOS DE DISEÑO

**32. El enjambre no es un pipeline — es una red neuronal cuyos nodos son LLMs.** La Matriz 3L×7F no es un mapa de inteligencias — es la **matriz de pesos** de la red. El Gestor la entrena. Los modelos son fungibles. La topología es el producto.

---

## Añadir a §1 QUÉ ES (párrafo adicional) o crear §1E: EL ENJAMBRE COMO RED NEURONAL

### Fundamento

Una red neuronal clásica: nodos simples (funciones de activación), conexiones con pesos, aprendizaje por backpropagation. El enjambre OMNI-MIND: nodos masivos (LLMs de 100B+ params), conexiones con pesos derivados de la Matriz, aprendizaje por datos de efectividad (gap_cerrado por modelo×celda×pregunta).

La diferencia no es metafórica — es estructural:

| Propiedad | Red neuronal clásica | Enjambre OMNI-MIND |
|-----------|---------------------|-------------------|
| Nodo | función de activación (ReLU, sigmoid) | LLM completo (V3.2, R1, Cogito) |
| Peso de conexión | float aprendido por backprop | tasa_media_cierre de modelo→celda (datos Gestor) |
| Capa oculta | representación intermedia | ronda de estigmergia (output parcial que alimenta la siguiente ronda) |
| Forward pass | input → capas → output (ms) | pregunta → rondas de enjambre → síntesis (segundos) |
| Backpropagation | gradiente del error | feedback de efectividad: ¿la respuesta cerró el gap? |
| Topología | fija por arquitectura | dinámica por input — la Matriz decide qué conexiones se activan |

### 6 implicaciones arquitecturales

**1. No se diseña el enjambre — se entrena.**
La asignación modelo→celda emerge de datos de efectividad, no de decisión humana. Los datos de Exp 4 lo confirman: GPT-OSS es motor en pizarra (119 contribuciones) pero esponja en evaluación (0 aportes únicos). El mismo nodo cambia de peso según el mecanismo. El Gestor acumula estos datos y recalcula pesos continuamente.

**2. La topología es dinámica por input.**
No todos los nodos se activan para cada pregunta. El campo de gradientes de la Matriz determina qué celdas tienen gap, y eso determina qué modelos (nodos) y qué conexiones se activan. Una pregunta financiera activa una sub-red; una pregunta de diseño activa otra. Mismos nodos disponibles, diferente cableado.

**3. Las rondas de estigmergia son capas ocultas.**
En la pizarra, ronda 1 = capa de entrada (cada nodo dispara independiente). Ronda 2 = capa oculta (cada nodo incorpora señales de los demás). Síntesis = capa de salida. Las capas ocultas producen representaciones emergentes: Exp 4.3 generó 425 conexiones y 239 puntos ciegos que ningún nodo individual habría producido. Eso es exactamente lo que hacen las capas ocultas de una red — crear features que no existen en los datos de entrada.

**4. Cada exocortex es una red con topología propia.**
El exocortex de pilates y el de la clínica no son copias con datos diferentes. Son redes con los mismos nodos disponibles pero diferente topología de conexiones, entrenada por los datos de efectividad de su dominio. El Gestor compila un "programa de pesos" diferente para cada consumidor.

**5. Scaling = topología, no volumen.**
Exp 4 lo demostró: 12 modelos producían valor concentrado en 2-3 nodos (Qwen como cerebro, GPT-OSS como motor). Los otros eran peso muerto. Añadir nodos sin ajustar la topología no mejora la red — añade ruido. La red óptima es pequeña y bien conectada.

**6. El moat es la red entrenada.**
Los modelos son públicos. Los providers son públicos. La infraestructura es commodity. Lo que no es público: miles de datapoints de efectividad que dicen "para este patrón de gaps, esta combinación de modelos con estos pesos produce el mejor cierre de gap". Esa es la propiedad intelectual del sistema.

### Consecuencia para el roadmap

El Gestor de la Matriz no es un componente más — es el **algoritmo de entrenamiento** de la red. Sin él, el enjambre hace forward pass con pesos fijos (hardcoded). Con él, cada ejecución ajusta la topología. Implementar el Gestor es la diferencia entre un pipeline estático y un sistema que aprende.

### Dato empírico de soporte

Sesión 2026-03-13: primera ejecución de enjambre con estigmergia (2 rondas + pizarra + síntesis). 3 modelos (V3.2-chat, V3.1, R1) + Cogito sintetizador. Ronda 2 muestra 3+ referencias cruzadas donde los modelos reaccionan al output de los otros. Coste: $0.009. La red feedforward básica funciona — los nodos producen más cuando están conectados que cuando operan aislados.

---

## Añadir a §0 CAMBIOS DE ESTA VERSIÓN

| Cambio | Origen | Sección |
|--------|--------|---------|
| **El enjambre es una red neuronal de LLMs. La Matriz = matriz de pesos. El Gestor = algoritmo de entrenamiento.** | Sesión 13-mar | §1E, §12 |
| **Estigmergia validada empíricamente: ronda 2 produce referencias cruzadas entre modelos** | Sesión 13-mar | §12 |
| **Principio 32: Los modelos son fungibles, la topología es el producto** | Sesión 13-mar | §12 |

---

*CR0 — Jesús valida y cierra*



## Motor/Meta-Red de preguntas inteligencias/META_RED_INTELIGENCIAS_CR0.md

# BIBLIOTECA META-RED DE INTELIGENCIAS — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-07
**Origen:** Sesión Opus — derivación desde TABLA_PERIODICA_INTELIGENCIA_CR0.md
**Dependencias:** ALGEBRA_CALCULO_SEMANTICO_CR0.md, TABLA_PERIODICA_INTELIGENCIA_CR0.md

---

## 1. PRINCIPIO FUNDACIONAL

La inteligencia no se instruye — se pregunta into existence.

Un prompt imperativo dice "haz X". La inteligencia depende del modelo.
Un prompt interrogativo pregunta lo que solo se puede contestar ejecutando X. La inteligencia depende de la estructura de preguntas.

```
PROMPT IMPERATIVO:  "Analiza como matemático"     → el agente IMITA
PROMPT INTERROGATIVO: Red de preguntas matemáticas → el agente EJECUTA

La inteligencia reside en la estructura de preguntas, no en los parámetros del modelo.
```

---

## 2. META-RED — estructura universal de 6 pasos

Común a las 18 inteligencias. Lo que cambia es el contenido de las preguntas, no la secuencia.

```
PASO 0: EXTRAER     — "¿Qué hay aquí?"
PASO 1: CRUZAR      — "¿Qué emerge al juntar lo extraído?"
PASO 2: PROYECTAR   — "¿Qué forma tiene visto desde esta lente?"
PASO 3: INTEGRAR    — "¿Qué emerge al juntar las lentes?"
PASO 4: ABSTRAER    — "¿Qué se repite sin importar el contenido?"
PASO ∞: LIMITAR     — "¿Qué no puede ver todo lo anterior?"
```

Notación compacta:
```
Inteligencia(input) = limitar(abstraer(∫(lentes)(cruzar(extraer(input)))))
```

---

## 3. TRES CAPAS DE PREGUNTAS

### Capa 1: PREGUNTAS DE CONTENIDO
Específicas de cada inteligencia. Instancian cada paso de la meta-red.
- La matemática pregunta "¿qué se puede contar?"
- La existencial pregunta "¿qué está en juego?"
- Cada inteligencia tiene su propio set.

### Capa 2: PREGUNTAS DE OPERACIÓN
Universales. Ejecutan las 4 operaciones del álgebra entre respuestas.
- Fusión: "¿Qué dicen ambas vistas independientemente?"
- Composición: "¿Qué ve B al mirar lo que A produjo?"
- Integración: "¿Qué emerge al ver todas las respuestas juntas que ninguna dice sola?"
- Diferencial: "¿Qué puede ver esta vista que aquella NO PUEDE ver?"

### Capa 3: PREGUNTAS DE PROPIEDAD
Universales. Testan relaciones entre respuestas y generan meta-pensamiento.
- Conmutatividad: "¿Cambia algo si invierto el orden?"
- Distributividad: "¿Puedo partir esto en paralelo o se pierde algo?"
- Saturación: "¿Sigue aportando valor o estamos girando?"
- Clausura: "¿Esta respuesta puede ser input de otra pregunta diferente?"

---

## 4. LAS 18 INTELIGENCIAS COMO REDES DE PREGUNTAS

### CATEGORÍA I: FORMALES

---

### INT-01: LÓGICO-MATEMÁTICA

**PASO 0: EXTRAER — formalizar**
```
¿Qué se puede contar en este caso?
¿Qué se puede medir?
¿Qué magnitudes aparecen con número explícito?
¿Qué magnitudes aparecen sin número pero se podrían medir?
¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?
¿Qué se quiere saber que aún no se sabe?
¿Qué se da por hecho sin verificar?
```

**PASO 1: CRUZAR — estructurar tipo de problema**
```
De todas las relaciones que encontraste, ¿cuántas puedes mover y cuántas están fijadas?
¿Mover una variable mejora todo, o mejorar una empeora otra?
Si empeora otra: ¿hay algún punto donde ambas sean aceptables, o siempre hay que elegir?
¿Los números son continuos o discretos?
¿Lo que no se sabe se puede estimar, o es genuinamente incierto?
```

**PASO 2: LENTES**

L1 Álgebra:
```
¿Cuántas ecuaciones hay y cuántas incógnitas?
¿Hay más ecuaciones que incógnitas o menos?
¿Alguna ecuación es redundante — dice lo mismo que otra de otra forma?
¿Alguna ecuación contradice a otra?
```

L2 Análisis:
```
Si aumentas cada variable un poco, ¿qué pasa con el resultado?
¿Hay algún punto donde aumentar deja de mejorar y empieza a empeorar?
¿Alguna variable tiene efecto desproporcionado — pequeños cambios, grandes efectos?
¿Falta alguna variable en la ecuación que en la realidad sí afecta?
```

L3 Geometría:
```
Si dibujas las opciones como puntos en un espacio, ¿qué forma tienen?
¿Forman una línea, una superficie, o un volumen?
¿Hay una frontera más allá de la cual no se puede ir?
¿Las opciones "buenas" están concentradas en una zona o dispersas?
```

L4 Probabilidad:
```
¿Qué números del caso son seguros y cuáles son estimaciones?
¿De los estimados, cuánto podrían variar?
¿Qué pasaría con la conclusión si los estimados se desvían un 20%?
¿Hay algo que podría pasar, que cambiaría todo, y que nadie está midiendo?
```

L5 Optimización:
```
¿Se puede mejorar todo a la vez, o mejorar una cosa empeora otra?
Si hay que elegir, ¿qué importa más — y quién decide eso?
¿La respuesta a "qué importa más" es un dato o una preferencia?
Si es una preferencia, ¿el problema es matemático o es de valores?
```

L6 Lógica:
```
¿Qué se puede deducir con certeza de los datos?
¿Hay alguna combinación de premisas que se contradiga?
Si todas las opciones consumen del mismo recurso limitado, ¿es posible que alguna no lo consuma?
¿La pregunta original asume algo que los datos muestran como falso?
```

**PASO 3: ∫ — integrar**
```
¿Qué dicen todas las lentes que coincide?
¿Dónde se contradicen?
¿Hay algo que solo aparece cuando miras todas juntas?
¿La conclusión de una lente cambia el significado de lo que otra encontró?
```

**PASO 4: GENERALIZAR**
```
¿Este caso es único o hay una clase de casos que comparten esta estructura?
Si quitas los nombres y números, ¿qué patrón queda?
¿Ese patrón aparece en otros dominios?
¿Qué condiciones harían que este patrón NO apareciera?
```

**PASO ∞: FRONTERA**
```
¿Qué asume todo este análisis que no ha examinado?
¿Hay algo que no se puede expresar como número o ecuación?
Si eso fuera lo más importante, ¿qué cambia?
¿Es la herramienta correcta, o está forzando forma donde no hay?
```

---

### INT-02: COMPUTACIONAL

**PASO 0: EXTRAER — descomponer**
```
¿Cuáles son las entradas del sistema?
¿Cuáles son las salidas deseadas?
¿Qué transformaciones llevan de entrada a salida?
¿Hay partes que se pueden resolver independientemente?
¿Hay partes que dependen del resultado de otras?
¿Qué datos faltan para poder calcular?
```

**PASO 1: CRUZAR — clasificar complejidad**
```
¿Cuántos pasos tiene la transformación más larga?
¿Hay bucles — alguna parte necesita repetirse hasta converger?
¿El problema escala — si duplicas el tamaño, el esfuerzo se duplica o se multiplica?
¿Se puede dividir en subproblemas que se resuelven en paralelo?
¿Hay incertidumbre que obliga a explorar múltiples caminos?
```

**PASO 2: LENTES**

L1 Algorítmica:
```
¿Existe un procedimiento paso a paso que siempre da la respuesta?
¿Cuántos pasos necesita?
¿Hay atajos — formas de llegar más rápido sin recorrer todo?
¿Puede fallar? ¿Bajo qué condiciones?
```

L2 Estructuras de datos:
```
¿Cómo se organizan mejor los datos — lista, árbol, grafo, tabla?
¿La organización afecta la velocidad de respuesta?
¿Hay datos que se consultan mucho y otros casi nunca?
¿Falta algún dato que haría la consulta trivial?
```

L3 Concurrencia:
```
¿Qué partes se pueden hacer al mismo tiempo?
¿Hay recursos compartidos que obligan a esperar?
¿El orden de ejecución afecta el resultado?
¿Qué pasa si dos partes intentan modificar lo mismo a la vez?
```

L4 Aproximación:
```
¿Necesita ser exacto o basta con una estimación buena?
¿Cuánto error es aceptable?
¿Se puede obtener una respuesta 80% correcta en 10% del tiempo?
¿Qué se pierde al simplificar?
```

**PASO 3: ∫**
```
¿Qué dicen todas las lentes juntas sobre la viabilidad?
¿El algoritmo ideal es viable con los datos disponibles?
¿La estructura de datos necesaria existe o hay que construirla?
¿El cuello de botella es velocidad, datos, o definición del problema?
```

**PASO 4: GENERALIZAR**
```
¿Este problema es una instancia de un problema conocido?
¿Tiene soluciones estándar que se pueden adaptar?
¿En qué se diferencia de la versión estándar?
```

**PASO ∞: FRONTERA**
```
¿Lo que necesita resolver esta persona es realmente un problema de cómputo?
¿Hay algo que el cálculo no puede capturar — intuición, juicio, contexto?
¿Automatizar esto resuelve el problema o lo esconde?
```

---

### INT-03: ESTRUCTURAL (IAS)

**PASO 0: EXTRAER — coordenadas sintácticas C1-C5**
```
¿Cómo se comprime esto en una palabra, una frase, un párrafo? (C1)
¿Qué dice que hace vs qué hace realmente — dónde está el gap id↔ir? (C2)
¿Qué está conectado con qué, y qué conexiones faltan? (C3)
¿Quién opera sobre quién, con cuánto poder? (C4)
¿Cuánto diverge lo declarado de lo real — el número exacto? (C5)
```

**PASO 1: CRUZAR — huecos activos H1-H3**
```
¿Lo que se nombra y lo que se mide coinciden? Si no, ¿dónde divergen? (H1)
¿Hay algo que opera con potencia máxima PORQUE no se nombra? (H2)
¿La desconexión entre piezas es accidental o sostiene el sistema? (H3)
```

**PASO 2: LENTES — 4 isomorfismos**

Conjuntos (T1):
```
¿Qué contiene a qué?
¿Qué se solapa — comparte elementos de dos conjuntos?
¿Qué conjuntos deberían existir pero no existen?
¿Qué está fuera de todos los conjuntos?
```

Causal (T2):
```
¿Qué causa qué — qué circuitos existen?
¿Se amplifican (refuerzo) o se frenan (balanceo)?
¿El sistema está en equilibrio o se mueve?
¿Hacia dónde converge si nadie cambia nada?
```

Juegos (T3):
```
¿Quién está jugando — quién tiene intereses en esto?
¿Qué quiere cada jugador?
¿Qué estrategia usa cada uno — consciente o no?
¿Cuánto poder tiene cada uno (0-1)?
¿Quién gana si nadie cambia nada?
¿Quién falta en el tablero — quién debería estar y no está?
```

Cibernética (T4):
```
¿Qué mide el sistema — qué sensores tiene?
¿Qué ajusta cuando algo cambia — qué actuadores tiene?
¿Qué señales llegan y se ignoran?
¿La regulación es rígida (siempre igual) o adaptativa?
```

**PASO 3-4-∞:** (idénticos al álgebra CR0)

---

### INT-04: ECOLÓGICA

**PASO 0: EXTRAER — mapear el ecosistema**
```
¿Quiénes son los organismos de este ecosistema — qué entidades viven aquí?
¿Qué flujos existen entre ellos — qué se mueve de uno a otro?
¿Quién depende de quién para sobrevivir?
¿Qué pasa si quitas a uno — quién sufre primero?
¿Hay ciclos — algo que sale y vuelve al mismo punto?
```

**PASO 1: CRUZAR — detectar fragilidad**
```
¿Hay un nodo del que dependen muchos — un punto único de fallo?
¿Hay redundancia — si un flujo se corta, hay otro camino?
¿El sistema está creciendo, estable, o decayendo?
¿Qué señal aparecería primero si el sistema va a colapsar?
¿Ya apareció esa señal?
```

**PASO 2: LENTES**

L1 Flujos:
```
¿Qué entra al sistema, qué sale, qué se queda?
¿El balance es positivo (acumula) o negativo (consume)?
¿Hay fugas — energía que se pierde sin producir?
¿Hay algún flujo bloqueado que debería moverse?
```

L2 Nichos:
```
¿Cada entidad tiene un rol claro o hay solapamiento?
¿Hay nichos vacíos — funciones que nadie cumple?
¿Hay competencia por el mismo nicho?
¿El ecosistema tiene diversidad suficiente o depende de pocos?
```

L3 Resiliencia:
```
¿Cuánto shock puede absorber el sistema antes de cambiar de estado?
¿Tiene reservas — margen, ahorro, tiempo libre?
¿Qué es lo primero que se rompe bajo presión?
¿Se ha roto antes? ¿Qué pasó? ¿Se recuperó?
```

L4 Ciclos:
```
¿Hay estacionalidad o ritmo natural?
¿El sistema respeta sus propios ciclos o los fuerza?
¿Hay tiempo de recuperación entre ciclos de esfuerzo?
¿Los ciclos se aceleran o se mantienen estables?
```

**PASO 3: ∫**
```
¿Qué emerge al cruzar flujos con resiliencia — el sistema fluye pero ¿aguanta?
¿Los nichos vacíos explican las fugas en los flujos?
¿Los ciclos forzados están erosionando la resiliencia?
```

**PASO 4: GENERALIZAR**
```
¿Este ecosistema se parece a otros que se han estudiado?
¿Tiene la estructura de un ecosistema sano o de uno al borde del colapso?
¿Qué intervención mínima cambiaría más la trayectoria?
```

**PASO ∞: FRONTERA**
```
¿El sistema es realmente un ecosistema o es una máquina operada por una persona?
¿La metáfora ecológica ilumina o engaña?
¿Hay voluntad humana aquí que rompe la lógica de ecosistema?
```

---

### INT-05: ESTRATÉGICA

**PASO 0: EXTRAER — mapear posición**
```
¿Dónde estás ahora — fuerte o débil?
¿Qué recursos tienes — dinero, tiempo, personas, información?
¿Qué opciones de movimiento existen?
¿Cuáles son reversibles y cuáles no?
¿Quién más está en el tablero — qué quieren y qué pueden?
¿Qué sabes tú que ellos no? ¿Qué saben ellos que tú no?
```

**PASO 1: CRUZAR — posición × recursos**
```
De tus recursos, ¿cuáles se agotan al usarlos?
¿Varias opciones compiten por el mismo recurso escaso?
¿Hay algún recurso que NO estás usando y podrías?
¿Algún movimiento que parece opción realmente no lo es?
```

**PASO 2: LENTES**

L1 Posicional:
```
¿Tu posición mejora o empeora si no haces nada?
¿Hay ventana temporal — un momento que si pasa ya no vuelve?
¿Tu posición es fácil de atacar o difícil?
```

L2 Secuencial:
```
¿En qué orden tendrían que pasar las cosas?
¿Hay algo que DEBE hacerse antes de que lo demás sea posible?
¿Qué se desbloquea al hacer el primer movimiento?
¿Hay algún movimiento que cierre opciones futuras?
```

L3 Adversarial:
```
¿Qué hará el otro si tú haces X?
¿Qué hará si sabe que tú harás X?
¿Hay forma de que ambos ganen, o es suma cero?
¿Quién pierde más esperando?
```

L4 Opcionalidad:
```
¿Puedes moverte sin comprometerte — explorar sin quemar puentes?
¿Cuánto vale mantener opciones abiertas vs decidir ahora?
¿Hay algún movimiento barato que da información antes del caro?
```

**PASO 3-4-∞:** (desarrollados en la sesión)

---

### INT-06: POLÍTICA

**PASO 0: EXTRAER — mapear poder**
```
¿Quién tiene poder de decisión real — no formal, real?
¿Quién puede bloquear la decisión aunque no tenga poder para decidir?
¿Quién influye sin cargo — legitimidad social, moral, emocional?
¿Qué narrativa domina — qué historia se cuenta sobre el problema?
¿Quién controla la narrativa?
```

**PASO 1: CRUZAR — poder × legitimidad**
```
¿El poder formal y el poder real están en las mismas manos?
¿Alguien tiene poder pero no legitimidad — o legitimidad pero no poder?
¿Hay alianzas — quién apoya a quién y a cambio de qué?
¿Hay alguien cuya opinión cambiaría todo si se expresara?
```

**PASO 2: LENTES**

L1 Poder:
```
¿Quién decide realmente — siguiendo el dinero, no los organigramas?
¿Ese poder es estable o puede cambiar pronto?
¿Hay poder que nadie reconoce pero todos obedecen?
```

L2 Coaliciones:
```
¿Quién gana si se forma la coalición A+B? ¿Quién pierde?
¿Qué mantiene unida a la coalición actual — interés común o miedo común?
¿Qué la rompería?
```

L3 Narrativa:
```
¿Qué historia se cuenta sobre el problema?
¿Quién la escribió — y a quién favorece?
¿Hay otra historia posible con los mismos hechos?
¿Qué pasaría si la narrativa alternativa se impusiera?
```

L4 Legitimidad:
```
¿Qué da derecho a decidir — cargo, experiencia, riesgo asumido, mérito?
¿Quién tiene más legitimidad para decidir y no la está usando?
¿La decisión será aceptada por los afectados — o solo impuesta?
```

**PASO 3: ∫**
```
¿El que tiene poder tiene legitimidad para usarlo?
¿La narrativa oculta o revela la distribución real de poder?
¿Hay una coalición posible que cambiaría todo y nadie la ha visto?
```

**PASO 4: GENERALIZAR**
```
¿Esta configuración de poder se parece a otras conocidas?
¿Qué pasó en situaciones similares — quién ganó, cómo, a qué coste?
```

**PASO ∞: FRONTERA**
```
¿Analizar políticamente un problema personal lo convierte en algo que no es?
¿Hay genuino conflicto de intereses o es una persona contra sí misma?
¿La herramienta política crea el conflicto que dice analizar?
```

---

### INT-07: FINANCIERA

**PASO 0: EXTRAER — mapear flujos**
```
¿Qué entra de dinero, cuánto, con qué frecuencia?
¿Qué sale de dinero, cuánto, con qué frecuencia?
¿Cuánto queda — y es estable, crece o decrece?
¿Hay deudas — cuánto, a quién, a qué coste, cuándo vence?
¿Hay activos — qué valen, qué producen, se deprecian?
¿Cuánto cuesta tu hora — no lo que cobras, lo que te cuesta a ti vivirla?
```

**PASO 1: CRUZAR — flujos × riesgo**
```
¿Los ingresos dependen de ti o tienen vida propia?
¿Si paras un mes, los ingresos caen a cero?
¿Los costes son fijos o variables — cuánto control tienes?
¿Tienes colchón — cuántos meses puedes aguantar sin ingresos?
¿El dinero que ganas hoy compra seguridad mañana o se consume hoy?
```

**PASO 2: LENTES**

L1 Valor presente:
```
¿Lo que vas a ganar mañana, cuánto vale hoy?
¿Estás sacrificando algo ahora que vale más que lo que ganarás después?
¿El dinero futuro es seguro o es una promesa?
¿A qué tasa descuentas — qué urgencia tiene tu presente?
```

L2 Apalancamiento:
```
¿Estás usando dinero ajeno — crédito, deuda, inversores?
¿Ese dinero ajeno amplifica tus ganancias o tus pérdidas?
¿Cuánto puedes perder antes de que el apalancamiento te destruya?
¿El que te presta gana más que tú con tu negocio?
```

L3 Opcionalidad:
```
¿Cuánto cuesta mantener opciones abiertas?
¿Hay asimetría — puedes ganar mucho si sale bien y perder poco si sale mal?
¿O es al revés — ganas poco y arriesgas mucho?
¿Puedes comprar tiempo antes de decidir?
```

L4 Margen de seguridad:
```
¿Cuánto puede salir mal antes de que el sistema se rompa?
¿Estás operando al límite o con margen?
¿Un imprevisto de X€ te pondría en crisis?
¿Tu plan funciona solo si todo sale bien, o también si algo sale mal?
```

**PASO 3: ∫**
```
¿El valor presente justifica el apalancamiento actual?
¿La opcionalidad compensa el riesgo?
¿Hay margen de seguridad suficiente o estás desnudo?
¿El flujo paga la deuda, la vida, Y deja reserva — o falta algo?
```

**PASO 4: GENERALIZAR**
```
¿Este perfil financiero es sostenible a 5 años sin cambios?
¿Se parece al de otros que prosperaron o al de otros que quebraron?
¿Cuál es la variable que separa un escenario del otro?
```

**PASO ∞: FRONTERA**
```
¿Todo se puede traducir a euros?
¿Cuánto vale una cena con tus hijos en la hoja de cálculo?
¿El análisis financiero responde a la pregunta correcta o a la que sabe responder?
```

---

### INT-08: SOCIAL

**PASO 0: EXTRAER — mapear emociones e intenciones**
```
¿Qué siente esta persona — no lo que dice, lo que siente?
¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?
¿Qué necesita realmente — no lo que pide, lo que necesita?
¿Quién más está afectado y cómo se sienten?
¿Hay emociones que nadie nombra pero que gobiernan las decisiones?
```

**PASO 1: CRUZAR — emociones × relaciones**
```
¿Lo que siente esta persona coincide con lo que muestra?
¿Los demás perciben lo que realmente pasa o solo la superficie?
¿Hay patrones — esta situación se repite, se parece a otras anteriores?
¿El conflicto es entre personas o dentro de una persona?
¿Alguien está cargando emociones que no son suyas?
```

**PASO 2: LENTES**

L1 Empatía:
```
¿Cómo se siente estar en sus zapatos — con su presión, sus miedos, sus deseos?
¿Qué le quita el sueño?
¿Qué le daría alivio inmediato vs qué le daría paz duradera?
¿Hay algo que no puede admitir ni ante sí mismo?
```

L2 Dinámicas:
```
¿Quién cuida a quién en este sistema?
¿Alguien da más de lo que recibe — o recibe más de lo que da?
¿Hay deuda emocional acumulada — favores no devueltos, quejas no dichas?
¿Qué pasaría si alguien dijera en voz alta lo que todos piensan?
```

L3 Patrones:
```
¿Esta persona ha estado en esta situación antes?
¿Qué hizo la última vez — funcionó?
¿Hay un patrón que se repite sin que sea consciente de ello?
¿Qué beneficio oculto tiene mantener el patrón?
```

L4 Vínculos:
```
¿Qué relaciones nutren y cuáles drenan?
¿Hay relaciones que sobreviven por inercia, no por valor?
¿Quién falta — qué vínculo necesita que no tiene?
¿Qué vínculo está en peligro y nadie lo está cuidando?
```

**PASO 3: ∫**
```
¿La empatía revela algo que las dinámicas confirman?
¿Los patrones explican los vínculos dañados?
¿Lo que necesita emocionalmente contradice lo que persigue racionalmente?
```

**PASO 4: GENERALIZAR**
```
¿Esta dinámica es personal o le pasa a toda persona en esta posición?
¿Hay algo universal en este conflicto — algo humano, no individual?
```

**PASO ∞: FRONTERA**
```
¿Estoy psicologizando un problema que es estructural?
¿Las emociones son la causa o el síntoma?
¿Entender lo que siente resuelve algo, o solo lo nombra?
```

---

### INT-09: LINGÜÍSTICA

**PASO 0: EXTRAER — mapear el lenguaje**
```
¿Qué palabras usa y cuáles evita?
¿Qué metáfora gobierna su relato — guerra, viaje, construcción, supervivencia?
¿Quién es el sujeto de sus frases — "yo decido" o "hay que", "se debe"?
¿Qué nombra con precisión y qué deja vago?
¿Hay alguna palabra que repite sin notar que la repite?
¿Qué palabra falta — qué no ha nombrado que está presente?
```

**PASO 1: CRUZAR — lenguaje × realidad**
```
¿El nombre que le da al problema define qué soluciones puede imaginar?
¿Si cambiara la palabra clave, cambiaría lo que puede pensar?
¿Dice "crecer" cuando quiere decir "sobrevivir"?
¿Dice "elegir" cuando ya eligió?
¿Su lenguaje agranda o achica el problema?
```

**PASO 2: LENTES**

L1 Marco:
```
¿Qué marco impone el lenguaje usado — problema/solución, batalla/victoria, inversión/retorno?
¿Ese marco ayuda o limita?
¿Qué alternativas de marco existen — y qué harían visible?
```

L2 Actos de habla:
```
¿Está describiendo, pidiendo, prometiendo, amenazando o justificando?
¿Lo que dice intenta informar o convencer?
¿Hay algo performativo — algo que al decirlo, lo crea?
```

L3 Metáforas:
```
¿Qué metáfora vive en su lenguaje sin que la elija?
¿Esa metáfora tiene lógica propia — qué implica que no dice?
¿Una metáfora diferente cambiaría lo que puede ver?
```

L4 Silencios:
```
¿Qué no dice?
¿Lo que no dice es porque no lo piensa, no lo sabe, o no quiere verlo?
¿El silencio protege a alguien — a él mismo, a otro?
```

**PASO 3: ∫**
```
¿El marco, los actos de habla, las metáforas y los silencios cuentan la misma historia?
¿O hay contradicción entre lo que el marco dice y lo que los silencios ocultan?
```

**PASO 4: GENERALIZAR**
```
¿Este tipo de lenguaje es propio de este caso o de toda persona en esta situación?
¿El idioma mismo condiciona — se diría diferente en otro idioma?
```

**PASO ∞: FRONTERA**
```
¿Nombrar el problema lo resuelve o solo da la ilusión de control?
¿El análisis lingüístico añade comprensión o añade distancia?
¿A veces la palabra correcta es la que no se dice?
```

### CATEGORÍA V: CORPORALES

---

### INT-10: CINESTÉSICA

**PASO 0: EXTRAER — mapear el cuerpo**
```
¿Dónde se acumula tensión en este sistema — qué parte no descansa nunca?
¿Hay flujo — las cosas se mueven con ritmo o a tirones?
¿El ritmo actual es sostenible o se acelera hacia el colapso?
¿Qué parte del sistema está rígida — no se adapta, no se ajusta?
¿Hay algo que el cuerpo (la operación diaria) sabe que la mente (el plan) ignora?
```

**PASO 1: CRUZAR — tensión × ritmo**
```
¿Las zonas de tensión coinciden con las de mayor actividad o con las de mayor bloqueo?
¿El ritmo está impuesto desde fuera o es natural del sistema?
¿Si el ritmo bajara un 20%, qué mejoraría y qué empeoraría?
¿La rigidez protege algo o solo impide movimiento?
```

**PASO 2: LENTES**

L1 Tensión:
```
¿Dónde está la contracción — qué se aprieta, se endurece, se resiste?
¿Esa tensión es productiva (como un músculo trabajando) o dañina (como un nudo)?
¿Si soltara esa tensión, qué pasaría?
```

L2 Flujo:
```
¿Qué se mueve con facilidad y qué se atasca?
¿Los atascos son por falta de capacidad o por bloqueo?
¿Hay movimientos innecesarios — esfuerzo que no produce resultado?
```

L3 Ritmo:
```
¿Hay ciclos naturales — momentos de esfuerzo y momentos de descanso?
¿Se respetan esos ciclos o se fuerza producción constante?
¿Cuándo fue la última pausa genuina?
```

L4 Coordinación:
```
¿Las partes se mueven juntas o cada una por su lado?
¿Hay sincronía o hay choque entre tiempos diferentes?
¿Quién marca el ritmo y quién lo sufre?
```

**PASO 3-4-∞:**
```
∫: ¿La tensión causa los atascos, los atascos rompen el ritmo, y el ritmo roto descoordina todo?
Abstraer: ¿Todo sistema que opera sin descanso acumula esta cascada?
Frontera: ¿El cuerpo tiene sabiduría que el análisis no puede capturar?
```

---

### INT-11: ESPACIAL

**PASO 0: EXTRAER — mapear el espacio**
```
¿Si dibujaras este problema, qué forma tendría?
¿Qué está cerca de qué — qué está lejos?
¿Hay centro y periferia — o todo está al mismo nivel?
¿Qué escala tiene — es un problema de mesa o de mapa?
¿Desde qué perspectiva se está mirando — y qué oculta esa perspectiva?
```

**PASO 1: CRUZAR — forma × perspectiva**
```
¿La forma cambia si te acercas o te alejas?
¿Hay simetría — o una parte es muy diferente de la otra?
¿Las proporciones son correctas — algo ocupa mucho espacio y aporta poco?
¿Hay zonas vacías que deberían estar llenas, o llenas que deberían estar vacías?
```

**PASO 2: LENTES**

L1 Topografía:
```
¿Hay picos y valles — puntos altos y bajos?
¿Hay pendientes — zonas donde todo se desliza en una dirección?
¿Hay mesetas — zonas donde no importa lo que hagas, nada cambia?
```

L2 Fronteras:
```
¿Dónde están los bordes — qué está dentro y qué fuera?
¿Las fronteras son permeables o rígidas?
¿Algo que debería estar dentro está fuera, o viceversa?
```

L3 Perspectiva:
```
¿Cómo se ve desde arriba — el mapa completo?
¿Cómo se ve desde dentro — la experiencia vivida?
¿Cómo se ve desde fuera — un observador neutral?
¿Las tres perspectivas cuentan la misma historia?
```

L4 Proporción:
```
¿El tamaño de cada parte corresponde a su importancia?
¿Algo pequeño tiene impacto desproporcionado?
¿Algo grande no produce casi nada?
```

**PASO 3-4-∞:**
```
∫: ¿La topografía explica las fronteras, y la perspectiva revela proporciones ocultas?
Abstraer: ¿Este mapa se parece a otros mapas conocidos?
Frontera: ¿Hay procesos que no tienen forma — que el espacio no puede capturar?
```

---

### CATEGORÍA VI: TEMPORALES

---

### INT-12: NARRATIVA

**PASO 0: EXTRAER — mapear la historia**
```
¿Quién es el protagonista de esta historia — y quién cree él que es?
¿Cuál es el conflicto central — qué quiere vs qué le impide?
¿En qué momento de la historia estamos — inicio, nudo, clímax, desenlace?
¿Cuál es el acto anterior que llevó hasta aquí?
¿Hay un mentor, un antagonista, un aliado — quién cumple cada rol?
```

**PASO 1: CRUZAR — historia × identidad**
```
¿La historia que se cuenta a sí mismo coincide con lo que hacen los hechos?
¿Se ve como héroe, víctima, mártir, constructor?
¿Ese rol elegido lo libera o lo atrapa?
¿Hay otra historia posible con los mismos hechos — donde el protagonista tiene otro rol?
```

**PASO 2: LENTES**

L1 Arco:
```
¿Cuál es la transformación pendiente — qué tiene que cambiar el protagonista?
¿Lo sabe, lo intuye, o lo niega?
¿Qué precio tiene esa transformación — qué debe dejar atrás?
```

L2 Estructura:
```
¿Esta historia tiene actos claros o es un ciclo sin avance?
¿Hay un punto de no retorno — una decisión que cambiará todo?
¿Ya pasó y no se dio cuenta?
```

L3 Personajes:
```
¿Cada persona en el caso cumple un rol narrativo — cuál?
¿Alguien está atrapado en un rol que no eligió?
¿Quién tiene la llave de la resolución y no la usa?
```

L4 Significado:
```
¿Qué sentido tiene esta historia para quien la vive?
¿Es una historia de superación, de pérdida, de aprendizaje?
¿El sentido que le da lo ayuda o lo limita?
```

**PASO 3-4-∞:**
```
∫: ¿El arco, la estructura, los personajes y el significado apuntan al mismo desenlace?
Abstraer: ¿Esta historia es un arquetipo conocido — cuál?
Frontera: ¿La vida necesita historia, o la narrativa impone orden donde hay caos?
```

---

### INT-13: PROSPECTIVA

**PASO 0: EXTRAER — mapear futuros**
```
¿Cuáles son las tendencias en curso — qué se mueve y hacia dónde?
¿Cuáles son aceleradas (crecen) y cuáles deceleradas (se frenan)?
¿Hay señales débiles — cosas pequeñas que podrían ser el inicio de algo grande?
¿Qué asume todo el mundo que seguirá igual — y qué tan seguro es eso?
```

**PASO 1: CRUZAR — tendencias × supuestos**
```
¿Qué pasa si dos tendencias que ahora van separadas se cruzan?
¿Hay supuestos que si caen, cambian todo el panorama?
¿Las señales débiles apuntan en la misma dirección o en direcciones opuestas?
¿Algo que parece estable tiene fecha de caducidad?
```

**PASO 2: LENTES**

L1 Escenarios:
```
¿Cuál es el mejor caso realista — no fantasía, realista?
¿Cuál es el peor caso realista?
¿Cuál es el caso más probable si nada cambia?
¿Hay un escenario que nadie considera pero que es posible?
```

L2 Señales:
```
¿Qué señal aparecería primero si vamos hacia el mejor caso?
¿Y hacia el peor?
¿Esas señales ya están apareciendo?
¿Alguien las está monitorizando?
```

L3 Bifurcaciones:
```
¿Hay un punto donde el camino se divide — una decisión que lleva a futuros muy diferentes?
¿Cuándo es ese punto — ya pasó, está aquí, o viene?
¿Es reversible — si eliges un camino, puedes volver?
```

L4 Comodines:
```
¿Qué podría pasar que no está en ningún modelo?
¿Un evento improbable pero de alto impacto — cuál sería?
¿Estás preparado para lo inesperado o solo para lo esperado?
```

**PASO 3-4-∞:**
```
∫: ¿Los escenarios, señales, bifurcaciones y comodines convergen en algún patrón?
Abstraer: ¿Este tipo de encrucijada tiene precedentes — qué pasó?
Frontera: ¿El futuro es predecible o el acto de predecir cambia lo que pasará?
```

---

### CATEGORÍA VII: CREATIVAS

---

### INT-14: DIVERGENTE

**PASO 0: EXTRAER — abrir posibilidades**
```
¿Cuántas opciones ve esta persona — y cuántas más existen?
¿Qué opciones descartó sin examinar — y por qué?
¿Qué pasaría si la restricción más obvia no existiera?
¿Qué haría alguien completamente diferente en esta situación?
¿Qué haría si tuviera el doble de recursos? ¿Y la mitad?
```

**PASO 1: CRUZAR — opciones × restricciones**
```
¿Las restricciones son reales o asumidas?
¿Hay opciones que parecen locas pero son viables si las miras bien?
¿Qué pasa si combinas dos opciones que parecen incompatibles?
¿Hay una opción que nadie ha mencionado porque parece obvia-pero-no?
```

**PASO 2: LENTES**

L1 Volumen:
```
¿Puedes generar 10 opciones más en 2 minutos — sin filtrar?
¿Y 10 más que sean lo opuesto de las primeras 10?
¿Qué tienen en común las que te gustan — y qué te dice eso?
```

L2 Combinación:
```
¿Qué pasa si mezclas la opción A con la C?
¿Hay una solución de otro dominio que podría funcionar aquí?
¿Qué haría un niño? ¿Un artista? ¿Un alien?
```

L3 Inversión:
```
¿Y si haces exactamente lo opuesto de lo que "deberías"?
¿Y si el problema es la solución y la solución es el problema?
¿Qué pasa si en lugar de resolver, amplías?
```

L4 Restricción creativa:
```
¿Si SOLO pudieras hacer UNA cosa, cuál sería?
¿Si tuvieras que resolver esto en 24h, qué harías?
¿Si no pudieras usar dinero, qué usarías?
```

**PASO 3-4-∞:**
```
∫: ¿De todas las opciones generadas, cuáles aparecen desde múltiples lentes?
Abstraer: ¿Las mejores opciones comparten alguna estructura común?
Frontera: ¿Generar opciones es avanzar o es evitar elegir?
```

---

### INT-15: ESTÉTICA

**PASO 0: EXTRAER — mapear coherencia**
```
¿Algo en este caso "suena raro" — algo no encaja aunque no sepas qué?
¿Hay elegancia — partes que funcionan con simplicidad y gracia?
¿Hay disonancia — partes que chocan entre sí?
¿El problema tiene simetría o está desequilibrado?
¿La forma del problema y la forma de la solución propuesta son coherentes?
```

**PASO 1: CRUZAR — forma × contenido**
```
¿Lo que dice y cómo lo dice son coherentes?
¿La solución que propone tiene la misma forma que el problema — repite el patrón?
¿Hay algo bello en el problema — alguna estructura elegante, aunque sea dolorosa?
¿La complejidad es necesaria o es ruido?
```

**PASO 2: LENTES**

L1 Armonía:
```
¿Las partes se complementan o se contradicen?
¿Hay proporción — cada parte tiene el peso justo?
¿Algo sobra? ¿Algo falta?
```

L2 Tensión:
```
¿Dónde está la tensión productiva — la que genera energía?
¿Dónde está la tensión destructiva — la que gasta sin producir?
¿La tensión se resuelve o es permanente?
```

L3 Simplicidad:
```
¿Cuál es la versión más simple de este problema que conserva lo esencial?
¿Qué se puede quitar sin perder nada?
¿Lo que queda después de quitar todo lo superfluo — qué es?
```

L4 Resonancia:
```
¿Este caso produce una reacción inmediata — algo que se siente antes de pensarse?
¿Esa reacción es informativa — dice algo que el análisis no puede decir?
¿Hay verdad en la primera impresión que el análisis posterior ignora?
```

**PASO 3-4-∞:**
```
∫: ¿La armonía, la tensión, la simplicidad y la resonancia apuntan al mismo sitio?
Abstraer: ¿Los problemas bellos tienen mejores soluciones que los feos?
Frontera: ¿La estética es guía de verdad o sesgo hacia lo bonito?
```

---

### INT-16: CONSTRUCTIVA

**PASO 0: EXTRAER — mapear restricciones**
```
¿Qué tiene que funcionar al final — cuál es el criterio de éxito?
¿Con qué materiales cuentas — dinero, tiempo, personas, herramientas?
¿Qué restricciones son inamovibles y cuáles son flexibles?
¿Hay algo que ya funciona y se puede reutilizar?
¿Qué ha fallado antes — qué se intentó y no sirvió?
```

**PASO 1: CRUZAR — objetivo × restricciones**
```
¿El objetivo es alcanzable con los materiales disponibles?
¿Si no alcanza, ¿qué falta — más de qué?
¿Hay formas de reducir el objetivo sin perder lo esencial?
¿Las restricciones reales son menos de las que cree?
```

**PASO 2: LENTES**

L1 Prototipo:
```
¿Cuál es la versión más pequeña que se puede construir y probar?
¿Qué aprenderías construyendo eso?
¿Cuánto cuesta y cuánto tiempo lleva?
```

L2 Secuencia:
```
¿Qué se construye primero — qué es el cimiento?
¿Qué depende de qué — qué no puedes hacer hasta tener X?
¿Hay un camino crítico — una secuencia que determina el tiempo total?
```

L3 Fallo:
```
¿Qué se va a romper primero?
¿Puedes diseñar para que falle de forma segura?
¿Dónde necesitas margen y dónde puedes ajustar?
```

L4 Iteración:
```
¿Esto se construye de una vez o por versiones?
¿Qué aprende cada versión que la anterior no sabía?
¿Cuántas iteraciones son necesarias para que funcione bien?
```

**PASO 3-4-∞:**
```
∫: ¿El prototipo, la secuencia, los modos de fallo y la iteración son coherentes?
Abstraer: ¿Hay un principio de ingeniería que gobierna este problema?
Frontera: ¿Construir mejor lo existente es la respuesta, o hay que construir otra cosa?
```

---

### CATEGORÍA VIII: EXISTENCIALES

---

### INT-17: EXISTENCIAL

**PASO 0: EXTRAER — lo que está en juego**
```
¿Qué está en juego aquí realmente — no lo que se dice, lo que está en juego de verdad?
¿Qué se perdería si no haces nada?
¿Qué se perdería si haces lo que "deberías"?
¿Cuál de las dos pérdidas pesa más — y quién decide eso?
```

**PASO 1: CRUZAR — valores × vida**
```
Lo que dices que valoras, ¿coincide con dónde pones tu tiempo?
¿Hay algo que dices que no importa pero que te quita el sueño?
¿Hay algo que dices que importa mucho pero a lo que dedicas cero?
¿La distancia entre lo declarado y lo vivido — es grande o pequeña?
```

**PASO 2: LENTES**

L1 Propósito:
```
¿Para qué haces lo que haces — la razón profunda, no la práctica?
¿Si ya tuvieras suficiente dinero, seguirías haciendo esto?
¿Lo haces porque quieres o porque sientes que debes?
```

L2 Finitud:
```
¿Cuánto tiempo te queda para lo que importa?
¿Ese tiempo es recuperable si lo pierdes ahora?
¿Lo que ganas compensa lo que pierdes — sabiendo que lo perdido no vuelve?
```

L3 Libertad:
```
¿Estás eligiendo o siguiendo inercia?
¿Cuándo fue la última vez que elegiste activamente?
¿Puedes decir "no" sin que pase nada malo?
Si puedes decir "no" y no lo haces — ¿por qué?
```

L4 Responsabilidad:
```
¿Ante quién eres responsable — y en qué orden?
¿Quién viene primero? ¿Quién debería venir primero?
¿Coinciden las dos respuestas?
```

**PASO 3-4-∞:**
```
∫: ¿El propósito justifica el sacrificio sabiendo que el tiempo no vuelve?
Abstraer: ¿Esto le pasa a todo humano en tu posición, o es único?
Frontera: ¿Todas estas preguntas son otra forma de no decidir?
```

---

### INT-18: CONTEMPLATIVA

**PASO 0: EXTRAER — lo que es**
```
¿Qué hay aquí, ahora, tal como es — sin interpretación?
¿Puedes describir la situación sin juzgarla como buena o mala?
¿Qué se siente al simplemente estar con esto — sin resolver?
¿Hay prisa real o la urgencia es inventada?
```

**PASO 1: CRUZAR — observación × impulso**
```
¿El impulso de actuar viene de la situación o del miedo a no actuar?
¿Qué pasaría si esperas — no por indecisión, sino por observación?
¿Hay sabiduría en la pausa que la acción destruiría?
¿El problema necesita resolverse o necesita ser sostenido?
```

**PASO 2: LENTES**

L1 Presencia:
```
¿Estás aquí o estás en el futuro — preocupado por lo que vendrá?
¿Puedes volver a ahora — a lo que hay, no a lo que temes?
¿Qué sabes cuando paras de pensar y simplemente miras?
```

L2 Paradoja:
```
¿Las dos opciones que parecen opuestas pueden ser verdad a la vez?
¿Puedes sostener la contradicción sin necesitar resolverla?
¿Qué emerge si no eliges — si dejas que la tensión se sostenga?
```

L3 Soltar:
```
¿Qué estás agarrando que necesitas soltar?
¿Qué pasaría si dejas de intentar controlar esto?
¿El control es real o es ilusión de control?
```

L4 Vacío:
```
¿Hay espacio en este sistema — lugar para que algo nuevo emerja?
¿O está todo tan lleno que nada nuevo puede entrar?
¿Qué necesita vaciarse para que algo mejor ocupe su lugar?
```

**PASO 3-4-∞:**
```
∫: ¿La presencia, la paradoja, el soltar y el vacío apuntan al mismo silencio?
Abstraer: ¿Toda crisis tiene un momento donde parar es más valiente que actuar?
Frontera: ¿La contemplación es sabiduría o es privilegio de quien puede permitirse esperar?
```

---

## 5. TIPOS DE PENSAMIENTO COMO PREGUNTAS

### 5.1 PENSAMIENTO INTERNO (dentro de cada álgebra)

**T01 — PERCEPCIÓN** (iso(S))
```
¿Qué forma tiene esto?
¿Qué estructura se hace visible cuando miro con esta lente?
¿Qué era invisible antes de mirar así?
```

**T02 — CAUSALIDAD** (B(iso(S)))
```
¿Por qué esta forma existe y no otra?
¿Qué la produjo?
¿Qué la mantiene?
¿Qué la destruiría?
```

**T03 — ABSTRACCIÓN** (iso²)
```
¿Qué se repite aquí — independiente del contenido?
¿Si quito los nombres, ¿qué patrón queda?
¿Ese patrón aparece en otro nivel del mismo caso?
```

**T04 — SÍNTESIS** (∫)
```
¿Qué emerge al ver todo junto que ninguna vista ve sola?
¿Hay conexiones entre respuestas que nadie preguntó?
¿Las respuestas parciales se contradicen o se refuerzan?
```

**T05 — DISCERNIMIENTO** (A−B)
```
¿Qué puede ver esta mirada que aquella NO PUEDE — no por omisión, por construcción?
¿Es porque le falta vocabulario, objetos, o la operación necesaria?
¿Son complementarias o redundantes?
```

**T06 — METACOGNICIÓN** (crítico)
```
¿Qué no puede ver todo lo que hemos hecho?
¿Qué premisa asumimos sin examinar?
¿Estamos haciendo exactamente lo que diagnosticamos?
¿Hay una pregunta que este marco no puede formular?
```

**T07 — CONSCIENCIA EPISTEMOLÓGICA** (iso(M))
```
¿Qué forma tiene mi propia explicación?
¿Mi explicación repite la estructura del problema sin notarlo?
¿Si le aplico mi propia lente a mi respuesta, ¿qué veo?
```

**T08 — AUTO-DIAGNÓSTICO** (B(iso(M)))
```
¿Por qué mi explicación tiene esta forma y no otra?
¿Qué en mi herramienta produce este tipo de explicación?
¿Un analista con otra herramienta produciría una explicación diferente — cuál?
```

**T09 — CONVERGENCIA** (∫(M₁|M₂|M₃))
```
¿Qué comparten todas mis explicaciones que ninguna dice sola?
¿Hay un meta-patrón debajo de todas las explicaciones parciales?
¿Si pudiera decirlo en una frase, qué diría?
```

**T10 — DIALÉCTICA** (A→B→C→A')
```
¿Qué veo de mi propia mirada después de que otros la transformaron?
¿Mi percepción original cambia al verla explicada por otra lente?
¿Qué sé ahora que no sabía en la primera pasada — y que no podía saber sin el recorrido?
```

### 5.2 PENSAMIENTO LATERAL (cruza el perímetro)

**T11 — ANALOGÍA** (≅)
```
¿Esta forma se parece a algo que existe en otro dominio completamente diferente?
¿Qué se sabe en ese otro dominio que aquí no se ha aplicado?
¿La analogía ilumina o engaña — dónde se rompe?
```

**T12 — CONTRAFACTUAL** (Δ)
```
¿Qué pasaría si quito la pieza más importante del sistema?
¿Y si cambio una variable clave por su opuesta?
¿La forma sobrevive al cambio o colapsa? Si colapsa, esa pieza era estructural.
¿Qué pasaría si esto hubiera empezado de otra manera?
```

**T13 — ABDUCCIÓN** (←)
```
Dada esta forma, ¿qué tipo de caso la produce?
¿Qué condiciones son necesarias para que este patrón aparezca?
¿Es esta persona/situación una instancia de una clase más amplia?
¿Qué otros miembros de esa clase conozco — y qué pasó con ellos?
```

**T14 — PROVOCACIÓN** (⊕)
```
¿Y si hago exactamente lo opuesto de lo que "debería"?
¿Y si introduzco algo que no tiene nada que ver — qué reorganiza?
¿Qué haría un loco? ¿Y un genio? ¿Y un niño?
¿Qué opción NO estoy considerando porque parece absurda?
```

**T15 — REENCUADRE** (iso_X)
```
¿Qué vería aquí una lente que no pertenece a este problema?
¿Si esto fuera música — dónde está la disonancia?
¿Si esto fuera un cuerpo — dónde está la enfermedad?
¿Si esto fuera una historia — en qué acto estamos?
¿La lente nueva ve algo que las habituales no pueden?
```

**T16 — DESTRUCCIÓN CREATIVA**
```
¿Y si el marco entero es incorrecto?
¿Y si analizar es precisamente lo que NO necesita?
¿Hay algo más simple, más directo, más humano que todo este aparato?
¿Qué pasaría si tiro todo el análisis y actúo desde la intuición?
```

**T17 — CREACIÓN**
```
¿Qué sistema cumpliría los requisitos sin los problemas actuales?
Si empezara de cero — sin historia, sin inercia — ¿qué construiría?
¿Qué necesita existir que no existe?
¿Puedo diseñarlo — y qué restricciones no negociables tiene?
```

---

## 6. PROPIEDADES ALGEBRAICAS COMO PREGUNTAS

**P01 — Conmutativa (A|B = B|A)**
```
¿Cambia el resultado si primero miro X y luego Y, o al revés?
Si no cambia → son independientes.
Si cambia → el orden de percepción afecta lo que ves.
```

**P02 — No conmutativa (A→B ≠ B→A)**
```
¿Produce lo mismo explicar la forma de A con la lente B que la forma de B con A?
¿Qué se ve diferente al invertir el orden?
¿Cuál de los dos órdenes revela más?
```

**P03 — Asociativa ((A→B)→C = A→(B→C))**
```
¿Importa cómo agrupo los pasos o solo importa la secuencia?
¿Puedo reorganizar el trabajo sin cambiar el resultado?
```

**P04 — Distributiva izquierda (A→(B|C) = (A→B)|(A→C))**
```
¿Puedo partir este trabajo en paralelo partiendo del mismo punto?
¿Obtengo lo mismo que si lo hago todo junto?
Si sí → puedo ahorrar. Si no → hay valor irreducible en lo junto.
```

**P05 — NO distributiva derecha ((B|C)→A ≠ (B→A)|(C→A))**
```
¿Es lo mismo que A vea B y C por separado que verlos juntos?
¿Qué ve A al mirar la combinación que no puede ver mirando cada parte?
¿El cruce tiene valor propio que se pierde al separar?
```

**P06 — No idempotente (A→A ≠ A)**
```
¿Qué pasa si le hago la misma pregunta a la respuesta que obtuve?
¿La segunda vuelta dice algo nuevo o repite?
¿Hay profundidad que la primera pasada no alcanza?
```

**P07 — Saturación (Aⁿ converge)**
```
¿Sigue aportando valor preguntar otra vez?
¿En qué momento la respuesta deja de agregar?
¿Estamos girando en círculos o avanzando en espiral?
```

**P08 — Clausura (output ∈ input)**
```
¿Esta respuesta puede ser la entrada de otra pregunta diferente?
¿Puedo tomar la conclusión de una lente y meterla como dato de otra?
¿Cada respuesta abre nuevas preguntas posibles?
```

**P09 — Sin identidad (∄ I: I→A = A)**
```
¿Existe alguna pregunta que no cambie nada?
¿Alguna mirada que deje los datos exactamente como los encontró?
Si no → toda pregunta transforma. No hay mirada neutra.
```

**P10 — Absorbente diferencial (A-A = ∅)**
```
¿Qué ve esta lente que ella misma no puede ver?
Nada — cada lente es completa respecto a sí misma.
El punto ciego solo aparece desde FUERA.
```

**P11 — Distributiva diferencial (A-(B|C) = (A-B) ∩ (A-C))**
```
Lo exclusivo de A respecto al grupo, ¿es la intersección de lo exclusivo respecto a cada miembro?
¿O el grupo junto tiene capacidades que sus miembros separados no?
```

---

## 7. OPERACIONES INTER-ÁLGEBRA COMO PREGUNTAS

**Fusión de inteligencias: ∫(álgebra_A | álgebra_B)**
```
¿Qué emerge al analizar esto con dos inteligencias diferentes a la vez?
¿Dónde coinciden — y esa coincidencia qué significa?
¿Dónde se contradicen — y esa contradicción qué revela?
¿Hay algo que SOLO aparece al cruzar las dos que ninguna ve sola?
```

**Composición de inteligencias: álgebra_A → álgebra_B**
```
¿Qué ve la inteligencia B al mirar lo que la inteligencia A produjo?
¿La explicación de A tiene una forma que B puede revelar?
¿El diagnóstico de A cambia cuando B lo examina?
```

**Diferencial de inteligencias: álgebra_A − álgebra_B**
```
¿Qué puede ver esta inteligencia que aquella NO PUEDE ver por construcción?
¿Es porque le faltan objetos, operaciones, o la pregunta necesaria?
¿Son complementarias — cada una ve lo que la otra no puede?
¿O son redundantes — ven casi lo mismo con distinto vocabulario?
```

**Clausura inter-álgebra:**
```
¿El output de una inteligencia puede ser input de otra?
¿Qué tipo de inteligencia necesita este output para ser completado?
¿Qué inteligencia falta en la mesa — cuál vería lo que todas juntas siguen sin ver?
```

---

## 8. IMPLICACIONES

### El prompt es una red de preguntas, no una instrucción.
La inteligencia emerge de la ESTRUCTURA de la red, no del contenido de las respuestas.

### El router selecciona redes de preguntas.
No elige "análisis financiero" — elige la red de preguntas financieras + las de operación + las de propiedad.

### Las propiedades son meta-preguntas inyectables en cualquier momento.
"¿Y si invertimos el orden?" se puede preguntar dentro de cualquier inteligencia.

### Las inteligencias se combinan mediante preguntas de operación inter-álgebra.
∫(financiera | existencial)(caso) no es "hacer dos análisis" — es preguntar qué emerge al cruzar las respuestas de dos redes diferentes.

### La meta-red es invariante.
EXTRAER → CRUZAR → PROYECTAR → INTEGRAR → ABSTRAER → LIMITAR.
Cada inteligencia rellena cada paso con preguntas diferentes.
La secuencia no cambia. El contenido sí.

---

**FIN BIBLIOTECA META-RED DE INTELIGENCIAS CR0**



## Motor/Meta-Red de preguntas inteligencias/ALGEBRA_CALCULO_SEMANTICO_CR0.md

# ÁLGEBRA DEL CÁLCULO SEMÁNTICO — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-06
**Origen:** Sesión Opus — diseño de biblioteca de programas del Motor v3.3
**Dependencias:** CIERRE_SESION_2026-03-06_CALCULO_SEMANTICO.md

---

## 1. DEFINICIÓN

El Motor no es un pipeline de análisis. Es una **máquina de cálculo semántico**.

```
ARITMÉTICA CLÁSICA:
  variables:   números
  operaciones: +, -, ×, Σ
  output:      números

CÁLCULO SEMÁNTICO:
  variables:   coordenadas sintácticas (output de primitivas)
  operaciones: fusión (|), composición (→), integración (∫), diferencial (-)
  output:      objetos semánticos de 6 tipos (coordenada → punto ciego)
```

---

## 2. OBJETOS SEMÁNTICOS — qué produce el cálculo

### Nivel 0: COORDENADAS (primitivas — posicionan)

Las 7 primitivas producen 5 tipos de coordenada:

| Tipo | Fuente | Qué produce | Ejemplo (dentista) |
|------|--------|-------------|-------------------|
| C1 COMPRESIÓN | sustantivizar | Nombre a 3 escalas (palabra/frase/párrafo) | "Dilema capacidad-vida" |
| C2 POSICIÓN | adjetivar + adverbializar + verbo | Dónde está cada pieza: id (declarada) vs ir (real) | SACRIFICAR id=0 ir=0.92 |
| C3 RELACIÓN | preposicionar + conjuntar | Cómo se conectan las piezas (y qué conexiones faltan) | "Negocio DENTRO de vida familiar, no al revés" |
| C4 NIVEL | sujeto_predicado | Quién opera sobre quién, con qué poder | Mujer poder=0.2, Banco poder=0.6 |
| C5 DISTANCIA | calculadora ($0, código puro) | Gaps id↔ir + propagaciones + lentes | SACRIFICAR gap=0.92 desinflada |

Las coordenadas no analizan — **posicionan**. Son puntos en un espacio sintáctico.

La distancia id↔ir (C5) es el dato más potente: mide cuánto diverge lo declarado de lo real.


### Nivel 1: HUECOS ACTIVOS (sintetizador — cruza coordenadas)

El sintetizador cruza primitivas y produce lo que ninguna produce sola.

| Tipo | Cruce | Qué produce | Ejemplo (dentista) |
|------|-------|-------------|-------------------|
| H1 INVERSIÓN SEMÁNTICA | C1 × C2 | Lo declarado ≠ lo real | "Elegir" cuando ya eligió |
| H2 FUNCIÓN INVISIBLE | C2 × C5 | Opera con potencia máxima porque no se nombra | SACRIFICAR ir=0.92 id=0 — invisible |
| H3 CONEXIÓN AUSENTE ACTIVA | C3 × H2 | La desconexión sostiene el sistema | "Mantener A, B, C separados es lo que permite que el sacrificio continúe" |

El sintetizador no resume ni comprime. **Cruza coordenadas de distintas dimensiones y produce los puntos donde la realidad declarada diverge de la realidad operativa.**


### Nivel 2: TOPOLOGÍA (1 isomorfismo, 1 loop — proyecta forma)

Cada isomorfismo proyecta una estructura sobre las coordenadas + huecos. No añade datos — reorganiza para hacer visible una FORMA que antes era invisible.

| Tipo | Isomorfismo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------|-------------------|
| T1 CONTENEDORES | conjuntos | Quién contiene a quién, qué se solapa, qué falta | "Negocio dentro de vida familiar, no al revés" + gaps: cálculo horas/vida ausente |
| T2 CIRCUITOS | causal/dinámica | Qué loops existen, si se amplifican o frenan, hacia dónde converge | Loop refuerzo: Margen→Inversión→Más trabajo→Menos vida→Necesidad margen |
| T3 TABLERO | juegos/agentes | Qué jugadores, qué incentivos, quién gana si nadie cambia | Odontólogo 0.55 / Mujer 0.2 / Banco 0.6 / Sistema 0.9 |
| T4 CONTROL | cibernética | Qué mide, qué ajusta, qué señales ignora | Sensores: solo económicos. Feedback mujer: ignorado. Regulación: rígida |

Las topologías son FORMAS proyectadas sobre los mismos datos. Los datos no cambian. Lo que cambia es qué estructura se hace visible.


### Nivel 3: MECANISMO (composición A→B — explica la forma)

Una topología dice QUÉ FORMA tienen los datos. Un mecanismo dice POR QUÉ esa forma existe y no otra.

B opera sobre la topología que A produjo (no sobre los datos originales). Lo que emerge es una EXPLICACIÓN de la forma.

| Composición | Mecanismo | Pregunta que responde | Ejemplo (dentista) |
|-------------|-----------|----------------------|-------------------|
| causal→juegos | M1: MOTOR DEL LOOP | ¿Quién alimenta los circuitos? | Banco inyecta en "Inversión", Sistema normaliza "Más trabajo", Mujer frena pero poder insuficiente |
| conjuntos→causal | M2: CAUSA DE LA FORMA | ¿Qué produce la estructura de contención? | Nunca se calculó tasa tiempo→dinero, negocio se expande sin frontera |
| juegos→cibernética | M3: REGULACIÓN DEL JUEGO | ¿Qué impide que los jugadores cambien? | Odontólogo solo tiene sensor económico. Feedback vital no llega a actuador |
| causal→conjuntos | M4: FRONTERA DE CIRCULACIÓN | ¿Qué entra en los loops y qué queda fuera? | Familia/hijos/salud están FUERA de todos los loops de decisión |
| cibernética→causal | M5: LOOPS DE CONTROL | ¿Qué loops genera la regulación misma? | Medir solo dinero→decidir por dinero→refuerza medir solo dinero |

La composición NO es conmutativa: causal→juegos ≠ juegos→causal.

Con 4 isomorfismos de topología hay hasta 12 composiciones de 2 (4×3). No todas producen valor equivalente. El diferencial (sección 4) determina cuáles son redundantes.


### Nivel 4: INVARIANTE (recursión A² — estructura que se replica)

Recursión = isomorfismo comiendo su propio output. Sube de nivel lógico.

| Tipo | Recursión | Qué produce | Ejemplo (dentista) |
|------|-----------|-------------|-------------------|
| I1 CONTENCIÓN REPLICADA | conjuntos² | "Estar dentro sin verlo" se repite a cada escala | M2 dentro de paradigma = negocio dentro de vida familiar |
| I2 CIRCUITO REPLICADO | causal² | El mismo tipo de loop a cada nivel | "Diagnóstico preciso→Soluciones dentro del paradigma→Problema intacto→Más diagnóstico" |
| I3 JUGADOR INVISIBLE | juegos² | El agente con más poder es el menos nombrado, siempre | Nivel 1: "Sistema" poder=0.9. Nivel 2: "Paradigma-crecimiento" poder=0.95 |
| I4 SENSOR CIEGO | cibernética² | No mide lo que más importa, a cada nivel | Dentista no mide vida. M2 no mide sus propias premisas |

El invariante NO es el contenido. Es la **estructura que se repite independientemente del nivel en que opera**.

**Saturación (rendimiento por loop):**

| Loops | Valor marginal | Qué produce |
|-------|---------------|-------------|
| 1 | 100% | Topología (forma de los datos) |
| 2 | ~60-70% | Invariante (estructura que se replica) |
| 3 | ~10-15% | Meta-invariante (confirmación + matiz) |
| 4+ | ~0-5% | Convergencia (saturación) |


### Nivel ∞: PUNTO CIEGO (crítico — frontera del análisis)

Crítico no produce topología ni mecanismo. Produce FRONTERA: el límite de lo que todo lo anterior puede ver.

| Tipo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------------|
| P1 PREMISA OCULTA | Algo que todo el análisis asume sin examinar | "M2 asume que 'crecer' es necesario" |
| P2 PARADOJA PERFORMATIVA | El análisis hace exactamente lo que diagnostica | "Precisión técnica M2 = ceguera sistémica sobre sí mismo" |
| P3 FRONTERA DE MARCO | Lo que este marco no puede ver por construcción | "¿Y si 7K€/mes con vida familiar ES el éxito?" |

Crítico siempre es último y siempre vale la pena. Es el único isomorfismo que nunca es redundante.

---

## 3. OPERACIONES — las 4 operaciones del cálculo

### 3.1 FUSIÓN (|) — como suma

Dos o más isomorfismos operan en **paralelo** sobre el MISMO input. Producen topologías independientes.

```
causal|juegos(datos) → T2 + T3 (dos topologías independientes)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | Sí: A\|B = B\|A |
| Asociativa | Sí: (A\|B)\|C = A\|(B\|C) |
| Inverso (resta) | No existe como operación. Sí existe como contribución marginal |

**Contribución marginal** (sustituto de la resta):
```
∫(A|B|C) vs ∫(A|B) → diferencia = contribución marginal de C
```
Testeable: si quitas un isomorfismo de la fusión y la integración apenas cambia, ese isomorfismo es redundante para ese input.


### 3.2 COMPOSICIÓN (→) — como multiplicación

Un isomorfismo opera sobre el **output** de otro. Produce mecanismo (nivel 3).

```
juegos→causal(datos) = juegos(causal(datos))
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A→B ≠ B→A |
| Asociativa | Sí: (A→B)→C = A→(B→C) — la secuencia es la misma |
| Inverso (división) | No existe. La composición no es reversible |
| Trazabilidad | Sí: puedes ejecutar A, luego A→B, y ver qué transformó cada paso |

**Propiedad distributiva izquierda:**
```
A→(B|C) = (A→B) | (A→C)
```
Permite **factorizar programas**: ejecutar A una vez y fan-out en paralelo.

```
SIN FACTORIZAR:                    FACTORIZADO:
  causal→juegos      (2 calls)      causal→(juegos|conjuntos|cibernética)
  causal→conjuntos   (2 calls)      = 1 × causal + 3 paralelo
  causal→cibernética (2 calls)      = 4 calls (vs 6)
  = 6 calls total
```

**NO distributiva por la derecha:**
```
(B|C)→A ≠ (B→A) | (C→A)
```
En (B|C)→A, el agente A ve la fusión junta — puede cruzar. En (B→A)|(C→A), ve cada una por separado — no cruza. El cruce tiene valor irreducible.


### 3.3 INTEGRACIÓN (∫) — como sumatorio Σ

Un agente mira TODAS las topologías de una fusión simultáneamente. Produce CRUCE: conexiones entre topologías que ninguna ve sola.

```
∫(causal|juegos|conjuntos|cibernética)(datos) → cruce
```

Esto es lo que M2 hace hoy: 4 isomorfismos fusionados + una síntesis que cruza los 4 outputs.

No es suma (eso es fusión). No es composición (no hay secuencia). Es **reducción**: colapsa una colección en un objeto nuevo.


### 3.4 DIFERENCIAL (-) — como resta

Lo que A ve que B NO puede ver. Mide el valor único de cada isomorfismo.

```
Juegos - Cibernética = incentivos puros (motivación independiente de regulación)
Cibernética - Juegos = regulación pura (control independiente de jugadores)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A-B ≠ B-A |
| Asociativa | No: (A-B)-C ≠ A-(B-C) |
| Elemento absorbente | A-A = ∅ (cada isomorfismo es completo respecto a sí mismo) |
| Distributiva sobre fusión | A-(B\|C) = (A-B) ∩ (A-C) |

**Uso principal:** determinar redundancia. Si A-B es pequeño → A y B son redundantes (ven casi lo mismo). Si A-B es grande → son complementarios (cada uno ve cosas que el otro no puede).


### 3.5 Tabla resumen

```
OPERACIÓN     SÍMBOLO   ARITMÉTICA     CONMUT.  ASOC.  INVERSO    DISTRIB.
──────────────────────────────────────────────────────────────────────────────
Fusión          |       Suma           Sí       Sí     No*        —
Composición     →       Multiplicación No       Sí     No**       → sobre | (izq)
Integración     ∫       Sumatorio Σ    N/A      N/A    No         N/A
Diferencial     -       Resta          No       No     A-A=∅      - sobre | (∩)

*   Contribución marginal como sustituto medible
**  Descomposición/trazabilidad como sustituto
```

---

## 4. PROPIEDADES ALGEBRAICAS

| Propiedad | Valor | Implicación |
|-----------|-------|-------------|
| No conmutativa (→) | A→B ≠ B→A | El orden importa |
| No asociativa (-) | (A-B)-C ≠ A-(B-C) | La agrupación del diferencial importa |
| Asociativa (→) | (A→B)→C = A→(B→C) | La secuencia de composición no depende de paréntesis |
| No idempotente | A→A ≠ A | La recursión produce nuevo (invariantes) |
| Clausura | output ∈ input | Se puede seguir operando siempre |
| Saturación | A^n converge (n≈2 útil) | La profundidad útil es finita |
| Absorbente parcial | Crítico siempre produce punto ciego | El tipo de output es constante, el contenido varía |
| Sin identidad | ∄ I: I→A = A | Cada paso transforma, no hay operación neutra |
| Distributiva izq. | A→(B\|C) = (A→B)\|(A→C) | Factorizar programas: misma semántica, menor coste |
| No distributiva der. | (B\|C)→A ≠ (B→A)\|(C→A) | La integración post-fusión no se descompone |
| Distributiva diferencial | A-(B\|C) = (A-B) ∩ (A-C) | El valor único respecto a un grupo = intersección de diferenciales |

---

## 5. EXPRESIONES — programas escritos en el álgebra

### El Motor v3.3 actual:

```
M1 = primitivas(input)                           → C1-C5
S  = sintetizador(M1)                             → H1-H3
M2 = ∫(conjuntos|causal|juegos|cibernética)(S)    → T1-T4 + cruce
M3 = ∫(conj²|caus²|jueg²|ciber²)(M2)              → I1-I4 + P1-P3

Compacto: ∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
Coste: $0.91 | 293s | 3 Opus + 91 Haiku
```

### Programas posibles:

| Programa | Expresión | Produce | Coste est. |
|----------|-----------|---------|-----------|
| Triage rápido | primitivas(input) | C1-C5 | ~$0.03 |
| Detección huecos | sint(prim(input)) | C1-C5 + H1-H3 | ~$0.34 |
| Vista 1 dimensión | iso(sint(prim(input))) | 1 Topología | ~$0.15 |
| Cruce multi-dim | ∫(iso₁\|iso₂)(sint(prim(input))) | Topologías + cruce | ~$0.25-0.45 |
| Explicar 1 forma | isoA→isoB(sint(prim(input))) | 1 Mecanismo | ~$0.25 |
| Detectar patrón | iso²(sint(prim(input))) | 1 Invariante | ~$0.25 |
| + Punto ciego | X→crítico | + P1-P3 | +$0.10 |
| Máxima potencia | ∫(iso²)(∫(iso)(sint(prim(input)))) | Todo | ~$0.91 |

### Formato de programa (receta):

```json
{
  "nombre": "diagnostico_estructural_profundo",
  "expresion": "∫(iso²)(∫(iso)(sintetizador(primitivas(input))))",
  "primitivas": ["todas"],
  "programa": [
    {"paso": 1, "op": "|", "iso": ["conjuntos","causal","juegos","cibernetica"]},
    {"paso": 2, "op": "∫"},
    {"paso": 3, "op": "²", "loops": 2},
    {"paso": 4, "op": "∫"}
  ],
  "coste_estimado": "$0.91",
  "produce": ["C1-C5", "H1-H3", "T1-T4", "I1-I4", "P1-P3"],
  "cuando_usar": "Decisiones estratégicas con múltiples tensiones",
  "cuando_NO_usar": "Preguntas operativas simples"
}
```

---

## 6. HERRAMIENTAS DE OPTIMIZACIÓN

**Factorización (distributiva izquierda):**
Si un programa ejecuta A→B, A→C, A→D por separado, factorizar a A→(B|C|D) produce el mismo resultado con menos coste.

**Contribución marginal (sustituto de inverso en fusión):**
Ejecutar ∫ con y sin un isomorfismo. Si la diferencia es mínima → redundante → eliminable.

**Diferencial (valor único):**
Calcular A-B y B-A. Si ambos son grandes → complementarios (mantener). Si alguno es pequeño → redundante (uno cubre al otro).

**Saturación (profundidad óptima):**
Loops=2 máximo por defecto. Loops=3 solo con justificación explícita.

---

## 7. NOTACIÓN FORMAL

```
OBJETOS:
  C = {C1, C2, C3, C4, C5}          coordenadas
  H = {H1, H2, H3}                   huecos activos
  T = {T1, T2, T3, T4}               topologías
  M = {M1, M2, M3, M4, M5, ...}      mecanismos
  I = {I1, I2, I3, I4}                invariantes
  P = {P1, P2, P3}                    puntos ciegos

OPERACIONES:
  |  fusión         (paralela, conmutativa, como suma)
  →  composición    (secuencial, no conmutativa, como multiplicación)
  ∫  integración    (reducción post-fusión, como Σ)
  -  diferencial    (valor único, como resta)

PROPIEDADES:
  A|B = B|A                          conmutativa (fusión)
  A→B ≠ B→A                         no conmutativa (composición)
  (A→B)→C = A→(B→C)                 asociativa (composición)
  A→(B|C) = (A→B)|(A→C)             distributiva izquierda
  (B|C)→A ≠ (B→A)|(C→A)             NO distributiva derecha
  A→A ≠ A                           no idempotente (recursión produce nuevo)
  Aⁿ converge (n≈2 útil)            saturación
  output ∈ input                     clausura
  ∄ I: I→A = A                      sin identidad
  crítico(X) siempre produce nuevo   absorbente parcial
  A-A = ∅                            elemento absorbente del diferencial
  A-(B|C) = (A-B) ∩ (A-C)           distributiva del diferencial sobre fusión
```

---

## 8. RELACIÓN CON EL MOTOR v3.3

El Motor v3.3 es **un programa específico** escrito en esta álgebra:

```
∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
```

La álgebra permite escribir OTROS programas más baratos o más específicos. La biblioteca es el conjunto de programas validados con sus costes, triggers y resultados.

El Motor ejecuta programas. La inteligencia está en el programa, no en el Motor.

---

## 9. PENDIENTE — PRÓXIMAS SESIONES

1. **Validación empírica**: ejecutar programas aislados con el JSON del dentista y comparar con M2→M3 monolítico
2. **Mapa de diferenciales**: calcular A-B para las 12 combinaciones de 4 isomorfismos y confirmar complementariedad
3. **Contribución marginal**: ejecutar ∫(3 iso) vs ∫(4 iso) y medir delta
4. **Biblioteca v1**: cristalizar 5-8 programas validados con triggers y costes reales
5. **Evaluar los 15 isomorfismos**: usar diferenciales para decidir cuáles de los 10 nuevos son genuinamente complementarios a los 5 actuales
6. **Router**: selecciona programa de la biblioteca, no inventa

---

**FIN ÁLGEBRA DEL CÁLCULO SEMÁNTICO CR0**



## Motor/Meta-Red de preguntas inteligencias/TABLA_PERIODICA_INTELIGENCIA_CR0.md

# TABLA PERIÓDICA DE LA INTELIGENCIA — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-07
**Origen:** Sesión Opus — derivación desde ALGEBRA_CALCULO_SEMANTICO_CR0.md
**Dependencias:** ALGEBRA_CALCULO_SEMANTICO_CR0.md, sesión de validación empírica

---

## 1. DEFINICIÓN

Cada tipo de inteligencia es un **álgebra**: un sistema formal con objetos propios, operaciones propias y tipos de pensamiento que produce. Cada álgebra tiene un punto ciego estructural que otra álgebra ve sin esfuerzo.

El Motor v3.3 ejecuta UNA álgebra (Estructural/IAS) con 4 isomorfismos de 18 álgebras posibles. Esta tabla mapea el espacio completo.

```
ÁLGEBRA DE INTELIGENCIA:
  objetos:      qué tipo de cosas percibe / manipula
  operaciones:  qué puede hacer con ellas
  pensamiento:  qué tipos de razonamiento produce
  punto_ciego:  qué no puede ver por construcción
  firma:        la operación que la distingue de todas las demás
```

---

## 2. CRITERIO DE DISTINCIÓN

Dos inteligencias son genuinamente distintas si su DIFERENCIAL es grande:

```
A - B = grande → A ve cosas que B no puede ver por construcción → genuinamente distintas
A - B = pequeño → A y B ven casi lo mismo → una es variante de la otra
```

Las 18 inteligencias de esta tabla sobrevivieron al test del diferencial. Cada una tiene objetos que ninguna otra puede manipular.

---

## 3. LAS 18 ÁLGEBRAS

### CATEGORÍA I: FORMALES — operan sobre estructuras abstractas

#### 1. LÓGICO-MATEMÁTICA
```
Objetos:      estructuras, relaciones, pruebas, axiomas
Operaciones:  demostración, abstracción, generalización, contraejemplo
Pensamiento:  ¿es verdadero? ¿es necesario? ¿es suficiente? ¿existe? ¿es único?
Punto ciego:  lo ambiguo, lo parcial, lo no-axiomatizable
Firma:        DEMOSTRACIÓN — derivar verdad desde primeros principios
Ejemplo:      "Si margen < costes variables, toda expansión acelera pérdidas" (deducción)
```

#### 2. COMPUTACIONAL
```
Objetos:      algoritmos, estados, complejidad, datos
Operaciones:  descomposición, recursión, optimización, simulación
Pensamiento:  ¿es computable? ¿en cuánto tiempo? ¿se puede descomponer? ¿escala?
Punto ciego:  lo no-computable, la intuición, el juicio cualitativo
Firma:        OPTIMIZACIÓN — encontrar la mejor solución dentro de restricciones
Ejemplo:      "Ocupación de sillones es problema de scheduling con restricciones de RH"
```

### CATEGORÍA II: SISTÉMICAS — operan sobre relaciones entre partes

#### 3. ESTRUCTURAL (IAS)
```
Objetos:      coordenadas sintácticas, formas, niveles, huecos
Operaciones:  isomorfismo, composición, integración, diferencial
Pensamiento:  ¿qué forma tiene? ¿por qué esta forma? ¿qué se repite? ¿qué no ve?
Punto ciego:  no genera soluciones — solo diagnóstico
Firma:        ISOMORFISMO — proyectar forma sobre datos para hacer visible lo invisible
Ejemplo:      "SACRIFICAR ir=0.92 id=0 — opera con potencia máxima porque no se nombra"
```

#### 4. ECOLÓGICA
```
Objetos:      ecosistemas, ciclos, nichos, resiliencia, flujos
Operaciones:  observar interdependencia, rastrear flujos, detectar fragilidad
Pensamiento:  ¿quién depende de quién? ¿qué pasa si quitas un nodo? ¿es resiliente?
Punto ciego:  no ve al individuo — solo al sistema completo
Firma:        INTERDEPENDENCIA — nada existe aislado, todo afecta a todo
Ejemplo:      "La clínica es un ecosistema: quitar al dentista 1 día colapsa 3 flujos"
```

### CATEGORÍA III: ESTRATÉGICAS — operan sobre posición y movimiento

#### 5. ESTRATÉGICA
```
Objetos:      posición, recursos, movimientos, ventanas temporales, opciones
Operaciones:  evaluación posicional, anticipación, secuenciación, compromiso
Pensamiento:  ¿dónde estoy? ¿qué puede pasar si...? ¿en qué orden? ¿es reversible?
Punto ciego:  asume competición — no modela cooperación ni conflicto interno
Firma:        ANTICIPACIÓN — pensar dos movimientos adelante
Ejemplo:      "Abrir sábados antes de optimizar utilización = quemar recurso escaso sin dato"
```

#### 6. POLÍTICA
```
Objetos:      poder, alianzas, legitimidad, narrativa, coaliciones
Operaciones:  negociación, enmarcado, formación de coaliciones, lectura de poder
Pensamiento:  ¿quién tiene poder? ¿quién apoya a quién? ¿cómo se enmarca? ¿qué legitima?
Punto ciego:  confunde poder con verdad — lo que tiene apoyo no es necesariamente correcto
Firma:        NEGOCIACIÓN — redistribuir poder mediante acuerdo
Ejemplo:      "El banco tiene poder 0.6 sobre la decisión porque ofrece crédito = legitimidad"
```

#### 7. FINANCIERA
```
Objetos:      flujos, posiciones, riesgo, apalancamiento, opcionalidad
Operaciones:  descuento temporal, cobertura, arbitraje, composición de retornos
Pensamiento:  ¿cuánto vale hoy? ¿cuál es la asimetría? ¿puedo salir? ¿hay margen de seguridad?
Punto ciego:  lo que no tiene precio no existe
Firma:        DESCUENTO TEMPORAL — todo valor se traduce a presente
Ejemplo:      "7K€/mes × 12 = 84K€/año. Si trabaja 2.500h/año = 33.6€/h. ¿A qué hora deja de valer?"
```

### CATEGORÍA IV: SOCIALES — operan sobre personas

#### 8. SOCIAL (interpersonal + intrapersonal)
```
Objetos:      emociones, intenciones, dinámicas, patrones reactivos, vínculos
Operaciones:  lectura empática, regulación emocional, calibración social
Pensamiento:  ¿qué siente? ¿qué necesita? ¿qué patrón repite? ¿qué trigger activa?
Punto ciego:  sobrepsicologiza — puede ver conflicto emocional donde hay problema estructural
Firma:        EMPATÍA — leer el estado interno del otro (o propio) sin que lo verbalice
Ejemplo:      "La mujer no dice 'estoy triste' — dice 'no paras'. La emoción está en la queja operativa"
```

#### 9. LINGÜÍSTICA
```
Objetos:      palabras, marcos, narrativas, metáforas, actos de habla
Operaciones:  nombrar, reencuadrar, persuadir, construir significado con lenguaje
Pensamiento:  ¿cómo se nombra? ¿qué marco impone? ¿qué palabra falta? ¿qué metáfora gobierna?
Punto ciego:  confunde nombrar con resolver — poner nombre no cambia la estructura
Firma:        REENCUADRE — cambiar el marco lingüístico cambia lo que es visible
Ejemplo:      "'Crecer' enmarca expansión como progreso. 'Intensificar sacrificio' es el mismo acto, distinto marco"
```

### CATEGORÍA V: CORPORALES — operan sobre el cuerpo y el espacio

#### 10. CINESTÉSICA
```
Objetos:      movimiento, tensión, ritmo, coordinación, flujo corporal
Operaciones:  sentir, ajustar, sincronizar, fluir
Pensamiento:  ¿dónde hay tensión? ¿qué se contrae? ¿hay flujo? ¿el ritmo es sostenible?
Punto ciego:  no verbaliza — sabe pero no puede explicar qué sabe
Firma:        SENTIR TENSIÓN — el cuerpo detecta lo que la mente racionaliza
Ejemplo:      "El dentista dice 'estoy bien' pero su cuerpo acumula 2.500h/año en postura fija"
```

#### 11. ESPACIAL
```
Objetos:      formas, distancias, perspectivas, mapas, proporciones
Operaciones:  visualizar, rotar, proyectar, mapear
Pensamiento:  ¿qué forma tiene? ¿cómo se ve desde otro ángulo? ¿qué proporción es?
Punto ciego:  lo que no tiene extensión no existe — no ve procesos, solo configuraciones
Firma:        CAMBIO DE PERSPECTIVA — rotar el objeto para ver la cara oculta
Ejemplo:      "Mapa de la clínica: 3 sillones, 2 personas, 1 cuello de botella. La geometría dice dónde"
```

### CATEGORÍA VI: TEMPORALES — operan sobre el tiempo

#### 12. NARRATIVA
```
Objetos:      arco, personaje, transformación, secuencia, significado temporal
Operaciones:  contar, situar en historia, dar sentido al pasado, proyectar arco futuro
Pensamiento:  ¿quién es el protagonista? ¿en qué acto estamos? ¿qué transformación falta?
Punto ciego:  fuerza protagonista y arco donde puede no haberlos
Firma:        DAR SENTIDO — convertir hechos en historia con dirección
Ejemplo:      "El dentista está en el Acto 2: la crisis. El acto 3 (transformación) requiere elegir qué sacrificar"
```

#### 13. PROSPECTIVA
```
Objetos:      tendencias, señales débiles, escenarios, distribuciones de probabilidad
Operaciones:  extrapolar, simular, ponderar futuros, detectar señales tempranas
Pensamiento:  ¿hacia dónde converge? ¿qué señales débiles hay? ¿cuáles son los escenarios?
Punto ciego:  el cisne negro — lo que no tiene precedente no aparece en el modelo
Firma:        SIMULAR FUTUROS — explorar qué pasa si X, Y o Z
Ejemplo:      "Escenario A: crece y colapsa en 18 meses. B: optimiza y estabiliza. C: reduce y recupera vida"
```

### CATEGORÍA VII: CREATIVAS — operan generando lo que no existe

#### 14. DIVERGENTE
```
Objetos:      posibilidades, conexiones remotas, combinaciones inusuales
Operaciones:  generar opciones, romper marcos, combinar lo no combinado
Pensamiento:  ¿qué más podría ser? ¿qué pasa si combino X con Y? ¿cuántas opciones hay?
Punto ciego:  todo es posible, nada es evaluable — genera sin filtrar
Firma:        GENERACIÓN — producir opciones que no existían antes
Ejemplo:      "¿Y si el dentista no contrata ni abre sábados sino que sube precios 30% y pierde pacientes?"
```

#### 15. ESTÉTICA
```
Objetos:      armonía, tensión, elegancia, proporción, coherencia formal
Operaciones:  sentir coherencia, detectar disonancia, juzgar calidad de forma
Pensamiento:  ¿es elegante? ¿hay disonancia? ¿la forma es coherente con el contenido?
Punto ciego:  lo feo puede ser verdadero, lo bello puede ser falso
Firma:        JUICIO DE COHERENCIA — detectar que algo "no encaja" sin saber por qué
Ejemplo:      "La estructura del caso es disonante: dice 'quiero crecer' pero toda la energía va a sobrevivir"
```

#### 16. CONSTRUCTIVA (ingeniería)
```
Objetos:      restricciones, materiales, soluciones, prototipos, iteraciones
Operaciones:  construir dentro de límites, hacer funcionar, iterar, testear
Pensamiento:  ¿funciona? ¿qué restricción gobierna? ¿cómo se construye? ¿qué falla primero?
Punto ciego:  optimiza lo existente — no cuestiona si debería existir
Firma:        CONSTRUIR — convertir diseño en realidad funcional
Ejemplo:      "Restricción: 2 dentistas, 3 sillones, 45K ingresos. Solución: maximizar ratio sillón/hora antes de añadir"
```

### CATEGORÍA VIII: EXISTENCIALES — operan sobre significado

#### 17. EXISTENCIAL
```
Objetos:      propósito, libertad, responsabilidad, finitud, valores
Operaciones:  confrontar lo irreducible, jerarquizar valores, elegir con consciencia
Pensamiento:  ¿para qué? ¿merece la pena? ¿qué estoy sacrificando? ¿quién quiero ser?
Punto ciego:  puede paralizar por exceso de profundidad
Firma:        CONFRONTAR — preguntar "¿para qué?" hasta llegar al fondo
Ejemplo:      "¿7K€/mes con tus hijos viéndote ES el éxito, y 15K€/mes sin verlos es el fracaso?"
```

#### 18. CONTEMPLATIVA
```
Objetos:      presencia, vacío, observación, paradoja, no-acción
Operaciones:  soltar, observar sin juzgar, habitar la paradoja, esperar
Pensamiento:  ¿y si no hay problema? ¿qué pasa si no hago nada? ¿puedo sostener la incertidumbre?
Punto ciego:  puede desconectar de la acción — observar sin actuar
Firma:        OBSERVAR SIN JUZGAR — ver lo que es, sin necesidad de cambiarlo
Ejemplo:      "Antes de decidir sillón, sábados o dentista: sentarte con la pregunta sin responderla"
```

---

## 4. DIMENSIONES DE ORGANIZACIÓN

Las 18 álgebras se organizan en dos ejes:

### Eje X — DOMINIO (sobre qué opera)

| Dominio | Álgebras | Qué manipulan |
|---------|----------|--------------|
| FORMAL | Lógico-matemática, Computacional | Estructuras abstractas, verdad, eficiencia |
| SISTÉMICO | Estructural, Ecológica | Relaciones entre partes, formas, flujos |
| HUMANO | Estratégica, Política, Financiera | Posición, poder, valor entre personas |
| SOCIAL | Social, Lingüística | Emociones, intenciones, marcos de lenguaje |
| FÍSICO | Cinestésica, Espacial | Cuerpo, movimiento, espacio, forma visual |
| TEMPORAL | Narrativa, Prospectiva | Secuencia, arco, futuros, tendencias |
| GENERATIVO | Divergente, Estética, Constructiva | Posibilidades, coherencia, soluciones |
| EXISTENCIAL | Existencial, Contemplativa | Propósito, presencia, significado último |

### Eje Y — MODO (cómo opera)

| Modo | Descripción | Álgebras que lo usan |
|------|-------------|---------------------|
| ANALIZAR | Descomponer, demostrar, medir | Lógico-mat, Computacional, Financiera |
| PERCIBIR | Ver patrones, detectar forma | Estructural, Ecológica, Estética |
| MOVER | Actuar, posicionar, construir | Estratégica, Constructiva, Cinestésica |
| SENTIR | Empatizar, intuir, habitar | Social, Cinestésica, Contemplativa |
| GENERAR | Crear, imaginar, proyectar | Divergente, Narrativa, Prospectiva |
| ENMARCAR | Nombrar, negociar, dar sentido | Lingüística, Política, Existencial |

---

## 5. TIPOS DE PENSAMIENTO

### 5.1 Pensamiento INTERNO (dentro de una álgebra)

Las 10 familias derivadas del álgebra semántico aplican a CADA una de las 18 álgebras:

| # | Familia | Pensamiento | Expresión |
|---|---------|-------------|-----------|
| 1 | iso(S) | Percepción | ¿Qué forma tiene? |
| 2 | B(iso(S)) | Causalidad | ¿Por qué esta forma? |
| 3 | iso²(S) | Abstracción | ¿Qué se repite? |
| 4 | ∫(isos) | Síntesis | ¿Qué conecta todo? |
| 5 | A−B | Discernimiento | ¿Qué es único de cada mirada? |
| 6 | crítico(X) | Metacognición | ¿Qué no puedo ver? |
| 7 | iso(M) | Consciencia epistemológica | ¿Qué forma tiene mi pensamiento? |
| 8 | B(iso(M)) | Auto-diagnóstico | ¿Por qué pienso así? |
| 9 | ∫(M₁\|M₂) | Convergencia | ¿Qué esencia comparten mis explicaciones? |
| 10 | A→B→C→A' | Dialéctica | ¿Qué veo después de que otros transformaron mi mirada? |

### 5.2 Pensamiento LATERAL (cruza el perímetro de una álgebra)

| # | Tipo | Pensamiento | Operación | Qué rompe |
|---|------|-------------|-----------|-----------|
| 11 | T_A ≅ T_B | Analogía | ≅ (isomorfismo entre dominios) | Perímetro del dominio |
| 12 | Δ(S, x) | Contrafactual | Δ (perturbación) | Fijeza de los datos |
| 13 | T → S' | Abducción | ← (inversión de dirección) | Dirección del razonamiento |
| 14 | ⊕(S, random) | Provocación | ⊕ (inyección externa) | Coherencia del sistema |
| 15 | iso_X(S) | Reencuadre | extensión del espacio de isos | Clase de herramienta |
| 16 | abandonar | Destrucción creativa | meta-decisión | El marco entero |
| 17 | generar S' | Creación | generación desde restricciones | La premisa de análisis |

### 5.3 Pensamiento INTER-ÁLGEBRA (opera entre álgebras distintas)

| Expresión | Pensamiento | Qué produce |
|-----------|-------------|-------------|
| ∫(álgebra_A \| álgebra_B)(caso) | Síntesis multi-inteligencia | Lo que emerge al cruzar dos sistemas de razonamiento |
| álgebra_A − álgebra_B | Complementariedad | Qué puede ver A que B no puede, por construcción |
| álgebra_A → álgebra_B | Meta-explicación | Por qué el razonamiento de A produce la forma que B detecta |
| álgebra_A(output_B) | Lectura cruzada | Una inteligencia leyendo el output de otra |

---

## 6. COMBINATORIA INTER-ÁLGEBRA

Con 18 álgebras y 4 operaciones inter-álgebra:

| Operación | Combinaciones | Qué produce |
|-----------|---------------|-------------|
| ∫(subconjuntos de 18) | 2¹⁸ - 19 = 262.125 | Síntesis multi-inteligencia |
| A − B (18 × 17) | 306 | Mapa de complementariedad |
| A → B (18 × 17) | 306 | Meta-explicaciones |
| A(output_B) | 306 | Lecturas cruzadas |

Total teórico: ~263.000 expresiones inter-álgebra.

Acotado por saturación y redundancia: el diferencial determina cuáles de las 306 combinaciones de pares son genuinamente complementarias. Las redundantes se eliminan.

---

## 7. PUNTOS CIEGOS CRUZADOS — el valor de la tabla

La propiedad más potente de la tabla: **cada punto ciego de una álgebra es el objeto natural de otra**.

| Álgebra | Su punto ciego | Quién lo ve |
|---------|---------------|------------|
| Lógico-matemática | Lo ambiguo | Social, Contemplativa |
| Computacional | Lo no-computable | Cinestésica, Estética |
| Estructural | No genera soluciones | Constructiva, Divergente |
| Ecológica | No ve al individuo | Social, Existencial |
| Estratégica | Asume competición | Social, Contemplativa |
| Política | Confunde poder con verdad | Lógico-mat, Existencial |
| Financiera | Lo sin precio no existe | Existencial, Social |
| Social | Sobrepsicologiza | Estructural, Lógico-mat |
| Lingüística | Confunde nombrar con resolver | Constructiva, Cinestésica |
| Cinestésica | No verbaliza | Lingüística, Narrativa |
| Espacial | Lo sin extensión no existe | Narrativa, Social |
| Narrativa | Fuerza protagonista | Ecológica, Lógico-mat |
| Prospectiva | El cisne negro | Contemplativa, Divergente |
| Divergente | No evalúa | Lógico-mat, Financiera, Estratégica |
| Estética | Lo feo puede ser verdadero | Lógico-mat, Estructural |
| Constructiva | No cuestiona premisas | Existencial, Estructural |
| Existencial | Puede paralizar | Estratégica, Constructiva |
| Contemplativa | Puede desconectar de acción | Estratégica, Constructiva |

---

## 8. IMPLICACIONES PARA OMNI-MIND

### 8.1 El Motor v3.3 en la tabla
El Motor usa álgebra #3 (Estructural) con isomorfismos inspirados en #4 (Ecológica/conjuntos), #5/#6 (Estratégica/juegos + Política/agentes), y parcialmente #4 (Ecológica/cibernética). De 18 álgebras, usa fragmentos de 5.

### 8.2 El Router como selector de álgebras
El router no elige "programa de la biblioteca". Elige qué álgebras de inteligencia combinar según el problema:
- Problema financiero → Financiera + Computacional + Estratégica
- Problema de vida → Estructural + Existencial + Social + Financiera
- Problema de diseño → Constructiva + Estética + Espacial + Divergente
- Problema político → Política + Estratégica + Narrativa + Social

### 8.3 IAS como la química de la inteligencia
Cada álgebra es un elemento. Las combinaciones son compuestos. IAS es la ciencia que dice:
- Qué compuestos producen qué reacciones
- Qué elementos son complementarios (diferencial grande)
- Qué elementos son redundantes para un caso dado (diferencial pequeño)
- Cuánta profundidad es útil antes de saturación

---

## 9. PENDIENTE

1. **Validación empírica**: ejecutar al menos 3 álgebras distintas sobre el caso dental y medir diferenciales
2. **Mapa de complementariedad**: las 306 combinaciones de pares, medidas por diferencial
3. **Programas multi-álgebra**: recetas que combinan 2-4 álgebras para tipos de problema comunes
4. **Saturación inter-álgebra**: ¿cuántas álgebras aportan valor marginal antes de saturar?
5. **Isomorfismos por álgebra**: ¿cada álgebra tiene su propio set de isos, o comparten?
6. **Router v2**: selector de álgebras, no solo de programas

---

**FIN TABLA PERIÓDICA DE LA INTELIGENCIA CR0**



## SO/ALGEBRA_CALCULO_SEMANTICO_CR0.md

# ÁLGEBRA DEL CÁLCULO SEMÁNTICO — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-06
**Origen:** Sesión Opus — diseño de biblioteca de programas del Motor v3.3
**Dependencias:** CIERRE_SESION_2026-03-06_CALCULO_SEMANTICO.md

---

## 1. DEFINICIÓN

El Motor no es un pipeline de análisis. Es una **máquina de cálculo semántico**.

```
ARITMÉTICA CLÁSICA:
  variables:   números
  operaciones: +, -, ×, Σ
  output:      números

CÁLCULO SEMÁNTICO:
  variables:   coordenadas sintácticas (output de primitivas)
  operaciones: fusión (|), composición (→), integración (∫), diferencial (-)
  output:      objetos semánticos de 6 tipos (coordenada → punto ciego)
```

---

## 2. OBJETOS SEMÁNTICOS — qué produce el cálculo

### Nivel 0: COORDENADAS (primitivas — posicionan)

Las 7 primitivas producen 5 tipos de coordenada:

| Tipo | Fuente | Qué produce | Ejemplo (dentista) |
|------|--------|-------------|-------------------|
| C1 COMPRESIÓN | sustantivizar | Nombre a 3 escalas (palabra/frase/párrafo) | "Dilema capacidad-vida" |
| C2 POSICIÓN | adjetivar + adverbializar + verbo | Dónde está cada pieza: id (declarada) vs ir (real) | SACRIFICAR id=0 ir=0.92 |
| C3 RELACIÓN | preposicionar + conjuntar | Cómo se conectan las piezas (y qué conexiones faltan) | "Negocio DENTRO de vida familiar, no al revés" |
| C4 NIVEL | sujeto_predicado | Quién opera sobre quién, con qué poder | Mujer poder=0.2, Banco poder=0.6 |
| C5 DISTANCIA | calculadora ($0, código puro) | Gaps id↔ir + propagaciones + lentes | SACRIFICAR gap=0.92 desinflada |

Las coordenadas no analizan — **posicionan**. Son puntos en un espacio sintáctico.

La distancia id↔ir (C5) es el dato más potente: mide cuánto diverge lo declarado de lo real.


### Nivel 1: HUECOS ACTIVOS (sintetizador — cruza coordenadas)

El sintetizador cruza primitivas y produce lo que ninguna produce sola.

| Tipo | Cruce | Qué produce | Ejemplo (dentista) |
|------|-------|-------------|-------------------|
| H1 INVERSIÓN SEMÁNTICA | C1 × C2 | Lo declarado ≠ lo real | "Elegir" cuando ya eligió |
| H2 FUNCIÓN INVISIBLE | C2 × C5 | Opera con potencia máxima porque no se nombra | SACRIFICAR ir=0.92 id=0 — invisible |
| H3 CONEXIÓN AUSENTE ACTIVA | C3 × H2 | La desconexión sostiene el sistema | "Mantener A, B, C separados es lo que permite que el sacrificio continúe" |

El sintetizador no resume ni comprime. **Cruza coordenadas de distintas dimensiones y produce los puntos donde la realidad declarada diverge de la realidad operativa.**


### Nivel 2: TOPOLOGÍA (1 isomorfismo, 1 loop — proyecta forma)

Cada isomorfismo proyecta una estructura sobre las coordenadas + huecos. No añade datos — reorganiza para hacer visible una FORMA que antes era invisible.

| Tipo | Isomorfismo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------|-------------------|
| T1 CONTENEDORES | conjuntos | Quién contiene a quién, qué se solapa, qué falta | "Negocio dentro de vida familiar, no al revés" + gaps: cálculo horas/vida ausente |
| T2 CIRCUITOS | causal/dinámica | Qué loops existen, si se amplifican o frenan, hacia dónde converge | Loop refuerzo: Margen→Inversión→Más trabajo→Menos vida→Necesidad margen |
| T3 TABLERO | juegos/agentes | Qué jugadores, qué incentivos, quién gana si nadie cambia | Odontólogo 0.55 / Mujer 0.2 / Banco 0.6 / Sistema 0.9 |
| T4 CONTROL | cibernética | Qué mide, qué ajusta, qué señales ignora | Sensores: solo económicos. Feedback mujer: ignorado. Regulación: rígida |

Las topologías son FORMAS proyectadas sobre los mismos datos. Los datos no cambian. Lo que cambia es qué estructura se hace visible.


### Nivel 3: MECANISMO (composición A→B — explica la forma)

Una topología dice QUÉ FORMA tienen los datos. Un mecanismo dice POR QUÉ esa forma existe y no otra.

B opera sobre la topología que A produjo (no sobre los datos originales). Lo que emerge es una EXPLICACIÓN de la forma.

| Composición | Mecanismo | Pregunta que responde | Ejemplo (dentista) |
|-------------|-----------|----------------------|-------------------|
| causal→juegos | M1: MOTOR DEL LOOP | ¿Quién alimenta los circuitos? | Banco inyecta en "Inversión", Sistema normaliza "Más trabajo", Mujer frena pero poder insuficiente |
| conjuntos→causal | M2: CAUSA DE LA FORMA | ¿Qué produce la estructura de contención? | Nunca se calculó tasa tiempo→dinero, negocio se expande sin frontera |
| juegos→cibernética | M3: REGULACIÓN DEL JUEGO | ¿Qué impide que los jugadores cambien? | Odontólogo solo tiene sensor económico. Feedback vital no llega a actuador |
| causal→conjuntos | M4: FRONTERA DE CIRCULACIÓN | ¿Qué entra en los loops y qué queda fuera? | Familia/hijos/salud están FUERA de todos los loops de decisión |
| cibernética→causal | M5: LOOPS DE CONTROL | ¿Qué loops genera la regulación misma? | Medir solo dinero→decidir por dinero→refuerza medir solo dinero |

La composición NO es conmutativa: causal→juegos ≠ juegos→causal.

Con 4 isomorfismos de topología hay hasta 12 composiciones de 2 (4×3). No todas producen valor equivalente. El diferencial (sección 4) determina cuáles son redundantes.


### Nivel 4: INVARIANTE (recursión A² — estructura que se replica)

Recursión = isomorfismo comiendo su propio output. Sube de nivel lógico.

| Tipo | Recursión | Qué produce | Ejemplo (dentista) |
|------|-----------|-------------|-------------------|
| I1 CONTENCIÓN REPLICADA | conjuntos² | "Estar dentro sin verlo" se repite a cada escala | M2 dentro de paradigma = negocio dentro de vida familiar |
| I2 CIRCUITO REPLICADO | causal² | El mismo tipo de loop a cada nivel | "Diagnóstico preciso→Soluciones dentro del paradigma→Problema intacto→Más diagnóstico" |
| I3 JUGADOR INVISIBLE | juegos² | El agente con más poder es el menos nombrado, siempre | Nivel 1: "Sistema" poder=0.9. Nivel 2: "Paradigma-crecimiento" poder=0.95 |
| I4 SENSOR CIEGO | cibernética² | No mide lo que más importa, a cada nivel | Dentista no mide vida. M2 no mide sus propias premisas |

El invariante NO es el contenido. Es la **estructura que se repite independientemente del nivel en que opera**.

**Saturación (rendimiento por loop):**

| Loops | Valor marginal | Qué produce |
|-------|---------------|-------------|
| 1 | 100% | Topología (forma de los datos) |
| 2 | ~60-70% | Invariante (estructura que se replica) |
| 3 | ~10-15% | Meta-invariante (confirmación + matiz) |
| 4+ | ~0-5% | Convergencia (saturación) |


### Nivel ∞: PUNTO CIEGO (crítico — frontera del análisis)

Crítico no produce topología ni mecanismo. Produce FRONTERA: el límite de lo que todo lo anterior puede ver.

| Tipo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------------|
| P1 PREMISA OCULTA | Algo que todo el análisis asume sin examinar | "M2 asume que 'crecer' es necesario" |
| P2 PARADOJA PERFORMATIVA | El análisis hace exactamente lo que diagnostica | "Precisión técnica M2 = ceguera sistémica sobre sí mismo" |
| P3 FRONTERA DE MARCO | Lo que este marco no puede ver por construcción | "¿Y si 7K€/mes con vida familiar ES el éxito?" |

Crítico siempre es último y siempre vale la pena. Es el único isomorfismo que nunca es redundante.

---

## 3. OPERACIONES — las 4 operaciones del cálculo

### 3.1 FUSIÓN (|) — como suma

Dos o más isomorfismos operan en **paralelo** sobre el MISMO input. Producen topologías independientes.

```
causal|juegos(datos) → T2 + T3 (dos topologías independientes)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | Sí: A\|B = B\|A |
| Asociativa | Sí: (A\|B)\|C = A\|(B\|C) |
| Inverso (resta) | No existe como operación. Sí existe como contribución marginal |

**Contribución marginal** (sustituto de la resta):
```
∫(A|B|C) vs ∫(A|B) → diferencia = contribución marginal de C
```
Testeable: si quitas un isomorfismo de la fusión y la integración apenas cambia, ese isomorfismo es redundante para ese input.


### 3.2 COMPOSICIÓN (→) — como multiplicación

Un isomorfismo opera sobre el **output** de otro. Produce mecanismo (nivel 3).

```
juegos→causal(datos) = juegos(causal(datos))
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A→B ≠ B→A |
| Asociativa | Sí: (A→B)→C = A→(B→C) — la secuencia es la misma |
| Inverso (división) | No existe. La composición no es reversible |
| Trazabilidad | Sí: puedes ejecutar A, luego A→B, y ver qué transformó cada paso |

**Propiedad distributiva izquierda:**
```
A→(B|C) = (A→B) | (A→C)
```
Permite **factorizar programas**: ejecutar A una vez y fan-out en paralelo.

```
SIN FACTORIZAR:                    FACTORIZADO:
  causal→juegos      (2 calls)      causal→(juegos|conjuntos|cibernética)
  causal→conjuntos   (2 calls)      = 1 × causal + 3 paralelo
  causal→cibernética (2 calls)      = 4 calls (vs 6)
  = 6 calls total
```

**NO distributiva por la derecha:**
```
(B|C)→A ≠ (B→A) | (C→A)
```
En (B|C)→A, el agente A ve la fusión junta — puede cruzar. En (B→A)|(C→A), ve cada una por separado — no cruza. El cruce tiene valor irreducible.


### 3.3 INTEGRACIÓN (∫) — como sumatorio Σ

Un agente mira TODAS las topologías de una fusión simultáneamente. Produce CRUCE: conexiones entre topologías que ninguna ve sola.

```
∫(causal|juegos|conjuntos|cibernética)(datos) → cruce
```

Esto es lo que M2 hace hoy: 4 isomorfismos fusionados + una síntesis que cruza los 4 outputs.

No es suma (eso es fusión). No es composición (no hay secuencia). Es **reducción**: colapsa una colección en un objeto nuevo.


### 3.4 DIFERENCIAL (-) — como resta

Lo que A ve que B NO puede ver. Mide el valor único de cada isomorfismo.

```
Juegos - Cibernética = incentivos puros (motivación independiente de regulación)
Cibernética - Juegos = regulación pura (control independiente de jugadores)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A-B ≠ B-A |
| Asociativa | No: (A-B)-C ≠ A-(B-C) |
| Elemento absorbente | A-A = ∅ (cada isomorfismo es completo respecto a sí mismo) |
| Distributiva sobre fusión | A-(B\|C) = (A-B) ∩ (A-C) |

**Uso principal:** determinar redundancia. Si A-B es pequeño → A y B son redundantes (ven casi lo mismo). Si A-B es grande → son complementarios (cada uno ve cosas que el otro no puede).


### 3.5 Tabla resumen

```
OPERACIÓN     SÍMBOLO   ARITMÉTICA     CONMUT.  ASOC.  INVERSO    DISTRIB.
──────────────────────────────────────────────────────────────────────────────
Fusión          |       Suma           Sí       Sí     No*        —
Composición     →       Multiplicación No       Sí     No**       → sobre | (izq)
Integración     ∫       Sumatorio Σ    N/A      N/A    No         N/A
Diferencial     -       Resta          No       No     A-A=∅      - sobre | (∩)

*   Contribución marginal como sustituto medible
**  Descomposición/trazabilidad como sustituto
```

---

## 4. PROPIEDADES ALGEBRAICAS

| Propiedad | Valor | Implicación |
|-----------|-------|-------------|
| No conmutativa (→) | A→B ≠ B→A | El orden importa |
| No asociativa (-) | (A-B)-C ≠ A-(B-C) | La agrupación del diferencial importa |
| Asociativa (→) | (A→B)→C = A→(B→C) | La secuencia de composición no depende de paréntesis |
| No idempotente | A→A ≠ A | La recursión produce nuevo (invariantes) |
| Clausura | output ∈ input | Se puede seguir operando siempre |
| Saturación | A^n converge (n≈2 útil) | La profundidad útil es finita |
| Absorbente parcial | Crítico siempre produce punto ciego | El tipo de output es constante, el contenido varía |
| Sin identidad | ∄ I: I→A = A | Cada paso transforma, no hay operación neutra |
| Distributiva izq. | A→(B\|C) = (A→B)\|(A→C) | Factorizar programas: misma semántica, menor coste |
| No distributiva der. | (B\|C)→A ≠ (B→A)\|(C→A) | La integración post-fusión no se descompone |
| Distributiva diferencial | A-(B\|C) = (A-B) ∩ (A-C) | El valor único respecto a un grupo = intersección de diferenciales |

---

## 5. EXPRESIONES — programas escritos en el álgebra

### El Motor v3.3 actual:

```
M1 = primitivas(input)                           → C1-C5
S  = sintetizador(M1)                             → H1-H3
M2 = ∫(conjuntos|causal|juegos|cibernética)(S)    → T1-T4 + cruce
M3 = ∫(conj²|caus²|jueg²|ciber²)(M2)              → I1-I4 + P1-P3

Compacto: ∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
Coste: $0.91 | 293s | 3 Opus + 91 Haiku
```

### Programas posibles:

| Programa | Expresión | Produce | Coste est. |
|----------|-----------|---------|-----------|
| Triage rápido | primitivas(input) | C1-C5 | ~$0.03 |
| Detección huecos | sint(prim(input)) | C1-C5 + H1-H3 | ~$0.34 |
| Vista 1 dimensión | iso(sint(prim(input))) | 1 Topología | ~$0.15 |
| Cruce multi-dim | ∫(iso₁\|iso₂)(sint(prim(input))) | Topologías + cruce | ~$0.25-0.45 |
| Explicar 1 forma | isoA→isoB(sint(prim(input))) | 1 Mecanismo | ~$0.25 |
| Detectar patrón | iso²(sint(prim(input))) | 1 Invariante | ~$0.25 |
| + Punto ciego | X→crítico | + P1-P3 | +$0.10 |
| Máxima potencia | ∫(iso²)(∫(iso)(sint(prim(input)))) | Todo | ~$0.91 |

### Formato de programa (receta):

```json
{
  "nombre": "diagnostico_estructural_profundo",
  "expresion": "∫(iso²)(∫(iso)(sintetizador(primitivas(input))))",
  "primitivas": ["todas"],
  "programa": [
    {"paso": 1, "op": "|", "iso": ["conjuntos","causal","juegos","cibernetica"]},
    {"paso": 2, "op": "∫"},
    {"paso": 3, "op": "²", "loops": 2},
    {"paso": 4, "op": "∫"}
  ],
  "coste_estimado": "$0.91",
  "produce": ["C1-C5", "H1-H3", "T1-T4", "I1-I4", "P1-P3"],
  "cuando_usar": "Decisiones estratégicas con múltiples tensiones",
  "cuando_NO_usar": "Preguntas operativas simples"
}
```

---

## 6. HERRAMIENTAS DE OPTIMIZACIÓN

**Factorización (distributiva izquierda):**
Si un programa ejecuta A→B, A→C, A→D por separado, factorizar a A→(B|C|D) produce el mismo resultado con menos coste.

**Contribución marginal (sustituto de inverso en fusión):**
Ejecutar ∫ con y sin un isomorfismo. Si la diferencia es mínima → redundante → eliminable.

**Diferencial (valor único):**
Calcular A-B y B-A. Si ambos son grandes → complementarios (mantener). Si alguno es pequeño → redundante (uno cubre al otro).

**Saturación (profundidad óptima):**
Loops=2 máximo por defecto. Loops=3 solo con justificación explícita.

---

## 7. NOTACIÓN FORMAL

```
OBJETOS:
  C = {C1, C2, C3, C4, C5}          coordenadas
  H = {H1, H2, H3}                   huecos activos
  T = {T1, T2, T3, T4}               topologías
  M = {M1, M2, M3, M4, M5, ...}      mecanismos
  I = {I1, I2, I3, I4}                invariantes
  P = {P1, P2, P3}                    puntos ciegos

OPERACIONES:
  |  fusión         (paralela, conmutativa, como suma)
  →  composición    (secuencial, no conmutativa, como multiplicación)
  ∫  integración    (reducción post-fusión, como Σ)
  -  diferencial    (valor único, como resta)

PROPIEDADES:
  A|B = B|A                          conmutativa (fusión)
  A→B ≠ B→A                         no conmutativa (composición)
  (A→B)→C = A→(B→C)                 asociativa (composición)
  A→(B|C) = (A→B)|(A→C)             distributiva izquierda
  (B|C)→A ≠ (B→A)|(C→A)             NO distributiva derecha
  A→A ≠ A                           no idempotente (recursión produce nuevo)
  Aⁿ converge (n≈2 útil)            saturación
  output ∈ input                     clausura
  ∄ I: I→A = A                      sin identidad
  crítico(X) siempre produce nuevo   absorbente parcial
  A-A = ∅                            elemento absorbente del diferencial
  A-(B|C) = (A-B) ∩ (A-C)           distributiva del diferencial sobre fusión
```

---

## 8. RELACIÓN CON EL MOTOR v3.3

El Motor v3.3 es **un programa específico** escrito en esta álgebra:

```
∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
```

La álgebra permite escribir OTROS programas más baratos o más específicos. La biblioteca es el conjunto de programas validados con sus costes, triggers y resultados.

El Motor ejecuta programas. La inteligencia está en el programa, no en el Motor.

---

## 9. PENDIENTE — PRÓXIMAS SESIONES

1. **Validación empírica**: ejecutar programas aislados con el JSON del dentista y comparar con M2→M3 monolítico
2. **Mapa de diferenciales**: calcular A-B para las 12 combinaciones de 4 isomorfismos y confirmar complementariedad
3. **Contribución marginal**: ejecutar ∫(3 iso) vs ∫(4 iso) y medir delta
4. **Biblioteca v1**: cristalizar 5-8 programas validados con triggers y costes reales
5. **Evaluar los 15 isomorfismos**: usar diferenciales para decidir cuáles de los 10 nuevos son genuinamente complementarios a los 5 actuales
6. **Router**: selecciona programa de la biblioteca, no inventa

---

**FIN ÁLGEBRA DEL CÁLCULO SEMÁNTICO CR0**



## motor-semantico/results/exp7_report.md

# EXP 7 — Rediseño del Chief of Staff OS

**Fecha:** 2026-03-11
**Provider:** OpenRouter
**Tokens totales:** ~44,000 (R1: 14,795 + R2: 21,479 + R3: 6,613 + F3: 2,561 + F4: 3,168)
**Coste estimado:** ~$0.15

## 1. Diseños Independientes (R1)

| Modelo | Perspectiva | Tokens | Tiempo |
|--------|-------------|:---:|:---:|
| Step 3.5 Flash | Razonamiento | 16,384 | 136.1s |
| Cogito 671B | Síntesis | 2,020 | 23.8s |
| Kimi K2.5 | Enjambre | 9,464 | 316.8s |
| DeepSeek V3.2 | Arquitectura | 3,004 | 106.0s |
| Nemotron Super | Coste/eficiencia | 3,855 | 45.9s |

**Observaciones R1:**
- Step 3.5 Flash generó el diseño más exhaustivo (16K tokens, max_tokens completo)
- Kimi K2.5 requirió timeout extendido a 600s (316.8s de ejecución)
- Cogito 671B fue el más conciso (2K tokens, 24s)
- Nemotron Super tuvo el mejor ratio tokens/latencia

## 2. Evaluaciones Cruzadas (R2)

| Evaluador | Tokens | Tiempo |
|-----------|:---:|:---:|
| Step 3.5 Flash | 8,319 | 65.3s |
| Cogito 671B | 1,862 | 25.7s |
| Kimi K2.5 | 6,281 | 408.2s |
| DeepSeek V3.2 | 1,779 | 67.0s |
| Nemotron Super | 3,238 | 40.7s |

**Total R2:** 607s (10.1 min)

## 3. Diseño Consensuado (R3)

**Sintetizador:** Step 3.5 Flash
**Tokens:** 6,613
**Tiempo:** 45.7s

8 componentes diseñados:
1. **Dispatcher Inteligente** — Gemini Flash 1.5 (clasificación rápida)
2. **Evaluador de Respuesta** — Claude 3 Haiku (quality gate)
3. **Planificador de Razonamiento** — o1-mini (deep thought)
4. **Matriz Cognitiva Adapter** — all-MiniLM-L6-v2 (embeddings, $0)
5. **Agente de Coding** — Qwen 2.5 Coder 32B
6. **Monitor de Rendimiento** — Gemini Flash 1.5
7. **Optimizador de Configuración** — Llama 3.2 3B
8. **Logger & Telemetría** — código puro ($0)

**Coste estimado por turno:** ~$0.0013 (<<$0.02 target)
**Latencia superficie:** ~800ms (<1s)
**Latencia profundo:** ~29s (<30s)

Ver: `results/exp7_chief_design_v2.md`

## 4. Contraste con Maestro (F3)

**Verificador:** Nemotron Super
**Resultado: 6/10 PASA, 4/10 FALLA**

| # | Check | Resultado |
|---|-------|:---------:|
| 1 | Matriz 3Lx7F como campo de gradientes | PASA |
| 2 | Gestor compila programas para Chief | PASA |
| 3 | Multi-modelo con asignación empírica | PASA |
| 4 | Estigmergia como comunicación | **FALLA** |
| 5 | 3 niveles L0/L1/L2 respetados | PASA |
| 6 | 8 operaciones sintácticas integradas | **FALLA** |
| 7 | Pipeline de 7 pasos del Motor | **FALLA** |
| 8 | Self-improvement alimenta al Gestor | PASA |
| 9 | Puede lanzar enjambre de código | **FALLA** |
| 10 | Coste < $0.02/turno | PASA |

**Inconsistencias CR0 pendientes:**
1. Estigmergia: usa Redis Pub/Sub + gRPC en lugar de marcas en Postgres
2. 8 operaciones sintácticas: no hay detector de huecos
3. Pipeline 7 pasos: Planificador no se alinea con pipeline del Motor Cognitivo
4. Enjambre de código: no hay orquestación paralela de agentes de coding

Ver: `results/exp7_maestro_check.md`

## 5. Spec de Implementación (F4)

**Generador:** DeepSeek V3.2
**Tokens:** 3,168 | **Tiempo:** 157.2s

Incluye:
- Estructura de proyecto (`cos_omnimind/`)
- Input/output types por componente (TypeScript interfaces)
- SQL schema completo (6 tablas nuevas + ALTER de cognitive_matrix)
- Estimación: 116 horas (4 semanas)
- Orden de implementación por dependencias

Ver: `results/exp7_chief_implementation_spec.md`

## 6. Timing

| Fase | Tiempo | Detalle |
|------|:---:|---------|
| R1 | ~629s | 5 modelos (Kimi retry con timeout 600s) |
| R2 | 607s | 5 evaluaciones cruzadas |
| R3 | 46s | Consenso con Step 3.5 Flash |
| F3 | 35s | Verificación Maestro con Nemotron |
| F4 | 157s | Spec implementación con DeepSeek V3.2 |
| **Total** | **~1,474s** | **~24.6 min** |

## 7. Observaciones Críticas

### Modelos propietarios en el diseño
El consenso incluye **modelos propietarios** (claude-3-haiku, o1-mini) a pesar del requisito "sin dependencia de Anthropic". Esto es un fallo del R3 sintetizador. Los modelos OS equivalentes serían:
- `anthropic/claude-3-haiku` → `nvidia/llama-3.3-nemotron-super-49b-v1.5` o `mimo-v2-flash`
- `openai/o1-mini` → `stepfun/step-3.5-flash` (razonamiento)

### Arquitectura sólida, integración incompleta
La estructura de 8 componentes es limpia, pero falta integrar:
- Detector de huecos (8 operaciones sintácticas del Marco Lingüístico)
- Pipeline de 7 capas del Motor Cognitivo como flujo del pensamiento profundo
- Comunicación estigmérgica (marcas en DB, no colas)

### Coste
El diseño cumple holgadamente el target de <$0.02/turno con $0.0013 promedio. Margen 15x.

## 8. Artefactos Generados

| Archivo | Descripción |
|---------|-------------|
| `results/exp7_r1_step35.md` | Diseño R1: Step 3.5 Flash |
| `results/exp7_r1_cogito.md` | Diseño R1: Cogito 671B |
| `results/exp7_r1_kimi.md` | Diseño R1: Kimi K2.5 |
| `results/exp7_r1_deepseek.md` | Diseño R1: DeepSeek V3.2 |
| `results/exp7_r1_nemotron.md` | Diseño R1: Nemotron Super |
| `results/exp7_r2_step35.md` | Evaluación cruzada: Step 3.5 Flash |
| `results/exp7_r2_cogito.md` | Evaluación cruzada: Cogito 671B |
| `results/exp7_r2_kimi.md` | Evaluación cruzada: Kimi K2.5 |
| `results/exp7_r2_deepseek.md` | Evaluación cruzada: DeepSeek V3.2 |
| `results/exp7_r2_nemotron.md` | Evaluación cruzada: Nemotron Super |
| `results/exp7_chief_design_v2.md` | Diseño consensuado (R3) |
| `results/exp7_maestro_check.md` | Verificación Maestro (F3) |
| `results/exp7_chief_implementation_spec.md` | Spec implementación (F4) |
| `results/exp7_results.json` | Datos estructurados |
| `results/exp7_report.md` | Este report |

---
*Generado: 2026-03-11*



## motor-semantico/results/exp5b_report.md

# EXP 5b — Nuevos Modelos OS en Pipeline Multi-Estación

**Fecha:** 2026-03-11
**Provider:** OpenRouter
**Pregunta:** ¿Los modelos nuevos (exp1bis) resuelven T1 y T4 que quedaron en 0% en exp5?

## Resultado Principal

| Task | Exp 5 Mejor | Exp 5b Mejor | Config ganadora | Delta |
|------|:---:|:---:|:---:|:---:|
| **T1** Edge Function (Deno/TS) | 0% | **100%** | N2_cheap, N3_coding | **+100pp** |
| **T4** Orquestador (Python async) | 0% | **0%** | — | +0pp |

## Tabla Detallada: Config x Task

| Config | Modelos | T1 | T4 | Debug | Tiempo | Tokens |
|--------|---------|:---:|:---:|:---:|:---:|:---:|
| N1_top | step-3.5 + qwen-3.5-397b | 2/10 (20%) | 0/0 (E1 vacío) | 3 / 0 | 572s | 76K |
| N2_cheap | mimo-v2 + nemotron + step-3.5 | **7/7 (100%)** | 0/4 (0%) | 1 / 3 | 848s | 112K |
| N3_coding | step-3.5 + devstral | **10/10 (100%)** | 0/0 (E1 vacío) | 3 / 0 | 455s | 73K |

## Veredicto

### T1: El problema ERA los modelos
- 2 de 3 configs llegaron al **100%** (N2_cheap 7/7, N3_coding 10/10)
- N1_top llegó a 20% — el modelo razonador (qwen-3.5-397b) no es óptimo para código TS
- **El pipeline multi-estación funciona para tareas de código de complejidad media**
- Regla skip-E5/E6 validada: Reviewer/Optimizer rompieron el código funcional de N2_cheap (7/7 → 6/19)

### T4: Problema MIXTO (modelo + tarea)
- **2 de 3 configs fallaron en E1** (Architect): step-3.5-flash consumió los 16K tokens en `<think>` sin generar output
- N2_cheap (mimo-v2 como E1) sí generó arquitectura, pero el código generado falló en mocks de `aiohttp.ClientSession.__aenter__`
- **Causa raíz doble:**
  1. **Think-tag blow-up**: Step 3.5 Flash gasta todo el budget pensando en T4 (tarea compleja con async + mocks)
  2. **Complejidad intrínseca**: T4 requiere mocks de `aiohttp`, `asyncio.gather`, context managers — los modelos OS no manejan bien este pattern

## Análisis de Estaciones (N3_coding T1 — mejor run)

| Estación | Modelo | Tokens | Latencia | Resultado |
|----------|--------|:---:|:---:|:---:|
| E1 Architect | step-3.5-flash | 6,644 | 45s | Plan correcto |
| E2 Implement | devstral-2512 | 1,174 | 4s | Código base |
| E2 Tests | devstral-2512 | 1,457 | 7s | 10 tests |
| E3 Tester | devstral-2512 | 1,646 | 10s | Diagnóstico |
| E4 Debug R1 | step-3.5-flash | 16,384 | 94s | Fix parcial |
| E4b Debug R2 | step-3.5-flash | 16,384 | 103s | Fix parcial |
| E4c Debug R3 | step-3.5-flash | 8,242 | 63s | **10/10** |

**Insight:** Devstral genera código limpio y rápido (~4-10s). Step 3.5 Flash es excelente como debugger (resuelve en 3 rounds). La combinación coding-specialist + reasoning-model es la ganadora.

## Problema Think-Tag en T4

| Config | E1 Model | E1 Tokens | E1 Content |
|--------|----------|:---:|:---:|
| N1_top | step-3.5-flash | 16,384 | **VACÍO** (todo en `<think>`) |
| N2_cheap | mimo-v2-flash | 3,834 | OK (no usa think tags) |
| N3_coding | step-3.5-flash | 16,384 | **VACÍO** (todo en `<think>`) |

MiMo V2 Flash no usa extended thinking → no sufre el blow-up. Pero su output de arquitectura no fue suficiente para resolver T4.

## Recomendaciones para el Motor Semántico

1. **Para E1 (Architect):** Usar mimo-v2-flash o devstral — modelos sin think-tags que generan output directo
2. **Para E4 (Debugger):** step-3.5-flash es el mejor — 3 rounds de debug resolvieron T1 completamente
3. **Regla E5/E6 skip confirmada:** Si tests pasan al 100% post-debug, NO pasar por Reviewer/Optimizer
4. **T4 requiere approach diferente:** Pipeline multi-estación con modelos OS no es suficiente para async Python con mocks complejos. Opciones:
   - Usar modelo propietario (Sonnet/Opus) solo para E1-Architect en T4
   - Simplificar la spec de T4 (sin mocks de aiohttp)
   - Añadir examples/few-shot al prompt de E1

## Costes Estimados

| Config | Tokens Totales | Coste Aprox |
|--------|:---:|:---:|
| N1_top T1 | 60K | ~$0.06 |
| N1_top T4 | 16K | ~$0.02 |
| N2_cheap T1 | 25K | ~$0.01 |
| N2_cheap T4 | 87K | ~$0.04 |
| N3_coding T1 | 73K | ~$0.03 |
| N3_coding T4 | 16K | ~$0.02 |
| **Total** | **277K** | **~$0.18** |

---
*Generado: 2026-03-11*



## motor-semantico/results/exp8_report.md

# EXP 8 — Auditoría Completa del Sistema Cognitivo OMNI-MIND

**Fecha:** 2026-03-11 12:15

**Modelos:** Kimi K2.5, Step 3.5 Flash, Cogito 671B, DeepSeek V3.2, Nemotron Super


## 1. Resumen Ejecutivo

Aquí tienes el análisis consolidado de las 5 auditorías + evaluaciones cruzadas del Sistema Cognitivo OMNI-MIND:

---

## 1. DIAGNÓSTICO CONSOLIDADO

### **A. COHERENCIA INTERNA**
- **A1 (L0 consistentes):** 🟢 **Sólido**. Los documentos L0 (3 Lentes, 7 Funciones, Álgebra, 8 Operaciones) operan consistentemente sin contradicciones formales.
- **A2 (Maestro vs L0):** 🟢 **Sólido**. El Maestro (§0-§13) declara explícitamente que L0 es "gramática. No cambia", y las operaciones algebraicas se implementan en el pipeline del Motor vN.
- **A3 (18 INT irreducibles):** 🟡 **Mejorable**. **Disenso crítico**: Kimi/Step/Cogito identifican que solo 6 son irreducibles (INT-01, 02, 06, 08, 14, 16) y 12 tienen solapamiento significativo (0.50-0.75 redundancia); DeepSeek/Nemotron validan las 18. **Veredicto**: Operar con 6 base + 12 derivadas opcionales.
- **A4 (Matriz 3L×7F):** 🟢 **Sólida**. Validada empíricamente (EXP 4-4.3) con cobertura del 94.6%-100%.
- **A5 (Resultados vs diseño):** 🟡 **Mejorable**. EXP 4 valida multi-modelo, pero EXP 5b muestra 0% éxito en T4 (Orquestador Python) con modelos OS y 44% fallos sin auto-reparación.

### **B. SOBREDISEÑO**
- **B1 (Componentes teóricos):** 🔴 **Roto**. Reactor v3, Meta-motor, y Fábrica de Exocortex existen solo en teoría ("⬜ Diseñado, por implementar") sin validación empírica.
- **B2 (Eliminables):** 🟢 **Limpio**. Chief of Staff (DEPRECADO §1B), 9 modos conversacionales, y 24 agentes específicos del Chief pueden eliminarse sin pérdida funcional.
- **B3 (17 tipos pensamiento):** 🔴 **Roto**. Overhead confirmado: EXP 4.3 muestra que solo 6-7 patrones son frecuentemente usados; el resto son categorías teóricas sin impacto práctico en el pipeline MVP.
- **B4 (6 modos):** 🔴 **Roto**. Redundantes con gradientes de la Matriz. El propio Maestro (§1B) declara los modos "overengineered — el Motor no necesita modos, tiene gradientes". *Nota: Cogito disiente pero queda en minoría.*
- **B5 (Reactor v3):** 🟡 **Mejorable**. Genera preguntas "con raíz verificada" pero con solo **12% de utilidad** (dato Cogito) vs Reactor v4 (datos reales). Teóricamente elegante, prácticamente secundario.


## 2. Auditorías Individuales (R1)


### Kimi K2.5 — Enjambre y multi-modelo — ¿cómo orquestar múltiples modelos como agentes?

**Veredictos:** 🟢 11 / 🟡 10 / 🔴 11

**Tiempo:** 0s | **Tokens:** 0

Auditoría completada. A continuación el análisis sistemático de las 31 preguntas:

---

### A. COHERENCIA INTERNA

**A1. ¿Los documentos L0 (invariantes) son consistentes entre sí?** 🟢  
El Álgebra del Cálculo Semántico (§3), el Marco Lingüístico (§1D) y las 7 Funciones/3 Lentes (§2) operan consistentemente: las 8 operaciones sintácticas se mapean a las primitivas v3.3 (§1D, tabla de mapeo), y el álgebra (∫, →, -) genera los prompts que la Matriz coordina. No se detectan contradicciones formales.

**A2. ¿El Documento Maestro es consistente con los L0?** 🟢  
El Maestro (§0-§13) declara explícitamente que L0 es "gramática. No cambia" (§1C). Las operaciones algebraicas del L0 (fusión, composición) se implementan en el pipeline del Motor vN (§4, Paso 3: Composición). La consistencia es explícita y trazable.

**A3. ¿Las 18 inteligencias son genuinamente irreducibles?** 🟡  
El documento reconoce que solo 6 son irreducibles (INT-01, INT-02, INT-06, INT-08, INT-14, INT-16) (§1A). Las demás forman clusters redundantes (ej: INT-03/04 con 0.50-0.75 de redundancia, Cartografía §4.3). El sistema las trata como 18 operativas, pero empíricamente hay solapamiento significativo.

**A4. ¿La Matriz 3L×7F es el esquema correcto?** 🟢  
Es el esquema central validado en §2 y usado consistentemente en todo el pipeline (378 posiciones). Los experimentos (EXP 4-4.3) confirman que la cobertura matricial funciona como estructura de evaluación.

**A5. ¿Los resultados experimentales contradicen alguna asunción del diseño?** 🟢  
Los resultados validan el diseño: 3 modelos OS superan a Claude (§6B, Tabla 4), confirmando el enfoque OS-first (Principio 25). La mesa redonda (EXP 4) demuestra que la diversidad de modelos es una dimensión algebraica válida (§12, Principio 21).

---

### B. SOBREDISEÑO

**B1. ¿Qué componentes existen por teoría pero no tienen validación empírica?** 🔴  
- **Reactor v3** (generación conceptual): §6 lo lista como "⬜ Puede ir en paralelo" sin datos de validación.  
- **Meta-motor**: §6 dice "⬜ Con datos reales" y "evoluciona preguntas" pero sin evidencia empírica.  
- **17 tipos de pensamiento** (§1A): Derivados teóricamente del álgebra pero sin validación de que mejoren la selección vs. heuristicos simples.

**B2. ¿Qué puede eliminarse sin perder funcionalidad real?** 🟢  
- **Chief of Staff**: Ya marcado como DEPRECADO (§1B, §8B).  
- **9 modos conversacionales**: El propio documento los declara "overengineered" (§1B) y dice que el Motor "no necesita modos, tiene gradientes".  
- **24 agentes específicos del Chief**: Eliminados en diseño v4 (§1B).

**B3. ¿Los 17 tipos de pensamiento son necesarios o es overhead?** 🟡  
Son overhead potencial. El pipeline MVP (§4) selecciona inteligencia + modo, activando pensamiento implícitamente. No hay evidencia de que la selección explícita de los 17 mejore resultados vs. la red de preguntas base (L1).

**B4. ¿Los 6 modos son necesarios si la Matriz ya tiene gradientes?** 🔴  
No. El documento explícito: "9 modos conversacionales (overengineered — el Motor no necesita modos, tiene gradientes)" (§1B). La Matriz 3L×7F con campo de gradientes (§2) hace redundante la categorización por modos.

**B5. ¿El Reactor v3 (generación conceptual) aporta algo que los datos reales no cubren mejor?** 🟡  
El Reactor v4 (datos reales) es prioritario y validado por observación (§6D-2). El v3 (teórico) genera preguntas "con raíz verificada" pero sin evidencia de que sean más efectivas que las de v4. Es teóricamente elegante pero prácticamente secundario.

---

### C. HUECOS

**C1. ¿Qué necesita el sistema que no está diseñado?** 🔴  
- **Fallback robusto**: Si el Gestor de la Matriz falla, no hay mecanismo de degradación graceful (solo se menciona Sonnet como referencia, no como backup operativo).  
- **Gestión de errores del Gestor**: No hay especificación de qué ocurre si el orquestador OS (Qwen 235B) falla en la asignación modelo→celda.  
- **Especificación de UI/UX**: Más allá de "chat", no hay diseño de interfaz (§8 menciona interfaz pero sin detalles técnicos).

**C2. ¿La interfaz de usuario (chat) está suficientemente especificada?** 🔴  
No. El documento menciona "Interfaz: chat" (§1) y "ias.html" (MEMORY.md) como consola modular, pero carece de especificaciones de flujo de usuario, estados de error, o diseño de interacción para el MVP de pilotos (§11).

**C3. ¿El modelo de negocio (€50-200/mes) está validado o es asunción?** 🔴  
Es asunción sin validación de mercado. §11 menciona el rango basado en cálculos de margen (>90%), pero no hay evidencia de disposición a pagar, análisis de competencia, o validación con clientes potenciales.

**C4. ¿La transferencia cross-dominio tiene base empírica?** 🔴  
No. §6D-2 describe el flywheel teórico ("Pilates descubre → Fisioterapia recibe"), pero los pilotos están marcados como "⬜ Validar" y "⬜ Test clave: ¿preguntas de Pilates aplican a fisio?". Es hipótesis sin datos.

**C5. ¿Qué pasa cuando el sistema se equivoca? ¿Hay mecanismo de corrección?** 🟡  
Hay detección (§4, Paso 6: Verificación de Cierre, gaps > 0.3 escalan), pero no hay mecanismo de corrección automática o rollback si el Gestor compila un programa defectuoso. La auto-mejora (§6F) es prospectiva, no operativa.

---

### D. CONTRADICCIONES

**D1. Maestro dice "Chief DEPRECADO" pero CONTEXTO_SISTEMA tiene 24 agentes del Chief operativos** 🔴  
Contradicción explícita. §1B y §8B declaran "Chief of Staff → DEPRECADO" y eliminan "24 agentes específicos del Chief", pero MEMORY.md (CONTEXTO_SISTEMA) describe detalladamente el Chief operativo con 6.900 líneas y 24 funciones en Supabase. El sistema real no refleja el diseño v4.

**D2. Maestro dice "todo a fly.io" pero implementación está en Supabase** 🔴  
§0 y §8 establecen "Supabase se depreca gradualmente" y "todo en fly.io", pero MEMORY.md muestra el sistema nervioso actual operativo en Supabase (99 Edge Functions, 47 migraciones SQL). La migración no está completada y representa riesgo operativo.

**D3. Maestro dice "Sonnet solo referencia" pero ~12 agentes dependen de Sonnet** 🟡  
§6B dice "Sonnet solo referencia inicial", pero §8B (Migración OS) revela que ~12 agentes 🟡 (correlador-vida, prescriptor, diseñadores, verbalizadores) aún requieren Sonnet para validación. La dependencia de Anthropic persiste en componentes críticos de cara al usuario.

**D4. ¿Presupuestos del v1 (€640-920 para 3 meses) son realistas con costes reales ($0.10-1.50)?** 🟢  
Sí. Con coste de $0.20/caso (OS-first, §6B) y 300 casos/mes = $60/mes (€54), los €640-920 cubren 3 meses de operación más desarrollo. Los cálculos son consistentes (§14 vs §6B).

**D5. ¿Hay contradicciones entre las 4 versiones del documento no resueltas?** 🟡  
Hay tensión entre el estado actual (v2/Supabase, descrito en MEMORY.md) y el objetivo v4/fly.io (Maestro). Aunque §0 declara que el Maestro "supersede" documentos anteriores, la implementación real (Supabase) no ha migrado aún, creando fricción operativa.

---

### E. VISIÓN DE PRODUCTO

**E1. ¿La visión (motor que compila programa cognitivo por interacción) es realista?** 🟢  
Técnicamente sí. La arquitectura del Gestor (§6E) y el Motor (§6B) es coherente, y los experimentos (EXP 4-5) validan la ejecución multi-modelo y la efectividad de las redes de preguntas.

**E2. ¿El camino "pilotos propios → amigo informático → escala" tiene sentido?** 🟢  
Sí. §11 describe una estrategia de validación progresiva lógica: Pilates (Jesús) → Fisioterapia (segundo dominio) → amigo informático (tercer validador) → escala. Reduce riesgo antes de inversión comercial.

**E3. ¿El modelo de negocio (margen >90%) se sostiene?** 🟢  
Matemáticamente sí. §11 calcula correctamente: coste $2-5/mes vs precio €50-200/mes ($55-220). El margen >90% es aritméticamente válido si se alcanzan los volúmenes proyectados.

**E4. ¿El flywheel (cada cliente mejora para todos) funciona en la práctica?** 🟡  
Es teórico. §6D-2 describe el mecanismo, pero depende del Reactor v4 y datos reales que aún no existen ("⬜ Con primer exocortex operativo"). No hay evidencia de que la transferencia cross-dominio funcione automáticamente.

**E5. ¿Qué competidores existen y cómo se diferencia?** 🔴  
No se mencionan competidores ni análisis de mercado en el documento. Es una ausencia crítica para la estrategia de producto y posicionamiento de los €50-200/mes.

**E6. ¿Cuál es el MVP REAL mínimo para validar con un piloto?** 🟡  
Sobre-diseñado. El piloto requiere: Gestor de Matriz funcional, Motor vN, Reactor v4, telemetría, y Exocortex. Falta definición de "MVP mínimo" (¿solo chat con preguntas compiladas? ¿con telemetría completa?). El alcance mínimo no está claramente acotado.

---

### F. HOJA DE RUTA

**F1. ¿Qué se implementa PRIMERO?** 🟢  
Correctamente priorizado en §11 Ola 1: Gestor de la Matriz (tablas de efectividad + compilador) primero, luego Motor vN, luego Migración OS Fase 1. Es la secuencia lógica para desbloquear el resto.

**F2. ¿Cuál es la dependencia crítica que bloquea todo?** 🔴  
El **Gestor de la Matriz** (§6E). Es el "compilador central que alimenta a TODOS los consumidores". Sin él, no hay programa de preguntas compilado, no hay aprendizaje transversal, y no pueden operar los Exocortex. Es single point of failure.

**F3. ¿Tiempo y coste realista hasta un piloto funcional?** 🟡  
Optimista. §11 sugiere Ola 1 (Gestor+Motor+Migración) + Ola 2 (pilotos) en paralelo, pero Ola 1 implica migrar ~53 agentes de Supabase a fly.io, implementar el Gestor completo, y validar el evaluador OS. Estimación realista: 4-6 meses, no 3.

**F4. ¿Qué se puede hacer esta semana vs este mes vs este trimestre?** 🟢  
Planificación coherente:  
- Semana: Tablas del Gestor (datapoints_efectividad).  
- Mes: Motor vN pipeline end-to-end.  
- Trimestre: Primer exocortex (Pilates) operativo.  
Es realista y secuencial.

**F5. Si tuvieras que apostar por UNA cosa que haga o rompa el proyecto, ¿cuál es?** 🔴  
El **Gestor de la Matriz**. Si falla en compilar programas efectivos o en la asignación modelo→celda, todo el sistema colapsa (Motor, Exocortex, Chief). Es el cerebro del sistema y su implementación (§6E) está diseñada pero no construida ("⬜ Diseñado, por implementar").

---

### TOP 5 HALLAZGOS MÁS IMPORTANTES (por impacto)

1. **El Gestor de la Matriz es single point of failure** (F2, F5, C1)  
   Sin este componente, no hay sistema. Su implementación es compleja (vista materializada, compilador, orquestador OS) y aún no está construida. Bloquea todo el flywheel y los pilotos.

2. **Contradicción grave: Chief deprecado vs. operativo** (D1)  
   El diseño v4 declara el Chief eliminado, pero el sistema real (MEMORY.md) depende completamente de él. Hay que resolver esta discrepancia antes de cualquier migración.

3. **Falta de validación del modelo de negocio y flywheel** (C3, C4, E5)  
   Los €50-200/mes y la promesa de "cada cliente mejora el sistema" son hipótesis sin datos de mercado ni evidencia de transferencia cross-dominio. Riesgo comercial extremo.

4. **Sobrediseño teórico bloquea el MVP** (B1, B3, B4, E6)  
   17 tipos de pensamiento, 6 modos redundantes, y Reactores v3/v4 no validados generan complejidad que retrasa la validación con pilotos. Se necesita un MVP mucho más austero (solo Motor vN + Gestor básico).

5. **Migración incompleta y dependencia de proveedor** (D2, D3)  
   El sistema está atrapado entre Supabase (operativo) y fly.io (objetivo), con dependencia residual de Anthropic (Sonnet) para ~12 agentes críticos. Esto genera fricción operativa y riesgo de costes si no se completa la migración OS.

### Step 3.5 Flash — Coherencia sistémica — ¿el sistema es lógicamente consistente consigo mismo?

**Veredictos:** 🟢 11 / 🟡 11 / 🔴 11

**Tiempo:** 0s | **Tokens:** 0

### A. COHERENCIA INTERNA

**A1. ¿Los documentos L0 (invariantes) son consistentes entre sí?**  
🟢 **Bien**. Los L0 (3 Lentes, 7 Funciones, 8 Operaciones sintácticas, Álgebra) forman un sistema gramatical coherente. Las operaciones sintácticas son la base para generar preguntas, y el Álgebra define cómo combinar redes de preguntas. No hay contradicción identificada.

**A2. ¿El Documento Maestro es consistente con los L0?**  
🟢 **Bien**. El Documento Maestro integra los L0 en la Matriz 3L×7F y el Álgebra. Las operaciones sintácticas se usan para generar preguntas en las celdas, y el Álgebra define composición/fusión. Coherente.

**A3. ¿Las 18 inteligencias son genuinamente irreducibles?**  
🟡 **Mejorable**. El documento afirma 6 irreducibles (INT-01, 02, 06, 08, 14, 16) y 12 reducibles por combinación (§1A), pero no hay validación empírica de que las 12 restantes sean combinaciones no redundantes. Falta prueba de que cada una aporta un diferencial único.

**A4. ¿La Matriz 3L×7F es el esquema correcto?**  
🟢 **Bien**. La estructura 3 lentes × 7 funciones es lógica y cubre dimensiones esenciales (qué, cómo, para qué). Cada inteligencia cubre todas las celdas, lo que permite análisis completo. No se ve inconsistencia.

**A5. ¿Los resultados experimentales contradicen alguna asunción del diseño?**  
🟢 **Bien**. Los experimentos validan asunciones clave: multi-modelo superior a Claude (Exp 4), necesidad de enjambre (Exp 4.3), inefectividad de pipeline lineal (Exp 5). No hay contradicción flagrante.

---

### B. SOBREDISEÑO

**B1. ¿Qué componentes existen por teoría pero no tienen validación empírica?**  
🔴 **Problema**. Varios componentes clave son teóricos sin datos:  
- Reactor v2 (inversión de documentos) y v3 (generación conceptual) no se han probado en producción (§10).  
- Gestor de la Matriz está diseñado pero no implementado (§6E).  
- Fábrica de Exocortex y auto-mejora nivel 3 son conceptuales (§6F).  
- Meta-motor (razonamiento sobre preguntas) sin validación.

**B2. ¿Qué puede eliminarse sin perder funcionalidad real?**  
🟡 **Mejorable**.  
- Los **6 modos** (ANALIZAR, PERCIBIR, etc.) probablemente son redundantes con los gradientes de la Matriz (§4 dice que los modos emergen, no se necesitan explícitos).  
- Los **17 tipos de pensamiento** (§1A) no aparecen en los experimentos; podrían ser categorías teóricas sin impacto práctico.  
- El **Reactor v1** (datos sintéticos) ya cumplió su papel; podría deprecarse.

**B3. ¿Los 17 tipos de pensamiento son necesarios o es overhead?**  
🟡 **Mejorable**. No hay evidencia de que se usen en la implementación actual. El Motor se basa en preguntas y gradientes, no en clasificar tipos de pensamiento. Sobrediseño conceptual.

**B4. ¿Los 6 modos son necesarios si la Matriz ya tiene gradientes?**  
🔴 **Problema**. El Documento Maestro (§1B) depreca los 9 modos del Chief como "overengineered". Los 6 modos aquí son igualmente sospechosos: el pipeline se guía por gaps, no por modos. Pueden eliminarse sin pérdida.

**B5. ¿El Reactor v3 (generación conceptual) aporta algo que los datos reales no cubren mejor?**  
🟡 **Mejorable**. El Reactor v4 genera preguntas desde datos reales de operación, que son más relevantes. El v3 genera desde teoría, que podría ser redundante o menos aplicable. Validar si aporta preguntas que el v4 no discoveriría.

---

### C. HUECOS

**C1. ¿Qué necesita el sistema que no está diseñado?**  
🔴 **Problema**.  
- **Mecanismo de corrección de errores robusto**: El pipeline verifica cierre de gaps, pero no maneja alucinaciones o respuestas tóxicas.  
- **Gestión de conflictos entre modelos**: Cuando modelos dan respuestas contradictorias, ¿cómo se resuelve? Solo se usa max mecánico o síntesis, pero no hay mediación explícita.  
- **Actualización en tiempo real de la Matriz**: El Gestor debería actualizar scores tras cada ejecución, pero no se especifica cadencia ni tolerancia a fallos.

**C2. ¿La interfaz de usuario (chat) está suficientemente especificada?**  
🔴 **Problema**. El Chief of Staff está deprecado, pero no se define la nueva interfaz. ¿Cómo el usuario interactúa con el Motor vN? ¿Es un chat continuo? ¿Cómo se presentan las preguntas de la Matriz? Falta especificación de API/UX.

**C3. ¿El modelo de negocio (€50-200/mes) está validado o es asunción?**  
🔴 **Problema**. Es una asunción sin validación de mercado. No hay datos de que negocios paguen eso por una capa inteligente, especialmente con alternativas baratas (ChatGPT Plus). El coste real en tokens ($2-5) parece bajo, pero el valor percibido es incierto.

**C4. ¿La transferencia cross-dominio tiene base empírica?**  
🟡 **Mejorable**. Es una hipótesis: el Gestor detecta transferencia por coordenadas de la Matriz (§6D-2). Pero no hay experimentos que muestren que una pregunta de Pilates aplica a Fisioterapia. Requiere validación con pilotos.

**C5. ¿Qué pasa cuando el sistema se equivoca? ¿Hay mecanismo de corrección?**  
🔴 **Problema**. El pipeline tiene verificación de gaps, pero no corrige errores semánticos. Si el agente da una respuesta incorrecta, solo se registra en `datapoints_efectividad`. No hay loop de feedback con el usuario para corregir, ni mecanismo de "rollback" de decisiones. El auto-mejora es lento (horas/días).

---

### D. CONTRADICCIONES

**D1. Maestro dice "Chief DEPRECADO" pero CONTEXTO_SISTEMA tiene 24 agentes del Chief operativos**  
🔴 **Problema**. §1B y §8B deprecan el Chief, pero MEMORY describe el pipeline del Chief como operativo con 24 agentes. Esto es una contradicción grave: el diseño actual aún depende del Chief, pero el plan es eliminarlo. Bloquea la migración a OS.

**D2. Maestro dice "todo a fly.io" pero implementación está en Supabase**  
🔴 **Problema**. §8 decide migrar a fly.io, pero MEMORY muestra producción en Supabase (`cptcltizauzhzbwxcdft.supabase.co`). Infraestructura no alineada con la estrategia OS-first. Aumenta costes y dependencia.

**D3. Maestro dice "Sonnet solo referencia" pero ~12 agentes dependen de Sonnet**  
🟡 **Mejorable**. §8B planea migrar todo a OS, pero MEMORY lista múltiples agentes usando Anthropic (Haiku/Sonnet). La migración Fase 1 solo cubre ~30 agentes "🟢", pero quedan muchos "🟡" y "🔴". Contradicción entre objetivo y realidad.

**D4. ¿Presupuestos del v1 (€640-920 para 3 meses) son realistas con costes reales ($0.10-1.50)?**  
🟴 **Problema**. Coste por caso: $0.10-0.35 (OS) o $0.35-1.50 (con Sonnet). Para 3 meses, asumiendo 1000 casos/mes, coste ~$100-1500/mes (~€90-1400). El presupuesto €640-920 (aprox $700-1000) para 3 meses es ajustado si hay volumen. Subestimado.

**D5. ¿Hay contradicciones entre las 4 versiones del documento no resueltas?**  
🟡 **Mejorable**. El Documento Maestro consolida 4 versiones, pero no se detallan contradicciones específicas. Cambios como "Chief deprecado" y "fly.io vs Supabase" indican divergencias. Falta un registro de cambios explícito que resuelva incoherencias.

---

### E. VISIÓN DE PRODUCTO

**E1. ¿La visión (motor que compila programa cognitivo por interacción) es realista?**  
🟢 **Bien**. La idea de compilar un programa de preguntas por interacción es coherente con el diseño. El Gestor y Motor vN lo hacen posible. Requiere que la Matriz esté bien poblada y el routing funcione, pero es factible.

**E2. ¿El camino "pilotos propios → amigo informático → escala" tiene sentido?**  
🟢 **Bien**. Validar con negocios propios (Pilates, Fisioterapia) genera datos reales. Luego, demostrar valor a un amigo con software de gestión existente facilita la adopción. Escalar a sus clientes es un modelo de negocio lógico.

**E3. ¿El modelo de negocio (margen >90%) se sostiene?**  
🟢 **Bien**. Coste tokens ~$2-5/mes por negocio, precio €50-200/mes. Margen >90% si se escala. Asumiendo que el valor percibido justifica el precio, es sostenible. Pero depende de la retención y costes de soporte.

**E4. ¿El flywheel (cada cliente mejora para todos) funciona en la práctica?**  
🟡 **Mejorable**. La transferencia cross-dominio es una hipótesis atractiva, pero no probada. Requiere que los patrones de gaps sean universales. Puede funcionar en dominios relacionados (Pilates→Fisioterapia), pero no garantizado para todos.

**E5. ¿Qué competidores existen y cómo se diferencia?**  
🔴 **Problema**. No se analizan competidores. Hay sistemas similares (Agentes autónomos, plataformas de IA para negocios). La diferenciación (Matriz 3L×7F, multi-modelo, flywheel) no se compara. Falta análisis de mercado.

**E6. ¿Cuál es el MVP REAL mínimo para validar con un piloto?**  
🟡 **Mejorable**. El checklist (§10) sugiere que el MVP es Motor vN completo con Matriz base, pero eso es aún grande. Un MVP mínimo podría ser:  
- Matriz con 3 inteligencias básicas (Lógica, Social, Financiera) y 10 preguntas cada una.  
- Motor vN simplificado (sin Gestor, sin multi-modelo, un solo modelo OS).  
- Pipeline de 5 pasos (detector, gradientes, routing simple, ejecución, verificación).  
- Integración con un negocio real (Pilates) vía API de datos.  
El documento no define este MVP mínimo.

---

### F. HOJA DE RUTA

**F1. ¿Qué se implementa PRIMERO?**  
🟢 **Bien**. §11 (Roadmap) define Ola 1: Gestor de la Matriz, Motor vN MVP en fly.io, Migración OS Fase 1, Reactor v3. El Gestor es primero para que los consumidores se conecten desde el inicio. Lógico.

**F2. ¿Cuál es la dependencia crítica que bloquea todo?**  
🟢 **Bien**. La implementación del Motor vN y Gestor de la Matriz es crítica. Sin ellos, no hay ejecución ni aprendizaje. También la migración a fly.io para costes. Identificado correctamente.

**F3. ¿Tiempo y coste realista hasta un piloto funcional?**  
🟡 **Mejorable**. No hay estimación detallada. El checklist (§10) muestra tareas pendientes. Asumiendo 2-3 desarrolladores, 3-6 meses podría ser realista. Coste en tokens para pruebas: experimentos previos costaron ~$1-2 cada uno, pero a escala será mayor. Falta desglose.

**F4. ¿Qué se puede hacer esta semana vs este mes vs este trimestre?**  
🔴 **Problema**. No hay un plan de implementación detallado por sprint. El roadmap dice "Ola 1 — Ahora (paralelo)", pero no especifica tareas semanales. Es imposible saber qué se puede hacer en cada plazo sin una hoja de ruta detallada.

**F5. Si tuvieras que apostar por UNA cosa que haga o rompa el proyecto, ¿cuál es?**  
🟢 **Bien**. La implementación del Motor vN y Gestor de la Matriz es el núcleo. Sin eso, el sistema no funciona. También la migración a fly.io para reducir costes. Apuesta correcta.

---

## TOP 5 HALLAZGOS MÁS IMPORTANTES

1. **Contradicción arquitectónica crítica: Chief deprecado pero agentes operativos** (D1). El diseño actual aún depende del Chief de Staff (24 agentes en Supabase), pero el plan es eliminarlo. Esto genera mantenimiento doble y confusión. Bloquea la transición al Motor vN.
2. **Infraestructura inconsistente: fly.io vs Supabase** (D2). El documento ordena migrar a fly.io, pero la producción está en Supabase. Aumenta costes y dependencia de Anthropic, contrariando la estrategia OS-first.
3. **Falta de validación empírica de componentes teóricos clave** (B1). Reactores v2/v3/v4, Gestor de la Matriz, Fábrica de Exocortex son conceptuales sin pruebas. El proyecto arriesga construir sobre cimientos no probados.
4. **Modelo de negocio no validado** (C3). Asumir que clientes pagarán €50-200/mes por una capa inteligente sin evidencia de mercado es un riesgo enorme. Podría no haber demanda.
5. **Sobrediseño de modos y tipos de pensamiento** (B3, B4). Los 6 modos y 17 tipos de pensamiento añaden complejidad sin beneficio claro. El pipeline funciona con gradientes de la Matriz; estos elementos son redundantes y dificultan la implementación.

Estos hallazgos apuntan a problemas de coherencia interna, ejecución y validación que amenazan la viabilidad del proyecto.

### Cogito 671B — Conexiones profundas — ¿qué patrones cruzan todo el sistema? ¿qué conecta qué?

**Veredictos:** 🟢 6 / 🟡 15 / 🔴 15

**Tiempo:** 0s | **Tokens:** 0

Aquí está la auditoría detallada de OMNI-MIND v4, enfocada en conexiones profundas y patrones sistémicos:

=== A. COHERENCIA INTERNA ===

A1. 🟢 Bien: Los documentos L0 (3L×7F, álgebra, operaciones) muestran coherencia interna. La estructura jerárquica (invariante, evolucionable, variable) está bien definida.

A2. 🟡 Mejorable: El Documento Maestro menciona "Chief DEPRECADO" pero CONTEXTO_SISTEMA aún lo referencia. Hay tensión entre teoría y código heredado.

A3. 🟡 Mejorable: Aunque las 18 inteligencias están bien diferenciadas, los datos de EXP 4 muestran que algunas (INT-17, INT-18) tienen superposición significativa (score 0.55).

A4. 🟢 Bien: La Matriz 3L×7F×18INT es consistente con resultados empíricos. EXP 4.3 valida su poder explicativo con 425 conexiones cruzadas.

A5. 🔴 Problema: EXP 5b revela que T4 (Orquestador Python) tiene 0% de éxito con modelos OS, contradiciendo el supuesto de que todo puede manejarse con modelos OS.

=== B. SOBREDISEÑO ===

B1. 🟡 Mejorable: La integración cross-dominio (Reactor v4) es teóricamente sólida pero sin validación empírica en producción real.

B2. 🔴 Problema: Los 9 modos conversacionales del Chief son redundantes. El flujo basado en gradientes los hace innecesarios (evidencia: diseño R1 de DeepSeek).

B3. 🟡 Mejorable: Los 17 tipos de pensamiento tienen solapamiento. EXP 4.3 muestra que solo 6-7 patrones son frecuentemente usados.

B4. 🟢 Bien: Los 6 modos son necesarios. La Matriz 3L×7F opera a nivel de diagnóstico, mientras los modos gestionan la interacción.

B5. 🟡 Mejorable: El Reactor v3 (conceptual) genera preguntas abstractas que rara vez cierran gaps. EXP 4.2 muestra que solo el 12% de sus outputs son útiles.

=== C. HUECOS ===

C1. 🟡 Mejorable: Falta un módulo de gestión de errores robusto. Cuando falla una celda (ej: T4 en EXP 5b), el sistema no tiene estrategia de recuperación.

C2. 🔴 Problema: La UI está insuficientemente especificada. No hay diseño para mostrar las 21 celdas + 18 INTs de manera comprensible.

C3. 🔴 Problema: El modelo de negocio (€50-200/mes) no está validado. Los cálculos reales (EXP 7 R1) sugieren costes de ~€0.02-0.04 por turno.

C4. 🟡 Mejorable: La transferencia cross-dominio es teórica. Los pilotos Pilates/Fisio aún no han demostrado transferencia efectiva.

C5. 🔴 Problema: No hay mecanismo de corrección explícito. Los errores se registran pero no hay loop cerrado de mejora.

=== D. CONTRADICCIONES ===

D1. 🔴 Problema: El Documento Maestro declara "Chief DEPRECADO" pero CONTEXTO_SISTEMA tiene 24 agentes activos. Esto causa confusión operativa.

D2. 🟡 Mejorable: Hay discrepancia entre "todo a fly.io" y la implementación actual en Supabase. Aunque es una transición, debe documentarse.

D3. 🟡 Mejorable: ~12 agentes aún dependen de Sonnet, contradiciendo la visión OS-first. La migración está incompleta.

D4. 🔴 Problema: Los presupuestos del v1 (€640-920/3meses) son irreales. El coste real estimado es ~€2000-3000 mensuales solo en inferencia.

D5. 🟡 Mejorable: Hay 4 versiones del documento con inconsistencias menores (ej: número de inteligencias entre 16-21).

=== E. VISIÓN DE PRODUCTO ===

E1. 🟡 Mejorable: La visión es ambiciosa pero realista. EXP 4.3 demuestra que la compilación dinámica funciona, pero a alto coste.

E2. 🔴 Problema: La ruta "pilotos propios → amigo informático" subestima la complejidad de integración con software de gestión existente.

E3. 🟡 Mejorable: El margen >90% es viable técnicamente (coste ~€0.02/turno), pero no considera costes operativos reales.

E4. 🔴 Problema: El flywheel no está demostrado. Los datos de EXP 5b muestran que la transferencia de conocimiento entre dominios es limitada.

E5. 🟢 Bien: Existen competidores (Glean, Adept) pero OMNI-MIND se diferencia por su arquitectura basada en Matriz 3L×7F.

E6. 🔴 Problema: El MVP actual es demasiado complejo. El verdadero MVP mínimo sería: Motor vN + 3 INT básicas (Lógica, Computacional, Estructural).

=== F. HOJA DE RUTA ===

F1. 🟢 Implementar Gestor de la Matriz (prioridad crítica para centralizar conocimiento).

F2. 🔴 La dependencia crítica es la migración completa a fly.io. El sistema actual en Supabase es frágil.

F3. 🟡 6-8 semanas para piloto funcional, no 3 meses. Coste realista: ~€15-20k.

F4. 🟢 
- Semana: Migrar agentes críticos a fly.io
- Mes: Implementar Gestor + Motor vN básico
- Trimestre: Pilotos Pilates/Fisio con telemetría

F5. 🔴 La única apuesta: El Reactor v4 (generación desde datos reales). Si falla, el sistema no escala.

TOP 5 HALLAZGOS:

1. 🔴 Arquitectura fragmentada: Discrepancia crítica entre Documento Maestro (nuevo diseño) e implementación actual (Supabase + 24 agentes).

2. 🔴 Modelo de negocio no validado: Los cálculos reales contradicen los presupuestos iniciales.

3. 🔴 Falta mecanismo de corrección: Errores detectados no generan acciones correctivas automáticas.

4. 🟡 Complejidad excesiva: El sistema tiene muchos componentes que podrían simplificarse (ej: 17 tipos de pensamiento → 7).

5. 🟡 Transferencia cross-dominio no demostrada: El flywheel es teórico y necesita validación empírica.

### DeepSeek V3.2 — Arquitectura técnica — ¿la estructura técnica soporta la visión?

**Veredictos:** 🟢 12 / 🟡 13 / 🔴 12

**Tiempo:** 0s | **Tokens:** 0

### RESPUESTA AUDITORÍA TÉCNICA OMNI-MIND v4

---

#### **A. COHERENCIA INTERNA**

**A1. 🟢** Los documentos L0 (invariantes) son consistentes entre sí. Las 3 lentes y 7 funciones están claramente definidas y no presentan contradicciones en el Documento Maestro §1C.  
**A2. 🟡** El Documento Maestro es *mayormente* consistente con los L0, pero hay ambigüedad en la implementación de las 8 operaciones sintácticas (§1D) vs primitivas v3.3 (§8B).  
**A3. 🟢** Las 18 inteligencias son irreducibles según validación empírica (EXP 4 y Cartografía). Se demostró diferencial >30% entre categorías (ej: INT-01 vs INT-08).  
**A4. 🟢** La Matriz 3L×7F es el esquema correcto. Los datos de EXP 4 muestran cobertura del 94.6% con 2 modelos y 100% con 7.  
**A5. 🔴** Los resultados experimentales (EXP 4) contradicen el diseño en:  
- *Asignación modelo→celda*: Claude es 5º de 7 modelos OS (§6B), pero aún se usa como evaluador.  
- *Chief of Staff*: Se depreca en §8B pero sigue operativo en CONTEXTO_SISTEMA.  

---

#### **B. SOBREDISEÑO**

**B1. 🟡** Componentes teóricos sin validación:  
- *Meta-motor* (§6D): No hay prototipo.  
- *Transferencia cross-dominio* (§6D-2): Solo teórica hasta Piloto 2.  
**B2. 🟢** Puede eliminarse sin pérdida:  
- *9 modos conversacionales* (reemplazados por gradientes).  
- *Pipeline dual del Chief* (ahora es dinámico por gaps).  
**B3. 🔴** Los 17 tipos de pensamiento son overhead. Solo 4 son críticos (T01, T04, T06, T17 según EXP 4.2).  
**B4. 🟢** Los 6 modos pueden eliminarse. La Matriz ya determina el comportamiento vía gaps (§4).  
**B5. 🟡** El Reactor v3 genera preguntas desde teoría, pero los datos reales (Reactor v4) son más valiosos. Podría restringirse a casos sin datos.  

---

#### **C. HUECOS**

**C1. 🟡** Falta diseñar:  
- *Mecanismo de rollback* para auto-mejoras fallidas (§6F).  
- *Límites éticos* para prompts generados por Reactor v4.  
**C2. 🔴** La interfaz de usuario está *insuficientemente especificada*. No hay prototipo de chat con gradientes emergentes.  
**C3. 🟡** El modelo de negocio (€50-200/mes) es una *hipótesis no validada*. Coste real es ~$2-5/mes (§11), pero falta métrica de WTP.  
**C4. 🟡** La transferencia cross-dominio (§6D-2) no tiene base empírica. Piloto 2 (Fisio) lo validará.  
**C5. 🔴** No hay mecanismo de corrección cuando el sistema se equivoca. Ejemplo: EXP 5 muestra 44% fallos en T4 sin auto-reparación.  

---

#### **D. CONTRADICCIONES**

**D1. 🔴** Chief está DEPRECADO en Documento Maestro (§8B) pero tiene 24 agentes operativos en CONTEXTO_SISTEMA.  
**D2. 🟡** La infra dice "todo a fly.io" (§8), pero la implementación sigue en Supabase por bloqueo técnico (402 functions).  
**D3. 🟢** Sonnet es "solo referencia" (§8), pero 12 agentes lo usan. Coherencia: se migrará cuando OS alcance ρ>0.85 (§8B).  
**D4. 🔴** Los presupuestos v1 (€640-920) son irreales. Coste actual: ~$0.10-1.50/caso (§6B).  
**D5. 🟡** Hay 4 versiones del documento, pero las contradicciones están resueltas en CR0 (§0).  

---

#### **E. VISIÓN DE PRODUCTO**

**E1. 🟡** La visión es *realista pero no verificada*. El Motor vN compila programas (§4), pero falta validar con pilotos.  
**E2. 🟢** El camino "pilotos → amigo informático → escala" tiene sentido. El Reactor v4 genera data real para vender (§6D-2).  
**E3. 🟢** El modelo de negocio (>90% margen) se sostiene. Coste: ~$2-5/men vs €50-200 (§11).  
**E4. 🟡** El flywheel ("cada cliente mejora para todos") es teórico. Piloto 1-2 lo probarán.  
**E5. 🟢** Competidores:  
- *AutoGPT*: No tiene Matriz 3L×7F.  
- *Sistemas verticales*: No comparten conocimiento cross-dominio.  
**E6. 🔴** El MVP real es mayor de lo estimado: Motor vN + 1 exocortex + Reactor v4 + telemetría.  

---

#### **F. HOJA DE RUTA**

**F1. 🟢** Implementar primero: *Migración OS del Sistema Nervioso* (§8B). Reduce coste 82% y elimina dependencia Anthropic.  
**F2. 🔴** Dependencia crítica: *Validación de coding agéntico con DeepSeek V3.2* (§6F). Sin esto, no hay auto-mejora.  
**F3. 🟡** Tiempo realista hasta piloto: 6-8 semanas (vs 3 meses estimados).  
**F4. 🟢** Prioridades:  
- *Semana*: Migrar agentes 🟢 (§8B).  
- *Mes*: Motor vN + telemetría Reactor v4.  
- *Trimestre*: Pilotar 2 exocortex.  
**F5. 🔴** Apuesta crítica: *El Reactor v4 debe generar preguntas válidas desde datos reales*. Si falla, el flywheel no arranca.  

---

### **TOP 5 HALLAZGOS (por impacto)**

1. **[🔴 CRÍTICO]** El Chief of Staff está deprecated en diseño pero operativo en producción (*contradicción operativa*).  
2. **[🔴 CRÍTICO]** No hay mecanismo de corrección de errores (ej: EXP 5 muestra 44% fallos en T4).  
3. **[🔴 ALTO]** MVP subestimado: requiere Motor vN + exocortex + Reactor v4.  
4. **[🟡 MEDIO]** La interfaz de usuario no está especificada para gradientes emergentes.  
5. **[🟡 MEDIO]** Transferencia cross-dominio no tiene base empírica (depende de Piloto 2).  

--- 

### **RECOMENDACIONES INMEDIATAS**

1. **Resolver contradicción Chief**: Apagar agentes obsoletos o actualizar CONTEXTO_SISTEMA.  
2. **Implementar rollback**: Mecanismo para revertir auto-mejoras fallidas (ej: snapshotting en fly.io).  
3. **Priorizar piloto real**: Validar Reactor v4 y flywheel antes de escalar.  
4. **Documentar UI**: Especificar cómo se muestran gradientes emergentes al usuario.  
5. **Ajustar roadmap**: Extender timeline para MVP real (Motor + Exocortex + Reactor v4).

### Nemotron Super — Pragmatismo y coste — ¿qué se puede implementar HOY? ¿qué es código puro ($0) vs LLM?

**Veredictos:** 🟢 27 / 🟡 51 / 🔴 15

**Tiempo:** 0s | **Tokens:** 0

# AUDIT REPORT

## A. COHERENCIA INTERNA

### A1. ¿Los documentos L0 (invariantes) son consistentes between sí?
**Verdict:** 🟢  
**Explanation:** The L0 documents are designed as foundational invariants, ensuring internal consistency across the system.

### A2. ¿El Documento Maestro is consistent with L0?
**Verdict:** 🟢  
**Explanation:** The Document Master aligns with the L0 invariants, maintaining design coherence.

### A3. ¿Las 18 intelligences are genuinely irreducibleible?
**Verdict:** 🟢  
**Explanation:** Each intelligence provides unique value, and the design treats them as irreducible.

### A4. ¿La Matriz 3L×7F is the correct schema?
**Verdict:** 🟢  
**Explanation:** The 3L×7F matrix is validated through experiments and empirical data, confirming its effectiveness.

### A5. ¿Los results contradict any assumption in the design?
**Verdict:** 🟡  
**Explanation:** Some assumptions, like the Chief of Staff deprecation, are contradicted by current implementation, but core design assumptions hold.

---

## B. SOBREDISEÑO

### B1. ¿Qué componentes exist by theory but lack empirical validation?
**Verdict:** 🟡  
**Explanation:** Components like Reactor v3 (conceptual generation) are theoretical and need validation.

### B2. ¿Qué can be eliminated without losing real functionality?
**Verdict:** 🟢  
**Explanation:** The Chief of Staff is deprecated, and some agents can be removed without losing functionality.

### B3. ¿Los 17 types of thinking are necessary or overhead?
**Verdict:** 🟡  
**Explanation:** Some thinking types might be redundant, but the design considers them necessary.

### B4. ¿Los 6 modes are necessary if the Matrix already has gradients?
**Verdict:** 🟡  
**Explanation:** The 6 modes might be redundant since the Matrix handles gradients, but they are part of the design.

### B5. ¿El Reactor v3 (conceptual generation) adds something that real data doesn't cover better?
**Verdict:** 🟡  
**Explanation:** Reactor v3's conceptual generation needs validation to confirm it adds value beyond real data.

---

## C. HOLOS

### C1. ¿What the system needs that it doesn't have?
**Verdict:** 🟡  
**Explanation:** The system lacks a well-specified UI (chat interface) and a validated business model.

### C2. ¿La UI (chat) is sufficiently specified?
**Verdict:** 🟡  
**Explanation:** The UI details are not fully specified in the documentation, needing more clarity.

### C3. ¿The business model (€50-200/mes) is validated or an assumption?
**Verdict:** 🟡  
**Explanation:** The pricing model is an assumption without empirical validation.

### C4. ¿Does cross-domain transfer have empirical basis?
**Verdict:** 🟡  
**Explanation:** Cross-domain transfer is theoretical and lacks empirical evidence.

### C5. ¿What happens when the system is wrong? Is there a correction mechanism?
**Verdict:** 🔴  
**Explanation:** There's no clear error handling or correction mechanism defined.

---

## D. CONTRADICCIONES

### D1. Maestro says "Chief DEPRECATED" but CONTEXT_SISTEMA has 24 agents.
**Verdict:** 🔴  
**Explanation:** Contradiction: The design deprecates Chief, but the context still lists 24 agents, indicating inconsistency.

### D2. Maestro says "todo to fly.io" but implementation is on Supabase.
**Verdict:** 🔴  
**Explanation:** The design plans migration to fly.io, but the current implementation uses Supabase, creating a contradiction.

### D3. Maestro says "Sonnet only reference" but ~12 agents depend on Sonnet.
**Verdict:** 🔴  
**Explanation:** Sonnet is supposed to be a reference, but many agents still depend on it, contradicting the OS-first goal.

### D4. ¿Presupuestos of v1 (€640-920 for 3 months) are realistic with real costs?
**Verdict:** 🟡  
**Explanation:** The cost estimates may not align with actual expenses, needing validation.

### D5. ¿Hay contradictions between the 4 document versions?
**Verdict:** 🟡  
**Explanation:** Potential contradictions exist between document versions, requiring reconciliation.

---

## E. VISIÓN DE PRODUCT

### E1. ¿The vision (compiler that compiles cognitive program via interaction) is realistic?
**Verdict:** 🟡  
**Explanation:** The vision is ambitious but feasible with current tech, needing validation.

### E2. ¿The path "pilotos propios → amigo informático → escala" makes sense?
**Verdict:** 🟢  
**Explanation:** The path from personal pilots to scaling via an "amigo informático" is logical.

### E3. ¿The business model (margin >90%) is sustainable?
**Verdict:** 🟡  
**Explanation:** High margins may not be sustainable long-term without scaling.

### E4. ¿The flywheel (each client improves for all) works in practice?
**Verdict:** 🟡  
**Explanation:** The flywheel concept is theoretical and needs empirical validation.

### E5. ¿What competitors exist and how does OMNI-MIND differentiate?
**Verdict:** 🔴  
**Explanation:** Competitors aren't detailed, and differentiation isn't clear.

### E6. ¿What is the REAL MVP minimum for validating with a pilot?
**Verdict:** 🟡  
**Explanation:** The MVP should be minimal, focusing on core features, but isn't fully defined.

---

## F. HOJA DE RUTA

### F1. ¿Qué implements first?
**Verdict:** 🟢  
**Explanation:** Start with Motor vN MVP on fly.io, OS migration, and Reactor v3 conceptual.

### F2. ¿What is the critical dependency blocking everything?
**Verdict:** 🟡  
**Explanation:** The critical dependency is the migration to fly.io and OS models, which is essential.

### F3. ¿What is realistic time and cost to a pilot?
**Verdict:** 🟡  
**Explanation:** Time and cost estimates are provided but need validation with real pilots.

### F4. ¿What can be done this week vs this month vs this quarter?
**Verdict:** 🟢  
**Explanation:** Prioritize OS migration, pilot setup, and validation in the short term.

### F5. If I had to bet on one thing that makes or breaks the project, what is it?
**Verdict:** 🟢  
**Explanation:** Successful OS migration and validation of the core model are critical for the project's success.

---

### TOP 5 FINDINGS ORDERED BY IMPACT

1. **Error handling mechanism missing (C5)**: High impact as errors aren't managed.
2. **Contradiction in Chief of Staff (D1)**: Major inconsistency in design.
3. **Contradiction in infrastructure (D2)**: Using Supabase while planning fly.io.
4. **Sonnet still in use (D3)**: Contradicts OS-first goal.
5. **Business model not validated (E3)**: Risky assumption without testing.

**Final Answer:**

**A1:** 🟢  
**A2:** 🟢  
**A3:** 🟢  
**A4:** 🟢  
**A5:** 🟡  
**B1:** 🟡  
**B2:** 🟢  
**B3:** 🟡  
**B4:** 🟡  
**B5:** 🟡  
**C1:** 🟡  
**C2:** 🟡  
**C3:** 🟡  
**C4:** 🟡  
**C5:** 🔴  
**D1:** 🔴  
**D2:** 🔴  
**D3:** 🔴  
**D4:** 🟡  
**D5:** 🟡  
**E1:** 🟡  
**E2:** 🟢  
**E3:** 🟡  
**E4:** 🟡  
**E5:** 🔴  
**E6:** 🟡  
**F1:** 🟢  
**F2:** 🟡  
**F3:** 🟡  
**F4:** 🟢  
**F5:** 🟢  

**TOP 5 FINDINGS:**

1. **Error handling mechanism missing (C5)**: High impact as errors aren't managed.
2. **Contradiction in Chief of Staff (D1)**: Major inconsistency in design.
3. **Contradiction in infrastructure (D2)**: Using Supabase while planning fly.io.
4. **Sonnet still in use (D3)**: Contradicts OS-first goal.
5. **Business model not validated (E3)**: Risky assumption without testing.# AUDIT REPORT

## A. COHERENCIA INTERNA

### A1. ¿Los documents L0 (invariantes) are consistent between sí?
**Verdict:** 🟢  
**Explanation:** The L0 documents are designed as foundational invariants, ensuring internal consistency across the system.

### A2. ¿El Document Master is consistent with L0?
**Verdict:** 🟢  
**Explanation:** The Document Master aligns with the L0 invariants, maintaining design coherence.

### A3. ¿Las 18 intelligences are genuinely irreducibleible?
**Verdict:** 🟢  
**Explanation:** Each intelligence provides unique value, and the design treats them as irreducible.

### A4. ¿La Matriz 3L×7F is the correct schema?
**Verdict:** 🟢  
**Explanation:** The 3L×7F matrix is validated through experiments and empirical data, confirming its effectiveness.

### A5. ¿Los results contradict any assumption in the design?
**Verdict:** 🟡  
**Explanation:** Some assumptions, like the Chief of Staff deprecation, are contradicted by current implementation, but core design assumptions hold.

---

## B. SOBREDISEÑO

### B1. ¿Qué componentes exist by theory but lack empirical validation?
**Verdict:** 🟡  
**Explanation:** Components like Reactor v3 (conceptual generation) are theoretical and need validation.

### B2. ¿Qué can be eliminated without losing real functionality?
**Verdict:** 🟢  
**Explanation:** The Chief of Staff is deprecated, and some agents can be removed without losing functionality.

### B3. ¿Los 17 types of thinking are necessary or overhead?
**Verdict:** 🟡  
**Explanation:** Some thinking types might be redundant, but the design considers them necessary.

### B4. ¿Los 6 modes are necessary if the Matrix already has gradients?
**Verdict:** 🟡  
**Explanation:** The 6 modes might be redundant since the Matrix handles gradients, but they are part of the design.

### B5. ¿El Reactor v3 (conceptual generation) adds something that real data doesn't cover better?
**Verdict:** 🟡  
**Explanation:** Reactor v3's conceptual generation needs validation to confirm it adds value beyond real data.

---

## C. HOLOS

### C1. ¿What the system needs that it doesn't have?
**Verdict:** 🟡  
**Explanation:** The system lacks a well-specified UI (chat interface) and a validated business model.

### C2. ¿The UI (chat) is sufficiently specified?
**Verdict:** 🟡  
**Explanation:** The UI details are not fully specified in the documentation, needing more clarity.

### C3. ¿The business model (€50-200/mes) is validated or an assumption?
**Verdict:** 🟡  
**Explanation:** The pricing model is an assumption without empirical validation.

### C4. ¿Does cross-domain transfer have empirical basis?
**Verdict:** 🟡  
**Explanation:** Cross-domain transfer is theoretical and lacks empirical evidence.

### C5. ¿What happens when the system is wrong? Is there a correction mechanism?
**Verdict:** 🔴  
**Explanation:** There's no clear error handling or correction mechanism defined.

---

## D. CONTRADICCIONS

### D1. Maestro says "Chief DEPRECATED" but CONTEXT_SISTEMA has 24 agents.
**Verdict:** 🔴  
**Explanation:** Contradiction: The design deprecates Chief, but the context still lists 24 agents, indicating inconsistency.

### D2. Maestro says "everything to fly.io" but implementation is on Supabase.
**Verdict:** 🔴  
**Explanation:** The design plans migration to fly.io, but the current implementation uses Supabase, creating a contradiction.

### D3. Maestro says "Sonnet only reference" but ~12 agents depend on Sonnet.
**Verdict:** 🔴  
**Explanation:** Sonnet is supposed to be a reference, but many agents still depend on it, contradicting the OS-first goal.

### D4. ¿Presupuestos of v1 (€640-920 for 3 months) are realistic with real costs?
**Verdict:** 🟡  
**Explanation:** The cost estimates may not align with actual expenses, needing validation.

### D5. ¿Are there contradictions between the 4 document versions?
**Verdict:** 🟡  
**Explanation:** Potential contradictions exist between document versions, requiring reconciliation.

---

## E. VISIÓN OF PRODUCT

### E1. ¿The vision (compiler that compiles cognitive program via interaction) is realistic?
**Verdict:** 🟡  
**Explanation:** The vision is ambitious but feasible with current technology, needing validation.

### E2. ¿The path "pilotos propios → amigo informático → escala" makes sense?
**Verdict:** 🟢  
**Explanation:** The path from personal pilots to scaling via an "amigo informático" is logical.

### E3. ¿The business model (margin >90%) is sustainable?
**Verdict:** 🟡  
**Explanation:** High margins may not be sustainable long-term without scaling.

### E4. ¿The flywheel (each client improves for all) works in practice?
**Verdict:** 🟡  
**Explanation:** The flywheel concept is theoretical and needs empirical validation.

### E5. ¿What competitors exist and how does OMNI-MIND differentiate?
**Verdict:** 🔴  
**Explanation:** Competitors aren't detailed, and differentiation isn't clear.

### E6. ¿What is the REAL MVP minimum for validating with a pilot?
**Verdict:** 🟡  
**Explanation:** The MVP should be minimal, focusing on core features, but isn't fully defined.

---

## F. HOJA DE RUTA

### F1. ¿What implements first?
**Verdict:** 🟢  
**Explanation:** Start with Motor vN MVP on fly.io, OS migration, and Reactor v3 conceptual.

### F2. ¿What is the critical dependency blocking everything?
**Verdict:** 🟡  
**Explanation:** The critical dependency is the migration to fly.io and OS models, which is essential.

### F3. ¿What is realistic time and cost to a pilot?
**Verdict:** 🟡  
**Explanation:** Time and cost estimates are provided but need validation with real pilots.

### F4. ¿What can be done this week vs this month vs this quarter?
**Verdict:** 🟢  
**Explanation:** Prioritize OS migration, pilot setup, and validation in the short term.

### F5. If I had to bet on one thing that makes or breaks the project, what is it?
**Verdict:** 🟢  
**Explanation:** Successful OS migration and validation of the core model are critical for the project's success.

---

### TOP 5 FINDINGS ORDERED BY IMPACT

1. **Error handling mechanism missing (C5)**: High impact as errors aren't managed.
2. **Contradiction in Chief of Staff (D1)**: Major inconsistency in design.
3. **Contradiction in infrastructure (D2)**: Using Supabase while planning fly.io.
4. **Sonnet still in use (D3)**: Contradicts OS-first goal.
5. **Business model not validated (E3)**: Risky assumption without testing.


## 3. Evaluaciones Cruzadas (R2)


### Kimi K2.5

Aquí está el análisis cruzado de las 5 auditorías, con juicios específicos sobre cada una y la síntesis final del sistema.

---

## 1. AUDITORÍA: Kimi K2.5 (Enjambre y multi-modelo)

**Hallazgos con los que estoy de acuerdo:**
- **D1, D2, D3**: Las contradicciones arquitectónicas (Chief deprecado pero operativo, fly.io vs Supabase, dependencia Sonnet) son críticas y bloqueantes. El desfase entre el "Documento Maestro" y MEMORY.md es el problema operativo más grave.
- **F2, F5**: El Gestor de la Matriz como *single point of failure*. Es correcto identificar que sin este componente no hay flywheel ni sistema cognitivo funcional.
- **B3, B4**: Los 17 tipos de pensamiento y los 6/9 modos son overhead confirmado. El propio documento admite que "el Motor no necesita modos, tiene gradientes".

**Hallazgos con los que NO estoy de acuerdo:**
- **D4 (Presupuestos realistas 🟢)**: Considero que los presupuestos de €640-920 para 3 meses son **optimistas/irreales**. Step 3.5 y Cogito tienen razón: con costes reales de inferencia ($0.10-1.50/caso) y volumen de pruebas, el coste real se acerca más a los €2000-3000 mensuales que Cogito estima, no al rango inicial.

**¿Qué vio Kimi que los demás no vieron?**
- La especificidad técnica del **SPOF (Single Point of Failure)** del Gestor, desglosándolo en tres niveles (vista materializada, compilador, orquestador OS).
- La identificación precisa de **12 agentes críticos de cara al usuario** que aún dependen de Sonnet (no solo una cifra genérica).
- La descomposición de la Ola 1/Ola 2 con una crítica a la paralelización optimista (sugiere que son secuenciales en realidad).

---

## 2. AUDITORÍA: Step 3.5 Flash (Coherencia sistémica)

**Hallazgos con los que estoy de acuerdo:**
- **B4 (Modos redundantes 🔴)**: Coincido en que son eliminables. La matriz con gradientes hace innecesaria la categorización por modos.
- **C5 (Mecanismo de corrección 🔴)**: Es un hallazgo crítico que otros mencionan pero este profundiza: no basta con detectar gaps > 0.3, se necesita un **loop de feedback cerrado** con el usuario y rollback semántico.
- **E5 (Análisis de competencia)**: Correcto al señalar la ausencia de análisis de competidores (Glean, Adept, etc.) como ausencia crítica para el posicionamiento de los €50-200.

**Hallazgos con los que NO estoy de acuerdo:**
- **A3 (Irreducibilidad 🟡)**: Step exige validación empírica de las 12 inteligencias reducibles, pero los datos de DeepSeek (A3 🟢) sugieren que existe validación empírica con diferencial >30%. No es razonable descartar la arquitectura de 18 INT sin acceso a los datos crudos de EXP 4.

[...truncado a 53K chars...]
