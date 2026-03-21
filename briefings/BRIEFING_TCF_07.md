# BRIEFING_TCF_07 — Router enforce reglas + Registrador + Evaluador TCF

**Fecha:** 2026-03-19
**Prioridad:** INMEDIATA — 3 gaps rápidos de cerrar
**Ejecutar:** Claude Code
**Prerequisito:** 59 tests passing (post BRIEFING_TCF_06)

---

## PARTE 1: ROUTER ENFORCE REGLAS (5 min)

### Problema
Las 14 reglas existen en `src/config/reglas.py` como funciones verificables, pero el Router no las llama. La selección de INTs pasa por `enforce_rules()` (hardcoded parcial) pero no por `verificar_reglas()`.

### Cambio en `src/pipeline/router.py`

1. Añadir import:

```python
from src.config.reglas import verificar_reglas, reglas_que_fallan
```

2. Después de `selected = enforce_rules(selected, modo)`, añadir verificación y corrección:

```python
    # Aplicar reglas obligatorias (legacy)
    selected = enforce_rules(selected, modo)

    # Verificar 14 reglas del compilador
    vector_dict = None
    if tcf and tcf.estado_campo:
        vector_dict = tcf.estado_campo.vector.to_dict()

    fallos = reglas_que_fallan(selected, modo, vector_dict)
    if fallos:
        log.info("router_reglas_fallan",
                 fallos=[(r.regla, r.nombre, r.mensaje) for r in fallos])
        # Auto-corregir: añadir INTs sugeridas por las reglas
        for fallo in fallos:
            for correccion in fallo.correccion:
                if correccion not in selected and len(selected) < 6:
                    selected.append(correccion)
        # Re-verificar después de corrección
        fallos_post = reglas_que_fallan(selected, modo, vector_dict)
        if fallos_post:
            log.warning("router_reglas_no_corregibles",
                        fallos=[(r.regla, r.nombre) for r in fallos_post])
```

3. Añadir info de reglas al RouterResult. Primero extender el dataclass:

```python
@dataclass
class RouterResult:
    inteligencias: list[str]
    pares_complementarios: list[list[str]]
    descartadas: list[str]
    razon: str
    cost: float = 0.0
    time_s: float = 0.0
    reglas_aplicadas: list[dict] = field(default_factory=list)  # NUEVO
```

4. Al final del return, llenar reglas_aplicadas:

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

### Test

```python
# En tests/test_router_reglas.py
"""Test que el router aplica las 14 reglas."""
import pytest
from src.config.reglas import verificar_reglas, reglas_que_fallan


class TestReglasEnRouter:
    def test_seleccion_sin_cuantitativa_falla_r1(self):
        ints = ["INT-08", "INT-12", "INT-16"]
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 1 in reglas_fallidas

    def test_seleccion_completa_pasa(self):
        ints = ["INT-01", "INT-08", "INT-07", "INT-14", "INT-16"]
        fallos = reglas_que_fallan(ints, "analisis")
        # Puede haber advertencias (no fallos duros) pero R1 debe pasar
        r1_fallos = [f for f in fallos if f.regla == 1]
        assert len(r1_fallos) == 0

    def test_cluster_redundante_falla_r5(self):
        ints = ["INT-01", "INT-03", "INT-04", "INT-08", "INT-16"]  # INT-03 + INT-04 = sistémicas
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 5 in reglas_fallidas

    def test_int16_no_ultima_falla_r13(self):
        ints = ["INT-01", "INT-16", "INT-08", "INT-07"]  # INT-16 no es última
        fallos = reglas_que_fallan(ints, "analisis")
        reglas_fallidas = [f.regla for f in fallos]
        assert 13 in reglas_fallidas

    def test_frenar_detecta_f7_alta_sin_f5(self):
        vector = {"F1": 0.30, "F2": 0.65, "F3": 0.30, "F4": 0.45, "F5": 0.25, "F6": 0.45, "F7": 0.75}
        fallos = reglas_que_fallan(["INT-01", "INT-08", "INT-16"], "analisis", vector)
        r14_fallos = [f for f in fallos if f.regla == 14]
        assert len(r14_fallos) > 0
        assert "F7" in r14_fallos[0].mensaje

    def test_confrontacion_sin_existenciales_falla_r7(self):
        ints = ["INT-01", "INT-08", "INT-07", "INT-16"]
        fallos = reglas_que_fallan(ints, "confrontacion")
        reglas_fallidas = [f.regla for f in fallos]
        assert 7 in reglas_fallidas
```

