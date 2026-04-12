"""
Geometria del Isomorfismo — Forma geometrica fractal del texto
Fecha: 2026-04-12

Dos niveles de geometria:

NIVEL MACRO: 10 marcos = 10 vertices en espacio 10D
  - Cada vertice = valor resumen del marco (norma de sus features)
  - Aristas = correlacion entre pares de marcos
  - Forma = poligono en 10D con metricas: area, perimetro, simetria, convexidad
  - Esta forma ES el isomorfismo del texto

NIVEL MICRO: Dentro de cada marco, N features = N vertices
  - Sub-forma geometrica por marco
  - Define la "textura" de cada vertice macro

MULTI-ESCALA: La misma geometria se calcula en 4 niveles (tokens, oraciones, parrafos, texto)
  - Similaridad de formas entre niveles = profundidad del patron

La busqueda de isomorfismos es por similitud de FORMAS, no de valores.

Ref: CAPA_0_ESPECIFICACION.md §4 "El espacio de coordenadas del isomorfismo"
"""

import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist, squareform
from itertools import combinations
import warnings

from marcos_matematicos import FEATURES_POR_EJE, FEATURES_POR_NIVEL


# ============================================================
# CONSTANTES
# ============================================================

MARCOS = list(FEATURES_POR_EJE.keys())
N_MARCOS = len(MARCOS)  # 10

# Offsets de cada marco dentro del vector de 62 features
MARCO_OFFSETS = {}
pos = 0
for marco, n_feat in FEATURES_POR_EJE.items():
    MARCO_OFFSETS[marco] = (pos, pos + n_feat)
    pos += n_feat


# ============================================================
# NIVEL MICRO: Geometria interna de cada marco
# ============================================================

