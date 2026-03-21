"""Test de integración: caso real Pilates — pipeline detect→Gestor sin LLM.

Valida que el input real de un estudio de Pilates produce:
  - Firma: maquina_sin_alma detectada
  - Vector estimado (no provisto)
  - Arquetipo primario: maquina_sin_alma
  - Receta: F5→F3→F7
  - Gestor: ProgramaCompilado con INTs correctas
  - Lente primaria: continuidad

Fuente: docs/L0/VALIDACION_TCF_CASO_PILATES.md, docs/L0/GRADIENTES_DUALES.md §8
"""
import pytest
from src.pipeline.detector_huecos import detect
from src.tcf.detector_tcf import detectar_tcf
from src.tcf.constantes import VECTOR_PILATES
from src.gestor.compilador import compilar_programa
from src.gestor.programa import ProgramaCompilado


# ---------------------------------------------------------------------------
# Input real: descripción del estudio Authentic Pilates
# ---------------------------------------------------------------------------

PILATES_INPUT_CORTO = (
    "Tengo un estudio de Pilates con método propio EEDAP. "
    "Todo depende de mí, sin mí no funciona. "
    "No puedo delegar porque nadie más puede enseñar mi método. "
    "Solo llegan clientes por boca a boca, no tengo marketing. "
    "Algunos horarios tienen 1 solo alumno pero los mantengo por compromiso. "
    "No he documentado nada del método."
)

PILATES_INPUT_LARGO = (
    "Soy Jesús, dueño de Authentic Pilates, un estudio de Pilates especializado. "
    "Tengo un método propio llamado EEDAP que es excelente, puntuación 8.5 sobre 10 en calidad. "
    "Pero todo depende de mí. Si mañana no estoy, el estudio no funciona. "
    "Solo yo sé enseñar el método, no hay manual, no hay documentación. "
    "No tengo proceso de onboarding para instructores porque no hay instructores. "
    "Los clientes llegan solo por boca a boca, el marketing es casi inexistente, 2 sobre 10. "
    "Tengo horarios de sábados con 1 solo alumno que no cubre el coste de apertura, "
    "pero lo mantengo porque siento que es un compromiso con ese alumno. "
    "No tengo señales tempranas de problemas, el tracking es manual con Excel. "
    "Trabajo 50 horas a la semana sin distribuir estratégicamente mi tiempo. "
    "El precio de grupo es igual al de individual, 105 euros entre 3 alumnos sale a 35 por persona. "
    "El método es adaptable a cada persona, personalización 8 sobre 10, "
    "pero el negocio es rígido: no adapto precios, horarios ni canales. "
    "Qué pasa si mañana no estoy?"
)


# ---------------------------------------------------------------------------
# Tests de firma lingüística
# ---------------------------------------------------------------------------

class TestFirmasPilates:
    def test_input_corto_detecta_maquina_sin_alma(self):
        """El input corto activa firma de maquina_sin_alma."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        arquetipos = [f.arquetipo for f in result.firmas]
        assert "maquina_sin_alma" in arquetipos

    def test_input_largo_detecta_maquina_sin_alma(self):
        """El input largo activa firma de maquina_sin_alma."""
        result = detectar_tcf(PILATES_INPUT_LARGO)
        arquetipos = [f.arquetipo for f in result.firmas]
        assert "maquina_sin_alma" in arquetipos

    def test_input_largo_detecta_semilla_dormida(self):
        """El input largo también activa firma de semilla_dormida (por boca a boca)."""
        result = detectar_tcf(PILATES_INPUT_LARGO)
        arquetipos = [f.arquetipo for f in result.firmas]
        assert "semilla_dormida" in arquetipos


# ---------------------------------------------------------------------------
# Tests de estimación de vector
# ---------------------------------------------------------------------------

class TestEstimacionPilates:
    def test_vector_estimado_sin_vector_previo(self):
        """Sin vector previo, estima vector desde firmas."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.vector_estimado is True
        assert result.estado_campo is not None

    def test_scoring_primario_maquina_sin_alma(self):
        """Scoring primario del vector estimado es maquina_sin_alma."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.scoring is not None
        assert result.scoring.primario.arquetipo == "maquina_sin_alma"

    def test_scoring_primario_score_alto(self):
        """Score del primario es significativo (> 0.50)."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.scoring.primario.score > 0.50

    def test_receta_secuencia_empieza_f5_termina_f7(self):
        """Receta de maquina_sin_alma: secuencia empieza F5, termina F7."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.receta is not None
        assert result.receta.secuencia[0] == "F5"
        assert result.receta.secuencia[-1] == "F7"

    def test_receta_lente_continuidad(self):
        """Lente primaria de maquina_sin_alma: continuidad."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.receta.lente == "continuidad"

    def test_receta_incluye_int16(self):
        """Receta incluye INT-16 (constructiva, siempre presente)."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert "INT-16" in result.receta.ints

    def test_eslabon_debil_f7(self):
        """Eslabón débil del vector estimado: F7 (replicar)."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.estado_campo.eslabon_debil == "F7"


