"""Razonador v3 — Framework ACD completo al 100%.

Basado en MARCO_LINGUISTICO_COMPLETO.md (12,800 lineas, S11-S48).

ARQUITECTURA:
  8 operaciones cognitivas (S11) — cada una detecta un tipo de fallo
  6 detectores de falacias (S48.5) — operaciones defectuosas
  6 roturas sujeto-predicado (S48.7) — falacias a escala oracion
  9 modos de percepcion (S6) — puntos ciegos perceptivos
  3 lentes SER/ESTAR/SEGUIR (S2.2) — condiciones de vida
  Resolucion luminica avanzada (S41) — vela/habitacion/estadio
  Analisis de posicion conjuntiva (S42.6) — que hay antes/despues del conector
  Operabilidad inter-capa (S10) — creencias condicionando capas
  Oracion del sistema (S2.3) — diagnostico completo
  3 cruces entre operaciones (S42.6) — reglas de cruce originales

Coste: $0.00 (codigo puro, sin LLM)
Latencia: <5ms

Referencia: docs/L0/MARCO_LINGUISTICO_COMPLETO.md
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re


# ===================================================================
# FILTRO ANTI-ARTEFACTOS
# El Perceptor a veces devuelve caracteres sueltos ("m", "é", "t")
# en vez de conceptos. Este filtro los elimina.
# ===================================================================

def _limpiar_lista(lista: list) -> list:
    """Filtra entradas de menos de 3 caracteres (artefactos del Perceptor)."""
    if not isinstance(lista, list):
        return []
    return [x for x in lista if isinstance(x, str) and len(x.strip()) >= 3]


def _e_limpio(e: dict) -> dict:
    """Limpia todas las listas de una estructura ACD para eliminar artefactos."""
    ec = {}
    for dim_key, dim_val in e.items():
        if isinstance(dim_val, dict):
            ec[dim_key] = {}
            for k, v in dim_val.items():
                if isinstance(v, list):
                    ec[dim_key][k] = _limpiar_lista(v)
                else:
                    ec[dim_key][k] = v
        else:
            ec[dim_key] = dim_val
    return ec


# ===================================================================
# TIPOS
# ===================================================================

@dataclass
class Hallazgo:
    tipo: str          # contradiccion | colapso | punto_ciego | tension | falacia | patron | oportunidad | modo_ausente | lente_ausente | creencia_oculta | posicion_conjuntiva
    operacion: str     # que operacion cognitiva detecto esto
    severidad: float   # 0.0 a 1.0
    descripcion: str
    dimensiones: list  # que dimensiones ACD estan involucradas
    accion_sugerida: str = ""


@dataclass
class Diagnostico:
    hallazgos: list[Hallazgo] = field(default_factory=list)
    salud: float = 1.0
    resumen: str = ""
    palanca: str = ""
    preguntas: list[str] = field(default_factory=list)
    oracion_sistema: str = ""                     # La oracion completa del sistema (S2.3)
    resolucion_luminica: float = 0.0              # Cuantas operaciones se ejecutaron (S41)
    nivel_luminico: str = ""                      # vela | habitacion | estadio (S41)
    operaciones_detectadas: list[str] = field(default_factory=list)
    falacias_detectadas: list[str] = field(default_factory=list)
    modos_presentes: list[str] = field(default_factory=list)    # S6
    modos_ausentes: list[str] = field(default_factory=list)     # S6
    lentes_cubiertas: list[str] = field(default_factory=list)   # S2.2 SER/ESTAR/SEGUIR
    invariantes_violados: list[str] = field(default_factory=list)  # L0 invariants
    # Cálculo 3: Operaciones cognitivas (qué hace el texto en la mente del receptor)
    ops_cognitivas: dict = field(default_factory=dict)  # {tipo: score}


# ===================================================================
# LAS 8 OPERACIONES COGNITIVAS (S11, S42)
#
# Cada operacion no solo analiza — detecta si se ejecuto bien,
# mal, o esta AUSENTE. La ausencia es tan importante como el fallo.
# ===================================================================

def _op1_modificacion(e: dict) -> list[Hallazgo]:
    """MODIFICACION: adj + sust -> sust' (Filtra/especifica)
    S42: Adjetivacion = cualificar, diferenciar, evaluar.
    Gana: capacidad de seleccion y juicio.
    Pierde: marco referencial si no se declara.
    S42.5: El dato numerico SUSTITUYE al adjetivo con maxima resolucion."""
    hallazgos = []
    adj = e.get("adjetivos", {})
    precision = adj.get("precision", 0.5)
    vacios = adj.get("vacios", [])
    cualidades = adj.get("cualidades", [])

    # Adjetivos vacios = modificacion sin contenido
    if len(vacios) > 1:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="modificacion",
            severidad=0.6,
            descripcion=f"Modificacion vacia: {len(vacios)} adjetivos sin contenido real ({', '.join(vacios[:3])}). Cualifican sin medir. S42.5: un dato numerico resolveria esto.",
            dimensiones=["adjetivos"],
            accion_sugerida="Reemplazar cada adjetivo vago por un dato: cuanto? comparado con que?",
        ))

    # Baja precision = modificacion sin marco referencial
    if precision < 0.3 and cualidades:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="modificacion",
            severidad=0.5,
            descripcion=f"Modificacion sin marco: las cualidades ({', '.join(str(c) for c in cualidades[:3])}) no tienen referente. 'Alto' sin saber respecto a que.",
            dimensiones=["adjetivos"],
            accion_sugerida="Declarar el marco referencial: alto respecto a que? bueno comparado con quien?",
        ))

    return hallazgos


def _op2_predicacion(e: dict) -> list[Hallazgo]:
    """PREDICACION: sust + verbo -> oracion (Genera valor de verdad)
    S42: Verbalizacion = activar, ejecutar, mover.
    S11.2: No conmutativa — 'el sistema estructura' != 'estructura el sistema?'
    S24.1: La predicacion ES el acto de pensar."""
    hallazgos = []
    sp = e.get("sujeto_predicado", {})
    agencia = sp.get("agencia", 0.5)
    sujeto = sp.get("sujeto", "")
    predicado = sp.get("predicado", "")
    responsabilidad = sp.get("responsabilidad", "")

    # Sujeto difuso = predicacion sin agente
    sujetos_difusos = ["se", "uno", "hay que", "se deberia", "habria que",
                       "nosotros", "la empresa", "el equipo", "todos", "nadie"]
    es_difuso = any(d in sujeto.lower() for d in sujetos_difusos) if sujeto else not sujeto

    if es_difuso:
        hallazgos.append(Hallazgo(
            tipo="patron", operacion="predicacion",
            severidad=0.6,
            descripcion=f"Predicacion sin agente: '{sujeto}' no puede ejecutar el verbo. S48.7.4: oracion impersonal como argumento. Nadie es responsable -> nada pasa.",
            dimensiones=["sujeto_predicado"],
            accion_sugerida="QUIEN exactamente va a hacer esto? Nombre propio.",
        ))

    # Agencia baja = el sujeto no es dueno de la accion
    if agencia < 0.3 and sujeto:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="predicacion",
            severidad=0.5,
            descripcion=f"Agencia diluida ({agencia:.1f}): '{sujeto}' aparece como sujeto pero no tiene control real sobre la accion.",
            dimensiones=["sujeto_predicado"],
            accion_sugerida="Quien tiene realmente el poder de actuar aqui?",
        ))

    return hallazgos


def _op3_complementacion(e: dict) -> list[Hallazgo]:
    """COMPLEMENTACION: adv + verbo -> verbo' (Especifica modo)
    S42: Adverbializacion = modalizar, describir proceso.
    Gana: diagnostico de operacion.
    Pierde: el verbo que modifica si queda ambiguo.
    S11.4: Operador -> aplicado a funcion. 'Con que instrumento observo?'"""
    hallazgos = []
    adv = e.get("adverbios", {})
    explicitud = adv.get("explicitud", 0.5)
    modos_ocultos = adv.get("modos_ocultos", [])
    modo_explicito = adv.get("modo_explicito", "")

    # Modos ocultos = hay operacion no declarada
    if len(modos_ocultos) > 0:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="complementacion",
            severidad=0.5 + 0.1 * min(len(modos_ocultos), 3),
            descripcion=f"Complementacion oculta: {len(modos_ocultos)} modos de operar no declarados ({', '.join(str(m) for m in modos_ocultos[:3])}). Se dice '{modo_explicito}' pero se hace de otra manera.",
            dimensiones=["adverbios"],
            accion_sugerida="Hacer explicito: como se hace REALMENTE esto?",
        ))

    # Baja explicitud = todo implicito
    if explicitud < 0.3:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="complementacion",
            severidad=0.6,
            descripcion=f"Explicitud baja ({explicitud:.1f}): casi todo el 'como' esta implicito. Alto riesgo de malentendido.",
            dimensiones=["adverbios"],
            accion_sugerida="Explicitar: con que metodo? en que orden? con que frecuencia?",
        ))

    return hallazgos


def _op4_transitividad(e: dict) -> list[Hallazgo]:
    """TRANSITIVIDAD: verbo + sust -> predicado (Funcion aplicada a argumento)
    S11.4: Funcion -> sobre objeto de otra capa. 'Estructura QUE?'
    S12 Paso 4: Sin objeto explicito, la funcion esta declarada pero no definida: f( ) sin argumento."""
    hallazgos = []
    verbo = e.get("verbo", {})
    sp = e.get("sujeto_predicado", {})
    fuerza = verbo.get("fuerza", 0.5)
    verbo_nuclear = verbo.get("verbo_nuclear", "")
    produce = verbo.get("produce_resultado", False)

    # Verbo sin resultado = transitividad incompleta
    if not produce and verbo_nuclear:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="transitividad",
            severidad=0.5,
            descripcion=f"Transitividad incompleta: '{verbo_nuclear}' no produce resultado observable. Funcion declarada sin argumento — f( ) sin input. S12: 'la funcion esta declarada pero no definida'.",
            dimensiones=["verbo"],
            accion_sugerida="Que resultado CONCRETO produce esta accion? Como se mide?",
        ))

    # Verbo debil = la accion no tiene fuerza para transitivizar
    if fuerza < 0.3 and verbo_nuclear:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="transitividad",
            severidad=0.5,
            descripcion=f"Verbo debil ({fuerza:.1f}): '{verbo_nuclear}' no tiene fuerza ejecutiva suficiente. No puede actuar sobre un objeto.",
            dimensiones=["verbo"],
            accion_sugerida="Reemplazar por un verbo mas especifico: que accion concreta?",
        ))

    return hallazgos


def _op5_subordinacion(e: dict) -> list[Hallazgo]:
    """SUBORDINACION: oracion + oracion -> oracion' (Reduce oracion a modificador)
    S11.4: Creencia/Regla -> condiciona otra capa.
    S42: Las cadenas causales (porque/si/aunque) SON subordinacion.
    S3: Creencias = proposiciones congeladas que condicionan todo lo demas.
    S48.6: Falacias compuestas = subordinaciones defectuosas encadenadas."""
    hallazgos = []
    conj = e.get("conjunciones", {})
    prep = e.get("preposiciones", {})
    cc = conj.get("causalidades_circulares", [])
    fd = conj.get("falsas_dicotomias", [])
    colapsos = prep.get("colapsos", [])

    # Causalidad circular = subordinacion que se muerde la cola
    if cc:
        hallazgos.append(Hallazgo(
            tipo="falacia", operacion="subordinacion",
            severidad=0.8,
            descripcion=f"Subordinacion circular: {', '.join(str(c) for c in cc[:2])}. La cadena causal vuelve al punto de partida — no hay causa raiz.",
            dimensiones=["conjunciones"],
            accion_sugerida="Romper el ciclo: cual es la causa que NO depende de las demas?",
        ))

    # Colapsos de nivel = subordinacion entre niveles incompatibles
    if colapsos:
        hallazgos.append(Hallazgo(
            tipo="colapso", operacion="subordinacion",
            severidad=0.7,
            descripcion=f"Colapso de niveles logicos: se subordina un nivel a otro incompatible ({', '.join(str(c) for c in colapsos[:3])}). S Tipos_Logicos: mezclar identidad con conducta rompe la logica.",
            dimensiones=["preposiciones"],
            accion_sugerida="Separar niveles: que es identidad? que es capacidad? que es conducta?",
        ))

    # Falsas dicotomias = subordinacion que elimina opciones
    if fd:
        hallazgos.append(Hallazgo(
            tipo="falacia", operacion="subordinacion",
            severidad=0.6,
            descripcion=f"Falsa dicotomia: se presenta como 'o X o Y' cuando hay mas opciones ({', '.join(str(f) for f in fd[:2])}). S48.5: falacia conjuntiva.",
            dimensiones=["conjunciones"],
            accion_sugerida="Que opciones NO se estan considerando?",
        ))

    return hallazgos


def _op6_cuantificacion(e: dict) -> list[Hallazgo]:
    """CUANTIFICACION: det + sust -> sust_acotado (Fija alcance)
    S11.4: Alcance -> aplicado a cualquier elemento. 'toda regla' vs 'alguna regla'.
    S42.5: El dato numerico es cuantificacion maxima — sustituye adjetivo por medida.
    Sin cuantificacion, la modificacion es vacia."""
    hallazgos = []
    adj = e.get("adjetivos", {})
    verbo = e.get("verbo", {})
    precision = adj.get("precision", 0.5)
    fuerza = verbo.get("fuerza", 0.5)

    # Baja precision + alta fuerza = actuar sin medir
    if precision < 0.4 and fuerza > 0.6:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="cuantificacion",
            severidad=0.6,
            descripcion=f"Accion sin cuantificacion: se actua con fuerza ({fuerza:.1f}) pero sin precision ({precision:.1f}). S42.5: sin dato numerico, no se puede calcular el gap.",
            dimensiones=["adjetivos", "verbo"],
            accion_sugerida="Cuanto exactamente? Como se mide el resultado?",
        ))

    # Baja precision + bajo todo = nada esta cuantificado
    if precision < 0.3 and fuerza < 0.3:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="cuantificacion",
            severidad=0.5,
            descripcion=f"Ausencia de cuantificacion: ni las cualidades ni las acciones tienen medida. Todo es opinion sin escala.",
            dimensiones=["adjetivos", "verbo"],
            accion_sugerida="Introducir al menos un dato: cuanto? cuando? comparado con que?",
        ))

    return hallazgos


def _op7_conexion(e: dict) -> list[Hallazgo]:
    """CONEXION: X + conj + X -> X' (Vincula homogeneos)
    S11.2: Y es conmutativa. PORQUE no es conmutativa. PERO no es asociativa.
    S42.6: La posicion respecto al conector revela funcion cognitiva.
    S42.6 cruce: [sust-de-verbo + adj] PERO [sust-de-verbo + adj] = tension entre acciones congeladas."""
    hallazgos = []
    conj = e.get("conjunciones", {})
    tipo_conexion = conj.get("tipo_conexion", "")
    piezas_sueltas = conj.get("piezas_sueltas", [])

    # Piezas sueltas = falta de conexion
    if len(piezas_sueltas) > 1:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="conexion",
            severidad=0.5,
            descripcion=f"Fragmentacion: {len(piezas_sueltas)} ideas sin conexion entre si ({', '.join(str(s) for s in piezas_sueltas[:3])}). Falta el conector que revele la relacion.",
            dimensiones=["conjunciones"],
            accion_sugerida="Estas ideas estan conectadas por Y (sinergia), PERO (tension), o AUNQUE (concesion)?",
        ))

    # Sin conexion explicita = yuxtaposicion
    if not tipo_conexion and len(piezas_sueltas) == 0:
        # Verificar si hay contenido que deberia estar conectado
        sust = e.get("sustantivos", {})
        perdido = sust.get("perdido", [])
        if len(perdido) > 2:
            hallazgos.append(Hallazgo(
                tipo="punto_ciego", operacion="conexion",
                severidad=0.4,
                descripcion="Yuxtaposicion sin conector: hay multiples elementos pero no se explicita la relacion entre ellos.",
                dimensiones=["conjunciones", "sustantivos"],
                accion_sugerida="Cual es la relacion: y (suman), pero (contrastan), porque (causan)?",
            ))

    return hallazgos


def _op8_transformacion(e: dict) -> list[Hallazgo]:
    """TRANSFORMACION: X -> Y (Cambia categoria)
    S11.2: No involutiva — la transformacion PIERDE informacion.
    S42.4: Cada categoria puede derivar de las demas. Lo que pierde depende del origen.
    S42.3: El sustantivo como reina del ajedrez — puede ocupar cualquier posicion.
    CLAVE: Sustantivizar = comprimir/congelar. Verbalizar = activar/descongelar.
    S42: 'congela pelicula en foto' -> gana portabilidad, pierde agente/verbo/tempo/objeto."""
    hallazgos = []
    sust = e.get("sustantivos", {})
    verbo = e.get("verbo", {})
    caps = sust.get("capsulas", {})
    perdido = sust.get("perdido", [])
    verbo_nuclear = verbo.get("verbo_nuclear", "")
    fuerza = verbo.get("fuerza", 0.5)

    # Mucha perdida al comprimir = transformacion destructiva
    if len(perdido) > 2:
        hallazgos.append(Hallazgo(
            tipo="tension", operacion="transformacion",
            severidad=0.5,
            descripcion=f"Compresion destructiva: al sustantivizar se pierden {len(perdido)} elementos ({', '.join(str(p) for p in perdido[:3])}). S42: 'congela pelicula en foto — gana portabilidad, pierde agente/verbo/tempo/objeto'.",
            dimensiones=["sustantivos"],
            accion_sugerida="Descomprimir: quien hace que, cuando, como, a quien?",
        ))

    # Verbo de vida ausente = la accion no alimenta ninguna funcion vital
    verbo_vida = verbo.get("verbo_vida", "")
    if not verbo_vida or verbo_vida.lower() in ("", "ninguno", "no aplica", "none"):
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="transformacion",
            severidad=0.5,
            descripcion="Sin verbo de vida: la accion no se conecta con ninguno de los 7 verbos vitales (mantener/distinguir/repartir/responder/copiar/sacar/meter). No alimenta vida.",
            dimensiones=["verbo"],
            accion_sugerida="Que funcion vital alimenta esta accion?",
        ))

    return hallazgos


# ===================================================================
# DETECTORES DE FALACIAS (S48.5, S48.7)
# 6 operaciones defectuosas + 6 roturas sujeto-predicado
# ===================================================================

def _fal_sustantiva(e: dict) -> Hallazgo | None:
    """FALACIA SUSTANTIVA: sustantivo opaco como prueba.
    S48.5: re-empaquetar con contenido falso."""
    sust = e.get("sustantivos", {})
    perdido = sust.get("perdido", [])
    caps = sust.get("capsulas", {})
    palabra = caps.get("palabra", "")

    # Si la capsula-palabra es muy corta pero hay mucha perdida
    if palabra and len(perdido) > 3:
        return Hallazgo(
            tipo="falacia", operacion="fal_sustantiva",
            severidad=0.6,
            descripcion=f"Posible falacia sustantiva: se comprime todo en '{palabra}' pero se pierden {len(perdido)} elementos. El paquete puede ocultar la realidad.",
            dimensiones=["sustantivos"],
            accion_sugerida=f"Abrir el paquete: que hay realmente dentro de '{palabra}'?",
        )
    return None


def _fal_adjetiva(e: dict) -> Hallazgo | None:
    """FALACIA ADJETIVA: cualidad atribuida sin soporte logico.
    S48.5: 'peligrosa' justificada por 'Musk lo dice' = adj sin conexion logica."""
    adj = e.get("adjetivos", {})
    vacios = adj.get("vacios", [])
    precision = adj.get("precision", 0.5)

    if len(vacios) > 2 and precision < 0.3:
        return Hallazgo(
            tipo="falacia", operacion="fal_adjetiva",
            severidad=0.7,
            descripcion=f"Falacia adjetiva: {len(vacios)} cualidades sin soporte logico ({', '.join(vacios[:3])}). Las cualidades se atribuyen sin prueba.",
            dimensiones=["adjetivos"],
            accion_sugerida="Para cada cualidad: que DATO la sostiene?",
        )
    return None


def _fal_adverbial(e: dict) -> Hallazgo | None:
    """FALACIA ADVERBIAL: modificador como prueba logica.
    S48.5: 'inevitablemente' sin dato."""
    adv = e.get("adverbios", {})
    explicitud = adv.get("explicitud", 0.5)
    ocultos = adv.get("modos_ocultos", [])

    if explicitud < 0.2 and len(ocultos) > 1:
        return Hallazgo(
            tipo="falacia", operacion="fal_adverbial",
            severidad=0.6,
            descripcion=f"Falacia adverbial: se opera de {len(ocultos)} formas no declaradas mientras se dice algo distinto. El 'como' real esta oculto.",
            dimensiones=["adverbios"],
            accion_sugerida="Como se hace REALMENTE vs como se dice que se hace?",
        )
    return None


def _fal_verbal(e: dict) -> Hallazgo | None:
    """FALACIA VERBAL: agente/accion mal asignados.
    S48.7.1: sujeto falso — sustantivo abstracto como agente."""
    sp = e.get("sujeto_predicado", {})
    sujeto = sp.get("sujeto", "")
    agencia = sp.get("agencia", 0.5)

    # Sujeto abstracto con agencia asignada = sujeto falso
    sujetos_abstractos = ["la economia", "la tradicion", "la ciencia", "el mercado",
                          "la sociedad", "el sistema", "la tecnologia", "la situacion",
                          "la realidad", "la vida", "el destino"]
    es_abstracto = any(sa in sujeto.lower() for sa in sujetos_abstractos) if sujeto else False

    if es_abstracto and agencia > 0.5:
        return Hallazgo(
            tipo="falacia", operacion="fal_verbal",
            severidad=0.7,
            descripcion=f"Sujeto falso (S48.7.1): '{sujeto}' es una nominalizacion — no tiene voluntad, no puede actuar. Se le atribuye agencia que no posee.",
            dimensiones=["sujeto_predicado"],
            accion_sugerida=f"Quien REALMENTE esta actuando detras de '{sujeto}'?",
        )
    return None


def _fal_conjuntiva(e: dict) -> Hallazgo | None:
    """FALACIA CONJUNTIVA: conector logico mal usado.
    S48.5: cadena si->entonces sin verificar cada paso."""
    conj = e.get("conjunciones", {})
    cc = conj.get("causalidades_circulares", [])
    fd = conj.get("falsas_dicotomias", [])

    # Ya detectadas en subordinacion — aqui marcamos la compuesta
    if cc and fd:
        return Hallazgo(
            tipo="falacia", operacion="fal_conjuntiva_compuesta",
            severidad=0.8,
            descripcion=f"Falacia compuesta (S48.6): causalidad circular + falsa dicotomia. Multiples operaciones defectuosas encadenadas.",
            dimensiones=["conjunciones"],
            accion_sugerida="Desmontar paso a paso: cada eslabon de la cadena es verificable?",
        )
    return None


def _fal_preposicional(e: dict) -> Hallazgo | None:
    """FALACIA PREPOSICIONAL: relacion sin justificacion.
    S48.5: relacion causa-efecto sin justificar."""
    prep = e.get("preposiciones", {})
    rotas = prep.get("conexiones_rotas", [])

    if len(rotas) > 0:
        return Hallazgo(
            tipo="falacia", operacion="fal_preposicional",
            severidad=0.6,
            descripcion=f"Falacia preposicional: {len(rotas)} relaciones sin justificacion ({', '.join(str(r) for r in rotas[:3])}). Se asume conexion que no esta probada.",
            dimensiones=["preposiciones"],
            accion_sugerida="Que PRUEBA hay de que estas cosas estan relacionadas?",
        )
    return None


# ===================================================================
# 6 ROTURAS SUJETO-PREDICADO (S48.7) — detectores individuales
# ===================================================================

def _sp_tipo1_sujeto_falso(e: dict) -> Hallazgo | None:
    """TIPO 1: SUJETO FALSO — sustantivo abstracto como agente.
    S48.7.1: 'la economia exige' — nominalizacion actuando como persona."""
    sp = e.get("sujeto_predicado", {})
    sujeto = sp.get("sujeto", "")
    if not sujeto:
        return None

    sujeto_lower = sujeto.lower().strip()

    # Detectar nominalizaciones como agentes
    sujetos_abstractos = [
        "la economia", "el mercado", "la tradicion", "la ciencia",
        "la sociedad", "el sistema", "la tecnologia", "la situacion",
        "la realidad", "la vida", "el destino", "la historia",
        "la naturaleza", "el progreso", "la evolucion", "el cambio",
        "la crisis", "la globalizacion", "la modernidad", "la cultura",
        "el gobierno", "la politica", "el capitalismo", "la democracia",
        "la educacion", "la industria", "la organizacion",
    ]

    # Tambien detectar patrones como "la X" + deverbal
    deverbales = [
        "regulacion", "gestion", "transformacion", "implementacion",
        "optimizacion", "innovacion", "disrupcion", "automatizacion",
        "digitalizacion", "planificacion", "evaluacion", "comunicacion",
    ]

    es_sujeto_falso = any(sa in sujeto_lower for sa in sujetos_abstractos)
    if not es_sujeto_falso:
        es_sujeto_falso = any(d in sujeto_lower for d in deverbales)

    verbo = e.get("verbo", {})
    verbo_nuclear = verbo.get("verbo_nuclear", "")
    # Verbos que requieren agencia real
    verbos_agentivos = [
        "exige", "decide", "quiere", "obliga", "necesita", "pide",
        "ordena", "demanda", "impone", "requiere", "determina",
        "dicta", "manda", "fuerza", "permite", "prohibe",
    ]
    verbo_agentivo = any(va in verbo_nuclear.lower() for va in verbos_agentivos) if verbo_nuclear else False

    if es_sujeto_falso and verbo_agentivo:
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo1_sujeto_falso",
            severidad=0.7,
            descripcion=f"SUJETO FALSO (S48.7.1): '{sujeto}' es una abstraccion que no puede '{verbo_nuclear}'. Se le atribuye voluntad e intencion que solo las personas tienen.",
            dimensiones=["sujeto_predicado", "verbo"],
            accion_sugerida=f"Quien REALMENTE '{verbo_nuclear}'? Nombre propio, cargo concreto.",
        )
    return None


def _sp_tipo2_predicado_desconectado(e: dict) -> Hallazgo | None:
    """TIPO 2: PREDICADO DESCONECTADO — P1 no implica P2.
    S48.7.2: 'eres ignorante, por tanto tu argumento es falso' — ad hominem."""
    sp = e.get("sujeto_predicado", {})
    conj = e.get("conjunciones", {})
    adj = e.get("adjetivos", {})

    # Detectar combinacion: adjetivo peyorativo + conector causal + conclusion
    vacios = adj.get("vacios", [])
    tipo_conexion = conj.get("tipo_conexion", "")
    agencia = sp.get("agencia", 0.5)

    # Adjetivos peyorativos/evaluativos como premises
    peyorativos = [
        "ignorante", "tonto", "estupido", "incompetente", "incapaz",
        "peligroso", "malo", "terrible", "ridiculo", "absurdo",
        "mediocre", "inutil", "irresponsable", "inmoral",
    ]
    tiene_peyorativo = any(
        any(p in str(v).lower() for p in peyorativos)
        for v in vacios
    ) if vacios else False

    if not tiene_peyorativo and adj.get("cualidades"):
        tiene_peyorativo = any(
            any(p in str(c).lower() for p in peyorativos)
            for c in adj["cualidades"]
        )

    # Si hay peyorativo + conector causal = predicado desconectado
    if tiene_peyorativo and tipo_conexion in ("causalidad", "causal", "consecuencia"):
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo2_predicado_desconectado",
            severidad=0.8,
            descripcion="PREDICADO DESCONECTADO (S48.7.2): se usa una cualidad personal como premisa para invalidar un argumento. La cualidad del sujeto NO implica falsedad del predicado.",
            dimensiones=["sujeto_predicado", "adjetivos", "conjunciones"],
            accion_sugerida="Separar: el argumento es valido o invalido INDEPENDIENTEMENTE de quien lo dice?",
        )
    return None


def _sp_tipo3_sujeto_sustituido(e: dict) -> Hallazgo | None:
    """TIPO 3: SUJETO SUSTITUIDO — se cambia el sujeto sin avisar (straw man).
    S48.7.3: responder a algo que NO se dijo."""
    sp = e.get("sujeto_predicado", {})
    sujeto = sp.get("sujeto", "")
    sust = e.get("sustantivos", {})

    # Detectar indicadores de sustitucion
    marcadores_sustitucion = [
        "lo que realmente", "en realidad", "lo que quieres decir",
        "eso significa que", "entonces tu", "o sea que",
        "lo que estas diciendo es", "lo que dices es",
        "basicamente", "en el fondo",
    ]

    texto_completo = _extraer_texto_completo(e)
    tiene_sustitucion = any(m in texto_completo for m in marcadores_sustitucion)

    if tiene_sustitucion:
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo3_sujeto_sustituido",
            severidad=0.7,
            descripcion="SUJETO SUSTITUIDO (S48.7.3): se reinterpreta lo dicho cambiando el sujeto original. Se responde a algo que NO se dijo (hombre de paja).",
            dimensiones=["sujeto_predicado"],
            accion_sugerida="Que se dijo LITERALMENTE? Repetirlo antes de responder.",
        )
    return None


def _sp_tipo4_predicado_sin_sujeto(e: dict) -> Hallazgo | None:
    """TIPO 4: PREDICADO SIN SUJETO — impersonal como argumento.
    S48.7.4: 'hay que', 'se dice que' — nadie es responsable."""
    sp = e.get("sujeto_predicado", {})
    sujeto = sp.get("sujeto", "")

    impersonales = [
        "hay que", "se dice que", "se sabe que", "es sabido",
        "es necesario", "se debe", "se deberia", "habria que",
        "conviene", "toca", "es obvio que", "esta claro que",
        "todo el mundo sabe", "es evidente", "nadie puede negar",
        "se supone", "se cree", "se piensa",
    ]

    sujeto_lower = sujeto.lower().strip() if sujeto else ""
    texto_completo = _extraer_texto_completo(e)

    es_impersonal = (
        not sujeto or
        any(imp in sujeto_lower for imp in impersonales) or
        any(imp in texto_completo for imp in impersonales)
    )

    # Solo reportar si hay un predicado fuerte sin sujeto
    verbo = e.get("verbo", {})
    fuerza = verbo.get("fuerza", 0.5)

    if es_impersonal and fuerza > 0.4:
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo4_predicado_sin_sujeto",
            severidad=0.6,
            descripcion=f"PREDICADO SIN SUJETO (S48.7.4): se usa la forma impersonal como argumento. Nadie se hace responsable de la afirmacion. '{sujeto or '(ausente)'}' no es un agente.",
            dimensiones=["sujeto_predicado"],
            accion_sugerida="QUIEN dice esto? QUIEN lo ha verificado? Nombre y apellido.",
        )
    return None


def _sp_tipo5_ecuacion_falsa(e: dict) -> Hallazgo | None:
    """TIPO 5: ECUACION FALSA — S=P sin justificacion.
    S48.7.5: 'correlacion = causalidad' — igualar sin demostrar."""
    conj = e.get("conjunciones", {})
    sust = e.get("sustantivos", {})
    sp = e.get("sujeto_predicado", {})

    # Detectar indicadores de ecuacion
    marcadores_ecuacion = [
        "es lo mismo que", "equivale a", "significa que",
        "es igual a", "no es mas que", "se reduce a",
        "es basicamente", "es simplemente",
    ]

    texto_completo = _extraer_texto_completo(e)
    tiene_ecuacion = any(m in texto_completo for m in marcadores_ecuacion)

    # Tambien detectar falsas equivalencias por estructura
    fd = conj.get("falsas_dicotomias", [])
    piezas = conj.get("piezas_sueltas", [])

    if tiene_ecuacion:
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo5_ecuacion_falsa",
            severidad=0.7,
            descripcion="ECUACION FALSA (S48.7.5): se iguala Sujeto con Predicado sin justificacion. 'X es Y' sin demostrar por que son equivalentes.",
            dimensiones=["sujeto_predicado", "conjunciones"],
            accion_sugerida="En que se DIFERENCIAN estos dos conceptos? Que pierde la ecuacion?",
        )
    return None


def _sp_tipo6_subordinada_disfrazada(e: dict) -> Hallazgo | None:
    """TIPO 6: SUBORDINADA DISFRAZADA DE PRINCIPAL.
    S48.7.6: condicional como amenaza, causal como prueba."""
    conj = e.get("conjunciones", {})
    tipo_conexion = conj.get("tipo_conexion", "")

    # Detectar subordinadas presentadas como principales
    marcadores_amenaza = [
        "si no", "o si no", "de lo contrario", "sino",
        "a menos que", "a no ser que",
    ]
    marcadores_prueba_causal = [
        "porque si", "ya que es obvio", "puesto que todos saben",
        "dado que es evidente",
    ]

    texto_completo = _extraer_texto_completo(e)

    tiene_amenaza = any(m in texto_completo for m in marcadores_amenaza)
    tiene_prueba_circular = any(m in texto_completo for m in marcadores_prueba_causal)

    # Condicional usado como amenaza
    if tiene_amenaza and tipo_conexion in ("condicion", "condicional", "condicionality"):
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo6_subordinada_disfrazada",
            severidad=0.6,
            descripcion="SUBORDINADA DISFRAZADA (S48.7.6): una condicion se presenta como amenaza. La subordinada condicional usurpa el rol de oracion principal.",
            dimensiones=["conjunciones", "sujeto_predicado"],
            accion_sugerida="Es realmente una condicion logica o es una amenaza encubierta?",
        )

    # Causal usado como prueba autorreferencial
    if tiene_prueba_circular and tipo_conexion in ("causalidad", "causal"):
        return Hallazgo(
            tipo="falacia", operacion="sp_tipo6_subordinada_disfrazada",
            severidad=0.7,
            descripcion="SUBORDINADA DISFRAZADA (S48.7.6): una causal autorreferencial se presenta como prueba. 'Porque es obvio' no es una causa — es una peticion de principio.",
            dimensiones=["conjunciones", "sujeto_predicado"],
            accion_sugerida="Eliminar el 'porque' y ver si la causa se sostiene sola.",
        )

    return None


# ===================================================================
# 9 MODOS DE PERCEPCION (S6)
# Cada modo es una forma de observar. Lo AUSENTE = punto ciego.
# ===================================================================

# Vocabulario indicador por modo
_VOCAB_MODOS = {
    "PROCESO": {
        "pregunta": "Que ocurre?",
        "indicadores": [
            "retroalimentacion", "regulacion", "ciclo", "flujo", "dinamica",
            "proceso", "feedback", "iteracion", "evolucion", "transformacion",
            "transicion", "desarrollo", "progresion", "secuencia", "etapa",
            "fase", "paso", "procedimiento", "mecanismo", "metabolismo",
            "crecimiento", "decrecimiento", "aceleracion", "desaceleracion",
        ],
    },
    "PROPIEDAD": {
        "pregunta": "Como es?",
        "indicadores": [
            "robustez", "simetria", "fragilidad", "rigidez", "flexibilidad",
            "complejidad", "simplicidad", "elegancia", "densidad", "intensidad",
            "calidad", "eficiencia", "estabilidad", "coherencia", "consistencia",
            "transparencia", "opacidad", "solidez", "ligereza", "resistencia",
            "resiliencia", "viscosidad", "elasticidad", "dureza",
        ],
    },
    "RELACION": {
        "pregunta": "Que interactua?",
        "indicadores": [
            "equilibrio", "gradiente", "sinergia", "tension", "conflicto",
            "cooperacion", "competencia", "dependencia", "interdependencia",
            "correlacion", "causalidad", "reciprocidad", "jerarquia",
            "red", "vinculo", "nexo", "interaccion", "conexion",
            "acoplamiento", "desacoplamiento", "simbiosis", "parasitismo",
        ],
    },
    "FORMA": {
        "pregunta": "Donde esta?",
        "indicadores": [
            "hub", "campo", "atractor", "nicho", "topologia",
            "estructura", "patron", "configuracion", "arquitectura",
            "mapa", "territorio", "frontera", "limite", "contorno",
            "centro", "periferia", "nodo", "cluster", "red",
            "espacio", "posicion", "geometria", "simetria",
        ],
    },
    "LEY": {
        "pregunta": "Que se cumple?",
        "indicadores": [
            "modus ponens", "contradiccion", "ley", "principio", "axioma",
            "teorema", "regla", "norma", "logica", "deduccion",
            "inferencia", "conclusion", "premisa", "implicacion",
            "necesidad", "suficiencia", "invariante", "constante",
            "determinismo", "probabilidad", "certeza",
        ],
    },
    "AGENTE": {
        "pregunta": "Quien opera?",
        "indicadores": [
            "observador", "fitness", "agente", "actor", "operador",
            "responsable", "decisor", "ejecutor", "facilitador",
            "catalizador", "inhibidor", "regulador", "controlador",
            "mediador", "intermediario", "lider", "seguidor",
            "usuario", "cliente", "proveedor", "stakeholder",
        ],
    },
    "ESTADO": {
        "pregunta": "En que condicion?",
        "indicadores": [
            "crisis", "latencia", "saturacion", "equilibrio",
            "estancamiento", "bloqueo", "paralisis", "inercia",
            "reposo", "activacion", "excitacion", "agotamiento",
            "sobrecarga", "deficit", "superavit", "optimo",
            "suboptimo", "degradacion", "recuperacion", "homeostasis",
        ],
        "hueco": True,  # Marcado como HUECO en framework original
    },
    "EVENTO": {
        "pregunta": "Que acaba de pasar?",
        "indicadores": [
            "ruptura", "bifurcacion", "emergencia", "colapso",
            "irrupcion", "quiebre", "salto", "discontinuidad",
            "accidente", "incidente", "hito", "punto de inflexion",
            "catastrofe", "descubrimiento", "revelacion", "shock",
            "trigger", "detonante", "catalizador", "precipitante",
        ],
    },
    "POTENCIAL": {
        "pregunta": "Que podria pasar?",
        "indicadores": [
            "capacidad", "vulnerabilidad", "oportunidad", "riesgo",
            "amenaza", "posibilidad", "probabilidad", "escenario",
            "proyeccion", "tendencia", "potencial", "latente",
            "emergente", "incipiente", "inminente", "previsible",
            "imprevisible", "contingencia", "reserva", "margen",
        ],
        "hueco": True,  # Marcado como HUECO en framework original
    },
}


def _detectar_modos_percepcion(e: dict) -> tuple[list[str], list[Hallazgo]]:
    """Detecta que modos de percepcion (S6) estan PRESENTES y cuales AUSENTES.
    Devuelve (modos_presentes, hallazgos_por_ausencia)."""
    texto = _extraer_texto_completo(e).lower()
    # Tambien examinar campos de estructura directamente
    todas_palabras = set(texto.split())

    # Anadir palabras de campos especificos
    sust = e.get("sustantivos", {})
    for p in sust.get("perdido", []):
        todas_palabras.update(str(p).lower().split())
    caps = sust.get("capsulas", {})
    if caps.get("palabra"):
        todas_palabras.add(str(caps["palabra"]).lower())

    adj = e.get("adjetivos", {})
    for c in adj.get("cualidades", []):
        todas_palabras.update(str(c).lower().split())

    modos_presentes = []
    modos_ausentes = []
    hallazgos = []

    for modo, config in _VOCAB_MODOS.items():
        # Buscar si hay al menos un indicador presente
        presente = any(
            ind in texto or ind in todas_palabras
            for ind in config["indicadores"]
        )

        if presente:
            modos_presentes.append(modo)
        else:
            modos_ausentes.append(modo)
            severidad = 0.5 if config.get("hueco") else 0.3
            hallazgos.append(Hallazgo(
                tipo="modo_ausente", operacion=f"modo_{modo.lower()}",
                severidad=severidad,
                descripcion=f"Modo de percepcion AUSENTE: {modo} ({config['pregunta']}). {'[HUECO critico] ' if config.get('hueco') else ''}No se observa desde este angulo — punto ciego perceptivo.",
                dimensiones=["modos_percepcion"],
                accion_sugerida=f"Explorar: {config['pregunta']}",
            ))

    return modos_presentes, hallazgos


# ===================================================================
# RESOLUCION LUMINICA AVANZADA (S41)
# Vela / Habitacion / Estadio
# ===================================================================

def _calcular_resolucion_avanzada(e: dict) -> tuple[float, str, list[Hallazgo]]:
    """Resolucion luminica avanzada (S41).
    Cuenta operaciones EXACTAS ejecutadas vs posibles.
    - VELA (1-2 ops): sujeto + predicado solamente
    - HABITACION (3-5 ops): + algunos complementos/subordinacion
    - ESTADIO (6+ ops): iluminacion completa
    Cada operacion ausente = una 'luz apagada' especifica.

    Devuelve (score, nivel, hallazgos).
    """
    ops_presentes = []
    ops_ausentes = []
    preguntas_por_luz = []

    # Checklist de 7 dimensiones + que pregunta enciende cada luz
    checks = [
        ("sustantivos", e.get("sustantivos", {}).get("capsulas", {}).get("palabra"),
         "QUE es? (sustantivar = nombrar la cosa)"),
        ("sujeto_predicado", e.get("sujeto_predicado", {}).get("sujeto"),
         "QUIEN lo hace? (predicar = asignar agente a accion)"),
        ("adjetivos", e.get("adjetivos", {}).get("cualidades"),
         "COMO es? (adjetivar = cualificar)"),
        ("adverbios", e.get("adverbios", {}).get("modo_explicito"),
         "DE QUE MANERA? (adverbializar = describir modo)"),
        ("preposiciones", e.get("preposiciones", {}).get("relaciones"),
         "EN QUE NIVEL? (preposicionar = situar en capa logica)"),
        ("conjunciones", e.get("conjunciones", {}).get("tipo_conexion"),
         "QUE RELACION HAY? (conjuntar = conectar partes)"),
        ("verbo", e.get("verbo", {}).get("verbo_nuclear"),
         "QUE ACCION? (verbalizar = activar/ejecutar)"),
    ]

    for nombre, valor, pregunta in checks:
        if valor:
            ops_presentes.append(nombre)
        else:
            ops_ausentes.append(nombre)
            preguntas_por_luz.append(pregunta)

    n_ops = len(ops_presentes)
    score = round(n_ops / 7.0, 2)

    # Determinar nivel
    if n_ops <= 2:
        nivel = "vela"
    elif n_ops <= 5:
        nivel = "habitacion"
    else:
        nivel = "estadio"

    hallazgos = []

    # Reportar luces apagadas
    if ops_ausentes:
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="resolucion_luminica",
            severidad=max(0.3, 0.8 - n_ops * 0.1),
            descripcion=f"Resolucion luminica: {nivel.upper()} ({n_ops}/7 operaciones). {len(ops_ausentes)} luz(es) apagada(s): {', '.join(ops_ausentes)}.",
            dimensiones=ops_ausentes,
            accion_sugerida=preguntas_por_luz[0] if preguntas_por_luz else "",
        ))

    # Si es vela, alerta especial
    if nivel == "vela":
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="resolucion_luminica_critica",
            severidad=0.8,
            descripcion=f"VELA (S41): solo {n_ops} operacion(es) ejecutada(s). Casi toda la experiencia esta a oscuras. Se necesitan al menos 3 operaciones mas para iluminar lo basico.",
            dimensiones=ops_ausentes,
            accion_sugerida="Encender luces: " + "; ".join(preguntas_por_luz[:3]),
        ))

    return score, nivel, hallazgos


# ===================================================================
# 3 LENTES SER/ESTAR/SEGUIR (S2.2)
# Condiciones de VIDA en el sistema
# ===================================================================

_VOCAB_LENTES = {
    "SALUD": {
        "lente": "ESTAR",
        "pregunta": "Como esta?",
        "indicadores": [
            "esta", "estado", "condicion", "situacion", "salud",
            "bienestar", "malestar", "dolor", "sintoma", "diagnostico",
            "crisis", "estable", "inestable", "funciona", "falla",
            "roto", "sano", "enfermo", "critico", "optimo",
            "saturado", "agotado", "bloqueado", "activo", "pasivo",
            "rendimiento", "performance", "metrica", "indicador",
        ],
    },
    "SENTIDO": {
        "lente": "SER",
        "pregunta": "Que es?",
        "indicadores": [
            "es", "identidad", "esencia", "naturaleza", "proposito",
            "mision", "vision", "valor", "significado", "sentido",
            "razon de ser", "fundamento", "nucleo", "alma",
            "vocacion", "definicion", "concepto", "principio",
            "filosof", "ontolog", "ser", "ente", "existencia",
        ],
    },
    "CONTINUIDAD": {
        "lente": "SEGUIR",
        "pregunta": "Sigue siendo?",
        "indicadores": [
            "sigue", "continua", "persiste", "mantiene", "sostiene",
            "dura", "permanece", "resiste", "sobrevive", "perdura",
            "sostenible", "sustentable", "viable", "continuidad",
            "futuro", "proyeccion", "horizonte", "legado",
            "herencia", "tradicion", "evolucion", "adaptacion",
            "largo plazo", "recurrente", "sistematico",
        ],
    },
}


def _detectar_lentes(e: dict) -> tuple[list[str], list[Hallazgo]]:
    """Detecta si el texto cubre las 3 condiciones de VIDA (S2.2).
    SALUD (ESTAR), SENTIDO (SER), CONTINUIDAD (SEGUIR).
    Si alguna falta -> punto ciego sistemico.

    Devuelve (lentes_cubiertas, hallazgos).
    """
    texto = _extraer_texto_completo(e).lower()

    lentes_cubiertas = []
    lentes_ausentes = []
    hallazgos = []

    for nombre, config in _VOCAB_LENTES.items():
        presente = any(ind in texto for ind in config["indicadores"])

        if presente:
            lentes_cubiertas.append(nombre)
        else:
            lentes_ausentes.append(nombre)

    # Reportar lentes ausentes
    for nombre in lentes_ausentes:
        config = _VOCAB_LENTES[nombre]
        hallazgos.append(Hallazgo(
            tipo="lente_ausente", operacion=f"lente_{config['lente'].lower()}",
            severidad=0.6,
            descripcion=f"Lente AUSENTE: {nombre} ({config['lente']}) — {config['pregunta']} Sin esta lente, una condicion de vida del sistema esta invisible.",
            dimensiones=["lentes"],
            accion_sugerida=f"Explorar la lente {config['lente']}: {config['pregunta']}",
        ))

    # Si faltan 2+ lentes, alerta critica
    if len(lentes_ausentes) >= 2:
        faltantes = [f"{n} ({_VOCAB_LENTES[n]['lente']})" for n in lentes_ausentes]
        hallazgos.append(Hallazgo(
            tipo="punto_ciego", operacion="lentes_sistemico",
            severidad=0.8,
            descripcion=f"Punto ciego sistemico (S2.2): faltan {len(lentes_ausentes)}/3 lentes vitales ({', '.join(faltantes)}). El sistema no puede verse completo.",
            dimensiones=["lentes"],
            accion_sugerida="Tres preguntas minimas: Que es? Como esta? Sigue siendo?",
        ))

    return lentes_cubiertas, hallazgos


# ===================================================================
# OPERABILIDAD INTER-CAPA (S10) — CREENCIAS
# ===================================================================

def _detectar_creencias_ocultas(e: dict) -> list[Hallazgo]:
    """Detecta si las CREENCIAS (S10, S3) condicionan otras capas invisiblemente.
    CREENCIAS = capa mas peligrosa. Puede anular cualquier otra."""
    hallazgos = []
    texto = _extraer_texto_completo(e).lower()
    prep = e.get("preposiciones", {})
    sp = e.get("sujeto_predicado", {})
    nivel = prep.get("nivel_logico", "").lower()

    # Marcadores de creencia operando como ley
    marcadores_creencia = [
        "siempre ha sido asi", "es asi", "no se puede", "es imposible",
        "nunca funciona", "todos saben", "nadie puede", "es obvio",
        "asi son las cosas", "no hay alternativa", "es lo que hay",
        "no queda otra", "siempre", "nunca", "jamas",
        "todo el mundo", "nadie", "es natural",
        "es logico", "es normal", "es inevitable",
    ]

    creencias_detectadas = [m for m in marcadores_creencia if m in texto]

    if creencias_detectadas:
        hallazgos.append(Hallazgo(
            tipo="creencia_oculta", operacion="inter_capa_creencias",
            severidad=0.7,
            descripcion=f"CREENCIAS condicionando (S10): {len(creencias_detectadas)} creencia(s) operando como ley ({', '.join(creencias_detectadas[:3])}). La capa de creencias es la mas peligrosa: puede anular cualquier otra capa sin ser visible.",
            dimensiones=["creencias", "inter_capa"],
            accion_sugerida="Es un HECHO o una CREENCIA? Que pasaria si no fuera verdad?",
        ))

    # Detectar creencias en nivel de identidad (mas peligroso)
    if nivel in ("identidad", "identity") and creencias_detectadas:
        hallazgos.append(Hallazgo(
            tipo="creencia_oculta", operacion="inter_capa_identidad",
            severidad=0.9,
            descripcion=f"CREENCIA en nivel IDENTIDAD (S10): maximo peligro. Una creencia en nivel identidad ('soy X') condiciona TODAS las capas inferiores (capacidad, conducta, entorno) sin dejar espacio para el cambio.",
            dimensiones=["creencias", "preposiciones", "inter_capa"],
            accion_sugerida="Distinguir: SOY X o ESTOY HACIENDO X? Identidad vs conducta.",
        ))

    return hallazgos


# ===================================================================
# ANALISIS DE POSICION CONJUNTIVA (S42.6)
# ===================================================================

def _analizar_posicion_conjuntiva(e: dict) -> list[Hallazgo]:
    """Analiza la posicion de las ideas respecto a los conectores (S42.6).
    - Lo que va ANTES de 'pero' = lo que funciona (cuestionado)
    - Lo que va DESPUES de 'pero' = la tension que contradice
    - Y = sinergia
    - PORQUE = causalidad
    - AUNQUE = concesion
    - SI = condicionalidad
    """
    hallazgos = []
    conj = e.get("conjunciones", {})
    tipo_conexion = conj.get("tipo_conexion", "")
    antes = conj.get("antes", "")
    despues = conj.get("despues", "")
    texto = _extraer_texto_completo(e).lower()

    if not tipo_conexion:
        return hallazgos

    tipo_lower = tipo_conexion.lower()

    # PERO / oposicion — lo de antes queda cuestionado
    if tipo_lower in ("oposicion", "adversativa", "pero"):
        if antes and despues:
            hallazgos.append(Hallazgo(
                tipo="posicion_conjuntiva", operacion="conjuncion_pero",
                severidad=0.4,
                descripcion=f"PERO (S42.6): lo que va antes ('{_truncar(str(antes), 60)}') queda cuestionado por lo que va despues ('{_truncar(str(despues), 60)}'). La tension real esta DESPUES del 'pero'.",
                dimensiones=["conjunciones"],
                accion_sugerida="Que pesa mas: lo de antes o lo de despues del 'pero'?",
            ))

    # Y — sinergia, verificar si realmente suman
    elif tipo_lower in ("adicion", "copulativa", "y"):
        piezas = conj.get("piezas_sueltas", [])
        if len(piezas) > 2:
            hallazgos.append(Hallazgo(
                tipo="posicion_conjuntiva", operacion="conjuncion_y",
                severidad=0.3,
                descripcion=f"Y (S42.6): {len(piezas)} elementos sumados. La Y es conmutativa (el orden no importa). Verificar: realmente suman o solo se yuxtaponen?",
                dimensiones=["conjunciones"],
                accion_sugerida="Estos elementos realmente se POTENCIAN entre si, o solo estan juntos?",
            ))

    # PORQUE — causalidad, verificar direccion
    elif tipo_lower in ("causalidad", "causal", "porque"):
        cc = conj.get("causalidades_circulares", [])
        if not cc:
            hallazgos.append(Hallazgo(
                tipo="posicion_conjuntiva", operacion="conjuncion_porque",
                severidad=0.3,
                descripcion=f"PORQUE (S42.6): relacion causal detectada. PORQUE NO es conmutativa — el orden SI importa. Verificar: la causa es ANTERIOR al efecto?",
                dimensiones=["conjunciones"],
                accion_sugerida="Invertir: si intercambio causa y efecto, sigue siendo valido?",
            ))

    # AUNQUE — concesion, la concesion se acepta pero no modifica la conclusion
    elif tipo_lower in ("concesion", "concesiva", "aunque"):
        hallazgos.append(Hallazgo(
            tipo="posicion_conjuntiva", operacion="conjuncion_aunque",
            severidad=0.4,
            descripcion=f"AUNQUE (S42.6): se concede algo pero no modifica la conclusion. La concesion puede ser una forma de neutralizar una objecion valida.",
            dimensiones=["conjunciones"],
            accion_sugerida="La concesion es real o se usa para desactivar una objecion legitima?",
        ))

    # SI — condicionalidad
    elif tipo_lower in ("condicion", "condicional", "si"):
        hallazgos.append(Hallazgo(
            tipo="posicion_conjuntiva", operacion="conjuncion_si",
            severidad=0.4,
            descripcion=f"SI (S42.6): condicion detectada. Verificar: la condicion es VERIFICABLE? Se puede comprobar si se cumple o no?",
            dimensiones=["conjunciones"],
            accion_sugerida="La condicion es verificable? Que pasa si NO se cumple?",
        ))

    # ALTERNATIVA — detectar si las alternativas son reales
    elif tipo_lower in ("alternativa", "disyuntiva", "o"):
        fd = conj.get("falsas_dicotomias", [])
        if not fd:
            hallazgos.append(Hallazgo(
                tipo="posicion_conjuntiva", operacion="conjuncion_o",
                severidad=0.3,
                descripcion=f"O (S42.6): alternativa presentada. Verificar: son TODAS las opciones o hay mas?",
                dimensiones=["conjunciones"],
                accion_sugerida="Que opciones faltan? Y si no es ni A ni B?",
            ))

    # AUSENCIA de conexion — detectar cuando deberia haber conector
    if tipo_lower in ("ausencia_conexion", "ausencia"):
        hallazgos.append(Hallazgo(
            tipo="posicion_conjuntiva", operacion="conjuncion_ausencia",
            severidad=0.5,
            descripcion=f"AUSENCIA de conexion (S42.6): piezas presentadas sin relacion explicita. La relacion implicita puede esconder la estructura real del argumento.",
            dimensiones=["conjunciones"],
            accion_sugerida="Cual es la relacion real: suman (Y), contrastan (PERO), causan (PORQUE)?",
        ))

    return hallazgos


# ===================================================================
# CRUCES ENTRE OPERACIONES (S42.6, reglas de cruce originales)
# ===================================================================

def _cruce_agencia_modo(e: dict) -> Hallazgo | None:
    """Agencia diluida + modo activo = contradiccion."""
    sp = e.get("sujeto_predicado", {})
    adv = e.get("adverbios", {})
    if sp.get("agencia", 0.5) < 0.4 and adv.get("explicitud", 0.5) > 0.6:
        return Hallazgo(
            tipo="contradiccion", operacion="cruce_predicacion_complementacion",
            severidad=0.8,
            descripcion=f"Predicacion pasiva + Complementacion activa: se dice COMO hacer algo sin definir QUIEN lo hace. Las dos operaciones se contradicen.",
            dimensiones=["sujeto_predicado", "adverbios"],
            accion_sugerida="Primero quien, luego como.",
        )
    return None


def _cruce_nivel_accion(e: dict) -> Hallazgo | None:
    """Nivel logico alto + accion operativa = colapso."""
    prep = e.get("preposiciones", {})
    verbo = e.get("verbo", {})
    nivel = prep.get("nivel_logico", "").lower()
    fuerza = verbo.get("fuerza", 0.5)
    niveles_altos = ["identidad", "meta", "creencia"]

    if any(n in nivel for n in niveles_altos) and fuerza > 0.7:
        return Hallazgo(
            tipo="colapso", operacion="cruce_subordinacion_transitividad",
            severidad=0.7,
            descripcion=f"Subordinacion meta + Transitividad operativa: se piensa en nivel '{nivel}' pero se actua en nivel conducta. Salto sin escalera.",
            dimensiones=["preposiciones", "verbo"],
            accion_sugerida="Cual es el paso intermedio entre la vision y la accion?",
        )
    return None


def _cruce_conexiones_agencia(e: dict) -> Hallazgo | None:
    """Logica rota + agencia clara = falsa confianza."""
    prep = e.get("preposiciones", {})
    sp = e.get("sujeto_predicado", {})
    rotas = prep.get("conexiones_rotas", [])
    agencia = sp.get("agencia", 0.5)

    if len(rotas) > 0 and agencia > 0.7:
        return Hallazgo(
            tipo="patron", operacion="cruce_conexion_predicacion",
            severidad=0.7,
            descripcion=f"Conexion rota + Predicacion fuerte: alta confianza ({agencia:.1f}) actuando sobre logica con {len(rotas)} conexiones rotas. Falsa confianza.",
            dimensiones=["preposiciones", "sujeto_predicado"],
            accion_sugerida="Verificar las premisas ANTES de actuar.",
        )
    return None


def _cruce_compresion_conexiones(e: dict) -> Hallazgo | None:
    """Compresion alta (sustantivizacion) + conexiones sueltas = estructura oculta."""
    sust = e.get("sustantivos", {})
    conj = e.get("conjunciones", {})
    perdido = sust.get("perdido", [])
    piezas_sueltas = conj.get("piezas_sueltas", [])

    if len(perdido) > 2 and len(piezas_sueltas) > 1:
        return Hallazgo(
            tipo="patron", operacion="cruce_transformacion_conexion",
            severidad=0.6,
            descripcion=f"Compresion + Fragmentacion: {len(perdido)} elementos comprimidos en capsulas + {len(piezas_sueltas)} piezas sin conectar. La estructura real esta oculta tras las nominalizaciones.",
            dimensiones=["sustantivos", "conjunciones"],
            accion_sugerida="Descomprimir primero (quien-hace-que), luego conectar.",
        )
    return None


def _cruce_modos_ocultos_colapsos(e: dict) -> Hallazgo | None:
    """Modos ocultos + colapsos de nivel = operar mal sin saberlo."""
    adv = e.get("adverbios", {})
    prep = e.get("preposiciones", {})
    ocultos = adv.get("modos_ocultos", [])
    colapsos = prep.get("colapsos", [])

    if len(ocultos) > 0 and len(colapsos) > 0:
        return Hallazgo(
            tipo="patron", operacion="cruce_complementacion_subordinacion",
            severidad=0.7,
            descripcion=f"Modos ocultos + Colapsos: se opera de forma no declarada ({len(ocultos)} modos ocultos) Y se mezclan niveles logicos ({len(colapsos)} colapsos). Se hace algo mal sin poder verlo.",
            dimensiones=["adverbios", "preposiciones"],
            accion_sugerida="Hacer explicito el modo de operar Y separar los niveles.",
        )
    return None


def _cruce_verbo_vacio_adjetivos_vacios(e: dict) -> Hallazgo | None:
    """Verbo debil + adjetivos vacios = discurso sin sustancia."""
    verbo = e.get("verbo", {})
    adj = e.get("adjetivos", {})
    fuerza = verbo.get("fuerza", 0.5)
    vacios = adj.get("vacios", [])

    if fuerza < 0.3 and len(vacios) > 1:
        return Hallazgo(
            tipo="patron", operacion="cruce_transitividad_modificacion",
            severidad=0.6,
            descripcion=f"Verbo debil ({fuerza:.1f}) + {len(vacios)} adjetivos vacios: ni la accion ni las cualidades tienen contenido real. Discurso sin sustancia.",
            dimensiones=["verbo", "adjetivos"],
            accion_sugerida="Que accion CONCRETA produce que resultado MEDIBLE?",
        )
    return None


# ===================================================================
# ORACION DEL SISTEMA (S2.3)
# ===================================================================

def _construir_oracion_sistema(e: dict) -> str:
    """Construye la 'oracion del sistema' — diagnostico completo en una frase.
    S2.3: El sistema [SUJETO] esta/es/opera/con/debe [cada capa]."""
    sp = e.get("sujeto_predicado", {})
    adj = e.get("adjetivos", {})
    adv = e.get("adverbios", {})
    verbo = e.get("verbo", {})
    prep = e.get("preposiciones", {})

    sujeto = sp.get("sujeto", "el sistema")
    cualidades = adj.get("cualidades", [])
    modo = adv.get("modo_explicito", "")
    v_nuclear = verbo.get("verbo_nuclear", "")
    v_vida = verbo.get("verbo_vida", "")
    nivel = prep.get("nivel_logico", "")

    partes = [f"'{sujeto}'"]

    if cualidades:
        partes.append(f"es {', '.join(str(c) for c in cualidades[:3])}")

    if v_nuclear:
        partes.append(f"hace: {v_nuclear}")

    if modo:
        partes.append(f"de forma: {modo}")

    if v_vida:
        partes.append(f"verbo vital: {v_vida}")

    if nivel:
        partes.append(f"opera en nivel: {nivel}")

    return " | ".join(partes)


# ===================================================================
# UTILIDADES
# ===================================================================

def _extraer_texto_completo(e: dict) -> str:
    """Extrae todo el texto disponible de la estructura para busquedas."""
    partes = []

    # sujeto_predicado
    sp = e.get("sujeto_predicado", {})
    for campo in ("sujeto", "predicado", "responsabilidad", "texto"):
        if sp.get(campo):
            partes.append(str(sp[campo]))

    # sustantivos
    sust = e.get("sustantivos", {})
    caps = sust.get("capsulas", {})
    if caps.get("palabra"):
        partes.append(str(caps["palabra"]))
    for p in sust.get("perdido", []):
        partes.append(str(p))

    # adjetivos
    adj = e.get("adjetivos", {})
    for c in adj.get("cualidades", []):
        partes.append(str(c))
    for v in adj.get("vacios", []):
        partes.append(str(v))

    # adverbios
    adv = e.get("adverbios", {})
    if adv.get("modo_explicito"):
        partes.append(str(adv["modo_explicito"]))
    for m in adv.get("modos_ocultos", []):
        partes.append(str(m))

    # verbo
    verbo = e.get("verbo", {})
    if verbo.get("verbo_nuclear"):
        partes.append(str(verbo["verbo_nuclear"]))
    if verbo.get("verbo_vida"):
        partes.append(str(verbo["verbo_vida"]))

    # conjunciones
    conj = e.get("conjunciones", {})
    if conj.get("tipo_conexion"):
        partes.append(str(conj["tipo_conexion"]))
    for ps in conj.get("piezas_sueltas", []):
        partes.append(str(ps))
    if conj.get("antes"):
        partes.append(str(conj["antes"]))
    if conj.get("despues"):
        partes.append(str(conj["despues"]))

    # preposiciones
    prep = e.get("preposiciones", {})
    if prep.get("nivel_logico"):
        partes.append(str(prep["nivel_logico"]))
    for r in prep.get("relaciones", []):
        partes.append(str(r))
    for c in prep.get("colapsos", []):
        partes.append(str(c))
    for cr in prep.get("conexiones_rotas", []):
        partes.append(str(cr))

    # texto raw si existe
    if e.get("texto"):
        partes.append(str(e["texto"]))
    if e.get("texto_original"):
        partes.append(str(e["texto_original"]))

    return " ".join(partes).lower()


def _truncar(s: str, max_len: int = 80) -> str:
    """Trunca un string a max_len caracteres."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


