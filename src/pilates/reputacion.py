"""Reputación — Pide reseñas Google a clientes contentos automáticamente.

Criterio "cliente contento":
- Asistencia regular >= N sesiones consecutivas (default 8)
- Sin quejas últimos 30 días
- Engagement score > 70
- No ha dejado reseña este año

Programa pedido por WA con enlace directo a Google Reviews.
Máximo 3 pedidos/semana.
"""
from __future__ import annotations

import os
import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
MAX_PEDIDOS_SEMANA = 3
SESIONES_MIN = 8
ENGAGEMENT_MIN = 70
GOOGLE_REVIEWS_URL = os.getenv("GOOGLE_REVIEWS_URL", "")


async def detectar_clientes_contentos() -> list[dict]:
    """Detecta clientes que cumplen criterio de 'contento'."""
    pool = await get_pool()
    hoy = date.today()
    hace_30d = hoy - timedelta(days=30)

    async with pool.acquire() as conn:
        candidatos = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   ct.engagement_score, ct.racha_actual
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            WHERE ct.estado = 'activo'
            AND ct.engagement_score >= $2
            AND ct.racha_actual >= $3
            AND c.telefono IS NOT NULL
        """, TENANT, ENGAGEMENT_MIN, SESIONES_MIN)

        contentos = []
        for c in candidatos:
            # Sin quejas últimos 30 días
            quejas = await conn.fetchval("""
                SELECT count(*) FROM om_mensajes_wa
                WHERE tenant_id = $1 AND intencion = 'queja'
                AND created_at >= $2
                AND (telefono_remitente LIKE '%' || $3 OR telefono_destinatario LIKE '%' || $3)
            """, TENANT, hace_30d, (c["telefono"] or "")[-9:]) or 0

            if quejas > 0:
                continue

            # No ha recibido pedido de reseña este año
            pedido = await conn.fetchval("""
                SELECT count(*) FROM om_pizarra_comunicacion
                WHERE tenant_id = $1 AND tipo = 'pedido_resena'
                AND destinatario LIKE '%' || $2
                AND created_at >= date_trunc('year', now())
            """, TENANT, (c["telefono"] or "")[-9:]) or 0

            if pedido > 0:
                continue

            contentos.append({
                "cliente_id": str(c["id"]),
                "nombre": f"{c['nombre']} {c['apellidos'] or ''}".strip(),
                "telefono": c["telefono"],
                "engagement": c["engagement_score"],
                "racha": c["racha_actual"],
            })

    return contentos


async def programar_pedidos_resena() -> dict:
    """Para cada cliente contento, programa pedido de reseña."""
    contentos = await detectar_clientes_contentos()

    if not GOOGLE_REVIEWS_URL:
        log.info("reputacion_skip", razon="Sin URL Google Reviews configurada")
        return {"status": "skip", "razon": "Sin GOOGLE_REVIEWS_URL", "candidatos": len(contentos)}

    pool = await get_pool()
    programados = 0

    async with pool.acquire() as conn:
        for c in contentos[:MAX_PEDIDOS_SEMANA]:
            mensaje = (
                f"Hola {c['nombre'].split()[0]}! Llevamos {c['racha']} sesiones juntos "
                f"y nos encanta verte progresar.\n\n"
                f"Te importaria dejarnos una resena? Nos ayuda mucho:\n"
                f"{GOOGLE_REVIEWS_URL}\n\n"
                f"Gracias!"
            )
            await conn.execute("""
                INSERT INTO om_pizarra_comunicacion
                    (tenant_id, destinatario, canal, tipo, mensaje,
                     programado_para, estado, origen)
                VALUES ($1, $2, 'whatsapp', 'pedido_resena', $3,
                        now() + interval '2 hours', 'pendiente', 'REPUTACION')
            """, TENANT, c["telefono"], mensaje)
            programados += 1

    log.info("reputacion_programada", candidatos=len(contentos), programados=programados)
    return {"status": "ok", "candidatos": len(contentos), "programados": programados}
