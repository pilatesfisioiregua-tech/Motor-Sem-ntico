"""Paso 1: Ejecuta modelos × variantes de prompt × 3 casos × 3 INTs."""
import json
import os
import re
import sys
import time
import requests as _requests
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

MODELS = {
    "70B": {
        "provider": "groq",
        "model_id": "llama-3.3-70b-versatile",
        "label": "Llama 3.3 70B",
        "variants": ["A", "B", "C", "D", "E"],
        "temperature": 0.3,
        "max_tokens": 8192,
        "timeout": 120,
        "use_system_prompt": True,
    },
    "Maverick": {
        "provider": "together",
        "model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "label": "Llama 4 Maverick",
        "variants": ["A", "B", "C", "D", "E"],
        "temperature": 0.3,
        "max_tokens": 8192,
        "timeout": 120,
        "use_system_prompt": True,
    },
    "DeepSeek-R1": {
        "provider": "together",
        "model_id": "deepseek-ai/DeepSeek-R1",
        "label": "DeepSeek R1",
        "variants": ["C"],
        "temperature": 0.6,
        "max_tokens": 8000,
        "timeout": 300,
        "use_system_prompt": False,
    },
    "Qwen3.5-397B": {
        "provider": "together",
        "model_id": "Qwen/Qwen3.5-397B-A17B",
        "label": "Qwen3.5 397B",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 300,
        "use_system_prompt": True,
    },
    "GPT-OSS-120B": {
        "provider": "together",
        "model_id": "openai/gpt-oss-120b",
        "label": "GPT-OSS 120B",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 180,
        "use_system_prompt": True,
    },
    "DeepSeek-V3.1": {
        "provider": "together",
        "model_id": "deepseek-ai/DeepSeek-V3.1",
        "label": "DeepSeek V3.1",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 180,
        "use_system_prompt": True,
    },
    "Qwen3-Thinking": {
        "provider": "together",
        "model_id": "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "label": "Qwen3 235B Thinking",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 300,
        "use_system_prompt": True,
    },
    "Kimi-K2.5": {
        "provider": "together",
        "model_id": "moonshotai/Kimi-K2.5",
        "label": "Kimi K2.5",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 180,
        "use_system_prompt": True,
    },
    "Cogito-671B": {
        "provider": "together",
        "model_id": "deepcogito/cogito-v2-1-671b",
        "label": "Cogito v2.1 671B",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 4000,
        "timeout": 300,
        "use_system_prompt": True,
    },
    "DeepSeek-V3.2-Chat": {
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "label": "DeepSeek V3.2 Chat",
        "variants": ["C"],
        "temperature": 1.0,
        "top_p": 0.95,
        "max_tokens": 4096,
        "timeout": 180,
        "use_system_prompt": True,
    },
    "DeepSeek-V3.2-Reasoner": {
        "provider": "deepseek",
        "model_id": "deepseek-reasoner",
        "label": "DeepSeek V3.2 Reasoner",
        "variants": ["C"],
        "temperature": 0.3,
        "max_tokens": 8192,
        "timeout": 300,
        "use_system_prompt": False,
    },
}

SYSTEM_PROMPT = (
    "Eres un analista experto. "
    "CALCULA cuando haya números. "
    "IDENTIFICA CONTRADICCIONES concretas. "
    "PROPÓN ACCIONES con coste y plazo específicos. "
    "No repitas datos — analízalos."
)

OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_FILE = OUTPUT_DIR / "all_outputs.json"
OLD_OUTPUT_FILE = OUTPUT_DIR / "llama_outputs.json"


def load_data() -> tuple[list[dict], dict]:
    with open(BASE_DIR / "data" / "cases.json", encoding="utf-8") as f:
        cases = json.load(f)
    with open(BASE_DIR / "data" / "question_networks.json", encoding="utf-8") as f:
        networks = json.load(f)
    return cases, networks


def run_key(case_id: str, int_id: str, model_key: str, variant: str) -> str:
    return f"{case_id}_{int_id}_{model_key}_{variant}"


def load_existing() -> dict[str, dict]:
    """Load existing results. Migrate old format if needed."""
    existing = {}

    # Migrate old llama_outputs.json → variant A, 70B
    if OLD_OUTPUT_FILE.exists() and not OUTPUT_FILE.exists():
        with open(OLD_OUTPUT_FILE, encoding="utf-8") as f:
            old_data = json.load(f)
        for item in old_data:
            if "error" in item:
                continue
            item["model_key"] = "70B"
            item["variant"] = "A"
            key = run_key(item["case_id"], item["int_id"], "70B", "A")
            existing[key] = item
        print(f"Migrados {len(existing)} runs previos como variante A / 70B")

    # Load existing all_outputs.json
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            if "error" in item:
                continue
            key = run_key(
                item["case_id"], item["int_id"],
                item.get("model_key", "70B"), item.get("variant", "A"),
            )
            existing[key] = item

    return existing


