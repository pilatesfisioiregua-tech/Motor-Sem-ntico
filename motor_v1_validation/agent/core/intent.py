"""Intent translator — de lenguaje de negocio a goal tecnico. $0, sin LLM."""

BUSINESS_KEYWORDS = {
    "coste": [
        "coste", "costo", "gasto", "presupuesto", "caro", "barato",
        "dinero", "euro", "dólar", "dollar", "precio", "factura",
        "cuánto he gastado", "cuanto he gastado", "cuánto cuesta", "cuanto cuesta",
    ],
    "rendimiento": [
        "lento", "rápido", "rapido", "tarda", "latencia", "velocidad",
        "rendimiento", "performance", "timeout", "demora", "responde lento",
    ],
    "error": [
        "error", "falla", "roto", "no funciona", "crashea", "bug",
        "problema", "broken", "failing", "caído", "caido", "down",
    ],
    "datos": [
        "datos", "pilotos", "pilates", "fisio", "clientes", "exocortex",
        "sin datos", "no tienen datos", "vacío", "vacio", "falta información",
    ],
    "estado": [
        "estado", "cómo está", "como esta", "salud", "funcionando",
        "check", "status", "health", "resumen", "overview",
    ],
    "feature": [
        "quiero", "necesito", "añadir", "crear", "nuevo", "feature",
        "implementar", "agregar", "construir", "montar",
    ],
    "diagnostico": [
        "por qué", "por que", "diagnóstico", "diagnostico", "investigar",
        "analizar", "analiza", "revisar", "revisa", "qué pasa", "que pasa",
    ],
}

TECHNICAL_GOALS = {
    "coste": (
        "Ejecuta estas queries y reporta resultados:\n"
        "1. SELECT consumidor, ROUND(SUM(coste_total_usd)::numeric, 4) as total "
        "FROM costes_llm WHERE date_trunc('month', created_at) = date_trunc('month', now()) "
        "GROUP BY consumidor ORDER BY total DESC;\n"
        "2. SELECT modelo, COUNT(*) as llamadas, ROUND(SUM(coste_total_usd)::numeric, 4) as total "
        "FROM costes_llm WHERE created_at > now() - interval '30 days' "
        "GROUP BY modelo ORDER BY total DESC LIMIT 10;\n"
        "3. SELECT consumidor, limite_mensual_usd FROM presupuestos WHERE activo = true;\n"
        "Resume: gasto actual, modelo mas caro, proyeccion mensual."
    ),
    "rendimiento": (
        "Ejecuta diagnostico de rendimiento:\n"
        "1. SELECT componente, evento, AVG((datos->>'latencia_ms')::int) as lat_media "
        "FROM metricas WHERE created_at > now() - interval '24 hours' "
        "AND datos ? 'latencia_ms' GROUP BY componente, evento ORDER BY lat_media DESC;\n"
        "2. Verifica endpoints: /health, /propiocepcion, /costes/resumen\n"
        "3. SELECT COUNT(*) FROM metricas WHERE created_at > now() - interval '1 hour';\n"
        "Si detectas SLOs rotos con fix claro → ARRÉGLALO.\n"
        "Resume: latencias, qué arreglaste."
    ),
    "error": (
        "Diagnostica errores activos:\n"
        "1. db_query('SELECT tipo, severidad, mensaje, created_at FROM señales "
        "WHERE resuelta = false ORDER BY created_at DESC LIMIT 10')\n"
        "2. db_query('SELECT componente, evento, datos FROM metricas "
        "WHERE datos->>error IS NOT NULL AND created_at > now() - interval 24 hours "
        "ORDER BY created_at DESC LIMIT 5')\n"
        "3. db_query('SELECT COUNT(*) FROM marcas_estigmergicas "
        "WHERE consumida = false AND tipo = alerta')\n"
        "Para cada error: si puedes arreglarlo → ARRÉGLALO. Si no → explica POR QUÉ no puedes.\n"
        "Resume: qué arreglaste, qué queda."
    ),
    "datos": (
        "Ejecuta diagnostico de datos:\n"
        "1. SELECT id, nombre, config->>'fase' as fase FROM exocortex_estado WHERE activo = true;\n"
        "2. SELECT consumidor, COUNT(*) as n FROM datapoints_efectividad "
        "WHERE created_at > now() - interval '7 days' GROUP BY consumidor ORDER BY n DESC;\n"
        "3. SELECT inteligencia, COUNT(*) as gaps FROM preguntas_matriz "
        "WHERE nivel != 'podada' GROUP BY inteligencia ORDER BY gaps DESC LIMIT 10;\n"
        "Resume: pilotos activos, datapoints recientes, gaps principales."
    ),
    "estado": (
        "PRIMERO consulta mochila('sistema') para contexto y problemas conocidos.\n"
        "Luego revisa el estado via endpoints HTTP (usa http_request a http://localhost:8080):\n"
        "1. http_request('GET', 'http://localhost:8080/propiocepcion')\n"
        "2. http_request('GET', 'http://localhost:8080/gestor/autopoiesis')\n"
        "3. http_request('GET', 'http://localhost:8080/costes/resumen')\n"
        "4. db_query('SELECT COUNT(*) FROM señales WHERE resuelta = false')\n"
        "5. db_query('SELECT COUNT(*) FROM metricas WHERE created_at > now() - interval 1 hour')\n"
        "Si encuentras algo roto → ARRÉGLALO si está en tu capacidad.\n"
        "Resume: estado general, lo que arreglaste, lo que necesita atención del CEO."
    ),
    "feature": (
        "Investiga antes de proponer:\n"
        "1. SELECT titulo, contenido FROM knowledge_base WHERE tipo = 'diseno' "
        "ORDER BY created_at DESC LIMIT 5;\n"
        "2. Lee los briefings existentes en @project/../../briefings/\n"
        "3. Propone plan con: archivos a crear/modificar, dependencias, riesgos.\n"
        "NO implementes todavia — solo propone via submit_design()."
    ),
    "diagnostico": (
        "PRIMERO consulta mochila('sistema') para ver problemas conocidos y no reportarlos como nuevos.\n"
        "Luego diagnostica el estado completo via endpoints HTTP (usa http_request a http://localhost:8080):\n"
        "1. http_request('GET', 'http://localhost:8080/health')\n"
        "2. http_request('GET', 'http://localhost:8080/gestor/autopoiesis')\n"
        "3. http_request('GET', 'http://localhost:8080/criticality/temperatura')\n"
        "4. http_request('GET', 'http://localhost:8080/criticality/avalanchas')\n"
        "5. http_request('GET', 'http://localhost:8080/propiocepcion')\n"
        "6. http_request('GET', 'http://localhost:8080/costes/resumen')\n"
        "7. db_query('SELECT tipo, COUNT(*) FROM señales WHERE resuelta = false GROUP BY tipo')\n"
        "8. db_query('SELECT componente, COUNT(*) FROM metricas WHERE created_at > now() - interval 24h GROUP BY componente')\n"
        "Para cada hallazgo NUEVO: si puedes arreglarlo → ARRÉGLALO. Tras cada arreglo → remember_save().\n"
        "Resume: qué encontraste, qué arreglaste, qué queda pendiente."
    ),
}

