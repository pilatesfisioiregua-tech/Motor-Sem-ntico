"""Evaluador ACD — métricas de efectividad de la prescripción.

Mide si la ejecución del pipeline respetó la prescripción.
Código puro, $0. No usa LLM — analiza outputs existentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from kernel.tcf.prescriptor import Prescripcion
from kernel.meta_red import load_pensamientos, load_razonamientos

if TYPE_CHECKING:
    from src.pipeline.ejecutor import ExecutionPlan


@dataclass
class MetricasACD:
    # Cobertura prescriptiva
    ints_prescritas: list[str]
    ints_ejecutadas: list[str]
    cobertura_ints: float          # 0.0 - 1.0

    # Alineación P/R
    ps_prescritos: list[str]
    ps_detectados: list[str]       # Ps cuya señal aparece en outputs
    rs_prescritos: list[str]
    rs_detectados: list[str]
    alineacion_pr: float           # 0.0 - 1.0

    # Ataque a lente objetivo
    lente_objetivo: str
    funciones_atacadas: list[str]  # Funciones mencionadas/atacadas en outputs
    lente_cubierta: bool           # ¿Se tocó la lente objetivo?

    # Prohibiciones
    prohibiciones_violadas: list[str]  # PRH-XX que la ejecución violó

    # Score compuesto
    score_acd: float               # 0.0 - 10.0

    # Detalle
    detalle: dict = field(default_factory=dict)


def evaluar_acd(
    plan: ExecutionPlan,
    prescripcion: Prescripcion,
) -> MetricasACD:
    """Evalúa qué tan bien la ejecución respetó la prescripción.

    Args:
        plan: ExecutionPlan del ejecutor (outputs reales).
        prescripcion: Prescripcion del prescriptor (lo que se debía hacer).

    Returns:
        MetricasACD con scores y detalle.
    """
    # --- 1. Cobertura prescriptiva ---
    ints_prescritas = set(prescripcion.ints)
    ints_ejecutadas = set()
    for key in plan.results:
        for int_id in ints_prescritas:
            if int_id in key:
                ints_ejecutadas.add(int_id)
    cobertura = len(ints_ejecutadas) / max(len(ints_prescritas), 1)

    # --- 2. Alineación P/R ---
    ps_detectados = _detectar_ps_en_outputs(plan, prescripcion.ps)
    rs_detectados = _detectar_rs_en_outputs(plan, prescripcion.rs)

    total_pr = len(prescripcion.ps) + len(prescripcion.rs)
    detectados_pr = len(ps_detectados) + len(rs_detectados)
    alineacion = detectados_pr / max(total_pr, 1)

    # --- 3. Ataque a lente objetivo ---
    funciones_atacadas = _detectar_funciones_en_outputs(plan)
    lente_cubierta = _lente_tocada(
        prescripcion.lente_objetivo,
        funciones_atacadas,
        plan,
    )

    # --- 4. Prohibiciones ---
    # Las prohibiciones ya están en prescripcion.prohibiciones_violadas
    # Aquí solo las reportamos
    prohibiciones = [p.codigo for p in prescripcion.prohibiciones_violadas]

    # --- 5. Score compuesto ---
    score = (
        cobertura * 4.0 +           # 40% cobertura INTs
        alineacion * 3.0 +          # 30% alineación P/R
        (1.0 if lente_cubierta else 0.0) * 2.0 +  # 20% lente
        (1.0 if not prohibiciones else 0.0) * 1.0  # 10% sin prohibiciones
    )

    return MetricasACD(
        ints_prescritas=list(ints_prescritas),
        ints_ejecutadas=list(ints_ejecutadas),
        cobertura_ints=round(cobertura, 3),
        ps_prescritos=prescripcion.ps,
        ps_detectados=ps_detectados,
        rs_prescritos=prescripcion.rs,
        rs_detectados=rs_detectados,
        alineacion_pr=round(alineacion, 3),
        lente_objetivo=prescripcion.lente_objetivo,
        funciones_atacadas=funciones_atacadas,
        lente_cubierta=lente_cubierta,
        prohibiciones_violadas=prohibiciones,
        score_acd=round(score, 1),
        detalle={
            "cobertura_raw": round(cobertura, 3),
            "alineacion_raw": round(alineacion, 3),
            "lente_raw": 1.0 if lente_cubierta else 0.0,
            "prohibiciones_raw": 0.0 if prohibiciones else 1.0,
        },
    )


def _detectar_ps_en_outputs(
    plan: ExecutionPlan,
    ps_prescritos: list[str],
) -> list[str]:
    """Detecta señales de Ps prescritos en los outputs del ejecutor.

    Usa la pregunta_activadora de cada P como señal de detección.
    No busca mención literal del ID — busca evidencia funcional.
    """
    ps_data = load_pensamientos()
    detectados = []

    # Concatenar todos los outputs en un solo texto (lowercase)
    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )

    for pid in ps_prescritos:
        p = ps_data.get(pid, {})
        # Señales: palabras clave de la descripción y nombre
        nombre = p.get("nombre", "").lower()
        keywords = _extraer_keywords(p.get("descripcion", ""))

        # Detectar si al menos 2 keywords aparecen en outputs
        hits = sum(1 for kw in keywords if kw in all_text)
        if hits >= 2 or nombre in all_text:
            detectados.append(pid)

    return detectados


def _detectar_rs_en_outputs(
    plan: ExecutionPlan,
    rs_prescritos: list[str],
) -> list[str]:
    """Detecta señales de Rs prescritos en los outputs."""
    rs_data = load_razonamientos()
    detectados = []

    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )

    for rid in rs_prescritos:
        r = rs_data.get(rid, {})
        nombre = r.get("nombre", "").lower()
        keywords = _extraer_keywords(r.get("descripcion", ""))

        hits = sum(1 for kw in keywords if kw in all_text)
        if hits >= 2 or nombre in all_text:
            detectados.append(rid)

    return detectados


def _extraer_keywords(texto: str) -> list[str]:
    """Extrae keywords significativas de un texto (>4 chars, no stopwords)."""
    stopwords = {
        "para", "como", "pero", "este", "esta", "todo", "cada",
        "donde", "cuando", "entre", "desde", "hasta", "sobre",
        "tiene", "puede", "debe", "hace", "algo", "otro", "otra",
        "forma", "modo", "tipo", "parte",
    }
    words = texto.lower().split()
    return [w.strip(".,;:()") for w in words
            if len(w) > 4 and w.strip(".,;:()") not in stopwords][:8]


def _detectar_funciones_en_outputs(plan: ExecutionPlan) -> list[str]:
    """Detecta qué funciones F1-F7 se mencionan/atacan en outputs."""
    funciones_map = {
        "f1": "F1", "conservar": "F1", "conservación": "F1",
        "f2": "F2", "captar": "F2", "captación": "F2",
        "f3": "F3", "depurar": "F3", "depuración": "F3",
        "f4": "F4", "distribuir": "F4", "distribución": "F4",
        "f5": "F5", "frontera": "F5", "identidad": "F5",
        "f6": "F6", "adaptar": "F6", "adaptación": "F6",
        "f7": "F7", "replicar": "F7", "replicación": "F7",
    }
    detectadas = set()

    for r in plan.results.values():
        if not r.output_raw:
            continue
        text = r.output_raw.lower()
        for keyword, fi in funciones_map.items():
            if keyword in text:
                detectadas.add(fi)

    return sorted(detectadas)


def _lente_tocada(
    lente_objetivo: str,
    funciones_atacadas: list[str],
    plan: ExecutionPlan,
) -> bool:
    """Verifica si la lente objetivo fue tocada por la intervención.

    Heurístico: la lente se considera tocada si:
    - Se mencionan funciones asociadas a esa lente, O
    - Aparecen keywords de la lente en outputs
    """
    # Funciones fuertemente asociadas a cada lente
    lente_funciones = {
        "salud": {"F1", "F2", "F4"},
        "sentido": {"F3", "F5", "F6"},
        "continuidad": {"F7", "F6", "F5"},
    }

    funcs_lente = lente_funciones.get(lente_objetivo, set())
    if funcs_lente.intersection(funciones_atacadas):
        return True

    # Fallback: keywords de lente en texto
    keywords_lente = {
        "salud": ["operativ", "ejecución", "recurso", "eficiencia", "funcionamiento"],
        "sentido": ["propósito", "significado", "cuestionar", "por qué", "sentido"],
        "continuidad": ["escalar", "replicar", "transmitir", "legado", "transferir"],
    }

    all_text = " ".join(
        r.output_raw.lower() for r in plan.results.values() if r.output_raw
    )
    kws = keywords_lente.get(lente_objetivo, [])
    hits = sum(1 for kw in kws if kw in all_text)
    return hits >= 2


# ---------------------------------------------------------------------------
# DECISIÓN TERNARIA
# ---------------------------------------------------------------------------

@dataclass
class DecisionTernaria:
    veredicto: str            # "cierre" | "inerte" | "toxico"
    confianza: float          # 0.0 - 1.0
    razon: str                # Explicación en 1 frase
    recomendacion: str        # Qué hacer a continuación
    metricas_clave: dict      # Métricas que determinaron la decisión


def decidir(metricas: MetricasACD) -> DecisionTernaria:
    """Decisión ternaria: ¿la intervención cerró, fue inerte, o fue tóxica?

    Reglas (en orden de prioridad):

    TÓXICO si:
      - Hay prohibiciones críticas violadas (PRH-01 o PRH-03), O
      - Cobertura INTs < 0.20 Y hay prohibiciones de cualquier severidad

    INERTE si:
      - Cobertura INTs < 0.40 (menos de la mitad de INTs prescritas), O
      - Alineación P/R = 0 (ningún P/R detectado en outputs), O
      - Score ACD < 4.0

    CIERRE si:
      - Cobertura INTs >= 0.60 Y
      - Lente objetivo cubierta Y
      - Score ACD >= 6.0

    CIERRE PARCIAL si:
      - No es tóxico ni inerte pero no cumple todos los criterios de cierre
    """
    prohibiciones = metricas.prohibiciones_violadas
    cobertura = metricas.cobertura_ints
    alineacion = metricas.alineacion_pr
    lente_ok = metricas.lente_cubierta
    score = metricas.score_acd

    metricas_clave = {
        "cobertura_ints": cobertura,
        "alineacion_pr": alineacion,
        "lente_cubierta": lente_ok,
        "score_acd": score,
        "prohibiciones": prohibiciones,
    }

    # --- TÓXICO ---
    prohibiciones_criticas = [p for p in prohibiciones if p in ("PRH-01", "PRH-03")]
    if prohibiciones_criticas:
        return DecisionTernaria(
            veredicto="toxico",
            confianza=0.90,
            razon=f"Prohibiciones críticas activas: {prohibiciones_criticas}. "
                  "La intervención amplifica el desequilibrio.",
            recomendacion="FRENAR. Revisar prescripción. Eliminar funciones que violan prohibiciones "
                          "antes de re-ejecutar.",
            metricas_clave=metricas_clave,
        )

    if cobertura < 0.20 and prohibiciones:
        return DecisionTernaria(
            veredicto="toxico",
            confianza=0.75,
            razon=f"Cobertura mínima ({cobertura:.0%}) con prohibiciones activas ({prohibiciones}). "
                  "Ejecución desalineada y dañina.",
            recomendacion="FRENAR. Re-diagnosticar. Las INTs ejecutadas no corresponden a la prescripción.",
            metricas_clave=metricas_clave,
        )

    # --- INERTE ---
    if cobertura < 0.40:
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.85,
            razon=f"Solo {cobertura:.0%} de INTs prescritas ejecutadas. "
                  "La intervención no atacó el problema.",
            recomendacion="Ampliar presupuesto o forzar INTs prescritas. "
                          "El Router descartó INTs clave.",
            metricas_clave=metricas_clave,
        )

    if alineacion == 0.0 and (metricas.ps_prescritos or metricas.rs_prescritos):
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.70,
            razon="Ningún P/R prescrito detectado en outputs. "
                  "Las INTs se ejecutaron pero sin la dirección cognitiva correcta.",
            recomendacion="Reforzar bloque P/R en prompts. Los templates no inyectaron "
                          "las directivas correctamente.",
            metricas_clave=metricas_clave,
        )

    if score < 4.0:
        return DecisionTernaria(
            veredicto="inerte",
            confianza=0.65,
            razon=f"Score ACD bajo ({score}/10). Intervención genérica sin foco.",
            recomendacion="Aumentar profundidad (tier 3+). Usar modo específico "
                          f"({metricas.lente_objetivo}) en vez de genérico.",
            metricas_clave=metricas_clave,
        )

    # --- CIERRE ---
    if cobertura >= 0.60 and lente_ok and score >= 6.0:
        return DecisionTernaria(
            veredicto="cierre",
            confianza=min(0.60 + cobertura * 0.20 + (0.10 if alineacion > 0.5 else 0), 0.95),
            razon=f"Cobertura {cobertura:.0%}, lente {metricas.lente_objetivo} cubierta, "
                  f"score {score}/10. Intervención alineada con prescripción.",
            recomendacion="Registrar como éxito. Medir delta real del campo en próxima "
                          "interacción (Reactor v4).",
            metricas_clave=metricas_clave,
        )

    # --- CIERRE PARCIAL ---
    return DecisionTernaria(
        veredicto="cierre",
        confianza=0.45,
        razon=f"Cierre parcial: cobertura={cobertura:.0%}, lente={'sí' if lente_ok else 'no'}, "
              f"score={score}/10. Mejorable pero no inerte.",
        recomendacion="Aceptar como cierre parcial. En próxima iteración, "
                      f"focalizar en {'lente ' + metricas.lente_objetivo if not lente_ok else 'profundidad'}.",
        metricas_clave=metricas_clave,
    )
