"""Code OS v3 — Main agent loop: observe-think-act with cerebro/trabajador split."""

import os
import sys
import json
import time
from typing import Optional

from .api import (
    TIER_CONFIG, OPENROUTER_KEY, call_with_retry, extract_response,
)
from .budget import Budget, StuckDetector, ProgressTracker
from .recovery import RecoveryEngine
from .router import TieredRouter, SmartRouter, DualModelRouter, ReasoningCouncil, detect_mode, MODE_CONFIGS
from .context import ContextManager
from .sandwich import pre_validate_tool_call, post_validate_result, validate_code_output, post_session_summary
from .drift_guard import check_drift, check_file_drift
from .monitoring import get_circuit_breaker, get_monitor

# Tool evolution telemetry (lazy)
_tool_evo = None

def _get_tool_evo():
    global _tool_evo
    if _tool_evo is None:
        try:
            from .tool_evolution import get_tool_evolution
            _tool_evo = get_tool_evolution()
        except Exception as _e:
            print(f"[WARN:agent_loop.tool_evo_init] {type(_e).__name__}: {_e}")
    return _tool_evo

# Lazy imports to avoid circular deps
_registry = None
_persistence = None

TOTAL_TIMEOUT = 600

TOOL_DESCRIPTIONS = {
    "read_file": "read_file(path) — lee archivos. SIEMPRE @project/ para proyecto",
    "edit_file": "edit_file(path, old_string, new_string) — edita archivos existentes",
    "write_file": "write_file(path, content) — crea archivos NUEVOS",
    "list_dir": "list_dir(path) — lista directorio",
    "run_command": "run_command(command) — ejecuta shell",
    "db_query": "db_query(sql) — consulta DB (solo SELECT)",
    "http_request": "http_request(method, url) — llamadas HTTP",
    "search_files": "search_files(pattern) — busca archivos por patrón",
    "finish": "finish(result) — TERMINAR con resultado. PON TU RESPUESTA AQUÍ.",
    "mochila": "mochila() — contexto del proyecto (máx 3 llamadas)",
}

CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. SIEMPRE en ESPAÑOL.

HERRAMIENTAS DISPONIBLES (usa SOLO estas, ninguna más):
{tools_section}

RUTAS: @project/ = proyecto real. Sin prefijo = sandbox temporal.

CÓMO TRABAJAR:
1. ¿Qué necesito saber? → usa las herramientas de lectura disponibles
2. ¿Necesito cambiar algo? → edit_file, write_file, run_command
3. ¿Ya tengo la respuesta? → finish(result='mi respuesta completa')

REGLA: Tu análisis va DENTRO de finish(result='...'), no como texto suelto.
Si solo te piden leer/analizar: lee → finish(result='lo que encontré').

{context_section}
"""

BRIEFING_EXECUTOR_PROMPT = """EJECUTA este briefing. Cada paso se EJECUTA, no se describe.

BRIEFING:
{briefing_content}

