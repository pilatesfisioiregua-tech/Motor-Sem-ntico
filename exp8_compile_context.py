#!/usr/bin/env python3
"""EXP 8 — Phase 0: Compile full system context for audit.

Reads all OMNI-MIND documents and compiles two versions:
- exp8_full_system.md: Everything (for Kimi K2.5, 1M ctx)
- exp8_condensed.md: ~50K tokens (for 128K ctx models)
"""

import os
from pathlib import Path

BASE = Path("/Users/jesusfernandezdominguez/omni-mind-cerebro")
MS = BASE / "motor-semantico"
MOTOR = BASE / "Motor" / "Meta-Red de preguntas inteligencias"
CTX = BASE / "Contexto"
OUT_DIR = MS / "context"

def read_file(path: Path) -> str:
    """Read file, return content or error message."""
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"[ERROR reading {path}: {e}]"

def section(title: str, content: str) -> str:
    """Wrap content in a clear section separator."""
    sep = "=" * 80
    return f"\n\n{sep}\n# {title}\n{sep}\n\n{content}\n"

def extract_firmas(content: str) -> str:
    """Extract just FIRMA and RESUMEN from an intelligence analysis."""
    lines = content.split("\n")
    result = []
    capturing = False
    for line in lines:
        if any(kw in line.upper() for kw in ["# FIRMA", "## FIRMA", "RESUMEN", "# INT-", "## INT-"]):
            capturing = True
        if capturing:
            result.append(line)
            if len(result) > 30:  # Cap at ~30 lines per section
                capturing = False
        if line.strip() == "" and capturing and len(result) > 5:
            capturing = False
    return "\n".join(result) if result else content[:500] + "\n[...truncated...]"

