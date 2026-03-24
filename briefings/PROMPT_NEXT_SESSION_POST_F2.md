# PROMPT CONTINUACIÓN — POST B-ORG-F2

**Fecha:** 24 marzo 2026
**Sesión anterior:** Escritura de B-ORG-PRODUCCION (F0+F1) + B-ORG-F2 (Pizarras+CQRS+Polish)

---

## QUÉ SE HIZO ESTA SESIÓN

1. **B-ORG-PRODUCCION** escrito: F0 Blindaje + F1 Valor Inmediato (10 pasos, 12 tests). Teléfono Jesús actualizado: 34607466631.
2. **B-ORG-F2** escrito: Pizarras + CQRS + Polish (8 pasos, 14 tests). Incluye migration 028, pizarras.py, json_utils.py, snapshots, LISTEN/NOTIFY, eliminación Stripe, G4 Opus-first, limpieza bus, Reactor v4 en cron.

## BRIEFINGS LISTOS PARA EJECUTAR (en orden)

| # | Briefing | Ruta | Prerequisito |
|---|----------|------|-------------|
| 1 | B-ORG-PRODUCCION | `briefings/B-ORG-PRODUCCION.md` | Nada |
| 2 | B-ORG-F2 | `briefings/B-ORG-F2.md` | B-ORG-PRODUCCION |
| 3 | B-ORG-POLISH | `briefings/B-ORG-POLISH.md` | Parcialmente cubierto por F2 |

## QUÉ HACER EN LA PRÓXIMA SESIÓN

**Opción A (recomendada): Ejecutar B-ORG-PRODUCCION + B-ORG-F2**
En ese orden. Primero blindaje, luego pizarras.

**Opción B: Si ya ejecutados, escribir B-ORG-F3 (Frontend profesional)**
F3 del roadmap: design system, mobile responsive, React Router, estado global.

**Opción C: Escribir B-ORG-TENANT (reemplazar TENANT hardcoded en 47 archivos)**
Briefing dedicado para la migración masiva de TENANT → pizarra dominio.

## DATOS DE JESÚS (confirmados)

- Teléfono: 607466631 (con prefijo: 34607466631)
- Email: pilatesfisioiregua@gmail.com
- Fly.io secret: `JESUS_TELEFONO=34607466631`

## DOCUMENTOS CLAVE

| Documento | Ruta |
|-----------|------|
| Briefing F0+F1 | `motor-semantico/briefings/B-ORG-PRODUCCION.md` |
| Briefing F2 | `motor-semantico/briefings/B-ORG-F2.md` |
| Roadmap v4 (CR1) | `docs/operativo/ROADMAP_CONSOLIDADO_23MAR.md` |
| Ficha Redsys | Adjunta en proyecto Claude |

## CONTEXTO RÁPIDO

```
query_conocimiento("B-ORG-PRODUCCION F0 blindaje auth cron health")
query_conocimiento("B-ORG-F2 pizarras CQRS HNSW snapshots LISTEN NOTIFY")
query_conocimiento("roadmap v4 127h 11 pizarras score 10")
```

## DEFERRED (no hacer ahora)

- B-ORG-TENANT: Reemplazar TENANT hardcoded en ~47 archivos con tenant_context.py
- Triggers proyección operacional → pizarra estado (requiere definir métricas frontend)
- Credenciales Redsys sandbox (esperando Caja Rural)
- Ficha Redsys: ya tiene email y teléfono de Jesús, lista para enviar
