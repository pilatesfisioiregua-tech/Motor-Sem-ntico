"""Autonomía — Motor de decisión que clasifica acciones por nivel.

Niveles:
  AUTO: ejecutar + log
  NOTIFICAR_4H: ejecutar + WA Jesús + si veto en 4h cancelar
  CR1: WA Jesús + esperar aprobación + timeout 48h
"""
from __future__ import annotations

import json
import os
import structlog

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


async def decidir_nivel(accion_tipo: str, tenant_id: str = TENANT) -> str:
    """Determina el nivel de autonomía para una acción.

    Lee pizarra dominio config.autonomia.
    Si acción no catalogada → CR1 (conservador).
    """
    from src.pilates.pizarras import leer_dominio
    dominio = await leer_dominio(tenant_id)
    autonomia = dominio.get("config", {}).get("autonomia", {})

    if accion_tipo in (autonomia.get("auto") or []):
        return "auto"
    elif accion_tipo in (autonomia.get("notificar_4h") or []):
        return "notificar_4h"
    else:
        return "cr1"


async def ejecutar_con_autonomia(accion_tipo: str, ejecutor, *args, **kwargs) -> dict:
    """Ejecuta una acción respetando el nivel de autonomía.

    ejecutor: async function a ejecutar si se permite.
    """
    nivel = await decidir_nivel(accion_tipo)

    if nivel == "auto":
        resultado = await ejecutor(*args, **kwargs)
        return {"nivel": "auto", "ejecutado": True, "resultado": resultado}

    elif nivel == "notificar_4h":
        resultado = await ejecutor(*args, **kwargs)
        telefono = os.getenv("JESUS_TELEFONO", "")
        if telefono:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_pizarra_comunicacion
                        (tenant_id, destinatario, canal, tipo, mensaje,
                         programado_para, estado, origen)
                    VALUES ($1, $2, 'whatsapp', 'notificacion_autonomia',
                            $3, now(), 'pendiente', 'AUTONOMIA')
                """, TENANT, telefono,
                    f"Accion ejecutada: {accion_tipo}\nTienes 4h para vetar. Responde 'cancelar' si no estas de acuerdo.")
        return {"nivel": "notificar_4h", "ejecutado": True, "resultado": resultado}

    else:  # cr1
        telefono = os.getenv("JESUS_TELEFONO", "")
        if telefono:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_pizarra_comunicacion
                        (tenant_id, destinatario, canal, tipo, mensaje,
                         programado_para, estado, origen, metadata)
                    VALUES ($1, $2, 'whatsapp', 'solicitud_cr1',
                            $3, now(), 'pendiente', 'AUTONOMIA', $4::jsonb)
                """, TENANT, telefono,
                    f"Necesito tu aprobacion:\n{accion_tipo}\nResponde 'si' o 'no'.",
                    json.dumps({"accion_tipo": accion_tipo}))
        return {"nivel": "cr1", "ejecutado": False, "esperando_aprobacion": True}
