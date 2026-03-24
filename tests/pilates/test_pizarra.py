"""Tests pizarra.py — pizarra compartida inter-agentes."""
import pytest


class TestPizarraImport:
    def test_import(self):
        from src.pilates.pizarra import escribir, leer_relevante, leer_todo
        assert callable(escribir)
        assert callable(leer_relevante)
        assert callable(leer_todo)

    def test_capas_definidas(self):
        """Verificar que las capas de la pizarra están definidas."""
        import inspect
        from src.pilates import pizarra
        source = inspect.getsource(pizarra)
        assert "escribir" in source