# ---------------------------------------------------------------------------
# Tests de Gestor (compilar programa)
# ---------------------------------------------------------------------------

class TestGestorPilates:
    def test_gestor_compila_desde_estimacion(self):
        """El Gestor compila programa válido desde scoring estimado."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
            modo="analisis",
        )
        assert isinstance(programa, ProgramaCompilado)
        assert len(programa.pasos) > 0

    def test_programa_arquetipo_maquina_sin_alma(self):
        """Programa compilado tiene base maquina_sin_alma."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        assert programa.arquetipo_base == "maquina_sin_alma"

    def test_programa_tier3_para_analisis(self):
        """Modo análisis = tier 3."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
            modo="analisis",
        )
        assert programa.tier == 3

    def test_programa_incluye_int17(self):
        """Programa incluye INT-17 (existencial) — clave para Máquina sin Alma."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        assert "INT-17" in programa.inteligencias()

    def test_programa_incluye_int16(self):
        """Programa incluye INT-16 (constructiva) — siempre presente."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        assert "INT-16" in programa.inteligencias()

    def test_programa_lente_continuidad(self):
        """Lente primaria del programa: continuidad."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        assert programa.lente_primaria == "continuidad"

    def test_programa_sin_frenar(self):
        """Maquina sin Alma no tiene funciones a frenar."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        assert programa.frenar == []

    def test_programa_modelos_asignados(self):
        """Cada paso tiene modelo OpenRouter asignado."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        programa = compilar_programa(
            scoring=result.scoring,
            vector=result.estado_campo.vector,
        )
        for paso in programa.pasos:
            assert "/" in paso.modelo  # formato openrouter


# ---------------------------------------------------------------------------
# Test de integración: detect() en pipeline
# ---------------------------------------------------------------------------

class TestDetectPipelinePilates:
    @pytest.mark.asyncio
    async def test_detect_pilates_pipeline_completo(self):
        """Pipeline completo detect→Gestor para input Pilates sin vector."""
        huecos = await detect(PILATES_INPUT_LARGO)

        # 1. TCF activa
        assert huecos.tcf is not None
        assert huecos.tcf.vector_estimado is True

        # 2. Firmas
        arquetipos = [f.arquetipo for f in huecos.tcf.firmas]
        assert "maquina_sin_alma" in arquetipos

        # 3. Campo estimado
        assert huecos.tcf.estado_campo is not None
        assert huecos.tcf.estado_campo.eslabon_debil == "F7"

        # 4. Scoring
        assert huecos.tcf.scoring is not None
        assert huecos.tcf.scoring.primario.arquetipo == "maquina_sin_alma"

        # 5. Receta
        assert huecos.tcf.receta is not None
        assert huecos.tcf.receta.secuencia[0] == "F5"
        assert huecos.tcf.receta.secuencia[-1] == "F7"

        # 6. Gestor compila
        programa = compilar_programa(
            scoring=huecos.tcf.scoring,
            vector=huecos.tcf.estado_campo.vector,
        )
        assert programa.arquetipo_base == "maquina_sin_alma"
        assert "INT-17" in programa.inteligencias()
        assert programa.lente_primaria == "continuidad"

        # 7. INTs enriquecidas en detector
        assert "INT-16" in huecos.inteligencias_sugeridas
