"""Feed del Estudio — Noticias en tiempo real.

Cada evento relevante genera una noticia en el feed.
Jesús abre el estudio y ve qué ha pasado sin buscar nada.

Fuente: Exocortex v2.1 B-PIL-18-DEF.
"""
from __future__ import annotations

import structlog
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def publicar(tipo: str, icono: str, titulo: str, detalle: str = None,
                   cliente_id: UUID = None, severidad: str = "info",
                   accion_url: str = None) -> None:
    """Publica una noticia en el feed del estudio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_feed_estudio (tenant_id, tipo, icono, titulo, detalle,
                cliente_id, severidad, accion_url)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """, TENANT, tipo, icono, titulo, detalle, cliente_id, severidad, accion_url)
    log.info("feed_publicado", tipo=tipo, titulo=titulo[:50])


# ============================================================
# HELPERS — cada tipo de evento
# ============================================================

async def feed_cancelacion(nombre: str, fecha: str, hora: str, cliente_id: UUID):
    await publicar("cancelacion", "🔴", f"{nombre} canceló clase",
                   f"{fecha} a las {hora}", cliente_id, "warning")


async def feed_pago(nombre: str, metodo: str, monto: float, cliente_id: UUID):
    await publicar("pago", "💰", f"Pago {nombre}",
                   f"{monto:.2f}€ vía {metodo}", cliente_id, "success")


async def feed_solicitud(nombre: str, tipo: str, descripcion: str, cliente_id: UUID):
    await publicar("solicitud", "📋", f"Solicitud de {nombre}",
                   f"{tipo}: {descripcion[:100]}", cliente_id, "warning")


async def feed_alerta(nombre: str, tipo_alerta: str, detalle: str, cliente_id: UUID):
    await publicar("alerta_retencion", "⚠️", f"Alerta: {nombre}",
                   f"{tipo_alerta} — {detalle}", cliente_id, "danger")


async def feed_milestone(nombre: str, milestone: str, cliente_id: UUID):
    await publicar("milestone", "🏆", f"{nombre}: {milestone}",
                   None, cliente_id, "success")


async def feed_cobro_fallido(nombre: str, monto: float, cliente_id: UUID):
    await publicar("cobro_fallido", "🔴", f"Cobro fallido: {nombre}",
                   f"{monto:.2f}€ — revisar tarjeta", cliente_id, "danger")


async def feed_onboarding(nombre: str, grupo: str, cliente_id: UUID):
    await publicar("onboarding", "🆕", f"Nuevo cliente: {nombre}",
                   f"Grupo: {grupo}" if grupo else None, cliente_id, "success")


async def feed_lista_espera(nombre: str, detalle: str, cliente_id: UUID):
    await publicar("lista_espera", "🔔", f"Lista espera: {nombre}",
                   detalle, cliente_id, "info")


async def feed_engagement(nombre: str, de_score: int, a_score: int, cliente_id: UUID):
    await publicar("engagement", "📉", f"Engagement cayendo: {nombre}",
                   f"De {de_score} a {a_score}", cliente_id, "warning")
