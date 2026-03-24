"""motor.pensar() — API única de pensamiento del organismo (P61).

TODO pensamiento del sistema pasa por aquí:
- Enjambre (clusters contextualizadores)
- Agentes funcionales (AF1-AF7)
- Director Opus (partituras)
- Séquito (24 asesores)
- Pipeline 7 capas (integración futura)

Selección de modelo desde Pizarra Modelos con fallback chain.
Caché semántico opcional.
Telemetría por llamada.
Presupuesto por ciclo.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import structlog
from dataclasses import dataclass, field
from typing import Optional

log = structlog.get_logger()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Presupuesto por ciclo (reseteado cada semana)
_presupuesto_ciclo: float = 0.0
PRESUPUESTO_MAX_SEMANAL = float(os.getenv("PRESUPUESTO_LLM_SEMANAL", "5.0"))


@dataclass
class ConfigPensamiento:
    """Configuración de una invocación de pensamiento."""
    funcion: str = "*"                  # F1..F7 o "*" para genérico
    lente: Optional[str] = None         # S, Se, C o None
    complejidad: str = "media"          # baja, media, alta
    tenant_id: str = "authentic_pilates"
    max_tokens: int = 4096
    temperature: float = 0.1
    usar_cache: bool = True             # Intentar caché semántico
    ttl_cache_horas: int = 168          # 7 días
    json_schema: Optional[dict] = None  # Para respuesta estructurada
    timeout: float = 90.0               # Timeout en segundos


@dataclass
class Pensamiento:
    """Resultado de una invocación de pensamiento."""
    texto: str
    modelo: str
    tokens_input: int = 0
    tokens_output: int = 0
    coste_usd: float = 0.0
    tiempo_ms: int = 0
    cache_hit: bool = False
    funcion: str = "*"
    lente: Optional[str] = None


async def pensar(
    system: str,
    user: str,
    config: ConfigPensamiento = None,
) -> Pensamiento:
    """Punto único de entrada para TODO pensamiento LLM.

    1. Selecciona modelo desde Pizarra Modelos
    2. Verifica presupuesto
    3. Busca en caché semántico
    4. Llama a OpenRouter
    5. Guarda en caché + telemetría
    """
    global _presupuesto_ciclo

    if config is None:
        config = ConfigPensamiento()

    t0 = time.time()

    # 1. Seleccionar modelo desde pizarra (con fallback)
    modelo = await _seleccionar_modelo(config)

    # 2. Verificar presupuesto
    if _presupuesto_ciclo >= PRESUPUESTO_MAX_SEMANAL:
        # Degradar a modelo barato
        modelo = "deepseek/deepseek-v3.2"
        log.warning("motor_presupuesto_excedido",
                    gastado=_presupuesto_ciclo, max=PRESUPUESTO_MAX_SEMANAL)

    # 3. Caché semántico
    if config.usar_cache:
        cached = await _buscar_cache(system, user, modelo)
        if cached:
            log.info("motor_cache_hit", funcion=config.funcion, modelo=modelo)
            return Pensamiento(
                texto=cached, modelo=modelo,
                cache_hit=True, funcion=config.funcion, lente=config.lente,
            )

    # 4. Llamar LLM via OpenRouter
    resultado = await _llamar_openrouter(
        modelo=modelo, system=system, user=user,
        max_tokens=config.max_tokens, temperature=config.temperature,
        json_schema=config.json_schema, timeout=config.timeout,
    )

    tiempo_ms = int((time.time() - t0) * 1000)

    pensamiento = Pensamiento(
        texto=resultado["texto"],
        modelo=modelo,
        tokens_input=resultado["tokens_input"],
        tokens_output=resultado["tokens_output"],
        coste_usd=resultado["coste_usd"],
        tiempo_ms=tiempo_ms,
        funcion=config.funcion,
        lente=config.lente,
    )

    # 5. Actualizar presupuesto
    _presupuesto_ciclo += pensamiento.coste_usd

    # 6. Guardar en caché + telemetría (fire and forget)
    if config.usar_cache and not pensamiento.cache_hit:
        try:
            await _guardar_cache(system, user, modelo, pensamiento.texto, config)
        except Exception as e:
            log.warning("motor_cache_save_error", error=str(e)[:80])

    try:
        await _registrar_telemetria(pensamiento, config)
    except Exception as e:
        log.warning("motor_telemetria_error", error=str(e)[:80])

    log.info("motor_pensar_ok",
             funcion=config.funcion, modelo=modelo,
             tokens=pensamiento.tokens_input + pensamiento.tokens_output,
             coste=round(pensamiento.coste_usd, 4),
             tiempo_ms=tiempo_ms)

    return pensamiento


def resetear_presupuesto():
    """Llamar al inicio de cada ciclo semanal."""
    global _presupuesto_ciclo
    _presupuesto_ciclo = 0.0


def presupuesto_restante() -> float:
    return max(0, PRESUPUESTO_MAX_SEMANAL - _presupuesto_ciclo)


# ============================================================
# SELECCIÓN DE MODELO (Pizarra Modelos)
# ============================================================

async def _seleccionar_modelo(config: ConfigPensamiento) -> str:
    """Selecciona modelo desde pizarra modelos con fallback chain."""
    try:
        from src.pilates.pizarras import leer_modelo
        return await leer_modelo(
            config.tenant_id, config.funcion, config.lente, config.complejidad)
    except Exception:
        defaults = {
            "baja": "deepseek/deepseek-v3.2",
            "media": "openai/gpt-4o",
            "alta": "anthropic/claude-opus-4",
        }
        return defaults.get(config.complejidad, "openai/gpt-4o")


# ============================================================
# OPENROUTER (cliente unificado)
# ============================================================

async def _llamar_openrouter(
    modelo: str, system: str, user: str,
    max_tokens: int = 4096, temperature: float = 0.1,
    json_schema: dict = None, timeout: float = 90.0,
) -> dict:
    """Llama a OpenRouter y devuelve resultado con metadata."""
    import httpx

    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY no configurada")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "OMNI-MIND Motor",
    }

    body = {
        "model": modelo,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }

    if json_schema:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": json_schema,
        }

    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(3):
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("Sin choices")

                usage = data.get("usage", {})
                tokens_in = usage.get("prompt_tokens", 0)
                tokens_out = usage.get("completion_tokens", 0)
                coste = _estimar_coste(modelo, tokens_in, tokens_out)

                return {
                    "texto": choices[0]["message"]["content"],
                    "tokens_input": tokens_in,
                    "tokens_output": tokens_out,
                    "coste_usd": coste,
                }
            except Exception as e:
                if attempt == 2:
                    raise
                log.warning("motor_retry", modelo=modelo, attempt=attempt, error=str(e)[:80])
                import asyncio
                await asyncio.sleep(2 ** attempt)


def _estimar_coste(modelo: str, tokens_in: int, tokens_out: int) -> float:
    """Estimación de coste por modelo (USD por 1K tokens)."""
    rates = {
        "deepseek/deepseek-v3.2": (0.0003, 0.0008),
        "openai/gpt-4o": (0.0025, 0.01),
        "anthropic/claude-sonnet-4-6": (0.003, 0.015),
        "anthropic/claude-sonnet-4-6-20250514": (0.003, 0.015),
        "anthropic/claude-opus-4": (0.015, 0.075),
        "anthropic/claude-opus-4.6": (0.015, 0.075),
    }
    in_rate, out_rate = rates.get(modelo, (0.003, 0.015))
    return (tokens_in * in_rate + tokens_out * out_rate) / 1000


# ============================================================
# CACHÉ SEMÁNTICO
# ============================================================

def _hash_prompt(system: str, user: str, modelo: str) -> str:
    """Hash determinístico para lookup exacto."""
    content = f"{modelo}::{system}::{user}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


async def _buscar_cache(system: str, user: str, modelo: str) -> Optional[str]:
    """Busca en caché por hash exacto."""
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        prompt_hash = _hash_prompt(system, user, modelo)

        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT id, respuesta FROM om_pizarra_cache_llm
                WHERE prompt_hash = $1 AND modelo = $2
                    AND expires_at > now()
                ORDER BY created_at DESC LIMIT 1
            """, prompt_hash, modelo)

            if row:
                # Incrementar hits
                await conn.execute(
                    "UPDATE om_pizarra_cache_llm SET hits = hits + 1 WHERE id = $1",
                    row["id"])
                return row["respuesta"]
    except Exception:
        pass
    return None