# ===================================================================
# DETECTORES DE INVARIANTES L0 (L0_adn_modelo_omni.md)
#
# 7 invariantes que detectan violaciones en COMO alguien piensa
# sobre sistemas.  Codigo puro, $0, <1ms cada uno.
# ===================================================================

def _inv_simultaneidad(e: dict) -> Hallazgo | None:
    """SIMULTANEIDAD: detecta cuando se introduce una falsa secuencia temporal
    donde hay coexistencia simultanea.  'Primero X, luego Y' cuando X e Y
    son escalas que coexisten."""
    texto = _extraer_texto_completo(e)
    patrones = [
        r"primero\b.*\bluego\b",
        r"antes\s+de\b.*\bdespues\b",
        r"cuando\s+termine\b.*\bhar[eé]\b",
        r"una\s+vez\s+que\b.*\bentonces\b",
        r"paso\s+1\b.*\bpaso\s+2\b",
    ]
    for p in patrones:
        if re.search(p, texto):
            return Hallazgo(
                tipo="colapso", operacion="inv_simultaneidad",
                severidad=0.7,
                descripcion="Falsa secuencia temporal: se tratan como pasos sucesivos escalas que coexisten simultaneamente. L0: las escalas no esperan turno.",
                dimensiones=["sujeto_predicado", "conjunciones"],
                accion_sugerida="Estas cosas ocurren A LA VEZ, no una despues de otra. Que pasa si las miras como simultaneas?",
            )
    return None


