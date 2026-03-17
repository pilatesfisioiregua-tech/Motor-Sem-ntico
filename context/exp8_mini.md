# OMNI-MIND v4 — CONTEXTO MINI

## EXP 8 — Versión mini (~40K tokens)
---



================================================================================
# [CLAVE] MAESTRO v4 (§0,§1,§4,§8,§11,§12)
================================================================================

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


---




================================================================================
# [MINI] CONTEXTO SISTEMA (§1, §4 Enjambres)
================================================================================

## 1. QUÉ ES OMNI-MIND

Un **sistema operativo cognitivo** construido sobre Supabase Edge Functions (Deno/TypeScript). Funciona como un "exocortex": el usuario (Jesús) interactúa via chat; el sistema analiza su input con múltiples agentes especializados que trabajan en paralelo sin llamarse entre sí — se comunican via **estigmergia** (marcas en base de datos que otros agentes leen).

**Modelo mental**: Colmena de agentes. Cada uno lee marcas, hace su trabajo, deja una marca nueva. Un orquestador decide el orden. Nadie manda a nadie directamente.

---


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


---




================================================================================
# [MINI] META-RED 18 INTELIGENCIAS
================================================================================

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

[...truncado a 12K chars...]



================================================================================
# [COMPLETO] MAPA MODELOS
================================================================================

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




================================================================================
# [COMPLETO] RESULTADOS EXPERIMENTALES
================================================================================

### EXP 4 — Mesa Redonda Principal

# EXP 4 — MESA REDONDA (13 modelos, 2 rondas)

## Ranking de Aporte

| # | Modelo | Valor | R1 medio | R2 medio | Δ | 3+ R1 | 3+ R2 | Aportes | Absorcion | Angulos | Inflacion |
|---|--------|-------|----------|----------|---|-------|-------|---------|-----------|---------|-----------|
| 1 | gpt-oss-120b | 118 | 1.26 | 2.74 | +1.49 | 14 | 66 | 0 | 82 | 18 | 0 |
| 2 | qwen3-235b | 98 | 2.54 | 3.19 | +0.65 | 58 | 87 | 31 | 25 | 7 | 17 |
| 3 | opus | 90 | 1.50 | 2.77 | +1.27 | 19 | 67 | 0 | 66 | 12 | 0 |
| 4 | v3.2-chat | 79 | 1.54 | 2.86 | +1.31 | 7 | 76 | 0 | 55 | 12 | 0 |
| 5 | deepseek-v3.1 | 55 | 1.66 | 2.80 | +1.14 | 10 | 74 | 0 | 33 | 11 | 0 |
| 6 | glm-4.7 | 45 | 1.81 | 2.42 | +0.61 | 15 | 54 | 0 | 29 | 8 | 0 |
| 7 | cogito-671b | 42 | 1.52 | 2.88 | +1.35 | 6 | 77 | 6 | 16 | 10 | 6 |
| 8 | kimi-k2.5 | 30 | 2.06 | 2.47 | +0.41 | 28 | 48 | 0 | 18 | 6 | 0 |
| 9 | deepseek-r1 | 0 | 1.57 | 1.57 | +0.00 | 12 | 12 | 0 | 0 | 0 | 0 |
| 10 | minimax-m2.5 | 0 | 1.60 | 1.79 | +0.19 | 14 | 17 | 0 | 0 | 0 | 0 |
| 11 | sonnet | 0 | 2.00 | 2.00 | +0.00 | 32 | 32 | 0 | 0 | 0 | 0 |
| 12 | v3.2-reasoner | 0 | 1.42 | 1.42 | +0.00 | 9 | 9 | 0 | 0 | 0 | 0 |

## Fichas por Modelo

### gpt-oss-120b (prescindible)
R1: medio=1.26, 3+=14. R2: medio=2.74, 3+=66 (Δ=+1.49). Aportes unicos: 0. Absorcion: 82 (mas de qwen3-235b). Angulos: 18. Inflacion: 0. Valor: 118. Sin el: pierde 0.0% de celdas 3+.

### qwen3-235b (valioso)
R1: medio=2.54, 3+=58. R2: medio=3.19, 3+=87 (Δ=+0.65). Aportes unicos: 31. Absorcion: 25 (mas de kimi-k2.5). Angulos: 7. Inflacion: 17. Valor: 98. Sin el: pierde 8.6% de celdas 3+.

### opus (prescindible)
R1: medio=1.50, 3+=19. R2: medio=2.77, 3+=67 (Δ=+1.27). Aportes unicos: 0. Absorcion: 66 (mas de qwen3-235b). Angulos: 12. Inflacion: 0. Valor: 90. Sin el: pierde 0.0% de celdas 3+.

### v3.2-chat (prescindible)
R1: medio=1.54, 3+=7. R2: medio=2.86, 3+=76 (Δ=+1.31). Aportes unicos: 0. Absorcion: 55 (mas de qwen3-235b). Angulos: 12. Inflacion: 0. Valor: 79. Sin el: pierde 0.0% de celdas 3+.

### deepseek-v3.1 (prescindible)
R1: medio=1.66, 3+=10. R2: medio=2.80, 3+=74 (Δ=+1.14). Aportes unicos: 0. Absorcion: 33 (mas de qwen3-235b). Angulos: 11. Inflacion: 0. Valor: 55. Sin el: pierde 0.0% de celdas 3+.

### glm-4.7 (prescindible)
R1: medio=1.81, 3+=15. R2: medio=2.42, 3+=54 (Δ=+0.61). Aportes unicos: 0. Absorcion: 29 (mas de qwen3-235b). Angulos: 8. Inflacion: 0. Valor: 45. Sin el: pierde 0.0% de celdas 3+.

### cogito-671b (valioso)
R1: medio=1.52, 3+=6. R2: medio=2.88, 3+=77 (Δ=+1.35). Aportes unicos: 6. Absorcion: 16 (mas de qwen3-235b). Angulos: 10. Inflacion: 6. Valor: 42. Sin el: pierde 5.4% de celdas 3+.

### kimi-k2.5 (prescindible)
R1: medio=2.06, 3+=28. R2: medio=2.47, 3+=48 (Δ=+0.41). Aportes unicos: 0. Absorcion: 18 (mas de qwen). Angulos: 6. Inflacion: 0. Valor: 30. Sin el: pierde 0.0% de celdas 3+.

### deepseek-r1 (prescindible)
R1: medio=1.57, 3+=12. R2: medio=1.57, 3+=12 (Δ=+0.00). Aportes unicos: 0. Absorcion: 0 (mas de ). Angulos: 0. Inflacion: 0. Valor: 0. Sin el: pierde 0.0% de celdas 3+.

### minimax-m2.5 (prescindible)
R1: medio=1.60, 3+=14. R2: medio=1.79, 3+=17 (Δ=+0.19). Aportes unicos: 0. Absorcion: 0 (mas de ). Angulos: 0. Inflacion: 0. Valor: 0. Sin el: pierde 0.0% de celdas 3+.

### sonnet (prescindible)
R1: medio=2.00, 3+=32. R2: medio=2.00, 3+=32 (Δ=+0.00). Aportes unicos: 0. Absorcion: 0 (mas de ). Angulos: 0. Inflacion: 0. Valor: 0. Sin el: pierde 0.0% de celdas 3+.

### v3.2-reasoner (prescindible)
R1: medio=1.42, 3+=9. R2: medio=1.42, 3+=9 (Δ=+0.00). Aportes unicos: 0. Absorcion: 0 (mas de ). Angulos: 0. Inflacion: 0. Valor: 0. Sin el: pierde 0.0% de celdas 3+.

## Mapa Enriquecido Colectivo

### v31_best

| Celda | Max | N≥2 | N≥3 |
|-------|-----|------|------|
| Salud×Conservar | 3 | 12 | 7 |
| Salud×Captar | 3 | 11 | 4 |
| Salud×Depurar | 3 | 12 | 8 |
| Salud×Distribuir | 3 | 12 | 8 |
| Salud×Frontera | 4 | 11 | 8 |
| Salud×Adaptar | 3 | 12 | 7 |
| Salud×Replicar | 3 | 9 | 5 |
| Sentido×Conservar | 3 | 11 | 7 |
| Sentido×Captar | 3 | 11 | 7 |
| Sentido×Depurar | 4 | 10 | 8 |
| Sentido×Distribuir | 3 | 12 | 8 |
| Sentido×Frontera | 4 | 12 | 10 |
| Sentido×Adaptar | 3 | 12 | 8 |
| Sentido×Replicar | 2 | 8 | 0 |
| Continuidad×Conservar | 3 | 12 | 8 |
| Continuidad×Captar | 3 | 12 | 3 |
| Continuidad×Depurar | 3 | 12 | 8 |
| Continuidad×Distribuir | 3 | 11 | 9 |
| Continuidad×Frontera | 4 | 12 | 8 |
| Continuidad×Adaptar | 4 | 12 | 7 |
| Continuidad×Replicar | 3 | 10 | 8 |

### 70b_worst

| Celda | Max | N≥2 | N≥3 |
|-------|-----|------|------|
| Salud×Conservar | 3 | 11 | 6 |
| Salud×Captar | 2 | 9 | 0 |
| Salud×Depurar | 3 | 11 | 7 |
| Salud×Distribuir | 2 | 10 | 0 |
| Salud×Frontera | 3 | 12 | 8 |
| Salud×Adaptar | 3 | 12 | 5 |
| Salud×Replicar | 3 | 12 | 9 |
| Sentido×Conservar | 3 | 12 | 9 |
| Sentido×Captar | 2 | 10 | 0 |
| Sentido×Depurar | 3 | 8 | 7 |
| Sentido×Distribuir | 2 | 10 | 0 |
| Sentido×Frontera | 3 | 12 | 9 |
| Sentido×Adaptar | 4 | 11 | 5 |
| Sentido×Replicar | 3 | 11 | 8 |
| Continuidad×Conservar | 3 | 11 | 4 |
| Continuidad×Captar | 2 | 8 | 0 |
| Continuidad×Depurar | 3 | 11 | 8 |
| Continuidad×Distribuir | 2 | 9 | 0 |
| Continuidad×Frontera | 3 | 12 | 8 |
| Continuidad×Adaptar | 3 | 12 | 6 |
| Continuidad×Replicar | 3 | 12 | 10 |

### maverick_medium

| Celda | Max | N≥2 | N≥3 |
|-------|-----|------|------|
| Salud×Conservar | 3 | 12 | 1 |
| Salud×Captar | 3 | 11 | 1 |
| Salud×Depurar | 2 | 1 | 0 |
| Salud×Distribuir | 3 | 11 | 1 |
| Salud×Frontera | 3 | 12 | 7 |
| Salud×Adaptar | 3 | 11 | 8 |
| Salud×Replicar | 3 | 9 | 7 |
| Sentido×Conservar | 2 | 7 | 0 |
| Sentido×Captar | 3 | 11 | 6 |
| Sentido×Depurar | 3 | 7 | 6 |
| Sentido×Distribuir | 3 | 8 | 1 |
| Sentido×Frontera | 3 | 10 | 9 |
| Sentido×Adaptar | 4 | 10 | 8 |
| Sentido×Replicar | 2 | 8 | 0 |
| Continuidad×Conservar | 3 | 12 | 1 |
| Continuidad×Captar | 2 | 8 | 0 |
| Continuidad×Depurar | 2 | 9 | 0 |
| Continuidad×Distribuir | 3 | 10 | 1 |
| Continuidad×Frontera | 3 | 12 | 7 |
| Continuidad×Adaptar | 4 | 12 | 12 |
| Continuidad×Replicar | 4 | 11 | 11 |

### gptoss_depurar

| Celda | Max | N≥2 | N≥3 |
|-------|-----|------|------|
| Salud×Conservar | 4 | 12 | 8 |
| Salud×Captar | 3 | 10 | 1 |
| Salud×Depurar | 4 | 12 | 9 |
| Salud×Distribuir | 3 | 10 | 1 |
| Salud×Frontera | 5 | 12 | 9 |
| Salud×Adaptar | 4 | 12 | 7 |
| Salud×Replicar | 3 | 7 | 4 |
| Sentido×Conservar | 3 | 9 | 1 |
| Sentido×Captar | 4 | 10 | 6 |
| Sentido×Depurar | 4 | 10 | 9 |
| Sentido×Distribuir | 3 | 8 | 1 |
| Sentido×Frontera | 5 | 10 | 9 |
| Sentido×Adaptar | 5 | 10 | 7 |
| Sentido×Replicar | 4 | 9 | 6 |
| Continuidad×Conservar | 3 | 12 | 3 |
| Continuidad×Captar | 3 | 11 | 1 |
| Continuidad×Depurar | 4 | 12 | 8 |
| Continuidad×Distribuir | 3 | 7 | 1 |
| Continuidad×Frontera | 4 | 12 | 7 |
| Continuidad×Adaptar | 4 | 12 | 6 |
| Continuidad×Replicar | 5 | 9 | 6 |

### qwen3t_medium

| Celda | Max | N≥2 | N≥3 |
|-------|-----|------|------|
| Salud×Conservar | 4 | 12 | 9 |
| Salud×Captar | 3 | 12 | 1 |
| Salud×Depurar | 4 | 11 | 9 |
| Salud×Distribuir | 3 | 10 | 2 |
| Salud×Frontera | 4 | 12 | 9 |
| Salud×Adaptar | 4 | 12 | 9 |
| Salud×Replicar | 3 | 11 | 10 |
| Sentido×Conservar | 4 | 12 | 9 |
| Sentido×Captar | 4 | 11 | 10 |
| Sentido×Depurar | 4 | 11 | 9 |
| Sentido×Distribuir | 3 | 12 | 6 |
| Sentido×Frontera | 4 | 12 | 10 |
| Sentido×Adaptar | 4 | 12 | 9 |
| Sentido×Replicar | 3 | 11 | 7 |
| Continuidad×Conservar | 4 | 12 | 5 |
| Continuidad×Captar | 3 | 9 | 7 |
| Continuidad×Depurar | 4 | 11 | 7 |
| Continuidad×Distribuir | 4 | 10 | 8 |
| Continuidad×Frontera | 4 | 12 | 11 |
| Continuidad×Adaptar | 4 | 12 | 10 |
| Continuidad×Replicar | 3 | 12 | 10 |

## Curva de Rendimiento

| N modelos | Celdas 3+ | % del total |
|-----------|-----------|-------------|
| 1 | 66 | 71.0% |
| 2 | 88 | 94.6% |
| 3 | 88 | 94.6% |
| 4 | 88 | 94.6% |
| 5 | 88 | 94.6% |
| 6 | 88 | 94.6% |
| 7 | 93 | 100.0% |
| 8 | 93 | 100.0% |
| 9 | 93 | 100.0% |
| 10 | 93 | 100.0% |
| 11 | 93 | 100.0% |
| 12 | 93 | 100.0% |

## Mesa Minima Optima

**2 modelos** capturan >= 90% del valor: gpt-oss-120b, qwen3-235b

## Quien se queda

**Valioso**: cogito-671b, qwen3-235b
**Prescindible**: deepseek-r1, deepseek-v3.1, glm-4.7, gpt-oss-120b, kimi-k2.5, minimax-m2.5, opus, sonnet, v3.2-chat, v3.2-reasoner

## Comparacion Ronda 1 vs Ronda 2

- Celdas 3+ con R1: 77
- Celdas 3+ con R2: 93
- Delta: +16
- Hallazgos emergentes (solo en R2): 16

### Top Hallazgos Emergentes

- v31_best / Salud×Captar: R1 max=2 -> R2 max=3
- v31_best / Continuidad×Captar: R1 max=2 -> R2 max=3
- maverick_medium / Salud×Conservar: R1 max=2 -> R2 max=3
- maverick_medium / Salud×Captar: R1 max=2 -> R2 max=3
- maverick_medium / Salud×Distribuir: R1 max=2 -> R2 max=3
- maverick_medium / Sentido×Distribuir: R1 max=2 -> R2 max=3
- maverick_medium / Continuidad×Conservar: R1 max=2 -> R2 max=3
- maverick_medium / Continuidad×Distribuir: R1 max=2 -> R2 max=3
- gptoss_depurar / Salud×Captar: R1 max=2 -> R2 max=3
- gptoss_depurar / Salud×Distribuir: R1 max=2 -> R2 max=3

## Opus: vale la pena?

Role: prescindible. Aportes unicos: 0. Sin Opus pierde 0.0% de 3+.

## Sonnet como referencia

Role: prescindible. Aportes unicos: 0. Sin Sonnet pierde 0.0% de 3+. Nivel medio R1: 2.00.

---
*Generado por exp4_analyze_enrichment.py*

### EXP 4.1 — Comparación

# EXP 4.1 vs EXP 4 -- Especializado vs Generico

## 1. Delta por Modelo (R1): Generico vs Especializado

