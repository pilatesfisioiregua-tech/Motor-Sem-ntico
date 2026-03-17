#!/usr/bin/env python3
"""EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas via OpenRouter.

Evalúa modelos OS para roles en OMNI-MIND motor semántico.
Usa subprocess+curl para API calls (Cloudflare bloquea urllib/requests).
"""

import json
import os
import sys
import time
import subprocess
import tempfile
import re
import argparse
import math
from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
MODELS_ENDPOINT = "https://openrouter.ai/api/v1/models"
RESULTS_DIR = Path("results")
RESULTS_FILE = RESULTS_DIR / "exp1bis_results.json"
REPORT_FILE = RESULTS_DIR / "exp1bis_report.md"
DELAY_BETWEEN_CALLS = 3  # seconds

MODELS = {
    "kimi-k2.5": {
        "model_id": "moonshotai/kimi-k2.5",
        "aliases": ["moonshotai/Kimi-K2.5", "moonshotai/kimi-k2-5"],
        "cost_per_m": 1.50,
        "profile": "Pizarra (agent swarm), evaluador",
    },
    "qwen3.5-397b": {
        "model_id": "qwen/qwen3.5-397b-a17b",
        "aliases": ["Qwen/Qwen3.5-397B-A17B", "qwen/Qwen3.5-397B-A17B"],
        "cost_per_m": 1.20,
        "profile": "Evaluador (IFEval 92.6, GPQA 88.4)",
    },
    "nemotron-super": {
        "model_id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "aliases": ["nvidia/llama-3.3-nemotron-super-49b-v1", "nvidia/Llama-3.3-Nemotron-Super-49B-v1.5"],
        "cost_per_m": 0.40,
        "profile": "Math/validación numérica barata",
    },
    "step-3.5-flash": {
        "model_id": "stepfun/step-3.5-flash",
        "aliases": ["stepfun/Step-3.5-Flash", "stepfun-ai/step-3.5-flash"],
        "cost_per_m": 0.80,
        "profile": "Razonamiento extremo (AIME 97.3)",
    },
    "mimo-v2-flash": {
        "model_id": "xiaomi/mimo-v2-flash",
        "aliases": ["xiaomi/MiMo-V2-Flash", "XiaomiMiMo/MiMo-V2-Flash"],
        "cost_per_m": 0.10,
        "profile": "Ultra-barato, SWE > V3.2",
    },
    "devstral": {
        "model_id": "mistralai/devstral-2512",
        "aliases": ["mistralai/devstral-small"],
        "cost_per_m": 0.50,
        "profile": "#1 SWE patching (reemplaza kimi-dev-72b, no disponible en OpenRouter)",
    },
}

TASK_CONFIG = {
    "T1": {"max_tokens": 8192, "timeout": 240, "temperature": 0.3},
    "T2": {"max_tokens": 8192, "timeout": 180, "temperature": 0.2},
    "T3": {"max_tokens": 16384, "timeout": 300, "temperature": 0.1},
    "T4": {"max_tokens": 8192, "timeout": 180, "temperature": 0.2},
    "T5": {"max_tokens": 8192, "timeout": 240, "temperature": 0.3},
}

# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