def _inv_fractalidad(e: dict) -> Hallazgo | None:
    """FRACTALIDAD: detecta cuando se asume un 'nivel fundamental' o
    'nivel maximo'.  No hay piso ni techo — la estructura se repite
    a todas las escalas."""
    texto = _extraer_texto_completo(e)
    patrones = [
        r"nivel\s+fundamental",
        r"\bla\s+base\b",
        r"lo\s+m[aá]s\s+importante",
        r"por\s+encima\s+de\s+todo",
        r"en\s+[uú]ltima\s+instancia",
        r"el\s+origen\s+de\s+todo",
        r"la\s+ra[ií]z\s+del\s+problema",
    ]
    for p in patrones:
        if re.search(p, texto):
            return Hallazgo(
                tipo="punto_ciego", operacion="inv_fractalidad",
                severidad=0.6,
                descripcion="Suposicion de nivel fundamental o maximo: se asume un piso o techo que no existe. L0: la estructura es fractal — no hay 'lo mas basico' ni 'lo mas alto'.",
                dimensiones=["sustantivos", "preposiciones"],
                accion_sugerida="Si bajas un nivel mas, que hay? Y si subes otro? El patron se repite.",
            )
    return None


def _inv_observador_sistema(e: dict) -> Hallazgo | None:
    """OBSERVADOR=SISTEMA: detecta cuando alguien se posiciona como externo
    al sistema que describe.  El observador ES parte del sistema."""
    texto = _extraer_texto_completo(e)
    sp = e.get("sujeto_predicado", {})
    sujeto = (sp.get("sujeto", "") or "").lower()

    # Marcadores de externalidad
    marcadores_externos = [
        r"\bdesde\s+fuera\b",
        r"\bel\s+usuario\b",
        r"\blos\s+clientes\b",
        r"\bellos\s+(hacen|piensan|quieren|necesitan)\b",
        r"\bel\s+sistema\s+(hace|tiene|necesita)\b",
        r"\bla\s+organizaci[oó]n\s+(debe|tiene|necesita)\b",
    ]

    for p in marcadores_externos:
        if re.search(p, texto):
            return Hallazgo(
                tipo="patron", operacion="inv_observador_sistema",
                severidad=0.7,
                descripcion="Observador externo: se describe el sistema desde fuera, como si uno no fuera parte de el. L0: observador = sistema. Tu ERES lo que describes.",
                dimensiones=["sujeto_predicado"],
                accion_sugerida="Tu estas DENTRO de esto. Como cambia el analisis si te incluyes?",
            )

    # Sujeto que trata al sistema como objeto externo
    if sujeto and any(x in sujeto for x in ["el sistema", "la empresa", "el mercado", "la industria"]):
        agencia = sp.get("agencia", 0.5)
        if agencia > 0.3:  # habla del sistema como agente independiente
            return Hallazgo(
                tipo="patron", operacion="inv_observador_sistema",
                severidad=0.5,
                descripcion=f"Sujeto externalizado: '{sujeto}' se trata como ente separado. L0: no hay 'afuera' — eres parte del sistema que describes.",
                dimensiones=["sujeto_predicado"],
                accion_sugerida="Reescribe esto en primera persona. Que cambia?",
            )
    return None


