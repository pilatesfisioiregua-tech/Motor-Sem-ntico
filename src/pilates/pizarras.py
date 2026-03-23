"""Pizarras — lectura universal de las 11 pizarras del organismo (P64).

Cada función lee de DB con fallback a defaults razonables.
Las pizarras son CAPA DE LECTURA (CQRS). Nunca escriben datos operacionales.

Pizarras:
  1. Estado      → om_pizarra (ya existe)
  2. Conocimiento → corpus MCP (externo)
  3. Dominio     → om_pizarra_dominio
  4. Cognitiva   → om_pizarra_cognitiva
  5. Temporal    → om_pizarra_temporal
  6. Modelos     → om_pizarra_modelos
  7. Evolución   → om_pizarra_evolucion
  8. Interfaz    → om_pizarra_interfaz
  9. Comunicación → (Fase 5)
  10. Caché LLM   → (Fase 4)
  11. Identidad   → (Fase 7)
"""
from __future__ import annotations

import json
import structlog
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

DEFAULT_TENANT = "authentic_pilates"

DEFAULT_DOMINIO = {
    "tenant_id": DEFAULT_TENANT,
    "nombre": "Authentic Pilates",
    "config": {
        "timezone": "Europe/Madrid",
        "moneda": "EUR",
        "datos_clinicos": True,
        "funciones_activas": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
        "idioma": "es",
        "ubicacion": "Albelda de Iregua, La Rioja",
    },
}


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# PIZARRA DOMINIO (#3)
# ============================================================

async def leer_dominio(tenant_id: str = DEFAULT_TENANT) -> dict:
    """Lee configuración del tenant desde pizarra dominio."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM om_pizarra_dominio WHERE tenant_id = $1", tenant_id)
            if row:
                config = row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])
                return {
                    "tenant_id": row["tenant_id"],
                    "nombre": row["nombre"],
                    "config": config,
                }
    except Exception as e:
        log.warning("pizarra_dominio_fallback", error=str(e)[:80])
    return DEFAULT_DOMINIO


async def leer_timezone(tenant_id: str = DEFAULT_TENANT) -> str:
    """Shortcut: timezone del tenant."""
    dom = await leer_dominio(tenant_id)
    return dom["config"].get("timezone", "Europe/Madrid")


async def leer_telefono_dueno(tenant_id: str = DEFAULT_TENANT) -> str:
    """Shortcut: teléfono del dueño."""
    dom = await leer_dominio(tenant_id)
    return dom["config"].get("telefono_dueno", "")


# ============================================================
# PIZARRA MODELOS (#6)
# ============================================================

async def leer_modelo(tenant_id: str, funcion: str, lente: str = None,
                      complejidad: str = "media") -> str:
    """Devuelve el modelo óptimo para función+lente+complejidad.

    Búsqueda: función+lente+complejidad → función+complejidad → *+complejidad → default.
    """
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            # Intento 1: match exacto
            if lente:
                modelo = await conn.fetchval("""
                    SELECT modelo FROM om_pizarra_modelos
                    WHERE tenant_id=$1 AND funcion=$2 AND lente=$3 AND complejidad=$4
                    ORDER BY score_historico DESC NULLS LAST LIMIT 1
                """, tenant_id, funcion, lente, complejidad)
                if modelo:
                    return modelo

            # Intento 2: función + complejidad (sin lente)
            modelo = await conn.fetchval("""
                SELECT modelo FROM om_pizarra_modelos
                WHERE tenant_id=$1 AND funcion=$2 AND lente IS NULL AND complejidad=$3
                ORDER BY score_historico DESC NULLS LAST LIMIT 1
            """, tenant_id, funcion, complejidad)
            if modelo:
                return modelo

            # Intento 3: wildcard
            modelo = await conn.fetchval("""
                SELECT modelo FROM om_pizarra_modelos
                WHERE tenant_id=$1 AND funcion='*' AND complejidad=$2
                ORDER BY score_historico DESC NULLS LAST LIMIT 1
            """, tenant_id, complejidad)
            if modelo:
                return modelo

    except Exception as e:
        log.warning("pizarra_modelos_fallback", error=str(e)[:80])

    # Fallback hardcoded
    defaults = {"baja": "deepseek/deepseek-v3.2", "media": "openai/gpt-4o", "alta": "anthropic/claude-opus-4"}
    return defaults.get(complejidad, "openai/gpt-4o")


# ============================================================
# PIZARRA COGNITIVA (#4)
# ============================================================

async def leer_recetas_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee todas las recetas del Director para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_cognitiva
                WHERE tenant_id=$1 AND ciclo=$2
                ORDER BY prioridad ASC
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA TEMPORAL (#5)
# ============================================================

async def leer_plan_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee el plan temporal (qué componentes ejecutar, en qué orden)."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_temporal
                WHERE tenant_id=$1 AND ciclo=$2 AND activo=true
                ORDER BY fase, orden
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA EVOLUCIÓN (#7)
# ============================================================

async def leer_patrones(tenant_id: str, tipo: str = None,
                        min_confianza: float = 0.3) -> list[dict]:
    """Lee patrones aprendidos, filtrados por tipo y confianza."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            query = """
                SELECT * FROM om_pizarra_evolucion
                WHERE tenant_id=$1 AND confianza >= $2
            """
            params = [tenant_id, min_confianza]
            if tipo:
                query += " AND tipo = $3"
                params.append(tipo)
            query += " ORDER BY confianza DESC, evidencia_ciclos DESC"
            rows = await conn.fetch(query, *params)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# PIZARRA INTERFAZ (#8)
# ============================================================

async def leer_layout_ciclo(tenant_id: str, ciclo: str) -> list[dict]:
    """Lee el layout del cockpit para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM om_pizarra_interfaz
                WHERE tenant_id=$1 AND ciclo=$2
                ORDER BY prioridad ASC
            """, tenant_id, ciclo)
            return [dict(r) for r in rows]
    except Exception:
        return []


# ============================================================
# SNAPSHOTS (P65) — "git del organismo"
# ============================================================

async def crear_snapshot(tenant_id: str, ciclo: str, tipo_pizarra: str,
                         contenido: dict) -> Optional[UUID]:
    """Crea un snapshot de una pizarra para un ciclo."""
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO om_pizarra_snapshot (tenant_id, ciclo, tipo_pizarra, contenido)
                VALUES ($1, $2, $3, $4::jsonb)
                RETURNING id
            """, tenant_id, ciclo, tipo_pizarra, json.dumps(contenido, default=str))
            return row["id"] if row else None
    except Exception as e:
        log.warning("snapshot_error", error=str(e)[:80])
        return None


