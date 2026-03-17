#!/usr/bin/env python3
"""Code OS CLI — terminal interactivo como Claude Code.

Uso:
  python3 cli.py                          # Chat interactivo
  python3 cli.py --briefing path/to.md    # Ejecutar briefing
  python3 cli.py --goal "instruccion"     # One-shot goal
  python3 cli.py --session ID             # Retomar sesion
"""

import os
import sys
import json
import time
import signal
import argparse

# Ensure agent/ is in path
sys.path.insert(0, os.path.dirname(__file__))

from core.api import _load_env
_load_env()

# Colors
BLUE = "\033[34m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _format_time(ms):
    if ms < 1000:
        return f"{ms}ms"
    return f"{ms/1000:.1f}s"


def _print_event(event, step_count):
    """Print an SSE event in Claude Code terminal style."""
    etype = event.get("type", "")

    if etype == "thinking":
        model = event.get("model", "")
        step = event.get("step", step_count)
        phase = event.get("phase", "")
        model_short = model.split("/")[-1][:20] if model else ""
        print(f"\r{DIM}  [{step}] thinking... {model_short} {phase}{RESET}", end="", flush=True)

    elif etype == "tool_call":
        tool = event.get("tool", "")
        args = event.get("args", {})
        step = event.get("step", step_count)
        # Format like Claude Code: > ToolName(key="value")
        arg_str = ""
        if args:
            key_arg = next(iter(args), "")
            val = str(args[key_arg])[:60]
            if len(args) > 1:
                arg_str = f'{key_arg}="{val}", +{len(args)-1}'
            else:
                arg_str = f'{key_arg}="{val}"'
        print(f"\r{CYAN}  [{step}] > {tool}({arg_str}){RESET}")

    elif etype == "tool_result":
        tool = event.get("tool", "")
        result = event.get("result", "")
        is_error = event.get("is_error", False)
        duration = event.get("duration_ms", 0)
        cost = event.get("cost_usd", 0)
        first_line = result.split("\n")[0][:100] if result else ""
        color = RED if is_error else GREEN
        status = "ERR" if is_error else "OK"
        extras = f" {_format_time(duration)}" if duration else ""
        if cost:
            extras += f" ${cost:.4f}"
        print(f"    {color}{status}{RESET}: {first_line}{DIM}{extras}{RESET}")

    elif etype == "text":
        text = event.get("content", "")
        if text.strip():
            # Wrap long lines
            for line in text.split("\n"):
                print(f"  {line}")

    elif etype == "done":
        total_ms = event.get("total_ms", 0)
        cost = event.get("total_cost_usd", 0)
        print(f"\n{DIM}  Done in {_format_time(total_ms)}", end="")
        if cost:
            print(f" (${cost:.4f})", end="")
        print(f"{RESET}\n")

    elif etype == "error":
        msg = event.get("message", event.get("error", ""))
        print(f"\n{RED}  Error: {msg}{RESET}\n")

    elif etype == "phase_transition":
        new_phase = event.get("new_phase", "")
        print(f"\n{YELLOW}  → Phase: {new_phase}{RESET}")

    elif etype == "file_received":
        fname = event.get("filename", "")
        chars = event.get("chars", 0)
        print(f"{DIM}  File: {fname} ({chars} chars){RESET}")


