"""
Catálogo de Finalidades — Cada fórmula categorizada por PARA QUÉ SIRVE.

Fecha: 2026-04-13

El harness demand-driven funciona así:
  1. Usuario pregunta algo
  2. Harness detecta la INTENCIÓN (diagnosticar, prescribir, verificar...)
  3. Activa SOLO las fórmulas de esa finalidad
  4. El Simbionte calcula solo lo necesario
  5. pgvector busca significado semántico de cada fórmula activada
  6. LLM recibe: valor + significado + razonamiento paso a paso

10 finalidades = 10 tipos de pregunta que la economía puede responder.

$0 total (definiciones estáticas)
"""

# ============================================================
# FINALIDADES: para qué sirve cada fórmula
# ============================================================

FINALIDADES = {
    "DIAGNOSTICAR": {
        "pregunta": "¿En qué estado estoy?",
        "descripcion": "Fórmulas que posicionan una variable en un eje (nivel, dispersión, concentración, equilibrio)",
        "cuando_activar": ["estado", "situación", "fase", "ciclo", "dónde estamos", "diagnóstico", "análisis", "evaluar"],
        "formulas": [
            "varianza", "desviacion_estandar", "coeficiente_variacion", "media", "mediana",
            "gini", "entropia_shannon", "skewness", "kurtosis", "percentil",
            "output_gap", "gap", "hhi", "inflacion", "tasa_crecimiento",
            "deuda_pib", "solow_steady_state", "pib",
        ],
    },

    "RELACIONAR": {
        "pregunta": "¿Cómo se conectan X e Y?",
        "descripcion": "Fórmulas que miden relación, sensibilidad, co-movimiento entre variables",
        "cuando_activar": ["relación", "correlación", "causa", "afecta", "depende", "sensible", "impacto", "conectan"],
        "formulas": [
            "correlacion", "covarianza", "elasticidad_precio", "elasticidad_general",
            "beta_capm", "tasa_marginal_sustitucion", "curva_phillips",
            "ley_okun", "ecuacion_fisher", "persistencia",
        ],
    },

    "PRESCRIBIR": {
        "pregunta": "¿Qué debería hacer?",
        "descripcion": "Fórmulas que producen recomendaciones de política o decisión",
        "cuando_activar": ["hacer", "recomendar", "política", "decisión", "debería", "óptimo", "estrategia", "acción"],
        "formulas": [
            "regla_taylor", "multiplicador_fiscal", "bellman", "lagrangiano", "kkt",
            "capm", "equilibrio_nash", "cournot", "stackelberg",
            "regla_friedman", "pigouviana", "regla_oro_fiscal",
        ],
    },

    "VERIFICAR": {
        "pregunta": "¿Es esto real o es ruido?",
        "descripcion": "Fórmulas que testean hipótesis, significancia, causalidad",
        "cuando_activar": ["significativo", "real", "verificar", "comprobar", "causal", "efecto", "test", "evidencia"],
        "formulas": [
            "t_statistic", "p_valor", "r_cuadrado", "did", "iv_2sls",
            "control_sintetico", "granger_formal", "hausman", "sargan_hansen",
            "adf", "johansen_formal", "gauss_markov",
        ],
    },

    "PREDECIR": {
        "pregunta": "¿Qué va a pasar?",
        "descripcion": "Fórmulas con componente temporal/dinámico que proyectan tendencias",
        "cuando_activar": ["futuro", "predecir", "proyección", "tendencia", "pronóstico", "forecast", "va a pasar"],
        "formulas": [
            "persistencia", "ar1", "var", "garch", "impulso_respuesta",
            "euler_estocastica", "dyn_deuda", "convergencia_condicional",
            "cointegracion", "momentum",
        ],
    },

    "DESCOMPONER": {
        "pregunta": "¿De dónde viene esto?",
        "descripcion": "Fórmulas que separan un fenómeno en sus componentes",
        "cuando_activar": ["descomponer", "explicar", "componentes", "fuente", "contribución", "por qué", "de dónde viene"],
        "formulas": [
            "residuo_solow", "contabilidad_crecimiento", "slutsky",
            "hodrick_prescott_formal", "descomposicion_espectral_ts",
            "mankiw_romer_weil", "cholesky_var",
            "valor_shapley", "pib",
        ],
    },

    "MEDIR_RIESGO": {
        "pregunta": "¿Qué puede salir mal?",
        "descripcion": "Fórmulas que cuantifican incertidumbre, pérdida potencial, vulnerabilidad",
        "cuando_activar": ["riesgo", "peligro", "vulnerable", "pérdida", "crisis", "incertidumbre", "volatilidad", "extremo"],
        "formulas": [
            "var_parametrico", "kurtosis", "skewness", "garch",
            "varianza", "coeficiente_variacion", "max_drawdown",
            "aversion_riesgo_arrow_pratt", "prima_riesgo_arrowpratt",
            "dyn_deuda", "prospect_value",
        ],
    },

    "OPTIMIZAR": {
        "pregunta": "¿Cuál es el mejor punto?",
        "descripcion": "Fórmulas que encuentran máximos, mínimos, fronteras eficientes",
        "cuando_activar": ["óptimo", "mejor", "maximizar", "minimizar", "eficiente", "frontera", "ideal"],
        "formulas": [
            "bellman", "lagrangiano", "kkt", "hjb",
            "beneficio_maximo", "golden_rule", "frontera_eficiente",
            "solow_steady_state", "regla_taylor", "regla_friedman",
        ],
    },

    "VALORAR": {
        "pregunta": "¿Cuánto vale esto?",
        "descripcion": "Fórmulas que asignan valor presente, precio justo, utilidad",
        "cuando_activar": ["valor", "precio", "cuánto vale", "valorar", "coste", "beneficio", "rentabilidad"],
        "formulas": [
            "valor_presente_neto", "black_scholes", "capm", "sdf",
            "excedente_consumidor", "excedente_productor",
            "q_tobin", "utilidad_esperada_vnm",
            "equivalente_cierto",
        ],
    },

    "COMPARAR": {
        "pregunta": "¿Es mejor A o B?",
        "descripcion": "Fórmulas que producen rankings, ratios, scores comparativos",
        "cuando_activar": ["mejor", "peor", "comparar", "ranking", "alternativa", "vs", "frente a", "elegir"],
        "formulas": [
            "sharpe", "r_cuadrado", "aic", "indice_lerner",
            "gini", "idh", "ventaja_comparativa",
            "dominancia_estocastica_1", "factor_bayes",
        ],
    },
}


