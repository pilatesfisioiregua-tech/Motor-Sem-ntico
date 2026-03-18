# Prompt para siguiente sesión — Post B26 (4/4 PASS)

## Estado: Code OS validation tests 4/4 PASS

### Hito alcanzado
B26 cerró T3 — los 4 tests de validación de modelos pasan. Code OS puede:
- T1: Consultar DB (cache hit)
- T2: Listar archivos (cache hit)
- T3: Crear endpoint GET /test/ping en api.py (8 iters, 12.8s, 0 errors)
- T4: Analizar código y extraer keywords (9 iters, 5/6 keywords)

### Stack validado
- Cerebro/worker/orchestrator: `mistralai/devstral-2512`
- Worker budget: `deepseek/deepseek-v3.2`
- Evaluador/synthesis: `z-ai/glm-5`

### Principios confirmados esta sesión (B18→B26)
- **P36 (CR1)**: Verificar goal real antes de cambiar modelos
- Loop > modelo: el agentic loop con fixes deterministas (path correction, finish force, tool enforcement) resolvió T3 sin cambiar modelo
- SSE args bug ocultaba progreso — siempre verificar harness antes de culpar al modelo

---

## Prioridad 4 — Roadmap post-4/4

### Opciones (requiere CR1 para priorizar):

1. **Supabase → fly.io migration** — Code OS's first real task ("come tu propia comida"). Migrar ~53 agentes de Supabase a fly.io Postgres + pgvector. Code OS ejecuta la migración como prueba de concepto.

2. **Code OS gaps** — context.py (141 líneas, sin compresión/limits), no briefing parser, no drift detection real, no atomic step concept. Estos gaps limitan la capacidad de Code OS para tareas más complejas.

3. **Reactor v4** — Generar preguntas desde telemetría operacional real (no solo documentos). Requiere las 3 tablas críticas: `programas_compilados`, `perfil_gradientes`, `observaciones_reactor`.

4. **Capa A Perplexity** — Búsquedas ad-hoc para F6 (Adaptación) y F5 (Identidad/Frontera). ~$1/mes por negocio. Aprobado pero no implementado.

5. **Swarm Tiers 4-5** — Profundo ($1/45min) y Cartografía ($10/horas). Los tiers 1-3 están validados.

6. **Wave 2 pilots** — Pilates studio + physiotherapy clinic. Requiere producto mínimo funcional.

### Mi recomendación (CR0):
Opción 1 (Supabase → fly.io) como siguiente paso. Razones:
- Valida Code OS en tarea real (no solo tests sintéticos)
- Elimina dependencia de Supabase (simplifica infra)
- Genera datos de telemetría reales para Reactor v4
- "Come tu propia comida" — principio 30

Pero tú decides (CR1).

---

## Archivos clave

- Agent loop: `motor_v1_validation/agent/core/agent_loop.py` (~975 líneas)
- Test: `briefings/test_validacion_modelos.py`
- Resultados B26: `results/B26_finish_force.md`
- Cadena completa: B18→B26 en `results/`
- Maestro v3: `docs/activo/MAESTRO_v3.md`
