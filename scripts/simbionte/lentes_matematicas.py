"""
Lentes Matematicas — Cada marco es un clasificador que lee datos crudos.

Fecha: 2026-04-12

Principio:
  El clasificador generico (24 formulas → 1 secuencia) es una aproximacion.
  La realidad es que cada marco matematico VE cosas diferentes en los mismos datos.

  Un estadistico mira la distribucion.
  Un teorico de grafos mira las conexiones.
  Un cibernetico mira los loops de feedback.

  NO ven lo mismo. Ven REALIDADES DIFERENTES del mismo dato.

  Cada lente produce su propia secuencia funcional.
  10 lentes × datos = 10 "textos" simultaneos.
  Es como si el mismo libro estuviera escrito en 10 idiomas a la vez.

Pipeline:
  1. Datos crudos (series temporales de metricas)
  2. Cada lente lee los datos y produce una secuencia de codigos funcionales
  3. Cada secuencia se procesa con calcular_10_ejes() → vector
  4. 10 vectores → geometria entre lentes → meta-patron

$0 total (compute local)
"""

import numpy as np
from collections import Counter
from scipy import stats as scipy_stats


# ============================================================
# TIPOS FUNCIONALES POR LENTE (lo que cada lente "ve")
# ============================================================

# Cada lente tiene sus propios tipos funcionales.
# Son los "adjetivos" que esa lente usa para describir lo que ve.

LENTE_ESTADISTICA = {
    "entropia_baja":        0,   # Distribucion concentrada, predecible
    "entropia_media":       1,   # Distribucion moderada
    "entropia_alta":        2,   # Distribucion dispersa, impredecible
    "skew_negativo":        3,   # Cola izquierda (riesgo de caida)
    "skew_neutro":          4,   # Simetrico
    "skew_positivo":        5,   # Cola derecha (potencial de upside)
    "kurtosis_baja":        6,   # Colas ligeras, sin extremos
    "kurtosis_alta":        7,   # Colas pesadas, extremos probables
    "concentracion":        8,   # Pocos valores dominan (Gini alto)
    "dispersion":           9,   # Valores distribuidos (Gini bajo)
    "estacionario":         10,  # Sin tendencia, media estable
    "no_estacionario":      11,  # Con tendencia, media cambiante
}
N_TIPOS_ESTADISTICA = 12

LENTE_CONJUNTOS = {
    "jaccard_alto":         0,   # Periodos similares (consistencia)
    "jaccard_medio":        1,   # Similitud moderada
    "jaccard_bajo":         2,   # Periodos diferentes (cambio)
    "cobertura_total":      3,   # Todas las metricas activas
    "cobertura_parcial":    4,   # Algunas metricas inactivas
    "gap":                  5,   # Metricas faltantes (agujero)
    "simetria":             6,   # Primera y segunda mitad iguales
    "asimetria":            7,   # Primera y segunda mitad diferentes
    "inclusion":            8,   # Un periodo contiene al otro (subset)
    "disjuncion":           9,   # Periodos completamente diferentes
}
N_TIPOS_CONJUNTOS = 10

LENTE_GRAFOS = {
    "hub":                  0,   # Metrica central (alta centralidad)
    "periferia":            1,   # Metrica aislada (baja centralidad)
    "cluster_denso":        2,   # Grupo de metricas correlacionadas
    "cluster_disperso":     3,   # Metricas poco correlacionadas
    "puente":               4,   # Metrica que conecta clusters
    "isla":                 5,   # Metrica sin correlacion con ninguna
    "estrella":             6,   # Una metrica conectada a todas
    "cadena":               7,   # Correlaciones en secuencia (A→B→C)
    "ciclo":                8,   # Correlacion circular (A→B→C→A)
    "desconexion":          9,   # Grafo fragmentado
}
N_TIPOS_GRAFOS = 10

LENTE_MARKOV = {
    "transicion_fuerte":    0,   # Alta probabilidad de cambiar de estado
    "transicion_debil":     1,   # Baja probabilidad de cambiar
    "estado_absorbente":    2,   # Estado del que no se sale (churn terminal)
    "estado_transitorio":   3,   # Estado temporal
    "diagonal_alta":        4,   # Tendencia a permanecer (estabilidad)
    "diagonal_baja":        5,   # Tendencia a cambiar (volatilidad)
    "ergodicidad":          6,   # Todo estado es alcanzable
    "no_ergodicidad":       7,   # Hay estados inalcanzables
    "periodicidad":         8,   # Patron ciclico en transiciones
    "aperiodico":           9,   # Sin patron ciclico
}
N_TIPOS_MARKOV = 10

