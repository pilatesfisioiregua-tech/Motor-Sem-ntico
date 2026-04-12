"""
Clasificador Funcional de Economía — Toda la matemática detrás de Economía.

Fecha: 2026-04-12

Principio:
  Economía es una forma de observar el mundo, de pensar sobre él.
  Cada fórmula económica produce un resultado que cumple una FUNCIÓN:
  califica, posiciona, compara, mide tensión, detecta equilibrio.

  El Simbionte traduce CADA fórmula a un código funcional que dice
  QUÉ TIPO DE ADJETIVO produce ese cálculo.

  Un economista no calcula un Gini — lee "cuán concentrada está la riqueza".
  Un economista no calcula una elasticidad — lee "cuán sensible es la demanda al precio".

Organización:
  A. MICROECONOMÍA (consumidor, productor, equilibrio, juegos, información)
  B. MACROECONOMÍA (crecimiento, ciclos, monetaria, fiscal, finanzas, internacional)
  C. ECONOMETRÍA (regresión, MLE, GMM, series temporales, panel, causalidad)
  D. MATEMÁTICA PURA (optimización, análisis, álgebra lineal, cálculo, probabilidad)
  E. ECONOMÍA CONDUCTUAL (prospect theory, descuento, racionalidad limitada)

Cada fórmula tiene:
  - Nombre
  - Código funcional (qué tipo de adjetivo produce)
  - Función de cálculo
  - Traducción legible (qué le dice al LLM)

$0 total (compute local)
"""

import numpy as np
from scipy import stats as scipy_stats
from collections import Counter


# ============================================================
# TIPOS FUNCIONALES ECONÓMICOS
# ============================================================
# Cada fórmula produce un TIPO de adjetivo.
# No importa si es micro, macro o econometría —
# lo que importa es QUÉ FUNCIÓN cumple el resultado.

