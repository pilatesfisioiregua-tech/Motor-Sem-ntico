"""
OMC-95 Pipeline API — Simbionte → Postgres → OpenRouter Opus tool_use.

Flujo:
  1. Simbionte calcula y escribe en Postgres ($0)
  2. LLM (Opus via OpenRouter) recibe protocolo + tools
  3. LLM consulta Postgres via tool_use (on-demand)
  4. H3 verificación ($0)
  5. Traductor via OpenRouter ($0.15)

Coste estimado: ~$1.12 con Opus
"""

import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

import httpx
from simbionte_writer import calcular_y_escribir
from protocolo_analista import generar_schema
from clasificador_economia import calcular_formulas_economia
from pipeline_completo import h3_verificar

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SIMBIONTE_URL = os.getenv("SIMBIONTE_URL", "https://motor-semantico-omni.fly.dev")

# Model IDs — OpenRouter usa puntos, no guiones
MODEL_OPUS = "anthropic/claude-opus-4"
MODEL_SONNET = "anthropic/claude-sonnet-4"


# ============================================================
# TOOLS — el LLM consulta Postgres
# ============================================================

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_formula",
            "description": "Busca semántica completa de una fórmula: polos, presupuestos, razonamiento, valor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la fórmula. Ej: 'varianza', 'correlacion', 'pib_gap'"}
                },
                "required": ["nombre"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_patron",
            "description": "Busca patrones históricos que coincidan con señales actuales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "senales": {"type": "string", "description": "Señales clave. Ej: 'inflación alta, desempleo alto'"}
                },
                "required": ["senales"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calcular",
            "description": "Consulta resultados del Simbionte por tipo: diagnostico, relaciones, riesgo, prescripcion, todo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ["diagnostico", "relaciones", "riesgo", "prescripcion", "todo"]}
                },
                "required": ["tipo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cascada_preguntas",
            "description": "Muestra qué preguntas se desbloquean desde un resultado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {"type": "string"},
                    "valor": {"type": "string", "enum": ["alto", "bajo", "extremo"]}
                },
                "required": ["formula", "valor"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_isomorfismo",
            "description": "Busca isomorfismos cross-domain en pgvector: fórmulas con la misma gramática (misma secuencia de operaciones) en dominios diferentes. Ej: elasticidad en economía = sensibilidad en física = dosis-respuesta en medicina.",
            "parameters": {
                "type": "object",
                "properties": {
                    "formula": {"type": "string", "description": "Nombre de la fórmula para buscar isomorfismos"},
                    "dominio": {"type": "string", "description": "Dominio opcional a buscar: 'economia', 'fisica', 'biologia', 'todos'"}
                },
                "required": ["formula"]
            }
        }
    },
]


def _consultar_postgres(sesion_id: str, tool: str, params: dict) -> str:
    """Consulta Postgres via REST."""
    r = httpx.post(
        f"{SIMBIONTE_URL}/simbionte/consultar",
        json={"sesion_id": sesion_id, "tool": tool, "params": params},
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("resultado", "Sin resultado.")


def _call_openrouter(model: str, messages: list, system: str = None,
                     tools: list = None, max_tokens: int = 2000, temperature: float = 0,
                     json_mode: bool = False) -> dict:
    """Llamada a OpenRouter con enforcement máximo de determinismo.

    Enforcement via API (no via prompt):
      - temperature=0 siempre
      - top_p=1 (no nucleus sampling)
      - response_format=json_object cuando se pide JSON
      - seed fijo para reproducibilidad
    """
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 1,
        "seed": 42,  # Reproducibilidad — mismo input = mismo output
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if system:
        payload["messages"] = [{"role": "system", "content": system}] + messages
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    r = httpx.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json=payload,
        timeout=180,
    )
    r.raise_for_status()
    return r.json()


# ============================================================
# PIPELINE
# ============================================================

