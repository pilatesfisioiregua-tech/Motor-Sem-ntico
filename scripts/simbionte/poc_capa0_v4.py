"""
Simbionte v4 — Funciones reales en contexto
Fecha: 2026-04-12

Evolución de v3: reemplaza distribuciones POS (18) + DEP (30) + MORPH (15)
por distribución de 57 funciones reales que combinan POS+DEP+MORPH en una
clasificación funcional única por token.

Principio: no codificar lo que la palabra ES sino lo que HACE en esta oración.

Vector: 131 features (74 nivel 1 + 30 nivel 2 + 13 nivel 3 + 14 nivel 4)

Ref: CAPA_0_ESPECIFICACION.md v1.5
Ref: DISEÑO_FUNCIONES_REALES.md
Ref: clasificador_funcional.py (catálogo de 57 funciones)
"""

import json
import numpy as np
from collections import Counter
from scipy import stats
from scipy.linalg import eig
import networkx as nx
import logging

logging.basicConfig(level=logging.WARNING)
np.random.seed(42)

# Importar clasificador funcional
from clasificador_funcional import (
    FUNCIONES, N_FUNCIONES, FUNC_NAMES, FUNC_CODES,
    clasificar_token, clasificar_texto, distribucion_funcional,
    SUF_NOM_VERBO, SUF_RELACIONAL,
    ADV_NEGACION, ADV_TIEMPO, ADV_LUGAR, ADV_CANTIDAD,
)

# ============================================================
# CONSTANTES
# ============================================================

# Tipos de oración (sin cambio respecto a v3)
SENT_TYPES = [
    "copulativa", "transitiva_simple", "intransitiva", "impersonal",
    "pasiva_refleja", "reflexiva", "adversativa", "condicional",
    "causal", "consecutiva", "concesiva", "interrogativa", "imperativa",
    "compuesta_coordinada", "compuesta_subordinada", "simple", "otra"
]
N_SENT_TYPES = 17

PARA_TYPES = ["expositivo", "argumentativo", "enumerativo", "confrontativo", "mixto"]
N_PARA_TYPES = 5

ADVERSATIVOS_SINGLE = {"pero", "aunque", "sino"}
ADVERSATIVOS_MULTI = {"sin embargo", "no obstante"}
SUFIJOS_OPACOS = ("ción", "sión", "miento", "idad", "ancia", "encia")
CAUSALES = {"porque", "ya", "puesto", "dado", "como", "debido"}
CONSECUTIVOS = {"entonces", "así", "luego", "consiguiente"}

# Dimensionalidad
FEATURES_NIVEL_1 = N_FUNCIONES + 10 + 7  # 63 funciones + 10 grafo + 7 Markov = 80
FEATURES_NIVEL_2 = 30
FEATURES_NIVEL_3 = 13
FEATURES_NIVEL_4 = 14
FEATURES_TOTAL = FEATURES_NIVEL_1 + FEATURES_NIVEL_2 + FEATURES_NIVEL_3 + FEATURES_NIVEL_4

# Nombres
FEATURE_NAMES = []
for name in FUNC_NAMES:
    FEATURE_NAMES.append(f"n1_func_{name}")
FEATURE_NAMES.extend([
    "n1_graf_prof_media", "n1_graf_prof_max", "n1_graf_grado_root",
    "n1_graf_ratio_hojas", "n1_graf_n_componentes", "n1_graf_centralidad_max",
    "n1_graf_densidad", "n1_graf_ratio_subordinacion", "n1_graf_ratio_coordinacion",
    "n1_graf_ratio_copulas"
])
FEATURE_NAMES.extend([
    "n1_markov_h_dist", "n1_markov_h_trans", "n1_markov_estructura",
    "n1_markov_diagonal", "n1_markov_est_0", "n1_markov_est_1", "n1_markov_est_2"
])
for st in SENT_TYPES:
    FEATURE_NAMES.append(f"n2_tipo_{st}")
FEATURE_NAMES.extend([
    "n2_prof_media", "n2_prof_std", "n2_long_media", "n2_long_std",
    "n2_n_sujetos", "n2_ratio_sin_sujeto", "n2_ratio_subordinadas", "n2_n_oraciones"
])
FEATURE_NAMES.extend([
    "n2_markov_h_dist", "n2_markov_h_trans", "n2_markov_estructura",
    "n2_markov_diagonal", "n2_markov_ratio_trans"
])
for pt in PARA_TYPES:
    FEATURE_NAMES.append(f"n3_tipo_{pt}")
