"""
Simbionte v6 — 10 marcos x 4 niveles + inter-nivel + fusion spaCy/Stanza
Fecha: 2026-04-12

Vector: 266D (62 features/nivel x 4 niveles + 6 features/transicion x 3 transiciones)

Niveles:
  N1: tokens (codigos funcionales de cada token)
  N2: oraciones (tipo de cada oracion)
  N3: parrafos (tipo de cada parrafo)
  N4: texto (resumen global como secuencia)

Inter-nivel:
  N1↔N2: correlacion, distancia, homomorfismo
  N2↔N3: correlacion, distancia, homomorfismo
  N3↔N4: correlacion, distancia, homomorfismo

Ref: CAPA_0_ESPECIFICACION.md §3 + §3.bis
"""

import json
import time
import sys
import os
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))

from clasificador_funcional import (
    clasificar_token, FUNC_NAMES, N_FUNCIONES, FUNC_CODES,
    distribucion_funcional,
)
from marcos_matematicos import (
    calcular_10_ejes, calcular_inter_nivel,
    FEATURES_POR_NIVEL, FEATURES_INTER_NIVEL,
)


# ============================================================
# CONSTANTES
# ============================================================

# Tipos de oracion (17 — mismos que v4)
SENT_TYPES = [
    "copulativa", "transitiva_simple", "intransitiva", "impersonal",
    "pasiva_refleja", "reflexiva", "adversativa", "condicional",
    "causal", "consecutiva", "concesiva", "interrogativa", "imperativa",
    "compuesta_coordinada", "compuesta_subordinada", "simple", "otra"
]
N_SENT_TYPES = 17

PARA_TYPES = ["expositivo", "argumentativo", "enumerativo", "confrontativo", "mixto"]
N_PARA_TYPES = 5

# Resumen texto (8 "tipos" globales usados como secuencia para N4)
TEXT_TYPES = ["certeza", "duda", "accion", "estado", "conflicto", "resolucion", "pregunta", "orden"]
N_TEXT_TYPES = 8

ADVERSATIVOS_SINGLE = {"pero", "aunque", "sino"}
ADVERSATIVOS_MULTI = {"sin embargo", "no obstante"}
CAUSALES = {"porque", "ya", "puesto", "dado", "como", "debido"}
CONSECUTIVOS = {"entonces", "así", "luego", "consiguiente"}
SUFIJOS_OPACOS = ("ción", "sión", "miento", "idad", "ancia", "encia")

# Dimensionalidad total
FEATURES_N1 = FEATURES_POR_NIVEL  # 62
FEATURES_N2 = FEATURES_POR_NIVEL  # 62
FEATURES_N3 = FEATURES_POR_NIVEL  # 62
FEATURES_N4 = FEATURES_POR_NIVEL  # 62
FEATURES_INTER = FEATURES_INTER_NIVEL * 3  # 18
FEATURES_TOTAL = FEATURES_N1 + FEATURES_N2 + FEATURES_N3 + FEATURES_N4 + FEATURES_INTER  # 266


# ============================================================
# UTILIDADES
# ============================================================

def tokens_funcionales(doc):
    return [t for t in doc if not t.is_punct and not t.is_space]

def safe_div(a, b):
    return a / b if b > 0 else 0.0


# ============================================================
# CLASIFICACION DE ORACIONES (reutilizada de v4)
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


# ============================================================
# CLASIFICACION DE PARRAFOS (reutilizada de v4)
# ============================================================

def clasificar_parrafo(tipos_oracion_del_parrafo):
    if not tipos_oracion_del_parrafo:
        return 4  # mixto
    moda = Counter(tipos_oracion_del_parrafo).most_common(1)[0][0]
    if moda in (0, 1, 2, 15): return 0  # expositivo
    elif moda in (7, 8, 9, 10, 14): return 1  # argumentativo
    elif moda in (13,): return 2  # enumerativo
    elif moda in (6,): return 3  # confrontativo
    else: return 4  # mixto


# ============================================================
# SECUENCIA N4: TEXTO COMO SECUENCIA DE "MOVIMIENTOS"
# ============================================================

