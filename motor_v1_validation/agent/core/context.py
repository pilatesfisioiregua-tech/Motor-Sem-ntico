"""Context management — LLM-powered compression + history management."""

import json
from typing import List, Optional

from .api import call_with_retry, TIER_CONFIG, call_model_with_retry, get_tier_config


def _estimate_tokens(msg: dict) -> int:
    content = msg.get("content", "")
    return len(content) // 4 if content else 10


def estimate_history_tokens(history: list) -> int:
    return sum(_estimate_tokens(m) for m in history)


class ContextManager:
    """Manages conversation history with LLM-powered compression."""

    def __init__(self, max_tokens: int = 80000, compress_threshold: int = 60000,
                 keep_last_n: int = 6):
        self.max_tokens = max_tokens
        self.compress_threshold = compress_threshold
        self.keep_last_n = keep_last_n
        self.compression_count = 0
        self.summaries: List[str] = []

    def reset(self):
        """Hard reset — nuevo paso, cero historial."""
        self.compression_count = 0
        self.summaries = []

    def maybe_compress(self, history: list) -> list:
        """Compress history if it exceeds threshold. Returns new history."""
        total = estimate_history_tokens(history)
        if total <= self.compress_threshold:
            return history
        if len(history) <= self.keep_last_n + 2:
            return history

        # Try LLM compression first, fall back to trim
        compressed = self._llm_compress(history)
        if compressed:
            result = compressed
        else:
            result = self._trim_history(history)

        # HARD LIMIT — si tras comprimir sigue por encima de max_tokens, forzar trim agresivo
        if estimate_history_tokens(result) > self.max_tokens:
            result = self._force_trim(result)

        return result

    def _llm_compress(self, history: list) -> Optional[list]:
        """Compress via LLM (Devstral Small — $0.001/compression)."""
        protected = history[:2]  # system + task
        rest = history[2:]
        to_compress = rest[:-self.keep_last_n] if len(rest) > self.keep_last_n else []
        to_keep = rest[-self.keep_last_n:] if len(rest) > self.keep_last_n else rest

        if not to_compress:
            return None

        # Build compression input
        compressed_text = ""
        for msg in to_compress:
            role = msg.get("role", "?")
            content = msg.get("content", "")[:500]
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                tools_summary = ", ".join(
                    tc.get("function", {}).get("name", "?") for tc in tool_calls
                )
                compressed_text += f"[{role}] tools: {tools_summary}\n"
            elif content:
                compressed_text += f"[{role}] {content[:300]}\n"

        if len(compressed_text) < 500:
            return None  # Not worth compressing

        compress_messages = [
            {"role": "system", "content": (
                "Summarize this agent conversation into a structured JSON. "
                "Focus on: what was accomplished, what failed, key files modified, "
                "current approach, and important errors."
            )},
            {"role": "user", "content": (
                f"Summarize this conversation history:\n\n{compressed_text[:8000]}\n\n"
                "Respond in JSON: {\"completed\": [...], \"failed\": [...], "
                "\"pending\": [...], \"key_files\": [...], \"approach\": \"...\", "
                "\"important_errors\": [...]}"
            )},
        ]

        try:
            resp = call_with_retry(compress_messages, TIER_CONFIG["compress"],
                                   max_retries=1, max_tokens=2048)
            content = resp["choices"][0]["message"].get("content", "")
            # Strip code blocks if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            summary = json.loads(content)
            self.summaries.append(summary)
            self.compression_count += 1

            # Inject summary as system context
            summary_msg = {
                "role": "user",
                "content": (
                    f"[CONTEXT SUMMARY — compression #{self.compression_count}]\n"
                    f"Completed: {json.dumps(summary.get('completed', []))}\n"
                    f"Failed: {json.dumps(summary.get('failed', []))}\n"
                    f"Key files: {json.dumps(summary.get('key_files', []))}\n"
                    f"Approach: {summary.get('approach', 'unknown')}\n"
                    f"Errors: {json.dumps(summary.get('important_errors', []))}\n"
                    "Continue from where you left off."
                ),
            }
            return protected + [summary_msg] + to_keep

        except Exception:
            return None  # Fall back to trim

    def _force_trim(self, history: list) -> list:
        """Nuclear option — keep only system + last N messages."""
        protected = history[:2]  # system + task
        recent = history[-self.keep_last_n:]
        return protected + recent

    def _trim_history(self, history: list) -> list:
        """Fallback: trim history preserving system+task and error messages."""
        if len(history) <= 4:
            return history

        protected = history[:2]
        rest = history[2:]

        # Find error messages in older half
        cutoff = len(rest) // 2
        error_messages = []
        for msg in rest[:cutoff]:
            content = msg.get("content", "") or ""
            if any(kw in content for kw in ["ERROR:", "FAILED", "Traceback", "AssertionError"]):
                error_messages.append(msg)

        error_tokens = sum(_estimate_tokens(m) for m in error_messages[:5])
        remaining_budget = self.max_tokens - error_tokens

        kept = []
        tokens_used = 0
        for msg in reversed(rest):
            msg_tokens = _estimate_tokens(msg)
            if tokens_used + msg_tokens > remaining_budget:
                break
            kept.insert(0, msg)
            tokens_used += msg_tokens

        return protected + error_messages[:5] + kept
