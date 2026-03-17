#!/usr/bin/env python3
"""EXP 5 — Cadena de Montaje: Assembly Line Pipeline
8 configs x 5 tasks = 40 runs. Tests ejecutados realmente con pytest/deno.
API calls via subprocess+curl (urllib bloqueado por Cloudflare).
"""

import os
import sys
import json
import time
import re
import tempfile
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ============================================================
# PATHS & ENV
# ============================================================

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


load_env()
TOGETHER_KEY = os.environ.get("TOGETHER_API_KEY", "")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# ============================================================
# MODELS (14 verified)
# ============================================================

MODELS = {
    "qwen3-coder-480b": {
        "provider": "together", "model_id": "Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8",
        "cost_per_m_out": 2.00, "timeout": 180,
    },
    "qwen3-coder-next": {
        "provider": "together", "model_id": "Qwen/Qwen3-Coder-Next-FP8",
        "cost_per_m_out": 1.20, "timeout": 120,
    },
    "deepseek-v3.2": {
        "provider": "deepseek", "model_id": "deepseek-chat",
        "cost_per_m_out": 1.10, "timeout": 120,
    },
    "deepseek-reasoner": {
        "provider": "deepseek", "model_id": "deepseek-reasoner",
        "cost_per_m_out": 2.19, "timeout": 180,
    },
    "glm-5": {
        "provider": "together", "model_id": "zai-org/GLM-5",
        "cost_per_m_out": 3.20, "timeout": 240,
    },
    "cogito-671b": {
        "provider": "together", "model_id": "deepcogito/cogito-v2-1-671b",
        "cost_per_m_out": 1.25, "timeout": 180,
    },
    "gpt-oss-120b": {
        "provider": "together", "model_id": "openai/gpt-oss-120b",
        "cost_per_m_out": 0.60, "timeout": 120,
    },
    "gpt-oss-20b": {
        "provider": "together", "model_id": "openai/gpt-oss-20b",
        "cost_per_m_out": 0.20, "timeout": 90,
    },
    "minimax-m2.5": {
        "provider": "together", "model_id": "MiniMaxAI/MiniMax-M2.5",
        "cost_per_m_out": 1.20, "timeout": 120,
    },
    "qwen3-235b-instruct": {
        "provider": "together", "model_id": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
        "cost_per_m_out": 0.60, "timeout": 120,
    },
    "qwen3-235b-thinking": {
        "provider": "together", "model_id": "Qwen/Qwen3-235B-A22B-Thinking-2507",
        "cost_per_m_out": 3.00, "timeout": 180,
    },
    "qwen3-next-80b": {
        "provider": "together", "model_id": "Qwen/Qwen3-Next-80B-A3B-Instruct",
        "cost_per_m_out": 1.50, "timeout": 120,
    },
    "llama4-maverick": {
        "provider": "together", "model_id": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "cost_per_m_out": 0.85, "timeout": 120,
    },
    "deepseek-v3.1": {
        "provider": "together", "model_id": "deepseek-ai/DeepSeek-V3.1",
        "cost_per_m_out": 1.70, "timeout": 120,
    },
}

# ============================================================
# TASK SPECS
# ============================================================

SPEC_T1 = (
    'Implementa una Edge Function en TypeScript (Deno style) para un agente "detector-anomalias" que:\n'
    '1. Recibe POST con JSON: { trigger: "cron" | "manual", sesion_id?: string }\n'
    '2. Lee datos de una tabla `metricas` (simula con array in-memory):\n'
    '   - Cada metrica tiene: { agente: string, evento: string, latencia_ms: number, coste: number, error: boolean, timestamp: string }\n'
    '3. Calcula baselines por agente (ultimas 100 entradas):\n'
    '   - media, p50, p95, stddev de latencia\n'
    '   - error_rate (errores / total)\n'
    '4. Detecta anomalias con 3 reglas:\n'
    '   - Latencia: p50 ultimas 10 > p95 del baseline * 1.5\n'
    '   - Errores: error_rate ultimas 10 > error_rate baseline * 2\n'
    '   - Coste: coste medio ultimas 10 > coste medio baseline * 1.5\n'
    '5. Retorna JSON: { ok: true, anomalias: [...], agentes_analizados: N, timestamp: ISO }\n'
    '6. Si no hay anomalias: { ok: true, anomalias: [], ... }\n'
    '7. Manejo de errores: si la tabla esta vacia o el input es invalido, retorna { ok: false, error: "mensaje descriptivo" }\n'
    '\n'
    'Para testing: incluye datos mock (al menos 5 agentes, 200 metricas) que generen al menos 1 anomalia detectable por cada regla.\n'
    'Lenguaje: TypeScript. Tests: ejecutables con Deno.test.\n'
    'El archivo principal se llamara solution.ts. Los tests deben importar desde "./solution.ts".'
)

