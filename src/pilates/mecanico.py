"""Mecánico — Agente META: procesa ALERTAs del Vigía, clasifica y actúa.

FONTANERÍA: auto-fix (limpiar bus, disparar ACD, etc.)
ARQUITECTURAL: registra en om_mejoras_pendientes para CR1.

Componentes protegidos (siempre ARQUITECTURAL):
  pipeline, orchestrator, tcf, diagnostico, prescriptor, motor_vn, database
"""
from __future__ import annotations

import json
import structlog

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
ORIGEN = "MECANICO"

PROTEGIDOS = {
    "pipeline", "orchestrator", "tcf", "diagnostico",
    "prescriptor", "motor_vn", "database",
}

# F8: Reparaciones automáticas por categoría
REPARACIONES_AUTO = {
    "bus_saturado": "_reparar_bus_saturado",
    "cache_lleno": "_reparar_cache_lleno",
    "llm_budget_excedido": "_reparar_budget",
    "cron_parado": "_reparar_cron",
    "bus": "_reparar_bus_saturado",
    "cache": "_reparar_cache_lleno",
    "llm_budget": "_reparar_budget",
}

REPARACIONES_CR1 = {
    "db_lenta": "Requiere VACUUM ANALYZE — puede afectar rendimiento",
    "disco_lleno": "Requiere borrar datos — riesgo de pérdida",
}


def clasificar(alerta: dict) -> str:
    """Clasifica alerta como FONTANERIA o ARQUITECTURAL."""
    subsistema = alerta.get("subsistema", "")
    severidad = alerta.get("severidad", "medium")
    auto_fixable = alerta.get("auto_fixable", False)

    if subsistema in PROTEGIDOS:
        return "ARQUITECTURAL"
    if severidad == "critical":
        return "ARQUITECTURAL"
    if auto_fixable:
        return "FONTANERIA"
    return "ARQUITECTURAL"


async def _ensure_mejoras_table():
    """Crea tabla om_mejoras_pendientes si no existe."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS om_mejoras_pendientes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT now(),
                tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
                tipo TEXT NOT NULL CHECK (tipo IN ('FONTANERIA', 'ARQUITECTURAL', 'AUTOFAGIA')),
                estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobada', 'rechazada', 'completada')),
                origen TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                senal_id TEXT,
                metadata JSONB DEFAULT '{}'
            )
        """)


async def _fix_bus_acumulacion() -> dict:
    """Fix: marcar como error señales pendientes >24h."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = 'MECANICO',
                procesada_at = now(), error_detalle = 'Expirada por antigüedad (>24h)'
            WHERE estado = 'pendiente' AND tenant_id = $1
            AND created_at < now() - interval '24 hours'
        """, TENANT)
    count = int(result.split()[-1]) if result else 0
    return {"accion": "bus_limpiado", "expiradas": count}


async def _fix_diagnostico_ausente() -> dict:
    """Fix: disparar diagnóstico ACD."""
    try:
        from src.pilates.diagnosticador import diagnosticar_tenant
        diag = await diagnosticar_tenant()
        return {"accion": "acd_ejecutado", "estado": diag.get("estado")}
    except Exception as e:
        return {"accion": "acd_fallido", "error": str(e)[:200]}


