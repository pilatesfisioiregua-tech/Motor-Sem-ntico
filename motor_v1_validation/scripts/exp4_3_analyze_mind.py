"""Exp 4.3: Mente Distribuida — Analisis.
Convergencia, perfiles de modelo, comparacion con Mesa Redonda y Max Mecanico,
trazabilidad, mente minima, contribuciones mas valiosas, conexiones.
"""
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
PIZARRAS_FILE = RESULTS_DIR / "exp4_3_pizarras_finales.json"
R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
REPORT_JSON = RESULTS_DIR / "exp4_3_mente_distribuida_report.json"
REPORT_MD = RESULTS_DIR / "exp4_3_mente_distribuida_report.md"

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
CELDAS_21 = ["%s\u00d7%s" % (l, f) for l in LENTES for f in FUNCIONES]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]


# ── Helpers ──────────────────────────────────────────────────────

def safe_div(a, b, default=0.0):
    """Division that returns default when denominator is zero."""
    if b == 0:
        return default
    return a / b


def get_nivel(celdas, celda):
    """Extract nivel from a cell dict."""
    val = celdas.get(celda, {})
    if isinstance(val, dict):
        return val.get("nivel", 0)
    return 0


def get_celdas_r1(r1, model, oid):
    """Get celdas from R1 data for a model+output."""
    entry = r1.get(model, {}).get(oid, {})
    return entry.get("celdas", {})


def get_celdas_r2(r2, model, oid):
    """Get celdas from R2 enriched evaluation for a model+output."""
    entry = r2.get(model, {}).get(oid, {})
    if "error" in entry:
        return None
    enriched = entry.get("evaluacion_enriquecida", {})
    return enriched.get("celdas", None)


def get_best_celdas(r1, r2, model, oid):
    """Return R2 celdas if available, else R1."""
    c2 = get_celdas_r2(r2, model, oid)
    if c2:
        return c2
    return get_celdas_r1(r1, model, oid)


def lente_of_cell(cell_name):
    """Extract lente from a cell name like 'Salud x Conservar'."""
    parts = cell_name.split("\u00d7")
    if len(parts) >= 1:
        return parts[0].strip()
    return ""


# ── Load Data ────────────────────────────────────────────────────

def load_data():
    """Load pizarras, R1 and R2 data."""
    with open(PIZARRAS_FILE, encoding="utf-8") as f:
        piz_data = json.load(f)

    pizarras = piz_data.get("pizarras", {})
    contrib_por_modelo = piz_data.get("contribuciones_por_modelo", {})

    r1 = {}
    if R1_FILE.exists():
        with open(R1_FILE, encoding="utf-8") as f:
            r1_data = json.load(f)
        r1 = r1_data.get("evaluaciones", {})

    r2 = {}
    if R2_FILE.exists():
        with open(R2_FILE, encoding="utf-8") as f:
            r2_data = json.load(f)
        r2 = r2_data.get("evaluaciones", {})

    all_r1_models = sorted(set(list(r1.keys()) + list(r2.keys())))
    return pizarras, contrib_por_modelo, r1, r2, all_r1_models


# ── A) Convergencia ──────────────────────────────────────────────

def analyze_convergencia(pizarras):
    """Analyze convergence per output: rondas, cambios, decay ratios."""
    results = {}
    for oid in OUTPUT_IDS:
        if oid not in pizarras:
            continue
        p = pizarras[oid]
        meta = p.get("meta", {})
        cambios = meta.get("cambios_por_ronda", [])
        rondas_total = meta.get("rondas_total", 0)
        convergencia = meta.get("convergencia", False)
        estado = p.get("estado", "desconocido")

        # Compute decay ratios cambios[i+1]/cambios[i]
        ratios = []
        for i in range(len(cambios) - 1):
            if cambios[i] > 0:
                ratios.append(round(safe_div(cambios[i + 1], cambios[i]), 3))
            else:
                ratios.append(None)

        # Is it exponential decay? Check if all ratios < 1 and roughly consistent
        is_exp_decay = False
        valid_ratios = [r for r in ratios if r is not None]
        if len(valid_ratios) >= 2 and all(r < 1.0 for r in valid_ratios):
            is_exp_decay = True

        # Mean decay ratio
        mean_ratio = round(safe_div(sum(valid_ratios), len(valid_ratios)), 3) if valid_ratios else None

        results[oid] = {
            "estado": estado,
            "rondas_total": rondas_total,
            "convergencia": convergencia,
            "cambios_por_ronda": cambios,
            "decay_ratios": ratios,
            "mean_decay_ratio": mean_ratio,
            "is_exponential_decay": is_exp_decay,
        }

    return results


# ── B) Contribucion por modelo ───────────────────────────────────

