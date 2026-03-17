#!/usr/bin/env python3
"""EXP 5b — ¿Los modelos nuevos resuelven T1 y T4?

Pipeline multi-estación con 3 configs de modelos nuevos.
T1: Edge Function TypeScript (Deno). T4: Orquestador async (Python).
API calls via subprocess+curl (Cloudflare bloquea urllib/requests).
"""

import json
import os
import sys
import time
import subprocess
import tempfile
import re
import argparse
import shutil
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
RESULTS_DIR = Path("results")
RESULTS_FILE = RESULTS_DIR / "exp5b_results.json"
REPORT_FILE = RESULTS_DIR / "exp5b_report.md"
DELAY = 2  # seconds between API calls

CONFIGS = {
    "N1_top": {
        "name": "Nuevos Top (7 estaciones)",
        "stations": {
            "E1": "stepfun/step-3.5-flash",
            "E2": "mistralai/devstral-2512",
            "E3": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            "E4": "stepfun/step-3.5-flash",
            "E4b": "xiaomi/mimo-v2-flash",
            "E4c": "stepfun/step-3.5-flash",
            "E5": "qwen/qwen3.5-397b-a17b",
            "E6": "xiaomi/mimo-v2-flash",
        },
    },
    "N2_cheap": {
        "name": "Ultra-Barato Nuevos (5 estaciones)",
        "stations": {
            "E1": "xiaomi/mimo-v2-flash",
            "E2": "xiaomi/mimo-v2-flash",
            "E3": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            "E4": "stepfun/step-3.5-flash",
            "E4b": "stepfun/step-3.5-flash",
            "E4c": "stepfun/step-3.5-flash",
            "E5": "xiaomi/mimo-v2-flash",
            "E6": "xiaomi/mimo-v2-flash",
        },
    },
    "N3_coding": {
        "name": "Coding Specialists (5 estaciones)",
        "stations": {
            "E1": "stepfun/step-3.5-flash",
            "E2": "mistralai/devstral-2512",
            "E3": "mistralai/devstral-2512",
            "E4": "stepfun/step-3.5-flash",
            "E4b": "stepfun/step-3.5-flash",
            "E4c": "stepfun/step-3.5-flash",
            "E5": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
            "E6": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        },
    },
}

TASK_SPECS = {
    "T1": """Crea una Edge Function en TypeScript para Deno (serve API) que:

1. Endpoint POST /detect recibe JSON: { "metrics": [{"name": string, "value": number, "timestamp": string}], "thresholds": {"metric_name": {"warn": number, "critical": number}} }

2. Para cada métrica:
   - value > critical → status "critical"
   - value > warn → status "warn"
   - sin threshold definido → status "unknown"
   - value <= warn → status "ok"

3. Response JSON:
   {
     "alerts": [{"name": string, "value": number, "status": string, "threshold": number|null}],
     "summary": {"total": number, "critical": number, "warn": number, "ok": number, "unknown": number},
     "worst": string
   }

4. Errores: body vacío → 400, metrics no array → 400
5. CORS headers en todas las respuestas

Runtime: Deno 2.6.10. El código debe funcionar con `deno serve`.
Los tests deben usar `Deno.test()` y hacer fetch al handler directamente.
IMPORTANTE: No usar imports de node. Solo Deno APIs nativas.
Usa el patrón `export default { fetch(req: Request): Response | Promise<Response> { ... } }` para compatibilidad con deno serve y testing.""",

    "T4": """Crea un orquestador Python que:

1. Recibe una lista de tasks, cada una con: model_id, prompt, max_tokens
2. Ejecuta todas en paralelo vía asyncio + aiohttp a un endpoint configurable
3. Retry logic: max 3 intentos, backoff exponencial (1s, 2s, 4s)
4. Timeout por task: 60s
5. Si un task falla después de 3 retries: registrar error, no bloquear los demás
6. Resultado: lista de resultados con status (ok/error), response, latency_ms, retries_used

Interfaz:
  async def orchestrate(tasks: List[Task], endpoint: str, api_key: str) -> List[Result]

Incluye:
- Dataclasses para Task y Result
- Rate limiting: max 5 requests concurrentes (semáforo)
- Logging de cada retry
- Tests con pytest usando unittest.mock para mockear aiohttp.ClientSession

IMPORTANTE: Los tests NO deben hacer llamadas reales a APIs. Usar unittest.mock.
Runtime: Python 3.9.6 (usar typing.List, typing.Optional, NO usar X | Y syntax).
pytest como test runner. Usar pytest-asyncio para tests async.""",
}

