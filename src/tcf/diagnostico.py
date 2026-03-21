"""Diagnóstico ACD — clasificación de estado y detección de flags.

Paso P3 del pipeline ACD: lentes → estado diagnóstico (1 de 10).
Lógica pura, sin LLM ($0).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.tcf.campo import VectorFuncional, EstadoCampo
from src.tcf.constantes import UMBRAL_LENTE_ALTA, UMBRAL_LENTE_BAJA
from src.tcf.flags import FlagPeligro, detectar_todos_flags
from src.tcf.repertorio import RepertorioCognitivo

_ESTADOS_PATH = Path(__file__).parent / "estados.json"


@dataclass
class EstadoDiagnostico:
    id: str                     # "E1", "operador_ciego", etc.
    nombre: str
    tipo: str                   # "equilibrado" | "desequilibrado"
    descripcion: str
    gap: float                  # max(lentes) - min(lentes)
    gradiente: float            # media de las 3 lentes
    lentes: dict[str, float]    # {salud, sentido, continuidad}
    flags: list[FlagPeligro] = field(default_factory=list)


def clasificar_estado(
    lentes: dict[str, float],
    scores_f_se: dict[str, float] | None = None,
) -> EstadoDiagnostico:
    """Clasifica un sistema en uno de los 10 estados ACD.

    Args:
        lentes: {salud: float, sentido: float, continuidad: float}
        scores_f_se: Scores de Se por función (para flag monopolio_se). Opcional.

    Returns:
        EstadoDiagnostico con estado, flags y métricas.
    """
    s = lentes["salud"]
    se = lentes["sentido"]
    c = lentes["continuidad"]

    gap = max(s, se, c) - min(s, se, c)
    gradiente = (s + se + c) / 3.0

    # Cargar estados para descripción/nombre
    estados_data = json.loads(_ESTADOS_PATH.read_text())

    # Detectar flags de peligro
    flags = detectar_todos_flags(lentes, scores_f_se)

    if gap < 0.15:
        # EQUILIBRADO: clasificar por gradiente
        if gradiente < 0.20:
            eid = "E1"
        elif gradiente < 0.40:
            eid = "E2"
        elif gradiente < 0.65:
            eid = "E3"
        else:
            eid = "E4"

        info = estados_data["equilibrados"][eid]
        return EstadoDiagnostico(
            id=eid,
            nombre=info["nombre"],
            tipo="equilibrado",
            descripcion=info["descripcion"],
            gap=round(gap, 3),
            gradiente=round(gradiente, 3),
            lentes=lentes,
            flags=flags,
        )

    # DESEQUILIBRADO: clasificar por distribución S/Se/C
    s_alta = s >= UMBRAL_LENTE_ALTA
    se_alta = se >= UMBRAL_LENTE_ALTA
    c_alta = c >= UMBRAL_LENTE_ALTA

    # 6 perfiles posibles (1 alta + 2 bajas, o 2 altas + 1 baja)
    if s_alta and not se_alta and not c_alta:
        did = "operador_ciego"
    elif not s_alta and se_alta and not c_alta:
        did = "visionario_atrapado"
    elif not s_alta and not se_alta and c_alta:
        did = "zombi_inmortal"
    elif s_alta and se_alta and not c_alta:
        did = "genio_mortal"
    elif s_alta and not se_alta and c_alta:
        did = "automata_eterno"
    elif not s_alta and se_alta and c_alta:
        did = "potencial_dormido"
    else:
        # Caso borde: todas bajas o todas altas pero gap >= 0.15
        # → clasificar por lente más desviada de la media
        desviaciones = {
            "salud": abs(s - gradiente),
            "sentido": abs(se - gradiente),
            "continuidad": abs(c - gradiente),
        }
        lente_max_desv = max(desviaciones, key=desviaciones.get)
        lente_val = lentes[lente_max_desv]

        if lente_val > gradiente:
            # Una lente sube por encima → perfil de 1 alta
            if lente_max_desv == "salud":
                did = "operador_ciego"
            elif lente_max_desv == "sentido":
                did = "visionario_atrapado"
            else:
                did = "zombi_inmortal"
        else:
            # Una lente baja por debajo → perfil de 2 altas
            if lente_max_desv == "salud":
                did = "potencial_dormido"
            elif lente_max_desv == "sentido":
                did = "automata_eterno"
            else:
                did = "genio_mortal"

    info = estados_data["desequilibrados"][did]
    return EstadoDiagnostico(
        id=did,
        nombre=info["nombre"],
        tipo="desequilibrado",
        descripcion=info["descripcion"],
        gap=round(gap, 3),
        gradiente=round(gradiente, 3),
        lentes=lentes,
        flags=flags,
    )


# ---------------------------------------------------------------------------
# DIAGNÓSTICO COMPLETO END-TO-END (B-ACD-08)
# ---------------------------------------------------------------------------


@dataclass
class DiagnosticoCompleto:
    """Resultado completo del pipeline diagnóstico ACD (P1-P4)."""
    # P1: Vector funcional
    scores_raw: dict[str, dict[str, float]]   # 21 scores F×L
    vector: VectorFuncional
    # P2: Estado del campo (lentes, coalición, perfil, toxicidad, atractor)
    estado_campo: EstadoCampo
    # P3: Estado diagnóstico (1 de 10) + flags
    estado: EstadoDiagnostico
    # P4: Repertorio cognitivo INT×P×R
    repertorio: RepertorioCognitivo


async def diagnosticar(caso_texto: str) -> DiagnosticoCompleto:
    """Pipeline diagnóstico ACD completo: texto → diagnóstico.

    Orquesta P1→P4:
      P1: evaluar_funcional(texto) → 21 scores + VectorFuncional
      P2: evaluar_campo(vector) → EstadoCampo (lentes, coalición, toxicidad, atractor)
      P3: clasificar_estado(lentes) → EstadoDiagnostico (1 de 10) + flags
      P4: inferir_repertorio(texto, vector) → RepertorioCognitivo + advertencias IC

    Args:
        caso_texto: Descripción del caso/sistema a diagnosticar.

    Returns:
        DiagnosticoCompleto con toda la información diagnóstica.

    Coste estimado: ~$0.005/caso (2 LLM calls Haiku: evaluador + repertorio).
    """
    import structlog
    log = structlog.get_logger()
    log.info("diagnosticar.start", caso_len=len(caso_texto))

    # P1: Derivar vector funcional desde texto
    from src.tcf.evaluador_funcional import evaluar_funcional
    scores_raw, vector = await evaluar_funcional(caso_texto)

    # P2: Evaluar campo completo (lentes, coalición, toxicidad, atractor)
    from src.tcf.campo import evaluar_campo
    estado_campo = evaluar_campo(vector)

    # P3: Clasificar estado diagnóstico (1 de 10) + flags
    # Extraer scores Se por función para flag monopolio_se
    scores_f_se = {fi: scores_raw[fi]["sentido"] for fi in scores_raw}
    estado = clasificar_estado(estado_campo.lentes, scores_f_se)

    # P4: Inferir repertorio cognitivo
    from src.tcf.repertorio import inferir_repertorio
    repertorio = await inferir_repertorio(caso_texto, vector)

    resultado = DiagnosticoCompleto(
        scores_raw=scores_raw,
        vector=vector,
        estado_campo=estado_campo,
        estado=estado,
        repertorio=repertorio,
    )

    log.info(
        "diagnosticar.ok",
        estado_id=estado.id,
        estado_nombre=estado.nombre,
        n_flags=len(estado.flags),
        n_ints_activas=len(repertorio.ints_activas),
        n_advertencias_ic=len(repertorio.advertencias_ic),
    )

    return resultado
