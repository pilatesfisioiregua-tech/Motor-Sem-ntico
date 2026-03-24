"""OMNI-MIND Motor — Pensamiento stateless, compartido entre tenants.

API única: motor.pensar(system, user, config) → Pensamiento verificado.
Sandwich LLM: código_pre → LLM → código_post.

Módulos:
  - pensar: API única de pensamiento
  - diagnosticador: pipeline ACD end-to-end
  - evaluador_acd: métricas de prescripción
  - evaluador_funcional: texto → VectorFuncional (LLM)
  - repertorio: inferencia INT×P×R (LLM)
"""
from motor.pensar import pensar, ConfigPensamiento, Pensamiento

__all__ = ["pensar", "ConfigPensamiento", "Pensamiento"]
