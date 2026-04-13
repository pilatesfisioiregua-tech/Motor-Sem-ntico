"""
OMC-95: Agente Analista v2 — LLM consulta Postgres via tool_use (0 inyeccion).

ANTES (agente_analista.py):
  - Simbionte calcula en memoria
  - Resultados se inyectan en el prompt (~4000 tokens/paso)
  - System prompt: ~2000 tokens

AHORA (agente_postgres.py):
  - Simbionte calcula y ESCRIBE en Postgres (simbionte_writer.py)
  - LLM recibe SOLO protocolo (~500 tokens)
  - LLM consulta Postgres via tool_use (on-demand)
  - Cada consulta: ~200 tokens de respuesta
  - Total estimado: 8-15K tokens (vs 40-60K antes)

Coste estimado: ~60-75% menos por analisis.
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

import httpx
from protocolo_analista import generar_schema
from simbionte_writer import calcular_y_escribir

SIMBIONTE_URL = os.getenv("SIMBIONTE_URL", "https://motor-semantico-omni.fly.dev")


# ============================================================
# HERRAMIENTAS — ahora consultan Postgres via REST
# ============================================================

TOOLS = [
    {
        "name": "consultar_formula",
        "description": "Busca la semantica completa de una formula en Postgres. "
                       "Devuelve: polos (eje semantico), presupuestos, razonamiento, "
                       "valor calculado y clasificacion. "
                       "Usa esto para entender QUE SIGNIFICA un valor.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre de la formula. Ej: 'varianza', 'correlacion', 'output_gap'"
                }
            },
            "required": ["nombre"]
        }
    },
    {
        "name": "consultar_patron",
        "description": "Busca patrones historicos que coincidan con las senales actuales. "
                       "Devuelve: patron, precedentes, prescripcion. "
                       "Usa esto para saber si la situacion se parece a algo conocido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "senales": {
                    "type": "string",
                    "description": "Senales clave. Ej: 'inflacion alta, desempleo alto, PIB estancado'"
                }
            },
            "required": ["senales"]
        }
    },
    {
        "name": "calcular",
        "description": "Consulta resultados del Simbionte por tipo. "
                       "Devuelve: valores calculados + clasificacion + texto legible. "
                       "Usa esto para obtener valores numericos que fundamenten tu analisis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "description": "Tipo: 'diagnostico', 'relaciones', 'riesgo', 'prescripcion', 'todo'"
                }
            },
            "required": ["tipo"]
        }
    },
    {
        "name": "cascada_preguntas",
        "description": "Dado un resultado, muestra que preguntas se desbloquean en cadena. "
                       "Usa esto para saber que analizar DESPUES de un hallazgo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "formula": {"type": "string", "description": "Nombre de la formula"},
                "valor": {"type": "string", "description": "'alto', 'bajo', o 'extremo'"}
            },
            "required": ["formula", "valor"]
        }
    },
]


def _consultar_postgres(sesion_id: str, tool: str, params: dict) -> str:
    """Consulta Postgres via REST endpoint."""
    try:
        r = httpx.post(
            f"{SIMBIONTE_URL}/simbionte/consultar",
            json={"sesion_id": sesion_id, "tool": tool, "params": params},
            timeout=15,
        )
        r.raise_for_status()
        return r.json().get("resultado", "Sin resultado.")
    except Exception as e:
        return f"Error consultando Postgres: {e}"


def ejecutar_tool(sesion_id: str, tool_name: str, input_data: dict) -> str:
    """Dispatcher — todas las tools consultan Postgres."""
    return _consultar_postgres(sesion_id, tool_name, input_data)


# ============================================================
# LOOP DEL AGENTE
# ============================================================

def ejecutar_agente(series_dict: dict, pregunta: str, client, model: str = "claude-sonnet-4-20250514", max_turns: int = 15) -> dict:
    """Ejecuta el agente analista OMC-95.

    1. Simbionte calcula y escribe en Postgres
    2. LLM recibe protocolo (~500 tokens)
    3. LLM consulta Postgres via tool_use (on-demand)
    4. H3 verificacion
    5. Traductor
    """
    # === PASO 1: Simbionte → Postgres ===
    write_result = calcular_y_escribir(series_dict, pregunta, modelo_llm=model)
    sesion_id = write_result["sesion_id"]

    # === PASO 2: Generar protocolo compacto ===
    schema, pasos = generar_schema(pregunta)

    system = f"""Eres un analista de datos ENJAULADO. Sigues un protocolo estricto y SOLO puedes usar datos de las herramientas.

SESION: {sesion_id}
DATOS DISPONIBLES: {list(series_dict.keys())}
FORMULAS CALCULADAS: {write_result['n_formulas_calculadas']}
PATRONES DETECTADOS: {write_result['n_patrones_detectados']}
FINALIDAD: {write_result['finalidad']}

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

=== JAULA: RESTRICCIONES ABSOLUTAS ===

