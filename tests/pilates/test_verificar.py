"""Tests motor/verificar.py — verificación post-output."""
import pytest
from src.motor.verificar import verificar, ResultadoVerificacion


class TestVerificar:
    def test_output_normal(self):
        r = verificar("Este es un texto normal de análisis suficientemente largo para pasar.")
        assert r.ok
        assert r.score >= 0.8

    def test_output_vacio(self):
        r = verificar("")
        assert not r.ok
        assert r.score == 0.0

    def test_output_generico(self):
        r = verificar("Como asistente de IA, es importante considerar muchos factores.")
        assert len(r.warnings) > 0
        assert r.score < 1.0

    def test_f3_no_sugiere_adicion(self):
        r = verificar("Deberíamos añadir un nuevo servicio premium.", funcion="F3")
        assert any("F3" in w for w in r.warnings)

    def test_json_malformado(self):
        r = verificar('{"key": value_sin_comillas}')
        # Debería detectar JSON malformado
        assert r.score < 1.0
