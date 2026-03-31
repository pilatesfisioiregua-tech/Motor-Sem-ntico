#!/usr/bin/env python3
"""
Benchmark: Opus vs GPT-5.4 vs Gemini 2.5 Pro
=============================================
Compara 3 modelos en la tarea de labeling de posición cognitiva.
Mide: acuerdo con Opus (referencia), auto-consistencia, coste real.

Usa OpenRouter para todos (una sola API key, formato unificado).

Uso:
  python benchmark_modelos_goldset.py \
    --corpus motor-semantico/corpus/corpus.jsonl \
    --n 30
"""

import json
import os
import sys
import time
import random
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

try:
    from shared_config import config as _cfg
    OPENROUTER_API_KEY = _cfg.OPENROUTER_API_KEY
    ANTHROPIC_API_KEY = _cfg.ANTHROPIC_API_KEY
except ImportError:
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

TELEGRAM_CONFIG = ROOT / "scripts" / "telegram_config.json"
CHAT_ID = "8091188679"

# ── Modelos a comparar ──────────────────────────────────────────────────────

MODELS = {
    "opus": {
        "api": "anthropic",
        "model": "claude-opus-4-20250514",
        "label": "Claude Opus 4",
        "cost_input_1m": 5.00,
        "cost_output_1m": 25.00,
    },
    "gpt54": {
        "api": "openrouter",
        "model": "openai/gpt-5.4",
        "label": "GPT-5.4",
        "cost_input_1m": 2.50,
        "cost_output_1m": 15.00,
    },
    "gemini25pro": {
        "api": "openrouter",
        "model": "google/gemini-2.5-pro-preview-05-06",
        "label": "Gemini 2.5 Pro",
        "cost_input_1m": 1.25,
        "cost_output_1m": 10.00,
    },
}

# ── Prompt (idéntico para todos) ────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un analizador lingüístico-cognitivo experto. Tu tarea es identificar
la POSICIÓN DEL OBSERVADOR en un texto, basándote en la estructura gramatical,
no en el contenido semántico.

## Las tres posiciones (Teoría Unificada §16)

### RAZONAMIENTO — posición SUJETO
El texto opera clasificando sujetos en conjuntos. Señales gramaticales:
- Verbos copulativos dominantes: "es", "resulta", "pertenece a", "se clasifica como"
- Adjetivos predicativos: "es viable", "resulta ineficiente", "parece sostenible"
- Estructura dominante: SUJETO + copulativo + ADJETIVO/CLASE
- Operaciones de membresía: incluir/excluir/comparar/jerarquizar sujetos
- Pregunta implícita: "¿A qué conjunto pertenece X?" / "¿Qué propiedades hereda X?"

### PENSAMIENTO — posición PREDICADO
El texto opera sobre procesos, nominalizándolos o descomponiéndolos. Señales:
- Verbos de acción dominantes: "implementar", "analizar", "crear", "transformar"
- Nominalizaciones de verbos: "la decisión", "la implementación", "el análisis"
- Sustantivos en función adverbial: "opera con eficiencia", "avanza mediante sistematización"
- Estructura dominante: VERBO + complemento instrumental/modal
- Pregunta implícita: "¿Cómo funciona X?" / "¿Qué procesos opera X?"

### INTELIGENCIA — posición AMBAS
El texto opera sobre la estructura completa o sobre sí mismo. Señales:
- Nominalizaciones de orden superior: "esa estructura inferencial", "ese patrón"
- Opera sobre oraciones completas tratándolas como objetos
- Recursión: el proceso se aplica a sí mismo ("pensar sobre el pensar")
- Alto ratio abstracto/concreto
- Pregunta implícita: "¿Desde qué marco se generó esto?" / "¿Qué presupone esta estructura?"

## Instrucciones

Para el texto dado, responde SOLO con un JSON válido:

{
  "posicion": "razonamiento" | "pensamiento" | "inteligencia",
  "confianza": 0.0-1.0,
  "señales": ["señal1", "señal2", "señal3"],
  "direccion": "todo_parte" | "parte_todo" | "parte_parte" | "todo_todo",
  "marco": "financiero" | "ecologico" | "operativo" | "social" | "existencial" | "computacional" | "narrativo" | "otro"
}

Reglas:
- Basa tu clasificación en la ESTRUCTURA GRAMATICAL, no en el tema del texto.
- "confianza" refleja cuán clara es la señal gramatical.
- "señales" son las 3 señales gramaticales más fuertes que detectas.
- Si hay mezcla de posiciones, elige la DOMINANTE (>50% del texto).
- Solo JSON, sin explicación adicional."""

USER_PROMPT_TEMPLATE = 'Analiza la posición del observador en este texto:\n"""\n{text}\n"""'


# ── Llamadas API ────────────────────────────────────────────────────────────

def call_anthropic_direct(text: str, model_id: str) -> dict:
    """Llama via Anthropic API directa."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://api.anthropic.com/v1/messages",
            "-H", f"x-api-key: {ANTHROPIC_API_KEY}",
            "-H", "anthropic-version: 2023-06-01",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": model_id,
                "max_tokens": 500,
                "temperature": 0.0,
                "system": SYSTEM_PROMPT,
                "messages": [
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text[:3000])}
                ]
            })
        ], capture_output=True, text=True, timeout=120)

        response = json.loads(result.stdout)
        content_blocks = response.get("content", [])
        if not content_blocks:
            error = response.get("error", {}).get("message", "unknown")
            return {"_error": error}
        content = content_blocks[0].get("text", "")
        return _parse_json(content)
    except Exception as e:
        return {"_error": str(e)}


