"""
Red de Preguntas Encadenadas — Cada respuesta desbloquea la siguiente pregunta.

Fecha: 2026-04-13

Arquitectura:
  1. Usuario pregunta algo
  2. Harness detecta finalidad → activa fórmulas Tier 1
  3. Simbionte calcula → obtiene valores + polos
  4. La RESPUESTA de cada fórmula determina qué preguntas se desbloquean
  5. Cascada: pregunta → respuesta → nueva pregunta → ...
  6. Verificación cruzada: ¿las respuestas estructurales (Simbionte)
     coinciden con las respuestas semánticas (LLM)?

Principio:
  varianza alta → desbloquea "¿dirección del riesgo?" (skewness)
  skewness negativa → desbloquea "¿cuánto puedo perder?" (VaR)

  Es un árbol de decisiones semántico donde cada nodo es una fórmula
  y cada arista es una condición sobre el resultado.

$0 total (definiciones estáticas + lógica)
"""

import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))

from semantica_formulas import SEMANTICA


# ============================================================
# ENLACES: qué pregunta desbloquea qué
# ============================================================
# Formato: "formula_origen" → [(condición, "formula_destino", razón)]
# Condición: "alto", "bajo", "extremo", "siempre"

ENLACES = {
    # === DIAGNÓSTICO INICIAL ===
    # La varianza es la puerta de entrada
    "varianza": [
        ("alto", "skewness", "disperso → ¿hacia dónde se inclina el riesgo?"),
        ("alto", "kurtosis", "disperso → ¿cuán probables son los extremos?"),
        ("alto", "gini", "disperso → ¿es desigualdad o heterogeneidad?"),
        ("bajo", "correlacion", "concentrado → ¿se mueven juntas las variables?"),
        ("bajo", "persistencia", "concentrado → ¿es estable o transitorio?"),
    ],

    "skewness": [
        ("bajo", "var_parametrico", "cola izquierda → ¿cuánto puedo perder?"),
        ("bajo", "marco_amplificacion", "cola izquierda → ¿hay espiral descendente?"),
        ("alto", "elasticidad_general", "cola derecha → ¿cuán sensible es al upside?"),
    ],

    "kurtosis": [
        ("alto", "var_parametrico", "colas pesadas → cuantificar el riesgo extremo"),
        ("alto", "garch", "colas pesadas → ¿la volatilidad se autoalimenta?"),
    ],

    "gini": [
        ("alto", "hhi", "desigualdad alta → ¿está concentrado en pocos?"),
        ("alto", "marco_n_agentes", "desigualdad alta → ¿cuántos jugadores dominan?"),
    ],

    # === RELACIONES ===
    "correlacion": [
        ("alto", "elasticidad_general", "co-movimiento fuerte → ¿cuán sensible?"),
        ("alto", "marco_cruce", "co-movimiento → ¿hay equilibrio de Nash?"),
        ("bajo", "marco_n_componentes", "independientes → ¿el sistema está fragmentado?"),
        ("siempre", "persistencia", "toda correlación → ¿es estable en el tiempo?"),
    ],

    "elasticidad_general": [
        ("alto", "curva_phillips", "hipersensible → ¿trade-off inflación/empleo?"),
        ("bajo", "regla_taylor", "insensible → ¿la política monetaria funciona?"),
    ],

    "persistencia": [
        ("alto", "marco_diagonal", "persistente → ¿cuánta inercia secuencial?"),
        ("alto", "dyn_deuda", "persistente → ¿es sostenible a largo plazo?"),
        ("bajo", "marco_vel_media", "transitorio → ¿a qué velocidad se disipa?"),
    ],

    # === GAPS Y DESEQUILIBRIOS ===
    "output_gap": [
        ("alto", "curva_phillips", "sobre potencial → ¿cuánta presión inflacionaria?"),
        ("alto", "regla_taylor", "sobre potencial → ¿qué tipo de interés?"),
        ("bajo", "multiplicador_fiscal", "bajo potencial → ¿cuánto efecto tiene el estímulo?"),
        ("bajo", "marco_agujeros", "bajo potencial → ¿qué falta?"),
    ],

    "gap": [
        ("alto", "marco_curvatura_media", "sobre tendencia → ¿está cambiando de dirección?"),
        ("bajo", "marco_desplazamiento", "bajo tendencia → ¿cuánto se ha movido del inicio?"),
    ],

    # === CICLOS Y DINÁMICA ===
    "curva_phillips": [
        ("alto", "regla_taylor", "presión inflacionaria → ¿qué hacer con los tipos?"),
        ("bajo", "multiplicador_fiscal", "sin presión → margen para estímulo fiscal"),
    ],

    "regla_taylor": [
        ("alto", "ecuacion_fisher", "tipos altos → ¿cuál es el tipo real?"),
        ("siempre", "dyn_deuda", "cualquier tipo → ¿es sostenible la deuda?"),
    ],

    "multiplicador_fiscal": [
        ("alto", "deuda_pib", "multiplicador alto → ¿hay margen fiscal?"),
        ("bajo", "marco_ratio_feedback", "multiplicador bajo → ¿hay leakage/feedback?"),
    ],

    # === RIESGO ===
    "var_parametrico": [
        ("alto", "marco_amplificacion", "riesgo alto → ¿se autoamplifica?"),
        ("alto", "prospect_value", "riesgo alto → ¿cómo lo percibe la gente?"),
    ],

    "garch": [
        ("alto", "marco_n_ciclos", "volatilidad autoalimentada → ¿cuántos loops?"),
        ("alto", "marco_prof_ciclo", "autoalimentada → ¿cuán profundos los loops?"),
    ],

    # === MARCOS DEL SIMBIONTE ===
    "marco_amplificacion": [
        ("alto", "marco_regulacion", "espiral detectada → ¿hay freno?"),
        ("alto", "marco_coherencia_dir", "espiral → ¿en qué dirección va?"),
    ],

    "marco_regulacion": [
        ("bajo", "marco_ratio_feedback", "sin freno → ¿domina la amplificación?"),
    ],

    "marco_n_agentes": [
        ("alto", "marco_simetria_juego", "muchos agentes → ¿poder equilibrado?"),
        ("alto", "marco_alternancia", "muchos agentes → ¿hay tensión activa?"),
    ],

    "marco_simetria_juego": [
        ("bajo", "marco_cruce", "asimétrico → ¿hay Nash?"),
        ("alto", "marco_completitud", "simétrico → ¿se exploran todas las estrategias?"),
    ],

    "marco_cruce": [
        ("alto", "equilibrio_nash", "cruce detectado → buscar Nash"),
    ],

    "marco_emergencia": [
        ("alto", "marco_coherencia_sis", "emergencia → ¿las partes son coherentes?"),
    ],

    "marco_agujeros": [
        ("alto", "marco_persistencia_topo", "gaps → ¿son persistentes o temporales?"),
        ("alto", "marco_compacidad", "gaps → ¿está dispersa la estructura?"),
    ],

    "marco_curvatura_media": [
        ("alto", "marco_curvatura_max", "mucha curvatura → ¿hay giros bruscos?"),
        ("alto", "marco_torsion", "mucha curvatura → ¿el ritmo es constante?"),
    ],

    "marco_curvatura_max": [
        ("alto", "marco_ratio_inflexion", "giro brusco → ¿cuántos cambios de régimen?"),
    ],

    "marco_vel_media": [
        ("alto", "marco_aceleracion", "rápido → ¿se acelera o frena?"),
        ("alto", "marco_bruscos", "rápido → ¿hay shocks?"),
        ("bajo", "marco_desplazamiento", "lento → ¿se movió algo o está parado?"),
    ],

    "marco_aceleracion": [
        ("alto", "marco_coherencia_dir", "acelerando → ¿hacia dónde?"),
    ],

    # === CAUSALIDAD ===
    "did": [
        ("alto", "iv_2sls", "efecto DiD → ¿confirma con IV?"),
        ("siempre", "t_statistic", "cualquier efecto → ¿es significativo?"),
    ],

    "ols": [
        ("siempre", "t_statistic", "estimación → ¿es significativo?"),
        ("siempre", "r_cuadrado", "estimación → ¿cuánto explica?"),
    ],

    "t_statistic": [
        ("alto", "p_valor", "significativo → ¿cuán incompatible con H0?"),
    ],

    "r_cuadrado": [
        ("bajo", "residuo_solow", "explica poco → ¿qué falta?"),
    ],

    # === FINANZAS ===
    "capm": [
        ("siempre", "sharpe", "retorno esperado → ¿eficiencia riesgo/retorno?"),
        ("siempre", "beta_capm", "retorno → ¿cuánta sensibilidad al mercado?"),
    ],

    "sharpe": [
        ("bajo", "frontera_eficiente", "mal compensado → ¿dónde está la frontera?"),
    ],

    "valor_presente_neto": [
        ("alto", "tir", "VPN positivo → ¿cuál es la TIR?"),
        ("bajo", "bellman", "VPN negativo → ¿hay opción de esperar? (valor de la opción)"),
    ],

    # === SOSTENIBILIDAD ===
    "deuda_pib": [
        ("alto", "dyn_deuda", "deuda alta → ¿trayectoria explosiva?"),
    ],

    "dyn_deuda": [
        ("alto", "prima_riesgo_arrowpratt", "deuda diverge → ¿cuánto riesgo percibe el mercado?"),
        ("alto", "marco_amplificacion", "diverge → ¿hay espiral deuda-tipos?"),
    ],
}


