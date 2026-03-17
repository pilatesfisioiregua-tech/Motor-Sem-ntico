**BRIEFING PARA AUDITOR: PRAGMATISMO Y COSTE (Nemotron Super)**
**Fecha:** 2026-03-12
**Auditor:** Nemotron Super (perspectiva coste/beneficio, implementación inmediata)
**Estado:** CR0 — Jesús valida y cierra

---

## 1. RESUMEN EJECUTIVO PARA EL AUDITOR

El sistema OMNI-MIND v4 está diseñado para operar con un **stack 100% Open Source (OS-first)**. La dependencia de proveedores premium (Anthropic) se elimina progresivamente. 

**Datos críticos de coste:**
- **Coste actual del sistema nervioso (Supabase):** ~$14/mes (€200 presupuesto total, sobran €186).
- **Coste objetivo por turno de chat:** <$0.02 (vs $0.10 del sistema anterior).
- **Reducción de coste:** 82% respecto a v1 mediante uso de modelos OS (MiMo V2 Flash $0.001, Devstral $0.004, Step 3.5 $0.019).
- **Infraestructura:** Migración completa a fly.io (Postgres + pgvector), deprecando Supabase progresivamente.

**Qué se puede implementar HOY:**
1. **Motor vN MVP** en fly.io con multi-modelo OS validado (V3.1, R1, GPT-OSS superan a Claude en la Matriz).
2. **Gestor de la Matriz** con tabla de efectividad y vista materializada (feedback loop de coste cero).
3. **Migración OS Fase 1:** ~30 agentes internos (parseadores, lentes, mejora continua) migrados a modelos OS vía llm-proxy multi-provider.
4. **Enjambre de código:** Pipeline de auto-mejora con Devstral + Step 3.5 Flash (coste ~$0.03 por tarea).

**Qué es código puro ($0) vs LLM:**
- **Código puro:** Detector de huecos (7 primitivas), campo de gradientes, composición algebraica (NetworkX), routing por gradiente, verificación de cierre, estigmergia (Postgres), telemetría, propiocepción.
- **LLM (OS):** Ejecución de preguntas por celda (MiMo, V3.1, R1, GPT-OSS), síntesis final (Cogito selectivo), debugging (Step 3.5).
- **LLM (Premium):** Solo evaluador de referencia (Sonnet) hasta correlación >0.85 con OS.

---

## 2. INFRAESTRUCTURA Y COSTES REALES (§8 + CONTEXTO_SISTEMA)

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

### Migración OS del Sistema Nervioso (§8B)

**Principio:** El Sistema Nervioso actual (Supabase) usa Haiku y Sonnet de Anthropic para ~53 agentes LLM. La mayoría hacen trabajo interno que el usuario nunca ve: clasificación, detección, extracción, correlación. Solo 2-3 agentes producen output que el usuario lee directamente (verbalizadores).

**Regla:** Si el usuario no lee el output, migra a OS.

**Mecanismo de migración:** llm-proxy multi-provider (un solo punto de cambio).

**Resumen de impacto:**

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

---

## 3. MAPA DE MODELOS Y PRECIOS (MAPA_MODELOS + EXP 1BIS)

### Leaderboard General (febrero-marzo 2026)

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

### Precios Reales (EXP 1BIS)

**Coste Total Exp 1bis:**
- Tokens input: 13,781
- Tokens output: 98,240
- **Coste total: $0.102**

| Modelo | Coste Aprox | Score Medio | Uso Recomendado |
|--------|-------------|-------------|-----------------|
| MiMo-V2-Flash | $0.001 | 0.90 | Tier barato universal, fontanería |
| Devstral | $0.004 | 0.86 | Patcher, implementación rápida |
| Nemotron Super | $0.007 | 0.96 | Math/Validación numérica |
| Step-3.5-Flash | $0.019 | 0.98 | Debugger, razonamiento profundo |
| Qwen 3.5 397B | $0.033 | 0.85 | Evaluador |
| Kimi K2.5 | $0.038 | 0.86 | Pizarra (agent swarm) |

---

## 4. RESULTADOS EXPERIMENTALES COMPLETOS (COSTES REALES)

