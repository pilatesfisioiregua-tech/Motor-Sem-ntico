"""AF3 Depuración — Agente funcional: eliminar lo que no aporta.

F3 es el diferenciador clave de OMNI-MIND: "Todo el mercado vende 'haz más.'
OMNI-MIND es el único que dice 'deja de hacer esto.'"

Ejecuta semanalmente. Analiza eficiencia de sesiones, horarios y servicios.
Emite ALERTA + VETO al bus cuando detecta algo que se debería eliminar.

Detecciones:
  1. Sesiones grupo infrautilizadas: <3 alumnos media en últimas 4 semanas
  2. Horarios vacíos: franjas con 0-1 sesiones programadas en 4 semanas
  3. Contratos zombi: activos pero sin asistencia ni pago en 6+ semanas

Señal VETO: cuando AF3 detecta algo que debe cerrarse, emite VETO que
otros AF (especialmente AF2 Captación) deben respetar. No tiene sentido
captar clientes para un horario que deberías cerrar.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
ORIGEN = "AF3"

INSTRUCCION_AF3 = """Analiza grupos y contratos ineficientes.
Para grupos infrautilizados: ¿cuáles fusionar entre sí? ¿cuáles cerrar?
¿cuáles cambiar de horario? Razona compatibilidad de alumnos y horarios.
Para zombis: ¿llamar o dar de baja? Calcula impacto en ingresos de cada decisión.
Di claramente QUÉ CORTAR y por qué."""


async def _detectar_grupos_infrautilizados() -> list[dict]:
    """Grupos con media <3 alumnos en las últimas 4 semanas."""
    pool = await get_pool()
    hace_4_sem = date.today() - timedelta(weeks=4)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.nombre, g.dias_semana, g.capacidad_max,
                   count(DISTINCT s.id) as sesiones_periodo,
                   COALESCE(AVG(asist_count.n), 0) as media_asistentes
            FROM om_grupos g
            JOIN om_sesiones s ON s.grupo_id = g.id AND s.fecha >= $2
            LEFT JOIN LATERAL (
                SELECT count(*) as n FROM om_asistencias a
                WHERE a.sesion_id = s.id AND a.estado = 'asistio'
            ) asist_count ON true
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            GROUP BY g.id, g.nombre, g.dias_semana, g.capacidad_max
            HAVING COALESCE(AVG(asist_count.n), 0) < 3
        """, TENANT, hace_4_sem)

    return [{
        "tipo": "grupo_infrautilizado",
        "grupo_id": str(r["id"]),
        "nombre": r["nombre"],
        "horario": r["dias_semana"],  # JSONB con días y horas
        "capacidad": r["capacidad_max"],
        "media_asistentes": round(float(r["media_asistentes"]), 1),
        "sesiones_periodo": r["sesiones_periodo"],
        "ocupacion_pct": round(float(r["media_asistentes"]) / max(r["capacidad_max"], 1) * 100),
    } for r in rows]


