"""Chat engine — multi-turn conversation with SSE streaming over Code OS v2."""

import os
import json
import re
import time
import uuid
import queue
import tempfile
import threading
from typing import Generator, Optional

from core.api import (
    TIER_CONFIG, call_with_retry, call_model_with_retry, extract_response, strip_think_tags,
    get_tier_config, is_anthropic_model,
)
from core.budget import Budget
from core.costes import set_call_context
from core.router import SmartRouter
from core.context import ContextManager
from core.protocol import ProtocolEngine, CHAPTERS, CHAPTER_TO_PHASE
from tools import create_default_registry
from tools.meta import (
    set_autonomous, get_submitted_briefing, clear_submitted_briefing,
)
import session_store

CHAT_SYSTEM_ADDENDUM = """
MODO CONVERSACIÓN AUTÓNOMO — Code OS como CTO del CEO.

PROTOCOLO AUTÓNOMO:
1. Lee (read_file, db_query, http_request) → 2. Entiende (qué está mal) → 3. Arregla (edit_file, db_insert) → 4. Verifica (re-lee, re-ejecuta) → 5. Siguiente (¿hay más? → paso 1) → 6. Reporta lo que hiciste

REGLA CARDINAL: Si detectas un problema y PUEDES arreglarlo → ARRÉGLALO. No describas lo que "se podría hacer". HAZLO.
Describir ≠ ejecutar. "Se podría..." ≠ aceptable. Cada fix se aplica. Cada INSERT se ejecuta.
Tras cada fix → remember_save() el hallazgo + solución.
Consulta mochila("autonomia") para la doctrina completa.

BÚSQUEDA INTELIGENTE (híbrida: full-text + Hebbiano):
- remember(query) → 27K+ entries, scope="patrones"|"chief"|"repo"
- glob_files(pattern, path="@project/") → archivos reales
- grep_content(pattern, path="@project/") → contenido en archivos

KNOWLEDGE BASE: remember() para API keys, DB credentials, deploy config, arquitectura, decisiones pasadas.
remember_save(title, content, category) para guardar conocimiento nuevo.

Para más detalle: mochila("herramientas"), mochila("reglas"), mochila("rutas"), mochila("errores"), mochila("autonomia").
"""

DESIGN_SYSTEM_ADDENDUM = """
MODO DISEÑO — Ayuda al CEO a diseñar requisitos.
- Haz preguntas para eliminar ambigüedad. Propón alternativas. Detecta contradicciones.
- Cuando el diseño esté completo, llama submit_design() con el briefing estructurado.
- NO escribas código. Solo usa read_file, list_dir, glob_files, grep_content, remember, search_patterns.
- Sé exhaustivo: requisitos faltantes son peores que preguntas extra.

BÚSQUEDA: remember(query, scope), glob_files(pattern, path="@project/"), grep_content.
Para más detalle: mochila("herramientas"), mochila("proyecto").
"""

DESIGN_TRIGGER_KEYWORDS = [
    "implementa", "hazlo", "ejecuta", "build it", "go ahead",
    "dale", "procede", "adelante", "do it", "execute",
]

DESIGN_ALLOWED_TOOLS = {
    "plan", "submit_design", "read_file", "list_dir", "glob_files", "grep_content",
    "remember", "remember_save", "db_query",
    "search_patterns", "search_concepts", "pattern_algebra", "pattern_transversal",
    "explore_patterns", "get_discoveries", "get_classifications",
    "swarm_analyze",
}

REVIEW_PROMPT = """You are a senior code architect doing a QUICK sanity check on a design briefing.

BRIEFING:
{briefing_json}

PROJECT CONTEXT:
{project_context}

IMPORTANT: This project uses Python + FastAPI + PostgreSQL (pgvector). The database schema is already deployed.
The agent can discover table schemas via db_query tool at runtime. Do NOT mark missing schema details as CRITICAL.
Do NOT mark missing framework choice as CRITICAL — the project uses FastAPI.
Do NOT mark missing auth as CRITICAL unless the briefing explicitly handles sensitive data.

Only mark as CRITICAL things that would DEFINITELY cause the execution to fail:
- File paths that contradict the project structure
- Logical contradictions in the briefing
- Security vulnerabilities (SQL injection, exposed secrets)

Everything else is WARNING or INFO at most.

Respond with ONLY valid JSON (no markdown, no code blocks):
{{
  "findings": [
    {{"severity": "info|warning|critical", "finding": "...", "suggestion": "..."}}
  ],
  "corrections": [
    {{"field": "tasks|constraints|files_to_create|files_to_modify", "original": "...", "corrected": "..."}}
  ],
  "verdict": "PASS|FAIL",
  "summary": "One-line summary"
}}

Rules:
- CRITICAL = execution will definitely fail (wrong paths, contradictions, security holes)
- WARNING = could be better but agent can figure it out at runtime
- INFO = nice to know
- Default to PASS. Only FAIL if there is a genuine showstopper.
- Apply corrections automatically — don't just suggest them
"""