TIPOS_FUNCIONALES = {
    # === NIVEL (dónde está) ===
    "nivel":              0,   # Posiciona un valor en un eje (PIB, precio, utilidad)
    "nivel_per_capita":   1,   # Nivel normalizado por población/unidad
    "nivel_real":         2,   # Nivel ajustado por inflación

    # === CAMBIO (cuánto se movió) ===
    "tasa_cambio":        3,   # Δx/x — cambio porcentual
    "tasa_crecimiento":   4,   # g = (x_t/x_{t-1}) - 1
    "aceleracion":        5,   # Δ(Δx) — cambio del cambio
    "acumulado":          6,   # Σ o ∫ — suma a lo largo del tiempo

    # === SENSIBILIDAD (cuánto responde X a Y) ===
    "elasticidad":        7,   # (Δq/q)/(Δp/p) — respuesta proporcional
    "semi_elasticidad":   8,   # Δq/(q·Δp) — respuesta a cambio absoluto
    "multiplicador":      9,   # dY/dG — cuánto se amplifica un impulso
    "beta":               10,  # Sensibilidad a un factor (CAPM, regresión)

    # === PROPORCIÓN (qué parte del todo) ===
    "ratio":              11,  # a/b — proporción simple
    "share":              12,  # x_i/Σx — participación en el total
    "margen":             13,  # (p-c)/p — proporción de ganancia

    # === DISPERSIÓN (cuán disperso/desigual) ===
    "varianza":           14,  # σ² — dispersión alrededor de la media
    "desviacion":         15,  # σ — dispersión en unidades originales
    "coef_variacion":     16,  # σ/μ — dispersión relativa
    "concentracion":      17,  # Gini, HHI — cuán concentrado/desigual
    "entropia":           18,  # H = -Σp·log(p) — diversidad/incertidumbre

    # === RELACIÓN (cómo se mueven juntos) ===
    "correlacion":        19,  # ρ — co-movimiento lineal
    "covarianza":         20,  # Cov(X,Y) — co-movimiento en unidades
    "causalidad":         21,  # β en modelo causal — efecto de X sobre Y
    "sustitucion":        22,  # TMS, σ — cuánto sustituye uno por otro

    # === EQUILIBRIO (dónde se balancea) ===
    "precio_equilibrio":  23,  # p* donde D=S
    "cantidad_equilibrio":24,  # q* donde D=S
    "tasa_equilibrio":    25,  # r*, i* — tasa natural/neutral
    "steady_state":       26,  # k*, y* — estado estacionario

    # === ÓPTIMO (cuál es el mejor punto) ===
    "optimo":             27,  # x* = argmax f(x)
    "frontera":           28,  # Pareto, posibilidades de producción
    "eficiencia":         29,  # Cuán cerca del óptimo
    "excedente":          30,  # Beneficio neto (consumidor, productor, total)

    # === RIESGO (cuán peligroso/incierto) ===
    "riesgo":             31,  # VaR, σ, β — cuánto puedes perder
    "prima_riesgo":       32,  # E[r] - r_f — compensación por riesgo
    "sharpe":             33,  # (E[r]-r_f)/σ — retorno por unidad de riesgo
    "probabilidad":       34,  # P(evento) — cuán probable es

    # === BIENESTAR (cuánto bienestar genera) ===
    "utilidad":           35,  # U(x) — satisfacción
    "utilidad_marginal":  36,  # ∂U/∂x — satisfacción adicional por unidad
    "bienestar_social":   37,  # W = Σw_i·U_i — bienestar agregado
    "coste_social":       38,  # Externalidad, deadweight loss

    # === PODER (quién domina) ===
    "poder_mercado":      39,  # Lerner index, markup
    "poder_negociacion":  40,  # Nash bargaining, threat points
    "ventaja":            41,  # Comparativa, absoluta, estratégica

    # === TIEMPO (cuándo, a qué velocidad) ===
    "descuento":          42,  # β^t, 1/(1+r)^t — valor presente
    "horizonte":          43,  # T, τ — duración, periodo
    "velocidad":          44,  # dx/dt — rapidez de ajuste
    "persistencia":       45,  # ρ en AR(1) — cuánto dura un shock

    # === ESTRUCTURA (cómo está organizado) ===
    "componentes":        46,  # Descomposición (trend, cycle, seasonal)
    "peso":               47,  # w_i en índice ponderado
    "parametro":          48,  # α, β, γ — parámetro estructural
    "dummy":              49,  # 0/1 — presencia/ausencia de característica

    # === SEÑAL (qué indica) ===
    "gap":                50,  # y - y* — distancia al potencial
    "residuo":            51,  # ε = y - ŷ — lo que el modelo no explica
    "test":               52,  # t-stat, F-stat, χ² — significancia estadística
    "score":              53,  # Índice compuesto (HDI, misery index)
}

N_TIPOS = len(TIPOS_FUNCIONALES)
N_NIVELES = 5  # quintiles
N_TOKENS = N_TIPOS * N_NIVELES  # 54 × 5 = 270 tipos posibles


# ============================================================
# A. MICROECONOMÍA
# ============================================================

