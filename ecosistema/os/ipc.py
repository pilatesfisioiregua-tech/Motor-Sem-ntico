"""IPC — Inter-Process Communication entre apps.

Las apps (exocortex) no comparten datos de negocio.
Pero el OS puede transferir RECETAS entre apps via IPC.

Analogia:
  IPC          = pipes/sockets entre procesos
  Transferencia = mensaje IPC (receta + evidencia + confianza)
  App Store    = el catalogo de recetas disponibles

Ley 10 TCF: La transferencia es por similaridad del GAP, no del dominio.
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass, field
from typing import Optional

log = structlog.get_logger()


@dataclass
class MensajeIPC:
    """Mensaje entre apps via el bus IPC del OS.

    NO contiene datos de negocio — solo recetas y metadatos.
    """
    origen_pid: str              # PID de la app origen
    destino_pid: str             # PID de la app destino
    tipo: str                    # "transferencia" | "alerta" | "heartbeat"
    gap: str = ""                # F3_baja, F6_baja, etc.
    payload: dict = field(default_factory=dict)
    similaridad: float = 0.0     # Coseno entre contextos
    confianza: float = 0.0       # tasa_cierre × similaridad
    requiere_cr1: bool = True    # SIEMPRE True para transferencias


class BusIPC:
    """Bus de comunicacion inter-proceso del OS.

    Las apps no se hablan directamente entre si.
    Todo pasa por el bus del OS, que garantiza:
      - Aislamiento de datos de negocio
      - Solo recetas y metricas anonimizadas
      - CR1 del propietario destino antes de aplicar
    """

    def __init__(self):
        self._cola: list[MensajeIPC] = []
        self._historial: list[MensajeIPC] = []

    def enviar(self, mensaje: MensajeIPC) -> None:
        """Encola un mensaje IPC."""
        self._cola.append(mensaje)
        log.debug("ipc.enviado",
                  origen=mensaje.origen_pid,
                  destino=mensaje.destino_pid,
                  tipo=mensaje.tipo)

    def recibir(self, pid: str) -> list[MensajeIPC]:
        """Lee mensajes pendientes para un proceso."""
        propios = [m for m in self._cola if m.destino_pid == pid]
        self._cola = [m for m in self._cola if m.destino_pid != pid]
        self._historial.extend(propios)
        return propios

    def broadcast(self, origen_pid: str, tipo: str,
                  payload: dict, excluir: list[str] = None) -> None:
        """Envia mensaje a todos los procesos (excepto excluidos)."""
        excluir = excluir or [origen_pid]
        # El scheduler anadira los PIDs al enviar
        self._cola.append(MensajeIPC(
            origen_pid=origen_pid,
            destino_pid="*",  # broadcast
            tipo=tipo,
            payload=payload,
        ))

    @property
    def mensajes_pendientes(self) -> int:
        return len(self._cola)

    @property
    def stats(self) -> dict:
        return {
            "pendientes": len(self._cola),
            "historial": len(self._historial),
            "por_tipo": {},
        }


class AppStore:
    """Catalogo de recetas transferibles — el App Store del OS.

    Cuando una receta funciona en una app (exocortex), se publica
    en el App Store como disponible para apps con gaps similares.

    El MOAT: N apps × M ciclos = catalogo intransferible.
    """

    def __init__(self):
        self._catalogo: list[dict] = []

    def publicar(self, receta: dict, evidencia: dict) -> None:
        """Publica una receta exitosa en el catalogo."""
        self._catalogo.append({
            "receta": receta,
            "evidencia": evidencia,
            "descargas": 0,
        })

    def buscar(self, gap: str, sector: str = None,
               min_confianza: float = 0.6) -> list[dict]:
        """Busca recetas en el catalogo por gap."""
        resultados = []
        for item in self._catalogo:
            receta = item["receta"]
            evidencia = item["evidencia"]

            if receta.get("gap") != gap:
                continue
            if evidencia.get("confianza", 0) < min_confianza:
                continue
            if sector and receta.get("sector") != sector:
                continue

            resultados.append(item)

        resultados.sort(key=lambda r: r["evidencia"].get("confianza", 0),
                       reverse=True)
        return resultados

    @property
    def total_recetas(self) -> int:
        return len(self._catalogo)
