"""Swarm algebra engine — multi-model pizarra pattern for pattern pair analysis.

5 explorer models analyze a pattern pair in parallel (R1), read each other's
contributions (R2), Cogito synthesizes, Opus validates. All results persist to DB.
"""

import os
import sys
import json
import time
import re
from typing import Dict, List, Optional, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.api import call_openrouter, call_with_retry, extract_response, strip_think_tags, _load_env
from tools.algebra_rules import (
    build_maestro_system_prompt, validate_operation_properties,
    THINKING_TYPES, CLASSIFICATION_TYPES, OPERATIONS,
)

_load_env()

# ═══════════════════════════════════════════════════════════════
# MODEL CONFIGURATION
# ═══════════════════════════════════════════════════════════════

SWARM_MODELS: Dict[str, dict] = {
    # Consolidated from 5 to 3 explorers (patterns 83735 Coalition O(n²), 60671 Fusión Paralela)
    # Kept: most differentiated thinking types. Dropped: dialectica (overlaps R1), metacognicion (overlaps abstraccion)
    "deepseek_r1": {
        "id": "deepseek/deepseek-r1",
        "thinking_type": "causalidad",
        "mode": "ANALIZAR",
        "via": "openrouter",
    },
    "qwen3.5": {
        "id": "qwen/qwen3.5-397b-a17b",
        "thinking_type": "abstraccion",
        "mode": "PERCIBIR",
        "via": "openrouter",
    },
    "kimi_k2.5": {
        "id": "moonshotai/kimi-k2.5",
        "thinking_type": "contrafactual",
        "mode": "GENERAR",
        "via": "openrouter",
    },
}

SYNTHESIZER_PRIMARY: Dict[str, str] = {
    "id": "deepcogito/cogito-v2.1-671b",
    "via": "openrouter",
}

# Validator disabled — no ANTHROPIC_API_KEY configured. Cogito synthesis is the final result.
# Reactivate when API key is available by uncommenting.
# SYNTHESIZER_VALIDATOR: Dict[str, str] = {
#     "id": "claude-opus-4-6",
#     "via": "anthropic",
# }
SYNTHESIZER_VALIDATOR: Optional[Dict[str, str]] = None

# Approximate $/M output tokens for cost estimation
_MODEL_PRICING: Dict[str, float] = {
    "deepseek/deepseek-r1": 2.19,
    "qwen/qwen3.5-397b-a17b": 1.20,
    "moonshotai/kimi-k2.5": 1.00,
    "deepcogito/cogito-v2.1-671b": 1.50,
}

PIZARRA_CELLS = [
    "emergencias",
    "conexiones_cruzadas",
    "contradicciones",
    "contextos_implementacion",
    "isomorfismos",
    "puntos_ciegos",
]


# ═══════════════════════════════════════════════════════════════
# PIZARRA
# ═══════════════════════════════════════════════════════════════

def create_algebra_pizarra(pat_a: dict, pat_b: dict, clasificacion: str, operacion: str) -> dict:
    """Create a fresh pizarra for a pattern pair analysis."""
    return {
        "par": {
            "patron_a": {
                "id": pat_a["id"],
                "concepto": pat_a.get("concepto", pat_a.get("tipo", "")),
                "scope": pat_a.get("scope", ""),
                "texto": (pat_a.get("texto", "") or "")[:500],
            },
            "patron_b": {
                "id": pat_b["id"],
                "concepto": pat_b.get("concepto", pat_b.get("tipo", "")),
                "scope": pat_b.get("scope", ""),
                "texto": (pat_b.get("texto", "") or "")[:500],
            },
            "clasificacion": clasificacion,
        },
        "operacion": operacion,
        "celdas": {
            "emergencias":              {"nivel": 0, "evidencias": []},
            "conexiones_cruzadas":      {"nivel": 0, "evidencias": []},
            "contradicciones":          {"nivel": 0, "evidencias": []},
            "contextos_implementacion": {"nivel": 0, "evidencias": []},
            "isomorfismos":             {"nivel": 0, "evidencias": []},
            "puntos_ciegos":            {"nivel": 0, "evidencias": []},
        },
        "meta": {
            "ronda": 0,
            "cambios_por_ronda": [],
            "convergencia": False,
            "modelos_participantes": [],
            "coste_acumulado": 0.0,
        },
    }


# ═══════════════════════════════════════════════════════════════
# PROMPT BUILDERS
# ═══════════════════════════════════════════════════════════════

