"""Recetas — 11 recetas + mezcla + Regla 14 (FRENAR).

Implementa:
  - generar_receta_mixta(): mezcla recetas según scoring multi-arquetipo
  - aplicar_regla_14(): detecta funciones que deben FRENARSE
  - secuencia_universal(): Teorema 2 de la TCF

Fuentes: RESULTADO_CALCULOS_ANALITICOS_v1.md Cálculo 5, §6.2
         TEORIA_CAMPO_FUNCIONAL.md Ley 13, Teorema 2
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.tcf.constantes import (
    FUNCIONES,
    RECETAS,
    DEPENDENCIAS, DEPS_POR_FUNCION,
    UMBRAL_BLOQUEANTE,
)
from src.tcf.campo import VectorFuncional
from src.tcf.arquetipos import ScoringMultiArquetipo


# ---------------------------------------------------------------------------
# §1. RECETA RESULTADO
# ---------------------------------------------------------------------------

@dataclass
class RecetaResultado:
    secuencia: list[str]       # ["F5", "F3", "F7", "F2", "F4"]
    ints: list[str]            # ["INT-02", "INT-17", "INT-15", "INT-12", "INT-16"]
    lente: str                 # "continuidad"
    frenar: list[str]          # ["F7"] si aplica Regla 14
    parar_primero: bool        # True solo para "quemado"
    arquetipo_base: str        # arquetipo primario que generó la receta base
    mezcla: bool               # True si se mezclaron recetas


# ---------------------------------------------------------------------------
# §2. REGLA 14 — FRENAR (Ley 13 TCF)
# ---------------------------------------------------------------------------

def aplicar_regla_14(vector: VectorFuncional) -> list[str]:
    """Detecta funciones altas con dependencias insatisfechas → FRENAR.

    Ley 13: Si Fi alta y Fj (dependencia bloqueante) baja,
    la intervención más eficiente es REDUCIR Fi, no subir Fj.
    """
    d = vector.to_dict()
    a_frenar = []

    for fi, fj, tipo in DEPENDENCIAS:
        if tipo != "B":
            continue
        grado_fi = d[fi]
        grado_fj = d[fj]

        # Fi significativamente alta + Fj por debajo de umbral bloqueante
        if grado_fi > 0.55 and grado_fj < UMBRAL_BLOQUEANTE:
            if fi not in a_frenar:
                a_frenar.append(fi)

    return a_frenar


# ---------------------------------------------------------------------------
# §3. GENERAR RECETA MIXTA (§6.2 Cálculos Analíticos)
# ---------------------------------------------------------------------------

def generar_receta_mixta(
    scoring: ScoringMultiArquetipo,
    vector: VectorFuncional | None = None,
) -> RecetaResultado:
    """Mezcla recetas según scoring multi-arquetipo.

    Protocolo (§6.2):
    1. Tomar receta del arquetipo primario como BASE
    2. Para cada secundario/terciario con score ≥ 0.15:
       a. Identificar funciones que SU receta ataca y la BASE no
       b. Insertar esos pasos en posición correcta según dependencias
    3. Eliminar redundancias
    4. Verificar Regla 14 (FRENAR)
    5. Asignar INTs por paso
    """
    primario = scoring.primario.arquetipo

    # Si no hay receta para el arquetipo, fallback genérico
    if primario not in RECETAS or primario == "equilibrado":
        return RecetaResultado(
            secuencia=[], ints=[], lente="salud",
            frenar=[], parar_primero=False,
            arquetipo_base=primario, mezcla=False,
        )

    receta_base = RECETAS[primario]
    secuencia = list(receta_base["secuencia"])
    ints = list(receta_base["ints"])
    lente = receta_base["lente"]
    frenar = list(receta_base.get("frenar", []))
    parar = receta_base.get("parar_primero", False)

    # Paso 2: Mezclar con secundario/terciario
    mezcla = False
    for extra in [scoring.secundario, scoring.terciario]:
        if extra is None:
            continue
        if extra.arquetipo not in RECETAS:
            continue
        receta_extra = RECETAS[extra.arquetipo]

        # Funciones que la receta extra ataca y la base no
        for f_extra in receta_extra["secuencia"]:
            if f_extra not in secuencia:
                # Insertar respetando dependencias
                pos = _posicion_insercion(f_extra, secuencia)
                secuencia.insert(pos, f_extra)
                mezcla = True

        # INTs complementarias que la base no tiene
        for int_extra in receta_extra["ints"]:
            if int_extra not in ints and len(ints) < 6:
                ints.append(int_extra)
                mezcla = True

        # Frenar adicional
        for f_frenar in receta_extra.get("frenar", []):
            if f_frenar not in frenar:
                frenar.append(f_frenar)

    # Paso 3: Aplicar Regla 14 si hay vector
    if vector is not None:
        frenar_r14 = aplicar_regla_14(vector)
        for f in frenar_r14:
            if f not in frenar:
                frenar.append(f)

    # Dedup secuencia preservando orden
    secuencia_dedup = list(dict.fromkeys(secuencia))

    return RecetaResultado(
        secuencia=secuencia_dedup,
        ints=ints,
        lente=lente,
        frenar=frenar,
        parar_primero=parar,
        arquetipo_base=primario,
        mezcla=mezcla,
    )


def _posicion_insercion(fi: str, secuencia: list[str]) -> int:
    """Determina dónde insertar fi respetando dependencias.

    Si fi depende de fj y fj ya está en la secuencia, fi va después.
    Si nada de lo que fi depende está en la secuencia, va al final.
    """
    deps = DEPS_POR_FUNCION.get(fi, [])
    ultima_dep = -1
    for fj, _tipo in deps:
        if fj in secuencia:
            idx = secuencia.index(fj)
            if idx > ultima_dep:
                ultima_dep = idx

    if ultima_dep >= 0:
        return ultima_dep + 1
    return len(secuencia)


# ---------------------------------------------------------------------------
# §4. SECUENCIA UNIVERSAL (Teorema 2 TCF)
# ---------------------------------------------------------------------------

def secuencia_universal(vector: VectorFuncional) -> list[str]:
    """Teorema 2: secuencia universal de recuperación.

    1. FRENAR funciones altas con dependencias insatisfechas (Ley 13)
    2. Subir F5 si está baja (Ley 4 + Ley 14)
    3. Subir F3 si F2 > F3 (Ley 3, prevenir intoxicación)
    4. Atacar el ESLABÓN MÁS DÉBIL (Axioma 5 — corregido post-validación)
    5. Subir las demás según prioridad de dependencias
    """
    d = vector.to_dict()
    pasos: list[str] = []

    # Paso 1: FRENAR
    for f in aplicar_regla_14(vector):
        pasos.append(f"FRENAR_{f}")

    # Paso 2: F5 si baja
    if d["F5"] < 0.40:
        pasos.append("SUBIR_F5")

    # Paso 3: F3 si F2 > F3 + margen
    if d["F2"] > d["F3"] + 0.10:
        pasos.append("SUBIR_F3")

    # Paso 4: Eslabón más débil (corregido: no siempre F1)
    debil = vector.eslabon_debil()
    paso_debil = f"SUBIR_{debil}"
    if paso_debil not in pasos:
        pasos.append(paso_debil)

    # Paso 5: Funciones restantes por debajo de 0.40, en orden de dependencias
    for f in ["F5", "F1", "F3", "F2", "F4", "F6", "F7"]:
        if d[f] < 0.40:
            paso = f"SUBIR_{f}"
            if paso not in pasos:
                pasos.append(paso)

    return pasos


# ---------------------------------------------------------------------------
# §5. PROHIBICIONES FORMALES (Leyes TCF 3, 4, 13, 14)
# ---------------------------------------------------------------------------

@dataclass
class Prohibicion:
    codigo: str          # "PRH-01", "PRH-02", etc.
    descripcion: str     # Qué se viola
    funcion_afectada: str  # "F7", "F2", etc.
    severidad: str       # "critica" | "alta"


def verificar_prohibiciones(
    secuencia: list[str],
    lentes: dict[str, float],
) -> list[Prohibicion]:
    """Detecta prohibiciones formales en una secuencia de funciones.

    Filtra combinaciones tóxicas ANTES de ejecutar. Complementa
    Regla 14 (FRENAR) y secuencia_universal().

    Args:
        secuencia: Lista de funciones en orden de ejecución.
                   Puede incluir prefijos "SUBIR_", "FRENAR_" que se limpian.
        lentes: {salud: float, sentido: float, continuidad: float}

    Returns:
        Lista de Prohibicion violadas (vacía si todo OK).
    """
    violaciones = []

    # Limpiar prefijos para trabajar con funciones puras
    funcs = [f.replace("SUBIR_", "").replace("FRENAR_", "") for f in secuencia]

    se = lentes.get("sentido", 0.0)
    gap = max(lentes.values()) - min(lentes.values()) if lentes else 0.0

    # PRH-01: F7 sin Se previo (Se < 0.40)
    if "F7" in funcs and se < 0.40:
        # F7 aparece sin que Se esté suficientemente alto
        violaciones.append(Prohibicion(
            codigo="PRH-01",
            descripcion=f"F7 (Replicar) con Se={se:.2f} < 0.40. "
                        "Amplifica sin sentido: replica mecánicamente.",
            funcion_afectada="F7",
            severidad="critica",
        ))

    # PRH-02: F2 sin F3 antes (captar sin depurar)
    if "F2" in funcs and "F3" in funcs:
        idx_f2 = funcs.index("F2")
        idx_f3 = funcs.index("F3")
        if idx_f2 < idx_f3:
            violaciones.append(Prohibicion(
                codigo="PRH-02",
                descripcion="F2 (Captar) antes de F3 (Depurar). "
                            "Captar sin depurar = intoxicación (Ley 3).",
                funcion_afectada="F2",
                severidad="alta",
            ))
    elif "F2" in funcs and "F3" not in funcs:
        # F2 presente sin F3 en absoluto
        violaciones.append(Prohibicion(
            codigo="PRH-02",
            descripcion="F2 (Captar) sin F3 (Depurar) en secuencia. "
                        "Captar sin depurar = intoxicación (Ley 3).",
            funcion_afectada="F2",
            severidad="alta",
        ))

    # PRH-03: F7 con gap > 0.30 (escalar desequilibrio)
    if "F7" in funcs and gap > 0.30:
        violaciones.append(Prohibicion(
            codigo="PRH-03",
            descripcion=f"F7 (Replicar) con gap={gap:.2f} > 0.30. "
                        "Escalar amplifica el desequilibrio entre lentes.",
            funcion_afectada="F7",
            severidad="critica",
        ))

    # PRH-04: F6 sin F5 antes (adaptar sin identidad)
    if "F6" in funcs and "F5" in funcs:
        idx_f6 = funcs.index("F6")
        idx_f5 = funcs.index("F5")
        if idx_f6 < idx_f5:
            violaciones.append(Prohibicion(
                codigo="PRH-04",
                descripcion="F6 (Adaptar) antes de F5 (Frontera). "
                            "Adaptar sin identidad = perder esencia (Ley 14).",
                funcion_afectada="F6",
                severidad="alta",
            ))
    elif "F6" in funcs and "F5" not in funcs:
        violaciones.append(Prohibicion(
            codigo="PRH-04",
            descripcion="F6 (Adaptar) sin F5 (Frontera) en secuencia. "
                        "Adaptar sin identidad = perder esencia (Ley 14).",
            funcion_afectada="F6",
            severidad="alta",
        ))

    return violaciones
