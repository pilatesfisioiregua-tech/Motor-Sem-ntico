#!/usr/bin/env python3
"""Comprehensive system test suite for Omni Mind v3 + Code OS v3.

Runs against a live deployment. Tests all subsystems:
- Health & infrastructure
- Motor Semántico (pipeline, signals, programs)
- Gestor GAMC (loop, salud, parameters, validation)
- Neural DB (search, stats, connections)
- Model Observatory (registry, discover, health)
- Tool Evolution (stats, rankings, gaps)
- Criticality Engine (temperature, avalanches, transitions)
- Information Theory (MI, entropy, redundancy)
- Metacognitive (FoK, JoL, Kalman)
- Predictive (trajectory, attractors)
- Game Theory (incentives, equilibria)
- CEO Advisor (scan, capabilities)
- Explorer (matrix, gaps, dimensions)
- Exocortex (tenants, stigmergy)
- Monitoring (dashboard, SLOs, budget, circuit breakers)

Usage:
    python3 tests/test_system.py [BASE_URL]
    python3 tests/test_system.py https://chief-os-omni.fly.dev
"""

import sys
import time
import json
import urllib.request
import urllib.error
import urllib.parse

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://chief-os-omni.fly.dev"

# Tracking
results = {"pass": 0, "fail": 0, "skip": 0, "errors": []}
start_time = time.time()


def test(name: str, method: str, path: str, body: dict = None,
         expect_status: int = 200, expect_keys: list = None,
         expect_value: dict = None, timeout: int = 30):
    """Run a single test against the API."""
    # URL-encode path for non-ASCII characters
    url = f"{BASE_URL}{urllib.parse.quote(path, safe='/:?=&')}"
    try:
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Content-Type": "application/json"} if data else {}
        )
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            raw = resp.read().decode()
            latency = int((time.time() - t0) * 1000)

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            result = {"_raw": raw[:500]}

        # Check status
        if status != expect_status:
            results["fail"] += 1
            results["errors"].append(f"{name}: expected {expect_status}, got {status}")
            print(f"  FAIL  {name} — status {status} (expected {expect_status})")
            return None

        # Check keys exist
        if expect_keys:
            missing = [k for k in expect_keys if k not in result]
            if missing:
                results["fail"] += 1
                results["errors"].append(f"{name}: missing keys {missing}")
                print(f"  FAIL  {name} — missing keys: {missing}")
                return result

        # Check specific values
        if expect_value:
            for k, v in expect_value.items():
                actual = result.get(k)
                if actual != v:
                    results["fail"] += 1
                    results["errors"].append(f"{name}: {k}={actual}, expected {v}")
                    print(f"  FAIL  {name} — {k}={actual} (expected {v})")
                    return result

        results["pass"] += 1
        print(f"  PASS  {name} ({latency}ms)")
        return result

    except urllib.error.HTTPError as e:
        if e.code == expect_status:
            results["pass"] += 1
            print(f"  PASS  {name} (expected {expect_status})")
            return None
        results["fail"] += 1
        body_text = ""
        try:
            body_text = e.read().decode()[:200]
        except Exception:
            pass
        results["errors"].append(f"{name}: HTTP {e.code} — {body_text}")
        print(f"  FAIL  {name} — HTTP {e.code}")
        return None
    except Exception as e:
        results["fail"] += 1
        results["errors"].append(f"{name}: {type(e).__name__}: {e}")
        print(f"  FAIL  {name} — {type(e).__name__}: {e}")
        return None


# ═══════════════════════════════════════════════
# 1. INFRASTRUCTURE
# ═══════════════════════════════════════════════
print("\n[1] INFRASTRUCTURE")
test("Health check", "GET", "/health",
     expect_keys=["status", "version", "tools"],
     expect_value={"status": "ok"})

test("Version endpoint", "GET", "/version",
     expect_keys=["version"])

test("API index", "GET", "/api/index",
     expect_keys=["endpoints"])

test("Dashboard serves HTML", "GET", "/dashboard",
     expect_status=200)


# ═══════════════════════════════════════════════
# 2. MOTOR SEMÁNTICO
# ═══════════════════════════════════════════════
print("\n[2] MOTOR SEMÁNTICO")