SPEC_T2 = (
    'Genera un script SQL completo (PostgreSQL) que:\n'
    '1. Crea tabla reglas_deteccion: id SERIAL PRIMARY KEY, nombre TEXT NOT NULL UNIQUE, '
    'tipo TEXT NOT NULL CHECK (tipo IN (\'latencia\', \'errores\', \'coste\', \'volumen\')), '
    'condicion JSONB NOT NULL, prioridad INT DEFAULT 0, activa BOOLEAN DEFAULT true, '
    'created_at TIMESTAMPTZ DEFAULT now(), updated_at TIMESTAMPTZ DEFAULT now()\n'
    '2. Crea tabla alertas_generadas: id SERIAL PRIMARY KEY, regla_id INT REFERENCES reglas_deteccion(id) ON DELETE CASCADE, '
    'agente TEXT NOT NULL, valor_detectado NUMERIC NOT NULL, valor_baseline NUMERIC NOT NULL, metadata JSONB, '
    'created_at TIMESTAMPTZ DEFAULT now(), INDEX en (agente, created_at DESC), INDEX en (regla_id)\n'
    '3. Crea funcion trigger_updated_at() que actualiza updated_at en UPDATE\n'
    '4. Crea trigger en reglas_deteccion que llama a trigger_updated_at()\n'
    '5. Seed: inserta 5 reglas de ejemplo (1 por tipo + 1 desactivada)\n'
    '6. Crea vista materializada resumen_alertas_diario: agrupa alertas por agente x regla x dia\n'
    '7. Script de rollback que deshace todo en orden correcto\n'
    '\n'
    'El archivo se llamara solution.sql. Incluye TODO en un solo archivo: migracion + seed + rollback (separados con comentarios).\n'
    'Los tests seran un archivo Python (test_solution.py) que lee solution.sql como texto y valida:\n'
    '- Que contiene CREATE TABLE para ambas tablas\n- Que tiene los CHECK constraints\n'
    '- Que define la funcion trigger\n- Que el seed inserta 5 reglas\n'
    '- Que tiene la vista materializada\n- Que el rollback existe y tiene DROP en orden correcto'
)

SPEC_T3 = (
    'Escribe un script Python solution.py que:\n'
    '1. Tiene una funcion analyze(data: dict) -> dict que recibe un JSON con estructura:\n'
    '   evaluaciones -> modelo -> output -> celdas -> celda_name -> {nivel: int, evidencia: str}\n'
    '   Hay 12 modelos, 5 outputs, 21 celdas (3 lentes x 7 funciones).\n'
    '   Lentes: Salud, Sentido, Continuidad. Funciones: Conservar, Captar, Depurar, Distribuir, Frontera, Adaptar, Replicar.\n'
    '2. Calcula por modelo: media de nivel, celdas con nivel >= 3, distribucion de niveles, tiempo total y medio\n'
    '3. Calcula acuerdo inter-evaluador: varianza por output x celda, celdas de alto desacuerdo (std > 1.0), '
    'correlacion de Spearman entre cada par de modelos\n'
    '4. Detecta sesgos: media global, delta de cada modelo vs media, clasifica INFLA (>+0.15), DEFLA (<-0.15), neutro\n'
    '5. Output: retorna dict con model_stats, agreement, biases\n'
    '6. Tiene funcion generate_synthetic_data() que genera datos sinteticos (12 modelos x 5 outputs x 21 celdas) con valores conocidos\n'
    '\n'
    'Tests: deben importar desde solution y verificar analisis contra datos sinteticos con valores conocidos.'
)

SPEC_T4 = (
    'Implementa un orquestador Python en solution.py con:\n'
    '1. Clase MultiModelOrchestrator: constructor recibe lista de configs de modelos\n'
    '   Cada config es dict con keys: name, provider, model_id, api_key_env, max_retries, timeout_s\n'
    '2. Metodo async run_parallel(prompt, models) -> dict: envia a N modelos en paralelo (asyncio), '
    'retry con backoff exponencial (1s, 2s, 4s), timeout por modelo. '
    'Retorna dict modelo -> {response, tokens, time_s, cost, error}\n'
    '3. Metodo async run_chain(steps) -> dict: ejecuta modelos en secuencia, output anterior es input siguiente. '
    'Cada step: dict con model, prompt_template (usa {previous_output}), parse_json. '
    'Si parse_json=True, parsea JSON del output (limpia backticks).\n'
    '4. Metodo async run_consensus(prompt, models, threshold) -> dict: envia a N, compara por campo, '
    'retorna respuesta consensuada + campos con desacuerdo\n'
    '5. Manejo robusto: API keys de env vars, JSON truncado cleanup (strip backticks, cerrar brackets), rate limiting\n'
    '6. Logging: cada llamada registra modelo, tokens, latencia, coste, error\n'
    '\n'
    'NO necesita API keys reales. Tests deben importar desde solution. '
    'Usa mocks (unittest.mock) para simular: respuestas exitosas, errores (timeout, 429, 500), JSON truncado. '
    'Unitarios para cada metodo + integracion con mocks.'
)

