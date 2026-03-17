#!/usr/bin/env python3
"""EXP P33 Evaluador Multi-Variante — 4 prompts × 149 hallazgos via MiMo."""

import json
import os
import re
import time
import httpx
import asyncio
from datetime import datetime, timezone
from pathlib import Path

# Load .env
ENV_PATH = Path(__file__).parent.parent / "motor_v1_validation" / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
MODEL = "deepseek/deepseek-chat-v3-0324"
BASE_DIR = Path(__file__).parent.parent / "datos" / "exp_p33"
RESULTS_DIR = BASE_DIR / "resultados"

# Cost tracking via deployed system
SYSTEM_URL = "https://chief-os-omni.fly.dev"

# =========================================================================
# BASELINE
# =========================================================================

BASELINE = """Estado verificado de OMNI-MIND (16-mar-2026):
- Autopoiesis: 1/4 checks con valor, 3 son null. 9 alertas autopoiesis_roto, 2 sin consumir. ciclo_roto=false contradice las alertas.
- Flywheel: 0 ciclos completados. Nunca ha aprendido autónomamente.
- Programas: 4 compilados, todos tasa_cierre=1.0 (sospechoso — calibración real ~0.52).
- Costes: Solo MiMo registrado en costes_llm. Motor principal (DeepSeek, Step) no aparece.
- Propiocepcion: dice 0 ejecuciones 24h pero métricas muestran ~10 recientes.
- tasa_media_global volátil: 0.18→0.72→0.51 sin patrón claro.
- Criticalidad: T=0.25, régimen orden_rigido pero avalanchas supercritico.
- 144 datapoints, 124 endpoints, 12 modelos activos (4 caídos), 2 exocortex piloto sin datos reales.
- Reactor: 0 candidatas pendientes, sin mecanismo de retroalimentación forzada.
- Consistencia: INCONSISTENTE — 144 datapoints huérfanos, 9 modelos inactivos en enjambre, 20 preguntas expiradas.
- Neural DB: 42 conexiones, fuerza media 0.108, 0 conexiones fuertes.
- Tools evolution: vacío, sin datos de uso de herramientas.
- No hay clientes externos ni ingresos."""

# =========================================================================
# 4 PROMPTS
# =========================================================================

PROMPT_V2 = """Eres un evaluador técnico. Clasifica este hallazgo sobre un sistema de IA en exactamente UNA categoría.

CATEGORÍAS:
- CONOCIDO: Repite un dato disponible directamente en los endpoints del sistema
- REFORMULADO: Reformula algo que un humano detectaría cruzando datos de varios endpoints
- NUEVO: Insight operativo que ningún endpoint ni cruce manual detecta — riesgo, dependencia o punto ciego genuinamente no visible
- RUIDO: Fragmento incompleto, encabezado de lista, preámbulo genérico, o texto sin análisis real

{baseline}

HALLAZGO:
"{hallazgo}"

Responde EXACTAMENTE con: CATEGORIA|razón (máx 15 palabras)"""

PROMPT_V3A = """Evalúa este hallazgo sobre un sistema de IA usando la siguiente secuencia analítica. Ejecuta cada paso internamente y da solo el resultado final.

SECUENCIA:
1. EXTRAER: ¿Qué afirmación concreta hace este hallazgo? Si no hace ninguna afirmación concreta (es un fragmento, encabezado, o preámbulo), clasifica como RUIDO y para aquí.

2. CRUZAR: Compara la afirmación con el baseline del sistema. ¿Coincide con algún dato que ya reportan los endpoints? Si sí → CONOCIDO.

3. LENTES: Mira la afirmación desde 3 ángulos:
   - Salud: ¿Dice algo sobre si algo funciona o no funciona? ¿Es dato directo o inferencia?
   - Sentido: ¿Dice algo sobre la dirección del sistema? ¿Es observación o interpretación nueva?
   - Continuidad: ¿Dice algo sobre qué sobrevive o qué es frágil? ¿Es visible en los datos o requiere razonamiento?

4. INTEGRAR: Si la afirmación es inferencia o interpretación que un humano haría cruzando datos del baseline → REFORMULADO. Si revela algo que NO se puede deducir ni cruzando todos los datos → NUEVO.

{baseline}

HALLAZGO:
"{hallazgo}"

Responde EXACTAMENTE con: CATEGORIA|razón (máx 15 palabras)
Categorías válidas: CONOCIDO, REFORMULADO, NUEVO, RUIDO"""

