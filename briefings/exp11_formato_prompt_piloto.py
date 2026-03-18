#!/usr/bin/env python3
"""EXP-11 Piloto — Formato de Prompt: Natural vs JSON vs Python vs Híbrido vs Program

Ejecuta 4-5 variantes del mismo contenido (INT-01) contra un modelo (V3.2)
y compara cobertura, tokens, adherencia al pipeline.

Uso:
  export OPENROUTER_API_KEY=sk-or-...
  python3 exp11_formato_prompt_piloto.py

O:
  python3 exp11_formato_prompt_piloto.py --key sk-or-...
"""

import json
import time
import argparse
import urllib.request
import urllib.error
import os
import re
import datetime

# ═══════════════════════════════════════════
# CASO DE PRUEBA
# ═══════════════════════════════════════════

CASO = """Mi socio quiere vender su parte del negocio. Llevamos 8 años juntos.
El negocio factura €420K/año con margen del 22%. Mi socio tiene el 40%.
Tengo €60K en ahorros. El banco me ofrece financiación al 6.5%.
Mi socio quiere cerrar en 30 días. No sé si puedo comprársela ni si debería."""

# ═══════════════════════════════════════════
# VARIANTE A — Natural (baseline)
# ═══════════════════════════════════════════

PROMPT_A = f"""Eres INT-01: Inteligencia Lógico-Matemática.
Firma: Contradicción formal demostrable entre premisas.
Punto ciego: Lo ambiguo, lo no-axiomatizable.

Aplica los siguientes pasos al caso que te doy:

PASO 1 — EXTRAER (formalizar):
¿Qué se puede contar? ¿Qué se puede medir?
¿Qué magnitudes aparecen con número explícito?
¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?
¿Qué se da por hecho sin verificar?

PASO 2 — CRUZAR (estructurar tipo de problema):
De todas las relaciones, ¿cuántas puedes mover y cuántas están fijadas?
¿Mover una variable mejora todo, o mejorar una empeora otra?
Si empeora otra: ¿hay punto donde ambas sean aceptables, o siempre hay que elegir?

PASO 3 — LENTES:
L1 Álgebra: ¿Cuántas ecuaciones hay y cuántas incógnitas? ¿Alguna contradice a otra?
L2 Análisis: Si aumentas cada variable un poco, ¿qué pasa? ¿Hay efecto desproporcionado?
L6 Lógica: ¿Qué se puede deducir con certeza? ¿Hay premisas que se contradigan?

PASO 4 — INTEGRAR: ¿Qué dicen todas las lentes que coincide? ¿Dónde se contradicen?
PASO 5 — ABSTRAER: ¿Este caso es único o hay una clase de casos con esta estructura?
PASO 6 — FRONTERA: ¿Qué asume este análisis que no ha examinado?

Responde con: hallazgos, firma combinada, y puntos ciegos.

CASO:
{CASO}"""

# ═══════════════════════════════════════════
# VARIANTE B — JSON puro
# ═══════════════════════════════════════════