FORMULAS_MICRO = {
    # --- Teoría del consumidor ---
    "utilidad_cobb_douglas": {
        "tipo": "utilidad",
        "funcion": lambda x, alpha=0.5: x[0]**alpha * x[1]**(1-alpha) if len(x) >= 2 else 0,
        "texto": "satisfacción del consumidor (Cobb-Douglas)",
    },
    "utilidad_marginal": {
        "tipo": "utilidad_marginal",
        "calculo": "derivada_parcial",
        "texto": "satisfacción adicional por unidad consumida",
    },
    "tms": {
        "tipo": "sustitucion",
        "texto": "cuántas unidades de Y sacrifica por 1 unidad más de X",
    },
    "elasticidad_precio_demanda": {
        "tipo": "elasticidad",
        "texto": "cuánto cambia la demanda cuando el precio sube 1%",
    },
    "elasticidad_ingreso": {
        "tipo": "elasticidad",
        "texto": "cuánto cambia la demanda cuando el ingreso sube 1%",
    },
    "elasticidad_cruzada": {
        "tipo": "elasticidad",
        "texto": "cuánto cambia la demanda de X cuando sube el precio de Y",
    },
    "excedente_consumidor": {
        "tipo": "excedente",
        "texto": "beneficio neto que obtiene el consumidor por pagar menos que su valoración",
    },
    "variacion_compensatoria": {
        "tipo": "bienestar_social",
        "texto": "cuánto dinero necesita el consumidor para quedar igual tras un cambio de precio",
    },
    "variacion_equivalente": {
        "tipo": "bienestar_social",
        "texto": "cuánto pagaría el consumidor para evitar un cambio de precio",
    },

    # --- Teoría del productor ---
    "coste_marginal": {
        "tipo": "utilidad_marginal",
        "texto": "coste adicional de producir una unidad más",
    },
    "coste_medio": {
        "tipo": "ratio",
        "texto": "coste por unidad producida",
    },
    "ingreso_marginal": {
        "tipo": "utilidad_marginal",
        "texto": "ingreso adicional por vender una unidad más",
    },
    "beneficio": {
        "tipo": "excedente",
        "texto": "diferencia entre ingresos totales y costes totales",
    },
    "productividad_marginal": {
        "tipo": "utilidad_marginal",
        "texto": "producto adicional por unidad de input añadida",
    },
    "rendimientos_escala": {
        "tipo": "elasticidad",
        "texto": "cuánto crece el output si escalas todos los inputs proporcionalmente",
    },
    "elasticidad_sustitucion": {
        "tipo": "sustitucion",
        "texto": "facilidad para sustituir un input por otro manteniendo output constante",
    },

    # --- Equilibrio ---
    "exceso_demanda": {
        "tipo": "gap",
        "texto": "cuánto excede la demanda a la oferta a este precio",
    },
    "deadweight_loss": {
        "tipo": "coste_social",
        "texto": "pérdida de bienestar que no recupera nadie (ineficiencia pura)",
    },
    "indice_lerner": {
        "tipo": "poder_mercado",
        "texto": "cuánto puede el monopolista subir el precio sobre el coste marginal",
    },
    "hhi": {
        "tipo": "concentracion",
        "texto": "cuán concentrado está el mercado (suma de cuadrados de cuotas)",
    },

    # --- Juegos ---
    "nash_payoff": {
        "tipo": "optimo",
        "texto": "resultado cuando ningún jugador puede mejorar unilateralmente",
    },
    "valor_shapley": {
        "tipo": "share",
        "texto": "contribución justa de cada jugador a la coalición",
    },
    "surplus_negociacion": {
        "tipo": "excedente",
        "texto": "ganancia total a repartir entre las partes",
    },
}

# ============================================================
# B. MACROECONOMÍA
# ============================================================

