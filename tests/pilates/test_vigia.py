"""Tests vigia.py — checks de salud."""
import pytest
from src.pilates.vigia import CheckResult, CATEGORIAS_DEGRADACION


class TestCheckResult:
    def test_defaults(self):
        r = CheckResult("test", "ok", "todo bien")
        assert r.severidad == "low"
        assert r.auto_fixable is False

    def test_custom(self):
        r = CheckResult("bus", "error", "saturado", "critical", True, "limpiar")
        assert r.auto_fixable
        assert r.fix_hint == "limpiar"


class TestCategorias:
    def test_todas_tienen_check(self):
        for cat, info in CATEGORIAS_DEGRADACION.items():
            assert "check" in info
            assert "reparacion" in info

    def test_auto_flags(self):
        auto = [k for k, v in CATEGORIAS_DEGRADACION.items() if v.get("auto")]
        assert "bus_saturado" in auto
        assert "cache_lleno" in auto
        no_auto = [k for k, v in CATEGORIAS_DEGRADACION.items() if not v.get("auto")]
        assert "db_lenta" in no_auto
