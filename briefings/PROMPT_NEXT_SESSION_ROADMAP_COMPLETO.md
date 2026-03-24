# PROMPT CONTINUACIÓN — ROADMAP v4 COMPLETO (9 BRIEFINGS)

**Fecha:** 24 marzo 2026
**Sesión:** Escritura completa del Roadmap v4 en 9 briefings ejecutables

---

## 9 BRIEFINGS COMPLETOS — DE 5.2 A 10/10

| # | Briefing | Ruta | Horas | Score | Dependencia |
|---|----------|------|-------|-------|-------------|
| 1 | B-ORG-PRODUCCION (F0+F1) | `briefings/B-ORG-PRODUCCION.md` | 8h | 6.3 | ✅ EJECUTADO |
| 2 | B-ORG-F2 (Pizarras+CQRS) | `briefings/B-ORG-F2.md` | 7h | 7.0 | Nada |
| 3 | B-ORG-F3 (Frontend) | `briefings/B-ORG-F3.md` | 12h | 7.5 | F2 parcial |
| 4 | B-ORG-F4 (Motor) | `briefings/B-ORG-F4.md` | 17h | 8.2 | F2 |
| 5 | B-ORG-F5 (Agentes Diana) | `briefings/B-ORG-F5.md` | 10h | 8.5 | F4 |
| 6 | B-ORG-F6 (Producción) | `briefings/B-ORG-F6.md` | 12h | 9.0 | F2, auth |
| 7 | B-ORG-F6B (Interfaz) | `briefings/B-ORG-F6B.md` | 11h | 9.3 | F3, F4 |
| 8 | B-ORG-F7 (Identidad) | `briefings/B-ORG-F7.md` | 28h | 9.8 | F4, F5, F6 |
| 9 | B-ORG-F8 (Autonomía) | `briefings/B-ORG-F8.md` | 22h | 10 | F5, F6, F6B, F7 |

**Total: ~127h → Score 5.2 → 10/10**

## GRAFO DE DEPENDENCIAS

```
F0+F1 ✅ → F2 → F3 (frontend)    ← paralelos
              → F4 (motor) → F5 (agentes) → F7 (identidad) → F8 (autonomía)
              → F6 (producción)            → F6B (interfaz) ↗
```

## PARALELISMO MÁXIMO

- F3 || F4 || F6 (todos después de F2)
- F5 después de F4
- F6B después de F3 + F4
- F7 después de F4 + F5 + F6
- F8 al final

## CONTEXTO RÁPIDO

```
query_conocimiento("B-ORG-F8 autonomia auto-reparacion prediccion PWA")
query_conocimiento("B-ORG-F7 presencia digital identidad filtro F3 contenido")
query_conocimiento("B-ORG-F6 tests CI/CD multi-tenant observabilidad")
query_conocimiento("B-ORG-F6B interfaz organismo paneles voz")
query_conocimiento("B-ORG-F5 mediador reactivo memoria traductor")
query_conocimiento("B-ORG-F4 motor pensar cache AF generico")
query_conocimiento("B-ORG-F3 frontend React Router SSE responsive")
query_conocimiento("B-ORG-F2 pizarras CQRS HNSW snapshots")
query_conocimiento("roadmap v4 127h 11 pizarras score 10")
```

## NOTAS CLAVE

- Redsys: código listo, esperando credenciales sandbox de Caja Rural
- Ficha Redsys: lista (email: pilatesfisioiregua@gmail.com, tel: 607466631)
- Publicación real IG/GBP: diferida a B-ORG-PUBLISH (requiere Meta app review)
- MCP conocimiento: /conocimiento-proyecto/ añadido a PUBLIC_PREFIXES
- fly.toml: grace_period 30s añadido para health check
