# EXP 7 — Model Discovery Report

Fecha: 2026-03-11

## Modelos verificados en OpenRouter

| Modelo | ID OpenRouter | $/M out | $/M in | Ctx | Resp. time | Status |
|--------|--------------|---------|--------|-----|------------|--------|
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | $0.38 | $0.26 | 163K | 2.0s | OK |
| Devstral Small | `mistralai/devstral-small` | $0.30 | $0.10 | 131K | 0.6s | OK |
| KAT-Coder-Pro | `kwaipilot/kat-coder-pro` | $0.83 | $0.21 | 256K | 2.5s | OK |
| Qwen3 Coder Next | `qwen/qwen3-coder-next` | $0.75 | $0.12 | 262K | 0.8s | OK |
| GLM-4.7 | `z-ai/glm-4.7` | $1.98 | $0.38 | 202K | timeout | TIMEOUT |
| GLM-4.7 Flash | `z-ai/glm-4.7-flash` | $0.40 | $0.06 | 202K | 2.9s | PARSE_ERROR |

## Bonus models found

| Modelo | ID | $/M out | Nota |
|--------|-----|---------|------|
| GLM-5 | `z-ai/glm-5` | $2.30 | Newest GLM |
| GLM-4.5 Air | `z-ai/glm-4.5-air` | $0.85 | Mid-tier |
| Qwen3 Coder (free) | `qwen/qwen3-coder:free` | $0 | Free tier |
| Qwen3 Coder Flash | `qwen/qwen3-coder-flash` | $0.975 | 1M context |
| Grok Code Fast 1 | `x-ai/grok-code-fast-1` | $1.50 | Agent-designed |
| DeepSeek V3.1 | `deepseek/deepseek-chat-v3.1` | $0.75 | Previous gen |
| Devstral Medium | `mistralai/devstral-medium` | $2.00 | Same as devstral-2512 |

## Tier assignment for Code OS

| Tier | Modelo | Precio | Latencia | Rol |
|------|--------|--------|----------|-----|
| **Tier 1** (fast/cheap) | Devstral Small | $0.30/M | 0.6s | Generar código |
| **Tier 2** (strong/cheap) | DeepSeek V3.2 | $0.38/M | 2.0s | Debug/escalado |
| **Tier 2b** (fallback) | Qwen3 Coder Next | $0.75/M | 0.8s | Fallback |
| **Tier 3** (proven) | Devstral 2512 | $2.00/M | 4-10s | Tareas complejas (T4) |
| **Vision** | DeepSeek V3.2 | $0.38/M | 2.0s | Entender + briefings |

## Smoke test results

### Test: Fibonacci (simple task)
- Model: Devstral Small (Tier 1)
- Result: DONE, 9 iterations, $0.013, 23s
- Tools used: plan → write_file → edit_file → run_command → finish

### Test: Vision mode (non-technical → briefing → code)
- Input: "Quiero que el motor tenga un endpoint que dado un texto me diga qué inteligencias necesita"
- Translation: "Create a FastAPI endpoint that receives natural language text and returns which of the 18 Meta-Red intelligences are needed"
- Briefing: Generated BRIEFING_06 with 3 modules, 5 steps
- Result: MAX_ITERATIONS (needed 25, had 15), $0.04, 28s
- Created: router.py, inteligencias.py, main.py, test_router.py

## Comparación con Exp 6

| Métrica | Exp 6 Devstral | Code OS Devstral Small |
|---------|---------------|----------------------|
| Precio modelo | $2.00/M | $0.30/M (6.7x más barato) |
| Fibonacci task | N/A | DONE, 9 iter, $0.013 |
| Tools disponibles | 5 + finish | 9 + finish |
| Context loading | No | Sí (CLAUDE.md + estructura) |
| Briefing generation | No | Sí |
| Supabase logging | No | Sí |
