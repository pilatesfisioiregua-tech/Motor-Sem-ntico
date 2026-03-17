"""AST analysis tools — ast_analyze, ast_find_dependencies, ast_detect_patterns, ast_complexity_report."""

import os
import ast
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from . import ToolRegistry

_SANDBOX = ""

SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'dist', 'build',
             '.mypy_cache', '.pytest_cache', '.tox', '.eggs', 'egg-info'}

# Common stdlib top-level modules (compatible with Python 3.9+).
_STDLIB_MODULES = {
    'abc', 'aifc', 'argparse', 'array', 'ast', 'asynchat', 'asyncio', 'asyncore',
    'atexit', 'base64', 'bdb', 'binascii', 'binhex', 'bisect', 'builtins',
    'bz2', 'calendar', 'cgi', 'cgitb', 'chunk', 'cmath', 'cmd', 'code',
    'codecs', 'codeop', 'collections', 'colorsys', 'compileall', 'concurrent',
    'configparser', 'contextlib', 'contextvars', 'copy', 'copyreg', 'cProfile',
    'crypt', 'csv', 'ctypes', 'curses', 'dataclasses', 'datetime', 'dbm',
    'decimal', 'difflib', 'dis', 'distutils', 'doctest', 'email', 'encodings',
    'enum', 'errno', 'faulthandler', 'fcntl', 'filecmp', 'fileinput', 'fnmatch',
    'fractions', 'ftplib', 'functools', 'gc', 'getopt', 'getpass', 'gettext',
    'glob', 'grp', 'gzip', 'hashlib', 'heapq', 'hmac', 'html', 'http',
    'idlelib', 'imaplib', 'imghdr', 'imp', 'importlib', 'inspect', 'io',
    'ipaddress', 'itertools', 'json', 'keyword', 'lib2to3', 'linecache',
    'locale', 'logging', 'lzma', 'mailbox', 'mailcap', 'marshal', 'math',
    'mimetypes', 'mmap', 'modulefinder', 'multiprocessing', 'netrc', 'nis',
    'nntplib', 'numbers', 'operator', 'optparse', 'os', 'ossaudiodev',
    'pathlib', 'pdb', 'pickle', 'pickletools', 'pipes', 'pkgutil', 'platform',
    'plistlib', 'poplib', 'posix', 'posixpath', 'pprint', 'profile', 'pstats',
    'pty', 'pwd', 'py_compile', 'pyclbr', 'pydoc', 'queue', 'quopri',
    'random', 're', 'readline', 'reprlib', 'resource', 'rlcompleter', 'runpy',
    'sched', 'secrets', 'select', 'selectors', 'shelve', 'shlex', 'shutil',
    'signal', 'site', 'smtpd', 'smtplib', 'sndhdr', 'socket', 'socketserver',
    'sqlite3', 'ssl', 'stat', 'statistics', 'string', 'stringprep', 'struct',
    'subprocess', 'sunau', 'symtable', 'sys', 'sysconfig', 'syslog', 'tabnanny',
    'tarfile', 'telnetlib', 'tempfile', 'termios', 'test', 'textwrap', 'threading',
    'time', 'timeit', 'tkinter', 'token', 'tokenize', 'tomllib', 'trace',
    'traceback', 'tracemalloc', 'tty', 'turtle', 'turtledemo', 'types',
    'typing', 'unicodedata', 'unittest', 'urllib', 'uu', 'uuid', 'venv',
    'warnings', 'wave', 'weakref', 'webbrowser', 'winreg', 'winsound',
    'wsgiref', 'xdrlib', 'xml', 'xmlrpc', 'zipapp', 'zipfile', 'zipimport',
    'zlib', '_thread', '__future__',
}


def _resolve_path(path: str) -> str:
    """Resolve path against sandbox root if not absolute."""
    if os.path.isabs(path):
        return path
    return os.path.join(_SANDBOX, path) if _SANDBOX else os.path.abspath(path)


def _mccabe_complexity(node: ast.AST) -> int:
    """Estimate McCabe cyclomatic complexity for a function/class node."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                              ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            # Each additional boolean operand adds a branch
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            complexity += 1
    return complexity


def _name_of(node: ast.AST) -> str:
    """Extract a human-readable name from an AST node."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_of(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    if isinstance(node, ast.Constant):
        return repr(node.value)
    return ast.dump(node)


# ---------------------------------------------------------------------------
# Tool 1: ast_analyze
# ---------------------------------------------------------------------------

