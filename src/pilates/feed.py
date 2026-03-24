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

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


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


# ============================================================
# FEED DEL ORGANISMO — El sistema se hace visible
# ============================================================

async def feed_af_deteccion(agente: str, tipo: str, detalle: str,
                             cliente_id: UUID = None):
    """AF detectó algo: riesgo, ineficiencia, oportunidad, etc."""
    iconos = {
        "AF1": "🛡️", "AF2": "🎯", "AF3": "🗑️",
        "AF4": "⚖️", "AF6": "🔄", "AF7": "📖",
    }
    await publicar(
        f"organismo_{agente.lower()}", iconos.get(agente, "🤖"),
        f"{agente}: {tipo}", detalle[:200],
        cliente_id, "info" if "oportunidad" in tipo.lower() else "warning")


async def feed_af_veto(agente_origen: str, agente_bloqueado: str,
                        motivo: str, cliente_id: UUID = None):
    """Un AF vetó la acción de otro."""
    await publicar(
        "organismo_veto", "🚫",
        f"VETO: {agente_origen} bloquea {agente_bloqueado}",
        motivo[:200], cliente_id, "danger")


async def feed_convergencia(clientes: list[str], agentes: list[str], detalle: str):
    """Múltiples AF señalan al mismo cliente/grupo."""
    nombres = ", ".join(clientes[:3])
    await publicar(
        "organismo_convergencia", "🔗",
        f"Convergencia: {nombres}",
        f"{'+'.join(agentes)} coinciden. {detalle[:150]}",
        severidad="warning")


async def feed_diagnostico_acd(estado: str, s: float, se: float, c: float,
                                 cambio: str = None):
    """Resultado del diagnóstico ACD semanal."""
    await publicar(
        "organismo_acd", "🧠",
        f"Diagnóstico ACD: {estado}",
        f"S={s:.2f} Se={se:.2f} C={c:.2f}" + (f" — {cambio}" if cambio else ""),
        severidad="info")


async def feed_perfil_cognitivo(perfil: str, disfunciones: int, confianza: float):
    """Resultado del enjambre: perfil INT×P×R."""
    sev = "danger" if perfil in ("automata", "operador_ciego") else "warning" if not perfil.startswith("E") else "info"
    await publicar(
        "organismo_perfil", "🔬",
        f"Perfil cognitivo: {perfil}",
        f"{disfunciones} disfunciones IC detectadas. Confianza: {confianza:.0%}",
        severidad=sev)


async def feed_prescripcion(resumen: str, agentes_afectados: int):
    """Prescripción del Estratega."""
    await publicar(
        "organismo_prescripcion", "💊",
        f"Prescripción Nivel 1",
        f"{resumen[:200]}. {agentes_afectados} agentes afectados.",
        severidad="info")


async def feed_recompilacion(agentes: list[str], cambios_estruct: int):
    """Recompilador modificó agentes."""
    nombres = ", ".join(agentes[:5])
    titulo = "Agentes reconfigurados" if cambios_estruct == 0 else "Recompilación + cambios estructurales pendientes CR1"
    sev = "info" if cambios_estruct == 0 else "warning"
    await publicar("organismo_recompilacion", "🔧", titulo,
                   f"Modificados: {nombres}", severidad=sev)


async def feed_vigia_alerta(tipo_alerta: str, detalle: str):
    """Vigía detectó un problema."""
    await publicar("organismo_vigia", "👁️", f"Vigía: {tipo_alerta}",
                   detalle[:200], severidad="warning")


async def feed_mecanico_fix(tipo_fix: str, detalle: str):
    """Mecánico reparó algo."""
    await publicar("organismo_mecanico", "🔨", f"Mecánico: {tipo_fix}",
                   detalle[:200], severidad="success")


async def feed_autofago(funciones_huerfanas: int, propuestas: int):
    """Autófago ejecutó la poda mensual."""
    await publicar("organismo_autofago", "♻️",
                   f"Autofagia mensual completada",
                   f"{funciones_huerfanas} funciones huérfanas, {propuestas} propuestas registradas.",
                   severidad="info")
