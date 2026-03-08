"""B1: Genera 200 casos etiquetados por dominio (10 dominios × 20 casos)."""
import asyncio
import structlog

from src.utils.llm_client import llm
from src.config.settings import MODEL_EXTRACTOR
from src.pipeline.ejecutor import try_parse_json
from src.reactor.config import DOMINIOS, CUANTITATIVAS, HUMANAS, FIRMAS

log = structlog.get_logger()

SYSTEM = "Responde EXCLUSIVAMENTE con JSON válido en español. Sin texto antes ni después del JSON."

PROMPT_B1 = """Genera exactamente 20 casos de decisión complejos del dominio "{dominio}".

Contexto: Existen 18 inteligencias analíticas (INT-01 a INT-18) con estas firmas:
{firmas}

Para CADA caso genera:
- "descripcion": Situación concreta con al menos 1 dato numérico, >50 caracteres
- "top_5_inteligencias": Las 5 inteligencias MÁS relevantes (IDs)
- "redundantes": 3 inteligencias que NO aportan valor (IDs)
- "operacion_optima": "composicion" o "fusion" y qué par
- "justificacion": Por qué ese top 5 y no otro

Reglas:
- top_5 y redundantes NO pueden solaparse
- top_5 DEBE incluir al menos 1 cuantitativa (INT-01, INT-02, INT-07)
- top_5 DEBE incluir al menos 1 humana (INT-08, INT-10, INT-17, INT-18)
- top_5 DEBE incluir INT-16 (constructiva)
- Cada descripción debe ser específica al dominio, con números concretos

Responde con:
{{
  "dominio": "{dominio}",
  "casos": [
    {{
      "descripcion": "...",
      "top_5_inteligencias": ["INT-XX", ...],
      "redundantes": ["INT-XX", ...],
      "operacion_optima": "composicion INT-XX→INT-YY",
      "justificacion": "..."
    }}
  ]
}}"""


def _format_firmas() -> str:
    return "\n".join(f"- {k}: {v}" for k, v in FIRMAS.items())


def _validar_caso(caso: dict) -> list[str]:
    """Valida un caso individual. Devuelve lista de errores."""
    errores: list[str] = []
    top5 = caso.get("top_5_inteligencias", [])
    redundantes = caso.get("redundantes", [])
    desc = caso.get("descripcion", "")

    if len(top5) != 5:
        errores.append(f"top_5 tiene {len(top5)} items, esperado 5")
    if len(redundantes) != 3:
        errores.append(f"redundantes tiene {len(redundantes)} items, esperado 3")
    if set(top5) & set(redundantes):
        errores.append("overlap entre top_5 y redundantes")
    if not set(top5) & CUANTITATIVAS:
        errores.append("sin cuantitativa en top_5")
    if not set(top5) & HUMANAS:
        errores.append("sin humana en top_5")
    if "INT-16" not in top5:
        errores.append("INT-16 ausente de top_5")
    if len(desc) < 50:
        errores.append(f"descripcion muy corta ({len(desc)} chars)")
    if not any(c.isdigit() for c in desc):
        errores.append("descripcion sin números")

    return errores


async def generar_casos(sem: asyncio.Semaphore) -> list[dict]:
    """Genera casos para los 10 dominios."""
    firmas_txt = _format_firmas()
    todos: list[dict] = []
    errores_validacion: list[str] = []

    async def _gen_dominio(dominio: str) -> list[dict]:
        async with sem:
            log.info("b1_generando", dominio=dominio)
            prompt = PROMPT_B1.format(dominio=dominio, firmas=firmas_txt)
            response = await llm.complete(
                model=MODEL_EXTRACTOR,
                system=SYSTEM,
                user_message=prompt,
                max_tokens=8192,
                temperature=0.7,
            )
            parsed = try_parse_json(response)
            if not parsed or "casos" not in parsed:
                log.error("b1_parse_fail", dominio=dominio)
                return []
            return [{"dominio": dominio, **c} for c in parsed["casos"]]

    results = await asyncio.gather(
        *[_gen_dominio(d) for d in DOMINIOS],
        return_exceptions=True,
    )

    for r in results:
        if isinstance(r, Exception):
            log.error("b1_error", error=str(r))
        elif r:
            for caso in r:
                errs = _validar_caso(caso)
                if errs:
                    errores_validacion.extend(errs)
                todos.append(caso)

    log.info("b1_completo", total=len(todos), errores_validacion=len(errores_validacion))
    return todos
