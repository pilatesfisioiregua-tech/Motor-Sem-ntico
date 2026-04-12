"""
Firma Geometrica — Capa de abstraccion domain-invariant.

Fecha: 2026-04-12

Problema:
  Los vectores 620D (10 lentes × 62 features) discriminan DENTRO de cada dominio,
  pero las magnitudes absolutas separan mercado de empresa.
  Un ticker y una empresa con el MISMO patron tienen vectores en regiones diferentes.

Solucion:
  Extraer la FORMA del patron, no los valores.
  La firma geometrica captura:
    1. Perfil de importancia: qué lentes dominan (relativo, no absoluto)
    2. Red de correlaciones: qué lentes se mueven juntas
    3. Estructura interna: concentracion/dispersion dentro de cada lente
    4. Simetrias: qué familias de lentes se parecen entre si
    5. Firma de dominancia: patron categorico (top 3 lentes)

  La firma es INVARIANTE al dominio porque solo ve proporciones y relaciones,
  nunca magnitudes absolutas.

Output: vector ~120D que ES la forma del patron.
$0 total (compute local)
"""

import numpy as np
from scipy import stats as scipy_stats


LENTE_NOMBRES = [
    "estadistica", "conjuntos", "grafos", "markov", "juegos",
    "cibernetica", "sistemas", "topologia", "geometria_diff", "cinematica",
]

# Familias semanticas de lentes
FAMILIA_FORMA     = [0, 7, 8]    # estadistica, topologia, geometria_diff
FAMILIA_DINAMICA  = [3, 9, 5]    # markov, cinematica, cibernetica
FAMILIA_ESTRUCTURA = [2, 6, 1]   # grafos, sistemas, conjuntos
FAMILIA_AGENTES   = [4]          # juegos

FAMILIAS = {
    "forma":      FAMILIA_FORMA,
    "dinamica":   FAMILIA_DINAMICA,
    "estructura": FAMILIA_ESTRUCTURA,
    "agentes":    FAMILIA_AGENTES,
}


