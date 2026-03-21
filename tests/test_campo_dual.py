"""Tests para src/tcf/campo_dual.py — CeldaCampo + VectorFuncionalDual + EstadoCampoDual.

Verifica:
  1. CeldaCampo: creación, validación, serialización
  2. VectorFuncionalDual: .numerico() compatibilidad con VectorFuncional
  3. EstadoCampoDual: evaluar_campo sobre .numerico() produce mismo resultado
  4. Caso Pilates dual: semántica + números coexisten
  5. Upgrade path: VectorFuncional existente → VectorFuncionalDual
"""
import pytest
from src.tcf.campo import VectorFuncional, evaluar_campo
from src.tcf.campo_dual import CeldaCampo, VectorFuncionalDual, EstadoCampoDual
from src.tcf.constantes import VECTOR_PILATES, FUNCIONES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def celda_f3_pilates():
    return CeldaCampo(
        funcion="F3",
        lente="salud",
        grado=0.25,
        estado="No elimina horario sábados con 1 alumno. Tracking manual impide detectar desperdicio.",
        objetivo="Dashboard con señales tempranas. Proceso de evaluación trimestral.",
        gap_semantico="De no tener feedback a tener dashboard con señales",
        evidencias=["retroalimentación 3/10", "40% sillón 3 vacío", "horario sábados: 1 alumno"],
        fuente="motor_vn",
        confianza=0.8,
    )


@pytest.fixture
def vector_pilates_numerico():
    return VectorFuncional.from_dict(VECTOR_PILATES)


@pytest.fixture
def vector_pilates_dual():
    """Vector Pilates con semántica completa."""
    celdas = {
        "F1": CeldaCampo(funcion="F1", lente="salud", grado=0.50,
                         estado="EEDAP excelente pero sostenido por 1 persona.",
                         fuente="motor_vn", confianza=0.8),
        "F2": CeldaCampo(funcion="F2", lente="salud", grado=0.30,
                         estado="Marketing casi ausente. Solo boca a boca.",
                         fuente="motor_vn", confianza=0.8),
        "F3": CeldaCampo(funcion="F3", lente="salud", grado=0.25,
                         estado="No elimina horario sábados con 1 alumno.",
                         gap_semantico="De no tener feedback a tener dashboard con señales",
                         evidencias=["retroalimentación 3/10", "40% sillón 3 vacío"],
                         fuente="motor_vn", confianza=0.8),
        "F4": CeldaCampo(funcion="F4", lente="salud", grado=0.35,
                         estado="Jesús 50h/semana sin distribución estratégica.",
                         fuente="motor_vn", confianza=0.7),
        "F5": CeldaCampo(funcion="F5", lente="sentido", grado=0.65,
                         estado="EEDAP como identidad: claro, definido, diferenciador.",
                         fuente="motor_vn", confianza=0.9),
        "F6": CeldaCampo(funcion="F6", lente="salud", grado=0.35,
                         estado="Método adaptable. Negocio rígido.",
                         fuente="motor_vn", confianza=0.7),
        "F7": CeldaCampo(funcion="F7", lente="continuidad", grado=0.20,
                         estado="EEDAP no documentado. 0 manual de instructor.",
                         gap_semantico="De 0 documentación a manual operativo",
                         evidencias=["0 documentos", "87% dependencia en 1 persona"],
                         fuente="motor_vn", confianza=0.9),
    }
    return VectorFuncionalDual(celdas=celdas)


@pytest.fixture
def vector_solo_numerico_dual():
    """Vector dual creado desde VectorFuncional (sin semántica)."""
    v = VectorFuncional.from_dict(VECTOR_PILATES)
    return VectorFuncionalDual.desde_vector_numerico(v)


# ---------------------------------------------------------------------------
# CeldaCampo
# ---------------------------------------------------------------------------

class TestCeldaCampo:
    def test_creacion_basica(self, celda_f3_pilates):
        assert celda_f3_pilates.funcion == "F3"
        assert celda_f3_pilates.grado == 0.25
        assert celda_f3_pilates.tiene_semantica() is True

    def test_solo_numerico(self):
        c = CeldaCampo.solo_numerico("F1", 0.50)
        assert c.grado == 0.50
        assert c.estado is None
        assert c.tiene_semantica() is False

    def test_validacion_grado_fuera_rango(self):
        with pytest.raises(ValueError, match="grado"):
            CeldaCampo(funcion="F1", lente="salud", grado=1.5)

    def test_validacion_confianza_fuera_rango(self):
        with pytest.raises(ValueError, match="confianza"):
            CeldaCampo(funcion="F1", lente="salud", grado=0.5, confianza=-0.1)

    def test_serialization_roundtrip(self, celda_f3_pilates):
        d = celda_f3_pilates.to_dict()
        c2 = CeldaCampo.from_dict(d)
        assert c2.funcion == celda_f3_pilates.funcion
        assert c2.grado == celda_f3_pilates.grado
        assert c2.estado == celda_f3_pilates.estado
        assert c2.evidencias == celda_f3_pilates.evidencias

    def test_serialization_solo_numerico_omite_nulos(self):
        c = CeldaCampo.solo_numerico("F1", 0.50)
        d = c.to_dict()
        assert "estado" not in d
        assert "objetivo" not in d
        assert "gap_semantico" not in d
        assert "evidencias" not in d

    def test_tiene_semantica_con_solo_evidencias(self):
        c = CeldaCampo(funcion="F1", lente="salud", grado=0.5,
                       evidencias=["dato 1"])
        assert c.tiene_semantica() is True

    def test_tiene_semantica_sin_nada(self):
        c = CeldaCampo.solo_numerico("F1", 0.5)
        assert c.tiene_semantica() is False


