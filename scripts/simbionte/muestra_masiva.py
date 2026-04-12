"""
Muestra Masiva — 10 lentes sobre datos reales + sinteticos a escala.

Fecha: 2026-04-12

Pipeline:
  1. Descargar S&P 500 + crypto + commodities via yfinance ($0)
  2. Convertir OHLCV a series de metricas financieras
  3. Generar 500 empresas sinteticas (6 tipos)
  4. Aplicar 10 lentes a TODOS
  5. Calcular vector 620D por entidad
  6. Clustering: encontrar grupos naturales
  7. Comparar geometrias mercado vs empresa
  8. Detectar isomorfismos cross-dominio

$0 total (yfinance + compute local)
"""

import sys
import os
import time
import json
import numpy as np
from collections import Counter, defaultdict
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(__file__))

import yfinance as yf

from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL
from geometria_isomorfismo import calcular_geometria_completa
from lentes_matematicas import aplicar_10_lentes, LENTES
from clasificador_empresarial import generar_empresa


# ============================================================
# S&P 500 TICKERS
# ============================================================

SP500_TICKERS = [
    # Tech (50)
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "META", "AVGO", "ADBE", "CRM", "CSCO",
    "INTC", "AMD", "QCOM", "TXN", "NOW", "INTU", "AMAT", "ADI", "LRCX", "KLAC",
    "MCHP", "SNPS", "CDNS", "FTNT", "PANW", "CRWD", "TEAM", "WDAY", "ZS", "DDOG",
    "SNOW", "NET", "MDB", "HUBS", "TTD", "BILL", "OKTA", "ZM", "DOCU", "TWLO",
    "PLTR", "PATH", "U", "RBLX", "COIN", "HOOD", "SOFI", "AFRM", "SQ", "PYPL",
    # Finance (30)
    "JPM", "V", "MA", "BLK", "GS", "MS", "BAC", "WFC", "SCHW", "AXP",
    "C", "USB", "PNC", "CME", "ICE", "SPGI", "MCO", "MSCI", "CBOE", "NDAQ",
    "BX", "KKR", "APO", "ARES", "OWL", "TFC", "FITB", "RF", "KEY", "CFG",
    # Health (25)
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
    "AMGN", "GILD", "ISRG", "VRTX", "SYK", "MDT", "BDX", "EW", "ZTS", "REGN",
    "BIIB", "ILMN", "DXCM", "ALGN", "HOLX",
    # Consumer (25)
    "PG", "KO", "PEP", "WMT", "COST", "MCD", "HD", "LOW", "TGT", "CL",
    "MDLZ", "EL", "GIS", "KHC", "MO", "PM", "STZ", "NKE", "SBUX", "CMG",
    "LULU", "DG", "DLTR", "ROST", "TJX",
    # Energy (15)
    "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "OXY",
    "HES", "DVN", "FANG", "HAL", "BKR",
    # Industrial (20)
    "CAT", "GE", "HON", "UNP", "RTX", "BA", "DE", "LMT", "NOC", "GD",
    "MMM", "EMR", "ITW", "FDX", "NSC", "CSX", "WM", "RSG", "VRSK", "IR",
    # Real Estate (10)
    "AMT", "PLD", "CCI", "EQIX", "PSA", "DLR", "SPG", "O", "WELL", "AVB",
    # Utilities (10)
    "NEE", "SO", "DUK", "AEP", "D", "SRE", "EXC", "XEL", "WEC", "ES",
    # Crypto + Indices + Commodities (15)
    "BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD",
    "SPY", "QQQ", "IWM", "DIA", "VTI",
    "GLD", "SLV", "USO", "UNG", "WEAT",
]

SECTOR_MAP = {}
for t in SP500_TICKERS[:50]: SECTOR_MAP[t] = "tech"
for t in SP500_TICKERS[50:80]: SECTOR_MAP[t] = "finance"
for t in SP500_TICKERS[80:105]: SECTOR_MAP[t] = "health"
for t in SP500_TICKERS[105:130]: SECTOR_MAP[t] = "consumer"
for t in SP500_TICKERS[130:145]: SECTOR_MAP[t] = "energy"
for t in SP500_TICKERS[145:165]: SECTOR_MAP[t] = "industrial"
for t in SP500_TICKERS[165:175]: SECTOR_MAP[t] = "realestate"
for t in SP500_TICKERS[175:185]: SECTOR_MAP[t] = "utilities"
for t in SP500_TICKERS[185:]: SECTOR_MAP[t] = "other"


