"""Detector TCF — Pre-screening lingüístico + integración con detector existente.

Integra la TCF en Capa 0 del pipeline:
  1. Pre-screening lingüístico (firmas → arquetipos candidatos)
  2. Si hay vector funcional disponible (de datos previos / Reactor):
     - Scoring multi-arquetipo
     - Evaluación del campo
     - Receta prescrita

Esto extiende DetectorResult sin romper la interfaz existente.

Fuente: TCF §11, VALIDACION_TCF_CASO_PILATES.md §5
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.tcf.campo import VectorFuncional, EstadoCampo, evaluar_campo
from src.tcf.arquetipos import (
    ScoringMultiArquetipo,
    FirmaDetectada,
    scoring_multi_arquetipo,
    pre_screening_linguistico,
)
from src.tcf.recetas import RecetaResultado, generar_receta_mixta


# ---------------------------------------------------------------------------
# §1. RESULTADO TCF
# ---------------------------------------------------------------------------

@dataclass
class DetectorTCFResult:
    """Resultado del análisis TCF. Se añade al DetectorResult existente."""

    # Pre-screening lingüístico (siempre disponible, solo necesita texto)
    firmas: list[FirmaDetectada]
    arquetipos_candidatos: list[str]  # arquetipos sugeridos por firma lingüística

    # Campo funcional (solo si hay vector disponible — real o estimado)
    estado_campo: EstadoCampo | None
    scoring: ScoringMultiArquetipo | None
    receta: RecetaResultado | None

    # True si el vector fue estimado desde firmas (no provisto externamente)
    vector_estimado: bool = False


# ---------------------------------------------------------------------------
# §1.5 ESTIMACIÓN DE VECTOR DESDE FIRMAS LINGÜÍSTICAS
# ---------------------------------------------------------------------------

def estimar_vector_desde_firmas(
    firmas: list[FirmaDetectada],
) -> VectorFuncional | None:
    """Estima un vector funcional a partir de firmas lingüísticas detectadas.

    Usa los vectores canónicos de ARQUETIPOS_CANONICOS ponderados por
    confianza de la firma. Es una ESTIMACIÓN, no un diagnóstico.

    Retorna None si no hay firmas.
    """
    if not firmas:
        return None

    from src.tcf.constantes import ARQUETIPOS_CANONICOS, FUNCIONES

    # Filtrar firmas cuyos arquetipos tienen vector canónico
    firmas_validas = [f for f in firmas if f.arquetipo in ARQUETIPOS_CANONICOS]
    if not firmas_validas:
        return None

    # Si solo hay 1 firma, usar su vector canónico directamente
    if len(firmas_validas) == 1:
        return VectorFuncional.from_dict(
            ARQUETIPOS_CANONICOS[firmas_validas[0].arquetipo]
        )

    # Blend ponderado por confianza
    peso_total = sum(f.confianza for f in firmas_validas)
    if peso_total == 0:
        # Todas con confianza 0 → peso igual
        peso_total = len(firmas_validas)
        pesos = [1.0] * len(firmas_validas)
    else:
        pesos = [f.confianza for f in firmas_validas]

    blended = {f: 0.0 for f in FUNCIONES}
    for firma, peso in zip(firmas_validas, pesos):
        canon = ARQUETIPOS_CANONICOS[firma.arquetipo]
        for fi in FUNCIONES:
            blended[fi] += canon[fi] * peso

    for fi in FUNCIONES:
        blended[fi] = round(blended[fi] / peso_total, 3)
        blended[fi] = max(0.0, min(1.0, blended[fi]))

    return VectorFuncional.from_dict(blended)


# ---------------------------------------------------------------------------
# §2. DETECTAR TCF
# ---------------------------------------------------------------------------

def detectar_tcf(
    input_text: str,
    vector: VectorFuncional | None = None,
) -> DetectorTCFResult:
    """Ejecuta análisis TCF sobre el input.

    Tres fases:
    - Fase A (siempre): pre-screening lingüístico del texto
    - Fase A.5 (si no hay vector pero sí firmas): estimar vector desde firmas
    - Fase B (si hay vector real o estimado): evaluación completa del campo funcional

    Args:
        input_text: texto del usuario a analizar
        vector: vector funcional previo del sistema (si existe, de DB/Reactor)
    """
    # Fase A: Pre-screening lingüístico
    firmas = pre_screening_linguistico(input_text)
    candidatos = [f.arquetipo for f in firmas]

    # Fase A.5: Estimar vector si no hay uno previo pero sí hay firmas
    vector_usado = vector
    estimado = False
    if vector_usado is None and firmas:
        vector_usado = estimar_vector_desde_firmas(firmas)
        estimado = vector_usado is not None

    # Fase B: Campo funcional (si hay vector real o estimado)
    estado = None
    scoring = None
    receta = None

    if vector_usado is not None:
        estado = evaluar_campo(vector_usado)
        scoring = scoring_multi_arquetipo(vector_usado)
        receta = generar_receta_mixta(scoring, vector_usado)

    return DetectorTCFResult(
        firmas=firmas,
        arquetipos_candidatos=candidatos,
        estado_campo=estado,
        scoring=scoring,
        receta=receta,
        vector_estimado=estimado,
    )


# ---------------------------------------------------------------------------
# §3. INTEGRACIÓN CON DETECTOR EXISTENTE
# ---------------------------------------------------------------------------

def enriquecer_detector_result(
    detector_result,
    tcf_result: DetectorTCFResult,
) -> dict:
    """Añade información TCF al resultado del detector existente.

    No modifica DetectorResult directamente (para no romper la interfaz).
    Devuelve un dict con la información combinada para el Router.
    """
    info = {
        "huecos_sintacticos": {
            "huecos": [
                {"tipo": h.tipo, "operacion": h.operacion, "capa": h.capa}
                for h in detector_result.huecos
            ],
            "perfil_acoples": detector_result.perfil_acoples,
            "diagnostico_acople": detector_result.diagnostico_acople,
            "inteligencias_sugeridas": detector_result.inteligencias_sugeridas,
        },
        "tcf": {
            "firmas_detectadas": [
                {"arquetipo": f.arquetipo, "confianza": f.confianza}
                for f in tcf_result.firmas
            ],
            "arquetipos_candidatos": tcf_result.arquetipos_candidatos,
        },
    }

    # Si hay análisis de campo completo
    if tcf_result.estado_campo is not None:
        info["tcf"]["campo"] = {
            "lentes": tcf_result.estado_campo.lentes,
            "coalicion": tcf_result.estado_campo.coalicion,
            "perfil_lente": tcf_result.estado_campo.perfil_lente,
            "eslabon_debil": tcf_result.estado_campo.eslabon_debil,
            "atractor": tcf_result.estado_campo.atractor_mas_cercano,
            "estable": tcf_result.estado_campo.estable,
            "toxicidad_total": tcf_result.estado_campo.toxicidad_total,
            "deps_violadas": [
                {"fi": dv.fi, "fj": dv.fj, "tipo": dv.tipo, "brecha": round(dv.brecha, 2)}
                for dv in tcf_result.estado_campo.dependencias_violadas
            ],
        }

    if tcf_result.scoring is not None:
        info["tcf"]["scoring"] = {
            "primario": {
                "arquetipo": tcf_result.scoring.primario.arquetipo,
                "score": tcf_result.scoring.primario.score,
            },
        }
        if tcf_result.scoring.secundario:
            info["tcf"]["scoring"]["secundario"] = {
                "arquetipo": tcf_result.scoring.secundario.arquetipo,
                "score": tcf_result.scoring.secundario.score,
            }

    if tcf_result.receta is not None:
        info["tcf"]["receta"] = {
            "secuencia": tcf_result.receta.secuencia,
            "ints": tcf_result.receta.ints,
            "lente": tcf_result.receta.lente,
            "frenar": tcf_result.receta.frenar,
            "parar_primero": tcf_result.receta.parar_primero,
            "mezcla": tcf_result.receta.mezcla,
        }

    return info
