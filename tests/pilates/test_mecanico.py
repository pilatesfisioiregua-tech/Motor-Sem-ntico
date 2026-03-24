"""Tests mecanico.py — clasificación de alertas."""
import pytest
from src.pilates.mecanico import clasificar, PROTEGIDOS


class TestClasificar:
    def test_protegido_siempre_arquitectural(self):
        for sub in PROTEGIDOS:
            assert clasificar({"subsistema": sub, "auto_fixable": True}) == "ARQUITECTURAL"

    def test_critical_siempre_arquitectural(self):
        assert clasificar({"subsistema": "bus", "severidad": "critical"}) == "ARQUITECTURAL"

    def test_auto_fixable_fontaneria(self):
        assert clasificar({"subsistema": "bus", "severidad": "medium", "auto_fixable": True}) == "FONTANERIA"

    def test_no_auto_fixable_arquitectural(self):
        assert clasificar({"subsistema": "bus", "severidad": "medium", "auto_fixable": False}) == "ARQUITECTURAL"
