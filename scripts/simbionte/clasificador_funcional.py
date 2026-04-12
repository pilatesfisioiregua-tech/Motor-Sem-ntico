"""
Clasificador de Función Real en Contexto
Fecha: 2026-04-12

Clasifica cada token por su función real en la oración, no por su categoría gramatical.
94.2% determinista (spaCy + listas cerradas + sufijos). 5.8% requiere Haiku en Harness H1.

Ref: DISEÑO_FUNCIONES_REALES.md
Ref: CAPA_0_ESPECIFICACION.md v1.5 §0 (paso 3: traducir función real)
"""

from collections import Counter

# ============================================================
# CATÁLOGO DE FUNCIONES REALES (51 tipos)
# ============================================================

# Cada tipo tiene un código numérico único y una categoría padre
FUNCIONES = {
    # SUSTANTIVOS (8 tipos)
    "sust_agente":         {"codigo": 1,  "cat": "sustantivo", "desc": "Quien realiza la acción (nsubj)"},
    "sust_paciente":       {"codigo": 2,  "cat": "sustantivo", "desc": "Quien recibe la acción (obj)"},
    "sust_complemento":    {"codigo": 3,  "cat": "sustantivo", "desc": "Complemento circunstancial (obl)"},
    "sust_modificador":    {"codigo": 4,  "cat": "sustantivo", "desc": "Modifica a otro sustantivo (nmod)"},
    "sust_locativo":       {"codigo": 5,  "cat": "sustantivo", "desc": "Dónde ocurre (obl + en/sobre)"},
    "sust_instrumento":    {"codigo": 6,  "cat": "sustantivo", "desc": "Con qué se hace (obl + con/mediante)"},
    "sust_nom_verbo":      {"codigo": 7,  "cat": "sustantivo", "desc": "Nominalización de verbo (-ción/-miento)"},
    "sust_nom_adj":        {"codigo": 8,  "cat": "sustantivo", "desc": "Nominalización de adjetivo (-dad/-eza)"},
    "sust_no_clasificado": {"codigo": 9,  "cat": "sustantivo", "desc": "Sustantivo sin clasificar (requiere Harness)"},

    # ADJETIVOS (7 tipos)
    "adj_relacional":      {"codigo": 10, "cat": "adjetivo", "desc": "Vincula con ámbito (-al/-ivo/-ico)"},
    "adj_participio":      {"codigo": 11, "cat": "adjetivo", "desc": "Verbo congelado como adjetivo (VerbForm=Part)"},
    "adj_predicativo":     {"codigo": 12, "cat": "adjetivo", "desc": "Atributo vía cópula (cop como hijo)"},
    "adj_ordinal":         {"codigo": 13, "cat": "adjetivo", "desc": "Posición (NumType=Ord)"},
    "adj_no_clasificado":  {"codigo": 14, "cat": "adjetivo", "desc": "Adjetivo sin clasificar (requiere Harness)"},

    # NUMERALES → reclasificados como adjetivos por función en contexto
    # Ref: CAPA_0_ESPECIFICACION.md §0 "Los datos numéricos son adjetivos comprimidos"
    # "3.000€" califica a "empresa" en el eje facturación = adj calificativo especificativo
    # "tres" califica a "trimestres" en el eje cantidad = numeral cardinal
    # El tipo de adjetivo depende del contexto, no de la naturaleza del dato
    "num_cardinal":        {"codigo": 15, "cat": "numeral_adj", "desc": "Cantidad cardinal que modifica sustantivo (tres equipos)"},
    "num_ordinal_func":    {"codigo": 58, "cat": "numeral_adj", "desc": "Posición en secuencia (primer trimestre)"},
    "num_calif_espec":     {"codigo": 59, "cat": "numeral_adj", "desc": "Dato que especifica CUÁL (la inversión de 3.000€)"},
    "num_calif_explic":    {"codigo": 60, "cat": "numeral_adj", "desc": "Dato que atribuye cualidad (los enormes 3M€)"},
    "num_indefinido":      {"codigo": 61, "cat": "numeral_adj", "desc": "Cantidad imprecisa con matiz (solo 3.000€, apenas el 2%)"},
    "num_posesivo":        {"codigo": 62, "cat": "numeral_adj", "desc": "Dato con poseedor (sus 3.000€, nuestro 15%)"},
    "num_predicativo":     {"codigo": 63, "cat": "numeral_adj", "desc": "Dato como atributo vía cópula (el margen es 15%)"},

    # DETERMINANTES (7 tipos)
    "det_articulo":        {"codigo": 16, "cat": "determinante", "desc": "Artículo (PronType=Art)"},
    "det_demostrativo":    {"codigo": 17, "cat": "determinante", "desc": "Señala cuál (PronType=Dem)"},
    "det_posesivo":        {"codigo": 18, "cat": "determinante", "desc": "De quién (Poss=Yes)"},
    "det_indefinido":      {"codigo": 19, "cat": "determinante", "desc": "Cantidad imprecisa (PronType=Ind)"},
    "det_total":           {"codigo": 20, "cat": "determinante", "desc": "Totalidad (PronType=Tot)"},
    "det_negativo":        {"codigo": 21, "cat": "determinante", "desc": "Negación determinante (PronType=Neg)"},
    "det_otro":            {"codigo": 22, "cat": "determinante", "desc": "Otro determinante"},

    # VERBOS (9 tipos)
    "verb_indicativo":     {"codigo": 23, "cat": "verbo", "desc": "Acción real, certeza (Mood=Ind)"},
    "verb_condicional":    {"codigo": 24, "cat": "verbo", "desc": "Acción hipotética (Mood=Cnd)"},
    "verb_subjuntivo":     {"codigo": 25, "cat": "verbo", "desc": "Deseo, duda, posibilidad (Mood=Sub)"},
    "verb_imperativo":     {"codigo": 26, "cat": "verbo", "desc": "Orden directa (Mood=Imp)"},
    "verb_infinitivo":     {"codigo": 27, "cat": "verbo", "desc": "Proceso sin conjugar (VerbForm=Inf)"},
    "verb_gerundio":       {"codigo": 28, "cat": "verbo", "desc": "Proceso en curso (VerbForm=Ger)"},
    "verb_participio":     {"codigo": 29, "cat": "verbo", "desc": "Estado resultante (VerbForm=Part)"},
    "verb_copula":         {"codigo": 30, "cat": "verbo", "desc": "Enlace ser/estar (dep=cop)"},
    "verb_auxiliar":       {"codigo": 31, "cat": "verbo", "desc": "Acompaña verbo principal (dep=aux)"},

    # ADVERBIOS (9 tipos)
    "adv_negacion":        {"codigo": 32, "cat": "adverbio", "desc": "Negación (no, nunca, jamás)"},
    "adv_tiempo":          {"codigo": 33, "cat": "adverbio", "desc": "Cuándo (ayer, después, finalmente)"},
    "adv_lugar":           {"codigo": 34, "cat": "adverbio", "desc": "Dónde (aquí, dentro, fuera)"},
    "adv_cantidad":        {"codigo": 35, "cat": "adverbio", "desc": "Cuánto (muy, más, casi)"},
    "adv_epistemico":      {"codigo": 36, "cat": "adverbio", "desc": "Certeza (probablemente, quizás)"},
    "adv_frecuencia":      {"codigo": 37, "cat": "adverbio", "desc": "Con qué frecuencia (siempre, a veces)"},
    "adv_absoluto":        {"codigo": 38, "cat": "adverbio", "desc": "Totalidad (absolutamente, completamente)"},
    "adv_modo":            {"codigo": 39, "cat": "adverbio", "desc": "Cómo (sufijo -mente u otro)"},
    "adv_no_clasificado":  {"codigo": 40, "cat": "adverbio", "desc": "Adverbio sin clasificar (requiere Harness)"},

    # CONJUNCIONES (8 tipos)
    "conj_copulativa":     {"codigo": 41, "cat": "conjuncion", "desc": "Y, sinergia, adición"},
    "conj_adversativa":    {"codigo": 42, "cat": "conjuncion", "desc": "PERO, tensión, oposición"},
    "conj_disyuntiva":     {"codigo": 43, "cat": "conjuncion", "desc": "O, alternativa, elección"},
    "conj_causal":         {"codigo": 44, "cat": "conjuncion", "desc": "PORQUE, causa-efecto"},
    "conj_condicional":    {"codigo": 45, "cat": "conjuncion", "desc": "SI, hipótesis"},
    "conj_concesiva":      {"codigo": 46, "cat": "conjuncion", "desc": "AUNQUE, tolerancia"},
    "conj_temporal":       {"codigo": 47, "cat": "conjuncion", "desc": "CUANDO, secuencia"},
    "conj_otra":           {"codigo": 48, "cat": "conjuncion", "desc": "Otra conjunción"},

    # PREPOSICIONES (7 tipos)
    "prep_espacial":       {"codigo": 49, "cat": "preposicion", "desc": "Ubicación (en, sobre, bajo)"},
    "prep_temporal":       {"codigo": 50, "cat": "preposicion", "desc": "Tiempo (durante, hasta, desde)"},
    "prep_instrumental":   {"codigo": 51, "cat": "preposicion", "desc": "Medio (con, mediante)"},
    "prep_final":          {"codigo": 52, "cat": "preposicion", "desc": "Propósito (para)"},
    "prep_relacion":       {"codigo": 53, "cat": "preposicion", "desc": "Pertenencia/relación (de)"},
    "prep_direccion":      {"codigo": 54, "cat": "preposicion", "desc": "Movimiento (a, hacia)"},
    "prep_no_clasificado": {"codigo": 55, "cat": "preposicion", "desc": "Preposición ambigua (requiere Harness)"},

    # PRONOMBRES (1 tipo)
    "pronombre":           {"codigo": 56, "cat": "pronombre", "desc": "Pronombre (sustituye al sustantivo)"},

    # OTRO (1 tipo)
    "otro":                {"codigo": 57, "cat": "otro", "desc": "No clasificado"},
}

