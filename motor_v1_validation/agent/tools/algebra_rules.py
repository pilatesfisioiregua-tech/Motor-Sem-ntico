"""MAESTRO v3 formal algebra — rules, operations, thinking types, validation (code puro, $0)."""

from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
# 8 ALGEBRAIC OPERATIONS (§3.2)
# ═══════════════════════════════════════════════════════════════

OPERATIONS = {
    "fusion": {
        "symbol": "∫(A|B)",
        "form": "parallel",
        "description": "Two patterns analyze the same problem in parallel. Produces complementary perspectives.",
        "properties": {
            "commutative": False,   # Rule 6: order affects framing
            "associative": False,   # Rule 9: ~30% loss when factorized
            "has_inverse": False,
            "idempotent": False,
            "factorizable_loss": 0.30,
        },
        "rules_applied": [2, 6, 9],
    },
    "composicion": {
        "symbol": "A→B",
        "form": "sequential",
        "description": "Output of A is input of B. Sequential pipeline. Non-commutative.",
        "properties": {
            "commutative": False,   # A→B ≠ B→A
            "associative": False,   # Rule 5: (A→B)→C > A→(B→C)
            "has_inverse": False,
        },
        "rules_applied": [4, 5],
    },
    "integracion": {
        "symbol": "∫",
        "form": "summation",
        "description": "Finds crossings and emergences across multiple patterns. Summation of perspectives.",
        "properties": {
            "commutative": True,
            "associative": True,
        },
        "rules_applied": [12],
    },
    "diferencial": {
        "symbol": "A-B",
        "form": "subtraction",
        "description": "Exclusive capabilities of A that B structurally cannot do.",
        "properties": {
            "commutative": False,   # A-B ≠ B-A
            "symmetric": False,
        },
        "rules_applied": [2],
    },
    "loop_test": {
        "symbol": "→→",
        "form": "recursion",
        "description": "Run output through a second pass. Non-idempotent, saturates at n=2.",
        "properties": {
            "idempotent": False,
            "saturation_n": 2,
        },
        "rules_applied": [7, 8, 13],
    },
    "contribucion_marginal": {
        "symbol": "Δ",
        "form": "delta",
        "description": "C is marginal if ∫(A|B|C) ≈ ∫(A|B). Measures added value of a third pattern.",
        "properties": {
            "threshold": 0.10,
        },
        "rules_applied": [3, 13],
    },
    "factorizacion_izquierda": {
        "symbol": "A→(B|C)",
        "form": "optimization",
        "description": "Left factorization: A feeds into parallel B|C. ~30% emergent loss.",
        "properties": {
            "emergent_loss": 0.30,
            "acceptable_if_not_top5": True,
        },
        "rules_applied": [9],
    },
    "cruce_previo": {
        "symbol": "(B|C)→A",
        "form": "irreducible",
        "description": "Right crossing: NEVER factorize. Irreducible value from joint view.",
        "properties": {
            "factorizable": False,
        },
        "rules_applied": [10],
    },
}

# ═══════════════════════════════════════════════════════════════
# 13 COMPILER RULES (§3.3)
# ═══════════════════════════════════════════════════════════════

