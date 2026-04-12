"""
Clasificador Funcional Bursátil — Base Tipo 5
Fecha: 2026-04-12

Convierte datos OHLCV en secuencias de códigos funcionales.
Misma lógica que clasificador_funcional.py para texto.
Cada vela/sesión/período recibe un código que representa su FUNCIÓN en contexto.

Ref: BASE_TIPO_5_BURSATIL.md
"""

import numpy as np
import pandas as pd
from collections import Counter


# ============================================================
# FUNCIONES DE VELA (N1) — 12 tipos
# ============================================================

VELA_TIPOS = {
    "impulso_alcista":    0,   # Cuerpo grande alcista (>70% del rango)
    "impulso_bajista":    1,   # Cuerpo grande bajista
    "doji":               2,   # Cuerpo < 10% rango — indecisión
    "martillo":           3,   # Sombra inferior larga, cuerpo arriba
    "estrella_fugaz":     4,   # Sombra superior larga, cuerpo abajo
    "envolvente_alcista": 5,   # Cierra por encima del máximo anterior
    "envolvente_bajista": 6,   # Cierra por debajo del mínimo anterior
    "inside":             7,   # Rango dentro del rango anterior
    "outside":            8,   # Rango fuera del rango anterior
    "gap_up":             9,   # Apertura > cierre anterior
    "gap_down":           10,  # Apertura < cierre anterior
    "volumen_anomalo":    11,  # Volumen > 2x media
}
N_VELA_TIPOS = 12
VELA_NAMES = list(VELA_TIPOS.keys())


def clasificar_vela(row, prev_row=None, vol_media=None):
    """Clasifica una vela OHLCV por su función en contexto."""
    o, h, l, c, v = row["Open"], row["High"], row["Low"], row["Close"], row["Volume"]
    body = abs(c - o)
    rango = h - l
    if rango < 1e-10:
        rango = 1e-10

    ratio_body = body / rango
    is_bull = c > o

    # Gap
    if prev_row is not None:
        prev_c = prev_row["Close"]
        if o > prev_c * 1.005:
            return "gap_up"
        if o < prev_c * 0.995:
            return "gap_down"

    # Volumen anómalo
    if vol_media and vol_media > 0 and v > vol_media * 2:
        return "volumen_anomalo"

    # Inside/Outside
    if prev_row is not None:
        prev_h, prev_l = prev_row["High"], prev_row["Low"]
        if h < prev_h and l > prev_l:
            return "inside"
        if h > prev_h and l < prev_l:
            return "outside"

    # Envolvente
    if prev_row is not None:
        if is_bull and c > prev_row["High"] and o < prev_row["Low"]:
            return "envolvente_alcista"
        if not is_bull and c < prev_row["Low"] and o > prev_row["High"]:
            return "envolvente_bajista"

    # Doji
    if ratio_body < 0.1:
        return "doji"

    # Martillo (sombra inferior > 2x cuerpo, cuerpo en tercio superior)
    sombra_inf = min(o, c) - l
    sombra_sup = h - max(o, c)
    if sombra_inf > body * 2 and sombra_sup < body * 0.5:
        return "martillo"

    # Estrella fugaz (sombra superior > 2x cuerpo, cuerpo en tercio inferior)
    if sombra_sup > body * 2 and sombra_inf < body * 0.5:
        return "estrella_fugaz"

    # Impulso
    if ratio_body > 0.7:
        return "impulso_alcista" if is_bull else "impulso_bajista"

    # Default: impulso débil
    return "impulso_alcista" if is_bull else "impulso_bajista"


# ============================================================
# FUNCIONES DE SESIÓN (N2) — 10 tipos
# ============================================================

SESION_TIPOS = {
    "tendencial_alcista":  0,
    "tendencial_bajista":  1,
    "rango":               2,
    "expansion":           3,
    "compresion":          4,
    "reversal_alcista":    5,
    "reversal_bajista":    6,
    "gap_up_session":      7,
    "gap_down_session":    8,
    "alta_volatilidad":    9,
}
N_SESION_TIPOS = 10
SESION_NAMES = list(SESION_TIPOS.keys())


