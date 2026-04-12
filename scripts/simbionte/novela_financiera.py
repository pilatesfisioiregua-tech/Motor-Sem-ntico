"""
Novela Financiera — Cada fórmula = una oración, cada sector = un párrafo, cada trimestre = un capítulo
Fecha: 2026-04-12

Pipeline:
  1. Descargar datos de N sectores × M empresas × T períodos
  2. Calcular K fórmulas financieras por empresa/período
  3. Cada fórmula produce un adjetivo funcional (qué función cumple el resultado)
  4. Secuenciar adjetivos como "texto financiero"
  5. Aplicar 10 marcos × 4 niveles → geometría
  6. Decodificar → LLM

Niveles:
  N1: datos individuales (cada cálculo de fórmula = 1 token funcional)
  N2: empresa (todos los cálculos de 1 empresa en 1 período = 1 oración)
  N3: sector (todas las empresas de 1 sector = 1 párrafo)
  N4: mercado (todos los sectores = el texto completo)

$0 total (yfinance + compute local)
"""

import sys
import os
import time
import json
import numpy as np
import pandas as pd
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))

import yfinance as yf
from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL, MARCOS
from geometria_isomorfismo import calcular_geometria_completa


# ============================================================
# FÓRMULAS FINANCIERAS → FUNCIONES SINTÁCTICAS
# ============================================================

# Cada fórmula produce un resultado que cumple una FUNCIÓN
# El código funcional indica QUÉ TIPO DE ADJETIVO es el resultado

FORMULA_FUNCIONES = {
    # Operación → código funcional
    "varianza":           0,   # Dispersión — "cuán disperso es"
    "media":              1,   # Centro — "dónde está el centro"
    "mediana":            2,   # Centro robusto — "dónde está el centro real"
    "skewness":           3,   # Asimetría — "hacia dónde se inclina"
    "kurtosis":           4,   # Colas — "cuán extremo puede ser"
    "retorno_total":      5,   # Cambio acumulado — "cuánto ganó/perdió"
    "retorno_medio":      6,   # Cambio por período — "cuánto por día"
    "sharpe":             7,   # Retorno/riesgo — "cuánto gana por unidad de riesgo"
    "sortino":            8,   # Retorno/riesgo bajista — "cuánto gana por unidad de caída"
    "max_drawdown":       9,   # Peor caída — "cuánto perdió en el peor momento"
    "beta":               10,  # Sensibilidad al mercado — "cuánto se mueve con el mercado"
    "correlacion_mercado":11,  # Relación con mercado — "cuánto se parece al mercado"
    "volatilidad":        12,  # Riesgo — "cuán impredecible es"
    "volumen_relativo":   13,  # Actividad — "cuánta atención tiene"
    "rango_medio":        14,  # Amplitud — "cuánto se mueve intradía"
    "momentum_20d":       15,  # Fuerza corto plazo — "hacia dónde va ahora"
    "momentum_60d":       16,  # Fuerza medio plazo — "hacia dónde va este trimestre"
    "rsi_proxy":          17,  # Sobrecompra/sobreventa — "está agotado o con fuerza"
}
N_FORMULAS = len(FORMULA_FUNCIONES)

# Clasificación del RESULTADO de cada fórmula en bins funcionales
# Cada resultado se clasifica en 5 niveles (muy bajo, bajo, normal, alto, muy alto)
# Esto produce el código funcional final: fórmula × nivel = "token"
N_NIVELES = 5
N_TOKENS_FORMULA = N_FORMULAS * N_NIVELES  # 18 × 5 = 90 tipos posibles


