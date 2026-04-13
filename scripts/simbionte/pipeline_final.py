"""
Pipeline FINAL — TODAS las piezas integradas.

Fecha: 2026-04-13

PIEZAS:
  1. Harness demand-driven (finalidad → fórmulas)
  2. Simbionte (calcula fórmulas sobre datos)
  3. Preguntas de las fórmulas (semántica: pregunta + polos + razonamiento)
  4. LLM enjaulado (JSON obligatorio, vocabulario cerrado)
  5. pgvector REAL (fly.io — busca significado + isomorfismos)
  6. Protocolo paso a paso (cada paso consulta lo que necesita)
  7. Loop output→input (cada paso acumula hallazgos)
  8. Traductor (JSON → lenguaje natural para CEO)
  9. H3 verificación (detecta datos inventados)

Funciona con CUALQUIER modelo via OpenRouter o Anthropic API.
"""

import sys, os, json, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from clasificador_economia import calcular_formulas_economia
from pipeline_completo import harness_seleccionar, h3_verificar, ISOMORFISMOS_CATALOGO
from semantica_formulas import SEMANTICA, razonamiento_a_texto
from catalogo_finalidades import detectar_finalidad
from red_preguntas import cascada, cascada_a_texto, ENLACES
from decodificador_economia import clasificar_nivel
from protocolo_analista import generar_schema


PGVECTOR_URL = "https://motor-semantico-omni.fly.dev/conocimiento-proyecto"


# ============================================================
# 1. PGVECTOR REAL — consulta fly.io
# ============================================================

def pgvector_buscar_formula(nombre):
    """Busca semántica de una fórmula en pgvector de fly.io."""
    # Local primero (más rápido)
    sem = SEMANTICA.get(nombre)
    texto_local = razonamiento_a_texto(nombre) if sem else None

    # pgvector remoto para enriquecer
    try:
        r = httpx.post(f"{PGVECTOR_URL}/query",
            json={"query": f"Formula {nombre} semántica razonamiento", "top_k": 1},
            timeout=8)
        if r.status_code == 200:
            data = r.json()
            if data.get("conocimiento") and data["conocimiento"][0].get("similaridad", 0) > 0.45:
                pgv_text = data["conocimiento"][0]["contenido"]
                # Combinar local + remoto
                if texto_local:
                    return f"{texto_local}\n\n--- pgvector ---\n{pgv_text[:500]}"
                return pgv_text[:1000]
    except:
        pass

    return texto_local or f"Fórmula '{nombre}' — sin semántica disponible."


def pgvector_buscar_patron(señales_texto):
    """Busca patrones históricos en pgvector de fly.io."""
    # Local
    local_matches = []
    resultados = _cache.get("resultados", {})
    for iso_nombre, iso_info in ISOMORFISMOS_CATALOGO.items():
        n_match = 0
        for señal, (op, threshold) in iso_info["señales"].items():
            for rn, ri in resultados.items():
                if señal in rn:
                    v = ri["valor"]
                    if (op == ">" and v > threshold) or (op == "<" and v < threshold):
                        n_match += 1
                    break
        if n_match >= len(iso_info["señales"]) * 0.5:
            local_matches.append(f"**{iso_nombre}** ({n_match}/{len(iso_info['señales'])} señales)\n"
                                 f"  {iso_info['descripcion']}\n"
                                 f"  Precedentes: {', '.join(iso_info['precedentes'])}\n"
                                 f"  Prescripción: {iso_info['prescripcion_historica']}")

    # pgvector remoto
    try:
        r = httpx.post(f"{PGVECTOR_URL}/query",
            json={"query": f"patrón histórico {señales_texto}", "top_k": 2, "tipo": "patron_validado"},
            timeout=8)
        if r.status_code == 200:
            for c in r.json().get("conocimiento", []):
                if c.get("similaridad", 0) > 0.45:
                    local_matches.append(f"--- pgvector ---\n{c['contenido'][:400]}")
    except:
        pass

    return "\n\n".join(local_matches) if local_matches else "Sin patrones históricos encontrados."


def pgvector_buscar_isomorfismo(gramatica_texto):
    """Busca isomorfismos por gramática compartida."""
    from gramatica_formulas import detectar_isomorfismos, FORMULAS, OPS
    isos = detectar_isomorfismos()
    matches = []
    for seq, nombres in isos.items():
        ramas = set(FORMULAS[n]["rama"] for n in nombres if n in FORMULAS)
        if len(ramas) > 1:
            ops_n = [list(OPS.keys())[list(OPS.values()).index(s)] for s in seq]
            matches.append(f"🔗 {'→'.join(ops_n)} = {', '.join(nombres[:5])} ({', '.join(ramas)})")
    return "\n".join(matches[:10]) if matches else "Sin isomorfismos cross-domain."


# ============================================================
# 2. CONSTRUIR CONTEXTO COMPLETO POR PASO
# ============================================================

_cache = {}


