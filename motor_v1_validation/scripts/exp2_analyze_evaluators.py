"""Exp 2: Enjambre de Evaluadores OS — Análisis.
Compara evaluaciones de N modelos OS contra la referencia Sonnet.
Genera rankings, complementariedad, asignación de roles, y reports.
"""
import json
import math
from collections import defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

import numpy as np
from scipy import stats

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
DATA_DIR = BASE_DIR / "data" / "evaluator_test_set"

ALL_CELLS = [
    f"{l}×{f}"
    for l in ["Salud", "Sentido", "Continuidad"]
    for f in ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
]

LENTES = {"Salud": [], "Sentido": [], "Continuidad": []}
for cell in ALL_CELLS:
    lente = cell.split("×")[0]
    LENTES[lente].append(cell)

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]
OUTPUT_TYPES = {
    "v31_best": "best",
    "70b_worst": "worst",
    "maverick_medium": "medium",
    "gptoss_depurar": "best",
    "qwen3t_medium": "medium",
}

# Approximate costs per eval (input ~1.5K tok + output ~1K tok)
COST_PER_EVAL = {
    "deepseek-r1": 0.012,      # $3+$7 per M
    "deepseek-v3.1": 0.003,    # $0.60+$1.70
    "v3.2-chat": 0.0015,       # $0.27+$1.10
    "v3.2-reasoner": 0.004,    # $0.55+$2.19
    "cogito-671b": 0.003,      # $1.25+$1.25
    "gpt-oss-120b": 0.001,     # $0.15+$0.60
    "qwen3-235b": 0.002,
    "minimax-m1": 0.002,
    "minimax-m2.5": 0.002,
    "kimi-k2.5": 0.005,        # $0.50+$2.80
    "glm-4.7": 0.003,          # $0.45+$2.00
}


def load_data():
    with open(RESULTS_DIR / "exp2_all_evaluator_results.json", encoding="utf-8") as f:
        evaluator_results = json.load(f)
    with open(DATA_DIR / "sonnet_reference_evals.json", encoding="utf-8") as f:
        sonnet_ref = json.load(f)
    return evaluator_results, sonnet_ref


def extract_levels(celdas):
    """Extract ordered list of 21 levels from celdas dict."""
    return [celdas.get(cell, {}).get("nivel", 0) for cell in ALL_CELLS]


def get_sonnet_vectors(sonnet_ref):
    """Get {output_id: [21 levels]} from Sonnet reference."""
    vectors = {}
    for output_id in OUTPUT_IDS:
        if output_id in sonnet_ref:
            result = sonnet_ref[output_id].get("result", {})
            celdas = result.get("celdas", {})
            vectors[output_id] = extract_levels(celdas)
    return vectors


def get_model_vectors(results, model_name):
    """Get {output_id: [21 levels]} for a model."""
    vectors = {}
    model_data = results.get("results", {}).get(model_name, {})
    for output_id in OUTPUT_IDS:
        if output_id in model_data and "error" not in model_data[output_id]:
            celdas = model_data[output_id].get("celdas", {})
            vectors[output_id] = extract_levels(celdas)
    return vectors


