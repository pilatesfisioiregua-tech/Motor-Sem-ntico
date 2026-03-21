# B-ACD-14: Métricas ACD en evaluador

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-13 ✅ (orchestrator pasa prescripción)
**Coste:** $0 (código puro, análisis de outputs existentes)

---

## CONTEXTO

El evaluador (capa 5) tiene `evaluar_mejora_campo()` que es heurístico. Con ACD, podemos medir precisamente si la intervención atacó lo que la prescripción mandó. Tres métricas nuevas:

1. **Cobertura prescriptiva:** ¿Se ejecutaron las INTs prescritas?
2. **Alineación P/R:** ¿Los outputs muestran evidencia de los Ps/Rs prescritos?
3. **Ataque a lente objetivo:** ¿La intervención tocó la lente que la prescripción identificó como faltante?

---

## PASO 1: Crear evaluador_acd.py

**Crear archivo:** `@project/src/tcf/evaluador_acd.py`

**Contenido EXACTO:**

```python
"""Evaluador ACD — métricas de efectividad de la prescripción.

Mide si la ejecución del pipeline respetó la prescripción.
Código puro, $0. No usa LLM — analiza outputs existentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.pipeline.ejecutor import ExecutionPlan
from src.tcf.prescriptor import Prescripcion
from src.meta_red import load_pensamientos, load_razonamientos


@dataclass
class MetricasACD:
    # Cobertura prescriptiva
    ints_prescritas: list[str]
    ints_ejecutadas: list[str]
    cobertura_ints: float          # 0.0 - 1.0

    # Alineación P/R
    ps_prescritos: list[str]
    ps_detectados: list[str]       # Ps cuya señal aparece en outputs
    rs_prescritos: list[str]
    rs_detectados: list[str]
    alineacion_pr: float           # 0.0 - 1.0

    # Ataque a lente objetivo
    lente_objetivo: str
    funciones_atacadas: list[str]  # Funciones mencionadas/atacadas en outputs
    lente_cubierta: bool           # ¿Se tocó la lente objetivo?

    # Prohibiciones
    prohibiciones_violadas: list[str]  # PRH-XX que la ejecución violó

    # Score compuesto
    score_acd: float               # 0.0 - 10.0

    # Detalle
    detalle: dict = field(default_factory=dict)


def evaluar_acd(
    plan: ExecutionPlan,
    prescripcion: Prescripcion,
) -> MetricasACD:
    """Evalúa qué tan bien la ejecución respetó la prescripción.

    Args:
        plan: ExecutionPlan del ejecutor (outputs reales).
        prescripcion: Prescripcion del prescriptor (lo que se debía hacer).

    Returns:
        MetricasACD con scores y detalle.
    """
    # --- 1. Cobertura prescriptiva ---
    ints_prescritas = set(prescripcion.ints)
    ints_ejecutadas = set()
    for key in plan.results:
        for int_id in ints_prescritas:
            if int_id in key:
                ints_ejecutadas.add(int_id)
    cobertura = len(ints_ejecutadas) / max(len(ints_prescritas), 1)

    # --- 2. Alineación P/R ---
    ps_detectados = _detectar_ps_en_outputs(plan, prescripcion.ps)
    rs_detectados = _detectar_rs_en_outputs(plan, prescripcion.rs)

    total_pr = len(prescripcion.ps) + len(prescripcion.rs)
    detectados_pr = len(ps_detectados) + len(rs_detectados)
    alineacion = detectados_pr / max(total_pr, 1)

    # --- 3. Ataque a lente objetivo ---
    funciones_atacadas = _detectar_funciones_en_outputs(plan)
    lente_cubierta = _lente_tocada(
        prescripcion.lente_objetivo,
        funciones_atacadas,
        plan,
    )

    # --- 4. Prohibiciones ---
    # Las prohibiciones ya están en prescripcion.prohibiciones_violadas
    # Aquí solo las reportamos
    prohibiciones = [p.codigo for p in prescripcion.prohibiciones_violadas]

    # --- 5. Score compuesto ---
    score = (
        cobertura * 4.0 +           # 40% cobertura INTs
        alineacion * 3.0 +          # 30% alineación P/R
        (1.0 if lente_cubierta else 0.0) * 2.0 +  # 20% lente
        (1.0 if not prohibiciones else 0.0) * 1.0  # 10% sin prohibiciones
    )

    return MetricasACD(
        ints_prescritas=list(ints_prescritas),
        ints_ejecutadas=list(ints_ejecutadas),
        cobertura_ints=round(cobertura, 3),
        ps_prescritos=prescripcion.ps,
        ps_detectados=ps_detectados,
        rs_prescritos=prescripcion.rs,
        rs_detectados=rs_detectados,
        alineacion_pr=round(alineacion, 3),
        lente_objetivo=prescripcion.lente_objetivo,
        funciones_atacadas=funciones_atacadas,
        lente_cubierta=lente_cubierta,
        prohibiciones_violadas=prohibiciones,
        score_acd=round(score, 1),
        detalle={
            "cobertura_raw": round(cobertura, 3),
            "alineacion_raw": round(alineacion, 3),
            "lente_raw": 1.0 if lente_cubierta else 0.0,
            "prohibiciones_raw": 0.0 if prohibiciones else 1.0,
        },
    )


def _detectar_ps_en_outputs(
    plan: ExecutionPlan,
    ps_prescritos: list[str],
) -> list[str]:
    """Detecta señales de Ps prescritos en los outputs del ejecutor.

    Usa la pregunta_activadora de cada P como señal de detección.
    No busca mención literal del ID — busca evidencia funcional.
    """
    ps_data = load_pensamientos()
    detectados = []

    # Concatenar todos los outputs en un solo texto (lowercase)
    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )

    for pid in ps_prescritos:
        p = ps_data.get(pid, {})
        # Señales: palabras clave de la descripción y nombre
        nombre = p.get("nombre", "").lower()
        keywords = _extraer_keywords(p.get("descripcion", ""))

        # Detectar si al menos 2 keywords aparecen en outputs
        hits = sum(1 for kw in keywords if kw in all_text)
        if hits >= 2 or nombre in all_text:
            detectados.append(pid)

    return detectados


def _detectar_rs_en_outputs(
    plan: ExecutionPlan,
    rs_prescritos: list[str],
) -> list[str]:
    """Detecta señales de Rs prescritos en los outputs."""
    rs_data = load_razonamientos()
    detectados = []

    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )

    for rid in rs_prescritos:
        r = rs_data.get(rid, {})
        nombre = r.get("nombre", "").lower()
        keywords = _extraer_keywords(r.get("descripcion", ""))

        hits = sum(1 for kw in keywords if kw in all_text)
        if hits >= 2 or nombre in all_text:
            detectados.append(rid)

    return detectados


def _extraer_keywords(texto: str) -> list[str]:
    """Extrae keywords significativas de un texto (>4 chars, no stopwords)."""
    stopwords = {
        "para", "como", "pero", "este", "esta", "todo", "cada",
        "donde", "cuando", "entre", "desde", "hasta", "sobre",
        "tiene", "puede", "debe", "hace", "algo", "otro", "otra",
        "forma", "modo", "tipo", "parte",
    }
    words = texto.lower().split()
    return [w.strip(".,;:()") for w in words
            if len(w) > 4 and w.strip(".,;:()") not in stopwords][:8]


def _detectar_funciones_en_outputs(plan: ExecutionPlan) -> list[str]:
    """Detecta qué funciones F1-F7 se mencionan/atacan en outputs."""
    funciones_map = {
        "f1": "F1", "conservar": "F1", "conservación": "F1",
        "f2": "F2", "captar": "F2", "captación": "F2",
        "f3": "F3", "depurar": "F3", "depuración": "F3",
        "f4": "F4", "distribuir": "F4", "distribución": "F4",
        "f5": "F5", "frontera": "F5", "identidad": "F5",
        "f6": "F6", "adaptar": "F6", "adaptación": "F6",
        "f7": "F7", "replicar": "F7", "replicación": "F7",
    }
    detectadas = set()

    for r in plan.results.values():
        if not r.output_raw:
            continue
        text = r.output_raw.lower()
        for keyword, fi in funciones_map.items():
            if keyword in text:
                detectadas.add(fi)

    return sorted(detectadas)


def _lente_tocada(
    lente_objetivo: str,
    funciones_atacadas: list[str],
    plan: ExecutionPlan,
) -> bool:
    """Verifica si la lente objetivo fue tocada por la intervención.

    Heurístico: la lente se considera tocada si:
    - Se mencionan funciones asociadas a esa lente, O
    - Aparecen keywords de la lente en outputs
    """
    # Funciones fuertemente asociadas a cada lente
    lente_funciones = {
        "salud": {"F1", "F2", "F4"},
        "sentido": {"F3", "F5", "F6"},
        "continuidad": {"F7", "F6", "F5"},
    }

    funcs_lente = lente_funciones.get(lente_objetivo, set())
    if funcs_lente.intersection(funciones_atacadas):
        return True

    # Fallback: keywords de lente en texto
    keywords_lente = {
        "salud": ["operativ", "ejecución", "recurso", "eficiencia", "funcionamiento"],
        "sentido": ["propósito", "significado", "cuestionar", "por qué", "sentido"],
        "continuidad": ["escalar", "replicar", "transmitir", "legado", "transferir"],
    }

    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )
    kws = keywords_lente.get(lente_objetivo, [])
    hits = sum(1 for kw in kws if kw in all_text)
    return hits >= 2
```