N_FUNCIONES = len(FUNCIONES)  # 63 (57 base + 6 tipos numeral-adjetivo nuevos)
FUNC_NAMES = list(FUNCIONES.keys())
FUNC_CODES = {name: info["codigo"] for name, info in FUNCIONES.items()}

# ============================================================
# LISTAS CERRADAS (verificadas)
# ============================================================

ADV_TIEMPO = frozenset({"ayer","hoy","mañana","después","antes","luego","finalmente",
    "posteriormente","previamente","entonces","mientras","ya","aún","todavía",
    "pronto","tarde","temprano","inmediatamente","recientemente"})
ADV_LUGAR = frozenset({"aquí","allí","ahí","dentro","fuera","arriba","abajo","cerca",
    "lejos","delante","detrás","encima","debajo","donde"})
ADV_CANTIDAD = frozenset({"muy","mucho","poco","bastante","demasiado","más","menos",
    "tanto","casi","apenas","solo","solamente"})
ADV_EPISTEMICO = frozenset({"probablemente","posiblemente","quizás","quizá","seguramente",
    "evidentemente","aparentemente","supuestamente","realmente","efectivamente",
    "ciertamente","indudablemente"})
ADV_NEGACION = frozenset({"no","nunca","jamás","tampoco","ni"})
ADV_FRECUENCIA = frozenset({"siempre","frecuentemente","habitualmente","generalmente",
    "normalmente","raramente","ocasionalmente"})