def ohlcv_a_series(df):
    """Convierte DataFrame OHLCV a series_dict para las 10 lentes.

    Calcula metricas financieras rolling y las devuelve como series temporales.
    """
    if len(df) < 60:
        return None

    close = df["Close"].values.astype(float)
    volume = df["Volume"].values.astype(float)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)

    # Retornos diarios
    returns = np.diff(close) / np.where(np.abs(close[:-1]) > 1e-10, close[:-1], 1e-10)

    # Ventana rolling de 20 dias
    window = 20
    n = len(returns)
    if n < window + 10:
        return None

    series = {}
    n_points = n - window + 1

    # Revenue proxy = precio (para compatibilidad con lentes)
    series["precio"] = [float(close[i + window - 1]) for i in range(n_points)]

    # Retorno rolling
    series["retorno"] = [float(np.mean(returns[i:i+window])) for i in range(n_points)]

    # Volatilidad rolling
    series["volatilidad"] = [float(np.std(returns[i:i+window])) for i in range(n_points)]

    # Sharpe rolling
    series["sharpe"] = [
        float(np.mean(returns[i:i+window]) / max(np.std(returns[i:i+window]), 1e-10))
        for i in range(n_points)
    ]

    # Max drawdown rolling
    def rolling_dd(closes, w):
        dd = []
        for i in range(len(closes) - w + 1):
            chunk = closes[i:i+w]
            cummax = np.maximum.accumulate(chunk)
            drawdowns = (chunk - cummax) / np.where(cummax > 0, cummax, 1)
            dd.append(float(np.min(drawdowns)))
        return dd
    series["drawdown"] = rolling_dd(close[1:], window)[:n_points]

    # Volumen relativo
    vol_mean = np.convolve(volume[1:], np.ones(window)/window, mode='valid')
    vol_rel = volume[window:] / np.where(vol_mean[:n_points] > 0, vol_mean[:n_points], 1)
    series["volumen"] = [float(v) for v in vol_rel[:n_points]]

    # Rango (ATR proxy)
    ranges = (high - low)[1:]
    series["rango"] = [float(np.mean(ranges[i:i+window])) for i in range(n_points)]

    # Momentum 20d
    series["momentum"] = [float(close[i+window-1] / close[i] - 1) for i in range(n_points)]

    # RSI proxy (% dias positivos)
    series["rsi"] = [
        float(np.sum(returns[i:i+window] > 0) / window)
        for i in range(n_points)
    ]

    # Skewness rolling
    series["skewness"] = [
        float(np.mean(((returns[i:i+window] - np.mean(returns[i:i+window])) / max(np.std(returns[i:i+window]), 1e-10))**3))
        for i in range(n_points)
    ]

    # Correlacion con propio lag (autocorrelacion)
    series["autocorr"] = []
    for i in range(n_points):
        chunk = returns[i:i+window]
        if len(chunk) > 2 and np.std(chunk) > 1e-10:
            ac = np.corrcoef(chunk[:-1], chunk[1:])[0, 1]
            series["autocorr"].append(float(ac) if np.isfinite(ac) else 0.0)
        else:
            series["autocorr"].append(0.0)

    # Beta proxy (correlacion con propia tendencia)
    series["trend_strength"] = []
    for i in range(n_points):
        chunk = close[i+1:i+window+1]
        if len(chunk) > 2:
            x = np.arange(len(chunk))
            r = np.corrcoef(x, chunk)[0, 1]
            series["trend_strength"].append(float(r) if np.isfinite(r) else 0.0)
        else:
            series["trend_strength"].append(0.0)

    # Verificar que todas las series tienen la misma longitud
    min_len = min(len(v) for v in series.values())
    series = {k: v[:min_len] for k, v in series.items()}

    return series


def empresa_a_series(meses):
    """Convierte meses de empresa sintetica a series_dict."""
    metricas = ["revenue", "churn", "ltv_cac", "nps", "conversion",
                "margen_bruto", "actividad", "adoption", "cash_flow",
                "concentracion", "equipo_rotacion", "expansion"]
    return {m: [float(mes.get(m, 0)) for mes in meses] for m in metricas}


