# BRIEFING_CASO_PILATES — Validar pipeline completo con input Pilates real

**Fecha:** 2026-03-19
**Prioridad:** ALTA — validación end-to-end pre-deploy
**Dependencias:** BRIEFING_VECTOR_ESTIMADO (✅ o debe completar antes)
**Paralelizable con VECTOR_ESTIMADO:** NO — depende de `estimar_vector_desde_firmas()`

---

## OBJETIVO

Validar que el pipeline produce el diagnóstico correcto para el caso Pilates usando SOLO texto (sin vector previo). Es la prueba de que todo encaja: firmas → estimación → TCF → Gestor → Router base.

Dos entregables:
1. **Test `tests/test_caso_pilates.py`** — tests de integración que validan detect→Gestor (código puro, $0, sin LLM)
2. **Actualización `orchestrator.py`** — log `vector_estimado` + incluirlo en response JSON

---

## ENTREGABLE 1: `tests/test_caso_pilates.py` (nuevo, ~150 líneas)

```python
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

    def test_receta_secuencia_f5_f3_f7(self):
        """Receta de maquina_sin_alma: secuencia F5→F3→F7."""
        result = detectar_tcf(PILATES_INPUT_CORTO)
        assert result.receta is not None
        assert result.receta.secuencia == ["F5", "F3", "F7"]

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
        assert huecos.tcf.receta.secuencia == ["F5", "F3", "F7"]

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
```

---

## ENTREGABLE 2: Actualización `orchestrator.py` — log vector_estimado

**EDIT 1 — Añadir log de `vector_estimado` después del log de scoring:**

**BEFORE:**
```python
    # Log TCF si disponible
    if huecos.tcf:
        if huecos.tcf.firmas:
            log.info("pipeline_tcf_firmas",
                     arquetipos=[f.arquetipo for f in huecos.tcf.firmas])
        if huecos.tcf.scoring:
            log.info("pipeline_tcf_scoring",
                     primario=huecos.tcf.scoring.primario.arquetipo,
                     score=huecos.tcf.scoring.primario.score)
```

**AFTER:**
```python
    # Log TCF si disponible
    if huecos.tcf:
        if huecos.tcf.firmas:
            log.info("pipeline_tcf_firmas",
                     arquetipos=[f.arquetipo for f in huecos.tcf.firmas])
        if huecos.tcf.scoring:
            log.info("pipeline_tcf_scoring",
                     primario=huecos.tcf.scoring.primario.arquetipo,
                     score=huecos.tcf.scoring.primario.score,
                     vector_estimado=huecos.tcf.vector_estimado)
```

**EDIT 2 — Añadir `vector_estimado` al response JSON, sección tcf:**

**BEFORE:**
```python
            "tcf": {
                "firmas": [f.arquetipo for f in huecos.tcf.firmas] if huecos.tcf else [],
                "arquetipo_primario": huecos.tcf.scoring.primario.arquetipo if huecos.tcf and huecos.tcf.scoring else None,
                "receta_ints": huecos.tcf.receta.ints if huecos.tcf and huecos.tcf.receta else [],
                "receta_frenar": huecos.tcf.receta.frenar if huecos.tcf and huecos.tcf.receta else [],
            },
```

**AFTER:**
```python
            "tcf": {
                "firmas": [f.arquetipo for f in huecos.tcf.firmas] if huecos.tcf else [],
                "arquetipo_primario": huecos.tcf.scoring.primario.arquetipo if huecos.tcf and huecos.tcf.scoring else None,
                "receta_ints": huecos.tcf.receta.ints if huecos.tcf and huecos.tcf.receta else [],
                "receta_frenar": huecos.tcf.receta.frenar if huecos.tcf and huecos.tcf.receta else [],
                "vector_estimado": huecos.tcf.vector_estimado if huecos.tcf else False,
            },
```

---

## ARCHIVOS QUE NO SE TOCAN

Todo excepto `orchestrator.py` (2 edits mínimos) y el nuevo `test_caso_pilates.py`.

---

## CRITERIOS PASS/FAIL

**Ejecutar:**
```bash
cd motor-semantico
python -m pytest tests/test_caso_pilates.py -v
python -m pytest tests/ -v --ignore=tests/test_pipeline_e2e.py
```

**PASS si:**
1. `tests/test_caso_pilates.py` — TODOS los tests pasan (~18 tests)
2. Tests existentes siguen pasando
3. Test CRÍTICO: `detect(PILATES_INPUT_LARGO)` sin vector → `scoring.primario.arquetipo == "maquina_sin_alma"`
4. Test CRÍTICO: `receta.secuencia == ["F5", "F3", "F7"]`
5. Test CRÍTICO: Gestor compila programa con `lente_primaria == "continuidad"` e `INT-17` incluida
6. `grep "vector_estimado" src/pipeline/orchestrator.py` aparece 2 veces

**FAIL si:**
- Algún test del caso Pilates no pasa (ej: no detecta maquina_sin_alma)
- Tests existentes se rompen
- Se modificó algo más allá de orchestrator.py (2 edits) y el nuevo test

---

**FIN BRIEFING**
