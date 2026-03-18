#!/usr/bin/env python3
"""EXP-11.1 — ¿Se puede generar ambigüedad productiva dentro de JSON/Python?

Pregunta: E fracasó porque las queries tipadas son slot-filling (el modelo rellena huecos).
D ganó porque las preguntas naturales activan razonamiento rico.
¿Hay un punto medio? ¿Queries estructuradas que CONTENGAN ambigüedad productiva?

3 nuevas variantes + D como baseline:
- D: híbrido original (pipeline código + preguntas natural separadas) — BASELINE
- F: queries con tensión semántica dentro del JSON (natural embedido en estructura)  
- G: queries con metáforas/provocaciones dentro del JSON
- H: JSON puro pero con "reasoning_hints" en natural por cada query

Uso:
  python3 exp11_1_ambiguedad_estructurada.py --key sk-or-...
"""

import json
import time
import argparse
import urllib.request
import urllib.error
import os
import datetime

# ═══════════════════════════════════════════
# CASO
# ═══════════════════════════════════════════

CASO = """Mi socio quiere vender su parte del negocio. Llevamos 8 años juntos.
El negocio factura €420K/año con margen del 22%. Mi socio tiene el 40%.
Tengo €60K en ahorros. El banco me ofrece financiación al 6.5%.
Mi socio quiere cerrar en 30 días. No sé si puedo comprársela ni si debería."""

# ═══════════════════════════════════════════
# VARIANTE D — Híbrido (BASELINE del EXP-11)
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
# VARIANTE F — Tensión semántica dentro del JSON
# Las preguntas son naturales pero VIVEN DENTRO de cada operación como campo "explore"
# ═══════════════════════════════════════════

PROMPT_F = json.dumps({
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
            "explore": [
                "¿Qué se puede contar aquí? ¿Qué se puede medir?",
                "¿Qué magnitudes aparecen con número explícito?",
                "¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan mutuamente?",
                "¿Qué se da por hecho sin que nadie lo haya verificado?"
            ],
            "output": "$datos"
        },
        {
            "op": "CRUZAR",
            "input": "$datos",
            "explore": [
                "De todo lo que encontraste, ¿cuánto puedes mover y cuánto está fijado?",
                "Si mejoras una variable, ¿empeoras otra? ¿O hay camino donde todo mejora?",
                "¿Existe un punto donde ambos lados aceptarían, o siempre hay que elegir?"
            ],
            "output": "$estructura"
        },
        {
            "op": "LENTES",
            "input": "$estructura",
            "lenses": [
                {
                    "id": "L1", "name": "álgebra",
                    "explore": "¿Cuántas ecuaciones tienes y cuántas incógnitas? ¿Alguna ecuación contradice a otra? ¿Hay información redundante que no aporta nada nuevo?"
                },
                {
                    "id": "L2", "name": "análisis",
                    "explore": "Si mueves cada variable un poco — un 10%, un 20% — ¿qué pasa? ¿Alguna variable tiene un efecto desproporcionado? ¿Hay un punto donde aumentar empieza a empeorar?"
                },
                {
                    "id": "L6", "name": "lógica",
                    "explore": "¿Qué puedes deducir con certeza absoluta de las premisas? ¿Hay alguna combinación de premisas que se contradiga? ¿El sujeto cree cosas incompatibles entre sí?"
                }
            ],
            "output": "$perspectivas"
        },
        {
            "op": "INTEGRAR",
            "input": "$perspectivas",
            "explore": [
                "¿Qué dicen TODAS las lentes que coincide? Ese es tu hallazgo más sólido.",
                "¿Dónde se contradicen las lentes entre sí? Esa tensión es información valiosa.",
                "¿Hay algo que solo aparece al mirar todas juntas, pero que ninguna lente veía sola?"
            ],
            "output": "$sintesis"
        },
        {
            "op": "ABSTRAER",
            "input": "$sintesis",
            "explore": [
                "Si quitas los nombres, los números y los detalles específicos — ¿qué patrón queda?",
                "¿Este caso pertenece a una clase de casos que ya conoces? ¿Cuál?"
            ],
            "output": "$patron"
        },
        {
            "op": "FRONTERA",
            "input": "$patron",
            "explore": [
                "¿Qué asume todo este análisis que NO ha examinado?",
                "¿Hay algo que no se puede expresar como número o ecuación? Si ESO fuera lo más importante, ¿qué cambia?",
                "¿Qué preguntaría alguien que piensa completamente diferente a INT-01?"
            ],
            "output": "$limites"
        }
    ],
    "output_format": {
        "hallazgos": "lista de descubrimientos con evidencia",
        "firma_combinada": "la contradicción central que define este caso",
        "puntos_ciegos": "lo que este análisis NO puede ver"
    }
}, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# VARIANTE G — Metáforas y provocaciones dentro del JSON
# Cada operación tiene un "provoke" que usa lenguaje figurativo para activar pensamiento lateral
# ═══════════════════════════════════════════

