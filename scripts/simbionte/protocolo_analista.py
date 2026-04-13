"""
Protocolo del Analista de Datos — Schema que fuerza al LLM a consultar pgvector.

Fecha: 2026-04-13

CAMBIO DE PARADIGMA:
  Antes: calcular todo → inyectar 4000 tokens → LLM lee todo → responde
  Ahora: darle un PROTOCOLO → en cada paso consulta pgvector → solo info relevante

El LLM no recibe datos — recibe un PROCEDIMIENTO.
En cada paso del procedimiento, consulta pgvector para obtener:
  - Qué fórmulas calcular
  - Qué significan los resultados
  - Qué preguntas desbloquean
  - Qué precedentes históricos aplican

Es la diferencia entre dar un libro vs dar un índice + acceso a la biblioteca.

$0 total (schema estático)
"""


# ============================================================
# PROTOCOLO: Los pasos que sigue un analista de datos
# ============================================================

PROTOCOLO = {
    # ==========================================
    # FASE 0: FRAMING
    # ==========================================
    "0_FRAMING": {
        "nombre": "Entender la pregunta",
        "pregunta_clave": "¿Qué se pregunta REALMENTE?",
        "descripcion": "Antes de tocar datos, entender qué necesita el stakeholder. "
                       "La pregunta literal casi nunca es la pregunta real.",
        "acciones": [
            "Reformular la pregunta en términos medibles",
            "Identificar la DECISIÓN que depende de la respuesta",
            "Definir qué sería una respuesta 'útil' vs 'inútil'",
            "Detectar la finalidad: DIAGNOSTICAR, RELACIONAR, PRESCRIBIR, VERIFICAR, PREDECIR, DESCOMPONER, MEDIR_RIESGO, OPTIMIZAR, VALORAR, COMPARAR",
        ],
        "consulta_pgvector": "Buscar: 'finalidades análisis datos' → obtener qué fórmulas activar",
        "output": "Pregunta reformulada + finalidad(es) + fórmulas a activar",
        "desbloquea": ["1_INVENTARIO"],
        "tokens_estimados": 100,
    },

    # ==========================================
    # FASE 1: INVENTARIO
    # ==========================================
    "1_INVENTARIO": {
        "nombre": "Inventariar los datos disponibles",
        "pregunta_clave": "¿Qué datos tengo?",
        "descripcion": "No analizar todavía — solo saber qué hay. "
                       "Cuántas series, cuántos periodos, qué fuentes, qué granularidad.",
        "acciones": [
            "Listar todas las variables disponibles con su fuente",
            "Verificar granularidad temporal (diario, mensual, trimestral) y de entidad",
            "Verificar rango temporal de cada serie",
            "Clasificar variables por tipo: nivel, tasa, ratio, índice, dummy",
            "Identificar datos que DEBERÍAN existir pero NO están",
        ],
        "consulta_pgvector": None,
        "output": "Lista de variables con: nombre, tipo, granularidad, rango, fuente",
        "desbloquea": ["1B_CALIDAD"],
        "tokens_estimados": 50,
    },

    # ==========================================
    # FASE 1B: CALIDAD DE DATOS (del research)
    # ==========================================
    "1B_CALIDAD": {
        "nombre": "Auditar calidad de datos",
        "pregunta_clave": "¿Puedo confiar en estos datos?",
        "descripcion": "ANTES de analizar: verificar que los datos no mienten. "
                       "NaN sistemáticos, duplicados, cambios de definición, huecos de ingesta. "
                       "Un análisis brillante sobre datos rotos es peor que inútil.",
        "acciones": [
            "Porcentaje de NaN por variable — ¿aleatorios o sistemáticos?",
            "Duplicados — ¿por qué existen? (reprocessing, bug, merge)",
            "Rangos plausibles — ¿valores imposibles? (negativos, futuros, extremos)",
            "Cambios de definición — ¿la métrica cambió su cálculo en algún punto?",
            "Volumen por periodo — ¿huecos o picos sospechosos?",
            "Para cada problema: limpiar con regla documentada, excluir con justificación, o marcar como limitación",
        ],
        "consulta_pgvector": None,
        "output": "Dataset auditado + lista de limitaciones conocidas + decisiones de limpieza documentadas",
        "desbloquea": ["2_DIAGNOSTICO"],
        "tokens_estimados": 80,
    },

    # ==========================================
    # FASE 2: DIAGNÓSTICO
    # ==========================================
    "2_DIAGNOSTICO": {
        "nombre": "Diagnosticar el estado de cada variable",
        "pregunta_clave": "¿Dónde está cada variable? ¿En qué polo de cada eje?",
        "descripcion": "Para cada variable, posicionarla en sus ejes fundamentales: "
                       "nivel, tendencia, dispersión, asimetría, persistencia.",
        "acciones": [
            "Calcular fórmulas de finalidad DIAGNOSTICAR",
            "Para cada resultado, consultar pgvector: ¿qué significa este valor?",
            "Posicionar en polos: disperso↔concentrado, creciendo↔contrayendo, etc.",
            "Detectar valores extremos (nivel 4 o nivel 0)",
        ],
        "consulta_pgvector": "Para cada fórmula calculada → buscar: 'Formula: {nombre}' → obtener polos + razonamiento + presupuestos",
        "output": "Mapa de posición: cada variable en sus ejes con significado",
        "desbloquea": ["3_RELACIONES", "6_ANOMALIAS"],
        "tokens_estimados": 300,
    },

    # ==========================================
    # FASE 3: RELACIONES
    # ==========================================
    "3_RELACIONES": {
        "nombre": "Descubrir relaciones entre variables",
        "pregunta_clave": "¿Qué se mueve con qué? ¿Qué causa qué?",
        "descripcion": "Correlaciones, elasticidades, causalidades. "
                       "Separar co-movimiento de causalidad.",
        "acciones": [
            "Calcular fórmulas de finalidad RELACIONAR",
            "Para correlaciones fuertes (>0.6): consultar pgvector qué isomorfismo aplica",
            "Para correlaciones ~0: consultar pgvector — ¿debería haber relación? (ausencia informativa)",
            "Buscar: ¿alguna relación tiene la misma GRAMÁTICA que otra? (isomorfismo cross-domain)",
        ],
        "consulta_pgvector": "Para cada correlación fuerte → buscar: 'isomorfismo {gramática}' → obtener precedentes cross-domain",
        "output": "Grafo de relaciones: quién afecta a quién, cuánto, y qué gramática comparten",
        "desbloquea": ["4_PATRON"],
        "tokens_estimados": 250,
    },

    # ==========================================
    # FASE 4: PATRÓN
    # ==========================================
    "4_PATRON": {
        "nombre": "Identificar patrón histórico",
        "pregunta_clave": "¿Esto se parece a algo que ya pasó?",
        "descripcion": "Buscar en pgvector patrones históricos que coincidan "
                       "con la combinación actual de señales.",
        "acciones": [
            "Construir vector de señales del estado actual",
            "Buscar en pgvector: patrones históricos con confianza >50%",
            "Para cada match: leer precedentes y prescripción histórica",
            "Verificar presupuestos: ¿los presupuestos del patrón se cumplen aquí?",
        ],
        "consulta_pgvector": "Buscar: 'patrón {señales clave}' → obtener ESTANFLACION, TRAMPA_LIQUIDEZ, etc.",
        "output": "Patrón(es) identificado(s) con confianza + precedentes + prescripción histórica",
        "desbloquea": ["5_VERIFICACION"],
        "tokens_estimados": 200,
    },

    # ==========================================
    # FASE 5: VERIFICACIÓN
    # ==========================================
    "5_VERIFICACION": {
        "nombre": "Verificar el razonamiento",
        "pregunta_clave": "¿Mi razonamiento es consistente con la estructura?",
        "descripcion": "Verificación cruzada: ¿las conclusiones semánticas (mi análisis) "
                       "coinciden con las conclusiones estructurales (Simbionte)?",
        "acciones": [
            "Para cada conclusión: consultar pgvector el razonamiento paso a paso de la fórmula",
            "Recorrer los pasos con significados — ¿cada paso se cumple?",
            "Verificar presupuestos: ¿alguno se viola? Si sí, la fórmula no aplica",
            "Ejecutar cascada de preguntas: ¿alguna verificación cruzada falla?",
        ],
        "consulta_pgvector": "Para cada fórmula clave → buscar: 'semántica {nombre}' → obtener razonamiento paso a paso + presupuestos",
        "output": "Lista de verificaciones: OK / ALERTA / CONTRADICCIÓN",
        "desbloquea": ["7_HIPOTESIS"],
        "tokens_estimados": 200,
    },

    # ==========================================
    # FASE 6: ANOMALÍAS (paralela a 3-5)
    # ==========================================
    "6_ANOMALIAS": {
        "nombre": "Detectar lo que no encaja",
        "pregunta_clave": "¿Hay algo raro que no debería estar ahí?",
        "descripcion": "Buscar outliers, discontinuidades, contradicciones entre variables, "
                       "ausencias sospechosas.",
        "acciones": [
            "Revisar fórmulas de finalidad MEDIR_RIESGO con valores extremos",
            "Buscar contradicciones: variables que deberían correlacionar pero no lo hacen",
            "Buscar gaps topológicos: funciones esperadas ausentes",
            "Buscar feedback loops: ¿hay espirales sin regulación?",
        ],
        "consulta_pgvector": "Buscar: 'feedback positivo sin regulación' o 'gap funcional' → obtener significado",
        "output": "Lista de anomalías con severidad",
        "desbloquea": ["7_HIPOTESIS"],
        "tokens_estimados": 150,
    },

    # ==========================================
    # FASE 7: HIPÓTESIS
    # ==========================================
    "7_HIPOTESIS": {
        "nombre": "Formular hipótesis",
        "pregunta_clave": "¿Por qué pasa lo que pasa?",
        "descripcion": "Con el diagnóstico, relaciones, patrón y anomalías: "
                       "formular hipótesis causales verificables.",
        "acciones": [
            "Para cada relación fuerte: ¿es causal o espuria?",
            "Para cada anomalía: ¿qué explicaría esto?",
            "Buscar en pgvector: ¿qué fórmula de VERIFICAR testea esta hipótesis?",
            "Consultar cascada: ¿qué preguntas quedan sin responder?",
        ],
        "consulta_pgvector": "Buscar: 'causalidad {X} {Y}' → obtener DiD, IV, Granger + presupuestos",
        "output": "Hipótesis rankeadas por evidencia + método de verificación",
        "desbloquea": ["8_PRESCRIPCION"],
        "tokens_estimados": 150,
    },

    # ==========================================
    # FASE 8: PRESCRIPCIÓN
    # ==========================================
    "8_PRESCRIPCION": {
        "nombre": "Prescribir acciones",
        "pregunta_clave": "¿Qué debería hacer el decisor?",
        "descripcion": "Con todo el análisis: recomendar acciones concretas. "
                       "Cada recomendación fundamentada en fórmulas específicas.",
        "acciones": [
            "Calcular fórmulas de finalidad PRESCRIBIR",
            "Para cada prescripción: consultar pgvector el precedente histórico",
            "Verificar: ¿la prescripción histórica aplica aquí? (presupuestos)",
            "Si el patrón tiene precedente: ¿qué funcionó y qué no?",
            "Cuantificar: ¿cuál es el efecto esperado? (multiplicador, elasticidad)",
        ],
        "consulta_pgvector": "Buscar: 'prescripción {patrón}' → obtener qué funcionó históricamente",
        "output": "Acciones recomendadas con fundamento + efecto esperado + riesgo",
        "desbloquea": ["9_RIESGO"],
        "tokens_estimados": 200,
    },

    # ==========================================
    # FASE 9: RIESGOS
    # ==========================================
    "9_RIESGO": {
        "nombre": "Mapear riesgos ocultos",
        "pregunta_clave": "¿Qué puede salir mal que no está en los titulares?",
        "descripcion": "Buscar riesgos estructurales que el análisis convencional no ve. "
                       "Feedback loops, dependencias, fragilidades.",
        "acciones": [
            "Revisar marcos cibernéticos: ¿hay espirales sin freno?",
            "Revisar marcos topológicos: ¿hay gaps que pueden romperse?",
            "Revisar marcos de sistemas: ¿hay fragilidad ante perturbaciones?",
            "Consultar pgvector: ¿algún presupuesto de las fórmulas se viola?",
            "Si se viola un presupuesto → la fórmula no aplica → riesgo de modelo",
        ],
        "consulta_pgvector": "Buscar: 'presupuestos {fórmula clave}' → verificar si se cumplen",
        "output": "Mapa de riesgos: estructurales + de modelo + ocultos",
        "desbloquea": ["10_COMUNICAR"],
        "tokens_estimados": 200,
    },

    # ==========================================
    # FASE 10: COMUNICAR
    # ==========================================
    "10_COMUNICAR": {
        "nombre": "Comunicar resultados",
        "pregunta_clave": "¿Cómo lo explico para que el decisor actúe?",
        "descripcion": "Pyramid Principle (Minto/McKinsey): respuesta primero, "
                       "3 argumentos de soporte, evidencia por argumento, apéndice técnico. "
                       "Cada gráfico tiene como título LA CONCLUSIÓN, no la métrica.",
        "acciones": [
            "RESPUESTA PRIMERO: una frase con la conclusión (no el proceso)",
            "3 ARGUMENTOS: los hallazgos clave que sostienen la conclusión",
            "EVIDENCIA: para cada argumento, el dato del Simbionte que lo soporta",
            "CONTRADICCIONES: donde el análisis estructural contradice el convencional",
            "LIMITACIONES: declarar ANTES de que pregunten",
            "Marcar confianza: [VERIFICADO] vs [SUPOSICIÓN] vs [RIESGO DE MODELO]",
        ],
        "consulta_pgvector": None,
        "output": "Informe: conclusión → argumentos → evidencia → riesgos → limitaciones",
        "desbloquea": [],
        "tokens_estimados": 200,
    },
}