async def snapshot_todas(tenant_id: str, ciclo: str) -> dict:
    """Crea snapshots de TODAS las pizarras existentes para un ciclo.

    Se llama al final de cada ciclo semanal.
    """
    resultados = {}

    # Dominio
    dom = await leer_dominio(tenant_id)
    sid = await crear_snapshot(tenant_id, ciclo, "dominio", dom)
    resultados["dominio"] = str(sid) if sid else "error"

    # Cognitiva
    recetas = await leer_recetas_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "cognitiva", {"recetas": recetas})
    resultados["cognitiva"] = str(sid) if sid else "error"

    # Temporal
    plan = await leer_plan_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "temporal", {"plan": plan})
    resultados["temporal"] = str(sid) if sid else "error"

    # Modelos
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM om_pizarra_modelos WHERE tenant_id=$1", tenant_id)
            modelos = [dict(r) for r in rows]
    except Exception:
        modelos = []
    sid = await crear_snapshot(tenant_id, ciclo, "modelos", {"modelos": modelos})
    resultados["modelos"] = str(sid) if sid else "error"

    # Evolución
    patrones = await leer_patrones(tenant_id, min_confianza=0.0)
    sid = await crear_snapshot(tenant_id, ciclo, "evolucion", {"patrones": patrones})
    resultados["evolucion"] = str(sid) if sid else "error"

    # Interfaz
    layout = await leer_layout_ciclo(tenant_id, ciclo)
    sid = await crear_snapshot(tenant_id, ciclo, "interfaz", {"layout": layout})
    resultados["interfaz"] = str(sid) if sid else "error"

    # Estado (om_pizarra existente)
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM om_pizarra WHERE tenant_id=$1", tenant_id)
            estado = [dict(r) for r in rows]
    except Exception:
        estado = []
    sid = await crear_snapshot(tenant_id, ciclo, "estado", {"estado": estado})
    resultados["estado"] = str(sid) if sid else "error"

    log.info("snapshot_todas_ok", ciclo=ciclo, pizarras=len(resultados))
    return resultados
