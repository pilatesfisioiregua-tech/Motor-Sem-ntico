# PROMPT SIGUIENTE SESION — Fase 2: Ejecucion ACD

**Fecha:** 2026-03-20
**Sesion anterior:** Escribio briefings B-ACD-05 a B-ACD-08 (Fase 2 Diagnostico)
**Objetivo:** Ejecutar los 4 briefings de Fase 2

---

## ESTADO AL CERRAR

### Completados
- Fase 0 (Code OS rediseno): B-ACD-00 PASS 5/5
- Fase 1 (Datos): B-ACD-01 a B-ACD-04, todos PASS

### Briefings escritos, pendientes ejecucion
- B-ACD-05: `evaluador_funcional.py` + `openrouter_client.py` (V3.2 via OpenRouter, json_schema)
- B-ACD-06: `diagnostico.py` (clasificador 10 estados, codigo puro $0)
- B-ACD-07: `repertorio.py` (V3.2 via OpenRouter, json_schema, verificaciones IC)
- B-ACD-08: Extender `diagnostico.py` con DiagnosticoCompleto + diagnosticar() end-to-end

### Checklist maestra
- `motor-semantico/briefings/CHECKLIST_ACD.md` — leer primero

---

## QUE HACER EN ESTA SESION

### 1. Verificar prerequisito
```
OPENROUTER_API_KEY debe estar en .env del motor-semantico
Si no esta → añadirla antes de ejecutar
```

### 2. Ejecutar briefings en orden

**Paralelo (WIP=2):**
- B-ACD-05 (evaluador funcional + cliente OpenRouter)
- B-ACD-06 (clasificador estados — no usa LLM, independiente)

**Secuencial despues:**
- B-ACD-07 (repertorio — necesita openrouter_client.py de B-ACD-05)
- B-ACD-08 (end-to-end — necesita los 3 anteriores)

### 3. Verificar resultados

Cada briefing tiene pass/fail explicito. Si algo falla:
- Diagnosticar en chat
- Escribir fix como briefing adicional
- No improvisar dentro del briefing

---

## ARCHIVOS CLAVE

**Para ejecutar:**
- `briefings/B-ACD-05.md` (3 pasos: cliente OR + evaluador + test)
- `briefings/B-ACD-06.md` (2 pasos: diagnostico.py + 10 tests)
- `briefings/B-ACD-07.md` (2 pasos: repertorio.py + test LLM)
- `briefings/B-ACD-08.md` (2 pasos: extender diagnostico + test e2e)

**Para contexto:**
- `src/tcf/campo.py` — VectorFuncional, evaluar_campo()
- `src/tcf/constantes.py` — FUNCIONES, LENTES, VECTOR_PILATES
- `src/tcf/flags.py` — detectar_todos_flags()
- `src/tcf/estados.json` — 10 estados

**NO leer:**
- MAESTRO_V4.md (ya procesado)
- FRAMEWORK_ACD.md (ya procesado)
- agent_loop.py, mochila.py (ya rediseñados)

---

## DECISION TOMADA (CR1 de esta sesion)

Modelo para evaluacion funcional + repertorio: **DeepSeek V3.2** via OpenRouter.
- `response_format: json_schema` fuerza estructura exacta
- Response Healing como safety net (gratis)
- Coste estimado: ~$0.0015/diagnostico completo (2 calls V3.2)
- Variable de entorno: `MODEL_EXTRACTOR_OR` (default: `deepseek/deepseek-v3.2`)
