"""Capa 5: Scorer heurístico + detección de falacias."""
from dataclasses import dataclass, field

from src.pipeline.ejecutor import ExecutionPlan
from src.pipeline.compositor import Algoritmo


@dataclass
class EvaluationResult:
    score: float  # 0-10
    scores_detalle: dict[str, float]
    issues: list[str]
    falacias: list[dict]
    should_relaunch: bool
    relaunch_suggestion: str | None = None


def evaluar(plan: ExecutionPlan, algoritmo: Algoritmo) -> EvaluationResult:
    """Scorer heurístico. Devuelve score 0-10 y recomendaciones."""
    scores: list[tuple[str, float]] = []
    issues: list[str] = []

    # 1. Cobertura: ¿Se ejecutaron todas las operaciones planeadas?
    planned = len(algoritmo.operaciones)
    executed = len([r for r in plan.results.values() if r.operacion_tipo != 'loop'])
    coverage = executed / max(planned, 1)
    scores.append(('cobertura', coverage * 10))
    if coverage < 0.8:
        issues.append(f"Solo {executed}/{planned} operaciones ejecutadas")

    # 2. JSON parseables: ¿Los outputs tienen estructura?
    total_results = len(plan.results)
    json_ok = len([r for r in plan.results.values() if r.output_json])
    structure = json_ok / max(total_results, 1)
    scores.append(('estructura', structure * 10))
    if structure < 0.5:
        issues.append("Más de 50% de outputs sin JSON parseable")

    # 3. Hallazgos: ¿Hay hallazgos no triviales?
    hallazgos_count = 0
    for r in plan.results.values():
        if r.output_json:
            h = r.output_json.get('hallazgos', [])
            hallazgos_count += len(h)
    hallazgos_score = min(hallazgos_count / (len(algoritmo.inteligencias) * 2), 1.0)
    scores.append(('hallazgos', hallazgos_score * 10))
    if hallazgos_count < 3:
        issues.append(f"Solo {hallazgos_count} hallazgos (mínimo esperado: {len(algoritmo.inteligencias) * 2})")

    # 4. Emergencia: ¿Las composiciones/fusiones produjeron hallazgos emergentes?
    emergentes = 0
    for r in plan.results.values():
        if r.output_json and r.operacion_tipo in ('composicion', 'fusion'):
            if r.output_json.get('hallazgo_emergente') or r.output_json.get('emergente'):
                emergentes += 1
    comp_fus = len([o for o in algoritmo.operaciones if o.tipo in ('composicion', 'fusion')])
    emergencia = emergentes / max(comp_fus, 1) if comp_fus > 0 else 1.0
    scores.append(('emergencia', emergencia * 10))

    # 5. Loop quality: ¿Los loops encontraron algo nuevo?
    loops = [r for r in plan.results.values() if r.operacion_tipo == 'loop']
    if loops:
        loops_with_new = len([l for l in loops if l.output_json and
                              l.output_json.get('hallazgos_nuevos')])
        loop_score = loops_with_new / len(loops)
        scores.append(('loops', loop_score * 10))

    # 6. Coste efficiency
    if plan.total_cost > 0:
        cost_per_hallazgo = plan.total_cost / max(hallazgos_count, 1)
        cost_score = max(0, 10 - cost_per_hallazgo * 20)
        scores.append(('eficiencia', cost_score))

    # 7. Detección de falacias aritméticas en los outputs
    falacias_detectadas = detectar_falacias(plan)
    if falacias_detectadas:
        falacia_penalty = min(len(falacias_detectadas) * 0.5, 3.0)
        scores.append(('falacias', max(0, 10 - falacia_penalty)))

    # Score final (media ponderada)
    weights = {
        'cobertura': 0.20,
        'estructura': 0.15,
        'hallazgos': 0.25,
        'emergencia': 0.20,
        'loops': 0.10,
        'eficiencia': 0.10,
    }

    total_score = sum(
        score * weights.get(name, 0.1)
        for name, score in scores
    )

    should_relaunch = total_score < 6.0

    return EvaluationResult(
        score=round(total_score, 1),
        scores_detalle={name: round(s, 1) for name, s in scores},
        issues=issues,
        falacias=falacias_detectadas,
        should_relaunch=should_relaunch,
        relaunch_suggestion="Añadir inteligencia complementaria o aumentar profundidad" if should_relaunch else None,
    )


def detectar_falacias(plan: ExecutionPlan) -> list[dict]:
    """Detecta falacias aritméticas en los outputs del ejecutor."""
    falacias: list[dict] = []

    for key, result in plan.results.items():
        if not result.output_raw:
            continue
        text = result.output_raw.lower()

        # conducta_valor / cualidad_como_funcion
        if 'es innovador' in text or 'es líder' in text or 'es emprendedor' in text:
            if 'innova' not in text and 'lidera' not in text:
                falacias.append({
                    'tipo': 'cualidad_como_funcion',
                    'fuente': key,
                    'fragmento': 'Atribuye cualidad sin verificar función',
                })

        # optimizacion_sin_finalidad
        if 'optimizar' in text or 'mejorar' in text or 'escalar' in text:
            if 'para' not in text and 'objetivo' not in text and 'fin' not in text:
                falacias.append({
                    'tipo': 'optimizacion_sin_finalidad',
                    'fuente': key,
                    'fragmento': 'Optimización sin finalidad explícita',
                })

        # verbo_sin_objeto
        for verbo in ['lidera', 'gestiona', 'dirige']:
            if verbo in text:
                idx = text.index(verbo)
                after = text[idx + len(verbo):idx + len(verbo) + 20].strip()
                if not after or after[0] in '.!?,;':
                    falacias.append({
                        'tipo': 'verbo_sin_objeto',
                        'fuente': key,
                        'fragmento': f'"{verbo}" sin objeto definido',
                    })

    return falacias