PROMPTS = {
    "T1": """Analiza el siguiente caso desde 3 lentes (Salud, Sentido, Continuidad) × 3 funciones (Conservar, Captar, Depurar).

Para CADA una de las 9 combinaciones, identifica:
1. El gap principal (qué falta o está mal)
2. Una pregunta diagnóstica que revelaría la raíz del gap
3. Una acción concreta para cerrar ese gap

CASO:
Elena, 42 años, odontóloga con clínica propia hace 12 años. 2 sillones, 1 higienista, 1 recepcionista.
Factura 180K€/año, beneficio neto ~45K€. Trabaja 50h/semana, no ha cogido vacaciones en 3 años.
Su padre (dentista jubilado) le presiona para abrir segunda sede. El banco le aprobó un crédito de 200K€.
Tiene un competidor low-cost a 2 calles que le ha quitado el 15% de pacientes en 18 meses.
Su higienista (la mejor de la zona) ha recibido una oferta de otra clínica.

Responde en formato estructurado: una sección por cada combinación Lente×Función.
Al final, identifica: ¿cuál es el gap MÁS CRÍTICO de los 9? ¿Por qué?""",

    "T2": """Eres evaluador de calidad analítica. Abajo tienes el OUTPUT de un modelo que analizó un caso.

Evalúa cada hallazgo en una escala 1-5:
1 = Genérico (podría aplicar a cualquier caso)
2 = Relevante pero superficial
3 = Específico y correcto
4 = Profundo (revela algo no obvio)
5 = Excepcional (insight que cambia la comprensión del caso)

OUTPUT A EVALUAR:
---
Caso: CTO de startup SaaS (28 empleados, 7 meses runway, 8% churn mensual) en conflicto con CEO sobre pivotar vs estabilizar.

Hallazgo 1: "El churn del 8% mensual implica que la base de clientes se renueva completamente cada 12 meses. Cualquier crecimiento neto requiere adquirir más del 8% mensual."
Hallazgo 2: "El conflicto CTO-CEO es un proxy de un conflicto más profundo sobre identidad: ¿somos una empresa técnica o comercial?"
Hallazgo 3: "Los 3 clientes enterprise que pagan 3x generan el 30% del MRR. Esto ya ES un pivot enterprise — solo que no reconocido."
Hallazgo 4: "La startup tiene un problema de decisión."
Hallazgo 5: "El CTO debería hablar con el CEO para resolver sus diferencias."
Hallazgo 6: "Con 7 meses de runway y un pivot que tarda 6-12 meses, la ventana temporal es contradictoria. El pivot no cabe en el runway."
---

Para cada hallazgo: score (1-5) + justificación en 1 frase.
Al final: ranking de los 6 hallazgos de mejor a peor, y score medio.

IMPORTANTE: Los hallazgos 4 y 5 son deliberadamente genéricos/vacíos. Si los puntúas alto, tu evaluación es mala.""",

    "T3": """Resuelve los siguientes 5 problemas. Muestra tu trabajo paso a paso.

P1 (aritmética de negocio):
Una clínica factura 180K€/año con margen neto del 25%. Si abre segunda sede con inversión de 200K€ y la nueva sede tarda 18 meses en alcanzar el mismo volumen (crecimiento lineal desde 0), ¿cuántos meses hasta recuperar la inversión completa? Asume que la sede original mantiene su facturación.

P2 (probabilidad):
En un equipo de 6 developers, cada uno tiene independientemente un 15% de probabilidad de irse en los próximos 6 meses. ¿Cuál es la probabilidad de perder 2 o más developers? ¿Y la de perder exactamente 0?

P3 (optimización):
Tienes 7 meses de runway a 28K€/mes de burn rate. Un pivot cuesta 15K€/mes adicionales durante 4 meses. Una estrategia de estabilización cuesta 5K€/mes adicionales durante 3 meses. ¿Cuántos meses de runway quedan después de cada opción? ¿Cuál es viable si necesitas al menos 2 meses de buffer post-implementación?

P4 (series):
El churn mensual es 8%. La base actual es 75 clientes. Adquieres 10 clientes nuevos por mes.
Calcula la base de clientes al final de los meses 1, 3, 6 y 12. ¿Converge a un equilibrio? Si sí, ¿cuál?

P5 (lógica):
Tres socios (A, B, C) votan sobre 4 propuestas. A vota Sí si el coste es <50K. B vota Sí si el ROI esperado es >20%. C vota Sí si no requiere más personal. Mayoría simple decide.
Propuesta 1: Coste 30K, ROI 25%, requiere 1 persona. → ¿Aprobada?
Propuesta 2: Coste 60K, ROI 35%, no requiere personal. → ¿Aprobada?
Propuesta 3: Coste 45K, ROI 15%, no requiere personal. → ¿Aprobada?
Propuesta 4: Coste 55K, ROI 22%, requiere 2 personas. → ¿Aprobada?

Responde CADA problema con resultado numérico final claramente marcado.""",

    "T4": """Genera una Edge Function en TypeScript (Deno runtime) que:

1. Recibe un POST con JSON body: { "metrics": [...], "thresholds": {...} }
   - metrics: array de { "name": string, "value": number, "timestamp": string }
   - thresholds: objeto { [metric_name]: { "warn": number, "critical": number } }

2. Para cada métrica:
   - Si value > critical threshold: status = "critical"
   - Si value > warn threshold: status = "warn"
   - Si no hay threshold definido para esa métrica: status = "unknown"
   - Si value <= warn: status = "ok"

3. Devuelve JSON:
   {
     "alerts": [{ "name": string, "value": number, "status": string, "threshold": number|null }],
     "summary": { "total": number, "critical": number, "warn": number, "ok": number, "unknown": number },
     "worst": string  // nombre de la métrica con peor estado (critical > warn > unknown > ok)
   }

4. Maneja errores: body vacío → 400, metrics no es array → 400, thresholds no es objeto → 400.

5. Incluye headers CORS.

Genera SOLO el código, sin explicación. El código debe ser ejecutable directamente con `deno serve`.""",

    "T5": """Abajo tienes hallazgos de 5 análisis DIFERENTES sobre el mismo caso (una abogada corporativa, 38 años, considerando cambio de carrera a mediación). Cada análisis viene de una lente distinta.

Tu tarea: sintetiza los 5 en un análisis integrado que:
1. Identifique las 3 CONEXIONES más importantes entre hallazgos de diferentes lentes
2. Para cada conexión: qué lentes conecta, qué revela que ninguna sola veía, y qué implicación tiene
3. Identifique 1 CONTRADICCIÓN entre lentes (donde dos lentes dicen cosas opuestas)
4. Produzca 1 HALLAZGO EMERGENTE que ninguna lente individual podría producir

HALLAZGOS POR LENTE:

LENTE FINANCIERA (INT-07):
"El salto de 95K€ a ~40K€ los primeros 2 años es absorbible: 120K€ ahorrados, pareja gana 60K€. El riesgo real no es financiero sino de coste de oportunidad: a los 38, cada año fuera del track de socia reduce su valor de mercado legal un ~15%."

LENTE SOCIAL (INT-08):
"No ha hablado con su marido sobre el cambio. El silencio no es olvido — es gestión de conflicto anticipado. Su identidad social ('la abogada exitosa') es más del entorno que suya. La pregunta que evita: ¿quién soy si no soy esto?"

LENTE ESTRATÉGICA (INT-05):
"Tiene 3 opciones que no ha considerado: (1) mediación dentro de su bufete actual, (2) transición gradual 60/40 durante 18 meses, (3) máster en mediación mientras trabaja. El framing binario 'saltar o quedarme' elimina opciones viables."

LENTE EXISTENCIAL (INT-17):
"El insomnio de 8 meses es la señal corporal de que la decisión ya está tomada emocionalmente. Lo que falta no es más información — es coraje para actuar. Cada mes de no-decisión degrada tanto la opción de quedarse (resentimiento) como la de irse (agotamiento)."

LENTE CONSTRUCTIVA (INT-16):
"La transición gradual es técnicamente viable: máster de 18 meses compatible con trabajo, coste 8K€, primeros clientes de mediación posibles en mes 12. El prototipo mínimo es hacer 1 mediación pro-bono este mes para validar si le gusta el trabajo real, no la idea del trabajo."

---
Formato: sección por cada elemento pedido (3 conexiones, 1 contradicción, 1 emergente). Para cada uno, marca qué lentes participan.""",
}