def geometria_micro(features_marco):
    """Calcula la forma geometrica dentro de un marco (sus features como vertices).

    Args:
        features_marco: np.array de N features del marco

    Returns:
        dict con metricas de la sub-forma
    """
    f = np.array(features_marco, dtype=np.float64)
    n = len(f)

    if n < 2 or np.all(f == 0):
        return {
            "norma": 0.0, "entropia_forma": 0.0, "concentracion": 0.0,
            "dispersion": 0.0, "asimetria": 0.0, "n_activos": 0,
            "ratio_activos": 0.0, "max_min_ratio": 0.0,
        }

    # Norma (magnitud total del marco)
    norma = float(np.linalg.norm(f))

    # Features activas (>0.01)
    activos = f[np.abs(f) > 0.01]
    n_activos = len(activos)
    ratio_activos = n_activos / n

    # Concentracion (Gini sobre valores absolutos)
    abs_f = np.abs(f)
    abs_sorted = np.sort(abs_f)[::-1]
    total = abs_sorted.sum()
    if total > 1e-10:
        concentracion = float(np.sum(abs_sorted[:max(n // 3, 1)])) / total
    else:
        concentracion = 0.0

    # Dispersion (coeficiente de variacion)
    if np.mean(np.abs(activos)) > 1e-10 and len(activos) > 1:
        dispersion = float(np.std(activos) / np.mean(np.abs(activos)))
    else:
        dispersion = 0.0

    # Asimetria (skewness)
    if len(activos) > 2:
        from scipy.stats import skew
        asimetria = float(skew(activos))
    else:
        asimetria = 0.0

    # Entropia de la forma (distribucion de pesos relativos)
    if total > 1e-10:
        probs = abs_sorted / total
        probs = probs[probs > 0]
        from scipy.stats import entropy
        entropia_forma = float(entropy(probs, base=2))
    else:
        entropia_forma = 0.0

    # Ratio max/min (contraste dentro del marco)
    if len(activos) >= 2:
        max_min_ratio = float(max(np.abs(activos)) / max(min(np.abs(activos)), 1e-10))
        max_min_ratio = min(max_min_ratio, 100.0)  # cap
    else:
        max_min_ratio = 0.0

    return {
        "norma": round(norma, 4),
        "entropia_forma": round(entropia_forma, 4),
        "concentracion": round(concentracion, 4),
        "dispersion": round(dispersion, 4),
        "asimetria": round(asimetria, 4),
        "n_activos": n_activos,
        "ratio_activos": round(ratio_activos, 4),
        "max_min_ratio": round(max_min_ratio, 4),
    }

FEATURES_MICRO = 8  # features por geometria micro


# ============================================================
# NIVEL MACRO: Geometria de los 10 marcos como vertices
# ============================================================

def geometria_macro(vector_nivel):
    """Calcula la forma geometrica de los 10 marcos como vertices en espacio 10D.

    Args:
        vector_nivel: np.array de 62 features (un nivel completo)

    Returns:
        dict con:
          - vertices: 10 valores (norma de cada marco)
          - aristas: 45 correlaciones (pares de marcos)
          - forma: metricas globales de la forma
          - micro: geometria interna de cada marco
    """
    # Extraer sub-vectors por marco
    sub_vectors = {}
    for marco, (start, end) in MARCO_OFFSETS.items():
        sub_vectors[marco] = vector_nivel[start:end]

    # VERTICES: norma de cada marco (10 valores)
    vertices = np.array([float(np.linalg.norm(sub_vectors[m])) for m in MARCOS])

    # ARISTAS: correlacion entre pares de marcos (45 pares)
    aristas = {}
    aristas_flat = []
    for i, j in combinations(range(N_MARCOS), 2):
        a, b = sub_vectors[MARCOS[i]], sub_vectors[MARCOS[j]]
        if np.std(a) > 1e-10 and np.std(b) > 1e-10:
            # Pad to same length
            min_len = min(len(a), len(b))
            corr = float(np.corrcoef(a[:min_len], b[:min_len])[0, 1])
        else:
            corr = 0.0
        aristas[f"{MARCOS[i]}_{MARCOS[j]}"] = round(corr, 4)
        aristas_flat.append(corr)

    aristas_arr = np.array(aristas_flat)

    # FORMA: metricas del poligono 10D
    forma = {}

    # Perimetro (suma de distancias entre vertices adyacentes en el orden de los marcos)
    dists_adj = [abs(vertices[i + 1] - vertices[i]) for i in range(N_MARCOS - 1)]
    dists_adj.append(abs(vertices[0] - vertices[-1]))  # cerrar el poligono
    forma["perimetro"] = round(float(sum(dists_adj)), 4)

    # Area aproximada (usando ConvexHull en 2D via PCA si hay >2 vertices activos)
    activos_idx = [i for i in range(N_MARCOS) if vertices[i] > 0.01]
    if len(activos_idx) >= 3:
        # Proyectar a 2D para calcular area
        puntos_2d = np.column_stack([
            vertices * np.cos(np.linspace(0, 2 * np.pi, N_MARCOS, endpoint=False)),
            vertices * np.sin(np.linspace(0, 2 * np.pi, N_MARCOS, endpoint=False)),
        ])
        try:
            hull = ConvexHull(puntos_2d)
            forma["area"] = round(float(hull.volume), 4)  # En 2D, volume = area
        except Exception:
            forma["area"] = 0.0
    else:
        forma["area"] = 0.0

    # Simetria (cuanto se parece el poligono a un circulo perfecto)
    if np.mean(vertices) > 1e-10:
        forma["simetria"] = round(1.0 - float(np.std(vertices) / np.mean(vertices)), 4)
    else:
        forma["simetria"] = 0.0

    # Convexidad (ratio de vertices en el convex hull vs total)
    if len(activos_idx) >= 3:
        forma["convexidad"] = round(len(activos_idx) / N_MARCOS, 4)
    else:
        forma["convexidad"] = 0.0

    # Excentricidad (ratio max/min vertice)
    if len(activos_idx) >= 2:
        vals_activos = vertices[vertices > 0.01]
        forma["excentricidad"] = round(float(max(vals_activos) / min(vals_activos)), 4)
    else:
        forma["excentricidad"] = 0.0

    # Densidad de aristas (% de correlaciones fuertes > 0.5)
    if len(aristas_flat) > 0:
        forma["densidad_aristas"] = round(
            sum(1 for a in aristas_flat if abs(a) > 0.5) / len(aristas_flat), 4
        )
    else:
        forma["densidad_aristas"] = 0.0

    # Coherencia (media de correlaciones absolutas)
    if len(aristas_flat) > 0:
        forma["coherencia"] = round(float(np.mean(np.abs(aristas_arr))), 4)
    else:
        forma["coherencia"] = 0.0

    # Polarizacion (desviacion estandar de vertices — formas irregulares = alta)
    forma["polarizacion"] = round(float(np.std(vertices)), 4)

    # Vertices dominantes (marcos con norma > media + 1 std)
    if np.std(vertices) > 1e-10:
        umbral = np.mean(vertices) + np.std(vertices)
        dominantes = [MARCOS[i] for i in range(N_MARCOS) if vertices[i] > umbral]
    else:
        dominantes = []
    forma["dominantes"] = dominantes
    forma["n_dominantes"] = len(dominantes)

    # MICRO: geometria interna de cada marco
    micro = {}
    for marco in MARCOS:
        micro[marco] = geometria_micro(sub_vectors[marco])

    return {
        "vertices": {MARCOS[i]: round(float(vertices[i]), 4) for i in range(N_MARCOS)},
        "vertices_array": vertices,
        "aristas": aristas,
        "forma": forma,
        "micro": micro,
    }

FEATURES_FORMA_MACRO = 10  # perimetro, area, simetria, convexidad, excentricidad, densidad, coherencia, polarizacion, n_dominantes, + 1 spare


# ============================================================
# MULTI-ESCALA: Comparar formas entre niveles
# ============================================================

def similaridad_formas(geom_a, geom_b):
    """Compara dos formas geometricas (de niveles diferentes).

    Returns:
        dict con metricas de similaridad entre formas
    """
    v_a = geom_a["vertices_array"]
    v_b = geom_b["vertices_array"]

    # Correlacion de vertices (mismos marcos, valores diferentes)
    if np.std(v_a) > 1e-10 and np.std(v_b) > 1e-10:
        corr_vertices = float(np.corrcoef(v_a, v_b)[0, 1])
    else:
        corr_vertices = 0.0

    # Distancia coseno entre formas
    na, nb = np.linalg.norm(v_a), np.linalg.norm(v_b)
    if na > 1e-10 and nb > 1e-10:
        cos_dist = 1.0 - float(np.dot(v_a, v_b) / (na * nb))
    else:
        cos_dist = 1.0

    # Mismos dominantes?
    dom_a = set(geom_a["forma"]["dominantes"])
    dom_b = set(geom_b["forma"]["dominantes"])
    if dom_a or dom_b:
        jaccard_dom = len(dom_a & dom_b) / max(len(dom_a | dom_b), 1)
    else:
        jaccard_dom = 1.0

    # Delta simetria
    delta_simetria = abs(geom_a["forma"]["simetria"] - geom_b["forma"]["simetria"])

    # Delta polarizacion
    delta_polarizacion = abs(geom_a["forma"]["polarizacion"] - geom_b["forma"]["polarizacion"])

    # Homomorfismo (forma similar = alto)
    homomorfismo = (1.0 - cos_dist) * 0.4 + corr_vertices * 0.3 + jaccard_dom * 0.3

    return {
        "corr_vertices": round(corr_vertices, 4),
        "cos_dist": round(cos_dist, 4),
        "jaccard_dominantes": round(jaccard_dom, 4),
        "delta_simetria": round(delta_simetria, 4),
        "delta_polarizacion": round(delta_polarizacion, 4),
        "homomorfismo": round(homomorfismo, 4),
    }

FEATURES_SIMILARIDAD = 6


# ============================================================
# VECTOR GEOMETRICO COMPLETO
# ============================================================

def calcular_geometria_completa(vectores_por_nivel):
    """Calcula la geometria completa: macro + micro + multi-escala.

    Args:
        vectores_por_nivel: dict {"N1": np.array(62), "N2": ..., "N3": ..., "N4": ...}

    Returns:
        dict con toda la geometria + vector numerico para pgvector
    """
    niveles = ["N1", "N2", "N3", "N4"]
    geometrias = {}

    # Geometria de cada nivel
    for nivel in niveles:
        if nivel in vectores_por_nivel:
            geometrias[nivel] = geometria_macro(vectores_por_nivel[nivel])

    # Similaridad entre niveles adyacentes
    similaridades = {}
    for i in range(len(niveles) - 1):
        na, nb = niveles[i], niveles[i + 1]
        if na in geometrias and nb in geometrias:
            similaridades[f"{na}_{nb}"] = similaridad_formas(geometrias[na], geometrias[nb])

    # Profundidad del patron: media de homomorfismos inter-nivel
    homos = [s["homomorfismo"] for s in similaridades.values()]
    profundidad = float(np.mean(homos)) if homos else 0.0

    # Vector numerico para pgvector (forma compacta)
    vector_geo = []

    # Por nivel: vertices (10) + forma metricas (9)
    for nivel in niveles:
        if nivel in geometrias:
            g = geometrias[nivel]
            vector_geo.extend(g["vertices_array"].tolist())  # 10
            vector_geo.extend([
                g["forma"]["perimetro"],
                g["forma"]["area"],
                g["forma"]["simetria"],
                g["forma"]["convexidad"],
                g["forma"]["excentricidad"],
                g["forma"]["densidad_aristas"],
                g["forma"]["coherencia"],
                g["forma"]["polarizacion"],
                float(g["forma"]["n_dominantes"]),
            ])  # 9
        else:
            vector_geo.extend([0.0] * 19)

    # Inter-nivel: similaridades (6 x 3)
    for pair in ["N1_N2", "N2_N3", "N3_N4"]:
        if pair in similaridades:
            s = similaridades[pair]
            vector_geo.extend([
                s["corr_vertices"], s["cos_dist"], s["jaccard_dominantes"],
                s["delta_simetria"], s["delta_polarizacion"], s["homomorfismo"],
            ])
        else:
            vector_geo.extend([0.0] * 6)

    # Profundidad global
    vector_geo.append(profundidad)

    vector_geo = np.array(vector_geo, dtype=np.float64)

    # Total: 4 niveles x 19 + 3 inter x 6 + 1 profundidad = 76 + 18 + 1 = 95
    EXPECTED = 4 * 19 + 3 * 6 + 1  # 95
    assert len(vector_geo) == EXPECTED, f"Geometria: {len(vector_geo)} != {EXPECTED}"

    return {
        "geometrias": geometrias,
        "similaridades": similaridades,
        "profundidad_patron": round(profundidad, 4),
        "vector_pgvector": vector_geo,
        "n_features": len(vector_geo),
    }

FEATURES_GEOMETRIA_TOTAL = 4 * 19 + 3 * 6 + 1  # 95


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import time
    import spacy
    from poc_capa0_v6 import calcular_vector_v6, FEATURES_POR_NIVEL as FPN

    print(f"Geometria del Isomorfismo")
    print(f"  Features por nivel (macro): 10 vertices + 9 forma = 19")
    print(f"  Features inter-nivel: 6 x 3 pares = 18")
    print(f"  Profundidad: 1")
    print(f"  Total vector geometrico: {FEATURES_GEOMETRIA_TOTAL}")
    print()

    nlp = spacy.load("es_dep_news_trf")

    with open("/tmp/texto_financiero.txt") as f:
        texto = f.read().strip()

    print(f"Procesando texto financiero ({len(texto.split())} palabras)...")
    doc = nlp(texto)
    vector_v6, meta = calcular_vector_v6(doc)

    # Extraer vectores por nivel
    vectores = {
        "N1": vector_v6[0:FPN],
        "N2": vector_v6[FPN:2*FPN],
        "N3": vector_v6[2*FPN:3*FPN],
        "N4": vector_v6[3*FPN:4*FPN],
    }

    t0 = time.time()
    geo = calcular_geometria_completa(vectores)
    dt = time.time() - t0

    print(f"\nGeometria calculada en {dt*1000:.1f}ms")
    print(f"Vector pgvector: {geo['n_features']}D")
    print(f"Profundidad del patron: {geo['profundidad_patron']}")

    print(f"\n{'='*60}")
    print(f"FORMA POR NIVEL")
    print(f"{'='*60}")
    for nivel in ["N1", "N2", "N3", "N4"]:
        g = geo["geometrias"][nivel]
        print(f"\n  {nivel}:")
        print(f"    Vertices (10 marcos):")
        for marco, val in g["vertices"].items():
            bar = "█" * int(val * 20)
            print(f"      {marco:<15s} {val:6.3f} {bar}")
        f = g["forma"]
        print(f"    Forma: perimetro={f['perimetro']:.3f} area={f['area']:.3f} simetria={f['simetria']:.3f}")
        print(f"    Convexidad={f['convexidad']:.3f} excentricidad={f['excentricidad']:.3f}")
        print(f"    Coherencia={f['coherencia']:.3f} polarizacion={f['polarizacion']:.3f}")
        print(f"    Dominantes: {f['dominantes']}")

    print(f"\n{'='*60}")
    print(f"SIMILARIDAD ENTRE NIVELES")
    print(f"{'='*60}")
    for pair, s in geo["similaridades"].items():
        print(f"\n  {pair}:")
        print(f"    Corr vertices: {s['corr_vertices']:.3f}")
        print(f"    Distancia coseno: {s['cos_dist']:.3f}")
        print(f"    Jaccard dominantes: {s['jaccard_dominantes']:.3f}")
        print(f"    Homomorfismo: {s['homomorfismo']:.3f}")

    print(f"\n  PROFUNDIDAD GLOBAL: {geo['profundidad_patron']:.3f}")
    if geo["profundidad_patron"] > 0.7:
        print(f"  → Patron PROFUNDO (permea todas las escalas)")
    elif geo["profundidad_patron"] > 0.4:
        print(f"  → Patron MEDIO (presente en algunos niveles)")
    else:
        print(f"  → Patron SUPERFICIAL (solo en nivel micro)")

    # Vector total: v6 (266D) + geometria (95D) = 361D
    vector_total = np.concatenate([vector_v6, geo["vector_pgvector"]])
    print(f"\n  VECTOR TOTAL: v6({len(vector_v6)}D) + geometria({geo['n_features']}D) = {len(vector_total)}D")
    print(f"  NaN: {np.isnan(vector_total).sum()}, Inf: {np.isinf(vector_total).sum()}")
    print(f"  Non-zero: {(vector_total!=0).sum()}/{len(vector_total)}")