FORMULAS_MACRO = {
    # --- Crecimiento ---
    "pib": {
        "tipo": "nivel",
        "texto": "valor total de la producción de una economía",
    },
    "pib_per_capita": {
        "tipo": "nivel_per_capita",
        "texto": "producción por habitante",
    },
    "pib_real": {
        "tipo": "nivel_real",
        "texto": "producción ajustada por inflación",
    },
    "tasa_crecimiento_pib": {
        "tipo": "tasa_crecimiento",
        "texto": "velocidad a la que crece la economía",
    },
    "solow_steady_state": {
        "tipo": "steady_state",
        "texto": "nivel de capital por trabajador donde la inversión iguala la depreciación",
    },
    "golden_rule": {
        "tipo": "optimo",
        "texto": "nivel de ahorro que maximiza el consumo por trabajador en estado estacionario",
    },
    "residuo_solow": {
        "tipo": "residuo",
        "texto": "crecimiento que no se explica por capital ni trabajo (productividad total)",
    },
    "ptf": {
        "tipo": "tasa_crecimiento",
        "texto": "cuánto crece la productividad total de los factores",
    },

    # --- Ciclos ---
    "output_gap": {
        "tipo": "gap",
        "texto": "distancia entre PIB real y potencial (presión inflacionaria si positivo)",
    },
    "tasa_desempleo": {
        "tipo": "ratio",
        "texto": "proporción de la fuerza laboral que busca empleo sin encontrarlo",
    },
    "nairu": {
        "tipo": "tasa_equilibrio",
        "texto": "tasa de desempleo que no acelera la inflación",
    },
    "ley_okun": {
        "tipo": "elasticidad",
        "texto": "cuánto cae el PIB por cada punto de desempleo sobre la NAIRU",
    },
    "curva_phillips": {
        "tipo": "causalidad",
        "texto": "relación inversa entre desempleo e inflación",
    },

    # --- Monetaria ---
    "inflacion": {
        "tipo": "tasa_cambio",
        "texto": "velocidad a la que suben los precios",
    },
    "inflacion_subyacente": {
        "tipo": "tasa_cambio",
        "texto": "inflación sin alimentos ni energía (tendencia de fondo)",
    },
    "ecuacion_fisher": {
        "tipo": "tasa_equilibrio",
        "texto": "tipo de interés real = nominal - inflación esperada",
    },
    "regla_taylor": {
        "tipo": "optimo",
        "texto": "tipo de interés óptimo del banco central dada la inflación y el output gap",
    },
    "velocidad_dinero": {
        "tipo": "velocidad",
        "texto": "cuántas veces se usa cada unidad monetaria por periodo",
    },
    "multiplicador_monetario": {
        "tipo": "multiplicador",
        "texto": "cuánto dinero crea el sistema bancario por cada unidad de base monetaria",
    },

    # --- Fiscal ---
    "multiplicador_fiscal": {
        "tipo": "multiplicador",
        "texto": "cuánto crece el PIB por cada euro de gasto público",
    },
    "deuda_pib": {
        "tipo": "ratio",
        "texto": "proporción de deuda pública sobre el PIB",
    },
    "deficit_primario": {
        "tipo": "gap",
        "texto": "diferencia entre gasto público (sin intereses) e ingresos",
    },
    "sostenibilidad_deuda": {
        "tipo": "test",
        "texto": "si la deuda/PIB converge (sostenible) o diverge (insostenible)",
    },

    # --- Finanzas ---
    "capm_retorno": {
        "tipo": "prima_riesgo",
        "texto": "retorno esperado = tasa libre + beta × prima de mercado",
    },
    "beta_activo": {
        "tipo": "beta",
        "texto": "sensibilidad del activo al mercado",
    },
    "sharpe_ratio": {
        "tipo": "sharpe",
        "texto": "retorno por unidad de riesgo asumido",
    },
    "var_parametrico": {
        "tipo": "riesgo",
        "texto": "máxima pérdida esperada con X% de confianza en Y días",
    },
    "black_scholes": {
        "tipo": "nivel",
        "texto": "precio justo de una opción financiera",
    },
    "tipo_cambio_ppc": {
        "tipo": "precio_equilibrio",
        "texto": "tipo de cambio donde un bien cuesta lo mismo en dos países",
    },

    # --- Internacional ---
    "balanza_comercial": {
        "tipo": "gap",
        "texto": "diferencia entre exportaciones e importaciones",
    },
    "ventaja_comparativa": {
        "tipo": "ventaja",
        "texto": "qué bien produce un país con menor coste de oportunidad",
    },
    "terminos_intercambio": {
        "tipo": "ratio",
        "texto": "precio de exportaciones / precio de importaciones",
    },
}

# ============================================================
# C. ECONOMETRÍA
# ============================================================

FORMULAS_ECONOMETRIA = {
    "ols_beta": {
        "tipo": "causalidad",
        "texto": "efecto estimado de X sobre Y controlando por otros factores",
    },
    "r_cuadrado": {
        "tipo": "ratio",
        "texto": "proporción de la variación de Y explicada por el modelo",
    },
    "error_estandar": {
        "tipo": "desviacion",
        "texto": "incertidumbre en la estimación del coeficiente",
    },
    "t_statistic": {
        "tipo": "test",
        "texto": "cuántos errores estándar está el coeficiente de cero (significancia)",
    },
    "f_statistic": {
        "tipo": "test",
        "texto": "si el modelo completo explica más que la media (significancia conjunta)",
    },
    "p_valor": {
        "tipo": "probabilidad",
        "texto": "probabilidad de ver este resultado si el efecto real fuera cero",
    },
    "intervalo_confianza": {
        "tipo": "riesgo",
        "texto": "rango donde está el valor real con X% de probabilidad",
    },
    "akaike_bic": {
        "tipo": "score",
        "texto": "calidad del modelo penalizada por complejidad (menor = mejor)",
    },
    "durbin_watson": {
        "tipo": "test",
        "texto": "si los residuos están autocorrelacionados (sesgo en errores estándar)",
    },
    "hausman": {
        "tipo": "test",
        "texto": "si efectos fijos o aleatorios es el modelo correcto",
    },
    "sargan_hansen": {
        "tipo": "test",
        "texto": "si los instrumentos son válidos (exogeneidad)",
    },
    "dickey_fuller": {
        "tipo": "test",
        "texto": "si la serie tiene raíz unitaria (no estacionaria)",
    },
    "johansen": {
        "tipo": "test",
        "texto": "cuántas relaciones de largo plazo existen entre variables",
    },
    "granger": {
        "tipo": "causalidad",
        "texto": "si los valores pasados de X predicen Y (causalidad temporal)",
    },
    "garch_volatilidad": {
        "tipo": "varianza",
        "texto": "volatilidad condicional — cuán variable es hoy dado el pasado reciente",
    },
    "did_efecto": {
        "tipo": "causalidad",
        "texto": "efecto de un tratamiento comparando antes/después × tratado/control",
    },
    "rdd_efecto": {
        "tipo": "causalidad",
        "texto": "efecto justo en el umbral donde se asigna el tratamiento",
    },
    "propensity_score": {
        "tipo": "probabilidad",
        "texto": "probabilidad de recibir tratamiento dados los observables",
    },
    "iv_first_stage_f": {
        "tipo": "test",
        "texto": "si el instrumento predice la variable endógena (instrumento fuerte)",
    },
}

