"""Tests json_utils — extracción JSON robusta."""
import pytest
from src.pilates.json_utils import extraer_json, extraer_json_lista


class TestExtraerJson:
    def test_json_directo(self):
        assert extraer_json('{"a": 1}') == {"a": 1}

    def test_json_markdown(self):
        assert extraer_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_con_texto(self):
        result = extraer_json('Aquí va: {"a": 1} y más texto')
        assert result == {"a": 1}

    def test_fallback(self):
        assert extraer_json("no json here", fallback={"x": 0}) == {"x": 0}

    def test_vacio(self):
        assert extraer_json("", fallback={}) == {}

    def test_array(self):
        result = extraer_json('[1, 2, 3]')
        assert result == [1, 2, 3]


class TestExtraerJsonLista:
    def test_lista_directa(self):
        assert extraer_json_lista('[1, 2]') == [1, 2]

    def test_sin_lista(self):
        assert extraer_json_lista("nada") == []