COMPILER_RULES = [
    {
        "id": 1,
        "name": "Nucleo irreducible",
        "rule": "Always ≥1 of {INT-01,INT-02} + ≥1 of {INT-08,INT-17} + INT-16",
        "quantitative_set": ["INT-01", "INT-02"],
        "human_set": ["INT-08", "INT-17"],
        "required": ["INT-16"],
    },
    {
        "id": 2,
        "name": "Maximo diferencial",
        "rule": "Prioritize quantitative-existential pairs for max perspective delta",
    },
    {
        "id": 3,
        "name": "Sweet spot",
        "rule": "4-5 intelligences. <3 = blind spots. >6 = diminishing returns",
        "min": 3, "optimal_min": 4, "optimal_max": 5, "max": 6,
    },
    {
        "id": 4,
        "name": "Formal primero",
        "rule": "In compositions, formal/distant first, then human/close",
    },
    {
        "id": 5,
        "name": "No reorganizar",
        "rule": "Linear sequence (A→B)→C beats grouped A→(B→C)",
    },
    {
        "id": 6,
        "name": "Fusiones con cuidado",
        "rule": "Order affects framing. First the most aligned with the subject",
    },
    {
        "id": 7,
        "name": "Loop test siempre",
        "rule": "2 passes by default in analysis/confrontation mode",
        "default_passes": 2,
    },
    {
        "id": 8,
        "name": "No tercera pasada",
        "rule": "n=3 not justified except calibration",
        "max_passes": 2,
    },
    {
        "id": 9,
        "name": "Fusiones paralelizables ~70%",
        "rule": "A→(B|C) loses ~30% emergent value. Acceptable if not in top 5",
        "retention_rate": 0.70,
    },
    {
        "id": 10,
        "name": "Cruce previo NO factorizable",
        "rule": "(B|C)→A always together. Irreducible value",
    },
    {
        "id": 11,
        "name": "Marco binario universal",
        "rule": "First action = INT-14 (amplify) + INT-01 (filter)",
    },
    {
        "id": 12,
        "name": "Conversacion pendiente universal",
        "rule": "16/18 intelligences detect unspoken conversation as output",
    },
    {
        "id": 13,
        "name": "Outputs como inputs",
        "rule": "Each pass generates higher-density inputs for next pass",
    },
]

# ═══════════════════════════════════════════════════════════════
# 17 THINKING TYPES (§2.3)
# ═══════════════════════════════════════════════════════════════

THINKING_TYPES = {
    # Internal/Introspective
    "percepcion": {
        "family": "internal",
        "description": "What do I see? Pattern recognition, structural detection.",
        "question": "¿Qué forma tiene esto? ¿Qué patrón repite?",
        "best_for": ["fusion", "integracion"],
    },
    "causalidad": {
        "family": "internal",
        "description": "Why does this happen? Trace causes, detect missing links.",
        "question": "¿Por qué ocurre? ¿Qué causa qué?",
        "best_for": ["composicion", "diferencial"],
    },
    "abstraccion": {
        "family": "internal",
        "description": "What is this an instance of? Generalize, find invariants.",
        "question": "¿De qué es caso particular? ¿Qué invariante subyace?",
        "best_for": ["integracion", "contribucion_marginal"],
    },
    "sintesis": {
        "family": "internal",
        "description": "How do the parts form a whole? Integration, coherence.",
        "question": "¿Cómo encajan las partes? ¿Qué emerge del conjunto?",
        "best_for": ["fusion", "integracion"],
    },
    "discernimiento": {
        "family": "internal",
        "description": "What is essential vs accidental? Filter signal from noise.",
        "question": "¿Qué es esencial y qué es accesorio?",
        "best_for": ["diferencial", "contribucion_marginal"],
    },
    "metacognicion": {
        "family": "internal",
        "description": "What am I assuming? Examine the reasoning process itself.",
        "question": "¿Qué estoy asumiendo? ¿Dónde están mis puntos ciegos?",
        "best_for": ["loop_test", "diferencial"],
    },
    "consciencia_epistemologica": {
        "family": "internal",
        "description": "What kind of knowledge is this? Distinguish fact/belief/hypothesis.",
        "question": "¿Qué tipo de conocimiento es: hecho, creencia, hipótesis?",
        "best_for": ["diferencial", "loop_test"],
    },
    "auto_diagnostico": {
        "family": "internal",
        "description": "Is the system working? Detect dysfunction in the process.",
        "question": "¿Funciona esto? ¿Dónde falla el proceso?",
        "best_for": ["loop_test", "contribucion_marginal"],
    },
    "convergencia": {
        "family": "internal",
        "description": "What do all perspectives agree on? Find common ground.",
        "question": "¿En qué coinciden todas las perspectivas?",
        "best_for": ["integracion", "fusion"],
    },
    "dialectica": {
        "family": "internal",
        "description": "What is the thesis-antithesis-synthesis? Productive opposition.",
        "question": "¿Cuál es la tesis, antítesis y síntesis posible?",
        "best_for": ["fusion", "diferencial"],
    },
    # Lateral/Divergent
    "analogia": {
        "family": "lateral",
        "description": "What is this like? Cross-domain mapping, isomorphisms.",
        "question": "¿A qué se parece en otro dominio? ¿Qué mapeo preserva estructura?",
        "best_for": ["fusion", "cruce_previo"],
    },
    "contrafactual": {
        "family": "lateral",
        "description": "What if X didn't exist? Remove elements to find dependencies.",
        "question": "¿Qué pasaría si eliminamos X? ¿Qué colapsaría?",
        "best_for": ["diferencial", "contribucion_marginal"],
    },
    "abduccion": {
        "family": "lateral",
        "description": "What would explain this? Infer best explanation from observations.",
        "question": "¿Qué explicaría mejor lo observado? ¿Qué hipótesis genera?",
        "best_for": ["integracion", "composicion"],
    },
    "provocacion": {
        "family": "lateral",
        "description": "What if we reverse the assumption? Deliberately break conventions.",
        "question": "¿Y si invertimos el supuesto fundamental?",
        "best_for": ["diferencial", "factorizacion_izquierda"],
    },
    "reencuadre": {
        "family": "lateral",
        "description": "How else can we frame this? Change perspective, find new meaning.",
        "question": "¿Cómo se ve desde otro marco? ¿Qué cambia al reencuadrar?",
        "best_for": ["fusion", "cruce_previo"],
    },
    "destruccion_creativa": {
        "family": "lateral",
        "description": "What must be destroyed to create? Identify structural blockers.",
        "question": "¿Qué hay que eliminar para que emerja algo nuevo?",
        "best_for": ["diferencial", "contribucion_marginal"],
    },
    "creacion": {
        "family": "lateral",
        "description": "What doesn't exist yet? Generate genuinely novel combinations.",
        "question": "¿Qué no existe todavía? ¿Qué combinación es nueva?",
        "best_for": ["fusion", "factorizacion_izquierda"],
    },
}

