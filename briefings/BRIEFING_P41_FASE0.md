# BRIEFING_P41_FASE0 — CeldaCampo + VectorFuncionalDual (aditivo, 0 cambios en código existente)

**Fecha:** 2026-03-19
**Prioridad:** MEDIA
**Dependencias:** TCF completa (✅), Gestor v0 (✅)
**Principio:** P41 CR0 — "Los gradientes son duales: número para calcular, significado para diagnosticar."

---

## OBJETIVO

Crear las estructuras de datos duales (numérica + semántica) como extensiones ADITIVAS. CERO cambios en archivos existentes. El código actual sigue funcionando exactamente igual.

---

## ARCHIVOS A CREAR (3 nuevos)

### 1. `src/tcf/campo_dual.py` (~120 líneas)

```python
"""Campo funcional dual — representación numérica + semántica coexistiendo.

Extiende campo.py SIN modificarlo. VectorFuncionalDual envuelve 7 CeldaCampo
y expone .numerico() → VectorFuncional para compatibilidad total con TCF.

Fuente: docs/L0/GRADIENTES_DUALES.md
Principio: P41 (CR0) — "Los gradientes son duales."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.tcf.campo import VectorFuncional, EstadoCampo, evaluar_campo
from src.tcf.constantes import FUNCIONES


# ---------------------------------------------------------------------------
# §1. CELDA CAMPO — unidad dual
# ---------------------------------------------------------------------------

@dataclass
class CeldaCampo:
    """Una celda del campo funcional con representación dual."""
    funcion: str              # "F3"
    lente: str                # "salud" (lente primaria para esta celda)

    # Representación numérica
    grado: float              # 0.25

    # Representación semántica (todas opcionales — se llenan progresivamente)
    estado: Optional[str] = None          # diagnóstico actual
    objetivo: Optional[str] = None        # estado objetivo
    gap_semantico: Optional[str] = None   # qué hay que cambiar, en palabras
    evidencias: list[str] = field(default_factory=list)

    # Metadata
    fuente: str = "estimado"    # "motor_vn" | "reactor_v4" | "usuario" | "estimado"
    confianza: float = 0.5      # 0.0-1.0
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not (0.0 <= self.grado <= 1.0):
            raise ValueError(f"grado={self.grado} fuera de rango [0, 1]")
        if not (0.0 <= self.confianza <= 1.0):
            raise ValueError(f"confianza={self.confianza} fuera de rango [0, 1]")

    def tiene_semantica(self) -> bool:
        """True si la celda tiene al menos estado o evidencias."""
        return self.estado is not None or len(self.evidencias) > 0

    def to_dict(self) -> dict:
        """Serializa para JSON/DB."""
        d = {
            "funcion": self.funcion,
            "lente": self.lente,
            "grado": self.grado,
            "fuente": self.fuente,
            "confianza": self.confianza,
        }
        if self.estado is not None:
            d["estado"] = self.estado
        if self.objetivo is not None:
            d["objetivo"] = self.objetivo
        if self.gap_semantico is not None:
            d["gap_semantico"] = self.gap_semantico
        if self.evidencias:
            d["evidencias"] = self.evidencias
        if self.timestamp is not None:
            d["timestamp"] = self.timestamp
        return d

    @classmethod
    def from_dict(cls, d: dict) -> CeldaCampo:
        return cls(
            funcion=d["funcion"],
            lente=d.get("lente", "salud"),
            grado=d["grado"],
            estado=d.get("estado"),
            objetivo=d.get("objetivo"),
            gap_semantico=d.get("gap_semantico"),
            evidencias=d.get("evidencias", []),
            fuente=d.get("fuente", "estimado"),
            confianza=d.get("confianza", 0.5),
            timestamp=d.get("timestamp"),
        )

    @classmethod
    def solo_numerico(cls, funcion: str, grado: float, lente: str = "salud") -> CeldaCampo:
        """Crea celda con solo grado numérico (Tier 1-2, lookup)."""
        return cls(funcion=funcion, lente=lente, grado=grado)


# ---------------------------------------------------------------------------
# §2. VECTOR FUNCIONAL DUAL — 7 celdas
# ---------------------------------------------------------------------------

@dataclass
class VectorFuncionalDual:
    """Vector de estado dual: 7 funciones × (número + semántica)."""
    celdas: dict[str, CeldaCampo]  # "F1" → CeldaCampo, ..., "F7" → CeldaCampo

    def __post_init__(self):
        for f in FUNCIONES:
            if f not in self.celdas:
                raise ValueError(f"Falta función {f} en celdas")

    def numerico(self) -> VectorFuncional:
        """Extrae solo la parte numérica. Compatibilidad total con TCF existente."""
        return VectorFuncional.from_dict({
            f: self.celdas[f].grado for f in FUNCIONES
        })

    def grado(self, funcion: str) -> float:
        """Acceso rápido al grado numérico de una función."""
        return self.celdas[funcion].grado

    def estado(self, funcion: str) -> Optional[str]:
        """Descripción semántica del estado actual de una función."""
        return self.celdas[funcion].estado

    def gap_semantico(self, funcion: str) -> Optional[str]:
        """Gap semántico de una función."""
        return self.celdas[funcion].gap_semantico

    def evidencias(self, funcion: str) -> list[str]:
        """Evidencias que soportan el grado de una función."""
        return self.celdas[funcion].evidencias

    def tiene_semantica(self) -> bool:
        """True si al menos una celda tiene semántica."""
        return any(c.tiene_semantica() for c in self.celdas.values())

    def cobertura_semantica(self) -> float:
        """Proporción de celdas con semántica (0.0-1.0)."""
        n = sum(1 for c in self.celdas.values() if c.tiene_semantica())
        return n / len(FUNCIONES)

    def to_dict(self) -> dict:
        return {f: self.celdas[f].to_dict() for f in FUNCIONES}

    @classmethod
    def from_dict(cls, d: dict) -> VectorFuncionalDual:
        celdas = {f: CeldaCampo.from_dict(v) for f, v in d.items()}
        return cls(celdas=celdas)

    @classmethod
    def desde_vector_numerico(
        cls,
        vector: VectorFuncional,
        lente: str = "salud",
        fuente: str = "estimado",
    ) -> VectorFuncionalDual:
        """Crea dual desde un VectorFuncional existente (solo números, sin semántica)."""
        d = vector.to_dict()
        celdas = {
            f: CeldaCampo.solo_numerico(funcion=f, grado=d[f], lente=lente)
            for f in FUNCIONES
        }
        for c in celdas.values():
            c.fuente = fuente
        return cls(celdas=celdas)


# ---------------------------------------------------------------------------
# §3. ESTADO CAMPO DUAL — campo completo con ambas capas
# ---------------------------------------------------------------------------

@dataclass
class EstadoCampoDual:
    """Estado completo del campo con representación dual.

    Envuelve EstadoCampo (numérico, ya existe) + VectorFuncionalDual (nuevo).
    """
    # Capa numérica (la que ya existe — generada por evaluar_campo)
    estado_numerico: EstadoCampo

    # Capa dual (nueva)
    vector_dual: VectorFuncionalDual

    # Diagnóstico integrado (se llena en fases posteriores)
    diagnostico_natural: Optional[str] = None
    intervenciones_concretas: list[str] = field(default_factory=list)

    @classmethod
    def desde_vector_dual(cls, vector_dual: VectorFuncionalDual) -> EstadoCampoDual:
        """Crea estado completo: evalúa TCF numérica + mantiene semántica."""
        estado_numerico = evaluar_campo(vector_dual.numerico())
        return cls(
            estado_numerico=estado_numerico,
            vector_dual=vector_dual,
        )

    @classmethod
    def desde_vector_numerico(cls, vector: VectorFuncional) -> EstadoCampoDual:
        """Crea estado dual desde vector solo numérico (upgrade path)."""
        dual = VectorFuncionalDual.desde_vector_numerico(vector)
        estado_numerico = evaluar_campo(vector)
        return cls(
            estado_numerico=estado_numerico,
            vector_dual=dual,
        )
```

