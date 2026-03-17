"""Exp 4.2: El Sintetizador — Runner.
6 candidate models synthesize 13 perspectives into a coherent final output.
Tests which model best integrates multiple evaluator perspectives.
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
SYNTH_FILE = RESULTS_DIR / "exp4_2_sintesis.json"
EXP4_R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
EXP4_R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
TEST_OUTPUTS_FILE = DATA_DIR / "test_outputs.json"

PROVIDERS = {
    "together":  {"api_key": os.getenv("TOGETHER_API_KEY")},
    "deepseek":  {"api_key": os.getenv("DEEPSEEK_API_KEY")},
    "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
}

# ── 6 Synthesizer candidates ────────────────────────────────────
SYNTHESIZERS = {
    "cogito-671b":   {"id": "deepcogito/cogito-v2-1-671b",               "provider": "together",  "timeout": 240},
    "deepseek-r1":   {"id": "deepseek-ai/DeepSeek-R1",                   "provider": "together",  "timeout": 300},
    "v3.2-chat":     {"id": "deepseek-chat",                             "provider": "deepseek",  "timeout": 180},
    "glm-5":         {"id": "zai-org/GLM-5",                             "provider": "together",  "timeout": 240},
    "minimax-m2.5":  {"id": "MiniMaxAI/MiniMax-M2.5",                    "provider": "together",  "timeout": 240},
    "qwen3-235b":    {"id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",   "provider": "together",  "timeout": 240},
}

ALL_13 = [
    "opus", "sonnet", "v3.2-chat", "v3.2-reasoner", "deepseek-r1",
    "deepseek-v3.1", "cogito-671b", "gpt-oss-120b", "qwen3-235b",
    "minimax-m2.5", "kimi-k2.5", "glm-4.7",
]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

# ── Synthesis System Prompt ──────────────────────────────────────
SYSTEM_SYNTH = (
    "Eres el sintetizador de una mesa redonda de 13 evaluadores expertos. Cada uno ha analizado el mismo output desde su angulo. Tu trabajo es INTEGRAR sus 13 perspectivas en una evaluacion final coherente.\n\n"
    "NO eres un evaluador mas. No anades tu opinion. Tu trabajo es:\n"
    "1. INTEGRAR: Combina las evidencias de los 13 evaluadores por celda. Si 3 evaluadores vieron cosas diferentes en la misma celda, tu evidencia incluye las 3.\n"
    "2. CONECTAR: Identifica relaciones entre celdas que ningun evaluador individual nombro. Si Cogito vio X en Sentido\u00d7Frontera y R1 vio Y en Continuidad\u00d7Replicar, hay una conexion?\n"
    "3. SINTETIZAR: Produce el hallazgo central — la frase que captura lo que la mesa vio colectivamente que ningun evaluador vio solo.\n"
    "4. SENALAR VACIOS: Que NO cubrio la mesa, incluso con 13 voces? Hay celdas que todos ignoraron?\n\n"
    "REGLAS:\n"
    "- El score de cada celda es el MAX de los 13 evaluadores. No lo bajes.\n"
    "- La evidencia es la UNION de las evidencias de todos los evaluadores que aportaron a esa celda. Sintetizalas, no las concatenes.\n"
    "- Las conexiones entre celdas son TU aporte principal. Los evaluadores miran celda por celda. Tu miras el MAPA COMPLETO.\n"
    "- No inventes evidencia que no este en ninguna evaluacion. Solo integras y conectas.\n\n"
    "Responde con JSON:\n"
    '{"evaluacion_integrada":{"celdas":{"Salud\u00d7Conservar":{"nivel":N,"evidencia_integrada":"Sintesis de evidencias","evaluadores_que_aportaron":["m1","m2"]},...21 celdas}},'
    '"conexiones_entre_celdas":[{"celda_a":"X\u00d7Y","celda_b":"W\u00d7Z","conexion":"...","evaluadores_origen":["a","b"]}],'
    '"hallazgo_central":"La frase que captura lo que la mesa vio colectivamente",'
    '"puntos_ciegos_residuales":[{"celda":"X\u00d7Y","que_falta":"Ningun evaluador cubrio..."}],'
    '"meta_patrones":["Patron 1 que cruza multiples celdas...","Patron 2..."]}'
)


# ── JSON Extraction ──────────────────────────────────────────────
def extract_json(text):
    if not text or not text.strip():
        return None
    if "</think>" in text:
        text = text.split("</think>")[-1]
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start < 0:
        return None
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


# ── API Calls ────────────────────────────────────────────────────
def call_together(model_cfg, system_prompt, user_prompt):
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": "Bearer " + PROVIDERS["together"]["api_key"],
            "Content-Type": "application/json",
        },
        json={
            "model": model_cfg["id"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 8192,
        },
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError("Together %d: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_deepseek(model_cfg, system_prompt, user_prompt):
    body = {
        "model": model_cfg["id"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 8192,
    }
    if model_cfg["id"] != "deepseek-reasoner":
        body["temperature"] = 0.0
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.deepseek.com/chat/completions",
        headers={
            "Authorization": "Bearer " + PROVIDERS["deepseek"]["api_key"],
            "Content-Type": "application/json",
        },
        json=body,
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError("DeepSeek %d: %s" % (resp.status_code, resp.text[:300]))
    data = resp.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    return content, elapsed


def call_model(model_name, model_cfg, system_prompt, user_prompt):
    provider = model_cfg["provider"]
    if provider == "together":
        return call_together(model_cfg, system_prompt, user_prompt)
    elif provider == "deepseek":
        return call_deepseek(model_cfg, system_prompt, user_prompt)
    raise ValueError("Unknown provider: " + provider)


# ── Load Data ────────────────────────────────────────────────────
def load_test_outputs():
    with open(TEST_OUTPUTS_FILE, encoding="utf-8") as f:
        items = json.load(f)
    return {item["id"]: item for item in items}


def load_all_evaluations():
    """Load best available evaluations (R2 if exists, else R1) for all 13 models."""
    with open(EXP4_R1_FILE, encoding="utf-8") as f:
        r1_data = json.load(f).get("evaluaciones", {})

    r2_data = {}
    if EXP4_R2_FILE.exists():
        with open(EXP4_R2_FILE, encoding="utf-8") as f:
            r2_data = json.load(f).get("evaluaciones", {})

    # For each model×output: use R2 if available, else R1
    best_evals = {}
    for model_name in ALL_13:
        best_evals[model_name] = {}
        for oid in OUTPUT_IDS:
            # Try R2 first
            r2_entry = r2_data.get(model_name, {}).get(oid, {})
            if r2_entry and "error" not in r2_entry:
                celdas = r2_entry.get("evaluacion_enriquecida", {}).get("celdas", {})
                if celdas:
                    best_evals[model_name][oid] = celdas
                    continue
            # Fall back to R1
            r1_entry = r1_data.get(model_name, {}).get(oid, {})
            if r1_entry:
                celdas = r1_entry.get("celdas", {})
                if celdas:
                    best_evals[model_name][oid] = celdas
    return best_evals


# ── Build Synthesis Prompt ───────────────────────────────────────
def build_synth_prompt(item, all_evals, oid):
    """Build user prompt with output + 13 evaluations."""
    parts = [
        "OUTPUT ORIGINAL:",
        "---",
        item["output"],
        "---\n",
        "CASO: %s" % item["case_nombre"],
        "INTELIGENCIA: %s — %s\n" % (item["int_id"], item["int_nombre"]),
        "EVALUACIONES DE LOS 13 EVALUADORES:\n",
    ]
    n_evals = 0
    for model_name in ALL_13:
        celdas = all_evals.get(model_name, {}).get(oid, {})
        if celdas:
            parts.append("Evaluador: %s" % model_name)
            parts.append(json.dumps(celdas, ensure_ascii=False))
            parts.append("")
            n_evals += 1
    parts.append(
        "Sintetiza las %d perspectivas. Integra evidencias, conecta celdas, "
        "identifica el hallazgo central y los puntos ciegos residuales. JSON puro." % n_evals
    )
    return "\n".join(parts), n_evals


# ── Run Synthesis ────────────────────────────────────────────────
def run_synthesis():
    """Run 6 synthesizers × 5 outputs."""
    if SYNTH_FILE.exists():
        with open(SYNTH_FILE, encoding="utf-8") as f:
            results = json.load(f).get("sintesis", {})
    else:
        results = {}

    test_outputs = load_test_outputs()
    all_evals = load_all_evaluations()

    # Filter by --model if provided
    model_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model_filter = arg.split("=", 1)[1]

    synth_list = list(SYNTHESIZERS.keys())
    if model_filter:
        synth_list = [m for m in synth_list if m == model_filter]

    print("=== EXP 4.2: EL SINTETIZADOR ===")
    print("%d sintetizadores x %d outputs = %d calls\n" % (
        len(synth_list), len(OUTPUT_IDS), len(synth_list) * len(OUTPUT_IDS)
    ))

    for synth_name in synth_list:
        synth_cfg = SYNTHESIZERS[synth_name]
        provider = synth_cfg["provider"]
        if not PROVIDERS.get(provider, {}).get("api_key"):
            print("  %s: no API key for %s, skipping" % (synth_name, provider))
            continue
        if synth_name not in results:
            results[synth_name] = {}

        for oid in OUTPUT_IDS:
            # Skip if already done
            if oid in results[synth_name] and "error" not in results[synth_name][oid]:
                print("  [%s] %s: cached" % (synth_name, oid))
                continue

            item = test_outputs[oid]
            user_prompt, n_evals = build_synth_prompt(item, all_evals, oid)
            print("  [%s] %s (%d evals)..." % (synth_name, oid, n_evals), end=" ", flush=True)

            result = None
            for attempt in range(2):
                try:
                    prompt = user_prompt
                    if attempt == 1:
                        prompt += (
                            "\n\nIMPORTANTE: Responde con JSON completo incluyendo "
                            "evaluacion_integrada, conexiones_entre_celdas, hallazgo_central, "
                            "puntos_ciegos_residuales, y meta_patrones."
                        )
                    content, elapsed = call_model(synth_name, synth_cfg, SYSTEM_SYNTH, prompt)
                    parsed = extract_json(content)
                    if parsed:
                        # Validate required fields
                        has_eval = "evaluacion_integrada" in parsed or "celdas" in parsed
                        if has_eval:
                            parsed["tiempo_s"] = elapsed
                            result = parsed
                            break
                    if attempt == 0:
                        print("(retry)", end=" ", flush=True)
                        time.sleep(3)
                except Exception as e:
                    err = str(e)
                    if attempt == 0:
                        wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                        print("(err, wait %ds)" % wait, end=" ", flush=True)
                        time.sleep(wait)

            if result:
                results[synth_name][oid] = result
                # Count metrics
                n_conn = len(result.get("conexiones_entre_celdas", []))
                hallazgo = result.get("hallazgo_central", "")
                n_ciegos = len(result.get("puntos_ciegos_residuales", []))
                n_meta = len(result.get("meta_patrones", []))
                print("OK (%.1fs, %dconn, %dciegos, %dmeta)" % (elapsed, n_conn, n_ciegos, n_meta))
            else:
                results[synth_name][oid] = {"error": "synthesis parse failed"}
                print("FAIL")
            time.sleep(3)

        # Save after each synthesizer
        save_results(results)

    # Summary
    print("\n--- Summary ---")
    for s in synth_list:
        sm = results.get(s, {})
        ok = sum(1 for v in sm.values() if "error" not in v)
        print("  %s: %d/5 OK" % (s, ok))

    return results


def save_results(results):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4.2 - El Sintetizador",
            "date": str(date.today()),
            "n_synthesizers": len(results),
        },
        "sintesis": results,
    }
    with open(SYNTH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    for prov, cfg in PROVIDERS.items():
        s = "OK" if cfg.get("api_key") else "MISSING"
        print("  %s: %s" % (prov, s))

    run_synthesis()

    print("\nDONE")
    print("Results: %s" % SYNTH_FILE)


if __name__ == "__main__":
    main()