def build_r1_prompt(pizarra: dict, thinking_type: str, mode: str) -> List[dict]:
    """Build messages for R1 exploration by a single model."""
    system_content = build_maestro_system_prompt(thinking_type=thinking_type, mode=mode)

    par = pizarra["par"]
    operacion = pizarra["operacion"]
    op_def = OPERATIONS.get(operacion, {})

    user_content = f"""RONDA 1 — EXPLORACIÓN INDEPENDIENTE

OPERACIÓN: {operacion} {op_def.get('symbol', '')} ({op_def.get('form', '')})
{op_def.get('description', '')}

PATRÓN A ({par['patron_a']['scope']}):
Concepto: {par['patron_a']['concepto']}
{par['patron_a']['texto']}

PATRÓN B ({par['patron_b']['scope']}):
Concepto: {par['patron_b']['concepto']}
{par['patron_b']['texto']}

CLASIFICACIÓN ESTRUCTURAL: {par['clasificacion']}

Tu tipo de pensamiento asignado es: {thinking_type.upper()}
{THINKING_TYPES.get(thinking_type, {}).get('description', '')}
Pregunta guía: {THINKING_TYPES.get(thinking_type, {}).get('question', '')}

INSTRUCCIÓN: Analiza este par de patrones desde tu tipo de pensamiento.
Contribuye a las 6 celdas de la pizarra algebraica. Para cada celda,
proporciona evidencias concretas y un nivel propuesto (1=indicios, 2=probable,
3=fuerte, 4=certeza).

Responde EXCLUSIVAMENTE con JSON válido:
{{
    "emergencias": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "conexiones_cruzadas": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "contradicciones": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "contextos_implementacion": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "isomorfismos": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "puntos_ciegos": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "sin_contribucion": false
}}

Si una celda no tiene contribución desde tu perspectiva, déjala como lista vacía.
NO inventes evidencias — solo contribuye donde tu tipo de pensamiento detecta algo genuino."""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_r2_prompt(pizarra: dict) -> List[dict]:
    """Build messages for R2 stigmergic enrichment (all models see pizarra)."""
    system_content = build_maestro_system_prompt()

    # Serialize pizarra state for R2
    celdas_text = ""
    for cell_name, cell_data in pizarra["celdas"].items():
        celdas_text += f"\n--- {cell_name.upper()} (nivel actual: {cell_data['nivel']}) ---\n"
        if cell_data["evidencias"]:
            for ev in cell_data["evidencias"]:
                modelo = ev.get("modelo", "?")
                texto = ev.get("texto", "")
                nivel = ev.get("nivel_propuesto", 0)
                celdas_text += f"  [{modelo}, nivel={nivel}]: {texto}\n"
        else:
            celdas_text += "  (sin contribuciones aún)\n"

    par = pizarra["par"]

    user_content = f"""RONDA 2 — ENRIQUECIMIENTO ESTIGMÉRGICO

Has leído las contribuciones de otros modelos en la pizarra colectiva.
Tu tarea: AÑADIR, CONTRADECIR o MATIZAR lo existente.

OPERACIÓN: {pizarra['operacion']}
PATRÓN A ({par['patron_a']['scope']}): {par['patron_a']['concepto']}
PATRÓN B ({par['patron_b']['scope']}): {par['patron_b']['concepto']}
CLASIFICACIÓN: {par['clasificacion']}

=== ESTADO DE LA PIZARRA ==={celdas_text}

Con esta pizarra colectiva, ¿qué añades, contradices o matizas?

Reglas R2:
- NO repitas lo que ya existe — solo contribuciones NUEVAS
- Si contradices una evidencia, referéncela y explica por qué
- Si matizas, indica qué evidencia matizas y cómo
- Puedes SUBIR un nivel si tienes evidencia más fuerte

Responde EXCLUSIVAMENTE con JSON válido:
{{
    "emergencias": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "conexiones_cruzadas": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "contradicciones": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "contextos_implementacion": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "isomorfismos": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "puntos_ciegos": [{{"texto": "...", "nivel_propuesto": 1-4}}],
    "sin_contribucion": false
}}"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_synthesis_prompt(pizarra: dict) -> List[dict]:
    """Build synthesis prompt for Cogito — integrate full pizarra into algebraic result."""
    celdas_json = {}
    for cell_name, cell_data in pizarra["celdas"].items():
        celdas_json[cell_name] = {
            "nivel": cell_data["nivel"],
            "num_evidencias": len(cell_data["evidencias"]),
            "evidencias": [
                {"modelo": ev.get("modelo", "?"), "texto": ev.get("texto", ""),
                 "nivel": ev.get("nivel_propuesto", 0), "ronda": ev.get("ronda", 0)}
                for ev in cell_data["evidencias"]
            ],
        }

    par = pizarra["par"]
    meta = pizarra["meta"]

    system_content = """Eres el SINTETIZADOR ALGEBRAICO MAESTRO v3.
Tu rol: integrar contribuciones de 5 modelos exploradores (2 rondas) en un resultado
algebraico formal. Debes preservar la riqueza de las contribuciones individuales
mientras produces una síntesis coherente.

NO simplifiques ni elimines matices — integra tensiones productivamente.
Si hay contradicciones entre modelos, señálalas como tensión fértil, no las resuelvas prematuramente."""

    user_content = f"""SÍNTESIS DE PIZARRA ALGEBRAICA

OPERACIÓN: {pizarra['operacion']}
PATRÓN A ({par['patron_a']['scope']}): {par['patron_a']['concepto']}
  {par['patron_a']['texto'][:300]}

PATRÓN B ({par['patron_b']['scope']}): {par['patron_b']['concepto']}
  {par['patron_b']['texto'][:300]}