def calcular_formulas(df, df_mercado=None):
    """Calcula todas las fórmulas financieras sobre un DataFrame OHLCV.

    Args:
        df: DataFrame OHLCV de un activo
        df_mercado: DataFrame OHLCV del mercado (SPY) para beta/correlación

    Returns:
        dict {nombre_formula: valor}
    """
    if len(df) < 20:
        return None

    close = df["Close"].values.astype(float)
    volume = df["Volume"].values.astype(float)
    high = df["High"].values.astype(float)
    low = df["Low"].values.astype(float)

    # Retornos diarios
    returns = np.diff(close) / close[:-1]
    returns = returns[np.isfinite(returns)]

    if len(returns) < 10:
        return None

    results = {}

    # Estadística de retornos
    results["varianza"] = float(np.var(returns))
    results["media"] = float(np.mean(returns))
    results["mediana"] = float(np.median(returns))
    from scipy.stats import skew, kurtosis
    results["skewness"] = float(skew(returns)) if len(returns) > 3 else 0.0
    results["kurtosis"] = float(kurtosis(returns)) if len(returns) > 4 else 0.0

    # Retornos
    results["retorno_total"] = float((close[-1] / close[0]) - 1)
    results["retorno_medio"] = float(np.mean(returns))

    # Sharpe (asumiendo rf=0 para simplificar)
    std = np.std(returns)
    results["sharpe"] = float(np.mean(returns) / std) if std > 1e-10 else 0.0

    # Sortino (solo downside deviation)
    neg_returns = returns[returns < 0]
    downside_std = np.std(neg_returns) if len(neg_returns) > 1 else 1e-10
    results["sortino"] = float(np.mean(returns) / downside_std) if downside_std > 1e-10 else 0.0

    # Max Drawdown
    cummax = np.maximum.accumulate(close)
    drawdowns = (close - cummax) / cummax
    results["max_drawdown"] = float(np.min(drawdowns))

    # Beta y correlación con mercado
    if df_mercado is not None and len(df_mercado) >= len(df):
        mkt_close = df_mercado["Close"].values[-len(close):].astype(float)
        mkt_returns = np.diff(mkt_close) / mkt_close[:-1]
        mkt_returns = mkt_returns[:len(returns)]
        if len(mkt_returns) == len(returns) and np.std(mkt_returns) > 1e-10:
            results["beta"] = float(np.cov(returns, mkt_returns)[0, 1] / np.var(mkt_returns))
            results["correlacion_mercado"] = float(np.corrcoef(returns, mkt_returns)[0, 1])
        else:
            results["beta"] = 1.0
            results["correlacion_mercado"] = 0.0
    else:
        results["beta"] = 1.0
        results["correlacion_mercado"] = 0.0

    # Volatilidad (anualizada)
    results["volatilidad"] = float(std * np.sqrt(252))

    # Volumen relativo (vs media)
    vol_mean = np.mean(volume)
    results["volumen_relativo"] = float(volume[-1] / vol_mean) if vol_mean > 0 else 1.0

    # Rango medio (ATR proxy)
    ranges = high - low
    results["rango_medio"] = float(np.mean(ranges) / np.mean(close)) if np.mean(close) > 0 else 0.0

    # Momentum
    if len(close) >= 20:
        results["momentum_20d"] = float(close[-1] / close[-20] - 1)
    else:
        results["momentum_20d"] = 0.0

    if len(close) >= 60:
        results["momentum_60d"] = float(close[-1] / close[-60] - 1)
    else:
        results["momentum_60d"] = results["retorno_total"]

    # RSI proxy (% de días alcistas en últimos 14)
    if len(returns) >= 14:
        recent = returns[-14:]
        results["rsi_proxy"] = float(np.sum(recent > 0) / 14)
    else:
        results["rsi_proxy"] = 0.5

    return results


def formulas_a_secuencia(resultados_formulas, percentiles_ref=None):
    """Convierte resultados de fórmulas en secuencia de códigos funcionales.

    Cada resultado se clasifica en 5 niveles (quintiles) relativo a la referencia.
    El código final = formula_idx × 5 + nivel (0-89)

    Args:
        resultados_formulas: dict {nombre: valor}
        percentiles_ref: dict {nombre: [p20, p40, p60, p80]} — si None, usa defaults

    Returns:
        list[int] — secuencia de códigos funcionales
    """
    if percentiles_ref is None:
        # Defaults razonables para mercado US
        percentiles_ref = {
            "varianza":       [0.0001, 0.0003, 0.0006, 0.001],
            "media":          [-0.001, 0.0, 0.0005, 0.001],
            "mediana":        [-0.001, 0.0, 0.0005, 0.001],
            "skewness":       [-0.5, -0.1, 0.1, 0.5],
            "kurtosis":       [0.5, 1.5, 3.0, 6.0],
            "retorno_total":  [-0.10, 0.0, 0.10, 0.30],
            "retorno_medio":  [-0.001, 0.0, 0.0005, 0.001],
            "sharpe":         [-0.05, 0.0, 0.05, 0.10],
            "sortino":        [-0.05, 0.0, 0.05, 0.10],
            "max_drawdown":   [-0.30, -0.20, -0.10, -0.05],
            "beta":           [0.5, 0.8, 1.0, 1.3],
            "correlacion_mercado": [0.2, 0.4, 0.6, 0.8],
            "volatilidad":    [0.10, 0.20, 0.30, 0.50],
            "volumen_relativo": [0.5, 0.8, 1.0, 1.5],
            "rango_medio":    [0.01, 0.02, 0.03, 0.05],
            "momentum_20d":   [-0.05, 0.0, 0.03, 0.08],
            "momentum_60d":   [-0.10, 0.0, 0.05, 0.15],
            "rsi_proxy":      [0.3, 0.4, 0.5, 0.6],
        }

    seq = []
    for formula_name, formula_idx in FORMULA_FUNCIONES.items():
        valor = resultados_formulas.get(formula_name, 0.0)
        thresholds = percentiles_ref.get(formula_name, [0, 0, 0, 0])

        # Clasificar en quintil
        if valor <= thresholds[0]:
            nivel = 0  # muy bajo
        elif valor <= thresholds[1]:
            nivel = 1  # bajo
        elif valor <= thresholds[2]:
            nivel = 2  # normal
        elif valor <= thresholds[3]:
            nivel = 3  # alto
        else:
            nivel = 4  # muy alto

        codigo = formula_idx * N_NIVELES + nivel
        seq.append(codigo)

    return seq