def compute_metrics(sonnet_vecs, model_vecs):
    """Compute all metrics comparing model vs Sonnet."""
    # Build aligned arrays
    s_all, m_all = [], []
    s_by_lente = defaultdict(list)
    m_by_lente = defaultdict(list)
    s_by_type = defaultdict(list)
    m_by_type = defaultdict(list)

    for output_id in OUTPUT_IDS:
        if output_id not in sonnet_vecs or output_id not in model_vecs:
            continue
        s_vec = sonnet_vecs[output_id]
        m_vec = model_vecs[output_id]
        s_all.extend(s_vec)
        m_all.extend(m_vec)

        out_type = OUTPUT_TYPES[output_id]
        s_by_type[out_type].extend(s_vec)
        m_by_type[out_type].extend(m_vec)

        for i, cell in enumerate(ALL_CELLS):
            lente = cell.split("×")[0]
            s_by_lente[lente].append(s_vec[i])
            m_by_lente[lente].append(m_vec[i])

    if len(s_all) < 10:
        return {"error": f"Too few datapoints: {len(s_all)}"}

    s_arr = np.array(s_all, dtype=float)
    m_arr = np.array(m_all, dtype=float)

    # Global metrics
    spearman_r, spearman_p = stats.spearmanr(s_arr, m_arr)
    pearson_r, pearson_p = stats.pearsonr(s_arr, m_arr)
    mae = float(np.mean(np.abs(s_arr - m_arr)))
    bias = float(np.mean(m_arr - s_arr))
    exact_match = float(np.mean(s_arr == m_arr))

    # F1 for level >= 3
    s_high = s_arr >= 3
    m_high = m_arr >= 3
    tp = int(np.sum(s_high & m_high))
    fp = int(np.sum(~s_high & m_high))
    fn = int(np.sum(s_high & ~m_high))
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1_3plus = 2 * precision * recall / max(precision + recall, 1e-9)

    # Spearman by lente
    sp_by_lente = {}
    for lente in ["Salud", "Sentido", "Continuidad"]:
        if len(s_by_lente[lente]) >= 5:
            r, _ = stats.spearmanr(s_by_lente[lente], m_by_lente[lente])
            sp_by_lente[lente] = round(r, 3) if not math.isnan(r) else 0.0
        else:
            sp_by_lente[lente] = None

    # Spearman by output type
    sp_by_type = {}
    for otype in set(OUTPUT_TYPES.values()):
        if len(s_by_type[otype]) >= 5:
            r, _ = stats.spearmanr(s_by_type[otype], m_by_type[otype])
            sp_by_type[otype] = round(r, 3) if not math.isnan(r) else 0.0
        else:
            sp_by_type[otype] = None

    # Difference distribution
    diffs = (m_arr - s_arr).astype(int)
    diff_dist = {}
    for d in range(-4, 5):
        diff_dist[str(d)] = int(np.sum(diffs == d))

    return {
        "n_datapoints": len(s_all),
        "spearman": round(float(spearman_r), 4),
        "spearman_p": round(float(spearman_p), 6),
        "pearson": round(float(pearson_r), 4),
        "pearson_p": round(float(pearson_p), 6),
        "mae": round(mae, 3),
        "bias": round(bias, 3),
        "exact_match_pct": round(exact_match * 100, 1),
        "f1_3plus": round(f1_3plus, 3),
        "precision_3plus": round(precision, 3),
        "recall_3plus": round(recall, 3),
        "tp_3plus": tp,
        "fp_3plus": fp,
        "fn_3plus": fn,
        "spearman_by_lente": sp_by_lente,
        "spearman_by_type": sp_by_type,
        "diff_distribution": diff_dist,
    }


def compute_complementarity(sonnet_vecs, all_model_vecs):
    """Find model pairs whose fusion (max of both) improves Spearman."""
    models = list(all_model_vecs.keys())
    results = []

    # Get flat Sonnet vector
    s_flat = []
    for oid in OUTPUT_IDS:
        if oid in sonnet_vecs:
            s_flat.extend(sonnet_vecs[oid])
    s_arr = np.array(s_flat, dtype=float)

    # Individual Spearmans
    individual = {}
    for m in models:
        m_flat = []
        valid = True
        for oid in OUTPUT_IDS:
            if oid in all_model_vecs[m]:
                m_flat.extend(all_model_vecs[m][oid])
            else:
                valid = False
                break
        if valid and len(m_flat) == len(s_flat):
            r, _ = stats.spearmanr(s_arr, np.array(m_flat, dtype=float))
            individual[m] = r

    # Pairwise fusion
    for m1, m2 in combinations(models, 2):
        if m1 not in individual or m2 not in individual:
            continue
        fused = []
        valid = True
        for oid in OUTPUT_IDS:
            if oid in all_model_vecs[m1] and oid in all_model_vecs[m2]:
                v1 = all_model_vecs[m1][oid]
                v2 = all_model_vecs[m2][oid]
                fused.extend([max(a, b) for a, b in zip(v1, v2)])
            else:
                valid = False
                break
        if not valid or len(fused) != len(s_flat):
            continue

        r_fused, _ = stats.spearmanr(s_arr, np.array(fused, dtype=float))
        best_individual = max(individual[m1], individual[m2])
        improvement = r_fused - best_individual

        results.append({
            "pair": f"{m1} + {m2}",
            "spearman_fused": round(float(r_fused), 4),
            "best_individual": round(float(best_individual), 4),
            "improvement": round(float(improvement), 4),
        })

    results.sort(key=lambda x: x["spearman_fused"], reverse=True)
    return results[:15]  # Top 15 pairs


