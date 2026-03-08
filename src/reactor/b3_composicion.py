"""B3: Genera 300 datapoints de orden de composición (10 pares × 30)."""
import asyncio
import structlog

from src.utils.llm_client import llm
from src.config.settings import MODEL_EXTRACTOR
from src.pipeline.ejecutor import try_parse_json
from src.reactor.config import TOP_PARES, FIRMAS

log = structlog.get_logger()

SYSTEM = "Responde EXCLUSIVAMENTE con JSON válido en español. Sin texto antes ni después del JSON."

PROMPT_B3 = """Genera exactamente 30 situaciones donde se usan las inteligencias {id_a} y {id_b} juntas.

{id_a} ({nombre_a}): {firma_a}
{id_b} ({nombre_b}): {firma_b}

Distribuye así:
- 15 situaciones donde EL ORDEN IMPORTA: analizar con {id_a} primero y {id_b} después da resultado diferente que al revés
- 15 situaciones donde EL ORDEN ES INDISTINTO: el resultado es similar sin importar quién va primero

Para CADA situación:
- "descripcion": Situación concreta >30 chars
- "orden_optimo": "{id_a}→{id_b}" o "{id_b}→{id_a}" o "indistinto"
- "por_que_importa": Explicación de por qué el orden importa (o no)
- "features_predictoras": 3-5 características del input que predicen si el orden importa

Responde con:
{{
  "par": "{id_a}×{id_b}",
  "datapoints": [
    {{
      "descripcion": "...",
      "orden_optimo": "...",
      "por_que_importa": "...",
      "features_predictoras": ["feature1", "feature2", "feature3"]
    }}
  ]
}}"""


def _validar_composicion(datapoints: list[dict], par: str) -> list[str]:
    """Valida split 15/15 y features no vacías."""
    errores: list[str] = []

    con_orden = sum(1 for d in datapoints if d.get("orden_optimo", "") != "indistinto")
    sin_orden = sum(1 for d in datapoints if d.get("orden_optimo", "") == "indistinto")

    if con_orden < 12:  # Tolerancia ±3
        errores.append(f"{par}: solo {con_orden}/15 con orden")
    if sin_orden < 12:
        errores.append(f"{par}: solo {sin_orden}/15 indistinto")

    for d in datapoints:
        features = d.get("features_predictoras", [])
        if not features:
            errores.append(f"{par}: features vacías")

    return errores


async def generar_composiciones(sem: asyncio.Semaphore) -> list[dict]:
    """Genera datapoints de composición para los 10 pares top."""
    from src.reactor.cartografia_loader import cargar_inteligencias
    inteligencias = cargar_inteligencias()
    todos: list[dict] = []
    errores_validacion: list[str] = []

    async def _gen_par(id_a: str, id_b: str) -> list[dict]:
        async with sem:
            par_label = f"{id_a}×{id_b}"
            log.info("b3_generando", par=par_label)
            prompt = PROMPT_B3.format(
                id_a=id_a, id_b=id_b,
                nombre_a=inteligencias[id_a]["nombre"],
                nombre_b=inteligencias[id_b]["nombre"],
                firma_a=FIRMAS[id_a],
                firma_b=FIRMAS[id_b],
            )
            response = await llm.complete(
                model=MODEL_EXTRACTOR,
                system=SYSTEM,
                user_message=prompt,
                max_tokens=8192,
                temperature=0.7,
            )
            parsed = try_parse_json(response)
            if not parsed or "datapoints" not in parsed:
                log.error("b3_parse_fail", par=par_label)
                return []
            return [{"par": par_label, **dp} for dp in parsed["datapoints"]]

    results = await asyncio.gather(
        *[_gen_par(a, b) for a, b in TOP_PARES],
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        par_label = f"{TOP_PARES[i][0]}×{TOP_PARES[i][1]}"
        if isinstance(r, Exception):
            log.error("b3_error", par=par_label, error=str(r))
        elif r:
            errs = _validar_composicion(r, par_label)
            errores_validacion.extend(errs)
            todos.extend(r)

    log.info("b3_completo", total=len(todos), errores_validacion=len(errores_validacion))
    return todos