def construir_contexto_paso(paso_id, paso_info, resultados, hallazgos_previos):
    """Construye el contexto para UN paso del protocolo.

    Incluye:
    - Instrucciones del paso
    - Datos calculados relevantes
    - Preguntas de las fórmulas (semántica)
    - Isomorfismos si aplica
    - Hallazgos acumulados de pasos anteriores
    """
    lines = []
    lines.append(f"## PASO: {paso_info['nombre']}")
    lines.append(f"**Pregunta clave:** {paso_info['pregunta_clave']}")
    lines.append(f"{paso_info['descripcion']}")

    # Hallazgos previos
    if hallazgos_previos:
        lines.append(f"\n### HALLAZGOS ACUMULADOS DE PASOS ANTERIORES:")
        lines.append(hallazgos_previos)

    # Datos del Simbionte (filtrados por tipo de paso)
    sel = harness_seleccionar(resultados, 20)

    if "DIAGNOSTICO" in paso_id or "INVENTARIO" in paso_id or "CALIDAD" in paso_id:
        # Solo diagnóstico
        datos_lines = []
        for n, info, s, r, ni, nt in sel[:15]:
            v = info["valor"]; sg = "+" if v >= 0 else ""
            sem = SEMANTICA.get(n, {})
            pregunta = sem.get("pregunta", "")
            datos_lines.append(f"  {n}: {sg}{v:.4f} → {nt}")
            if pregunta:
                datos_lines.append(f"    Pregunta: {pregunta}")
        lines.append(f"\n### DATOS DEL SIMBIONTE:")
        lines.extend(datos_lines)

    elif "RELACION" in paso_id:
        # Correlaciones + elasticidades con preguntas
        for n, info, s, r, ni, nt in sel:
            if info["tipo"] in ("correlacion", "elasticidad"):
                v = info["valor"]; sg = "+" if v >= 0 else ""
                sem = SEMANTICA.get(n, {})
                lines.append(f"  {n}: {sg}{v:.4f} → {nt}")
                if sem.get("pregunta"):
                    lines.append(f"    Pregunta: {sem['pregunta']}")
                if sem.get("si_alto") and abs(v) > 0.5:
                    lines.append(f"    Significado: {sem['si_alto']}")

    elif "PATRON" in paso_id:
        # Patrones históricos
        señales = " ".join(f"{n}={info['valor']:.2f}" for n, info, _, _, _, _ in sel[:5])
        patron = pgvector_buscar_patron(señales)
        lines.append(f"\n### PATRONES HISTÓRICOS:")
        lines.append(patron)

        # Isomorfismos
        isos = pgvector_buscar_isomorfismo("")
        if "Sin isomorfismos" not in isos:
            lines.append(f"\n### ISOMORFISMOS CROSS-DOMAIN:")
            lines.append(isos)

    elif "VERIFICACION" in paso_id:
        # Semántica completa de fórmulas clave
        lines.append(f"\n### SEMÁNTICA PARA VERIFICAR:")
        for n, info, s, r, ni, nt in sel[:5]:
            texto = pgvector_buscar_formula(n)
            if texto:
                lines.append(f"\n{texto[:400]}")

    elif "PRESCRIPCION" in paso_id or "RIESGO" in paso_id:
        # Datos + preguntas + cascada
        resultados_por_tipo = {}
        for n, info in resultados.items():
            for enlace in ENLACES:
                if enlace in n or info["tipo"] == enlace:
                    if enlace not in resultados_por_tipo or abs(info["valor"]) > abs(resultados_por_tipo[enlace]):
                        resultados_por_tipo[enlace] = info["valor"]
        cadena = cascada(resultados_por_tipo, max_profundidad=2)
        if cadena:
            ctx_cascada = cascada_a_texto(cadena, resultados_por_tipo)
            lines.append(f"\n### CASCADA DE PREGUNTAS:")
            lines.append(ctx_cascada[:800])

    return "\n".join(lines)


# ============================================================
# 3. EJECUTAR PIPELINE COMPLETO
# ============================================================