def _inv_convergencia(e: dict) -> Hallazgo | None:
    """CONVERGENCIA EN INVARIANTES: detecta cuando se confunden PARTES
    (herramientas, tecnologias) con INVARIANTES (lo que hace emerger el sistema).
    'Necesitamos X herramienta' confunde el medio con el invariante."""
    texto = _extraer_texto_completo(e)
    patrones = [
        r"necesitamos\s+\w+",
        r"hay\s+que\s+usar\s+\w+",
        r"sin\s+\w+\s+no\s+(se\s+)?puede",
        r"la\s+soluci[oó]n\s+es\s+\w+",
        r"lo\s+que\s+falta\s+es\s+\w+",
        r"implementar\s+\w+\s+(para|y)\b",
    ]

    sust = e.get("sustantivos", {})
    caps = sust.get("capsulas", {})
    palabra = (caps.get("palabra", "") or "").lower()

    for p in patrones:
        if re.search(p, texto):
            desc_extra = f" (comprimido en '{palabra}')" if palabra else ""
            return Hallazgo(
                tipo="falacia", operacion="inv_convergencia",
                severidad=0.6,
                descripcion=f"Parte confundida con invariante: se identifica una herramienta/parte especifica como necesaria{desc_extra}. L0: las partes cambian, los invariantes permanecen. Que FUNCION cumple eso?",
                dimensiones=["sustantivos", "verbo"],
                accion_sugerida="Eso es una PARTE. Cual es el invariante que la hace necesaria? La funcion, no la forma.",
            )
    return None


