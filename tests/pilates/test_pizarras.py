"""Tests pizarras.py — lectura con fallback."""
import pytest
from src.pilates.pizarras import leer_dominio, leer_modelo, DEFAULT_DOMINIO


class TestPizarraFallbacks:
    """Testa que los fallbacks funcionan sin DB."""

    @pytest.mark.asyncio
    async def test_dominio_fallback_sin_db(self):
        """Sin DB, devuelve DEFAULT_DOMINIO."""
        result = await leer_dominio("tenant_inexistente")
        assert result["tenant_id"] == DEFAULT_DOMINIO["tenant_id"]

    @pytest.mark.asyncio
    async def test_modelo_fallback_sin_db(self):
        """Sin DB, devuelve modelo por defecto según complejidad."""
        result = await leer_modelo("x", "F1", None, "baja")
        assert "deepseek" in result.lower()

    @pytest.mark.asyncio
    async def test_modelo_fallback_alta(self):
        result = await leer_modelo("x", "F1", None, "alta")
        assert "opus" in result.lower() or "claude" in result.lower()
