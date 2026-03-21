# PROMPT SIGUIENTE SESIÓN — Post B-PIL-17 (COMPLETO)

**Fecha:** 2026-03-20
**Sesión anterior:** Escribió y ejecutó B-PIL-01 a B-PIL-17. TODOS completados.

---

## ESTADO: EXOCORTEX PILATES v2.1 — 100% IMPLEMENTADO

### 17/17 briefings PASS
- B-PIL-01: ✅ 29 tablas om_*
- B-PIL-02: ✅ 16 grupos seed
- B-PIL-03: ✅ 11 endpoints CRUD
- B-PIL-04: ✅ 11 endpoints lógica (FIFO, cancelación tardía, suscripciones)
- B-PIL-05: ✅ Automatismos (cron, alertas, bizum, días esperados)
- B-PIL-06: ✅ Frontend Modo Estudio (React + Vite, dark mode)
- B-PIL-07: ✅ Onboarding self-service (4 endpoints + formulario 4 pasos)
- B-PIL-08: ✅ Facturación (7 endpoints, VeriFactu, paquete gestor)
- B-PIL-09: ✅ WhatsApp Business Cloud API (webhook, envío, clasificación)
- B-PIL-10: ✅ Panel WA Modo Estudio (respuestas inteligentes, 1-clic)
- B-PIL-11: ✅ Portal del Cliente (8 endpoints, autogestión)
- B-PIL-12: ✅ Modo Profundo + Briefing semanal + ACD tenant
- B-PIL-13: ✅ Séquito 24 asesores ($0.003/consulta rápida)
- B-PIL-14: ✅ ADN + Procesos + Conocimiento + Tensiones + Depuración + Readiness (20 endpoints)
- B-PIL-15: ✅ Bloque Voz (15 propuestas generadas, Capa A Open-Meteo, ISP)
- B-PIL-16: ✅ Seed realista (20 clientes, 270 sesiones, 342 asistencias, 38 pagos) + Smoke 35/35 PASS + Production readiness (CORS, health ampliado, 111 endpoints, error handler)
- B-PIL-17: ✅ Calendario semanal tipo iOS (bloques color, hora actual, navegación)

### Números en producción
- 111 endpoints totales
- 29 tablas om_*
- 22 clientes activos (20 seed + 2 test)
- 270 sesiones, 342 asistencias (92.1%)
- 38 cargos + 38 pagos
- 15 propuestas Voz generadas
- 5 principios ADN + 18 gastos fijos
- Readiness replicación: 17%
- Smoke test: 35/35 PASS

### URLs
- Modo Estudio: `https://motor-semantico-omni.fly.dev/estudio`
- Modo Profundo: `https://motor-semantico-omni.fly.dev/profundo`
- Health: `https://motor-semantico-omni.fly.dev/health`
- Endpoints: `https://motor-semantico-omni.fly.dev/endpoints`
- Onboarding: `https://motor-semantico-omni.fly.dev/onboarding/{token}`
- Portal: `https://motor-semantico-omni.fly.dev/portal/{token}`

---

## QUÉ HACER EN ESTA SESIÓN

### 1. Migración Excel de clientes
Jesús quiere importar sus clientes reales desde un Excel. Tiene solo nombres.
Flujo: subir Excel → leer → script migración → asignar grupos → generar portales.

### 2. Verificar frontend visual
Verificar que `/estudio` y `/profundo` cargan correctamente.
Si 404: verificar `frontend/dist/` en Docker image.

### 3. Configurar secrets fly.io (externos)
```bash
fly secrets set WHATSAPP_TOKEN=<token> WHATSAPP_PHONE_ID=<phone_id> JESUS_TELEFONO=<tel> PERPLEXITY_API_KEY=<key> -a motor-semantico-omni
```

### 4. Preguntas operativas pendientes (CR1 Jesús)
| # | Pregunta | Impacto |
|---|----------|---------|
| 1 | Duración sesión individual | om_sesiones hora_fin |
| 2 | Gastos fijos mensuales reales | om_gastos |
| 3 | Autónomo o SL | Serie facturas |
| 5 | Resultado visita Caja Rural | Integración pagos |

---

## HORIZONTE (no bloqueado por briefings)

| Qué | Depende de |
|-----|-----------|
| Integración Redsys | Resultado Caja Rural |
| Cobro recurrente | Redsys |
| Base compartida fisioterapia | Sesión diseño con esposa |
| EEDAP codificado | Sesión diseño con Jesús |

---

## ARCHIVOS CLAVE

| Archivo | Qué |
|---------|-----|
| `src/pilates/router.py` | Backend principal (~70+ endpoints Pilates) |
| `src/pilates/portal.py` | Portal cliente (8 endpoints) |
| `src/pilates/whatsapp.py` | WhatsApp bidireccional |
| `src/pilates/wa_respuestas.py` | Respuestas inteligentes WA |
| `src/pilates/sequito.py` | 24 asesores + Consejo |
| `src/pilates/briefing.py` | Briefing semanal + ACD tenant |
| `src/pilates/voz.py` | Bloque Voz + Capa A + ISP |
| `src/pilates/automatismos.py` | Crons + alertas |
| `frontend/src/App.jsx` | Frontend principal Modo Estudio |
| `frontend/src/Calendario.jsx` | Vista calendario iOS |
| `frontend/src/Profundo.jsx` | Modo Profundo (8 pestañas) |
| `frontend/src/Portal.jsx` | Portal cliente (5 vistas) |
| `frontend/src/Onboarding.jsx` | Formulario onboarding (4 pasos) |
| `frontend/src/Consejo.jsx` | Séquito asesores UI |
| `frontend/src/PanelWA.jsx` | Panel WhatsApp Modo Estudio |
| `frontend/src/api.js` | Cliente API (~60+ funciones) |
| `scripts/seed_realista.py` | Seed 20 clientes + 8 semanas datos |
| `scripts/smoke_test_e2e.py` | 35 tests E2E |

## RESUMEN SESIÓN 20-MAR-2026

De cero a Exocortex completo en UNA sesión:
- 17 briefings escritos y ejecutados
- 111 endpoints en producción
- 29 tablas, 22 clientes, 270 sesiones
- Frontend completo (calendario iOS + dashboard + séquito + portal)
- Smoke test 35/35 PASS
- Coste séquito: $0.003/consulta
