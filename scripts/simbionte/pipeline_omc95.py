"""
OMC-95 Pipeline Completo — Simbionte → Postgres → claude -p → respuesta.

FLUJO:
  1. Simbionte calcula fórmulas sobre datos ($0, local)
  2. Escribe resultados en Postgres via REST ($0, fly.io)
  3. Harness demand-driven: pregunta → finalidad → selecciona fórmulas relevantes
  4. Consulta Postgres para obtener contexto compacto
  5. claude -p con system prompt + JSON schema ($0, Max Plan)
  6. H3 verificación ($0, local)
  7. Traductor via claude -p ($0, Max Plan)

COSTE TOTAL: $0

VENTAJAS vs API tool_use:
  - $0 vs ~$0.10-0.30 por análisis
  - MÁS determinista (1 llamada vs multi-turn)
  - Datos persistidos en Postgres (auditable)
  - Harness pre-filtra → LLM recibe solo lo relevante
"""

import sys, os, json, time, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from simbionte_writer import calcular_y_escribir
from protocolo_analista import generar_schema
from clasificador_economia import calcular_formulas_economia
from pipeline_completo import h3_verificar

import httpx

SIMBIONTE_URL = os.getenv("SIMBIONTE_URL", "https://motor-semantico-omni.fly.dev")
CLAUDE_CMD = os.getenv("CLAUDE_CMD", "claude")


# ============================================================
# HARNESS: consulta Postgres y construye contexto compacto
# ============================================================

def harness_consultar_postgres(sesion_id: str, finalidad: str) -> dict:
    """Consulta Postgres y devuelve contexto compacto para el LLM.

    El harness decide QUÉ consultar basándose en la finalidad detectada.
    """
    url = SIMBIONTE_URL
    contexto = {}

    # 1. Datos de diagnóstico (siempre)
    r = httpx.post(f"{url}/simbionte/consultar", json={
        "sesion_id": sesion_id, "tool": "calcular", "params": {"tipo": "diagnostico"}
    }, timeout=15)
    contexto["diagnostico"] = r.json().get("resultado", "Sin datos.")

    # 2. Relaciones (si finalidad incluye RELACIONAR, PRESCRIBIR, DIAGNOSTICAR)
    r = httpx.post(f"{url}/simbionte/consultar", json={
        "sesion_id": sesion_id, "tool": "calcular", "params": {"tipo": "relaciones"}
    }, timeout=15)
    contexto["relaciones"] = r.json().get("resultado", "Sin datos.")

    # 3. Patrones históricos (siempre)
    r = httpx.post(f"{url}/simbionte/consultar", json={
        "sesion_id": sesion_id, "tool": "consultar_patron",
        "params": {"senales": "patron historico"}
    }, timeout=15)
    contexto["patrones"] = r.json().get("resultado", "Sin datos.")

    # 4. Riesgo (si finalidad incluye PRESCRIBIR, MEDIR_RIESGO)
    if finalidad in ("PRESCRIBIR", "MEDIR_RIESGO", "DIAGNOSTICAR"):
        r = httpx.post(f"{url}/simbionte/consultar", json={
            "sesion_id": sesion_id, "tool": "calcular", "params": {"tipo": "riesgo"}
        }, timeout=15)
        contexto["riesgo"] = r.json().get("resultado", "Sin datos.")

    # 5. Top resultados (siempre — vista panorámica)
    r = httpx.post(f"{url}/simbionte/consultar", json={
        "sesion_id": sesion_id, "tool": "calcular", "params": {"tipo": "todo"}
    }, timeout=15)
    contexto["panoramica"] = r.json().get("resultado", "Sin datos.")

    return contexto


def construir_prompt(pregunta: str, contexto: dict, pasos: list) -> str:
    """Construye el prompt compacto para claude -p."""
    secciones = []
    for clave, datos in contexto.items():
        if datos and datos != "Sin datos." and datos != "Sin resultados para tipo 'riesgo'.":
            secciones.append(f"=== {clave.upper()} ===\n{datos}")

    datos_texto = "\n\n".join(secciones)

    prompt = f"""PREGUNTA DEL USUARIO:
{pregunta}

DATOS DEL SIMBIONTE (calculados sobre las series temporales):
{datos_texto}

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

Analiza los datos del Simbionte siguiendo el protocolo. Para CADA paso, cita datos específicos.
Al final, produce el JSON de respuesta."""

    return prompt


