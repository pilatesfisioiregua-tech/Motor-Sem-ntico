# Análisis: Validación Modelos Post-B06

## Fecha: 2026-03-18
## Estado: DECISIÓN PENDIENTE (CR0 — propuesta)

## Hallazgos

### Test original (key muerta → 401)
- Ejecutado ~00:15 UTC
- 4/4 "fail" → pero por API_FAILURE, no por capacidad del modelo
- Diagnóstico del test script incorrecto: culpaba al modelo, era la API key

### Test real (key funcional → modelos responden)
- Ejecutado ~00:33 UTC
- **0/4 passed** — ahora sí es un problema de capacidad

### Desglose por modelo

| Modelo | Slug OpenRouter | Rol | Tests | Resultado |
|--------|----------------|-----|-------|-----------|
| Qwen3-Coder 480B-A35B | `qwen/qwen3-coder` | cerebro | T1,T2,T4 | 0/3 |
| MiniMax M2.5 | `minimax/minimax-m2.5` | worker (execute mode) | T3 | 0/1 |
| DeepSeek V3.2 | `deepseek/deepseek-v3.2` | worker_budget (fallback) | N/A | No testeado solo |
| GLM-5 | `z-ai/glm-5` | evaluador | N/A | No testeado solo |

### Patrones de fallo

1. **Qwen3-Coder → monólogo loop**: El modelo "piensa en voz alta" sin usar tools.
   StuckDetector lo detecta (3x monologue) pero el modelo no aprende del nudge.
   - T1: 13 iters, 7 errores → STUCK
   - T2: 7 iters, 3 errores → lee pero no extrae
   - T4: 11 iters, 1 error → ejecuta HTTP pero no sintetiza

2. **MiniMax M2.5 → tool spam sin acción**: Ejecuta 17 tool calls pero 0 edits.
   El modelo llama herramientas de lectura/exploración infinitamente sin actuar.
   - T3: 17 iters, 2 errores → 0 edit_file calls

3. **Ambos modelos luchan con 61 tools**: El schema de herramientas es enorme.
   Posible que los modelos no prioricen las herramientas correctas.

### Diagnóstico de conectividad (herramienta creada)

`briefings/diag_conectividad_modelos.py` — test de 3 fases:
- Fase 1: OpenRouter directo (sin Code OS) → aisla API vs modelo
- Fase 2: Cerebro con tool_call → verifica function calling
- Fase 3: Code OS end-to-end → verifica integración

Resultado: API key local `...6621603b` estaba muerta (HTTP 401).
fly.io tenía key diferente y funcional.

## Propuesta (CR0)

**Revertir a Devstral 2 como cerebro Y worker (unified).**

Razones:
1. Devstral 2 validado al 100% previamente en este mismo stack
2. 123B dense, 256K context, diseñado para agentic coding
3. Más barato: $0.40/$2.00 vs $1.00 de Qwen3-Coder
4. El split cerebro/worker falló — MiniMax como worker no completa
5. Modelo unificado simplifica el routing

Briefing: `briefings/BRIEFING_07_cambio_cerebro.md`

## Artefactos creados

- `briefings/diag_conectividad_modelos.py` — diagnóstico de conectividad
- `briefings/BRIEFING_07_cambio_cerebro.md` — briefing para cambio de cerebro
- `results/analisis_validacion_modelos_b06.md` — este documento
