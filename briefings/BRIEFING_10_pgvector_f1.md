# BRIEFING_10: pgvector F1 — COMPLETO (Fases 1 + 2A + 2B + 2C)

Fecha: 2026-03-18
CR1: nomic-embed-text-v1.5 (768 dims) + HNSW + RRF confirmado.

---

## ARCHIVOS YA CREADOS POR OPUS CHAT (no tocar, solo verificar que existen)

### Fase 1 — Core
- `core/embedder.py` — cliente embedding via OpenRouter (nomic-embed-text-v1.5, 768 dims)
- `migrations/011_vector_f1.sql` — schema vector(768), HNSW, tsvector, nueva hybrid_search() con RRF
- `embed_pipeline.py` — backfill 27k+ rows + 18 inteligencias
- `core/neural_db.py` — EDITADO: `_get_query_embedding()` usa `embedder.embed_one()`
- `ingest.py` — EDITADO: `_generate_embeddings_for_batch()` usa `embedder.embed_batch()`

### Fase 2A — Autonomía
- `core/embed_maintenance.py` — refresh stale, reindex HNSW, prune orphans, health report

### Fase 2B — Conexión al sistema
- `core/vector_routing.py` — route_by_similarity, enrich_gap_routing para Motor vN
- `core/reglas_compilador.py` — EDITADO: `_ints_para_gaps()` acepta `input_texto`, llama a `enrich_gap_routing()`
- `core/reglas_compilador.py` — EDITADO: `generar()` acepta `input_texto`, lo pasa a `_ints_para_gaps()`
- `core/motor_vn.py` — EDITADO: `_fase_compilacion()` pasa `input_texto` a `manifold.generar()`

### Fase 2C — Telemetría + Clusters
- `migrations/012_search_telemetry.sql` — tabla + vista materializada para comparar vector vs FTS
- `core/search_telemetry.py` — track_search, track_click, get_quality_report
- `core/auto_cluster.py` — k-means sobre embeddings, pobla knowledge_clusters

---

## 3 EDICIONES PENDIENTES QUE CLAUDE CODE DEBE HACER

### Edición 1: Instrumentar neural_db.py con telemetría de búsqueda

Archivo: `core/neural_db.py`

Buscar este bloque EXACTO dentro de `semantic_search()`:

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

### Edición 2: Añadir endpoint /hooks/maintenance al API

Archivo: `api.py` (la raíz del agent, NO core/api.py)

Buscar el último `@app.get` o `@app.post` que haya antes del `if __name__` block, y AÑADIR justo antes de `if __name__`:

```python
@app.post("/hooks/maintenance")
async def run_maintenance():
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

### Edición 3: Añadir maintenance al Dockerfile o fly.toml release_command

Archivo: `fly.toml`

Si existe un `[deploy]` section, añadir:
```toml
  release_command = "python3 -c 'from core.embed_maintenance import run_maintenance; run_maintenance()'"
```

Si NO existe `[deploy]` section, crear:
```toml
[deploy]
  release_command = "python3 -c 'from core.embed_maintenance import run_maintenance; run_maintenance()'"
```

Esto ejecuta el refresh de embeddings automáticamente en cada deploy.

---

## ORDEN DE EJECUCIÓN

```
PASO 1: Hacer las 3 ediciones pendientes (arriba)
PASO 2: Ejecutar migración 011 contra la DB
         fly proxy 15432:5432 -a omni-mind-db &
         sleep 3
         psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -f /Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/011_vector_f1.sql
PASO 3: Ejecutar migración 012
         psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -f /Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/012_search_telemetry.sql
PASO 4: Ejecutar backfill de embeddings + inteligencias
         cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent
         python3 embed_pipeline.py --inteligencias
PASO 5: Ejecutar clustering inicial
         cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/motor_v1_validation/agent
         python3 -m core.auto_cluster --n-clusters 20
PASO 6: REINDEX HNSW (post-backfill optimization)
         psql "postgres://chief_os_omni:77qJGeKtMTgCYhz@localhost:15432/omni_mind" -c "REINDEX INDEX CONCURRENTLY idx_kb_embedding_hnsw;"
PASO 7: Verificar TODO
```

---

## VERIFICACIÓN (ejecutar después de PASO 6)

```sql
-- 1. Columnas vector correctas (debe decir vector, not null count > 0)
SELECT count(*) as with_embedding FROM knowledge_base WHERE embedding IS NOT NULL;
SELECT count(*) as without_embedding FROM knowledge_base WHERE embedding IS NULL;

-- 2. HNSW indexes activos
SELECT indexname, indexdef FROM pg_indexes WHERE indexname LIKE '%hnsw%';

-- 3. tsvector column + trigger
SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_base' AND column_name = 'tsv';
SELECT tgname FROM pg_trigger WHERE tgname = 'trg_kb_tsv';

-- 4. 18 inteligencias embeddeadas
SELECT count(*) FROM embeddings_inteligencias WHERE embedding IS NOT NULL;

-- 5. Clusters generados
SELECT count(*), avg(coherence_score) FROM knowledge_clusters;

-- 6. Search telemetry table exists
SELECT count(*) FROM search_telemetry;

-- 7. TEST SEMÁNTICO: buscar por significado (no por palabras exactas)
-- Esto DEBE devolver resultados aunque "retención" no aparezca en texto
SELECT kb.id, kb.scope, left(kb.texto, 100) as texto,
       1 - (kb.embedding <=> ei.embedding) as sim
FROM knowledge_base kb,
     (SELECT embedding FROM embeddings_inteligencias WHERE id = 'INT-07') ei
WHERE kb.embedding IS NOT NULL
ORDER BY kb.embedding <=> ei.embedding
LIMIT 5;

-- 8. hybrid_search() con vector funciona
-- (necesita embedding de query — probar desde Code OS o con embed_pipeline)
```

## CRITERIO DE ÉXITO
- [ ] 3 ediciones aplicadas
- [ ] Migración 011 ejecutada sin errores
- [ ] Migración 012 ejecutada sin errores
- [ ] HNSW index creado
- [ ] tsvector columna + trigger activo
- [ ] >90% de knowledge_base rows tienen embedding
- [ ] 18 embeddings_inteligencias pobladas
- [ ] Clusters generados (knowledge_clusters > 0)
- [ ] search_telemetry table existe
- [ ] Endpoints /hooks/maintenance, /hooks/vector-health, /hooks/search-quality responden
- [ ] fly.toml tiene release_command de maintenance
- [ ] hybrid_search() con firma vectorial funciona

## COSTE TOTAL ESTIMADO
- Backfill 27k chunks: ~$0.10
- Embeddings 18 inteligencias: ~$0.001
- Clustering: $0 (local numpy, sin LLM)
- Total: ~$0.10
