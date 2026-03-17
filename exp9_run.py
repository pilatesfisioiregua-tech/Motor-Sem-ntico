#!/usr/bin/env python3
"""EXP 9 — De Sistema Cognitivo a Producto de Alto Valor.

5 modelos OS diseñan el producto final desde 5 perspectivas.
Fases: F0 (contexto+briefings) → F1 (diseño) → F2 (cruce) → F3 (síntesis) → F4 (report)
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent
PROJECT_DIR = BASE_DIR.parent  # omni-mind-cerebro
CTX_DIR = BASE_DIR / "context"
RESULTS_DIR = BASE_DIR / "results"
MOTOR = PROJECT_DIR / "Motor" / "Meta-Red de preguntas inteligencias"
CTX_SRC = PROJECT_DIR / "Contexto"

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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"
)

MODELS = {
    "step35": {
        "id": "stepfun/step-3.5-flash",
        "name": "Step 3.5 Flash",
        "perspective": "Producto — ¿qué producto concreto construyes con estos datos?",
    },
    "cogito": {
        "id": "deepcogito/cogito-v2.1-671b",
        "name": "Cogito 671B",
        "perspective": "Valor — ¿dónde está el valor real para el usuario final?",
    },
    "kimi": {
        "id": "moonshotai/kimi-k2.5",
        "name": "Kimi K2.5",
        "perspective": "Arquitectura final — ¿cómo se ensamblan todas las piezas?",
    },
    "deepseek": {
        "id": "deepseek/deepseek-chat-v3-0324",
        "name": "DeepSeek V3.2",
        "perspective": "Implementación — ¿qué se construye primero y cómo?",
    },
    "nemotron": {
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "name": "Nemotron Super",
        "perspective": "Negocio — ¿cómo se convierte esto en algo que la gente pague?",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS (from exp8)
# ═══════════════════════════════════════════════════════════════════════════════

def strip_think_tags(text: str) -> str:
    if not text:
        return ""
    stripped = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL).strip()
    if stripped:
        return stripped
    if "<think>" in text:
        parts = text.split("<think>")
        for part in reversed(parts):
            clean = part.strip()
            if clean and not clean.startswith("</think>"):
                return clean
    return text.strip()


def call_openrouter(
    model_id: str, system_prompt: str, user_prompt: str,
    max_tokens: int = 16384, temperature: float = 0.7,
    timeout_s: int = 600, label: str = ""
) -> dict:
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
        print(f"  [{label}] Calling {model_id}...", flush=True)
        input_chars = len(system_prompt + user_prompt)
        print(f"  [{label}] Input: {input_chars:,} chars (~{input_chars//4:,} tokens)", flush=True)
        start = time.time()
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-H", "HTTP-Referer: https://omni-mind.app",
            "-H", "X-Title: OMNI-MIND Exp9",
            "-d", f"@{tmpfile}"
        ], capture_output=True, text=True, timeout=timeout_s)
        elapsed = time.time() - start
        if result.returncode != 0:
            return {"error": f"curl failed: {result.stderr}", "time_s": elapsed, "tokens_out": 0}
        resp = json.loads(result.stdout)
        if "error" in resp:
            return {"error": resp["error"], "time_s": elapsed, "tokens_out": 0}
        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        content = strip_think_tags(content)
        usage = resp.get("usage", {})
        tokens_in = usage.get("prompt_tokens", 0)
        tokens_out = usage.get("completion_tokens", 0)
        cost = float(usage.get("total_cost", 0) or 0)
        print(f"  [{label}] Done in {elapsed:.0f}s — {tokens_in:,} in / {tokens_out:,} out — ${cost:.4f}", flush=True)
        return {
            "content": content, "time_s": round(elapsed, 1),
            "tokens_in": tokens_in, "tokens_out": tokens_out,
            "cost": cost, "model": model_id,
            "error": None if content else "Empty response"
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout ({timeout_s}s)", "time_s": timeout_s, "tokens_out": 0}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode: {e}", "time_s": 0, "tokens_out": 0}
    except Exception as e:
        return {"error": str(e), "time_s": 0, "tokens_out": 0}
    finally:
        os.unlink(tmpfile)


def save_result(filename: str, content: str):
    path = RESULTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path} ({len(content):,} chars)", flush=True)


def read_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR: {e}]"


def section(title: str, content: str) -> str:
    sep = "=" * 80
    return f"\n\n{sep}\n# {title}\n{sep}\n\n{content}\n"


def truncate_to(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    cut = content[:max_chars].rfind("\n\n")
    if cut == -1:
        cut = max_chars
    return content[:cut] + f"\n\n[...truncado a {max_chars//1000}K chars...]"


def extract_firmas_brief(content: str) -> str:
    lines = content.split("\n")
    result_lines = []
    in_firma = False
    for line in lines:
        upper = line.upper().strip()
        if "FIRMA" in upper or "RESUMEN" in upper:
            in_firma = True
            result_lines.append(line)
            continue
        if in_firma:
            if line.strip() == "" and len(result_lines) > 2:
                in_firma = False
                result_lines.append("")
            elif line.startswith("##") or line.startswith("# "):
                in_firma = False
            else:
                result_lines.append(line)
                if len(result_lines) > 8:
                    in_firma = False
    if not result_lines:
        non_empty = [l for l in lines if l.strip() and not l.startswith("#")][:3]
        return "\n".join(non_empty)
    return "\n".join(result_lines)


def extract_sections_by_number(content: str, section_nums: list[str]) -> str:
    lines = content.split("\n")
    result = []
    capturing = False
    for line in lines:
        if line.startswith("## "):
            rest = line[3:].strip()
            matched = False
            for num in section_nums:
                if rest.startswith(f"{num}.") or rest.startswith(f"{num} "):
                    for suffix in ["", "A", "B", "C", "D", "E", "F"]:
                        if rest.startswith(f"{num}{suffix}"):
                            matched = True
                            break
                if matched:
                    break
            if matched:
                capturing = True
                result.append(line)
                continue
            elif capturing:
                capturing = False
                result.append("\n---\n")
                continue
        if capturing:
            result.append(line)
    return "\n".join(result) if result else ""


# ═══════════════════════════════════════════════════════════════════════════════
# EXPERIMENT RESULTS BLOCK (the core context for exp9)
# ═══════════════════════════════════════════════════════════════════════════════

EXPERIMENT_RESULTS_BLOCK = """
=== EXP 4 — MESA REDONDA MULTI-MODELO (12 modelos, 2 rondas) ===

