"""Capa 3: Genera prompts desde Meta-Red. Código puro, $0."""
from __future__ import annotations

from dataclasses import dataclass, field

from src.config.settings import MODEL_EXTRACTOR, MODEL_INTEGRATOR
from src.pipeline.compositor import Algoritmo, Operacion
from src.meta_red import load_pensamientos, load_razonamientos


def _generar_bloque_pr(ps: list[str], rs: list[str]) -> str:
    """Genera bloque de texto con Ps y Rs prescritos para inyectar en prompts.

    Args:
        ps: IDs de pensamientos prescritos (ej: ["P05", "P03", "P08"])
        rs: IDs de razonamientos prescritos (ej: ["R03", "R09", "R08"])

    Returns:
        Bloque de texto formateado, o string vacío si no hay P/R.
    """
    if not ps and not rs:
        return ""

    ps_data = load_pensamientos()
    rs_data = load_razonamientos()

    lines = ["\n## DIRECTIVAS COGNITIVAS (cómo abordar este caso)\n"]

    if ps:
        lines.append("TIPOS DE PENSAMIENTO A APLICAR:")
        for pid in ps:
            p = ps_data.get(pid, {})
            nombre = p.get("nombre", pid)
            pregunta = p.get("pregunta_activadora", "")
            lines.append(f"  - {pid} {nombre}: {pregunta}")
        lines.append("")

    if rs:
        lines.append("TIPOS DE RAZONAMIENTO A USAR:")
        for rid in rs:
            r = rs_data.get(rid, {})
            nombre = r.get("nombre", rid)
            desc = r.get("descripcion", "")[:80]
            lines.append(f"  - {rid} {nombre}: {desc}")
        lines.append("")

    lines.append("INSTRUCCIÓN: Aplica estos tipos de pensamiento y razonamiento "
                 "ACTIVAMENTE durante tu análisis. No los menciones por nombre — "
                 "úsalos como lentes operativas.\n")

    return "\n".join(lines)


TEMPLATE_INDIVIDUAL = """Eres la inteligencia {nombre} ({id}).

Tu firma: {firma}
Tu punto ciego: {punto_ciego}

Aplica tu red de preguntas al siguiente caso. Sigue EXACTAMENTE esta secuencia:

1. EXTRAER — {extraer_nombre}:
{extraer_preguntas}

2. CRUZAR — {cruzar_nombre}:
{cruzar_preguntas}

3. LENTES:
{lentes_preguntas}

4. INTEGRAR: {integrar}

5. ABSTRAER: {abstraer}

6. FRONTERA: {frontera}

CASO:
{input}

{contexto_extra}

Responde de forma estructurada. Para cada paso, contesta CADA pregunta. No saltes ninguna.
IMPORTANTE: Al final de tu análisis, incluye un bloque JSON entre triple backticks. Este JSON es OBLIGATORIO:
```json
{{
  "firma_caso": "la firma específica de este caso en 1-2 frases",
  "hallazgos": ["hallazgo 1", "hallazgo 2", ...],
  "puntos_ciegos": ["lo que esta inteligencia NO puede ver"],
  "accion_prioritaria": "la acción más importante que sugiere este análisis",
  "confianza": 0.0-1.0
}}
```"""

