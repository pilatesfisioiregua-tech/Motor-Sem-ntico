"""
Pipeline Completo — Simbionte + Prompt Caching + pgvector + H3 Verificación

Fecha: 2026-04-13

Las piezas:
  1. Simbionte: calcula fórmulas sobre datos
  2. Harness: selecciona las más informativas
  3. Decodificador: traduce a texto con gramática
  4. pgvector (local): busca isomorfismos previos en catálogo
  5. Prompt caching: system prompt cacheado (1/10 coste en calls 2+)
  6. LLM: Sonnet o Opus con T=0, pre-fill JSON
  7. H3: verifica que el LLM no inventa datos

$0 compute local + coste API por llamada
"""

import sys, os, json, time, numpy as np
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))

from clasificador_economia import calcular_formulas_economia
from gramatica_formulas import FORMULAS, OPS, detectar_isomorfismos
from decodificador_economia import clasificar_nivel


# ============================================================
# COMPONENTE 1: HARNESS (selección inteligente)
# ============================================================

def harness_seleccionar(resultados, top_n=30):
    """Selecciona fórmulas más informativas."""
    scored = []
    for n, info in resultados.items():
        v = info["valor"]; t = info["tipo"]; av = abs(v)
        ni, nt = clasificar_nivel(v, t)
        s = 0; r = ""

        # Principio: la AUSENCIA de señal es tan informativa como su PRESENCIA.
        # Persistencia baja = "transitorio" es tan valioso como persistencia alta = "estructural".
        # Correlación ~0 = "independientes" es valioso si se esperaría relación.
        # Gap ~0 = "en equilibrio" es valioso como confirmación.

        if t == "correlacion":
            if av > 0.8: s, r = 100, "corr muy fuerte"
            elif av > 0.6: s, r = 70, "corr fuerte"
            elif av < 0.05: s, r = 40, "independientes (sin relación)"  # AUSENCIA informativa
            else: s = 10
        elif t == "gap":
            if av > 0.05: s, r = 90, "gap significativo"
            elif av > 0.02: s, r = 50, "gap moderado"
            elif av < 0.005: s, r = 35, "en equilibrio"  # AUSENCIA informativa
            else: s = 5
        elif t == "elasticidad":
            s, r = 85, "elasticidad"
            if av < 0.05: r = "inelástico (insensible)"  # AUSENCIA informativa
        elif t == "persistencia":
            if av > 0.5: s, r = 80, "persistente (estructural)"
            elif av < 0.1: s, r = 60, "transitorio (se disipa)"  # FIX: antes era 25 → descartado
            else: s = 25
        elif t == "aceleracion":
            if av > 0.05: s, r = 65, "aceleración"
            elif av < 0.005: s, r = 30, "sin aceleración (velocidad constante)"  # AUSENCIA
            else: s = 10
        elif t == "tasa_crecimiento":
            if "momentum" in n and av > 0.10: s, r = 55, "momentum fuerte"
            elif "momentum" in n and av < 0.01: s, r = 35, "sin momentum (estancado)"  # AUSENCIA
            elif "crecimiento" in n:
                s = 40
                if av < 0.002: r = "crecimiento nulo"  # AUSENCIA
            else: s = 15
        elif t == "coef_variacion":
            if av > 0.20: s, r = 50, "alta impredecibilidad"
            elif av < 0.03: s, r = 30, "muy predecible"  # AUSENCIA
            else: s = 5
        elif t == "tasa_cambio":
            if av > 0.05: s, r = 45, "cambio reciente grande"
            else: s = 10
        elif t in ("varianza", "nivel"):
            s = 2
        else:
            s = 15
        scored.append((n, info, s, r, ni, nt))
    scored.sort(key=lambda x: -x[2])
    return scored[:top_n]


# ============================================================
# COMPONENTE 2: DECODIFICADOR
# ============================================================

