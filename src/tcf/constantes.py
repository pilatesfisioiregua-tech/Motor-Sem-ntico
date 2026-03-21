"""Constantes de la TCF — Tablas numéricas derivadas de los docs L0.

Fuentes:
  - RESULTADO_CALCULOS_ANALITICOS_v1.md (Cálculos 1-5)
  - TEORIA_CAMPO_FUNCIONAL.md (14 leyes, dependencias)
  - TEORIA_JUEGOS_LENTES.md (tabla valoración, coaliciones)
  - VALIDACION_TCF_CASO_PILATES.md (vector validado)
"""

# ---------------------------------------------------------------------------
# §1. FUNCIONES Y LENTES — VOCABULARIO
# ---------------------------------------------------------------------------

FUNCIONES = ("F1", "F2", "F3", "F4", "F5", "F6", "F7")

NOMBRES_FUNCIONES = {
    "F1": "Conservar",
    "F2": "Captar",
    "F3": "Depurar",
    "F4": "Distribuir",
    "F5": "Frontera",
    "F6": "Adaptar",
    "F7": "Replicar",
}

LENTES = ("salud", "sentido", "continuidad")

INTELIGENCIAS = tuple(f"INT-{i:02d}" for i in range(1, 19))

NOMBRES_INTELIGENCIAS = {
    "INT-01": "Lógica",
    "INT-02": "Computacional",
    "INT-03": "Estructural",
    "INT-04": "Ecológica",
    "INT-05": "Estratégica",
    "INT-06": "Política",
    "INT-07": "Financiera",
    "INT-08": "Social",
    "INT-09": "Lingüística",
    "INT-10": "Cinestésica",
    "INT-11": "Espacial",
    "INT-12": "Narrativa",
    "INT-13": "Prospectiva",
    "INT-14": "Divergente",
    "INT-15": "Estética",
    "INT-16": "Constructiva",
    "INT-17": "Existencial",
    "INT-18": "Contemplativa",
}


# ---------------------------------------------------------------------------
# §2. MAPA INT × F  (18 × 7 = 126 celdas)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md, Cálculo 1
#     Escala: A=1.0, M=0.5, B=0.25, N=0.0
# ---------------------------------------------------------------------------

AFINIDAD_INT_F: dict[str, dict[str, float]] = {
    #              F1    F2    F3    F4    F5    F6    F7
    "INT-01": {"F1": 0.50, "F2": 0.50, "F3": 0.50, "F4": 0.50, "F5": 0.50, "F6": 0.25, "F7": 0.25},
    "INT-02": {"F1": 0.50, "F2": 1.00, "F3": 0.50, "F4": 1.00, "F5": 0.25, "F6": 0.50, "F7": 0.50},
    "INT-03": {"F1": 1.00, "F2": 0.50, "F3": 0.50, "F4": 0.50, "F5": 1.00, "F6": 0.50, "F7": 0.50},
    "INT-04": {"F1": 0.50, "F2": 0.50, "F3": 1.00, "F4": 0.50, "F5": 0.50, "F6": 1.00, "F7": 0.50},
    "INT-05": {"F1": 0.50, "F2": 0.50, "F3": 0.25, "F4": 0.50, "F5": 0.50, "F6": 1.00, "F7": 0.50},
    "INT-06": {"F1": 0.50, "F2": 0.50, "F3": 0.25, "F4": 0.50, "F5": 1.00, "F6": 0.50, "F7": 0.25},
    "INT-07": {"F1": 1.00, "F2": 1.00, "F3": 0.50, "F4": 1.00, "F5": 0.50, "F6": 0.25, "F7": 0.50},
    "INT-08": {"F1": 0.50, "F2": 0.50, "F3": 0.50, "F4": 0.25, "F5": 0.50, "F6": 0.50, "F7": 0.25},
    "INT-09": {"F1": 0.25, "F2": 0.50, "F3": 0.50, "F4": 0.25, "F5": 1.00, "F6": 0.50, "F7": 0.50},
    "INT-10": {"F1": 0.50, "F2": 0.25, "F3": 0.50, "F4": 0.50, "F5": 0.25, "F6": 1.00, "F7": 0.25},
    "INT-11": {"F1": 0.50, "F2": 0.25, "F3": 0.25, "F4": 1.00, "F5": 1.00, "F6": 0.25, "F7": 0.50},
    "INT-12": {"F1": 0.50, "F2": 0.50, "F3": 0.25, "F4": 0.25, "F5": 0.50, "F6": 0.50, "F7": 1.00},
    "INT-13": {"F1": 0.25, "F2": 1.00, "F3": 0.25, "F4": 0.50, "F5": 0.50, "F6": 1.00, "F7": 0.50},
    "INT-14": {"F1": 0.25, "F2": 1.00, "F3": 0.50, "F4": 0.50, "F5": 0.50, "F6": 1.00, "F7": 0.50},
    "INT-15": {"F1": 0.50, "F2": 0.25, "F3": 1.00, "F4": 0.50, "F5": 0.50, "F6": 0.25, "F7": 0.25},
    "INT-16": {"F1": 1.00, "F2": 0.50, "F3": 0.25, "F4": 1.00, "F5": 0.50, "F6": 0.50, "F7": 1.00},
    "INT-17": {"F1": 0.25, "F2": 0.25, "F3": 1.00, "F4": 0.25, "F5": 1.00, "F6": 0.50, "F7": 0.50},
    "INT-18": {"F1": 0.25, "F2": 0.25, "F3": 0.50, "F4": 0.25, "F5": 0.50, "F6": 0.50, "F7": 0.25},
}


