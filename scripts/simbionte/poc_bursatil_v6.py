"""
POC Bursátil v6 — Datos de mercado → 10 marcos × 4 niveles → geometría → isomorfismos
Fecha: 2026-04-12

Descarga datos reales de yfinance, los convierte en secuencias funcionales,
calcula los 10 marcos a 4 niveles, produce geometría 95D, y compara con
los isomorfismos textuales del catálogo fundacional.

$0 total. Mismos marcos_matematicos.py que texto.
"""

import sys
import os
import time
import json
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import yfinance as yf
from clasificador_bursatil import procesar_ohlcv, VELA_NAMES, SESION_NAMES, PERIODO_NAMES, CICLO_NAMES
from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL, FEATURES_POR_EJE, MARCOS
from geometria_isomorfismo import calcular_geometria_completa


def analizar_activo(ticker, period="1y", interval="1d"):
    """Analiza un activo financiero con Simbionte v6."""
    print(f"\n{'='*60}")
    print(f"ACTIVO: {ticker} ({period}, {interval})")
    print(f"{'='*60}")

    # Descargar
    t0 = time.time()
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if len(df) < 10:
        print(f"  ERROR: solo {len(df)} filas")
        return None
    dt_download = time.time() - t0

    # Flatten MultiIndex columns if needed
    if hasattr(df.columns, 'levels'):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    print(f"  Datos: {len(df)} velas, {df.index[0]} → {df.index[-1]}")
    print(f"  Precio: ${df['Close'].iloc[0]:.2f} → ${df['Close'].iloc[-1]:.2f} ({(df['Close'].iloc[-1]/df['Close'].iloc[0]-1)*100:+.1f}%)")
    print(f"  Download: {dt_download*1000:.0f}ms")

    # Clasificar
    t0 = time.time()
    result = procesar_ohlcv(df)
    if not result:
        print("  ERROR: no se pudo procesar")
        return None
    dt_clasif = time.time() - t0

    print(f"\n  CLASIFICACIÓN ({dt_clasif*1000:.0f}ms):")
    from collections import Counter
    for nivel, seq, names in [
        ("N1 (velas)", result["seq_n1"], VELA_NAMES),
        ("N2 (sesiones)", result["seq_n2"], SESION_NAMES),
        ("N3 (períodos)", result["seq_n3"], PERIODO_NAMES),
        ("N4 (ciclo)", result["seq_n4"], CICLO_NAMES),
    ]:
        counts = Counter(seq)
        top3 = counts.most_common(3)
        top_str = ", ".join(f"{names[k]}={v}" for k, v in top3)
        print(f"    {nivel}: {len(seq)} items → {top_str}")

    # 10 marcos × 4 niveles
    t0 = time.time()
    v_n1 = calcular_10_ejes(result["seq_n1"], result["n_tipos"]["N1"])
    v_n2 = calcular_10_ejes(result["seq_n2"], result["n_tipos"]["N2"])
    v_n3 = calcular_10_ejes(result["seq_n3"], result["n_tipos"]["N3"])
    v_n4 = calcular_10_ejes(result["seq_n4"], result["n_tipos"]["N4"])
    dt_marcos = time.time() - t0

    vector = np.concatenate([v_n1, v_n2, v_n3, v_n4])
    print(f"\n  VECTOR: {len(vector)}D en {dt_marcos*1000:.0f}ms")

    # Geometría
    t0 = time.time()
    vectores = {"N1": v_n1, "N2": v_n2, "N3": v_n3, "N4": v_n4}
    geo = calcular_geometria_completa(vectores)
    dt_geo = time.time() - t0

    print(f"  GEOMETRÍA: {geo['n_features']}D en {dt_geo*1000:.0f}ms")
    print(f"  Profundidad patrón: {geo['profundidad_patron']}")

    for nivel in ["N1", "N2", "N3", "N4"]:
        g = geo["geometrias"][nivel]
        dom = g["forma"]["dominantes"]
        sym = g["forma"]["simetria"]
        coh = g["forma"]["coherencia"]
        if dom:
            print(f"    {nivel}: dominantes={dom}, simetría={sym:.3f}, coherencia={coh:.3f}")

    # Similaridades inter-nivel
    for pair, s in geo["similaridades"].items():
        homo = s["homomorfismo"]
        label = "PROFUNDO" if homo > 0.7 else "MEDIO" if homo > 0.4 else "SUPERFICIAL"
        print(f"    {pair}: homomorfismo={homo:.3f} ({label})")

    return {
        "ticker": ticker,
        "n_velas": len(result["seq_n1"]),
        "cambio_pct": result["metadata"]["cambio_total_pct"],
        "profundidad": geo["profundidad_patron"],
        "dominantes": {
            nivel: geo["geometrias"][nivel]["forma"]["dominantes"]
            for nivel in ["N1", "N2", "N3", "N4"]
        },
        "simetria": {
            nivel: geo["geometrias"][nivel]["forma"]["simetria"]
            for nivel in ["N1", "N2", "N3", "N4"]
        },
        "vector_geo": geo["vector_pgvector"],
        "geo": geo,
    }


if __name__ == "__main__":
    tickers = [
        # Acciones US
        "AAPL",   # Apple — tech mega cap
        "TSLA",   # Tesla — alta volatilidad
        "JPM",    # JPMorgan — banca
        "XOM",    # ExxonMobil — energía
        # Índices
        "SPY",    # S&P 500
        "QQQ",    # Nasdaq 100
        # Crypto
        "BTC-USD",  # Bitcoin
        "ETH-USD",  # Ethereum
    ]

    resultados = {}
    for ticker in tickers:
        r = analizar_activo(ticker, period="1y", interval="1d")
        if r:
            resultados[ticker] = r

    # Comparación
    print(f"\n\n{'#'*60}")
    print(f"COMPARACIÓN DE GEOMETRÍAS BURSÁTILES")
    print(f"{'#'*60}")

    print(f"\n{'Ticker':<10s} {'Cambio%':>8s} {'Prof':>6s} {'N1 dom':<20s} {'N2 dom':<20s} {'N4 dom':<15s}")
    print("-" * 85)
    for t, r in resultados.items():
        n1d = ",".join(r["dominantes"]["N1"][:2]) if r["dominantes"]["N1"] else "-"
        n2d = ",".join(r["dominantes"]["N2"][:2]) if r["dominantes"]["N2"] else "-"
        n4d = ",".join(r["dominantes"]["N4"][:2]) if r["dominantes"]["N4"] else "-"
        print(f"{t:<10s} {r['cambio_pct']:>+7.1f}% {r['profundidad']:>6.3f} {n1d:<20s} {n2d:<20s} {n4d:<15s}")

    # Clustering
    if len(resultados) >= 3:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler

        X = np.array([r["vector_geo"] for r in resultados.values()])
        X_norm = StandardScaler().fit_transform(X)
        X_norm = np.nan_to_num(X_norm, 0)

        km = KMeans(n_clusters=min(3, len(resultados)), random_state=42, n_init=10)
        labels = km.fit_predict(X_norm)

        print(f"\n  CLUSTERS:")
        for i, (t, r) in enumerate(resultados.items()):
            print(f"    {t}: cluster {labels[i]}")

    # Guardar
    save = {
        "version": "poc_bursatil_v6",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "activos": {t: {
            "cambio_pct": r["cambio_pct"],
            "profundidad": r["profundidad"],
            "dominantes": r["dominantes"],
            "simetria": r["simetria"],
        } for t, r in resultados.items()},
    }
    path = os.path.join(os.path.dirname(__file__), "../../data/poc_bursatil_v6.json")
    with open(path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\nGuardado en {path}")
