"""
Agente Analista — LLM con tool_use que sigue protocolo y consulta pgvector.

Fecha: 2026-04-13

ARQUITECTURA:
  El LLM recibe un PROTOCOLO (schema corto ~500 tokens).
  En cada paso del protocolo, LLAMA A HERRAMIENTAS:
    - consultar_formula(nombre) → semántica completa de pgvector
    - consultar_patron(señales) → patrón histórico de pgvector
    - calcular(formulas, datos) → ejecuta fórmulas del Simbionte

  El LLM NO recibe todo el contexto de golpe.
  CONSULTA lo que necesita, cuando lo necesita.

  Esto reduce tokens de ~4000 (inyectado) a ~500 (schema) + N consultas de ~200 tokens cada una.
"""

import sys, os, json, time, numpy as np
sys.path.insert(0, os.path.dirname(__file__))

from protocolo_analista import generar_schema
from clasificador_economia import calcular_formulas_economia
from semantica_formulas import SEMANTICA, razonamiento_a_texto
from pipeline_completo import (
    harness_seleccionar, pgvector_buscar, pgvector_a_texto,
    h3_verificar, ISOMORFISMOS_CATALOGO
)
from red_preguntas import cascada, cascada_a_texto, ENLACES
from decodificador_economia import clasificar_nivel
from catalogo_finalidades import detectar_finalidad
from collections import defaultdict


# ============================================================
# HERRAMIENTAS (tools) que el LLM puede llamar
# ============================================================

TOOLS = [
    {
        "name": "consultar_formula",
        "description": "Busca la semántica completa de una fórmula en el catálogo. "
                       "Devuelve: polos (eje semántico), presupuestos (lo que asume sin decirlo), "
                       "razonamiento paso a paso, y la pregunta que responde. "
                       "Usa esto para entender QUÉ SIGNIFICA un valor calculado.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre de la fórmula. Ej: 'varianza', 'correlacion', 'output_gap', 'marco_amplificacion'"
                }
            },
            "required": ["nombre"]
        }
    },
    {
        "name": "consultar_patron",
        "description": "Busca patrones históricos que coincidan con las señales actuales. "
                       "Devuelve: nombre del patrón, descripción, precedentes históricos, "
                       "y prescripción que funcionó en el pasado. "
                       "Usa esto para saber si la situación actual se parece a algo conocido.",
        "input_schema": {
            "type": "object",
            "properties": {
                "senales": {
                    "type": "string",
                    "description": "Descripción de las señales clave. Ej: 'inflación alta, desempleo alto, PIB estancado'"
                }
            },
            "required": ["senales"]
        }
    },
    {
        "name": "calcular",
        "description": "Ejecuta fórmulas del Simbionte sobre los datos disponibles. "
                       "Devuelve: valor calculado + clasificación (alto/bajo/normal) + texto legible. "
                       "Usa esto para obtener valores numéricos que fundamenten tu análisis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "description": "Tipo de fórmulas a calcular. Opciones: "
                                   "'diagnostico' (varianza, gaps, persistencia), "
                                   "'relaciones' (correlaciones, elasticidades), "
                                   "'riesgo' (VaR, feedback, fragilidad), "
                                   "'prescripcion' (multiplicadores, Taylor), "
                                   "'todo' (todas las fórmulas)"
                }
            },
            "required": ["tipo"]
        }
    },
    {
        "name": "cascada_preguntas",
        "description": "Dado un resultado, muestra qué preguntas se desbloquean. "
                       "La respuesta de una fórmula activa nuevas preguntas en cadena. "
                       "Usa esto para saber qué analizar DESPUÉS de un hallazgo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "formula": {
                    "type": "string",
                    "description": "Nombre de la fórmula cuyo resultado quieres encadenar"
                },
                "valor": {
                    "type": "string",
                    "description": "'alto', 'bajo', o 'extremo'"
                }
            },
            "required": ["formula", "valor"]
        }
    },
]


# ============================================================
# EJECUTORES DE HERRAMIENTAS
# ============================================================

# Estado global del agente (datos cargados)
_datos_agente = {}
_resultados_cache = {}


