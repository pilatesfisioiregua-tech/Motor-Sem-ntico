#!/usr/bin/env python3
"""EXP 8 — Auditoría Completa del Sistema Cognitivo OMNI-MIND.

5 modelos OS auditan el sistema completo desde 5 perspectivas.
Fases: F0 (contexto) → F0b (Kimi briefings) → F1 (auditorías) → F2 (cruce) → F3 (síntesis) → F4 (report)
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

OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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"
)

MODELS = {
    "kimi": {
        "id": "moonshotai/kimi-k2.5",
        "name": "Kimi K2.5",
        "perspective": "Enjambre y multi-modelo — ¿cómo orquestar múltiples modelos como agentes?",
        "ctx_window": 1_000_000,
        "context_version": "full",
    },
    "step35": {
        "id": "stepfun/step-3.5-flash",
        "name": "Step 3.5 Flash",
        "perspective": "Coherencia sistémica — ¿el sistema es lógicamente consistente consigo mismo?",
        "ctx_window": 128_000,
        "context_version": "briefing",  # Kimi-compiled briefing
    },
    "cogito": {
        "id": "deepcogito/cogito-v2.1-671b",
        "name": "Cogito 671B",
        "perspective": "Conexiones profundas — ¿qué patrones cruzan todo el sistema? ¿qué conecta qué?",
        "ctx_window": 128_000,
        "context_version": "briefing",
    },
    "deepseek": {
        "id": "deepseek/deepseek-chat-v3-0324",
        "name": "DeepSeek V3.2",
        "perspective": "Arquitectura técnica — ¿la estructura técnica soporta la visión?",
        "ctx_window": 128_000,
        "context_version": "briefing",
    },
    "nemotron": {
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "name": "Nemotron Super",
        "perspective": "Pragmatismo y coste — ¿qué se puede implementar HOY? ¿qué es código puro ($0) vs LLM?",
        "ctx_window": 128_000,
        "context_version": "briefing",
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
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
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 16384,
    temperature: float = 0.7,
    timeout_s: int = 600,
    label: str = ""
) -> dict:
    """Call OpenRouter API via subprocess+curl."""
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
        print(f"  [{label}] Calling {model_id}...")
        print(f"  [{label}] Input: {len(system_prompt + user_prompt):,} chars (~{(len(system_prompt + user_prompt))//4:,} tokens)")
        start = time.time()
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-H", "HTTP-Referer: https://omni-mind.app",
            "-H", "X-Title: OMNI-MIND Exp8",
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
        cost = float(resp.get("usage", {}).get("total_cost", 0) or 0)

        print(f"  [{label}] Done in {elapsed:.0f}s — {tokens_in:,} in / {tokens_out:,} out — ${cost:.4f}")

        return {
            "content": content,
            "time_s": round(elapsed, 1),
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost": cost,
            "model": model_id,
            "error": None if content else "Empty response after stripping think tags"
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Timeout ({timeout_s}s)", "time_s": timeout_s, "tokens_out": 0}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}", "time_s": 0, "tokens_out": 0}
    except Exception as e:
        return {"error": str(e), "time_s": 0, "tokens_out": 0}
    finally:
        os.unlink(tmpfile)


def save_result(filename: str, content: str):
    """Save a result file."""
    path = RESULTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"  Saved: {path} ({len(content):,} chars)")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0 — COMPILE CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

def read_file(path: Path) -> str:
    """Read file content or return error."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR: {e}]"


def section(title: str, content: str) -> str:
    """Wrap content in a section separator."""
    sep = "=" * 80
    return f"\n\n{sep}\n# {title}\n{sep}\n\n{content}\n"


def truncate_to(content: str, max_chars: int) -> str:
    """Truncate content at paragraph break."""
    if len(content) <= max_chars:
        return content
    cut = content[:max_chars].rfind("\n\n")
    if cut == -1:
        cut = max_chars
    return content[:cut] + f"\n\n[...truncado a {max_chars//1000}K chars...]"


def extract_sections_by_number(content: str, section_nums: list[str]) -> str:
    """Extract sections from a document by section number (e.g., '4', '5', '8').

    Looks for headings like '## 4. ENJAMBRES' or '## 4 ENJAMBRES'.
    Captures until the next ## heading of same or higher level.
    """
    lines = content.split("\n")
    result = []
    capturing = False

    for i, line in enumerate(lines):
        # Check if this is a ## heading matching one of our target sections
        if line.startswith("## "):
            # Check if any section number matches
            rest = line[3:].strip()
            matched = False
            for num in section_nums:
                # Match "## 4." or "## 4 " or "## 4A" patterns
                if rest.startswith(f"{num}.") or rest.startswith(f"{num} ") or rest.startswith(f"{num}A") or rest.startswith(f"{num}B") or rest.startswith(f"{num}C") or rest.startswith(f"{num}D") or rest.startswith(f"{num}E") or rest.startswith(f"{num}F"):
                    matched = True
                    break
            if matched:
                capturing = True
                result.append(line)
                continue
            elif capturing:
                # Hit a new ## section that's NOT one of ours — stop
                capturing = False
                result.append("\n---\n")
                continue

        if capturing:
            result.append(line)

    return "\n".join(result) if result else ""


