# BRIEFING_GESTOR_02 — Conectar Gestor al pipeline

**Fecha:** 2026-03-19
**Prioridad:** Alta — el Gestor existe pero no está conectado
**Ejecutar:** Claude Code
**Prerequisito:** BRIEFING_TCF_07 + BRIEFING_GESTOR_01 completos (87+ tests pass)

---

## CONTEXTO

El Gestor v0 existe en `src/gestor/` (compilador, programa, tier, modelos) con 17 tests pasando. El pipeline en `orchestrator.py` ya tiene TCF integrada. Pero el Gestor NO está conectado — el pipeline sigue usando el Router directamente sin pasar por el compilador del Gestor.

**Objetivo:** Insertar el Gestor entre el Detector (Capa 0) y el Router (Capa 1). El flujo pasa de:

```
ANTES:  detect → route (LLM elige INTs) → compose → ...
DESPUÉS: detect → GESTOR compila programa → route (usa programa como base) → compose → ...
```

El ProgramaCompilado aporta: INTs prescriptas por receta, modelos asignados por celda, tier decidido, funciones a FRENAR. El Router sigue existiendo pero su rol cambia: refina/complementa lo que el Gestor prescribe, no decide desde cero.

---

## ARCHIVOS A MODIFICAR

1. `src/pipeline/orchestrator.py` — insertar Gestor entre detect y route
2. `src/pipeline/router.py` — recibir programa del Gestor (reemplaza el `tcf` directo)
3. `tests/test_gestor_pipeline.py` — test de integración (NUEVO)

