"""Lentes — Juegos de Lentes: coaliciones, perfiles, Nash, transferencia.

Implementa:
  - ecuacion_transferencia(): ΔL_j = Σ_i (v(j,Fi) × ΔFi)
  - identificar_perfil_lente(): 8 perfiles binarios
  - es_equilibrio_nash(): ¿alguna lente puede mejorar unilateralmente?
  - predecir_impacto(): predice efecto de subir/bajar una función

Fuente: TEORIA_JUEGOS_LENTES.md
"""
from __future__ import annotations

from dataclasses import dataclass

from kernel.tcf.constantes import (
    FUNCIONES, LENTES,
    VALORACION_F_L,
    UMBRAL_LENTE_ALTA,
)
from kernel.tcf.campo import VectorFuncional, calcular_lentes


# ---------------------------------------------------------------------------
# §1. ECUACIÓN DE TRANSFERENCIA (Juegos de Lentes §5)
# ---------------------------------------------------------------------------

def ecuacion_transferencia(
    delta_funciones: dict[str, float],
) -> dict[str, float]:
    """Predice cambio en lentes dado un cambio en funciones.

    ΔL_j = Σ_i (v(j, Fi) × ΔFi)

    Ejemplo: subir F7 en +0.30
      ΔSalud = 0.25 × 0.30 = +0.075
      ΔSentido = 0.25 × 0.30 = +0.075
      ΔContinuidad = 1.00 × 0.30 = +0.300
    """
    resultado = {}
    for lente in LENTES:
        delta_lente = sum(
            VALORACION_F_L.get(f, {}).get(lente, 0.0) * delta_funciones.get(f, 0.0)
            for f in FUNCIONES
        )
        resultado[lente] = round(delta_lente, 4)
    return resultado


# ---------------------------------------------------------------------------
# §2. PREDECIR IMPACTO DE UNA INTERVENCIÓN
# ---------------------------------------------------------------------------

@dataclass
class ImpactoIntervencion:
    funcion: str
    delta: float                    # cuánto se mueve la función
    delta_lentes: dict[str, float]  # cambio predicho en cada lente
    lente_mas_beneficiada: str
    neutral: bool                   # True si beneficia a las 3 por igual (ej: F5)


def predecir_impacto(
    funcion: str,
    delta: float,
) -> ImpactoIntervencion:
    """Predice el impacto de mover una función en las 3 lentes."""
    deltas = ecuacion_transferencia({funcion: delta})

    # Lente más beneficiada
    mas_beneficiada = max(deltas, key=deltas.get)

    # ¿Es neutral? (las 3 lentes se benefician similarmente)
    valores = list(deltas.values())
    rango = max(valores) - min(valores)
    neutral = rango < 0.05  # diferencia menor a 0.05 = neutral

    return ImpactoIntervencion(
        funcion=funcion,
        delta=delta,
        delta_lentes=deltas,
        lente_mas_beneficiada=mas_beneficiada,
        neutral=neutral,
    )


# ---------------------------------------------------------------------------
# §3. EQUILIBRIO DE NASH (Juegos de Lentes §4)
# ---------------------------------------------------------------------------

def es_equilibrio_nash(vector: VectorFuncional) -> bool:
    """¿El estado actual es un equilibrio de Nash entre lentes?

    Nash = ninguna lente puede mejorar unilateralmente redirigiendo una función.

    Heurístico simplificado: si todas las lentes están en la misma "banda"
    (todas altas o todas bajas), no hay incentivo a redirigir.
    Si hay disparidad grande, la lente baja tiene incentivo a "robar"
    funciones → NO es Nash.
    """
    lentes = calcular_lentes(vector)

    # Disparidad entre lentes
    vals = list(lentes.values())
    rango = max(vals) - min(vals)

    # Si el rango es pequeño, es Nash (nadie puede mejorar mucho)
    if rango < 0.15:
        return True

    # Si hay funciones "disputadas" (valoradas alto por 2+ lentes)
    # y una lente está muy baja, podría redirigir → no Nash
    return False


# ---------------------------------------------------------------------------
# §4. PERFILES DE LENTE (ya en campo.py pero aquí funciones auxiliares)
# ---------------------------------------------------------------------------

# Mapeo perfil → nombre descriptivo + arquetipo típico
PERFILES_NOMBRES = {
    "S+Se+C+": ("Equilibrado", "equilibrado"),
    "S+Se+C-": ("Mortal Feliz", "maquina_sin_alma"),
    "S+Se-C+": ("Franquicia Vacía", "copia_sin_esencia"),
    "S+Se-C-": ("Máquina Ciega", "sin_rumbo"),
    "S-Se+C+": ("Profeta sin Recursos", "semilla_dormida"),
    "S-Se+C-": ("Soñador", "semilla_dormida"),
    "S-Se-C+": ("Zombi", "copia_sin_esencia"),
    "S-Se-C-": ("Colapso", "quemado"),
}


def nombre_perfil(perfil: str) -> str:
    """Devuelve el nombre descriptivo del perfil."""
    entry = PERFILES_NOMBRES.get(perfil)
    return entry[0] if entry else "Desconocido"


def arquetipo_tipico_perfil(perfil: str) -> str:
    """Devuelve el arquetipo típico asociado al perfil."""
    entry = PERFILES_NOMBRES.get(perfil)
    return entry[1] if entry else "mixto"


# ---------------------------------------------------------------------------
# §5. TRANSICIONES ENTRE PERFILES (Juegos de Lentes §8)
# ---------------------------------------------------------------------------

# Secuencia natural de degradación (sin intervención): C → Se → S → Colapso
# Secuencia natural de recuperación (con intervención): S → Se → C

DEGRADACION_NATURAL = [
    ("S+Se+C+", "S+Se+C-"),  # Continuidad se pierde primero
    ("S+Se+C-", "S+Se-C-"),  # Sentido se pierde segundo
    ("S+Se-C-", "S-Se-C-"),  # Salud se pierde última
]

RECUPERACION_NATURAL = [
    ("S-Se-C-", "S+Se-C-"),  # Restaurar Salud primero
    ("S+Se-C-", "S+Se+C-"),  # Restaurar Sentido segundo
    ("S+Se+C-", "S+Se+C+"),  # Restaurar Continuidad último
]
