"""Code OS v3 — Main agent loop: observe-think-act with cerebro/trabajador split."""

import os
import sys
import json
import time
from typing import Optional

from .api import (
    TIER_CONFIG, OPENROUTER_KEY, call_with_retry, extract_response,
)
from .budget import Budget, StuckDetector
from .router import TieredRouter, SmartRouter, DualModelRouter, ReasoningCouncil, detect_mode, MODE_CONFIGS
from .context import ContextManager
from .sandwich import pre_validate_tool_call, post_validate_result, validate_code_output, post_session_summary

# Tool evolution telemetry (lazy)
_tool_evo = None

def _get_tool_evo():
    global _tool_evo
    if _tool_evo is None:
        try:
            from .tool_evolution import get_tool_evolution
            _tool_evo = get_tool_evolution()
        except Exception:
            pass
    return _tool_evo

# Lazy imports to avoid circular deps
_registry = None
_persistence = None

TOTAL_TIMEOUT = 600

CODE_OS_SYSTEM = """Eres Code OS v3 — el Exocortex tecnico de OMNI-MIND. SIEMPRE responde en ESPAÑOL.

CHUNK 1 — IDENTIDAD:
Eres un equipo tech completo: arquitecto, developer, QA, DevOps, DBA. El usuario es el CEO.
Tomas decisiones técnicas. Ejecutas. Verificas. Reportas.

CHUNK 2 — ARCHIVOS (CRITICO):
@project/ = archivos REALES del proyecto. Sin prefijo = sandbox temporal (SE PIERDE).
  write_file(path='@project/core/nuevo.py')  → crea en proyecto
  edit_file(path='@project/api.py', ...)      → edita en proyecto
  read_file(path='@project/src/main.py')      → lee del proyecto
NUNCA escribas código del proyecto sin @project/.

CHUNK 3 — HERRAMIENTAS:
Tienes 63 tools. Usa mochila("herramientas") para ver el catálogo completo.
Esenciales: read_file, write_file, edit_file, db_query, db_insert, run_command, remember, mochila.
Usa mochila("errores") si algo falla. Usa mochila("reglas") si dudas del protocolo.

CHUNK 4 — PROTOCOLO:
1. Entiende → 2. Investiga (@project/, remember, db_query) → 3. Implementa → 4. Verifica → 5. Reporta
Antes de finish(): ejecuta TODAS las verificaciones. RESUMEN FINAL al CEO con métricas.
Leer ≠ ejecutar. Describir ≠ hacer. Cada INSERT se ejecuta. Cada archivo se crea con @project/.

{context_section}
"""

BRIEFING_EXECUTOR_PROMPT = """EJECUTA este briefing. Cada paso se EJECUTA, no se describe.

BRIEFING:
{briefing_content}

PROTOCOLO: mochila("briefing") tiene el protocolo completo. Resumen:
- SQL → db_insert(). Archivos → write_file(path='@project/...'). Comandos → run_command().
- SIEMPRE @project/ para archivos del proyecto. Sin él → sandbox temporal, SE PIERDE.
- Tras cada paso → VERIFICAR. Si falla → ARREGLAR.
- Al terminar → RESUMEN FINAL + métricas + finish().
"""


