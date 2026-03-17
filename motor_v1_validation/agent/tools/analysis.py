"""Codebase analysis tools — analyze_codebase, dependency_graph, complexity_metrics."""

import os
import re
import ast
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build',
             '.mypy_cache', '.pytest_cache', '.tox'}

LANG_EXTENSIONS = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'TypeScript',
    '.jsx': 'JavaScript', '.rs': 'Rust', '.go': 'Go', '.java': 'Java',
    '.rb': 'Ruby', '.php': 'PHP', '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header',
    '.sql': 'SQL', '.sh': 'Shell', '.yml': 'YAML', '.yaml': 'YAML',
    '.json': 'JSON', '.md': 'Markdown', '.html': 'HTML', '.css': 'CSS',
}


def tool_analyze_codebase(path: str = ".") -> str:
    """Analyze codebase: lines by language, longest files, largest functions."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    if not os.path.isdir(root):
        return f"ERROR: Not a directory: {path}"

    lang_stats = {}  # lang -> {files, lines, blank, comment}
    largest_files = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            lang = LANG_EXTENSIONS.get(ext)
            if not lang:
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    lines = f.readlines()
                total = len(lines)
                blank = sum(1 for l in lines if not l.strip())
                comment = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*')))
                code_lines = total - blank - comment

                if lang not in lang_stats:
                    lang_stats[lang] = {"files": 0, "total_lines": 0, "code_lines": 0,
                                       "blank_lines": 0, "comment_lines": 0}
                lang_stats[lang]["files"] += 1
                lang_stats[lang]["total_lines"] += total
                lang_stats[lang]["code_lines"] += code_lines
                lang_stats[lang]["blank_lines"] += blank
                lang_stats[lang]["comment_lines"] += comment

                rel_path = os.path.relpath(fpath, root)
                largest_files.append((rel_path, total, lang))
            except (PermissionError, IsADirectoryError):
                continue

    largest_files.sort(key=lambda x: x[1], reverse=True)

    total_files = sum(s["files"] for s in lang_stats.values())
    total_lines = sum(s["total_lines"] for s in lang_stats.values())

    return json.dumps({
        "total_files": total_files,
        "total_lines": total_lines,
        "languages": lang_stats,
        "largest_files": [{"file": f, "lines": l, "language": lg}
                         for f, l, lg in largest_files[:15]],
    }, indent=2)


def tool_dependency_graph(path: str = ".") -> str:
    """Generate import/dependency graph between modules."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    if not os.path.isdir(root):
        return f"ERROR: Not a directory: {path}"

    graph = {}  # file -> [imported_modules]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith('.py'):
                continue
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    source = f.read()
                tree = ast.parse(source)
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.append(node.module)
                if imports:
                    graph[rel_path] = sorted(set(imports))
            except (SyntaxError, PermissionError):
                continue

    return json.dumps({
        "modules": len(graph),
        "graph": graph,
    }, indent=2)


def tool_complexity_metrics(file_path: str) -> str:
    """Compute complexity metrics for a Python file using AST."""
    root = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(root):
        return f"ERROR: File not found: {file_path}"

    try:
        with open(root, 'r', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"ERROR: Cannot parse {file_path}: {e}"

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # McCabe complexity: count branches
            complexity = 1  # Base complexity
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                     ast.With, ast.Assert, ast.BoolOp)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1

            end_line = getattr(node, 'end_lineno', node.lineno + 10)
            loc = end_line - node.lineno + 1

            functions.append({
                "name": node.name,
                "line": node.lineno,
                "loc": loc,
                "complexity": complexity,
                "args": len(node.args.args),
            })

    functions.sort(key=lambda f: f["complexity"], reverse=True)

    total_lines = len(source.splitlines())
    avg_complexity = (sum(f["complexity"] for f in functions) / len(functions)
                     if functions else 0)

    return json.dumps({
        "file": file_path,
        "total_lines": total_lines,
        "total_functions": len(functions),
        "avg_complexity": round(avg_complexity, 1),
        "functions": functions[:20],
    }, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("analyze_codebase", {
        "name": "analyze_codebase",
        "description": "Analyze codebase: lines by language, largest files, code stats.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to analyze. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_analyze_codebase(a.get("path", ".")), category="analysis")

    registry.register("dependency_graph", {
        "name": "dependency_graph",
        "description": "Generate import/dependency graph between Python modules.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_dependency_graph(a.get("path", ".")), category="analysis")

    registry.register("complexity_metrics", {
        "name": "complexity_metrics",
        "description": "Compute McCabe complexity, LOC per function for a Python file.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Python file to analyze"}
        }, "required": ["file_path"]}
    }, lambda a: tool_complexity_metrics(a["file_path"]), category="analysis")