# ============================================================
# META-REGLAS TRANSVERSALES (del research)
# ============================================================

META_REGLAS = [
    "Documentar CADA decisión de limpieza/exclusión. Si dentro de 3 meses alguien pregunta por qué, la respuesta está escrita.",
    "Reproducibilidad: cualquier analista puede reejecutar y llegar al mismo número.",
    "El análisis NO termina en el entregable. Termina cuando se mide si la acción recomendada funcionó (feedback loop).",
    "Si todas las hipótesis son inconclusas, volver al Paso 1 por más datos — no inventar.",
    "Cada observación es factual ('X bajó 15%') hasta que se demuestre causal ('X bajó 15% PORQUE Y').",
]

# Tokens totales estimados: ~1800 (vs ~4000 del approach anterior)
TOKENS_ESTIMADOS_TOTAL = sum(p["tokens_estimados"] for p in PROTOCOLO.values())


# ============================================================
# SCHEMA: Lo que recibe el LLM (en vez del prompt enorme)
# ============================================================

def generar_schema(pregunta_usuario, datos_disponibles=None):
    """Genera el schema/protocolo que recibe el LLM.

    En vez de 4000 tokens de datos, recibe ~500 tokens de instrucciones
    y la capacidad de consultar pgvector en cada paso.
    """
    from catalogo_finalidades import detectar_finalidad

    finalidades = detectar_finalidad(pregunta_usuario)

    schema = f"""# PROTOCOLO DE ANÁLISIS

## Tu pregunta: "{pregunta_usuario}"
## Finalidades detectadas: {', '.join(finalidades)}

## INSTRUCCIONES
Eres un analista de datos. Sigue este protocolo paso a paso.
En CADA paso, consulta pgvector para obtener SOLO la información que necesitas.
NO inventes datos. Si pgvector no tiene algo, di "sin datos".

## PASOS A SEGUIR:

"""
    # Solo incluir los pasos relevantes para las finalidades detectadas
    pasos_relevantes = []
    for paso_id, paso in PROTOCOLO.items():
        # Siempre incluir framing, inventario, calidad, diagnóstico, comunicar
        if paso_id in ("0_FRAMING", "1_INVENTARIO", "1B_CALIDAD", "2_DIAGNOSTICO", "10_COMUNICAR"):
            pasos_relevantes.append((paso_id, paso))
            continue

        # Incluir si la finalidad lo requiere
        if "RELACIONAR" in finalidades and paso_id == "3_RELACIONES":
            pasos_relevantes.append((paso_id, paso))
        elif "PRESCRIBIR" in finalidades and paso_id in ("4_PATRON", "8_PRESCRIPCION"):
            pasos_relevantes.append((paso_id, paso))
        elif "VERIFICAR" in finalidades and paso_id in ("5_VERIFICACION", "7_HIPOTESIS"):
            pasos_relevantes.append((paso_id, paso))
        elif "MEDIR_RIESGO" in finalidades and paso_id in ("6_ANOMALIAS", "9_RIESGO"):
            pasos_relevantes.append((paso_id, paso))
        elif "PREDECIR" in finalidades and paso_id in ("3_RELACIONES", "4_PATRON"):
            pasos_relevantes.append((paso_id, paso))
        elif "DESCOMPONER" in finalidades and paso_id in ("3_RELACIONES", "7_HIPOTESIS"):
            pasos_relevantes.append((paso_id, paso))
        elif "OPTIMIZAR" in finalidades and paso_id == "8_PRESCRIPCION":
            pasos_relevantes.append((paso_id, paso))
        elif "VALORAR" in finalidades and paso_id in ("3_RELACIONES", "8_PRESCRIPCION"):
            pasos_relevantes.append((paso_id, paso))
        elif "COMPARAR" in finalidades and paso_id in ("2_DIAGNOSTICO", "3_RELACIONES"):
            pasos_relevantes.append((paso_id, paso))

    # Deduplicar manteniendo orden
    vistos = set()
    pasos_unicos = []
    for pid, paso in pasos_relevantes:
        if pid not in vistos:
            vistos.add(pid)
            pasos_unicos.append((pid, paso))

    for i, (paso_id, paso) in enumerate(pasos_unicos):
        schema += f"""### PASO {i+1}: {paso['nombre']}
**Pregunta clave:** {paso['pregunta_clave']}
{paso['descripcion']}

Acciones:
"""
        for accion in paso["acciones"]:
            schema += f"  - {accion}\n"

        if paso["consulta_pgvector"]:
            schema += f"\n📚 **Consulta pgvector:** {paso['consulta_pgvector']}\n"

        schema += f"\n**Output esperado:** {paso['output']}\n\n"

    # Datos disponibles
    if datos_disponibles:
        schema += f"\n## DATOS DISPONIBLES\n"
        for nombre, valores in datos_disponibles.items():
            n = len(valores) if isinstance(valores, list) else "?"
            schema += f"  - {nombre}: {n} periodos\n"

    tokens_est = sum(p["tokens_estimados"] for _, p in pasos_unicos)
    schema += f"\n---\n*Protocolo: {len(pasos_unicos)} pasos, ~{tokens_est} tokens por paso*\n"

    return schema, pasos_unicos


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PROTOCOLO DEL ANALISTA DE DATOS")
    print("=" * 70)

    print(f"\n  {len(PROTOCOLO)} pasos en el protocolo completo")
    print(f"  Tokens estimados total: ~{TOKENS_ESTIMADOS_TOTAL}")

    # Test: generar schema para diferentes preguntas
    preguntas = [
        "¿En qué fase del ciclo está la economía?",
        "¿Qué debería hacer el banco central?",
        "¿Qué riesgos ocultos hay?",
        "¿El tratamiento tuvo efecto causal?",
        "¿Cuánto vale esta inversión?",
    ]

    datos = {"pib": [1]*48, "inflacion": [1]*48, "desempleo": [1]*48}

    for p in preguntas:
        schema, pasos = generar_schema(p, datos)
        print(f"\n  \"{p}\"")
        print(f"    → {len(pasos)} pasos, ~{len(schema)} chars, ~{len(schema.split())} palabras")
        print(f"    → Pasos: {[pid for pid, _ in pasos]}")
