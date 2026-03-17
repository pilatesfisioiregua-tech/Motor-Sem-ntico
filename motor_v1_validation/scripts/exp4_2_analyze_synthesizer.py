"""Exp 4.2: El Sintetizador — Analisis.
Compara 6 candidatos de sintetizador. Genera report JSON y MD.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
SYNTH_FILE = RESULTS_DIR / "exp4_2_sintesis.json"
R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
REPORT_JSON = RESULTS_DIR / "exp4_2_sintetizador_report.json"
REPORT_MD = RESULTS_DIR / "exp4_2_sintetizador_report.md"

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
CELDAS_21 = ["%s\u00d7%s" % (l, f) for l in LENTES for f in FUNCIONES]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

ALL_EVALUATORS = [
    "opus", "sonnet", "v3.2-chat", "v3.2-reasoner",
    "deepseek-r1", "deepseek-v3.1", "cogito-671b",
    "gpt-oss-120b", "qwen3-235b", "minimax-m2.5",
    "kimi-k2.5", "glm-4.7",
]


# ── Helpers ──────────────────────────────────────────────────────

def get_nivel(celdas, celda):
    # type: (dict, str) -> int
    val = celdas.get(celda, {})
    if isinstance(val, dict):
        return val.get("nivel", 0)
    return 0


def get_celdas_r1(r1, model, oid):
    # type: (dict, str, str) -> dict
    entry = r1.get(model, {}).get(oid, {})
    return entry.get("celdas", {})


def get_celdas_r2(r2, model, oid):
    # type: (dict, str, str) -> dict
    entry = r2.get(model, {}).get(oid, {})
    if "error" in entry:
        return None
    enriched = entry.get("evaluacion_enriquecida", {})
    return enriched.get("celdas", None)


def get_best_celdas(r1, r2, model, oid):
    # type: (dict, dict, str, str) -> dict
    """Return R2 celdas if available, else R1."""
    c2 = get_celdas_r2(r2, model, oid)
    if c2:
        return c2
    return get_celdas_r1(r1, model, oid)


def lente_of(celda):
    # type: (str) -> str
    """Extract lente from 'Lente x Funcion'."""
    return celda.split("\u00d7")[0].strip()


# ── Load Data ────────────────────────────────────────────────────

def load_data():
    with open(SYNTH_FILE, encoding="utf-8") as f:
        synth_data = json.load(f)
    sintesis = synth_data.get("sintesis", {})

    with open(R1_FILE, encoding="utf-8") as f:
        r1_data = json.load(f)
    r1 = r1_data.get("evaluaciones", {})

    r2 = {}
    if R2_FILE.exists():
        with open(R2_FILE, encoding="utf-8") as f:
            r2_data = json.load(f)
        r2 = r2_data.get("evaluaciones", {})

    all_eval_models = sorted(set(list(r1.keys()) + list(r2.keys())))
    return sintesis, r1, r2, all_eval_models


# ── A) Max mecanico baseline ────────────────────────────────────

def compute_max_mecanico(r1, r2, all_eval_models):
    # type: (dict, dict, list) -> dict
    """For each output x cell, compute max(all evaluators), using best available eval."""
    max_mec = {}  # {output_id: {celda: int}}
    for oid in OUTPUT_IDS:
        cell_maxes = {}
        for celda in CELDAS_21:
            best = 0
            for model in all_eval_models:
                celdas = get_best_celdas(r1, r2, model, oid)
                n = get_nivel(celdas, celda)
                if n > best:
                    best = n
            cell_maxes[celda] = best
        max_mec[oid] = cell_maxes
    return max_mec


# ── B) Per-synthesizer quality metrics ──────────────────────────

def analyze_synth_output(synth_output, max_mec_for_output, output_id):
    # type: (dict, dict, str) -> dict
    """Analyze a single synthesizer output for one output_id."""
    result = {
        "output_id": output_id,
        "has_data": False,
    }

    # Check for errors
    if "error" in synth_output:
        result["error"] = synth_output["error"]
        return result

    eval_integrada = synth_output.get("evaluacion_integrada", {})
    celdas = eval_integrada.get("celdas", {})

    if not celdas:
        result["error"] = "no celdas found"
        return result

    result["has_data"] = True

    # 1. Evaluadores citados
    evaluators_cited = set()
    for celda in CELDAS_21:
        cell_data = celdas.get(celda, {})
        for ev in cell_data.get("evaluadores_que_aportaron", []):
            evaluators_cited.add(ev)
    result["evaluadores_citados"] = len(evaluators_cited)
    result["evaluadores_citados_list"] = sorted(evaluators_cited)

    # 2. Genuinidad de integracion
    genuine_count = 0
    total_cells = 0
    for celda in CELDAS_21:
        cell_data = celdas.get(celda, {})
        evidencia = cell_data.get("evidencia_integrada", "")
        evaluadores = cell_data.get("evaluadores_que_aportaron", [])
        total_cells += 1
        # Heuristic: length > 50 AND mentions 2+ evaluator names in text
        # Since evidencia_integrada is the synthesis, we check if it integrates
        # multiple sources by length AND having 2+ evaluators listed
        if len(evidencia) > 50 and len(evaluadores) >= 2:
            genuine_count += 1
    genuinidad_pct = round(100.0 * genuine_count / max(total_cells, 1), 1)
    result["genuinidad_pct"] = genuinidad_pct
    result["genuine_cells"] = genuine_count
    result["total_cells"] = total_cells

    # 3. Celdas que suben vs max mecanico
    celdas_up = 0
    celdas_same = 0
    celdas_down = 0
    nivel_sum_synth = 0
    nivel_sum_max = 0
    for celda in CELDAS_21:
        cell_data = celdas.get(celda, {})
        synth_nivel = cell_data.get("nivel", 0)
        max_nivel = max_mec_for_output.get(celda, 0)
        nivel_sum_synth += synth_nivel
        nivel_sum_max += max_nivel
        if synth_nivel > max_nivel:
            celdas_up += 1
        elif synth_nivel == max_nivel:
            celdas_same += 1
        else:
            celdas_down += 1
    result["celdas_up_vs_max"] = celdas_up
    result["celdas_same_vs_max"] = celdas_same
    result["celdas_down_vs_max"] = celdas_down
    result["nivel_sum_synth"] = nivel_sum_synth
    result["nivel_sum_max"] = nivel_sum_max

    # 4. Conexiones entre celdas
    conexiones = synth_output.get("conexiones_entre_celdas", [])
    total_conex = len(conexiones)
    cross_lente = 0
    intra_lente = 0
    for con in conexiones:
        la = lente_of(con.get("celda_a", ""))
        lb = lente_of(con.get("celda_b", ""))
        if la and lb and la != lb:
            cross_lente += 1
        else:
            intra_lente += 1
    result["conexiones_total"] = total_conex
    result["conexiones_cross_lente"] = cross_lente
    result["conexiones_intra_lente"] = intra_lente
    result["conexiones_detail"] = conexiones

    # 5. Hallazgo central
    hallazgo = synth_output.get("hallazgo_central", "")
    result["hallazgo_central"] = hallazgo
    result["hallazgo_len"] = len(hallazgo)
    result["hallazgo_non_generic"] = len(hallazgo) > 100

    # 6. Puntos ciegos residuales
    puntos_ciegos = synth_output.get("puntos_ciegos_residuales", [])
    result["puntos_ciegos_count"] = len(puntos_ciegos)
    result["puntos_ciegos"] = puntos_ciegos

    # 7. Meta-patrones
    meta_patrones = synth_output.get("meta_patrones", [])
    result["meta_patrones_count"] = len(meta_patrones)
    result["meta_patrones"] = meta_patrones

    # 8. Tiempo
    result["tiempo_s"] = synth_output.get("tiempo_s", 0)

    return result


def analyze_all_synths(sintesis, max_mec):
    # type: (dict, dict) -> dict
    """Analyze all synthesizers across all outputs."""
    synth_results = {}
    for synth_model in sorted(sintesis.keys()):
        synth_outputs = sintesis[synth_model]
        output_analyses = {}
        for oid in OUTPUT_IDS:
            if oid not in synth_outputs:
                continue
            output_analyses[oid] = analyze_synth_output(
                synth_outputs[oid],
                max_mec.get(oid, {}),
                oid,
            )
        synth_results[synth_model] = output_analyses
    return synth_results


def compute_synth_summary(synth_model, output_analyses):
    # type: (str, dict) -> dict
    """Compute aggregate metrics for a synthesizer across all outputs."""
    valid = [v for v in output_analyses.values() if v.get("has_data")]
    n = len(valid)
    if n == 0:
        return {
            "sintetizador": synth_model,
            "outputs_exitosos": 0,
            "failed": True,
        }

    avg_evaluadores = round(sum(v["evaluadores_citados"] for v in valid) / n, 1)
    avg_genuinidad = round(sum(v["genuinidad_pct"] for v in valid) / n, 1)
    total_up = sum(v["celdas_up_vs_max"] for v in valid)
    total_same = sum(v["celdas_same_vs_max"] for v in valid)
    total_down = sum(v["celdas_down_vs_max"] for v in valid)
    avg_conexiones = round(sum(v["conexiones_total"] for v in valid) / n, 1)
    avg_cross = round(sum(v["conexiones_cross_lente"] for v in valid) / n, 1)
    avg_hallazgo_len = round(sum(v["hallazgo_len"] for v in valid) / n, 1)
    hallazgo_non_generic = sum(1 for v in valid if v["hallazgo_non_generic"])
    avg_puntos_ciegos = round(sum(v["puntos_ciegos_count"] for v in valid) / n, 1)
    avg_meta_patrones = round(sum(v["meta_patrones_count"] for v in valid) / n, 1)
    avg_tiempo = round(sum(v["tiempo_s"] for v in valid) / n, 1)

    return {
        "sintetizador": synth_model,
        "outputs_exitosos": n,
        "failed": False,
        "avg_evaluadores_citados": avg_evaluadores,
        "avg_genuinidad_pct": avg_genuinidad,
        "celdas_up_total": total_up,
        "celdas_same_total": total_same,
        "celdas_down_total": total_down,
        "avg_conexiones": avg_conexiones,
        "avg_cross_lente": avg_cross,
        "avg_hallazgo_len": avg_hallazgo_len,
        "hallazgo_non_generic_count": hallazgo_non_generic,
        "avg_puntos_ciegos": avg_puntos_ciegos,
        "avg_meta_patrones": avg_meta_patrones,
        "avg_tiempo_s": avg_tiempo,
    }


# ── C) Comparative Table ────────────────────────────────────────

def format_comparative_table(summaries):
    # type: (list) -> str
    """Generate markdown table from summaries."""
    lines = []
    header = (
        "| Sintetizador | Outputs OK | Eval citados | Genuinidad%% "
        "| Celdas up | Conexiones | Cross-lente | Hallazgo (len) "
        "| Puntos ciegos | Meta-patrones | Tiempo (s) |"
    )
    sep = (
        "|---|---|---|---|---|---|---|---|---|---|---|"
    )
    lines.append(header)
    lines.append(sep)
    for s in summaries:
        if s["failed"]:
            lines.append(
                "| %s | 0 (FAILED) | - | - | - | - | - | - | - | - | - |"
                % s["sintetizador"]
            )
        else:
            lines.append(
                "| %s | %d | %.1f | %.1f%% | %d | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |"
                % (
                    s["sintetizador"],
                    s["outputs_exitosos"],
                    s["avg_evaluadores_citados"],
                    s["avg_genuinidad_pct"],
                    s["celdas_up_total"],
                    s["avg_conexiones"],
                    s["avg_cross_lente"],
                    s["avg_hallazgo_len"],
                    s["avg_puntos_ciegos"],
                    s["avg_meta_patrones"],
                    s["avg_tiempo_s"],
                )
            )
    return "\n".join(lines)


# ── D) Synthesizer vs max mecanico ──────────────────────────────

def compare_best_synth_vs_max(synth_results, max_mec, sintesis):
    # type: (dict, dict, dict) -> dict
    """Find the best synthesizer and compare to max mecanico."""
    # Determine best: highest avg genuinidad + most conexiones + most celdas_up
    best_synth = None
    best_score = -1
    summaries_for_rank = {}

    for synth_model, output_analyses in synth_results.items():
        valid = [v for v in output_analyses.values() if v.get("has_data")]
        if not valid:
            continue
        n = len(valid)
        avg_gen = sum(v["genuinidad_pct"] for v in valid) / n
        avg_conex = sum(v["conexiones_total"] for v in valid) / n
        total_up = sum(v["celdas_up_vs_max"] for v in valid)
        # Composite score: genuinidad (0-100) + conexiones*10 + celdas_up*5
        score = avg_gen + avg_conex * 10 + total_up * 5
        summaries_for_rank[synth_model] = score
        if score > best_score:
            best_score = score
            best_synth = synth_model

    if not best_synth:
        return {"best_synth": None}

    # Detailed comparison for best synth
    comparison = {
        "best_synth": best_synth,
        "ranking": sorted(summaries_for_rank.items(), key=lambda x: -x[1]),
        "per_output": {},
    }

    best_analyses = synth_results[best_synth]
    total_same = 0
    total_higher = 0
    total_lower = 0
    total_conexiones = 0

    for oid in OUTPUT_IDS:
        analysis = best_analyses.get(oid)
        if not analysis or not analysis.get("has_data"):
            continue
        total_same += analysis["celdas_same_vs_max"]
        total_higher += analysis["celdas_up_vs_max"]
        total_lower += analysis["celdas_down_vs_max"]
        total_conexiones += analysis["conexiones_total"]
        comparison["per_output"][oid] = {
            "same": analysis["celdas_same_vs_max"],
            "higher": analysis["celdas_up_vs_max"],
            "lower": analysis["celdas_down_vs_max"],
            "conexiones": analysis["conexiones_total"],
            "hallazgo": analysis["hallazgo_central"],
        }

    comparison["total_cells_same"] = total_same
    comparison["total_cells_higher"] = total_higher
    comparison["total_cells_lower"] = total_lower
    comparison["total_conexiones"] = total_conexiones
    comparison["max_mec_conexiones"] = 0  # Max mecanico has 0 by definition
    comparison["max_mec_hallazgo"] = "(none)"

    return comparison


# ── E) Top 5 connections ────────────────────────────────────────

def find_top_connections(synth_results):
    # type: (dict) -> list
    """Find top 5 most interesting cross-lente connections across all synthesizers."""
    all_connections = []
    for synth_model, output_analyses in synth_results.items():
        for oid, analysis in output_analyses.items():
            if not analysis.get("has_data"):
                continue
            for con in analysis.get("conexiones_detail", []):
                la = lente_of(con.get("celda_a", ""))
                lb = lente_of(con.get("celda_b", ""))
                is_cross = (la and lb and la != lb)
                all_connections.append({
                    "synth": synth_model,
                    "output": oid,
                    "celda_a": con.get("celda_a", ""),
                    "celda_b": con.get("celda_b", ""),
                    "conexion": con.get("conexion", ""),
                    "evaluadores_origen": con.get("evaluadores_origen", []),
                    "is_cross_lente": is_cross,
                })

    # Prioritize cross-lente, then by connection text length (more detailed = more interesting)
    all_connections.sort(
        key=lambda c: (
            not c["is_cross_lente"],  # cross first (False < True)
            -len(c["conexion"]),      # longer text = more interesting
        )
    )

    # Deduplicate by (celda_a, celda_b) - keep first (best) per pair
    seen_pairs = set()
    top = []
    for con in all_connections:
        pair = (con["celda_a"], con["celda_b"])
        pair_rev = (con["celda_b"], con["celda_a"])
        if pair in seen_pairs or pair_rev in seen_pairs:
            continue
        seen_pairs.add(pair)
        top.append(con)
        if len(top) >= 5:
            break

    return top


# ── F) Hallazgos centrales side by side ─────────────────────────

def collect_hallazgos(synth_results):
    # type: (dict) -> dict
    """Collect hallazgo_central from all synthesizers per output."""
    hallazgos = {}  # {output_id: {synth: hallazgo_text}}
    for synth_model, output_analyses in synth_results.items():
        for oid, analysis in output_analyses.items():
            if not analysis.get("has_data"):
                continue
            hallazgo = analysis.get("hallazgo_central", "")
            if not hallazgo:
                continue
            if oid not in hallazgos:
                hallazgos[oid] = {}
            hallazgos[oid][synth_model] = hallazgo
    return hallazgos


# ── G) Veredicto ────────────────────────────────────────────────

def compute_veredicto(summaries, comparison, synth_results, max_mec):
    # type: (list, dict, dict, dict) -> dict
    """Final verdict: best synth, cost vs value, recommended protocol."""

    # Best synthesizer
    active = [s for s in summaries if not s["failed"]]
    if not active:
        return {
            "mejor_sintetizador": "N/A",
            "justificacion": "Todos fallaron.",
            "vale_la_pena": False,
            "protocolo_recomendado": "N/A",
        }

    # Rank by composite: genuinidad + conexiones weight + hallazgo quality
    def rank_score(s):
        return (
            s["avg_genuinidad_pct"]
            + s["avg_conexiones"] * 10
            + s["celdas_up_total"] * 5
            + s["avg_meta_patrones"] * 8
            + (1 if s["avg_hallazgo_len"] > 100 else 0) * 10
        )

    active.sort(key=rank_score, reverse=True)
    best = active[0]
    best_name = best["sintetizador"]

    # Is synthesis worth it?
    # Value: conexiones, hallazgos, meta-patrones are UNIQUE to synthesis (max mec has 0)
    total_higher = comparison.get("total_cells_higher", 0)
    total_conexiones = comparison.get("total_conexiones", 0)
    has_hallazgos = any(
        a.get("hallazgo_non_generic", False)
        for analyses in synth_results.values()
        for a in analyses.values()
        if a.get("has_data")
    )

    # Compute how many cells synth matches or exceeds max mec
    total_cells_compared = (
        comparison.get("total_cells_same", 0)
        + comparison.get("total_cells_higher", 0)
        + comparison.get("total_cells_lower", 0)
    )
    match_or_exceed_pct = 0.0
    if total_cells_compared > 0:
        match_or_exceed_pct = round(
            100.0
            * (comparison.get("total_cells_same", 0) + comparison.get("total_cells_higher", 0))
            / total_cells_compared,
            1,
        )

    vale_la_pena = (total_conexiones > 0 or has_hallazgos or total_higher > 0)

    reasons = []
    if total_conexiones > 0:
        reasons.append(
            "genera %d conexiones entre celdas (max mecanico: 0)" % total_conexiones
        )
    if has_hallazgos:
        reasons.append("produce hallazgos centrales no triviales")
    if total_higher > 0:
        reasons.append(
            "%d celdas superan el max mecanico" % total_higher
        )
    if match_or_exceed_pct > 0:
        reasons.append(
            "%.1f%% de celdas igualan o superan max mecanico" % match_or_exceed_pct
        )

    justificacion_vale = "; ".join(reasons) if reasons else "sin mejoras claras"

    return {
        "mejor_sintetizador": best_name,
        "ranking": [
            {"modelo": s["sintetizador"], "score": round(rank_score(s), 1)}
            for s in active
        ],
        "justificacion": (
            "%s destaca por genuinidad %.1f%%, %.1f conexiones/output, "
            "%.1f meta-patrones/output, %d celdas por encima del max mecanico"
            % (
                best_name,
                best["avg_genuinidad_pct"],
                best["avg_conexiones"],
                best["avg_meta_patrones"],
                best["celdas_up_total"],
            )
        ),
        "vale_la_pena": vale_la_pena,
        "justificacion_vale_la_pena": justificacion_vale,
        "match_or_exceed_pct": match_or_exceed_pct,
        "protocolo_recomendado": (
            "1. Recoger evaluaciones R1+R2 de la mesa redonda (12 evaluadores). "
            "2. Pasar todas las evaluaciones al sintetizador (%s). "
            "3. El sintetizador produce: evaluacion integrada 21 celdas + conexiones + hallazgo central + puntos ciegos + meta-patrones. "
            "4. Coste adicional: 1 llamada LLM (~%.1fs). "
            "5. Valor: conexiones entre lentes, hallazgo central, meta-patrones — informacion que max mecanico NO produce."
            % (best_name, best["avg_tiempo_s"])
        ),
    }


# ── Report MD ────────────────────────────────────────────────────

def generate_report_md(
    summaries,
    synth_results,
    max_mec,
    comparison,
    top_connections,
    hallazgos,
    veredicto,
):
    lines = []
    lines.append("# Exp 4.2 — El Sintetizador: Informe de Analisis")
    lines.append("")
    lines.append("## Resumen")
    lines.append("")
    n_total = len(summaries)
    n_ok = sum(1 for s in summaries if not s["failed"])
    n_fail = n_total - n_ok
    lines.append(
        "- **Sintetizadores evaluados:** %d (%d exitosos, %d fallidos)"
        % (n_total, n_ok, n_fail)
    )
    lines.append("- **Outputs por sintetizador:** %d" % len(OUTPUT_IDS))
    lines.append("- **Celdas por output:** %d (3 lentes x 7 funciones)" % len(CELDAS_21))
    lines.append(
        "- **Evaluadores en mesa redonda:** %d" % len(ALL_EVALUATORS)
    )
    lines.append("")

    # Failed synthesizers
    failed = [s for s in summaries if s["failed"]]
    if failed:
        lines.append("### Sintetizadores fallidos")
        lines.append("")
        for s in failed:
            lines.append("- **%s**: todos los outputs fallaron (parse error)" % s["sintetizador"])
        lines.append("")

    # ── A) Max mecanico
    lines.append("---")
    lines.append("")
    lines.append("## A) Max Mecanico Baseline")
    lines.append("")
    lines.append(
        "Para cada output, se calcula `max(13 evaluadores)` por celda "
        "usando la mejor evaluacion disponible (R2 si no tiene error, sino R1)."
    )
    lines.append("")
    for oid in OUTPUT_IDS:
        cells = max_mec.get(oid, {})
        total = sum(cells.get(c, 0) for c in CELDAS_21)
        n3plus = sum(1 for c in CELDAS_21 if cells.get(c, 0) >= 3)
        n4 = sum(1 for c in CELDAS_21 if cells.get(c, 0) >= 4)
        avg = total / max(len(CELDAS_21), 1)
        lines.append(
            "- **%s**: suma=%d, media=%.2f, celdas>=3: %d, celdas>=4: %d"
            % (oid, total, avg, n3plus, n4)
        )
    lines.append("")

    # ── B) Per-synthesizer detail
    lines.append("---")
    lines.append("")
    lines.append("## B) Metricas por Sintetizador")
    lines.append("")
    for s in summaries:
        if s["failed"]:
            continue
        lines.append("### %s" % s["sintetizador"])
        lines.append("")
        lines.append("| Metrica | Valor |")
        lines.append("|---|---|")
        lines.append("| Outputs exitosos | %d / %d |" % (s["outputs_exitosos"], len(OUTPUT_IDS)))
        lines.append("| Evaluadores citados (media) | %.1f |" % s["avg_evaluadores_citados"])
        lines.append("| Genuinidad de integracion | %.1f%% |" % s["avg_genuinidad_pct"])
        lines.append(
            "| Celdas que suben vs max mec | %d (same: %d, down: %d) |"
            % (s["celdas_up_total"], s["celdas_same_total"], s["celdas_down_total"])
        )
        lines.append("| Conexiones (media) | %.1f |" % s["avg_conexiones"])
        lines.append("| Cross-lente (media) | %.1f |" % s["avg_cross_lente"])
        lines.append("| Hallazgo central (len media) | %.1f chars |" % s["avg_hallazgo_len"])
        lines.append(
            "| Hallazgos no-genericos | %d / %d |"
            % (s["hallazgo_non_generic_count"], s["outputs_exitosos"])
        )
        lines.append("| Puntos ciegos residuales (media) | %.1f |" % s["avg_puntos_ciegos"])
        lines.append("| Meta-patrones (media) | %.1f |" % s["avg_meta_patrones"])
        lines.append("| Tiempo medio (s) | %.1f |" % s["avg_tiempo_s"])
        lines.append("")

    # ── C) Comparative Table
    lines.append("---")
    lines.append("")
    lines.append("## C) Tabla Comparativa")
    lines.append("")
    lines.append(format_comparative_table(summaries))
    lines.append("")

    # ── D) Best synth vs max mecanico
    lines.append("---")
    lines.append("")
    lines.append("## D) Mejor Sintetizador vs Max Mecanico")
    lines.append("")
    if comparison.get("best_synth"):
        lines.append("**Mejor sintetizador:** %s" % comparison["best_synth"])
        lines.append("")
        lines.append("| Metrica | Sintetizador | Max Mecanico |")
        lines.append("|---|---|---|")
        lines.append(
            "| Celdas al mismo nivel | %d | (referencia) |"
            % comparison["total_cells_same"]
        )
        lines.append(
            "| Celdas por encima | %d | 0 |" % comparison["total_cells_higher"]
        )
        lines.append(
            "| Celdas por debajo | %d | 0 |" % comparison["total_cells_lower"]
        )
        lines.append(
            "| Conexiones totales | %d | 0 |" % comparison["total_conexiones"]
        )
        lines.append(
            "| Hallazgo central | Si | No |"
        )
        lines.append("")
        lines.append("### Detalle por output")
        lines.append("")
        for oid in OUTPUT_IDS:
            detail = comparison["per_output"].get(oid)
            if not detail:
                lines.append("- **%s**: no data" % oid)
                continue
            lines.append(
                "- **%s**: same=%d, higher=%d, lower=%d, conexiones=%d"
                % (oid, detail["same"], detail["higher"], detail["lower"], detail["conexiones"])
            )
        lines.append("")
    else:
        lines.append("No hay sintetizador exitoso para comparar.")
        lines.append("")

    # ── E) Top 5 connections
    lines.append("---")
    lines.append("")
    lines.append("## E) Top 5 Conexiones Cross-Lente")
    lines.append("")
    for i, con in enumerate(top_connections):
        lines.append(
            "### %d. %s <-> %s" % (i + 1, con["celda_a"], con["celda_b"])
        )
        cross_tag = " **(CROSS-LENTE)**" if con["is_cross_lente"] else ""
        lines.append(
            "- **Tipo:** %s%s" % (
                "cross-lente" if con["is_cross_lente"] else "intra-lente",
                cross_tag,
            )
        )
        lines.append("- **Sintetizador:** %s (output: %s)" % (con["synth"], con["output"]))
        lines.append("- **Conexion:** %s" % con["conexion"])
        lines.append(
            "- **Evaluadores origen:** %s"
            % ", ".join(con["evaluadores_origen"])
        )
        lines.append("")

    # ── F) Hallazgos centrales side by side
    lines.append("---")
    lines.append("")
    lines.append("## F) Hallazgos Centrales — Comparacion")
    lines.append("")
    for oid in OUTPUT_IDS:
        if oid not in hallazgos:
            continue
        lines.append("### Output: %s" % oid)
        lines.append("")
        for synth_model in sorted(hallazgos[oid].keys()):
            text = hallazgos[oid][synth_model]
            lines.append("**%s** (%d chars):" % (synth_model, len(text)))
            lines.append("> %s" % text)
            lines.append("")

    # ── G) Veredicto
    lines.append("---")
    lines.append("")
    lines.append("## G) Veredicto")
    lines.append("")
    lines.append("### Mejor sintetizador")
    lines.append("")
    lines.append("**%s**" % veredicto["mejor_sintetizador"])
    lines.append("")
    lines.append(veredicto["justificacion"])
    lines.append("")
    lines.append("### Ranking")
    lines.append("")
    for item in veredicto.get("ranking", []):
        lines.append("1. **%s** — score: %.1f" % (item["modelo"], item["score"]))
    lines.append("")
    lines.append("### Vale la pena la sintesis vs max mecanico?")
    lines.append("")
    lines.append("**%s**" % ("SI" if veredicto["vale_la_pena"] else "NO"))
    lines.append("")
    lines.append(veredicto["justificacion_vale_la_pena"])
    lines.append("")
    if veredicto.get("match_or_exceed_pct"):
        lines.append(
            "El mejor sintetizador iguala o supera el max mecanico en **%.1f%%** de las celdas."
            % veredicto["match_or_exceed_pct"]
        )
        lines.append("")
    lines.append("### Protocolo recomendado")
    lines.append("")
    lines.append(veredicto["protocolo_recomendado"])
    lines.append("")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=== Exp 4.2 — Analisis del Sintetizador ===")
    print()

    # Load
    sintesis, r1, r2, all_eval_models = load_data()
    print("Sintetizadores: %s" % sorted(sintesis.keys()))
    print("Evaluadores R1: %d, R2: %d, Union: %d" % (
        len(r1), len(r2), len(all_eval_models),
    ))
    print()

    # A) Max mecanico
    print("[A] Calculando max mecanico baseline...")
    max_mec = compute_max_mecanico(r1, r2, all_eval_models)
    for oid in OUTPUT_IDS:
        cells = max_mec[oid]
        total = sum(cells[c] for c in CELDAS_21)
        print("  %s: suma_niveles=%d" % (oid, total))
    print()

    # B) Per-synthesizer analysis
    print("[B] Analizando sintetizadores...")
    synth_results = analyze_all_synths(sintesis, max_mec)

    summaries = []
    for synth_model in sorted(synth_results.keys()):
        s = compute_synth_summary(synth_model, synth_results[synth_model])
        summaries.append(s)
        if s["failed"]:
            print("  %s: FAILED" % synth_model)
        else:
            print(
                "  %s: %d outputs, genuinidad=%.1f%%, conex=%.1f, up=%d"
                % (
                    synth_model,
                    s["outputs_exitosos"],
                    s["avg_genuinidad_pct"],
                    s["avg_conexiones"],
                    s["celdas_up_total"],
                )
            )
    print()

    # C) Comparative table (generated in MD)

    # D) Best synth vs max mecanico
    print("[D] Comparando mejor sintetizador vs max mecanico...")
    comparison = compare_best_synth_vs_max(synth_results, max_mec, sintesis)
    if comparison.get("best_synth"):
        print(
            "  Mejor: %s — same=%d, higher=%d, lower=%d, conexiones=%d"
            % (
                comparison["best_synth"],
                comparison["total_cells_same"],
                comparison["total_cells_higher"],
                comparison["total_cells_lower"],
                comparison["total_conexiones"],
            )
        )
    print()

    # E) Top 5 connections
    print("[E] Buscando top 5 conexiones cross-lente...")
    top_connections = find_top_connections(synth_results)
    for i, con in enumerate(top_connections):
        tag = "CROSS" if con["is_cross_lente"] else "intra"
        print(
            "  %d. [%s] %s <-> %s (%s)"
            % (i + 1, tag, con["celda_a"], con["celda_b"], con["synth"])
        )
    print()

    # F) Hallazgos
    print("[F] Recopilando hallazgos centrales...")
    hallazgos = collect_hallazgos(synth_results)
    for oid in OUTPUT_IDS:
        synths_with = hallazgos.get(oid, {})
        print(
            "  %s: %d sintetizadores con hallazgo"
            % (oid, len(synths_with))
        )
    print()

    # G) Veredicto
    print("[G] Computando veredicto...")
    veredicto = compute_veredicto(summaries, comparison, synth_results, max_mec)
    print("  Mejor: %s" % veredicto["mejor_sintetizador"])
    print("  Vale la pena: %s" % veredicto["vale_la_pena"])
    print()

    # ── Build report
    report = {
        "meta": {
            "experiment": "Exp 4.2 - El Sintetizador - Analisis",
            "outputs": OUTPUT_IDS,
            "celdas": CELDAS_21,
            "evaluadores": ALL_EVALUATORS,
        },
        "max_mecanico": max_mec,
        "synth_results": {},
        "summaries": summaries,
        "comparison_vs_max": comparison,
        "top_connections": top_connections,
        "hallazgos": hallazgos,
        "veredicto": veredicto,
    }

    # Include per-synth results but strip conexiones_detail to keep JSON manageable
    for synth_model, output_analyses in synth_results.items():
        cleaned = {}
        for oid, analysis in output_analyses.items():
            a = dict(analysis)
            a.pop("conexiones_detail", None)
            cleaned[oid] = a
        report["synth_results"][synth_model] = cleaned

    # ── Write JSON
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("JSON: %s" % REPORT_JSON)

    # ── Write MD
    md = generate_report_md(
        summaries, synth_results, max_mec, comparison,
        top_connections, hallazgos, veredicto,
    )
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print("MD:   %s" % REPORT_MD)
    print()
    print("Done.")


if __name__ == "__main__":
    main()
