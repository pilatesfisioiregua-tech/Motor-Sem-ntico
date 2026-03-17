"""Exp 2: Enjambre de Evaluadores OS — Runner.
Ejecuta N modelos OS como evaluadores de 5 outputs de análisis contra la Matriz 3L×7F.
"""
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
import requests as _requests

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "evaluator_test_set"
RESULTS_DIR = BASE_DIR / "results"
OUTPUT_FILE = RESULTS_DIR / "exp2_all_evaluator_results.json"

# ── Providers ────────────────────────────────────────────────────

PROVIDERS = {
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "api_key": os.getenv("TOGETHER_API_KEY"),
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "api_key": os.getenv("DEEPSEEK_API_KEY"),
    },
}

# ── Models ───────────────────────────────────────────────────────

MODELS = {
    "v3.2-chat":      {"id": "deepseek-chat",                                   "provider": "deepseek", "timeout": 90},
    "gpt-oss-120b":   {"id": "openai/gpt-oss-120b",                             "provider": "together", "timeout": 180},
    "kimi-k2.5":      {"id": "moonshotai/Kimi-K2.5",                            "provider": "together", "timeout": 180},
    "glm-4.7":        {"id": "zai-org/GLM-4.7",                                 "provider": "together", "timeout": 180},
    "qwen3-235b":     {"id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",         "provider": "together", "timeout": 180},
    "minimax-m1":     {"id": "MiniMaxAI/MiniMax-M1-40k",                        "provider": "together", "timeout": 180},
    "minimax-m2.5":   {"id": "MiniMaxAI/MiniMax-M2.5",                          "provider": "together", "timeout": 180},
    "deepseek-v3.1":  {"id": "deepseek-ai/DeepSeek-V3.1",                       "provider": "together", "timeout": 180},
    "cogito-671b":    {"id": "deepcogito/cogito-v2-preview-deepseek-671b",       "provider": "together", "timeout": 180},
    "deepseek-r1":    {"id": "deepseek-ai/DeepSeek-R1",                         "provider": "together", "timeout": 300},
    "v3.2-reasoner":  {"id": "deepseek-reasoner",                               "provider": "deepseek", "timeout": 240},
}

# Execution order (cheapest/fastest first)
EXEC_ORDER = list(MODELS.keys())

# ── System Prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """Eres un evaluador de profundidad analítica. Mapea un output a la Matriz 3L×7F (21 celdas) con nivel 0-4.

3 LENTES: Salud (funciona/recursos/estructura), Sentido (dirección/propósito/identidad), Continuidad (sobrevive/legado/replicabilidad).
7 FUNCIONES: Conservar (mantener), Captar (incorporar), Depurar (eliminar sobra), Distribuir (repartir), Frontera (límites), Adaptar (cambio), Replicar (copiar patrón).

NIVELES: 0=no toca, 1=mención genérica, 2=dato/inferencia específica del caso, 3=revela algo no obvio (contradicción/patrón invisible), 4=redefine la pregunta.

REGLAS: Evalúa SOLO lo que dice el output. Evidencia = cita corta. Celda ausente = nivel 0. Sé estricto: 3 requiere genuina no-obviedad, 4 genuina redefinición. No infles.

Responde EXCLUSIVAMENTE con JSON válido. Sin texto ni markdown.
{"celdas":{"Salud×Conservar":{"nivel":N,"evidencia":"..."},"Salud×Captar":{"nivel":N,"evidencia":"..."},"Salud×Depurar":{"nivel":N,"evidencia":"..."},"Salud×Distribuir":{"nivel":N,"evidencia":"..."},"Salud×Frontera":{"nivel":N,"evidencia":"..."},"Salud×Adaptar":{"nivel":N,"evidencia":"..."},"Salud×Replicar":{"nivel":N,"evidencia":"..."},"Sentido×Conservar":{"nivel":N,"evidencia":"..."},"Sentido×Captar":{"nivel":N,"evidencia":"..."},"Sentido×Depurar":{"nivel":N,"evidencia":"..."},"Sentido×Distribuir":{"nivel":N,"evidencia":"..."},"Sentido×Frontera":{"nivel":N,"evidencia":"..."},"Sentido×Adaptar":{"nivel":N,"evidencia":"..."},"Sentido×Replicar":{"nivel":N,"evidencia":"..."},"Continuidad×Conservar":{"nivel":N,"evidencia":"..."},"Continuidad×Captar":{"nivel":N,"evidencia":"..."},"Continuidad×Depurar":{"nivel":N,"evidencia":"..."},"Continuidad×Distribuir":{"nivel":N,"evidencia":"..."},"Continuidad×Frontera":{"nivel":N,"evidencia":"..."},"Continuidad×Adaptar":{"nivel":N,"evidencia":"..."},"Continuidad×Replicar":{"nivel":N,"evidencia":"..."}}}"""


def build_user_prompt(item: dict) -> str:
    return f"""CASO: {item['case_nombre']}
