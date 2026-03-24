"""Audit Log — Registro inmutable de acciones sobre datos sensibles.

Apple-grade: quién hizo qué cuándo sobre qué entidad.
RGPD Art. 30: registro de actividades de tratamiento.

Uso:
    from src.pilates.audit_log import registrar
    await registrar(conn, "Jesus", "UPDATE", "om_clientes", cliente_id, {"campo": "telefono"})
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()


async def registrar(
    conn,
    actor: str,
    accion: str,
    entidad: str,
    entidad_id: Optional[str] = None,
    detalles: Optional[dict] = None,
    tenant_id: str = "authentic_pilates",
    ip: Optional[str] = None,
) -> None:
    """Registra una acción en el audit log. Nunca falla (fire-and-forget)."""
    try:
        await conn.execute("""
            INSERT INTO om_audit_log
                (tenant_id, actor, accion, entidad, entidad_id, detalles, ip)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7)
        """, tenant_id, actor, accion, entidad,
            str(entidad_id) if entidad_id else None,
            json.dumps(detalles or {}), ip)
    except Exception as e:
        log.debug("audit_log_error", error=str(e)[:80])


async def consultar(
    conn,
    tenant_id: str = "authentic_pilates",
    entidad: Optional[str] = None,
    entidad_id: Optional[str] = None,
    actor: Optional[str] = None,
    limite: int = 50,
) -> list[dict]:
    """Consulta el audit log con filtros."""
    query = "SELECT * FROM om_audit_log WHERE tenant_id = $1"
    params = [tenant_id]
    idx = 2

    if entidad:
        query += f" AND entidad = ${idx}"
        params.append(entidad)
        idx += 1
    if entidad_id:
        query += f" AND entidad_id = ${idx}"
        params.append(entidad_id)
        idx += 1
    if actor:
        query += f" AND actor = ${idx}"
        params.append(actor)
        idx += 1

    query += f" ORDER BY created_at DESC LIMIT ${idx}"
    params.append(limite)

    rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]
