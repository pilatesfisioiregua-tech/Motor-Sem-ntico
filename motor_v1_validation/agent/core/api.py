"""OpenRouter + Anthropic API client — dual-path with DB-driven model registry."""

import os
import re
import json
import time
from typing import Optional, Tuple
from pathlib import Path

MODEL_CALL_TIMEOUT = 60

# Load API key
def _load_env() -> None:
    for env_path in [
        Path(__file__).parent.parent.parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
            break

_load_env()

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ---- DB-driven model config via Observatory (with hardcoded fallback) ---- #

def _get_observatory():
    """Lazy import to avoid circular dependency."""
    try:
        from .model_observatory import get_observatory
        return get_observatory()
    except Exception:
        return None

def get_tier_config() -> dict:
    """Get current tier config from observatory or fallback."""
    obs = _get_observatory()
    if obs:
        return obs.get_tier_config()
    # Consolidated 4-role architecture — MAX ROI open-source (March 2026)
    # Optimizado por coste-por-tarea-completada, no por coste-por-token
    # Qwen3-Coder: Agent RL trained, SOTA agentic tool-use — mejor seguimiento instrucciones
    # MiniMax M2.5: 80.2% SWE-bench (#1 open-weight) — arregla código en menos iteraciones
    # GLM-5: #1 Arena rating (1451 ELO) — mejor juicio y evaluación
    return {
        "cerebro":       "qwen/qwen3-coder",               # orquesta, decide, encadena (Agent RL)
        "worker":        "minimax/minimax-m2.5",            # código + fix (80.2% SWE-bench, menos iters)
        "worker_budget": "deepseek/deepseek-v3.2",          # fallback para tareas simples
        "evaluador":     "z-ai/glm-5",                     # evaluación + juicio (#1 Arena)
        "swarm":         "deepseek/deepseek-v3.2",          # exploradores paralelos (volumen)
        # Legacy aliases for backward compatibility
        "orchestrator":  "qwen/qwen3-coder",
        "synthesis":     "z-ai/glm-5",
    }

def get_model_pricing(model_id: str) -> float:
    """Get output price per M tokens from observatory or fallback."""
    obs = _get_observatory()
    if obs:
        return obs.get_output_price(model_id)
    # Hardcoded fallback — OpenRouter pricing March 2026
    fallback = {
        # Current stack (MAX ROI)
        "qwen/qwen3-coder": 1.00,
        "minimax/minimax-m2.5": 1.20,
        "z-ai/glm-5": 2.30,
        "deepseek/deepseek-v3.2": 0.38,
        # Anthropic
        "claude-sonnet-4-6": 15.00, "claude-opus-4-6": 25.00,
        # Legacy (kept for compatibility)
        "mistralai/devstral-2512": 0.60,
        "stepfun/step-3.5-flash": 3.80,
        "xiaomi/mimo-v2-flash": 0.28,
        "deepcogito/cogito-v2.1-671b": 5.00,
        "openai/gpt-4o-mini": 0.60,
        "moonshotai/kimi-k2.5": 2.20,
    }
    return fallback.get(model_id, 1.0)

def is_anthropic_model(model_id: str) -> bool:
    """Check if model uses Anthropic API directly."""
    return model_id in {"claude-sonnet-4-6", "claude-opus-4-6"}

# Legacy compatibility aliases (old tier1/tier2/tier3 names map to new function-based tiers)
TIER_CONFIG = get_tier_config()
# Add backward-compat aliases for code that still uses tier1/tier2/tier3
TIER_CONFIG.setdefault("tier1", TIER_CONFIG.get("worker_budget", "xiaomi/mimo-v2-flash"))
TIER_CONFIG.setdefault("tier2", TIER_CONFIG.get("worker", "stepfun/step-3.5-flash"))
TIER_CONFIG.setdefault("tier2b", TIER_CONFIG.get("worker_budget", "xiaomi/mimo-v2-flash"))
TIER_CONFIG.setdefault("tier3", TIER_CONFIG.get("orchestrator", "mistralai/devstral-2512"))
# Legacy aliases that no longer have direct equivalents
TIER_CONFIG.setdefault("code_gen", TIER_CONFIG.get("worker", "stepfun/step-3.5-flash"))
TIER_CONFIG.setdefault("compress", TIER_CONFIG.get("worker_budget", "xiaomi/mimo-v2-flash"))
TIER_CONFIG.setdefault("fallback", TIER_CONFIG.get("worker_budget", "xiaomi/mimo-v2-flash"))
MODEL_PRICING = {mid: get_model_pricing(mid) for mid in set(TIER_CONFIG.values())}
MODELS = {k: v for k, v in TIER_CONFIG.items()}


def strip_think_tags(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


# Shared httpx client with connection pooling (lazy init)
_http_client = None

def _get_http_client():
    global _http_client
    if _http_client is None:
        import httpx
        _http_client = httpx.Client(
            base_url="https://openrouter.ai/api/v1",
            timeout=httpx.Timeout(MODEL_CALL_TIMEOUT, connect=15.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
    return _http_client


def reset_http_client():
    """Reset the cached HTTP client (e.g., after timeout change)."""
    global _http_client
    if _http_client:
        _http_client.close()
    _http_client = None


def call_openrouter(messages: list, model: str, tools: list = None,
                    temperature: float = 0.0, max_tokens: int = 16384) -> dict:
    """Call OpenRouter via httpx with connection pooling. Auto-registers cost."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    t0 = time.time()
    try:
        client = _get_http_client()
        resp = client.post(
            "/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://omni-mind.app",
                "X-Title": "OMNI-MIND Code OS v3",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"API: {data['error']}")

        # Auto-register cost
        latencia = int((time.time() - t0) * 1000)
        usage = data.get('usage', {})
        try:
            from .costes import registrar_coste
            registrar_coste(
                modelo=model,
                tokens_input=usage.get('prompt_tokens', 0),
                tokens_output=usage.get('completion_tokens', 0),
                latencia_ms=latencia,
                provider='openrouter',
            )
        except Exception:
            pass

        return data
    except Exception as e:
        if hasattr(e, '__module__') and "httpx" in getattr(type(e), '__module__', ''):
            raise RuntimeError(f"OpenRouter HTTP error: {e}")
        raise


def call_with_retry(messages: list, model: str, tools: list = None,
                    max_retries: int = 3, **kwargs) -> dict:
    for attempt in range(max_retries):
        try:
            return call_openrouter(messages, model, tools, **kwargs)
        except (json.JSONDecodeError, RuntimeError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"API failed after {max_retries} tries: {e}")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("Unreachable")


def extract_response(api_resp: dict) -> Tuple[str, Optional[list], bool]:
    """Extract content + tool_calls + reasoning_blowup flag."""
    msg = api_resp["choices"][0]["message"]
    content = strip_think_tags(msg.get("content") or "")
    tool_calls = msg.get("tool_calls")

    if not content and not tool_calls:
        reasoning = msg.get("reasoning", "") or ""
        if len(reasoning) > 1000:
            return "(REASONING_BLOWUP: model spent all tokens thinking, no action)", None, True
        return "(No content or tool calls)", None, False
    return content, tool_calls, False


def call_anthropic(messages: list, model: str = "claude-sonnet-4-6",
                   tools: list = None, temperature: float = 0.0,
                   max_tokens: int = 16384, system: str = None) -> dict:
    """Call Anthropic API directly for Claude models. Returns parsed response."""
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed")

    client = anthropic.Anthropic()

    kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": messages,
        "temperature": temperature,
    }
    if system:
        kwargs["system"] = system
    if tools:
        # Convert OpenRouter tool format to Anthropic format
        anthropic_tools = []
        for t in tools:
            if t.get("type") == "function":
                fn = t["function"]
                anthropic_tools.append({
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
                })
            else:
                anthropic_tools.append(t)
        kwargs["tools"] = anthropic_tools

    resp = client.messages.create(**kwargs)

    # Convert to OpenRouter-compatible format
    content_text = ""
    tool_calls = []
    for block in resp.content:
        if block.type == "text":
            content_text += block.text
        elif block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "type": "function",
                "function": {
                    "name": block.name,
                    "arguments": json.dumps(block.input),
                },
            })

    result = {
        "choices": [{
            "message": {
                "content": content_text or None,
                "tool_calls": tool_calls if tool_calls else None,
            },
        }],
        "usage": {
            "prompt_tokens": resp.usage.input_tokens,
            "completion_tokens": resp.usage.output_tokens,
        },
        "model": model,
    }

    # Auto-register cost
    try:
        from .costes import registrar_coste
        registrar_coste(
            modelo=model,
            tokens_input=resp.usage.input_tokens,
            tokens_output=resp.usage.output_tokens,
            provider='anthropic',
        )
    except Exception:
        pass

    return result


def call_model(messages: list, model: str, tools: list = None,
               temperature: float = 0.0, max_tokens: int = 16384,
               system: str = None) -> dict:
    """Universal model caller — routes to Anthropic or OpenRouter based on model ID."""
    if is_anthropic_model(model):
        return call_anthropic(messages, model, tools, temperature, max_tokens, system)
    return call_openrouter(messages, model, tools, temperature, max_tokens)


def call_model_with_retry(messages: list, model: str, tools: list = None,
                          max_retries: int = 3, **kwargs) -> dict:
    """Universal call with retry — routes to correct API."""
    for attempt in range(max_retries):
        try:
            return call_model(messages, model, tools, **kwargs)
        except Exception as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"API failed after {max_retries} tries: {e}")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("Unreachable")
