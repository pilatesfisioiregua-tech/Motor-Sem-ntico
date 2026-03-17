"""Security tools — scan_secrets, scan_vulnerabilities, audit_deps."""

import os
import re
import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""

# Patterns for secret detection
SECRET_PATTERNS = [
    (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([A-Za-z0-9_\-]{20,})', "API Key"),
    (r'(?i)(secret|token|password|passwd|pwd)\s*[=:]\s*["\']?([^\s"\']{8,})', "Secret/Token"),
    (r'sk-[A-Za-z0-9]{32,}', "OpenAI API Key"),
    (r'sk-ant-[A-Za-z0-9\-]{40,}', "Anthropic API Key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub PAT"),
    (r'gsk_[A-Za-z0-9]{40,}', "Groq API Key"),
    (r'eyJ[A-Za-z0-9_\-]{50,}\.eyJ[A-Za-z0-9_\-]+', "JWT Token"),
    (r'-----BEGIN (?:RSA )?PRIVATE KEY-----', "Private Key"),
    (r'AKIA[0-9A-Z]{16}', "AWS Access Key"),
    (r'(?i)postgres(?:ql)?://[^\s"\']+:[^\s"\']+@', "Database URL with credentials"),
]

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build'}
SKIP_EXT = {'.pyc', '.pyo', '.so', '.o', '.jpg', '.png', '.gif', '.zip', '.gz', '.tar'}


def tool_scan_secrets(path: str = ".") -> str:
    """Scan code for hardcoded secrets, API keys, passwords, tokens."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    if not os.path.isdir(root):
        return f"ERROR: Not a directory: {path}"

    findings = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in SKIP_EXT):
                continue
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, 'r', errors='replace') as f:
                    content = f.read(50000)  # First 50KB
                for pattern, secret_type in SECRET_PATTERNS:
                    for match in re.finditer(pattern, content):
                        line_num = content[:match.start()].count('\n') + 1
                        rel_path = os.path.relpath(fpath, root)
                        # Mask the actual secret
                        secret_preview = match.group()[:8] + "..." + match.group()[-4:]
                        findings.append({
                            "file": rel_path,
                            "line": line_num,
                            "type": secret_type,
                            "preview": secret_preview,
                        })
                        if len(findings) >= 50:
                            break
            except (PermissionError, IsADirectoryError):
                continue
        if len(findings) >= 50:
            break

    return json.dumps({
        "total_findings": len(findings),
        "findings": findings,
        "status": "CLEAN" if not findings else "SECRETS_FOUND",
    }, indent=2)


def tool_scan_vulnerabilities(path: str = ".") -> str:
    """Run vulnerability scanners (bandit for Python, npm audit for JS)."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    results = {"scanners_run": [], "issues": []}

    # Python: try bandit
    if os.path.isfile(os.path.join(root, "requirements.txt")) or \
       any(f.endswith('.py') for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))):
        try:
            r = subprocess.run(
                f"python3 -m bandit -r {root} -f json -q",
                shell=True, capture_output=True, text=True, timeout=60
            )
            results["scanners_run"].append("bandit")
            if r.stdout:
                try:
                    bandit = json.loads(r.stdout)
                    for issue in bandit.get("results", [])[:20]:
                        results["issues"].append({
                            "scanner": "bandit",
                            "severity": issue.get("issue_severity", ""),
                            "confidence": issue.get("issue_confidence", ""),
                            "file": issue.get("filename", ""),
                            "line": issue.get("line_number", 0),
                            "message": issue.get("issue_text", ""),
                        })
                except json.JSONDecodeError:
                    results["issues"].append({"scanner": "bandit", "raw": r.stdout[:1000]})
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results["scanners_run"].append("bandit (not installed)")

    # JS: try npm audit
    if os.path.isfile(os.path.join(root, "package-lock.json")):
        try:
            r = subprocess.run(
                "npm audit --json",
                shell=True, capture_output=True, text=True, timeout=30, cwd=root
            )
            results["scanners_run"].append("npm-audit")
            if r.stdout:
                try:
                    audit = json.loads(r.stdout)
                    for vuln_name, vuln in audit.get("vulnerabilities", {}).items():
                        results["issues"].append({
                            "scanner": "npm-audit",
                            "severity": vuln.get("severity", ""),
                            "package": vuln_name,
                            "message": vuln.get("title", ""),
                        })
                except json.JSONDecodeError:
                    pass
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return json.dumps(results, indent=2)


def tool_audit_deps(path: str = ".") -> str:
    """Audit dependencies for known vulnerabilities."""
    root = os.path.join(_SANDBOX, path) if not os.path.isabs(path) else path
    results = {"auditors_run": [], "vulnerabilities": []}

    # Python: pip-audit or safety
    req_file = os.path.join(root, "requirements.txt")
    if os.path.isfile(req_file):
        try:
            r = subprocess.run(
                f"python3 -m pip_audit -r {req_file} --format json",
                shell=True, capture_output=True, text=True, timeout=60
            )
            results["auditors_run"].append("pip-audit")
            if r.stdout:
                try:
                    results["vulnerabilities"] = json.loads(r.stdout)[:20]
                except json.JSONDecodeError:
                    results["vulnerabilities"].append({"raw": r.stdout[:1000]})
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Fallback: just list packages with versions
            with open(req_file) as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            results["auditors_run"].append("requirements-list")
            results["dependencies"] = deps[:50]

    return json.dumps(results, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("scan_secrets", {
        "name": "scan_secrets",
        "description": "Scan code for hardcoded secrets, API keys, passwords, tokens.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to scan. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_scan_secrets(a.get("path", ".")), category="security")

    registry.register("scan_vulnerabilities", {
        "name": "scan_vulnerabilities",
        "description": "Run vulnerability scanners (bandit/npm audit) on code.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path to scan. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_scan_vulnerabilities(a.get("path", ".")), category="security")

    registry.register("audit_deps", {
        "name": "audit_deps",
        "description": "Audit dependencies for known vulnerabilities.",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Path. Default: '.'"}
        }, "required": []}
    }, lambda a: tool_audit_deps(a.get("path", ".")), category="security")