def clasificar_sesion(sesion_df, atr=None):
    """Clasifica una sesión (día) por sus velas."""
    if len(sesion_df) < 2:
        return "rango"

    o_first = sesion_df.iloc[0]["Open"]
    c_last = sesion_df.iloc[-1]["Close"]
    h_max = sesion_df["High"].max()
    l_min = sesion_df["Low"].min()
    rango = h_max - l_min
    cambio = c_last - o_first
    vol_total = sesion_df["Volume"].sum()

    if atr and rango > atr * 2:
        return "expansion"
    if atr and rango < atr * 0.5:
        return "compresion"

    # Reversal: abrió en un extremo, cerró en el opuesto
    mid = (h_max + l_min) / 2
    if o_first > mid and c_last < mid:
        return "reversal_bajista"
    if o_first < mid and c_last > mid:
        return "reversal_alcista"

    if rango > 0 and abs(cambio) / rango > 0.5:
        return "tendencial_alcista" if cambio > 0 else "tendencial_bajista"

    return "rango"


# ============================================================
# FUNCIONES DE PERÍODO (N3) — 5 tipos
# ============================================================

PERIODO_TIPOS = {
    "acumulacion":    0,
    "distribucion":   1,
    "impulso":        2,
    "correccion":     3,
    "consolidacion":  4,
}
N_PERIODO_TIPOS = 5
PERIODO_NAMES = list(PERIODO_TIPOS.keys())


def clasificar_periodo(closes, volumes, n_sesiones=5):
    """Clasifica un período de N sesiones."""
    if len(closes) < 3:
        return "consolidacion"

    cambio_total = (closes[-1] - closes[0]) / max(closes[0], 1e-10)
    vol_trend = np.polyfit(range(len(volumes)), volumes, 1)[0] if len(volumes) >= 3 else 0
    volatilidad = np.std(np.diff(closes) / closes[:-1]) if len(closes) >= 3 else 0

    # Impulso: cambio grande + dirección clara
    if abs(cambio_total) > 0.05 and volatilidad < 0.03:
        return "impulso"

    # Corrección: cambio moderado contra tendencia previa
    if abs(cambio_total) > 0.02 and volatilidad > 0.02:
        return "correccion"

    # Acumulación: rango lateral + volumen creciente
    if abs(cambio_total) < 0.02 and vol_trend > 0:
        return "acumulacion"

    # Distribución: rango lateral + volumen decreciente
    if abs(cambio_total) < 0.02 and vol_trend < 0:
        return "distribucion"

    return "consolidacion"


# ============================================================
# FUNCIONES DE CICLO (N4) — 4 tipos
# ============================================================

CICLO_TIPOS = {
    "alcista":     0,
    "bajista":     1,
    "lateral":     2,
    "transicion":  3,
}
N_CICLO_TIPOS = 4
CICLO_NAMES = list(CICLO_TIPOS.keys())


def clasificar_ciclo(sesiones_tipos):
    """Clasifica el ciclo basándose en la secuencia de sesiones."""
    if len(sesiones_tipos) < 3:
        return "lateral"

    alcistas = sum(1 for s in sesiones_tipos if s in (0, 5, 7))  # tendencial_alc, reversal_alc, gap_up
    bajistas = sum(1 for s in sesiones_tipos if s in (1, 6, 8))  # tendencial_baj, reversal_baj, gap_down
    total = len(sesiones_tipos)

    if alcistas / total > 0.6:
        return "alcista"
    if bajistas / total > 0.6:
        return "bajista"
    if abs(alcistas - bajistas) / total < 0.15:
        return "lateral"
    return "transicion"


# ============================================================
# PIPELINE COMPLETO: OHLCV → Secuencias funcionales 4 niveles
# ============================================================

