#!/usr/bin/env python3
"""EXP 7 — Mesa Redonda: Rediseno del Chief of Staff OS
5 modelos generan disenos independientes, evaluan cruzado, y se sintetiza consenso.
"""
import json, os, re, subprocess, sys, tempfile, time
from typing import Optional, List, Dict
from pathlib import Path

BASE_DIR = Path(__file__).parent
CONTEXT_PATH = BASE_DIR / "context" / "exp7_input_context.md"
RESULTS_DIR = BASE_DIR / "results"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "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")

# --- Models ---
MODELS = {
    "step35": {
        "id": "stepfun/step-3.5-flash",
        "name": "Step 3.5 Flash",
        "perspective": "Razonamiento -- que es logicamente necesario vs sobrediseno?"
    },
    "cogito": {
        "id": "deepcogito/cogito-v2.1-671b",
        "name": "Cogito 671B",
        "perspective": "Sintesis -- como conectar Motor + Gestor + Agente + Chat?"
    },
    "kimi": {
        "id": "moonshotai/kimi-k2.5",
        "name": "Kimi K2.5",
        "perspective": "Enjambre -- como orquestar multiples modelos como agentes?"
    },
    "deepseek": {
        "id": "deepseek/deepseek-chat-v3-0324",
        "name": "DeepSeek V3.2",
        "perspective": "Arquitectura -- que estructura minimiza complejidad y maximiza capacidad?"
    },
    "nemotron": {
        "id": "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "name": "Nemotron Super",
        "perspective": "Coste/eficiencia -- que se puede hacer con codigo puro ($0) vs LLM?"
    }
}


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> blocks from model output."""
    if not text:
        return ""
    # Closed think tags
    stripped = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.DOTALL).strip()
    if stripped:
        return stripped
    # Unclosed think tag (model ran out of tokens while thinking)
    if "<think>" in text:
        parts = text.split("<think>")
        # Try to get content after last think block
        for part in reversed(parts):
            clean = part.strip()
            if clean and not clean.startswith("</think>"):
                return clean
    return text.strip()


def call_openrouter(model_id: str, system_prompt: str, user_prompt: str,
                     max_tokens: int = 16384, temperature: float = 0.7) -> dict:
    """Call OpenRouter API via subprocess+curl."""
    payload = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(payload, f)
        tmpfile = f.name

    try:
        start = time.time()
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://openrouter.ai/api/v1/chat/completions",
            "-H", f"Authorization: Bearer {OPENROUTER_API_KEY}",
            "-H", "Content-Type: application/json",
            "-H", "HTTP-Referer: https://omni-mind.app",
            "-H", "X-Title: OMNI-MIND Exp7",
            "-d", f"@{tmpfile}"
        ], capture_output=True, text=True, timeout=600)
        elapsed = time.time() - start

        resp = json.loads(result.stdout)
        if "error" in resp:
            return {"error": resp["error"], "time_s": elapsed, "tokens_out": 0}

        content = resp.get("choices", [{}])[0].get("message", {}).get("content", "")
        content = strip_think_tags(content)
        usage = resp.get("usage", {})
        tokens_out = usage.get("completion_tokens", 0)

        return {
            "content": content,
            "time_s": round(elapsed, 1),
            "tokens_out": tokens_out,
            "model": model_id,
            "error": None if content else "Empty response after stripping think tags"
        }
    except subprocess.TimeoutExpired:
        return {"error": "Timeout (600s)", "time_s": 600, "tokens_out": 0}
    except Exception as e:
        return {"error": str(e), "time_s": 0, "tokens_out": 0}
    finally:
        os.unlink(tmpfile)


def load_context() -> str:
    """Load the compiled context document."""
    return CONTEXT_PATH.read_text(encoding='utf-8')


# ============================================================
# PHASE 2 - R1: Independent designs
# ============================================================

def build_r1_prompt(perspective: str, context: str) -> str:
    """Build the R1 prompt for a model."""
    return f"""Eres un experto en {perspective} Se te pide redisenar el sistema conversacional de OMNI-MIND (el "Chief of Staff").

{context}

Tu tarea: disena el REEMPLAZO del Chief of Staff. No un parche -- un rediseno desde cero informado por toda la evidencia empirica.