def calcular_firma(vector_620d):
    """Calcula la firma geometrica domain-invariant de un vector de 10 lentes.

    Args:
        vector_620d: np.array de 620 floats (10 lentes × 62 features)

    Returns:
        dict con:
          - "firma": np.array (~120D) — la firma geometrica
          - "perfil": np.array (10,) — importancia relativa de cada lente
          - "correlaciones": np.array (10, 10) — correlacion entre lentes
          - "dominantes": list[str] — top 3 lentes dominantes
          - "familia_dominante": str — familia con mayor magnitud
          - "n_features": int — dimensiones de la firma
    """
    v = np.nan_to_num(np.array(vector_620d, dtype=np.float64))
    assert len(v) == 620, f"Esperado 620D, recibido {len(v)}"

    # Separar en 10 sub-vectores de 62D
    lentes = [v[i*62:(i+1)*62] for i in range(10)]

    firma = []

    # =========================================
    # 1. PERFIL DE IMPORTANCIA (10D)
    # =========================================
    # Norma L2 de cada lente, normalizada a suma = 1
    normas = np.array([np.linalg.norm(l) for l in lentes])
    normas_sum = np.sum(normas)
    if normas_sum < 1e-10:
        perfil = np.ones(10) / 10
    else:
        perfil = normas / normas_sum

    firma.extend(perfil)  # 10D

    # =========================================
    # 2. ESTADISTICA DEL PERFIL (8D)
    # =========================================
    # Entropia del perfil (cuán distribuida está la importancia)
    perfil_pos = perfil[perfil > 1e-10]
    entropia = -np.sum(perfil_pos * np.log2(perfil_pos)) / np.log2(10) if len(perfil_pos) > 1 else 0
    firma.append(entropia)

    # Concentracion (Gini del perfil)
    sorted_p = np.sort(perfil)
    n = len(sorted_p)
    gini = (2 * np.sum((np.arange(1, n+1) * sorted_p)) / (n * np.sum(sorted_p)) - (n + 1) / n) if np.sum(sorted_p) > 0 else 0
    firma.append(gini)

    # Max/min ratio
    firma.append(np.max(perfil) / max(np.min(perfil), 1e-10))

    # Skewness del perfil
    firma.append(float(scipy_stats.skew(perfil)) if len(perfil) > 2 else 0)

    # Kurtosis del perfil
    firma.append(float(scipy_stats.kurtosis(perfil)) if len(perfil) > 3 else 0)

    # Top 3 concentracion (% de importancia en top 3)
    top3_pct = np.sum(np.sort(perfil)[-3:])
    firma.append(top3_pct)

    # Distancia al perfil uniforme
    uniforme = np.ones(10) / 10
    dist_uniforme = np.linalg.norm(perfil - uniforme)
    firma.append(dist_uniforme)

    # Ratio familia mas fuerte / mas debil
    fam_normas = {}
    for fname, fidx in FAMILIAS.items():
        fam_normas[fname] = np.sum(perfil[fidx])
    fam_vals = list(fam_normas.values())
    firma.append(max(fam_vals) / max(min(fam_vals), 1e-10))
    # Total: 8D

    # =========================================
    # 3. CORRELACIONES ENTRE LENTES (45D + 10D)
    # =========================================
    # Matriz de correlacion 10×10
    # Cada lente es un vector de 62D, correlacionar entre pares
    lentes_arr = np.array(lentes)  # (10, 62)

    # Normalizar cada lente (L2) para que la correlacion sea sobre forma, no magnitud
    lentes_norm = np.zeros_like(lentes_arr)
    for i in range(10):
        n_l = np.linalg.norm(lentes_arr[i])
        lentes_norm[i] = lentes_arr[i] / n_l if n_l > 1e-10 else lentes_arr[i]

    corr = np.corrcoef(lentes_norm)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)

    # Triangulo superior (45 pares)
    for i in range(10):
        for j in range(i+1, 10):
            firma.append(corr[i, j])
    # 45D

    # Centralidad de cada lente (media de sus correlaciones con las demas)
    for i in range(10):
        centralidad = np.mean(np.abs(corr[i, :])) - 1/10  # descontar self
        firma.append(centralidad)
    # 10D

    # =========================================
    # 4. ESTRUCTURA INTERNA POR LENTE (50D: 5 features × 10 lentes)
    # =========================================
    for i in range(10):
        l = lentes_norm[i]  # Usar normalizado

        # Entropia interna
        l_abs = np.abs(l)
        l_sum = np.sum(l_abs)
        if l_sum > 1e-10:
            p = l_abs / l_sum
            p_pos = p[p > 1e-10]
            ent = -np.sum(p_pos * np.log2(p_pos)) / np.log2(62) if len(p_pos) > 1 else 0
        else:
            ent = 0
        firma.append(ent)

        # Ratio features activas (|x| > 0.01)
        activas = np.sum(np.abs(l) > 0.01) / 62
        firma.append(activas)

        # Concentracion (top 5 features como % del total)
        top5 = np.sum(np.sort(np.abs(l))[-5:]) / max(l_sum, 1e-10)
        firma.append(top5)

        # Skewness interna
        firma.append(float(scipy_stats.skew(l)) if np.std(l) > 1e-10 else 0)

        # Signo dominante (% de features positivas)
        n_pos = np.sum(l > 0.01) / max(np.sum(np.abs(l) > 0.01), 1)
        firma.append(n_pos)
    # 50D

    # =========================================
    # 5. SIMETRIAS ENTRE FAMILIAS (6D)
    # =========================================
    # Similaridad coseno entre familias
    fam_vectors = {}
    for fname, fidx in FAMILIAS.items():
        fv = np.concatenate([lentes_norm[i] for i in fidx])
        n_fv = np.linalg.norm(fv)
        fam_vectors[fname] = fv / n_fv if n_fv > 1e-10 else fv

    # Representar cada familia como media de sus lentes normalizadas (62D)
    fam_mean_vectors = {}
    for fname, fidx in FAMILIAS.items():
        mean_v = np.mean([lentes_norm[i] for i in fidx], axis=0)
        n_fv = np.linalg.norm(mean_v)
        fam_mean_vectors[fname] = mean_v / n_fv if n_fv > 1e-10 else mean_v

    fam_names = list(fam_mean_vectors.keys())
    for i in range(len(fam_names)):
        for j in range(i+1, len(fam_names)):
            sim = np.dot(fam_mean_vectors[fam_names[i]], fam_mean_vectors[fam_names[j]])
            if not np.isfinite(sim):
                sim = 0.0
            firma.append(sim)
    # 6D (4 familias → 6 pares)

    # =========================================
    # CONSTRUIR OUTPUT
    # =========================================
    firma_array = np.array(firma, dtype=np.float64)
    firma_array = np.nan_to_num(firma_array, nan=0.0, posinf=0.0, neginf=0.0)

    # Dominantes
    top_idx = np.argsort(perfil)[::-1][:3]
    dominantes = [LENTE_NOMBRES[i] for i in top_idx]

    # Familia dominante
    familia_dominante = max(fam_normas, key=fam_normas.get)

    return {
        "firma": firma_array,
        "perfil": perfil,
        "correlaciones": corr,
        "dominantes": dominantes,
        "familia_dominante": familia_dominante,
        "familias": fam_normas,
        "n_features": len(firma_array),
    }


