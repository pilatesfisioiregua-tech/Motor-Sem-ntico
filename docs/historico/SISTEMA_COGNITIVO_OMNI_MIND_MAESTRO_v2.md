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
