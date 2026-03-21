#!/usr/bin/env python3
"""Diagnóstico de Conectividad — Aísla API vs Modelo vs Agente.

Testea cada modelo del stack DIRECTAMENTE contra OpenRouter,
sin pasar por Code OS. Si esto falla → problema de API/key/red.
Si esto pasa y Code OS falla → problema en el agente.

Uso:
  python3 diag_conectividad_modelos.py
  python3 diag_conectividad_modelos.py --skip-codeos
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# ── Cargar .env ──
for env_path in [
    Path(__file__).parent.parent / "motor_v1_validation" / "agent" / ".env",
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent / ".env",
]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))
        break

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_KEY:
    print("⛔ OPENROUTER_API_KEY no encontrada en .env")
    sys.exit(1)

# ── Stack actual (de api.py) ──
MODELS = {
    "cerebro":       "qwen/qwen3-coder",
    "worker":        "minimax/minimax-m2.5",
    "worker_budget": "deepseek/deepseek-v3.2",
    "evaluador":     "z-ai/glm-5",
}

SIMPLE_MESSAGES = [
    {"role": "user", "content": "Responde exactamente: OK"}
]

TOOL_MESSAGES = [
    {"role": "system", "content": "Usa la herramienta finish cuando termines."},
    {"role": "user", "content": "Di 'hola' y llama finish con result='done'."},
]

SIMPLE_TOOL = [{
    "type": "function",
    "function": {
        "name": "finish",
        "description": "Terminar la tarea",
        "parameters": {
            "type": "object",
            "properties": {
                "result": {"type": "string", "description": "Resultado"}
            },
            "required": ["result"]
        }
    }
}]


def call_openrouter(model, messages, tools=None, timeout=30):
    import urllib.request
    import urllib.error

    body = {
        "model": model,
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.0,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "HTTP-Referer": "https://omni-mind.app",
            "X-Title": "OMNI-MIND Diagnostico",
        },
        method="POST",
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            elapsed = time.time() - t0
            return {"ok": True, "data": result, "time_s": round(elapsed, 2)}
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        body_text = ""
        try:
            body_text = e.read().decode()[:500]
        except:
            pass
        return {"ok": False, "error": f"HTTP {e.code}", "body": body_text, "time_s": round(elapsed, 2)}
    except Exception as e:
        elapsed = time.time() - t0
        return {"ok": False, "error": str(e), "time_s": round(elapsed, 2)}


def extract_content(result):
    if not result.get("ok"):
        return None, None
    try:
        msg = result["data"]["choices"][0]["message"]
        content = msg.get("content", "")
        tool_calls = msg.get("tool_calls")
        usage = result["data"].get("usage", {})
        return {
            "content": content[:200] if content else "(vacío)",
            "tool_calls": len(tool_calls) if tool_calls else 0,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
        }, None
    except Exception as e:
        return None, str(e)


def test_code_os_health(base_url):
    import urllib.request
    try:
        req = urllib.request.Request(f"{base_url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def test_code_os_simple(base_url):
    import urllib.request
    body = json.dumps({
        "input": "Responde 'OK' y llama finish.",
        "mode": "auto",
    }).encode()
    req = urllib.request.Request(
        f"{base_url}/code-os/execute",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    events = []
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            buffer = ""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk.decode(errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line.startswith("data: "):
                        try:
                            evt = json.loads(line[6:])
                            events.append(evt)
                            if evt.get("type") in ("done", "error"):
                                elapsed = time.time() - t0
                                return {"ok": evt.get("type") == "done", "events": events,
                                        "time_s": round(elapsed, 2)}
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        elapsed = time.time() - t0
        return {"ok": False, "error": str(e), "events": events, "time_s": round(elapsed, 2)}
    elapsed = time.time() - t0
    return {"ok": False, "error": "stream ended without done/error", "events": events,
            "time_s": round(elapsed, 2)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnostico de conectividad de modelos")
    parser.add_argument("--base-url", default="https://chief-os-omni.fly.dev")
    parser.add_argument("--skip-codeos", action="store_true", help="Solo testear OpenRouter directo")
    args = parser.parse_args()

    print("=" * 52)
    print("  DIAGNOSTICO CONECTIVIDAD MODELOS")
    print("=" * 52)
    print(f"  API Key: ...{OPENROUTER_KEY[-8:]}")
    print()

    # FASE 1
    print("=== FASE 1: OpenRouter directo (sin Code OS) ===\n")

    all_ok = True
    for role, model in MODELS.items():
        print(f"  [{role}] {model}...", end=" ", flush=True)
        r = call_openrouter(model, SIMPLE_MESSAGES, timeout=30)
        if r["ok"]:
            parsed, err = extract_content(r)
            if parsed:
                print(f"OK {r['time_s']}s -- {parsed['content'][:60]}")
            else:
                print(f"WARN {r['time_s']}s -- parse error: {err}")
        else:
            print(f"FAIL {r['time_s']}s -- {r['error']}")
            if r.get("body"):
                print(f"       Body: {r['body'][:200]}")
            all_ok = False

    print()

    # FASE 2
    print("=== FASE 2: Cerebro con tool_call ===\n")

    cerebro = MODELS["cerebro"]
    print(f"  [{cerebro}] con finish() tool...", end=" ", flush=True)
    r = call_openrouter(cerebro, TOOL_MESSAGES, tools=SIMPLE_TOOL, timeout=30)
    if r["ok"]:
        parsed, err = extract_content(r)
        if parsed:
            tc = parsed["tool_calls"]
            print(f"OK {r['time_s']}s -- tool_calls={tc}, tokens_out={parsed['tokens_out']}")
            if tc == 0:
                print(f"       WARN: Respondio pero NO llamo finish(). Content: {parsed['content'][:80]}")
        else:
            print(f"WARN {r['time_s']}s -- parse error: {err}")
    else:
        print(f"FAIL {r['time_s']}s -- {r['error']}")
        if r.get("body"):
            print(f"       Body: {r['body'][:200]}")

    print()

    # FASE 3
    if not args.skip_codeos:
        print("=== FASE 3: Code OS end-to-end ===\n")

        print(f"  Health check {args.base_url}...", end=" ", flush=True)
        h = test_code_os_health(args.base_url)
        if h["ok"]:
            print(f"OK v{h['data'].get('version','?')}, tools={h['data'].get('tools','?')}")

            print(f"  Execute minimo...", end=" ", flush=True)
            r = test_code_os_simple(args.base_url)
            if r["ok"]:
                print(f"OK {r['time_s']}s")
            else:
                print(f"FAIL {r['time_s']}s -- {r.get('error','?')}")
                for evt in r.get("events", [])[:5]:
                    etype = evt.get("type", "?")
                    msg = evt.get("message", evt.get("summary", ""))[:100]
                    print(f"       [{etype}] {msg}")
        else:
            print(f"FAIL {h['error']}")

    # RESUMEN
    print()
    print("=== DIAGNOSTICO ===\n")

    if not all_ok:
        print("  ROJO: Fase 1 fallo -> PROBLEMA EN OpenRouter/API Key/Red")
        print("     Acciones:")
        print("     1. Verifica saldo en https://openrouter.ai/settings/credits")
        print("     2. Prueba regenerar API key")
        print("     3. Comprueba si OpenRouter reporta caida: https://status.openrouter.ai")
    else:
        print("  VERDE: Fase 1 OK -> OpenRouter funciona, modelos responden")
        print("     Si Code OS sigue fallando -> problema en el agente, no en los modelos")
        print("     Revisa logs: fly logs -a chief-os-omni --since 10m")
