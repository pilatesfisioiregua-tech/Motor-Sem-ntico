"""Tests http_client.py — singleton y rate_limit."""
import pytest


class TestHttpClientSingleton:
    def test_import(self):
        from src.pilates.http_client import get_http_client, close_http_client
        assert callable(get_http_client)
        assert callable(close_http_client)

    @pytest.mark.asyncio
    async def test_singleton_returns_same(self):
        from src.pilates.http_client import get_http_client
        c1 = await get_http_client()
        c2 = await get_http_client()
        assert c1 is c2

    @pytest.mark.asyncio
    async def test_has_timeout(self):
        from src.pilates.http_client import get_http_client
        client = await get_http_client()
        assert client.timeout.read == 30.0