# ═══════════════════════════════════════════════════════════════
# 6 CONCEPTUAL MODES (§2.4)
# ═══════════════════════════════════════════════════════════════

CONCEPTUAL_MODES = {
    "ANALIZAR": {
        "orientation": "decompose",
        "description": "Decompose, demonstrate, measure. Break down into components.",
        "activation": "Analyze this systematically: decompose, trace dependencies, find gaps.",
        "best_operations": ["diferencial", "composicion", "contribucion_marginal"],
    },
    "PERCIBIR": {
        "orientation": "pattern_recognition",
        "description": "See patterns, detect form, map topology.",
        "activation": "Look for structural patterns: symmetries, repetitions, isomorphisms.",
        "best_operations": ["fusion", "integracion", "cruce_previo"],
    },
    "MOVER": {
        "orientation": "action",
        "description": "Act, position, construct. Generate executable steps.",
        "activation": "Think in terms of actions: what to build, where to place, how to sequence.",
        "best_operations": ["composicion", "factorizacion_izquierda"],
    },
    "SENTIR": {
        "orientation": "affective",
        "description": "Empathize, intuit, inhabit. Register quality signals.",
        "activation": "Sense the quality: what feels right/wrong, what's missing emotionally.",
        "best_operations": ["fusion", "loop_test"],
    },
    "GENERAR": {
        "orientation": "expansive",
        "description": "Create, imagine, project. Open option space, diverge.",
        "activation": "Generate alternatives freely: diverge, imagine, project possibilities.",
        "best_operations": ["fusion", "factorizacion_izquierda", "cruce_previo"],
    },
    "ENMARCAR": {
        "orientation": "meta_linguistic",
        "description": "Name, negotiate, give meaning. Redefine the frame.",
        "activation": "Reframe the problem: rename, negotiate meaning, find the real question.",
        "best_operations": ["diferencial", "integracion", "loop_test"],
    },
}

# ═══════════════════════════════════════════════════════════════
# STRUCTURAL CLASSIFICATION TYPES
# ═══════════════════════════════════════════════════════════════

