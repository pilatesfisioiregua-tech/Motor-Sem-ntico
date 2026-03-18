"""Model routing — 4-role architecture (cerebro/worker/evaluador/swarm) with 3 modes.

Consolidated from 8 roles to 4 based on patterns 60665 (sweet spot 4-5), 60673 (Diferencial A-B).
3 modes (Quick/Standard/Deep) per pattern 60666 (Modos API Diferenciados).

Architecture — Devstral 2 unified stack (March 2026):
- CEREBRO (Devstral 2, 123B dense): agentic coding, $0.40/$2.00 — validado 100%
- WORKER (Devstral 2, unified): mismo modelo — evita split cerebro/worker que falló con Qwen3+MiniMax
- EVALUADOR (GLM-5): #1 Arena rating (1451 ELO), $2.30/M — sin cambio
- Key insight: unified model > split cuando el worker no completa tareas
"""

from dataclasses import dataclass, field
from typing import Optional, List

from .api import get_tier_config, call_with_retry, call_model_with_retry, extract_response


# ============================================================
# 3 MODES — Quick / Standard / Deep (pattern 60666)
# ============================================================

@dataclass
class ModeConfig:
    """Pipeline configuration per mode."""
    name: str
    max_iterations: int
    timeout_s: int
    use_council: bool
    use_swarm: bool

MODE_CONFIGS = {
    "quick": ModeConfig("quick", max_iterations=999, timeout_s=120,
                        use_council=False, use_swarm=False),
    "standard": ModeConfig("standard", max_iterations=999, timeout_s=600,
                           use_council=True, use_swarm=False),
    "deep": ModeConfig("deep", max_iterations=999, timeout_s=900,
                       use_council=True, use_swarm=True),
    "execute": ModeConfig("execute", max_iterations=999, timeout_s=600,
                          use_council=False, use_swarm=False),
    "analyze": ModeConfig("analyze", max_iterations=999, timeout_s=600,
                          use_council=False, use_swarm=False),
}

QUICK_KEYWORDS = [
    "typo", "rename", "renombra", "fix import", "corrige", "cambia nombre",
    "agrega comment", "quita", "borra linea", "actualiza version",
    "simple", "pequeño", "rápido", "trivial",
]
DEEP_KEYWORDS = [
    "arquitectura", "refactor completo", "análisis profundo", "debugging",
    "por qué falla", "diseña", "analiza todo", "revisa a fondo",
    "investiga", "swarm", "patrones", "optimiza",
]

ANALYZE_KEYWORDS = [
    "diagnosticar", "analizar", "revisar", "revisa", "comparar", "evaluar",
    "listar", "mostrar", "comprobar", "comprueba", "verificar", "verifica",
    "diagnose", "analyze", "review", "compare", "evaluate", "check",
]
EXECUTE_KEYWORDS = [
    "crear", "crea", "modificar", "modifica", "implementar", "implementa",
    "fix", "deploy", "añadir", "añade", "agrega",
    "create", "modify", "implement", "build", "write", "add",
]


def detect_mode(goal: str) -> str:
    """Detect execution mode from goal text.

    Returns 'quick', 'execute', 'analyze', 'standard', or 'deep'.
    """
    goal_lower = goal.lower()

    # Briefing step detection (highest priority)
    if goal_lower.startswith("paso ") or "instruccion:" in goal_lower or "instrucción:" in goal_lower:
        return "execute"

    if any(kw in goal_lower for kw in QUICK_KEYWORDS) and len(goal) < 200:
        return "quick"
    if any(kw in goal_lower for kw in DEEP_KEYWORDS):
        return "deep"
    # Execute tiene prioridad sobre analyze — la acción principal importa más que la verificación
    if any(kw in goal_lower for kw in EXECUTE_KEYWORDS):
        return "execute"
    if any(kw in goal_lower for kw in ANALYZE_KEYWORDS):
        return "analyze"

    return "standard"


# ---- Phase detection for cerebro/trabajador switching ---- #

# Tools that signal the agent is in "thinking" mode (cerebro)
CEREBRO_TOOLS = {
    "plan", "list_dir", "glob_files", "grep_content", "search_files",
    "read_file", "ask_user", "web_search", "web_fetch",
    "git_status", "git_log", "git_diff",
    "analyze_codebase", "dependency_graph", "complexity_metrics",
    "review_code", "suggest_improvements",
    "db_query", "search_patterns", "explore_patterns", "remember",
}