def run_agent_loop(
    goal: str,
    mode: str = "goal",
    project_dir: str = ".",
    strategy: str = "tiered",
    forced_model: Optional[str] = None,
    max_iterations: int = 80,
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

    set_autonomous(autonomous)
    set_call_context(componente='agent_loop', operacion='ejecucion', caso_id=session_id or goal[:20])

    if sandbox_dir is None:
        import tempfile
        sandbox_dir = tempfile.mkdtemp(prefix="code_os_")
    os.makedirs(sandbox_dir, exist_ok=True)

    # Initialize components
    if registry is None:
        registry = create_default_registry(sandbox_dir)

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
    ctx_mgr = ContextManager()

    # Get tool schemas
    tool_schemas = registry.get_schemas()

    # Build system prompt
    system = CODE_OS_SYSTEM.format(
        context_section=f"PROJECT CONTEXT:\n{context_prompt}" if context_prompt else ""
    )

    # Handle briefing mode
    if mode == "briefing" and briefing_path:
        from pathlib import Path
        briefing_content = Path(briefing_path).read_text(errors='replace')
        goal = BRIEFING_EXECUTOR_PROMPT.format(briefing_content=briefing_content[:30000])

    history = [
        {"role": "system", "content": system},
        {"role": "user", "content": (
            f"TASK:\n{goal}\n\n"
            f"Workspace: {sandbox_dir}\n"
            f"Runtimes: python3, pytest, deno, node.\n"
            f"Tools available: {registry.tool_count()}\n"
            f"Start by understanding the task, then plan and implement."
        )},
    ]

    log = []
    start_time = time.time()
    stop_reason = None
    final_result = None
    files_changed = set()

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
    except Exception:
        pass  # Cache nunca debe romper la ejecución

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

        # Run pre_tool hooks
        if hooks:
            hooks.run("pre_iteration", {"iteration": iteration, "model": model})

        # Call model
        try:
            api_resp = call_with_retry(history, model, tools=tool_schemas)
        except RuntimeError as e:
            try:
                fallback = TIER_CONFIG.get("worker_budget", TIER_CONFIG.get("tier2b", "xiaomi/mimo-v2-flash"))
                api_resp = call_with_retry(history, fallback, tools=tool_schemas, max_retries=1)
                model = fallback
            except RuntimeError:
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
                history.append({"role": "user", "content": "Use a tool NOW to make progress."})
            elif stuck.no_tool_streak >= 3:
                router.on_blowup()
                history.append({"role": "user", "content": "CRITICAL: Call list_dir('.') NOW."})
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

            # Handle finish
            if tool_name == "finish":
                final_result = tool_args.get("result", "Task completed")
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
                except Exception:
                    pass

            if verbose:
                status = "ERR" if is_error else "OK"
                print(f" -> {tool_name}({status}): {result_str[:60].replace(chr(10), ' ')}")

            stuck.record_action(tool_name, tool_args, result_str, is_error)

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
                except Exception:
                    pass

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
                    except Exception:
                        pass
            else:
                router.on_success()
                if tool_name == "run_command" and any(kw in result_str for kw in
                        ["FAILED", "failed", "Error", "AssertionError"]):
                    router.on_test_failure()

            # Track file changes
            if tool_name in ("write_file", "edit_file") and not is_error:
                fpath = tool_args.get("path", "")
                files_changed.add(fpath)
                if db:
                    action = "create" if tool_name == "write_file" else "edit"
                    db.log_file_change(session_id, fpath, action, iter_n=iteration)

            # Run post_tool hooks
            if hooks:
                hooks.run("post_tool", {"tool": tool_name, "args": tool_args,
                                        "result": result_str, "is_error": is_error})

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

        if stop_reason:
            break

        history = ctx_mgr.maybe_compress(history)

    # Flush telemetry buffer
    evo = _get_tool_evo()
    if evo and hasattr(evo, 'flush'):
        try:
            evo.flush()
        except Exception:
            pass

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
    except Exception:
        pass  # Telemetria nunca debe romper la ejecucion

    # Flywheel feedback (pattern 60668) — close the loop
    try:
        from .flywheel import after_session
        result_for_flywheel = {
            "stop_reason": stop_reason or "MAX_ITERATIONS",
            "iterations": stuck.iteration,
            "time_s": round(total_time, 1),
            "cost_usd": round(budget.cost_usd, 4),
            "model_used": router.select(),
            "task_type": router.task_type if hasattr(router, 'task_type') else "unknown",
            "phase_info": router.get_phase_info() if hasattr(router, 'get_phase_info') else {},
            "log": log,
        }
        summary = post_session_summary(result_for_flywheel)
        after_session(summary)
    except Exception:
        pass  # Flywheel nunca debe romper la ejecución

    # Cache save — store successful short executions for Tier 0 (pattern 60661)
    if stop_reason == "DONE" and stuck.iteration <= 5:
        try:
            from .cache_tier import save_to_cache
            tool_seq = [e for e in log if isinstance(e, dict) and e.get("tool")]
            save_to_cache(goal, tool_seq, final_result or "", True)
        except Exception:
            pass

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
        "log": log,
    }
