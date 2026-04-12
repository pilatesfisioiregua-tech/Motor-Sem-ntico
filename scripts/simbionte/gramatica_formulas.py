"""
Gramática de Fórmulas — Cada fórmula es una oración, cada operación una palabra.

Fecha: 2026-04-12

Principio:
  Varianza = Σ(xi - μ)² / n

  No es UN número. Es una ORACIÓN:
    1. μ = Σx/n          → ACUMULAR + NORMALIZAR = "encontrar el centro" (SUJETO)
    2. (xi - μ)          → COMPARAR = "medir distancia al centro" (ADJETIVO)
    3. (xi - μ)²         → TRANSFORMAR_EJE = "eliminar dirección, conservar magnitud"
    4. Σ(xi - μ)²        → ACUMULAR = "sumar todas las magnitudes"
    5. Σ(xi - μ)² / n    → NORMALIZAR = "cuánta magnitud por punto"

  El resultado final: adjetivo predicativo que califica al conjunto
  en el eje de dispersión.

  TODA fórmula económica se descompone así.
  Y formulas de ramas diferentes que comparten la misma secuencia
  de operaciones SON ISOMORFAS — hacen lo mismo sobre dominios diferentes.

Vocabulario:
  12 operaciones primitivas = las 12 funciones sintácticas de la matemática.

$0 total (compute local)
"""

import numpy as np
from collections import Counter


# ============================================================
# VOCABULARIO: 12 operaciones primitivas
# ============================================================

OPS = {
    "ACUMULAR":       0,   # Σ, ∫ — agregar, sumar, acumular
    "NORMALIZAR":     1,   # ÷n, /total — proyectar sobre unidad
    "COMPARAR":       2,   # − (resta) — medir distancia, diferencia
    "TRANSFORMAR":    3,   # ², √, log, exp — cambiar de eje/escala
    "ESCALAR":        4,   # × constante — amplificar, ponderar
    "COMPONER":       5,   # × entre variables — combinar dos ejes
    "DERIVAR":        6,   # d/dx, Δ/Δt — velocidad de cambio
    "INTEGRAR":       7,   # ∫dt — acumular a lo largo del tiempo
    "SELECCIONAR":    8,   # max, min, argmax — elegir extremo
    "CONDICIONAR":    9,   # E[X|Y], P(A|B) — restringir universo
    "INVERTIR":       10,  # 1/x, x⁻¹ — reciprocar, voltear eje
    "ACOTAR":         11,  # max(0,x), min(1,x), clamp — poner límites
}

N_OPS = len(OPS)

# Nombres legibles para decodificación
OPS_TEXTO = {
    "ACUMULAR":     "acumula (agrega en un eje)",
    "NORMALIZAR":   "normaliza (proyecta por unidad)",
    "COMPARAR":     "compara (mide distancia)",
    "TRANSFORMAR":  "transforma (cambia de eje/escala)",
    "ESCALAR":      "escala (pondera/amplifica)",
    "COMPONER":     "compone (combina dos ejes)",
    "DERIVAR":      "deriva (mide velocidad de cambio)",
    "INTEGRAR":     "integra (acumula en el tiempo)",
    "SELECCIONAR":  "selecciona (elige extremo)",
    "CONDICIONAR":  "condiciona (restringe universo)",
    "INVERTIR":     "invierte (reciproca el eje)",
    "ACOTAR":       "acota (pone límites)",
}

# Rol sintáctico de cada operación
OPS_ROL = {
    "ACUMULAR":     "verbo_acumulativo",
    "NORMALIZAR":   "verbo_normalizador",
    "COMPARAR":     "verbo_comparativo",
    "TRANSFORMAR":  "verbo_transformador",
    "ESCALAR":      "modificador",
    "COMPONER":     "conjuncion",
    "DERIVAR":      "verbo_temporal",
    "INTEGRAR":     "verbo_acumulativo_temporal",
    "SELECCIONAR":  "determinante",
    "CONDICIONAR":  "subordinante",
    "INVERTIR":     "verbo_inversor",
    "ACOTAR":       "adverbio_limitador",
}