---

## PASO 2: Integrar en evaluador.py

**Archivo:** `@project/src/pipeline/evaluador.py` (ya existe)

**Leer primero.** Luego:

1. Añadir import al inicio:
```python
from src.tcf.evaluador_acd import evaluar_acd, MetricasACD
from src.tcf.prescriptor import Prescripcion
```

2. Extender `evaluar()` para aceptar prescripción:

**ANTES:**
```python
def evaluar(
    plan: ExecutionPlan,
    algoritmo: Algoritmo,
    tcf_pre: DetectorTCFResult | None = None,
) -> EvaluationResult:
```

**DESPUÉS:**
```python
def evaluar(
    plan: ExecutionPlan,
    algoritmo: Algoritmo,
    tcf_pre: DetectorTCFResult | None = None,
    prescripcion: Prescripcion | None = None,
) -> EvaluationResult:
```

3. Añadir campo `metricas_acd` a `EvaluationResult`:

```python
@dataclass
class EvaluationResult:
    score: float
    scores_detalle: dict[str, float]
    issues: list[str]
    falacias: list[dict]
    should_relaunch: bool
    relaunch_suggestion: str | None = None
    tcf_mejora: dict | None = None
    metricas_acd: MetricasACD | None = None
```

4. Al final de `evaluar()`, ANTES del return, añadir:

```python
    # Evaluar ACD si hay prescripción
    metricas_acd = None
    if prescripcion:
        metricas_acd = evaluar_acd(plan, prescripcion)
        # Ponderar score ACD en score final (20% del total)
        score_acd_norm = metricas_acd.score_acd / 10.0  # normalizar a 0-1
        total_score = total_score * 0.80 + score_acd_norm * 10.0 * 0.20
        if metricas_acd.cobertura_ints < 0.5:
            issues.append(
                f"ACD: Solo {len(metricas_acd.ints_ejecutadas)}/{len(metricas_acd.ints_prescritas)} "
                "INTs prescritas ejecutadas"
            )
        if metricas_acd.prohibiciones_violadas:
            issues.append(
                f"ACD: Prohibiciones activas: {metricas_acd.prohibiciones_violadas}"
            )
```

Y en el return, añadir `metricas_acd=metricas_acd`.

---

## PASO 3: Pasar prescripción desde orchestrator a evaluador

**Archivo:** `@project/src/pipeline/orchestrator.py`

**Modificar la llamada a `evaluar()`:**

**ANTES:**
```python
    evaluation = evaluar(execution, algoritmo, tcf_pre=huecos.tcf)
```

**DESPUÉS:**
```python
    evaluation = evaluar(execution, algoritmo, tcf_pre=huecos.tcf, prescripcion=prescripcion)
```

---

## PASO 4: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
from src.tcf.evaluador_acd import evaluar_acd, MetricasACD, _extraer_keywords
from src.tcf.prescriptor import Prescripcion
from src.tcf.nivel_logico import NivelModo
from src.pipeline.ejecutor import ExecutionPlan, ExecutionResult

