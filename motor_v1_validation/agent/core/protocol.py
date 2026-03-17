"""Implementation Protocol — 6-chapter 'Book Structure' for structured work."""

import time
from typing import Optional


CHAPTERS = {
    "DESCUBRIMIENTO": {
        "order": 1,
        "purpose": "Entender el problema y su contexto completo",
        "metaphor": "Prologo",
        "tools_allowed": [
            "read_file", "list_dir", "glob_files", "grep_content",
            "db_query", "search_patterns", "search_concepts", "remember",
            "remember_save", "web_search", "pattern_transversal",
        ],
        "deliverables": ["problem_statement", "context_map", "constraints", "stakeholders"],
        "transition_criteria": "Problem statement claro + contexto mapeado + restricciones identificadas",
        "max_iterations": 15,
        "prompt_hint": (
            "You are in DESCUBRIMIENTO (Discovery). Your goal: understand the problem fully.\n"
            "- Ask clarifying questions\n"
            "- Read relevant files and search the knowledge base\n"
            "- Map the context: what exists, what constraints, who is affected\n"
            "- Do NOT propose solutions yet — just understand"
        ),
    },
    "ARQUITECTURA": {
        "order": 2,
        "purpose": "Disenar la estructura de alto nivel",
        "metaphor": "Los personajes y el mundo",
        "tools_allowed": [
            "plan", "search_patterns", "search_concepts", "pattern_algebra",
            "pattern_transversal", "remember", "remember_save", "db_query",
            "read_file", "list_dir", "glob_files", "grep_content",
            "explore_patterns", "swarm_analyze", "web_search",
        ],
        "deliverables": ["architecture_diagram", "component_list", "interfaces",
                         "technology_choices", "risk_assessment"],
        "transition_criteria": "Arquitectura aprobada + componentes definidos + riesgos mitigados",
        "max_iterations": 10,
        "prompt_hint": (
            "You are in ARQUITECTURA. Your goal: design the high-level structure.\n"
            "- Define components and their interfaces\n"
            "- Choose technologies and patterns\n"
            "- Identify risks and mitigations\n"
            "- Use pattern algebra for cross-domain insights\n"
            "- Present architecture for user approval before proceeding"
        ),
    },
    "DISENO_DETALLADO": {
        "order": 3,
        "purpose": "Especificar cada componente al detalle",
        "metaphor": "El nudo se tensa",
        "tools_allowed": [
            "plan", "submit_design", "search_patterns", "search_concepts",
            "pattern_algebra", "remember", "remember_save", "db_query",
            "read_file", "list_dir", "glob_files", "grep_content",
        ],
        "deliverables": ["detailed_specs", "api_contracts", "data_models",
                         "test_strategy", "implementation_order"],
        "transition_criteria": "Specs completas + contratos API + plan de tests",
        "max_iterations": 10,
        "prompt_hint": (
            "You are in DISENO DETALLADO. Your goal: specify each component.\n"
            "- Define API contracts, data models, function signatures\n"
            "- Plan test strategy\n"
            "- Define implementation order\n"
            "- When ready, call submit_design() with the structured briefing"
        ),
    },
    "IMPLEMENTACION": {
        "order": 4,
        "purpose": "Escribir el codigo siguiendo las specs",
        "metaphor": "La accion",
        "tools_allowed": "ALL",
        "deliverables": ["code_changes", "migrations", "tests_written"],
        "transition_criteria": "Codigo escrito + tests pasando + sin TODOs pendientes",
        "max_iterations": 80,
        "prompt_hint": (
            "You are in IMPLEMENTACION. Your goal: write code following the approved specs.\n"
            "- All tools available\n"
            "- Follow the detailed design\n"
            "- Write tests alongside code\n"
            "- Commit frequently with clear messages"
        ),
    },
    "VALIDACION": {
        "order": 5,
        "purpose": "Verificar que todo funciona correctamente",
        "metaphor": "La resolucion",
        "tools_allowed": [
            "run_command", "run_tests", "db_query", "read_file", "list_dir",
            "glob_files", "grep_content", "curl_api", "remember_save",
        ],
        "deliverables": ["test_results", "integration_verification", "performance_metrics"],
        "transition_criteria": "Tests pasando + integracion verificada + metricas aceptables",
        "max_iterations": 10,
        "prompt_hint": (
            "You are in VALIDACION. Your goal: verify everything works.\n"
            "- Run all tests\n"
            "- Verify integration between components\n"
            "- Check performance metrics\n"
            "- Document any issues found"
        ),
    },
    "CIERRE": {
        "order": 6,
        "purpose": "Documentar, persistir aprendizajes, limpiar",
        "metaphor": "Epilogo",
        "tools_allowed": [
            "remember_save", "db_query", "db_insert", "write_file",
            "read_file", "run_command",
        ],
        "deliverables": ["summary", "lessons_learned", "knowledge_persisted"],
        "transition_criteria": "Resumen entregado + conocimiento persistido",
        "max_iterations": 3,
        "prompt_hint": (
            "You are in CIERRE. Your goal: document and persist learnings.\n"
            "- Write a summary of what was done\n"
            "- Save lessons learned to knowledge base\n"
            "- Clean up temporary files\n"
            "- Report final metrics"
        ),
    },
}

# Map old phases to chapters for backward compat
PHASE_TO_CHAPTER = {
    "design": "DESCUBRIMIENTO",
    "review": "VALIDACION",
    "execute": "IMPLEMENTACION",
    "done": "CIERRE",
}

