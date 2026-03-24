"""Teoría de Campo Funcional — 14 leyes, 5 teoremas, 12 arquetipos.

Exports principales:
- VectorFuncional: representación del estado de un negocio en 7F×3L
- evaluar_campo(): aplica leyes TCF
- clasificar_estado(): E1-E10
- prescribir(): receta código puro $0
"""
from kernel.tcf.campo import VectorFuncional, evaluar_campo
from kernel.tcf.campo_dual import CeldaCampo
from kernel.tcf.constantes import (
    FUNCIONES, LENTES, AFINIDAD_INT_F, AFINIDAD_INT_L,
    ARQUETIPOS_CANONICOS, DEPENDENCIAS, CICLOS,
)
from kernel.tcf.arquetipos import scoring_multi_arquetipo, pre_screening_linguistico
from kernel.tcf.recetas import generar_receta_mixta, RecetaResultado
from kernel.tcf.prescriptor import prescribir
from kernel.tcf.diagnostico import clasificar_estado, DiagnosticoCompleto
from kernel.tcf.flags import detectar_todos_flags
from kernel.tcf.lentes import ecuacion_transferencia, predecir_impacto, es_equilibrio_nash

__all__ = [
    "VectorFuncional", "evaluar_campo", "CeldaCampo",
    "FUNCIONES", "LENTES", "AFINIDAD_INT_F", "AFINIDAD_INT_L",
    "ARQUETIPOS_CANONICOS", "DEPENDENCIAS", "CICLOS",
    "scoring_multi_arquetipo", "pre_screening_linguistico",
    "generar_receta_mixta", "RecetaResultado",
    "prescribir",
    "clasificar_estado", "DiagnosticoCompleto",
    "detectar_todos_flags",
    "ecuacion_transferencia", "predecir_impacto", "es_equilibrio_nash",
]