| Modelo | Media Gen | Media Esp | Delta Global | Delta Foco | Delta Fuera |
|--------|-----------|-----------|--------------|------------|-------------|
| opus | 1.50 | 1.82 | +0.314 | n/a | n/a |
| v3.2-reasoner | 1.42 | 1.71 | +0.286 | n/a | n/a |
| cogito-671b | 1.52 | 1.80 | +0.276 | +0.667 | -0.017 |
| gpt-oss-120b | 1.26 | 1.52 | +0.267 | +1.133 | -0.080 |
| v3.2-chat | 1.54 | 1.80 | +0.257 | n/a | n/a |
| deepseek-r1 | 1.57 | 1.72 | +0.152 | +0.371 | +0.043 |
| minimax-m2.5 | 1.60 | 1.75 | +0.152 | +0.367 | +0.067 |
| sonnet | 2.00 | 2.00 | +0.000 | n/a | n/a |
| deepseek-v3.1 | 1.66 | 1.63 | -0.029 | +0.467 | -0.227 |
| kimi-k2.5 | 2.06 | 1.99 | -0.067 | +0.467 | -0.156 |
| qwen3-235b | 2.54 | 2.43 | -0.114 | n/a | n/a |
| glm-4.7 | 1.81 | 1.54 | -0.267 | +0.371 | -0.586 |

**Resumen R1:** Delta medio = +0.102. Mejoran: 7. Empeoran: 4. Igual: 1.

## 2. Mapa Colectivo Comparado (Best of R1+R2)

| Metrica | Generico | Especializado | Delta |
|---------|----------|---------------|-------|
| Celdas nivel 3+ | 93 | 95 | +2.000 |
| Celdas totales | 105 | 105 | - |

Celdas que suben: **17**. Celdas que bajan: **12**. Igual: **76**.

### Cambios en mapa colectivo (max por celda)

| Output | Celda | Gen Max | Esp Max | Delta |
|--------|-------|---------|---------|-------|
| v31_best | Sentido×Adaptar | 3 | 4 | +1.000 |
| v31_best | Sentido×Replicar | 2 | 3 | +1.000 |
| 70b_worst | Salud×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Captar | 2 | 3 | +1.000 |
| 70b_worst | Sentido×Depurar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Distribuir | 2 | 3 | +1.000 |
| 70b_worst | Sentido×Frontera | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Captar | 2 | 3 | +1.000 |
| 70b_worst | Continuidad×Distribuir | 2 | 3 | +1.000 |
| 70b_worst | Continuidad×Frontera | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Adaptar | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Replicar | 3 | 4 | +1.000 |
| maverick_medium | Salud×Adaptar | 3 | 4 | +1.000 |
| maverick_medium | Sentido×Frontera | 3 | 4 | +1.000 |
| maverick_medium | Continuidad×Frontera | 3 | 4 | +1.000 |
| qwen3t_medium | Continuidad×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Conservar | 3 | 2 | -1.000 |
| maverick_medium | Sentido×Distribuir | 3 | 2 | -1.000 |
| maverick_medium | Continuidad×Adaptar | 4 | 3 | -1.000 |
| gptoss_depurar | Salud×Adaptar | 4 | 3 | -1.000 |
| gptoss_depurar | Salud×Replicar | 3 | 2 | -1.000 |
| gptoss_depurar | Sentido×Captar | 4 | 3 | -1.000 |
| gptoss_depurar | Sentido×Adaptar | 5 | 4 | -1.000 |
| gptoss_depurar | Sentido×Replicar | 4 | 3 | -1.000 |
| gptoss_depurar | Continuidad×Replicar | 5 | 4 | -1.000 |
| qwen3t_medium | Salud×Conservar | 4 | 3 | -1.000 |
| qwen3t_medium | Sentido×Captar | 4 | 3 | -1.000 |
| qwen3t_medium | Continuidad×Conservar | 4 | 3 | -1.000 |

## 3. Top Mejoras: Celdas que subieron 2+ niveles

No se encontraron celdas con mejora >= 2 niveles.

## 4. Comparacion R2 (Best of R1+R2) por Modelo

| Modelo | Gen Best | Esp Best | Delta |
|--------|----------|----------|-------|
| v3.2-reasoner | 1.42 | 1.91 | +0.495 |
| deepseek-r1 | 1.57 | 2.00 | +0.429 |
| minimax-m2.5 | 1.79 | 2.07 | +0.276 |
| deepseek-v3.1 | 2.80 | 2.99 | +0.190 |
| v3.2-chat | 2.86 | 3.02 | +0.162 |
| cogito-671b | 2.88 | 2.90 | +0.019 |
| sonnet | 2.00 | 2.00 | +0.000 |
| gpt-oss-120b | 2.74 | 2.71 | -0.038 |
| glm-4.7 | 2.42 | 2.15 | -0.267 |
| qwen3-235b | 3.19 | 2.88 | -0.314 |
| opus | 2.77 | 2.37 | -0.400 |
| kimi-k2.5 | 2.47 | 1.99 | -0.476 |

**Mapa enriquecido colectivo (R2):** Celdas 3+ gen=93, esp=95 (+2.000). Suben=17, bajan=12.

## 5. Fichas Actualizadas por Modelo

### opus

- Media generica: 2.771 / Media especializada: 2.371 / Delta: -0.400
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Continuidad×Frontera (delta medio +0.000)
- Top retroceso: Sentido×Depurar (delta medio -1.000)

### v3.2-reasoner

- Media generica: 1.419 / Media especializada: 1.914 / Delta: +0.495
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Sentido×Captar (delta medio +2.000)
- Top retroceso: Continuidad×Replicar (delta medio -0.600)

### cogito-671b

- Media generica: 2.876 / Media especializada: 2.895 / Delta: +0.019
- En foco: gen=3.022, esp=3.111, delta=+0.089
- Fuera foco: gen=2.767, esp=2.733, delta=-0.033
- Top mejora: Sentido×Frontera (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.400)

### gpt-oss-120b

- Media generica: 2.743 / Media especializada: 2.705 / Delta: -0.038
- En foco: gen=2.567, esp=2.567, delta=+0.000
- Fuera foco: gen=2.813, esp=2.760, delta=-0.053
- Top mejora: Sentido×Distribuir (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.600)

### v3.2-chat

- Media generica: 2.857 / Media especializada: 3.019 / Delta: +0.162
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Salud×Depurar (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.200)

### deepseek-r1

- Media generica: 1.571 / Media especializada: 2.000 / Delta: +0.429
- En foco: gen=1.771, esp=2.429, delta=+0.657
- Fuera foco: gen=1.471, esp=1.786, delta=+0.314
- Top mejora: Continuidad×Captar (delta medio +1.000)
- Top retroceso: Salud×Distribuir (delta medio +0.000)

### minimax-m2.5

- Media generica: 1.790 / Media especializada: 2.067 / Delta: +0.277
- En foco: gen=1.400, esp=2.067, delta=+0.667
- Fuera foco: gen=1.947, esp=2.067, delta=+0.120
- Top mejora: Sentido×Depurar (delta medio +1.000)
- Top retroceso: Sentido×Conservar (delta medio -0.400)

### sonnet

- Media generica: 2.000 / Media especializada: 2.000 / Delta: +0.000
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Salud×Conservar (delta medio +0.000)
- Top retroceso: Salud×Conservar (delta medio +0.000)

### deepseek-v3.1

- Media generica: 2.800 / Media especializada: 2.990 / Delta: +0.190
- En foco: gen=3.000, esp=3.167, delta=+0.167
- Fuera foco: gen=2.720, esp=2.920, delta=+0.200
- Top mejora: Salud×Depurar (delta medio +0.600)
- Top retroceso: Salud×Frontera (delta medio -0.200)

### kimi-k2.5

- Media generica: 2.467 / Media especializada: 1.990 / Delta: -0.477
- En foco: gen=2.667, esp=2.800, delta=+0.133
- Fuera foco: gen=2.433, esp=1.856, delta=-0.578
- Top mejora: Salud×Adaptar (delta medio +0.200)
- Top retroceso: Sentido×Depurar (delta medio -1.200)

### qwen3-235b

- Media generica: 3.190 / Media especializada: 2.876 / Delta: -0.314
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Continuidad×Adaptar (delta medio +0.200)
- Top retroceso: Salud×Captar (delta medio -0.600)

### glm-4.7

- Media generica: 2.419 / Media especializada: 2.152 / Delta: -0.267
- En foco: gen=2.371, esp=2.257, delta=-0.114
- Fuera foco: gen=2.443, esp=2.100, delta=-0.343
- Top mejora: Sentido×Depurar (delta medio +0.200)
- Top retroceso: Salud×Frontera (delta medio -0.800)

## 6. Veredicto: Vale la especializacion?

**SI, la especializacion vale**

Delta medio positivo (+0.102) y 7/12 modelos mejoran. La especializacion produce evaluaciones mas profundas.

Datos clave:
- Delta medio R1: +0.102
- Modelos que mejoran (R1): 7/12
- Mapa colectivo 3+: gen=93, esp=95 (delta=+2.000)
- Delta medio en foco (modelos con foco): +0.549
- Delta medio fuera foco (modelos con foco): -0.137

## 7. Protocolo Recomendado

1. **Usar prompts especializados** para todos los modelos con foco definido
2. Para modelos sin foco (v3.2-chat, qwen3-235b, opus): mantener prompt generico o cross-celda
3. R2 de enriquecimiento sigue siendo necesaria para consolidar

## 8. Mesa Minima Actualizada (con datos especializados)

**2 modelos** capturan >= 90% del valor: v3.2-chat, deepseek-v3.1

Celdas 3+: 93/95 (97.9% del total con 2 modelos)

### Curva de cobertura

| N modelos | Modelos | Celdas 3+ | % del total |
|-----------|---------|-----------|-------------|
| 1 | v3.2-chat | 85 | 89.5% |
| 2 | v3.2-chat, deepseek-v3.1 | 93 | 97.9% |
| 3 | v3.2-chat, deepseek-v3.1, deepseek-r1 | 95 | 100.0% |
| 4 | v3.2-chat, deepseek-v3.1, deepseek-r1, cogito-671b | 95 | 100.0% |
| 5 | v3.2-chat, deepseek-v3.1, deepseek-r1, cogito-671b, glm-4.7 | 95 | 100.0% |

---
*Generado por exp4_1_analyze_comparison.py*

### EXP 4.2 — Sintetizador

# Exp 4.2 — El Sintetizador: Informe de Analisis

## Resumen

- **Sintetizadores evaluados:** 6 (4 exitosos, 2 fallidos)
- **Outputs por sintetizador:** 5
- **Celdas por output:** 21 (3 lentes x 7 funciones)
- **Evaluadores en mesa redonda:** 12

### Sintetizadores fallidos

- **glm-5**: todos los outputs fallaron (parse error)
- **minimax-m2.5**: todos los outputs fallaron (parse error)

---

## A) Max Mecanico Baseline

Para cada output, se calcula `max(13 evaluadores)` por celda usando la mejor evaluacion disponible (R2 si no tiene error, sino R1).

- **v31_best**: suma=67, media=3.19, celdas>=3: 20, celdas>=4: 5
- **70b_worst**: suma=58, media=2.76, celdas>=3: 15, celdas>=4: 1
- **maverick_medium**: suma=61, media=2.90, celdas>=3: 16, celdas>=4: 3
- **gptoss_depurar**: suma=80, media=3.81, celdas>=3: 21, celdas>=4: 13
- **qwen3t_medium**: suma=77, media=3.67, celdas>=3: 21, celdas>=4: 14

---

## B) Metricas por Sintetizador

### cogito-671b

| Metrica | Valor |
|---|---|
| Outputs exitosos | 5 / 5 |
| Evaluadores citados (media) | 9.4 |
| Genuinidad de integracion | 100.0% |
| Celdas que suben vs max mec | 0 (same: 105, down: 0) |
| Conexiones (media) | 3.6 |
| Cross-lente (media) | 3.6 |
| Hallazgo central (len media) | 357.4 chars |
| Hallazgos no-genericos | 5 / 5 |
| Puntos ciegos residuales (media) | 2.6 |
| Meta-patrones (media) | 3.0 |
| Tiempo medio (s) | 47.3 |

### deepseek-r1

| Metrica | Valor |
|---|---|
| Outputs exitosos | 5 / 5 |
| Evaluadores citados (media) | 10.6 |
| Genuinidad de integracion | 100.0% |
| Celdas que suben vs max mec | 0 (same: 105, down: 0) |
| Conexiones (media) | 3.0 |
| Cross-lente (media) | 3.0 |
| Hallazgo central (len media) | 326.6 chars |
| Hallazgos no-genericos | 5 / 5 |
| Puntos ciegos residuales (media) | 2.0 |
| Meta-patrones (media) | 2.6 |
| Tiempo medio (s) | 54.7 |

### qwen3-235b

| Metrica | Valor |
|---|---|
| Outputs exitosos | 5 / 5 |
| Evaluadores citados (media) | 11.6 |
| Genuinidad de integracion | 100.0% |
| Celdas que suben vs max mec | 0 (same: 105, down: 0) |
| Conexiones (media) | 2.2 |
| Cross-lente (media) | 2.2 |
| Hallazgo central (len media) | 190.8 chars |
| Hallazgos no-genericos | 3 / 5 |
| Puntos ciegos residuales (media) | 1.2 |
| Meta-patrones (media) | 2.0 |
| Tiempo medio (s) | 136.8 |

### v3.2-chat

| Metrica | Valor |
|---|---|
| Outputs exitosos | 5 / 5 |
| Evaluadores citados (media) | 12.0 |
| Genuinidad de integracion | 100.0% |
| Celdas que suben vs max mec | 0 (same: 105, down: 0) |
| Conexiones (media) | 2.0 |
| Cross-lente (media) | 2.0 |
| Hallazgo central (len media) | 160.4 chars |
| Hallazgos no-genericos | 2 / 5 |
| Puntos ciegos residuales (media) | 1.2 |
| Meta-patrones (media) | 1.4 |
| Tiempo medio (s) | 120.5 |

---

## C) Tabla Comparativa

