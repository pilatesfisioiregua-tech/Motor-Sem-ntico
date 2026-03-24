"""Tests bus.py — validación de tipos."""
import pytest


class TestBusImport:
    def test_tipos_validos(self):
        from src.pilates.bus import TIPOS_VALIDOS
        assert "DATO" in TIPOS_VALIDOS
        assert "ALERTA" in TIPOS_VALIDOS
        assert "PRESCRIPCION" in TIPOS_VALIDOS
        assert "PERCEPCION_CAUSAL" in TIPOS_VALIDOS
        assert "INVENTADO" not in TIPOS_VALIDOS

    def test_functions_exist(self):
        from src.pilates.bus import emitir, leer_pendientes, marcar_procesada, marcar_error
        assert callable(emitir)
        assert callable(leer_pendientes)