# ============================================================
# FORMULAS DE LOS 10 MARCOS MATEMÁTICOS (del Simbionte)
# ============================================================
# Las fórmulas que el Simbionte USA internamente —
# también deben estar en el catálogo para que el LLM pueda
# verificar el razonamiento del Simbionte.

FORMULAS_MARCOS = {
    "estadistica": {
        "formulas_internas": ["entropia_shannon", "varianza", "skewness", "kurtosis", "gini"],
        "pregunta_marco": "¿Cuál es la distribución de tipos funcionales?",
    },
    "conjuntos": {
        "formulas_internas": ["jaccard"],
        "formulas_nuevas": {
            "jaccard": {
                "formula": "J(A,B) = |A∩B| / |A∪B|",
                "eje": "similitud entre conjuntos",
                "polos": ("completamente diferentes", "idénticos"),
                "pregunta": "¿Cuánto se parecen dos períodos/grupos?",
                "razonamiento": [
                    ("Calcular intersección (elementos en común)", "¿Qué comparten?", "COMÚN"),
                    ("Calcular unión (todos los elementos)", "¿Cuántos hay en total?", "TOTAL"),
                    ("Dividir", "Proporción de lo compartido", "RESULTADO: grado de similitud"),
                ],
            },
        },
    },
    "grafos": {
        "formulas_internas": ["correlacion"],
        "formulas_nuevas": {
            "centralidad_grado": {
                "formula": "C(i) = Σ_j a_ij / (n-1)",
                "eje": "importancia en la red",
                "polos": ("periférico (pocas conexiones)", "central (muchas conexiones)"),
                "pregunta": "¿Cuán conectada está esta variable con las demás?",
                "razonamiento": [
                    ("Contar conexiones significativas de cada nodo", "¿Con cuántos se relaciona?", "GRADO"),
                    ("Normalizar por máximo posible", "Relativizar", "RESULTADO: importancia relativa en la red"),
                ],
            },
            "clustering_coef": {
                "formula": "C_i = 2·e_i / (k_i·(k_i-1))",
                "eje": "agrupamiento local",
                "polos": ("vecinos desconectados", "vecinos interconectados"),
                "pregunta": "¿Los vecinos de este nodo se conocen entre sí?",
                "razonamiento": [
                    ("Contar triángulos alrededor del nodo", "¿Cuántos vecinos están conectados entre sí?", "TRIÁNGULOS"),
                    ("Dividir por triángulos posibles", "Normalizar", "RESULTADO: densidad local de la red"),
                ],
            },
        },
    },
    "markov": {
        "formulas_internas": ["ar1", "persistencia"],
        "formulas_nuevas": {
            "matriz_transicion": {
                "formula": "P_ij = P(X_{t+1}=j | X_t=i)",
                "eje": "estructura de transiciones",
                "polos": ("transiciones aleatorias", "transiciones deterministas"),
                "pregunta": "¿Cuál es la probabilidad de pasar de un estado a otro?",
                "razonamiento": [
                    ("Para cada par de estados, contar transiciones observadas", "¿Cuántas veces se pasó de i a j?", "FRECUENCIA"),
                    ("Normalizar por total de salidas de cada estado", "Convertir a probabilidad", "RESULTADO: mapa de probabilidades de cambio"),
                ],
            },
            "distribucion_estacionaria": {
                "formula": "π = πP",
                "eje": "estado de largo plazo",
                "polos": ("transitorio (no tiene)", "ergódico (converge)"),
                "pregunta": "¿A dónde converge el sistema si lo dejas suficiente tiempo?",
                "razonamiento": [
                    ("Iterar la matriz de transición muchas veces", "P^n para n grande", "CONVERGENCIA"),
                    ("Cada fila converge a la misma distribución", "Estado de largo plazo", "RESULTADO: proporción de tiempo en cada estado"),
                ],
            },
        },
    },
    "juegos": {
        "formulas_internas": ["equilibrio_nash", "valor_shapley", "equilibrio_bayesiano", "cournot", "bertrand", "stackelberg"],
        "formulas_nuevas": {
            "payoff_matrix": {
                "formula": "u_i(s_i, s_{-i})",
                "eje": "resultado estratégico",
                "polos": ("peor resultado posible", "mejor resultado posible"),
                "pregunta": "¿Qué gana cada jugador con cada combinación de estrategias?",
                "razonamiento": [
                    ("Para cada combinación de estrategias, calcular payoff de cada jugador", "Matriz de resultados", "ESTRUCTURA del conflicto"),
                    ("Identificar dominancias, Nash, Pareto", "¿Qué se puede predecir?", "RESULTADO: mapa de incentivos"),
                ],
            },
        },
    },
    "cibernetica": {
        "formulas_internas": [],
        "formulas_nuevas": {
            "feedback_positivo": {
                "formula": "autocorr(x_t, x_{t+1}) > 0 con amplificación",
                "eje": "amplificación",
                "polos": ("sin feedback (independiente)", "feedback fuerte (espiral)"),
                "pregunta": "¿El sistema se autoamplifica?",
                "razonamiento": [
                    ("Medir autocorrelación de la serie", "¿El pasado refuerza el presente?", "DIRECCIÓN"),
                    ("Medir si la varianza crece con el tiempo", "¿Se amplifica?", "INTENSIDAD"),
                    ("Positivo + creciente = feedback positivo (espiral)", "El sistema diverge", "RESULTADO: ¿espiral virtuosa o viciosa?"),
                ],
            },
            "feedback_negativo": {
                "formula": "autocorr < 0 o mean-reversion",
                "eje": "regulación",
                "polos": ("sin regulación", "autorregulación fuerte"),
                "pregunta": "¿El sistema se corrige solo?",
                "razonamiento": [
                    ("Medir si desviaciones tienden a revertir", "¿Vuelve al equilibrio?", "REVERSIÓN"),
                    ("Velocidad de reversión", "¿Cuán rápido corrige?", "RESULTADO: resiliencia del sistema"),
                ],
            },
        },
    },
    "sistemas": {
        "formulas_internas": ["correlacion"],
        "formulas_nuevas": {
            "acoplamiento": {
                "formula": "media de |corr| entre todos los pares",
                "eje": "interdependencia",
                "polos": ("subsistemas independientes", "todo conectado con todo"),
                "pregunta": "¿Cuán interdependientes son las partes del sistema?",
                "razonamiento": [
                    ("Calcular correlación entre cada par de variables", "¿Se mueven juntas?", "PARES"),
                    ("Promediar valores absolutos", "¿Cuánta conexión media hay?", "RESULTADO: grado de acoplamiento"),
                ],
            },
            "emergencia": {
                "formula": "Var(Σx_i) / Σ Var(x_i)",
                "eje": "propiedades emergentes",
                "polos": ("reducible (todo = suma de partes)", "emergente (todo > suma de partes)"),
                "pregunta": "¿El todo es más que la suma de sus partes?",
                "razonamiento": [
                    ("Calcular varianza del agregado", "¿Cuánto varía el todo?", "VARIANZA total"),
                    ("Calcular suma de varianzas individuales", "¿Cuánto varía cada parte?", "SUMA de partes"),
                    ("Si ratio > 1: emergencia", "Las interacciones crean algo nuevo", "RESULTADO: ¿hay comportamiento emergente?"),
                ],
            },
        },
    },
    "topologia": {
        "formulas_internas": [],
        "formulas_nuevas": {
            "gaps_funcionales": {
                "formula": "funciones_esperadas - funciones_observadas",
                "eje": "completitud",
                "polos": ("completo (todo presente)", "con agujeros (faltan piezas)"),
                "pregunta": "¿Falta algo que debería estar?",
                "razonamiento": [
                    ("Listar funciones/tipos esperados", "¿Qué debería haber?", "EXPECTATIVA"),
                    ("Comparar con observados", "¿Qué hay realmente?", "REALIDAD"),
                    ("La diferencia son gaps", "Lo que falta", "RESULTADO: agujeros en la estructura"),
                ],
            },
            "persistencia_topologica": {
                "formula": "¿El patrón sobrevive si quitas una pieza?",
                "eje": "robustez",
                "polos": ("frágil (depende de pocas piezas)", "robusto (sobrevive a perturbaciones)"),
                "pregunta": "¿Cuán robusto es este patrón?",
                "razonamiento": [
                    ("Quitar un elemento", "Perturbar", "TEST"),
                    ("¿El patrón se mantiene?", "Robustez", "RESULTADO: ¿es estructural o depende de una pieza?"),
                ],
            },
        },
    },
    "geometria_diff": {
        "formulas_internas": [],
        "formulas_nuevas": {
            "curvatura": {
                "formula": "κ ≈ f''(x) / (1+f'(x)²)^(3/2)",
                "eje": "cambio de dirección",
                "polos": ("lineal (sin curvatura)", "muy curvo (giros bruscos)"),
                "pregunta": "¿La trayectoria está cambiando de dirección?",
                "razonamiento": [
                    ("Calcular segunda derivada", "¿El cambio se acelera o frena?", "ACELERACIÓN"),
                    ("Normalizar por pendiente", "Curvatura pura", "RESULTADO: cuánto gira la trayectoria"),
                ],
            },
            "inflexion": {
                "formula": "f''(x) cambia de signo",
                "eje": "punto de giro",
                "polos": ("sin cambio de régimen", "cambio de régimen"),
                "pregunta": "¿Hay un punto donde la tendencia cambia de naturaleza?",
                "razonamiento": [
                    ("Detectar cambios de signo en la segunda derivada", "¿Dónde cambia la curvatura?", "DETECCIÓN"),
                    ("En ese punto: la tendencia pasa de acelerarse a frenarse (o viceversa)", "Cambio de régimen", "RESULTADO: punto de inflexión"),
                ],
            },
        },
    },
    "cinematica": {
        "formulas_internas": ["tasa_crecimiento"],
        "formulas_nuevas": {
            "velocidad": {
                "formula": "v = Δx/Δt",
                "eje": "rapidez de cambio",
                "polos": ("estático (sin movimiento)", "rápido (cambio acelerado)"),
                "pregunta": "¿A qué velocidad cambia?",
                "razonamiento": [
                    ("Medir cambio en un período", "¿Cuánto se movió?", "CAMBIO"),
                    ("Dividir por tiempo", "Normalizar por duración", "RESULTADO: velocidad de cambio"),
                ],
            },
            "aceleracion_cinematica": {
                "formula": "a = Δv/Δt = Δ²x/Δt²",
                "eje": "cambio de velocidad",
                "polos": ("frenando", "acelerando"),
                "pregunta": "¿La velocidad de cambio está aumentando o disminuyendo?",
                "razonamiento": [
                    ("Medir cambio de velocidad entre períodos", "¿Se acelera o frena?", "CAMBIO de cambio"),
                    ("Positivo = acelerando, negativo = frenando", "Dirección", "RESULTADO: momentum del momentum"),
                ],
            },
            "coherencia_direccional": {
                "formula": "|mean(sign(Δx))| ",
                "eje": "consistencia de dirección",
                "polos": ("errático (cambia de dirección)", "coherente (dirección consistente)"),
                "pregunta": "¿Se mueve en una dirección consistente o zigzaguea?",
                "razonamiento": [
                    ("Calcular signo de cada cambio (+1 o -1)", "¿Sube o baja cada período?", "DIRECCIÓN"),
                    ("Promediar signos", "¿La mayoría van en la misma dirección?", "RESULTADO: consistencia del movimiento"),
                ],
            },
        },
    },
}


