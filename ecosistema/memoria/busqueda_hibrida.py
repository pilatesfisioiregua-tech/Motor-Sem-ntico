"""Busqueda hibrida — vector + keyword + metadata (pgvector + Weaviate).

Combina 3 estrategias:
  1. Semantica: pgvector coseno sobre embeddings (sinónimos, conceptos)
  2. Keyword: tsvector full-text search (acronimos, codigos internos)
  3. Metadata: filtros exactos (tenant_id, tipo, fecha, agente)

Alpha configurable: 0.0=puro keyword, 1.0=puro semantico, 0.6=optimo.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from typing import Any, Optional

log = structlog.get_logger()


@dataclass
class ResultadoBusqueda:
    """Un resultado de busqueda hibrida."""
    tenant_id: str
    tipo: str
    clave: str
    valor: Any
    score_semantico: float = 0.0
    score_keyword: float = 0.0
    score_final: float = 0.0
    ciclo: str = ""


class BusquedaHibrida:
    """Motor de busqueda hibrida sobre om_pizarra.

    Requiere:
      - pgvector extension (para columna embedding)
      - tsvector column (para full-text search)

    Si no estan disponibles, fallback a busqueda exacta por clave.
    """

    def __init__(self, tenant_id: str, alpha: float = 0.6):
        self.tenant_id = tenant_id
        self.alpha = alpha  # peso semantico vs keyword

    async def buscar(self, query: str, tipo: str = None,
                     limite: int = 10, alpha: float = None,
                     fecha_desde: str = None) -> list[ResultadoBusqueda]:
        """Busqueda hibrida: semantica + keyword + metadata."""
        alpha = alpha or self.alpha

        try:
            return await self._busqueda_hibrida_sql(
                query, tipo, limite, alpha, fecha_desde)
        except Exception as e:
            log.debug("busqueda.fallback_exacta", error=str(e)[:80])
            return await self._busqueda_exacta(query, tipo, limite)

    async def _busqueda_hibrida_sql(self, query: str, tipo: str,
                                     limite: int, alpha: float,
                                     fecha_desde: str) -> list[ResultadoBusqueda]:
        """Busqueda hibrida via SQL (pgvector + tsvector)."""
        from src.db.client import get_pool
        pool = await get_pool()

        # Generar embedding del query
        embedding = await self._generar_embedding(query)

        filtro_tipo = "AND tipo = $3" if tipo else ""
        filtro_fecha = "AND created_at >= $4::timestamptz" if fecha_desde else ""

        params = [self.tenant_id, query]
        if tipo:
            params.append(tipo)
        if fecha_desde:
            params.append(fecha_desde)

        # Query hibrida: combina score vectorial y FTS
        if embedding:
            param_idx = len(params) + 1
            params.append(str(embedding))

            sql = f"""
                WITH semantica AS (
                    SELECT id, clave, tipo, valor, ciclo,
                           1 - (embedding <=> ${param_idx}::vector) as score_sem
                    FROM om_pizarra
                    WHERE tenant_id = $1
                      AND embedding IS NOT NULL
                      {filtro_tipo} {filtro_fecha}
                    ORDER BY embedding <=> ${param_idx}::vector
                    LIMIT {limite * 2}
                ),
                keyword AS (
                    SELECT id, clave, tipo, valor, ciclo,
                           ts_rank(search_vector, plainto_tsquery('spanish', $2)) as score_kw
                    FROM om_pizarra
                    WHERE tenant_id = $1
                      AND search_vector @@ plainto_tsquery('spanish', $2)
                      {filtro_tipo} {filtro_fecha}
                    LIMIT {limite * 2}
                )
                SELECT COALESCE(s.id, k.id) as id,
                       COALESCE(s.clave, k.clave) as clave,
                       COALESCE(s.tipo, k.tipo) as tipo,
                       COALESCE(s.valor, k.valor) as valor,
                       COALESCE(s.ciclo, k.ciclo) as ciclo,
                       COALESCE(s.score_sem, 0) as score_sem,
                       COALESCE(k.score_kw, 0) as score_kw,
                       ({alpha} * COALESCE(s.score_sem, 0)
                        + {1 - alpha} * COALESCE(k.score_kw, 0)) as score_final
                FROM semantica s
                FULL OUTER JOIN keyword k ON s.id = k.id
                ORDER BY score_final DESC
                LIMIT {limite}
            """
        else:
            # Sin embedding, solo keyword
            sql = f"""
                SELECT id, clave, tipo, valor, ciclo,
                       0 as score_sem,
                       ts_rank(search_vector, plainto_tsquery('spanish', $2)) as score_kw,
                       ts_rank(search_vector, plainto_tsquery('spanish', $2)) as score_final
                FROM om_pizarra
                WHERE tenant_id = $1
                  AND search_vector @@ plainto_tsquery('spanish', $2)
                  {filtro_tipo} {filtro_fecha}
                ORDER BY score_final DESC
                LIMIT {limite}
            """

        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        import json
        return [
            ResultadoBusqueda(
                tenant_id=self.tenant_id,
                tipo=r["tipo"],
                clave=r["clave"],
                valor=json.loads(r["valor"]) if isinstance(r["valor"], str) else r["valor"],
                score_semantico=float(r["score_sem"]),
                score_keyword=float(r["score_kw"]),
                score_final=float(r["score_final"]),
                ciclo=r["ciclo"],
            )
            for r in rows
        ]

    async def _busqueda_exacta(self, query: str, tipo: str,
                                limite: int) -> list[ResultadoBusqueda]:
        """Fallback: busqueda por LIKE en clave y valor."""
        from src.db.client import get_pool
        pool = await get_pool()

        filtro_tipo = "AND tipo = $3" if tipo else ""
        params = [self.tenant_id, f"%{query}%"]
        if tipo:
            params.append(tipo)

        async with pool.acquire() as conn:
            rows = await conn.fetch(f"""
                SELECT clave, tipo, valor, ciclo
                FROM om_pizarra
                WHERE tenant_id = $1
                  AND (clave ILIKE $2 OR valor::text ILIKE $2)
                  {filtro_tipo}
                ORDER BY created_at DESC
                LIMIT {limite}
            """, *params)

        import json
        return [
            ResultadoBusqueda(
                tenant_id=self.tenant_id,
                tipo=r["tipo"],
                clave=r["clave"],
                valor=json.loads(r["valor"]) if isinstance(r["valor"], str) else r["valor"],
                score_final=0.5,
                ciclo=r["ciclo"],
            )
            for r in rows
        ]

    async def _generar_embedding(self, texto: str) -> Optional[list[float]]:
        """Genera embedding via OpenAI text-embedding-3-small."""
        try:
            import httpx
            import os
            key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
            if not key:
                return None

            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": "text-embedding-3-small", "input": texto},
                )
                resp.raise_for_status()
                return resp.json()["data"][0]["embedding"]
        except Exception:
            return None