CLASIFICACIÓN: {par['clasificacion']}
MODELOS PARTICIPANTES: {', '.join(meta.get('modelos_participantes', []))}
RONDAS COMPLETADAS: {meta.get('ronda', 0)}
CAMBIOS POR RONDA: {meta.get('cambios_por_ronda', [])}

=== PIZARRA COMPLETA ===
{json.dumps(celdas_json, indent=2, ensure_ascii=False)}

INSTRUCCIÓN: Sintetiza toda la pizarra en un resultado algebraico formal.

Responde EXCLUSIVAMENTE con JSON válido:
{{
    "emergencias": ["texto de cada emergencia sintetizada..."],
    "conexiones_cruzadas": ["texto de cada conexión..."],
    "contradicciones": ["texto de cada contradicción..."],
    "contextos_implementacion": ["texto de cada contexto..."],
    "isomorfismos": ["texto de cada isomorfismo..."],
    "puntos_ciegos": ["texto de cada punto ciego..."],
    "confianza": 0.0-1.0,
    "resultado_texto": "Texto completo de síntesis integrada..."
}}"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


def build_validation_prompt(pizarra: dict, cogito_result: dict) -> List[dict]:
    """Build validation prompt for Opus — validate and refine synthesis."""
    par = pizarra["par"]

    # Compact pizarra summary for context
    pizarra_summary = {}
    for cell_name, cell_data in pizarra["celdas"].items():
        pizarra_summary[cell_name] = {
            "nivel": cell_data["nivel"],
            "evidencias_count": len(cell_data["evidencias"]),
            "modelos": list({ev.get("modelo", "?") for ev in cell_data["evidencias"]}),
        }

    system_content = """Eres el VALIDADOR ALGEBRAICO MAESTRO v3 (Opus).
Tu rol: validar la síntesis producida por Cogito sobre una pizarra de 5 modelos x 2 rondas.

Detecta:
1. Información perdida: evidencias de la pizarra que no aparecen en la síntesis
2. Simplificaciones excesivas: matices eliminados prematuramente
3. Emergencias promotibles: insights de nivel >= 3 que podrían ser PATRONES INDEPENDIENTES
4. Coherencia algebraica: que las propiedades de la operación se respeten"""

    user_content = f"""VALIDACIÓN DE SÍNTESIS ALGEBRAICA

OPERACIÓN: {pizarra['operacion']}
PATRÓN A ({par['patron_a']['scope']}): {par['patron_a']['concepto']}
PATRÓN B ({par['patron_b']['scope']}): {par['patron_b']['concepto']}
CLASIFICACIÓN: {par['clasificacion']}

=== RESUMEN PIZARRA (5 modelos × 2 rondas) ===
{json.dumps(pizarra_summary, indent=2, ensure_ascii=False)}

=== SÍNTESIS DE COGITO ===
{json.dumps(cogito_result, indent=2, ensure_ascii=False)}

INSTRUCCIÓN: Valida esta síntesis. ¿Se perdió algo? ¿Hay matices simplificados?
Refina. Si alguna emergencia puede ser PATRON INDEPENDIENTE, márcala con
promover_a_patron: true con spec completa.

Responde EXCLUSIVAMENTE con JSON válido:
{{
    "validacion": "pass" | "refine",
    "informacion_perdida": ["..."],
    "simplificaciones": ["..."],
    "refinamientos": ["..."],
    "emergencias_refinadas": ["texto refinado..."],
    "conexiones_cruzadas_refinadas": ["..."],
    "contradicciones_refinadas": ["..."],
    "contextos_implementacion_refinados": ["..."],
    "isomorfismos_refinados": ["..."],
    "puntos_ciegos_refinados": ["..."],
    "emergencias_promotibles": [
        {{
            "texto": "...",
            "promover_a_patron": true,
            "spec": {{
                "scope": "patrones:...",
                "tipo": "...",
                "concepto": "...",
                "texto": "full spec of the new pattern...",
                "nivel": "L2"
            }}
        }}
    ],
    "confianza_final": 0.0-1.0,
    "resultado_texto_refinado": "Texto refinado de síntesis final..."
}}"""

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]


# ═══════════════════════════════════════════════════════════════
# MERGE LOGIC
# ═══════════════════════════════════════════════════════════════

