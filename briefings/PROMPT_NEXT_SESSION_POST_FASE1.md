# PROMPT SIGUIENTE SESIÓN — Post FASE 1 Organismo

**Fecha:** 23 marzo 2026
**Contexto:** FASE 0 + FASE 1 del organismo COMPLETADAS en una sesión maratón.

---

## ESTADO ACTUAL — 8 briefings ejecutados, 6/7 gomas giran

### Briefings ejecutados (todos PASS):

| Briefing | Qué | Tests | Commit |
|---|---|---|---|
| B-ORG-01+02 | Bus señales + OBSERVADOR + Diagnosticador ACD + Buscador | 6/6 | 3690c84 |
| B-ORG-03 | Vigía + Mecánico + Autófago | 6/6 | dd75f64 |
| B-ORG-04 | Propiocepción (telemetría sistema) | 4/4 | fae7c0b |
| B-ORG-05 | AF1 Conservación + AF3 Depuración + VETO | 5/5 | — |
| B-ORG-06 | B2.9 Voz Reactivo (WA webhook→bus) | 4/4 | fbd6da1 |
| B-ORG-07 | AF2+AF4+AF6+AF7 → bus | 5/5 | 4ab5eee |
| B-ORG-08 | Ejecutor + Convergencia + Gestor | PENDIENTE RESULTADO | corriendo |

### Primer diagnóstico ACD REAL:
- **Estado: E3** (equilibrado bajo-medio)
- **Lentes: S=0.46, Se=0.34, C=0.40**
- **Gaps: F6 (Adaptación), F7 (Replicación)**

### Datos operativos del organismo (primera ejecución real):
- **AF1:** 2 clientes fantasma (contrato activo, sin asistencia 3+ semanas)
- **AF3:** 15/16 grupos infrautilizados (<3 alumnos), 2 contratos zombi, 12 VETOs emitidos
- **AF4:** 4 días sobrecargados (Ma=10, J=11.2 sesiones/día)
- **AF2:** 12 VETOs de AF3 respetados (mecanismo cross-AF funciona)
- **AF7:** Readiness 38%, 4/6 áreas sin procesos, 100% ADN sin contra-ejemplos
- **AF6:** 0 tensiones (tabla vacía — no hay reflexión sobre adaptación)
- **Autófago:** 91 funciones huérfanas, stripe_pagos.py detectado como obsoleto, 32 propuestas

### INSIGHT CRUZADO:
S=0.46 se explica por 15 grupos infrautilizados + 4 días sobrecargados = mucho horario con poca gente mal distribuida.
C=0.40 se explica por readiness 38% + 0% contra-ejemplos ADN.
Se=0.34 se explica por 0 tensiones + gaps F6/F7.

### Gomas:
- G1 ✅ Datos→Señales (OBSERVADOR en 4 CRUD)
- G2 ✅ Señales→Diagnóstico (DIAGNOSTICADOR, ACD E3)
- G3 ✅ Diagnóstico→Búsqueda (BUSCADOR, Perplexity sin API key aún)
- G4 ⏳ Búsqueda→Prescripción (FASE 2: enjambre cognitivo)
- G5 ✅ Prescripción→Acción (7 AF + EJECUTOR)
- G6 ✅ Acción→Aprendizaje (GESTOR + PROPIOCEPCIÓN)
- META ✅ Rotura→Reparación (VIGÍA+MECÁNICO+AUTÓFAGO)

---

## QUÉ HACER AHORA

### Opción A: FASE 2 — Enjambre Cognitivo (G4)
B-ORG-09/10/11 del plan: 23 agentes de percepción, Compositor, Estratega, Orquestador, Guardián.
Es la goma que falta. Pero es la más compleja y cara (~€2/ejecución profunda).

### Opción B: Redsys — Pagos reales
La ficha técnica está lista (Ficha_Tecnica_Caja_Rural_Redsys.docx en el proyecto).
Cuando Caja Rural responda con credenciales sandbox, implementar endpoints Redsys.
Es B-ORG-R1 del plan — paralelo e independiente.

### Opción C: Valor operativo inmediato
Con los datos que ya tiene el organismo, hay acciones concretas:
1. Cerrar/fusionar los 15 grupos infrautilizados (AF3 + 12 VETOs lo dicen)
2. Redistribuir sesiones de Ma/J a días menos cargados (AF4)
3. Documentar procesos en las 4 áreas vacías (AF7, sube C)
4. Definir contra-ejemplos para el ADN (AF7, sube C)
5. Añadir PERPLEXITY_API_KEY a fly.io para activar búsqueda real (G3)

### Opción D: Maestro V5 bloques pendientes
V5-03 a V5-09 están pendientes de escribir. Con el organismo funcionando,
hay experiencia real para documentar.

---

## ARCHIVOS CLAVE CREADOS ESTA SESIÓN

```
src/pilates/bus.py              — Bus de señales (emitir/leer/marcar/historial)
src/pilates/observador.py       — OBSERVADOR G1 (hooks CRUD)
src/pilates/diagnosticador.py   — DIAGNOSTICADOR G2 (ACD sobre datos reales)
src/pilates/buscador.py         — BUSCADOR G3 (gaps→Perplexity)
src/pilates/vigia.py            — VIGÍA META (6 health checks)
src/pilates/mecanico.py         — MECÁNICO META (clasifica+auto-fix)
src/pilates/autofago.py         — AUTÓFAGO F3 (ast+datos caducados)
src/pilates/propiocepcion.py    — PROPIOCEPCIÓN (telemetría sistema)
src/pilates/af1_conservacion.py — AF1 (fantasmas, engagement, deuda)
src/pilates/af3_depuracion.py   — AF3 (grupos, zombis, VETO)
src/pilates/voz_reactivo.py     — AF5 B2.9 (WA webhook→bus)
src/pilates/af_restantes.py     — AF2+AF4+AF6+AF7
src/pilates/ejecutor_convergencia.py — EJECUTOR+CONVERGENCIA+GESTOR
migrations/018_bus_senales.sql
migrations/019_telemetria_sistema.sql
```

## CORPUS MCP: 751 piezas

Queries útiles:
- "estado organismo gomas briefings ejecutados" → resumen
- "AF3 grupos infrautilizados VETO" → datos F3
- "ACD E3 lentes salud sentido continuidad" → diagnóstico real
- "readiness 38 procesos ADN" → gaps C
- "convergencia ejecutor gestor" → B-ORG-08
- "autofago stripe funciones huérfanas" → propuestas limpieza
