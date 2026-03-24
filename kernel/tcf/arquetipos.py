"""Arquetipos — Scoring multi-arquetipo y pre-screening lingüístico.

Implementa:
  - scoring_multi_arquetipo(): distancia a cada arquetipo canónico, top 3
  - pre_screening_linguistico(): firma lingüística → arquetipos candidatos
  - Validación §6.1: casos reales son mixtos, scoring ponderado

Fuentes: RESULTADO_CALCULOS_ANALITICOS_v1.md §6, VALIDACION_TCF_CASO_PILATES.md §5
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from kernel.tcf.constantes import (
    ARQUETIPOS_CANONICOS,
    FIRMAS_LINGUISTICAS,
    UMBRAL_SCORE_ARQUETIPO,
)
from kernel.tcf.campo import VectorFuncional


# ---------------------------------------------------------------------------
# §1. SCORING MULTI-ARQUETIPO
# ---------------------------------------------------------------------------

@dataclass
class ScoreArquetipo:
    arquetipo: str
    score: float   # 0.0 - 1.0 (1.0 = match perfecto)


@dataclass
class ScoringMultiArquetipo:
    primario: ScoreArquetipo
    secundario: ScoreArquetipo | None
    terciario: ScoreArquetipo | None
    todos: list[ScoreArquetipo]   # todos los que pasan el umbral
    vector_real: VectorFuncional


def scoring_multi_arquetipo(vector: VectorFuncional) -> ScoringMultiArquetipo:
    """Calcula distancia a cada arquetipo canónico, devuelve top 3 con score ≥ 0.15.

    score(arquetipo, vector) = 1 - distancia_normalizada(patron, vector)
    """
    scores = []
    for nombre, patron_dict in ARQUETIPOS_CANONICOS.items():
        patron = VectorFuncional.from_dict(patron_dict)
        dist = vector.distancia(patron)
        score = max(0.0, 1.0 - dist)
        scores.append(ScoreArquetipo(arquetipo=nombre, score=round(score, 3)))

    # Ordenar por score descendente
    scores.sort(key=lambda s: s.score, reverse=True)

    # Filtrar por umbral
    filtrados = [s for s in scores if s.score >= UMBRAL_SCORE_ARQUETIPO]

    primario = filtrados[0] if filtrados else ScoreArquetipo("mixto", 0.0)
    secundario = filtrados[1] if len(filtrados) > 1 else None
    terciario = filtrados[2] if len(filtrados) > 2 else None

    return ScoringMultiArquetipo(
        primario=primario,
        secundario=secundario,
        terciario=terciario,
        todos=filtrados,
        vector_real=vector,
    )


# ---------------------------------------------------------------------------
# §2. PRE-SCREENING LINGÜÍSTICO (Paso 0 del pipeline)
# ---------------------------------------------------------------------------

@dataclass
class FirmaDetectada:
    arquetipo: str
    patron_matched: str   # el regex que matcheó
    fragmento: str        # el fragmento del texto que matcheó
    confianza: float      # 0.0 - 1.0 (heurístico: más patrones = más confianza)


def pre_screening_linguistico(input_text: str) -> list[FirmaDetectada]:
    """Detecta firma lingüística → arquetipos candidatos.

    Es PRE-SCREENING, no diagnóstico. Confirma pero no reemplaza
    el análisis funcional completo (TCF §11).

    Retorna lista de firmas detectadas, ordenadas por confianza.
    """
    text = input_text.lower()
    resultados_por_arquetipo: dict[str, list[FirmaDetectada]] = {}

    for arquetipo, patrones in FIRMAS_LINGUISTICAS.items():
        matches = []
        for patron in patrones:
            try:
                for match in re.finditer(patron, text):
                    matches.append(FirmaDetectada(
                        arquetipo=arquetipo,
                        patron_matched=patron,
                        fragmento=match.group(0),
                        confianza=0.0,  # se calcula después
                    ))
            except re.error:
                continue

        if matches:
            # Confianza = proporción de patrones que matchearon (max 0.8)
            # No llega a 1.0 porque la firma no es diagnóstico definitivo
            n_patrones = len(patrones)
            n_matched = len(set(m.patron_matched for m in matches))
            confianza = min(0.80, n_matched / n_patrones)

            # Actualizar confianza en todas las firmas de este arquetipo
            for m in matches:
                m.confianza = round(confianza, 2)

            resultados_por_arquetipo[arquetipo] = matches

    # Aplanar y deduplicar por arquetipo (tomar el de mayor confianza)
    resultado = []
    for arquetipo, firmas in resultados_por_arquetipo.items():
        mejor = max(firmas, key=lambda f: f.confianza)
        resultado.append(mejor)

    # Ordenar por confianza descendente
    resultado.sort(key=lambda f: f.confianza, reverse=True)

    return resultado
