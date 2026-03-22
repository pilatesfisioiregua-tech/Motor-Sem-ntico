"""OBSERVADOR — Agente G1: datos → señales DATO al bus.

Hooks ligeros que se llaman DESPUÉS de operaciones CRUD exitosas.
No bloquean la respuesta al usuario. Fire-and-forget.

Uso en router.py:
    asyncio.create_task(_observar_crud("asistencia", "crear", {"id": str(id)}))
"""
from __future__ import annotations

import structlog

log = structlog.get_logger()

ORIGEN = "OBSERVADOR"


async def observar(entidad: str, accion: str, datos: dict):
    """Emite señal DATO al bus tras operación CRUD."""
    try:
        from src.pilates.bus import emitir

        payload = {
            "entidad": entidad,
            "accion": accion,
            **datos,
        }

        prioridad_map = {
            "pago": 2,
            "asistencia": 3,
            "contrato": 3,
            "cliente": 4,
            "sesion": 5,
            "wa_mensaje": 6,
        }
        prioridad = prioridad_map.get(entidad, 5)

        await emitir("DATO", ORIGEN, payload, prioridad=prioridad)

    except Exception as e:
        # NUNCA bloquear CRUD por error en observador
        log.warning("observador_error", entidad=entidad, accion=accion, error=str(e))
