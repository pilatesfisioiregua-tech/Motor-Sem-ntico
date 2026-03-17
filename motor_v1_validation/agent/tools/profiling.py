"""Profiling tools — profile_performance, memory_usage."""

import os
import json
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""


def tool_profile_performance(file_path: str, function: str = "") -> str:
    """Profile Python file with cProfile. Returns top functions by time."""
    abs_path = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {file_path}"

    # Build profiling script
    if function:
        run_code = f"import {os.path.splitext(os.path.basename(file_path))[0]} as m; m.{function}()"
    else:
        run_code = f"exec(open('{abs_path}').read())"

    profile_script = f"""
import cProfile
import pstats
import io

pr = cProfile.Profile()
pr.enable()
try:
    {run_code}
except SystemExit:
    pass
except Exception as e:
    print(f"EXEC_ERROR: {{e}}")
pr.disable()

s = io.StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats(20)
print(s.getvalue())
"""
    try:
        result = subprocess.run(
            ["python3", "-c", profile_script],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(abs_path) or _SANDBOX
        )
        output = result.stdout + result.stderr
        return json.dumps({
            "file": file_path,
            "function": function or "(main)",
            "profile_output": output[:5000],
            "exit_code": result.returncode,
        }, indent=2)
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Profiling timed out after 60s"})


def tool_memory_usage(file_path: str, function: str = "") -> str:
    """Profile memory usage with tracemalloc."""
    abs_path = os.path.join(_SANDBOX, file_path) if not os.path.isabs(file_path) else file_path
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {file_path}"

    if function:
        run_code = f"import {os.path.splitext(os.path.basename(file_path))[0]} as m; m.{function}()"
    else:
        run_code = f"exec(open('{abs_path}').read())"

    mem_script = f"""
import tracemalloc
import json

tracemalloc.start()
try:
    {run_code}
except SystemExit:
    pass
except Exception as e:
    print(f"EXEC_ERROR: {{e}}")

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

results = []
for stat in top_stats[:20]:
    results.append({{
        "file": str(stat.traceback),
        "size_kb": round(stat.size / 1024, 2),
        "count": stat.count,
    }})

current, peak = tracemalloc.get_traced_memory()
print(json.dumps({{
    "current_mb": round(current / 1024 / 1024, 2),
    "peak_mb": round(peak / 1024 / 1024, 2),
    "top_allocations": results,
}}))
"""
    try:
        result = subprocess.run(
            ["python3", "-c", mem_script],
            capture_output=True, text=True, timeout=60,
            cwd=os.path.dirname(abs_path) or _SANDBOX
        )
        try:
            return result.stdout
        except json.JSONDecodeError:
            return json.dumps({"output": result.stdout[:3000], "stderr": result.stderr[:1000]})
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Memory profiling timed out after 60s"})


def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("profile_performance", {
        "name": "profile_performance",
        "description": "Profile Python file with cProfile. Returns top 20 functions by time.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Python file to profile"},
            "function": {"type": "string", "description": "Specific function to profile"}
        }, "required": ["file_path"]}
    }, lambda a: tool_profile_performance(a["file_path"], a.get("function", "")),
    category="profiling")

    registry.register("memory_usage", {
        "name": "memory_usage",
        "description": "Profile memory usage with tracemalloc. Returns allocations.",
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Python file to profile"},
            "function": {"type": "string", "description": "Specific function to profile"}
        }, "required": ["file_path"]}
    }, lambda a: tool_memory_usage(a["file_path"], a.get("function", "")),
    category="profiling")
