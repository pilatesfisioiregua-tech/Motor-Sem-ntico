# PROMPT SIGUIENTE SESIÓN — Post Auditoría + Exocortex v2.1

**Fecha:** 2026-03-20
**Sesión anterior:** Completó B-ACD-16/17/18. Escribió B-ACD-19. Actualizó Exocortex a v2.1 con ACD.
**Objetivo:** Ejecutar B-ACD-19 (5 fases) + commit pendiente + avanzar Exocortex Pilates hacia implementación.

---

## ESTADO AL CERRAR

### Completados esta sesión
- B-ACD-16: ✅ PASS (deploy + persistencia + test e2e)
- B-ACD-17: ✅ PASS local (migrations V4 listas, pendiente deploy)
- B-ACD-18: ✅ PASS (auditoría motores → results/AUDITORIA_MOTORES.md)
- B-ACD-19: 📝 BRIEFING ESCRITO (5 fases: deploy+models+gestor+reactores)
- Exocortex Pilates: v2.0 → v2.1 (renombrado + ACD integrado: +S17, +T28/T29, séquito INT×P×R)
- INDICE_VIVO raíz: actualizado con v2.1

### Commit pendiente (HACER PRIMERO)
```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro

# Si motor-semantico es submodule, commit ahí primero:
cd motor-semantico
git add briefings/B-ACD-17.md briefings/B-ACD-18.md briefings/B-ACD-19.md \
        briefings/CHECKLIST_ACD.md briefings/PROMPT_NEXT_SESSION_POST_B17_B18.md \
        docs/INDICE_VIVO.md results/AUDITORIA_MOTORES.md
git commit -m "B-ACD-16/17/18 PASS, B-ACD-19 escrito, auditoría motores"
cd ..

# Commit raíz
git add docs/producto/casos/pilates/EXOCORTEX_PILATES_DEFINITIVO_v2.1.md \
        INDICE_VIVO.md motor-semantico \
        motor-semantico/briefings/PROMPT_NEXT_SESSION_POST_ACD_EXOCORTEX.md
git commit -m "ACD completo + Exocortex v2.1 con ACD integrado

- B-ACD-16: deploy + persistencia PASS
- B-ACD-17: migración DB V4 PASS (local)
- B-ACD-18: auditoría motores PASS
- B-ACD-19: briefing consolidado (deploy+models+gestor+reactores)
- Exocortex Pilates v2.0 → v2.1: +S17 ACD, +T28/T29, séquito INT×P×R
- INDICE_VIVO raíz actualizado"
```

---

## QUÉ HACER EN ESTA SESIÓN

### 1. Commit (si no se hizo)
Ejecutar los comandos del bloque anterior.

### 2. Ejecutar B-ACD-19
Briefing: `motor-semantico/briefings/B-ACD-19.md`
5 fases independientes:

| Fase | Qué | Tiempo est. |
|------|-----|-------------|
| A | Deploy con migrations V4 en startup (SQL + seeds Python) | ~2 min |
| B | Models: instalar sklearn en requirements.txt | ~5 min |
| C | **Gestor loop lento v0:** crear `src/gestor/analizador.py` + endpoint `/gestor/analizar` | ~30 min |
| D | **Reactor v4 telemetría v0:** crear `src/reactor/v4_telemetria.py` + endpoint `/reactor/telemetria` | ~20 min |
| E | **Reactor v5 como código:** crear `src/reactor/v5_empirico.py` + 5 casos semilla + endpoint `/reactor/v5` | ~15 min |

Resultado esperado: 3 endpoints nuevos. Post-deploy smoke test:
```bash
curl -X POST https://motor-semantico-omni.fly.dev/gestor/analizar
curl -X POST https://motor-semantico-omni.fly.dev/reactor/telemetria
# NO ejecutar /reactor/v5 como test — gasta ~$0.05
```

### 3. Si sobra tiempo: avanzar implementación Exocortex Pilates

El Exocortex v2.1 (`docs/producto/casos/pilates/EXOCORTEX_PILATES_DEFINITIVO_v2.1.md`) es el documento de diseño completo. Para avanzar hacia implementación, las siguientes piezas necesitan briefings:

**Fase 1 MVP (lo que Jesús necesita mañana):**

