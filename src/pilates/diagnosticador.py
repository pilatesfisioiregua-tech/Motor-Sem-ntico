"""Diagnosticador autónomo — Agente G2: datos reales → diagnóstico ACD.

Ejecuta semanalmente (lunes) en cron.
Recopila métricas reales de Authentic Pilates → calcula lentes → clasifica estado → persiste → señal si cambio.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool, log_diagnostico
from src.tcf.diagnostico import clasificar_estado

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "DIAGNOSTICADOR"


async def _recopilar_metricas() -> dict:
    """Recopila métricas reales de las últimas 4 semanas."""
    pool = await get_pool()
    ahora = datetime.now(timezone.utc)
    hace_4_sem = ahora - timedelta(weeks=4)

    async with pool.acquire() as conn:
        total_activos = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id = $1 AND estado = 'activo'",
            TENANT) or 0

        bajas_periodo = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id = $1 AND estado = 'cancelado' AND updated_at >= $2",
            TENANT, hace_4_sem) or 0

        nuevos_clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id = $1 AND fecha_alta >= $2::date",
            TENANT, hace_4_sem.date()) or 0

        sesiones_grupo = await conn.fetchval(
            "SELECT count(*) FROM om_sesiones WHERE tenant_id = $1 AND tipo = 'grupo' AND fecha >= $2::date",
            TENANT, hace_4_sem.date()) or 0

        sesiones_bajas = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones s
            WHERE s.tenant_id = $1 AND s.tipo = 'grupo' AND s.fecha >= $2::date
            AND (SELECT count(*) FROM om_asistencias a WHERE a.sesion_id = s.id AND a.estado = 'asistio') < 3
        """, TENANT, hace_4_sem.date()) or 0

        total_asistencias = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON a.sesion_id = s.id
            WHERE s.tenant_id = $1 AND s.fecha >= $2::date AND a.estado = 'asistio'
        """, TENANT, hace_4_sem.date()) or 0

        try:
            senales_voz = await conn.fetchval(
                "SELECT count(*) FROM om_voz_senales WHERE tenant_id = $1 AND created_at >= $2",
                TENANT, hace_4_sem) or 0
        except Exception:
            senales_voz = 0

        try:
            tensiones = await conn.fetchval(
                "SELECT count(*) FROM om_voz_tensiones WHERE tenant_id = $1 AND created_at >= $2",
                TENANT, hace_4_sem) or 0
        except Exception:
            tensiones = 0

        try:
            procesos = await conn.fetchval(
                "SELECT count(*) FROM om_voz_adn_procesos WHERE tenant_id = $1",
                TENANT) or 0
        except Exception:
            procesos = 0

        cobrado = await conn.fetchval("""
            SELECT COALESCE(sum(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, hace_4_sem) or 0

        pendiente = await conn.fetchval("""
            SELECT COALESCE(sum(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT) or 0

    return {
        "total_activos": total_activos,
        "bajas_periodo": bajas_periodo,
        "nuevos_clientes": nuevos_clientes,
        "sesiones_grupo": sesiones_grupo,
        "sesiones_bajas": sesiones_bajas,
        "total_asistencias": total_asistencias,
        "senales_voz": senales_voz,
        "tensiones": tensiones,
        "procesos": procesos,
        "cobrado": float(cobrado),
        "pendiente": float(pendiente),
    }


def _metricas_a_lentes(m: dict) -> dict[str, float]:
    """Traduce métricas brutas a las 3 lentes ACD (0.0 a 1.0).

    Salud (S): F1 retención + F3 eficiencia + F4 distribución → ¿sobrevive?
    Sentido (Se): F2 captación + F5 identidad + F6 adaptación → ¿tiene propósito?
    Continuidad (C): F7 replicación + cobros + documentación → ¿puede transferirse?
    """
    tasa_retencion = max(0.0, min(1.0, 1.0 - (m["bajas_periodo"] / max(m["total_activos"], 1))))
    eficiencia = max(0.0, min(1.0, 1.0 - (m["sesiones_bajas"] / max(m["sesiones_grupo"], 1))))
    asist_media = m["total_asistencias"] / max(m["sesiones_grupo"], 1)
    distribucion = min(1.0, asist_media / 6.0)

    captacion = min(1.0, m["nuevos_clientes"] / max(m["total_activos"] * 0.1, 1))
    identidad = min(1.0, m["senales_voz"] / 20.0)
    adaptacion = min(1.0, m["tensiones"] / 5.0)

    replicacion = min(1.0, m["procesos"] / 10.0)
    cobro_ratio = m["cobrado"] / max(m["cobrado"] + m["pendiente"], 1)

    salud = (tasa_retencion * 0.4 + eficiencia * 0.3 + distribucion * 0.3)
    sentido = (captacion * 0.3 + identidad * 0.4 + adaptacion * 0.3)
    continuidad = (replicacion * 0.4 + cobro_ratio * 0.4 + min(1.0, m["procesos"] / 15.0) * 0.2)

    return {
        "salud": round(salud, 3),
        "sentido": round(sentido, 3),
        "continuidad": round(continuidad, 3),
    }


def _metricas_a_vector_f(m: dict) -> dict[str, float]:
    """Traduce métricas a vector funcional F1-F7."""
    return {
        "F1": round(max(0, min(1, 1.0 - (m["bajas_periodo"] / max(m["total_activos"], 1)))), 3),
        "F2": round(max(0, min(1, m["nuevos_clientes"] / max(m["total_activos"] * 0.1, 1))), 3),
        "F3": round(max(0, min(1, 1.0 - (m["sesiones_bajas"] / max(m["sesiones_grupo"], 1)))), 3),
        "F4": round(max(0, min(1, (m["total_asistencias"] / max(m["sesiones_grupo"], 1)) / 6.0)), 3),
        "F5": round(max(0, min(1, m["senales_voz"] / 20.0)), 3),
        "F6": round(max(0, min(1, m["tensiones"] / 5.0)), 3),
        "F7": round(max(0, min(1, m["procesos"] / 10.0)), 3),
    }


async def diagnosticar_tenant() -> dict:
    """Ejecuta diagnóstico ACD completo sobre datos reales."""
    # 1. Recopilar
    metricas = await _recopilar_metricas()
    log.info("diagnosticador_metricas", activos=metricas["total_activos"],
             bajas=metricas["bajas_periodo"], nuevos=metricas["nuevos_clientes"])

    # 2. Traducir a lentes
    lentes = _metricas_a_lentes(metricas)
    vector_f = _metricas_a_vector_f(metricas)
    log.info("diagnosticador_lentes", **lentes)

    # 3. Clasificar estado ACD
    estado = clasificar_estado(lentes)
    log.info("diagnosticador_estado", id=estado.id, nombre=estado.nombre, gap=estado.gap)

    # 4. Persistir diagnóstico
    diag_data = {
        "caso_input": f"Diagnóstico autónomo Authentic Pilates — {datetime.now(timezone.utc).isoformat()[:10]}",
        "vector_pre": json.dumps(vector_f),
        "lentes_pre": json.dumps(lentes),
        "estado_pre": estado.id,
        "flags_pre": [f.nombre for f in estado.flags] if estado.flags else [],
        "metricas": json.dumps({"raw": metricas}),
        "resultado": "pendiente",
    }
    diag_id = await log_diagnostico(diag_data)

    # 5. Comparar con último diagnóstico anterior
    cambio = False
    pool = await get_pool()
    async with pool.acquire() as conn:
        anterior = await conn.fetchrow("""
            SELECT estado_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC
            OFFSET 1 LIMIT 1
        """)
    if anterior and anterior["estado_pre"] != estado.id:
        cambio = True

    # 6. Emitir señal al bus si cambió o si hay flags
    if cambio or estado.flags:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "DIAGNOSTICO", ORIGEN,
                {
                    "estado": estado.id,
                    "nombre": estado.nombre,
                    "lentes": lentes,
                    "gap": estado.gap,
                    "flags": [f.nombre for f in estado.flags],
                    "cambio": cambio,
                    "anterior": anterior["estado_pre"] if anterior else None,
                    "diagnostico_id": diag_id,
                },
                prioridad=2 if cambio else 4,
            )
        except Exception as e:
            log.warning("diagnosticador_bus_error", error=str(e))

    resultado = {
        "diagnostico_id": diag_id,
        "estado": estado.id,
        "nombre": estado.nombre,
        "tipo": estado.tipo,
        "lentes": lentes,
        "vector_f": vector_f,
        "gap": estado.gap,
        "flags": [f.nombre for f in estado.flags],
        "cambio_vs_anterior": cambio,
        "metricas_raw": metricas,
    }

    log.info("diagnosticador_completo", estado=estado.id, cambio=cambio, flags=len(estado.flags))
    return resultado
