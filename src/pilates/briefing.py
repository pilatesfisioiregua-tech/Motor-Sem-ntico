"""Generador de Briefing Semanal — Authentic Pilates.

Produce un resumen ejecutivo con: números, tendencias, alertas, ACD.
Se genera cada lunes (cron) o bajo demanda.

Fuente: Exocortex v2.1 S17.4.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta
from typing import Optional

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def generar_briefing(semana_inicio: Optional[date] = None) -> dict:
    """Genera briefing semanal completo.

    Args:
        semana_inicio: Lunes de la semana a analizar. Default: lunes pasado.

    Returns:
        Dict con secciones: numeros, asistencia, financiero, alertas, acd, acciones.
    """
    if semana_inicio is None:
        hoy = date.today()
        semana_inicio = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
        if hoy.weekday() == 0:  # Si es lunes, semana pasada
            semana_inicio -= timedelta(weeks=1)

    semana_fin = semana_inicio + timedelta(days=6)
    mes_actual = date.today().replace(day=1)

    pool = await _get_pool()
    async with pool.acquire() as conn:

        # === NÚMEROS SEMANA ===
        sesiones_semana = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id = $1 AND fecha >= $2 AND fecha <= $3
        """, TENANT, semana_inicio, semana_fin)

        asistencias = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistidas,
                count(*) FILTER (WHERE a.estado = 'no_vino') as faltas,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
        """, TENANT, semana_inicio, semana_fin)

        pct_asistencia = round(
            (asistencias["asistidas"] or 0) / max(asistencias["total"] or 1, 1) * 100, 1
        )

        # === FINANCIERO SEMANA ===
        ingresos_semana = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago <= $3
        """, TENANT, semana_inicio, semana_fin)

        # === FINANCIERO MES (acumulado) ===
        import calendar
        ultimo_dia_mes = mes_actual.replace(
            day=calendar.monthrange(mes_actual.year, mes_actual.month)[1])

        ingresos_mes = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago <= $3
        """, TENANT, mes_actual, ultimo_dia_mes)

        deuda_total = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)

        # === OCUPACIÓN ===
        ocupacion = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(g.capacidad_max), 0) as plazas_totales,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.tenant_id = $1 AND c.tipo = 'grupo' AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
        """, TENANT)

        pct_ocupacion = round(
            (ocupacion["ocupadas"] or 0) / max(ocupacion["plazas_totales"] or 1, 1) * 100, 1
        )

        # === CLIENTES ===
        clientes_activos = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT)

        nuevos_semana = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_alta >= $2 AND fecha_alta <= $3
        """, TENANT, semana_inicio, semana_fin)

        bajas_semana = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_baja >= $2 AND fecha_baja <= $3
        """, TENANT, semana_inicio, semana_fin)

        # === ALERTAS ===
        from src.pilates.automatismos import detectar_alertas_retencion
        alertas_result = await detectar_alertas_retencion()
        alertas = alertas_result.get("alertas", [])

        # === TOP DEUDORES ===
        deudores = await conn.fetch("""
            SELECT c.cliente_id, cl.nombre, cl.apellidos,
                   SUM(c.total) as deuda,
                   MIN(c.fecha_cargo) as desde
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE c.tenant_id = $1 AND c.estado = 'pendiente'
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
            ORDER BY deuda DESC
            LIMIT 5
        """, TENANT)

        # === TENDENCIA ASISTENCIA (4 semanas) ===
        tendencia = []
        for i in range(4):
            sem_ini = semana_inicio - timedelta(weeks=i)
            sem_fin = sem_ini + timedelta(days=6)
            row = await conn.fetchrow("""
                SELECT
                    count(*) as total,
                    count(*) FILTER (WHERE a.estado = 'asistio') as asistidas
                FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
            """, TENANT, sem_ini, sem_fin)
            pct = round((row["asistidas"] or 0) / max(row["total"] or 1, 1) * 100, 1)
            tendencia.append({
                "semana": str(sem_ini),
                "asistencia_pct": pct,
                "total": row["total"],
                "asistidas": row["asistidas"],
            })

        # === DIAGNÓSTICO ACD (último disponible) ===
        ultimo_acd = await conn.fetchrow("""
            SELECT * FROM om_diagnosticos_tenant
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        # Propuestas Voz pendientes
        voz_pendientes = await conn.fetchval("""
            SELECT count(*) FROM om_voz_propuestas
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)

    # Construir briefing
    briefing = {
        "semana": f"{semana_inicio} a {semana_fin}",
        "generado": str(date.today()),

        "numeros": {
            "sesiones_semana": sesiones_semana,
            "asistencia_total": asistencias["total"] or 0,
            "asistencia_asistidas": asistencias["asistidas"] or 0,
            "asistencia_faltas": asistencias["faltas"] or 0,
            "asistencia_canceladas": asistencias["canceladas"] or 0,
            "asistencia_pct": pct_asistencia,
            "clientes_activos": clientes_activos,
            "nuevos_semana": nuevos_semana,
            "bajas_semana": bajas_semana,
        },

        "financiero": {
            "ingresos_semana": float(ingresos_semana),
            "ingresos_mes_acumulado": float(ingresos_mes),
            "deuda_pendiente": float(deuda_total),
            "top_deudores": [
                {"nombre": f"{d['nombre']} {d['apellidos']}",
                 "deuda": float(d["deuda"]),
                 "desde": str(d["desde"])}
                for d in deudores
            ],
        },

        "ocupacion": {
            "plazas_totales": ocupacion["plazas_totales"],
            "plazas_ocupadas": ocupacion["ocupadas"],
            "pct": pct_ocupacion,
        },

        "tendencia_asistencia": list(reversed(tendencia)),

        "alertas": alertas[:10],
        "total_alertas": len(alertas),

        "acd": {
            "tiene_diagnostico": ultimo_acd is not None,
            "estado": ultimo_acd["estado"] if ultimo_acd else None,
            "estado_tipo": ultimo_acd["estado_tipo"] if ultimo_acd else None,
            "lentes": dict(ultimo_acd["lentes"]) if ultimo_acd and ultimo_acd.get("lentes") else None,
            "gap": float(ultimo_acd["gap"]) if ultimo_acd and ultimo_acd.get("gap") else None,
            "prescripcion": dict(ultimo_acd["prescripcion"]) if ultimo_acd and ultimo_acd.get("prescripcion") else None,
            "fecha": str(ultimo_acd["created_at"].date()) if ultimo_acd else None,
        },

        "voz_propuestas_pendientes": voz_pendientes,
    }

    # Generar texto para WA
    briefing["texto_wa"] = _generar_texto_wa(briefing)

    log.info("briefing_generado", semana=str(semana_inicio))
    return briefing