# ---------------------------------------------------------------------------
# §3. MAPA INT × L  (18 × 3 = 54 celdas)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md, Cálculo 2
# ---------------------------------------------------------------------------

AFINIDAD_INT_L: dict[str, dict[str, float]] = {
    #              salud  sentido continuidad
    "INT-01": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.25},
    "INT-02": {"salud": 1.00, "sentido": 0.25, "continuidad": 0.50},
    "INT-03": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.50},
    "INT-04": {"salud": 1.00, "sentido": 0.50, "continuidad": 1.00},
    "INT-05": {"salud": 0.50, "sentido": 1.00, "continuidad": 0.50},
    "INT-06": {"salud": 0.50, "sentido": 0.50, "continuidad": 0.50},
    "INT-07": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.50},
    "INT-08": {"salud": 0.50, "sentido": 1.00, "continuidad": 0.50},
    "INT-09": {"salud": 0.25, "sentido": 1.00, "continuidad": 0.50},
    "INT-10": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.25},
    "INT-11": {"salud": 1.00, "sentido": 0.25, "continuidad": 0.25},
    "INT-12": {"salud": 0.25, "sentido": 1.00, "continuidad": 1.00},
    "INT-13": {"salud": 0.50, "sentido": 0.50, "continuidad": 1.00},
    "INT-14": {"salud": 0.50, "sentido": 0.50, "continuidad": 0.50},
    "INT-15": {"salud": 0.50, "sentido": 1.00, "continuidad": 0.25},
    "INT-16": {"salud": 1.00, "sentido": 0.25, "continuidad": 1.00},
    "INT-17": {"salud": 0.25, "sentido": 1.00, "continuidad": 1.00},
    "INT-18": {"salud": 0.25, "sentido": 1.00, "continuidad": 0.25},
}


# ---------------------------------------------------------------------------
# §4. DEPENDENCIAS ENTRE FUNCIONES (Ley 2 TCF)
#     Fuente: TEORIA_CAMPO_FUNCIONAL.md §2, RESULTADO_CALCULOS_ANALITICOS_v1.md Cálculo 3
#     Formato: (Fi_dependiente, Fj_de_quien_depende, tipo)
#     Tipo B = bloqueante, Tipo D = degradante
# ---------------------------------------------------------------------------

