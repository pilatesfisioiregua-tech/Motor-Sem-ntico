"""Tests redsys_pagos — firma HMAC SHA-256 y generación de pedidos."""
import base64
import json
import pytest
from src.pilates.redsys_pagos import (
    _encode_params, _decode_params, _generate_order,
    _sign, _decode_key, _encrypt_order,
)


class TestRedsysParams:
    def test_encode_decode_roundtrip(self):
        params = {"Ds_Merchant_Amount": "5500", "Ds_Merchant_Currency": "978"}
        encoded = _encode_params(params)
        decoded = _decode_params(encoded)
        assert decoded == params

    def test_generate_order_format(self):
        order = _generate_order()
        assert len(order) == 12
        assert order[:4].isdigit()

    def test_generate_order_unique(self):
        orders = {_generate_order() for _ in range(100)}
        assert len(orders) >= 95  # Al menos 95% únicos


class TestRedsysFirma:
    """Tests de firma con clave ficticia."""

    @pytest.fixture
    def fake_key_b64(self):
        # Clave de 24 bytes en base64 (3DES necesita 24 bytes)
        return base64.b64encode(b"0123456789ABCDEF01234567").decode()

    def test_encrypt_order_deterministic(self, fake_key_b64):
        key = _decode_key(fake_key_b64)
        result1 = _encrypt_order("1234", key)
        result2 = _encrypt_order("1234", key)
        assert result1 == result2

    def test_sign_deterministic(self, fake_key_b64, monkeypatch):
        monkeypatch.setattr("src.pilates.redsys_pagos.SECRET_KEY", fake_key_b64)
        params_b64 = _encode_params({"Ds_Merchant_Amount": "5500"})
        sig1 = _sign(params_b64, "00001234")
        sig2 = _sign(params_b64, "00001234")
        assert sig1 == sig2

    def test_sign_different_orders(self, fake_key_b64, monkeypatch):
        monkeypatch.setattr("src.pilates.redsys_pagos.SECRET_KEY", fake_key_b64)
        params_b64 = _encode_params({"Ds_Merchant_Amount": "5500"})
        sig1 = _sign(params_b64, "00001234")
        sig2 = _sign(params_b64, "00005678")
        assert sig1 != sig2
