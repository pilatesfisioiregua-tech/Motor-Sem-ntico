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
    # ==========================================
    # G. EQUILIBRIO GENERAL Y BIENESTAR
    # ==========================================
    "exceso_demanda": {
        "formula": "z(p) = Σ x_i(p) - Σ ω_i",
        "ops": ["ACUMULAR", "ACUMULAR", "COMPARAR"],
        "lectura": "acumula todas las demandas, acumula todas las dotaciones, compara → cuánto sobra o falta en el mercado",
        "resultado": "adjetivo de desequilibrio de mercado",
        "rama": "micro",
    },
    "ley_walras": {
        "formula": "p·z(p) = 0",
        "ops": ["COMPONER", "ACUMULAR"],
        "lectura": "compone precio×exceso por cada bien, acumula → el valor total del exceso siempre es cero",
        "resultado": "identidad (restricción del sistema)",
        "rama": "micro",
    },
    "bienestar_utilitarista": {
        "formula": "W = Σ u_i(x_i)",
        "ops": ["ACUMULAR"],
        "lectura": "acumula las utilidades de todos los individuos → bienestar total",
        "resultado": "sujeto (bienestar social agregado)",
        "rama": "micro",
    },
    "bienestar_rawls": {
        "formula": "W = min_i {u_i(x_i)}",
        "ops": ["SELECCIONAR"],
        "lectura": "selecciona la utilidad mínima → bienestar del peor individuo",
        "resultado": "sujeto (bienestar del más desfavorecido)",
        "rama": "micro",
    },
    "indice_atkinson": {
        "formula": "A = 1 - [Σ(y_i/ȳ)^(1-ε)/n]^(1/(1-ε))",
        "ops": ["NORMALIZAR", "TRANSFORMAR", "ACUMULAR", "NORMALIZAR", "TRANSFORMAR", "COMPARAR"],
        "lectura": "normaliza rentas por media, transforma por aversión ε, acumula, normaliza, transforma de vuelta, compara con 1 → desigualdad con preferencia ética explícita",
        "resultado": "adjetivo de desigualdad (con juicio de valor)",
        "rama": "micro",
    },
    "indice_theil": {
        "formula": "T = (1/n)Σ (y_i/ȳ)·ln(y_i/ȳ)",
        "ops": ["NORMALIZAR", "TRANSFORMAR", "COMPONER", "ACUMULAR", "NORMALIZAR"],
        "lectura": "normaliza rentas por media, transforma a log, compone ratio×log, acumula, normaliza → desigualdad descomponible por grupos",
        "resultado": "adjetivo de desigualdad descomponible",
        "rama": "micro",
    },

    # ==========================================
    # H. OPTIMIZACIÓN DINÁMICA
    # ==========================================
    "bellman": {
        "formula": "V(x) = max_a {r(x,a) + β·V(f(x,a))}",
        "ops": ["COMPONER", "ESCALAR", "ACUMULAR", "SELECCIONAR"],
        "lectura": "compone acción×estado, escala futuro por descuento, acumula presente+futuro, selecciona máximo → valor óptimo del estado",
        "resultado": "sujeto (valor fundamental de una situación)",
        "rama": "optimizacion",
    },
    "bellman_estocastica": {
        "formula": "V(x) = max_a {r(x,a) + β·E[V(x')|x,a]}",
        "ops": ["COMPONER", "ESCALAR", "CONDICIONAR", "ACUMULAR", "SELECCIONAR"],
        "lectura": "como Bellman pero condiciona el futuro a la incertidumbre → decisión óptima bajo riesgo",
        "resultado": "sujeto (valor fundamental bajo incertidumbre)",
        "rama": "optimizacion",
    },
    "lagrangiano": {
        "formula": "L = f(x) - Σ λ_j·g_j(x)",
        "ops": ["ESCALAR", "COMPARAR"],
        "lectura": "escala restricciones por precios sombra, compara con objetivo → función auxiliar para optimizar con restricciones",
        "resultado": "herramienta (transforma problema restringido en libre)",
        "rama": "optimizacion",
    },
    "kkt": {
        "formula": "∇f = Σλ∇g + Σμ∇h; μ≥0; μ·h(x)=0",
        "ops": ["DERIVAR", "ESCALAR", "COMPARAR", "CONDICIONAR"],
        "lectura": "deriva objetivo, escala restricciones por multiplicadores, compara gradientes, condiciona por complementariedad → óptimo con desigualdades",
        "resultado": "condición de óptimo (cuándo parar)",
        "rama": "optimizacion",
    },
    "hjb": {
        "formula": "ρV(x) = max_a {r(x,a) + V'(x)·f(x,a)}",
        "ops": ["DERIVAR", "COMPONER", "ACUMULAR", "SELECCIONAR", "ESCALAR"],
        "lectura": "Bellman en tiempo continuo: deriva valor, compone con dinámica, acumula flujo+cambio, selecciona óptimo, escala por impaciencia",
        "resultado": "sujeto (valor en tiempo continuo)",
        "rama": "optimizacion",
    },

    # ==========================================
    # I. PUNTO FIJO Y EXISTENCIA
    # ==========================================
    "punto_fijo_brouwer": {
        "formula": "f:K→K continua, K compacto convexo → ∃x*: f(x*)=x*",
        "ops": ["CONDICIONAR", "SELECCIONAR"],
        "lectura": "condiciona por propiedades del espacio, selecciona punto donde la función se reproduce a sí misma → existencia de equilibrio",
        "resultado": "existencia (garantía de que el equilibrio existe)",
        "rama": "matematica",
    },
    "contraccion_banach": {
        "formula": "T contracción → ∃! x*=T(x*), T^n(x_0)→x*",
        "ops": ["COMPARAR", "TRANSFORMAR", "SELECCIONAR"],
        "lectura": "compara iteraciones sucesivas (se acercan), transforma por contracción, selecciona punto fijo → existencia + unicidad + convergencia",
        "resultado": "existencia + unicidad + algoritmo",
        "rama": "matematica",
    },

    # ==========================================
    # J. ECONOMETRÍA AVANZADA
    # ==========================================
    "control_sintetico": {
        "formula": "Ŷ₁ = Σ w_j·Y_j, w* = argmin ||X₁-X₀w||",
        "ops": ["ESCALAR", "ACUMULAR", "COMPARAR", "SELECCIONAR"],
        "lectura": "escala controles por pesos óptimos, acumula → contrafactual sintético, compara con tratado → efecto causal",
        "resultado": "adjetivo de efecto causal (contrafactual construido)",
        "rama": "econometria",
    },
    "doubly_robust": {
        "formula": "τ̂ = (1/n)Σ[m̂₁(x)-m̂₀(x) + D(Y-m̂₁)/ê - (1-D)(Y-m̂₀)/(1-ê)]",
        "ops": ["COMPARAR", "NORMALIZAR", "COMPARAR", "NORMALIZAR", "ACUMULAR", "NORMALIZAR"],
        "lectura": "compara outcomes estimados, normaliza por propensity score, acumula correcciones → efecto causal robusto a errores en un modelo",
        "resultado": "adjetivo de efecto causal (doblemente robusto)",
        "rama": "econometria",
    },
    "kalman": {
        "formula": "x̂ = x̂_pred + K·(y - H·x̂_pred); K = PH'(HPH'+R)⁻¹",
        "ops": ["COMPONER", "COMPARAR", "COMPONER", "INVERTIR", "ESCALAR", "ACUMULAR"],
        "lectura": "compone predicción×modelo, compara con observación (innovación), compone incertidumbres, invierte para ponderar, escala corrección → estimación óptima de estado oculto",
        "resultado": "sujeto (mejor estimación del estado real)",
        "rama": "econometria",
    },
    "garch": {
        "formula": "σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}",
        "ops": ["TRANSFORMAR", "ESCALAR", "ESCALAR", "ACUMULAR"],
        "lectura": "transforma error al cuadrado, escala por reacción α, escala persistencia por β, acumula con base ω → volatilidad que se alimenta de sí misma",
        "resultado": "adjetivo de volatilidad auto-alimentada",
        "rama": "econometria",
    },

    # ==========================================
    # K. FINANZAS AVANZADAS
    # ==========================================
    "sdf": {
        "formula": "p = E[m·x], m = β·u'(c₁)/u'(c₀)",
        "ops": ["DERIVAR", "DERIVAR", "NORMALIZAR", "ESCALAR", "COMPONER", "CONDICIONAR", "ACUMULAR"],
        "lectura": "deriva utilidad hoy y mañana, normaliza (ratio), escala por descuento, compone con pago, condiciona por información, acumula → precio de cualquier activo",
        "resultado": "sujeto universal (precio de TODO activo financiero)",
        "rama": "finanzas",
    },
    "modigliani_miller": {
        "formula": "V_L = V_U (sin fricciones)",
        "ops": ["COMPARAR"],
        "lectura": "compara valor apalancado con no apalancado → la estructura de capital no importa",
        "resultado": "identidad (irrelevancia)",
        "rama": "finanzas",
    },
    "ito_lemma": {
        "formula": "df = (∂f/∂t + μS·∂f/∂S + ½σ²S²·∂²f/∂S²)dt + σS·∂f/∂S·dW",
        "ops": ["DERIVAR", "DERIVAR", "DERIVAR", "COMPONER", "TRANSFORMAR", "COMPONER", "ACUMULAR"],
        "lectura": "deriva por tiempo, deriva por precio (1ª y 2ª orden), compone con drift y difusión, transforma cuadrático, acumula → cómo cambia cualquier función de un activo aleatorio",
        "resultado": "herramienta universal (cadena de regla estocástica)",
        "rama": "finanzas",
    },
    "frontera_eficiente": {
        "formula": "min w'Σw s.a. w'μ=μ̄, w'1=1",
        "ops": ["COMPONER", "CONDICIONAR", "SELECCIONAR"],
        "lectura": "compone pesos×varianzas, condiciona por retorno objetivo, selecciona mínimo riesgo → portfolio óptimo",
        "resultado": "prescripción (cómo invertir dado un objetivo)",
        "rama": "finanzas",
    },

    # ==========================================
    # L. CONDUCTUAL AVANZADA
    # ==========================================
    "fehr_schmidt": {
        "formula": "U_i = x_i - α·Σmax(x_j-x_i,0)/(n-1) - β·Σmax(x_i-x_j,0)/(n-1)",
        "ops": ["COMPARAR", "ACOTAR", "ACUMULAR", "NORMALIZAR", "ESCALAR", "COMPARAR", "ACOTAR", "ACUMULAR", "NORMALIZAR", "ESCALAR", "COMPARAR"],
        "lectura": "compara con cada otro, acota a positivos (envidia), acumula, normaliza, escala por aversión; repite para culpa; compara con pago propio → utilidad que sufre por desigualdad",
        "resultado": "adjetivo de preferencia social (envidia + culpa)",
        "rama": "conductual",
    },
    "quantal_response": {
        "formula": "σ_i(s) = exp(λ·Eπ_i(s)) / Σ exp(λ·Eπ_i(s'))",
        "ops": ["ESCALAR", "TRANSFORMAR", "NORMALIZAR"],
        "lectura": "escala payoff por racionalidad λ, transforma a exponencial, normaliza (softmax) → equilibrio con errores",
        "resultado": "adjetivo de racionalidad limitada (λ→∞ = Nash, λ→0 = aleatorio)",
        "rama": "conductual",
    },

    # ==========================================
    # M. SERIES TEMPORALES
    # ==========================================
    "ar1": {
        "formula": "y_t = c + φ·y_{t-1} + ε_t",
        "ops": ["ESCALAR", "ACUMULAR"],
        "lectura": "escala valor anterior por persistencia φ, acumula con constante + shock → cuánto del pasado permanece en el presente",
        "resultado": "adjetivo de persistencia (φ→1 = permanente, φ→0 = transitorio)",
        "rama": "econometria",
    },
    "var": {
        "formula": "Y_t = c + A₁Y_{t-1} + ... + A_pY_{t-p} + ε_t",
        "ops": ["COMPONER", "ACUMULAR"],
        "lectura": "compone vectores pasados por matrices de impacto, acumula → sistema completo de interdependencias temporales",
        "resultado": "sistema (cómo todo afecta a todo en el tiempo)",
        "rama": "econometria",
    },
    "cointegracion": {
        "formula": "β'Y_t ~ I(0) aunque Y_t ~ I(1)",
        "ops": ["COMPONER", "TRANSFORMAR", "COMPARAR"],
        "lectura": "compone variables no estacionarias por vector β, transforma → resultado estacionario, compara con I(0) → relación de largo plazo entre variables que deambulan",
        "resultado": "adjetivo de relación estable de largo plazo",
        "rama": "econometria",
    },
    "impulso_respuesta": {
        "formula": "IRF: Y_{t+h} = Σ Ψ_s·ε_{t+h-s}",
        "ops": ["COMPONER", "ACUMULAR"],
        "lectura": "compone shocks pasados por matrices de respuesta, acumula → efecto dinámico completo de un shock",
        "resultado": "narrativa (cómo se propaga un shock en el tiempo)",
        "rama": "econometria",
    },

    # ==========================================
    # N. MACRO AVANZADA
    # ==========================================
    "nkpc": {
        "formula": "π_t = β·E_t[π_{t+1}] + κ·x_t",
        "ops": ["CONDICIONAR", "ESCALAR", "ESCALAR", "ACUMULAR"],
        "lectura": "condiciona inflación futura por información actual, escala por descuento, escala output gap por pendiente, acumula → inflación como expectativas + presión real",
        "resultado": "adjetivo de presión inflacionaria (expectativas + gap)",
        "rama": "macro",
    },
    "is_nk": {
        "formula": "x_t = E_t[x_{t+1}] - (1/σ)(i_t - E_t[π_{t+1}] - r^n)",
        "ops": ["CONDICIONAR", "COMPARAR", "INVERTIR", "ESCALAR", "COMPARAR"],
        "lectura": "condiciona futuro, compara tipo de interés con natural, invierte elasticidad, escala → output gap como función del tipo real vs natural",
        "resultado": "adjetivo de posición cíclica",
        "rama": "macro",
    },
    "calvo_pricing": {
        "formula": "p* = (1-βθ)Σ(βθ)^k E_t[mc_{t+k}]",
        "ops": ["CONDICIONAR", "ESCALAR", "TRANSFORMAR", "ACUMULAR"],
        "lectura": "condiciona costes futuros, escala por descuento×rigidez, transforma a serie geométrica, acumula → precio óptimo mirando al futuro",
        "resultado": "sujeto (precio que fijaría si pudiera cambiar)",
        "rama": "macro",
    },
    "dyn_deuda": {
        "formula": "ΔB/Y = (r-g)·B/Y - pb",
        "ops": ["COMPARAR", "COMPONER", "COMPARAR"],
        "lectura": "compara tipo de interés con crecimiento, compone con ratio deuda, compara con superávit primario → si la deuda crece o se reduce",
        "resultado": "adjetivo de sostenibilidad fiscal (r>g = diverge, r<g = converge)",
        "rama": "macro",
    },
    "ramsey_euler": {
        "formula": "ċ/c = (1/σ)[f'(k) - δ - ρ]",
        "ops": ["DERIVAR", "COMPARAR", "COMPARAR", "INVERTIR", "COMPONER"],
        "lectura": "deriva utilidad, compara productividad marginal con depreciación+impaciencia, invierte aversión al riesgo, compone → velocidad óptima de cambio del consumo",
        "resultado": "prescripción (cuánto debe crecer el consumo)",
        "rama": "macro",
    },
    "hodrick_prescott": {
        "formula": "min Σ(y_t-τ_t)² + λΣ[(τ_{t+1}-τ_t)-(τ_t-τ_{t-1})]²",
        "ops": ["COMPARAR", "TRANSFORMAR", "ACUMULAR", "COMPARAR", "COMPARAR", "TRANSFORMAR", "ACUMULAR", "ESCALAR", "ACUMULAR", "SELECCIONAR"],
        "lectura": "compara dato con tendencia (ajuste), transforma al cuadrado, acumula; compara cambios de tendencia (suavidad), transforma, acumula, escala por λ; suma ambos, selecciona mínimo → separa tendencia de ciclo",
        "resultado": "descomposición (trend + cycle)",
        "rama": "macro",
    },

    # ==========================================
    # O. PROBABILIDAD Y CONVERGENCIA
    # ==========================================
    "lln": {
        "formula": "X̄_n → E[X] (p o a.s.)",
        "ops": ["ACUMULAR", "NORMALIZAR", "COMPARAR"],
        "lectura": "acumula observaciones, normaliza por n, compara con esperanza → la media muestral converge a la real",
        "resultado": "garantía (los datos eventualmente revelan la verdad)",
        "rama": "matematica",
    },
    "tcl": {
        "formula": "√n(X̄-μ)/σ →d N(0,1)",
        "ops": ["ACUMULAR", "NORMALIZAR", "COMPARAR", "NORMALIZAR", "TRANSFORMAR"],
        "lectura": "acumula, normaliza (media), compara con esperanza, normaliza por desviación, transforma por √n → la distribución de la media es normal",
        "resultado": "garantía (la incertidumbre se puede cuantificar)",
        "rama": "matematica",
    },
    "jensen": {
        "formula": "E[g(X)] ≥ g(E[X]) si g convexa",
        "ops": ["TRANSFORMAR", "CONDICIONAR", "COMPARAR"],
        "lectura": "transforma por función convexa, condiciona por convexidad, compara esperanza de transformada con transformada de esperanza → la desigualdad fundamental de la aversión al riesgo",
        "resultado": "restricción (por qué los aversos al riesgo pagan prima)",
        "rama": "matematica",
    },

    # ==========================================
    # P. SUBASTAS Y MECANISMOS
    # ==========================================
    "vickrey": {
        "formula": "b(v) = v (estrategia dominante)",
        "ops": [],
        "lectura": "pujas tu valor real — ninguna operación, la verdad es óptima",
        "resultado": "identidad (la verdad es la estrategia óptima)",
        "rama": "micro",
    },
    "myerson_subasta": {
        "formula": "ψ(v) = v - (1-F(v))/f(v)",
        "ops": ["NORMALIZAR", "INVERTIR", "COMPARAR"],
        "lectura": "normaliza la distribución (hazard rate), invierte, compara con valor real → valor virtual (lo que realmente vale extraer del comprador)",
        "resultado": "sujeto (valor virtual — la verdad económica detrás del valor reportado)",
        "rama": "micro",
    },
    "vcg": {
        "formula": "t_i = Σ_{j≠i} v_j(q*) - Σ_{j≠i} v_j(q*_{-i})",
        "ops": ["ACUMULAR", "ACUMULAR", "COMPARAR"],
        "lectura": "acumula valor de los demás con i, acumula sin i, compara → cuánto cambia el bienestar de otros por la presencia de i",
        "resultado": "adjetivo de externalidad (cuánto afectas a los demás)",
        "rama": "micro",
    },

    # ==========================================
    # Q. MICRO: Consumidor avanzado (del catálogo 288)
    # ==========================================
    "utilidad_indirecta": {
        "formula": "v(p,w) = max_{p·x≤w} u(x)",
        "ops": ["CONDICIONAR", "SELECCIONAR"],
        "lectura": "condiciona por presupuesto, selecciona máximo → máxima satisfacción posible",
        "resultado": "sujeto (techo de bienestar dada la restricción)",
        "rama": "micro",
    },
    "identidad_roy": {
        "formula": "x_i = -(∂v/∂p_i)/(∂v/∂w)",
        "ops": ["DERIVAR", "DERIVAR", "NORMALIZAR", "TRANSFORMAR"],
        "lectura": "deriva utilidad indirecta por precio y por renta, divide, invierte signo → demanda desde arriba",
        "resultado": "herramienta (demanda sin resolver el problema del consumidor)",
        "rama": "micro",
    },
    "funcion_gasto": {
        "formula": "e(p,ū) = min_{u(x)≥ū} p·x",
        "ops": ["CONDICIONAR", "COMPONER", "SELECCIONAR"],
        "lectura": "condiciona por utilidad mínima, compone precio×cantidad, selecciona mínimo → cuánto cuesta ser feliz",
        "resultado": "sujeto (coste de la felicidad)",
        "rama": "micro",
    },
    "slutsky": {
        "formula": "∂x/∂p = ∂h/∂p - x·∂x/∂w",
        "ops": ["DERIVAR", "DERIVAR", "COMPONER", "COMPARAR"],
        "lectura": "deriva efecto sustitución, deriva efecto renta, compone cantidad×renta, compara → descompone por qué cambias lo que compras",
        "resultado": "descomposición (sustitución + renta)",
        "rama": "micro",
    },
    "aversion_riesgo_arrow_pratt": {
        "formula": "r_A(x) = -u''(x)/u'(x)",
        "ops": ["DERIVAR", "DERIVAR", "NORMALIZAR", "TRANSFORMAR"],
        "lectura": "deriva 2x la utilidad, normaliza por la primera derivada, invierte signo → cuánto te disgusta el riesgo",
        "resultado": "adjetivo de personalidad frente al riesgo",
        "rama": "micro",
    },
    "prima_riesgo_arrowpratt": {
        "formula": "π ≈ ½·r_A·Var(x)",
        "ops": ["COMPONER", "ESCALAR"],
        "lectura": "compone aversión×varianza, escala por ½ → cuánto pagas para NO tener incertidumbre",
        "resultado": "adjetivo de coste del miedo",
        "rama": "micro",
    },
    "equivalente_cierto": {
        "formula": "CE: u(CE) = E[u(x)]",
        "ops": ["CONDICIONAR", "ACUMULAR", "INVERTIR"],
        "lectura": "condiciona por incertidumbre, acumula utilidades esperadas, invierte la función → riqueza segura equivalente a la lotería",
        "resultado": "sujeto (cuánto vale la certeza)",
        "rama": "micro",
    },
    "dominancia_estocastica_1": {
        "formula": "F ≥_FSD G ⟺ F(x) ≤ G(x) ∀x",
        "ops": ["COMPARAR"],
        "lectura": "compara distribuciones punto a punto → F da más probabilidad a resultados buenos",
        "resultado": "ordenamiento (esta opción domina a la otra para todos)",
        "rama": "micro",
    },
    "agregacion_engel": {
        "formula": "Σ s_i·ε_wi = 1",
        "ops": ["COMPONER", "ACUMULAR"],
        "lectura": "compone participación×elasticidad-renta por bien, acumula → la suma ponderada siempre es 1",
        "resultado": "identidad (restricción contable del consumidor)",
        "rama": "micro",
    },

    # ==========================================
    # R. MICRO: Productor avanzado
    # ==========================================
    "funcion_coste": {
        "formula": "C(w,y) = min_{f(x)≥y} w·x",
        "ops": ["CONDICIONAR", "COMPONER", "SELECCIONAR"],
        "lectura": "condiciona por output mínimo, compone precio×input, selecciona mínimo → coste de producir",
        "resultado": "sujeto (precio de crear)",
        "rama": "micro",
    },
    "lema_shephard": {
        "formula": "x_i*(w,y) = ∂C/∂w_i",
        "ops": ["DERIVAR"],
        "lectura": "deriva coste respecto al precio del input → cuánto usas de cada input",
        "resultado": "adjetivo de intensidad de uso del input",
        "rama": "micro",
    },
    "hotelling": {
        "formula": "y* = ∂π/∂p",
        "ops": ["DERIVAR"],
        "lectura": "deriva beneficio respecto al precio → cuánto produces",
        "resultado": "adjetivo de respuesta al precio",
        "rama": "micro",
    },
    "ces": {
        "formula": "f = A[δK^ρ + (1-δ)L^ρ]^{1/ρ}",
        "ops": ["TRANSFORMAR", "ESCALAR", "ACUMULAR", "TRANSFORMAR", "ESCALAR"],
        "lectura": "transforma inputs por elasticidad ρ, escala por participación δ, acumula, transforma de vuelta, escala por productividad → producción con sustituibilidad constante",
        "resultado": "sujeto (output con flexibilidad paramétrica)",
        "rama": "micro",
    },

    # ==========================================
    # S. EQUILIBRIO GENERAL avanzado
    # ==========================================
    "pareto_eficiencia": {
        "formula": "∄x' t.q. u_i(x'_i) ≥ u_i(x_i) ∀i con ≥1 estricta",
        "ops": ["COMPARAR", "CONDICIONAR"],
        "lectura": "compara todas las asignaciones posibles, condiciona por mejora sin empeoramiento → no se puede mejorar a nadie sin perjudicar a otro",
        "resultado": "test de eficiencia (¿es óptimo?)",
        "rama": "micro",
    },
    "precios_arrow_debreu": {
        "formula": "q(s) = β·π(s)·u'(c₁(s))/u'(c₀)",
        "ops": ["DERIVAR", "DERIVAR", "NORMALIZAR", "ESCALAR", "COMPONER"],
        "lectura": "deriva utilidades en dos estados, normaliza, escala por descuento, compone con probabilidad → precio de un seguro por estado del mundo",
        "resultado": "sujeto (precio del miedo a cada escenario)",
        "rama": "micro",
    },

    # ==========================================
    # T. JUEGOS avanzados
    # ==========================================
    "equilibrio_bayesiano": {
        "formula": "σ_i*(θ_i) : E_{θ-i|θi}[u_i(σ*)] ≥ E[u_i(s_i,σ*_{-i})]",
        "ops": ["CONDICIONAR", "ACUMULAR", "COMPARAR", "SELECCIONAR"],
        "lectura": "condiciona por información privada, acumula utilidad esperada, compara estrategias, selecciona la mejor → jugar óptimo con información incompleta",
        "resultado": "prescripción bajo incertidumbre",
        "rama": "micro",
    },
    "cournot": {
        "formula": "q_i* = (a-c_i-q_{-i})/(2b)",
        "ops": ["COMPARAR", "COMPARAR", "NORMALIZAR"],
        "lectura": "compara demanda con coste, compara con producción rival, normaliza → cuánto producir contra el competidor",
        "resultado": "prescripción de cantidad (oligopolio)",
        "rama": "micro",
    },
    "bertrand": {
        "formula": "p* = c",
        "ops": ["COMPARAR"],
        "lectura": "compara precio con coste → la competencia en precios lleva al coste marginal",
        "resultado": "identidad (competencia perfecta en precios)",
        "rama": "micro",
    },
    "stackelberg": {
        "formula": "q_1* = argmax q_1·P(q_1+BR_2(q_1))-C_1",
        "ops": ["COMPONER", "CONDICIONAR", "SELECCIONAR"],
        "lectura": "compone precio×cantidad, condiciona por reacción del seguidor, selecciona máximo → ventaja del primero en mover",
        "resultado": "prescripción con compromiso (liderazgo)",
        "rama": "micro",
    },
    "folk_theorem": {
        "formula": "Todo pago factible+IR es SPE para δ suficientemente alto",
        "ops": ["COMPARAR", "CONDICIONAR"],
        "lectura": "compara payoff con punto de amenaza, condiciona por paciencia → la cooperación emerge si el futuro importa",
        "resultado": "condición (cuándo la cooperación es sostenible)",
        "rama": "micro",
    },

    # ==========================================
    # U. INFORMACIÓN Y MECANISMOS
    # ==========================================
    "incentive_compatibility": {
        "formula": "U(θ,θ) ≥ U(θ,θ̂) ∀θ,θ̂",
        "ops": ["COMPARAR", "CONDICIONAR"],
        "lectura": "compara utilidad de decir verdad vs mentir, condiciona por todo tipo → la verdad es óptima",
        "resultado": "restricción (cuándo conviene ser honesto)",
        "rama": "micro",
    },
    "envelope_theorem": {
        "formula": "dU*/dθ = ∂v(q*(θ),θ)/∂θ",
        "ops": ["DERIVAR", "CONDICIONAR"],
        "lectura": "deriva utilidad óptima respecto al tipo, condicionado a decisión óptima → cómo cambia el valor cuando cambias quién eres",
        "resultado": "adjetivo de sensibilidad del valor al tipo",
        "rama": "micro",
    },
    "moral_hazard": {
        "formula": "max E[x-w(x)] s.a. IC + IR",
        "ops": ["CONDICIONAR", "CONDICIONAR", "SELECCIONAR"],
        "lectura": "condiciona por incentivos del agente, condiciona por participación, selecciona contrato → diseñar incentivos cuando no ves lo que hace el otro",
        "resultado": "prescripción (contrato óptimo bajo acción oculta)",
        "rama": "micro",
    },
    "señalizacion_spence": {
        "formula": "e*(θ_H) > e*(θ_L) t.q. w(e)-c(e,θ) satisface IC",
        "ops": ["COMPARAR", "CONDICIONAR", "SELECCIONAR"],
        "lectura": "compara señales por tipo, condiciona por incentivos, selecciona separador → los buenos se distinguen invirtiendo más en señal",
        "resultado": "mecanismo (cómo demuestras lo que vales)",
        "rama": "micro",
    },
    "myerson_satterthwaite": {
        "formula": "No ∃ mecanismo IC+IR+eficiente+BB con tipos continuos",
        "ops": [],
        "lectura": "imposibilidad — no puedes tener incentivos, participación, eficiencia y presupuesto equilibrado a la vez",
        "resultado": "imposibilidad (el mercado perfecto no existe bajo asimetría)",
        "rama": "micro",
    },

    # ==========================================
    # V. MACRO: Crecimiento avanzado
    # ==========================================
    "romer_variedades": {
        "formula": "Y = L^(1-α)∫₀^A x(i)^α di; Ȧ = δ·L_A·A",
        "ops": ["TRANSFORMAR", "INTEGRAR", "COMPONER", "DERIVAR", "COMPONER"],
        "lectura": "transforma por elasticidad, integra sobre variedades, compone trabajo×capital; la innovación es más gente investigando × más conocimiento",
        "resultado": "sistema (crecimiento por crear cosas nuevas)",
        "rama": "macro",
    },
    "schumpeter_destruccion_creativa": {
        "formula": "V = π/(r+φ) donde φ = tasa destrucción",
        "ops": ["NORMALIZAR", "ACUMULAR", "INVERTIR"],
        "lectura": "normaliza beneficio del monopolio temporal, acumula con riesgo de destrucción, invierte → valor de innovar sabiendo que te reemplazarán",
        "resultado": "sujeto (precio de la innovación con fecha de caducidad)",
        "rama": "macro",
    },
    "mankiw_romer_weil": {
        "formula": "ln(Y/L) = const + [α/(1-α)]ln(s_K) + [β/(1-α)]ln(s_H) - [(α+β)/(1-α)]ln(n+g+δ)",
        "ops": ["TRANSFORMAR", "ESCALAR", "ACUMULAR"],
        "lectura": "transforma a logaritmos, escala por elasticidades, acumula → renta per cápita explicada por ahorro físico, humano y crecimiento poblacional",
        "resultado": "descomposición (por qué unos países son ricos y otros pobres)",
        "rama": "macro",
    },
    "contabilidad_crecimiento": {
        "formula": "ΔA/A = ΔY/Y - α·ΔK/K - (1-α)·ΔL/L",
        "ops": ["COMPARAR", "ESCALAR", "COMPARAR", "ESCALAR", "COMPARAR"],
        "lectura": "compara crecimiento del output con contribución ponderada de capital y trabajo → lo que sobra es productividad",
        "resultado": "residuo (la medida de nuestra ignorancia — Solow)",
        "rama": "macro",
    },
    "transversalidad": {
        "formula": "lim_{t→∞} β^t·u'(c_t)·k_t = 0",
        "ops": ["ESCALAR", "DERIVAR", "COMPONER", "SELECCIONAR"],
        "lectura": "escala por descuento, deriva utilidad marginal, compone con capital, selecciona límite → no acumules para siempre ni te arruines",
        "resultado": "restricción (la vida es finita — no mueras rico ni pobre)",
        "rama": "macro",
    },

    # ==========================================
    # W. MACRO: Ciclos NK avanzados
    # ==========================================
    "blanchard_kahn": {
        "formula": "condición: #eigenvalues>1 = #variables forward",
        "ops": ["TRANSFORMAR", "COMPARAR"],
        "lectura": "transforma sistema a eigenvalores, compara número de inestables con variables forward → ¿el modelo tiene solución única?",
        "resultado": "test de determinación (¿este modelo está bien definido?)",
        "rama": "macro",
    },
    "perdida_banco_central": {
        "formula": "L = E Σ β^t [(π-π*)² + λ·x²]",
        "ops": ["COMPARAR", "TRANSFORMAR", "COMPARAR", "TRANSFORMAR", "ESCALAR", "ACUMULAR", "ESCALAR", "CONDICIONAR"],
        "lectura": "compara inflación con objetivo (al cuadrado), compara output gap (al cuadrado), escala por preferencia λ, acumula en el tiempo, escala por descuento → cuánto sufre el banco central",
        "resultado": "sujeto (dolor del banquero central)",
        "rama": "macro",
    },
    "inconsistencia_temporal": {
        "formula": "π^e = π* + λκ/α > π* (sesgo inflacionario)",
        "ops": ["COMPARAR", "NORMALIZAR", "ACUMULAR"],
        "lectura": "compara equilibrio con objetivo, normaliza por parámetros, acumula sesgo → sin compromiso creíble, siempre hay más inflación de la deseada",
        "resultado": "adjetivo de credibilidad (cuánto vale tu palabra)",
        "rama": "macro",
    },

    # ==========================================
    # X. ECONOMETRÍA avanzada
    # ==========================================
    "gauss_markov": {
        "formula": "β̂_OLS es BLUE bajo E[ε|X]=0, Var(ε|X)=σ²I",
        "ops": ["CONDICIONAR", "COMPARAR"],
        "lectura": "condiciona por supuestos clásicos, compara con todo estimador lineal insesgado → OLS es el mejor (bajo esos supuestos)",
        "resultado": "garantía (OLS gana si el mundo es como asumes)",
        "rama": "econometria",
    },
    "varianza_robusta_white": {
        "formula": "V̂ = (X'X)⁻¹(Σ ê²xᵢxᵢ')(X'X)⁻¹",
        "ops": ["COMPONER", "INVERTIR", "TRANSFORMAR", "COMPONER", "COMPONER", "INVERTIR"],
        "lectura": "invierte la varianza de X, transforma residuos al cuadrado, compone sandwich → incertidumbre correcta aunque los errores sean irregulares",
        "resultado": "herramienta (errores estándar que no mienten)",
        "rama": "econometria",
    },
    "lr_test": {
        "formula": "LR = 2[ℓ(θ̂_u) - ℓ(θ̂_r)]",
        "ops": ["COMPARAR", "ESCALAR"],
        "lectura": "compara verosimilitud del modelo libre vs restringido, escala por 2 → ¿las restricciones duelen?",
        "resultado": "test (¿la simplificación pierde información?)",
        "rama": "econometria",
    },
    "wald_test": {
        "formula": "W = (Rθ̂-r)'[RVR']⁻¹(Rθ̂-r)",
        "ops": ["COMPARAR", "COMPONER", "INVERTIR", "COMPONER"],
        "lectura": "compara estimaciones con restricción, compone con varianza invertida → distancia cuadrática a la hipótesis",
        "resultado": "test (cuán lejos estás de lo que asumes)",
        "rama": "econometria",
    },
    "aic": {
        "formula": "AIC = -2ℓ(θ̂) + 2k",
        "ops": ["TRANSFORMAR", "ESCALAR", "ACUMULAR"],
        "lectura": "transforma verosimilitud (×-2), escala parámetros (×2), acumula → calidad penalizada por complejidad",
        "resultado": "score (cuánto vale tu modelo descontando cuánto le cuesta)",
        "rama": "econometria",
    },
    "probit": {
        "formula": "P(y=1|x) = Φ(x'β)",
        "ops": ["COMPONER", "TRANSFORMAR"],
        "lectura": "compone variables×coeficientes, transforma por función normal acumulada → probabilidad de que ocurra",
        "resultado": "adjetivo de probabilidad (cuán probable es el evento)",
        "rama": "econometria",
    },
    "logit": {
        "formula": "P(y=1|x) = exp(x'β)/(1+exp(x'β))",
        "ops": ["COMPONER", "TRANSFORMAR", "NORMALIZAR"],
        "lectura": "compone variables×coeficientes, transforma a exponencial, normaliza → probabilidad logística",
        "resultado": "adjetivo de probabilidad (versión logística)",
        "rama": "econometria",
    },
    "tobit": {
        "formula": "y* = x'β+ε; y = max(0,y*)",
        "ops": ["COMPONER", "ACOTAR"],
        "lectura": "compone variables×coeficientes, acota por cero → estimar cuando los datos están censurados",
        "resultado": "herramienta (ver lo que está detrás del cero)",
        "rama": "econometria",
    },
    "bootstrap": {
        "formula": "θ̂* = g(X₁*,...,Xₙ*) remuestreando con reemplazo",
        "ops": ["TRANSFORMAR", "ACUMULAR", "NORMALIZAR"],
        "lectura": "transforma por remuestreo aleatorio, acumula estadísticos, normaliza → incertidumbre sin supuestos distribucionales",
        "resultado": "herramienta (medir error sin asumir nada)",
        "rama": "econometria",
    },
    "kaplan_meier": {
        "formula": "Ŝ(t) = Π (1-d_i/n_i)",
        "ops": ["NORMALIZAR", "COMPONER"],
        "lectura": "normaliza eventos por expuestos, compone probabilidades de supervivencia → probabilidad de seguir vivo/activo",
        "resultado": "adjetivo de supervivencia",
        "rama": "econometria",
    },

    # ==========================================
    # Y. PROBABILIDAD Y CONVERGENCIA avanzada
    # ==========================================
    "chebyshev": {
        "formula": "P(|X-μ| ≥ kσ) ≤ 1/k²",
        "ops": ["COMPARAR", "NORMALIZAR", "TRANSFORMAR", "INVERTIR"],
        "lectura": "compara con media, normaliza por desviación, transforma al cuadrado, invierte → cota universal de cuán raro es un evento",
        "resultado": "cota (lo peor que puede pasar sin asumir nada)",
        "rama": "matematica",
    },
    "delta_method": {
        "formula": "√n(g(θ̂)-g(θ)) →d N(0, g'V g')",
        "ops": ["DERIVAR", "COMPONER", "TRANSFORMAR"],
        "lectura": "deriva la función, compone con varianza del estimador, transforma → incertidumbre de funciones de estimadores",
        "resultado": "herramienta (propagar incertidumbre a través de funciones)",
        "rama": "matematica",
    },
    "radon_nikodym": {
        "formula": "dQ/dP = f → Q(A) = ∫_A f dP",
        "ops": ["NORMALIZAR", "INTEGRAR"],
        "lectura": "normaliza una medida por otra, integra → cambiar de perspectiva probabilística",
        "resultado": "herramienta universal (ver el mundo desde otra distribución)",
        "rama": "matematica",
    },
    "girsanov": {
        "formula": "dQ/dP = exp(-∫θdW - ½∫θ²dt)",
        "ops": ["COMPONER", "INTEGRAR", "TRANSFORMAR", "NORMALIZAR"],
        "lectura": "compone drift×browniano, integra, transforma a exponencial, normaliza → cambiar drift preservando estructura estocástica",
        "resultado": "herramienta (pricing neutral al riesgo — la base de toda finanza moderna)",
        "rama": "matematica",
    },
    "martingala": {
        "formula": "E[X_{t+1}|F_t] = X_t",
        "ops": ["CONDICIONAR", "COMPARAR"],
        "lectura": "condiciona por información actual, compara esperanza futura con presente → sin tendencia predecible",
        "resultado": "propiedad (el futuro es justo dado lo que sabes)",
        "rama": "matematica",
    },

    # ==========================================
    # Z. CONDUCTUAL avanzada
    # ==========================================
    "quasi_hiperbolic": {
        "formula": "U₀ = u₀ + β·Σδ^t·u_t (β<1)",
        "ops": ["ESCALAR", "ESCALAR", "TRANSFORMAR", "ACUMULAR"],
        "lectura": "escala presente por 1, escala futuro por β<1 (penalización), transforma por descuento δ^t, acumula → presente vale desproporcionadamente más",
        "resultado": "adjetivo de sesgo presente (la procrastinación modelada)",
        "rama": "conductual",
    },
    "aversion_inequidad_fehr_schmidt_simple": {
        "formula": "U = x_i - α·max(x_j-x_i,0) - β·max(x_i-x_j,0)",
        "ops": ["COMPARAR", "ACOTAR", "ESCALAR", "COMPARAR", "ACOTAR", "ESCALAR", "COMPARAR"],
        "lectura": "compara con otros (envidia si menos, culpa si más), acota a positivo, escala por intensidad → utilidad que sufre por desigualdad",
        "resultado": "adjetivo de justicia percibida",
        "rama": "conductual",
    },
    "referencia_dependiente_koszegi_rabin": {
        "formula": "U(c|r) = m(c) + μ(m(c)-m(r))",
        "ops": ["COMPARAR", "TRANSFORMAR", "ACUMULAR"],
        "lectura": "compara consumo real con expectativa (referencia), transforma la diferencia por aversión a pérdida, acumula → cuánto duele no cumplir tus expectativas",
        "resultado": "adjetivo de decepción/satisfacción relativa",
        "rama": "conductual",
    },
    "maxmin_ambiguedad": {
        "formula": "V(f) = min_{P∈C} E_P[u(f)]",
        "ops": ["CONDICIONAR", "ACUMULAR", "SELECCIONAR"],
        "lectura": "condiciona por múltiples distribuciones posibles, acumula utilidad esperada bajo cada una, selecciona la peor → decisión cuando no sabes ni las probabilidades",
        "resultado": "prescripción bajo ignorancia profunda",
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
