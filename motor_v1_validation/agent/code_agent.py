#!/usr/bin/env python3
"""EXP 6 — Code Agent OS: observe→think→act loop with multi-model routing.
~450 lines. API calls via subprocess+curl (Cloudflare blocks urllib/requests).
"""

import os
import sys
import re
import json
import time
import shlex
import fnmatch
import hashlib
import argparse
import subprocess
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any

# ============================================================
# CONSTANTS
# ============================================================

SANDBOX_DIR = ""  # Set at runtime
MAX_FILE_SIZE = 500_000
COMMAND_TIMEOUT = 60
MODEL_CALL_TIMEOUT = 180
TOTAL_TIMEOUT = 600
MAX_OUTPUT_LEN = 20_000

# Load API key
def _load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ============================================================
# MODELS
# ============================================================

MODELS = {
    # Exp 6 originals
    "devstral":      "mistralai/devstral-2512",
    "step-3.5":      "stepfun/step-3.5-flash",
    "mimo-v2-flash": "xiaomi/mimo-v2-flash",
    "nemotron":      "nvidia/llama-3.3-nemotron-super-49b-v1",
    # Exp 7 new models
    "devstral-small": "mistralai/devstral-small",
    "deepseek-v3.2":  "deepseek/deepseek-v3.2",
    "glm-4.7":        "z-ai/glm-4.7",
    "kat-coder":      "kwaipilot/kat-coder-pro",
    "qwen3-coder":    "qwen/qwen3-coder-next",
}

# ============================================================
# TOOLS — OpenAI function calling schema
# ============================================================

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read file contents. Returns string. Max 500KB.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path from workspace"}
        }, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write content to file. Creates dirs if needed. Overwrites.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path from workspace"},
            "content": {"type": "string", "description": "Full file content"}
        }, "required": ["path", "content"]}
    }},
    {"type": "function", "function": {
        "name": "run_command",
        "description": "Execute shell command in workspace. Returns stdout+stderr. Timeout 60s. Dangerous commands blocked.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to run"}
        }, "required": ["command"]}
    }},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List files/dirs at path. One entry per line with d/f prefix.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path. Default: '.'"}
        }, "required": []}
    }},
    {"type": "function", "function": {
        "name": "search_files",
        "description": "Search files by glob pattern or content regex.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Glob for names or regex for content"},
            "path": {"type": "string", "description": "Root dir. Default: '.'"},
            "content_search": {"type": "boolean", "description": "If true, search contents. Default: false"}
        }, "required": ["pattern"]}
    }},
    {"type": "function", "function": {
        "name": "edit_file",
        "description": "Replace exact string in file. More efficient than rewriting whole file. Fails if old_string not found or appears multiple times.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path from workspace"},
            "old_string": {"type": "string", "description": "Exact string to find and replace"},
            "new_string": {"type": "string", "description": "Replacement string"}
        }, "required": ["path", "old_string", "new_string"]}
    }},
    {"type": "function", "function": {
        "name": "glob_files",
        "description": "Find files matching glob pattern. E.g. '**/*.py', 'src/**/*.ts'.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match"},
            "path": {"type": "string", "description": "Root directory. Default: '.'"}
        }, "required": ["pattern"]}
    }},
    {"type": "function", "function": {
        "name": "grep_content",
        "description": "Search file contents for regex pattern. Returns matching lines with file:line: prefix.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "Root directory. Default: '.'"},
            "max_results": {"type": "integer", "description": "Max results. Default: 30"}
        }, "required": ["pattern"]}
    }},
    {"type": "function", "function": {
        "name": "plan",
        "description": "Create or read the execution plan. Use 'read' to see current plan, 'write' to update it.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["read", "write"], "description": "Action: 'read' or 'write'"},
            "content": {"type": "string", "description": "Plan content (only for 'write' action)"}
        }, "required": ["action"]}
    }},
    {"type": "function", "function": {
        "name": "finish",
        "description": "Signal task complete. Call when done or tests pass 100%.",
        "parameters": {"type": "object", "properties": {
            "result": {"type": "string", "description": "Summary of what was accomplished"}
        }, "required": ["result"]}
    }},
]