def main():
    print("=" * 70)
    print("MUESTRA MASIVA — 10 lentes sobre datos reales + sinteticos")
    print("=" * 70)

    # ========================================
    # FASE 1: DESCARGAR DATOS DE MERCADO
    # ========================================
    print(f"\n{'='*70}")
    print("FASE 1: Descargando {0} tickers via yfinance...".format(len(SP500_TICKERS)))
    print(f"{'='*70}")

    t0_total = time.time()
    datos_mercado = {}
    errores = []

    for i, ticker in enumerate(SP500_TICKERS):
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if hasattr(df.columns, 'levels'):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            if len(df) >= 60:
                datos_mercado[ticker] = df
        except Exception:
            errores.append(ticker)

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(SP500_TICKERS)}] ok={len(datos_mercado)} err={len(errores)}")

    dt_download = time.time() - t0_total
    print(f"  Descarga: {len(datos_mercado)} tickers en {dt_download:.0f}s")

    # ========================================
    # FASE 2: CONVERTIR A SERIES + 10 LENTES
    # ========================================
    print(f"\n{'='*70}")
    print("FASE 2: Aplicando 10 lentes a {0} tickers...".format(len(datos_mercado)))
    print(f"{'='*70}")

    vectores_mercado = {}
    meta_mercado = {}
    t0 = time.time()

    for ticker, df in datos_mercado.items():
        series = ohlcv_a_series(df)
        if series is None:
            continue

        resultados_lentes = aplicar_10_lentes(series)

        # Vector 620D: 10 lentes × 62 features
        sub_vectors = []
        for nombre_lente in LENTES.keys():
            res = resultados_lentes[nombre_lente]
            if len(res["secuencia"]) >= 2:
                v = calcular_10_ejes(res["secuencia"], res["n_tipos"])
            else:
                v = np.zeros(FEATURES_POR_NIVEL)
            sub_vectors.append(v)

        vector = np.concatenate(sub_vectors)
        vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)
        vectores_mercado[ticker] = vector

        meta_mercado[ticker] = {
            "sector": SECTOR_MAP.get(ticker, "other"),
            "n_tokens": sum(r["n_tokens"] for r in resultados_lentes.values()),
            "cambio_1y": float((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100),
        }

    dt_lentes = time.time() - t0
    print(f"  {len(vectores_mercado)} tickers procesados en {dt_lentes:.1f}s ({dt_lentes/max(len(vectores_mercado),1)*1000:.0f}ms/ticker)")

    # ========================================
    # FASE 3: GENERAR EMPRESAS SINTETICAS
    # ========================================
    print(f"\n{'='*70}")
    print("FASE 3: Generando 500 empresas sinteticas...")
    print(f"{'='*70}")

    tipos_empresa = {
        "saas_growth": 100,
        "saas_mature": 80,
        "saas_declining": 60,
        "smb_stable": 100,
        "startup_burn": 80,
        "ecommerce": 80,
    }

    vectores_empresa = {}
    meta_empresa = {}
    t0 = time.time()

    empresa_id = 0
    for tipo, n in tipos_empresa.items():
        for i in range(n):
            nombre = f"{tipo}_{i}"
            meses = generar_empresa(tipo, n_meses=24, seed=empresa_id * 31337)
            series = empresa_a_series(meses)

            resultados_lentes = aplicar_10_lentes(series)

            sub_vectors = []
            for nombre_lente in LENTES.keys():
                res = resultados_lentes[nombre_lente]
                if len(res["secuencia"]) >= 2:
                    v = calcular_10_ejes(res["secuencia"], res["n_tipos"])
                else:
                    v = np.zeros(FEATURES_POR_NIVEL)
                sub_vectors.append(v)

            vector = np.concatenate(sub_vectors)
            vector = np.nan_to_num(vector, nan=0.0, posinf=0.0, neginf=0.0)
            vectores_empresa[nombre] = vector

            meta_empresa[nombre] = {
                "tipo": tipo,
                "rev_fin": meses[-1].get("revenue", 0),
                "churn": meses[-1].get("churn", 0),
                "ltv_cac": meses[-1].get("ltv_cac", 0),
            }
            empresa_id += 1

    dt_empresa = time.time() - t0
    print(f"  {len(vectores_empresa)} empresas en {dt_empresa:.1f}s ({dt_empresa/max(len(vectores_empresa),1)*1000:.0f}ms/empresa)")

    # ========================================
    # FASE 4: ANALISIS A ESCALA
    # ========================================
    print(f"\n{'='*70}")
    print("FASE 4: Analisis a escala")
    print(f"{'='*70}")

    # 4a. CLUSTERING de mercado
    print(f"\n  --- CLUSTERING MERCADO ({len(vectores_mercado)} tickers) ---")
    tickers_list = sorted(vectores_mercado.keys())
    X_mercado = np.array([vectores_mercado[t] for t in tickers_list])

    n_clusters = 8
    kmeans_m = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels_m = kmeans_m.fit_predict(X_mercado)

    for c in range(n_clusters):
        idx = [i for i, l in enumerate(labels_m) if l == c]
        tickers_c = [tickers_list[i] for i in idx]
        sectores = Counter([meta_mercado[t]["sector"] for t in tickers_c])
        cambios = [meta_mercado[t]["cambio_1y"] for t in tickers_c]
        print(f"\n  Cluster {c} ({len(idx)} tickers):")
        print(f"    Sectores: {dict(sectores)}")
        print(f"    Cambio 1Y: {np.mean(cambios):+.1f}% (median {np.median(cambios):+.1f}%)")
        print(f"    Ejemplos: {tickers_c[:8]}")

    # 4b. CLUSTERING de empresas
    print(f"\n  --- CLUSTERING EMPRESAS ({len(vectores_empresa)} empresas) ---")
    empresas_list = sorted(vectores_empresa.keys())
    X_empresa = np.array([vectores_empresa[e] for e in empresas_list])

    kmeans_e = KMeans(n_clusters=6, random_state=42, n_init=10)
    labels_e = kmeans_e.fit_predict(X_empresa)

    for c in range(6):
        idx = [i for i, l in enumerate(labels_e) if l == c]
        nombres_c = [empresas_list[i] for i in idx]
        tipos = Counter([meta_empresa[n]["tipo"] for n in nombres_c])
        revs = [meta_empresa[n]["rev_fin"] for n in nombres_c]
        churns = [meta_empresa[n]["churn"] for n in nombres_c]
        print(f"\n  Cluster {c} ({len(idx)} empresas):")
        print(f"    Tipos: {dict(tipos)}")
        print(f"    Revenue medio: ${np.mean(revs):,.0f}")
        print(f"    Churn medio: {np.mean(churns):.1%}")

    # 4c. ISOMORFISMO CROSS-DOMINIO: mercado vs empresa
    print(f"\n  --- ISOMORFISMOS CROSS-DOMINIO ---")

    # Centroides de cada cluster de mercado
    centroids_m = kmeans_m.cluster_centers_
    centroids_e = kmeans_e.cluster_centers_

    # Similaridad coseno entre clusters de mercado y clusters de empresa
    cross_sim = cosine_similarity(centroids_m, centroids_e)

    print(f"\n  Similaridad coseno (clusters mercado × clusters empresa):")
    print(f"  {'':>12s}", end="")
    for j in range(6):
        print(f"  emp_{j}", end="")
    print()
    for i in range(n_clusters):
        print(f"  mkt_{i:>6d}", end="")
        for j in range(6):
            sim = cross_sim[i, j]
            marker = " ***" if sim > 0.85 else " ** " if sim > 0.75 else "    "
            print(f"  {sim:.3f}{marker}", end="")
        print()

    # Top matches
    print(f"\n  Top isomorfismos cross-dominio (coseno > 0.80):")
    for i in range(n_clusters):
        for j in range(6):
            if cross_sim[i, j] > 0.80:
                # Describir cada cluster
                mkt_sectores = Counter([meta_mercado[tickers_list[k]]["sector"] for k in range(len(tickers_list)) if labels_m[k] == i])
                emp_tipos = Counter([meta_empresa[empresas_list[k]]["tipo"] for k in range(len(empresas_list)) if labels_e[k] == j])
                print(f"    mkt_{i} ({dict(mkt_sectores)}) <-> emp_{j} ({dict(emp_tipos)}) = {cross_sim[i,j]:.3f}")

    # 4d. VECINOS MAS CERCANOS cross-dominio
    print(f"\n  --- VECINOS CERCANOS: ¿Qué ticker se parece a qué empresa? ---")

    # Para cada tipo de empresa, encontrar el ticker mas parecido
    for tipo in tipos_empresa.keys():
        tipo_nombres = [n for n in empresas_list if meta_empresa[n]["tipo"] == tipo]
        if not tipo_nombres:
            continue
        # Centroide del tipo
        tipo_vectors = np.array([vectores_empresa[n] for n in tipo_nombres])
        centroid = np.mean(tipo_vectors, axis=0, keepdims=True)

        # Similaridad con todos los tickers
        sims = cosine_similarity(centroid, X_mercado)[0]
        top_idx = np.argsort(sims)[::-1][:5]

        print(f"\n  {tipo}:")
        for idx in top_idx:
            t = tickers_list[idx]
            sector = meta_mercado[t]["sector"]
            cambio = meta_mercado[t]["cambio_1y"]
            print(f"    {t:<8s} ({sector:<12s}) cambio={cambio:+.1f}% sim={sims[idx]:.3f}")

    # ========================================
    # FASE 5: PCA - Estructura del espacio
    # ========================================
    print(f"\n{'='*70}")
    print("FASE 5: Estructura del espacio (PCA)")
    print(f"{'='*70}")

    # Combinar todos los vectores
    all_names = tickers_list + empresas_list
    all_vectors = np.vstack([X_mercado, X_empresa])
    all_domains = ["mercado"] * len(tickers_list) + ["empresa"] * len(empresas_list)

    pca = PCA(n_components=10)
    X_pca = pca.fit_transform(all_vectors)

    print(f"\n  Varianza explicada por componente:")
    for i, var in enumerate(pca.explained_variance_ratio_[:10]):
        bar = "█" * int(var * 100)
        print(f"    PC{i+1}: {var:.1%} {bar}")
    print(f"    Total (10 PCs): {sum(pca.explained_variance_ratio_[:10]):.1%}")

    # Separacion mercado vs empresa en PC1-PC2
    mercado_pc = X_pca[:len(tickers_list)]
    empresa_pc = X_pca[len(tickers_list):]

    print(f"\n  Centroide en PC1-PC2:")
    print(f"    Mercado:  PC1={np.mean(mercado_pc[:, 0]):.2f}  PC2={np.mean(mercado_pc[:, 1]):.2f}")
    print(f"    Empresa:  PC1={np.mean(empresa_pc[:, 0]):.2f}  PC2={np.mean(empresa_pc[:, 1]):.2f}")

    overlap = np.mean(cosine_similarity(
        mercado_pc[:, :3].mean(axis=0, keepdims=True),
        empresa_pc[:, :3].mean(axis=0, keepdims=True)
    ))
    print(f"    Overlap (coseno centroides PC1-3): {overlap:.3f}")

    # ========================================
    # RESUMEN FINAL
    # ========================================
    dt_total = time.time() - t0_total
    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"  Tickers descargados:   {len(datos_mercado)}")
    print(f"  Tickers procesados:    {len(vectores_mercado)}")
    print(f"  Empresas generadas:    {len(vectores_empresa)}")
    print(f"  Total entidades:       {len(vectores_mercado) + len(vectores_empresa)}")
    print(f"  Dimensiones vector:    620D (10 lentes × 62 features)")
    print(f"  Tiempo total:          {dt_total:.0f}s")
    print(f"  Coste:                 $0.00")

    # Guardar
    save = {
        "version": "muestra_masiva_v1",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "n_tickers": len(vectores_mercado),
        "n_empresas": len(vectores_empresa),
        "clusters_mercado": n_clusters,
        "clusters_empresa": 6,
        "pca_varianza_10": float(sum(pca.explained_variance_ratio_[:10])),
        "cross_sim_max": float(np.max(cross_sim)),
        "cross_sim_mean": float(np.mean(cross_sim)),
    }

    path = os.path.join(os.path.dirname(__file__), "../../data/muestra_masiva.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)

    # Guardar vectores para pgvector posterior
    np.save(path.replace(".json", "_mercado.npy"), X_mercado)
    np.save(path.replace(".json", "_empresa.npy"), X_empresa)
    np.save(path.replace(".json", "_nombres_mercado.npy"), np.array(tickers_list))
    np.save(path.replace(".json", "_nombres_empresa.npy"), np.array(empresas_list))

    print(f"\n  Artefactos guardados en data/muestra_masiva_*")
    print(f"\n{'='*70}")
    print(f"  $0.00 | {len(vectores_mercado) + len(vectores_empresa)} entidades | 620D | {dt_total:.0f}s")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
