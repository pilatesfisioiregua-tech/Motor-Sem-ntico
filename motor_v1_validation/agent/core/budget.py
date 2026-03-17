"""Budget tracking + stuck detection for agent loop."""

import json
import hashlib
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from .api import get_model_pricing


@dataclass
class Budget:
    max_iterations: int = 100
    max_cost_usd: float = 5.0
    tokens_used: int = 0
    cost_usd: float = 0.0

    def track(self, usage: dict, model_id: str = "", override_cost: float = 0.0) -> None:
        if override_cost > 0:
            self.cost_usd += override_cost
            return
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        self.tokens_used += in_tokens + out_tokens
        price_per_m = get_model_pricing(model_id)
        self.cost_usd += out_tokens * price_per_m / 1_000_000
        self.cost_usd += in_tokens * (price_per_m * 0.25) / 1_000_000

    def exceeded(self) -> Optional[str]:
        if self.cost_usd > self.max_cost_usd:
            return f"BUDGET: ${self.cost_usd:.4f} > ${self.max_cost_usd}"
        return None

    def summary(self) -> dict:
        return {
            "tokens_used": self.tokens_used,
            "cost_usd": round(self.cost_usd, 4),
            "budget_remaining": round(self.max_cost_usd - self.cost_usd, 4),
        }


@dataclass
class StuckDetector:
    action_history: List[str] = field(default_factory=list)
    result_history: List[Tuple[str, bool]] = field(default_factory=list)
    error_history: List[str] = field(default_factory=list)
    no_tool_streak: int = 0
    iteration: int = 0

    def record_action(self, tool_name: str, args: dict, result: str, is_error: bool) -> None:
        key = f"{tool_name}:{hashlib.md5(json.dumps(args, sort_keys=True).encode()).hexdigest()[:8]}"
        self.action_history.append(key)
        result_hash = hashlib.md5(result[:500].encode()).hexdigest()[:8]
        self.result_history.append((result_hash, is_error))
        if is_error:
            self.error_history.append(result[:200])
        else:
            self.error_history.clear()
        self.no_tool_streak = 0
        self.iteration += 1

    def record_no_tool(self) -> None:
        self.no_tool_streak += 1
        self.iteration += 1

    def check(self) -> Optional[str]:
        # Same action 4x with same error
        if len(self.action_history) >= 4:
            last4_actions = self.action_history[-4:]
            last4_results = self.result_history[-4:]
            if len(set(last4_actions)) == 1:
                result_hashes = [r[0] for r in last4_results]
                all_errors = all(r[1] for r in last4_results)
                if all_errors and len(set(result_hashes)) == 1:
                    return f"STUCK: Same action 4x with same error: {last4_actions[0]}"
                elif all_errors:
                    return f"STUCK: Same action 4x, all errors: {last4_actions[0]}"
        # Same error 3x
        if len(self.error_history) >= 3:
            last3 = self.error_history[-3:]
            if len(set(last3)) == 1:
                return "STUCK: Same error 3x"
        # Monologue 3x
        if self.no_tool_streak >= 3:
            return "STUCK: Monologue 3x"
        # Loop detection
        loop = self.detect_loop()
        if loop:
            return loop
        # Regression detection
        regression = self.detect_regression()
        if regression:
            return regression
        return None

    def detect_loop(self) -> Optional[str]:
        """Detect A→B→A→B cycles in action history (length 2-4 patterns)."""
        if len(self.action_history) < 6:
            return None
        # Check for cycles of length 2, 3, 4
        for cycle_len in (2, 3, 4):
            needed = cycle_len * 3  # Need 3 repetitions to confirm
            if len(self.action_history) < needed:
                continue
            recent = self.action_history[-needed:]
            pattern = recent[:cycle_len]
            is_cycle = True
            for i in range(cycle_len, needed, cycle_len):
                if recent[i:i+cycle_len] != pattern:
                    is_cycle = False
                    break
            if is_cycle:
                return f"STUCK: Loop detected — pattern {pattern} repeated {needed // cycle_len}x"
        return None

    def detect_regression(self) -> Optional[str]:
        """Detect regression: success→error→error pattern on same tool.

        Returns warning when a tool that was working starts failing consistently.
        """
        if len(self.result_history) < 5:
            return None
        # Look for pattern: at least 2 successes followed by 3+ errors on same tool
        last_n = min(len(self.action_history), 8)
        actions = self.action_history[-last_n:]
        results = self.result_history[-last_n:]
        # Find transitions from success to error for same tool
        for i in range(1, len(actions)):
            if (actions[i] == actions[i-1]
                    and not results[i-1][1]  # previous was success
                    and results[i][1]):        # current is error
                # Count consecutive errors after this point
                consecutive_errors = 0
                for j in range(i, len(actions)):
                    if actions[j] == actions[i] and results[j][1]:
                        consecutive_errors += 1
                    else:
                        break
                if consecutive_errors >= 3:
                    return f"STUCK: Regression — {actions[i]} was working, now failing {consecutive_errors}x"
        return None


class ProgressTracker:
    """Track tool actions to detect progress vs stagnation."""

    def __init__(self, goal: str):
        self.goal = goal
        self.keywords = [w.lower() for w in goal.split() if len(w) > 3][:20]
        self._actions: List[Tuple[str, str, bool]] = []  # (tool, result_hash, is_error)

    def record_action(self, tool_name: str, result: str, is_error: bool) -> None:
        result_hash = hashlib.md5(result[:500].encode()).hexdigest()[:8]
        self._actions.append((tool_name, result_hash, is_error))

    def get_signal(self) -> dict:
        tools_ok = sum(1 for _, _, e in self._actions if not e)
        tools_error = sum(1 for _, _, e in self._actions if e)
        error_rate = tools_error / max(len(self._actions), 1)
        # Trend based on last 3 actions
        last3 = self._actions[-3:] if len(self._actions) >= 3 else self._actions
        if all(not e for _, _, e in last3) and len(last3) == 3:
            trend = "progressing"
        elif all(e for _, _, e in last3) and len(last3) == 3:
            trend = "stuck"
        else:
            trend = "mixed"
        return {
            "tools_ok": tools_ok,
            "tools_error": tools_error,
            "error_rate": round(error_rate, 2),
            "trend": trend,
        }

    def stagnant(self) -> bool:
        """True if last 5 actions are identical (same tool + same result hash)."""
        if len(self._actions) < 5:
            return False
        last5 = self._actions[-5:]
        signatures = [(t, h) for t, h, _ in last5]
        return len(set(signatures)) == 1