def comparar_firmas(firma_a, firma_b):
    """Compara dos firmas geometricas.

    Returns:
        dict con metricas de similaridad
    """
    fa = firma_a["firma"]
    fb = firma_b["firma"]

    # Coseno
    dot = np.dot(fa, fb)
    na, nb = np.linalg.norm(fa), np.linalg.norm(fb)
    coseno = dot / (na * nb) if na > 1e-10 and nb > 1e-10 else 0

    # Euclidea normalizada
    euclidea = np.linalg.norm(fa - fb) / max(na, nb, 1e-10)

    # Correlacion de perfiles
    corr_perfil = np.corrcoef(firma_a["perfil"], firma_b["perfil"])[0, 1]
    corr_perfil = 0 if not np.isfinite(corr_perfil) else corr_perfil

    # Jaccard de dominantes
    set_a = set(firma_a["dominantes"])
    set_b = set(firma_b["dominantes"])
    jaccard_dom = len(set_a & set_b) / max(len(set_a | set_b), 1)

    # Misma familia dominante
    misma_familia = firma_a["familia_dominante"] == firma_b["familia_dominante"]

    return {
        "coseno": float(coseno),
        "euclidea": float(euclidea),
        "corr_perfil": float(corr_perfil),
        "jaccard_dominantes": float(jaccard_dom),
        "misma_familia": misma_familia,
        # Score compuesto
        "isomorfismo": float(0.4 * coseno + 0.3 * corr_perfil + 0.2 * jaccard_dom + 0.1 * int(misma_familia)),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import time
    from sklearn.cluster import KMeans
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.decomposition import PCA
    from collections import Counter

    # Cargar datos de la muestra masiva
    X_m = np.load("../../data/muestra_masiva_mercado.npy")
    X_e = np.load("../../data/muestra_masiva_empresa.npy")
    names_m = list(np.load("../../data/muestra_masiva_nombres_mercado.npy"))
    names_e = list(np.load("../../data/muestra_masiva_nombres_empresa.npy"))

    print("=" * 70)
    print("FIRMA GEOMETRICA — Capa de abstraccion domain-invariant")
    print("=" * 70)

    # Calcular firma para todo
    t0 = time.time()

    firmas_m = {}
    for i, name in enumerate(names_m):
        firmas_m[name] = calcular_firma(X_m[i])

    firmas_e = {}
    for i, name in enumerate(names_e):
        firmas_e[name] = calcular_firma(X_e[i])

    dt = time.time() - t0
    n_features = list(firmas_m.values())[0]["n_features"]
    print(f"\n  {len(firmas_m) + len(firmas_e)} firmas calculadas en {dt:.1f}s")
    print(f"  Dimensiones firma: {n_features}D")

    # Construir matrices
    F_m = np.array([firmas_m[n]["firma"] for n in names_m])
    F_e = np.array([firmas_e[n]["firma"] for n in names_e])
    F_all = np.vstack([F_m, F_e])
    all_names = names_m + names_e
    all_domain = ["M"] * len(names_m) + ["E"] * len(names_e)

    # PCA
    pca = PCA(n_components=10)
    X_pca = pca.fit_transform(F_all)
    print(f"\n  PCA sobre firmas:")
    for i in range(10):
        bar = "█" * int(pca.explained_variance_ratio_[i] * 100)
        print(f"    PC{i+1}: {pca.explained_variance_ratio_[i]:.1%} {bar}")
    print(f"    Total 10: {sum(pca.explained_variance_ratio_[:10]):.1%}")

    # Separacion dominios en PC1-PC2
    m_pc = X_pca[:len(names_m)]
    e_pc = X_pca[len(names_m):]
    overlap = cosine_similarity(
        m_pc[:, :3].mean(axis=0, keepdims=True),
        e_pc[:, :3].mean(axis=0, keepdims=True)
    )[0, 0]
    print(f"\n  Overlap dominios (coseno centroides PC1-3): {overlap:.3f}")
    print(f"  (antes de firma: -1.000 — completamente separados)")

    # Clustering conjunto
    print(f"\n{'='*70}")
    print("CLUSTERING CONJUNTO (firmas)")
    print(f"{'='*70}")

    km = KMeans(10, random_state=42, n_init=10)
    labels = km.fit_predict(F_all)

    # Sector map simplificado
    tickers_crypto = {"BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD"}
    tickers_tech_top = {"AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "ADBE", "CRM", "AMD", "INTC"}

    for c in range(10):
        idx = [i for i, l in enumerate(labels) if l == c]
        domains = Counter([all_domain[i] for i in idx])
        n_m = domains.get("M", 0)
        n_e = domains.get("E", 0)

        if n_m + n_e < 3:
            continue

        mercado_names = [all_names[i] for i in idx if all_domain[i] == "M"]
        empresa_names = [all_names[i] for i in idx if all_domain[i] == "E"]
        emp_tipos = Counter([n.rsplit("_", 1)[0] for n in empresa_names])

        # Dominantes del cluster
        cluster_firmas = [firmas_m.get(all_names[i]) or firmas_e.get(all_names[i]) for i in idx]
        dom_counter = Counter()
        fam_counter = Counter()
        for f in cluster_firmas:
            if f:
                for d in f["dominantes"]:
                    dom_counter[d] += 1
                fam_counter[f["familia_dominante"]] += 1

        mix = "MIXTO" if n_m > 0 and n_e > 0 else ("MERCADO" if n_e == 0 else "EMPRESA")

        print(f"\n  Cluster {c} [{mix}] ({n_m}M + {n_e}E = {n_m+n_e}):")
        print(f"    Lentes dominantes: {dom_counter.most_common(3)}")
        print(f"    Familia dominante: {fam_counter.most_common(2)}")
        if mercado_names:
            print(f"    Mercado: {mercado_names[:8]}")
        if empresa_names:
            print(f"    Empresa tipos: {dict(emp_tipos.most_common(4))}")

    # Cross-domain: vecinos mas cercanos
    print(f"\n{'='*70}")
    print("VECINOS CROSS-DOMINIO (firmas)")
    print(f"{'='*70}")

    cross_sim = cosine_similarity(F_m, F_e)

    # Para cada tipo de empresa, top 5 tickers mas parecidos
    tipos_empresa = set(n.rsplit("_", 1)[0] for n in names_e)
    for tipo in sorted(tipos_empresa):
        tipo_idx = [i for i, n in enumerate(names_e) if n.startswith(tipo + "_")]
        if not tipo_idx:
            continue

        # Media de similaridad del tipo con cada ticker
        sim_media = np.mean(cross_sim[:, tipo_idx], axis=1)
        top_idx = np.argsort(sim_media)[::-1][:5]

        print(f"\n  {tipo}:")
        for idx in top_idx:
            ticker = names_m[idx]
            sim = sim_media[idx]
            firma_t = firmas_m[ticker]
            print(f"    {ticker:<8s} sim={sim:.3f} dom={firma_t['dominantes']} fam={firma_t['familia_dominante']}")

    # Isomorfismos especificos
    print(f"\n{'='*70}")
    print("ISOMORFISMOS ESPECIFICOS")
    print(f"{'='*70}")

    # Encontrar los pares cross-dominio con mayor isomorfismo
    print(f"\n  Top 20 pares mercado-empresa (por score isomorfismo):")
    scores = []
    for i, nm in enumerate(names_m):
        for j, ne in enumerate(names_e):
            comp = comparar_firmas(firmas_m[nm], firmas_e[ne])
            scores.append((nm, ne, comp["isomorfismo"], comp))

    scores.sort(key=lambda x: x[2], reverse=True)
    seen_types = set()
    count = 0
    for ticker, empresa, score, comp in scores:
        tipo = empresa.rsplit("_", 1)[0]
        key = (ticker, tipo)
        if key in seen_types:
            continue
        seen_types.add(key)

        fm = firmas_m[ticker]
        fe = firmas_e[empresa]
        print(f"    {ticker:<8s} <-> {tipo:<16s} iso={score:.3f} "
              f"cos={comp['coseno']:.3f} corr={comp['corr_perfil']:.3f} "
              f"dom_m={fm['dominantes'][:2]} dom_e={fe['dominantes'][:2]}")
        count += 1
        if count >= 20:
            break

    print(f"\n{'='*70}")
    print(f"  {n_features}D firma | {len(firmas_m)+len(firmas_e)} entidades | $0")
    print(f"{'='*70}")
