"""B2: Genera 540 peticiones mapeadas a inteligencias (18 × 30)."""
import asyncio
import structlog

from src.utils.llm_client import llm
from src.config.settings import MODEL_EXTRACTOR
from src.pipeline.ejecutor import try_parse_json
from src.reactor.config import FIRMAS, INTELIGENCIAS_IDS
from src.reactor.cartografia_loader import cargar_inteligencias

log = structlog.get_logger()

SYSTEM = "Responde EXCLUSIVAMENTE con JSON válido en español. Sin texto antes ni después del JSON."

PROMPT_B2 = """Genera exactamente 30 peticiones en lenguaje natural que un usuario real haría, donde la inteligencia {id} ({nombre}) es relevante.

Firma de {id}: {firma}
Punto ciego: {punto_ciego}

Distribuye así:
- 10 peticiones OBVIAS (dificultad "obvia", relevancia 0.8-1.0): claramente pertenecen a {id}
- 10 peticiones MODERADAS (dificultad "moderada", relevancia 0.5-0.7): requieren pensar para asociar
- 10 peticiones NO OBVIAS (dificultad "no_obvia", relevancia 0.3-0.5): solo un experto las asociaría

Para CADA petición:
- "texto": La petición tal como la escribiría un usuario (>20 chars, lenguaje natural)
- "relevancia": 0.0-1.0 coherente con la dificultad
- "dominio": A qué dominio pertenece
- "inteligencias_secundarias": 2-3 inteligencias que también serían útiles
- "dificultad": "obvia", "moderada", o "no_obvia"

Responde con:
{{
  "inteligencia": "{id}",
  "peticiones": [
    {{
      "texto": "...",
      "relevancia": 0.0,
      "dominio": "...",
      "inteligencias_secundarias": ["INT-XX", "INT-YY"],
      "dificultad": "obvia"
    }}
  ]
}}"""


def _validar_peticiones(peticiones: list[dict], intel_id: str) -> list[str]:
    """Valida distribución y coherencia."""
    errores: list[str] = []

    por_dificultad = {"obvia": 0, "moderada": 0, "no_obvia": 0}
    for p in peticiones:
        d = p.get("dificultad", "")
        if d in por_dificultad:
            por_dificultad[d] += 1
        texto = p.get("texto", "")
        if len(texto) < 20:
            errores.append(f"{intel_id}: texto muy corto ({len(texto)} chars)")
        rel = p.get("relevancia", 0)
        if d == "obvia" and rel < 0.7:
            errores.append(f"{intel_id}: obvia con relevancia {rel}")
        if d == "no_obvia" and rel > 0.6:
            errores.append(f"{intel_id}: no_obvia con relevancia {rel}")

    for d, count in por_dificultad.items():
        if count < 8:  # Tolerancia de ±2
            errores.append(f"{intel_id}: {d} tiene {count}/10")

    return errores


async def generar_peticiones(sem: asyncio.Semaphore) -> list[dict]:
    """Genera peticiones para las 18 inteligencias."""
    inteligencias = cargar_inteligencias()
    todas: list[dict] = []
    errores_validacion: list[str] = []

    async def _gen_intel(intel_id: str) -> list[dict]:
        async with sem:
            intel = inteligencias[intel_id]
            log.info("b2_generando", inteligencia=intel_id)
            prompt = PROMPT_B2.format(
                id=intel_id,
                nombre=intel["nombre"],
                firma=intel["firma"],
                punto_ciego=intel["punto_ciego"],
            )
            response = await llm.complete(
                model=MODEL_EXTRACTOR,
                system=SYSTEM,
                user_message=prompt,
                max_tokens=8192,
                temperature=0.7,
            )
            parsed = try_parse_json(response)
            if not parsed or "peticiones" not in parsed:
                log.error("b2_parse_fail", inteligencia=intel_id)
                return []
            return [{"inteligencia_primaria": intel_id, **p} for p in parsed["peticiones"]]

    results = await asyncio.gather(
        *[_gen_intel(iid) for iid in INTELIGENCIAS_IDS],
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            log.error("b2_error", inteligencia=INTELIGENCIAS_IDS[i], error=str(r))
        elif r:
            errs = _validar_peticiones(r, INTELIGENCIAS_IDS[i])
            errores_validacion.extend(errs)
            todas.extend(r)

    log.info("b2_completo", total=len(todas), errores_validacion=len(errores_validacion))
    return todas
