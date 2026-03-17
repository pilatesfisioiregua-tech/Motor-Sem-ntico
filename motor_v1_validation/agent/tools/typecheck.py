"""Type checking tool — type_check (mypy/tsc)."""

import os
import re
import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def tool_type_check(path: str = ".", language: str = "") -> str:
    """Run type checker (mypy for Python, tsc for TypeScript)."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path

    # Auto-detect language
    if not language:
        if os.path.isfile(os.path.join(root, "tsconfig.json")):
            language = "typescript"
        else:
            language = "python"

    if language == "python":
        try:
            result = subprocess.run(
                f"python3 -m mypy {root} --no-color-output --show-error-codes",
                shell=True, capture_output=True, text=True, timeout=60,
                cwd=_SANDBOX
            )
            output = result.stdout + result.stderr
            # Parse mypy output
            errors = []
            for line in output.splitlines():
                match = re.match(r'(.+?):(\d+):\s*(error|warning|note):\s*(.+)', line)
                if match:
                    errors.append({
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "severity": match.group(3),
                        "message": match.group(4),
                    })
            return json.dumps({
                "checker": "mypy",
                "total_errors": len([e for e in errors if e["severity"] == "error"]),
                "total_warnings": len([e for e in errors if e["severity"] == "warning"]),
                "errors": errors[:30],
                "exit_code": result.returncode,
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "mypy timed out after 60s"})
        except FileNotFoundError:
            return json.dumps({"error": "mypy not installed. Run: pip install mypy"})

    elif language in ("typescript", "ts"):
        try:
            result = subprocess.run(
                "npx tsc --noEmit --pretty false",
                shell=True, capture_output=True, text=True, timeout=60,
                cwd=root
            )
            output = result.stdout + result.stderr
            errors = []
            for line in output.splitlines():
                match = re.match(r'(.+?)\((\d+),\d+\):\s*error\s+(TS\d+):\s*(.+)', line)
                if match:
                    errors.append({
                        "file": match.group(1),
                        "line": int(match.group(2)),
                        "code": match.group(3),
                        "message": match.group(4),
                    })
            return json.dumps({
                "checker": "tsc",
                "total_errors": len(errors),
                "errors": errors[:30],
                "exit_code": result.returncode,
            }, indent=2)
        except subprocess.TimeoutExpired:
            return json.dumps({"error": "tsc timed out after 60s"})

    return json.dumps({"error": f"Unsupported language: {language}. Use: python, typescript."})


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("type_check", {
        "name": "type_check",
        "description": "Run type checker (mypy for Python, tsc for TypeScript). Returns errors as JSON.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to check. Default: '.'"},
            "language": {"type": "string", "description": "Language: python, typescript. Auto-detected."}
        }, "required": []}
    }, lambda a: tool_type_check(a.get("path", "."), a.get("language", "")), category="typecheck")
