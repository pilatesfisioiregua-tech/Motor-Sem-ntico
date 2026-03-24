"""Event Sourcing + CQRS — memoria episodica del OS.

Event Sourcing (Kafka/EventStoreDB):
  om_pizarra es PROYECCION de un log inmutable de eventos.
  El sistema recuerda no solo QUE sabe, sino COMO llego a saberlo.

CQRS:
  Escritura → log de eventos (append-only, simple, rapido)
  Lectura → multiples vistas optimizadas por caso de uso
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from zoneinfo import ZoneInfo

log = structlog.get_logger()
MADRID_TZ = ZoneInfo("Europe/Madrid")


@dataclass
class EventoCognitivo:
    """Evento inmutable en el log del sistema.

    Cada cambio al conocimiento es un evento:
      - ConocimientoCreado, ConocimientoActualizado, ConocimientoArchivado
      - DiagnosticoRealizado, PrescripcionEmitida, RecetaTransferida
      - AgenteCicloInicio, AgenteCicloFin, ErrorDetectado
    """
    tipo_evento: str              # ConocimientoCreado, PrescripcionEmitida, etc.
    tenant_id: str
    agente: str                   # Quien genero el evento (identidad F5)
    datos: dict                   # Payload del evento
    metadata: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(MADRID_TZ))
    ciclo: str = ""
    version: int = 1              # Version del schema del evento


class EventLog:
    """Log inmutable de eventos — la fuente de verdad.

    Append-only: los eventos NUNCA se modifican ni borran.
    om_pizarra se reconstruye proyectando estos eventos.
    """

    def __init__(self, tenant_id: str = "os"):
        self.tenant_id = tenant_id

    async def append(self, evento: EventoCognitivo) -> Optional[int]:
        """Anade un evento al log. Devuelve el ID del evento."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                row = await conn.fetchrow("""
                    INSERT INTO om_event_log
                        (tenant_id, tipo_evento, agente, datos, metadata, ciclo, version)
                    VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7)
                    RETURNING id
                """, evento.tenant_id, evento.tipo_evento, evento.agente,
                    json.dumps(evento.datos), json.dumps(evento.metadata),
                    evento.ciclo, evento.version)
                return row["id"]
        except Exception as e:
            log.debug("event_log.append_error", error=str(e)[:80])
            return None

    async def leer(self, desde_id: int = 0, limite: int = 100,
                   tipo_evento: str = None, agente: str = None,
                   ) -> list[EventoCognitivo]:
        """Lee eventos del log (para proyecciones o replay)."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()

            filtros = ["tenant_id = $1", "id > $2"]
            params = [self.tenant_id, desde_id]
            idx = 3

            if tipo_evento:
                filtros.append(f"tipo_evento = ${idx}")
                params.append(tipo_evento)
                idx += 1

            if agente:
                filtros.append(f"agente = ${idx}")
                params.append(agente)
                idx += 1

            sql = f"""
                SELECT id, tipo_evento, agente, datos, metadata, ciclo, version, created_at
                FROM om_event_log
                WHERE {' AND '.join(filtros)}
                ORDER BY id ASC
                LIMIT {limite}
            """

            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)

            return [
                EventoCognitivo(
                    tipo_evento=r["tipo_evento"],
                    tenant_id=self.tenant_id,
                    agente=r["agente"],
                    datos=json.loads(r["datos"]) if isinstance(r["datos"], str) else r["datos"],
                    metadata=json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"],
                    ciclo=r["ciclo"],
                    version=r["version"],
                    timestamp=r["created_at"],
                )
                for r in rows
            ]
        except Exception as e:
            log.debug("event_log.leer_error", error=str(e)[:80])
            return []

    async def contar(self, tipo_evento: str = None) -> int:
        """Cuenta eventos en el log."""
        try:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                if tipo_evento:
                    return await conn.fetchval("""
                        SELECT count(*) FROM om_event_log
                        WHERE tenant_id = $1 AND tipo_evento = $2
                    """, self.tenant_id, tipo_evento)
                return await conn.fetchval("""
                    SELECT count(*) FROM om_event_log
                    WHERE tenant_id = $1
                """, self.tenant_id)
        except Exception:
            return 0


class Proyector:
    """Proyecta eventos del log en vistas materializadas.

    Cada proyeccion transforma el stream de eventos en una vista
    optimizada para un caso de uso especifico.
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.event_log = EventLog(tenant_id)

    async def proyectar_estado_actual(self, desde_id: int = 0):
        """Proyecta eventos → om_pizarra (estado actual)."""
        eventos = await self.event_log.leer(desde_id=desde_id, limite=1000)

        from ecosistema.memoria.almacen import Almacen
        almacen = Almacen(self.tenant_id)

        for ev in eventos:
            if ev.tipo_evento == "ConocimientoCreado":
                await almacen.escribir(
                    ev.datos.get("tipo", "estado"),
                    ev.datos.get("clave", "unknown"),
                    ev.datos.get("valor", {}),
                    ciclo=ev.ciclo,
                )
            elif ev.tipo_evento == "ConocimientoArchivado":
                await almacen.borrar(
                    ev.datos.get("tipo", "estado"),
                    ev.datos.get("clave", "unknown"),
                )

        log.info("proyector.estado_actualizado",
                 tenant=self.tenant_id, eventos=len(eventos))

    async def proyectar_timeline(self, limite: int = 50) -> list[dict]:
        """Proyecta eventos → vista cronologica."""
        eventos = await self.event_log.leer(limite=limite)
        return [
            {
                "timestamp": ev.timestamp.isoformat() if ev.timestamp else "",
                "tipo": ev.tipo_evento,
                "agente": ev.agente,
                "resumen": str(ev.datos)[:100],
                "ciclo": ev.ciclo,
            }
            for ev in eventos
        ]

    async def time_travel(self, hasta: datetime) -> dict:
        """Reconstruye el estado del conocimiento en un momento dado."""
        eventos = await self.event_log.leer(limite=10000)

        estado = {}
        for ev in eventos:
            if ev.timestamp and ev.timestamp > hasta:
                break
            if ev.tipo_evento == "ConocimientoCreado":
                tipo = ev.datos.get("tipo", "estado")
                clave = ev.datos.get("clave", "?")
                estado[f"{tipo}/{clave}"] = ev.datos.get("valor")
            elif ev.tipo_evento == "ConocimientoArchivado":
                tipo = ev.datos.get("tipo", "estado")
                clave = ev.datos.get("clave", "?")
                estado.pop(f"{tipo}/{clave}", None)

        return estado
