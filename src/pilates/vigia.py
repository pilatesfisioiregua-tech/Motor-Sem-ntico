"""Vigía — Agente META: monitoriza salud del sistema cada 15 min.

Ejecuta health checks ligeros y emite ALERTA al bus cuando detecta problemas.

Checks:
  1. DB conectividad
  2. Tablas om_* existen
  3. Bus: acumulación de pendientes >2h
  4. ACD: antigüedad último diagnóstico
  5. Cobros: cargos pendientes > umbral
  6. Clientes: hay clientes activos
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "VIGIA"


@dataclass
class CheckResult:
    subsistema: str
    estado: str           # "ok", "warning", "error"
    mensaje: str
    severidad: str = "low"      # "low", "medium", "high", "critical"
    auto_fixable: bool = False
    fix_hint: str = ""


async def _check_db() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            r = await conn.fetchval("SELECT 1")
            if r == 1:
                return CheckResult("database", "ok", "Conexión OK")
        return CheckResult("database", "error", "SELECT 1 falló", "critical")
    except Exception as e:
        return CheckResult("database", "error", f"Sin conexión: {str(e)[:100]}", "critical")


async def _check_tables() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'om_%'")
            if count >= 20:
                return CheckResult("tables", "ok", f"{count} tablas om_*")
            return CheckResult("tables", "warning", f"Solo {count} tablas om_* (esperadas >=20)", "medium")
    except Exception as e:
        return CheckResult("tables", "error", str(e)[:100], "high")


async def _check_bus_acumulacion() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            pendientes = await conn.fetchval("""
                SELECT count(*) FROM om_senales_agentes
                WHERE estado = 'pendiente' AND tenant_id = $1
                AND created_at < now() - interval '2 hours'
            """, TENANT)
            if pendientes is None:
                return CheckResult("bus", "ok", "Tabla bus no existe aún")
            if pendientes > 20:
                return CheckResult("bus", "warning",
                    f"{pendientes} señales pendientes >2h",
                    "medium", True, "Procesar o descartar señales antiguas del bus")
            return CheckResult("bus", "ok", f"{pendientes} señales antiguas pendientes")
    except Exception as e:
        return CheckResult("bus", "ok", f"Bus no disponible: {str(e)[:50]}")


async def _check_ultimo_diagnostico() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            ultimo = await conn.fetchval("""
                SELECT created_at FROM diagnosticos
                WHERE caso_input LIKE 'Diagnóstico autónomo%'
                ORDER BY created_at DESC LIMIT 1
            """)
            if not ultimo:
                return CheckResult("acd", "warning", "Nunca se ha ejecutado diagnóstico ACD",
                    "low", True, "Ejecutar POST /pilates/acd/diagnosticar-tenant")
            dias = (datetime.now(timezone.utc) - ultimo).days
            if dias > 10:
                return CheckResult("acd", "warning",
                    f"Último diagnóstico hace {dias} días",
                    "medium", True, "Ejecutar POST /pilates/acd/diagnosticar-tenant")
            return CheckResult("acd", "ok", f"Último diagnóstico hace {dias} días")
    except Exception as e:
        return CheckResult("acd", "ok", f"Tabla diagnosticos no disponible: {str(e)[:50]}")


async def _check_cobros_pendientes() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            deuda = await conn.fetchval("""
                SELECT COALESCE(sum(total), 0) FROM om_cargos
                WHERE tenant_id = $1 AND estado = 'pendiente'
            """, TENANT) or 0
            deuda = float(deuda)
            if deuda > 2000:
                return CheckResult("cobros", "warning", f"€{deuda:.0f} en cargos pendientes", "high")
            if deuda > 500:
                return CheckResult("cobros", "warning", f"€{deuda:.0f} en cargos pendientes", "medium")
            return CheckResult("cobros", "ok", f"€{deuda:.0f} pendiente")
    except Exception as e:
        return CheckResult("cobros", "ok", f"Sin datos cobros: {str(e)[:50]}")


async def _check_clientes_activos() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            activos = await conn.fetchval("""
                SELECT count(*) FROM om_cliente_tenant
                WHERE tenant_id = $1 AND estado = 'activo'
            """, TENANT) or 0
            if activos == 0:
                return CheckResult("clientes", "warning", "0 clientes activos", "high")
            return CheckResult("clientes", "ok", f"{activos} clientes activos")
    except Exception as e:
        return CheckResult("clientes", "ok", str(e)[:50])


async def ejecutar_checks() -> list[CheckResult]:
    """Ejecuta TODOS los health checks."""
    return [
        await _check_db(),
        await _check_tables(),
        await _check_bus_acumulacion(),
        await _check_ultimo_diagnostico(),
        await _check_cobros_pendientes(),
        await _check_clientes_activos(),
    ]


async def vigilar() -> dict:
    """Ejecuta checks + emite ALERTAs al bus para los que fallan."""
    checks = await ejecutar_checks()
    problemas = [c for c in checks if c.estado in ("warning", "error")]

    alertas_emitidas = 0
    for p in problemas:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "ALERTA", ORIGEN,
                {
                    "subsistema": p.subsistema,
                    "estado": p.estado,
                    "mensaje": p.mensaje,
                    "severidad": p.severidad,
                    "auto_fixable": p.auto_fixable,
                    "fix_hint": p.fix_hint,
                },
                destino="MECANICO",
                prioridad=2 if p.severidad == "critical" else 3 if p.severidad == "high" else 5,
            )
            alertas_emitidas += 1
        except Exception as e:
            log.warning("vigia_bus_error", subsistema=p.subsistema, error=str(e))

    resultado = {
        "checks_total": len(checks),
        "ok": len([c for c in checks if c.estado == "ok"]),
        "warnings": len([c for c in checks if c.estado == "warning"]),
        "errors": len([c for c in checks if c.estado == "error"]),
        "alertas_emitidas": alertas_emitidas,
        "detalle": [{"subsistema": c.subsistema, "estado": c.estado, "mensaje": c.mensaje}
                    for c in checks],
    }

    level = "vigia_ok" if not problemas else "vigia_alerta"
    log.info(level, ok=resultado["ok"], warn=resultado["warnings"], err=resultado["errors"])
    return resultado
