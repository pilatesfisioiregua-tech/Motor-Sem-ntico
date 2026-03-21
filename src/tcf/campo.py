"""Campo funcional — VectorFuncional, EstadoCampo, evaluar_campo().

Implementa:
  - Ley 1: Dependencia jerárquica (grado_efectivo)
  - Ley 2: Acoplamiento funcional (bloqueante/degradante)
  - Ley 3: Retroalimentación tóxica (con factor de intensidad)
  - Ley 4: F5 como base
  - Ley 8: Mapa función→lente (lentes emergentes)
  - Ley 9: Estabilidad por coherencia de dependencias
  - Ley 10: Atractor más cercano
  - Ley 11: Entropía funcional (eslabón más débil)
  - Axioma 5: Eslabón más débil

Fuentes: TEORIA_CAMPO_FUNCIONAL.md, TEORIA_JUEGOS_LENTES.md
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.tcf.constantes import (
    FUNCIONES, LENTES,
    DEPENDENCIAS, DEPS_POR_FUNCION, DEPENDIENTES_DE,
    VALORACION_F_L,
    ARQUETIPOS_CANONICOS,
    UMBRAL_BLOQUEANTE, UMBRAL_DEGRADANTE,
    UMBRAL_PERCEPCION_TOXICIDAD,
    UMBRAL_LENTE_ALTA, UMBRAL_LENTE_BAJA,
)


# ---------------------------------------------------------------------------
# §1. VECTOR FUNCIONAL
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VectorFuncional:
    """Vector de estado de un sistema: 7 funciones con grado 0.0-1.0."""
    f1: float  # Conservar
    f2: float  # Captar
    f3: float  # Depurar
    f4: float  # Distribuir
    f5: float  # Frontera
    f6: float  # Adaptar
    f7: float  # Replicar

    def __post_init__(self):
        for name in ("f1", "f2", "f3", "f4", "f5", "f6", "f7"):
            val = getattr(self, name)
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{name}={val} fuera de rango [0, 1]")

    def to_dict(self) -> dict[str, float]:
        return {
            "F1": self.f1, "F2": self.f2, "F3": self.f3, "F4": self.f4,
            "F5": self.f5, "F6": self.f6, "F7": self.f7,
        }

    @classmethod
    def from_dict(cls, d: dict[str, float]) -> VectorFuncional:
        return cls(
            f1=d["F1"], f2=d["F2"], f3=d["F3"], f4=d["F4"],
            f5=d["F5"], f6=d["F6"], f7=d["F7"],
        )

    def grado(self, fi: str) -> float:
        """Acceso por nombre de función: 'F1' -> self.f1."""
        return getattr(self, fi.lower())

    def eslabon_debil(self) -> str:
        """Axioma 5: función con menor grado."""
        d = self.to_dict()
        return min(d, key=d.get)

    def distancia(self, otro: VectorFuncional) -> float:
        """Distancia euclídea normalizada [0, 1]."""
        d = self.to_dict()
        o = otro.to_dict()
        suma = sum((d[f] - o[f]) ** 2 for f in FUNCIONES)
        # Max distancia posible = sqrt(7) ≈ 2.6457
        return math.sqrt(suma) / math.sqrt(len(FUNCIONES))


# ---------------------------------------------------------------------------
# §2. DEPENDENCIA VIOLADA
# ---------------------------------------------------------------------------

@dataclass
class DependenciaViolada:
    fi: str           # función dependiente
    fj: str           # función de la que depende
    tipo: str         # "B" o "D"
    grado_fi: float
    grado_fj: float
    brecha: float     # grado_fi - grado_fj (si >0, Fi supera su soporte)


# ---------------------------------------------------------------------------
# §3. TOXICIDAD POR PAR
# ---------------------------------------------------------------------------

@dataclass
class Toxicidad:
    fi: str
    fj: str
    tipo: str         # solo "B" genera toxicidad directa (Ley 3)
    valor: float      # grado(Fi) × (1 - grado(Fj)) × factor_brecha
    subliminal: bool  # True si brecha < umbral_percepcion


# ---------------------------------------------------------------------------
# §4. ESTADO DEL CAMPO
# ---------------------------------------------------------------------------

@dataclass
class EstadoCampo:
    vector: VectorFuncional
    lentes: dict[str, float]                # {salud: 0.40, sentido: 0.60, continuidad: 0.20}
    coalicion: str                          # "salud_sentido", "salud_continuidad", etc.
    perfil_lente: str                       # "S+Se+C-" etc.
    dependencias_violadas: list[DependenciaViolada]
    toxicidades: list[Toxicidad]
    toxicidad_total: float
    eslabon_debil: str                      # "F7"
    atractor_mas_cercano: str               # "equilibrio", "rigidez", "colapso", "aislamiento"
    estable: bool                           # True si no hay violaciones bloqueantes severas


# ---------------------------------------------------------------------------
# §5. CALCULAR LENTES (Ley 8)
# ---------------------------------------------------------------------------

def calcular_lentes(vector: VectorFuncional) -> dict[str, float]:
    """Calcula grado de cada lente como emergente de las funciones.

    L_j = Σ_i (v(j, Fi) × grado(Fi)) / Σ_i v(j, Fi)

    Normalizado a [0, 1].
    """
    d = vector.to_dict()
    resultado = {}
    for lente in LENTES:
        numerador = sum(
            VALORACION_F_L[f][lente] * d[f]
            for f in FUNCIONES
        )
        denominador = sum(
            VALORACION_F_L[f][lente]
            for f in FUNCIONES
        )
        resultado[lente] = numerador / denominador if denominador > 0 else 0.0
    return resultado


# ---------------------------------------------------------------------------
# §6. DETECTAR COALICIÓN (Juegos de Lentes §3)
# ---------------------------------------------------------------------------

def detectar_coalicion(lentes: dict[str, float]) -> str:
    """Identifica qué coalición de lentes domina.

    Coaliciones posibles:
      - salud_sentido: S y Se altas, C baja → Máquina sin Alma
      - salud_continuidad: S y C altas, Se baja → Franquicia Vacía
      - sentido_continuidad: Se y C altas, S baja → Profeta sin Recursos
      - ninguna: las 3 altas (equilibrado) o las 3 bajas (colapso) o disputa
    """
    s = lentes["salud"]
    se = lentes["sentido"]
    c = lentes["continuidad"]

    s_alta = s >= UMBRAL_LENTE_ALTA
    se_alta = se >= UMBRAL_LENTE_ALTA
    c_alta = c >= UMBRAL_LENTE_ALTA

    if s_alta and se_alta and not c_alta:
        return "salud_sentido"
    if s_alta and c_alta and not se_alta:
        return "salud_continuidad"
    if se_alta and c_alta and not s_alta:
        return "sentido_continuidad"
    return "ninguna"


# ---------------------------------------------------------------------------
# §7. PERFIL DE LENTE (Juegos de Lentes §6)
# ---------------------------------------------------------------------------

def identificar_perfil_lente(lentes: dict[str, float]) -> str:
    """Clasifica en uno de los 8 perfiles binarios.

    Formato: "S+Se+C-" donde + = alta, - = baja.
    """
    partes = []
    for lente, abbr in [("salud", "S"), ("sentido", "Se"), ("continuidad", "C")]:
        if lentes[lente] >= UMBRAL_LENTE_ALTA:
            partes.append(f"{abbr}+")
        else:
            partes.append(f"{abbr}-")
    return "".join(partes)


# ---------------------------------------------------------------------------
# §8. DETECTAR DEPENDENCIAS VIOLADAS (Ley 9)
# ---------------------------------------------------------------------------

def detectar_dependencias_violadas(
    vector: VectorFuncional,
) -> list[DependenciaViolada]:
    """Ley 9: encontrar dependencias insatisfechas."""
    d = vector.to_dict()
    violaciones = []

    for fi, fj, tipo in DEPENDENCIAS:
        grado_fi = d[fi]
        grado_fj = d[fj]
        umbral = UMBRAL_BLOQUEANTE if tipo == "B" else UMBRAL_DEGRADANTE

        # Fi significativa y Fj por debajo del umbral
        if grado_fi > 0.25 and grado_fj < umbral:
            violaciones.append(DependenciaViolada(
                fi=fi, fj=fj, tipo=tipo,
                grado_fi=grado_fi, grado_fj=grado_fj,
                brecha=max(0, grado_fi - grado_fj),
            ))

    return violaciones


# ---------------------------------------------------------------------------
# §9. EVALUAR TOXICIDAD (Ley 3 corregida)
# ---------------------------------------------------------------------------

def evaluar_toxicidad(vector: VectorFuncional) -> list[Toxicidad]:
    """Ley 3 con factor de intensidad: toxicidad proporcional a la brecha.

    Toxicidad(Fi, Fj) = grado(Fi) × (1 - grado(Fj)) × factor_brecha
    factor_brecha = max(0, (grado(Fi) - grado(Fj)) - umbral_percepcion)
    """
    d = vector.to_dict()
    toxicidades = []

    for fi, fj, tipo in DEPENDENCIAS:
        if tipo != "B":
            continue  # Solo bloqueantes generan toxicidad directa

        grado_fi = d[fi]
        grado_fj = d[fj]
        brecha = grado_fi - grado_fj

        if brecha <= 0:
            continue  # Fi no supera Fj, no hay toxicidad

        factor_brecha = max(0, brecha - UMBRAL_PERCEPCION_TOXICIDAD)
        valor = grado_fi * (1 - grado_fj) * factor_brecha
        subliminal = brecha < UMBRAL_PERCEPCION_TOXICIDAD

        if valor > 0 or subliminal:
            toxicidades.append(Toxicidad(
                fi=fi, fj=fj, tipo=tipo,
                valor=round(valor, 4),
                subliminal=subliminal,
            ))

    return toxicidades


# ---------------------------------------------------------------------------
# §10. ATRACTOR MÁS CERCANO (Ley 10)
# ---------------------------------------------------------------------------

def atractor_mas_cercano(vector: VectorFuncional) -> str:
    """Determina hacia qué atractor converge el sistema."""
    d = vector.to_dict()
    media = sum(d.values()) / len(d)

    # Colapso: media muy baja
    if media < 0.30:
        return "colapso"

    # Aislamiento: F5 muy alta, F2 muy baja
    if d["F5"] > 0.70 and d["F2"] < 0.30:
        return "aislamiento"

    # Rigidez: F1 alta, F6 baja
    if d["F1"] > 0.60 and d["F6"] < 0.35:
        return "rigidez"

    # Equilibrio: todas las funciones en rango medio-alto
    if min(d.values()) > 0.45:
        return "equilibrio"

    # Default: entre rigidez y colapso según la tendencia
    if d["F1"] > 0.50:
        return "rigidez"
    return "colapso"


# ---------------------------------------------------------------------------
# §11. EVALUAR CAMPO COMPLETO
# ---------------------------------------------------------------------------

def evaluar_campo(vector: VectorFuncional) -> EstadoCampo:
    """Evalúa el campo funcional aplicando las 14 leyes TCF.

    Entrada: VectorFuncional (7 grados)
    Salida: EstadoCampo completo (lentes, coalición, perfil, dependencias,
            toxicidad, eslabón débil, atractor, estabilidad)
    """
    # Ley 8: Lentes emergentes
    lentes = calcular_lentes(vector)

    # Juegos de Lentes §3: Coalición dominante
    coalicion = detectar_coalicion(lentes)

    # Juegos de Lentes §6: Perfil de lente
    perfil = identificar_perfil_lente(lentes)

    # Ley 9: Dependencias violadas
    deps_violadas = detectar_dependencias_violadas(vector)

    # Ley 3: Toxicidad
    toxicidades = evaluar_toxicidad(vector)
    toxicidad_total = sum(t.valor for t in toxicidades)

    # Axioma 5: Eslabón débil
    eslabon = vector.eslabon_debil()

    # Ley 10: Atractor
    atractor = atractor_mas_cercano(vector)

    # Estabilidad: no hay violaciones bloqueantes
    bloqueantes = [dv for dv in deps_violadas if dv.tipo == "B"]
    estable = len(bloqueantes) == 0

    return EstadoCampo(
        vector=vector,
        lentes={k: round(v, 3) for k, v in lentes.items()},
        coalicion=coalicion,
        perfil_lente=perfil,
        dependencias_violadas=deps_violadas,
        toxicidades=toxicidades,
        toxicidad_total=round(toxicidad_total, 4),
        eslabon_debil=eslabon,
        atractor_mas_cercano=atractor,
        estable=estable,
    )
