"""14 reglas del compilador — cada regla como función verificable.

Cada regla recibe una selección de INTs (y contexto TCF si disponible)
y devuelve pass/fail + corrección sugerida.

Fuentes: MAESTRO_V3.md §2.8, RESULTADO_CALCULOS_ANALITICOS_v1.md (Meta-Patrones)
"""
from __future__ import annotations

from dataclasses import dataclass

from src.tcf.constantes import (
    RECETAS, DEPENDENCIAS, DEPS_POR_FUNCION,
    UMBRAL_BLOQUEANTE,
)


# ---------------------------------------------------------------------------
# §1. RESULTADO DE REGLA
# ---------------------------------------------------------------------------

@dataclass
class ReglaResult:
    regla: int            # 1-14
    nombre: str
    passed: bool
    mensaje: str          # explicación si falla
    correccion: list[str] # INTs a añadir/quitar


# ---------------------------------------------------------------------------
# §2. LAS 14 REGLAS
# ---------------------------------------------------------------------------

def regla_01_nucleo_irreducible(ints: list[str], modo: str = "analisis") -> ReglaResult:
    """R1: Al menos 1 cuantitativa + 1 humana + 1 constructiva (excepto conversación)."""
    cuant = {"INT-01", "INT-02", "INT-07"}
    humana = {"INT-08", "INT-17"}
    constructiva = {"INT-16"}

    has_cuant = bool(cuant & set(ints))
    has_humana = bool(humana & set(ints))
    has_const = bool(constructiva & set(ints))

    if modo == "conversacion":
        # Relajado en conversación
        return ReglaResult(1, "Núcleo irreducible", True, "OK (conversación)", [])

    faltantes = []
    if not has_cuant:
        faltantes.append("INT-01")
    if not has_humana:
        faltantes.append("INT-08")
    if not has_const:
        faltantes.append("INT-16")

    if faltantes:
        return ReglaResult(
            1, "Núcleo irreducible", False,
            f"Falta: cuant={has_cuant}, humana={has_humana}, constructiva={has_const}",
            faltantes,
        )
    return ReglaResult(1, "Núcleo irreducible", True, "OK", [])


def regla_02_minimo_inteligencias(ints: list[str]) -> ReglaResult:
    """R2: Mínimo 3, máximo 6 inteligencias (sweet spot 4-5)."""
    n = len(ints)
    if n < 3:
        return ReglaResult(2, "Mínimo inteligencias", False, f"Solo {n}, mínimo 3", [])
    if n > 6:
        return ReglaResult(2, "Máximo inteligencias", False, f"{n} INTs, máximo 6", ints[6:])
    return ReglaResult(2, "Rango inteligencias", True, f"{n} INTs OK", [])


def regla_03_sweet_spot(ints: list[str]) -> ReglaResult:
    """R3: Sweet spot = 4-5 inteligencias."""
    n = len(ints)
    if 4 <= n <= 5:
        return ReglaResult(3, "Sweet spot", True, f"{n} INTs en sweet spot", [])
    return ReglaResult(
        3, "Sweet spot", True,  # Advertencia, no fallo
        f"{n} INTs fuera de sweet spot (4-5)", [],
    )


def regla_04_formal_primero(ints: list[str]) -> ReglaResult:
    """R4: INTs formales antes que humanas en la secuencia de composición.

    Formal: INT-01, INT-02, INT-07, INT-11 (cuantitativas/espaciales)
    Humanas: INT-08, INT-12, INT-17, INT-18 (interpretativas/existenciales)
    """
    formales = {"INT-01", "INT-02", "INT-07", "INT-11"}
    humanas = {"INT-08", "INT-12", "INT-17", "INT-18"}

    primera_formal = None
    ultima_humana_antes = None

    for i, int_id in enumerate(ints):
        if int_id in formales and primera_formal is None:
            primera_formal = i
        if int_id in humanas:
            if primera_formal is None:
                ultima_humana_antes = i

    if ultima_humana_antes is not None and primera_formal is not None:
        if ultima_humana_antes < primera_formal:
            return ReglaResult(
                4, "Formal primero", False,
                "Humana antes de formal en la secuencia",
                [],
            )

    return ReglaResult(4, "Formal primero", True, "OK", [])


def regla_05_no_redundancia_cluster(ints: list[str]) -> ReglaResult:
    """R5: No 2 INTs del mismo cluster redundante."""
    clusters_redundantes = [
        ({"INT-03", "INT-04"}, "sistémicas"),
        ({"INT-08", "INT-12"}, "interpretativas"),
        ({"INT-17", "INT-18"}, "existenciales"),
        ({"INT-03", "INT-10"}, "sistémicas-partes"),
        ({"INT-04", "INT-10"}, "sistémicas-eco"),
    ]
    for cluster, nombre in clusters_redundantes:
        if len(cluster & set(ints)) > 1:
            return ReglaResult(
                5, "No redundancia cluster", False,
                f"Cluster redundante: {nombre} ({cluster & set(ints)})",
                [],
            )
    return ReglaResult(5, "No redundancia cluster", True, "OK", [])


def regla_06_maximo_diferencial(ints: list[str]) -> ReglaResult:
    """R6: Priorizar pares de máximo diferencial."""
    pares_altos = [
        ({"INT-01", "INT-08"}, 0.95),
        ({"INT-07", "INT-17"}, 0.93),
        ({"INT-02", "INT-15"}, 0.90),
    ]
    tiene_par = False
    for par, peso in pares_altos:
        if par.issubset(set(ints)):
            tiene_par = True
            break

    if not tiene_par and len(ints) >= 4:
        return ReglaResult(
            6, "Máximo diferencial", True,  # Advertencia, no fallo
            "Ningún par de máximo diferencial incluido",
            [],
        )
    return ReglaResult(6, "Máximo diferencial", True, "OK", [])