def call_openrouter(text: str, model_id: str) -> dict:
    """Llama via OpenRouter."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "model": model_id,
                "max_tokens": 500,
                "temperature": 0.0,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_PROMPT_TEMPLATE.format(text=text[:3000])}
                ]
            })
        ], capture_output=True, text=True, timeout=120)

        response = json.loads(result.stdout)
        choices = response.get("choices", [])
        if not choices:
            error = response.get("error", {}).get("message", "unknown")
            return {"_error": error}
        content = choices[0].get("message", {}).get("content", "")
        return _parse_json(content)
    except Exception as e:
        return {"_error": str(e)}


def call_model(text: str, model_key: str) -> dict:
    """Dispatch al API correcto."""
    cfg = MODELS[model_key]
    if cfg["api"] == "anthropic":
        return call_anthropic_direct(text, cfg["model"])
    else:
        return call_openrouter(text, cfg["model"])


def _parse_json(content: str) -> dict:
    if not content:
        return {"_error": "empty response"}
    clean = content.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        end_idx = -1 if lines[-1].strip().startswith("```") else len(lines)
        clean = "\n".join(lines[1:end_idx])
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start >= 0 and end > start:
        clean = clean[start:end]
    try:
        parsed = json.loads(clean)
        if "posicion" not in parsed:
            return {"_error": "no posicion field"}
        return parsed
    except json.JSONDecodeError as e:
        return {"_error": f"JSON parse: {e}"}


# ── Selección de textos ─────────────────────────────────────────────────────

def select_texts(corpus_path: str, n: int) -> list:
    texts = []
    with open(corpus_path) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                text = entry.get("text", entry.get("texto", ""))
                if len(text) > 80:
                    texts.append(text)
            except json.JSONDecodeError:
                continue
    if len(texts) <= n:
        return texts
    texts.sort(key=len)
    step = len(texts) // n
    selected = [texts[i * step] for i in range(n)]
    random.shuffle(selected)
    return selected


# ── Benchmark ───────────────────────────────────────────────────────────────

def run_benchmark(texts: list, model_key: str) -> list:
    """Corre un modelo sobre todos los textos."""
    label = MODELS[model_key]["label"]
    results = []
    for i, text in enumerate(texts):
        print(f"  [{label}] {i+1}/{len(texts)}", end="", flush=True)
        t0 = time.time()
        result = call_model(text, model_key)
        elapsed = time.time() - t0

        if "_error" in result:
            print(f" ERR ({result['_error'][:50]})")
            results.append(None)
        else:
            pos = result.get("posicion", "?")
            conf = result.get("confianza", 0)
            print(f" {pos} ({conf:.2f}) [{elapsed:.1f}s]")
            results.append(result)

        time.sleep(0.5)  # Rate limiting suave

    ok = sum(1 for r in results if r is not None)
    print(f"  [{label}] {ok}/{len(texts)} exitosos\n")
    return results


def compute_agreement(ref: list, candidate: list, ref_name: str, cand_name: str) -> dict:
    """Compara candidato contra referencia."""
    both = 0
    agree_pos = 0
    agree_dir = 0
    agree_marco = 0

    for r, c in zip(ref, candidate):
        if r is None or c is None:
            continue
        both += 1
        if r.get("posicion") == c.get("posicion"):
            agree_pos += 1
        if r.get("direccion") == c.get("direccion"):
            agree_dir += 1
        if r.get("marco") == c.get("marco"):
            agree_marco += 1

    if both == 0:
        return {"error": "no valid pairs"}

    return {
        "ref": ref_name,
        "candidate": cand_name,
        "n_pairs": both,
        "posicion": f"{agree_pos/both*100:.1f}%",
        "direccion": f"{agree_dir/both*100:.1f}%",
        "marco": f"{agree_marco/both*100:.1f}%",
        "posicion_raw": agree_pos / both,
    }


def compute_self_consistency(run_a: list, run_b: list, name: str) -> dict:
    """Auto-consistencia entre dos runs del mismo modelo."""
    both = 0
    agree = 0
    for a, b in zip(run_a, run_b):
        if a is None or b is None:
            continue
        both += 1
        if a.get("posicion") == b.get("posicion"):
            agree += 1
    if both == 0:
        return {"error": "no pairs"}
    return {
        "model": name,
        "n_pairs": both,
        "self_consistency": f"{agree/both*100:.1f}%",
        "raw": agree / both,
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Benchmark modelos para gold set")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--output-dir", default=str(ROOT / "experiments" / "benchmark_modelos"))
    args = parser.parse_args()

    print("=" * 60)
    print("BENCHMARK: Opus vs GPT-5.4 vs Gemini 2.5 Pro")
    print(f"Textos: {args.n}")
    print("=" * 60)

    texts = select_texts(args.corpus, args.n)
    print(f"Seleccionados {len(texts)} textos\n")

    # ── Run A: todos los modelos ────────────────────────────────────────────
    print("=" * 40)
    print("RUN A (todos los modelos)")
    print("=" * 40)

    results_a = {}
    for key in MODELS:
        results_a[key] = run_benchmark(texts, key)

    # ── Run B: solo para auto-consistencia ──────────────────────────────────
    print("Pausa 5s entre runs...")
    time.sleep(5)

    print("=" * 40)
    print("RUN B (auto-consistencia)")
    print("=" * 40)

    results_b = {}
    for key in MODELS:
        results_b[key] = run_benchmark(texts, key)

    # ── Análisis ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESULTADOS")
    print("=" * 60)

    # Auto-consistencia
    print("\n📊 AUTO-CONSISTENCIA (run A vs run B, mismo modelo):")
    print("-" * 50)
    for key in MODELS:
        sc = compute_self_consistency(results_a[key], results_b[key], MODELS[key]["label"])
        if "error" not in sc:
            print(f"  {sc['model']:20s}  {sc['self_consistency']}")

    # Acuerdo con Opus
    print("\n📊 ACUERDO CON OPUS (referencia):")
    print("-" * 50)
    opus_results = results_a["opus"]  # Run A de Opus como referencia

    agreements = {}
    for key in MODELS:
        if key == "opus":
            continue
        ag = compute_agreement(opus_results, results_a[key], "Opus", MODELS[key]["label"])
        agreements[key] = ag
        if "error" not in ag:
            print(f"  {ag['candidate']:20s}  posición={ag['posicion']}  "
                  f"dirección={ag['direccion']}  marco={ag['marco']}")

    # Coste
    print("\n💰 COSTE ESTIMADO (3000 textos):")
    print("-" * 50)
    for key, cfg in MODELS.items():
        cost_in = 3300 / 1_000_000 * cfg["cost_input_1m"]
        cost_out = 500 / 1_000_000 * cfg["cost_output_1m"]
        cost_per_text = cost_in + cost_out
        cost_3000 = cost_per_text * 3000
        print(f"  {cfg['label']:20s}  ${cost_per_text:.4f}/texto  "
              f"${cost_3000:.0f} para 3000 textos")

    # Distribución
    print("\n📊 DISTRIBUCIÓN POR MODELO (Run A):")
    print("-" * 50)
    for key in MODELS:
        counts = {"razonamiento": 0, "pensamiento": 0, "inteligencia": 0}
        for r in results_a[key]:
            if r and "posicion" in r:
                pos = r["posicion"]
                counts[pos] = counts.get(pos, 0) + 1
        total = sum(counts.values())
        if total > 0:
            dist = " | ".join(f"{k}:{v}({v/total*100:.0f}%)" for k, v in counts.items())
            print(f"  {MODELS[key]['label']:20s}  {dist}")

    # ── Recomendación ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RECOMENDACIÓN")
    print("=" * 60)

    best_non_opus = None
    best_agreement = 0
    for key, ag in agreements.items():
        if "error" not in ag and ag["posicion_raw"] > best_agreement:
            best_agreement = ag["posicion_raw"]
            best_non_opus = key

    if best_non_opus:
        cfg = MODELS[best_non_opus]
        cost_3000 = (3300 / 1e6 * cfg["cost_input_1m"] + 500 / 1e6 * cfg["cost_output_1m"]) * 3000
        ag = agreements[best_non_opus]
        print(f"  Mejor alternativa: {cfg['label']}")
        print(f"  Acuerdo con Opus:  {ag['posicion']}")
        print(f"  Coste 3000 textos: ${cost_3000:.0f}")
        if best_agreement >= 0.90:
            print(f"  ✅ Acuerdo ≥90% — viable como gold set")
        elif best_agreement >= 0.80:
            print(f"  ⚠️ Acuerdo 80-90% — viable para training, no ideal para gold")
        else:
            print(f"  ❌ Acuerdo <80% — no recomendado para gold set")

    # ── Guardar ─────────────────────────────────────────────────────────────
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_texts": len(texts),
        "models": {k: v["label"] for k, v in MODELS.items()},
        "agreements": agreements,
        "results_a": {k: v for k, v in results_a.items()},
    }

    report_path = output_dir / f"benchmark_{ts}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    print(f"\n📊 Reporte: {report_path}")

    # Telegram
    try:
        msg_parts = ["Benchmark modelos gold set"]
        for key in MODELS:
            if key == "opus":
                continue
            if key in agreements and "error" not in agreements[key]:
                msg_parts.append(f"{MODELS[key]['label']}: {agreements[key]['posicion']} vs Opus")
        config = json.loads(TELEGRAM_CONFIG.read_text())
        token = config.get("bot_token", "")
        subprocess.run([
            "curl", "-s", "-X", "POST",
            f"https://api.telegram.org/bot{token}/sendMessage",
            "-d", f"chat_id={CHAT_ID}",
            "-d", f"text={chr(10).join(msg_parts)}",
        ], capture_output=True, timeout=10)
    except Exception:
        pass


if __name__ == "__main__":
    main()