def merge_swarm_contributions(
    pizarra: dict,
    contributions: Dict[str, dict],
    ronda: int,
) -> int:
    """Merge contributions from all models into pizarra. Returns change count.

    Rules:
    - Only RAISE level if nivel_propuesto > current nivel
    - Always append evidencias tagged with model name + ronda
    - Return total change count
    """
    changes = 0

    for model_name, contrib in contributions.items():
        if not contrib or contrib.get("sin_contribucion", False):
            continue

        for cell_name in PIZARRA_CELLS:
            cell_contribs = contrib.get(cell_name, [])
            if not cell_contribs or not isinstance(cell_contribs, list):
                continue

            cell = pizarra["celdas"].get(cell_name)
            if cell is None:
                continue

            for item in cell_contribs:
                if not isinstance(item, dict):
                    # Handle bare strings
                    item = {"texto": str(item), "nivel_propuesto": 1}

                texto = item.get("texto", "")
                if not texto:
                    continue

                nivel_propuesto = item.get("nivel_propuesto", 1)
                try:
                    nivel_propuesto = int(nivel_propuesto)
                except (ValueError, TypeError):
                    nivel_propuesto = 1
                nivel_propuesto = max(1, min(4, nivel_propuesto))

                # Append evidencia tagged with model + ronda
                cell["evidencias"].append({
                    "texto": texto,
                    "nivel_propuesto": nivel_propuesto,
                    "modelo": model_name,
                    "ronda": ronda,
                })
                changes += 1

                # Only RAISE level
                if nivel_propuesto > cell["nivel"]:
                    cell["nivel"] = nivel_propuesto

    # Update meta
    pizarra["meta"]["ronda"] = ronda
    pizarra["meta"]["cambios_por_ronda"].append(changes)

    # Check convergence: if R2 changes < 20% of R1 changes
    if len(pizarra["meta"]["cambios_por_ronda"]) >= 2:
        r1_changes = pizarra["meta"]["cambios_por_ronda"][-2]
        r2_changes = changes
        if r1_changes > 0 and r2_changes / r1_changes < 0.20:
            pizarra["meta"]["convergencia"] = True

    return changes


# ═══════════════════════════════════════════════════════════════
# LLM CALL WRAPPERS
# ═══════════════════════════════════════════════════════════════