# ═══════════════════════════════════════════════════════════════════════════════
# API
# ═══════════════════════════════════════════════════════════════════════════════

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks. If all content was inside, return last block."""
    stripped = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if stripped:
        return stripped
    blocks = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if blocks:
        return blocks[-1].strip()
    # Handle unclosed <think> tag (model hit max_tokens mid-thinking)
    if "<think>" in text:
        after = text.split("<think>")[-1].strip()
        if after:
            return after
    return text.strip()


def call_model(model_id: str, prompt: str, max_tokens: int = 16384,
               temperature: float = 0.2, timeout: int = 240) -> Dict:
    """Call OpenRouter via subprocess+curl."""
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY not set", "text": ""}

    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    })

    tmpfile = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(body)
            tmpfile = f.name

        t0 = time.time()
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), ENDPOINT,
             "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
             "-H", "HTTP-Referer: https://omni-mind.app",
             "-H", "X-Title: OMNI-MIND Exp5b",
             "-H", "Content-Type: application/json",
             "-d", f"@{tmpfile}"],
            capture_output=True, text=True, timeout=timeout + 15,
        )
        latency = time.time() - t0

        if not result.stdout.strip():
            return {"error": "empty response", "text": "", "latency_s": latency}

        resp = json.loads(result.stdout)
        if "error" in resp:
            return {"error": str(resp["error"]), "text": "", "latency_s": latency}

        choices = resp.get("choices", [])
        if not choices:
            return {"error": "no choices", "text": "", "latency_s": latency}

        text = choices[0].get("message", {}).get("content", "") or ""
        text = strip_think_tags(text)

        usage = resp.get("usage", {})
        return {
            "text": text,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "latency_s": round(latency, 2),
        }
    except subprocess.TimeoutExpired:
        return {"error": f"timeout {timeout}s", "text": "", "latency_s": timeout}
    except Exception as e:
        return {"error": str(e), "text": "", "latency_s": 0}
    finally:
        if tmpfile and os.path.exists(tmpfile):
            os.unlink(tmpfile)


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

def extract_code(response: str, lang: str = "") -> str:
    """Extract code from model response (handles markdown code blocks)."""
    if not response:
        return ""
    patterns = [
        rf"```{lang}\s*\n(.*?)```",
        r"```\w+\s*\n(.*?)```",
        r"```\s*\n(.*?)```",
    ]
    for pat in patterns:
        matches = re.findall(pat, response, re.DOTALL)
        if matches:
            # Return the longest match (likely the main code)
            return max(matches, key=len).strip()
    # If no code block, check if response looks like code
    lines = response.strip().split("\n")
    code_indicators = ["import ", "export ", "def ", "class ", "function ", "async ",
                       "from ", "const ", "let ", "var ", "Deno.", "@dataclass"]
    if any(lines[0].strip().startswith(ind) for ind in code_indicators):
        return response.strip()
    return response.strip()


def fix_test_imports(test_code: str, task_id: str) -> str:
    """Fix import mismatches between generated tests and actual filenames."""
    if task_id == "T1":
        # Fix: any import from "./whatever.ts" → "./solution.ts"
        test_code = re.sub(
            r'from\s+["\']\.\/[^"\']+\.ts["\']',
            'from "./solution.ts"',
            test_code,
        )
        # Ensure Deno assert imports exist
        if "assert" in test_code and "from " not in test_code.split("Deno.test")[0]:
            # Check if assertEquals/assertExists etc. are used without import
            if re.search(r'\bassert\.\w+', test_code) and 'import' not in test_code.split('\n')[0]:
                assert_import = 'import { assert, assertEquals, assertExists } from "https://deno.land/std/assert/mod.ts";\n'
                test_code = assert_import + test_code
    else:  # T4
        # Fix: "from orchestrator.core import X" → "from orchestrator import X"
        # Fix: "from orchestrator.xxx import X" → "from orchestrator import X"
        test_code = re.sub(
            r'from\s+orchestrator\.\w+\s+import',
            'from orchestrator import',
            test_code,
        )
        # Fix: patch('orchestrator.core.X') → patch('orchestrator.X')
        test_code = re.sub(
            r"patch\(['\"]orchestrator\.\w+\.",
            "patch('orchestrator.",
            test_code,
        )
        # Ensure aiohttp is imported if referenced
        if 'aiohttp' in test_code and 'import aiohttp' not in test_code:
            test_code = 'import aiohttp\n' + test_code
        # Ensure pytest-asyncio marker is available
        if '@pytest.mark.asyncio' in test_code and 'import pytest' not in test_code:
            test_code = 'import pytest\n' + test_code
    return test_code


def syntax_check(code: str, task_id: str, workdir: str) -> Tuple[bool, str]:
    """Check syntax. Returns (ok, error_message)."""
    if not code.strip():
        return False, "Empty code"
    if task_id == "T1":
        filepath = os.path.join(workdir, "solution.ts")
        with open(filepath, "w") as f:
            f.write(code)
        r = subprocess.run(["deno", "check", filepath],
                           capture_output=True, text=True, timeout=30)
        return r.returncode == 0, (r.stderr + r.stdout)[:1000]
    else:  # T4
        try:
            import ast
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)


def run_tests(code: str, test_code: str, task_id: str, workdir: str) -> Dict:
    """Execute tests. Returns dict with passed, output, tests_passed, tests_total, pass_rate."""
    if task_id == "T1":
        return _run_deno_tests(code, test_code, workdir)
    else:
        return _run_pytest(code, test_code, workdir)


def _run_deno_tests(code: str, test_code: str, workdir: str) -> Dict:
    """Run Deno tests for T1."""
    sol_path = os.path.join(workdir, "solution.ts")
    test_path = os.path.join(workdir, "solution_test.ts")
    with open(sol_path, "w") as f:
        f.write(code)
    with open(test_path, "w") as f:
        f.write(test_code)

    try:
        r = subprocess.run(
            ["deno", "test", "--allow-net", "--allow-read", test_path],
            capture_output=True, text=True, timeout=60, cwd=workdir,
        )
        output = (r.stdout + "\n" + r.stderr).strip()

        # Parse: "ok | N passed | M failed" or "N passed" lines
        passed_m = re.search(r"(\d+)\s+passed", output)
        failed_m = re.search(r"(\d+)\s+failed", output)
        passed = int(passed_m.group(1)) if passed_m else 0
        failed = int(failed_m.group(1)) if failed_m else 0
        # Also count individual "... ok" and "... FAILED"
        if passed == 0 and failed == 0:
            passed = len(re.findall(r"\.\.\.\s+ok", output))
            failed = len(re.findall(r"\.\.\.\s+FAILED", output))

        total = passed + failed
        return {
            "passed": r.returncode == 0 and passed > 0,
            "output": output[:3000],
            "tests_passed": passed,
            "tests_total": total,
            "pass_rate": passed / max(1, total),
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "TIMEOUT", "tests_passed": 0,
                "tests_total": 0, "pass_rate": 0}
    except Exception as e:
        return {"passed": False, "output": str(e), "tests_passed": 0,
                "tests_total": 0, "pass_rate": 0}


def _run_pytest(code: str, test_code: str, workdir: str) -> Dict:
    """Run pytest for T4."""
    code_path = os.path.join(workdir, "orchestrator.py")
    test_path = os.path.join(workdir, "test_orchestrator.py")
    with open(code_path, "w") as f:
        f.write(code)
    with open(test_path, "w") as f:
        f.write(test_code)

    try:
        r = subprocess.run(
            ["python3", "-m", "pytest", test_path, "-v", "--tb=short", "-x"],
            capture_output=True, text=True, timeout=60, cwd=workdir,
            env={**os.environ, "PYTHONPATH": workdir},
        )
        output = (r.stdout + "\n" + r.stderr).strip()

        passed = len(re.findall(r"PASSED", output))
        failed = len(re.findall(r"FAILED", output))
        errors = len(re.findall(r"ERROR", output))
        total = passed + failed + errors
        return {
            "passed": r.returncode == 0 and passed > 0,
            "output": output[:3000],
            "tests_passed": passed,
            "tests_total": total,
            "pass_rate": passed / max(1, total),
        }
    except subprocess.TimeoutExpired:
        return {"passed": False, "output": "TIMEOUT", "tests_passed": 0,
                "tests_total": 0, "pass_rate": 0}
    except Exception as e:
        return {"passed": False, "output": str(e), "tests_passed": 0,
                "tests_total": 0, "pass_rate": 0}


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

def prompt_architect(spec: str, task_id: str) -> str:
    lang = "TypeScript/Deno" if task_id == "T1" else "Python 3.9"
    return f"""You are a senior software architect. Design the solution for this spec.

