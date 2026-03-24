"""Tests RGPD + Audit Log — Apple-grade privacy."""
import pytest
from src.pilates.audit_log import registrar, consultar
from src.pilates.rgpd import exportar_datos_cliente, solicitar_borrado


class TestAuditLog:
    def test_import(self):
        """Audit log se importa correctamente."""
        assert callable(registrar)
        assert callable(consultar)


class TestRGPD:
    def test_import(self):
        """RGPD se importa correctamente."""
        assert callable(exportar_datos_cliente)
        assert callable(solicitar_borrado)

    def test_exportar_requiere_cliente_id(self):
        """exportar_datos_cliente necesita UUID."""
        import inspect
        sig = inspect.signature(exportar_datos_cliente)
        assert "cliente_id" in sig.parameters
        assert "tenant_id" in sig.parameters
