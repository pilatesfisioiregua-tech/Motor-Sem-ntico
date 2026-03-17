#!/usr/bin/env python3
"""EXP 5 — Cadena de Montaje: Analysis & Report Generator
Reads exp5_results.json and generates exp5_report.md + exp5_report.json
"""

import json
import os
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results"

# Config metadata
CONFIG_META = {
    "0": {"name": "Baseline", "stations": 1, "type": "baseline"},
    "A": {"name": "Linea Industrial", "stations": 7, "type": "full"},
    "B": {"name": "Coder Puro", "stations": 5, "type": "full"},
    "C": {"name": "Maxima Diversidad", "stations": 7, "type": "full"},
    "D": {"name": "Ultra-Barato", "stations": 5, "type": "cheap"},
    "E": {"name": "Premium", "stations": 7, "type": "premium"},
    "F": {"name": "Cadena Minima", "stations": 3, "type": "minimal"},
    "G": {"name": "Razonadores", "stations": 7, "type": "reasoning"},
}

TASK_META = {
    "T1": {"name": "Edge Function TS", "difficulty": "Media"},
    "T2": {"name": "Migration SQL", "difficulty": "Media"},
    "T3": {"name": "Analysis Script", "difficulty": "Media"},
    "T4": {"name": "Orchestrator", "difficulty": "Alta"},
    "T5": {"name": "Assembly Line", "difficulty": "Muy Alta"},
}


def load_results():
    path = RESULTS_DIR / "exp5_results.json"
    if not path.exists():
        print("ERROR: %s not found" % path)
        return []
    with open(path) as f:
        return json.load(f)


def build_matrix(results):
    """Build config x task matrix."""
    matrix = {}
    for r in results:
        key = (r["config"], r["task"])
        matrix[key] = r
    return matrix


def section_a_main_table(results, matrix):
    """A) Main table: Config x Task pass rates."""
    lines = ["## A) Tabla Principal: Config x Task\n"]
    tasks = sorted(set(r["task"] for r in results))
    configs = sorted(set(r["config"] for r in results), key=lambda x: (x.isdigit(), x))

    # Header
    header = "| Config | Nombre |"
    sep = "|--------|--------|"
    for t in tasks:
        header += " %s |" % t
        sep += "------|"
    header += " **Media** | Coste | Tiempo |"
    sep += "--------|-------|--------|"
    lines.append(header)
    lines.append(sep)

    for cfg in configs:
        name = CONFIG_META.get(cfg, {}).get("name", cfg)
        row = "| %s | %s |" % (cfg, name)
        rates = []
        total_cost = 0.0
        total_time = 0.0
        for t in tasks:
            r = matrix.get((cfg, t))
            if r:
                pr = r["final"].get("pass_rate", 0)
                passed = r["final"].get("tests_passed", 0)
                total = r["final"].get("tests_total", 0)
                rates.append(pr)
                total_cost += r.get("total_cost_usd", 0)
                total_time += r.get("total_time_s", 0)
                if pr >= 0.9:
                    row += " **%d/%d** |" % (passed, total)
                elif pr > 0:
                    row += " %d/%d |" % (passed, total)
                else:
                    row += " 0/%d |" % total
            else:
                row += " — |"
        avg_rate = sum(rates) / len(rates) if rates else 0
        row += " **%.0f%%** | $%.3f | %.0fs |" % (avg_rate * 100, total_cost, total_time)
        lines.append(row)
    lines.append("")
    return "\n".join(lines)


