"""Meta tools — plan, finish, ask_user, spawn_agents, create_tool."""

import os
import sys
import json
import ast
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from . import ToolRegistry

# Plan storage (in-memory per session)
_PLAN_CONTENT = ""
_AUTONOMOUS = True
_SUBMITTED_BRIEFING = None


def set_autonomous(value: bool) -> None:
    global _AUTONOMOUS
    _AUTONOMOUS = value


def tool_plan(action: str, content: str = "") -> str:
    global _PLAN_CONTENT
    if action == "read":
        return _PLAN_CONTENT if _PLAN_CONTENT else "(no plan yet)"
    elif action == "write":
        _PLAN_CONTENT = content
        return f"OK: Plan updated ({len(content)} chars)"
    return f"ERROR: Unknown action '{action}'. Use 'read' or 'write'."


def tool_finish(result: str) -> str:
    return result


def tool_ask_user(question: str) -> str:
    """Ask the user a question. Only works in interactive mode."""
    if _AUTONOMOUS:
        return "ERROR: ask_user disabled in autonomous mode. Make a decision and proceed."
    try:
        print(f"\n[AGENT QUESTION] {question}")
        answer = input("Your answer: ").strip()
        return answer if answer else "(no response)"
    except (EOFError, KeyboardInterrupt):
        return "(user interrupted)"


# ============================================================
# SELF-EXTENDING: create_tool
# ============================================================

# Dangerous imports/calls that custom tools cannot use
FORBIDDEN_IMPORTS = {
    'os.system', 'subprocess.call', 'subprocess.Popen', 'subprocess.run',
    'eval', 'exec', 'compile', '__import__', 'importlib',
    'shutil.rmtree', 'os.remove', 'os.unlink',
}

ALLOWED_MODULES = {
    'json', 're', 'math', 'datetime', 'collections', 'itertools',
    'functools', 'string', 'textwrap', 'csv', 'io', 'hashlib',
    'base64', 'urllib.parse', 'pathlib', 'socket', 'struct',
}