# ============================================================
# TOOL IMPLEMENTATIONS
# ============================================================

def _resolve_path(rel_path: str) -> str:
    """Resolve path inside sandbox. Raises ValueError if escapes."""
    abs_path = os.path.abspath(os.path.join(SANDBOX_DIR, rel_path))
    if not abs_path.startswith(os.path.abspath(SANDBOX_DIR)):
        raise ValueError(f"Path escapes sandbox: {rel_path}")
    return abs_path


def tool_read_file(path: str) -> str:
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    size = os.path.getsize(abs_path)
    if size > MAX_FILE_SIZE:
        return f"ERROR: File too large ({size} bytes, max {MAX_FILE_SIZE})"
    with open(abs_path, 'r', errors='replace') as f:
        content = f.read()
    if len(content) > MAX_OUTPUT_LEN:
        content = content[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED, {len(content)} total chars]"
    return content


def tool_write_file(path: str, content: str) -> str:
    if len(content) > MAX_FILE_SIZE:
        return f"ERROR: Content too large ({len(content)} chars, max {MAX_FILE_SIZE})"
    abs_path = _resolve_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w') as f:
        f.write(content)
    return f"OK: Written {len(content)} chars to {path}"


BLOCKED_CMDS = {'rmdir', 'dd', 'mkfs', 'chmod', 'chown', 'sudo', 'su',
                'passwd', 'shutdown', 'reboot', 'halt', 'poweroff', 'fdisk',
                'parted', 'mount', 'umount', 'killall', 'pkill'}
BLOCKED_PATTERNS = [r'\bsudo\b', r'\bdd\b\s+if=', r'>\s*/dev/',
                    r'\|\s*sh\b', r'\|\s*bash\b', r'rm\s+-rf\s+/',
                    r'rm\s+-rf\s+\*', r'rm\s+-rf\s+~']


def tool_run_command(command: str) -> str:
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            return f"ERROR: Command blocked (matched: {pattern})"
    try:
        args = shlex.split(command)
    except ValueError as e:
        return f"ERROR: Invalid syntax: {e}"
    if args and args[0] in BLOCKED_CMDS:
        return f"ERROR: Command '{args[0]}' is blocked"

    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=COMMAND_TIMEOUT, cwd=SANDBOX_DIR
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n--- STDERR ---\n" + result.stderr)
        if not output.strip():
            output = f"(exit code {result.returncode}, no output)"
        if len(output) > MAX_OUTPUT_LEN:
            output = output[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED, {len(output)} total chars]"
        return f"Exit code: {result.returncode}\n{output}"
    except subprocess.TimeoutExpired:
        return f"ERROR: Timed out after {COMMAND_TIMEOUT}s"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def tool_list_dir(path: str = ".") -> str:
    abs_path = _resolve_path(path)
    if not os.path.isdir(abs_path):
        return f"ERROR: Not a directory: {path}"
    entries = sorted(os.listdir(abs_path))
    result = []
    for entry in entries:
        full = os.path.join(abs_path, entry)
        prefix = "d " if os.path.isdir(full) else "f "
        size = ""
        if os.path.isfile(full):
            size = f" ({os.path.getsize(full)} bytes)"
        result.append(prefix + entry + size)
    return "\n".join(result) if result else "(empty directory)"


def tool_search_files(pattern: str, path: str = ".", content_search: bool = False) -> str:
    abs_root = _resolve_path(path)
    if not os.path.isdir(abs_root):
        return f"ERROR: Not a directory: {path}"
    matches = []
    if content_search:
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"ERROR: Invalid regex: {e}"
        for root_dir, _, files in os.walk(abs_root):
            for fname in files:
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, 'r', errors='replace') as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fpath, abs_root)
                                matches.append(f"{rel}:{i}: {line.rstrip()}")
                                if len(matches) >= 50:
                                    break
                except (PermissionError, IsADirectoryError):
                    continue
            if len(matches) >= 50:
                break
    else:
        for root_dir, _, files in os.walk(abs_root):
            for fname in fnmatch.filter(files, pattern):
                rel = os.path.relpath(os.path.join(root_dir, fname), abs_root)
                matches.append(rel)
                if len(matches) >= 100:
                    break
            if len(matches) >= 100:
                break
    return "\n".join(matches) if matches else "(no matches)"


