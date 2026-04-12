"""
POC E2E v4 — Pipeline completo: Simbionte v4 → Sonnet (LLM enjaulado) → Traductor
Fecha: 2026-04-12

Flujo:
  1. Capa 0: Simbionte v4 extrae vector 131D + funciones reales (spaCy, determinista)
  2. Harness H1: Haiku clasifica tokens ambiguos (~6%)
  3. Capa 2: Sonnet enjaulado (T=0, JSON, pre-fill) → bytecode diagnóstico + prescripción
  4. Agente Modulador: Python determinista → config Traductor (tono, T, max_tokens)
  5. Capa 3: Haiku/Sonnet traduce bytecode → texto natural para usuario
  6. Harness H3: spaCy verifica restricciones geométricas del output

Ref: CAPA_0_ESPECIFICACION.md, CAPA_2_ESPECIFICACION.md, CAPA_3_ESPECIFICACION.md
"""

import json
import time
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from poc_capa0_v4 import (
    calcular_vector_simbionte, FEATURE_NAMES, FEATURES_TOTAL,
    FEATURES_NIVEL_1, FEATURES_NIVEL_2, FEATURES_NIVEL_3, FEATURES_NIVEL_4,
    SUFIJOS_OPACOS, contar_adversativos, tokens_funcionales, safe_div,
)
from clasificador_funcional import FUNC_NAMES, distribucion_funcional
from harness_h1_haiku import clasificar_haiku

# ============================================================
# CONFIG
# ============================================================

API_KEY = "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"

# Vocabulario cerrado de acciones (CAPA_2_ESPECIFICACION.md §4)
ACCIONES_PERMITIDAS = {
    "romper_simetria",
    "reforzar_compromiso",
    "desescalar",
    "reencuadrar",
    "confrontar_disonancia",
    "solicitar_especificidad",
    "escalar_humano",
    "registrar_sin_accion",
}

# Templates estáticos — última línea de defensa (CAPA_3_ESPECIFICACION.md §6)
TEMPLATES_ESTATICOS = {
    "romper_simetria": "Elige una opción concreta y actúa hoy. ¿Cuál de las dos eliges?",
    "desescalar": "Entiendo la situación. Vamos paso a paso. ¿Qué es lo primero que necesitas resolver?",
    "solicitar_especificidad": "Necesito que seas más específico. ¿A qué te refieres exactamente?",
    "reforzar_compromiso": "Buen enfoque. Sigue con eso. ¿Cuándo lo ejecutas?",
    "escalar_humano": "Esta situación requiere atención personalizada. Te conecto con un especialista.",
    "confrontar_disonancia": "Noto una contradicción en tu planteamiento. ¿Cuál es tu posición real?",
    "reencuadrar": "Otra forma de ver esto: el problema no está donde crees.",
    "registrar_sin_accion": "Registrado. ¿Hay algo más que necesites?",
}

# ============================================================
# CAPA 0: SIMBIONTE v4
# ============================================================

