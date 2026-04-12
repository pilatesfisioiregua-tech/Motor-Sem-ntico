"""
POC Números como Adjetivos — 4 condiciones comparativas
Fecha: 2026-04-12

Prueba la tesis: "Los datos numéricos son adjetivos comprimidos que califican
al sujeto especificando su posición en un eje."

4 condiciones:
  A. CON reclasificación NUM→adj + Opus enjaulado
  B. CON reclasificación NUM→adj + Sonnet enjaulado
  C. SIN reclasificación (NUM=cardinal) + Opus enjaulado
  D. SIN reclasificación (NUM=cardinal) + Sonnet enjaulado

Cada condición ejecuta el pipeline E2E:
  Simbionte v4 → H1 Haiku (clasifica función adj de números) → LLM enjaulado → Traductor

Ref: CAPA_0_ESPECIFICACION.md §0 "Principio de los datos numéricos como adjetivos"
"""

import json
import time
import sys
import os
import numpy as np
from copy import deepcopy

sys.path.insert(0, os.path.dirname(__file__))

import spacy
import anthropic

API_KEY = "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"

# ============================================================
# SYSTEM PROMPTS (Capa 2) — idénticos para las 4 condiciones
# ============================================================

SYSTEM_PROMPT = """Eres OMNI_MIND_EXEC_ENGINE. Emites JSON bytecode. Cero lenguaje natural.

REGLAS ABSOLUTAS:
1. Tu output es EXCLUSIVAMENTE JSON válido.
2. Evalúas las dims cognitivas basándote en el análisis estructural del Simbionte.
3. NUNCA generas texto explicativo, saludos ni disculpas.

DIMS A EVALUAR (escala 0-5):
- epist_calibracion: ¿distingue entre lo que sabe y lo que supone?
- cogn_fuerza_equilibrio: ¿hay fuerzas opuestas en equilibrio destructivo?
- cog_pensamiento_sistemico: ¿ve conexiones entre partes o solo partes aisladas?
- f1_conservar: ¿protege lo que funciona?
- f3_depurar: ¿identifica ineficiencias?
- lente_salud: ¿el sistema funciona o está disfuncional?
- gob_sin_medir: ¿gobernanza sin métricas adecuadas? (0=mide bien, 5=ciega)
- cib_escalada_simetrica: ¿feedback positivo que amplifica conflicto?
- cogn_fuerza_patron: ¿patrones predecibles y repetitivos?
- dato_como_escudo: ¿los actores usan datos numéricos para justificar posición individual? (0=no, 5=sí)
- coherencia_datos: ¿los datos individuales forman un todo coherente o se contradicen sistémicamente? (0=coherentes, 5=incoherentes)

ACCIONES: romper_simetria, reforzar_compromiso, desescalar, reencuadrar, confrontar_disonancia, solicitar_especificidad, escalar_humano, registrar_sin_accion

SCHEMA:
{"diagnostico":{"patron_principal":"...","confianza":0.0-1.0,"dims_evaluadas":{...}},"prescripcion":{"accion":"...","instrucciones_traductor":["...","...","..."]},"metadata":{"geometria_cumplida":true}}"""


def build_input_msg(texto, resumen, con_adj=True):
    """Construye el mensaje de input para el LLM enjaulado."""
    mode = "CON reclasificación NUM→adjetivo" if con_adj else "SIN reclasificación (NUM=cardinal genérico)"

    msg = f"""INPUT (primeros 600 chars):
{texto[:600]}...

ANÁLISIS SIMBIONTE ({mode}):
- F_G global: {resumen['fg_global']}
- Patrones detectados: {resumen['patrones_detectados']}
- Ratio condicional: {resumen['ratio_condicional']}
- Ratio nominalización: {resumen['ratio_nominalizacion']}
- Ratio adversativo: {resumen['ratio_adversativo']}
- Top funciones: {json.dumps(resumen['top_funciones'], ensure_ascii=False)}
"""
    if con_adj and resumen.get('num_como_adj'):
        msg += f"""
NÚMEROS RECLASIFICADOS COMO ADJETIVOS:
{json.dumps(resumen['num_como_adj'], ensure_ascii=False, indent=2)}

Nota: cada dato numérico ha sido clasificado por su FUNCIÓN ADJETIVAL en contexto.
"47 millones" no es un número — es un adjetivo especificativo que posiciona a "empresa" en el eje de facturación.
"sus 340 euros" no es un número — es un adjetivo posesivo que vincula el coste al director comercial.
"solo 1.200 euros" no es un número — es un adjetivo indefinido con matiz de insuficiencia.
"""
    msg += "\nEvalúa las 11 dims cognitivas y genera bytecode."
    return msg


