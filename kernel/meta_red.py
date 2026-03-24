"""Bridge: re-exporta loaders puros ($0) de src.meta_red.

Estos son cargadores de JSON (inteligencias, pensamientos, razonamientos,
marco lingüístico). Son código puro sin LLM, pertenecen al kernel.
En Sprint 1 migraremos los JSON a kernel/datos/ y eliminaremos este bridge.
"""
from src.meta_red import (
    load_inteligencias,
    load_marco_linguistico,
    load_pensamientos,
    load_razonamientos,
)

__all__ = [
    "load_inteligencias",
    "load_marco_linguistico",
    "load_pensamientos",
    "load_razonamientos",
]
