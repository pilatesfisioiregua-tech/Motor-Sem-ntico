"""
10 Marcos Matematicos del Simbionte — Funcion reutilizable por nivel
Fecha: 2026-04-12

Cada marco opera sobre una secuencia de codigos funcionales y produce un sub-vector.
Los 10 sub-vectores concatenados = vector-isomorfismo de ese nivel.

Se aplica UNIFORMEMENTE a los 4 niveles:
  N1 (tokens), N2 (oraciones), N3 (parrafos), N4 (texto)
Y a las transiciones inter-nivel: N1↔N2, N2↔N3, N3↔N4.

Ref: CAPA_0_ESPECIFICACION.md §3 "Los 10 marcos matematicos"
Ref: CAPA_0_ESPECIFICACION.md §3.bis "Analisis multi-escala"

Total: 62 features por nivel × 4 niveles = 248D + ~18D inter-nivel = ~266D
"""

import numpy as np
from collections import Counter
from scipy import stats
from scipy.linalg import eig
import networkx as nx


# ============================================================
# EJE 1: ESTADISTICA DESCRIPTIVA (8 features)
# ============================================================

def eje_estadistica(seq, n_tipos):
    """Proporciones, frecuencias, ratios sobre codigos funcionales."""
    if len(seq) < 2:
        return [0.0] * 8

    n = len(seq)
    counts = Counter(seq)
    probs = np.zeros(n_tipos)
    for s, c in counts.items():
        if 0 <= s < n_tipos:
            probs[s] = c / n

    # Entropia de la distribucion
    ps = probs[probs > 0]
    entropia = float(stats.entropy(ps, base=2)) if len(ps) > 1 else 0.0

    # Diversidad (n tipos unicos / n tipos posibles)
    diversidad = len(counts) / max(n_tipos, 1)

    # Concentracion (Gini simplificado)
    sorted_p = np.sort(probs[probs > 0])[::-1]
    gini = 1.0 - float(np.sum(sorted_p ** 2)) if len(sorted_p) > 0 else 0.0

    # Tipo dominante (proporcion del mas frecuente)
    dominante = float(max(probs)) if len(probs) > 0 else 0.0

    # Ratio top2/total
    top2 = float(sum(sorted(counts.values(), reverse=True)[:2])) / n if counts else 0.0

    # Asimetria (skewness de la distribucion)
    asimetria = float(stats.skew(probs[probs > 0])) if len(ps) > 2 else 0.0

    # Curtosis
    curtosis = float(stats.kurtosis(probs[probs > 0])) if len(ps) > 3 else 0.0

    # Ratio tipos raros (<5% de ocurrencias) / total tipos
    raros = sum(1 for p in probs if 0 < p < 0.05) / max(len(counts), 1)

    return [entropia, diversidad, gini, dominante, top2, asimetria, curtosis, raros]


# ============================================================
# EJE 2: TEORIA DE CONJUNTOS (5 features)
# ============================================================

def eje_conjuntos(seq, seq_ref=None):
    """Pertenencia, exclusion, interseccion entre conjuntos de funciones.

    Si seq_ref es None, compara primera mitad vs segunda mitad del texto.
    """
    if len(seq) < 4:
        return [0.0] * 5

    if seq_ref is None:
        mid = len(seq) // 2
        set_a = set(seq[:mid])
        set_b = set(seq[mid:])
    else:
        set_a = set(seq)
        set_b = set(seq_ref)

    union = set_a | set_b
    inter = set_a & set_b
    only_a = set_a - set_b
    only_b = set_b - set_a

    jaccard = len(inter) / max(len(union), 1)
    exclusivas_a = len(only_a) / max(len(set_a), 1)
    exclusivas_b = len(only_b) / max(len(set_b), 1)
    cobertura = len(inter) / max(len(set_b), 1)
    simetria = 1.0 - abs(len(only_a) - len(only_b)) / max(len(union), 1)

    return [jaccard, exclusivas_a, exclusivas_b, cobertura, simetria]