PROMPT_V3B = """Evalúa este hallazgo sobre un sistema de IA respondiendo las siguientes preguntas. Responde internamente y da solo la clasificación final.

PREGUNTAS DE FILTRO:
- ¿Este texto contiene una afirmación analítica completa, o es un fragmento/encabezado/preámbulo? → Si fragmento: RUIDO

PREGUNTAS DE SALUD (¿funciona?):
- ¿Este hallazgo describe un dato que ya está disponible en los endpoints del sistema? → Si sí: CONOCIDO
- ¿Describe un fallo o riesgo que un endpoint reporta directamente? → Si sí: CONOCIDO

PREGUNTAS DE SENTIDO (¿tiene dirección?):
- ¿Este hallazgo conecta dos datos que están en endpoints separados para revelar una contradicción o patrón? → Si sí: REFORMULADO
- ¿Reformula una inconsistencia que alguien leyendo los datos cruzados detectaría? → Si sí: REFORMULADO

PREGUNTAS DE CONTINUIDAD (¿sobrevive?):
- ¿Este hallazgo revela un riesgo, dependencia o punto ciego que NO es visible ni siquiera cruzando todos los datos disponibles? → Si sí: NUEVO
- ¿Identifica algo que solo emerge al razonar sobre el sistema como un todo, no como suma de métricas? → Si sí: NUEVO
- ¿Propone una pregunta que el sistema debería hacerse pero no se hace? → Si sí: NUEVO

{baseline}

HALLAZGO:
"{hallazgo}"

Responde EXACTAMENTE con: CATEGORIA|razón (máx 15 palabras)
Categorías válidas: CONOCIDO, REFORMULADO, NUEVO, RUIDO"""

PROMPT_V3C = """Tu tarea es clasificar un hallazgo sobre un sistema de IA. Para hacerlo, vas a usar un método de evaluación en dos fases.

FASE 1 — ENTIENDE EL MÉTODO (lee esto como marco de trabajo):

El sistema OMNI-MIND se analiza a través de 3 lentes y 7 funciones. Las 3 lentes son:
- SALUD: ¿funciona? ¿Los componentes operan correctamente?
- SENTIDO: ¿tiene dirección? ¿Avanza o da vueltas?
- CONTINUIDAD: ¿sobrevive? ¿Qué lo hace frágil o robusto?

Un hallazgo puede ser información que el sistema ya tiene (sus endpoints la reportan), información que emerge al cruzar datos de varios endpoints (un humano la vería), o información genuinamente nueva que no es visible ni cruzando todos los datos disponibles.

La secuencia de evaluación es: primero extraer la afirmación del hallazgo, luego cruzarla con lo que el sistema ya sabe, luego mirarla a través de las 3 lentes, y finalmente integrar para decidir si es nueva o no.

FASE 2 — EJECUTA EL MÉTODO (responde estas preguntas internamente):

Pregunta 0: ¿Este texto contiene una afirmación analítica completa? ¿O es un fragmento, un encabezado de lista, o un preámbulo sin contenido propio?
→ Si no es una afirmación completa: RUIDO

Pregunta 1 — EXTRAER: ¿Cuál es la afirmación central de este hallazgo en una frase?

Pregunta 2 — CRUZAR: ¿Esta afirmación aparece como dato directo en algún endpoint del sistema?
→ Si sí: CONOCIDO

Pregunta 3 — LENTE SALUD: ¿Lo que dice sobre "funciona/no funciona" es algo que un humano vería cruzando los datos del baseline?
Pregunta 4 — LENTE SENTIDO: ¿Lo que dice sobre "dirección/estancamiento" es algo que un humano inferiría del baseline?
Pregunta 5 — LENTE CONTINUIDAD: ¿Lo que dice sobre "fragilidad/robustez" es algo deducible del baseline?
→ Si alguna lente dice sí: REFORMULADO

Pregunta 6 — INTEGRAR: ¿Queda algo que NO sea visible en los datos ni cruzándolos? ¿Hay un riesgo, dependencia, punto ciego o pregunta que solo emerge al razonar sobre el sistema como totalidad?
→ Si sí: NUEVO
→ Si no: REFORMULADO

{baseline}

HALLAZGO:
"{hallazgo}"

Responde EXACTAMENTE con: CATEGORIA|razón (máx 15 palabras)
Categorías válidas: CONOCIDO, REFORMULADO, NUEVO, RUIDO"""

