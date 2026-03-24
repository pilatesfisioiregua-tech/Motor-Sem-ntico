"""Tests diagnosticador.py — diagnóstico ACD."""
import pytest


class TestDiagnosticadorImport:
    def test_import(self):
        from src.pilates.diagnosticador import diagnosticar_tenant
        assert callable(diagnosticar_tenant)

    def test_tenant(self):
        from src.pilates.diagnosticador import TENANT
        assert TENANT == "authentic_pilates"