def capa0_simbionte(doc):
    """Extrae vector 131D + funciones reales + resumen para Capa 2."""
    t0 = time.time()
    vector, func_result = calcular_vector_simbionte(doc)
    dt = time.time() - t0

    # Extraer resumen compacto para el LLM
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv = contar_adversativos(doc)

    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs) * 0.25 +
                                    safe_div(n_nom, n_total) * 0.15 +
                                    safe_div(n_adv, n_total) * 0.20)))

    # Top funciones (las 5 más frecuentes)
    top_funcs = sorted(
        [(FUNC_NAMES[i], func_result["distribucion"][i])
         for i in range(len(func_result["distribucion"]))
         if func_result["distribucion"][i] > 0.01],
        key=lambda x: -x[1]
    )[:5]

    # Detectar patrones clave para el LLM
    patrones = []
    # Nash: adversativas + condicionales
    if n_adv >= 3 and n_cnd >= 2:
        patrones.append("equilibrio_nash_posible")
    # Feedback cibernético: causal + adversativa en secuencia
    sents = list(doc.sents)
    n_causal = sum(1 for s in sents for t in s if t.dep_ == "mark" and t.lemma_.lower() in
                   ("porque", "ya", "puesto", "dado", "como", "debido"))
    if n_causal >= 2 and n_adv >= 2:
        patrones.append("feedback_ciclico")
    # Gobernanza sin métricas: muchas nominalizaciones + pocos números
    n_nums = sum(1 for t in toks if t.pos_ == "NUM")
    if safe_div(n_nom, n_total) > 0.08 and n_nums < 5:
        patrones.append("gobernanza_opaca")
    # Pensamiento sistémico: alta subordinación
    n_sub = sum(1 for t in toks if t.dep_ in ("advcl", "ccomp", "xcomp"))
    if safe_div(n_sub, len(sents)) > 0.5:
        patrones.append("pensamiento_sistemico")

    resumen = {
        "fg_global": round(fg, 3),
        "n_tokens": n_total,
        "n_oraciones": len(sents),
        "top_funciones": {name: round(val, 3) for name, val in top_funcs},
        "ratio_condicional": round(safe_div(n_cnd, n_verbs), 3),
        "ratio_nominalizacion": round(safe_div(n_nom, n_total), 3),
        "ratio_adversativo": round(safe_div(n_adv, n_total), 3),
        "patrones_detectados": patrones,
        "pct_determinista": func_result["stats"]["pct_determinista"],
        "tokens_haiku": func_result["stats"]["haiku"],
    }

    return vector, func_result, resumen, dt


# ============================================================
# HARNESS H1: Clasificar tokens ambiguos con Haiku
# ============================================================

def harness_h1(func_result, api_key):
    """Clasifica los ~6% de tokens no resueltos por spaCy."""
    tokens_h = func_result.get("tokens_haiku", [])
    if not tokens_h:
        return {}, {"n_clasificados": 0, "coste_usd": 0, "skipped": True}
    return clasificar_haiku(tokens_h, api_key)


# ============================================================
# CAPA 2: LLM ENJAULADO (Sonnet, T=0, JSON, pre-fill)
# ============================================================

SYSTEM_PROMPT_CAPA2 = """Eres OMNI_MIND_EXEC_ENGINE. Emites JSON bytecode. Cero lenguaje natural.

REGLAS ABSOLUTAS:
1. Tu output es EXCLUSIVAMENTE JSON válido.
2. Evalúas las dims cognitivas que el Simbionte detectó como patrones.
3. Si no reconoces un patrón, responde con confianza "baja".
4. NUNCA generas texto explicativo, saludos ni disculpas.
5. Tu respuesta debe cumplir el schema especificado.

VOCABULARIO DE ACCIONES (solo estas):
- romper_simetria: Nash o equilibrio destructivo → forzar decisión unilateral
- reforzar_compromiso: input positivo → amplificar
- desescalar: input caliente → bajar tensión
- reencuadrar: cambiar marco de referencia del usuario
- confrontar_disonancia: contradicción detectada → señalar
- solicitar_especificidad: nominalización opaca → pedir detalle
- escalar_humano: el sistema no puede resolver
- registrar_sin_accion: input informativo → solo log

DIMS COGNITIVAS A EVALUAR (escala 0-5):
- epist_calibracion: ¿el texto distingue entre lo que sabe y lo que supone?
- cogn_fuerza_equilibrio: ¿hay fuerzas opuestas en equilibrio destructivo?
- cog_pensamiento_sistemico: ¿ve conexiones entre partes o solo partes aisladas?
- f1_conservar: ¿protege lo que funciona o destruye sin discriminar?
- f3_depurar: ¿identifica y elimina ineficiencias?
- lente_salud: ¿el sistema descrito funciona o está disfuncional?
- gob_sin_medir: ¿hay gobernanza sin métricas adecuadas? (0=mide bien, 5=gobernanza ciega)
- cib_escalada_simetrica: ¿hay feedback positivo que amplifica el conflicto?
- cogn_fuerza_patron: ¿los patrones son predecibles y repetitivos?

SCHEMA OUTPUT:
{
  "diagnostico": {
    "patron_principal": "nombre del patrón dominante",
    "confianza": float 0-1,
    "dims_evaluadas": {dim: valor 0-5, ...}
  },
  "prescripcion": {
    "accion": "del vocabulario cerrado",
    "instrucciones_traductor": ["instrucción 1", "instrucción 2", "instrucción 3"]
  },
  "metadata": {
    "modo_recibido": "match_directo|vecinos|sin_ancla",
    "geometria_cumplida": true|false
  }
}"""