| Sintetizador | Outputs OK | Eval citados | Genuinidad%% | Celdas up | Conexiones | Cross-lente | Hallazgo (len) | Puntos ciegos | Meta-patrones | Tiempo (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| cogito-671b | 5 | 9.4 | 100.0% | 0 | 3.6 | 3.6 | 357.4 | 2.6 | 3.0 | 47.3 |
| deepseek-r1 | 5 | 10.6 | 100.0% | 0 | 3.0 | 3.0 | 326.6 | 2.0 | 2.6 | 54.7 |
| glm-5 | 0 (FAILED) | - | - | - | - | - | - | - | - | - |
| minimax-m2.5 | 0 (FAILED) | - | - | - | - | - | - | - | - | - |
| qwen3-235b | 5 | 11.6 | 100.0% | 0 | 2.2 | 2.2 | 190.8 | 1.2 | 2.0 | 136.8 |
| v3.2-chat | 5 | 12.0 | 100.0% | 0 | 2.0 | 2.0 | 160.4 | 1.2 | 1.4 | 120.5 |

---

## D) Mejor Sintetizador vs Max Mecanico

**Mejor sintetizador:** cogito-671b

| Metrica | Sintetizador | Max Mecanico |
|---|---|---|
| Celdas al mismo nivel | 105 | (referencia) |
| Celdas por encima | 0 | 0 |
| Celdas por debajo | 0 | 0 |
| Conexiones totales | 18 | 0 |
| Hallazgo central | Si | No |

### Detalle por output

- **v31_best**: same=21, higher=0, lower=0, conexiones=4
- **70b_worst**: same=21, higher=0, lower=0, conexiones=3
- **maverick_medium**: same=21, higher=0, lower=0, conexiones=4
- **gptoss_depurar**: same=21, higher=0, lower=0, conexiones=3
- **qwen3t_medium**: same=21, higher=0, lower=0, conexiones=4

---

## E) Top 5 Conexiones Cross-Lente

### 1. Salud×Depurar <-> Continuidad×Depurar
- **Tipo:** cross-lente **(CROSS-LENTE)**
- **Sintetizador:** v3.2-chat (output: gptoss_depurar)
- **Conexion:** La depuración de costes variables ocultos (6.000€/mes) conecta directamente con la inviabilidad de la expansión a 5 sillones. Lo que en Salud se ve como 'sobrecarga financiera que impacta indirectamente en la salud', en Continuidad se traduce en 'opción no rentable que amenaza la viabilidad del negocio'. La misma evidencia numérica sirve para ambos diagnósticos.
- **Evaluadores origen:** opus, v3.2-chat, cogito-671b, qwen3-235b

### 2. Salud×Frontera <-> Sentido×Frontera
- **Tipo:** cross-lente **(CROSS-LENTE)**
- **Sintetizador:** v3.2-chat (output: gptoss_depurar)
- **Conexion:** Ambas celdas identifican la oposición fundamental entre 'máxima facturación' y 'máxima salud', pero desde perspectivas complementarias: Salud×Frontera enfatiza el riesgo humano y límites físicos, mientras Sentido×Frontera abstrae el patrón cognitivo que genera esta contradicción. Juntas revelan que la frontera no es solo técnica, sino ética y epistemológica.
- **Evaluadores origen:** opus, v3.2-chat, cogito-671b, qwen3-235b

### 3. Salud×Replicar <-> Continuidad×Replicar
- **Tipo:** cross-lente **(CROSS-LENTE)**
- **Sintetizador:** v3.2-chat (output: v31_best)
- **Conexion:** El patrón identificado de startup con product-market fit parcial pero problemas operativos (Salud×Replicar) se proyecta en la continuidad como modelo insostenible que requiere cambios estructurales para replicar el éxito de clientes grandes (Continuidad×Replicar), mostrando cómo el diagnóstico del presente informa las opciones futuras.
- **Evaluadores origen:** v3.2-chat, deepseek-v3.1, cogito-671b, qwen3-235b

### 4. Salud×Frontera <-> Sentido×Depurar
- **Tipo:** cross-lente **(CROSS-LENTE)**
- **Sintetizador:** v3.2-chat (output: v31_best)
- **Conexion:** La contradicción formal (estabilización requiere tiempo que el runway no permite, pivot requiere recursos que la estabilización demanda) no es solo un límite operativo (Salud×Frontera) sino que redefine la pregunta estratégica como dilema estructural que necesita depuración de supuestos y mediación externa (Sentido×Depurar).
- **Evaluadores origen:** opus, v3.2-chat, deepseek-v3.1, cogito-671b

### 5. Sentido×Frontera <-> Continuidad×Frontera
- **Tipo:** cross-lente **(CROSS-LENTE)**
- **Sintetizador:** qwen3-235b (output: qwen3t_medium)
- **Conexion:** El miedo a la irrelevancia (Sentido×Frontera) no nombrado como límite identitario bloquea la toma de decisiones auténticas, lo que impide anticipar o prepararse para el trigger crítico de cancelación de cliente (Continuidad×Frontera). La frontera emocional paraliza la acción estructural necesaria para evitar el colapso.
- **Evaluadores origen:** opus, v3.2-chat, cogito-671b, qwen3-235b

---

## F) Hallazgos Centrales — Comparacion

### Output: v31_best

**cogito-671b** (356 chars):
> La startup enfrenta una contradicción estructural insalvable: la estabilización requiere tiempo que el runway no permite, y el pivot requiere recursos que la estabilización demanda, agravada por una relación CEO-CTO rota que impide resolver el dilema, mientras el tiempo y efectivo se agotan en un contexto de alta rotación y sobrecarga del equipo técnico.

**deepseek-r1** (351 chars):
> La contradicción tiempo-recursos es una trampa estructural que trasciende el trade-off operativo: exige una intervención triple simultánea (reducción inmediata de burn rate, mediación externa del conflicto CEO-CTO, y enfoque quirúrgico en bugs que impactan churn) para crear el espacio temporal y relacional necesario para evitar el colapso inminente.

**v3.2-chat** (406 chars):
> La startup enfrenta una trampa estructural donde el tiempo necesario para estabilizar el producto excede el runway disponible, mientras que los recursos requeridos para pivotar a enterprise son los mismos que la estabilización demanda, creando un dilema irresoluble sin mediación externa o cambio fundamental de variables, agravado por una ruptura en la relación CEO-CTO que paraliza la toma de decisiones.

### Output: 70b_worst

**cogito-671b** (299 chars):
> La paradoja de una lealtad invisible que, al intentar preservar tanto el éxito profesional como los lazos familiares, perpetúa un patrón transgeneracional de sacrificio personal que amenaza con destruir exactamente lo que busca conservar: la salud, el sentido de identidad y la continuidad familiar.

**deepseek-r1** (280 chars):
> La lealtad invisible al rol de proveedor encierra un circuito transgeneracional donde el miedo a repetir el destino paterno paradójicamente reproduce las condiciones que amenazan la salud y los vínculos, requiriendo una ruptura simultánea de estructuras operativas e identitarias.

**qwen3-235b** (329 chars):
> El miedo no nombrado a repetir el destino del padre —un infarto por estrés laboral— actúa como un motor oculto que perpetúa un ciclo transgeneracional de sacrificio, donde el éxito profesional se paga con la salud y la familia, y solo puede romperse mediante una adaptación identitaria profunda que redefina el sentido del deber.

### Output: maverick_medium

**cogito-671b** (449 chars):
> La propuesta transforma un cambio de carrera potencialmente disruptivo en un proceso de 'prototipado reversible' que equilibra la búsqueda de sentido profesional con la preservación de la estabilidad familiar, mediante un marco iterativo de bajo riesgo que valida hipótesis antes de compromisos irreversibles, redefiniendo la transición profesional no como un salto binario sino como una adaptación escalonada con mecanismos de seguridad integrados.

**deepseek-r1** (288 chars):
> La propuesta transforma el cambio de carrera de un salto binario a un proceso de 'validación existencial escalonada', donde la preservación financiera (Salud) y los límites temporales (Continuidad) crean un corredor seguro para probar el sentido (Sentido) mediante prototipos reversibles.

**qwen3-235b** (294 chars):
> El output transforma un dilema existencial de alto riesgo en un proceso de validación incremental y reversible, donde la preservación del sistema familiar no limita el cambio, sino que lo posibilita mediante fronteras claras, iteraciones controladas y un patrón replicable de transición segura.

### Output: gptoss_depurar

**cogito-671b** (343 chars):
> La contradicción entre el deseo de expansión lineal y los límites humanos/financieros revela que la verdadera innovación no está en crecer, sino en redefinir el crecimiento como equilibrio entre salud y sostenibilidad económica, donde la restricción (4 sillones, vacaciones obligatorias) genera un modelo más viable que la expansión ilimitada.

**deepseek-r1** (299 chars):
> La contradicción fundamental entre salud y expansión financiera se resuelve mediante un reequilibrio sistémico donde el límite humano (60h/semana) y el patrón cognitivo (confianza en ingresos lineales) convergen en S′=4 como síntesis viable, transformando el crecimiento en sostenibilidad replicable

**v3.2-chat** (396 chars):
> La mesa vio colectivamente que el caso no es un problema de optimización financiera, sino la manifestación concreta de un patrón sistémico donde la contradicción entre salud humana y lógica de crecimiento se materializa en discrepancias numéricas, límites físicos ignorados y una propuesta de expansión que, al ser analizada, revela ser formalmente inconsistente con la supervivencia del sistema.

### Output: qwen3t_medium

**cogito-671b** (340 chars):
> La startup enfrenta un colapso inminente donde la preservación de identidades individuales (CTO como 'guardián', CEO como 'salvador') ha creado un sistema que prioriza la supervivencia emocional sobre la viabilidad estructural, acelerando su propia destrucción mediante patrones de adaptación que exacerban las crisis que intentan resolver.

**deepseek-r1** (415 chars):
> La startup opera en un punto de no retorno estructural donde la conservación de identidades defensivas (CTO como 'guardián', CEO como 'salvador') acelera el colapso al bloquear la depuración de emociones no nombradas (vergüenza/miedo) y deudas técnicas/humanas críticas, haciendo que las adaptaciones propuestas (pivot) sean suicidio estructural ante fronteras objetivas insalvables (runway 7 meses, SLA imposible).

**qwen3-235b** (331 chars):
> La startup no está fallando por falta de estrategia o tecnología, sino por un conflicto sistémico entre supervivencia emocional y continuidad estructural: ambos líderes priorizan su identidad sobre la realidad, lo que bloquea cualquier acción efectiva, y convierte sus respuestas reactivas en mecanismos de aceleración del colapso.

---

## G) Veredicto

### Mejor sintetizador

**cogito-671b**

cogito-671b destaca por genuinidad 100.0%, 3.6 conexiones/output, 3.0 meta-patrones/output, 0 celdas por encima del max mecanico

### Ranking

1. **cogito-671b** — score: 170.0
1. **deepseek-r1** — score: 160.8
1. **qwen3-235b** — score: 148.0
1. **v3.2-chat** — score: 141.2

### Vale la pena la sintesis vs max mecanico?

**SI**

genera 18 conexiones entre celdas (max mecanico: 0); produce hallazgos centrales no triviales; 100.0% de celdas igualan o superan max mecanico

El mejor sintetizador iguala o supera el max mecanico en **100.0%** de las celdas.

### Protocolo recomendado

1. Recoger evaluaciones R1+R2 de la mesa redonda (12 evaluadores). 2. Pasar todas las evaluaciones al sintetizador (cogito-671b). 3. El sintetizador produce: evaluacion integrada 21 celdas + conexiones + hallazgo central + puntos ciegos + meta-patrones. 4. Coste adicional: 1 llamada LLM (~47.3s). 5. Valor: conexiones entre lentes, hallazgo central, meta-patrones — informacion que max mecanico NO produce.


### EXP 4.3 — Mente Distribuida

# EXP 4.3 — MENTE DISTRIBUIDA (Analisis)

## A) Convergencia por Output

| Output | Estado | Rondas | Cambios por ronda | Ratio medio | Decay exp? |
|--------|--------|--------|-------------------|-------------|------------|
| v31_best | convergido | 4 | [12, 7, 10, 0] | 0.671 | No |
| 70b_worst | max_rondas | 5 | [11, 13, 6, 7, 10] | 1.060 | No |
| maverick_medium | max_rondas | 5 | [16, 12, 10, 5, 3] | 0.671 | Si |
| gptoss_depurar | convergido | 5 | [16, 9, 5, 5, 2] | 0.630 | No |
| qwen3t_medium | convergido | 4 | [11, 9, 9, 0] | 0.606 | No |

### Curvas de cambios

**v31_best** (max=12):
```
  R0: ######################################## 12
  R1: ####################### 7
  R2: ################################# 10
  R3:  0
```

**70b_worst** (max=13):
```
  R0: ################################## 11
  R1: ######################################## 13
  R2: ################## 6
  R3: ###################### 7
  R4: ############################### 10
```

**maverick_medium** (max=16):
```
  R0: ######################################## 16
  R1: ############################## 12
  R2: ######################### 10
  R3: ############ 5
  R4: ######## 3
```

**gptoss_depurar** (max=16):
```
  R0: ######################################## 16
  R1: ###################### 9
  R2: ############ 5
  R3: ############ 5
  R4: ##### 2
```

**qwen3t_medium** (max=11):
```
  R0: ######################################## 11
  R1: ################################# 9
  R2: ################################# 9
  R3:  0
```

## B) Perfil de Cada Modelo

| Modelo | Contribuciones | Conexiones | P.Ciegos | Rondas activas | Perfiles |
|--------|---------------|------------|----------|----------------|----------|
| gpt-oss-120b | 119 | 77 | 46 | 22 | Sembrador, Conector, Detector de huecos |
| minimax-m2.5 | 75 | 55 | 45 | 22 | Sembrador, Conector, Detector de huecos |
| qwen3-235b | 63 | 48 | 25 | 22 | Sembrador, Conector, Detector de huecos |
| v3.2-chat | 56 | 52 | 28 | 23 | Sembrador, Conector, Detector de huecos |
| deepseek-v3.1 | 52 | 45 | 22 | 18 | Sembrador, Conector, Detector de huecos |
| deepseek-r1 | 44 | 30 | 12 | 16 | Sembrador, Conector |
| v3.2-reasoner | 42 | 28 | 14 | 18 | Sembrador, Conector, Detector de huecos |
| opus | 33 | 34 | 8 | 15 | Sembrador, Conector |
| cogito-671b | 31 | 29 | 22 | 20 | Sembrador, Conector, Detector de huecos |
| kimi-k2.5 | 25 | 19 | 15 | 11 | Sembrador, Conector, Detector de huecos |
| glm-4.7 | 20 | 8 | 2 | 5 | Sembrador |

### Contribuciones por ronda (agregadas)

- **gpt-oss-120b**: [32, 29, 29, 15, 14]
- **minimax-m2.5**: [20, 14, 13, 15, 13]
- **qwen3-235b**: [22, 16, 10, 9, 6]
- **v3.2-chat**: [18, 13, 11, 9, 5]
- **deepseek-v3.1**: [25, 7, 15, 2, 3]
- **deepseek-r1**: [20, 8, 8, 5, 3]
- **v3.2-reasoner**: [18, 12, 7, 4, 1]
- **opus**: [13, 6, 6, 5, 3]
- **cogito-671b**: [13, 7, 6, 3, 2]
- **kimi-k2.5**: [11, 10, 3, 1]
- **glm-4.7**: [17, 3]

## C) Comparacion: Mente Distribuida vs Mesa Redonda vs Max Mecanico

### v31_best

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 18 | 20 | 21 |
| Nivel medio | 3.10 | 3.19 | 4.00 |
| Conexiones | 0 | 0 | 77 |
| Puntos ciegos detectados | 0 | 0 | 40 |

### 70b_worst

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 15 | 15 | 21 |
| Nivel medio | 2.76 | 2.76 | 4.00 |
| Conexiones | 0 | 0 | 99 |
| Puntos ciegos detectados | 0 | 0 | 59 |

### maverick_medium

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 10 | 16 | 21 |
| Nivel medio | 2.52 | 2.90 | 4.00 |
| Conexiones | 0 | 0 | 85 |
| Puntos ciegos detectados | 0 | 0 | 62 |

### gptoss_depurar

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 15 | 21 | 21 |
| Nivel medio | 2.90 | 3.81 | 3.95 |
| Conexiones | 0 | 0 | 86 |
| Puntos ciegos detectados | 0 | 0 | 44 |

### qwen3t_medium

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 19 | 21 | 21 |
| Nivel medio | 3.14 | 3.67 | 4.00 |
| Conexiones | 0 | 0 | 78 |
| Puntos ciegos detectados | 0 | 0 | 34 |

### Agregado (todos los outputs)

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas total | 105 | 105 | 105 |
| Celdas 3+ total | 77 | 93 | 105 |
| Nivel medio promedio | 2.886 | 3.267 | 3.990 |
| Conexiones total | 0 | 0 | 425 |
| Puntos ciegos total | 0 | 0 | 239 |

## D) Top 5 Contribuciones Mas Valiosas

**1. v31_best / Sentido×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Contradicción central: elección forzada entre calidad inmediata y crecimiento futuro

**2. v31_best / Continuidad×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: La contradicción formal es que la estabilización requiere tiempo que el runway no permite

**3. gptoss_depurar / Salud×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Solo al equilibrar salud y finanzas la expansión se vuelve lógica

**4. qwen3t_medium / Sentido×Adaptar** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Patrón 'miedo + acción reactiva' redefine el conflicto: no es estratégico sino supervivencia emocional

**5. v31_best / Salud×Depurar** (salto: 0 -> 3, +3)
- Modelo: sonnet (ronda -1)
- Evidencia: 47 bugs abiertos afectan calidad y churn

## E) Top 5 Conexiones Mas Interesantes

**1. Salud×Depurar <-> Continuidad×Distribuir** (cross-lente: Salud <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: Los 47 bugs no solo afectan churn actual (8%) sino que aceleran la caída proyectada del MRR a €7,200 - cada bug sin resolver aumenta la velocidad de deterioro

**2. Sentido×Frontera <-> Continuidad×Frontera** (cross-lente: Sentido <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: La contradicción entre calidad/crecimiento se amplifica por la restricción temporal - no es solo elegir, sino que el tiempo hace ambas opciones progresivamente menos viables

**3. Salud×Replicar <-> Continuidad×Depurar** (cross-lente: Salud <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: La salida del co-fundador técnico hace 6 meses precedió la fuga de 2 devs - patrón de deterioro en cascada del equipo técnico

**4. Continuidad×Conservar <-> Sentido×Frontera** (cross-lente: Continuidad <-> Sentido)
- Modelo: v3.2-chat (ronda 0, output: v31_best)
- Conexion: El runway de 7 meses (Conservar) es la restricción dura que fuerza la contradicción central (Frontera): no hay tiempo suficiente para hacer ambas cosas (estabilizar y pivotar) antes de que se acabe el

**5. Salud×Conservar <-> Continuidad×Captar** (cross-lente: Salud <-> Continuidad)
- Modelo: v3.2-chat (ronda 0, output: v31_best)
- Conexion: El MRR de €12k (Conservar) es insuficiente para cubrir el burn rate de €28k (Captar), creando la pérdida neta que drena el efectivo y define el runway.

## F) Historia de la Celda Mas Disputada

**Output**: 70b_worst
**Celda**: Salud×Depurar
**Nivel final**: 4
**Historial de niveles**: [0, 1, 2, 3, 4]
**Semilla**: sonnet

### Transiciones

- Nivel 0 -> 1 por **sonnet** (ronda -1)
  > patrón de trabajo excesivo
- Nivel 1 -> 2 por **v3.2-chat** (ronda 0)
  > El patrón de trabajo excesivo es identificado como 'una respuesta aprendida que ya no sirve' - esto es una depuración específica de un patrón disfunci
- Nivel 2 -> 3 por **gpt-oss-120b** (ronda 0)
  > El patrón de trabajo excesivo está impulsado por el miedo heredado a un infarto y la presión de ser el principal proveedor.
- Nivel 3 -> 4 por **qwen3-235b** (ronda 0)
  > el agotamiento y estrés son síntomas que deben depurarse al reconocer que el modelo de trabajo actual es insostenible

### Todas las evidencias

- [sonnet, ronda -1] patrón de trabajo excesivo
- [v3.2-chat, ronda 0] El patrón de trabajo excesivo es identificado como 'una respuesta aprendida que ya no sirve' - esto es una depuración específica de un patrón disfunci
- [gpt-oss-120b, ronda 0] El patrón de trabajo excesivo está impulsado por el miedo heredado a un infarto y la presión de ser el principal proveedor.
- [qwen3-235b, ronda 0] el agotamiento y estrés son síntomas que deben depurarse al reconocer que el modelo de trabajo actual es insostenible
- [deepseek-v3.1, ronda 0] El patrón emocional de dedicación laboral excesiva es una respuesta aprendida que ya no sirve
- [deepseek-r1, ronda 0] patrón de trabajo excesivo es respuesta aprendida y obsoleta que daña salud
- [gpt-oss-120b, ronda 4] Se identifican marcadores fisiológicos tempranos (variabilidad de la frecuencia cardíaca reducida, cortisol diurno elevado, alteraciones del sueño) qu

## G) Mente Minima Recomendada

| N modelos | Modelos | Celdas cubiertas | % del total |
|-----------|---------|-----------------|-------------|
| 3 | gpt-oss-120b, minimax-m2.5, qwen3-235b | 42/105 | 40.0% |
| 5 | gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1 | 70/105 | 66.7% |
| 7 | gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1, deepseek-r1, v3.2-reasoner | 80/105 | 76.2% |

**Recomendacion**: 7 modelos capturan 76.2% del resultado: gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1, deepseek-r1, v3.2-reasoner

## H) Veredicto: Produce la Mente Distribuida Resultado Cualitativamente Diferente?

### Datos cuantitativos

- Celdas 3+ vs Max Mecanico: +28
- Celdas 3+ vs Mesa Redonda: +12
- Nivel medio vs Max Mecanico: +1.104
- Nivel medio vs Mesa Redonda: +0.723
- Conexiones detectadas (exclusivo de Mente Distribuida): 425
- Puntos ciegos detectados (exclusivo de Mente Distribuida): 239

### Veredicto

**SI, cualitativamente diferente.** La Mente Distribuida supera tanto en metricas cuantitativas (nivel medio, celdas 3+) como en dimensiones que los otros enfoques no capturan: 425 conexiones entre celdas y 239 puntos ciegos detectados. Los modelos exhiben 3 perfiles diferenciados (Conector, Detector de huecos, Sembrador), lo que sugiere especializacion emergente.

### Convergencia

3/5 outputs convergieron (media 4.6 rondas). La convergencia no esta garantizada.

---
*Generado por exp4_3_analyze_mind.py*

### EXP 5 — Cadena de Montaje

# EXP 5 — CADENA DE MONTAJE (Analisis)

Fecha: 2026-03-10
Total runs: 40

## A) Tabla Principal: Config x Task

| Config | Nombre | T1 | T2 | T3 | T4 | T5 | **Media** | Coste | Tiempo |
|--------|--------|------|------|------|------|------|--------|-------|--------|
| A | Linea Industrial | 0/1 | **17/18** | **21/21** | 0/2 | 5/6 | **56%** | $0.327 | 2632s |
| B | Coder Puro | 0/1 | **14/15** | **10/11** | 0/2 | 0/0 | **37%** | $0.136 | 1771s |
| C | Maxima Diversidad | 25/30 | 0/0 | 0/0 | 0/2 | 0/2 | **17%** | $0.249 | 2468s |
| D | Ultra-Barato | 0/1 | 4/5 | **9/10** | 0/2 | 6/7 | **51%** | $0.047 | 944s |
| E | Premium | 0/1 | 3/4 | 0/2 | 0/2 | 0/2 | **15%** | $0.343 | 2732s |
| F | Cadena Minima | 0/1 | 0/1 | 8/9 | 0/2 | 0/2 | **18%** | $0.119 | 943s |
| G | Razonadores | 0/1 | 0/0 | **9/10** | 0/2 | 3/4 | **33%** | $0.191 | 2265s |
| 0 | Baseline | 0/1 | 0/1 | 5/6 | 0/2 | 3/4 | **32%** | $0.033 | 262s |

## B) Baseline vs Mejor Cadena

| Task | Baseline (0) | Mejor Cadena | Config | Delta |
|------|-------------|-------------|--------|-------|
| T1 | 0% | 83% | C | +83% |
| T2 | 0% | 94% | A | +94% |
| T3 | 83% | 100% | A | +17% |
| T4 | 0% | 0% | A | 0% |
| T5 | 75% | 86% | D | +11% |

**Baseline medio: 32% | Mejor cadena medio: 73% | Delta: +41%**

## C) Cuantas Estaciones Necesitas?

| Grupo | Pass Rate Medio | Coste Medio | Tiempo Medio |
|-------|----------------|-------------|--------------|
| 7 estaciones (A,C,E,G) | 30% | $0.0554 | 505s |
| 5 estaciones (B,D) | 44% | $0.0183 | 272s |
| 3 estaciones (F) | 18% | $0.0238 | 189s |
| 1 estacion (0) | 32% | $0.0066 | 52s |

## D) Impacto del Debugger (E4)

| Config | Task | Tests Pre-Debug | Tests Post-Debug R1 | Post-Debug R2 | Delta |
|--------|------|----------------|--------------------|--------------:|-------|
| A | T3 | 21/21 | — | — | +0% |
| A | T1 | 0/1 | 0/1 | 0/1 | +0% |
| A | T2 | 17/18 | 17/18 | 17/18 | -0% |
| A | T4 | 0/2 | 0/2 | 0/2 | +0% |
| A | T5 | 14/15 | 0/2 | 13/14 | -10% |
| B | T1 | 0/1 | 0/1 | — | +0% |
| B | T2 | 17/18 | 17/18 | — | -1% |
| B | T3 | 9/10 | 10/11 | — | +1% |
| B | T4 | 0/2 | — | — | +0% |
| C | T1 | 0/1 | 0/1 | 21/30 | +83% |
| C | T4 | 0/2 | 0/2 | 0/2 | +0% |
| C | T5 | 0/2 | 0/2 | 0/2 | +0% |
| D | T1 | 0/1 | 0/1 | — | +0% |
| D | T2 | 4/5 | 4/5 | — | +0% |
| D | T3 | 11/12 | 10/11 | — | -2% |
| D | T4 | 0/2 | 0/2 | — | +0% |
| D | T5 | 7/8 | 7/8 | — | -2% |
| E | T1 | 0/1 | 0/1 | 0/1 | +0% |
| E | T2 | 3/4 | 7/8 | 7/8 | +0% |
| E | T3 | 17/18 | 0/2 | 0/2 | -94% |
| E | T4 | 0/2 | 0/2 | 0/2 | +0% |
| E | T5 | 0/2 | 0/2 | 0/2 | +0% |
| F | T1 | 15/18 | 15/18 | — | -83% |
| F | T2 | 2/3 | 2/3 | — | -67% |
| F | T3 | 8/9 | 8/9 | — | +0% |
| F | T4 | 0/2 | 0/2 | — | +0% |
| F | T5 | 3/4 | 6/7 | — | -75% |
| G | T1 | 0/1 | 0/1 | 0/1 | +0% |
| G | T3 | 5/6 | 5/6 | 5/6 | +7% |
| G | T4 | 0/2 | 0/2 | 0/2 | +0% |
| G | T5 | 1/2 | 3/4 | 3/4 | +25% |

**Debugger mejoro en 5/35 casos. Media de mejora: +23%**

## E) Pareto Coste/Calidad

| Config | Nombre | Pass Rate | Coste Total | Coste/Task | Ratio Calidad/Coste |
|--------|--------|-----------|-------------|------------|---------------------|
| D | Ultra-Barato | 51% | $0.0470 | $0.0094 | 54 |
| 0 | Baseline | 32% | $0.0331 | $0.0066 | 48 |
| B | Coder Puro | 37% | $0.1364 | $0.0273 | 13 |
| G | Razonadores | 33% | $0.1908 | $0.0382 | 9 |
| A | Linea Industrial | 56% | $0.3267 | $0.0653 | 9 |
| F | Cadena Minima | 18% | $0.1192 | $0.0238 | 7 |
| C | Maxima Diversidad | 17% | $0.2488 | $0.0498 | 3 |
| E | Premium | 15% | $0.3425 | $0.0685 | 2 |

## F) Analisis de Fallos

### Fallos por Tarea

**T1** (Edge Function TS): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=0%)
  - Config B: implementation (pass_rate=0%)
  - Config C: implementation (pass_rate=83%)
  - Config D: implementation (pass_rate=0%)
  - Config E: reviewer (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: reviewer (pass_rate=0%)

**T2** (Migration SQL): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=94%)
  - Config B: implementation (pass_rate=93%)
  - Config C: architect (pass_rate=0%)
  - Config D: implementation (pass_rate=80%)
  - Config E: implementation (pass_rate=75%)
  - Config F: implementation (pass_rate=0%)
  - Config G: architect (pass_rate=0%)

**T3** (Analysis Script): 7/8 configs con fallos
  - Config 0: implementation (pass_rate=83%)
  - Config B: reviewer (pass_rate=91%)
  - Config C: tester (pass_rate=0%)
  - Config D: implementation (pass_rate=90%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=89%)
  - Config G: reviewer (pass_rate=90%)

**T4** (Orchestrator): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=0%)
  - Config B: debugger1 (pass_rate=0%)
  - Config C: implementation (pass_rate=0%)
  - Config D: implementation (pass_rate=0%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: reviewer (pass_rate=0%)

**T5** (Assembly Line): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=75%)
  - Config A: optimizer (pass_rate=83%)
  - Config B: tester (pass_rate=0%)
  - Config C: implementation (pass_rate=0%)
  - Config D: implementation (pass_rate=86%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: implementation (pass_rate=75%)

### Dificultad Real por Tarea

| Task | Nombre | Configs con 100% | Configs con >0% | Configs con 0% |
|------|--------|-----------------|----------------|----------------|
| T1 | Edge Function TS | 0 | 1 | 7 |
| T2 | Migration SQL | 0 | 4 | 4 |
| T3 | Analysis Script | 1 | 5 | 2 |
| T4 | Orchestrator | 0 | 0 | 8 |
| T5 | Assembly Line | 0 | 4 | 4 |

## G) VEREDICTO: Puede Reemplazar a Code?

### Datos Clave

- **Mejor cadena**: Config A (Linea Industrial) con 56% pass rate medio
- **Baseline (modelo solo)**: 32% pass rate medio
- **Delta cadena vs baseline**: +24%
- **Config D (ultra-barato)**: 51% pass rate medio

### Criterios

| Criterio | Resultado | Cumple? |
|----------|-----------|---------|
| Mejor cadena > baseline | 56% vs 32% | SI |
| >=1 config con >=90% pass rate | 56% | NO |
| Config D >= 70% | 51% | NO |
| Debugger sube >=30% de fallos | 16% (7/45) | NO |
| Config F ~= Config B | F=18% vs B=37% | NO |

### Veredicto

**NO, la cadena no es suficiente hoy.** Mejor cadena: 56% pass rate.

La cadena de montaje **supera al modelo solo** en +24%.

---
*Generado por exp5_analyze.py*

### EXP 5b — Modelos Nuevos en Pipeline

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


### EXP 1 BIS — 6 Modelos Nuevos

# EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas

**Fecha:** 2026-03-11
**Provider:** OpenRouter

## Tabla Principal: Modelo × Tarea (scores 0-1)

| Modelo | T1 Cognitivo | T2 Evaluador | T3 Math | T4 Código | T5 Síntesis | **Media** | **Coste** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| kimi-k2.5 | 0.81 🟡 | **0.89** 🟢 | 0.80 🟡 | 0.80 🟡 | **1.00** 🟢 | **0.86** | $0.038 |
| qwen3.5-397b | 0.59 🔴 | **0.88** 🟢 | 0.80 🟡 | **1.00** 🟢 | **1.00** 🟢 | **0.85** | $0.033 |
| nemotron-super | **1.00** 🟢 | **0.88** 🟢 | **1.00** 🟢 | **0.90** 🟢 | **1.00** 🟢 | **0.96** | $0.007 |
| step-3.5-flash | **1.00** 🟢 | **0.89** 🟢 | **1.00** 🟢 | **1.00** 🟢 | **1.00** 🟢 | **0.98** | $0.019 |
| mimo-v2-flash | **1.00** 🟢 | **0.89** 🟢 | 0.60 🔴 | **1.00** 🟢 | **1.00** 🟢 | **0.90** | $0.001 |
| devstral | **1.00** 🟢 | 0.50 🔴 | 0.80 🟡 | **1.00** 🟢 | **1.00** 🟢 | **0.86** | $0.004 |

## Rankings

### Overall

| # | Modelo | Score | Coste |
|---|--------|:---:|:---:|
| 1 | step-3.5-flash | 0.98 | $0.019 |
| 2 | nemotron-super | 0.96 | $0.007 |
| 3 | mimo-v2-flash | 0.90 | $0.001 |
| 4 | kimi-k2.5 | 0.86 | $0.038 |
| 5 | devstral | 0.86 | $0.004 |
| 6 | qwen3.5-397b | 0.85 | $0.033 |

### Mejor por Tarea

- **T1 (Análisis Cognitivo):** Mejor=nemotron-super, Media=0.90
- **T2 (Evaluación Output):** Mejor=step-3.5-flash, Media=0.82
- **T3 (Razonamiento Math):** Mejor=nemotron-super, Media=0.83
- **T4 (Generación Código):** Mejor=qwen3.5-397b, Media=0.95
- **T5 (Síntesis Multi-Fuente):** Mejor=kimi-k2.5, Media=1.00

## Recomendaciones por Rol OMNI-MIND

| **Pizarra (agent swarm)** | kimi-k2.5 | ✅ SÍ (0.91 vs 0.8) | T1 + T5 ≥ 0.80 → Supera GPT-OSS |
| **Evaluador** | qwen3.5-397b | ✅ SÍ (0.88 vs 0.85) | T2 ≥ 0.85 → Discriminación perfecta en H4/H5 |
| **Math/Validación numérica** | nemotron-super | ✅ SÍ (1.00 vs 0.8) | T3 ≥ 0.80 → 4/5 problemas correctos |
| **Debugger/Razonador** | step-3.5-flash | ✅ SÍ (1.00 vs 0.85) | T3 + T4 ≥ 0.85 → Math + código funcional |
| **Tier barato universal** | mimo-v2-flash | ✅ SÍ (0.90 vs 0.65) | Media ≥ 0.65 → Aceptable en todo a $0.10/M |
| **Patcher (#1 SWE)** | devstral | ✅ SÍ (1.00 vs 0.85) | T4 ≥ 0.85 → Tests pasan sin debug |

## Coste Total

- **Tokens input:** 13,781
- **Tokens output:** 98,240
- **Coste total:** $0.102

---
*Generado: 2026-03-11 01:06:49*

### EXP 6 — OpenHands

# EXP 6 — Fase 1: Análisis de OpenHands

Fecha: 2026-03-11
Fuente: github.com/All-Hands-AI/OpenHands (commit más reciente)

## 1. Loop principal: observe→think→act

**Archivo:** `openhands/controller/agent_controller.py` (líneas 863-1039)

OpenHands usa un loop event-driven:
- **observe**: `_on_event()` procesa eventos del EventStream (Actions y Observations)
- **think**: `agent.step(state)` llama al LLM para generar la siguiente acción
- **act**: La acción se añade al EventStream, triggering observers

**Max iteraciones: 500** (configurable via `OpenHandsConfig.max_iterations`)

**Condiciones de parada:**
```python
# Control flags check
self.state_tracker.run_control_flags()  # Throws si límites alcanzados

# Stuck detection
if self.agent.config.enable_stuck_detection and self._is_stuck():
    raise AgentStuckInLoopError('Agent got stuck in a loop')

# Budget check
if self.current_value >= self.max_value:
    raise RuntimeError('Agent reached maximum budget.')
```

**Patrón clave:** El agente NO ejecuta directamente — emite Actions al EventStream, y el Runtime las ejecuta y devuelve Observations.

## 2. Sandbox: Docker isolation

**Archivo:** `openhands/runtime/impl/docker/docker_runtime.py`

- Cada agente corre en un **contenedor Docker** aislado
- Runtime: servidor HTTP dentro del contenedor (puertos 30000-39999)
- Volúmenes configurados via Docker API (`Mount` types)
- Contenedor creado al inicio, destruido al final
- Fallback: CLI runtime para ejecución local/test sin Docker

```python
self.docker_client = self._init_docker_client()
self.container = None  # Se crea/destruye automáticamente
```

## 3. Timeouts

**Archivos:** `action_execution_client.py:283-349`, `sandbox_config.py:68`

- **Per-command timeout: 120s** (default, configurable por acción)
- Buffer de 5s extra para captura de errores client-side
- Si timeout → `AgentRuntimeTimeoutError` → se convierte en `ErrorObservation` visible al agente
- Blocking commands sin timeout → RuntimeError inmediato

```python
if action.timeout is None:
    if isinstance(action, CmdRunAction) and action.blocking:
        raise RuntimeError('Blocking command with no timeout set')
    action.set_hard_timeout(self.config.sandbox.timeout, blocking=False)
```

## 4. Loops infinitos: 5 escenarios de detección

**Archivo:** `openhands/controller/stuck.py`

| Escenario | Condición | Umbral |
|-----------|-----------|--------|
| Acción+Observación repetida | Mismo par exacto | 4x consecutivas |
| Acción+Error repetido | Mismo error | 3x consecutivas |
| Monólogo | Habla sin acciones | Detectado |
| Patrón cíclico largo | Ciclo en historial | 6+ pasos |
| Context window error | Repetido ContextWindowExceeded | 10+ pasos |

**Respuesta:** `AgentStuckInLoopError` → estado ERROR, ejecución parada.

## 5. Comandos peligrosos: modelo de riesgo (NO blacklist)

**Archivos:** `security/invariant/analyzer.py`, `tools/security_utils.py`

OpenHands **NO usa blacklist**. Usa un modelo basado en riesgo:
- Risk levels: LOW, MEDIUM, HIGH
- HIGH o UNKNOWN → requiere confirmación del usuario
- Sin analyzer configurado → TODO es UNKNOWN → pide confirmación
- Seguridad delegada a: contenedor Docker + confirmación + auto-evaluación del LLM

**Insight para nuestro agente:** Sin Docker necesitamos blacklist explícita.

## 6. Gestión de contexto: Condenser plugin

**Archivos:** `controller/state/state_tracker.py`, `codeact_agent.py:200-216`

- **Sliding window** via plugin Condenser (configurable por agente)
- Cuando contexto excede ventana → `CondensationRequestAction`
- Sumariza eventos antiguos, preserva historial reciente
- No hay truncamiento automático a nivel framework — depende del Condenser

```python
match self.condenser.condensed_history(state):
    case View(events=events, forgotten_event_ids=forgotten_ids):
        condensed_history = events
    case Condensation(action=condensation_action):
        return condensation_action
```

## 7. Tool calling: function calling JSON

**Archivos:** `codeact_agent.py:116-157`, `function_calling.py:80-200+`

**9 herramientas:**
1. Bash (run shell commands)
2. IPython (run Python code)
3. File editor (str_replace_editor)
4. Browser (browse URLs)
5. Think (internal reasoning)
6. Finish (mark task complete)
7. Task tracker (manage tasks)
8. Condensation request (memory cleanup)
9. MCP tools (dynamic integrations)

**Formato: JSON function calling** (OpenAI-compatible via LiteLLM):
```json
{
  "tool_calls": [{
    "function": {
      "name": "bash",
      "arguments": "{\"command\": \"ls -la\", \"timeout\": 30}"
    },
    "id": "call_abc123"
  }]
}
```

## 8. Recuperación de errores

**Archivos:** `agent_controller.py:323-411, 916-976`, `retry_mixin.py`

**Patrón:** Error → ErrorObservation → el agente VE el error en su historial → decide siguiente acción.

**Errores capturados:**
- LLM: `LLMMalformedActionError`, `LLMNoActionError`, `LLMResponseError`
- Function: `FunctionCallValidationError`, `FunctionCallNotExistsError`
- Contexto: `ContextWindowExceededError` → trigger condensation
- API: `AuthenticationError`, `RateLimitError`, `ServiceUnavailableError`

**Retry:** Exponential backoff via Tenacity (`wait_exponential(multiplier=1, min=4, max=15)`)
- 3-5 intentos por defecto

## 9. Multi-modelo: LLMRegistry + LiteLLM

**Archivos:** `llm/llm_registry.py`, `llm/llm.py:64-115`, `llm/router/`

- **LLMRegistry** como factory de instancias LLM
- **LiteLLM** abstrae todos los providers (OpenAI, Claude, Gemini, Groq, local)
- **Router** opcional para dirigir diferentes prompts a diferentes modelos
- Cada LLM tiene `service_id` para tracking/métricas
- API key rotation y normalización de timeouts

## 10. Métricas

**Archivo:** `openhands/llm/metrics.py`

| Métrica | Tipo | Descripción |
|---------|------|-------------|
| `accumulated_cost` | float (USD) | Coste total acumulado |
| `prompt_tokens` | int | Tokens de entrada por llamada |
| `completion_tokens` | int | Tokens de salida por llamada |
| `cache_read/write_tokens` | int | Tokens de caché (Anthropic) |
| `response_latencies` | list[float] | Latencia por llamada |
| `max_budget_per_task` | float | Límite duro — para agente si excede |

**Budget enforcement:** Si coste acumulado > max_budget → RuntimeError.

## Patrones Clave para Nuestro Agente

1. **Event-driven > imperativo**: Separar acciones de observaciones permite retry limpio
2. **Error como input**: El error completo va al agente como Observation, no como excepción
3. **Stuck detection multi-escenario**: No basta con 1 check — necesitas 3-5 patrones
4. **Sin blacklist, con risk model**: Pero solo funciona con Docker. Sin Docker → blacklist
5. **Condenser > truncate**: Sumarizar es mejor que cortar, pero requiere LLM call extra
6. **Budget enforcement**: Imprescindible — los loops agenticos pueden costar mucho
7. **Function calling JSON**: Más robusto que parsing de texto libre
8. **5 herramientas son suficientes**: bash + file editor + finish cubren el 95% de los casos


### EXP 7 — exp7_r1_cogito

# R1 Design: Cogito 671B
**Perspectiva:** Sintesis -- como conectar Motor + Gestor + Agente + Chat?

# Rediseño del Sistema Conversacional de OMNI-MIND (Chief of Staff)

## A. Arquitectura del Sistema

```
[USUARIO]
     │
     ▼
  [CHAT UI] ◄─────────────┐
     │                     │
     │ (input + contexto)  │ (respuesta + preguntas)
     ▼                     │
[INTERFAZ DE CHAT]         │
     │                     │
     ├────▶ [MOTOR v3.3]   │
     │         │           │
     │         ▼           │
     │   [GESTOR MATRIZ]   │
     │         │           │
     │         ▼           │
     └───── [AGENTE] ◄─────┘
               │
               ▼
  [BACKEND: Postgres + Redis]
```

## B. Componentes Principales (8)

1. **Motor de Conversación (Orquestador)**
   - Función: Coordina el flujo completo de la conversación
   - Modelo: DeepSeek V3.2 (mejor orquestador según EXP 5b)
   - Herramientas: Detector de gaps, Router de tareas, Gestor de contexto
   - Comunicación: Estigmergia (marcas Postgres) + Redis para estado

2. **Analizador de Campo de Gradientes**
   - Función: Mapea gaps en la matriz 3Lx7F
   - Modelo: DeepSeek R1 (mejor en continuidad según EXP 4)
   - Herramientas: Matriz 3Lx7F, Historial de conversación
   - Comunicación: Marcas estigmergicas

3. **Generador de Preguntas**
   - Función: Crea preguntas basadas en gaps detectados
   - Modelo: MiMo V2 Flash ($0.001/llamada, EXP 1bis)
   - Herramientas: Plantillas de preguntas, Historial
   - Comunicación: Cola de preguntas en Redis

4. **Sintetizador de Respuestas**
   - Función: Integra información y genera respuesta natural
   - Modelo: Cogito-671B (mejor sintetizador, EXP 4)
   - Herramientas: Memoria de contexto, Plantillas
   - Comunicación: Canal directo con Motor

5. **Agente de Ejecución**
   - Función: Ejecuta acciones y código
   - Modelo: Devstral (mejor en coding, EXP 1bis)
   - Herramientas: Sandbox de ejecución, API de sistema
   - Comunicación: Cola de tareas en Redis

6. **Sistema de Memoria**
   - Función: Gestiona memoria a corto y largo plazo
   - Modelo: Nemotron Super ($0.007/llamada, EXP 1bis)
   - Herramientas: Vector DB, Cache de contexto
   - Comunicación: Postgres + Redis

7. **Monitor de Auto-mejora**
   - Función: Aprende de cada interacción
   - Modelo: Step 3.5 Flash ($0.019/llamada, EXP 5b)
   - Herramientas: Base de datos de efectividad
   - Comunicación: Marcas estigmergicas

8. **Validador de Seguridad**
   - Función: Verifica seguridad y coherencia
   - Modelo: Qwen 3.5 397B (mejor evaluador, EXP 1bis)
   - Herramientas: Listas de verificación, Políticas
   - Comunicación: Canal directo con Motor

## C. Flujo de un Turno de Chat

1. **Recepción** (200ms)
   - Usuario envía mensaje
   - Motor captura input + contexto
   - Validador de Seguridad verifica input

2. **Análisis Superficial** (500ms)
   - Motor ejecuta Detector de Gaps (primitivas INT-01 a INT-18)
   - Si gap < 0.3: responde directamente desde caché
   - Si gap > 0.3: inicia análisis profundo asíncrono

3. **Generación de Respuesta** (300ms)
   - Sintetizador genera respuesta inicial
   - Generador de Preguntas añade 2-3 preguntas
   - Sistema actualiza memoria con interacción

4. **Respuesta al Usuario** (<1s total)
   - Se envía respuesta + preguntas
   - Análisis profundo continúa en segundo plano

## D. Flujo del Pensamiento Profundo

1. **Mapeo de Campo** (3s)
   - Analizador ejecuta matriz 3Lx7F completa
   - Identifica gaps mayores a 0.3
   - Prioriza por impacto y urgencia

2. **Generación de Estrategia** (10s)
   - Motor selecciona mejores modelos para cada gap
   - Programa ejecución paralela
   - Prepara contexto necesario

3. **Ejecución Paralela** (15s)
   - Se ejecutan análisis en paralelo
   - Cada subtarea usa modelo óptimo
   - Resultados se almacenan en memoria

4. **Integración** (2s)
   - Sintetizador combina resultados
   - Generador crea preguntas de seguimiento
   - Actualiza memoria y perfil de usuario

## E. Integración con Motor Cognitivo

- **Detección de Gaps**: Usa primitivas INT-01 a INT-18
- **Matriz 3Lx7F**: Base para análisis de campo de gradientes
- **Asignación de Modelos**: Basada en datos de EXP 4 y EXP 1bis
- **Feedback Loop**: Cada interacción alimenta base de datos de efectividad

## F. Integración con Agente de Coding

1. **Detección de Necesidad**: Motor identifica tarea de codificación
2. **Preparación de Contexto**: 
   - Requisitos claros
   - Restricciones técnicas
   - Ejemplos relevantes
3. **Ejecución Controlada**:
   - Sandbox aislado
   - Timeout de 30s
   - Validación de resultados
4. **Integración de Resultados**:
   - Análisis de salida
   - Generación de resumen
   - Actualización de memoria

## G. Self-Improvement

1. **Recolección de Datos**:
   - Efectividad por pregunta
   - Tiempo de respuesta
   - Satisfacción del usuario implícita

2. **Análisis Periódico**:
   - Identificación de patrones
   - Detección de áreas de mejora
   - Optimización de asignación de modelos

3. **Actualización Automática**:
   - Ajuste de parámetros
   - Actualización de plantillas
   - Mejora de algoritmos

## H. Eliminado del Sistema Anterior

1. **Pipeline Dual**: Reemplazado por análisis de campo de gradientes
2. **9 Modos Conversacionales**: Simplificado a gradientes de comportamiento
3. **24 Agentes**: Reducido a 8 componentes más eficientes
4. **Dependencia de Anthropic**: Eliminada totalmente

## I. Conservado del Sistema Anterior

1. **Estigmergia**: Comunicación vía marcas en Postgres
2. **Cola de Preguntas**: Priorización inteligente
3. **Persistencia Inter-sesión**: Perfiles y memoria
4. **Detección de Contradicciones**: Mejorada con multi-modelo

## J. Estimación de Coste por Turno

| Componente | Coste/Turno | Frecuencia | Coste Total |
|------------|-------------|------------|-------------|
| Motor | $0.002 | 1x | $0.002 |
| Analizador | $0.001 | 0.3x | $0.0003 |
| Generador Preguntas | $0.0001 | 2x | $0.0002 |
| Sintetizador | $0.003 | 1x | $0.003 |
| Memoria | $0.0005 | 1x | $0.0005 |
| Validador | $0.0002 | 1x | $0.0002 |
| **Total** | | | **$0.0062** |

- **Costo Objetivo**: <$0.02/turno ✓
- **Latencia Objetivo**: <1s (superficial), <30s (profundo) ✓
- **Mejora**: 84% más barato que sistema anterior ($0.10 → $0.0062)

Este diseño cumple con todos los requisitos, aprovecha los hallazgos empíricos recientes y mantiene las fortalezas del sistema anterior mientras elimina sus limitaciones.

### EXP 7 — exp7_r1_deepseek

# R1 Design: DeepSeek V3.2
**Perspectiva:** Arquitectura -- que estructura minimiza complejidad y maximiza capacidad?

# Rediseño del Chief of Staff (OMNI-MIND) - Arquitectura Optimizada

Basado en la evidencia empírica y los requisitos, propongo una arquitectura radicalmente simplificada que maximiza capacidad operativa mientras minimiza complejidad.

## A. Arquitectura (Diagrama ASCII)

```
┌───────────────────────────────────────────────────────┐
│                   CHIEF OF STAFF v2                   │
│                                                       │
│  ┌─────────────┐    ┌─────────────────────────────┐  │
│  │             │    │                             │  │
│  │  Detector   │◄──►│   Motor de Pensamiento      │  │
│  │  de Huecos  │    │    (Superficial/Profundo)   │  │
│  │             │    │                             │  │
│  └──────┬──────┘    └───────────────┬─────────────┘  │
│         │                           │                │
│         ▼                           ▼                │
│  ┌─────────────┐    ┌─────────────────────────────┐  │
│  │  Gestor de  │    │                             │  │
│  │  Preguntas  │    │    Ejecutor de Acciones     │  │
│  │ Compiladas  │    │     (Coding/Workflows)      │  │
│  └──────┬──────┘    └───────────────┬─────────────┘  │
│         │                           │                │
│         ▼                           ▼                │
│  ┌─────────────┐    ┌─────────────────────────────┐  │
│  │  Sintetiz   │    │                             │  │
│  │ Multi-Modelo│    │    Memoria Evolutiva        │  │
│  │             │    │ (Perfil+Decisiones+Stats)   │  │
│  └─────────────┘    └─────────────────────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘
```

## B. Componentes (8 núcleos)

1. **Detector de Huecos**
   - *Función*: Identifica gaps en el input usando 7 primitivas sintácticas (basado en Motor v3.3)
   - *Modelo*: DeepSeek V3.1 (empírico: 95% precisión en EXP 4)
   - *Herramientas*: Matriz 3Lx7F como referencia, parser sintáctico
   - *Comunicación*: Estigmergia (marcas tipo "gap_detectado")

2. **Motor de Pensamiento**
   - *Función*: Orquesta flujo superficial/profundo basado en gaps
   - *Modelo*: Router multi-modelo (DeepSeek V3.2 + R1 + MiMo V2 Flash)
   - *Herramientas*: Pipeline configurable, timer de latencia
   - *Comunicación*: Eventos via Postgres (think_events)

3. **Gestor de Preguntas Compiladas**
   - *Función*: Recibe programa de preguntas del Gestor de Matriz
   - *Modelo*: NetworkX (álgebra de preguntas) + GPT-OSS 120B (empírico: mejor en distribución)
   - *Herramientas*: Cola priorizada, sistema de dosificación
   - *Comunicación*: Direct call al Gestor de Matriz (1x/hora)

4. **Ejecutor de Acciones**
   - *Función*: Ejecuta código/workflows cuando se detecta necesidad
   - *Modelo*: Devstral + Step 3.5 Flash (empírico: 100% en T1 EXP 5b)
   - *Herramientas*: Sandbox ejecución, monitor de recursos
   - *Comunicación*: Marcas "accion_solicitada" + callbacks

5. **Sintetizador Multi-Modelo**
   - *Función*: Integra respuestas usando mejores modelos por dominio
   - *Modelo*: Cogito-671B (empírico: score 170 vs 141 en EXP 4)
   - *Herramientas*: Plantillas de verbalización, validador de coherencia
   - *Comunicación*: Consume marcas de otros componentes

6. **Memoria Evolutiva**
   - *Función*: Almacena perfil, decisiones y estadísticas de efectividad
   - *Modelo*: MiMo V2 Flash (empírico: $0.001/turno en EXP 1bis)
   - *Herramientas*: Compresor de contexto, buscador semántico
   - *Comunicación*: Escritura directa a tablas SQL

7. **Monitor de Recursos**
   - *Función*: Aplica presupuestos y timeouts
   - *Modelo*: Código puro (0 LLM)
   - *Herramientas*: Kill switches, limitadores de tasa
   - *Comunicación*: Intercepta todas las llamadas a modelos

8. **Auto-Mejorador**
   - *Función*: Ajusta parámetros basado en datos históricos
   - *Modelo*: DeepSeek V3.2 (empírico: mejor arquitecto en EXP 4)
   - *Herramientas*: Dataset de entrenamiento, evaluador A/B
   - *Comunicación*: Lee estadísticas, escribe configuraciones

## C. Flujo de un Turno de Chat (Paso a Paso)

1. **Entrada de Usuario** (0ms)
   - Evento: nuevo_input
   - Acción: Se escribe en tabla `marcas` con tipo "input_usuario"

2. **Detección Rápida** (200-500ms)
   - Detector de Huecos analiza input contra Matriz 3Lx7F
   - Si gaps simples -> responde inmediato desde caché
   - Si gaps complejos -> dispara Motor de Pensamiento

3. **Pensamiento Superficial** (800ms)
   - Motor usa modelo barato (MiMo V2 Flash) para:
     - Clasificar intención
     - Extraer entidades clave
     - Buscar en memoria respuestas similares

4. **Generación Preguntas** (1s)
   - Gestor de Preguntas compila 2-3 preguntas basadas en gaps
   - Prioriza usando: urgencia, perfil usuario, historial

5. **Sintesis Respuesta** (1.2s)
   - Sintetizador combina:
     - Respuesta rápida
     - Preguntas prioritarias
     - Acciones sugeridas (si aplica)

6. **Monitoreo** (en paralelo)
   - Si se detectan gaps profundos -> inicia pipeline profundo async
   - Si input requiere acción -> pasa a Ejecutor

## D. Flujo del Pensamiento Profundo (Paso a Paso)

1. **Inicio** (0ms)
   - Trigger: gap > 0.3 en al menos 3 celdas de la Matriz

2. **Descomposición** (1s)
   - Motor divide problema en sub-tareas usando primitivas INT-XX

3. **Asignación Modelos** (2s)
   - Para cada sub-tarea selecciona mejor modelo (datos EXP 4):
     - Razonamiento: DeepSeek V3.2
     - Creatividad: R1
     - Validación: Nemotron Super

4. **Ejecución Paralela** (10s)
   - Cada modelo resuelve su parte con:
     - Timeout individual
     - Presupuesto de tokens
     - Plantilla específica

5. **Integración** (5s)
   - Cogito-671B sintetiza resultados parciales
   - Verifica coherencia con decisiones previas

6. **Generación Output** (3s)
   - Crea:
     - Respuesta verbal
     - Acciones recomendadas
     - Preguntas de seguimiento

7. **Registro** (2s)
   - Memoria Evolutiva guarda:
     - Gaps iniciales/finales
     - Modelos usados
     - Efectividad por celda

## E. Integración con Motor Cognitivo

- **Matriz 3Lx7F como Fuente de Verdad**:
  - Los gaps dirigen todo el flujo (no modos predefinidos)
  - Cada 1h recibe programa actualizado de preguntas
  - Reporta estadísticas de efectividad por celda/INT

- **Diferencias Clave**:
  - Elimina router de intenciones (usa detector de huecos)
  - Reemplaza pipeline fijo por composición dinámica
  - Usa múltiples modelos especializados (no solo Claude)

## F. Integración con Agente de Coding

- **Activación**:
  - Cuando se detecta necesidad de:
    - Auto-mejora (cambios <20 líneas)
    - Implementación de workflows
    - Corrección de errores

- **Flujo**:
  1. Ejecutor crea especificación técnica
  2. Devstral genera código inicial
  3. Step 3.5 Flash revisa y debuggea
  4. Monitor ejecuta en sandbox
  5. Si pasa tests -> despliegue automático

## G. Self-Improvement

1. **Datos Recopilados**:
   - Efectividad por tipo de gap
   - Rendimiento por modelo/subtarea
   - Tasa de cierre de preguntas
   - Satisfacción usuario implícita

2. **Mecanismos**:
   - Ajuste semanal de parámetros (Auto-Mejorador)
   - Podar preguntas inefectivas (basado en stats)
   - Re-asignar modelos a subtareas (EXP 4)
   - Generar nuevos tests automáticos

3. **Límites**:
   - Cambios arquitectónicos requieren CR1
   - Máximo 5% variación diaria en parámetros
   - Backup automático pre-cambios

## H. Qué se Elimina del Chief Viejo y Por Qué

1. **24 Agentes Específicos**:
   - Reemplazados por pipeline dinámico basado en gaps
   - Evidencia: EXP 5b muestra que modelos modernos hacen trabajo equivalente con menos componentes

2. **9 Modos Conversacionales**:
   - Sobrediseño (overengineered según documento maestro)
   - Los gradientes emergen naturalmente de la Matriz

3. **Router de Intenciones**:
   - El detector de huecos es más preciso (95% vs ~80%)
   - Menos propenso a errores de clasificación

4. **Pipeline Dual Fijo**:
   - Reemplazado por composición dinámica basada en gaps
   - Permite más flexibilidad (EXP 5 mostró límites del enfoque lineal)

## I. Qué se Conserva del Chief Viejo y Por Qué

1. **Estigmergia**:
   - Patrón probado que reduce acoplamiento
   - Permite escalabilidad horizontal

2. **Cola Priorizada de Preguntas**:
   - Mecanismo efectivo para engagement
   - Mejorado con datos de efectividad del Gestor

3. **Persistencia Inter-sesión**:
   - Clave para continuidad conversacional
   - Ahora con compresión más eficiente (MiMo V2)

4. **Detección Contradicciones**:
   - Integrado como paso del pipeline
   - Usa multi-modelo para mayor precisión

## J. Estimación de Coste por Turno

| Componente               | Coste   | Modelo                  | Frecuencia |
|--------------------------|---------|-------------------------|------------|
| Detección Huecos         | $0.0003 | DeepSeek V3.1           | 100%       |
| Pensamiento Superficial  | $0.001  | MiMo V2 Flash           | 100%       |
| Gestor Preguntas         | $0.0005 | GPT-OSS 120B            | 30%        |
| Sintesis Respuesta       | $0.002  | Cogito-671B             | 100%       |
| Pensamiento Profundo     | $0.005  | Multi-modelo (avg)      | 20%        |
| Memoria                  | $0.0002 | MiMo V2 Flash           | 100%       |
| Auto-Mejorador           | $0.001  | DeepSeek V3.2           | 5%         |
| **Total promedio**       | **$0.015** |                         |            |

**Optimizaciones Clave**:
- Uso estratégico de modelos baratos (MiMo V2) para tareas simples
- Ejecución paralela optimizada (EXP 4)
- Cache agresivo de respuestas frecuentes
- Limitación estricta de tokens por subtarea

Esta arquitectura logra:
- 85% reducción de coste vs sistema anterior
- 50% menor latencia en modo superficial
- 2x más capacidad (puede actuar y auto-mejorarse)
- 70% menos componentes (8 vs 24)

### EXP 7 — exp7_r1_kimi

# R1 Design: Kimi K2.5
**Perspectiva:** Enjambre -- como orquestar multiples modelos como agentes?

Aquí está el rediseño completo del **Chief of Staff v2.0** (codename: *Enjambre*), migrando de un orquestador monolítico a una arquitectura de agentes especializados basada en evidencia empírica.

---

## A. ARQUITECTURA (Diagrama ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE INTERACCIÓN                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Usuario    │◄──►│   Chat API   │◄──►│   Director   │      │
│  │  (Turno N)   │    │  (Edge/Deno) │    │ (V3.2-chat)  │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────┐
                    │         ORQUESTACIÓN         │              │
                    │                              ▼              │
                    │  ┌─────────────────────────────────────┐   │
                    │  │     COMPILADOR DE MATRIZ            │   │
                    │  │     (MiMo V2 Flash + Código puro)   │   │
                    │  │  • Compila programa de preguntas    │   │
                    │  │  • Lee scores de efectividad        │   │
                    │  │  • Selecciona modelo por celda      │   │
                    │  └──────────────┬──────────────────────┘   │
                    │                 │                           │
                    ▼                 ▼                           │
┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│   MODO SUPERFICIAL (<1s)    │  │    MODO PROFUNDO (<30s)     │  │
│  ┌─────────────────────┐    │  │  ┌─────────────────────┐    │  │
│  │  DETECTIVE DE GAPS  │    │  │  │  AGENTE ANALÍTICO   │    │  │
│  │   (MiMo V2 Flash)   │    │  │  │  (Step 3.5 Flash)   │    │  │
│  │  • Paso 0 Motor v3  │    │  │  │  • Loop observe→act │    │  │
│  │  • 7 primitivas     │    │  │  │  • Max 5 iteraciones│    │  │
│  │  • Falacias aritm.  │    │  │  │  • Stuck detection  │    │  │
│  └──────────┬──────────┘    │  │  └──────────┬──────────┘    │  │
│             │               │  │             │               │  │
│  ┌──────────▼──────────┐    │  │  ┌──────────▼──────────┐    │  │
│  │   GUARDIÁN DE       │    │  │  │   ARTESANO DE       │    │  │
│  │   MEMORIA           │    │  │  │   CÓDIGO            │    │  │
│  │  (MiMo + Postgres)  │    │  │  │  (Devstral + Qwen3) │    │  │
│  │  • Cola priorizada  │    │  │  │  • Ejecuta pipelines│    │  │
│  │  • Estigmergia      │    │  │  │  • Modifica agentes │    │  │
│  │  • Perfil usuario   │    │  │  │  • Sandbox seguro   │    │  │
│  └──────────┬──────────┘    │  │  └──────────┬──────────┘    │  │
│             │               │  │             │               │  │
└─────────────┼───────────────┘  └─────────────┼───────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│              SINTETIZADOR DE ENJAMBRE                         │
│         (Cogito-671B + GPT-OSS 120B paralelo)                 │
│  • Integra hallazgos multi-modelo                             │
│  • Verifica coherencia (POST sandwich)                        │
│  • Genera respuesta final + próximas preguntas                │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                   REFINADOR (Self-Improvement)                │
│              (DeepSeek V3.1 + Datos históricos)               │
│  • Actualiza scores: gap_pre vs gap_post                      │
│  • Podar preguntas (tasa<0.05)                                │
│  • Promover preguntas (tasa>0.40)                             │
│  • Recalcula asignación modelo→celda                          │
└───────────────────────────────────────────────────────────────┘
```

---

## B. COMPONENTES (Máximo 8)

### 1. DIRECTOR (DeepSeek V3.2-chat)
**Qué hace:** Enrutamiento de alto nivel, decisión superficial vs profundo, detección de cambio de tema, presupuesto de tokens por turno.

**Por qué este modelo:** EXP 4 demostró que V3.2-chat + V3.1 + R1 = 100% cobertura de celdas. V3.2 es el mejor generalista para orquestación (score 141 en síntesis vs 170 Cogito, pero 10x más barato y rápido).

**Herramientas:** 
- Router de intención (código puro basado en keywords)
- Control de presupuesto ($0.02 hard limit por turno)
- Scheduler de tareas paralelas

**Comunicación:** Direct call al Compilador y Detective; estigmergia (marca `director_decision`) para el resto.

---

### 2. COMPILADOR DE MATRIZ (MiMo V2 Flash + Código puro)
**Qué hace:** Implementa el "Gestor de la Matriz" local. Recibe el campo de gradientes (21 celdas) y compila el "Programa de Preguntas" óptimo para el contexto actual.

**Por qué este modelo:** EXP 1bis: MiMo V2 Flash ($0.001) es el "tier barato universal" (score 0.90). Las tareas mecánicas de compilación (filtrar preguntas muertas, asignar modelos) no requieren razonamiento profundo.

**Herramientas:**
- Query a `matriz_efectividad` (Postgres): scores por pregunta×modelo×celda
- Algoritmo de selección: maximiza cobertura de gaps > 0.3 con mínimo coste
- Cache de programas compilados (TTL 1h)

**Comunicación:** Lee marcas `gradiente_campo` (output del Detective); escribe marca `programa_compilado`.

---

### 3. DETECTIVE DE GAPS (MiMo V2 Flash)
**Qué hace:** Paso 0 del Motor v3.3. Detecta qué falta en el input usando las 7 primitivas sintácticas (INT-03) y 8 operaciones. Identifica falacias aritméticas.

**Por qué este modelo:** Paso 0 es mecánico y debe ser <200ms. MiMo es 20x más barato que Haiku y suficiente para parsing sintáctico (reemplaza a los 7 parseadores antiguos).

**Herramientas:**
- Regex compiladas para primitivas (INT-01 a INT-07)
- Detector de contradicciones simples (sandwich ligero: input→MiMo→check)
- Output: JSON con `huecos_detectados[]` y `gradientes_iniciales[21]`

**Comunicación:** Escribe marca `analisis_huecos`; nunca llama directamente.

---

### 4. AGENTE ANALÍTICO (Step 3.5 Flash + Loop iterativo)
**Qué hace:** Reemplaza el pipeline profundo lineal. Opera bajo el "Programa de Preguntas" compilado. Loop observe→think→act con máximo 5 iteraciones.

**Por qué este modelo:** EXP 5b demostró que Step 3.5 Flash es el #1 en debugging (resolvió T1 100% con Devstral). EXP 6 validó que el patrón OpenHands (loop event-driven) es necesario para romper el techo del 56% de pipelines lineales.

**Herramientas:**
- 9 herramientas tipo OpenHands: Bash, FileEditor, Think, Browser, TaskTracker
- Stuck detection: 5 patrones (acción repetida×4, error×3, monólogo, ciclo largo, context window)
- Condenser: sliding window + resumen cada 3 iteraciones
- Budget: max $0.015 por ejecución profunda

**Comunicación:** Lee `programa_compilado`; escribe marcas `hallazgo_iteracion_N`. No ejecuta código peligroso directamente (delega al Artesano).

---

### 5. ARTESANO DE CÓDIGO (Devstral + Qwen3 Coder)
**Qué hace:** Brazo ejecutor. Implementa cambios de código, modifica agentes, lanza pipelines de testing. Aislamiento vía blacklist (sin Docker por ahora).

**Por qué este modelo:** EXP 1bis: Devstral es #1 en SWE (score 0.86, $0.004). EXP 5b: Devstral + Step 3.5 = 100% pass rate en T1. Qwen3 Coder genera tests unitarios y valida.

**Herramientas:**
- FileEditor con diff semántico
- Test runner local (Deno/Node)
- Git operations (branch, commit, PR)
- Sandbox: blacklist de comandos peligrosos (rm -rf, curl | bash)

**Comunicación:** Recibe tareas vía marca `tarea_codigo` del Agente Analítico o Director; escribe `resultado_codigo` + `tests_passed`.

---

### 6. SINTETIZADOR DE ENJAMBRE (Cogito-671B + GPT-OSS 120B paralelo)
**Qué hace:** Integra hallazgos del Agente Analítico y contexto histórico. Genera respuesta final en lenguaje natural + próximas 2 preguntas.

**Por qué estos modelos:** EXP 4: Cogito-671B es el mejor sintetizador (score 170, 100% genuinidad, 3.6 conexiones cross-lente). GPT-OSS 120B es el mejor contribuidor en pizarra iterativa (119 aportes). Ejecutar en paralelo y fusionar sus outputs supera a cualquier modelo solo.

**Herramientas:**
- Fusion de outputs: combina respuesta Cogito (profundidad) + GPT-OSS (creatividad)
- Verificador de coherencia (sandwich POST: output→MiMo→check vs decisiones previas)
- Selector de modo conversacional implícito (emerge de gaps, no explícito)

**Comunicación:** Lee marcas `hallazgo_*` y `perfil_usuario`; escribe `respuesta_final` + `cola_preguntas`.

---

### 7. GUARDIÁN DE MEMORIA (MiMo V2 Flash + Código puro)
**Qué hace:** Gestiona estigmergia, cola priorizada, persistencia inter-sesión, compresión de memoria.

**Por qué este modelo:** Tareas mecánicas de I/O y ranking. Reemplaza a chief-datos, chief-mcm, calculador, y compresor-memoria antiguos.

**Herramientas:**
- `priorizarCola()`: ranking por urgencia (gap alto) + relevancia histórica
- `actualizarPerfil()`: extrae patrones/decisiones vía regex + embeddings ligeros
- `compactarMarcas()`: GC de marcas consumidas (>24h)
- `detectarCambioTema()`: cosine similarity vs embeddings sesión previa

**Comunicación:** Todas las operaciones vía Postgres (`marcas_estigmergicas`). Es el único componente que escribe en `perfil_usuario` y `decisiones_chief`.

---

### 8. REFINADOR (DeepSeek V3.1 + Datos históricos)
**Qué hace:** Self-improvement. Analiza resultados de cada interacción para optimizar la Matriz. Corre en background (async) cada 10 turnos o al cerrar sesión.

**Por qué este modelo:** V3.1 es barato ($0.005) y bueno para análisis estadístico y código. No requiere creatividad, sí procesamiento de datos.

**Herramientas:**
- Query a `historial_cierres`: gap_pre, gap_post, modelo_usado, tasa_cierre
- Algoritmo de poda: elimina preguntas con n>10, tasa<0.05
- Algoritmo de promoción: marca preguntas con n>10, tasa>0.40 como "default"
- Recalculador de asignación: qué modelo va a qué celda basado en efectividad histórica

**Comunicación:** Lee todas las marcas de la sesión; escribe en `matriz_efectividad` y `configuracion_enjambre`.

---

## C. FLUJO DE UN TURNO DE CHAT (Paso a paso)

### Turno Tipo 1: Superficial/Rápido (<1s, ~$0.005)

1. **Input usuario** → Edge Function recibe mensaje
2. **Director** (V3.2, $0.01) decide: "superficial" (consulta simple, no gaps críticos)
3. **Detective** (MiMo, $0.001) corre en paralelo:
   - Detecta huecos sintácticos en <200ms
   - Si gap_max < 0.3: continúa superficial
   - Si gap_max >= 0.3: marca para profundo (fire-and-forget)
4. **Guardián** (código puro):
   - `actualizarCola()` con input usuario
   - Filtra preguntas ya resueltas
   - Selecciona top 2 de cola existente
5. **Sintetizador** (modo ligero: solo GPT-OSS o incluso V3.2, $0.01):
   - Genera respuesta corta + 2 preguntas de la cola
6. **Response** → Usuario recibe respuesta en ~800ms
7. **Background** (async): Si se detectaron gaps graves, lanza Agente Analítico para próximo turno

### Turno Tipo 2: Profundo/Análisis (<30s, ~$0.018)

1. **Input usuario** → Director detecta que hay gaps pendientes o el usuario pide análisis
2. **Compilador** (MiMo, $0.001 + código):
   - Lee campo de gradientes (21 celdas) de la marca del Detective
   - Selecciona modelo óptimo por celda (ej: R1 para Frontera×Sentido, V3.1 para Conservar)
   - Compila "Programa de 5-7 preguntas específicas"
3. **Agente Analítico** (Step 3.5, max $0.015):
   - Iteración 1: Observa programa + contexto → Think → Act (busca datos)
   - Iteración 2: Observa resultados → Think → Act (analiza contradicciones)
   - Iteración 3: Verifica cierre de gaps (si gap > 0.3 persiste, iteración 4)
   - Max 5 iteraciones o hasta stuck detection
   - Escribe hallazgos en marcas `hallazgo_nivel_1`, `hallazgo_nivel_2`, etc.
4. **Guardián**: Actualiza cola con insights del análisis (prioriza gaps cerrados)
5. **Sintetizador** (Cogito + GPT-OSS paralelo, $0.08... *corrección: esto excede presupuesto*):

**Ajuste para cumplir <$0.02:**
- En modo profundo estándar, usar solo **Step 3.5** ($0.019) para análisis + **V3.2** ($0.01) para síntesis = $0.029... sigue siendo alto.

**Solución de coste:**
- **Modo Profundo Ligero**: Step 3.5 Flash ($0.019) hace análisis + síntesis en un solo paso (1 llamada, 1 iteración). Total: ~$0.02.
- **Modo Profundo Enjambre**: Solo cuando el usuario lo solicita explícitamente o es crítico. Usa Cogito ($0.08) pero amortizado en sesiones largas (cada 10 turnos, no cada turno).

6. **Refinador** (background): Actualiza scores de efectividad del modelo usado para las celdas tratadas.

---

## D. FLUJO DEL PENSAMIENTO PROFUNDO (Loop iterativo)

Basado en EXP 6 (OpenHands) y EXP 5b (Cadena de Montaje):

```
INICIO: Programa de Preguntas compilado + Contexto histórico
  │
  ▼
[OBSERVE] Leer marcas actuales, estado del sistema, gaps detectados
  │
  ▼
[THINK] Step 3.5 Flash genera plan de acción:
        - Qué información falta para cerrar gap X?
        - Qué herramienta usar (Browser, FileEditor, Bash)?
        - Qué modelo del enjambre consultar para opinión complementaria?
  │
  ▼
[ACT] Ejecuta acción (ej: consulta browser, lee archivo, llama a Devstral para patch)
  │
  ▼
[VERIFY] Chequea si se cerró el gap:
         - Si gap < 0.3: éxito, pasa a siguiente celda
         - Si gap >= 0.3 y reintentos < 2: vuelve a OBSERVE
         - Si reintentos >= 2: escala a modelo superior (Cogito) o marca como "gap persistente"
  │
  ▼
[STUCK DETECTION] Cada 3 iteraciones:
                  - ¿Acción repetida? → Aborta, cambia estrategia
                  - ¿Error idéntico? → Aborta, reporta al Refinador
                  - ¿Monólogo largo (>2K tokens sin acción)? → Condensar contexto
  │
  ▼
[OUTPUT] Escribe marca `sintesis_profunda` con:
         - Gaps cerrados (lista)
         - Gaps persistentes (lista + justificación)
         - Recomendaciones de acción (para Artesano o Usuario)
```

**Tiempo máximo:** 30s (timeout hard).  
**Presupuesto:** $0.015 por ejecución (max 3 iteraciones de Step 3.5).

---

## E. INTEGRACIÓN CON MOTOR COGNITIVO (Matriz 3Lx7F)

El Chief ya no "diagnostica" con IAS (parseadores + lentes). Ahora es un **consumidor compilado** de la Matriz:

1. **Entrada al Motor**: El Detective de Gaps implementa el **Paso 0** del Motor v3.3:
   - Usa las 7 primitivas sintácticas (INT-03) para mapear input a celdas
   - Genera el **Campo de Gradientes**: 21 valores (grado_actual vs grado_objetivo)

2. **Compilación**: El Compilador recibe este campo y ejecuta lógica del **Gestor de la Matriz**:
   - Para cada celda con gap > 0.3, consulta: "¿Qué INT cierra este gap con más efectividad?"
   - Selecciona top 3 inteligencias por impacto
   - Aplica **álgebra de composición** (13 reglas como restricciones duras vía NetworkX)

3. **Ejecución**: El Agente Analítico opera bajo el "Programa de Preguntas" que es el output del paso anterior. Las preguntas son el prompt (no hay texto imperativo).

4. **Verificación de Cierre**: Paso 6 del Motor. El Sintetizador verifica si los gaps se cerraron:
   - Si persisten gaps > 0.3: marca para re-intento o escalamiento
   - Máximo 2 re-intentos por celda

5. **Sin Modos**: Los 9 modos antiguos desaparecen. El "modo" emerge del campo de gradientes:
   - Todos los gaps bajos + usuario preguntando datos → modo "escucha"
   - Gaps altos en Frontera + Sentido → modo "confrontar"
   - Gaps en Operativo puro → modo "ejecutar"

---

## F. INTEGRACIÓN CON AGENTE DE CODING

El Chief ahora puede **actuar**, no solo analizar:

**Caso 1: Modificación de sí mismo**
- El Agente Analítico detecta que una función está obsoleta (gap en código)
- Escribe marca `tarea_refactor` con especificación
- **Artesano** (Devstral) lee la marca, crea branch, implementa cambio, corre tests
- Si tests pass: escribe `propuesta_cambio` para revisión humana (o auto-aprobar si <20 líneas según reglas de Fontanería)

**Caso 2: Lanzar pipelines externos**
- Usuario pide: "Analiza las ventas del Q3 y genera un reporte PDF"
- Director detecta tarea de código → enruta a Agente Analítico con herramienta `TaskTracker`
- Agente descompone: 1) Query datos, 2) Generar gráficos, 3) Compilar PDF
- Delega pasos 1-2 al Artesano (Qwen3 Coder para scripts Python)
- Sintetizador integra resultado y entrega al usuario

**Caso 3: Auto-mejora arquitectural**
- Refinador detecta que cierta celda de la Matriz nunca se cierra con el modelo actual
- Lanza `tarea_arquitectura`: "Evaluar si necesitamos nuevo modelo para celda X"
- Artesano investiga (browser) modelos nuevos en OpenRouter, actualiza `matriz_efectividad`

---

## G. SELF-IMPROVEMENT (Ciclo de aprendizaje)

Basado en Section 6F (Motor de auto-mejora):

**Nivel 1: Fontanería (Auto-aprobable)**
- Cada interacción registra: `gap_pre`, `gap_post`, `modelo_usado`, `coste`, `tiempo`, `tasa_cierre` (gap_post/gap_pre)
- Refinador detecta anomalías: "Step 3.5 cierra gap Frontera 40% mejor que V3.2"
- Ajusta asignación modelo→celda en tiempo real (próxima compilación usa nuevo modelo)

**Nivel 2: Mejoras Arquitecturales (CR1 - Code Review 1)**
- Cuando un gap persiste (>0.3) en 5 sesiones consecutivas, el Refinador genera `propuesta_mejora`:
  - "Añadir nueva pregunta tipo INT-16 para celda Distribuir×Sentido"
  - "Dividir Agente Analítico en dos especializados"
- Artesano implementa cambio en branch
- Director evalúa en sandbox (simulación con datos históricos)
- Si mejora tasa_cierre >10%: merge

**Nivel 3: Auto-evolución (Semillas dormidas)**
- Refinador mantiene lista de "semillas" (ideas para nuevos componentes)
- Cuando presupuesto mensual lo permite, activa semilla:
  - Ej: "Añadir modelo Nemotron Super para validación matemática" (EXP 1bis: score 0.96 en math)
- Corre 10 sesiones de prueba, compara vs baseline
- Si es mejor, promueve a componente permanente

---

## H. QUÉ SE ELIMINA DEL CHIEF VIEJO Y POR QUÉ

| Componente Eliminado | Razón (Evidencia) |
|---------------------|-------------------|
| **Pipeline dual superficial/profundo fijo** | Reemplazado por gradientes de la Matriz. El "modo" emerge de los gaps, no de rutas codificadas. |
| **9 modos conversacionales** | Overengineered (Section 8B). Los gradientes del campo determinan el comportamiento; no se necesitan modos explícitos. |
| **Router de intenciones (código puro)** | El detector de huecos del Motor v3.3 es más preciso que keywords (Section 4). |
| **24 agentes específicos** | Fan-out excesivo. EXP 1bis demostró que MiMo V2 Flash ($0.001) reemplaza trabajo de 7 parseadores + 9 lentes IAS. |
| **Profundo-runner (5 pasos secuenciales)** | Techo estructural de 56% (EXP 5). Reemplazado por Agente Analítico con loop iterativo (observe→think→act). |
| **Verbalizador monolítico (Sonnet)** | EXP 4: Un solo modelo es peor que síntesis multi-modelo (Cogito+GPT-OSS). Además, Claude es prescindible (0 aportes únicos). |
| **Chief-datos, chief-mcm, calculador** | Consolidados en Guardián de Memoria (MiMo + código puro). Tareas mecánicas no necesitan LLM caro. |
| **Dependencia Anthropic (Claude/Haiku/Sonnet)** | Coste ($0.10/turno) y lock-in. Modelos OS superan a Claude en la Matriz (V3.1: 2.19 vs Claude: 1.79, Section 6B). |
| **Comunicación síncrona entre agentes** | Reemplazada por estigmergia pura. El Chief viejo tenía llamadas sync "calculador + chief-datos" que bloqueaban. |

---

## I. QUÉ SE CONSERVA Y POR QUÉ

| Patrón Conservado | Justificación |
|------------------|---------------|
| **Estigmergia (marcas en Postgres)** | Funciona, cuesta $0, desacopla componentes. Evita cascadas de fallos. |
| **Cola priorizada de preguntas** | Dosifica insights complejos al usuario (2 preguntas/turno). Evita sobrecarga cognitiva. |
| **Persistencia inter-sesión** | `perfil_usuario` y `decisiones_chief` son datos críticos para coherencia a largo plazo. |
| **Detección de contradicciones** | Mecanismo validado (sandwich PRE→LLM→POST). Ahora integrado en Detective y Sintetizador. |
| **Concepto dual rápido/profundo** | El usuario necesita feedback inmediato (<1s) pero también análisis profundo (<30s). La dualidad se mantiene, la implementación cambia. |
| **Compresor de memoria** | Necesario para sesiones largas. MiMo V2 Flash reemplaza a Haiku pero mantiene función. |
| **Fire-and-forget para profundo** | Lanza análisis profundo en background mientras usuario recibe respuesta superficial. Optimiza tiempo de espera. |

---

## J. ESTIMACIÓN DE COSTE POR TURNO

### Escenario A: Turno Superficial (80% de los casos)
```
Director (V3.2, 2K tokens)        $0.008
Detective (MiMo, 1K tokens)       $0.001
Sintetizador ligero (V3.2, 1.5K)  $0.006
Guardián (código puro)            $0.000
-----------------------------------------
TOTAL                             $0.015
```
**Latencia:** ~600-800ms

### Escenario B: Turno Profundo Estándar (15% de los casos)
```
Director (V3.2)                   $0.008
Compilador (MiMo + código)        $0.001
Agente Analítico (Step 3.5 Flash) 
  - 2 iteraciones × $0.0095       $0.019
Sintetizador (V3.2, modo síntesis) $0.008
Refinador (background, amortizado) $0.002
-----------------------------------------
TOTAL                             $0.038
```
*Nota: Esto excede ligeramente $0.02, pero ocurre solo 1 de cada 6-7 turnos. Promedio ponderado: $0.019.*

**Optimización para cumplir <$0.02 en profundo:**
- Reducir a 1 iteración de Step 3.5 ($0.0095) + verificación ligera ($0.001) = $0.0105
- Total ajustado: $0.008 + $0.001 + $0.0105 + $0.008 = **$0.0275**... aún alto.

**Solución final:** Usar **DeepSeek V3.1** ($0.005) para análisis profundo (2 iteraciones = $0.01) en lugar de Step 3.5. EXP 4 demostró que V3.1 es efectivo (2.19 score).
- Coste profundo: $0.008 + $0.001 + $0.010 + $0.008 = **$0.027**

**Promedio real por usuario activo:**
- 80% × $0.015 = $0.012
- 20% × $0.027 = $0.0054
- **Promedio: $0.0174/turno** (vs $0.10 anterior = **82% de reducción**)

### Escenario C: Turno Profundo Enjambre (5% de casos críticos)
```
Sintetizador (Cogito-671B)        $0.08
GPT-OSS 120B (paralelo)           $0.015
Integración y fusión              $0.005
-----------------------------------------
TOTAL                             $0.10
```
*Justificación: Solo para decisiones arquitectónicas críticas o cuando el usuario explicita "piensa profundamente".*

---

## RESUMEN EJECUTIVO

El nuevo Chief of Staff pasa de ser un **orquestador monolítico de 24 agentes** a un **Director de Enjambre de 8 componentes**, eliminando la dependencia de Anthropic y reduciendo costes un 82%. 

La clave es la **Matriz 3Lx7F** como núcleo de diagnóstico (reemplazando IAS), la **diversidad de modelos OS** como dimensión algebraica (V3.2, Step 3.5, Devstral, Cogito), y el **loop iterativo** (tipo OpenHands) que rompe el techo del 56% de efectividad de los pipelines lineales.

El sistema ahora puede **actuar** (modificar código, lanzar pipelines) y **auto-mejorarse** (aprender de cada interacción qué preguntas y modelos funcionan mejor para cada celda de la Matriz), cumpliendo con el requisito de ser un "Chief of Staff" verdaderamente inteligente y autónomo.

### EXP 7 — exp7_r1_nemotron

# R1 Design: Nemotron Super
**Perspectiva:** Coste/eficiencia -- que se puede hacer con codigo puro ($0) vs LLM?

### A. ARQUITECTURA (DIAGRAMA ASCII)

```
+-----------------------------+
|        Usuario             |
+------------+---------------+
             |
             v
+-----------------------------+
|   Orquestador de Gaps      |  (Código puro)
|  - Paso 0 (Detector Huecos)|
|  - Paso 2 (Routing Gradient)|
+------------+---------------+
             |
             v
+-----------------------------+
|   Router de Modelos        |  (Código puro)
|  - Asignación por celda    |
|  - Selección modelo OS     |
+------------+---------------+
             |
             v
+-----------------------------+
|   Ejecutor Multi-Modelo     |  (LLM)
|  - Paralelo por celda      |
|  - Modelos: MiMo, Devstral,|
|    Step3.5, Cogito         |
+------------+---------------+
             |
             v
+-----------------------------+
|   Sintetizador de Respuestas |  (LLM)
|  - Combinación de outputs  |
|  - Modelo: Cogito (selectivo)|
+------------+---------------+
             |
             v
+-----------------------------+
|   Agente de Actuación       |  (Código puro)
|  - Lanzar pipelines         |
|  - Invocar Agente de Código |
+------------+---------------+
             |
             v
+-----------------------------+
|   Gestor de Persistencia    |  (Código puro)
|  - Perfil usuario            |
|  - Decisiones históricas     |
+------------+---------------+
             |
             v
+-----------------------------+
|   Optimizador de Coste      |  (Código puro)
|  - Selección dinámica modelo|
|  - Control de presupuesto   |
+------------+---------------+
             |
             v
+-----------------------------+
|   Detector de Contradicciones|  (Código puro)
|  - Comparación histórico     |
+----------------------------+
```

---

### B. COMPONENTES (MAX 8)

#### 1. **Orquestador de Gaps**
- **Función**: Detecta gaps usando primitivas sintácticas (Paso 0 del Motor) y routing por gradientes (Paso 2).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Parser de gaps, algoritmo de ranking gradientes.
- **Comunicación**: Estigmergia (Postgres) + eventos async.

#### 2. **Router de Modelos**
- **Función**: Asigna modelos OS óptimos por celda (basado en datos de EXP1bis y EXP4).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Reglas de asignación (ej: MiMo para celdas baratas, Step3.5 para debugging).
- **Comunicación**: API interna con Ejecutor.

#### 3. **Ejecutor Multi-Modelo**
- **Función**: Ejecuta modelos OS en paralelo por celda.
- **Modelo**: 
  - **MiMo V2 Flash** ($0.001): Tareas generales (EXP1bis).
  - **Devstral** ($0.004): Implementación rápida (EXP5b).
  - **Step3.5 Flash** ($0.019): Debugging complejo (EXP1bis).
- **Herramientas**: Paralelizador, timeout control.
- **Comunicación**: Prompts desde Matriz, outputs a Sintetizador.

#### 4. **Sintetizador de Respuestas**
- **Función**: Combina outputs de modelos en respuesta coherente.
- **Modelo**: **Cogito-671B** ($0.15/turno, usado selectivamente).
- **Herramientas**: Algoritmo de fusión lógica.
- **Comunicación**: Estigmergia + respuesta final al usuario.

#### 5. **Agente de Actuación**
- **Función**: Ejecuta acciones externas (coding, pipelines).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Integración con Agente de Coding, Docker sandbox.
- **Comunicación**: Llamadas directas a herramientas.

#### 6. **Gestor de Persistencia**
- **Función**: Almacenamiento inter-sesión (perfil, decisiones, cola emergencia).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Supabase Edge Functions, compresor de memoria.
- **Comunicación**: Estigmergia.

#### 7. **Optimizador de Coste**
- **Función**: Ajusta selección de modelos y parámetros para minimizar coste.
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Algoritmo de balance coste/efectividad.
- **Comunicación**: Feedback loop con Router.

#### 8. **Detector de Contradicciones**
- **Función**: Compara inputs con decisiones históricas.
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Motor de comparación semántica.
- **Comunicación**: Estigmergia.

---

### C. FLUJO DE UN TURNO DE CHAT

1. **Input Usuario** → Orquestador de Gaps
2. **Paso 0 (Detector Huecos)**: Identifica gaps en input (código puro).
3. **Paso 2 (Routing Gradient)**: Prioriza celdas por gap (código puro).
4. **Router de Modelos**: Asigna modelos OS óptimos (ej: MiMo para gaps simples).
5. **Ejecutor Multi-Modelo**: Ejecuta modelos en paralelo (LLM).
6. **Sintetizador**: Combina outputs (LLM selectivo).
7. **Agente de Actuación**: Si hay acción requerida, la ejecuta (código puro).
8. **Gestor de Persistencia**: Almacena datos inter-sesión (código puro).
9. **Optimizador**: Ajusta parámetros para próximo turno (código puro).

---

### D. FLUJO DEL PENSAMIENTO PROFUNDO

1. **Input + Gaps** → Motor v3.3 (Paso 0-2).
2. **Campo de Gradientes**: Calcula gaps (código puro).
3. **Routing por Gradients**: Selecciona modelos OS (código puro).
4. **Composición**: Ensambla preguntas (código puro, NetworkX).
5. **Ejecución Multi-Modelo**: Resuelve gaps (LLM).
6. **Verificación de Cierre**: Revisa gaps cerrados (LLM).
7. **Integración + Registro**: Sintetiza respuesta final (LLM).
8. **Gestor de Matriz**: Actualiza efectividad de preguntas (async, código puro).

---

### E. INTEGRACIÓN CON MOTOR COGNITIVO

- **Matriz 3Lx7F**: El Gestor compila preguntas específicas para el Chief basadas en gaps históricos.
- **Campo de Gradientes**: El Orquestador de Gaps usa las primitivas sintácticas del Motor para detectar gaps.
- **Routing**: El Router de Modelos asigna modelos OS según dominio de celda (ej: DeepSeek para Frontera, GPT-OSS para Depurar).

---

### F. INTEGRACIÓN CON AGENTE DE CODING

- **Agente de Actuación**: 
  - Detecta necesidad de implementación (ej: "Crea un script para X").
  - Llama al Agente de Coding con especificaciones.
  - Usa **Devstral** ($0.004) para implementación rápida (EXP5b).
  - Validación: **Step3.5 Flash** ($0.019) para debugging.

---

### G. SELF-IMPROVEMENT

1. **Registro de Efectividad**: 
   - Gap_pre vs gap_post por celda.
   - Tasa de cierre de gaps.
2. **Optimizador de Coste**:
   - Ajusta selección de modelos (ej: si MiMo falla en celda X, prueba Devstral).
3. **Gestor de Matriz**:
   - Actualiza preguntas compiladas basadas en datos de efectividad.
4. **Auto-corrección**:
   - Si un modelo falla repetidamente, se descarta (ej: Qwen3 inflador en EXP4).

---

### H. LO QUE SE ELIMINA DEL CHIEF VIEJO Y POR QUÉ

1. **Pipeline Dual Superficial/Profundo**: Reemplazado por Motor + Matriz (más eficiente).
2. **9 Modos Conversacionales**: Sustituidos por gradientes emergentes (overengineered).
3. **24 Agentes**: Consolidados en 8 componentes (reducción de overhead).
4. **Verbalizador Monolítico**: Reemplazado por Sintetizador multi-modelo.
5. **Router de Intenciones**: Sustituido por Detector de Huecos del Motor.

---

### I. LO QUE SE CONSERVA DEL CHIEF VIEJO Y POR QUÉ

1. **Estigmergia (Postgres)**: Comunicación asíncrona eficiente (0 LLM).
2. **Cola Priorizada**: Gestión inteligente de preguntas (código puro).
3. **Persistencia Inter-Sesión**: Memoria de usuario y decisiones (código puro).
4. **Detección de Contradicciones**: Integrada en Motor (código puro).
5. **Concepto Dual Rapido/Profundo**: Reimplementado con Motor (latencia mejorada).

---

### J. ESTIMACIÓN DE COSTE POR TURNO

| Componente               | Coste (USD) | Detalle                          |
|-------------------------|-------------|----------------------------------|
| Orquestador de Gaps     | $0.00       | Código puro                     |
| Router de Modelos       | $0.00       | Código puro                     |
| Ejecutor Multi-Modelo    | $0.015      | MiMo ($0.001) + Step3.5 ($0.019) |
| Sintetizador             | $0.005      | Cogito (selectivo, ~$0.15/100) |
| Agente de Actuación      | $0.00       | Código puro                     |
| Gestor de Persistencia   | $0.00       | Código puro                     |
| Optimizador de Coste     | $0.00       | Código puro                     |
| Detector de Contradicciones | $0.00    | Código puro                     |
| **Total**               | **$0.02**   | (Incluye margen de seguridad)  |

**Nota**: Coste profundo (~30s) puede variar entre $0.02-$0.05 dependiendo de celdas activas, pero se mantiene bajo $0.05 con modelos OS eficientes.

### EXP 7 — exp7_r1_step35

# R1 Design: Step 3.5 Flash
**Perspectiva:** Razonamiento -- que es logicamente necesario vs sobrediseno?

# Rediseño del Chief of Staff (CoS) — Arquitectura Basada en Evidencia Empírica

## A. Diagrama Arquitectónico Completo

```
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   +----------------+       +------------------+       +----------------+       +----------------+ |
|   |                |       |                  |       |                |       |                | |
|   |   USUARIO      |<----->|  ROUTER & QUEUE  |<----->|  MOTOR         |<----->|  AGENTE DE     | |
|   |                |       |   MANAGER        |       |  COGNITIVO     |       |  CODING        | |
|   +----------------+       +------------------+       +----------------+       +----------------+ |
|          ^                         |  ^                      |  ^                      |          |
|          |                         |  |                      |  |                      |          |
|          |                         v  |                      v  |                      v          |
|          |               +------------------+       +------------------+                     |
|          |               |  SISTEMA DE      |       |  SISTEMA DE      |                     |
|          +-------------->|  ESTIGMERGIA     |<------>|  PERSISTENCIA    |<--------------------+
|                          |  (Postgres)      |       |  (Postgres)      |                     |
|                          +------------------+       +------------------+                     |
|                                   ^                           ^                               |
|                                   |                           |                               |
|                          +------------------+       +------------------+                     |
|                          |  GESTOR DE LA    |       |  MODELOS OS      |                     |
|                          |  MATRIZ          |<------|  (DeepSeek,      |                     |
|                          |  (Externo)       |       |   R1, GPT-OSS,   |                     |
|                          +------------------+       |   MiMo, etc.)    |                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Leyenda**:
- Flechas: flujo de datos/control.
- Componentes en azul: lógicos del CoS (≤8).
- Componentes en gris: infraestructura/servicios externos.
- Comunicación: mayormente **estigmergia** (marcas en Postgres) excepto invocación directa Router→Motor y Motor→Agente de Coding.

---

## B. Componentes Lógicos (Máximo 8)

### 1. Router & Queue Manager
- **Qué hace**: 
  - Gestiona el ciclo de chat turno a turno.
  - En turno 0: genera pregunta de encuadre instantánea (código puro, 0 LLM).
  - En turnos 1+: actualiza cola priorizada, emite 2 preguntas por turno.
  - Dispara el Motor Cognitivo cuando la cola está vacía o hay gaps críticos.
  - Gestiona cierre de sesión (inactividad >2h) y compresión de memoria.
  - Lee/escribe marcas estigmergicas y persistencia.
- **Modelo**: **MiMo V2 Flash** ($0.001, ~100ms). Basado en EXP 1bis: modelo barato universal para tareas ligeras. Suficiente para generación de preguntas de emergencia y gestión de cola.
- **Herramientas**: 
  - Acceso a Postgres (lectura/escritura de tablas: `sesiones_chief`, `cola_emergencia`, `marcas_estigmergicas`).
  - Código puro para lógica de turnos y priorización.
- **Comunicación**:
  - Directa con Motor Cognitivo: llamada asincrónica (via `pg_net` o cola de tareas) para disparar análisis profundo.
  - Con Estigmergia: lee marcas de la sesión actual para contexto; escribe marcas de tipo `senal` (ej: "nueva_pregunta").
  - Con Persistencia: lee `perfil_usuario`, `decisiones_chief`; escribe actualizaciones de sesión.

### 2. Motor Cognitivo
- **Qué hace**: 
  - Ejecuta el pipeline de 7 pasos usando la Matriz 3Lx7F.
  - **Paso 0**: Detector de huecos completo (7 primitivas + 8 operaciones sintácticas).
  - **Paso 1**: Campo de gradientes (calcula gap por celda).
  - **Paso 2**: Routing por gradiente (selecciona top 3-5 INT por celda, basado en efectividad del Gestor).
  - **Paso 3**: Composición algebraica (NetworkX, 13 reglas duras).
  - **Paso 4**: Ensamblaje del prompt (preguntas compiladas por el Gestor como prompt interno).
  - **Paso 5**: Ejecución multi-modelo en paralelo (asigna modelos OS a INT según Gestor). Invoca Agente de Coding si la INT requiere acción.
  - **Paso 6**: Verificación de cierre (reintentos si gap >0.3).
  - **Paso 7**: Integración + verbalización (síntesis multi-modelo, extracción de decisiones, generación de marcas).
  - Produce lista de preguntas priorizadas para la cola.
- **Modelo**: **Multi-modelo** (asignación dinámica por celda/INT, según datos del Gestor). Ejemplos empíricos (EXP 4):
  - Celdas "Conservar"/"Frontera": **DeepSeek V3.1** (score 2.19, costo ~$0.001).
  - Celdas "Continuidad"/"FronteraxSentido": **DeepSeek R1** (score 2.18).
  - Celdas "Depurar"/"DistribuirxSentido": **GPT-OSS 120B** (score 2.15).
  - Integración N3/N45: **DeepSeek R1** o **R1** (buenos en trade-offs).
  - Tareas de código: **Devstral** (EXP 1bis: #1 patcher, $0.004).
  - Tareas de depuración: **Step 3.5 Flash** (EXP 1bis: debugger potente, $0.019).
- **Herramientas**:
  - NetworkX para composición.
  - Cliente API para modelos OS (via LiteLLM o similar).
  - Invocación a Agente de Coding (RPC interna).
  - Acceso a Postgres (lectura de Matriz, marcas, persistencia).
- **Comunicación**:
  - Con Router: recibe trigger, devuelve preguntas y marcas.
  - Con Gestor: solicita programa de preguntas compilado; reporta métricas (gap_pre, gap_post, tasa_cierre, INT usadas).
  - Con Agente de Coding: invoca tareas específicas.
  - Con Estigmergia: escribe marcas de `hallazgo`, `sintesis`, `decision`.
  - Con Persistencia: guarda decisiones extraídas, actualiza perfil.

### 3. Agente de Coding
- **Qué hace**:
  - Ejecuta tareas de codificación con loop observe->think->act.
  - Implementa, prueba, depura, revisa código.
  - Gestiona contexto (condenser), detecta stuck (5 escenarios), aplica budget enforcement.
  - Opera en sandbox aislado (Docker preferido, sino blacklist).
- **Modelo**: **Multi-modelo especializado**:
  - **Devstral** para implementación rápida (EXP 5b: 100% en T1 con Step).
  - **Step 3.5 Flash** para depuración (EXP 1bis: debugger potente).
  - Router interno: si la tarea es "escribir código", usa Devstral; si es "depurar error", usa Step.
- **Herramientas**:
  - Sandbox: Docker (con límites de recursos) o blacklist de comandos.
  - Herramientas: Bash, IPython, File editor, Browser, Think, Finish, Task tracker, Condensation, MCP (como OpenHands, EXP 6).
  - Condenser para gestión de contexto (sliding window + sumarización).
  - Timeout per command: 120s.
- **Comunicación**:
  - Invocado por Motor Cognitivo con tarea estructurada (JSON: descripción, archivos, expected output).
  - Devuelve resultado (código, logs, tests) al Motor.
  - Puede escribir marcas estigmergicas (ej: `codigo_generado`).

### 4. Sistema de Estigmergia (Infraestructura Compartida)
- **Qué hace**: 
  - Tabla `marcas_estigmergicas` en Postgres.
  - Tipos: `hallazgo`, `sintesis`, `alerta`, `triage`, `basal`, `prescripcion`, `verbalizacion`, `propuesta`, `meta`, `respuesta`, `senal`, `profundo_resultado`.
  - Todos los componentes escriben/leen marcas para coordinación sin acoplamiento.
  - Las marcas incluyen: `sesion_id`, `turno`, `tipo`, `contenido` (JSON), `timestamp`.
- **Modelo**: No aplica (infraestructura).
- **Herramientas**: Postgres (Supabase).
- **Comunicación**: 
  - Lectura/escritura directa por Router, Motor, Agente de Coding.
  - Coste: $0 (solo base de datos).

### 5. Sistema de Persistencia (Infraestructura Compartida)
- **Qué hace**:
  - Almacena datos inter-sesión:
    - `perfil_usuario`: patrones, sesgos, datos personales, confianza.
    - `decisiones_chief`: decisiones tomadas con contexto y alternativas.
    - `sesiones_chief`: metadata de sesiones (dominio, intención, turnos).
    - `cola_emergencia`: insights pendientes (TTL 24h).
  - El Router gestiona la cola activa en memoria, pero `cola_emergencia` es persistente.
- **Modelo**: No aplica.
- **Herramientas**: Postgres (Supabase).
- **Comunicación**: Lectura/escritura por Router y Motor.

### 6. Detector de Contradicciones (Subcomponente del Motor)
- **Qué hace**: 
  - Compara input actual con decisiones previas (`decisiones_chief`) para detectar contradicciones.
  - Implementa sandwich PRE->Haiku->POST? No, usa modelo OS ligero (MiMo V2 Flash) para eficiencia.
  - Inyecta alertas como marcas estigmergicas y ajusta gaps.
- **Modelo**: **MiMo V2 Flash** ($0.001). Suficiente para comparación semántica.
- **Herramientas**: Acceso a `decisiones_chief` y marcas.
- **Comunicación**: Integrado en Motor (Paso 0 o Paso 6). Escribe marcas `alerta`.

### 7. Compresor de Memoria (Función del Router)
- **Qué hace**: 
  - Al cerrar sesión (inactividad >2h), extrae decisiones, datos, patrones usando modelo ligero.
  - Actualiza `perfil_usuario` y `decisiones_chief`.
  - Elimina marcas consumidas (compactador).
- **Modelo**: **MiMo V2 Flash** ($0.001).
- **Herramientas**: Acceso a sesión, marcas, persistencia.
- **Comunicación**: Disparado por Router (cron-cierre-sesiones integrado).

### 8. Interfaz con Gestor de la Matriz (Componente de Integración)
- **Qué hace**:
  - Solicita al Gestor (servicio externo) el "programa de preguntas compilado" para el CoS (asignación modelo→celda/INT).
  - Reporta métricas de efectividad tras cada ejecución del Motor.
- **Modelo**: No aplica (cliente HTTP).
- **Herramientas**: API REST/GraphQL al Gestor.
- **Comunicación**: 
  - Motor → Gestor: GET programa, POST métricas.
  - Gestor → Motor: devuelve asignaciones.

---

## C. Flujo de un Turno de Chat (Paso a Paso)

1. **Usuario envía mensaje** en turno N.
2. **Router & Queue Manager** recibe mensaje.
3. **Si turno 0 (nueva sesión)**:
   - Genera pregunta de encuadre instantánea (código puro, ej: "¿Qué dominio principal abordamos hoy?").
   - Crea registro en `sesiones_chief`.
   - Emite pregunta al usuario.
   - **Fin de turno** (~500ms).
4. **Si turno ≥1**:
   - Lee contexto: `sesiones_chief`, `decisiones_chief`, `perfil_usuario`, marcas recientes.
   - **Actualiza cola**:
     - Para cada pregunta en cola (almacenada en memoria o `cola_emergencia`), usa MiMo V2 Flash para determinar si el input del usuario la responde (similitud semántica >80%). Si sí, marca como resuelta y elimina.
   - **Si hay preguntas en cola**:
     - Prioriza por: (1) antigüedad, (2) prioridad asignada por Motor, (3) relevancia a gaps actuales (si se tienen).
     - Emite top 2 preguntas.
     - **Fin de turno** (~200-500ms).
   - **Si cola vacía**:
     - Calcula gaps rápidos (Paso 0 ligero) con MiMo V2 Flash sobre input + contexto.
     - Si gaps >0.3 en alguna celda:
       * Dispara Motor Cognitivo asincrónicamente (via `pg_net`).
       * Genera 2 preguntas de emergencia con MiMo V2 Flash (prompt: "Basado en gaps [lista], genera 2 preguntas exploratorias").
       * Emite preguntas de emergencia.
     - Si no hay gaps:
       * Responde con conocimiento de `perfil_usuario`/`decisiones_chief` (MiMo V2 Flash para redacción).
     - **Fin de turno** (~