REQUISITOS:
1. Sin dependencia de Anthropic (Claude/Sonnet/Haiku). Solo modelos OS.
2. Integrado con la Matriz 3Lx7F (los gaps dirigen las preguntas, no rutas fijas)
3. Multi-modelo (modelo optimo para cada subtarea, basado en datos empiricos)
4. Capacidad de actuar (puede lanzar el agente de coding, puede ejecutar pipelines)
5. Self-improvement (acumula datos de efectividad, se mejora)
6. Coste < $0.02/turno (el viejo costaba ~$0.10/turno)
7. Latencia: respuesta superficial < 1s, profundo < 30s
8. Maximo 8 componentes logicos (el viejo tenia 24 agentes)

PRODUCE:
A. Arquitectura (diagrama ASCII completo)
B. Componentes (max 8) con:
   - Que hace
   - Que modelo usa y por que (con dato empirico que lo respalda)
   - Que herramientas tiene
   - Como se comunica con los demas (estigmergia, direct call, etc.)
C. Flujo de un turno de chat (paso a paso)
D. Flujo del pensamiento profundo (paso a paso)
E. Integracion con Motor Cognitivo (como usa la Matriz 3Lx7F)
F. Integracion con Agente de Coding (como lanza tareas de implementacion)
G. Self-improvement (como aprende de cada interaccion)
H. Que se elimina del Chief viejo y POR QUE
I. Que se conserva del Chief viejo y POR QUE
J. Estimacion de coste por turno con desglose

Desde tu perspectiva de {perspective}, prioriza lo que consideres mas importante."""


def run_r1(context: str) -> Dict[str, dict]:
    """Run R1: 5 independent designs."""
    designs = {}
    for key, model in MODELS.items():
        print(f"\n  [R1] {model['name']} ({model['perspective'][:40]}...)")
        prompt = build_r1_prompt(model["perspective"], context)
        result = call_openrouter(
            model["id"],
            "Eres un arquitecto de sistemas de IA. Responde en espanol. Se exhaustivo y concreto.",
            prompt,
            max_tokens=16384,
            temperature=0.7
        )
        if result.get("error"):
            print(f"    ERROR: {result['error']}")
        else:
            print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")
            # Save individual design
            design_path = RESULTS_DIR / f"exp7_r1_{key}.md"
            design_path.write_text(f"# R1 Design: {model['name']}\n**Perspectiva:** {model['perspective']}\n\n{result['content']}", encoding='utf-8')
        designs[key] = result
    return designs


# ============================================================
# PHASE 2 - R2: Cross-evaluation
# ============================================================

def build_r2_prompt(designs: Dict[str, dict]) -> str:
    """Build the R2 prompt with all 5 designs."""
    prompt = "Aqui tienes 5 propuestas de rediseno del Chief of Staff de OMNI-MIND, cada una desde una perspectiva diferente.\n\n"

    for key, model in MODELS.items():
        design = designs.get(key, {})
        content = design.get("content", "[ERROR: no se genero diseno]")
        prompt += f"---\n## PROPUESTA {key.upper()}: {model['name']} (Perspectiva: {model['perspective']})\n\n{content}\n\n"

    prompt += """---

Para CADA propuesta:
1. Score 1-5 (1=inviable, 5=implementar ya)
2. Que aporta que las demas no? (1 frase)
3. Que falla o falta? (1 frase)
4. Que adoptarias de esta propuesta para el diseno final? (1 idea concreta)

Al final: disena el MERGE -- tu propuesta de diseno final que toma lo mejor de las 5.
El merge debe incluir:
A. Arquitectura (diagrama ASCII)
B. Componentes (max 8) con modelo asignado
C. Flujo de un turno de chat
D. Flujo del pensamiento profundo
E. Estimacion de coste por turno"""

    return prompt


def run_r2(designs: Dict[str, dict]) -> Dict[str, dict]:
    """Run R2: Cross-evaluation by each model."""
    evaluations = {}
    r2_prompt = build_r2_prompt(designs)

    for key, model in MODELS.items():
        print(f"\n  [R2] {model['name']} evaluando 5 disenos...")
        result = call_openrouter(
            model["id"],
            "Eres un evaluador experto de arquitecturas de sistemas. Evalua con rigor y concrecion. Responde en espanol.",
            r2_prompt,
            max_tokens=16384,
            temperature=0.5
        )
        if result.get("error"):
            print(f"    ERROR: {result['error']}")
        else:
            print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")
            eval_path = RESULTS_DIR / f"exp7_r2_{key}.md"
            eval_path.write_text(f"# R2 Evaluation: {model['name']}\n\n{result['content']}", encoding='utf-8')
        evaluations[key] = result
    return evaluations


# ============================================================
# PHASE 2 - R3: Consensus
# ============================================================

def run_r3(evaluations: Dict[str, dict], context: str) -> dict:
    """Run R3: Synthesize consensus from 5 merges."""

    merges_text = "Aqui tienes 5 evaluaciones cruzadas y propuestas de MERGE para el rediseno del Chief of Staff de OMNI-MIND.\n\n"
    for key, model in MODELS.items():
        ev = evaluations.get(key, {})
        content = ev.get("content", "[ERROR]")
        merges_text += f"---\n## MERGE de {model['name']}:\n\n{content}\n\n"

    consensus_prompt = merges_text + """---

