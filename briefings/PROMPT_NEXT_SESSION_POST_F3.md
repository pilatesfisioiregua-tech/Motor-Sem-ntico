# PROMPT CONTINUACIÓN — POST B-ORG-F3

**Fecha:** 24 marzo 2026
**Sesión anterior:** Escritura de B-ORG-F3 (Frontend Profesional)

---

## QUÉ SE HIZO ESTA SESIÓN

1. **B-ORG-PRODUCCION** actualizado con teléfono Jesús (34607466631) en secrets fly.io.
2. **B-ORG-F2** escrito: Pizarras + CQRS + Polish (8 pasos, 14 tests).
3. **B-ORG-F3** escrito: Frontend Profesional (10 pasos, 12 tests).

## INCIDENCIA: MCP CONOCIMIENTO BLOQUEADO POR AUTH

El auth middleware de B-ORG-PRODUCCION ya está activo en producción (401 en /conocimiento-proyecto/ingest). El MCP server local (`scripts/mcp_conocimiento_server.py`) necesita enviar `X-API-Key` header. **FIX:** Añadir OMNI_API_KEY a las llamadas httpx del MCP server, o añadir `/conocimiento-proyecto/*` a PUBLIC_PREFIXES en main.py.

Recomendación: Añadir a PUBLIC_PREFIXES ya que el MCP server es de uso interno:
```python
PUBLIC_PREFIXES = (
    ...,
    "/conocimiento-proyecto/",
)
```

## BRIEFINGS LISTOS PARA EJECUTAR (en orden)

| # | Briefing | Ruta | Estado |
|---|----------|------|--------|
| 1 | B-ORG-PRODUCCION | `briefings/B-ORG-PRODUCCION.md` | ✅ EJECUTADO |
| 2 | B-ORG-F2 | `briefings/B-ORG-F2.md` | Pendiente |
| 3 | B-ORG-F3 | `briefings/B-ORG-F3.md` | Pendiente |

## QUÉ HACER EN LA PRÓXIMA SESIÓN

**Fix urgente:** Desbloquear MCP conocimiento (añadir a PUBLIC_PREFIXES o API key al MCP server).

**Opción A (recomendada): Ejecutar B-ORG-F2 + B-ORG-F3**

**Opción B: Escribir B-ORG-F4 (Motor + Caché LLM)**

## CONTEXTO RÁPIDO

```
query_conocimiento("B-ORG-PRODUCCION F0 blindaje auth cron health")
query_conocimiento("B-ORG-F2 pizarras CQRS HNSW snapshots")
query_conocimiento("B-ORG-F3 frontend profesional React Router SSE responsive")
query_conocimiento("roadmap v4 127h 11 pizarras score 10")
```