### EXP 4 — Mesa Redonda (12 modelos, 2 rondas)

**Coste estimado:** ~$0.50-1.00 (12 modelos × 5 outputs = 60 llamadas).

**Ranking de Aporte (Valor = contribuciones únicas):**

| # | Modelo | Valor | R1 medio | R2 medio | 3+ R1 | 3+ R2 |
|---|--------|-------|----------|----------|-------|-------|
| 1 | gpt-oss-120b | 118 | 1.26 | 2.74 | 14 | 66 |
| 2 | qwen3-235b | 98 | 2.54 | 3.19 | 58 | 87 |
| 3 | opus | 90 | 1.50 | 2.77 | 19 | 67 |
| 4 | v3.2-chat | 79 | 1.54 | 2.86 | 7 | 76 |
| 5 | deepseek-v3.1 | 55 | 1.66 | 2.80 | 10 | 74 |
| 6 | glm-4.7 | 45 | 1.81 | 2.42 | 15 | 54 |
| 7 | cogito-671b | 42 | 1.52 | 2.88 | 6 | 77 |
| 8 | kimi-k2.5 | 30 | 2.06 | 2.47 | 28 | 48 |
| 9 | deepseek-r1 | 0 | 1.57 | 1.57 | 12 | 12 |
| 10 | minimax-m2.5 | 0 | 1.60 | 1.79 | 14 | 17 |
| 11 | sonnet | 0 | 2.00 | 2.00 | 32 | 32 |
| 12 | v3.2-reasoner | 0 | 1.42 | 1.42 | 9 | 9 |

**Hallazgo crítico:** 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). R1 cubre 20/21 celdas — la mayor cobertura de todos.

**Mesa mínima óptima:** 2 modelos (gpt-oss-120b + qwen3-235b) capturan 94.6% del valor.

### EXP 5 — Cadena de Montaje (40 runs)

**Coste real:** $0.3267 (Config A — Línea Industrial).

| Config | Nombre | Pass Rate | Coste Total | Coste/Task |
|--------|--------|-----------|-------------|------------|
| A | Linea Industrial | 56% | $0.327 | $0.065 |
| B | Coder Puro | 37% | $0.136 | $0.027 |
| C | Maxima Diversidad | 17% | $0.249 | $0.050 |
| D | Ultra-Barato | 51% | $0.047 | $0.009 |
| E | Premium | 15% | $0.343 | $0.069 |
| F | Cadena Minima | 18% | $0.119 | $0.024 |
| G | Razonadores | 33% | $0.191 | $0.038 |
| 0 | Baseline | 32% | $0.033 | $0.007 |

**Veredicto:** La cadena de montaje supera al modelo solo en +24% (56% vs 32%), pero no alcanza el umbral del 90% requerido para reemplazar completamente a Code. Sin embargo, para tareas específicas (T2, T3) alcanza 94-100%.

### EXP 5b — Nuevos Modelos en Pipeline Multi-Estación

**Coste real:** $0.18 (277K tokens).

| Config | Modelos | T1 | T4 | Coste Aprox |
|--------|---------|----|----|-------------|
| N1_top | step-3.5 + qwen-3.5-397b | 20% | E1 vacío | $0.08 |
| N2_cheap | mimo-v2 + nemotron + step-3.5 | **100%** | 0% | $0.04 |
| N3_coding | step-3.5 + devstral | **100%** | E1 vacío | $0.03 |

**Insight:** MiMo V2 Flash + Step 3.5 Flash resuelven T1 (Edge Function TS) al 100% por $0.03. El problema de T4 (Orquestador Python async) es el "think-tag blow-up" de Step 3.5 Flash, no el coste.

### EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas

**Coste real:** $0.102.

