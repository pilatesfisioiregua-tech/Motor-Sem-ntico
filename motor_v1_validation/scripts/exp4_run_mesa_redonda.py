"""Exp 4: Mesa Redonda — Runner.
13 modelos x 5 outputs. Ronda 1 (ciega) + Ronda 2 (enriquecimiento colectivo).
Reutiliza datos de Exp 2 donde disponibles.
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
R1_FILE = RESULTS_DIR / "exp4_ronda1_completa.json"
R2_FILE = RESULTS_DIR / "exp4_ronda2.json"
EXP2_FILE = RESULTS_DIR / "exp2_all_evaluator_results.json"
SONNET_REF_FILE = DATA_DIR / "sonnet_reference_evals.json"
TEST_OUTPUTS_FILE = DATA_DIR / "test_outputs.json"

# ── Providers ────────────────────────────────────────────────────

PROVIDERS = {
    "together":  {"api_key": os.getenv("TOGETHER_API_KEY")},
    "deepseek":  {"api_key": os.getenv("DEEPSEEK_API_KEY")},
    "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
}

# ── All 13 Models (sonnet is special: loaded from reference) ─────

ALL_MODELS = {
    "opus":           {"id": "claude-opus-4-20250514",                     "provider": "anthropic", "timeout": 180},
    "v3.2-chat":      {"id": "deepseek-chat",                             "provider": "deepseek",  "timeout": 90},
    "v3.2-reasoner":  {"id": "deepseek-reasoner",                         "provider": "deepseek",  "timeout": 300},
    "gpt-oss-120b":   {"id": "openai/gpt-oss-120b",                       "provider": "together",  "timeout": 180},
    "qwen3-235b":     {"id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",   "provider": "together",  "timeout": 180},
    "deepseek-v3.1":  {"id": "deepseek-ai/DeepSeek-V3.1",                 "provider": "together",  "timeout": 180},
    "deepseek-r1":    {"id": "deepseek-ai/DeepSeek-R1",                   "provider": "together",  "timeout": 300},
    "glm-4.7":        {"id": "zai-org/GLM-4.7",                           "provider": "together",  "timeout": 180},
    "minimax-m2.5":   {"id": "MiniMaxAI/MiniMax-M2.5",                    "provider": "together",  "timeout": 180},
    "kimi-k2.5":      {"id": "moonshotai/Kimi-K2.5",                      "provider": "together",  "timeout": 300},
    "cogito-671b":    {"id": "deepcogito/cogito-v2-1-671b",                "provider": "together",  "timeout": 180},
}

ALL_13 = [
    "opus", "sonnet", "v3.2-chat", "v3.2-reasoner", "deepseek-r1",
    "deepseek-v3.1", "cogito-671b", "gpt-oss-120b", "qwen3-235b",
    "minimax-m2.5", "kimi-k2.5", "glm-4.7",
]

OUTPUT_IDS = ["v31_best", "70b_worst", "maverick_medium", "gptoss_depurar", "qwen3t_medium"]

# ── System Prompts ───────────────────────────────────────────────

SYSTEM_R1 = (
    "Eres un evaluador de profundidad analitica. Mapea un output a la Matriz 3Lx7F (21 celdas) con nivel 0-4.\n\n"
    "3 LENTES: Salud (funciona/recursos/estructura), Sentido (direccion/proposito/identidad), Continuidad (sobrevive/legado/replicabilidad).\n"
    "7 FUNCIONES: Conservar (mantener), Captar (incorporar), Depurar (eliminar sobra), Distribuir (repartir), Frontera (limites), Adaptar (cambio), Replicar (copiar patron).\n\n"
    "NIVELES: 0=no toca, 1=mencion generica, 2=dato/inferencia especifica del caso, 3=revela algo no obvio (contradiccion/patron invisible), 4=redefine la pregunta.\n\n"
    "REGLAS: Evalua SOLO lo que dice el output. Evidencia = cita corta. Celda ausente = nivel 0. Se estricto: 3 requiere genuina no-obviedad, 4 genuina redefinicion. No infles.\n\n"
    "Responde EXCLUSIVAMENTE con JSON valido. Sin texto ni markdown.\n"
    '{"celdas":{"Salud\u00d7Conservar":{"nivel":N,"evidencia":"..."},"Salud\u00d7Captar":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Depurar":{"nivel":N,"evidencia":"..."},"Salud\u00d7Distribuir":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Frontera":{"nivel":N,"evidencia":"..."},"Salud\u00d7Adaptar":{"nivel":N,"evidencia":"..."},'
    '"Salud\u00d7Replicar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Conservar":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Captar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Depurar":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Distribuir":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Frontera":{"nivel":N,"evidencia":"..."},'
    '"Sentido\u00d7Adaptar":{"nivel":N,"evidencia":"..."},"Sentido\u00d7Replicar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Conservar":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Captar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Depurar":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Distribuir":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Frontera":{"nivel":N,"evidencia":"..."},"Continuidad\u00d7Adaptar":{"nivel":N,"evidencia":"..."},'
    '"Continuidad\u00d7Replicar":{"nivel":N,"evidencia":"..."}}}'
)

SYSTEM_R2 = (
    "Eres un evaluador experto en una mesa redonda de enriquecimiento colectivo. "
    "Ya evaluaste un output. Ahora ves las evaluaciones de tus colegas.\n\n"
    "Tu tarea es ENRIQUECER, no debatir:\n"
    "1. MIRA lo que vieron tus colegas que tu no viste\n"
    "2. INCORPORA lo valido — sube niveles donde encontraron evidencia que pasaste por alto\n"
    "3. APORTA lo que solo tu detectaste\n"
    "4. MANTEN tus scores validos aunque otros no los vean\n"
    "5. SENALA angulos genuinamente diferentes\n\n"
    "REGLAS:\n"
    "- NO bajes scores. Solo sube si descubres evidencia nueva en el output original.\n"
    "- Verifica contra el OUTPUT: si un colega vio algo, comprueba que realmente esta ahi.\n"
    "- Tu evaluacion enriquecida >= tu original en cada celda.\n\n"
    "JSON puro, sin texto ni markdown:\n"
    '{"evaluacion_enriquecida":{"celdas":{"Salud\u00d7Conservar":{"nivel":N,"evidencia":"..."},...21 celdas}},'
    '"incorporado_de_otros":[{"celda":"X\u00d7Y","antes":N,"despues":M,"de_quien":"modelo","que_vi_gracias_a_el":"..."}],'
    '"mi_aporte_unico":[{"celda":"X\u00d7Y","mi_score":N,"score_maximo_otros":M,"que_veo_que_nadie_ve":"..."}],'
    '"angulos_diferentes":[{"celda":"X\u00d7Y","mi_lectura":"...","lectura_otros":"...","por_que_ambas_son_validas":"..."}]}'
)


# ── Prompt Builders ──────────────────────────────────────────────

def build_r1_user_prompt(item):
    return (
        f"CASO: {item['case_nombre']}\n"
        f"INTELIGENCIA APLICADA: {item['int_id']} \u2014 {item['int_nombre']}\n"
        f"MODELO QUE GENERO EL OUTPUT: {item['model_key']}\n\n"
        f"OUTPUT A EVALUAR:\n---\n{item['output']}\n---\n\n"
        "Evalua este output mapeando cada hallazgo a la Matriz 3Lx7F. "
        "Asigna nivel de profundidad (0-4) y evidencia por celda. JSON puro."
    )


def build_r2_user_prompt(output_text, my_celdas, other_evals):
    """other_evals: list of (model_name, celdas_dict)"""
    parts = [
        "OUTPUT ORIGINAL A EVALUAR:\n---",
        output_text,
        "---\n",
        "TU EVALUACION (Ronda 1):",
        json.dumps(my_celdas, ensure_ascii=False),
        "\nEVALUACIONES DE TUS COLEGAS:\n",
    ]
    for name, celdas in other_evals:
        parts.append(f"Evaluador: {name}")
        parts.append(json.dumps(celdas, ensure_ascii=False))
        parts.append("")
    parts.append(
        "Enriquece tu evaluacion con lo que aportan tus colegas. "
        "Incorpora lo valido, senala lo que tu ves que nadie mas ve, "
        "y marca los angulos genuinamente diferentes. JSON puro."
    )
    return "\n".join(parts)


# ── JSON Extraction ──────────────────────────────────────────────

def extract_json(text):
    if not text or not text.strip():
        return None
    # Strip think tags
    if "</think>" in text:
        text = text.split("</think>")[-1]
    # Strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find JSON object
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
            "Authorization": f"Bearer {PROVIDERS['together']['api_key']}",
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
        raise RuntimeError(f"Together {resp.status_code}: {resp.text[:300]}")
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


def call_anthropic(model_cfg, system_prompt, user_prompt):
    timeout = model_cfg.get("timeout", 180)
    t0 = time.time()
    resp = _requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": PROVIDERS["anthropic"]["api_key"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model_cfg["id"],
            "max_tokens": 8192,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=timeout,
    )
    elapsed = round(time.time() - t0, 2)
    if resp.status_code != 200:
        raise RuntimeError(f"Anthropic {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    content = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            content += block.get("text", "")
    return content, elapsed


def call_model(model_name, model_cfg, system_prompt, user_prompt):
    provider = model_cfg["provider"]
    if provider == "together":
        return call_together(model_cfg, system_prompt, user_prompt)
    elif provider == "deepseek":
        return call_deepseek(model_cfg, system_prompt, user_prompt)
    elif provider == "anthropic":
        return call_anthropic(model_cfg, system_prompt, user_prompt)
    raise ValueError(f"Unknown provider: {provider}")


# ── Ronda 1 ──────────────────────────────────────────────────────

def load_test_outputs():
    with open(TEST_OUTPUTS_FILE, encoding="utf-8") as f:
        items = json.load(f)
    return {item["id"]: item for item in items}


def load_sonnet_reference():
    with open(SONNET_REF_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    normalized = {}
    for output_id, entry in raw.items():
        celdas = entry.get("result", {}).get("celdas", entry.get("celdas", {}))
        normalized[output_id] = {
            "celdas": celdas,
            "tiempo_s": entry.get("tiempo_s", 0),
        }
    return normalized


def load_exp2_results():
    if not EXP2_FILE.exists():
        return {}
    with open(EXP2_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    results = {}
    for model_name, model_data in raw.get("results", {}).items():
        model_results = {}
        for output_id, entry in model_data.items():
            if "error" not in entry and "celdas" in entry:
                model_results[output_id] = {
                    "celdas": entry["celdas"],
                    "tiempo_s": entry.get("tiempo_s", 0),
                }
        if model_results:
            results[model_name] = model_results
    return results


def eval_output_r1(model_name, model_cfg, item):
    """Evaluate one output. Returns {celdas, tiempo_s} or None."""
    user_prompt = build_r1_user_prompt(item)
    for attempt in range(2):
        try:
            prompt = user_prompt
            if attempt == 1:
                prompt += "\n\nIMPORTANTE: Responde SOLO con JSON valido. Sin texto adicional."
            content, elapsed = call_model(model_name, model_cfg, SYSTEM_R1, prompt)
            parsed = extract_json(content)
            if parsed and "celdas" in parsed:
                return {"celdas": parsed["celdas"], "tiempo_s": elapsed}
            if parsed:
                sample_key = next(iter(parsed.keys()), "")
                if "\u00d7" in sample_key:
                    return {"celdas": parsed, "tiempo_s": elapsed}
            if attempt == 0:
                print("(retry)", end=" ", flush=True)
                time.sleep(2)
        except Exception as e:
            err = str(e)
            if attempt == 0:
                wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                print(f"(err, wait {wait}s)", end=" ", flush=True)
                time.sleep(wait)
    return None


def save_r1(evaluaciones):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4 - Mesa Redonda",
            "date": str(date.today()),
            "ronda": 1,
            "n_models": len(evaluaciones),
        },
        "evaluaciones": evaluaciones,
    }
    with open(R1_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def consolidate_ronda1():
    """Merge Sonnet ref + Exp 2 data + run missing R1 evals."""
    # Load existing R1 if available
    if R1_FILE.exists():
        with open(R1_FILE, encoding="utf-8") as f:
            evaluaciones = json.load(f).get("evaluaciones", {})
    else:
        evaluaciones = {}

    test_outputs = load_test_outputs()

    # 1. Sonnet reference
    if "sonnet" not in evaluaciones or len(evaluaciones.get("sonnet", {})) < 5:
        sonnet = load_sonnet_reference()
        evaluaciones["sonnet"] = sonnet
        print(f"Sonnet: loaded {len(sonnet)}/5 from reference")
    else:
        print(f"Sonnet: already complete ({len(evaluaciones['sonnet'])}/5)")

    # 2. Exp 2 data
    exp2 = load_exp2_results()
    for model_name in exp2:
        if model_name not in evaluaciones:
            evaluaciones[model_name] = {}
        for oid, entry in exp2[model_name].items():
            if oid not in evaluaciones[model_name]:
                evaluaciones[model_name][oid] = entry

    # 3. Status check
    print("\n--- R1 Status ---")
    to_complete = []
    for model_name in ALL_13:
        n = len(evaluaciones.get(model_name, {}))
        missing = [oid for oid in OUTPUT_IDS if oid not in evaluaciones.get(model_name, {})]
        status = "OK" if n >= 5 else f"{n}/5"
        print(f"  {model_name}: {status}")
        if missing and model_name != "sonnet":
            to_complete.append((model_name, missing))

    # 4. Run missing R1
    total_calls = sum(len(m[1]) for m in to_complete)
    if total_calls == 0:
        print("\nR1 complete, no calls needed.")
        save_r1(evaluaciones)
        return evaluaciones

    # Filter by --model arg if provided
    model_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model_filter = arg.split("=", 1)[1]

    print(f"\n--- Completing R1 ({total_calls} calls) ---")
    for model_name, missing_oids in to_complete:
        if model_filter and model_name != model_filter:
            continue
        if model_name not in ALL_MODELS:
            print(f"  {model_name}: no model config, skipping")
            continue
        model_cfg = ALL_MODELS[model_name]
        provider = model_cfg["provider"]
        if not PROVIDERS.get(provider, {}).get("api_key"):
            print(f"  {model_name}: no API key for {provider}, skipping")
            continue
        if model_name not in evaluaciones:
            evaluaciones[model_name] = {}

        print(f"\n  [{model_name}] {len(missing_oids)} outputs pending")
        for oid in missing_oids:
            item = test_outputs[oid]
            print(f"    {oid}...", end=" ", flush=True)
            result = eval_output_r1(model_name, model_cfg, item)
            if result:
                evaluaciones[model_name][oid] = result
                niveles = [c.get("nivel", 0) for c in result["celdas"].values()]
                medio = sum(niveles) / max(len(niveles), 1)
                print(f"OK ({result['tiempo_s']}s, medio={medio:.2f})")
            else:
                print("FAIL")
            time.sleep(2)
        save_r1(evaluaciones)

    # Final status
    print("\n--- R1 Final ---")
    complete = 0
    for m in ALL_13:
        n = len(evaluaciones.get(m, {}))
        if n >= 5:
            complete += 1
        print(f"  {m}: {n}/5")
    print(f"  Total: {complete}/13 complete")
    save_r1(evaluaciones)
    return evaluaciones


# ── Ronda 2 ──────────────────────────────────────────────────────

def validate_r2(r2_parsed, r1_celdas):
    """Extract enriched celdas from R2, enforce no-decrease rule."""
    if not r2_parsed:
        return None
    # Find enriched celdas
    enriched = None
    if "evaluacion_enriquecida" in r2_parsed:
        enriched = r2_parsed["evaluacion_enriquecida"].get("celdas", {})
    elif "celdas" in r2_parsed:
        enriched = r2_parsed["celdas"]
    else:
        sample = next(iter(r2_parsed.keys()), "")
        if "\u00d7" in sample:
            enriched = r2_parsed
    if not enriched:
        return None
    # Enforce no-decrease
    for celda, r1_val in r1_celdas.items():
        r1_nivel = r1_val.get("nivel", 0) if isinstance(r1_val, dict) else 0
        if celda in enriched:
            r2_nivel = enriched[celda].get("nivel", 0) if isinstance(enriched[celda], dict) else 0
            if r2_nivel < r1_nivel:
                enriched[celda]["nivel"] = r1_nivel
        else:
            enriched[celda] = r1_val
    return {
        "evaluacion_enriquecida": {"celdas": enriched},
        "incorporado_de_otros": r2_parsed.get("incorporado_de_otros", []),
        "mi_aporte_unico": r2_parsed.get("mi_aporte_unico", []),
        "angulos_diferentes": r2_parsed.get("angulos_diferentes", []),
    }


def save_r2(r2_evals):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "meta": {
            "experiment": "Exp 4 - Mesa Redonda",
            "date": str(date.today()),
            "ronda": 2,
            "n_models": len(r2_evals),
        },
        "evaluaciones": r2_evals,
    }
    with open(R2_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def run_ronda2(evaluaciones):
    """Execute R2 for all models (except Sonnet) that have R1 data."""
    if R2_FILE.exists():
        with open(R2_FILE, encoding="utf-8") as f:
            r2_evals = json.load(f).get("evaluaciones", {})
    else:
        r2_evals = {}

    test_outputs = load_test_outputs()
    r2_models = [
        m for m in ALL_13
        if m != "sonnet" and m in evaluaciones and len(evaluaciones[m]) > 0
    ]

    # Filter by --model arg
    model_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--model="):
            model_filter = arg.split("=", 1)[1]
    if model_filter:
        r2_models = [m for m in r2_models if m == model_filter]

    print(f"\n{'='*60}")
    print(f"RONDA 2: {len(r2_models)} modelos")
    print(f"{'='*60}")

    for model_name in r2_models:
        if model_name not in ALL_MODELS:
            continue
        model_cfg = ALL_MODELS[model_name]
        provider = model_cfg["provider"]
        if not PROVIDERS.get(provider, {}).get("api_key"):
            print(f"  {model_name}: no API key, skipping R2")
            continue
        if model_name not in r2_evals:
            r2_evals[model_name] = {}

        model_r1 = evaluaciones[model_name]

        for oid in OUTPUT_IDS:
            if oid not in model_r1:
                continue
            # Skip cached OK results
            if oid in r2_evals[model_name] and "error" not in r2_evals[model_name][oid]:
                print(f"  [{model_name}] {oid}: cached, skip")
                continue

            # Build peer list
            other_evals = []
            for other in ALL_13:
                if other == model_name:
                    continue
                if other in evaluaciones and oid in evaluaciones[other]:
                    other_evals.append((other, evaluaciones[other][oid].get("celdas", {})))
            if not other_evals:
                print(f"  [{model_name}] {oid}: no peers, skip")
                continue

            output_text = test_outputs[oid]["output"]
            my_celdas = model_r1[oid]["celdas"]
            user_prompt = build_r2_user_prompt(output_text, my_celdas, other_evals)

            print(f"  [{model_name}] {oid} R2 ({len(other_evals)} peers)...", end=" ", flush=True)

            # Higher timeout for R2
            r2_cfg = dict(model_cfg)
            r2_cfg["timeout"] = max(model_cfg.get("timeout", 180), 240)

            result = None
            for attempt in range(2):
                try:
                    prompt = user_prompt
                    if attempt == 1:
                        prompt += (
                            "\n\nIMPORTANTE: Responde con JSON completo incluyendo "
                            "evaluacion_enriquecida, incorporado_de_otros, "
                            "mi_aporte_unico, y angulos_diferentes."
                        )
                    content, elapsed = call_model(model_name, r2_cfg, SYSTEM_R2, prompt)
                    parsed = extract_json(content)
                    if parsed:
                        validated = validate_r2(parsed, my_celdas)
                        if validated:
                            validated["tiempo_s"] = elapsed
                            result = validated
                            break
                    if attempt == 0:
                        print("(retry)", end=" ", flush=True)
                        time.sleep(3)
                except Exception as e:
                    err = str(e)
                    if attempt == 0:
                        wait = 30 if ("rate" in err.lower() or "429" in err) else 5
                        print(f"(err, wait {wait}s)", end=" ", flush=True)
                        time.sleep(wait)

            if result:
                r2_evals[model_name][oid] = result
                celdas_r2 = result["evaluacion_enriquecida"]["celdas"]
                niveles = [c.get("nivel", 0) for c in celdas_r2.values() if isinstance(c, dict)]
                medio = sum(niveles) / max(len(niveles), 1)
                n_inc = len(result.get("incorporado_de_otros", []))
                n_uni = len(result.get("mi_aporte_unico", []))
                print(f"OK ({elapsed}s, medio={medio:.2f}, +{n_inc}inc, {n_uni}uni)")
            else:
                r2_evals[model_name][oid] = {"error": "R2 parse failed"}
                print("FAIL")
            time.sleep(3)

        save_r2(r2_evals)

    # Summary
    print(f"\n--- R2 Final ---")
    for m in r2_models:
        r2m = r2_evals.get(m, {})
        ok = sum(1 for v in r2m.values() if "error" not in v)
        print(f"  {m}: {ok}/5 R2 OK")
    return r2_evals


# ── Main ─────────────────────────────────────────────────────────

def main():
    print("=== EXP 4: MESA REDONDA ===")
    print(f"13 modelos x 5 outputs x 2 rondas\n")

    for prov, cfg in PROVIDERS.items():
        s = "OK" if cfg.get("api_key") else "MISSING"
        print(f"  {prov}: {s}")

    ronda2_only = "--ronda2-only" in sys.argv
    ronda1_only = "--ronda1-only" in sys.argv

    if not ronda2_only:
        evaluaciones = consolidate_ronda1()
    else:
        with open(R1_FILE, encoding="utf-8") as f:
            evaluaciones = json.load(f)["evaluaciones"]

    if not ronda1_only:
        run_ronda2(evaluaciones)

    print(f"\nDONE")
    print(f"R1: {R1_FILE}")
    print(f"R2: {R2_FILE}")


if __name__ == "__main__":
    main()
