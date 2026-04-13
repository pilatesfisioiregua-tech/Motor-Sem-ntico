"""
MCTS Pipeline — Monte Carlo Tree Search sobre análisis del Simbionte.

Flujo:
  1. Simbionte → Postgres (datos determinísticos)
  2. LLM genera N hipótesis (temperature>0 para variedad)
  3. Evaluador determinístico puntúa cada hipótesis (15 reglas, $0)
  4. Si score < umbral → feedback al LLM con reglas fallidas → genera variantes
  5. Repite hasta score > umbral o max rondas
  6. Traductor sobre la mejor hipótesis

Analogía AlphaZero:
  - Posición del tablero = datos del Simbionte
  - Jugadas posibles = hipótesis del LLM
  - Reglas del ajedrez = 15 reglas determinísticas
  - MCTS = loop generar→evaluar→refinar
  - Retropropagación = feedback de reglas fallidas al LLM
"""

import sys, os, json, time, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from simbionte_writer import calcular_y_escribir
from protocolo_analista import generar_schema
from clasificador_economia import calcular_formulas_economia
from evaluador_reglas import evaluar
from pipeline_completo import h3_verificar

import httpx

SIMBIONTE_URL = os.getenv("SIMBIONTE_URL", "https://motor-semantico-omni.fly.dev")
CLAUDE_CMD = os.getenv("CLAUDE_CMD", "claude")

# Configuración MCTS
SCORE_UMBRAL = 85        # Score mínimo para aceptar
MAX_RONDAS = 3           # Máximo de rondas de refinamiento
HIPOTESIS_POR_RONDA = 3  # N hipótesis por ronda (ronda 1)
VARIANTES_REFINE = 2     # Variantes en rondas de refinamiento


def _harness_context(sesion_id: str) -> str:
    """Consulta Postgres y devuelve contexto compacto."""
    url = SIMBIONTE_URL
    secciones = []
    for tipo in ("diagnostico", "relaciones", "riesgo", "prescripcion", "todo"):
        try:
            r = httpx.post(f"{url}/simbionte/consultar", json={
                "sesion_id": sesion_id, "tool": "calcular", "params": {"tipo": tipo}
            }, timeout=15)
            data = r.json().get("resultado", "")
            if data and data != f"Sin resultados para tipo '{tipo}'.":
                secciones.append(f"=== {tipo.upper()} ===\n{data}")
        except:
            pass
    # Patrones
    try:
        r = httpx.post(f"{url}/simbionte/consultar", json={
            "sesion_id": sesion_id, "tool": "consultar_patron", "params": {"senales": "patron"}
        }, timeout=15)
        data = r.json().get("resultado", "")
        if data and "Sin patrones" not in data:
            secciones.append(f"=== PATRONES ===\n{data}")
    except:
        pass
    return "\n\n".join(secciones)


