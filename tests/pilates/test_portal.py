"""Tests portal.py — portal público del cliente."""
import pytest


class TestPortalImport:
    def test_import(self):
        from src.pilates.portal import router
        assert router is not None
        assert router.prefix == "/portal"