SPEC:
{spec}

Language: {lang}

Output a clear design with:
1. Module structure and key types (as code)
2. Function signatures with 1-line descriptions
3. Error handling strategy
4. Key implementation notes

Be specific and concrete. Include type definitions as code blocks."""


def prompt_implementer(spec: str, architecture: str, task_id: str) -> str:
    if task_id == "T1":
        lang_note = """Language: TypeScript for Deno 2.6.10.
FILENAME: solution.ts (IMPORTANT — tests will import from "./solution.ts")
Pattern: `export default { fetch(req: Request): Response | Promise<Response> { ... } }`
This pattern is required for `deno serve` AND for test imports.
Do NOT call Deno.serve() directly — use the export default pattern.
Do NOT import from node or npm. Only Deno native APIs."""
    else:
        lang_note = """Language: Python 3.9.6.
FILENAME: orchestrator.py (single flat file, NOT a package — no submodules)
Use `from typing import List, Optional, Dict` (NOT `list[X]` or `X | Y` syntax).
Use dataclasses. Use asyncio + aiohttp.
All async functions must use `async def`.
Export all public names (Task, Result, orchestrate) at module level."""

    return f"""You are an expert developer. Write the COMPLETE, working implementation.

SPEC:
{spec}

ARCHITECTURE:
{architecture}