EXPLANATIONS = {
    "coste": "Voy a revisar los gastos del sistema — cuánto has gastado, en qué modelos, y si vas dentro del presupuesto.",
    "rendimiento": "Voy a comprobar la velocidad del sistema — latencias, tiempos de respuesta, y si hay cuellos de botella.",
    "error": "Voy a buscar errores activos — alertas pendientes, fallos recientes, y qué está roto.",
    "datos": "Voy a revisar el estado de los datos — pilotos activos, datapoints, y si falta información.",
    "estado": "Voy a hacer un chequeo general del sistema — todo: estado, alertas, costes, actividad.",
    "feature": "Voy a investigar qué existe ya y proponer un plan antes de implementar nada.",
    "diagnostico": "Voy a investigar a fondo — datos, errores, rendimiento, todo lo que pueda explicar qué pasa.",
}


def translate_intent(user_input: str, system_context: dict = None) -> dict:
    """Translate business language to technical goal.

    Args:
        user_input: Natural language from user (e.g. "cuánto he gastado este mes")
        system_context: Optional system state for context-aware translation

    Returns:
        {category, technical_goal, explanation_for_user, original_input}
    """
    if system_context is None:
        system_context = {}

    input_lower = user_input.lower()

    # Score each category by keyword matches
    scores = {}
    for category, keywords in BUSINESS_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in input_lower:
                # Longer keywords get more weight (multi-word phrases are more specific)
                score += len(kw.split())
        if score > 0:
            scores[category] = score

    if not scores:
        # No match — pass through as-is (assumed technical)
        return {
            "category": None,
            "technical_goal": user_input,
            "explanation_for_user": None,
            "original_input": user_input,
        }

    # Pick highest scoring category
    category = max(scores, key=scores.get)

    return {
        "category": category,
        "technical_goal": TECHNICAL_GOALS[category],
        "explanation_for_user": EXPLANATIONS[category],
        "original_input": user_input,
    }