TAREA: Sintetiza un DISENO FINAL UNICO que:
1. Tome lo mejor de las 5 propuestas de merge
2. Resuelva contradicciones entre ellas
3. Sea implementable (no conceptual)
4. Cumpla TODOS los requisitos: max 8 componentes, <$0.02/turno, <1s superficie, <30s profundo, multi-modelo OS, integrado con Matriz 3Lx7F, self-improving

PRODUCE EL DISENO FINAL con:
A. Arquitectura (diagrama ASCII completo y detallado)
B. Componentes (max 8) con:
   - Responsabilidad exacta
   - Modelo asignado (model_id de OpenRouter)
   - Herramientas
   - Comunicacion
C. Flujo de un turno de chat (paso a paso con tiempos)
D. Flujo del pensamiento profundo (paso a paso con tiempos)
E. Integracion con Motor Cognitivo (Matriz 3Lx7F)
F. Integracion con Agente de Coding
G. Self-improvement
H. Que se elimina del Chief viejo y POR QUE
I. Que se conserva del Chief viejo y POR QUE
J. Estimacion de coste por turno con desglose
K. Esquema de base de datos (tablas nuevas/modificadas)

Se exhaustivo. Este documento sera la spec para implementar."""

    # Use Step 3.5 Flash for synthesis (best overall in exp1bis)
    print(f"\n  [R3] Sintetizando consenso con Step 3.5 Flash...")
    result = call_openrouter(
        "stepfun/step-3.5-flash",
        "Eres un arquitecto senior de sistemas de IA. Tu tarea es sintetizar el mejor diseno posible. Se exhaustivo, concreto e implementable. Responde en espanol.",
        consensus_prompt,
        max_tokens=16384,
        temperature=0.3
    )

    if result.get("error"):
        print(f"    ERROR: {result['error']}")
    else:
        print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")
        consensus_path = RESULTS_DIR / "exp7_chief_design_v2.md"
        consensus_path.write_text(f"# CHIEF OF STAFF v2 — Diseno Consensuado\n\n{result['content']}", encoding='utf-8')
        print(f"    Guardado en: {consensus_path}")

    return result


# ============================================================
# PHASE 3: Maestro verification
# ============================================================

def run_maestro_check(consensus: dict) -> dict:
    """Verify consensus design against Maestro document."""
    design_content = consensus.get("content", "")

    check_prompt = f"""Aqui tienes el diseno consensuado del nuevo Chief of Staff de OMNI-MIND:

{design_content}

VERIFICA que el diseno es CONSISTENTE con el Documento Maestro usando este checklist:

1. Usa la Matriz 3Lx7F como campo de gradientes? (los gaps dirigen las preguntas)
2. El Gestor compila programas para el Chief como consumidor? (no usa preguntas fijas)
3. Multi-modelo con asignacion empirica? (cada modelo en su celda optima)
4. Estigmergia como comunicacion? (marcas en Postgres, no llamadas directas)
5. Los 3 niveles L0/L1/L2 respetados? (invariante/evolucionable/variable)
6. Las 8 operaciones sintacticas integradas? (detector de huecos)
7. Pensamiento profundo usa el pipeline de 7 pasos del Motor?
8. Self-improvement alimenta al Gestor? (datapoints de efectividad)
9. Puede lanzar enjambre de codigo? (Fabrica de Exocortex)
10. Coste < $0.02/turno?

Para CADA punto:
- PASA o FALLA
- Evidencia concreta del diseno
- Si FALLA: que falta y como arreglarlo

