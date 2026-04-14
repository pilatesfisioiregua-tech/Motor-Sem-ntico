"""
Calibrador MCTS — 50 preguntas × 5 datasets = 250 evaluaciones.

Objetivo: encontrar los pesos óptimos de las 15 reglas basándose en
qué reglas discriminan (a veces pasan, a veces fallan) y cuáles no.

Cada evaluación genera 1 hipótesis (no 3 — optimizamos por volumen).
Total: 250 hipótesis evaluadas contra 15 reglas = 3750 datapoints.

Output: calibracion_resultados.json con estadísticas por regla.
"""

import sys, os, json, time, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from clasificador_economia import calcular_formulas_economia
from evaluador_reglas import evaluar
from protocolo_analista import generar_schema

CLAUDE_CMD = os.getenv("CLAUDE_CMD", "claude")

# ============================================================
# 50 PREGUNTAS — 10 categorías × 5 preguntas cada una
# ============================================================

PREGUNTAS = [
    # DIAGNÓSTICO (10)
    "Cuál es el estado actual de la economía? Está en expansión o recesión?",
    "En qué fase del ciclo económico estamos? Qué indicadores lo confirman?",
    "La economía está sobrecalentada o enfriándose? Qué datos lo muestran?",
    "Hay señales de recesión inminente? Cuáles son los indicadores adelantados?",
    "Cómo se compara la situación actual con la media histórica de los últimos 20 años?",
    "Cuál es el principal desequilibrio de la economía ahora mismo?",
    "La inflación es de demanda o de oferta? Qué datos lo distinguen?",
    "El mercado laboral está tenso o holgado? Qué implica para la política?",
    "Hay divergencia entre el crecimiento del PIB y el bienestar real de los ciudadanos?",
    "Cuál es la salud fiscal del país? La deuda es sostenible?",

    # PRESCRIPCIÓN (10)
    "Qué debería hacer el banco central con los tipos de interés? Subir, bajar o mantener?",
    "Qué política fiscal recomiendas? Expansiva, contractiva o neutral?",
    "Cómo mejorar la competitividad exportadora sin depreciar la moneda?",
    "Qué reformas estructurales son más urgentes según los datos?",
    "Cómo reducir el desempleo sin alimentar la inflación?",
    "Debería el gobierno aumentar o reducir el gasto público? Con qué datos?",
    "Cuál es la mejor estrategia para reducir la deuda pública gradualmente?",
    "Cómo proteger a los ciudadanos de la inflación sin distorsionar el mercado?",
    "Qué sector debería priorizar la inversión pública para maximizar el crecimiento?",
    "Cómo coordinar política monetaria y fiscal en esta situación?",

    # RIESGO (10)
    "Cuáles son los 3 riesgos ocultos más graves de la economía actual?",
    "Hay riesgo de crisis de deuda soberana? Qué umbrales son peligrosos?",
    "Qué pasa si la inflación se desancla completamente? Cuál es el peor escenario?",
    "Hay riesgo de espiral salarios-precios? Los datos lo sugieren?",
    "Cuán vulnerable es la economía a un shock externo? Exportaciones, energía, tipos?",
    "Qué riesgos sistémicos no son evidentes en los titulares?",
    "Si el desempleo sube 3 puntos, cuál es el efecto cascada en el resto de indicadores?",
    "Hay burbuja en algún sector según los datos? Inmobiliario, consumo, crédito?",
    "Cuál es el riesgo de que el banco central se equivoque de política?",
    "Qué pasaría si los tipos de interés suben 200 puntos básicos adicionales?",

    # COMPARACIÓN (10)
    "Cómo se compara esta economía con las demás del G7 en estos indicadores?",
    "La recuperación post-COVID está siendo más rápida o lenta que la media?",
    "El ratio deuda/PIB es mejor o peor que el de economías comparables?",
    "El desempleo es estructural o cíclico? Cómo se compara con la media OCDE?",
    "La balanza comercial ha mejorado o empeorado en la última década?",
    "Los tipos de interés reales son positivos o negativos? Qué implica?",
    "La productividad está creciendo más rápido o más lento que la inflación?",
    "El consumo está tirando más que la inversión? Es sostenible?",
    "Hay convergencia o divergencia con las economías centrales de la zona euro?",
    "El modelo de crecimiento actual es más dependiente de deuda o de productividad?",

    # PREDICCIÓN (10)
    "Basándote en las tendencias actuales, qué escenario es más probable en 2 años?",
    "Si las tendencias continúan, cuándo se alcanzará pleno empleo?",
    "La inflación va a converger al objetivo del 2% o se va a quedar por encima?",
    "Es sostenible el ritmo de crecimiento actual durante 5 años más?",
    "Qué variable es más probable que se deteriore primero? Por qué?",
    "Si no se hace nada, cuál es la trayectoria natural de la deuda/PIB?",
    "El sector exterior va a mejorar o empeorar? Qué factores lo determinan?",
    "Los tipos de interés van a seguir bajando o hay riesgo de reversión?",
    "El mercado laboral va a seguir mejorando al ritmo actual?",
    "Cuál es el escenario base, el optimista y el pesimista para los próximos 4 trimestres?",
]