MAX_TOOL_LOOPS = 80


class ChatEngine:
    """Manages multi-turn chat sessions backed by Code OS v2 tools."""

    MAX_ACTIVE_SESSIONS = 10

    def __init__(
        self,
        project_dir: str = ".",
        strategy: str = "tiered",
        forced_model: Optional[str] = None,
        max_cost: float = 15.0,
        sandbox_dir: Optional[str] = None,
    ):
        self.project_dir = os.path.abspath(project_dir)
        self.strategy = strategy
        self.forced_model = forced_model
        self.max_cost = max_cost
        self.sandbox_dir = sandbox_dir or tempfile.mkdtemp(prefix="chat_os_")
        os.makedirs(self.sandbox_dir, exist_ok=True)
        self.sessions: dict = {}  # chat_id -> session dict
        self._access_order: list = []  # LRU tracking

    def _build_system_prompt(self, phase: str = "design", protocol: ProtocolEngine = None) -> str:
        from core.agent_loop import CODE_OS_SYSTEM
        base = CODE_OS_SYSTEM.format(
            context_section=(
                f"PROJECT DIR: {self.project_dir}\n"
                f"WORKSPACE: {self.sandbox_dir}"
            )
        )

        # Add chapter-specific context if protocol engine available
        chapter_hint = ""
        if protocol:
            ch = protocol.get_current_chapter()
            chapter_hint = (
                f"\n\nPROTOCOLO DE 6 CAPITULOS (actual: {ch['name']} — {ch['metaphor']})\n"
                f"Proposito: {ch['purpose']}\n"
                f"{protocol.get_prompt_hint()}\n"
                f"Entregables pendientes: {', '.join(ch['deliverables_pending']) or 'ninguno'}\n"
            )

        if phase == "design":
            return base + DESIGN_SYSTEM_ADDENDUM + chapter_hint
        return base + CHAT_SYSTEM_ADDENDUM + chapter_hint

    def create_session(self, chat_id: str) -> dict:
        """Initialize a new chat session."""
        set_autonomous(False)

        registry = create_default_registry(self.sandbox_dir, self.project_dir)
        router = SmartRouter(strategy=self.strategy, forced_model=self.forced_model)
        budget = Budget(max_iterations=999, max_cost_usd=self.max_cost)
        ctx_mgr = ContextManager()
        protocol = ProtocolEngine(session_id=chat_id)

        # Wire up Hebbian learning — session_id flows to remember → neural_db
        try:
            from tools.remember import set_session_id
            set_session_id(chat_id)
        except Exception:
            pass

        system_prompt = self._build_system_prompt("chat", protocol)
        history = [{"role": "system", "content": system_prompt}]

        session = {
            "registry": registry,
            "router": router,
            "budget": budget,
            "ctx_mgr": ctx_mgr,
            "protocol": protocol,
            "history": history,
            "tool_schemas": registry.get_schemas(),
            "created_at": time.time(),
            "phase": "done",
            "briefing": None,
        }
        self.sessions[chat_id] = session
        return session

    def get_or_create_session(self, chat_id: str) -> dict:
        if chat_id in self.sessions:
            self._touch_lru(chat_id)
            return self.sessions[chat_id]

        # Try to restore from DB
        restored = self._restore_session(chat_id)
        if restored:
            self._touch_lru(chat_id)
            return restored

        session = self.create_session(chat_id)
        self._touch_lru(chat_id)
        return session

    def _touch_lru(self, chat_id: str) -> None:
        """Update LRU order and evict if needed."""
        if chat_id in self._access_order:
            self._access_order.remove(chat_id)
        self._access_order.append(chat_id)

        # Evict oldest if over limit
        while len(self._access_order) > self.MAX_ACTIVE_SESSIONS:
            evict_id = self._access_order.pop(0)
            if evict_id in self.sessions and evict_id != chat_id:
                self._persist_session(evict_id)
                del self.sessions[evict_id]

    def _restore_session(self, chat_id: str) -> Optional[dict]:
        """Restore a session from DB."""
        try:
            data = session_store.load_session(chat_id)
            if not data:
                return None

            set_autonomous(False)
            registry = create_default_registry(self.sandbox_dir, self.project_dir)
            router = SmartRouter(strategy=self.strategy, forced_model=self.forced_model)
            budget = Budget(max_iterations=999, max_cost_usd=self.max_cost)
            ctx_mgr = ContextManager()

            # Wire up Hebbian learning for restored session
            try:
                from tools.remember import set_session_id
                set_session_id(chat_id)
            except Exception:
                pass

            phase = data.get("phase", "done")
            # Migrate old sessions to direct chat mode
            if phase == "design":
                phase = "done"

            # Restore protocol engine (stored in metadata.protocol)
            meta = data.get("metadata") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            protocol_data = meta.get("protocol")
            if protocol_data:
                protocol = ProtocolEngine.from_dict(protocol_data, session_id=chat_id)
            else:
                protocol = ProtocolEngine(session_id=chat_id)

            system_prompt = self._build_system_prompt(phase, protocol)

            # Reconstruct history with system prompt
            saved_history = data.get("history", [])
            history = [{"role": "system", "content": system_prompt}]

            # Re-add non-system messages from saved history
            for msg in saved_history:
                if msg.get("role") != "system":
                    history.append(msg)

            session = {
                "registry": registry,
                "router": router,
                "budget": budget,
                "ctx_mgr": ctx_mgr,
                "protocol": protocol,
                "history": history,
                "tool_schemas": registry.get_schemas(),
                "created_at": data.get("created_at", time.time()),
                "phase": phase,
                "briefing": data.get("briefing"),
                "title": data.get("title", "Nueva sesión"),
            }
            self.sessions[chat_id] = session
            return session
        except Exception:
            return None

    def _persist_session(self, chat_id: str) -> None:
        """Save current session state to DB."""
        session = self.sessions.get(chat_id)
        if not session:
            return
        try:
            protocol = session.get("protocol")
            protocol_data = protocol.to_dict() if protocol else None
            session_store.save_session(
                session_id=chat_id,
                title=session.get("title", "Nueva sesión"),
                phase=session.get("phase", "design"),
                history=session.get("history", []),
                briefing=session.get("briefing"),
                protocol=protocol_data,
            )
        except Exception:
            pass  # Best effort

    def _auto_title(self, chat_id: str, message: str) -> None:
        """Generate auto-title from first user message."""
        session = self.sessions.get(chat_id)
        if not session:
            return
        if session.get("title") and session["title"] != "Nueva sesión":
            return
        # Use first 60 chars of first message as title
        title = message.strip()[:60]
        if len(message.strip()) > 60:
            title += "..."
        session["title"] = title

    def process_message(
        self, chat_id: str, message: str, force_phase: Optional[str] = None,
    ) -> Generator[dict, None, None]:
        """Process a user message and yield SSE events."""
        set_call_context(componente='copiloto', operacion='chat', caso_id=chat_id)
        session = self.get_or_create_session(chat_id)

        # Auto-title from first user message
        self._auto_title(chat_id, message)

        # Handle force_phase transitions
        if force_phase and force_phase != session["phase"]:
            old_phase = session["phase"]
            session["phase"] = force_phase
            yield {"type": "phase_change", "from": old_phase, "to": force_phase}

        phase = session.get("phase", "done")

        if phase == "done":
            yield from self._process_chat(chat_id, session, message)
        elif phase == "design":
            yield from self._process_design(chat_id, session, message)
        elif phase in ("review", "execute"):
            yield {"type": "text", "content": "Procesando, espera..."}

        # Persist after each interaction
        self._persist_session(chat_id)

    # ------------------------------------------------------------------ #
    # DESIGN phase
    # ------------------------------------------------------------------ #

    def _process_design(
        self, chat_id: str, session: dict, message: str,
    ) -> Generator[dict, None, None]:
        """Design phase: LLM helps user refine requirements, limited tools."""
        history = session["history"]
        registry = session["registry"]
        router = session["router"]
        budget = session["budget"]
        ctx_mgr = session["ctx_mgr"]

        # Auto-inject context before user message
        self._auto_inject_context(message, history)

        # Check for trigger keywords — nudge LLM toward submit_design
        msg_lower = message.lower()
        has_trigger = any(kw in msg_lower for kw in DESIGN_TRIGGER_KEYWORDS)

        history.append({"role": "user", "content": message})

        if has_trigger:
            history.append({
                "role": "user",
                "content": (
                    "[SYSTEM] The user wants to proceed with implementation. "
                    "If you have enough information, call submit_design() now with "
                    "the structured briefing. If critical details are missing, ask "
                    "ONE final question before submitting."
                ),
            })

        # Only expose design-safe tools
        design_schemas = registry.get_schemas(names=DESIGN_ALLOWED_TOOLS)

        for loop_i in range(MAX_TOOL_LOOPS):
            budget_err = budget.exceeded()
            if budget_err:
                yield {"type": "error", "content": f"Budget exceeded: {budget_err}"}
                break

            # Use tier1 (cheap) for design
            model = TIER_CONFIG["tier1"]
            yield {"type": "thinking"}

            try:
                api_resp = call_with_retry(history, model, tools=design_schemas)
            except RuntimeError as e:
                try:
                    fallback = TIER_CONFIG["tier2"]
                    api_resp = call_with_retry(
                        history, fallback, tools=design_schemas, max_retries=1
                    )
                    model = fallback
                except RuntimeError:
                    yield {"type": "error", "content": f"API error: {e}"}
                    break

            usage = api_resp.get("usage", {})
            budget.track(usage, model)

            content, tool_calls, is_blowup = extract_response(api_resp)

            if is_blowup:
                router.on_blowup()
                history.append({"role": "assistant", "content": content or "(empty)"})
                history.append({
                    "role": "user",
                    "content": "Please respond with text or use a tool.",
                })
                continue

            # Text-only response — done for this turn
            if not tool_calls:
                if content:
                    history.append({"role": "assistant", "content": content})
                    yield {"type": "text", "content": content}
                break

            # Process tool calls
            assistant_msg = {"role": "assistant", "content": content or ""}
            assistant_msg["tool_calls"] = tool_calls
            history.append(assistant_msg)

            if content:
                yield {"type": "text", "content": content}

            submitted = False
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                if isinstance(raw_args, dict):
                    tool_args = raw_args
                else:
                    try:
                        tool_args = json.loads(raw_args)
                    except (json.JSONDecodeError, TypeError):
                        tool_args = {}

                tc_id = tc.get("id", f"call_{loop_i}")

                # Block non-design tools
                if tool_name not in DESIGN_ALLOWED_TOOLS:
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": f"ERROR: Tool '{tool_name}' not available in DESIGN phase. "
                                   f"Only {', '.join(sorted(DESIGN_ALLOWED_TOOLS))} are allowed.",
                    })
                    continue

                # Skip finish in design mode
                if tool_name == "finish":
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": "finish() not available in DESIGN phase. Use submit_design() instead.",
                    })
                    continue

                yield {"type": "tool_call", "name": tool_name, "args": tool_args}

                # Sandwich pre-validation
                from core.sandwich import pre_validate_tool_call, post_validate_result
                is_valid, pre_error = pre_validate_tool_call(tool_name, tool_args, registry)
                if not is_valid:
                    result_str, is_error = pre_error, True
                else:
                    result_str, is_error = registry.execute(tool_name, tool_args)
                    result_str, is_error = post_validate_result(tool_name, result_str, is_error)

                history.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_str,
                })

                yield {
                    "type": "tool_result",
                    "name": tool_name,
                    "result": result_str[:5000],
                    "is_error": is_error,
                }

                # Intercept submit_design
                if tool_name == "submit_design" and not is_error:
                    briefing = get_submitted_briefing()
                    if briefing:
                        session["briefing"] = briefing
                        clear_submitted_briefing()
                        submitted = True

            if submitted:
                # Transition to REVIEW
                yield from self._process_review(chat_id, session)
                return

            history = ctx_mgr.maybe_compress(history)
            session["history"] = history

        # Flush tool evolution telemetry buffer
        try:
            from core.tool_evolution import get_tool_evolution
            get_tool_evolution().flush()
        except Exception:
            pass

        # Final status
        summary = budget.summary()
        yield {
            "type": "status",
            "tokens": summary["tokens_used"],
            "cost": summary["cost_usd"],
            "model": TIER_CONFIG["tier1"].split("/")[-1],
        }

    # ------------------------------------------------------------------ #
    # REVIEW phase
    # ------------------------------------------------------------------ #

    def _process_review(
        self, chat_id: str, session: dict,
    ) -> Generator[dict, None, None]:
        """Review phase: tier3 validates briefing, auto-corrects, gates execution."""
        session["phase"] = "review"
        yield {"type": "phase_change", "from": "design", "to": "review"}

        briefing = session["briefing"]
        if not briefing:
            yield {"type": "error", "content": "No briefing to review."}
            session["phase"] = "design"
            return

        # Load project context
        project_context = self._load_project_context()

        # Build review prompt
        prompt = REVIEW_PROMPT.format(
            briefing_json=json.dumps(briefing, indent=2, ensure_ascii=False),
            project_context=project_context,
        )

        # Call tier3 for review
        review_history = [
            {"role": "system", "content": "You are a code review expert. Respond only with valid JSON."},
            {"role": "user", "content": prompt},
        ]

        model = TIER_CONFIG["tier3"]
        yield {"type": "thinking"}

        try:
            api_resp = call_with_retry(review_history, model, tools=None)
        except RuntimeError as e:
            yield {"type": "error", "content": f"Review API error: {e}"}
            session["phase"] = "design"
            return

        usage = api_resp.get("usage", {})
        session["budget"].track(usage, model)

        content, _, _ = extract_response(api_resp)

        # Parse review JSON
        review = self._parse_review_response(content)
        if not review:
            yield {"type": "error", "content": "Review response could not be parsed. Proceeding anyway."}
            review = {"findings": [], "corrections": [], "verdict": "PASS", "summary": "Unparseable"}

        # Emit findings
        findings = review.get("findings", [])
        corrections = review.get("corrections", [])

        for f in findings:
            yield {
                "type": "review_finding",
                "severity": f.get("severity", "info"),
                "finding": f.get("finding", ""),
                "suggestion": f.get("suggestion", ""),
            }

        # Apply corrections
        for c in corrections:
            self._apply_correction(briefing, c)
            yield {
                "type": "review_correction",
                "field": c.get("field", ""),
                "original": c.get("original", ""),
                "corrected": c.get("corrected", ""),
            }

        has_critical = any(f.get("severity") == "critical" for f in findings)

        yield {
            "type": "review_complete",
            "findings_count": len(findings),
            "corrections_count": len(corrections),
            "briefing_summary": review.get("summary", briefing.get("title", "")),
        }

        if has_critical:
            # Send back to DESIGN with feedback
            session["phase"] = "design"
            critical_items = [f for f in findings if f.get("severity") == "critical"]
            feedback = "REVIEW FAILED. Critical issues found:\n" + "\n".join(
                f"- {f['finding']}: {f.get('suggestion', '')}" for f in critical_items
            )
            session["history"].append({
                "role": "user",
                "content": f"[REVIEW FEEDBACK] {feedback}\n\nPlease address these issues and submit_design() again.",
            })
            yield {"type": "review_critical", "reason": feedback}
            yield {"type": "phase_change", "from": "review", "to": "design"}
        else:
            # Proceed to EXECUTE
            session["briefing"] = briefing  # updated with corrections
            yield from self._process_execute(chat_id, session)

    # ------------------------------------------------------------------ #
    # EXECUTE phase
    # ------------------------------------------------------------------ #

    def _process_execute(
        self, chat_id: str, session: dict,
    ) -> Generator[dict, None, None]:
        """Execute phase: run_agent_loop with the approved briefing."""
        session["phase"] = "execute"
        yield {"type": "phase_change", "from": "review", "to": "execute"}

        briefing = session["briefing"]
        briefing_md = self._render_briefing_md(briefing)

        # Write briefing to temp file for agent_loop
        briefing_file = os.path.join(self.sandbox_dir, f"briefing_{chat_id[:8]}.md")
        with open(briefing_file, "w") as f:
            f.write(briefing_md)

        # Run agent_loop in a thread, streaming progress via queue
        progress_q: queue.Queue = queue.Queue()
        result_holder: list = [None]

        def _run():
            from core.agent_loop import run_agent_loop
            try:
                result = run_agent_loop(
                    goal=briefing_md,
                    mode="briefing",
                    project_dir=self.project_dir,
                    strategy=self.strategy,
                    forced_model=self.forced_model,
                    max_iterations=999,
                    max_cost=self.max_cost,
                    sandbox_dir=self.sandbox_dir,
                    verbose=False,
                    briefing_path=briefing_file,
                    autonomous=True,
                    on_progress=lambda i, total, msg: progress_q.put(
                        {"type": "execution_progress", "iteration": i, "max": total, "message": msg}
                    ),
                )
                result_holder[0] = result
            except Exception as e:
                result_holder[0] = {"error": str(e), "stop_reason": "ERROR"}
            finally:
                progress_q.put(None)  # sentinel

        thread = threading.Thread(target=_run, daemon=True)
        start_time = time.time()
        thread.start()

        # Stream progress events
        while True:
            try:
                event = progress_q.get(timeout=120)
            except queue.Empty:
                yield {"type": "execution_progress", "iteration": 0, "max": 30,
                       "message": "Still running..."}
                continue

            if event is None:
                break
            yield event

        thread.join(timeout=5)

        # Emit completion
        result = result_holder[0] or {}
        elapsed = time.time() - start_time

        session["phase"] = "done"

        yield {
            "type": "execution_complete",
            "result": result.get("stop_reason", "UNKNOWN"),
            "stop_reason": result.get("stop_reason", "UNKNOWN"),
            "files_changed": list(result.get("files_changed", [])),
            "cost": result.get("cost_usd", 0),
            "iterations": result.get("iterations", 0),
            "time_s": round(elapsed, 1),
        }
        yield {"type": "phase_change", "from": "execute", "to": "done"}

        # Update system prompt for post-execution chat
        session["history"][0]["content"] = self._build_system_prompt("done")

        # Flush tool evolution telemetry buffer
        try:
            from core.tool_evolution import get_tool_evolution
            get_tool_evolution().flush()
        except Exception:
            pass

        summary = session["budget"].summary()
        yield {
            "type": "status",
            "tokens": summary["tokens_used"],
            "cost": summary["cost_usd"],
            "model": TIER_CONFIG["tier3"].split("/")[-1],
        }

    # ------------------------------------------------------------------ #
    # DONE / free chat phase
    # ------------------------------------------------------------------ #

    def _process_chat(
        self, chat_id: str, session: dict, message: str,
    ) -> Generator[dict, None, None]:
        """Post-execution free chat — all tools available."""
        history = session["history"]
        registry = session["registry"]
        router = session["router"]
        budget = session["budget"]
        ctx_mgr = session["ctx_mgr"]
        tool_schemas = session["tool_schemas"]

        # Mode detection + task classification (Cambio 4)
        from core.router import detect_mode, MODE_CONFIGS
        mode = detect_mode(message)
        mode_config = MODE_CONFIGS[mode]
        session["mode_config"] = mode_config
        if hasattr(router, 'classify_task'):
            router.classify_task(message)
        if hasattr(router, 'set_mode'):
            router.set_mode(mode)

        # Auto-inject context before user message
        self._auto_inject_context(message, history)

        history.append({"role": "user", "content": message})

        import logging
        logger = logging.getLogger("chat")

        msg_start_time = time.time()

        # StuckDetector per message (Cambio 2)
        from core.budget import StuckDetector
        stuck = StuckDetector()
        stuck_reason = None

        for loop_i in range(mode_config.max_iterations):
            budget_err = budget.exceeded()
            if budget_err:
                yield {"type": "error", "content": f"Budget exceeded: {budget_err}"}
                break

            # Stuck detection (Cambio 2)
            stuck_reason = stuck.check()
            if stuck_reason:
                logger.warning(f"[loop {loop_i}] {stuck_reason}")
                yield {"type": "error", "content": f"Loop detectado: {stuck_reason}"}
                break

            # Timeout per message (Cambio 3)
            elapsed = time.time() - msg_start_time
            timeout_s = mode_config.timeout_s
            if elapsed > timeout_s:
                logger.warning(f"[loop {loop_i}] Timeout: {elapsed:.0f}s > {timeout_s}s")
                yield {"type": "error", "content": f"Timeout: {elapsed:.0f}s > {timeout_s}s"}
                break

            model = router.select()
            model_short = model.split("/")[-1] if "/" in model else model
            phase_tag = getattr(router, '_phase', 'unknown')
            logger.info(f"[loop {loop_i}] [{phase_tag}] calling {model} with {len(tool_schemas)} tools")
            yield {"type": "thinking", "step": loop_i + 1, "model": model_short, "phase": phase_tag}

            think_start = time.time()
            try:
                api_resp = call_with_retry(history, model, tools=tool_schemas, max_retries=2)
                logger.info(f"[loop {loop_i}] API response received from {model}")
            except RuntimeError as e:
                logger.warning(f"[loop {loop_i}] API error with {model}: {e}, trying fallback")
                # Escalation context (Cambio 6)
                esc_ctx = router.get_escalation_context() if hasattr(router, 'get_escalation_context') else ""
                if esc_ctx:
                    history.append({"role": "user", "content": f"[ESCALATION CONTEXT] {esc_ctx}"})
                try:
                    fallback = TIER_CONFIG.get("worker_budget", "xiaomi/mimo-v2-flash")
                    api_resp = call_with_retry(
                        history, fallback, tools=tool_schemas, max_retries=1
                    )
                    model = fallback
                    model_short = model.split("/")[-1] if "/" in model else model
                    logger.info(f"[loop {loop_i}] Fallback to {fallback} succeeded")
                except RuntimeError as e2:
                    logger.error(f"[loop {loop_i}] Fallback also failed: {e2}")
                    yield {"type": "error", "content": f"Error de API: {e}. Reintenta en unos segundos."}
                    break
            think_ms = int((time.time() - think_start) * 1000)

            usage = api_resp.get("usage", {})
            budget.track(usage, model)

            content, tool_calls, is_blowup = extract_response(api_resp)

            if is_blowup:
                router.on_blowup()
                stuck.record_no_tool()
                history.append({"role": "assistant", "content": content or "(empty)"})
                history.append({
                    "role": "user",
                    "content": "Please respond with text or use a tool.",
                })
                continue

            if not tool_calls:
                stuck.record_no_tool()
                if content:
                    history.append({"role": "assistant", "content": content})
                    yield {"type": "text", "content": content}
                break

            assistant_msg = {"role": "assistant", "content": content or ""}
            assistant_msg["tool_calls"] = tool_calls
            history.append(assistant_msg)

            if content:
                yield {"type": "text", "content": content}

            finished = False
            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                raw_args = tc["function"]["arguments"]
                if isinstance(raw_args, dict):
                    tool_args = raw_args
                else:
                    try:
                        tool_args = json.loads(raw_args)
                    except (json.JSONDecodeError, TypeError):
                        tool_args = {}

                tc_id = tc.get("id", f"call_{loop_i}")

                if tool_name == "finish":
                    result_text = tool_args.get("result", "Tarea completada.")
                    history.append({
                        "role": "tool",
                        "tool_call_id": tc_id,
                        "content": result_text,
                    })
                    yield {"type": "text", "content": result_text}
                    finished = True
                    break

                yield {"type": "tool_call", "name": tool_name, "args": tool_args,
                       "step": loop_i + 1, "model": model_short}

                # Sandwich pre-validation
                from core.sandwich import pre_validate_tool_call, post_validate_result
                is_valid, pre_error = pre_validate_tool_call(tool_name, tool_args, registry)
                tool_start = time.time()
                if not is_valid:
                    result_str, is_error = pre_error, True
                    tool_ms = 0
                else:
                    result_str, is_error = registry.execute(tool_name, tool_args)
                    tool_ms = int((time.time() - tool_start) * 1000)
                    result_str, is_error = post_validate_result(tool_name, result_str, is_error)

                # Code validation for write/edit (Cambio 9)
                if not is_error and tool_name in ("write_file", "edit_file"):
                    from core.sandwich import validate_code_output
                    code_valid, code_err = validate_code_output(tool_name, tool_args)
                    if not code_valid:
                        result_str = f"[CODE VALIDATION] {code_err}\n{result_str}"
                        is_error = True

                history.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "content": result_str,
                })

                elapsed_total = round(time.time() - msg_start_time, 1)
                yield {
                    "type": "tool_result",
                    "name": tool_name,
                    "result": result_str[:5000],
                    "is_error": is_error,
                    "duration_ms": tool_ms,
                    "step": loop_i + 1,
                    "cost_usd": round(budget.cost_usd, 4),
                    "elapsed_s": elapsed_total,
                }

                # Track tool use for cerebro/trabajador switching
                router.record_tool_use(tool_name)

                if is_error:
                    router.on_error(result_str)
                else:
                    router.on_success()

                # StuckDetector tracking (Cambio 2)
                stuck.record_action(tool_name, tool_args, result_str, is_error)

                # Tool Evolution telemetry (SN-03)
                try:
                    from core.tool_evolution import get_tool_evolution
                    get_tool_evolution().log_invocation(
                        tool_name=tool_name,
                        session_id=chat_id,
                        success=not is_error,
                        latency_ms=tool_ms,
                        error_message=result_str[:200] if is_error else None,
                        cost_usd=0.0,
                    )
                except Exception:
                    pass

            if finished:
                break

            # Update budget awareness in router
            router.update_budget(budget.cost_usd)

            history = ctx_mgr.maybe_compress(history)
            session["history"] = history

        # Flywheel feedback (Cambio 8)
        try:
            from core.flywheel import after_session, post_session_summary
            elapsed_total = round(time.time() - msg_start_time, 1)
            flywheel_data = {
                "stop_reason": stuck_reason or "DONE",
                "iterations": stuck.iteration,
                "time_s": elapsed_total,
                "cost_usd": round(budget.cost_usd, 4),
                "model_used": router.select(),
                "task_type": getattr(router, 'task_type', 'unknown'),
                "log": [],
            }
            after_session(post_session_summary(flywheel_data))
        except Exception:
            pass

        # Flush tool evolution telemetry buffer
        try:
            from core.tool_evolution import get_tool_evolution
            get_tool_evolution().flush()
        except Exception:
            pass

        summary = budget.summary()
        yield {
            "type": "status",
            "tokens": summary["tokens_used"],
            "cost": summary["cost_usd"],
            "model": model.split("/")[-1] if "/" in model else model,
        }

    # ------------------------------------------------------------------ #
    # Context auto-injection
    # ------------------------------------------------------------------ #

    def _auto_inject_context(self, message: str, history: list) -> None:
        """Lightweight context — skip short messages and avoid repeated lookups."""
        # Skip short messages (< 20 chars)
        if len(message.strip()) < 20:
            return
        # Skip if context was already injected recently
        if any("[CONTEXT PRE-FETCH" in str(m.get("content", "")) for m in history[-6:]):
            return
        try:
            from tools.remember import _search_knowledge_base
            stopwords = {"para", "como", "esto", "esta", "que", "los", "las",
                         "del", "por", "con", "una", "the", "and", "for", "with",
                         "from", "this", "that", "are", "was", "have", "has"}
            words = re.findall(r'\b\w{4,}\b', message.lower())
            keywords = [w for w in words if w not in stopwords][:3]
            if not keywords:
                return
            query = " ".join(keywords)
            result = _search_knowledge_base(query, limit=3)
            if result:
                context_msg = f"[CONTEXT PRE-FETCH for '{query}']\n{result}"
                history.append({"role": "user", "content": context_msg})
                history.append({"role": "assistant", "content": "(context loaded)"})
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _render_briefing_md(self, briefing: dict) -> str:
        """Convert briefing dict to markdown for the executor prompt."""
        lines = [f"# {briefing['title']}", "", f"## Objetivo", briefing["objective"], ""]

        if briefing.get("constraints"):
            lines.append("## Restricciones")
            for c in briefing["constraints"]:
                lines.append(f"- {c}")
            lines.append("")

        if briefing.get("files_to_create"):
            lines.append("## Archivos a crear")
            for f in briefing["files_to_create"]:
                lines.append(f"- `{f['path']}` — {f.get('purpose', '')}")
            lines.append("")

        if briefing.get("files_to_modify"):
            lines.append("## Archivos a modificar")
            for f in briefing["files_to_modify"]:
                lines.append(f"- `{f['path']}` — {f.get('changes', '')}")
            lines.append("")

        lines.append("## Tareas")
        for t in briefing["tasks"]:
            lines.append(f"### Paso {t.get('step', '?')}")
            lines.append(t.get("description", ""))
            if t.get("verification"):
                lines.append(f"**Verificacion:** {t['verification']}")
            lines.append("")

        if briefing.get("tests"):
            lines.append("## Tests")
            for t in briefing["tests"]:
                lines.append(f"- {t}")
            lines.append("")

        return "\n".join(lines)

    def _apply_correction(self, briefing: dict, correction: dict) -> None:
        """Apply a review correction to the briefing dict."""
        field = correction.get("field", "")
        corrected = correction.get("corrected", "")
        if not field or not corrected:
            return

        if field == "tasks" and isinstance(corrected, list):
            briefing["tasks"] = corrected
        elif field == "constraints" and isinstance(corrected, list):
            briefing["constraints"] = corrected
        elif field in ("files_to_create", "files_to_modify") and isinstance(corrected, list):
            briefing[field] = corrected
        elif field == "objective" and isinstance(corrected, str):
            briefing["objective"] = corrected
        elif field == "title" and isinstance(corrected, str):
            briefing["title"] = corrected

    def _load_project_context(self) -> str:
        """Read key project files to provide context for review."""
        context_parts = [
            "--- Stack ---",
            "Framework: Python + FastAPI (uvicorn)",
            "Database: PostgreSQL + pgvector (fly.io)",
            "LLM: OpenRouter + Anthropic API (dual path)",
            "Main API file: api.py (in /app/ on VM)",
            "DB access: psycopg2 with connection pooling (core/db_pool.py)",
            "The agent has db_query tool to inspect schemas at runtime.",
        ]
        key_files = [
            "CLAUDE.md", "README.md", "package.json", "pyproject.toml",
            "requirements.txt", "Cargo.toml", "go.mod",
        ]
        for fname in key_files:
            fpath = os.path.join(self.project_dir, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, "r", errors="replace") as f:
                        content = f.read(3000)
                    context_parts.append(f"--- {fname} ---\n{content}")
                except OSError:
                    pass

        # Also list top-level directory structure
        try:
            entries = os.listdir(self.project_dir)
            dirs = sorted(e for e in entries if os.path.isdir(os.path.join(self.project_dir, e)) and not e.startswith("."))
            files = sorted(e for e in entries if os.path.isfile(os.path.join(self.project_dir, e)) and not e.startswith("."))
            context_parts.append(f"--- Directory listing ---\nDirs: {', '.join(dirs[:20])}\nFiles: {', '.join(files[:20])}")
        except OSError:
            pass

        return "\n\n".join(context_parts) if context_parts else "(no project context available)"

    def _parse_review_response(self, content: str) -> Optional[dict]:
        """Parse JSON from review LLM response, tolerating markdown wrappers."""
        if not content:
            return None
        # Strip markdown code blocks if present
        text = content.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = lines[1:]  # remove ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return None

    def list_sessions(self) -> list:
        """Return list of sessions from DB (with fallback to in-memory)."""
        try:
            db_sessions = session_store.list_sessions(limit=20)
            if db_sessions:
                return db_sessions
        except Exception:
            pass
        # Fallback to in-memory
        return [
            {"id": cid, "title": s.get("title", "Sin título"),
             "phase": s.get("phase", "design")}
            for cid, s in self.sessions.items()
        ]

    def delete_session(self, chat_id: str) -> bool:
        """Delete a chat session from memory and DB."""
        if chat_id in self.sessions:
            del self.sessions[chat_id]
        if chat_id in self._access_order:
            self._access_order.remove(chat_id)
        try:
            return session_store.delete_session(chat_id)
        except Exception:
            return True

    def get_session_history(self, chat_id: str) -> list:
        """Get displayable history for a session (for frontend restore)."""
        # Check in-memory first
        if chat_id in self.sessions:
            history = self.sessions[chat_id].get("history", [])
            return [
                msg for msg in history
                if msg.get("role") in ("user", "assistant")
                and msg.get("content")
                and not msg["content"].startswith("[CONTEXT PRE-FETCH")
                and msg["content"] != "(context loaded)"
                and not msg["content"].startswith("[SYSTEM]")
            ]
        # Load from DB
        try:
            data = session_store.load_session(chat_id)
            if data:
                history = data.get("history", [])
                return [
                    msg for msg in history
                    if msg.get("role") in ("user", "assistant")
                    and msg.get("content")
                    and not msg["content"].startswith("[CONTEXT PRE-FETCH")
                    and msg["content"] != "(context loaded)"
                    and not msg["content"].startswith("[SYSTEM]")
                ]
        except Exception:
            pass
        return []