def analyze_perfiles(contrib_por_modelo):
    """Classify each model's contribution profile."""
    perfiles = {}
    for modelo, stats in contrib_por_modelo.items():
        total_contrib = stats.get("contribuciones_aceptadas", 0)
        total_conn = stats.get("conexiones", 0)
        total_pc = stats.get("puntos_ciegos", 0)
        rondas_activas = stats.get("rondas_activas", 0)
        outputs_part = stats.get("outputs_participados", 0)

        # Gather contribuciones_por_ronda across all outputs
        all_ronda_contribs = []  # list of lists (one per output)
        por_output = stats.get("por_output", {})
        for oid, ostats in por_output.items():
            cpr = ostats.get("contribuciones_por_ronda", [])
            all_ronda_contribs.append(cpr)

        # Aggregate per-ronda across outputs: sum all ronda-0 contribs, ronda-1 contribs, etc.
        max_rondas = max((len(x) for x in all_ronda_contribs), default=0)
        aggregated_per_ronda = []
        for r in range(max_rondas):
            total_r = 0
            for cpr in all_ronda_contribs:
                if r < len(cpr):
                    total_r += cpr[r]
            aggregated_per_ronda.append(total_r)

        # Classify profiles
        profiles = []

        # Sembrador: ronda 0 contributes more than avg of later rounds
        if len(aggregated_per_ronda) >= 2:
            ronda_0 = aggregated_per_ronda[0]
            rest = aggregated_per_ronda[1:]
            rest_avg = safe_div(sum(rest), len(rest))
            if ronda_0 > rest_avg and ronda_0 > 0:
                profiles.append("Sembrador")

        # Profundizador: later rounds avg > ronda 0
        if len(aggregated_per_ronda) >= 2:
            ronda_0 = aggregated_per_ronda[0]
            rest = aggregated_per_ronda[1:]
            rest_avg = safe_div(sum(rest), len(rest))
            if rest_avg > ronda_0 and rest_avg > 0:
                profiles.append("Profundizador")

        # Conector: conexiones > contribuciones * 0.5
        if total_contrib > 0 and total_conn > total_contrib * 0.5:
            profiles.append("Conector")

        # Detector de huecos: puntos_ciegos > contribuciones * 0.3
        if total_contrib > 0 and total_pc > total_contrib * 0.3:
            profiles.append("Detector de huecos")

        if not profiles:
            profiles.append("Generalista")

        perfiles[modelo] = {
            "contribuciones_aceptadas": total_contrib,
            "conexiones": total_conn,
            "puntos_ciegos": total_pc,
            "rondas_activas": rondas_activas,
            "outputs_participados": outputs_part,
            "contribuciones_por_ronda_agregadas": aggregated_per_ronda,
            "perfiles": profiles,
        }

    return perfiles


# ── C) Comparison: Mente Distribuida vs Mesa Redonda vs Max Mecanico ──

def compute_max_mecanico(r1, all_models, oid):
    """Max of all models' R1 scores per cell."""
    result = {}
    for c in CELDAS_21:
        max_n = 0
        for m in all_models:
            celdas = get_celdas_r1(r1, m, oid)
            if celdas:
                max_n = max(max_n, get_nivel(celdas, c))
        result[c] = max_n
    return result


def compute_mesa_redonda(r1, r2, all_models, oid):
    """Max of all models' best (R2 if available, else R1) scores per cell."""
    result = {}
    for c in CELDAS_21:
        max_n = 0
        for m in all_models:
            celdas = get_best_celdas(r1, r2, m, oid)
            if celdas:
                max_n = max(max_n, get_nivel(celdas, c))
        result[c] = max_n
    return result


def compute_mente_distribuida(pizarra):
    """Extract nivel per cell from pizarra."""
    result = {}
    celdas = pizarra.get("celdas", {})
    for c in CELDAS_21:
        result[c] = celdas.get(c, {}).get("nivel", 0)
    return result


