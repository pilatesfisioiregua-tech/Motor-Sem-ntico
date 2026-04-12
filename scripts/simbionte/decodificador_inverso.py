"""
Decodificador Inverso — Vector numerico → significado sintactico → texto para LLM
Fecha: 2026-04-12

Pipeline forward:  texto → sintaxis → numeros → calculos → geometria
Pipeline inverso:  geometria → calculos → significado → texto decodificado

El texto decodificado va al LLM como input estructurado en prompt caching.
Junto con el match de pgvector (si existe) y la instruccion de catalogacion.

Ref: CAPA_0_ESPECIFICACION.md §4.bis "Catalogo de decodificacion"
"""

import numpy as np
from marcos_matematicos import FEATURES_POR_EJE, MARCOS


# ============================================================
# DICCIONARIO DE DECODIFICACION
# Cada feature tiene un significado sintactico que se puede verbalizar
# ============================================================

DECODIFICACION = {
    "estadistica": {
        "nombres": ["entropia", "diversidad", "concentracion", "dominante", "top2", "asimetria", "curtosis", "raros"],
        "traducciones": [
            ("entropia", "> 3.0", "alta diversidad de funciones — el texto usa muchos tipos diferentes"),
            ("entropia", "< 1.5", "baja diversidad — el texto repite las mismas funciones"),
            ("concentracion", "> 0.6", "pocas funciones dominan — el discurso esta concentrado"),
            ("dominante", "> 0.3", "una sola funcion domina >30% del texto"),
            ("asimetria", "> 1.0", "distribucion muy asimetrica — hay outliers funcionales"),
            ("raros", "> 0.5", "muchas funciones raras — texto atipico o rico en matices"),
        ],
    },
    "conjuntos": {
        "nombres": ["jaccard", "exclusivas_a", "exclusivas_b", "cobertura", "simetria_conj"],
        "traducciones": [
            ("jaccard", "> 0.7", "primera y segunda mitad del texto usan funciones similares — coherente"),
            ("jaccard", "< 0.3", "primera y segunda mitad usan funciones distintas — hay un giro"),
            ("simetria_conj", "> 0.8", "equilibrio entre las dos mitades"),
            ("simetria_conj", "< 0.4", "desequilibrio fuerte — una mitad tiene funciones que la otra no"),
        ],
    },
    "grafos": {
        "nombres": ["profundidad", "grado_medio", "betweenness_max", "n_componentes", "densidad", "ratio_hojas", "reciprocidad", "clustering"],
        "traducciones": [
            ("profundidad", "> 0.3", "arbol de dependencias profundo — razonamiento encadenado"),
            ("betweenness_max", "> 0.3", "hay un cuello de botella retorico — un nodo conecta todo"),
            ("n_componentes", "> 3", "pensamiento fragmentado en multiples lineas desconectadas"),
            ("reciprocidad", "> 0.3", "relaciones bidireccionales — interaccion entre partes"),
            ("clustering", "> 0.4", "estructura en grupos densos — argumentos locales fuertes"),
        ],
    },
    "markov": {
        "nombres": ["h_dist", "h_trans", "estructura", "diagonal", "est_0", "est_1", "est_2"],
        "traducciones": [
            ("estructura", "> 1.0", "secuencia muy estructurada — transiciones predecibles, no aleatorias"),
            ("estructura", "< 0.3", "secuencia poco estructurada — transiciones casi aleatorias"),
            ("diagonal", "> 0.4", "tendencia a repetir el mismo tipo — monotonia secuencial"),
            ("diagonal", "< 0.1", "alta variedad secuencial — cada tipo va seguido de otro diferente"),
        ],
    },
    "juegos": {
        "nombres": ["n_agentes", "n_condicionales", "cruce", "simetria_juego", "alternancia", "completitud"],
        "traducciones": [
            ("n_agentes", "> 3", "multiples agentes en juego — conflicto multipartito"),
            ("cruce", "== 1.0", "condicionales cruzados detectados — Nash posible: cada agente condiciona al otro"),
            ("simetria_juego", "> 0.8", "agentes con peso similar — equilibrio simetrico"),
            ("simetria_juego", "< 0.4", "asimetria fuerte entre agentes — uno domina"),
            ("alternancia", "> 0.7", "alta alternancia entre tipos — tension/conflicto en la secuencia"),
            ("completitud", "> 0.3", "muchas combinaciones de estrategias exploradas — analisis exhaustivo"),
        ],
    },
    "cibernetica": {
        "nombres": ["n_ciclos", "prof_ciclo", "amplificacion", "regulacion", "ratio_feedback"],
        "traducciones": [
            ("n_ciclos", "> 5", "multiples ciclos de feedback — sistema altamente interconectado"),
            ("amplificacion", "== 1.0", "feedback POSITIVO detectado — el sistema se autoamplifica (inestable)"),
            ("regulacion", "== 1.0", "feedback NEGATIVO detectado — hay mecanismo de freno (estable)"),
            ("amplificacion", "== 1.0", "SIN regulacion — feedback destructivo sin contrapeso"),
            ("ratio_feedback", "> 0.7", "mayoria de ciclos son amplificadores — sistema en escalada"),
        ],
    },
    "sistemas": {
        "nombres": ["prof_max", "prof_media", "n_subsistemas", "equilibrio", "emergencia", "coherencia_sis"],
        "traducciones": [
            ("n_subsistemas", "> 5", "sistema complejo con muchas partes"),
            ("emergencia", "== 1.0", "la conclusion del texto NO esta en las premisas — salto logico (emergencia)"),
            ("coherencia_sis", "> 0.7", "las partes son coherentes entre si"),
            ("coherencia_sis", "< 0.3", "las partes se contradicen o son incoherentes"),
            ("equilibrio", "> 0.7", "subsistemas de tamano similar — equilibrado"),
            ("equilibrio", "< 0.3", "subsistemas muy desiguales — desequilibrio estructural"),
        ],
    },
    "topologia": {
        "nombres": ["n_comp_topo", "agujeros", "ratio_agujeros", "compacidad", "persistencia", "convexidad_topo"],
        "traducciones": [
            ("agujeros", "> 5", "multiples funciones esperadas AUSENTES — gaps en la argumentacion"),
            ("compacidad", "> 0.7", "argumento compacto — todo apunta al mismo sitio"),
            ("compacidad", "< 0.3", "argumento disperso — funciones esparcidas sin foco"),
            ("persistencia", "> 0.7", "patron robusto — si quitas una pieza, la estructura se mantiene"),
            ("persistencia", "< 0.3", "patron fragil — depende de pocas piezas clave"),
        ],
    },
    "geometria": {
        "nombres": ["curvatura_media", "curvatura_max", "torsion", "ratio_inflexion", "ratio_curv_if"],
        "traducciones": [
            ("curvatura_media", "> 0.5", "el discurso gira mucho — cambios de direccion frecuentes"),
            ("curvatura_max", "> 1.0", "hay un giro BRUSCO — contradiccion o cambio radical"),
            ("torsion", "> 0.3", "la curvatura cambia — el ritmo de giro no es constante"),
            ("ratio_inflexion", "> 0.3", "multiples puntos de inflexion — el discurso zigzaguea"),
        ],
    },
    "cinematica": {
        "nombres": ["vel_media", "vel_max", "aceleracion", "bruscos", "coherencia_dir", "desplazamiento"],
        "traducciones": [
            ("vel_media", "> 0.3", "ritmo rapido de cambio estructural"),
            ("vel_media", "< 0.05", "ritmo lento — texto estable y repetitivo"),
            ("aceleracion", "> 0.1", "el texto se acelera — tension creciente"),
            ("aceleracion", "< -0.1", "el texto se frena — resolucion o cierre"),
            ("bruscos", "> 0.2", "cambios abruptos — giros de guion"),
            ("coherencia_dir", "> 0.5", "el discurso va en una direccion consistente"),
            ("coherencia_dir", "< 0", "el discurso cambia de direccion — incoherencia o deliberacion"),
            ("desplazamiento", "> 0.5", "el texto termina lejos de donde empezo — hubo transformacion"),
            ("desplazamiento", "< 0.1", "el texto termina donde empezo — circular o sin progreso"),
        ],
    },
}

