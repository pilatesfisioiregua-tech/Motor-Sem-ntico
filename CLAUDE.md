# MOTOR SEMÁNTICO OMNI-MIND — CLAUDE.md

## QUÉ ES

Un motor que recibe input en lenguaje natural y genera automáticamente el algoritmo óptimo de inteligencias para procesarlo. No tiene programas fijos — compila un programa nuevo para cada petición desde las primitivas de la Meta-Red (18 inteligencias, cada una es una red de preguntas).

```
INPUT:  "Mi socio quiere vender su parte y no sé si puedo comprársela"
MOTOR:  Router → [INT-07, INT-06, INT-08, INT-05]
        Compositor → INT-07→INT-06 → ∫(INT-08|INT-05)
        Ejecutor → ejecuta preguntas de cada inteligencia sobre el input
        Integrador → síntesis final
OUTPUT: Diagnóstico multi-inteligencia con hallazgos, firma combinada, puntos ciegos
```

## STACK

- **Runtime:** Python 3.12+
- **Framework:** FastAPI
- **DB:** fly.io Postgres con pgvector
- **Grafos:** NetworkX
- **LLM:** Anthropic API (Haiku para extracción, Sonnet para routing/integración)
- **Deploy:** fly.io
- **NO usar:** OpenAI, Supabase, Deno, Edge Functions

## ESTRUCTURA

```
motor-semantico/
├── fly.toml
├── Dockerfile
├── requirements.txt
├── CLAUDE.md
├── src/
│   ├── main.py                  # FastAPI server
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── orchestrator.py      # Orquesta las 7 capas
│   │   ├── detector_huecos.py   # Capa 0: detector de huecos (código puro, $0)
│   │   ├── router.py            # Capa 1: selección de inteligencias (Sonnet)
│   │   ├── compositor.py        # Capa 2: grafo + algoritmo (NetworkX)
│   │   ├── generador.py         # Capa 3: genera prompts desde Meta-Red
│   │   ├── ejecutor.py          # Capa 4: ejecuta prompts via Anthropic API
│   │   ├── evaluador.py         # Capa 5: scorer heurístico + detección falacias
│   │   └── integrador.py        # Capa 6: síntesis final (Sonnet)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.sql
│   │   ├── seed.sql
│   │   └── client.py            # asyncpg connection pool
│   ├── meta_red/
│   │   ├── __init__.py
│   │   ├── inteligencias.json   # 18 redes de preguntas (cargado en memoria al arrancar)
│   │   └── marco_linguistico.json # 8 ops, 9 capas, 6 acoples, falacias
│   ├── config/
│   │   ├── __init__.py
│   │   ├── reglas.py            # 13 reglas del compilador
│   │   ├── modelos.py           # Config LLM (keys, modelos, fallback)
│   │   └── settings.py          # Env vars, constantes
│   └── utils/
│       ├── __init__.py
│       └── llm_client.py        # Wrapper Anthropic con rotación de keys
├── tests/
│   ├── test_detector.py
│   ├── test_router.py
│   ├── test_compositor.py
│   └── test_pipeline_e2e.py
└── scripts/
    └── seed_db.py               # Poblar DB
```

## CONVENCIONES

- Python 3.12+, type hints obligatorios
- async/await para todo IO (DB, LLM calls)
- Logging estructurado con `structlog`
- Errores explícitos, no silenciosos
- Cada módulo tiene docstring de 1 línea explicando qué hace
- Tests con pytest + pytest-asyncio
- Variables de entorno para secrets (ANTHROPIC_API_KEY_1..4, DATABASE_URL)

## PIPELINE — 7 CAPAS

```
Capa 0: DETECTOR     → 7 primitivas + 8 ops sintácticas         (~200ms, $0, código puro)
Capa 1: ROUTER       → Sonnet selecciona 4-5 inteligencias     (~2-5s, ~$0.02-0.05)
Capa 2: COMPOSITOR   → NetworkX genera algoritmo óptimo         (~100ms, $0)
Capa 3: GENERADOR    → Templates → prompts exactos              (~50ms, $0)
Capa 4: EJECUTOR     → Haiku extrae, Sonnet integra             (30-120s, $0.30-0.80)
Capa 5: EVALUADOR    → Scorer heurístico + detección falacias   (~50ms, $0)
Capa 6: INTEGRADOR   → Sonnet síntesis final                    (10-20s, $0.10-0.20)
```

## CAPA 0 — DETECTOR DE HUECOS (código puro, $0)