def procesar_ohlcv(df, periodo_size=5):
    """Convierte DataFrame OHLCV en secuencias funcionales de 4 niveles.

    Args:
        df: DataFrame con columnas Open, High, Low, Close, Volume (index=datetime)
        periodo_size: N sesiones por período (default 5 = 1 semana)

    Returns:
        dict con seq_n1, seq_n2, seq_n3, seq_n4 + metadata
    """
    df = df.copy().dropna()
    if len(df) < 5:
        return None

    # === N1: Velas ===
    vol_media = df["Volume"].mean()
    seq_n1 = []
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1] if i > 0 else None
        tipo = clasificar_vela(row, prev, vol_media)
        seq_n1.append(VELA_TIPOS[tipo])

    # === N2: Sesiones ===
    # Para datos diarios, cada fila = 1 sesión
    # Para intradía, agrupar por día
    if hasattr(df.index, 'date'):
        dates = df.index.date
        unique_dates = sorted(set(dates))

        if len(unique_dates) > 1 and len(df) / len(unique_dates) > 2:
            # Intradía: agrupar por día
            atr_vals = []
            seq_n2 = []
            for d in unique_dates:
                mask = dates == d
                sesion = df[mask]
                atr = sesion["High"].max() - sesion["Low"].min()
                atr_vals.append(atr)
                atr_media = np.mean(atr_vals[-20:]) if atr_vals else atr
                tipo = clasificar_sesion(sesion, atr_media)
                seq_n2.append(SESION_TIPOS[tipo])
        else:
            # Diario: cada fila = 1 sesión, calcular ATR rolling
            atr = (df["High"] - df["Low"]).rolling(14).mean()
            seq_n2 = []
            for i in range(len(df)):
                row_df = df.iloc[i:i + 1]
                a = atr.iloc[i] if not pd.isna(atr.iloc[i]) else (df["High"].iloc[i] - df["Low"].iloc[i])
                tipo = clasificar_sesion(row_df, a)
                seq_n2.append(SESION_TIPOS[tipo])
    else:
        seq_n2 = [SESION_TIPOS["rango"]] * len(df)

    # === N3: Períodos ===
    seq_n3 = []
    for i in range(0, len(df) - periodo_size + 1, periodo_size):
        chunk = df.iloc[i:i + periodo_size]
        tipo = clasificar_periodo(
            chunk["Close"].values,
            chunk["Volume"].values,
            periodo_size
        )
        seq_n3.append(PERIODO_TIPOS[tipo])

    if not seq_n3:
        seq_n3 = [PERIODO_TIPOS["consolidacion"]]

    # === N4: Ciclo ===
    tipo_ciclo = clasificar_ciclo(seq_n2)
    # Crear secuencia dividiendo en tercios
    n = max(len(seq_n2), 1)
    tercio = max(n // 3, 1)
    seq_n4 = [
        CICLO_TIPOS[clasificar_ciclo(seq_n2[:tercio])],
        CICLO_TIPOS[clasificar_ciclo(seq_n2[tercio:2 * tercio])],
        CICLO_TIPOS[clasificar_ciclo(seq_n2[2 * tercio:])],
    ]

    return {
        "seq_n1": seq_n1,
        "seq_n2": seq_n2,
        "seq_n3": seq_n3,
        "seq_n4": seq_n4,
        "n_tipos": {
            "N1": N_VELA_TIPOS,
            "N2": N_SESION_TIPOS,
            "N3": N_PERIODO_TIPOS,
            "N4": N_CICLO_TIPOS,
        },
        "metadata": {
            "n_velas": len(seq_n1),
            "n_sesiones": len(seq_n2),
            "n_periodos": len(seq_n3),
            "periodo_size": periodo_size,
            "cambio_total_pct": round((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100, 2),
            "vol_media": round(float(vol_media)),
        },
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import yfinance as yf

    print("Descargando datos bursátiles...")

    # Apple 1 año diario
    aapl = yf.download("AAPL", period="1y", interval="1d", progress=False)
    print(f"\nAAPL: {len(aapl)} sesiones, {aapl.index[0].date()} → {aapl.index[-1].date()}")

    result = procesar_ohlcv(aapl)
    if result:
        print(f"  N1 (velas): {len(result['seq_n1'])} → tipos: {dict(Counter(result['seq_n1']))}")
        print(f"  N2 (sesiones): {len(result['seq_n2'])} → tipos: {dict(Counter(result['seq_n2']))}")
        print(f"  N3 (períodos): {len(result['seq_n3'])} → tipos: {dict(Counter(result['seq_n3']))}")
        print(f"  N4 (ciclo): {result['seq_n4']}")
        print(f"  Cambio total: {result['metadata']['cambio_total_pct']}%")

    # SPY 1 año
    spy = yf.download("SPY", period="1y", interval="1d", progress=False)
    print(f"\nSPY: {len(spy)} sesiones")

    result_spy = procesar_ohlcv(spy)
    if result_spy:
        print(f"  N1 (velas): {len(result_spy['seq_n1'])} → tipos: {dict(Counter(result_spy['seq_n1']))}")
        print(f"  N2 (sesiones): {len(result_spy['seq_n2'])} → tipos: {dict(Counter(result_spy['seq_n2']))}")
        print(f"  N3 (períodos): {len(result_spy['seq_n3'])} → tipos: {dict(Counter(result_spy['seq_n3']))}")
        print(f"  N4 (ciclo): {result_spy['seq_n4']}")
        print(f"  Cambio total: {result_spy['metadata']['cambio_total_pct']}%")

    # BTC crypto
    btc = yf.download("BTC-USD", period="1y", interval="1d", progress=False)
    print(f"\nBTC: {len(btc)} sesiones")

    result_btc = procesar_ohlcv(btc)
    if result_btc:
        print(f"  N1 (velas): {len(result_btc['seq_n1'])} → tipos: {dict(Counter(result_btc['seq_n1']))}")
        print(f"  Cambio total: {result_btc['metadata']['cambio_total_pct']}%")
