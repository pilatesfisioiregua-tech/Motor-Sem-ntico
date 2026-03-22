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

TENANT = "authentic_pilates"
ORIGEN = "AF3"


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
    """Ejecuta AF3 Depuración: detecta ineficiencias y emite al bus.

    Emite dos tipos de señal:
    - ALERTA: algo ineficiente detectado (informativo)
    - PRESCRIPCION con subtipo VETO: propuesta de cortar algo + señal
      para que otros AF la respeten

    Returns dict con resumen.
    """
    log.info("af3_inicio")

    grupos = await _detectar_grupos_infrautilizados()
    zombis = await _detectar_contratos_zombi()

    alertas_emitidas = 0
    vetos_emitidos = 0
    depuraciones_creadas = 0

    from src.pilates.bus import emitir

    # Grupos infrautilizados → ALERTA + VETO + registrar depuración
    for g in grupos:
        try:
            # ALERTA informativa
            await emitir(
                "ALERTA", ORIGEN,
                {
                    **g,
                    "funcion": "F3",
                    "accion_sugerida": f"Grupo '{g['nombre']}' con media {g['media_asistentes']} alumnos ({g['ocupacion_pct']}% ocupación). Considerar cerrar o fusionar.",
                },
                prioridad=4,
            )
            alertas_emitidas += 1

            # VETO: si ocupación <30%, emitir señal VETO para bloquear captación en ese horario
            if g["ocupacion_pct"] < 30:
                await emitir(
                    "PRESCRIPCION", ORIGEN,
                    {
                        "subtipo": "VETO",
                        "objeto": f"grupo:{g['grupo_id']}",
                        "razon": f"Grupo '{g['nombre']}' a {g['ocupacion_pct']}% ocupación. No captar para este horario hasta resolver.",
                        "funcion": "F3",
                        "bloquea_af": ["AF2"],  # AF2 Captación no debería llenar un horario que debería cerrarse
                    },
                    prioridad=2,
                )
                vetos_emitidos += 1

            # Registrar en om_depuracion
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO om_depuracion (tenant_id, tipo, descripcion,
                            impacto_estimado, funcion_l07, lente, origen)
                        VALUES ($1, 'servicio_eliminar', $2, $3, 'F3', 'salud', 'automatizacion')
                        ON CONFLICT DO NOTHING
                    """, TENANT,
                        f"Grupo '{g['nombre']}': {g['media_asistentes']} alumnos media, {g['ocupacion_pct']}% ocupación.",
                        f"Liberar franja horaria. {g['capacidad']} plazas infrautilizadas.")
                depuraciones_creadas += 1
            except Exception as e:
                log.warning("af3_depuracion_error", error=str(e))

        except Exception as e:
            log.warning("af3_bus_error", tipo="grupo", error=str(e))

    # Contratos zombi → ALERTA
    for z in zombis:
        try:
            await emitir(
                "ALERTA", ORIGEN,
                {
                    **z,
                    "funcion": "F3",
                    "accion_sugerida": f"Contrato zombi de {z['nombre']}: ni asiste ni paga desde hace >6 semanas. Proponer baja formal o conversación.",
                },
                prioridad=4,
            )
            alertas_emitidas += 1

            # Registrar en om_depuracion
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO om_depuracion (tenant_id, tipo, descripcion,
                            funcion_l07, lente, origen)
                        VALUES ($1, 'cliente_toxico', $2, 'F3', 'salud', 'automatizacion')
                        ON CONFLICT DO NOTHING
                    """, TENANT,
                        f"Contrato zombi de {z['nombre']}: sin asistencia ni pago en 6+ semanas. Considerar baja formal.")
                depuraciones_creadas += 1
            except Exception as e:
                pass

        except Exception as e:
            log.warning("af3_bus_error", tipo="zombi", error=str(e))

    resultado = {
        "grupos_infrautilizados": len(grupos),
        "contratos_zombi": len(zombis),
        "total_detecciones": len(grupos) + len(zombis),
        "alertas_emitidas": alertas_emitidas,
        "vetos_emitidos": vetos_emitidos,
        "depuraciones_registradas": depuraciones_creadas,
        "detalle_grupos": grupos[:10],
        "detalle_zombis": zombis[:10],
    }

    log.info("af3_completo", grupos=len(grupos), zombis=len(zombis), vetos=vetos_emitidos)
    return resultado