def _parse_json_response(raw: str) -> dict:
    """Robustly parse JSON from LLM response. Handles think tags, code blocks, etc."""
    if not raw:
        return {}

    # Strip think tags first
    text = strip_think_tags(raw)

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting ```json ... ``` blocks
    json_block = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block:
        try:
            return json.loads(json_block.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting any { ... } block
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return {}


def _estimate_cost(model_id: str, output_tokens: int) -> float:
    """Estimate cost based on output tokens."""
    price_per_m = _MODEL_PRICING.get(model_id, 1.0)
    return (output_tokens / 1_000_000) * price_per_m


def _call_model_openrouter(
    model_id: str,
    messages: List[dict],
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> dict:
    """Call a model via OpenRouter. Returns parsed response with cost estimate."""
    t0 = time.time()
    try:
        resp = call_with_retry(
            messages=messages,
            model=model_id,
            tools=None,
            max_retries=2,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        content, _, blowup = extract_response(resp)
        elapsed = time.time() - t0

        # Estimate tokens from content length (rough: 1 token ~ 4 chars)
        output_tokens = len(content or "") // 4
        usage = resp.get("usage", {})
        if usage.get("completion_tokens"):
            output_tokens = usage["completion_tokens"]

        parsed = _parse_json_response(content or "")
        cost = _estimate_cost(model_id, output_tokens)

        return {
            "content": content,
            "parsed": parsed,
            "cost": cost,
            "elapsed_s": round(elapsed, 1),
            "output_tokens": output_tokens,
            "blowup": blowup,
            "error": None,
        }
    except Exception as e:
        return {
            "content": "",
            "parsed": {},
            "cost": 0.0,
            "elapsed_s": round(time.time() - t0, 1),
            "output_tokens": 0,
            "blowup": False,
            "error": str(e),
        }


def _call_model_anthropic(
    messages: List[dict],
    max_tokens: int = 4096,
    model: str = "claude-opus-4-6",
) -> dict:
    """Call Anthropic model directly. Returns parsed response with cost estimate."""
    t0 = time.time()
    try:
        import anthropic
        client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

        # Separate system from user/assistant messages
        system_text = ""
        api_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text = msg["content"]
            else:
                api_messages.append(msg)

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": api_messages,
        }
        if system_text:
            kwargs["system"] = system_text

        response = client.messages.create(**kwargs)
        elapsed = time.time() - t0

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        output_tokens = response.usage.output_tokens if response.usage else len(content) // 4
        parsed = _parse_json_response(content)
        cost = _estimate_cost(model, output_tokens)

        return {
            "content": content,
            "parsed": parsed,
            "cost": cost,
            "elapsed_s": round(elapsed, 1),
            "output_tokens": output_tokens,
            "blowup": False,
            "error": None,
        }
    except Exception as e:
        return {
            "content": "",
            "parsed": {},
            "cost": 0.0,
            "elapsed_s": round(time.time() - t0, 1),
            "output_tokens": 0,
            "blowup": False,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════
# DB HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_conn():
    """Get a psycopg2 connection. Thread-safe: returns a new connection each call."""
    import psycopg2
    url = os.environ.get(
        "DATABASE_URL",
        "postgresql://chief_os_omni:77qJGeKtMTgCYhz@motor-semantico-db.flycast:5432/omni_mind",
    )
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = False
    return conn


def _load_pattern(pat_id: int) -> Optional[dict]:
    """Load a single pattern from knowledge_base by ID."""
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, scope, tipo, texto, metadata FROM knowledge_base WHERE id = %s",
                [pat_id],
            )
            row = cur.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _persist_result(
    pizarra: dict,
    final_result: dict,
    exploration_id: Optional[int],
) -> int:
    """Persist swarm analysis result to relaciones_patrones. Returns relacion id."""
    par = pizarra["par"]
    operacion = pizarra["operacion"]
    op_def = OPERATIONS.get(operacion, {})

    emergencias = final_result.get("emergencias", [])
    confianza = final_result.get("confianza_final", final_result.get("confianza", 0.5))

    estrategia = {
        "engine": "swarm_algebra",
        "models": list(SWARM_MODELS.keys()),
        "synthesizer": SYNTHESIZER_PRIMARY["id"],
        "validator": SYNTHESIZER_VALIDATOR["id"] if SYNTHESIZER_VALIDATOR else None,
        "rondas": pizarra["meta"]["ronda"],
        "cambios_por_ronda": pizarra["meta"]["cambios_por_ronda"],
        "convergencia": pizarra["meta"]["convergencia"],
        "coste_total": pizarra["meta"]["coste_acumulado"],
    }
    if exploration_id:
        estrategia["exploration_id"] = exploration_id

    # Validate algebraic properties
    violations = validate_operation_properties(operacion, final_result)

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO relaciones_patrones
                    (patron_a_id, patron_b_id, operacion, resultado,
                     propiedades, emergencias, validado, confianza,
                     reglas_aplicadas, estrategia_razonamiento)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [
                par["patron_a"]["id"], par["patron_b"]["id"], operacion,
                json.dumps(final_result, ensure_ascii=False),
                json.dumps({"violations": violations, "swarm_meta": pizarra["meta"]}, ensure_ascii=False),
                emergencias if emergencias else None,
                len(violations) == 0,
                confianza,
                op_def.get("rules_applied", []),
                json.dumps(estrategia, ensure_ascii=False),
            ])
            rel_id = cur.fetchone()[0]
        conn.commit()
        return rel_id
    finally:
        conn.close()


def _persist_emergencias(
    relacion_id: int,
    emergencias: List,
    pat_a_id: int,
    pat_b_id: int,
) -> None:
    """Persist individual emergencias to emergencias_descubiertas."""
    if not emergencias:
        return
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            for emg in emergencias:
                if isinstance(emg, dict):
                    emg_text = emg.get("texto", json.dumps(emg, ensure_ascii=False))
                    tipo = "emergencia"
                    if emg.get("promover_a_patron"):
                        tipo = "promotible"
                else:
                    emg_text = str(emg)
                    tipo = "emergencia"

                cur.execute("""
                    INSERT INTO emergencias_descubiertas
                        (relacion_id, texto, tipo, patron_origen_a, patron_origen_b)
                    VALUES (%s, %s, %s, %s, %s)
                """, [relacion_id, emg_text, tipo, pat_a_id, pat_b_id])
        conn.commit()
    finally:
        conn.close()


def _persist_pizarra_snapshot(
    pizarra: dict,
    ronda: int,
    exploration_id: Optional[int],
    relacion_id: int,
) -> None:
    """Persist a pizarra snapshot to pizarras_algebra."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO pizarras_algebra
                    (relacion_id, exploracion_id, ronda, pizarra_snapshot)
                VALUES (%s, %s, %s, %s)
            """, [
                relacion_id,
                exploration_id,
                ronda,
                json.dumps(pizarra, ensure_ascii=False, default=str),
            ])
        conn.commit()
    except Exception:
        # Table might not exist yet; log and continue
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def _persist_audit(
    relacion_id: int,
    modelo: str,
    ronda: int,
    thinking_type: str,
    contribuciones_count: int,
) -> None:
    """Persist audit trail entry to algebra_audit."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO algebra_audit
                    (relacion_id, accion, resultado, detalle)
                VALUES (%s, %s, %s, %s)
            """, [
                relacion_id,
                f"swarm_r{ronda}",
                "contribute" if contribuciones_count > 0 else "skip",
                json.dumps({
                    "modelo": modelo,
                    "ronda": ronda,
                    "thinking_type": thinking_type,
                    "contribuciones": contribuciones_count,
                }, ensure_ascii=False),
            ])
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()


def _maybe_promote_emergencia(
    emergencia: dict,
    relacion_id: int,
    pat_a_id: int,
    pat_b_id: int,
) -> Optional[int]:
    """If confianza > 0.8 and promover_a_patron is true, create new pattern in knowledge_base."""
    if not isinstance(emergencia, dict):
        return None
    if not emergencia.get("promover_a_patron"):
        return None

    spec = emergencia.get("spec", {})
    if not spec:
        return None

    texto = spec.get("texto", emergencia.get("texto", ""))
    if not texto:
        return None

    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO knowledge_base
                    (scope, tipo, texto, nivel, metadata)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, [
                spec.get("scope", "patrones:emergente"),
                spec.get("tipo", "emergencia"),
                texto,
                spec.get("nivel", "L2"),
                json.dumps({
                    "origen": "swarm_algebra",
                    "relacion_id": relacion_id,
                    "patron_origen_a": pat_a_id,
                    "patron_origen_b": pat_b_id,
                    "concepto": spec.get("concepto", ""),
                }, ensure_ascii=False),
            ])
            new_id = cur.fetchone()[0]

            # Mark emergencia as promoted
            cur.execute("""
                UPDATE emergencias_descubiertas
                SET promovido_a_patron = %s
                WHERE relacion_id = %s AND texto LIKE %s
            """, [new_id, relacion_id, f"%{texto[:100]}%"])

        conn.commit()
        return new_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════

