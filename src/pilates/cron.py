"""Cron del Exocortex — Tareas programadas.

Ejecuta tareas periódicas sin dependencias externas.
Se inicia en el lifespan de FastAPI como background task.

Tareas:
- Diaria (06:00 Madrid): escuchar señales
- Semanal (lunes 07:00): calcular estrategia + ciclo completo
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, time, timedelta

log = structlog.get_logger()

# Zona horaria: Madrid = UTC+1 (invierno) / UTC+2 (verano)
# Simplificación: usamos UTC+1 fijo. Suficiente para un cron de SMB.
MADRID_OFFSET = timedelta(hours=1)


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (aprox)."""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    return utc_now + MADRID_OFFSET


async def _tarea_diaria():
    """Tarea diaria: escuchar señales de las 3 capas."""
    try:
        from src.pilates.voz_ciclos import escuchar
        result = await escuchar()
        log.info("cron_diaria_ok", senales=result.get("senales_creadas", 0))
    except Exception as e:
        log.error("cron_diaria_error", error=str(e))


async def _tarea_semanal():
    """Tarea semanal (lunes): ciclo completo + estrategia."""
    try:
        # 1. Ciclo completo (escuchar + priorizar + IRC + ISP)
        from src.pilates.voz_ciclos import ejecutar_ciclo_completo
        ciclo = await ejecutar_ciclo_completo()
        log.info("cron_semanal_ciclo_ok", isp=ciclo.get("ciclos", {}).get("aprender", {}).get("isp_global"))

        # 2. Calcular nueva estrategia semanal
        from src.pilates.voz_estrategia import calcular_estrategia
        est = await calcular_estrategia()
        log.info("cron_semanal_estrategia_ok",
                 foco=est.get("estrategia", {}).get("foco_principal"),
                 items=est.get("calendario_items"))

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))


async def cron_loop():
    """Loop principal del cron. Se ejecuta como background task.

    Revisa cada 15 minutos si hay tareas pendientes.
    Marca las ejecutadas para no repetir en el mismo día/semana.
    """
    log.info("cron_iniciado")

    ultima_diaria = None
    ultima_semanal = None

    while True:
        try:
            ahora = _hora_madrid()
            hoy = ahora.date()
            hora = ahora.time()

            # Tarea diaria: después de las 06:00, una vez al día
            if hora >= time(6, 0) and ultima_diaria != hoy:
                log.info("cron_ejecutando_diaria", hora=str(hora))
                await _tarea_diaria()
                ultima_diaria = hoy

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                semana = hoy.isocalendar()[1]
                if ultima_semanal != semana:
                    log.info("cron_ejecutando_semanal", semana=semana)
                    await _tarea_semanal()
                    ultima_semanal = semana

        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