def section_b_baseline_vs_chain(results, matrix):
    """B) Baseline vs best chain."""
    lines = ["## B) Baseline vs Mejor Cadena\n"]
    tasks = sorted(set(r["task"] for r in results))
    configs = sorted(set(r["config"] for r in results), key=lambda x: (x.isdigit(), x))

    # Baseline data
    baseline_rates = {}
    for t in tasks:
        r = matrix.get(("0", t))
        if r:
            baseline_rates[t] = r["final"].get("pass_rate", 0)

    # Best chain per task
    best_chain = {}
    for t in tasks:
        best_rate = -1
        best_cfg = None
        for cfg in configs:
            if cfg == "0":
                continue
            r = matrix.get((cfg, t))
            if r:
                pr = r["final"].get("pass_rate", 0)
                if pr > best_rate:
                    best_rate = pr
                    best_cfg = cfg
        if best_cfg:
            best_chain[t] = (best_cfg, best_rate)

    lines.append("| Task | Baseline (0) | Mejor Cadena | Config | Delta |")
    lines.append("|------|-------------|-------------|--------|-------|")
    for t in tasks:
        bl = baseline_rates.get(t, 0)
        bc_cfg, bc_rate = best_chain.get(t, ("—", 0))
        delta = bc_rate - bl
        sign = "+" if delta > 0 else ""
        lines.append("| %s | %.0f%% | %.0f%% | %s | %s%.0f%% |" % (
            t, bl * 100, bc_rate * 100, bc_cfg, sign, delta * 100))

    # Averages
    avg_bl = sum(baseline_rates.values()) / max(len(baseline_rates), 1)
    avg_bc = sum(r for _, r in best_chain.values()) / max(len(best_chain), 1) if best_chain else 0
    lines.append("")
    lines.append("**Baseline medio: %.0f%% | Mejor cadena medio: %.0f%% | Delta: %+.0f%%**\n" % (
        avg_bl * 100, avg_bc * 100, (avg_bc - avg_bl) * 100))
    return "\n".join(lines)


def section_c_station_count(results, matrix):
    """C) 7 vs 5 vs 3 stations."""
    lines = ["## C) Cuantas Estaciones Necesitas?\n"]
    tasks = sorted(set(r["task"] for r in results))

    groups = {
        "7 estaciones (A,C,E,G)": ["A", "C", "E", "G"],
        "5 estaciones (B,D)": ["B", "D"],
        "3 estaciones (F)": ["F"],
        "1 estacion (0)": ["0"],
    }

    lines.append("| Grupo | Pass Rate Medio | Coste Medio | Tiempo Medio |")
    lines.append("|-------|----------------|-------------|--------------|")
    for group_name, cfgs in groups.items():
        rates = []
        costs = []
        times = []
        for cfg in cfgs:
            for t in tasks:
                r = matrix.get((cfg, t))
                if r:
                    rates.append(r["final"].get("pass_rate", 0))
                    costs.append(r.get("total_cost_usd", 0))
                    times.append(r.get("total_time_s", 0))
        if rates:
            lines.append("| %s | %.0f%% | $%.4f | %.0fs |" % (
                group_name, sum(rates) / len(rates) * 100,
                sum(costs) / len(costs), sum(times) / len(times)))
    lines.append("")
    return "\n".join(lines)


def section_d_debugger_impact(results, matrix):
    """D) Debugger impact: tests before vs after."""
    lines = ["## D) Impacto del Debugger (E4)\n"]
    lines.append("| Config | Task | Tests Pre-Debug | Tests Post-Debug R1 | Post-Debug R2 | Delta |")
    lines.append("|--------|------|----------------|--------------------|--------------:|-------|")

    debug_improvements = []
    for r in results:
        if r["config"] == "0":
            continue
        tester_st = None
        debug1_st = None
        debug2_st = None
        for st in r.get("stations", []):
            if st["station"] == "tester":
                tester_st = st
            elif st["station"] == "debugger1":
                debug1_st = st
            elif st["station"] == "debugger2":
                debug2_st = st

        if tester_st and tester_st.get("tests_after"):
            pre = tester_st["tests_after"]
            post1 = debug1_st["tests_after"] if debug1_st and debug1_st.get("tests_after") else "—"
            post2 = debug2_st["tests_after"] if debug2_st and debug2_st.get("tests_after") else "—"

            # Parse pre rate
            try:
                p, t = pre.split("/")
                pre_rate = int(p) / max(int(t), 1)
            except (ValueError, ZeroDivisionError):
                pre_rate = 0

            final_rate = r["final"].get("pass_rate", 0)
            delta = final_rate - pre_rate
            if delta > 0:
                debug_improvements.append(delta)

            lines.append("| %s | %s | %s | %s | %s | %+.0f%% |" % (
                r["config"], r["task"], pre, post1, post2, delta * 100))

    lines.append("")
    if debug_improvements:
        lines.append("**Debugger mejoro en %d/%d casos. Media de mejora: +%.0f%%**\n" % (
            len(debug_improvements), len([r for r in results if r["config"] != "0"]),
            sum(debug_improvements) / len(debug_improvements) * 100))
    return "\n".join(lines)


