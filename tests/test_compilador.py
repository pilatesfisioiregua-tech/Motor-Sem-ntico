"""Tests para src/gestor/compilador.py — Compilar programa por arquetipo."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import scoring_multi_arquetipo
from src.gestor.compilador import compilar_programa
from src.gestor.programa import ProgramaCompilado
from src.tcf.constantes import VECTOR_PILATES


@pytest.fixture
def vector_pilates():
    return VectorFuncional.from_dict(VECTOR_PILATES)


@pytest.fixture
def scoring_pilates(vector_pilates):
    return scoring_multi_arquetipo(vector_pilates)


class TestCompilarPrograma:
    def test_pilates_compila(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert isinstance(prog, ProgramaCompilado)
        assert prog.arquetipo_base == "maquina_sin_alma"
        assert prog.tier == 3  # modo analisis por defecto
        assert len(prog.pasos) > 0

    def test_pilates_lente_continuidad(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert prog.lente_primaria == "continuidad"

    def test_pilates_sin_frenar(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert len(prog.frenar) == 0

    def test_pilates_tiene_int16(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        assert "INT-16" in prog.inteligencias()

    def test_pilates_modelos_asignados(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates)
        for paso in prog.pasos:
            assert paso.modelo != ""
            assert "/" in paso.modelo  # formato openrouter

    def test_conversacion_tier_2(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, modo="conversacion")
        assert prog.tier == 2

    def test_forzar_tier(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, forzar_tier=4)
        assert prog.tier == 4

    def test_presupuesto_bajo_baja_tier(self, scoring_pilates, vector_pilates):
        prog = compilar_programa(scoring_pilates, vector_pilates, presupuesto_max=0.10)
        assert prog.tier <= 2

    def test_expansion_sin_cimientos_frenar(self):
        v = VectorFuncional(f1=0.30, f2=0.65, f3=0.30, f4=0.45, f5=0.25, f6=0.45, f7=0.75)
        scoring = scoring_multi_arquetipo(v)
        prog = compilar_programa(scoring, v)
        assert "F7" in prog.frenar

    def test_quemado_parar_primero(self):
        v = VectorFuncional(f1=0.25, f2=0.20, f3=0.20, f4=0.25, f5=0.35, f6=0.20, f7=0.15)
        scoring = scoring_multi_arquetipo(v)
        prog = compilar_programa(scoring, v)
        assert prog.parar_primero