def compare_approaches(pizarras, r1, r2, all_models):
    """Compare the three approaches for each output."""
    comparisons = {}
    for oid in OUTPUT_IDS:
        if oid not in pizarras:
            continue

        max_mec = compute_max_mecanico(r1, all_models, oid)
        mesa_red = compute_mesa_redonda(r1, r2, all_models, oid)
        mente_dist = compute_mente_distribuida(pizarras[oid])

        pizarra = pizarras[oid]
        n_conexiones = len(pizarra.get("conexiones", []))
        n_puntos_ciegos = len(pizarra.get("puntos_ciegos", []))

        def metrics(scores_dict, conexiones=0, puntos_ciegos=0):
            vals = list(scores_dict.values())
            cubiertas = sum(1 for v in vals if v > 0)
            n3plus = sum(1 for v in vals if v >= 3)
            medio = round(safe_div(sum(vals), len(vals)), 3)
            return {
                "celdas_cubiertas": cubiertas,
                "celdas_3plus": n3plus,
                "nivel_medio": medio,
                "conexiones": conexiones,
                "puntos_ciegos": puntos_ciegos,
            }

        comparisons[oid] = {
            "max_mecanico": metrics(max_mec),
            "mesa_redonda": metrics(mesa_red),
            "mente_distribuida": metrics(mente_dist, n_conexiones, n_puntos_ciegos),
        }

    # Aggregate across all outputs
    agg = {}
    for approach in ["max_mecanico", "mesa_redonda", "mente_distribuida"]:
        agg[approach] = {
            "celdas_cubiertas": 0,
            "celdas_3plus": 0,
            "nivel_medio_sum": 0.0,
            "conexiones": 0,
            "puntos_ciegos": 0,
            "n_outputs": 0,
        }
    for oid, comp in comparisons.items():
        for approach in ["max_mecanico", "mesa_redonda", "mente_distribuida"]:
            m = comp[approach]
            agg[approach]["celdas_cubiertas"] += m["celdas_cubiertas"]
            agg[approach]["celdas_3plus"] += m["celdas_3plus"]
            agg[approach]["nivel_medio_sum"] += m["nivel_medio"]
            agg[approach]["conexiones"] += m["conexiones"]
            agg[approach]["puntos_ciegos"] += m["puntos_ciegos"]
            agg[approach]["n_outputs"] += 1

    aggregate = {}
    for approach in ["max_mecanico", "mesa_redonda", "mente_distribuida"]:
        a = agg[approach]
        n = max(a["n_outputs"], 1)
        aggregate[approach] = {
            "celdas_cubiertas_total": a["celdas_cubiertas"],
            "celdas_3plus_total": a["celdas_3plus"],
            "nivel_medio_promedio": round(safe_div(a["nivel_medio_sum"], n), 3),
            "conexiones_total": a["conexiones"],
            "puntos_ciegos_total": a["puntos_ciegos"],
        }

    return comparisons, aggregate


# ── D) Trazabilidad: celda mas interesante ───────────────────────

def trace_most_interesting_cell(pizarras):
    """Find the cell with longest nivel_historial in the output with most rondas."""
    # Find output with most rondas
    best_oid = None
    best_rondas = 0
    for oid in OUTPUT_IDS:
        if oid not in pizarras:
            continue
        rondas = pizarras[oid].get("meta", {}).get("rondas_total", 0)
        if rondas > best_rondas:
            best_rondas = rondas
            best_oid = oid

    if not best_oid:
        return None

    pizarra = pizarras[best_oid]
    celdas = pizarra.get("celdas", {})

    # Find cell with longest nivel_historial
    best_cell = None
    best_len = 0
    for cell_name, cell_data in celdas.items():
        historial = cell_data.get("nivel_historial", [])
        if len(historial) > best_len:
            best_len = len(historial)
            best_cell = cell_name

    if not best_cell:
        return None

    cell_data = celdas[best_cell]
    historial = cell_data.get("nivel_historial", [])
    evidencias = cell_data.get("evidencias", [])
    ultima = cell_data.get("ultima_modificacion", {})

    # Build trace
    trace_entries = []
    for ev in evidencias:
        trace_entries.append({
            "modelo": ev.get("fuente", "?"),
            "ronda": ev.get("ronda", "?"),
            "evidencia": ev.get("texto", "")[:200],
        })

    # Determine who seeded (ronda <= 0)
    seeder = None
    for ev in evidencias:
        if ev.get("ronda", 99) <= 0:
            seeder = ev.get("fuente", "?")
            break

    # Level transitions
    transitions = []
    for i in range(1, len(historial)):
        if historial[i] != historial[i - 1]:
            # Find the evidence that corresponds to this transition
            ev_match = None
            for ev in evidencias:
                # Evidencias are in order, try to match by index
                pass
            transitions.append({
                "de": historial[i - 1],
                "a": historial[i],
                "transicion_index": i,
            })

    # Enrich transitions with model info from evidencias
    # evidencias[j] corresponds roughly to nivel_historial transitions
    # (evidencias may include same-level additions too, but we try to match)
    ev_idx = 0
    for t in transitions:
        while ev_idx < len(evidencias):
            ev = evidencias[ev_idx]
            ev_idx += 1
            # This evidence likely caused this level change
            t["modelo"] = ev.get("fuente", "?")
            t["ronda"] = ev.get("ronda", "?")
            t["evidencia"] = ev.get("texto", "")[:150]
            break

    return {
        "output": best_oid,
        "celda": best_cell,
        "nivel_final": cell_data.get("nivel", 0),
        "nivel_historial": historial,
        "n_cambios": len(historial) - 1,
        "seeder": seeder,
        "ultima_modificacion": ultima,
        "transitions": transitions,
        "all_evidencias": trace_entries,
    }


# ── E) Mente Minima ─────────────────────────────────────────────