def _generar_texto_wa(b: dict) -> str:
    """Genera versión texto del briefing para enviar por WhatsApp."""
    n = b["numeros"]
    f = b["financiero"]
    o = b["ocupacion"]
    acd = b["acd"]

    texto = f"""*Briefing Semanal — Authentic Pilates*
_{b['semana']}_

*Asistencia:* {n['asistencia_pct']}% ({n['asistencia_asistidas']}/{n['asistencia_total']})
Faltas: {n['asistencia_faltas']} · Cancelaciones: {n['asistencia_canceladas']}

*Financiero:*
Ingresos semana: {f['ingresos_semana']:.0f}€
Ingresos mes: {f['ingresos_mes_acumulado']:.0f}€
Deuda pendiente: {f['deuda_pendiente']:.0f}€

*Ocupación:* {o['pct']}% ({o['plazas_ocupadas']}/{o['plazas_totales']} plazas)
Clientes: {n['clientes_activos']} activos ({'+' if n['nuevos_semana'] > 0 else ''}{n['nuevos_semana']} nuevos, -{n['bajas_semana']} bajas)
"""

    if b["total_alertas"] > 0:
        texto += f"\n⚠️ *{b['total_alertas']} alertas* de retención"

    if acd["tiene_diagnostico"]:
        texto += f"""

*Diagnóstico ACD:*
Estado: {acd['estado']} ({acd['estado_tipo']})"""
        if acd["lentes"]:
            texto += f"\nLentes: S={acd['lentes'].get('S','?')} Se={acd['lentes'].get('Se','?')} C={acd['lentes'].get('C','?')}"
        if acd["gap"]:
            texto += f" (gap={acd['gap']:.3f})"
        if acd["prescripcion"] and acd["prescripcion"].get("objetivo"):
            texto += f"\nObjetivo: {acd['prescripcion']['objetivo']}"

    return texto