**NO se tocan:** src/gestor/*, src/tcf/*, src/pipeline/evaluador.py, src/pipeline/registrador.py

---

## CAMBIO 1: `src/pipeline/orchestrator.py`

### Añadir import al principio:

```python
from src.gestor.compilador import compilar_programa
from src.gestor.programa import ProgramaCompilado
from src.tcf.arquetipos import scoring_multi_arquetipo
from src.tcf.campo import VectorFuncional
```

### Insertar Gestor después de Capa 0, antes de Capa 1

Buscar el bloque que empieza con `# CAPA 1: Router` y añadir ANTES:

```python
    # GESTOR: Compilar programa por arquetipo
    programa: ProgramaCompilado | None = None
    if huecos.tcf and huecos.tcf.scoring:
        log.info("pipeline_gestor_start",
                 arquetipo=huecos.tcf.scoring.primario.arquetipo)
        programa = compilar_programa(
            scoring=huecos.tcf.scoring,
            vector=huecos.tcf.estado_campo.vector if huecos.tcf.estado_campo else None,
            modo=config.modo,
            presupuesto_max=config.presupuesto_max,
        )
        log.info("pipeline_gestor_done",
                 tier=programa.tier,
                 ints=programa.inteligencias(),
                 frenar=programa.frenar,
                 pasos=len(programa.pasos))
    else:
        log.info("pipeline_gestor_skip", reason="sin scoring TCF")
```

### Pasar programa al Router

Cambiar la llamada a `route()`:

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
        tcf=huecos.tcf,
        programa=programa,  # <-- NUEVO
    )
    log.info("pipeline_router_done", inteligencias=router_result.inteligencias)
```

### Añadir programa a la telemetría de respuesta

En el dict `response["algoritmo_usado"]`, añadir después de "tcf":

```python
            "gestor": {
                "tier": programa.tier if programa else None,
                "arquetipo_base": programa.arquetipo_base if programa else None,
                "arquetipo_score": programa.arquetipo_score if programa else None,
                "pasos": len(programa.pasos) if programa else 0,
                "modelos": programa.modelos() if programa else [],
                "frenar": programa.frenar if programa else [],
                "lente_primaria": programa.lente_primaria if programa else None,
                "coste_estimado": programa.coste_estimado if programa else None,
            },
```

---

## CAMBIO 2: `src/pipeline/router.py`

### Añadir import:

```python
from src.gestor.programa import ProgramaCompilado
```

### Modificar firma de `route()`:

Añadir parámetro `programa`:

```python
async def route(
    input_text: str,
    contexto: str | None,
    modo: str,
    forzadas: list[str],
    excluidas: list[str],
    huecos: DetectorResult | None = None,
    tcf: DetectorTCFResult | None = None,
    programa: ProgramaCompilado | None = None,  # <-- NUEVO
) -> RouterResult:
```

### Usar programa como fuente principal de INTs (reemplaza TCF directo)

Buscar el bloque que dice:

```python
    # TCF: si hay receta, usarla como base (el LLM refina, no contradice)
    if tcf and tcf.receta and tcf.receta.ints:
        receta_ints = tcf.receta.ints
        merged = list(receta_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged
```

Reemplazar ese bloque completo por:

```python
    # GESTOR: si hay programa compilado, usarlo como base (tiene prioridad sobre TCF directo)
    if programa and programa.pasos:
        programa_ints = programa.inteligencias()
        merged = list(programa_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged
        log.info("router_usando_programa_gestor", ints_programa=programa_ints)
    # Fallback: TCF directo si no hay programa
    elif tcf and tcf.receta and tcf.receta.ints:
        receta_ints = tcf.receta.ints
        merged = list(receta_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged
```

### Añadir info del programa al prompt del LLM

Buscar donde se construye `tcf_info` y añadir después:

```python
    # Info del programa del Gestor para el prompt
    programa_info = ""
    if programa and programa.pasos:
        programa_info = (
            f"\nPROGRAMA COMPILADO POR EL GESTOR (tier {programa.tier}):\n"
            f"  INTs prescritas: {', '.join(programa.inteligencias())}\n"
            f"  Lente primaria: {programa.lente_primaria}\n"
            f"  Funciones objetivo: {[p.funcion_objetivo for p in programa.pasos]}\n"
        )
        if programa.frenar:
            programa_info += f"  FRENAR: {', '.join(programa.frenar)}\n"
        programa_info += "IMPORTANTE: El programa del Gestor tiene prioridad. Tu selección COMPLEMENTA.\n"
```

Y concatenarlo en el `system_prompt`:

```python
    system_prompt = ROUTER_SYSTEM.format(
        catalogo=catalogo,
        modo=modo,
        huecos_info=huecos_info + tcf_info + programa_info,  # <-- AÑADIR programa_info
    )
```

### Añadir info programa al RouterResult

Buscar el return y añadir tier:

```python
    return RouterResult(
        inteligencias=selected,
        pares_complementarios=data.get("pares_complementarios", []),
        descartadas=data.get("descartadas", []),
        razon=data.get("razon", ""),
        cost=llm.total_cost,
        time_s=elapsed,
        reglas_aplicadas=[
            {"regla": r.regla, "nombre": r.nombre, "passed": r.passed, "mensaje": r.mensaje}
            for r in verificar_reglas(selected, modo, vector_dict)
        ],
    )
```

No hace falta cambiar RouterResult — la info del programa ya está en la telemetría del orchestrator.

---

## CAMBIO 3: `tests/test_gestor_pipeline.py` (NUEVO)

```python
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
```

---

## SECUENCIA DE EJECUCIÓN

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico

# 1. Leer archivos antes de modificar
#    src/pipeline/orchestrator.py
#    src/pipeline/router.py

# 2. Modificar orchestrator.py (insertar Gestor + telemetría)
# 3. Modificar router.py (añadir parámetro programa + usar como fuente principal)
# 4. Crear tests/test_gestor_pipeline.py

# 5. Ejecutar tests nuevos
python -m pytest tests/test_gestor_pipeline.py -v --tb=short

# 6. Ejecutar TODOS los tests para verificar 0 regressions
python -m pytest tests/ -v --tb=short -k "not e2e"

# 7. Verificar import limpio
python -c "from src.pipeline.orchestrator import run_pipeline; print('OK')"
```

## CRITERIO PASS

- `tests/test_gestor_pipeline.py`: 7/7 pass
- Tests existentes: 0 regressions
- Import de orchestrator: sin errores

## NOTAS IMPORTANTES

- El parámetro `programa` en `route()` es **opcional** (default None). Si no hay scoring TCF, el Gestor se salta y el Router funciona como antes. Esto mantiene retrocompatibilidad total.
- Los tests existentes de `test_router.py` NO deben romperse porque `programa=None` por defecto.
- Los tests existentes de `test_pipeline_tcf.py` siguen pasando porque el Gestor se activa transparentemente cuando hay TCF.
- El test `test_detect_con_vector_produce_scoring_para_gestor` necesita `pytest-asyncio` (ya instalado por briefings anteriores).

---

**FIN BRIEFING_GESTOR_02**