DEPENDENCIAS: list[tuple[str, str, str]] = [
    # Bloqueantes (B) — Fi no puede operar sin Fj
    ("F2", "F3", "B"),   # Captar sin depurar = acumular basura
    ("F4", "F5", "B"),   # Distribuir sin frontera = fugas
    ("F7", "F5", "B"),   # Replicar sin frontera = replicar ruido

    # Degradantes (D) — Fi opera peor sin Fj, pero no se bloquea
    ("F1", "F6", "D"),   # Conservar sin adaptar = rigidez
    ("F6", "F5", "D"),   # Adaptar sin frontera = perder identidad
    ("F7", "F1", "D"),   # Replicar sin conservar = copias degradadas
    ("F3", "F5", "D"),   # Depurar sin frontera = no saber qué es residuo
    ("F2", "F5", "D"),   # Captar sin frontera = captar cualquier cosa
    ("F4", "F1", "D"),   # Distribuir sin conservar = descapitalizarse
    ("F7", "F3", "D"),   # Replicar sin depurar = amplificar defectos
    ("F6", "F1", "D"),   # Adaptar sin conservar = destruir lo esencial
]

# Índice rápido: dependencias por función dependiente
DEPS_POR_FUNCION: dict[str, list[tuple[str, str]]] = {}
for _fi, _fj, _tipo in DEPENDENCIAS:
    DEPS_POR_FUNCION.setdefault(_fi, []).append((_fj, _tipo))

# Índice rápido: funciones que dependen de Fj (dependientes de)
DEPENDIENTES_DE: dict[str, list[tuple[str, str]]] = {}
for _fi, _fj, _tipo in DEPENDENCIAS:
    DEPENDIENTES_DE.setdefault(_fj, []).append((_fi, _tipo))


# ---------------------------------------------------------------------------
# §5. TABLA DE VALORACIÓN FUNCIÓN → LENTE (Juegos de Lentes §2)
#     Fuente: TEORIA_JUEGOS_LENTES.md §2
#     Escala: ALTO=1.0, MEDIO=0.5, BAJO=0.25
# ---------------------------------------------------------------------------

VALORACION_F_L: dict[str, dict[str, float]] = {
    "F1": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.50},
    "F2": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.25},
    "F3": {"salud": 1.00, "sentido": 1.00, "continuidad": 0.50},
    "F4": {"salud": 1.00, "sentido": 0.50, "continuidad": 0.25},
    "F5": {"salud": 1.00, "sentido": 1.00, "continuidad": 1.00},
    "F6": {"salud": 0.50, "sentido": 0.50, "continuidad": 1.00},
    "F7": {"salud": 0.25, "sentido": 0.25, "continuidad": 1.00},
}


# ---------------------------------------------------------------------------
# §6. VECTORES CANÓNICOS DE ARQUETIPOS (12)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md Cálculo 4
#     + VALIDACION_TCF_CASO_PILATES.md (vector Pilates validado)
#     Formato: {F1, F2, F3, F4, F5, F6, F7}
# ---------------------------------------------------------------------------