def section_e_pareto(results, matrix):
    """E) Pareto cost/quality."""
    lines = ["## E) Pareto Coste/Calidad\n"]
    tasks = sorted(set(r["task"] for r in results))
    configs = sorted(set(r["config"] for r in results), key=lambda x: (x.isdigit(), x))

    lines.append("| Config | Nombre | Pass Rate | Coste Total | Coste/Task | Ratio Calidad/Coste |")
    lines.append("|--------|--------|-----------|-------------|------------|---------------------|")

    config_data = []
    for cfg in configs:
        cfg_results = [r for r in results if r["config"] == cfg]
        if not cfg_results:
            continue
        rates = [r["final"].get("pass_rate", 0) for r in cfg_results]
        costs = [r.get("total_cost_usd", 0) for r in cfg_results]
        avg_rate = sum(rates) / len(rates)
        total_cost = sum(costs)
        cost_per_task = total_cost / max(len(cfg_results), 1)
        ratio = avg_rate / max(cost_per_task, 0.0001)
        config_data.append((cfg, avg_rate, total_cost, cost_per_task, ratio))

    config_data.sort(key=lambda x: -x[4])  # Sort by ratio desc
    for cfg, avg_rate, total_cost, cost_per_task, ratio in config_data:
        name = CONFIG_META.get(cfg, {}).get("name", cfg)
        lines.append("| %s | %s | %.0f%% | $%.4f | $%.4f | %.0f |" % (
            cfg, name, avg_rate * 100, total_cost, cost_per_task, ratio))
    lines.append("")
    return "\n".join(lines)


def section_f_failures(results, matrix):
    """F) Failure analysis: where do errors originate?"""
    lines = ["## F) Analisis de Fallos\n"]

    # Per task: which station originates errors
    task_failures = defaultdict(list)
    for r in results:
        if r["final"].get("pass_rate", 0) >= 1.0:
            continue
        failed_station = "unknown"
        for st in r.get("stations", []):
            if st.get("error"):
                failed_station = st["station"]
                break
        if failed_station == "unknown" and r.get("stations"):
            # Tests generated but failing — implementation issue
            failed_station = "implementation"
        task_failures[r["task"]].append({
            "config": r["config"], "station": failed_station,
            "pass_rate": r["final"].get("pass_rate", 0),
        })

    lines.append("### Fallos por Tarea\n")
    for task in sorted(task_failures.keys()):
        failures = task_failures[task]
        total_runs = len([r for r in results if r["task"] == task])
        fail_count = len(failures)
        lines.append("**%s** (%s): %d/%d configs con fallos" % (
            task, TASK_META.get(task, {}).get("name", ""), fail_count, total_runs))
        for f in failures:
            lines.append("  - Config %s: %s (pass_rate=%.0f%%)" % (
                f["config"], f["station"], f["pass_rate"] * 100))
        lines.append("")

    # Which tasks are hardest?
    lines.append("### Dificultad Real por Tarea\n")
    tasks = sorted(set(r["task"] for r in results))
    lines.append("| Task | Nombre | Configs con 100% | Configs con >0% | Configs con 0% |")
    lines.append("|------|--------|-----------------|----------------|----------------|")
    for t in tasks:
        task_results = [r for r in results if r["task"] == t]
        perfect = sum(1 for r in task_results if r["final"].get("pass_rate", 0) >= 1.0)
        partial = sum(1 for r in task_results if 0 < r["final"].get("pass_rate", 0) < 1.0)
        zero = sum(1 for r in task_results if r["final"].get("pass_rate", 0) == 0)
        lines.append("| %s | %s | %d | %d | %d |" % (
            t, TASK_META.get(t, {}).get("name", ""), perfect, partial, zero))
    lines.append("")
    return "\n".join(lines)