def analyze_mente_minima(pizarras, contrib_por_modelo):
    """Simulate: with top N models (3, 5, 7), what % of cells are covered?"""
    # Rank models by total contribuciones_aceptadas
    ranked = sorted(
        contrib_por_modelo.items(),
        key=lambda x: x[1].get("contribuciones_aceptadas", 0),
        reverse=True
    )
    ranked_names = [m for m, _ in ranked]

    results = {}
    for n in [3, 5, 7]:
        top_n = set(ranked_names[:n])

        total_cells = 0
        covered_cells = 0

        for oid in OUTPUT_IDS:
            if oid not in pizarras:
                continue
            celdas = pizarras[oid].get("celdas", {})
            for cell_name in CELDAS_21:
                cell_data = celdas.get(cell_name, {})
                if cell_data.get("nivel", 0) == 0:
                    continue
                total_cells += 1
                ultima = cell_data.get("ultima_modificacion", {})
                if ultima and ultima.get("modelo", "") in top_n:
                    covered_cells += 1
                elif ultima and ultima.get("modelo", "") == "sonnet":
                    # Sonnet seeded, check if any top-N model contributed
                    evidencias = cell_data.get("evidencias", [])
                    for ev in evidencias:
                        if ev.get("fuente", "") in top_n:
                            covered_cells += 1
                            break

        pct = round(safe_div(covered_cells * 100.0, total_cells), 1)
        results[n] = {
            "top_n_models": ranked_names[:n],
            "celdas_con_nivel": total_cells,
            "celdas_cubiertas_por_top_n": covered_cells,
            "pct_cubierto": pct,
        }

    # Recommendation
    recommended = None
    for n in [3, 5, 7]:
        if results[n]["pct_cubierto"] >= 80.0:
            recommended = n
            break
    if recommended is None:
        recommended = 7

    return {
        "ranking_modelos": ranked_names,
        "simulaciones": results,
        "recomendacion": {
            "n_minimo": recommended,
            "modelos": ranked_names[:recommended],
            "pct_cubierto": results[recommended]["pct_cubierto"],
        },
    }


# ── F) Top 5 contribuciones mas valiosas ─────────────────────────

def find_top_contributions(pizarras):
    """Find the 5 evidencias that caused the biggest jump in nivel_historial."""
    candidates = []

    for oid in OUTPUT_IDS:
        if oid not in pizarras:
            continue
        celdas = pizarras[oid].get("celdas", {})
        for cell_name, cell_data in celdas.items():
            historial = cell_data.get("nivel_historial", [])
            evidencias = cell_data.get("evidencias", [])

            # Find jumps in historial and match to evidencias
            # historial[0] is always 0 (empty), then each append corresponds
            # to a level change (or seed). evidencias are appended on each change.
            ev_idx = 0
            for i in range(1, len(historial)):
                jump = historial[i] - historial[i - 1]
                if jump > 0 and ev_idx < len(evidencias):
                    ev = evidencias[ev_idx]
                    candidates.append({
                        "output": oid,
                        "celda": cell_name,
                        "de": historial[i - 1],
                        "a": historial[i],
                        "salto": jump,
                        "modelo": ev.get("fuente", "?"),
                        "ronda": ev.get("ronda", "?"),
                        "evidencia": ev.get("texto", "")[:200],
                    })
                ev_idx += 1

    # Sort by biggest jump, then by final level
    candidates.sort(key=lambda x: (x["salto"], x["a"]), reverse=True)
    return candidates[:5]


# ── G) Top 5 conexiones mas interesantes ─────────────────────────

def find_top_connections(pizarras):
    """Find 5 cross-lente connections (celda_a and celda_b have different lentes)."""
    cross_lente = []

    for oid in OUTPUT_IDS:
        if oid not in pizarras:
            continue
        conexiones = pizarras[oid].get("conexiones", [])
        for conn in conexiones:
            celda_a = conn.get("celda_a", "")
            celda_b = conn.get("celda_b", "")
            lente_a = lente_of_cell(celda_a)
            lente_b = lente_of_cell(celda_b)
            if lente_a and lente_b and lente_a != lente_b:
                cross_lente.append({
                    "output": oid,
                    "celda_a": celda_a,
                    "celda_b": celda_b,
                    "lente_a": lente_a,
                    "lente_b": lente_b,
                    "conexion": conn.get("conexion", ""),
                    "modelo": conn.get("fuente", "?"),
                    "ronda": conn.get("ronda", "?"),
                })

    # If not enough cross-lente, add same-lente ones
    if len(cross_lente) < 5:
        for oid in OUTPUT_IDS:
            if oid not in pizarras:
                continue
            conexiones = pizarras[oid].get("conexiones", [])
            for conn in conexiones:
                celda_a = conn.get("celda_a", "")
                celda_b = conn.get("celda_b", "")
                lente_a = lente_of_cell(celda_a)
                lente_b = lente_of_cell(celda_b)
                if lente_a == lente_b:
                    cross_lente.append({
                        "output": oid,
                        "celda_a": celda_a,
                        "celda_b": celda_b,
                        "lente_a": lente_a,
                        "lente_b": lente_b,
                        "conexion": conn.get("conexion", ""),
                        "modelo": conn.get("fuente", "?"),
                        "ronda": conn.get("ronda", "?"),
                    })
                if len(cross_lente) >= 5:
                    break
            if len(cross_lente) >= 5:
                break

    return cross_lente[:5]


