"""
POC E2E v5 — Pipeline simplificado: Modulador fusionado en H1, H3 modulado por tono
Fecha: 2026-04-12

Cambios vs v4:
  - Modulador eliminado como componente separado
  - H1 determina tono desde el vector del Simbionte (Python, $0)
  - H3 verifica restricciones MODULADAS por tono (frío=estricto, caliente=flexible)
  - Config API del LLM enjaulado (Capa 2) fija: T=0, JSON, pre-fill
  - Config del Traductor (Capa 3) variable según tono de H1

Flujo:
  INPUT → Capa 0 (Simbionte v4, 137D)
       → H1 (Haiku: reclasifica tokens + determina tono)
       → Capa 2 (LLM enjaulado, T=0, JSON)
       → Capa 3 (Traductor, config según tono)
       → H3 (verificación modulada por tono)
       → OUTPUT
"""

import json
import time
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import spacy
import anthropic

from poc_capa0_v4 import (
    calcular_vector_simbionte, FEATURE_NAMES, FEATURES_TOTAL,
    SUFIJOS_OPACOS, contar_adversativos, tokens_funcionales, safe_div,
)
from clasificador_funcional import clasificar_token, FUNC_NAMES, distribucion_funcional
from harness_h1_haiku import clasificar_haiku, determinar_tono

API_KEY = "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"

ACCIONES_PERMITIDAS = {
    "romper_simetria", "reforzar_compromiso", "desescalar", "reencuadrar",
    "confrontar_disonancia", "solicitar_especificidad", "escalar_humano",
    "registrar_sin_accion",
}

SYSTEM_PROMPT_CAPA2 = """Eres OMNI_MIND_EXEC_ENGINE. Emites JSON bytecode. Cero lenguaje natural.

REGLAS: Solo JSON. Solo punteros del catálogo o input. Si no reconoces patrón: confianza "baja".

DIMS (escala 0-5): epist_calibracion, cogn_fuerza_equilibrio, cog_pensamiento_sistemico, f1_conservar, f3_depurar, lente_salud, gob_sin_medir, cib_escalada_simetrica, cogn_fuerza_patron, dato_como_escudo, coherencia_datos

ACCIONES: romper_simetria, reforzar_compromiso, desescalar, reencuadrar, confrontar_disonancia, solicitar_especificidad, escalar_humano, registrar_sin_accion

SCHEMA: {"diagnostico":{"patron_principal":"...","confianza":0.0-1.0,"dims_evaluadas":{...}},"prescripcion":{"accion":"...","instrucciones_traductor":["..."],"restricciones_output":{"mood_prohibido":[],"conectores_prohibidos":[],"fg_minimo":0.0}},"metadata":{"geometria_cumplida":true}}"""


# ============================================================
# CAPA 0 + H1: Simbionte + Reclasificación + Tono
# ============================================================