CHAPTER_TO_PHASE = {
    "DESCUBRIMIENTO": "design",
    "ARQUITECTURA": "design",
    "DISENO_DETALLADO": "design",
    "IMPLEMENTACION": "execute",
    "VALIDACION": "review",
    "CIERRE": "done",
}


class ProtocolEngine:
    """Motor del protocolo de 6 capitulos."""

    def __init__(self, session_id: str = ""):
        self.session_id = session_id
        self.current_chapter = "DESCUBRIMIENTO"
        self.chapter_history = []
        self.deliverables = {}
        self.iteration_counts = {}

    def get_current_chapter(self) -> dict:
        """Return current chapter config with all metadata."""
        ch = CHAPTERS.get(self.current_chapter, CHAPTERS["DESCUBRIMIENTO"])
        return {
            "name": self.current_chapter,
            "phase": CHAPTER_TO_PHASE.get(self.current_chapter, "design"),
            **ch,
            "deliverables_completed": list(self.deliverables.get(self.current_chapter, {}).keys()),
            "deliverables_pending": [
                d for d in ch["deliverables"]
                if d not in self.deliverables.get(self.current_chapter, {})
            ],
            "iterations_used": self.iteration_counts.get(self.current_chapter, 0),
        }

    def get_allowed_tools(self) -> set:
        """Get set of allowed tool names for current chapter."""
        ch = CHAPTERS.get(self.current_chapter, {})
        allowed = ch.get("tools_allowed", "ALL")
        if allowed == "ALL":
            return None  # None means all tools allowed
        return set(allowed)

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed in the current chapter."""
        allowed = self.get_allowed_tools()
        if allowed is None:
            return True
        return tool_name in allowed

    def record_iteration(self) -> None:
        """Record an iteration in the current chapter."""
        self.iteration_counts[self.current_chapter] = \
            self.iteration_counts.get(self.current_chapter, 0) + 1

    def record_deliverable(self, deliverable_type: str, content: dict = None) -> None:
        """Record a completed deliverable."""
        if self.current_chapter not in self.deliverables:
            self.deliverables[self.current_chapter] = {}
        self.deliverables[self.current_chapter][deliverable_type] = {
            "completed_at": time.time(),
            "content": content,
        }

    def can_advance(self) -> bool:
        """Check if we can advance to the next chapter. ALL deliverables required."""
        ch = CHAPTERS.get(self.current_chapter, {})
        required = ch.get("deliverables", [])
        if not required:
            return True
        completed = set(self.deliverables.get(self.current_chapter, {}).keys())
        return len(completed) >= len(required)

    def advance_chapter(self) -> Optional[str]:
        """Advance to the next chapter. Returns new chapter name or None."""
        current = CHAPTERS.get(self.current_chapter, {})
        current_order = current.get("order", 1)
        next_order = current_order + 1

        for name, ch in CHAPTERS.items():
            if ch["order"] == next_order:
                self.chapter_history.append({
                    "chapter": self.current_chapter,
                    "completed_at": time.time(),
                    "deliverables": self.deliverables.get(self.current_chapter, {}),
                    "iterations": self.iteration_counts.get(self.current_chapter, 0),
                })
                self.current_chapter = name
                return name
        return None  # Already at last chapter

    def set_chapter(self, chapter_name: str) -> bool:
        """Force-set chapter (for backward compat with phase transitions)."""
        if chapter_name in CHAPTERS:
            if chapter_name != self.current_chapter:
                self.chapter_history.append({
                    "chapter": self.current_chapter,
                    "jumped_to": chapter_name,
                    "at": time.time(),
                })
                self.current_chapter = chapter_name
            return True
        # Try mapping from old phase name
        mapped = PHASE_TO_CHAPTER.get(chapter_name)
        if mapped and mapped in CHAPTERS:
            return self.set_chapter(mapped)
        return False

    def get_prompt_hint(self) -> str:
        """Get the prompt hint for the current chapter."""
        ch = CHAPTERS.get(self.current_chapter, {})
        return ch.get("prompt_hint", "")

    def get_progress(self) -> dict:
        """Full progress report across all chapters."""
        progress = []
        for name, ch in sorted(CHAPTERS.items(), key=lambda x: x[1]["order"]):
            completed = list(self.deliverables.get(name, {}).keys())
            status = "completed" if name in [h["chapter"] for h in self.chapter_history] else \
                     "active" if name == self.current_chapter else "pending"
            progress.append({
                "chapter": name,
                "order": ch["order"],
                "purpose": ch["purpose"],
                "metaphor": ch["metaphor"],
                "status": status,
                "deliverables_total": len(ch["deliverables"]),
                "deliverables_completed": len(completed),
                "iterations": self.iteration_counts.get(name, 0),
            })
        return {
            "current_chapter": self.current_chapter,
            "chapters": progress,
            "total_iterations": sum(self.iteration_counts.values()),
        }

    def to_dict(self) -> dict:
        """Serialize for session persistence."""
        return {
            "current_chapter": self.current_chapter,
            "chapter_history": self.chapter_history,
            "deliverables": self.deliverables,
            "iteration_counts": self.iteration_counts,
        }

    @classmethod
    def from_dict(cls, data: dict, session_id: str = "") -> 'ProtocolEngine':
        """Deserialize from persisted data."""
        engine = cls(session_id=session_id)
        engine.current_chapter = data.get("current_chapter", "DESCUBRIMIENTO")
        engine.chapter_history = data.get("chapter_history", [])
        engine.deliverables = data.get("deliverables", {})
        engine.iteration_counts = data.get("iteration_counts", {})
        return engine
