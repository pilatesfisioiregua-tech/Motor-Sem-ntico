"""Evaluador funcional — deriva VectorFuncional desde texto usando LLM.

Paso P1 del pipeline ACD: caso (texto) → 21 scores F×L → VectorFuncional.
Usa DeepSeek V3.2 vía OpenRouter con json_schema forzado.
"""
from __future__ import annotations

import structlog

from src.tcf.campo import VectorFuncional
from src.tcf.constantes import FUNCIONES, LENTES
from src.utils.openrouter_client import openrouter_json, MODEL_EXTRACTOR_OR

log = structlog.get_logger()


SYSTEM_PROMPT = """Eres un evaluador funcional de sistemas (empresas, proyectos, organizaciones).

Tu tarea: dado un caso descrito en texto, evaluar 7 funciones vitales desde 3 perspectivas (lentes).

## 7 FUNCIONES

F1 Conservar: Mantener lo que funciona. Proteger recursos, conocimiento, procesos estables.
F2 Captar: Adquirir del exterior. Clientes, talento, información, recursos, oportunidades.
F3 Depurar: Eliminar lo que sobra o daña. Filtrar, limpiar, descartar lo tóxico o ineficiente.
F4 Distribuir: Repartir internamente. Asignar recursos, información, responsabilidades donde se necesitan.
F5 Frontera: Definir identidad y límites. Saber qué es el sistema y qué no, qué entra y qué no.
F6 Adaptar: Cambiar ante el entorno. Flexibilidad, innovación, respuesta a nuevas condiciones.
F7 Replicar: Transmitir y escalar. Que el sistema pueda funcionar sin sus creadores originales.

## 3 LENTES

salud: ¿Funciona? Operativa, eficiencia, supervivencia día a día.
sentido: ¿Comprende por qué? Propósito, significado, cuestionamiento profundo.
continuidad: ¿Puede persistir y transmitirse? Escalabilidad, transferencia, legado.

## INSTRUCCIONES

Para CADA función (F1-F7), evalúa el grado en que el sistema la cumple desde CADA lente.

Escala: 0.0 (ausente) a 1.0 (excelente).
- 0.0-0.20: No existe o no funciona
- 0.20-0.40: Presente pero deficiente
- 0.40-0.60: Funcional pero mejorable
- 0.60-0.80: Bueno
- 0.80-1.0: Excelente"""


# JSON Schema para response_format (fuerza estructura exacta)
SCHEMA_VECTOR = {
    "type": "object",
    "properties": {
        fi: {
            "type": "object",
            "properties": {
                lente: {"type": "number"} for lente in ("salud", "sentido", "continuidad")
            },
            "required": ["salud", "sentido", "continuidad"],
            "additionalProperties": False,
        }
        for fi in ("F1", "F2", "F3", "F4", "F5", "F6", "F7")
    },
    "required": ["F1", "F2", "F3", "F4", "F5", "F6", "F7"],
    "additionalProperties": False,
}


async def evaluar_funcional(caso_texto: str) -> tuple[dict[str, dict[str, float]], VectorFuncional]:
    """Deriva VectorFuncional desde texto usando LLM.

    Args:
        caso_texto: Descripción del caso/sistema a evaluar.

    Returns:
        Tupla (scores_raw, vector):
          - scores_raw: dict 7F × 3L con los 21 scores originales del LLM
          - vector: VectorFuncional agregado (7 scores, uno por función)

    Raises:
        ValueError: Si los scores están fuera de rango.
    """
    log.info("evaluador_funcional.start", caso_len=len(caso_texto))

    scores_raw = await openrouter_json(
        model=MODEL_EXTRACTOR_OR,
        system=SYSTEM_PROMPT,
        user_message=f"CASO A EVALUAR:\n\n{caso_texto}",
        schema_name="vector_funcional",
        schema=SCHEMA_VECTOR,
        max_tokens=512,
        temperature=0.1,
    )

    # Validar rangos
    for fi in FUNCIONES:
        if fi not in scores_raw:
            raise ValueError(f"Falta función {fi} en respuesta LLM")
        for lente in LENTES:
            if lente not in scores_raw[fi]:
                raise ValueError(f"Falta lente {lente} en {fi}")
            val = float(scores_raw[fi][lente])
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{fi}.{lente}={val} fuera de rango [0,1]")
            scores_raw[fi][lente] = val

    # Agregar: promedio de las 3 lentes por función → grado funcional
    grados = {}
    for fi in FUNCIONES:
        grados[fi] = round(
            sum(scores_raw[fi][l] for l in LENTES) / len(LENTES),
            3,
        )

    vector = VectorFuncional.from_dict(grados)

    log.info(
        "evaluador_funcional.ok",
        vector=vector.to_dict(),
        eslabon_debil=vector.eslabon_debil(),
    )

    return scores_raw, vector