def tool_edit_file(path: str, old_string: str, new_string: str) -> str:
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    with open(abs_path, 'r', errors='replace') as f:
        content = f.read()
    if old_string not in content:
        return f"ERROR: old_string not found in {path}. Read the file first to get exact content."
    count = content.count(old_string)
    if count > 1:
        return f"ERROR: old_string appears {count} times in {path}. Provide more context to be unique."
    new_content = content.replace(old_string, new_string, 1)
    with open(abs_path, 'w') as f:
        f.write(new_content)
    return f"OK: Replaced in {path} ({len(old_string)} chars → {len(new_string)} chars)"


def tool_glob_files(pattern: str, path: str = ".") -> str:
    import glob as glob_mod
    abs_root = _resolve_path(path)
    if not os.path.isdir(abs_root):
        return f"ERROR: Not a directory: {path}"
    matches = []
    for m in glob_mod.glob(os.path.join(abs_root, pattern), recursive=True):
        rel = os.path.relpath(m, abs_root)
        matches.append(rel)
        if len(matches) >= 100:
            break
    return "\n".join(matches) if matches else "(no matches)"


def tool_grep_content(pattern: str, path: str = ".", max_results: int = 30) -> str:
    abs_root = _resolve_path(path)
    if not os.path.isdir(abs_root):
        return f"ERROR: Not a directory: {path}"
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"ERROR: Invalid regex: {e}"
    matches = []
    for root_dir, _, files in os.walk(abs_root):
        for fname in files:
            if fname.endswith(('.pyc', '.pyo', '.so', '.o', '.class', '.jar')):
                continue
            fpath = os.path.join(root_dir, fname)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            rel = os.path.relpath(fpath, abs_root)
                            matches.append(f"{rel}:{i}: {line.rstrip()}")
                            if len(matches) >= max_results:
                                return "\n".join(matches) + f"\n... (limited to {max_results})"
            except (PermissionError, IsADirectoryError):
                continue
    return "\n".join(matches) if matches else "(no matches)"


# Plan storage (in-memory per session)
_PLAN_CONTENT = ""

def tool_plan(action: str, content: str = "") -> str:
    global _PLAN_CONTENT
    if action == "read":
        return _PLAN_CONTENT if _PLAN_CONTENT else "(no plan yet — use plan(action='write', content='...') to create one)"
    elif action == "write":
        _PLAN_CONTENT = content
        return f"OK: Plan updated ({len(content)} chars)"
    return f"ERROR: Unknown action '{action}'. Use 'read' or 'write'."


TOOL_DISPATCH = {
    "read_file":     lambda a: tool_read_file(a["path"]),
    "write_file":    lambda a: tool_write_file(a["path"], a["content"]),
    "run_command":   lambda a: tool_run_command(a["command"]),
    "list_dir":      lambda a: tool_list_dir(a.get("path", ".")),
    "search_files":  lambda a: tool_search_files(
        a["pattern"], a.get("path", "."), a.get("content_search", False)),
    "edit_file":     lambda a: tool_edit_file(a["path"], a["old_string"], a["new_string"]),
    "glob_files":    lambda a: tool_glob_files(a["pattern"], a.get("path", ".")),
    "grep_content":  lambda a: tool_grep_content(
        a["pattern"], a.get("path", "."), a.get("max_results", 30)),
    "plan":          lambda a: tool_plan(a["action"], a.get("content", "")),
}


def execute_tool(name: str, args: dict) -> Tuple[str, bool]:
    """Execute tool, return (result, is_error)."""
    if name not in TOOL_DISPATCH:
        return f"ERROR: Unknown tool '{name}'", True
    try:
        result = TOOL_DISPATCH[name](args)
        is_error = result.startswith("ERROR:")
        return result, is_error
    except ValueError as e:
        return f"ERROR: {e}", True
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}", True

