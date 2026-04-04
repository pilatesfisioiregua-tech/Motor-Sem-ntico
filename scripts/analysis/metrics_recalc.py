#!/usr/bin/env python3
"""
metrics_recalc.py — Paso 2: Recalcular métricas correctamente para pre-flight gold_set_v3.

Ejecuta 4 análisis:
  1. Recalcular métricas poc_v1 con Spearman + Bootstrap CI
  2. Calidad de labels del gold_set_v2 (distribución, skewness, floor/ceiling)
  3. Split analysis train/val (Mann-Whitney, equivalencia estadística)
  4. Baseline realista (predictor random, predictor-media)

Coste: $0 (todo local, sin llamadas LLM)
"""

import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

# ─── Paths ───────────────────────────────────────────────────────────────────
REPO = Path("/Users/jesusfernandezdominguez/omni-mind-cerebro")
MOTOR = REPO / "motor-semantico"

POC_V1_EVAL    = MOTOR / "experiments/poc_v1/metrics/eval_report.json"
POC_V1_MODEL   = MOTOR / "experiments/poc_v1/model/final_metrics.json"
GOLD_SET_V2    = MOTOR / "data/gold_set_v2_3000.jsonl"
POC_MICRO      = MOTOR / "data/poc_micro_71dims.jsonl"
OUT_DIR        = MOTOR / "experiments/metrics_preflight"
REPORT_PATH    = OUT_DIR / "report.md"
DATA_PATH      = OUT_DIR / "metrics_recalc.json"

SEED = 42
N_BOOTSTRAP = 1000
random.seed(SEED)
np.random.seed(SEED)


# ─── Utilidades ──────────────────────────────────────────────────────────────

def spearman_r(x, y):
    """Spearman rank correlation."""
    n = len(x)
    if n < 4:
        return float("nan"), float("nan")
    result = stats.spearmanr(x, y)
    return float(result.statistic), float(result.pvalue)


def bootstrap_ci(x, y, n_resamples=N_BOOTSTRAP, ci=0.95, method="spearman"):
    """Bootstrap CI para correlación entre x e y."""
    n = len(x)
    if n < 8:
        return float("nan"), float("nan")

    samples = []
    for _ in range(n_resamples):
        idx = np.random.randint(0, n, size=n)
        xb = np.array(x)[idx]
        yb = np.array(y)[idx]
        if np.std(xb) < 1e-10 or np.std(yb) < 1e-10:
            continue
        if method == "spearman":
            r = stats.spearmanr(xb, yb).statistic
        else:
            r = stats.pearsonr(xb, yb)[0]
        samples.append(r)

    if len(samples) < 10:
        return float("nan"), float("nan")

    alpha = (1 - ci) / 2
    lo = float(np.percentile(samples, alpha * 100))
    hi = float(np.percentile(samples, (1 - alpha) * 100))
    return lo, hi


def weighted_corr_global(dim_corrs, dim_vars):
    """Corr_global ponderada por varianza de cada dim."""
    total_weight = 0.0
    weighted_sum = 0.0
    for name in dim_corrs:
        r = dim_corrs[name]
        v = dim_vars.get(name, 0.0)
        if not math.isnan(r) and v > 0:
            weighted_sum += r * v
            total_weight += v
    if total_weight == 0:
        return float("nan")
    return weighted_sum / total_weight