1. DATOS: Solo cita valores de las herramientas. Si no viene de una herramienta, di "sin datos".
2. PROTOCOLO: Sigue los pasos EN ORDEN. En CADA paso, llama herramientas y escribe "PASO N CONCLUSION: [hallazgo]".
3. VOCABULARIO: [VERIFICADO], [SUPOSICION], ALERTA, [SIN DATOS].
4. FORMATO FINAL (ultimo paso): JSON con diagnostico, desequilibrios, prescripcion_bc, prescripcion_gobierno, riesgos_ocultos, alertas, confianza, datos_clave.
5. PROHIBIDO: citar % sin "calcular", teorias sin "consultar_formula", precedentes sin "consultar_patron".
6. CIERRE: Maximo 8 llamadas a herramientas, despues sintetiza con lo que tienes."""

    messages = [{"role": "user", "content": f"Pregunta: {pregunta}"}]

    all_tool_calls = []
    total_tokens_in = 0
    total_tokens_out = 0
    t0 = time.time()
    final_text = ""

    for turn in range(max_turns):
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            temperature=0,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        total_tokens_in += response.usage.input_tokens
        total_tokens_out += response.usage.output_tokens

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            break

        elif response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = ejecutar_tool(sesion_id, block.name, block.input)
                    all_tool_calls.append({
                        "turn": turn,
                        "tool": block.name,
                        "input": block.input,
                        "result_length": len(result),
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result[:2000],
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            final_text = str(response.content)
            break
    else:
        final_text = "Maximo de turnos alcanzado."
        for block in response.content:
            if hasattr(block, "text"):
                final_text = block.text
                break

    dt_agente = time.time() - t0

    # === H3 verificacion ===
    from pipeline_completo import h3_verificar
    from clasificador_economia import calcular_formulas_economia
    resultados_local = calcular_formulas_economia(series_dict)
    discrepancias = h3_verificar(final_text, resultados_local)

    # === TRADUCTOR ===
    t_trad = time.time()
    try:
        traductor_response = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.3,
            system="Eres un traductor. Recibes analisis tecnico (JSON o texto con datos). "
                   "Traduce a lenguaje natural claro para un CEO no economista. "
                   "REGLAS: No inventes datos. Solo traduce lo que recibes. "
                   "Estructura: 1 parrafo diagnostico, 1 de que hacer, 1 de riesgos. Max 250 palabras.",
            messages=[{"role": "user", "content": f"Traduce:\n\n{final_text}"}],
        )
        traduccion = traductor_response.content[0].text
        total_tokens_in += traductor_response.usage.input_tokens
        total_tokens_out += traductor_response.usage.output_tokens
    except Exception as e:
        traduccion = final_text

    dt_total = time.time() - t0

    # Coste
    if "opus" in model:
        cost = (total_tokens_in * 15 + total_tokens_out * 75) / 1e6
    elif "sonnet" in model:
        cost = (total_tokens_in * 3 + total_tokens_out * 15) / 1e6
    else:
        cost = (total_tokens_in * 3 + total_tokens_out * 15) / 1e6

    return {
        "respuesta_raw": final_text,
        "respuesta": traduccion,
        "sesion_id": sesion_id,
        "write_result": write_result,
        "n_tool_calls": len(all_tool_calls),
        "tool_calls": all_tool_calls,
        "n_turns": turn + 1,
        "tokens_in": total_tokens_in,
        "tokens_out": total_tokens_out,
        "system_chars": len(system),
        "cost": cost,
        "dt_write": write_result["dt"],
        "dt_agente": dt_agente,
        "dt_total": dt_total,
        "n_discrepancias": len(discrepancias),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import numpy as np
    from dotenv import load_dotenv
    load_dotenv("../../.env")
    import anthropic

    key = os.getenv("ANTHROPIC_API_KEY_1")
    if not key:
        load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
        key = os.getenv("ANTHROPIC_API_KEY_1")

    client = anthropic.Anthropic(api_key=key)

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

    print("=" * 70)
    print("AGENTE OMC-95 — Simbionte -> Postgres -> tool_use")
    print("=" * 70)

    result = ejecutar_agente(
        series,
        "Que deberia hacer el banco central ante esta estanflacion? Que riesgos ocultos hay?",
        client,
        model="claude-sonnet-4-20250514",
    )

    print(f"\n  Sesion ID: {result['sesion_id']}")
    print(f"  Escritura: {result['write_result']['n_escritos']} resultados en {result['dt_write']:.1f}s")
    print(f"  Turnos LLM: {result['n_turns']}")
    print(f"  Tool calls: {result['n_tool_calls']}")
    for tc in result['tool_calls']:
        print(f"    Turn {tc['turn']}: {tc['tool']}({json.dumps(tc['input'])[:60]}) -> {tc['result_length']}c")
    print(f"  System prompt: {result['system_chars']} chars")
    print(f"  Tokens: {result['tokens_in']} in + {result['tokens_out']} out")
    print(f"  Coste: ${result['cost']:.4f}")
    print(f"  Tiempo total: {result['dt_total']:.0f}s")
    print(f"  H3 discrepancias: {result['n_discrepancias']}")

    print(f"\n{'=' * 70}")
    print("RESPUESTA TRADUCIDA:")
    print(f"{'=' * 70}")
    print(result["respuesta"])

    # Comparar con agente v1
    print(f"\n{'=' * 70}")
    print("COMPARATIVA vs AGENTE v1 (inyeccion directa):")
    print(f"{'=' * 70}")
    print(f"  System prompt: {result['system_chars']} chars (v1: ~2000+ chars)")
    print(f"  Tokens totales: {result['tokens_in'] + result['tokens_out']} (v1: ~40-60K)")
    print(f"  Tool calls a Postgres: {result['n_tool_calls']} (v1: local, no auditable)")
    print(f"  Datos persistidos: SI (v1: NO)")
    print(f"  Auditable: SI (v1: NO)")