def _inv_escalas(e: dict) -> Hallazgo | None:
    """SISTEMA/PARTE = ESCALAS: detecta cuando se mezcla la escala de
    ejecucion (N-1) con la de optimizacion (N).  'Mientras hago X tambien
    optimizo X' = colapso de escalas."""
    texto = _extraer_texto_completo(e)
    patrones = [
        r"mientras\s+(hago|hacemos)\s+\w+.*\btambi[eé]n\s+(optimiz|mejor|revis)",
        r"al\s+mismo\s+tiempo\s+(ejecut|hac|implement).*\b(diseñ|planific|evalu)",
        r"hacer\s+y\s+(pensar|evaluar|medir)",
        r"ejecutar\s+y\s+(optimizar|diseñar|planificar)",
    ]

    for p in patrones:
        if re.search(p, texto):
            return Hallazgo(
                tipo="colapso", operacion="inv_escalas",
                severidad=0.7,
                descripcion="Colapso de escalas: se mezcla ejecucion (N-1) con optimizacion (N). L0: no puedes operar y meta-operar al mismo tiempo sin perder resolucion.",
                dimensiones=["verbo", "adverbios"],
                accion_sugerida="Separa las escalas: primero haz, luego observa lo que hiciste. O al reves. No las dos a la vez.",
            )

    # Detectar via adverbios: modo explicito de ejecucion + modos ocultos de meta
    adv = e.get("adverbios", {})
    modos_ocultos = adv.get("modos_ocultos", [])
    modo_explicito = (adv.get("modo_explicito", "") or "").lower()
    meta_palabras = ["optimiz", "mejor", "evalu", "medir", "diseñ", "planific"]

    if modo_explicito and modos_ocultos:
        for m in modos_ocultos:
            m_lower = str(m).lower()
            if any(mp in m_lower for mp in meta_palabras):
                return Hallazgo(
                    tipo="colapso", operacion="inv_escalas",
                    severidad=0.6,
                    descripcion=f"Escala oculta: se declara modo '{modo_explicito}' pero se opera en modo meta ('{m}'). Ejecucion y optimizacion simultaneas sin declarar.",
                    dimensiones=["adverbios"],
                    accion_sugerida="En que escala estas? Haciendo o mirando como haces?",
                )
    return None


