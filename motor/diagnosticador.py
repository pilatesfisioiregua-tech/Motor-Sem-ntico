"""Diagnosticador ACD — orquestación end-to-end del pipeline diagnóstico.

Vive en motor/ porque llama LLM (evaluador_funcional + repertorio).
El kernel (kernel/tcf/diagnostico.py) tiene la lógica pura ($0):
clasificar_estado(), EstadoDiagnostico, DiagnosticoCompleto.
"""
from __future__ import annotations

import structlog

from kernel.tcf.campo import evaluar_campo
from kernel.tcf.diagnostico import clasificar_estado, DiagnosticoCompleto

log = structlog.get_logger()


async def diagnosticar(caso_texto: str) -> DiagnosticoCompleto:
    """Pipeline diagnóstico ACD completo: texto → diagnóstico.

    Orquesta P1→P4:
      P1: evaluar_funcional(texto) → 21 scores + VectorFuncional
      P2: evaluar_campo(vector) → EstadoCampo
      P3: clasificar_estado(lentes) → EstadoDiagnostico (1 de 10) + flags
      P4: inferir_repertorio(texto, vector) → RepertorioCognitivo + advertencias IC

    Coste estimado: ~$0.005/caso (2 LLM calls vía OpenRouter).
    """
    log.info("diagnosticar.start", caso_len=len(caso_texto))

    # P1: Derivar vector funcional desde texto (LLM)
    from motor.evaluador_funcional import evaluar_funcional
    scores_raw, vector = await evaluar_funcional(caso_texto)

    # P2: Evaluar campo completo (código puro $0)
    estado_campo = evaluar_campo(vector)

    # P3: Clasificar estado diagnóstico (código puro $0)
    scores_f_se = {fi: scores_raw[fi]["sentido"] for fi in scores_raw}
    estado = clasificar_estado(estado_campo.lentes, scores_f_se)

    # P4: Inferir repertorio cognitivo (LLM)
    from motor.repertorio import inferir_repertorio
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