async def _guardar_cache(system: str, user: str, modelo: str,
                         respuesta: str, config: ConfigPensamiento):
    """Guarda resultado en caché."""
    from src.db.client import get_pool
    pool = await get_pool()
    prompt_hash = _hash_prompt(system, user, modelo)

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_cache_llm
                (tenant_id, prompt_hash, modelo, funcion, lente, respuesta, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6, now() + make_interval(hours => $7))
            ON CONFLICT DO NOTHING
        """, config.tenant_id, prompt_hash, modelo, config.funcion,
            config.lente, respuesta, config.ttl_cache_horas)


# ============================================================
# TELEMETRÍA
# ============================================================

async def _registrar_telemetria(pensamiento: Pensamiento, config: ConfigPensamiento):
    """Registra cada llamada LLM en om_motor_telemetria."""
    from src.db.client import get_pool
    from datetime import datetime
    from zoneinfo import ZoneInfo

    pool = await get_pool()
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_motor_telemetria
                (tenant_id, funcion, lente, modelo, tokens_input, tokens_output,
                 coste_usd, tiempo_ms, cache_hit, ciclo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """, config.tenant_id, config.funcion, config.lente,
            pensamiento.modelo, pensamiento.tokens_input, pensamiento.tokens_output,
            pensamiento.coste_usd, pensamiento.tiempo_ms,
            pensamiento.cache_hit, ciclo)