def tool_ast_analyze(file_path: str) -> str:
    """Analyze a Python file using AST. Returns classes, functions, imports, lines, complexity."""
    resolved = _resolve_path(file_path)
    if not os.path.isfile(resolved):
        return json.dumps({"error": f"File not found: {file_path}"})

    try:
        with open(resolved, 'r', errors='replace') as f:
            source = f.read()
    except PermissionError:
        return json.dumps({"error": f"Permission denied: {file_path}"})

    lines = source.splitlines()
    total_lines = len(lines)
    blank_lines = sum(1 for ln in lines if not ln.strip())
    comment_lines = sum(1 for ln in lines if ln.strip().startswith('#'))

    # Non-Python files: return basic stats only
    if not file_path.endswith('.py'):
        return json.dumps({
            "file": file_path,
            "is_python": False,
            "total_lines": total_lines,
            "blank_lines": blank_lines,
            "comment_lines": comment_lines,
            "total_chars": len(source),
        }, indent=2)

    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return json.dumps({"error": f"Syntax error in {file_path}: {e}"})

    # Collect classes
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in ast.iter_child_nodes(node)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            end_line = getattr(node, 'end_lineno', node.lineno)
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": end_line,
                "methods": methods,
                "method_count": len(methods),
                "bases": [_name_of(b) for b in node.bases],
                "complexity": _mccabe_complexity(node),
            })

    # Collect top-level functions
    functions = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end_line = getattr(node, 'end_lineno', node.lineno + 5)
            is_async = isinstance(node, ast.AsyncFunctionDef)
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "end_line": end_line,
                "loc": end_line - node.lineno + 1,
                "args": len(node.args.args),
                "is_async": is_async,
                "complexity": _mccabe_complexity(node),
                "decorators": [_name_of(d) for d in node.decorator_list],
            })

    # Collect imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "alias": alias.asname, "type": "import"})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append({
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "type": "from",
                })

    # Overall complexity estimate (avg of all functions + classes)
    all_complexities = [f["complexity"] for f in functions]
    for cls in classes:
        all_complexities.append(cls["complexity"])
    avg_complexity = round(sum(all_complexities) / len(all_complexities), 1) if all_complexities else 0

    return json.dumps({
        "file": file_path,
        "is_python": True,
        "total_lines": total_lines,
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": total_lines - blank_lines - comment_lines,
        "classes": classes,
        "class_count": len(classes),
        "functions": functions,
        "function_count": len(functions),
        "imports": imports,
        "import_count": len(imports),
        "avg_complexity": avg_complexity,
    }, indent=2)


# ---------------------------------------------------------------------------
# Tool 2: ast_find_dependencies
# ---------------------------------------------------------------------------