ARQUETIPOS_CANONICOS: dict[str, dict[str, float]] = {
    "intoxicado": {
        # F2 media-alta, F3 muy baja, F1 degradándose
        "F1": 0.45, "F2": 0.65, "F3": 0.20, "F4": 0.50, "F5": 0.40, "F6": 0.40, "F7": 0.30,
    },
    "rigido": {
        # F1 alta, F6 muy baja, F5 rígida (cerrada)
        "F1": 0.80, "F2": 0.50, "F3": 0.50, "F4": 0.55, "F5": 0.70, "F6": 0.20, "F7": 0.30,
    },
    "sin_rumbo": {
        # F1-F4 medias-altas, F5 baja
        "F1": 0.60, "F2": 0.55, "F3": 0.45, "F4": 0.55, "F5": 0.30, "F6": 0.40, "F7": 0.25,
    },
    "hemorragico": {
        # F2 media, F4 baja, F5 baja
        "F1": 0.40, "F2": 0.50, "F3": 0.35, "F4": 0.25, "F5": 0.30, "F6": 0.35, "F7": 0.25,
    },
    "parasito_interno": {
        # F3 muy baja, F5 baja, F1 media (mantiene al parásito)
        "F1": 0.50, "F2": 0.45, "F3": 0.15, "F4": 0.40, "F5": 0.30, "F6": 0.35, "F7": 0.20,
    },
    "maquina_sin_alma": {
        # F5 decente (identidad clara), F7 muy baja (no replica), F2-F4 bajos-moderados
        # (el sistema funciona PORQUE una persona lo sostiene, no por sí mismo)
        # Validado contra caso Pilates: F1=0.50, F2=0.30, F3=0.25, F4=0.35, F5=0.65, F6=0.35, F7=0.20
        "F1": 0.50, "F2": 0.35, "F3": 0.30, "F4": 0.40, "F5": 0.65, "F6": 0.35, "F7": 0.20,
    },
    "semilla_dormida": {
        # F5 alta, F2 baja, F4 baja, Sentido alto
        "F1": 0.45, "F2": 0.25, "F3": 0.35, "F4": 0.25, "F5": 0.70, "F6": 0.40, "F7": 0.30,
    },
    "expansion_sin_cimientos": {
        # F7 alta, F1 baja, F2 alta
        "F1": 0.30, "F2": 0.65, "F3": 0.30, "F4": 0.45, "F5": 0.45, "F6": 0.45, "F7": 0.75,
    },
    "aislado": {
        # F5 muy alta (cerrada), F2 muy baja, F6 baja
        "F1": 0.60, "F2": 0.20, "F3": 0.45, "F4": 0.40, "F5": 0.85, "F6": 0.25, "F7": 0.30,
    },
    "copia_sin_esencia": {
        # F7 alta, F5 baja, F3 baja
        "F1": 0.45, "F2": 0.50, "F3": 0.25, "F4": 0.45, "F5": 0.30, "F6": 0.40, "F7": 0.70,
    },
    "quemado": {
        # Múltiples funciones colapsando
        "F1": 0.25, "F2": 0.20, "F3": 0.20, "F4": 0.25, "F5": 0.35, "F6": 0.20, "F7": 0.15,
    },
    "equilibrado": {
        # Todas las F en grado medio-alto
        "F1": 0.75, "F2": 0.70, "F3": 0.70, "F4": 0.70, "F5": 0.80, "F6": 0.70, "F7": 0.65,
    },
}

NOMBRES_ARQUETIPOS = {
    "intoxicado": "Intoxicado",
    "rigido": "Rígido",
    "sin_rumbo": "Sin Rumbo",
    "hemorragico": "Hemorrágico",
    "parasito_interno": "Parásito Interno",
    "maquina_sin_alma": "Máquina sin Alma",
    "semilla_dormida": "Semilla Dormida",
    "expansion_sin_cimientos": "Expansión sin Cimientos",
    "aislado": "Aislado",
    "copia_sin_esencia": "Copia sin Esencia",
    "quemado": "Quemado",
    "equilibrado": "Equilibrado",
}

# Señal lingüística típica de cada arquetipo (para logs/debug)
SENALES_ARQUETIPOS = {
    "intoxicado": "Estamos muy ocupados pero no avanzamos.",
    "rigido": "Siempre hemos hecho así y funciona.",
    "sin_rumbo": "No sé decir no / Todo me parece bien.",
    "hemorragico": "Facturamos mucho pero no nos queda nada.",
    "parasito_interno": "Es parte de cómo somos.",
    "maquina_sin_alma": "¿Qué pasa si mañana no estoy?",
    "semilla_dormida": "Lo que hago es bueno, pero nadie lo sabe.",
    "expansion_sin_cimientos": "Estamos creciendo muy rápido.",
    "aislado": "No necesitamos nada de fuera.",
    "copia_sin_esencia": "Ya no es lo que era.",
    "quemado": "Ya da igual.",
    "equilibrado": "Sé lo que soy, funciono, y podría transmitir esto.",
}


# ---------------------------------------------------------------------------
# §7. FIRMAS LINGÜÍSTICAS (Pre-screening Paso 0)
#     Fuente: TCF §11, VALIDACION_TCF_CASO_PILATES.md §5
#     Cada firma = lista de patrones regex-compatible
# ---------------------------------------------------------------------------

