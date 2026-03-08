"""B4: Genera 180 outputs con scoring de calidad variable (18 × 10)."""
import asyncio
import structlog

from src.utils.llm_client import llm
from src.config.settings import MODEL_INTEGRATOR
from src.pipeline.ejecutor import try_parse_json
from src.reactor.config import FIRMAS, INTELIGENCIAS_IDS
from src.reactor.cartografia_loader import cargar_inteligencias

log = structlog.get_logger()

SYSTEM = "Responde EXCLUSIVAMENTE con JSON válido en español. Sin texto antes ni después del JSON."

PROMPT_B4 = """Genera exactamente 10 outputs de análisis de la inteligencia {id} ({nombre}).

Firma: {firma}
Punto ciego: {punto_ciego}

Cada output simula lo que {id} produciría al analizar un caso. Varía la CALIDAD deliberadamente:
- 2 outputs MALOS (score_global 0.1-0.3): superficiales, genéricos, sin hallazgos reales
- 3 outputs MEDIOCRES (score_global 0.4-0.5): correctos pero sin profundidad
- 3 outputs BUENOS (score_global 0.6-0.8): hallazgos específicos, bien fundamentados
- 2 outputs EXCELENTES (score_global 0.9-1.0): insights genuinos, contradicciones detectadas

Para CADA output:
- "caso_breve": Descripción del caso analizado (1-2 frases)
- "output_texto": El análisis completo (200-400 palabras). Debe reflejar la calidad asignada
- "scores": {{
    "profundidad": 0.0-1.0,
    "originalidad": 0.0-1.0,
    "accionabilidad": 0.0-1.0,
    "precision": 0.0-1.0,
    "score_global": calculado como 0.3*profundidad + 0.3*originalidad + 0.25*accionabilidad + 0.15*precision
  }}
- "calidad": "malo", "mediocre", "bueno", o "excelente"

Los outputs malos deben ser RECONOCIBLEMENTE malos: vagos, con falacias, sin números.
Los excelentes deben ser RECONOCIBLEMENTE superiores: insights no obvios, datos concretos.

Responde con:
{{
  "inteligencia": "{id}",
  "outputs": [
    {{
      "caso_breve": "...",
      "output_texto": "...",
      "scores": {{
        "profundidad": 0.0,
        "originalidad": 0.0,
        "accionabilidad": 0.0,
        "precision": 0.0,
        "score_global": 0.0
      }},
      "calidad": "malo"
    }}
  ]
}}"""


def _validar_scoring(outputs: list[dict], intel_id: str) -> list[str]:
    """Valida distribución 2/3/3/2 y recalcula scores."""
    errores: list[str] = []

    distrib = {"malo": 0, "mediocre": 0, "bueno": 0, "excelente": 0}
    for o in outputs:
        cal = o.get("calidad", "")
        if cal in distrib:
            distrib[cal] += 1

        # Verificar score_global
        scores = o.get("scores", {})
        prof = scores.get("profundidad", 0)
        orig = scores.get("originalidad", 0)
        acc = scores.get("accionabilidad", 0)
        prec = scores.get("precision", 0)
        expected = round(0.3 * prof + 0.3 * orig + 0.25 * acc + 0.15 * prec, 2)
        actual = scores.get("score_global", 0)
        if abs(expected - actual) > 0.05:
            # Corregir in-place
            scores["score_global"] = expected

        # Verificar longitud del output
        texto = o.get("output_texto", "")
        words = len(texto.split())
        if words < 100:
            errores.append(f"{intel_id}: output muy corto ({words} palabras)")

    expected_distrib = {"malo": 2, "mediocre": 3, "bueno": 3, "excelente": 2}
    for cal, expected_count in expected_distrib.items():
        if distrib[cal] < expected_count - 1:  # Tolerancia ±1
            errores.append(f"{intel_id}: {cal} tiene {distrib[cal]}/{expected_count}")

    return errores


async def generar_scoring(sem: asyncio.Semaphore) -> list[dict]:
    """Genera outputs con scoring para las 18 inteligencias."""
    inteligencias = cargar_inteligencias()
    todos: list[dict] = []
    errores_validacion: list[str] = []

    async def _gen_intel(intel_id: str) -> list[dict]:
        async with sem:
            intel = inteligencias[intel_id]
            log.info("b4_generando", inteligencia=intel_id)
            prompt = PROMPT_B4.format(
                id=intel_id,
                nombre=intel["nombre"],
                firma=intel["firma"],
                punto_ciego=intel["punto_ciego"],
            )
            response = await llm.complete(
                model=MODEL_INTEGRATOR,  # Sonnet para calibrar calidad
                system=SYSTEM,
                user_message=prompt,
                max_tokens=8192,
                temperature=0.7,
            )
            parsed = try_parse_json(response)
            if not parsed or "outputs" not in parsed:
                log.error("b4_parse_fail", inteligencia=intel_id)
                return []
            return [{"inteligencia": intel_id, **o} for o in parsed["outputs"]]

    results = await asyncio.gather(
        *[_gen_intel(iid) for iid in INTELIGENCIAS_IDS],
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            log.error("b4_error", inteligencia=INTELIGENCIAS_IDS[i], error=str(r))
        elif r:
            errs = _validar_scoring(r, INTELIGENCIAS_IDS[i])
            errores_validacion.extend(errs)
            todos.extend(r)

    log.info("b4_completo", total=len(todos), errores_validacion=len(errores_validacion))
    return todos