# ============================================================
# BUDGET & STUCK DETECTION
# ============================================================

MODEL_PRICING = {  # $/M output tokens (from OpenRouter)
    "mistralai/devstral-2512": 2.00,
    "mistralai/devstral-small-2505": 0.30,
    "stepfun/step-3.5-flash": 0.30,
    "xiaomi/mimo-v2-flash": 0.29,
    "nvidia/llama-3.3-nemotron-super-49b-v1": 0.30,
    "deepseek/deepseek-chat-v3-0324": 0.38,
    "zai-org/glm-4.7": 1.98,
    "kwaipilot/kat-coder-pro": 0.83,
    "qwen/qwen3-coder-next-80b": 0.75,
}


@dataclass
class Budget:
    max_iterations: int = 100
    max_cost_usd: float = 2.0
    tokens_used: int = 0
    cost_usd: float = 0.0

    def track(self, usage: dict, model_id: str = ""):
        in_tokens = usage.get("prompt_tokens", 0)
        out_tokens = usage.get("completion_tokens", 0)
        self.tokens_used += in_tokens + out_tokens
        # Per-model pricing (output tokens dominate cost)
        price_per_m = MODEL_PRICING.get(model_id, 1.0)
        self.cost_usd += out_tokens * price_per_m / 1_000_000
        # Input tokens are typically 10-50% of output price
        self.cost_usd += in_tokens * (price_per_m * 0.25) / 1_000_000

    def exceeded(self) -> Optional[str]:
        if self.cost_usd > self.max_cost_usd:
            return f"BUDGET: ${self.cost_usd:.4f} > ${self.max_cost_usd}"
        return None


@dataclass
class StuckDetector:
    action_history: List[str] = field(default_factory=list)
    result_history: List[Tuple[str, bool]] = field(default_factory=list)  # (result_hash, is_error)
    error_history: List[str] = field(default_factory=list)
    no_tool_streak: int = 0
    iteration: int = 0

    def record_action(self, tool_name: str, args: dict, result: str, is_error: bool):
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

    def record_no_tool(self):
        self.no_tool_streak += 1
        self.iteration += 1

    def check(self) -> Optional[str]:
        # Same action 4x: only STUCK if ALL results are errors with same output
        if len(self.action_history) >= 4:
            last4_actions = self.action_history[-4:]
            last4_results = self.result_history[-4:]
            if len(set(last4_actions)) == 1:
                # Same action — but are results different? (progress = not stuck)
                result_hashes = [r[0] for r in last4_results]
                all_errors = all(r[1] for r in last4_results)
                if all_errors and len(set(result_hashes)) == 1:
                    return f"STUCK: Same action 4x with same error: {last4_actions[0]}"
                elif all_errors:
                    return f"STUCK: Same action 4x, all errors: {last4_actions[0]}"
                # Same action but different results (or some success) = making progress
        # Same error 3x
        if len(self.error_history) >= 3:
            last3 = self.error_history[-3:]
            if len(set(last3)) == 1:
                return "STUCK: Same error 3x"
        # Monologue 3x
        if self.no_tool_streak >= 3:
            return "STUCK: Monologue 3x"
        return None

# ============================================================
# MODEL ROUTER
# ============================================================

@dataclass
class ModelRouter:
    fast_model: str = "mistralai/devstral-2512"
    debug_model: str = "stepfun/step-3.5-flash"
    fallback_model: str = "xiaomi/mimo-v2-flash"
    _use_debug: bool = False
    _debug_rounds: int = 0
    _max_debug_rounds: int = 5
    _consecutive_errors: int = 0

    def select(self) -> str:
        if self._use_debug:
            self._debug_rounds += 1
            if self._debug_rounds > self._max_debug_rounds:
                self._use_debug = False
                self._debug_rounds = 0
                return self.fast_model
            return self.debug_model
        return self.fast_model

    def on_error(self, error_text: str = ""):
        # Classify error — don't switch models for non-reasoning errors
        if any(kw in error_text for kw in ["JSONDecodeError", "SyntaxError", "Invalid syntax",
                                            "Timed out", "File not found", "not a directory"]):
            return  # Tool/env errors, not reasoning failures
        self._consecutive_errors += 1
        if self._consecutive_errors >= 2:
            self._use_debug = True
            self._debug_rounds = 0

    def on_success(self):
        self._consecutive_errors = 0