# Tools that signal the agent is in "coding" mode (trabajador)
WORKER_TOOLS = {
    "write_file", "edit_file", "insert_at",
    "run_command", "run_tests", "run_linter",
    "git_add", "git_commit",
    "docker_build", "docker_run",
    "install_deps",
}


@dataclass
class TieredRouter:
    """Routes to progressively stronger models based on errors."""
    strategy: str = "tiered"
    forced_model: Optional[str] = None
    current_tier: int = 0
    consecutive_errors: int = 0
    reasoning_blowups: int = 0

    def __post_init__(self):
        tc = get_tier_config()
        self.tiers = [
            tc.get("worker_budget", tc.get("fast", tc.get("tier1", "deepseek/deepseek-v3.2"))),
            tc.get("worker", tc.get("code_gen", tc.get("tier2", "deepseek/deepseek-v3.2"))),
            tc.get("orchestrator", tc.get("tier3", "qwen/qwen3-coder")),
        ]

    def select(self) -> str:
        if self.forced_model:
            return self.forced_model
        if self.strategy == "solo":
            return self.tiers[0]
        return self.tiers[min(self.current_tier, len(self.tiers) - 1)]

    def on_error(self, error_text: str = "") -> None:
        if any(kw in error_text for kw in ["JSONDecodeError", "SyntaxError", "Timed out",
                                            "File not found", "not a directory"]):
            return
        self.consecutive_errors += 1
        if self.consecutive_errors >= 2 and self.strategy != "solo":
            self.current_tier = min(self.current_tier + 1, len(self.tiers) - 1)
            self.consecutive_errors = 0

    def on_test_failure(self) -> None:
        self.consecutive_errors += 1
        if self.consecutive_errors >= 3 and self.strategy != "solo":
            self.current_tier = min(self.current_tier + 1, len(self.tiers) - 1)
            self.consecutive_errors = 0

    def on_success(self) -> None:
        self.consecutive_errors = 0

    def on_blowup(self) -> None:
        self.reasoning_blowups += 1
        if self.strategy != "solo":
            self.current_tier = min(self.current_tier + 1, len(self.tiers) - 1)


# ============================================================
# TASK TYPES — keyword classification
# ============================================================

TASK_TYPES = {
    "code_gen":      {"tier": 0, "description": "Generate new code"},
    "debugging":     {"tier": 1, "description": "Fix bugs, resolve errors"},
    "refactoring":   {"tier": 0, "description": "Restructure existing code"},
    "testing":       {"tier": 0, "description": "Write or run tests"},
    "architecture":  {"tier": 2, "description": "Design decisions, system design"},
    "security":      {"tier": 1, "description": "Security analysis, vulnerability fix"},
    "documentation": {"tier": 0, "description": "Write docs, comments"},
    "devops":        {"tier": 1, "description": "CI/CD, Docker, deployment"},
}

TASK_KEYWORDS = {
    "code_gen":      ["create", "implement", "add", "build", "write", "genera", "crea"],
    "debugging":     ["fix", "bug", "error", "broken", "failing", "arregla", "falla"],
    "refactoring":   ["refactor", "clean", "reorganize", "extract", "simplify"],
    "testing":       ["test", "pytest", "coverage", "verify", "valida"],
    "architecture":  ["design", "architect", "system", "plan", "estructura"],
    "security":      ["security", "vulnerability", "scan", "secret", "audit"],
    "documentation": ["document", "readme", "docstring", "explain"],
    "devops":        ["deploy", "docker", "ci", "cd", "pipeline", "github actions"],
}


# ============================================================
# DUAL MODEL ROUTER — cerebro/trabajador split
# ============================================================