FIRMAS_LINGUISTICAS: dict[str, list[str]] = {
    "maquina_sin_alma": [
        r"todo depende de (mí|mi|él|ella)",
        r"sin (mí|él|ella) no funciona",
        r"qué pasa si.*no estoy",
        r"solo yo (sé|puedo|hago)",
        r"nadie (más|otro) puede",
        r"todo requiere.*intervención",
        r"no puedo delegar",
    ],
    "semilla_dormida": [
        r"(es|es bueno|funciona) pero nadie (lo )?sabe",
        r"solo por boca a boca",
        r"no (sé|sabemos) (cómo )?vender",
        r"tengo algo (bueno|valioso) pero",
        r"nadie (conoce|sabe de)",
        r"no llega a (más|nadie)",
    ],
    "rigido": [
        r"siempre (hemos|ha) (hecho|funcionado) así",
        r"no (hace falta|necesitamos?) cambiar",
        r"esto funciona (bien|perfecto)",
        r"no (veo|hay) (necesidad|razón) de",
        r"nunca hemos (necesitado|tenido que)",
    ],
    "intoxicado": [
        r"hacemos (mucho|de todo|mil cosas)",
        r"no paramos",
        r"estamos (muy )?ocupados pero no",
        r"todo (está|sigue) (igual|como antes)",
        r"no (puedo|podemos) (con todo|más)",
        r"acumulamos",
    ],
    "quemado": [
        r"ya (da|me da) (igual|lo mismo)",
        r"estoy (cansad[oa]|hart[oa]) de (intentar|todo)",
        r"no (merece|vale) la pena",
        r"para qué (seguir|intentar|esforzarse)",
        r"no (tengo|queda) (energía|fuerza|ganas)",
    ],
    "sin_rumbo": [
        r"estamos en todo",
        r"no (sé|sabemos) (decir no|rechazar|priorizar)",
        r"todo (me |nos )parece (bien|interesante)",
        r"no (sé|tengo claro) (qué|quién|adónde)",
        r"hacemos (un poco )?de todo",
    ],
    "hemorragico": [
        r"facturamos.*pero no (queda|sobra)",
        r"(entra|ingresa).*pero (se va|sale)",
        r"no (retenemos|conservamos)",
        r"(perdemos|se van) (clientes|talento|recursos)",
        r"como llenar.*agujeros",
    ],
    "expansion_sin_cimientos": [
        r"creciendo (muy |más )rápido",
        r"abrimos.*nuevo",
        r"escalando",
        r"(más|nuevas) (sucursales|sedes|oficinas|líneas)",
        r"los números no cuadran.*pero",
    ],
    "aislado": [
        r"no necesitamos (nada|a nadie) de fuera",
        r"nosotros (solos|mismos)",
        r"no (aceptamos|queremos) (ayuda|inversión|socios)",
        r"lo (hacemos|resolvemos) todo (internamente|solos)",
    ],
    "copia_sin_esencia": [
        r"ya no es lo que era",
        r"se (perdió|diluyó) la (esencia|identidad|calidad)",
        r"cada (vez|copia|réplica) (peor|más diluida)",
        r"no es lo (mismo|original)",
    ],
    "parasito_interno": [
        r"es parte de (cómo|lo que) somos",
        r"siempre (ha sido|fue) así",
        r"no (podemos|se puede) (cambiar|tocar|mover) eso",
        r"sin (él|ella|eso) no (funciona|podemos)",
        r"es (intocable|sagrado|imposible de cambiar)",
    ],
}


# ---------------------------------------------------------------------------
# §8. RECETAS POR ARQUETIPO (Cálculo 5)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md Cálculo 5
#     secuencia: orden de ataque a funciones
#     ints: INTs en orden de ejecución
#     lente: lente primaria de la intervención
#     frenar: funciones a FRENAR antes de empezar (Regla 14 / Ley 13)
# ---------------------------------------------------------------------------

