"""Repertorio cognitivo — infiere INT×P×R activas/atrofiadas/ausentes.

Paso P4 del pipeline ACD:
  1. V3.2 (OpenRouter, json_schema) infiere repertorio desde texto + vector
  2. Código puro verifica leyes IC (invariantes cognitivos)
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field

from kernel.tcf.campo import VectorFuncional
from kernel.tcf.constantes import (
    FUNCIONES, NOMBRES_FUNCIONES, NOMBRES_INTELIGENCIAS,
    AFINIDAD_INT_F, AFINIDAD_INT_L,
)
from kernel.meta_red import load_inteligencias, load_pensamientos, load_razonamientos
from src.utils.openrouter_client import openrouter_json, MODEL_EXTRACTOR_OR

log = structlog.get_logger()


@dataclass
class RepertorioCognitivo:
    ints_activas: list[str]      # ["INT-10", "INT-07", ...]
    ints_atrofiadas: list[str]   # Presentes pero infrautilizadas
    ints_ausentes: list[str]     # No detectadas
    ps_activos: list[str]        # ["P07", "P13", ...]
    ps_ausentes: list[str]
    rs_activos: list[str]        # ["R01", "R07", ...]
    rs_ausentes: list[str]
    advertencias_ic: list[str] = field(default_factory=list)


SYSTEM_PROMPT_REPERTORIO = """Eres un analista cognitivo. Dado un caso y su perfil funcional, infiere qué herramientas cognitivas usa el sistema.

## HERRAMIENTAS COGNITIVAS

### 18 Inteligencias (INT)
{inteligencias_resumen}

### 15 Tipos de Pensamiento (P)
{pensamientos_resumen}

### 12 Tipos de Razonamiento (R)
{razonamientos_resumen}

## INSTRUCCIONES

Analiza el caso y su vector funcional. Clasifica cada INT, P y R en:
- **activa**: claramente presente y operando
- **atrofiada**: presente pero infrautilizada o mecánica
- **ausente**: no detectada