# ============================================================
# API CALL
# ============================================================

def strip_think_tags(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()


def call_openrouter(messages: list, model: str, tools: list = None,
                    temperature: float = 0.0, max_tokens: int = 16384) -> dict:
    """Call OpenRouter via subprocess+curl. Returns parsed JSON response."""
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"

    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(body, tmp)
    tmp.close()

    try:
        cmd = [
            'curl', '-s', '--max-time', str(MODEL_CALL_TIMEOUT),
            '-X', 'POST', 'https://openrouter.ai/api/v1/chat/completions',
            '-H', f'Authorization: Bearer {OPENROUTER_KEY}',
            '-H', 'Content-Type: application/json',
            '-H', 'HTTP-Referer: https://omni-mind.app',
            '-H', 'X-Title: OMNI-MIND Agent',
            '-d', '@' + tmp.name
        ]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=MODEL_CALL_TIMEOUT + 15)
        if result.returncode != 0:
            raise RuntimeError(f"curl rc={result.returncode}: {result.stderr[:200]}")
        data = json.loads(result.stdout)
        if "error" in data:
            raise RuntimeError(f"API: {data['error']}")
        return data
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def call_with_retry(messages, model, tools=None, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return call_openrouter(messages, model, tools, **kwargs)
        except (json.JSONDecodeError, RuntimeError, subprocess.TimeoutExpired) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"API failed after {max_retries} tries: {e}")
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("Unreachable")


def extract_response(api_resp: dict) -> Tuple[str, Optional[list], bool]:
    """Extract content + tool_calls + reasoning_blowup flag.
    Returns (content, tool_calls, is_reasoning_blowup)."""
    msg = api_resp["choices"][0]["message"]
    content = strip_think_tags(msg.get("content") or "")
    tool_calls = msg.get("tool_calls")

    if not content and not tool_calls:
        reasoning = msg.get("reasoning", "") or ""
        if len(reasoning) > 1000:
            return "(REASONING_BLOWUP: model spent all tokens thinking, no action)", None, True
        return "(No content or tool calls)", None, False
    return content, tool_calls, False

# ============================================================
# CONTEXT MANAGEMENT
# ============================================================

def trim_history(history: list, max_tokens: int = 80000) -> list:
    """Trim history by token estimate, preserving system+task and error messages."""
    if len(history) <= 4:
        return history

    protected = history[:2]  # system + task (always keep)
    rest = history[2:]

    def _estimate_tokens(msg):
        content = msg.get("content", "")
        return len(content) // 4 if content else 10

    total = sum(_estimate_tokens(m) for m in rest)
    if total <= max_tokens:
        return history

    # Keep from end, but also preserve messages containing ERROR/FAILED
    kept_from_end = []
    tokens_used = 0
    error_messages = []

    # First pass: identify important error messages in older history
    cutoff = len(rest) // 2  # only search older half
    for i, msg in enumerate(rest[:cutoff]):
        content = msg.get("content", "") or ""
        if any(kw in content for kw in ["ERROR:", "FAILED", "Traceback", "AssertionError"]):
            error_messages.append(msg)

    # Second pass: keep last N messages that fit in budget
    error_tokens = sum(_estimate_tokens(m) for m in error_messages[:5])
    remaining_budget = max_tokens - error_tokens

    for msg in reversed(rest):
        msg_tokens = _estimate_tokens(msg)
        if tokens_used + msg_tokens > remaining_budget:
            break
        kept_from_end.insert(0, msg)
        tokens_used += msg_tokens

    return protected + error_messages[:5] + kept_from_end

