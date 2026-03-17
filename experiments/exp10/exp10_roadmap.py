#!/usr/bin/env python3
"""EXP 10 — Roadmap OMNI-MIND por Enjambre (8 modelos con estigmergia).

7 modelos activos + Cogito sintetizador. 2 rondas + síntesis.
Contexto asimétrico: max (Kimi), full (V3.2/Qwen3/GPT-OSS), compact (R1/Step/Nemotron).
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent.parent  # motor-semantico/
PROJECT_DIR = BASE_DIR.parent  # omni-mind-cerebro/
RESULTS_DIR = BASE_DIR / "results" / "exp10"
MOTOR = PROJECT_DIR / "Motor" / "Meta-Red de preguntas inteligencias"
CTX_SRC = PROJECT_DIR / "Contexto"

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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"
)

# Verified model IDs (all confirmed on OpenRouter 2026-03-11)
MODELS = {
    "kimi": {
        "id": "moonshotai/kimi-k2.5",
        "name": "Kimi K2.5",
        "ctx_window": 262144,
        "context_level": "full",
        "role": "Auditor, perspectiva amplia",
        "dato": "Auditor en Exp 8 (31 preguntas, contexto largo)",
    },
    "v32": {
        "id": "deepseek/deepseek-chat-v3-0324",
        "name": "V3.2-chat",
        "ctx_window": 128000,
        "context_level": "full",
        "role": "Arquitectura, evaluación principal",
        "dato": "89.5% cobertura, líder mesa especializada",
    },
    "qwen3": {
        "id": "qwen/qwen3-235b-a22b",
        "name": "Qwen3-235B",
        "ctx_window": 131072,
        "context_level": "full",
        "role": "Generalista amplio, conecta ideas",
        "dato": "Cerebro de mesa genérica, 63 contrib pizarra",
    },
    "gptoss": {
        "id": "openai/gpt-4.1-mini",
        "name": "GPT-OSS",
        "ctx_window": 1047576,
        "context_level": "max",
        "role": "Ve TODO sin comprimir. Auditor de contexto completo + motor productivo",
        "dato": "119 contrib pizarra (#1), el más prolífico. 1M ventana",
    },
    "r1": {
        "id": "deepseek/deepseek-r1",
        "name": "R1",
        "ctx_window": 64000,
        "context_level": "compact",
        "role": "Razonamiento profundo, detectar contradicciones",
        "dato": "2.18 Matriz, 100% cobertura con V3.2",
    },
    "step": {
        "id": "stepfun/step-3.5-flash",
        "name": "Step 3.5 Flash",
        "ctx_window": 256000,
        "context_level": "compact",
        "role": "Rigor lógico, evaluar viabilidad",
        "dato": "0.98 score (#1 benchmarks)",
    },
    "nemotron": {
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "name": "Nemotron Super",
        "ctx_window": 131072,
        "context_level": "compact",
        "role": "Validación numérica, costes, timelines",
        "dato": "0.96 score, MATH-500 97.4",
    },
}

SYNTHESIZER = {
    "id": "deepcogito/cogito-v2.1-671b",
    "name": "Cogito 671B",
    "ctx_window": 128000,
    "role": "Sintetizador final",
    "dato": "#1 sintetizador, 3.6 conexiones/output",
}

# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def strip_think_tags(text: str) -> str:
    if not text:
        return ""
    stripped = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL).strip()
    if stripped:
        return stripped
    if "<think>" in text:
        parts = text.split("</think>")
        for part in reversed(parts):
            clean = part.strip()
            if clean and "<think>" not in clean:
                return clean
    return text.strip()


def extract_thinking(text: str) -> str:
    """Extract think content separately (for saving)."""
    matches = re.findall(r"<think>([\s\S]*?)</think>", text, flags=re.DOTALL)
    return "\n---\n".join(matches) if matches else ""


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def truncate_to(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    cut = content[:max_chars].rfind("\n\n")
    if cut == -1:
        cut = max_chars
    return content[:cut] + f"\n\n[...truncado a {max_chars//1000}K chars...]"


def section(title: str, content: str) -> str:
    return f"\n{'='*60}\n# {title}\n{'='*60}\n\n{content}\n"


def call_openrouter_sync(
    model_id: str, system_prompt: str, user_prompt: str,
    max_tokens: int = 3000, temperature: float = 0.7,
    timeout_s: int = 300, label: str = ""
) -> dict:
    """Synchronous OpenRouter call via subprocess+curl."""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f, ensure_ascii=False)
        tmpfile = f.name
    try:
        input_chars = len(system_prompt + user_prompt)
        print(f"  [{label}] → {model_id} ({input_chars:,} chars, ~{input_chars//4:,} tok)", flush=True)
        start = time.time()
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-H", "HTTP-Referer: https://omni-mind.app",
            "-H", "X-Title: OMNI-MIND Exp10",
            "-d", f"@{tmpfile}"
        ], capture_output=True, text=True, timeout=timeout_s)
        elapsed = time.time() - start

        if result.returncode != 0:
            return {"error": f"curl failed: {result.stderr}", "time_s": round(elapsed, 1),
                    "tokens_in": 0, "tokens_out": 0, "cost": 0}

        resp = json.loads(result.stdout)
        if "error" in resp:
            err_msg = resp["error"].get("message", str(resp["error"])) if isinstance(resp["error"], dict) else str(resp["error"])
            return {"error": err_msg, "time_s": round(elapsed, 1),
                    "tokens_in": 0, "tokens_out": 0, "cost": 0}

        raw_content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        content = strip_think_tags(raw_content)
        thinking = extract_thinking(raw_content)
        usage = resp.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        cost = float(usage.get("total_cost", 0) or 0)

        print(f"  [{label}] ✓ {elapsed:.0f}s — {tokens_in:,}in/{tokens_out:,}out — ${cost:.4f}", flush=True)
        return {
            "content": content, "thinking": thinking, "raw": raw_content,
            "time_s": round(elapsed, 1), "tokens_in": tokens_in, "tokens_out": tokens_out,
            "cost": cost, "model": model_id,
            "error": None if content else "Empty response"
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout ({timeout_s}s)", "time_s": timeout_s,
                "tokens_in": 0, "tokens_out": 0, "cost": 0}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode: {e}", "time_s": 0,
                "tokens_in": 0, "tokens_out": 0, "cost": 0}
    except Exception as e:
        return {"error": str(e), "time_s": 0,
                "tokens_in": 0, "tokens_out": 0, "cost": 0}
    finally:
        os.unlink(tmpfile)


async def call_openrouter(
    model_id: str, system_prompt: str, user_prompt: str,
    max_tokens: int = 3000, temperature: float = 0.7,
    timeout_s: int = 300, label: str = ""
) -> dict:
    """Async wrapper — runs sync call in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, call_openrouter_sync,
        model_id, system_prompt, user_prompt,
        max_tokens, temperature, timeout_s, label
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT COMPILATION
# ═══════════════════════════════════════════════════════════════════════════════