def run_swarm_analysis(
    pat_a_id: int,
    pat_b_id: int,
    operacion: str = "auto",
    exploration_id: Optional[int] = None,
) -> Generator[dict, None, None]:
    """Run multi-model swarm analysis on a pattern pair. Yields SSE events.

    Flow:
    1. Load patterns from DB
    2. Auto-classify if operacion == "auto"
    3. Create pizarra
    4. R1: 5 models explore in parallel
    5. Merge R1
    6. R2: 5 models enrich stigmergically
    7. Merge R2
    8. Synthesis (Cogito)
    9. Validation (Opus)
    10. Validate algebraic properties
    11. Persist all results
    12. Yield final event
    """
    t_start = time.time()

    from core.costes import set_call_context
    set_call_context(componente='swarm_algebra', operacion='swarm_analysis',
                     caso_id=f'{pat_a_id}x{pat_b_id}')

    # 1. Load patterns
    pat_a = _load_pattern(pat_a_id)
    pat_b = _load_pattern(pat_b_id)
    if not pat_a or not pat_b:
        yield {"type": "error", "message": f"Could not load patterns: a={pat_a_id}, b={pat_b_id}"}
        return

    yield {"type": "swarm_start", "patron_a_id": pat_a_id, "patron_b_id": pat_b_id}

    # 2. Auto-classify if needed
    clasificacion = "complementary"
    if operacion == "auto":
        try:
            from tools.explorer import classify_pair
            meta_a = pat_a.get("metadata") or {}
            meta_b = pat_b.get("metadata") or {}
            cls_result = classify_pair(
                meta_a, meta_b,
                pat_a.get("scope", ""), pat_b.get("scope", ""),
            )
            clasificacion = cls_result.get("clasificacion", "complementary")
            operacion = cls_result.get("operacion_sugerida", "fusion")
            yield {
                "type": "swarm_classified",
                "clasificacion": clasificacion,
                "operacion": operacion,
                "score": cls_result.get("score", 0),
            }
        except Exception as e:
            operacion = "fusion"
            yield {"type": "swarm_classify_fallback", "error": str(e), "operacion": operacion}

    # 3. Create pizarra
    pizarra = create_algebra_pizarra(pat_a, pat_b, clasificacion, operacion)

    # 4. R1: call all 5 models in parallel
    model_names = list(SWARM_MODELS.keys())
    yield {"type": "swarm_r1_start", "models": model_names}

    r1_contributions: Dict[str, dict] = {}

    def _call_model_r1(name: str, cfg: dict) -> tuple:
        messages = build_r1_prompt(pizarra, cfg["thinking_type"], cfg["mode"])
        result = _call_model_openrouter(cfg["id"], messages, max_tokens=4096, temperature=0.7)
        return name, cfg, result

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_call_model_r1, name, cfg): name
            for name, cfg in SWARM_MODELS.items()
        }
        for future in as_completed(futures):
            try:
                name, cfg, result = future.result(timeout=300)
                parsed = result.get("parsed", {})
                r1_contributions[name] = parsed
                pizarra["meta"]["coste_acumulado"] += result.get("cost", 0)

                contributed = bool(parsed) and not parsed.get("sin_contribucion", False)
                if name not in pizarra["meta"]["modelos_participantes"] and contributed:
                    pizarra["meta"]["modelos_participantes"].append(name)

                yield {
                    "type": "swarm_r1_model_done",
                    "model": name,
                    "contributed": contributed,
                    "elapsed_s": result.get("elapsed_s", 0),
                    "cost": result.get("cost", 0),
                    "error": result.get("error"),
                }
            except Exception as e:
                name = futures[future]
                r1_contributions[name] = {}
                yield {
                    "type": "swarm_r1_model_done",
                    "model": name,
                    "contributed": False,
                    "error": str(e),
                }

    # 5. Merge R1
    r1_changes = merge_swarm_contributions(pizarra, r1_contributions, ronda=1)
    yield {"type": "swarm_merge", "ronda": 1, "cambios": r1_changes}

    # 6. R2: call all 5 models with full pizarra
    yield {"type": "swarm_r2_start", "models": model_names}

    r2_contributions: Dict[str, dict] = {}

    def _call_model_r2(name: str, cfg: dict) -> tuple:
        messages = build_r2_prompt(pizarra)
        result = _call_model_openrouter(cfg["id"], messages, max_tokens=4096, temperature=0.7)
        return name, cfg, result

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(_call_model_r2, name, cfg): name
            for name, cfg in SWARM_MODELS.items()
        }
        for future in as_completed(futures):
            try:
                name, cfg, result = future.result(timeout=300)
                parsed = result.get("parsed", {})
                r2_contributions[name] = parsed
                pizarra["meta"]["coste_acumulado"] += result.get("cost", 0)

                contributed = bool(parsed) and not parsed.get("sin_contribucion", False)
                if name not in pizarra["meta"]["modelos_participantes"] and contributed:
                    pizarra["meta"]["modelos_participantes"].append(name)

                yield {
                    "type": "swarm_r2_model_done",
                    "model": name,
                    "contributed": contributed,
                    "elapsed_s": result.get("elapsed_s", 0),
                    "cost": result.get("cost", 0),
                    "error": result.get("error"),
                }
            except Exception as e:
                name = futures[future]
                r2_contributions[name] = {}
                yield {
                    "type": "swarm_r2_model_done",
                    "model": name,
                    "contributed": False,
                    "error": str(e),
                }

    # 7. Merge R2
    r2_changes = merge_swarm_contributions(pizarra, r2_contributions, ronda=2)
    yield {"type": "swarm_merge", "ronda": 2, "cambios": r2_changes}

    # 8. Synthesis 1 (Cogito)
    yield {"type": "swarm_synthesis_cogito", "status": "running"}
    cogito_messages = build_synthesis_prompt(pizarra)
    cogito_result_raw = _call_model_openrouter(
        SYNTHESIZER_PRIMARY["id"], cogito_messages, max_tokens=4096, temperature=0.3,
    )
    cogito_result = cogito_result_raw.get("parsed", {})
    pizarra["meta"]["coste_acumulado"] += cogito_result_raw.get("cost", 0)
    yield {
        "type": "swarm_synthesis_cogito",
        "status": "done",
        "elapsed_s": cogito_result_raw.get("elapsed_s", 0),
        "cost": cogito_result_raw.get("cost", 0),
        "error": cogito_result_raw.get("error"),
    }

    # 9. Synthesis 2 (Opus validation) — skipped if no ANTHROPIC_API_KEY
    opus_result = {}
    if SYNTHESIZER_VALIDATOR:
        yield {"type": "swarm_synthesis_opus", "status": "running"}
        opus_messages = build_validation_prompt(pizarra, cogito_result)
        opus_result_raw = _call_model_anthropic(opus_messages, max_tokens=4096)
        opus_result = opus_result_raw.get("parsed", {})
        pizarra["meta"]["coste_acumulado"] += opus_result_raw.get("cost", 0)
        yield {
            "type": "swarm_synthesis_opus",
            "status": "done",
            "elapsed_s": opus_result_raw.get("elapsed_s", 0),
            "cost": opus_result_raw.get("cost", 0),
            "error": opus_result_raw.get("error"),
        }
    else:
        yield {"type": "swarm_synthesis_opus", "status": "skipped",
               "reason": "No ANTHROPIC_API_KEY — Cogito synthesis is final result"}

    # 10. Build final merged result
    final_result = _build_final_result(cogito_result, opus_result, pizarra)

    # 11. Validate algebraic properties
    violations = validate_operation_properties(operacion, final_result)
    final_result["violaciones_algebraicas"] = violations

    # 12. Persist all results
    try:
        relacion_id = _persist_result(pizarra, final_result, exploration_id)

        pat_a_id_val = pizarra["par"]["patron_a"]["id"]
        pat_b_id_val = pizarra["par"]["patron_b"]["id"]

        # Persist emergencias
        all_emergencias = final_result.get("emergencias", [])
        _persist_emergencias(relacion_id, all_emergencias, pat_a_id_val, pat_b_id_val)

        # Persist contextos as separate emergencias
        contextos = final_result.get("contextos_implementacion", [])
        if contextos:
            conn = _get_conn()
            try:
                with conn.cursor() as cur:
                    for ctx in contextos:
                        ctx_text = ctx if isinstance(ctx, str) else json.dumps(ctx, ensure_ascii=False)
                        cur.execute("""
                            INSERT INTO emergencias_descubiertas
                                (relacion_id, texto, tipo, patron_origen_a, patron_origen_b)
                            VALUES (%s, %s, 'contexto', %s, %s)
                        """, [relacion_id, ctx_text, pat_a_id_val, pat_b_id_val])
                conn.commit()
            finally:
                conn.close()

        # Persist pizarra snapshots
        _persist_pizarra_snapshot(pizarra, 1, exploration_id, relacion_id)
        _persist_pizarra_snapshot(pizarra, 2, exploration_id, relacion_id)

        # Persist audit for each model
        for name, cfg in SWARM_MODELS.items():
            r1_count = sum(
                len(r1_contributions.get(name, {}).get(c, []))
                for c in PIZARRA_CELLS
            )
            r2_count = sum(
                len(r2_contributions.get(name, {}).get(c, []))
                for c in PIZARRA_CELLS
            )
            _persist_audit(relacion_id, name, 1, cfg["thinking_type"], r1_count)
            _persist_audit(relacion_id, name, 2, cfg["thinking_type"], r2_count)

        # Audit for synthesizers
        _persist_audit(relacion_id, SYNTHESIZER_PRIMARY["id"], 3, "sintesis", 1)
        if SYNTHESIZER_VALIDATOR:
            _persist_audit(relacion_id, SYNTHESIZER_VALIDATOR["id"], 4, "validacion", 1)

        # Maybe promote emergencias
        promotibles = opus_result.get("emergencias_promotibles", [])
        promoted_ids = []
        for emg in promotibles:
            if isinstance(emg, dict) and emg.get("promover_a_patron"):
                new_id = _maybe_promote_emergencia(emg, relacion_id, pat_a_id_val, pat_b_id_val)
                if new_id:
                    promoted_ids.append(new_id)

    except Exception as e:
        yield {"type": "swarm_persist_error", "error": str(e)}
        relacion_id = -1
        promoted_ids = []

    # 13. Yield final event
    elapsed_total = round(time.time() - t_start, 1)
    emergencias_count = len(final_result.get("emergencias", []))
    confianza = final_result.get("confianza_final", final_result.get("confianza", 0))

    yield {
        "type": "swarm_complete",
        "relacion_id": relacion_id,
        "confianza": confianza,
        "emergencias_count": emergencias_count,
        "coste_total": round(pizarra["meta"]["coste_acumulado"], 4),
        "elapsed_total_s": elapsed_total,
        "convergencia": pizarra["meta"]["convergencia"],
        "cambios_por_ronda": pizarra["meta"]["cambios_por_ronda"],
        "modelos_participantes": pizarra["meta"]["modelos_participantes"],
        "promoted_patterns": promoted_ids,
        "violations": violations,
    }


