"""Verificador post-LLM — código puro $0.

Verifica outputs de LLM contra reglas IC2-IC7 deterministas.
Detecta output genérico, repetición, JSON malformado,
F3 sugiriendo adición (anti-patrón).
"""
from kernel.verificador.verificar import verificar

__all__ = ["verificar"]