def _inv_mapa_xny(e: dict) -> Hallazgo | None:
    """MAPA = X interseccion Y: detecta cuando se usa SOLO percepcion interna (X)
    o SOLO datos externos (Y) sin convergencia.  El mapa requiere ambos."""
    adj = e.get("adjetivos", {})
    precision = adj.get("precision", 0.5)
    vacios = adj.get("vacios", [])
    cualidades = adj.get("cualidades", [])

    sust = e.get("sustantivos", {})
    perdido = sust.get("perdido", [])

    verbo = e.get("verbo", {})
    produce = verbo.get("produce_resultado", False)

    # Solo X (opiniones sin datos): muchos adjetivos vacios, baja precision, sin resultados medibles
    solo_opinion = len(vacios) > 2 and precision < 0.3 and not produce
    # Solo Y (metricas sin contexto): alta precision pero sin cualidades ni sujeto claro
    sp = e.get("sujeto_predicado", {})
    sujeto = sp.get("sujeto", "")
    agencia = sp.get("agencia", 0.5)
    solo_dato = precision > 0.7 and len(cualidades) == 0 and agencia < 0.3

    if solo_opinion:
        return Hallazgo(
            tipo="punto_ciego", operacion="inv_mapa_xny",
            severidad=0.6,
            descripcion="Solo percepcion interna (X): muchas opiniones, cero datos. L0: el mapa necesita X (lo que ves) INTERSECCION Y (lo que mides). Falta Y.",
            dimensiones=["adjetivos", "verbo"],
            accion_sugerida="Que DATO concreto soporta esto? Un numero, una fecha, una medicion.",
        )

    if solo_dato:
        return Hallazgo(
            tipo="punto_ciego", operacion="inv_mapa_xny",
            severidad=0.5,
            descripcion="Solo datos externos (Y): hay metricas pero sin contexto ni agente que interprete. L0: el mapa necesita X (percepcion) INTERSECCION Y (datos). Falta X.",
            dimensiones=["sujeto_predicado", "adjetivos"],
            accion_sugerida="Que SIGNIFICA este dato para ti? Que ves tu que el dato no dice?",
        )
    return None


