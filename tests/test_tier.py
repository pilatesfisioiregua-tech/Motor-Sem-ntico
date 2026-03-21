"""Tests para src/gestor/tier.py — Decisión de tier."""
import pytest
from src.gestor.tier import decidir_tier


class TestDecidirTier:
    def test_conversacion_precompilado_tier1(self):
        assert decidir_tier("conversacion", tiene_programa_precompilado=True) == 1

    def test_conversacion_sin_precompilado_tier2(self):
        assert decidir_tier("conversacion") == 2

    def test_analisis_tier3(self):
        assert decidir_tier("analisis") == 3

    def test_confrontacion_tier3(self):
        assert decidir_tier("confrontacion") == 3

    def test_presupuesto_bajo_tier2(self):
        assert decidir_tier("analisis", presupuesto_max=0.10) == 2

    def test_forzar_tier(self):
        assert decidir_tier("conversacion", forzar_tier=5) == 5

    def test_forzar_tier_clamp(self):
        assert decidir_tier("analisis", forzar_tier=0) == 1
        assert decidir_tier("analisis", forzar_tier=99) == 5