Al final: lista de inconsistencias pendientes como decisiones CR0."""

    print(f"\n  [F3] Verificando contra Maestro con Nemotron Super...")
    result = call_openrouter(
        "nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "Eres un auditor de consistencia arquitectural. Se riguroso. Responde en espanol.",
        check_prompt,
        max_tokens=8192,
        temperature=0.2
    )

    if not result.get("error"):
        check_path = RESULTS_DIR / "exp7_maestro_check.md"
        check_path.write_text(f"# Verificacion Maestro\n\n{result['content']}", encoding='utf-8')
        print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")

    return result


# ============================================================
# PHASE 4: Implementation spec
# ============================================================

def run_impl_spec(consensus: dict) -> dict:
    """Generate implementation spec from consensus design."""
    design_content = consensus.get("content", "")

    spec_prompt = f"""Aqui tienes el diseno consensuado del nuevo Chief of Staff de OMNI-MIND:

{design_content}

TRADUCE este diseno a una SPEC TECNICA IMPLEMENTABLE. Para CADA componente:

1. Nombre y responsabilidad exacta
2. Input/output (tipos, formato)
3. Modelo(s) asignado(s) con model_id exacto de OpenRouter
4. Herramientas disponibles (funciones que puede llamar)
5. Comunicacion (marcas estigmergicas: tipos, campos; direct call: endpoints; async: colas)
6. Codigo puro vs LLM (que cuesta $0 y que tiene coste)
7. Tabla(s) de base de datos que necesita (con schema SQL)
8. Estimacion de latencia y coste por call

INFRAESTRUCTURA:
- Runtime: Python/FastAPI en fly.io (misma infra que Motor Semantico)
- DB: fly.io Postgres (mismo que Motor -- comparten DB)
- LLM: OpenRouter para todos los modelos
- Interfaz chat: definir cual (Open WebUI / LibreChat / custom)
- Conexion con agente de coding

SCHEMA SQL COMPLETO para tablas nuevas/modificadas.