@dataclass
class DualModelRouter(TieredRouter):
    """Cerebro/Trabajador router — uses different models for thinking vs coding.

    B07: Unified Devstral 2 stack (Qwen3-Coder falló 0/4, MiniMax worker no completaba):
    - CEREBRO (Devstral 2, 123B dense): agentic coding, $0.40/$2.00 — validado 100%
    - WORKER (Devstral 2, unified): mismo modelo — evita split que falló
    - EVALUADOR (GLM-5): #1 Arena rating (1451 ELO) — mejor juicio y evaluación
    """
    task_type: str = "code_gen"
    reflection_history: List[str] = field(default_factory=list)
    consecutive_failures: int = 0
    _reflection_active: bool = False

    # Dual-model state
    _phase: str = "cerebro"  # "cerebro" or "trabajador"
    _last_tools: List[str] = field(default_factory=list)
    _cerebro_iters: int = 0
    _worker_iters: int = 0
    _blowup_models: List[str] = field(default_factory=list)
    # Escalation context preservation (Tiers Adaptativos 60670)
    _just_escalated: bool = False
    _escalation_reason: str = ""

    # Mode configuration (pattern 60666)
    _mode: str = "standard"

    def __post_init__(self):
        super().__post_init__()
        tc = get_tier_config()
        self._cerebro_model = tc.get("cerebro", tc.get("orchestrator", "qwen/qwen3-coder"))
        self._worker_model = tc.get("worker", "minimax/minimax-m2.5")
        self._worker_budget = tc.get("worker_budget", "deepseek/deepseek-v3.2")
        self._evaluador_model = tc.get("evaluador", tc.get("synthesis", "z-ai/glm-5"))
        self._cerebro_execute = tc.get("cerebro_execute", self._cerebro_model)   # B14
        self._cerebro_analyze = tc.get("cerebro_analyze", self._cerebro_model)   # B14

    def classify_task(self, goal: str) -> str:
        """Classify task type from goal text."""
        goal_lower = goal.lower()
        scores = {}
        for task_type, keywords in TASK_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in goal_lower)
            if score > 0:
                scores[task_type] = score
        if scores:
            self.task_type = max(scores, key=scores.get)
        return self.task_type

    # Budget tracking for cost-aware routing
    _budget_remaining: float = 5.0
    _budget_total: float = 5.0

    def set_budget(self, total: float, spent: float = 0.0) -> None:
        """Set budget awareness for cost-based routing."""
        self._budget_total = total
        self._budget_remaining = total - spent

    def update_budget(self, spent: float) -> None:
        """Update remaining budget after each iteration."""
        self._budget_remaining = self._budget_total - spent

    def set_mode(self, mode: str) -> None:
        """Set execution mode (quick/standard/deep)."""
        if mode in MODE_CONFIGS:
            self._mode = mode

    def get_mode_config(self) -> ModeConfig:
        """Get current mode configuration."""
        return MODE_CONFIGS.get(self._mode, MODE_CONFIGS["standard"])

    def select(self) -> str:
        """Select model based on mode + phase + budget awareness."""
        if self.forced_model:
            return self.forced_model

        # Quick mode: always use budget model (pattern 60666)
        if self._mode == "quick":
            self._worker_iters += 1
            return self._worker_budget

        # Execute mode: modelo capaz de escribir código via tools
        if self._mode == "execute":
            model = self._cerebro_execute
            if model in self._blowup_models:
                model = self._worker_budget
            self._worker_iters += 1
            return model

        # Analyze mode: modelo capaz de sintetizar diagnósticos
        if self._mode == "analyze":
            model = self._cerebro_analyze
            if model in self._blowup_models:
                model = self._worker_budget
            self._cerebro_iters += 1
            return model

        # Budget-aware: if <20% budget left, force budget model
        if self._budget_remaining < self._budget_total * 0.20:
            self._worker_iters += 1
            return self._worker_budget

        if self._phase == "cerebro":
            model = self._cerebro_model
            if model in self._blowup_models:
                model = self._worker_budget
            self._cerebro_iters += 1
            return model
        else:
            model = self._worker_model
            if model in self._blowup_models:
                model = self._worker_budget
            self._worker_iters += 1
            return model

    def record_tool_use(self, tool_name: str) -> None:
        """Track tool usage to detect phase transitions."""
        self._last_tools.append(tool_name)
        if len(self._last_tools) > 5:
            self._last_tools = self._last_tools[-5:]

        # Transition logic
        if tool_name in WORKER_TOOLS:
            if self._phase == "cerebro":
                self._phase = "trabajador"
        elif tool_name in CEREBRO_TOOLS:
            if self._phase == "trabajador":
                # Only switch back to cerebro after reading/searching
                # (not just any cerebro tool — need 2+ consecutive)
                recent = self._last_tools[-3:]
                cerebro_count = sum(1 for t in recent if t in CEREBRO_TOOLS)
                if cerebro_count >= 2:
                    self._phase = "cerebro"

    def on_error(self, error_text: str = "") -> None:
        """On error: switch to cerebro (debugging needs thinking)."""
        old_tier = self.current_tier
        super().on_error(error_text)
        self.consecutive_failures += 1
        # Errors → switch to cerebro for analysis
        if self.consecutive_failures >= 2:
            self._phase = "cerebro"
        # Track escalation for context preservation (Tiers Adaptativos 60670)
        if self.current_tier > old_tier:
            self._just_escalated = True
            self._escalation_reason = error_text[:500] if error_text else "errores consecutivos"

    def on_test_failure(self) -> None:
        """Test failures → cerebro for debugging."""
        super().on_test_failure()
        self._phase = "cerebro"

    def on_success(self) -> None:
        super().on_success()
        self.consecutive_failures = 0

    def get_escalation_context(self) -> Optional[str]:
        """If tier escalation just happened, return context message for new model.

        Implements Tiers Adaptativos (60670): preserve context when escalating
        so the stronger model doesn't repeat the same failed approaches.
        """
        if not self._just_escalated:
            return None
        self._just_escalated = False
        return (
            f"Error previo: {(self._escalation_reason or '')[:100]}. "
            f"Prueba diferente enfoque."
        )

    def on_blowup(self) -> None:
        """Extended thinking blowup → blacklist model, switch to budget."""
        model = self.select()
        if model not in self._blowup_models:
            self._blowup_models.append(model)
        self.reasoning_blowups += 1

    def should_reflect(self) -> bool:
        return self.consecutive_failures >= 3 and not self._reflection_active

    def reflect(self, error_history: List[str], history: list) -> Optional[str]:
        """Reflection uses cerebro model (devstral for analysis)."""
        if not error_history:
            return None

        self._reflection_active = True
        errors_text = "\n".join(f"- {e}" for e in error_history[-5:])

        reflection_prompt = [
            {"role": "system", "content": (
                "You are a senior debugging expert. Analyze the pattern of errors below "
                "and provide a concrete, actionable strategy to fix the issue. "
                "Focus on what's actually wrong, not generic advice."
            )},
            {"role": "user", "content": (
                f"The agent has failed {self.consecutive_failures} times consecutively.\n\n"
                f"Recent errors:\n{errors_text}\n\n"
                "What is the root cause? What specific approach should be tried next?"
            )},
        ]

        try:
            resp = call_model_with_retry(reflection_prompt, self._cerebro_model, max_retries=1)
            content, _, _ = extract_response(resp)
            self.reflection_history.append(content)
            self.consecutive_failures = 0
            self._reflection_active = False
            self._phase = "cerebro"  # After reflection, stay in cerebro
            return f"[REFLECTION] Analysis of repeated failures:\n{content}"
        except Exception:
            self._reflection_active = False
            return None

    def get_phase_info(self) -> dict:
        """Return current routing state for telemetry/debugging."""
        return {
            "phase": self._phase,
            "mode": self._mode,
            "cerebro_model": self._cerebro_model,
            "worker_model": self._worker_model,
            "evaluador_model": self._evaluador_model,
            "cerebro_iters": self._cerebro_iters,
            "worker_iters": self._worker_iters,
            "blowup_models": self._blowup_models,
            "task_type": self.task_type,
        }