# Mock ExecutionPlan con outputs sintéticos
plan = ExecutionPlan()
plan.results = {
    'INT-17': ExecutionResult(
        intel_id='INT-17', operacion_tipo='individual',
        output_raw='Análisis existencial: el propósito del estudio no está definido. '
                   'Falta cuestionamiento profundo sobre el sentido del negocio. '
                   'La frontera de identidad es clara pero la depuración es nula.',
        output_json=None, modelo_usado='test', input_tokens=0,
        output_tokens=0, coste_usd=0, tiempo_s=0,
    ),
    'INT-08': ExecutionResult(
        intel_id='INT-08', operacion_tipo='individual',
        output_raw='El tejido social es débil. Los clientes se conectan con María, no con la marca. '
                   'Necesita construir comunidad y sistematizar la transferencia de relaciones.',
        output_json=None, modelo_usado='test', input_tokens=0,
        output_tokens=0, coste_usd=0, tiempo_s=0,
    ),
}

# Mock Prescripcion
presc = Prescripcion(
    ints=['INT-17', 'INT-08', 'INT-12'],
    ints_refuerzo=['INT-17', 'INT-08', 'INT-12'],
    ps=['P05', 'P03'],
    rs=['R03', 'R09'],
    secuencia=['F5', 'F3', 'F7'],
    frenar=[],
    parar_primero=False,
    lente_objetivo='sentido',
    nivel_logico=NivelModo(lente='sentido', niveles=[3,4,5], modos=['ENMARCAR','PERCIBIR'], descripcion='test'),
    objetivo='CUESTIONAR premisas',
    prohibiciones_violadas=[],
    advertencias_ic=[],
    arquetipo_base='maquina_sin_alma',
    estado_id='operador_ciego',
)

metricas = evaluar_acd(plan, presc)

# Test 1: Cobertura INTs
assert metricas.cobertura_ints > 0, 'Debería detectar INTs ejecutadas'
print(f'PASS 1: Cobertura INTs = {metricas.cobertura_ints} ({metricas.ints_ejecutadas})')

# Test 2: Score ACD
assert 0 <= metricas.score_acd <= 10, f'Score fuera de rango: {metricas.score_acd}'
print(f'PASS 2: Score ACD = {metricas.score_acd}')

# Test 3: Lente cubierta
print(f'PASS 3: Lente cubierta = {metricas.lente_cubierta} (funciones: {metricas.funciones_atacadas})')

# Test 4: Alineación P/R
print(f'PASS 4: Alineación P/R = {metricas.alineacion_pr} (Ps={metricas.ps_detectados}, Rs={metricas.rs_detectados})')

# Test 5: Keywords
kws = _extraer_keywords('Busca soluciones fuera del marco habitual moviendo lateralmente')
assert len(kws) > 0
print(f'PASS 5: Keywords extraídas: {kws}')

# Test 6: Sin prohibiciones
assert metricas.prohibiciones_violadas == []
print('PASS 6: Sin prohibiciones violadas')

print(f'\\n=== METRICAS ACD ===')
print(f'Score: {metricas.score_acd}/10')
print(f'Cobertura INTs: {metricas.cobertura_ints}')
print(f'Alineación P/R: {metricas.alineacion_pr}')
print(f'Lente cubierta: {metricas.lente_cubierta}')
print(f'Funciones atacadas: {metricas.funciones_atacadas}')

print('\\nTODOS LOS TESTS PASAN (6/6)')
"
```

**CRITERIO PASS:**
1. Cobertura INTs > 0 (detecta INTs ejecutadas)
2. Score ACD en rango [0, 10]
3. Lente cubierta reportada
4. Alineación P/R reportada
5. Keywords se extraen
6. Sin prohibiciones = score no penalizado

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/tcf/evaluador_acd.py` | CREAR (nuevo) |
| `src/pipeline/evaluador.py` | EDITAR — añadir import, campo metricas_acd, llamar evaluar_acd |
| `src/pipeline/orchestrator.py` | EDITAR — pasar prescripcion a evaluar() |

## NOTAS

- Todo código puro, $0 — analiza outputs existentes sin LLM adicional
- Detección de P/R en outputs es heurística (keywords). Fase futura podría usar LLM para clasificación semántica.
- Las funciones_atacadas detectan menciones de F1-F7 en texto. Complementa la cobertura de INTs.
- Score compuesto: 40% cobertura INTs + 30% alineación P/R + 20% lente + 10% sin prohibiciones
- Backward compatible: si no hay prescripcion, metricas_acd=None y score no cambia
