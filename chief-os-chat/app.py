"""Chief OS Chat v0.1 — Enjambre de modelos OS con estigmergia. DeepSeek directo + OpenRouter."""
import asyncio
import os
import re
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Chief OS Chat")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
PORT = int(os.getenv("PORT", 8080))

# --- Models ---
# provider: "deepseek" = direct API, "openrouter" = via OpenRouter
MODELS = {
    "v3.2": {
        "id": "deepseek-chat",
        "provider": "deepseek",
        "name": "V3.2-chat",
        "cost_in": 0.27,   # per 1M tokens (DeepSeek pricing)
        "cost_out": 1.10,
    },
    "v3.1": {
        "id": "deepseek/deepseek-chat-v3.1",
        "provider": "openrouter",
        "name": "V3.1",
        "cost_in": 0.15,
        "cost_out": 0.75,
    },
    "r1": {
        "id": "deepseek-reasoner",
        "provider": "deepseek",
        "name": "R1",
        "cost_in": 0.55,
        "cost_out": 2.19,
    },
    "cogito": {
        "id": "deepcogito/cogito-v2.1-671b",
        "provider": "openrouter",
        "name": "Cogito 671B",
        "cost_in": 1.25,
        "cost_out": 1.25,
    },
}

ENJAMBRE_KEYS = ["v3.2", "v3.1", "r1"]

SYSTEM_PROMPT = """Eres el Chief of Staff de OMNI-MIND v4, un sistema cognitivo basado en una Matriz 3 Lentes × 7 Funciones × 18 Inteligencias.

Contexto:
- 3 Lentes: Salud/Supervivencia, Sentido/Coherencia, Continuidad/Sostenibilidad
- 7 Funciones: Conservar, Captar, Depurar, Distribuir, Frontera, Adaptar, Replicar
- La Matriz es un campo de gradientes donde cada celda tiene grado_actual, grado_objetivo y gap
- Los gaps dirigen la ejecución

Principios:
- Jesús cierra (CR1), tú propones (CR0)
- Verdad brutal > ego
- Implementación > teoría
- Si no está documentado, no existe

Responde en español. Sé directo, concreto, sin rodeos."""

SYNTH_PROMPT = """Eres el sintetizador de un enjambre de modelos OS en OMNI-MIND v4.

Tu trabajo:
1. Integrar perspectivas donde convergen — no repetir, comprimir
2. Señalar divergencias significativas y por qué importan
3. Extraer lo accionable
4. Señalar puntos ciegos que ningún modelo cubrió

Prosa directa, español, brutal."""

DEEP_SIGNALS = [
    "cómo", "por qué", "diseña", "analiza", "debería", "arquitectura",
    "migración", "decisión", "trade-off", "riesgo", "estrategia",
    "propuesta", "spec", "prioriza", "matriz",
]

HELP_TEXT = """**Chief OS Chat v0.1** — Enjambre de modelos OS con estigmergia

**Comandos:**
- `/fast <msg>` — Fuerza modo superficial (1 modelo)
- `/deep <msg>` — Fuerza modo profundo (2 rondas estigmérticas + síntesis)
- `/models` — Muestra configuración de modelos
- `/help` — Este mensaje

**Auto-routing:**
- Superficial: mensajes cortos, preguntas simples → 1 modelo (V3.2)
- Profundo: mensajes >200 chars, señales de análisis, 2+ preguntas

**Modo profundo (estigmergia):**
- Ronda 1: 3 modelos responden en paralelo
- Ronda 2: cada modelo lee lo que los OTROS 2 dijeron → enriquece/contradice
- Síntesis: Cogito 671B integra la pizarra completa (6 bloques)

**Providers:**
- V3.2, R1 → API directa DeepSeek (menor latencia)
- V3.1, Cogito → OpenRouter"""


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


def classify_depth(message: str) -> str:
    """Classify message as superficial or profundo."""
    msg_lower = message.lower()
    signal_count = sum(1 for s in DEEP_SIGNALS if s in msg_lower)
    question_count = message.count("?")
    if len(message) > 200:
        return "profundo"
    if signal_count >= 2:
        return "profundo"
    if question_count >= 2:
        return "profundo"
    return "superficial"


