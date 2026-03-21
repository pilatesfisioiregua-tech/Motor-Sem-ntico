"""Test que el evaluador integra TCF."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.detector_tcf import detectar_tcf
from src.pipeline.evaluador import evaluar_mejora_campo
from src.tcf.constantes import VECTOR_PILATES


class TestEvaluadorTCF:
    def test_sin_tcf_retorna_none(self):
        assert evaluar_mejora_campo(None, {}) is None

    def test_con_tcf_retorna_metricas(self):
        vector = VectorFuncional.from_dict(VECTOR_PILATES)
        tcf = detectar_tcf("Todo depende de mí", vector)
        resultado = evaluar_mejora_campo(tcf, {})
        assert resultado is not None
        assert "eslabon_debil_pre" in resultado
        assert "toxicidad_pre" in resultado

    def test_cobertura_receta_con_ints_ejecutadas(self):
        vector = VectorFuncional.from_dict(VECTOR_PILATES)
        tcf = detectar_tcf("Todo depende de mí", vector)
        # Simular que INT-02 y INT-17 se ejecutaron
        resultados = {
            "INT-02_individual": "algo",
            "INT-17_individual": "algo",
            "INT-16_individual": "algo",
        }
        resultado = evaluar_mejora_campo(tcf, resultados)
        assert resultado is not None
        assert resultado["cobertura_receta"] > 0