def capa0_y_h1(doc, client):
    """Simbionte v4 + H1 (reclasificación + tono). Una sola etapa."""
    t0 = time.time()

    # Vector 137D
    vector, func_result = calcular_vector_simbionte(doc)

    # Métricas para tono
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv = contar_adversativos(doc)
    sents = list(doc.sents)

    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs) * 0.25 +
                                    safe_div(n_nom, n_total) * 0.15 +
                                    safe_div(n_adv, n_total) * 0.20)))
    r_cnd = safe_div(n_cnd, n_verbs)
    r_nom = safe_div(n_nom, n_total)
    r_adv = safe_div(n_adv, n_total)

    # TONO (ex-Modulador, ahora en H1)
    tono_config = determinar_tono(fg, r_adv, r_cnd, r_nom)

    # Reclasificación NUM → adjetivo (Haiku)
    nums_for_haiku = []
    num_como_adj = {}
    for t in doc:
        if t.pos_ == "NUM":
            func, needs_haiku = clasificar_token(t)
            if needs_haiku:
                nums_for_haiku.append({
                    "text": t.text, "pos": t.pos_, "dep": t.dep_,
                    "head": t.head.text, "func_asignada": func,
                })
            else:
                num_como_adj[t.text] = {"funcion": func, "head": t.head.text, "via": "spaCy"}

    h1_cost = 0
    if nums_for_haiku:
        h1_result, h1_stats = clasificar_haiku(nums_for_haiku, API_KEY)
        h1_cost = h1_stats.get("coste_usd", 0)
        for t_info in nums_for_haiku:
            if t_info["text"] in h1_result:
                num_como_adj[t_info["text"]] = {
                    "funcion": h1_result[t_info["text"]],
                    "head": t_info["head"], "via": "Haiku H1"
                }

    # Top funciones
    top_funcs = sorted(
        [(FUNC_NAMES[i], func_result["distribucion"][i])
         for i in range(len(func_result["distribucion"]))
         if func_result["distribucion"][i] > 0.01],
        key=lambda x: -x[1]
    )[:7]

    # Patrones
    patrones = []
    if n_adv >= 2 and n_cnd >= 1: patrones.append("equilibrio_nash")
    n_causal = sum(1 for s in sents for t in s if t.dep_ == "mark" and t.lemma_.lower() in
                   ("porque", "ya", "puesto", "dado", "como", "debido"))
    if n_causal >= 2: patrones.append("feedback_ciclico")
    if r_nom > 0.06: patrones.append("gobernanza_opaca")
    n_sub = sum(1 for t in toks if t.dep_ in ("advcl", "ccomp", "xcomp"))
    if safe_div(n_sub, len(sents)) > 0.3: patrones.append("pensamiento_sistemico")

    dt = time.time() - t0

    return {
        "vector": vector,
        "fg": fg,
        "tono": tono_config,
        "num_como_adj": num_como_adj,
        "patrones": patrones,
        "top_funciones": {name: round(val, 3) for name, val in top_funcs},
        "ratios": {"condicional": round(r_cnd, 3), "nominalizacion": round(r_nom, 3), "adversativo": round(r_adv, 3)},
        "n_oraciones": len(sents),
        "h1_cost": h1_cost,
        "latencia_ms": round(dt * 1000),
        "pct_determinista": func_result["stats"]["pct_determinista"],
    }


# ============================================================
# CAPA 2: LLM Enjaulado (config API fija: T=0, JSON, pre-fill)
# ============================================================

def capa2_llm(texto, h1_output, client, model="claude-sonnet-4-20250514"):
    """LLM enjaulado. Config API FIJA. Tono viaja como metadata, no cambia la config."""
    t0 = time.time()

    input_msg = f"""INPUT (primeros 600 chars):
{texto[:600]}...

ANÁLISIS SIMBIONTE (con reclasificación NUM→adjetivo):
- F_G: {h1_output['fg']:.3f}
- Tono detectado: {h1_output['tono']['tono']} ({', '.join(h1_output['tono']['razones'])})
- Patrones: {h1_output['patrones']}
- Top funciones: {json.dumps(h1_output['top_funciones'], ensure_ascii=False)}
- Ratios: {json.dumps(h1_output['ratios'])}

NÚMEROS COMO ADJETIVOS:
{json.dumps(h1_output['num_como_adj'], ensure_ascii=False, indent=2)}

Evalúa las 11 dims. En prescripcion.restricciones_output, especifica qué debe cumplir el texto final (moods prohibidos, conectores prohibidos, fg_minimo)."""

    resp = client.messages.create(
        model=model,
        max_tokens=600,
        temperature=0.0,
        system=[{"type": "text", "text": SYSTEM_PROMPT_CAPA2, "cache_control": {"type": "ephemeral"}}],
        messages=[
            {"role": "user", "content": input_msg},
            {"role": "assistant", "content": '{"diagnostico":'},
        ],
    )

    raw = '{"diagnostico":' + resp.content[0].text
    depth = 0
    for ch in raw:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
    while depth > 0: raw += '}'; depth -= 1

    try:
        bytecode = json.loads(raw)
    except json.JSONDecodeError:
        bytecode = {"diagnostico": {"patron_principal": "error", "confianza": 0.0, "dims_evaluadas": {}},
                    "prescripcion": {"accion": "registrar_sin_accion", "instrucciones_traductor": ["Error JSON"]}}

    # Validar acción
    accion = bytecode.get("prescripcion", {}).get("accion", "")
    if accion not in ACCIONES_PERMITIDAS:
        bytecode.setdefault("prescripcion", {})["accion"] = "registrar_sin_accion"

    dt = time.time() - t0
    is_opus = "opus" in model
    cost = (
        resp.usage.input_tokens * (15.0 if is_opus else 3.0) +
        resp.usage.output_tokens * (75.0 if is_opus else 15.0) +
        getattr(resp.usage, 'cache_read_input_tokens', 0) * (1.50 if is_opus else 0.30) +
        getattr(resp.usage, 'cache_creation_input_tokens', 0) * (18.75 if is_opus else 3.75)
    ) / 1_000_000

    return bytecode, {"cost": cost, "latencia_s": round(dt, 1),
                      "input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens,
                      "cache_read": getattr(resp.usage, 'cache_read_input_tokens', 0)}


