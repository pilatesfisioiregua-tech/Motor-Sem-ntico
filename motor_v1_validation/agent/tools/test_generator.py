"""Test generation tools — generate_tests, generate_test_plan, coverage_gaps."""

import os
import ast
import json
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".mypy_cache", ".pytest_cache", ".tox",
}


# ═══════════════════════════════════════════════════════════════
# AST helpers
# ═══════════════════════════════════════════════════════════════

def _ast_analyze(filepath: str) -> Dict:
    """Analyze a Python file via AST and return structured info."""
    result: Dict = {
        "file": filepath,
        "functions": [],
        "classes": [],
        "imports": [],
        "errors": [],
    }
    try:
        with open(filepath, "r", errors="replace") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        result["errors"].append(f"SyntaxError: {e}")
        return result
    except (IOError, OSError) as e:
        result["errors"].append(f"IOError: {e}")
        return result

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = []
            for arg in node.args.args:
                if arg.arg != "self":
                    args.append(arg.arg)
            end_line = getattr(node, "end_lineno", node.lineno + 5)
            result["functions"].append({
                "name": node.name,
                "args": args,
                "line": node.lineno,
                "end_line": end_line,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "decorators": [
                    ast.dump(d) if not isinstance(d, ast.Name) else d.id
                    for d in node.decorator_list
                ],
            })
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            result["classes"].append({
                "name": node.name,
                "methods": methods,
                "line": node.lineno,
                "bases": [
                    ast.dump(b) if not isinstance(b, ast.Name) else b.id
                    for b in node.bases
                ],
            })
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            module = getattr(node, "module", None) or ""
            for alias in node.names:
                result["imports"].append(f"{module}.{alias.name}" if module else alias.name)

    return result


def _read_file_safe(filepath: str, max_chars: int = 12000) -> str:
    """Read file content with size limit."""
    try:
        with open(filepath, "r", errors="replace") as f:
            content = f.read(max_chars)
        if len(content) >= max_chars:
            content += "\n# ... [truncated]"
        return content
    except (IOError, OSError):
        return ""


# ═══════════════════════════════════════════════════════════════
# Tool 1: generate_tests
# ═══════════════════════════════════════════════════════════════

def tool_generate_tests(file_path: str, framework: str = "pytest") -> str:
    """Generate tests for a Python file using AST analysis + LLM."""
    resolved = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(resolved):
        return f"ERROR: File not found: {file_path}"

    # AST analysis
    structure = _ast_analyze(resolved)
    if structure["errors"]:
        return json.dumps({"error": structure["errors"][0], "file": file_path})

    if not structure["functions"] and not structure["classes"]:
        return json.dumps({
            "file": file_path,
            "tests": "",
            "note": "No functions or classes found to test.",
        })

    source = _read_file_safe(resolved)

    # Build prompt
    structure_summary = json.dumps({
        "functions": structure["functions"],
        "classes": structure["classes"],
        "imports": structure["imports"][:20],
    }, indent=2)

    prompt = f"""Analyze this Python file and generate comprehensive {framework} tests.

## File: {file_path}

### Structure (AST):
```json
{structure_summary}
```

### Source code:
```python
{source}
```

## Requirements:
- Framework: {framework}
- Cover all public functions and methods
- Include: happy path, edge cases, error handling
- Use descriptive test names (test_<function>_<scenario>)
- Add brief docstrings to each test
- Mock external dependencies (DB, API calls, file I/O)
- For async functions, use pytest-asyncio

Generate ONLY the test code, no explanations. Start with imports."""

    try:
        from core.api import call_model_with_retry, extract_response, get_tier_config
        tc = get_tier_config()
        model = tc.get("code_gen", "minimax/minimax-m2.5")
        messages = [
            {"role": "system", "content": "You are a senior Python test engineer. Generate clean, thorough tests."},
            {"role": "user", "content": prompt},
        ]
        resp = call_model_with_retry(messages, model, max_retries=2, max_tokens=4096)
        content, _, _ = extract_response(resp)
        test_code = content or ""

        # Strip markdown fences if present
        if test_code.startswith("```"):
            lines = test_code.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            test_code = "\n".join(lines)

        return json.dumps({
            "file": file_path,
            "framework": framework,
            "functions_covered": [f["name"] for f in structure["functions"]],
            "classes_covered": [c["name"] for c in structure["classes"]],
            "tests": test_code,
        }, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"LLM call failed: {type(e).__name__}: {e}",
            "file": file_path,
            "structure": structure_summary,
        })