PROMPT_B = json.dumps({
    "agent": {
        "id": "INT-01",
        "name": "Lógico-Matemática",
        "signature": "Contradicción formal demostrable entre premisas",
        "blind_spot": "Lo ambiguo, lo no-axiomatizable"
    },
    "case": CASO,
    "pipeline": [
        {
            "step": "EXTRAER",
            "action": "formalizar",
            "questions": [
                "¿Qué se puede contar? ¿Qué se puede medir?",
                "¿Qué magnitudes aparecen con número explícito?",
                "¿Qué relación tiene cada número con los demás?",
                "¿Qué se da por hecho sin verificar?"
            ]
        },
        {
            "step": "CRUZAR",
            "action": "estructurar tipo de problema",
            "questions": [
                "¿Cuántas relaciones puedes mover y cuántas están fijadas?",
                "¿Mover una variable mejora todo, o empeora otra?",
                "¿Hay punto de equilibrio o siempre hay que elegir?"
            ]
        },
        {
            "step": "LENTES",
            "lenses": [
                {"id": "L1", "name": "Álgebra", "question": "¿Cuántas ecuaciones hay y cuántas incógnitas? ¿Alguna contradice a otra?"},
                {"id": "L2", "name": "Análisis", "question": "Si aumentas cada variable un poco, ¿qué pasa? ¿Hay efecto desproporcionado?"},
                {"id": "L6", "name": "Lógica", "question": "¿Qué se puede deducir con certeza? ¿Hay premisas que se contradigan?"}
            ]
        },
        {"step": "INTEGRAR", "question": "¿Qué dicen todas las lentes que coincide? ¿Dónde se contradicen?"},
        {"step": "ABSTRAER", "question": "¿Este caso es único o hay una clase de casos con esta estructura?"},
        {"step": "FRONTERA", "question": "¿Qué asume este análisis que no ha examinado?"}
    ],
    "output_schema": {
        "hallazgos": ["string"],
        "firma_combinada": "string",
        "puntos_ciegos": ["string"]
    }
}, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# VARIANTE D — Híbrido (ops en código, preguntas en natural)
# ═══════════════════════════════════════════

PROMPT_D = f"""```python
pipeline = [
    {{"op": "EXTRAER", "target": caso, "output": "datos_formalizados"}},
    {{"op": "CRUZAR", "input": "datos_formalizados", "output": "estructura_problema"}},
    {{"op": "LENTES", "input": "estructura_problema", "lenses": ["L1_algebra", "L2_analisis", "L6_logica"], "output": "perspectivas"}},
    {{"op": "INTEGRAR", "input": "perspectivas", "output": "sintesis"}},
    {{"op": "ABSTRAER", "input": "sintesis", "output": "patron"}},
    {{"op": "FRONTERA", "input": "patron", "output": "limites"}},
]

agent = {{"id": "INT-01", "signature": "Contradicción formal demostrable entre premisas", "blind_spot": "Lo ambiguo, lo no-axiomatizable"}}
```

Ejecuta este pipeline sobre el caso. Preguntas por paso:

**EXTRAER**: ¿Qué se puede contar? ¿Qué magnitudes con número explícito? ¿Qué relación entre números? ¿Qué se da por hecho?
**CRUZAR**: ¿Cuántas relaciones son fijas vs móviles? ¿Hay tradeoffs? ¿Hay equilibrio?
**LENTES**: L1: ¿Ecuaciones vs incógnitas? L2: ¿Sensibilidad a cambios? L6: ¿Premisas contradictorias?
**INTEGRAR**: ¿Convergencia entre lentes? ¿Divergencia?
**ABSTRAER**: ¿Caso único o clase de casos?
**FRONTERA**: ¿Supuestos no examinados?

Output: hallazgos, firma_combinada, puntos_ciegos.

CASO:
{CASO}"""

# ═══════════════════════════════════════════
# VARIANTE E — Prompt-as-Program (todo tipado)
# ═══════════════════════════════════════════

PROMPT_E = json.dumps({
    "agent": {
        "id": "INT-01",
        "signature": "Contradicción formal demostrable entre premisas",
        "blind_spot": "Lo ambiguo, lo no-axiomatizable"
    },
    "case": CASO,
    "program": [
        {
            "op": "EXTRAER",
            "action": "formalizar",
            "input": "$caso",
            "queries": [
                {"type": "cuantificar", "target": "magnitudes", "filter": "explicitas"},
                {"type": "cuantificar", "target": "magnitudes", "filter": "implicitas_medibles"},
                {"type": "relacion", "between": "magnitudes", "ops": ["suma", "producto", "limite"]},
                {"type": "verificar", "target": "supuestos", "status": "no_verificado"}
            ],
            "output": "$datos"
        },
        {
            "op": "CRUZAR",
            "input": "$datos",
            "queries": [
                {"type": "clasificar", "dimension": "movilidad", "values": ["fija", "movil"]},
                {"type": "detectar", "pattern": "tradeoff", "between": "variables"},
                {"type": "detectar", "pattern": "punto_equilibrio", "condition": "si_tradeoff"}
            ],
            "output": "$estructura"
        },
        {
            "op": "LENTES",
            "input": "$estructura",
            "lenses": [
                {
                    "id": "L1", "name": "algebra",
                    "queries": [
                        {"type": "contar", "target": "ecuaciones_vs_incognitas"},
                        {"type": "detectar", "pattern": "contradiccion"}
                    ]
                },
                {
                    "id": "L2", "name": "analisis",
                    "queries": [
                        {"type": "sensibilidad", "method": "delta_incremental", "target": "cada_variable"},
                        {"type": "detectar", "pattern": "efecto_desproporcionado"}
                    ]
                },
                {
                    "id": "L6", "name": "logica",
                    "queries": [
                        {"type": "deducir", "from": "premisas", "certainty": "required"},
                        {"type": "detectar", "pattern": "contradiccion", "scope": "combinaciones_premisas"}
                    ]
                }
            ],
            "output": "$perspectivas"
        },
        {
            "op": "INTEGRAR",
            "input": "$perspectivas",
            "queries": [
                {"type": "convergencia", "across": "lentes"},
                {"type": "divergencia", "across": "lentes"},
                {"type": "emergente", "condition": "solo_visible_en_conjunto"}
            ],
            "output": "$sintesis"
        },
        {
            "op": "ABSTRAER",
            "input": "$sintesis",
            "queries": [
                {"type": "generalizar", "method": "eliminar_nombres_y_numeros"},
                {"type": "clasificar", "target": "patron_residual", "into": "clase_de_casos"}
            ],
            "output": "$patron"
        },
        {
            "op": "FRONTERA",
            "input": "$patron",
            "queries": [
                {"type": "detectar", "target": "supuestos_no_examinados"},
                {"type": "detectar", "target": "dimensiones_no_formalizables"},
                {"type": "condicional", "if": "dimension_no_formalizable_es_importante", "then": "que_cambia"}
            ],
            "output": "$limites"
        }
    ],
    "output_schema": {
        "hallazgos": [{"claim": "string", "evidence": "string", "lens": "string"}],
        "firma_combinada": "string",
        "puntos_ciegos": [{"gap": "string", "severity": "alta|media|baja"}]
    }
}, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════

VARIANTES = {
    "A_natural": PROMPT_A,
    "B_json": PROMPT_B,
    "D_hibrido": PROMPT_D,
    "E_program": PROMPT_E,
}

PIPELINE_STEPS = ["EXTRAER", "CRUZAR", "LENTES", "INTEGRAR", "ABSTRAER", "FRONTERA"]

# Preguntas clave de INT-01 para medir cobertura
COVERAGE_KEYWORDS = [
    # EXTRAER
    "420", "22%", "40%", "60", "6.5", "30 día",
    # CRUZAR
    "tradeoff", "equilibrio", "fij", "variable",
    # LENTES
    "ecuación", "incógnita", "sensib", "contradic",
    # INTEGRAR
    "coincid", "converg", "diverg",
    # ABSTRAER
    "patrón", "clase", "estructura",
    # FRONTERA
    "supuesto", "asume", "no examinad",
]


def call_openrouter(prompt, model, api_key, temperature=0.3):
    """Call OpenRouter API."""
    url = "https://openrouter.ai/api/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://omni-mind.dev",
        "X-Title": "EXP-11 Formato Prompt",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            elapsed = time.time() - t0
            return data, elapsed
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:500]}"}, time.time() - t0
    except Exception as e:
        return {"error": str(e)}, time.time() - t0


