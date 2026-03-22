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
EMBED_MODEL = "openai/text-embedding-3-small"
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
    """Obtiene embedding via OpenRouter (text-embedding-3-small, 768 dims)."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            EMBED_URL,
            headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
            json={"model": EMBED_MODEL, "input": texto, "dimensions": 768}
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