| Modelo | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|----|----|----|----|----|-------|-------|
| step-3.5-flash | 1.00 | 0.89 | 1.00 | 1.00 | 1.00 | 0.98 | $0.019 |
| nemotron-super | 1.00 | 0.88 | 1.00 | 0.90 | 1.00 | 0.96 | $0.007 |
| mimo-v2-flash | 1.00 | 0.89 | 0.60 | 1.00 | 1.00 | 0.90 | $0.001 |
| kimi-k2.5 | 0.81 | 0.89 | 0.80 | 0.80 | 1.00 | 0.86 | $0.038 |
| devstral | 1.00 | 0.50 | 0.80 | 1.00 | 1.00 | 0.86 | $0.004 |
| qwen3.5-397b | 0.59 | 0.88 | 0.80 | 1.00 | 1.00 | 0.85 | $0.033 |

**Recomendaciones por rol:**
- **Debugger/Razonador:** Step 3.5 Flash ($0.019)
- **Math/Validación:** Nemotron Super ($0.007)
- **Tier barato universal:** MiMo V2 Flash ($0.001)
- **Patcher:** Devstral ($0.004)

### EXP 6 — OpenHands (Análisis de Infraestructura)

Relevante para costes de infraestructura de agentes:
- **Max iteraciones:** 500 (configurable)
- **Timeout per-command:** 120s
- **Loop:** observe→think→act (event-driven)
- **Sandbox:** Docker isolation (o blacklist sin Docker)
- **Coste:** LiteLLM abstrae providers, unifica billing

### EXP 7 — Diseños Alternativos (Costes por Turno)

**Diseño Cogito (Síntesis):**
- Turno superficial: ~$0.015 (MiMo V2 + V3.2)
- Turno profundo: ~$0.038 (Step 3.5) → ajustado a $0.027 con V3.1
- **Promedio real:** $0.0174/turno (82% reducción vs $0.10 anterior)

**Diseño DeepSeek (Arquitectura):**
- Turno superficial: ~$0.015
- Turno profundo: ~$0.027
- **Promedio:** $0.0174/turno

**Diseño Kimi (Enjambre):**
- Turno superficial: ~$0.015
- Turno profundo selectivo: $0.10 (solo casos críticos)
- **Promedio ponderado:** $0.0174/turno

**Diseño Nematron (Coste/Eficiencia):**
- Turno superficial: $0.015
- Turno profundo: $0.027
- **Promedio:** $0.0174/turno

---

## 5. ROADMAP DE IMPLEMENTACIÓN (§11)

### Ola 1 — Ahora (paralelo)
- **Gestor de la Matriz** — tabla de efectividad + vista materializada + compilador de programas
- **Motor vN MVP en fly.io** — pipeline end-to-end que USA la Matriz via Gestor
- **Migración OS Fase 1** — llm-proxy multi-provider + migrar ~30 agentes 🟢 (primitivas, parseadores, lentes, mejora continua)
- **Reactor v3 conceptual** — poblar Matriz con preguntas desde fundamentos teóricos (~$10-18)

### Ola 2 — Motor funcional + primeros pilotos reales
- Test evaluador OS vs Sonnet (objetivo: correlación >0.85 → migrar a OS)
- **Migración OS Fase 2** — testear ~12 agentes 🟡 con OS vs Anthropic en 10 inputs reales
- **Integrar enjambre de código** en pipeline de auto-mejora (V3.2+Qwen Coder+Cogito+V3.1)
- **PILOTO 1: Exocortex Pilates** (estudio de Jesús) — primer consumidor real del Gestor
- **PILOTO 2: Exocortex Fisioterapia** (clínica de la mujer de Jesús) — segundo dominio

### Ola 3 — Retroalimentación + autonomía
- Datos reales de ambos pilotos refinan la Matriz via Gestor (feedback transversal)
- **Reactor v4 activo** — telemetría genera preguntas desde datos reales de operación
- **Flywheel validado** — Pilates y Fisio se enriquecen mutuamente via la Matriz
- **Prompts vivos** — los agentes evolucionan con el negocio sin intervención manual
- **Migración OS Fase 3** — evaluar verbalizadores con OS. Si pasan → stack 100% OS
- **Auto-mejora nivel 2 activa** — el sistema propone + implementa mejoras arquitecturales, CR1 aprueba

