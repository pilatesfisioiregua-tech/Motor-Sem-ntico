"""Propiocepción — El organismo mide su propio funcionamiento.

Vigía pregunta: "¿el negocio está sano?"
Propiocepción pregunta: "¿el organismo funciona bien?"

Métricas:
  1. Throughput del bus: señales emitidas/procesadas/error por periodo
  2. Actividad de agentes: quién emite, quién calla
  3. Latencia: tiempo medio entre emisión y procesamiento
  4. ACD drift: cambio en lentes respecto al snapshot anterior
  5. Mecánico: fixes y mejoras acumuladas
  6. Agentes silenciosos: los que deberían emitir pero no lo hacen

Ejecución: snapshot diario + resumen semanal.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Agentes que esperamos que emitan al menos una señal por semana
AGENTES_ESPERADOS = {
    "OBSERVADOR",   # Cada CRUD → señal DATO
    "VIGIA",        # Cada 15 min → señal ALERTA si hay problemas
    "DIAGNOSTICADOR",  # Semanal → señal DIAGNOSTICO
    "MECANICO",     # Reactivo → procesa ALERTAs
}


async def _metricas_bus(desde: datetime) -> dict:
    """Métricas del bus de señales desde una fecha."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Conteos por estado
        stats = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE estado = 'procesada') as procesadas,
                count(*) FILTER (WHERE estado = 'error') as errores,
                count(*) FILTER (WHERE estado = 'pendiente') as pendientes
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, desde)

        # Latencia media (solo procesadas)
        latencia = await conn.fetchval("""
            SELECT AVG(EXTRACT(EPOCH FROM (procesada_at - created_at)) / 60.0)
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND estado = 'procesada'
            AND created_at >= $2 AND procesada_at IS NOT NULL
        """, TENANT, desde)

        # Actividad por agente (origen)
        agentes_rows = await conn.fetch("""
            SELECT origen, count(*) as n
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
            GROUP BY origen ORDER BY n DESC
        """, TENANT, desde)

    actividad = {r["origen"]: r["n"] for r in agentes_rows}
    agentes_activos = set(actividad.keys())
    silenciosos = sorted(AGENTES_ESPERADOS - agentes_activos)

    return {
        "emitidas": stats["total"] or 0,
        "procesadas": stats["procesadas"] or 0,
        "errores": stats["errores"] or 0,
        "pendientes": stats["pendientes"] or 0,
        "latencia_media_min": round(float(latencia), 2) if latencia else None,
        "actividad_agentes": actividad,
        "agentes_silenciosos": silenciosos,
    }


