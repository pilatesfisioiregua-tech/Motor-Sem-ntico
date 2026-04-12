"""
POC E2E v6 — Pipeline completo con decodificador inverso + prompt caching
Fecha: 2026-04-12

Flujo:
  Capa 0 (v6, 266D) → Geometria (95D) → H1 (tono + NUM→adj)
  → Decodificador inverso (vector → texto)
  → [pgvector busqueda: PENDIENTE]
  → Capa 2 (Sonnet, T=0, prompt caching con decodificacion)
  → Capa 3 (Traductor, config por tono)
  → H3 (verificacion modulada)
"""

import json
import time
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import spacy
import anthropic

from poc_capa0_v6 import calcular_vector_v6, FEATURES_TOTAL, tokens_funcionales, safe_div, SUFIJOS_OPACOS, ADVERSATIVOS_SINGLE, ADVERSATIVOS_MULTI
from marcos_matematicos import FEATURES_POR_NIVEL
from geometria_isomorfismo import calcular_geometria_completa
from clasificador_funcional import clasificar_token, FUNC_NAMES, N_FUNCIONES
from harness_h1_haiku import clasificar_haiku, determinar_tono
from decodificador_inverso import construir_prompt_decodificado

API_KEY = "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"

ACCIONES_PERMITIDAS = {
    "romper_simetria", "reforzar_compromiso", "desescalar", "reencuadrar",
    "confrontar_disonancia", "solicitar_especificidad", "escalar_humano",
    "registrar_sin_accion",
}

SYSTEM_RULES = """Eres OMNI_MIND_EXEC_ENGINE. Emites JSON bytecode. Cero lenguaje natural.

REGLAS: Solo JSON. Evalua las dims cognitivas basandote en el ANALISIS ESTRUCTURAL que recibes.
El analisis fue producido por el Simbionte (determinista, verificable). Tu trabajo es INTERPRETAR
la evidencia estructural y producir diagnostico + prescripcion.

DIMS (escala 0-5): epist_calibracion, cogn_fuerza_equilibrio, cog_pensamiento_sistemico,
f1_conservar, f3_depurar, lente_salud, gob_sin_medir, cib_escalada_simetrica,
cogn_fuerza_patron, dato_como_escudo, coherencia_datos

ACCIONES: romper_simetria, reforzar_compromiso, desescalar, reencuadrar,
confrontar_disonancia, solicitar_especificidad, escalar_humano, registrar_sin_accion

Si detectas un patron estructural recurrente que NO esta en el catalogo,
proponlo en "candidato_isomorfismo" con: nombre, definicion, ejes_dominantes.

SCHEMA:
{"diagnostico":{"patron_principal":"...","confianza":0.0-1.0,"dims_evaluadas":{...}},
"prescripcion":{"accion":"...","instrucciones_traductor":["..."],
"restricciones_output":{"mood_prohibido":[],"conectores_prohibidos":[],"fg_minimo":0.0}},
"candidato_isomorfismo":null,
"metadata":{"geometria_cumplida":true}}"""