{lang_note}

Output ONLY the code in a single code block. No explanation before or after.
The code must be complete and executable as-is."""


def prompt_tester(spec: str, code: str, task_id: str) -> str:
    if task_id == "T1":
        test_note = """Write Deno tests using Deno.test() API.
CRITICAL — use EXACTLY this import:
  import server from "./solution.ts";
  import { assertEquals } from "https://deno.land/std/assert/mod.ts";
Then call: `const res = await server.fetch(new Request(...))`
Test: valid POST, empty body (400), invalid metrics (400), unknown thresholds, CORS headers, worst calculation.
Do NOT start a real server. Import and call the handler directly."""
    else:
        test_note = """Write pytest tests with pytest-asyncio.
CRITICAL — use EXACTLY this import pattern:
  from orchestrator import orchestrate, Task, Result
  (orchestrator is a FLAT FILE, NOT a package — no orchestrator.core or submodules)
Use `@pytest.mark.asyncio` for async tests.
Mock aiohttp.ClientSession using unittest.mock.patch('orchestrator.aiohttp.ClientSession') or AsyncMock.
Test: successful orchestration, retry on failure, timeout, concurrent limiting, error handling.
Do NOT make real HTTP calls. All external calls must be mocked."""

    return f"""Write comprehensive tests for this implementation.

SPEC:
{spec}

IMPLEMENTATION:
```
{code}
```

{test_note}

