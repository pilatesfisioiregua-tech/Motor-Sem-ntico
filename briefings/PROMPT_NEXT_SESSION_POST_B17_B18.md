# PROMPT SIGUIENTE SESIÓN — Post B-ACD-16/17/18

**Fecha:** 2026-03-20
**Sesión anterior:** Escribió B-ACD-17 (DB V4) y B-ACD-18 (auditoría motores). B-ACD-16 en ejecución.
**Objetivo:** Ejecutar B-ACD-19 (consolidado post-ACD: deploy + models + gestor + reactores).

---

## ESTADO AL CERRAR

### Completados
- Fases 0-5 ACD: 16/16 briefings PASS
- B-ACD-16: EN EJECUCIÓN (deploy + persistencia + test e2e)
- B-ACD-17: BRIEFING ESCRITO (migración DB → V4)
- B-ACD-18: BRIEFING ESCRITO (auditoría funcional motores)
- Maestro V4 en repo: `docs/maestro/MAESTRO_V4.md` (CR0 — pendiente validación)

### CR1 pendiente
- B-ACD-17 paso 5: ¿Opción A (DROP FK en aristas_grafo) o Opción B (tabla separada relaciones_cognitivas)?

---

## QUÉ HACER EN ESTA SESIÓN

### 1. Verificar B-ACD-16
```
Leer briefings/CHECKLIST_ACD.md → ver si B-ACD-16 pasó
Si PASS → continuar con B-ACD-17
Si FAIL → diagnosticar y arreglar
```

### 2. Ejecutar B-ACD-19 (consolidado post-ACD)
Briefing: `briefings/B-ACD-19.md`
5 fases:
- **Fase A:** Deploy con migrations V4 (SQL + seeds en startup)
- **Fase B:** Models — instalar sklearn, verificar imports
- **Fase C:** Gestor loop lento v0 — `src/gestor/analizador.py` + endpoint
- **Fase D:** Reactor v4 telemetría v0 — `src/reactor/v4_telemetria.py` + endpoint
- **Fase E:** Reactor v5 como código — `src/reactor/v5_empirico.py` + 5 casos semilla + endpoint

---

## ARCHIVOS CLAVE (bajo demanda)

| Archivo | Cuándo leer |
|---------|-------------|
| `briefings/B-ACD-19.md` | Para ejecutar consolidado post-ACD (5 fases) |
| `briefings/B-ACD-17.md` | Referencia migración DB (ya ejecutado local) |
| `briefings/B-ACD-18.md` | Referencia auditoría (ya ejecutada) |
| `briefings/CHECKLIST_ACD.md` | Para verificar estado global |
| `docs/maestro/MAESTRO_V4.md` | Si necesitas contexto del framework ACD |
| `src/db/schema.sql` | Si hay errores de migración |

---

## MAPA DE MOTORES (referencia rápida)

```
FUNCIONAL:
  Motor vN (pipeline + ACD)     → src/pipeline/ + src/tcf/
  Gestor compilador             → src/gestor/compilador.py
  Reactor v1 (sintéticos)       → src/reactor/
  Code OS                       → motor_v1_validation/agent/

PARCIAL / STUB:
  Models C1-C4                  → src/models/ (imports OK, ¿datos?)

NO EXISTE (hipótesis pre-auditoría):
  Gestor loop lento             → necesita: análisis patrones + poda + recompilación
  Reactor v5 como código        → outputs en results/reactor_v5/, sin automatización
  Reactor v4 (telemetría real)  → concepto en Maestro V4 §8, sin código
```
