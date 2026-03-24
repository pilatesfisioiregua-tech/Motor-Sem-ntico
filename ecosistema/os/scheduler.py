"""Scheduler — Planificador del OS.

Decide CUANDO ejecutar cada proceso (app/exocortex).
Gestiona prioridades, presupuesto y health de todos los procesos.

Analogia:
  Scheduler    = cron + nice + OOM killer del OS
  Prioridad    = nice value (1=RT, 5=normal, 10=idle)
  Presupuesto  = cgroup memory limit (cuanto LLM puede gastar)
  Health check = watchdog que mata procesos enfermos
"""
from __future__ import annotations

import asyncio
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ecosistema.os.proceso import Proceso, EstadoProceso
from ecosistema.memoria.almacen import Almacen

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass
class Scheduler:
    """Planificador del OS — gestiona N procesos.

    Responsabilidades:
      1. Mantener tabla de procesos (ps aux)
      2. Decidir orden de ejecucion por prioridad
      3. Ejecutar ciclos respetando presupuesto
      4. Health check y recovery de procesos rotos
      5. Reset semanal de presupuestos
    """
    procesos: dict[str, Proceso] = field(default_factory=dict)
    max_procesos_simultaneos: int = 3   # Limite de concurrencia
    _ejecutando: bool = False

    # ----------------------------------------------------------
    # GESTION DE PROCESOS (ps, kill, top)
    # ----------------------------------------------------------

    def registrar(self, proceso: Proceso) -> None:
        """Registra un nuevo proceso en la tabla."""
        self.procesos[proceso.pid] = proceso
        log.info("scheduler.proceso_registrado",
                 pid=proceso.pid, app=proceso.app_id)

    def obtener(self, pid: str) -> Optional[Proceso]:
        """Busca un proceso por PID."""
        return self.procesos.get(pid)

    def listar_activos(self) -> list[Proceso]:
        """Lista procesos no terminados, ordenados por prioridad."""
        activos = [p for p in self.procesos.values()
                   if p.estado != EstadoProceso.TERMINADO]
        activos.sort(key=lambda p: p.prioridad)
        return activos

    def terminar(self, pid: str) -> bool:
        """Termina un proceso (desinstalar app)."""
        p = self.procesos.get(pid)
        if p:
            p.estado = EstadoProceso.TERMINADO
            log.info("scheduler.proceso_terminado", pid=pid)
            return True
        return False

    # ----------------------------------------------------------
    # EJECUCION (el loop principal del OS)
    # ----------------------------------------------------------

    async def ejecutar_ronda(self) -> dict:
        """Ejecuta una ronda del scheduler.

        1. Selecciona procesos ejecutables (dormidos + con presupuesto)
        2. Ordena por prioridad
        3. Ejecuta hasta max_procesos_simultaneos en paralelo
        4. Registra resultados
        """
        if self._ejecutando:
            log.warning("scheduler.ya_ejecutando")
            return {"estado": "ya_ejecutando"}

        self._ejecutando = True
        try:
            ejecutables = [
                p for p in self.listar_activos()
                if p.estado == EstadoProceso.DORMIDO
                and p.presupuesto_gastado < p.presupuesto_semanal
            ]

            if not ejecutables:
                return {"estado": "sin_procesos_ejecutables", "ejecutados": 0}

            # Tomar los N mas prioritarios
            batch = ejecutables[:self.max_procesos_simultaneos]

            log.info("scheduler.ronda_inicio",
                     ejecutables=len(ejecutables),
                     batch=len(batch),
                     pids=[p.pid for p in batch])

            # Ejecutar en paralelo
            tareas = [p.ejecutar_ciclo() for p in batch]
            resultados = await asyncio.gather(*tareas, return_exceptions=True)

            resumen = {
                "estado": "ok",
                "ejecutados": len(batch),
                "resultados": {},
            }

            for i, resultado in enumerate(resultados):
                pid = batch[i].pid
                if isinstance(resultado, Exception):
                    resumen["resultados"][pid] = {
                        "estado": "error", "error": str(resultado)[:100]}
                else:
                    resumen["resultados"][pid] = resultado

            log.info("scheduler.ronda_fin", resumen=resumen)
            return resumen

        finally:
            self._ejecutando = False

    # ----------------------------------------------------------
    # MANTENIMIENTO (cron semanal)
    # ----------------------------------------------------------

    def resetear_presupuestos(self):
        """Reset semanal de presupuestos de todos los procesos."""
        for p in self.procesos.values():
            p.resetear_presupuesto()
        log.info("scheduler.presupuestos_reset", n=len(self.procesos))

    async def health_check(self) -> dict[str, str]:
        """Health check de todos los procesos."""
        return {pid: p.salud for pid, p in self.procesos.items()
                if p.estado != EstadoProceso.TERMINADO}

    async def recovery(self):
        """Intenta recuperar procesos en estado ERROR."""
        for p in self.procesos.values():
            if p.estado == EstadoProceso.ERROR:
                log.info("scheduler.recovery", pid=p.pid)
                p.errores_consecutivos = 0
                p.estado = EstadoProceso.DORMIDO

    # ----------------------------------------------------------
    # ESTADISTICAS (top)
    # ----------------------------------------------------------

    @property
    def stats(self) -> dict:
        """Estadisticas del scheduler (como top)."""
        activos = self.listar_activos()
        return {
            "total_procesos": len(self.procesos),
            "activos": len(activos),
            "ejecutando": len([p for p in activos if p.estado == EstadoProceso.EJECUTANDO]),
            "dormidos": len([p for p in activos if p.estado == EstadoProceso.DORMIDO]),
            "pausados": len([p for p in activos if p.estado == EstadoProceso.PAUSADO]),
            "error": len([p for p in activos if p.estado == EstadoProceso.ERROR]),
            "presupuesto_total": sum(p.presupuesto_semanal for p in activos),
            "presupuesto_gastado": sum(p.presupuesto_gastado for p in activos),
            "ciclos_totales": sum(p.ciclos_ejecutados for p in activos),
        }