CLASSIFICATION_TYPES = {
    "complementary": {
        "description": "Different concepts but compatible dimensions → fusion candidates",
        "default_operation": "fusion",
        "reasoning_strategy": {
            "thinking": "sintesis",
            "mode": "PERCIBIR",
        },
    },
    "sequential": {
        "description": "One's output is another's natural input → composition candidates",
        "default_operation": "composicion",
        "reasoning_strategy": {
            "thinking": "causalidad",
            "mode": "ANALIZAR",
        },
    },
    "opposing": {
        "description": "Similar concepts but different value dimensions → differential candidates",
        "default_operation": "diferencial",
        "reasoning_strategy": {
            "thinking": "dialectica",
            "mode": "ANALIZAR",
        },
    },
    "cross_domain": {
        "description": "Same concept in different scopes → transversal/isomorphism candidates",
        "default_operation": "integracion",
        "reasoning_strategy": {
            "thinking": "analogia",
            "mode": "PERCIBIR",
        },
    },
    "redundant": {
        "description": "Too similar → marginal contribution analysis",
        "default_operation": "contribucion_marginal",
        "reasoning_strategy": {
            "thinking": "discernimiento",
            "mode": "ANALIZAR",
        },
    },
    "irreducible_pair": {
        "description": "Joint view produces irreducible value → right crossing candidates",
        "default_operation": "cruce_previo",
        "reasoning_strategy": {
            "thinking": "reencuadre",
            "mode": "GENERAR",
        },
    },
}

# ═══════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS (deterministic, $0)
# ═══════════════════════════════════════════════════════════════

def validate_operation_properties(
    operacion: str,
    result_data: dict,
) -> List[Dict]:
    """Validate algebraic properties after an operation. Returns list of violations."""
    op_def = OPERATIONS.get(operacion)
    if not op_def:
        return [{"severity": "error", "message": f"Unknown operation: {operacion}"}]

    violations = []
    props = op_def["properties"]

    # Check commutativity claims
    if "commutative" in props and not props["commutative"]:
        if result_data.get("claims_commutative") or result_data.get("conmutativa"):
            violations.append({
                "severity": "warning",
                "rule": f"commutativity ({op_def['symbol']})",
                "message": f"{operacion} is non-commutative per MAESTRO but result claims A|B = B|A",
            })

    # Check saturation for loop_test
    if operacion == "loop_test":
        n_passes = result_data.get("passes", result_data.get("pass_number", 1))
        if n_passes > 2:
            violations.append({
                "severity": "critical",
                "rule": "Rule 8 (no third pass)",
                "message": f"Loop test requested {n_passes} passes, max is 2",
            })

    # Check right crossing integrity
    if operacion == "cruce_previo":
        if result_data.get("factorized") or result_data.get("factorizable"):
            violations.append({
                "severity": "critical",
                "rule": "Rule 10 (right crossing irreducible)",
                "message": "(B|C)→A was factorized — NEVER factorize right crossing",
            })

    # Check factorization loss acknowledgement
    if operacion == "factorizacion_izquierda":
        if not result_data.get("emergent_loss_acknowledged"):
            violations.append({
                "severity": "info",
                "rule": "Rule 9 (~30% loss)",
                "message": "Left factorization should acknowledge ~30% emergent value loss",
            })

    return violations


def validate_sweet_spot(count: int) -> List[Dict]:
    """Validate Rule 3: sweet spot 4-5."""
    violations = []
    if count < 3:
        violations.append({"severity": "critical", "rule": "Rule 3",
                          "message": f"{count} patterns < 3 = blind spots"})
    elif count > 6:
        violations.append({"severity": "warning", "rule": "Rule 3",
                          "message": f"{count} patterns > 6 = diminishing returns"})
    return violations


# ═══════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER
# ═══════════════════════════════════════════════════════════════