# ============================================================
# INTENCIÓN → FINALIDADES (para el harness demand-driven)
# ============================================================

def detectar_finalidad(pregunta_usuario):
    """Detecta qué finalidades activan la pregunta del usuario.

    Returns: lista de nombres de finalidad ordenados por relevancia
    """
    pregunta = pregunta_usuario.lower()
    scores = {}

    for nombre, info in FINALIDADES.items():
        score = 0
        for keyword in info["cuando_activar"]:
            if keyword in pregunta:
                score += 1
        if score > 0:
            scores[nombre] = score

    # Siempre incluir DIAGNOSTICAR como base
    if "DIAGNOSTICAR" not in scores:
        scores["DIAGNOSTICAR"] = 0.5

    return sorted(scores.keys(), key=lambda x: -scores[x])


def formulas_para_pregunta(pregunta_usuario):
    """Devuelve las fórmulas que debe activar el harness para esta pregunta.

    Returns: set de nombres de fórmulas
    """
    finalidades = detectar_finalidad(pregunta_usuario)
    formulas = set()
    for fin in finalidades:
        formulas.update(FINALIDADES[fin]["formulas"])
    return formulas


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("CATÁLOGO DE FINALIDADES")
    print("=" * 70)

    print(f"\n  {len(FINALIDADES)} finalidades")
    for nombre, info in FINALIDADES.items():
        print(f"    {nombre:<16s}: {info['pregunta']:<40s} ({len(info['formulas'])} fórmulas)")

    print(f"\n  {len(FORMULAS_MARCOS)} marcos con fórmulas internas")
    for marco, info in FORMULAS_MARCOS.items():
        n_internas = len(info.get("formulas_internas", []))
        n_nuevas = len(info.get("formulas_nuevas", {}))
        print(f"    {marco:<16s}: {n_internas} internas + {n_nuevas} nuevas")

    # Test de intención
    print(f"\n  TEST INTENCIÓN:")
    preguntas = [
        "¿En qué fase del ciclo está la economía?",
        "¿Qué debería hacer el banco central?",
        "¿El efecto del tratamiento es significativo?",
        "¿Qué riesgos ocultos hay?",
        "¿Cuánto vale esta inversión?",
        "¿Por qué bajó el PIB?",
        "¿Se mueven juntas la inflación y el desempleo?",
    ]
    for p in preguntas:
        fins = detectar_finalidad(p)
        forms = formulas_para_pregunta(p)
        print(f"    \"{p[:50]}...\"")
        print(f"      → {fins[:3]} ({len(forms)} fórmulas)")
