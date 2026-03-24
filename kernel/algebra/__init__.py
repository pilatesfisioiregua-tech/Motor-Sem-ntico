"""Álgebra compositiva — operaciones puras sobre inteligencias ($0).

8 operaciones semánticas + 13 reglas compilador.
Las operaciones manipulan vocabularios, marcos conceptuales,
objetos de percepción. NO son aritméticas sobre scores.

Re-exporta operaciones del pipeline que son código puro:
  - compose(): compone N inteligencias en algoritmo (grafos)
  - detect(): detecta huecos y firmas lingüísticas
  - generar_prompts(): genera templates de prompt

Estas funciones NO llaman LLM. Son el álgebra del Motor.
"""
from src.pipeline.compositor import compose, componer, Operacion, Algoritmo
from src.pipeline.detector_huecos import detect, detectar_huecos, DetectorResult
from src.pipeline.generador import generar_prompts, PromptPlan

__all__ = [
    "compose", "componer", "Operacion", "Algoritmo",
    "detect", "detectar_huecos", "DetectorResult",
    "generar_prompts", "PromptPlan",
]
