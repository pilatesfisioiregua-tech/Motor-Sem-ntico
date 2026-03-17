"""Drift detection — heuristic guard against off-topic wandering."""

import os
from typing import Optional


OFF_TOPIC = [
    "cryptography", "blockchain", "build system", "bazel", "cmake",
    "financial transaction", "payment processing", "sable",
    "compiler design", "operating system kernel",
]

DOMAIN_ANCHORS = [
    "omni", "motor", "gestor", "matriz", "inteligencia", "reactor",
    "flywheel", "estigmergia", "exocortex", "briefing",
    "registrador", "sandwich", "mochila", "costes", "gradiente", "celda",
]

MAX_CONSECUTIVE_DRIFTS = 3

# Module-level state
_consecutive_drifts = 0


def check_drift(content: str, project_dir: str) -> Optional[str]:
    """Return drift reason if off-topic keyword found without domain anchors, else None."""
    if not content:
        return None
    content_lower = content.lower()

    for kw in OFF_TOPIC:
        if kw in content_lower:
            has_anchor = any(a in content_lower for a in DOMAIN_ANCHORS)
            if not has_anchor:
                return f"Off-topic keyword detected: '{kw}' without domain anchors"

    return None


def check_file_drift(file_path: str, project_dir: str) -> Optional[str]:
    """Return reason if file_path is outside project_dir, else None."""
    if not file_path or not project_dir:
        return None
    # Normalize paths
    fp = os.path.abspath(file_path)
    pd = os.path.abspath(project_dir)
    if not fp.startswith(pd) and not file_path.startswith("@project/") and not file_path.startswith("./"):
        return f"File '{file_path}' is outside project dir '{project_dir}'"
    return None


def drift_hook_post_tool(context: dict) -> None:
    """Hook: increment drift counter if drift detected in tool result."""
    global _consecutive_drifts
    result = context.get("result", "")
    project_dir = context.get("project_dir", ".")
    reason = check_drift(str(result), project_dir)
    if reason:
        _consecutive_drifts += 1
    else:
        _consecutive_drifts = 0


def drift_hook_pre_iteration(context: dict) -> None:
    """Hook: inject warning if drifts accumulating, set abort flag if >= MAX."""
    global _consecutive_drifts
    if _consecutive_drifts >= MAX_CONSECUTIVE_DRIFTS:
        context["_drift_abort"] = True
    elif _consecutive_drifts >= 2:
        history = context.get("history")
        if history and isinstance(history, list):
            history.append({
                "role": "user",
                "content": f"WARNING: {_consecutive_drifts} consecutive drifts detected. "
                           f"Refocus on the current task immediately.",
            })


def reset_drift_state() -> None:
    """Reset drift counter — call between briefing steps."""
    global _consecutive_drifts
    _consecutive_drifts = 0


def register_drift_hooks(hook_registry) -> None:
    """Register drift detection hooks on a HookRegistry."""
    hook_registry.register("drift_post_tool", "post_tool", drift_hook_post_tool)
    hook_registry.register("drift_pre_iteration", "pre_iteration", drift_hook_pre_iteration)
