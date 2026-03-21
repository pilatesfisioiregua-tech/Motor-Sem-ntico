"""Tests para src/tcf/recetas.py — recetas + mezcla + Regla 14."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import scoring_multi_arquetipo
from src.tcf.recetas import (
    generar_receta_mixta,
    aplicar_regla_14,
    secuencia_universal,
)
from src.tcf.constantes import VECTOR_PILATES


@pytest.fixture
def vector_pilates():
    return VectorFuncional.from_dict(VECTOR_PILATES)


@pytest.fixture
def scoring_pilates(vector_pilates):
    return scoring_multi_arquetipo(vector_pilates)


# ---------------------------------------------------------------------------
# Regla 14 — FRENAR
# ---------------------------------------------------------------------------

class TestRegla14:
    def test_pilates_nada_que_frenar(self, vector_pilates):
        # Pilates no tiene función alta con dep insatisfecha
        a_frenar = aplicar_regla_14(vector_pilates)
        assert len(a_frenar) == 0

    def test_expansion_sin_cimientos_frenar_f7(self):
        v = VectorFuncional(f1=0.30, f2=0.65, f3=0.30, f4=0.45, f5=0.25, f6=0.45, f7=0.75)
        a_frenar = aplicar_regla_14(v)
        assert "F7" in a_frenar

    def test_intoxicado_frenar_f2(self):
        v = VectorFuncional(f1=0.45, f2=0.70, f3=0.15, f4=0.50, f5=0.40, f6=0.40, f7=0.30)
        a_frenar = aplicar_regla_14(v)
        assert "F2" in a_frenar


# ---------------------------------------------------------------------------
# Receta mixta
# ---------------------------------------------------------------------------

class TestRecetaMixta:
    def test_pilates_receta_base_maquina_sin_alma(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert receta.arquetipo_base == "maquina_sin_alma"

    def test_pilates_secuencia_empieza_f5(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert receta.secuencia[0] == "F5"

    def test_pilates_f7_en_secuencia(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert "F7" in receta.secuencia

    def test_pilates_int16_en_ints(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert "INT-16" in receta.ints

    def test_pilates_sin_frenar(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert len(receta.frenar) == 0

    def test_pilates_lente_continuidad(self, scoring_pilates, vector_pilates):
        receta = generar_receta_mixta(scoring_pilates, vector_pilates)
        assert receta.lente == "continuidad"


# ---------------------------------------------------------------------------
# Secuencia universal (Teorema 2)
# ---------------------------------------------------------------------------

class TestSecuenciaUniversal:
    def test_pilates_secuencia(self, vector_pilates):
        pasos = secuencia_universal(vector_pilates)
        assert len(pasos) > 0
        # F7 es eslabón débil → SUBIR_F7 debe estar
        assert "SUBIR_F7" in pasos

    def test_expansion_frenar_primero(self):
        v = VectorFuncional(f1=0.30, f2=0.65, f3=0.30, f4=0.45, f5=0.25, f6=0.45, f7=0.75)
        pasos = secuencia_universal(v)
        # FRENAR debe ser primer paso
        assert pasos[0].startswith("FRENAR")

    def test_equilibrado_poco_que_hacer(self):
        v = VectorFuncional(f1=0.75, f2=0.70, f3=0.70, f4=0.70, f5=0.80, f6=0.70, f7=0.65)
        pasos = secuencia_universal(v)
        # Pocas funciones < 0.40
        assert all("FRENAR" not in p for p in pasos)
