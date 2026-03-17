"""Sandwich Validation — capas deterministas pre/post tool calls.

Patrón Sandwich LLM (60675): Código puro envuelve cada llamada LLM/tool.
- Pre-validación: ¿existe el tool? ¿parámetros correctos? ¿tipos válidos?
- Post-validación: ¿output coherente? ¿error detectado? ¿normalizar formato?
- Code validation: syntax check Python antes de escribir
- Context analysis: detección de modo, compresión de historial

Reduce hallucinated tool calls y respuestas malformadas.
"""

import json
import re
from typing import Tuple, Optional, Dict, List, Any


def pre_validate_tool_call(tool_name: str, tool_args: dict,
                           registry) -> Tuple[bool, Optional[str]]:
    """Validación determinista ANTES de ejecutar un tool call.

    Returns:
        (is_valid, error_message) — si is_valid=False, no ejecutar el tool.
    """
    # 1. ¿Existe el tool?
    if not registry.has_tool(tool_name):
        # Suggest closest match
        similar = registry.find_similar(tool_name)
        suggestion = f" ¿Quisiste decir: {', '.join(similar)}?" if similar else ""
        return False, f"Tool '{tool_name}' no existe.{suggestion}"

    # 2. ¿Parámetros requeridos presentes?
    schema = registry.get_tool_schema(tool_name)
    if schema:
        params_schema = schema.get("parameters", {})
        required = params_schema.get("required", [])
        for req in required:
            if req not in tool_args:
                return False, f"Tool '{tool_name}' requiere parámetro '{req}'."

        # 3. ¿Tipos básicos correctos?
        properties = params_schema.get("properties", {})
        for param_name, param_value in tool_args.items():
            if param_name in properties:
                expected_type = properties[param_name].get("type", "")
                if expected_type == "string" and not isinstance(param_value, str):
                    # Auto-coerce to string if possible
                    tool_args[param_name] = str(param_value)
                elif expected_type == "integer" and isinstance(param_value, str):
                    try:
                        tool_args[param_name] = int(param_value)
                    except ValueError:
                        return False, f"Parámetro '{param_name}' debe ser entero, recibido: '{param_value}'"

    # 4. Validaciones específicas por tool
    if tool_name in ("read_file", "write_file", "edit_file", "list_dir"):
        path = tool_args.get("path", "")
        # Detectar paths peligrosos
        if ".." in path:
            return False, f"Path con '..' no permitido: {path}"

    if tool_name == "edit_file":
        old_str = tool_args.get("old_string", "")
        new_str = tool_args.get("new_string", "")
        if not old_str:
            return False, "edit_file requiere old_string no vacío."
        if old_str == new_str:
            return False, "old_string y new_string son idénticos. No hay cambio."

    if tool_name == "db_insert":
        sql = tool_args.get("sql", "").strip().upper()
        if sql.startswith("DROP"):
            return False, "DROP bloqueado por seguridad."

    if tool_name == "run_command":
        cmd = tool_args.get("command", "")
        # Bloquear comandos destructivos obvios
        dangerous = ["rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){:|:&};:"]
        for d in dangerous:
            if d in cmd:
                return False, f"Comando potencialmente destructivo bloqueado: {cmd[:50]}"

    return True, None


def post_validate_result(tool_name: str, result: str,
                         is_error: bool) -> Tuple[str, bool]:
    """Validación determinista DESPUÉS de ejecutar un tool call.

    Normaliza el output y detecta problemas no capturados.

    Returns:
        (normalized_result, is_error) — resultado normalizado y flag de error actualizado.
    """
    if not result:
        return "(empty result)", is_error

    # Truncar resultados excesivamente largos para no contaminar el contexto
    if len(result) > 15000:
        truncated = result[:14000] + f"\n\n... [TRUNCADO: {len(result)} chars total. Usa read_file con offset/limit para ver más.]"
        return truncated, is_error

    # Detectar errores no marcados como tal
    if not is_error:
        error_indicators = [
            "ERROR:", "Traceback (most recent call",
            "FATAL:", "Permission denied",
            "ConnectionRefusedError", "TimeoutError",
        ]
        for indicator in error_indicators:
            if indicator in result:
                is_error = True
                break

    return result, is_error