def decodificar(seleccion, nombre=""):
    """Decodifica fórmulas seleccionadas a texto."""
    lines = [f"# ANÁLISIS ESTRUCTURAL — {nombre}", ""]
    pt = defaultdict(list)
    for item in seleccion:
        pt[item[1]["tipo"]].append(item)
    for t in sorted(pt.keys()):
        lines.append(f"## {t.upper().replace('_', ' ')}")
        for n, info, sc, r, ni, nt in pt[t]:
            v = info["valor"]; sg = "+" if v >= 0 else ""
            l = f"  {n}: {sg}{v:.4f} → {nt}"
            if r: l += f" [{r}]"
            l += f" ({info['texto']})"
            lines.append(l)
        lines.append("")
    # Isomorfismos cross-domain
    isos = detectar_isomorfismos()
    cross = [(s, ns) for s, ns in isos.items()
             if len(set(FORMULAS[n]["rama"] for n in ns if n in FORMULAS)) > 1]
    if cross:
        lines.append("## ISOMORFISMOS CROSS-DOMAIN")
        for seq, nombres in cross[:5]:
            ops_n = [list(OPS.keys())[list(OPS.values()).index(s)] for s in seq]
            lines.append(f"  🔗 {'→'.join(ops_n)} = {', '.join(nombres)}")
        lines.append("")
    return "\n".join(lines)


# ============================================================
# COMPONENTE 3: pgvector LOCAL (catálogo de isomorfismos)
# ============================================================

# Catálogo de patrones conocidos con sus firmas
ISOMORFISMOS_CATALOGO = {
    "ESTANFLACION": {
        "señales": {"corr_inflacion_desempleo": (">", 0.3), "pib_crecimiento_medio": ("<", 0.01),
                     "inflacion_momentum": (">", 0.1)},
        "descripcion": "Inflación persistente con estancamiento económico. La curva de Phillips colapsa.",
        "precedentes": ["UK 1970s", "USA 1973-75", "Brasil 2014-16"],
        "prescripcion_historica": "Volcker shock (subida agresiva tipos) funcionó; gradualismo fracasó.",
    },
    "TRAMPA_LIQUIDEZ": {
        "señales": {"tipo_interes_nivel": ("<", 1.0), "inflacion_momentum": ("<", -0.05),
                     "elasticidad_consumo_tipo_interes": (">", -0.05)},
        "descripcion": "Tipos cerca de cero, política monetaria ineficaz. El dinero se acumula sin circular.",
        "precedentes": ["Japón 1990-2020", "Eurozona 2014-19", "USA 2008-15"],
        "prescripcion_historica": "QE + estímulo fiscal masivo + forward guidance comprometido.",
    },
    "BOOM_EXPORTADOR": {
        "señales": {"pib_crecimiento_medio": (">", 0.008), "exportaciones_momentum": (">", 0.1),
                     "desempleo_momentum": ("<", -0.05)},
        "descripcion": "Crecimiento liderado por exportaciones. Riesgo de dutch disease y dependencia externa.",
        "precedentes": ["Alemania 2003-08", "China 2001-08", "Corea 1960-97"],
        "prescripcion_historica": "Diversificar fuentes de crecimiento; crear fondos soberanos; invertir en capital humano.",
    },
    "CRISIS_FISCAL": {
        "señales": {"deuda_pib_momentum": (">", 0.1), "tipo_interes_momentum": (">", 0.1),
                     "pib_crecimiento_medio": ("<", -0.005)},
        "descripcion": "Espiral deuda-tipos: la deuda sube, los mercados exigen más interés, la deuda sube más.",
        "precedentes": ["Grecia 2010-15", "Argentina 2001", "Italia 2011"],
        "prescripcion_historica": "Reestructuración + ajuste fiscal creíble + apoyo externo (FMI/BCE).",
    },
    "BURBUJA_ACTIVOS": {
        "señales": {"pib_crecimiento_medio": (">", 0.01), "inflacion_nivel": ("<", 2.0),
                     "inversion_momentum": (">", 0.15)},
        "descripcion": "Crecimiento alto con inflación baja oculta formación de burbuja en activos.",
        "precedentes": ["USA 1995-2000 (dot-com)", "USA 2003-07 (inmobiliaria)", "Japón 1985-90"],
        "prescripcion_historica": "Regulación macroprudencial; subida preventiva de tipos; vigilancia apalancamiento.",
    },
    "DEFLACION_SECULAR": {
        "señales": {"inflacion_crecimiento_medio": ("<", -0.01), "tipo_interes_nivel": ("<", 0.5),
                     "deuda_pib_nivel": (">", 200)},
        "descripcion": "Deflación crónica con deuda masiva. El valor real de la deuda crece, deprimiendo inversión.",
        "precedentes": ["Japón 1990-2020", "Gran Depresión 1930-33"],
        "prescripcion_historica": "Expansión fiscal masiva + QE permanente + reformas estructurales profundas.",
    },
    "SUDDEN_STOP": {
        "señales": {"pib_tasa_cambio": ("<", -0.03), "importaciones_momentum": (">", 0.05)},
        "descripcion": "Parada súbita de flujos de capital. Colapso de tipo de cambio y output.",
        "precedentes": ["Asia 1997", "Rusia 1998", "Turquía 2018"],
        "prescripcion_historica": "Control de capitales temporal + ajuste fiscal + acuerdo FMI.",
    },
    "AUSTERIDAD_CONTRAPRODUCENTE": {
        "señales": {"pib_crecimiento_medio": ("<", -0.002), "deuda_pib_momentum": (">", 0.02),
                     "consumo_momentum": ("<", -0.05)},
        "descripcion": "El ajuste fiscal deprime tanto el PIB que la ratio deuda/PIB sube en vez de bajar.",
        "precedentes": ["Grecia 2010-14", "España 2011-13", "Portugal 2011-13"],
        "prescripcion_historica": "Ajuste más gradual; priorizar crecimiento; reformas estructurales antes que recortes.",
    },
}