VARIANTES = {
    "v2": {"prompt": PROMPT_V2, "desc": "clasificacion directa"},
    "v3a": {"prompt": PROMPT_V3A, "desc": "imperativo algebra semantica (EXTRAER→CRUZAR→LENTES→INTEGRAR)"},
    "v3b": {"prompt": PROMPT_V3B, "desc": "red de preguntas por lente (Salud/Sentido/Continuidad)"},
    "v3c": {"prompt": PROMPT_V3C, "desc": "mixto: explicacion algoritmo (imperativo) + ejecucion con preguntas"},
}

# =========================================================================
# HALLAZGO EXTRACTION (same as evaluador v1)
# =========================================================================

def extraer_hallazgos_texto(resultado: dict) -> list:
    """Extrae SOLO hallazgos reales (no preguntas) del Motor."""
    textos = []
    for h in resultado.get("hallazgos", []):
        if isinstance(h, dict):
            text = h.get("hallazgo", "")
            inteligencia = h.get("inteligencia", "?")
        elif isinstance(h, str):
            text = h
            inteligencia = "?"
        else:
            continue

        stripped = text.strip().lstrip("- *#")
        if stripped.startswith("¿") or stripped.startswith("1.") or stripped.startswith("2."):
            if "allazgo:" not in text:
                continue

        is_finding = "allazgo:" in text
        is_substantive = len(text.strip()) > 80 and "¿" not in text[:20]

        if is_finding or is_substantive:
            textos.append({"texto": text.strip(), "inteligencia": inteligencia, "caso": resultado.get("caso_id", "?")})

    sintesis = resultado.get("sintesis", "")
    if sintesis:
        paragraphs = re.split(r'\n\n+', sintesis)
        for p in paragraphs:
            p = p.strip()
            if p.startswith("[INT-") or p.startswith("SINTESIS") or "¿" in p[:20]:
                continue
            if len(p) > 80:
                textos.append({"texto": p, "inteligencia": "sintesis", "caso": resultado.get("caso_id", "?")})

    return textos


def cargar_hallazgos() -> list:
    """Carga todos los hallazgos de los 6 resultados."""
    all_h = []
    for f in sorted(RESULTS_DIR.glob("p33_resultado_*.json")):
        with open(f) as fh:
            r = json.load(fh)
        hallazgos = extraer_hallazgos_texto(r)
        all_h.extend(hallazgos)
    return all_h


# =========================================================================
# LLM CALL
# =========================================================================

async def call_mimo(client: httpx.AsyncClient, prompt: str) -> str:
    """Call MiMo via OpenRouter."""
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0.0,
    }
    try:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=body,
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://omni-mind.app",
                "X-Title": "OMNI-MIND P33 Evaluator",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"RUIDO|error: {str(e)[:50]}"