def interactive_loop(engine, session_id):
    """Main interactive REPL loop."""
    from core.intent import translate_intent
    from core.reporter import Reporter

    reporter = Reporter()

    print(f"\n{BOLD}Code OS v3{RESET} — terminal interactivo")
    print(f"{DIM}Session: {session_id[:8]}...{RESET}")
    print(f"{DIM}Escribe tu mensaje. Ctrl+C para salir.{RESET}\n")

    # Proactive health check at session start
    try:
        from core.proactive import health_check
        alerts = health_check()
        for alert in alerts[:3]:
            nivel = alert.get("nivel", "info")
            msg = alert.get("mensaje", "")
            sugerencia = alert.get("accion_sugerida", "")
            if nivel == "alert":
                color = RED
            elif nivel == "warning":
                color = YELLOW
            else:
                color = DIM
            print(f"{color}  {msg}. Sugerencia: {sugerencia}{RESET}")
        if alerts:
            print()
    except Exception:
        pass

    while True:
        try:
            user_input = input(f"{BLUE}> {RESET}")
        except (EOFError, KeyboardInterrupt):
            print(f"\n{DIM}Bye.{RESET}")
            break

        if not user_input.strip():
            continue

        # Special commands
        cmd = user_input.strip().lower()
        if cmd in ("exit", "quit", "/exit", "/quit"):
            print(f"{DIM}Bye.{RESET}")
            break
        if cmd == "/health":
            import requests
            try:
                r = requests.get("https://chief-os-omni.fly.dev/health", timeout=5)
                print(json.dumps(r.json(), indent=2))
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
            continue
        if cmd == "/propiocepcion":
            import requests
            try:
                r = requests.get("https://chief-os-omni.fly.dev/propiocepcion", timeout=10)
                print(json.dumps(r.json(), indent=2))
            except Exception as e:
                print(f"{RED}Error: {e}{RESET}")
            continue
        if cmd == "/sessions":
            sessions = engine.list_sessions()
            for s in sessions[:10]:
                print(f"  {s.get('id', '')[:8]}  {s.get('preview', '')[:60]}")
            continue

        # Intent translation — business to technical
        intent = translate_intent(user_input, {})
        message = user_input
        if intent["category"]:
            print(f"{DIM}  Entendido: {intent['explanation_for_user']}{RESET}")
            message = intent["technical_goal"]

        # Process message
        step_count = 0
        last_result = None
        is_question = "?" in user_input
        try:
            for event in engine.process_message(session_id, message):
                if event.get("type") == "tool_call":
                    step_count += 1
                    event["step"] = step_count
                elif event.get("type") == "thinking":
                    event["step"] = step_count + 1
                elif event.get("type") == "done":
                    last_result = event
                _print_event(event, step_count)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}  Interrupted{RESET}\n")
            continue

        # Reporter summary
        if last_result and intent["category"]:
            summary = reporter.summarize_session(last_result)
            print(f"\n{GREEN}  {summary}{RESET}")


def oneshot(engine, session_id, message):
    """Run a single message and exit."""
    step_count = 0
    for event in engine.process_message(session_id, message):
        if event.get("type") == "tool_call":
            step_count += 1
            event["step"] = step_count
        elif event.get("type") == "thinking":
            event["step"] = step_count + 1
        _print_event(event, step_count)


def main():
    parser = argparse.ArgumentParser(description="Code OS v3 — CLI interactivo")
    parser.add_argument("--goal", help="One-shot: ejecutar un goal y salir")
    parser.add_argument("--briefing", help="One-shot: ejecutar un briefing y salir")
    parser.add_argument("--session", help="Retomar session existente por ID")
    parser.add_argument("--project", default=None, help="Project directory")
    parser.add_argument("--budget", type=float, default=15.0, help="Budget USD (default: 15)")
    parser.add_argument("--verify", choices=["fast", "standard", "deep"],
                       default="fast", help="Verification tier (default: fast)")
    args = parser.parse_args()

    from chat import ChatEngine

    project_dir = args.project or os.environ.get(
        "CODE_OS_PROJECT_DIR",
        os.path.abspath(".")
    )

    engine = ChatEngine(
        project_dir=project_dir,
        strategy=os.environ.get("CODE_OS_STRATEGY", "tiered"),
        forced_model=os.environ.get("CODE_OS_MODEL"),
        max_cost=args.budget,
    )

    session_id = args.session or str(__import__("uuid").uuid4())

    if args.briefing:
        from core.agent_loop import run_briefing
        print(f"{DIM}Briefing: {args.briefing}{RESET}")
        result = run_briefing(
            briefing_path=args.briefing,
            project_dir=project_dir,
            verbose=True,
            verify_tier=args.verify,
        )
        for r in result["results"]:
            status_color = GREEN if r["status"] == "DONE" else RED
            print(f"  Step {r['step']}: {status_color}{r['status']}{RESET}"
                  f" ({r['iterations']} iters, ${r['cost']:.4f})")
        print(f"\n{BOLD}Total: {result['steps_completed']}/{result['steps_total']} "
              f"(${result['total_cost']:.4f}){RESET}")
        return
    elif args.goal:
        print(f"{DIM}Goal: {args.goal[:80]}{RESET}")
        oneshot(engine, session_id, args.goal)
    else:
        interactive_loop(engine, session_id)


if __name__ == "__main__":
    main()
