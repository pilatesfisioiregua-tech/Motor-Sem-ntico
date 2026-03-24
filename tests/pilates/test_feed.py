"""Tests feed.py — sistema de feed de eventos."""
import pytest


class TestFeedImport:
    def test_import(self):
        from src.pilates.feed import feed_pago, feed_vigia_alerta, feed_mecanico_fix
        assert callable(feed_pago)
        assert callable(feed_vigia_alerta)
        assert callable(feed_mecanico_fix)