# ============================================================
# D. INDICADORES / SCORES COMPUESTOS
# ============================================================

FORMULAS_INDICADORES = {
    "gini": {
        "tipo": "concentracion",
        "texto": "cuán desigualmente está distribuida la renta (0=igualdad, 1=un individuo tiene todo)",
    },
    "ipc": {
        "tipo": "nivel",
        "texto": "nivel general de precios de una cesta de consumo",
    },
    "ipc_variacion": {
        "tipo": "tasa_cambio",
        "texto": "cuánto subieron los precios en este periodo (inflación IPC)",
    },
    "idh": {
        "tipo": "score",
        "texto": "desarrollo humano combinando esperanza de vida, educación e ingreso",
    },
    "indice_miseria": {
        "tipo": "score",
        "texto": "suma de inflación + desempleo (cuánto sufre la población)",
    },
    "big_mac_index": {
        "tipo": "gap",
        "texto": "cuánto está sobre/infravalorada una moneda comparando precios de Big Mac",
    },
    "indice_libertad_economica": {
        "tipo": "score",
        "texto": "grado de libertad económica de un país (propiedad, comercio, regulación)",
    },
    "renta_per_capita_ppc": {
        "tipo": "nivel_per_capita",
        "texto": "ingreso por habitante ajustado por poder adquisitivo",
    },
}

# ============================================================
# E. ECONOMÍA CONDUCTUAL
# ============================================================

FORMULAS_CONDUCTUAL = {
    "prospect_theory_value": {
        "tipo": "utilidad",
        "texto": "valor percibido donde las pérdidas pesan ~2.5x más que las ganancias",
    },
    "descuento_hiperbolico": {
        "tipo": "descuento",
        "texto": "cuánto devalúa el futuro de forma inconsistente (preferencia por lo inmediato)",
    },
    "aversion_perdida": {
        "tipo": "elasticidad",
        "texto": "cuánto más duele perder €100 que alegra ganar €100 (~2.5x)",
    },
    "sesgo_status_quo": {
        "tipo": "persistencia",
        "texto": "tendencia a no cambiar aunque haya opciones mejores",
    },
    "efecto_dotacion": {
        "tipo": "gap",
        "texto": "cuánto más valoras algo por el hecho de poseerlo (WTA > WTP)",
    },
    "framing_effect": {
        "tipo": "gap",
        "texto": "diferencia de decisión según cómo se presenta la misma información",
    },
}

# ============================================================
# CATÁLOGO UNIFICADO
# ============================================================

CATALOGO_COMPLETO = {}
CATALOGO_COMPLETO.update(FORMULAS_MICRO)
CATALOGO_COMPLETO.update(FORMULAS_MACRO)
CATALOGO_COMPLETO.update(FORMULAS_ECONOMETRIA)
CATALOGO_COMPLETO.update(FORMULAS_INDICADORES)
CATALOGO_COMPLETO.update(FORMULAS_CONDUCTUAL)