Output ONLY the test code in a single code block. No explanation."""


def prompt_debugger(spec: str, code: str, test_code: str,
                    error_output: str, prev_errors: List[str], task_id: str) -> str:
    lang = "TypeScript/Deno" if task_id == "T1" else "Python 3.9"
    prev = ""
    if prev_errors:
        prev = "\n\nPREVIOUS DEBUG ATTEMPTS ALSO FAILED:\n"
        for i, e in enumerate(prev_errors, 1):
            prev += f"\n--- Attempt {i} errors ---\n{e[:800]}\n"

    return f"""Tests failed. Fix the implementation.

SPEC:
{spec}

LANGUAGE: {lang}

CURRENT CODE:
```
{code}
```

TEST CODE:
```
{test_code}
```

ERROR OUTPUT:
```
{error_output[:2000]}
```
{prev}

Analyze errors carefully. Fix ONLY the implementation code (not the tests).
Output the COMPLETE fixed code in a single code block. Not a diff — the full file."""


def prompt_reviewer(spec: str, code: str, task_id: str) -> str:
    return f"""Review this code for correctness, edge cases, and bugs.

SPEC:
{spec}

CODE:
```
{code}
```

If you find issues, fix them. Output the COMPLETE code (fixed or unchanged) in a single code block.
No explanation — just the code."""


def prompt_optimizer(code: str) -> str:
    return f"""Optimize this code for readability and performance. Do not change functionality.

CODE:
```
{code}
```

