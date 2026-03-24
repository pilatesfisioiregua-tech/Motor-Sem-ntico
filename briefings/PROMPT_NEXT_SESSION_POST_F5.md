# PROMPT CONTINUACIÓN — POST B-ORG-F5

**Fecha:** 24 marzo 2026
**Sesión:** Escritura de 5 briefings (F0+F1, F2, F3, F4, F5) + fix producción

---

## BRIEFINGS COMPLETOS

| # | Briefing | Ruta | Horas | Score | Dependencia |
|---|----------|------|-------|-------|-------------|
| 1 | B-ORG-PRODUCCION (F0+F1) | `briefings/B-ORG-PRODUCCION.md` | 8h | 6.3 | ✅ EJECUTADO |
| 2 | B-ORG-F2 (Pizarras+CQRS) | `briefings/B-ORG-F2.md` | 7h | 7.0 | Nada |
| 3 | B-ORG-F3 (Frontend) | `briefings/B-ORG-F3.md` | 12h | 7.5 | F2 (parcial) |
| 4 | B-ORG-F4 (Motor) | `briefings/B-ORG-F4.md` | 17h | 8.2 | F2 |
| 5 | B-ORG-F5 (Agentes Diana) | `briefings/B-ORG-F5.md` | 10h | 8.5 | F4 |

**Total:** ~54h de implementación planificada. Score 5.2 → 8.5.

## PARALELISMO POSIBLE

```
F2 ──→ F3 (frontend)
   └──→ F4 (motor) ──→ F5 (agentes)
```

F3 y F4 son paralelos después de F2.

## QUÉ FALTA POR ESCRIBIR

| Fase | Horas | Descripción |
|------|-------|-------------|
| F6 Producción + Redsys + multi-tenant | 12h | Redsys completo, API docs, CI/CD, tests, segundo tenant |
| F6B Interfaz organismo + voz | 11h | Paneles organismo Cockpit, tabs profundos |
| F7 Presencia digital con identidad | 28h | Pizarra identidad, sensores externos, filtro F3, calendario contenido |
| F8 Autonomía total | 22h | Sin intervención humana semanal |

## CONTEXTO RÁPIDO

```
query_conocimiento("B-ORG-F5 mediador reactivo memoria traductor comunicacion")
query_conocimiento("B-ORG-F4 motor pensar cache AF generico")
query_conocimiento("roadmap v4 127h 11 pizarras score 10")
```