N_FORMULAS = len(CATALOGO_COMPLETO)

# Mapa inverso: tipo funcional → fórmulas que lo producen
TIPO_A_FORMULAS = {}
for nombre, info in CATALOGO_COMPLETO.items():
    tipo = info["tipo"]
    if tipo not in TIPO_A_FORMULAS:
        TIPO_A_FORMULAS[tipo] = []
    TIPO_A_FORMULAS[tipo].append(nombre)


# ============================================================
# FUNCIONES DE CÁLCULO SOBRE SERIES ECONÓMICAS
# ============================================================

def calcular_formulas_economia(series_dict):
    """Calcula todas las fórmulas económicas aplicables sobre series temporales.

    Acepta cualquier serie temporal con nombres de métricas.
    Detecta automáticamente qué fórmulas son aplicables.

    Args:
        series_dict: {nombre_metrica: [valor_t1, valor_t2, ...]}

    Returns:
        dict {nombre_formula: {"valor": float, "tipo": str, "texto": str}}
    """
    resultados = {}

    for nombre_metrica, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s)]
        if len(s) < 3:
            continue

        retornos = np.diff(s) / np.where(np.abs(s[:-1]) > 1e-10, s[:-1], 1e-10)
        retornos = retornos[np.isfinite(retornos)]

        # --- Nivel ---
        resultados[f"{nombre_metrica}_nivel"] = {
            "valor": float(s[-1]),
            "tipo": "nivel",
            "texto": f"nivel actual de {nombre_metrica}",
        }

        # --- Tasa de cambio ---
        if len(retornos) > 0:
            resultados[f"{nombre_metrica}_tasa_cambio"] = {
                "valor": float(retornos[-1]),
                "tipo": "tasa_cambio",
                "texto": f"cambio porcentual más reciente de {nombre_metrica}",
            }

        # --- Tasa de crecimiento media ---
        if len(retornos) >= 3:
            resultados[f"{nombre_metrica}_crecimiento_medio"] = {
                "valor": float(np.mean(retornos)),
                "tipo": "tasa_crecimiento",
                "texto": f"crecimiento medio por periodo de {nombre_metrica}",
            }

        # --- Aceleración ---
        if len(retornos) >= 4:
            accel = np.diff(retornos)
            resultados[f"{nombre_metrica}_aceleracion"] = {
                "valor": float(np.mean(accel[-3:])),
                "tipo": "aceleracion",
                "texto": f"si {nombre_metrica} se acelera (+) o desacelera (-)",
            }

        # --- Varianza ---
        resultados[f"{nombre_metrica}_varianza"] = {
            "valor": float(np.var(retornos)) if len(retornos) > 1 else 0,
            "tipo": "varianza",
            "texto": f"cuán impredecible es {nombre_metrica}",
        }

        # --- Coeficiente de variación ---
        mean_abs = np.mean(np.abs(s))
        if mean_abs > 1e-10:
            resultados[f"{nombre_metrica}_cv"] = {
                "valor": float(np.std(s) / mean_abs),
                "tipo": "coef_variacion",
                "texto": f"dispersión relativa de {nombre_metrica}",
            }

        # --- Persistencia (autocorrelación) ---
        if len(retornos) >= 5:
            ac = np.corrcoef(retornos[:-1], retornos[1:])[0, 1]
            if np.isfinite(ac):
                resultados[f"{nombre_metrica}_persistencia"] = {
                    "valor": float(ac),
                    "tipo": "persistencia",
                    "texto": f"cuánto dura un shock en {nombre_metrica} (alto=persistente)",
                }

        # --- Gap respecto a tendencia ---
        trend = np.polyfit(range(len(s)), s, 1)
        s_trend = np.polyval(trend, len(s) - 1)
        if abs(s_trend) > 1e-10:
            gap = (s[-1] - s_trend) / abs(s_trend)
            resultados[f"{nombre_metrica}_gap"] = {
                "valor": float(gap),
                "tipo": "gap",
                "texto": f"distancia de {nombre_metrica} a su tendencia (>0 sobre tendencia)",
            }

        # --- Momentum ---
        if len(s) >= 6:
            momentum = s[-1] / s[max(len(s)-6, 0)] - 1
            resultados[f"{nombre_metrica}_momentum"] = {
                "valor": float(momentum),
                "tipo": "tasa_crecimiento",
                "texto": f"crecimiento acumulado reciente de {nombre_metrica}",
            }

    # --- Correlaciones entre pares de series ---
    nombres = list(series_dict.keys())
    for i in range(len(nombres)):
        for j in range(i + 1, min(i + 4, len(nombres))):
            s_i = np.array(series_dict[nombres[i]], dtype=float)
            s_j = np.array(series_dict[nombres[j]], dtype=float)
            min_len = min(len(s_i), len(s_j))
            if min_len < 5:
                continue
            s_i, s_j = s_i[:min_len], s_j[:min_len]
            corr = np.corrcoef(s_i, s_j)[0, 1]
            if np.isfinite(corr):
                resultados[f"corr_{nombres[i]}_{nombres[j]}"] = {
                    "valor": float(corr),
                    "tipo": "correlacion",
                    "texto": f"co-movimiento entre {nombres[i]} y {nombres[j]}",
                }

    # --- Concentración (si hay series de shares/proporciones) ---
    for nombre, serie in series_dict.items():
        s = np.array(serie, dtype=float)
        s = s[np.isfinite(s) & (s > 0)]
        if len(s) >= 3 and np.all(s <= 1):
            sorted_s = np.sort(s)
            n = len(sorted_s)
            gini = (2 * np.sum((np.arange(1, n+1) * sorted_s)) / (n * np.sum(sorted_s)) - (n+1)/n) if np.sum(sorted_s) > 0 else 0
            resultados[f"{nombre}_gini"] = {
                "valor": float(gini),
                "tipo": "concentracion",
                "texto": f"cuán concentrada está la distribución de {nombre}",
            }

    # --- Elasticidades entre pares (si hay precio/cantidad) ---
    # Se calculan si los nombres sugieren pares naturales
    for nombre_q in nombres:
        for nombre_p in nombres:
            if nombre_q == nombre_p:
                continue
            if any(q in nombre_q.lower() for q in ['cantidad', 'demanda', 'output', 'empleo', 'consumo']):
                if any(p in nombre_p.lower() for p in ['precio', 'tasa', 'salario', 'tipo', 'coste']):
                    s_q = np.array(series_dict[nombre_q], dtype=float)
                    s_p = np.array(series_dict[nombre_p], dtype=float)
                    min_len = min(len(s_q), len(s_p))
                    if min_len < 4:
                        continue
                    r_q = np.diff(s_q[:min_len]) / np.where(np.abs(s_q[:min_len-1]) > 1e-10, s_q[:min_len-1], 1e-10)
                    r_p = np.diff(s_p[:min_len]) / np.where(np.abs(s_p[:min_len-1]) > 1e-10, s_p[:min_len-1], 1e-10)
                    r_p_mean = np.mean(np.abs(r_p))
                    if r_p_mean > 1e-10:
                        elast = np.mean(r_q) / r_p_mean
                        resultados[f"elasticidad_{nombre_q}_{nombre_p}"] = {
                            "valor": float(elast),
                            "tipo": "elasticidad",
                            "texto": f"sensibilidad de {nombre_q} a cambios en {nombre_p}",
                        }

    return resultados


