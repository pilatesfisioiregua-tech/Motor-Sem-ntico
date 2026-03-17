"""Documentation tools — generate_readme, generate_api_docs."""

import os
import re
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def _scan_project(path: str) -> dict:
    """Scan project for documentation-relevant info."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    info = {"name": os.path.basename(os.path.abspath(root)), "files": [], "endpoints": [],
            "dependencies": [], "scripts": {}}

    # Check for package files
    for pkg_file in ["package.json", "requirements.txt", "Cargo.toml", "go.mod"]:
        fpath = os.path.join(root, pkg_file)
        if os.path.isfile(fpath):
            with open(fpath, 'r', errors='replace') as f:
                content = f.read()
            if pkg_file == "package.json":
                try:
                    pkg = json.loads(content)
                    info["name"] = pkg.get("name", info["name"])
                    info["dependencies"] = list(pkg.get("dependencies", {}).keys())[:20]
                    info["scripts"] = pkg.get("scripts", {})
                except json.JSONDecodeError:
                    pass
            elif pkg_file == "requirements.txt":
                info["dependencies"] = [l.strip().split("==")[0] for l in content.splitlines()
                                       if l.strip() and not l.startswith('#')][:20]

    # Scan for API endpoints
    skip = {'.git', 'node_modules', '__pycache__', '.venv', 'dist'}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fname in filenames:
            if not fname.endswith(('.py', '.js', '.ts')):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    content = f.read(20000)
                rel = os.path.relpath(fpath, root)
                info["files"].append(rel)
                # FastAPI/Flask/Express endpoints
                for match in re.finditer(
                    r'@(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
                    content, re.IGNORECASE
                ):
                    info["endpoints"].append({"method": match.group(1).upper(),
                                             "path": match.group(2), "file": rel})
            except (PermissionError, IsADirectoryError):
                continue

    return info


def tool_generate_readme(path: str = ".") -> str:
    """Generate a README.md template based on project structure and code."""
    info = _scan_project(path)

    sections = [f"# {info['name']}\n"]

    # Description
    sections.append("## Description\n\nTODO: Add project description.\n")

    # Installation
    if info["dependencies"]:
        sections.append("## Installation\n")
        if any(d in info["files"] for d in ["requirements.txt"]):
            sections.append("```bash\npip install -r requirements.txt\n```\n")
        elif any(d in info["files"] for d in ["package.json"]):
            sections.append("```bash\nnpm install\n```\n")

    # Usage / Scripts
    if info["scripts"]:
        sections.append("## Usage\n")
        for name, cmd in list(info["scripts"].items())[:10]:
            sections.append(f"- `npm run {name}` — `{cmd}`")
        sections.append("")

    # API Endpoints
    if info["endpoints"]:
        sections.append("## API Endpoints\n")
        sections.append("| Method | Path | File |")
        sections.append("|--------|------|------|")
        for ep in info["endpoints"][:20]:
            sections.append(f"| {ep['method']} | `{ep['path']}` | {ep['file']} |")
        sections.append("")

    # Dependencies
    if info["dependencies"]:
        sections.append("## Dependencies\n")
        sections.append(", ".join(f"`{d}`" for d in info["dependencies"][:20]))
        sections.append("")

    # Project structure
    sections.append("## Project Structure\n")
    sections.append("```")
    for f in sorted(info["files"])[:30]:
        sections.append(f)
    sections.append("```\n")

    return "\n".join(sections)


def tool_generate_api_docs(path: str = ".") -> str:
    """Generate API documentation from code (endpoints, params, responses)."""
    info = _scan_project(path)
    if not info["endpoints"]:
        return "No API endpoints found in the codebase."

    docs = ["# API Documentation\n"]
    for ep in info["endpoints"]:
        docs.append(f"## {ep['method']} `{ep['path']}`\n")
        docs.append(f"**File:** `{ep['file']}`\n")
        docs.append("**Parameters:** TODO\n")
        docs.append("**Response:** TODO\n")
        docs.append("---\n")

    return "\n".join(docs)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("generate_readme", {
        "name": "generate_readme",
        "description": "Generate a README.md based on project structure, endpoints, dependencies.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Project path. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_generate_readme(a.get("path", ".")), category="docs")

    registry.register("generate_api_docs", {
        "name": "generate_api_docs",
        "description": "Generate API documentation from code endpoints.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Project path. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_generate_api_docs(a.get("path", ".")), category="docs")
