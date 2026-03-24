"""Tests compositor.py — compositor del organismo."""
import pytest


class TestCompositorImport:
    def test_import(self):
        from src.pilates.compositor import ejecutar_g4
        assert callable(ejecutar_g4)

    def test_tenant(self):
        from src.pilates.compositor import TENANT
        assert TENANT == "authentic_pilates"