def resultados_a_secuencia(resultados, percentiles_ref=None):
    """Convierte resultados de fórmulas económicas en secuencia funcional.

    Args:
        resultados: output de calcular_formulas_economia()
        percentiles_ref: dict {tipo: [p20, p40, p60, p80]}

    Returns:
        list[int] — secuencia de códigos funcionales
    """
    seq = []
    for nombre, info in resultados.items():
        tipo = info["tipo"]
        tipo_idx = TIPOS_FUNCIONALES.get(tipo, 0)
        valor = info["valor"]

        # Clasificar en quintil
        if percentiles_ref and tipo in percentiles_ref:
            thresholds = percentiles_ref[tipo]
            if valor <= thresholds[0]:
                nivel = 0
            elif valor <= thresholds[1]:
                nivel = 1
            elif valor <= thresholds[2]:
                nivel = 2
            elif valor <= thresholds[3]:
                nivel = 3
            else:
                nivel = 4
        else:
            # Default: clasificar por magnitud relativa
            abs_val = abs(valor)
            if abs_val < 0.01:
                nivel = 0  # muy bajo
            elif abs_val < 0.05:
                nivel = 1  # bajo
            elif abs_val < 0.15:
                nivel = 2  # normal
            elif abs_val < 0.40:
                nivel = 3  # alto
            else:
                nivel = 4  # muy alto

        codigo = tipo_idx * N_NIVELES + nivel
        seq.append(codigo)

    return seq


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CLASIFICADOR ECONÓMICO — Catálogo completo")
    print("=" * 70)

    print(f"\n  Tipos funcionales: {N_TIPOS}")
    print(f"  Tokens posibles: {N_TOKENS} ({N_TIPOS} × {N_NIVELES})")
    print(f"  Fórmulas en catálogo: {N_FORMULAS}")

    # Distribución por tipo
    print(f"\n  Distribución por tipo funcional:")
    for tipo, formulas in sorted(TIPO_A_FORMULAS.items(), key=lambda x: -len(x[1])):
        print(f"    {tipo:<22s}: {len(formulas)} fórmulas ({', '.join(formulas[:3])}{'...' if len(formulas)>3 else ''})")

    # Distribución por rama
    print(f"\n  Distribución por rama:")
    print(f"    Micro:       {len(FORMULAS_MICRO)}")
    print(f"    Macro:       {len(FORMULAS_MACRO)}")
    print(f"    Econometría: {len(FORMULAS_ECONOMETRIA)}")
    print(f"    Indicadores: {len(FORMULAS_INDICADORES)}")
    print(f"    Conductual:  {len(FORMULAS_CONDUCTUAL)}")

    # Test con datos económicos simulados
    print(f"\n{'='*70}")
    print("TEST: Series económicas simuladas")
    print(f"{'='*70}")

    np.random.seed(42)
    # Simular una economía durante 48 trimestres (12 años)
    t = np.arange(48)
    pib = 100 * (1.02 ** t) * (1 + 0.02 * np.sin(2*np.pi*t/4) + 0.01 * np.random.randn(48))
    inflacion_nivel = 2.0 + 0.5 * np.sin(2*np.pi*t/8) + 0.3 * np.random.randn(48)
    desempleo = 5.0 - 0.3 * (pib / pib[0] - 1) * 100 + 0.5 * np.random.randn(48)
    tipo_interes = 3.0 + 0.5 * inflacion_nivel + 0.2 * np.random.randn(48)
    consumo = 0.65 * pib + 2 * np.random.randn(48)
    inversion = 0.20 * pib * (1 + 0.1 * np.random.randn(48))
    gasto_publico = 0.15 * pib * (1 + 0.02 * np.random.randn(48))
    exportaciones = 10 * (1.03 ** t) * (1 + 0.05 * np.random.randn(48))
    importaciones = 10 * (1.025 ** t) * (1 + 0.04 * np.random.randn(48))

    series = {
        "pib": list(pib),
        "inflacion": list(inflacion_nivel),
        "desempleo": list(desempleo),
        "tipo_interes": list(tipo_interes),
        "consumo": list(consumo),
        "inversion": list(inversion),
        "gasto_publico": list(gasto_publico),
        "exportaciones": list(exportaciones),
        "importaciones": list(importaciones),
    }

    resultados = calcular_formulas_economia(series)
    print(f"\n  {len(resultados)} fórmulas calculadas sobre 9 series × 48 trimestres")

    # Mostrar resultados por tipo
    por_tipo = {}
    for nombre, info in resultados.items():
        tipo = info["tipo"]
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append((nombre, info))

    for tipo in sorted(por_tipo.keys()):
        items = por_tipo[tipo]
        print(f"\n  {tipo.upper()} ({len(items)}):")
        for nombre, info in items[:5]:
            print(f"    {nombre:<40s} = {info['valor']:+.4f}  ({info['texto']})")
        if len(items) > 5:
            print(f"    ... y {len(items)-5} más")

    # Secuencia funcional
    seq = resultados_a_secuencia(resultados)
    print(f"\n  Secuencia funcional: {len(seq)} tokens, {len(set(seq))} tipos únicos")
    freq = Counter(seq)
    print(f"  Top 5 tokens: {freq.most_common(5)}")