def analyze_output(text):
    """Analizar output para métricas automáticas."""
    text_lower = text.lower()

    # Cobertura de keywords
    found = sum(1 for kw in COVERAGE_KEYWORDS if kw.lower() in text_lower)
    coverage = found / len(COVERAGE_KEYWORDS)

    # Adherencia al pipeline (¿menciona los 6 pasos?)
    steps_found = sum(1 for step in PIPELINE_STEPS if step.lower() in text_lower)
    adherence = steps_found / len(PIPELINE_STEPS)

    # Output estructurado (¿contiene hallazgos, firma, puntos ciegos?)
    has_hallazgos = any(kw in text_lower for kw in ["hallazgo", "finding", "descubr"])
    has_firma = any(kw in text_lower for kw in ["firma", "signature", "contradicc"])
    has_ciegos = any(kw in text_lower for kw in ["punto ciego", "blind spot", "limitac", "supuesto"])
    output_completeness = sum([has_hallazgos, has_firma, has_ciegos]) / 3

    return {
        "coverage": round(coverage, 2),
        "coverage_found": found,
        "coverage_total": len(COVERAGE_KEYWORDS),
        "adherence": round(adherence, 2),
        "steps_found": steps_found,
        "output_completeness": round(output_completeness, 2),
        "has_hallazgos": has_hallazgos,
        "has_firma": has_firma,
        "has_ciegos": has_ciegos,
        "output_length": len(text),
    }