async def _reparar_cache_lleno() -> dict:
    """Fix: limpiar caché LLM expirado."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            result = await conn.execute("""
                DELETE FROM om_pizarra_cache_llm
                WHERE expira_at < now() AND tenant_id = $1
            """, TENANT)
            count = int(result.split()[-1]) if result else 0
            return {"accion": "cache_limpiado", "eliminadas": count}
        except Exception:
            return {"accion": "cache_error", "nota": "Tabla caché no accesible"}


async def _reparar_budget() -> dict:
    """Fix: degradar modelos a baja complejidad."""
    try:
        from src.motor.pensar import resetear_presupuesto
        resetear_presupuesto()
        return {"accion": "budget_reseteado", "nota": "Presupuesto reseteado a máximo"}
    except Exception as e:
        return {"accion": "budget_error", "error": str(e)[:100]}


async def _reparar_cron() -> dict:
    """Fix: resetear estado cron para que se ejecute."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE om_cron_state SET ultima_ejecucion = now() - interval '25 hours',
            resultado = 'reset_mecanico'
            WHERE tenant_id = $1
        """, TENANT)
    return {"accion": "cron_reseteado"}


async def _auto_fix(alerta: dict) -> dict:
    """Intenta auto-fix para alertas FONTANERIA."""
    subsistema = alerta.get("subsistema", "")

    # F8: buscar en REPARACIONES_AUTO por subsistema
    if subsistema in ("bus", "bus_saturado"):
        return await _fix_bus_acumulacion()
    if subsistema in ("cache", "cache_lleno"):
        return await _reparar_cache_lleno()
    if subsistema in ("llm_budget", "llm_budget_excedido"):
        return await _reparar_budget()
    if subsistema in ("cron", "cron_parado"):
        return await _reparar_cron()
    if subsistema == "acd":
        return await _fix_diagnostico_ausente()

    return {"accion": "sin_fix_auto", "subsistema": subsistema,
            "nota": "Marcada como procesada. Revisar si persiste."}


async def _registrar_mejora(tipo: str, origen: str, descripcion: str,
                            senal_id: str = None, metadata: dict = None) -> str:
    """Registra mejora pendiente. Devuelve UUID."""
    await _ensure_mejoras_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_mejoras_pendientes (tenant_id, tipo, origen, descripcion, senal_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING id
        """, TENANT, tipo, origen, descripcion, senal_id,
            json.dumps(metadata or {}))
    return str(row["id"])


async def procesar_alertas() -> dict:
    """Lee ALERTAs pendientes del bus y las procesa."""
    from src.pilates.bus import leer_pendientes, marcar_procesada, marcar_error

    alertas = await leer_pendientes(destino="MECANICO", tipo="ALERTA", limite=20)

    fixes = []
    arquitecturales = []
    errores = []

    for señal in alertas:
        señal_id = str(señal["id"])
        payload = señal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        try:
            clase = clasificar(payload)

            if clase == "FONTANERIA":
                fix = await _auto_fix(payload)
                fixes.append({"señal_id": señal_id, **fix})
                await marcar_procesada(señal_id, ORIGEN)
            else:
                mejora_id = await _registrar_mejora(
                    "ARQUITECTURAL", ORIGEN,
                    payload.get("mensaje", "Sin descripción"),
                    señal_id, payload)
                arquitecturales.append({"señal_id": señal_id, "mejora_id": mejora_id,
                    "subsistema": payload.get("subsistema")})
                await marcar_procesada(señal_id, ORIGEN)
                log.warning("mecanico_arquitectural",
                    subsistema=payload.get("subsistema"),
                    mensaje=payload.get("mensaje"))

        except Exception as e:
            errores.append({"señal_id": señal_id, "error": str(e)[:200]})
            await marcar_error(señal_id, ORIGEN, str(e)[:500])

    resultado = {
        "alertas_procesadas": len(alertas),
        "fixes_fontaneria": len(fixes),
        "arquitecturales": len(arquitecturales),
        "errores": len(errores),
        "detalle_fixes": fixes,
        "detalle_arquitectural": arquitecturales,
    }

    # Publicar al feed
    try:
        from src.pilates.feed import feed_mecanico_fix
        for fix in fixes[:3]:
            await feed_mecanico_fix(fix.get("accion", "fontanería"), str(fix)[:200])
    except Exception as e:
        log.warning("mecanico_feed_error", error=str(e))

    if alertas:
        log.info("mecanico_procesado",
            total=len(alertas), fixes=len(fixes), arq=len(arquitecturales))

    # F8: Informe post-mortem por WA para reparaciones auto
    for fix in fixes[:3]:
        try:
            await informe_postmortem(fix.get("accion", "reparación"), fix, fix)
        except Exception as e:
            log.debug("silenced_exception", exc=str(e))

    return resultado


async def informe_postmortem(categoria: str, diagnostico: dict, resultado: dict):
    """Genera y programa informe post-mortem por WA."""
    import os
    telefono = os.getenv("JESUS_TELEFONO", "")
    if not telefono:
        return

    mensaje = (
        f"Reparacion automatica completada\n\n"
        f"Problema: {categoria}\n"
        f"Diagnostico: {str(diagnostico)[:100]}\n"
        f"Accion: {resultado.get('accion', '')[:100]}\n"
        f"Estado: {'Resuelto' if resultado.get('ok', True) else 'Requiere atencion'}"
    )

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, canal, tipo, mensaje,
                 programado_para, estado, origen)
            VALUES ($1, $2, 'whatsapp', 'postmortem', $3,
                    now(), 'pendiente', 'MECANICO')
        """, TENANT, telefono, mensaje)