SPEC_T5 = (
    'Implementa un pipeline Python en solution.py que:\n'
    '1. Clase AssemblyLine: constructor recibe configs de modelos + configs de estaciones. '
    'Cada estacion es dict con name, model, prompt_template.\n'
    '2. Metodo run_task(spec) -> dict: ejecuta 5 estaciones en secuencia. '
    'Despues de estacion "tester": ejecuta tests con subprocess (pytest, timeout 30s). '
    'Pasa resultado de tests a estacion "reviewer". Despues de reviewer y optimizer: re-ejecuta tests.\n'
    '3. Metodo run_batch(tasks, configs) -> dict: ejecuta multiples tareas x configs, '
    'paraleliza por config (ThreadPoolExecutor).\n'
    '4. Metodo generate_report(results) -> str: tabla exito por config x tarea, pass rate, delta revisor, coste y tiempo.\n'
    '5. Metodo cleanup(): borra archivos temporales, deja solo reports.\n'
    '\n'
    'Tests deben importar desde solution. Usa mocks de llamadas LLM. '
    'Los mocks devuelven codigo Python predefinido que puede o no pasar tests. '
    'Verifica: estacion que genera syntax error, tests fallidos corregidos por revisor, timeout, cleanup completo.'
)

TASKS = {
    "T1": {"name": "Edge Function TS", "language": "typescript", "spec": SPEC_T1},
    "T2": {"name": "Migration SQL", "language": "sql", "spec": SPEC_T2},
    "T3": {"name": "Analysis Script", "language": "python", "spec": SPEC_T3},
    "T4": {"name": "Orchestrator", "language": "python", "spec": SPEC_T4},
    "T5": {"name": "Assembly Line", "language": "python", "spec": SPEC_T5},
}

# ============================================================
# CONFIGS (8)
# ============================================================

CONFIGS = {
    "0": {
        "name": "Baseline", "type": "baseline", "model": "qwen3-coder-480b",
    },
    "A": {
        "name": "Linea Industrial",
        "architect": "deepseek-v3.2", "implementer": "qwen3-coder-480b",
        "tester": "minimax-m2.5", "debugger1": "deepseek-reasoner",
        "debugger2": "cogito-671b", "reviewer": "glm-5",
        "optimizer": "qwen3-235b-instruct",
    },
    "B": {
        "name": "Coder Puro",
        "architect": "deepseek-v3.2", "implementer": "qwen3-coder-480b",
        "tester": "minimax-m2.5", "debugger1": "qwen3-coder-next",
        "reviewer": "deepseek-v3.1", "optimizer": "qwen3-next-80b",
    },
    "C": {
        "name": "Maxima Diversidad",
        "architect": "glm-5", "implementer": "qwen3-coder-480b",
        "tester": "minimax-m2.5", "debugger1": "deepseek-reasoner",
        "debugger2": "cogito-671b", "reviewer": "llama4-maverick",
        "optimizer": "gpt-oss-120b",
    },
    "D": {
        "name": "Ultra-Barato",
        "architect": "gpt-oss-20b", "implementer": "qwen3-235b-instruct",
        "tester": "gpt-oss-120b", "debugger1": "qwen3-coder-next",
        "reviewer": "llama4-maverick",
    },
    "E": {
        "name": "Premium",
        "architect": "glm-5", "implementer": "qwen3-coder-480b",
        "tester": "qwen3-235b-thinking", "debugger1": "deepseek-reasoner",
        "debugger2": "cogito-671b", "reviewer": "deepseek-v3.1",
        "optimizer": "deepseek-v3.2",
    },
    "F": {
        "name": "Cadena Minima",
        "implementer": "qwen3-coder-480b", "tester": "deepseek-reasoner",
        "debugger1": "qwen3-next-80b", "reviewer": "cogito-671b",
    },
    "G": {
        "name": "Razonadores",
        "architect": "qwen3-235b-thinking", "implementer": "deepseek-reasoner",
        "tester": "cogito-671b", "debugger1": "deepseek-v3.2",
        "debugger2": "qwen3-coder-480b", "reviewer": "qwen3-235b-thinking",
        "optimizer": "gpt-oss-120b",
    },
}

# ============================================================
# PROMPT SYSTEMS
# ============================================================

SYS_BASELINE = "Eres un programador experto. Genera codigo que funcione a la primera."
SYS_ARCHITECT = "Eres un arquitecto de software senior. Disenas ESTRUCTURA, no implementas."
SYS_IMPLEMENTER = "Eres un programador experto. Recibes un esqueleto ya disenado. Implementa la logica respetando la estructura exacta."
SYS_IMPLEMENTER_DIRECT = "Eres un programador experto. Genera codigo completo y funcional."
SYS_TESTER = "Eres un QA engineer. Genera tests EXHAUSTIVOS para el codigo recibido."
SYS_DEBUGGER = (
    "Eres un code reviewer senior. Corriges SOLO el codigo, NUNCA los tests.\n"
    "REGLAS ESTRICTAS:\n"
    "- SOLO modifica el codigo, NUNCA los tests\n"
    "- Si un test parece incorrecto, reportalo pero NO lo cambies\n"
    "- Si todos los tests pasan, devuelve el codigo sin cambios"
)
SYS_REVIEWER = "Eres un ingeniero senior. Revisa calidad, seguridad y edge cases del codigo."
SYS_REVIEW_OPTIMIZE = "Eres un ingeniero senior. Revisa calidad, seguridad, edge cases Y optimiza en una sola pasada."
SYS_OPTIMIZER = "Eres un ingeniero senior. El codigo funciona. Optimiza sin romper nada."

# ============================================================
# API: curl-based calls (Cloudflare blocks urllib/requests)
# ============================================================


