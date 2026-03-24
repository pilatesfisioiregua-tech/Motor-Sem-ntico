"""Tests predictor.py — importación y sugerencias."""
import pytest


class TestPredictor:
    def test_import(self):
        from src.pilates.predictor import predecir_abandonos, predecir_demanda_semana, predecir_cashflow_mes
        assert callable(predecir_abandonos)
        assert callable(predecir_demanda_semana)
        assert callable(predecir_cashflow_mes)

    def test_sugerir_accion(self):
        from src.pilates.predictor import _sugerir_accion
        assert "plan de pago" in _sugerir_accion(["Deuda 200€"], 50).lower()
        assert "WA" in _sugerir_accion(["0 asistencias últimas 2 semanas"], 50)
        assert "cortesía" in _sugerir_accion([], 20).lower()
        assert "WA" in _sugerir_accion(["Racha rota"], 60)
