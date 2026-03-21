"""Programa compilado — output del Gestor para el Motor.

Un programa es la receta ejecutable: qué INTs, en qué orden,
con qué modelos, para qué funciones.

Maestro §6.4.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PasoPrograma:
    """Un paso del programa compilado."""
    orden: int                  # 1, 2, 3...
    inteligencia: str           # "INT-07"
    funcion_objetivo: str       # "F5" — la función que este paso ataca
    lente_objetivo: str         # "continuidad"
    modelo: str                 # "deepseek/deepseek-chat-v3-0324"
    operacion: str              # "individual", "composicion", "fusion"
    con_inteligencia: str | None = None  # para composición: A→B, B es con_inteligencia


@dataclass
class ProgramaCompilado:
    """Programa completo que el Motor ejecuta."""
    arquetipo_base: str             # "maquina_sin_alma"
    arquetipo_score: float          # 0.78
    tier: int                       # 1-5
    pasos: list[PasoPrograma]       # secuencia de ejecución
    frenar: list[str]               # funciones a FRENAR antes de ejecutar
    parar_primero: bool             # True solo para "quemado"
    lente_primaria: str             # "continuidad"
    mezcla: bool                    # True si receta mixta
    coste_estimado: float           # $ estimado
    tiempo_estimado_s: float        # segundos estimados

    def inteligencias(self) -> list[str]:
        """INTs únicas en el programa."""
        return list(dict.fromkeys(p.inteligencia for p in self.pasos))

    def modelos(self) -> list[str]:
        """Modelos únicos en el programa."""
        return list(dict.fromkeys(p.modelo for p in self.pasos))
