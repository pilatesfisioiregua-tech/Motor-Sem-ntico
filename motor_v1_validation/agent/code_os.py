#!/usr/bin/env python3
"""CODE OS v2 — "El Enjambre"

Un Claude Code Open Source con 52+ herramientas, sub-agentes, compresion de contexto,
smart routing con reflection, session resume, hooks, y auto-extension.

Modos:
  --vision "idea no tecnica"     → entiende + genera briefing + ejecuta
  --goal "instruccion tecnica"   → ejecuta directamente (como Claude Code)
  --briefing path/to/BRIEFING.md → ejecuta un briefing existente

Flags v2:
  --autonomous    No pregunta (default despues de aprobar)
  --interactive   Puede preguntar al usuario
  --swarm         Habilita sub-agentes paralelos
  --resume ID     Restaura sesion previa
  --hooks         Activa hook system
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

# Ensure agent/ is in path
sys.path.insert(0, os.path.dirname(__file__))

from core.api import MODELS, OPENROUTER_KEY, TIER_CONFIG, call_with_retry, _load_env
from core.agent_loop import run_agent_loop
from understanding import (
    ContextLoader, VisionTranslator, BriefingGenerator,
    ProjectContext, TechnicalSpec,
)
from persistence import SupabaseClient

_load_env()


def run_code_os(goal: str, mode: str = "goal", project_dir: str = ".",
                strategy: str = "tiered", forced_model: str = None,
                max_iterations: int = 30, max_cost: float = 2.0,
                sandbox_dir: str = None, verbose: bool = False,
                vision_text: str = None, briefing_path: str = None,
                autonomous: bool = True, swarm: bool = False,
                resume_id: str = None, enable_hooks: bool = False,
                verify_tier: str = "fast") -> dict:
    """Main Code OS v2 execution."""

    # Initialize Supabase
    db = SupabaseClient()
    loader = ContextLoader()

    # Load project context
    context = loader.load(project_dir, supabase_client=db)
    context_prompt = context.to_prompt(max_chars=4000)

    # Resume session if requested
    if resume_id:
        session_state = db.get_session_state(resume_id) if db.enabled else None
        if session_state:
            if verbose:
                print(f"  Resuming session {resume_id[:8]}...")
            session_id = resume_id
        else:
            session_id = db.log_session_start(
                mode=mode, input_raw=vision_text or goal or briefing_path or "",
                project_name=context.project_name, project_dir=project_dir,
                model_primary="", strategy=strategy,
            )
    else:
        session_id = db.log_session_start(
            mode=mode, input_raw=vision_text or goal or briefing_path or "",
            project_name=context.project_name, project_dir=project_dir,
            model_primary="", strategy=strategy,
        )

    if verbose:
        print(f"  Session: {session_id[:8]}...")
        print(f"  Project: {context.project_name} ({context.stack})")
        print(f"  Mode: {mode} | Strategy: {strategy}")

    # ================================================================
    # MODE: VISION → Translate → Briefing → Execute
    # ================================================================
    if mode == "vision" and vision_text:
        if verbose:
            print(f"  Translating vision...")

        def _call_llm(messages, model=None):
            m = model or TIER_CONFIG["vision"]
            return call_with_retry(messages, m, max_retries=2)

        translator = VisionTranslator()
        spec = translator.translate(vision_text, context, call_llm_fn=_call_llm)
        db.log_vision(session_id, vision_text, spec.__dict__)

        if verbose:
            print(f"  Spec: {spec.objective}")
            print(f"  Modules: {len(spec.modules)} | Steps: {len(spec.implementation_order)}")

        generator = BriefingGenerator()
        next_num = len(context.briefings) + 1
        briefing_md = generator.generate(spec, context, briefing_number=next_num,
                                         call_llm_fn=_call_llm)
        db.log_briefing(session_id, f"BRIEFING_{next_num:02d}", briefing_md, approved=True)

        if verbose:
            print(f"  Briefing generated: BRIEFING_{next_num:02d}")

        from core.agent_loop import BRIEFING_EXECUTOR_PROMPT
        goal = BRIEFING_EXECUTOR_PROMPT.format(briefing_content=briefing_md[:15000])

    # ================================================================
    # Intent translation — business to technical (goal mode only)
    # ================================================================
    intent = None
    if mode == "goal" and goal:
        from core.intent import translate_intent
        intent = translate_intent(goal, {})
        if intent["category"]:
            if verbose:
                print(f"  Intent: {intent['category']} — {intent['explanation_for_user']}")
            goal = intent["technical_goal"]

    # ================================================================
    # MODE: BRIEFING → run_briefing (step-by-step with drift guard)
    # ================================================================
    if mode == "briefing" and briefing_path:
        from core.agent_loop import run_briefing
        br = run_briefing(
            briefing_path=briefing_path,
            project_dir=os.path.abspath(project_dir),
            max_cost_per_step=max_cost / 5,
            verbose=verbose,
            db=db,
            verify_tier=verify_tier,
        )
        return {
            "session_id": session_id,
            "stop_reason": "DONE" if br["all_passed"] else "BRIEFING_INCOMPLETE",
            "iterations": sum(r["iterations"] for r in br["results"]),
            "cost_usd": br["total_cost"],
            "tokens_used": 0,
            "time_s": 0,
            "model_used": "multi",
            "files_changed": [],
            "result": f"Briefing: {br['steps_completed']}/{br['steps_total']} pasos",
            "sandbox_dir": sandbox_dir or ".",
        }

    # ================================================================
    # Initialize hooks if enabled
    # ================================================================
    hooks = None
    if enable_hooks:
        try:
            from hooks import HookRegistry, create_default_hooks
            hooks = create_default_hooks(sandbox_dir or ".")
        except ImportError:
            pass

    # ================================================================
    # Run agent loop
    # ================================================================
    result = run_agent_loop(
        goal=goal,
        mode=mode,
        project_dir=project_dir,
        strategy=strategy,
        forced_model=forced_model,
        max_iterations=max_iterations,
        max_cost=max_cost,
        sandbox_dir=sandbox_dir,
        verbose=verbose,
        briefing_path=briefing_path if mode == "briefing" else None,
        autonomous=autonomous,
        context_prompt=context_prompt,
        session_id=session_id,
        db=db,
        hooks=hooks,
    )

    # Save session state for resume
    if db.enabled and result.get("stop_reason") != "DONE":
        db.save_session_state(session_id, {
            "goal": goal,
            "mode": mode,
            "iteration": result["iterations"],
            "cost_usd": result["cost_usd"],
            "files_changed": result["files_changed"],
        })

    return result


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Code OS v2 — El Enjambre",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Goal mode (direct technical instruction)
  python3 code_os.py --goal "Add retry logic to llm_client.py"

  # Vision mode (non-technical input -> briefing -> code)
  python3 code_os.py --vision "Quiero que el motor tenga un chat"

  # Briefing mode (execute existing briefing)
  python3 code_os.py --briefing briefings/BRIEFING_05_CHAT.md

  # Force specific model
  python3 code_os.py --goal "..." --model devstral-small

  # Tiered routing (cheap -> strong -> top on errors)
  python3 code_os.py --goal "..." --strategy tiered

  # Resume a previous session
  python3 code_os.py --goal "..." --resume SESSION_ID

  # Autonomous mode with swarm
  python3 code_os.py --goal "..." --autonomous --swarm
""")

    # v1 compatible modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--vision", help="Non-technical vision -> briefing -> code")
    mode_group.add_argument("--goal", help="Direct technical goal to implement")
    mode_group.add_argument("--briefing", help="Path to briefing .md file to execute")

    # v1 compatible options
    parser.add_argument("--project", default=".", help="Project directory (default: current)")
    parser.add_argument("--strategy", choices=["solo", "tiered"], default="tiered",
                       help="Model routing strategy (default: tiered)")
    parser.add_argument("--model", help="Force specific model (overrides strategy)")
    parser.add_argument("--max-iter", type=int, default=30, help="Max iterations (default: 30)")
    parser.add_argument("--budget", type=float, default=2.0, help="Max cost in USD (default: 2.0)")
    parser.add_argument("--sandbox", help="Override sandbox directory")
    parser.add_argument("--verbose", action="store_true", help="Log each iteration")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")

    # v2 new options
    parser.add_argument("--autonomous", action="store_true", default=True,
                       help="Autonomous mode — no user interaction (default)")
    parser.add_argument("--interactive", action="store_true",
                       help="Interactive mode — can ask user questions")
    parser.add_argument("--swarm", action="store_true",
                       help="Enable sub-agent swarm for parallel tasks")
    parser.add_argument("--resume", metavar="SESSION_ID",
                       help="Resume a previous session by ID")
    parser.add_argument("--hooks", action="store_true",
                       help="Enable hook system (audit, auto-test, git checkpoint)")
    parser.add_argument("--verify", choices=["fast", "standard", "deep"],
                       default="fast", help="Verification tier for briefings (default: fast)")

    args = parser.parse_args()

    if not OPENROUTER_KEY:
        print("ERROR: OPENROUTER_API_KEY not set in .env")
        sys.exit(1)

    # Determine mode and goal
    if args.vision:
        mode = "vision"
        goal = args.vision
        display = f"Vision: {args.vision[:80]}"
    elif args.goal:
        mode = "goal"
        goal = args.goal
        display = f"Goal: {args.goal[:80]}"
    else:
        mode = "briefing"
        goal = f"Execute briefing: {args.briefing}"
        display = f"Briefing: {args.briefing}"

    # Resolve model
    forced_model = None
    if args.model:
        forced_model = MODELS.get(args.model, args.model)

    autonomous = not args.interactive

    if not args.quiet:
        print(f"{'='*60}")
        print(f"  CODE OS v2 — El Enjambre")
        print(f"  {display}")
        print(f"  Strategy: {args.strategy} | Iter: {args.max_iter} | Budget: ${args.budget}")
        print(f"  Mode: {'autonomous' if autonomous else 'interactive'}"
              f" | Swarm: {'on' if args.swarm else 'off'}"
              f" | Hooks: {'on' if args.hooks else 'off'}")
        if args.resume:
            print(f"  Resume: {args.resume[:8]}...")
        print(f"{'='*60}")

    result = run_code_os(
        goal=goal,
        mode=mode,
        project_dir=os.path.abspath(args.project),
        strategy=args.strategy,
        forced_model=forced_model,
        max_iterations=args.max_iter,
        max_cost=args.budget,
        sandbox_dir=args.sandbox,
        verbose=args.verbose,
        vision_text=args.vision if mode == "vision" else None,
        briefing_path=args.briefing if mode == "briefing" else None,
        autonomous=autonomous,
        swarm=args.swarm,
        resume_id=args.resume,
        enable_hooks=args.hooks,
        verify_tier=args.verify,
    )

    if not args.quiet:
        # Reporter summary (human-readable) when not verbose
        if not args.verbose:
            from core.reporter import Reporter
            reporter = Reporter()
            print(f"\n  {reporter.summarize_session(result)}")
        else:
            print(f"\n{'='*60}")
            print(f"  Session:      {result['session_id'][:8]}...")
            print(f"  Stop:         {result['stop_reason']}")
            print(f"  Iterations:   {result['iterations']}")
            print(f"  Tokens:       {result['tokens_used']:,}")
            print(f"  Cost:         ${result['cost_usd']:.4f}")
            print(f"  Time:         {result['time_s']}s")
            print(f"  Model:        {result['model_used']}")
            print(f"  Task type:    {result.get('task_type', 'unknown')}")
            print(f"  Compressions: {result.get('compressions', 0)}")
            print(f"  Tools:        52+")
            print(f"  Sandbox:      {result['sandbox_dir']}")
            if result['files_changed']:
                print(f"  Files:        {', '.join(result['files_changed'][:5])}")
            if result['result']:
                print(f"  Result:       {result['result'][:200]}")
            print(f"{'='*60}")

    sys.exit(0 if result['stop_reason'] == 'DONE' else 1)


if __name__ == "__main__":
    main()