PROTOCOLO:
- SQL → db_insert(). Archivos → write_file(@project/...) o edit_file(@project/...).
- Tras cada paso → VERIFICAR (db_query, run_command).
- Al terminar → finish(result='resumen de lo ejecutado').
"""


def run_agent_loop(
    goal: str,
    mode: str = "goal",
    project_dir: str = ".",
    strategy: str = "tiered",
    forced_model: Optional[str] = None,
    max_iterations: int = 999,
    max_cost: float = 15.0,
    sandbox_dir: Optional[str] = None,
    verbose: bool = False,
    vision_text: Optional[str] = None,
    briefing_path: Optional[str] = None,
    autonomous: bool = True,
    context_prompt: str = "",
    session_id: str = "",
    db=None,
    registry=None,
    hooks=None,
    on_progress=None,
) -> dict:
    """Main Code OS v2 execution loop.

    Args:
        goal: Task description
        mode: "goal", "vision", or "briefing"
        project_dir: Project root directory
        strategy: "solo" or "tiered"
        forced_model: Force specific model
        max_iterations: Max agent iterations
        max_cost: Budget in USD
        sandbox_dir: Workspace directory
        verbose: Log each iteration
        vision_text: Non-technical vision (mode=vision)
        briefing_path: Path to briefing (mode=briefing)
        autonomous: If True, never ask user
        context_prompt: Pre-loaded project context
        session_id: Supabase session ID
        db: SupabaseClient instance
        registry: ToolRegistry instance
        hooks: HookRegistry instance
        on_progress: Callback(iteration, total, message)
    """
    from tools import create_default_registry
    from tools.meta import set_autonomous
    from .costes import set_call_context
    from .mochila import reset_mochila

    reset_mochila()
    set_autonomous(autonomous)
    set_call_context(componente='agent_loop', operacion='ejecucion', caso_id=session_id or goal[:20])

    if sandbox_dir is None:
        import tempfile
        sandbox_dir = tempfile.mkdtemp(prefix="code_os_")
    os.makedirs(sandbox_dir, exist_ok=True)

    # Initialize components
    if registry is None:
        registry = create_default_registry(sandbox_dir, project_dir)

    router = SmartRouter(strategy=strategy, forced_model=forced_model)
    router.classify_task(goal)
    if hasattr(router, 'set_budget'):
        router.set_budget(max_cost)

    # Detect execution mode (Quick/Standard/Deep — pattern 60666)
    exec_mode = detect_mode(goal)
    if hasattr(router, 'set_mode'):
        router.set_mode(exec_mode)
    mode_cfg = MODE_CONFIGS.get(exec_mode, MODE_CONFIGS["standard"])
    max_iterations = min(max_iterations, mode_cfg.max_iterations)

    council = ReasoningCouncil()
    budget = Budget(max_iterations=max_iterations, max_cost_usd=max_cost)
    stuck = StuckDetector()
    progress = ProgressTracker(goal)
    recovery = RecoveryEngine()
    ctx_mgr = ContextManager()

    # Get tool schemas — filtered by execution mode
    CORE_TOOLS = {
        "read_file", "edit_file", "write_file", "list_dir",
        "run_command", "finish", "mochila",
    }
    MODE_TOOLS = {
        "quick": CORE_TOOLS,
        "execute": CORE_TOOLS | {"http_request", "run_command"},
        "analyze": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "standard": CORE_TOOLS | {"http_request", "db_query", "search_files"},
        "deep": CORE_TOOLS | {"http_request", "db_query", "search_files",
                               "remember_search", "plan"},
    }
    active_tools = MODE_TOOLS.get(exec_mode, CORE_TOOLS | {"http_request", "db_query"})
    tool_schemas = registry.get_schemas(names=active_tools)

    # Fallback: si el filtro dejó <3 tools, usar todo (safety net)
    if len(tool_schemas) < 3:
        tool_schemas = registry.get_schemas()

    # === DIAGNOSTIC LOGGING (B18) — eliminar cuando T3 pase ===
    _filtered_names = [s["function"]["name"] for s in tool_schemas]
    print(f"[DIAG:B18] exec_mode={exec_mode} | goal_start='{goal[:60]}' | "
          f"tools_count={len(tool_schemas)} | "
          f"tools={_filtered_names[:15]} | "
          f"safety_net={'YES' if len(tool_schemas) > len(active_tools) + 5 else 'NO'}")
    # === END DIAGNOSTIC ===

    # Build dynamic tools section — ONLY list tools that are in the filtered schema
    _schema_names = {s["function"]["name"] for s in tool_schemas}
    _tools_lines = []
    for tname in ["read_file", "edit_file", "write_file", "list_dir", "run_command",
                   "db_query", "http_request", "search_files", "finish", "mochila"]:
        if tname in _schema_names and tname in TOOL_DESCRIPTIONS:
            _tools_lines.append(f"- {TOOL_DESCRIPTIONS[tname]}")
    _tools_section = "\n".join(_tools_lines) if _tools_lines else "- finish(result)"

    # Build system prompt
    system = CODE_OS_SYSTEM.format(
        tools_section=_tools_section,
        context_section=f"PROJECT CONTEXT:\n{context_prompt}" if context_prompt else ""
    )

    # Handle briefing mode
    if mode == "briefing" and briefing_path:
        from pathlib import Path
        briefing_content = Path(briefing_path).read_text(errors='replace')
        goal = BRIEFING_EXECUTOR_PROMPT.format(briefing_content=briefing_content[:30000])

    # Mode-specific hints — guían al modelo sobre QUÉ herramientas usar
    MODE_HINTS = {
        "execute": (
            "\n\nPROTOCOLO EXECUTE: Esta tarea requiere MODIFICAR CÓDIGO. "
            "Flujo obligatorio: "
            "1) read_file(@project/archivo) para ver el código actual, "
            "2) edit_file(@project/archivo, old_string, new_string) para hacer cambios, "
            "3) run_command() o finish() para verificar/completar."
        ),
        "analyze": "",  # V3.2 ya maneja analyze bien (B14: 5/6 keywords)
        "quick": "",
        "standard": "",
        "deep": "",
    }
    mode_hint = MODE_HINTS.get(exec_mode, "")

    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"TASK:\n{goal}\n\n"
            f"Workspace: {sandbox_dir}\n"
            f"Runtimes: python3, pytest, deno, node.\n"
            f"Tools available: {len(tool_schemas)}"
            f"{mode_hint}\n"
            f"Start by understanding the task, then plan and implement."
        )},
    ]

    log = []
    start_time = time.time()
    stop_reason = None
    final_result = None
    files_changed = set()
    _finish_nudged = False  # Finish gate: nudge once before accepting early finish

    # Metacognitive FOK: estimate confidence BEFORE execution
    fok_result = {}
    try:
        from .metacognitive import get_metacognitive
        meta = get_metacognitive()
        fok_result = meta.feeling_of_knowing(goal, 'CodeOS_execution')
    except Exception:
        fok_result = {'fok': 0.5, 'error': 'fok_unavailable'}

    # Cache Tier 0 — lookup puro, sin LLM (pattern 60661)
    try:
        from .cache_tier import try_cache
        cached = try_cache(goal)
        if cached:
            return {
                "session_id": session_id,
                "result": f"[CACHE HIT: {cached['source']}] {cached['data'].get('result_preview', '')}",
                "stop_reason": "CACHE_HIT",
                "iterations": 0,
                "tokens_used": 0,
                "cost_usd": 0.0,
                "time_s": round(time.time() - start_time, 1),
                "sandbox_dir": sandbox_dir,
                "files_changed": [],
                "model_used": "cache_tier_0",
                "task_type": "cached",
                "compressions": 0,
                "phase_info": {"mode": exec_mode},
                "log": [],
            }
    except Exception as _e:
        print(f"[WARN:agent_loop.cache_init] {type(_e).__name__}: {_e}")

    for iteration in range(max_iterations):
        elapsed = time.time() - start_time
        effective_timeout = mode_cfg.timeout_s if mode_cfg else TOTAL_TIMEOUT
        if elapsed > effective_timeout:
            stop_reason = f"TIMEOUT ({effective_timeout}s)"
            break

        budget_err = budget.exceeded()
        if budget_err:
            stop_reason = budget_err
            break

        stuck_reason = stuck.check()
        if stuck_reason:
            # Try reflection before giving up
            if router.should_reflect():
                hint = router.reflect(stuck.error_history, history)
                if hint:
                    history.append({"role": "user", "content": hint})
                    stuck.error_history.clear()
                    stuck.no_tool_streak = 0
                    continue
            stop_reason = stuck_reason
            break

        # Update router budget awareness
        if hasattr(router, 'update_budget'):
            router.update_budget(budget.cost_usd)

        model = router.select()
        iter_start = time.time()

        # Escalation context preservation (Tiers Adaptativos 60670)
        if hasattr(router, 'get_escalation_context'):
            esc_ctx = router.get_escalation_context()
            if esc_ctx:
                history.append({"role": "user", "content": esc_ctx})

        phase_tag = ""
        if hasattr(router, '_phase'):
            phase_tag = f" [{router._phase}]"

        if verbose:
            print(f"  [{iteration+1}/{max_iterations}]{phase_tag} model={model.split('/')[-1]}",
                  end="", flush=True)

        if on_progress:
            on_progress(iteration + 1, max_iterations,
                        f"iter {iteration+1}, model={model.split('/')[-1]}")

        # Run pre_iteration hooks (drift guard injects warnings/abort here)
        pre_iter_ctx = {"iteration": iteration, "model": model, "history": history}
        if hooks:
            hooks.run("pre_iteration", pre_iter_ctx)
        if pre_iter_ctx.get("_drift_abort"):
            stop_reason = "DRIFT_ABORT"
            break

        # Circuit Breaker: check model availability before calling
        breaker = get_circuit_breaker()
        if not breaker.puede_llamar(model):
            model = breaker.get_modelo_fallback(model)

        # Call model
        try:
            api_resp = call_with_retry(history, model, tools=tool_schemas)
            breaker.registrar_exito(model)
        except RuntimeError as e:
            breaker.registrar_fallo(model)
            try:
                fallback = TIER_CONFIG.get("worker_budget", TIER_CONFIG.get("tier2b", "deepseek/deepseek-v3.2"))
                api_resp = call_with_retry(history, fallback, tools=tool_schemas, max_retries=1)
                breaker.registrar_exito(fallback)
                model = fallback
            except RuntimeError:
                breaker.registrar_fallo(fallback)
                stop_reason = f"API_FAILURE: {e}"
                break

        usage = api_resp.get("usage", {})
        budget.track(usage, model)
        content, tool_calls, is_blowup = extract_response(api_resp)
        iter_ms = int((time.time() - iter_start) * 1000)

        # Reasoning blowup
        if is_blowup:
            if verbose:
                print(f" (BLOWUP)")
            router.on_blowup()
            history.append({"role": "assistant", "content": content or "(empty)"})
            history.append({"role": "user", "content": "USE A TOOL NOW. Start with list_dir('.')."})
            stuck.record_no_tool()
            if db:
                db.log_iteration(session_id, iteration, model, tool_called="(blowup)",
                               is_error=True, tokens_in=usage.get("prompt_tokens", 0),
                               tokens_out=usage.get("completion_tokens", 0),
                               cost_usd=budget.cost_usd, duration_ms=iter_ms)
            history = ctx_mgr.maybe_compress(history)
            continue

        # No tool calls — monologue
        if not tool_calls:
            if verbose:
                print(f" (no tool)")
            history.append({"role": "assistant", "content": content or "(empty)"})
            stuck.record_no_tool()
            if stuck.no_tool_streak == 2:
                # EXTRAER: pregunta que fuerza síntesis de lo encontrado
                history.append({"role": "user", "content": (
                    "¿Qué has encontrado hasta ahora? "
                    "¿Es suficiente para responder la tarea original? "
                    "Si sí → llama finish(result='tu conclusión'). "
                    "Si no → ¿qué dato te falta?"
                )})
            elif stuck.no_tool_streak == 3:
                # INTEGRAR: pregunta que empuja a formular conclusión
                history.append({"role": "user", "content": (
                    "Formula tu conclusión en UNA frase. "
                    "Luego llama finish(result='esa frase')."
                )})
            elif stuck.no_tool_streak >= 4:
                # FRONTERA: safety net mecánico — auto-finish con el texto del modelo
                last_text = content or ""
                if len(last_text) > 50:
                    stop_reason = "AUTO_FINISH"
                    final_result = last_text[:2000]
                    break
                else:
                    router.on_blowup()
                    history.append({"role": "user", "content": "Llama finish(result='...') ahora."})

            if db:
                db.log_iteration(session_id, iteration, model, tool_called="(monologue)",
                               tokens_in=usage.get("prompt_tokens", 0),
                               tokens_out=usage.get("completion_tokens", 0),
                               duration_ms=iter_ms)
            history = ctx_mgr.maybe_compress(history)
            continue

        # Process tool calls
        assistant_msg = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        history.append(assistant_msg)

        for tc in tool_calls:
            tool_name = tc["function"]["name"]
            try:
                tool_args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, TypeError):
                tool_args = {}

            tc_id = tc.get("id", f"call_{iteration}")

            # Run pre_tool hooks
            if hooks:
                hooks.run("pre_tool", {"tool": tool_name, "args": tool_args})

            # Handle finish — with goal verification (CRITERIO check)
            if tool_name == "finish":
                final_result = tool_args.get("result", "Task completed")

                # Goal verification: extract and run CRITERIO command
                finish_accepted = True
                if "CRITERIO:" in goal:
                    import re as _re
                    criterio_match = _re.search(r'CRITERIO:\s*(.+)', goal)
                    if criterio_match:
                        criterio_cmd = criterio_match.group(1).strip()
                        cmd_prefixes = ("python3", "grep", "curl", "db_query", "cat", "ls", "test")
                        if any(criterio_cmd.startswith(p) for p in cmd_prefixes):
                            try:
                                check_result, check_error = registry.execute("run_command", {"command": criterio_cmd})
                                if check_error:
                                    finish_accepted = False
                                    history.append({"role": "tool", "tool_call_id": tc_id,
                                                    "content": f"Finish rejected: criterio no cumplido. "
                                                               f"Resultado del check: {check_result}. Reintenta."})
                                    if verbose:
                                        print(f" -> finish REJECTED: criterio failed")
                            except Exception:
                                pass  # If check fails to run, accept finish

                # Finish gate: nudge once if >80% iterations remain AND <5 successful actions
                if finish_accepted and not _finish_nudged:
                    remaining_ratio = (max_iterations - iteration) / max_iterations
                    successful_actions = sum(1 for e in log if isinstance(e, dict) and not e.get("is_error"))
                    if remaining_ratio > 0.8 and successful_actions < 5:
                        _finish_nudged = True
                        finish_accepted = False
                        history.append({"role": "tool", "tool_call_id": tc_id,
                                        "content": "¿Terminaste? Si todo OK → finish() de nuevo."})
                        if verbose:
                            print(f" -> finish NUDGED: >80% iterations remain, <5 actions")

                if finish_accepted:
                    history.append({"role": "tool", "tool_call_id": tc_id, "content": final_result})
                    stop_reason = "DONE"
                    if verbose:
                        print(f" -> finish: {final_result[:80]}")
                    if db:
                        db.log_iteration(session_id, iteration, model, tool_called="finish",
                                       tool_args=tool_args, tool_result=final_result,
                                       tokens_in=usage.get("prompt_tokens", 0),
                                       tokens_out=usage.get("completion_tokens", 0),
                                       duration_ms=iter_ms)
                    break
                else:
                    continue

            # DRIFT DETECTION — file path check for write/edit tools
            if tool_name in ("write_file", "edit_file", "create_tool"):
                file_arg = tool_args.get("path", "")
                file_drift = check_file_drift(file_arg, project_dir)
                if file_drift:
                    history.append({
                        "role": "tool", "tool_call_id": tc_id,
                        "content": f"DRIFT DETECTED: {file_drift}. "
                                   f"Stop and verify your working directory.",
                    })
                    stuck.record_no_tool()
                    continue

            # DRIFT DETECTION — content check
            drift_reason = check_drift(content or "", project_dir)
            if drift_reason:
                history.append({
                    "role": "user",
                    "content": f"DRIFT DETECTED: {drift_reason}. "
                               f"Refocus on the current step.",
                })
                router.on_error(drift_reason)
                continue

            # SANDWICH PRE-VALIDATION (deterministic layer before LLM tool call)
            is_valid, pre_error = pre_validate_tool_call(tool_name, tool_args, registry)
            if not is_valid:
                result_str, is_error = pre_error, True
                tool_latency = 0
            else:
                # Code validation for write/edit (pattern 60675)
                if tool_name in ("write_file", "edit_file"):
                    code_ok, code_err = validate_code_output(tool_name, tool_args)
                    if not code_ok:
                        result_str, is_error = code_err, True
                        tool_latency = 0
                        history.append({"role": "tool", "tool_call_id": tc_id, "content": result_str})
                        stuck.record_action(tool_name, tool_args, result_str, is_error)
                        continue
                # Execute tool via registry (with telemetry)
                tool_start = time.time()
                result_str, is_error = registry.execute(tool_name, tool_args)
                tool_latency = int((time.time() - tool_start) * 1000)
                # SANDWICH POST-VALIDATION (normalize output, detect hidden errors)
                result_str, is_error = post_validate_result(tool_name, result_str, is_error)
            history.append({"role": "tool", "tool_call_id": tc_id, "content": result_str})

            # Log to tool evolution telemetry
            evo = _get_tool_evo()
            if evo:
                try:
                    evo.log_invocation(
                        tool_name=tool_name,
                        session_id=session_id,
                        success=not is_error,
                        latency_ms=tool_latency,
                        error_message=result_str[:500] if is_error else None,
                        context={"iteration": iteration, "model": model},
                    )
                except Exception as _e:
                    print(f"[WARN:agent_loop.tool_telemetry] {type(_e).__name__}: {_e}")

            if verbose:
                status = "ERR" if is_error else "OK"
                print(f" -> {tool_name}({status}): {result_str[:60].replace(chr(10), ' ')}")

            stuck.record_action(tool_name, tool_args, result_str, is_error)
            progress.record_action(tool_name, result_str, is_error)
            if progress.stagnant():
                history.append({"role": "user", "content":
                    "WARNING: You are repeating the same actions. Try a different approach."})

            # Notify dual-model router of tool use (cerebro/trabajador switching)
            if hasattr(router, 'record_tool_use'):
                router.record_tool_use(tool_name)

            # Reasoning Council — validate complex plans before execution
            if (tool_name == "plan" and not is_error
                    and tool_args.get("action") == "write"
                    and len(result_str) > 500
                    and council.should_convene(
                        getattr(router, 'task_type', ''),
                        getattr(router, 'consecutive_failures', 0))):
                try:
                    verdict = council.convene(result_str, goal)
                    if verdict["verdict"] == "needs_revision":
                        # Inject council feedback into conversation
                        council_msg = (
                            f"[REASONING COUNCIL] Plan needs revision.\n"
                            f"Math check: {verdict['votes'].get('math_check', 'N/A')}\n"
                            f"Code check: {verdict['votes'].get('code_check', 'N/A')}\n"
                            f"Synthesis: {verdict.get('synthesis', 'N/A')}\n"
                            f"Revise your plan based on this feedback."
                        )
                        history.append({"role": "user", "content": council_msg})
                    budget.track({"prompt_tokens": 0, "completion_tokens": 0},
                                 "council", override_cost=verdict.get("cost_usd", 0))
                except Exception as _e:
                    print(f"[WARN:agent_loop.council] {type(_e).__name__}: {_e}")

            if is_error:
                router.on_error(result_str)
                # Detect tool gap if unknown tool
                if "Unknown tool" in result_str and evo:
                    try:
                        evo.detect_gap(
                            description=f"Tool '{tool_name}' requested but not found",
                            attempted_tools=[tool_name],
                            failure_reason=result_str[:200],
                        )
                    except Exception as _e:
                        print(f"[WARN:agent_loop.tool_gap] {type(_e).__name__}: {_e}")

                # Recovery engine: decide action based on error context
                last_write = recovery.last_writes[-1][1] if recovery.last_writes else None
                decision = recovery.decide(
                    stuck.error_history, tool_name, goal, last_write=last_write,
                )
                action = decision["action"]
                if action == "retry_different" and decision.get("hint"):
                    history.append({"role": "user", "content":
                        f"Hint: {decision['hint'][:100]}"})
                elif action == "escalate":
                    router.on_error(f"RECOVERY_ESCALATE: {decision['reason']}")
                elif action == "rollback" and recovery._git_checkpoints:
                    rolled = recovery.rollback(sandbox_dir)
                    if rolled:
                        history.append({"role": "user", "content":
                            f"Rollback a {rolled[:8]}. Prueba diferente enfoque."})
                elif action == "decompose":
                    if recovery.should_decompose(stuck.error_history, stuck.iteration, max_iterations):
                        sub_goals = recovery.decompose(goal, result_str)
                        history.append({"role": "user", "content":
                            f"Error repetido. Simplifica: {sub_goals[0] if sub_goals else 'siguiente paso'}"})
                elif action == "skip":
                    history.append({"role": "user", "content":
                        f"Salta esto: {decision['reason'][:80]}. Siguiente paso."})
                # abort is handled by StuckDetector

            else:
                router.on_success()
                if tool_name == "run_command" and any(kw in result_str for kw in
                        ["FAILED", "failed", "Error", "AssertionError"]):
                    router.on_test_failure()

            # Track file changes + recovery write tracking
            if tool_name in ("write_file", "edit_file") and not is_error:
                fpath = tool_args.get("path", "")
                files_changed.add(fpath)
                recovery.record_write(tool_name, fpath)
                if db:
                    action = "create" if tool_name == "write_file" else "edit"
                    db.log_file_change(session_id, fpath, action, iter_n=iteration)

            # Run post_tool hooks
            post_tool_ctx = {"tool": tool_name, "args": tool_args,
                             "result": result_str, "is_error": is_error}
            if hooks:
                hooks.run("post_tool", post_tool_ctx)
            # Record checkpoint hash from git_checkpoint_hook for rollback
            if post_tool_ctx.get("_checkpoint_hash"):
                recovery.record_checkpoint(post_tool_ctx["_checkpoint_hash"])

            # Log iteration
            if db:
                db.log_iteration(session_id, iteration, model,
                               tool_called=tool_name, tool_args=tool_args,
                               tool_result=result_str[:2000], is_error=is_error,
                               tokens_in=usage.get("prompt_tokens", 0),
                               tokens_out=usage.get("completion_tokens", 0),
                               cost_usd=budget.cost_usd, duration_ms=iter_ms)

            log.append({
                "iter": iteration + 1, "tool": tool_name, "model": model,
                "is_error": is_error, "tokens": usage.get("total_tokens", 0),
            })

        # Monitor: register execution metrics at end of each iteration
        try:
            monitor = get_monitor()
            monitor.registrar_ejecucion({
                'latencia_total_s': (time.time() - iter_start),
                'coste_total_usd': budget.cost_usd,
                'error': stop_reason if stop_reason else None,
                'modo': exec_mode,
                'tier': getattr(router, '_phase', 'unknown'),
                'n_inteligencias': len(tool_calls) if tool_calls else 0,
            })
        except Exception as _e:
            print(f"[WARN:agent_loop.monitoring] {type(_e).__name__}: {_e}")

        if stop_reason:
            break

        history = ctx_mgr.maybe_compress(history)

    # Flush telemetry buffer
    evo = _get_tool_evo()
    if evo and hasattr(evo, 'flush'):
        try:
            evo.flush()
        except Exception as _e:
            print(f"[WARN:agent_loop.evo_flush] {type(_e).__name__}: {_e}")

    # Telemetry (SN-03)
    total_time = time.time() - start_time
    try:
        from core.telemetria import registrar_metrica
        registrar_metrica('code_os', 'ejecucion', {
            'session_id': session_id,
            'modo': mode,
            'iteraciones': iteration if 'iteration' in dir() else 0,
            'tokens_usados': budget.tokens_used,
            'coste_usd': budget.cost_usd,
            'tiempo_s': round(total_time, 1),
            'modelo_usado': router.select(),
            'tarea_tipo': router.task_type if hasattr(router, 'task_type') else 'unknown',
            'archivos_cambiados': len(files_changed),
            'compresiones': ctx_mgr.compression_count,
            'exito': stop_reason == 'DONE',
        })
    except Exception as _e:
        print(f"[WARN:agent_loop.telemetria] {type(_e).__name__}: {_e}")

    # Metacognitive JOL: evaluate quality AFTER execution
    jol_result = {}
    try:
        from .metacognitive import get_metacognitive
        meta = get_metacognitive()
        jol_result = meta.judgment_of_learning({
            'tasa_cierre': 1.0 if stop_reason == "DONE" else 0.0,
            'hallazgos': log,
            'latencia_ms': int(total_time * 1000),
            'coste_usd': budget.cost_usd,
            'celda_objetivo': 'CodeOS_execution',
        })
    except Exception:
        jol_result = {'jol': 0.5, 'error': 'jol_unavailable'}

    # Flywheel feedback (pattern 60668) — close the loop
    flywheel_promotion = None
    try:
        from .flywheel import after_session, check_promotion
        result_for_flywheel = {
            "stop_reason": stop_reason or "MAX_ITERATIONS",
            "iterations": stuck.iteration,
            "time_s": round(total_time, 1),
            "cost_usd": round(budget.cost_usd, 4),
            "model_used": router.select(),
            "success": stop_reason == "DONE",
            "task_type": router.task_type if hasattr(router, 'task_type') else "unknown",
            "phase_info": router.get_phase_info() if hasattr(router, 'get_phase_info') else {},
            "error_rate": progress.get_signal().get("error_rate", 0),
            "mode": exec_mode,
            "log": log,
        }
        summary = post_session_summary(result_for_flywheel)
        after_session(summary)
        flywheel_promotion = check_promotion()
    except Exception as _e:
        print(f"[WARN:agent_loop.flywheel] {type(_e).__name__}: {_e}")

    # Auto-learning: persist successful sessions with file changes
    if stop_reason == "DONE" and files_changed:
        try:
            from tools.remember import tool_remember_save
            tool_remember_save(
                title=f"session: {goal[:80]}",
                content=f"Archivos: {', '.join(list(files_changed)[:10])}\nResultado: {(final_result or '')[:500]}",
                category="session_log",
            )
        except Exception as _e:
            print(f"[WARN:agent_loop.auto_learning] {type(_e).__name__}: {_e}")

    # Cache save — store successful short executions for Tier 0 (pattern 60661)
    if stop_reason == "DONE" and stuck.iteration <= 5:
        try:
            from .cache_tier import save_to_cache
            tool_seq = [e for e in log if isinstance(e, dict) and e.get("tool")]
            save_to_cache(goal, tool_seq, final_result or "", True)
        except Exception as _e:
            print(f"[WARN:agent_loop.cache_save] {type(_e).__name__}: {_e}")

    # Finalize

    if db:
        db.log_result(
            session_id=session_id,
            total_cost_usd=round(budget.cost_usd, 4),
            total_time_s=round(total_time, 1),
            total_tokens=budget.tokens_used,
            total_iterations=stuck.iteration,
            stop_reason=stop_reason or "MAX_ITERATIONS",
            files_changed=list(files_changed),
        )
        db.log_session_end(session_id, status="completed" if stop_reason == "DONE" else "failed")

    # Phase info from dual-model router
    phase_info = router.get_phase_info() if hasattr(router, 'get_phase_info') else {}

    # Session diagnostics
    diagnostics = {
        "error_counts": dict(recovery.error_counts),
        "total_errors": sum(recovery.error_counts.values()),
        "recoveries_attempted": len(recovery.last_errors),
        "rollbacks": len([c for c in recovery._git_checkpoints]),  # remaining checkpoints
        "files_written": len(recovery.last_writes),
        "stuck_checks": {
            "loop_detected": stuck.detect_loop() is not None,
            "regression_detected": stuck.detect_regression() is not None,
        },
        "progress": progress.get_signal(),
        "circuit_breaker": get_circuit_breaker().get_estados(),
        "monitor_slos": get_monitor().check_slos(),
        "monitor_budget": get_monitor().check_budget(),
        "metacognitive": {
            "fok": fok_result,
            "jol": jol_result,
        },
    }

    return {
        "session_id": session_id,
        "result": final_result,
        "stop_reason": stop_reason or "MAX_ITERATIONS",
        "iterations": stuck.iteration,
        "tokens_used": budget.tokens_used,
        "cost_usd": round(budget.cost_usd, 4),
        "time_s": round(total_time, 1),
        "sandbox_dir": sandbox_dir,
        "files_changed": list(files_changed),
        "model_used": router.select(),
        "task_type": router.task_type if hasattr(router, 'task_type') else "unknown",
        "compressions": ctx_mgr.compression_count,
        "phase_info": phase_info,
        "diagnostics": diagnostics,
        "flywheel_promotion": flywheel_promotion,
        "log": log,
    }


# =====================================================
# RUN BRIEFING — multi-step execution with fresh context
# =====================================================

def run_briefing(briefing_path: str, project_dir: str = ".",
                 max_cost_per_step: float = 2.0,
                 verbose: bool = False, db=None,
                 verify_tier: str = "fast") -> dict:
    """Execute a multi-step briefing. Each step = fresh context.

    Args:
        verify_tier: "fast" (deterministic), "standard" (+ Cogito), "deep" (+ panel)
    """
    from .briefing_parser import parse_briefing
    from .drift_guard import reset_drift_state

    briefing = parse_briefing(briefing_path)
    results = []

    # Initialize verifier
    verifier = None
    try:
        from .verifier import Verifier
        verifier = Verifier(verify_tier)
    except Exception:
        pass

    for step in briefing.steps:
        reset_drift_state()

        goal = (
            f"PASO {step.number}: {step.description}\n"
            f"REPO: {step.repo_dir}\n"
            f"ARCHIVOS: {', '.join(step.files)}\n"
            f"INSTRUCCION:\n{step.instruction}\n"
            f"CRITERIO: {step.success_criteria}"
        )

        result = run_agent_loop(
            goal=goal,
            mode="goal",
            project_dir=step.repo_dir,
            max_iterations=999,
            max_cost=max_cost_per_step,
            autonomous=True,
            verbose=verbose,
            db=db,
        )

        step_result = {
            "step": step.number,
            "description": step.description,
            "status": result.get("stop_reason", "unknown"),
            "iterations": result.get("iterations", 0),
            "cost": result.get("cost_usd", 0),
        }

        # Verify step if verifier available
        if verifier:
            try:
                verification = verifier.verify_step(step, result)
                step_result["verification"] = verification
                if not verification.get("passed") and verbose:
                    print(f"  [VERIFIER] Step {step.number} verification failed: "
                          f"{verification.get('issues', [])}")
            except Exception:
                pass

        results.append(step_result)

        if result.get("stop_reason") != "DONE":
            results[-1]["error"] = result.get("result") or "Step did not complete"
            break

    all_passed = all(r["status"] == "DONE" for r in results) and len(results) == len(briefing.steps)

    # Post-briefing verification
    briefing_result = {
        "briefing": briefing.title,
        "steps_total": len(briefing.steps),
        "steps_completed": len(results),
        "all_passed": all_passed,
        "results": results,
        "total_cost": sum(r["cost"] for r in results),
    }

    briefing_verification = None
    if verifier:
        try:
            briefing_verification = verifier.verify_briefing(briefing_result, {})
        except Exception:
            pass

    briefing_result["verification"] = briefing_verification
    return briefing_result
