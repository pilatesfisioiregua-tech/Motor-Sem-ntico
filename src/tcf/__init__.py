"""Módulo TCF — Teoría del Campo Funcional como código ejecutable.

Implementa las 14 leyes + 5 teoremas de la TCF:
  - constantes: tablas INT×F, INT×L, dependencias, valoración lentes, arquetipos, firmas
  - campo: VectorFuncional, EstadoCampo, evaluar_campo()
  - campo_dual: CeldaCampo, VectorFuncionalDual, EstadoCampoDual (P41)
  - arquetipos: scoring_multi_arquetipo(), pre_screening_linguistico()
  - recetas: 11 recetas + generar_receta_mixta() + aplicar_regla_14()
  - lentes: ecuacion_transferencia(), identificar_perfil_lente(), es_equilibrio_nash()
  - detector_tcf: integración con detector de huecos existente
"""
from __future__ import annotations

import json
from pathlib import Path

_TCF_BASE = Path(__file__).parent
_estados: dict | None = None


def load_estados() -> dict:
    """Carga estados.json en memoria (singleton)."""
    global _estados
    if _estados is None:
        _estados = json.loads((_TCF_BASE / "estados.json").read_text())
    return _estados