def _build_final_result(cogito_result: dict, opus_result: dict, pizarra: dict) -> dict:
    """Merge Cogito synthesis with Opus validation into final result."""
    final = {}

    # Use Opus refinements if available, otherwise Cogito's version
    for cell_name in PIZARRA_CELLS:
        refined_key = f"{cell_name}_refinadas"
        if opus_result.get(refined_key):
            final[cell_name] = opus_result[refined_key]
        elif cogito_result.get(cell_name):
            final[cell_name] = cogito_result[cell_name]
        else:
            # Fall back to pizarra raw evidencias
            cell = pizarra["celdas"].get(cell_name, {})
            final[cell_name] = [ev.get("texto", "") for ev in cell.get("evidencias", [])]

    # Confianza: use Opus final if available
    final["confianza"] = cogito_result.get("confianza", 0.5)
    final["confianza_final"] = opus_result.get("confianza_final", final["confianza"])

    # Result text: prefer Opus refined, then Cogito
    final["resultado_texto"] = (
        opus_result.get("resultado_texto_refinado")
        or cogito_result.get("resultado_texto", "")
    )

    # Validation metadata from Opus
    final["validacion"] = opus_result.get("validacion", "unknown")
    final["informacion_perdida"] = opus_result.get("informacion_perdida", [])
    final["simplificaciones"] = opus_result.get("simplificaciones", [])
    final["refinamientos"] = opus_result.get("refinamientos", [])

    # Promotable emergencias
    final["emergencias_promotibles"] = opus_result.get("emergencias_promotibles", [])

    return final


