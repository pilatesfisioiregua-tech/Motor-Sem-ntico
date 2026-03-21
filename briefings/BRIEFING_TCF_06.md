# BRIEFING_TCF_06 — Integrar TCF en pipeline existente

**Fecha:** 2026-03-19
**Prioridad:** Después de que BRIEFING_TCF_TEST pase con 0 failures
**Ejecutar:** Claude Code
**Prerequisito:** Todos los tests de BRIEFING_TCF_TEST pasan

---

## QUÉ HACER

Integrar el módulo `src/tcf/` en el pipeline existente (3 archivos a modificar). El módulo TCF ya existe y tiene tests pasando. Ahora hay que conectarlo.

---

## ARCHIVO 1: `src/pipeline/detector_huecos.py`

### ANTES (estado actual)

```python
@dataclass
class DetectorResult:
    huecos: list[Hueco]
    perfil_acoples: dict[str, int]
    diagnostico_acople: str
    inteligencias_sugeridas: list[str]
```

La función `detect()` solo hace análisis sintáctico (regex).

### DESPUÉS (lo que debe quedar)

Añadir import al principio del archivo:

```python
from src.tcf.detector_tcf import detectar_tcf, DetectorTCFResult, enriquecer_detector_result
from src.tcf.campo import VectorFuncional
```

Añadir campo opcional a `DetectorResult`:

```python
@dataclass
class DetectorResult:
    huecos: list[Hueco]
    perfil_acoples: dict[str, int]
    diagnostico_acople: str
    inteligencias_sugeridas: list[str]
    tcf: DetectorTCFResult | None = None  # <-- NUEVO
```

Modificar `detect()` para incluir TCF:

```python
async def detect(input_text: str, vector_previo: dict[str, float] | None = None) -> DetectorResult:
    """Ejecuta detección de huecos + análisis TCF."""
    from src.meta_red import load_marco_linguistico
    marco = load_marco_linguistico()
    result = detectar_huecos(input_text, marco)

    # TCF: pre-screening lingüístico + campo si hay vector
    vector = VectorFuncional.from_dict(vector_previo) if vector_previo else None
    tcf_result = detectar_tcf(input_text, vector)
    result.tcf = tcf_result

    # Si TCF sugiere INTs por receta, añadirlas a las sugeridas
    if tcf_result.receta and tcf_result.receta.ints:
        for int_id in tcf_result.receta.ints:
            if int_id not in result.inteligencias_sugeridas:
                result.inteligencias_sugeridas.append(int_id)

    return result
```

### CRITERIO PASS

```bash
python -c "from src.pipeline.detector_huecos import detect; print('OK')"
```

No debe romper el test existente `tests/test_detector.py` (el parámetro `vector_previo` es opcional).

---

## ARCHIVO 2: `src/pipeline/router.py`

### QUÉ CAMBIAR

El Router actualmente selecciona INTs solo por LLM. Con TCF, la receta prescribe las INTs y el LLM las refina pero NO las contradice.

1. Añadir import:

```python
from src.tcf.detector_tcf import DetectorTCFResult
```

2. Modificar la firma de `route()` para recibir TCF:

```python
async def route(
    input_text: str,
    contexto: str | None,
    modo: str,
    forzadas: list[str],
    excluidas: list[str],
    huecos: DetectorResult | None = None,
    tcf: DetectorTCFResult | None = None,  # <-- NUEVO
) -> RouterResult:
```

3. Dentro de `route()`, después de parsear la respuesta del LLM, añadir lógica de receta:

```python
    selected = data.get("inteligencias", [])

    # TCF: si hay receta, usarla como base (el LLM refina, no contradice)
    if tcf and tcf.receta and tcf.receta.ints:
        receta_ints = tcf.receta.ints
        # La receta tiene prioridad — las INTs del LLM complementan
        merged = list(receta_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged
```

4. Añadir info de TCF al `huecos_info` del prompt:

```python
    # Info TCF para el prompt
    tcf_info = ""
    if tcf and tcf.scoring:
        tcf_info = (
            f"\nARQUETIPO DETECTADO: {tcf.scoring.primario.arquetipo} "
            f"(score {tcf.scoring.primario.score})\n"
        )
        if tcf.receta:
            tcf_info += f"RECETA PRESCRITA: {', '.join(tcf.receta.ints)}\n"
            tcf_info += f"LENTE PRIMARIA: {tcf.receta.lente}\n"
            if tcf.receta.frenar:
                tcf_info += f"FUNCIONES A FRENAR: {', '.join(tcf.receta.frenar)}\n"
            tcf_info += "IMPORTANTE: La receta tiene prioridad. Tu selección COMPLEMENTA, no reemplaza.\n"
```

Y concatenarlo en el `system_prompt`:

```python
    system_prompt = ROUTER_SYSTEM.format(
        catalogo=catalogo,
        modo=modo,
        huecos_info=huecos_info + tcf_info,  # <-- AÑADIR tcf_info
    )
```

### CRITERIO PASS

```bash
python -c "from src.pipeline.router import route; print('OK')"
```