def _inv_sintonizacion(e: dict) -> Hallazgo | None:
    """SINTONIZACION: detecta cuando se niega la capacidad de cambiar de escala.
    'No puedo ver', 'es imposible saber', 'no se puede medir'.
    L0: siempre se puede cambiar la escala de observacion."""
    texto = _extraer_texto_completo(e)
    patrones = [
        r"no\s+(puedo|podemos|se\s+puede)\s+(ver|saber|medir|entender|conocer|evaluar)",
        r"es\s+imposible\s+(saber|ver|medir|entender|predecir)",
        r"no\s+hay\s+(forma|manera)\s+de\s+(saber|ver|medir)",
        r"no\s+se\s+puede\s+(saber|ver|medir|controlar|predecir)",
        r"nunca\s+(sabremos|veremos|podremos)",
        r"es\s+demasiado\s+complejo\s+(para|como\s+para)",
    ]

    for p in patrones:
        if re.search(p, texto):
            return Hallazgo(
                tipo="patron", operacion="inv_sintonizacion",
                severidad=0.7,
                descripcion="Negacion de sintonizacion: se declara que no se puede ver/medir/saber. L0: la sintonizacion permite cambiar de escala para observar. No es que no se pueda — es que no se ha cambiado de escala.",
                dimensiones=["verbo", "adverbios"],
                accion_sugerida="Desde que escala estas mirando? Si subes o bajas un nivel, que ves?",
            )
    return None


# Lista de todos los detectores de invariantes L0
INVARIANTES_L0 = [
    _inv_simultaneidad,
    _inv_fractalidad,
    _inv_observador_sistema,
    _inv_convergencia,
    _inv_escalas,
    _inv_mapa_xny,
    _inv_sintonizacion,
]


# ===================================================================
# RAZONADOR PRINCIPAL
# ===================================================================

# Las 8 operaciones cognitivas
OPERACIONES = [
    ("modificacion", _op1_modificacion),
    ("predicacion", _op2_predicacion),
    ("complementacion", _op3_complementacion),
    ("transitividad", _op4_transitividad),
    ("subordinacion", _op5_subordinacion),
    ("cuantificacion", _op6_cuantificacion),
    ("conexion", _op7_conexion),
    ("transformacion", _op8_transformacion),
]

# 6 detectores de falacias
FALACIAS = [
    _fal_sustantiva, _fal_adjetiva, _fal_adverbial,
    _fal_verbal, _fal_conjuntiva, _fal_preposicional,
]

# 6 roturas sujeto-predicado (S48.7)
ROTURAS_SP = [
    _sp_tipo1_sujeto_falso,
    _sp_tipo2_predicado_desconectado,
    _sp_tipo3_sujeto_sustituido,
    _sp_tipo4_predicado_sin_sujeto,
    _sp_tipo5_ecuacion_falsa,
    _sp_tipo6_subordinada_disfrazada,
]

# Cruces entre operaciones (3 originales + 3 nuevos)
CRUCES = [
    _cruce_agencia_modo, _cruce_nivel_accion, _cruce_conexiones_agencia,
    _cruce_compresion_conexiones, _cruce_modos_ocultos_colapsos, _cruce_verbo_vacio_adjetivos_vacios,
]


# ===================================================================
# CÁLCULO 3: OPERACIONES COGNITIVAS
# Qué HACE el texto en la mente del receptor.
# No es qué dice (semántica) ni cómo está estructurado (sintaxis),
# sino qué operación mental EJECUTA.
# Código puro, $0, <1ms.
# ===================================================================

def _detectar_ops_cognitivas(estructura: dict, texto_original: str = "") -> dict:
    """Detecta qué operaciones cognitivas ejecuta un texto en el receptor.

    12 operaciones cognitivas, cada una con score 0.0-1.0:

    APERTURA (abren espacio mental):
      1. interrogacion   — preguntas que fuerzan construcción mental
      2. reformulacion   — cambia el marco/frame de la situación
      3. confrontacion   — desafía creencia o patrón existente

    CONSTRUCCIÓN (construyen estructura mental):
      4. subordinacion_causal — explica POR QUÉ (crea modelo causal)
      5. cuantificacion  — pone números (crea modelo medible)
      6. ejemplificacion — da ejemplo concreto (crea modelo visual)

    DIRECCIÓN (dirigen acción):
      7. imperativo      — ordena directamente
      8. propuesta       — sugiere con opción (agencia del receptor)
      9. urgencia        — crea presión temporal

    CONEXIÓN (conectan emocionalmente):
      10. validacion     — reconoce estado emocional del receptor
      11. personalizacion — usa nombre/datos del receptor
      12. narrativa      — cuenta una historia (crea identificación)
    """
    ops = {}

    # ─── Detectar desde texto original (si disponible) ───
    texto = texto_original.lower() if texto_original else ""

    # 1. INTERROGACIÓN — preguntas
    n_preguntas = texto.count("?")
    ops["interrogacion"] = min(1.0, n_preguntas * 0.3)  # 1 pregunta=0.3, 3+=1.0

    # 2. REFORMULACIÓN — indicadores de cambio de frame
    reformulacion_markers = [
        "en realidad", "lo que realmente", "dicho de otro modo", "es decir",
        "en otras palabras", "más bien", "no es que", "la verdad es",
        "lo importante es", "el punto es", "la clave es", "piensa en",
        "imagina que", "míralo así", "desde otro ángulo",
    ]
    n_reform = sum(1 for m in reformulacion_markers if m in texto)
    ops["reformulacion"] = min(1.0, n_reform * 0.4)

    # 3. CONFRONTACIÓN — desafío a creencias
    confrontacion_markers = [
        "pero realmente", "sin embargo", "¿estás segur", "¿de verdad",
        "no crees que", "contradicción", "inconsistente", "por otro lado",
        "¿y si no", "asumes que", "das por hecho", "la evidencia dice",
    ]
    n_confront = sum(1 for m in confrontacion_markers if m in texto)
    ops["confrontacion"] = min(1.0, n_confront * 0.4)

    # 4. SUBORDINACIÓN CAUSAL — explica por qué
    causal_markers = [
        "porque", "ya que", "dado que", "puesto que", "debido a",
        "por eso", "por lo tanto", "en consecuencia", "como resultado",
        "esto causa", "esto produce", "esto genera",
    ]
    n_causal = sum(1 for m in causal_markers if m in texto)
    ops["subordinacion_causal"] = min(1.0, n_causal * 0.3)

    # 5. CUANTIFICACIÓN — números concretos
    import re as _re
    numeros = _re.findall(r'\d+[%€$]?|\d+\.\d+', texto)
    ops["cuantificacion"] = min(1.0, len(numeros) * 0.15)  # 7+ números = 1.0

    # 6. EJEMPLIFICACIÓN — ejemplos concretos
    ejemplo_markers = [
        "por ejemplo", "como cuando", "imagina", "supón que",
        "un caso", "en concreto", "específicamente", "como",
    ]
    n_ejemplo = sum(1 for m in ejemplo_markers if m in texto)
    ops["ejemplificacion"] = min(1.0, n_ejemplo * 0.3)

    # 7. IMPERATIVO — órdenes directas
    imperativo_markers = [
        "haz", "llama", "envía", "responde", "confirma", "cancela",
        "reserva", "ven", "prueba", "contacta", "decide", "actúa",
        "empieza", "deja de", "no hagas", "asegúrate",
    ]
    n_imp = sum(1 for m in imperativo_markers if m in texto)
    ops["imperativo"] = min(1.0, n_imp * 0.3)

    # 8. PROPUESTA — sugiere con agencia del receptor
    propuesta_markers = [
        "¿qué te parece", "¿quieres que", "te propongo", "podrías",
        "¿prefieres", "tienes la opción", "puedes elegir", "si quieres",
        "¿te gustaría", "una opción es", "otra opción",
    ]
    n_prop = sum(1 for m in propuesta_markers if m in texto)
    ops["propuesta"] = min(1.0, n_prop * 0.4)

    # 9. URGENCIA — presión temporal
    urgencia_markers = [
        "ahora", "hoy", "antes de", "última oportunidad", "urgente",
        "inmediatamente", "no esperes", "ya", "cuanto antes", "deadline",
        "fecha límite", "mañana", "esta semana", "quedan",
    ]
    n_urg = sum(1 for m in urgencia_markers if m in texto)
    ops["urgencia"] = min(1.0, n_urg * 0.3)

    # 10. VALIDACIÓN — reconocimiento emocional
    validacion_markers = [
        "entiendo", "comprendo", "es normal", "tiene sentido",
        "sé que", "es difícil", "es lógico", "me imagino",
        "debe ser", "no es fácil", "tienes razón",
    ]
    n_val = sum(1 for m in validacion_markers if m in texto)
    ops["validacion"] = min(1.0, n_val * 0.4)

    # 11. PERSONALIZACIÓN — usa datos del receptor
    nombre_markers = [
        # Detectar nombres propios (mayúsculas tras punto o al inicio)
        # + referencias directas
    ]
    n_tu = texto.count(" tú ") + texto.count(" tu ") + texto.count(" usted ")
    n_nombre = len(_re.findall(r'(?:^|[.!?]\s+)[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+', texto_original or ""))
    ops["personalizacion"] = min(1.0, (n_tu * 0.15 + n_nombre * 0.3))

    # 12. NARRATIVA — cuenta historia
    narrativa_markers = [
        "había una vez", "recuerdo cuando", "me pasó", "un día",
        "la historia", "resulta que", "lo que pasó fue",
        "antes", "después", "entonces", "finalmente",
    ]
    n_narr = sum(1 for m in narrativa_markers if m in texto)
    ops["narrativa"] = min(1.0, n_narr * 0.3)

    # ─── Enriquecer desde estructura ACD ───
    sp = estructura.get("sujeto_predicado", {})
    conj = estructura.get("conjunciones", {})

    # Refinar confrontación con falsas dicotomías
    fd = conj.get("falsas_dicotomias", [])
    if fd:
        ops["confrontacion"] = min(1.0, ops.get("confrontacion", 0) + len(fd) * 0.2)

    # Refinar causal con conexiones
    tipo_conn = str(conj.get("tipo_conexion", "")).lower()
    if "causal" in tipo_conn:
        ops["subordinacion_causal"] = min(1.0, ops.get("subordinacion_causal", 0) + 0.3)

    # ─── Calcular scores agregados ───
    ops["_apertura"] = round((ops.get("interrogacion", 0) + ops.get("reformulacion", 0) + ops.get("confrontacion", 0)) / 3, 3)
    ops["_construccion"] = round((ops.get("subordinacion_causal", 0) + ops.get("cuantificacion", 0) + ops.get("ejemplificacion", 0)) / 3, 3)
    ops["_direccion"] = round((ops.get("imperativo", 0) + ops.get("propuesta", 0) + ops.get("urgencia", 0)) / 3, 3)
    ops["_conexion"] = round((ops.get("validacion", 0) + ops.get("personalizacion", 0) + ops.get("narrativa", 0)) / 3, 3)

    # Score total de operaciones cognitivas
    ops["_total"] = round(sum(ops.get(k, 0) for k in [
        "interrogacion", "reformulacion", "confrontacion",
        "subordinacion_causal", "cuantificacion", "ejemplificacion",
        "imperativo", "propuesta", "urgencia",
        "validacion", "personalizacion", "narrativa",
    ]) / 12, 3)

    return ops


