"""Pizarra Compartida — Conciencia colectiva del organismo.

Cada agente ESCRIBE lo que está haciendo/pensando.
Cada agente LEE lo que los demás escribieron ANTES de actuar.
El resultado: agentes que saben lo que los demás están haciendo.

Operaciones:
  escribir(agente, capa, datos) → persiste en om_pizarra
  leer_relevante(agente) → lee lo que NECESITA saber según su rol
  leer_conflictos(agente) → quién tiene conflicto conmigo
  leer_bloqueos(agente) → quién me bloquea
  leer_todo() → snapshot completo del ciclo (para compositor/enjambre)
  resumen_narrativo() → resumen legible de toda la pizarra (para cockpit)
"""
from __future__ import annotations

import json
import structlog
from datetime import date

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


def _ciclo_actual() -> str:
    """Devuelve el identificador del ciclo actual (semanal)."""
    hoy = date.today()
    return f"semanal_{hoy.isocalendar()[0]}W{hoy.isocalendar()[1]:02d}"


# ============================================================
# ESCRIBIR — Cada agente deja su estado en la pizarra
# ============================================================

async def escribir(
    agente: str,
    capa: str,
    estado: str = "activo",
    detectando: str | None = None,
    interpretacion: str | None = None,
    accion_propuesta: str | None = None,
    necesita_de: list[str] | None = None,
    bloquea_a: list[str] | None = None,
    conflicto_con: list[str] | None = None,
    confianza: float = 0.5,
    prioridad: int = 5,
    datos: dict | None = None,
) -> str:
    """Escribe/actualiza la entrada del agente en la pizarra del ciclo actual.

    UPSERT: si ya escribió en este ciclo, actualiza (version+1).
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_pizarra
                (tenant_id, agente, capa, estado, detectando, interpretacion,
                 accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                 confianza, prioridad, datos, ciclo, version, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13::jsonb, $14, 1, now())
            ON CONFLICT (tenant_id, agente, ciclo)
            DO UPDATE SET
                estado = EXCLUDED.estado,
                detectando = COALESCE(EXCLUDED.detectando, om_pizarra.detectando),
                interpretacion = COALESCE(EXCLUDED.interpretacion, om_pizarra.interpretacion),
                accion_propuesta = COALESCE(EXCLUDED.accion_propuesta, om_pizarra.accion_propuesta),
                necesita_de = COALESCE(EXCLUDED.necesita_de, om_pizarra.necesita_de),
                bloquea_a = COALESCE(EXCLUDED.bloquea_a, om_pizarra.bloquea_a),
                conflicto_con = COALESCE(EXCLUDED.conflicto_con, om_pizarra.conflicto_con),
                confianza = EXCLUDED.confianza,
                prioridad = EXCLUDED.prioridad,
                datos = om_pizarra.datos || EXCLUDED.datos,
                version = om_pizarra.version + 1,
                updated_at = now()
            RETURNING id
        """, TENANT, agente, capa, estado,
            detectando, interpretacion, accion_propuesta,
            necesita_de or [], bloquea_a or [], conflicto_con or [],
            confianza, prioridad,
            json.dumps(datos or {}),
            ciclo)

    log.info("pizarra_escrita", agente=agente, ciclo=ciclo)
    return str(row["id"])


# ============================================================
# LEER — Cada agente consulta antes de actuar
# ============================================================

async def leer_relevante(agente: str) -> list[dict]:
    """Lee las entradas de la pizarra relevantes para este agente.

    Relevante = agentes que me mencionan en necesita_de, bloquea_a, conflicto_con
    + agentes de la misma capa + compositor/enjambre (siempre relevante para todos).
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, capa, estado, detectando, interpretacion,
                   accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                   confianza, prioridad, datos, version, updated_at
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND (
                -- Me mencionan
                $3 = ANY(necesita_de) OR
                $3 = ANY(bloquea_a) OR
                $3 = ANY(conflicto_con) OR
                -- Agentes de gobierno (siempre relevantes)
                agente IN ('COMPOSITOR', 'ENJAMBRE', 'RECOMPILADOR', 'GUARDIAN', 'ESTRATEGA') OR
                -- Misma capa ejecutiva (AF se leen entre sí)
                (capa = 'ejecutiva' AND $4 = 'ejecutiva')
            )
            AND agente != $3
            ORDER BY prioridad, updated_at DESC
        """, TENANT, ciclo, agente,
            _capa_de_agente(agente))

    return [_row_to_dict(r) for r in rows]