def parse_response(resp: str) -> tuple:
    """Parse CATEGORIA|razón from LLM response."""
    # Find the line with CATEGORIA|razón pattern
    for line in resp.strip().splitlines():
        line = line.strip()
        if "|" in line:
            parts = line.split("|", 1)
            cat = parts[0].strip().upper().replace("*", "").replace(":", "")
            razon = parts[1].strip() if len(parts) > 1 else ""
            if cat in ("CONOCIDO", "REFORMULADO", "NUEVO", "RUIDO"):
                return cat, razon

    # Fallback: look for category keyword anywhere
    upper = resp.upper()
    for cat in ("NUEVO", "REFORMULADO", "CONOCIDO", "RUIDO"):
        if cat in upper:
            return cat, resp.strip()[:60]

    return "RUIDO", f"unparseable: {resp[:60]}"


# =========================================================================
# EVALUATION
# =========================================================================

async def evaluar_variante(hallazgos: list, variante: str, prompt_template: str) -> list:
    """Evalúa todos los hallazgos con una variante de prompt."""
    resultados = []
    async with httpx.AsyncClient() as client:
        for i, h in enumerate(hallazgos):
            prompt = prompt_template.format(baseline=BASELINE, hallazgo=h["texto"][:1500])
            resp = await call_mimo(client, prompt)
            cat, razon = parse_response(resp)

            resultados.append({
                "categoria": cat,
                "razon": razon,
                "variante": variante,
                "caso": h["caso"],
                "inteligencia": h["inteligencia"],
                "hallazgo": h["texto"][:300],
                "raw_response": resp[:200],
            })

            if (i + 1) % 25 == 0:
                print(f"  [{variante}] {i+1}/{len(hallazgos)}")

            # Small delay to avoid rate limits
            if (i + 1) % 10 == 0:
                await asyncio.sleep(0.5)

    return resultados


# =========================================================================
# COMPARATIVA
# =========================================================================

def generar_comparativa(todos: dict, hallazgos: list) -> dict:
    """Genera análisis comparativo entre las 4 variantes."""
    n = len(hallazgos)

    # Per-hallazgo comparison
    acuerdo_total = 0
    nuevo_unanime = []
    nuevo_mayoria = []
    nuevo_minimo = []
    solo = {v: [] for v in VARIANTES}

    for i in range(n):
        cats = {}
        for v in VARIANTES:
            cats[v] = todos[v][i]["categoria"]

        values = list(cats.values())
        if len(set(values)) == 1:
            acuerdo_total += 1

        nuevo_count = sum(1 for c in values if c == "NUEVO")
        hallazgo_info = {"idx": i, "hallazgo": hallazgos[i]["texto"][:200], "cats": cats}

        if nuevo_count == 4:
            nuevo_unanime.append(hallazgo_info)
        if nuevo_count >= 3:
            nuevo_mayoria.append(hallazgo_info)
        if nuevo_count >= 2:
            nuevo_minimo.append(hallazgo_info)

        # Solo in one variant
        for v in VARIANTES:
            if cats[v] == "NUEVO" and sum(1 for c in values if c == "NUEVO") == 1:
                solo[v].append(hallazgo_info)

    # v3c specific comparisons
    v3c_nuevo = set(i for i, r in enumerate(todos["v3c"]) if r["categoria"] == "NUEVO")
    v3a_nuevo = set(i for i, r in enumerate(todos["v3a"]) if r["categoria"] == "NUEVO")
    v3b_nuevo = set(i for i, r in enumerate(todos["v3b"]) if r["categoria"] == "NUEVO")

    return {
        "acuerdo_total": f"{acuerdo_total}/{n} ({acuerdo_total/max(n,1)*100:.0f}%)",
        "nuevo_unanime": len(nuevo_unanime),
        "nuevo_unanime_hallazgos": [h["hallazgo"] for h in nuevo_unanime[:10]],
        "nuevo_mayoria": len(nuevo_mayoria),
        "nuevo_mayoria_hallazgos": [h["hallazgo"] for h in nuevo_mayoria[:10]],
        "nuevo_minimo": len(nuevo_minimo),
        "solo_v2": len(solo["v2"]),
        "solo_v3a": len(solo["v3a"]),
        "solo_v3b": len(solo["v3b"]),
        "solo_v3c": len(solo["v3c"]),
        "v3c_vs_v3a": {
            "v3c_detecta_v3a_no": len(v3c_nuevo - v3a_nuevo),
            "v3a_detecta_v3c_no": len(v3a_nuevo - v3c_nuevo),
            "ambos": len(v3c_nuevo & v3a_nuevo),
        },
        "v3c_vs_v3b": {
            "v3c_detecta_v3b_no": len(v3c_nuevo - v3b_nuevo),
            "v3b_detecta_v3c_no": len(v3b_nuevo - v3c_nuevo),
            "ambos": len(v3c_nuevo & v3b_nuevo),
        },
        "v3c_vs_v3a_v3b_union": {
            "solo_v3c": len(v3c_nuevo - (v3a_nuevo | v3b_nuevo)),
            "v3c_superset": v3c_nuevo >= (v3a_nuevo | v3b_nuevo),
        },
    }