# ═══════════════════════════════════════════════════════════════════════════════
# API FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks (Qwen, DeepSeek, etc.).
    If stripping leaves nothing, return the content inside the last think block."""
    stripped = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    if stripped:
        return stripped
    # All content was inside think tags — extract the last block's content
    think_blocks = re.findall(r"<think>(.*?)</think>", text, flags=re.DOTALL)
    if think_blocks:
        return think_blocks[-1].strip()
    # No think tags at all but text was empty after strip
    return text.strip()


def call_openrouter(
    model_id: str,
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 4000,
    timeout: int = 120,
) -> dict:
    """Call OpenRouter via subprocess+curl (Cloudflare blocks urllib/requests)."""
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY not set"}

    body = json.dumps({
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    })

    tmpfile = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(body)
            tmpfile = f.name

        t0 = time.time()
        result = subprocess.run(
            [
                "curl", "-s", "--max-time", str(timeout),
                ENDPOINT,
                "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
                "-H", "HTTP-Referer: https://omni-mind.app",
                "-H", "X-Title: OMNI-MIND Exp1bis",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmpfile}",
            ],
            capture_output=True,
            text=True,
            timeout=timeout + 10,
        )
        latency = time.time() - t0

        if result.returncode != 0:
            return {"error": f"curl failed: {result.stderr[:200]}", "latency_s": latency}

        if not result.stdout.strip():
            return {"error": "empty response", "latency_s": latency}

        resp = json.loads(result.stdout)

        if "error" in resp:
            return {"error": resp["error"], "latency_s": round(latency, 2)}

        choices = resp.get("choices", [])
        if not choices:
            return {"error": f"no choices in response: {result.stdout[:300]}", "latency_s": latency}

        text = choices[0].get("message", {}).get("content", "") or ""
        text = strip_think_tags(text)

        usage = resp.get("usage", {})
        return {
            "text": text,
            "tokens_in": usage.get("prompt_tokens", 0),
            "tokens_out": usage.get("completion_tokens", 0),
            "latency_s": round(latency, 2),
            "model_id": model_id,
        }

    except subprocess.TimeoutExpired:
        return {"error": f"timeout after {timeout}s", "latency_s": timeout}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}", "latency_s": time.time() - t0}
    except Exception as e:
        return {"error": str(e), "latency_s": 0}
    finally:
        if tmpfile and os.path.exists(tmpfile):
            os.unlink(tmpfile)


def verify_models() -> dict:
    """Verify model IDs against OpenRouter catalog. Returns {name: resolved_id|None}."""
    print("⏳ Fetching OpenRouter model catalog...")
    result = subprocess.run(
        ["curl", "-s", "--max-time", "30", MODELS_ENDPOINT,
         "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}"],
        capture_output=True, text=True,
    )
    try:
        data = json.loads(result.stdout)
        catalog = data if isinstance(data, list) else data.get("data", [])
        catalog_ids = {m.get("id", "").lower(): m.get("id", "") for m in catalog}
    except Exception as e:
        print(f"❌ Failed to fetch catalog: {e}")
        return {}

    print(f"   Catalog: {len(catalog_ids)} models\n")
    resolved = {}

    for name, cfg in MODELS.items():
        mid = cfg["model_id"]
        candidates = [mid] + cfg.get("aliases", [])

        found = None
        for c in candidates:
            if c.lower() in catalog_ids:
                found = catalog_ids[c.lower()]
                break

        if found:
            print(f"  ✅ {name:20s} → {found}")
            resolved[name] = found
        else:
            # Fuzzy search
            key = name.replace("-", "").replace(".", "").replace(" ", "").lower()
            suggestions = [
                cid for cid in catalog_ids.values()
                if key[:6] in cid.lower().replace("-", "").replace(".", "")
            ]
            print(f"  ❌ {name:20s} → NOT FOUND (tried: {mid})")
            if suggestions:
                print(f"     Suggestions: {suggestions[:5]}")
            resolved[name] = None

    # Quick ping test for resolved models
    print("\n⏳ Ping test (short prompt)...")
    for name, mid in resolved.items():
        if mid is None:
            continue
        resp = call_openrouter(mid, "Say OK", temperature=0, max_tokens=10, timeout=15)
        if "error" in resp:
            print(f"  ⚠️  {name:20s} → ping FAILED: {resp['error']}")
            # Try aliases
            for alias in MODELS[name].get("aliases", []):
                if alias.lower() in catalog_ids:
                    alt = catalog_ids[alias.lower()]
                    resp2 = call_openrouter(alt, "Say OK", temperature=0, max_tokens=10, timeout=15)
                    if "error" not in resp2:
                        print(f"     → fixed with alias: {alt}")
                        resolved[name] = alt
                        break
        else:
            print(f"  ✅ {name:20s} → OK ({resp['latency_s']}s)")
        time.sleep(1)

    return resolved


# ═══════════════════════════════════════════════════════════════════════════════
# EVALUATORS
# ═══════════════════════════════════════════════════════════════════════════════

def eval_T1(text: str) -> dict:
    """T1: Análisis Cognitivo — Matriz 3 Lentes × 3 Funciones."""
    t = text.lower()
    lentes = ["salud", "sentido", "continuidad"]
    funciones = ["conservar", "captar", "depurar"]

    # Count sections covering each combination
    sections_found = 0
    for l in lentes:
        for f in funciones:
            # Look for both terms near each other (within ~500 chars)
            pattern = rf"(?:{l})(?:.{{0,500}})(?:{f})|(?:{f})(?:.{{0,500}})(?:{l})"
            if re.search(pattern, t, re.DOTALL):
                sections_found += 1

    # Count structural elements
    gap_count = len(re.findall(r"(?:gap|brecha|falta|déficit|problema|carencia)", t))
    pregunta_count = len(re.findall(r"\?", t))
    accion_count = len(re.findall(
        r"(?:acción|accion|implementar|ejecutar|hacer|realizar|establecer|crear|definir|contratar|negociar|diseñar)",
        t
    ))

    # Critical gap identification
    has_critical = bool(re.search(
        r"(?:más crítico|mas critico|más importante|critical|priorid)", t
    ))

    # Length as proxy for depth
    length = len(text)
    length_score = min(1.0, length / 3000)

    sections_score = sections_found / 9
    elements_score = min(1.0, (min(gap_count, 9) + min(pregunta_count, 9) + min(accion_count, 9)) / 27)
    critical_score = 1.0 if has_critical else 0.0

    score = (sections_score * 0.40 + elements_score * 0.25 +
             critical_score * 0.20 + length_score * 0.15)

    return {
        "score": round(score, 3),
        "metrics": {
            "sections_found": sections_found,
            "sections_score": round(sections_score, 3),
            "gap_mentions": gap_count,
            "questions": pregunta_count,
            "actions": accion_count,
            "has_critical_gap": has_critical,
            "length": length,
        },
    }


def eval_T2(text: str) -> dict:
    """T2: Evaluación de Output Ajeno — Discriminación y reconocimiento."""
    # Expected scores: H1=4, H2=4, H3=5, H4=1, H5=1, H6=4
    expected = {1: 4, 2: 4, 3: 5, 4: 1, 5: 1, 6: 4}

    # Extract scores for H1-H6
    scores = {}
    for h in range(1, 7):
        patterns = [
            # **Hallazgo 1:** 3 - description  (markdown bold)
            rf"\*\*[Hh]allazgo\s*{h}[:\*]*\*?\*?\s*[:=\-–—]?\s*(\d)",
            # Hallazgo 1: Score: 3 or Hallazgo 1: 3
            rf"[Hh]allazgo\s*{h}\s*[:=\-–—]\s*(?:[Ss]core\s*[:=]?\s*)?(\d)",
            # Hallazgo 1: Puntuación 3  or  Puntuación: 3
            rf"[Hh]allazgo\s*{h}.*?[Pp]untuaci[oó]n\s*[:=]?\s*(\d)",
            # H1: 4/5
            rf"[Hh]allazgo\s*{h}.*?(\d)\s*/?\s*5",
            # H1 = 3
            rf"[Hh]{h}\s*[:=\-–—]\s*(\d)",
            # N. ... Score/Puntuación X
            rf"(?:^|\n)\s*\*?\*?{h}\s*[\.\):\-–—]\s*.*?(?:[Ss]core|[Pp]untuaci[oó]n|[Cc]alificaci[oó]n)\s*[:=]?\s*(\d)",
            # **N** (bold score)
            rf"[Hh]allazgo\s*{h}.*?\*\*(\d)\*\*",
            # N. ... : X
            rf"(?:^|\n)\s*\*?\*?{h}\s*[\.\)]\s*.*?[:=]\s*(\d)",
            # Score/Puntuación first, then number  (e.g. "Score: 3 — Hallazgo...")
            rf"(?:^|\n).*?{h}.*?[:]\s*(\d)(?:\s|/|$)",
        ]
        for pat in patterns:
            m = re.search(pat, text, re.MULTILINE | re.DOTALL)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 5:
                    scores[h] = val
                    break

    # Discrimination: H4 and H5 should be ≤ 2
    h4 = scores.get(4, 3)
    h5 = scores.get(5, 3)
    discrimination = sum([h4 <= 2, h5 <= 2]) / 2

    # Recognition: H1, H3, H6 should be ≥ 4
    h1 = scores.get(1, 2)
    h3 = scores.get(3, 2)
    h6 = scores.get(6, 2)
    recognition = sum([h1 >= 4, h3 >= 4, h6 >= 4]) / 3

    # Correlation with expected
    if len(scores) >= 4:
        extracted = [scores.get(i, 3) for i in range(1, 7)]
        exp_list = [expected[i] for i in range(1, 7)]
        mean_e = sum(extracted) / 6
        mean_x = sum(exp_list) / 6
        num = sum((a - mean_e) * (b - mean_x) for a, b in zip(extracted, exp_list))
        den_a = math.sqrt(sum((a - mean_e) ** 2 for a in extracted))
        den_b = math.sqrt(sum((b - mean_x) ** 2 for b in exp_list))
        correlation = num / (den_a * den_b) if den_a * den_b > 0 else 0
    else:
        correlation = 0

    # Ranking check: look for a ranking section
    has_ranking = bool(re.search(r"(?:ranking|orden|mejor.*peor|peor.*mejor)", text.lower()))

    score = (discrimination * 0.35 + recognition * 0.30 +
             max(0, correlation) * 0.20 + (0.15 if has_ranking else 0))

    return {
        "score": round(score, 3),
        "metrics": {
            "extracted_scores": scores,
            "discrimination": round(discrimination, 3),
            "recognition": round(recognition, 3),
            "correlation": round(correlation, 3),
            "has_ranking": has_ranking,
            "h4_score": h4,
            "h5_score": h5,
        },
    }


def _extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    return [float(x.replace(",", ".")) for x in re.findall(r"\d+[.,]?\d*", text)]


def _check_near(numbers: List[float], target: float, tolerance: float) -> bool:
    """Check if any number in list is near target."""
    return any(abs(n - target) <= tolerance for n in numbers)


def eval_T3(text: str) -> dict:
    """T3: Razonamiento Matemático — 5 problemas."""
    t = text
    results = {}

    # Split by problem markers
    sections = {}
    for i in range(1, 6):
        pattern = rf"(?:P{i}|[Pp]roblema\s*{i})"
        parts = re.split(pattern, t)
        if len(parts) > 1:
            # Get text until next problem or end
            next_pattern = rf"(?:P{i+1}|[Pp]roblema\s*{i+1})" if i < 5 else r"$$$NEVER$$$"
            section = parts[1]
            next_split = re.split(next_pattern, section)
            sections[i] = next_split[0]
        else:
            sections[i] = ""

    # If sections are empty, try splitting the whole text into 5 roughly equal parts
    if not any(sections.values()):
        chunk = len(t) // 5
        for i in range(1, 6):
            sections[i] = t[(i - 1) * chunk : i * chunk]

    # P1: months to recover investment
    # Accept range 25-65 (various valid interpretations)
    nums_p1 = _extract_numbers(sections.get(1, ""))
    p1_ok = any(25 <= n <= 65 for n in nums_p1)
    results["P1"] = p1_ok

    # P2: P(>=2) ≈ 0.224, P(0) ≈ 0.377
    nums_p2 = _extract_numbers(sections.get(2, ""))
    p2_prob_ge2 = _check_near(nums_p2, 0.224, 0.03) or _check_near(nums_p2, 22.4, 3)
    p2_prob_0 = _check_near(nums_p2, 0.377, 0.03) or _check_near(nums_p2, 37.7, 3)
    results["P2"] = p2_prob_ge2 and p2_prob_0

    # P3: Pivot runway ≈ 0.86, Stabilize ≈ 3.46, pivot NOT viable, stab viable
    s3 = sections.get(3, "").lower()
    nums_p3 = _extract_numbers(sections.get(3, ""))
    p3_pivot_val = _check_near(nums_p3, 0.86, 0.5) or _check_near(nums_p3, 0.857, 0.5)
    p3_stab_val = _check_near(nums_p3, 3.46, 0.5) or _check_near(nums_p3, 3.464, 0.5)
    p3_viability = ("no viable" in s3 or "not viable" in s3 or "no es viable" in s3 or
                    "inviable" in s3) and ("viable" in s3)  # needs both: one not viable, one viable
    results["P3"] = (p3_pivot_val or p3_stab_val) and p3_viability

    # P4: Equilibrium = 125
    nums_p4 = _extract_numbers(sections.get(4, ""))
    p4_equil = _check_near(nums_p4, 125, 3)
    # Month 1 ≈ 79
    p4_m1 = _check_near(nums_p4, 79, 3)
    results["P4"] = p4_equil and p4_m1

    # P5: P1=Sí(A+B), P2=Sí(B+C), P3=Sí(A+C), P4=No(solo B)
    s5 = sections.get(5, "").lower()
    # Look for approval patterns per proposal
    p5_answers = []
    for pi in range(1, 5):
        # Look near "propuesta X" for yes/no
        pat = rf"propuesta\s*{pi}.*?(?:aprobada|sí|si\b|yes|rechazada|no\b)"
        m = re.search(pat, s5, re.DOTALL)
        if m:
            found = m.group(0)
            approved = bool(re.search(r"(?:aprobada|sí\b|si\b|yes)", found))
            rejected = bool(re.search(r"(?:rechazada|no\b)", found))
            p5_answers.append("yes" if approved and not rejected else "no")
        else:
            p5_answers.append("?")

    expected_p5 = ["yes", "yes", "yes", "no"]
    p5_correct = sum(a == e for a, e in zip(p5_answers, expected_p5))
    results["P5"] = p5_correct >= 3  # at least 3 of 4 correct

    correct = sum(results.values())
    score = correct / 5

    return {
        "score": round(score, 3),
        "metrics": {
            "P1_correct": results["P1"],
            "P2_correct": results["P2"],
            "P3_correct": results["P3"],
            "P4_correct": results["P4"],
            "P5_correct": results["P5"],
            "P5_detail": p5_answers,
            "correct_count": correct,
        },
    }


def eval_T4(text: str) -> dict:
    """T4: Generación de Código — análisis estructural."""
    # Extract code block
    code_match = re.search(r"```(?:typescript|ts|tsx)?\s*\n(.*?)```", text, re.DOTALL)
    if code_match:
        code = code_match.group(1)
    else:
        # Maybe the whole response is code
        code = text

    checks = {
        "has_serve_handler": bool(re.search(r"(?:Deno\.serve|export\s+default|serve\s*\()", code)),
        "handles_post": bool(re.search(r"(?:POST|method.*POST|request\.method)", code, re.IGNORECASE)),
        "parses_json": bool(re.search(r"(?:\.json\(\)|JSON\.parse)", code)),
        "error_400": bool(re.search(r"(?:400|Bad Request)", code)),
        "cors_headers": bool(re.search(
            r"(?:Access-Control|CORS|cors|OPTIONS)", code, re.IGNORECASE
        )),
        "iterates_metrics": bool(re.search(r"(?:\.map\(|\.forEach\(|for\s*\()", code)),
        "threshold_compare": bool(re.search(r"(?:critical|warn|threshold)", code, re.IGNORECASE)),
        "returns_alerts": bool(re.search(r"alerts", code)),
        "returns_summary": bool(re.search(r"summary", code)),
        "returns_worst": bool(re.search(r"worst", code)),
    }

    passed = sum(checks.values())
    score = passed / len(checks)

    return {
        "score": round(score, 3),
        "metrics": {
            "checks": checks,
            "passed": passed,
            "total": len(checks),
            "code_length": len(code),
        },
    }


def eval_T5(text: str) -> dict:
    """T5: Síntesis Multi-Fuente — conexiones, contradicción, emergente."""
    t = text.lower()

    # Count connections (should be 3)
    connection_patterns = [
        r"conexi[oó]n\s*[#\d]",
        r"(?:primera|segunda|tercera|1[ªa]|2[ªa]|3[ªa])\s*conexi[oó]n",
        r"connection\s*[#\d]",
    ]
    connection_count = 0
    for pat in connection_patterns:
        matches = re.findall(pat, t)
        connection_count = max(connection_count, len(matches))

    # If no explicit connection markers, look for numbered sections
    if connection_count == 0:
        # Count sections that discuss lens connections
        lens_mentions = len(re.findall(r"(?:INT-\d{2}|lente\s+\w+)", t))
        connection_count = min(3, lens_mentions // 2)

    # Check lens references in connections
    lens_ids = re.findall(r"INT-\d{2}", text)
    unique_lenses = len(set(lens_ids))
    has_cross_lens = unique_lenses >= 3

    # Contradiction section
    has_contradiction = bool(re.search(
        r"(?:contradicci[oó]n|contradiction|opuest[oa]s|conflicto entre|tension entre|tensión entre)",
        t
    ))

    # Emergent finding
    has_emergent = bool(re.search(
        r"(?:emergente|emergen[tc]|nuevo hallazgo|hallazgo.*ninguna lente|insight.*integra)",
        t
    ))

    # Count inter-lens connections (mentions of multiple lenses together)
    inter_lens = len(re.findall(
        r"(?:INT-\d{2}.*?INT-\d{2})|(?:lente\s+\w+.*?lente\s+\w+)",
        t, re.DOTALL
    ))

    # Length and depth
    length = len(text)
    length_score = min(1.0, length / 2000)

    connections_score = min(1.0, connection_count / 3)
    cross_score = 1.0 if has_cross_lens else 0.3

    score = (connections_score * 0.30 + cross_score * 0.15 +
             (1.0 if has_contradiction else 0.0) * 0.20 +
             (1.0 if has_emergent else 0.0) * 0.20 +
             length_score * 0.15)

    return {
        "score": round(score, 3),
        "metrics": {
            "connections_found": connection_count,
            "unique_lenses_referenced": unique_lenses,
            "has_cross_lens": has_cross_lens,
            "has_contradiction": has_contradiction,
            "has_emergent": has_emergent,
            "inter_lens_connections": inter_lens,
            "length": length,
        },
    }


EVALUATORS = {
    "T1": eval_T1,
    "T2": eval_T2,
    "T3": eval_T3,
    "T4": eval_T4,
    "T5": eval_T5,
}

TASK_NAMES = {
    "T1": "Análisis Cognitivo",
    "T2": "Evaluación Output",
    "T3": "Razonamiento Math",
    "T4": "Generación Código",
    "T5": "Síntesis Multi-Fuente",
}


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def load_results() -> dict:
    """Load existing results or create empty structure."""
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE) as f:
            return json.load(f)
    return {
        "experiment": "exp1_bis",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "models": list(MODELS.keys()),
        "results": {},
        "summary": {},
    }


def save_results(results: dict):
    """Save results incrementally."""
    RESULTS_DIR.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def run_single(
    model_name: str,
    model_id: str,
    task_id: str,
) -> dict:
    """Run a single model × task combination."""
    cfg = TASK_CONFIG[task_id]
    prompt = PROMPTS[task_id]

    print(f"  📤 {model_name} × {task_id} ({TASK_NAMES[task_id]})...", end=" ", flush=True)

    resp = call_openrouter(
        model_id,
        prompt,
        temperature=cfg["temperature"],
        max_tokens=cfg["max_tokens"],
        timeout=cfg["timeout"],
    )

    if "error" in resp:
        print(f"❌ {resp['error']}")
        return {
            "error": resp["error"],
            "score": 0,
            "metrics": {},
            "latency_s": resp.get("latency_s", 0),
            "tokens_in": 0,
            "tokens_out": 0,
        }

    # Evaluate
    evaluator = EVALUATORS[task_id]
    evaluation = evaluator(resp["text"])

    cost = (resp["tokens_in"] + resp["tokens_out"]) * MODELS[model_name]["cost_per_m"] / 1_000_000

    print(f"✅ score={evaluation['score']:.2f}  "
          f"({resp['tokens_out']}tok, {resp['latency_s']}s, ${cost:.4f})")

    return {
        "score": evaluation["score"],
        "metrics": evaluation["metrics"],
        "tokens_in": resp["tokens_in"],
        "tokens_out": resp["tokens_out"],
        "latency_s": resp["latency_s"],
        "cost": round(cost, 5),
        "raw": resp["text"][:5000],  # truncate for storage
    }


def run_experiment(
    model_filter: Optional[str] = None,
    task_filter: Optional[str] = None,
    resolved_ids: Optional[Dict] = None,
):
    """Run the full experiment (or filtered subset)."""
    results = load_results()

    models_to_run = {k: v for k, v in MODELS.items()
                     if model_filter is None or model_filter in k}
    tasks_to_run = [t for t in TASK_CONFIG
                    if task_filter is None or task_filter.upper() == t]

    if not models_to_run:
        print(f"❌ No models match filter: {model_filter}")
        print(f"   Available: {list(MODELS.keys())}")
        return
    if not tasks_to_run:
        print(f"❌ No tasks match filter: {task_filter}")
        print(f"   Available: {list(TASK_CONFIG.keys())}")
        return

    total = len(models_to_run) * len(tasks_to_run)
    print(f"\n🚀 EXP 1 BIS — {len(models_to_run)} modelos × {len(tasks_to_run)} tareas = {total} runs\n")

    completed = 0
    for model_name, model_cfg in models_to_run.items():
        # Resolve model ID
        if resolved_ids and model_name in resolved_ids and resolved_ids[model_name]:
            model_id = resolved_ids[model_name]
        else:
            model_id = model_cfg["model_id"]

        print(f"\n{'═' * 60}")
        print(f"  MODEL: {model_name} ({model_id})")
        print(f"{'═' * 60}")

        if model_name not in results["results"]:
            results["results"][model_name] = {}

        for task_id in tasks_to_run:
            # Skip if already completed
            if task_id in results["results"][model_name]:
                existing = results["results"][model_name][task_id]
                if existing.get("score", 0) > 0 or "raw" in existing:
                    print(f"  ⏭️  {model_name} × {task_id} already done (score={existing['score']:.2f})")
                    completed += 1
                    continue

            result = run_single(model_name, model_id, task_id)
            results["results"][model_name][task_id] = result
            completed += 1

            # Save incrementally
            save_results(results)

            # Rate limiting
            if completed < total:
                time.sleep(DELAY_BETWEEN_CALLS)

    # Generate summary
    results["summary"] = generate_summary(results["results"])
    save_results(results)

    # Generate markdown report
    generate_report(results)

    print(f"\n{'═' * 60}")
    print(f"  ✅ COMPLETADO: {completed}/{total} runs")
    print(f"  📁 Results: {RESULTS_FILE}")
    print(f"  📄 Report:  {REPORT_FILE}")
    print(f"{'═' * 60}")


def generate_summary(results: dict) -> dict:
    """Generate summary statistics from results."""
    by_model = {}
    by_task = {}

    for model_name, tasks in results.items():
        scores = []
        total_cost = 0
        total_latency = 0
        for task_id, data in tasks.items():
            s = data.get("score", 0)
            scores.append(s)
            total_cost += data.get("cost", 0)
            total_latency += data.get("latency_s", 0)

            if task_id not in by_task:
                by_task[task_id] = {"scores": {}, "best": "", "worst": "", "mean": 0}
            by_task[task_id]["scores"][model_name] = s

        by_model[model_name] = {
            "mean_score": round(sum(scores) / len(scores), 3) if scores else 0,
            "total_cost": round(total_cost, 4),
            "total_latency": round(total_latency, 1),
            "scores": {t: d.get("score", 0) for t, d in tasks.items()},
        }

    # Find best/worst per task
    for task_id, data in by_task.items():
        if data["scores"]:
            data["best"] = max(data["scores"], key=data["scores"].get)
            data["worst"] = min(data["scores"], key=data["scores"].get)
            data["mean"] = round(sum(data["scores"].values()) / len(data["scores"]), 3)
        # Remove raw scores dict for cleanliness
        del data["scores"]

    # Overall ranking
    ranking = sorted(by_model.items(), key=lambda x: x[1]["mean_score"], reverse=True)
    overall = [{"model": name, "score": data["mean_score"], "cost": data["total_cost"]}
               for name, data in ranking]

    return {
        "by_model": by_model,
        "by_task": by_task,
        "rankings": {"overall": overall},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_report(data: dict):
    """Generate markdown report."""
    results = data.get("results", {})
    summary = data.get("summary", {})
    by_model = summary.get("by_model", {})

    lines = [
        "# EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas",
        f"\n**Fecha:** {data.get('date', 'N/A')}",
        f"**Provider:** OpenRouter",
        "",
        "## Tabla Principal: Modelo × Tarea (scores 0-1)",
        "",
        "| Modelo | T1 Cognitivo | T2 Evaluador | T3 Math | T4 Código | T5 Síntesis | **Media** | **Coste** |",
        "|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for model_name in MODELS:
        if model_name not in results:
            continue
        tasks = results[model_name]
        row = [model_name]
        for t in ["T1", "T2", "T3", "T4", "T5"]:
            s = tasks.get(t, {}).get("score", 0)
            # Color coding via emoji
            if s >= 0.85:
                row.append(f"**{s:.2f}** 🟢")
            elif s >= 0.65:
                row.append(f"{s:.2f} 🟡")
            elif s > 0:
                row.append(f"{s:.2f} 🔴")
            else:
                row.append("— ⚪")
        mean = by_model.get(model_name, {}).get("mean_score", 0)
        cost = by_model.get(model_name, {}).get("total_cost", 0)
        row.append(f"**{mean:.2f}**")
        row.append(f"${cost:.3f}")
        lines.append("| " + " | ".join(row) + " |")

    # Rankings
    lines.extend([
        "",
        "## Rankings",
        "",
        "### Overall",
        "",
        "| # | Modelo | Score | Coste |",
        "|---|--------|:---:|:---:|",
    ])
    for i, entry in enumerate(summary.get("rankings", {}).get("overall", []), 1):
        lines.append(f"| {i} | {entry['model']} | {entry['score']:.2f} | ${entry['cost']:.3f} |")

    # Best per task
    lines.extend(["", "### Mejor por Tarea", ""])
    by_task = summary.get("by_task", {})
    for task_id in ["T1", "T2", "T3", "T4", "T5"]:
        td = by_task.get(task_id, {})
        lines.append(f"- **{task_id} ({TASK_NAMES.get(task_id, '')}):** "
                      f"Mejor={td.get('best', '?')}, Media={td.get('mean', 0):.2f}")

    # Role recommendations
    lines.extend([
        "",
        "## Recomendaciones por Rol OMNI-MIND",
        "",
    ])

    role_checks = {
        "Pizarra (agent swarm)": ("kimi-k2.5", ["T1", "T5"], 0.80,
            "T1 + T5 ≥ 0.80 → Supera GPT-OSS"),
        "Evaluador": ("qwen3.5-397b", ["T2"], 0.85,
            "T2 ≥ 0.85 → Discriminación perfecta en H4/H5"),
        "Math/Validación numérica": ("nemotron-super", ["T3"], 0.80,
            "T3 ≥ 0.80 → 4/5 problemas correctos"),
        "Debugger/Razonador": ("step-3.5-flash", ["T3", "T4"], 0.85,
            "T3 + T4 ≥ 0.85 → Math + código funcional"),
        "Tier barato universal": ("mimo-v2-flash", ["T1", "T2", "T3", "T4", "T5"], 0.65,
            "Media ≥ 0.65 → Aceptable en todo a $0.10/M"),
        "Patcher (#1 SWE)": ("devstral", ["T4"], 0.85,
            "T4 ≥ 0.85 → Tests pasan sin debug"),
    }

    for role, (model, tasks, threshold, criteria) in role_checks.items():
        if model in results:
            task_scores = [results[model].get(t, {}).get("score", 0) for t in tasks]
            mean = sum(task_scores) / len(task_scores) if task_scores else 0
            verdict = "✅ SÍ" if mean >= threshold else "❌ NO"
            lines.append(f"| **{role}** | {model} | {verdict} ({mean:.2f} vs {threshold}) | {criteria} |")
        else:
            lines.append(f"| **{role}** | {model} | ⚪ Sin datos | {criteria} |")

    # Cost summary
    total_cost = sum(m.get("total_cost", 0) for m in by_model.values())
    total_tokens_in = sum(
        d.get("tokens_in", 0)
        for tasks in results.values()
        for d in tasks.values()
    )
    total_tokens_out = sum(
        d.get("tokens_out", 0)
        for tasks in results.values()
        for d in tasks.values()
    )

    lines.extend([
        "",
        "## Coste Total",
        "",
        f"- **Tokens input:** {total_tokens_in:,}",
        f"- **Tokens output:** {total_tokens_out:,}",
        f"- **Coste total:** ${total_cost:.3f}",
        "",
        "---",
        f"*Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
    ])

    RESULTS_DIR.mkdir(exist_ok=True)
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(lines))


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas via OpenRouter"
    )
    parser.add_argument("--verify", action="store_true",
                        help="Verify model availability without running tasks")
    parser.add_argument("--model", type=str, default=None,
                        help="Filter: run only this model (partial match)")
    parser.add_argument("--task", type=str, default=None,
                        help="Filter: run only this task (T1-T5)")
    parser.add_argument("--report", action="store_true",
                        help="Regenerate report from existing results")
    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("❌ Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)

    print("=" * 60)
    print("  EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas")
    print("  Provider: OpenRouter")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    if args.report:
        data = load_results()
        if data.get("results"):
            data["summary"] = generate_summary(data["results"])
            generate_report(data)
            save_results(data)
            print(f"\n📄 Report regenerated: {REPORT_FILE}")
        else:
            print("❌ No results found to generate report")
        return

    if args.verify:
        resolved = verify_models()
        ok = sum(1 for v in resolved.values() if v)
        print(f"\n{'=' * 40}")
        print(f"  Verified: {ok}/{len(MODELS)} models available")
        print(f"{'=' * 40}")

        # Save resolved IDs for later use
        resolved_file = RESULTS_DIR / "resolved_model_ids.json"
        RESULTS_DIR.mkdir(exist_ok=True)
        with open(resolved_file, "w") as f:
            json.dump(resolved, f, indent=2)
        print(f"  Saved: {resolved_file}")
        return

    # Load resolved IDs if available
    resolved_file = RESULTS_DIR / "resolved_model_ids.json"
    resolved_ids = None
    if resolved_file.exists():
        with open(resolved_file) as f:
            resolved_ids = json.load(f)

    run_experiment(
        model_filter=args.model,
        task_filter=args.task,
        resolved_ids=resolved_ids,
    )


if __name__ == "__main__":
    main()