def razonar(estructura: dict) -> Diagnostico:
    """Razona sobre una estructura ACD. Codigo puro, $0, <5ms.

    Implementa el framework ACD completo:
    - 8 operaciones cognitivas (S11, S42)
    - 6 detectores de falacias (S48.5)
    - 6 roturas sujeto-predicado (S48.7)
    - 9 modos de percepcion (S6)
    - 3 lentes SER/ESTAR/SEGUIR (S2.2)
    - Resolucion luminica avanzada vela/habitacion/estadio (S41)
    - Analisis de posicion conjuntiva (S42.6)
    - Operabilidad inter-capa: creencias (S10)
    - 6 cruces entre operaciones (S42.6)
    - Oracion del sistema (S2.3)

    Total: 8 ops + 6 falacias + 6 roturas SP + 9 modos + 3 lentes +
           resolucion luminica + posicion conjuntiva + creencias + 6 cruces
    = ~40+ detectores = 100% cobertura ACD.
    """
    if "error" in estructura:
        return Diagnostico(resumen=f"Error en percepcion: {estructura['error']}")

    # Limpiar artefactos del Perceptor (caracteres sueltos en listas)
    estructura = _e_limpio(estructura)

    hallazgos = []
    operaciones_activas = []
    falacias_encontradas = []

    # 1. Aplicar las 8 operaciones cognitivas
    for nombre, fn in OPERACIONES:
        try:
            h_list = fn(estructura)
            if h_list:
                hallazgos.extend(h_list)
                operaciones_activas.append(nombre)
        except Exception:
            continue

    # 2. Detectar falacias (6 operaciones defectuosas)
    for fn in FALACIAS:
        try:
            h = fn(estructura)
            if h:
                hallazgos.append(h)
                falacias_encontradas.append(h.operacion)
        except Exception:
            continue

    # 3. Detectar roturas sujeto-predicado (6 tipos, S48.7)
    for fn in ROTURAS_SP:
        try:
            h = fn(estructura)
            if h:
                hallazgos.append(h)
                falacias_encontradas.append(h.operacion)
        except Exception:
            continue

    # 4. Detectar modos de percepcion (9 modos, S6)
    try:
        modos_presentes, h_modos = _detectar_modos_percepcion(estructura)
        hallazgos.extend(h_modos)
    except Exception:
        modos_presentes = []

    modos_ausentes = [m for m in _VOCAB_MODOS if m not in modos_presentes]

    # 5. Detectar lentes SER/ESTAR/SEGUIR (S2.2)
    try:
        lentes_cubiertas, h_lentes = _detectar_lentes(estructura)
        hallazgos.extend(h_lentes)
    except Exception:
        lentes_cubiertas = []

    # 6. Resolucion luminica avanzada (S41)
    try:
        resolucion, nivel_luminico, h_luminica = _calcular_resolucion_avanzada(estructura)
        hallazgos.extend(h_luminica)
    except Exception:
        resolucion = 0.0
        nivel_luminico = "vela"

    # 7. Analisis de posicion conjuntiva (S42.6)
    try:
        h_conjuntiva = _analizar_posicion_conjuntiva(estructura)
        hallazgos.extend(h_conjuntiva)
    except Exception:
        pass

    # 8. Operabilidad inter-capa: creencias (S10)
    try:
        h_creencias = _detectar_creencias_ocultas(estructura)
        hallazgos.extend(h_creencias)
    except Exception:
        pass

    # 9. Aplicar cruces entre operaciones (6 cruces)
    for fn in CRUCES:
        try:
            h = fn(estructura)
            if h:
                hallazgos.append(h)
        except Exception:
            continue

    # 10. Detectar operaciones cognitivas (Cálculo 3)
    try:
        ops_cognitivas = _detectar_ops_cognitivas(estructura)
    except Exception:
        ops_cognitivas = {}

    # 11. Detectar invariantes L0 violados (7 invariantes)
    invariantes_violados = []
    for fn in INVARIANTES_L0:
        try:
            h = fn(estructura)
            if h:
                hallazgos.append(h)
                invariantes_violados.append(h.operacion)
        except Exception:
            continue

    # Ordenar por severidad
    hallazgos.sort(key=lambda h: h.severidad, reverse=True)

    # Calcular salud (penalizacion ponderada por tipo)
    # Operaciones de ESTILO pesan menos que las de LOGICA
    _STYLE_OPS = {"modificacion", "cuantificacion", "conexion", "transformacion",
                  "complementacion", "transitividad"}
    # Tipos de logica real (falacias graves, contradicciones, colapsos)
    _LOGIC_TYPES = {"contradiccion", "colapso"}
    if hallazgos:
        penalizacion = 0.0
        for h in hallazgos:
            if h.tipo in ("modo_ausente", "lente_ausente"):
                penalizacion += h.severidad * 0.01  # Peso minimo — observacionales
            elif h.tipo == "falacia":
                penalizacion += h.severidad * 0.03  # Falacias: moderado
            elif h.tipo in _LOGIC_TYPES:
                penalizacion += h.severidad * 0.04  # Contradicciones/colapsos
            elif h.operacion in _STYLE_OPS:
                penalizacion += h.severidad * 0.5 * 0.02  # Estilo: muy bajo
            elif h.tipo == "posicion_conjuntiva":
                penalizacion += h.severidad * 0.005  # Observacion pura
            else:
                penalizacion += h.severidad * 0.02  # Default: bajo
        salud = max(0.15, round(1.0 - penalizacion, 2))
    else:
        salud = 1.0

    # Palanca = el hallazgo mas impactante con accion sugerida
    palanca = ""
    if hallazgos:
        con_accion = [h for h in hallazgos if h.accion_sugerida]
        if con_accion:
            palanca = con_accion[0].accion_sugerida

    # Preguntas
    preguntas = []
    for h in hallazgos[:5]:
        if h.accion_sugerida and "?" in h.accion_sugerida:
            preguntas.append(h.accion_sugerida)

    # Oracion del sistema
    oracion = _construir_oracion_sistema(estructura)

    # Resumen
    tipos = {}
    for h in hallazgos:
        tipos[h.tipo] = tipos.get(h.tipo, 0) + 1

    partes = []
    for tipo_nombre in ["contradiccion", "colapso", "falacia", "creencia_oculta",
                        "punto_ciego", "tension", "patron", "modo_ausente",
                        "lente_ausente", "posicion_conjuntiva"]:
        if tipos.get(tipo_nombre):
            partes.append(f"{tipos[tipo_nombre]} {tipo_nombre}(s)")

    resumen = f"Salud {salud:.0%} | Resolucion {resolucion:.0%} ({nivel_luminico.upper()}) | "
    resumen += f"Modos {len(modos_presentes)}/9 | Lentes {len(lentes_cubiertas)}/3 | "
    resumen += (", ".join(partes) + "." if partes else "Sin hallazgos.")
    if falacias_encontradas:
        resumen += f" | {len(falacias_encontradas)} falacia(s) detectada(s)."
    if invariantes_violados:
        resumen += f" | {len(invariantes_violados)} invariante(s) L0 violado(s)."

    return Diagnostico(
        hallazgos=hallazgos,
        salud=salud,
        resumen=resumen,
        palanca=palanca,
        preguntas=preguntas,
        oracion_sistema=oracion,
        resolucion_luminica=resolucion,
        nivel_luminico=nivel_luminico,
        operaciones_detectadas=operaciones_activas,
        falacias_detectadas=falacias_encontradas,
        modos_presentes=modos_presentes,
        modos_ausentes=modos_ausentes,
        lentes_cubiertas=lentes_cubiertas,
        invariantes_violados=invariantes_violados,
        ops_cognitivas=ops_cognitivas,
    )


def diagnostico_a_dict(d: Diagnostico) -> dict:
    """Convierte un Diagnostico a dict serializable."""
    return {
        "salud": d.salud,
        "resolucion_luminica": d.resolucion_luminica,
        "nivel_luminico": d.nivel_luminico,
        "resumen": d.resumen,
        "oracion_sistema": d.oracion_sistema,
        "palanca": d.palanca,
        "preguntas": d.preguntas,
        "operaciones_detectadas": d.operaciones_detectadas,
        "falacias_detectadas": d.falacias_detectadas,
        "modos_presentes": d.modos_presentes,
        "modos_ausentes": d.modos_ausentes,
        "lentes_cubiertas": d.lentes_cubiertas,
        "hallazgos": [
            {
                "tipo": h.tipo,
                "operacion": h.operacion,
                "severidad": round(h.severidad, 2),
                "descripcion": h.descripcion,
                "dimensiones": h.dimensiones,
                "accion": h.accion_sugerida,
            }
            for h in d.hallazgos
        ],
        "n_hallazgos": len(d.hallazgos),
        "n_falacias": len(d.falacias_detectadas),
        "n_modos_presentes": len(d.modos_presentes),
        "n_modos_ausentes": len(d.modos_ausentes),
        "n_lentes_cubiertas": len(d.lentes_cubiertas),
        "invariantes_violados": d.invariantes_violados,
        "n_invariantes_violados": len(d.invariantes_violados),
        "coste": 0.0,
    }