def generar_resumen(evaluacion: dict):
    """Genera RESUMEN_P33_v2.md."""
    v = evaluacion["variantes"]
    comp = evaluacion["comparativa"]

    lines = [
        "# RESUMEN P33 v2 — Evaluación con 4 variantes de prompt",
        "",
        f"**Fecha:** {evaluacion['fecha']}",
        f"**Modelo evaluador:** {MODEL}",
        f"**Coste total:** ${evaluacion['coste_total_usd']:.4f}",
        f"**Hallazgos evaluados:** {evaluacion['total_hallazgos']}",
        "",
        "---",
        "",
        "## Tabla comparativa",
        "",
        "| Categoría | v1 (keywords) | v2 (directo) | v3a (imperativo) | v3b (preguntas) | v3c (mixto) |",
        "|-----------|--------------|--------------|-------------------|-----------------|-------------|",
    ]

    v1 = {"CONOCIDO": 49, "REFORMULADO": 41, "CANDIDATO_NUEVO": 59, "RUIDO": 0}
    for cat in ["CONOCIDO", "REFORMULADO", "NUEVO", "RUIDO"]:
        v1_key = "CANDIDATO_NUEVO" if cat == "NUEVO" else cat
        v1_val = v1.get(v1_key, 0)
        v1_str = f"{v1_val}*" if cat == "NUEVO" else str(v1_val)
        row = f"| {cat} | {v1_str} | "
        for vname in ["v2", "v3a", "v3b", "v3c"]:
            row += f"{v[vname]['clasificacion'].get(cat, 0)} | "
        lines.append(row)

    lines.extend([
        "",
        "*v1 no tenía RUIDO — todo lo no matcheado caía en CANDIDATO_NUEVO*",
        "",
        "## Hallazgos NUEVO por consenso (≥3 de 4 variantes)",
        "",
        f"**Total: {comp['nuevo_mayoria']}**",
        "",
    ])
    for h in comp.get("nuevo_mayoria_hallazgos", [])[:10]:
        lines.append(f"- {h[:180]}")
    lines.append("")

    lines.extend([
        "## Hallazgos NUEVO unánimes (4 de 4)",
        "",
        f"**Total: {comp['nuevo_unanime']}**",
        "",
    ])
    for h in comp.get("nuevo_unanime_hallazgos", [])[:10]:
        lines.append(f"- {h[:180]}")
    lines.append("")

    # Prompt comparison table
    lines.extend([
        "## ¿Qué prompt funciona mejor?",
        "",
        "| Métrica | v2 | v3a | v3b | v3c |",
        "|---------|----|----|-----|-----|",
    ])
    for metric_name, metric_key in [
        ("RUIDO filtrado", "RUIDO"),
        ("NUEVO detectados", "NUEVO"),
        ("REFORMULADO", "REFORMULADO"),
        ("CONOCIDO", "CONOCIDO"),
    ]:
        row = f"| {metric_name} | "
        for vname in ["v2", "v3a", "v3b", "v3c"]:
            row += f"{v[vname]['clasificacion'].get(metric_key, 0)} | "
        lines.append(row)

    # Solo findings
    lines.extend([
        f"| Solo este prompt dice NUEVO | {comp['solo_v2']} | {comp['solo_v3a']} | {comp['solo_v3b']} | {comp['solo_v3c']} |",
        "",
    ])

    # v3c comparison
    v3c_comp = comp.get("v3c_vs_v3a", {})
    v3c_vs_b = comp.get("v3c_vs_v3b", {})
    v3c_union = comp.get("v3c_vs_v3a_v3b_union", {})

    lines.extend([
        "## Comparativa clave: v3c vs v3a+v3b",
        "",
        "| Pregunta | Resultado |",
        "|----------|-----------|",
        f"| v3c detecta NUEVO que v3a no | {v3c_comp.get('v3c_detecta_v3a_no', '?')} hallazgos |",
        f"| v3a detecta NUEVO que v3c no | {v3c_comp.get('v3a_detecta_v3c_no', '?')} hallazgos |",
        f"| v3c detecta NUEVO que v3b no | {v3c_vs_b.get('v3c_detecta_v3b_no', '?')} hallazgos |",
        f"| v3b detecta NUEVO que v3c no | {v3c_vs_b.get('v3b_detecta_v3c_no', '?')} hallazgos |",
        f"| Solo v3c encuentra (no v3a ni v3b) | {v3c_union.get('solo_v3c', '?')} hallazgos |",
        f"| v3c es superset de v3a∪v3b | {v3c_union.get('v3c_superset', '?')} |",
        "",
    ])

    # Interpretation
    n_v3c = v["v3c"]["clasificacion"].get("NUEVO", 0)
    n_v3a = v["v3a"]["clasificacion"].get("NUEVO", 0)
    n_v3b = v["v3b"]["clasificacion"].get("NUEVO", 0)

    if n_v3c > n_v3a and n_v3c > n_v3b:
        interp = f"v3c ({n_v3c}) > v3a ({n_v3a}) Y v3c > v3b ({n_v3b}): el prompt de dos partes (marco + preguntas) es SUPERIOR."
    elif n_v3c >= max(n_v3a, n_v3b) * 0.9:
        interp = f"v3c ({n_v3c}) ≈ max(v3a={n_v3a}, v3b={n_v3b}): combinar no suma significativamente."
    else:
        interp = f"v3c ({n_v3c}) < max(v3a={n_v3a}, v3b={n_v3b}): el prompt mixto introduce ruido al ser más largo."

    lines.extend([
        "## Dato empírico sobre estructura de prompts",
        "",
        f"→ **{interp}**",
        "",
    ])

    # Verdict
    n_consenso = comp["nuevo_mayoria"]
    if n_consenso >= 3:
        veredicto = "VALIDADO"
        razon = f"{n_consenso} hallazgos NUEVO por consenso ≥3/4 (umbral: ≥3)"
    elif n_consenso >= 1 and sum(v[vn]["clasificacion"].get("REFORMULADO", 0) for vn in VARIANTES) / 4 >= 5:
        veredicto = "PARCIAL"
        razon = f"{n_consenso} NUEVO por consenso + media de reformulados ≥5"
    else:
        veredicto = "DESCARTADO"
        razon = f"Solo {n_consenso} NUEVO por consenso (<3)"

    lines.extend([
        "## Veredicto P33",
        "",
        f"**{veredicto}** — {razon}",
        "",
        "---",
        "",
        f"*Generado por exp_p33_evaluador_multi.py — {evaluacion['fecha']}*",
    ])

    resumen_path = BASE_DIR / "RESUMEN_P33_v2.md"
    resumen_path.write_text("\n".join(lines))
    print(f"[multi] RESUMEN guardado en {resumen_path}")