# ============================================================
# CATÁLOGO: Cada fórmula como secuencia de operaciones
# ============================================================

FORMULAS = {
    # ==========================================
    # A. ESTADÍSTICA DESCRIPTIVA
    # ==========================================
    "media": {
        "formula": "μ = Σxi / n",
        "ops": ["ACUMULAR", "NORMALIZAR"],
        "lectura": "acumula todos los valores y normaliza por cantidad → dónde está el centro",
        "resultado": "sujeto (punto de referencia del conjunto)",
        "rama": "estadistica",
    },
    "mediana": {
        "formula": "x_{n/2} de la serie ordenada",
        "ops": ["TRANSFORMAR", "SELECCIONAR"],
        "lectura": "transforma a serie ordenada y selecciona el punto central → centro robusto",
        "resultado": "sujeto robusto (centro que ignora extremos)",
        "rama": "estadistica",
    },
    "varianza": {
        "formula": "σ² = Σ(xi-μ)² / n",
        "ops": ["ACUMULAR", "NORMALIZAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR"],
        "lectura": "encuentra el centro (media), compara cada punto con el centro, transforma a magnitud (²), acumula magnitudes, normaliza por cantidad → cuánta dispersión por punto",
        "resultado": "adjetivo predicativo de dispersión",
        "rama": "estadistica",
    },
    "desviacion_estandar": {
        "formula": "σ = √(Σ(xi-μ)² / n)",
        "ops": ["ACUMULAR", "NORMALIZAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "TRANSFORMAR"],
        "lectura": "varianza + transforma de vuelta al eje original (√) → dispersión en unidades originales",
        "resultado": "adjetivo predicativo de dispersión en escala original",
        "rama": "estadistica",
    },
    "coeficiente_variacion": {
        "formula": "CV = σ / μ",
        "ops": ["ACUMULAR", "NORMALIZAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "TRANSFORMAR", "NORMALIZAR"],
        "lectura": "desviación estándar normalizada por la media → dispersión RELATIVA al nivel",
        "resultado": "adjetivo predicativo de dispersión relativa",
        "rama": "estadistica",
    },
    "skewness": {
        "formula": "γ = E[(X-μ)³] / σ³",
        "ops": ["COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "NORMALIZAR"],
        "lectura": "compara con el centro, transforma al cubo (preserva dirección + amplifica extremos), acumula, normaliza 2x → hacia dónde se inclina",
        "resultado": "adjetivo de asimetría (dirección del riesgo)",
        "rama": "estadistica",
    },
    "kurtosis": {
        "formula": "κ = E[(X-μ)⁴] / σ⁴",
        "ops": ["COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "NORMALIZAR"],
        "lectura": "como skewness pero a la 4ª potencia → amplifica extremos aún más → cuán probables son los eventos extremos",
        "resultado": "adjetivo de riesgo de colas",
        "rama": "estadistica",
    },
    "correlacion": {
        "formula": "ρ = Σ(xi-μx)(yi-μy) / (n·σx·σy)",
        "ops": ["COMPARAR", "COMPARAR", "COMPONER", "ACUMULAR", "NORMALIZAR", "NORMALIZAR"],
        "lectura": "compara cada X con su centro, compara cada Y con su centro, compone las distancias (×), acumula, normaliza 2x → cuánto se mueven juntos",
        "resultado": "adjetivo de relación entre dos ejes",
        "rama": "estadistica",
    },
    "covarianza": {
        "formula": "Cov = Σ(xi-μx)(yi-μy) / n",
        "ops": ["COMPARAR", "COMPARAR", "COMPONER", "ACUMULAR", "NORMALIZAR"],
        "lectura": "como correlación sin normalizar por desviaciones → co-movimiento en unidades originales",
        "resultado": "adjetivo de co-movimiento absoluto",
        "rama": "estadistica",
    },
    "percentil": {
        "formula": "P_k = valor en posición k·n/100",
        "ops": ["TRANSFORMAR", "ESCALAR", "SELECCIONAR"],
        "lectura": "transforma a serie ordenada, escala posición, selecciona → dónde está este punto en la distribución",
        "resultado": "adjetivo de posición relativa",
        "rama": "estadistica",
    },
    "gini": {
        "formula": "G = (2·Σi·xi) / (n·Σxi) - (n+1)/n",
        "ops": ["TRANSFORMAR", "ESCALAR", "ACUMULAR", "NORMALIZAR", "COMPARAR"],
        "lectura": "ordena, pondera por posición, acumula, normaliza, compara con distribución uniforme → cuánta desigualdad",
        "resultado": "adjetivo de concentración/desigualdad",
        "rama": "estadistica",
    },
    "entropia_shannon": {
        "formula": "H = -Σp·log(p)",
        "ops": ["NORMALIZAR", "TRANSFORMAR", "COMPONER", "ACUMULAR", "TRANSFORMAR"],
        "lectura": "normaliza a probabilidades, transforma a log (comprime), compone p×log(p), acumula, invierte signo → cuánta incertidumbre/diversidad",
        "resultado": "adjetivo de diversidad/incertidumbre",
        "rama": "estadistica",
    },

    # ==========================================
    # B. MICROECONOMÍA
    # ==========================================
    "utilidad_marginal": {
        "formula": "MU = ∂U/∂x",
        "ops": ["DERIVAR"],
        "lectura": "deriva la utilidad respecto al bien → cuánta satisfacción adicional por unidad",
        "resultado": "adjetivo de satisfacción marginal",
        "rama": "micro",
    },
    "tasa_marginal_sustitucion": {
        "formula": "TMS = MUx/MUy = -dy/dx|U=cte",
        "ops": ["DERIVAR", "DERIVAR", "NORMALIZAR"],
        "lectura": "deriva utilidad por X, deriva por Y, divide → cuánto Y sacrificas por 1 más de X",
        "resultado": "adjetivo de sustituibilidad",
        "rama": "micro",
    },
    "elasticidad_precio": {
        "formula": "ε = (∂Q/Q)/(∂P/P) = (∂Q/∂P)·(P/Q)",
        "ops": ["DERIVAR", "NORMALIZAR", "DERIVAR", "NORMALIZAR", "NORMALIZAR"],
        "lectura": "deriva cantidad respecto a precio, normaliza ambos por sus niveles → cambio proporcional de demanda por cambio proporcional de precio",
        "resultado": "adjetivo de sensibilidad proporcional",
        "rama": "micro",
    },
    "excedente_consumidor": {
        "formula": "EC = ∫[0,Q*] D(q)dq - P*·Q*",
        "ops": ["INTEGRAR", "COMPONER", "COMPARAR"],
        "lectura": "integra la curva de demanda (lo que estaría dispuesto a pagar), compone precio×cantidad (lo que paga), compara → beneficio neto del consumidor",
        "resultado": "adjetivo de bienestar del consumidor",
        "rama": "micro",
    },
    "coste_marginal": {
        "formula": "MC = dC/dq",
        "ops": ["DERIVAR"],
        "lectura": "deriva el coste total respecto a la cantidad → cuánto cuesta producir una unidad más",
        "resultado": "adjetivo de coste incremental",
        "rama": "micro",
    },
    "beneficio_maximo": {
        "formula": "π* : dπ/dq = 0 → MR = MC",
        "ops": ["DERIVAR", "COMPARAR", "SELECCIONAR"],
        "lectura": "deriva beneficio, compara ingreso marginal con coste marginal, selecciona punto donde son iguales → producción óptima",
        "resultado": "sujeto (punto óptimo de producción)",
        "rama": "micro",
    },
    "indice_lerner": {
        "formula": "L = (P-MC)/P",
        "ops": ["COMPARAR", "NORMALIZAR"],
        "lectura": "compara precio con coste marginal, normaliza por precio → cuánto poder de mercado tiene la empresa",
        "resultado": "adjetivo de poder de mercado",
        "rama": "micro",
    },
    "hhi": {
        "formula": "HHI = Σsi²",
        "ops": ["NORMALIZAR", "TRANSFORMAR", "ACUMULAR"],
        "lectura": "normaliza a cuotas de mercado, transforma al cuadrado (amplifica dominantes), acumula → cuán concentrado está el mercado",
        "resultado": "adjetivo de concentración de mercado",
        "rama": "micro",
    },
    "equilibrio_nash": {
        "formula": "σ* : ui(σi*, σ-i*) ≥ ui(σi, σ-i*) ∀i,σi",
        "ops": ["COMPARAR", "CONDICIONAR", "SELECCIONAR"],
        "lectura": "compara payoff de cada estrategia condicionado a lo que hacen los demás, selecciona donde nadie mejora cambiando → punto de equilibrio",
        "resultado": "sujeto (estado de equilibrio estratégico)",
        "rama": "micro",
    },
    "valor_shapley": {
        "formula": "φi = Σ [|S|!(n-|S|-1)!/n!] · [v(S∪{i})-v(S)]",
        "ops": ["COMPARAR", "ESCALAR", "ACUMULAR", "NORMALIZAR"],
        "lectura": "compara valor con y sin el jugador i, escala por factor combinatorio, acumula sobre todas las coaliciones, normaliza → contribución justa de cada jugador",
        "resultado": "adjetivo de contribución justa",
        "rama": "micro",
    },
    "deadweight_loss": {
        "formula": "DWL = ½·(P_m-P_c)·(Q_c-Q_m)",
        "ops": ["COMPARAR", "COMPARAR", "COMPONER", "ESCALAR"],
        "lectura": "compara precio monopolio vs competitivo, compara cantidades, compone ambas diferencias (área del triángulo), escala por ½ → pérdida que no recupera nadie",
        "resultado": "adjetivo de ineficiencia social",
        "rama": "micro",
    },

    # ==========================================
    # C. MACROECONOMÍA
    # ==========================================
    "pib": {
        "formula": "Y = C + I + G + (X-M)",
        "ops": ["ACUMULAR", "COMPARAR", "ACUMULAR"],
        "lectura": "acumula consumo+inversión+gasto, compara exportaciones-importaciones, acumula todo → producción total",
        "resultado": "sujeto (tamaño de la economía)",
        "rama": "macro",
    },
    "deflactor": {
        "formula": "D = PIB_nominal / PIB_real × 100",
        "ops": ["NORMALIZAR", "ESCALAR"],
        "lectura": "normaliza nominal por real, escala a índice → cuánto subieron los precios en general",
        "resultado": "adjetivo de nivel de precios",
        "rama": "macro",
    },
    "tasa_crecimiento": {
        "formula": "g = (Yt - Yt-1) / Yt-1",
        "ops": ["COMPARAR", "NORMALIZAR"],
        "lectura": "compara con el periodo anterior, normaliza por el nivel anterior → velocidad de crecimiento",
        "resultado": "adjetivo de velocidad",
        "rama": "macro",
    },
    "solow_steady_state": {
        "formula": "k* : sf(k*) = (n+δ)k*",
        "ops": ["COMPONER", "COMPONER", "COMPARAR", "SELECCIONAR"],
        "lectura": "compone ahorro×producción, compone depreciación×capital, compara inversión con depreciación, selecciona donde son iguales → capital de largo plazo",
        "resultado": "sujeto (estado estacionario)",
        "rama": "macro",
    },
    "residuo_solow": {
        "formula": "A = Y / (K^α · L^(1-α))",
        "ops": ["TRANSFORMAR", "COMPONER", "NORMALIZAR"],
        "lectura": "transforma inputs por elasticidades, compone capital×trabajo, normaliza output por inputs → lo que no explican los factores (productividad)",
        "resultado": "residuo (lo no explicado = innovación)",
        "rama": "macro",
    },
    "ecuacion_euler": {
        "formula": "u'(ct) = β(1+r)u'(ct+1)",
        "ops": ["DERIVAR", "DERIVAR", "ESCALAR", "COMPARAR"],
        "lectura": "deriva utilidad hoy, deriva utilidad mañana, escala por descuento×retorno, compara → cuánto sacrificas hoy por mañana",
        "resultado": "adjetivo de paciencia intertemporal",
        "rama": "macro",
    },
    "curva_phillips": {
        "formula": "π = πe + β(Y-Y*) + ε",
        "ops": ["COMPARAR", "ESCALAR", "ACUMULAR"],
        "lectura": "compara output con potencial (gap), escala por sensibilidad, acumula expectativas + shock → inflación",
        "resultado": "adjetivo de presión inflacionaria",
        "rama": "macro",
    },
    "regla_taylor": {
        "formula": "i = r* + π + 0.5(π-π*) + 0.5(Y-Y*)/Y*",
        "ops": ["COMPARAR", "COMPARAR", "ESCALAR", "ESCALAR", "ACUMULAR"],
        "lectura": "compara inflación con target, compara output con potencial, escala ambas desviaciones, acumula con tasa natural → tipo de interés óptimo",
        "resultado": "prescripción (qué debería hacer el banco central)",
        "rama": "macro",
    },
    "multiplicador_fiscal": {
        "formula": "m = 1/(1-c(1-t))",
        "ops": ["COMPONER", "COMPARAR", "INVERTIR"],
        "lectura": "compone propensión marginal×(1-impuesto), compara con 1, invierte → cuánto se amplifica cada euro de gasto",
        "resultado": "adjetivo de amplificación",
        "rama": "macro",
    },
    "ecuacion_fisher": {
        "formula": "r = i - πe",
        "ops": ["COMPARAR"],
        "lectura": "compara tipo nominal con inflación esperada → tipo de interés real",
        "resultado": "adjetivo de coste real del dinero",
        "rama": "macro",
    },
    "velocidad_dinero": {
        "formula": "V = PY/M",
        "ops": ["COMPONER", "NORMALIZAR"],
        "lectura": "compone precios×output, normaliza por masa monetaria → cuántas veces circula cada euro",
        "resultado": "adjetivo de velocidad monetaria",
        "rama": "macro",
    },
    "output_gap": {
        "formula": "gap = (Y - Y*) / Y*",
        "ops": ["COMPARAR", "NORMALIZAR"],
        "lectura": "compara PIB real con potencial, normaliza → cuánto está la economía por encima/debajo de su capacidad",
        "resultado": "adjetivo de presión (inflacionaria si +, recesiva si -)",
        "rama": "macro",
    },
    "ley_okun": {
        "formula": "Δu = -β·(ΔY/Y - g*)",
        "ops": ["DERIVAR", "NORMALIZAR", "COMPARAR", "ESCALAR", "TRANSFORMAR"],
        "lectura": "deriva crecimiento, normaliza, compara con crecimiento potencial, escala por sensibilidad, invierte signo → cuánto desempleo genera cada punto de gap",
        "resultado": "adjetivo de coste humano del gap",
        "rama": "macro",
    },

    # ==========================================
    # D. FINANZAS
    # ==========================================
    "capm": {
        "formula": "E[ri] = rf + βi·(E[rm]-rf)",
        "ops": ["COMPARAR", "ESCALAR", "ACUMULAR"],
        "lectura": "compara retorno mercado con tasa libre (prima), escala por beta (sensibilidad), acumula con tasa libre → retorno justo por el riesgo",
        "resultado": "prescripción (cuánto deberías ganar dado tu riesgo)",
        "rama": "finanzas",
    },
    "beta_capm": {
        "formula": "β = Cov(ri,rm) / Var(rm)",
        "ops": ["COMPARAR", "COMPARAR", "COMPONER", "ACUMULAR", "NORMALIZAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "NORMALIZAR"],
        "lectura": "covarianza del activo con el mercado normalizada por varianza del mercado → cuánto se mueve el activo por cada 1% del mercado",
        "resultado": "adjetivo de sensibilidad al mercado",
        "rama": "finanzas",
    },
    "sharpe": {
        "formula": "S = (E[r]-rf) / σ",
        "ops": ["COMPARAR", "NORMALIZAR"],
        "lectura": "compara retorno con tasa libre, normaliza por volatilidad → cuánto ganas por cada unidad de riesgo",
        "resultado": "adjetivo de eficiencia riesgo/retorno",
        "rama": "finanzas",
    },
    "valor_presente_neto": {
        "formula": "VPN = Σ CFt/(1+r)^t",
        "ops": ["ESCALAR", "INVERTIR", "TRANSFORMAR", "ACUMULAR"],
        "lectura": "escala cada flujo por factor de descuento (invierte + transforma por exponente temporal), acumula → valor hoy de todos los flujos futuros",
        "resultado": "sujeto (valor fundamental del activo)",
        "rama": "finanzas",
    },
    "tir": {
        "formula": "TIR: Σ CFt/(1+TIR)^t = 0",
        "ops": ["ESCALAR", "INVERTIR", "TRANSFORMAR", "ACUMULAR", "COMPARAR", "SELECCIONAR"],
        "lectura": "como VPN pero selecciona la tasa que hace VPN=0 → rentabilidad implícita de la inversión",
        "resultado": "adjetivo de rentabilidad implícita",
        "rama": "finanzas",
    },
    "black_scholes": {
        "formula": "C = S·N(d1) - K·e^(-rT)·N(d2)",
        "ops": ["TRANSFORMAR", "CONDICIONAR", "COMPONER", "ESCALAR", "INVERTIR", "TRANSFORMAR", "CONDICIONAR", "COMPONER", "COMPARAR"],
        "lectura": "transforma a distribución normal, condiciona por probabilidad de ejercicio, compone precio×probabilidad para ambas partes, escala por descuento, compara → precio justo de la opción",
        "resultado": "sujeto (precio justo de un derecho futuro)",
        "rama": "finanzas",
    },
    "var_parametrico": {
        "formula": "VaR = μ - z_α · σ",
        "ops": ["ESCALAR", "COMPARAR"],
        "lectura": "escala desviación por z de confianza, compara con media → máxima pérdida probable",
        "resultado": "adjetivo de riesgo extremo",
        "rama": "finanzas",
    },

    # ==========================================
    # E. ECONOMETRÍA
    # ==========================================
    "ols": {
        "formula": "β = (X'X)⁻¹X'y",
        "ops": ["COMPONER", "INVERTIR", "COMPONER"],
        "lectura": "compone X consigo misma (varianza de X), invierte, compone con X'y (covarianza) → efecto de X sobre Y",
        "resultado": "adjetivo de efecto causal (estimado)",
        "rama": "econometria",
    },
    "r_cuadrado": {
        "formula": "R² = 1 - SSR/SST = 1 - Σei²/Σ(yi-ȳ)²",
        "ops": ["COMPARAR", "TRANSFORMAR", "ACUMULAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "COMPARAR"],
        "lectura": "acumula residuos al cuadrado, acumula variación total al cuadrado, normaliza, compara con 1 → cuánto explica el modelo",
        "resultado": "adjetivo de poder explicativo",
        "rama": "econometria",
    },
    "t_statistic": {
        "formula": "t = β̂ / se(β̂)",
        "ops": ["NORMALIZAR"],
        "lectura": "normaliza el coeficiente por su error estándar → cuántas veces más grande es el efecto que su incertidumbre",
        "resultado": "adjetivo de significancia (señal/ruido)",
        "rama": "econometria",
    },
    "did": {
        "formula": "τ = (Ȳ_T,post - Ȳ_T,pre) - (Ȳ_C,post - Ȳ_C,pre)",
        "ops": ["COMPARAR", "COMPARAR", "COMPARAR"],
        "lectura": "compara antes/después en tratados, compara antes/después en control, compara ambos cambios → efecto neto del tratamiento",
        "resultado": "adjetivo de efecto causal (doble diferencia)",
        "rama": "econometria",
    },
    "mle": {
        "formula": "θ̂ = argmax Σ log f(xi|θ)",
        "ops": ["CONDICIONAR", "TRANSFORMAR", "ACUMULAR", "SELECCIONAR"],
        "lectura": "condiciona probabilidad por parámetros, transforma a log, acumula (log-verosimilitud), selecciona máximo → parámetros más probables",
        "resultado": "sujeto (mejor estimación de los parámetros)",
        "rama": "econometria",
    },
    "gmm": {
        "formula": "θ̂ = argmin g(θ)'W g(θ)",
        "ops": ["CONDICIONAR", "COMPONER", "ESCALAR", "SELECCIONAR"],
        "lectura": "condiciona momentos por parámetros, compone g×W×g (distancia ponderada), selecciona mínimo → parámetros que mejor cumplen las condiciones de momento",
        "resultado": "sujeto (estimación por momentos)",
        "rama": "econometria",
    },
    "iv_2sls": {
        "formula": "β̂_IV = (Z'X)⁻¹Z'y",
        "ops": ["COMPONER", "INVERTIR", "COMPONER"],
        "lectura": "como OLS pero usando instrumento Z en lugar de X → efecto causal limpio de endogeneidad",
        "resultado": "adjetivo de efecto causal (instrumentado)",
        "rama": "econometria",
    },

    # ==========================================
    # F. ECONOMÍA CONDUCTUAL
    # ==========================================
    "prospect_value": {
        "formula": "v(x) = x^α si x≥0, -λ(-x)^β si x<0",
        "ops": ["CONDICIONAR", "TRANSFORMAR", "ESCALAR"],
        "lectura": "condiciona por signo (ganancia/pérdida), transforma por potencia (concavidad/convexidad), escala pérdidas por λ≈2.5 → valor percibido asimétrico",
        "resultado": "adjetivo de valor percibido (pérdidas pesan 2.5× más)",
        "rama": "conductual",
    },
    "descuento_hiperbolico": {
        "formula": "D(t) = 1/(1+kt)",
        "ops": ["ESCALAR", "ACUMULAR", "INVERTIR"],
        "lectura": "escala tiempo por k, acumula con 1, invierte → descuento inconsistente (hoy pesa mucho, mañana casi igual que pasado mañana)",
        "resultado": "adjetivo de impaciencia inconsistente",
        "rama": "conductual",
    },
    "probabilidad_ponderada": {
        "formula": "w(p) = p^γ / (p^γ + (1-p)^γ)^(1/γ)",
        "ops": ["TRANSFORMAR", "TRANSFORMAR", "ACUMULAR", "TRANSFORMAR", "NORMALIZAR"],
        "lectura": "transforma probabilidades (sobrepondera raros, infrapondera frecuentes) → percepción distorsionada del riesgo",
        "resultado": "adjetivo de distorsión probabilística",
        "rama": "conductual",
    },
}

N_FORMULAS = len(FORMULAS)


# ============================================================
# FUNCIONES DE ANÁLISIS
# ============================================================

def formula_a_secuencia(nombre):
    """Devuelve la secuencia de operaciones de una fórmula como códigos."""
    if nombre not in FORMULAS:
        return []
    ops_nombres = FORMULAS[nombre]["ops"]
    return [OPS[op] for op in ops_nombres]


def todas_las_secuencias():
    """Devuelve todas las fórmulas como secuencias de operaciones."""
    return {nombre: formula_a_secuencia(nombre) for nombre in FORMULAS}


def detectar_isomorfismos():
    """Encuentra fórmulas con la misma secuencia de operaciones (isomorfas).

    Dos fórmulas con la misma gramática hacen lo MISMO sobre dominios diferentes.
    """
    seqs = todas_las_secuencias()

    # Agrupar por secuencia
    por_secuencia = {}
    for nombre, seq in seqs.items():
        key = tuple(seq)
        if key not in por_secuencia:
            por_secuencia[key] = []
        por_secuencia[key].append(nombre)

    # Filtrar grupos con 2+
    isomorfismos = {k: v for k, v in por_secuencia.items() if len(v) >= 2}
    return isomorfismos


def decodificar_formula(nombre):
    """Decodifica una fórmula a texto legible para un LLM."""
    if nombre not in FORMULAS:
        return f"Fórmula '{nombre}' no encontrada en catálogo."

    f = FORMULAS[nombre]
    lines = []
    lines.append(f"**{nombre}**: {f['formula']}")
    lines.append(f"  Lectura: {f['lectura']}")
    lines.append(f"  Resultado: {f['resultado']}")
    lines.append(f"  Operaciones: {' → '.join(f['ops'])}")
    return "\n".join(lines)


def perfil_operaciones():
    """Cuenta la frecuencia de cada operación en todo el catálogo."""
    counts = Counter()
    for nombre, info in FORMULAS.items():
        for op in info["ops"]:
            counts[op] += 1
    return counts


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("GRAMÁTICA DE FÓRMULAS — Cada fórmula es una oración")
    print("=" * 70)

    print(f"\n  Operaciones primitivas: {N_OPS}")
    print(f"  Fórmulas en catálogo: {N_FORMULAS}")

    # Perfil de operaciones
    print(f"\n  FRECUENCIA DE OPERACIONES (en todo el catálogo):")
    perfil = perfil_operaciones()
    for op, count in perfil.most_common():
        bar = "█" * count
        print(f"    {op:<14s}: {count:3d} {bar}")

    # Distribución por rama
    ramas = Counter(f["rama"] for f in FORMULAS.values())
    print(f"\n  POR RAMA:")
    for rama, n in ramas.most_common():
        print(f"    {rama:<14s}: {n}")

    # Longitud de fórmulas (complejidad)
    lengths = [(nombre, len(info["ops"])) for nombre, info in FORMULAS.items()]
    lengths.sort(key=lambda x: -x[1])
    print(f"\n  COMPLEJIDAD (número de operaciones):")
    print(f"    Más compleja: {lengths[0][0]} ({lengths[0][1]} ops)")
    print(f"    Más simple:   {lengths[-1][0]} ({lengths[-1][1]} ops)")
    print(f"    Media:        {np.mean([l for _, l in lengths]):.1f} ops")

    # ISOMORFISMOS — fórmulas con la misma gramática
    print(f"\n{'='*70}")
    print("ISOMORFISMOS (fórmulas con la misma gramática)")
    print(f"{'='*70}")

    isos = detectar_isomorfismos()
    if isos:
        for seq, nombres in isos.items():
            ops_nombres = [list(OPS.keys())[list(OPS.values()).index(s)] for s in seq]
            print(f"\n  Gramática: {' → '.join(ops_nombres)}")
            for n in nombres:
                f = FORMULAS[n]
                print(f"    {n:<30s} ({f['rama']:<12s}) — {f['resultado']}")
    else:
        print("  Ninguno encontrado (todas las fórmulas tienen gramática única)")

    # Ejemplo de decodificación
    print(f"\n{'='*70}")
    print("EJEMPLO: Decodificación para LLM")
    print(f"{'='*70}")
    for nombre in ["varianza", "elasticidad_precio", "capm", "did", "prospect_value"]:
        print(f"\n{decodificar_formula(nombre)}")