REGLAS:
- Toda INT debe aparecer en exactamente una categoría (activa, atrofiada o ausente)
- Todo P debe aparecer en activos o ausentes
- Todo R debe aparecer en activos o ausentes
- Sé conservador: si no hay evidencia clara, marca como ausente"""


# JSON Schema para response_format
SCHEMA_REPERTORIO = {
    "type": "object",
    "properties": {
        "ints_activas": {"type": "array", "items": {"type": "string"}},
        "ints_atrofiadas": {"type": "array", "items": {"type": "string"}},
        "ints_ausentes": {"type": "array", "items": {"type": "string"}},
        "ps_activos": {"type": "array", "items": {"type": "string"}},
        "ps_ausentes": {"type": "array", "items": {"type": "string"}},
        "rs_activos": {"type": "array", "items": {"type": "string"}},
        "rs_ausentes": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "ints_activas", "ints_atrofiadas", "ints_ausentes",
        "ps_activos", "ps_ausentes", "rs_activos", "rs_ausentes",
    ],
    "additionalProperties": False,
}


def _construir_resumen_ints() -> str:
    ints = load_inteligencias()
    lineas = []
    for int_id in sorted(ints.keys()):
        nombre = NOMBRES_INTELIGENCIAS.get(int_id, int_id)
        firma = ints[int_id].get("firma_semantica", "")
        if firma:
            lineas.append(f"- {int_id} ({nombre}): {firma}")
        else:
            lineas.append(f"- {int_id} ({nombre})")
    return "\n".join(lineas)


def _construir_resumen_ps() -> str:
    ps = load_pensamientos()
    lineas = []
    for pid in sorted(ps.keys()):
        nombre = ps[pid].get("nombre", pid)
        desc = ps[pid].get("descripcion", "")[:80]
        lineas.append(f"- {pid} ({nombre}): {desc}")
    return "\n".join(lineas)


def _construir_resumen_rs() -> str:
    rs = load_razonamientos()
    lineas = []
    for rid in sorted(rs.keys()):
        nombre = rs[rid].get("nombre", rid)
        desc = rs[rid].get("descripcion", "")[:80]
        lineas.append(f"- {rid} ({nombre}): {desc}")
    return "\n".join(lineas)


async def inferir_repertorio(
    caso_texto: str,
    vector: VectorFuncional,
) -> RepertorioCognitivo:
    """Infiere repertorio cognitivo INT×P×R desde texto + vector.

    Args:
        caso_texto: Descripción del caso.
        vector: VectorFuncional del caso (de evaluador_funcional).

    Returns:
        RepertorioCognitivo con clasificación + advertencias IC.
    """
    log.info("repertorio.start")

    system = SYSTEM_PROMPT_REPERTORIO.format(
        inteligencias_resumen=_construir_resumen_ints(),
        pensamientos_resumen=_construir_resumen_ps(),
        razonamientos_resumen=_construir_resumen_rs(),
    )

    user_msg = (
        f"CASO:\n{caso_texto}\n\n"
        f"VECTOR FUNCIONAL:\n{json.dumps(vector.to_dict(), indent=2)}\n"
        f"Eslabón débil: {vector.eslabon_debil()}"
    )

    data = await openrouter_json(
        model=MODEL_EXTRACTOR_OR,
        system=system,
        user_message=user_msg,
        schema_name="repertorio_cognitivo",
        schema=SCHEMA_REPERTORIO,
        max_tokens=1024,
        temperature=0.1,
    )

    repertorio = RepertorioCognitivo(
        ints_activas=data.get("ints_activas", []),
        ints_atrofiadas=data.get("ints_atrofiadas", []),
        ints_ausentes=data.get("ints_ausentes", []),
        ps_activos=data.get("ps_activos", []),
        ps_ausentes=data.get("ps_ausentes", []),
        rs_activos=data.get("rs_activos", []),
        rs_ausentes=data.get("rs_ausentes", []),
    )

    # Verificaciones IC (código puro, post-LLM)
    repertorio.advertencias_ic = _verificar_invariantes(repertorio, vector)

    log.info(
        "repertorio.ok",
        n_activas=len(repertorio.ints_activas),
        n_atrofiadas=len(repertorio.ints_atrofiadas),
        n_ausentes=len(repertorio.ints_ausentes),
        n_advertencias=len(repertorio.advertencias_ic),
    )

    return repertorio


def _verificar_invariantes(rep: RepertorioCognitivo, vector: VectorFuncional) -> list[str]:
    """Verificaciones IC post-LLM (código puro).

    IC2: Monopolio INT — una sola INT activa
    IC3: Desacople INT-P — INT activa sin P compatible
    IC4: Desacople INT-R — INT activa sin R compatible
    IC5: Pares complementarios faltantes
    IC6: R aislados — R activo sin INT que lo soporte
    """
    advertencias = []
    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    # IC2: Monopolio INT
    if len(rep.ints_activas) == 1 and len(rep.ints_atrofiadas) == 0:
        advertencias.append(
            f"IC2: Monopolio INT — solo {rep.ints_activas[0]} activa. "
            "Sistema frágil ante cambios."
        )

    # IC3: Desacople INT-P
    for int_id in rep.ints_activas:
        tiene_p_compatible = False
        for pid in rep.ps_activos:
            p_info = ps_data.get(pid, {})
            ints_compat = p_info.get("ints_compatibles", [])
            if int_id in ints_compat:
                tiene_p_compatible = True
                break
        if not tiene_p_compatible and rep.ps_activos:
            advertencias.append(
                f"IC3: {int_id} activa sin P compatible entre {rep.ps_activos}."
            )

    # IC4: Desacople INT-R
    for int_id in rep.ints_activas:
        tiene_r_compatible = False
        for rid in rep.rs_activos:
            r_info = rs_data.get(rid, {})
            ints_compat = r_info.get("ints_compatibles", [])
            if int_id in ints_compat:
                tiene_r_compatible = True
                break
        if not tiene_r_compatible and rep.rs_activos:
            advertencias.append(
                f"IC4: {int_id} activa sin R compatible entre {rep.rs_activos}."
            )

    # IC5: Pares complementarios básicos
    pares = [
        ("INT-01", "INT-14", "Lógica sin Divergente"),
        ("INT-02", "INT-17", "Computacional sin Existencial"),
        ("INT-05", "INT-08", "Estratégica sin Social"),
        ("INT-16", "INT-15", "Constructiva sin Estética"),
    ]
    for a, b, desc in pares:
        if a in rep.ints_activas and b in rep.ints_ausentes:
            advertencias.append(f"IC5: {desc} — {a} activa, {b} ausente.")

    # IC6: R aislados
    for rid in rep.rs_activos:
        r_info = rs_data.get(rid, {})
        ints_compat = r_info.get("ints_compatibles", [])
        if ints_compat and not any(i in rep.ints_activas for i in ints_compat):
            advertencias.append(
                f"IC6: {rid} activo sin INT soporte (necesita {ints_compat})."
            )

    return advertencias
