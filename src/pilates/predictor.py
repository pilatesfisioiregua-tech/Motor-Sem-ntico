"""Predictor — Modelos predictivos basados en patrones del organismo.

No usa ML complejo — usa reglas + patrones de pizarra evolución.
Los patrones vienen de Memoria (F5) que detecta estacionalidad/recurrencia.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta
from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


async def predecir_abandonos() -> list[dict]:
    """Predice qué clientes van a abandonar en las próximas 3 semanas.

    Factores:
    1. Asistencia decreciente (últimas 4 semanas)
    2. Patrones estacionales (de pizarra evolución)
    3. Deuda acumulada
    4. Engagement score bajando
    5. Cancelaciones recientes
    """
    pool = await get_pool()
    predicciones = []
    hoy = date.today()

    async with pool.acquire() as conn:
        # Clientes activos con métricas
        clientes = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, ct.engagement_score,
                   ct.racha_actual, ct.frecuencia_semanal
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            WHERE ct.estado = 'activo'
        """, TENANT)

        for cl in clientes:
            factores = []
            prob = 0.0

            # 1. Asistencia últimas 4 semanas
            hace_4sem = hoy - timedelta(weeks=4)
            hace_2sem = hoy - timedelta(weeks=2)
            asist_4sem = await conn.fetchval("""
                SELECT count(*) FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = $1 AND s.fecha >= $2 AND a.estado = 'asistio'
            """, cl["id"], hace_4sem) or 0
            asist_2sem = await conn.fetchval("""
                SELECT count(*) FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = $1 AND s.fecha >= $2 AND a.estado = 'asistio'
            """, cl["id"], hace_2sem) or 0

            if asist_4sem > 0 and asist_2sem == 0:
                prob += 0.4
                factores.append("0 asistencias últimas 2 semanas")
            elif asist_4sem > 0 and asist_2sem < asist_4sem * 0.3:
                prob += 0.25
                factores.append("Asistencia cayendo >70%")

            # 2. Deuda acumulada
            deuda = await conn.fetchval("""
                SELECT COALESCE(SUM(total), 0) FROM om_cargos
                WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
            """, cl["id"], TENANT) or 0
            if float(deuda) > 100:
                prob += 0.2
                factores.append(f"Deuda {float(deuda):.0f}€")

            # 3. Engagement bajando
            engagement = cl["engagement_score"] or 50
            if engagement < 30:
                prob += 0.15
                factores.append(f"Engagement bajo: {engagement}")

            # 4. Racha rota
            if (cl["racha_actual"] or 0) == 0 and (cl["frecuencia_semanal"] or 0) >= 1:
                prob += 0.1
                factores.append("Racha rota (frecuencia habitual >= 1/sem)")

            # Solo reportar si probabilidad significativa
            if prob >= 0.3:
                predicciones.append({
                    "cliente_id": str(cl["id"]),
                    "nombre": f"{cl['nombre']} {cl['apellidos'] or ''}".strip(),
                    "probabilidad": round(min(prob, 0.95), 2),
                    "factores": factores,
                    "accion_preventiva": _sugerir_accion(factores, engagement),
                })

    predicciones.sort(key=lambda x: x["probabilidad"], reverse=True)
    log.info("predictor_abandonos", total=len(predicciones))
    return predicciones[:10]


def _sugerir_accion(factores: list, engagement: int) -> str:
    if any("Deuda" in f for f in factores):
        return "Contactar para plan de pago flexible"
    if any("0 asistencias" in f for f in factores):
        return "WA personal preguntando si todo bien"
    if engagement < 30:
        return "Sesión individual de cortesía para reconectar"
    return "Seguimiento personal por WA"


async def predecir_demanda_semana() -> dict:
    """Predice sesiones esperadas la próxima semana.

    Cruza: calendario, cancelaciones históricas del mismo periodo.
    """
    pool = await get_pool()
    hoy = date.today()
    lunes_prox = hoy + timedelta(days=(7 - hoy.weekday()))

    async with pool.acquire() as conn:
        # Sesiones programadas
        programadas = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id = $1 AND fecha >= $2 AND fecha < $2 + 7
        """, TENANT, lunes_prox) or 0

        # Tasa cancelación últimas 4 semanas
        hace_4sem = hoy - timedelta(weeks=4)
        total_4sem = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE s.tenant_id = $1 AND s.fecha >= $2
        """, TENANT, hace_4sem) or 1
        canceladas_4sem = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE s.tenant_id = $1 AND s.fecha >= $2 AND a.estado IN ('no_asistio', 'cancelada')
        """, TENANT, hace_4sem) or 0

        tasa_cancel = canceladas_4sem / max(total_4sem, 1)
        estimadas = round(programadas * (1 - tasa_cancel))

    log.info("predictor_demanda", programadas=programadas, estimadas=estimadas, tasa_cancel=round(tasa_cancel, 2))
    return {
        "semana": str(lunes_prox),
        "programadas": programadas,
        "tasa_cancelacion": round(tasa_cancel, 2),
        "sesiones_estimadas": estimadas,
    }


async def predecir_cashflow_mes() -> dict:
    """Predice cobros esperados vs gastos fijos."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Contratos activos
        contratos = await conn.fetch("""
            SELECT importe FROM om_pago_recurrente
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT)
        ingresos_recurrentes = sum(float(c["importe"]) for c in contratos)

        # Cargos pendientes
        pendientes = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT) or 0

    gastos_fijos = 300  # Alquiler + infra (configurable)
    gastos_llm = 15     # Presupuesto LLM mensual
    gap = ingresos_recurrentes - gastos_fijos - gastos_llm
    alerta = gap < gastos_fijos * 0.2

    return {
        "ingresos_recurrentes": round(ingresos_recurrentes, 2),
        "pendientes_cobro": round(float(pendientes), 2),
        "gastos_estimados": gastos_fijos + gastos_llm,
        "gap": round(gap, 2),
        "alerta_gap": alerta,
    }