### Criterio Pass

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
python -m pytest tests/test_router_reglas.py -v --tb=short
# 6/6 pass
python -c "from src.pipeline.router import route; print('import OK')"
```

---

## PARTE 2: REGISTRADOR — Paso 7 del pipeline (20 min)

### Problema
El Maestro §5.1 Paso 7 dice: registrar `datapoints_efectividad` con gap_pre, gap_post, modelo, celda. El schema SQL existe pero no hay código que lo llene, y la tabla no está creada en el schema actual.

### 2a. Añadir tabla en schema

Crear archivo de migración:

```sql
-- migrations/003_registrador.sql

-- Tabla de datapoints de efectividad (§6.6 Maestro)
CREATE TABLE IF NOT EXISTS datapoints_efectividad (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ejecucion_id UUID REFERENCES ejecuciones(id),
    pregunta_id TEXT,                    -- "INT07_F2_L1_003" (si disponible)
    inteligencia TEXT NOT NULL,          -- "INT-07"
    modelo TEXT NOT NULL,                -- "deepseek-v3.2-chat"
    caso_id TEXT,                        -- identificador del caso
    consumidor TEXT NOT NULL DEFAULT 'motor_vn',
    celda_objetivo TEXT,                 -- "F2×Salud" (si disponible de TCF)
    funcion TEXT,                        -- "F2" (de TCF)
    lente TEXT,                          -- "salud" (de TCF)
    gap_pre FLOAT,                      -- grado pre-ejecución (de TCF si disponible)
    gap_post FLOAT,                     -- grado post-ejecución (evaluador TCF)
    gap_cerrado FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre IS NOT NULL AND gap_post IS NOT NULL
        THEN gap_pre - gap_post ELSE NULL END
    ) STORED,
    tasa_cierre FLOAT GENERATED ALWAYS AS (
        CASE WHEN gap_pre IS NOT NULL AND gap_pre > 0 AND gap_post IS NOT NULL
        THEN (gap_pre - gap_post) / gap_pre ELSE NULL END
    ) STORED,
    operacion TEXT,                      -- 'individual', 'composicion', 'fusion', 'loop'
    score_calidad FLOAT,                -- del evaluador
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dp_inteligencia ON datapoints_efectividad(inteligencia);
CREATE INDEX IF NOT EXISTS idx_dp_modelo ON datapoints_efectividad(modelo);
CREATE INDEX IF NOT EXISTS idx_dp_celda ON datapoints_efectividad(celda_objetivo);
CREATE INDEX IF NOT EXISTS idx_dp_created ON datapoints_efectividad(created_at DESC);

-- Tabla de perfil de gradientes por caso (estado del campo pre/post)
CREATE TABLE IF NOT EXISTS perfil_gradientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ejecucion_id UUID REFERENCES ejecuciones(id),
    momento TEXT NOT NULL CHECK (momento IN ('pre', 'post')),
    vector_funcional JSONB NOT NULL,      -- {"F1": 0.50, "F2": 0.30, ...}
    lentes JSONB NOT NULL,                -- {"salud": 0.40, "sentido": 0.60, ...}
    arquetipo_primario TEXT,
    arquetipo_score FLOAT,
    coalicion TEXT,
    perfil_lente TEXT,
    eslabon_debil TEXT,
    toxicidad_total FLOAT,
    estable BOOLEAN,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pg_ejecucion ON perfil_gradientes(ejecucion_id);
