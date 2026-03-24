"""Tests cron.py — verificar estructura y timeouts."""
import pytest


class TestCronStructure:
    def test_import(self):
        from src.pilates.cron import cron_loop, _tarea_diaria
        assert callable(cron_loop)
        assert callable(_tarea_diaria)

    def test_tarea_semanal_exists(self):
        from src.pilates.cron import _tarea_semanal
        assert callable(_tarea_semanal)

    def test_timeout_constants(self):
        """Verificar que hay timeouts configurados."""
        import inspect
        from src.pilates import cron
        source = inspect.getsource(cron)
        assert "wait_for" in source or "timeout" in source.lower()