RECETAS: dict[str, dict] = {
    "intoxicado": {
        "secuencia": ["F5", "F3", "F1"],
        "ints": ["INT-04", "INT-17", "INT-16"],
        "ints_complemento": ["INT-01"],
        "lente": "salud",
        "frenar": [],
    },
    "rigido": {
        "secuencia": ["F5", "F6", "F1"],
        "ints": ["INT-13", "INT-14", "INT-05", "INT-16"],
        "ints_complemento": [],
        "lente": "salud",
        "frenar": [],
    },
    "sin_rumbo": {
        "secuencia": ["F5", "F2", "F3"],
        "ints": ["INT-06", "INT-17", "INT-08", "INT-16"],
        "ints_complemento": [],
        "lente": "sentido",
        "frenar": [],
    },
    "hemorragico": {
        "secuencia": ["F5", "F4", "F1"],
        "ints": ["INT-07", "INT-11", "INT-03", "INT-16"],
        "ints_complemento": ["INT-08"],
        "lente": "salud",
        "frenar": [],
    },
    "parasito_interno": {
        "secuencia": ["F5", "F3", "F1"],
        "ints": ["INT-03", "INT-06", "INT-17", "INT-16"],
        "ints_complemento": [],
        "lente": "salud",
        "frenar": [],
    },
    "maquina_sin_alma": {
        "secuencia": ["F5", "F3", "F7"],
        "ints": ["INT-02", "INT-17", "INT-15", "INT-12", "INT-16"],
        "ints_complemento": [],
        "lente": "continuidad",
        "frenar": [],
    },
    "semilla_dormida": {
        "secuencia": ["F2", "F4", "F7"],
        "ints": ["INT-07", "INT-05", "INT-14", "INT-16"],
        "ints_complemento": ["INT-08"],
        "lente": "salud",
        "frenar": [],
    },
    "expansion_sin_cimientos": {
        "secuencia": ["F1", "F3"],
        "ints": ["INT-01", "INT-03", "INT-04", "INT-16"],
        "ints_complemento": ["INT-08"],
        "lente": "salud",
        "frenar": ["F7"],  # Ley 13: FRENAR expansión
    },
    "aislado": {
        "secuencia": ["F5", "F2", "F6"],
        "ints": ["INT-13", "INT-14", "INT-05", "INT-16"],
        "ints_complemento": ["INT-08"],
        "lente": "salud",
        "frenar": [],
    },
    "copia_sin_esencia": {
        "secuencia": ["F5", "F3", "F7"],
        "ints": ["INT-01", "INT-17", "INT-15", "INT-03", "INT-16"],
        "ints_complemento": [],
        "lente": "continuidad",
        "frenar": ["F7"],  # Ley 13: FRENAR replicación sin esencia
    },
    "quemado": {
        "secuencia": ["F3", "F2", "F1"],  # PARAR primero (implícito)
        "ints": ["INT-18", "INT-10", "INT-04", "INT-16"],
        "ints_complemento": [],
        "lente": "salud",
        "frenar": [],  # No hay función alta que frenar; el freno es global (PARAR)
        "parar_primero": True,  # Señal especial: bajar tensión antes de todo
    },
    "equilibrado": {
        "secuencia": [],  # Mantenimiento, no intervención
        "ints": [],
        "ints_complemento": [],
        "lente": "salud",
        "frenar": [],
    },
}


# ---------------------------------------------------------------------------
# §9. TOP 3 INTs POR FUNCIÓN (derivado del mapa INT×F)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md, resumen Cálculo 1
# ---------------------------------------------------------------------------

TOP_INTS_POR_FUNCION: dict[str, list[str]] = {
    "F1": ["INT-03", "INT-07", "INT-16"],
    "F2": ["INT-07", "INT-02", "INT-13"],
    "F3": ["INT-04", "INT-17", "INT-15"],
    "F4": ["INT-07", "INT-02", "INT-16"],
    "F5": ["INT-03", "INT-06", "INT-09"],
    "F6": ["INT-04", "INT-05", "INT-14"],
    "F7": ["INT-16", "INT-12", "INT-02"],
}


# ---------------------------------------------------------------------------
# §10. TOP 3 INTs POR LENTE (derivado del mapa INT×L)
#     Fuente: RESULTADO_CALCULOS_ANALITICOS_v1.md, resumen Cálculo 2
# ---------------------------------------------------------------------------

TOP_INTS_POR_LENTE: dict[str, list[str]] = {
    "salud":       ["INT-03", "INT-07", "INT-16"],
    "sentido":     ["INT-17", "INT-08", "INT-12"],
    "continuidad": ["INT-04", "INT-16", "INT-13"],
}


# ---------------------------------------------------------------------------
# §11. ATRACTORES DEL CAMPO (Ley 10 TCF)
# ---------------------------------------------------------------------------