async def generar_diagnostico_acd_tenant() -> dict:
    """Genera un diagnóstico ACD fresco del negocio usando datos reales.

    Lee om_grupos, om_contratos, om_sesiones, om_cargos, om_adn, om_procesos
    y construye un caso textual para el evaluador funcional del Motor vN.

    Returns: dict con diagnóstico completo almacenado en om_diagnosticos_tenant.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'", TENANT)
        grupos = await conn.fetchval(
            "SELECT count(*) FROM om_grupos WHERE tenant_id=$1 AND estado='activo'", TENANT)
        contratos_grupo = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id=$1 AND tipo='grupo' AND estado='activo'", TENANT)
        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT)
        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id=$1", TENANT)
        adn = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true", TENANT)
        onboarding = await conn.fetchval(
            "SELECT count(*) FROM om_onboarding_instructor WHERE tenant_id=$1", TENANT)

        ocupacion = await conn.fetchrow("""
            SELECT COALESCE(SUM(capacidad_max),0) as total,
                (SELECT count(*) FROM om_contratos WHERE tenant_id=$1 AND tipo='grupo' AND estado='activo') as ocu
            FROM om_grupos WHERE tenant_id=$1 AND estado='activo'
        """, TENANT)
        pct_ocu = round((ocupacion["ocu"] or 0) / max(ocupacion["total"] or 1, 1) * 100, 0)

    # Construir caso textual
    caso = (
        f"Estudio de Pilates reformer en Logroño. {clientes} clientes activos, "
        f"{grupos} grupos activos, {pct_ocu}% ocupación. "
        f"Factura {float(ingresos):.0f}€/mes. "
        f"Operado por un único instructor-dueño (Jesús). "
        f"{'Sin' if procesos == 0 else f'{procesos}'} procesos documentados. "
        f"{'Sin' if adn == 0 else f'{adn}'} principios ADN codificados. "
        f"{'Sin' if onboarding == 0 else f'{onboarding}'} onboarding instructor registrado. "
        f"Todo el conocimiento tácito reside en el dueño."
    )

    # Ejecutar pipeline ACD
    try:
        from src.tcf.evaluador_funcional import evaluar_funcional
        vector_result = await evaluar_funcional(caso)

        from src.tcf.diagnostico import diagnosticar
        diag = await diagnosticar(caso)

        prescripcion_dict = None
        if hasattr(diag, 'estado') and hasattr(diag.estado, 'tipo') and diag.estado.tipo == 'desequilibrado':
            from src.tcf.prescriptor import prescribir
            presc = prescribir(diag)
            prescripcion_dict = {
                'ints': presc.ints, 'ps': presc.ps, 'rs': presc.rs,
                'secuencia': presc.secuencia, 'frenar': presc.frenar,
                'lente_objetivo': presc.lente_objetivo,
                'objetivo': presc.objetivo,
            }

        # Almacenar en om_diagnosticos_tenant
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO om_diagnosticos_tenant (
                    tenant_id, trigger, vector_funcional, lentes,
                    gradiente, gap, estado, estado_tipo,
                    perfil_lentes, repertorio, prescripcion,
                    resultado, coste_usd
                ) VALUES ($1, 'manual', $2::jsonb, $3::jsonb,
                    $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb,
                    'pendiente', $11)
                RETURNING id, created_at
            """, TENANT,
                vector_result.vector.to_dict() if hasattr(vector_result, 'vector') and hasattr(vector_result.vector, 'to_dict') else {},
                diag.estado_campo.lentes if hasattr(diag, 'estado_campo') else {},
                diag.estado_campo.gradiente if hasattr(diag, 'estado_campo') else 0,
                diag.estado_campo.gap if hasattr(diag, 'estado_campo') else 0,
                diag.estado.id if hasattr(diag.estado, 'id') else str(diag.estado),
                diag.estado.tipo if hasattr(diag.estado, 'tipo') else 'desconocido',
                str(diag.estado_campo.perfil) if hasattr(diag, 'estado_campo') else '',
                {},  # repertorio
                prescripcion_dict,
                (vector_result.coste_usd if hasattr(vector_result, 'coste_usd') else 0) +
                (diag.coste_usd if hasattr(diag, 'coste_usd') else 0),
            )

        log.info("acd_tenant_diagnostico",
                 estado=diag.estado.id if hasattr(diag.estado, 'id') else '?')

        return {
            "status": "ok",
            "diagnostico_id": str(row["id"]),
            "estado": diag.estado.id if hasattr(diag.estado, 'id') else str(diag.estado),
            "lentes": diag.estado_campo.lentes if hasattr(diag, 'estado_campo') else {},
            "prescripcion": prescripcion_dict,
        }

    except Exception as e:
        log.error("acd_tenant_error", error=str(e))
        return {"status": "error", "detail": str(e)}