# ============================================================
# EJE 3: GRAFOS / REDES (8 features)
# ============================================================

def eje_grafos(seq, edges=None):
    """Propiedades del grafo de transiciones entre codigos.

    Si edges es None, construye grafo de transiciones de la secuencia.
    Si edges se provee, usa ese grafo directamente (para nivel token con deps).
    """
    if len(seq) < 3:
        return [0.0] * 8

    G = nx.DiGraph()

    if edges is not None:
        for u, v in edges:
            G.add_edge(u, v)
    else:
        # Grafo de transiciones
        for i in range(len(seq) - 1):
            G.add_edge(seq[i], seq[i + 1])

    if G.number_of_nodes() < 2:
        return [0.0] * 8

    # Profundidad (aproximada para grafos grandes)
    try:
        if G.number_of_nodes() < 50 and nx.is_directed_acyclic_graph(G):
            prof = nx.dag_longest_path_length(G)
        else:
            # Aproximacion: max de shortest paths desde nodos con in-degree=0
            roots = [n for n in G.nodes() if G.in_degree(n) == 0]
            if roots:
                prof = max(max(nx.single_source_shortest_path_length(G, r).values()) for r in roots[:5])
            else:
                prof = 0
    except Exception:
        prof = 0
    prof_norm = prof / max(G.number_of_nodes(), 1)

    # Grado medio
    grado_medio = float(np.mean([d for _, d in G.degree()])) if G.number_of_nodes() > 0 else 0.0

    # Betweenness max (sampled para grafos grandes)
    try:
        if G.number_of_nodes() > 100:
            bc = nx.betweenness_centrality(G, k=min(50, G.number_of_nodes()))
        else:
            bc = nx.betweenness_centrality(G)
        bc_max = float(max(bc.values())) if bc else 0.0
    except Exception:
        bc_max = 0.0

    # Componentes conexas (weakly)
    n_comp = float(nx.number_weakly_connected_components(G))

    # Densidad
    densidad = nx.density(G)

    # Ratio hojas (nodos sin sucesores)
    n_hojas = sum(1 for n in G.nodes() if G.out_degree(n) == 0)
    ratio_hojas = n_hojas / max(G.number_of_nodes(), 1)

    # Reciprocidad (% de aristas bidireccionales)
    reciprocidad = nx.reciprocity(G) if G.number_of_edges() > 0 else 0.0

    # Clustering medio (sobre version no dirigida)
    try:
        clustering = nx.average_clustering(G.to_undirected())
    except Exception:
        clustering = 0.0

    return [prof_norm, grado_medio, bc_max, n_comp, densidad, ratio_hojas, reciprocidad, clustering]


# ============================================================
# EJE 4: CADENAS DE MARKOV (7 features)
# ============================================================

def eje_markov(seq, n_estados):
    """Transiciones entre codigos y dinamica secuencial."""
    if len(seq) < 3:
        return [0.0] * 7

    counts = Counter(seq)
    total = len(seq)
    probs = np.zeros(n_estados)
    for s, c in counts.items():
        if 0 <= s < n_estados:
            probs[s] = c / total

    ps = probs[probs > 0]
    h_dist = float(stats.entropy(ps, base=2)) if len(ps) > 1 else 0.0

    # Matriz de transicion
    T = np.zeros((n_estados, n_estados))
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i + 1]
        if 0 <= a < n_estados and 0 <= b < n_estados:
            T[a, b] += 1
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    T = T / row_sums

    # Entropia de transicion
    h_trans = 0.0
    for i in range(n_estados):
        if probs[i] > 0:
            row = T[i][T[i] > 0]
            if len(row) > 0:
                h_trans += probs[i] * float(stats.entropy(row, base=2))

    # Estructura = h_dist - h_trans
    estructura = h_dist - h_trans

    # Diagonal media (monotonia)
    diagonal = float(np.mean(np.diag(T)))

    # Distribucion estacionaria
    try:
        eigenvalues, eigenvectors = eig(T.T)
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        stationary = np.abs(eigenvectors[:, idx].real)
        s_sum = stationary.sum()
        stationary = stationary / s_sum if s_sum > 1e-10 else probs
    except Exception:
        stationary = probs

    est_0 = float(stationary[0]) if len(stationary) > 0 else 0.0
    est_1 = float(stationary[1]) if len(stationary) > 1 else 0.0
    est_2 = float(stationary[2]) if len(stationary) > 2 else 0.0

    return [h_dist, h_trans, estructura, diagonal, est_0, est_1, est_2]


