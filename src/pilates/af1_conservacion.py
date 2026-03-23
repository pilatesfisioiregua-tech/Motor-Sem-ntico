"""AF1 Conservación — Agente funcional: proteger lo que el negocio ya tiene.

Ejecuta semanalmente. Lee datos de asistencia, engagement y pagos.
Emite señales ALERTA al bus cuando detecta riesgo de pérdida.

Detecciones:
  1. Clientes fantasma: contrato activo pero 0 asistencias en 3+ semanas
  2. Engagement en caída: score bajó >15 puntos vs semana anterior
  3. Deuda silenciosa: cargos pendientes >60€ sin pago en 2+ semanas
  4. Racha rota: cliente que tenía racha >4 semanas y la rompió

Cada detección → ALERTA al bus con contexto completo para acción.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF1"

INSTRUCCION_AF1 = """Analiza los clientes en riesgo de pérdida.
Para cada cliente fantasma, deduce POR QUÉ puede haber dejado de venir
(lesión mejorada, vacaciones, insatisfacción, vergüenza, problemas de dinero)
y propón una acción DIFERENTE para cada caso.
Para engagement cayendo, identifica si es tendencia o evento puntual.
Para deuda silenciosa, evalúa si el cliente vale la pena retener o si
es mejor dejarlo ir.
Prioriza: ¿a quién salvar primero y cómo?"""


async def _detectar_fantasmas() -> list[dict]:
    """Clientes con contrato activo pero sin asistencia en 3+ semanas."""
    pool = await get_pool()
    hace_3_sem = date.today() - timedelta(weeks=3)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   co.tipo as contrato_tipo, co.id as contrato_id,
                   (SELECT MAX(s.fecha) FROM om_asistencias a
                    JOIN om_sesiones s ON s.id = a.sesion_id
                    WHERE a.cliente_id = c.id AND a.estado = 'asistio') as ultima_asistencia
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
            JOIN om_contratos co ON co.cliente_id = c.id AND co.tenant_id = $1 AND co.estado = 'activo'
            WHERE NOT EXISTS (
                SELECT 1 FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = c.id AND a.estado = 'asistio' AND s.fecha >= $2
            )
        """, TENANT, hace_3_sem)

    return [{
        "tipo": "cliente_fantasma",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "contrato_tipo": r["contrato_tipo"],
        "ultima_asistencia": str(r["ultima_asistencia"]) if r["ultima_asistencia"] else "nunca",
        "dias_sin_asistir": (date.today() - r["ultima_asistencia"]).days if r["ultima_asistencia"] else 999,
    } for r in rows]


async def _detectar_engagement_cayendo() -> list[dict]:
    """Clientes cuyo engagement score bajó >15 puntos."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Necesita om_cliente_perfil con engagement_score y engagement_anterior
        try:
            rows = await conn.fetch("""
                SELECT c.id, c.nombre, c.apellidos, c.telefono,
                       p.engagement_score, p.engagement_tendencia
                FROM om_cliente_perfil p
                JOIN om_clientes c ON c.id = p.cliente_id
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
                WHERE p.engagement_tendencia = 'bajando'
                AND p.engagement_score < 40
            """, TENANT)
        except Exception:
            return []

    return [{
        "tipo": "engagement_cayendo",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "score": r["engagement_score"],
        "tendencia": r["engagement_tendencia"],
    } for r in rows]


async def _detectar_deuda_silenciosa() -> list[dict]:
    """Clientes con deuda >60€ pendiente >2 semanas."""
    pool = await get_pool()
    hace_2_sem = date.today() - timedelta(weeks=2)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   SUM(ca.total) as deuda,
                   MIN(ca.fecha_cargo) as cargo_mas_antiguo
            FROM om_cargos ca
            JOIN om_clientes c ON c.id = ca.cliente_id
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
            WHERE ca.tenant_id = $1 AND ca.estado = 'pendiente'
            AND ca.fecha_cargo < $2
            GROUP BY c.id, c.nombre, c.apellidos, c.telefono
            HAVING SUM(ca.total) > 60
        """, TENANT, hace_2_sem)

    return [{
        "tipo": "deuda_silenciosa",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "deuda": float(r["deuda"]),
        "desde": str(r["cargo_mas_antiguo"]),
    } for r in rows]


async def ejecutar_af1() -> dict:
    """Ejecuta AF1 Conservación: detecta riesgos, razona con LLM, emite al bus.

    Returns dict con resumen de detecciones, razonamiento y alertas emitidas.
    """
    log.info("af1_inicio")

    # === SENSORES (código puro, sin cambios) ===
    fantasmas = await _detectar_fantasmas()
    engagement = await _detectar_engagement_cayendo()
    deuda = await _detectar_deuda_silenciosa()

    datos_sensor = {
        "fantasmas": fantasmas,
        "engagement_cayendo": engagement,
        "deuda_silenciosa": deuda,
    }

    # === CEREBRO (NIVEL 1: gpt-4o — razonamiento de negocio en español) ===
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="AF1",
        funcion="F1 Conservación",
        datos_detectados=datos_sensor,
        instruccion_especifica=INSTRUCCION_AF1,
        nivel=1,
    )

    # === EMISIÓN AL BUS (prescripciones razonadas) ===
    from src.pilates.bus import emitir
    alertas_emitidas = 0

    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", ORIGEN, {
                "funcion": "F1",
                "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 3),
                "impacto": accion.get("impacto", ""),
                "esfuerzo": accion.get("esfuerzo", ""),
                "cliente_id": accion.get("cliente_id"),
                "grupo_id": accion.get("grupo_id"),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 3))
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af1_bus_error", error=str(e))

    if razonamiento.get("alerta_critica"):
        try:
            await emitir("ALERTA", ORIGEN, {
                "funcion": "F1",
                "alerta_critica": razonamiento["alerta_critica"],
                "urgente": True,
            }, prioridad=1)
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af1_alerta_critica_error", error=str(e))

    resultado = {
        "fantasmas": len(fantasmas),
        "engagement_cayendo": len(engagement),
        "deuda_silenciosa": len(deuda),
        "total_riesgos": len(fantasmas) + len(engagement) + len(deuda),
        "alertas_emitidas": alertas_emitidas,
        "razonamiento": razonamiento,
        "detalle": (fantasmas + engagement + deuda)[:20],
    }

    log.info("af1_completo", fantasmas=len(fantasmas),
        engagement=len(engagement), deuda=len(deuda),
        acciones_cerebro=len(razonamiento.get("acciones", [])))
    return resultado


def _sugerir_accion(det: dict) -> str:
    """Sugiere acción concreta para cada tipo de riesgo."""
    tipo = det["tipo"]
    nombre = det.get("nombre", "")

    if tipo == "cliente_fantasma":
        dias = det.get("dias_sin_asistir", 0)
        if dias > 30:
            return f"URGENTE: {nombre} lleva {dias} días sin venir. Llamar hoy. Riesgo de baja."
        return f"{nombre} lleva {dias} días sin asistir. Enviar WA preguntando si está bien."

    if tipo == "engagement_cayendo":
        return f"{nombre} engagement en caída (score={det.get('score')}). Revisar si hay problema personal o insatisfacción."

    if tipo == "deuda_silenciosa":
        return f"{nombre} tiene €{det.get('deuda', 0):.0f} pendientes desde {det.get('desde')}. Enviar recordatorio amable."

    return "Revisar situación del cliente."