def build_maestro_system_prompt(
    thinking_type: Optional[str] = None,
    mode: Optional[str] = None,
) -> str:
    """Build LLM system prompt with MAESTRO v3 algebra rules embedded."""

    rules_text = "\n".join(
        f"  R{r['id']:02d}: {r['name']} — {r['rule']}"
        for r in COMPILER_RULES
    )

    ops_text = "\n".join(
        f"  {op}: {d['symbol']} ({d['form']}) — {d['description']}"
        for op, d in OPERATIONS.items()
    )

    # Optional thinking activation
    thinking_activation = ""
    if thinking_type and thinking_type in THINKING_TYPES:
        t = THINKING_TYPES[thinking_type]
        thinking_activation = f"""
=== TIPO DE PENSAMIENTO ACTIVO: {thinking_type.upper()} ===
{t['description']}
Pregunta guía: {t['question']}
Familia: {t['family']}
"""

    # Optional mode activation
    mode_activation = ""
    if mode and mode in CONCEPTUAL_MODES:
        m = CONCEPTUAL_MODES[mode]
        mode_activation = f"""
=== MODO CONCEPTUAL ACTIVO: {mode} ===
Orientación: {m['orientation']}
{m['description']}
Instrucción: {m['activation']}
"""

    return f"""Eres el MOTOR ALGEBRAICO MAESTRO v3. Ejecutas operaciones algebraicas formales
sobre patrones siguiendo reglas estrictas. NO eres un analista genérico — eres un motor de álgebra.

=== 8 OPERACIONES ALGEBRAICAS (§3.2) ===
{ops_text}

=== 13 REGLAS DEL COMPILADOR (OBLIGATORIAS) ===
{rules_text}

=== RESTRICCIONES CRITICAS ===
- Fusión NO es conmutativa: el orden afecta el framing (R06)
- Composición NO es conmutativa: A→B ≠ B→A (R04: formal primero)
- Secuencia lineal supera agrupada: (A→B)→C > A→(B→C) (R05)
- Loop test satura en n=2 (R07). NUNCA hacer n=3 (R08)
- Factorización izquierda A→(B|C) pierde ~30% valor emergente (R09)
- Cruce previo (B|C)→A es IRREDUCIBLE — NUNCA factorizar (R10)
{thinking_activation}{mode_activation}
=== FORMATO DE SALIDA ===
Responde SIEMPRE con JSON válido conteniendo:
- "analisis": análisis textual de la operación
- "emergencias": lista de insights emergentes descubiertos
- "propiedades_verificadas": qué propiedades algebraicas se verificaron
- "contextos_implementacion": lista de contextos donde aplicar el resultado
- "confianza": 0.0-1.0 confianza en el resultado
"""


def build_exploration_prompt(
    classification_type: str,
    pat_a: dict,
    pat_b: dict,
    meta_a: dict,
    meta_b: dict,
) -> str:
    """Build exploration prompt using classification-specific reasoning strategy."""

    cls = CLASSIFICATION_TYPES.get(classification_type, {})
    strategy = cls.get("reasoning_strategy", {})
    thinking = strategy.get("thinking", "sintesis")
    mode = strategy.get("mode", "ANALIZAR")
    operation = cls.get("default_operation", "fusion")
    op_def = OPERATIONS.get(operation, {})

    t_info = THINKING_TYPES.get(thinking, {})
    m_info = CONCEPTUAL_MODES.get(mode, {})

    return f"""EXPLORACIÓN AUTÓNOMA — Universidad I+D de Patrones

CLASIFICACIÓN: {classification_type} — {cls.get('description', '')}
OPERACIÓN: {operation} {op_def.get('symbol', '')} ({op_def.get('form', '')})
PENSAMIENTO: {thinking} — {t_info.get('description', '')}
MODO: {mode} — {m_info.get('description', '')}
PREGUNTA GUÍA: {t_info.get('question', '')}
INSTRUCCIÓN DE MODO: {m_info.get('activation', '')}

PATRÓN A ({pat_a.get('scope', '')}):
{pat_a.get('texto', '')[:600]}
Conceptos: {meta_a.get('conceptos', [])}
Dimensiones: {meta_a.get('dimensiones_valor', {{}})}

PATRÓN B ({pat_b.get('scope', '')}):
{pat_b.get('texto', '')[:600]}
Conceptos: {meta_b.get('conceptos', [])}
Dimensiones: {meta_b.get('dimensiones_valor', {{}})}

EJECUTA:
1. Aplica el tipo de pensamiento "{thinking}" sobre ambos patrones
2. Usa la orientación del modo "{mode}" para guiar tu análisis
3. Realiza la operación "{operation}" ({op_def.get('description', '')})
4. Identifica EMERGENCIAS: insights que solo aparecen al combinar A y B
5. Propón CONTEXTOS DE IMPLEMENTACIÓN: dónde y cómo aplicar lo descubierto

Responde en JSON:
{{"analisis": "...", "emergencias": [...], "complementariedades": [...],
  "tensiones": [...], "contextos_implementacion": [...],
  "propiedades_verificadas": {{}}, "confianza": 0.0-1.0}}"""
