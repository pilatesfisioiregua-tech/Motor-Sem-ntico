"""Paso 3: Genera reporte con matriz modelo × variante."""
import json
import sys
from datetime import datetime
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"

DIM_NAMES = {
    "cobertura": "Cobertura",
    "profundidad": "Profundidad",
    "hallazgos_exclusivos": "Hallazgos excl.",
    "errores_factuales": "Sin errores",
    "cierre_gap": "Gap closure",
}
DIMS = list(DIM_NAMES.keys())

CASE_NAMES = {
    "clinica_dental": "Clínica Dental",
    "startup_saas": "Startup SaaS",
    "cambio_carrera": "Cambio Carrera",
}
INT_NAMES = {
    "INT-01": "Lógico-Mat.",
    "INT-08": "Social",
    "INT-16": "Constructiva",
}


def load():
    path = OUTPUT_DIR / "all_evaluations.json"
    if not path.exists():
        print("ERROR: No se encontró all_evaluations.json")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def valid_evals(evals):
    return [
        e for e in evals
        if "error" not in e and "error" not in e.get("evaluacion", {})
    ]


def avg_score(evals, dim):
    scores = [e["evaluacion"][dim]["score"] for e in evals if dim in e["evaluacion"]]
    return sum(scores) / len(scores) if scores else 0