def save_outputs(results: list[dict]):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


# ── Prompt Variants ──────────────────────────────────────────────


def _structured_questions(mr: dict) -> str:
    """Build structured question blocks from meta_red."""
    sections = []

    extraer = mr["extraer"]
    qs = "\n".join(f"  - {q}" for q in extraer["preguntas"])
    sections.append(f"## PASO 1: EXTRAER — {extraer['nombre']}\n{qs}")

    cruzar = mr["cruzar"]
    qs = "\n".join(f"  - {q}" for q in cruzar["preguntas"])
    sections.append(f"## PASO 2: CRUZAR — {cruzar['nombre']}\n{qs}")

    lentes = []
    for lens in mr["lentes"]:
        qs = "\n".join(f"    - {q}" for q in lens["preguntas"])
        lentes.append(f"  ### Lente {lens['id']}: {lens['nombre']}\n{qs}")
    sections.append("## PASO 3: LENTES\n" + "\n".join(lentes))

    sections.append(f"## PASO 4: INTEGRAR\n  - {mr['integrar']}")
    sections.append(f"## PASO 5: ABSTRAER\n  - {mr['abstraer']}")
    sections.append(f"## PASO 6: FRONTERA\n  - {mr['frontera']}")

    return "\n\n".join(sections)


def _flat_questions(mr: dict) -> str:
    """All questions as a flat list."""
    qs = []
    for q in mr["extraer"]["preguntas"]:
        qs.append(q)
    for q in mr["cruzar"]["preguntas"]:
        qs.append(q)
    for lens in mr["lentes"]:
        for q in lens["preguntas"]:
            qs.append(q)
    qs.append(mr["integrar"])
    qs.append(mr["abstraer"])
    qs.append(mr["frontera"])
    return "\n".join(f"- {q}" for q in qs)


def build_prompt(case: dict, network: dict, variant: str) -> str:
    mr = network["meta_red"]
    case_block = f"# CASO: {case['nombre']}\n\n{case['input']}"
    structured = _structured_questions(mr)
    tail = "\nAl final: RESUMEN (máx 200 palabras) + FIRMA (1 frase con lo que SOLO este análisis ve)."

    if variant == "A":
        flat = _flat_questions(mr)
        return f"Analiza este caso respondiendo CADA pregunta. Sé concreto con los datos.\n\n{case_block}\n\n# PREGUNTAS\n{flat}{tail}"

    identity = (
        f"Opera bajo la inteligencia {network['nombre']}.\n"
        f"Firma: {network['firma']}\n"
        f"Punto ciego: {network['punto_ciego']}\n"
    )

    if variant == "B":
        return f"{identity}\nAnaliza este caso respondiendo CADA pregunta.\n\n{case_block}\n\n# RED DE PREGUNTAS — {network['nombre']}\n\n{structured}{tail}"

    if variant == "C":
        analytic = (
            "## INSTRUCCIÓN ANALÍTICA\n"
            "Antes de responder, extrae del caso:\n"
            "1. Todas las magnitudes numéricas y sus relaciones\n"
            "2. Ecuaciones implícitas entre ellas\n"
            "3. Restricciones duras (no negociables) vs blandas (ajustables)\n"
            "Usa estos datos como base para cada respuesta.\n"
        )
        return f"{identity}\n{analytic}\nAnaliza este caso respondiendo CADA pregunta.\n\n{case_block}\n\n# RED DE PREGUNTAS — {network['nombre']}\n\n{structured}{tail}"

    if variant == "D":
        deps = (
            "## DEPENDENCIAS ENTRE PASOS\n"
            "- EXTRAER produce datos crudos → úsalos explícitamente en CRUZAR\n"
            "- CRUZAR identifica tensiones → cada LENTE opera sobre ellas\n"
            "- Si dos LENTES se contradicen → INTEGRAR dice dónde y por qué\n"
            "- ABSTRAER: quita nombres y números, ¿qué patrón general queda?\n"
            "- FRONTERA: ¿qué NO puede ver este análisis? ¿qué asume sin examinar?\n"
        )
        return f"{identity}\n{deps}\nAnaliza este caso respondiendo CADA pregunta.\n\n{case_block}\n\n# RED DE PREGUNTAS — {network['nombre']}\n\n{structured}{tail}"

    if variant == "E":
        meta = (
            "## INSTRUCCIÓN ANALÍTICA\n"
            "Extrae primero: magnitudes numéricas, ecuaciones implícitas, restricciones duras vs blandas.\n\n"
            "## DEPENDENCIAS\n"
            "EXTRAER → CRUZAR → LENTES → INTEGRAR → ABSTRAER → FRONTERA.\n"
            "Cada paso usa explícitamente el output del anterior.\n\n"
            "## INSTRUCCIONES POR LENTE\n"
            "Para cada lente, produce obligatoriamente:\n"
            "1. Un hallazgo ESPECÍFICO de este caso (no genérico)\n"
            "2. Un número o dato concreto del caso que lo respalde\n"
            "3. Una implicación concreta para la decisión\n"
        )
        return f"{identity}\n{meta}\nAnaliza este caso respondiendo CADA pregunta.\n\n{case_block}\n\n# RED DE PREGUNTAS — {network['nombre']}\n\n{structured}{tail}"

    raise ValueError(f"Variante desconocida: {variant}")