def run_condition(texto, nlp, client, model, con_adj, label):
    """Ejecuta una condición del experimento."""
    print(f"\n{'='*60}")
    print(f"CONDICIÓN {label}: {'CON' if con_adj else 'SIN'} reclasificación + {model.split('-')[1].upper()}")
    print(f"{'='*60}")

    t0 = time.time()

    # Capa 0: Simbionte
    doc = nlp(texto)
    from poc_capa0_v4 import calcular_vector_simbionte, tokens_funcionales, SUFIJOS_OPACOS, contar_adversativos, safe_div
    from clasificador_funcional import clasificar_token, FUNC_NAMES, distribucion_funcional

    vector, func_result = calcular_vector_simbionte(doc)
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv = contar_adversativos(doc)
    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs) * 0.25 + safe_div(n_nom, n_total) * 0.15 + safe_div(n_adv, n_total) * 0.20)))
    sents = list(doc.sents)

    # Top funciones
    top_funcs = sorted(
        [(FUNC_NAMES[i], func_result["distribucion"][i])
         for i in range(len(func_result["distribucion"]))
         if func_result["distribucion"][i] > 0.01],
        key=lambda x: -x[1]
    )[:7]

    # Patrones
    patrones = []
    if n_adv >= 2 and n_cnd >= 1:
        patrones.append("equilibrio_nash_posible")
    n_causal = sum(1 for s in sents for t in s if t.dep_ == "mark" and t.lemma_.lower() in ("porque", "ya", "puesto", "dado", "como", "debido"))
    if n_causal >= 2:
        patrones.append("feedback_ciclico")
    if safe_div(n_nom, n_total) > 0.06:
        patrones.append("gobernanza_opaca")
    n_sub = sum(1 for t in toks if t.dep_ in ("advcl", "ccomp", "xcomp"))
    if safe_div(n_sub, len(sents)) > 0.3:
        patrones.append("pensamiento_sistemico")

    resumen = {
        "fg_global": round(fg, 3),
        "patrones_detectados": patrones,
        "ratio_condicional": round(safe_div(n_cnd, n_verbs), 3),
        "ratio_nominalizacion": round(safe_div(n_nom, n_total), 3),
        "ratio_adversativo": round(safe_div(n_adv, n_total), 3),
        "top_funciones": {name: round(val, 3) for name, val in top_funcs},
    }

    # H1: Clasificar números como adjetivos (solo si con_adj=True)
    num_como_adj = {}
    h1_cost = 0
    if con_adj:
        # Recoger todos los NUM con needs_haiku=True
        nums_for_haiku = []
        for t in doc:
            if t.pos_ == "NUM":
                func, needs_haiku = clasificar_token(t)
                if needs_haiku:
                    nums_for_haiku.append({
                        "text": t.text,
                        "pos": t.pos_,
                        "dep": t.dep_,
                        "head": t.head.text,
                        "func_asignada": func,
                        "context": str(t.sent)[:100],
                    })
                else:
                    num_como_adj[t.text] = {"funcion": func, "head": t.head.text, "via": "spaCy"}

        if nums_for_haiku:
            from harness_h1_haiku import clasificar_haiku
            h1_result, h1_stats = clasificar_haiku(nums_for_haiku, API_KEY,
                                                    texto_contexto=texto[:300])
            h1_cost = h1_stats.get("coste_usd", 0)
            for t_info in nums_for_haiku:
                if t_info["text"] in h1_result:
                    num_como_adj[t_info["text"]] = {
                        "funcion": h1_result[t_info["text"]],
                        "head": t_info["head"],
                        "via": "Haiku H1"
                    }

        resumen["num_como_adj"] = num_como_adj
        print(f"  Números reclasificados: {len(num_como_adj)}")
        for text, info in num_como_adj.items():
            print(f"    \"{text}\" → {info['funcion']} (modifica \"{info['head']}\", vía {info['via']})")
    else:
        print(f"  Números: todos como num_cardinal (sin reclasificación)")

    # Capa 2: LLM enjaulado
    print(f"\n  Capa 2: {model}...")
    user_msg = build_input_msg(texto, resumen, con_adj)

    resp = client.messages.create(
        model=model,
        max_tokens=600,
        temperature=0.0,
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": '{"diagnostico":'},
        ],
    )

    raw = '{"diagnostico":' + resp.content[0].text
    # Cerrar JSON
    depth = 0
    for ch in raw:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
    while depth > 0:
        raw += '}'
        depth -= 1

    try:
        bytecode = json.loads(raw)
    except json.JSONDecodeError:
        bytecode = {"diagnostico": {"error": "JSON parse failed"}, "raw": raw[:500]}

    c2_cost = (
        resp.usage.input_tokens * (15.0 if "opus" in model else 3.0) +
        resp.usage.output_tokens * (75.0 if "opus" in model else 15.0) +
        getattr(resp.usage, 'cache_read_input_tokens', 0) * (1.50 if "opus" in model else 0.30) +
        getattr(resp.usage, 'cache_creation_input_tokens', 0) * (18.75 if "opus" in model else 3.75)
    ) / 1_000_000

    # Capa 3: Traductor (Haiku)
    accion = bytecode.get("prescripcion", {}).get("accion", "registrar_sin_accion")
    instrucciones = bytecode.get("prescripcion", {}).get("instrucciones_traductor", [])
    dims = bytecode.get("diagnostico", {}).get("dims_evaluadas", {})

    trad_resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        temperature=0.2,
        system="Responde de forma directa y profesional. Solo datos y acciones. Máximo 4 oraciones. En español. Sin disclaimers.",
        messages=[{"role": "user", "content": f"""Traduce este bytecode a texto natural para el usuario.
ACCIÓN: {accion}
INSTRUCCIONES: {json.dumps(instrucciones, ensure_ascii=False)}
DIMS CLAVE: {json.dumps({k:v for k,v in dims.items() if isinstance(v,(int,float)) and v >= 3}, ensure_ascii=False)}"""}],
    )

    texto_final = trad_resp.content[0].text.strip()
    c3_cost = (trad_resp.usage.input_tokens * 1.0 + trad_resp.usage.output_tokens * 5.0) / 1_000_000

    dt = time.time() - t0
    total_cost = h1_cost + c2_cost + c3_cost

    # Resultado
    result = {
        "condicion": label,
        "con_adj": con_adj,
        "modelo": model,
        "bytecode": bytecode,
        "texto_final": texto_final,
        "latencia_s": round(dt, 1),
        "coste_total": round(total_cost, 5),
        "coste_detalle": {
            "h1": round(h1_cost, 5),
            "capa2": round(c2_cost, 5),
            "capa3": round(c3_cost, 5),
        },
        "tokens_capa2": {
            "input": resp.usage.input_tokens,
            "output": resp.usage.output_tokens,
            "cache_read": getattr(resp.usage, 'cache_read_input_tokens', 0),
            "cache_creation": getattr(resp.usage, 'cache_creation_input_tokens', 0),
        },
        "num_reclasificados": len(num_como_adj) if con_adj else 0,
    }

    # Print
    print(f"\n  BYTECODE:")
    print(f"    Patrón: {bytecode.get('diagnostico', {}).get('patron_principal', '?')}")
    print(f"    Confianza: {bytecode.get('diagnostico', {}).get('confianza', '?')}")
    print(f"    Acción: {bytecode.get('prescripcion', {}).get('accion', '?')}")
    if dims:
        print(f"    Dims:")
        for d, v in sorted(dims.items()):
            print(f"      {d}: {v}")

    print(f"\n  OUTPUT TRADUCTOR:")
    print(f"  ─────────────")
    print(f"  {texto_final}")
    print(f"  ─────────────")
    print(f"  Latencia: {dt:.1f}s | Coste: ${total_cost:.4f}")

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("Cargando spaCy...")
    nlp = spacy.load("es_dep_news_trf")
    client = anthropic.Anthropic(api_key=API_KEY)

    with open("/tmp/texto_financiero.txt") as f:
        texto = f.read().strip()
    print(f"Texto financiero: {len(texto.split())} palabras")

    results = {}

    # A: CON + Opus
    results["A"] = run_condition(texto, nlp, client, "claude-opus-4-20250514", con_adj=True, label="A")

    # B: CON + Sonnet
    results["B"] = run_condition(texto, nlp, client, "claude-sonnet-4-20250514", con_adj=True, label="B")

    # C: SIN + Opus
    results["C"] = run_condition(texto, nlp, client, "claude-opus-4-20250514", con_adj=False, label="C")

    # D: SIN + Sonnet
    results["D"] = run_condition(texto, nlp, client, "claude-sonnet-4-20250514", con_adj=False, label="D")

    # ============================================================
    # COMPARACIÓN
    # ============================================================
    print(f"\n\n{'#'*60}")
    print(f"COMPARACIÓN 4 CONDICIONES")
    print(f"{'#'*60}")

    print(f"\n{'Cond':<6s} {'Modelo':<10s} {'NUM→adj':<10s} {'Coste':<10s} {'Latencia':<10s} {'Patrón':<25s} {'Acción':<25s}")
    print("-" * 96)
    for k in ["A", "B", "C", "D"]:
        r = results[k]
        modelo = "Opus" if "opus" in r["modelo"] else "Sonnet"
        adj = "CON" if r["con_adj"] else "SIN"
        patron = r["bytecode"].get("diagnostico", {}).get("patron_principal", "?")[:24]
        accion = r["bytecode"].get("prescripcion", {}).get("accion", "?")[:24]
        print(f"{k:<6s} {modelo:<10s} {adj:<10s} ${r['coste_total']:<9.4f} {r['latencia_s']:<9.1f}s {patron:<25s} {accion:<25s}")

    # Dims comparison
    print(f"\n{'Dim':<30s} {'A(CON+Op)':<12s} {'B(CON+Son)':<12s} {'C(SIN+Op)':<12s} {'D(SIN+Son)':<12s} {'Δ CON-SIN':<10s}")
    print("-" * 88)
    all_dims = set()
    for k in ["A", "B", "C", "D"]:
        dims = results[k]["bytecode"].get("diagnostico", {}).get("dims_evaluadas", {})
        all_dims.update(dims.keys())

    for dim in sorted(all_dims):
        vals = []
        for k in ["A", "B", "C", "D"]:
            v = results[k]["bytecode"].get("diagnostico", {}).get("dims_evaluadas", {}).get(dim, "-")
            vals.append(v)

        # Delta CON vs SIN (promedio)
        con_vals = [v for v in vals[:2] if isinstance(v, (int, float))]
        sin_vals = [v for v in vals[2:] if isinstance(v, (int, float))]
        if con_vals and sin_vals:
            delta = np.mean(con_vals) - np.mean(sin_vals)
            delta_str = f"{delta:+.1f}"
        else:
            delta_str = "?"

        print(f"{dim:<30s} {str(vals[0]):<12s} {str(vals[1]):<12s} {str(vals[2]):<12s} {str(vals[3]):<12s} {delta_str:<10s}")

    # Outputs comparison
    print(f"\nOUTPUTS DEL TRADUCTOR:")
    for k in ["A", "B", "C", "D"]:
        r = results[k]
        modelo = "Opus" if "opus" in r["modelo"] else "Sonnet"
        adj = "CON" if r["con_adj"] else "SIN"
        print(f"\n  [{k}] {adj} + {modelo}:")
        print(f"  {r['texto_final']}")

    # Costes totales
    total = sum(r["coste_total"] for r in results.values())
    print(f"\nCOSTE TOTAL 4 CONDICIONES: ${total:.4f}")

    # Guardar
    output_path = os.path.join(os.path.dirname(__file__), "../../data/test_num_adj_4cond.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    save = {
        "version": "poc_num_adj_4cond",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "texto_words": len(texto.split()),
        "condiciones": {k: {
            "con_adj": r["con_adj"],
            "modelo": r["modelo"],
            "bytecode": r["bytecode"],
            "texto_final": r["texto_final"],
            "coste_total": r["coste_total"],
            "latencia_s": r["latencia_s"],
            "num_reclasificados": r.get("num_reclasificados", 0),
        } for k, r in results.items()}
    }
    with open(output_path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {output_path}")