def _curl_post(url, headers, body, timeout=120):
    """POST via curl subprocess. Returns (response_dict, error_str)."""
    tmp = None
    try:
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(body, tmp)
        tmp.close()
        cmd = ['curl', '-s', '--max-time', str(timeout), '-X', 'POST', url]
        for k, v in headers.items():
            cmd += ['-H', '%s: %s' % (k, v)]
        cmd += ['-d', '@' + tmp.name]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
        os.unlink(tmp.name)
        if result.returncode != 0:
            return None, "curl rc=%d: %s" % (result.returncode, result.stderr[:200])
        if not result.stdout.strip():
            return None, "empty response"
        data = json.loads(result.stdout)
        if "error" in data:
            return None, "API error: %s" % str(data["error"])[:200]
        return data, None
    except subprocess.TimeoutExpired:
        if tmp and os.path.exists(tmp.name):
            os.unlink(tmp.name)
        return None, "curl timeout"
    except json.JSONDecodeError as e:
        return None, "JSON decode: %s" % str(e)[:100]
    except Exception as e:
        if tmp and os.path.exists(tmp.name):
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
        return None, str(e)[:200]


def call_together(model_id, system, user, timeout=120):
    """Call Together API. Returns (content, tokens_out, elapsed, error)."""
    body = {
        "model": model_id,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": 16000, "temperature": 0.3,
    }
    headers = {"Authorization": "Bearer " + TOGETHER_KEY, "Content-Type": "application/json"}
    t0 = time.time()
    data, err = _curl_post("https://api.together.xyz/v1/chat/completions", headers, body, timeout)
    elapsed = round(time.time() - t0, 2)
    if err:
        return None, 0, elapsed, err
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return content, tokens, elapsed, None


def call_deepseek(model_id, system, user, timeout=180):
    """Call DeepSeek API. Returns (content, tokens_out, elapsed, error)."""
    body = {
        "model": model_id,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "max_tokens": 8192,
    }
    if model_id != "deepseek-reasoner":
        body["temperature"] = 0.3
    headers = {"Authorization": "Bearer " + DEEPSEEK_KEY, "Content-Type": "application/json"}
    t0 = time.time()
    data, err = _curl_post("https://api.deepseek.com/chat/completions", headers, body, timeout)
    elapsed = round(time.time() - t0, 2)
    if err:
        return None, 0, elapsed, err
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    reasoning = msg.get("reasoning_content", "") or ""
    if not content.strip() and reasoning.strip():
        content = reasoning
    tokens = data.get("usage", {}).get("completion_tokens", 0)
    return content, tokens, elapsed, None


def call_model(model_name, system, user):
    """Dispatch to provider. Returns (content, tokens_out, elapsed, error)."""
    cfg = MODELS[model_name]
    provider = cfg["provider"]
    model_id = cfg["model_id"]
    timeout = cfg["timeout"]
    if provider == "together":
        return call_together(model_id, system, user, timeout)
    elif provider == "deepseek":
        return call_deepseek(model_id, system, user, timeout)
    return None, 0, 0, "unknown provider: " + provider

# ============================================================
# CODE EXTRACTION
# ============================================================


def strip_think(text):
    """Strip <think>...</think> tags from reasoning models."""
    if not text:
        return ""
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()


def extract_code_block(text, lang=None):
    """Extract code from markdown code blocks. Returns largest match."""
    text = strip_think(text)
    if not text:
        return ""
    patterns = []
    if lang:
        patterns.append(r'```' + re.escape(lang) + r'\s*\n(.*?)```')
    patterns.append(r'```\w*\s*\n(.*?)```')
    for pat in patterns:
        matches = re.findall(pat, text, re.DOTALL)
        if matches:
            return max(matches, key=len).strip()
    # No code blocks — return raw text (might be code without fences)
    return text.strip()


def extract_sections(text, section_names):
    """Extract named sections: ### SECTION_NAME ###"""
    text = strip_think(text)
    sections = {}
    for i, name in enumerate(section_names):
        pat = r'###\s*' + re.escape(name) + r'\s*###\s*\n(.*?)'
        if i < len(section_names) - 1:
            pat += r'(?=###\s*' + re.escape(section_names[i + 1]) + r'\s*###)'
        else:
            pat += r'$'
        m = re.search(pat, text, re.DOTALL | re.IGNORECASE)
        if m:
            sections[name] = extract_code_block(m.group(1))
        else:
            sections[name] = ""
    return sections

# ============================================================
# TEST EXECUTION
# ============================================================


def get_filenames(language):
    if language == "typescript":
        return "solution.ts", "solution_test.ts"
    elif language == "sql":
        return "solution.sql", "test_solution.py"
    else:
        return "solution.py", "test_solution.py"