def parse_thinking(content: str) -> tuple[str, Optional[str]]:
    """Separate <think>...</think> from content."""
    if not content:
        return "", None
    think_match = re.search(r"<think>([\s\S]*?)</think>", content, re.DOTALL)
    thinking = think_match.group(1).strip() if think_match else None
    clean = re.sub(r"<think>[\s\S]*?</think>", "", content, flags=re.DOTALL).strip()
    if not clean and "<think>" in content:
        parts = content.split("<think>")
        for part in reversed(parts):
            c = part.strip()
            if c and not c.startswith("</think>"):
                clean = c
                break
    return clean or content.strip(), thinking


def estimate_cost(tokens_in: int, tokens_out: int, model_key: str) -> float:
    """Estimate cost in USD."""
    m = MODELS[model_key]
    return (tokens_in / 1_000_000) * m["cost_in"] + (tokens_out / 1_000_000) * m["cost_out"]


async def call_model(client: httpx.AsyncClient, model_key: str,
                     messages: list[dict], max_tokens: int = 2000) -> dict:
    """Call a model via DeepSeek direct API or OpenRouter."""
    model = MODELS[model_key]
    provider = model["provider"]
    t0 = time.time()

    if provider == "deepseek":
        url = "https://api.deepseek.com/chat/completions"
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
    else:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://chief-os-omni.fly.dev",
            "X-Title": "OMNI-MIND Chief OS",
        }

    try:
        resp = await client.post(
            url,
            headers=headers,
            json={
                "model": model["id"],
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=120.0,
        )
        elapsed = time.time() - t0
        data = resp.json()

        if "error" in data:
            err_msg = data["error"]
            if isinstance(err_msg, dict):
                err_msg = err_msg.get("message", str(err_msg))
            return {
                "model": model["name"],
                "model_key": model_key,
                "provider": provider,
                "content": f"Error: {err_msg}",
                "latency_s": round(elapsed, 1),
                "tokens_out": 0,
                "cost_usd": 0,
                "thinking": None,
                "error": True,
            }

        raw_content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        content, thinking = parse_thinking(raw_content)

        # R1 via DeepSeek direct returns reasoning_content separately
        if provider == "deepseek" and model_key == "r1" and not thinking:
            reasoning = data.get("choices", [{}])[0].get("message", {}).get("reasoning_content", "")
            if reasoning:
                thinking = reasoning.strip()

        cost = estimate_cost(tokens_in, tokens_out, model_key)

        return {
            "model": model["name"],
            "model_key": model_key,
            "provider": provider,
            "content": content,
            "latency_s": round(elapsed, 1),
            "tokens_out": tokens_out,
            "cost_usd": round(cost, 6),
            "thinking": thinking,
            "error": False,
        }
    except Exception as e:
        return {
            "model": model["name"],
            "model_key": model_key,
            "provider": provider,
            "content": f"Error: {str(e)}",
            "latency_s": round(time.time() - t0, 1),
            "tokens_out": 0,
            "cost_usd": 0,
            "thinking": None,
            "error": True,
        }


def build_messages(history: list[dict], user_content: str, system: str) -> list[dict]:
    """Build messages list with system prompt and last 10 turns of history."""
    msgs = [{"role": "system", "content": system}]
    for turn in history[-10:]:
        msgs.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
    msgs.append({"role": "user", "content": user_content})
    return msgs


def build_r2_prompt(question: str, model_key: str, ronda_1: list[dict]) -> str:
    """Build round 2 prompt: original question + what the OTHER models said."""
    others = [r for r in ronda_1 if r["model_key"] != model_key and not r.get("error")]
    pizarra_text = ""
    for r in others:
        pizarra_text += f"[{r['model']}]:\n{r['content']}\n\n"

    return (
        f"{question}\n\n"
        f"PIZARRA DEL ENJAMBRE (ronda anterior):\n\n"
        f"{pizarra_text}"
        f"Con esta información adicional, ¿qué añades, contradices o matizas "
        f"de tu análisis inicial? Sé específico sobre dónde los otros aportan "
        f"algo que tú no viste y dónde crees que se equivocan."
    )


def build_synth_prompt(question: str, ronda_1: list[dict], ronda_2: list[dict]) -> str:
    """Build synthesis prompt with the full pizarra."""
    text = f'Pregunta del usuario: "{question}"\n\nPIZARRA DEL ENJAMBRE:\n\n'
    text += "=== RONDA 1 (exploración inicial) ===\n\n"
    for r in ronda_1:
        text += f"[{r['model']}]:\n{r['content']}\n\n"
    text += "=== RONDA 2 (enriquecimiento tras leer a los demás) ===\n\n"
    for r in ronda_2:
        text += f"[{r['model']}]:\n{r['content']}\n\n"
    return text


def strip_internal_fields(entry: dict) -> dict:
    """Remove internal fields from response entry."""
    return {k: v for k, v in entry.items() if k not in ("model_key",)}


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "deepseek_key_set": bool(DEEPSEEK_API_KEY),
        "openrouter_key_set": bool(OPENROUTER_API_KEY),
    }


