"""Universidad I+D — Autonomous pattern exploration engine.

Uses MAESTRO v3 cognitive machinery (17 thinking types × 6 modes × 8 operations)
to autonomously discover relationships between patterns.

Flow: Classify → Select strategy → Execute algebra → Validate → Store → Report
"""

import os
import json
import time
from typing import Dict, Generator, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

from .algebra_rules import (
    OPERATIONS, CLASSIFICATION_TYPES, THINKING_TYPES, CONCEPTUAL_MODES,
    build_maestro_system_prompt, build_exploration_prompt,
    validate_operation_properties,
)


def _get_conn():
    from .database import _get_conn as db_conn
    return db_conn()


def _call_llm(prompt: str, system: str) -> str:
    """Call LLM via OpenRouter for algebra reasoning."""
    try:
        from core.api import call_with_retry, extract_response, TIER_CONFIG
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        model = TIER_CONFIG.get("tier2", "anthropic/claude-3.5-sonnet")
        resp = call_with_retry(messages, model, tools=None, max_retries=2)
        content, _, _ = extract_response(resp)
        return content or "{}"
    except Exception as e:
        return json.dumps({"error": str(e), "analisis": "LLM call failed"})


# ═══════════════════════════════════════════════════════════════
# STRUCTURAL CLASSIFIER (code puro, $0)
# ═══════════════════════════════════════════════════════════════

def classify_pair(meta_a: dict, meta_b: dict, scope_a: str, scope_b: str) -> Dict:
    """Classify the structural relationship between two patterns.
    Returns classification type and score. Pure code, no LLM."""

    concepts_a = set(meta_a.get("conceptos", []))
    concepts_b = set(meta_b.get("conceptos", []))
    dims_a = meta_a.get("dimensiones_valor", {})
    dims_b = meta_b.get("dimensiones_valor", {})

    shared = concepts_a & concepts_b
    exclusive_a = concepts_a - concepts_b
    exclusive_b = concepts_b - concepts_a
    total = len(concepts_a | concepts_b) or 1

    overlap_ratio = len(shared) / total

    # Cross-domain: same concepts but different scopes
    domain_a = scope_a.split(":")[-1] if ":" in scope_a else scope_a
    domain_b = scope_b.split(":")[-1] if ":" in scope_b else scope_b
    different_domain = domain_a != domain_b

    if different_domain and overlap_ratio > 0.3:
        return {
            "clasificacion": "cross_domain",
            "score": min(1.0, overlap_ratio + 0.2),
            "conceptos_compartidos": list(shared),
            "conceptos_exclusivos_a": list(exclusive_a),
            "conceptos_exclusivos_b": list(exclusive_b),
            "operacion_sugerida": "integracion",
        }

    # Redundant: very high overlap in same domain
    if overlap_ratio > 0.7:
        return {
            "clasificacion": "redundant",
            "score": overlap_ratio,
            "conceptos_compartidos": list(shared),
            "conceptos_exclusivos_a": list(exclusive_a),
            "conceptos_exclusivos_b": list(exclusive_b),
            "operacion_sugerida": "contribucion_marginal",
        }

    # Opposing: shared concepts but different value dimensions
    if shared and dims_a and dims_b:
        dim_keys_a = set(dims_a.keys())
        dim_keys_b = set(dims_b.keys())
        dim_overlap = dim_keys_a & dim_keys_b
        conflicts = 0
        for k in dim_overlap:
            if str(dims_a.get(k, "")) != str(dims_b.get(k, "")):
                conflicts += 1
        if conflicts > 0 and len(shared) > 0:
            return {
                "clasificacion": "opposing",
                "score": min(1.0, conflicts / max(len(dim_overlap), 1) * 0.8 + 0.2),
                "conceptos_compartidos": list(shared),
                "conceptos_exclusivos_a": list(exclusive_a),
                "conceptos_exclusivos_b": list(exclusive_b),
                "operacion_sugerida": "diferencial",
            }

    # Complementary: different concepts, compatible
    if exclusive_a and exclusive_b and overlap_ratio < 0.3:
        return {
            "clasificacion": "complementary",
            "score": min(1.0, (len(exclusive_a) + len(exclusive_b)) / total * 0.7),
            "conceptos_compartidos": list(shared),
            "conceptos_exclusivos_a": list(exclusive_a),
            "conceptos_exclusivos_b": list(exclusive_b),
            "operacion_sugerida": "fusion",
        }

    # Sequential: check algebraic properties for composition hints
    props_a = meta_a.get("propiedades_algebraicas", {})
    props_b = meta_b.get("propiedades_algebraicas", {})
    if props_a.get("factorizable_izq") or props_b.get("factorizable_der"):
        return {
            "clasificacion": "sequential",
            "score": 0.6,
            "conceptos_compartidos": list(shared),
            "conceptos_exclusivos_a": list(exclusive_a),
            "conceptos_exclusivos_b": list(exclusive_b),
            "operacion_sugerida": "composicion",
        }

    # Default: complementary with lower score
    return {
        "clasificacion": "complementary",
        "score": 0.3,
        "conceptos_compartidos": list(shared),
        "conceptos_exclusivos_a": list(exclusive_a),
        "conceptos_exclusivos_b": list(exclusive_b),
        "operacion_sugerida": "fusion",
    }