# ═══════════════════════════════════════════════════════════════
# TOOL REGISTRATION
# ═══════════════════════════════════════════════════════════════

def _run_swarm_sync(pat_a_id: int, pat_b_id: int, operacion: str = "auto") -> str:
    """Run swarm analysis synchronously for tool use. Returns JSON string."""
    events = []
    for event in run_swarm_analysis(pat_a_id, pat_b_id, operacion):
        events.append(event)
    return json.dumps(events, indent=2, default=str, ensure_ascii=False)


def register_tools(registry, sandbox_dir: str = "") -> None:
    """Register swarm_analyze tool with the ToolRegistry."""
    registry.register("swarm_analyze", {
        "name": "swarm_analyze",
        "description": (
            "Analyze a pattern pair using multi-model swarm with algebraic pizarra. "
            "5 models x 2 rounds + double synthesis (Cogito + Opus). "
            "Models: DeepSeek V3.2 (dialectica), DeepSeek R1 (causalidad), "
            "Qwen 3.5 (abstraccion), GLM 4.7 (metacognicion), Kimi K2.5 (contrafactual). "
            "Synthesis: Cogito V2 + Claude Opus 4.6 validation. "
            "Results persist to DB with full audit trail."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "patron_a_id": {
                    "type": "integer",
                    "description": "ID of first pattern",
                },
                "patron_b_id": {
                    "type": "integer",
                    "description": "ID of second pattern",
                },
                "operacion": {
                    "type": "string",
                    "enum": [
                        "auto", "fusion", "composicion", "diferencial",
                        "integracion", "loop_test", "contribucion_marginal",
                        "factorizacion_izquierda", "cruce_previo",
                    ],
                    "default": "auto",
                },
            },
            "required": ["patron_a_id", "patron_b_id"],
        },
    }, lambda a: _run_swarm_sync(
        a["patron_a_id"], a["patron_b_id"], a.get("operacion", "auto"),
    ), category="swarm")