LENTE_JUEGOS = {
    "cooperacion":          0,   # Metricas se refuerzan mutuamente
    "competencia":          1,   # Metricas en tension (una sube, otra baja)
    "dilema":               2,   # Optimizar una empeora otra
    "suma_cero":            3,   # Ganancia de una = perdida de otra
    "suma_positiva":        4,   # Ambas pueden mejorar
    "suma_negativa":        5,   # Ambas empeoran
    "nash":                 6,   # Equilibrio estable
    "inestable":            7,   # Sin equilibrio (oscilacion)
    "dominancia":           8,   # Una metrica domina la otra
    "simetria_juego":       9,   # Metricas en balance
}
N_TIPOS_JUEGOS = 10

LENTE_CIBERNETICA = {
    "feedback_positivo":    0,   # Amplificacion (crecimiento exponencial o colapso)
    "feedback_negativo":    1,   # Regulacion (vuelta al equilibrio)
    "sin_feedback":         2,   # Metricas independientes
    "delay_corto":          3,   # Efecto inmediato (< 1 periodo)
    "delay_largo":          4,   # Efecto retardado (> 3 periodos)
    "amplificacion":        5,   # Señal se amplifica con el tiempo
    "amortiguacion":        6,   # Señal se atenua con el tiempo
    "oscilacion":           7,   # Señal oscila alrededor del equilibrio
    "saturacion":           8,   # Señal llega a techo
    "runaway":              9,   # Señal sin control (divergencia)
}
N_TIPOS_CIBERNETICA = 10

LENTE_SISTEMAS = {
    "acoplamiento_fuerte":  0,   # Subsistemas muy interdependientes
    "acoplamiento_debil":   1,   # Subsistemas semi-independientes
    "emergencia":           2,   # Propiedad del todo que no esta en las partes
    "reducibilidad":        3,   # El todo = suma de partes
    "anidacion":            4,   # Subsistemas dentro de subsistemas
    "plano":                5,   # Sin jerarquia
    "coherencia":           6,   # Subsistemas alineados
    "conflicto":            7,   # Subsistemas en contradiccion
    "resiliencia":          8,   # Sistema se recupera de perturbaciones
    "fragilidad":           9,   # Sistema se rompe con perturbaciones
}
N_TIPOS_SISTEMAS = 10

LENTE_TOPOLOGIA = {
    "agujero":              0,   # Gap, metrica faltante, discontinuidad
    "continuo":             1,   # Sin gaps, flujo continuo
    "meseta":               2,   # Zona plana prolongada
    "pico":                 3,   # Extremo aislado
    "valle":                4,   # Minimo aislado
    "pendiente":            5,   # Cambio gradual sostenido
    "acantilado":           6,   # Cambio brusco (discontinuidad)
    "compacto":             7,   # Metricas en rango acotado
    "disperso":             8,   # Metricas en rango amplio
    "persistente":          9,   # Patron que NO desaparece
}
N_TIPOS_TOPOLOGIA = 10

LENTE_GEOMETRIA_DIFF = {
    "curvatura_positiva":   0,   # Tendencia convexa (acelerandose)
    "curvatura_negativa":   1,   # Tendencia concava (desacelerandose)
    "curvatura_cero":       2,   # Tendencia lineal
    "inflexion":            3,   # Cambio de curvatura (punto de giro)
    "torsion":              4,   # Cambio en el plano de curvatura
    "geodesica":            5,   # Camino mas corto (eficiencia)
    "desviacion":           6,   # Lejos de la geodesica (ineficiencia)
    "suave":                7,   # Curva sin discontinuidades
    "rugoso":               8,   # Curva con muchos cambios de direccion
    "plano":                9,   # Sin curvatura, sin torsion
}
N_TIPOS_GEOMETRIA = 10

LENTE_CINEMATICA = {
    "acelerando":           0,   # Velocidad creciente
    "desacelerando":        1,   # Velocidad decreciente
    "velocidad_constante":  2,   # Sin aceleracion
    "reposo":               3,   # Velocidad ≈ 0
    "retroceso":            4,   # Velocidad negativa
    "coherente":            5,   # Direccion consistente
    "incoherente":          6,   # Direccion cambiante
    "impulso":              7,   # Cambio brusco de velocidad
    "inercia":              8,   # Resiste cambio (momentum alto)
    "volatil":              9,   # Velocidad fluctuante
}
N_TIPOS_CINEMATICA = 10