TEMPLATE_COMPOSICION = """Eres la inteligencia {nombre_b} ({id_b}).

Tu firma: {firma_b}
Tu punto ciego: {punto_ciego_b}

Se te proporciona el ANÁLISIS PREVIO realizado por {nombre_a} ({id_a}).
Tu trabajo es aplicar tus preguntas SOBRE ESE ANÁLISIS, no sobre el caso original directamente.

ANÁLISIS PREVIO ({id_a}):
{output_a}

CASO ORIGINAL (para referencia):
{input}

Aplica tu red de preguntas al análisis previo:
{preguntas_b}

Presta especial atención a:
- Lo que {id_a} NO pudo ver (sus puntos ciegos: {punto_ciego_a})
- Lo que EMERGE al cruzar su análisis con tu lente
- Contradicciones entre lo que {id_a} encontró y lo que tú ves

INSTRUCCIÓN CRÍTICA SOBRE EMERGENCIA:
Un hallazgo emergente es algo que SOLO aparece al cruzar {id_a} con {id_b} — algo que ninguna de las dos inteligencias produciría por separado. No es un resumen ni una combinación. Es un insight de ORDEN SUPERIOR que requiere ambas lentes simultáneamente. Si no encuentras ninguno genuino, escribe "ninguno" — pero busca bien antes de rendirte.

Responde EXCLUSIVAMENTE con JSON válido (sin texto antes ni después):
{{
  "firma_caso": "firma específica de este caso en 1-2 frases",
  "hallazgos": ["hallazgo 1", "hallazgo 2"],
  "puntos_ciegos": ["lo que esta composición NO puede ver"],
  "contradicciones": ["contradicción entre {id_a} y {id_b}"],
  "hallazgo_emergente": "lo que SOLO aparece al cruzar {id_a} con {id_b} — el insight de orden superior",
  "emergencias": ["hallazgo emergente 1 detallado", "hallazgo emergente 2 si existe"],
  "accion_prioritaria": "acción más importante",
  "confianza": 0.0
}}"""

TEMPLATE_FUSION = """Tienes dos análisis del MISMO caso, realizados por dos inteligencias diferentes.

ANÁLISIS 1 ({id_a} — {nombre_a}):
{output_a}

ANÁLISIS 2 ({id_b} — {nombre_b}):
{output_b}

Tu trabajo es FUSIONAR ambos análisis:
1. ¿Qué dicen los dos que coincide?
2. ¿Dónde se contradicen?
3. ¿Qué emerge SOLO al juntar ambos que ninguno veía solo?
4. ¿Cuál es la síntesis que respeta lo mejor de ambos?

INSTRUCCIÓN CRÍTICA SOBRE EMERGENCIA:
Un hallazgo emergente NO es un resumen de ambos análisis. NO es algo que ya aparece en uno de ellos. Es un insight de ORDEN SUPERIOR que SOLO existe porque las dos lentes operan simultáneamente sobre el mismo material. Piensa: ¿qué ve el cruce que ninguna lente individual puede ver? Si {nombre_a} ve X e {nombre_b} ve Y, ¿qué Z aparece que no es ni X ni Y sino algo nuevo? Busca al menos 1 hallazgo emergente genuino.

CASO ORIGINAL:
{input}

Responde EXCLUSIVAMENTE con JSON válido (sin texto antes ni después):
{{
  "convergencias": ["punto donde ambos coinciden"],
  "divergencias": ["punto donde se contradicen"],
  "hallazgo_emergente": "el insight principal de orden superior que SOLO aparece al fusionar",
  "emergencias": ["emergencia 1 detallada", "emergencia 2 si existe"],
  "emergente": "síntesis de lo que emerge (1-2 frases)",
  "sintesis": "la síntesis integradora",
  "firma_combinada": "firma del par fusionado en 1-2 frases"
}}"""

TEMPLATE_LOOP = """Eres la inteligencia {nombre} ({id}).

Se te proporciona tu PROPIO ANÁLISIS PREVIO de este caso.
Tu trabajo es re-examinar tu análisis con ojos frescos.

TU ANÁLISIS PREVIO:
{output_previo}

Preguntas de meta-diagnóstico:
- ¿Tu análisis tiene sesgos propios de tu forma de pensar?
- ¿Hay algo que diste por hecho sin verificar?
- ¿Tu punto ciego ({punto_ciego}) afectó lo que encontraste?
- ¿Hay hallazgos genuinamente nuevos que emergen al re-examinar?

Responde SOLO con lo NUEVO. No repitas lo anterior.
Responde EXCLUSIVAMENTE con JSON válido (sin texto antes ni después):
{{
  "hallazgos_nuevos": ["genuinamente nuevo, no repetido"],
  "sesgos_detectados": ["sesgo de tu propio análisis"],
  "correccion": "si algo del análisis previo era erróneo, null si todo correcto"
}}"""


