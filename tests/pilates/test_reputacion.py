"""Tests reputacion.py — importación y constantes."""
import pytest
from src.pilates.reputacion import MAX_PEDIDOS_SEMANA, SESIONES_MIN, ENGAGEMENT_MIN


class TestReputacion:
    def test_constantes(self):
        assert MAX_PEDIDOS_SEMANA == 3
        assert SESIONES_MIN == 8
        assert ENGAGEMENT_MIN == 70

    def test_import(self):
        from src.pilates.reputacion import detectar_clientes_contentos, programar_pedidos_resena
        assert callable(detectar_clientes_contentos)
        assert callable(programar_pedidos_resena)