### Ola 4 — Escala: caso de negocio real con terceros
- **Con datos reales de Piloto 1 y 2**, presentar resultados al amigo informático
- **Integración con software de gestión del amigo** — capa de telemetría que lee datos del software existente via API
- **Fábrica de Exocortex** para generar conectores por tipo de software
- **Modelo de negocio**: capa inteligente a €50-200/mes por negocio, coste ~$2-5/mes en tokens, margen >90%

---

## 6. PRESUPUESTOS DETALLADOS (§14 v1 + Contexto Real)

### Coste API (Anthropic + Voyage) — Estimación v1

```
FASE A — CARTOGRAFÍA
  Ejecución en claude.ai Pro:                    €0
  Tu tiempo: ~12-15 horas
  COSTE API: €0

FASE B — DATOS SINTÉTICOS
  3 rondas generación + validación:              €60
  Enriquecimiento con fuentes externas:          €20
  Generación preguntas nivel 2 (18 INTs):        €30
  Generación preguntas nivel 3 (10 INTs):        €25
  Validación cruzada (Opus revisa Opus):         €15
  COSTE API: ~€150

FASE C — ENTRENAMIENTO
  Fine-tune embeddings Voyage:                   €5
  Computación (local o fly.io):                  €0
  3 ciclos entrenamiento + evaluación:           €5
  COSTE API: ~€10

FASE D — MOTOR v1
  Desarrollo (Code CLI):                         €0
  Testing pipeline (~100 ejecuciones):           €100-150
  Debugging + re-ejecuciones:                    €50
  COSTE API: ~€150-200

FASE E — CHAT / EXOCORTEX
  Desarrollo:                                    €0
  Testing conversacional (~200 turnos):          €50-80
  Testing capa profunda:                         €30
  COSTE API: ~€80-110

FASE F — PILOTOS (primeros 3 meses)
  Ejecuciones reales (~30/día × 90 días):        €200-400
  Re-entrenamiento con datos reales:             €20
  Cartografía parcial dominios nuevos:           €30
  COSTE API: ~€250-450
```

### Totales acumulados v1

```
Hasta Motor funcionando (A-D):      ~€310-360
Hasta Chat funcionando (A-E):       ~€390-470
Con 3 meses de pilotos (A-F):       ~€640-920
```

### Distribución óptima con presupuesto fijo (€500)

```
CON €500:
  €0    Fase A (gratis en claude.ai Pro)
  €100  Fase B (2 rondas + fuentes externas)
  €10   Fase C (entrenamiento)
  €150  Fase D (testing motor)
  €80   Fase E (testing chat)
  €160  Fase F (pilotos — ~2 meses a volumen medio)

CON €1.000:
  €0    Fase A
  €150  Fase B (3 rondas completas + nivel 2-3)
  €10   Fase C
  €200  Fase D (testing exhaustivo)
  €110  Fase E (testing completo)
  €530  Fase F (pilotos — ~4-5 meses a volumen alto)
```

### Coste recurrente post-lanzamiento (Real)

```
Ejecuciones del motor:  ~€1/ejecución × volumen
  10/día = ~€300/mes
  30/día = ~€900/mes
  
Re-entrenamiento mensual: ~€20/mes
Cartografía nuevos dominios: ~€30/dominio (puntual)
```

**Nota:** El coste real actual del sistema nervioso es ~$14/mes (€13), muy por debajo del presupuesto de €200/mes.

---

## 7. DECISIONES CR0 PENDIENTES (Acciones Inmediatas)

1. **Aprobar migración a fly.io:** Cancelar upgrade de Supabase (402), migrar 99 Edge Functions a fly.io progresivamente.
2. **Aprobar stack OS-first:** Validar que Nemotron Super + MiMo V2 Flash + Step 3.5 Flash cubren el 90% de casos a <$0.02/turno.
3. **Aprobar deprecación Chief of Staff:** Reemplazar por Motor v3.3 + Matriz (ahorro de ~$10/mes en agentes legacy).
4. **Aprobar pilotos reales:** Pilates + Fisioterapia con telemetría activa (coste ~$5/mes por piloto).
5. **Aprobar Fábrica de Exocortex:** Permitir al sistema generar nuevos exocortex autónomamente (coste ~$0.50-2 por exocortex, margen >90%).

---

**FIN DEL BRIEFING**