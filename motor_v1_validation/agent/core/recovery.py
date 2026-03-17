"""Code OS v3.1 — RecoveryEngine: automatic error recovery with decision tree."""

import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Error classification patterns
ERROR_PATTERNS = {
    "syntax": ["SyntaxError", "IndentationError", "TabError"],
    "import": ["ModuleNotFoundError", "ImportError", "No module named"],
    "type": ["TypeError", "AttributeError", "NameError"],
    "io": ["FileNotFoundError", "PermissionError", "IsADirectoryError", "OSError"],
    "timeout": ["TimeoutError", "timeout", "timed out", "TIMEOUT"],
    "api": ["429", "rate limit", "503", "502", "API_FAILURE", "ConnectionError"],
    "test": ["FAILED", "AssertionError", "AssertionError", "test failed"],
    "unknown_tool": ["Unknown tool"],
}

# Max retries per error type
MAX_RETRIES = {
    "syntax": 2,
    "import": 1,
    "type": 2,
    "io": 1,
    "timeout": 2,
    "api": 3,
    "test": 3,
    "unknown_tool": 0,
}


def classify_error(error_str: str) -> str:
    """Classify an error string into a category."""
    for category, patterns in ERROR_PATTERNS.items():
        if any(p.lower() in error_str.lower() for p in patterns):
            return category
    return "unknown"