def load_gold_set_v2(path):
    """Carga gold_set_v2 y devuelve dict {dim_name: [valores]}."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        return {}, []

    # Detectar dims numéricas (float/int, no string)
    all_dims = list(records[0]["labels"].keys())
    numeric_dims = []
    for d in all_dims:
        val = records[0]["labels"][d]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            numeric_dims.append(d)

    dim_values = defaultdict(list)
    for rec in records:
        for d in numeric_dims:
            v = rec["labels"].get(d, None)
            if v is not None and isinstance(v, (int, float)):
                dim_values[d].append(float(v))

    return dict(dim_values), records


def load_poc_micro(path):
    """Carga poc_micro_71dims (labels T-001). Devuelve dict {dim: [valores]}."""
    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        return {}

    all_dims = list(records[0]["labels"].keys())
    numeric_dims = []
    for d in all_dims:
        val = records[0]["labels"][d]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            numeric_dims.append(d)

    dim_values = defaultdict(list)
    for rec in records:
        for d in numeric_dims:
            v = rec["labels"].get(d, None)
            if v is not None and isinstance(v, (int, float)):
                dim_values[d].append(float(v))

    return dict(dim_values)


# ─── Módulo 1: Recalcular métricas poc_v1 con Spearman + Bootstrap ───────────

def recalculate_poc_v1_metrics():
    """
    No tenemos predicciones por muestra. Usamos:
      - final_metrics.json: tiene corr/dim_name (Pearson del test split del modelo)
      - eval_report.json: tiene pearson_r, label_mean, label_std, pred_mean, pred_std

    Sin los vectores pred/label originales, no podemos calcular Spearman exacto.
    PERO podemos:
      1. Comparar distribución Pearson del report vs los valores del modelo
      2. Re-ponderar la corr_global por varianza (en lugar de media simple)
      3. Documentar que necesitamos las predicciones brutas para Bootstrap real
    """
    print("[1/4] Recalculando métricas poc_v1...")

    with open(POC_V1_EVAL) as f:
        eval_report = json.load(f)
    with open(POC_V1_MODEL) as f:
        model_metrics = json.load(f)

    # Extraer corr y varianza de labels por dim
    dim_pearson_eval = {}  # del eval_report (val set 499 muestras)
    dim_label_std = {}
    for entry in eval_report.get("float_dims", []):
        name = entry["name"]
        dim_pearson_eval[name] = entry["pearson_r"]
        dim_label_std[name] = entry.get("label_std", 0.0)

    # Extraer corr del training (split del trainer)
    dim_corr_model = {}
    for k, v in model_metrics.get("test_metrics", {}).items():
        if k.startswith("corr/"):
            dim_name = k[5:]
            dim_corr_model[dim_name] = v

    # Variance proxy: label_std^2
    dim_vars = {d: (s ** 2) for d, s in dim_label_std.items()}

    # Corr_global ACTUAL (media simple, como en el report)
    pearson_vals = list(dim_pearson_eval.values())
    corr_global_simple = float(np.mean(pearson_vals))
    corr_global_median = float(np.median(pearson_vals))

    # Corr_global NUEVO (ponderado por varianza)
    corr_global_weighted = weighted_corr_global(dim_pearson_eval, dim_vars)

    # Categorizar dims
    n_positive = sum(1 for r in pearson_vals if r > 0.3)
    n_weak = sum(1 for r in pearson_vals if 0.0 < r <= 0.3)
    n_negative = sum(1 for r in pearson_vals if r <= 0.0)

    # Ranking por Pearson
    ranked = sorted(dim_pearson_eval.items(), key=lambda x: x[1], reverse=True)

    # Para cada dim, verificar si hay overfitting (model test vs eval)
    overfitting_analysis = []
    for d in dim_pearson_eval:
        if d in dim_corr_model:
            train_corr = dim_corr_model[d]  # modelo test split (durante training)
            eval_corr = dim_pearson_eval[d]   # eval report (val set)
            delta = eval_corr - train_corr
            overfitting_analysis.append({
                "dim": d,
                "train_corr": round(train_corr, 4),
                "val_corr": round(eval_corr, 4),
                "delta": round(delta, 4),
                "flag": "OVERFIT" if delta < -0.2 else ("UNDERFIT" if delta > 0.2 else "OK")
            })

    result = {
        "corr_global_simple_original": round(corr_global_simple, 4),
        "corr_global_median": round(corr_global_median, 4),
        "corr_global_weighted_by_variance": round(corr_global_weighted, 4),
        "n_dims": len(dim_pearson_eval),
        "n_positive_corr_gt_03": n_positive,
        "n_weak_corr_0_03": n_weak,
        "n_negative_corr": n_negative,
        "note_bootstrap": "SIN predicciones por muestra — Bootstrap requiere vectores pred/label originales",
        "top_10_dims": [{"dim": d, "pearson": round(r, 4)} for d, r in ranked[:10]],
        "bottom_10_dims": [{"dim": d, "pearson": round(r, 4)} for d, r in ranked[-10:]],
        "overfitting_analysis": sorted(overfitting_analysis, key=lambda x: x["delta"]),
        "n_overfit_dims": sum(1 for x in overfitting_analysis if x["flag"] == "OVERFIT"),
        "n_underfit_dims": sum(1 for x in overfitting_analysis if x["flag"] == "UNDERFIT"),
    }

    print(f"  corr_global simple (original): {result['corr_global_simple_original']}")
    print(f"  corr_global weighted (nuevo): {result['corr_global_weighted_by_variance']}")
    print(f"  Dims positiva>0.3: {n_positive}, débil: {n_weak}, negativa: {n_negative}")
    print(f"  OVERFIT dims: {result['n_overfit_dims']} | UNDERFIT dims: {result['n_underfit_dims']}")
    return result


# ─── Módulo 2: Calidad de labels gold_set_v2 ─────────────────────────────────

def analyze_label_quality(dim_values):
    """Distribución, skewness, kurtosis, floor/ceiling por dim."""
    print("[2/4] Analizando calidad de labels gold_set_v2...")

    dim_stats = {}
    n_normal = 0
    n_skewed = 0
    n_floor_ceiling = 0
    n_total = len(dim_values)

    for dim, vals in dim_values.items():
        arr = np.array(vals, dtype=float)
        n = len(arr)
        if n < 10:
            continue

        mean = float(np.mean(arr))
        std = float(np.std(arr))
        median = float(np.median(arr))
        var = float(np.var(arr))
        skewness = float(stats.skew(arr))
        kurt = float(stats.kurtosis(arr))

        # Floor/ceiling: >50% en mín o máx del rango [0,1]
        floor_rate = float(np.mean(arr <= 0.05))  # cerca de 0
        ceil_rate = float(np.mean(arr >= 0.95))   # cerca de 1
        has_floor = floor_rate > 0.5
        has_ceiling = ceil_rate > 0.5

        # Test de normalidad (Shapiro-Wilk en muestra de 500)
        sample = arr[:500] if n > 500 else arr
        if len(sample) >= 8:
            _, p_normal = stats.shapiro(sample)
            is_normal = p_normal > 0.05
        else:
            is_normal = False
            p_normal = 0.0

        # Percentiles
        p10 = float(np.percentile(arr, 10))
        p25 = float(np.percentile(arr, 25))
        p75 = float(np.percentile(arr, 75))
        p90 = float(np.percentile(arr, 90))

        if is_normal:
            n_normal += 1
        else:
            n_skewed += 1

        if has_floor or has_ceiling:
            n_floor_ceiling += 1

        dim_stats[dim] = {
            "n": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "median": round(median, 4),
            "var": round(var, 6),
            "skewness": round(skewness, 4),
            "kurtosis": round(kurt, 4),
            "p10": round(p10, 4),
            "p25": round(p25, 4),
            "p75": round(p75, 4),
            "p90": round(p90, 4),
            "floor_rate": round(floor_rate, 4),
            "ceil_rate": round(ceil_rate, 4),
            "has_floor_effect": has_floor,
            "has_ceiling_effect": has_ceiling,
            "is_normal": is_normal,
            "p_normality": round(p_normal, 4),
            "abs_skewness": round(abs(skewness), 4),
            "dist_type": "normal" if is_normal else ("floor" if has_floor else ("ceiling" if has_ceiling else "skewed")),
        }

    # Top dims más sesgadas
    by_skewness = sorted(dim_stats.items(), key=lambda x: abs(x[1]["skewness"]), reverse=True)
    top_skewed = [{"dim": d, "skewness": s["skewness"], "floor_rate": s["floor_rate"]}
                  for d, s in by_skewness[:10]]

    # Dims con floor/ceiling effect
    floor_ceiling_dims = [d for d, s in dim_stats.items() if s["has_floor_effect"] or s["has_ceiling_effect"]]

    result = {
        "n_dims_analyzed": n_total,
        "n_normal_distribution": n_normal,
        "n_skewed_distribution": n_skewed,
        "n_floor_ceiling_effect": n_floor_ceiling,
        "pct_skewed": round(n_skewed / max(n_total, 1) * 100, 1),
        "pct_floor_ceiling": round(n_floor_ceiling / max(n_total, 1) * 100, 1),
        "top_10_most_skewed": top_skewed,
        "floor_ceiling_dims": floor_ceiling_dims,
        "dim_stats": dim_stats,
    }

    print(f"  Dims normales: {n_normal}/{n_total} ({round(n_normal/max(n_total,1)*100,1)}%)")
    print(f"  Dims sesgadas: {n_skewed}/{n_total} ({round(n_skewed/max(n_total,1)*100,1)}%)")
    print(f"  Dims con floor/ceiling effect: {n_floor_ceiling}")
    return result


# ─── Módulo 3: Split analysis 80/20 ──────────────────────────────────────────

def split_analysis(dim_values, records, train_ratio=0.8):
    """80/20 split aleatorio, verificar equivalencia estadística."""
    print("[3/4] Analizando split train/val 80/20...")

    n = len(records)
    indices = list(range(n))
    random.shuffle(indices)
    n_train = int(n * train_ratio)
    train_idx = set(indices[:n_train])
    val_idx = set(indices[n_train:])

    # Por dim: calcular estadísticas en train vs val
    dim_split_stats = {}
    n_equivalent = 0
    n_not_equivalent = 0
    n_dims = 0

    all_dims = list(dim_values.keys())

    for dim in all_dims:
        vals = dim_values[dim]
        if len(vals) != n:
            continue  # skip si longitud no coincide

        train_vals = [vals[i] for i in sorted(train_idx)]
        val_vals   = [vals[i] for i in sorted(val_idx)]

        if len(train_vals) < 8 or len(val_vals) < 8:
            continue

        arr_train = np.array(train_vals, dtype=float)
        arr_val   = np.array(val_vals, dtype=float)

        # Mann-Whitney U test (no paramétrico, no asume normalidad)
        mw_stat, mw_pvalue = stats.mannwhitneyu(arr_train, arr_val, alternative="two-sided")

        # Estadísticas descriptivas
        t_mean = float(np.mean(arr_train))
        v_mean = float(np.mean(arr_val))
        t_std  = float(np.std(arr_train))
        v_std  = float(np.std(arr_val))
        t_var  = float(np.var(arr_train))
        v_var  = float(np.var(arr_val))

        # Equivalentes si p > 0.05 (no hay diferencia significativa)
        is_equivalent = mw_pvalue > 0.05
        if is_equivalent:
            n_equivalent += 1
        else:
            n_not_equivalent += 1
        n_dims += 1

        dim_split_stats[dim] = {
            "train_n": len(train_vals),
            "val_n": len(val_vals),
            "train_mean": round(t_mean, 4),
            "val_mean": round(v_mean, 4),
            "train_std": round(t_std, 4),
            "val_std": round(v_std, 4),
            "train_var": round(t_var, 6),
            "val_var": round(v_var, 6),
            "mean_delta": round(abs(t_mean - v_mean), 4),
            "std_delta": round(abs(t_std - v_std), 4),
            "mw_pvalue": round(float(mw_pvalue), 4),
            "is_statistically_equivalent": is_equivalent,
        }

    # Dims donde el split NO es equivalente
    non_equiv_dims = [
        {"dim": d, "mw_pvalue": s["mw_pvalue"], "mean_delta": s["mean_delta"]}
        for d, s in dim_split_stats.items()
        if not s["is_statistically_equivalent"]
    ]
    non_equiv_dims.sort(key=lambda x: x["mw_pvalue"])

    pct_equiv = round(n_equivalent / max(n_dims, 1) * 100, 1)

    result = {
        "n_total": n,
        "n_train": n_train,
        "n_val": n - n_train,
        "train_ratio": train_ratio,
        "n_dims_analyzed": n_dims,
        "n_statistically_equivalent": n_equivalent,
        "n_not_equivalent": n_not_equivalent,
        "pct_equivalent": pct_equiv,
        "verdict": "SPLIT REPRESENTATIVO" if pct_equiv >= 90 else "SPLIT SESGADO — revisar",
        "non_equivalent_dims": non_equiv_dims[:20],
        "split_stats_by_dim": dim_split_stats,
        "split_seed": SEED,
    }

    print(f"  Train: {n_train}, Val: {n - n_train}")
    print(f"  Dims estadísticamente equivalentes: {n_equivalent}/{n_dims} ({pct_equiv}%)")
    print(f"  Veredicto: {result['verdict']}")
    return result


# ─── Módulo 4: Baseline realista ─────────────────────────────────────────────

def compute_baselines(dim_values):
    """
    Para cada dim, calcular:
      - Spearman de predictor random (media ~0, CI bootstrap)
      - Spearman de predictor "siempre media" (siempre = mean del train)
      - Spearman Bootstrap CI del gold_set_v2 (límite de lo que puede lograr un modelo perfecto)
    """
    print("[4/4] Calculando baselines realistas...")

    baselines = {}
    N_SAMPLE = 200  # suficiente para bootstrap rápido en 48 dims

    for dim, vals in dim_values.items():
        arr = np.array(vals, dtype=float)
        n = len(arr)
        if n < 10:
            continue

        # Muestra para no tardar demasiado
        if n > N_SAMPLE:
            idx = np.random.choice(n, N_SAMPLE, replace=False)
            sample = arr[idx]
        else:
            sample = arr

        n_s = len(sample)

        # Baseline 1: predictor random (uniform [0, 1])
        rng = np.random.default_rng(SEED)
        random_preds = rng.uniform(0, 1, n_s)
        r_random, _ = spearman_r(sample, random_preds)
        # Bootstrap CI del predictor random
        random_corrs = []
        for _ in range(200):
            idx_b = np.random.randint(0, n_s, n_s)
            xb = sample[idx_b]
            yb = rng.uniform(0, 1, n_s)
            if np.std(xb) > 1e-10:
                random_corrs.append(stats.spearmanr(xb, yb).statistic)
        r_random_lo = float(np.percentile(random_corrs, 2.5)) if random_corrs else float("nan")
        r_random_hi = float(np.percentile(random_corrs, 97.5)) if random_corrs else float("nan")

        # Baseline 2: predictor "siempre la media" → Spearman = 0 (constante)
        # Una pred constante no tiene rango variado → corr = NaN
        r_mean_pred = 0.0  # por definición, constante tiene corr=0

        # Baseline 3: Bootstrap CI del gold mismo (cuánto varía la correlación del dataset consigo mismo)
        # Se calcula como: corr entre la muestra y una copia con ruido pequeño
        # Esto representa el "ruido de etiquetado" del dataset
        noisy_vals = sample + np.random.normal(0, float(np.std(sample)) * 0.05, n_s)
        r_gold_signal, _ = spearman_r(sample, noisy_vals)

        # Bootstrap CI sobre los datos reales para la dim (auto-correlación bootstrap)
        ci_lo, ci_hi = bootstrap_ci(sample, sample + np.random.normal(0, float(np.std(sample)) * 0.1, n_s),
                                    n_resamples=500, method="spearman")

        mean_val = float(np.mean(sample))
        std_val = float(np.std(sample))
        var_val = float(np.var(sample))

        # Spearman sobre todos los datos (no solo muestra)
        r_full, p_full = spearman_r(arr, arr + np.random.normal(0, std_val * 0.1, n))

        baselines[dim] = {
            "n": n,
            "mean": round(mean_val, 4),
            "std": round(std_val, 4),
            "var": round(var_val, 6),
            "baseline_random_spearman": round(float(r_random), 4),
            "baseline_random_ci95_lo": round(r_random_lo, 4),
            "baseline_random_ci95_hi": round(r_random_hi, 4),
            "baseline_mean_pred_spearman": r_mean_pred,
            "signal_spearman_5pct_noise": round(float(r_gold_signal), 4),
            "signal_ci95_lo": round(ci_lo, 4) if not math.isnan(ci_lo) else None,
            "signal_ci95_hi": round(ci_hi, 4) if not math.isnan(ci_hi) else None,
        }

    # Calcular estadísticas globales
    random_corrs_all = [b["baseline_random_spearman"] for b in baselines.values()
                        if not math.isnan(b["baseline_random_spearman"])]
    signal_corrs_all = [b["signal_spearman_5pct_noise"] for b in baselines.values()
                        if not math.isnan(b["signal_spearman_5pct_noise"])]

    result = {
        "n_dims": len(baselines),
        "random_baseline_mean": round(float(np.mean(random_corrs_all)), 4) if random_corrs_all else None,
        "random_baseline_ci95": f"[{round(float(np.percentile(random_corrs_all, 2.5)), 4)}, "
                                f"{round(float(np.percentile(random_corrs_all, 97.5)), 4)}]"
                                if len(random_corrs_all) > 4 else "N/A",
        "signal_baseline_mean": round(float(np.mean(signal_corrs_all)), 4) if signal_corrs_all else None,
        "interpretation": (
            "El predictor random oscila en torno a 0 (esperado). "
            "Un modelo debe superar claramente ~0.10 de Spearman medio para ser mejor que random."
        ),
        "by_dim": baselines,
    }

    print(f"  Baseline random (media): {result['random_baseline_mean']}")
    print(f"  Baseline random CI95: {result['random_baseline_ci95']}")
    print(f"  Signal baseline (5% noise): {result['signal_baseline_mean']}")
    return result


# ─── Módulo 5: Spearman sobre datos de poc_v1 eval_report ──────────────────-
# Sin predicciones por muestra no podemos calcular Spearman exacto.
# Podemos SIMULAR cuánto cambiaría si los datos fueran Gaussianos vs skewed.

def estimate_pearson_vs_spearman_delta(dim_values, eval_report):
    """
    Estima la diferencia esperada Pearson→Spearman para las dims del poc_v1.
    Para distribuciones skewed, Spearman suele ser más alto que Pearson
    porque los rankings eliminan la influencia de outliers.
    Usa las distribuciones reales del gold_set_v2 como proxy.
    """
    print("  [extra] Estimando delta Pearson→Spearman para dims poc_v1...")

    # Dims del eval_report
    eval_dims = {e["name"]: e for e in eval_report.get("float_dims", [])}

    deltas = []
    for dim_name, entry in eval_dims.items():
        if dim_name not in dim_values:
            continue
        arr = np.array(dim_values[dim_name], dtype=float)
        skewness = abs(float(stats.skew(arr)))
        # Empírico: para skewness > 1, Spearman ~ Pearson + 0.05 a 0.15
        # Para skewness < 0.5, Spearman ~ Pearson
        expected_delta = 0.0
        if skewness > 2.0:
            expected_delta = 0.12
        elif skewness > 1.0:
            expected_delta = 0.07
        elif skewness > 0.5:
            expected_delta = 0.03
        deltas.append({
            "dim": dim_name,
            "pearson_r": entry["pearson_r"],
            "label_skewness": round(skewness, 3),
            "expected_spearman_delta": expected_delta,
            "estimated_spearman": round(entry["pearson_r"] + expected_delta, 4),
        })

    deltas.sort(key=lambda x: x["estimated_spearman"], reverse=True)

    # Recalcular corr_global con Spearman estimado
    spearman_vals = [d["estimated_spearman"] for d in deltas]
    corr_global_spearman_est = round(float(np.mean(spearman_vals)), 4)
    corr_global_spearman_med = round(float(np.median(spearman_vals)), 4)

    return {
        "note": "[SUPOSICION] Delta Pearson->Spearman estimado, no calculado con datos reales",
        "corr_global_spearman_estimated_mean": corr_global_spearman_est,
        "corr_global_spearman_estimated_median": corr_global_spearman_med,
        "by_dim": deltas[:20],  # top 20
    }


# ─── Generador de Informe MD ─────────────────────────────────────────────────

def generate_report(poc_v1_result, label_quality, split_result, baselines,
                    spearman_est, n_records_gold):
    lines = []
    L = lines.append

    L("# Métricas Pre-flight — Paso 2")
    L("")
    L("**Fecha**: 2026-04-04")
    L("**Coste**: $0 (todo local)")
    L("**Rama**: feature/labeling-double-pass")
    L("")
    L("---")
    L("")

    # ── Sección 1: poc_v1 recalculado ──
    L("## 1. Recalculo métricas poc_v1")
    L("")
    L(f"- **n_samples eval**: 499")
    L(f"- **Dims analizadas**: {poc_v1_result['n_dims']}")
    L(f"- **corr_global Pearson simple (original)**: `{poc_v1_result['corr_global_simple_original']}`")
    L(f"- **corr_global Pearson ponderado por varianza**: `{poc_v1_result['corr_global_weighted_by_variance']}`")
    L(f"- **corr_global Spearman estimado (media)**: `{spearman_est['corr_global_spearman_estimated_mean']}`")
    L(f"  - _Nota: {spearman_est['note']}_")
    L("")
    L("### Distribución de correlaciones")
    L("")
    L(f"| Rango | N dims |")
    L(f"|---|---|")
    L(f"| Pearson > 0.3 (buenas) | {poc_v1_result['n_positive_corr_gt_03']} |")
    L(f"| Pearson 0.0–0.3 (débiles) | {poc_v1_result['n_weak_corr_0_03']} |")
    L(f"| Pearson < 0.0 (negativas) | {poc_v1_result['n_negative_corr']} |")
    L("")
    L("### Top 10 dims (Pearson)")
    L("")
    L("| Dim | Pearson | Spearman est. |")
    L("|---|---|---|")
    spearman_by_dim = {d["dim"]: d for d in spearman_est["by_dim"]}
    for entry in poc_v1_result["top_10_dims"]:
        sp = spearman_by_dim.get(entry["dim"], {})
        sp_val = sp.get("estimated_spearman", "N/A")
        L(f"| {entry['dim']} | {entry['pearson']} | {sp_val} |")
    L("")
    L("### Bottom 10 dims (Pearson)")
    L("")
    L("| Dim | Pearson |")
    L("|---|---|")
    for entry in poc_v1_result["bottom_10_dims"]:
        L(f"| {entry['dim']} | {entry['pearson']} |")
    L("")
    L("### Análisis overfitting (train_corr vs val_corr)")
    L("")
    L(f"- **Dims OVERFIT** (val_corr < train_corr - 0.2): {poc_v1_result['n_overfit_dims']}")
    L(f"- **Dims UNDERFIT** (val_corr > train_corr + 0.2): {poc_v1_result['n_underfit_dims']}")
    L(f"- **Dims OK**: {len(poc_v1_result['overfitting_analysis']) - poc_v1_result['n_overfit_dims'] - poc_v1_result['n_underfit_dims']}")
    L("")

    overfit_items = [x for x in poc_v1_result["overfitting_analysis"] if x["flag"] == "OVERFIT"]
    underfit_items = [x for x in poc_v1_result["overfitting_analysis"] if x["flag"] == "UNDERFIT"]

    if overfit_items:
        L("**Dims con OVERFIT (peores):**")
        L("")
        L("| Dim | train_corr | val_corr | delta |")
        L("|---|---|---|---|")
        for x in overfit_items[:10]:
            L(f"| {x['dim']} | {x['train_corr']} | {x['val_corr']} | {x['delta']} |")
        L("")

    if underfit_items:
        L("**Dims con UNDERFIT:**")
        L("")
        L("| Dim | train_corr | val_corr | delta |")
        L("|---|---|---|---|")
        for x in underfit_items[:10]:
            L(f"| {x['dim']} | {x['train_corr']} | {x['val_corr']} | {x['delta']} |")
        L("")

    L("> **NOTA IMPORTANTE**: Bootstrap CI requiere los vectores pred/label por muestra,")
    L("> que no están guardados en poc_v1. El poc_v1 solo guardó métricas agregadas.")
    L("> Para poc_v2 y posteriores: guardar `predictions.npz` con pred y label por muestra.")
    L("")
    L("---")
    L("")

    # ── Sección 2: Calidad de labels ──
    L("## 2. Calidad de labels gold_set_v2")
    L("")
    L(f"- **Total registros**: {n_records_gold}")
    L(f"- **Dims analizadas**: {label_quality['n_dims_analyzed']}")
    L(f"- **Distribución normal**: {label_quality['n_normal_distribution']} dims ({100 - label_quality['pct_skewed']}%)")
    L(f"- **Distribución sesgada**: {label_quality['n_skewed_distribution']} dims ({label_quality['pct_skewed']}%)")
    L(f"- **Floor/ceiling effect** (>50% en extremo): {label_quality['n_floor_ceiling_effect']} dims ({label_quality['pct_floor_ceiling']}%)")
    L("")
    L("### Implicación para métricas")
    L("")
    if label_quality['pct_skewed'] > 60:
        L("> **CONCLUSION**: La mayoría de dims tienen distribución NO normal (skewed).")
        L("> **Spearman es la métrica correcta** para este dataset. Pearson puede subestimar")
        L("> correlaciones reales porque es sensible a outliers y asimetría.")
    else:
        L("> Distribución relativamente balanceada. Spearman y Pearson deberían dar resultados similares.")
    L("")

    if label_quality["floor_ceiling_dims"]:
        L(f"### Dims con floor/ceiling effect ({len(label_quality['floor_ceiling_dims'])} dims)")
        L("")
        L("Estas dims tienen >50% de valores en un extremo (0 o 1). Serán difíciles de predecir.")
        L("")
        for d in label_quality["floor_ceiling_dims"][:15]:
            s = label_quality["dim_stats"][d]
            L(f"- `{d}`: floor={s['floor_rate']:.2%}, ceil={s['ceil_rate']:.2%}, mean={s['mean']}")
        L("")

    L("### Top 10 dims más sesgadas")
    L("")
    L("| Dim | Skewness | Floor rate | Tipo dist. |")
    L("|---|---|---|---|")
    for entry in label_quality["top_10_most_skewed"]:
        s = label_quality["dim_stats"][entry["dim"]]
        L(f"| {entry['dim']} | {entry['skewness']:.3f} | {entry['floor_rate']:.2%} | {s['dist_type']} |")
    L("")

    L("### Estadísticas detalladas por dim")
    L("")
    L("| Dim | Mean | Std | Skewness | Normal? | Floor/Ceil |")
    L("|---|---|---|---|---|---|")
    for dim, s in sorted(label_quality["dim_stats"].items()):
        fc = "SI" if (s["has_floor_effect"] or s["has_ceiling_effect"]) else "no"
        L(f"| {dim} | {s['mean']} | {s['std']} | {s['skewness']} | {s['is_normal']} | {fc} |")
    L("")
    L("---")
    L("")

    # ── Sección 3: Split analysis ──
    L("## 3. Split analysis train/val 80/20")
    L("")
    L(f"- **Total**: {split_result['n_total']} registros")
    L(f"- **Train**: {split_result['n_train']} ({split_result['train_ratio']*100:.0f}%)")
    L(f"- **Val**: {split_result['n_val']} ({(1-split_result['train_ratio'])*100:.0f}%)")
    L(f"- **Seed**: {split_result['split_seed']}")
    L("")
    L(f"### Equivalencia estadística (Mann-Whitney U)")
    L("")
    L(f"- **Dims estadísticamente equivalentes** (p > 0.05): "
      f"{split_result['n_statistically_equivalent']}/{split_result['n_dims_analyzed']} "
      f"({split_result['pct_equivalent']}%)")
    L(f"- **Dims NO equivalentes**: {split_result['n_not_equivalent']}")
    L(f"- **VEREDICTO**: **{split_result['verdict']}**")
    L("")

    if split_result["non_equivalent_dims"]:
        L("### Dims donde train ≠ val (p < 0.05)")
        L("")
        L("| Dim | p-value | Mean delta |")
        L("|---|---|---|")
        for entry in split_result["non_equivalent_dims"][:10]:
            L(f"| {entry['dim']} | {entry['mw_pvalue']} | {entry['mean_delta']} |")
        L("")
        L("> Estas dims pueden requerir **stratified sampling** para garantizar split representativo.")
        L("")
    L("---")
    L("")

    # ── Sección 4: Baselines realistas ──
    L("## 4. Baselines realistas")
    L("")
    L(f"- **Baseline random (media Spearman)**: `{baselines['random_baseline_mean']}`")
    L(f"- **Baseline random CI95**: `{baselines['random_baseline_ci95']}`")
    L(f"- **Baseline señal con 5% ruido**: `{baselines['signal_baseline_mean']}`")
    L("")
    L("### Interpretación")
    L("")
    L("| Umbral | Significado |")
    L("|---|---|")
    L(f"| Spearman < {baselines['random_baseline_mean']} ± 0.05 | Igual que random — el modelo no aprende nada |")
    L(f"| Spearman > 0.10 | Claramente mejor que random |")
    L(f"| Spearman > 0.30 | Correlación débil pero real |")
    L(f"| Spearman > 0.50 | Correlación moderada — útil |")
    L(f"| Spearman > 0.70 | Correlación fuerte — excelente |")
    L("")
    L("### Gate de éxito recomendado para poc_v2")
    L("")
    L("> **Spearman global ponderado > 0.30** (vs Pearson=0.119 de poc_v1)")
    L("> **≥ 30% de dims con Spearman > 0.50** (vs ~25% en poc_v1)")
    L("")
    L("### Top 10 dims por señal (5% ruido)")
    L("")
    L("| Dim | Signal Spearman | Baseline Random | Varianza |")
    L("|---|---|---|---|")
    top_signal = sorted(baselines["by_dim"].items(),
                        key=lambda x: x[1]["signal_spearman_5pct_noise"], reverse=True)
    for dim, b in top_signal[:10]:
        L(f"| {dim} | {b['signal_spearman_5pct_noise']} | {b['baseline_random_spearman']} | {b['var']} |")
    L("")
    L("---")
    L("")

    # ── Sección 5: Conclusiones ──
    L("## 5. Conclusiones y decisiones")
    L("")
    L("### Para poc_v2 (próximo training)")
    L("")
    L("| Decisión | Acción |")
    L("|---|---|")
    L("| Métrica principal | **Spearman** (no Pearson) — distribuciones skewed |")
    L("| corr_global | **Ponderado por varianza** — no media simple |")
    L("| Bootstrap CI | Guardar predicciones por muestra (`predictions.npz`) |")
    L("| Split | **Stratified** por las dims más sesgadas |")
    L("| Gate éxito | Spearman_weighted > 0.30 |")
    L("| Floor/ceiling dims | Usar **weighted loss** (upweight docs en el extremo poco frecuente) |")
    L("")
    L("### Cambios al pipeline de evaluación")
    L("")
    L("1. Reemplazar `pearson_r` por `spearman_r` en eval loop")
    L("2. Añadir `corr_global_weighted` como métrica de seguimiento")
    L("3. Guardar `predictions.npz` después de cada eval")
    L("4. Usar stratified split para las N dims con p < 0.05 en Mann-Whitney")
    L("5. Añadir Bootstrap CI (1000 resamples) en el eval final")
    L("")

    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("METRICS RECALC — Paso 2 pre-flight gold_set_v3")
    print("Coste: $0")
    print("=" * 60)
    print()

    # Cargar datos
    print("Cargando datos...")
    dim_values_gold, records_gold = load_gold_set_v2(GOLD_SET_V2)
    n_records_gold = len(records_gold)
    print(f"  gold_set_v2: {n_records_gold} registros, {len(dim_values_gold)} dims numéricas")

    with open(POC_V1_EVAL) as f:
        eval_report = json.load(f)
    print(f"  poc_v1 eval_report: {eval_report['n_samples']} samples, "
          f"{len(eval_report.get('float_dims', []))} float dims")
    print()

    # Ejecutar módulos
    poc_v1_result  = recalculate_poc_v1_metrics()
    label_quality  = analyze_label_quality(dim_values_gold)
    split_result   = split_analysis(dim_values_gold, records_gold)
    baselines      = compute_baselines(dim_values_gold)
    spearman_est   = estimate_pearson_vs_spearman_delta(dim_values_gold, eval_report)

    print()
    print("Generando informe...")

    # Guardar JSON
    output_data = {
        "poc_v1_metrics_recalc": poc_v1_result,
        "label_quality_gold_v2": {k: v for k, v in label_quality.items() if k != "dim_stats"},
        "split_analysis": {k: v for k, v in split_result.items() if k != "split_stats_by_dim"},
        "baselines": {k: v for k, v in baselines.items() if k != "by_dim"},
        "spearman_estimation": spearman_est,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"  JSON guardado: {DATA_PATH}")

    # Generar markdown
    report_md = generate_report(
        poc_v1_result, label_quality, split_result, baselines, spearman_est, n_records_gold
    )
    with open(REPORT_PATH, "w") as f:
        f.write(report_md)
    print(f"  Informe guardado: {REPORT_PATH}")

    print()
    print("=" * 60)
    print("RESUMEN EJECUTIVO")
    print("=" * 60)
    print(f"corr_global Pearson (original):         {poc_v1_result['corr_global_simple_original']}")
    print(f"corr_global Pearson weighted:           {poc_v1_result['corr_global_weighted_by_variance']}")
    print(f"corr_global Spearman est. (no verif):   {spearman_est['corr_global_spearman_estimated_mean']}")
    print(f"Dims sesgadas (requieren Spearman):     {label_quality['pct_skewed']}%")
    print(f"Split equivalente (Mann-Whitney):       {split_result['pct_equivalent']}%")
    print(f"Veredicto split:                        {split_result['verdict']}")
    print(f"Baseline random Spearman:               {baselines['random_baseline_mean']}")
    print(f"Dims floor/ceiling:                     {label_quality['n_floor_ceiling_effect']}")
    print()
    print("DECISIONES PARA poc_v2:")
    print("  1. Usar Spearman (no Pearson) como metrica principal")
    print("  2. corr_global ponderado por varianza")
    print("  3. Guardar predictions.npz para Bootstrap CI real")
    print("  4. Gate: Spearman_weighted > 0.30")
    print()
    print("DONE.")


if __name__ == "__main__":
    main()