NIVEL_NOMBRES = {
    "N1": "TOKENS (micro: cada palabra)",
    "N2": "ORACIONES (meso: cada oracion)",
    "N3": "PARRAFOS (macro: cada parrafo)",
    "N4": "TEXTO (global: movimientos cognitivos)",
}


# ============================================================
# DECODIFICADOR
# ============================================================

def decodificar_nivel(vector_nivel, nivel_id):
    """Decodifica un vector de 62 features a texto legible.

    Args:
        vector_nivel: np.array de 62 features
        nivel_id: "N1", "N2", "N3" o "N4"

    Returns:
        str: texto decodificado para el LLM
    """
    lines = []
    lines.append(f"## {nivel_id}: {NIVEL_NOMBRES.get(nivel_id, nivel_id)}")

    pos = 0
    marcos_activos = []

    for marco, n_feat in FEATURES_POR_EJE.items():
        features = vector_nivel[pos:pos + n_feat]
        pos += n_feat

        norma = float(np.linalg.norm(features))
        if norma < 0.1:
            continue  # Marco inactivo — no decodificar

        marcos_activos.append(marco)
        decos = DECODIFICACION.get(marco, {})
        nombres = decos.get("nombres", [])
        traducciones = decos.get("traducciones", [])

        hallazgos = []
        for nombre_feat, condicion, texto_trad in traducciones:
            idx = nombres.index(nombre_feat) if nombre_feat in nombres else -1
            if idx == -1 or idx >= len(features):
                continue
            valor = features[idx]

            # Evaluar condicion
            cumple = False
            if condicion.startswith("> "):
                cumple = valor > float(condicion[2:])
            elif condicion.startswith("< "):
                cumple = valor < float(condicion[2:])
            elif condicion.startswith("== "):
                cumple = abs(valor - float(condicion[3:])) < 0.1
            elif condicion.startswith(">= "):
                cumple = valor >= float(condicion[3:])

            if cumple:
                hallazgos.append(f"  - {texto_trad} ({nombre_feat}={valor:.2f})")

        if hallazgos:
            lines.append(f"\n### {marco.upper()} (norma={norma:.2f})")
            lines.extend(hallazgos)

    if not marcos_activos:
        lines.append("  (sin marcos activos en este nivel)")

    return "\n".join(lines)