@dataclass
class RecoveryEngine:
    """Decision tree for automatic error recovery.

    decide() returns {action, reason, hint} where action is one of:
      - retry: retry same tool with same args
      - retry_different: retry with modified approach (hint has suggestion)
      - skip: skip this tool, continue with next step
      - decompose: break goal into sub-goals
      - escalate: switch to stronger model
      - rollback: revert last file changes and retry
      - abort: give up on this path
    """

    error_counts: Dict[str, int] = field(default_factory=dict)
    last_errors: List[Tuple[str, str, float]] = field(default_factory=list)  # (tool, error, timestamp)
    last_writes: List[Tuple[str, str]] = field(default_factory=list)  # (tool, path) for rollback
    _git_checkpoints: List[str] = field(default_factory=list)  # commit hashes

    def decide(self, error_history: List[str], current_tool: str, goal: str,
               last_write: Optional[str] = None) -> dict:
        """Main decision tree: given error context, decide recovery action.

        Args:
            error_history: List of recent error strings
            current_tool: Tool that just failed
            goal: Current goal/task description
            last_write: Path of last file written (for rollback decisions)

        Returns:
            dict with keys: action, reason, hint (optional)
        """
        if not error_history:
            return {"action": "retry", "reason": "no_errors", "hint": None}

        latest_error = error_history[-1]
        category = classify_error(latest_error)

        # Track error count per category
        self.error_counts[category] = self.error_counts.get(category, 0) + 1
        self.last_errors.append((current_tool, latest_error, time.time()))

        count = self.error_counts[category]
        max_retry = MAX_RETRIES.get(category, 2)

        # Unknown tool — skip immediately, no retry
        if category == "unknown_tool":
            return {
                "action": "skip",
                "reason": f"Tool '{current_tool}' not found. Skip and use available tools.",
                "hint": "Use mochila('herramientas') to see available tools.",
            }

        # API errors — retry with backoff, then escalate
        if category == "api":
            if count <= max_retry:
                return {
                    "action": "retry",
                    "reason": f"API error (attempt {count}/{max_retry}), retrying.",
                    "hint": None,
                }
            return {
                "action": "escalate",
                "reason": "API errors persist after retries. Escalating to fallback model.",
                "hint": None,
            }

        # Timeout — retry once, then skip
        if category == "timeout":
            if count <= 1:
                return {
                    "action": "retry",
                    "reason": "Timeout, retrying once.",
                    "hint": None,
                }
            return {
                "action": "skip",
                "reason": "Persistent timeout. Skipping this operation.",
                "hint": "Consider breaking the operation into smaller parts.",
            }

        # Syntax/type errors — can be fixed by retry with different approach
        if category in ("syntax", "type"):
            if count <= 1:
                return {
                    "action": "retry_different",
                    "reason": f"{category} error. Retry with corrected code.",
                    "hint": f"Fix the {category} error: {latest_error[:150]}",
                }
            if last_write and count <= 2:
                return {
                    "action": "rollback",
                    "reason": f"Repeated {category} error. Rolling back last write and retrying.",
                    "hint": f"Rollback {last_write} and try a different implementation.",
                }
            return {
                "action": "decompose",
                "reason": f"Persistent {category} errors. Decomposing into simpler steps.",
                "hint": None,
            }

        # Import errors — install or skip
        if category == "import":
            return {
                "action": "retry_different",
                "reason": "Import error. Check if module exists or use alternative.",
                "hint": f"Module not found: {latest_error[:100]}. Try pip install or use stdlib.",
            }

        # IO errors — skip if file not found, retry if permission
        if category == "io":
            if "PermissionError" in latest_error:
                return {
                    "action": "retry_different",
                    "reason": "Permission error. Try different path or check permissions.",
                    "hint": "Check file permissions or use a different output path.",
                }
            return {
                "action": "skip",
                "reason": f"IO error: file not accessible. {latest_error[:100]}",
                "hint": "Verify the file path exists.",
            }

        # Test failures — retry with fixes, then decompose
        if category == "test":
            if count <= 2:
                return {
                    "action": "retry_different",
                    "reason": f"Test failure (attempt {count}/{max_retry}). Fix and retry.",
                    "hint": f"Test failed: {latest_error[:150]}. Analyze the error and fix.",
                }
            if last_write:
                return {
                    "action": "rollback",
                    "reason": "Tests failing repeatedly. Rolling back to last checkpoint.",
                    "hint": None,
                }
            return {
                "action": "decompose",
                "reason": "Tests failing repeatedly. Breaking into smaller testable pieces.",
                "hint": None,
            }

        # Unknown errors — generic escalation
        if count <= 2:
            return {
                "action": "retry_different",
                "reason": f"Unknown error (attempt {count}). Trying different approach.",
                "hint": f"Error: {latest_error[:150]}",
            }
        if count <= 4:
            return {
                "action": "escalate",
                "reason": "Persistent unknown errors. Escalating to stronger model.",
                "hint": None,
            }
        return {
            "action": "abort",
            "reason": f"Too many errors ({count}). Aborting this approach.",
            "hint": None,
        }

    def should_decompose(self, error_history: List[str], iteration: int,
                         max_iterations: int) -> bool:
        """Should the current goal be decomposed into sub-goals?

        Returns True when:
          - 3+ different error types in last 10 errors
          - More than 40% of max_iterations used with errors > successes
          - Same tool failing 3+ times with different errors
        """
        if len(error_history) < 3:
            return False

        # Check diversity of error types in recent errors
        recent = error_history[-10:]
        categories = set(classify_error(e) for e in recent)
        if len(categories) >= 3:
            return True

        # Check iteration budget burn
        if iteration > max_iterations * 0.4:
            error_rate = len(error_history) / max(iteration, 1)
            if error_rate > 0.5:
                return True

        # Check same tool failing with different errors
        recent_tools = self.last_errors[-5:]
        if len(recent_tools) >= 3:
            tool_names = [t[0] for t in recent_tools]
            from collections import Counter
            tool_counts = Counter(tool_names)
            for tool, cnt in tool_counts.items():
                if cnt >= 3:
                    tool_errors = [e for t, e, _ in recent_tools if t == tool]
                    if len(set(tool_errors)) >= 2:
                        return True

        return False

    def decompose(self, goal: str, error_context: str = "") -> List[str]:
        """Break a goal into simpler sub-goals based on error context.

        Uses heuristics (no LLM) to split common patterns:
          - File creation + test → separate create and test
          - Multi-file changes → one file per sub-goal
          - SQL + code → separate DB and code changes
        """
        sub_goals = []

        goal_lower = goal.lower()

        # Pattern: multiple files mentioned
        import re
        file_refs = re.findall(r'@project/[\w/._-]+\.(?:py|js|ts|sql|md)', goal)
        if not file_refs:
            file_refs = re.findall(r'[\w/._-]+\.(?:py|js|ts|sql)', goal)

        if len(file_refs) >= 2:
            for f in file_refs:
                sub_goals.append(f"Modify file {f}: apply the relevant changes from the original goal.")
            if any("test" in g.lower() for g in sub_goals):
                # Move test to end
                tests = [g for g in sub_goals if "test" in g.lower()]
                others = [g for g in sub_goals if "test" not in g.lower()]
                sub_goals = others + tests
            sub_goals.append("Verify all changes work together.")
            return sub_goals

        # Pattern: SQL + code
        if "sql" in goal_lower or "db_" in goal_lower or "query" in goal_lower:
            if any(ext in goal_lower for ext in [".py", "write_file", "edit_file"]):
                sub_goals.append("Execute the database changes (SQL/migrations).")
                sub_goals.append("Implement the code changes.")
                sub_goals.append("Verify DB and code work together.")
                return sub_goals

        # Pattern: create + test
        if "test" in goal_lower and ("create" in goal_lower or "write" in goal_lower or "implement" in goal_lower):
            sub_goals.append("Implement the main functionality.")
            sub_goals.append("Run tests and fix any failures.")
            return sub_goals

        # Default: split into investigate → implement → verify
        sub_goals = [
            f"Investigate: read relevant files and understand the codebase for: {goal[:200]}",
            f"Implement: make the required changes for: {goal[:200]}",
            f"Verify: run tests and check the changes work.",
        ]
        return sub_goals

    def rollback(self, sandbox_dir: str = ".") -> Optional[str]:
        """Rollback to the last git checkpoint.

        Returns:
            Commit hash rolled back to, or None if rollback failed.
        """
        if not self._git_checkpoints:
            return None

        target_commit = self._git_checkpoints[-1]
        try:
            result = subprocess.run(
                ["git", "checkout", target_commit, "--", "."],
                capture_output=True, text=True, timeout=10,
                cwd=sandbox_dir,
            )
            if result.returncode == 0:
                self._git_checkpoints.pop()
                return target_commit
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def record_checkpoint(self, commit_hash: str) -> None:
        """Record a git checkpoint for potential rollback."""
        self._git_checkpoints.append(commit_hash)
        # Keep only last 10 checkpoints
        if len(self._git_checkpoints) > 10:
            self._git_checkpoints = self._git_checkpoints[-10:]

    def record_write(self, tool_name: str, path: str) -> None:
        """Record a file write for rollback tracking."""
        self.last_writes.append((tool_name, path))
        if len(self.last_writes) > 20:
            self.last_writes = self.last_writes[-20:]

    def reset(self) -> None:
        """Reset all error tracking state."""
        self.error_counts.clear()
        self.last_errors.clear()
        self.last_writes.clear()