ADV_ABSOLUTO = frozenset({"absolutamente","totalmente","completamente","definitivamente",
    "enteramente","plenamente"})

SUF_NOM_VERBO = ("ción","sión","miento","aje","ura","anza","encia","ancia")
SUF_NOM_ADJ = ("dad","eza","ía","itud","ez")
SUF_RELACIONAL = ("al","ar","ivo","iva","ico","ica","ero","era","ario","aria","tico","tica")

# ============================================================
# CLASIFICADOR PRINCIPAL
# ============================================================

def _dep(t):
    """Normaliza DEP labels entre spaCy ES (Universal) y EN (Clear NLP)."""
    d = t.dep_
    if d == "dobj": return "obj"      # EN→ES
    if d == "pobj": return "obl"      # EN→ES
    if d == "dative": return "iobj"   # EN→ES
    return d


def clasificar_token(t):
    """Clasifica un token spaCy por su función real en contexto.
    Funciona con spaCy ES y EN (normaliza deps automáticamente).

    Returns: (func_name: str, needs_haiku: bool)
    """
    dep = _dep(t)

    # === SUSTANTIVOS ===
    if t.pos_ in ("NOUN", "PROPN"):
        if dep == "nsubj":
            return "sust_agente", False
        elif dep == "obj":
            return "sust_paciente", False
        elif dep == "obl":
            cases = [c for c in t.children if _dep(c) == "case"]
            if cases:
                prep = cases[0].text.lower()
                if prep in ("con", "mediante", "with", "by"):
                    return "sust_instrumento", False
                elif prep in ("en", "dentro", "sobre", "in", "on", "at"):
                    return "sust_locativo", False
            return "sust_complemento", False
        elif dep == "nmod":
            return "sust_modificador", False
        elif t.text.lower().endswith(SUF_NOM_VERBO):
            return "sust_nom_verbo", False
        elif t.text.lower().endswith(SUF_NOM_ADJ):
            return "sust_nom_adj", False
        else:
            return "sust_no_clasificado", True

    # === ADJETIVOS ===
    elif t.pos_ == "ADJ":
        vf = t.morph.get("VerbForm", [""])[0] if t.morph.get("VerbForm") else ""
        nt = t.morph.get("NumType", [""])[0] if t.morph.get("NumType") else ""
        if vf == "Part":
            return "adj_participio", False
        elif nt == "Ord":
            return "adj_ordinal", False
        elif any(_dep(c) == "cop" for c in t.children):
            return "adj_predicativo", False
        elif t.text.lower().endswith(SUF_RELACIONAL):
            return "adj_relacional", False
        else:
            return "adj_no_clasificado", True

    # === NUMERALES → adjetivos por función en contexto ===
    # Ref: CAPA_0_ESPECIFICACION.md "Los datos numéricos son adjetivos comprimidos"
    elif t.pos_ == "NUM":
        nt = t.morph.get("NumType", [""])[0] if t.morph.get("NumType") else ""
        head = t.head
        # Ordinal
        if nt == "Ord":
            return "num_ordinal_func", False
        # Predicativo: "el margen ES 15%", "la cifra FUE 3000"
        if head.pos_ in ("VERB", "AUX") and _dep(head) == "cop":
            return "num_predicativo", False
        if dep == "attr" or (dep == "ROOT" and any(_dep(c) == "cop" for c in t.children)):
            return "num_predicativo", False
        # Posesivo: "sus 3.000€" — PRON/DET posesivo como hijo del NUM o hermano del NUM
        own_children = list(t.children)
        siblings = list(head.children) if head != t else []
        has_poss = (
            any(s.morph.get("Poss") for s in own_children if s.pos_ in ("PRON", "DET")) or
            any(s.morph.get("Poss") for s in siblings if s.pos_ in ("PRON", "DET"))
        )
        if has_poss:
            return "num_posesivo", False
        # Indefinido: "solo 3.000€", "apenas el 2%", "unos 5.000" — ADV limitador
        INDEF_MARKERS = frozenset({"solo","sólo","solamente","apenas","unos","unas","casi","cerca","alrededor"})
        has_indef = (
            any(s.text.lower() in INDEF_MARKERS for s in own_children if s.pos_ in ("ADV", "DET")) or
            any(s.text.lower() in INDEF_MARKERS for s in siblings if s.pos_ in ("ADV", "DET"))
        )
        if has_indef:
            return "num_indefinido", False
        # Calificativo explicativo: ADJ valorativo antepuesto como hermano ("los enormes 3M€")
        has_valorativo = any(s.pos_ == "ADJ" and s.i < t.i and _dep(s) == "amod" for s in siblings)
        if has_valorativo:
            return "num_calif_explic", False
        # Calificativo especificativo: modifica sustantivo vía nmod/obl ("inversión DE 3.000€")
        if dep in ("nmod", "obl") and head.pos_ in ("NOUN", "PROPN"):
            return "num_calif_espec", False
        # Caso compound: "treinta por ciento" → el head es otro NUM
        if dep == "compound" and head.pos_ == "NUM":
            return "num_cardinal", False  # el head llevará la función real
        # Default simple nummod → cardinal si modifica sustantivo directamente
        if dep == "nummod" and head.pos_ in ("NOUN", "PROPN"):
            return "num_cardinal", False
        # Todo lo demás: necesita Harness H1 para clasificar qué tipo de adjetivo
        # "facturó 47 millones" → ¿califica la acción? ¿especifica cuánto?
        return "num_cardinal", True  # True = needs_haiku

    # === DETERMINANTES ===
    elif t.pos_ == "DET":
        pt = t.morph.get("PronType", [""])[0] if t.morph.get("PronType") else ""
        poss = t.morph.get("Poss")
        if pt == "Dem": return "det_demostrativo", False
        elif poss: return "det_posesivo", False
        elif pt == "Ind": return "det_indefinido", False
        elif pt == "Art": return "det_articulo", False
        elif pt == "Tot": return "det_total", False
        elif pt == "Neg": return "det_negativo", False
        else: return "det_otro", False

    # === VERBOS ===
    elif t.pos_ in ("VERB", "AUX"):
        mood = t.morph.get("Mood", [""])[0] if t.morph.get("Mood") else ""
        vf = t.morph.get("VerbForm", [""])[0] if t.morph.get("VerbForm") else ""
        if dep == "cop": return "verb_copula", False
        elif dep == "aux": return "verb_auxiliar", False
        elif mood == "Ind": return "verb_indicativo", False
        elif mood == "Cnd": return "verb_condicional", False
        elif mood == "Sub": return "verb_subjuntivo", False
        elif mood == "Imp": return "verb_imperativo", False
        elif vf == "Inf": return "verb_infinitivo", False
        elif vf == "Ger": return "verb_gerundio", False
        elif vf == "Part": return "verb_participio", False
        else: return "verb_indicativo", False  # Default para verbos finitos sin Mood

    # === ADVERBIOS ===
    elif t.pos_ == "ADV":
        tl = t.text.lower()
        if tl in ADV_NEGACION or t.morph.get("Polarity"): return "adv_negacion", False
        elif tl in ADV_TIEMPO: return "adv_tiempo", False
        elif tl in ADV_LUGAR: return "adv_lugar", False
        elif tl in ADV_CANTIDAD: return "adv_cantidad", False
        elif tl in ADV_EPISTEMICO: return "adv_epistemico", False
        elif tl in ADV_FRECUENCIA: return "adv_frecuencia", False
        elif tl in ADV_ABSOLUTO: return "adv_absoluto", False
        elif tl.endswith("mente"): return "adv_modo", False
        else: return "adv_no_clasificado", True

    # === CONJUNCIONES ===
    elif t.pos_ in ("CCONJ", "SCONJ"):
        tl = t.text.lower()
        if tl in ("y", "e", "ni"): return "conj_copulativa", False
        elif tl in ("pero", "sino", "mas"): return "conj_adversativa", False
        elif tl in ("o", "u"): return "conj_disyuntiva", False
        elif tl in ("porque", "pues"): return "conj_causal", False
        elif tl == "si": return "conj_condicional", False
        elif tl == "aunque": return "conj_concesiva", False
        elif tl in ("cuando", "mientras"): return "conj_temporal", False
        else: return "conj_otra", False

    # === PREPOSICIONES ===
    elif t.pos_ == "ADP":
        tl = t.text.lower()
        if tl in ("en", "sobre", "bajo", "entre", "dentro", "fuera"): return "prep_espacial", False
        elif tl in ("durante", "hasta", "desde", "tras"): return "prep_temporal", False
        elif tl in ("con", "mediante"): return "prep_instrumental", False
        elif tl == "para": return "prep_final", False
        elif tl == "de": return "prep_relacion", False
        elif tl == "a": return "prep_direccion", False
        elif tl == "por": return "prep_no_clasificado", True
        else: return "prep_no_clasificado", False

    # === PRONOMBRES ===
    elif t.pos_ == "PRON":
        return "pronombre", False

    # === OTRO ===
    else:
        return "otro", False


