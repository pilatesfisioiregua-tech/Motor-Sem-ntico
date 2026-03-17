"""Testing tools — run_tests, run_linter, check_coverage."""

import os
import re
import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""
COMMAND_TIMEOUT = 120


def _run_cmd(cmd: str, cwd: str = None, timeout: int = None) -> tuple:
    """Run command, return (stdout+stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout or COMMAND_TIMEOUT,
            cwd=cwd or _SANDBOX
        )
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        return output, result.returncode
    except subprocess.TimeoutExpired:
        return f"ERROR: Timed out after {timeout or COMMAND_TIMEOUT}s", -1


def _detect_framework(path: str = None) -> str:
    """Auto-detect test framework from project files."""
    root = path or _SANDBOX
    if os.path.isfile(os.path.join(root, "pytest.ini")) or \
       os.path.isfile(os.path.join(root, "conftest.py")) or \
       os.path.isfile(os.path.join(root, "setup.cfg")):
        return "pytest"
    if os.path.isfile(os.path.join(root, "package.json")):
        try:
            with open(os.path.join(root, "package.json")) as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "jest" in deps:
                    return "jest"
                if "vitest" in deps:
                    return "vitest"
        except (json.JSONDecodeError, IOError):
            pass
    if os.path.isfile(os.path.join(root, "deno.json")):
        return "deno"
    if os.path.isfile(os.path.join(root, "go.mod")):
        return "go"
    # Default for Python projects
    for root_dir, _, files in os.walk(root):
        if any(f.startswith("test_") and f.endswith(".py") for f in files):
            return "pytest"
        if root_dir.count(os.sep) > 3:
            break
    return "pytest"


def _parse_pytest(output: str) -> dict:
    """Parse pytest output into structured JSON."""
    result = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0,
              "failures": [], "total": 0, "raw": output[-3000:]}

    # Parse summary line: "5 passed, 2 failed, 1 error"
    summary_match = re.search(
        r'=+ ([\d]+ passed)?[,\s]*([\d]+ failed)?[,\s]*([\d]+ error)?[,\s]*([\d]+ skipped)?',
        output
    )
    if summary_match:
        for group in summary_match.groups():
            if group:
                num = int(re.search(r'\d+', group).group())
                if 'passed' in group:
                    result["passed"] = num
                elif 'failed' in group:
                    result["failed"] = num
                elif 'error' in group:
                    result["errors"] = num
                elif 'skipped' in group:
                    result["skipped"] = num

    result["total"] = result["passed"] + result["failed"] + result["errors"]

    # Extract failure details
    failure_blocks = re.findall(
        r'FAILED ([\w/\.]+::\w+).*?(?=FAILED|={3,}|\Z)',
        output, re.DOTALL
    )
    for fb in failure_blocks[:10]:
        result["failures"].append(fb.strip()[:300])

    return result


def tool_run_tests(framework: str = "", path: str = "", args: str = "") -> str:
    """Run tests and return structured JSON results."""
    fw = framework or _detect_framework(path or _SANDBOX)
    test_path = path or "."

    if fw == "pytest":
        cmd = f"python3 -m pytest {test_path} -v --tb=short {args}"
    elif fw == "jest":
        cmd = f"npx jest {test_path} --verbose {args}"
    elif fw == "vitest":
        cmd = f"npx vitest run {test_path} {args}"
    elif fw == "deno":
        cmd = f"deno test {test_path} {args}"
    elif fw == "go":
        cmd = f"go test {test_path} -v {args}"
    else:
        cmd = f"python3 -m pytest {test_path} -v --tb=short {args}"

    output, rc = _run_cmd(cmd)

    if fw == "pytest":
        parsed = _parse_pytest(output)
        parsed["framework"] = "pytest"
        parsed["exit_code"] = rc
        return json.dumps(parsed, indent=2)

    # Generic parsing for other frameworks
    return json.dumps({
        "framework": fw,
        "exit_code": rc,
        "output": output[-5000:],
        "passed": output.lower().count("pass"),
        "failed": output.lower().count("fail"),
    }, indent=2)


def tool_run_linter(language: str = "python", path: str = ".", args: str = "") -> str:
    """Run linter and return issues found."""
    if language == "python":
        # Try ruff first (fast), fall back to flake8
        cmd = f"python3 -m ruff check {path} --output-format json {args}"
        output, rc = _run_cmd(cmd, timeout=30)
        if "No module named ruff" in output:
            cmd = f"python3 -m flake8 {path} --format json {args}"
            output, rc = _run_cmd(cmd, timeout=30)
            if "No module named flake8" in output:
                cmd = f"python3 -m py_compile {path}"
                output, rc = _run_cmd(cmd, timeout=15)
                return json.dumps({"linter": "py_compile", "exit_code": rc, "output": output[:3000]})
        try:
            issues = json.loads(output)
            return json.dumps({"linter": "ruff", "issues": issues[:50],
                              "total": len(issues) if isinstance(issues, list) else 0})
        except json.JSONDecodeError:
            return json.dumps({"linter": "ruff", "exit_code": rc, "output": output[:3000]})

    elif language in ("javascript", "typescript", "js", "ts"):
        cmd = f"npx eslint {path} --format json {args}"
        output, rc = _run_cmd(cmd, timeout=30)
        return json.dumps({"linter": "eslint", "exit_code": rc, "output": output[:5000]})

    elif language == "rust":
        cmd = f"cargo clippy --message-format json {args}"
        output, rc = _run_cmd(cmd, timeout=60)
        return json.dumps({"linter": "clippy", "exit_code": rc, "output": output[:5000]})

    return f"ERROR: Unsupported language '{language}'. Supported: python, javascript, typescript, rust"


def tool_check_coverage(path: str = ".", threshold: float = 0) -> str:
    """Check test coverage percentage."""
    cmd = f"python3 -m pytest {path} --cov --cov-report=json --cov-report=term-missing -q"
    output, rc = _run_cmd(cmd, timeout=120)

    # Try to parse coverage JSON
    cov_file = os.path.join(_SANDBOX, "coverage.json")
    if os.path.isfile(cov_file):
        try:
            with open(cov_file) as f:
                cov_data = json.load(f)
            total = cov_data.get("totals", {})
            return json.dumps({
                "coverage_percent": total.get("percent_covered", 0),
                "lines_covered": total.get("covered_lines", 0),
                "lines_missing": total.get("missing_lines", 0),
                "files": {k: v.get("summary", {}).get("percent_covered", 0)
                         for k, v in cov_data.get("files", {}).items()},
            }, indent=2)
        except (json.JSONDecodeError, IOError):
            pass

    # Fallback: parse text output
    cov_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', output)
    coverage = int(cov_match.group(1)) if cov_match else -1

    return json.dumps({
        "coverage_percent": coverage,
        "raw_output": output[-3000:],
        "exit_code": rc,
    }, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("run_tests", {
        "name": "run_tests",
        "description": "Run tests and return structured JSON results. Auto-detects pytest/jest/deno/go.",
        "parameters": {"type": "object", "properties": {
            "framework": {"type": "string", "description": "Test framework. Auto-detected if empty."},
            "path": {"type": "string", "description": "Test path. Default: '.'"},
            "args": {"type": "string", "description": "Additional arguments"}
        }, "required": []}
    }, lambda a: tool_run_tests(a.get("framework", ""), a.get("path", ""), a.get("args", "")),
    category="testing")

    registry.register("run_linter", {
        "name": "run_linter",
        "description": "Run linter (ruff/eslint/clippy) and return issues as JSON.",
        "parameters": {"type": "object", "properties": {
            "language": {"type": "string", "description": "Language: python, javascript, typescript, rust"},
            "path": {"type": "string", "description": "Path to lint. Default: '.'"},
            "args": {"type": "string", "description": "Additional arguments"}
        }, "required": []}
    }, lambda a: tool_run_linter(a.get("language", "python"), a.get("path", "."), a.get("args", "")),
    category="testing")

    registry.register("check_coverage", {
        "name": "check_coverage",
        "description": "Check test coverage percentage. Returns coverage % and uncovered files.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Default: '.'"},
            "threshold": {"type": "number", "description": "Minimum coverage threshold (0-100)"}
        }, "required": []}
    }, lambda a: tool_check_coverage(a.get("path", "."), a.get("threshold", 0)),
    category="testing")
