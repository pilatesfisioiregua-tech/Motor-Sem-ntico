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
    if not text or not text.strip():
        return None

    # Paso 0: Limpiar BOM, whitespace raro
    text = text.strip().lstrip('\ufeff')

    # Paso 1: Si empieza con { intenta directo
    if text.startswith('{'):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Paso 2: Buscar en bloques de código
    patterns = [
        r'```json\s*(.*?)\s*```',
        r'```\s*(\{.*?\})\s*```',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue

    # Paso 3: Encontrar el JSON más grande en el texto
    # Buscar desde la última { hasta su } correspondiente
    last_start = text.rfind('{')
    if last_start == -1:
        return None

    # Buscar desde la primera { también
    first_start = text.find('{')
    for start in [first_start, last_start]:
        if start == -1:
            continue
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        candidate = text[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Intentar reparar JSON común: trailing commas
            cleaned = re.sub(r',\s*}', '}', candidate)
            cleaned = re.sub(r',\s*]', ']', cleaned)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue

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
            system="Responde en español. Sé preciso y estructurado. Al final de tu respuesta SIEMPRE incluye un bloque JSON entre ```json y ``` con los campos solicitados.",
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
        # System prompt diferenciado: composiciones y fusiones = JSON puro
        sys_prompt = (
            "Responde EXCLUSIVAMENTE con JSON válido en español. "
            "Sin texto antes ni después del JSON. Sin markdown. Sin backticks. "
            "Solo el objeto JSON con todos los campos solicitados."
        )
        response = await llm.complete(
            model=prompt_plan.modelo,
            system=sys_prompt,
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

    # Fase 3: Loop tests (pasada 2) — en paralelo
    loops = [p for p in prompts if p.operacion.tipo == 'loop']

    async def ejecutar_loop(prompt_plan: PromptPlan) -> ExecutionResult | None:
        intel_id = prompt_plan.operacion.inteligencias[0]
        if intel_id not in outputs:
            return None

        prompt_text = format_loop(
            prompt_plan.intel_data, outputs[intel_id],
        )

        t0 = time.time()
        response = await llm.complete(
            model=prompt_plan.modelo,
            system="Responde EXCLUSIVAMENTE con JSON válido en español. Solo hallazgos NUEVOS. Sin texto fuera del JSON.",
            user_message=prompt_text,
            max_tokens=2048,
            temperature=0.2,
        )
        elapsed = time.time() - t0

        outputs[intel_id + '_loop'] = response
        return ExecutionResult(
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

    if loops:
        loop_results = await asyncio.gather(
            *[ejecutar_loop(p) for p in loops],
            return_exceptions=True,
        )
        for r in loop_results:
            if isinstance(r, Exception):
                plan.errors.append(str(r))
                log.error("ejecutor_error_loop", error=str(r))
            elif r is not None:
                plan.results[r.intel_id + '_loop'] = r

    plan.total_time = sum(r.tiempo_s for r in plan.results.values())
    plan.total_cost = llm.total_cost  # acumulado real

    return plan