def decodificar_geometria(geo_result):
    """Decodifica la geometria a texto legible.

    Args:
        geo_result: output de calcular_geometria_completa()

    Returns:
        str: texto decodificado
    """
    lines = ["## GEOMETRIA (forma del isomorfismo)"]

    # Forma por nivel
    for nivel in ["N1", "N2", "N3", "N4"]:
        if nivel not in geo_result["geometrias"]:
            continue
        g = geo_result["geometrias"][nivel]
        f = g["forma"]
        dom = f["dominantes"]
        if dom:
            lines.append(f"\n{nivel} forma dominada por: {', '.join(dom)}")
            lines.append(f"  Simetria={f['simetria']:.2f} Coherencia={f['coherencia']:.2f} Polarizacion={f['polarizacion']:.2f}")

    # Similaridad entre niveles
    lines.append("\n### PROFUNDIDAD DEL PATRON")
    for pair, s in geo_result.get("similaridades", {}).items():
        homo = s["homomorfismo"]
        if homo > 0.7:
            lines.append(f"  {pair}: homomorfismo={homo:.2f} — MISMO patron en ambos niveles")
        elif homo > 0.4:
            lines.append(f"  {pair}: homomorfismo={homo:.2f} — patron SIMILAR entre niveles")
        else:
            lines.append(f"  {pair}: homomorfismo={homo:.2f} — patrones DIFERENTES entre niveles")

    prof = geo_result.get("profundidad_patron", 0)
    if prof > 0.7:
        lines.append(f"\n  PROFUNDIDAD GLOBAL: {prof:.2f} — patron PROFUNDO (permea todas las escalas)")
    elif prof > 0.4:
        lines.append(f"\n  PROFUNDIDAD GLOBAL: {prof:.2f} — patron MEDIO (presente en algunos niveles)")
    else:
        lines.append(f"\n  PROFUNDIDAD GLOBAL: {prof:.2f} — patron SUPERFICIAL (solo micro)")

    return "\n".join(lines)


def decodificar_numeros_adj(num_como_adj):
    """Decodifica los numeros reclasificados como adjetivos."""
    if not num_como_adj:
        return ""

    lines = ["## NUMEROS COMO ADJETIVOS"]
    for texto, info in num_como_adj.items():
        func = info["funcion"]
        head = info["head"]
        if func == "num_posesivo":
            lines.append(f"  \"{texto}\" → POSESIVO: vincula dato a poseedor (modifica \"{head}\")")
        elif func == "num_calif_espec":
            lines.append(f"  \"{texto}\" → ESPECIFICATIVO: posiciona \"{head}\" en un eje cuantitativo")
        elif func == "num_predicativo":
            lines.append(f"  \"{texto}\" → PREDICATIVO: el dato ES el atributo de \"{head}\"")
        elif func == "num_indefinido":
            lines.append(f"  \"{texto}\" → INDEFINIDO: matiz de insuficiencia/imprecision sobre \"{head}\"")
        elif func == "num_calif_explic":
            lines.append(f"  \"{texto}\" → EXPLICATIVO: atribuye cualidad valorativa a \"{head}\"")
        else:
            lines.append(f"  \"{texto}\" → CARDINAL: cantidad simple que modifica \"{head}\"")

    lines.append("  Nota: cada dato numerico califica a su sujeto posicionandolo en un eje, como un adjetivo.")
    return "\n".join(lines)


# ============================================================
# CONSTRUIR PROMPT COMPLETO PARA LLM (prompt caching)
# ============================================================

