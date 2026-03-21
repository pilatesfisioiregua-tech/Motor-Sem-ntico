"""Decisión de tier de enjambre.

Maestro §4.4:
  Tier 1 — Reflejo:      lookup precompilado, $0
  Tier 2 — Respuesta:    1 modelo barato, $0.01-0.05
  Tier 3 — Análisis:     3-5 modelos, $0.10-0.50
  Tier 4 — Profundo:     7+ modelos pizarra, $0.50-2.00
  Tier 5 — Cartografía:  exploración completa, $5-20
"""
from __future__ import annotations


def decidir_tier(
    modo: str,
    tiene_programa_precompilado: bool = False,
    forzar_tier: int | None = None,
    presupuesto_max: float = 1.50,
) -> int:
    """Decide el tier de enjambre según contexto.

    Maestro §4.4:
      ¿Respuesta precompilada? → TIER 1
      ¿Conversación normal?   → TIER 2
      ¿Análisis o decisión?   → TIER 3
      ¿Batch (nadie espera)?  → TIER 4
      ¿Dominio nuevo?         → TIER 5
    """
    if forzar_tier is not None:
        return max(1, min(5, forzar_tier))

    # Tier 1: lookup directo
    if tiene_programa_precompilado and modo == "conversacion":
        return 1

    # Tier 2: conversación sin programa previo
    if modo == "conversacion":
        return 2

    # Tier 3: análisis (default para la mayoría)
    if modo in ("analisis", "confrontacion", "generacion"):
        if presupuesto_max < 0.20:
            return 2
        return 3

    # Default
    return 3


# Costes y tiempos estimados por tier
TIER_CONFIG = {
    1: {"coste_est": 0.00,  "tiempo_est_s": 0.2,   "desc": "Reflejo (lookup)"},
    2: {"coste_est": 0.03,  "tiempo_est_s": 10,     "desc": "Respuesta (1 modelo)"},
    3: {"coste_est": 0.30,  "tiempo_est_s": 90,     "desc": "Análisis (3-5 modelos)"},
    4: {"coste_est": 2.00,  "tiempo_est_s": 2700,   "desc": "Profundo (pizarra)"},
    5: {"coste_est": 10.00, "tiempo_est_s": 10800,  "desc": "Cartografía (exploración)"},
}
