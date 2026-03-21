# PROMPT SIGUIENTE SESIÓN — Post Fase 5: Deploy a Producción

**Fecha:** 2026-03-20
**Sesión anterior:** Completó Fases 0-5 ACD (16 briefings, todos PASS). Escribió B-ACD-16.
**Objetivo:** Ejecutar B-ACD-16 (deploy + migration + persistencia + test integración)

---

## ESTADO AL CERRAR

### Completados (16/16 briefings PASS)
- Fase 0: B-ACD-00 (Code OS rediseño) ✅
- Fase 1: B-ACD-01 a 04 (datos P, R, estados, DB) ✅
- Fase 2: B-ACD-05 a 08 (diagnóstico end-to-end) ✅
- Fase 3: B-ACD-09 a 11 (prescripción) ✅
- Fase 4: B-ACD-12, 13 (integración pipeline) ✅
- Fase 5: B-ACD-14, 15 (métricas + decisión ternaria) ✅

### Pendiente
- **B-ACD-16** — Deploy + migration + persistencia + test integración e2e
  - Briefing listo: `briefings/B-ACD-16.md`
  - 7 pasos: imports check → log_diagnostico() → persistir en orchestrator → fly deploy → verificar tablas → test e2e API → verificar persistencia DB

---

## QUÉ HACER EN ESTA SESIÓN

### 1. Leer estado
```
Leer briefings/CHECKLIST_ACD.md → confirmar Fases 0-5 completas
Leer briefings/B-ACD-16.md → ejecutar
```

### 2. Ejecutar B-ACD-16
Dile a Claude Code que ejecute `briefings/B-ACD-16.md`. Son 7 pasos secuenciales.

**Posibles bloqueantes:**
- `OPENROUTER_API_KEY` no está como secret en fly.io → `fly secrets set OPENROUTER_API_KEY=sk-...`
- DB no accesible → verificar `fly postgres list` y `DATABASE_URL` en secrets
- Import errors → paso 0 los detecta antes del deploy

### 3. Si B-ACD-16 pasa → ACD en producción

El pipeline completo funciona:
```
Texto → diagnosticar() → prescribir() → Router(+INTs) → Generador(+P/R) → Ejecutor → evaluar_acd() → decidir() → cierre/inerte/tóxico
```

Coste: ~$0.005/caso ACD + coste pipeline (variable según tier).

---

## ARCHIVOS CLAVE (no leer al inicio, solo bajo demanda)

| Archivo | Cuándo leer |
|---------|-------------|
| `briefings/B-ACD-16.md` | Para ejecutar el deploy |
| `briefings/CHECKLIST_ACD.md` | Para verificar estado |
| `src/pipeline/orchestrator.py` | Si hay errores de integración |
| `src/db/client.py` | Si hay errores de DB |
| `fly.toml` | Si hay errores de deploy |

---

## DESPUÉS DE B-ACD-16

Prioridades post-deploy (no para esta sesión a menos que sobre tiempo):

1. **Pilot Pilates real** — correr pipeline con caso real del estudio (no mock)
2. **Seed datos ACD en DB** — poblar tipos_pensamiento, tipos_razonamiento, estados_diagnosticos desde JSON (opcional, los JSON files funcionan fine)
3. **R09 sin INT compatible** — mapear o aceptar como gap conocido
4. **Reactor v4** — generar preguntas desde telemetría real (convierte decisión ternaria de heurística a empírica)