FEATURE_NAMES.extend([
    "n3_n_parrafos", "n3_long_media", "n3_long_std", "n3_diversidad", "n3_delta_ac"
])
FEATURE_NAMES.extend(["n3_markov_h_trans", "n3_markov_diagonal", "n3_markov_estructura"])
FEATURE_NAMES.extend([
    "n4_vel_media", "n4_vel_max", "n4_acel_media", "n4_curvatura",
    "n4_n_bruscos", "n4_coherencia", "n4_delta_ac", "n4_zona_final"
])
FEATURE_NAMES.extend([
    "n4_fg", "n4_ratio_nom", "n4_ratio_adv", "n4_div_lexica", "n4_ratio_cf", "n4_densidad"
])

assert len(FEATURE_NAMES) == FEATURES_TOTAL, \
    f"Nombres {len(FEATURE_NAMES)} != features {FEATURES_TOTAL}"


# ============================================================
# UTILIDADES
# ============================================================

def tokens_funcionales(doc):
    return [t for t in doc if not t.is_punct and not t.is_space]

def contar_adversativos(doc):
    count = sum(1 for t in doc if t.text.lower() in ADVERSATIVOS_SINGLE)
    text_lower = doc.text.lower()
    for adv in ADVERSATIVOS_MULTI:
        count += text_lower.count(adv)
    return count

def safe_div(a, b):
    return a / b if b > 0 else 0.0

def cadena_markov(secuencia, n_estados):
    if len(secuencia) < 3:
        return [0.0] * 7
    seq = list(secuencia)
    counts = Counter(seq)
    total = len(seq)
    probs = np.zeros(n_estados)
    for s, c in counts.items():
        if 0 <= s < n_estados:
            probs[s] = c / total
    probs_safe = probs[probs > 0]
    h_dist = float(stats.entropy(probs_safe, base=2)) if len(probs_safe) > 1 else 0.0

    T = np.zeros((n_estados, n_estados))
    for i in range(len(seq) - 1):
        a, b = seq[i], seq[i+1]
        if 0 <= a < n_estados and 0 <= b < n_estados:
            T[a, b] += 1
    row_sums = T.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    T = T / row_sums

    h_trans = 0.0
    for i in range(n_estados):
        if probs[i] > 0:
            row = T[i]
            row_safe = row[row > 0]
            if len(row_safe) > 0:
                h_trans += probs[i] * float(stats.entropy(row_safe, base=2))

    diagonal = float(np.mean(np.diag(T)))
    try:
        eigenvalues, eigenvectors = eig(T.T)
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        stationary = np.abs(eigenvectors[:, idx].real)
        s_sum = stationary.sum()
        stationary = stationary / s_sum if s_sum > 1e-10 else probs
    except Exception:
        stationary = probs

    return [h_dist, h_trans, h_dist - h_trans, diagonal,
            float(stationary[0]) if len(stationary) > 0 else 0.0,
            float(stationary[1]) if len(stationary) > 1 else 0.0,
            float(stationary[2]) if len(stationary) > 2 else 0.0]


# ============================================================
# NIVEL 1: PALABRAS (74 features)
# 57 funciones reales + 10 grafo + 7 Markov
# ============================================================

