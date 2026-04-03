#!/usr/bin/env python3
"""
Data Audit — Gold Set v2
Track B del plan de ejecucion.

Analiza el gold set v2 (2990 textos, 51 dims) y produce:
- Resumen en consola
- Informe completo en motor-semantico/experiments/gold_set_v1/data_audit_report.md
- Matriz de correlacion en motor-semantico/experiments/gold_set_v1/correlation_matrix.csv

Uso: python motor-semantico/scripts/training/data_audit.py
"""

import json
import sys
import os
import csv
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Dependencias (stdlib + basicas)
# ---------------------------------------------------------------------------
try:
    import numpy as np
except ImportError:
    print("ERROR: numpy no disponible. Instalar: pip install numpy")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas no disponible. Instalar: pip install pandas")
    sys.exit(1)

# scipy es opcional — lo usamos solo para Pearson; si no esta, usamos pandas
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]  # omni-mind-cerebro/
DATA_FILE = REPO_ROOT / "motor-semantico/data/gold_set_v2_3000.jsonl"
OUT_DIR   = REPO_ROOT / "motor-semantico/experiments/gold_set_v1"
REPORT_MD = OUT_DIR / "data_audit_report.md"
CORR_CSV  = OUT_DIR / "correlation_matrix.csv"

# Dims binarias conocidas (prefijo h)
BINARY_DIMS = [
    "h01_confirmacion",
    "h04_autoridad_implicita",
    "h12_granularidad_falsa",
    "h14_causalidad_narrativa",
    "h22_validacion_social",
    "h25_aversion_perdida",
    "h26_framing",
    "h55_atribucion_autoservicio",
    "h62_difusion_resp_cognitiva",
    "h77_reificacion_categorias",
]

# Umbrales
VAR_DEAD_THRESHOLD    = 0.05   # varianza < 0.05 → dim muerta
CORR_FUSION_THRESHOLD = 0.85   # |r| > 0.85 → candidata a fusion
CORR_REDUND_THRESHOLD = 0.90   # |r| > 0.90 → redundante
IMBALANCE_THRESHOLD   = 0.05   # < 5% de 1s → imbalanced (binarias)
PCT_ZERO_DEAD         = 0.95   # >= 95% zeros → dim muerta por saturacion


# ---------------------------------------------------------------------------
# 1. Carga de datos
# ---------------------------------------------------------------------------
def load_data(path: Path):
    if not path.exists():
        print(f"ERROR: archivo no encontrado: {path}")
        sys.exit(1)

    records = []
    errors  = 0
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                errors += 1
                print(f"  WARN: linea {i} no es JSON valido: {e}")

    print(f"Cargados {len(records)} registros ({errors} errores de parse).")
    return records


# ---------------------------------------------------------------------------
# 2. Construir DataFrame de labels
# ---------------------------------------------------------------------------
def build_df(records):
    rows = []
    ids  = []
    for r in records:
        ids.append(r.get("id", ""))
        labels = r.get("labels", {})
        # convertir None a NaN
        row = {}
        for k, v in labels.items():
            if v is None:
                row[k] = float("nan")
            else:
                try:
                    row[k] = float(v)
                except (ValueError, TypeError):
                    row[k] = float("nan")
        rows.append(row)

    df = pd.DataFrame(rows, index=ids)
    return df


# ---------------------------------------------------------------------------
# 3. Estadisticas por dimension
# ---------------------------------------------------------------------------
def dim_stats(df: pd.DataFrame):
    results = []
    for col in df.columns:
        s = df[col].dropna()
        n_total   = len(df)
        n_valid   = len(s)
        n_missing = n_total - n_valid

        mean   = float(s.mean())   if n_valid > 0 else float("nan")
        median = float(s.median()) if n_valid > 0 else float("nan")
        std    = float(s.std())    if n_valid > 0 else float("nan")
        var    = float(s.var())    if n_valid > 0 else float("nan")
        mn     = float(s.min())    if n_valid > 0 else float("nan")
        mx     = float(s.max())    if n_valid > 0 else float("nan")

        pct_zero = float((s == 0.0).sum() / n_valid) if n_valid > 0 else float("nan")
        pct_one  = float((s == 1.0).sum() / n_valid) if n_valid > 0 else float("nan")

        is_binary = col in BINARY_DIMS

        # Dim muerta: varianza muy baja O >= 95% de los valores son 0
        is_dead = (var < VAR_DEAD_THRESHOLD) or (pct_zero >= PCT_ZERO_DEAD)

        # Imbalanced (solo binarias): < 5% de 1s
        is_imbalanced = is_binary and (pct_one < IMBALANCE_THRESHOLD)

        results.append({
            "dim":           col,
            "is_binary":     is_binary,
            "n_valid":       n_valid,
            "n_missing":     n_missing,
            "mean":          mean,
            "median":        median,
            "std":           std,
            "var":           var,
            "min":           mn,
            "max":           mx,
            "pct_zero":      pct_zero,
            "pct_one":       pct_one,
            "is_dead":       is_dead,
            "is_imbalanced": is_imbalanced,
        })

    return results