def _run_pytest(test_path, workdir, timeout=60):
    """Run pytest. Returns result dict."""
    try:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(workdir)
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', str(test_path), '-v', '--tb=short', '-x'],
            capture_output=True, text=True, timeout=timeout, cwd=str(workdir), env=env,
        )
        output = (result.stdout + "\n" + result.stderr)[-4000:]
        passed = len(re.findall(r' PASSED', output))
        failed = len(re.findall(r' FAILED', output))
        errors = len(re.findall(r' ERROR', output))
        total = passed + failed + errors
        return {
            "passed": passed, "failed": failed, "errors": errors, "total": max(total, 1),
            "output": output, "returncode": result.returncode,
            "pass_rate": round(passed / max(total, 1), 3),
        }
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "errors": 1, "total": 1,
                "output": "TIMEOUT after %ds" % timeout, "returncode": -1, "pass_rate": 0.0}
    except Exception as e:
        return {"passed": 0, "failed": 0, "errors": 1, "total": 1,
                "output": str(e)[:500], "returncode": -1, "pass_rate": 0.0}


def _run_deno_test(test_path, workdir, timeout=60):
    """Run deno test. Returns result dict."""
    try:
        result = subprocess.run(
            ['deno', 'test', '--allow-all', str(test_path)],
            capture_output=True, text=True, timeout=timeout, cwd=str(workdir),
        )
        output = (result.stdout + "\n" + result.stderr)[-4000:]
        # Parse deno output: "X passed | Y failed"
        m = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed', output, re.DOTALL)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
        else:
            passed = output.count("... ok")
            failed = output.count("... FAILED")
        total = max(passed + failed, 1)
        return {
            "passed": passed, "failed": failed, "errors": 0, "total": total,
            "output": output, "returncode": result.returncode,
            "pass_rate": round(passed / total, 3),
        }
    except subprocess.TimeoutExpired:
        return {"passed": 0, "failed": 0, "errors": 1, "total": 1,
                "output": "TIMEOUT after %ds" % timeout, "returncode": -1, "pass_rate": 0.0}
    except Exception as e:
        return {"passed": 0, "failed": 0, "errors": 1, "total": 1,
                "output": str(e)[:500], "returncode": -1, "pass_rate": 0.0}


def write_and_run_tests(language, code, tests, workdir, timeout=60):
    """Write code + tests to workdir, run tests, return results."""
    code_file, test_file = get_filenames(language)
    code_path = os.path.join(workdir, code_file)
    test_path = os.path.join(workdir, test_file)
    with open(code_path, 'w') as f:
        f.write(code)
    with open(test_path, 'w') as f:
        f.write(tests)
    if language == "typescript":
        return _run_deno_test(test_path, workdir, timeout)
    else:
        return _run_pytest(test_path, workdir, timeout)

# ============================================================
# PROMPT BUILDERS
# ============================================================


def build_baseline_user(spec):
    return (
        "TAREA:\n" + spec + "\n\n"
        "Genera:\n1. Codigo completo y funcional\n"
        "2. Suite de tests exhaustiva\n\n"
        "Responde con DOS bloques claramente separados:\n"
        "### CODE ###\n(codigo completo)\n"
        "### TESTS ###\n(tests completos)"
    )


def build_architect_user(spec):
    return (
        "TAREA:\n" + spec + "\n\n"
        "Genera el esqueleto:\n"
        "1. Clases con nombres, atributos, type hints\n"
        "2. Funciones/metodos con firma completa + docstrings\n"
        "3. Cuerpo = `pass` o `...` (NO implementes logica)\n"
        "4. Imports necesarios\n5. Constantes y configuracion\n\n"
        "Codigo debe pasar syntax check limpio. Responde SOLO con codigo."
    )


def build_implementer_user(spec, skeleton):
    return (
        "TAREA ORIGINAL:\n" + spec + "\n\n"
        "ESQUELETO:\n" + skeleton + "\n\n"
        "Implementa donde hay `pass` o `...`. NO cambies interfaces (nombres, tipos, parametros). "
        "Responde SOLO con codigo completo."
    )


def build_implementer_direct_user(spec):
    return (
        "TAREA:\n" + spec + "\n\n"
        "Implementa codigo completo y funcional. Responde SOLO con codigo."
    )


def build_tester_user(spec, code, language):
    framework = "Deno.test" if language == "typescript" else "pytest"
    import_note = ""
    if language == "typescript":
        import_note = "Los tests deben importar desde './solution.ts'."
    elif language == "sql":
        import_note = "Los tests son Python (pytest) que leen solution.sql como texto y validan su estructura."
    else:
        import_note = "Los tests deben importar desde solution (from solution import ...)."
    return (
        "TAREA ORIGINAL:\n" + spec + "\n\n"
        "CODIGO:\n" + code + "\n\n"
        "Genera tests (" + framework + "):\n"
        "1. Unitarios para cada funcion/metodo publico\n"
        "2. Edge cases: vacios, None, extremos, tipos incorrectos\n"
        "3. Integracion: flujos end-to-end\n"
        "4. Negativos: errores esperados\n"
        "5. Minimo 15 tests. Minimo 3 edge cases por funcion principal.\n\n"
        + import_note + "\n"
        "Responde SOLO con codigo de tests ejecutable."
    )


def build_debugger_user(spec, code, tests, test_output):
    return (
        "TAREA:\n" + spec + "\n\n"
        "CODIGO:\n" + code + "\n\n"
        "TESTS:\n" + tests + "\n\n"
        "RESULTADO DE TESTS:\n" + test_output[-3000:] + "\n\n"
        "Para cada test que falla, identifica la causa en el codigo y corrige.\n"
        "SOLO modifica el codigo, NUNCA los tests.\n\n"
        "Responde:\n### CODIGO CORREGIDO ###\n(codigo completo)\n"
        "### INFORME ###\n- Bugs encontrados: ...\n- Cambios realizados: ..."
    )