ESTIMACION:
- Horas de implementacion por componente
- Orden de implementacion (dependencias)
- Que se puede reusar del Motor Semantico actual"""

    print(f"\n  [F4] Generando spec de implementacion con DeepSeek V3.2...")
    result = call_openrouter(
        "deepseek/deepseek-chat-v3-0324",
        "Eres un ingeniero senior de software. Genera specs tecnicas implementables, con codigo SQL, tipos exactos, y estimaciones realistas. Responde en espanol.",
        spec_prompt,
        max_tokens=16384,
        temperature=0.3
    )

    if not result.get("error"):
        spec_path = RESULTS_DIR / "exp7_chief_implementation_spec.md"
        spec_path.write_text(f"# Spec de Implementacion — Chief of Staff v2\n\n{result['content']}", encoding='utf-8')
        print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")

    return result


# ============================================================
# PHASE 5: Report
# ============================================================

def generate_report(designs, evaluations, consensus, maestro_check, impl_spec, timing):
    """Generate final report and results JSON."""

    # --- Results JSON ---
    total_tokens = sum(d.get("tokens_out", 0) for d in designs.values())
    total_tokens += sum(e.get("tokens_out", 0) for e in evaluations.values())
    total_tokens += consensus.get("tokens_out", 0)
    total_tokens += maestro_check.get("tokens_out", 0)
    total_tokens += impl_spec.get("tokens_out", 0)

    # Count maestro checks passed
    check_content = maestro_check.get("content", "")
    passes = len(re.findall(r'(?i)\bPASA\b', check_content))
    fails = len(re.findall(r'(?i)\bFALLA\b', check_content))

    results_json = {
        "experiment": "exp7_chief_redesign",
        "date": "2026-03-13",
        "mesa_redonda": {
            "r1_designs": sum(1 for d in designs.values() if not d.get("error")),
            "r2_evaluations": sum(1 for e in evaluations.values() if not e.get("error")),
            "r3_merges": 5,
            "consensus_reached": not consensus.get("error")
        },
        "design": {
            "total_tokens": total_tokens,
            "r1_tokens": sum(d.get("tokens_out", 0) for d in designs.values()),
            "r2_tokens": sum(e.get("tokens_out", 0) for e in evaluations.values()),
            "r3_tokens": consensus.get("tokens_out", 0)
        },
        "maestro_consistency": {
            "checks_passed": passes,
            "checks_failed": fails,
            "checks_total": passes + fails
        },
        "timing": timing,
        "models_used": {k: {"id": m["id"], "name": m["name"]} for k, m in MODELS.items()}
    }

    results_path = RESULTS_DIR / "exp7_results.json"
    results_path.write_text(json.dumps(results_json, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f"\n  Guardado: {results_path}")

    # --- Report MD ---
    report = "# EXP 7 -- Rediseno del Chief of Staff OS\n\n"
    report += f"**Fecha:** 2026-03-13\n"
    report += f"**Provider:** OpenRouter\n"
    report += f"**Tokens totales:** {total_tokens:,}\n\n"

    report += "## 1. Disenos Independientes (R1)\n\n"
    report += "| Modelo | Perspectiva | Tokens | Tiempo |\n"
    report += "|--------|-------------|:---:|:---:|\n"
    for key, model in MODELS.items():
        d = designs.get(key, {})
        tok = d.get("tokens_out", 0)
        t = d.get("time_s", 0)
        err = d.get("error", "")
        status = f"{tok:,} tok" if not err else f"ERROR: {err[:30]}"
        report += f"| {model['name']} | {model['perspective'][:40]}... | {status} | {t}s |\n"

    report += "\n## 2. Evaluaciones Cruzadas (R2)\n\n"
    report += "| Evaluador | Tokens | Tiempo |\n"
    report += "|-----------|:---:|:---:|\n"
    for key, model in MODELS.items():
        e = evaluations.get(key, {})
        tok = e.get("tokens_out", 0)
        t = e.get("time_s", 0)
        report += f"| {model['name']} | {tok:,} | {t}s |\n"

    report += "\n## 3. Diseno Consensuado (R3)\n\n"
    report += f"Sintetizador: Step 3.5 Flash\n"
    report += f"Tokens: {consensus.get('tokens_out', 0):,}\n"
    report += f"Tiempo: {consensus.get('time_s', 0)}s\n\n"
    report += f"Ver: `results/exp7_chief_design_v2.md`\n\n"

    report += "## 4. Contraste con Maestro (F3)\n\n"
    report += f"Checks passed: {passes}/{passes+fails}\n\n"
    report += f"Ver: `results/exp7_maestro_check.md`\n\n"

    report += "## 5. Spec de Implementacion (F4)\n\n"
    report += f"Ver: `results/exp7_chief_implementation_spec.md`\n\n"

    report += "## 6. Timing\n\n"
    for phase, t in timing.items():
        report += f"- **{phase}:** {t:.0f}s\n"
    report += f"- **Total:** {sum(timing.values()):.0f}s\n"

    report += "\n---\n*Generado: 2026-03-13*\n"

    report_path = RESULTS_DIR / "exp7_report.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"  Guardado: {report_path}")


# ============================================================
# Main
# ============================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="EXP 7 - Rediseno Chief of Staff")
    parser.add_argument("--phase", type=str, default="all",
                       choices=["r1", "r2", "r3", "f3", "f4", "report", "all"],
                       help="Phase to run")
    parser.add_argument("--model", type=str, help="Run only this model in R1/R2")
    args = parser.parse_args()

    print("=" * 60)
    print("EXP 7 — REDISENO DEL CHIEF OF STAFF OS")
    print("=" * 60)

    context = load_context()
    print(f"Contexto cargado: {len(context):,} chars")

    timing = {}

    # Load existing results if resuming
    designs = {}
    evaluations = {}
    consensus = {}
    maestro_check = {}
    impl_spec = {}

    # Try to load saved R1 designs
    for key in MODELS:
        r1_path = RESULTS_DIR / f"exp7_r1_{key}.md"
        if r1_path.exists():
            content = r1_path.read_text(encoding='utf-8')
            # Strip the header we added
            lines = content.split('\n')
            actual = '\n'.join(lines[3:]) if len(lines) > 3 else content
            designs[key] = {"content": actual, "tokens_out": len(actual)//4, "time_s": 0, "error": None}

    # ===== R1 =====
    if args.phase in ("r1", "all"):
        print("\n" + "=" * 40)
        print("FASE 2 - R1: Disenos Independientes")
        print("=" * 40)
        t0 = time.time()

        for key, model in MODELS.items():
            if args.model and key != args.model:
                continue
            if key in designs and designs[key].get("content"):
                print(f"\n  [R1] {model['name']} -- ya existe, skip")
                continue

            print(f"\n  [R1] {model['name']} ({model['perspective'][:40]}...)")
            prompt = build_r1_prompt(model["perspective"], context)
            result = call_openrouter(
                model["id"],
                "Eres un arquitecto de sistemas de IA. Responde en espanol. Se exhaustivo y concreto.",
                prompt,
                max_tokens=16384,
                temperature=0.7
            )
            if result.get("error"):
                print(f"    ERROR: {result['error']}")
            else:
                print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")
                design_path = RESULTS_DIR / f"exp7_r1_{key}.md"
                design_path.write_text(
                    f"# R1 Design: {model['name']}\n**Perspectiva:** {model['perspective']}\n\n{result['content']}",
                    encoding='utf-8'
                )
            designs[key] = result

        timing["R1"] = time.time() - t0
        print(f"\n  R1 completado en {timing['R1']:.0f}s")

    # Load R2 from disk if exists (always, for report)
    for key in MODELS:
        r2_path = RESULTS_DIR / f"exp7_r2_{key}.md"
        if r2_path.exists() and key not in evaluations:
            content = r2_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            actual = '\n'.join(lines[2:]) if len(lines) > 2 else content
            evaluations[key] = {"content": actual, "tokens_out": len(actual)//4, "time_s": 0, "error": None}

    # ===== R2 =====
    if args.phase in ("r2", "all"):
        print("\n" + "=" * 40)
        print("FASE 2 - R2: Evaluacion Cruzada")
        print("=" * 40)
        t0 = time.time()

        r2_prompt = build_r2_prompt(designs)

        for key, model in MODELS.items():
            if args.model and key != args.model:
                continue
            if key in evaluations and evaluations[key].get("content"):
                print(f"\n  [R2] {model['name']} -- ya existe, skip")
                continue

            print(f"\n  [R2] {model['name']} evaluando 5 disenos...")
            result = call_openrouter(
                model["id"],
                "Eres un evaluador experto de arquitecturas de sistemas. Evalua con rigor y concrecion. Responde en espanol.",
                r2_prompt,
                max_tokens=16384,
                temperature=0.5
            )
            if result.get("error"):
                print(f"    ERROR: {result['error']}")
            else:
                print(f"    OK: {result['tokens_out']} tokens, {result['time_s']}s")
                eval_path = RESULTS_DIR / f"exp7_r2_{key}.md"
                eval_path.write_text(f"# R2 Evaluation: {model['name']}\n\n{result['content']}", encoding='utf-8')
            evaluations[key] = result

        timing["R2"] = time.time() - t0
        print(f"\n  R2 completado en {timing['R2']:.0f}s")

    # ===== R3 =====
    if args.phase in ("r3", "all"):
        print("\n" + "=" * 40)
        print("FASE 2 - R3: Consenso")
        print("=" * 40)
        t0 = time.time()
        consensus = run_r3(evaluations, context)
        timing["R3"] = time.time() - t0
        print(f"\n  R3 completado en {timing['R3']:.0f}s")
    else:
        # Load from disk
        cp = RESULTS_DIR / "exp7_chief_design_v2.md"
        if cp.exists():
            content = cp.read_text(encoding='utf-8')
            lines = content.split('\n')
            actual = '\n'.join(lines[2:]) if len(lines) > 2 else content
            consensus = {"content": actual, "tokens_out": len(actual)//4, "time_s": 0}

    # ===== F3 =====
    if args.phase in ("f3", "all"):
        print("\n" + "=" * 40)
        print("FASE 3: Contraste con Maestro")
        print("=" * 40)
        t0 = time.time()
        maestro_check = run_maestro_check(consensus)
        timing["F3"] = time.time() - t0

    # ===== F4 =====
    if args.phase in ("f4", "all"):
        print("\n" + "=" * 40)
        print("FASE 4: Spec de Implementacion")
        print("=" * 40)
        t0 = time.time()
        impl_spec = run_impl_spec(consensus)
        timing["F4"] = time.time() - t0

    # ===== Report =====
    if args.phase in ("report", "all"):
        print("\n" + "=" * 40)
        print("FASE 5: Report")
        print("=" * 40)

        # Load from disk if not in memory
        if not maestro_check:
            mp = RESULTS_DIR / "exp7_maestro_check.md"
            if mp.exists():
                maestro_check = {"content": mp.read_text(encoding='utf-8'), "tokens_out": 0, "time_s": 0}
        if not impl_spec:
            ip = RESULTS_DIR / "exp7_chief_implementation_spec.md"
            if ip.exists():
                impl_spec = {"content": ip.read_text(encoding='utf-8'), "tokens_out": 0, "time_s": 0}

        generate_report(designs, evaluations, consensus, maestro_check, impl_spec, timing)

    print("\n" + "=" * 60)
    print("EXP 7 COMPLETADO")
    print("=" * 60)
    total_time = sum(timing.values())
    print(f"Tiempo total: {total_time:.0f}s ({total_time/60:.1f}min)")
    for phase, t in timing.items():
        print(f"  {phase}: {t:.0f}s")


if __name__ == "__main__":
    main()
