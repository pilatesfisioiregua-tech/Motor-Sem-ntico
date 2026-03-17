"""CI/CD tools — trigger_ci, check_ci_status."""

import json
import time
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
            return f"ERROR: gh {' '.join(args)} failed\n{output[:2000]}"
        return output.strip()
    except FileNotFoundError:
        return "ERROR: gh CLI not found. Install: https://cli.github.com/"
    except subprocess.TimeoutExpired:
        return f"ERROR: gh command timed out after {timeout}s"


def tool_trigger_ci(workflow: str = "", branch: str = "") -> str:
    """Trigger a GitHub Actions workflow run."""
    args = ["workflow", "run"]
    if workflow:
        args.append(workflow)
    else:
        # List workflows first
        return _run_gh(["workflow", "list"])
    if branch:
        args.extend(["--ref", branch])
    return _run_gh(args)


def tool_check_ci_status(run_id: str = "", wait: bool = False) -> str:
    """Check GitHub Actions run status. Optionally wait for completion."""
    if not run_id:
        # List recent runs
        output = _run_gh(["run", "list", "--limit", "5", "--json",
                          "databaseId,status,conclusion,name,createdAt"])
        return output

    if wait:
        # Poll until complete (max 5 min)
        for _ in range(20):
            output = _run_gh(["run", "view", run_id, "--json",
                              "status,conclusion,name,createdAt,updatedAt"])
            try:
                data = json.loads(output)
                if data.get("status") == "completed":
                    return json.dumps(data, indent=2)
            except json.JSONDecodeError:
                pass
            time.sleep(15)
        return f"ERROR: CI run {run_id} still running after 5 minutes."

    return _run_gh(["run", "view", run_id, "--json",
                    "status,conclusion,name,createdAt,updatedAt"])


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("trigger_ci", {
        "name": "trigger_ci",
        "description": "Trigger a GitHub Actions workflow or list available workflows.",
        "parameters": {"type": "object", "properties": {
            "workflow": {"type": "string", "description": "Workflow name or filename"},
            "branch": {"type": "string", "description": "Branch to run on"}
        }, "required": []}
    }, lambda a: tool_trigger_ci(a.get("workflow", ""), a.get("branch", "")), category="cicd")

    registry.register("check_ci_status", {
        "name": "check_ci_status",
        "description": "Check GitHub Actions run status or list recent runs.",
        "parameters": {"type": "object", "properties": {
            "run_id": {"type": "string", "description": "Run ID to check"},
            "wait": {"type": "boolean", "description": "Wait for completion (polls every 15s)"}
        }, "required": []}
    }, lambda a: tool_check_ci_status(a.get("run_id", ""), a.get("wait", False)), category="cicd")
