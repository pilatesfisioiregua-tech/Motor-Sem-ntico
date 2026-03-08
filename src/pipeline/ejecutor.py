"""Capa 4: Ejecuta prompts via Anthropic API."""
import asyncio
import json
import re
import time
import structlog
from dataclasses import dataclass, field
from typing import Any

from src.utils.llm_client import llm
from src.pipeline.generador import (
    PromptPlan, format_composicion, format_fusion, format_loop,
)

log = structlog.get_logger()


@dataclass
class ExecutionResult:
    intel_id: str
    operacion_tipo: str  # 'individual', 'composicion', 'fusion', 'loop'
    output_raw: str  # texto completo del LLM
    output_json: dict | None  # JSON parseado si disponible
    modelo_usado: str
    input_tokens: int
    output_tokens: int
    coste_usd: float
    tiempo_s: float
    pasada: int = 1


@dataclass
class ExecutionPlan:
    results: dict[str, ExecutionResult] = field(default_factory=dict)
    total_cost: float = 0.0
    total_time: float = 0.0
    errors: list[str] = field(default_factory=list)


def try_parse_json(text: str) -> dict | None:
    """Intenta extraer JSON de una respuesta que puede tener texto alrededor."""
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(.*?)\s*```',
        r'(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def ejecutar_plan(
    prompts: list[PromptPlan],
    input_text: str,
    contexto: str | None,
    inteligencias_data: dict,
    presupuesto_max: float,
) -> ExecutionPlan:
    """Ejecuta todos los prompts respetando dependencias y presupuesto."""
    plan = ExecutionPlan()
    outputs: dict[str, str] = {}  # intel_id → output text

    # Fase 1: Ejecutar independientes en paralelo
    independientes = [p for p in prompts if not p.depende_de and p.operacion.tipo != 'loop']

    async def ejecutar_uno(prompt_plan: PromptPlan) -> ExecutionResult:
        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Sé preciso y estructurado.",
            user_message=prompt_plan.prompt_user,
            max_tokens=4096,
            temperature=0.3,
        )
        elapsed = time.time() - t0

        parsed = try_parse_json(response)

        intel_id = prompt_plan.operacion.inteligencias[0]
        outputs[intel_id] = response

        return ExecutionResult(
            intel_id=intel_id,
            operacion_tipo=prompt_plan.operacion.tipo,
            output_raw=response,
            output_json=parsed,
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
            pasada=1,
        )

    # Ejecutar independientes
    if independientes:
        results = await asyncio.gather(
            *[ejecutar_uno(p) for p in independientes],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                plan.errors.append(str(r))
                log.error("ejecutor_error_independiente", error=str(r))
            else:
                plan.results[r.intel_id] = r
                plan.total_cost += r.coste_usd

    # Check presupuesto
    if plan.total_cost >= presupuesto_max:
        plan.errors.append(f"Presupuesto agotado: ${plan.total_cost:.2f} >= ${presupuesto_max:.2f}")
        return plan

    # Fase 2: Ejecutar dependientes (composiciones, fusiones)
    dependientes = [p for p in prompts if p.depende_de and p.operacion.tipo != 'loop']
    for prompt_plan in sorted(dependientes, key=lambda p: p.operacion.orden):
        deps_ok = all(d in outputs for d in prompt_plan.depende_de)
        if not deps_ok:
            plan.errors.append(f"Dependencias no resueltas para {prompt_plan.operacion.inteligencias}")
            continue

        # Generar prompt dinámico
        if prompt_plan.template == 'composicion':
            id_a = prompt_plan.depende_de[0]
            prompt_text = format_composicion(
                prompt_plan.intel_a, prompt_plan.intel_b,
                outputs[id_a], input_text,
            )
        elif prompt_plan.template == 'fusion':
            id_a, id_b = prompt_plan.depende_de
            prompt_text = format_fusion(
                prompt_plan.intel_a, prompt_plan.intel_b,
                outputs[id_a], outputs[id_b], input_text,
            )
        else:
            continue

        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Sé preciso y estructurado.",
            user_message=prompt_text,
            max_tokens=4096,
            temperature=0.3,
        )
        elapsed = time.time() - t0

        intel_id = prompt_plan.operacion.inteligencias[-1]
        outputs[intel_id + '_comp'] = response

        plan.results[intel_id + '_' + prompt_plan.template] = ExecutionResult(
            intel_id=intel_id,
            operacion_tipo=prompt_plan.template,
            output_raw=response,
            output_json=try_parse_json(response),
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
        )

    # Fase 3: Loop tests (pasada 2)
    loops = [p for p in prompts if p.operacion.tipo == 'loop']
    for prompt_plan in loops:
        intel_id = prompt_plan.operacion.inteligencias[0]
        if intel_id not in outputs:
            continue

        prompt_text = format_loop(
            prompt_plan.intel_data, outputs[intel_id],
        )

        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde en español. Solo hallazgos NUEVOS.",
            user_message=prompt_text,
            max_tokens=2048,
            temperature=0.2,
        )
        elapsed = time.time() - t0

        outputs[intel_id + '_loop'] = response
        plan.results[intel_id + '_loop'] = ExecutionResult(
            intel_id=intel_id,
            operacion_tipo='loop',
            output_raw=response,
            output_json=try_parse_json(response),
            modelo_usado=prompt_plan.modelo,
            input_tokens=0,
            output_tokens=0,
            coste_usd=0,
            tiempo_s=elapsed,
            pasada=2,
        )

    plan.total_time = sum(r.tiempo_s for r in plan.results.values())
    plan.total_cost = llm.total_cost  # acumulado real

    return plan