# Mapa de lentes
LENTES = {
    "estadistica":     (LENTE_ESTADISTICA,     N_TIPOS_ESTADISTICA),
    "conjuntos":       (LENTE_CONJUNTOS,       N_TIPOS_CONJUNTOS),
    "grafos":          (LENTE_GRAFOS,          N_TIPOS_GRAFOS),
    "markov":          (LENTE_MARKOV,          N_TIPOS_MARKOV),
    "juegos":          (LENTE_JUEGOS,          N_TIPOS_JUEGOS),
    "cibernetica":     (LENTE_CIBERNETICA,     N_TIPOS_CIBERNETICA),
    "sistemas":        (LENTE_SISTEMAS,        N_TIPOS_SISTEMAS),
    "topologia":       (LENTE_TOPOLOGIA,       N_TIPOS_TOPOLOGIA),
    "geometria_diff":  (LENTE_GEOMETRIA_DIFF,  N_TIPOS_GEOMETRIA),
    "cinematica":      (LENTE_CINEMATICA,      N_TIPOS_CINEMATICA),
}


# ============================================================
# CLASIFICADORES POR LENTE
# ============================================================

def _serie_a_retornos(serie):
    """Convierte serie de valores a retornos porcentuales."""
    s = np.array(serie, dtype=float)
    s = s[np.isfinite(s)]
    if len(s) < 2:
        return np.array([0.0])
    retornos = np.diff(s) / np.where(np.abs(s[:-1]) > 1e-10, s[:-1], 1e-10)
    return retornos[np.isfinite(retornos)]


def lente_estadistica(series_dict):
    """Lee datos crudos con la lente estadistica.

    Para cada metrica, clasifica su distribucion temporal.

    Args:
        series_dict: {nombre_metrica: [valor_mes1, valor_mes2, ...]}

    Returns:
        list[int] — secuencia de codigos funcionales estadisticos
    """
    seq = []
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 3:
            seq.append(LENTE_ESTADISTICA["entropia_media"])
            continue

        # Entropia (Shannon sobre bins)
        hist, _ = np.histogram(s, bins=min(5, len(s)))
        probs = hist / hist.sum()
        probs = probs[probs > 0]
        entropia = -np.sum(probs * np.log2(probs))
        max_entropia = np.log2(len(probs))
        entropia_norm = entropia / max_entropia if max_entropia > 0 else 0

        if entropia_norm < 0.3:
            seq.append(LENTE_ESTADISTICA["entropia_baja"])
        elif entropia_norm < 0.7:
            seq.append(LENTE_ESTADISTICA["entropia_media"])
        else:
            seq.append(LENTE_ESTADISTICA["entropia_alta"])

        # Skewness
        sk = float(scipy_stats.skew(s)) if len(s) > 3 else 0
        if sk < -0.5:
            seq.append(LENTE_ESTADISTICA["skew_negativo"])
        elif sk > 0.5:
            seq.append(LENTE_ESTADISTICA["skew_positivo"])
        else:
            seq.append(LENTE_ESTADISTICA["skew_neutro"])

        # Kurtosis
        ku = float(scipy_stats.kurtosis(s)) if len(s) > 4 else 0
        if ku > 1.0:
            seq.append(LENTE_ESTADISTICA["kurtosis_alta"])
        else:
            seq.append(LENTE_ESTADISTICA["kurtosis_baja"])

        # Estacionariedad (tendencia simple)
        trend = np.polyfit(range(len(s)), s, 1)[0]
        rel_trend = abs(trend) / (np.std(s) + 1e-10)
        if rel_trend > 0.3:
            seq.append(LENTE_ESTADISTICA["no_estacionario"])
        else:
            seq.append(LENTE_ESTADISTICA["estacionario"])

        # Concentracion (Gini)
        sorted_s = np.sort(np.abs(s))
        n = len(sorted_s)
        gini = (2 * np.sum((np.arange(1, n+1) * sorted_s)) / (n * np.sum(sorted_s)) - (n + 1) / n) if np.sum(sorted_s) > 0 else 0
        if gini > 0.4:
            seq.append(LENTE_ESTADISTICA["concentracion"])
        else:
            seq.append(LENTE_ESTADISTICA["dispersion"])

    return seq