def build_reviewer_user(spec, code, tests):
    return (
        "TAREA ORIGINAL:\n" + spec + "\n\n"
        "CODIGO:\n" + code + "\n\n"
        "TESTS (deben seguir pasando):\n" + tests + "\n\n"
        "Revisa calidad, seguridad, edge cases. Corrige lo que encuentres.\n\n"
        "Responde:\n### CODIGO REVISADO ###\n(codigo completo corregido)\n"
        "### ISSUES ###\n- Issues encontrados: ..."
    )


def build_review_optimize_user(spec, code, tests):
    return (
        "TAREA ORIGINAL:\n" + spec + "\n\n"
        "CODIGO:\n" + code + "\n\n"
        "TESTS (deben seguir pasando):\n" + tests + "\n\n"
        "Revisa calidad, seguridad, edge cases. Optimiza legibilidad, DRY, rendimiento.\n"
        "NO cambies interfaz publica. Responde SOLO con codigo final optimizado."
    )


def build_optimizer_user(code, tests):
    return (
        "CODIGO:\n" + code + "\n\n"
        "TESTS (deben seguir pasando):\n" + tests + "\n\n"
        "Optimiza legibilidad, DRY, rendimiento. NO cambies interfaz publica.\n"
        "Responde SOLO con codigo optimizado."
    )

# ============================================================
# ASSEMBLY LINE
# ============================================================


def _lang_for_extract(language):
    if language == "typescript":
        return "typescript"
    elif language == "sql":
        return "sql"
    return "python"