def capa2_llm_enjaulado(texto_original, resumen_simbionte, client):
    """LLM enjaulado: T=0, JSON, pre-fill. Produce bytecode."""
    t0 = time.time()

    # Construir input compacto (Capa 3 del prompt según spec)
    input_simbionte = {
        "modo": "match_directo" if resumen_simbionte["patrones_detectados"] else "sin_ancla",
        "resumen_vector": {
            "fg_global": resumen_simbionte["fg_global"],
            "top_funciones": resumen_simbionte["top_funciones"],
            "ratios": {
                "condicional": resumen_simbionte["ratio_condicional"],
                "nominalizacion": resumen_simbionte["ratio_nominalizacion"],
                "adversativo": resumen_simbionte["ratio_adversativo"],
            },
        },
        "patrones_detectados": resumen_simbionte["patrones_detectados"],
        "n_oraciones": resumen_simbionte["n_oraciones"],
    }

    user_msg = f"""INPUT ORIGINAL (primeros 500 chars):
{texto_original[:500]}...

ANÁLISIS SIMBIONTE:
{json.dumps(input_simbionte, ensure_ascii=False, indent=2)}

Evalúa las 9 dims cognitivas y genera bytecode de prescripción."""

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        temperature=0.0,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT_CAPA2,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": '{"diagnostico":'},
        ],
    )

    dt = time.time() - t0
    raw = '{"diagnostico":' + resp.content[0].text

    # Parse JSON robusto
    try:
        # Cerrar JSON si está truncado
        depth = 0
        for ch in raw:
            if ch == '{': depth += 1
            elif ch == '}': depth -= 1
        while depth > 0:
            raw += '}'
            depth -= 1
        bytecode = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: bytecode mínimo
        bytecode = {
            "diagnostico": {
                "patron_principal": "desconocido",
                "confianza": 0.3,
                "dims_evaluadas": {}
            },
            "prescripcion": {
                "accion": "registrar_sin_accion",
                "instrucciones_traductor": ["Responde de forma neutral"]
            },
            "metadata": {"modo_recibido": "sin_ancla", "geometria_cumplida": False}
        }

    # Validar acción del vocabulario cerrado
    accion = bytecode.get("prescripcion", {}).get("accion", "")
    if accion not in ACCIONES_PERMITIDAS:
        bytecode["prescripcion"]["accion"] = "registrar_sin_accion"
        bytecode.setdefault("metadata", {})["accion_corregida"] = accion

    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cache_read": getattr(resp.usage, 'cache_read_input_tokens', 0),
        "cache_creation": getattr(resp.usage, 'cache_creation_input_tokens', 0),
        "coste_usd": (
            resp.usage.input_tokens * 3.0 +
            resp.usage.output_tokens * 15.0 +
            getattr(resp.usage, 'cache_read_input_tokens', 0) * 0.30 +
            getattr(resp.usage, 'cache_creation_input_tokens', 0) * 3.75
        ) / 1_000_000,
        "latencia_s": round(dt, 2),
        "stop_reason": resp.stop_reason,
    }

    return bytecode, usage


# ============================================================
# AGENTE MODULADOR (Python determinista, ~1ms)
# ============================================================