PROMPT_G = json.dumps({
    "agent": {
        "id": "INT-01",
        "signature": "Contradicción formal demostrable entre premisas",
        "blind_spot": "Lo ambiguo, lo no-axiomatizable"
    },
    "case": CASO,
    "program": [
        {
            "op": "EXTRAER",
            "explore": "¿Qué se puede contar? ¿Qué magnitudes tienen número? ¿Qué relaciones hay entre ellos? ¿Qué se da por hecho?",
            "provoke": "Los números que faltan a veces son más importantes que los que están. ¿Qué número necesitarías para tomar la decisión y nadie te lo ha dado?",
            "output": "$datos"
        },
        {
            "op": "CRUZAR",
            "input": "$datos",
            "explore": "¿Qué variables son fijas y cuáles móviles? ¿Hay tradeoffs? ¿Hay punto de equilibrio?",
            "provoke": "Si este problema fuera una balanza, ¿qué hay en cada plato? ¿Se puede añadir peso a un lado sin sacar del otro?",
            "output": "$estructura"
        },
        {
            "op": "LENTES",
            "input": "$estructura",
            "lenses": [
                {
                    "id": "L1", "name": "álgebra",
                    "explore": "¿Cuántas ecuaciones y cuántas incógnitas? ¿Alguna contradice a otra?",
                    "provoke": "¿Hay una ecuación escondida que nadie ha escrito pero todo el mundo asume?"
                },
                {
                    "id": "L2", "name": "análisis",
                    "explore": "¿Sensibilidad a cambios? ¿Efecto desproporcionado?",
                    "provoke": "¿Qué variable, si cambiara un 1%, haría que toda la decisión se invirtiera?"
                },
                {
                    "id": "L6", "name": "lógica",
                    "explore": "¿Qué se deduce con certeza? ¿Premisas contradictorias?",
                    "provoke": "El sujeto dice que no sabe si debería comprar — pero ¿ya ha decidido y no lo admite?"
                }
            ],
            "output": "$perspectivas"
        },
        {
            "op": "INTEGRAR",
            "input": "$perspectivas",
            "explore": "¿Convergencia entre lentes? ¿Divergencia? ¿Emergencia?",
            "provoke": "Si las tres lentes fueran tres personas en una mesa, ¿sobre qué estarían de acuerdo y sobre qué discutirían?",
            "output": "$sintesis"
        },
        {
            "op": "ABSTRAER",
            "input": "$sintesis",
            "explore": "¿Patrón residual? ¿Clase de casos?",
            "provoke": "Si le cuentas este problema a alguien sin decirle los números ni los nombres, ¿qué diría? ¿Lo reconocería?",
            "output": "$patron"
        },
        {
            "op": "FRONTERA",
            "input": "$patron",
            "explore": "¿Supuestos no examinados? ¿Dimensiones no formalizables?",
            "provoke": "INT-01 es ciega a lo que no se puede poner en una ecuación. ¿Qué está pasando aquí que no cabe en ningún número?",
            "output": "$limites"
        }
    ],
    "output_format": {
        "hallazgos": "lista con evidencia",
        "firma_combinada": "la contradicción central",
        "puntos_ciegos": "lo que este análisis NO puede ver"
    }
}, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# VARIANTE H — JSON con reasoning_hints por query
# Estructura de E pero cada query tiene un "hint" en natural que guía el razonamiento
# ═══════════════════════════════════════════

PROMPT_H = json.dumps({
    "agent": {
        "id": "INT-01",
        "signature": "Contradicción formal demostrable entre premisas",
        "blind_spot": "Lo ambiguo, lo no-axiomatizable"
    },
    "case": CASO,
    "program": [
        {
            "op": "EXTRAER",
            "queries": [
                {"type": "cuantificar", "target": "magnitudes", "filter": "explicitas",
                 "hint": "Busca todos los números que aparecen literalmente en el texto"},
                {"type": "cuantificar", "target": "magnitudes", "filter": "implicitas",
                 "hint": "¿Qué se podría medir pero nadie ha medido? ¿Cuánto vale realmente el 40%?"},
                {"type": "relacion", "between": "magnitudes",
                 "hint": "¿Los €60K se suman a la financiación? ¿El margen del 22% se multiplica por los 8 años? ¿El 6.5% limita cuánto puede pedir?"},
                {"type": "verificar", "target": "supuestos",
                 "hint": "¿Quién dijo que el 40% vale €X? ¿Es precio de mercado o precio de socio? ¿Los 30 días son reales o presión?"}
            ],
            "output": "$datos"
        },
        {
            "op": "CRUZAR",
            "input": "$datos",
            "queries": [
                {"type": "clasificar", "dimension": "movilidad",
                 "hint": "La facturación puede crecer o bajar. El plazo de 30 días es móvil si se negocia. ¿Qué es realmente inamovible?"},
                {"type": "detectar", "pattern": "tradeoff",
                 "hint": "Si pide más financiación, paga más interés. Si pide plazo, el socio puede buscar otro comprador. ¿Hay un tradeoff escondido?"},
                {"type": "detectar", "pattern": "punto_equilibrio",
                 "hint": "¿Existe un precio donde ambos ganan, o este es un juego de suma cero?"}
            ],
            "output": "$estructura"
        },
        {
            "op": "LENTES",
            "input": "$estructura",
            "lenses": [
                {"id": "L1", "name": "algebra",
                 "queries": [
                     {"type": "contar", "target": "ecuaciones_vs_incognitas",
                      "hint": "Ecuaciones: valoración, capacidad de pago, coste financiación. Incógnitas: valor real, precio justo, capacidad futura. ¿Cuadra?"},
                     {"type": "detectar", "pattern": "contradiccion",
                      "hint": "¿Los números que da el sujeto son compatibles entre sí? ¿Puede pagar lo que cuesta?"}
                 ]},
                {"id": "L2", "name": "analisis",
                 "queries": [
                     {"type": "sensibilidad", "target": "variables",
                      "hint": "Si el margen baja de 22% a 18%, ¿sigue siendo viable? Si el tipo sube a 8%, ¿cambia la decisión?"},
                     {"type": "detectar", "pattern": "efecto_desproporcionado",
                      "hint": "¿Hay una variable que al moverse un poco cambia todo?"}
                 ]},
                {"id": "L6", "name": "logica",
                 "queries": [
                     {"type": "deducir", "from": "premisas",
                      "hint": "Con 420K×22%×40% = ¿cuánto genera el 40%? Si eso no cubre el préstamo, la respuesta es matemática"},
                     {"type": "detectar", "pattern": "contradiccion",
                      "hint": "Dice que no sabe si debería, pero pregunta si puede. ¿Ya decidió y solo busca validación?"}
                 ]}
            ],
            "output": "$perspectivas"
        },
        {
            "op": "INTEGRAR",
            "input": "$perspectivas",
            "queries": [
                {"type": "convergencia", "hint": "¿Las tres lentes dicen lo mismo sobre si puede pagar?"},
                {"type": "divergencia", "hint": "¿Álgebra dice sí pero lógica dice no? Esa tensión es el hallazgo"},
                {"type": "emergente", "hint": "¿Qué solo se ve al combinar las tres perspectivas?"}
            ],
            "output": "$sintesis"
        },
        {
            "op": "ABSTRAER",
            "queries": [
                {"type": "generalizar", "hint": "Sin nombres ni números: ¿esto es 'socio quiere salir, otro quiere quedarse con financiación'?"},
                {"type": "clasificar", "into": "clase_de_casos", "hint": "¿Es un buyout clásico, una ruptura forzada, o algo diferente?"}
            ],
            "output": "$patron"
        },
        {
            "op": "FRONTERA",
            "queries": [
                {"type": "detectar", "target": "supuestos_no_examinados",
                 "hint": "¿Y si el socio no quiere vender sino que quiere ser comprado? ¿Y si el negocio sin el socio vale menos?"},
                {"type": "detectar", "target": "dimensiones_no_formalizables",
                 "hint": "8 años juntos no caben en una ecuación. ¿Qué hay en esos 8 años que los números no capturan?"}
            ],
            "output": "$limites"
        }
    ],
    "output_format": {
        "hallazgos": [{"claim": "string", "evidence": "string", "lens": "string"}],
        "firma_combinada": "string",
        "puntos_ciegos": [{"gap": "string", "severity": "alta|media|baja"}]
    }
}, ensure_ascii=False, indent=2)

# ═══════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════

VARIANTES = {
    "D_hibrido": PROMPT_D,
    "F_tension": PROMPT_F,
    "G_metafora": PROMPT_G,
    "H_hints": PROMPT_H,
}

PIPELINE_STEPS = ["EXTRAER", "CRUZAR", "LENTES", "INTEGRAR", "ABSTRAER", "FRONTERA"]

COVERAGE_KEYWORDS = [
    "420", "22%", "40%", "60", "6.5", "30 día",
    "tradeoff", "equilibrio", "fij", "variable",
    "ecuación", "incógnita", "sensib", "contradic",
    "coincid", "converg", "diverg",
    "patrón", "clase", "estructura",
    "supuesto", "asume", "no examinad",
]

# Bonus: keywords que indican razonamiento profundo (ambiguity payoff)
DEPTH_KEYWORDS = [
    "sin embargo", "pero", "tension", "paradoj", "contradicci",
    "no obvio", "escondid", "implicit", "asume sin",
    "cuestión de fondo", "realment", "en realidad",
    "lo que no dice", "lo que falta", "invisible",
    "8 años", "relación", "confianza", "emocional",
]


def call_openrouter(prompt, model, api_key, temperature=0.3):
    url = "https://openrouter.ai/api/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://omni-mind.dev",
        "X-Title": "EXP-11.1 Ambiguedad Estructurada",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode()), time.time() - t0
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.read().decode()[:500]}"}, time.time() - t0
    except Exception as e:
        return {"error": str(e)}, time.time() - t0