HALLAZGOS:
- Mesa evaluadora producción: V3.2-chat + V3.1 + R1 = 100% cobertura con prompts especializados
- Sintetizador: Cogito-671b #1 sin discusión (3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s)
- Qwen3 inflador (+0.93 vs media global). NO cerebro. 77% de convergencias hacia donde Qwen3 apuntaba en R1
- Auto-tracking inflaba +0.93 puntos. Evaluación externa Claude: media 3.06 (vs auto 3.99)
- Pizarra distribuida: 425 conexiones + 239 puntos ciegos (valor exclusivo). GPT-OSS mayor contribuidor (119), no Qwen3 (63)
- Kimi K2 INERTE (0/5 R2). GLM-4.7 marginal. Opus $75/M 0 únicos. Sonnet 0 únicos.

DECISIONES VALIDADAS:
- Mesa producción: V3.2-chat + V3.1 + R1
- Sintetizador: Cogito-671b
- Pizarra (Tier 4): 7 modelos → Cogito sintetiza → panel evaluador externo valida
- Descartados: Opus, Sonnet, Kimi K2, GLM-4.7


=== EXP 5 — CADENA DE MONTAJE (8 configs × 5 tasks = 40 runs) ===

| Config | T1(TS) | T2(SQL) | T3(Py) | T4(Orch) | T5(Asm) | Media | Coste |
|--------|--------|---------|--------|----------|---------|-------|-------|
| A Industrial (7 est.) | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| D Ultra-Barato (5 est.) | 0% | 80% | 90% | 0% | 86% | 51% | $0.05 |
| B Coder Puro (5 est.) | 0% | 93% | 91% | 0% | 0% | 37% | $0.14 |
| G Razonadores (7 est.) | 0% | 0% | 90% | 0% | 75% | 33% | $0.19 |
| 0 Baseline (1 est.) | 0% | 0% | 83% | 0% | 75% | 32% | $0.03 |

HALLAZGOS:
1. Pipeline lineal: techo 56%. NO reemplaza a Code
2. T4 (Orquestador async): 0% en 8/8 configs — techo ESTRUCTURAL
3. Config D Pareto: 51% a $0.05 — 7x más barato que A para -5%
4. Premium PEOR: 15% a $0.34 — pagar más NO ayuda
5. Debugger poco eficaz: 5/35 mejoras. Reviewer ROMPE código funcional (3 casos)


=== EXP 1 BIS — 6 MODELOS NUEVOS (6 × 5 tareas = 30 runs) ===

| Modelo | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Step 3.5 Flash | 1.00 | 0.89 | 1.00 | 1.00 | 1.00 | 0.98 | $0.019 |
| Nemotron Super | 1.00 | 0.88 | 1.00 | 0.90 | 1.00 | 0.96 | $0.007 |
| MiMo V2 Flash | 1.00 | 0.89 | 0.60 | 1.00 | 1.00 | 0.90 | $0.001 |
| Devstral | 1.00 | 0.50 | 0.80 | 1.00 | 1.00 | 0.86 | $0.004 |
| Kimi K2.5 | 0.81 | 0.89 | 0.80 | 0.80 | 1.00 | 0.86 | $0.038 |
| Qwen 3.5 397B | 0.59 | 0.88 | 0.80 | 1.00 | 1.00 | 0.85 | $0.033 |

