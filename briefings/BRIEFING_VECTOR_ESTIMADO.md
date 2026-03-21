# BRIEFING_VECTOR_ESTIMADO — Detector estima vector funcional desde firmas lingüísticas

**Fecha:** 2026-03-19
**Prioridad:** ALTA — bloquea caso real Pilates
**Dependencias:** TCF completa (✅), Gestor v0 (✅)
**Paralelizable con:** BRIEFING_P41_FASE0 (sí — archivos distintos)

---

## PROBLEMA

Hoy, `detect("Todo depende de mí")` sin `vector_previo`:
- Pre-screening: detecta firmas → "maquina_sin_alma" ✅
- Campo TCF: `None` ❌
- Scoring: `None` ❌
- Receta: `None` ❌
- Gestor: skip ❌
- Router: modo fallback sin programa ❌

**El pipeline completo (detect→Gestor→route) solo funciona si alguien pasa un vector previo. Para un caso NUEVO, el pipeline opera degradado.**

---

## SOLUCIÓN

Cuando hay firmas detectadas pero no hay `vector_previo`, **estimar un vector funcional a partir de las firmas lingüísticas**, usando los vectores canónicos de los arquetipos en `ARQUETIPOS_CANONICOS`.

Algoritmo:
1. Pre-screening lingüístico → firmas con confianza (ya existe)
2. Para cada firma, obtener vector canónico del arquetipo: `ARQUETIPOS_CANONICOS[firma.arquetipo]`
3. Blend: media ponderada de vectores canónicos por confianza de firma
4. Si solo 1 firma → usar su vector canónico directamente
5. Marcar vector como `fuente="estimado"`, confianza baja (~0.4-0.6)
6. Usar este vector estimado para ejecutar TCF completa (campo + scoring + receta)

**Resultado:** `detect("Todo depende de mí")` → EstadoCampo completo → scoring → receta → Gestor compila programa → Router tiene base.

---

## ARCHIVOS A MODIFICAR (2) + TESTS (1 modificado, 1 nuevo)

### 1. `src/tcf/detector_tcf.py` — Añadir `estimar_vector_desde_firmas()`

**AÑADIR** entre §1 y §2 (después de la clase `DetectorTCFResult`, antes de `detectar_tcf`):

```python
# ---------------------------------------------------------------------------
# §1.5 ESTIMACIÓN DE VECTOR DESDE FIRMAS LINGÜÍSTICAS
# ---------------------------------------------------------------------------

def estimar_vector_desde_firmas(
    firmas: list[FirmaDetectada],
) -> VectorFuncional | None:
    """Estima un vector funcional a partir de firmas lingüísticas detectadas.

    Usa los vectores canónicos de ARQUETIPOS_CANONICOS ponderados por
    confianza de la firma. Es una ESTIMACIÓN, no un diagnóstico.

    Retorna None si no hay firmas.
    """
    if not firmas:
        return None

    from src.tcf.constantes import ARQUETIPOS_CANONICOS, FUNCIONES

    # Filtrar firmas cuyos arquetipos tienen vector canónico
    firmas_validas = [f for f in firmas if f.arquetipo in ARQUETIPOS_CANONICOS]
    if not firmas_validas:
        return None

    # Si solo hay 1 firma, usar su vector canónico directamente
    if len(firmas_validas) == 1:
        return VectorFuncional.from_dict(
            ARQUETIPOS_CANONICOS[firmas_validas[0].arquetipo]
        )

    # Blend ponderado por confianza
    peso_total = sum(f.confianza for f in firmas_validas)
    if peso_total == 0:
        # Todas con confianza 0 → peso igual
        peso_total = len(firmas_validas)
        pesos = [1.0] * len(firmas_validas)
    else:
        pesos = [f.confianza for f in firmas_validas]

    blended = {f: 0.0 for f in FUNCIONES}
    for firma, peso in zip(firmas_validas, pesos):
        canon = ARQUETIPOS_CANONICOS[firma.arquetipo]
        for fi in FUNCIONES:
            blended[fi] += canon[fi] * peso

    for fi in FUNCIONES:
        blended[fi] = round(blended[fi] / peso_total, 3)
        blended[fi] = max(0.0, min(1.0, blended[fi]))

    return VectorFuncional.from_dict(blended)
```

**MODIFICAR** la función `detectar_tcf()`:

**BEFORE:**
```python
def detectar_tcf(
    input_text: str,
    vector: VectorFuncional | None = None,
) -> DetectorTCFResult:
    """Ejecuta análisis TCF sobre el input.

    Dos fases:
    - Fase A (siempre): pre-screening lingüístico del texto
    - Fase B (si hay vector): evaluación completa del campo funcional

    Args:
        input_text: texto del usuario a analizar
        vector: vector funcional previo del sistema (si existe, de DB/Reactor)
    """
    # Fase A: Pre-screening lingüístico
    firmas = pre_screening_linguistico(input_text)
    candidatos = [f.arquetipo for f in firmas]

    # Fase B: Campo funcional (si hay vector)
    estado = None
    scoring = None
    receta = None

    if vector is not None:
        estado = evaluar_campo(vector)
        scoring = scoring_multi_arquetipo(vector)
        receta = generar_receta_mixta(scoring, vector)

    return DetectorTCFResult(
        firmas=firmas,
        arquetipos_candidatos=candidatos,
        estado_campo=estado,
        scoring=scoring,
        receta=receta,
    )
```

