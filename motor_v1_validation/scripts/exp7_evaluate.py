#!/usr/bin/env python3
"""EXP 7 — Evaluate Code OS on T1-T5.

Test A: Code OS tiered on T1-T5 (compare with Exp 6)
Test B: Code OS solo (single model) on T1, T4 with Devstral Small vs DeepSeek V3.2
"""

import os
import sys
import json
import time
import re
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

# Add agent dir to path
AGENT_DIR = str(Path(__file__).parent.parent / "agent")
sys.path.insert(0, AGENT_DIR)
from code_os import run_code_os, TIER_CONFIG

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
RESULTS_DIR = BASE_DIR / "results"
RESULTS_FILE = RESULTS_DIR / "exp7_results.json"

# ============================================================
# TASK SPECS (same as Exp 5/6)
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
# INDEPENDENT TEST RUNNER (same as Exp 6)
# ============================================================

def run_tests_in_sandbox(sandbox_dir: str, language: str) -> dict:
    """Run tests independently to verify agent's work."""
    if language in ("python", "sql"):
        test_file = os.path.join(sandbox_dir, "test_solution.py")
        if not os.path.exists(test_file):
            return {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0, "output": "No test file found"}
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True, text=True, timeout=60, cwd=sandbox_dir
            )
            output = (result.stdout + "\n" + result.stderr)[-4000:]
            m = re.search(r'(\d+) passed', output)
            passed = int(m.group(1)) if m else 0
            m = re.search(r'(\d+) failed', output)
            failed = int(m.group(1)) if m else 0
            m = re.search(r'(\d+) error', output)
            errors = int(m.group(1)) if m else 0
            total = passed + failed + errors
            if total == 0:
                total = 1
            return {
                "passed": passed, "failed": failed, "errors": errors,
                "total": total, "pass_rate": round(passed / total, 3),
                "output": output
            }
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "total": 1, "pass_rate": 0.0, "output": "TIMEOUT"}
        except Exception as e:
            return {"passed": 0, "failed": 0, "total": 1, "pass_rate": 0.0, "output": str(e)}

    elif language == "typescript":
        test_file = os.path.join(sandbox_dir, "test_solution.ts")
        if not os.path.exists(test_file):
            test_file = os.path.join(sandbox_dir, "solution_test.ts")
            if not os.path.exists(test_file):
                return {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0, "output": "No test file found"}
        try:
            result = subprocess.run(
                ['deno', 'test', '--allow-all', test_file],
                capture_output=True, text=True, timeout=60, cwd=sandbox_dir
            )
            output = (result.stdout + "\n" + result.stderr)[-4000:]
            m = re.search(r'(\d+)\s+passed.*?(\d+)\s+failed', output, re.DOTALL)
            if m:
                passed, failed = int(m.group(1)), int(m.group(2))
            else:
                passed = output.count("... ok")
                failed = output.count("... FAILED")
            total = max(passed + failed, 1)
            return {
                "passed": passed, "failed": failed, "total": total,
                "pass_rate": round(passed / total, 3), "output": output
            }
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "total": 1, "pass_rate": 0.0, "output": "TIMEOUT"}
        except Exception as e:
            return {"passed": 0, "failed": 0, "total": 1, "pass_rate": 0.0, "output": str(e)}

    return {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0, "output": "Unknown language"}


# ============================================================
# EVALUATION
# ============================================================

def evaluate_task(task_id: str, strategy: str = "tiered",
                  forced_model: str = None, max_iter: int = 30,
                  verbose: bool = True) -> dict:
    """Run Code OS on one task and verify with independent test execution."""
    task = TASKS[task_id]
    spec = task["spec"]
    language = task["language"]
    name = task["name"]

    sandbox = tempfile.mkdtemp(prefix=f"exp7_{task_id}_{strategy}_")
    label = forced_model.split("/")[-1] if forced_model else strategy

    print(f"  [{task_id}] {name} ({label})", end="", flush=True)

    start = time.time()
    agent_result = run_code_os(
        goal=spec,
        mode="goal",
        strategy=strategy,
        forced_model=forced_model,
        max_iterations=max_iter,
        sandbox_dir=sandbox,
        verbose=verbose,
    )
    elapsed = time.time() - start

    # Run tests independently
    test_result = run_tests_in_sandbox(sandbox, language)

    print(f" → {test_result['passed']}/{test_result['total']} ({agent_result['stop_reason']}) "
          f"${agent_result['cost_usd']:.4f} {elapsed:.0f}s")

    return {
        "task": task_id,
        "task_name": name,
        "language": language,
        "strategy": strategy,
        "model": forced_model or "tiered",
        "agent_result": {
            "stop_reason": agent_result["stop_reason"],
            "iterations": agent_result["iterations"],
            "tokens_used": agent_result["tokens_used"],
            "cost_usd": agent_result["cost_usd"],
            "time_s": round(elapsed, 1),
            "model_used": agent_result["model_used"],
            "session_id": agent_result.get("session_id", ""),
        },
        "tests": {
            "passed": test_result["passed"],
            "total": test_result["total"],
            "pass_rate": test_result["pass_rate"],
        },
        "sandbox": sandbox,
        "timestamp": datetime.now().isoformat(),
    }


