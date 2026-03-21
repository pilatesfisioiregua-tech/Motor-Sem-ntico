"""Campo funcional dual — representación numérica + semántica coexistiendo.

Extiende campo.py SIN modificarlo. VectorFuncionalDual envuelve 7 CeldaCampo
y expone .numerico() → VectorFuncional para compatibilidad total con TCF.

Fuente: docs/L0/GRADIENTES_DUALES.md
Principio: P41 (CR0) — "Los gradientes son duales."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.tcf.campo import VectorFuncional, EstadoCampo, evaluar_campo
from src.tcf.constantes import FUNCIONES


# ---------------------------------------------------------------------------
# §1. CELDA CAMPO — unidad dual
# ---------------------------------------------------------------------------

@dataclass
class CeldaCampo:
    """Una celda del campo funcional con representación dual."""
    funcion: str              # "F3"
    lente: str                # "salud" (lente primaria para esta celda)

    # Representación numérica
    grado: float              # 0.25

    # Representación semántica (todas opcionales — se llenan progresivamente)
    estado: Optional[str] = None          # diagnóstico actual
    objetivo: Optional[str] = None        # estado objetivo
    gap_semantico: Optional[str] = None   # qué hay que cambiar, en palabras
    evidencias: list[str] = field(default_factory=list)

    # Metadata
    fuente: str = "estimado"    # "motor_vn" | "reactor_v4" | "usuario" | "estimado"
    confianza: float = 0.5      # 0.0-1.0
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not (0.0 <= self.grado <= 1.0):
            raise ValueError(f"grado={self.grado} fuera de rango [0, 1]")
        if not (0.0 <= self.confianza <= 1.0):
            raise ValueError(f"confianza={self.confianza} fuera de rango [0, 1]")

    def tiene_semantica(self) -> bool:
        """True si la celda tiene al menos estado o evidencias."""
        return self.estado is not None or len(self.evidencias) > 0

    def to_dict(self) -> dict:
        """Serializa para JSON/DB."""
        d = {
            "funcion": self.funcion,
            "lente": self.lente,
            "grado": self.grado,
            "fuente": self.fuente,
            "confianza": self.confianza,
        }
        if self.estado is not None:
            d["estado"] = self.estado
        if self.objetivo is not None:
            d["objetivo"] = self.objetivo
        if self.gap_semantico is not None:
            d["gap_semantico"] = self.gap_semantico
        if self.evidencias:
            d["evidencias"] = self.evidencias
        if self.timestamp is not None:
            d["timestamp"] = self.timestamp
        return d

    @classmethod
    def from_dict(cls, d: dict) -> CeldaCampo:
        return cls(
            funcion=d["funcion"],
            lente=d.get("lente", "salud"),
            grado=d["grado"],
            estado=d.get("estado"),
            objetivo=d.get("objetivo"),
            gap_semantico=d.get("gap_semantico"),
            evidencias=d.get("evidencias", []),
            fuente=d.get("fuente", "estimado"),
            confianza=d.get("confianza", 0.5),
            timestamp=d.get("timestamp"),
        )

    @classmethod
    def solo_numerico(cls, funcion: str, grado: float, lente: str = "salud") -> CeldaCampo:
        """Crea celda con solo grado numérico (Tier 1-2, lookup)."""
        return cls(funcion=funcion, lente=lente, grado=grado)


# ---------------------------------------------------------------------------
# §2. VECTOR FUNCIONAL DUAL — 7 celdas
# ---------------------------------------------------------------------------

@dataclass
class VectorFuncionalDual:
    """Vector de estado dual: 7 funciones × (número + semántica)."""
    celdas: dict[str, CeldaCampo]  # "F1" → CeldaCampo, ..., "F7" → CeldaCampo

    def __post_init__(self):
        for f in FUNCIONES:
            if f not in self.celdas:
                raise ValueError(f"Falta función {f} en celdas")

    def numerico(self) -> VectorFuncional:
        """Extrae solo la parte numérica. Compatibilidad total con TCF existente."""
        return VectorFuncional.from_dict({
            f: self.celdas[f].grado for f in FUNCIONES
        })

    def grado(self, funcion: str) -> float:
        """Acceso rápido al grado numérico de una función."""
        return self.celdas[funcion].grado

    def estado(self, funcion: str) -> Optional[str]:
        """Descripción semántica del estado actual de una función."""
        return self.celdas[funcion].estado

    def gap_semantico(self, funcion: str) -> Optional[str]:
        """Gap semántico de una función."""
        return self.celdas[funcion].gap_semantico

    def evidencias(self, funcion: str) -> list[str]:
        """Evidencias que soportan el grado de una función."""
        return self.celdas[funcion].evidencias

    def tiene_semantica(self) -> bool:
        """True si al menos una celda tiene semántica."""
        return any(c.tiene_semantica() for c in self.celdas.values())

    def cobertura_semantica(self) -> float:
        """Proporción de celdas con semántica (0.0-1.0)."""
        n = sum(1 for c in self.celdas.values() if c.tiene_semantica())
        return n / len(FUNCIONES)

    def to_dict(self) -> dict:
        return {f: self.celdas[f].to_dict() for f in FUNCIONES}

    @classmethod
    def from_dict(cls, d: dict) -> VectorFuncionalDual:
        celdas = {f: CeldaCampo.from_dict(v) for f, v in d.items()}
        return cls(celdas=celdas)

    @classmethod
    def desde_vector_numerico(
        cls,
        vector: VectorFuncional,
        lente: str = "salud",
        fuente: str = "estimado",
    ) -> VectorFuncionalDual:
        """Crea dual desde un VectorFuncional existente (solo números, sin semántica)."""
        d = vector.to_dict()
        celdas = {
            f: CeldaCampo.solo_numerico(funcion=f, grado=d[f], lente=lente)
            for f in FUNCIONES
        }
        for c in celdas.values():
            c.fuente = fuente
        return cls(celdas=celdas)


# ---------------------------------------------------------------------------
# §3. ESTADO CAMPO DUAL — campo completo con ambas capas
# ---------------------------------------------------------------------------

@dataclass
class EstadoCampoDual:
    """Estado completo del campo con representación dual.

    Envuelve EstadoCampo (numérico, ya existe) + VectorFuncionalDual (nuevo).
    """
    # Capa numérica (la que ya existe — generada por evaluar_campo)
    estado_numerico: EstadoCampo

    # Capa dual (nueva)
    vector_dual: VectorFuncionalDual

    # Diagnóstico integrado (se llena en fases posteriores)
    diagnostico_natural: Optional[str] = None
    intervenciones_concretas: list[str] = field(default_factory=list)

    @classmethod
    def desde_vector_dual(cls, vector_dual: VectorFuncionalDual) -> EstadoCampoDual:
        """Crea estado completo: evalúa TCF numérica + mantiene semántica."""
        estado_numerico = evaluar_campo(vector_dual.numerico())
        return cls(
            estado_numerico=estado_numerico,
            vector_dual=vector_dual,
        )

    @classmethod
    def desde_vector_numerico(cls, vector: VectorFuncional) -> EstadoCampoDual:
        """Crea estado dual desde vector solo numérico (upgrade path)."""
        dual = VectorFuncionalDual.desde_vector_numerico(vector)
        estado_numerico = evaluar_campo(vector)
        return cls(
            estado_numerico=estado_numerico,
            vector_dual=dual,
        )