def tool_ast_find_dependencies(file_path: str) -> str:
    """Extract all imports from a Python file, categorized into stdlib/third-party/local."""
    resolved = _resolve_path(file_path)
    if not os.path.isfile(resolved):
        return json.dumps({"error": f"File not found: {file_path}"})
    if not file_path.endswith('.py'):
        return json.dumps({"error": f"Not a Python file: {file_path}"})

    try:
        with open(resolved, 'r', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return json.dumps({"error": f"Syntax error in {file_path}: {e}"})
    except PermissionError:
        return json.dumps({"error": f"Permission denied: {file_path}"})

    stdlib = []
    third_party = []
    local = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                _categorize_import(alias.name, None, alias.asname, node.lineno,
                                   stdlib, third_party, local)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level or 0
            names = [alias.name for alias in node.names]
            if level > 0:
                # Relative import -> always local
                local.append({
                    "module": ("." * level) + module,
                    "names": names,
                    "line": node.lineno,
                })
            else:
                _categorize_import(module, names, None, node.lineno,
                                   stdlib, third_party, local)

    return json.dumps({
        "file": file_path,
        "stdlib": stdlib,
        "stdlib_count": len(stdlib),
        "third_party": third_party,
        "third_party_count": len(third_party),
        "local": local,
        "local_count": len(local),
        "total_imports": len(stdlib) + len(third_party) + len(local),
        "dependency_graph": {
            "stdlib": sorted({d["module"].split('.')[0] for d in stdlib}),
            "third_party": sorted({d["module"].split('.')[0] for d in third_party}),
            "local": sorted({d["module"].split('.')[0] for d in local}),
        },
    }, indent=2)


def _categorize_import(module: str, names: list, alias: str, line: int,
                       stdlib: list, third_party: list, local: list) -> None:
    """Categorize a single import into stdlib, third-party, or local."""
    top_level = module.split('.')[0] if module else ""
    entry = {"module": module, "line": line}
    if names:
        entry["names"] = names
    if alias:
        entry["alias"] = alias

    if top_level in _STDLIB_MODULES:
        stdlib.append(entry)
    elif top_level.startswith('_') and not top_level.startswith('__'):
        # Private/C-extension modules are typically stdlib
        stdlib.append(entry)
    else:
        third_party.append(entry)


# ---------------------------------------------------------------------------
# Tool 3: ast_detect_patterns
# ---------------------------------------------------------------------------

def tool_ast_detect_patterns(file_path: str) -> str:
    """Detect common design patterns in a Python file: singleton, factory, observer, decorator."""
    resolved = _resolve_path(file_path)
    if not os.path.isfile(resolved):
        return json.dumps({"error": f"File not found: {file_path}"})
    if not file_path.endswith('.py'):
        return json.dumps({"error": f"Not a Python file: {file_path}"})

    try:
        with open(resolved, 'r', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except SyntaxError as e:
        return json.dumps({"error": f"Syntax error in {file_path}: {e}"})
    except PermissionError:
        return json.dumps({"error": f"Permission denied: {file_path}"})

    patterns_found = []

    # --- Singleton detection ---
    # Look for classes with _instance attribute or __new__ that checks _instance
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        attr_names = set()
        method_names = set()
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_names.add(child.name)
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        attr_names.add(target.id)

        # Check for _instance class variable or __new__ override
        has_instance_attr = any(n for n in attr_names
                                if n in ('_instance', '_singleton', '__instance'))
        has_new = '__new__' in method_names

        if has_instance_attr or (has_new and _body_references(node, '_instance')):
            patterns_found.append({
                "pattern": "singleton",
                "class": node.name,
                "line": node.lineno,
                "evidence": {
                    "has_instance_attr": has_instance_attr,
                    "has_new_override": has_new,
                },
            })

    # --- Factory detection ---
    # Functions that create and return objects based on input (if/elif chains returning different types)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Heuristic: function has if/elif and multiple return statements with Call nodes
        return_calls = []
        has_conditional = False
        for child in ast.walk(node):
            if isinstance(child, ast.If):
                has_conditional = True
            if isinstance(child, ast.Return) and child.value:
                if isinstance(child.value, ast.Call):
                    return_calls.append(_name_of(child.value.func))

        unique_returns = set(return_calls)
        if has_conditional and len(unique_returns) >= 2:
            patterns_found.append({
                "pattern": "factory",
                "function": node.name,
                "line": node.lineno,
                "evidence": {
                    "conditional_returns": True,
                    "return_types": sorted(unique_returns),
                    "return_count": len(return_calls),
                },
            })

    # --- Observer detection ---
    # Classes with subscribe/register/on + notify/emit/dispatch methods
    _subscribe_names = {'subscribe', 'register', 'add_listener', 'on', 'attach', 'add_observer'}
    _notify_names = {'notify', 'emit', 'dispatch', 'publish', 'fire', 'trigger', 'notify_all'}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        methods = {child.name for child in ast.iter_child_nodes(node)
                   if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))}

        subscribe_matches = methods & _subscribe_names
        notify_matches = methods & _notify_names
        if subscribe_matches and notify_matches:
            patterns_found.append({
                "pattern": "observer",
                "class": node.name,
                "line": node.lineno,
                "evidence": {
                    "subscribe_methods": sorted(subscribe_matches),
                    "notify_methods": sorted(notify_matches),
                },
            })

    # --- Decorator pattern detection ---
    # Classes that wrap another object (store it in __init__) and delegate methods
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        init_method = None
        other_methods = []
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef) and child.name == '__init__':
                init_method = child
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not child.name.startswith('_'):
                    other_methods.append(child)

        if init_method is None or not other_methods:
            continue

        # Check if __init__ stores a wrapped object (self._wrapped = ..., self._component = ...)
        wrapped_attrs = set()
        for stmt in ast.walk(init_method):
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if (isinstance(target, ast.Attribute) and
                            isinstance(target.value, ast.Name) and
                            target.value.id == 'self'):
                        attr = target.attr
                        if any(kw in attr.lower() for kw in
                               ('wrapped', 'component', 'delegate', 'inner', 'base', 'original')):
                            wrapped_attrs.add(attr)

        # Check if other methods delegate to the wrapped attribute
        delegating_methods = []
        for method in other_methods:
            for child in ast.walk(method):
                if isinstance(child, ast.Attribute):
                    if (isinstance(child.value, ast.Attribute) and
                            isinstance(child.value.value, ast.Name) and
                            child.value.value.id == 'self' and
                            child.value.attr in wrapped_attrs):
                        delegating_methods.append(method.name)
                        break

        if wrapped_attrs and delegating_methods:
            patterns_found.append({
                "pattern": "decorator",
                "class": node.name,
                "line": node.lineno,
                "evidence": {
                    "wrapped_attributes": sorted(wrapped_attrs),
                    "delegating_methods": sorted(set(delegating_methods)),
                },
            })

    return json.dumps({
        "file": file_path,
        "patterns_found": patterns_found,
        "pattern_count": len(patterns_found),
        "patterns_checked": ["singleton", "factory", "observer", "decorator"],
    }, indent=2)