@dataclass
class PromptPlan:
    operacion: Operacion
    prompt_system: str
    prompt_user: str | None
    modelo: str
    depende_de: list[str] = field(default_factory=list)
    template: str | None = None
    intel_a: dict | None = None
    intel_b: dict | None = None
    intel_data: dict | None = None


def _format_preguntas(preguntas: list[str]) -> str:
    """Formatea lista de preguntas como texto indentado."""
    return "\n".join(f"  - {p}" for p in preguntas)


def _format_lentes(lentes: list[dict]) -> str:
    """Formatea lentes con sus preguntas."""
    lines = []
    for lente in lentes:
        lines.append(f"  {lente['id']} {lente['nombre']}:")
        for p in lente['preguntas']:
            lines.append(f"    - {p}")
    return "\n".join(lines)


def _format_all_preguntas(meta_red: dict) -> str:
    """Formatea todas las preguntas de una inteligencia como bloque de texto."""
    lines = []
    lines.append(f"EXTRAER — {meta_red['extraer']['nombre']}:")
    for p in meta_red['extraer']['preguntas']:
        lines.append(f"  - {p}")
    lines.append(f"\nCRUZAR — {meta_red['cruzar']['nombre']}:")
    for p in meta_red['cruzar']['preguntas']:
        lines.append(f"  - {p}")
    lines.append("\nLENTES:")
    lines.append(_format_lentes(meta_red['lentes']))
    lines.append(f"\nINTEGRAR: {meta_red['integrar']}")
    lines.append(f"ABSTRAER: {meta_red['abstraer']}")
    lines.append(f"FRONTERA: {meta_red['frontera']}")
    return "\n".join(lines)


def format_individual(intel: dict, input_text: str, contexto: str | None, bloque_pr: str = "") -> str:
    """Genera prompt individual para una inteligencia."""
    meta = intel['meta_red']
    return TEMPLATE_INDIVIDUAL.format(
        nombre=intel['nombre'],
        id=intel['id'],
        firma=intel['firma'],
        punto_ciego=intel['punto_ciego'],
        extraer_nombre=meta['extraer']['nombre'],
        extraer_preguntas=_format_preguntas(meta['extraer']['preguntas']),
        cruzar_nombre=meta['cruzar']['nombre'],
        cruzar_preguntas=_format_preguntas(meta['cruzar']['preguntas']),
        lentes_preguntas=_format_lentes(meta['lentes']),
        integrar=meta['integrar'],
        abstraer=meta['abstraer'],
        frontera=meta['frontera'],
        input=input_text,
        contexto_extra=(
            (bloque_pr if bloque_pr else "") +
            (f"\nCONTEXTO ADICIONAL:\n{contexto}" if contexto else "")
        ),
    )


def format_composicion(intel_a: dict, intel_b: dict, output_a: str, input_text: str) -> str:
    """Genera prompt de composición (B sobre output de A)."""
    meta_b = intel_b['meta_red']
    return TEMPLATE_COMPOSICION.format(
        nombre_b=intel_b['nombre'],
        id_b=intel_b['id'],
        firma_b=intel_b['firma'],
        punto_ciego_b=intel_b['punto_ciego'],
        nombre_a=intel_a['nombre'],
        id_a=intel_a['id'],
        punto_ciego_a=intel_a['punto_ciego'],
        output_a=output_a,
        input=input_text,
        preguntas_b=_format_all_preguntas(meta_b),
    )


def format_fusion(intel_a: dict, intel_b: dict, output_a: str, output_b: str, input_text: str) -> str:
    """Genera prompt de fusión (integrar dos análisis)."""
    return TEMPLATE_FUSION.format(
        id_a=intel_a['id'],
        nombre_a=intel_a['nombre'],
        output_a=output_a,
        id_b=intel_b['id'],
        nombre_b=intel_b['nombre'],
        output_b=output_b,
        input=input_text,
    )


