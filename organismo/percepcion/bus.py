"""Bus de percepción — converge 3 fuentes ANTES del procesamiento.

Arquitectura:
  Exterocepción ──┐
  Interocepción ──┼── BusPercepcion.recoger() ──► [Senal, ...]
  Propiocepción ──┘

Cada fuente tiene N sensores. Un sensor es una función async que
devuelve señales. El bus las unifica, prioriza y entrega al NodoVivo.

Fuente: L0_10 §Gomas, docs/L0/L0_8_SISTEMA_NERVIOSO.md
"""
from __future__ import annotations

import asyncio
import structlog
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from organismo.nodo_vivo import Senal

log = structlog.get_logger()


class SensorBase(ABC):
    """Base para sensores de percepción.

    Un sensor lee una fuente de datos y emite señales.
    Puede ser SQL, webhook, telemetría, o cualquier fuente.
    """

    def __init__(self, nombre: str, fuente: str, tenant_id: str):
        self.nombre = nombre
        self.fuente = fuente  # exterocepcion | interocepcion | propiocepcion_motora
        self.tenant_id = tenant_id

    @abstractmethod
    async def leer(self) -> list[Senal]:
        """Lee datos de la fuente y devuelve señales."""
        ...


class SensorSQL(SensorBase):
    """Sensor que ejecuta una query SQL y emite señales."""

    def __init__(self, nombre: str, fuente: str, tenant_id: str,
                 query: str, tipo_senal: str = "RESUMEN",
                 modo: str = "proceso", prioridad: int = 5):
        super().__init__(nombre, fuente, tenant_id)
        self.query = query
        self.tipo_senal = tipo_senal
        self.modo = modo
        self.prioridad = prioridad

    async def leer(self) -> list[Senal]:
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(self.query, self.tenant_id)
                if not rows:
                    return []
                return [Senal(
                    origen=f"sensor_{self.nombre}",
                    tipo=self.tipo_senal,
                    modo=self.modo,
                    fuente=self.fuente,
                    prioridad=self.prioridad,
                    payload={
                        "sensor": self.nombre,
                        "datos": [dict(r) for r in rows[:50]],
                        "total": len(rows),
                    },
                    tenant_id=self.tenant_id,
                )]
        except Exception as e:
            log.warning("sensor_sql_error", sensor=self.nombre, error=str(e)[:80])
            return []


class SensorPizarra(SensorBase):
    """Sensor que lee de la pizarra unificada."""

    def __init__(self, nombre: str, fuente: str, tenant_id: str,
                 tipo_pizarra: str, claves: list[str] = None):
        super().__init__(nombre, fuente, tenant_id)
        self.tipo_pizarra = tipo_pizarra
        self.claves = claves

    async def leer(self) -> list[Senal]:
        from organismo.pizarras.pizarra import PizarraUnificada
        pizarra = PizarraUnificada(self.tenant_id)

        if self.claves:
            datos = {}
            for clave in self.claves:
                val = await pizarra.leer(self.tipo_pizarra, clave)
                if val is not None:
                    datos[clave] = val
        else:
            datos = await pizarra.leer_tipo(self.tipo_pizarra)

        if not datos:
            return []

        return [Senal(
            origen=f"pizarra_{self.tipo_pizarra}",
            tipo="RESUMEN",
            modo="estado",
            fuente=self.fuente,
            payload=datos,
            tenant_id=self.tenant_id,
        )]


@dataclass
class BusPercepcion:
    """Bus que converge las 3 fuentes de percepción.

    Uso:
        bus = BusPercepcion(tenant_id="authentic_pilates")
        bus.registrar(SensorSQL("clientes_nuevos", "exterocepcion", ...))
        bus.registrar(SensorPizarra("estado_gomas", "interocepcion", ...))
        señales = await bus.recoger()
    """
    tenant_id: str
    sensores: list[SensorBase] = field(default_factory=list)

    def registrar(self, sensor: SensorBase) -> None:
        """Registra un sensor en el bus."""
        self.sensores.append(sensor)

    async def recoger(self, timeout: float = 30.0) -> list[Senal]:
        """Ejecuta todos los sensores en paralelo y converge señales.

        Las señales se ordenan por prioridad (1=urgente primero).
        """
        if not self.sensores:
            return []

        tareas = [sensor.leer() for sensor in self.sensores]

        try:
            resultados = await asyncio.wait_for(
                asyncio.gather(*tareas, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            log.warning("bus.timeout", tenant=self.tenant_id, timeout=timeout)
            return []

        señales = []
        for i, resultado in enumerate(resultados):
            if isinstance(resultado, Exception):
                log.warning("bus.sensor_error",
                            sensor=self.sensores[i].nombre,
                            error=str(resultado)[:80])
                continue
            señales.extend(resultado)

        # Ordenar por prioridad (1=urgente primero)
        señales.sort(key=lambda s: s.prioridad)

        log.info("bus.recogido",
                 tenant=self.tenant_id,
                 sensores=len(self.sensores),
                 señales=len(señales))

        return señales

    @property
    def sensores_por_fuente(self) -> dict[str, list[SensorBase]]:
        """Agrupa sensores por fuente de percepción."""
        por_fuente: dict[str, list[SensorBase]] = {}
        for s in self.sensores:
            por_fuente.setdefault(s.fuente, []).append(s)
        return por_fuente