INTELIGENCIA APLICADA: {item['int_id']} — {item['int_nombre']}
MODELO QUE GENERÓ EL OUTPUT: {item['model_key']}

OUTPUT A EVALUAR:
---
{item['output']}
---

Evalúa este output mapeando cada hallazgo a la Matriz 3L×7F. Asigna nivel de profundidad (0-4) y evidencia por celda. JSON puro."""


# ── JSON Extraction ──────────────────────────────────────────────

def extract_json(text: str):
    """Robustly extract JSON from model response text."""
    if not text or not text.strip():
        return None

    # Strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    # Try direct parse
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find JSON object
    start = text.find("{")
    if start < 0:
        return None
    # Find matching closing brace
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


# ── API Call ─────────────────────────────────────────────────────

def call_together(model_cfg, user_prompt):
    """Call Together API via requests (reliable timeout). Returns (content_text, elapsed)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    timeout = model_cfg.get("timeout", 120)

    t0 = time.time()
    resp = _requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {PROVIDERS['together']['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_cfg["id"],
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)

    if resp.status_code != 200:
        raise RuntimeError(f"Together {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_deepseek(model_cfg, user_prompt):
    """Call DeepSeek API via requests. Returns (content_text, elapsed)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    body = {
        "model": model_cfg["id"],
        "messages": messages,
        "max_tokens": 4096,
    }
    # deepseek-reasoner doesn't support temperature
    if model_cfg["id"] != "deepseek-reasoner":
        body["temperature"] = 0.0

    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": f"Bearer {PROVIDERS['deepseek']['api_key']}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)

    if resp.status_code != 200:
        raise RuntimeError(f"DeepSeek {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_evaluator(model_cfg, user_prompt):
    """Dispatch to provider. Returns (content_text, elapsed)."""
    if model_cfg["provider"] == "together":
        return call_together(model_cfg, user_prompt)
    elif model_cfg["provider"] == "deepseek":
        return call_deepseek(model_cfg, user_prompt)
    else:
        raise ValueError(f"Unknown provider: {model_cfg['provider']}")


# ── Main ─────────────────────────────────────────────────────────

def load_existing() -> dict:
    """Load existing results for incremental execution."""
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {
        "meta": {
            "experiment": "Exp 2 - Enjambre Evaluadores OS",
            "date": str(date.today()),
            "n_outputs": 5,
            "n_datapoints_per_model": 105,
            "sonnet_reference": "sonnet_reference_evals.json",
        },
        "models_tested": [],
        "models_failed": [],
        "results": {},
    }


def save_results(results: dict):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def main():
    # Load test outputs
    with open(DATA_DIR / "test_outputs.json", encoding="utf-8") as f:
        test_outputs = json.load(f)

    print(f"Test outputs: {len(test_outputs)}")
    for item in test_outputs:
        print(f"  {item['id']}: {item['model_key']} / {item['case_id']} / {item['int_id']} ({item['output_length']} chars)")

    # Check API keys
    for prov_name, prov_cfg in PROVIDERS.items():
        if not prov_cfg["api_key"]:
            print(f"WARNING: No API key for {prov_name}")

    # Load existing results
    all_results = load_existing()
    total_evals = 0
    total_ok = 0
    total_fail = 0

    for model_name in EXEC_ORDER:
        model_cfg = MODELS[model_name]
        provider = model_cfg["provider"]

        if not PROVIDERS.get(provider, {}).get("api_key"):
            msg = f"{model_name}: no API key for {provider}"
            print(f"SKIP {msg}")
            if msg not in all_results["models_failed"]:
                all_results["models_failed"].append(msg)
            continue

        # Skip if already fully completed
        if model_name in all_results["results"]:
            existing_count = len(all_results["results"][model_name])
            if existing_count >= len(test_outputs):
                print(f"\n[{model_name}] Already complete ({existing_count}/{len(test_outputs)}). Skipping.")
                continue

        print(f"\n{'='*60}")
        print(f"MODEL: {model_name} ({model_cfg['id']}) via {provider}")
        print(f"{'='*60}")

        model_results = all_results["results"].get(model_name, {})
        model_ok = 0
        model_fail = 0

        for item in test_outputs:
            output_id = item["id"]

            # Skip if already evaluated
            if output_id in model_results and "error" not in model_results[output_id]:
                print(f"  [{output_id}] cached. Skipping.")
                model_ok += 1
                continue

            user_prompt = build_user_prompt(item)
            print(f"  [{output_id}] {item['case_nombre']} × {item['int_nombre']}...", end=" ", flush=True)

            parsed = None
            elapsed = 0
            error = None

            for attempt in range(2):
                try:
                    retry_prompt = user_prompt
                    if attempt == 1:
                        retry_prompt += "\n\nIMPORTANTE: Responde SOLO con JSON válido. Sin texto adicional."

                    content_text, elapsed = call_evaluator(model_cfg, retry_prompt)

                    # Strip think tags if present
                    if "</think>" in content_text:
                        content_text = content_text.split("</think>")[-1]

                    parsed = extract_json(content_text)

                    if parsed and "celdas" in parsed:
                        break
                    elif parsed:
                        # Got JSON but missing 'celdas' key — might be flat
                        sample_key = next(iter(parsed.keys()), "")
                        if "×" in sample_key:
                            parsed = {"celdas": parsed}
                            break
                    # else retry
                    if attempt == 0:
                        print("(retry)", end=" ", flush=True)
                        time.sleep(2)

                except Exception as e:
                    error = str(e)
                    if attempt == 0 and ("rate" in error.lower() or "429" in error):
                        print(f"(rate limit, wait 30s)", end=" ", flush=True)
                        time.sleep(30)
                    elif attempt == 0:
                        print(f"(error, retry)", end=" ", flush=True)
                        time.sleep(5)

            if parsed and "celdas" in parsed:
                model_results[output_id] = {
                    "celdas": parsed["celdas"],
                    "tiempo_s": elapsed,
                }
                n_celdas = len(parsed["celdas"])
                niveles = [c.get("nivel", 0) for c in parsed["celdas"].values()]
                medio = sum(niveles) / max(len(niveles), 1)
                print(f"OK ({elapsed}s, {n_celdas} celdas, medio={medio:.2f})")
                model_ok += 1
            else:
                err_msg = error or "JSON parse failed"
                model_results[output_id] = {"error": err_msg, "tiempo_s": elapsed}
                print(f"FAIL ({elapsed}s: {err_msg[:80]})")
                model_fail += 1

            total_evals += 1
            time.sleep(2)  # Rate limit

        all_results["results"][model_name] = model_results
        total_ok += model_ok
        total_fail += model_fail

        if model_name not in all_results["models_tested"]:
            all_results["models_tested"].append(model_name)

        if model_fail > 0:
            fail_msg = f"{model_name}: {model_fail}/{len(test_outputs)} failed"
            if fail_msg not in all_results["models_failed"]:
                all_results["models_failed"].append(fail_msg)

        # Save incrementally
        save_results(all_results)
        print(f"  Summary: {model_ok} OK, {model_fail} FAIL")

    # Final save
    save_results(all_results)

    print(f"\n{'='*60}")
    print(f"DONE: {total_ok} OK, {total_fail} FAIL across {len(all_results['models_tested'])} models")
    print(f"Results: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