def assign_roles(metrics_by_model, all_model_vecs):
    """Assign evaluator roles based on metrics."""
    roles = {}

    # Evaluador general: highest Spearman
    best_sp = sorted(metrics_by_model.items(), key=lambda x: x[1].get("spearman", 0), reverse=True)
    if best_sp:
        roles["evaluador_general"] = {"model": best_sp[0][0], "spearman": best_sp[0][1].get("spearman", 0)}

    # Evaluador de insights: highest F1(3+)
    best_f1 = sorted(metrics_by_model.items(), key=lambda x: x[1].get("f1_3plus", 0), reverse=True)
    if best_f1:
        roles["evaluador_insights"] = {"model": best_f1[0][0], "f1_3plus": best_f1[0][1].get("f1_3plus", 0)}

    # Evaluador rápido: fastest with Spearman > 0.80
    fast_candidates = []
    for m, met in metrics_by_model.items():
        if met.get("spearman", 0) > 0.80 and "avg_time_s" in met:
            fast_candidates.append((m, met["avg_time_s"]))
    fast_candidates.sort(key=lambda x: x[1])
    if fast_candidates:
        roles["evaluador_rapido"] = {"model": fast_candidates[0][0], "avg_time_s": fast_candidates[0][1]}

    # Evaluador de Sentido: highest Spearman on Sentido lens
    best_sentido = sorted(
        metrics_by_model.items(),
        key=lambda x: x[1].get("spearman_by_lente", {}).get("Sentido", 0) or 0,
        reverse=True,
    )
    if best_sentido:
        sp_s = best_sentido[0][1].get("spearman_by_lente", {}).get("Sentido", 0)
        roles["evaluador_sentido"] = {"model": best_sentido[0][0], "spearman_sentido": sp_s}

    # Pre-filtro barato: Spearman > 0.70 and cost < $0.005/eval
    for m, met in metrics_by_model.items():
        cost = COST_PER_EVAL.get(m, 0.01)
        if met.get("spearman", 0) > 0.70 and cost < 0.005:
            roles["prefiltro_barato"] = {"model": m, "spearman": met["spearman"], "cost": cost}
            break

    return roles