El test existente `tests/test_router.py` debe seguir pasando (tcf=None por defecto).

---

## ARCHIVO 3: `src/pipeline/orchestrator.py`

### QUÉ CAMBIAR

Añadir Paso 0 (pre-screening TCF) y pasar el resultado TCF al Router.

1. En `run_pipeline()`, después de Capa 0 (detector), añadir paso TCF:

```python
    # CAPA 0: Detector de Huecos (código puro, $0)
    log.info("pipeline_detector_start")
    huecos = await detect(request.input)  # Ya incluye TCF internamente
    log.info("pipeline_detector_done", huecos=len(huecos.huecos),
             sugeridas=huecos.inteligencias_sugeridas)

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

2. Pasar TCF al Router:

```python
    # CAPA 1: Router
    log.info("pipeline_router_start", modo=config.modo)
    router_result = await route(
        input_text=request.input,
        contexto=request.contexto,
        modo=config.modo,
        forzadas=config.inteligencias_forzadas,
        excluidas=config.inteligencias_excluidas,
        huecos=huecos,
        tcf=huecos.tcf,  # <-- NUEVO
    )
```

3. Añadir info TCF a la telemetría de respuesta:

```python
    # En el dict response, dentro de "algoritmo_usado":
    "algoritmo_usado": {
        "inteligencias": algoritmo.inteligencias,
        "operaciones": [...],
        "loops": algoritmo.loops,
        "huecos_detectados": len(huecos.huecos),
        # NUEVO: info TCF
        "tcf": {
            "firmas": [f.arquetipo for f in huecos.tcf.firmas] if huecos.tcf else [],
            "arquetipo_primario": huecos.tcf.scoring.primario.arquetipo if huecos.tcf and huecos.tcf.scoring else None,
            "receta_ints": huecos.tcf.receta.ints if huecos.tcf and huecos.tcf.receta else [],
            "receta_frenar": huecos.tcf.receta.frenar if huecos.tcf and huecos.tcf.receta else [],
        },
    },
```

### CRITERIO PASS

```bash
python -c "from src.pipeline.orchestrator import run_pipeline; print('OK')"
```

---

## TEST DE INTEGRACIÓN

Crear `tests/test_pipeline_tcf.py`:

```python
"""Test de integración: pipeline con TCF."""
import pytest
from src.pipeline.detector_huecos import detect
from src.tcf.constantes import VECTOR_PILATES


@pytest.mark.asyncio
async def test_detect_con_tcf_sin_vector():
    """Detect funciona sin vector previo (solo pre-screening)."""
    result = await detect("Todo depende de mí, necesito delegar")
    assert result.tcf is not None
    assert len(result.tcf.firmas) > 0
    assert result.tcf.estado_campo is None  # Sin vector, no hay campo


@pytest.mark.asyncio
async def test_detect_con_tcf_con_vector():
    """Detect funciona con vector previo (campo completo)."""
    result = await detect("Todo depende de mí", vector_previo=VECTOR_PILATES)
    assert result.tcf is not None
    assert result.tcf.estado_campo is not None
    assert result.tcf.scoring is not None
    assert result.tcf.receta is not None
    assert result.tcf.scoring.primario.arquetipo == "maquina_sin_alma"


@pytest.mark.asyncio
async def test_detect_ints_enriquecidas_por_receta():
    """Las INTs sugeridas incluyen las de la receta TCF."""
    result = await detect("Todo depende de mí", vector_previo=VECTOR_PILATES)
    # La receta de maquina_sin_alma incluye INT-02, INT-17, INT-15, INT-12, INT-16
    assert "INT-16" in result.inteligencias_sugeridas
```

Nota: necesita `pytest-asyncio`. Instalar si falta: `pip install pytest-asyncio`

### COMANDO FINAL

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico && python -m pytest tests/test_pipeline_tcf.py tests/test_detector.py -v --tb=short 2>&1
```

### CRITERIO PASS TOTAL

- Tests TCF módulo: 0 failures (BRIEFING_TCF_TEST)
- Tests integración: 0 failures (este briefing)
- Tests existentes: 0 failures (test_detector.py, test_router.py)

---

## SECUENCIA DE EJECUCIÓN

```
1. pytest tests/test_campo.py tests/test_arquetipos.py tests/test_recetas.py tests/test_lentes.py -v
   → Si falla, corregir src/tcf/*.py y repetir

2. Modificar src/pipeline/detector_huecos.py (añadir TCF)
   → python -c "from src.pipeline.detector_huecos import detect; print('OK')"

3. Modificar src/pipeline/router.py (añadir TCF)
   → python -c "from src.pipeline.router import route; print('OK')"

4. Modificar src/pipeline/orchestrator.py (añadir TCF)
   → python -c "from src.pipeline.orchestrator import run_pipeline; print('OK')"

5. Crear tests/test_pipeline_tcf.py
   → pytest tests/test_pipeline_tcf.py -v

6. Verificar que tests existentes no se rompieron:
   → pytest tests/test_detector.py tests/test_router.py -v
```

---

**FIN BRIEFING_TCF_06**