def compile_full() -> str:
    """Compile the FULL context (~450K tokens for Kimi K2.5)."""
    parts = []

    parts.append("# OMNI-MIND v4 — SISTEMA COGNITIVO COMPLETO\n")
    parts.append("## Compilado para auditoría EXP 8\n")
    parts.append(f"## Fecha: 2026-03-11\n")
    parts.append("---\n")

    # ═══ CAPA L0 — INVARIANTES ═══
    parts.append(section(
        "CAPA L0 — INVARIANTES (no cambian)",
        "Los documentos L0 definen los invariantes del sistema."
    ))

    # L0: Álgebra del Cálculo Semántico
    parts.append(section(
        "L0: ALGEBRA DEL CALCULO SEMANTICO (CR0)",
        read_file(MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md")
    ))

    # L0: Meta-Red de Inteligencias
    parts.append(section(
        "L0: META-RED DE INTELIGENCIAS (CR0)",
        read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md")
    ))

    # L0: Tabla Periódica
    parts.append(section(
        "L0: TABLA PERIODICA DE LA INTELIGENCIA (CR0)",
        read_file(MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md")
    ))

    # ═══ DOCUMENTO MAESTRO ═══
    parts.append(section(
        "DOCUMENTO MAESTRO — SISTEMA COGNITIVO OMNI-MIND v4 (Fuente de verdad)",
        read_file(MS / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # ═══ IMPLEMENTACIÓN ACTUAL ═══
    parts.append(section(
        "IMPLEMENTACION ACTUAL — CONTEXTO SISTEMA (estado real del código)",
        read_file(CTX / "CONTEXTO_SISTEMA.md")
    ))

    parts.append(section(
        "IMPLEMENTACION ACTUAL — MEMORY (estado operativo)",
        read_file(CTX / "MEMORY.md")
    ))

    # ═══ ARQUITECTURA MULTI-MODELO ═══
    parts.append(section(
        "ARQUITECTURA MECANISMOS MULTI-MODELO",
        read_file(MS / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md")
    ))

    parts.append(section(
        "MAPA DE MODELOS OS — MARZO 2026",
        read_file(MS / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    parts.append(section(
        "ACTUALIZACION MAESTRO — PRINCIPIO 31 TIERS",
        read_file(MS / "ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md")
    ))

    parts.append(section(
        "ACTUALIZACION MAESTRO — SESION 11 MARZO",
        read_file(MS / "ACTUALIZACION_MAESTRO_SESION_11_MAR.md")
    ))

    # ═══ VERSIONES ANTERIORES ═══
    parts.append(section(
        "VERSION ANTERIOR — DISEÑO MOTOR SEMANTICO v1",
        read_file(MS / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md")
    ))

    parts.append(section(
        "VERSION ANTERIOR — DISEÑO MOTOR SEMANTICO v2",
        read_file(MS / "DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md")
    ))

    parts.append(section(
        "VERSION ANTERIOR — SISTEMA COGNITIVO v2",
        read_file(MS / "SISTEMA_COGNITIVO_OMNI_MIND_v2.md")
    ))

    # ═══ CARTOGRAFÍA ═══
    parts.append(section(
        "CARTOGRAFIA — PROTOCOLO",
        read_file(MOTOR / "PROTOCOLO_CARTOGRAFIA_META_RED_v1.md")
    ))

    parts.append(section(
        "CARTOGRAFIA — OUTPUT FINAL (34 chats)",
        read_file(MOTOR / "OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md")
    ))

    # ═══ 18 INTELIGENCIAS INDIVIDUALES ═══
    resultados = MOTOR / "resultados"
    if resultados.exists():
        int_parts = []
        for f in sorted(resultados.glob("*.md")):
            int_parts.append(f"### {f.stem}\n\n{read_file(f)}\n")
        parts.append(section(
            "18 INTELIGENCIAS — ANALISIS INDIVIDUALES",
            "\n".join(int_parts)
        ))

    # JSONs de inteligencias
    jsons = MOTOR / "json"
    if jsons.exists():
        json_parts = []
        for f in sorted(jsons.glob("*.md")):
            json_parts.append(f"### {f.stem}\n\n{read_file(f)}\n")
        parts.append(section(
            "18 INTELIGENCIAS — DATOS JSON",
            "\n".join(json_parts)
        ))

    # ═══ OPERACIONES ALGEBRAICAS ═══
    fase3 = MOTOR / "Fase 3"
    if fase3.exists():
        ops_parts = []
        for f in sorted(fase3.glob("*.md")):
            ops_parts.append(f"### {f.stem}\n\n{read_file(f)}\n")
        parts.append(section(
            "OPERACIONES ALGEBRAICAS — FASE 3",
            "\n".join(ops_parts)
        ))

    fase4 = MOTOR / "Fase 4"
    if fase4.exists():
        ops_parts = []
        for f in sorted(fase4.glob("*.md")):
            ops_parts.append(f"### {f.stem}\n\n{read_file(f)}\n")
        parts.append(section(
            "OPERACIONES ALGEBRAICAS — FASE 4",
            "\n".join(ops_parts)
        ))

    # ═══ CASOS DE TEST ═══
    diff = MOTOR / "Fase 2 diferenciales"
    if diff.exists():
        test_parts = []
        for f in sorted(diff.glob("*.md")):
            test_parts.append(f"### {f.stem}\n\n{read_file(f)}\n")
        parts.append(section(
            "CASOS DE TEST (benchmarks)",
            "\n".join(test_parts)
        ))

    # ═══ RESULTADOS EXPERIMENTALES ═══
    exp_results = []

    exp_files = [
        (MS / "motor_v1_validation/results/exp4_mesa_redonda_report.md", "EXP 4 — Mesa Redonda Principal"),
        (MS / "motor_v1_validation/results/exp4_1_comparison_report.md", "EXP 4.1 — Comparación"),
        (MS / "motor_v1_validation/results/exp4_2_sintetizador_report.md", "EXP 4.2 — Sintetizador"),
        (MS / "motor_v1_validation/results/exp4_3_mente_distribuida_report.md", "EXP 4.3 — Mente Distribuida"),
        (MS / "motor_v1_validation/results/exp5_report.md", "EXP 5 — Cadena de Montaje"),
        (MS / "results/exp5b_report.md", "EXP 5b — Modelos Nuevos en Pipeline"),
        (MS / "results/exp1bis_report.md", "EXP 1 BIS — 6 Modelos Nuevos"),
        (MS / "motor_v1_validation/results/exp6_openhands_analysis.md", "EXP 6 — OpenHands Analysis"),
    ]

    for path, title in exp_files:
        if path.exists():
            exp_results.append(f"### {title}\n\n{read_file(path)}\n")
        else:
            exp_results.append(f"### {title}\n\n[Archivo no encontrado: {path}]\n")

    # Check for exp7 results
    exp7_results = list((MS / "results").glob("exp7*"))
    for f in sorted(exp7_results):
        exp_results.append(f"### EXP 7 — {f.stem}\n\n{read_file(f)}\n")

    parts.append(section(
        "RESULTADOS EXPERIMENTALES",
        "\n".join(exp_results)
    ))

    # ═══ ADDITIONAL CONTEXT ═══
    # Matrix coverage report
    matrix_report = MS / "motor_v1_validation/results/MATRIX_COVERAGE_REPORT.md"
    if matrix_report.exists():
        parts.append(section(
            "MATRIX COVERAGE REPORT",
            read_file(matrix_report)
        ))

    multi_model = MS / "motor_v1_validation/results/MULTI_MODEL_COVERAGE_REPORT.md"
    if multi_model.exists():
        parts.append(section(
            "MULTI-MODEL COVERAGE REPORT",
            read_file(multi_model)
        ))

    return "\n".join(parts)


def truncate_to(content: str, max_chars: int) -> str:
    """Truncate content to max_chars, cutting at last paragraph break."""
    if len(content) <= max_chars:
        return content
    # Find last double newline before limit
    cut = content[:max_chars].rfind("\n\n")
    if cut == -1:
        cut = max_chars
    return content[:cut] + f"\n\n[...truncado a {max_chars//1000}K chars para versión condensada...]"


def compile_condensed() -> str:
    """Compile condensed context (~70K tokens for 128K models).

    Budget: ~280K chars = ~70K tokens
    Leaves ~58K tokens for prompt + response in 128K models.
    """
    parts = []

    parts.append("# OMNI-MIND v4 — CONTEXTO CONDENSADO PARA AUDITORÍA\n")
    parts.append("## EXP 8 — Versión condensada (~70K tokens)\n")
    parts.append("## Fecha: 2026-03-11\n")
    parts.append("---\n")
    parts.append("""
NOTA: Versión condensada. [COMPLETO] = íntegro. [TRUNCADO] = cortado. [RESUMEN] = resumido.
""")

    # ═══ DOCUMENTO MAESTRO [COMPLETO] ~19K tokens ═══
    parts.append(section(
        "[COMPLETO] DOCUMENTO MAESTRO — SISTEMA COGNITIVO OMNI-MIND v4",
        read_file(MS / "SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md")
    ))

    # ═══ L0 INVARIANTES [COMPLETO] ~4K tokens ═══
    parts.append(section(
        "[COMPLETO] L0: ALGEBRA DEL CALCULO SEMANTICO (CR0)",
        read_file(MOTOR / "ALGEBRA_CALCULO_SEMANTICO_CR0.md")
    ))

    # ═══ META-RED [TRUNCADO] ~8K tokens (from 12K) ═══
    parts.append(section(
        "[TRUNCADO] L0: META-RED DE INTELIGENCIAS (CR0)",
        truncate_to(read_file(MOTOR / "META_RED_INTELIGENCIAS_CR0.md"), 32000)
    ))

    # ═══ TABLA PERIODICA [COMPLETO] ~4K tokens ═══
    parts.append(section(
        "[COMPLETO] L0: TABLA PERIODICA DE LA INTELIGENCIA (CR0)",
        read_file(MOTOR / "TABLA_PERIODICA_INTELIGENCIA_CR0.md")
    ))

    # ═══ IMPLEMENTACIÓN [TRUNCADO] ~10K tokens (from 17K) ═══
    parts.append(section(
        "[TRUNCADO] CONTEXTO SISTEMA (implementación actual)",
        truncate_to(read_file(CTX / "CONTEXTO_SISTEMA.md"), 40000)
    ))

    # ═══ MEMORY [TRUNCADO] ~3K tokens (from 6K) ═══
    parts.append(section(
        "[TRUNCADO] MEMORY (estado operativo)",
        truncate_to(read_file(CTX / "MEMORY.md"), 12000)
    ))

    # ═══ ARQUITECTURA MULTI-MODELO [COMPLETO] ~4K tokens ═══
    parts.append(section(
        "[COMPLETO] ARQUITECTURA MECANISMOS MULTI-MODELO",
        read_file(MS / "ARQUITECTURA_MECANISMOS_MULTI_MODELO.md")
    ))

    # ═══ MAPA MODELOS [COMPLETO] ~2K tokens ═══
    parts.append(section(
        "[COMPLETO] MAPA DE MODELOS OS — MARZO 2026",
        read_file(MS / "MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md")
    ))

    # ═══ ACTUALIZACIONES [COMPLETO] ~1K + 3K tokens ═══
    parts.append(section(
        "[COMPLETO] ACTUALIZACION MAESTRO — PRINCIPIO 31 TIERS",
        read_file(MS / "ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md")
    ))

    parts.append(section(
        "[COMPLETO] ACTUALIZACION MAESTRO — SESION 11 MARZO",
        read_file(MS / "ACTUALIZACION_MAESTRO_SESION_11_MAR.md")
    ))

    # ═══ RESULTADOS EXPERIMENTALES [COMPLETO] ~12K tokens ═══
    exp_results = []
    exp_files = [
        (MS / "motor_v1_validation/results/exp4_mesa_redonda_report.md", "EXP 4 — Mesa Redonda"),
        (MS / "motor_v1_validation/results/exp4_2_sintetizador_report.md", "EXP 4.2 — Sintetizador"),
        (MS / "motor_v1_validation/results/exp4_3_mente_distribuida_report.md", "EXP 4.3 — Mente Distribuida"),
        (MS / "motor_v1_validation/results/exp5_report.md", "EXP 5 — Cadena de Montaje"),
        (MS / "results/exp5b_report.md", "EXP 5b — Modelos Nuevos"),
        (MS / "results/exp1bis_report.md", "EXP 1 BIS — 6 Modelos Nuevos"),
        (MS / "motor_v1_validation/results/exp6_openhands_analysis.md", "EXP 6 — OpenHands"),
    ]
    for path, title in exp_files:
        if path.exists():
            exp_results.append(f"### {title}\n\n{read_file(path)}\n")

    exp7_results = list((MS / "results").glob("exp7*"))
    for f in sorted(exp7_results):
        exp_results.append(f"### EXP 7 — {f.stem}\n\n{read_file(f)}\n")

    parts.append(section(
        "[COMPLETO] RESULTADOS EXPERIMENTALES",
        "\n".join(exp_results)
    ))

    # ═══ OPERACIONES ALGEBRAICAS [RESUMEN] ~1K token ═══
    ops_summary = """
Operaciones algebraicas validadas empíricamente (Fase 3 + Fase 4):
- Fusión INT-01⊕INT-08 (SaaS): Validada, firma combinada correcta
- Composición INT-01→INT-08 (Startup SaaS): Validada, orden importa
- Composición INT-02→INT-17 (SaaS): Validada
- Fusión INT-06⊕INT-16 (Startup SaaS): Validada
- Composición INT-14→INT-01 (SaaS): Validada (marco binario universal)
- Fusión INT-07⊕INT-17 (Cambio carrera): Validada
- Fusión INT-03⊕INT-18 (Clínica): Validada
- Distributividad (Startup SaaS): A⊕(B⊕C) ≈ (A⊕B)⊕(A⊕C) — parcial, ~70% factorizable
- Distributividad inversa (SaaS): (B⊕C)→A NO factorizable — valor irreducible
- Asociatividad (SaaS): (A⊕B)⊕C ≈ A⊕(B⊕C) — confirmada con matices
- Clausura INT-07⊕INT-14 (Cambio carrera): Validada, resultado dentro del álgebra
- Saturación INT-03 (Clínica): Detectada — rendimiento decreciente > 3 pasadas
"""
    parts.append(section(
        "[RESUMEN] OPERACIONES ALGEBRAICAS VALIDADAS",
        ops_summary
    ))

    # Total estimated: ~71K tokens
    return "\n".join(parts)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Compiling FULL context...")
    full = compile_full()
    full_path = OUT_DIR / "exp8_full_system.md"
    full_path.write_text(full, encoding="utf-8")
    full_tokens = len(full) // 4  # rough estimate
    print(f"  Written: {full_path}")
    print(f"  Size: {len(full):,} chars (~{full_tokens:,} tokens)")

    print("\nCompiling CONDENSED context...")
    condensed = compile_condensed()
    condensed_path = OUT_DIR / "exp8_condensed.md"
    condensed_path.write_text(condensed, encoding="utf-8")
    cond_tokens = len(condensed) // 4
    print(f"  Written: {condensed_path}")
    print(f"  Size: {len(condensed):,} chars (~{cond_tokens:,} tokens)")

    print("\nDone!")


if __name__ == "__main__":
    main()