def generate_md_report(metrics_by_model, complementarity, roles):
    """Generate markdown report."""
    lines = []
    lines.append("# EXP 2 — ENJAMBRE DE EVALUADORES OS")
    lines.append("")
    lines.append(f"Fecha: {date.today()}")
    lines.append(f"Referencia: Claude Sonnet (105 datapoints, 5 outputs × 21 celdas)")
    lines.append("")

    # ── Ranking Table ──
    lines.append("## Ranking Global de Evaluadores")
    lines.append("")
    lines.append("| # | Modelo | Spearman | Pearson | MAE | Bias | F1(3+) | Exact% | Tiempo | Coste |")
    lines.append("|---|--------|----------|---------|-----|------|--------|--------|--------|-------|")

    ranked = sorted(metrics_by_model.items(), key=lambda x: x[1].get("spearman", 0), reverse=True)
    for i, (m, met) in enumerate(ranked):
        if "error" in met:
            lines.append(f"| {i+1} | {m} | ERROR | — | — | — | — | — | — | — |")
            continue
        cost = COST_PER_EVAL.get(m, "?")
        cost_str = f"${cost:.4f}" if isinstance(cost, float) else str(cost)
        avg_t = met.get("avg_time_s", "?")
        avg_t_str = f"{avg_t:.1f}s" if isinstance(avg_t, float) else str(avg_t)
        bias_str = f"{met['bias']:+.2f}"
        lines.append(
            f"| {i+1} | {m} | {met['spearman']:.3f} | {met['pearson']:.3f} | "
            f"{met['mae']:.2f} | {bias_str} | {met['f1_3plus']:.3f} | "
            f"{met['exact_match_pct']:.0f}% | {avg_t_str} | {cost_str} |"
        )
    lines.append("")

    # ── Per-Lente Table ──
    lines.append("## Spearman por Lente")
    lines.append("")
    lines.append("| # | Modelo | Sp Salud | Sp Sentido | Sp Continuidad |")
    lines.append("|---|--------|----------|------------|----------------|")
    for i, (m, met) in enumerate(ranked):
        if "error" in met:
            continue
        sp_l = met.get("spearman_by_lente", {})
        s_sal = sp_l.get("Salud", "—")
        s_sen = sp_l.get("Sentido", "—")
        s_con = sp_l.get("Continuidad", "—")
        fmt = lambda v: f"{v:.3f}" if isinstance(v, (int, float)) and v is not None else "—"
        lines.append(f"| {i+1} | {m} | {fmt(s_sal)} | {fmt(s_sen)} | {fmt(s_con)} |")
    lines.append("")

    # ── Spearman by Output Type ──
    lines.append("## Spearman por Tipo de Output")
    lines.append("")
    lines.append("| # | Modelo | Best | Medium | Worst |")
    lines.append("|---|--------|------|--------|-------|")
    for i, (m, met) in enumerate(ranked):
        if "error" in met:
            continue
        sp_t = met.get("spearman_by_type", {})
        fmt = lambda v: f"{v:.3f}" if isinstance(v, (int, float)) and v is not None else "—"
        lines.append(f"| {i+1} | {m} | {fmt(sp_t.get('best'))} | {fmt(sp_t.get('medium'))} | {fmt(sp_t.get('worst'))} |")
    lines.append("")

    # ── Complementarity ──
    lines.append("## Complementariedad (Top 10 pares)")
    lines.append("")
    lines.append("| Par | Sp Fusión | Mejor Individual | Mejora |")
    lines.append("|-----|-----------|-----------------|--------|")
    for comp in complementarity[:10]:
        imp_str = f"{comp['improvement']:+.4f}"
        lines.append(f"| {comp['pair']} | {comp['spearman_fused']:.4f} | {comp['best_individual']:.4f} | {imp_str} |")
    lines.append("")

    # ── Role Assignment ──
    lines.append("## Asignación Modelo → Rol Evaluador")
    lines.append("")
    lines.append("| Rol | Modelo | Métrica clave |")
    lines.append("|-----|--------|---------------|")
    for role_name, role_data in roles.items():
        model = role_data.get("model", "—")
        # Format key metric
        metric_parts = [f"{k}={v}" for k, v in role_data.items() if k != "model"]
        metric_str = ", ".join(metric_parts)
        lines.append(f"| {role_name} | {model} | {metric_str} |")
    lines.append("")

    # ── Diff Distribution ──
    lines.append("## Distribución de Diferencias (modelo - Sonnet)")
    lines.append("")
    lines.append("| Modelo | -3/-2 | -1 | 0 | +1 | +2/+3 |")
    lines.append("|--------|-------|----|---|----|----|")
    for m, met in ranked:
        if "error" in met:
            continue
        dd = met.get("diff_distribution", {})
        neg_big = sum(dd.get(str(d), 0) for d in [-4, -3, -2])
        neg_1 = dd.get("-1", 0)
        zero = dd.get("0", 0)
        pos_1 = dd.get("1", 0)
        pos_big = sum(dd.get(str(d), 0) for d in [2, 3, 4])
        lines.append(f"| {m} | {neg_big} | {neg_1} | {zero} | {pos_1} | {pos_big} |")
    lines.append("")

    # ── Veredicto ──
    lines.append("## Veredicto")
    lines.append("")

    best_model = ranked[0][0] if ranked else "—"
    best_sp = ranked[0][1].get("spearman", 0) if ranked else 0

    if best_sp >= 0.85:
        lines.append(f"**Evaluador OS aprobado.** {best_model} alcanza Spearman {best_sp:.3f} ≥ 0.85.")
        lines.append("Ahorro estimado: ~60× vs Sonnet por evaluación.")
    elif best_sp >= 0.75:
        lines.append(f"**Evaluador OS parcial.** Mejor modelo ({best_model}, Sp={best_sp:.3f}) no alcanza 0.85.")
        lines.append("Recomendación: pre-filtro OS + Sonnet para discrepancias.")
    else:
        lines.append(f"**Evaluador OS insuficiente.** Mejor Spearman={best_sp:.3f}. Sonnet necesario.")

    # Check complementarity
    if complementarity and complementarity[0]["spearman_fused"] >= 0.90:
        top = complementarity[0]
        lines.append(f"\n**Enjambre viable:** {top['pair']} alcanza Sp={top['spearman_fused']:.3f} ≥ 0.90.")

    # Check Sentido
    best_sentido = max(
        [(m, met.get("spearman_by_lente", {}).get("Sentido", 0)) for m, met in ranked if "error" not in met],
        key=lambda x: x[1] or 0,
        default=("—", 0),
    )
    if best_sentido[1] and best_sentido[1] >= 0.80:
        lines.append(f"\n**Sentido cubierto:** {best_sentido[0]} alcanza Sp Sentido={best_sentido[1]:.3f}.")
    else:
        lines.append(f"\n**Sentido débil:** mejor Sp Sentido={best_sentido[1]:.3f} < 0.80. Sonnet necesario para Sentido.")

    # Check F1(3+)
    best_f1 = max(
        [(m, met.get("f1_3plus", 0)) for m, met in ranked if "error" not in met],
        key=lambda x: x[1],
        default=("—", 0),
    )
    if best_f1[1] >= 0.60:
        lines.append(f"\n**Detección de insights OK:** {best_f1[0]} alcanza F1(3+)={best_f1[1]:.3f}.")
    else:
        lines.append(f"\n**Insights débil:** mejor F1(3+)={best_f1[1]:.3f} < 0.60. Sonnet mejor para niveles 3+.")

    lines.append("")
    lines.append("---")
    lines.append("*Generado por exp2_analyze_evaluators.py*")

    return "\n".join(lines)