# Gradientes
test("Gradientes", "POST", "/gestor/gradientes",
     body={"input": "Mi socio quiere vender su parte"})

# Compilar programa
test("Compilar programa", "POST", "/gestor/compilar",
     body={"input": "Quiero comprar la parte de mi socio", "modo": "analisis"})

# Listar programas
test("Listar programas", "GET", "/gestor/programas")

# Señales PID (all)
test("Señales PID (todas)", "GET", "/motor/señales",
     expect_keys=["status"])

# Validar programa
test("Validar programa", "POST", "/gestor/validar-programa",
     body={"inteligencias": ["INT-14"]},
     expect_keys=["status", "valido"])

# Corregir programa
test("Corregir programa inválido", "POST", "/gestor/corregir-programa",
     body={"inteligencias": ["INT-14"]},
     expect_keys=["status"])

# Evaluar reglas
test("Evaluar reglas compilador", "POST", "/evaluar-reglas",
     body={"inteligencias": ["INT-01", "INT-07", "INT-08", "INT-16"]})


# ═══════════════════════════════════════════════
# 3. GESTOR GAMC
# ═══════════════════════════════════════════════
print("\n[3] GESTOR GAMC")

test("Gestor salud", "GET", "/gestor/salud",
     expect_keys=["status"])

test("Gestor parámetros", "GET", "/gestor/parametros",
     expect_keys=["status", "parametros"])

test("Gestor estado", "GET", "/gestor/estado",
     expect_keys=["status"])

test("Gestor flywheel", "GET", "/gestor/flywheel",
     expect_keys=["status"])

test("Gestor autopoiesis", "GET", "/gestor/autopoiesis",
     expect_keys=["status"])

test("Gestor log", "GET", "/gestor/log")

test("Gestor obsoletas", "GET", "/gestor/obsoletas")

test("Gestor contradicciones", "GET", "/gestor/contradicciones")

test("Gestor expiradas", "GET", "/gestor/expiradas")

test("Gestor consistencia", "GET", "/gestor/consistencia",
     expect_keys=["status"])


# ═══════════════════════════════════════════════
# 4. NEURAL DB
# ═══════════════════════════════════════════════
print("\n[4] NEURAL DB")

test("Neural search", "POST", "/neural/search",
     body={"query": "motor semántico", "limit": 5},
     expect_keys=["results"])

test("Neural stats", "GET", "/neural/stats",
     expect_keys=["total_connections"])


# ═══════════════════════════════════════════════
# 5. MODEL OBSERVATORY
# ═══════════════════════════════════════════════
print("\n[5] MODEL OBSERVATORY")

test("Model registry", "GET", "/models/registry",
     expect_keys=["models"])

test("Model discover", "GET", "/models/discover")

test("Model health", "GET", "/models/health")

test("Model report", "GET", "/models/report")


# ═══════════════════════════════════════════════
# 6. TOOL EVOLUTION
# ═══════════════════════════════════════════════
print("\n[6] TOOL EVOLUTION")

test("Tool stats", "GET", "/tools/stats",
     expect_keys=["tools"])

test("Tool rankings", "GET", "/tools/rankings")

test("Tool gaps", "GET", "/tools/gaps")

test("Tool compositions", "GET", "/tools/compositions")

test("Tool evolution report", "GET", "/tools/evolution-report")


# ═══════════════════════════════════════════════
# 7. CRITICALITY ENGINE
# ═══════════════════════════════════════════════
print("\n[7] CRITICALITY ENGINE")

test("Criticality temperatura", "GET", "/criticality/temperatura",
     expect_keys=["status"])

test("Criticality avalanchas", "GET", "/criticality/avalanchas",
     expect_keys=["status"])

test("Criticality transiciones", "GET", "/criticality/transiciones",
     expect_keys=["status"])

test("Criticality estado", "GET", "/criticality/estado",
     expect_keys=["status"])


# ═══════════════════════════════════════════════
# 8. INFORMATION THEORY
# ═══════════════════════════════════════════════
print("\n[8] INFORMATION THEORY")

test("Info redundancia", "GET", "/info/redundancia",
     expect_keys=["status"])