async def leer_conflictos(agente: str) -> list[dict]:
    """Lee quién tiene conflicto conmigo."""
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, detectando, interpretacion, accion_propuesta, confianza
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND $3 = ANY(conflicto_con)
        """, TENANT, ciclo, agente)

    return [_row_to_dict(r) for r in rows]


async def leer_bloqueos(agente: str) -> list[dict]:
    """Lee quién me bloquea."""
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, detectando, accion_propuesta, confianza
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND $3 = ANY(bloquea_a)
        """, TENANT, ciclo, agente)

    return [_row_to_dict(r) for r in rows]


async def leer_todo() -> list[dict]:
    """Snapshot completo de la pizarra del ciclo actual.

    Para el Compositor, Enjambre, Guardián — ven TODO.
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, capa, estado, detectando, interpretacion,
                   accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                   confianza, prioridad, datos, version, updated_at
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            ORDER BY capa, prioridad, agente
        """, TENANT, ciclo)

    return [_row_to_dict(r) for r in rows]


async def resumen_narrativo() -> str:
    """Genera un resumen legible de toda la pizarra para el cockpit.

    No usa LLM — construye el resumen por código.
    """
    entradas = await leer_todo()
    if not entradas:
        return "Pizarra vacía — ningún agente ha ejecutado en este ciclo."

    lines = [f"PIZARRA DEL ORGANISMO — Ciclo {_ciclo_actual()}\n"]

    # Agrupar por capa
    capas: dict[str, list[dict]] = {}
    for e in entradas:
        capa = e.get("capa", "otra")
        capas.setdefault(capa, []).append(e)

    for capa, agentes in capas.items():
        lines.append(f"\n{'='*40}")
        lines.append(f"CAPA {capa.upper()} ({len(agentes)} agentes)")
        lines.append(f"{'='*40}")

        for a in agentes:
            estado_icon = {"activo": "[ON]", "esperando": "[WAIT]",
                           "bloqueado": "[BLOCK]", "completado": "[OK]"}.get(a["estado"], "[?]")
            lines.append(f"\n{estado_icon} {a['agente']} (confianza: {a.get('confianza', 0):.0%})")
            if a.get("detectando"):
                lines.append(f"  Detectando: {a['detectando'][:150]}")
            if a.get("interpretacion"):
                lines.append(f"  Interpreta: {a['interpretacion'][:150]}")
            if a.get("accion_propuesta"):
                lines.append(f"  Propone: {a['accion_propuesta'][:150]}")
            if a.get("conflicto_con"):
                lines.append(f"  CONFLICTO con: {', '.join(a['conflicto_con'])}")
            if a.get("bloquea_a"):
                lines.append(f"  BLOQUEA a: {', '.join(a['bloquea_a'])}")
            if a.get("necesita_de"):
                lines.append(f"  NECESITA de: {', '.join(a['necesita_de'])}")

    # Detectar conflictos cruzados
    conflictos = []
    for e in entradas:
        for c in (e.get("conflicto_con") or []):
            conflictos.append(f"{e['agente']} <> {c}")
    if conflictos:
        lines.append(f"\n{'='*40}")
        lines.append("CONFLICTOS ACTIVOS")
        lines.append(f"{'='*40}")
        for c in set(conflictos):
            lines.append(f"  {c}")

    return "\n".join(lines)


# ============================================================
# HELPERS
# ============================================================

def _capa_de_agente(agente: str) -> str:
    """Devuelve la capa de un agente."""
    if agente.startswith("AF") or agente in ("EJECUTOR", "CONVERGENCIA", "GESTOR", "SEQUITO"):
        return "ejecutiva"
    if agente.startswith("CLUSTER") or agente in ("COMPOSITOR", "ESTRATEGA", "ORQUESTADOR",
                                                     "ENJAMBRE", "GUARDIAN", "RECOMPILADOR"):
        return "cognitiva"
    if agente in ("DIAGNOSTICADOR", "BUSCADOR", "COLLECTOR"):
        return "sensorial"
    if agente in ("VIGIA", "MECANICO", "AUTOFAGO", "PROPIOCEPCION"):
        return "meta"
    if agente in ("HUERFANAS", "CRISTALIZADOR", "SEMILLAS"):
        return "generativa"
    return "otra"


def _row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
    return d