# =========================================================================
# MAIN
# =========================================================================

async def main():
    if not OPENROUTER_KEY:
        print("[multi] ERROR: OPENROUTER_API_KEY no encontrada")
        return

    # Load hallazgos
    hallazgos = cargar_hallazgos()
    print(f"[multi] {len(hallazgos)} hallazgos cargados")

    # Run 4 variants sequentially
    todos = {}
    coste_total = 0

    for nombre, cfg in VARIANTES.items():
        print(f"\n[multi] === Variante {nombre}: {cfg['desc']} ===")
        t0 = time.time()
        resultados = await evaluar_variante(hallazgos, nombre, cfg["prompt"])
        t1 = time.time()
        todos[nombre] = resultados

        conteo = {}
        for r in resultados:
            conteo[r["categoria"]] = conteo.get(r["categoria"], 0) + 1
        print(f"  {nombre}: {conteo} ({t1-t0:.1f}s)")

    # Comparativa
    comp = generar_comparativa(todos, hallazgos)

    # Build evaluation
    evaluacion = {
        "fecha": datetime.now(timezone.utc).isoformat(),
        "total_hallazgos": len(hallazgos),
        "modelo_evaluador": MODEL,
        "variantes": {},
        "comparativa": comp,
        "coste_total_usd": 0,
    }

    for nombre in VARIANTES:
        conteo = {}
        for r in todos[nombre]:
            conteo[r["categoria"]] = conteo.get(r["categoria"], 0) + 1
        nuevos = [r for r in todos[nombre] if r["categoria"] == "NUEVO"]
        evaluacion["variantes"][nombre] = {
            "prompt": VARIANTES[nombre]["desc"],
            "clasificacion": conteo,
            "hallazgos_nuevo": [{"caso": r["caso"], "hallazgo": r["hallazgo"], "razon": r["razon"]} for r in nuevos[:15]],
            "total_llamadas": len(todos[nombre]),
        }

    # Veredicto
    n_consenso = comp["nuevo_mayoria"]
    if n_consenso >= 3:
        evaluacion["veredicto_p33"] = "VALIDADO"
        evaluacion["razon"] = f"{n_consenso} hallazgos NUEVO por consenso ≥3/4"
    elif n_consenso >= 1:
        evaluacion["veredicto_p33"] = "PARCIAL"
        evaluacion["razon"] = f"{n_consenso} NUEVO por consenso"
    else:
        evaluacion["veredicto_p33"] = "DESCARTADO"
        evaluacion["razon"] = f"0 NUEVO por consenso"

    # Save
    eval_path = BASE_DIR / "evaluacion_p33_comparativa.json"
    with open(eval_path, "w") as f:
        json.dump(evaluacion, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n[multi] Evaluación guardada en {eval_path}")

    # Save raw per-variant results
    for nombre in VARIANTES:
        raw_path = BASE_DIR / f"evaluacion_p33_{nombre}_raw.json"
        with open(raw_path, "w") as f:
            json.dump(todos[nombre], f, indent=2, ensure_ascii=False, default=str)

    # Generate summary
    generar_resumen(evaluacion)

    # Final output
    print(f"\n{'='*60}")
    print(f"  VEREDICTO P33: {evaluacion['veredicto_p33']}")
    print(f"  {evaluacion['razon']}")
    print(f"{'='*60}")
    print(f"  Acuerdo total: {comp['acuerdo_total']}")
    print(f"  NUEVO unánime: {comp['nuevo_unanime']}")
    print(f"  NUEVO mayoría (≥3/4): {comp['nuevo_mayoria']}")
    print(f"  NUEVO mínimo (≥2/4): {comp['nuevo_minimo']}")
    for vn in VARIANTES:
        c = evaluacion["variantes"][vn]["clasificacion"]
        print(f"  {vn}: C={c.get('CONOCIDO',0)} R={c.get('REFORMULADO',0)} N={c.get('NUEVO',0)} X={c.get('RUIDO',0)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