---

### 2. `tests/test_campo_dual.py` (~180 líneas)

```python
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
        assert estado.estado_numerico.coalicion == "salud_sentido"
        # Semántico también
        assert estado.vector_dual.estado("F7") is not None
        assert "documentado" in estado.vector_dual.estado("F7").lower()

    def test_diagnostico_natural_inicialmente_none(self, vector_pilates_dual):
        estado = EstadoCampoDual.desde_vector_dual(vector_pilates_dual)
        assert estado.diagnostico_natural is None
        assert estado.intervenciones_concretas == []
```

---

### 3. Actualizar `src/tcf/__init__.py`

Añadir al final del docstring y los imports:

**BEFORE (actual):**
```python
"""Módulo TCF — Teoría del Campo Funcional como código ejecutable.

Implementa las 14 leyes + 5 teoremas de la TCF:
  - constantes: tablas INT×F, INT×L, dependencias, valoración lentes, arquetipos, firmas
  - campo: VectorFuncional, EstadoCampo, evaluar_campo()
  - arquetipos: scoring_multi_arquetipo(), pre_screening_linguistico()
  - recetas: 11 recetas + generar_receta_mixta() + aplicar_regla_14()
  - lentes: ecuacion_transferencia(), identificar_perfil_lente(), es_equilibrio_nash()
  - detector_tcf: integración con detector de huecos existente
"""
```

