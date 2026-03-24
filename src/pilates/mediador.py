"""Mediador — Resuelve conflictos cross-AF ANTES de actuar (P62).

Hoy: Convergencia detecta conflictos DESPUÉS (daño ya hecho).
Mañana: Mediador lee señales PRESCRIPCION pendientes, agrupa por objeto,
        detecta contradicciones, y resuelve con motor.pensar().

Ejemplo:
  AF3 dice "cerrar grupo L-X 17:15" (3 alumnos, no rentable)
  AF1 dice "retener a María" (está en ese grupo, riesgo baja)
  Mediador decide: "mover María a grupo M-J 18:15 antes de cerrar L-X"
"""
from __future__ import annotations

import json
import structlog
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"

SYSTEM_MEDIADOR = """Eres el Mediador del organismo cognitivo.
Tu trabajo: resolver CONFLICTOS entre agentes funcionales ANTES de que actúen.

Cuando 2+ agentes señalan el mismo cliente/grupo con acciones contradictorias:
- NO elijas un ganador automáticamente
- Busca una TERCERA OPCIÓN que satisfaga ambas intenciones
- Si no hay tercera opción, prioriza: Salud > Sentido > Continuidad

Formato de respuesta JSON:
{
  "conflictos_detectados": N,
  "resoluciones": [
    {
      "objeto": "cliente/grupo afectado",
      "conflicto": "AF3 quiere X, AF1 quiere Y",
      "resolucion": "Hacer Z que satisface ambos",
      "accion_final": "descripción de la acción unificada",
      "af_origen": ["AF1", "AF3"],
      "prioridad": 1-5
    }
  ],
  "sin_conflicto": ["señales que no conflictan — pasar directo"]
}"""


async def mediar(ciclo: str = None) -> dict:
    """Lee señales PRESCRIPCION pendientes, detecta conflictos, resuelve.

    Se ejecuta ANTES del Ejecutor en el ciclo semanal.
    """
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Leer señales PRESCRIPCION y ACCION no procesadas
        senales = await conn.fetch("""
            SELECT id, tipo_senal, origen, contenido, prioridad, payload
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND procesada = false
                AND tipo_senal IN ('PRESCRIPCION', 'ACCION', 'ALERTA')
            ORDER BY prioridad ASC
        """, TENANT)

    if len(senales) < 2:
        log.info("mediador_skip", razon="<2 señales pendientes")
        return {"status": "skip", "conflictos": 0}

    # Agrupar por objeto (cliente_id o grupo_id en payload)
    por_objeto = defaultdict(list)
    for s in senales:
        payload = s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"] or "{}")
        obj_id = payload.get("cliente_id") or payload.get("grupo_id") or payload.get("objeto_id") or "global"
        por_objeto[obj_id].append({
            "id": str(s["id"]),
            "tipo": s["tipo_senal"],
            "origen": s["origen"],
            "contenido": s["contenido"],
            "prioridad": s["prioridad"],
            "payload": payload,
        })

    # Solo mediar objetos con señales de 2+ AF distintos
    conflictos = []
    for obj_id, sigs in por_objeto.items():
        origenes = set(s["origen"] for s in sigs)
        if len(origenes) >= 2:
            conflictos.append({"objeto_id": obj_id, "senales": sigs})

    if not conflictos:
        log.info("mediador_sin_conflictos", total_senales=len(senales))
        return {"status": "ok", "conflictos": 0, "senales_directas": len(senales)}

    # Mediar con motor.pensar()
    user_msg = f"CONFLICTOS A RESOLVER ({len(conflictos)}):\n\n"
    for i, c in enumerate(conflictos):
        user_msg += f"=== Conflicto {i+1} (objeto: {c['objeto_id']}) ===\n"
        for s in c["senales"]:
            user_msg += f"  {s['origen']} [{s['tipo']}] p{s['prioridad']}: {s['contenido']}\n"
        user_msg += "\n"

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=False,
    )
    resultado = await pensar(system=SYSTEM_MEDIADOR, user=user_msg, config=config)
    parsed = extraer_json(resultado.texto, fallback={"resoluciones": [], "conflictos_detectados": 0})

    # Registrar mediaciones
    resoluciones = parsed.get("resoluciones", [])
    pool = await get_pool()
    async with pool.acquire() as conn:
        for r in resoluciones:
            await conn.execute("""
                INSERT INTO om_mediaciones
                    (tenant_id, ciclo, conflicto, resolucion, af_involucrados)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5)
            """, TENANT, ciclo,
                json.dumps({"descripcion": r.get("conflicto", "")}),
                json.dumps(r),
                r.get("af_origen", []))

    log.info("mediador_ok", conflictos=len(conflictos), resoluciones=len(resoluciones),
             coste=resultado.coste_usd)

    return {
        "status": "ok",
        "conflictos": len(conflictos),
        "resoluciones": len(resoluciones),
        "coste": resultado.coste_usd,
    }
