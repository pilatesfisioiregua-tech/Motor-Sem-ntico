#!/usr/bin/env python3
"""Test de Validación de Modelos — Post BRIEFING_06

Ejecuta 4 tests contra Code OS desplegado para verificar si los modelos OS
actuales son capaces con la infraestructura arreglada.

Uso:
  python3 test_validacion_modelos.py [--base-url URL]

Default: https://chief-os-omni.fly.dev
"""

import sys
import json
import time
import argparse
import urllib.request
import urllib.error
import datetime
import os
import tempfile

BASE_URL = "https://chief-os-omni.fly.dev"
RESULTS = []


def api(method, path, body=None, timeout=120):
    """Llamar a la API de Code OS."""
    url = BASE_URL.rstrip("/") + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}


def api_sse(path, body, timeout=300):
    """Llamar a endpoint SSE y recoger todos los eventos hasta 'done' o 'error'."""
    url = BASE_URL.rstrip("/") + path
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    events = []
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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
                                return events
                        except json.JSONDecodeError:
                            pass
    except Exception as e:
        events.append({"type": "error", "message": str(e)})
    return events


def record(test_name, passed, iterations, time_s, errors, notes=""):
    RESULTS.append({
        "test": test_name,
        "passed": passed,
        "iterations": iterations,
        "time_s": round(time_s, 1),
        "errors": errors,
        "notes": notes,
    })
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{'='*60}")
    print(f"{status} — {test_name}")
    print(f"  Iteraciones: {iterations} | Tiempo: {time_s:.1f}s | Errores: {errors}")
    if notes:
        print(f"  Notas: {notes}")
    print(f"{'='*60}\n")


# ══════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════
def check_health():
    print(f"Verificando salud de Code OS en {BASE_URL}...")
    d = api("GET", "/health")
    if d.get("status") == "ok":
        print(f"  ✓ Healthy — version {d.get('version', '?')}, tools: {d.get('tools', '?')}")
        return True
    else:
        print(f"  ✗ No healthy: {d}")
        return False


# ══════════════════════════════════════════
# TEST 1: QUICK — Rename simple
# ══════════════════════════════════════════
def test_1_quick():
    print("\n" + "─"*60)
    print("TEST 1: QUICK — Rename get_gestor → obtener_gestor")
    print("─"*60)

    t0 = time.time()

    # Verificar que /code-os/execute existe
    result = api_sse("/code-os/execute", {
        "input": (
            "En el archivo @project/core/gestor.py, busca la función get_gestor() "
            "(la que está al final del archivo, fuera de la clase). "
            "Solo dime en qué línea está y qué hace. NO modifiques nada."
        ),
        "mode": "auto",
    }, timeout=180)

    elapsed = time.time() - t0
    
    # Analizar resultado
    done_evt = next((e for e in result if e.get("type") == "done"), None)
    error_evt = next((e for e in result if e.get("type") == "error"), None)
    tool_calls = [e for e in result if e.get("type") == "tool_call"]
    n_errors = sum(1 for e in result if e.get("type") == "tool_result" and e.get("is_error"))

    if error_evt:
        record("T1 Quick (read+report)", False, len(tool_calls), elapsed, n_errors,
               f"Error: {error_evt.get('message', '?')[:200]}")
        return

    passed = done_evt is not None and len(tool_calls) <= 8
    notes = f"Tools: {[e.get('tool') for e in tool_calls[:5]]}"
    if done_evt:
        notes += f" | Summary: {done_evt.get('summary', '')[:100]}"

    record("T1 Quick (read+report)", passed, len(tool_calls), elapsed, n_errors, notes)


# ══════════════════════════════════════════
# TEST 2: ANÁLISIS — Listar métodos
# ══════════════════════════════════════════
def test_2_analysis():
    print("\n" + "─"*60)
    print("TEST 2: ANÁLISIS — Listar métodos de MotorVN")
    print("─"*60)

    t0 = time.time()

    result = api_sse("/code-os/execute", {
        "input": (
            "Lee el archivo @project/core/motor_vn.py y lista TODOS los métodos "
            "de la clase MotorVN. Solo los nombres, como lista. No modifiques nada."
        ),
        "mode": "auto",
    }, timeout=180)

    elapsed = time.time() - t0
    
    done_evt = next((e for e in result if e.get("type") == "done"), None)
    error_evt = next((e for e in result if e.get("type") == "error"), None)
    tool_calls = [e for e in result if e.get("type") == "tool_call"]
    text_evts = [e for e in result if e.get("type") == "text"]
    n_errors = sum(1 for e in result if e.get("type") == "tool_result" and e.get("is_error"))

    expected_methods = [
        "ejecutar", "_fase_compilacion", "_fase_ejecucion",
        "_llamar_llm", "_registrar", "_persistir_programa",
    ]

    # Check if the text output mentions the expected methods
    all_text = " ".join(e.get("content", "") for e in text_evts)
    if done_evt:
        all_text += " " + done_evt.get("summary", "")

    found = sum(1 for m in expected_methods if m in all_text)
    passed = found >= 4 and len(tool_calls) <= 12

    notes = f"Métodos encontrados: {found}/{len(expected_methods)}"
    if error_evt:
        notes += f" | Error: {error_evt.get('message', '')[:100]}"

    record("T2 Análisis (listar métodos)", passed, len(tool_calls), elapsed, n_errors, notes)


