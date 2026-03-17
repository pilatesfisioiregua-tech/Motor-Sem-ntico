"""Schema validation tool — validate_schema (JSON Schema, OpenAPI)."""

import os
import re
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def _validate_json_schema(schema: dict, data: dict) -> list:
    """Validate data against JSON Schema. Basic implementation without jsonschema lib."""
    errors = []

    def _check(schema_part, data_part, path="$"):
        if not isinstance(schema_part, dict):
            return

        schema_type = schema_part.get("type")

        # Type checking
        type_map = {
            "string": str, "integer": int, "number": (int, float),
            "boolean": bool, "array": list, "object": dict, "null": type(None),
        }
        if schema_type and schema_type in type_map:
            expected = type_map[schema_type]
            if not isinstance(data_part, expected):
                errors.append({
                    "path": path,
                    "message": f"Expected {schema_type}, got {type(data_part).__name__}",
                })
                return

        # Required fields
        if schema_type == "object":
            required = schema_part.get("required", [])
            if isinstance(data_part, dict):
                for req in required:
                    if req not in data_part:
                        errors.append({"path": f"{path}.{req}", "message": "Required field missing"})

                # Check properties
                props = schema_part.get("properties", {})
                for key, prop_schema in props.items():
                    if key in data_part:
                        _check(prop_schema, data_part[key], f"{path}.{key}")

        # Array items
        elif schema_type == "array" and isinstance(data_part, list):
            items_schema = schema_part.get("items", {})
            min_items = schema_part.get("minItems", 0)
            max_items = schema_part.get("maxItems", float('inf'))
            if len(data_part) < min_items:
                errors.append({"path": path, "message": f"Array has {len(data_part)} items, min {min_items}"})
            if len(data_part) > max_items:
                errors.append({"path": path, "message": f"Array has {len(data_part)} items, max {max_items}"})
            for i, item in enumerate(data_part[:20]):
                _check(items_schema, item, f"{path}[{i}]")

        # String constraints
        elif schema_type == "string" and isinstance(data_part, str):
            min_len = schema_part.get("minLength", 0)
            max_len = schema_part.get("maxLength", float('inf'))
            if len(data_part) < min_len:
                errors.append({"path": path, "message": f"String length {len(data_part)} < minLength {min_len}"})
            if len(data_part) > max_len:
                errors.append({"path": path, "message": f"String length {len(data_part)} > maxLength {max_len}"})
            pattern = schema_part.get("pattern")
            if pattern and not re.match(pattern, data_part):
                errors.append({"path": path, "message": f"Does not match pattern: {pattern}"})
            enum = schema_part.get("enum")
            if enum and data_part not in enum:
                errors.append({"path": path, "message": f"Value not in enum: {enum}"})

        # Number constraints
        elif schema_type in ("integer", "number") and isinstance(data_part, (int, float)):
            minimum = schema_part.get("minimum")
            maximum = schema_part.get("maximum")
            if minimum is not None and data_part < minimum:
                errors.append({"path": path, "message": f"Value {data_part} < minimum {minimum}"})
            if maximum is not None and data_part > maximum:
                errors.append({"path": path, "message": f"Value {data_part} > maximum {maximum}"})

    _check(schema, data)
    return errors


def tool_validate_schema(schema_file: str, data_file: str = "",
                         data_string: str = "") -> str:
    """Validate JSON/YAML data against a JSON Schema or OpenAPI spec."""
    # Load schema
    schema_path = os.path.join(_SANDBOX, schema_file) if not os.path.isabs(schema_file) else schema_file
    if not os.path.isfile(schema_path):
        return f"ERROR: Schema file not found: {schema_file}"

    try:
        with open(schema_path, 'r') as f:
            content = f.read()
        if schema_path.endswith(('.yml', '.yaml')):
            # Basic YAML parsing (key: value only, no full YAML parser)
            return json.dumps({"error": "YAML schemas need PyYAML. Use JSON schema instead."})
        schema = json.loads(content)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in schema: {e}"})

    # Load data
    data = None
    if data_string:
        try:
            data = json.loads(data_string)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON in data_string: {e}"})
    elif data_file:
        data_path = os.path.join(_SANDBOX, data_file) if not os.path.isabs(data_file) else data_file
        if not os.path.isfile(data_path):
            return json.dumps({"error": f"Data file not found: {data_file}"})
        try:
            with open(data_path) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON in data file: {e}"})
    else:
        return json.dumps({"error": "Provide either data_file or data_string."})

    errors = _validate_json_schema(schema, data)

    return json.dumps({
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors[:20],
    }, indent=2)


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("validate_schema", {
        "name": "validate_schema",
        "description": "Validate JSON data against a JSON Schema. Returns validation errors.",
        "parameters": {"type": "object", "properties": {
            "schema_file": {"type": "string", "description": "Path to JSON Schema file"},
            "data_file": {"type": "string", "description": "Path to JSON data file"},
            "data_string": {"type": "string", "description": "JSON data as string (alternative to data_file)"}
        }, "required": ["schema_file"]}
    }, lambda a: tool_validate_schema(a["schema_file"], a.get("data_file", ""),
                                       a.get("data_string", "")),
    category="schema")