# ============================================================
# SECTORES S&P 500
# ============================================================

SECTORES = {
    "tech":       ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "ADBE", "CRM", "CSCO", "INTC", "AMD", "QCOM", "TXN", "NOW", "INTU"],
    "finanzas":   ["JPM", "V", "MA", "BLK", "GS", "MS", "BAC", "WFC", "SCHW", "AXP", "C", "USB", "PNC", "CME", "ICE"],
    "salud":      ["UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD", "ISRG", "VRTX", "SYK"],
    "consumo":    ["PG", "KO", "PEP", "WMT", "COST", "MCD", "HD", "LOW", "TGT", "CL", "MDLZ", "EL", "GIS", "KHC", "MO"],
    "energia":    ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "OXY", "HES", "DVN", "FANG", "HAL", "BKR"],
    "industrial": ["CAT", "GE", "HON", "UNP", "RTX", "BA", "DE", "LMT", "NOC", "GD", "MMM", "EMR", "ITW", "FDX", "NSC"],
}

EXTRAS = {
    "crypto":     ["BTC-USD", "ETH-USD", "SOL-USD"],
    "indices":    ["SPY", "QQQ", "IWM", "DIA"],
    "commodities":["GLD", "SLV", "USO"],
}


def construir_novela(period="1y"):
    """Construye la novela financiera completa."""
    print(f"{'='*60}")
    print(f"NOVELA FINANCIERA — {period}")
    print(f"{'='*60}")

    todos_tickers = {}
    for sector, tickers in {**SECTORES, **EXTRAS}.items():
        for t in tickers:
            todos_tickers[t] = sector

    # Descargar mercado (SPY) primero
    print(f"\nDescargando SPY como referencia de mercado...")
    spy = yf.download("SPY", period=period, interval="1d", progress=False)
    if hasattr(spy.columns, 'levels'):
        spy.columns = [c[0] if isinstance(c, tuple) else c for c in spy.columns]

    # Descargar todos los activos
    all_tickers = list(todos_tickers.keys())
    print(f"Descargando {len(all_tickers)} activos...")
    t0 = time.time()

    datos = {}
    errores = []
    for i, ticker in enumerate(all_tickers):
        try:
            df = yf.download(ticker, period=period, interval="1d", progress=False)
            if hasattr(df.columns, 'levels'):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            if len(df) >= 20:
                datos[ticker] = df
        except Exception as e:
            errores.append(ticker)

        if (i + 1) % 30 == 0:
            print(f"  [{i+1}/{len(all_tickers)}] descargados={len(datos)} errores={len(errores)}")

    print(f"  Descarga: {len(datos)} activos en {time.time()-t0:.0f}s")

    # Calcular fórmulas por activo
    print(f"\nCalculando fórmulas financieras...")
    formulas_por_activo = {}
    for ticker, df in datos.items():
        resultado = calcular_formulas(df, spy)
        if resultado:
            formulas_por_activo[ticker] = resultado

    print(f"  Fórmulas calculadas: {len(formulas_por_activo)} activos × {N_FORMULAS} fórmulas")

    # Calcular percentiles reales del mercado (para clasificación relativa)
    print(f"\nCalculando percentiles de referencia...")
    all_vals = defaultdict(list)
    for ticker, formulas in formulas_por_activo.items():
        for name, val in formulas.items():
            if np.isfinite(val):
                all_vals[name].append(val)

    percentiles_ref = {}
    for name, vals in all_vals.items():
        if vals:
            percentiles_ref[name] = [
                float(np.percentile(vals, 20)),
                float(np.percentile(vals, 40)),
                float(np.percentile(vals, 60)),
                float(np.percentile(vals, 80)),
            ]

    # Convertir a secuencias funcionales
    print(f"\nConvirtiendo a secuencias funcionales...")
    secuencias = {}
    for ticker, formulas in formulas_por_activo.items():
        seq = formulas_a_secuencia(formulas, percentiles_ref)
        secuencias[ticker] = seq

    # === CONSTRUIR LA NOVELA (4 NIVELES) ===
    print(f"\n{'='*60}")
    print(f"CONSTRUYENDO NOVELA (4 niveles)")
    print(f"{'='*60}")

    # N1: Todos los tokens de todas las empresas (secuencia plana)
    seq_n1 = []
    for ticker in sorted(secuencias.keys()):
        seq_n1.extend(secuencias[ticker])
    print(f"  N1 (tokens): {len(seq_n1)} datos funcionales")

    # N2: Cada empresa = 1 tipo de oración (clasificada por su perfil)
    def clasificar_empresa(formulas):
        """Clasifica empresa en tipo basado en su perfil de fórmulas."""
        ret = formulas.get("retorno_total", 0)
        vol = formulas.get("volatilidad", 0)
        beta = formulas.get("beta", 1)
        sharpe = formulas.get("sharpe", 0)

        if ret > 0.20 and vol < 0.25:
            return 0  # "estrella" — alto retorno, baja volatilidad
        elif ret > 0.20 and vol >= 0.25:
            return 1  # "cohete" — alto retorno, alta volatilidad
        elif ret > 0 and ret <= 0.20:
            return 2  # "estable" — retorno moderado
        elif ret <= 0 and vol < 0.30:
            return 3  # "defensivo" — pierde pero poco volátil
        elif ret <= 0 and vol >= 0.30:
            return 4  # "caída" — pierde y muy volátil
        elif beta > 1.3:
            return 5  # "agresivo" — muy sensible al mercado
        elif beta < 0.7:
            return 6  # "independiente" — poco correlacionado
        else:
            return 7  # "neutro"

    N_TIPO_EMPRESA = 8
    seq_n2 = []
    empresa_tipos = {}
    for ticker in sorted(secuencias.keys()):
        tipo = clasificar_empresa(formulas_por_activo[ticker])
        seq_n2.append(tipo)
        empresa_tipos[ticker] = tipo
    print(f"  N2 (empresas): {len(seq_n2)} empresas → tipos: {dict(Counter(seq_n2))}")

    # N3: Cada sector = 1 tipo de párrafo
    def clasificar_sector(sector_tickers, empresa_tipos):
        tipos = [empresa_tipos.get(t, 7) for t in sector_tickers if t in empresa_tipos]
        if not tipos:
            return 4
        moda = Counter(tipos).most_common(1)[0][0]
        if moda in (0, 2):
            return 0  # sector estable
        elif moda in (1, 5):
            return 1  # sector agresivo
        elif moda in (3, 6):
            return 2  # sector defensivo
        elif moda == 4:
            return 3  # sector en caída
        else:
            return 4  # sector mixto

    N_TIPO_SECTOR = 5
    seq_n3 = []
    for sector, tickers in {**SECTORES, **EXTRAS}.items():
        tipo = clasificar_sector(tickers, empresa_tipos)
        seq_n3.append(tipo)
    print(f"  N3 (sectores): {len(seq_n3)} sectores → tipos: {dict(Counter(seq_n3))}")

    # N4: El mercado como secuencia de movimientos
    # Dividir en 4 sub-períodos y clasificar cada uno
    spy_close = spy["Close"].values.astype(float)
    cuarto = max(len(spy_close) // 4, 1)
    seq_n4 = []
    for i in range(4):
        chunk = spy_close[i*cuarto:(i+1)*cuarto]
        if len(chunk) < 2:
            seq_n4.append(2)
            continue
        cambio = (chunk[-1] / chunk[0]) - 1
        vol = np.std(np.diff(chunk) / chunk[:-1]) if len(chunk) > 2 else 0
        if cambio > 0.05 and vol < 0.015:
            seq_n4.append(0)  # rally tranquilo
        elif cambio > 0.05 and vol >= 0.015:
            seq_n4.append(1)  # rally volátil
        elif cambio < -0.05:
            seq_n4.append(3)  # corrección
        else:
            seq_n4.append(2)  # lateral
    N_TIPO_MERCADO = 4
    print(f"  N4 (mercado): {seq_n4}")

    # === 10 MARCOS × 4 NIVELES ===
    print(f"\nCalculando 10 marcos × 4 niveles...")
    t0 = time.time()
    v_n1 = calcular_10_ejes(seq_n1, N_TOKENS_FORMULA)
    v_n2 = calcular_10_ejes(seq_n2, N_TIPO_EMPRESA)
    v_n3 = calcular_10_ejes(seq_n3, N_TIPO_SECTOR)
    v_n4 = calcular_10_ejes(seq_n4, N_TIPO_MERCADO)
    dt = time.time() - t0
    print(f"  Vector: {FEATURES_POR_NIVEL * 4}D en {dt*1000:.0f}ms")

    # === GEOMETRÍA ===
    vectores = {"N1": v_n1, "N2": v_n2, "N3": v_n3, "N4": v_n4}
    geo = calcular_geometria_completa(vectores)
    print(f"  Geometría: {geo['n_features']}D")
    print(f"  Profundidad: {geo['profundidad_patron']}")

    # Resultados por nivel
    print(f"\n{'='*60}")
    print(f"LECTURA DE LA NOVELA FINANCIERA")
    print(f"{'='*60}")

    for nivel in ["N1", "N2", "N3", "N4"]:
        g = geo["geometrias"][nivel]
        dom = g["forma"]["dominantes"]
        sym = g["forma"]["simetria"]
        coh = g["forma"]["coherencia"]
        print(f"\n  {nivel}:")
        if dom:
            print(f"    Dominantes: {dom}")
        print(f"    Simetría: {sym:.3f} | Coherencia: {coh:.3f}")

    for pair, s in geo["similaridades"].items():
        print(f"  {pair}: homomorfismo={s['homomorfismo']:.3f}")

    # Resumen por sector
    print(f"\n  POR SECTOR:")
    for sector, tickers in {**SECTORES, **EXTRAS}.items():
        sector_formulas = {t: formulas_por_activo[t] for t in tickers if t in formulas_por_activo}
        if not sector_formulas:
            continue
        ret_medio = np.mean([f["retorno_total"] for f in sector_formulas.values()])
        vol_medio = np.mean([f["volatilidad"] for f in sector_formulas.values()])
        sharpe_medio = np.mean([f["sharpe"] for f in sector_formulas.values()])
        var_medio = np.mean([f["varianza"] for f in sector_formulas.values()])
        print(f"    {sector:<12s}: ret={ret_medio:+.1%} vol={vol_medio:.1%} sharpe={sharpe_medio:.3f} var={var_medio:.5f} n={len(sector_formulas)}")

    # Guardar
    save = {
        "version": "novela_financiera_v1",
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "period": period,
        "n_activos": len(formulas_por_activo),
        "n_formulas": N_FORMULAS,
        "profundidad": geo["profundidad_patron"],
        "dominantes": {
            nivel: geo["geometrias"][nivel]["forma"]["dominantes"]
            for nivel in ["N1", "N2", "N3", "N4"]
        },
        "sectores": {
            sector: {
                "n": len([t for t in tickers if t in formulas_por_activo]),
                "ret_medio": float(np.mean([formulas_por_activo[t]["retorno_total"] for t in tickers if t in formulas_por_activo])) if any(t in formulas_por_activo for t in tickers) else 0,
                "vol_medio": float(np.mean([formulas_por_activo[t]["volatilidad"] for t in tickers if t in formulas_por_activo])) if any(t in formulas_por_activo for t in tickers) else 0,
            }
            for sector, tickers in {**SECTORES, **EXTRAS}.items()
        },
        "seq_n4": seq_n4,
        "percentiles_ref": percentiles_ref,
    }

    path = os.path.join(os.path.dirname(__file__), "../../data/novela_financiera.json")
    with open(path, "w") as f:
        json.dump(save, f, ensure_ascii=False, indent=2)
    print(f"\n  Guardado en {path}")

    # Vector para pgvector
    vector_total = np.concatenate([v_n1, v_n2, v_n3, v_n4, geo["vector_pgvector"]])
    vpath = path.replace(".json", "_vector.npy")
    np.save(vpath, vector_total)
    print(f"  Vector: {vpath} ({len(vector_total)}D)")

    return save, geo


if __name__ == "__main__":
    novela, geo = construir_novela(period="1y")
