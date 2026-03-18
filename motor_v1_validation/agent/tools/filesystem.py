"""Filesystem tools — read_file, write_file, edit_file, list_dir.

Supports two roots:
  - Sandbox (default): isolated temp workspace for scratch files
  - Project (@project/ prefix): the actual codebase (read + edit allowed, write blocked)
"""

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

MAX_FILE_SIZE = 500_000
MAX_OUTPUT_LEN = 40_000

_SANDBOX = ""
_PROJECT_DIR = ""


def _resolve_path(rel_path: str, allow_project: bool = True) -> str:
    """Resolve path against sandbox or project dir.

    Paths starting with @project/ resolve against _PROJECT_DIR.
    All other paths resolve against _SANDBOX.
    """
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


def tool_read_file(path: str, offset: int = 0, limit: int = 0) -> str:
    """Read file with line numbers. Use offset/limit for large files."""
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    size = os.path.getsize(abs_path)
    if size > MAX_FILE_SIZE:
        return f"ERROR: File too large ({size} bytes, max {MAX_FILE_SIZE})"
    with open(abs_path, 'r', errors='replace') as f:
        all_lines = f.readlines()
    total_lines = len(all_lines)
    if offset > 0 or limit > 0:
        start = max(0, offset)
        end = start + limit if limit > 0 else total_lines
        selected = all_lines[start:end]
        header = f"[Lines {start+1}-{min(end, total_lines)} of {total_lines}]\n"
    else:
        selected = all_lines
        header = f"[{total_lines} lines]\n"
        start = 0
    # Always show line numbers (like cat -n) so models can reference them for insert_at
    numbered = [f"{start + i + 1:4d}| {line}" for i, line in enumerate(selected)]
    content = header + "".join(numbered)
    if len(content) > MAX_OUTPUT_LEN:
        total_len = len(content)
        content = content[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED at {MAX_OUTPUT_LEN} of {total_len} chars. Use offset/limit params to read sections: read_file(path, offset=LINE, limit=LINES)]"
    return content


def tool_write_file(path: str, content: str) -> str:
    if path.startswith("@project"):
        abs_path = _resolve_path(path)
        if os.path.isfile(abs_path):
            return "ERROR: File already exists at @project/. Use edit_file to modify existing project files."
        # Allow creating NEW files in @project/
    if len(content) > MAX_FILE_SIZE:
        return f"ERROR: Content too large ({len(content)} chars, max {MAX_FILE_SIZE})"
    abs_path = _resolve_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w') as f:
        f.write(content)
    return f"OK: Written {len(content)} chars to {path}"


def tool_edit_file(path: str, old_string: str, new_string: str) -> str:
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    with open(abs_path, 'r', errors='replace') as f:
        content = f.read()
    if old_string not in content:
        return f"ERROR: old_string not found in {path}. TIP: usa insert_at(path, línea, contenido) para insertar código en una línea específica — más fiable que edit_file. Usa los números de línea de read_file."
    count = content.count(old_string)
    if count > 1:
        return f"ERROR: old_string appears {count} times in {path}. Provide more context to be unique."
    new_content = content.replace(old_string, new_string, 1)
    with open(abs_path, 'w') as f:
        f.write(new_content)
    return f"OK: Replaced in {path} ({len(old_string)} chars -> {len(new_string)} chars)"


def tool_insert_at(path: str, line: int, content: str) -> str:
    """Insert content at a specific line number. Existing lines shift down."""
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    with open(abs_path, 'r', errors='replace') as f:
        lines = f.readlines()
    total = len(lines)
    if line < 1 or line > total + 1:
        return f"ERROR: Line {line} out of range (file has {total} lines, valid: 1-{total+1})"
    # Ensure content ends with newline
    if content and not content.endswith('\n'):
        content += '\n'
    new_lines = content.splitlines(keepends=True)
    # Insert at position (1-based: line=1 inserts before first line, line=total+1 appends)
    lines[line-1:line-1] = new_lines
    with open(abs_path, 'w') as f:
        f.writelines(lines)
    return f"OK: Inserted {len(new_lines)} lines at line {line} in {path} (file now {len(lines)} lines)"


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


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "",
                   project_dir: str = "") -> None:
    global _SANDBOX, _PROJECT_DIR
    _SANDBOX = sandbox_dir
    _PROJECT_DIR = project_dir

    registry.register("read_file", {
        "name": "read_file",
        "description": "Read file contents. Use @project/ prefix for project files (e.g. @project/src/main.py). No prefix = sandbox workspace. For large files (>40KB), use offset+limit to read sections.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/... for project files, or relative path for sandbox."},
            "offset": {"type": "integer", "description": "Start reading from this line number (0-based). Use for large files."},
            "limit": {"type": "integer", "description": "Max number of lines to read. Use for large files."}
        }, "required": ["path"]}
    }, lambda a: tool_read_file(a["path"], a.get("offset", 0), a.get("limit", 0)), category="filesystem")

    registry.register("write_file", {
        "name": "write_file",
        "description": "Create a NEW file. Use @project/ prefix to create files in the project (e.g. @project/core/nuevo.py). Without prefix = sandbox. Use edit_file to modify existing files.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/... to create project files, or relative path for sandbox scratch files."},
            "content": {"type": "string", "description": "Full file content"}
        }, "required": ["path", "content"]}
    }, lambda a: tool_write_file(a["path"], a["content"]), category="filesystem")

    registry.register("edit_file", {
        "name": "edit_file",
        "description": "Replace exact string in file. Works on both sandbox and @project/ files. Fails if old_string not found or appears >1x.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/... for project files."},
            "old_string": {"type": "string", "description": "Exact string to find"},
            "new_string": {"type": "string", "description": "Replacement string"}
        }, "required": ["path", "old_string", "new_string"]}
    }, lambda a: tool_edit_file(a["path"], a["old_string"], a["new_string"]), category="filesystem")

    registry.register("insert_at", {
        "name": "insert_at",
        "description": "Insert new lines at a specific line number. Use read_file first to see line numbers. Line 1 = before first line, line N+1 = append at end. Existing lines shift down.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/... for project files."},
            "line": {"type": "integer", "description": "Line number where content will be inserted (1-based). Use line numbers from read_file output."},
            "content": {"type": "string", "description": "Code/text to insert. Can be multiple lines."}
        }, "required": ["path", "line", "content"]}
    }, lambda a: tool_insert_at(a["path"], a["line"], a["content"]), category="filesystem")

    registry.register("list_dir", {
        "name": "list_dir",
        "description": "List files/dirs at path. Use @project/ prefix for project directory. One entry per line with d/f prefix.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Use @project/ for project root, @project/src/ for subdirs. Default: '.' (sandbox)"}
        }, "required": []}
    }, lambda a: tool_list_dir(a.get("path", ".")), category="filesystem")