async def _metricas_acd() -> dict:
    """Estado ACD actual + delta vs anterior."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        ultimos = await conn.fetch("""
            SELECT estado_pre, lentes_pre, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 2
        """)

    if not ultimos:
        return {"estado": None, "lentes": None, "delta": None}

    actual = ultimos[0]
    lentes_actual = actual["lentes_pre"]
    if isinstance(lentes_actual, str):
        lentes_actual = json.loads(lentes_actual)

    delta = None
    if len(ultimos) > 1:
        lentes_anterior = ultimos[1]["lentes_pre"]
        if isinstance(lentes_anterior, str):
            lentes_anterior = json.loads(lentes_anterior)
        delta = {
            k: round(lentes_actual.get(k, 0) - lentes_anterior.get(k, 0), 3)
            for k in ["salud", "sentido", "continuidad"]
        }

    return {
        "estado": actual["estado_pre"],
        "lentes": lentes_actual,
        "delta": delta,
        "fecha": str(actual["created_at"])[:10],
    }


async def _metricas_mecanico(desde: datetime) -> dict:
    """Conteo de fixes y mejoras en el periodo."""
    pool = await get_pool()
    resultado = {"fixes_fontaneria": 0, "arquitecturales": 0, "autofagia": 0}

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch("""
                SELECT tipo, count(*) as n
                FROM om_mejoras_pendientes
                WHERE tenant_id = $1 AND created_at >= $2
                GROUP BY tipo
            """, TENANT, desde)
            for r in rows:
                if r["tipo"] == "FONTANERIA":
                    resultado["fixes_fontaneria"] = r["n"]
                elif r["tipo"] == "ARQUITECTURAL":
                    resultado["arquitecturales"] = r["n"]
                elif r["tipo"] == "AUTOFAGIA":
                    resultado["autofagia"] = r["n"]
        except Exception:
            pass

    return resultado


async def snapshot(periodo: str = "diario") -> dict:
    """Genera y persiste un snapshot de telemetría del organismo.

    Args:
        periodo: "diario" (últimas 24h) o "semanal" (últimos 7 días)
    """
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=1 if periodo == "diario" else 7)

    # Recopilar métricas
    bus = await _metricas_bus(desde)
    acd = await _metricas_acd()
    mecanico = await _metricas_mecanico(desde)

    # Persistir snapshot
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_telemetria_sistema (
                tenant_id, periodo,
                senales_emitidas, senales_procesadas, senales_error, senales_pendientes,
                latencia_media_min, actividad_agentes, agentes_silenciosos,
                acd_estado, acd_lentes, acd_delta_lentes,
                fixes_fontaneria, mejoras_arquitecturales, propuestas_autofagia
            ) VALUES (
                $1, $2,
                $3, $4, $5, $6,
                $7, $8::jsonb, $9,
                $10, $11::jsonb, $12::jsonb,
                $13, $14, $15
            )
        """, TENANT, periodo,
            bus["emitidas"], bus["procesadas"], bus["errores"], bus["pendientes"],
            bus["latencia_media_min"], json.dumps(bus["actividad_agentes"]), bus["agentes_silenciosos"],
            acd.get("estado"), json.dumps(acd.get("lentes")) if acd.get("lentes") else None,
            json.dumps(acd.get("delta")) if acd.get("delta") else None,
            mecanico["fixes_fontaneria"], mecanico["arquitecturales"], mecanico["autofagia"],
        )

    resultado = {
        "periodo": periodo,
        "desde": str(desde)[:19],
        "bus": bus,
        "acd": acd,
        "mecanico": mecanico,
        "alerta_drift": _evaluar_drift(acd),
        "alerta_silencio": bus["agentes_silenciosos"],
    }

    # Emitir alerta si hay drift significativo o agentes silenciosos
    alertas = []
    if resultado["alerta_drift"]:
        alertas.append(resultado["alerta_drift"])
    if bus["agentes_silenciosos"] and periodo == "semanal":
        alertas.append(f"Agentes silenciosos esta semana: {', '.join(bus['agentes_silenciosos'])}")

    if alertas:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "ALERTA", "PROPIOCEPCION",
                {
                    "tipo": "drift_o_silencio",
                    "alertas": alertas,
                    "periodo": periodo,
                    "bus_emitidas": bus["emitidas"],
                    "acd_estado": acd.get("estado"),
                },
                prioridad=6,
            )
        except Exception as e:
            log.warning("propiocepcion_bus_error", error=str(e))

    log.info(f"propiocepcion_{periodo}",
        señales=bus["emitidas"], silenciosos=len(bus["agentes_silenciosos"]),
        acd=acd.get("estado"), drift=resultado["alerta_drift"] is not None)

    return resultado


def _evaluar_drift(acd: dict) -> str | None:
    """Evalúa si hay drift significativo en las lentes ACD."""
    delta = acd.get("delta")
    if not delta:
        return None

    for lente, cambio in delta.items():
        if abs(cambio) > 0.15:
            direccion = "subió" if cambio > 0 else "bajó"
            return f"DRIFT: {lente} {direccion} {abs(cambio):.2f} respecto al diagnóstico anterior"

    return None


async def obtener_tendencia(n_snapshots: int = 10) -> list[dict]:
    """Devuelve los últimos N snapshots para visualizar tendencia."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT created_at, periodo, senales_emitidas, senales_procesadas,
                   senales_error, latencia_media_min, agentes_silenciosos,
                   acd_estado, acd_lentes, acd_delta_lentes,
                   fixes_fontaneria, mejoras_arquitecturales
            FROM om_telemetria_sistema
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, TENANT, n_snapshots)

    return [dict(r) for r in rows]