HALLAZGOS:
1. Step 3.5 Flash #1 overall (0.98), MiMo ratio absurdo (0.90 a $0.001)
2. T5 Síntesis: 6/6 modelos 1.00 — TODOS sintetizan bien
3. Devstral: coding specialist (T4=1.00)
4. Todos los roles cubiertos: evaluador, debugger, pizarra, patcher, math, tier barato


=== EXP 5b — MODELOS NUEVOS EN PIPELINE ===

| Config | T1 | T4 |
|--------|:---:|:---:|
| N2_cheap (MiMo+Nemotron+Step) | 100% | 0% |
| N3_coding (Step+Devstral) | 100% | 0% |

HALLAZGOS:
1. T1 RESUELTO: 0%→100% con modelos nuevos
2. T4 SIGUE 0%: think-tag blowup + async mocking imposible
3. Regla skip-E5/E6 VALIDADA: reviewer/optimizer rompen código funcional


=== EXP 6 — AGENTE DE CODING OS (loop agéntico, 460 líneas) ===

| Approach | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exp 5 Config A | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| **Agente multi-modelo** | **100%** | **100%** | **100%** | **93%** | **100%** | **99%** | $1.57 |
| Agente Devstral solo | 83% | — | — | **100%** | — | — | $0.66 |
| Agente MiMo solo | 79% | — | — | 96% | — | — | $0.92 |

HALLAZGOS:
1. T4 RESUELTO: 0% en 11 configs pipeline → 93% con agente (13/14 tests)
2. Devstral solo = 100% en T4 a $0.66
3. Step 0% en T4 como agente — piensa sin actuar
4. MiMo+loop (88%) SUPERA pipeline caro sin loop (56%)
5. 460 líneas bastan. Loop > cantidad de modelos
6. Si tests pasan 100% → finish() inmediato (reviewers rompen código)

AGENTE: 5 herramientas (read_file, write_file, run_command, list_dir, search_files) + finish
ROUTING: Devstral (genera) → Step (debugea tras 2 errores) → MiMo (fallback)
SEGURIDAD: sandbox path, command blacklist, stuck detection


=== EXP 7 — REDISEÑO CHIEF OS (5 modelos, 3 rondas) ===

DISEÑO CONSENSUADO: 8 componentes
1. Dispatcher Inteligente 2. Evaluador de Respuesta 3. Planificador Razonamiento
4. Matriz Cognitiva Adapter ($0) 5. Agente de Coding 6. Monitor Rendimiento
7. Optimizador Configuración 8. Logger & Telemetría ($0)
COSTE: $0.0013/turno (15x bajo target)
PROBLEMA: 4/10 checks vs Maestro fallan (estigmergia, 8 ops, pipeline 7 pasos, enjambre código)


=== EXP 8 — AUDITORÍA COMPLETA (5 modelos, 3 rondas) ===

CONSENSO 5/5:
1. Chief deprecado vs operativo — contradicción crítica (D1)
2. No hay corrección de errores (C5)
3. Modelo negocio no validado (C3)
4. Supabase vs fly.io insostenible (D2)
5. Sobrediseño: 17 tipos pensamiento + 6 modos (B3/B4)
6. UI/UX no especificada (C2)
7. Cross-dominio no demostrado (C4)
8. Componentes teóricos sin validación (B1)
9. MVP sobrediseñado (E6)
10. Dependencia Sonnet en 12 agentes (D3)

DECISIONES CR0: Eliminar Chief, migrar fly.io, eliminar Sonnet del MVP,
podar componentes teóricos, MVP con 6 INTs irreducibles, presupuesto realista


=== MAPA DEFINITIVO DE MODELOS OS ===

| Modelo | Score | Coste | Rol óptimo |
|--------|:---:|:---:|------------|
| Step 3.5 Flash | 0.98 | $0.019 | Debugger, Evaluador, Razonador |
| Nemotron Super | 0.96 | $0.007 | Validador numérico, Evaluador |
| MiMo V2 Flash | 0.90 | $0.001 | Workhorse, Arquitecto, Fallback |
| Devstral | 0.86 | $0.004 | Agente coding, Implementador |
| Kimi K2.5 | 0.86 | $0.038 | Pizarra, Auditor contexto largo |
| Qwen 3.5 397B | 0.85 | $0.033 | Evaluador, Implementador |
| Cogito 671B | #1 sint. | $0.125 | Sintetizador mesa redonda |
| DeepSeek V3.2 | — | $1.10/M | Diseño, Orquestación |