```

### 2b. Crear `src/pipeline/registrador.py`

```python
"""Capa 7: Registrador — Persiste datapoints de efectividad.

Cada ejecución del pipeline genera datapoints que alimentan al Gestor.
Sin esto, el sistema no aprende.

Fuente: Maestro §5.1 Paso 7, §6.5
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass

log = structlog.get_logger()


@dataclass
class Datapoint:
    inteligencia: str
    modelo: str
    operacion: str          # 'individual', 'composicion', 'fusion', 'loop'
    score_calidad: float | None
    # Campos TCF (pueden ser None si no hay vector)
    funcion: str | None
    lente: str | None
    gap_pre: float | None
    gap_post: float | None


async def registrar_ejecucion(
    ejecucion_id: str,
    plan,                    # ExecutionPlan
    evaluation,              # EvaluationResult
    tcf_pre: dict | None,    # estado campo pre-ejecución (de detector)
    tcf_post: dict | None,   # estado campo post-ejecución (del evaluador, si existe)
) -> list[Datapoint]:
    """Registra datapoints de efectividad para cada operación ejecutada.

    Args:
        ejecucion_id: UUID de la ejecución en tabla 'ejecuciones'
        plan: ExecutionPlan con results
        evaluation: EvaluationResult con scores
        tcf_pre: estado del campo TCF antes de la ejecución (dict serializado)
        tcf_post: estado del campo TCF después (si el evaluador lo calculó)
    """
    datapoints = []

    for key, result in plan.results.items():
        dp = Datapoint(
            inteligencia=result.inteligencia,
            modelo=result.model,
            operacion=result.operacion_tipo,
            score_calidad=evaluation.score if evaluation else None,
            funcion=None,
            lente=None,
            gap_pre=None,
            gap_post=None,
        )

        # Si hay info TCF, enriquecer con coordenadas del campo
        if tcf_pre and "receta" in tcf_pre:
            receta = tcf_pre.get("receta", {})
            # Asignar función/lente según la receta
            if receta.get("secuencia"):
                # La primera función de la secuencia es el foco principal
                dp.lente = receta.get("lente")

        datapoints.append(dp)

    # Persistir en DB (fire and forget)
    try:
        await _persist_datapoints(ejecucion_id, datapoints)
        if tcf_pre:
            await _persist_gradientes(ejecucion_id, tcf_pre, "pre")
        if tcf_post:
            await _persist_gradientes(ejecucion_id, tcf_post, "post")
        log.info("registrador_ok", n_datapoints=len(datapoints))
    except Exception as e:
        log.error("registrador_error", error=str(e))

    return datapoints


async def _persist_datapoints(ejecucion_id: str, datapoints: list[Datapoint]):
    """Inserta datapoints en DB."""
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            for dp in datapoints:
                await conn.execute(
                    """INSERT INTO datapoints_efectividad
                       (ejecucion_id, inteligencia, modelo, operacion,
                        score_calidad, funcion, lente, gap_pre, gap_post)
                       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                       ON CONFLICT DO NOTHING""",
                    ejecucion_id, dp.inteligencia, dp.modelo, dp.operacion,
                    dp.score_calidad, dp.funcion, dp.lente, dp.gap_pre, dp.gap_post,
                )
    except Exception as e:
        log.warning("persist_datapoints_skip", error=str(e))


async def _persist_gradientes(ejecucion_id: str, tcf_data: dict, momento: str):
    """Inserta perfil de gradientes pre/post en DB."""
    try:
        from src.db.client import get_pool
        import json
        pool = await get_pool()

        campo = tcf_data.get("campo", {})
        scoring = tcf_data.get("scoring", {})

        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO perfil_gradientes
                   (ejecucion_id, momento, vector_funcional, lentes,
                    arquetipo_primario, arquetipo_score, coalicion,
                    perfil_lente, eslabon_debil, toxicidad_total, estable)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                   ON CONFLICT DO NOTHING""",
                ejecucion_id, momento,
                json.dumps(campo.get("vector", {})),
                json.dumps(campo.get("lentes", {})),
                scoring.get("primario", {}).get("arquetipo"),
                scoring.get("primario", {}).get("score"),
                campo.get("coalicion"),
                campo.get("perfil_lente"),
                campo.get("eslabon_debil"),
                campo.get("toxicidad_total"),
                campo.get("estable"),
            )
    except Exception as e:
        log.warning("persist_gradientes_skip", error=str(e))