# ---------------------------------------------------------------------------
# 4. Textos sospechosos
# ---------------------------------------------------------------------------
def suspicious_texts(df: pd.DataFrame):
    suspicious = []

    # Todos en cero
    all_zero_mask = (df == 0).all(axis=1)
    all_zero_ids  = list(df[all_zero_mask].index)

    # Pattern repetitivo: todos los valores de las 51 dims identicos
    def is_repetitive(row):
        vals = row.dropna().unique()
        return len(vals) <= 2  # solo 2 valores distintos en 51 dims

    rep_mask = df.apply(is_repetitive, axis=1)
    rep_ids  = list(df[rep_mask & ~all_zero_mask].index)

    return all_zero_ids, rep_ids


# ---------------------------------------------------------------------------
# 5. Correlacion
# ---------------------------------------------------------------------------
def correlation_analysis(df: pd.DataFrame):
    # Usar solo columnas con suficiente varianza
    valid_cols = [c for c in df.columns if df[c].var() > 1e-8]
    df_valid   = df[valid_cols].dropna()

    corr = df_valid.corr(method="pearson")

    # Pares con alta correlacion
    fusion_pairs   = []
    redundant_pairs = []

    cols = list(corr.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            r = corr.iloc[i, j]
            if abs(r) > CORR_REDUND_THRESHOLD:
                redundant_pairs.append((cols[i], cols[j], round(r, 4)))
            elif abs(r) > CORR_FUSION_THRESHOLD:
                fusion_pairs.append((cols[i], cols[j], round(r, 4)))

    # Ordenar por correlacion descendente
    fusion_pairs.sort(key=lambda x: abs(x[2]), reverse=True)
    redundant_pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    return corr, fusion_pairs, redundant_pairs, valid_cols


# ---------------------------------------------------------------------------
# 6. Calidad general
# ---------------------------------------------------------------------------
def quality_summary(records, stats, all_zero_ids, rep_ids, fusion_pairs, redundant_pairs):
    n_total      = len(records)
    n_dead       = sum(1 for s in stats if s["is_dead"])
    n_imbalanced = sum(1 for s in stats if s["is_imbalanced"])
    n_redundant  = len(redundant_pairs)
    n_fusion     = len(fusion_pairs)

    print("\n" + "="*70)
    print("DATA AUDIT — GOLD SET V2")
    print("="*70)
    print(f"Textos cargados:          {n_total}")
    print(f"Dimensiones analizadas:   {len(stats)} (10 binarias + 41 continuas)")
    print(f"Dims muertas (var<0.05 o 95%+ zeros): {n_dead}")
    print(f"Dims binarias desbalanceadas (<5% 1s): {n_imbalanced}")
    print(f"Pares redundantes (|r|>0.90):          {n_redundant}")
    print(f"Pares candidatos fusion (|r|>0.85):    {n_fusion}")
    print(f"Textos todo-cero:         {len(all_zero_ids)}")
    print(f"Textos pattern repetitivo:{len(rep_ids)}")
    print("="*70)

    # Dims muertas
    dead = [s for s in stats if s["is_dead"]]
    if dead:
        print(f"\nDIMS MUERTAS ({len(dead)}):")
        for s in dead:
            reason = "var<0.05" if s["var"] < VAR_DEAD_THRESHOLD else "95%+ zeros"
            print(f"  {s['dim']:<35} var={s['var']:.4f}  pct_zero={s['pct_zero']:.2%}  [{reason}]")

    # Dims imbalanceadas (binarias)
    imb = [s for s in stats if s["is_imbalanced"]]
    if imb:
        print(f"\nDIMS BINARIAS DESBALANCEADAS ({len(imb)}):")
        for s in imb:
            print(f"  {s['dim']:<35} pct_one={s['pct_one']:.2%}")

    # Pares redundantes
    if redundant_pairs:
        print(f"\nPARES REDUNDANTES |r|>0.90 ({len(redundant_pairs)}):")
        for a, b, r in redundant_pairs[:15]:
            print(f"  {a} <-> {b}  r={r:.4f}")

    # Pares fusion
    if fusion_pairs:
        print(f"\nCANDIDATOS A FUSION |r|>0.85 ({len(fusion_pairs)}):")
        for a, b, r in fusion_pairs[:15]:
            print(f"  {a} <-> {b}  r={r:.4f}")

    if all_zero_ids:
        print(f"\nTEXTOS TODO-CERO ({len(all_zero_ids)}) — primeros 5:")
        for i in all_zero_ids[:5]:
            print(f"  id={i}")

    print()


# ---------------------------------------------------------------------------
# 7. Guardar informe MD
# ---------------------------------------------------------------------------
def save_report(records, stats, corr, fusion_pairs, redundant_pairs,
                all_zero_ids, rep_ids, valid_cols):
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# Data Audit — Gold Set V2\n")
    lines.append(f"**Generado**: {ts}  \n")
    lines.append(f"**Textos**: {len(records)}  \n")
    lines.append(f"**Dims**: 51 (10 binarias h* + 41 continuas)  \n\n")

    # --- Resumen ejecutivo
    n_dead       = sum(1 for s in stats if s["is_dead"])
    n_imbalanced = sum(1 for s in stats if s["is_imbalanced"])

    lines.append("## Resumen ejecutivo\n\n")
    lines.append(f"| Metrica | Valor |\n|---|---|\n")
    lines.append(f"| Textos cargados | {len(records)} |\n")
    lines.append(f"| Dims muertas | {n_dead} |\n")
    lines.append(f"| Dims binarias desbalanceadas | {n_imbalanced} |\n")
    lines.append(f"| Pares redundantes (|r|>0.90) | {len(redundant_pairs)} |\n")
    lines.append(f"| Candidatos fusion (|r|>0.85) | {len(fusion_pairs)} |\n")
    lines.append(f"| Textos todo-cero | {len(all_zero_ids)} |\n")
    lines.append(f"| Textos pattern repetitivo | {len(rep_ids)} |\n")
    lines.append("\n")

    # --- Estadisticas por dim
    lines.append("## Estadisticas por dimension\n\n")
    lines.append("| Dim | Tipo | Media | Median | Std | Var | Min | Max | "
                 "pct_zero | pct_one | Estado |\n")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for s in stats:
        tipo   = "binaria" if s["is_binary"] else "continua"
        estado = []
        if s["is_dead"]:       estado.append("MUERTA")
        if s["is_imbalanced"]: estado.append("IMBALANCED")
        estado_str = ", ".join(estado) if estado else "OK"

        def fmt(v):
            if v != v:  # nan
                return "nan"
            return f"{v:.4f}"

        lines.append(
            f"| {s['dim']} | {tipo} | {fmt(s['mean'])} | {fmt(s['median'])} | "
            f"{fmt(s['std'])} | {fmt(s['var'])} | {fmt(s['min'])} | {fmt(s['max'])} | "
            f"{s['pct_zero']:.2%} | {s['pct_one']:.2%} | {estado_str} |\n"
        )
    lines.append("\n")

    # --- Dims binarias: class balance
    lines.append("## Class balance (dims binarias)\n\n")
    lines.append("| Dim | % 1s | % 0s | Estado |\n|---|---|---|---|\n")
    for s in stats:
        if s["is_binary"]:
            estado = "IMBALANCED (<5% de 1s)" if s["is_imbalanced"] else "OK"
            lines.append(f"| {s['dim']} | {s['pct_one']:.2%} | {s['pct_zero']:.2%} | {estado} |\n")
    lines.append("\n")

    # --- Pares redundantes
    lines.append("## Pares redundantes |r| > 0.90\n\n")
    if redundant_pairs:
        lines.append("| Dim A | Dim B | r |\n|---|---|---|\n")
        for a, b, r in redundant_pairs:
            lines.append(f"| {a} | {b} | {r:.4f} |\n")
    else:
        lines.append("_Ninguno._\n")
    lines.append("\n")

    # --- Candidatos fusion
    lines.append("## Candidatos a fusion |r| > 0.85\n\n")
    if fusion_pairs:
        lines.append("| Dim A | Dim B | r |\n|---|---|---|\n")
        for a, b, r in fusion_pairs:
            lines.append(f"| {a} | {b} | {r:.4f} |\n")
    else:
        lines.append("_Ninguno._\n")
    lines.append("\n")

    # --- Textos sospechosos
    lines.append("## Textos sospechosos\n\n")
    if all_zero_ids:
        lines.append(f"### Todo-cero ({len(all_zero_ids)} textos)\n\n")
        for i in all_zero_ids[:20]:
            lines.append(f"- `{i}`\n")
        if len(all_zero_ids) > 20:
            lines.append(f"- _(y {len(all_zero_ids)-20} mas)_\n")
        lines.append("\n")
    else:
        lines.append("**Todo-cero**: ninguno.  \n")

    if rep_ids:
        lines.append(f"### Pattern repetitivo ({len(rep_ids)} textos)\n\n")
        for i in rep_ids[:20]:
            lines.append(f"- `{i}`\n")
        if len(rep_ids) > 20:
            lines.append(f"- _(y {len(rep_ids)-20} mas)_\n")
        lines.append("\n")
    else:
        lines.append("**Pattern repetitivo**: ninguno.  \n")

    lines.append("\n---\n")
    lines.append(f"_Audit generado automaticamente por `data_audit.py` — {ts}_\n")

    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Informe guardado: {REPORT_MD}")


# ---------------------------------------------------------------------------
# 8. Guardar CSV correlacion
# ---------------------------------------------------------------------------
def save_correlation_csv(corr: pd.DataFrame):
    corr.to_csv(CORR_CSV, float_format="%.4f")
    print(f"Matriz correlacion guardada: {CORR_CSV}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print(f"\nData Audit — Gold Set V2")
    print(f"Archivo: {DATA_FILE}")
    print(f"Salida:  {OUT_DIR}\n")

    # Asegurar directorio de salida
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Carga
    records = load_data(DATA_FILE)

    # 2. DataFrame
    df = build_df(records)
    print(f"DataFrame shape: {df.shape}  (textos x dims)")
    n_missing_total = df.isna().sum().sum()
    print(f"Valores missing totales: {n_missing_total}")

    # 3. Estadisticas
    stats = dim_stats(df)

    # 4. Textos sospechosos
    all_zero_ids, rep_ids = suspicious_texts(df)

    # 5. Correlacion
    print("\nCalculando matriz de correlacion (Pearson)...")
    corr, fusion_pairs, redundant_pairs, valid_cols = correlation_analysis(df)
    print(f"Dims con varianza suficiente para correlacion: {len(valid_cols)}")

    # 6. Resumen en consola
    quality_summary(records, stats, all_zero_ids, rep_ids, fusion_pairs, redundant_pairs)

    # 7. Detalle binarias en consola
    print("CLASS BALANCE (dims binarias):")
    for s in stats:
        if s["is_binary"]:
            flag = " <-- IMBALANCED" if s["is_imbalanced"] else ""
            print(f"  {s['dim']:<35} 1s={s['pct_one']:.2%}  0s={s['pct_zero']:.2%}{flag}")

    # 8. Guardar artefactos
    print()
    save_report(records, stats, corr, fusion_pairs, redundant_pairs, all_zero_ids, rep_ids, valid_cols)
    save_correlation_csv(corr)

    # Resumen final de alertas
    n_dead       = sum(1 for s in stats if s["is_dead"])
    n_imbalanced = sum(1 for s in stats if s["is_imbalanced"])
    print("\n--- ALERTAS PARA EL INGENIERO ---")
    if n_dead:
        print(f"  ALERTA: {n_dead} dims muertas — revisar si incluirlas en training")
    if n_imbalanced:
        print(f"  ALERTA: {n_imbalanced} dims binarias desbalanceadas — considerar oversampling o weight")
    if redundant_pairs:
        print(f"  ALERTA: {len(redundant_pairs)} pares redundantes — candidatos a eliminar/fusionar")
    if all_zero_ids:
        print(f"  ALERTA: {len(all_zero_ids)} textos todo-cero — posibles errores de labeling")
    if rep_ids:
        print(f"  ALERTA: {len(rep_ids)} textos con pattern repetitivo — revisar manualmente")
    if not any([n_dead, n_imbalanced, redundant_pairs, all_zero_ids, rep_ids]):
        print("  Sin alertas criticas.")
    print()


if __name__ == "__main__":
    main()