REGLAS EMPÍRICAS:
1. Loop > modelos: MiMo+loop (88%) supera pipeline caro sin loop (56%)
2. Barato+bueno > caro+solo: MiMo $0.001 con 0.90
3. Diversidad > calidad individual
4. Reviewers rompen código: si tests 100% → PARAR
5. Think-tag blowup: Step/Qwen gastan 16K pensando sin output
6. Devstral = agente coding ideal: rápido (4-10s), barato ($0.004), T4=100%


=== COSTES REALES ===

| Experimento | Estimado | Real | Factor |
|-------------|----------|------|--------|
| Exp 5 (40 runs) | $5-15 | $1.50 | 3-10x sobrestimado |
| Exp 1 bis (30 runs) | $1-3 | $0.10 | 10-30x sobrestimado |
| Exp 6 (agente) | $3-6 | $1.57 | 2-4x sobrestimado |
| Exp 7 (15 calls) | $3-5 | $0.15 | 20-33x sobrestimado |
| TOTAL 6 exps | $14-33 | ~$5.50 | 3-6x sobrestimado |
"""


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0 — COMPILE CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

def compile_exp_reports() -> str:
    """Compile actual experiment report files."""
    parts = []
    report_files = [
        (BASE_DIR / "motor_v1_validation/results/exp4_mesa_redonda_report.md", "EXP 4 — Mesa Redonda Report"),
        (BASE_DIR / "motor_v1_validation/results/exp4_2_sintetizador_report.md", "EXP 4.2 — Sintetizador Report"),
        (BASE_DIR / "motor_v1_validation/results/exp4_3_mente_distribuida_report.md", "EXP 4.3 — Mente Distribuida"),
        (BASE_DIR / "motor_v1_validation/results/exp5_report.md", "EXP 5 — Cadena de Montaje"),
        (RESULTS_DIR / "exp5b_report.md", "EXP 5b — Modelos Nuevos"),
        (RESULTS_DIR / "exp1bis_report.md", "EXP 1 BIS — 6 Modelos Nuevos"),
        (BASE_DIR / "motor_v1_validation/results/exp6_openhands_analysis.md", "EXP 6 — OpenHands"),
        (RESULTS_DIR / "exp7_report.md", "EXP 7 — Rediseño Chief"),
        (RESULTS_DIR / "exp8_synthesis.md", "EXP 8 — Auditoría Síntesis"),
    ]
    for path, title in report_files:
        if path.exists():
            parts.append(f"### {title}\n\n{read_file(path)}\n")
    # Exp 7 individual results
    for f in sorted(RESULTS_DIR.glob("exp7_r1_*.md")):
        parts.append(f"### EXP 7 R1 — {f.stem}\n\n{read_file(f)}\n")
    return "\n".join(parts)


def compile_full_context() -> str:
    """Full context for Kimi K2.5 (1M window)."""
    parts = []
    parts.append("# OMNI-MIND — CONTEXTO COMPLETO PARA DISEÑO DE PRODUCTO\n")
    parts.append(f"## EXP 9 — Fecha: {datetime.now().strftime('%Y-%m-%d')}\n---\n")

    # BLOQUE 1: Experiment results summary (structured)
    parts.append(section("BLOQUE 1: RESULTADOS EXPERIMENTALES (RESUMEN ESTRUCTURADO)", EXPERIMENT_RESULTS_BLOCK))

    # BLOQUE 1b: Actual experiment reports
    parts.append(section("BLOQUE 1b: REPORTES EXPERIMENTALES COMPLETOS", compile_exp_reports()))

    # BLOQUE 2: Maestro completo
    parts.append(section(
        "DOCUMENTO MAESTRO — SISTEMA COGNITIVO OMNI-MIND v4",
        read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # BLOQUE 3: L0 + META_RED
    parts.append(section(
        "L0: ALGEBRA DEL CALCULO SEMANTICO",
        read_file(MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md")
    ))
    parts.append(section(
        "META-RED DE INTELIGENCIAS",
        read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    ))
    parts.append(section(
        "TABLA PERIODICA DE LA INTELIGENCIA",
        read_file(MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md")
    ))

    # BLOQUE 4: Implementation state
    parts.append(section(
        "CONTEXTO SISTEMA (implementación actual)",
        read_file(CTX_SRC / "CONTEXTO_SISTEMA.md")
    ))
    parts.append(section(
        "MEMORY (estado operativo)",
        read_file(CTX_SRC / "MEMORY.md")
    ))

    # BLOQUE 5: Architecture docs
    parts.append(section(
        "ARQUITECTURA MECANISMOS MULTI-MODELO",
        read_file(BASE_DIR / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md")
    ))
    parts.append(section(
        "MAPA DE MODELOS OS",
        read_file(BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    # BLOQUE 6: Cartography
    parts.append(section(
        "CARTOGRAFIA OUTPUT FINAL",
        read_file(MOTOR / "OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md")
    ))

    # BLOQUE 7: Previous designs
    parts.append(section(
        "DISEÑO MOTOR SEMANTICO v1 (selección)",
        truncate_to(read_file(BASE_DIR / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md"), 40000)
    ))

    # BLOQUE 8: Firmas de 18 INTs
    resultados = MOTOR / "resultados"
    if resultados.exists():
        firma_parts = []
        for f in sorted(resultados.glob("*.md")):
            firma_parts.append(f"**{f.stem}:** {extract_firmas_brief(read_file(f))[:300]}")
        parts.append(section("18 INTELIGENCIAS — FIRMAS", "\n\n".join(firma_parts)))

    # BLOQUE 9: Exp 8 full audit results
    parts.append(section("EXP 8 — AUDITORÍA R1 (5 auditorías)", ""))
    for key in ["kimi", "step35", "cogito", "deepseek", "nemotron"]:
        r1 = RESULTS_DIR / f"exp8_r1_{key}.md"
        if r1.exists():
            parts.append(f"\n### Auditoría {key}\n\n{read_file(r1)}\n")
    parts.append(section("EXP 8 — SÍNTESIS CONSOLIDADA", read_file(RESULTS_DIR / "exp8_synthesis.md")))

    return "\n".join(parts)


def compile_standard_context() -> str:
    """Standard context (~80K tokens) for 128K models."""
    parts = []
    parts.append("# OMNI-MIND — CONTEXTO PARA DISEÑO DE PRODUCTO\n")
    parts.append(f"## EXP 9 — Versión standard\n---\n")

    # Experiment results (structured) — MOST IMPORTANT
    parts.append(section("RESULTADOS EXPERIMENTALES", EXPERIMENT_RESULTS_BLOCK))

    # Maestro completo
    parts.append(section(
        "[COMPLETO] DOCUMENTO MAESTRO v4",
        read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # Exp 8 synthesis
    parts.append(section(
        "[COMPLETO] EXP 8 SÍNTESIS (auditoría)",
        read_file(RESULTS_DIR / "exp8_synthesis.md")
    ))

    # META_RED
    parts.append(section(
        "[COMPLETO] META-RED INTELIGENCIAS",
        read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    ))

    # MAPA_MODELOS
    parts.append(section(
        "[COMPLETO] MAPA MODELOS OS",
        read_file(BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    # Condensed docs
    parts.append(section("[CONDENSADO] CONTEXTO SISTEMA",
        truncate_to(read_file(CTX_SRC / "CONTEXTO_SISTEMA.md"), 32000)))
    parts.append(section("[CONDENSADO] ARQUITECTURA MULTI-MODELO",
        truncate_to(read_file(BASE_DIR / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md"), 8000)))

    # Experiment reports
    parts.append(section("[COMPLETO] REPORTES EXPERIMENTALES", compile_exp_reports()))

    return "\n".join(parts)


def phase0():
    """Compile context and generate Kimi briefings."""
    print("\n" + "=" * 60)
    print("PHASE 0 — COMPILING CONTEXT + KIMI BRIEFINGS")
    print("=" * 60)

    CTX_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Create exp9_all_experiments.md (experiment results block)
    all_exp_path = CTX_DIR / "exp9_all_experiments.md"
    all_exp_path.write_text(EXPERIMENT_RESULTS_BLOCK, encoding="utf-8")
    print(f"  exp9_all_experiments.md: {len(EXPERIMENT_RESULTS_BLOCK):,} chars")

    # Compile full context
    print("\n  Compiling full context...", flush=True)
    full = compile_full_context()
    full_path = CTX_DIR / "exp9_full.md"
    full_path.write_text(full, encoding="utf-8")
    print(f"  Full: {len(full):,} chars (~{len(full)//4:,} tokens)")

    # Compile standard context
    print("  Compiling standard context...", flush=True)
    standard = compile_standard_context()
    std_path = CTX_DIR / "exp9_standard.md"
    std_path.write_text(standard, encoding="utf-8")
    print(f"  Standard: {len(standard):,} chars (~{len(standard)//4:,} tokens)")

    # Kimi briefings (4 calls, one per auditor except Kimi itself)
    print("\n  Generating Kimi briefings...", flush=True)
    briefing_specs = {
        "step35": ("Producto", "diseñador de producto que quiere saber qué producto concreto construir"),
        "cogito": ("Valor", "analista que busca dónde está el valor real para el usuario final"),
        "deepseek": ("Implementación", "ingeniero que necesita saber qué construir primero y cómo"),
        "nemotron": ("Negocio", "estratega de negocio que quiere convertir esto en algo que la gente pague"),
    }

    for key, (perspective, description) in briefing_specs.items():
        brief_path = CTX_DIR / f"exp9_brief_{key}.md"
        if brief_path.exists() and brief_path.stat().st_size > 2000:
            print(f"  Existing briefing for {key}: {brief_path.stat().st_size:,} chars — skipping")
            continue

        system_prompt = f"""Eres el director de un ejercicio de diseño de producto para OMNI-MIND.
