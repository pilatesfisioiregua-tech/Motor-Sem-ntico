"""Evalúa outputs mapeándolos a la Matriz 3 Lentes × 7 Funciones (21 celdas).
Soporta múltiples modelos: 70B, Maverick, DeepSeek-R1, Qwen3-235B, DeepSeek-V3.1, Claude (ref)."""
import json
import os
import sys
import time
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
import anthropic

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY no configurada.")
    sys.exit(1)

MODEL = "claude-sonnet-4-20250514"
OUTPUT_DIR = BASE_DIR / "outputs"
RESULTS_DIR = BASE_DIR / "results"
CACHE_FILE = RESULTS_DIR / "matrix_evaluations.json"

LENTES = ["Salud", "Sentido", "Continuidad"]
FUNCIONES = ["Conservar", "Captar", "Depurar", "Distribuir", "Frontera", "Adaptar", "Replicar"]
ALL_CELLS = [f"{l}×{f}" for l in LENTES for f in FUNCIONES]

# All OS models to evaluate (variant C)
OS_MODELS = ["70B", "Maverick", "DeepSeek-R1", "Qwen3.5-397B", "DeepSeek-V3.1", "GPT-OSS-120B",
             "Qwen3-Thinking", "Kimi-K2.5", "Cogito-671B",
             "DeepSeek-V3.2-Chat", "DeepSeek-V3.2-Reasoner"]

# Display order for reports
ALL_SOURCES = OS_MODELS + ["claude"]

CASE_NAMES = {
    "clinica_dental": "Clínica Dental",
    "startup_saas": "Startup SaaS",
    "cambio_carrera": "Cambio de Carrera",
}
INT_NAMES = {
    "INT-01": "Lógico-Matemática",
    "INT-08": "Social",
    "INT-16": "Constructiva",
}

SOURCE_LABELS = {
    "70B": "70B",
    "Maverick": "Maverick",
    "DeepSeek-R1": "DeepSeek R1",
    "Qwen3.5-397B": "Qwen3.5 397B",
    "DeepSeek-V3.1": "DeepSeek V3.1",
    "GPT-OSS-120B": "GPT-OSS 120B",
    "Qwen3-Thinking": "Qwen3 Thinking",
    "Kimi-K2.5": "Kimi K2.5",
    "Cogito-671B": "Cogito 671B",
    "DeepSeek-V3.2-Chat": "DS-V3.2 Chat",
    "DeepSeek-V3.2-Reasoner": "DS-V3.2 Reasoner",
    "claude": "Claude (ref)",
    "maverick": "Maverick",  # Legacy key compat
}


def build_eval_prompt(output_text: str) -> str:
    return f"""Mapea el siguiente análisis a las 21 celdas de la Matriz (3 Lentes × 7 Funciones).

Las 3 Lentes:
- Salud: ¿Funciona? ¿Hay disfunción?
- Sentido: ¿Tiene dirección? ¿Hay propósito?
- Continuidad: ¿Sobrevive más allá del sistema? ¿Es replicable?

Las 7 Funciones:
- F1 Conservar: ¿Qué se conserva? ¿Debería conservarse?
- F2 Captar: ¿Qué capta? ¿Qué no capta?
- F3 Depurar: ¿Qué filtra mal? ¿Qué basura entra?
- F4 Distribuir: ¿Cómo distribuye? ¿Dónde no llega?
- F5 Frontera: ¿Dónde está el límite? ¿Es permeable?
- F6 Adaptar: ¿Se adapta? ¿Hay rigidez?
- F7 Replicar: ¿Es replicable? ¿Sobrevive al creador?

Para cada celda, asigna un nivel:
0 = no toca esta celda
1 = la menciona genéricamente
2 = dato o inferencia específica del caso
3 = revela algo no obvio (contradicción, patrón invisible, restricción oculta)
4 = redefine la pregunta del caso desde esta celda

## ANÁLISIS A EVALUAR

{output_text}

Responde SOLO con JSON válido (sin markdown):
{{
  "celdas": {{
    "Salud×Conservar": {{"nivel": N, "evidencia": "frase corta del output que lo demuestra"}},
    "Salud×Captar": {{"nivel": N, "evidencia": "..."}},
    "Salud×Depurar": {{"nivel": N, "evidencia": "..."}},
    "Salud×Distribuir": {{"nivel": N, "evidencia": "..."}},
    "Salud×Frontera": {{"nivel": N, "evidencia": "..."}},
    "Salud×Adaptar": {{"nivel": N, "evidencia": "..."}},
    "Salud×Replicar": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Conservar": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Captar": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Depurar": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Distribuir": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Frontera": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Adaptar": {{"nivel": N, "evidencia": "..."}},
    "Sentido×Replicar": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Conservar": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Captar": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Depurar": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Distribuir": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Frontera": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Adaptar": {{"nivel": N, "evidencia": "..."}},
    "Continuidad×Replicar": {{"nivel": N, "evidencia": "..."}}
  }},
  "total_cubiertas": N,
  "nivel_medio": X.X,
  "celdas_nivel_3_plus": ["lista de celdas con nivel 3 o 4"],
  "celdas_vacias": ["lista de celdas con nivel 0"]
}}"""