# ============================================================
# MOTOR DE CASCADA
# ============================================================

def evaluar_condicion(condicion, valor, polos):
    """Evalúa si la condición se cumple dado un valor y sus polos."""
    if condicion == "siempre":
        return True

    # Clasificar en alto/bajo/extremo usando el valor
    abs_val = abs(valor) if valor is not None else 0

    if condicion == "alto":
        return abs_val > 0.3 or (valor is not None and valor > 0)
    elif condicion == "bajo":
        return abs_val < 0.1 or (valor is not None and valor < 0)
    elif condicion == "extremo":
        return abs_val > 0.8

    return False


def cascada(resultados_simbionte, max_profundidad=4):
    """Ejecuta la cascada de preguntas encadenadas.

    Args:
        resultados_simbionte: dict {nombre_formula: valor} (output del Simbionte)
        max_profundidad: máximo de niveles de cascada

    Returns:
        lista de (profundidad, formula_origen, condicion, formula_destino, razon, valor)
    """
    cadena = []
    visitados = set()

    # Nivel 0: todas las fórmulas con resultado
    cola = [(0, None, None, nombre, "dato directo", valor)
            for nombre, valor in resultados_simbionte.items()
            if nombre in ENLACES]

    while cola:
        prof, origen, cond, nombre, razon, valor = cola.pop(0)

        if nombre in visitados:
            continue
        if prof > max_profundidad:
            continue

        visitados.add(nombre)

        # Obtener semántica para polos
        sem = SEMANTICA.get(nombre, {})
        polos = sem.get("polos", ("bajo", "alto"))

        # Registrar en la cadena
        if origen:
            cadena.append((prof, origen, cond, nombre, razon, valor))

        # Buscar enlaces desde esta fórmula
        if nombre in ENLACES:
            for cond_enlace, destino, razon_enlace in ENLACES[nombre]:
                if destino not in visitados:
                    if evaluar_condicion(cond_enlace, valor, polos):
                        # Obtener valor del destino si existe
                        val_destino = resultados_simbionte.get(destino)
                        cola.append((prof + 1, nombre, cond_enlace, destino, razon_enlace, val_destino))

    return cadena


