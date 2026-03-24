"""Bus de Percepción Unificado — 3 fuentes × 9 modos.

Exterocepción (datos negocio) + Interocepción (telemetría) +
Propiocepción Motora (delta prescripción vs resultado)
convergen ANTES del procesamiento.
"""
from organismo.percepcion.bus import BusPercepcion, SensorBase

__all__ = ["BusPercepcion", "SensorBase"]