def regla_07_confrontacion_existencial(ints: list[str], modo: str) -> ReglaResult:
    """R7: En modo confrontación, incluir INT-17 y/o INT-18."""
    if modo != "confrontacion":
        return ReglaResult(7, "Confrontación existencial", True, "No aplica", [])

    existenciales = {"INT-17", "INT-18"}
    if not existenciales & set(ints):
        return ReglaResult(
            7, "Confrontación existencial", False,
            "Modo confrontación sin existenciales",
            ["INT-17"],
        )
    return ReglaResult(7, "Confrontación existencial", True, "OK", [])


def regla_08_generacion_creativas(ints: list[str], modo: str) -> ReglaResult:
    """R8: En modo generación, priorizar INT-14, INT-15, INT-09."""
    if modo != "generacion":
        return ReglaResult(8, "Generación creativas", True, "No aplica", [])

    creativas = {"INT-14", "INT-15", "INT-09"}
    if not creativas & set(ints):
        return ReglaResult(
            8, "Generación creativas", False,
            "Modo generación sin creativas",
            ["INT-14"],
        )
    return ReglaResult(8, "Generación creativas", True, "OK", [])


def regla_09_composicion_lineal(ints: list[str]) -> ReglaResult:
    """R9: Composición lineal > agrupada. La secuencia importa."""
    # Esta regla se verifica en el compositor, no en el router.
    # Aquí solo marcamos como pass.
    return ReglaResult(9, "Composición lineal", True, "Verificar en compositor", [])


def regla_10_saturacion_n2(ints: list[str]) -> ReglaResult:
    """R10: Profundidad óptima = 2 pasadas por inteligencia."""
    # Se verifica en el ejecutor. Aquí solo marcamos como pass.
    return ReglaResult(10, "Saturación n=2", True, "Verificar en ejecutor", [])


def regla_11_no_comutatividad(ints: list[str]) -> ReglaResult:
    """R11: El orden de composición importa (no conmutativo)."""
    # Advertencia informativa — se verifica en compositor
    return ReglaResult(11, "No conmutatividad", True, "Verificar orden en compositor", [])


def regla_12_no_asociatividad(ints: list[str]) -> ReglaResult:
    """R12: (A∘B)∘C ≠ A∘(B∘C). No reordenar agrupaciones."""
    return ReglaResult(12, "No asociatividad", True, "Verificar agrupaciones", [])


def regla_13_int16_cierra(ints: list[str]) -> ReglaResult:
    """R13: INT-16 (Constructiva) debe cerrar la secuencia.

    Meta-patrón B: INT-16 cierra TODAS las recetas (11/11).
    """
    if "INT-16" not in ints:
        return ReglaResult(13, "INT-16 cierra", True, "INT-16 no presente", [])

    if ints[-1] != "INT-16":
        return ReglaResult(
            13, "INT-16 cierra", False,
            f"INT-16 no es última (pos {ints.index('INT-16')+1}/{len(ints)})",
            [],
        )
    return ReglaResult(13, "INT-16 cierra", True, "OK", [])


def regla_14_frenar(vector_dict: dict[str, float] | None = None) -> ReglaResult:
    """R14: FRENAR funciones altas con dependencias insatisfechas.

    Meta-patrón E: en arquetipos inestables, el primer paso no es mejorar
    sino DETENER la función que causa daño.

    Derivación: Ley 13 TCF (no-acción paradójica).
    """
    if vector_dict is None:
        return ReglaResult(14, "FRENAR", True, "Sin vector, no evaluable", [])

    a_frenar = []
    for fi, fj, tipo in DEPENDENCIAS:
        if tipo != "B":
            continue
        grado_fi = vector_dict.get(fi, 0)
        grado_fj = vector_dict.get(fj, 0)
        if grado_fi > 0.55 and grado_fj < UMBRAL_BLOQUEANTE:
            a_frenar.append(fi)

    if a_frenar:
        return ReglaResult(
            14, "FRENAR", False,
            f"Funciones a FRENAR: {a_frenar}",
            [],
        )
    return ReglaResult(14, "FRENAR", True, "OK", [])


# ---------------------------------------------------------------------------
# §3. VERIFICAR TODAS LAS REGLAS
# ---------------------------------------------------------------------------

def verificar_reglas(
    ints: list[str],
    modo: str = "analisis",
    vector_dict: dict[str, float] | None = None,
) -> list[ReglaResult]:
    """Ejecuta todas las reglas y devuelve resultados."""
    return [
        regla_01_nucleo_irreducible(ints, modo),
        regla_02_minimo_inteligencias(ints),
        regla_03_sweet_spot(ints),
        regla_04_formal_primero(ints),
        regla_05_no_redundancia_cluster(ints),
        regla_06_maximo_diferencial(ints),
        regla_07_confrontacion_existencial(ints, modo),
        regla_08_generacion_creativas(ints, modo),
        regla_09_composicion_lineal(ints),
        regla_10_saturacion_n2(ints),
        regla_11_no_comutatividad(ints),
        regla_12_no_asociatividad(ints),
        regla_13_int16_cierra(ints),
        regla_14_frenar(vector_dict),
    ]


def reglas_que_fallan(
    ints: list[str],
    modo: str = "analisis",
    vector_dict: dict[str, float] | None = None,
) -> list[ReglaResult]:
    """Devuelve solo las reglas que no pasan."""
    return [r for r in verificar_reglas(ints, modo, vector_dict) if not r.passed]