def pipeline_final(series_dict, pregunta, client, model, is_anthropic=True):
    """Ejecuta el pipeline COMPLETO con TODAS las piezas.

    Args:
        series_dict: datos económicos
        pregunta: pregunta del usuario
        client: cliente API (Anthropic o OpenAI-compatible)
        model: nombre del modelo
        is_anthropic: True para Anthropic API, False para OpenRouter

    Returns: dict con respuesta, métricas, traducciones
    """
    global _cache
    t0 = time.time()

    # 1. HARNESS: detectar finalidad
    finalidades = detectar_finalidad(pregunta)

    # 2. SIMBIONTE: calcular fórmulas
    resultados = calcular_formulas_economia(series_dict)
    _cache["resultados"] = resultados

    # 3. PROTOCOLO: generar pasos
    schema, pasos = generar_schema(pregunta)

    # 4. LOOP: ejecutar paso a paso con acumulación
    hallazgos = ""
    all_responses = []
    total_tokens_in = 0
    total_tokens_out = 0

    system_base = """Eres un economista ENJAULADO. Sigues un protocolo paso a paso.

REGLAS:
- SOLO cita datos que aparecen en el contexto. NO inventes.
- Escribe "CONCLUSIÓN: [hallazgo con datos]" al final de cada paso.
- Usa [VERIFICADO] cuando los datos confirman tu análisis.
- Usa ⚡ ALERTA cuando hay contradicción.
- Di "sin datos" si no hay información.
- El último paso produce JSON con: diagnostico, desequilibrios, prescripcion_bc, prescripcion_gobierno, riesgos_ocultos, datos_clave."""

    for i, (paso_id, paso_info) in enumerate(pasos):
        contexto_paso = construir_contexto_paso(paso_id, paso_info, resultados, hallazgos)

        user_msg = f"{contexto_paso}\n\nEjecuta este paso. Cita datos específicos del Simbionte."
        if i == len(pasos) - 1:
            user_msg += "\n\nEste es el ÚLTIMO paso. Produce el JSON final de síntesis."

        if is_anthropic:
            import anthropic
            response = client.messages.create(
                model=model,
                max_tokens=800,
                temperature=0,
                system=system_base,
                messages=[{"role": "user", "content": user_msg}],
            )
            paso_output = response.content[0].text
            total_tokens_in += response.usage.input_tokens
            total_tokens_out += response.usage.output_tokens
        else:
            response = client.chat.completions.create(
                model=model,
                max_tokens=800,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_base},
                    {"role": "user", "content": user_msg},
                ],
            )
            paso_output = response.choices[0].message.content
            if response.usage:
                total_tokens_in += response.usage.prompt_tokens or 0
                total_tokens_out += response.usage.completion_tokens or 0

        all_responses.append({"paso": paso_id, "output": paso_output})
        hallazgos += f"\n\n### {paso_info['nombre']}:\n{paso_output}"

    # 5. COMBINAR respuestas
    raw_completo = hallazgos

    # 6. TRADUCTOR con Opus
    dt_agente = time.time() - t0
    import anthropic as anth_mod
    traductor_client = anth_mod.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY_1"))

    try:
        trad_resp = traductor_client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=1000,
            temperature=0.3,
            system="Traductor: análisis técnico → 3 párrafos claros para CEO. "
                   "No añadas info nueva. Cita los datos más importantes. Máximo 300 palabras.",
            messages=[{"role": "user", "content": f"Traduce este análisis:\n\n{raw_completo[-3000:]}"}],
        )
        traduccion = trad_resp.content[0].text
        total_tokens_in += trad_resp.usage.input_tokens
        total_tokens_out += trad_resp.usage.output_tokens
    except Exception as e:
        traduccion = f"Error traductor: {e}"

    # 7. H3 VERIFICACIÓN
    discrepancias = h3_verificar(raw_completo, resultados)

    dt_total = time.time() - t0

    # Coste
    if is_anthropic and "opus" in model:
        cost = (total_tokens_in * 15 + total_tokens_out * 75) / 1e6
    elif is_anthropic:
        cost = (total_tokens_in * 3 + total_tokens_out * 15) / 1e6
    else:
        # OpenRouter — estimación
        cost = (total_tokens_in * 5 + total_tokens_out * 15) / 1e6

    # Coste traductor (siempre Opus)
    cost += (trad_resp.usage.input_tokens * 15 + trad_resp.usage.output_tokens * 75) / 1e6 if 'trad_resp' in dir() else 0

    return {
        "respuesta_raw": raw_completo,
        "respuesta": traduccion,
        "pasos": all_responses,
        "n_pasos": len(pasos),
        "finalidades": finalidades,
        "n_discrepancias": len(discrepancias),
        "tokens_in": total_tokens_in,
        "tokens_out": total_tokens_out,
        "cost": cost,
        "dt_agente": dt_agente,
        "dt_total": dt_total,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY_1"))

    rng = np.random.default_rng(20); t = np.arange(48)
    series = {
        'pib': list(300000*(1-0.001*t)*(1+0.005*rng.standard_normal(48))),
        'inflacion': list(2+0.1*t+0.2*rng.standard_normal(48)),
        'desempleo': list(7+0.06*t+0.3*rng.standard_normal(48)),
        'tipo_interes': list(1.5+0.04*t+0.1*rng.standard_normal(48)),
        'consumo': list(0.58*300000+200*rng.standard_normal(48)),
        'inversion': list(0.22*300000+150*rng.standard_normal(48)),
        'exportaciones': list(0.30*300000+100*rng.standard_normal(48)),
        'importaciones': list(0.32*300000+100*rng.standard_normal(48)),
        'deuda_pib': list(80+0.3*t+0.5*rng.standard_normal(48)),
    }

    print("="*70)
    print("PIPELINE FINAL — Test rápido")
    print("="*70)

    result = pipeline_final(series, "¿Qué debería hacer el banco central?", client, "claude-opus-4-20250514")

    print(f"\n  Pasos: {result['n_pasos']}")
    print(f"  Finalidades: {result['finalidades']}")
    print(f"  H3: {result['n_discrepancias']}")
    print(f"  Coste: ${result['cost']:.4f}")
    print(f"  Tiempo: {result['dt_total']:.0f}s")
    print(f"\n--- TRADUCCIÓN ---")
    print(result["respuesta"])