def extract_firmas_brief(content: str) -> str:
    """Extract 2-3 sentence firma from intelligence analysis."""
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
                    result_lines.append("")
    if not result_lines:
        # Fallback: first 3 non-empty lines
        non_empty = [l for l in lines if l.strip() and not l.startswith("#")][:3]
        return "\n".join(non_empty)
    return "\n".join(result_lines)


def compile_experiment_results() -> str:
    """Compile all experiment results into one section."""
    parts = []
    exp_files = [
        (BASE_DIR / "motor_v1_validation/results/exp4_mesa_redonda_report.md", "EXP 4 — Mesa Redonda Principal"),
        (BASE_DIR / "motor_v1_validation/results/exp4_1_comparison_report.md", "EXP 4.1 — Comparación"),
        (BASE_DIR / "motor_v1_validation/results/exp4_2_sintetizador_report.md", "EXP 4.2 — Sintetizador"),
        (BASE_DIR / "motor_v1_validation/results/exp4_3_mente_distribuida_report.md", "EXP 4.3 — Mente Distribuida"),
        (BASE_DIR / "motor_v1_validation/results/exp5_report.md", "EXP 5 — Cadena de Montaje"),
        (RESULTS_DIR / "exp5b_report.md", "EXP 5b — Modelos Nuevos en Pipeline"),
        (RESULTS_DIR / "exp1bis_report.md", "EXP 1 BIS — 6 Modelos Nuevos"),
        (BASE_DIR / "motor_v1_validation/results/exp6_openhands_analysis.md", "EXP 6 — OpenHands"),
    ]
    for path, title in exp_files:
        if path.exists():
            parts.append(f"### {title}\n\n{read_file(path)}\n")
    # Exp 7 results
    for f in sorted(RESULTS_DIR.glob("exp7*.md")):
        parts.append(f"### EXP 7 — {f.stem}\n\n{read_file(f)}\n")
    return "\n".join(parts)


# Paths
MOTOR = PROJECT_DIR / "Motor" / "Meta-Red de preguntas inteligencias"
CTX_SRC = PROJECT_DIR / "Contexto"