def llamar_claude_p(system: str, prompt: str, json_schema: dict = None) -> tuple:
    """Llama a claude -p y devuelve (texto, tiempo)."""
    t0 = time.time()

    # Combinar system + prompt en un solo input para claude -p
    full_input = f"""INSTRUCCIONES DEL SISTEMA:
{system}

---

{prompt}"""

    cmd = [CLAUDE_CMD, "-p"]
    if json_schema:
        cmd.extend(["--output-format", "json"])

    # Bypass nested session check + clean env
    env = {k: v for k, v in os.environ.items()}
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            cmd,
            input=full_input,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        output = result.stdout.strip()
        if not output and result.stderr:
            output = f"[ERROR claude -p]: {result.stderr[:500]}"
        dt = time.time() - t0
        return output, dt
    except subprocess.TimeoutExpired:
        return "TIMEOUT: claude -p tardó más de 300s", time.time() - t0


# ============================================================
# PIPELINE COMPLETO
# ============================================================

def ejecutar_pipeline(series_dict: dict, pregunta: str) -> dict:
    """Pipeline OMC-95 completo.

    1. Simbionte → Postgres
    2. Harness → consulta Postgres
    3. claude -p → análisis
    4. H3 → verificación
    5. claude -p → traducción
    """
    t_total = time.time()

    # === FASE 1: SIMBIONTE → POSTGRES ===
    print("  [1/5] Simbionte calculando y escribiendo en Postgres...")
    write_result = calcular_y_escribir(series_dict, pregunta, modelo_llm="claude-p-maxplan")
    sesion_id = write_result["sesion_id"]
    print(f"        {write_result['n_escritos']} resultados escritos ({write_result['dt']:.2f}s)")

    # === FASE 2: HARNESS → CONSULTA POSTGRES ===
    print("  [2/5] Harness consultando Postgres...")
    t2 = time.time()
    schema, pasos = generar_schema(pregunta)
    contexto = harness_consultar_postgres(sesion_id, write_result["finalidad"])
    dt_harness = time.time() - t2
    n_chars = sum(len(v) for v in contexto.values())
    print(f"        {len(contexto)} secciones, ~{n_chars} chars ({dt_harness:.2f}s)")

    # === FASE 3: CLAUDE -P → ANÁLISIS ===
    print("  [3/5] claude -p analizando (Max Plan, $0)...")

    system_analista = f"""Responde SOLO con un JSON válido. Sin markdown, sin explicaciones, sin texto antes o después del JSON.

Eres un analista de datos. Analizas los datos del Simbionte proporcionados.

REGLAS:
- Solo cita valores que aparezcan en los datos. Si no hay dato, pon "sin datos".
- NUNCA inventes números. Solo usa los que ves en los datos.
- Sigue los pasos del protocolo en orden para construir tu análisis interno.
- Tu respuesta FINAL es SOLO el JSON de abajo. Nada más.

Responde EXACTAMENTE con este JSON (rellena cada campo):
{{
  "diagnostico": "fase del ciclo económico en una frase",
  "datos_citados": [
    {{"nombre": "nombre_formula", "valor": 0.0, "interpretacion": "qué significa"}}
  ],
  "desequilibrios": ["desequilibrio 1", "desequilibrio 2"],
  "prescripcion_bc": "qué debería hacer el banco central",
  "prescripcion_gobierno": "qué debería hacer el gobierno",
  "riesgos_ocultos": ["riesgo 1", "riesgo 2", "riesgo 3"],
  "alertas": ["contradicciones o señales de alarma"],
  "confianza": "alta/media/baja",
  "razonamiento": "resumen de los pasos del protocolo en 3-4 frases"
}}"""

    prompt_analista = construir_prompt(pregunta, contexto, pasos)
    respuesta_raw, dt_analista = llamar_claude_p(system_analista, prompt_analista)

    # Extraer JSON si viene envuelto en markdown
    import re as _re
    json_match = _re.search(r'\{[\s\S]*\}', respuesta_raw)
    if json_match:
        try:
            respuesta_json = json.loads(json_match.group())
            respuesta_raw = json.dumps(respuesta_json, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            pass  # Mantener respuesta_raw como está
    print(f"        {len(respuesta_raw)} chars ({dt_analista:.1f}s)")

    # === FASE 4: H3 VERIFICACIÓN ===
    print("  [4/5] H3 verificando datos inventados...")
    resultados_local = calcular_formulas_economia(series_dict)
    discrepancias = h3_verificar(respuesta_raw, resultados_local)
    print(f"        {len(discrepancias)} discrepancias")

    # === FASE 5: TRADUCTOR ===
    print("  [5/5] Traduciendo para CEO...")

    system_traductor = """Eres un traductor. Recibes análisis técnico económico (puede ser JSON o texto con datos).
Tu trabajo es traducirlo a lenguaje natural claro y directo para un CEO que NO es economista.
REGLAS: No añadas información nueva. No inventes datos. Solo traduce lo que recibes.
Estructura: 1 párrafo de diagnóstico, 1 de qué hacer, 1 de riesgos. Máximo 250 palabras."""

    prompt_traductor = f"Traduce este análisis económico a lenguaje natural:\n\n{respuesta_raw}"
    traduccion, dt_traductor = llamar_claude_p(system_traductor, prompt_traductor)
    print(f"        {len(traduccion)} chars ({dt_traductor:.1f}s)")

    dt_total = time.time() - t_total

    return {
        "respuesta_raw": respuesta_raw,
        "respuesta": traduccion,
        "sesion_id": sesion_id,
        "write_result": write_result,
        "contexto_chars": n_chars,
        "n_secciones": len(contexto),
        "system_chars": len(system_analista),
        "dt_write": write_result["dt"],
        "dt_harness": dt_harness,
        "dt_analista": dt_analista,
        "dt_traductor": dt_traductor,
        "dt_total": dt_total,
        "n_discrepancias": len(discrepancias),
        "discrepancias": discrepancias,
        "coste": 0.0,  # Max Plan = $0
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
    print("PIPELINE OMC-95 COMPLETO")
    print("Simbionte → Postgres → Harness → claude -p → H3 → Traductor")
    print("Coste: $0 (Max Plan)")
    print("=" * 70)
    print(f"Pregunta: {pregunta}")
    print(f"Series: {list(series.keys())}")
    print()

    result = ejecutar_pipeline(series, pregunta)

    print(f"\n{'=' * 70}")
    print("MÉTRICAS")
    print(f"{'=' * 70}")
    wr = result["write_result"]
    print(f"  Fórmulas calculadas: {wr['n_formulas_calculadas']}")
    print(f"  Escritos en Postgres: {wr['n_escritos']}")
    print(f"  Patrones detectados: {wr['n_patrones_detectados']}")
    print(f"  Finalidad: {wr['finalidad']}")
    print(f"  Contexto para LLM: {result['contexto_chars']} chars ({result['n_secciones']} secciones)")
    print(f"  System prompt: {result['system_chars']} chars")
    print(f"  H3 discrepancias: {result['n_discrepancias']}")
    print(f"  Coste: ${result['coste']:.2f}")
    print(f"\n  Tiempos:")
    print(f"    Simbionte → Postgres: {result['dt_write']:.2f}s")
    print(f"    Harness → consulta:   {result['dt_harness']:.2f}s")
    print(f"    claude -p análisis:   {result['dt_analista']:.1f}s")
    print(f"    claude -p traductor:  {result['dt_traductor']:.1f}s")
    print(f"    TOTAL:                {result['dt_total']:.1f}s")

    print(f"\n{'=' * 70}")
    print("RESPUESTA RAW (del analista):")
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