# ---------------------------------------------------------------------------
# VectorFuncionalDual
# ---------------------------------------------------------------------------

class TestVectorFuncionalDual:
    def test_numerico_devuelve_vector_funcional(self, vector_pilates_dual, vector_pilates_numerico):
        """CRÍTICO: .numerico() debe producir el mismo VectorFuncional."""
        v = vector_pilates_dual.numerico()
        assert isinstance(v, VectorFuncional)
        assert v.to_dict() == vector_pilates_numerico.to_dict()

    def test_grado_acceso(self, vector_pilates_dual):
        assert vector_pilates_dual.grado("F3") == 0.25
        assert vector_pilates_dual.grado("F5") == 0.65
        assert vector_pilates_dual.grado("F7") == 0.20

    def test_estado_acceso(self, vector_pilates_dual):
        assert "sábados" in vector_pilates_dual.estado("F3")
        assert vector_pilates_dual.estado("F5") is not None

    def test_gap_semantico(self, vector_pilates_dual):
        assert vector_pilates_dual.gap_semantico("F3") is not None
        assert vector_pilates_dual.gap_semantico("F7") is not None
        assert vector_pilates_dual.gap_semantico("F1") is None  # no definido en fixture

    def test_evidencias(self, vector_pilates_dual):
        ev = vector_pilates_dual.evidencias("F3")
        assert len(ev) >= 2

    def test_tiene_semantica_true(self, vector_pilates_dual):
        assert vector_pilates_dual.tiene_semantica() is True

    def test_tiene_semantica_false(self, vector_solo_numerico_dual):
        assert vector_solo_numerico_dual.tiene_semantica() is False

    def test_cobertura_semantica(self, vector_pilates_dual):
        cob = vector_pilates_dual.cobertura_semantica()
        assert cob == 1.0  # todas las celdas de la fixture tienen estado

    def test_cobertura_semantica_solo_numerico(self, vector_solo_numerico_dual):
        assert vector_solo_numerico_dual.cobertura_semantica() == 0.0

    def test_desde_vector_numerico(self, vector_pilates_numerico):
        dual = VectorFuncionalDual.desde_vector_numerico(vector_pilates_numerico)
        assert dual.numerico() == vector_pilates_numerico
        assert dual.tiene_semantica() is False

    def test_falta_funcion_raises(self):
        celdas = {f"F{i}": CeldaCampo.solo_numerico(f"F{i}", 0.5) for i in range(1, 7)}
        # Falta F7
        with pytest.raises(ValueError, match="F7"):
            VectorFuncionalDual(celdas=celdas)

    def test_serialization_roundtrip(self, vector_pilates_dual):
        d = vector_pilates_dual.to_dict()
        v2 = VectorFuncionalDual.from_dict(d)
        assert v2.numerico().to_dict() == vector_pilates_dual.numerico().to_dict()
        assert v2.estado("F3") == vector_pilates_dual.estado("F3")


# ---------------------------------------------------------------------------
# EstadoCampoDual
# ---------------------------------------------------------------------------

class TestEstadoCampoDual:
    def test_desde_vector_dual(self, vector_pilates_dual, vector_pilates_numerico):
        """TCF numérica produce mismo resultado que evaluar_campo directo."""
        estado_dual = EstadoCampoDual.desde_vector_dual(vector_pilates_dual)
        estado_directo = evaluar_campo(vector_pilates_numerico)

        assert estado_dual.estado_numerico.lentes == estado_directo.lentes
        assert estado_dual.estado_numerico.coalicion == estado_directo.coalicion
        assert estado_dual.estado_numerico.eslabon_debil == estado_directo.eslabon_debil
        assert estado_dual.estado_numerico.atractor_mas_cercano == estado_directo.atractor_mas_cercano

    def test_desde_vector_numerico(self, vector_pilates_numerico):
        """Upgrade path: VectorFuncional → EstadoCampoDual."""
        estado_dual = EstadoCampoDual.desde_vector_numerico(vector_pilates_numerico)
        assert estado_dual.vector_dual.tiene_semantica() is False
        assert estado_dual.estado_numerico.eslabon_debil == "F7"

    def test_semantica_coexiste_con_numerico(self, vector_pilates_dual):
        estado = EstadoCampoDual.desde_vector_dual(vector_pilates_dual)
        # Numérico funciona
        assert estado.estado_numerico.eslabon_debil == "F7"
        assert estado.estado_numerico.coalicion is not None
        # Semántico también
        assert estado.vector_dual.estado("F7") is not None
        assert "documentado" in estado.vector_dual.estado("F7").lower()

    def test_diagnostico_natural_inicialmente_none(self, vector_pilates_dual):
        estado = EstadoCampoDual.desde_vector_dual(vector_pilates_dual)
        assert estado.diagnostico_natural is None
        assert estado.intervenciones_concretas == []