def classify_scope_pairs(scope_a: str, scope_b: str,
                         limit: int = 20) -> List[Dict]:
    """Classify all pairs between two scopes. Returns sorted by score."""
    import psycopg2.extras
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, scope, tipo, texto, metadata
                FROM knowledge_base
                WHERE scope = %s AND metadata IS NOT NULL
                ORDER BY relevancia DESC LIMIT 30
            """, [scope_a])
            patterns_a = cur.fetchall()

            cur.execute("""
                SELECT id, scope, tipo, texto, metadata
                FROM knowledge_base
                WHERE scope = %s AND metadata IS NOT NULL
                ORDER BY relevancia DESC LIMIT 30
            """, [scope_b])
            patterns_b = cur.fetchall()

        classifications = []
        for pa in patterns_a:
            for pb in patterns_b:
                if pa["id"] == pb["id"]:
                    continue
                meta_a = pa.get("metadata") or {}
                meta_b = pb.get("metadata") or {}
                cls = classify_pair(meta_a, meta_b, pa["scope"], pb["scope"])
                cls["patron_a_id"] = pa["id"]
                cls["patron_b_id"] = pb["id"]
                cls["patron_a_texto"] = pa["texto"][:100]
                cls["patron_b_texto"] = pb["texto"][:100]
                classifications.append(cls)

        # Sort by score descending, take top N
        classifications.sort(key=lambda x: x["score"], reverse=True)
        return classifications[:limit]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# EXPLORATION ENGINE
# ═══════════════════════════════════════════════════════════════

def run_exploration(
    scope_a: str,
    scope_b: str,
    max_pairs: int = 5,
    operations: Optional[List[str]] = None,
    mode: str = "fast",
) -> Generator:
    """Run autonomous exploration between two scopes. Yields SSE events.

    mode: "fast" = single model (original), "swarm" = 5 models + pizarra + double synthesis
    """
    import psycopg2.extras

    # 1. Create exploration session
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO exploraciones (scope_a, scope_b, config, estado)
                VALUES (%s, %s, %s, 'running')
                RETURNING id
            """, [scope_a, scope_b, json.dumps({
                "max_pairs": max_pairs,
                "operations": operations,
                "mode": mode,
            })])
            exploration_id = cur.fetchone()[0]
        conn.commit()
    finally:
        conn.close()

    yield {
        "type": "exploration_started",
        "exploration_id": exploration_id,
        "scope_a": scope_a,
        "scope_b": scope_b,
    }

    # 2. Classify pairs (code puro, $0)
    yield {"type": "phase", "phase": "classifying", "message": "Clasificando patrones estructuralmente..."}

    try:
        classifications = classify_scope_pairs(scope_a, scope_b, limit=max_pairs * 3)
    except Exception as e:
        yield {"type": "error", "message": f"Classification failed: {e}"}
        _finish_exploration(exploration_id, "failed", {})
        return

    if not classifications:
        yield {"type": "error", "message": "No pattern pairs found between scopes"}
        _finish_exploration(exploration_id, "failed", {})
        return

    # Store classifications
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            for cls in classifications:
                cur.execute("""
                    INSERT INTO clasificaciones_estructurales
                        (patron_a_id, patron_b_id, clasificacion, score,
                         conceptos_compartidos, conceptos_exclusivos_a,
                         conceptos_exclusivos_b, operacion_sugerida, exploracion_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, [
                    cls["patron_a_id"], cls["patron_b_id"],
                    cls["clasificacion"], cls["score"],
                    cls.get("conceptos_compartidos"),
                    cls.get("conceptos_exclusivos_a"),
                    cls.get("conceptos_exclusivos_b"),
                    cls.get("operacion_sugerida"),
                    exploration_id,
                ])
        conn.commit()
    finally:
        conn.close()

    # Group by classification type
    by_type = {}
    for cls in classifications:
        t = cls["clasificacion"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(cls)

    yield {
        "type": "classifications",
        "total": len(classifications),
        "by_type": {k: len(v) for k, v in by_type.items()},
    }

    # 3. Select top pairs to analyze (diversity: pick from each classification)
    selected = []
    for cls_type, pairs in by_type.items():
        n_from_type = max(1, max_pairs // len(by_type))
        selected.extend(pairs[:n_from_type])
    selected = selected[:max_pairs]

    yield {"type": "phase", "phase": "analyzing",
           "message": f"Analizando {len(selected)} pares con razonamiento MAESTRO..."}

    # 4. Execute algebra with reasoning strategies
    discoveries = []
    for i, pair in enumerate(selected):
        yield {
            "type": "analyzing_pair",
            "pair": i + 1,
            "total": len(selected),
            "clasificacion": pair["clasificacion"],
            "patron_a": pair["patron_a_texto"],
            "patron_b": pair["patron_b_texto"],
            "mode": mode,
        }

        try:
            if mode == "swarm":
                # Use multi-model swarm with pizarra
                from .swarm_algebra import run_swarm_analysis
                swarm_result = None
                for swarm_event in run_swarm_analysis(
                    pair["patron_a_id"], pair["patron_b_id"],
                    operacion=pair.get("operacion_sugerida", "auto"),
                    exploration_id=exploration_id,
                ):
                    yield swarm_event
                    if swarm_event.get("type") == "swarm_complete":
                        swarm_result = swarm_event
                if swarm_result:
                    discoveries.append(swarm_result)
            else:
                # Fast mode: single model analysis
                result = _analyze_pair(pair, exploration_id)
                if result:
                    discoveries.append(result)
                    yield {
                        "type": "discovery",
                        "pair": i + 1,
                        "clasificacion": pair["clasificacion"],
                        "operacion": result.get("operacion"),
                        "emergencias": result.get("emergencias", []),
                        "contextos": result.get("contextos_implementacion", []),
                        "confianza": result.get("confianza", 0),
                    }
        except Exception as e:
            yield {"type": "pair_error", "pair": i + 1, "error": str(e)}

    # 5. Finish
    summary = {
        "pairs_analyzed": len(selected),
        "discoveries": len(discoveries),
        "total_emergencias": sum(
            len(d.get("emergencias", [])) for d in discoveries
        ),
        "classifications_found": {k: len(v) for k, v in by_type.items()},
        "top_discoveries": discoveries[:5],
    }

    _finish_exploration(exploration_id, "completed", summary)

    yield {
        "type": "exploration_completed",
        "exploration_id": exploration_id,
        "summary": summary,
    }


def _analyze_pair(pair: dict, exploration_id: int) -> Optional[dict]:
    """Analyze a classified pair using MAESTRO reasoning strategy."""
    import psycopg2.extras

    cls_type = pair["clasificacion"]
    cls_def = CLASSIFICATION_TYPES.get(cls_type, {})
    strategy = cls_def.get("reasoning_strategy", {})
    thinking = strategy.get("thinking", "sintesis")
    mode = strategy.get("mode", "ANALIZAR")
    operation = pair.get("operacion_sugerida", cls_def.get("default_operation", "fusion"))

    # Load full patterns
    conn = _get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, scope, tipo, texto, metadata
                FROM knowledge_base WHERE id IN (%s, %s)
            """, [pair["patron_a_id"], pair["patron_b_id"]])
            rows = cur.fetchall()
    finally:
        conn.close()

    if len(rows) < 2:
        return None

    patterns = {r["id"]: r for r in rows}
    pat_a = patterns.get(pair["patron_a_id"], rows[0])
    pat_b = patterns.get(pair["patron_b_id"], rows[1])
    meta_a = pat_a.get("metadata") or {}
    meta_b = pat_b.get("metadata") or {}

    # Build prompts with MAESTRO reasoning
    system_prompt = build_maestro_system_prompt(thinking_type=thinking, mode=mode)
    user_prompt = build_exploration_prompt(cls_type, pat_a, pat_b, meta_a, meta_b)

    # Call LLM
    llm_result = _call_llm(user_prompt, system_prompt)

    # Parse result
    try:
        result_data = json.loads(llm_result) if llm_result.strip().startswith("{") else {
            "analisis": llm_result, "emergencias": [],
        }
    except json.JSONDecodeError:
        result_data = {"analisis": llm_result, "emergencias": []}

    # Validate algebraic properties
    violations = validate_operation_properties(operation, result_data)
    result_data["violaciones_algebraicas"] = violations

    estrategia = {
        "thinking_type": thinking,
        "mode": mode,
        "classification": cls_type,
    }

    # Persist to relaciones_patrones
    emergencias = result_data.get("emergencias", [])
    confianza = result_data.get("confianza", 0.5)
    op_def = OPERATIONS.get(operation, {})
    reglas = op_def.get("rules_applied", [])

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
                pair["patron_a_id"], pair["patron_b_id"], operation,
                json.dumps(result_data, ensure_ascii=False),
                json.dumps({"violations": violations}, ensure_ascii=False),
                emergencias if emergencias else None,
                len(violations) == 0,
                confianza,
                reglas,
                json.dumps(estrategia, ensure_ascii=False),
            ])
            rel_id = cur.fetchone()[0]

            # Store emergencias individually
            for emg in emergencias:
                emg_text = emg if isinstance(emg, str) else json.dumps(emg, ensure_ascii=False)
                cur.execute("""
                    INSERT INTO emergencias_descubiertas
                        (relacion_id, texto, tipo, patron_origen_a, patron_origen_b)
                    VALUES (%s, %s, 'emergencia', %s, %s)
                """, [rel_id, emg_text, pair["patron_a_id"], pair["patron_b_id"]])

            # Store contextos as emergencias of type 'contexto'
            for ctx in result_data.get("contextos_implementacion", []):
                ctx_text = ctx if isinstance(ctx, str) else json.dumps(ctx, ensure_ascii=False)
                cur.execute("""
                    INSERT INTO emergencias_descubiertas
                        (relacion_id, texto, tipo, patron_origen_a, patron_origen_b)
                    VALUES (%s, %s, 'contexto', %s, %s)
                """, [rel_id, ctx_text, pair["patron_a_id"], pair["patron_b_id"]])

            # Audit trail
            cur.execute("""
                INSERT INTO algebra_audit
                    (relacion_id, accion, resultado, detalle)
                VALUES (%s, 'exploration', %s, %s)
            """, [
                rel_id,
                "pass" if not violations else "warning",
                json.dumps({
                    "exploration_id": exploration_id,
                    "strategy": estrategia,
                    "violations": violations,
                }, ensure_ascii=False),
            ])

        conn.commit()
    finally:
        conn.close()

    result_data["relacion_id"] = rel_id
    result_data["operacion"] = operation
    result_data["estrategia"] = estrategia
    return result_data