```

### 2c. Integrar en orchestrator.py

Después del paso de telemetría existente (el `log_ejecucion`), añadir:

```python
    # CAPA 7: Registrador (datapoints de efectividad)
    try:
        from src.pipeline.registrador import registrar_ejecucion
        from src.tcf.detector_tcf import enriquecer_detector_result

        tcf_pre_data = None
        if huecos.tcf:
            tcf_pre_data = enriquecer_detector_result(huecos, huecos.tcf).get("tcf")

        await registrar_ejecucion(
            ejecucion_id=str(response.get("meta", {}).get("ejecucion_id", "")),
            plan=execution,
            evaluation=evaluation,
            tcf_pre=tcf_pre_data,
            tcf_post=None,  # TODO: evaluador TCF post-ejecución (Parte 3)
        )
    except Exception as e:
        log.error("registrador_error", error=str(e))
```

### Criterio Pass

```bash
python -c "from src.pipeline.registrador import registrar_ejecucion; print('import OK')"
# Sin errores de import
```

La persistencia real se testea con DB conectada (integración). Lo importante es que el código existe y no rompe el pipeline sin DB.

---

## PARTE 3: EVALUADOR CON TCF (15 min)

### Problema
El evaluador actual mide "calidad del texto" con heurísticas. El Maestro dice que Paso 5 debe re-evaluar el campo de gradientes POST-ejecución.

### Cambio en `src/pipeline/evaluador.py`

1. Añadir import:

```python
from src.tcf.campo import VectorFuncional, evaluar_campo, calcular_lentes
from src.tcf.detector_tcf import DetectorTCFResult
```

2. Extender `EvaluationResult`:

```python
@dataclass
class EvaluationResult:
    score: float
    scores_detalle: dict[str, float]
    issues: list[str]
    falacias: list[dict]
    should_relaunch: bool
    relaunch_suggestion: str | None = None
    # NUEVO: evaluación TCF post-ejecución
    tcf_mejora: dict | None = None   # {"toxicidad_delta": -0.05, "deps_resueltas": 1, ...}
```

3. Crear función `evaluar_mejora_campo()`:

```python
def evaluar_mejora_campo(
    tcf_pre: DetectorTCFResult | None,
    resultados: dict,
) -> dict | None:
    """Evalúa si el campo de gradientes mejoró post-ejecución.

    Heurístico: analiza los outputs del ejecutor para estimar
    qué funciones fueron "tocadas" y en qué dirección.

    Retorna dict con métricas de mejora o None si no hay TCF pre.
    """
    if not tcf_pre or not tcf_pre.estado_campo:
        return None

    estado_pre = tcf_pre.estado_campo
    mejora = {
        "eslabon_debil_pre": estado_pre.eslabon_debil,
        "toxicidad_pre": estado_pre.toxicidad_total,
        "deps_violadas_pre": len(estado_pre.dependencias_violadas),
        "estable_pre": estado_pre.estable,
        "arquetipo_pre": tcf_pre.scoring.primario.arquetipo if tcf_pre.scoring else None,
        # Post se calcula cuando haya vector post (Reactor v4)
        # Por ahora: estimación basada en cobertura de la receta
        "funciones_cubiertas": [],
        "receta_ejecutada": False,
    }

    # Verificar si la receta se ejecutó (las INTs prescritas fueron usadas)
    if tcf_pre.receta:
        ints_receta = set(tcf_pre.receta.ints)
        ints_ejecutadas = set()
        for key in resultados:
            # key suele ser "INT-XX_individual" o similar
            for int_id in ints_receta:
                if int_id in key:
                    ints_ejecutadas.add(int_id)

        cobertura_receta = len(ints_ejecutadas) / max(len(ints_receta), 1)
        mejora["receta_ejecutada"] = cobertura_receta > 0.5
        mejora["cobertura_receta"] = round(cobertura_receta, 2)
        mejora["funciones_cubiertas"] = tcf_pre.receta.secuencia

    return mejora
