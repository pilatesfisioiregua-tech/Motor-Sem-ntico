# PROMPT SIGUIENTE SESIÓN — Implementación Organismo Vivo

**Fecha:** 22 marzo 2026
**Objetivo:** Ejecutar B-ORG-01 (bus de señales + OBSERVADOR) y B-ORG-02 (Diagnosticador autónomo + Buscador)

---

## CONTEXTO CRÍTICO

### Qué se descubrió esta sesión

1. **45,000 líneas de Python** en el repo (no 18,000). El checklist estaba MUY desactualizado.
2. **ACD 11 pasos YA ESTÁN implementados** en src/tcf/ (diagnostico.py, repertorio.py, prescriptor.py, evaluador_acd.py, campo_dual.py). Integrados en pipeline/orchestrator.py.
3. **Code OS agent/core/ tiene 720KB** con infraestructura COMPLETA de organismo: self_healing.py, watchdog.py, mejora_continua.py, metacognitive.py (Kalman+FOK+JOL), telemetria.py, monitoring.py (SLOs+CircuitBreaker), flywheel.py, tool_evolution.py, drift_guard.py, predictive_controller.py, criticality_engine.py, gestor.py (52KB), motor_vn.py (49KB), chief.py (36KB), swarm.py (19KB), model_observatory.py (22KB).
4. **DOS sistemas paralelos desconectados:** src/ (asyncpg, FastAPI) y agent/core/ (psycopg2, Code OS). La prioridad es CONECTARLOS.
5. **72 agentes IA** en el plan completo. ~30 tienen código, ~20 son listeners ligeros, ~22 son nuevos.
6. **P59:** "Donde hay decisión, hay agente."

### Plan de implementación

Documento: `docs/operativo/PLAN_IMPLEMENTACION_ORGANISMO.md`

11 briefings en ~6 sesiones:
- FASE 0 (B-ORG-01 a 04): Sistema nervioso — bus, diagnosticador, vigía+mecánico+sanador, propiocepción
- FASE 1 (B-ORG-05 a 08): AF conectados — AF1+AF3, B2.9, AF2+AF4+AF6+AF7, Ejecutor+convergencia
- FASE 2 (B-ORG-09 a 11): Enjambre cognitivo — 23 agentes percepción, Compositor+Estratega+Orquestador, Guardián+Generativa

### Qué hacer AHORA

1. **Escribir B-ORG-01** como briefing ejecutable para Claude Code:
   - Migración 015: tabla om_senales_agentes
   - 4 endpoints en src/ (asyncpg)
   - Adaptador para agent/core/ (psycopg2) → misma tabla
   - OBSERVADOR: hooks en endpoints CRUD → señal DATO al bus
   - TEST PASS/FAIL concreto

2. **Escribir B-ORG-02** como briefing ejecutable:
   - POST /pilates/acd/diagnosticar-tenant
   - Recopila datos reales → diagnosticar() (YA EXISTE) → persiste → señal si cambio
   - POST /pilates/buscar-por-gaps → Perplexity → corpus
   - Añadir al cron

3. **Ejecutar ambos con Claude Code**

### Archivos clave

- Plan: `docs/operativo/PLAN_IMPLEMENTACION_ORGANISMO.md`
- Pipeline principal: `motor-semantico/src/pipeline/orchestrator.py`
- ACD: `motor-semantico/src/tcf/diagnostico.py` (diagnosticar() funciona)
- Prescriptor: `motor-semantico/src/tcf/prescriptor.py` (prescribir() funciona)
- Code OS self_healing: `motor-semantico/motor_v1_validation/agent/core/self_healing.py`
- Code OS watchdog: `motor-semantico/motor_v1_validation/agent/core/watchdog.py`
- Code OS telemetria: `motor-semantico/motor_v1_validation/agent/core/telemetria.py`
- Cron existente: `motor-semantico/src/pilates/cron.py`
- Main: `motor-semantico/src/main.py`
- Migraciones: `migrations/` (última: 014_acd_tables.sql)

### Corpus MCP

Consultar al inicio:
- query: "plan organismo v2 72 agentes" → plan completo
- query: "dos sistemas desconectados" → el problema de conexión
- query: "principio P59 agente decisión" → filosofía
- query: "self_healing watchdog mejora_continua" → código existente en Code OS