def lente_conjuntos(series_dict):
    """Lee datos con la lente de teoria de conjuntos.

    Compara conjuntos de metricas "activas" entre periodos.
    Una metrica esta "activa" si esta por encima de su mediana.
    """
    seq = []
    nombres = list(series_dict.keys())
    n_metricas = len(nombres)
    if n_metricas == 0:
        return seq

    # Convertir a matriz (metricas × tiempo)
    max_len = max(len(v) for v in series_dict.values())
    matriz = np.zeros((n_metricas, max_len))
    for i, nombre in enumerate(nombres):
        vals = series_dict[nombre]
        for j, v in enumerate(vals):
            if np.isfinite(v):
                matriz[i, j] = v

    # Para cada par de periodos consecutivos
    for t in range(max_len - 1):
        col_t = matriz[:, t]
        col_t1 = matriz[:, t + 1]
        medianas = np.median(matriz, axis=1)

        set_t = set(np.where(col_t > medianas)[0])
        set_t1 = set(np.where(col_t1 > medianas)[0])

        # Jaccard
        inter = len(set_t & set_t1)
        union = len(set_t | set_t1)
        jaccard = inter / union if union > 0 else 0

        if jaccard > 0.7:
            seq.append(LENTE_CONJUNTOS["jaccard_alto"])
        elif jaccard > 0.3:
            seq.append(LENTE_CONJUNTOS["jaccard_medio"])
        else:
            seq.append(LENTE_CONJUNTOS["jaccard_bajo"])

        # Cobertura
        activas = len(set_t1)
        ratio = activas / n_metricas
        if ratio > 0.8:
            seq.append(LENTE_CONJUNTOS["cobertura_total"])
        elif ratio > 0.4:
            seq.append(LENTE_CONJUNTOS["cobertura_parcial"])
        else:
            seq.append(LENTE_CONJUNTOS["gap"])

    # Simetria primera/segunda mitad
    mid = max_len // 2
    set_h1 = set(np.where(np.mean(matriz[:, :mid], axis=1) > np.median(matriz, axis=1))[0])
    set_h2 = set(np.where(np.mean(matriz[:, mid:], axis=1) > np.median(matriz, axis=1))[0])
    inter_h = len(set_h1 & set_h2)
    union_h = len(set_h1 | set_h2)
    j_halves = inter_h / union_h if union_h > 0 else 0
    if j_halves > 0.6:
        seq.append(LENTE_CONJUNTOS["simetria"])
    else:
        seq.append(LENTE_CONJUNTOS["asimetria"])

    return seq


def lente_grafos(series_dict):
    """Lee datos con la lente de teoria de grafos.

    Construye grafo de correlaciones entre metricas.
    Clasifica la estructura del grafo.
    """
    seq = []
    nombres = list(series_dict.keys())
    n = len(nombres)
    if n < 3:
        return [LENTE_GRAFOS["cluster_disperso"]]

    # Matriz de correlacion
    max_len = max(len(v) for v in series_dict.values())
    matriz = np.zeros((n, max_len))
    for i, nombre in enumerate(nombres):
        vals = series_dict[nombre]
        for j, v in enumerate(vals):
            if np.isfinite(v):
                matriz[i, j] = v

    # Normalizar cada fila para evitar correlaciones degeneradas
    for i in range(n):
        std_i = np.std(matriz[i])
        if std_i < 1e-10:
            matriz[i] = np.random.default_rng(i).normal(0, 1e-6, max_len)

    corr = np.corrcoef(matriz)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)

    # Para cada metrica: clasificar su rol en el grafo
    threshold = 0.5
    for i in range(n):
        connections = np.sum(np.abs(corr[i, :]) > threshold) - 1  # -1 for self
        mean_corr = np.mean(np.abs(corr[i, :])) - 1/n

        if connections > n * 0.6:
            seq.append(LENTE_GRAFOS["hub"])
        elif connections == 0:
            seq.append(LENTE_GRAFOS["isla"])
        elif connections > n * 0.3:
            seq.append(LENTE_GRAFOS["cluster_denso"])
        else:
            seq.append(LENTE_GRAFOS["periferia"])

    # Estructura global
    avg_connections = np.mean([np.sum(np.abs(corr[i, :]) > threshold) - 1 for i in range(n)])
    if avg_connections < 1:
        seq.append(LENTE_GRAFOS["desconexion"])
    elif avg_connections > n * 0.5:
        seq.append(LENTE_GRAFOS["estrella"])
    else:
        seq.append(LENTE_GRAFOS["cluster_disperso"])

    return seq


def lente_markov(series_dict):
    """Lee datos con la lente de cadenas de Markov.

    Clasifica cada metrica en estados (bajo/medio/alto) y
    analiza las transiciones entre estados.
    """
    seq = []
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 4:
            seq.append(LENTE_MARKOV["diagonal_alta"])
            continue

        # Discretizar en 3 estados: bajo(0), medio(1), alto(2)
        p33, p66 = np.percentile(s, [33, 66])
        estados = np.digitize(s, [p33, p66])

        # Matriz de transicion 3×3
        trans = np.zeros((3, 3))
        for t in range(len(estados) - 1):
            trans[estados[t], estados[t + 1]] += 1

        # Normalizar
        row_sums = trans.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        P = trans / row_sums

        # Diagonal (tendencia a permanecer)
        diag_mean = np.mean(np.diag(P))
        if diag_mean > 0.6:
            seq.append(LENTE_MARKOV["diagonal_alta"])
        else:
            seq.append(LENTE_MARKOV["diagonal_baja"])

        # Transicion fuerte o debil
        off_diag = np.mean(P[~np.eye(3, dtype=bool)])
        if off_diag > 0.3:
            seq.append(LENTE_MARKOV["transicion_fuerte"])
        else:
            seq.append(LENTE_MARKOV["transicion_debil"])

        # Absorcion: si algun estado tiene diagonal > 0.9
        if np.max(np.diag(P)) > 0.9:
            seq.append(LENTE_MARKOV["estado_absorbente"])
        else:
            seq.append(LENTE_MARKOV["estado_transitorio"])

        # Periodicidad: alternancias
        alternations = sum(1 for t in range(len(estados)-2) if estados[t] == estados[t+2] and estados[t] != estados[t+1])
        if alternations > len(estados) * 0.3:
            seq.append(LENTE_MARKOV["periodicidad"])
        else:
            seq.append(LENTE_MARKOV["aperiodico"])

    return seq