# ============================================================
# MAIN AGENT LOOP
# ============================================================

SYSTEM_PROMPT = (
    "You are a coding agent. You write, test, and debug code in a sandboxed workspace.\n\n"
    "RULES:\n"
    "1. Always use tools to interact with the environment. Never guess file contents.\n"
    "2. After writing code, ALWAYS run tests to verify it works.\n"
    "3. If tests pass at 100%, call finish() immediately. Do NOT refactor working code.\n"
    "4. Read the EXACT error message carefully before fixing.\n"
    "5. Use list_dir and search_files to explore before modifying.\n"
    "6. Call finish(result='...') when task is complete.\n"
    "7. Write complete files — never partial snippets.\n"
    "8. For Python: use pytest. For TypeScript: use Deno.test. For SQL: validate structure.\n"
    "9. Install dependencies with pip3 install if needed.\n"
    "10. If you get the same error 3 times, try a completely different approach.\n"
)


def run_agent(goal: str, max_iterations: int = 25,
              fast_model: str = None, debug_model: str = None,
              single_model: str = None, verbose: bool = False,
              sandbox_dir: str = None) -> dict:
    """Main agent loop. Returns result dict."""
    global SANDBOX_DIR
    if sandbox_dir:
        SANDBOX_DIR = sandbox_dir
    else:
        SANDBOX_DIR = tempfile.mkdtemp(prefix="agent_")
    os.makedirs(SANDBOX_DIR, exist_ok=True)

    router = ModelRouter()
    if single_model:
        model_id = MODELS.get(single_model, single_model)
        router.fast_model = model_id
        router.debug_model = model_id
        router.fallback_model = model_id
    else:
        if fast_model:
            router.fast_model = MODELS.get(fast_model, fast_model)
        if debug_model:
            router.debug_model = MODELS.get(debug_model, debug_model)

    budget = Budget(max_iterations=max_iterations)
    stuck = StuckDetector()

    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"TASK:\n{goal}\n\nWorkspace directory: {SANDBOX_DIR}\nAvailable runtimes: python3, pytest, deno, node.\nStart by understanding the task, then implement and test."},
    ]

    log = []
    start_time = time.time()
    stop_reason = None
    final_result = None

    for iteration in range(max_iterations):
        elapsed = time.time() - start_time
        if elapsed > TOTAL_TIMEOUT:
            stop_reason = f"TIMEOUT ({TOTAL_TIMEOUT}s)"
            break

        budget_err = budget.exceeded()
        if budget_err:
            stop_reason = budget_err
            break

        stuck_reason = stuck.check()
        if stuck_reason:
            stop_reason = stuck_reason
            break

        # Select model
        model = router.select()
        if verbose:
            print(f"  [{iteration+1}/{max_iterations}] model={model.split('/')[-1]}", end="", flush=True)

        # Call model
        try:
            api_resp = call_with_retry(history, model, tools=TOOLS)
        except RuntimeError as e:
            # Try fallback
            try:
                api_resp = call_with_retry(history, router.fallback_model, tools=TOOLS, max_retries=1)
                model = router.fallback_model
            except RuntimeError:
                stop_reason = f"API_FAILURE: {e}"
                break

        usage = api_resp.get("usage", {})
        budget.track(usage, model)
        content, tool_calls, is_blowup = extract_response(api_resp)

        # Reasoning blowup — switch model immediately
        if is_blowup:
            if verbose:
                print(f" (REASONING BLOWUP — switching model)")
            history.append({"role": "assistant", "content": content or "(empty)"})
            history.append({"role": "user", "content": "You spent all tokens reasoning without acting. USE A TOOL NOW. Start with list_dir to see the workspace."})
            # Force switch to a different model
            if model == router.debug_model:
                router._use_debug = False
            else:
                router.on_error()
                router.on_error()  # Force debug mode
            stuck.record_no_tool()
            history = trim_history(history)
            continue

        # No tool calls — monologue
        if not tool_calls:
            if verbose:
                print(f" (no tool call)")
            history.append({"role": "assistant", "content": content or "(empty)"})
            stuck.record_no_tool()
            # If model can't use tools, add a nudge then switch
            if stuck.no_tool_streak == 2:
                history.append({"role": "user", "content": "Please use one of your tools (write_file, run_command, etc.) to make progress on the task. Do not just describe what to do — actually do it."})
            elif stuck.no_tool_streak >= 3:
                # Switch model instead of just stopping
                if model == router.fast_model:
                    router._use_debug = True
                    router._debug_rounds = 0
                else:
                    router._use_debug = False
                history.append({"role": "user", "content": "CRITICAL: You MUST use a tool now. Call list_dir('.') to start."})
            history = trim_history(history)
            continue

        # Process tool calls (handle all of them)
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

            # Handle finish
            if tool_name == "finish":
                final_result = tool_args.get("result", "Task completed")
                history.append({"role": "tool", "tool_call_id": tc_id, "content": final_result})
                stop_reason = "DONE"
                if verbose:
                    print(f" → finish: {final_result[:80]}")
                log.append({"iter": iteration+1, "tool": "finish", "model": model,
                            "tokens": usage.get("total_tokens", 0)})
                break

            # Execute tool
            result_str, is_error = execute_tool(tool_name, tool_args)
            history.append({"role": "tool", "tool_call_id": tc_id, "content": result_str})

            if verbose:
                status = "ERR" if is_error else "OK"
                result_preview = result_str[:80].replace('\n', ' ')
                print(f" → {tool_name}({status}): {result_preview}")

            stuck.record_action(tool_name, tool_args, result_str, is_error)

            if is_error:
                router.on_error(result_str)
            else:
                router.on_success()

            log.append({
                "iter": iteration+1, "tool": tool_name, "model": model,
                "is_error": is_error, "tokens": usage.get("total_tokens", 0),
                "result_preview": result_str[:200],
            })

        if stop_reason:
            break

        history = trim_history(history)

    total_time = time.time() - start_time
    return {
        "result": final_result,
        "stop_reason": stop_reason or "MAX_ITERATIONS",
        "iterations": stuck.iteration,
        "tokens_used": budget.tokens_used,
        "estimated_cost_usd": round(budget.cost_usd, 4),
        "time_s": round(total_time, 1),
        "sandbox_dir": SANDBOX_DIR,
        "log": log,
    }

# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Code Agent OS — EXP 6")
    parser.add_argument("--goal", required=True, help="Task description")
    parser.add_argument("--max-iter", type=int, default=25, help="Max iterations (default 25)")
    parser.add_argument("--model", help="Force single model (e.g. devstral, step-3.5, mimo-v2-flash)")
    parser.add_argument("--fast-model", help="Override fast model")
    parser.add_argument("--debug-model", help="Override debug model")
    parser.add_argument("--verbose", action="store_true", help="Log each iteration")
    parser.add_argument("--sandbox", help="Override sandbox directory")
    args = parser.parse_args()

    if not OPENROUTER_KEY:
        print("ERROR: OPENROUTER_API_KEY not set in .env")
        sys.exit(1)

    print(f"Agent starting — goal: {args.goal[:80]}...")
    print(f"Max iterations: {args.max_iter}")

    result = run_agent(
        goal=args.goal,
        max_iterations=args.max_iter,
        single_model=args.model,
        fast_model=args.fast_model,
        debug_model=args.debug_model,
        verbose=args.verbose,
        sandbox_dir=args.sandbox,
    )

    print(f"\n{'='*60}")
    print(f"Stop reason: {result['stop_reason']}")
    print(f"Iterations:  {result['iterations']}")
    print(f"Tokens:      {result['tokens_used']}")
    print(f"Cost:        ${result['estimated_cost_usd']:.4f}")
    print(f"Time:        {result['time_s']}s")
    print(f"Sandbox:     {result['sandbox_dir']}")
    if result['result']:
        print(f"Result:      {result['result'][:200]}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
