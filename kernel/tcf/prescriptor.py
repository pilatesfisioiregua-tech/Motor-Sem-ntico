"""Prescriptor ACD — selección cognitiva INT×P×R.

Dado un DiagnosticoCompleto, prescribe:
  - Qué INTs activar (base por arquetipo + refuerzo por lente faltante)
  - Qué Ps usar (por estado diagnóstico)
  - Qué Rs usar (por estado diagnóstico)
  - Secuencia de funciones (receta + prohibiciones)
  - Nivel lógico y modos conceptuales
  - Funciones a FRENAR
  - Objetivo de la prescripción

Código puro, $0, sin LLM.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from kernel.tcf.arquetipos import scoring_multi_arquetipo
from kernel.tcf.campo import VectorFuncional
from kernel.tcf.constantes import TOP_INTS_POR_LENTE, LENTES
from kernel.tcf.nivel_logico import seleccionar_nivel_modo, NivelModo
from kernel.tcf.recetas import (
    generar_receta_mixta,
    verificar_prohibiciones,
    RecetaResultado,
    Prohibicion,
)
from kernel.meta_red import load_pensamientos, load_razonamientos

_ESTADOS_PATH = Path(__file__).parent / "estados.json"


@dataclass
class Prescripcion:
    # INTs
    ints: list[str]               # INTs a activar (base + refuerzo, dedup)
    ints_refuerzo: list[str]      # INTs añadidas por lente faltante (subset de ints)

    # P y R
    ps: list[str]                 # Tipos de pensamiento prescritos
    rs: list[str]                 # Tipos de razonamiento prescritos

    # Secuencia
    secuencia: list[str]          # Funciones en orden de ejecución
    frenar: list[str]             # Funciones a FRENAR (Regla 14 + receta)
    parar_primero: bool           # True solo para "quemado"

    # Nivel y modo
    lente_objetivo: str           # Lente más baja (foco de la intervención)
    nivel_logico: NivelModo       # Nivel + modos (de B-ACD-10)

    # Objetivo
    objetivo: str                 # "CUESTIONAR premisas", "EJECUTAR", etc.

    # Diagnóstico de la prescripción
    prohibiciones_violadas: list[Prohibicion] = field(default_factory=list)
    advertencias_ic: list[str] = field(default_factory=list)

    # Metadata
    arquetipo_base: str = ""      # Arquetipo primario que generó la receta
    estado_id: str = ""           # ID del estado diagnóstico


def prescribir(diagnostico) -> Prescripcion:
    """Genera prescripción completa desde DiagnosticoCompleto.

    Args:
        diagnostico: DiagnosticoCompleto (de B-ACD-08).
                     Type hint omitido para evitar import circular.

    Returns:
        Prescripcion con INTs, Ps, Rs, secuencia, modos, objetivo.
    """
    vector = diagnostico.vector
    estado = diagnostico.estado
    repertorio = diagnostico.repertorio
    lentes = diagnostico.estado_campo.lentes

    # --- 1. Receta base por arquetipo ---
    scoring = scoring_multi_arquetipo(vector)
    receta = generar_receta_mixta(scoring, vector)

    # --- 2. P y R desde estado diagnóstico (estados.json) ---
    estados_data = json.loads(_ESTADOS_PATH.read_text())

    ps_prescritos = []
    rs_prescritos = []
    objetivo = ""

    if estado.tipo == "desequilibrado" and estado.id in estados_data["desequilibrados"]:
        info = estados_data["desequilibrados"][estado.id]
        ps_prescritos = info.get("prescripcion_ps", [])
        rs_prescritos = info.get("prescripcion_rs", [])
        objetivo = info.get("objetivo_prescripcion", "")
    elif estado.tipo == "equilibrado":
        # Estados equilibrados: mantener, no prescribir agresivamente
        objetivo = "MANTENER" if estado.id in ("E3", "E4") else "ACTIVAR"

    # --- 3. INTs de refuerzo por lente faltante ---
    lente_baja = min(lentes, key=lentes.get)
    ints_refuerzo = TOP_INTS_POR_LENTE.get(lente_baja, [])

    # Fusionar INTs: receta base + refuerzo, dedup preservando orden
    ints_base = list(receta.ints)
    ints_todas = list(dict.fromkeys(ints_base + ints_refuerzo))

    # --- 4. Nivel lógico + modos (B-ACD-10) ---
    nivel_modo = seleccionar_nivel_modo(lente_baja)

    # --- 5. Verificar prohibiciones (B-ACD-11) ---
    prohibiciones = verificar_prohibiciones(receta.secuencia, lentes)

    # --- 6. Verificar compatibilidad IC3/IC4/IC5 ---
    advertencias = _verificar_compatibilidad_prescripcion(
        ints_todas, ps_prescritos, rs_prescritos,
    )

    return Prescripcion(
        ints=ints_todas,
        ints_refuerzo=ints_refuerzo,
        ps=ps_prescritos,
        rs=rs_prescritos,
        secuencia=receta.secuencia,
        frenar=receta.frenar,
        parar_primero=receta.parar_primero,
        lente_objetivo=lente_baja,
        nivel_logico=nivel_modo,
        objetivo=objetivo,
        prohibiciones_violadas=prohibiciones,
        advertencias_ic=advertencias,
        arquetipo_base=receta.arquetipo_base,
        estado_id=estado.id,
    )


def _verificar_compatibilidad_prescripcion(
    ints: list[str],
    ps: list[str],
    rs: list[str],
) -> list[str]:
    """Verifica compatibilidad INT-P (IC3) e INT-R (IC4) de la prescripción.

    A diferencia de repertorio.py (que verifica lo que el sistema YA tiene),
    aquí verificamos que lo que PRESCRIBIMOS sea coherente internamente.

    También verifica pares complementarios (IC5).
    """
    advertencias = []
    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    # IC3: Cada P prescrito debería tener al menos 1 INT compatible prescrita
    for pid in ps:
        p_info = ps_data.get(pid, {})
        ints_compat = p_info.get("ints_compatibles", [])
        if ints_compat and not any(i in ints for i in ints_compat):
            advertencias.append(
                f"IC3-PRE: {pid} prescrito sin INT compatible en prescripción "
                f"(necesita alguna de {ints_compat})."
            )

    # IC4: Cada R prescrito debería tener al menos 1 INT compatible prescrita
    for rid in rs:
        r_info = rs_data.get(rid, {})
        ints_compat = r_info.get("ints_compatibles", [])
        if ints_compat and not any(i in ints for i in ints_compat):
            advertencias.append(
                f"IC4-PRE: {rid} prescrito sin INT compatible en prescripción "
                f"(necesita alguna de {ints_compat})."
            )

    # IC5: Si prescribimos INT-01 (Lógica) sin INT-14 (Divergente), advertir
    pares = [
        ("INT-01", "INT-14", "Lógica sin Divergente"),
        ("INT-02", "INT-17", "Computacional sin Existencial"),
        ("INT-05", "INT-08", "Estratégica sin Social"),
        ("INT-16", "INT-15", "Constructiva sin Estética"),
    ]
    for a, b, desc in pares:
        if a in ints and b not in ints:
            advertencias.append(f"IC5-PRE: {desc} — prescribir {b} como complemento.")

    return advertencias
