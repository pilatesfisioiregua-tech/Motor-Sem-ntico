"""Exp 4.1 vs Exp 4: Specialized vs Generic prompt comparison.
Compares Mesa Redonda Especializada (4.1) against generic (4) across all models and cells.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"

# Input files
EXP4_R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
EXP4_R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
EXP41_R1_FILE = RESULTS_DIR / "exp4_1_ronda1_especializada.json"
EXP41_R2_FILE = RESULTS_DIR / "exp4_1_ronda2.json"

# Output files
REPORT_JSON = RESULTS_DIR / "exp4_1_comparison_report.json"
REPORT_MD = RESULTS_DIR / "exp4_1_comparison_report.md"

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
CELDAS_21 = ["%s\u00d7%s" % (l, f) for l in LENTES for f in FUNCIONES]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

# ── Model Focus Areas ────────────────────────────────────────────
MODEL_FOCUS = {
    "cogito-671b": {"lentes": ["Sentido"], "funciones": ["Frontera"]},
    "deepseek-r1": {"lentes": ["Continuidad"], "funciones": []},
    "deepseek-v3.1": {"lentes": [], "funciones": ["Frontera", "Conservar"]},
    "v3.2-chat": {"lentes": [], "funciones": []},
    "gpt-oss-120b": {"lentes": [], "funciones": ["Depurar", "Captar"]},
    "qwen3-235b": {"lentes": [], "funciones": []},
    "v3.2-reasoner": {"lentes": [], "funciones": []},
    "glm-4.7": {"lentes": ["Sentido"], "funciones": []},
    "kimi-k2.5": {"lentes": [], "funciones": ["Adaptar"]},
    "minimax-m2.5": {"lentes": [], "funciones": ["Distribuir", "Replicar"]},
    "opus": {"lentes": [], "funciones": []},
}


def is_in_focus(model, celda):
    """Return True if the celda is in the model's focus area."""
    focus = MODEL_FOCUS.get(model, {"lentes": [], "funciones": []})
    parts = celda.split("\u00d7")
    if len(parts) != 2:
        return False
    lente, funcion = parts
    if lente in focus["lentes"]:
        return True
    if funcion in focus["funciones"]:
        return True
    return False


def has_focus(model):
    """Return True if the model has any specific focus cells."""
    focus = MODEL_FOCUS.get(model, {"lentes": [], "funciones": []})
    return len(focus["lentes"]) > 0 or len(focus["funciones"]) > 0


# ── Helpers ──────────────────────────────────────────────────────

def get_nivel(celdas, celda):
    val = celdas.get(celda, {})
    if isinstance(val, dict):
        return val.get("nivel", 0)
    return 0


def get_celdas_r1(r1_evals, model, oid):
    entry = r1_evals.get(model, {}).get(oid, {})
    return entry.get("celdas", {})


def get_celdas_r2(r2_evals, model, oid):
    entry = r2_evals.get(model, {}).get(oid, {})
    if "error" in entry:
        return None
    enriched = entry.get("evaluacion_enriquecida", {})
    return enriched.get("celdas", None)


def get_best_celdas(r1_evals, r2_evals, model, oid):
    """Return R2 celdas if available, else R1."""
    c2 = get_celdas_r2(r2_evals, model, oid)
    if c2:
        return c2
    return get_celdas_r1(r1_evals, model, oid)


