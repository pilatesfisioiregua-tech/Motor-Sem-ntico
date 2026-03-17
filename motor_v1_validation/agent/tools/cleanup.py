"""Cleanup tools — detect_dead_code, detect_duplicates."""

import os
import re
import ast
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}


def tool_detect_dead_code(path: str = ".") -> str:
    """Detect unused functions, imports, variables in Python code."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    if not os.path.isdir(root):
        return f"ERROR: Not a directory: {path}"

    # Collect all definitions and usages across all Python files
    all_definitions = {}  # name -> {file, line, type}
    all_usages = set()    # names that are used/referenced

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

                for node in ast.walk(tree):
                    # Track definitions
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        all_definitions[node.name] = {
                            "file": rel_path, "line": node.lineno, "type": "function"
                        }
                    elif isinstance(node, ast.ClassDef):
                        all_definitions[node.name] = {
                            "file": rel_path, "line": node.lineno, "type": "class"
                        }
                    # Track usages (names referenced)
                    elif isinstance(node, ast.Name):
                        all_usages.add(node.id)
                    elif isinstance(node, ast.Attribute):
                        all_usages.add(node.attr)

                # Track unused imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            name = alias.asname or alias.name.split('.')[-1]
                            if name not in all_usages and name != '*':
                                all_definitions[f"import:{name}"] = {
                                    "file": rel_path, "line": node.lineno, "type": "import",
                                    "name": alias.name,
                                }
                    elif isinstance(node, ast.ImportFrom):
                        for alias in node.names:
                            name = alias.asname or alias.name
                            if name not in all_usages and name != '*':
                                all_definitions[f"import:{name}"] = {
                                    "file": rel_path, "line": node.lineno, "type": "import",
                                    "name": f"from {node.module} import {alias.name}",
                                }
            except (SyntaxError, PermissionError):
                continue

    # Find unused definitions
    unused = []
    for name, info in all_definitions.items():
        clean_name = name.replace("import:", "")
        # Skip private/dunder/test functions
        if clean_name.startswith('_') or clean_name.startswith('test_'):
            continue
        # Skip if it's an import that's unused
        if info["type"] == "import":
            unused.append({
                "name": info.get("name", clean_name),
                "file": info["file"],
                "line": info["line"],
                "type": "unused_import",
            })
        elif clean_name not in all_usages:
            unused.append({
                "name": clean_name,
                "file": info["file"],
                "line": info["line"],
                "type": f"unused_{info['type']}",
            })

    return json.dumps({
        "total_unused": len(unused),
        "unused": unused[:30],
    }, indent=2)


def tool_detect_duplicates(path: str = ".", min_lines: int = 5) -> str:
    """Detect duplicate code blocks (>5 lines identical)."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    if not os.path.isdir(root):
        return f"ERROR: Not a directory: {path}"

    # Collect normalized line blocks from all files
    blocks = {}  # hash -> [{file, start_line}]

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if not fname.endswith(('.py', '.js', '.ts', '.java', '.go')):
                continue
            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    lines = [l.strip() for l in f.readlines()]

                # Sliding window of min_lines
                for i in range(len(lines) - min_lines + 1):
                    block = lines[i:i + min_lines]
                    # Skip empty/comment-only blocks
                    if all(not l or l.startswith(('#', '//', '/*', '*')) for l in block):
                        continue
                    block_key = "\n".join(block)
                    import hashlib
                    h = hashlib.md5(block_key.encode()).hexdigest()
                    if h not in blocks:
                        blocks[h] = []
                    blocks[h].append({"file": rel_path, "start_line": i + 1})
            except (PermissionError, IsADirectoryError):
                continue

    # Find duplicates (blocks appearing in 2+ locations)
    duplicates = []
    for h, locations in blocks.items():
        if len(locations) >= 2:
            # Deduplicate overlapping blocks in same file
            unique_locs = []
            seen = set()
            for loc in locations:
                key = f"{loc['file']}:{loc['start_line']}"
                if key not in seen:
                    seen.add(key)
                    unique_locs.append(loc)
            if len(unique_locs) >= 2:
                duplicates.append({
                    "locations": unique_locs[:5],
                    "count": len(unique_locs),
                })

    duplicates.sort(key=lambda d: d["count"], reverse=True)

    return json.dumps({
        "total_duplicate_blocks": len(duplicates),
        "duplicates": duplicates[:20],
    }, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("detect_dead_code", {
        "name": "detect_dead_code",
        "description": "Detect unused functions, imports, variables in Python code.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to scan. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_detect_dead_code(a.get("path", ".")), category="cleanup")

    registry.register("detect_duplicates", {
        "name": "detect_duplicates",
        "description": "Detect duplicate code blocks (>5 lines identical).",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to scan. Default: '.'"},
            "min_lines": {"type": "integer", "description": "Min lines for duplicate. Default: 5"}
        }, "required": []}
    }, lambda a: tool_detect_duplicates(a.get("path", "."), a.get("min_lines", 5)),
    category="cleanup")
