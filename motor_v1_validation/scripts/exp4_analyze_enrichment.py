"""Exp 4: Mesa Redonda — Analisis.
Fichas individuales, ranking de aporte, mapa colectivo, curva de rendimiento, mesa minima.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "results"
R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
FICHAS_FILE = RESULTS_DIR / "exp4_fichas_por_modelo.json"
REPORT_JSON = RESULTS_DIR / "exp4_mesa_redonda_report.json"
REPORT_MD = RESULTS_DIR / "exp4_mesa_redonda_report.md"

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
CELDAS_21 = [f"{l}\u00d7{f}" for l in LENTES for f in FUNCIONES]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]


# ── Helpers ──────────────────────────────────────────────────────

def get_nivel(celdas, celda):
    val = celdas.get(celda, {})
    if isinstance(val, dict):
        return val.get("nivel", 0)
    return 0


def get_celdas_r1(r1, model, oid):
    entry = r1.get(model, {}).get(oid, {})
    return entry.get("celdas", {})


def get_celdas_r2(r2, model, oid):
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


# ── Load Data ────────────────────────────────────────────────────

def load_data():
    with open(R1_FILE, encoding="utf-8") as f:
        r1_data = json.load(f)
    r1 = r1_data.get("evaluaciones", {})

    r2 = {}
    if R2_FILE.exists():
        with open(R2_FILE, encoding="utf-8") as f:
            r2_data = json.load(f)
        r2 = r2_data.get("evaluaciones", {})

    # All models that have at least 1 output in R1
    all_models = sorted(set(list(r1.keys()) + list(r2.keys())))
    return r1, r2, all_models


# ── Ficha Individual ─────────────────────────────────────────────

def compute_ficha(model, r1, r2, all_models):
    ficha = {"modelo": model}

    # R1 metrics
    r1_niveles = []
    r1_cubiertas = 0
    r1_3plus = 0
    r1_outputs = 0
    for oid in OUTPUT_IDS:
        celdas = get_celdas_r1(r1, model, oid)
        if not celdas:
            continue
        r1_outputs += 1
        for c in CELDAS_21:
            n = get_nivel(celdas, c)
            r1_niveles.append(n)
            if n > 0:
                r1_cubiertas += 1
            if n >= 3:
                r1_3plus += 1

    ficha["ronda1"] = {
        "outputs_evaluados": r1_outputs,
        "nivel_medio": round(sum(r1_niveles) / max(len(r1_niveles), 1), 3),
        "celdas_cubiertas": r1_cubiertas,
        "celdas_3plus": r1_3plus,
    }

    # R2 metrics
    r2_niveles = []
    r2_cubiertas = 0
    r2_3plus = 0
    r2_outputs = 0
    has_r2 = False
    for oid in OUTPUT_IDS:
        celdas = get_celdas_r2(r2, model, oid)
        if celdas is None:
            # Use R1 as fallback
            celdas = get_celdas_r1(r1, model, oid)
            if not celdas:
                continue
        else:
            has_r2 = True
        r2_outputs += 1
        for c in CELDAS_21:
            n = get_nivel(celdas, c)
            r2_niveles.append(n)
            if n > 0:
                r2_cubiertas += 1
            if n >= 3:
                r2_3plus += 1

    r2_medio = round(sum(r2_niveles) / max(len(r2_niveles), 1), 3)
    delta = round(r2_medio - ficha["ronda1"]["nivel_medio"], 3)
    ficha["ronda2"] = {
        "has_r2": has_r2,
        "outputs_evaluados": r2_outputs,
        "nivel_medio": r2_medio,
        "celdas_cubiertas": r2_cubiertas,
        "celdas_3plus": r2_3plus,
        "delta_nivel_medio": delta,
    }

    # Aportes unicos (objective: R2 score > max of all others for that cell)
    aportes = []
    for oid in OUTPUT_IDS:
        my_celdas = get_best_celdas(r1, r2, model, oid)
        if not my_celdas:
            continue
        for c in CELDAS_21:
            my_n = get_nivel(my_celdas, c)
            if my_n < 2:
                continue
            max_others = 0
            for other in all_models:
                if other == model:
                    continue
                other_celdas = get_best_celdas(r1, r2, other, oid)
                if other_celdas:
                    max_others = max(max_others, get_nivel(other_celdas, c))
            if my_n > max_others:
                aportes.append({
                    "output": oid,
                    "celda": c,
                    "mi_score": my_n,
                    "max_otros": max_others,
                })

    ficha["aportes_unicos"] = {
        "total": len(aportes),
        "detalle": aportes[:10],  # top 10
    }

    # Absorcion (cells raised from R1 to R2)
    celdas_incorporadas = 0
    de_quien_counts = {}
    for oid in OUTPUT_IDS:
        r2_entry = r2.get(model, {}).get(oid, {})
        if "error" in r2_entry or "evaluacion_enriquecida" not in r2_entry:
            continue
        for inc in r2_entry.get("incorporado_de_otros", []):
            celdas_incorporadas += 1
            de = inc.get("de_quien", "unknown")
            de_quien_counts[de] = de_quien_counts.get(de, 0) + 1

    de_quien_top = max(de_quien_counts, key=de_quien_counts.get) if de_quien_counts else ""
    ficha["absorcion"] = {
        "celdas_incorporadas": celdas_incorporadas,
        "de_quien_mas_incorporo": de_quien_top,
    }

    # Angulos propios
    angulos = 0
    for oid in OUTPUT_IDS:
        r2_entry = r2.get(model, {}).get(oid, {})
        if "error" not in r2_entry:
            angulos += len(r2_entry.get("angulos_diferentes", []))
    ficha["angulos_propios"] = angulos

    # Inflacion: cells raised in R2 beyond all others AND not attributed
    inflacion = 0
    for oid in OUTPUT_IDS:
        r1_celdas = get_celdas_r1(r1, model, oid)
        r2_celdas = get_celdas_r2(r2, model, oid)
        if not r1_celdas or not r2_celdas:
            continue
        # Get attributed cells
        r2_entry = r2.get(model, {}).get(oid, {})
        attributed = set()
        for inc in r2_entry.get("incorporado_de_otros", []):
            attributed.add(inc.get("celda", ""))
        for u in r2_entry.get("mi_aporte_unico", []):
            attributed.add(u.get("celda", ""))

        for c in CELDAS_21:
            r1_n = get_nivel(r1_celdas, c)
            r2_n = get_nivel(r2_celdas, c)
            if r2_n > r1_n and c not in attributed:
                # Check if exceeds consensus
                max_others = 0
                for other in all_models:
                    if other == model:
                        continue
                    oc = get_best_celdas(r1, r2, other, oid)
                    if oc:
                        max_others = max(max_others, get_nivel(oc, c))
                if r2_n > max_others:
                    inflacion += 1
    ficha["inflacion"] = inflacion

    return ficha


def compute_valor(ficha):
    """Valor = aportes_unicos*3 + absorcion*1 + angulos*2 - inflacion*2"""
    return (
        ficha["aportes_unicos"]["total"] * 3
        + ficha["absorcion"]["celdas_incorporadas"] * 1
        + ficha["angulos_propios"] * 2
        - ficha["inflacion"] * 2
    )


# ── Mapa Colectivo ───────────────────────────────────────────────

def compute_collective_map(r1, r2, all_models):
    """For each output x cell: max score, n_models >= 2/3, evidencias."""
    mapa = {}
    for oid in OUTPUT_IDS:
        mapa[oid] = {}
        for c in CELDAS_21:
            scores = []
            evidencias = []
            for m in all_models:
                celdas = get_best_celdas(r1, r2, m, oid)
                if not celdas:
                    continue
                n = get_nivel(celdas, c)
                scores.append(n)
                if n >= 2:
                    ev = celdas.get(c, {})
                    if isinstance(ev, dict):
                        txt = ev.get("evidencia", "")
                        if txt:
                            evidencias.append(f"[{m}] {txt[:100]}")
            mapa[oid][c] = {
                "max_score": max(scores) if scores else 0,
                "n_models_2plus": sum(1 for s in scores if s >= 2),
                "n_models_3plus": sum(1 for s in scores if s >= 3),
                "n_evaluadores": len(scores),
                "evidencias_top": evidencias[:5],
            }
    return mapa


# ── Curva de Rendimiento ─────────────────────────────────────────

def compute_performance_curve(r1, r2, ranking, all_models):
    """With top-N models: total cells level 3+."""
    # Ranking is list of (model_name, ficha) sorted by value desc
    ranked_models = [m for m, _ in ranking]

    curve = []
    for n in range(1, len(ranked_models) + 1):
        subset = ranked_models[:n]
        total_3plus = 0
        for oid in OUTPUT_IDS:
            for c in CELDAS_21:
                max_score = 0
                for m in subset:
                    celdas = get_best_celdas(r1, r2, m, oid)
                    if celdas:
                        max_score = max(max_score, get_nivel(celdas, c))
                if max_score >= 3:
                    total_3plus += 1
        curve.append({
            "n_models": n,
            "models": subset,
            "celdas_3plus": total_3plus,
        })

    # Also compute with all models for reference
    full_3plus = curve[-1]["celdas_3plus"] if curve else 0
    for entry in curve:
        entry["pct_of_full"] = round(100 * entry["celdas_3plus"] / max(full_3plus, 1), 1)

    return curve


# ── Roles: Quien se queda ────────────────────────────────────────

def determine_roles(fichas, collective_map, r1, r2, all_models):
    """Classify: imprescindible, valioso, prescindible, nocivo."""
    # Full 3+ count
    full_3plus = 0
    for oid in OUTPUT_IDS:
        for c in CELDAS_21:
            max_score = 0
            for m in all_models:
                celdas = get_best_celdas(r1, r2, m, oid)
                if celdas:
                    max_score = max(max_score, get_nivel(celdas, c))
            if max_score >= 3:
                full_3plus += 1

    roles = {}
    for model, ficha in fichas.items():
        # Without this model: count 3+ cells
        without_3plus = 0
        for oid in OUTPUT_IDS:
            for c in CELDAS_21:
                max_score = 0
                for m in all_models:
                    if m == model:
                        continue
                    celdas = get_best_celdas(r1, r2, m, oid)
                    if celdas:
                        max_score = max(max_score, get_nivel(celdas, c))
                if max_score >= 3:
                    without_3plus += 1

        loss = full_3plus - without_3plus
        loss_pct = round(100 * loss / max(full_3plus, 1), 1)
        n_aportes = ficha["aportes_unicos"]["total"]

        if loss_pct >= 10:
            role = "imprescindible"
        elif n_aportes >= 2:
            role = "valioso"
        elif ficha["inflacion"] > ficha["aportes_unicos"]["total"]:
            role = "nocivo"
        else:
            role = "prescindible"

        roles[model] = {
            "role": role,
            "loss_3plus": loss,
            "loss_pct": loss_pct,
            "aportes_unicos": n_aportes,
            "inflacion": ficha["inflacion"],
        }
    return roles


# ── Comparacion R1 vs R2 ─────────────────────────────────────────

def compare_rounds(r1, r2, all_models):
    """Compare max(R1) vs max(R2) across all cells."""
    r1_max_3plus = 0
    r2_max_3plus = 0
    emergent = []

    for oid in OUTPUT_IDS:
        for c in CELDAS_21:
            max_r1 = 0
            max_r2 = 0
            for m in all_models:
                r1c = get_celdas_r1(r1, m, oid)
                if r1c:
                    max_r1 = max(max_r1, get_nivel(r1c, c))
                best = get_best_celdas(r1, r2, m, oid)
                if best:
                    max_r2 = max(max_r2, get_nivel(best, c))
            if max_r1 >= 3:
                r1_max_3plus += 1
            if max_r2 >= 3:
                r2_max_3plus += 1
            if max_r2 >= 3 and max_r1 < 3:
                emergent.append({"output": oid, "celda": c, "r1_max": max_r1, "r2_max": max_r2})

    return {
        "r1_celdas_3plus": r1_max_3plus,
        "r2_celdas_3plus": r2_max_3plus,
        "delta_3plus": r2_max_3plus - r1_max_3plus,
        "emergent_count": len(emergent),
        "emergent": emergent[:20],
    }


# ── Mesa Minima Optima ───────────────────────────────────────────

def find_mesa_minima(curve):
    """Smallest N that captures >= 90% of full value."""
    if not curve:
        return 0, []
    for entry in curve:
        if entry["pct_of_full"] >= 90:
            return entry["n_models"], entry["models"]
    last = curve[-1]
    return last["n_models"], last["models"]


# ── Generate Reports ─────────────────────────────────────────────

def generate_json_report(fichas, ranking, collective_map, curve, roles, comparison, mesa_min):
    report = {
        "meta": {"experiment": "Exp 4 - Mesa Redonda"},
        "ranking": [
            {"modelo": m, "valor": compute_valor(f), **f}
            for m, f in ranking
        ],
        "collective_map": collective_map,
        "performance_curve": curve,
        "roles": roles,
        "comparison_r1_r2": comparison,
        "mesa_minima": {"n": mesa_min[0], "models": mesa_min[1]},
    }
    with open(REPORT_JSON, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
    print(f"JSON: {REPORT_JSON}")

    # Fichas separate file
    with open(FICHAS_FILE, "w", encoding="utf-8") as fh:
        json.dump(fichas, fh, ensure_ascii=False, indent=2)
    print(f"Fichas: {FICHAS_FILE}")


def generate_md_report(fichas, ranking, collective_map, curve, roles, comparison, mesa_min):
    lines = ["# EXP 4 \u2014 MESA REDONDA (13 modelos, 2 rondas)", ""]

    # Ranking de aporte
    lines.append("## Ranking de Aporte")
    lines.append("")
    lines.append("| # | Modelo | Valor | R1 medio | R2 medio | \u0394 | 3+ R1 | 3+ R2 | Aportes | Absorcion | Angulos | Inflacion |")
    lines.append("|---|--------|-------|----------|----------|---|-------|-------|---------|-----------|---------|-----------|")
    for i, (m, f) in enumerate(ranking, 1):
        v = compute_valor(f)
        lines.append(
            f"| {i} | {m} | {v} | {f['ronda1']['nivel_medio']:.2f} | "
            f"{f['ronda2']['nivel_medio']:.2f} | {f['ronda2']['delta_nivel_medio']:+.2f} | "
            f"{f['ronda1']['celdas_3plus']} | {f['ronda2']['celdas_3plus']} | "
            f"{f['aportes_unicos']['total']} | {f['absorcion']['celdas_incorporadas']} | "
            f"{f['angulos_propios']} | {f['inflacion']} |"
        )
    lines.append("")

    # Fichas resumidas
    lines.append("## Fichas por Modelo")
    lines.append("")
    for m, f in ranking:
        v = compute_valor(f)
        role = roles.get(m, {}).get("role", "?")
        loss = roles.get(m, {}).get("loss_pct", 0)
        lines.append(f"### {m} ({role})")
        lines.append(
            f"R1: medio={f['ronda1']['nivel_medio']:.2f}, 3+={f['ronda1']['celdas_3plus']}. "
            f"R2: medio={f['ronda2']['nivel_medio']:.2f}, 3+={f['ronda2']['celdas_3plus']} "
            f"(\u0394={f['ronda2']['delta_nivel_medio']:+.2f}). "
            f"Aportes unicos: {f['aportes_unicos']['total']}. "
            f"Absorcion: {f['absorcion']['celdas_incorporadas']} "
            f"(mas de {f['absorcion']['de_quien_mas_incorporo']}). "
            f"Angulos: {f['angulos_propios']}. Inflacion: {f['inflacion']}. "
            f"Valor: {v}. Sin el: pierde {loss}% de celdas 3+."
        )
        lines.append("")

    # Mapa enriquecido colectivo (resumen por output)
    lines.append("## Mapa Enriquecido Colectivo")
    lines.append("")
    for oid in OUTPUT_IDS:
        lines.append(f"### {oid}")
        lines.append("")
        lines.append("| Celda | Max | N\u22652 | N\u22653 |")
        lines.append("|-------|-----|------|------|")
        m = collective_map.get(oid, {})
        for c in CELDAS_21:
            entry = m.get(c, {})
            lines.append(
                f"| {c} | {entry.get('max_score', 0)} | "
                f"{entry.get('n_models_2plus', 0)} | {entry.get('n_models_3plus', 0)} |"
            )
        lines.append("")

    # Curva de rendimiento
    lines.append("## Curva de Rendimiento")
    lines.append("")
    lines.append("| N modelos | Celdas 3+ | % del total |")
    lines.append("|-----------|-----------|-------------|")
    for entry in curve:
        lines.append(
            f"| {entry['n_models']} | {entry['celdas_3plus']} | {entry['pct_of_full']}% |"
        )
    lines.append("")

    # Mesa minima
    lines.append("## Mesa Minima Optima")
    lines.append("")
    lines.append(f"**{mesa_min[0]} modelos** capturan >= 90% del valor: {', '.join(mesa_min[1])}")
    lines.append("")

    # Roles
    lines.append("## Quien se queda")
    lines.append("")
    for role_type in ["imprescindible", "valioso", "prescindible", "nocivo"]:
        members = [m for m, r in roles.items() if r["role"] == role_type]
        if members:
            lines.append(f"**{role_type.title()}**: {', '.join(members)}")
    lines.append("")

    # Comparacion R1 vs R2
    lines.append("## Comparacion Ronda 1 vs Ronda 2")
    lines.append("")
    lines.append(f"- Celdas 3+ con R1: {comparison['r1_celdas_3plus']}")
    lines.append(f"- Celdas 3+ con R2: {comparison['r2_celdas_3plus']}")
    lines.append(f"- Delta: {comparison['delta_3plus']:+d}")
    lines.append(f"- Hallazgos emergentes (solo en R2): {comparison['emergent_count']}")
    lines.append("")
    if comparison["emergent"]:
        lines.append("### Top Hallazgos Emergentes")
        lines.append("")
        for e in comparison["emergent"][:10]:
            lines.append(f"- {e['output']} / {e['celda']}: R1 max={e['r1_max']} -> R2 max={e['r2_max']}")
        lines.append("")

    # Opus question
    lines.append("## Opus: vale la pena?")
    lines.append("")
    if "opus" in fichas:
        of = fichas["opus"]
        or_ = roles.get("opus", {})
        lines.append(
            f"Role: {or_.get('role', '?')}. Aportes unicos: {of['aportes_unicos']['total']}. "
            f"Sin Opus pierde {or_.get('loss_pct', 0)}% de 3+."
        )
    else:
        lines.append("Opus no participo.")
    lines.append("")

    # Sonnet question
    lines.append("## Sonnet como referencia")
    lines.append("")
    if "sonnet" in fichas:
        sf = fichas["sonnet"]
        sr = roles.get("sonnet", {})
        lines.append(
            f"Role: {sr.get('role', '?')}. Aportes unicos: {sf['aportes_unicos']['total']}. "
            f"Sin Sonnet pierde {sr.get('loss_pct', 0)}% de 3+. "
            f"Nivel medio R1: {sf['ronda1']['nivel_medio']:.2f}."
        )
    lines.append("")

    lines.append("---")
    lines.append("*Generado por exp4_analyze_enrichment.py*")

    md = "\n".join(lines)
    with open(REPORT_MD, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"MD: {REPORT_MD}")


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=== EXP 4: ANALISIS MESA REDONDA ===\n")

    r1, r2, all_models = load_data()
    print(f"Models with R1: {len(r1)}")
    print(f"Models with R2: {len(r2)}")

    # Compute fichas
    fichas = {}
    for m in all_models:
        fichas[m] = compute_ficha(m, r1, r2, all_models)

    # Ranking
    ranking = sorted(fichas.items(), key=lambda x: compute_valor(x[1]), reverse=True)
    print("\nRanking:")
    for i, (m, f) in enumerate(ranking, 1):
        print(f"  {i}. {m}: valor={compute_valor(f)}")

    # Collective map
    collective_map = compute_collective_map(r1, r2, all_models)

    # Performance curve
    curve = compute_performance_curve(r1, r2, ranking, all_models)

    # Roles
    roles = determine_roles(fichas, collective_map, r1, r2, all_models)
    print("\nRoles:")
    for m, r in roles.items():
        print(f"  {m}: {r['role']} (pierde {r['loss_pct']}% sin el)")

    # Comparison
    comparison = compare_rounds(r1, r2, all_models)
    print(f"\nR1 3+: {comparison['r1_celdas_3plus']} -> R2 3+: {comparison['r2_celdas_3plus']} "
          f"(delta={comparison['delta_3plus']:+d}, emergentes={comparison['emergent_count']})")

    # Mesa minima
    mesa_min = find_mesa_minima(curve)
    print(f"\nMesa minima: {mesa_min[0]} modelos ({', '.join(mesa_min[1])})")

    # Reports
    print("\n--- Generating Reports ---")
    generate_json_report(fichas, ranking, collective_map, curve, roles, comparison, mesa_min)
    generate_md_report(fichas, ranking, collective_map, curve, roles, comparison, mesa_min)
    print("\nDONE")


if __name__ == "__main__":
    main()
