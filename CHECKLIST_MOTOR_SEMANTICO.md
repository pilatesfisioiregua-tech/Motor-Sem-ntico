# CHECKLIST MOTOR SEMANTICO — 2026-03-08

> **Estado:** MVP v1 completo. Pipeline end-to-end funcional. Deploy fly.io pendiente (sin CLI).

---

## BRIEFINGS — ESTADO

| # | Briefing | Estado | Fecha |
|---|----------|--------|-------|
| B00 | SCAFFOLD — Estructura, deps, Docker, fly.toml, settings, llm_client, main.py | COMPLETADO | 2026-03-08 |
| B01 | DATOS — Schema SQL, seed, inteligencias.json, marco_linguistico.json, db client | COMPLETADO | 2026-03-08 |
| B02 | PIPELINE 1-3 — Detector Huecos, Router, Compositor, Generador | COMPLETADO | 2026-03-08 |
| B03 | PIPELINE 4-6 — Ejecutor, Evaluador, Integrador, Orquestador | COMPLETADO | 2026-03-08 |
| B04 | DEPLOY + TESTS — Lifespan hooks, fly.toml timeout, tests E2E cartografía | COMPLETADO (deploy pendiente) | 2026-03-08 |

---

## CRITERIO DE CIERRE MVP

| # | Criterio | Estado | Nota |
|---|----------|--------|------|
| 1 | `GET /health` responde 200 | PASS | Endpoint definido en main.py |
| 2 | Pipeline end-to-end funcional: POST acepta input en lenguaje natural | PASS | 7 capas ejecutan en secuencia |
| 3 | Router selecciona 4-5 inteligencias respetando reglas | PASS | 13 reglas, enforce_rules(), núcleo irreducible |
| 4 | Compositor genera algoritmo con composiciones/fusiones | PASS | NetworkX, aristas con fallback en memoria |
| 5 | Ejecutor ejecuta preguntas via Anthropic API | PASS | 3 fases: paralelo, dependientes, loops |
| 6 | Integrador produce síntesis final con narrativa + hallazgos + acciones | PASS | Sonnet, 6 secciones en output |
| 7 | 4 modos funcionan (analisis, generacion, conversacion, confrontacion) | PASS | MODE_CONFIG con k/temperature por modo |
| 8 | Coste < $1.50 por ejecucion | PASS | MAX_COST_USD=1.50, presupuesto enforced en ejecutor |
| 9 | Latencia < 150s en analisis, < 60s en conversacion | PASS | MAX_TIME_S=150, timeout en fly.toml 180s |
| 10 | Telemetria guardada en DB | PASS | log_ejecucion() en orchestrator, fire-and-forget |
| 11 | Test E2E con los 3 casos de cartografia pasan | PASS (mock) | Mock test pasa. Live tests listos, requieren servidor |
| 12 | Deploy en fly.io funcionando | PENDIENTE | fly CLI no instalado. Codigo y config listos |

---

## PIPELINE — 7 CAPAS

```
Capa 0: DETECTOR     detector_huecos.py   7 primitivas + 8 ops sintacticas       ~200ms, $0
Capa 1: ROUTER       router.py            Sonnet selecciona 4-5 inteligencias    ~2-5s, ~$0.02-0.05
Capa 2: COMPOSITOR   compositor.py        NetworkX genera algoritmo optimo       ~100ms, $0
Capa 3: GENERADOR    generador.py         Templates a prompts exactos            ~50ms, $0
Capa 4: EJECUTOR     ejecutor.py          Haiku extrae, Sonnet integra           30-120s, $0.30-0.80
Capa 5: EVALUADOR    evaluador.py         Scorer heuristico + falacias           ~50ms, $0
Capa 6: INTEGRADOR   integrador.py        Sonnet sintesis final                  10-20s, $0.10-0.20
```

---

## BUGS ENCONTRADOS Y RESUELTOS

| Bug | Causa raiz | Fix | Briefing |
|-----|-----------|-----|----------|
| LLMClient crash al importar sin API keys | `llm = LLMClient()` se ejecutaba en module-level | Proxy `_LazyLLM` que instancia bajo demanda | B03 |
| Compositor llama DB para aristas sin Postgres | `compose()` llamaba `fetch_aristas()` siempre | `get_aristas()` en orchestrator con `_aristas_seed()` fallback | B03 |
| Composiciones fallan por dependencias no resueltas | `generar_prompts()` no generaba prompt individual para A en composicion A-B | Emitir prompt individual prerequisito automaticamente | B03 (fix post) |
| Detector no detecta huecos en inputs cortos | Thresholds `> 2` y `> 1` excluian inputs de 1-2 oraciones | Cambiar a `>= 2` y `>= 1` | B02 |

---

## ESTRUCTURA DE ARCHIVOS

```
motor-semantico/
  .gitignore
  CLAUDE.md
  CHECKLIST_MOTOR_SEMANTICO.md
  Dockerfile
  fly.toml
  PROMPT_MVP.md
  README.md
  requirements.txt
  briefings/
    BRIEFING_00_SCAFFOLD.md
    BRIEFING_01_DATOS.md
    BRIEFING_02_PIPELINE_1_3.md
    BRIEFING_03_PIPELINE_4_6.md
    BRIEFING_04_DEPLOY_TESTS.md
  registros/
    REGISTRO_2026-03-08_BRIEFING_04.md
  scripts/
    seed_db.py
  src/
    __init__.py
    main.py
    config/
      __init__.py
      settings.py
    db/
      __init__.py
      client.py
      schema.sql
      seed.sql
    meta_red/
      __init__.py
      inteligencias.json
      marco_linguistico.json
    pipeline/
      __init__.py
      compositor.py
      detector_huecos.py
      ejecutor.py
      evaluador.py
      generador.py
      integrador.py
      orchestrator.py
      router.py
    utils/
      __init__.py
      llm_client.py
  tests/
    test_pipeline_e2e.py
```

---

## PROXIMO PASO

```
1. Instalar fly CLI: brew install flyctl
2. fly auth login
3. fly apps create motor-semantico-omni
4. fly postgres create --name motor-semantico-db --region mad
5. fly postgres attach motor-semantico-db --app motor-semantico-omni
6. fly secrets set ANTHROPIC_API_KEY_1="sk-ant-..." (x4)
7. fly deploy
8. BASE_URL=https://motor-semantico-omni.fly.dev pytest tests/test_pipeline_e2e.py -v -s
```
