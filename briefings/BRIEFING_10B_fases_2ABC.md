# BRIEFING_10B: pgvector F1 — Fases 2A + 2B + 2C + 3 ediciones pendientes

Fecha: 2026-03-18
Prerequisito: Fase 1 ya ejecutada (migración 011, backfill, embedder.py, neural_db.py, ingest.py)

---

## CONTEXTO

Fase 1 ya está corriendo: migración 011 (HNSW, tsvector, hybrid_search RRF), backfill de embeddings, embedder.py, neural_db.py con _get_query_embedding, ingest.py con embed on insert.

Este briefing cubre TODO lo que queda para que la pata vectorial sea autónoma, esté conectada al Motor vN, y tenga telemetría.

---

## ARCHIVOS YA CREADOS POR OPUS CHAT (verificar que existen, no reescribir)

| Archivo | Fase | Descripción |
|---|---|---|
| `core/embed_maintenance.py` | 2A | refresh stale, reindex HNSW, prune orphans, health report, run_maintenance() |
| `core/vector_routing.py` | 2B | route_by_similarity(), enrich_gap_routing() para Motor vN |
| `core/auto_cluster.py` | 2C | k-means sobre embeddings → pobla knowledge_clusters |
| `core/search_telemetry.py` | 2C | track_search(), track_click(), get_quality_report() |
| `migrations/012_search_telemetry.sql` | 2C | tabla search_telemetry + vista materializada |

Verificar que existen en:
- `/Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent/core/`
- `/Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/`

Y también verificar que estas ediciones de Opus Chat ya están aplicadas:
- `core/reglas_compilador.py` — `_ints_para_gaps()` acepta `input_texto` y llama a `enrich_gap_routing()`
- `core/reglas_compilador.py` — `generar()` acepta `input_texto` y lo pasa
- `core/motor_vn.py` — `_fase_compilacion()` pasa `input_texto` a `manifold.generar()`

---

## 3 EDICIONES QUE CLAUDE CODE DEBE HACER

### Edición 1: Instrumentar neural_db.py con telemetría de búsqueda

Archivo: `core/neural_db.py`

Buscar esta línea dentro de `semantic_search()`:

```python
            logger.info(f"hybrid_search('{query}', scope={scope}) → {len(results)} results")
```

Reemplazar por:

```python
            has_vector = query_embedding is not None and len(query_embedding) > 0
            logger.info(f"hybrid_search('{query}', scope={scope}, vector={has_vector}) → {len(results)} results")

            # Search quality telemetry (Phase 2C)
            try:
                from core.search_telemetry import track_search
                track_search(
                    query=query, results=results, has_vector=has_vector,
                    scope=scope, session_id=session_id,
                )
            except Exception:
                pass
```

NOTA: si la línea ya fue cambiada parcialmente por Opus Chat, adaptarse al estado actual del archivo. Lo importante es que:
1. Se compute `has_vector` basado en `query_embedding`
2. Se llame a `track_search()` después del log
3. El bloque `track_search` esté en try/except para no romper búsquedas si falla la telemetría

### Edición 2: Añadir 3 endpoints de mantenimiento a api.py

Archivo: `api.py` (la raíz del agent: `motor_v1_validation/agent/api.py`, NO `core/api.py`)

Añadir justo ANTES del bloque `if __name__` al final del archivo:

```python
@app.post("/hooks/maintenance")
async def run_maintenance_hook():
    """Post-deploy hook: refresh embeddings, prune orphans, health check."""
    try:
        from core.embed_maintenance import run_maintenance
        results = run_maintenance()
        return {"status": "ok", "results": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/hooks/vector-health")
async def vector_health():
    """Health check for the vector search system."""
    try:
        from core.embed_maintenance import get_health_report
        return get_health_report()
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/hooks/search-quality")
async def search_quality():
    """Compare vector vs FTS search quality."""
    try:
        from core.search_telemetry import get_quality_report
        return get_quality_report()
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Edición 3: Añadir release_command a fly.toml para auto-maintenance en cada deploy

Archivo: `fly.toml` (en `motor_v1_validation/agent/fly.toml`)

Si existe una sección `[deploy]`, añadir dentro:
```toml
  release_command = "python3 -c 'from core.embed_maintenance import run_maintenance; run_maintenance()'"
```

Si NO existe sección `[deploy]`, crearla:
```toml
[deploy]
  release_command = "python3 -c 'from core.embed_maintenance import run_maintenance; run_maintenance()'"
```

---

## EJECUCIÓN DESPUÉS DE LAS EDICIONES

### Paso 1: Ejecutar migración 012 (search telemetry)
```bash
fly proxy 15432:5432 -a omni-mind-db &
sleep 3
psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -f /Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/012_search_telemetry.sql
```

### Paso 2: Ejecutar clustering inicial
```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent
python3 -m core.auto_cluster --n-clusters 20
```

### Paso 3: REINDEX HNSW (optimización post-backfill de Fase 1)
```bash
psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -c "REINDEX INDEX CONCURRENTLY idx_kb_embedding_hnsw;"
```

Si REINDEX CONCURRENTLY falla (requiere pgvector reciente), usar:
```bash
psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -c "REINDEX INDEX idx_kb_embedding_hnsw;"
```

---

## VERIFICACIÓN

```sql
-- 1. Migración 012 aplicada
SELECT count(*) FROM search_telemetry;
-- Debe devolver 0 (tabla existe, vacía)

-- 2. Vista materializada existe
SELECT * FROM search_quality_comparison;
-- Puede dar 0 rows, pero no debe dar error

-- 3. Clusters generados
SELECT count(*) as n_clusters, round(avg(coherence_score)::numeric, 3) as avg_coherence
FROM knowledge_clusters WHERE auto_generated = true;
-- Debe devolver > 0 clusters

-- 4. Top 5 clusters por tamaño
SELECT cluster_name, array_length(member_ids, 1) as size, coherence_score
FROM knowledge_clusters
ORDER BY array_length(member_ids, 1) DESC
LIMIT 5;

-- 5. Vector routing funciona (test con embedding de INT-07)
SELECT ei.id, 1 - (ei.embedding <=> ei2.embedding) as self_sim
FROM embeddings_inteligencias ei, embeddings_inteligencias ei2
WHERE ei.id = 'INT-07' AND ei2.id = 'INT-06'
LIMIT 1;
-- Debe devolver un float entre 0 y 1

-- 6. HNSW index optimizado
SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes WHERE indexname LIKE '%hnsw%';
```

### Verificar endpoints (después de deploy):
```bash
curl -X POST https://chief-os-omni.fly.dev/hooks/maintenance
curl https://chief-os-omni.fly.dev/hooks/vector-health
curl https://chief-os-omni.fly.dev/hooks/search-quality
```

---

## CRITERIO DE ÉXITO

- [ ] Las 3 ediciones aplicadas (neural_db telemetría, api.py endpoints, fly.toml release_command)
- [ ] Ediciones previas de Opus verificadas (reglas_compilador, motor_vn)
- [ ] Migración 012 ejecutada sin errores
- [ ] Clustering ejecutado (knowledge_clusters > 0)
- [ ] REINDEX HNSW completado
- [ ] search_telemetry tabla existe
- [ ] fly.toml tiene release_command

## COSTE
- Clustering: $0 (numpy local, sin LLM)
- Migración: $0
- Total: $0