def run_baseline(config, task_name, workdir):
    """Config 0: single model generates code + tests."""
    task = TASKS[task_name]
    spec = task["spec"]
    language = task["language"]
    model = config["model"]

    print("  [BASELINE] %s..." % model, end="", flush=True)
    content, tokens, elapsed, error = call_model(model, SYS_BASELINE, build_baseline_user(spec))

    station = {"station": "baseline", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
    if error:
        print(" FAIL (%s)" % error[:60])
        return {"stations": [station], "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

    sections = extract_sections(content, ["CODE", "TESTS"])
    code = sections.get("CODE", "")
    tests = sections.get("TESTS", "")
    if not code:
        code = extract_code_block(content, _lang_for_extract(language))
    if not tests:
        # Try to split by any remaining separator
        tests = ""

    station["syntax_ok"] = bool(code.strip())
    station["has_tests"] = bool(tests.strip())

    if not code.strip() or not tests.strip():
        print(" NO CODE/TESTS")
        return {"stations": [station], "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

    test_result = write_and_run_tests(language, code, tests, workdir)
    station["tests"] = "%d/%d" % (test_result["passed"], test_result["total"])
    print(" %d/%d (%.1fs)" % (test_result["passed"], test_result["total"], elapsed))
    return {
        "stations": [station],
        "final": {"tests_total": test_result["total"], "tests_passed": test_result["passed"],
                  "pass_rate": test_result["pass_rate"]},
    }


def run_pipeline(config_name, task_name, workdir):
    """Run assembly line for one (config, task)."""
    config = CONFIGS[config_name]
    task = TASKS[task_name]
    spec = task["spec"]
    language = task["language"]
    lang_ext = _lang_for_extract(language)
    stations = []
    code = ""
    tests = ""
    test_output_text = ""

    # --- E1: ARCHITECT ---
    if config.get("architect"):
        model = config["architect"]
        print("  [ARCHITECT] %s..." % model, end="", flush=True)
        content, tokens, elapsed, error = call_model(model, SYS_ARCHITECT, build_architect_user(spec))
        st = {"station": "architect", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
        if error:
            print(" FAIL (%s)" % error[:60])
            stations.append(st)
            return {"stations": stations, "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}
        code = extract_code_block(content, lang_ext)
        st["syntax_ok"] = bool(code.strip())
        stations.append(st)
        print(" OK (%.1fs, %d tok)" % (elapsed, tokens))

    # --- E2: IMPLEMENTER ---
    model = config["implementer"]
    print("  [IMPLEMENTER] %s..." % model, end="", flush=True)
    if config.get("architect"):
        user_prompt = build_implementer_user(spec, code)
        sys_prompt = SYS_IMPLEMENTER
    else:
        user_prompt = build_implementer_direct_user(spec)
        sys_prompt = SYS_IMPLEMENTER_DIRECT
    content, tokens, elapsed, error = call_model(model, sys_prompt, user_prompt)
    st = {"station": "implementer", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
    if error:
        print(" FAIL (%s)" % error[:60])
        stations.append(st)
        return {"stations": stations, "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}
    code = extract_code_block(content, lang_ext)
    st["syntax_ok"] = bool(code.strip())
    stations.append(st)
    print(" OK (%.1fs, %d tok)" % (elapsed, tokens))

    if not code.strip():
        print("  [!] No code generated, aborting")
        return {"stations": stations, "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

    # --- E3: TESTER ---
    model = config["tester"]
    print("  [TESTER] %s..." % model, end="", flush=True)
    content, tokens, elapsed, error = call_model(
        model, SYS_TESTER, build_tester_user(spec, code, language))
    st = {"station": "tester", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
    if error:
        print(" FAIL (%s)" % error[:60])
        stations.append(st)
        return {"stations": stations, "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

    if language == "sql":
        tests = extract_code_block(content, "python")
    else:
        tests = extract_code_block(content, lang_ext)
    st["has_tests"] = bool(tests.strip())
    stations.append(st)

    if not tests.strip():
        print(" NO TESTS")
        return {"stations": stations, "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

    # Run tests after E3
    test_result = write_and_run_tests(language, code, tests, workdir)
    st["tests_after"] = "%d/%d" % (test_result["passed"], test_result["total"])
    test_output_text = test_result["output"]
    print(" %d/%d (%.1fs)" % (test_result["passed"], test_result["total"], elapsed))

    # --- E4: DEBUGGER R1 ---
    if test_result["pass_rate"] < 1.0 and config.get("debugger1"):
        model = config["debugger1"]
        print("  [DEBUGGER-R1] %s..." % model, end="", flush=True)
        content, tokens, elapsed, error = call_model(
            model, SYS_DEBUGGER, build_debugger_user(spec, code, tests, test_output_text))
        st = {"station": "debugger1", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
        if not error:
            secs = extract_sections(content, ["CODIGO CORREGIDO", "INFORME"])
            new_code = secs.get("CODIGO CORREGIDO", "")
            if not new_code:
                new_code = extract_code_block(content, lang_ext)
            if new_code.strip():
                code = new_code
            # Re-run tests
            test_result = write_and_run_tests(language, code, tests, workdir)
            st["tests_after"] = "%d/%d" % (test_result["passed"], test_result["total"])
            test_output_text = test_result["output"]
            print(" %d/%d (%.1fs)" % (test_result["passed"], test_result["total"], elapsed))
        else:
            print(" FAIL (%s)" % error[:60])
        stations.append(st)

    # --- E4b: DEBUGGER R2 ---
    if test_result["pass_rate"] < 1.0 and config.get("debugger2"):
        model = config["debugger2"]
        print("  [DEBUGGER-R2] %s..." % model, end="", flush=True)
        content, tokens, elapsed, error = call_model(
            model, SYS_DEBUGGER, build_debugger_user(spec, code, tests, test_output_text))
        st = {"station": "debugger2", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
        if not error:
            secs = extract_sections(content, ["CODIGO CORREGIDO", "INFORME"])
            new_code = secs.get("CODIGO CORREGIDO", "")
            if not new_code:
                new_code = extract_code_block(content, lang_ext)
            if new_code.strip():
                code = new_code
            test_result = write_and_run_tests(language, code, tests, workdir)
            st["tests_after"] = "%d/%d" % (test_result["passed"], test_result["total"])
            test_output_text = test_result["output"]
            print(" %d/%d (%.1fs)" % (test_result["passed"], test_result["total"], elapsed))
        else:
            print(" FAIL (%s)" % error[:60])
        stations.append(st)

    # --- E5: REVIEWER / E5+E6: REVIEW+OPTIMIZE ---
    if config.get("reviewer"):
        has_optimizer = bool(config.get("optimizer"))
        model = config["reviewer"]
        label = "REVIEWER" if has_optimizer else "REVIEW+OPT"
        print("  [%s] %s..." % (label, model), end="", flush=True)

        if has_optimizer:
            sys_p, user_p = SYS_REVIEWER, build_reviewer_user(spec, code, tests)
        else:
            sys_p, user_p = SYS_REVIEW_OPTIMIZE, build_review_optimize_user(spec, code, tests)

        content, tokens, elapsed, error = call_model(model, sys_p, user_p)
        st = {"station": "reviewer" if has_optimizer else "review_optimize",
              "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
        if not error:
            if has_optimizer:
                secs = extract_sections(content, ["CODIGO REVISADO", "ISSUES"])
                new_code = secs.get("CODIGO REVISADO", "")
            else:
                new_code = extract_code_block(content, lang_ext)
            if new_code.strip():
                code = new_code
            print(" OK (%.1fs)" % elapsed)
        else:
            print(" FAIL (%s)" % error[:60])
        stations.append(st)

    # --- E6: OPTIMIZER ---
    if config.get("optimizer"):
        model = config["optimizer"]
        print("  [OPTIMIZER] %s..." % model, end="", flush=True)
        content, tokens, elapsed, error = call_model(
            model, SYS_OPTIMIZER, build_optimizer_user(code, tests))
        st = {"station": "optimizer", "model": model, "time_s": elapsed, "tokens_out": tokens, "error": error}
        if not error:
            new_code = extract_code_block(content, lang_ext)
            if new_code.strip():
                code = new_code
            print(" OK (%.1fs)" % elapsed)
        else:
            print(" FAIL (%s)" % error[:60])
        stations.append(st)

    # --- FINAL TESTS ---
    print("  [FINAL TESTS]", end=" ", flush=True)
    test_result = write_and_run_tests(language, code, tests, workdir)
    print("%d/%d (%.1f%%)" % (test_result["passed"], test_result["total"],
                               test_result["pass_rate"] * 100))

    return {
        "stations": stations,
        "final": {
            "tests_total": test_result["total"],
            "tests_passed": test_result["passed"],
            "pass_rate": test_result["pass_rate"],
        },
    }


# ============================================================
# VERIFY MODELS
# ============================================================


def verify_models():
    """Verify all models respond to a trivial prompt."""
    print("Verifying %d models...\n" % len(MODELS))
    ok_count = 0
    for name, cfg in sorted(MODELS.items()):
        print("  %-25s " % name, end="", flush=True)
        content, tokens, elapsed, error = call_model(name, "respond with OK", "say OK")
        if error:
            print("FAIL (%.1fs) %s" % (elapsed, error[:80]))
        else:
            preview = strip_think(content)[:40].replace("\n", " ")
            print("OK   (%.1fs) %s" % (elapsed, preview))
            ok_count += 1
    print("\n%d/%d models available" % (ok_count, len(MODELS)))
    return ok_count


# ============================================================
# MAIN
# ============================================================


def main():
    parser = argparse.ArgumentParser(description="EXP 5 — Cadena de Montaje")
    parser.add_argument('--verify', action='store_true', help='Only verify models')
    parser.add_argument('--config', type=str, help='Run specific config (0,A,B,C,D,E,F,G)')
    parser.add_argument('--task', type=str, help='Run specific task (T1-T5)')
    parser.add_argument('--resume', type=str, help='Resume from results file')
    args = parser.parse_args()

    if args.verify:
        verify_models()
        return

    configs_to_run = [args.config] if args.config else list(CONFIGS.keys())
    tasks_to_run = [args.task] if args.task else list(TASKS.keys())

    # Load existing results if resuming
    results = []
    if args.resume and os.path.exists(args.resume):
        with open(args.resume) as f:
            results = json.load(f)
    done = set((r["config"], r["task"]) for r in results)
    results_path = str(RESULTS_DIR / "exp5_results.json")

    print("=" * 60)
    print("EXP 5 — CADENA DE MONTAJE")
    print("Configs: %s | Tasks: %s" % (", ".join(configs_to_run), ", ".join(tasks_to_run)))
    print("=" * 60)

    for config_name in configs_to_run:
        config = CONFIGS[config_name]
        print("\n" + "=" * 60)
        print("CONFIG %s: %s" % (config_name, config["name"]))
        if config.get("type") != "baseline":
            station_models = []
            for key in ["architect", "implementer", "tester", "debugger1", "debugger2", "reviewer", "optimizer"]:
                if config.get(key):
                    station_models.append("%s=%s" % (key[:4], config[key]))
            print("  " + " | ".join(station_models))
        print("=" * 60)

        for task_name in tasks_to_run:
            if (config_name, task_name) in done:
                print("\n  %s — already done, skipping" % task_name)
                continue

            task = TASKS[task_name]
            print("\n  --- %s: %s (%s) ---" % (task_name, task["name"], task["language"]))

            workdir = tempfile.mkdtemp(prefix="exp5_%s_%s_" % (config_name, task_name))

            try:
                if config.get("type") == "baseline":
                    result_data = run_baseline(config, task_name, workdir)
                else:
                    result_data = run_pipeline(config_name, task_name, workdir)
            except Exception as e:
                print("  [ERROR] %s" % str(e)[:200])
                result_data = {"stations": [], "final": {"tests_total": 0, "tests_passed": 0, "pass_rate": 0.0}}

            # Calculate cost
            total_cost = 0.0
            total_time = 0.0
            for st in result_data.get("stations", []):
                tok = st.get("tokens_out", 0)
                m = st.get("model", "")
                if m in MODELS:
                    total_cost += tok * MODELS[m]["cost_per_m_out"] / 1_000_000
                total_time += st.get("time_s", 0)

            record = {
                "config": config_name,
                "config_name": config["name"],
                "task": task_name,
                "task_name": task["name"],
                "language": task["language"],
                "stations": result_data.get("stations", []),
                "final": result_data.get("final", {}),
                "total_cost_usd": round(total_cost, 5),
                "total_time_s": round(total_time, 1),
                "timestamp": datetime.now().isoformat(),
            }
            results.append(record)

            # Save incrementally
            with open(results_path, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            final = record["final"]
            print("  RESULT: %d/%d (%.0f%%) — $%.4f — %.1fs" % (
                final.get("tests_passed", 0), final.get("tests_total", 0),
                final.get("pass_rate", 0) * 100, total_cost, total_time))

            # Cleanup workdir
            shutil.rmtree(workdir, ignore_errors=True)

    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for config_name in configs_to_run:
        config_results = [r for r in results if r["config"] == config_name]
        if not config_results:
            continue
        rates = [r["final"].get("pass_rate", 0) for r in config_results]
        avg_rate = sum(rates) / len(rates) if rates else 0
        total_cost = sum(r.get("total_cost_usd", 0) for r in config_results)
        print("  Config %s (%s): avg pass_rate=%.0f%%, total_cost=$%.4f" % (
            config_name, CONFIGS[config_name]["name"], avg_rate * 100, total_cost))

    print("\nResults saved to %s" % results_path)


if __name__ == "__main__":
    main()
