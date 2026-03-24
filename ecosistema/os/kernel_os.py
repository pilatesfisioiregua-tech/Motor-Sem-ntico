"""Kernel del OS — boot, shutdown, tabla de procesos.

El KernelOS es el punto de entrada del sistema operativo.
Arranca todos los componentes, carga apps instaladas, inicia scheduler.

Analogia:
  KernelOS     = init/systemd (PID 1)
  boot()       = arranque del sistema
  shutdown()   = apagado ordenado
  instalar_app = apt install / App Store download
  ps()         = tabla de procesos
"""
from __future__ import annotations

import structlog
from typing import Optional

from ecosistema.os.scheduler import Scheduler
from ecosistema.os.proceso import Proceso, EstadoProceso
from ecosistema.os.ipc import BusIPC
from ecosistema.memoria.almacen import Almacen

log = structlog.get_logger()


class KernelOS:
    """Kernel del Sistema Operativo OMNI-MIND.

    Responsabilidades:
      1. Boot: cargar apps instaladas desde DB, iniciar scheduler
      2. Instalar/desinstalar apps (exocortex)
      3. Gestionar IPC entre apps
      4. Shutdown ordenado
    """

    def __init__(self):
        self.scheduler = Scheduler()
        self.ipc = BusIPC()
        self.memoria_os = Almacen("os")  # Memoria del propio OS
        self._booted = False

    async def boot(self) -> dict:
        """Arranca el sistema operativo.

        1. Lee apps instaladas desde memoria (om_pizarra dominio)
        2. Crea un Proceso por cada app
        3. Registra en scheduler
        """
        log.info("os.boot_inicio")

        # Leer todos los tenants registrados
        tenants = await self.memoria_os.leer_todos_tenants()

        for tenant_id in tenants:
            almacen = Almacen(tenant_id)
            config = await almacen.leer("dominio", "config")
            if not config:
                continue

            proceso = Proceso(
                pid=tenant_id,
                app_id=f"{config.get('sector', 'general')}_{tenant_id}",
                nombre=config.get("nombre", tenant_id),
                sector=config.get("sector", "general"),
                estado=EstadoProceso.DORMIDO,
                presupuesto_semanal=config.get("presupuesto_llm_semanal", 5.0),
            )
            self.scheduler.registrar(proceso)

        self._booted = True
        stats = self.scheduler.stats

        log.info("os.boot_completado",
                 procesos=stats["total_procesos"],
                 activos=stats["activos"])

        return {
            "estado": "ok",
            "procesos_cargados": stats["total_procesos"],
        }

    async def shutdown(self) -> dict:
        """Apagado ordenado del OS."""
        log.info("os.shutdown_inicio")

        # Pausar todos los procesos
        for p in self.scheduler.listar_activos():
            if p.estado == EstadoProceso.EJECUTANDO:
                p.pausar()

        self._booted = False
        log.info("os.shutdown_completado")
        return {"estado": "apagado"}

    async def instalar_app(self, tenant_id: str, nombre: str,
                            sector: str = "general",
                            presupuesto: float = 5.0,
                            **kwargs) -> Proceso:
        """Instala una nueva app (exocortex) en el OS.

        1. Ejecuta onboarding (seeds pizarras)
        2. Crea Proceso
        3. Registra en scheduler
        """
        from tenant.onboarding import onboarding_tenant

        # Onboarding = instalacion de la app
        await onboarding_tenant(
            tenant_id=tenant_id,
            nombre=nombre,
            sector=sector,
            presupuesto_llm_semanal=presupuesto,
            **kwargs,
        )

        proceso = Proceso(
            pid=tenant_id,
            app_id=f"{sector}_{tenant_id}",
            nombre=nombre,
            sector=sector,
            estado=EstadoProceso.DORMIDO,
            presupuesto_semanal=presupuesto,
        )
        self.scheduler.registrar(proceso)

        log.info("os.app_instalada", pid=tenant_id, sector=sector)
        return proceso

    async def desinstalar_app(self, tenant_id: str) -> bool:
        """Desinstala una app (marca como terminada, NO borra datos)."""
        ok = self.scheduler.terminar(tenant_id)
        if ok:
            log.info("os.app_desinstalada", pid=tenant_id)
        return ok

    def ps(self) -> list[dict]:
        """Tabla de procesos (ps aux)."""
        return [
            {
                "pid": p.pid,
                "app": p.app_id,
                "nombre": p.nombre,
                "estado": p.estado.value,
                "prioridad": p.prioridad,
                "presupuesto": f"${p.presupuesto_gastado:.2f}/${p.presupuesto_semanal:.2f}",
                "ciclos": p.ciclos_ejecutados,
                "salud": p.salud,
            }
            for p in self.scheduler.listar_activos()
        ]

    def top(self) -> dict:
        """Estadisticas globales del OS (top)."""
        return self.scheduler.stats