def nivel1_palabras(doc):
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)

    # 57 funciones reales
    result = distribucion_funcional(doc)
    dist_func = result["distribucion"]  # 57 valores

    # 10 propiedades del grafo
    G = nx.DiGraph()
    for t in toks:
        G.add_node(t.i, pos=t.pos_, dep=t.dep_)
        if t.head != t and not t.head.is_punct and not t.head.is_space:
            G.add_edge(t.head.i, t.i)

    depths = []
    for t in toks:
        d = 0
        current = t
        safety = 0
        while current.head != current and safety < 100:
            d += 1
            current = current.head
            safety += 1
        depths.append(d)

    prof_media = float(np.mean(depths)) if depths else 0.0
    prof_max = float(max(depths)) if depths else 0.0

    roots = [t for t in doc if t.dep_ == "ROOT"]
    grado_root = sum(sum(1 for c in r.children if not c.is_punct and not c.is_space) for r in roots)

    ratio_hojas = safe_div(
        sum(1 for t in toks if len([c for c in t.children if not c.is_punct and not c.is_space]) == 0),
        n_total)

    n_comp = float(nx.number_weakly_connected_components(G)) if G.number_of_nodes() > 0 else 1.0

    centralidad_max = 0.0
    if G.number_of_nodes() > 2:
        bc = nx.betweenness_centrality(G)
        centralidad_max = float(max(bc.values())) if bc else 0.0

    densidad = safe_div(G.number_of_edges(), G.number_of_nodes() * max(G.number_of_nodes() - 1, 1))
    n_sents = max(len(list(doc.sents)), 1)
    ratio_sub = safe_div(sum(1 for t in toks if t.dep_ in ("advcl", "ccomp", "xcomp")), n_sents)
    ratio_coord = safe_div(sum(1 for t in toks if t.dep_ == "conj"), n_total)
    ratio_cop = safe_div(sum(1 for t in toks if t.dep_ == "cop"), n_total)

    grafo = [prof_media, prof_max, float(grado_root), ratio_hojas,
             n_comp, centralidad_max, densidad, ratio_sub, ratio_coord, ratio_cop]

    # 7 Markov sobre secuencia de funciones reales (códigos 1-57)
    func_seq = []
    for t in toks:
        func_name, _ = clasificar_token(t)
        func_seq.append(FUNC_CODES[func_name] - 1)  # 0-indexed para Markov
    markov = cadena_markov(func_seq, N_FUNCIONES)

    vector = dist_func + grafo + markov
    assert len(vector) == FEATURES_NIVEL_1, \
        f"Nivel 1: {len(vector)} != {FEATURES_NIVEL_1}"
    return vector, result


# ============================================================
# NIVEL 2: ORACIONES (30 features) — sin cambio vs v3
# ============================================================

def clasificar_oracion(sent):
    toks = [t for t in sent if not t.is_punct and not t.is_space]
    deps = set(t.dep_ for t in toks)
    moods = set()
    for t in toks:
        m = t.morph.get("Mood")
        if m: moods.update(m)

    if "cop" in deps: return 0
    if any(t.dep_ == "cc" and t.text.lower() in ADVERSATIVOS_SINGLE for t in toks): return 6
    for t in toks:
        if t.dep_ == "mark" and t.lemma_.lower() == "si": return 7
    if "Cnd" in moods and "advcl" in deps: return 7
    if "advcl" in deps and any(t.dep_ == "mark" and t.lemma_.lower() in CAUSALES for t in toks): return 8
    if "advcl" in deps and any(t.dep_ == "mark" and t.lemma_.lower() in CONSECUTIVOS for t in toks): return 9
    if "advcl" in deps and any(t.dep_ == "mark" and t.lemma_.lower() == "aunque" for t in toks): return 10
    if any(t.text == "?" for t in sent): return 11
    if "Imp" in moods: return 12
    if "expl:pass" in deps: return 4
    if "expl:pv" in deps: return 5
    if "conj" in deps and "cc" in deps: return 13
    if any(d in deps for d in ("advcl", "ccomp", "xcomp")): return 14
    if "nsubj" not in deps: return 3
    if "obj" in deps: return 1
    if "nsubj" in deps: return 15
    return 2