def construir_prompt_decodificado(vectores_por_nivel, geo_result, num_como_adj=None,
                                   match_pgvector=None, tono=None):
    """Construye el prompt completo decodificado para el LLM.

    Este texto va en el system prompt con prompt caching (TTL 5 min, coste 1/10).

    Args:
        vectores_por_nivel: dict {"N1": array, "N2": array, ...}
        geo_result: output de calcular_geometria_completa()
        num_como_adj: dict de numeros reclasificados
        match_pgvector: dict con match encontrado (o None)
        tono: str ("frio", "templado", "caliente", "incierto")

    Returns:
        str: prompt decodificado completo
    """
    secciones = []

    # 1. Decodificacion por nivel (solo marcos activos con hallazgos)
    secciones.append("# ANALISIS ESTRUCTURAL (decodificado del Simbionte)")
    secciones.append("Cada hallazgo tiene evidencia numerica verificable.\n")

    for nivel_id in ["N1", "N2", "N3", "N4"]:
        if nivel_id in vectores_por_nivel:
            decoded = decodificar_nivel(vectores_por_nivel[nivel_id], nivel_id)
            if "sin marcos activos" not in decoded:
                secciones.append(decoded)

    # 2. Geometria
    secciones.append("\n" + decodificar_geometria(geo_result))

    # 3. Numeros como adjetivos
    if num_como_adj:
        secciones.append("\n" + decodificar_numeros_adj(num_como_adj))

    # 4. Match pgvector (precedente)
    if match_pgvector:
        secciones.append(f"\n## PRECEDENTE (match en catalogo, similitud={match_pgvector.get('similitud', '?')})")
        secciones.append(f"  Nombre: {match_pgvector.get('nombre', '?')}")
        secciones.append(f"  Definicion: {match_pgvector.get('definicion', '?')}")
        secciones.append(f"  Contexto previo: {match_pgvector.get('contexto', '?')}")
        secciones.append(f"  Usa este precedente como ancla, pero verifica si aplica al caso actual.")
    else:
        secciones.append("\n## SIN PRECEDENTE EN CATALOGO")
        secciones.append("  No hay match en pgvector. Si identificas un patron estructural recurrente,")
        secciones.append("  proponlo como candidato a isomorfismo nuevo en el campo 'candidato_isomorfismo'")
        secciones.append("  con: nombre, definicion, ejes_dominantes, nivel_profundidad.")

    # 5. Tono detectado
    if tono:
        secciones.append(f"\n## TONO DETECTADO: {tono}")
        if tono == "frio":
            secciones.append("  Texto directo, sin tension. Respuesta clinica.")
        elif tono == "caliente":
            secciones.append("  Texto con tension alta. Protocolo de desescalada.")
        elif tono == "incierto":
            secciones.append("  Baja confianza. Hacer pregunta clarificadora.")

    return "\n".join(secciones)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import time
    import spacy
    from poc_capa0_v6 import calcular_vector_v6
    from geometria_isomorfismo import calcular_geometria_completa
    from marcos_matematicos import FEATURES_POR_NIVEL as FPN

    nlp = spacy.load("es_dep_news_trf")

    with open("/tmp/texto_financiero.txt") as f:
        texto = f.read().strip()

    doc = nlp(texto)
    vector_v6, meta = calcular_vector_v6(doc)

    vectores = {
        "N1": vector_v6[0:FPN],
        "N2": vector_v6[FPN:2*FPN],
        "N3": vector_v6[2*FPN:3*FPN],
        "N4": vector_v6[3*FPN:4*FPN],
    }

    geo = calcular_geometria_completa(vectores)

    # Simular nums reclasificados
    num_adj = {
        "47": {"funcion": "num_posesivo", "head": "millones"},
        "340": {"funcion": "num_posesivo", "head": "euros"},
        "1.200": {"funcion": "num_indefinido", "head": "euros"},
        "ocho": {"funcion": "num_predicativo", "head": "por ciento"},
        "treinta": {"funcion": "num_calif_espec", "head": "rotacion"},
    }

    prompt = construir_prompt_decodificado(
        vectores, geo,
        num_como_adj=num_adj,
        match_pgvector=None,  # Sin match — patron nuevo
        tono="frio",
    )

    print(prompt)
    print(f"\n{'='*60}")
    print(f"TOKENS ESTIMADOS: ~{len(prompt.split()) * 1.3:.0f} tokens")
    print(f"COSTE PROMPT CACHING (primera): ~${len(prompt.split()) * 1.3 * 3 / 1_000_000:.4f}")
    print(f"COSTE PROMPT CACHING (siguientes): ~${len(prompt.split()) * 1.3 * 0.3 / 1_000_000:.5f}")