def compile_full() -> str:
    """VERSION FULL (~300K tokens) — Para Kimi K2.5."""
    parts = []
    parts.append("# OMNI-MIND v4 — SISTEMA COGNITIVO COMPLETO\n")
    parts.append("## Compilado para auditoría EXP 8 — Versión FULL\n")
    parts.append(f"## Fecha: {datetime.now().strftime('%Y-%m-%d')}\n---\n")

    # ═══ MAESTRO [COMPLETO] ═══
    parts.append(section(
        "DOCUMENTO MAESTRO — SISTEMA COGNITIVO OMNI-MIND v4 (§0-§13)",
        read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # ═══ L0 INVARIANTES ═══
    # L0_7 and L0_5 are embedded in Maestro. Álgebra is separate.
    parts.append(section(
        "L0: ALGEBRA DEL CALCULO SEMANTICO (CR0)",
        read_file(MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md")
    ))

    # ═══ CAPA L1 ═══
    parts.append(section(
        "L1: META-RED DE INTELIGENCIAS (CR0) — 18 redes de preguntas",
        read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    ))

    parts.append(section(
        "L1: TABLA PERIODICA DE LA INTELIGENCIA (CR0) — 18 álgebras con firmas",
        read_file(MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md")
    ))

    # ═══ IMPLEMENTACIÓN ═══
    parts.append(section(
        "CONTEXTO SISTEMA — Estado real de la implementación Supabase",
        read_file(CTX_SRC / "CONTEXTO_SISTEMA.md")
    ))

    parts.append(section(
        "MEMORY — Estado operativo del sistema nervioso",
        read_file(CTX_SRC / "MEMORY.md")
    ))

    # ═══ ARQUITECTURA MULTI-MODELO ═══
    parts.append(section(
        "ARQUITECTURA MECANISMOS MULTI-MODELO",
        read_file(BASE_DIR / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md")
    ))

    parts.append(section(
        "MAPA DE MODELOS OS — MARZO 2026",
        read_file(BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    parts.append(section(
        "ACTUALIZACION MAESTRO — PRINCIPIO 31 TIERS",
        read_file(BASE_DIR / "ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md")
    ))

    parts.append(section(
        "ACTUALIZACION MAESTRO — SESION 11 MARZO",
        read_file(BASE_DIR / "ACTUALIZACION_MAESTRO_SESION_11_MAR.md")
    ))

    # ═══ CARTOGRAFÍA ═══
    parts.append(section(
        "CARTOGRAFIA — OUTPUT FINAL (34 chats)",
        read_file(MOTOR / "OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md")
    ))

    parts.append(section(
        "CARTOGRAFIA — PROTOCOLO",
        read_file(MOTOR / "PROTOCOLO_CARTOGRAFIA_META_RED_v1.md")
    ))

    # ═══ VERSIONES ANTERIORES — Secciones clave ═══
    v1 = read_file(BASE_DIR / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md")
    v1_extracted = extract_sections_by_number(v1, ["1", "8", "9", "14"])
    if len(v1_extracted.strip()) < 500:
        v1_extracted = truncate_to(v1, 40000)
    parts.append(section(
        "DISEÑO MOTOR SEMANTICO v1 — Secciones clave (§1, §8, §9, §14)",
        v1_extracted
    ))

    v2 = read_file(BASE_DIR / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md")
    parts.append(section(
        "DISEÑO MOTOR SEMANTICO v2 — Cambios vs v1",
        truncate_to(v2, 30000)
    ))

    scv2 = read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_v2.md")
    scv2_extracted = extract_sections_by_number(scv2, ["1", "2", "8", "9"])
    if len(scv2_extracted.strip()) < 500:
        scv2_extracted = truncate_to(scv2, 30000)
    parts.append(section(
        "SISTEMA COGNITIVO v2 — §1 Qué es, §2, §8 Auto-diagnóstico, §9 Profundidad",
        scv2_extracted
    ))

    # ═══ 18 INTELIGENCIAS — FIRMAS ═══
    resultados = MOTOR / "resultados"
    if resultados.exists():
        firma_parts = []
        for f in sorted(resultados.glob("*.md")):
            firma_parts.append(f"### {f.stem}\n{extract_firmas_brief(read_file(f))}\n")
        parts.append(section(
            "18 INTELIGENCIAS — FIRMAS (2-3 frases cada una)",
            "\n".join(firma_parts)
        ))

    # ═══ OPERACIONES ALGEBRAICAS — Conclusiones ═══
    ops_parts = []
    fase3 = MOTOR / "Fase 3"
    fase4 = MOTOR / "Fase 4"
    for folder in [fase3, fase4]:
        if folder.exists():
            for f in sorted(folder.glob("*.md")):
                content = read_file(f)
                # Just take first 3000 chars as summary
                conclusion = truncate_to(content, 3000)
                ops_parts.append(f"### {f.stem}\n{conclusion}\n")
    parts.append(section(
        "OPERACIONES ALGEBRAICAS — Conclusiones",
        "\n".join(ops_parts)
    ))

    # ═══ CASO DE TEST — CLINICA (referencia) ═══
    clinica = MOTOR / "Fase 2 diferenciales" / "CLINICA.md"
    if clinica.exists():
        parts.append(section(
            "CASO DE TEST — CLINICA (benchmark completo)",
            read_file(clinica)
        ))

    # ═══ RESULTADOS EXPERIMENTALES ═══
    parts.append(section(
        "RESULTADOS EXPERIMENTALES",
        compile_experiment_results()
    ))

    # ═══ REPORTS ADICIONALES ═══
    for report_name in ["MATRIX_COVERAGE_REPORT.md", "MULTI_MODEL_COVERAGE_REPORT.md"]:
        rpath = BASE_DIR / "motor_v1_validation" / "results" / report_name
        if rpath.exists():
            parts.append(section(
                report_name.replace(".md", "").replace("_", " "),
                read_file(rpath)
            ))

    return "\n".join(parts)


def compile_standard() -> str:
    """VERSION STANDARD (~80K tokens) — Para modelos 128K (fallback)."""
    parts = []
    parts.append("# OMNI-MIND v4 — CONTEXTO STANDARD\n")
    parts.append("## EXP 8 — Versión standard (~80K tokens)\n---\n")

    # Maestro COMPLETO (~19K tokens) — NON-NEGOTIABLE
    parts.append(section(
        "[COMPLETO] DOCUMENTO MAESTRO v4",
        read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # CONTEXTO_SISTEMA — sections 4, 5 only (~8K tokens target)
    ctx_sys = read_file(CTX_SRC / "CONTEXTO_SISTEMA.md")
    ctx_extracted = extract_sections_by_number(ctx_sys, ["1", "4", "5"])
    if len(ctx_extracted.strip()) < 1000:
        ctx_extracted = truncate_to(ctx_sys, 32000)
    else:
        ctx_extracted = truncate_to(ctx_extracted, 32000)
    parts.append(section(
        "[SECCIONES] CONTEXTO SISTEMA (§1 Qué es, §4 Enjambres, §5 Compartidos)",
        ctx_extracted
    ))

    # META_RED completo (~12K tokens)
    parts.append(section(
        "[COMPLETO] META-RED DE INTELIGENCIAS",
        read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    ))

    # MAPA_MODELOS completo (~2K tokens)
    parts.append(section(
        "[COMPLETO] MAPA DE MODELOS OS",
        read_file(BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    # Condensados (~2K chars = ~500 words each, ~6K tokens total)
    for title, path in [
        ("L0: ALGEBRA CALCULO SEMANTICO", MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md"),
        ("ARQUITECTURA MECANISMOS MULTI-MODELO", BASE_DIR / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md"),
        ("TABLA PERIODICA INTELIGENCIA", MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md"),
    ]:
        parts.append(section(f"[CONDENSADO] {title}", truncate_to(read_file(path), 8000)))

    for title, path in [
        ("MEMORY", CTX_SRC / "MEMORY.md"),
        ("ACTUALIZACION PRINCIPIO 31 TIERS", BASE_DIR / "ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md"),
    ]:
        if path.exists():
            parts.append(section(f"[CONDENSADO] {title}", truncate_to(read_file(path), 4000)))

    # Firmas de 18 INTs (~3K tokens)
    resultados = MOTOR / "resultados"
    if resultados.exists():
        firma_parts = []
        for f in sorted(resultados.glob("*.md")):
            firma_parts.append(f"**{f.stem}:** {extract_firmas_brief(read_file(f))[:200]}")
        parts.append(section("[FIRMAS] 18 Inteligencias", "\n".join(firma_parts)))

    # Ops algebraicas — solo conclusiones (~1K token)
    ops_summary = """
Operaciones algebraicas validadas empíricamente:
- Fusión INT-01⊕INT-08 (SaaS): Validada, firma combinada correcta
- Composición INT-01→INT-08 (Startup SaaS): Validada, orden importa
- Distributividad: ~70% factorizable. (B|C)→A NO factorizable (valor irreducible)
- Asociatividad: confirmada con matices
- Clausura INT-07⊕INT-14: Resultado dentro del álgebra
- Saturación INT-03 (Clínica): Rendimiento decreciente > 3 pasadas
"""
    parts.append(section("[RESUMEN] OPERACIONES ALGEBRAICAS", ops_summary))

    # Resultados experimentales COMPLETOS (~12K tokens)
    parts.append(section(
        "[COMPLETO] RESULTADOS EXPERIMENTALES",
        compile_experiment_results()
    ))

    return "\n".join(parts)


def compile_mini() -> str:
    """VERSION MINI (~40K tokens) — Fallback."""
    parts = []
    parts.append("# OMNI-MIND v4 — CONTEXTO MINI\n")
    parts.append("## EXP 8 — Versión mini (~40K tokens)\n---\n")

    # Maestro — sections 0, 1, 4, 8, 11, 12 only (~12K tokens)
    maestro = read_file(BASE_DIR / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    m_extracted = extract_sections_by_number(maestro, ["0", "1", "4", "8", "11", "12"])
    if len(m_extracted.strip()) < 2000:
        m_extracted = truncate_to(maestro, 48000)
    parts.append(section("[CLAVE] MAESTRO v4 (§0,§1,§4,§8,§11,§12)", m_extracted))

    # CONTEXTO_SISTEMA — just enjambres list (~4K tokens)
    ctx_sys = read_file(CTX_SRC / "CONTEXTO_SISTEMA.md")
    ctx_extracted = extract_sections_by_number(ctx_sys, ["1", "4"])
    if len(ctx_extracted.strip()) < 500:
        ctx_extracted = truncate_to(ctx_sys, 16000)
    else:
        ctx_extracted = truncate_to(ctx_extracted, 16000)
    parts.append(section("[MINI] CONTEXTO SISTEMA (§1, §4 Enjambres)", ctx_extracted))

    # META_RED — first 12K chars (~3K tokens)
    meta_red = read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    parts.append(section("[MINI] META-RED 18 INTELIGENCIAS", truncate_to(meta_red, 12000)))

    # MAPA_MODELOS (~2K tokens)
    parts.append(section(
        "[COMPLETO] MAPA MODELOS",
        read_file(BASE_DIR / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    # Resultados experimentales COMPLETOS (~12K tokens)
    parts.append(section(
        "[COMPLETO] RESULTADOS EXPERIMENTALES",
        compile_experiment_results()
    ))

    return "\n".join(parts)


def phase0():
    """Compile 3 context versions."""
    print("\n" + "=" * 60)
    print("PHASE 0 — COMPILING CONTEXT VERSIONS")
    print("=" * 60)

    CTX_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for name, compiler in [("full", compile_full), ("standard", compile_standard), ("mini", compile_mini)]:
        print(f"\n  Compiling {name}...")
        content = compiler()
        path = CTX_DIR / f"exp8_{name}.md"
        path.write_text(content, encoding="utf-8")
        tokens = len(content) // 4
        print(f"  Written: {path}")
        print(f"  Size: {len(content):,} chars (~{tokens:,} tokens)")

    print("\nPhase 0 complete.")


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 0b — KIMI COMPILES BRIEFINGS
# ═══════════════════════════════════════════════════════════════════════════════

KIMI_BRIEFING_SPECS = {
    "step": {
        "auditor": "COHERENCIA SISTÉMICA (Step 3.5 Flash)",
        "focus": """¿El sistema es lógicamente consistente consigo mismo?
NECESITA: L0 completos (las 7 Funciones + 3 Lentes dentro del Maestro §2, Mecanismo Universal, Álgebra), Maestro completo, META_RED, propiedades algebraicas confirmadas/refutadas.
NO NECESITA: detalles de implementación Supabase, specs de reactores, casos de test."""
    },
    "cogito": {
        "auditor": "CONEXIONES PROFUNDAS (Cogito 671B)",
        "focus": """¿Qué patrones cruzan todo el sistema? ¿Qué conecta qué?
NECESITA: Maestro completo, 18 firmas de inteligencias, cartografía de pares complementarios, Gestor de la Matriz, flywheel cross-dominio.
NO NECESITA: detalles de infra, migraciones SQL, gateway specs."""
    },
    "deepseek": {
        "auditor": "ARQUITECTURA TÉCNICA (DeepSeek V3.2)",
        "focus": """¿La estructura técnica soporta la visión?
NECESITA: CONTEXTO_SISTEMA completo, Maestro §4-§8 (pipeline + infra), MAPA_MODELOS, ARQUITECTURA_MECANISMOS, pipeline del Motor.
NO NECESITA: cartografía detallada de inteligencias, operaciones algebraicas, casos de test."""
    },
    "nemotron": {
        "auditor": "PRAGMATISMO Y COSTE (Nemotron Super)",
        "focus": """¿Qué se puede implementar HOY? ¿Qué es código puro ($0) vs LLM?
NECESITA: Maestro §8 (infra) + §11 (roadmap), CONTEXTO_SISTEMA (costes reales), MAPA_MODELOS (precios), resultados de experimentos (costes reales), presupuestos del v1.
NO NECESITA: teoría de inteligencias, álgebra, cartografía, L0 filosófico."""
    },
}


def phase0b():
    """Send full context to Kimi to compile personalized briefings (1 call per auditor)."""
    print("\n" + "=" * 60)
    print("PHASE 0b — KIMI COMPILES BRIEFINGS (4 calls)")
    print("=" * 60)

    full_ctx = (CTX_DIR / "exp8_full.md").read_text(encoding="utf-8")
    print(f"  Full context: {len(full_ctx):,} chars (~{len(full_ctx)//4:,} tokens)")

    # Check if briefing for step already exists from previous run
    existing = {}
    for key in KIMI_BRIEFING_SPECS:
        path = CTX_DIR / f"exp8_brief_{key}.md"
        if path.exists():
            content = path.read_text(encoding="utf-8")
            if len(content) > 2000:
                existing[key] = True
                print(f"  Found existing briefing for {key}: {len(content):,} chars")

    success_count = len(existing)

    for key, spec in KIMI_BRIEFING_SPECS.items():
        if key in existing:
            continue

        system_prompt = f"""Eres el director de una auditoría del sistema cognitivo OMNI-MIND.
Tienes acceso al diseño COMPLETO del sistema.

Tu tarea: preparar UN briefing personalizado para este auditor:

AUDITOR: {spec['auditor']}
PERSPECTIVA: {spec['focus']}

REGLAS:
- Máximo ~15.000 palabras
- NO resumas — copia las secciones relevantes TAL CUAL del documento original
- Si una sección es relevante, inclúyela ÍNTEGRA
- Si no es relevante, OMÍTELA por completo
- Mejor 10 secciones íntegras que 30 resumidas
- Incluye SIEMPRE: resultados experimentales completos (Exp 4, 5, 5b, 1bis, 6, 7)
- IMPORTANTE: No inventes contenido. Copia secciones literales del documento."""

        result = call_openrouter(
            model_id="moonshotai/kimi-k2.5",
            system_prompt=system_prompt,
            user_prompt=full_ctx,
            max_tokens=16384,
            temperature=0.3,
            timeout_s=600,
            label=f"F0b-{key}"
        )

        if result.get("error"):
            print(f"  ERROR for {key}: {result['error']}")
            continue

        content = result.get("content", "")
        if len(content) < 1000:
            print(f"  WARNING: {key} briefing too short ({len(content)} chars)")
            continue

        path = CTX_DIR / f"exp8_brief_{key}.md"
        path.write_text(content, encoding="utf-8")
        tokens = len(content) // 4
        print(f"  Saved: {path} (~{tokens:,} tokens)")
        success_count += 1

    print(f"\n  Compiled {success_count}/4 briefings")
    if success_count < 4:
        print("  Missing briefings will use standard version as fallback")

    return success_count >= 3  # OK if at least 3/4 succeeded


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — R1: AUDIT
# ═══════════════════════════════════════════════════════════════════════════════

R1_SYSTEM_PROMPT = """Eres auditor experto en sistemas cognitivos. Se te presenta el diseño de OMNI-MIND v4 — un sistema que usa redes de preguntas (no instrucciones) para que agentes de IA analicen cualquier situación.

Tu perspectiva es: {perspective}

AUDITA el sistema respondiendo CADA una de estas preguntas:

=== A. COHERENCIA INTERNA ===

A1. ¿Los documentos L0 (invariantes) son consistentes entre sí?
A2. ¿El Documento Maestro es consistente con los L0?
A3. ¿Las 18 inteligencias son genuinamente irreducibles?
A4. ¿La Matriz 3L×7F es el esquema correcto?
A5. ¿Los resultados experimentales contradicen alguna asunción del diseño?

=== B. SOBREDISEÑO ===

B1. ¿Qué componentes existen por teoría pero no tienen validación empírica?
B2. ¿Qué puede eliminarse sin perder funcionalidad real?
B3. ¿Los 17 tipos de pensamiento son necesarios o es overhead?
B4. ¿Los 6 modos son necesarios si la Matriz ya tiene gradientes?
B5. ¿El Reactor v3 (generación conceptual) aporta algo que los datos reales no cubren mejor?

=== C. HUECOS ===

C1. ¿Qué necesita el sistema que no está diseñado?
C2. ¿La interfaz de usuario (chat) está suficientemente especificada?
C3. ¿El modelo de negocio (€50-200/mes) está validado o es asunción?
C4. ¿La transferencia cross-dominio tiene base empírica?
C5. ¿Qué pasa cuando el sistema se equivoca? ¿Hay mecanismo de corrección?

=== D. CONTRADICCIONES ===

D1. Maestro dice "Chief DEPRECADO" pero CONTEXTO_SISTEMA tiene 24 agentes del Chief operativos
D2. Maestro dice "todo a fly.io" pero implementación está en Supabase
D3. Maestro dice "Sonnet solo referencia" pero ~12 agentes dependen de Sonnet
D4. ¿Presupuestos del v1 (€640-920 para 3 meses) son realistas con costes reales ($0.10-1.50)?
D5. ¿Hay contradicciones entre las 4 versiones del documento no resueltas?

=== E. VISIÓN DE PRODUCTO ===

E1. ¿La visión (motor que compila programa cognitivo por interacción) es realista?
E2. ¿El camino "pilotos propios → amigo informático → escala" tiene sentido?
E3. ¿El modelo de negocio (margen >90%) se sostiene?
E4. ¿El flywheel (cada cliente mejora para todos) funciona en la práctica?
E5. ¿Qué competidores existen y cómo se diferencia?
E6. ¿Cuál es el MVP REAL mínimo para validar con un piloto?

=== F. HOJA DE RUTA ===

F1. ¿Qué se implementa PRIMERO?
F2. ¿Cuál es la dependencia crítica que bloquea todo?
F3. ¿Tiempo y coste realista hasta un piloto funcional?
F4. ¿Qué se puede hacer esta semana vs este mes vs este trimestre?
F5. Si tuvieras que apostar por UNA cosa que haga o rompa el proyecto, ¿cuál es?

FORMATO:
- Responde CADA pregunta (A1-F5 = 31 preguntas)
- Para cada una: veredicto (🟢 bien / 🟡 mejorable / 🔴 problema) + explicación breve
- Si citas el documento, indica la sección exacta
- Al final: TOP 5 hallazgos más importantes ordenados por impacto"""


def get_context_for_model(model_key: str, kimi_briefings_ok: bool) -> str:
    """Get the appropriate context for a model.

    Strategy:
    - Kimi: full version (~172K tokens, within 1M window)
    - Others: standard version (~75K tokens) with optional Kimi-compiled
      perspective guide prepended (~4-11K tokens extra)
    """
    if model_key == "kimi":
        return (CTX_DIR / "exp8_full.md").read_text(encoding="utf-8")

    # For 128K models: use standard version
    std = CTX_DIR / "exp8_standard.md"
    standard_ctx = std.read_text(encoding="utf-8") if std.exists() else ""

    # Optionally prepend Kimi-compiled perspective guide
    if kimi_briefings_ok:
        brief_path = CTX_DIR / f"exp8_brief_{model_key}.md"
        if brief_path.exists():
            brief = brief_path.read_text(encoding="utf-8")
            if len(brief) > 1000:
                total_tokens = (len(brief) + len(standard_ctx)) // 4
                if total_tokens < 95000:  # Leave 33K for prompt + response
                    return f"## GUÍA DE PERSPECTIVA PARA TU AUDITORÍA\n\n{brief}\n\n---\n\n## DOCUMENTACIÓN COMPLETA DEL SISTEMA\n\n{standard_ctx}"

    if standard_ctx and len(standard_ctx) // 4 < 95000:
        return standard_ctx

    return (CTX_DIR / "exp8_mini.md").read_text(encoding="utf-8")


def phase1(kimi_briefings_ok: bool):
    """Run R1 audits with all 5 models."""
    print("\n" + "=" * 60)
    print("PHASE 1 — R1: AUDIT (5 models × 31 questions)")
    print("=" * 60)

    audits = {}
    for key, model in MODELS.items():
        print(f"\n--- {model['name']} ({key}) ---")

        context = get_context_for_model(key, kimi_briefings_ok)
        system_prompt = R1_SYSTEM_PROMPT.format(perspective=model["perspective"])
        user_prompt = f"CONTEXTO DEL SISTEMA OMNI-MIND:\n\n{context}"

        result = call_openrouter(
            model_id=model["id"],
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=16384,
            temperature=0.7,
            timeout_s=600,
            label=f"R1-{key}"
        )

        audits[key] = result

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        else:
            save_result(f"exp8_r1_{key}.md", result["content"])

    return audits


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — R2: CROSS-EVALUATION
# ═══════════════════════════════════════════════════════════════════════════════

R2_SYSTEM_PROMPT = """Aquí tienes 5 auditorías independientes del Sistema Cognitivo OMNI-MIND, cada una desde una perspectiva diferente.

Para CADA auditoría:
1. ¿Con qué hallazgos estás de acuerdo? (citar por código A1, B3, etc.)
2. ¿Con qué hallazgos NO estás de acuerdo? ¿Por qué?
3. ¿Qué vio este auditor que los demás no vieron?

Al final:
- Los 10 hallazgos con MAYOR CONSENSO (4+ auditores de acuerdo)
- Los 5 hallazgos con MAYOR DISENSO (opiniones opuestas)
- Tu síntesis: ¿cuáles son los 3 cambios más urgentes para OMNI-MIND?"""


def phase2(audits: dict):
    """Run R2 cross-evaluations."""
    print("\n" + "=" * 60)
    print("PHASE 2 — R2: CROSS-EVALUATION")
    print("=" * 60)

    # Compile all audits into one document
    audit_doc = ""
    for key, audit in audits.items():
        if audit.get("content"):
            model = MODELS[key]
            audit_doc += f"\n\n{'='*60}\n## AUDITORÍA: {model['name']} — {model['perspective']}\n{'='*60}\n\n"
            audit_doc += audit["content"]

    if not audit_doc:
        print("  ERROR: No audits to cross-evaluate")
        return {}

    evaluations = {}
    for key, model in MODELS.items():
        print(f"\n--- {model['name']} ({key}) ---")

        result = call_openrouter(
            model_id=model["id"],
            system_prompt=R2_SYSTEM_PROMPT,
            user_prompt=audit_doc,
            max_tokens=12288,
            temperature=0.5,
            timeout_s=600,
            label=f"R2-{key}"
        )

        evaluations[key] = result

        if result.get("error"):
            print(f"  ERROR: {result['error']}")
        else:
            save_result(f"exp8_r2_{key}.md", result["content"])

    return evaluations


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — SYNTHESIS
# ═══════════════════════════════════════════════════════════════════════════════

SYNTHESIS_PROMPT = """Aquí tienes las 5 auditorías + las 5 evaluaciones cruzadas del Sistema Cognitivo OMNI-MIND.

Produce:

1. DIAGNÓSTICO CONSOLIDADO
   Para cada área (A-F), el veredicto final con justificación:
   - 🟢 = sólido, no tocar
   - 🟡 = funciona pero hay que mejorar (decir qué)
   - 🔴 = roto o inconsistente (decir qué y cómo arreglar)

2. MAPA DE CONTRADICCIONES
   Cada contradicción encontrada entre documentos, con:
   - Documento A dice X (sección)
   - Documento B dice Y (sección)
   - Resolución propuesta

3. MAPA DE SOBREDISEÑO
   Cada componente que puede eliminarse o simplificarse:
   - Componente
   - Por qué sobra (con dato empírico si existe)
   - Qué lo reemplaza (si algo)

4. MAPA DE HUECOS
   Cada cosa que falta:
   - Qué falta
   - Por qué es necesario
   - Prioridad (bloqueante / importante / nice-to-have)

5. HOJA DE RUTA ACTUALIZADA
   SEMANA 1 (esta semana): [acciones]
   SEMANA 2-3: [acciones]
   MES 1: [acciones]
   MES 2-3: [acciones]
   Para cada acción: qué, quién (Code/humano/sistema), dependencia, coste estimado

6. DECISIONES CR0 PENDIENTES
   Lista de decisiones que Jesús necesita tomar, con opciones y recomendación."""


def phase3(audits: dict, evaluations: dict):
    """Run synthesis with Cogito 671B."""
    print("\n" + "=" * 60)
    print("PHASE 3 — SYNTHESIS (Cogito 671B)")
    print("=" * 60)

    # Compile all R1 + R2
    full_doc = "# AUDITORÍAS R1\n\n"
    for key, audit in audits.items():
        if audit.get("content"):
            model = MODELS[key]
            full_doc += f"\n## R1: {model['name']}\n\n{audit['content']}\n"

    full_doc += "\n\n# EVALUACIONES CRUZADAS R2\n\n"
    for key, ev in evaluations.items():
        if ev.get("content"):
            model = MODELS[key]
            full_doc += f"\n## R2: {model['name']}\n\n{ev['content']}\n"

    result = call_openrouter(
        model_id="deepcogito/cogito-v2.1-671b",
        system_prompt=SYNTHESIS_PROMPT,
        user_prompt=full_doc,
        max_tokens=16384,
        temperature=0.3,
        timeout_s=600,
        label="F3-synthesis"
    )

    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        # Fallback: try with Kimi
        print("  Trying fallback with Kimi K2.5...")
        result = call_openrouter(
            model_id="moonshotai/kimi-k2.5",
            system_prompt=SYNTHESIS_PROMPT,
            user_prompt=full_doc,
            max_tokens=16384,
            temperature=0.3,
            timeout_s=600,
            label="F3-synthesis-fallback"
        )

    if result.get("content"):
        save_result("exp8_synthesis.md", result["content"])

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def count_verdicts(text: str) -> dict:
    """Count 🟢🟡🔴 verdicts in text."""
    return {
        "green": text.count("🟢"),
        "yellow": text.count("🟡"),
        "red": text.count("🔴"),
    }


def extract_top5(text: str) -> list:
    """Try to extract TOP 5 hallazgos from audit text."""
    lines = text.split("\n")
    top5 = []
    capturing = False
    for line in lines:
        if "TOP 5" in line.upper() or "TOP-5" in line.upper() or "5 HALLAZGOS" in line.upper():
            capturing = True
            continue
        if capturing:
            stripped = line.strip()
            if stripped and (stripped[0].isdigit() or stripped.startswith("-") or stripped.startswith("*")):
                top5.append(stripped)
            if len(top5) >= 5:
                break
    return top5[:5]


def phase4(audits: dict, evaluations: dict, synthesis: dict):
    """Generate final report and JSON."""
    print("\n" + "=" * 60)
    print("PHASE 4 — FINAL REPORT")
    print("=" * 60)

    # Build report
    report_parts = []
    report_parts.append("# EXP 8 — Auditoría Completa del Sistema Cognitivo OMNI-MIND")
    report_parts.append(f"\n**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_parts.append(f"\n**Modelos:** {', '.join(m['name'] for m in MODELS.values())}")

    # 1. Executive summary
    report_parts.append("\n\n## 1. Resumen Ejecutivo\n")
    if synthesis.get("content"):
        # Take first ~2000 chars of synthesis as executive summary
        synth_lines = synthesis["content"].split("\n")
        summary_lines = []
        for line in synth_lines:
            summary_lines.append(line)
            if len("\n".join(summary_lines)) > 2000:
                break
        report_parts.append("\n".join(summary_lines))
    else:
        report_parts.append("*Síntesis no disponible*")

    # 2. Individual audits
    report_parts.append("\n\n## 2. Auditorías Individuales (R1)\n")
    for key, audit in audits.items():
        model = MODELS[key]
        report_parts.append(f"\n### {model['name']} — {model['perspective']}\n")
        if audit.get("content"):
            verdicts = count_verdicts(audit["content"])
            report_parts.append(f"**Veredictos:** 🟢 {verdicts['green']} / 🟡 {verdicts['yellow']} / 🔴 {verdicts['red']}")
            report_parts.append(f"\n**Tiempo:** {audit.get('time_s', 'N/A')}s | **Tokens:** {audit.get('tokens_out', 'N/A')}\n")
            report_parts.append(audit["content"])
        elif audit.get("error"):
            report_parts.append(f"**ERROR:** {audit['error']}")

    # 3. Cross-evaluations
    report_parts.append("\n\n## 3. Evaluaciones Cruzadas (R2)\n")
    for key, ev in evaluations.items():
        model = MODELS[key]
        report_parts.append(f"\n### {model['name']}\n")
        if ev.get("content"):
            report_parts.append(ev["content"])
        elif ev.get("error"):
            report_parts.append(f"**ERROR:** {ev['error']}")

    # 4. Synthesis
    report_parts.append("\n\n## 4. Síntesis Consolidada\n")
    if synthesis.get("content"):
        report_parts.append(synthesis["content"])

    # 5. Metadata
    report_parts.append("\n\n## 5. Metadatos\n")
    total_cost = sum(
        a.get("cost", 0) for a in list(audits.values()) + list(evaluations.values()) + [synthesis]
    )
    total_tokens = sum(
        a.get("tokens_out", 0) for a in list(audits.values()) + list(evaluations.values()) + [synthesis]
    )
    report_parts.append(f"- **Coste total estimado:** ${total_cost:.4f}")
    report_parts.append(f"- **Tokens generados:** {total_tokens:,}")
    report_parts.append(f"- **Modelos usados:** {len(MODELS)}")

    report = "\n".join(report_parts)
    save_result("exp8_report.md", report)

    # Build JSON
    results_json = {
        "experiment": "exp8_system_audit",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "models_used": {k: v["id"] for k, v in MODELS.items()},
        "audits": {},
        "cross_evaluations": {},
        "synthesis": {
            "content_length": len(synthesis.get("content", "")),
            "time_s": synthesis.get("time_s", 0),
            "error": synthesis.get("error"),
        },
        "totals": {
            "cost": total_cost,
            "tokens_generated": total_tokens,
        },
    }

    for key, audit in audits.items():
        results_json["audits"][key] = {
            "model": MODELS[key]["id"],
            "perspective": MODELS[key]["perspective"],
            "verdict_counts": count_verdicts(audit.get("content", "")),
            "top5": extract_top5(audit.get("content", "")),
            "time_s": audit.get("time_s", 0),
            "tokens_out": audit.get("tokens_out", 0),
            "cost": audit.get("cost", 0),
            "error": audit.get("error"),
        }

    for key, ev in evaluations.items():
        results_json["cross_evaluations"][key] = {
            "model": MODELS[key]["id"],
            "time_s": ev.get("time_s", 0),
            "tokens_out": ev.get("tokens_out", 0),
            "cost": ev.get("cost", 0),
            "error": ev.get("error"),
        }

    json_path = RESULTS_DIR / "exp8_results.json"
    json_path.write_text(json.dumps(results_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Saved: {json_path}")

    print(f"\n  TOTAL COST: ${total_cost:.4f}")
    print(f"  TOTAL TOKENS: {total_tokens:,}")
    print("\nEXP 8 COMPLETE.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="EXP 8 — Auditoría Completa OMNI-MIND")
    parser.add_argument("--phase", type=str, default="all",
                        help="Phase to run: 0, 0b, 1, 2, 3, 4, or 'all'")
    parser.add_argument("--skip-kimi-briefings", action="store_true",
                        help="Skip Phase 0b and use standard/mini fallback")
    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    phase = args.phase

    if phase in ("all", "0"):
        phase0()

    kimi_briefings_ok = False
    if phase in ("all", "0b"):
        if not args.skip_kimi_briefings:
            kimi_briefings_ok = phase0b()
        else:
            print("\nSkipping Phase 0b (--skip-kimi-briefings)")

    # Check if briefings exist from previous run
    if phase not in ("all", "0b"):
        kimi_briefings_ok = all(
            (CTX_DIR / f"exp8_brief_{k}.md").exists()
            for k in ["step", "cogito", "deepseek", "nemotron"]
        )

    audits = {}
    if phase in ("all", "1"):
        audits = phase1(kimi_briefings_ok)
    elif phase in ("2", "3", "4"):
        # Load existing R1 results
        for key in MODELS:
            path = RESULTS_DIR / f"exp8_r1_{key}.md"
            if path.exists():
                audits[key] = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    evaluations = {}
    if phase in ("all", "2"):
        evaluations = phase2(audits)
    elif phase in ("3", "4"):
        for key in MODELS:
            path = RESULTS_DIR / f"exp8_r2_{key}.md"
            if path.exists():
                evaluations[key] = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    synthesis = {}
    if phase in ("all", "3"):
        synthesis = phase3(audits, evaluations)
    elif phase == "4":
        path = RESULTS_DIR / "exp8_synthesis.md"
        if path.exists():
            synthesis = {"content": path.read_text(encoding="utf-8"), "time_s": 0, "tokens_out": 0}

    if phase in ("all", "4"):
        phase4(audits, evaluations, synthesis)


if __name__ == "__main__":
    main()