@app.post("/chat")
async def chat(req: ChatRequest):
    message = req.message.strip()
    history = req.history

    # Special commands
    if message.lower() == "/models":
        model_info = []
        for k, m in MODELS.items():
            prov = "DeepSeek direct" if m["provider"] == "deepseek" else "OpenRouter"
            model_info.append(f"**{k}**: `{m['id']}` via {prov} — ${m['cost_in']}/{m['cost_out']} per 1M tok")
        return {
            "mode": "system",
            "synthesis": "**Configuración de modelos:**\n\n" + "\n".join(model_info),
            "individual_responses": [],
            "models_used": [],
            "total_latency_s": 0,
            "total_cost_usd": 0,
        }

    if message.lower() == "/help":
        return {
            "mode": "system",
            "synthesis": HELP_TEXT,
            "individual_responses": [],
            "models_used": [],
            "total_latency_s": 0,
            "total_cost_usd": 0,
        }

    # Depth routing
    forced_mode = None
    if message.lower().startswith("/fast "):
        forced_mode = "superficial"
        message = message[6:].strip()
    elif message.lower().startswith("/deep "):
        forced_mode = "profundo"
        message = message[6:].strip()

    mode = forced_mode or classify_depth(message)
    t_start = time.time()

    async with httpx.AsyncClient() as client:
        if mode == "superficial":
            msgs = build_messages(history, message, SYSTEM_PROMPT)
            result = await call_model(client, "v3.2", msgs)
            total_latency = round(time.time() - t_start, 1)
            return {
                "mode": "superficial",
                "synthesis": result["content"],
                "individual_responses": [strip_internal_fields(result)],
                "models_used": [result["model"]],
                "total_latency_s": total_latency,
                "total_cost_usd": result["cost_usd"],
            }

        # --- MODO PROFUNDO: Estigmergia con pizarra ---

        # RONDA 1 — Exploración inicial (paralelo)
        r1_msgs = build_messages(history, message, SYSTEM_PROMPT)
        ronda_1_results = await asyncio.gather(
            call_model(client, "v3.2", r1_msgs, max_tokens=800),
            call_model(client, "v3.1", r1_msgs, max_tokens=800),
            call_model(client, "r1", r1_msgs, max_tokens=800),
        )
        ronda_1 = list(ronda_1_results)

        # RONDA 2 — Enriquecimiento estigmértico (paralelo)
        r2_tasks = []
        for key in ENJAMBRE_KEYS:
            r2_user = build_r2_prompt(message, key, ronda_1)
            r2_msgs = build_messages(history, r2_user, SYSTEM_PROMPT)
            r2_tasks.append(call_model(client, key, r2_msgs, max_tokens=800))
        ronda_2_results = await asyncio.gather(*r2_tasks)
        ronda_2 = list(ronda_2_results)

        # SÍNTESIS — Cogito integra toda la pizarra
        synth_user = build_synth_prompt(message, ronda_1, ronda_2)
        synth_msgs = [
            {"role": "system", "content": SYNTH_PROMPT},
            {"role": "user", "content": synth_user},
        ]
        synth_result = await call_model(client, "cogito", synth_msgs, max_tokens=2000)

        # Aggregate
        all_entries = ronda_1 + ronda_2 + [synth_result]
        total_cost = round(sum(r["cost_usd"] for r in all_entries), 6)
        total_latency = round(time.time() - t_start, 1)
        models_used = [MODELS[k]["name"] for k in ENJAMBRE_KEYS]
        models_used.append(f"{synth_result['model']} (síntesis)")

        return {
            "mode": "profundo",
            "synthesis": synth_result["content"],
            "pizarra": {
                "ronda_1": [strip_internal_fields(r) for r in ronda_1],
                "ronda_2": [strip_internal_fields(r) for r in ronda_2],
            },
            "synthesizer_meta": {
                "model": synth_result["model"],
                "latency_s": synth_result["latency_s"],
                "tokens_out": synth_result["tokens_out"],
                "cost_usd": synth_result["cost_usd"],
            },
            "models_used": models_used,
            "total_latency_s": total_latency,
            "total_cost_usd": total_cost,
            "rounds": 2,
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
