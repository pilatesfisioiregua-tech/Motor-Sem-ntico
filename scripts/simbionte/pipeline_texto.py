"""
Pipeline Final para TEXTO — El mismo pipeline de Economía pero sobre texto natural.

Fecha: 2026-04-13

Flujo:
  Texto → spaCy → Simbionte v6 (361D) → Decodificador inverso
  → Protocolo paso a paso → pgvector (significado + isomorfismos)
  → LLM enjaulado → Traductor → H3

El Simbionte convierte texto en:
  - 266D de 10 marcos × 4 niveles (tokens, oraciones, párrafos, texto)
  - 95D de geometría del isomorfismo
  - Decodificación: cada marco traducido a texto legible

El pipeline usa EXACTAMENTE la misma arquitectura que para economía.

$0 el Simbionte (spaCy local). Coste solo de LLM.
"""

import sys, os, time, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))

import spacy
import httpx

from poc_capa0_v6 import calcular_vector_v6
from marcos_matematicos import FEATURES_POR_NIVEL
from geometria_isomorfismo import calcular_geometria_completa
from decodificador_inverso import construir_prompt_decodificado
from semantica_formulas import SEMANTICA
from pipeline_completo import h3_verificar


PGVECTOR_URL = "https://motor-semantico-omni.fly.dev/conocimiento-proyecto"

# Cargar spaCy una sola vez
_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("es_dep_news_trf")
    return _nlp


# ============================================================
# PROTOCOLO PARA TEXTO (adaptado del protocolo de datos)
# ============================================================

PROTOCOLO_TEXTO = [
    {
        "nombre": "Entender la pregunta",
        "pregunta_clave": "¿Qué se pregunta sobre este texto?",
        "instruccion": "Reformula la pregunta. ¿Se pide análisis retórico? ¿Detección de falacias? ¿Evaluación de argumentos? ¿Estructura del discurso?",
    },
    {
        "nombre": "Diagnóstico estructural",
        "pregunta_clave": "¿Qué estructura tiene el texto según el Simbionte?",
        "instruccion": "Usa los datos del Simbionte para diagnosticar: diversidad funcional, profundidad de razonamiento, fragmentación, feedback loops, coherencia, gaps.",
    },
    {
        "nombre": "Buscar patrones y precedentes",
        "pregunta_clave": "¿Este texto se parece a algo conocido?",
        "instruccion": "Consulta pgvector para buscar isomorfismos. ¿La geometría del texto coincide con patrones catalogados?",
    },
    {
        "nombre": "Verificar razonamiento",
        "pregunta_clave": "¿Lo que dice el texto es consistente con su estructura?",
        "instruccion": "Verificación cruzada: ¿las conclusiones del autor coinciden con la estructura detectada? Si dice 'argumento sólido' pero la estructura muestra gaps → ALERTA.",
    },
    {
        "nombre": "Detectar falacias y sesgos",
        "pregunta_clave": "¿Hay errores lógicos o manipulación?",
        "instruccion": "Usa los datos de cibernética (feedback), juegos (tensión), topología (gaps), geometría (giros) para detectar falacias estructurales.",
    },
    {
        "nombre": "Síntesis final",
        "pregunta_clave": "¿Qué le digo al usuario?",
        "instruccion": "Produce JSON con: tipo_texto, estructura, fortalezas, debilidades, falacias, presupuestos_ocultos, veredicto.",
    },
]