def section_g_verdict(results, matrix):
    """G) Final verdict."""
    lines = ["## G) VEREDICTO: Puede Reemplazar a Code?\n"]
    tasks = sorted(set(r["task"] for r in results))
    configs = sorted(set(r["config"] for r in results), key=lambda x: (x.isdigit(), x))

    # Best chain overall
    best_cfg = None
    best_avg = -1
    for cfg in configs:
        if cfg == "0":
            continue
        cfg_results = [r for r in results if r["config"] == cfg]
        if not cfg_results:
            continue
        avg = sum(r["final"].get("pass_rate", 0) for r in cfg_results) / len(cfg_results)
        if avg > best_avg:
            best_avg = avg
            best_cfg = cfg

    # Baseline avg
    bl_results = [r for r in results if r["config"] == "0"]
    bl_avg = sum(r["final"].get("pass_rate", 0) for r in bl_results) / max(len(bl_results), 1)

    # Config D (cheap)
    d_results = [r for r in results if r["config"] == "D"]
    d_avg = sum(r["final"].get("pass_rate", 0) for r in d_results) / max(len(d_results), 1)

    lines.append("### Datos Clave\n")
    lines.append("- **Mejor cadena**: Config %s (%s) con %.0f%% pass rate medio" % (
        best_cfg, CONFIG_META.get(best_cfg, {}).get("name", ""),
        best_avg * 100) if best_cfg else "- No hay datos suficientes")
    lines.append("- **Baseline (modelo solo)**: %.0f%% pass rate medio" % (bl_avg * 100))
    lines.append("- **Delta cadena vs baseline**: %+.0f%%" % ((best_avg - bl_avg) * 100) if best_cfg else "")
    lines.append("- **Config D (ultra-barato)**: %.0f%% pass rate medio" % (d_avg * 100))
    lines.append("")

    # Check criteria
    lines.append("### Criterios\n")
    lines.append("| Criterio | Resultado | Cumple? |")
    lines.append("|----------|-----------|---------|")

    if best_cfg:
        lines.append("| Mejor cadena > baseline | %.0f%% vs %.0f%% | %s |" % (
            best_avg * 100, bl_avg * 100, "SI" if best_avg > bl_avg else "NO"))
        lines.append("| >=1 config con >=90%% pass rate | %.0f%% | %s |" % (
            best_avg * 100, "SI" if best_avg >= 0.9 else "NO"))
    lines.append("| Config D >= 70%% | %.0f%% | %s |" % (
        d_avg * 100, "SI" if d_avg >= 0.7 else "NO"))

    # Debugger impact
    debug_improvements = 0
    debug_opportunities = 0
    for r in results:
        if r["config"] == "0":
            continue
        for st in r.get("stations", []):
            if st["station"] in ("debugger1", "debugger2") and st.get("tests_after"):
                debug_opportunities += 1
                try:
                    tester_st = [s for s in r["stations"] if s["station"] == "tester"][0]
                    pre = tester_st.get("tests_after", "0/1")
                    p1, t1 = pre.split("/")
                    p2, t2 = st["tests_after"].split("/")
                    if int(p2) > int(p1):
                        debug_improvements += 1
                except (ValueError, IndexError):
                    pass

    if debug_opportunities > 0:
        debug_rate = debug_improvements / debug_opportunities
        lines.append("| Debugger sube >=30%% de fallos | %.0f%% (%d/%d) | %s |" % (
            debug_rate * 100, debug_improvements, debug_opportunities,
            "SI" if debug_rate >= 0.3 else "NO"))

    # Config F vs Config B
    f_results = [r for r in results if r["config"] == "F"]
    b_results = [r for r in results if r["config"] == "B"]
    f_avg = sum(r["final"].get("pass_rate", 0) for r in f_results) / max(len(f_results), 1)
    b_avg = sum(r["final"].get("pass_rate", 0) for r in b_results) / max(len(b_results), 1)
    lines.append("| Config F ~= Config B | F=%.0f%% vs B=%.0f%% | %s |" % (
        f_avg * 100, b_avg * 100, "SI" if abs(f_avg - b_avg) < 0.15 else "NO"))

    lines.append("")

    # Final verdict
    lines.append("### Veredicto\n")
    if best_avg >= 0.9:
        lines.append("**SI, puede reemplazar a Code para trabajo estandar.** "
                      "La mejor cadena alcanza %.0f%% pass rate." % (best_avg * 100))
    elif best_avg >= 0.8:
        lines.append("**SI, con limitaciones.** La mejor cadena alcanza %.0f%% pass rate. "
                      "Funciona para tareas medias pero puede fallar en tareas complejas." % (best_avg * 100))
    elif best_avg >= 0.6:
        lines.append("**PARCIAL.** La mejor cadena alcanza %.0f%% pass rate. "
                      "Util para tareas simples pero insuficiente para trabajo complejo." % (best_avg * 100))
    else:
        lines.append("**NO, la cadena no es suficiente hoy.** "
                      "Mejor cadena: %.0f%% pass rate." % (best_avg * 100))

    if best_avg > bl_avg:
        lines.append("\nLa cadena de montaje **supera al modelo solo** en %+.0f%%." % (
            (best_avg - bl_avg) * 100))
    else:
        lines.append("\nEl modelo solo **es igual o mejor** que la cadena.")

    lines.append("")
    return "\n".join(lines)