ATRACTORES = {
    "equilibrio": {
        "descripcion": "Todas las F en grado medio-alto, coherentes con dependencias",
        "estable": True,
        "sano": True,
    },
    "rigidez": {
        "descripcion": "F1 alta, F6 baja. Conserva sin adaptar. Mínimo local.",
        "estable": True,
        "sano": False,
    },
    "colapso": {
        "descripcion": "Todas las F cayendo. Atractor de entropía máxima.",
        "estable": True,
        "sano": False,
    },
    "aislamiento": {
        "descripcion": "F5 muy alta cerrada, F2 baja. Desconectado.",
        "estable": True,
        "sano": False,
    },
}


# ---------------------------------------------------------------------------
# §12. CICLOS FUNCIONALES (Teorema 4 TCF)
# ---------------------------------------------------------------------------

CICLOS = {
    "metabolico": {
        "funciones": ["F2", "F3", "F4", "F1"],
        "cadencia": "rapida",    # día a día
        "descripcion": "Captar, depurar, distribuir, conservar",
    },
    "identidad": {
        "funciones": ["F5", "F2", "F3", "F5"],
        "cadencia": "media",     # semanas/meses
        "descripcion": "Saber quién soy, captar lo que me nutre, depurar lo que no soy, refinar identidad",
    },
    "evolucion": {
        "funciones": ["F6", "F5", "F7", "F1"],
        "cadencia": "lenta",     # meses/años
        "descripcion": "Adaptar, redefinir, replicar, conservar nueva forma",
    },
}


# ---------------------------------------------------------------------------
# §13. OPERACIONES SOBRE EL CAMPO (§8 TCF)
# ---------------------------------------------------------------------------

OPERACIONES_CAMPO = [
    "SUBIR",              # Aumentar grado de Fi
    "FRENAR",             # Reducir grado de Fi (Ley 13)
    "PERMEABILIZAR_F5",   # Abrir frontera selectivamente
    "ENDURECER_F5",       # Cerrar frontera
    "CICLO_METABOLICO",   # Activar F2→F3→F4→F1
    "CICLO_IDENTIDAD",    # Activar F5→F2→F3→F5
    "CICLO_EVOLUCION",    # Activar F6→F5→F7→F1
    "ROMPER_CICLO_VICIOSO",
    "CAMBIAR_ATRACTOR",
]


# ---------------------------------------------------------------------------
# §14. UMBRALES (derivados empíricamente de la validación Pilates)
# ---------------------------------------------------------------------------

# Umbral para considerar una dependencia violada
UMBRAL_BLOQUEANTE = 0.30   # Fj < 0.30 con tipo B → Fi bloqueada
UMBRAL_DEGRADANTE = 0.35   # Fj < 0.35 con tipo D → Fi degradada

# Umbral de percepción de toxicidad (Ley 3 corregida)
UMBRAL_PERCEPCION_TOXICIDAD = 0.10  # brecha Fi-Fj < 0.10 → toxicidad subliminal

# Umbral para scoring de arquetipos
UMBRAL_SCORE_ARQUETIPO = 0.15  # score < 0.15 → ruido, no reportar

# Umbral para considerar una función "alta" vs "baja"
UMBRAL_FUNCION_ALTA = 0.55
UMBRAL_FUNCION_BAJA = 0.35

# Umbral para considerar una lente "alta" vs "baja"
UMBRAL_LENTE_ALTA = 0.50
UMBRAL_LENTE_BAJA = 0.35


# ---------------------------------------------------------------------------
# §15. VECTOR DE TEST — CASO PILATES (validado empíricamente)
#     Fuente: VALIDACION_TCF_CASO_PILATES.md §1
# ---------------------------------------------------------------------------

VECTOR_PILATES = {
    "F1": 0.50, "F2": 0.30, "F3": 0.25, "F4": 0.35,
    "F5": 0.65, "F6": 0.35, "F7": 0.20,
}

LENTES_PILATES_ESPERADAS = {
    "salud": 0.40,
    "sentido": 0.60,
    "continuidad": 0.20,
}

ARQUETIPO_PILATES_ESPERADO = {
    "primario": {"arquetipo": "maquina_sin_alma", "score_min": 0.65},
    "secundario": {"arquetipo": "semilla_dormida"},
    "coalicion": "salud_sentido",
    "perfil_lente": "S+Se+C-",  # Salud↑ Sentido↑ Continuidad↓
}
