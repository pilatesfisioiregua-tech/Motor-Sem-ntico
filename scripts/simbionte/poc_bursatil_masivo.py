"""
POC Bursátil Masivo — Simbionte v6 sobre datos reales a escala
Fecha: 2026-04-12

Descarga y analiza:
  - S&P 500 completo (~500 empresas × 1 año = ~125.000 sesiones)
  - Cada empresa = 1 "texto" bursátil → 1 geometría 95D
  - Clustering → isomorfismos bursátiles emergentes
  - Comparación con isomorfismos textuales del catálogo fundacional

$0 total (yfinance gratuito + compute local)
"""

import sys
import os
import time
import json
import numpy as np
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))

import yfinance as yf
import pandas as pd
from clasificador_bursatil import procesar_ohlcv
from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL, MARCOS
from geometria_isomorfismo import calcular_geometria_completa


def get_sp500_tickers():
    """Obtiene lista de tickers del S&P 500 via Wikipedia."""
    try:
        table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]
        tickers = table['Symbol'].tolist()
        # Limpiar: algunos tienen . que yfinance quiere como -
        tickers = [t.replace('.', '-') for t in tickers]
        return tickers
    except Exception as e:
        print(f"Error obteniendo S&P 500: {e}")
        # Fallback: top 100 por capitalización
        return [
            "AAPL","MSFT","AMZN","NVDA","GOOGL","META","TSLA","BRK-B","UNH","JNJ",
            "JPM","V","PG","XOM","HD","MA","CVX","MRK","ABBV","PEP","KO","AVGO",
            "COST","LLY","WMT","TMO","MCD","CSCO","ACN","ABT","DHR","NEE","ADBE",
            "CRM","TXN","CMCSA","BMY","PM","UNP","RTX","HON","INTC","AMGN","IBM",
            "QCOM","LOW","SPGI","ELV","GE","CAT","INTU","ISRG","BA","SYK","BLK",
            "ADP","MDLZ","GILD","DE","VRTX","MMC","AMT","ADI","REGN","CI","PYPL",
            "LRCX","SCHW","ZTS","CB","NOW","MO","DUK","SO","AON","CL","BSX","PGR",
            "CME","SLB","EQIX","ITW","WM","NOC","ICE","FDX","SHW","MCK","EMR",
            "PXD","GD","APD","ORLY","KLAC","NSC","AJG","MPC","PSX","VLO","F","GM",
        ]