DATASETS = ["espana", "usa", "alemania", "japon", "sintetico_crisis"]


def _llamar_claude_p_rapido(prompt: str) -> str:
    """claude -p optimizado para velocidad."""
    env = {k: v for k, v in os.environ.items()}
    env.pop("CLAUDECODE", None)
    try:
        result = subprocess.run(
            [CLAUDE_CMD, "-p"],
            input=prompt,
            capture_output=True, text=True,
            timeout=120,  # 2 min max
            env=env,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return '{"error": "TIMEOUT"}'


def evaluar_una(pregunta: str, series: dict, idx: int, total: int) -> dict:
    """Evalúa una pregunta sobre un dataset. Genera 1 hipótesis."""
    t0 = time.time()

    # Calcular resultados + valores absolutos
    resultados = calcular_formulas_economia(series)
    for ns, vals in series.items():
        arr = np.array(vals, dtype=float)
        arr = arr[np.isfinite(arr)]
        if len(arr) < 2:
            continue
        resultados[f"{ns}_ultimo"] = {"valor": float(arr[-1]), "tipo": "nivel", "texto": f"último {ns}"}
        resultados[f"{ns}_minimo"] = {"valor": float(np.min(arr)), "tipo": "nivel", "texto": f"min {ns}"}
        resultados[f"{ns}_maximo"] = {"valor": float(np.max(arr)), "tipo": "nivel", "texto": f"max {ns}"}
        resultados[f"{ns}_media"] = {"valor": float(np.mean(arr)), "tipo": "nivel", "texto": f"media {ns}"}

    # Construir contexto compacto (top resultados)
    sorted_res = sorted(resultados.items(), key=lambda x: abs(x[1]["valor"]), reverse=True)
    contexto_lines = []
    for rn, ri in sorted_res[:25]:
        v = ri["valor"]
        sg = "+" if v >= 0 else ""
        contexto_lines.append(f"{rn}: {sg}{v:.4f} ({ri['texto']})")
    contexto = "\n".join(contexto_lines)

    schema, pasos = generar_schema(pregunta)

    prompt = f"""INSTRUCCIONES: Analista de datos. Responde SOLO con JSON válido.

DATOS DEL SIMBIONTE:
{contexto}

PROTOCOLO ({len(pasos)} pasos):
{chr(10).join(f'  {i+1}. {p["nombre"]}' for i, (_, p) in enumerate(pasos))}

REGLAS:
- Solo cita valores de los datos. NUNCA inventes.
- Cada desequilibrio con dato de respaldo.
- Cada prescripción dirigida a un desequilibrio.
- Cada riesgo derivado de los datos, con números.
- Si confianza="alta", cita >=5 datos. Si hay >=2 alertas, confianza="media".
- Menciona datos más extremos en razonamiento.

PREGUNTA: {pregunta}

JSON:
{{"diagnostico":"frase","datos_citados":[{{"nombre":"formula","valor":0.0,"interpretacion":"texto"}}],"desequilibrios":["..."],"prescripcion_bc":"texto","prescripcion_gobierno":"texto","riesgos_ocultos":["..."],"alertas":["..."],"confianza":"alta/media/baja","razonamiento":"resumen"}}"""

    raw = _llamar_claude_p_rapido(prompt)
    dt = time.time() - t0

    # Parse JSON
    import re
    json_match = re.search(r'\{[\s\S]*\}', raw)
    hipotesis = None
    if json_match:
        try:
            hipotesis = json.loads(json_match.group())
        except:
            pass

    if not hipotesis:
        return {
            "idx": idx, "pregunta": pregunta[:50], "score": 0,
            "error": True, "dt": dt, "reglas": {},
        }

    # Evaluar
    ev = evaluar(hipotesis, resultados)

    # Detalle por regla
    reglas = {}
    for r_name in [f"R{i}" for i in range(1, 16)]:
        reglas[r_name] = ev["detalle"].get(r_name, {}).get("ok", None)

    print(f"  [{idx+1}/{total}] {ev['score']:>3}/100 | {pregunta[:45]}... ({dt:.0f}s)")

    return {
        "idx": idx,
        "pregunta": pregunta[:80],
        "score": ev["score"],
        "n_pasadas": ev["n_pasadas"],
        "n_fallidas": ev["n_fallidas"],
        "fallidas": ev["fallidas"],
        "reglas": reglas,
        "hard_gate": ev.get("hard_gate", False),
        "dt": round(dt, 1),
        "error": False,
    }


def calibrar(n_preguntas: int = 50, datasets: list = None):
    """Ejecuta calibración completa."""
    if datasets is None:
        datasets = DATASETS

    preguntas = PREGUNTAS[:n_preguntas]
    total = len(preguntas) * len(datasets)

    print(f"CALIBRACIÓN MCTS")
    print(f"  Preguntas: {len(preguntas)}")
    print(f"  Datasets: {datasets}")
    print(f"  Total evaluaciones: {total}")
    print(f"  Estimación: ~{total * 60 // 60} min")
    print()

    resultados = []
    t_total = time.time()

    for ds_name in datasets:
        print(f"\n=== Dataset: {ds_name} ===")
        with open(f"datos_{ds_name}_fred.json") as f:
            series = json.load(f)

        for i, pregunta in enumerate(preguntas):
            idx_global = len(resultados)
            r = evaluar_una(pregunta, series, idx_global, total)
            r["dataset"] = ds_name
            resultados.append(r)

            # Guardar progresivo cada 10
            if (idx_global + 1) % 10 == 0:
                with open("calibracion_progreso.json", "w") as f:
                    json.dump(resultados, f, indent=2, ensure_ascii=False)

    dt_total = time.time() - t_total

    # Guardar resultados completos
    with open("calibracion_resultados.json", "w") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    # ================================================================
    # ANÁLISIS
    # ================================================================
    print(f"\n{'=' * 70}")
    print("ANÁLISIS DE CALIBRACIÓN")
    print(f"{'=' * 70}")
    print(f"  Total evaluaciones: {len(resultados)}")
    print(f"  Errores (JSON inválido): {sum(1 for r in resultados if r['error'])}")
    print(f"  Tiempo total: {dt_total/60:.1f} min")

    # Score distribution
    scores = [r["score"] for r in resultados if not r["error"]]
    print(f"\n  Score distribución:")
    print(f"    Media: {np.mean(scores):.1f}")
    print(f"    Mediana: {np.median(scores):.1f}")
    print(f"    Min: {np.min(scores)}")
    print(f"    Max: {np.max(scores)}")
    print(f"    <60: {sum(1 for s in scores if s < 60)}")
    print(f"    60-79: {sum(1 for s in scores if 60 <= s < 80)}")
    print(f"    80-89: {sum(1 for s in scores if 80 <= s < 90)}")
    print(f"    90+: {sum(1 for s in scores if s >= 90)}")

    # Regla por regla
    print(f"\n  Regla por regla (tasa de fallo):")
    regla_stats = {}
    for r_name in [f"R{i}" for i in range(1, 16)]:
        ok = sum(1 for r in resultados if not r["error"] and r["reglas"].get(r_name) == True)
        fail = sum(1 for r in resultados if not r["error"] and r["reglas"].get(r_name) == False)
        total_r = ok + fail
        fail_rate = fail / total_r if total_r > 0 else 0
        regla_stats[r_name] = {"ok": ok, "fail": fail, "total": total_r, "fail_rate": fail_rate}

        discrimina = "DISCRIMINA" if 0.10 < fail_rate < 0.60 else ("SIEMPRE PASA" if fail_rate < 0.10 else "MUY ESTRICTA")
        print(f"    {r_name}: {ok}✓ {fail}✗ ({fail_rate*100:.0f}% fallo) → {discrimina}")

    # Score por dataset
    print(f"\n  Score por dataset:")
    for ds in datasets:
        ds_scores = [r["score"] for r in resultados if r["dataset"] == ds and not r["error"]]
        if ds_scores:
            print(f"    {ds}: media={np.mean(ds_scores):.1f}, min={np.min(ds_scores)}, max={np.max(ds_scores)}")

    # Score por categoría de pregunta
    print(f"\n  Score por categoría:")
    categorias = ["DIAGNÓSTICO", "PRESCRIPCIÓN", "RIESGO", "COMPARACIÓN", "PREDICCIÓN"]
    for i, cat in enumerate(categorias):
        cat_scores = [r["score"] for r in resultados[i*10*len(datasets):(i+1)*10*len(datasets)] if not r.get("error")]
        if cat_scores:
            print(f"    {cat}: media={np.mean(cat_scores):.1f}")

    # Pesos recalibrados
    print(f"\n  PESOS RECALIBRADOS (basado en tasa de discriminación):")
    pesos_nuevos = {}
    for r_name, stats in regla_stats.items():
        fr = stats["fail_rate"]
        if fr < 0.05:
            peso = 2   # Casi nunca falla → poco útil
        elif fr < 0.15:
            peso = 5   # Falla poco → moderadamente útil
        elif fr < 0.30:
            peso = 10  # Sweet spot — discrimina bien
        elif fr < 0.50:
            peso = 15  # Discrimina mucho — muy valiosa
        else:
            peso = 8   # Falla demasiado — puede ser demasiado estricta
        pesos_nuevos[r_name] = peso
        print(f"    {r_name}: {peso} (fail_rate={fr*100:.0f}%)")

    # Guardar pesos
    with open("pesos_calibrados.json", "w") as f:
        json.dump({
            "pesos": pesos_nuevos,
            "stats": regla_stats,
            "meta": {
                "n_evaluaciones": len(resultados),
                "n_errores": sum(1 for r in resultados if r["error"]),
                "score_media": round(float(np.mean(scores)), 1),
                "datasets": datasets,
                "n_preguntas": len(preguntas),
                "dt_total_min": round(dt_total / 60, 1),
            }
        }, f, indent=2)

    print(f"\n  Guardado: calibracion_resultados.json + pesos_calibrados.json")
    return resultados, pesos_nuevos


if __name__ == "__main__":
    # Verificar que los datasets existen
    for ds in DATASETS:
        try:
            with open(f"datos_{ds}_fred.json") as f:
                json.load(f)
        except:
            print(f"FALTA: datos_{ds}_fred.json")
            sys.exit(1)

    calibrar(n_preguntas=50, datasets=DATASETS)
