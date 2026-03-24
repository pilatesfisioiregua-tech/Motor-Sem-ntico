"""Bus de señales inter-agente — infraestructura del sistema nervioso.

Tabla: om_senales_agentes
Tipos: DATO, ALERTA, DIAGNOSTICO, OPORTUNIDAD, PRESCRIPCION, ACCION
Prioridad: 1 (máx) a 10 (mín)

Uso:
    from src.pilates.bus import emitir, leer_pendientes, marcar_procesada
    await emitir("DATO", "OBSERVADOR", {"entidad": "asistencia", "accion": "crear", "id": str(id)})
"""
from __future__ import annotations

import json
import structlog
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
TIPOS_VALIDOS = {
    "DATO", "ALERTA", "DIAGNOSTICO", "OPORTUNIDAD", "PRESCRIPCION", "ACCION",
    "PERCEPCION", "PERCEPCION_CAUSAL", "PRESCRIPCION_ESTRATEGICA",
    "RECOMPILACION", "BRIEFING_PENDIENTE",
}


async def emitir(
    tipo: str,
    origen: str,
    payload: dict,
    destino: str | None = None,
    prioridad: int = 5,
) -> str:
    """Emite una señal al bus. Devuelve UUID de la señal creada."""
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {tipo}. Válidos: {TIPOS_VALIDOS}")

    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_senales_agentes (tipo, origen, destino, prioridad, payload, tenant_id)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6)
            RETURNING id
        """, tipo, origen, destino, prioridad, json.dumps(payload), TENANT)

    señal_id = str(row["id"])
    log.info("bus_emitir", tipo=tipo, origen=origen, destino=destino, prioridad=prioridad, id=señal_id)
    return señal_id


async def leer_pendientes(
    destino: str | None = None,
    tipo: str | None = None,
    limite: int = 20,
) -> list[dict]:
    """Lee señales pendientes, ordenadas por prioridad y antigüedad."""
    pool = await get_pool()
    conditions = ["estado = 'pendiente'", "tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if destino:
        conditions.append(f"(destino = ${idx} OR destino IS NULL)")
        params.append(destino)
        idx += 1

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    query = f"""
        SELECT id, created_at, tipo, origen, destino, prioridad, payload, estado
        FROM om_senales_agentes
        WHERE {where}
        ORDER BY prioridad ASC, created_at ASC
        LIMIT ${idx}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


async def marcar_procesada(señal_id: str | UUID, procesada_por: str) -> bool:
    """Marca una señal como procesada. Devuelve True si se actualizó."""
    pool = await get_pool()
    uid = señal_id if isinstance(señal_id, UUID) else UUID(str(señal_id))
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'procesada', procesada_por = $1, procesada_at = now()
            WHERE id = $2 AND estado = 'pendiente'
        """, procesada_por, uid)

    actualizado = result == "UPDATE 1"
    if actualizado:
        log.info("bus_procesada", id=str(señal_id), por=procesada_por)
    return actualizado


async def marcar_error(señal_id: str | UUID, procesada_por: str, detalle: str) -> bool:
    """Marca una señal como error."""
    pool = await get_pool()
    uid = señal_id if isinstance(señal_id, UUID) else UUID(str(señal_id))
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = $1, procesada_at = now(), error_detalle = $2
            WHERE id = $3 AND estado IN ('pendiente', 'procesando')
        """, procesada_por, detalle[:500], uid)
    return result == "UPDATE 1"


async def historial(
    limite: int = 50,
    tipo: str | None = None,
    origen: str | None = None,
) -> list[dict]:
    """Devuelve historial de señales recientes."""
    pool = await get_pool()
    conditions = ["tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    if origen:
        conditions.append(f"origen = ${idx}")
        params.append(origen)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    query = f"""
        SELECT id, created_at, tipo, origen, destino, prioridad, payload, estado, procesada_por, procesada_at
        FROM om_senales_agentes
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ${idx}
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


async def contar_pendientes() -> dict:
    """Cuenta señales pendientes agrupadas por tipo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT tipo, count(*) as n
            FROM om_senales_agentes
            WHERE estado = 'pendiente' AND tenant_id = $1
            GROUP BY tipo
        """, TENANT)
    return {r["tipo"]: r["n"] for r in rows}