# ============================================================
# REASONING COUNCIL — multi-model validation for complex tasks
# ============================================================

# Tasks that benefit from council validation
COUNCIL_TASK_TYPES = {"architecture", "security", "debugging"}

COUNCIL_ROLES = {
    "math_check":  "cerebro",        # Devstral — validates logic/math (consolidates reasoning)
    "code_check":  "worker",         # Step 3.5 — validates code feasibility
    "synthesizer": "evaluador",      # Cogito — synthesizes if disagreement (consolidates evaluator)
}


class ReasoningCouncil:
    """Multi-model council for complex reasoning tasks.

    Validated by experiments:
    - EXP 4: 2-model mesa captures 90% of value
    - EXP 4.2: Cogito best synthesizer (3.6 connections)
    - EXP 7: 5-model design produced superior architecture
    """

    def __init__(self):
        tc = get_tier_config()
        self._models = {
            role: tc.get(tier, "mistralai/devstral-2512")
            for role, tier in COUNCIL_ROLES.items()
        }

    def should_convene(self, task_type: str, consecutive_failures: int) -> bool:
        """Decide if council should be activated."""
        # Architecture/security tasks always benefit
        if task_type in COUNCIL_TASK_TYPES:
            return True
        # Stuck tasks need council
        if consecutive_failures >= 2:
            return True
        return False

    def convene(self, proposal: str, context: str = "") -> dict:
        """Run council: proposer → validators → synthesizer.

        Args:
            proposal: The plan/architecture to validate
            context: Task context

        Returns: {verdict, votes, synthesis, cost_usd}
        """
        votes = {}
        total_cost = 0.0

        # Phase 1: Math/logic check (Nemotron, $0.30/M)
        math_prompt = [
            {"role": "system", "content": (
                "You are a logic and math validator. Check this proposal for: "
                "logical errors, impossible requirements, mathematical inconsistencies, "
                "missing edge cases. Be brief — 2-3 sentences max."
            )},
            {"role": "user", "content": f"CONTEXT:\n{context[:2000]}\n\nPROPOSAL:\n{proposal[:3000]}"},
        ]
        try:
            resp = call_model_with_retry(math_prompt, self._models["math_check"], max_retries=1)
            content, _, _ = extract_response(resp)
            votes["math_check"] = content
            total_cost += resp.get("usage", {}).get("completion_tokens", 0) * 0.30 / 1_000_000
        except Exception:
            votes["math_check"] = "(unavailable)"

        # Phase 2: Code feasibility check (Step 3.5, $3.80/M)
        code_prompt = [
            {"role": "system", "content": (
                "You are a senior engineer. Check this proposal for: "
                "code feasibility, API compatibility, dependency issues, "
                "implementation blockers. Be brief — 2-3 sentences max."
            )},
            {"role": "user", "content": f"CONTEXT:\n{context[:2000]}\n\nPROPOSAL:\n{proposal[:3000]}"},
        ]
        try:
            resp = call_model_with_retry(code_prompt, self._models["code_check"], max_retries=1)
            content, _, _ = extract_response(resp)
            votes["code_check"] = content
            total_cost += resp.get("usage", {}).get("completion_tokens", 0) * 3.80 / 1_000_000
        except Exception:
            votes["code_check"] = "(unavailable)"

        # Phase 3: Check for disagreement
        all_ok = all(
            not any(kw in v.lower() for kw in ["error", "impossible", "blocker", "fail", "wrong"])
            for v in votes.values() if v != "(unavailable)"
        )

        if all_ok:
            return {
                "verdict": "approved",
                "votes": votes,
                "synthesis": None,
                "cost_usd": round(total_cost, 4),
            }

        # Phase 4: Synthesis (Cogito, $5/M) — only if disagreement
        synth_prompt = [
            {"role": "system", "content": (
                "You are a technical synthesizer. Two reviewers found issues with a proposal. "
                "Synthesize their feedback into a single concrete action list (max 5 items)."
            )},
            {"role": "user", "content": (
                f"PROPOSAL:\n{proposal[:2000]}\n\n"
                f"MATH REVIEW:\n{votes.get('math_check', 'N/A')}\n\n"
                f"CODE REVIEW:\n{votes.get('code_check', 'N/A')}"
            )},
        ]
        synthesis = ""
        try:
            resp = call_model_with_retry(synth_prompt, self._models["synthesizer"], max_retries=1)
            synthesis, _, _ = extract_response(resp)
            total_cost += resp.get("usage", {}).get("completion_tokens", 0) * 5.0 / 1_000_000
        except Exception:
            synthesis = "(synthesis unavailable)"

        return {
            "verdict": "needs_revision",
            "votes": votes,
            "synthesis": synthesis,
            "cost_usd": round(total_cost, 4),
        }


# Backward compatibility alias
SmartRouter = DualModelRouter