# ═══════════════════════════════════════════════════════════════
# Tool 2: generate_test_plan
# ═══════════════════════════════════════════════════════════════

def tool_generate_test_plan(description: str) -> str:
    """Generate a structured test plan from a feature description using LLM."""
    if not description or not description.strip():
        return "ERROR: description is required"

    prompt = f"""Given this feature description, generate a comprehensive test plan.

## Feature:
{description}

## Output format (JSON):
{{
  "feature_summary": "one-line summary",
  "test_cases": [
    {{
      "id": "TC-001",
      "category": "unit|integration|edge_case|error_handling",
      "name": "descriptive test name",
      "description": "what this test validates",
      "preconditions": ["list of preconditions"],
      "steps": ["step 1", "step 2"],
      "expected": "expected outcome",
      "priority": "high|medium|low"
    }}
  ],
  "coverage_notes": "what areas need special attention"
}}

Generate 8-15 test cases across all categories. Return ONLY valid JSON."""

    try:
        from core.api import call_model_with_retry, extract_response, get_tier_config
        tc = get_tier_config()
        model = tc.get("fast", "google/gemini-2.5-flash")
        messages = [
            {"role": "system", "content": "You are a QA engineer. Output valid JSON only."},
            {"role": "user", "content": prompt},
        ]
        resp = call_model_with_retry(messages, model, max_retries=2, max_tokens=4096)
        content, _, _ = extract_response(resp)

        # Try to parse as JSON to validate
        if content:
            # Strip markdown fences
            text = content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = lines[1:] if lines[0].startswith("```") else lines
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                text = "\n".join(lines)

            try:
                parsed = json.loads(text)
                return json.dumps(parsed, indent=2)
            except json.JSONDecodeError:
                return json.dumps({
                    "feature_summary": description[:100],
                    "test_cases": [],
                    "raw_response": text[:3000],
                    "warning": "LLM response was not valid JSON",
                })

        return json.dumps({"error": "Empty LLM response", "feature": description[:100]})

    except Exception as e:
        return json.dumps({
            "error": f"LLM call failed: {type(e).__name__}: {e}",
            "feature": description[:100],
        })


# ═══════════════════════════════════════════════════════════════
# Tool 3: coverage_gaps
# ═══════════════════════════════════════════════════════════════