def nivel2_oraciones(doc):
    sents = list(doc.sents)
    n_sents = max(len(sents), 1)
    tipos = [clasificar_oracion(sent) for sent in sents]

    dist_tipos = [0.0] * N_SENT_TYPES
    tc = Counter(tipos)
    for t_idx, count in tc.items():
        if 0 <= t_idx < N_SENT_TYPES:
            dist_tipos[t_idx] = count / n_sents

    profundidades, longitudes = [], []
    sujetos_unicos = set()
    n_sin_suj, n_sub = 0, 0
    for sent in sents:
        st = [t for t in sent if not t.is_punct and not t.is_space]
        longitudes.append(len(st))
        ds = []
        for t in st:
            d, c, s = 0, t, 0
            while c.head != c and s < 100: d += 1; c = c.head; s += 1
            ds.append(d)
        profundidades.append(float(np.mean(ds)) if ds else 0.0)
        for t in st:
            if t.dep_ == "nsubj": sujetos_unicos.add(t.lemma_)
        if not any(t.dep_ == "nsubj" for t in st): n_sin_suj += 1
        if any(t.dep_ in ("advcl","ccomp","xcomp") for t in st): n_sub += 1

    props = [
        float(np.mean(profundidades)) if profundidades else 0.0,
        float(np.std(profundidades)) if len(profundidades) > 1 else 0.0,
        float(np.mean(longitudes)) if longitudes else 0.0,
        float(np.std(longitudes)) if len(longitudes) > 1 else 0.0,
        float(len(sujetos_unicos)), safe_div(n_sin_suj, n_sents),
        safe_div(n_sub, n_sents), float(n_sents)
    ]

    markov_7 = cadena_markov(tipos, N_SENT_TYPES)
    trans_u = len(set(zip(tipos[:-1], tipos[1:])))
    markov_5 = markov_7[:4] + [safe_div(trans_u, max(len(tipos)-1, 1))]

    vector = dist_tipos + props + markov_5
    assert len(vector) == FEATURES_NIVEL_2, f"Nivel 2: {len(vector)} != {FEATURES_NIVEL_2}"
    return vector, tipos


# ============================================================
# NIVEL 3: PÁRRAFOS (13 features) — sin cambio vs v3
# ============================================================