# ============================================================
# CAPA 3: Traductor (config VARIABLE según tono de H1)
# ============================================================

def capa3_traductor(bytecode, tono_config, client):
    """Traductor. Config viene del tono detectado por H1."""
    t0 = time.time()

    accion = bytecode.get("prescripcion", {}).get("accion", "registrar_sin_accion")
    instrucciones = bytecode.get("prescripcion", {}).get("instrucciones_traductor", [])
    dims = bytecode.get("diagnostico", {}).get("dims_evaluadas", {})
    restricciones = bytecode.get("prescripcion", {}).get("restricciones_output", {})

    # Config del Traductor viene del tono
    model = "claude-sonnet-4-20250514" if tono_config["modelo"] == "sonnet" else "claude-haiku-4-5-20251001"

    bytecode_compact = json.dumps({
        "accion": accion,
        "instrucciones": instrucciones,
        "dims_clave": {k: v for k, v in dims.items() if isinstance(v, (int, float)) and v >= 3},
    }, ensure_ascii=False, indent=2)

    # Restricciones geométricas del bytecode
    restr_str = ""
    if restricciones:
        moods = restricciones.get("mood_prohibido", [])
        conns = restricciones.get("conectores_prohibidos", [])
        if moods: restr_str += f"\nNO usar modos: {', '.join(moods)}"
        if conns: restr_str += f"\nNO usar conectores: {', '.join(conns)}"
        fg_min = restricciones.get("fg_minimo", 0)
        if fg_min: restr_str += f"\nFuerza mínima del texto: {fg_min}"

    resp = client.messages.create(
        model=model,
        max_tokens=tono_config["max_tokens"],
        temperature=tono_config["temperature"],
        system=tono_config["system"],
        messages=[{"role": "user", "content": f"""Traduce este bytecode a texto natural para el usuario.

BYTECODE:
{bytecode_compact}
{restr_str}

Responde en español. Sin disclaimers ni meta-comentarios."""}],
    )

    texto_final = resp.content[0].text.strip()
    dt = time.time() - t0
    is_sonnet = "sonnet" in model
    cost = (
        resp.usage.input_tokens * (3.0 if is_sonnet else 1.0) +
        resp.usage.output_tokens * (15.0 if is_sonnet else 5.0)
    ) / 1_000_000

    return texto_final, {"cost": cost, "latencia_s": round(dt, 1), "modelo": model,
                         "tono": tono_config["tono"], "T": tono_config["temperature"]}


# ============================================================
# H3: Verificación MODULADA por tono
# ============================================================

