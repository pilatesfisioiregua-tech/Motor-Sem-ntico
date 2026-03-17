"""Issue tracking tools — create_issue, update_issue, list_issues."""

import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry


def _run_gh(args: list, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"ERROR: gh {' '.join(args[:3])} failed\n{output[:2000]}"
        return output.strip()
    except FileNotFoundError:
        return "ERROR: gh CLI not found."
    except subprocess.TimeoutExpired:
        return f"ERROR: Timed out after {timeout}s"


def tool_create_issue(title: str, body: str = "", labels: str = "") -> str:
    """Create a GitHub Issue."""
    args = ["issue", "create", "--title", title]
    if body:
        args.extend(["--body", body])
    if labels:
        args.extend(["--label", labels])
    return _run_gh(args)


def tool_update_issue(issue_id: str, comment: str = "", state: str = "") -> str:
    """Add comment to or close/reopen a GitHub Issue."""
    results = []
    if comment:
        results.append(_run_gh(["issue", "comment", issue_id, "--body", comment]))
    if state in ("closed", "open"):
        action = "close" if state == "closed" else "reopen"
        results.append(_run_gh(["issue", action, issue_id]))
    if not results:
        return "ERROR: Provide either comment or state to update."
    return "\n".join(results)


def tool_list_issues(state: str = "open", labels: str = "",
                     limit: int = 10) -> str:
    """List GitHub Issues."""
    args = ["issue", "list", "--state", state, "--limit", str(min(limit, 50)),
            "--json", "number,title,state,labels,createdAt,author"]
    if labels:
        args.extend(["--label", labels])
    return _run_gh(args)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("create_issue", {
        "name": "create_issue",
        "description": "Create a GitHub Issue.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Issue title"},
            "body": {"type": "string", "description": "Issue description"},
            "labels": {"type": "string", "description": "Comma-separated labels"}
        }, "required": ["title"]}
    }, lambda a: tool_create_issue(a["title"], a.get("body", ""), a.get("labels", "")),
    category="issues")

    registry.register("update_issue", {
        "name": "update_issue",
        "description": "Add comment to or close/reopen a GitHub Issue.",
        "parameters": {"type": "object", "properties": {
            "issue_id": {"type": "string", "description": "Issue number"},
            "comment": {"type": "string", "description": "Comment to add"},
            "state": {"type": "string", "enum": ["open", "closed"], "description": "New state"}
        }, "required": ["issue_id"]}
    }, lambda a: tool_update_issue(a["issue_id"], a.get("comment", ""), a.get("state", "")),
    category="issues")

    registry.register("list_issues", {
        "name": "list_issues",
        "description": "List GitHub Issues.",
        "parameters": {"type": "object", "properties": {
            "state": {"type": "string", "enum": ["open", "closed", "all"]},
            "labels": {"type": "string", "description": "Filter by labels"},
            "limit": {"type": "integer", "description": "Max results. Default: 10"}
        }, "required": []}
    }, lambda a: tool_list_issues(a.get("state", "open"), a.get("labels", ""), a.get("limit", 10)),
    category="issues")
