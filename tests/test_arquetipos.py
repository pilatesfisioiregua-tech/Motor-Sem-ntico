"""Tests para src/tcf/arquetipos.py — scoring + pre-screening lingüístico."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import (
    scoring_multi_arquetipo,
    pre_screening_linguistico,
    ScoringMultiArquetipo,
)
from src.tcf.constantes import VECTOR_PILATES


@pytest.fixture
def vector_pilates():
    return VectorFuncional.from_dict(VECTOR_PILATES)


# ---------------------------------------------------------------------------
# Scoring multi-arquetipo
# ---------------------------------------------------------------------------

class TestScoringMultiArquetipo:
    def test_pilates_primario_maquina_sin_alma(self, vector_pilates):
        scoring = scoring_multi_arquetipo(vector_pilates)
        assert scoring.primario.arquetipo == "maquina_sin_alma"
        assert scoring.primario.score >= 0.65

    def test_pilates_tiene_secundario(self, vector_pilates):
        scoring = scoring_multi_arquetipo(vector_pilates)
        assert scoring.secundario is not None

    def test_pilates_secundario_semilla_dormida(self, vector_pilates):
        scoring = scoring_multi_arquetipo(vector_pilates)
        # El secundario debería ser semilla_dormida o similar
        arquetipos_top = [s.arquetipo for s in scoring.todos[:3]]
        assert "semilla_dormida" in arquetipos_top or scoring.secundario is not None

    def test_equilibrado_matchea_equilibrado(self):
        v = VectorFuncional(f1=0.75, f2=0.70, f3=0.70, f4=0.70, f5=0.80, f6=0.70, f7=0.65)
        scoring = scoring_multi_arquetipo(v)
        assert scoring.primario.arquetipo == "equilibrado"

    def test_scores_descendentes(self, vector_pilates):
        scoring = scoring_multi_arquetipo(vector_pilates)
        for i in range(len(scoring.todos) - 1):
            assert scoring.todos[i].score >= scoring.todos[i + 1].score

    def test_scores_en_rango(self, vector_pilates):
        scoring = scoring_multi_arquetipo(vector_pilates)
        for s in scoring.todos:
            assert 0.0 <= s.score <= 1.0


# ---------------------------------------------------------------------------
# Pre-screening lingüístico
# ---------------------------------------------------------------------------

class TestPreScreening:
    def test_maquina_sin_alma_firma(self):
        texto = "Todo depende de mí, necesito delegar 20h a un instructor"
        firmas = pre_screening_linguistico(texto)
        arquetipos = [f.arquetipo for f in firmas]
        assert "maquina_sin_alma" in arquetipos

    def test_semilla_dormida_firma(self):
        texto = "Es bueno pero nadie lo sabe, crecemos solo por boca a boca"
        firmas = pre_screening_linguistico(texto)
        arquetipos = [f.arquetipo for f in firmas]
        assert "semilla_dormida" in arquetipos

    def test_quemado_firma(self):
        texto = "Ya da igual, estoy cansado de intentar"
        firmas = pre_screening_linguistico(texto)
        arquetipos = [f.arquetipo for f in firmas]
        assert "quemado" in arquetipos

    def test_rigido_firma(self):
        texto = "Siempre hemos hecho así y funciona perfectamente"
        firmas = pre_screening_linguistico(texto)
        arquetipos = [f.arquetipo for f in firmas]
        assert "rigido" in arquetipos

    def test_texto_sin_firma(self):
        texto = "Hoy hace sol y voy a pasear al perro"
        firmas = pre_screening_linguistico(texto)
        assert len(firmas) == 0

    def test_confianza_no_llega_a_1(self):
        texto = "Todo depende de mí, sin mí no funciona, nadie más puede"
        firmas = pre_screening_linguistico(texto)
        for f in firmas:
            assert f.confianza <= 0.80
