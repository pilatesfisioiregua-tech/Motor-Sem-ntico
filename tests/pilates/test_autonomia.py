"""Tests autonomia.py — motor de decisión 3 niveles."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestDecidirNivel:
    @pytest.mark.asyncio
    async def test_auto(self):
        dominio = {"config": {"autonomia": {
            "auto": ["confirmacion_sesion", "felicitacion_cumpleanos"],
            "notificar_4h": ["cerrar_grupo_bajo"],
            "cr1_siempre": ["subir_precio_10pct"],
        }}}
        with patch("src.pilates.pizarras.leer_dominio", AsyncMock(return_value=dominio)):
            from src.pilates.autonomia import decidir_nivel
            assert await decidir_nivel("confirmacion_sesion") == "auto"

    @pytest.mark.asyncio
    async def test_notificar(self):
        dominio = {"config": {"autonomia": {
            "auto": ["confirmacion_sesion"],
            "notificar_4h": ["cerrar_grupo_bajo"],
        }}}
        with patch("src.pilates.pizarras.leer_dominio", AsyncMock(return_value=dominio)):
            from src.pilates.autonomia import decidir_nivel
            assert await decidir_nivel("cerrar_grupo_bajo") == "notificar_4h"

    @pytest.mark.asyncio
    async def test_cr1_subir_precio(self):
        """subir_precio_10pct no está en auto ni notificar → cr1."""
        dominio = {"config": {"autonomia": {
            "auto": ["confirmacion_sesion"],
            "notificar_4h": ["cerrar_grupo_bajo"],
        }}}
        with patch("src.pilates.pizarras.leer_dominio", AsyncMock(return_value=dominio)):
            from src.pilates.autonomia import decidir_nivel
            assert await decidir_nivel("subir_precio_10pct") == "cr1"

    @pytest.mark.asyncio
    async def test_cr1_accion_desconocida(self):
        """Acción desconocida → cr1 (conservador)."""
        dominio = {"config": {"autonomia": {"auto": []}}}
        with patch("src.pilates.pizarras.leer_dominio", AsyncMock(return_value=dominio)):
            from src.pilates.autonomia import decidir_nivel
            assert await decidir_nivel("accion_desconocida") == "cr1"

    @pytest.mark.asyncio
    async def test_cr1_sin_config(self):
        dominio = {"config": {}}
        with patch("src.pilates.pizarras.leer_dominio", AsyncMock(return_value=dominio)):
            from src.pilates.autonomia import decidir_nivel
            assert await decidir_nivel("cualquier_cosa") == "cr1"