def lente_juegos(series_dict):
    """Lee datos con la lente de teoria de juegos.

    Analiza PARES de metricas como "jugadores" en tension.
    """
    seq = []
    nombres = list(series_dict.keys())
    n = len(nombres)

    for i in range(n):
        for j in range(i + 1, min(i + 3, n)):  # Solo pares cercanos para no explotar
            s_i = np.array(series_dict[nombres[i]], dtype=float)
            s_j = np.array(series_dict[nombres[j]], dtype=float)
            min_len = min(len(s_i), len(s_j))
            if min_len < 3:
                continue
            s_i, s_j = s_i[:min_len], s_j[:min_len]

            # Retornos
            r_i = np.diff(s_i) / np.where(np.abs(s_i[:-1]) > 1e-10, s_i[:-1], 1e-10)
            r_j = np.diff(s_j) / np.where(np.abs(s_j[:-1]) > 1e-10, s_j[:-1], 1e-10)
            r_i = np.clip(r_i, -10, 10)
            r_j = np.clip(r_j, -10, 10)

            if len(r_i) < 2:
                continue

            # Correlacion de cambios
            corr = np.corrcoef(r_i, r_j)[0, 1] if np.std(r_i) > 1e-10 and np.std(r_j) > 1e-10 else 0
            corr = 0 if not np.isfinite(corr) else corr

            # Suma de cambios
            sum_changes = np.mean(r_i + r_j)

            if corr > 0.5:
                seq.append(LENTE_JUEGOS["cooperacion"])
            elif corr < -0.5:
                seq.append(LENTE_JUEGOS["competencia"])
            elif abs(corr) < 0.2:
                if sum_changes > 0.01:
                    seq.append(LENTE_JUEGOS["suma_positiva"])
                elif sum_changes < -0.01:
                    seq.append(LENTE_JUEGOS["suma_negativa"])
                else:
                    seq.append(LENTE_JUEGOS["nash"])
            else:
                # Tension: uno sube, otro baja → dilema
                signs_different = np.sum(np.sign(r_i) != np.sign(r_j))
                if signs_different > len(r_i) * 0.5:
                    seq.append(LENTE_JUEGOS["dilema"])
                else:
                    seq.append(LENTE_JUEGOS["simetria_juego"])

    if not seq:
        seq = [LENTE_JUEGOS["nash"]]
    return seq