def agente_modulador(resumen_simbionte, bytecode):
    """Decide tono, T, modelo y max_tokens del Traductor."""
    fg = resumen_simbionte["fg_global"]
    tension = resumen_simbionte["ratio_adversativo"]
    confianza = bytecode.get("diagnostico", {}).get("confianza", 0.5)
    accion = bytecode.get("prescripcion", {}).get("accion", "registrar_sin_accion")

    # Estado INCIERTO: prioridad sobre los demás
    if confianza < 0.4:
        return {
            "temperature": 0.3,
            "tono": "exploratorio",
            "system_prompt": "El sistema tiene baja confianza en el análisis. Responde haciendo una pregunta clarificadora al usuario. No prescribas acciones.",
            "max_tokens": 150,
            "modelo": "haiku",
        }

    # Estado CALIENTE: tensión alta
    if fg < 0.3 or tension > 0.15:
        return {
            "temperature": 0.6,
            "tono": "desescalada",
            "system_prompt": "El usuario está en estado de tensión alta. Protocolo de desescalada: 1) Reconoce su situación sin validar las excusas. 2) Espejea una emoción antes de prescribir. 3) Propón una acción mínima y alcanzable.",
            "max_tokens": 350,
            "modelo": "sonnet",
        }

    # Estado FRÍO: directo, va al grano
    if fg > 0.7 and tension < 0.05:
        return {
            "temperature": 0.1,
            "tono": "clinico",
            "system_prompt": "Responde de forma directa y breve. Solo datos y acciones. Cero rodeos.",
            "max_tokens": 150,
            "modelo": "haiku",
        }

    # Estado TEMPLADO: default
    return {
        "temperature": 0.4,
        "tono": "profesional",
        "system_prompt": "Responde de forma profesional y clara. Ofrece una alternativa concreta. Tono educado pero sin exceso de empatía.",
        "max_tokens": 250,
        "modelo": "haiku",
    }


# ============================================================
# CAPA 3: TRADUCTOR
# ============================================================

def capa3_traductor(bytecode, config_modulador, client):
    """Traduce bytecode JSON → texto natural para el usuario."""
    t0 = time.time()

    accion = bytecode.get("prescripcion", {}).get("accion", "registrar_sin_accion")
    instrucciones = bytecode.get("prescripcion", {}).get("instrucciones_traductor", [])
    patron = bytecode.get("diagnostico", {}).get("patron_principal", "")
    dims = bytecode.get("diagnostico", {}).get("dims_evaluadas", {})

    # Construir prompt del Traductor
    bytecode_str = json.dumps({
        "accion": accion,
        "patron": patron,
        "instrucciones": instrucciones,
        "dims_clave": {k: v for k, v in dims.items() if v >= 4},  # Solo dims altas
    }, ensure_ascii=False, indent=2)

    # Restricciones geométricas (de H2)
    restricciones = """RESTRICCIONES ABSOLUTAS:
- NO usar modo condicional ("gustaría", "podría", "debería")
- NO usar estructuras adversativas ("pero", "aunque", "sin embargo") a menos que la prescripción lo requiera
- Máximo 4 oraciones
- Responde en español
- NO añadas disclaimers, disculpas ni meta-comentarios"""

    model = "claude-sonnet-4-20250514" if config_modulador["modelo"] == "sonnet" else "claude-haiku-4-5-20251001"

    resp = client.messages.create(
        model=model,
        max_tokens=config_modulador["max_tokens"],
        temperature=config_modulador["temperature"],
        system=config_modulador["system_prompt"],
        messages=[{"role": "user", "content": f"""Traduce este bytecode a texto natural para el usuario.

BYTECODE:
{bytecode_str}

{restricciones}"""}],
    )

    dt = time.time() - t0
    texto_final = resp.content[0].text.strip()

    usage = {
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "coste_usd": (
            resp.usage.input_tokens * (3.0 if "sonnet" in model else 1.0) +
            resp.usage.output_tokens * (15.0 if "sonnet" in model else 5.0)
        ) / 1_000_000,
        "latencia_s": round(dt, 2),
        "modelo": model,
        "tono": config_modulador["tono"],
    }

    return texto_final, usage


# ============================================================
# HARNESS H3: Verificación geométrica del output
# ============================================================