# ── API Calls ────────────────────────────────────────────────────


def call_groq(prompt: str, model_cfg: dict) -> tuple[str, dict, float]:
    """Call Groq API. Returns (text, usage_dict, elapsed_seconds)."""
    client = Groq(api_key=GROQ_API_KEY)
    messages = []
    if model_cfg["use_system_prompt"]:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": prompt})

    t0 = time.time()
    resp = client.chat.completions.create(
        model=model_cfg["model_id"],
        messages=messages,
        temperature=model_cfg["temperature"],
        max_tokens=model_cfg["max_tokens"],
    )
    elapsed = round(time.time() - t0, 2)
    usage = {
        "prompt": resp.usage.prompt_tokens,
        "completion": resp.usage.completion_tokens,
        "total": resp.usage.total_tokens,
    }
    return resp.choices[0].message.content, usage, elapsed, ""


def extract_thinking(text: str) -> tuple[str, str]:
    """Extract <think>...</think> from DeepSeek R1 output.
    Returns (thinking, response)."""
    match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
    if match:
        thinking = match.group(1).strip()
        response = text[match.end():].strip()
        return thinking, response
    return "", text


def call_together(prompt: str, model_cfg: dict) -> tuple[str, dict, float]:
    """Call Together API via REST. Returns (text, usage_dict, elapsed_seconds)."""
    messages = []
    if model_cfg["use_system_prompt"]:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": prompt})
    else:
        # For DeepSeek R1: no system prompt, prepend instructions to user message
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        messages.append({"role": "user", "content": full_prompt})

    t0 = time.time()
    resp = _requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model_cfg["model_id"],
            "messages": messages,
            "temperature": model_cfg["temperature"],
            "max_tokens": model_cfg["max_tokens"],
        },
        timeout=model_cfg["timeout"],
    )
    elapsed = round(time.time() - t0, 2)

    if resp.status_code != 200:
        raise RuntimeError(f"Together API {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    msg = data["choices"][0]["message"]
    text = msg.get("content", "") or ""
    # Some models (Qwen3.5, GPT-OSS) put reasoning in a separate field
    reasoning = msg.get("reasoning", "") or ""
    # If content is empty but reasoning has text, use reasoning as the output
    if not text.strip() and reasoning.strip():
        text = reasoning
    u = data.get("usage", {})
    usage = {
        "prompt": u.get("prompt_tokens", 0),
        "completion": u.get("completion_tokens", 0),
        "total": u.get("total_tokens", 0),
    }
    return text, usage, elapsed, reasoning


def call_deepseek(prompt: str, model_cfg: dict) -> tuple[str, dict, float, str]:
    """Call DeepSeek direct API via OpenAI client. Returns (text, usage, elapsed, reasoning)."""
    from openai import OpenAI

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    messages = []
    if model_cfg["use_system_prompt"]:
        messages.append({"role": "system", "content": SYSTEM_PROMPT})
        messages.append({"role": "user", "content": prompt})
    else:
        full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
        messages.append({"role": "user", "content": full_prompt})

    kwargs = {
        "model": model_cfg["model_id"],
        "messages": messages,
        "max_tokens": model_cfg["max_tokens"],
    }
    # deepseek-reasoner doesn't support temperature
    if model_cfg["model_id"] != "deepseek-reasoner":
        kwargs["temperature"] = model_cfg["temperature"]
        if "top_p" in model_cfg:
            kwargs["top_p"] = model_cfg["top_p"]

    t0 = time.time()
    resp = client.chat.completions.create(**kwargs)
    elapsed = round(time.time() - t0, 2)

    text = resp.choices[0].message.content or ""
    reasoning = getattr(resp.choices[0].message, "reasoning_content", "") or ""
    # If content is empty but reasoning has text, use reasoning as the output
    if not text.strip() and reasoning.strip():
        text = reasoning

    usage = {
        "prompt": resp.usage.prompt_tokens,
        "completion": resp.usage.completion_tokens,
        "total": resp.usage.total_tokens,
    }
    return text, usage, elapsed, reasoning


def call_model(model_cfg: dict, prompt: str) -> tuple[str, dict, float, str]:
    """Dispatch to provider with retry. Returns (text, usage, elapsed, reasoning)."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if model_cfg["provider"] == "groq":
                return call_groq(prompt, model_cfg)
            elif model_cfg["provider"] == "together":
                return call_together(prompt, model_cfg)
            elif model_cfg["provider"] == "deepseek":
                return call_deepseek(prompt, model_cfg)
            else:
                raise ValueError(f"Provider desconocido: {model_cfg['provider']}")
        except Exception as e:
            err_str = str(e).lower()
            if "rate" in err_str or "429" in err_str or "limit" in err_str:
                wait = (attempt + 1) * 15
                print(f"RATE LIMIT, esperando {wait}s...", end=" ", flush=True)
                time.sleep(wait)
                continue
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            raise


# ── Main ─────────────────────────────────────────────────────────


def main():
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY no configurada")
        sys.exit(1)
    if not TOGETHER_API_KEY:
        print("ERROR: TOGETHER_API_KEY no configurada")
        sys.exit(1)

    cases, networks = load_data()
    existing = load_existing()

    # Plan runs — use per-model variant lists
    planned = []
    total = 0
    for model_key, model_cfg in MODELS.items():
        for variant in model_cfg["variants"]:
            for case in cases:
                for int_id in networks:
                    total += 1
                    key = run_key(case["id"], int_id, model_key, variant)
                    if key not in existing:
                        planned.append((model_key, variant, case, int_id))

    print(f"Total combinaciones: {total}")
    print(f"Ya completadas: {len(existing)}")
    print(f"Pendientes: {len(planned)}")

    if not planned:
        print("Nada que ejecutar.")
        save_outputs(list(existing.values()))
        return

    results = list(existing.values())
    done = 0

    for model_key, variant, case, int_id in planned:
        done += 1
        network = networks[int_id]
        model_cfg = MODELS[model_key]
        label = f"{case['nombre']} × {network['nombre']} [{model_key}/{variant}]"
        print(f"[{done}/{len(planned)}] {label}...", end=" ", flush=True)

        try:
            prompt = build_prompt(case, network, variant)
            text, usage, elapsed, reasoning = call_model(model_cfg, prompt)

            result = {
                "case_id": case["id"],
                "case_nombre": case["nombre"],
                "int_id": int_id,
                "int_nombre": network["nombre"],
                "model": model_cfg["model_id"],
                "model_key": model_key,
                "model_label": model_cfg["label"],
                "variant": variant,
                "output": text,
                "tokens": usage,
                "tiempo_s": elapsed,
            }

            # Store reasoning if present (Qwen3.5, GPT-OSS)
            if reasoning:
                result["reasoning"] = reasoning

            # DeepSeek R1: extract thinking separately
            if model_key == "DeepSeek-R1":
                thinking, response = extract_thinking(text)
                result["thinking"] = thinking
                result["output"] = response

            results.append(result)
            print(f"OK ({elapsed}s, {usage['total']} tok)")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "case_id": case["id"],
                "int_id": int_id,
                "model_key": model_key,
                "variant": variant,
                "error": str(e),
            })

        # Save incrementally
        save_outputs(results)

        # Rate limit delay
        time.sleep(3 if model_cfg["provider"] == "groq" else 2)

    # Final summary
    ok = sum(1 for r in results if "error" not in r)
    print(f"\nTotal resultados: {ok}/{total} exitosos")
    total_tokens = sum(r.get("tokens", {}).get("total", 0) for r in results)
    print(f"Tokens totales: {total_tokens:,}")


if __name__ == "__main__":
    main()