def load_results() -> list:
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return []


def save_results(results: list):
    RESULTS_FILE.write_text(json.dumps(results, indent=2))


def is_done(results: list, task_id: str, strategy: str, model: str = None) -> bool:
    for r in results:
        if r["task"] == task_id and r["strategy"] == strategy:
            if model and r.get("model") != model:
                continue
            return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="EXP 7 — Evaluate Code OS")
    parser.add_argument("--test", choices=["A", "B", "all"], default="all")
    parser.add_argument("--task", help="Run only this task (T1-T5)")
    parser.add_argument("--max-iter", type=int, default=30)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Skip already done")
    args = parser.parse_args()

    results = load_results() if args.resume else []

    print("=" * 60)
    print("EXP 7 — Code OS Evaluation")
    print("=" * 60)

    # Test A: Code OS tiered on all 5 tasks
    if args.test in ("A", "all"):
        print("\n--- TEST A: Code OS tiered on T1-T5 ---")
        tasks = [args.task] if args.task else ["T1", "T2", "T3", "T4", "T5"]
        for tid in tasks:
            if args.resume and is_done(results, tid, "tiered"):
                print(f"  [{tid}] already done, skipping")
                continue
            r = evaluate_task(tid, strategy="tiered", max_iter=args.max_iter,
                            verbose=args.verbose)
            results.append(r)
            save_results(results)

    # Test B: Code OS solo on T1, T4 with different models
    if args.test in ("B", "all"):
        print("\n--- TEST B: Code OS solo (single model) ---")
        test_b_tasks = [args.task] if args.task else ["T1", "T4"]
        test_b_models = [
            TIER_CONFIG["tier1"],   # Devstral Small
            TIER_CONFIG["tier2"],   # DeepSeek V3.2
        ]
        for tid in test_b_tasks:
            for model in test_b_models:
                if args.resume and is_done(results, tid, "solo", model):
                    print(f"  [{tid}] {model.split('/')[-1]} already done, skipping")
                    continue
                r = evaluate_task(tid, strategy="solo", forced_model=model,
                                max_iter=args.max_iter, verbose=args.verbose)
                results.append(r)
                save_results(results)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Test A summary
    test_a = [r for r in results if r["strategy"] == "tiered"]
    if test_a:
        print("\nTest A (Tiered routing):")
        total_cost = 0
        total_pass = 0
        for r in test_a:
            pr = r["tests"]["pass_rate"] * 100
            cost = r["agent_result"]["cost_usd"]
            total_cost += cost
            total_pass += (1 if r["tests"]["pass_rate"] > 0.5 else 0)
            t = r["agent_result"]["time_s"]
            iters = r["agent_result"]["iterations"]
            model = r["agent_result"].get("model_used", "tiered").split("/")[-1]
            print(f"  {r['task']}: {pr:5.1f}% ({r['tests']['passed']}/{r['tests']['total']}) "
                  f"— ${cost:.4f} — {t:.0f}s — {iters} iters — {r['agent_result']['stop_reason']} [{model}]")
        avg_pass = total_pass / len(test_a) * 100 if test_a else 0
        print(f"  ---")
        print(f"  Total cost: ${total_cost:.4f}")
        print(f"  Task pass rate: {total_pass}/{len(test_a)} ({avg_pass:.0f}%)")

    # Test B summary
    test_b = [r for r in results if r["strategy"] == "solo"]
    if test_b:
        print("\nTest B (Solo models):")
        models_seen = list(dict.fromkeys(r.get("model", "") for r in test_b))
        for model in models_seen:
            model_results = [r for r in test_b if r.get("model") == model]
            if model_results:
                model_short = model.split("/")[-1] if "/" in model else model
                print(f"  {model_short}:")
                for r in model_results:
                    pr = r["tests"]["pass_rate"] * 100
                    print(f"    {r['task']}: {pr:5.1f}% ({r['tests']['passed']}/{r['tests']['total']}) "
                          f"— ${r['agent_result']['cost_usd']:.4f} — {r['agent_result']['time_s']:.0f}s "
                          f"— {r['agent_result']['stop_reason']}")

    save_results(results)
    print(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