# ============================================================
# EXTENDED SANDWICH — Code Validation (pattern 60675, 60663)
# ============================================================

def validate_code_output(tool_name: str, tool_args: dict) -> Tuple[bool, Optional[str]]:
    """Validate code BEFORE writing/editing files. Returns (is_valid, error_msg).

    Catches: syntax errors, placeholder code, obvious issues.
    Only validates Python files (.py extension or detected Python content).
    """
    if tool_name not in ("write_file", "edit_file"):
        return True, None

    # Determine content to validate
    if tool_name == "write_file":
        content = tool_args.get("content", "")
        path = tool_args.get("path", "")
    else:  # edit_file
        content = tool_args.get("new_string", "")
        path = tool_args.get("path", "")

    if not content or not content.strip():
        return True, None

    # Only validate Python files
    is_python = path.endswith(".py") or path.endswith(".pyw")
    if not is_python:
        return True, None

    # 1. Syntax check (only for write_file with complete files)
    if tool_name == "write_file" and len(content) > 20:
        try:
            compile(content, path or "<string>", "exec")
        except SyntaxError as e:
            return False, f"SyntaxError en código Python: {e.msg} (línea {e.lineno})"

    # 2. Placeholder detection
    placeholder_patterns = [
        r"#\s*TODO\s*:",
        r"#\s*FIXME\s*:",
        r"pass\s*#\s*implement",
        r"\.\.\.\s*#\s*implement",
        r"raise\s+NotImplementedError\(\s*\)",
    ]
    for pattern in placeholder_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return False, f"Código incompleto detectado: '{match.group(0).strip()}'. Implementa la lógica completa."

    return True, None


def pre_analyze_context(goal: str, history: list) -> Dict[str, Any]:
    """Deterministic analysis BEFORE sending to LLM. Returns hints for routing.

    Pattern 60675: Reduce problem space before LLM call.
    Pattern 60666: Detect execution mode from goal characteristics.
    """
    result = {
        "mode_hint": "standard",
        "should_compress": False,
        "goal_length": len(goal),
        "history_length": len(history),
    }

    goal_lower = goal.lower()

    # Quick mode detection
    quick_signals = ["typo", "rename", "corrige", "cambia nombre", "fix import",
                     "agrega comment", "quita", "borra linea", "simple", "rápido"]
    if any(s in goal_lower for s in quick_signals) and len(goal) < 200:
        result["mode_hint"] = "quick"

    # Deep mode detection
    deep_signals = ["arquitectura", "análisis profundo", "refactor completo",
                    "por qué falla", "diseña", "investiga", "swarm", "patrones"]
    if any(s in goal_lower for s in deep_signals):
        result["mode_hint"] = "deep"

    # Compression hint
    if len(history) > 20:
        result["should_compress"] = True

    return result


def post_session_summary(result: dict) -> Dict[str, Any]:
    """Generate deterministic post-session summary for flywheel feedback.

    Pattern 60668: Each cycle's output improves the next cycle's inputs.
    """
    log = result.get("log", [])
    iterations = result.get("iterations", 0)
    time_s = result.get("time_s", 0)
    cost = result.get("cost_usd", 0)

    tools_used = set()
    error_count = 0
    for entry in log:
        if isinstance(entry, dict):
            tools_used.add(entry.get("tool", ""))
            if entry.get("is_error"):
                error_count += 1

    return {
        "success": result.get("stop_reason") == "DONE",
        "iterations": iterations,
        "time_s": time_s,
        "cost_usd": cost,
        "cost_per_iteration": round(cost / max(iterations, 1), 4),
        "error_rate": round(error_count / max(iterations, 1), 2),
        "tools_used": list(tools_used),
        "model_used": result.get("model_used", ""),
        "task_type": result.get("task_type", ""),
        "mode": result.get("phase_info", {}).get("mode", "standard"),
    }
