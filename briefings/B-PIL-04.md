# B-PIL-04: Backend Lógica de Negocio — Sesiones + Asistencias + Cargos + Pagos

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-03 (router Pilates montado)
**Coste:** $0

## CONTEXTO
CRUD montado. Cadena causal: SESION > ASISTENCIA > CARGO > PAGO (FIFO). Fuente: Exocortex v2.1 S1.3, S1.4, S5.

## INSTRUCCIONES
Archivo: src/pilates/router.py — LEER, ANADIR schemas + 11 endpoints.

### Schemas: SesionCreate, MarcarAsistencia, MarcarAsistenciaGrupo, PagoCreate, CargoManual

### 11 Endpoints nuevos:
- POST /sesiones — crea sesion + auto-asistencias grupo
- GET /sesiones/hoy — agenda dia
- POST /sesiones/{id}/completar — confirmada>asistio + cargos individual
- POST /sesiones/{id}/marcar — asistencia individual + cancelacion tardia
- POST /sesiones/{id}/marcar-grupo — solo ausencias (default=viene)
- GET /cargos — lista filtrable
- POST /cargos — cargo manual
- POST /cargos/suscripciones-mes — suscripciones mensuales idempotentes
- POST /pagos — pago + FIFO conciliacion
- GET /pagos — lista recientes
- GET /resumen — dashboard mes

### Logica FIFO, cancelacion tardia, suscripciones, default=viene
Codigo completo en archivo de descarga B-PIL-04.md de la sesion.

## Pass/fail
- Cadena cliente>contrato>suscripcion>cargo>pago>FIFO
- ~20 endpoints Pilates totales
