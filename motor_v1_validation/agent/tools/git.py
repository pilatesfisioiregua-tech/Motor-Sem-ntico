"""Git tools — 8 tools for complete git workflow."""

import os
import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""
COMMAND_TIMEOUT = 30

PROTECTED_BRANCHES = {"main", "master", "production", "prod"}


def _run_git(args: list, cwd: str = None) -> str:
    """Run a git command safely. Returns output string."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True, text=True,
            timeout=COMMAND_TIMEOUT,
            cwd=cwd or _SANDBOX
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" + result.stderr).rstrip()
        if result.returncode != 0:
            return f"ERROR: git {' '.join(args)} failed (rc={result.returncode})\n{output}"
        return output.strip() if output.strip() else "(no output)"
    except subprocess.TimeoutExpired:
        return f"ERROR: git {' '.join(args)} timed out after {COMMAND_TIMEOUT}s"
    except FileNotFoundError:
        return "ERROR: git not found. Install git first."


def tool_git_status() -> str:
    """Show working tree status."""
    return _run_git(["status", "--short", "--branch"])


def tool_git_add(files: str) -> str:
    """Stage files for commit. No 'git add .' allowed — specify files."""
    if files.strip() in (".", "*", "-A", "--all"):
        return "ERROR: 'git add .' is blocked for safety. Specify files explicitly."
    file_list = [f.strip() for f in files.split(",") if f.strip()]
    if not file_list:
        return "ERROR: No files specified."
    return _run_git(["add"] + file_list)


def tool_git_commit(message: str) -> str:
    """Create a commit with the given message."""
    if not message.strip():
        return "ERROR: Empty commit message."
    return _run_git(["commit", "-m", message])


def tool_git_diff(ref: str = "") -> str:
    """Show diff. Optional ref for comparing branches/commits."""
    args = ["diff"]
    if ref:
        args.append(ref)
    output = _run_git(args)
    if len(output) > 15000:
        output = output[:15000] + "\n... [DIFF TRUNCATED]"
    return output


def tool_git_log(n: int = 10) -> str:
    """Show recent commits. Default: last 10."""
    n = min(max(1, n), 50)
    return _run_git(["log", f"--oneline", f"-{n}", "--decorate"])


def tool_git_branch(name: str = "", action: str = "list") -> str:
    """Manage branches. Actions: list, create, switch, delete."""
    if action == "list":
        return _run_git(["branch", "-a", "--no-color"])
    elif action == "create":
        if not name:
            return "ERROR: Branch name required."
        return _run_git(["checkout", "-b", name])
    elif action == "switch":
        if not name:
            return "ERROR: Branch name required."
        return _run_git(["checkout", name])
    elif action == "delete":
        if not name:
            return "ERROR: Branch name required."
        if name in PROTECTED_BRANCHES:
            return f"ERROR: Cannot delete protected branch '{name}'."
        return _run_git(["branch", "-d", name])
    return f"ERROR: Unknown action '{action}'. Use: list, create, switch, delete."


def tool_git_push(remote: str = "origin", branch: str = "", force: bool = False) -> str:
    """Push to remote. Force push is blocked."""
    if force:
        return "ERROR: Force push is blocked for safety."
    args = ["push", remote]
    if branch:
        args.extend(["-u", remote, branch])
    return _run_git(args)


def tool_create_pr(title: str, body: str = "", base: str = "main",
                   head: str = "", draft: bool = False) -> str:
    """Create a GitHub Pull Request using gh CLI."""
    try:
        subprocess.run(["which", "gh"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "ERROR: gh CLI not found. Install: https://cli.github.com/"

    args = ["gh", "pr", "create", "--title", title, "--base", base]
    if body:
        args.extend(["--body", body])
    if head:
        args.extend(["--head", head])
    if draft:
        args.append("--draft")

    try:
        result = subprocess.run(
            args, capture_output=True, text=True,
            timeout=30, cwd=_SANDBOX
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"ERROR: PR creation failed\n{output}"
        return output.strip()
    except subprocess.TimeoutExpired:
        return "ERROR: PR creation timed out."


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("git_status", {
        "name": "git_status",
        "description": "Show git working tree status (staged, modified, untracked files).",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }, lambda a: tool_git_status(), category="git")

    registry.register("git_add", {
        "name": "git_add",
        "description": "Stage files for commit. Specify files explicitly (no 'git add .').",
        "parameters": {"type": "object", "properties": {
            "files": {"type": "string", "description": "Comma-separated file paths to stage"}
        }, "required": ["files"]}
    }, lambda a: tool_git_add(a["files"]), category="git")

    registry.register("git_commit", {
        "name": "git_commit",
        "description": "Create a git commit with the given message.",
        "parameters": {"type": "object", "properties": {
            "message": {"type": "string", "description": "Commit message"}
        }, "required": ["message"]}
    }, lambda a: tool_git_commit(a["message"]), category="git")

    registry.register("git_diff", {
        "name": "git_diff",
        "description": "Show git diff. Optional ref for comparing branches/commits.",
        "parameters": {"type": "object", "properties": {
            "ref": {"type": "string", "description": "Reference to diff against (branch, commit, etc.)"}
        }, "required": []}
    }, lambda a: tool_git_diff(a.get("ref", "")), category="git")

    registry.register("git_log", {
        "name": "git_log",
        "description": "Show recent git commits. Default: last 10.",
        "parameters": {"type": "object", "properties": {
            "n": {"type": "integer", "description": "Number of commits to show. Default: 10"}
        }, "required": []}
    }, lambda a: tool_git_log(a.get("n", 10)), category="git")

    registry.register("git_branch", {
        "name": "git_branch",
        "description": "Manage git branches: list, create, switch, delete.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Branch name (for create/switch/delete)"},
            "action": {"type": "string", "enum": ["list", "create", "switch", "delete"],
                      "description": "Action to perform. Default: list"}
        }, "required": []}
    }, lambda a: tool_git_branch(a.get("name", ""), a.get("action", "list")), category="git")

    registry.register("git_push", {
        "name": "git_push",
        "description": "Push commits to remote. Force push is blocked.",
        "parameters": {"type": "object", "properties": {
            "remote": {"type": "string", "description": "Remote name. Default: origin"},
            "branch": {"type": "string", "description": "Branch to push. Default: current"}
        }, "required": []}
    }, lambda a: tool_git_push(a.get("remote", "origin"), a.get("branch", "")), category="git")

    registry.register("create_pr", {
        "name": "create_pr",
        "description": "Create a GitHub Pull Request using gh CLI.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "PR title"},
            "body": {"type": "string", "description": "PR description"},
            "base": {"type": "string", "description": "Base branch. Default: main"},
            "draft": {"type": "boolean", "description": "Create as draft PR"}
        }, "required": ["title"]}
    }, lambda a: tool_create_pr(a["title"], a.get("body", ""), a.get("base", "main"),
                                 draft=a.get("draft", False)),
    category="git")