def cascada_a_texto(cadena, resultados_simbionte):
    """Convierte la cascada en texto para el LLM.

    Incluye la pregunta de cada fórmula y marca verificación cruzada.
    """
    if not cadena:
        return "Sin cascada de preguntas (datos insuficientes)."

    lines = ["## RED DE PREGUNTAS (cascada del Simbionte)", ""]
    lines.append("Cada respuesta desbloquea nuevas preguntas. Usa esto para verificar tu razonamiento.")
    lines.append("Si tu análisis semántico contradice una respuesta estructural → señal de alerta.\n")

    by_depth = {}
    for prof, origen, cond, destino, razon, valor in cadena:
        if prof not in by_depth:
            by_depth[prof] = []
        by_depth[prof].append((origen, cond, destino, razon, valor))

    for prof in sorted(by_depth.keys()):
        lines.append(f"### Nivel {prof}")
        for origen, cond, destino, razon, valor in by_depth[prof]:
            sem = SEMANTICA.get(destino, {})
            pregunta = sem.get("pregunta", f"¿{destino}?")
            polos = sem.get("polos", ("?", "?"))

            val_str = f"{valor:.4f}" if valor is not None else "no calculado"

            lines.append(f"  {origen} ({cond}) → **{destino}**")
            lines.append(f"    Pregunta: {pregunta}")
            lines.append(f"    Eje: {polos[0]} ↔ {polos[1]}")
            lines.append(f"    Valor: {val_str}")
            lines.append(f"    Razón: {razon}")

            # Verificación cruzada
            if valor is not None:
                lines.append(f"    ⚡ VERIFICA: ¿tu análisis semántico coincide con '{polos[1] if valor > 0 else polos[0]}'?")
            lines.append("")

    lines.append(f"**{len(cadena)} preguntas encadenadas en {max(by_depth.keys()) + 1 if by_depth else 0} niveles.**")
    lines.append("Si alguna verificación cruzada falla → revisa tu razonamiento en ese punto.")

    return "\n".join(lines)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import numpy as np

    print("=" * 70)
    print("RED DE PREGUNTAS ENCADENADAS — Test")
    print("=" * 70)

    # Simular resultados del Simbionte para un escenario de estanflación
    resultados = {
        "varianza": 0.15,          # alta dispersión
        "skewness": -0.8,          # cola izquierda
        "kurtosis": 2.5,           # colas pesadas
        "gini": 0.45,              # desigualdad
        "correlacion": -0.92,      # co-movimiento fuerte negativo
        "elasticidad_general": -0.02,  # inelástico
        "persistencia": 0.65,      # persistente
        "output_gap": -0.07,       # bajo potencial
        "gap": -0.05,              # bajo tendencia
        "curva_phillips": 0.6,     # presión inflacionaria
        "regla_taylor": 4.5,       # tipos altos
        "multiplicador_fiscal": 0.8,  # bajo multiplicador
        "var_parametrico": 0.12,   # riesgo alto
        "garch": 0.08,             # volatilidad autoalimentada
        "deuda_pib": 120,          # deuda alta
        "dyn_deuda": 0.05,         # divergiendo
        "marco_amplificacion": 1.0,  # espiral
        "marco_regulacion": 0.0,   # sin freno
        "marco_n_agentes": 7,      # muchos agentes
        "marco_simetria_juego": 0.3,  # asimétrico
        "marco_cruce": 1.0,        # Nash posible
        "marco_agujeros": 15,      # muchos gaps
        "marco_curvatura_media": 0.6,  # mucha curvatura
        "marco_curvatura_max": 1.2,  # giro brusco
        "marco_vel_media": 0.4,    # rápido
        "marco_aceleracion": 0.1,  # acelerando
        "marco_emergencia": 1.0,   # emergencia
        "ols": 0.5,
        "t_statistic": 3.2,
        "r_cuadrado": 0.35,
        "capm": 0.08,
        "sharpe": 0.3,
        "valor_presente_neto": -50000,
    }

    cadena = cascada(resultados, max_profundidad=3)

    print(f"\n  {len(cadena)} preguntas encadenadas activadas")
    print(f"  {len(ENLACES)} fórmulas con enlaces definidos")
    print(f"  {sum(len(v) for v in ENLACES.values())} enlaces totales")

    texto = cascada_a_texto(cadena, resultados)
    print(f"\n{texto}")