def nivel3_parrafos(doc, tipos_oracion):
    text = doc.text
    parrafos_texto = [p.strip() for p in text.split('\n') if p.strip()]

    if len(parrafos_texto) < 2:
        n = len(tipos_oracion)
        if n >= 3:
            tercio = max(n // 3, 1)
            bloques = [tipos_oracion[:tercio], tipos_oracion[tercio:2*tercio], tipos_oracion[2*tercio:]]
        elif n == 2:
            bloques = [tipos_oracion[:1], tipos_oracion[1:]]
        else:
            bloques = [tipos_oracion]
    else:
        sents = list(doc.sents)
        para_ranges = []
        pos = 0
        for pt in parrafos_texto:
            start = text.find(pt, pos)
            if start == -1: start = pos
            para_ranges.append((start, start + len(pt)))
            pos = start + len(pt)
        bloques = [[] for _ in para_ranges]
        for si, sent in enumerate(sents):
            if si >= len(tipos_oracion): break
            mid = (sent.start_char + sent.end_char) // 2
            assigned = False
            for pi, (ps, pe) in enumerate(para_ranges):
                if ps <= mid <= pe:
                    bloques[pi].append(tipos_oracion[si])
                    assigned = True
                    break
            if not assigned and bloques:
                bloques[-1].append(tipos_oracion[si])
        bloques = [b for b in bloques if b]

    tipos_para = []
    for bloque in bloques:
        if not bloque: tipos_para.append(4); continue
        moda = Counter(bloque).most_common(1)[0][0]
        if moda in (0,1,2,15): tipos_para.append(0)
        elif moda in (7,8,9,10,14): tipos_para.append(1)
        elif moda in (13,): tipos_para.append(2)
        elif moda in (6,): tipos_para.append(3)
        else: tipos_para.append(4)

    n_para = max(len(tipos_para), 1)
    dist_para = [0.0] * N_PARA_TYPES
    pc = Counter(tipos_para)
    for pi, cnt in pc.items():
        if 0 <= pi < N_PARA_TYPES: dist_para[pi] = cnt / n_para

    longs = [len(b) for b in bloques]
    probs_p = np.array(dist_para)
    ps = probs_p[probs_p > 0]
    div = float(stats.entropy(ps, base=2)) if len(ps) > 1 else 0.0
    delta = 1.0 if len(tipos_para) >= 2 and tipos_para[0] != tipos_para[-1] else 0.0

    props = [float(n_para), float(np.mean(longs)) if longs else 0.0,
             float(np.std(longs)) if len(longs) > 1 else 0.0, div, delta]

    if len(tipos_para) >= 3:
        mk = cadena_markov(tipos_para, N_PARA_TYPES)
        markov_3 = [mk[1], mk[3], mk[2]]
    else:
        markov_3 = [0.0, 0.0, 0.0]

    vector = dist_para + props + markov_3
    assert len(vector) == FEATURES_NIVEL_3, f"Nivel 3: {len(vector)} != {FEATURES_NIVEL_3}"
    return vector


# ============================================================
# NIVEL 4: TEXTO (14 features) — sin cambio vs v3
# ============================================================

def nivel4_texto(doc):
    sents = list(doc.sents)
    toks = tokens_funcionales(doc)
    n_total = max(len(toks), 1)
    n_verbs = max(sum(1 for t in toks if t.pos_ in ("VERB", "AUX")), 1)

    # Trayectoria (8)
    if len(sents) >= 2:
        POS_SHORT = ["ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET"]
        centroids = []
        for sent in sents:
            st = [t for t in sent if not t.is_punct and not t.is_space]
            n = max(len(st), 1)
            centroids.append(np.array([sum(1 for t in st if t.pos_==p)/n for p in POS_SHORT]))

        vels = [float(np.linalg.norm(centroids[i+1]-centroids[i])) for i in range(len(centroids)-1)]
        vm = float(np.mean(vels)) if vels else 0.0
        vx = float(max(vels)) if vels else 0.0
        am = float(np.mean([vels[i+1]-vels[i] for i in range(len(vels)-1)])) if len(vels)>1 else 0.0

        if len(centroids) >= 3:
            curvs = []
            for i in range(len(centroids)-2):
                d1, d2 = centroids[i+1]-centroids[i], centroids[i+2]-centroids[i+1]
                n1, n2 = np.linalg.norm(d1), np.linalg.norm(d2)
                if n1>1e-10 and n2>1e-10:
                    curvs.append(1-np.clip(np.dot(d1,d2)/(n1*n2),-1,1))
            curv = float(np.mean(curvs)) if curvs else 0.0
        else: curv = 0.0

        nb = float(sum(1 for v in vels if v > vm + np.std(vels))) / max(len(sents)-1,1) if len(vels)>1 else 0.0

        if len(centroids) >= 3:
            dirs = [centroids[i+1]-centroids[i] for i in range(len(centroids)-1)]
            cohs = []
            for i in range(len(dirs)-1):
                n1, n2 = np.linalg.norm(dirs[i]), np.linalg.norm(dirs[i+1])
                if n1>1e-10 and n2>1e-10: cohs.append(np.dot(dirs[i],dirs[i+1])/(n1*n2))
            coh = float(np.mean(cohs)) if cohs else 0.0
        else: coh = 0.0

        dac = float(np.linalg.norm(centroids[-1]-centroids[0]))
        last_t = [t for t in sents[-1] if not t.is_punct and not t.is_space]
        if last_t:
            lp = Counter(t.pos_ for t in last_t).most_common(1)[0][0]
            zf = float(POS_SHORT.index(lp))/len(POS_SHORT) if lp in POS_SHORT else 0.0
        else: zf = 0.0
        trayectoria = [vm, vx, am, curv, nb, coh, dac, zf]
    else:
        trayectoria = [0.0]*8

    # Resúmenes (6)
    n_cnd = sum(1 for t in toks if t.morph.get("Mood") and t.morph.get("Mood")[0]=="Cnd")
    n_nom = sum(1 for t in toks if t.pos_=="NOUN" and t.text.lower().endswith(SUFIJOS_OPACOS))
    n_adv = contar_adversativos(doc)
    rc = safe_div(n_cnd, n_verbs)
    rn = safe_div(n_nom, n_total)
    ra = safe_div(n_adv, n_total)
    fg = max(0.0, min(1.0, 1.0-(rc*0.25+rn*0.15+ra*0.20)))
    dl = safe_div(len(set(t.lemma_ for t in toks)), n_total)
    nc = sum(1 for t in toks if t.pos_ in ("NOUN","VERB","ADJ","ADV"))
    nf = sum(1 for t in toks if t.pos_ in ("DET","ADP","PRON","CCONJ","SCONJ"))
    rcf = safe_div(nc, max(nf,1))
    dens = safe_div(nc, n_total)
    resumenes = [fg, rn, ra, dl, rcf, dens]

    vector = trayectoria + resumenes
    assert len(vector) == FEATURES_NIVEL_4, f"Nivel 4: {len(vector)} != {FEATURES_NIVEL_4}"
    return vector


# ============================================================
# VECTOR COMPLETO
# ============================================================

def calcular_vector_simbionte(doc):
    """Vector completo v4: 131 features sobre 4 niveles con funciones reales."""
    v1, func_result = nivel1_palabras(doc)
    v2, tipos_oracion = nivel2_oraciones(doc)
    v3 = nivel3_parrafos(doc, tipos_oracion)
    v4 = nivel4_texto(doc)
    vector = v1 + v2 + v3 + v4
    assert len(vector) == FEATURES_TOTAL, f"Total: {len(vector)} != {FEATURES_TOTAL}"
    return np.array(vector, dtype=np.float64), func_result


# ============================================================
# VALIDADOR P30
# ============================================================

def validar_vector(X):
    report = {"valid": True, "warnings": [], "errors": []}
    if X.shape[1] != FEATURES_TOTAL:
        report["valid"] = False
        report["errors"].append(f"Dims {X.shape[1]} != {FEATURES_TOTAL}")
        return report
    if np.isnan(X).sum() > 0 or np.isinf(X).sum() > 0:
        report["valid"] = False
        report["errors"].append(f"NaN={np.isnan(X).sum()}, Inf={np.isinf(X).sum()}")
    niveles = [
        ("nivel_1", 0, FEATURES_NIVEL_1),
        ("nivel_2", FEATURES_NIVEL_1, FEATURES_NIVEL_1+FEATURES_NIVEL_2),
        ("nivel_3", FEATURES_NIVEL_1+FEATURES_NIVEL_2, FEATURES_NIVEL_1+FEATURES_NIVEL_2+FEATURES_NIVEL_3),
        ("nivel_4", FEATURES_NIVEL_1+FEATURES_NIVEL_2+FEATURES_NIVEL_3, FEATURES_TOTAL),
    ]
    for name, s, e in niveles:
        sub = X[:, s:e]
        nd = sum(1 for i in range(sub.shape[1]) if (sub[:,i]==0).sum()/len(sub) > 0.90)
        r = nd / sub.shape[1]
        if r > 0.30:
            report["warnings"].append(f"{name}: {nd}/{sub.shape[1]} features >90% ceros ({r:.0%})")
    return report


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import time, sys

    print(f"Simbionte v4 — {FEATURES_TOTAL} features ({N_FUNCIONES} funciones reales + grafo + Markov + niveles 2-4)")
    print(f"  Nivel 1: {FEATURES_NIVEL_1} ({N_FUNCIONES} func + 10 grafo + 7 Markov)")
    print(f"  Nivel 2: {FEATURES_NIVEL_2}")
    print(f"  Nivel 3: {FEATURES_NIVEL_3}")
    print(f"  Nivel 4: {FEATURES_NIVEL_4}")
    print()

    import spacy
    nlp = spacy.load("es_dep_news_trf")

    with open('/tmp/texto_test_1200.txt') as f:
        texto = f.read().strip()

    print(f"Procesando texto ({len(texto.split())} palabras)...")
    t0 = time.time()
    doc = nlp(texto)
    v, func_result = calcular_vector_simbionte(doc)
    dt = time.time() - t0

    print(f"  Vector: {len(v)} features en {dt*1000:.0f}ms")
    print(f"  NaN: {np.isnan(v).sum()}, Inf: {np.isinf(v).sum()}, Zeros: {(v==0).sum()}/{len(v)}")
    print(f"  Funciones: {func_result['stats']['pct_determinista']:.1f}% determinista, {func_result['stats']['haiku']} tokens Haiku")
    print()

    # P30
    report = validar_vector(v.reshape(1,-1))
    if not report["errors"] and not report["warnings"]:
        print("  ✅ P30 PASADO")
    for w in report["warnings"]: print(f"  ⚠️ {w}")
    for e in report["errors"]: print(f"  ❌ {e}")

    # Top features
    print("\nTop 15 features:")
    for idx in np.argsort(np.abs(v))[::-1][:15]:
        print(f"  {FEATURE_NAMES[idx]:<45s}: {v[idx]:8.4f}")