def safe_mean(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


# ── Load Data ────────────────────────────────────────────────────

def load_evals(filepath):
    if not filepath.exists():
        print("WARNING: %s not found" % filepath)
        return {}
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("evaluaciones", {})


def load_all():
    gen_r1 = load_evals(EXP4_R1_FILE)
    gen_r2 = load_evals(EXP4_R2_FILE)
    spec_r1 = load_evals(EXP41_R1_FILE)
    spec_r2 = load_evals(EXP41_R2_FILE)

    # Models present in both generic R1 and specialized R1
    common_models = sorted(set(gen_r1.keys()) & set(spec_r1.keys()))

    return gen_r1, gen_r2, spec_r1, spec_r2, common_models


# ── A) Per-model comparison: generic vs specialized (R1) ─────────

def compute_per_model_r1(gen_r1, spec_r1, common_models):
    """For each model x output: compare generic R1 vs specialized R1."""
    results = {}
    for model in common_models:
        model_data = {
            "por_output": {},
            "nivel_medio_generico": 0.0,
            "nivel_medio_especializado": 0.0,
            "delta_global": 0.0,
            "delta_en_foco": None,
            "delta_fuera_foco": None,
        }

        all_gen_niveles = []
        all_spec_niveles = []
        all_deltas = []
        focus_deltas = []
        nonfocus_deltas = []

        for oid in OUTPUT_IDS:
            gen_celdas = get_celdas_r1(gen_r1, model, oid)
            spec_celdas = get_celdas_r1(spec_r1, model, oid)
            if not gen_celdas and not spec_celdas:
                continue

            output_data = {"celdas": {}}
            for celda in CELDAS_21:
                g = get_nivel(gen_celdas, celda)
                s = get_nivel(spec_celdas, celda)
                d = s - g
                output_data["celdas"][celda] = {
                    "generico": g,
                    "especializado": s,
                    "delta": d,
                }
                all_gen_niveles.append(g)
                all_spec_niveles.append(s)
                all_deltas.append(d)

                if is_in_focus(model, celda):
                    focus_deltas.append(d)
                else:
                    nonfocus_deltas.append(d)

            gen_niveles_oid = [get_nivel(gen_celdas, c) for c in CELDAS_21]
            spec_niveles_oid = [get_nivel(spec_celdas, c) for c in CELDAS_21]
            output_data["nivel_medio_generico"] = round(safe_mean(gen_niveles_oid), 3)
            output_data["nivel_medio_especializado"] = round(safe_mean(spec_niveles_oid), 3)
            output_data["delta"] = round(output_data["nivel_medio_especializado"] - output_data["nivel_medio_generico"], 3)
            model_data["por_output"][oid] = output_data

        model_data["nivel_medio_generico"] = round(safe_mean(all_gen_niveles), 3)
        model_data["nivel_medio_especializado"] = round(safe_mean(all_spec_niveles), 3)
        model_data["delta_global"] = round(safe_mean(all_deltas), 3)

        if has_focus(model) and focus_deltas:
            model_data["delta_en_foco"] = round(safe_mean(focus_deltas), 3)
        if has_focus(model) and nonfocus_deltas:
            model_data["delta_fuera_foco"] = round(safe_mean(nonfocus_deltas), 3)

        results[model] = model_data

    return results


# ── B) Collective map comparison ─────────────────────────────────

def compute_collective_map(gen_r1, gen_r2, spec_r1, spec_r2, common_models):
    """Max score per cell across all models: generic vs specialized."""
    map_data = {}
    summary = {
        "gen_3plus": 0,
        "spec_3plus": 0,
        "celdas_up": 0,
        "celdas_down": 0,
        "celdas_equal": 0,
    }

    for oid in OUTPUT_IDS:
        map_data[oid] = {}
        for celda in CELDAS_21:
            max_gen = 0
            max_spec = 0
            for m in common_models:
                # Generic: best available (R2 if exists, else R1)
                gen_celdas = get_best_celdas(gen_r1, gen_r2, m, oid)
                if gen_celdas:
                    max_gen = max(max_gen, get_nivel(gen_celdas, celda))
                # Specialized: best available (R2 if exists, else R1)
                spec_celdas = get_best_celdas(spec_r1, spec_r2, m, oid)
                if spec_celdas:
                    max_spec = max(max_spec, get_nivel(spec_celdas, celda))

            delta = max_spec - max_gen
            map_data[oid][celda] = {
                "max_generico": max_gen,
                "max_especializado": max_spec,
                "delta": delta,
            }

            if max_gen >= 3:
                summary["gen_3plus"] += 1
            if max_spec >= 3:
                summary["spec_3plus"] += 1
            if delta > 0:
                summary["celdas_up"] += 1
            elif delta < 0:
                summary["celdas_down"] += 1
            else:
                summary["celdas_equal"] += 1

    return map_data, summary


# ── C) R2 comparison ─────────────────────────────────────────────

def compute_per_model_r2(gen_r1, gen_r2, spec_r1, spec_r2, common_models):
    """Same as A but using best available (R2 > R1)."""
    results = {}
    for model in common_models:
        model_data = {
            "nivel_medio_generico_best": 0.0,
            "nivel_medio_especializado_best": 0.0,
            "delta_global": 0.0,
            "delta_en_foco": None,
            "delta_fuera_foco": None,
        }

        all_gen_niveles = []
        all_spec_niveles = []
        all_deltas = []
        focus_deltas = []
        nonfocus_deltas = []

        for oid in OUTPUT_IDS:
            gen_celdas = get_best_celdas(gen_r1, gen_r2, model, oid)
            spec_celdas = get_best_celdas(spec_r1, spec_r2, model, oid)
            if not gen_celdas and not spec_celdas:
                continue

            for celda in CELDAS_21:
                g = get_nivel(gen_celdas, celda) if gen_celdas else 0
                s = get_nivel(spec_celdas, celda) if spec_celdas else 0
                d = s - g
                all_gen_niveles.append(g)
                all_spec_niveles.append(s)
                all_deltas.append(d)

                if is_in_focus(model, celda):
                    focus_deltas.append(d)
                else:
                    nonfocus_deltas.append(d)

        model_data["nivel_medio_generico_best"] = round(safe_mean(all_gen_niveles), 3)
        model_data["nivel_medio_especializado_best"] = round(safe_mean(all_spec_niveles), 3)
        model_data["delta_global"] = round(safe_mean(all_deltas), 3)

        if has_focus(model) and focus_deltas:
            model_data["delta_en_foco"] = round(safe_mean(focus_deltas), 3)
        if has_focus(model) and nonfocus_deltas:
            model_data["delta_fuera_foco"] = round(safe_mean(nonfocus_deltas), 3)

        results[model] = model_data

    return results


def compute_collective_map_r2(gen_r1, gen_r2, spec_r1, spec_r2, common_models):
    """Collective map using best available data (R2 > R1)."""
    summary = {
        "gen_3plus": 0,
        "spec_3plus": 0,
        "celdas_up": 0,
        "celdas_down": 0,
        "celdas_equal": 0,
    }

    for oid in OUTPUT_IDS:
        for celda in CELDAS_21:
            max_gen = 0
            max_spec = 0
            for m in common_models:
                gen_celdas = get_best_celdas(gen_r1, gen_r2, m, oid)
                if gen_celdas:
                    max_gen = max(max_gen, get_nivel(gen_celdas, celda))
                spec_celdas = get_best_celdas(spec_r1, spec_r2, m, oid)
                if spec_celdas:
                    max_spec = max(max_spec, get_nivel(spec_celdas, celda))

            if max_gen >= 3:
                summary["gen_3plus"] += 1
            if max_spec >= 3:
                summary["spec_3plus"] += 1
            delta = max_spec - max_gen
            if delta > 0:
                summary["celdas_up"] += 1
            elif delta < 0:
                summary["celdas_down"] += 1
            else:
                summary["celdas_equal"] += 1

    return summary


# ── D) Fichas actualizadas per model ─────────────────────────────

def compute_fichas(gen_r1, gen_r2, spec_r1, spec_r2, common_models):
    """Per-model ficha with generic vs specialized stats."""
    fichas = {}
    for model in common_models:
        ficha = {"modelo": model}

        gen_niveles = []
        spec_niveles = []
        gen_foco = []
        spec_foco = []
        gen_fuera = []
        spec_fuera = []
        per_cell_deltas = {}  # celda -> list of deltas

        for oid in OUTPUT_IDS:
            gen_celdas = get_best_celdas(gen_r1, gen_r2, model, oid)
            spec_celdas = get_best_celdas(spec_r1, spec_r2, model, oid)
            if not gen_celdas and not spec_celdas:
                continue

            for celda in CELDAS_21:
                g = get_nivel(gen_celdas, celda) if gen_celdas else 0
                s = get_nivel(spec_celdas, celda) if spec_celdas else 0
                gen_niveles.append(g)
                spec_niveles.append(s)

                d = s - g
                if celda not in per_cell_deltas:
                    per_cell_deltas[celda] = []
                per_cell_deltas[celda].append(d)

                if is_in_focus(model, celda):
                    gen_foco.append(g)
                    spec_foco.append(s)
                else:
                    gen_fuera.append(g)
                    spec_fuera.append(s)

        media_gen = round(safe_mean(gen_niveles), 3)
        media_spec = round(safe_mean(spec_niveles), 3)
        ficha["media_generica"] = media_gen
        ficha["media_especializada"] = media_spec
        ficha["delta"] = round(media_spec - media_gen, 3)

        if has_focus(model) and gen_foco:
            ficha["media_en_foco_generica"] = round(safe_mean(gen_foco), 3)
            ficha["media_en_foco_especializada"] = round(safe_mean(spec_foco), 3)
            ficha["delta_foco"] = round(safe_mean(spec_foco) - safe_mean(gen_foco), 3)
        else:
            ficha["media_en_foco_generica"] = None
            ficha["media_en_foco_especializada"] = None
            ficha["delta_foco"] = None

        if has_focus(model) and gen_fuera:
            ficha["media_fuera_foco_generica"] = round(safe_mean(gen_fuera), 3)
            ficha["media_fuera_foco_especializada"] = round(safe_mean(spec_fuera), 3)
            ficha["delta_fuera"] = round(safe_mean(spec_fuera) - safe_mean(gen_fuera), 3)
        else:
            ficha["media_fuera_foco_generica"] = None
            ficha["media_fuera_foco_especializada"] = None
            ficha["delta_fuera"] = None

        # Top mejora and top retroceso
        cell_avg_deltas = {}
        for celda, deltas in per_cell_deltas.items():
            cell_avg_deltas[celda] = round(safe_mean(deltas), 3)

        if cell_avg_deltas:
            top_mejora_celda = max(cell_avg_deltas, key=cell_avg_deltas.get)
            top_retroceso_celda = min(cell_avg_deltas, key=cell_avg_deltas.get)
            ficha["top_mejora"] = {
                "celda": top_mejora_celda,
                "delta_medio": cell_avg_deltas[top_mejora_celda],
            }
            ficha["top_retroceso"] = {
                "celda": top_retroceso_celda,
                "delta_medio": cell_avg_deltas[top_retroceso_celda],
            }
        else:
            ficha["top_mejora"] = None
            ficha["top_retroceso"] = None

        fichas[model] = ficha

    return fichas


# ── E) Mesa minima actualizada ───────────────────────────────────

def compute_mesa_minima(spec_r1, spec_r2, common_models):
    """Find 2-3 models that cover most cells at highest levels using specialized data."""
    # Compute each model's max score contribution per output x cell
    model_scores = {}
    for m in common_models:
        scores = {}
        for oid in OUTPUT_IDS:
            celdas = get_best_celdas(spec_r1, spec_r2, m, oid)
            if not celdas:
                continue
            for celda in CELDAS_21:
                key = "%s/%s" % (oid, celda)
                scores[key] = get_nivel(celdas, celda)
        model_scores[m] = scores

    # Total cells with score >= 3 with all models
    all_keys = set()
    for oid in OUTPUT_IDS:
        for celda in CELDAS_21:
            all_keys.add("%s/%s" % (oid, celda))

    def coverage_3plus(models):
        count = 0
        for key in all_keys:
            max_score = 0
            for m in models:
                s = model_scores.get(m, {}).get(key, 0)
                if s > max_score:
                    max_score = s
            if max_score >= 3:
                count += 1
        return count

    full_coverage = coverage_3plus(common_models)

    # Greedy: pick model that adds most 3+ cells
    remaining = list(common_models)
    selected = []
    best_combos = []

    for step in range(min(5, len(remaining))):
        best_model = None
        best_count = -1
        for m in remaining:
            candidate = selected + [m]
            c = coverage_3plus(candidate)
            if c > best_count:
                best_count = c
                best_model = m
        if best_model is None:
            break
        selected.append(best_model)
        remaining.remove(best_model)
        pct = round(100.0 * best_count / max(full_coverage, 1), 1)
        best_combos.append({
            "n": len(selected),
            "models": list(selected),
            "celdas_3plus": best_count,
            "pct_of_full": pct,
        })

    # Find smallest n >= 90%
    mesa_min_n = len(common_models)
    mesa_min_models = list(common_models)
    for combo in best_combos:
        if combo["pct_of_full"] >= 90:
            mesa_min_n = combo["n"]
            mesa_min_models = combo["models"]
            break

    return {
        "full_coverage_3plus": full_coverage,
        "curve": best_combos,
        "mesa_minima": {
            "n": mesa_min_n,
            "models": mesa_min_models,
            "celdas_3plus": coverage_3plus(mesa_min_models),
            "pct_of_full": round(100.0 * coverage_3plus(mesa_min_models) / max(full_coverage, 1), 1),
        },
    }


# ── Top improvements: cells that went up 2+ levels ───────────────

def find_top_improvements(gen_r1, gen_r2, spec_r1, spec_r2, common_models):
    """Find cells with biggest collective improvement (max across models)."""
    improvements = []
    for oid in OUTPUT_IDS:
        for celda in CELDAS_21:
            max_gen = 0
            max_spec = 0
            best_gen_model = ""
            best_spec_model = ""
            for m in common_models:
                gen_celdas = get_best_celdas(gen_r1, gen_r2, m, oid)
                if gen_celdas:
                    g = get_nivel(gen_celdas, celda)
                    if g > max_gen:
                        max_gen = g
                        best_gen_model = m
                spec_celdas = get_best_celdas(spec_r1, spec_r2, m, oid)
                if spec_celdas:
                    s = get_nivel(spec_celdas, celda)
                    if s > max_spec:
                        max_spec = s
                        best_spec_model = m

            delta = max_spec - max_gen
            if delta >= 2:
                improvements.append({
                    "output": oid,
                    "celda": celda,
                    "gen_max": max_gen,
                    "spec_max": max_spec,
                    "delta": delta,
                    "gen_best_model": best_gen_model,
                    "spec_best_model": best_spec_model,
                })

    improvements.sort(key=lambda x: -x["delta"])
    return improvements


# ── Generate Reports ─────────────────────────────────────────────

def generate_json_report(per_model_r1, collective_map, collective_summary,
                         per_model_r2, collective_r2_summary,
                         fichas, mesa_minima, top_improvements):
    report = {
        "meta": {
            "experiment": "Exp 4.1 vs Exp 4 - Specialized vs Generic Comparison",
            "description": "Compares specialized prompts (Exp 4.1) vs generic prompts (Exp 4)",
        },
        "A_per_model_r1": per_model_r1,
        "B_collective_map": {
            "summary": collective_summary,
            "detail": collective_map,
        },
        "C_r2_comparison": {
            "per_model": per_model_r2,
            "collective_summary": collective_r2_summary,
        },
        "D_fichas": fichas,
        "E_mesa_minima": mesa_minima,
        "top_improvements_2plus": top_improvements,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("JSON: %s" % REPORT_JSON)


def fmt_delta(v):
    """Format delta with sign."""
    if v is None:
        return "n/a"
    if v >= 0:
        return "+%.3f" % v
    return "%.3f" % v


def fmt_val(v):
    """Format a nullable float."""
    if v is None:
        return "n/a"
    return "%.3f" % v


def generate_md_report(per_model_r1, collective_map, collective_summary,
                       per_model_r2, collective_r2_summary,
                       fichas, mesa_minima, top_improvements, common_models):
    lines = []
    lines.append("# EXP 4.1 vs EXP 4 -- Especializado vs Generico")
    lines.append("")

    # ── Section 1: Per-model delta table (R1) ────────────────────
    lines.append("## 1. Delta por Modelo (R1): Generico vs Especializado")
    lines.append("")
    lines.append("| Modelo | Media Gen | Media Esp | Delta Global | Delta Foco | Delta Fuera |")
    lines.append("|--------|-----------|-----------|--------------|------------|-------------|")
    # Sort by delta descending
    sorted_models = sorted(
        common_models,
        key=lambda m: per_model_r1.get(m, {}).get("delta_global", 0),
        reverse=True,
    )
    for m in sorted_models:
        data = per_model_r1.get(m, {})
        gen = "%.2f" % data.get("nivel_medio_generico", 0)
        esp = "%.2f" % data.get("nivel_medio_especializado", 0)
        d_global = fmt_delta(data.get("delta_global", 0))
        d_foco = fmt_delta(data.get("delta_en_foco"))
        d_fuera = fmt_delta(data.get("delta_fuera_foco"))
        lines.append("| %s | %s | %s | %s | %s | %s |" % (m, gen, esp, d_global, d_foco, d_fuera))
    lines.append("")

    # Aggregate stats
    all_deltas = [per_model_r1[m]["delta_global"] for m in common_models if m in per_model_r1]
    avg_delta = safe_mean(all_deltas)
    n_positive = sum(1 for d in all_deltas if d > 0)
    n_negative = sum(1 for d in all_deltas if d < 0)
    n_zero = sum(1 for d in all_deltas if d == 0)
    lines.append("**Resumen R1:** Delta medio = %s. Mejoran: %d. Empeoran: %d. Igual: %d." % (
        fmt_delta(round(avg_delta, 3)), n_positive, n_negative, n_zero))
    lines.append("")

    # ── Section 2: Mapa colectivo comparado ──────────────────────
    lines.append("## 2. Mapa Colectivo Comparado (Best of R1+R2)")
    lines.append("")
    lines.append("| Metrica | Generico | Especializado | Delta |")
    lines.append("|---------|----------|---------------|-------|")
    lines.append("| Celdas nivel 3+ | %d | %d | %s |" % (
        collective_summary["gen_3plus"],
        collective_summary["spec_3plus"],
        fmt_delta(collective_summary["spec_3plus"] - collective_summary["gen_3plus"]),
    ))
    total_cells = len(OUTPUT_IDS) * len(CELDAS_21)
    lines.append("| Celdas totales | %d | %d | - |" % (total_cells, total_cells))
    lines.append("")
    lines.append("Celdas que suben: **%d**. Celdas que bajan: **%d**. Igual: **%d**." % (
        collective_summary["celdas_up"],
        collective_summary["celdas_down"],
        collective_summary["celdas_equal"],
    ))
    lines.append("")

    # Detailed map: show cells where delta != 0
    changes = []
    for oid in OUTPUT_IDS:
        for celda in CELDAS_21:
            entry = collective_map.get(oid, {}).get(celda, {})
            d = entry.get("delta", 0)
            if d != 0:
                changes.append((oid, celda, entry.get("max_generico", 0), entry.get("max_especializado", 0), d))

    if changes:
        changes.sort(key=lambda x: -x[4])
        lines.append("### Cambios en mapa colectivo (max por celda)")
        lines.append("")
        lines.append("| Output | Celda | Gen Max | Esp Max | Delta |")
        lines.append("|--------|-------|---------|---------|-------|")
        for oid, celda, g, s, d in changes[:30]:
            lines.append("| %s | %s | %d | %d | %s |" % (oid, celda, g, s, fmt_delta(d)))
        if len(changes) > 30:
            lines.append("| ... | ... | ... | ... | ... |")
        lines.append("")

    # ── Section 3: Top mejoras (2+ niveles) ──────────────────────
    lines.append("## 3. Top Mejoras: Celdas que subieron 2+ niveles")
    lines.append("")
    if top_improvements:
        lines.append("| Output | Celda | Gen Max | Esp Max | Delta | Mejor modelo esp |")
        lines.append("|--------|-------|---------|---------|-------|------------------|")
        for imp in top_improvements[:20]:
            lines.append("| %s | %s | %d | %d | +%d | %s |" % (
                imp["output"], imp["celda"], imp["gen_max"], imp["spec_max"],
                imp["delta"], imp["spec_best_model"],
            ))
        lines.append("")
    else:
        lines.append("No se encontraron celdas con mejora >= 2 niveles.")
        lines.append("")

    # ── Section 4: R2 comparison ─────────────────────────────────
    lines.append("## 4. Comparacion R2 (Best of R1+R2) por Modelo")
    lines.append("")
    lines.append("| Modelo | Gen Best | Esp Best | Delta |")
    lines.append("|--------|----------|----------|-------|")
    sorted_models_r2 = sorted(
        common_models,
        key=lambda m: per_model_r2.get(m, {}).get("delta_global", 0),
        reverse=True,
    )
    for m in sorted_models_r2:
        data = per_model_r2.get(m, {})
        gen = "%.2f" % data.get("nivel_medio_generico_best", 0)
        esp = "%.2f" % data.get("nivel_medio_especializado_best", 0)
        d = fmt_delta(data.get("delta_global", 0))
        lines.append("| %s | %s | %s | %s |" % (m, gen, esp, d))
    lines.append("")

    lines.append("**Mapa enriquecido colectivo (R2):** Celdas 3+ gen=%d, esp=%d (%s). Suben=%d, bajan=%d." % (
        collective_r2_summary["gen_3plus"],
        collective_r2_summary["spec_3plus"],
        fmt_delta(collective_r2_summary["spec_3plus"] - collective_r2_summary["gen_3plus"]),
        collective_r2_summary["celdas_up"],
        collective_r2_summary["celdas_down"],
    ))
    lines.append("")

    # ── Section 5: Fichas actualizadas ───────────────────────────
    lines.append("## 5. Fichas Actualizadas por Modelo")
    lines.append("")
    for m in sorted_models:
        f = fichas.get(m, {})
        lines.append("### %s" % m)
        lines.append("")
        lines.append("- Media generica: %s / Media especializada: %s / Delta: %s" % (
            fmt_val(f.get("media_generica")),
            fmt_val(f.get("media_especializada")),
            fmt_delta(f.get("delta")),
        ))

        if f.get("delta_foco") is not None:
            lines.append("- En foco: gen=%s, esp=%s, delta=%s" % (
                fmt_val(f.get("media_en_foco_generica")),
                fmt_val(f.get("media_en_foco_especializada")),
                fmt_delta(f.get("delta_foco")),
            ))
            lines.append("- Fuera foco: gen=%s, esp=%s, delta=%s" % (
                fmt_val(f.get("media_fuera_foco_generica")),
                fmt_val(f.get("media_fuera_foco_especializada")),
                fmt_delta(f.get("delta_fuera")),
            ))
        else:
            lines.append("- Sin foco especifico asignado (cross-celda o cobertura completa)")

        if f.get("top_mejora"):
            lines.append("- Top mejora: %s (delta medio %s)" % (
                f["top_mejora"]["celda"], fmt_delta(f["top_mejora"]["delta_medio"]),
            ))
        if f.get("top_retroceso"):
            lines.append("- Top retroceso: %s (delta medio %s)" % (
                f["top_retroceso"]["celda"], fmt_delta(f["top_retroceso"]["delta_medio"]),
            ))
        lines.append("")

    # ── Section 6: Veredicto ─────────────────────────────────────
    lines.append("## 6. Veredicto: Vale la especializacion?")
    lines.append("")

    # Compute verdict metrics
    n_models = len(common_models)
    n_models_positive_r1 = sum(
        1 for m in common_models
        if per_model_r1.get(m, {}).get("delta_global", 0) > 0
    )
    avg_delta_r1 = safe_mean([per_model_r1[m]["delta_global"] for m in common_models if m in per_model_r1])

    # Focus-specific improvement
    focus_models = [m for m in common_models if has_focus(m)]
    focus_deltas_list = []
    for m in focus_models:
        d = per_model_r1.get(m, {}).get("delta_en_foco")
        if d is not None:
            focus_deltas_list.append(d)
    avg_focus_delta = safe_mean(focus_deltas_list) if focus_deltas_list else 0

    nonfocus_deltas_list = []
    for m in focus_models:
        d = per_model_r1.get(m, {}).get("delta_fuera_foco")
        if d is not None:
            nonfocus_deltas_list.append(d)
    avg_nonfocus_delta = safe_mean(nonfocus_deltas_list) if nonfocus_deltas_list else 0

    map_delta = collective_summary["spec_3plus"] - collective_summary["gen_3plus"]

    if avg_delta_r1 > 0.1 and n_models_positive_r1 > n_models / 2:
        veredicto = "SI, la especializacion vale"
        razon = (
            "Delta medio positivo (+%.3f) y %d/%d modelos mejoran. "
            "La especializacion produce evaluaciones mas profundas."
        ) % (avg_delta_r1, n_models_positive_r1, n_models)
    elif avg_delta_r1 > 0 and map_delta > 0:
        veredicto = "SI, con matices"
        razon = (
            "Delta medio ligeramente positivo (+%.3f) y el mapa colectivo gana %d celdas 3+. "
            "No todos los modelos mejoran pero el efecto agregado es positivo."
        ) % (avg_delta_r1, map_delta)
    elif avg_delta_r1 > -0.05 and avg_focus_delta > 0.1:
        veredicto = "PARCIAL: vale en foco, neutro fuera"
        razon = (
            "Delta global neutro (%.3f) pero delta en celdas de foco positivo (+%.3f). "
            "La especializacion funciona donde se enfoca pero no mejora el resto."
        ) % (avg_delta_r1, avg_focus_delta)
    elif avg_delta_r1 < -0.1:
        veredicto = "NO, la especializacion perjudica"
        razon = (
            "Delta medio negativo (%.3f). "
            "Los prompts especializados reducen la calidad global de las evaluaciones."
        ) % avg_delta_r1
    else:
        veredicto = "NEUTRO: sin efecto claro"
        razon = (
            "Delta medio cercano a cero (%.3f). "
            "La especializacion no produce diferencia significativa."
        ) % avg_delta_r1

    lines.append("**%s**" % veredicto)
    lines.append("")
    lines.append(razon)
    lines.append("")
    lines.append("Datos clave:")
    lines.append("- Delta medio R1: %s" % fmt_delta(round(avg_delta_r1, 3)))
    lines.append("- Modelos que mejoran (R1): %d/%d" % (n_models_positive_r1, n_models))
    lines.append("- Mapa colectivo 3+: gen=%d, esp=%d (delta=%s)" % (
        collective_summary["gen_3plus"],
        collective_summary["spec_3plus"],
        fmt_delta(map_delta),
    ))
    if focus_deltas_list:
        lines.append("- Delta medio en foco (modelos con foco): %s" % fmt_delta(round(avg_focus_delta, 3)))
        lines.append("- Delta medio fuera foco (modelos con foco): %s" % fmt_delta(round(avg_nonfocus_delta, 3)))
    lines.append("")

    # ── Section 7: Protocolo recomendado ─────────────────────────
    lines.append("## 7. Protocolo Recomendado")
    lines.append("")

    if avg_delta_r1 > 0.1:
        lines.append("1. **Usar prompts especializados** para todos los modelos con foco definido")
        lines.append("2. Para modelos sin foco (v3.2-chat, qwen3-235b, opus): mantener prompt generico o cross-celda")
        lines.append("3. R2 de enriquecimiento sigue siendo necesaria para consolidar")
    elif avg_delta_r1 > 0 or avg_focus_delta > 0.1:
        lines.append("1. **Usar prompts especializados SOLO para modelos con foco definido y delta positivo**")
        lines.append("2. Mantener prompt generico para el resto")
        lines.append("3. Modelos recomendados para especializacion:")
        for m in focus_models:
            d = per_model_r1.get(m, {}).get("delta_en_foco")
            if d is not None and d > 0:
                focus_info = MODEL_FOCUS.get(m, {})
                areas = []
                if focus_info.get("lentes"):
                    areas.extend(focus_info["lentes"])
                if focus_info.get("funciones"):
                    areas.extend(focus_info["funciones"])
                lines.append("   - %s (foco: %s, delta foco: %s)" % (m, ", ".join(areas), fmt_delta(d)))
    else:
        lines.append("1. **No especializar** — el prompt generico produce resultados equivalentes o mejores")
        lines.append("2. La diversidad de perspectiva genomerica es mas valiosa que la profundidad focalizada")
        lines.append("3. Invertir esfuerzo en R2 de enriquecimiento en lugar de en tuning de prompts")
    lines.append("")

    # ── Section 8: Mesa minima actualizada ───────────────────────
    lines.append("## 8. Mesa Minima Actualizada (con datos especializados)")
    lines.append("")
    mesa = mesa_minima["mesa_minima"]
    lines.append("**%d modelos** capturan >= 90%% del valor: %s" % (mesa["n"], ", ".join(mesa["models"])))
    lines.append("")
    lines.append("Celdas 3+: %d/%d (%.1f%% del total con %d modelos)" % (
        mesa["celdas_3plus"],
        mesa_minima["full_coverage_3plus"],
        mesa["pct_of_full"],
        mesa["n"],
    ))
    lines.append("")
    lines.append("### Curva de cobertura")
    lines.append("")
    lines.append("| N modelos | Modelos | Celdas 3+ | % del total |")
    lines.append("|-----------|---------|-----------|-------------|")
    for entry in mesa_minima["curve"]:
        lines.append("| %d | %s | %d | %.1f%% |" % (
            entry["n"], ", ".join(entry["models"]), entry["celdas_3plus"], entry["pct_of_full"],
        ))
    lines.append("")

    # ── Footer ───────────────────────────────────────────────────
    lines.append("---")
    lines.append("*Generado por exp4_1_analyze_comparison.py*")

    md = "\n".join(lines)
    with open(REPORT_MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    print("MD: %s" % REPORT_MD)


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=== EXP 4.1 vs EXP 4: SPECIALIZED vs GENERIC ===\n")

    gen_r1, gen_r2, spec_r1, spec_r2, common_models = load_all()
    print("Common models: %d (%s)" % (len(common_models), ", ".join(common_models)))
    print("Outputs: %d (%s)" % (len(OUTPUT_IDS), ", ".join(OUTPUT_IDS)))
    print("")

    # A) Per-model comparison R1
    print("--- A) Per-model R1 comparison ---")
    per_model_r1 = compute_per_model_r1(gen_r1, spec_r1, common_models)
    for m in common_models:
        data = per_model_r1[m]
        print("  %s: gen=%.3f esp=%.3f delta=%s foco=%s fuera=%s" % (
            m,
            data["nivel_medio_generico"],
            data["nivel_medio_especializado"],
            fmt_delta(data["delta_global"]),
            fmt_delta(data["delta_en_foco"]),
            fmt_delta(data["delta_fuera_foco"]),
        ))

    # B) Collective map
    print("\n--- B) Collective map comparison ---")
    collective_map, collective_summary = compute_collective_map(
        gen_r1, gen_r2, spec_r1, spec_r2, common_models)
    print("  Gen 3+: %d, Spec 3+: %d" % (
        collective_summary["gen_3plus"], collective_summary["spec_3plus"]))
    print("  Up: %d, Down: %d, Equal: %d" % (
        collective_summary["celdas_up"], collective_summary["celdas_down"], collective_summary["celdas_equal"]))

    # C) R2 comparison
    print("\n--- C) R2 comparison ---")
    per_model_r2 = compute_per_model_r2(gen_r1, gen_r2, spec_r1, spec_r2, common_models)
    collective_r2_summary = compute_collective_map_r2(gen_r1, gen_r2, spec_r1, spec_r2, common_models)
    for m in common_models:
        data = per_model_r2[m]
        print("  %s: gen_best=%.3f esp_best=%.3f delta=%s" % (
            m,
            data["nivel_medio_generico_best"],
            data["nivel_medio_especializado_best"],
            fmt_delta(data["delta_global"]),
        ))
    print("  Collective R2: gen 3+=%d, spec 3+=%d, up=%d, down=%d" % (
        collective_r2_summary["gen_3plus"],
        collective_r2_summary["spec_3plus"],
        collective_r2_summary["celdas_up"],
        collective_r2_summary["celdas_down"],
    ))

    # D) Fichas
    print("\n--- D) Fichas actualizadas ---")
    fichas = compute_fichas(gen_r1, gen_r2, spec_r1, spec_r2, common_models)
    for m in common_models:
        f = fichas[m]
        print("  %s: gen=%.3f esp=%.3f delta=%s" % (
            m, f["media_generica"], f["media_especializada"], fmt_delta(f["delta"])))
        if f.get("top_mejora"):
            print("    top_mejora: %s (%s)" % (f["top_mejora"]["celda"], fmt_delta(f["top_mejora"]["delta_medio"])))
        if f.get("top_retroceso"):
            print("    top_retroceso: %s (%s)" % (f["top_retroceso"]["celda"], fmt_delta(f["top_retroceso"]["delta_medio"])))

    # E) Mesa minima
    print("\n--- E) Mesa minima ---")
    mesa_minima = compute_mesa_minima(spec_r1, spec_r2, common_models)
    mesa = mesa_minima["mesa_minima"]
    print("  Mesa minima: %d modelos (%s)" % (mesa["n"], ", ".join(mesa["models"])))
    print("  Celdas 3+: %d/%d (%.1f%%)" % (mesa["celdas_3plus"], mesa_minima["full_coverage_3plus"], mesa["pct_of_full"]))
    for entry in mesa_minima["curve"]:
        print("    N=%d: %d celdas 3+ (%.1f%%) %s" % (
            entry["n"], entry["celdas_3plus"], entry["pct_of_full"], ", ".join(entry["models"])))

    # Top improvements
    top_improvements = find_top_improvements(gen_r1, gen_r2, spec_r1, spec_r2, common_models)
    print("\n--- Top improvements (2+ levels) ---")
    if top_improvements:
        for imp in top_improvements[:10]:
            print("  %s/%s: %d -> %d (+%d, by %s)" % (
                imp["output"], imp["celda"], imp["gen_max"], imp["spec_max"],
                imp["delta"], imp["spec_best_model"]))
    else:
        print("  None found")

    # Generate reports
    print("\n--- Generating Reports ---")
    generate_json_report(
        per_model_r1, collective_map, collective_summary,
        per_model_r2, collective_r2_summary,
        fichas, mesa_minima, top_improvements,
    )
    generate_md_report(
        per_model_r1, collective_map, collective_summary,
        per_model_r2, collective_r2_summary,
        fichas, mesa_minima, top_improvements, common_models,
    )
    print("\nDONE")


if __name__ == "__main__":
    main()