**AFTER:**
```python
def detectar_tcf(
    input_text: str,
    vector: VectorFuncional | None = None,
) -> DetectorTCFResult:
    """Ejecuta análisis TCF sobre el input.

    Tres fases:
    - Fase A (siempre): pre-screening lingüístico del texto
    - Fase A.5 (si no hay vector pero sí firmas): estimar vector desde firmas
    - Fase B (si hay vector real o estimado): evaluación completa del campo funcional

    Args:
        input_text: texto del usuario a analizar
        vector: vector funcional previo del sistema (si existe, de DB/Reactor)
    """
    # Fase A: Pre-screening lingüístico
    firmas = pre_screening_linguistico(input_text)
    candidatos = [f.arquetipo for f in firmas]

    # Fase A.5: Estimar vector si no hay uno previo pero sí hay firmas
    vector_usado = vector
    estimado = False
    if vector_usado is None and firmas:
        vector_usado = estimar_vector_desde_firmas(firmas)
        estimado = vector_usado is not None

    # Fase B: Campo funcional (si hay vector real o estimado)
    estado = None
    scoring = None
    receta = None

    if vector_usado is not None:
        estado = evaluar_campo(vector_usado)
        scoring = scoring_multi_arquetipo(vector_usado)
        receta = generar_receta_mixta(scoring, vector_usado)

    return DetectorTCFResult(
        firmas=firmas,
        arquetipos_candidatos=candidatos,
        estado_campo=estado,
        scoring=scoring,
        receta=receta,
        vector_estimado=estimado,
    )
```

**MODIFICAR** el dataclass `DetectorTCFResult` — añadir campo:

**BEFORE:**
```python
@dataclass
class DetectorTCFResult:
    """Resultado del análisis TCF. Se añade al DetectorResult existente."""

    # Pre-screening lingüístico (siempre disponible, solo necesita texto)
    firmas: list[FirmaDetectada]
    arquetipos_candidatos: list[str]  # arquetipos sugeridos por firma lingüística

    # Campo funcional (solo si hay vector disponible)
    estado_campo: EstadoCampo | None
    scoring: ScoringMultiArquetipo | None
    receta: RecetaResultado | None
```

**AFTER:**
```python
@dataclass
class DetectorTCFResult:
    """Resultado del análisis TCF. Se añade al DetectorResult existente."""

    # Pre-screening lingüístico (siempre disponible, solo necesita texto)
    firmas: list[FirmaDetectada]
    arquetipos_candidatos: list[str]  # arquetipos sugeridos por firma lingüística

    # Campo funcional (solo si hay vector disponible — real o estimado)
    estado_campo: EstadoCampo | None
    scoring: ScoringMultiArquetipo | None
    receta: RecetaResultado | None

    # True si el vector fue estimado desde firmas (no provisto externamente)
    vector_estimado: bool = False
```

---

### 2. `src/pipeline/detector_huecos.py` — sin cambios

La función `detect()` ya pasa el resultado TCF al pipeline. Con el cambio en `detectar_tcf()`, ahora producirá campo+scoring+receta automáticamente para textos con firmas detectables. No hace falta tocar `detect()` ni `orchestrator.py`.

---

### 3. `tests/test_pipeline_tcf.py` — Actualizar test existente + añadir nuevos

**REEMPLAZAR archivo completo:**

```python
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
```

---

## ARCHIVOS QUE NO SE TOCAN

- `src/tcf/campo.py` — INTACTO
- `src/tcf/constantes.py` — INTACTO
- `src/tcf/arquetipos.py` — INTACTO
- `src/tcf/recetas.py` — INTACTO
- `src/tcf/lentes.py` — INTACTO
- `src/tcf/__init__.py` — INTACTO (el briefing P41_FASE0 puede tocarlo, no colisiona)
- `src/pipeline/orchestrator.py` — INTACTO (ya consume tcf.scoring correctamente)
- `src/pipeline/router.py` — INTACTO
- `src/gestor/*` — INTACTO
- `tests/test_campo.py`, `tests/test_arquetipos.py`, etc. — INTACTOS

---

## CRITERIOS PASS/FAIL

**Ejecutar:**
```bash
cd motor-semantico
python -m pytest tests/test_pipeline_tcf.py -v
python -m pytest tests/ -v --ignore=tests/test_pipeline_e2e.py
```

**PASS si:**
1. `tests/test_pipeline_tcf.py` — TODOS los tests pasan (~15 tests)
2. Tests existentes — los que pasaban siguen pasando (el test anterior `test_detect_con_tcf_sin_vector` se reemplazó, no se rompió)
3. `from src.tcf.detector_tcf import estimar_vector_desde_firmas` funciona
4. Test CRÍTICO: `detect("Todo depende de mí")` sin vector_previo → `result.tcf.scoring is not None`
5. Test CRÍTICO: el scoring estimado permite `compilar_programa()` → ProgramaCompilado válido

**FAIL si:**
- `detect("Todo depende de mí")` sigue devolviendo `scoring=None`
- Tests existentes en otros archivos se rompen
- Se modificaron archivos fuera de `detector_tcf.py` y `test_pipeline_tcf.py`

---

**FIN BRIEFING**
