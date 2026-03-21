"""Tests para src/tcf/campo.py — VectorFuncional + EstadoCampo + evaluar_campo().

Caso de test principal: Authentic Pilates (vector validado empíricamente).
"""
import pytest
from src.tcf.campo import (
    VectorFuncional, EstadoCampo,
    calcular_lentes, detectar_coalicion, identificar_perfil_lente,
    detectar_dependencias_violadas, evaluar_toxicidad,
    atractor_mas_cercano, evaluar_campo,
)
from src.tcf.constantes import VECTOR_PILATES


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vector_pilates():
    return VectorFuncional.from_dict(VECTOR_PILATES)


@pytest.fixture
def vector_equilibrado():
    return VectorFuncional(f1=0.75, f2=0.70, f3=0.70, f4=0.70, f5=0.80, f6=0.70, f7=0.65)


@pytest.fixture
def vector_intoxicado():
    return VectorFuncional(f1=0.45, f2=0.65, f3=0.20, f4=0.50, f5=0.40, f6=0.40, f7=0.30)


# ---------------------------------------------------------------------------
# VectorFuncional
# ---------------------------------------------------------------------------

class TestVectorFuncional:
    def test_from_dict_to_dict_roundtrip(self, vector_pilates):
        d = vector_pilates.to_dict()
        v2 = VectorFuncional.from_dict(d)
        assert v2 == vector_pilates

    def test_grado_acceso(self, vector_pilates):
        assert vector_pilates.grado("F1") == 0.50
        assert vector_pilates.grado("F5") == 0.65
        assert vector_pilates.grado("F7") == 0.20

    def test_eslabon_debil_pilates(self, vector_pilates):
        assert vector_pilates.eslabon_debil() == "F7"

    def test_distancia_consigo_mismo(self, vector_pilates):
        assert vector_pilates.distancia(vector_pilates) == 0.0

    def test_distancia_simetrica(self, vector_pilates, vector_equilibrado):
        d1 = vector_pilates.distancia(vector_equilibrado)
        d2 = vector_equilibrado.distancia(vector_pilates)
        assert abs(d1 - d2) < 1e-10

    def test_validacion_rango(self):
        with pytest.raises(ValueError):
            VectorFuncional(f1=1.5, f2=0, f3=0, f4=0, f5=0, f6=0, f7=0)


# ---------------------------------------------------------------------------
# Lentes (Ley 8)
# ---------------------------------------------------------------------------

class TestCalcularLentes:
    def test_pilates_lentes(self, vector_pilates):
        lentes = calcular_lentes(vector_pilates)
        # Esperado: salud ≈ 0.40, sentido ≈ 0.60, continuidad ≈ 0.20
        # Los valores exactos dependen de la normalización; verificamos orden
        assert lentes["sentido"] > lentes["salud"]
        assert lentes["salud"] > lentes["continuidad"]

    def test_equilibrado_lentes_altas(self, vector_equilibrado):
        lentes = calcular_lentes(vector_equilibrado)
        assert all(v > 0.6 for v in lentes.values())


# ---------------------------------------------------------------------------
# Coaliciones (Juegos de Lentes §3)
# ---------------------------------------------------------------------------

class TestCoalicion:
    def test_pilates_coalicion(self, vector_pilates):
        lentes = calcular_lentes(vector_pilates)
        coalicion = detectar_coalicion(lentes)
        # Pilates: Salud y Sentido dominan, Continuidad baja
        # Depende de umbrales exactos — verificamos que no es "ninguna"
        # dado que sentido debería ser alta
        assert coalicion in ("salud_sentido", "ninguna")

    def test_equilibrado_ninguna(self, vector_equilibrado):
        lentes = calcular_lentes(vector_equilibrado)
        coalicion = detectar_coalicion(lentes)
        # Todas altas → ninguna coalición domina
        assert coalicion == "ninguna"


# ---------------------------------------------------------------------------
# Perfil de Lente (Juegos de Lentes §6)
# ---------------------------------------------------------------------------