def collect_project_docs() -> dict[str, str]:
    """Collect all relevant .md files from the project, keyed by relative path."""
    docs = {}
    search_dirs = [
        (BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md", None),
        (BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO.md", None),
        (BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_v2.md", None),
        (BASE_DIR / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md", None),
        (BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md", None),
        (BASE_DIR / "ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md", None),
        (BASE_DIR / "ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md", None),
        (BASE_DIR / "ACTUALIZACION_MAESTRO_SESION_11_MAR.md", None),
        (BASE_DIR / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md", None),
        (BASE_DIR / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md", None),
        (CTX_SRC / "CONTEXTO_SISTEMA.md", None),
        (CTX_SRC / "MEMORY.md", None),
        (CTX_SRC / "architecture.md", None),
        (CTX_SRC / "chief-pipeline.md", None),
        (CTX_SRC / "enjambre-diseno.md", None),
        (CTX_SRC / "patterns.md", None),
    ]
    # Motor docs
    motor_files = [
        MOTOR / "META_RED_INTELIGENCIAS_CR0.md",
        MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md",
        MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md",
        MOTOR / "OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md",
        MOTOR / "PROTOCOLO_CARTOGRAFIA_META_RED_v1.md",
    ]
    # Motor specs
    motor_specs = list((PROJECT_DIR / "Motor").glob("SPEC_*.md"))
    motor_specs += list((PROJECT_DIR / "Motor").glob("ADDENDUM_*.md"))

    # Individual intelligence results
    int_results = list((MOTOR / "resultados").glob("*.md")) if (MOTOR / "resultados").exists() else []

    # Experiment results (reports only)
    exp_reports = list((BASE_DIR / "results").glob("exp*_report.md"))
    exp_reports += list((BASE_DIR / "results").glob("exp*_synthesis.md"))
    exp_reports += [
        BASE_DIR / "results" / "exp1bis_report.md",
        BASE_DIR / "results" / "exp5b_report.md",
    ]
    # Validation reports
    val_dir = BASE_DIR / "motor_v1_validation" / "results"
    if val_dir.exists():
        exp_reports += list(val_dir.glob("*.md"))

    # SO docs
    so_files = list((PROJECT_DIR / "SO").glob("*.md"))
    so_files += list((PROJECT_DIR / "SO" / "estado actual").glob("*.md")) if (PROJECT_DIR / "SO" / "estado actual").exists() else []
    so_files += list((PROJECT_DIR / "SO" / "exocortex").glob("*.md")) if (PROJECT_DIR / "SO" / "exocortex").exists() else []

    # OMNI-MIND framework (select key docs)
    omni_dir = PROJECT_DIR / "OMNI-MIND"
    framework_files = [
        omni_dir / "01_FRAMEWORK" / "00_ARQUITECTURA.md",
        omni_dir / "01_FRAMEWORK" / "L0_adn_modelo_omni.md",
        omni_dir / "01_FRAMEWORK" / "L0.5_MECANISMO_UNIVERSAL_VINCULACION.md",
        omni_dir / "01_FRAMEWORK" / "L0.7_FUNCIONES_NUCLEARES.md",
        omni_dir / "01_FRAMEWORK" / "Constitucion.md",
        omni_dir / "01_FRAMEWORK" / "OMNI_ENGINE_VISION_PRODUCTO.md",
        omni_dir / "01_FRAMEWORK" / "MARCO_LINGUISTICO_COMPLETO.md",
    ]

    # Roadmaps
    roadmap_files = list((PROJECT_DIR / "Roadmaps").glob("*.md")) if (PROJECT_DIR / "Roadmaps").exists() else []

    all_files = []
    for item in search_dirs:
        all_files.append(item[0])
    all_files += motor_files + motor_specs + int_results + exp_reports
    all_files += so_files + framework_files + roadmap_files

    for f in all_files:
        if isinstance(f, Path) and f.exists():
            rel = str(f.relative_to(PROJECT_DIR))
            content = read_file(f)
            if content and len(content) > 50:
                docs[rel] = content

    return docs


def compile_context_max(docs: dict[str, str]) -> str:
    """Max context for Kimi (262k tokens ≈ ~1M chars). Include everything."""
    parts = ["# OMNI-MIND — DOCUMENTACIÓN COMPLETA\n"]
    for rel_path, content in sorted(docs.items()):
        parts.append(f"\n{'='*60}\n## {rel_path}\n{'='*60}\n\n{content}\n")
    full = "\n".join(parts)
    # Kimi has 262k tokens ≈ ~1M chars. Truncate if needed.
    return truncate_to(full, 900000)


def compile_context_full(docs: dict[str, str]) -> str:
    """Full context for V3.2, Qwen3, GPT-OSS (~100k tokens ≈ ~400k chars)."""
    priority_keys = [
        "motor-semantico/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md",
        "Contexto/CONTEXTO_SISTEMA.md",
        "Contexto/MEMORY.md",
        "motor-semantico/ARQUITECTURA_MECANISMOS_MULTI_MODELO.md",
        "motor-semantico/MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md",
        "motor-semantico/ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md",
        "motor-semantico/ACTUALIZACION_MAESTRO_SESION_11_MAR.md",
        "motor-semantico/ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md",
    ]
    # Motor core
    motor_keys = [k for k in docs if "META_RED_INTELIGENCIAS" in k or "ALGEBRA_CALCULO" in k
                  or "TABLA_PERIODICA" in k]
    # Experiment reports
    exp_keys = [k for k in docs if "results/exp" in k and ("report" in k.lower() or "synthesis" in k.lower())]
    # Architecture
    arch_keys = [k for k in docs if "ARQUITECTURA" in k or "DISENO_MOTOR" in k]
    # SO
    so_keys = [k for k in docs if k.startswith("SO/")]

    ordered = []
    seen = set()
    for k in priority_keys + motor_keys + exp_keys + arch_keys + so_keys:
        if k in docs and k not in seen:
            ordered.append(k)
            seen.add(k)
    # Add remaining docs
    for k in sorted(docs.keys()):
        if k not in seen:
            ordered.append(k)
            seen.add(k)

    parts = ["# OMNI-MIND — CONTEXTO COMPLETO\n"]
    total = 0
    max_chars = 380000  # ~95k tokens
    for key in ordered:
        content = docs[key]
        if total + len(content) > max_chars:
            # Try truncated version
            remaining = max_chars - total
            if remaining > 2000:
                parts.append(f"\n## {key}\n\n{truncate_to(content, remaining)}\n")
            break
        parts.append(f"\n## {key}\n\n{content}\n")
        total += len(content)

    return "\n".join(parts)


def compile_context_compact(docs: dict[str, str]) -> str:
    """Compact context for R1, Step, Nemotron (~50k tokens ≈ ~200k chars)."""
    essential_keys = [
        "motor-semantico/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md",
        "Contexto/CONTEXTO_SISTEMA.md",
        "Contexto/MEMORY.md",
        "motor-semantico/ARQUITECTURA_MECANISMOS_MULTI_MODELO.md",
        "motor-semantico/MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md",
        "motor-semantico/ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md",
        "motor-semantico/ACTUALIZACION_MAESTRO_SESION_11_MAR.md",
    ]
    exp_keys = [k for k in sorted(docs.keys()) if "results/exp" in k
                and ("report" in k.lower() or "synthesis" in k.lower())]

    parts = ["# OMNI-MIND — CONTEXTO ESENCIAL\n"]
    total = 0
    max_chars = 180000  # ~45k tokens

    for key in essential_keys:
        if key in docs:
            content = docs[key]
            # Truncate Maestro if needed
            if "MAESTRO" in key and len(content) > 60000:
                content = truncate_to(content, 60000)
            if total + len(content) > max_chars:
                content = truncate_to(content, max_chars - total)
            parts.append(f"\n## {key}\n\n{content}\n")
            total += len(content)

    for key in exp_keys:
        if key in docs and total < max_chars:
            content = docs[key]
            if total + len(content) > max_chars:
                content = truncate_to(content, max_chars - total)
            parts.append(f"\n## {key}\n\n{content}\n")
            total += len(content)

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """Eres un arquitecto de sistemas que diseña roadmaps de producto tecnológico.
Tienes acceso a documentación de un proyecto llamado OMNI-MIND — un sistema cognitivo basado en una Matriz 3 Lentes × 7 Funciones × 18 Inteligencias, implementado como enjambres de modelos OS.

Tu trabajo: diseñar un roadmap REALISTA para convertir este proyecto en un sistema digital funcional y vendible.

Reglas:
- Solo incluir lo que tiene datos empíricos que lo soportan
- Ser brutal sobre qué es real y qué es teoría inflada o sobrediseño
- Priorizar por: qué genera valor AHORA con lo que ya existe
- Cada item del roadmap debe tener: qué, por qué, dependencias, coste estimado, tiempo estimado
- Señalar explícitamente qué partes del proyecto deberían ELIMINARSE o simplificarse
- No ser complaciente. Si el proyecto tiene problemas fundamentales, decirlo
- Pensar en: quién paga por esto, cuándo, y cuánto"""


def make_r1_user_prompt(context: str) -> str:
    return f"""DOCUMENTACIÓN DEL PROYECTO OMNI-MIND:

{context}

---

Diseña el roadmap para que OMNI-MIND se convierta en un sistema digital real, funcional y vendible.
Sé brutal: qué funciona, qué es humo, qué se construye primero, qué se tira a la basura."""


def make_r2_user_prompt(context: str, pizarra: str) -> str:
    return f"""{context}

---

PIZARRA DEL ENJAMBRE — Ronda 1 (lo que propusieron los otros modelos):

{pizarra}

---

Has leído lo que los otros modelos proponen como roadmap.
Cada uno tiene un expertise diferente. Ahora:
1. ¿Dónde hay consenso fuerte (3+ modelos coinciden)? Eso es señal.
2. ¿Dónde hay divergencia importante? ¿Quién tiene razón y por qué?
3. ¿Qué no vio NINGUNO de los otros que tú sí ves?
4. Tu roadmap revisado, incorporando lo mejor de todos y descartando lo peor."""


def make_synthesis_prompt(r1_results: dict, r2_results: dict) -> str:
    parts = ["PREGUNTA: Diseñar el roadmap realista de OMNI-MIND como sistema digital funcional y vendible.\n"]
    parts.append("\nPIZARRA COMPLETA DEL ENJAMBRE (7 modelos × 2 rondas):\n")
    parts.append("\n=== RONDA 1 (exploración independiente) ===\n")
    for key, model in MODELS.items():
        r = r1_results.get(key, {})
        content = r.get("content", "[no response]")
        parts.append(f"\n[{model['name']} — {model['role']}]:\n{content}\n")

    parts.append("\n=== RONDA 2 (enriquecimiento — cada modelo leyó a los otros 6) ===\n")
    for key, model in MODELS.items():
        r = r2_results.get(key, {})
        content = r.get("content", "[no response]")
        parts.append(f"\n[{model['name']}]:\n{content}\n")

    parts.append("""
---

Integra los 14 bloques en UN roadmap final coherente:

1. CONSENSO FUERTE: Qué se construye primero (ítems donde 4+ modelos coinciden)
2. ELIMINAR: Qué se tira o simplifica (consenso del enjambre)
3. DIVERGENCIAS: Puntos donde el enjambre no se pone de acuerdo — presentar como CR0 con opciones para que Jesús decida
4. TIMELINE: Realista, con dependencias entre ítems
5. COSTES: Estimación por fase (infra, APIs, tiempo)
6. BRUTAL HONESTY: Qué sigue siendo teoría sin validar, qué es real
7. MODELO DE NEGOCIO: Si algún modelo lo mencionó — quién paga, cuándo, cuánto

No seas complaciente. Si el enjambre dice que algo es humo, es humo.""")
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

async def run_round1(contexts: dict[str, str]) -> dict:
    """Run R1 in parallel for all 7 models."""
    print("\n" + "=" * 60)
    print("RONDA 1 — EXPLORACIÓN INDEPENDIENTE (7 modelos en paralelo)")
    print("=" * 60, flush=True)

    results = {}
    # Check for existing results
    tasks_to_run = {}
    for key, model in MODELS.items():
        existing = RESULTS_DIR / f"exp10_r1_{key}.md"
        if existing.exists() and existing.stat().st_size > 500:
            print(f"  [{key}] Existing: {existing.stat().st_size:,} chars — skipping", flush=True)
            results[key] = {"content": read_file(existing), "time_s": 0,
                           "tokens_in": 0, "tokens_out": 0, "cost": 0, "error": None}
        else:
            tasks_to_run[key] = model

    if tasks_to_run:
        async def run_one(key, model):
            ctx = contexts[model["context_level"]]
            user_prompt = make_r1_user_prompt(ctx)
            return key, await call_openrouter(
                model["id"], SYSTEM_PROMPT, user_prompt,
                max_tokens=3000, temperature=0.7,
                timeout_s=300, label=f"R1-{key}"
            )

        coros = [run_one(k, m) for k, m in tasks_to_run.items()]
        for coro in asyncio.as_completed(coros):
            key, result = await coro
            results[key] = result
            if result.get("error"):
                print(f"  [{key}] ERROR: {result['error']}", flush=True)
                # Retry once
                print(f"  [{key}] Retrying...", flush=True)
                model = MODELS[key]
                ctx = contexts[model["context_level"]]
                user_prompt = make_r1_user_prompt(ctx)
                retry = await call_openrouter(
                    model["id"], SYSTEM_PROMPT, user_prompt,
                    max_tokens=3000, temperature=0.7,
                    timeout_s=300, label=f"R1-{key}-retry"
                )
                if not retry.get("error"):
                    results[key] = retry
            # Save
            if results[key].get("content"):
                path = RESULTS_DIR / f"exp10_r1_{key}.md"
                path.write_text(results[key]["content"], encoding="utf-8")
                print(f"  [{key}] Saved: {path.name} ({len(results[key]['content']):,} chars)", flush=True)
                # Save thinking separately if present
                if results[key].get("thinking"):
                    think_path = RESULTS_DIR / f"exp10_r1_{key}_thinking.md"
                    think_path.write_text(results[key]["thinking"], encoding="utf-8")

    return results


async def run_round2(contexts: dict[str, str], r1_results: dict) -> dict:
    """Run R2 with stigmergy — each model reads others' R1."""
    print("\n" + "=" * 60)
    print("RONDA 2 — ESTIGMERGIA (7 modelos leen a los otros 6)")
    print("=" * 60, flush=True)

    results = {}
    tasks_to_run = {}
    for key, model in MODELS.items():
        existing = RESULTS_DIR / f"exp10_r2_{key}.md"
        if existing.exists() and existing.stat().st_size > 500:
            print(f"  [{key}] Existing: {existing.stat().st_size:,} chars — skipping", flush=True)
            results[key] = {"content": read_file(existing), "time_s": 0,
                           "tokens_in": 0, "tokens_out": 0, "cost": 0, "error": None,
                           "pizarra_compressed": False}
        else:
            tasks_to_run[key] = model

    if tasks_to_run:
        # Build pizarra for each model (exclude self)
        def build_pizarra(exclude_key: str, compress: bool = False) -> str:
            parts = []
            for k, m in MODELS.items():
                if k == exclude_key:
                    continue
                r = r1_results.get(k, {})
                content = r.get("content", "[no response]")
                if compress and len(content) > 6000:
                    content = content[:6000] + "\n[...comprimido...]"
                parts.append(f"[{m['name']} — {m['role']}]:\n{content}\n")
            return "\n".join(parts)

        async def run_one(key, model):
            ctx = contexts[model["context_level"]]
            # Check if pizarra fits in context window
            pizarra_full = build_pizarra(key, compress=False)
            total_chars = len(ctx) + len(pizarra_full)
            total_tokens_est = total_chars // 4
            compressed = False

            # If total exceeds ~80% of context window, compress pizarra
            if total_tokens_est > model["ctx_window"] * 0.75:
                pizarra = build_pizarra(key, compress=True)
                compressed = True
                print(f"  [{key}] Pizarra comprimida ({total_tokens_est:,} tok > {int(model['ctx_window']*0.75):,})", flush=True)
            else:
                pizarra = pizarra_full

            user_prompt = make_r2_user_prompt(ctx, pizarra)
            result = await call_openrouter(
                model["id"], SYSTEM_PROMPT, user_prompt,
                max_tokens=3000, temperature=0.5,
                timeout_s=300, label=f"R2-{key}"
            )
            result["pizarra_compressed"] = compressed
            return key, result

        coros = [run_one(k, m) for k, m in tasks_to_run.items()]
        for coro in asyncio.as_completed(coros):
            key, result = await coro
            results[key] = result
            if result.get("error"):
                print(f"  [{key}] ERROR: {result['error']}", flush=True)
                # Retry once
                print(f"  [{key}] Retrying...", flush=True)
                model = MODELS[key]
                ctx = contexts[model["context_level"]]
                pizarra = build_pizarra(key, compress=True)
                user_prompt = make_r2_user_prompt(ctx, pizarra)
                retry = await call_openrouter(
                    model["id"], SYSTEM_PROMPT, user_prompt,
                    max_tokens=3000, temperature=0.5,
                    timeout_s=300, label=f"R2-{key}-retry"
                )
                if not retry.get("error"):
                    retry["pizarra_compressed"] = True
                    results[key] = retry
            # Save
            if results[key].get("content"):
                path = RESULTS_DIR / f"exp10_r2_{key}.md"
                path.write_text(results[key]["content"], encoding="utf-8")
                print(f"  [{key}] Saved: {path.name} ({len(results[key]['content']):,} chars)", flush=True)
                if results[key].get("thinking"):
                    think_path = RESULTS_DIR / f"exp10_r2_{key}_thinking.md"
                    think_path.write_text(results[key]["thinking"], encoding="utf-8")

    return results


async def run_synthesis(r1_results: dict, r2_results: dict) -> dict:
    """Run Cogito synthesis."""
    print("\n" + "=" * 60)
    print("SÍNTESIS — COGITO 671B")
    print("=" * 60, flush=True)

    existing = RESULTS_DIR / "exp10_synthesis.md"
    if existing.exists() and existing.stat().st_size > 500:
        print(f"  Existing: {existing.stat().st_size:,} chars — skipping", flush=True)
        return {"content": read_file(existing), "time_s": 0,
                "tokens_in": 0, "tokens_out": 0, "cost": 0, "error": None}

    user_prompt = make_synthesis_prompt(r1_results, r2_results)

    # Check if prompt fits Cogito's 128k window
    total_chars = len(SYSTEM_PROMPT) + len(user_prompt)
    compressed = False
    if total_chars // 4 > 100000:
        # Compress: truncate R1 responses to 4000 chars each, keep R2 full
        print(f"  Pizarra for synthesis too large ({total_chars//4:,} tok). Compressing R1...", flush=True)
        compressed_r1 = {}
        for key, r in r1_results.items():
            compressed_r1[key] = dict(r)
            if r.get("content") and len(r["content"]) > 4000:
                compressed_r1[key]["content"] = r["content"][:4000] + "\n[...comprimido...]"
        user_prompt = make_synthesis_prompt(compressed_r1, r2_results)
        compressed = True

    result = await call_openrouter(
        SYNTHESIZER["id"], SYSTEM_PROMPT, user_prompt,
        max_tokens=5000, temperature=0.3,
        timeout_s=600, label="Synthesis-Cogito"
    )

    if result.get("error"):
        print(f"  Cogito failed: {result['error']}. Trying Kimi fallback...", flush=True)
        result = await call_openrouter(
            "moonshotai/kimi-k2.5", SYSTEM_PROMPT, user_prompt,
            max_tokens=5000, temperature=0.3,
            timeout_s=600, label="Synthesis-Kimi-fallback"
        )

    result["pizarra_compressed"] = compressed
    if result.get("content"):
        existing.write_text(result["content"], encoding="utf-8")
        print(f"  Saved: exp10_synthesis.md ({len(result['content']):,} chars)", flush=True)

    return result


def save_meta(contexts: dict, r1: dict, r2: dict, synthesis: dict, total_start: float):
    """Save exp10_meta.json."""
    total_time = time.time() - total_start
    total_cost = sum(r.get("cost", 0) for r in r1.values())
    total_cost += sum(r.get("cost", 0) for r in r2.values())
    total_cost += synthesis.get("cost", 0)

    failed = [k for k, r in {**r1, **r2}.items() if r.get("error")]

    meta = {
        "timestamp": datetime.now().isoformat(),
        "experiment": "exp10_roadmap_enjambre",
        "description": "7 modelos + Cogito diseñan roadmap OMNI-MIND con estigmergia",
        "models": {},
        "context_sizes": {
            "max_tokens": len(contexts["max"]) // 4,
            "full_tokens": len(contexts["full"]) // 4,
            "compact_tokens": len(contexts["compact"]) // 4,
        },
        "ronda1": {},
        "ronda2": {},
        "synthesis": {
            "model": synthesis.get("model", SYNTHESIZER["id"]),
            "latency_s": synthesis.get("time_s", 0),
            "tokens_in": synthesis.get("tokens_in", 0),
            "tokens_out": synthesis.get("tokens_out", 0),
            "cost_usd": synthesis.get("cost", 0),
            "status": "ok" if not synthesis.get("error") else "error",
            "pizarra_compressed": synthesis.get("pizarra_compressed", False),
            "error": synthesis.get("error"),
        },
        "total_cost_usd": round(total_cost, 4),
        "total_latency_s": round(total_time, 1),
        "models_failed": failed,
        "notes": "",
    }

    for key, model in MODELS.items():
        meta["models"][key] = {
            "id": model["id"],
            "name": model["name"],
            "provider": "openrouter",
            "context_level": model["context_level"],
        }

    for key in MODELS:
        r = r1.get(key, {})
        meta["ronda1"][key] = {
            "latency_s": r.get("time_s", 0),
            "tokens_in": r.get("tokens_in", 0),
            "tokens_out": r.get("tokens_out", 0),
            "cost_usd": r.get("cost", 0),
            "status": "ok" if not r.get("error") else "error",
            "error": r.get("error"),
        }
        r2_r = r2.get(key, {})
        meta["ronda2"][key] = {
            "latency_s": r2_r.get("time_s", 0),
            "tokens_in": r2_r.get("tokens_in", 0),
            "tokens_out": r2_r.get("tokens_out", 0),
            "cost_usd": r2_r.get("cost", 0),
            "status": "ok" if not r2_r.get("error") else "error",
            "pizarra_compressed": r2_r.get("pizarra_compressed", False),
            "error": r2_r.get("error"),
        }

    meta["models"]["cogito"] = {
        "id": SYNTHESIZER["id"],
        "name": SYNTHESIZER["name"],
        "provider": "openrouter",
        "role": "synthesizer",
    }

    meta_path = RESULTS_DIR / "exp10_meta.json"
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Saved: exp10_meta.json", flush=True)
    return meta


def print_summary(meta: dict, synthesis: dict):
    """Print final summary."""
    print("\n" + "=" * 60)
    print("=== EXP 10 COMPLETE ===")
    print("=" * 60)
    print(f"Models: 7 active + 1 synthesizer")
    ctx = meta["context_sizes"]
    print(f"Context: max={ctx['max_tokens']//1000}k / full={ctx['full_tokens']//1000}k / compact={ctx['compact_tokens']//1000}k tokens\n")

    print("Ronda 1 (parallel):")
    for key in MODELS:
        r = meta["ronda1"][key]
        status = "✓" if r["status"] == "ok" else "✗"
        print(f"  {status} {MODELS[key]['name']:20s} {r['tokens_out']:5d} tok, {r['latency_s']:5.0f}s, ${r['cost_usd']:.4f}")

    print("\nRonda 2 (parallel, estigmergia):")
    for key in MODELS:
        r = meta["ronda2"][key]
        status = "✓" if r["status"] == "ok" else "✗"
        comp = " [compressed]" if r.get("pizarra_compressed") else ""
        print(f"  {status} {MODELS[key]['name']:20s} {r['tokens_out']:5d} tok, {r['latency_s']:5.0f}s, ${r['cost_usd']:.4f}{comp}")

    s = meta["synthesis"]
    print(f"\nSynthesis (Cogito):")
    print(f"  {s['tokens_out']} tok, {s['latency_s']:.0f}s, ${s['cost_usd']:.4f}")

    print(f"\nTotal: ${meta['total_cost_usd']:.4f}, {meta['total_latency_s']:.0f}s")
    print(f"Failed: {meta['models_failed'] or 'none'}")
    print(f"Files: results/exp10/")

    print("\n" + "=" * 60)
    print("=== SYNTHESIS ===")
    print("=" * 60)
    print(synthesis.get("content", "[no synthesis]"))
    print(flush=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    total_start = time.time()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Compile contexts
    print("=" * 60)
    print("PASO 0 — COMPILANDO CONTEXTO ASIMÉTRICO")
    print("=" * 60, flush=True)

    docs = collect_project_docs()
    print(f"  Documentos encontrados: {len(docs)}", flush=True)
    total_chars = sum(len(v) for v in docs.values())
    print(f"  Total: {total_chars:,} chars (~{total_chars//4:,} tokens)", flush=True)

    contexts = {
        "max": compile_context_max(docs),
        "full": compile_context_full(docs),
        "compact": compile_context_compact(docs),
    }

    for level, content in contexts.items():
        print(f"  context_{level}: {len(content):,} chars (~{len(content)//4:,} tokens)", flush=True)
        # Save context files for reference
        (RESULTS_DIR / f"context_{level}.md").write_text(content, encoding="utf-8")

    # Step 2: Round 1
    r1_results = await run_round1(contexts)

    # Step 3: Round 2
    r2_results = await run_round2(contexts, r1_results)

    # Step 4: Synthesis
    synthesis = await run_synthesis(r1_results, r2_results)

    # Step 5: Save meta + print summary
    meta = save_meta(contexts, r1_results, r2_results, synthesis, total_start)
    print_summary(meta, synthesis)


if __name__ == "__main__":
    asyncio.run(main())