def pipeline_texto(texto, pregunta, client, model, is_anthropic=True):
    """Ejecuta el pipeline FINAL sobre texto natural.

    Args:
        texto: el texto a analizar
        pregunta: qué se pregunta sobre el texto
        client: Anthropic o OpenRouter client
        model: nombre del modelo
        is_anthropic: True para Anthropic API

    Returns: dict con respuesta, métricas
    """
    t0 = time.time()

    # 1. SIMBIONTE: texto → vector 361D
    nlp = get_nlp()
    doc = nlp(texto)
    vector, meta = calcular_vector_v6(doc)

    vectores = {
        "N1": vector[0:FEATURES_POR_NIVEL],
        "N2": vector[FEATURES_POR_NIVEL:2*FEATURES_POR_NIVEL],
        "N3": vector[2*FEATURES_POR_NIVEL:3*FEATURES_POR_NIVEL],
        "N4": vector[3*FEATURES_POR_NIVEL:4*FEATURES_POR_NIVEL],
    }

    # 2. GEOMETRÍA
    geo = calcular_geometria_completa(vectores)

    # 3. DECODIFICADOR INVERSO
    contexto_simbionte = construir_prompt_decodificado(vectores, geo)

    # 4. pgvector: buscar isomorfismos del texto
    pgvector_context = ""
    try:
        r = httpx.post(f"{PGVECTOR_URL}/query",
            json={"query": f"isomorfismo texto estructura {' '.join(geo.get('geometrias',{}).get('N1',{}).get('forma',{}).get('dominantes',[]))}", "top_k": 2},
            timeout=8)
        if r.status_code == 200:
            for c in r.json().get("conocimiento", []):
                if c.get("similaridad", 0) > 0.4:
                    pgvector_context += f"\n--- pgvector ---\n{c['contenido'][:400]}\n"
    except:
        pass

    # 5. Preguntas de los marcos (semántica de las 62 features)
    preguntas_marcos = []
    for n, sem in SEMANTICA.items():
        if n.startswith("marco_") and sem.get("pregunta"):
            preguntas_marcos.append(f"  - {sem['pregunta']}")

    dt_simbionte = time.time() - t0

    # 6. LOOP PASO A PASO
    hallazgos = ""
    all_responses = []
    total_tokens_in = 0
    total_tokens_out = 0

    system_base = f"""Eres un analista de texto ENJAULADO. Sigues un protocolo paso a paso.

REGLAS:
- SOLO cita datos que aparecen en el contexto del Simbionte. NO inventes.
- Cada hallazgo: [VERIFICADO] si estructura confirma, ⚡ ALERTA si contradice.
- El último paso produce JSON.

DATOS DEL SIMBIONTE (estructura del texto):
{contexto_simbionte[:3000]}

{pgvector_context}

PREGUNTAS ESTRUCTURALES (verificar en cada paso):
{chr(10).join(preguntas_marcos[:15])}"""

    for i, paso in enumerate(PROTOCOLO_TEXTO):
        user_msg = f"""## PASO {i+1}: {paso['nombre']}
**Pregunta clave:** {paso['pregunta_clave']}
{paso['instruccion']}

TEXTO A ANALIZAR:
{texto}

HALLAZGOS PREVIOS:
{hallazgos if hallazgos else '(primer paso)'}

Ejecuta este paso. Cita datos del Simbionte."""

        if i == len(PROTOCOLO_TEXTO) - 1:
            user_msg += """

ÚLTIMO PASO. Produce JSON:
{
  "tipo_texto": "argumentativo/narrativo/manipulativo/técnico/emocional",
  "estructura": "descripción en 1 frase",
  "fortalezas": ["fortaleza 1"],
  "debilidades": ["debilidad 1"],
  "falacias": ["falacia 1 si hay"],
  "presupuestos_ocultos": ["lo que asume sin decir"],
  "veredicto": "evaluación final en 1 frase"
}"""

        if is_anthropic:
            response = client.messages.create(
                model=model, max_tokens=800, temperature=0,
                system=system_base,
                messages=[{"role": "user", "content": user_msg}],
            )
            paso_output = response.content[0].text
            total_tokens_in += response.usage.input_tokens
            total_tokens_out += response.usage.output_tokens
        else:
            response = client.chat.completions.create(
                model=model, max_tokens=800, temperature=0,
                messages=[
                    {"role": "system", "content": system_base},
                    {"role": "user", "content": user_msg},
                ],
            )
            paso_output = response.choices[0].message.content
            if response.usage:
                total_tokens_in += response.usage.prompt_tokens or 0
                total_tokens_out += response.usage.completion_tokens or 0

        all_responses.append({"paso": paso["nombre"], "output": paso_output})
        hallazgos += f"\n### {paso['nombre']}:\n{paso_output}"

    raw = hallazgos

    # 7. TRADUCTOR
    import anthropic as anth
    trad_client = anth.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY_1"))
    try:
        trad = trad_client.messages.create(
            model="claude-opus-4-20250514", max_tokens=800, temperature=0.3,
            system="Traductor: análisis técnico de texto → 3 párrafos claros. "
                   "Párrafo 1: qué tipo de texto es y cómo está estructurado. "
                   "Párrafo 2: qué fortalezas y debilidades tiene. "
                   "Párrafo 3: qué falacias o presupuestos ocultos hay. "
                   "No añadas info nueva. Máximo 250 palabras.",
            messages=[{"role": "user", "content": f"Traduce:\n\n{raw[-3000:]}"}],
        )
        traduccion = trad.content[0].text
        total_tokens_in += trad.usage.input_tokens
        total_tokens_out += trad.usage.output_tokens
    except Exception as e:
        traduccion = f"Error: {e}"

    # 8. H3 — verificar que no inventa
    # Para texto, H3 verifica contra los datos del Simbionte
    import re
    discrepancias = 0
    # Buscar números citados y comparar con el contexto
    nums_citados = re.findall(r'(\d+\.?\d*)', raw)
    nums_contexto = re.findall(r'(\d+\.?\d*)', contexto_simbionte)
    for n in nums_citados[:20]:
        if n not in nums_contexto and float(n) > 1:
            discrepancias += 1

    dt_total = time.time() - t0

    if is_anthropic and "opus" in model:
        cost = (total_tokens_in * 15 + total_tokens_out * 75) / 1e6
    elif is_anthropic:
        cost = (total_tokens_in * 3 + total_tokens_out * 15) / 1e6
    else:
        cost = (total_tokens_in * 5 + total_tokens_out * 15) / 1e6

    return {
        "respuesta_raw": raw,
        "respuesta": traduccion,
        "pasos": all_responses,
        "n_pasos": len(PROTOCOLO_TEXTO),
        "vector_dims": len(vector),
        "features_activas": int(np.sum(np.abs(vector) > 1e-10)),
        "geometria_profundidad": geo.get("profundidad_patron", 0),
        "n_discrepancias": discrepancias,
        "tokens_in": total_tokens_in,
        "tokens_out": total_tokens_out,
        "cost": cost,
        "dt_simbionte": dt_simbionte,
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

    TEXTOS = {
        "manipulativo": """Todo el mundo sabe que las vacunas causan más problemas de los que
resuelven. Mi vecino se vacunó y al mes siguiente le diagnosticaron una alergia nueva.
¿Casualidad? Los expertos que dicen lo contrario están pagados por las farmacéuticas.
Si realmente fueran seguras, ¿por qué no publican TODOS los datos? El gobierno nos
oculta la verdad porque le conviene tener una población enferma y dependiente.""",

        "argumentativo": """La educación universitaria debería ser gratuita porque constituye un
derecho fundamental. Los países nórdicos demuestran que el modelo funciona: Finlandia
no cobra matrícula y lidera los rankings PISA. Además, el retorno fiscal de un graduado
universitario supera en 340 mil euros al de alguien sin título a lo largo de su vida
laboral. Quienes argumentan que es insostenible ignoran que el gasto militar español
supera al educativo, lo cual revela dónde están realmente las prioridades.""",
    }

    PREGUNTA = "Analiza este texto: identifica estrategias retóricas, falacias, presupuestos ocultos, y qué le falta para ser un argumento completo."

    print("="*70)
    print("PIPELINE TEXTO — Test con Opus")
    print("="*70)

    for nombre, texto in TEXTOS.items():
        print(f"\n{'='*70}")
        print(f"TEXTO: {nombre} ({len(texto.split())} palabras)")
        print(f"{'='*70}")

        result = pipeline_texto(texto, PREGUNTA, client, "claude-opus-4-20250514")

        print(f"  Simbionte: {result['vector_dims']}D, {result['features_activas']} activas, {result['dt_simbionte']*1000:.0f}ms")
        print(f"  Profundidad: {result['geometria_profundidad']:.3f}")
        print(f"  Pasos: {result['n_pasos']} | H3: {result['n_discrepancias']}")
        print(f"  Coste: ${result['cost']:.4f} | Tiempo: {result['dt_total']:.0f}s")

        print(f"\n--- TRADUCCIÓN ---")
        print(result["respuesta"])
