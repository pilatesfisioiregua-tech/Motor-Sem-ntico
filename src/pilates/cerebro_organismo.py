"""Cerebro del Organismo — Capa de razonamiento LLM para agentes autónomos.

Dos niveles de razonamiento:
  NIVEL 1 (gpt-4o): AF1-AF7 + Gestor — razonamiento de negocio en español
  NIVEL 2 (claude-sonnet-4.6): Ejecutor + Convergencia — razonamiento complejo cross-AF

El sensor no cambia. El bus no cambia. Se AÑADE cerebro entre detección y emisión.
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
from datetime import date

from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Nivel 1: Razonamiento de negocio (español peninsular, acciones concretas)
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")

# Nivel 2: Razonamiento complejo (conflictos cross-AF, patrones sistémicos)
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4-6")


async def _contexto_negocio() -> str:
    """Contexto actualizado del negocio para inyectar en cada razonamiento."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'",
            TENANT) or 0

        grupos = await conn.fetch("""
            SELECT g.nombre, g.dias_semana, g.capacidad_max,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.grupo_id=g.id AND c.estado='activo') as ocupadas
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
        """, TENANT)

        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT)

        ultimo_acd = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        señales_recientes = await conn.fetch("""
            SELECT tipo, origen, payload, prioridad, created_at
            FROM om_senales_agentes WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 20
        """, TENANT)

    grupos_str = "\n".join(
        f"  - {g['nombre']}: {g['ocupadas']}/{g['capacidad_max']} plazas, días: {g['dias_semana']}"
        for g in grupos
    )

    señales_str = "\n".join(
        f"  - [{s['origen']}] {s['tipo']}: {json.dumps(s['payload'], ensure_ascii=False)[:120]}"
        for s in señales_recientes[:10]
    )

    acd_str = "Sin diagnóstico"
    if ultimo_acd:
        acd_str = f"Estado: {ultimo_acd['estado_pre']}, Lentes: {ultimo_acd['lentes_pre']}"

    return f"""AUTHENTIC PILATES — Estudio de Pilates en Albelda de Iregua (La Rioja)
Dueño: Jesús. Instructor único. Método EEDAP (Pilates auténtico).
~{clientes} clientes activos. Pueblo de ~4.000 hab, cabeza de comarca, cerca de Logroño.
Ingresos este mes: {float(ingresos):.0f}€.
Diagnóstico ACD: {acd_str}

GRUPOS ACTIVOS:
{grupos_str}

SEÑALES RECIENTES EN EL BUS:
{señales_str}

Fecha: {date.today()}"""


async def _call_llm(model: str, system_prompt: str, user_prompt: str,
                     max_tokens: int = 1500, temperature: float = 0.4) -> str:
    """Llamada genérica a LLM via OpenRouter."""
    timeout = 90 if max_tokens > 1500 else 45
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://motor-semantico-omni.fly.dev",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _parse_json(raw: str) -> dict:
    """Parsea JSON tolerante a markdown fences y prefijos.

    Delega en extraer_json (json_utils).
    """
    return extraer_json(raw)


async def razonar(
    agente: str,
    funcion: str,
    datos_detectados: dict,
    instruccion_especifica: str,
    nivel: int = 1,
) -> dict:
    """Razonamiento LLM para agentes del organismo.

    Args:
        agente: Nombre del agente (AF1, AF3, EJECUTOR, etc.)
        funcion: Función L0.7 (F1 Conservación, F3 Depuración, etc.)
        datos_detectados: Output del sensor (código puro)
        instruccion_especifica: Qué debe razonar este agente
        nivel: 1 = gpt-4o (negocio), 2 = claude-sonnet (complejo)

    Returns:
        {
            "interpretacion": str,
            "acciones": [{"accion": str, "prioridad": int, "impacto": str,
                          "esfuerzo": str, "cliente_id": str|None, "grupo_id": str|None}],
            "patron_detectado": str | None,
            "alerta_critica": str | None,
        }
    """
    if not OPENROUTER_API_KEY:
        return {
            "interpretacion": "Sin modelo LLM configurado. Datos crudos.",
            "acciones": [{"accion": json.dumps(datos_detectados, ensure_ascii=False)[:200],
                          "prioridad": 3, "impacto": "desconocido", "esfuerzo": "desconocido"}],
            "patron_detectado": None,
            "alerta_critica": None,
        }

    model = BRAIN_MODEL if nivel == 1 else REASONING_MODEL
    contexto = await _contexto_negocio()

    # Intentar cargar config dinámica (Recompilador)
    try:
        from src.pilates.recompilador import construir_prompt_desde_config
        prompt_dinamico = await construir_prompt_desde_config(agente, funcion, contexto)
        if prompt_dinamico:
            log.info("cerebro_usando_config_dinamica", agente=agente)
            system_prompt = prompt_dinamico
        else:
            system_prompt = None
    except Exception:
        system_prompt = None

    if system_prompt is None:
        system_prompt = f"""Eres el cerebro del agente {agente} ({funcion}) del organismo cognitivo de Authentic Pilates.

Tu trabajo: interpretar datos operativos y proponer acciones CONCRETAS, PRIORIZADAS y ACCIONABLES.

REGLAS:
1. No repitas los datos — interprétalos. ¿QUÉ SIGNIFICAN? ¿POR QUÉ pasa esto?
2. Cada acción debe ser ejecutable por Jesús (el dueño) en <5 minutos.
3. Prioriza por impacto en ingresos y retención.
4. Si ves un patrón que cruza varios datos, señálalo.
5. Si algo es urgente (riesgo de perder cliente o dinero HOY), marca alerta_critica.
6. Tono: directo, sin formalismos. Como hablar con un socio inteligente.
7. Las acciones deben ser ESPECÍFICAS: no "contactar al cliente" sino "enviar WA a María preguntando si la espalda le ha mejorado desde la última sesión".

CONTEXTO DEL NEGOCIO:
{contexto}

Responde SOLO en JSON válido con esta estructura:
{{
    "interpretacion": "... (2-4 frases: qué significan los datos, por qué pasa)",
    "acciones": [
        {{
            "accion": "... (acción concreta y específica)",
            "prioridad": 1-5,
            "impacto": "... (qué efecto tendrá si se hace)",
            "esfuerzo": "bajo|medio|alto",
            "cliente_id": "uuid o null",
            "grupo_id": "uuid o null"
        }}
    ],
    "patron_detectado": "... o null",
    "alerta_critica": "... o null"
}}"""

    user_prompt = f"""{instruccion_especifica}

DATOS DETECTADOS POR LOS SENSORES:
{json.dumps(datos_detectados, ensure_ascii=False, indent=2)}"""

    tokens = 2500 if nivel == 2 else 1500

    try:
        raw = await _call_llm(model, system_prompt, user_prompt, max_tokens=tokens)
        resultado = _parse_json(raw)
    except json.JSONDecodeError:
        log.warning("cerebro_parse_error", agente=agente, model=model)
        return {"interpretacion": raw[:500] if 'raw' in dir() else "Parse error",
                "acciones": [], "patron_detectado": None, "alerta_critica": None}
    except Exception as e:
        log.error("cerebro_llm_error", agente=agente, model=model, error=str(e))
        return {"interpretacion": f"Error: {str(e)[:100]}",
                "acciones": [], "patron_detectado": None, "alerta_critica": None}

    log.info("cerebro_ok", agente=agente, model=model.split("/")[-1],
             acciones=len(resultado.get("acciones", [])),
             critica=resultado.get("alerta_critica") is not None)

    return resultado