def harness_h3(texto_final, doc_output):
    """Verifica restricciones geométricas del output del Traductor."""
    checks = {"passed": True, "violations": []}

    toks = [t for t in doc_output if not t.is_punct and not t.is_space]

    # Check 1: cero condicionales
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd")
    if n_cnd > 0:
        checks["violations"].append(f"condicional_detectado: {n_cnd} tokens con Mood=Cnd")
        checks["passed"] = False

    # Check 2: máximo 4 oraciones
    sents = list(doc_output.sents)
    if len(sents) > 5:  # margen de 1
        checks["violations"].append(f"exceso_oraciones: {len(sents)} (max 4)")
        checks["passed"] = False

    # Check 3: no vacío
    if len(toks) < 3:
        checks["violations"].append("output_vacio")
        checks["passed"] = False

    # Check 4: F_G estimado
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)
    n_nom = sum(1 for t in toks if t.pos_ == "NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv_out = contar_adversativos(doc_output)
    fg = max(0.0, min(1.0, 1.0 - (safe_div(n_cnd, n_verbs) * 0.25 +
                                    safe_div(n_nom, n_total) * 0.15 +
                                    safe_div(n_adv_out, n_total) * 0.20)))
    checks["fg_output"] = round(fg, 3)
    if fg < 0.6:
        checks["violations"].append(f"fg_bajo: {fg:.3f} (min 0.6)")
        checks["passed"] = False

    checks["n_oraciones"] = len(sents)
    checks["n_tokens"] = len(toks)
    return checks


# ============================================================
# PIPELINE E2E
# ============================================================

def run_e2e(texto, nlp, client, verbose=True):
    """Ejecuta el pipeline completo y devuelve resultados."""
    resultados = {"timings": {}, "costs": {}, "stages": {}}
    t_total = time.time()

    # === CAPA 0: Simbionte v4 ===
    if verbose: print("\n" + "="*60)
    if verbose: print("CAPA 0: Simbionte v4 (determinista)")
    if verbose: print("="*60)

    doc = nlp(texto)
    vector, func_result, resumen, dt_c0 = capa0_simbionte(doc)
    resultados["timings"]["capa0"] = round(dt_c0 * 1000)
    resultados["stages"]["capa0"] = resumen

    if verbose:
        print(f"  Vector: {len(vector)}D en {dt_c0*1000:.0f}ms")
        print(f"  F_G: {resumen['fg_global']}")
        print(f"  Patrones: {resumen['patrones_detectados']}")
        print(f"  Top funciones: {resumen['top_funciones']}")
        print(f"  Determinista: {resumen['pct_determinista']:.1f}%, Haiku: {resumen['tokens_haiku']} tokens")

    # === HARNESS H1: Clasificar tokens ambiguos ===
    if verbose: print("\n" + "-"*40)
    if verbose: print("HARNESS H1: Clasificar tokens ambiguos")

    h1_result, h1_stats = harness_h1(func_result, API_KEY)
    resultados["stages"]["h1"] = h1_stats
    resultados["costs"]["h1"] = h1_stats.get("coste_usd", 0)

    if verbose:
        if h1_stats.get("skipped"):
            print("  Skipped — 0 tokens ambiguos")
        else:
            print(f"  Clasificados: {h1_stats.get('n_clasificados', 0)}")
            print(f"  Coste: ${h1_stats.get('coste_usd', 0):.4f}")

    # === CAPA 2: LLM Enjaulado (Sonnet) ===
    if verbose: print("\n" + "="*60)
    if verbose: print("CAPA 2: LLM Enjaulado (Sonnet, T=0, JSON, pre-fill)")
    if verbose: print("="*60)

    bytecode, c2_usage = capa2_llm_enjaulado(texto, resumen, client)
    resultados["timings"]["capa2"] = round(c2_usage["latencia_s"] * 1000)
    resultados["stages"]["capa2_bytecode"] = bytecode
    resultados["stages"]["capa2_usage"] = c2_usage
    resultados["costs"]["capa2"] = c2_usage["coste_usd"]

    if verbose:
        print(f"  Latencia: {c2_usage['latencia_s']:.1f}s")
        print(f"  Tokens: {c2_usage['input_tokens']} in / {c2_usage['output_tokens']} out")
        print(f"  Cache: read={c2_usage['cache_read']}, creation={c2_usage['cache_creation']}")
        print(f"  Coste: ${c2_usage['coste_usd']:.4f}")
        print(f"  Stop: {c2_usage['stop_reason']}")
        print(f"\n  BYTECODE:")
        print(f"    Patrón: {bytecode.get('diagnostico', {}).get('patron_principal', '?')}")
        print(f"    Confianza: {bytecode.get('diagnostico', {}).get('confianza', '?')}")
        print(f"    Acción: {bytecode.get('prescripcion', {}).get('accion', '?')}")
        dims = bytecode.get('diagnostico', {}).get('dims_evaluadas', {})
        if dims:
            print(f"    Dims:")
            for d, v in dims.items():
                print(f"      {d}: {v}")
        instrs = bytecode.get('prescripcion', {}).get('instrucciones_traductor', [])
        if instrs:
            print(f"    Instrucciones traductor:")
            for i, inst in enumerate(instrs):
                print(f"      {i+1}. {inst}")

    # === AGENTE MODULADOR (determinista, ~0ms) ===
    if verbose: print("\n" + "-"*40)
    if verbose: print("AGENTE MODULADOR (determinista)")

    config_mod = agente_modulador(resumen, bytecode)
    resultados["stages"]["modulador"] = config_mod

    if verbose:
        print(f"  Tono: {config_mod['tono']}")
        print(f"  T: {config_mod['temperature']}")
        print(f"  Modelo: {config_mod['modelo']}")
        print(f"  Max tokens: {config_mod['max_tokens']}")

    # === CAPA 3: TRADUCTOR ===
    if verbose: print("\n" + "="*60)
    if verbose: print(f"CAPA 3: Traductor ({config_mod['modelo']}, T={config_mod['temperature']}, tono={config_mod['tono']})")
    if verbose: print("="*60)

    texto_final, c3_usage = capa3_traductor(bytecode, config_mod, client)
    resultados["timings"]["capa3"] = round(c3_usage["latencia_s"] * 1000)
    resultados["stages"]["capa3_output"] = texto_final
    resultados["stages"]["capa3_usage"] = c3_usage
    resultados["costs"]["capa3"] = c3_usage["coste_usd"]

    if verbose:
        print(f"\n  OUTPUT FINAL:")
        print(f"  ─────────────")
        print(f"  {texto_final}")
        print(f"  ─────────────")
        print(f"  Latencia: {c3_usage['latencia_s']:.1f}s")
        print(f"  Tokens: {c3_usage['input_tokens']} in / {c3_usage['output_tokens']} out")
        print(f"  Coste: ${c3_usage['coste_usd']:.6f}")

    # === HARNESS H3: Verificación geométrica ===
    if verbose: print("\n" + "-"*40)
    if verbose: print("HARNESS H3: Verificación geométrica del output")

    doc_output = nlp(texto_final)
    h3 = harness_h3(texto_final, doc_output)
    resultados["stages"]["h3"] = h3

    if verbose:
        status = "✅ PASADO" if h3["passed"] else "❌ FALLADO"
        print(f"  {status}")
        print(f"  F_G output: {h3['fg_output']}")
        print(f"  Oraciones: {h3['n_oraciones']}, Tokens: {h3['n_tokens']}")
        for v in h3["violations"]:
            print(f"  ⚠️ {v}")

    # === RESUMEN ===
    dt_total = time.time() - t_total
    resultados["timings"]["total_ms"] = round(dt_total * 1000)
    coste_total = sum(resultados["costs"].values())
    resultados["costs"]["total"] = round(coste_total, 6)

    if verbose:
        print("\n" + "="*60)
        print("RESUMEN E2E")
        print("="*60)
        print(f"  Latencia total: {dt_total:.1f}s")
        print(f"    Capa 0 (spaCy):  {resultados['timings']['capa0']}ms")
        print(f"    Capa 2 (Sonnet): {resultados['timings']['capa2']}ms")
        print(f"    Capa 3 (Trad.):  {resultados['timings']['capa3']}ms")
        print(f"  Coste total: ${coste_total:.4f}")
        print(f"    H1: ${resultados['costs'].get('h1', 0):.4f}")
        print(f"    Capa 2: ${resultados['costs']['capa2']:.4f}")
        print(f"    Capa 3: ${resultados['costs']['capa3']:.6f}")
        print(f"  H3 verificación: {'✅' if h3['passed'] else '❌'}")
        print(f"  Pipeline completo: Simbionte v4 → Sonnet → {config_mod['modelo'].capitalize()}")

    return resultados


# ============================================================
# REPETICIONES PARA MEDIR VARIANZA
# ============================================================

def run_varianza(texto, nlp, client, n_reps=3):
    """Ejecuta N repeticiones y mide varianza de dims y coste."""
    print(f"\n{'#'*60}")
    print(f"TEST VARIANZA: {n_reps} repeticiones")
    print(f"{'#'*60}")

    all_dims = []
    all_costs = []
    all_outputs = []

    for i in range(n_reps):
        print(f"\n--- Repetición {i+1}/{n_reps} ---")
        r = run_e2e(texto, nlp, client, verbose=(i == 0))
        dims = r["stages"].get("capa2_bytecode", {}).get("diagnostico", {}).get("dims_evaluadas", {})
        all_dims.append(dims)
        all_costs.append(r["costs"]["total"])
        all_outputs.append(r["stages"].get("capa3_output", ""))
        if i > 0:
            print(f"  Coste: ${r['costs']['total']:.4f} | Acción: {r['stages']['capa2_bytecode'].get('prescripcion', {}).get('accion', '?')}")
            print(f"  Output: {r['stages'].get('capa3_output', '')[:100]}...")

    # Análisis
    print(f"\n{'='*60}")
    print("ANÁLISIS DE VARIANZA")
    print(f"{'='*60}")

    if all_dims:
        all_dim_names = set()
        for d in all_dims:
            all_dim_names.update(d.keys())

        print(f"\n  {'Dim':<35s} {'Media':>6s} {'Std':>6s} {'Min':>4s} {'Max':>4s}")
        print(f"  {'-'*35} {'-'*6} {'-'*6} {'-'*4} {'-'*4}")
        total_var = 0
        for name in sorted(all_dim_names):
            vals = [d.get(name, 0) for d in all_dims]
            mean = np.mean(vals)
            std = np.std(vals)
            total_var += std
            print(f"  {name:<35s} {mean:6.2f} {std:6.2f} {min(vals):4.0f} {max(vals):4.0f}")

        var_media = total_var / max(len(all_dim_names), 1)
        print(f"\n  Varianza media dims: {var_media:.3f}")

    print(f"\n  Coste medio: ${np.mean(all_costs):.4f} ± ${np.std(all_costs):.4f}")
    print(f"  Coste total ({n_reps} reps): ${sum(all_costs):.4f}")

    # Comparar outputs
    print(f"\n  Outputs del Traductor:")
    for i, out in enumerate(all_outputs):
        print(f"    [{i+1}] {out[:120]}...")

    return all_dims, all_costs, all_outputs


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import spacy

    print("Cargando spaCy es_dep_news_trf...")
    nlp = spacy.load("es_dep_news_trf")

    print("Conectando Anthropic API...")
    client = anthropic.Anthropic(api_key=API_KEY)

    # Cargar texto de prueba
    texto_path = "/tmp/texto_test_1200.txt"
    if not os.path.exists(texto_path):
        print(f"ERROR: no existe {texto_path}")
        sys.exit(1)

    with open(texto_path) as f:
        texto = f.read().strip()

    print(f"Texto: {len(texto.split())} palabras, {len(texto)} chars")

    # 1 ejecución completa (verbose)
    resultados = run_e2e(texto, nlp, client, verbose=True)

    # N repeticiones para varianza
    n_reps = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    if n_reps > 1:
        run_varianza(texto, nlp, client, n_reps=n_reps)

    # Guardar resultados
    output_path = os.path.join(os.path.dirname(__file__), "../../data/test_e2e_v4_harness.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Serializar solo lo serializable
    save_data = {
        "version": "e2e_v4_harness",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "texto_words": len(texto.split()),
        "timings": resultados["timings"],
        "costs": resultados["costs"],
        "capa2_bytecode": resultados["stages"].get("capa2_bytecode"),
        "capa3_output": resultados["stages"].get("capa3_output"),
        "h3_verificacion": resultados["stages"].get("h3"),
        "modulador": resultados["stages"].get("modulador"),
        "resumen_simbionte": resultados["stages"].get("capa0"),
    }
    with open(output_path, "w") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    print(f"\nResultados guardados en {output_path}")
