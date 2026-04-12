"""
Harness H1 — Reclasificación + Determinación de tono
Fecha: 2026-04-12

Hace DOS cosas:
1. Clasifica tokens no resueltos por spaCy (ADJ, SUST, ADV, PREP, NUM→adjetivo)
   via Haiku (~$0.001 por texto)
2. Determina el tono del texto de entrada desde el vector del Simbionte
   (Python determinista, ~0ms, $0) — reemplaza al Modulador separado

El tono fluye: H1 lo detecta → Capa 2 lo recibe → Capa 3 lo aplica → H3 lo verifica.

Ref: HARNESS_ESPECIFICACION.md §F3 Depurar
Ref: CAPA_0_ESPECIFICACION.md §0 "Datos numéricos como adjetivos"
Ref: CAPA_3_ESPECIFICACION.md §2 "Agente Modulador" (fusionado aquí)
"""

import anthropic
import json


# ============================================================
# DETERMINACIÓN DE TONO (ex-Modulador, ahora dentro de H1)
# ============================================================

# Umbrales verificados con POC v3/v4 (2026-04-12)
TONOS = {
    "frio":      {"temperature": 0.1, "max_tokens": 150, "modelo": "haiku",
                  "system": "Responde de forma directa y breve. Solo datos y acciones. Cero rodeos. Máximo 2 oraciones."},
    "templado":  {"temperature": 0.4, "max_tokens": 250, "modelo": "haiku",
                  "system": "Responde de forma profesional y clara. Ofrece una alternativa concreta. Tono educado. Máximo 3 oraciones."},
    "caliente":  {"temperature": 0.6, "max_tokens": 350, "modelo": "sonnet",
                  "system": "El usuario está en tensión alta. 1) Reconoce su situación sin validar excusas. 2) Espejea una emoción. 3) Propón acción mínima alcanzable. Máximo 4 oraciones."},
    "incierto":  {"temperature": 0.3, "max_tokens": 150, "modelo": "haiku",
                  "system": "El análisis tiene baja confianza. Haz UNA pregunta clarificadora concreta. No prescribas."},
}


def determinar_tono(fg, ratio_adversativo, ratio_condicional, ratio_nominalizacion, confianza=None):
    """Determina tono del texto desde métricas del Simbionte.

    No es un componente separado — es una función que H1 ejecuta
    después de calcular el vector. El tono viaja con el resumen
    hasta Capa 3 (Traductor) y H3 (verificación).

    Args:
        fg: Fuerza Generativa global (0-1). Alto=directo, bajo=evasivo
        ratio_adversativo: proporción de adversativos. Alto=tensión
        ratio_condicional: proporción de condicionales. Alto=evasión
        ratio_nominalizacion: proporción de nominalizaciones. Alto=opacidad
        confianza: confianza del Simbionte (float o None)

    Returns:
        dict con: tono, temperature, max_tokens, modelo, system, razones
    """
    razones = []

    # Incierto: prioridad sobre los demás
    if confianza is not None and confianza < 0.4:
        razones.append(f"confianza_baja={confianza:.2f}")
        return {**TONOS["incierto"], "tono": "incierto", "razones": razones}

    # Caliente: tensión alta O F_G muy baja
    tension = ratio_adversativo + ratio_condicional * 0.5
    if fg < 0.3 or tension > 0.15:
        if fg < 0.3: razones.append(f"fg_bajo={fg:.3f}")
        if tension > 0.15: razones.append(f"tension_alta={tension:.3f}")
        return {**TONOS["caliente"], "tono": "caliente", "razones": razones}

    # Frío: directo, va al grano
    if fg > 0.7 and tension < 0.05 and ratio_nominalizacion < 0.05:
        razones.append(f"fg_alto={fg:.3f}, tension_baja={tension:.3f}")
        return {**TONOS["frio"], "tono": "frio", "razones": razones}

    # Templado: default
    razones.append(f"fg={fg:.3f}, tension={tension:.3f}")
    return {**TONOS["templado"], "tono": "templado", "razones": razones}