```

4. Modificar `evaluar()` para incluir TCF:

Cambiar la firma:

```python
def evaluar(
    plan: ExecutionPlan,
    algoritmo: Algoritmo,
    tcf_pre: DetectorTCFResult | None = None,
) -> EvaluationResult:
```

Al final, antes del return, añadir:

```python
    # Evaluación TCF
    tcf_mejora = evaluar_mejora_campo(tcf_pre, plan.results)

    # Si la receta no se ejecutó, penalizar
    if tcf_mejora and not tcf_mejora.get("receta_ejecutada", True):
        total_score -= 1.0
        issues.append("Receta TCF prescrita pero no ejecutada (cobertura < 50%)")

    return EvaluationResult(
        score=round(total_score, 1),
        scores_detalle={name: round(s, 1) for name, s in scores},
        issues=issues,
        falacias=falacias_detectadas,
        should_relaunch=should_relaunch,
        relaunch_suggestion="Añadir inteligencia complementaria o aumentar profundidad" if should_relaunch else None,
        tcf_mejora=tcf_mejora,
    )
```

5. En `orchestrator.py`, pasar TCF al evaluador:

Cambiar la llamada:

```python
    # CAPA 5: Evaluador (incluye detección de falacias v2 + TCF)
    log.info("pipeline_evaluador_start")
    evaluation = evaluar(execution, algoritmo, tcf_pre=huecos.tcf)
    log.info("pipeline_evaluador_done", score=evaluation.score,
             tcf_mejora=evaluation.tcf_mejora)
```

### Test

```python
# En tests/test_evaluador_tcf.py
"""Test que el evaluador integra TCF."""
import pytest
from src.tcf.campo import VectorFuncional
from src.tcf.detector_tcf import detectar_tcf
from src.pipeline.evaluador import evaluar_mejora_campo
from src.tcf.constantes import VECTOR_PILATES


class TestEvaluadorTCF:
    def test_sin_tcf_retorna_none(self):
        assert evaluar_mejora_campo(None, {}) is None

    def test_con_tcf_retorna_metricas(self):
        vector = VectorFuncional.from_dict(VECTOR_PILATES)
        tcf = detectar_tcf("Todo depende de mí", vector)
        resultado = evaluar_mejora_campo(tcf, {})
        assert resultado is not None
        assert "eslabon_debil_pre" in resultado
        assert "toxicidad_pre" in resultado

    def test_cobertura_receta_con_ints_ejecutadas(self):
        vector = VectorFuncional.from_dict(VECTOR_PILATES)
        tcf = detectar_tcf("Todo depende de mí", vector)
        # Simular que INT-02 y INT-17 se ejecutaron
        resultados = {
            "INT-02_individual": "algo",
            "INT-17_individual": "algo",
            "INT-16_individual": "algo",
        }
        resultado = evaluar_mejora_campo(tcf, resultados)
        assert resultado is not None
        assert resultado["cobertura_receta"] > 0
```

### Criterio Pass

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
python -m pytest tests/test_router_reglas.py tests/test_evaluador_tcf.py -v --tb=short
# Todos pasan
python -c "from src.pipeline.evaluador import evaluar; from src.pipeline.registrador import registrar_ejecucion; print('OK')"
# Sin errores
```

---

## SECUENCIA DE EJECUCIÓN COMPLETA

```
1. Parte 1: Modificar router.py + crear tests/test_router_reglas.py
   → pytest tests/test_router_reglas.py -v

2. Parte 2: Crear migrations/003_registrador.sql + src/pipeline/registrador.py
   → Modificar orchestrator.py para incluir registrador
   → python -c "from src.pipeline.registrador import registrar_ejecucion; print('OK')"

3. Parte 3: Modificar evaluador.py + crear tests/test_evaluador_tcf.py
   → Modificar orchestrator.py para pasar TCF al evaluador
   → pytest tests/test_evaluador_tcf.py -v

4. Verificación final:
   → pytest tests/ -v --tb=short (TODOS los tests)
   → python -c "from src.pipeline.orchestrator import run_pipeline; print('OK')"
```

---

## DECISIONES YA TOMADAS (NO re-abrir)

- Registrador es fire-and-forget (no bloquea pipeline si DB falla)
- Evaluador TCF es heurístico por ahora (vector post-ejecución real = Reactor v4)
- Reglas auto-corrigen donde pueden, loguean donde no
- La tabla `datapoints_efectividad` NO tiene FK estricta a `ejecuciones` (puede insertar sin ejecucion_id)
- `perfil_gradientes` guarda snapshot completo del campo pre/post

---

**FIN BRIEFING_TCF_07**
