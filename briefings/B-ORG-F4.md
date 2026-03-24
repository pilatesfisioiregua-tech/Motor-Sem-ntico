# B-ORG-F4 — Fase 4: Motor Unificado + Pizarras Cognitiva/Temporal/Modelos/Caché

**Fecha:** 24 marzo 2026
**Estimación:** ~17h
**Prerequisito:** B-ORG-F2 (pizarras en DB, pizarras.py)
**WIP:** 1 (secuencial)
**Principios:** P61 (piensa CON el motor), P63 (leen intenciones, no instrucciones), P64 (pizarras), P66 (circuitos)

---

## OBJETIVO

Unificar los DOS MUNDOS DESCONECTADOS (pipeline 7 capas + organismo pilates/) en un ÚNICO motor de pensamiento. Eliminar duplicación de clientes LLM. Los agentes dejan de tener prompts hardcoded — leen recetas de la pizarra cognitiva.

**Antes:** Pipeline (llm_client.py/Anthropic directo) || Organismo (openrouter_client.py). Desconectados.
**Después:** `motor.pensar()` → único punto de entrada para TODO pensamiento, con selección de modelo desde pizarra, caché semántico, verificación IC, y presupuesto por ciclo.

---

## ESTADO ACTUAL — LOS 2 MUNDOS

**Mundo 1: Pipeline 7 capas** (`src/pipeline/`)
- Cliente: `llm_client.py` → Anthropic directo, 4 keys rotación
- Modelos: `settings.py` hardcoded (MODEL_ROUTER=sonnet, MODEL_EXTRACTOR=haiku, MODEL_INTEGRATOR=sonnet)
- Coste: ~$1/ejecución manual
- Acceso: Solo via `POST /motor/ejecutar`

**Mundo 2: Organismo Pilates** (`src/pilates/`)
- Cliente: `openrouter_client.py` → OpenRouter
- Modelos: hardcoded por archivo (enjambre=sonnet, director=opus, af=sonnet, etc.)
- Coste: ~$2/semana automático
- Acceso: Cron semanal + endpoints

**Deuda:** 2 facturas, 2 mecanismos retry, modelos hardcoded en 10+ sitios.

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/pipeline/orchestrator.py       ← Pipeline 7 capas completo
src/utils/llm_client.py            ← Cliente Anthropic directo
src/utils/openrouter_client.py     ← Cliente OpenRouter
src/config/settings.py             ← Modelos hardcoded
src/pilates/pizarras.py            ← Helper pizarras (creado en F2)
src/pilates/enjambre.py            ← 13 clusters hardcoded
src/pilates/director_opus.py       ← Director con manual
src/pilates/af1_conservacion.py    ← AF1 ejemplo
src/pilates/af3_depuracion.py      ← AF3 ejemplo
src/pilates/af5_identidad.py       ← AF5 ejemplo
src/pilates/af_restantes.py        ← AF2,AF4,AF6,AF7
src/pilates/recompilador.py        ← Sonnet recompila configs
src/pilates/config_agentes.py      ← om_config_agentes (push model)
```

---

## PASO 0: MIGRACIÓN SQL (029_motor_cache.sql)

Crear archivo: `migrations/029_motor_cache.sql`

```sql
-- 029_motor_cache.sql — Caché semántico LLM + telemetría motor
-- Fase 4 del Roadmap v4 (P66)