Output the optimized code in a single code block. No explanation."""


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(config_name: str, config: Dict, task_id: str) -> Dict:
    """Run the complete pipeline for one config × task."""
    spec = TASK_SPECS[task_id]
    stations = config["stations"]
    lang = "typescript" if task_id == "T1" else "python"

    workdir = tempfile.mkdtemp(prefix=f"exp5b_{config_name}_{task_id}_")
    log = []
    total_cost_tokens = 0
    t_start = time.time()

    def call_station(station: str, prompt: str) -> Dict:
        nonlocal total_cost_tokens
        model = stations[station]
        print(f"    [{station}] {model}...", end=" ", flush=True)
        time.sleep(DELAY)
        resp = call_model(model, prompt)
        if resp.get("error"):
            print(f"❌ {resp['error'][:60]}")
        else:
            toks = resp.get("tokens_out", 0)
            lat = resp.get("latency_s", 0)
            total_cost_tokens += resp.get("tokens_in", 0) + toks
            print(f"✅ {toks}tok {lat}s")
        log.append({"station": station, "model": model,
                     "latency_s": resp.get("latency_s", 0),
                     "tokens_out": resp.get("tokens_out", 0),
                     "error": resp.get("error")})
        return resp

    print(f"\n  ── {config_name} × {task_id} ──")

    # E1: Architect
    resp = call_station("E1", prompt_architect(spec, task_id))
    architecture = resp.get("text", "")
    if not architecture:
        return _fail_result(config_name, task_id, log, t_start, "E1 returned empty")

    # E2: Implementer
    resp = call_station("E2", prompt_implementer(spec, architecture, task_id))
    code = extract_code(resp.get("text", ""), lang)
    if not code:
        return _fail_result(config_name, task_id, log, t_start, "E2 returned no code")

    # Syntax Gate
    syn_ok, syn_err = syntax_check(code, task_id, workdir)
    if not syn_ok:
        print(f"    [SYNTAX] ❌ Asking E2 to fix...")
        fix_prompt = f"This code has syntax errors:\n```\n{syn_err[:1000]}\n```\n\nOriginal code:\n```\n{code}\n```\n\nFix all syntax errors. Output the COMPLETE fixed code."
        resp = call_station("E2", fix_prompt)
        code = extract_code(resp.get("text", ""), lang)
        syn_ok, syn_err = syntax_check(code, task_id, workdir)
        if not syn_ok:
            print(f"    [SYNTAX] ❌❌ Still broken: {syn_err[:100]}")
    if syn_ok:
        print(f"    [SYNTAX] ✅")

    # E3: Tester
    resp = call_station("E3", prompt_tester(spec, code, task_id))
    test_code = extract_code(resp.get("text", ""), lang)
    if not test_code:
        return _fail_result(config_name, task_id, log, t_start, "E3 returned no test code")

    # Auto-fix import mismatches
    test_code = fix_test_imports(test_code, task_id)
    print(f"    [IMPORT FIX] ✅ Applied")

    # Run Tests
    print(f"    [TEST]", end=" ", flush=True)
    test_result = run_tests(code, test_code, task_id, workdir)
    _print_test_result(test_result)

    # Debug loop (up to 3 rounds)
    prev_errors = []
    debug_stations = ["E4", "E4b", "E4c"]
    for i, dbg_station in enumerate(debug_stations):
        if test_result["passed"]:
            break
        prev_errors.append(test_result["output"][:1000])
        prompt = prompt_debugger(spec, code, test_code, test_result["output"],
                                 prev_errors[:-1], task_id)
        resp = call_station(dbg_station, prompt)
        new_code = extract_code(resp.get("text", ""), lang)
        if new_code:
            code = new_code
        # Syntax check
        syn_ok, syn_err = syntax_check(code, task_id, workdir)
        if not syn_ok:
            print(f"    [SYNTAX post-debug] ❌ {syn_err[:80]}")
        # Re-run tests
        print(f"    [TEST R{i+1}]", end=" ", flush=True)
        test_result = run_tests(code, test_code, task_id, workdir)
        _print_test_result(test_result)

    # Skip E5/E6 if tests already pass 100% — reviewer/optimizer can break working code
    if test_result["passed"] and test_result["pass_rate"] >= 1.0:
        print(f"    [SKIP E5+E6] ✅ Tests 100% — no tocar lo que funciona")
        final_result = test_result
    else:
        # E5: Reviewer
        resp = call_station("E5", prompt_reviewer(spec, code, task_id))
        reviewed = extract_code(resp.get("text", ""), lang)
        if reviewed and reviewed != code:
            code = reviewed
            print(f"    [E5] Code updated by reviewer")

        # E6: Optimizer
        resp = call_station("E6", prompt_optimizer(code))
        optimized = extract_code(resp.get("text", ""), lang)
        if optimized and optimized != code:
            code = optimized
            print(f"    [E6] Code optimized")

        # Final Tests
        print(f"    [FINAL TEST]", end=" ", flush=True)
        final_result = run_tests(code, test_code, task_id, workdir)
        _print_test_result(final_result)

    elapsed = time.time() - t_start

    # Save final artifacts
    artifacts_dir = RESULTS_DIR / f"{config_name}_{task_id}"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    fname = "solution.ts" if task_id == "T1" else "orchestrator.py"
    tname = "solution_test.ts" if task_id == "T1" else "test_orchestrator.py"
    with open(artifacts_dir / fname, "w") as f:
        f.write(code)
    with open(artifacts_dir / tname, "w") as f:
        f.write(test_code)

    # Cleanup
    shutil.rmtree(workdir, ignore_errors=True)

    return {
        "config": config_name,
        "task": task_id,
        "pass_rate": final_result["pass_rate"],
        "tests_passed": final_result["tests_passed"],
        "tests_total": final_result["tests_total"],
        "all_passed": final_result["passed"],
        "time_s": round(elapsed, 1),
        "total_tokens": total_cost_tokens,
        "stages": log,
        "debug_rounds_used": sum(1 for l in log if l["station"].startswith("E4")),
        "final_test_output": final_result["output"][:1500],
    }


def _fail_result(config_name, task_id, log, t_start, reason):
    return {
        "config": config_name, "task": task_id,
        "pass_rate": 0, "tests_passed": 0, "tests_total": 0,
        "all_passed": False, "time_s": round(time.time() - t_start, 1),
        "total_tokens": 0, "stages": log, "debug_rounds_used": 0,
        "error": reason, "final_test_output": reason,
    }


def _print_test_result(r: Dict):
    if r["passed"]:
        print(f"✅ {r['tests_passed']}/{r['tests_total']} passed")
    else:
        print(f"❌ {r['tests_passed']}/{r['tests_total']} passed")
        # Show first line of error
        first_err = r["output"].split("\n")[0][:80] if r["output"] else "unknown"
        print(f"      → {first_err}")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT
# ═══════════════════════════════════════════════════════════════════════════════

def run_experiment(config_filter: Optional[str] = None,
                   task_filter: Optional[str] = None):
    """Run the full experiment."""
    RESULTS_DIR.mkdir(exist_ok=True)

    configs = {k: v for k, v in CONFIGS.items()
               if config_filter is None or config_filter in k}
    tasks = [t for t in ["T1", "T4"]
             if task_filter is None or task_filter.upper() == t]

    if not configs or not tasks:
        print(f"❌ No matches. Configs: {list(CONFIGS.keys())}, Tasks: [T1, T4]")
        return

    total_runs = len(configs) * len(tasks)
    print(f"\n🚀 EXP 5b — {len(configs)} configs × {len(tasks)} tasks = {total_runs} pipeline runs\n")

    # Load existing results to merge (don't overwrite previous runs)
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            existing = json.load(f)
        results = existing.get("configs", {})
    else:
        results = {}

    for cfg_name, cfg in configs.items():
        if cfg_name not in results:
            results[cfg_name] = {}
        print(f"\n{'═' * 60}")
        print(f"  CONFIG: {cfg_name} — {cfg['name']}")
        print(f"{'═' * 60}")

        for task_id in tasks:
            # Skip if already completed
            if task_id in results[cfg_name] and results[cfg_name][task_id].get("tests_total", 0) > 0:
                pr = results[cfg_name][task_id].get("pass_rate", 0)
                print(f"\n  ⏭️  {cfg_name} × {task_id} already done ({pr*100:.0f}%)")
                continue

            result = run_pipeline(cfg_name, cfg, task_id)
            results[cfg_name][task_id] = result

            # Save incrementally
            _save_results(results)

    # Generate report
    _save_results(results)
    generate_report(results)

    print(f"\n{'═' * 60}")
    print(f"  ✅ COMPLETADO: {total_runs} pipeline runs")
    print(f"  📁 Results: {RESULTS_FILE}")
    print(f"  📄 Report:  {REPORT_FILE}")
    print(f"{'═' * 60}")


def _save_results(results: Dict):
    """Save results to JSON."""
    # Build comparison vs exp5
    best_t1 = max((r.get("T1", {}).get("pass_rate", 0) for r in results.values()), default=0)
    best_t4 = max((r.get("T4", {}).get("pass_rate", 0) for r in results.values()), default=0)

    data = {
        "experiment": "exp5b_new_models",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "configs": results,
        "comparison_vs_exp5": {
            "T1": {"exp5_best": 0, "exp5b_best": best_t1, "delta": best_t1},
            "T4": {"exp5_best": 0, "exp5b_best": best_t4, "delta": best_t4},
        },
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(results: Dict):
    """Generate markdown report."""
    lines = [
        "# EXP 5b — ¿Los modelos nuevos resuelven T1 y T4?",
        f"\n**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "**Provider:** OpenRouter",
        "",
        "## Tabla Principal: Config × Task",
        "",
        "| Config | T1 Edge Function | T4 Orquestador | Debug Rounds | Tiempo | Tokens |",
        "|--------|:---:|:---:|:---:|:---:|:---:|",
    ]

    for cfg_name, tasks in results.items():
        t1 = tasks.get("T1", {})
        t4 = tasks.get("T4", {})
        t1_str = _score_cell(t1)
        t4_str = _score_cell(t4)
        debug_t1 = t1.get("debug_rounds_used", "-")
        debug_t4 = t4.get("debug_rounds_used", "-")
        time_total = t1.get("time_s", 0) + t4.get("time_s", 0)
        tokens_total = t1.get("total_tokens", 0) + t4.get("total_tokens", 0)
        lines.append(f"| {cfg_name} | {t1_str} | {t4_str} | {debug_t1}/{debug_t4} | "
                     f"{time_total:.0f}s | {tokens_total:,} |")

    # Comparison vs Exp 5
    best_t1 = max((r.get("T1", {}).get("pass_rate", 0) for r in results.values()), default=0)
    best_t4 = max((r.get("T4", {}).get("pass_rate", 0) for r in results.values()), default=0)

    lines.extend([
        "",
        "## Comparativa con Exp 5",
        "",
        "| Task | Exp 5 Mejor | Exp 5b Mejor | Delta |",
        "|------|:---:|:---:|:---:|",
        f"| T1 Edge Function | 0% | **{best_t1*100:.0f}%** | +{best_t1*100:.0f}pp |",
        f"| T4 Orquestador | 0% | **{best_t4*100:.0f}%** | +{best_t4*100:.0f}pp |",
        "",
    ])

    # Verdict
    if best_t1 > 0.5 or best_t4 > 0.5:
        lines.append("### Veredicto: El problema ERA los modelos")
        lines.append("El pipeline funciona si eliges bien. No hace falta loop agéntico (Exp 6).")
    elif best_t1 > 0 or best_t4 > 0:
        lines.append("### Veredicto: Mejora parcial")
        lines.append("Los modelos nuevos ayudan pero el pipeline lineal sigue limitado. "
                     "Exp 6 (loop agéntico) puede ser necesario.")
    else:
        lines.append("### Veredicto: El problema es la ESTRUCTURA")
        lines.append("Ni con modelos top se resuelven T1/T4. "
                     "Confirma que Exp 6 (loop agéntico) es imprescindible.")

    # Station details
    lines.extend(["", "## Detalle por Config", ""])
    for cfg_name, tasks in results.items():
        lines.append(f"### {cfg_name}")
        for task_id in ["T1", "T4"]:
            t = tasks.get(task_id, {})
            if not t:
                continue
            lines.append(f"\n**{task_id}:** {t.get('tests_passed', 0)}/{t.get('tests_total', 0)} "
                         f"tests ({t.get('pass_rate', 0)*100:.0f}%) — "
                         f"{t.get('debug_rounds_used', 0)} debug rounds — "
                         f"{t.get('time_s', 0):.0f}s")
            if t.get("error"):
                lines.append(f"  Error: {t['error']}")
            # Station trace
            for s in t.get("stages", []):
                status = "✅" if not s.get("error") else "❌"
                lines.append(f"  {status} {s['station']:4s} {s['model']:45s} "
                             f"{s.get('tokens_out', 0):5d}tok {s.get('latency_s', 0):5.1f}s")

    lines.extend(["", "---",
                   f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"])

    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines))


def _score_cell(t: Dict) -> str:
    if not t:
        return "— ⚪"
    pr = t.get("pass_rate", 0)
    tp = t.get("tests_passed", 0)
    tt = t.get("tests_total", 0)
    if pr >= 0.8:
        return f"**{tp}/{tt}** ({pr*100:.0f}%) 🟢"
    elif pr >= 0.5:
        return f"{tp}/{tt} ({pr*100:.0f}%) 🟡"
    elif pr > 0:
        return f"{tp}/{tt} ({pr*100:.0f}%) 🔴"
    else:
        return f"0/{tt} (0%) ⚫"


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="EXP 5b — Modelos nuevos vs T1/T4")
    parser.add_argument("--config", type=str, help="Filter config (N1_top, N2_cheap, N3_coding)")
    parser.add_argument("--task", type=str, help="Filter task (T1, T4)")
    parser.add_argument("--verify", action="store_true", help="Verify models only")
    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("❌ Set OPENROUTER_API_KEY")
        sys.exit(1)

    # Check deps
    if not shutil.which("deno"):
        print("⚠️  deno not found — T1 tests will fail")

    print("=" * 60)
    print("  EXP 5b — ¿Los modelos nuevos resuelven T1 y T4?")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if args.verify:
        # Quick ping test
        seen = set()
        for cfg in CONFIGS.values():
            for model in cfg["stations"].values():
                if model in seen:
                    continue
                seen.add(model)
                r = call_model(model, "Say OK", max_tokens=10, timeout=15)
                status = "✅" if not r.get("error") else f"❌ {r['error'][:50]}"
                print(f"  {model:50s} {status}")
        return

    run_experiment(config_filter=args.config, task_filter=args.task)


if __name__ == "__main__":
    main()