def main():
    evaluator_results, sonnet_ref = load_data()

    sonnet_vecs = get_sonnet_vectors(sonnet_ref)
    print(f"Sonnet reference: {len(sonnet_vecs)} outputs, {sum(len(v) for v in sonnet_vecs.values())} datapoints")

    models_tested = evaluator_results.get("models_tested", [])
    print(f"Models to analyze: {models_tested}")

    metrics_by_model = {}
    all_model_vecs = {}

    for model_name in models_tested:
        model_vecs = get_model_vectors(evaluator_results, model_name)
        if not model_vecs:
            print(f"  {model_name}: no valid evaluations, skipping")
            continue

        all_model_vecs[model_name] = model_vecs
        metrics = compute_metrics(sonnet_vecs, model_vecs)

        # Add average time
        model_data = evaluator_results["results"].get(model_name, {})
        times = [v.get("tiempo_s", 0) for v in model_data.values() if "error" not in v and "tiempo_s" in v]
        if times:
            metrics["avg_time_s"] = round(sum(times) / len(times), 1)

        metrics_by_model[model_name] = metrics
        sp = metrics.get("spearman", "ERR")
        print(f"  {model_name}: Spearman={sp}, F1(3+)={metrics.get('f1_3plus', '?')}, MAE={metrics.get('mae', '?')}")

    # Complementarity
    print("\nComputing complementarity...")
    complementarity = compute_complementarity(sonnet_vecs, all_model_vecs)
    if complementarity:
        print(f"  Best pair: {complementarity[0]['pair']} → Sp={complementarity[0]['spearman_fused']:.4f}")

    # Role assignment
    roles = assign_roles(metrics_by_model, all_model_vecs)
    print(f"\nRoles assigned: {list(roles.keys())}")

    # Save JSON report
    json_report = {
        "meta": {
            "experiment": "Exp 2 - Enjambre Evaluadores OS",
            "date": str(date.today()),
            "n_models": len(metrics_by_model),
            "n_datapoints_per_model": 105,
        },
        "metrics_by_model": metrics_by_model,
        "complementarity": complementarity,
        "roles": roles,
    }
    json_path = RESULTS_DIR / "exp2_enjambre_evaluadores_report.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_report, f, ensure_ascii=False, indent=2)
    print(f"\nJSON report: {json_path}")

    # Save MD report
    md_report = generate_md_report(metrics_by_model, complementarity, roles)
    md_path = RESULTS_DIR / "exp2_enjambre_evaluadores_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"MD report: {md_path}")


if __name__ == "__main__":
    main()