def format_loop(intel: dict, output_previo: str) -> str:
    """Genera prompt de loop test (segunda pasada)."""
    return TEMPLATE_LOOP.format(
        nombre=intel['nombre'],
        id=intel['id'],
        punto_ciego=intel['punto_ciego'],
        output_previo=output_previo,
    )


def generar_prompts(
    algoritmo: Algoritmo,
    input_text: str,
    contexto: str | None,
    inteligencias_data: dict,
    ps: list[str] | None = None,
    rs: list[str] | None = None,
) -> list[PromptPlan]:
    """Genera los prompts exactos para cada operación del algoritmo."""
    bloque_pr = _generar_bloque_pr(ps or [], rs or [])
    prompts: list[PromptPlan] = []
    intels_con_prompt: set[str] = set()  # Track de qué intels ya tienen prompt individual

    def _add_individual(intel_id: str, orden: int) -> None:
        """Añade prompt individual para una inteligencia si no existe ya."""
        if intel_id in intels_con_prompt:
            return
        intels_con_prompt.add(intel_id)
        intel = inteligencias_data[intel_id]
        prompt = format_individual(intel, input_text, contexto, bloque_pr=bloque_pr)
        prompts.append(PromptPlan(
            operacion=Operacion(
                tipo='individual',
                inteligencias=[intel_id],
                orden=orden,
                pasadas=1,
            ),
            prompt_system="",
            prompt_user=prompt,
            modelo=MODEL_EXTRACTOR,
            depende_de=[],
        ))

    for operacion in sorted(algoritmo.operaciones, key=lambda o: o.orden):
        if operacion.tipo == 'individual':
            intel_id = operacion.inteligencias[0]
            intels_con_prompt.add(intel_id)
            intel = inteligencias_data[intel_id]
            prompt = format_individual(intel, input_text, contexto, bloque_pr=bloque_pr)
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=prompt,
                modelo=MODEL_EXTRACTOR,  # Haiku para extracción
                depende_de=[],
            ))
        elif operacion.tipo == 'composicion':
            # Prerequisito: A debe ejecutarse individualmente primero
            id_a, id_b = operacion.inteligencias
            _add_individual(id_a, operacion.orden)
            # Composición: B se ejecuta sobre output de A
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=None,  # Se genera dinámicamente con output_a
                modelo=MODEL_EXTRACTOR,
                depende_de=[id_a],
                template='composicion',
                intel_a=inteligencias_data[id_a],
                intel_b=inteligencias_data[id_b],
            ))
        elif operacion.tipo == 'fusion':
            # Prerequisito: ambos deben ejecutarse individualmente primero
            id_a, id_b = operacion.inteligencias
            _add_individual(id_a, operacion.orden)
            _add_individual(id_b, operacion.orden)
            # Fusión: se ejecuta con outputs de A y B
            prompts.append(PromptPlan(
                operacion=operacion,
                prompt_system="",
                prompt_user=None,  # Se genera con ambos outputs
                modelo=MODEL_INTEGRATOR,  # Sonnet para fusión
                depende_de=[id_a, id_b],
                template='fusion',
                intel_a=inteligencias_data[id_a],
                intel_b=inteligencias_data[id_b],
            ))

    # Añadir loop tests (pasada 2) si procede
    for intel_id, pasadas in algoritmo.loops.items():
        if pasadas >= 2:
            intel = inteligencias_data[intel_id]
            prompts.append(PromptPlan(
                operacion=Operacion(
                    tipo='loop',
                    inteligencias=[intel_id],
                    orden=999,
                    pasadas=1,
                ),
                prompt_system="",
                prompt_user=None,  # Se genera con output de pasada 1
                modelo=MODEL_EXTRACTOR,
                depende_de=[intel_id],
                template='loop',
                intel_data=intel,
            ))

    return prompts
