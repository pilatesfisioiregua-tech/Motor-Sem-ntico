"""Test de integración: pipeline con TCF."""
import pytest
from src.pipeline.detector_huecos import detect
from src.tcf.constantes import VECTOR_PILATES
from src.tcf.detector_tcf import (
    detectar_tcf, estimar_vector_desde_firmas, DetectorTCFResult,
)
from src.tcf.arquetipos import FirmaDetectada, pre_screening_linguistico
from src.tcf.campo import VectorFuncional


# ---------------------------------------------------------------------------
# estimar_vector_desde_firmas
# ---------------------------------------------------------------------------

class TestEstimarVector:
    def test_sin_firmas_retorna_none(self):
        assert estimar_vector_desde_firmas([]) is None

    def test_una_firma_usa_canonico_directo(self):
        """Con 1 firma, el vector estimado ES el canónico del arquetipo."""
        from src.tcf.constantes import ARQUETIPOS_CANONICOS
        firma = FirmaDetectada(
            arquetipo="maquina_sin_alma",
            patron_matched="todo depende de mí",
            fragmento="todo depende de mí",
            confianza=0.60,
        )
        v = estimar_vector_desde_firmas([firma])
        assert v is not None
        canon = ARQUETIPOS_CANONICOS["maquina_sin_alma"]
        assert v.to_dict() == VectorFuncional.from_dict(canon).to_dict()

    def test_dos_firmas_blend_ponderado(self):
        """Con 2 firmas, el vector es blend ponderado."""
        from src.tcf.constantes import ARQUETIPOS_CANONICOS
        f1 = FirmaDetectada(
            arquetipo="maquina_sin_alma", patron_matched="p1",
            fragmento="f1", confianza=0.60,
        )
        f2 = FirmaDetectada(
            arquetipo="semilla_dormida", patron_matched="p2",
            fragmento="f2", confianza=0.40,
        )
        v = estimar_vector_desde_firmas([f1, f2])
        assert v is not None
        # F7 de maquina=0.20, F7 de semilla=0.30
        # blend: (0.20*0.60 + 0.30*0.40) / (0.60+0.40) = 0.24
        assert abs(v.grado("F7") - 0.24) < 0.01

    def test_firma_arquetipo_desconocido_ignorada(self):
        """Firma con arquetipo no canónico se ignora."""
        firma = FirmaDetectada(
            arquetipo="inventado", patron_matched="p",
            fragmento="f", confianza=0.50,
        )
        assert estimar_vector_desde_firmas([firma]) is None

    def test_vector_en_rango(self):
        """Todas las funciones del vector estimado están en [0, 1]."""
        f1 = FirmaDetectada(
            arquetipo="maquina_sin_alma", patron_matched="p1",
            fragmento="f1", confianza=0.80,
        )
        f2 = FirmaDetectada(
            arquetipo="quemado", patron_matched="p2",
            fragmento="f2", confianza=0.30,
        )
        v = estimar_vector_desde_firmas([f1, f2])
        assert v is not None
        for fi in ("F1", "F2", "F3", "F4", "F5", "F6", "F7"):
            assert 0.0 <= v.grado(fi) <= 1.0


# ---------------------------------------------------------------------------
# detectar_tcf con estimación
# ---------------------------------------------------------------------------

class TestDetectarTCFConEstimacion:
    def test_texto_con_firma_produce_campo(self):
        """Texto con firma lingüística → campo estimado, no None."""
        result = detectar_tcf("Todo depende de mí, sin mí no funciona")
        assert result.firmas  # al menos una firma
        assert result.estado_campo is not None
        assert result.scoring is not None
        assert result.receta is not None
        assert result.vector_estimado is True

    def test_texto_sin_firma_no_produce_campo(self):
        """Texto sin firma lingüística → campo sigue None."""
        result = detectar_tcf("Hola, buenos días")
        assert result.estado_campo is None
        assert result.scoring is None
        assert result.vector_estimado is False

    def test_vector_explicito_prevalece(self):
        """Si se pasa vector, se usa ese y no se estima."""
        v = VectorFuncional.from_dict(VECTOR_PILATES)
        result = detectar_tcf("Todo depende de mí", vector=v)
        assert result.estado_campo is not None
        assert result.vector_estimado is False

    def test_estimado_detecta_maquina_sin_alma(self):
        """Firma 'maquina_sin_alma' → scoring primario maquina_sin_alma."""
        result = detectar_tcf("Todo depende de mí, solo yo puedo, nadie más puede")
        assert result.scoring is not None
        assert result.scoring.primario.arquetipo == "maquina_sin_alma"

    def test_estimado_produce_receta_con_ints(self):
        """Vector estimado → receta con INTs ejecutables."""
        result = detectar_tcf("Todo depende de mí, qué pasa si no estoy")
        assert result.receta is not None
        assert len(result.receta.ints) > 0


# ---------------------------------------------------------------------------
# Pipeline integration: detect() usa estimación
# ---------------------------------------------------------------------------

class TestDetectPipelineConEstimacion:
    @pytest.mark.asyncio
    async def test_detect_sin_vector_con_firma_produce_scoring(self):
        """detect() sin vector_previo pero con firma → scoring para Gestor."""
        result = await detect("Todo depende de mí, necesito delegar")
        assert result.tcf is not None
        assert result.tcf.firmas
        assert result.tcf.estado_campo is not None  # AHORA no es None
        assert result.tcf.scoring is not None
        assert result.tcf.vector_estimado is True

    @pytest.mark.asyncio
    async def test_detect_con_vector_explicito(self):
        """detect() con vector previo funciona como antes."""
        result = await detect("Todo depende de mí", vector_previo=VECTOR_PILATES)
        assert result.tcf is not None
        assert result.tcf.estado_campo is not None
        assert result.tcf.scoring is not None
        assert result.tcf.scoring.primario.arquetipo == "maquina_sin_alma"
        assert result.tcf.vector_estimado is False

    @pytest.mark.asyncio
    async def test_detect_sin_firma_sigue_sin_campo(self):
        """detect() con texto genérico → sin campo (como antes)."""
        result = await detect("Buenos días, quiero hablar sobre mi negocio")
        assert result.tcf is not None
        assert result.tcf.estado_campo is None

    @pytest.mark.asyncio
    async def test_detect_ints_enriquecidas_desde_estimacion(self):
        """Las INTs sugeridas incluyen las de la receta estimada."""
        result = await detect("Todo depende de mí, necesito delegar")
        # maquina_sin_alma receta: INT-02, INT-17, INT-15, INT-12, INT-16
        assert "INT-16" in result.inteligencias_sugeridas

    @pytest.mark.asyncio
    async def test_detect_estimado_gestor_puede_compilar(self):
        """El scoring estimado permite compilar programa en el Gestor."""
        from src.gestor.compilador import compilar_programa
        from src.gestor.programa import ProgramaCompilado

        result = await detect("Todo depende de mí, solo yo sé cómo funciona")
        assert result.tcf.scoring is not None
        programa = compilar_programa(
            result.tcf.scoring,
            result.tcf.estado_campo.vector if result.tcf.estado_campo else None,
        )
        assert isinstance(programa, ProgramaCompilado)
        assert len(programa.pasos) > 0