def secuencia_texto(doc):
    """Convierte el texto completo en una secuencia de movimientos cognitivos.

    Cada oracion se clasifica por su "movimiento" dominante:
      0=certeza, 1=duda, 2=accion, 3=estado, 4=conflicto,
      5=resolucion, 6=pregunta, 7=orden
    """
    sents = list(doc.sents)
    movimientos = []
    for sent in sents:
        toks = [t for t in sent if not t.is_punct and not t.is_space]
        moods = set()
        deps = set()
        for t in toks:
            m = t.morph.get("Mood")
            if m: moods.update(m)
            deps.add(t.dep_)

        # Pregunta
        if any(t.text == "?" for t in sent):
            movimientos.append(6)
        # Orden
        elif "Imp" in moods:
            movimientos.append(7)
        # Conflicto (adversativa)
        elif any(t.dep_ == "cc" and t.text.lower() in ADVERSATIVOS_SINGLE for t in toks):
            movimientos.append(4)
        # Duda (condicional/subjuntivo)
        elif "Cnd" in moods or "Sub" in moods:
            movimientos.append(1)
        # Resolucion (causal + indicativo)
        elif "advcl" in deps and "Ind" in moods:
            movimientos.append(5)
        # Accion (verbos de accion en indicativo)
        elif any(t.pos_ == "VERB" and t.dep_ == "ROOT" for t in toks) and "Ind" in moods:
            if any(t.dep_ == "obj" for t in toks):
                movimientos.append(2)  # accion transitiva
            else:
                movimientos.append(3)  # estado
        # Estado (copulativa)
        elif "cop" in deps:
            movimientos.append(3)
        else:
            movimientos.append(0)  # certeza por defecto

    return movimientos


# ============================================================
# VECTOR COMPLETO v6: 10 marcos x 4 niveles + inter-nivel
# ============================================================

def calcular_vector_v6(doc):
    """Vector completo v6: 266D.

    Returns:
        (vector, metadata)
    """
    t0 = time.time()
    toks = tokens_funcionales(doc)
    sents = list(doc.sents)

    # --- N1: TOKENS ---
    # Secuencia de codigos funcionales (0-indexed)
    seq_n1 = []
    agentes_n1 = []
    condicionales_n1 = []
    edges_n1 = []

    for i, t in enumerate(toks):
        func_name, _ = clasificar_token(t)
        code = FUNC_CODES[func_name] - 1  # 0-indexed
        seq_n1.append(code)

        # Agentes (sujeto)
        if t.dep_ == "nsubj":
            agentes_n1.append(hash(t.lemma_) % 100)
        else:
            agentes_n1.append(None)

        # Condicionales
        if t.morph.get("Mood") and t.morph.get("Mood")[0] == "Cnd":
            condicionales_n1.append(i)

        # Aristas del grafo de dependencias
        if t.head != t and not t.head.is_punct and not t.head.is_space:
            head_idx = next((j for j, tok in enumerate(toks) if tok.i == t.head.i), None)
            if head_idx is not None:
                edges_n1.append((head_idx, i))

    v_n1 = calcular_10_ejes(
        seq_n1, N_FUNCIONES,
        edges=edges_n1,
        agentes=agentes_n1,
        condicionales=condicionales_n1,
    )

    # --- N2: ORACIONES ---
    seq_n2 = [clasificar_oracion(sent) for sent in sents]
    v_n2 = calcular_10_ejes(seq_n2, N_SENT_TYPES)

    # --- N3: PARRAFOS ---
    text = doc.text
    parrafos_texto = [p.strip() for p in text.split('\n') if p.strip()]

    if len(parrafos_texto) < 2:
        # Partir oraciones en tercios como proxy de parrafos
        n = len(seq_n2)
        if n >= 3:
            tercio = max(n // 3, 1)
            bloques = [seq_n2[:tercio], seq_n2[tercio:2*tercio], seq_n2[2*tercio:]]
        elif n == 2:
            bloques = [seq_n2[:1], seq_n2[1:]]
        else:
            bloques = [seq_n2]
    else:
        # Asignar oraciones a parrafos por posicion
        para_ranges = []
        pos = 0
        for pt in parrafos_texto:
            start = text.find(pt, pos)
            if start == -1: start = pos
            para_ranges.append((start, start + len(pt)))
            pos = start + len(pt)
        bloques = [[] for _ in para_ranges]
        for si, sent in enumerate(sents):
            if si >= len(seq_n2): break
            mid = (sent.start_char + sent.end_char) // 2
            assigned = False
            for pi, (ps, pe) in enumerate(para_ranges):
                if ps <= mid <= pe:
                    bloques[pi].append(seq_n2[si])
                    assigned = True
                    break
            if not assigned and bloques:
                bloques[-1].append(seq_n2[si])
        bloques = [b for b in bloques if b]

    seq_n3 = [clasificar_parrafo(bloque) for bloque in bloques]
    v_n3 = calcular_10_ejes(seq_n3, N_PARA_TYPES)

    # --- N4: TEXTO (movimientos cognitivos) ---
    seq_n4 = secuencia_texto(doc)
    v_n4 = calcular_10_ejes(seq_n4, N_TEXT_TYPES)

    # --- INTER-NIVEL ---
    inter_12 = calcular_inter_nivel(v_n1, v_n2)
    inter_23 = calcular_inter_nivel(v_n2, v_n3)
    inter_34 = calcular_inter_nivel(v_n3, v_n4)

    # --- CONCATENAR ---
    vector = np.concatenate([v_n1, v_n2, v_n3, v_n4, inter_12, inter_23, inter_34])

    dt = time.time() - t0

    assert len(vector) == FEATURES_TOTAL, f"v6: {len(vector)} != {FEATURES_TOTAL}"
    # Replace NaN/Inf with 0 (textos muy cortos pueden producir NaN en stats)
    vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)

    metadata = {
        "n_tokens": len(toks),
        "n_oraciones": len(sents),
        "n_parrafos": len(seq_n3),
        "n_movimientos": len(seq_n4),
        "seq_n1_len": len(seq_n1),
        "seq_n2": seq_n2,
        "seq_n3": seq_n3,
        "seq_n4": seq_n4,
        "latencia_ms": round(dt * 1000),
    }

    return vector, metadata