def analyze_output(text):
    text_lower = text.lower()
    found_cov = sum(1 for kw in COVERAGE_KEYWORDS if kw.lower() in text_lower)
    coverage = found_cov / len(COVERAGE_KEYWORDS)
    steps_found = sum(1 for step in PIPELINE_STEPS if step.lower() in text_lower)
    adherence = steps_found / len(PIPELINE_STEPS)
    has_hallazgos = any(kw in text_lower for kw in ["hallazgo", "finding", "descubr"])
    has_firma = any(kw in text_lower for kw in ["firma", "signature", "contradicc"])
    has_ciegos = any(kw in text_lower for kw in ["punto ciego", "blind spot", "limitac", "supuesto"])
    output_completeness = sum([has_hallazgos, has_firma, has_ciegos]) / 3

    # Depth: indicadores de razonamiento profundo
    found_depth = sum(1 for kw in DEPTH_KEYWORDS if kw.lower() in text_lower)
    depth = found_depth / len(DEPTH_KEYWORDS)

    return {
        "coverage": round(coverage, 2),
        "coverage_found": found_cov,
        "coverage_total": len(COVERAGE_KEYWORDS),
        "adherence": round(adherence, 2),
        "steps_found": steps_found,
        "output_completeness": round(output_completeness, 2),
        "has_hallazgos": has_hallazgos,
        "has_firma": has_firma,
        "has_ciegos": has_ciegos,
        "depth": round(depth, 2),
        "depth_found": found_depth,
        "depth_total": len(DEPTH_KEYWORDS),
        "output_length": len(text),
    }