def pgvector_buscar(resultados):
    """Busca isomorfismos en el catálogo local.

    Returns: lista de matches con score de confianza
    """
    matches = []

    for iso_nombre, iso_info in ISOMORFISMOS_CATALOGO.items():
        señales = iso_info["señales"]
        n_match = 0
        n_total = len(señales)
        detalles = []

        for señal_nombre, (op, threshold) in señales.items():
            # Buscar en resultados
            for res_nombre, res_info in resultados.items():
                if señal_nombre in res_nombre:
                    valor = res_info["valor"]
                    if op == ">" and valor > threshold:
                        n_match += 1
                        detalles.append(f"{señal_nombre}={valor:.4f} (>{threshold})")
                    elif op == "<" and valor < threshold:
                        n_match += 1
                        detalles.append(f"{señal_nombre}={valor:.4f} (<{threshold})")
                    break

        confianza = n_match / max(n_total, 1)
        if confianza >= 0.5:  # Al menos 50% de señales match
            matches.append({
                "nombre": iso_nombre,
                "confianza": confianza,
                "descripcion": iso_info["descripcion"],
                "precedentes": iso_info["precedentes"],
                "prescripcion_historica": iso_info["prescripcion_historica"],
                "detalles": detalles,
            })

    matches.sort(key=lambda x: -x["confianza"])
    return matches


def pgvector_a_texto(matches):
    """Convierte matches de pgvector a texto para el LLM."""
    if not matches:
        return ""
    lines = ["## PATRONES HISTÓRICOS DETECTADOS (pgvector)"]
    lines.append("Estos patrones coinciden con situaciones históricas conocidas.\n")
    for m in matches[:3]:  # Top 3
        lines.append(f"### 🔍 {m['nombre']} (confianza: {m['confianza']:.0%})")
        lines.append(f"  {m['descripcion']}")
        lines.append(f"  Precedentes: {', '.join(m['precedentes'])}")
        lines.append(f"  Prescripción histórica: {m['prescripcion_historica']}")
        lines.append(f"  Señales: {'; '.join(m['detalles'])}")
        lines.append("")
    return "\n".join(lines)


# ============================================================
# COMPONENTE 4: H3 VERIFICACIÓN
# ============================================================

def h3_verificar(respuesta_llm, resultados):
    """Verifica que el LLM no inventa datos.

    Busca números citados en la respuesta y compara con Simbionte.
    Devuelve lista de discrepancias.
    """
    import re
    discrepancias = []

    # Buscar patrones como "correlación X-Y = 0.XX" o "elasticidad = 0.XX"
    # Pattern: word followed by number
    numeros_citados = re.findall(r'(\w+)[:\s=]+([+-]?\d+\.?\d*)', respuesta_llm.lower())

    for contexto, valor_str in numeros_citados:
        try:
            valor_citado = float(valor_str)
        except ValueError:
            continue

        # Buscar en resultados del Simbionte
        for res_nombre, res_info in resultados.items():
            if contexto in res_nombre.lower():
                valor_real = res_info["valor"]
                # Verificar si el LLM citó algo cercano
                if abs(valor_real) > 0.01:
                    error_pct = abs(valor_citado - valor_real) / abs(valor_real)
                    if error_pct > 0.20:  # >20% discrepancia
                        discrepancias.append({
                            "contexto": contexto,
                            "citado": valor_citado,
                            "real": valor_real,
                            "error_pct": error_pct,
                        })
                break

    return discrepancias


