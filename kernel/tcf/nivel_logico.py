"""Nivel lógico — mapea lente faltante a nivel de intervención y modos.

Tabla derivada de Maestro v3 §modos + TCF:
  - salud faltante → nivel operativo (1-2) → MOVER, GENERAR
  - sentido faltante → nivel semántico/existencial (3-5) → ENMARCAR, PERCIBIR
  - continuidad faltante → nivel transferencia (4) → GENERAR, ANALIZAR

Código puro, $0.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class NivelModo:
    lente: str                # "salud" | "sentido" | "continuidad"
    niveles: list[int]        # niveles lógicos de intervención (1-5)
    modos: list[str]          # modos conceptuales a activar
    descripcion: str          # para logs/debug


# Tabla maestra: lente faltante → niveles + modos
MAPEO_LENTE_NIVEL_MODO: dict[str, dict] = {
    "salud": {
        "niveles": [1, 2],
        "modos": ["MOVER", "GENERAR"],
        "descripcion": "Nivel operativo: acciones concretas, producción, ejecución inmediata.",
    },
    "sentido": {
        "niveles": [3, 4, 5],
        "modos": ["ENMARCAR", "PERCIBIR"],
        "descripcion": "Nivel semántico/existencial: cuestionar premisas, redefinir marcos, buscar propósito.",
    },
    "continuidad": {
        "niveles": [4],
        "modos": ["GENERAR", "ANALIZAR"],
        "descripcion": "Nivel transferencia: sistematizar, documentar, diseñar replicación.",
    },
}

# Modos secundarios que refuerzan la lente faltante sin ser el foco principal
MODOS_SECUNDARIOS: dict[str, list[str]] = {
    "salud": ["ANALIZAR"],        # Diagnosticar qué falla operativamente
    "sentido": ["SENTIR"],        # Conectar con el porqué emocional
    "continuidad": ["ENMARCAR"],  # Definir qué merece transmitirse
}


def seleccionar_nivel_modo(lente_faltante: str) -> NivelModo:
    """Dado la lente más baja, retorna nivel lógico y modos de intervención.

    Args:
        lente_faltante: "salud" | "sentido" | "continuidad"

    Returns:
        NivelModo con niveles, modos y descripción.

    Raises:
        ValueError: Si la lente no existe.
    """
    if lente_faltante not in MAPEO_LENTE_NIVEL_MODO:
        raise ValueError(
            f"Lente '{lente_faltante}' no válida. "
            f"Opciones: {list(MAPEO_LENTE_NIVEL_MODO.keys())}"
        )

    data = MAPEO_LENTE_NIVEL_MODO[lente_faltante]
    return NivelModo(
        lente=lente_faltante,
        niveles=data["niveles"],
        modos=data["modos"],
        descripcion=data["descripcion"],
    )


def modos_secundarios(lente_faltante: str) -> list[str]:
    """Retorna modos secundarios de refuerzo para la lente faltante."""
    return MODOS_SECUNDARIOS.get(lente_faltante, [])