async def _detectar_contratos_zombi() -> list[dict]:
    """Contratos activos sin asistencia ni pago en 6+ semanas."""
    pool = await get_pool()
    hace_6_sem = date.today() - timedelta(weeks=6)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT co.id as contrato_id, co.tipo, co.precio_mensual, co.precio_sesion,
                   c.id as cliente_id, c.nombre, c.apellidos,
                   (SELECT MAX(s.fecha) FROM om_asistencias a
                    JOIN om_sesiones s ON s.id = a.sesion_id
                    WHERE a.cliente_id = c.id AND a.estado = 'asistio') as ultima_asistencia,
                   (SELECT MAX(p.fecha_pago) FROM om_pagos p
                    WHERE p.cliente_id = c.id AND p.tenant_id = $1) as ultimo_pago
            FROM om_contratos co
            JOIN om_clientes c ON c.id = co.cliente_id
            WHERE co.tenant_id = $1 AND co.estado = 'activo'
            AND NOT EXISTS (
                SELECT 1 FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = c.id AND s.fecha >= $2
            )
            AND NOT EXISTS (
                SELECT 1 FROM om_pagos p
                WHERE p.cliente_id = c.id AND p.tenant_id = $1 AND p.fecha_pago >= $2
            )
        """, TENANT, hace_6_sem)

    return [{
        "tipo": "contrato_zombi",
        "contrato_id": str(r["contrato_id"]),
        "cliente_id": str(r["cliente_id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "contrato_tipo": r["tipo"],
        "ultima_asistencia": str(r["ultima_asistencia"]) if r["ultima_asistencia"] else "nunca",
        "ultimo_pago": str(r["ultimo_pago"]) if r["ultimo_pago"] else "nunca",
    } for r in rows]


async def ejecutar_af3() -> dict:
    """Ejecuta AF3 Depuración: detecta ineficiencias, razona con LLM, emite al bus.

    Returns dict con resumen + razonamiento.
    """
    log.info("af3_inicio")

    # === SENSORES (código puro) ===
    grupos = await _detectar_grupos_infrautilizados()
    zombis = await _detectar_contratos_zombi()

    datos_sensor = {
        "grupos_infrautilizados": grupos,
        "contratos_zombi": zombis,
    }

    # === CEREBRO (NIVEL 1: gpt-4o — razonamiento de negocio) ===
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="AF3",
        funcion="F3 Depuración",
        datos_detectados=datos_sensor,
        instruccion_especifica=INSTRUCCION_AF3,
        nivel=1,
    )

    # === EMISIÓN AL BUS ===
    from src.pilates.bus import emitir
    alertas_emitidas = 0
    vetos_emitidos = 0

    # Prescripciones razonadas del cerebro
    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", ORIGEN, {
                "funcion": "F3",
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
            log.warning("af3_bus_error", error=str(e))

    # VETOs para grupos <30% ocupación (determinista, no LLM)
    for g in grupos:
        if g["ocupacion_pct"] < 30:
            try:
                await emitir("PRESCRIPCION", ORIGEN, {
                    "subtipo": "VETO",
                    "objeto": f"grupo:{g['grupo_id']}",
                    "razon": f"Grupo '{g['nombre']}' a {g['ocupacion_pct']}% ocupación. No captar para este horario.",
                    "funcion": "F3",
                    "bloquea_af": ["AF2"],
                }, prioridad=2)
                vetos_emitidos += 1
            except Exception as e:
                log.warning("af3_veto_error", error=str(e))

    if razonamiento.get("alerta_critica"):
        try:
            await emitir("ALERTA", ORIGEN, {
                "funcion": "F3",
                "alerta_critica": razonamiento["alerta_critica"],
                "urgente": True,
            }, prioridad=1)
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af3_alerta_critica_error", error=str(e))

    resultado = {
        "grupos_infrautilizados": len(grupos),
        "contratos_zombi": len(zombis),
        "total_detecciones": len(grupos) + len(zombis),
        "alertas_emitidas": alertas_emitidas,
        "vetos_emitidos": vetos_emitidos,
        "razonamiento": razonamiento,
        "detalle_grupos": grupos[:10],
        "detalle_zombis": zombis[:10],
    }

    # Publicar al feed
    try:
        from src.pilates.feed import feed_af_veto, feed_af_deteccion
        for det in (grupos + zombis)[:5]:
            await feed_af_deteccion("AF3", det.get("tipo", "ineficiencia"),
                                     det.get("nombre", det.get("tipo", "")))
        for g in grupos:
            if g["ocupacion_pct"] < 30:
                await feed_af_veto("AF3", "AF2",
                                    f"Grupo '{g['nombre']}' a {g['ocupacion_pct']}% — no captar")
    except Exception as e:
        log.warning("af3_feed_error", error=str(e))

    log.info("af3_completo", grupos=len(grupos), zombis=len(zombis),
        vetos=vetos_emitidos, acciones_cerebro=len(razonamiento.get("acciones", [])))
    return resultado