def _finish_exploration(exploration_id: int, estado: str, resultados: dict):
    """Mark exploration as finished."""
    conn = _get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE exploraciones
                SET estado = %s, resultados = %s, finished_at = NOW()
                WHERE id = %s
            """, [estado, json.dumps(resultados, ensure_ascii=False), exploration_id])
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# TOOL: Get discoveries
# ═══════════════════════════════════════════════════════════════

def tool_get_discoveries(limit: int = 20, tipo: str = "") -> str:
    """Get recent discoveries (emergencias) from pattern exploration."""
    import psycopg2.extras
    conn = _get_conn()
    try:
        conditions = ["1=1"]
        params = []
        if tipo:
            conditions.append("e.tipo = %s")
            params.append(tipo)

        params.append(limit)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT e.id, e.texto, e.tipo, e.promovido_a_patron, e.created_at,
                       r.operacion, r.estrategia_razonamiento,
                       ka.texto AS patron_a_texto, ka.scope AS patron_a_scope,
                       kb.texto AS patron_b_texto, kb.scope AS patron_b_scope
                FROM emergencias_descubiertas e
                LEFT JOIN relaciones_patrones r ON e.relacion_id = r.id
                LEFT JOIN knowledge_base ka ON e.patron_origen_a = ka.id
                LEFT JOIN knowledge_base kb ON e.patron_origen_b = kb.id
                WHERE {' AND '.join(conditions)}
                ORDER BY e.created_at DESC
                LIMIT %s
            """, params)
            rows = cur.fetchall()

        if not rows:
            return "No discoveries found yet. Run an exploration first."

        return json.dumps(rows, indent=2, default=str, ensure_ascii=False)
    finally:
        conn.close()