def run_e2e_v6(texto, nlp, client, model="claude-sonnet-4-20250514", verbose=True):
    """Pipeline E2E v6 completo."""
    t_total = time.time()
    FPN = FEATURES_POR_NIVEL

    # === CAPA 0: Simbionte v6 (266D) ===
    if verbose: print(f"\n{'='*60}\nCAPA 0: Simbionte v6 (266D, 10 marcos × 4 niveles)\n{'='*60}")
    doc = nlp(texto)
    vector_v6, meta = calcular_vector_v6(doc)

    if verbose:
        print(f"  Vector: {len(vector_v6)}D en {meta['latencia_ms']}ms")
        print(f"  Tokens: {meta['n_tokens']}, Oraciones: {meta['n_oraciones']}, Parrafos: {meta['n_parrafos']}")

    # === GEOMETRIA (95D) ===
    if verbose: print(f"\n{'─'*40}\nGEOMETRIA (forma fractal)")
    t0 = time.time()
    vectores_nivel = {
        "N1": vector_v6[0:FPN],
        "N2": vector_v6[FPN:2*FPN],
        "N3": vector_v6[2*FPN:3*FPN],
        "N4": vector_v6[3*FPN:4*FPN],
    }
    geo = calcular_geometria_completa(vectores_nivel)
    dt_geo = time.time() - t0

    if verbose:
        print(f"  Geometria: {geo['n_features']}D en {dt_geo*1000:.0f}ms")
        print(f"  Profundidad patron: {geo['profundidad_patron']}")
        for nivel in ["N1", "N2", "N3", "N4"]:
            dom = geo["geometrias"][nivel]["forma"]["dominantes"]
            if dom: print(f"  {nivel} dominantes: {dom}")

    # === H1: Reclasificacion + Tono ===
    if verbose: print(f"\n{'─'*40}\nH1: Reclasificacion + Tono")
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv = sum(1 for t in doc if t.text.lower() in ADVERSATIVOS_SINGLE)
    n_adv += sum(doc.text.lower().count(a) for a in ADVERSATIVOS_MULTI)
    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs)*0.25 + safe_div(n_nom, n_total)*0.15 + safe_div(n_adv, n_total)*0.20)))

    tono_config = determinar_tono(fg, safe_div(n_adv, n_total), safe_div(n_cnd, n_verbs), safe_div(n_nom, n_total))

    # NUM → adjetivo
    num_como_adj = {}
    nums_haiku = []
    for t in doc:
        if t.pos_ == "NUM":
            func, needs = clasificar_token(t)
            if needs:
                nums_haiku.append({"text": t.text, "pos": t.pos_, "dep": t.dep_, "head": t.head.text, "func_asignada": func})
            else:
                num_como_adj[t.text] = {"funcion": func, "head": t.head.text, "via": "spaCy"}

    h1_cost = 0
    if nums_haiku:
        h1_res, h1_stats = clasificar_haiku(nums_haiku, API_KEY)
        h1_cost = h1_stats.get("coste_usd", 0)
        for ti in nums_haiku:
            if ti["text"] in h1_res:
                num_como_adj[ti["text"]] = {"funcion": h1_res[ti["text"]], "head": ti["head"], "via": "Haiku"}

    if verbose:
        print(f"  Tono: {tono_config['tono']} ({', '.join(tono_config['razones'])})")
        print(f"  F_G: {fg:.3f}")
        print(f"  Nums reclasificados: {len(num_como_adj)}")

    # === DECODIFICADOR INVERSO ===
    if verbose: print(f"\n{'='*60}\nDECODIFICADOR INVERSO (vector → texto para LLM)\n{'='*60}")
    prompt_decodificado = construir_prompt_decodificado(
        vectores_nivel, geo,
        num_como_adj=num_como_adj,
        match_pgvector=None,  # TODO: busqueda pgvector
        tono=tono_config["tono"],
    )

    n_tokens_prompt = len(prompt_decodificado.split()) * 1.3
    if verbose:
        # Mostrar preview
        lines = prompt_decodificado.split("\n")
        print(f"  Prompt decodificado: ~{n_tokens_prompt:.0f} tokens, {len(lines)} lineas")
        print(f"  Preview (primeras 20 lineas):")
        for line in lines[:20]:
            print(f"    {line}")
        if len(lines) > 20:
            print(f"    ... ({len(lines)-20} lineas mas)")

    # === CAPA 2: LLM Enjaulado con prompt caching ===
    if verbose: print(f"\n{'='*60}\nCAPA 2: LLM Enjaulado ({model.split('-')[1]}, prompt caching)\n{'='*60}")
    t0 = time.time()

    resp = client.messages.create(
        model=model,
        max_tokens=600,
        temperature=0.0,
        system=[
            {"type": "text", "text": SYSTEM_RULES, "cache_control": {"type": "ephemeral"}},
        ],
        messages=[
            {"role": "user", "content": f"""{prompt_decodificado}

---
INPUT ORIGINAL (primeros 400 chars):
{texto[:400]}...

Evalua las 11 dims basandote en el ANALISIS ESTRUCTURAL. Si detectas isomorfismo nuevo, proponlo."""},
            {"role": "assistant", "content": '{"diagnostico":'},
        ],
    )

    dt_c2 = time.time() - t0
    raw = '{"diagnostico":' + resp.content[0].text
    depth = 0
    for ch in raw:
        if ch == '{': depth += 1
        elif ch == '}': depth -= 1
    while depth > 0: raw += '}'; depth -= 1

    try:
        bytecode = json.loads(raw)
    except json.JSONDecodeError:
        bytecode = {"diagnostico": {"patron_principal": "error_json", "confianza": 0, "dims_evaluadas": {}},
                    "prescripcion": {"accion": "registrar_sin_accion", "instrucciones_traductor": ["Error"]}}

    accion = bytecode.get("prescripcion", {}).get("accion", "")
    if accion not in ACCIONES_PERMITIDAS:
        bytecode.setdefault("prescripcion", {})["accion"] = "registrar_sin_accion"

    is_opus = "opus" in model
    c2_cost = (
        resp.usage.input_tokens * (15.0 if is_opus else 3.0) +
        resp.usage.output_tokens * (75.0 if is_opus else 15.0) +
        getattr(resp.usage, 'cache_read_input_tokens', 0) * (1.50 if is_opus else 0.30) +
        getattr(resp.usage, 'cache_creation_input_tokens', 0) * (18.75 if is_opus else 3.75)
    ) / 1_000_000

    if verbose:
        print(f"  Latencia: {dt_c2:.1f}s")
        print(f"  Tokens: {resp.usage.input_tokens} in / {resp.usage.output_tokens} out")
        print(f"  Cache: read={getattr(resp.usage, 'cache_read_input_tokens', 0)}, creation={getattr(resp.usage, 'cache_creation_input_tokens', 0)}")
        print(f"  Coste: ${c2_cost:.4f}")
        print(f"  Patron: {bytecode.get('diagnostico',{}).get('patron_principal','?')}")
        print(f"  Confianza: {bytecode.get('diagnostico',{}).get('confianza','?')}")
        print(f"  Accion: {bytecode.get('prescripcion',{}).get('accion','?')}")
        dims = bytecode.get('diagnostico',{}).get('dims_evaluadas',{})
        if dims:
            for d, v in sorted(dims.items()): print(f"    {d}: {v}")
        candidato = bytecode.get("candidato_isomorfismo")
        if candidato:
            print(f"  ISOMORFISMO NUEVO PROPUESTO:")
            print(f"    {json.dumps(candidato, ensure_ascii=False, indent=4)}")

    # === CAPA 3: Traductor ===
    if verbose: print(f"\n{'='*60}\nCAPA 3: Traductor ({tono_config['tono']}, T={tono_config['temperature']})\n{'='*60}")
    t0 = time.time()

    instrs = bytecode.get("prescripcion", {}).get("instrucciones_traductor", [])
    dims_clave = {k: v for k, v in dims.items() if isinstance(v, (int, float)) and v >= 3}
    trad_model = "claude-sonnet-4-20250514" if tono_config["modelo"] == "sonnet" else "claude-haiku-4-5-20251001"

    trad_resp = client.messages.create(
        model=trad_model,
        max_tokens=tono_config["max_tokens"],
        temperature=tono_config["temperature"],
        system=tono_config["system"],
        messages=[{"role": "user", "content": f"""Traduce a texto natural para el usuario.
ACCION: {bytecode.get('prescripcion',{}).get('accion','')}
INSTRUCCIONES: {json.dumps(instrs, ensure_ascii=False)}
DIMS CLAVE: {json.dumps(dims_clave, ensure_ascii=False)}
Responde en espanol. Sin disclaimers."""}],
    )

    texto_final = trad_resp.content[0].text.strip()
    dt_c3 = time.time() - t0
    is_sonnet_trad = "sonnet" in trad_model
    c3_cost = (trad_resp.usage.input_tokens * (3.0 if is_sonnet_trad else 1.0) +
               trad_resp.usage.output_tokens * (15.0 if is_sonnet_trad else 5.0)) / 1_000_000

    if verbose:
        print(f"\n  OUTPUT:")
        print(f"  {'─'*50}")
        print(f"  {texto_final}")
        print(f"  {'─'*50}")
        print(f"  Latencia: {dt_c3:.1f}s | Coste: ${c3_cost:.6f}")

    # === H3: Verificacion modulada ===
    if verbose: print(f"\n{'─'*40}\nH3: Verificacion (tono={tono_config['tono']})")
    from poc_e2e_v5 import harness_h3
    restrs_bc = bytecode.get("prescripcion", {}).get("restricciones_output", {})
    h3 = harness_h3(texto_final, nlp, tono_config, restrs_bc)

    if verbose:
        print(f"  {'✅' if h3['passed'] else '❌'} {'PASADO' if h3['passed'] else 'FALLADO'}")
        print(f"  F_G: {h3['fg_output']} | Oraciones: {h3['n_oraciones']}")
        for v in h3["violations"]: print(f"  ⚠️ {v}")

    # === RESUMEN ===
    dt_total = time.time() - t_total
    total_cost = h1_cost + c2_cost + c3_cost

    if verbose:
        print(f"\n{'='*60}")
        print(f"RESUMEN E2E v6")
        print(f"{'='*60}")
        print(f"  Vector: {FEATURES_TOTAL}D + {geo['n_features']}D geometria = {FEATURES_TOTAL + geo['n_features']}D")
        print(f"  Latencia total: {dt_total:.1f}s")
        print(f"  Coste total: ${total_cost:.4f}")
        print(f"  Pipeline: v6(361D) → decodificador → {model.split('-')[1]} → {tono_config['modelo']} → H3({tono_config['tono']})")
        print(f"  Profundidad patron: {geo['profundidad_patron']}")
        print(f"  Candidato isomorfismo: {'SI' if bytecode.get('candidato_isomorfismo') else 'NO'}")
        print(f"  H3: {'✅' if h3['passed'] else '❌'}")

    return {
        "vector_dims": FEATURES_TOTAL + geo["n_features"],
        "bytecode": bytecode,
        "texto_final": texto_final,
        "total_cost": total_cost,
        "total_latencia": round(dt_total, 1),
        "profundidad": geo["profundidad_patron"],
        "tono": tono_config["tono"],
        "h3": h3,
        "candidato": bytecode.get("candidato_isomorfismo"),
        "prompt_tokens": n_tokens_prompt,
        "c2_tokens": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens,
                      "cache_read": getattr(resp.usage, 'cache_read_input_tokens', 0),
                      "cache_creation": getattr(resp.usage, 'cache_creation_input_tokens', 0)},
    }


if __name__ == "__main__":
    print("Cargando spaCy...")
    nlp = spacy.load("es_dep_news_trf")
    client = anthropic.Anthropic(api_key=API_KEY)

    with open("/tmp/texto_financiero.txt") as f:
        texto = f.read().strip()
    print(f"Texto: {len(texto.split())} palabras\n")

    # Sonnet
    r = run_e2e_v6(texto, nlp, client, "claude-sonnet-4-20250514")

    # Guardar
    save = {
        "version": "e2e_v6_decodificador",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "vector_dims": r["vector_dims"],
        "bytecode": r["bytecode"],
        "texto_final": r["texto_final"],
        "total_cost": r["total_cost"],
        "profundidad": r["profundidad"],
        "candidato": r["candidato"],
        "h3": r["h3"],
    }
    path = os.path.join(os.path.dirname(__file__), "../../data/test_e2e_v6.json")
    with open(path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {path}")