# ═══════════════════════════════════════════════
# 9. METACOGNITIVE
# ═══════════════════════════════════════════════
print("\n[9] METACOGNITIVE")

test("Metacognitive FoK", "POST", "/metacognitive/fok",
     body={"query": "test query", "context": {}})

test("Metacognitive JoL", "POST", "/metacognitive/jol",
     body={"resultado": {"hallazgos": [], "confianza": 0.5}, "contexto": {}})

test("Metacognitive Kalman", "GET", "/metacognitive/kalman")


# ═══════════════════════════════════════════════
# 10. PREDICTIVE
# ═══════════════════════════════════════════════
print("\n[10] PREDICTIVE")

test("Predictive trayectoria", "GET", "/predictive/trayectoria")
test("Predictive plan", "GET", "/predictive/plan")
test("Predictive atractores", "GET", "/predictive/atractores")
test("Predictive estado", "GET", "/predictive/estado")


# ═══════════════════════════════════════════════
# 11. GAME THEORY
# ═══════════════════════════════════════════════
print("\n[11] GAME THEORY")

test("Game Theory incentivos", "GET", "/game-theory/incentivos")
test("Game Theory equilibrios", "GET", "/game-theory/equilibrios")
test("Game Theory estado", "GET", "/game-theory/estado")


# ═══════════════════════════════════════════════
# 12. CEO ADVISOR
# ═══════════════════════════════════════════════
print("\n[12] CEO ADVISOR")

test("CEO Advisor scan", "GET", "/ceo/advisor",
     expect_keys=["status", "acciones"])

test("CEO Advisor capabilities", "GET", "/ceo/advisor/capabilities",
     expect_keys=["status"])


# ═══════════════════════════════════════════════
# 13. EXPLORER
# ═══════════════════════════════════════════════
print("\n[13] EXPLORER")

test("Explorer matrix", "GET", "/explorer/matrix")
test("Explorer gaps", "GET", "/explorer/gaps")
test("Explorer dimensions", "GET", "/explorer/by-dimension")
test("Explorer estimate", "GET", "/explorer/estimate?scope_a=patrones&scope_b=sistema")
test("Explorer checklist", "GET", "/explorer/checklist")
test("Explorer scopes", "GET", "/explorer/scopes")


# ═══════════════════════════════════════════════
# 14. EXOCORTEX & STIGMERGY
# ═══════════════════════════════════════════════
print("\n[14] EXOCORTEX & STIGMERGY")

test("Exocortex tenants", "GET", "/exocortex/tenants")
test("Estigmergia marcas", "GET", "/estigmergia/marcas")


# ═══════════════════════════════════════════════
# 15. MONITORING
# ═══════════════════════════════════════════════
print("\n[15] MONITORING")

test("Monitoring dashboard", "GET", "/monitoring/dashboard",
     expect_keys=["status"])

test("Monitoring SLOs", "GET", "/monitoring/slos")

test("Monitoring budget", "GET", "/monitoring/budget")

test("Monitoring circuit breakers", "GET", "/monitoring/circuit-breakers")


# ═══════════════════════════════════════════════
# 16. MISCELLANEOUS
# ═══════════════════════════════════════════════
print("\n[16] MISCELLANEOUS")

test("Propiocepción", "GET", "/propiocepcion")
test("Señales", "GET", "/senales")
test("Métricas", "GET", "/metricas")

test("Reactor candidatas", "GET", "/reactor/candidatas",
     expect_keys=["status"])

test("Chat sessions list", "GET", "/chat/sessions")


# ═══════════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════════
elapsed = round(time.time() - start_time, 1)
total = results["pass"] + results["fail"] + results["skip"]

print(f"\n{'='*60}")
print(f"  SYSTEM TEST REPORT")
print(f"  Target: {BASE_URL}")
print(f"  Elapsed: {elapsed}s")
print(f"{'='*60}")
print(f"  PASS:  {results['pass']}/{total}")
print(f"  FAIL:  {results['fail']}/{total}")
print(f"  SKIP:  {results['skip']}/{total}")

if results["errors"]:
    print(f"\n  FAILURES:")
    for err in results["errors"]:
        print(f"    - {err}")

print(f"{'='*60}")

# Exit code
sys.exit(0 if results["fail"] == 0 else 1)
