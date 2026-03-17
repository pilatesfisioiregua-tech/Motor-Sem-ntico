"""Environment management tools — manage_env, check_versions, install_deps."""

import os
import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def tool_manage_env(action: str, path: str = ".venv") -> str:
    """Manage virtual environments: create, activate info, list packages."""
    if action == "create":
        try:
            result = subprocess.run(
                ["python3", "-m", "venv", path],
                capture_output=True, text=True, timeout=30,
                cwd=_SANDBOX
            )
            if result.returncode != 0:
                return f"ERROR: venv creation failed: {result.stderr[:500]}"
            return f"OK: Virtual environment created at {path}\nActivate: source {path}/bin/activate"
        except subprocess.TimeoutExpired:
            return "ERROR: venv creation timed out."

    elif action == "info":
        try:
            result = subprocess.run(
                ["python3", "-c", "import sys; print(sys.prefix); print(sys.executable); print(sys.version)"],
                capture_output=True, text=True, timeout=10,
                cwd=_SANDBOX
            )
            return result.stdout.strip()
        except Exception as e:
            return f"ERROR: {e}"

    elif action == "list":
        try:
            result = subprocess.run(
                ["pip3", "list", "--format", "json"],
                capture_output=True, text=True, timeout=15,
                cwd=_SANDBOX
            )
            return result.stdout[:5000]
        except Exception as e:
            return f"ERROR: {e}"

    return f"ERROR: Unknown action '{action}'. Use: create, info, list."


def tool_check_versions(path: str = ".") -> str:
    """Check installed vs required package versions."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    req_file = os.path.join(root, "requirements.txt")

    if not os.path.isfile(req_file):
        return "ERROR: No requirements.txt found."

    with open(req_file) as f:
        requirements = [l.strip() for l in f if l.strip() and not l.startswith('#')]

    # Get installed packages
    try:
        result = subprocess.run(
            ["pip3", "list", "--format", "json"],
            capture_output=True, text=True, timeout=15
        )
        installed = {}
        if result.stdout:
            for pkg in json.loads(result.stdout):
                installed[pkg["name"].lower()] = pkg["version"]
    except Exception:
        installed = {}

    checks = []
    for req in requirements[:30]:
        # Parse requirement: name==version, name>=version, name
        import re
        match = re.match(r'([a-zA-Z0-9_\-]+)\s*([><=!]+\s*[\d.]+)?', req)
        if match:
            pkg_name = match.group(1).lower()
            required_ver = match.group(2) or "any"
            installed_ver = installed.get(pkg_name, "NOT INSTALLED")
            checks.append({
                "package": pkg_name,
                "required": required_ver.strip(),
                "installed": installed_ver,
                "ok": installed_ver != "NOT INSTALLED",
            })

    return json.dumps({
        "total": len(checks),
        "missing": sum(1 for c in checks if not c["ok"]),
        "packages": checks,
    }, indent=2)


def tool_install_deps(deps: str = "", requirements_file: str = "") -> str:
    """Install Python packages via pip."""
    if requirements_file:
        cmd = f"pip3 install -r {requirements_file}"
    elif deps:
        cmd = f"pip3 install {deps}"
    else:
        return "ERROR: Specify deps (space-separated) or requirements_file."

    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=120, cwd=_SANDBOX
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"ERROR: Installation failed:\n{output[:3000]}"
        return f"OK: Installed successfully.\n{output[-1000:]}"
    except subprocess.TimeoutExpired:
        return "ERROR: Installation timed out after 120s."


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("manage_env", {
        "name": "manage_env",
        "description": "Manage virtual environments: create, info, list packages.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["create", "info", "list"]},
            "path": {"type": "string", "description": "Venv path for create. Default: .venv"}
        }, "required": ["action"]}
    }, lambda a: tool_manage_env(a["action"], a.get("path", ".venv")), category="environment")

    registry.register("check_versions", {
        "name": "check_versions",
        "description": "Check installed vs required package versions from requirements.txt.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Project path. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_check_versions(a.get("path", ".")), category="environment")

    registry.register("install_deps", {
        "name": "install_deps",
        "description": "Install Python packages via pip.",
        "parameters": {"type": "object", "properties": {
            "deps": {"type": "string", "description": "Space-separated package names"},
            "requirements_file": {"type": "string", "description": "Path to requirements.txt"}
        }, "required": []}
    }, lambda a: tool_install_deps(a.get("deps", ""), a.get("requirements_file", "")),
    category="environment")