# ============================================================
# VALIDADOR P30
# ============================================================

def validar_vector_v6(X):
    report = {"valid": True, "warnings": [], "errors": []}
    if X.shape[1] != FEATURES_TOTAL:
        report["valid"] = False
        report["errors"].append(f"Dims {X.shape[1]} != {FEATURES_TOTAL}")
        return report
    if np.isnan(X).sum() > 0 or np.isinf(X).sum() > 0:
        report["valid"] = False
        report["errors"].append(f"NaN={np.isnan(X).sum()}, Inf={np.isinf(X).sum()}")

    niveles = [
        ("N1", 0, FEATURES_N1),
        ("N2", FEATURES_N1, FEATURES_N1 + FEATURES_N2),
        ("N3", FEATURES_N1 + FEATURES_N2, FEATURES_N1 + FEATURES_N2 + FEATURES_N3),
        ("N4", FEATURES_N1 + FEATURES_N2 + FEATURES_N3, FEATURES_N1 + FEATURES_N2 + FEATURES_N3 + FEATURES_N4),
        ("inter", FEATURES_N1 + FEATURES_N2 + FEATURES_N3 + FEATURES_N4, FEATURES_TOTAL),
    ]
    for name, s, e in niveles:
        sub = X[:, s:e]
        nd = sum(1 for i in range(sub.shape[1]) if (sub[:, i] == 0).sum() / len(sub) > 0.90)
        r = nd / max(sub.shape[1], 1)
        if r > 0.30:
            report["warnings"].append(f"{name}: {nd}/{sub.shape[1]} features >90% ceros ({r:.0%})")
    return report


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import spacy

    print(f"Simbionte v6 — {FEATURES_TOTAL}D (10 marcos × 4 niveles + inter-nivel)")
    print(f"  N1 (tokens):    {FEATURES_N1} features")
    print(f"  N2 (oraciones): {FEATURES_N2} features")
    print(f"  N3 (parrafos):  {FEATURES_N3} features")
    print(f"  N4 (texto):     {FEATURES_N4} features")
    print(f"  Inter-nivel:    {FEATURES_INTER} features")
    print()

    nlp = spacy.load("es_dep_news_trf")

    with open('/tmp/texto_financiero.txt') as f:
        texto = f.read().strip()

    print(f"Procesando texto financiero ({len(texto.split())} palabras)...")
    doc = nlp(texto)
    vector, meta = calcular_vector_v6(doc)

    print(f"  Vector: {len(vector)}D en {meta['latencia_ms']}ms")
    print(f"  NaN: {np.isnan(vector).sum()}, Inf: {np.isinf(vector).sum()}")
    print(f"  Zeros: {(vector==0).sum()}/{len(vector)}")
    print(f"  Non-zero: {(vector!=0).sum()}/{len(vector)}")
    print(f"  Tokens: {meta['n_tokens']}, Oraciones: {meta['n_oraciones']}, Parrafos: {meta['n_parrafos']}")
    print(f"  Secuencia N2 (tipos oracion): {meta['seq_n2']}")
    print(f"  Secuencia N3 (tipos parrafo): {meta['seq_n3']}")
    print(f"  Secuencia N4 (movimientos):   {meta['seq_n4']}")

    # P30
    report = validar_vector_v6(vector.reshape(1, -1))
    if not report["errors"] and not report["warnings"]:
        print("\n  ✅ P30 PASADO")
    for w in report["warnings"]: print(f"  ⚠️ {w}")
    for e in report["errors"]: print(f"  ❌ {e}")

    # Comparar con v4
    print(f"\n  Comparación: v4=137D → v6=266D (+{266-137} features, +{(266-137)/137*100:.0f}%)")