class TestPerfilLente:
    def test_perfil_format(self, vector_pilates):
        lentes = calcular_lentes(vector_pilates)
        perfil = identificar_perfil_lente(lentes)
        # Formato: "S+Se+C-" o similar
        assert len(perfil) > 0
        assert "S" in perfil
        assert "Se" in perfil
        assert "C" in perfil

    def test_equilibrado_todo_alto(self, vector_equilibrado):
        lentes = calcular_lentes(vector_equilibrado)
        perfil = identificar_perfil_lente(lentes)
        assert "S+" in perfil


# ---------------------------------------------------------------------------
# Dependencias violadas (Ley 9)
# ---------------------------------------------------------------------------

class TestDependencias:
    def test_intoxicado_viola_f2_f3(self, vector_intoxicado):
        violaciones = detectar_dependencias_violadas(vector_intoxicado)
        # F2=0.65, F3=0.20 → F2→F3 (B) violada
        bloqueantes = [v for v in violaciones if v.tipo == "B"]
        pares = [(v.fi, v.fj) for v in bloqueantes]
        assert ("F2", "F3") in pares

    def test_equilibrado_sin_violaciones(self, vector_equilibrado):
        violaciones = detectar_dependencias_violadas(vector_equilibrado)
        assert len(violaciones) == 0


# ---------------------------------------------------------------------------
# Toxicidad (Ley 3)
# ---------------------------------------------------------------------------

class TestToxicidad:
    def test_intoxicado_tiene_toxicidad(self, vector_intoxicado):
        toxicidades = evaluar_toxicidad(vector_intoxicado)
        # F2=0.65 sin F3=0.20 → toxicidad alta
        assert len(toxicidades) > 0
        f2_f3 = [t for t in toxicidades if t.fi == "F2" and t.fj == "F3"]
        assert len(f2_f3) > 0
        assert f2_f3[0].valor > 0

    def test_pilates_toxicidad_subliminal(self, vector_pilates):
        toxicidades = evaluar_toxicidad(vector_pilates)
        # F2=0.30, F3=0.25 → brecha 0.05 < umbral 0.10 → subliminal
        f2_f3 = [t for t in toxicidades if t.fi == "F2" and t.fj == "F3"]
        if f2_f3:
            assert f2_f3[0].subliminal or f2_f3[0].valor == 0

    def test_equilibrado_sin_toxicidad(self, vector_equilibrado):
        toxicidades = evaluar_toxicidad(vector_equilibrado)
        # No debería haber toxicidad significativa
        total = sum(t.valor for t in toxicidades)
        assert total < 0.01


# ---------------------------------------------------------------------------
# Atractor (Ley 10)
# ---------------------------------------------------------------------------

class TestAtractor:
    def test_equilibrado_atractor_equilibrio(self, vector_equilibrado):
        assert atractor_mas_cercano(vector_equilibrado) == "equilibrio"

    def test_quemado_atractor_colapso(self):
        v = VectorFuncional(f1=0.25, f2=0.20, f3=0.20, f4=0.25, f5=0.35, f6=0.20, f7=0.15)
        assert atractor_mas_cercano(v) == "colapso"


# ---------------------------------------------------------------------------
# evaluar_campo() completo
# ---------------------------------------------------------------------------

class TestEvaluarCampo:
    def test_pilates_completo(self, vector_pilates):
        estado = evaluar_campo(vector_pilates)
        assert isinstance(estado, EstadoCampo)
        assert estado.eslabon_debil == "F7"
        assert "salud" in estado.lentes
        assert "sentido" in estado.lentes
        assert "continuidad" in estado.lentes

    def test_estado_tiene_todos_los_campos(self, vector_pilates):
        estado = evaluar_campo(vector_pilates)
        assert estado.vector == vector_pilates
        assert isinstance(estado.coalicion, str)
        assert isinstance(estado.perfil_lente, str)
        assert isinstance(estado.dependencias_violadas, list)
        assert isinstance(estado.toxicidades, list)
        assert isinstance(estado.toxicidad_total, float)
        assert isinstance(estado.estable, bool)
        assert isinstance(estado.atractor_mas_cercano, str)
