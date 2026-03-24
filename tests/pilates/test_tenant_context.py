"""Tests tenant_context.py — extracción de tenant."""
import pytest
from unittest.mock import MagicMock
from src.pilates.tenant_context import get_tenant_id, get_tenant_config, DEFAULT_TENANT


class TestGetTenantId:
    def test_fallback_sin_request(self):
        assert get_tenant_id() == DEFAULT_TENANT

    def test_from_state(self):
        req = MagicMock()
        req.state.tenant_id = "clinica_fisio"
        assert get_tenant_id(req) == "clinica_fisio"

    def test_from_header(self):
        req = MagicMock()
        req.state.tenant_id = None
        req.headers.get.return_value = "yoga_studio"
        assert get_tenant_id(req) == "yoga_studio"

    def test_fallback_con_request_vacio(self):
        req = MagicMock()
        req.state.tenant_id = None
        req.headers.get.return_value = None
        assert get_tenant_id(req) == DEFAULT_TENANT


class TestGetTenantConfig:
    def test_sin_request(self):
        config = get_tenant_config()
        assert config["tenant_id"] == DEFAULT_TENANT

    def test_con_config(self):
        req = MagicMock()
        req.state.tenant_config = {"tenant_id": "test", "nombre": "Test"}
        config = get_tenant_config(req)
        assert config["tenant_id"] == "test"
