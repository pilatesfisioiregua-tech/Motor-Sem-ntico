"""Code OS v2 — Hook System for extensibility."""

import os
import time
import subprocess
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class Hook:
    """A single hook — function called on event."""
    name: str
    event: str  # "pre_tool", "post_tool", "on_error", "pre_iteration", "post_iteration"
    handler: Callable
    enabled: bool = True


class HookRegistry:
    """Registry for hooks that fire on agent events."""

    def __init__(self):
        self._hooks: Dict[str, List[Hook]] = {}

    def register(self, name: str, event: str, handler: Callable) -> None:
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(Hook(name=name, event=event, handler=handler))

    def unregister(self, name: str) -> None:
        for event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h.name != name]

    def run(self, event: str, context: dict) -> None:
        """Run all hooks for an event. Hooks should not raise."""
        for hook in self._hooks.get(event, []):
            if not hook.enabled:
                continue
            try:
                hook.handler(context)
            except Exception:
                pass  # Hooks should never break the agent

    def list_hooks(self) -> Dict[str, List[str]]:
        return {event: [h.name for h in hooks] for event, hooks in self._hooks.items()}


# ============================================================
# BUILT-IN HOOKS
# ============================================================

def audit_hook(context: dict) -> None:
    """Log every tool call to audit.log for debugging."""
    tool = context.get("tool", "")
    args = context.get("args", {})
    result_preview = str(context.get("result", ""))[:200]
    is_error = context.get("is_error", False)

    log_line = f"[{time.strftime('%H:%M:%S')}] {tool}"
    if is_error:
        log_line += f" ERROR: {result_preview}"
    # Write to audit log
    log_dir = os.environ.get("CODE_OS_LOG_DIR", "/tmp")
    log_file = os.path.join(log_dir, "code_os_audit.log")
    try:
        with open(log_file, 'a') as f:
            f.write(log_line + "\n")
    except OSError:
        pass


def auto_test_hook(context: dict) -> None:
    """After file writes, run corresponding test if it exists."""
    tool = context.get("tool", "")
    if tool not in ("write_file", "edit_file") or context.get("is_error"):
        return
    path = context.get("args", {}).get("path", "")
    if not path.endswith(".py"):
        return
    basename = os.path.basename(path)
    if basename.startswith("test_") or basename == "__init__.py":
        return

    # Look for corresponding test file
    dirpath = os.path.dirname(path)
    name_no_ext = os.path.splitext(basename)[0]
    candidates = [
        os.path.join(dirpath, f"test_{basename}"),
        os.path.join(dirpath, "tests", f"test_{basename}"),
        os.path.join(os.path.dirname(dirpath), "tests", f"test_{basename}"),
    ]
    test_path = None
    for c in candidates:
        if os.path.isfile(c):
            test_path = c
            break
    if not test_path:
        return

    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", test_path, "-x", "-q"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            context["auto_test_result"] = (
                f"Auto-test FAILED ({test_path}):\n{result.stdout}\n{result.stderr}"
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def git_checkpoint_hook(context: dict) -> None:
    """Smart git checkpoint: only after successful file writes with actual changes.

    Fires on post_tool. Creates checkpoint only when:
      - Tool was write_file or edit_file
      - Tool succeeded (no error)
      - git status shows actual changes

    Stores commit hash in context['_checkpoint_hash'] for RecoveryEngine.
    """
    tool = context.get("tool", "")
    is_error = context.get("is_error", False)

    # Only checkpoint after successful file writes
    if tool not in ("write_file", "edit_file") or is_error:
        return

    try:
        # Check if there are actual changes to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=10,
        )
        if not status.stdout.strip():
            return  # No changes, skip

        # Stage only tracked files + new files in project
        subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, timeout=10,
        )

        path = context.get("args", {}).get("path", "unknown")
        result = subprocess.run(
            ["git", "commit", "-m",
             f"[Code OS] checkpoint: {tool} {os.path.basename(path)}"],
            capture_output=True, text=True, timeout=10,
        )

        if result.returncode == 0:
            # Extract commit hash for rollback tracking
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=5,
            )
            if hash_result.returncode == 0:
                context["_checkpoint_hash"] = hash_result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def post_briefing_step_hook(context: dict) -> None:
    """After each briefing step, verify with Verifier (fast tier, $0)."""
    step = context.get("step")
    result = context.get("result", {})
    if not step:
        return
    try:
        from core.verifier import Verifier
        v = Verifier("fast")
        verification = v.verify_step(step, result)
        context["_verification"] = verification
    except Exception:
        pass


def create_default_hooks(sandbox_dir: str = ".") -> HookRegistry:
    """Create HookRegistry with built-in hooks."""
    registry = HookRegistry()
    registry.register("audit", "post_tool", audit_hook)
    registry.register("auto_test", "post_tool", auto_test_hook)
    registry.register("git_checkpoint", "post_tool", git_checkpoint_hook)
    registry.register("post_briefing_step", "post_briefing_step", post_briefing_step_hook)

    try:
        from core.drift_guard import register_drift_hooks
        register_drift_hooks(registry)
    except ImportError:
        pass

    return registry