Tienes el sistema COMPLETO. Prepara UN briefing personalizado para un {description}.

Perspectiva: {perspective}

REGLAS:
- Máximo ~15.000 palabras
- NO resumas — copia secciones relevantes TAL CUAL
- Incluye SIEMPRE: todos los resultados experimentales (Exp 4, 5, 5b, 1bis, 6, 7, 8) COMPLETOS
- Incluye SIEMPRE: mapa de modelos OS con costes
- Incluye SIEMPRE: síntesis de auditoría Exp 8
- Para Producto/Valor: incluir Maestro §1-§4, firmas de inteligencias, casos de uso
- Para Implementación: incluir CONTEXTO_SISTEMA, pipeline, agente Exp 6
- Para Negocio: incluir costes reales, presupuestos, roadmap, modelos competidores"""

        result = call_openrouter(
            model_id="moonshotai/kimi-k2.5",
            system_prompt=system_prompt,
            user_prompt=full,
            max_tokens=16384, temperature=0.3,
            timeout_s=600, label=f"F0-brief-{key}"
        )

        if result.get("content") and len(result["content"]) > 1000:
            brief_path.write_text(result["content"], encoding="utf-8")
            print(f"  Saved briefing {key}: {len(result['content']):,} chars (~{len(result['content'])//4:,} tokens)")
        else:
            print(f"  WARNING: briefing for {key} failed — will use standard context")

    print("\nPhase 0 complete.")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — R1: PRODUCT DESIGN
# ═══════════════════════════════════════════════════════════════════════════════

R1_SYSTEM = """Eres diseñador de producto experto. Se te presentan los resultados de 6 experimentos empíricos sobre un sistema cognitivo llamado OMNI-MIND, más su diseño completo.

