"""Capa 1: Selección de inteligencias (Sonnet)."""
from __future__ import annotations

import json
import time
import structlog
from dataclasses import dataclass, field

from src.config.settings import MODEL_ROUTER
from src.meta_red import load_inteligencias
from src.pipeline.detector_huecos import DetectorResult
from src.tcf.detector_tcf import DetectorTCFResult
from src.config.reglas import verificar_reglas, reglas_que_fallan
from src.gestor.programa import ProgramaCompilado

log = structlog.get_logger()


ROUTER_SYSTEM = """Eres un router de inteligencias. Tu trabajo es seleccionar las 4-5 inteligencias más relevantes para analizar el input del usuario.

CATÁLOGO DE INTELIGENCIAS:
{catalogo}

REGLAS OBLIGATORIAS:
1. SIEMPRE incluir al menos 1 de {{INT-01, INT-02}} (cuantitativa) + 1 de {{INT-08, INT-17}} (humana) + INT-16 (constructiva). Sin este triángulo, el análisis está incompleto.
2. Priorizar pares de máximo diferencial: INT-01×INT-08 (0.95), INT-07×INT-17 (0.93), INT-02×INT-15 (0.90).
3. Sweet spot: 4-5 inteligencias. Nunca menos de 3. Nunca más de 6.
4. Evitar pares redundantes del mismo cluster: INT-03+INT-04 (sistémicas), INT-08+INT-12 (interpretativas), INT-17+INT-18 (existenciales).

MODO: {modo}
- análisis: 4-5 inteligencias, máximo diferencial
- generación: priorizar INT-14, INT-15, INT-09 (creativas)
- conversación: 2-3 inteligencias, las más directamente relevantes
- confrontación: incluir INT-17 y/o INT-18 (frontera)

{huecos_info}

Responde SOLO con un JSON válido, sin markdown, sin explicación:
{{
  "inteligencias": ["INT-XX", "INT-YY", ...],
  "razon": "explicación breve de la selección",
  "pares_complementarios": [["INT-XX", "INT-YY"], ...],
  "descartadas": ["INT-ZZ", ...]
}}"""


# Configuración por modo
MODE_CONFIG = {
    'analisis':       {'k': 5, 'temperature': 0.2},
    'generacion':     {'k': 4, 'temperature': 0.4},
    'conversacion':   {'k': 3, 'temperature': 0.1},
    'confrontacion':  {'k': 5, 'temperature': 0.3},
}


@dataclass
class RouterResult:
    inteligencias: list[str]
    pares_complementarios: list[list[str]]
    descartadas: list[str]
    razon: str
    cost: float = 0.0
    time_s: float = 0.0
    reglas_aplicadas: list[dict] = field(default_factory=list)


def build_catalogo(inteligencias_data: dict) -> str:
    """Genera catálogo de firmas para el prompt del router."""
    lines = []
    for int_id in sorted(inteligencias_data.keys()):
        d = inteligencias_data[int_id]
        lines.append(f"{int_id} | {d['nombre']} | Firma: {d['firma']} | Punto ciego: {d['punto_ciego']}")
    return "\n".join(lines)


def enforce_rules(selected: list[str], modo: str) -> list[str]:
    """Aplica reglas obligatorias sobre la selección del LLM."""
    result = list(selected)

    # Regla 1: Núcleo irreducible
    has_quant = any(i in result for i in ['INT-01', 'INT-02'])
    has_human = any(i in result for i in ['INT-08', 'INT-17'])
    has_constructive = 'INT-16' in result

    if not has_quant:
        result.append('INT-01')  # Default cuantitativa
    if not has_human:
        result.append('INT-08')  # Default humana
    if not has_constructive and modo != 'conversacion':
        result.append('INT-16')

    # Regla 3: Límites
    if len(result) > 6:
        result = result[:6]
    if len(result) < 3:
        pass  # No debería pasar con las reglas anteriores

    # Regla: Confrontación requiere existenciales
    if modo == 'confrontacion':
        if 'INT-17' not in result and 'INT-18' not in result:
            result.append('INT-17')

    # Dedup preservando orden
    seen: set[str] = set()
    deduped: list[str] = []
    for i in result:
        if i not in seen:
            seen.add(i)
            deduped.append(i)
    return deduped