def call_sonnet(client: anthropic.Anthropic, prompt: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text
    try:
        j_start = raw.find("{")
        j_end = raw.rfind("}") + 1
        return json.loads(raw[j_start:j_end]) if j_start >= 0 else {"error": "No JSON", "raw": raw}
    except json.JSONDecodeError:
        return {"error": "JSON inválido", "raw": raw}


def eval_key(source: str, case_id: str, int_id: str) -> str:
    return f"{source}_{case_id}_{int_id}"


def load_cache() -> dict:
    if CACHE_FILE.exists():
        with open(CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache: dict):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def load_os_model_outputs(model_key: str) -> list[dict]:
    """Load variant C outputs for a given model."""
    with open(OUTPUT_DIR / "all_outputs.json", encoding="utf-8") as f:
        data = json.load(f)
    return [d for d in data
            if d.get("model_key") == model_key
            and d.get("variant") == "C"
            and "error" not in d]


def load_reference() -> list[dict]:
    with open(BASE_DIR / "data" / "reference_outputs.json", encoding="utf-8") as f:
        ref = json.load(f)
    items = []
    for int_id, cases in ref["outputs"].items():
        for case_id, data in cases.items():
            hallazgos = "\n".join(f"- {h}" for h in data["hallazgos_clave"])
            text = f"RESUMEN: {data['resumen']}\n\nFIRMA: {data['firma']}\n\nHALLAZGOS CLAVE:\n{hallazgos}"
            items.append({
                "case_id": case_id,
                "int_id": int_id,
                "output": text,
                "source": "claude",
            })
    return items


def evaluate_all():
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    cache = load_cache()

    # Build work list for all models
    work = []

    for model_key in OS_MODELS:
        items = load_os_model_outputs(model_key)
        source_key = model_key.lower()  # cache key uses lowercase
        for item in items:
            key = eval_key(source_key, item["case_id"], item["int_id"])
            if key not in cache:
                work.append((source_key, item["case_id"], item["int_id"], item["output"]))

    # Claude reference
    claude_items = load_reference()
    for item in claude_items:
        key = eval_key("claude", item["case_id"], item["int_id"])
        if key not in cache:
            work.append(("claude", item["case_id"], item["int_id"], item["output"]))

    print(f"Total a evaluar: {len(work)} (cache: {len(cache)})")

    for i, (source, case_id, int_id, output) in enumerate(work):
        label = f"{source}/{CASE_NAMES.get(case_id, case_id)} × {INT_NAMES.get(int_id, int_id)}"
        print(f"[{i+1}/{len(work)}] {label}...", end=" ", flush=True)

        prompt = build_eval_prompt(output)
        t0 = time.time()
        result = call_sonnet(client, prompt)
        elapsed = round(time.time() - t0, 2)

        key = eval_key(source, case_id, int_id)
        cache[key] = {
            "source": source,
            "case_id": case_id,
            "int_id": int_id,
            "result": result,
            "tiempo_s": elapsed,
        }

        if "error" in result:
            print(f"ERROR ({elapsed}s)")
        else:
            nc = result.get("total_cubiertas", "?")
            nm = result.get("nivel_medio", "?")
            print(f"OK (cubiertas={nc}, medio={nm}, {elapsed}s)")

        save_cache(cache)
        if i < len(work) - 1:
            time.sleep(1)

    return cache


# ── Report Generation ──────────────────────────────────────────


def _source_key(model_key: str) -> str:
    """Map model_key to cache source key."""
    return model_key.lower()


def _collect_levels(cache: dict) -> dict:
    """Returns {source: {cell: [niveles across 9 combos]}}."""
    levels = defaultdict(lambda: defaultdict(list))
    combos_seen = defaultdict(set)

    for key, entry in cache.items():
        result = entry.get("result", {})
        if "error" in result:
            continue
        source = entry["source"]
        case_id = entry["case_id"]
        int_id = entry["int_id"]
        combo = f"{case_id}_{int_id}"
        celdas = result.get("celdas", {})

        combos_seen[source].add(combo)
        for cell in ALL_CELLS:
            nivel = celdas.get(cell, {}).get("nivel", 0)
            levels[source][cell].append(nivel)

    return dict(levels)


def generate_multi_model_report(cache: dict) -> str:
    levels = _collect_levels(cache)
    lines = []

    lines.append("# MULTI-MODEL MATRIX COVERAGE REPORT")
    lines.append("")
    lines.append("Comparativa de cobertura sobre la Matriz 3 Lentes × 7 Funciones (21 celdas).")
    lines.append("Todos los modelos OS ejecutan variante C (instrucción analítica).")
    lines.append("")
    lines.append("**Niveles:** 0=no toca, 1=genérico, 2=dato específico, 3=no obvio, 4=redefine la pregunta")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Map source keys we expect
    source_keys = []
    source_labels = []
    for mk in OS_MODELS:
        sk = _source_key(mk)
        # Handle legacy 'maverick' key
        if sk not in levels and mk.lower() != sk:
            sk = mk.lower()
        if sk in levels:
            source_keys.append(sk)
            source_labels.append(SOURCE_LABELS.get(mk, mk))
    if "claude" in levels:
        source_keys.append("claude")
        source_labels.append("Claude (ref)")

    def _avg(source_key, cells=None):
        if cells is None:
            cells = ALL_CELLS
        vals = []
        for c in cells:
            vals.extend(levels.get(source_key, {}).get(c, []))
        return sum(vals) / max(len(vals), 1)

    def _covered(source_key):
        count = 0
        for cell in ALL_CELLS:
            ns = levels.get(source_key, {}).get(cell, [])
            if ns and sum(1 for n in ns if n >= 2) > len(ns) / 2:
                count += 1
        return count

    # ── TABLA 1: Nivel medio por Lente ──
    lines.append("## Tabla 1 — Nivel medio por Lente")
    lines.append("")

    header = "| Modelo | Salud | Sentido | Continuidad | Total celdas | Nivel medio |"
    sep = "|--------|-------|---------|-------------|-------------|-------------|"
    lines.append(header)
    lines.append(sep)

    for sk, label in zip(source_keys, source_labels):
        salud = _avg(sk, [c for c in ALL_CELLS if c.startswith("Salud")])
        sentido = _avg(sk, [c for c in ALL_CELLS if c.startswith("Sentido")])
        continuidad = _avg(sk, [c for c in ALL_CELLS if c.startswith("Continuidad")])
        total_c = _covered(sk)
        medio = _avg(sk)
        lines.append(f"| {label} | {salud:.2f} | {sentido:.2f} | {continuidad:.2f} | {total_c}/21 | {medio:.2f} |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # ── TABLA 2: Nivel medio por Función ──
    lines.append("## Tabla 2 — Nivel medio por Función")
    lines.append("")

    header = "| Modelo |"
    sep = "|--------|"
    for f in FUNCIONES:
        header += f" {f} |"
        sep += "---------|"
    lines.append(header)
    lines.append(sep)

    for sk, label in zip(source_keys, source_labels):
        row = f"| {label} |"
        for func in FUNCIONES:
            cells_f = [c for c in ALL_CELLS if c.endswith(func)]
            v = _avg(sk, cells_f)
            row += f" {v:.2f} |"
        lines.append(row)
    lines.append("")

    lines.append("---")
    lines.append("")

    # ── TABLA 3: Mejor modelo por celda ──
    lines.append("## Tabla 3 — Mejor modelo por celda (nivel medio más alto)")
    lines.append("")

    header = "| |"
    sep = "|---|"
    for f in FUNCIONES:
        header += f" {f} |"
        sep += "---------|"
    lines.append(header)
    lines.append(sep)

    for lente in LENTES:
        row = f"| **{lente}** |"
        for func in FUNCIONES:
            cell = f"{lente}×{func}"
            best_val = -1
            best_model = "—"
            for sk, label in zip(source_keys, source_labels):
                ns = levels.get(sk, {}).get(cell, [])
                if ns:
                    mean = sum(ns) / len(ns)
                    if mean > best_val:
                        best_val = mean
                        best_model = label
            # Short label
            short = best_model.replace(" (ref)", "").replace("DeepSeek ", "DS-")
            row += f" {short} ({best_val:.1f}) |"
        lines.append(row)
    lines.append("")

    lines.append("---")
    lines.append("")

    # ── TABLA 4: Ranking global ──
    lines.append("## Tabla 4 — Ranking global")
    lines.append("")
    lines.append("| # | Modelo | Nivel medio | Celdas cubiertas | Celdas nivel 3+ |")
    lines.append("|---|--------|-------------|-----------------|-----------------|")

    ranking = []
    for sk, label in zip(source_keys, source_labels):
        medio = _avg(sk)
        covered = _covered(sk)
        n3plus = 0
        for cell in ALL_CELLS:
            ns = levels.get(sk, {}).get(cell, [])
            if ns and (sum(ns) / len(ns)) >= 2.5:  # average suggests 3+ frequent
                n3plus += 1
        ranking.append((label, medio, covered, n3plus))

    ranking.sort(key=lambda x: x[1], reverse=True)
    for i, (label, medio, covered, n3) in enumerate(ranking):
        lines.append(f"| {i+1} | {label} | {medio:.2f} | {covered}/21 | {n3}/21 |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # ── HEATMAP: all models ──
    lines.append("## Heatmap — Nivel medio por celda (todos los modelos)")
    lines.append("")
    lines.append("```")

    # Header
    col_w = 10
    hdr = f"{'':>16} |"
    for f in FUNCIONES:
        hdr += f" {f:>{col_w}} |"
    lines.append(hdr)
    lines.append(f"{'':>16} |" + (f"{'':->12}|" * 7))

    for sk, label in zip(source_keys, source_labels):
        short = label[:12]
        for lente in LENTES:
            tag = f"{short[:4]}/{lente[:4]}"
            row = f"{tag:>16} |"
            for func in FUNCIONES:
                cell = f"{lente}×{func}"
                ns = levels.get(sk, {}).get(cell, [])
                mean = sum(ns) / max(len(ns), 1) if ns else 0
                bar = "█" * int(mean) + "░" * (4 - int(mean))
                row += f" {bar} {mean:.1f} |"
            lines.append(row)
        lines.append(f"{'':>16} |" + (f"{'':->12}|" * 7))

    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("*Generado por evaluate_matrix_coverage.py*")

    return "\n".join(lines)


def generate_legacy_report(cache: dict) -> str:
    """Generate the original Maverick-vs-Claude report for backwards compat."""
    levels = _collect_levels(cache)

    maverick_key = "maverick"
    claude_key = "claude"

    if maverick_key not in levels or claude_key not in levels:
        return "# No hay datos suficientes para Maverick vs Claude report"

    # (keeping original report generation logic for MATRIX_COVERAGE_REPORT.md)
    # Simplified — just regenerate from cache
    lines = ["# MATRIX COVERAGE REPORT — Maverick vs Claude", "",
             "*(Ver MULTI_MODEL_COVERAGE_REPORT.md para comparativa completa)*", ""]
    return "\n".join(lines)


def main():
    cache = evaluate_all()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Multi-model report
    report = generate_multi_model_report(cache)
    report_path = RESULTS_DIR / "MULTI_MODEL_COVERAGE_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReporte multi-modelo: {report_path}")


if __name__ == "__main__":
    main()
