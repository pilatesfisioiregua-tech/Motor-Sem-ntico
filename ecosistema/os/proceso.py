"""Proceso — Un exocortex en ejecucion.

Cada app instalada, cuando se ejecuta, se convierte en un Proceso.
Un Proceso es un wrapper del Enjambre con metadatos de OS.

Analogia:
  App instalada = binario en disco
  Proceso       = binario en ejecucion con PID, estado, memoria
  Enjambre      = el codigo que ejecuta el proceso
  tenant_id     = PID del proceso
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from zoneinfo import ZoneInfo

from organismo.cognitiva.enjambre import Enjambre
from organismo.cognitiva.director import Director
from organismo.meta.circuito_gomas import CircuitoGomas
from ecosistema.memoria.almacen import Almacen

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


class EstadoProceso(str, Enum):
    """Estado de un proceso del OS."""
    CREADO = "creado"           # App instalada, nunca ejecutada
    EJECUTANDO = "ejecutando"   # Ciclo en curso
    DORMIDO = "dormido"         # Esperando proximo ciclo (idle)
    PAUSADO = "pausado"         # CR1 frenado por propietario
    ERROR = "error"             # Fallo, requiere atencion
    TERMINADO = "terminado"     # App desinstalada


@dataclass
class Proceso:
    """Un exocortex en ejecucion.

    Es la unidad que el Scheduler gestiona.
    Cada Proceso tiene:
      - pid: identificador unico (= tenant_id)
      - app_id: que app ejecuta (sector + config)
      - enjambre: el motor cognitivo que ejecuta
      - memoria: acceso al filesystem del tenant
      - metricas: uso de recursos
    """
    pid: str                    # = tenant_id
    app_id: str                 # sector + nombre
    nombre: str
    sector: str
    estado: EstadoProceso = EstadoProceso.CREADO
    prioridad: int = 5          # 1=critico, 5=normal, 10=background

    # Recursos asignados
    presupuesto_semanal: float = 5.0   # $ LLM por semana
    presupuesto_gastado: float = 0.0

    # Metricas del proceso
    ciclos_ejecutados: int = 0
    ultimo_ciclo: Optional[datetime] = None
    errores_consecutivos: int = 0
    uptime_horas: float = 0.0

    # Componentes internos (lazy init)
    _enjambre: Optional[Enjambre] = field(default=None, repr=False)
    _memoria: Optional[Almacen] = field(default=None, repr=False)

    @property
    def memoria(self) -> Almacen:
        """Acceso al filesystem del proceso."""
        if self._memoria is None:
            self._memoria = Almacen(self.pid)
        return self._memoria

    @property
    def enjambre(self) -> Enjambre:
        """Motor cognitivo del proceso."""
        if self._enjambre is None:
            director = Director(self.pid)
            circuito = CircuitoGomas(self.pid)
            self._enjambre = Enjambre(self.pid, director, circuito)
        return self._enjambre

    async def ejecutar_ciclo(self) -> dict:
        """Ejecuta un ciclo del proceso (= enjambre.ciclo())."""
        if self.estado == EstadoProceso.PAUSADO:
            log.warning("proceso.pausado", pid=self.pid)
            return {"estado": "pausado"}

        if self.presupuesto_gastado >= self.presupuesto_semanal:
            log.warning("proceso.sin_presupuesto", pid=self.pid)
            return {"estado": "sin_presupuesto"}

        self.estado = EstadoProceso.EJECUTANDO
        try:
            resultado = await self.enjambre.ciclo()

            self.ciclos_ejecutados += 1
            self.ultimo_ciclo = datetime.now(MADRID_TZ)
            self.errores_consecutivos = 0
            self.estado = EstadoProceso.DORMIDO

            # Actualizar presupuesto gastado
            for s in (resultado or []):
                self.presupuesto_gastado += s.payload.get("coste_usd", 0)

            return {
                "estado": "ok",
                "señales": len(resultado) if resultado else 0,
                "coste_ciclo": sum(
                    s.payload.get("coste_usd", 0) for s in (resultado or [])
                ),
            }
        except Exception as e:
            self.errores_consecutivos += 1
            if self.errores_consecutivos >= 3:
                self.estado = EstadoProceso.ERROR
            else:
                self.estado = EstadoProceso.DORMIDO

            log.error("proceso.ciclo_error",
                      pid=self.pid, error=str(e)[:120],
                      errores=self.errores_consecutivos)
            return {"estado": "error", "error": str(e)[:200]}

    def pausar(self):
        """CR1: Pausa el proceso (propietario)."""
        self.estado = EstadoProceso.PAUSADO
        log.warning("proceso.CR1_pausado", pid=self.pid)

    def reanudar(self):
        """CR1: Reanuda el proceso."""
        if self.estado == EstadoProceso.PAUSADO:
            self.estado = EstadoProceso.DORMIDO
            log.info("proceso.reanudado", pid=self.pid)

    def resetear_presupuesto(self):
        """Llamar al inicio de cada semana."""
        self.presupuesto_gastado = 0.0

    @property
    def salud(self) -> str:
        """Health check rapido del proceso."""
        if self.estado == EstadoProceso.ERROR:
            return "critico"
        if self.estado == EstadoProceso.PAUSADO:
            return "pausado"
        if self.errores_consecutivos > 0:
            return "degradado"
        if self.presupuesto_gastado / max(self.presupuesto_semanal, 0.01) > 0.9:
            return "presupuesto_bajo"
        return "ok"
