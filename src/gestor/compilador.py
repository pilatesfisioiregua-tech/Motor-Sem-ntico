"""Compilador del Gestor — programa por arquetipo.

Dado un scoring multi-arquetipo:
1. Busca la receta mixta (de src/tcf/recetas.py)
2. Asigna modelos por celda (de src/gestor/modelos.py)
3. Decide tier de enjambre (de src/gestor/tier.py)
4. Produce un ProgramaCompilado que el Motor ejecuta

Maestro §6.1, §6.4.
"""
from __future__ import annotations

from src.tcf.arquetipos import ScoringMultiArquetipo
from src.tcf.campo import VectorFuncional
from src.tcf.recetas import generar_receta_mixta, RecetaResultado
from src.gestor.modelos import modelo_para_celda
from src.gestor.programa import ProgramaCompilado, PasoPrograma
from src.gestor.tier import decidir_tier, TIER_CONFIG


def compilar_programa(
    scoring: ScoringMultiArquetipo,
    vector: VectorFuncional | None = None,
    modo: str = "analisis",
    presupuesto_max: float = 1.50,
    forzar_tier: int | None = None,
) -> ProgramaCompilado:
    """Compila un programa de preguntas a partir del scoring de arquetipo.

    Este es el output principal del Gestor. El Motor recibe esto y ejecuta.

    Args:
        scoring: resultado del scoring multi-arquetipo
        vector: vector funcional del caso (para Regla 14 / FRENAR)
        modo: modo del pipeline (analisis, conversacion, etc.)
        presupuesto_max: presupuesto máximo en USD
        forzar_tier: si se quiere forzar un tier específico
    """
    # 1. Generar receta mixta
    receta = generar_receta_mixta(scoring, vector)

    # 2. Decidir tier
    tier = decidir_tier(
        modo=modo,
        tiene_programa_precompilado=False,  # v0: nunca hay precompilado aún
        forzar_tier=forzar_tier,
        presupuesto_max=presupuesto_max,
    )

    # 3. Construir pasos del programa
    pasos = _construir_pasos(receta, tier)

    # 4. Estimar coste y tiempo
    config_tier = TIER_CONFIG.get(tier, TIER_CONFIG[3])

    return ProgramaCompilado(
        arquetipo_base=receta.arquetipo_base,
        arquetipo_score=scoring.primario.score,
        tier=tier,
        pasos=pasos,
        frenar=receta.frenar,
        parar_primero=receta.parar_primero,
        lente_primaria=receta.lente,
        mezcla=receta.mezcla,
        coste_estimado=config_tier["coste_est"],
        tiempo_estimado_s=config_tier["tiempo_est_s"],
    )


def _construir_pasos(receta: RecetaResultado, tier: int) -> list[PasoPrograma]:
    """Traduce una receta en pasos ejecutables con modelos asignados."""
    pasos = []
    orden = 1

    # Emparejar INTs con funciones de la secuencia
    # La receta tiene secuencia de funciones y lista de INTs
    # Cada INT se asigna a la función que mejor cubre (según la receta)
    funciones = receta.secuencia if receta.secuencia else ["F5"]  # default F5
    ints = receta.ints if receta.ints else ["INT-01", "INT-08", "INT-16"]  # fallback
    lente = receta.lente or "salud"

    for i, int_id in enumerate(ints):
        # Asignar función: round-robin sobre la secuencia
        funcion = funciones[min(i, len(funciones) - 1)]

        # Asignar modelo según celda
        modelo = modelo_para_celda(funcion, lente)

        # Tier 2: solo 1 modelo, usar el de mayor cobertura
        if tier <= 2:
            modelo = "deepseek/deepseek-chat-v3-0324"

        pasos.append(PasoPrograma(
            orden=orden,
            inteligencia=int_id,
            funcion_objetivo=funcion,
            lente_objetivo=lente,
            modelo=modelo,
            operacion="individual",
        ))
        orden += 1

    return pasos