**AFTER:**
```python
"""Módulo TCF — Teoría del Campo Funcional como código ejecutable.

Implementa las 14 leyes + 5 teoremas de la TCF:
  - constantes: tablas INT×F, INT×L, dependencias, valoración lentes, arquetipos, firmas
  - campo: VectorFuncional, EstadoCampo, evaluar_campo()
  - campo_dual: CeldaCampo, VectorFuncionalDual, EstadoCampoDual (P41)
  - arquetipos: scoring_multi_arquetipo(), pre_screening_linguistico()
  - recetas: 11 recetas + generar_receta_mixta() + aplicar_regla_14()
  - lentes: ecuacion_transferencia(), identificar_perfil_lente(), es_equilibrio_nash()
  - detector_tcf: integración con detector de huecos existente
"""
```

---

## ARCHIVOS QUE NO SE TOCAN

- `src/tcf/campo.py` — INTACTO
- `src/tcf/constantes.py` — INTACTO
- `src/tcf/arquetipos.py` — INTACTO
- `src/tcf/recetas.py` — INTACTO
- `src/tcf/lentes.py` — INTACTO
- `src/tcf/detector_tcf.py` — INTACTO
- `src/pipeline/*` — INTACTO
- `src/gestor/*` — INTACTO
- Todos los tests existentes — INTACTOS

---

## CRITERIOS PASS/FAIL

**Ejecutar:**
```bash
cd motor-semantico
python -m pytest tests/test_campo_dual.py -v
python -m pytest tests/ -v  # todos los tests anteriores siguen pasando
```

**PASS si:**
1. `test_campo_dual.py` — TODOS los tests pasan (esperados: ~20)
2. Tests existentes — 92 passed, 0 failures (mismos que antes)
3. `src/tcf/campo_dual.py` existe con las 3 clases: CeldaCampo, VectorFuncionalDual, EstadoCampoDual
4. `from src.tcf.campo_dual import CeldaCampo, VectorFuncionalDual, EstadoCampoDual` funciona
5. El test CRÍTICO pasa: `VectorFuncionalDual.numerico()` produce exactamente el mismo `VectorFuncional` que `VectorFuncional.from_dict(VECTOR_PILATES)`

**FAIL si:**
- Algún test existente se rompe
- Se modificó algún archivo existente (excepto `__init__.py`)
- Las clases no son importables desde `src.tcf.campo_dual`

---

**FIN BRIEFING**