def lente_cibernetica(series_dict):
    """Lee datos con la lente cibernetica.

    Busca feedback loops: si metrica A sube → metrica B sube despues (con delay).
    """
    seq = []
    nombres = list(series_dict.keys())
    n = len(nombres)

    for i in range(n):
        serie = np.array(series_dict[nombres[i]], dtype=float)
        if len(serie) < 5:
            seq.append(LENTE_CIBERNETICA["sin_feedback"])
            continue

        retornos = _serie_a_retornos(serie)
        if len(retornos) < 3:
            seq.append(LENTE_CIBERNETICA["sin_feedback"])
            continue

        # Autocorrelacion (feedback consigo misma)
        autocorr_1 = np.corrcoef(retornos[:-1], retornos[1:])[0, 1] if len(retornos) > 2 and np.std(retornos) > 1e-10 else 0
        autocorr_1 = 0 if not np.isfinite(autocorr_1) else autocorr_1

        if autocorr_1 > 0.3:
            seq.append(LENTE_CIBERNETICA["feedback_positivo"])
        elif autocorr_1 < -0.3:
            seq.append(LENTE_CIBERNETICA["oscilacion"])
        else:
            seq.append(LENTE_CIBERNETICA["sin_feedback"])

        # Amplificacion vs amortiguacion
        if len(retornos) >= 4:
            var_h1 = np.var(retornos[:len(retornos)//2])
            var_h2 = np.var(retornos[len(retornos)//2:])
            if var_h2 > var_h1 * 1.5:
                seq.append(LENTE_CIBERNETICA["amplificacion"])
            elif var_h2 < var_h1 * 0.5:
                seq.append(LENTE_CIBERNETICA["amortiguacion"])
            else:
                # Saturacion: si la serie converge
                diff_abs = np.abs(np.diff(serie))
                if len(diff_abs) >= 3 and diff_abs[-1] < diff_abs[0] * 0.3:
                    seq.append(LENTE_CIBERNETICA["saturacion"])
                # Runaway: si crece sin control
                elif len(diff_abs) >= 3 and diff_abs[-1] > diff_abs[0] * 3:
                    seq.append(LENTE_CIBERNETICA["runaway"])
                else:
                    seq.append(LENTE_CIBERNETICA["delay_corto"])

    return seq


def lente_sistemas(series_dict):
    """Lee datos con la lente de sistemas.

    Analiza acoplamiento, emergencia, coherencia entre metricas.
    """
    seq = []
    nombres = list(series_dict.keys())
    n = len(nombres)
    if n < 3:
        return [LENTE_SISTEMAS["plano"]]

    # Matriz de correlacion
    max_len = max(len(v) for v in series_dict.values())
    matriz = np.zeros((n, max_len))
    for i, nombre in enumerate(nombres):
        vals = series_dict[nombre]
        for j, v in enumerate(vals):
            if np.isfinite(v):
                matriz[i, j] = v

    # Normalizar filas constantes
    for i in range(n):
        if np.std(matriz[i]) < 1e-10:
            matriz[i] = np.random.default_rng(i).normal(0, 1e-6, max_len)

    corr = np.corrcoef(matriz)
    corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)

    # Acoplamiento medio
    acopl = np.mean(np.abs(corr[np.triu_indices(n, k=1)]))
    if acopl > 0.5:
        seq.append(LENTE_SISTEMAS["acoplamiento_fuerte"])
    else:
        seq.append(LENTE_SISTEMAS["acoplamiento_debil"])

    # Emergencia: varianza del "todo" vs suma de varianzas de partes
    var_total = np.var(np.sum(matriz, axis=0))
    var_partes = np.sum(np.var(matriz, axis=1))
    ratio_emergencia = var_total / (var_partes + 1e-10)
    if ratio_emergencia > 1.5:
        seq.append(LENTE_SISTEMAS["emergencia"])
    else:
        seq.append(LENTE_SISTEMAS["reducibilidad"])

    # Coherencia: todas las metricas van en la misma direccion?
    tendencias = [np.polyfit(range(max_len), matriz[i], 1)[0] for i in range(n)]
    signos = np.sign(tendencias)
    coherencia = np.abs(np.mean(signos))
    if coherencia > 0.6:
        seq.append(LENTE_SISTEMAS["coherencia"])
    else:
        seq.append(LENTE_SISTEMAS["conflicto"])

    # Resiliencia: despues de un shock, vuelve?
    for i in range(n):
        serie = matriz[i]
        retornos = np.diff(serie)
        if len(retornos) < 4:
            continue
        # Buscar shocks (retorno > 2σ)
        std_r = np.std(retornos)
        if std_r < 1e-10:
            continue
        shocks = np.where(np.abs(retornos) > 2 * std_r)[0]
        if len(shocks) > 0:
            # Despues del shock, vuelve al nivel?
            for shock_t in shocks:
                if shock_t + 3 < len(serie):
                    pre = serie[shock_t]
                    post = serie[shock_t + 3]
                    if abs(post - pre) < abs(retornos[shock_t]) * 0.5:
                        seq.append(LENTE_SISTEMAS["resiliencia"])
                    else:
                        seq.append(LENTE_SISTEMAS["fragilidad"])
                    break

    return seq


def lente_topologia(series_dict):
    """Lee datos con la lente topologica.

    Busca gaps, mesetas, discontinuidades, persistencia.
    """
    seq = []
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 3:
            seq.append(LENTE_TOPOLOGIA["continuo"])
            continue

        retornos = np.diff(s)
        std_r = np.std(retornos)
        if std_r < 1e-10:
            seq.append(LENTE_TOPOLOGIA["meseta"])
            continue

        # Meseta: muchos periodos con cambio < 0.1σ
        n_planos = np.sum(np.abs(retornos) < std_r * 0.3)
        if n_planos > len(retornos) * 0.6:
            seq.append(LENTE_TOPOLOGIA["meseta"])
        elif n_planos > len(retornos) * 0.3:
            seq.append(LENTE_TOPOLOGIA["continuo"])
        else:
            # Muchos cambios → rugoso
            seq.append(LENTE_TOPOLOGIA["pendiente"])

        # Discontinuidad (acantilado): cambio > 3σ
        max_cambio = np.max(np.abs(retornos))
        if max_cambio > 3 * std_r:
            seq.append(LENTE_TOPOLOGIA["acantilado"])
        else:
            seq.append(LENTE_TOPOLOGIA["continuo"])

        # Persistencia: patron que no desaparece
        # Si los ultimos 3 periodos mantienen la misma tendencia que los primeros 3
        if len(retornos) >= 6:
            trend_start = np.sign(np.mean(retornos[:3]))
            trend_end = np.sign(np.mean(retornos[-3:]))
            if trend_start == trend_end and trend_start != 0:
                seq.append(LENTE_TOPOLOGIA["persistente"])
            else:
                # Pico o valle
                mid_val = np.mean(s[len(s)//3:2*len(s)//3])
                end_val = np.mean(s[-len(s)//3:])
                start_val = np.mean(s[:len(s)//3])
                if mid_val > start_val and mid_val > end_val:
                    seq.append(LENTE_TOPOLOGIA["pico"])
                elif mid_val < start_val and mid_val < end_val:
                    seq.append(LENTE_TOPOLOGIA["valle"])
                else:
                    seq.append(LENTE_TOPOLOGIA["continuo"])

    return seq


def lente_geometria_diff(series_dict):
    """Lee datos con la lente de geometria diferencial.

    Calcula curvatura, torsion, inflexiones.
    """
    seq = []
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 4:
            seq.append(LENTE_GEOMETRIA_DIFF["plano"])
            continue

        # Primera derivada (velocidad)
        d1 = np.diff(s)
        # Segunda derivada (aceleracion = curvatura)
        d2 = np.diff(d1)

        mean_d2 = np.mean(d2)
        std_d1 = np.std(d1)

        if std_d1 < 1e-10:
            seq.append(LENTE_GEOMETRIA_DIFF["plano"])
            continue

        # Curvatura media
        curvatura = mean_d2 / (std_d1 + 1e-10)
        if curvatura > 0.3:
            seq.append(LENTE_GEOMETRIA_DIFF["curvatura_positiva"])
        elif curvatura < -0.3:
            seq.append(LENTE_GEOMETRIA_DIFF["curvatura_negativa"])
        else:
            seq.append(LENTE_GEOMETRIA_DIFF["curvatura_cero"])

        # Inflexiones (cambios de signo en d2)
        sign_changes = np.sum(np.diff(np.sign(d2)) != 0)
        if sign_changes > len(d2) * 0.4:
            seq.append(LENTE_GEOMETRIA_DIFF["rugoso"])
        elif sign_changes > 0:
            seq.append(LENTE_GEOMETRIA_DIFF["inflexion"])
        else:
            seq.append(LENTE_GEOMETRIA_DIFF["suave"])

    return seq


def lente_cinematica(series_dict):
    """Lee datos con la lente cinematica.

    Velocidad, aceleracion, coherencia de movimiento.
    """
    seq = []
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 3:
            seq.append(LENTE_CINEMATICA["reposo"])
            continue

        # Velocidad (primera derivada normalizada)
        velocidad = np.diff(s) / (np.abs(s[:-1]) + 1e-10)
        velocidad = np.clip(velocidad, -10, 10)
        vel_media = np.mean(velocidad)

        # Aceleracion (segunda derivada)
        if len(velocidad) >= 2:
            aceleracion = np.diff(velocidad)
            acel_media = np.mean(aceleracion)
        else:
            acel_media = 0

        # Clasificar velocidad
        if abs(vel_media) < 0.005:
            seq.append(LENTE_CINEMATICA["reposo"])
        elif vel_media > 0.005:
            if acel_media > 0.002:
                seq.append(LENTE_CINEMATICA["acelerando"])
            elif acel_media < -0.002:
                seq.append(LENTE_CINEMATICA["desacelerando"])
            else:
                seq.append(LENTE_CINEMATICA["velocidad_constante"])
        else:  # vel_media < -0.005
            seq.append(LENTE_CINEMATICA["retroceso"])

        # Coherencia direccional
        if len(velocidad) >= 3:
            signos = np.sign(velocidad)
            coherencia = abs(np.mean(signos))
            if coherencia > 0.6:
                seq.append(LENTE_CINEMATICA["coherente"])
            elif np.std(velocidad) > abs(vel_media) * 2:
                seq.append(LENTE_CINEMATICA["volatil"])
            else:
                seq.append(LENTE_CINEMATICA["incoherente"])

    return seq


# Mapa de funciones clasificadoras
CLASIFICADORES = {
    "estadistica":    lente_estadistica,
    "conjuntos":      lente_conjuntos,
    "grafos":         lente_grafos,
    "markov":         lente_markov,
    "juegos":         lente_juegos,
    "cibernetica":    lente_cibernetica,
    "sistemas":       lente_sistemas,
    "topologia":      lente_topologia,
    "geometria_diff": lente_geometria_diff,
    "cinematica":     lente_cinematica,
}


# ============================================================
# PIPELINE COMPLETO: Datos → 10 lentes → 10 secuencias
# ============================================================

def aplicar_10_lentes(series_dict):
    """Aplica las 10 lentes matematicas a datos crudos.

    Args:
        series_dict: {nombre_metrica: [valor_t1, valor_t2, ...]}

    Returns:
        dict {nombre_lente: {"secuencia": list[int], "n_tipos": int}}
    """
    resultados = {}
    for nombre_lente, clasificador in CLASIFICADORES.items():
        _, n_tipos = LENTES[nombre_lente]
        seq = clasificador(series_dict)
        resultados[nombre_lente] = {
            "secuencia": seq,
            "n_tipos": n_tipos,
            "n_tokens": len(seq),
        }
    return resultados


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import sys
    import os
    import time
    sys.path.insert(0, os.path.dirname(__file__))

    from clasificador_empresarial import generar_empresa
    from marcos_matematicos import calcular_10_ejes, FEATURES_POR_NIVEL
    from geometria_isomorfismo import calcular_geometria_completa

    print("=" * 70)
    print("10 LENTES MATEMATICAS — Cada marco como clasificador")
    print("=" * 70)

    # Generar empresa
    tipos = ["saas_growth", "saas_declining", "startup_burn"]

    for tipo in tipos:
        print(f"\n{'='*70}")
        print(f"  EMPRESA: {tipo.upper()}")
        print(f"{'='*70}")

        meses = generar_empresa(tipo, n_meses=12, seed=42)

        # Construir series_dict desde los meses
        series_dict = {}
        metricas = ["revenue", "churn", "ltv_cac", "nps", "conversion",
                     "margen_bruto", "actividad", "adoption", "cash_flow",
                     "concentracion", "equipo_rotacion", "expansion"]
        for m in metricas:
            series_dict[m] = [mes.get(m, 0) for mes in meses]

        # Aplicar 10 lentes
        t0 = time.time()
        resultados = aplicar_10_lentes(series_dict)
        dt = time.time() - t0

        total_tokens = 0
        for nombre, res in resultados.items():
            lente_dict = LENTES[nombre][0]
            inv = {v: k for k, v in lente_dict.items()}
            tokens_texto = [inv.get(t, f"?{t}") for t in res["secuencia"][:8]]
            print(f"  {nombre:<16s}: {res['n_tokens']:3d} tokens | {tokens_texto}")
            total_tokens += res["n_tokens"]

        print(f"\n  Total: {total_tokens} tokens en {dt*1000:.0f}ms")

        # Aplicar 10 marcos a CADA secuencia de lente
        print(f"\n  10 marcos × 10 lentes:")
        t0 = time.time()
        vectores_por_lente = {}
        for nombre, res in resultados.items():
            if len(res["secuencia"]) >= 3:
                v = calcular_10_ejes(res["secuencia"], res["n_tipos"])
                vectores_por_lente[nombre] = v
            else:
                vectores_por_lente[nombre] = np.zeros(FEATURES_POR_NIVEL)

        # Vector mega: concatenar los 10 vectores
        vector_mega = np.concatenate(list(vectores_por_lente.values()))
        dt = time.time() - t0

        n_activas = np.sum(np.abs(vector_mega) > 1e-10)
        print(f"  Vector: {len(vector_mega)}D ({n_activas} activas, {n_activas/len(vector_mega):.0%})")
        print(f"  Latencia: {dt*1000:.0f}ms")

        # Geometria entre lentes
        if len(vectores_por_lente) >= 3:
            # Usar 4 "niveles" arbitrarios agrupando lentes por familia
            grupo_forma = np.concatenate([vectores_por_lente["estadistica"],
                                          vectores_por_lente["topologia"],
                                          vectores_por_lente["geometria_diff"]])
            grupo_dinamica = np.concatenate([vectores_por_lente["markov"],
                                             vectores_por_lente["cinematica"],
                                             vectores_por_lente["cibernetica"]])
            grupo_estructura = np.concatenate([vectores_por_lente["grafos"],
                                               vectores_por_lente["sistemas"],
                                               vectores_por_lente["conjuntos"]])
            grupo_agentes = vectores_por_lente["juegos"]

            # Normas por grupo (magnitud de cada lectura)
            print(f"\n  Magnitud por grupo:")
            print(f"    Forma (estad+topo+geom):     {np.linalg.norm(grupo_forma):.1f}")
            print(f"    Dinamica (markov+cine+ciber): {np.linalg.norm(grupo_dinamica):.1f}")
            print(f"    Estructura (graf+sist+conj):  {np.linalg.norm(grupo_estructura):.1f}")
            print(f"    Agentes (juegos):             {np.linalg.norm(grupo_agentes):.1f}")

    print(f"\n{'='*70}")
    print("$0 total")