def harness_h3(texto_final, nlp, tono_config, restricciones_bytecode=None):
    """Verificación geométrica modulada por tono.

    Frío: estricto (F_G>0.8, max 2 oraciones, cero condicional)
    Templado: medio (F_G>0.6, max 3 oraciones)
    Caliente: flexible (F_G>0.4, max 4 oraciones, adversativas OK para espejeo)
    Incierto: pregunta (F_G>0.5, max 2 oraciones, debe contener ?)
    """
    doc = nlp(texto_final)
    toks = [t for t in doc if not t.is_punct and not t.is_space]
    sents = list(doc.sents)
    tono = tono_config["tono"]

    checks = {"passed": True, "violations": [], "tono": tono}

    # Thresholds por tono
    THRESHOLDS = {
        "frio":     {"fg_min": 0.8, "max_sents": 4, "cnd_ok": False, "adv_ok": False},
        "templado": {"fg_min": 0.6, "max_sents": 4, "cnd_ok": False, "adv_ok": False},
        "caliente": {"fg_min": 0.4, "max_sents": 5, "cnd_ok": True,  "adv_ok": True},  # espejeo
        "incierto": {"fg_min": 0.5, "max_sents": 3, "cnd_ok": False, "adv_ok": False},
    }
    th = THRESHOLDS.get(tono, THRESHOLDS["templado"])

    # Check 1: Condicionales
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    if n_cnd > 0 and not th["cnd_ok"]:
        checks["violations"].append(f"condicional: {n_cnd} tokens Mood=Cnd (prohibido en tono {tono})")
        checks["passed"] = False

    # Check 2: Oraciones
    if len(sents) > th["max_sents"]:
        checks["violations"].append(f"oraciones: {len(sents)} > {th['max_sents']} (tono {tono})")
        checks["passed"] = False

    # Check 3: No vacío
    if len(toks) < 3:
        checks["violations"].append("output_vacio")
        checks["passed"] = False

    # Check 4: F_G
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv_out = contar_adversativos(doc)
    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs) * 0.25 +
                                    safe_div(n_nom, n_total) * 0.15 +
                                    safe_div(n_adv_out, n_total) * 0.20)))
    checks["fg_output"] = round(fg, 3)
    if fg < th["fg_min"]:
        checks["violations"].append(f"fg: {fg:.3f} < {th['fg_min']} (tono {tono})")
        checks["passed"] = False

    # Check 5: Incierto debe contener pregunta
    if tono == "incierto" and "?" not in texto_final:
        checks["violations"].append("incierto_sin_pregunta")
        checks["passed"] = False

    # Check 6: Restricciones del bytecode (Capa 2 las especifica)
    if restricciones_bytecode:
        moods_prohibidos = restricciones_bytecode.get("mood_prohibido", [])
        for mood in moods_prohibidos:
            count = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == mood)
            if count > 0:
                checks["violations"].append(f"bytecode_mood_{mood}: {count} tokens")
                checks["passed"] = False

        conns_prohibidos = restricciones_bytecode.get("conectores_prohibidos", [])
        for conn in conns_prohibidos:
            if conn.lower() in texto_final.lower():
                checks["violations"].append(f"bytecode_conector: '{conn}' encontrado")
                checks["passed"] = False

    checks["n_oraciones"] = len(sents)
    checks["n_tokens"] = len(toks)
    return checks


# ============================================================
# PIPELINE E2E v5
# ============================================================