def _body_references(node: ast.AST, name: str) -> bool:
    """Check if any node in the body references a given name as a string."""
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and child.id == name:
            return True
        if isinstance(child, ast.Attribute) and child.attr == name:
            return True
    return False


# ---------------------------------------------------------------------------
# Tool 4: ast_complexity_report
# ---------------------------------------------------------------------------

def tool_ast_complexity_report(directory: str) -> str:
    """Scan all .py files in a directory and return aggregate complexity stats."""
    resolved = _resolve_path(directory)
    if not os.path.isdir(resolved):
        return json.dumps({"error": f"Not a directory: {directory}"})

    file_reports = []
    total_lines = 0
    total_functions = 0
    total_classes = 0
    total_files = 0
    errors = []

    for dirpath, dirnames, filenames in os.walk(resolved):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in sorted(filenames):
            if not fname.endswith('.py'):
                continue

            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, resolved)
            total_files += 1

            try:
                with open(fpath, 'r', errors='replace') as f:
                    source = f.read()
                tree = ast.parse(source, filename=fpath)
            except SyntaxError as e:
                errors.append({"file": rel_path, "error": str(e)})
                continue
            except PermissionError:
                errors.append({"file": rel_path, "error": "Permission denied"})
                continue

            lines = len(source.splitlines())
            total_lines += lines

            funcs = []
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs.append({
                        "name": node.name,
                        "complexity": _mccabe_complexity(node),
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)

            total_functions += len(funcs)
            total_classes += len(classes)

            max_complexity = max((f["complexity"] for f in funcs), default=0)
            avg_complexity = (round(sum(f["complexity"] for f in funcs) / len(funcs), 1)
                              if funcs else 0)

            file_reports.append({
                "file": rel_path,
                "lines": lines,
                "functions": len(funcs),
                "classes": len(classes),
                "max_complexity": max_complexity,
                "avg_complexity": avg_complexity,
            })

    # Sort by max_complexity descending
    file_reports.sort(key=lambda r: r["max_complexity"], reverse=True)

    overall_avg = 0.0
    if file_reports:
        all_avgs = [r["avg_complexity"] for r in file_reports if r["avg_complexity"] > 0]
        if all_avgs:
            overall_avg = round(sum(all_avgs) / len(all_avgs), 1)

    return json.dumps({
        "directory": directory,
        "total_files": total_files,
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_classes": total_classes,
        "overall_avg_complexity": overall_avg,
        "most_complex_files": file_reports[:10],
        "all_files": file_reports,
        "errors": errors,
    }, indent=2)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_tools(registry: 'ToolRegistry', sandbox_dir: str = "") -> None:
    """Register AST analysis tools into the tool registry."""
    global _SANDBOX
    _SANDBOX = sandbox_dir

    registry.register("ast_analyze", {
        "name": "ast_analyze",
        "description": (
            "Analyze a Python file using AST. Returns classes, functions, imports, "
            "total lines, and complexity estimate. For non-Python files returns basic stats."
        ),
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Path to the file to analyze"},
        }, "required": ["file_path"]},
    }, lambda a: tool_ast_analyze(a["file_path"]), category="analysis")

    registry.register("ast_find_dependencies", {
        "name": "ast_find_dependencies",
        "description": (
            "Extract all imports from a Python file and categorize them into "
            "stdlib, third-party, and local. Returns dependency graph."
        ),
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Path to the Python file"},
        }, "required": ["file_path"]},
    }, lambda a: tool_ast_find_dependencies(a["file_path"]), category="analysis")

    registry.register("ast_detect_patterns", {
        "name": "ast_detect_patterns",
        "description": (
            "Detect common design patterns in a Python file: singleton, factory, "
            "observer, and decorator pattern."
        ),
        "parameters": {"type": "object", "properties": {
            "file_path": {"type": "string", "description": "Path to the Python file"},
        }, "required": ["file_path"]},
    }, lambda a: tool_ast_detect_patterns(a["file_path"]), category="analysis")

    registry.register("ast_complexity_report", {
        "name": "ast_complexity_report",
        "description": (
            "Scan all .py files in a directory and return aggregate complexity stats: "
            "total files, lines, functions, classes, average complexity, most complex files."
        ),
        "parameters": {"type": "object", "properties": {
            "directory": {"type": "string", "description": "Directory to scan"},
        }, "required": ["directory"]},
    }, lambda a: tool_ast_complexity_report(a["directory"]), category="analysis")