# ══════════════════════════════════════════
# TEST 3: EXECUTE — Crear endpoint
# ══════════════════════════════════════════
def test_3_execute():
    print("\n" + "─"*60)
    print("TEST 3: EXECUTE — Crear endpoint GET /test/ping")
    print("─"*60)

    t0 = time.time()

    result = api_sse("/code-os/execute", {
        "input": (
            "Añade un endpoint GET /test/ping en @project/api.py que devuelva "
            '{"status": "pong", "timestamp": <ISO timestamp actual>, "version": "3.4.0"}. '
            "Usa datetime.datetime.now(datetime.timezone.utc).isoformat() para el timestamp. "
            "Añádelo cerca del endpoint /health. Verifica que el código compila."
        ),
        "mode": "auto",
    }, timeout=300)

    elapsed = time.time() - t0
    
    done_evt = next((e for e in result if e.get("type") == "done"), None)
    error_evt = next((e for e in result if e.get("type") == "error"), None)
    tool_calls = [e for e in result if e.get("type") == "tool_call"]
    n_errors = sum(1 for e in result if e.get("type") == "tool_result" and e.get("is_error"))

    # Check if edit_file or write_file was used on api.py
    edit_calls = [e for e in tool_calls if e.get("tool") in ("edit_file", "write_file") 
                  and "api.py" in str(e.get("args", {}))]

    passed = done_evt is not None and len(edit_calls) > 0 and len(tool_calls) <= 20

    notes = f"Edit calls: {len(edit_calls)} | Total tools: {len(tool_calls)}"
    if error_evt:
        notes += f" | Error: {error_evt.get('message', '')[:100]}"

    record("T3 Execute (crear endpoint)", passed, len(tool_calls), elapsed, n_errors, notes)


# ══════════════════════════════════════════
# TEST 4: DEEP — Diagnosticar consistencia
# ══════════════════════════════════════════
def test_4_deep():
    print("\n" + "─"*60)
    print("TEST 4: DEEP — Diagnosticar /gestor/consistencia")
    print("─"*60)

    t0 = time.time()

    result = api_sse("/code-os/execute", {
        "input": (
            "Diagnostica por qué GET /gestor/consistencia reporta consistente=false. "
            "Usa http_request para llamar al endpoint, analiza la respuesta, "
            "identifica las causas específicas, y propón acciones concretas para cada una. "
            "NO apliques cambios — solo diagnostica y reporta."
        ),
        "mode": "auto",
    }, timeout=300)

    elapsed = time.time() - t0
    
    done_evt = next((e for e in result if e.get("type") == "done"), None)
    error_evt = next((e for e in result if e.get("type") == "error"), None)
    tool_calls = [e for e in result if e.get("type") == "tool_call"]
    text_evts = [e for e in result if e.get("type") == "text"]
    n_errors = sum(1 for e in result if e.get("type") == "tool_result" and e.get("is_error"))

    # Check if http_request was called
    http_calls = [e for e in tool_calls if e.get("tool") == "http_request"]
    
    all_text = " ".join(e.get("content", "") for e in text_evts)
    if done_evt:
        all_text += " " + done_evt.get("summary", "")

    # Should mention at least 2 of: programas, modelos, datapoints, huérfanos, inactivos
    diagnosis_keywords = ["programa", "modelo", "datapoint", "huérfano", "inactiv", "inconsist"]
    found_keywords = sum(1 for kw in diagnosis_keywords if kw in all_text.lower())

    passed = (done_evt is not None and len(http_calls) >= 1 
              and found_keywords >= 2 and len(tool_calls) <= 30)

    notes = f"HTTP calls: {len(http_calls)} | Keywords diagnóstico: {found_keywords}/6"
    if error_evt:
        notes += f" | Error: {error_evt.get('message', '')[:100]}"

    record("T4 Deep (diagnóstico)", passed, len(tool_calls), elapsed, n_errors, notes)


# ══════════════════════════════════════════
# RESUMEN
# ══════════════════════════════════════════
def print_summary():
    print("\n" + "═"*60)
    print("RESUMEN — Test de Validación de Modelos Post BRIEFING_06")
    print("═"*60)
    
    print(f"\n{'Test':<35} {'Result':<8} {'Iters':<8} {'Time':<8} {'Errors':<8}")
    print("─"*70)
    for r in RESULTS:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"{r['test']:<35} {status:<8} {r['iterations']:<8} {r['time_s']:<8} {r['errors']:<8}")
    
    n_passed = sum(1 for r in RESULTS if r["passed"])
    n_total = len(RESULTS)
    
    print(f"\n{'─'*70}")
    print(f"Total: {n_passed}/{n_total} passed")
    
    # Diagnóstico
    t1_ok = RESULTS[0]["passed"] if len(RESULTS) > 0 else False
    t2_ok = RESULTS[1]["passed"] if len(RESULTS) > 1 else False
    t3_ok = RESULTS[2]["passed"] if len(RESULTS) > 2 else False
    t4_ok = RESULTS[3]["passed"] if len(RESULTS) > 3 else False
    
    print("\nDIAGNÓSTICO:")
    if not t1_ok or not t2_ok:
        print("  ❌ T1-T2 fallaron → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO")
    elif not t3_ok or not t4_ok:
        print("  ⚠️  T1-T2 pasan pero T3-T4 fallan → capacidad parcial → EVALUAR cambio de cerebro")
    else:
        print("  ✅ T1-T4 pasan → los modelos son capaces, el problema era la infraestructura")
    
    return RESULTS