# ============================================================
# EJE 5: TEORIA DE JUEGOS (6 features)
# ============================================================

def eje_juegos(seq, agentes=None, condicionales=None):
    """Conflicto entre agentes/posiciones en la estructura.

    Args:
        seq: secuencia de codigos funcionales
        agentes: lista de IDs de agente por posicion (o None)
        condicionales: indices de posiciones condicionales (o None)
    """
    if len(seq) < 3:
        return [0.0] * 6

    # N agentes (tipos unicos de sujeto/agente en la secuencia)
    if agentes is not None:
        n_agentes = len(set(a for a in agentes if a is not None))
    else:
        n_agentes = len(set(seq))  # proxy: tipos unicos

    # N estrategias condicionales
    if condicionales is not None:
        n_cond = len(condicionales)
    else:
        # Proxy: cambios bruscos en la secuencia
        n_cond = sum(1 for i in range(len(seq) - 1) if seq[i] != seq[i + 1])

    # Cruce de condicionales (hay >=2 bloques con agente distinto?)
    cruce = 1.0 if n_agentes >= 2 and n_cond >= 2 else 0.0

    # Simetria entre agentes (igualdad de peso)
    if agentes is not None and len(set(a for a in agentes if a is not None)) >= 2:
        agent_counts = Counter(a for a in agentes if a is not None)
        vals = list(agent_counts.values())
        total = sum(vals)
        simetria = 1.0 - float(np.std([v / total for v in vals])) * 2
    else:
        # Proxy: simetria primera/segunda mitad
        mid = len(seq) // 2
        c1, c2 = Counter(seq[:mid]), Counter(seq[mid:])
        total = len(seq)
        simetria = 1.0 - abs(len(c1) - len(c2)) / max(len(c1) + len(c2), 1)

    # Polaridad (alternancia de tipos — proxy para payoffs opuestos)
    alternancia = sum(1 for i in range(len(seq) - 1) if seq[i] != seq[i + 1]) / max(len(seq) - 1, 1)

    # Completitud (cuantos pares de transicion existen vs posibles)
    pares_reales = len(set(zip(seq[:-1], seq[1:])))
    tipos_unicos = len(set(seq))
    pares_posibles = tipos_unicos * tipos_unicos
    completitud = pares_reales / max(pares_posibles, 1)

    return [float(n_agentes), float(n_cond), cruce, simetria, alternancia, completitud]


# ============================================================
# EJE 6: CIBERNETICA (5 features)
# ============================================================

def eje_cibernetica(seq, grafo_deps=None):
    """Bucles de retroalimentacion en la estructura."""
    if len(seq) < 3:
        return [0.0] * 5

    # Construir grafo de transiciones
    G = nx.DiGraph()
    for i in range(len(seq) - 1):
        G.add_edge(seq[i], seq[i + 1])

    if grafo_deps is not None:
        for u, v in grafo_deps:
            G.add_edge(u, v)

    # N ciclos (limitado a 100 para evitar explosion combinatoria en grafos grandes)
    try:
        ciclos = []
        for ciclo in nx.simple_cycles(G):
            ciclos.append(ciclo)
            if len(ciclos) >= 100:
                break
        n_ciclos = len(ciclos)
    except Exception:
        ciclos = []
        n_ciclos = 0

    # Profundidad media de ciclos
    if ciclos:
        prof_ciclo_media = float(np.mean([len(c) for c in ciclos]))
    else:
        prof_ciclo_media = 0.0

    # Tiene amplificacion (mismo tipo se repite en ciclo)
    tiene_amplif = 0.0
    for ciclo in ciclos:
        if len(ciclo) != len(set(ciclo)):  # hay repeticion
            tiene_amplif = 1.0
            break

    # Tiene regulacion (tipos distintos en ciclo = feedback negativo)
    tiene_regul = 0.0
    for ciclo in ciclos:
        if len(ciclo) == len(set(ciclo)) and len(ciclo) >= 2:
            tiene_regul = 1.0
            break

    # Ratio feedback: ciclos con repeticion / total ciclos
    if n_ciclos > 0:
        n_amplif = sum(1 for c in ciclos if len(c) != len(set(c)))
        ratio_fb = n_amplif / n_ciclos
    else:
        ratio_fb = 0.0

    return [float(n_ciclos), prof_ciclo_media, tiene_amplif, tiene_regul, ratio_fb]