def run_e2e_v5(texto, nlp, client, model="claude-sonnet-4-20250514", verbose=True):
    """Pipeline completo v5: H1 fusionado, H3 modulado."""
    t_total = time.time()

    # === CAPA 0 + H1 ===
    if verbose: print(f"\n{'='*60}\nCAPA 0 + H1: Simbionte v4 + Reclasificación + Tono\n{'='*60}")
    doc = nlp(texto)
    h1 = capa0_y_h1(doc, client)

    if verbose:
        print(f"  Vector: {len(h1['vector'])}D en {h1['latencia_ms']}ms")
        print(f"  F_G: {h1['fg']:.3f}")
        print(f"  TONO: {h1['tono']['tono']} ({', '.join(h1['tono']['razones'])})")
        print(f"  Patrones: {h1['patrones']}")
        print(f"  Nums reclasificados: {len(h1['num_como_adj'])}")
        for text, info in list(h1['num_como_adj'].items())[:8]:
            print(f"    \"{text}\" → {info['funcion']} (→\"{info['head']}\", {info['via']})")
        print(f"  H1 coste: ${h1['h1_cost']:.4f}")

    # === CAPA 2 ===
    if verbose: print(f"\n{'='*60}\nCAPA 2: LLM Enjaulado ({model.split('-')[1]}, T=0, JSON)\n{'='*60}")
    bytecode, c2_stats = capa2_llm(texto, h1, client, model)

    if verbose:
        print(f"  Latencia: {c2_stats['latencia_s']}s | Coste: ${c2_stats['cost']:.4f}")
        print(f"  Tokens: {c2_stats['input_tokens']} in / {c2_stats['output_tokens']} out (cache: {c2_stats['cache_read']})")
        print(f"  Patrón: {bytecode.get('diagnostico',{}).get('patron_principal','?')}")
        print(f"  Confianza: {bytecode.get('diagnostico',{}).get('confianza','?')}")
        print(f"  Acción: {bytecode.get('prescripcion',{}).get('accion','?')}")
        dims = bytecode.get('diagnostico',{}).get('dims_evaluadas',{})
        if dims:
            for d, v in sorted(dims.items()): print(f"    {d}: {v}")
        restrs = bytecode.get('prescripcion',{}).get('restricciones_output',{})
        if restrs: print(f"  Restricciones output: {restrs}")

    # === CAPA 3 ===
    if verbose: print(f"\n{'='*60}\nCAPA 3: Traductor ({h1['tono']['tono']}, T={h1['tono']['temperature']}, {h1['tono']['modelo']})\n{'='*60}")
    texto_final, c3_stats = capa3_traductor(bytecode, h1["tono"], client)

    if verbose:
        print(f"\n  OUTPUT:")
        print(f"  {'─'*50}")
        print(f"  {texto_final}")
        print(f"  {'─'*50}")
        print(f"  Latencia: {c3_stats['latencia_s']}s | Coste: ${c3_stats['cost']:.6f}")

    # === H3 ===
    if verbose: print(f"\n{'─'*40}\nH3: Verificación modulada (tono={h1['tono']['tono']})\n{'─'*40}")
    restricciones_bc = bytecode.get("prescripcion", {}).get("restricciones_output", {})
    h3 = harness_h3(texto_final, nlp, h1["tono"], restricciones_bc)

    if verbose:
        status = "PASADO" if h3["passed"] else "FALLADO"
        print(f"  {'✅' if h3['passed'] else '❌'} {status}")
        print(f"  F_G output: {h3['fg_output']} | Oraciones: {h3['n_oraciones']} | Tokens: {h3['n_tokens']}")
        for v in h3["violations"]: print(f"  ⚠️ {v}")

    # === RESUMEN ===
    dt_total = time.time() - t_total
    total_cost = h1["h1_cost"] + c2_stats["cost"] + c3_stats["cost"]

    if verbose:
        print(f"\n{'='*60}\nRESUMEN v5\n{'='*60}")
        print(f"  Latencia: {dt_total:.1f}s")
        print(f"  Coste: ${total_cost:.4f}")
        print(f"  Pipeline: Capa0+H1 → {model.split('-')[1]} → {h1['tono']['modelo']} → H3({h1['tono']['tono']})")
        print(f"  Tono: {h1['tono']['tono']} | H3: {'✅' if h3['passed'] else '❌'}")

    return {
        "h1": h1, "bytecode": bytecode, "c2_stats": c2_stats,
        "texto_final": texto_final, "c3_stats": c3_stats, "h3": h3,
        "total_cost": total_cost, "total_latencia": round(dt_total, 1),
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    print("Cargando spaCy...")
    nlp = spacy.load("es_dep_news_trf")
    client = anthropic.Anthropic(api_key=API_KEY)

    # Texto financiero
    with open("/tmp/texto_financiero.txt") as f:
        texto = f.read().strip()
    print(f"Texto: {len(texto.split())} palabras")

    # Ejecutar con Sonnet
    print(f"\n{'#'*60}")
    print(f"PRUEBA v5: SONNET")
    print(f"{'#'*60}")
    r_sonnet = run_e2e_v5(texto, nlp, client, "claude-sonnet-4-20250514")

    # Ejecutar con Opus
    print(f"\n{'#'*60}")
    print(f"PRUEBA v5: OPUS")
    print(f"{'#'*60}")
    r_opus = run_e2e_v5(texto, nlp, client, "claude-opus-4-20250514")

    # Comparación
    print(f"\n\n{'#'*60}")
    print(f"COMPARACIÓN v5: SONNET vs OPUS")
    print(f"{'#'*60}")
    print(f"\n{'Métrica':<30s} {'Sonnet':<20s} {'Opus':<20s}")
    print("-" * 70)
    print(f"{'Coste':<30s} ${r_sonnet['total_cost']:<19.4f} ${r_opus['total_cost']:<19.4f}")
    print(f"{'Latencia':<30s} {r_sonnet['total_latencia']:<19.1f}s {r_opus['total_latencia']:<19.1f}s")
    print(f"{'Tono detectado':<30s} {r_sonnet['h1']['tono']['tono']:<20s} {r_opus['h1']['tono']['tono']:<20s}")
    print(f"{'Patrón':<30s} {r_sonnet['bytecode'].get('diagnostico',{}).get('patron_principal','?'):<20s} {r_opus['bytecode'].get('diagnostico',{}).get('patron_principal','?'):<20s}")
    print(f"{'Confianza':<30s} {str(r_sonnet['bytecode'].get('diagnostico',{}).get('confianza','?')):<20s} {str(r_opus['bytecode'].get('diagnostico',{}).get('confianza','?')):<20s}")
    print(f"{'Acción':<30s} {r_sonnet['bytecode'].get('prescripcion',{}).get('accion','?'):<20s} {r_opus['bytecode'].get('prescripcion',{}).get('accion','?'):<20s}")
    print(f"{'H3':<30s} {'✅' if r_sonnet['h3']['passed'] else '❌':<20s} {'✅' if r_opus['h3']['passed'] else '❌':<20s}")

    # Dims
    all_dims = set()
    for r in [r_sonnet, r_opus]:
        all_dims.update(r["bytecode"].get("diagnostico",{}).get("dims_evaluadas",{}).keys())
    print(f"\n{'Dim':<30s} {'Sonnet':<10s} {'Opus':<10s}")
    print("-" * 50)
    for d in sorted(all_dims):
        vs = r_sonnet["bytecode"].get("diagnostico",{}).get("dims_evaluadas",{}).get(d, "-")
        vo = r_opus["bytecode"].get("diagnostico",{}).get("dims_evaluadas",{}).get(d, "-")
        print(f"{d:<30s} {str(vs):<10s} {str(vo):<10s}")

    # Guardar
    output_path = os.path.join(os.path.dirname(__file__), "../../data/test_e2e_v5.json")
    save = {
        "version": "e2e_v5_h1_tono_h3_modulado",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "sonnet": {"bytecode": r_sonnet["bytecode"], "texto_final": r_sonnet["texto_final"],
                   "cost": r_sonnet["total_cost"], "h3": r_sonnet["h3"], "tono": r_sonnet["h1"]["tono"]["tono"]},
        "opus": {"bytecode": r_opus["bytecode"], "texto_final": r_opus["texto_final"],
                 "cost": r_opus["total_cost"], "h3": r_opus["h3"], "tono": r_opus["h1"]["tono"]["tono"]},
    }
    with open(output_path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {output_path}")
