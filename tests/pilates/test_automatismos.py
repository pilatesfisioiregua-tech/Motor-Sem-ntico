"""Tests automatismos.py — con DB mock."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date
from uuid import uuid4


def _make_mock_pool():
    """Crea mock de pool con context manager async correcto."""
    conn = AsyncMock()

    # pool.acquire() debe devolver un objeto sync que soporte async with
    acm = MagicMock()
    acm.__aenter__ = AsyncMock(return_value=conn)
    acm.__aexit__ = AsyncMock(return_value=False)

    pool = MagicMock()
    pool.acquire.return_value = acm

    return pool, conn


class TestFelicitarCumpleanos:
    @pytest.mark.asyncio
    async def test_sin_cumples_hoy(self):
        pool, conn = _make_mock_pool()
        conn.fetch.return_value = []  # Sin cumpleaños

        with patch("src.pilates.automatismos._get_pool", AsyncMock(return_value=pool)):
            from src.pilates.automatismos import felicitar_cumpleanos
            result = await felicitar_cumpleanos()
            assert result["cumpleanos_hoy"] == 0


class TestConciliarBizum:
    @pytest.mark.asyncio
    async def test_cliente_no_encontrado(self):
        pool, conn = _make_mock_pool()
        conn.fetchrow.return_value = None  # No existe

        with patch("src.pilates.automatismos._get_pool", AsyncMock(return_value=pool)):
            from src.pilates.automatismos import conciliar_bizum_entrante
            result = await conciliar_bizum_entrante("666999000", 55.0)
            assert result["status"] == "error"