# ============================================================
# EJE 7: TEORIA GENERAL DE SISTEMAS (6 features)
# ============================================================

def eje_sistemas(seq, niveles_anidacion=None):
    """Jerarquia, anidacion y relaciones parte-todo."""
    if len(seq) < 3:
        return [0.0] * 6

    n = len(seq)

    # Profundidad de anidacion (proxy: runs consecutivos del mismo tipo)
    runs = []
    current_run = 1
    for i in range(1, n):
        if seq[i] == seq[i - 1]:
            current_run += 1
        else:
            runs.append(current_run)
            current_run = 1
    runs.append(current_run)

    prof_max = max(runs) if runs else 0
    prof_media = float(np.mean(runs)) if runs else 0.0

    # N subsistemas (bloques contiguos del mismo tipo)
    n_subsistemas = len(runs)

    # Ratio tokens por nivel (proxy: distribucion de runs)
    run_sizes = np.array(runs, dtype=float)
    ratio_equilibrio = 1.0 - float(np.std(run_sizes) / max(np.mean(run_sizes), 1e-10))
    ratio_equilibrio = max(0.0, min(1.0, ratio_equilibrio))

    # Emergencia (el tipo final NO esta en los subsistemas anteriores)
    if n >= 3:
        tipo_final = seq[-1]
        tipos_previos = set(seq[:-max(n // 4, 1)])
        emergencia = 0.0 if tipo_final in tipos_previos else 1.0
    else:
        emergencia = 0.0

    # Coherencia parte-todo (similitud de subsistemas consecutivos)
    if len(runs) >= 2:
        # Proxy: cuantos subsistemas consecutivos son del mismo tipo
        coherencia = sum(1 for i in range(len(runs) - 1)
                        if i + 1 < n_subsistemas) / max(n_subsistemas - 1, 1)
        # Recalcular con tipos reales
        tipos_subs = []
        pos = 0
        for r in runs:
            tipos_subs.append(seq[pos])
            pos += r
        coherencia = sum(1 for i in range(len(tipos_subs) - 1)
                        if tipos_subs[i] == tipos_subs[i + 1]) / max(len(tipos_subs) - 1, 1)
    else:
        coherencia = 1.0

    return [float(prof_max), prof_media, float(n_subsistemas), ratio_equilibrio, emergencia, coherencia]


# ============================================================
# EJE 8: TOPOLOGIA (6 features)
# ============================================================

def eje_topologia(seq, n_tipos, funciones_esperadas=None):
    """Invariantes de forma del codigo funcional."""
    if len(seq) < 3:
        return [0.0] * 6

    presentes = set(seq)

    # N componentes conexas (del grafo de transiciones)
    G = nx.DiGraph()
    for i in range(len(seq) - 1):
        G.add_edge(seq[i], seq[i + 1])
    n_comp = float(nx.number_weakly_connected_components(G)) if G.number_of_nodes() > 0 else 1.0

    # Agujeros logicos (funciones esperadas ausentes)
    if funciones_esperadas is not None:
        agujeros = len(funciones_esperadas - presentes)
        ratio_agujeros = agujeros / max(len(funciones_esperadas), 1)
    else:
        # Proxy: tipos con frecuencia 0 que aparecen en otros textos
        agujeros = n_tipos - len(presentes)
        ratio_agujeros = agujeros / max(n_tipos, 1)

    # Compacidad (inversa de la dispersion de tipos)
    counts = Counter(seq)
    freqs = np.array([counts.get(i, 0) for i in range(n_tipos)], dtype=float)
    freqs_nonzero = freqs[freqs > 0]
    if len(freqs_nonzero) > 1:
        compacidad = 1.0 - float(np.std(freqs_nonzero) / max(np.mean(freqs_nonzero), 1e-10))
        compacidad = max(0.0, min(1.0, compacidad))
    else:
        compacidad = 1.0

    # Persistencia (robustez: si quito el tipo mas frecuente, cambia la estructura?)
    if len(presentes) >= 2:
        tipo_top = max(counts, key=counts.get)
        seq_sin_top = [s for s in seq if s != tipo_top]
        if len(seq_sin_top) >= 2:
            presentes_sin = set(seq_sin_top)
            persistencia = len(presentes_sin & presentes) / max(len(presentes), 1)
        else:
            persistencia = 0.0
    else:
        persistencia = 0.0

    # Convexidad (proxy: ratio de pares de transicion existentes vs envolvente)
    pares = set(zip(seq[:-1], seq[1:]))
    convexidad = len(pares) / max(len(presentes) ** 2, 1)

    return [n_comp, float(agujeros), ratio_agujeros, compacidad, persistencia, convexidad]


# ============================================================
# EJE 9: GEOMETRIA DIFERENCIAL (5 features)
# ============================================================

def eje_geometria_diferencial(seq, n_tipos):
    """Curvatura y cambio de la estructura a lo largo de la secuencia."""
    if len(seq) < 4:
        return [0.0] * 5

    # Convertir secuencia a serie de one-hot vectors
    window = max(len(seq) // 5, 3)
    centroids = []
    for i in range(0, len(seq) - window + 1, max(window // 2, 1)):
        chunk = seq[i:i + window]
        vec = np.zeros(min(n_tipos, 20))  # Limitar a 20 dims para eficiencia
        for s in chunk:
            if 0 <= s < len(vec):
                vec[s] += 1
        vec = vec / max(len(chunk), 1)
        centroids.append(vec)

    if len(centroids) < 3:
        return [0.0] * 5

    # Vectores de direccion
    dirs = [centroids[i + 1] - centroids[i] for i in range(len(centroids) - 1)]

    # Curvatura: 1 - cos(d_i, d_i+1)
    curvaturas = []
    for i in range(len(dirs) - 1):
        n1, n2 = np.linalg.norm(dirs[i]), np.linalg.norm(dirs[i + 1])
        if n1 > 1e-10 and n2 > 1e-10:
            cos_a = np.clip(np.dot(dirs[i], dirs[i + 1]) / (n1 * n2), -1, 1)
            curvaturas.append(1.0 - cos_a)

    if not curvaturas:
        return [0.0] * 5

    curv_media = float(np.mean(curvaturas))
    curv_max = float(max(curvaturas))

    # Torsion (cambio de curvatura)
    if len(curvaturas) >= 2:
        torsion = float(np.mean([abs(curvaturas[i + 1] - curvaturas[i]) for i in range(len(curvaturas) - 1)]))
    else:
        torsion = 0.0

    # Puntos de inflexion (donde cos < 0)
    n_inflexion = sum(1 for c in curvaturas if c > 1.0)  # cos < 0 → curvatura > 1
    ratio_inflexion = n_inflexion / max(len(curvaturas), 1)

    # Ratio curvatura inicio/fin
    if len(curvaturas) >= 2:
        tercio = max(len(curvaturas) // 3, 1)
        curv_inicio = float(np.mean(curvaturas[:tercio]))
        curv_fin = float(np.mean(curvaturas[-tercio:]))
        ratio_if = curv_inicio / max(curv_fin, 1e-10)
    else:
        ratio_if = 1.0

    return [curv_media, curv_max, torsion, ratio_inflexion, min(ratio_if, 5.0)]


# ============================================================
# EJE 10: CINEMATICA (6 features)
# ============================================================

def eje_cinematica(seq, n_tipos):
    """Movimiento del pensamiento a traves del espacio funcional."""
    if len(seq) < 4:
        return [0.0] * 6

    # Centroides por segmento
    n_segs = min(len(seq), 10)
    seg_size = max(len(seq) // n_segs, 1)
    centroids = []
    for i in range(0, len(seq), seg_size):
        chunk = seq[i:i + seg_size]
        vec = np.zeros(min(n_tipos, 20))
        for s in chunk:
            if 0 <= s < len(vec):
                vec[s] += 1
        vec = vec / max(len(chunk), 1)
        centroids.append(vec)

    if len(centroids) < 2:
        return [0.0] * 6

    # Velocidades
    vels = [float(np.linalg.norm(centroids[i + 1] - centroids[i])) for i in range(len(centroids) - 1)]

    vel_media = float(np.mean(vels))
    vel_max = float(max(vels))

    # Aceleracion
    if len(vels) >= 2:
        accel = float(np.mean([vels[i + 1] - vels[i] for i in range(len(vels) - 1)]))
    else:
        accel = 0.0

    # Cambios bruscos
    if len(vels) > 1:
        std_v = float(np.std(vels))
        n_bruscos = sum(1 for v in vels if v > vel_media + 2 * std_v) / max(len(vels), 1)
    else:
        n_bruscos = 0.0

    # Coherencia direccional
    if len(centroids) >= 3:
        dirs = [centroids[i + 1] - centroids[i] for i in range(len(centroids) - 1)]
        cohs = []
        for i in range(len(dirs) - 1):
            n1, n2 = np.linalg.norm(dirs[i]), np.linalg.norm(dirs[i + 1])
            if n1 > 1e-10 and n2 > 1e-10:
                cohs.append(float(np.dot(dirs[i], dirs[i + 1]) / (n1 * n2)))
        coherencia = float(np.mean(cohs)) if cohs else 0.0
    else:
        coherencia = 0.0

    # Desplazamiento total (distancia inicio-fin)
    desplazamiento = float(np.linalg.norm(centroids[-1] - centroids[0]))

    return [vel_media, vel_max, accel, n_bruscos, coherencia, desplazamiento]


# ============================================================
# FUNCION PRINCIPAL: calcular_10_ejes()
# ============================================================

FEATURES_POR_EJE = {
    "estadistica": 8,
    "conjuntos": 5,
    "grafos": 8,
    "markov": 7,
    "juegos": 6,
    "cibernetica": 5,
    "sistemas": 6,
    "topologia": 6,
    "geometria": 5,
    "cinematica": 6,
}
MARCOS = list(FEATURES_POR_EJE.keys())  # Los 10 marcos
FEATURES_POR_NIVEL = sum(FEATURES_POR_EJE.values())  # 62

FEATURE_NAMES_EJES = []
for eje, n in FEATURES_POR_EJE.items():
    for i in range(n):
        FEATURE_NAMES_EJES.append(f"{eje}_{i}")


def calcular_10_ejes(seq, n_tipos, edges=None, agentes=None, condicionales=None,
                     funciones_esperadas=None, seq_ref=None):
    """Calcula los 10 marcos matematicos sobre una secuencia de codigos.

    Args:
        seq: list[int] — secuencia de codigos funcionales (0-indexed)
        n_tipos: int — numero total de tipos posibles
        edges: list[(int,int)] — aristas del grafo de dependencias (opcional)
        agentes: list[int|None] — ID de agente por posicion (opcional, para juegos)
        condicionales: list[int] — indices de posiciones condicionales (opcional)
        funciones_esperadas: set[int] — funciones que deberian estar (opcional, para topologia)
        seq_ref: list[int] — secuencia de referencia (patron conocido, para conjuntos)

    Returns:
        np.array de 62 floats
    """
    v = []
    v.extend(eje_estadistica(seq, n_tipos))           # 8
    v.extend(eje_conjuntos(seq, seq_ref))              # 5
    v.extend(eje_grafos(seq, edges))                   # 8
    v.extend(eje_markov(seq, n_tipos))                 # 7
    v.extend(eje_juegos(seq, agentes, condicionales))  # 6
    v.extend(eje_cibernetica(seq))                     # 5
    v.extend(eje_sistemas(seq))                        # 6
    v.extend(eje_topologia(seq, n_tipos, funciones_esperadas))  # 6
    v.extend(eje_geometria_diferencial(seq, n_tipos))  # 5
    v.extend(eje_cinematica(seq, n_tipos))             # 6

    assert len(v) == FEATURES_POR_NIVEL, f"10 ejes: {len(v)} != {FEATURES_POR_NIVEL}"
    return np.array(v, dtype=np.float64)


# ============================================================
# INTER-NIVEL: transiciones entre escalas
# ============================================================

def calcular_inter_nivel(v_nivel_a, v_nivel_b):
    """Calcula relacion entre dos niveles adyacentes.

    Returns: 6 features de transicion inter-nivel
    """
    if len(v_nivel_a) == 0 or len(v_nivel_b) == 0:
        return [0.0] * 6

    # Correlacion entre vectores de los dos niveles
    min_len = min(len(v_nivel_a), len(v_nivel_b))
    a, b = v_nivel_a[:min_len], v_nivel_b[:min_len]

    # Correlacion
    if np.std(a) > 1e-10 and np.std(b) > 1e-10:
        corr = float(np.corrcoef(a, b)[0, 1])
    else:
        corr = 0.0

    # Distancia coseno
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na > 1e-10 and nb > 1e-10:
        cos_dist = 1.0 - float(np.dot(a, b) / (na * nb))
    else:
        cos_dist = 1.0

    # Ratio de magnitudes
    ratio_mag = float(na / max(nb, 1e-10))

    # Diferencia de entropia (eje 0 de cada nivel = entropia)
    delta_entropia = float(v_nivel_a[0] - v_nivel_b[0]) if len(v_nivel_a) > 0 and len(v_nivel_b) > 0 else 0.0

    # Homomorfismo (similitud de estructura entre niveles)
    homomorfismo = 1.0 - cos_dist

    # Emergencia (features que son >0 en nivel superior pero ~0 en inferior)
    emergencia = sum(1 for i in range(min_len) if abs(b[i]) > 0.1 and abs(a[i]) < 0.01) / max(min_len, 1)

    return [corr, cos_dist, min(ratio_mag, 5.0), delta_entropia, homomorfismo, emergencia]


FEATURES_INTER_NIVEL = 6


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print(f"10 marcos matematicos: {FEATURES_POR_NIVEL} features por nivel")
    for eje, n in FEATURES_POR_EJE.items():
        print(f"  {eje}: {n}")
    print(f"Inter-nivel: {FEATURES_INTER_NIVEL} features por par")
    print(f"Total 4 niveles + 3 inter: {FEATURES_POR_NIVEL * 4 + FEATURES_INTER_NIVEL * 3}")

    # Test con secuencia sintetica
    seq = [0, 1, 2, 0, 1, 3, 0, 2, 1, 4, 0, 1, 2, 3, 4, 0, 1, 2, 0, 3]
    v = calcular_10_ejes(seq, n_tipos=10)
    print(f"\nVector test: {len(v)} features, NaN={np.isnan(v).sum()}, Inf={np.isinf(v).sum()}")
    print(f"Non-zero: {(v != 0).sum()}/{len(v)}")

    # Test inter-nivel
    v2 = calcular_10_ejes([0, 1, 0, 2, 0, 1, 3, 0], n_tipos=5)
    inter = calcular_inter_nivel(v, v2)
    print(f"Inter-nivel: {len(inter)} features")
