"""Code OS v2 — Dynamic ToolRegistry with hot-reload support."""

import os
import json
import importlib
from typing import Dict, List, Callable, Any, Optional, Tuple


class ToolRegistry:
    """Central registry for all tools. Supports dynamic registration and hot-reload."""

    def __init__(self):
        self._tools: Dict[str, dict] = {}  # name -> {schema, handler, category}
        self._categories: Dict[str, List[str]] = {}  # category -> [tool_names]

    def register(self, name: str, schema: dict, handler: Callable,
                 category: str = "misc") -> None:
        """Register a tool with its OpenAI function calling schema and handler."""
        self._tools[name] = {
            "schema": schema,
            "handler": handler,
            "category": category,
        }
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        if name in self._tools:
            cat = self._tools[name]["category"]
            del self._tools[name]
            if cat in self._categories:
                self._categories[cat] = [n for n in self._categories[cat] if n != name]

    def get_schemas(self, categories: Optional[List[str]] = None,
                    names: Optional[set] = None) -> list:
        """Get OpenAI function calling schemas for tools, optionally filtered."""
        schemas = []
        for name, tool in self._tools.items():
            if categories and tool["category"] not in categories:
                continue
            if names and name not in names:
                continue
            schemas.append({"type": "function", "function": tool["schema"]})
        return schemas

    def execute(self, name: str, args: dict) -> Tuple[str, bool]:
        """Execute a tool by name. Returns (result_string, is_error)."""
        if name not in self._tools:
            return f"ERROR: Unknown tool '{name}'", True
        try:
            result = self._tools[name]["handler"](args)
            is_error = isinstance(result, str) and result.startswith("ERROR:")
            return result, is_error
        except ValueError as e:
            return f"ERROR: {e}", True
        except Exception as e:
            return f"ERROR: {type(e).__name__}: {e}", True

    def list_tools(self) -> Dict[str, List[str]]:
        """List all registered tools by category."""
        return dict(self._categories)

    def tool_count(self) -> int:
        return len(self._tools)

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool_schema(self, name: str) -> Optional[dict]:
        """Get schema for a specific tool."""
        if name in self._tools:
            return self._tools[name]["schema"]
        return None

    def find_similar(self, name: str, max_results: int = 3) -> List[str]:
        """Find tools with similar names (for typo correction)."""
        if not name:
            return []
        candidates = []
        name_lower = name.lower()
        for tool_name in self._tools:
            # Substring match
            if name_lower in tool_name or tool_name in name_lower:
                candidates.append(tool_name)
            # Shared prefix
            elif len(name_lower) > 3 and tool_name.startswith(name_lower[:4]):
                candidates.append(tool_name)
        return candidates[:max_results]

    def load_custom_tools(self, custom_dir: str) -> int:
        """Load custom tools from tools/custom/ directory. Returns count loaded."""
        loaded = 0
        if not os.path.isdir(custom_dir):
            return 0
        for fname in os.listdir(custom_dir):
            if not fname.endswith(".json"):
                continue
            try:
                with open(os.path.join(custom_dir, fname)) as f:
                    tool_def = json.load(f)
                name = tool_def["name"]
                code = tool_def["code"]
                schema = tool_def["schema"]
                # Create handler from code string
                namespace = {}
                exec(code, namespace)  # noqa: S102
                handler_name = f"tool_{name}"
                if handler_name in namespace:
                    self.register(
                        name=name,
                        schema=schema,
                        handler=lambda a, fn=namespace[handler_name]: fn(**a),
                        category="custom",
                    )
                    loaded += 1
            except Exception:
                continue
        return loaded


def create_default_registry(sandbox_dir: str = "", project_dir: str = "") -> ToolRegistry:
    """Create a ToolRegistry with all built-in tools registered."""
    from .filesystem import register_tools as reg_fs
    from .search import register_tools as reg_search
    from .shell import register_tools as reg_shell
    from .meta import register_tools as reg_meta

    registry = ToolRegistry()
    reg_fs(registry, sandbox_dir, project_dir)
    reg_search(registry, sandbox_dir, project_dir)
    reg_shell(registry, sandbox_dir, project_dir)
    reg_meta(registry)

    # Register mochila tool (reference backpack)
    from core.mochila import consultar as mochila_consultar
    registry.register("mochila", {
        "name": "mochila",
        "description": "Consulta tu mochila de referencia. Secciones: herramientas, reglas, rutas, proyecto, briefing, errores, modos. Úsala cuando necesites recordar cómo usar tools, rutas @project/, o protocolo de ejecución.",
        "parameters": {"type": "object", "properties": {
            "seccion": {"type": "string", "description": "Sección a consultar: herramientas | reglas | rutas | proyecto | briefing | errores | modos"}
        }, "required": ["seccion"]}
    }, lambda a: mochila_consultar(a["seccion"]), category="meta")

    # Try loading additional tool modules (fail silently if not yet created)
    optional_modules = [
        "git", "web", "testing", "security", "database", "http",
        "docker", "analysis", "docs", "cicd", "issues", "review",
        "typecheck", "profiling", "cleanup", "environment", "schema",
        "remember", "patterns", "explorer", "swarm_algebra",
        "ast_tools", "test_generator", "gestor_tools",
    ]
    for mod_name in optional_modules:
        try:
            mod = importlib.import_module(f".{mod_name}", package="tools")
            if hasattr(mod, "register_tools"):
                mod.register_tools(registry, sandbox_dir)
        except (ImportError, ModuleNotFoundError):
            pass

    # Load custom tools
    custom_dir = os.path.join(os.path.dirname(__file__), "custom")
    registry.load_custom_tools(custom_dir)

    return registry