def tool_get_classifications(scope_a: str = "", scope_b: str = "",
                             limit: int = 20) -> str:
    """Get structural classifications between pattern pairs."""
    import psycopg2.extras
    conn = _get_conn()
    try:
        conditions = ["1=1"]
        params = []

        if scope_a:
            conditions.append("""
                patron_a_id IN (SELECT id FROM knowledge_base WHERE scope = %s)
            """)
            params.append(scope_a)
        if scope_b:
            conditions.append("""
                patron_b_id IN (SELECT id FROM knowledge_base WHERE scope = %s)
            """)
            params.append(scope_b)

        params.append(limit)

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT c.*, ka.texto AS pat_a_texto, kb.texto AS pat_b_texto,
                       ka.scope AS scope_a, kb.scope AS scope_b
                FROM clasificaciones_estructurales c
                LEFT JOIN knowledge_base ka ON c.patron_a_id = ka.id
                LEFT JOIN knowledge_base kb ON c.patron_b_id = kb.id
                WHERE {' AND '.join(conditions)}
                ORDER BY c.score DESC
                LIMIT %s
            """, params)
            rows = cur.fetchall()

        if not rows:
            return "No classifications found. Run an exploration first."

        # Summary
        by_type = {}
        for r in rows:
            t = r["clasificacion"]
            if t not in by_type:
                by_type[t] = 0
            by_type[t] += 1

        result = {
            "total": len(rows),
            "by_type": by_type,
            "classifications": [{
                "id": r["id"],
                "clasificacion": r["clasificacion"],
                "score": r["score"],
                "patron_a": r["pat_a_texto"][:80] if r.get("pat_a_texto") else "",
                "patron_b": r["pat_b_texto"][:80] if r.get("pat_b_texto") else "",
                "scope_a": r.get("scope_a", ""),
                "scope_b": r.get("scope_b", ""),
                "conceptos_compartidos": r.get("conceptos_compartidos", []),
                "operacion_sugerida": r.get("operacion_sugerida"),
                "analizado": r.get("analizado", False),
            } for r in rows],
        }
        return json.dumps(result, indent=2, default=str, ensure_ascii=False)
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# TOOL REGISTRATION
# ═══════════════════════════════════════════════════════════════

def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    """Register Universidad I+D exploration tools."""

    registry.register("explore_patterns", {
        "name": "explore_patterns",
        "description": (
            "Run autonomous exploration between two pattern scopes. "
            "Classifies pairs structurally (complementary, sequential, opposing, cross-domain, redundant), "
            "selects reasoning strategy (thinking type × conceptual mode × operation), "
            "executes MAESTRO v3 algebra, validates properties, and stores discoveries. "
            "Use mode='swarm' for multi-model analysis (5 models + pizarra + double synthesis). "
            "Available scopes: patrones:maestro, patrones:database, patrones:ia, "
            "patrones:distribuidos, patrones:software, patrones:invariantes, "
            "patrones:enjambre, patrones:semillas, patrones:frontend, patrones:api, "
            "patrones:distributed_systems, patrones:cognitive_science, patrones:game_theory, "
            "patrones:complexity_science, patrones:information_theory, patrones:control_theory, "
            "patrones:category_theory, etc."
        ),
        "parameters": {"type": "object", "properties": {
            "scope_a": {"type": "string", "description": "First scope (e.g. 'patrones:maestro')"},
            "scope_b": {"type": "string", "description": "Second scope (e.g. 'patrones:database')"},
            "max_pairs": {"type": "integer", "description": "Max pairs to analyze (default 5, max 10)"},
            "mode": {"type": "string", "enum": ["fast", "swarm"], "description": "fast=single model, swarm=5 models + pizarra (default: fast)"},
        }, "required": ["scope_a", "scope_b"]},
    }, lambda a: json.dumps(list(_run_explore_sync(
        a["scope_a"], a["scope_b"], min(a.get("max_pairs", 5), 10),
        mode=a.get("mode", "fast"),
    )), default=str, ensure_ascii=False),
    category="explorer")

    registry.register("get_discoveries", {
        "name": "get_discoveries",
        "description": "Get recent discoveries (emergencias, contextos, cruces) from pattern exploration.",
        "parameters": {"type": "object", "properties": {
            "limit": {"type": "integer", "description": "Max results (default 20)"},
            "tipo": {"type": "string", "description": "Filter: 'emergencia', 'cruce', 'contexto', 'isomorfismo'"},
        }, "required": []},
    }, lambda a: tool_get_discoveries(a.get("limit", 20), a.get("tipo", "")),
    category="explorer")

    registry.register("get_classifications", {
        "name": "get_classifications",
        "description": "Get structural classifications detected between pattern pairs. Shows complementary, sequential, opposing, cross-domain relationships.",
        "parameters": {"type": "object", "properties": {
            "scope_a": {"type": "string", "description": "Filter by scope A"},
            "scope_b": {"type": "string", "description": "Filter by scope B"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        }, "required": []},
    }, lambda a: tool_get_classifications(
        a.get("scope_a", ""), a.get("scope_b", ""), a.get("limit", 20)
    ), category="explorer")


def _run_explore_sync(scope_a: str, scope_b: str, max_pairs: int,
                      mode: str = "fast") -> list:
    """Run exploration synchronously for tool use. Returns list of events."""
    events = []
    for event in run_exploration(scope_a, scope_b, max_pairs, mode=mode):
        events.append(event)
    return events


# Generator import for type hint
from typing import Generator