def process_batch_bursatil(tickers, period="1y", output_path=None, report_every=50):
    """Procesa batch de activos bursátiles."""
    print(f"Procesando {len(tickers)} activos ({period})...")

    results = []
    vectors_geo = []
    errores = []
    tiempos = []
    t_total = time.time()

    for i, ticker in enumerate(tickers):
        t0 = time.time()
        try:
            # Descargar
            df = yf.download(ticker, period=period, interval="1d", progress=False)
            if hasattr(df.columns, 'levels'):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

            if len(df) < 20:
                errores.append({"ticker": ticker, "error": f"solo {len(df)} filas"})
                tiempos.append(time.time() - t0)
                continue

            # Clasificar
            result = procesar_ohlcv(df)
            if not result:
                errores.append({"ticker": ticker, "error": "procesar_ohlcv falló"})
                tiempos.append(time.time() - t0)
                continue

            # 10 marcos × 4 niveles
            v_n1 = calcular_10_ejes(result["seq_n1"], result["n_tipos"]["N1"])
            v_n2 = calcular_10_ejes(result["seq_n2"], result["n_tipos"]["N2"])
            v_n3 = calcular_10_ejes(result["seq_n3"], result["n_tipos"]["N3"])
            v_n4 = calcular_10_ejes(result["seq_n4"], result["n_tipos"]["N4"])

            # Geometría
            vectores = {"N1": v_n1, "N2": v_n2, "N3": v_n3, "N4": v_n4}
            geo = calcular_geometria_completa(vectores)

            dt = time.time() - t0
            tiempos.append(dt)

            dominantes = {}
            for nivel in ["N1", "N2", "N3", "N4"]:
                dom = geo["geometrias"][nivel]["forma"]["dominantes"]
                if dom:
                    dominantes[nivel] = dom

            cambio = result["metadata"]["cambio_total_pct"]

            results.append({
                "ticker": ticker,
                "cambio_pct": cambio,
                "n_sesiones": result["metadata"]["n_sesiones"],
                "profundidad": geo["profundidad_patron"],
                "dominantes": dominantes,
                "simetria_N1": geo["geometrias"]["N1"]["forma"]["simetria"],
                "coherencia_N1": geo["geometrias"]["N1"]["forma"]["coherencia"],
                "simetria_N3": geo["geometrias"]["N3"]["forma"]["simetria"],
                "latencia_ms": round(dt * 1000),
            })
            vectors_geo.append(geo["vector_pgvector"])

        except Exception as e:
            errores.append({"ticker": ticker, "error": str(e)[:100]})
            tiempos.append(time.time() - t0)

        if (i + 1) % report_every == 0:
            elapsed = time.time() - t_total
            avg = np.mean(tiempos[-report_every:]) * 1000
            eta = (len(tickers) - i - 1) * np.mean(tiempos)
            n_ok = len(results)
            print(f"  [{i+1}/{len(tickers)}] ok={n_ok} err={len(errores)} avg={avg:.0f}ms ETA={eta:.0f}s ({eta/60:.1f}min)")

    dt_total = time.time() - t_total

    # Estadísticas
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETADO: {len(results)} activos en {dt_total:.0f}s ({dt_total/60:.1f}min)")
    print(f"{'='*60}")
    print(f"  OK: {len(results)} | Errores: {len(errores)}")
    print(f"  Media: {np.mean(tiempos)*1000:.0f}ms/activo")

    if not vectors_geo:
        print("  ERROR: 0 vectores generados")
        return results, []

    X = np.array(vectors_geo)
    print(f"  Vectores: {X.shape}")

    # Clustering
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score

    scaler = StandardScaler()
    X_norm = scaler.fit_transform(X)
    X_norm = np.nan_to_num(X_norm, 0)

    print(f"\n  CLUSTERING:")
    best_k, best_sil = 3, -1
    for k in range(3, min(12, len(results) // 3)):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X_norm)
        sil = silhouette_score(X_norm, labels)
        print(f"    k={k}: silhouette={sil:.3f}")
        if sil > best_sil:
            best_sil = sil
            best_k = k

    print(f"  Mejor k={best_k} (silhouette={best_sil:.3f})")

    km_best = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = km_best.fit_predict(X_norm)

    # Análisis por cluster
    print(f"\n  CLUSTERS:")
    for c in range(best_k):
        mask = labels == c
        n_c = mask.sum()
        profs = [results[i]["profundidad"] for i in range(len(results)) if mask[i]]
        cambios = [results[i]["cambio_pct"] for i in range(len(results)) if mask[i]]
        tickers_c = [results[i]["ticker"] for i in range(len(results)) if mask[i]]

        all_dom = []
        for i in range(len(results)):
            if mask[i]:
                for nivel, doms in results[i]["dominantes"].items():
                    all_dom.extend(doms)
        dom_freq = Counter(all_dom).most_common(3)
        dom_str = ", ".join(f"{d}({c})" for d, c in dom_freq)

        # Top/bottom performers
        sorted_by_change = sorted(zip(cambios, tickers_c), reverse=True)
        top3 = [f"{t}({ch:+.1f}%)" for ch, t in sorted_by_change[:3]]
        bot3 = [f"{t}({ch:+.1f}%)" for ch, t in sorted_by_change[-3:]]

        print(f"\n    Cluster {c}: n={n_c} ({n_c/len(results)*100:.1f}%)")
        print(f"      Prof media: {np.mean(profs):.3f} ± {np.std(profs):.3f}")
        print(f"      Cambio medio: {np.mean(cambios):+.1f}% ± {np.std(cambios):.1f}%")
        print(f"      Dominantes: [{dom_str}]")
        print(f"      Top 3: {', '.join(top3)}")
        print(f"      Bottom 3: {', '.join(bot3)}")
        print(f"      Muestra: {', '.join(tickers_c[:10])}")

    # Asignar clusters
    for i, r in enumerate(results):
        r["cluster"] = int(labels[i])

    # Guardar
    if output_path:
        save = {
            "version": "poc_bursatil_masivo_v6",
            "fecha": time.strftime("%Y-%m-%d %H:%M"),
            "n_activos": len(results),
            "n_errores": len(errores),
            "tiempo_s": round(dt_total),
            "best_k": best_k,
            "silhouette": round(best_sil, 4),
            "results": results,
            "errores": errores[:20],
        }
        with open(output_path, "w") as f:
            json.dump(save, f, ensure_ascii=False, indent=2)
        print(f"\n  Guardado en {output_path}")

        # Vectores para pgvector
        vpath = output_path.replace(".json", "_vectors.npy")
        np.save(vpath, X)
        print(f"  Vectores: {vpath} ({X.shape})")

    return results, vectors_geo


if __name__ == "__main__":
    max_tickers = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    print("Obteniendo tickers S&P 500...")
    tickers = get_sp500_tickers()[:max_tickers]
    print(f"Tickers: {len(tickers)}")

    # Añadir crypto + índices para comparar
    extras = ["BTC-USD", "ETH-USD", "SOL-USD", "SPY", "QQQ", "IWM", "DIA",
              "GLD", "SLV", "USO", "TLT", "VIX"]
    for e in extras:
        if e not in tickers:
            tickers.append(e)
    print(f"Total con extras: {len(tickers)}")

    output = os.path.join(os.path.dirname(__file__), "../../data/poc_bursatil_masivo.json")
    process_batch_bursatil(tickers, period="1y", output_path=output)