def run_pilot(api_key, model="deepseek/deepseek-v3.2"):
    results = []
    print(f"\n{'='*70}")
    print(f"  EXP-11.1 — Ambigüedad Estructurada")
    print(f"  Modelo: {model}")
    print(f"  Variantes: {list(VARIANTES.keys())}")
    print(f"  Pregunta: ¿Se puede generar ambigüedad productiva dentro de JSON?")
    print(f"{'='*70}\n")

    for name, prompt in VARIANTES.items():
        print(f"  [{name}] Ejecutando...", end="", flush=True)
        resp, elapsed = call_openrouter(prompt, model, api_key)
        if "error" in resp:
            print(f" ERROR: {resp['error'][:100]}")
            results.append({"variant": name, "error": resp["error"][:200]})
            continue
        choice = resp.get("choices", [{}])[0]
        text = choice.get("message", {}).get("content", "")
        usage = resp.get("usage", {})
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
            "output_full": text,
        }
        results.append(result)
        print(f" OK ({elapsed:.1f}s, {usage.get('total_tokens', '?')} tok, "
              f"cov={metrics['coverage']:.0%}, depth={metrics['depth']:.0%})")
    return results


def save_results(results, output_path):
    now = datetime.datetime.now().isoformat()[:19]
    md = f"# EXP-11.1 — Ambigüedad Estructurada\n\n"
    md += f"Fecha: {now}\n"
    md += f"Modelo: {results[0].get('model', '?') if results else '?'}\n"
    md += f"Pregunta: ¿Se puede generar ambigüedad productiva dentro de JSON/Python?\n\n"

    md += "## Resumen\n\n"
    md += "| Variante | Tok In | Tok Out | Cobertura | Adherencia | Depth | Completitud | Tiempo |\n"
    md += "|----------|--------|---------|-----------|------------|-------|-------------|--------|\n"
    for r in results:
        if "error" in r:
            md += f"| {r['variant']} | ERROR | | | | | | |\n"
            continue
        md += (f"| {r['variant']} | {r['tokens_input']} | {r['tokens_output']} | "
               f"{r['coverage']:.0%} ({r['coverage_found']}/{r['coverage_total']}) | "
               f"{r['adherence']:.0%} | "
               f"{r['depth']:.0%} ({r['depth_found']}/{r['depth_total']}) | "
               f"{r['output_completeness']:.0%} | {r['time_s']}s |\n")

    md += "\n## Análisis\n\n"
    valid = [r for r in results if "error" not in r]
    if valid:
        by_cov = sorted(valid, key=lambda x: x["coverage"], reverse=True)
        by_depth = sorted(valid, key=lambda x: x["depth"], reverse=True)
        combined = sorted(valid, key=lambda x: x["coverage"] * 0.5 + x["depth"] * 0.5, reverse=True)
        md += f"**Mejor cobertura**: {by_cov[0]['variant']} ({by_cov[0]['coverage']:.0%})\n"
        md += f"**Mayor profundidad**: {by_depth[0]['variant']} ({by_depth[0]['depth']:.0%})\n"
        md += f"**Mejor combinado** (cov×50% + depth×50%): {combined[0]['variant']}\n\n"

        # ¿Alguna variante JSON supera a D en profundidad?
        d_result = next((r for r in valid if r["variant"] == "D_hibrido"), None)
        if d_result:
            better_depth = [r for r in valid if r["depth"] > d_result["depth"] and r["variant"] != "D_hibrido"]
            if better_depth:
                md += f"**🔑 Variantes JSON que superan a D en profundidad**: {', '.join(r['variant'] for r in better_depth)}\n"
                md += "Esto indica que SÍ se puede generar ambigüedad productiva dentro de JSON.\n\n"
            else:
                md += "**Ninguna variante JSON supera a D en profundidad**. El híbrido con preguntas naturales SEPARADAS sigue siendo superior.\n\n"

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
        md += f"- Profundidad: {r['depth']:.0%} ({r['depth_found']}/{r['depth_total']})\n"
        md += f"- Completitud: {r['output_completeness']:.0%}\n"
        md += f"- Tiempo: {r['time_s']}s\n\n"
        md += f"**Output (primeros 1000 chars):**\n\n```\n{r['output_full'][:1000]}\n```\n\n"

    with open(output_path, "w") as f:
        f.write(md)
    print(f"\nResultados guardados en: {output_path}")
    json_path = output_path.replace(".md", ".json")
    with open(json_path, "w") as f:
        slim = [{k: v for k, v in r.items() if k != "output_full"} for r in results]
        json.dump(slim, f, indent=2, ensure_ascii=False)
    print(f"JSON guardado en: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EXP-11.1: Ambigüedad Estructurada")
    parser.add_argument("--key", default=os.environ.get("OPENROUTER_API_KEY", ""),
                       help="OpenRouter API key")
    parser.add_argument("--model", default="deepseek/deepseek-v3.2")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    if not args.key:
        print("ERROR: --key sk-or-... o export OPENROUTER_API_KEY=...")
        exit(1)

    output = args.output or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "results", "exp11_1_ambiguedad.md"
    )

    results = run_pilot(args.key, args.model)
    save_results(results, output)

    valid = [r for r in results if "error" not in r]
    if valid:
        print(f"\n{'='*70}")
        print(f"  RESUMEN")
        print(f"{'='*70}")
        for r in sorted(valid, key=lambda x: x["coverage"] * 0.5 + x["depth"] * 0.5, reverse=True):
            print(f"  {r['variant']:15s} cov={r['coverage']:.0%} depth={r['depth']:.0%} "
                  f"adh={r['adherence']:.0%} tok={r['tokens_output']} t={r['time_s']}s")