def save_results(results, output_path):
    """Guardar resultados en markdown."""
    now = datetime.datetime.now().isoformat()[:19]
    md = f"# Test Validación Modelos — Post BRIEFING_06\n\n"
    md += f"Fecha: {now}\n"
    md += f"Base URL: {BASE_URL}\n\n"
    
    # Health
    h = api("GET", "/health")
    md += f"Version: {h.get('version', '?')}\n"
    md += f"Tools: {h.get('tools', '?')}\n\n"
    
    # Tier config
    md += "## Modelos en uso\n\n"
    try:
        v = api("GET", "/version")
        md += f"```json\n{json.dumps(v, indent=2, ensure_ascii=False)[:500]}\n```\n\n"
    except:
        pass
    
    md += "## Resultados\n\n"
    md += f"| Test | Resultado | Iteraciones | Tiempo | Errores | Notas |\n"
    md += f"|------|-----------|-------------|--------|---------|-------|\n"
    for r in results:
        status = "✅ PASS" if r["passed"] else "❌ FAIL"
        notes = r.get("notes", "")[:80].replace("|", "/")
        md += f"| {r['test']} | {status} | {r['iterations']} | {r['time_s']}s | {r['errors']} | {notes} |\n"
    
    n_passed = sum(1 for r in results if r["passed"])
    md += f"\n**Total: {n_passed}/{len(results)} passed**\n\n"
    
    # Diagnóstico
    t1_ok = results[0]["passed"] if len(results) > 0 else False
    t2_ok = results[1]["passed"] if len(results) > 1 else False
    t3_ok = results[2]["passed"] if len(results) > 2 else False
    t4_ok = results[3]["passed"] if len(results) > 3 else False
    
    md += "## Diagnóstico\n\n"
    if not t1_ok or not t2_ok:
        md += "**❌ T1-T2 fallaron** → el cerebro no sirve ni para tareas básicas → CAMBIAR MODELO\n"
    elif not t3_ok or not t4_ok:
        md += "**⚠️ T1-T2 pasan pero T3-T4 fallan** → capacidad parcial → EVALUAR cambio de cerebro\n"
    else:
        md += "**✅ T1-T4 pasan** → los modelos son capaces, el problema era la infraestructura\n"
    
    md += "\n## Detalle por test\n\n"
    for r in results:
        md += f"### {r['test']}\n"
        md += f"- Resultado: {'PASS' if r['passed'] else 'FAIL'}\n"
        md += f"- Iteraciones: {r['iterations']}\n"
        md += f"- Tiempo: {r['time_s']}s\n"
        md += f"- Errores: {r['errors']}\n"
        md += f"- Notas: {r.get('notes', '')}\n\n"
    
    with open(output_path, "w") as f:
        f.write(md)
    print(f"\nResultados guardados en: {output_path}")


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test de validación de modelos Code OS")
    parser.add_argument("--base-url", default=BASE_URL, help="URL base de Code OS")
    parser.add_argument("--output", default=None, help="Path para guardar resultados (.md)")
    parser.add_argument("--test", type=int, default=0, help="Ejecutar solo test N (1-4), 0=todos")
    args = parser.parse_args()
    
    BASE_URL = args.base_url
    
    print(f"╔══════════════════════════════════════════════════╗")
    print(f"║  TEST VALIDACIÓN MODELOS — Post BRIEFING_06     ║")
    print(f"║  Target: {BASE_URL:<40}║")
    print(f"╚══════════════════════════════════════════════════╝")
    
    if not check_health():
        print("\n⛔ Code OS no está healthy. Abortando tests.")
        sys.exit(1)
    
    tests = {1: test_1_quick, 2: test_2_analysis, 3: test_3_execute, 4: test_4_deep}
    
    if args.test > 0:
        if args.test in tests:
            tests[args.test]()
        else:
            print(f"Test {args.test} no existe. Disponibles: 1-4")
            sys.exit(1)
    else:
        for t in [test_1_quick, test_2_analysis, test_3_execute, test_4_deep]:
            try:
                t()
            except Exception as e:
                print(f"\n⛔ Test falló con excepción: {e}")
                RESULTS.append({"test": t.__name__, "passed": False, 
                               "iterations": 0, "time_s": 0, "errors": 1, 
                               "notes": f"Exception: {e}"})
    
    results = print_summary()
    
    output = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 
        "..", "results", "test_modelos_post_b06.md"
    )
    save_results(results, output)
