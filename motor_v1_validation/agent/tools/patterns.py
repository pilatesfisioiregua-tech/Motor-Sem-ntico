"""Pattern algebra tools — search, compose, fuse, and analyze patterns."""

import os
import json
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import ToolRegistry


def _get_conn():
    from .database import _get_conn as db_conn
    return db_conn()


def tool_search_patterns(query: str, scope: str = "", tipo: str = "",
                         nivel: str = "", limit: int = 10) -> str:
    """Search patterns by text + filters in knowledge_base."""
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            conditions = ["scope LIKE 'patrones:%'"]
            params = []

            if query:
                conditions.append("(texto ILIKE %s OR scope ILIKE %s)")
                params.extend([f"%{query}%", f"%{query}%"])

            if scope:
                conditions.append("scope = %s")
                params.append(scope)

            if tipo:
                conditions.append("tipo = %s")
                params.append(tipo)

            if nivel:
                conditions.append("nivel = %s")
                params.append(nivel)

            where = " AND ".join(conditions)
            params.append(limit)

            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(f"""
                    SELECT id, scope, tipo, nivel, texto, documento, seccion, metadata,
                           created_at
                    FROM knowledge_base
                    WHERE {where}
                    ORDER BY relevancia DESC, created_at DESC
                    LIMIT %s
                """, params)
                rows = cur.fetchall()

            if not rows:
                return f"No patterns found for query='{query}' scope='{scope}' tipo='{tipo}'"

            return json.dumps(rows, indent=2, default=str, ensure_ascii=False)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_search_concepts(concept: str, limit: int = 15) -> str:
    """Search patterns by concept in metadata->'conceptos'. Cross-domain discovery."""
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, scope, tipo, nivel, texto, documento, seccion, metadata
                    FROM knowledge_base
                    WHERE scope LIKE 'patrones:%%'
                      AND (
                          metadata->'conceptos' ? %s
                          OR texto ILIKE %s
                      )
                    ORDER BY relevancia DESC
                    LIMIT %s
                """, [concept, f"%{concept}%", limit])
                rows = cur.fetchall()

            if not rows:
                return f"No patterns found with concept '{concept}'"

            # Group by scope for cross-domain view
            by_scope = {}
            for r in rows:
                s = r.get("scope", "unknown")
                if s not in by_scope:
                    by_scope[s] = []
                by_scope[s].append({
                    "id": r["id"],
                    "tipo": r["tipo"],
                    "texto": r["texto"][:200],
                    "metadata": r.get("metadata", {}),
                })

            result = {
                "concept": concept,
                "total_matches": len(rows),
                "domains": len(by_scope),
                "by_scope": by_scope,
            }
            return json.dumps(result, indent=2, default=str, ensure_ascii=False)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_pattern_algebra(patron_a_id: int, patron_b_id: int,
                         operacion: str) -> str:
    """Calculate fusion/composition/differential between two patterns.

    Operations (MAESTRO v3 algebra):
    - fusion: Two patterns in parallel on same problem -> complementary perspectives
    - composicion: Output of A feeds into B -> sequential mechanism
    - diferencial: What A does that B structurally cannot
    """
    VALID_OPS = ("fusion", "composicion", "diferencial", "integracion",
                 "loop_test", "contribucion_marginal",
                 "factorizacion_izquierda", "cruce_previo")
    if operacion not in VALID_OPS:
        return f"ERROR: operacion must be one of: {', '.join(VALID_OPS)}"

    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            # Load both patterns
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, scope, tipo, texto, metadata
                    FROM knowledge_base WHERE id IN (%s, %s)
                """, [patron_a_id, patron_b_id])
                rows = cur.fetchall()

            if len(rows) < 2:
                return f"ERROR: Could not find both patterns (ids: {patron_a_id}, {patron_b_id})"

            patterns = {r["id"]: r for r in rows}
            pat_a = patterns.get(patron_a_id, rows[0])
            pat_b = patterns.get(patron_b_id, rows[1])

            meta_a = pat_a.get("metadata", {}) or {}
            meta_b = pat_b.get("metadata", {}) or {}

            # Build algebra prompt
            prompt_builders = {
                "fusion": _build_fusion_prompt,
                "composicion": _build_composition_prompt,
                "diferencial": _build_differential_prompt,
                "integracion": _build_integration_prompt,
                "loop_test": _build_loop_test_prompt,
                "contribucion_marginal": _build_marginal_contribution_prompt,
                "factorizacion_izquierda": _build_left_factorization_prompt,
                "cruce_previo": _build_right_crossing_prompt,
            }
            builder = prompt_builders.get(operacion, _build_fusion_prompt)
            prompt = builder(pat_a, pat_b, meta_a, meta_b)

            # Call LLM (Sonnet via OpenRouter)
            llm_result = _call_llm_for_algebra(prompt)

            # Parse result
            try:
                result_data = json.loads(llm_result) if llm_result.strip().startswith("{") else {
                    "analisis": llm_result,
                    "emergencias": [],
                }
            except json.JSONDecodeError:
                result_data = {"analisis": llm_result, "emergencias": []}

            # Validate algebraic properties (code puro)
            from .algebra_rules import validate_operation_properties, OPERATIONS
            violations = validate_operation_properties(operacion, result_data)
            result_data["violaciones_algebraicas"] = violations

            op_def = OPERATIONS.get(operacion, {})
            propiedades = {
                "symbol": op_def.get("symbol", ""),
                "form": op_def.get("form", ""),
                "properties_checked": op_def.get("properties", {}),
                "violations": violations,
            }

            # Persist to relaciones_patrones
            emergencias = result_data.get("emergencias", [])
            confianza = result_data.get("confianza", 0.5)
            conn2 = _get_conn()
            try:
                with conn2.cursor() as cur:
                    cur.execute("""
                        INSERT INTO relaciones_patrones
                            (patron_a_id, patron_b_id, operacion, resultado,
                             propiedades, emergencias, validado, confianza,
                             reglas_aplicadas)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, [
                        patron_a_id, patron_b_id, operacion,
                        json.dumps(result_data, ensure_ascii=False),
                        json.dumps(propiedades, ensure_ascii=False),
                        emergencias if emergencias else None,
                        len(violations) == 0,
                        confianza,
                        op_def.get("rules_applied", []),
                    ])
                    rel_id = cur.fetchone()[0]
                conn2.commit()
            finally:
                conn2.close()

            output = {
                "relacion_id": rel_id,
                "operacion": operacion,
                "patron_a": {"id": pat_a["id"], "scope": pat_a["scope"], "texto": pat_a["texto"][:100]},
                "patron_b": {"id": pat_b["id"], "scope": pat_b["scope"], "texto": pat_b["texto"][:100]},
                "resultado": result_data,
            }
            return json.dumps(output, indent=2, default=str, ensure_ascii=False)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_pattern_transversal(concept_or_query: str) -> str:
    """Find cross-domain applications of a concept. Identifies isomorphisms between domains."""
    try:
        import psycopg2.extras
        conn = _get_conn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Search by concept in metadata + text
                cur.execute("""
                    SELECT id, scope, tipo, nivel, texto, metadata
                    FROM knowledge_base
                    WHERE scope LIKE 'patrones:%%'
                      AND (
                          metadata->'conceptos' ? %s
                          OR metadata->'isomorfismos' @> '[{"dominio_origen": "%s"}]'::jsonb
                          OR metadata->'isomorfismos' @> '[{"dominio_destino": "%s"}]'::jsonb
                          OR texto ILIKE %s
                      )
                    ORDER BY relevancia DESC
                    LIMIT 30
                """, [concept_or_query, concept_or_query, concept_or_query,
                      f"%{concept_or_query}%"])
                rows = cur.fetchall()

            if not rows:
                return f"No cross-domain patterns found for '{concept_or_query}'"

            # Group by domain/scope
            domains = {}
            for r in rows:
                scope = r.get("scope", "unknown")
                domain = scope.split(":")[-1] if ":" in scope else scope
                if domain not in domains:
                    domains[domain] = []
                meta = r.get("metadata", {}) or {}
                domains[domain].append({
                    "id": r["id"],
                    "tipo": r["tipo"],
                    "texto": r["texto"][:150],
                    "conceptos": meta.get("conceptos", []),
                    "isomorfismos": meta.get("isomorfismos", []),
                })

            # Identify potential bridges
            all_concepts = set()
            for patterns in domains.values():
                for p in patterns:
                    all_concepts.update(p.get("conceptos", []))

            # Find concepts that appear in multiple domains
            concept_domains = {}
            for domain, patterns in domains.items():
                for p in patterns:
                    for c in p.get("conceptos", []):
                        if c not in concept_domains:
                            concept_domains[c] = set()
                        concept_domains[c].add(domain)

            bridge_concepts = {
                c: list(ds) for c, ds in concept_domains.items()
                if len(ds) > 1
            }

            result = {
                "query": concept_or_query,
                "total_patterns": len(rows),
                "domains_found": list(domains.keys()),
                "bridge_concepts": bridge_concepts,
                "patterns_by_domain": {d: ps[:5] for d, ps in domains.items()},
            }
            return json.dumps(result, indent=2, default=str, ensure_ascii=False)
        finally:
            conn.close()
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


# ---- LLM helpers for algebra ---- #

def _build_fusion_prompt(pat_a: dict, pat_b: dict,
                         meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: FUSION (A|B) — Dos patrones en paralelo sobre mismo problema.

PATRON A ({pat_a['scope']}):
{pat_a['texto'][:500]}
Conceptos: {meta_a.get('conceptos', [])}
Dimensiones: {json.dumps(meta_a.get('dimensiones_valor', {}), ensure_ascii=False)}

PATRON B ({pat_b['scope']}):
{pat_b['texto'][:500]}
Conceptos: {meta_b.get('conceptos', [])}
Dimensiones: {json.dumps(meta_b.get('dimensiones_valor', {}), ensure_ascii=False)}

Analiza la fusion:
1. Perspectivas complementarias que aporta cada patron
2. Tensiones o conflictos entre ellos
3. Emergencias: insights que solo aparecen al combinarlos
4. Aplicabilidad: donde usar esta fusion

Responde en JSON:
{{"analisis": "...", "complementariedades": [...], "tensiones": [...], "emergencias": [...], "aplicabilidad": [...]}}"""


def _build_composition_prompt(pat_a: dict, pat_b: dict,
                              meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: COMPOSICION A->B — Output de A es input de B.

PATRON A ({pat_a['scope']}):
{pat_a['texto'][:500]}
Conceptos: {meta_a.get('conceptos', [])}

PATRON B ({pat_b['scope']}):
{pat_b['texto'][:500]}
Conceptos: {meta_b.get('conceptos', [])}

Analiza la composicion A->B:
1. Como el output de A alimenta a B
2. Es conmutativa? (B->A produce resultado diferente?)
3. Emergencias del pipeline
4. Donde aplicar esta composicion

Responde en JSON:
{{"analisis": "...", "flujo": "...", "conmutativa": true/false, "emergencias": [...], "aplicabilidad": [...]}}"""


def _build_differential_prompt(pat_a: dict, pat_b: dict,
                               meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: DIFERENCIAL A-B — Que hace A que B estructuralmente NO puede.

PATRON A ({pat_a['scope']}):
{pat_a['texto'][:500]}
Conceptos: {meta_a.get('conceptos', [])}
Dimensiones: {json.dumps(meta_a.get('dimensiones_valor', {}), ensure_ascii=False)}

PATRON B ({pat_b['scope']}):
{pat_b['texto'][:500]}
Conceptos: {meta_b.get('conceptos', [])}
Dimensiones: {json.dumps(meta_b.get('dimensiones_valor', {}), ensure_ascii=False)}

Analiza el diferencial A-B:
1. Capacidades exclusivas de A (que B no tiene)
2. Trade-offs estructurales
3. Cuando elegir A sobre B
4. Complementos: que necesitaria B para cubrir el gap

Responde en JSON:
{{"analisis": "...", "exclusivas_a": [...], "tradeoffs": [...], "cuando_a": "...", "gap_b": [...], "emergencias": [...]}}"""


def _build_integration_prompt(pat_a: dict, pat_b: dict,
                              meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: INTEGRACION ∫ — Encontrar cruces y emergencias entre patrones.

PATRON A ({pat_a['scope']}):
{pat_a['texto'][:500]}
Conceptos: {meta_a.get('conceptos', [])}

PATRON B ({pat_b['scope']}):
{pat_b['texto'][:500]}
Conceptos: {meta_b.get('conceptos', [])}

Analiza la integracion:
1. Cruces: donde se intersectan los patrones
2. Emergencias: propiedades que solo aparecen al sumarlos
3. Conversacion pendiente: que queda sin decir (Regla 12)
4. Contextos de implementacion: donde aplicar lo integrado

Responde en JSON:
{{"analisis": "...", "cruces": [...], "emergencias": [...], "conversacion_pendiente": "...", "contextos_implementacion": [...], "confianza": 0.0-1.0}}"""


def _build_loop_test_prompt(pat_a: dict, pat_b: dict,
                            meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: LOOP TEST →→ — Segunda pasada sobre resultado previo (Regla 7).

El output de la primera pasada se convierte en input de mayor densidad (Regla 13).
NUNCA hacer tercera pasada (Regla 8: n=3 no justifica coste).

RESULTADO DE PRIMERA PASADA (patron A):
{pat_a['texto'][:500]}

CONTEXTO ORIGINAL (patron B):
{pat_b['texto'][:500]}

Ejecuta segunda pasada:
1. Que nueva informacion emerge al re-examinar?
2. Que se confirma y que se refina?
3. Densidad: el output es mas denso que el input?
4. Saturacion: hay valor genuino o es repeticion?

Responde en JSON:
{{"analisis": "...", "refinamientos": [...], "emergencias": [...], "densidad_ganada": true/false, "saturado": true/false, "confianza": 0.0-1.0}}"""


def _build_marginal_contribution_prompt(pat_a: dict, pat_b: dict,
                                         meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: CONTRIBUCION MARGINAL Δ — Medir valor añadido de B sobre A.

Pregunta: si ya tenemos A, cuanto aporta B? Es marginal (<10% ganancia)?
Regla 3: >6 patrones = rendimiento decreciente.

PATRON BASE A ({pat_a['scope']}):
{pat_a['texto'][:500]}
Conceptos: {meta_a.get('conceptos', [])}

PATRON CANDIDATO B ({pat_b['scope']}):
{pat_b['texto'][:500]}
Conceptos: {meta_b.get('conceptos', [])}

Analiza contribucion marginal:
1. Que aporta B que A no tiene?
2. Cuanta ganancia porcentual estimas?
3. Es marginal (<10%) o significativa?
4. Justifica el coste de añadir B?

Responde en JSON:
{{"analisis": "...", "aporta": [...], "ganancia_estimada": 0.0-1.0, "es_marginal": true/false, "justifica_coste": true/false, "emergencias": [...], "confianza": 0.0-1.0}}"""


def _build_left_factorization_prompt(pat_a: dict, pat_b: dict,
                                      meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: FACTORIZACION IZQUIERDA A→(B|C) — Medir perdida emergente.

Regla 9: A→(B|C) pierde ~30% del valor emergente respecto a (A→B)|(A→C).
Aceptable si B|C no estan en top 5 por importancia.

PATRON A (input comun) ({pat_a['scope']}):
{pat_a['texto'][:500]}

PATRON B|C (paralelo) ({pat_b['scope']}):
{pat_b['texto'][:500]}

Analiza factorizacion izquierda:
1. Que se pierde al factorizar (valor emergente)?
2. Estimacion de perdida porcentual
3. Es aceptable para este caso?
4. Que alternativa seria mejor?

Responde en JSON:
{{"analisis": "...", "perdida_estimada": 0.0-1.0, "emergent_loss_acknowledged": true, "aceptable": true/false, "alternativa": "...", "emergencias": [...], "confianza": 0.0-1.0}}"""


def _build_right_crossing_prompt(pat_a: dict, pat_b: dict,
                                  meta_a: dict, meta_b: dict) -> str:
    return f"""OPERACION: CRUCE PREVIO (B|C)→A — Verificar irreducibilidad (Regla 10).

REGLA CRITICA: (B|C)→A NUNCA se factoriza. El valor del cruce previo es IRREDUCIBLE.
La vista conjunta de B|C sobre A produce insights que ni B→A ni C→A pueden dar por separado.

PATRON B|C (vista conjunta) ({pat_a['scope']}):
{pat_a['texto'][:500]}

PATRON A (destino) ({pat_b['scope']}):
{pat_b['texto'][:500]}

Analiza cruce previo:
1. Que insight produce la vista conjunta que es irreducible?
2. Por que no se puede factorizar?
3. Que se perderia si se intentara separar?
4. Contextos donde este cruce es critico

Responde en JSON:
{{"analisis": "...", "insight_irreducible": "...", "factorizable": false, "perdida_si_factoriza": "...", "contextos_implementacion": [...], "emergencias": [...], "confianza": 0.0-1.0}}"""


def _call_llm_for_algebra(prompt: str) -> str:
    """Call LLM for algebra calculation via OpenRouter with MAESTRO v3 rules."""
    try:
        from core.api import call_with_retry, extract_response
        from .algebra_rules import build_maestro_system_prompt
        messages = [
            {"role": "system", "content": build_maestro_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        # Use tier2 (mid-range) for algebra
        from core.api import TIER_CONFIG
        model = TIER_CONFIG.get("tier2", "anthropic/claude-3.5-sonnet")
        resp = call_with_retry(messages, model, tools=None, max_retries=2)
        content, _, _ = extract_response(resp)
        return content or "{}"
    except Exception as e:
        return json.dumps({"error": str(e), "analisis": "LLM call failed"})


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("search_patterns", {
        "name": "search_patterns",
        "description": "Search patterns in the University I+D repository. Filters by scope (patrones:maestro, patrones:database, patrones:ia, etc.), tipo, nivel. Returns patterns with metadata.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Text to search for in pattern content"},
            "scope": {"type": "string", "description": "Filter by scope (e.g. 'patrones:maestro', 'patrones:database')"},
            "tipo": {"type": "string", "description": "Filter by type (arquitectura, mecanismo, algebra, invariante, principio, etc.)"},
            "nivel": {"type": "string", "description": "Filter by level (L0=invariant, L1=stable, L2=variable, ext=external)"},
            "limit": {"type": "integer", "description": "Max results (default 10)"},
        }, "required": ["query"]}
    }, lambda a: tool_search_patterns(
        a["query"], a.get("scope", ""), a.get("tipo", ""),
        a.get("nivel", ""), a.get("limit", 10)
    ), category="patterns")

    registry.register("search_concepts", {
        "name": "search_concepts",
        "description": "Search patterns by concept across all domains. Finds patterns sharing a concept in different scopes — enables cross-domain discovery and abduction.",
        "parameters": {"type": "object", "properties": {
            "concept": {"type": "string", "description": "Concept to search (e.g. 'feedback_positivo', 'autoorganización', 'coordinación')"},
            "limit": {"type": "integer", "description": "Max results (default 15)"},
        }, "required": ["concept"]}
    }, lambda a: tool_search_concepts(a["concept"], a.get("limit", 15)),
    category="patterns")

    registry.register("pattern_algebra", {
        "name": "pattern_algebra",
        "description": "Calculate algebraic operations between two patterns (MAESTRO v3 §3.2). "
                       "8 operations: fusion (parallel), composicion (sequential), diferencial (exclusive capabilities), "
                       "integracion (crossings), loop_test (2nd pass), contribucion_marginal (added value), "
                       "factorizacion_izquierda (A→B|C ~30% loss), cruce_previo (B|C→A irreducible).",
        "parameters": {"type": "object", "properties": {
            "patron_a_id": {"type": "integer", "description": "ID of first pattern in knowledge_base"},
            "patron_b_id": {"type": "integer", "description": "ID of second pattern in knowledge_base"},
            "operacion": {"type": "string",
                         "enum": ["fusion", "composicion", "diferencial", "integracion",
                                  "loop_test", "contribucion_marginal",
                                  "factorizacion_izquierda", "cruce_previo"],
                         "description": "Algebraic operation to perform (MAESTRO v3 §3.2)"},
        }, "required": ["patron_a_id", "patron_b_id", "operacion"]}
    }, lambda a: tool_pattern_algebra(
        a["patron_a_id"], a["patron_b_id"], a["operacion"]
    ), category="patterns")

    registry.register("pattern_transversal", {
        "name": "pattern_transversal",
        "description": "Find cross-domain applications of a concept. Identifies isomorphisms between domains and proposes where a pattern could apply via abduction.",
        "parameters": {"type": "object", "properties": {
            "concept_or_query": {"type": "string", "description": "Concept or query to search transversally across domains"},
        }, "required": ["concept_or_query"]}
    }, lambda a: tool_pattern_transversal(a["concept_or_query"]),
    category="patterns")