def clasificar_texto(doc):
    """Clasifica todos los tokens funcionales de un documento.

    Returns: list of (token, func_name, needs_haiku)
    """
    resultados = []
    for t in doc:
        if t.is_punct or t.is_space:
            continue
        func_name, needs_haiku = clasificar_token(t)
        resultados.append((t, func_name, needs_haiku))
    return resultados


def distribucion_funcional(doc):
    """Calcula la distribución de funciones reales del texto.

    Returns: dict con:
        - distribucion: list de 57 floats (proporción de cada función)
        - tokens_haiku: list de tokens que necesitan clasificación por Harness
        - stats: dict con estadísticas
    """
    resultados = clasificar_texto(doc)
    n_total = max(len(resultados), 1)

    counts = Counter()
    tokens_haiku = []
    n_haiku = 0

    for t, func_name, needs_haiku in resultados:
        counts[func_name] += 1
        if needs_haiku:
            n_haiku += 1
            tokens_haiku.append({
                "text": t.text,
                "pos": t.pos_,
                "dep": t.dep_,
                "head": t.head.text,
                "func_asignada": func_name,
            })

    # Vector de distribución (57 valores)
    dist = [counts.get(name, 0) / n_total for name in FUNC_NAMES]

    return {
        "distribucion": dist,
        "tokens_haiku": tokens_haiku,
        "stats": {
            "total": n_total,
            "determinista": n_total - n_haiku,
            "haiku": n_haiku,
            "pct_determinista": (n_total - n_haiku) / n_total * 100,
            "n_tipos_activos": len([d for d in dist if d > 0]),
        }
    }
