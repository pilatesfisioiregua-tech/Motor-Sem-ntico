"""Code review tools — review_code, suggest_improvements."""

import os
import re
import ast
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def _analyze_python_file(filepath: str) -> list:
    """Analyze a Python file for code smells and issues."""
    issues = []
    try:
        with open(filepath, 'r', errors='replace') as f:
            source = f.read()
        lines = source.splitlines()
        tree = ast.parse(source)
    except SyntaxError as e:
        return [{"severity": "error", "line": e.lineno or 0, "message": f"Syntax error: {e}"}]
    except Exception:
        return []

    for node in ast.walk(tree):
        # Long functions (>50 lines)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, 'end_lineno', node.lineno + 10)
            func_len = end_line - node.lineno
            if func_len > 50:
                issues.append({
                    "severity": "warning",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' is {func_len} lines long (>50). Consider splitting.",
                    "type": "long_function",
                })
            # Too many arguments
            if len(node.args.args) > 7:
                issues.append({
                    "severity": "warning",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' has {len(node.args.args)} args (>7). Use a config object.",
                    "type": "too_many_args",
                })
        # Bare except
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                issues.append({
                    "severity": "warning",
                    "line": node.lineno,
                    "message": "Bare 'except:' catches all exceptions. Be specific.",
                    "type": "bare_except",
                })
        # TODO/FIXME/HACK comments
    for i, line in enumerate(lines, 1):
        for marker in ["TODO", "FIXME", "HACK", "XXX"]:
            if marker in line:
                issues.append({
                    "severity": "info",
                    "line": i,
                    "message": f"Found {marker}: {line.strip()[:100]}",
                    "type": "todo_marker",
                })

    # Long lines (>120 chars)
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            issues.append({
                "severity": "info",
                "line": i,
                "message": f"Line is {len(line)} chars (>120).",
                "type": "long_line",
            })

    return issues[:30]


def tool_review_code(file_path: str) -> str:
    """Review a code file for issues: long functions, complexity, naming, TODOs."""
    abs_path = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {file_path}"

    if file_path.endswith('.py'):
        issues = _analyze_python_file(abs_path)
    else:
        # Generic review: line count, TODOs, long lines
        with open(abs_path, 'r', errors='replace') as f:
            lines = f.readlines()
        issues = []
        for i, line in enumerate(lines, 1):
            for marker in ["TODO", "FIXME", "HACK"]:
                if marker in line:
                    issues.append({"severity": "info", "line": i,
                                  "message": f"{marker}: {line.strip()[:100]}"})
            if len(line) > 120:
                issues.append({"severity": "info", "line": i,
                              "message": f"Long line ({len(line)} chars)"})

    return json.dumps({
        "file": file_path,
        "total_issues": len(issues),
        "issues": issues,
        "summary": {
            "errors": sum(1 for i in issues if i["severity"] == "error"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        }
    }, indent=2)


def tool_suggest_improvements(file_path: str) -> str:
    """Suggest code improvements: naming, patterns, simplification."""
    abs_path = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {file_path}"

    with open(abs_path, 'r', errors='replace') as f:
        content = f.read()

    suggestions = []

    # Python-specific
    if file_path.endswith('.py'):
        # Missing type hints
        for match in re.finditer(r'def (\w+)\(([^)]*)\)(?!.*->)', content):
            suggestions.append({
                "type": "type_hints",
                "message": f"Function '{match.group(1)}' missing return type hint.",
            })
        # Using print instead of logging
        print_count = len(re.findall(r'\bprint\(', content))
        if print_count > 5:
            suggestions.append({
                "type": "logging",
                "message": f"Found {print_count} print() calls. Consider using logging module.",
            })
        # Magic numbers
        for match in re.finditer(r'(?<!["\'])\b(\d{4,})\b(?!["\'])', content):
            num = match.group(1)
            if num not in ('0000', '1000', '10000'):
                suggestions.append({
                    "type": "magic_number",
                    "message": f"Magic number {num} — consider using a named constant.",
                })

    return json.dumps({
        "file": file_path,
        "suggestions": suggestions[:20],
        "total": len(suggestions),
    }, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("review_code", {
        "name": "review_code",
        "description": "Review code file for issues: long functions, bare excepts, TODOs, complexity.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "File to review"}
        }, "required": ["file_path"]}
    }, lambda a: tool_review_code(a["file_path"]), category="review")

    registry.register("suggest_improvements", {
        "name": "suggest_improvements",
        "description": "Suggest code improvements: missing type hints, logging, naming.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "File to analyze"}
        }, "required": ["file_path"]}
    }, lambda a: tool_suggest_improvements(a["file_path"]), category="review")