def _llamar_claude_p(prompt: str, temperature_hint: str = "variado") -> str:
    """Llama a claude -p. temperature_hint se pasa en el prompt."""
    env = {k: v for k, v in os.environ.items()}
    env.pop("CLAUDECODE", None)

    try:
        result = subprocess.run(
            [CLAUDE_CMD, "-p"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return '{"error": "TIMEOUT"}'


def _generar_hipotesis(pregunta: str, contexto: str, pasos: list,
                       n: int = 3, feedback: str = None) -> list:
    """Genera N hipótesis de análisis via claude -p."""
    hipotesis = []

    base_prompt = f"""INSTRUCCIONES DEL SISTEMA:
Analista de datos. Responde SOLO con JSON válido.

DATOS DEL SIMBIONTE:
{contexto}

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

REGLAS:
- Solo cita valores de los datos. Si no hay, pon "sin datos".
- NUNCA inventes números.
- Cada desequilibrio debe tener al menos 1 dato de respaldo.
- Cada prescripción debe dirigirse a un desequilibrio diagnosticado.
- Cada riesgo debe derivarse de los datos, no de conocimiento general.
- Si confianza="alta", cita ≥5 datos verificados.
- Menciona los valores más extremos en el razonamiento.

---

PREGUNTA: {pregunta}

Responde SOLO con JSON:
{{
  "diagnostico": "frase",
  "datos_citados": [{{"nombre": "formula", "valor": 0.0, "interpretacion": "texto"}}],
  "desequilibrios": ["con datos de respaldo"],
  "prescripcion_bc": "dirigida a desequilibrios",
  "prescripcion_gobierno": "dirigida a desequilibrios",
  "riesgos_ocultos": ["derivados de los datos, con números"],
  "alertas": ["contradicciones con números"],
  "confianza": "alta/media/baja",
  "razonamiento": "mencionar datos más extremos"
}}"""

    for i in range(n):
        if feedback and i == 0:
            prompt = f"""{base_prompt}

IMPORTANTE — CORRECCIONES DE LA RONDA ANTERIOR:
{feedback}

Genera un análisis DIFERENTE que corrija estos problemas."""
        elif i > 0:
            prompt = f"""{base_prompt}

IMPORTANTE: Genera un análisis DIFERENTE al anterior. Explora otra perspectiva. Cita datos diferentes si es posible."""
        else:
            prompt = base_prompt

        print(f"        Generando hipótesis {i+1}/{n}...", end=" ", flush=True)
        t0 = time.time()
        raw = _llamar_claude_p(prompt)
        dt = time.time() - t0

        # Extraer JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', raw)
        if json_match:
            try:
                h = json.loads(json_match.group())
                hipotesis.append(h)
                print(f"OK ({dt:.0f}s)")
                continue
            except json.JSONDecodeError:
                pass
        print(f"JSON inválido ({dt:.0f}s)")
        hipotesis.append({"error": "JSON parse failed", "raw": raw[:500]})

    return hipotesis


def ejecutar_mcts(series_dict: dict, pregunta: str) -> dict:
    """Pipeline MCTS completo."""
    t_total = time.time()

    # === FASE 1: Simbionte → Postgres ===
    print("  [1] Simbionte → Postgres...")
    write_result = calcular_y_escribir(series_dict, pregunta, modelo_llm="mcts-claude-p")
    sesion_id = write_result["sesion_id"]
    print(f"      {write_result['n_escritos']} escritos ({write_result['dt']:.2f}s)")

    # Calcular resultados locales para evaluador
    resultados_local = calcular_formulas_economia(series_dict)

    # Añadir valores absolutos al dict de referencia (para que R1 pueda verificar)
    for nombre_serie, valores in series_dict.items():
        arr = np.array(valores, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) < 2:
            continue
        resultados_local[f"{nombre_serie}_ultimo"] = {"valor": float(arr[-1]), "tipo": "nivel", "texto": f"último valor de {nombre_serie}"}
        resultados_local[f"{nombre_serie}_minimo"] = {"valor": float(np.min(arr)), "tipo": "nivel", "texto": f"mínimo de {nombre_serie}"}
        resultados_local[f"{nombre_serie}_maximo"] = {"valor": float(np.max(arr)), "tipo": "nivel", "texto": f"máximo de {nombre_serie}"}
        resultados_local[f"{nombre_serie}_media"] = {"valor": float(np.mean(arr)), "tipo": "nivel", "texto": f"media de {nombre_serie}"}

    # === FASE 2: Harness consulta Postgres ===
    print("  [2] Harness → Postgres...")
    contexto = _harness_context(sesion_id)
    schema, pasos = generar_schema(pregunta)
    print(f"      {len(contexto)} chars contexto")

    # === FASE 3: MCTS Loop ===
    print("  [3] MCTS Loop...")
    mejor_score = 0
    mejor_hipotesis = None
    mejor_eval = None
    historial = []
    total_hipotesis = 0
    feedback = None

    for ronda in range(MAX_RONDAS):
        n = HIPOTESIS_POR_RONDA if ronda == 0 else VARIANTES_REFINE
        print(f"\n      --- Ronda {ronda+1}/{MAX_RONDAS} ({n} hipótesis) ---")

        hipotesis_list = _generar_hipotesis(pregunta, contexto, pasos, n=n, feedback=feedback)
        total_hipotesis += len(hipotesis_list)

        for i, h in enumerate(hipotesis_list):
            if "error" in h:
                print(f"      H{i+1}: ERROR (JSON inválido)")
                historial.append({"ronda": ronda+1, "idx": i+1, "score": 0, "error": True})
                continue

            # Evaluar contra 15 reglas
            ev = evaluar(h, resultados_local)
            score = ev["score"]
            historial.append({
                "ronda": ronda+1, "idx": i+1, "score": score,
                "pasadas": ev["n_pasadas"], "fallidas": ev["n_fallidas"],
            })

            print(f"      H{i+1}: {score}/100 ({ev['n_pasadas']}✓ {ev['n_fallidas']}✗)")
            if ev["fallidas"]:
                for f in ev["fallidas"][:2]:
                    print(f"           ✗ {f[:80]}")

            if score > mejor_score:
                mejor_score = score
                mejor_hipotesis = h
                mejor_eval = ev

        # ¿Suficientemente bueno?
        if mejor_score >= SCORE_UMBRAL:
            print(f"\n      ✓ Score {mejor_score}/100 ≥ {SCORE_UMBRAL} → ACEPTAR")
            break

        # Feedback para siguiente ronda
        if mejor_eval and mejor_eval["fallidas"]:
            feedback = "Reglas fallidas en la mejor hipótesis:\n"
            for f in mejor_eval["fallidas"]:
                feedback += f"  - {f}\n"
            feedback += f"\nScore actual: {mejor_score}/100. Necesario: {SCORE_UMBRAL}."
            print(f"\n      Score {mejor_score}/100 < {SCORE_UMBRAL} → refinando con feedback...")

    dt_mcts = time.time() - t_total - write_result["dt"]

    # === FASE 4: Traductor ===
    print(f"\n  [4] Traduciendo mejor hipótesis (score={mejor_score})...")
    t_trad = time.time()
    trad_prompt = f"""INSTRUCCIONES DEL SISTEMA:
Eres un traductor. Traduce análisis técnico a lenguaje natural para un CEO no economista.
3 párrafos: diagnóstico, qué hacer, riesgos. Max 250 palabras. No inventes datos.

---

Traduce:
{json.dumps(mejor_hipotesis, indent=2, ensure_ascii=False)}"""

    traduccion = _llamar_claude_p(trad_prompt)
    dt_trad = time.time() - t_trad
    print(f"      {len(traduccion)} chars ({dt_trad:.0f}s)")

    dt_total = time.time() - t_total

    return {
        "mejor_hipotesis": mejor_hipotesis,
        "mejor_score": mejor_score,
        "mejor_eval": mejor_eval,
        "traduccion": traduccion,
        "sesion_id": sesion_id,
        "write_result": write_result,
        "historial": historial,
        "total_hipotesis": total_hipotesis,
        "n_rondas": min(ronda + 1, MAX_RONDAS),
        "dt_mcts": dt_mcts,
        "dt_trad": dt_trad,
        "dt_total": dt_total,
        "coste": 0.0,
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
    print("MCTS PIPELINE — Monte Carlo Tree Search + Simbionte")
    print("Simbionte → Postgres → N hipótesis → 15 reglas → refinar → mejor")
    print(f"Config: umbral={SCORE_UMBRAL}, max_rondas={MAX_RONDAS}, "
          f"hipotesis_r1={HIPOTESIS_POR_RONDA}, variantes={VARIANTES_REFINE}")
    print(f"Coste: $0 (claude -p Max Plan)")
    print("=" * 70)
    print(f"Pregunta: {pregunta}")
    print()

    # Wake fly.io
    try:
        httpx.get(f"{SIMBIONTE_URL}/health", timeout=30)
    except:
        pass

    result = ejecutar_mcts(series, pregunta)

    print(f"\n{'=' * 70}")
    print("RESULTADOS MCTS")
    print(f"{'=' * 70}")
    print(f"  Score final: {result['mejor_score']}/100")
    print(f"  Rondas: {result['n_rondas']}")
    print(f"  Hipótesis totales: {result['total_hipotesis']}")
    print(f"  Coste: ${result['coste']:.2f}")
    print(f"  Tiempo MCTS: {result['dt_mcts']:.0f}s")
    print(f"  Tiempo total: {result['dt_total']:.0f}s")

    print(f"\n  Historial:")
    for h in result["historial"]:
        status = "✓" if h["score"] >= SCORE_UMBRAL else "·"
        err = " ERROR" if h.get("error") else ""
        print(f"    R{h['ronda']} H{h['idx']}: {h['score']}/100 {status}{err}")

    if result["mejor_eval"]:
        print(f"\n  Reglas mejor hipótesis:")
        for p in result["mejor_eval"]["pasadas"]:
            print(f"    ✓ {p}")
        for f in result["mejor_eval"]["fallidas"]:
            print(f"    ✗ {f}")

    print(f"\n{'=' * 70}")
    print("MEJOR HIPÓTESIS (JSON):")
    print(f"{'=' * 70}")
    print(json.dumps(result["mejor_hipotesis"], indent=2, ensure_ascii=False)[:2000])

    print(f"\n{'=' * 70}")
    print("RESPUESTA PARA CEO:")
    print(f"{'=' * 70}")
    print(result["traduccion"])
