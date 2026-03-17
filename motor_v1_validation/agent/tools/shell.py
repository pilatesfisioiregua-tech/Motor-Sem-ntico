"""Shell tool — run_command with sandboxing and safety."""

import os
import re
import shlex
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

COMMAND_TIMEOUT = 60
MAX_OUTPUT_LEN = 20_000
_SANDBOX = ""
_PROJECT_DIR = ""

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
            timeout=COMMAND_TIMEOUT, cwd=_PROJECT_DIR or _SANDBOX
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


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "",
                   project_dir: str = "") -> None:
    global _SANDBOX, _PROJECT_DIR
    _SANDBOX = sandbox_dir
    _PROJECT_DIR = project_dir

    registry.register("run_command", {
        "name": "run_command",
        "description": "Execute shell command in workspace. Timeout 60s. Dangerous commands blocked.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "Shell command to run"}
        }, "required": ["command"]}
    }, lambda a: tool_run_command(a["command"]), category="shell")