-- 1. Caché semántico LLM (Pizarra Caché #10)
CREATE TABLE IF NOT EXISTS om_pizarra_cache_llm (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    prompt_hash TEXT NOT NULL,
    prompt_embedding vector(768),
    modelo TEXT NOT NULL,
    funcion TEXT,
    lente TEXT,
    respuesta TEXT NOT NULL,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    coste_usd FLOAT DEFAULT 0,
    hits INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ DEFAULT (now() + interval '7 days')
);
CREATE INDEX IF NOT EXISTS idx_cache_hash ON om_pizarra_cache_llm(prompt_hash);
CREATE INDEX IF NOT EXISTS idx_cache_embedding ON om_pizarra_cache_llm
    USING hnsw (prompt_embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON om_pizarra_cache_llm(expires_at);

-- 2. Telemetría de llamadas LLM
CREATE TABLE IF NOT EXISTS om_motor_telemetria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    funcion TEXT,
    lente TEXT,
    modelo TEXT NOT NULL,
    tokens_input INT,
    tokens_output INT,
    coste_usd FLOAT,
    tiempo_ms INT,
    cache_hit BOOLEAN DEFAULT false,
    ciclo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_telem_tenant_ciclo ON om_motor_telemetria(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_telem_modelo ON om_motor_telemetria(modelo);

-- 3. Limpieza automática de caché expirado (función para cron)
CREATE OR REPLACE FUNCTION limpiar_cache_expirado() RETURNS void AS $$
    DELETE FROM om_pizarra_cache_llm WHERE expires_at < now();
$$ LANGUAGE sql;
```

**Test 0.1:** `SELECT count(*) FROM om_pizarra_cache_llm` → 0
**Test 0.2:** `SELECT count(*) FROM om_motor_telemetria` → 0

---

## PASO 1: motor/pensar.py — API ÚNICA DE PENSAMIENTO (P61)

Crear directorio y archivo: `src/motor/pensar.py`

También crear `src/motor/__init__.py` vacío.

```python
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
        json_schema=config.json_schema,
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
    global _presupuesto_ciclo
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
    json_schema: dict = None,
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

    async with httpx.AsyncClient(timeout=90.0) as client:
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
```

**Test 1.1:** `python -c "from src.motor.pensar import pensar, ConfigPensamiento; print('ok')"` → ok
**Test 1.2:** `python -c "from src.motor.pensar import _estimar_coste; print(_estimar_coste('deepseek/deepseek-v3.2', 1000, 500))"` → ~0.0007

---

## PASO 2: motor/verificar.py — VERIFICACIÓN POST-OUTPUT ($0)

Crear archivo: `src/motor/verificar.py`

```python
"""motor.verificar() — Verificación post-output (código puro, $0).

Verifica que el output de un pensamiento cumple las invariantes:
- IC2: No-conmutatividad (orden importa)
- IC3: Desacoples detectados (contradicciones internas)
- IC4: Razonamiento circular detectado
- IC6: Falacias verificadas
- Reglas del compilador (14 reglas)

Todo es determinístico. No llama a ningún LLM.
"""
from __future__ import annotations

import re
import structlog
from dataclasses import dataclass, field

log = structlog.get_logger()


@dataclass
class ResultadoVerificacion:
    """Resultado de verificar un output."""
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    score: float = 1.0  # 0.0-1.0


def verificar(
    texto: str,
    ints_usadas: list[str] = None,
    ps_usados: list[str] = None,
    rs_usados: list[str] = None,
    funcion: str = None,
) -> ResultadoVerificacion:
    """Verifica un output contra invariantes del sistema.

    Args:
        texto: Output del LLM a verificar
        ints_usadas: INTs que se usaron para generar el output
        ps_usados: Pensamientos usados
        rs_usados: Razonamientos usados
        funcion: Función (F1-F7) para reglas específicas

    Returns:
        ResultadoVerificacion con ok, warnings, errors, score
    """
    result = ResultadoVerificacion()

    if not texto or len(texto.strip()) < 10:
        result.ok = False
        result.errors.append("Output vacío o demasiado corto")
        result.score = 0.0
        return result

    # V1: Detectar output genérico / placeholder
    marcadores_genericos = [
        "como asistente de IA",
        "como modelo de lenguaje",
        "no puedo proporcionar",
        "es importante considerar",
        "hay que tener en cuenta que",
    ]
    for m in marcadores_genericos:
        if m.lower() in texto.lower():
            result.warnings.append(f"Output genérico detectado: '{m}'")
            result.score -= 0.1

    # V2: Detectar repetición excesiva (posible loop)
    sentences = [s.strip() for s in texto.split('.') if len(s.strip()) > 20]
    if len(sentences) > 3:
        unique = set(sentences)
        ratio = len(unique) / len(sentences)
        if ratio < 0.5:
            result.warnings.append(f"Repetición excesiva: {ratio:.0%} frases únicas")
            result.score -= 0.2

    # V3: Si hay INTs, verificar que el output las refleja mínimamente
    if ints_usadas and len(ints_usadas) >= 2:
        # Al menos debería tener párrafos proporcionales a las INTs
        parrafos = [p for p in texto.split('\n\n') if len(p.strip()) > 30]
        if len(parrafos) < len(ints_usadas) * 0.5:
            result.warnings.append(
                f"Output corto para {len(ints_usadas)} INTs "
                f"({len(parrafos)} párrafos)")
            result.score -= 0.1

    # V4: Detectar JSON malformado si se esperaba
    if texto.strip().startswith('{') or texto.strip().startswith('['):
        try:
            import json
            json.loads(texto)
        except Exception:
            # Intentar extraer JSON
            from src.pilates.json_utils import extraer_json
            parsed = extraer_json(texto)
            if not parsed:
                result.errors.append("JSON malformado en output")
                result.score -= 0.3

    # V5: F3 Depuración no debe sugerir añadir (solo eliminar)
    if funcion == "F3":
        marcadores_adicion = ["añadir", "crear nuevo", "implementar", "construir"]
        for m in marcadores_adicion:
            if m.lower() in texto.lower():
                result.warnings.append(
                    f"F3 (Depuración) sugiere adición: '{m}' — debería solo eliminar")
                result.score -= 0.05

    # Normalizar score
    result.score = max(0.0, min(1.0, result.score))
    result.ok = result.score >= 0.5 and len(result.errors) == 0

    return result
```

**Test 2.1:** `python -c "from src.motor.verificar import verificar; r = verificar('Texto normal de prueba suficientemente largo.'); print(r.ok, r.score)"` → True 1.0
**Test 2.2:** `python -c "from src.motor.verificar import verificar; r = verificar(''); print(r.ok)"` → False

---

## PASO 3: ENJAMBRE USA motor.pensar() (src/pilates/enjambre.py)

La idea NO es reescribir todo el enjambre, sino cambiar la función que hace las llamadas LLM.

Buscar la función que llama a OpenRouter en el enjambre (probablemente `_ejecutar_cluster` o similar que usa `httpx` directamente) y reemplazar por `motor.pensar()`.

**Patrón a buscar:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    resp = await client.post(OPENROUTER_BASE_URL, ...)
```

**Reemplazar por:**
```python
from src.motor.pensar import pensar, ConfigPensamiento

config = ConfigPensamiento(
    funcion="*",  # o la función del cluster
    lente=cluster.get("lente"),
    complejidad="media",
    usar_cache=True,
)
resultado = await pensar(system=system_prompt, user=user_prompt, config=config)
texto = resultado.texto
```

**Nota:** Leer `enjambre.py` completo para encontrar todos los puntos de llamada LLM. Puede haber 2-3 funciones distintas (clusters INT, clusters P, clusters R). Reemplazar TODAS con `motor.pensar()`.

**Test 3.1:** `grep "httpx" src/pilates/enjambre.py` → 0 resultados (todo va por motor.pensar)
**Test 3.2:** `grep "motor.pensar" src/pilates/enjambre.py` → match

---

## PASO 4: DIRECTOR OPUS USA motor.pensar() (src/pilates/director_opus.py)

Similar al enjambre. El Director actualmente llama a OpenRouter directamente:

```python
resp = await client.post(OPENROUTER_BASE_URL, headers=headers, json=body)
```

Reemplazar por:
```python
from src.motor.pensar import pensar, ConfigPensamiento

config = ConfigPensamiento(
    funcion="F5",  # Director diseña identidad/inteligencia
    lente="sentido",
    complejidad="alta",  # Opus
    max_tokens=8192,
    temperature=0.2,
    usar_cache=False,  # Director siempre fresco
)
resultado = await pensar(system=SYSTEM_DIRECTOR, user=user_prompt, config=config)
```

**Test 4.1:** `grep "httpx" src/pilates/director_opus.py` → 0 resultados
**Test 4.2:** `grep "motor.pensar" src/pilates/director_opus.py` → match

---

## PASO 5: DIRECTOR ESCRIBE EN 3 PIZARRAS (P63 + P64)

Actualmente el Director escribe en `om_config_agentes`. Debe escribir en:
1. **Pizarra Cognitiva** — recetas INT×P×R por función
2. **Pizarra Temporal** — orden de ejecución de componentes
3. **Pizarra Interfaz** — qué módulos mostrar en Cockpit

En `director_opus.py`, después de parsear el output del Director, añadir escritura a pizarras:

```python
async def _escribir_pizarras(tenant_id: str, ciclo: str, output: dict):
    """Director escribe en las 3 pizarras que le corresponden."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        # 1. Pizarra Cognitiva — recetas por función
        recetas = output.get("recetas", [])
        for r in recetas:
            await conn.execute("""
                INSERT INTO om_pizarra_cognitiva
                    (tenant_id, ciclo, funcion, lente, prioridad,
                     ints, ps, rs, prompt_imperativo, prompt_preguntas,
                     prompt_provocacion, prompt_razonamiento, intencion, origen)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, 'director')
            """, tenant_id, ciclo, r.get("funcion", "*"),
                r.get("lente"), r.get("prioridad", 5),
                r.get("ints", []), r.get("ps", []), r.get("rs", []),
                r.get("prompt_imperativo"), r.get("prompt_preguntas"),
                r.get("prompt_provocacion"), r.get("prompt_razonamiento"),
                r.get("intencion"))

        # 2. Pizarra Temporal — orden de ejecución
        plan = output.get("plan_temporal", [])
        for i, p in enumerate(plan):
            await conn.execute("""
                INSERT INTO om_pizarra_temporal
                    (tenant_id, ciclo, fase, orden, componente, activo, motivo)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, tenant_id, ciclo, p.get("fase", "ejecutiva"),
                i + 1, p.get("componente"), p.get("activo", True),
                p.get("motivo"))

        # 3. Pizarra Interfaz — módulos cockpit
        layout = output.get("layout", [])
        for l in layout:
            await conn.execute("""
                INSERT INTO om_pizarra_interfaz
                    (tenant_id, ciclo, modulo, rol, prioridad, motivo, origen)
                VALUES ($1, $2, $3, $4, $5, $6, 'director')
            """, tenant_id, ciclo, l.get("modulo"),
                l.get("rol", "secundario"), l.get("prioridad", 5),
                l.get("motivo"))

    log.info("director_pizarras_escritas", ciclo=ciclo,
             recetas=len(recetas), plan=len(plan), layout=len(layout))
```

Llamar `_escribir_pizarras()` en `dirigir_orquesta()` después del parseo del output.

**Nota:** El MANUAL_DIRECTOR_OPUS.md necesita actualizarse para indicar al Director que produzca secciones `recetas`, `plan_temporal` y `layout` en su output JSON. Esto requiere leer y editar el manual.

**Test 5.1:** Tras ejecutar Director: `SELECT count(*) FROM om_pizarra_cognitiva WHERE origen='director'` → >0
**Test 5.2:** `SELECT count(*) FROM om_pizarra_temporal` → >0

---

## PASO 6: ejecutar_af() GENÉRICO (P63)

Crear archivo: `src/pilates/af_generico.py`

```python
"""AF Genérico — Ejecuta cualquier función leyendo Pizarra Cognitiva (P63).

Reemplaza la lógica hardcoded de af1_conservacion, af3_depuracion, etc.
Los sensores de cada AF se mantienen como funciones importadas.
La INTELIGENCIA viene de la pizarra (escrita por Director Opus).
"""
from __future__ import annotations

import structlog
from typing import Optional

from src.motor.pensar import pensar, ConfigPensamiento
from src.motor.verificar import verificar

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def ejecutar_af(
    funcion: str,
    datos_sensor: dict,
    ciclo: str = None,
    fallback_instruccion: str = None,
) -> dict:
    """Ejecuta un agente funcional genérico.

    1. Lee receta de Pizarra Cognitiva (escrita por Director)
    2. Si no hay receta, usa fallback_instruccion
    3. Llama a motor.pensar() con la receta
    4. Verifica output con motor.verificar()
    5. Emite señales al bus
    """
    from src.pilates.pizarras import leer_recetas_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo

    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    # 1. Leer receta de pizarra
    recetas = await leer_recetas_ciclo(TENANT, ciclo)
    receta = None
    for r in recetas:
        if r.get("funcion") == funcion:
            receta = r
            break
    # Buscar receta universal si no hay específica
    if not receta:
        for r in recetas:
            if r.get("funcion") == "*":
                receta = r
                break

    # 2. Construir prompt
    if receta:
        system = _construir_system_desde_receta(funcion, receta)
        user = _construir_user_desde_datos(funcion, datos_sensor, receta)
        complejidad = "alta" if funcion in ("F3", "F5") else "media"
    elif fallback_instruccion:
        system = f"Eres el agente {funcion} del organismo cognitivo. {fallback_instruccion}"
        user = f"Datos del sensor:\n{_formatear_datos(datos_sensor)}\n\nAnaliza y propón acciones."
        complejidad = "media"
    else:
        log.warning("af_sin_receta_ni_fallback", funcion=funcion, ciclo=ciclo)
        return {"status": "skip", "razon": "Sin receta ni fallback"}

    # 3. Pensar
    config = ConfigPensamiento(
        funcion=funcion,
        lente=receta.get("lente") if receta else None,
        complejidad=complejidad,
        usar_cache=False,  # AF siempre fresco (datos cambian cada semana)
    )
    resultado = await pensar(system=system, user=user, config=config)

    # 4. Verificar
    ints = receta.get("ints", []) if receta else []
    verif = verificar(resultado.texto, ints_usadas=ints, funcion=funcion)

    if not verif.ok:
        log.warning("af_verificacion_fallida",
                    funcion=funcion, errors=verif.errors, score=verif.score)

    # 5. Emitir señales al bus (si hay alertas en el output)
    alertas_emitidas = 0
    try:
        from src.pilates.json_utils import extraer_json
        parsed = extraer_json(resultado.texto, fallback={"acciones": []})
        acciones = parsed.get("acciones", parsed.get("alertas", []))
        if acciones:
            alertas_emitidas = await _emitir_senales(funcion, acciones)
    except Exception as e:
        log.warning("af_senales_error", error=str(e)[:80])

    return {
        "status": "ok",
        "funcion": funcion,
        "modelo": resultado.modelo,
        "coste": resultado.coste_usd,
        "verificacion_score": verif.score,
        "verificacion_warnings": verif.warnings,
        "alertas_emitidas": alertas_emitidas,
    }


def _construir_system_desde_receta(funcion: str, receta: dict) -> str:
    """Construye system prompt desde receta del Director."""
    parts = [f"Eres el agente {funcion} del organismo cognitivo."]
    if receta.get("intencion"):
        parts.append(f"Intención: {receta['intencion']}")
    if receta.get("prompt_imperativo"):
        parts.append(f"INSTRUCCIÓN:\n{receta['prompt_imperativo']}")
    if receta.get("prompt_provocacion"):
        parts.append(f"PROVOCACIÓN:\n{receta['prompt_provocacion']}")
    parts.append("Responde en JSON con campos: analisis, acciones[], severidad.")
    return "\n\n".join(parts)


def _construir_user_desde_datos(funcion: str, datos: dict, receta: dict) -> str:
    """Construye user message con datos del sensor + preguntas del Director."""
    parts = [f"DATOS DEL SENSOR {funcion}:\n{_formatear_datos(datos)}"]
    if receta.get("prompt_preguntas"):
        parts.append(f"PREGUNTAS A RESPONDER:\n{receta['prompt_preguntas']}")
    if receta.get("prompt_razonamiento"):
        parts.append(f"RAZONAMIENTO REQUERIDO:\n{receta['prompt_razonamiento']}")
    return "\n\n".join(parts)


def _formatear_datos(datos: dict) -> str:
    """Formatea datos del sensor para el prompt."""
    import json
    return json.dumps(datos, indent=2, ensure_ascii=False, default=str)


async def _emitir_senales(funcion: str, acciones: list) -> int:
    """Emite señales al bus desde las acciones del AF."""
    from src.db.client import get_pool
    pool = await get_pool()
    emitidas = 0

    async with pool.acquire() as conn:
        for a in acciones[:10]:  # Max 10 señales por AF
            tipo = a.get("tipo", "ALERTA")
            prioridad = {"alta": 1, "media": 3, "baja": 5}.get(
                a.get("severidad", "media"), 3)
            try:
                await conn.execute("""
                    INSERT INTO om_senales_agentes
                        (tenant_id, origen, tipo_senal, prioridad, contenido, procesada)
                    VALUES ($1, $2, $3, $4, $5, false)
                """, TENANT, funcion, tipo, prioridad,
                    a.get("descripcion", str(a)[:500]))
                emitidas += 1
            except Exception:
                pass

    return emitidas
```

**Nota:** Los AF existentes (af1_conservacion.py, etc.) NO se eliminan todavía. Sus funciones de SENSOR se mantienen. Solo la parte de "pensar" se reemplaza cuando haya recetas en la pizarra. La transición es gradual:
1. Si hay receta en pizarra → usa `ejecutar_af()`
2. Si no hay receta → cron sigue llamando a los AF viejos como fallback

**Test 6.1:** `python -c "from src.pilates.af_generico import ejecutar_af; print('ok')"` → ok

---

## PASO 7: RESETEO PRESUPUESTO EN CRON (src/pilates/cron.py)

Al inicio de `_tarea_semanal()`, ANTES de todo lo demás:

```python
    # 0. Resetear presupuesto LLM semanal
    try:
        from src.motor.pensar import resetear_presupuesto
        resetear_presupuesto()
        log.info("cron_semanal_presupuesto_reset")
    except Exception as e:
        log.error("cron_semanal_presupuesto_error", error=str(e))
```

Y en `_tarea_mensual()`, añadir limpieza de caché expirado:

```python
    # Limpiar caché LLM expirado
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT limpiar_cache_expirado()")
        log.info("cron_mensual_cache_limpiado")
    except Exception as e:
        log.error("cron_mensual_cache_limpieza_error", error=str(e))
```

**Test 7.1:** `grep "resetear_presupuesto" src/pilates/cron.py` → match
**Test 7.2:** `grep "limpiar_cache_expirado" src/pilates/cron.py` → match

---

## PASO 8: ENDPOINT TELEMETRÍA MOTOR (src/pilates/router.py)

Añadir endpoint para que Jesús vea el gasto LLM:

```python
@router.get("/motor/telemetria")
async def get_motor_telemetria():
    """Telemetría del motor: gasto LLM por modelo, función, ciclo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Gasto por modelo en el ciclo actual
        por_modelo = await conn.fetch("""
            SELECT modelo, count(*) as calls,
                   SUM(coste_usd) as coste_total,
                   SUM(tokens_input + tokens_output) as tokens_total,
                   SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
            FROM om_motor_telemetria
            WHERE tenant_id = 'authentic_pilates'
                AND created_at >= date_trunc('week', now())
            GROUP BY modelo
            ORDER BY coste_total DESC
        """)

        # Gasto por función
        por_funcion = await conn.fetch("""
            SELECT funcion, count(*) as calls, SUM(coste_usd) as coste_total
            FROM om_motor_telemetria
            WHERE tenant_id = 'authentic_pilates'
                AND created_at >= date_trunc('week', now())
            GROUP BY funcion
            ORDER BY coste_total DESC
        """)

        # Caché stats
        cache_stats = await conn.fetchrow("""
            SELECT count(*) as entradas,
                   SUM(hits) as total_hits,
                   count(*) FILTER (WHERE expires_at < now()) as expiradas
            FROM om_pizarra_cache_llm
            WHERE tenant_id = 'authentic_pilates'
        """)

    return {
        "presupuesto_restante": presupuesto_restante(),
        "gastado_ciclo": _presupuesto_ciclo,
        "por_modelo": [dict(r) for r in por_modelo],
        "por_funcion": [dict(r) for r in por_funcion],
        "cache": dict(cache_stats) if cache_stats else {},
    }
```

**Test 8.1:** `curl /pilates/motor/telemetria` → JSON con presupuesto + stats

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `migrations/029_motor_cache.sql` | **NUEVO** — caché LLM + telemetría | 0 |
| `src/motor/__init__.py` | **NUEVO** — vacío | 1 |
| `src/motor/pensar.py` | **NUEVO** — API única pensamiento | 1 |
| `src/motor/verificar.py` | **NUEVO** — verificación post-output $0 | 2 |
| `src/pilates/enjambre.py` | httpx → motor.pensar() | 3 |
| `src/pilates/director_opus.py` | httpx → motor.pensar() + escribe 3 pizarras | 4, 5 |
| `src/pilates/af_generico.py` | **NUEVO** — AF genérico lee pizarra cognitiva | 6 |
| `src/pilates/cron.py` | +reseteo presupuesto + limpieza caché | 7 |
| `src/pilates/router.py` | +endpoint telemetría motor | 8 |

**NO SE ELIMINA TODAVÍA:**
- `llm_client.py` — pipeline 7 capas sigue usándolo (migración futura)
- `openrouter_client.py` — algunos componentes pueden seguir importándolo
- AF individuales — se mantienen como fallback hasta que Director escriba recetas

## TESTS FINALES (PASS/FAIL)

```
T1:  python -c "from src.motor.pensar import pensar" → sin error                    [PASS/FAIL]
T2:  python -c "from src.motor.verificar import verificar" → sin error               [PASS/FAIL]
T3:  python -c "from src.pilates.af_generico import ejecutar_af" → sin error         [PASS/FAIL]
T4:  SELECT count(*) FROM om_pizarra_cache_llm → tabla existe                        [PASS/FAIL]
T5:  SELECT count(*) FROM om_motor_telemetria → tabla existe                         [PASS/FAIL]
T6:  grep "httpx" src/pilates/enjambre.py → 0 resultados                             [PASS/FAIL]
T7:  grep "httpx" src/pilates/director_opus.py → 0 resultados                        [PASS/FAIL]
T8:  grep "motor.pensar" src/pilates/enjambre.py → match                             [PASS/FAIL]
T9:  grep "motor.pensar" src/pilates/director_opus.py → match                        [PASS/FAIL]
T10: grep "resetear_presupuesto" src/pilates/cron.py → match                         [PASS/FAIL]
T11: curl /pilates/motor/telemetria → JSON con presupuesto                           [PASS/FAIL]
T12: Ciclo semanal completo → om_motor_telemetria tiene filas                        [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear `migrations/029_motor_cache.sql` (Paso 0)
2. Crear `src/motor/__init__.py` + `src/motor/pensar.py` (Paso 1)
3. Crear `src/motor/verificar.py` (Paso 2)
4. Crear `src/pilates/af_generico.py` (Paso 6)
5. Editar `src/pilates/enjambre.py` — reemplazar httpx por motor.pensar (Paso 3)
6. Editar `src/pilates/director_opus.py` — reemplazar httpx + añadir escritura pizarras (Pasos 4, 5)
7. Editar `src/pilates/cron.py` — reseteo presupuesto + limpieza caché (Paso 7)
8. Editar `src/pilates/router.py` — endpoint telemetría (Paso 8)
9. Deploy
10. Ejecutar ciclo semanal completo (manual o esperar lunes)
11. Verificar T1-T12

## NOTAS

- La migración del pipeline 7 capas (orchestrator.py) a motor.pensar() se DEFER — es más complejo porque usa Anthropic directo con 4 keys rotación. Se puede hacer en F5 o como briefing dedicado.
- Los AF individuales (af1, af3, af5, af_restantes) NO se eliminan — se mantienen como fallback. El cron puede verificar si hay receta en pizarra → ejecutar_af genérico, sino → AF viejo.
- El caché semántico usa hash exacto (no embeddings semánticos). Los embeddings semánticos (búsqueda por similaridad al 95%) se pueden añadir después si el hash exacto no es suficiente.
- Presupuesto semanal default: $5 (suficiente para ~2 ciclos completos + Director Opus).