def run_pilot(api_key, model="deepseek/deepseek-v3.2"):
    """Ejecutar piloto: 4 variantes × INT-01 × 1 modelo."""
    results = []

    print(f"\n{'='*70}")
    print(f"  EXP-11 PILOTO — Formato de Prompt")
    print(f"  Modelo: {model}")
    print(f"  Variantes: {list(VARIANTES.keys())}")
    print(f"  Caso: socio/buyout")
    print(f"{'='*70}\n")

    for name, prompt in VARIANTES.items():
        print(f"  [{name}] Ejecutando...", end="", flush=True)

        tokens_in = len(prompt.split())  # Aprox
        resp, elapsed = call_openrouter(prompt, model, api_key)

        if "error" in resp:
            print(f" ERROR: {resp['error'][:100]}")
            results.append({"variant": name, "error": resp["error"][:200]})
            continue

        # Extraer respuesta
        choice = resp.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "")
        usage = resp.get("usage", {})

        # Analizar
        metrics = analyze_output(text)

        result = {
            "variant": name,
            "model": model,
            "tokens_input": usage.get("prompt_tokens", 0),
            "tokens_output": usage.get("completion_tokens", 0),
            "tokens_total": usage.get("total_tokens", 0),
            "time_s": round(elapsed, 1),
            "prompt_chars": len(prompt),
            **metrics,
            "output_preview": text[:500],
            "output_full": text,
        }
        results.append(result)

        print(f" OK ({elapsed:.1f}s, {usage.get('total_tokens', '?')} tok, "
              f"cov={metrics['coverage']:.0%}, adh={metrics['adherence']:.0%})")

    return results