def clasificar_haiku(tokens_haiku, api_key, texto_contexto=""):
    """Clasifica tokens no resueltos usando Haiku.

    Args:
        tokens_haiku: list of dicts con {text, pos, dep, head, func_asignada}
        api_key: ANTHROPIC_API_KEY
        texto_contexto: oración o texto para dar contexto

    Returns:
        dict: {token_text: func_clasificada}
    """
    if not tokens_haiku:
        return {}

    client = anthropic.Anthropic(api_key=api_key)

    # Construir prompt compacto
    tokens_str = "\n".join(
        f"  {i+1}. \"{t['text']}\" (POS={t['pos']}, DEP={t['dep']}, modifica a \"{t['head']}\")"
        for i, t in enumerate(tokens_haiku)
    )

    prompt = f"""Clasifica cada token por su función REAL en contexto. Responde SOLO JSON.

Tipos posibles para SUSTANTIVOS (cuando func_asignada=sust_no_clasificado):
  concreto = objeto físico perceptible
  abstracto = concepto no perceptible

Tipos posibles para ADJETIVOS (cuando func_asignada=adj_no_clasificado):
  calif_especificativo = distingue CUÁL entre opciones ("la inversión fallida")
  calif_explicativo = cualidad inherente, embellece ("los enormes beneficios")

Tipos posibles para ADVERBIOS (cuando func_asignada=adv_no_clasificado):
  adv_modo = cómo (bien, mal, rápido)
  adv_grado = cuánto (bastante, demasiado)
  adv_afirmacion = sí, claro, efectivamente

Tipos posibles para PREPOSICIONES (cuando func_asignada=prep_no_clasificado):
  prep_causal = causa/origen ("por eso", "por culpa de")
  prep_agente = agente de pasiva ("construido por ellos")
  prep_espacial = lugar ("por la calle", "por debajo")

Tipos posibles para NÚMEROS (cuando func_asignada=num_cardinal y needs_haiku=True):
  Los datos numéricos en un texto NO son matemáticas — son adjetivos comprimidos que califican al sujeto posicionándolo en un eje.
  Clasifica QUÉ TIPO DE ADJETIVO cumple este número en ESTA oración:
  num_calif_espec = especifica CUÁL entre opciones ("facturó 47 millones" → cuánto facturó, califica la acción)
  num_calif_explic = atribuye cualidad inherente o valorativa ("los enormes 3M€")
  num_predicativo = atributo vía cópula ("el margen ES 15%", "la cifra FUE 3000")
  num_posesivo = con poseedor ("sus 47 millones", "nuestro 15%")
  num_indefinido = cantidad con matiz de insuficiencia/imprecisión ("solo 1.200€", "apenas el 2%")
  num_cardinal = simple cantidad sin función adjetival especial ("tres factores", "cuatro horas")

Tokens a clasificar:
{tokens_str}

Responde SOLO JSON: {{"1": "tipo", "2": "tipo", ...}}"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}]
        )

        text = resp.content[0].text.strip()
        # Limpiar backticks de Sonnet/Haiku
        if "```" in text:
            # Extraer contenido entre primer ``` y último ```
            start = text.index("```") + 3
            end = text.rindex("```")
            text = text[start:end].strip()
            # Quitar "json" si está al inicio
            if text.startswith("json"):
                text = text[4:].strip()

        clasificaciones = json.loads(text)

        # Mapear de vuelta a los tokens
        resultado = {}
        for i, t in enumerate(tokens_haiku):
            key = str(i + 1)
            if key in clasificaciones:
                func = clasificaciones[key]
                # Mapear a nombre funcional completo
                if t["func_asignada"] == "sust_no_clasificado":
                    if func in ("concreto", "abstracto"):
                        resultado[t["text"]] = f"sust_{func}"
                    else:
                        resultado[t["text"]] = "sust_abstracto"  # default
                elif t["func_asignada"] == "adj_no_clasificado":
                    if func in ("calif_especificativo", "calif_explicativo"):
                        resultado[t["text"]] = f"adj_{func}"
                    else:
                        resultado[t["text"]] = "adj_calif_especificativo"  # default
                elif t["func_asignada"] == "adv_no_clasificado":
                    if func.startswith("adv_"):
                        resultado[t["text"]] = func
                    else:
                        resultado[t["text"]] = f"adv_{func}"
                elif t["func_asignada"] == "prep_no_clasificado":
                    if func.startswith("prep_"):
                        resultado[t["text"]] = func
                    else:
                        resultado[t["text"]] = f"prep_{func}"
                elif t["func_asignada"] == "num_cardinal" and t["pos"] == "NUM":
                    # Números reclasificados como adjetivos por función
                    NUM_VALID = {"num_calif_espec", "num_calif_explic", "num_predicativo",
                                 "num_posesivo", "num_indefinido", "num_cardinal"}
                    if func in NUM_VALID:
                        resultado[t["text"]] = func
                    elif func.startswith("num_"):
                        resultado[t["text"]] = func
                    else:
                        resultado[t["text"]] = f"num_{func}" if not func.startswith("num") else func
                else:
                    resultado[t["text"]] = func

        return resultado, {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "n_clasificados": len(resultado),
            "coste_usd": (resp.usage.input_tokens * 0.80 + resp.usage.output_tokens * 4) / 1_000_000,
        }

    except Exception as e:
        # Fallback: clasificar con defaults
        resultado = {}
        for t in tokens_haiku:
            if t["func_asignada"] == "sust_no_clasificado":
                resultado[t["text"]] = "sust_abstracto"
            elif t["func_asignada"] == "adj_no_clasificado":
                resultado[t["text"]] = "adj_calif_especificativo"
            elif t["func_asignada"] == "adv_no_clasificado":
                resultado[t["text"]] = "adv_modo"
            elif t["func_asignada"] == "num_cardinal" and t.get("pos") == "NUM":
                resultado[t["text"]] = "num_cardinal"
            elif t["func_asignada"] == "prep_no_clasificado":
                resultado[t["text"]] = "prep_causal"
        return resultado, {"error": str(e), "fallback": True}


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from clasificador_funcional import distribucion_funcional
    import spacy

    API_KEY = "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"

    nlp = spacy.load('es_dep_news_trf')

    with open('/tmp/texto_test_1200.txt') as f:
        texto = f.read().strip()

    doc = nlp(texto)
    result = distribucion_funcional(doc)

    print(f"Tokens para Haiku: {len(result['tokens_haiku'])}")
    print()

    # Clasificar con Haiku
    clasificaciones, stats = clasificar_haiku(result["tokens_haiku"], API_KEY)

    print(f"Clasificaciones Haiku:")
    for text, func in clasificaciones.items():
        print(f"  \"{text}\" → {func}")

    print(f"\nStats: {stats}")