Tu perspectiva es: {perspective}

OMNI-MIND tiene:
- Una Matriz 3L×7F×18INT que organiza TODO el conocimiento (validada empíricamente)
- Un agente de coding OS de 460 líneas que logra 99% en 5 tareas (incluida una que 11 pipelines no pudieron)
- 10+ modelos OS mapeados con roles específicos (datos de 6 experimentos)
- Coste real de operación: $0.001-$1.57 por tarea
- Una auditoría que dice: el núcleo es sólido pero hay sobrediseño, contradicciones, y modelo de negocio no validado

Tu tarea: NO auditar. DISEÑAR.

Responde:

1. PRODUCTO
   - ¿Qué producto concreto se puede construir HOY con lo que existe?
   - ¿Quién es el usuario? ¿Qué problema le resuelve?
   - ¿Cuál es el "wow moment" — el instante donde el usuario dice "esto es increíble"?
   - ¿Cuál es la diferencia con ChatGPT/Claude/Gemini que justifica pagar?

2. VALOR
   - ¿Dónde está el valor REAL basado en los datos experimentales?
   - ¿Qué pueden hacer los modelos OS que NO pueden los chatbots genéricos?
   - ¿La Matriz 3L×7F aporta valor perceptible al usuario o es infraestructura invisible?
   - ¿El multi-modelo (enjambre) aporta valor vs un solo modelo bueno?

3. ARQUITECTURA MÍNIMA VIABLE
   - Con los datos de Exp 6 (agente 460 líneas, 99%), ¿cuál es la arquitectura mínima?
   - ¿Cuántos componentes realmente necesitas?
   - ¿Qué se elimina del diseño actual sin perder valor?
   - ¿Qué se añade que no está diseñado?

4. IMPLEMENTACIÓN
   - ¿Qué se puede construir en 1 semana? ¿En 1 mes? ¿En 3 meses?
   - ¿Cuál es la secuencia que maximiza aprendizaje con mínimo esfuerzo?
   - ¿Qué del agente de Exp 6 se reutiliza directamente?
   - ¿Coste realista por mes de operación?

5. NEGOCIO
   - ¿€50-200/mes es el precio correcto? ¿Para quién?
   - ¿Cuál es el modelo: SaaS, servicio, API, otro?
   - ¿Qué competidores reales hay y cómo se diferencia?
   - ¿Pilotos propios → amigo informático → escala es la ruta correcta?

6. RIESGOS
   - ¿Cuál es el riesgo #1 que mata el proyecto?
   - ¿Qué asunción no validada es la más peligrosa?
   - ¿Qué pasa si el flywheel (cross-dominio) no funciona?