def save_results(results, output_path):
    """Guardar resultados en markdown."""
    now = datetime.datetime.now().isoformat()[:19]

    md = f"# EXP-11 Piloto — Formato de Prompt\n\n"
    md += f"Fecha: {now}\n"
    md += f"Modelo: {results[0].get('model', '?') if results else '?'}\n"
    md += f"Caso: Socio buyout (420K€, 40%, 8 años)\n\n"

    md += "## Resumen\n\n"
    md += "| Variante | Tokens In | Tokens Out | Cobertura | Adherencia | Completitud | Tiempo |\n"
    md += "|----------|----------|-----------|-----------|------------|-------------|--------|\n"
    for r in results:
        if "error" in r:
            md += f"| {r['variant']} | ERROR | | | | | |\n"
            continue
        md += (f"| {r['variant']} | {r['tokens_input']} | {r['tokens_output']} | "
               f"{r['coverage']:.0%} ({r['coverage_found']}/{r['coverage_total']}) | "
               f"{r['adherence']:.0%} ({r['steps_found']}/6) | "
               f"{r['output_completeness']:.0%} | {r['time_s']}s |\n")

    md += "\n## Análisis\n\n"
    # Ranking por cobertura
    valid = [r for r in results if "error" not in r]
    if valid:
        by_cov = sorted(valid, key=lambda x: x["coverage"], reverse=True)
        md += f"**Mejor cobertura**: {by_cov[0]['variant']} ({by_cov[0]['coverage']:.0%})\n"
        by_eff = sorted(valid, key=lambda x: x["coverage"] / max(x["tokens_output"], 1), reverse=True)
        md += f"**Más eficiente** (cobertura/token): {by_eff[0]['variant']}\n"
        by_adh = sorted(valid, key=lambda x: x["adherence"], reverse=True)
        md += f"**Mejor adherencia al pipeline**: {by_adh[0]['variant']} ({by_adh[0]['adherence']:.0%})\n\n"

    md += "## Detalle por variante\n\n"
    for r in results:
        if "error" in r:
            md += f"### {r['variant']}\n\nERROR: {r['error']}\n\n"
            continue
        md += f"### {r['variant']}\n\n"
        md += f"- Tokens: {r['tokens_input']} in / {r['tokens_output']} out\n"
        md += f"- Prompt: {r['prompt_chars']} chars\n"
        md += f"- Cobertura: {r['coverage']:.0%} ({r['coverage_found']}/{r['coverage_total']})\n"
        md += f"- Adherencia: {r['adherence']:.0%} ({r['steps_found']}/6 pasos)\n"
        md += f"- Completitud output: {r['output_completeness']:.0%} "
        md += f"(hallazgos={'✅' if r['has_hallazgos'] else '❌'} "
        md += f"firma={'✅' if r['has_firma'] else '❌'} "
        md += f"ciegos={'✅' if r['has_ciegos'] else '❌'})\n"
        md += f"- Tiempo: {r['time_s']}s\n\n"
        md += f"**Output (primeros 800 chars):**\n\n"
        md += f"```\n{r['output_full'][:800]}\n```\n\n"

    with open(output_path, "w") as f:
        f.write(md)
    print(f"\nResultados guardados en: {output_path}")

    # También guardar JSON crudo
    json_path = output_path.replace(".md", ".json")
    with open(json_path, "w") as f:
        # Excluir output_full del JSON para no hacerlo enorme
        slim = [{k: v for k, v in r.items() if k != "output_full"} for r in results]
        json.dump(slim, f, indent=2, ensure_ascii=False)
    print(f"JSON guardado en: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EXP-11 Piloto: Formato de Prompt")
    parser.add_argument("--key", default=os.environ.get("OPENROUTER_API_KEY", ""),
                       help="OpenRouter API key")
    parser.add_argument("--model", default="deepseek/deepseek-v3.2",
                       help="Modelo a usar")
    parser.add_argument("--output", default=None,
                       help="Path para resultados (.md)")
    args = parser.parse_args()

    if not args.key:
        print("ERROR: Necesitas API key. Usa --key sk-or-... o export OPENROUTER_API_KEY=...")
        exit(1)

    output = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "results", "exp11_piloto.md"
    )

    results = run_pilot(args.key, args.model)
    save_results(results, output)

    # Print quick summary
    valid = [r for r in results if "error" not in r]
    if valid:
        print(f"\n{'='*70}")
        print(f"  RESUMEN RÁPIDO")
        print(f"{'='*70}")
        for r in sorted(valid, key=lambda x: x["coverage"], reverse=True):
            print(f"  {r['variant']:15s} cov={r['coverage']:.0%} adh={r['adherence']:.0%} "
                  f"tok_out={r['tokens_output']} time={r['time_s']}s")