def _validate_tool_code(code: str) -> Optional[str]:
    """Validate tool code using AST. Returns error message or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Syntax error: {e}"

    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name not in ALLOWED_MODULES:
                    return f"Forbidden import: {alias.name}. Allowed: {ALLOWED_MODULES}"
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split('.')[0] not in ALLOWED_MODULES:
                return f"Forbidden import: {node.module}. Allowed: {ALLOWED_MODULES}"
        # Check dangerous calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ('eval', 'exec', 'compile', '__import__'):
                    return f"Forbidden call: {node.func.id}"
            elif isinstance(node.func, ast.Attribute):
                call_name = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
                if call_name in FORBIDDEN_IMPORTS:
                    return f"Forbidden call: {call_name}"
    return None


def tool_create_tool(name: str, description: str, code: str,
                     parameters: dict, test_code: str = "") -> str:
    """Create a new tool dynamically. Validates code, runs test, registers if passing."""
    # Validate name
    if not name.isidentifier():
        return f"ERROR: Invalid tool name: {name}"

    # Validate code safety
    error = _validate_tool_code(code)
    if error:
        return f"ERROR: Code validation failed: {error}"

    # Check function exists in code
    handler_name = f"tool_{name}"
    if handler_name not in code:
        return f"ERROR: Code must define function '{handler_name}'"

    # Execute code in sandbox namespace
    namespace = {}
    try:
        exec(code, namespace)  # noqa: S102
    except Exception as e:
        return f"ERROR: Code execution failed: {e}"

    if handler_name not in namespace:
        return f"ERROR: Function '{handler_name}' not found after execution"

    # Run test if provided
    if test_code:
        test_ns = dict(namespace)
        try:
            exec(test_code, test_ns)  # noqa: S102
        except AssertionError as e:
            return f"ERROR: Test failed: {e}"
        except Exception as e:
            return f"ERROR: Test error: {type(e).__name__}: {e}"

    # Save to tools/custom/
    custom_dir = os.path.join(os.path.dirname(__file__), "custom")
    os.makedirs(custom_dir, exist_ok=True)
    tool_def = {
        "name": name,
        "description": description,
        "code": code,
        "schema": {
            "name": name,
            "description": description,
            "parameters": parameters,
        },
        "test_code": test_code,
    }
    with open(os.path.join(custom_dir, f"{name}.json"), 'w') as f:
        json.dump(tool_def, f, indent=2)

    return f"OK: Tool '{name}' created and saved to tools/custom/{name}.json"


def tool_submit_design(title: str, objective: str, tasks: list,
                       files_to_create: list = None,
                       files_to_modify: list = None,
                       constraints: list = None,
                       tests: list = None) -> str:
    """Submit design briefing for review and execution."""
    global _SUBMITTED_BRIEFING
    _SUBMITTED_BRIEFING = {
        "title": title,
        "objective": objective,
        "tasks": tasks,
        "files_to_create": files_to_create or [],
        "files_to_modify": files_to_modify or [],
        "constraints": constraints or [],
        "tests": tests or [],
    }
    return json.dumps(_SUBMITTED_BRIEFING, indent=2, ensure_ascii=False)


def get_submitted_briefing() -> Optional[dict]:
    """Return the last submitted briefing (used by ChatEngine)."""
    return _SUBMITTED_BRIEFING


def clear_submitted_briefing() -> None:
    """Clear the submitted briefing after consumption."""
    global _SUBMITTED_BRIEFING
    _SUBMITTED_BRIEFING = None


def tool_spawn_agents(subtasks: list, context: str = "") -> str:
    """Spawn sub-agents to work in parallel on independent tasks."""
    try:
        from swarm.coordinator import SwarmCoordinator
    except ImportError:
        return "ERROR: Swarm module not available."

    if not subtasks or not isinstance(subtasks, list):
        return "ERROR: subtasks must be a list of {name, goal, files} objects."

    coordinator = SwarmCoordinator(
        max_workers=min(3, len(subtasks)),
        sandbox_dir=os.path.dirname(__file__) or ".",
        verbose=True,
    )

    result = coordinator.execute(subtasks, context=context)
    return json.dumps(result, indent=2, default=str)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    registry.register("plan", {
        "name": "plan",
        "description": "Create or read the execution plan. Use 'read' to see current, 'write' to update.",
        "parameters": {"type": "object", "properties": {
            "action": {"type": "string", "enum": ["read", "write"]},
            "content": {"type": "string", "description": "Plan content (only for 'write')"}
        }, "required": ["action"]}
    }, lambda a: tool_plan(a["action"], a.get("content", "")), category="meta")

    registry.register("finish", {
        "name": "finish",
        "description": "Signal task complete. Call when done or tests pass 100%.",
        "parameters": {"type": "object", "properties": {
            "result": {"type": "string", "description": "Summary of what was accomplished"}
        }, "required": ["result"]}
    }, lambda a: tool_finish(a["result"]), category="meta")

    registry.register("ask_user", {
        "name": "ask_user",
        "description": "Ask the user a question. Only works in interactive mode (--interactive).",
        "parameters": {"type": "object", "properties": {
            "question": {"type": "string", "description": "Question to ask"}
        }, "required": ["question"]}
    }, lambda a: tool_ask_user(a["question"]), category="meta")

    registry.register("spawn_agents", {
        "name": "spawn_agents",
        "description": "Spawn sub-agents to work in parallel on independent tasks. Each subtask runs in its own agent loop.",
        "parameters": {"type": "object", "properties": {
            "subtasks": {"type": "array", "items": {"type": "object", "properties": {
                "name": {"type": "string"}, "goal": {"type": "string"},
                "files": {"type": "array", "items": {"type": "string"}}
            }}, "description": "List of independent subtasks"},
            "context": {"type": "string", "description": "Shared context for all children"}
        }, "required": ["subtasks"]}
    }, lambda a: tool_spawn_agents(a["subtasks"], a.get("context", "")), category="meta")

    registry.register("submit_design", {
        "name": "submit_design",
        "description": "Submit a structured design briefing for review and autonomous execution. Call this when the design is complete.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string", "description": "Brief title for the task"},
            "objective": {"type": "string", "description": "What this implementation achieves"},
            "tasks": {"type": "array", "items": {"type": "object", "properties": {
                "step": {"type": "integer"},
                "description": {"type": "string"},
                "verification": {"type": "string"},
            }}, "description": "Ordered list of implementation steps"},
            "files_to_create": {"type": "array", "items": {"type": "object", "properties": {
                "path": {"type": "string"},
                "purpose": {"type": "string"},
            }}, "description": "New files to create"},
            "files_to_modify": {"type": "array", "items": {"type": "object", "properties": {
                "path": {"type": "string"},
                "changes": {"type": "string"},
            }}, "description": "Existing files to modify"},
            "constraints": {"type": "array", "items": {"type": "string"},
                           "description": "Technical constraints or rules"},
            "tests": {"type": "array", "items": {"type": "string"},
                     "description": "Verification tests to run"},
        }, "required": ["title", "objective", "tasks"]}
    }, lambda a: tool_submit_design(
        a["title"], a["objective"], a["tasks"],
        a.get("files_to_create"), a.get("files_to_modify"),
        a.get("constraints"), a.get("tests"),
    ), category="meta")

    registry.register("create_tool", {
        "name": "create_tool",
        "description": "Create a new tool dynamically. Code is validated for safety and tested before registering.",
        "parameters": {"type": "object", "properties": {
            "name": {"type": "string", "description": "Tool name (valid Python identifier)"},
            "description": {"type": "string", "description": "What the tool does"},
            "code": {"type": "string", "description": "Python code defining tool_<name>(**kwargs) function"},
            "parameters": {"type": "object", "description": "OpenAI function calling parameters schema"},
            "test_code": {"type": "string", "description": "Python test code with assertions"}
        }, "required": ["name", "description", "code", "parameters"]}
    }, lambda a: tool_create_tool(a["name"], a["description"], a["code"],
                                   a["parameters"], a.get("test_code", "")),
    category="meta")