async def route(
    input_text: str,
    contexto: str | None,
    modo: str,
    forzadas: list[str],
    excluidas: list[str],
    huecos: DetectorResult | None = None,
    tcf: DetectorTCFResult | None = None,
    programa: ProgramaCompilado | None = None,
) -> RouterResult:
    """Selecciona inteligencias para el input dado. Usa programa del Gestor, TCF y huecos."""
    from src.utils.llm_client import llm

    inteligencias_data = load_inteligencias()
    catalogo = build_catalogo(inteligencias_data)
    config = MODE_CONFIG.get(modo, MODE_CONFIG['analisis'])

    # Info de huecos para el prompt
    huecos_info = ""
    if huecos and huecos.inteligencias_sugeridas:
        huecos_info = (
            f"HUECOS DETECTADOS (Capa 0 sugiere priorizar): "
            f"{', '.join(huecos.inteligencias_sugeridas)}\n"
            f"Diagnóstico acople: {huecos.diagnostico_acople}"
        )

    # Info TCF para el prompt
    tcf_info = ""
    if tcf and tcf.scoring:
        tcf_info = (
            f"\nARQUETIPO DETECTADO: {tcf.scoring.primario.arquetipo} "
            f"(score {tcf.scoring.primario.score})\n"
        )
        if tcf.receta:
            tcf_info += f"RECETA PRESCRITA: {', '.join(tcf.receta.ints)}\n"
            tcf_info += f"LENTE PRIMARIA: {tcf.receta.lente}\n"
            if tcf.receta.frenar:
                tcf_info += f"FUNCIONES A FRENAR: {', '.join(tcf.receta.frenar)}\n"
            tcf_info += "IMPORTANTE: La receta tiene prioridad. Tu selección COMPLEMENTA, no reemplaza.\n"

    # Info del programa del Gestor para el prompt
    programa_info = ""
    if programa and programa.pasos:
        programa_info = (
            f"\nPROGRAMA COMPILADO POR EL GESTOR (tier {programa.tier}):\n"
            f"  INTs prescritas: {', '.join(programa.inteligencias())}\n"
            f"  Lente primaria: {programa.lente_primaria}\n"
            f"  Funciones objetivo: {[p.funcion_objetivo for p in programa.pasos]}\n"
        )
        if programa.frenar:
            programa_info += f"  FRENAR: {', '.join(programa.frenar)}\n"
        programa_info += "IMPORTANTE: El programa del Gestor tiene prioridad. Tu selección COMPLEMENTA.\n"

    system_prompt = ROUTER_SYSTEM.format(
        catalogo=catalogo,
        modo=modo,
        huecos_info=huecos_info + tcf_info + programa_info,
    )

    user_msg = input_text
    if contexto:
        user_msg = f"CONTEXTO: {contexto}\n\nINPUT: {input_text}"

    t0 = time.time()
    raw = await llm.complete(
        model=MODEL_ROUTER,
        system=system_prompt,
        user_message=user_msg,
        max_tokens=1024,
        temperature=config['temperature'],
    )
    elapsed = time.time() - t0

    # Parse JSON del LLM
    try:
        # Limpiar posible markdown wrapping
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.split("\n")[1:-1])
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        log.error("router_json_parse_error", raw=raw[:200])
        # Fallback: selección por defecto
        data = {
            "inteligencias": ["INT-01", "INT-08", "INT-16", "INT-07", "INT-05"],
            "razon": "Fallback por error de parsing",
            "pares_complementarios": [],
            "descartadas": [],
        }

    selected = data.get("inteligencias", [])

    # GESTOR: si hay programa compilado, usarlo como base (tiene prioridad sobre TCF directo)
    if programa and programa.pasos:
        programa_ints = programa.inteligencias()
        merged = list(programa_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged
        log.info("router_usando_programa_gestor", ints_programa=programa_ints)
    # Fallback: TCF directo si no hay programa
    elif tcf and tcf.receta and tcf.receta.ints:
        receta_ints = tcf.receta.ints
        merged = list(receta_ints)
        for s in selected:
            if s not in merged and len(merged) < 6:
                merged.append(s)
        selected = merged

    # Añadir forzadas, quitar excluidas
    for f in forzadas:
        if f not in selected:
            selected.append(f)
    selected = [s for s in selected if s not in excluidas]

    # Aplicar reglas obligatorias (legacy)
    selected = enforce_rules(selected, modo)

    # Verificar 14 reglas del compilador
    vector_dict = None
    if tcf and tcf.estado_campo:
        vector_dict = tcf.estado_campo.vector.to_dict()

    fallos = reglas_que_fallan(selected, modo, vector_dict)
    if fallos:
        log.info("router_reglas_fallan",
                 fallos=[(r.regla, r.nombre, r.mensaje) for r in fallos])
        # Auto-corregir: añadir INTs sugeridas por las reglas
        for fallo in fallos:
            for correccion in fallo.correccion:
                if correccion not in selected and len(selected) < 6:
                    selected.append(correccion)
        # Re-verificar después de corrección
        fallos_post = reglas_que_fallan(selected, modo, vector_dict)
        if fallos_post:
            log.warning("router_reglas_no_corregibles",
                        fallos=[(r.regla, r.nombre) for r in fallos_post])

    return RouterResult(
        inteligencias=selected,
        pares_complementarios=data.get("pares_complementarios", []),
        descartadas=data.get("descartadas", []),
        razon=data.get("razon", ""),
        cost=llm.total_cost,
        time_s=elapsed,
        reglas_aplicadas=[
            {"regla": r.regla, "nombre": r.nombre, "passed": r.passed, "mensaje": r.mensaje}
            for r in verificar_reglas(selected, modo, vector_dict)
        ],
    )