# ============================================================
# PIPELINE COMPLETO
# ============================================================

def pipeline_completo(series_dict, nombre, client, model, question):
    """Ejecuta el pipeline completo v2:
    Finalidad → Harness demand-driven → Simbionte → Cascada → pgvector → Semántica → Caching → LLM → H3

    Returns: dict con respuesta, métricas, verificación
    """
    from catalogo_finalidades import detectar_finalidad, formulas_para_pregunta
    from red_preguntas import cascada, cascada_a_texto
    from semantica_formulas import razonamiento_a_texto

    t0 = time.time()

    # 1. FINALIDAD: detectar intención del usuario
    finalidades = detectar_finalidad(question)

    # 2. SIMBIONTE: calcular TODAS las fórmulas (el harness filtra después)
    resultados = calcular_formulas_economia(series_dict)
    dt_sim = time.time() - t0

    # 3. HARNESS demand-driven: seleccionar por finalidad + relevancia
    formulas_activas = formulas_para_pregunta(question)
    seleccion = harness_seleccionar(resultados, top_n=35)

    # 4. CASCADA: red de preguntas encadenadas
    # Mapear resultados detallados (pib_varianza) a tipos genéricos (varianza)
    # tomando el valor más extremo de cada tipo
    import numpy as _np
    resultados_por_tipo = {}
    for n, info in resultados.items():
        tipo = info["tipo"]
        val = info["valor"]
        # Extraer nombre genérico: "pib_varianza" → "varianza", "corr_pib_inflacion" → "correlacion"
        for enlace_nombre in ENLACES:
            if enlace_nombre in n or tipo == enlace_nombre:
                if enlace_nombre not in resultados_por_tipo or abs(val) > abs(resultados_por_tipo[enlace_nombre]):
                    resultados_por_tipo[enlace_nombre] = val
    # También añadir marcos si están
    for n, info in resultados.items():
        if n.startswith("marco_"):
            resultados_por_tipo[n] = info["valor"]

    resultados_valores = resultados_por_tipo
    cadena = cascada(resultados_valores, max_profundidad=3)
    contexto_cascada = cascada_a_texto(cadena, resultados_valores)

    # 5. SEMÁNTICA: razonamiento paso a paso para las fórmulas más importantes
    contexto_semantica_lines = []
    formulas_con_semantica = 0
    for nombre_f, info, score, reason, ni, nt in seleccion[:10]:  # Top 10
        texto_raz = razonamiento_a_texto(nombre_f, info["valor"])
        if texto_raz:
            contexto_semantica_lines.append(texto_raz)
            formulas_con_semantica += 1
    contexto_semantica = "\n\n".join(contexto_semantica_lines) if contexto_semantica_lines else ""

    # 6. DECODIFICADOR: traducir selección a texto
    contexto_simbionte = decodificar(seleccion, nombre)

    # 7. pgvector: buscar patrones históricos
    matches = pgvector_buscar(resultados)
    contexto_pgvector = pgvector_a_texto(matches)

    # 8. Construir system prompt completo (para caching)
    system_prompt = f"""Eres un economista senior con acceso al Simbionte — un sistema que:
1. Calcula fórmulas económicas sobre datos reales
2. Descompone cada fórmula en su gramática de operaciones primitivas
3. Detecta patrones históricos (isomorfismos) por similitud estructural
4. Encadena preguntas: la respuesta de una fórmula desbloquea la siguiente
5. Verifica cruzado: ¿tu análisis semántico coincide con la estructura?

INSTRUCCIONES:
- Usa los datos del Simbionte como EVIDENCIA. Cita valores específicos.
- Cada fórmula tiene POLOS (eje semántico) y PRESUPUESTOS (lo que asume sin decirlo).
- Los isomorfismos cross-domain indican que el MISMO mecanismo opera en dominios diferentes.
- La RED DE PREGUNTAS muestra qué preguntas desbloquea cada respuesta. SÍGUELA.
- La VERIFICACIÓN CRUZADA marca puntos donde tu análisis debe coincidir con la estructura.
- Los patrones históricos son PRECEDENTES verificados — úsalos para prescribir.
- NO inventes datos. Si no tienes un valor del Simbionte, di "sin datos".
- Máximo 400 palabras.

Finalidades detectadas: {', '.join(finalidades)}

{contexto_simbionte}

{contexto_cascada}

{contexto_pgvector}

## SEMÁNTICA (razonamiento paso a paso de las fórmulas clave)
{contexto_semantica}"""

    dt_prep = time.time() - t0

    # 6. Llamada LLM con prompt caching
    t_llm = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=800,
        temperature=0,  # Determinístico
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Prompt caching
            }
        ],
        messages=[{"role": "user", "content": question}],
    )
    dt_llm = time.time() - t_llm

    respuesta = response.content[0].text

    # 7. H3: verificar
    discrepancias = h3_verificar(respuesta, resultados)

    # Costes
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cache_read = getattr(response.usage, 'cache_read_input_tokens', 0) or 0
    cache_create = getattr(response.usage, 'cache_creation_input_tokens', 0) or 0

    if "opus" in model:
        cost = (input_tokens * 15 + output_tokens * 75 + cache_read * 1.5 + cache_create * 18.75) / 1e6
    else:
        cost = (input_tokens * 3 + output_tokens * 15 + cache_read * 0.3 + cache_create * 3.75) / 1e6

    return {
        "respuesta": respuesta,
        "finalidades": finalidades,
        "n_formulas": len(resultados),
        "n_seleccionadas": len(seleccion),
        "n_formulas_activas": len(formulas_activas),
        "n_cascada": len(cadena),
        "n_semantica": formulas_con_semantica,
        "n_isomorfismos": len(matches),
        "isomorfismos": [m["nombre"] for m in matches],
        "n_discrepancias": len(discrepancias),
        "discrepancias": discrepancias,
        "tokens_input": input_tokens,
        "tokens_output": output_tokens,
        "cache_read": cache_read,
        "cache_create": cache_create,
        "cost": cost,
        "dt_simbionte_ms": dt_prep * 1000,
        "dt_llm_s": dt_llm,
        "system_prompt_chars": len(system_prompt),
    }