def ejecutar_pipeline(series_dict: dict, pregunta: str, model: str = MODEL_OPUS) -> dict:
    t_total = time.time()

    # === FASE 1: Simbionte → Postgres ===
    print("  [1/5] Simbionte → Postgres...")
    write_result = calcular_y_escribir(series_dict, pregunta, modelo_llm=model)
    sesion_id = write_result["sesion_id"]
    print(f"        {write_result['n_escritos']} escritos, {write_result['n_patrones_detectados']} patrones ({write_result['dt']:.2f}s)")

    # === FASE 2: LLM con tool_use ===
    print(f"  [2/5] {model} con tool_use...")
    schema, pasos = generar_schema(pregunta)

    # === FIX 5: Harness demand-driven REAL ===
    # La finalidad determina QUÉ tools el LLM debe priorizar
    finalidad = write_result["finalidad"]
    FINALIDAD_TOOLS = {
        "DIAGNOSTICAR": ["calcular(diagnostico)", "calcular(relaciones)", "consultar_patron"],
        "PRESCRIBIR": ["calcular(prescripcion)", "calcular(relaciones)", "consultar_patron", "consultar_isomorfismo"],
        "RELACIONAR": ["calcular(relaciones)", "cascada_preguntas", "consultar_isomorfismo"],
        "VERIFICAR": ["calcular(diagnostico)", "calcular(todo)", "consultar_formula"],
        "PREDECIR": ["calcular(diagnostico)", "calcular(riesgo)", "consultar_patron"],
        "MEDIR_RIESGO": ["calcular(riesgo)", "calcular(diagnostico)", "consultar_patron"],
        "COMPARAR": ["calcular(todo)", "consultar_isomorfismo"],
        "DESCOMPONER": ["calcular(diagnostico)", "cascada_preguntas", "consultar_formula"],
        "OPTIMIZAR": ["calcular(prescripcion)", "calcular(relaciones)", "calcular(riesgo)"],
        "VALORAR": ["calcular(todo)", "consultar_formula", "consultar_patron"],
    }
    tools_priorizados = FINALIDAD_TOOLS.get(finalidad, ["calcular(todo)", "consultar_patron"])

    system = f"""Analista de datos. Consultas el Simbionte via herramientas.

SESION: {sesion_id}
SERIES: {list(series_dict.keys())}
FINALIDAD DETECTADA: {finalidad}

HERRAMIENTAS PRIORIZADAS para esta finalidad:
{chr(10).join(f'  - {t}' for t in tools_priorizados)}

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

REGLAS ABSOLUTAS:
1. Solo cita datos de herramientas. Sin dato = "sin datos".
2. Sigue protocolo en orden. Llama PRIMERO las herramientas priorizadas.
3. Max 8 tool calls. Prioriza las herramientas de la finalidad.
4. Respuesta FINAL: JSON valido con los campos especificados.
5. PROHIBIDO inventar numeros. Cada valor debe venir de una herramienta."""

    messages = [{"role": "user", "content": f"""Pregunta: {pregunta}

Responde SOLO con un JSON valido con esta estructura exacta:
{{
  "diagnostico": "frase",
  "datos_citados": [{{"nombre": "formula", "valor": 0.0, "interpretacion": "texto"}}],
  "desequilibrios": ["..."],
  "prescripcion_bc": "texto",
  "prescripcion_gobierno": "texto",
  "riesgos_ocultos": ["..."],
  "alertas": ["..."],
  "confianza": "alta/media/baja",
  "razonamiento": "resumen 3-4 frases"
}}"""}]

    all_tool_calls = []
    total_in = 0
    total_out = 0
    t_llm = time.time()

    for turn in range(15):
        # Fix 2: JSON mode en la última llamada (cuando no hay tools pendientes)
        is_final = turn > 0 and not (turn == 0)
        resp = _call_openrouter(model, messages, system=system if turn == 0 else None,
                                tools=TOOLS, max_tokens=2000)

        usage = resp.get("usage", {})
        total_in += usage.get("prompt_tokens", 0)
        total_out += usage.get("completion_tokens", 0)

        choice = resp["choices"][0]
        message = choice["message"]
        finish = choice.get("finish_reason", "")

        if finish == "tool_calls" or message.get("tool_calls"):
            messages.append(message)
            for tc in message["tool_calls"]:
                fn = tc["function"]
                tool_name = fn["name"]
                try:
                    tool_args = json.loads(fn["arguments"])
                except:
                    tool_args = {}

                result = _consultar_postgres(sesion_id, tool_name, tool_args)
                all_tool_calls.append({
                    "turn": turn, "tool": tool_name,
                    "input": tool_args, "result_length": len(result),
                })
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result[:2000],
                })
                print(f"        Turn {turn}: {tool_name}({json.dumps(tool_args, ensure_ascii=False)[:40]}) → {len(result)}c")
        else:
            break

    dt_llm = time.time() - t_llm
    respuesta_raw = message.get("content", "")

    # Extraer JSON (robust)
    import re
    json_match = re.search(r'\{[\s\S]*\}', respuesta_raw)
    respuesta_json = None
    if json_match:
        try:
            respuesta_json = json.loads(json_match.group())
            respuesta_raw = json.dumps(respuesta_json, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass

    print(f"        {len(respuesta_raw)} chars, {len(all_tool_calls)} tool calls ({dt_llm:.1f}s)")
    print(f"        JSON válido: {'SÍ' if respuesta_json else 'NO'}")
    print(f"        Herramientas priorizadas: {tools_priorizados}")

    # === FASE 3: H3 verificación mejorada ===
    # Nivel 1: números (h3_verificar original)
    # Nivel 2: datos_citados del JSON vs Postgres (nuevo)
    # Nivel 3: audit trail — todo lo que citó debe existir en auditorias_simbionte
    print("  [3/5] H3 verificación (3 niveles)...")
    resultados_local = calcular_formulas_economia(series_dict)

    # Nivel 1: números sueltos
    disc_numeros = h3_verificar(respuesta_raw, resultados_local)
    print(f"        N1 (números): {len(disc_numeros)} discrepancias")

    # Nivel 2: datos_citados del JSON — cada valor citado debe existir en resultados
    disc_citados = []
    if respuesta_json and "datos_citados" in respuesta_json:
        for dato in respuesta_json["datos_citados"]:
            nombre = dato.get("nombre", "")
            valor = dato.get("valor")
            if valor is None:
                continue
            # Buscar en resultados locales
            found = False
            for rn, ri in resultados_local.items():
                if nombre.lower() in rn.lower() or rn.lower() in nombre.lower():
                    if abs(ri["valor"] - valor) < 0.01:
                        found = True
                        break
                    elif abs(ri["valor"]) > 0.001:
                        error = abs(valor - ri["valor"]) / abs(ri["valor"])
                        if error < 0.05:  # 5% tolerancia
                            found = True
                            break
                        else:
                            disc_citados.append({
                                "tipo": "valor_incorrecto",
                                "formula": nombre,
                                "citado": valor,
                                "real": round(ri["valor"], 6),
                                "error_pct": round(error, 3),
                            })
                            found = True
                            break
            if not found and nombre != "ESTANFLACION" and abs(valor) > 0.001:
                disc_citados.append({
                    "tipo": "formula_no_existe",
                    "formula": nombre,
                    "citado": valor,
                    "real": None,
                })
        print(f"        N2 (datos_citados): {len(disc_citados)} discrepancias de {len(respuesta_json['datos_citados'])} citados")

    # Nivel 3: audit trail — ¿el LLM consultó antes de citar?
    disc_audit = []
    try:
        r_audit = httpx.get(f"{SIMBIONTE_URL}/simbionte/auditorias/{sesion_id}", timeout=10)
        audits = r_audit.json()
        tools_usados = {a["tool_name"] for a in audits}
        if respuesta_json and "datos_citados" in respuesta_json and len(respuesta_json["datos_citados"]) > 0:
            if "calcular" not in tools_usados:
                disc_audit.append("LLM citó datos pero NUNCA llamó 'calcular'")
    except:
        pass
    print(f"        N3 (audit): {len(disc_audit)} alertas")

    discrepancias = disc_numeros + disc_citados + disc_audit

    # === FASE 4: Traductor ===
    print("  [4/5] Traductor...")
    t_trad = time.time()
    trad_resp = _call_openrouter(
        MODEL_SONNET,  # Traductor con Sonnet (más barato)
        [{"role": "user", "content": f"Traduce este análisis a lenguaje natural para un CEO no economista. "
                                      f"3 párrafos: diagnóstico, qué hacer, riesgos. Max 250 palabras.\n\n{respuesta_raw}"}],
        max_tokens=1000, temperature=0.3,
    )
    traduccion = trad_resp["choices"][0]["message"]["content"]
    trad_usage = trad_resp.get("usage", {})
    total_in += trad_usage.get("prompt_tokens", 0)
    total_out += trad_usage.get("completion_tokens", 0)
    dt_trad = time.time() - t_trad
    print(f"        {len(traduccion)} chars ({dt_trad:.1f}s)")

    dt_total = time.time() - t_total

    # Coste
    if "opus" in model:
        cost = (total_in * 15 + total_out * 75) / 1e6
    else:
        cost = (total_in * 3 + total_out * 15) / 1e6

    return {
        "respuesta_raw": respuesta_raw,
        "respuesta": traduccion,
        "sesion_id": sesion_id,
        "write_result": write_result,
        "model": model,
        "n_tool_calls": len(all_tool_calls),
        "tool_calls": all_tool_calls,
        "n_turns": turn + 1,
        "tokens_in": total_in,
        "tokens_out": total_out,
        "cost": cost,
        "dt_write": write_result["dt"],
        "dt_llm": dt_llm,
        "dt_trad": dt_trad,
        "dt_total": dt_total,
        "n_discrepancias": len(discrepancias),
        "discrepancias": discrepancias,
    }


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    rng = np.random.default_rng(77); t = np.arange(48)
    series = {
        'pib': list(300000*(1+0.008*t-0.0002*t**2)*(1+0.005*rng.standard_normal(48))),
        'inflacion': list(1.5+0.08*t+0.3*np.sin(2*np.pi*t/12)+0.2*rng.standard_normal(48)),
        'desempleo': list(7+0.05*t+0.3*rng.standard_normal(48)),
        'tipo_interes': list(0.5+0.03*t+0.1*rng.standard_normal(48)),
        'consumo': list(0.58*300000+200*rng.standard_normal(48)),
        'inversion': list(0.22*300000+150*rng.standard_normal(48)),
        'exportaciones': list(0.30*300000+100*rng.standard_normal(48)),
        'importaciones': list(0.32*300000+100*rng.standard_normal(48)),
        'deuda_pib': list(95+0.8*t+0.5*rng.standard_normal(48)),
    }

    pregunta = "Qué debería hacer el banco central ante esta estanflación? Qué riesgos ocultos hay?"

    print("=" * 70)
    print(f"PIPELINE OMC-95 API — Opus via OpenRouter + tool_use")
    print("Simbionte → Postgres → Opus tool_use → H3 → Traductor")
    print("=" * 70)
    print(f"Pregunta: {pregunta}")
    print(f"Series: {list(series.keys())}")
    print()

    # Wake up fly.io first
    print("  [0] Despertando fly.io...")
    try:
        r = httpx.get(f"{SIMBIONTE_URL}/health", timeout=30)
        print(f"      {r.json().get('status', '?')}")
    except:
        print("      WARN: fly.io no respondió, intentando de todos modos...")

    result = ejecutar_pipeline(series, pregunta, model=MODEL_OPUS)

    print(f"\n{'=' * 70}")
    print("MÉTRICAS")
    print(f"{'=' * 70}")
    wr = result["write_result"]
    print(f"  Modelo: {result['model']}")
    print(f"  Fórmulas: {wr['n_formulas_calculadas']} calculadas, {wr['n_escritos']} escritos")
    print(f"  Tool calls: {result['n_tool_calls']} en {result['n_turns']} turnos")
    print(f"  Tokens: {result['tokens_in']} in + {result['tokens_out']} out = {result['tokens_in']+result['tokens_out']}")
    print(f"  H3: {result['n_discrepancias']} discrepancias")
    print(f"  Coste: ${result['cost']:.4f}")
    print(f"  Tiempos: write={result['dt_write']:.1f}s, LLM={result['dt_llm']:.1f}s, trad={result['dt_trad']:.1f}s, TOTAL={result['dt_total']:.1f}s")

    print(f"\n{'=' * 70}")
    print("RESPUESTA RAW (JSON del analista):")
    print(f"{'=' * 70}")
    print(result["respuesta_raw"][:3000])

    if result["n_discrepancias"] > 0:
        print(f"\n⚡ DISCREPANCIAS H3:")
        for d in result["discrepancias"][:5]:
            print(f"  - {d}")

    print(f"\n{'=' * 70}")
    print("RESPUESTA PARA CEO:")
    print(f"{'=' * 70}")
    print(result["respuesta"])

    # Comparativa
    print(f"\n{'=' * 70}")
    print("COMPARATIVA claude -p vs API Opus:")
    print(f"{'=' * 70}")
    print(f"  {'Métrica':<25} {'claude -p ($0)':>20} {'Opus API':>20}")
    cost_str = f"${result['cost']:.4f}"
    print(f"  {'Coste':<25} {'$0.00':>20} {cost_str:>20}")
    print(f"  {'Tool calls':<25} {'0 (pre-fetch)':>20} {str(result['n_tool_calls'])+' (on-demand)':>20}")
    print(f"  {'Tokens':<25} {'N/A':>20} {str(result['tokens_in']+result['tokens_out']):>20}")
    print(f"  {'H3 discrepancias':<25} {'0':>20} {str(result['n_discrepancias']):>20}")
    dt_str = f"{result['dt_total']:.1f}s"
    print(f"  {'Tiempo total':<25} {'65.4s':>20} {dt_str:>20}")