def ejecutar_consultar_formula(nombre):
    """Busca semántica de una fórmula."""
    # Buscar en catálogo local primero
    sem = SEMANTICA.get(nombre)
    if sem:
        texto = razonamiento_a_texto(nombre)
        if texto:
            return texto
        # Fallback: construir desde semántica
        polos = sem.get("polos", ("?", "?"))
        return (f"**{nombre}** — {sem.get('pregunta', '?')}\n"
                f"Eje: {polos[0]} ↔ {polos[1]}\n"
                f"Presupuestos: {'; '.join(sem.get('presupuestos', []))}\n"
                f"Si alto: {sem.get('si_alto', '?')}\n"
                f"Si bajo: {sem.get('si_bajo', '?')}")

    # Buscar en pgvector (fly.io)
    try:
        import httpx
        r = httpx.post(
            "https://motor-semantico-omni.fly.dev/conocimiento-proyecto/query",
            json={"query": f"Formula {nombre}", "top_k": 1},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("conocimiento"):
                return data["conocimiento"][0]["contenido"]
    except:
        pass

    return f"Fórmula '{nombre}' no encontrada en el catálogo."


def ejecutar_consultar_patron(señales):
    """Busca patrones históricos."""
    # Local primero
    resultados = _resultados_cache or {}
    matches = pgvector_buscar(resultados)
    if matches:
        return pgvector_a_texto(matches)

    # pgvector remoto
    try:
        import httpx
        r = httpx.post(
            "https://motor-semantico-omni.fly.dev/conocimiento-proyecto/query",
            json={"query": f"patrón histórico {señales}", "top_k": 3, "tipo": "patron_validado"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            if data.get("conocimiento"):
                return "\n\n".join(c["contenido"] for c in data["conocimiento"])
    except:
        pass

    return "Sin patrones históricos encontrados."


def ejecutar_calcular(tipo):
    """Calcula fórmulas del Simbionte."""
    global _resultados_cache
    datos = _datos_agente

    if not datos:
        return "Error: no hay datos cargados."

    if not _resultados_cache:
        _resultados_cache = calcular_formulas_economia(datos)

    resultados = _resultados_cache

    # Filtrar por tipo
    if tipo == "diagnostico":
        tipos_filtro = {"nivel", "tasa_cambio", "tasa_crecimiento", "varianza", "coef_variacion",
                        "gap", "persistencia", "aceleracion"}
    elif tipo == "relaciones":
        tipos_filtro = {"correlacion", "elasticidad"}
    elif tipo == "riesgo":
        tipos_filtro = {"varianza", "coef_variacion", "persistencia", "aceleracion"}
    elif tipo == "prescripcion":
        tipos_filtro = {"elasticidad", "correlacion", "gap", "tasa_crecimiento"}
    else:
        tipos_filtro = None

    sel = harness_seleccionar(resultados, 20)
    lines = []
    for n, info, score, reason, ni, nt in sel:
        if tipos_filtro and info["tipo"] not in tipos_filtro:
            continue
        v = info["valor"]; sg = "+" if v >= 0 else ""
        lines.append(f"{n}: {sg}{v:.4f} → {nt} ({info['texto']})")

    return "\n".join(lines[:15]) if lines else "Sin resultados para este tipo."


def ejecutar_cascada_preguntas(formula, valor):
    """Muestra preguntas encadenadas."""
    if formula in ENLACES:
        links = ENLACES[formula]
        lines = [f"Desde {formula} ({valor}):"]
        for cond, destino, razon in links:
            if cond == valor or cond == "siempre":
                sem = SEMANTICA.get(destino, {})
                pregunta = sem.get("pregunta", "?")
                lines.append(f"  → {destino}: {pregunta}")
                lines.append(f"    Razón: {razon}")
        return "\n".join(lines) if len(lines) > 1 else f"Sin preguntas encadenadas para {formula} ({valor})."
    return f"Fórmula '{formula}' no tiene enlaces en la red de preguntas."


def ejecutar_tool(nombre_tool, input_data):
    """Dispatcher de herramientas."""
    if nombre_tool == "consultar_formula":
        return ejecutar_consultar_formula(input_data.get("nombre", ""))
    elif nombre_tool == "consultar_patron":
        return ejecutar_consultar_patron(input_data.get("senales", ""))
    elif nombre_tool == "calcular":
        return ejecutar_calcular(input_data.get("tipo", "todo"))
    elif nombre_tool == "cascada_preguntas":
        return ejecutar_cascada_preguntas(input_data.get("formula", ""), input_data.get("valor", "alto"))
    return f"Herramienta '{nombre_tool}' no reconocida."


# ============================================================
# LOOP DEL AGENTE
# ============================================================

def ejecutar_agente(series_dict, pregunta, client, model="claude-sonnet-4-20250514", max_turns=8):
    """Ejecuta el agente analista con tool_use.

    El LLM recibe el protocolo y puede llamar herramientas en cada paso.
    """
    global _datos_agente, _resultados_cache
    _datos_agente = series_dict
    _resultados_cache = {}

    # Generar schema compacto
    schema, pasos = generar_schema(pregunta)

    system = f"""Eres un analista de datos que sigue un protocolo riguroso.

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

REGLAS:
- Sigue los pasos EN ORDEN.
- En CADA paso, usa las herramientas para obtener datos. NO inventes.
- consultar_formula: para entender qué significa un valor
- consultar_patron: para buscar precedentes históricos
- calcular: para obtener valores del Simbionte
- cascada_preguntas: para saber qué analizar después de un hallazgo
- Marca [VERIFICADO] cuando la estructura confirma tu análisis semántico.
- Marca ⚡ ALERTA cuando hay contradicción.
- Máximo 400 palabras en la respuesta final."""

    messages = [{"role": "user", "content": f"Datos disponibles: {list(series_dict.keys())}\n\nPregunta: {pregunta}"}]

    all_tool_calls = []
    total_tokens_in = 0
    total_tokens_out = 0
    t0 = time.time()

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

        # Procesar respuesta
        if response.stop_reason == "end_turn":
            # El LLM terminó — extraer texto final
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            break

        elif response.stop_reason == "tool_use":
            # El LLM quiere usar una herramienta
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    # Ejecutar herramienta
                    result = ejecutar_tool(tool_name, tool_input)
                    all_tool_calls.append({
                        "turn": turn,
                        "tool": tool_name,
                        "input": tool_input,
                        "result_length": len(result),
                    })

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result[:2000],  # Limitar para no explotar contexto
                    })

            messages.append({"role": "user", "content": tool_results})
        else:
            # Otro stop reason
            final_text = str(response.content)
            break
    else:
        # Max turns reached
        final_text = "Máximo de turnos alcanzado."
        for block in response.content:
            if hasattr(block, "text"):
                final_text = block.text
                break

    dt = time.time() - t0

    # Coste
    if "opus" in model:
        cost = (total_tokens_in * 15 + total_tokens_out * 75) / 1e6
    else:
        cost = (total_tokens_in * 3 + total_tokens_out * 15) / 1e6

    # H3 verificación
    resultados = _resultados_cache or calcular_formulas_economia(series_dict)
    discrepancias = h3_verificar(final_text, resultados)

    return {
        "respuesta": final_text,
        "n_tool_calls": len(all_tool_calls),
        "tool_calls": all_tool_calls,
        "n_turns": turn + 1,
        "tokens_in": total_tokens_in,
        "tokens_out": total_tokens_out,
        "cost": cost,
        "dt": dt,
        "system_chars": len(system),
        "n_discrepancias": len(discrepancias),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv("../../.env")
    import anthropic

    key = os.getenv("ANTHROPIC_API_KEY_1")
    if not key:
        # Try parent
        load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))
        key = os.getenv("ANTHROPIC_API_KEY_1")

    client = anthropic.Anthropic(api_key=key)

    # Datos estanflación
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

    print("="*70)
    print("AGENTE ANALISTA — Tool Use Test")
    print("="*70)

    result = ejecutar_agente(
        series,
        "¿Qué debería hacer el banco central ante esta estanflación? ¿Qué riesgos ocultos hay?",
        client
    )

    print(f"\n  Turnos: {result['n_turns']}")
    print(f"  Tool calls: {result['n_tool_calls']}")
    for tc in result['tool_calls']:
        print(f"    Turn {tc['turn']}: {tc['tool']}({json.dumps(tc['input'])[:60]}) → {tc['result_length']}c")
    print(f"  Tokens: {result['tokens_in']} in + {result['tokens_out']} out")
    print(f"  System: {result['system_chars']} chars")
    print(f"  Coste: ${result['cost']:.4f}")
    print(f"  Tiempo: {result['dt']:.0f}s")
    print(f"  H3: {result['n_discrepancias']} discrepancias")

    print(f"\n{'='*70}")
    print("RESPUESTA:")
    print(f"{'='*70}")
    print(result["respuesta"])