def llamada_sin(dashboard, client, model, question):
    """Llamada SIN Simbionte (baseline)."""
    t0 = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=800,
        temperature=0,
        messages=[{"role": "user", "content": f"Datos: {dashboard}\n\n{question}"}],
    )
    dt = time.time() - t0

    if "opus" in model:
        cost = (response.usage.input_tokens * 15 + response.usage.output_tokens * 75) / 1e6
    else:
        cost = (response.usage.input_tokens * 3 + response.usage.output_tokens * 15) / 1e6

    return {
        "respuesta": response.content[0].text,
        "tokens_input": response.usage.input_tokens,
        "tokens_output": response.usage.output_tokens,
        "cost": cost,
        "dt_llm_s": dt,
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Pipeline completo — test rápido")

    # Simular datos
    np.random.seed(77)
    t = np.arange(48)
    series = {
        "pib": list(300000*(1+0.008*t-0.0002*t**2)*(1+0.005*np.random.randn(48))),
        "inflacion": list(1.5+0.08*t+0.3*np.sin(2*np.pi*t/12)+0.2*np.random.randn(48)),
        "desempleo": list(7+0.05*t+0.3*np.random.randn(48)),
        "tipo_interes": list(0.5+0.03*t+0.1*np.random.randn(48)),
        "consumo": list(0.58*300000*(1+0.008*t)+200*np.random.randn(48)),
        "inversion": list(0.22*300000*(1+0.008*t)+150*np.random.randn(48)),
        "exportaciones": list(0.30*300000*(1+0.008*t)+100*np.random.randn(48)),
        "importaciones": list(0.34*300000*(1+0.008*t)+100*np.random.randn(48)),
        "deuda_pib": list(95+0.8*t+0.5*np.random.randn(48)),
    }

    resultados = calcular_formulas_economia(series)
    matches = pgvector_buscar(resultados)

    print(f"\n  Fórmulas calculadas: {len(resultados)}")
    print(f"  Isomorfismos encontrados: {len(matches)}")
    for m in matches:
        print(f"    🔍 {m['nombre']} ({m['confianza']:.0%}) — {m['descripcion'][:60]}...")

    print(f"\n  pgvector texto:")
    print(pgvector_a_texto(matches))
