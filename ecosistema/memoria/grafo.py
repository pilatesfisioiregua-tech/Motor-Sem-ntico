"""Grafo de conocimiento — relaciones tipadas entre conceptos (Neo4j pattern).

El conocimiento no es tabular — es un grafo.
Las relaciones entre conceptos son tan valiosas como los conceptos mismos.

Implementado sobre PostgreSQL con tabla de relaciones + queries recursivas.
Compatible con Apache AGE si se instala.
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from typing import Any, Optional

log = structlog.get_logger()


# Tipos de relacion soportados
TIPOS_RELACION = (
    "DEPENDE_DE",      # A depende de B para funcionar
    "IMPLEMENTA",      # A implementa B (concepto → codigo)
    "USA",             # A usa B como herramienta/recurso
    "CONTIENE",        # A contiene B (jerarquia)
    "CONFLICTO",       # A contradice B (IC3)
    "MEJORA",          # A mejoro B (evolucion)
    "REEMPLAZA",       # A reemplaza B (superseded)
    "SIMILAR",         # A es similar a B (embedding proximity)
    "CAUSA",           # A causa B (causalidad)
    "PRECEDE",         # A ocurre antes de B (temporal)
)


@dataclass
class Nodo:
    """Un nodo en el grafo de conocimiento."""
    id: str                  # tenant_id:tipo:clave
    tenant_id: str
    tipo: str                # tipo de pizarra
    clave: str
    label: str = ""          # Etiqueta legible
    propiedades: dict = field(default_factory=dict)


@dataclass
class Relacion:
    """Una relacion tipada entre dos nodos."""
    origen_id: str
    destino_id: str
    tipo: str                # DEPENDE_DE, USA, etc.
    peso: float = 1.0        # Fuerza de la relacion
    propiedades: dict = field(default_factory=dict)
    bidireccional: bool = False


class GrafoConocimiento:
    """Grafo de conocimiento sobre PostgreSQL.

    Operaciones:
      - Crear/eliminar nodos y relaciones
      - Traversal: vecinos, camino mas corto, N hops
      - Analisis: centralidad, clusters, dependencias
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def _nodo_id(self, tipo: str, clave: str) -> str:
        return f"{self.tenant_id}:{tipo}:{clave}"

    async def crear_relacion(self, origen_tipo: str, origen_clave: str,
                              destino_tipo: str, destino_clave: str,
                              tipo_relacion: str, peso: float = 1.0,
                              propiedades: dict = None) -> bool:
        """Crea una relacion entre dos nodos."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_grafo_relaciones
                        (tenant_id, origen_tipo, origen_clave,
                         destino_tipo, destino_clave,
                         tipo_relacion, peso, propiedades)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    ON CONFLICT (tenant_id, origen_tipo, origen_clave,
                                 destino_tipo, destino_clave, tipo_relacion)
                    DO UPDATE SET peso = $7, propiedades = $8::jsonb
                """, self.tenant_id, origen_tipo, origen_clave,
                    destino_tipo, destino_clave, tipo_relacion, peso,
                    json.dumps(propiedades or {}))
            return True
        except Exception as e:
            log.debug("grafo.crear_relacion_error", error=str(e)[:80])
            return False

    async def vecinos(self, tipo: str, clave: str,
                      tipo_relacion: str = None,
                      max_hops: int = 1) -> list[dict]:
        """Encuentra nodos conectados hasta N hops."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()

            if max_hops == 1:
                filtro_rel = f"AND tipo_relacion = '{tipo_relacion}'" if tipo_relacion else ""
                async with pool.acquire() as conn:
                    rows = await conn.fetch(f"""
                        SELECT destino_tipo, destino_clave, tipo_relacion, peso
                        FROM om_grafo_relaciones
                        WHERE tenant_id = $1
                          AND origen_tipo = $2 AND origen_clave = $3
                          {filtro_rel}
                        UNION
                        SELECT origen_tipo, origen_clave, tipo_relacion, peso
                        FROM om_grafo_relaciones
                        WHERE tenant_id = $1
                          AND destino_tipo = $2 AND destino_clave = $3
                          {filtro_rel}
                    """, self.tenant_id, tipo, clave)
            else:
                # Traversal recursivo para N hops
                async with pool.acquire() as conn:
                    rows = await conn.fetch("""
                        WITH RECURSIVE traversal AS (
                            SELECT destino_tipo as tipo, destino_clave as clave,
                                   tipo_relacion, peso, 1 as depth
                            FROM om_grafo_relaciones
                            WHERE tenant_id = $1
                              AND origen_tipo = $2 AND origen_clave = $3
                            UNION
                            SELECT r.destino_tipo, r.destino_clave,
                                   r.tipo_relacion, r.peso, t.depth + 1
                            FROM om_grafo_relaciones r
                            JOIN traversal t ON r.origen_tipo = t.tipo
                                              AND r.origen_clave = t.clave
                            WHERE r.tenant_id = $1 AND t.depth < $4
                        )
                        SELECT DISTINCT tipo, clave, tipo_relacion, peso, depth
                        FROM traversal
                        ORDER BY depth, peso DESC
                    """, self.tenant_id, tipo, clave, max_hops)

            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("grafo.vecinos_error", error=str(e)[:80])
            return []

    async def dependencias(self, tipo: str, clave: str) -> list[dict]:
        """Que se rompe si cambio este nodo? (traversal DEPENDE_DE)."""
        return await self.vecinos(tipo, clave, "DEPENDE_DE", max_hops=3)

    async def centralidad(self, limite: int = 10) -> list[dict]:
        """Nodos mas conectados (PageRank simplificado)."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT tipo_nodo, clave_nodo, count(*) as conexiones
                    FROM (
                        SELECT origen_tipo as tipo_nodo, origen_clave as clave_nodo
                        FROM om_grafo_relaciones WHERE tenant_id = $1
                        UNION ALL
                        SELECT destino_tipo, destino_clave
                        FROM om_grafo_relaciones WHERE tenant_id = $1
                    ) nodos
                    GROUP BY tipo_nodo, clave_nodo
                    ORDER BY conexiones DESC
                    LIMIT $2
                """, self.tenant_id, limite)
            return [dict(r) for r in rows]
        except Exception as e:
            log.debug("grafo.centralidad_error", error=str(e)[:80])
            return []