Antes del router. Analiza el input con 7 primitivas sintácticas + 8 operaciones del Marco Lingüístico.
Detecta: qué falta en el input (verbos sin objeto, creencias sin evidencia, etc.)
Output: lista de huecos tipificados que informan al router sobre qué inteligencias activar.

Las 8 operaciones: Modificación, Predicación, Complementación, Transitividad, Subordinación, Cuantificación, Conexión, Transformación.

## 6 MODOS CONCEPTUALES (Inteligencia × Pensamiento × Modo)

| Modo | Descripción | Inteligencias naturales |
|------|-------------|------------------------|
| ANALIZAR | Descomponer, demostrar, medir | INT-01, INT-02, INT-07 |
| PERCIBIR | Ver patrones, detectar forma | INT-03, INT-04, INT-15 |
| MOVER | Actuar, posicionar, construir | INT-05, INT-16, INT-10 |
| SENTIR | Empatizar, intuir, habitar | INT-08, INT-10, INT-18 |
| GENERAR | Crear, imaginar, proyectar | INT-14, INT-12, INT-13 |
| ENMARCAR | Nombrar, negociar, dar sentido | INT-09, INT-06, INT-17 |

Estos coexisten con los 4 modos API (análisis, generación, conversación, confrontación) que son configuraciones del pipeline.

## 13 REGLAS DEL COMPILADOR (OBLIGATORIAS)

1. **Núcleo irreducible:** Siempre ≥1 de {INT-01,INT-02} + ≥1 de {INT-08,INT-17} + INT-16
2. **Máximo diferencial:** Priorizar pares cuantitativo-existencial
3. **Sweet spot:** 4-5 inteligencias. <3 = puntos ciegos. >6 = rendimiento decreciente
4. **Formal primero:** En composiciones, formal/distante primero → humano/cercano después
5. **No reorganizar:** Secuencia lineal (A→B)→C supera agrupada A→(B→C)
6. **Fusiones con cuidado:** Orden afecta framing. Primero la más alineada con el sujeto
7. **Loop test siempre:** 2 pasadas por defecto en modo análisis/confrontación
8. **No tercera pasada:** n=3 no justifica coste excepto calibración
9. **Fusiones paralelizables ~70%:** Factorizar A→(B|C) pierde ~30%. Aceptable si no TOP 5
10. **Cruce previo NO factorizable:** (B|C)→A siempre junto. Valor irreducible
11. **Marco binario universal:** Primera acción = INT-14 (ampliar) + INT-01 (filtrar)
12. **Conversación pendiente universal:** Buscar este patrón como output mínimo
13. **Infrautilización antes de expansión:** Medir uso actual antes de construir nuevo

## 4 MODOS

| Modo | Inteligencias | Profundidad | Latencia |
|------|---------------|-------------|----------|
| análisis | 4-5, máx diferencial | 2 pasadas | <150s |
| generación | creativas (INT-14,15,09) | 1 pasada | <90s |
| conversación | 2-3, routing rápido | 1 pasada | <60s |
| confrontación | frontera (INT-17,18) | 2 pasadas | <120s |

## API

```
POST /motor/ejecutar
GET  /health
```

## RESTRICCIONES

- Coste máximo por ejecución: $1.50
- 4 API keys Anthropic rotativas
- Presupuesto testing: ~€150
- Haiku para extracción, Sonnet para routing/integración, Opus solo si frontera

## BRIEFINGS DE IMPLEMENTACIÓN

Los briefings están en `briefings/` y se ejecutan en orden secuencial. Cada uno es autónomo.

```
ORDEN:
1. briefings/BRIEFING_00_SCAFFOLD.md   → Estructura, deps, Docker, fly.toml, settings, llm_client, main.py
2. briefings/BRIEFING_01_DATOS.md      → Schema SQL, seed, inteligencias.json, marco_linguistico.json, db client
3. briefings/BRIEFING_02_PIPELINE_1_3.md → Detector Huecos, Router, Compositor, Generador
4. briefings/BRIEFING_03_PIPELINE_4_6.md → Ejecutor, Evaluador, Integrador, Orquestador
5. briefings/BRIEFING_04_DEPLOY_TESTS.md → fly.io deploy, tests E2E
```

REGLAS:
- Lee el briefing completo ANTES de escribir código
- Cada briefing tiene sección VERIFICACIÓN al final — ejecútala antes de pasar al siguiente
- Las 18 redes de preguntas completas para inteligencias.json están en el documento PROMPT_MVP.md (raíz del repo)
- No inventar datos. Copiar literal del briefing y del PROMPT_MVP.md
- Si un briefing falla verificación, arréglalo antes de avanzar