| Briefing | Qué | Dependencia |
|----------|-----|-------------|
| B-PIL-01 | Schema SQL 29 tablas en fly.io Postgres (om_* namespace) | Ninguna |
| B-PIL-02 | Seed data: 16 grupos + datos iniciales | B-PIL-01 |
| B-PIL-03 | Backend FastAPI: CRUD clientes + contratos + grupos | B-PIL-01 |
| B-PIL-04 | Backend: sesiones + asistencias + cargos + pagos (lógica de negocio) | B-PIL-03 |
| B-PIL-05 | Backend: automatismos (triggers: asistencia→cargo, cron→suscripción, pago→FIFO) | B-PIL-04 |
| B-PIL-06 | Frontend React: Modo Estudio (agenda día + marcar ausencias + cobro rápido) | B-PIL-04 |

**Fase 1b MVP extendido:**

| Briefing | Qué | Dependencia |
|----------|-----|-------------|
| B-PIL-07 | Onboarding self-service (T27 om_onboarding_links + formulario + contrato digital) | B-PIL-04 |
| B-PIL-08 | Facturación (T09-T10 + VeriFactu ready + PDF) | B-PIL-04 |

**Estos briefings NO están escritos todavía.** La sesión puede dedicarse a:
a) Escribir B-PIL-01 a B-PIL-06 (diseño → briefings ejecutables)
b) O ejecutar B-ACD-19 primero y escribir los B-PIL después

---

## DECISIÓN PENDIENTE (CR1 Jesús)

Antes de escribir B-PIL-01, necesitas decidir:

| # | Pregunta | Impacto |
|---|----------|---------|
| 1 | ¿Duración sesión individual? (1h? 45min? 55min?) | om_sesiones hora_fin |
| 2 | ¿Gastos fijos mensuales? (alquiler, seguros, suministros) | om_gastos seed data |
| 3 | ¿Autónomo o SL? | Serie facturas, datos fiscales |
| 4 | ¿Migrar Excel histórico o arrancar limpio? | Migración inicial |
| 5 | ¿Resultado visita Caja Rural? (TPV, Bizum, PayGold, Redsys) | Integración pagos |

Si no están resueltas, B-PIL-01 y B-PIL-02 se pueden escribir con placeholders marcados `-- PENDIENTE`.

---

## ARCHIVOS CLAVE (bajo demanda)

| Archivo | Cuándo leer |
|---------|-------------|
| `motor-semantico/briefings/B-ACD-19.md` | Para ejecutar consolidado post-ACD |
| `docs/producto/casos/pilates/EXOCORTEX_PILATES_DEFINITIVO_v2.1.md` | Fuente de verdad Pilates + ACD |
| `motor-semantico/briefings/CHECKLIST_ACD.md` | Estado global briefings |
| `motor-semantico/results/AUDITORIA_MOTORES.md` | Qué motores funcionan vs no |
| `docs/maestro/MAESTRO_V4.md` | Framework ACD completo |

---

## MAPA DE MOTORES (post B-ACD-18)

```
FUNCIONAL:
  Motor vN (pipeline + ACD)     → src/pipeline/ + src/tcf/
  Gestor compilador             → src/gestor/compilador.py
  Reactor v1 (sintéticos)       → src/reactor/
  Code OS                       → motor_v1_validation/agent/

PENDIENTE B-ACD-19:
  Gestor loop lento v0          → Fase C → src/gestor/analizador.py
  Reactor v4 telemetría v0      → Fase D → src/reactor/v4_telemetria.py
  Reactor v5 como código        → Fase E → src/reactor/v5_empirico.py
  Models C1-C4                  → Fase B → sklearn + datos

NO EXISTE (horizonte):
  Reactor v5.2 automatizado     → solo outputs manuales en results/reactor_v5/
  Meta-motor                    → concepto en Maestro V4 §8
```

---

## RESUMEN DE LA SESIÓN 20-MAR-2026

| Hito | Estado |
|------|--------|
| 18 briefings ACD (B-ACD-00 a B-ACD-15) | ✅ 16/16 PASS |
| B-ACD-16 deploy producción | ✅ PASS |
| B-ACD-17 migración DB V4 | ✅ PASS local |
| B-ACD-18 auditoría motores | ✅ PASS |
| B-ACD-19 consolidado post-ACD | 📝 escrito |
| Exocortex Pilates v2.1 | ✅ actualizado con ACD |
| Maestro V4 en repo | ✅ (CR0 pendiente validación) |
| Pipeline ACD en producción | ✅ Texto→diagnosticar→prescribir→ejecutar→evaluar→decidir |
| Coste por caso ACD | ~$0.005 + coste pipeline |

**Velocidad de la sesión:** 18 briefings escritos y ejecutados + 2 documentos mayores actualizados en ~1 día. El sistema ACD pasó de concepto (19-mar) a producción (20-mar) en 2 sesiones.
