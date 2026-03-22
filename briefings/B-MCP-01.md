# B-MCP-01 — MCP Server de Conocimiento del Proyecto

**Estado:** CR0 — Pendiente ejecucion con Claude Code
**Fecha:** 2026-03-22
**Objetivo:** Crear un MCP server que permita a Claude Desktop consultar y alimentar un corpus de conocimiento destilado de los chats del proyecto, almacenado en pgvector.
**Dependencias:** pgvector ya desplegado (768 dims, nomic embeddings), fly.io activo
**Resultado:** Claude deja de perder contexto al comprimir ventana o abrir nueva sesion.

---

## FASE A — Migration SQL

Crear `migrations/015_conocimiento_proyecto.sql`:

```sql
BEGIN;

-- Verificar dependencia
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_clientes') THEN
    RAISE EXCEPTION 'Tabla om_clientes no existe — ejecutar migrations anteriores primero';
  END IF;
END $$;

-- Tabla principal: piezas de conocimiento destiladas de chats
CREATE TABLE IF NOT EXISTS om_conocimiento_proyecto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contenido TEXT NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN (
        'decision_cr1', 'principio', 'patron_validado',
        'error_no_repetir', 'arquitectura', 'implementacion',
        'insight', 'estado_sistema', 'otro'
    )),
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    -- metadata: {fecha_chat, titulo_chat, documentos_relacionados: [], F: [], L: [], INT: []}
    fuente VARCHAR(100) DEFAULT 'chat_destilado',
    fecha_conocimiento DATE DEFAULT CURRENT_DATE,
    relevancia_actual FLOAT DEFAULT 1.0,
    -- relevancia decae con el tiempo y cambia con el estado ACD
    ttl_dias INT,
    -- null = no caduca, >0 = caduca despues de N dias
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indice vectorial para busqueda por similaridad
CREATE INDEX IF NOT EXISTS idx_conocimiento_embedding
    ON om_conocimiento_proyecto USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- Indices de filtrado
CREATE INDEX IF NOT EXISTS idx_conocimiento_tipo
    ON om_conocimiento_proyecto (tipo);
CREATE INDEX IF NOT EXISTS idx_conocimiento_fecha
    ON om_conocimiento_proyecto (fecha_conocimiento DESC);

COMMIT;
```

### Test A1: Migration ejecuta sin error
```
fly postgres connect -a chief-os-omni -d motor_semantico < migrations/015_conocimiento_proyecto.sql
SELECT count(*) FROM om_conocimiento_proyecto;
-- Esperado: 0 (tabla existe, vacia)
```

---

## FASE B — Modulo Python: conocimiento.py

Crear `src/conocimiento.py`:

```python
"""Corpus vivo de conocimiento del proyecto.

Endpoints para ingestar, consultar y mantener el corpus
de conocimiento destilado de chats y documentos.
Usa pgvector para busqueda por similaridad semantica.
"""
from __future__ import annotations
import json
import structlog
import httpx
import os
from datetime import date, datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID

log = structlog.get_logger()
router = APIRouter(prefix="/conocimiento-proyecto", tags=["conocimiento"])

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
EMBED_MODEL = "nomic-ai/nomic-embed-text-v1.5"
EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
DISTILL_MODEL = "deepseek/deepseek-chat"
LLM_URL = "https://openrouter.ai/api/v1/chat/completions"


# ============================================================
# SCHEMAS
# ============================================================

class ConocimientoIngest(BaseModel):
    contenido: str
    tipo: str = Field(pattern="^(decision_cr1|principio|patron_validado|error_no_repetir|arquitectura|implementacion|insight|estado_sistema|otro)$")
    metadata: Optional[dict] = None
    ttl_dias: Optional[int] = None


class ChatIngest(BaseModel):
    """Texto completo o parcial de un chat para destilar."""
    texto_chat: str
    titulo_chat: Optional[str] = None
    fecha_chat: Optional[date] = None


class QueryConocimiento(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    tipo: Optional[str] = None
    umbral_similaridad: float = Field(default=0.70, ge=0, le=1)


# ============================================================
# HELPERS
# ============================================================

async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def _get_embedding(texto: str) -> list[float]:
    """Obtiene embedding via OpenRouter (nomic 768 dims)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            EMBED_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": EMBED_MODEL, "input": texto}
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"][0]["embedding"]


async def _destilar_chat(texto: str) -> list[dict]:
    """Destila un chat en piezas de conocimiento usando LLM barato."""
    system = """Eres un destilador de conocimiento. Dado un chat de trabajo,
extrae SOLO el conocimiento valioso: decisiones cerradas (CR1), principios descubiertos,
patrones validados, errores a no repetir, arquitectura diseñada, estados del sistema.

NO copies el chat. DESTILA en piezas cortas y densas.

Responde SOLO con JSON array:
[
  {"contenido": "texto de la pieza", "tipo": "decision_cr1|principio|patron_validado|error_no_repetir|arquitectura|implementacion|insight|estado_sistema", "metadata": {"documentos": [], "F": [], "L": [], "INT": []}}
]

Si el chat no tiene conocimiento destilable, responde: []"""

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            LLM_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={
                "model": DISTILL_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Destila este chat:\n\n{texto[:15000]}"}
                ],
                "temperature": 0.1,
                "max_tokens": 4000,
            }
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        # Limpiar markdown fences
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        return json.loads(content)


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/query")
async def query_conocimiento(data: QueryConocimiento):
    """Busca conocimiento por similaridad semantica.
    Este es el endpoint que Claude Desktop usa via MCP.
    """
    embedding = await _get_embedding(data.query)
    pool = await _get_pool()

    async with pool.acquire() as conn:
        conditions = ["1 - (embedding <=> $1::vector) > $2"]
        params = [str(embedding), data.umbral_similaridad]
        idx = 3

        if data.tipo:
            conditions.append(f"tipo = ${idx}")
            params.append(data.tipo)
            idx += 1

        # Excluir caducados
        conditions.append("(ttl_dias IS NULL OR fecha_conocimiento + ttl_dias * interval '1 day' > now())")

        where = " AND ".join(conditions)

        rows = await conn.fetch(f"""
            SELECT id, contenido, tipo, metadata, fecha_conocimiento,
                   relevancia_actual,
                   1 - (embedding <=> $1::vector) as similaridad
            FROM om_conocimiento_proyecto
            WHERE {where}
            ORDER BY similaridad DESC
            LIMIT ${idx}
        """, str(embedding), data.umbral_similaridad, *params[2:], data.top_k)

    return {
        "query": data.query,
        "resultados": len(rows),
        "conocimiento": [{
            "id": str(r["id"]),
            "contenido": r["contenido"],
            "tipo": r["tipo"],
            "metadata": r["metadata"] if isinstance(r["metadata"], dict) else json.loads(r["metadata"]) if r["metadata"] else {},
            "fecha": str(r["fecha_conocimiento"]),
            "similaridad": round(float(r["similaridad"]), 4),
        } for r in rows]
    }


@router.post("/ingest")
async def ingest_conocimiento(data: ConocimientoIngest):
    """Ingesta una pieza de conocimiento con embedding."""
    embedding = await _get_embedding(data.contenido)
    pool = await _get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_conocimiento_proyecto
                (contenido, tipo, embedding, metadata, ttl_dias)
            VALUES ($1, $2, $3::vector, $4::jsonb, $5)
            RETURNING id
        """, data.contenido, data.tipo, str(embedding),
            json.dumps(data.metadata or {}), data.ttl_dias)

    log.info("conocimiento_ingestado", tipo=data.tipo,
             contenido_preview=data.contenido[:80])
    return {"id": str(row["id"]), "status": "created"}


@router.post("/ingest-chat")
async def ingest_chat(data: ChatIngest):
    """Destila un chat completo y almacena las piezas de conocimiento."""
    piezas = await _destilar_chat(data.texto_chat)
    if not piezas:
        return {"status": "ok", "piezas_creadas": 0,
                "nota": "Chat sin conocimiento destilable"}

    pool = await _get_pool()
    creadas = 0

    for pieza in piezas:
        contenido = pieza.get("contenido", "")
        tipo = pieza.get("tipo", "otro")
        meta = pieza.get("metadata", {})
        if data.titulo_chat:
            meta["titulo_chat"] = data.titulo_chat
        if data.fecha_chat:
            meta["fecha_chat"] = str(data.fecha_chat)

        # Validar tipo
        tipos_validos = {"decision_cr1", "principio", "patron_validado",
                         "error_no_repetir", "arquitectura", "implementacion",
                         "insight", "estado_sistema", "otro"}
        if tipo not in tipos_validos:
            tipo = "otro"

        try:
            embedding = await _get_embedding(contenido)
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_conocimiento_proyecto
                        (contenido, tipo, embedding, metadata,
                         fecha_conocimiento, fuente)
                    VALUES ($1, $2, $3::vector, $4::jsonb, $5, 'chat_destilado')
                """, contenido, tipo, str(embedding),
                    json.dumps(meta),
                    data.fecha_chat or date.today())
            creadas += 1
        except Exception as e:
            log.warning("pieza_fallida", error=str(e), contenido=contenido[:50])

    log.info("chat_destilado", piezas=creadas, titulo=data.titulo_chat)
    return {"status": "ok", "piezas_creadas": creadas, "piezas_totales": len(piezas)}


@router.get("/stats")
async def stats_conocimiento():
    """Estadisticas del corpus de conocimiento."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento_proyecto")
        por_tipo = await conn.fetch("""
            SELECT tipo, count(*) as n FROM om_conocimiento_proyecto
            GROUP BY tipo ORDER BY n DESC
        """)
        caducados = await conn.fetchval("""
            SELECT count(*) FROM om_conocimiento_proyecto
            WHERE ttl_dias IS NOT NULL
              AND fecha_conocimiento + ttl_dias * interval '1 day' < now()
        """)
    return {
        "total_piezas": total,
        "por_tipo": {r["tipo"]: r["n"] for r in por_tipo},
        "caducadas": caducados,
    }


@router.delete("/limpiar-caducados")
async def limpiar_caducados():
    """Elimina piezas de conocimiento caducadas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM om_conocimiento_proyecto
            WHERE ttl_dias IS NOT NULL
              AND fecha_conocimiento + ttl_dias * interval '1 day' < now()
        """)
    eliminadas = int(result.split()[-1]) if result else 0
    log.info("conocimiento_limpiado", eliminadas=eliminadas)
    return {"eliminadas": eliminadas}
```

