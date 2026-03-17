"""Search tools — glob_files, grep_content, search_files.

Supports @project/ prefix for searching the actual codebase.
"""

import os
import re
import fnmatch
import glob as glob_mod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

MAX_OUTPUT_LEN = 20_000
_SANDBOX = ""
_PROJECT_DIR = ""


def _resolve_path(rel_path: str) -> str:
    """Resolve path against sandbox or project dir (@project/ prefix)."""
    if rel_path.startswith("@project/") or rel_path == "@project":
        if not _PROJECT_DIR:
            raise ValueError("No project directory configured")
        clean = rel_path[len("@project/"):] if rel_path.startswith("@project/") else ""
        clean = clean or "."
        abs_path = os.path.abspath(os.path.join(_PROJECT_DIR, clean))
        if not abs_path.startswith(os.path.abspath(_PROJECT_DIR)):
            raise ValueError(f"Path escapes project: {rel_path}")
        return abs_path

    abs_path = os.path.abspath(os.path.join(_SANDBOX, rel_path))
    if not abs_path.startswith(os.path.abspath(_SANDBOX)):
        raise ValueError(f"Path escapes sandbox: {rel_path}")
    return abs_path


def tool_glob_files(pattern: str, path: str = ".") -> str:
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
    skip_ext = {'.pyc', '.pyo', '.so', '.o', '.class', '.jar', '.png', '.jpg', '.gif', '.zip'}
    for root_dir, _, files in os.walk(abs_root):
        for fname in files:
            if any(fname.endswith(ext) for ext in skip_ext):
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


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "",
                   project_dir: str = "") -> None:
    global _SANDBOX, _PROJECT_DIR
    _SANDBOX = sandbox_dir
    _PROJECT_DIR = project_dir

    registry.register("glob_files", {
        "name": "glob_files",
        "description": "Find files matching glob pattern. Use @project/ prefix to search project files (e.g. path='@project/'). Default searches sandbox.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Glob pattern to match (e.g. '**/*.py')"},
            "path": {"type": "string", "description": "Root directory. Use @project/ for project. Default: '.' (sandbox)"}
        }, "required": ["pattern"]}
    }, lambda a: tool_glob_files(a["pattern"], a.get("path", ".")), category="search")

    registry.register("grep_content", {
        "name": "grep_content",
        "description": "Search file contents for regex pattern. Use @project/ prefix to search project files. Returns file:line: prefix.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Regex pattern"},
            "path": {"type": "string", "description": "Root directory. Use @project/ for project. Default: '.' (sandbox)"},
            "max_results": {"type": "integer", "description": "Max results. Default: 30"}
        }, "required": ["pattern"]}
    }, lambda a: tool_grep_content(a["pattern"], a.get("path", "."), a.get("max_results", 30)),
    category="search")

    registry.register("search_files", {
        "name": "search_files",
        "description": "Search files by glob pattern or content regex. Use @project/ for project files.",
        "parameters": {"type": "object", "properties": {
            "pattern": {"type": "string", "description": "Glob for names or regex for content"},
            "path": {"type": "string", "description": "Root dir. Use @project/ for project. Default: '.' (sandbox)"},
            "content_search": {"type": "boolean", "description": "If true, search contents"}
        }, "required": ["pattern"]}
    }, lambda a: tool_search_files(a["pattern"], a.get("path", "."), a.get("content_search", False)),
    category="search")