# ── Generate JSON Report ─────────────────────────────────────────

def generate_json_report(convergencia, perfiles, comparisons, aggregate,
                         trace, mente_minima, top_contribs, top_conns):
    """Write full JSON report."""
    report = {
        "meta": {"experiment": "Exp 4.3 - Mente Distribuida - Analisis"},
        "convergencia": convergencia,
        "perfiles_por_modelo": perfiles,
        "comparacion_por_output": comparisons,
        "comparacion_agregada": aggregate,
        "trazabilidad_celda_mas_interesante": trace,
        "mente_minima": mente_minima,
        "top_5_contribuciones": top_contribs,
        "top_5_conexiones": top_conns,
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print("JSON: %s" % REPORT_JSON)
    return report


# ── Generate MD Report ───────────────────────────────────────────

def generate_md_report(convergencia, perfiles, comparisons, aggregate,
                       trace, mente_minima, top_contribs, top_conns):
    """Write human-readable Markdown report."""
    lines = ["# EXP 4.3 — MENTE DISTRIBUIDA (Analisis)", ""]

    # ── Convergencia por output ──
    lines.append("## A) Convergencia por Output")
    lines.append("")
    lines.append("| Output | Estado | Rondas | Cambios por ronda | Ratio medio | Decay exp? |")
    lines.append("|--------|--------|--------|-------------------|-------------|------------|")
    for oid in OUTPUT_IDS:
        if oid not in convergencia:
            continue
        c = convergencia[oid]
        cambios_str = ", ".join(str(x) for x in c["cambios_por_ronda"])
        ratio_str = "%.3f" % c["mean_decay_ratio"] if c["mean_decay_ratio"] is not None else "N/A"
        decay_str = "Si" if c["is_exponential_decay"] else "No"
        lines.append("| %s | %s | %d | [%s] | %s | %s |" % (
            oid, c["estado"], c["rondas_total"], cambios_str, ratio_str, decay_str
        ))
    lines.append("")

    # Cambios curve (ASCII)
    lines.append("### Curvas de cambios")
    lines.append("")
    for oid in OUTPUT_IDS:
        if oid not in convergencia:
            continue
        c = convergencia[oid]
        cambios = c["cambios_por_ronda"]
        if not cambios:
            continue
        max_c = max(cambios) if cambios else 1
        lines.append("**%s** (max=%d):" % (oid, max_c))
        lines.append("```")
        for i, val in enumerate(cambios):
            bar_len = int(round(safe_div(val * 40.0, max(max_c, 1))))
            bar = "#" * bar_len
            lines.append("  R%d: %s %d" % (i, bar, val))
        lines.append("```")
        lines.append("")

    # ── Perfil de cada modelo ──
    lines.append("## B) Perfil de Cada Modelo")
    lines.append("")
    lines.append("| Modelo | Contribuciones | Conexiones | P.Ciegos | Rondas activas | Perfiles |")
    lines.append("|--------|---------------|------------|----------|----------------|----------|")

    # Sort by contributions desc
    sorted_perfiles = sorted(perfiles.items(), key=lambda x: x[1]["contribuciones_aceptadas"], reverse=True)
    for modelo, p in sorted_perfiles:
        perfiles_str = ", ".join(p["perfiles"])
        lines.append("| %s | %d | %d | %d | %d | %s |" % (
            modelo,
            p["contribuciones_aceptadas"],
            p["conexiones"],
            p["puntos_ciegos"],
            p["rondas_activas"],
            perfiles_str,
        ))
    lines.append("")

    # Detail per-ronda aggregated
    lines.append("### Contribuciones por ronda (agregadas)")
    lines.append("")
    for modelo, p in sorted_perfiles:
        cpr = p["contribuciones_por_ronda_agregadas"]
        if cpr:
            cpr_str = ", ".join(str(x) for x in cpr)
            lines.append("- **%s**: [%s]" % (modelo, cpr_str))
    lines.append("")

    # ── Comparacion ──
    lines.append("## C) Comparacion: Mente Distribuida vs Mesa Redonda vs Max Mecanico")
    lines.append("")

    for oid in OUTPUT_IDS:
        if oid not in comparisons:
            continue
        comp = comparisons[oid]
        lines.append("### %s" % oid)
        lines.append("")
        lines.append("| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |")
        lines.append("|---------|-------------|-------------|-------------------|")

        for metric_key, metric_label in [
            ("celdas_cubiertas", "Celdas cubiertas (>0)"),
            ("celdas_3plus", "Celdas nivel 3+"),
            ("nivel_medio", "Nivel medio"),
            ("conexiones", "Conexiones"),
            ("puntos_ciegos", "Puntos ciegos detectados"),
        ]:
            mm = comp["max_mecanico"][metric_key]
            mr = comp["mesa_redonda"][metric_key]
            md = comp["mente_distribuida"][metric_key]
            if metric_key == "nivel_medio":
                lines.append("| %s | %.2f | %.2f | %.2f |" % (metric_label, mm, mr, md))
            else:
                lines.append("| %s | %s | %s | %s |" % (metric_label, mm, mr, md))
        lines.append("")

    # Aggregate
    lines.append("### Agregado (todos los outputs)")
    lines.append("")
    lines.append("| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |")
    lines.append("|---------|-------------|-------------|-------------------|")
    for metric_key, metric_label in [
        ("celdas_cubiertas_total", "Celdas cubiertas total"),
        ("celdas_3plus_total", "Celdas 3+ total"),
        ("nivel_medio_promedio", "Nivel medio promedio"),
        ("conexiones_total", "Conexiones total"),
        ("puntos_ciegos_total", "Puntos ciegos total"),
    ]:
        mm = aggregate["max_mecanico"][metric_key]
        mr = aggregate["mesa_redonda"][metric_key]
        md = aggregate["mente_distribuida"][metric_key]
        if "medio" in metric_key:
            lines.append("| %s | %.3f | %.3f | %.3f |" % (metric_label, mm, mr, md))
        else:
            lines.append("| %s | %s | %s | %s |" % (metric_label, mm, mr, md))
    lines.append("")

    # ── Top 5 contribuciones ──
    lines.append("## D) Top 5 Contribuciones Mas Valiosas")
    lines.append("")
    if top_contribs:
        for i, tc in enumerate(top_contribs, 1):
            lines.append("**%d. %s / %s** (salto: %d -> %d, +%d)" % (
                i, tc["output"], tc["celda"], tc["de"], tc["a"], tc["salto"]
            ))
            lines.append("- Modelo: %s (ronda %s)" % (tc["modelo"], tc["ronda"]))
            lines.append("- Evidencia: %s" % tc["evidencia"][:150])
            lines.append("")
    else:
        lines.append("No se encontraron contribuciones con salto de nivel.")
        lines.append("")

    # ── Top 5 conexiones ──
    lines.append("## E) Top 5 Conexiones Mas Interesantes")
    lines.append("")
    if top_conns:
        for i, tc in enumerate(top_conns, 1):
            cross = "(cross-lente: %s <-> %s)" % (tc["lente_a"], tc["lente_b"]) if tc["lente_a"] != tc["lente_b"] else "(intra-lente)"
            lines.append("**%d. %s <-> %s** %s" % (i, tc["celda_a"], tc["celda_b"], cross))
            lines.append("- Modelo: %s (ronda %s, output: %s)" % (tc["modelo"], tc["ronda"], tc["output"]))
            lines.append("- Conexion: %s" % tc["conexion"][:200])
            lines.append("")
    else:
        lines.append("No se encontraron conexiones.")
        lines.append("")

    # ── Trazabilidad ──
    lines.append("## F) Historia de la Celda Mas Disputada")
    lines.append("")
    if trace:
        lines.append("**Output**: %s" % trace["output"])
        lines.append("**Celda**: %s" % trace["celda"])
        lines.append("**Nivel final**: %d" % trace["nivel_final"])
        lines.append("**Historial de niveles**: %s" % trace["nivel_historial"])
        lines.append("**Semilla**: %s" % (trace["seeder"] if trace["seeder"] else "ninguna"))
        lines.append("")
        lines.append("### Transiciones")
        lines.append("")
        for t in trace.get("transitions", []):
            lines.append("- Nivel %d -> %d por **%s** (ronda %s)" % (
                t["de"], t["a"], t.get("modelo", "?"), t.get("ronda", "?")
            ))
            if t.get("evidencia"):
                lines.append("  > %s" % t["evidencia"][:150])
        lines.append("")
        lines.append("### Todas las evidencias")
        lines.append("")
        for ev in trace.get("all_evidencias", []):
            lines.append("- [%s, ronda %s] %s" % (ev["modelo"], ev["ronda"], ev["evidencia"][:150]))
        lines.append("")
    else:
        lines.append("No hay datos de trazabilidad.")
        lines.append("")

    # ── Mente minima ──
    lines.append("## G) Mente Minima Recomendada")
    lines.append("")
    mm = mente_minima
    lines.append("| N modelos | Modelos | Celdas cubiertas | % del total |")
    lines.append("|-----------|---------|-----------------|-------------|")
    for n in [3, 5, 7]:
        sim = mm["simulaciones"][n]
        modelos_str = ", ".join(sim["top_n_models"])
        lines.append("| %d | %s | %d/%d | %.1f%% |" % (
            n, modelos_str, sim["celdas_cubiertas_por_top_n"],
            sim["celdas_con_nivel"], sim["pct_cubierto"]
        ))
    lines.append("")
    rec = mm["recomendacion"]
    lines.append("**Recomendacion**: %d modelos capturan %.1f%% del resultado: %s" % (
        rec["n_minimo"], rec["pct_cubierto"], ", ".join(rec["modelos"])
    ))
    lines.append("")

    # ── Veredicto ──
    lines.append("## H) Veredicto: Produce la Mente Distribuida Resultado Cualitativamente Diferente?")
    lines.append("")

    # Compute delta metrics for verdict
    agg_mm = aggregate["max_mecanico"]
    agg_mr = aggregate["mesa_redonda"]
    agg_md = aggregate["mente_distribuida"]

    delta_3plus_vs_mm = agg_md["celdas_3plus_total"] - agg_mm["celdas_3plus_total"]
    delta_3plus_vs_mr = agg_md["celdas_3plus_total"] - agg_mr["celdas_3plus_total"]
    delta_medio_vs_mm = agg_md["nivel_medio_promedio"] - agg_mm["nivel_medio_promedio"]
    delta_medio_vs_mr = agg_md["nivel_medio_promedio"] - agg_mr["nivel_medio_promedio"]

    lines.append("### Datos cuantitativos")
    lines.append("")
    lines.append("- Celdas 3+ vs Max Mecanico: %+d" % delta_3plus_vs_mm)
    lines.append("- Celdas 3+ vs Mesa Redonda: %+d" % delta_3plus_vs_mr)
    lines.append("- Nivel medio vs Max Mecanico: %+.3f" % delta_medio_vs_mm)
    lines.append("- Nivel medio vs Mesa Redonda: %+.3f" % delta_medio_vs_mr)
    lines.append("- Conexiones detectadas (exclusivo de Mente Distribuida): %d" % agg_md["conexiones_total"])
    lines.append("- Puntos ciegos detectados (exclusivo de Mente Distribuida): %d" % agg_md["puntos_ciegos_total"])
    lines.append("")

    # Qualitative verdict
    has_quantitative_advantage = delta_3plus_vs_mr > 0 or delta_medio_vs_mr > 0.1
    has_qualitative_advantage = agg_md["conexiones_total"] > 0 or agg_md["puntos_ciegos_total"] > 0
    n_profiles = set()
    for p in perfiles.values():
        for prof in p["perfiles"]:
            n_profiles.add(prof)

    lines.append("### Veredicto")
    lines.append("")
    if has_quantitative_advantage and has_qualitative_advantage:
        lines.append(
            "**SI, cualitativamente diferente.** La Mente Distribuida supera tanto en metricas "
            "cuantitativas (nivel medio, celdas 3+) como en dimensiones que los otros enfoques "
            "no capturan: %d conexiones entre celdas y %d puntos ciegos detectados. "
            "Los modelos exhiben %d perfiles diferenciados (%s), "
            "lo que sugiere especializacion emergente." % (
                agg_md["conexiones_total"], agg_md["puntos_ciegos_total"],
                len(n_profiles), ", ".join(sorted(n_profiles))
            )
        )
    elif has_qualitative_advantage:
        lines.append(
            "**PARCIALMENTE diferente.** La Mente Distribuida no supera claramente en metricas "
            "cuantitativas, pero aporta dimensiones nuevas: %d conexiones entre celdas y "
            "%d puntos ciegos que los otros enfoques no detectan. "
            "El valor es cualitativo, no cuantitativo." % (
                agg_md["conexiones_total"], agg_md["puntos_ciegos_total"]
            )
        )
    elif has_quantitative_advantage:
        lines.append(
            "**Cuantitativamente mejor, cualitativamente similar.** La Mente Distribuida "
            "mejora los numeros pero no aporta dimensiones nuevas significativas."
        )
    else:
        lines.append(
            "**NO claramente diferente.** La Mente Distribuida no supera de forma consistente "
            "a la Mesa Redonda ni al Max Mecanico. El coste computacional adicional "
            "(multiples rondas, todos los modelos) no se justifica con estos datos."
        )
    lines.append("")

    # Convergence verdict
    all_converged = all(
        convergencia.get(oid, {}).get("convergencia", False)
        for oid in OUTPUT_IDS if oid in convergencia
    )
    avg_rondas = safe_div(
        sum(convergencia.get(oid, {}).get("rondas_total", 0) for oid in OUTPUT_IDS if oid in convergencia),
        sum(1 for oid in OUTPUT_IDS if oid in convergencia)
    )
    lines.append("### Convergencia")
    lines.append("")
    if all_converged:
        lines.append(
            "Todos los outputs convergieron (media %.1f rondas). "
            "El mecanismo de pizarra compartida converge de forma fiable." % avg_rondas
        )
    else:
        n_conv = sum(1 for oid in OUTPUT_IDS if oid in convergencia and convergencia[oid].get("convergencia", False))
        n_total = sum(1 for oid in OUTPUT_IDS if oid in convergencia)
        lines.append(
            "%d/%d outputs convergieron (media %.1f rondas). "
            "La convergencia no esta garantizada." % (n_conv, n_total, avg_rondas)
        )
    lines.append("")

    lines.append("---")
    lines.append("*Generado por exp4_3_analyze_mind.py*")

    md = "\n".join(lines)
    with open(REPORT_MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    print("MD: %s" % REPORT_MD)


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=== EXP 4.3: ANALISIS MENTE DISTRIBUIDA ===\n")

    pizarras, contrib_por_modelo, r1, r2, all_r1_models = load_data()
    n_pizarras = len(pizarras)
    n_modelos_contrib = len(contrib_por_modelo)
    n_r1 = len(r1)
    n_r2 = len(r2)
    print("Pizarras: %d outputs" % n_pizarras)
    print("Modelos con contribuciones: %d" % n_modelos_contrib)
    print("Modelos R1 (comparacion): %d" % n_r1)
    print("Modelos R2 (comparacion): %d" % n_r2)

    # A) Convergencia
    print("\n--- A) Convergencia ---")
    convergencia = analyze_convergencia(pizarras)
    for oid, c in convergencia.items():
        cambios_str = ", ".join(str(x) for x in c["cambios_por_ronda"])
        print("  %s: %s en %d rondas, cambios=[%s], ratio=%.3f, exp_decay=%s" % (
            oid, c["estado"], c["rondas_total"], cambios_str,
            c["mean_decay_ratio"] if c["mean_decay_ratio"] is not None else 0,
            c["is_exponential_decay"],
        ))

    # B) Perfiles
    print("\n--- B) Perfiles ---")
    perfiles = analyze_perfiles(contrib_por_modelo)
    sorted_p = sorted(perfiles.items(), key=lambda x: x[1]["contribuciones_aceptadas"], reverse=True)
    for modelo, p in sorted_p:
        print("  %s: %d contribs, %d conn, %d pc -> %s" % (
            modelo, p["contribuciones_aceptadas"], p["conexiones"],
            p["puntos_ciegos"], ", ".join(p["perfiles"])
        ))

    # C) Comparacion
    print("\n--- C) Comparacion ---")
    comparisons, aggregate = compare_approaches(pizarras, r1, r2, all_r1_models)
    for oid, comp in comparisons.items():
        mm = comp["max_mecanico"]
        mr = comp["mesa_redonda"]
        md = comp["mente_distribuida"]
        print("  %s: 3+ MM=%d MR=%d MD=%d | medio MM=%.2f MR=%.2f MD=%.2f | conn=%d pc=%d" % (
            oid,
            mm["celdas_3plus"], mr["celdas_3plus"], md["celdas_3plus"],
            mm["nivel_medio"], mr["nivel_medio"], md["nivel_medio"],
            md["conexiones"], md["puntos_ciegos"],
        ))

    # D) Trazabilidad
    print("\n--- D) Trazabilidad ---")
    trace = trace_most_interesting_cell(pizarras)
    if trace:
        print("  Output: %s, Celda: %s, Nivel: %d, Historial: %s" % (
            trace["output"], trace["celda"], trace["nivel_final"], trace["nivel_historial"]
        ))
        print("  Seeder: %s, Transiciones: %d" % (trace["seeder"], len(trace["transitions"])))
    else:
        print("  No trace data available")

    # E) Mente minima
    print("\n--- E) Mente Minima ---")
    mente_minima = analyze_mente_minima(pizarras, contrib_por_modelo)
    for n in [3, 5, 7]:
        sim = mente_minima["simulaciones"][n]
        print("  Top %d: %d/%d celdas (%.1f%%) -> %s" % (
            n, sim["celdas_cubiertas_por_top_n"], sim["celdas_con_nivel"],
            sim["pct_cubierto"], ", ".join(sim["top_n_models"])
        ))
    rec = mente_minima["recomendacion"]
    print("  Recomendacion: %d modelos (%.1f%%)" % (rec["n_minimo"], rec["pct_cubierto"]))

    # F) Top contribuciones
    print("\n--- F) Top 5 Contribuciones ---")
    top_contribs = find_top_contributions(pizarras)
    for i, tc in enumerate(top_contribs, 1):
        print("  %d. %s/%s: %d->%d (+%d) por %s (R%s)" % (
            i, tc["output"], tc["celda"], tc["de"], tc["a"], tc["salto"],
            tc["modelo"], tc["ronda"],
        ))

    # G) Top conexiones
    print("\n--- G) Top 5 Conexiones ---")
    top_conns = find_top_connections(pizarras)
    for i, tc in enumerate(top_conns, 1):
        cross = "CROSS" if tc["lente_a"] != tc["lente_b"] else "intra"
        print("  %d. [%s] %s <-> %s por %s (%s)" % (
            i, cross, tc["celda_a"], tc["celda_b"], tc["modelo"], tc["output"],
        ))

    # Generate reports
    print("\n--- Generating Reports ---")
    generate_json_report(convergencia, perfiles, comparisons, aggregate,
                         trace, mente_minima, top_contribs, top_conns)
    generate_md_report(convergencia, perfiles, comparisons, aggregate,
                       trace, mente_minima, top_contribs, top_conns)

    print("\nDONE")


if __name__ == "__main__":
    main()