def generate(evals):
    good = valid_evals(evals)
    if not good:
        return "# ERROR: Sin evaluaciones válidas."

    models = sorted(set(e.get("model_key", "70B") for e in good))
    variants = sorted(set(e.get("variant", "A") for e in good))

    lines = []
    lines.append("# MOTOR v1 — VALIDACIÓN EXPANDIDA")
    lines.append("")
    lines.append(f"**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Modelos:** {', '.join(models)}")
    lines.append(f"**Variantes:** {', '.join(variants)}")
    lines.append(f"**Evaluaciones válidas:** {len(good)}")
    lines.append("")
    lines.append("**Variantes:**")
    lines.append("- A: Solo preguntas (sin identidad de inteligencia)")
    lines.append("- B: + firma + punto ciego")
    lines.append("- C: B + instrucción analítica (extraer magnitudes, ecuaciones, restricciones)")
    lines.append("- D: B + dependencias entre pasos")
    lines.append("- E: Completa (B + C + D + instrucciones por lente)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── MATRIZ PRINCIPAL: modelo × variante (gap closure) ──
    lines.append("## 1. MATRIZ GAP CLOSURE — Modelo × Variante")
    lines.append("")

    # Header
    header = "| Modelo |"
    sep = "|--------|"
    for v in variants:
        header += f" {v} |"
        sep += "------|"
    lines.append(header)
    lines.append(sep)

    # Data rows
    best_score = 0
    best_cell = ""
    for m in models:
        row = f"| **{m}** |"
        for v in variants:
            cell_evals = [e for e in good if e.get("model_key") == m and e.get("variant") == v]
            if cell_evals:
                score = avg_score(cell_evals, "cierre_gap")
                pct = score * 10
                row += f" {pct:.0f}% |"
                if score > best_score:
                    best_score = score
                    best_cell = f"{m}/{v}"
            else:
                row += " — |"
        lines.append(row)

    lines.append("")
    lines.append(f"**Mejor celda:** {best_cell} ({best_score*10:.0f}%)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── MATRIZ COMPLETA: todas las dimensiones ──
    lines.append("## 2. SCORES POR DIMENSIÓN — Modelo × Variante")
    lines.append("")

    for dim in DIMS:
        lines.append(f"### {DIM_NAMES[dim]}")
        lines.append("")
        header = "| Modelo |"
        sep = "|--------|"
        for v in variants:
            header += f" {v} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        for m in models:
            row = f"| {m} |"
            for v in variants:
                cell = [e for e in good if e.get("model_key") == m and e.get("variant") == v]
                if cell:
                    s = avg_score(cell, dim)
                    row += f" {s:.1f} |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── POR INTELIGENCIA ──
    lines.append("## 3. GAP CLOSURE POR INTELIGENCIA")
    lines.append("")

    for int_id in sorted(INT_NAMES.keys()):
        lines.append(f"### {int_id} ({INT_NAMES[int_id]})")
        lines.append("")
        header = "| Modelo |"
        sep = "|--------|"
        for v in variants:
            header += f" {v} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        for m in models:
            row = f"| {m} |"
            for v in variants:
                cell = [e for e in good if e.get("model_key") == m and e.get("variant") == v and e["int_id"] == int_id]
                if cell:
                    s = avg_score(cell, "cierre_gap")
                    row += f" {s*10:.0f}% |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── POR CASO ──
    lines.append("## 4. GAP CLOSURE POR CASO")
    lines.append("")

    for case_id in sorted(CASE_NAMES.keys()):
        lines.append(f"### {CASE_NAMES[case_id]}")
        lines.append("")
        header = "| Modelo |"
        sep = "|--------|"
        for v in variants:
            header += f" {v} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        for m in models:
            row = f"| {m} |"
            for v in variants:
                cell = [e for e in good if e.get("model_key") == m and e.get("variant") == v and e["case_id"] == case_id]
                if cell:
                    s = avg_score(cell, "cierre_gap")
                    row += f" {s*10:.0f}% |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")

    lines.append("---")
    lines.append("")

    # ── CRITERIOS DE ÉXITO ──
    lines.append("## 5. CRITERIOS DE ÉXITO (mejor celda)")
    lines.append("")

    # Find best model×variant
    best_evals = [e for e in good if f"{e.get('model_key')}/{e.get('variant')}" == best_cell]
    if best_evals:
        gap_pct = avg_score(best_evals, "cierre_gap") * 10
        err_rate = (10 - avg_score(best_evals, "errores_factuales")) * 10

        int_gaps = {}
        for int_id in INT_NAMES:
            ie = [e for e in best_evals if e["int_id"] == int_id]
            if ie:
                int_gaps[int_id] = avg_score(ie, "cierre_gap") * 10

        all_above_20 = all(v > 20 for v in int_gaps.values()) if int_gaps else False

        check = lambda b: "SI" if b else "NO"
        lines.append(f"Evaluando la mejor combinación: **{best_cell}**")
        lines.append("")
        lines.append("| Criterio | Resultado | Cumple |")
        lines.append("|----------|-----------|--------|")
        lines.append(f"| Gap closure >50% | {gap_pct:.0f}% | {check(gap_pct > 50)} |")
        lines.append(f"| Todas INTs >20% | {', '.join(f'{k}={v:.0f}%' for k,v in int_gaps.items())} | {check(all_above_20)} |")
        lines.append(f"| Errores <10% | {err_rate:.0f}% | {check(err_rate < 10)} |")

        criteria_met = sum([gap_pct > 50, all_above_20, err_rate < 10])
        verdict = "APROBADO" if criteria_met == 3 else f"NO APROBADO ({criteria_met}/3)"
        lines.append("")
        lines.append(f"**Veredicto: {verdict}**")

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── DELTA MODELO: Maverick vs 70B ──
    if "Maverick" in models and "70B" in models:
        lines.append("## 6. DELTA Maverick vs 70B")
        lines.append("")
        header = "| Variante |"
        sep = "|----------|"
        for dim in DIMS:
            header += f" {DIM_NAMES[dim]} |"
            sep += "------|"
        lines.append(header)
        lines.append(sep)

        for v in variants:
            e70 = [e for e in good if e.get("model_key") == "70B" and e.get("variant") == v]
            e405 = [e for e in good if e.get("model_key") == "Maverick" and e.get("variant") == v]
            if e70 and e405:
                row = f"| {v} |"
                for dim in DIMS:
                    s70 = avg_score(e70, dim)
                    s405 = avg_score(e405, dim)
                    delta = s405 - s70
                    sign = "+" if delta > 0 else ""
                    row += f" {sign}{delta:.1f} |"
                lines.append(row)
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── CONCLUSIÓN ──
    lines.append("## 7. CONCLUSIÓN")
    lines.append("")
    gap_global = avg_score(good, "cierre_gap") * 10
    if gap_global > 50:
        lines.append(f"Con {gap_global:.0f}% de gap closure global, las redes de preguntas compensan significativamente la diferencia de modelo.")
    elif gap_global > 30:
        lines.append(f"Con {gap_global:.0f}% de gap closure global, las preguntas guían pero el modelo aporta profundidad diferencial significativa.")
    else:
        lines.append(f"Con {gap_global:.0f}% de gap closure global, la capacidad del modelo domina sobre la estructura del prompt.")

    if "Maverick" in models and "70B" in models:
        e70_all = [e for e in good if e.get("model_key") == "70B"]
        e405_all = [e for e in good if e.get("model_key") == "Maverick"]
        if e70_all and e405_all:
            g70 = avg_score(e70_all, "cierre_gap") * 10
            g405 = avg_score(e405_all, "cierre_gap") * 10
            lines.append(f"\nDelta modelo (Maverick vs 70B): {g405:.0f}% vs {g70:.0f}% = +{g405-g70:.0f}pp")

    # Best/worst variants
    var_scores = {}
    for v in variants:
        ve = [e for e in good if e.get("variant") == v]
        if ve:
            var_scores[v] = avg_score(ve, "cierre_gap") * 10
    if var_scores:
        best_v = max(var_scores, key=var_scores.get)
        worst_v = min(var_scores, key=var_scores.get)
        lines.append(f"\nMejor variante: {best_v} ({var_scores[best_v]:.0f}%), peor: {worst_v} ({var_scores[worst_v]:.0f}%)")
        lines.append(f"Delta variante: +{var_scores[best_v]-var_scores[worst_v]:.0f}pp")

    lines.append("")
    lines.append("---")
    lines.append("*Generado por motor_v1_validation*")

    return "\n".join(lines)


def main():
    evals = load()
    report = generate(evals)

    path = OUTPUT_DIR / "VALIDATION_REPORT.md"
    with open(path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Reporte: {path}")
    print()
    # Print the matrix section
    for line in report.split("\n"):
        if line.startswith("## 1.") or line.startswith("| ") or line.startswith("|--") or line.startswith("**Mejor") or line.startswith("**Veredicto"):
            print(line)


if __name__ == "__main__":
    main()