Sé concreto. Usa datos de los experimentos. No teorices."""


def get_context_for_model(key: str) -> str:
    """Get appropriate context for each model."""
    if key == "kimi":
        return (CTX_DIR / "exp9_full.md").read_text(encoding="utf-8")

    # Try Kimi briefing + standard
    brief_path = CTX_DIR / f"exp9_brief_{key}.md"
    std_path = CTX_DIR / "exp9_standard.md"
    standard = std_path.read_text(encoding="utf-8") if std_path.exists() else ""

    if brief_path.exists():
        brief = brief_path.read_text(encoding="utf-8")
        if len(brief) > 1000:
            total = len(brief) + len(standard)
            if total // 4 < 95000:
                return f"## GUÍA DE PERSPECTIVA\n\n{brief}\n\n---\n\n## DOCUMENTACIÓN COMPLETA\n\n{standard}"

    return standard


def phase1():
    """Run R1 product design with all 5 models."""
    print("\n" + "=" * 60)
    print("PHASE 1 — R1: PRODUCT DESIGN (5 models)")
    print("=" * 60)

    results = {}
    for key, model in MODELS.items():
        print(f"\n--- {model['name']} ({key}) ---")

        # Check if result already exists
        existing = RESULTS_DIR / f"exp9_r1_{key}.md"
        if existing.exists() and existing.stat().st_size > 2000:
            print(f"  Existing result: {existing.stat().st_size:,} chars — skipping")
            results[key] = {"content": existing.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}
            continue

        context = get_context_for_model(key)
        system_prompt = R1_SYSTEM.format(perspective=model["perspective"])

        result = call_openrouter(
            model_id=model["id"],
            system_prompt=system_prompt,
            user_prompt=f"CONTEXTO OMNI-MIND:\n\n{context}",
            max_tokens=16384, temperature=0.7,
            timeout_s=600, label=f"R1-{key}"
        )

        results[key] = result
        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        else:
            save_result(f"exp9_r1_{key}.md", result["content"])

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — R2: PIZARRA DISTRIBUIDA
# ═══════════════════════════════════════════════════════════════════════════════

R2_SYSTEM = """5 propuestas de diseño de producto para OMNI-MIND. Cada una desde perspectiva diferente.

NO evalúes ni puntúes. En vez de eso:

1. CONEXIONES (mínimo 5):
   Identifica conexiones entre propuestas que ningún autor individual vio.
   Formato: "Propuesta X dice [A]. Propuesta Y dice [B]. La conexión que ninguno vio: [C]"

2. PUNTOS CIEGOS (mínimo 3):
   ¿Qué asumen TODAS las propuestas sin cuestionarlo?
   ¿Qué no menciona NINGUNA propuesta pero es crítico?

3. CONTRADICCIONES (mínimo 2):
   ¿Dónde dicen cosas opuestas? ¿Cuál tiene razón y por qué?

4. LA IDEA QUE FALTA:
   Basado en los datos experimentales Y las 5 propuestas,
   ¿hay una idea de producto o implementación que NADIE propuso pero que los datos sugieren?

5. TU MERGE:
   Construye tu propuesta final tomando lo mejor de las 5 + tus conexiones + la idea que falta."""


def phase2(r1_results: dict):
    """Pizarra distribuida — connections, blind spots, contradictions, merge."""
    print("\n" + "=" * 60)
    print("PHASE 2 — R2: PIZARRA DISTRIBUIDA")
    print("=" * 60)

    # Compile all R1 results
    doc = ""
    for key, r in r1_results.items():
        if r.get("content"):
            doc += f"\n\n{'='*60}\n## PROPUESTA: {MODELS[key]['name']} — {MODELS[key]['perspective']}\n{'='*60}\n\n{r['content']}"

    results = {}
    for key, model in MODELS.items():
        print(f"\n--- {model['name']} ({key}) ---")

        existing = RESULTS_DIR / f"exp9_r2_{key}.md"
        if existing.exists() and existing.stat().st_size > 1000:
            print(f"  Existing: {existing.stat().st_size:,} chars — skipping")
            results[key] = {"content": existing.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}
            continue

        result = call_openrouter(
            model_id=model["id"],
            system_prompt=R2_SYSTEM,
            user_prompt=doc,
            max_tokens=12288, temperature=0.5,
            timeout_s=600, label=f"R2-{key}"
        )
        results[key] = result
        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        else:
            save_result(f"exp9_r2_{key}.md", result["content"])

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════

SYNTHESIS_PROMPT = """Aquí tienes 5 propuestas de diseño de producto + 5 pizarras distribuidas (conexiones, puntos ciegos, contradicciones, ideas que faltan, y merges) de OMNI-MIND.

Produce:

1. PRODUCTO FINAL
   - Nombre, tagline, usuario objetivo
   - Problema que resuelve (1 párrafo)
   - "Wow moment" definitivo
   - Diferenciación vs competidores

2. ARQUITECTURA DEFINITIVA
   - Componentes (con número exacto)
   - Modelo asignado a cada componente (con dato empírico)
   - Flujo de un turno de chat
   - Flujo de pensamiento profundo
   - Flujo de ejecución de código