def generate_report(results):
    """Generate full report."""
    matrix = build_matrix(results)

    report = []
    report.append("# EXP 5 — CADENA DE MONTAJE (Analisis)\n")
    report.append("Fecha: %s" % results[0].get("timestamp", "?")[:10] if results else "")
    report.append("Total runs: %d\n" % len(results))
    report.append(section_a_main_table(results, matrix))
    report.append(section_b_baseline_vs_chain(results, matrix))
    report.append(section_c_station_count(results, matrix))
    report.append(section_d_debugger_impact(results, matrix))
    report.append(section_e_pareto(results, matrix))
    report.append(section_f_failures(results, matrix))
    report.append(section_g_verdict(results, matrix))
    report.append("---\n*Generado por exp5_analyze.py*")

    return "\n".join(report)


def main():
    results = load_results()
    if not results:
        return

    print("Loaded %d results" % len(results))

    # Generate report
    report_md = generate_report(results)
    md_path = RESULTS_DIR / "exp5_report.md"
    with open(md_path, 'w') as f:
        f.write(report_md)
    print("Report saved to %s" % md_path)

    # Save structured report data
    matrix = build_matrix(results)
    tasks = sorted(set(r["task"] for r in results))
    configs = sorted(set(r["config"] for r in results), key=lambda x: (x.isdigit(), x))

    report_data = {
        "summary": {},
        "per_config": {},
        "per_task": {},
    }

    for cfg in configs:
        cfg_results = [r for r in results if r["config"] == cfg]
        rates = [r["final"].get("pass_rate", 0) for r in cfg_results]
        costs = [r.get("total_cost_usd", 0) for r in cfg_results]
        times = [r.get("total_time_s", 0) for r in cfg_results]
        report_data["per_config"][cfg] = {
            "name": CONFIG_META.get(cfg, {}).get("name", ""),
            "avg_pass_rate": round(sum(rates) / max(len(rates), 1), 3),
            "total_cost": round(sum(costs), 5),
            "avg_time": round(sum(times) / max(len(times), 1), 1),
            "tasks": {r["task"]: r["final"] for r in cfg_results},
        }

    for t in tasks:
        task_results = [r for r in results if r["task"] == t]
        rates = [r["final"].get("pass_rate", 0) for r in task_results]
        report_data["per_task"][t] = {
            "name": TASK_META.get(t, {}).get("name", ""),
            "avg_pass_rate": round(sum(rates) / max(len(rates), 1), 3),
            "configs": {r["config"]: r["final"] for r in task_results},
        }

    json_path = RESULTS_DIR / "exp5_report.json"
    with open(json_path, 'w') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print("JSON data saved to %s" % json_path)


if __name__ == "__main__":
    main()