---

## FASE C — Montar router en main.py

Añadir en `src/main.py` despues del bloque de portal_router:

```python
# Mount Conocimiento router (MCP endpoint)
try:
    from src.conocimiento import router as conocimiento_router
    app.include_router(conocimiento_router)
    log.info("conocimiento_router_mounted")
except Exception as e:
    log.warning("conocimiento_router_mount_failed", error=str(e))
```

---

## FASE D — Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy
```

---

## FASE E — Tests PASS/FAIL

### V1: Health check incluye conocimiento
```
curl https://motor-semantico-omni.fly.dev/health
# PASS si devuelve status ok y no hay error de import
```

### V2: Tabla existe
```
curl -X GET https://motor-semantico-omni.fly.dev/conocimiento-proyecto/stats
# PASS si devuelve {"total_piezas": 0, "por_tipo": {}, "caducadas": 0}
```

### V3: Ingest funciona
```
curl -X POST https://motor-semantico-omni.fly.dev/conocimiento-proyecto/ingest \
  -H "Content-Type: application/json" \
  -d '{"contenido": "P41: Los gradientes son duales. Numero para calcular, semantica para diagnosticar. La semantica es fuente de verdad.", "tipo": "principio", "metadata": {"F": ["F1","F2","F3","F4","F5","F6","F7"], "L": ["S","Se","C"]}}'
# PASS si devuelve {"id": "...", "status": "created"}
```

### V4: Query por similaridad funciona
```
curl -X POST https://motor-semantico-omni.fly.dev/conocimiento-proyecto/query \
  -H "Content-Type: application/json" \
  -d '{"query": "gradientes duales numero semantica", "top_k": 3}'
# PASS si devuelve la pieza ingestada en V3 con similaridad > 0.80
```

### V5: Ingest-chat funciona (destilacion)
```
curl -X POST https://motor-semantico-omni.fly.dev/conocimiento-proyecto/ingest-chat \
  -H "Content-Type: application/json" \
  -d '{"texto_chat": "H: necesitamos que ACD sea numerico y semantico\nA: Exacto. La semantica es la fuente de verdad, el numero es resumen derivado. Esto es P41.\nH: si, ambos coexisten\nA: CR1 cerrado.", "titulo_chat": "test_destilacion", "fecha_chat": "2026-03-22"}'
# PASS si piezas_creadas >= 1
```

### V6: Stats refleja las ingestas
```
curl -X GET https://motor-semantico-omni.fly.dev/conocimiento-proyecto/stats
# PASS si total_piezas >= 2
```

---

## FASE F — Configuracion MCP en Claude Desktop

Despues del deploy, Jesús añade en la configuracion de Claude Desktop (`claude_desktop_config.json`) o en la interfaz de MCP:

**Opcion 1: Via HTTP MCP (si Claude Desktop lo soporta):**
```json
{
  "mcpServers": {
    "conocimiento-omni": {
      "url": "https://motor-semantico-omni.fly.dev/conocimiento-proyecto",
      "tools": [
        {"name": "query_conocimiento", "endpoint": "/query", "method": "POST"},
        {"name": "ingest_conocimiento", "endpoint": "/ingest", "method": "POST"},
        {"name": "ingest_chat", "endpoint": "/ingest-chat", "method": "POST"}
      ]
    }
  }
}
```

**Opcion 2: Via MCP wrapper local (mas robusto):**
Crear un script Python local que actue como MCP server y haga proxy a fly.io.
Esto se escribe en B-MCP-02 si la opcion 1 no funciona directamente.

---

## NOTAS

- El endpoint `/query` es el que Claude llama cuando necesita contexto
- El endpoint `/ingest-chat` es el que se llama al cerrar cada sesion
- `_destilar_chat` usa deepseek-chat (~$0.001/call) para extraer conocimiento
- `_get_embedding` usa nomic via OpenRouter (~$0.0001/call)
- Coste total por chat ingestado: ~$0.002
- Coste por query: ~$0.0001
- La tabla usa ivfflat con 10 listas (suficiente para <10K piezas)

---

**Autor:** Claude (diseño) + Jesus (CR1)
**Proximo paso:** Ejecutar con Claude Code. Despues: B-MCP-02 (wrapper MCP local si necesario) + ingestar chats historicos del proyecto.
