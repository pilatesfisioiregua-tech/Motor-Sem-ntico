"""Tests director_opus.py — Director Opus del organismo."""
import pytest


class TestDirectorImport:
    def test_import(self):
        from src.pilates.director_opus import dirigir_orquesta
        assert callable(dirigir_orquesta)

    def test_tenant(self):
        from src.pilates.director_opus import TENANT
        assert TENANT == "authentic_pilates"