3. MVP EN 4 SEMANAS
   - Semana 1: qué
   - Semana 2: qué
   - Semana 3: qué
   - Semana 4: qué
   - Coste total estimado

4. MODELO DE NEGOCIO
   - Precio y para quién
   - Coste por cliente por mes
   - Ruta de go-to-market
   - Primer hito de validación

5. LAS 3 DECISIONES QUE HACEN O ROMPEN EL PROYECTO"""


def phase3(r1: dict, r2: dict):
    """Synthesis with Cogito 671B."""
    print("\n" + "=" * 60)
    print("PHASE 3 — SYNTHESIS")
    print("=" * 60)

    doc = "# PROPUESTAS R1\n\n"
    for key, r in r1.items():
        if r.get("content"):
            doc += f"\n## {MODELS[key]['name']}\n\n{r['content']}\n"
    doc += "\n\n# PIZARRAS DISTRIBUIDAS R2\n\n"
    for key, r in r2.items():
        if r.get("content"):
            doc += f"\n## {MODELS[key]['name']}\n\n{r['content']}\n"

    result = call_openrouter(
        model_id="deepcogito/cogito-v2.1-671b",
        system_prompt=SYNTHESIS_PROMPT,
        user_prompt=doc,
        max_tokens=16384, temperature=0.3,
        timeout_s=600, label="F3-synthesis"
    )

    if result.get("error"):
        print(f"  Cogito failed: {result['error']} — trying Kimi fallback")
        result = call_openrouter(
            model_id="moonshotai/kimi-k2.5",
            system_prompt=SYNTHESIS_PROMPT,
            user_prompt=doc,
            max_tokens=16384, temperature=0.3,
            timeout_s=600, label="F3-fallback"
        )

    if result.get("content"):
        save_result("exp9_synthesis.md", result["content"])
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def phase4(r1: dict, r2: dict, synthesis: dict):
    """Generate final report and JSON."""
    print("\n" + "=" * 60)
    print("PHASE 4 — FINAL REPORT")
    print("=" * 60)

    parts = []
    parts.append("# EXP 9 — De Sistema Cognitivo a Producto de Alto Valor")
    parts.append(f"\n**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    parts.append(f"\n**Modelos:** {', '.join(m['name'] for m in MODELS.values())}")

    # Synthesis as executive summary
    parts.append("\n\n## 1. Síntesis del Producto Final\n")
    if synthesis.get("content"):
        parts.append(synthesis["content"])

    # Individual proposals
    parts.append("\n\n## 2. Propuestas Individuales (R1)\n")
    for key, r in r1.items():
        parts.append(f"\n### {MODELS[key]['name']} — {MODELS[key]['perspective']}\n")
        if r.get("content"):
            parts.append(r["content"])
        elif r.get("error"):
            parts.append(f"**ERROR:** {r['error']}")

    # Pizarra distribuida
    parts.append("\n\n## 3. Pizarra Distribuida (R2)\n")
    for key, r in r2.items():
        parts.append(f"\n### {MODELS[key]['name']}\n")
        if r.get("content"):
            parts.append(r["content"])

    report = "\n".join(parts)
    save_result("exp9_report.md", report)

    # JSON
    results_json = {
        "experiment": "exp9_product_design",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "models": {k: v["id"] for k, v in MODELS.items()},
        "r1_proposals": {k: {"chars": len(r.get("content", "")), "error": r.get("error")} for k, r in r1.items()},
        "r2_pizarras": {k: {"chars": len(r.get("content", "")), "error": r.get("error")} for k, r in r2.items()},
        "synthesis_chars": len(synthesis.get("content", "")),
    }
    json_path = RESULTS_DIR / "exp9_results.json"
    json_path.write_text(json.dumps(results_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved: {json_path}")
    print("\nEXP 9 COMPLETE.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="EXP 9 — Product Design")
    parser.add_argument("--phase", type=str, default="all", help="0, 1, 2, 3, 4, or all")
    args = parser.parse_args()
    phase = args.phase

    if phase in ("all", "0"):
        phase0()

    r1 = {}
    if phase in ("all", "1"):
        r1 = phase1()
    elif phase in ("2", "3", "4"):
        for key in MODELS:
            path = RESULTS_DIR / f"exp9_r1_{key}.md"
            if path.exists():
                r1[key] = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    r2 = {}
    if phase in ("all", "2"):
        r2 = phase2(r1)
    elif phase in ("3", "4"):
        for key in MODELS:
            path = RESULTS_DIR / f"exp9_r2_{key}.md"
            if path.exists():
                r2[key] = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    synthesis = {}
    if phase in ("all", "3"):
        synthesis = phase3(r1, r2)
    elif phase == "4":
        path = RESULTS_DIR / "exp9_synthesis.md"
        if path.exists():
            synthesis = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    if phase in ("all", "4"):
        phase4(r1, r2, synthesis)


if __name__ == "__main__":
    main()
