"""META — Circuito de gomas elásticas del motor perpetuo.

6 gomas + META (auto-reparación):
  G1: DATOS → SEÑALES
  G2: SEÑALES → DIAGNÓSTICO
  G3: DIAGNÓSTICO → BÚSQUEDA
  G4: BÚSQUEDA → PRESCRIPCIÓN
  G5: PRESCRIPCIÓN → ACCIÓN
  G6: ACCIÓN → APRENDIZAJE
  META: ROTURA → REPARACIÓN
"""
from organismo.meta.circuito_gomas import CircuitoGomas, Goma, EstadoGoma

__all__ = ["CircuitoGomas", "Goma", "EstadoGoma"]
