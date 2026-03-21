"""Test de integración: Gestor conectado al pipeline."""
from __future__ import annotations

import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import scoring_multi_arquetipo
from src.gestor.compilador import compilar_programa
from src.gestor.programa import ProgramaCompilado
from src.tcf.constantes import VECTOR_PILATES
from src.pipeline.detector_huecos import detect


class TestGestorEnPipeline:
    """Verifica que el Gestor se integra correctamente con el flujo."""

    def test_programa_pilates_tiene_ints_de_receta(self):
        """El programa compilado contiene las INTs de la receta del arquetipo."""
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v)
        # Maquina sin alma: INT-02, INT-17, INT-15, INT-12, INT-16
        assert "INT-16" in programa.inteligencias()
        assert "INT-17" in programa.inteligencias()

    def test_programa_tiene_modelos_asignados(self):
        """Cada paso del programa tiene un modelo de OpenRouter asignado."""
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v)
        for paso in programa.pasos:
            assert paso.modelo != ""
            assert "/" in paso.modelo  # formato openrouter: provider/model

    def test_programa_tier3_para_analisis(self):
        """Modo análisis con presupuesto normal = tier 3."""
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v, modo="analisis")
        assert programa.tier == 3

    def test_programa_tier2_para_conversacion(self):
        """Modo conversación = tier 2."""
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v, modo="conversacion")
        assert programa.tier == 2

    def test_programa_serializable(self):
        """El programa se puede serializar a JSON para telemetría."""
        import json
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v)
        # No debe fallar
        data = {
            "tier": programa.tier,
            "arquetipo": programa.arquetipo_base,
            "ints": programa.inteligencias(),
            "modelos": programa.modelos(),
            "frenar": programa.frenar,
            "n_pasos": len(programa.pasos),
        }
        serialized = json.dumps(data)
        assert len(serialized) > 0

    @pytest.mark.asyncio
    async def test_detect_con_vector_produce_scoring_para_gestor(self):
        """El detector con vector previo produce scoring que el Gestor consume."""
        result = await detect("Todo depende de mí", vector_previo=VECTOR_PILATES)
        assert result.tcf is not None
        assert result.tcf.scoring is not None
        # El scoring se puede pasar al compilador
        programa = compilar_programa(result.tcf.scoring,
                                     result.tcf.estado_campo.vector if result.tcf.estado_campo else None)
        assert isinstance(programa, ProgramaCompilado)
        assert len(programa.pasos) > 0

    def test_expansion_sin_cimientos_programa_con_frenar(self):
        """Arquetipo con función a FRENAR genera programa con frenar."""
        v = VectorFuncional(f1=0.30, f2=0.65, f3=0.30, f4=0.45, f5=0.25, f6=0.45, f7=0.75)
        scoring = scoring_multi_arquetipo(v)
        programa = compilar_programa(scoring, v)
        assert len(programa.frenar) > 0