def _scan_source_functions(source_dir: str) -> List[Dict]:
    """Scan source directory for Python functions and classes."""
    items: List[Dict] = []
    if not os.path.isdir(source_dir):
        return items

    for dirpath, dirnames, filenames in os.walk(source_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            filepath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(filepath, source_dir)
            analysis = _ast_analyze(filepath)
            for func in analysis["functions"]:
                if not func["name"].startswith("_"):
                    items.append({
                        "file": rel_path,
                        "type": "function",
                        "name": func["name"],
                        "args": func["args"],
                        "is_async": func["is_async"],
                    })
            for cls in analysis["classes"]:
                items.append({
                    "file": rel_path,
                    "type": "class",
                    "name": cls["name"],
                    "methods": [m for m in cls["methods"] if not m.startswith("_")],
                })
    return items


def _scan_test_coverage(test_dir: str) -> set:
    """Scan test directory and extract function/class names being tested."""
    covered: set = set()
    if not os.path.isdir(test_dir):
        return covered

    for dirpath, dirnames, filenames in os.walk(test_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not (fname.startswith("test_") and fname.endswith(".py")):
                continue
            filepath = os.path.join(dirpath, fname)
            try:
                with open(filepath, "r", errors="replace") as f:
                    source = f.read()
                tree = ast.parse(source, filename=filepath)
            except (SyntaxError, IOError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    name = node.name
                    # Extract the tested function name from test_<name>_<scenario>
                    if name.startswith("test_"):
                        parts = name[5:].split("_")
                        # Try progressive combinations: test_my_func_works -> my_func
                        for i in range(len(parts), 0, -1):
                            candidate = "_".join(parts[:i])
                            covered.add(candidate)
                # Also check for imports from source modules
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        covered.add(alias.name)
    return covered


def tool_coverage_gaps(test_dir: str, source_dir: str) -> str:
    """Find functions in source that lack corresponding tests."""
    resolved_test = os.path.join(_SANDBOX, test_dir) if not os.path.isabs(test_dir) else test_dir
    resolved_src = os.path.join(_SANDBOX, source_dir) if not os.path.isabs(source_dir) else source_dir

    if not os.path.isdir(resolved_src):
        return f"ERROR: Source directory not found: {source_dir}"
    if not os.path.isdir(resolved_test):
        return f"ERROR: Test directory not found: {test_dir}"

    source_items = _scan_source_functions(resolved_src)
    tested_names = _scan_test_coverage(resolved_test)

    uncovered: List[Dict] = []
    covered_count = 0

    for item in source_items:
        if item["type"] == "function":
            if item["name"] in tested_names:
                covered_count += 1
            else:
                uncovered.append(item)
        elif item["type"] == "class":
            untested_methods = [m for m in item["methods"] if m not in tested_names]
            tested_methods = [m for m in item["methods"] if m in tested_names]
            covered_count += len(tested_methods)
            if item["name"] not in tested_names or untested_methods:
                uncovered.append({
                    "file": item["file"],
                    "type": "class",
                    "name": item["name"],
                    "untested_methods": untested_methods,
                    "class_tested": item["name"] in tested_names,
                })

    total = covered_count + len(uncovered)
    coverage_pct = round((covered_count / total) * 100, 1) if total > 0 else 100.0

    return json.dumps({
        "source_dir": source_dir,
        "test_dir": test_dir,
        "total_items": total,
        "covered": covered_count,
        "uncovered_count": len(uncovered),
        "coverage_percent": coverage_pct,
        "uncovered": uncovered[:50],
    }, indent=2)


# ═══════════════════════════════════════════════════════════════
# Registration
# ═══════════════════════════════════════════════════════════════

def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("generate_tests", {
        "name": "generate_tests",
        "description": "Generate pytest/unittest tests for a Python file using AST analysis + LLM. Returns test code and coverage info.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Path to the Python file to generate tests for."},
            "framework": {"type": "string", "description": "Test framework: pytest (default) or unittest."},
        }, "required": ["file_path"]},
    }, lambda a: tool_generate_tests(a["file_path"], a.get("framework", "pytest")),
    category="testing")

    registry.register("generate_test_plan", {
        "name": "generate_test_plan",
        "description": "Generate a structured test plan (unit, integration, edge_case, error_handling) from a feature description using LLM.",
        "parameters": {"type": "object", "properties": {
            "description": {"type": "string", "description": "Feature description to generate test plan for."},
        }, "required": ["description"]},
    }, lambda a: tool_generate_test_plan(a["description"]),
    category="testing")

    registry.register("coverage_gaps", {
        "name": "coverage_gaps",
        "description": "Compare source files against test files to find functions/classes without corresponding tests.",
        "parameters": {"type": "object", "properties": {
            "test_dir": {"type": "string", "description": "Path to the test directory."},
            "source_dir": {"type": "string", "description": "Path to the source directory."},
        }, "required": ["test_dir", "source_dir"]},
    }, lambda a: tool_coverage_gaps(a["test_dir"], a["source_dir"]),
    category="testing")
