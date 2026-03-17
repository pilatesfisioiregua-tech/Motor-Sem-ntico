# EXP6: Diseno Agente de Coding Minimo — Sintesis Mesa Redonda

**Fecha:** 2026-03-11
**Modelos consultados:**
- `stepfun/step-3.5-flash` — Razonamiento profundo (contexto, stuck detection, multi-modelo)
- `mistralai/devstral-2512` — Perspectiva coding (arquitectura limpia, clases, herramientas)
- `nvidia/llama-3.3-nemotron-super-49b-v1.5` — Perspectiva practica (seguridad, subprocess, errores)

**Consensos clave:**
1. Los 3 modelos coinciden en loop observe->think->act con max ~100-500 iteraciones
2. Los 3 proponen sandbox via path validation (no Docker)
3. Los 3 coinciden en blacklist de comandos peligrosos + timeout por comando
4. Los 3 proponen ventana deslizante para contexto (no sumarizacion LLM, demasiado costoso)
5. Los 3 proponen modelos diferentes para generar vs debugear

---

## 1. ARQUITECTURA

```
                    +------------------+
                    |   TASK (input)   |
                    +--------+---------+
                             |
                             v
              +-----------------------------+
              |     SYSTEM PROMPT + TOOLS   |
              |   (OpenAI function calling) |
              +-------------+---------------+
                            |
           +================|================+
           |    MAIN LOOP   |  (max 100 it)  |
           |                v                |
           |  +-------------------------+    |
           |  |   1. OBSERVE            |    |
           |  |   - Last tool result    |    |
           |  |   - Error if any        |    |
           |  |   (already in history)  |    |
           |  +------------+------------+    |
           |               |                 |
           |               v                 |
           |  +-------------------------+    |
           |  |   2. THINK              |    |
           |  |   - Select model        |    |
           |  |     (fast vs debug)     |    |
           |  |   - Call OpenRouter     |    |
           |  |     via curl+tempfile   |    |
           |  |   - Strip think tags    |    |
           |  |   - Parse tool_calls    |    |
           |  +------------+------------+    |
           |               |                 |
           |          +----+----+            |
           |          |         |            |
           |      tool_call   finish         |
           |          |         |            |
           |          v         v            |
           |  +-------------+ EXIT ------>  RESULT
           |  |   3. ACT    |               |
           |  |   - Validate|               |
           |  |   - Execute |               |
           |  |   - Capture |               |
           |  |     output  |               |
           |  +------+------+               |
           |         |                      |
           |         v                      |
           |  +-------------------------+   |
           |  |   4. CHECK              |   |
           |  |   - Stuck detection     |   |
           |  |   - Budget check        |   |
           |  |   - Context trim        |   |
           |  +------------+------------+   |
           |               |                |
           |               v                |
           |         [LOOP BACK]            |
           +================================+
```

### Decisiones de diseno

| Decision | Elegido | Descartado | Por que |
|----------|---------|------------|---------|
| Loop tipo | observe->think->act | Pipeline lineal | Permite adaptacion dinamica a errores |
| Sandbox | Path validation en codigo | Docker / chroot | Requisito: sin Docker. Path validation es suficiente para ~95% de casos |
| Tool format | OpenAI function calling | Prompt engineering JSON | Los modelos OpenRouter soportan `tools` nativo. Mas robusto que parsear JSON libre |
| Iteraciones max | 100 (no 500) | 500 como OpenHands | Nuestro caso es mas acotado. 100 suficiente, 500 quema presupuesto |
| Modelo LLM | subprocess + curl + tempfile | urllib/requests | Cloudflare bloquea requests. Tempfile evita problemas de shell escaping |

---

## 2. SPECS DE LAS 5 HERRAMIENTAS + FINISH

### Constantes

```python
SANDBOX_DIR = "/tmp/agent_sandbox"
MAX_FILE_SIZE = 500_000        # 500KB
COMMAND_TIMEOUT = 30           # segundos
MAX_OUTPUT_LEN = 10_000        # chars de output truncado
```

### Tool Definitions (OpenAI format para el API call)

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file. Returns the file content as string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from workspace root"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file. Creates parent directories if needed. Overwrites if exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from workspace root"},
                    "content": {"type": "string", "description": "Full file content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute a shell command in the workspace. Returns stdout+stderr. Timeout: 30s. Dangerous commands (rm, sudo, etc) are blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories at a path. Returns one entry per line.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path from workspace root. Default: '.'"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a glob pattern OR search file contents with a regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern for filenames (e.g. '*.py') or regex for content search"},
                    "path": {"type": "string", "description": "Root directory to search from. Default: '.'"},
                    "content_search": {"type": "boolean", "description": "If true, search file contents instead of names. Default: false"}
                },
                "required": ["pattern"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Signal that the task is complete. Call this when done.",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {"type": "string", "description": "Summary of what was accomplished"}
                },
                "required": ["result"]
            }
        }
    }
]
```

### Tool Implementations

```python
import os
import re
import json
import shlex
import fnmatch
import subprocess
import tempfile
import time
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field

def _resolve_path(relative_path: str, sandbox: str = SANDBOX_DIR) -> str:
    """Resolve and validate path is inside sandbox. Raises ValueError if not."""
    abs_path = os.path.abspath(os.path.join(sandbox, relative_path))
    if not abs_path.startswith(os.path.abspath(sandbox)):
        raise ValueError(f"Path escapes sandbox: {relative_path}")
    return abs_path

def tool_read_file(path: str) -> str:
    abs_path = _resolve_path(path)
    if not os.path.isfile(abs_path):
        return f"ERROR: File not found: {path}"
    size = os.path.getsize(abs_path)
    if size > MAX_FILE_SIZE:
        return f"ERROR: File too large ({size} bytes, max {MAX_FILE_SIZE})"
    with open(abs_path, 'r', errors='replace') as f:
        content = f.read()
    return content

def tool_write_file(path: str, content: str) -> str:
    if len(content) > MAX_FILE_SIZE:
        return f"ERROR: Content too large ({len(content)} chars, max {MAX_FILE_SIZE})"
    abs_path = _resolve_path(path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, 'w') as f:
        f.write(content)
    return f"OK: Written {len(content)} chars to {path}"

def tool_run_command(command: str) -> str:
    # Security: block dangerous commands
    BLOCKED = {'rm', 'rmdir', 'dd', 'mkfs', 'chmod', 'chown', 'sudo', 'su',
               'passwd', 'shutdown', 'reboot', 'halt', 'poweroff', 'fdisk',
               'parted', 'mount', 'umount', 'kill', 'killall', 'pkill'}
    BLOCKED_PATTERNS = [r'\brm\b', r'\bsudo\b', r'\bdd\b', r'>\s*/dev/',
                        r'\|\s*sh\b', r'\|\s*bash\b', r';\s*rm\b']

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            return f"ERROR: Command blocked by security policy (matched: {pattern})"

    try:
        args = shlex.split(command)
    except ValueError as e:
        return f"ERROR: Invalid command syntax: {e}"

    if args and args[0] in BLOCKED:
        return f"ERROR: Command '{args[0]}' is blocked by security policy"

    try:
        result = subprocess.run(
            command, shell=True,
            capture_output=True, text=True,
            timeout=COMMAND_TIMEOUT,
            cwd=SANDBOX_DIR
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n--- STDERR ---\n" + result.stderr)
        if not output.strip():
            output = f"(exit code {result.returncode}, no output)"
        # Truncate if too long
        if len(output) > MAX_OUTPUT_LEN:
            output = output[:MAX_OUTPUT_LEN] + f"\n... [TRUNCATED, {len(output)} total chars]"
        return f"Exit code: {result.returncode}\n{output}"
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {COMMAND_TIMEOUT}s"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"

def tool_list_dir(path: str = ".") -> str:
    abs_path = _resolve_path(path)
    if not os.path.isdir(abs_path):
        return f"ERROR: Not a directory: {path}"
    entries = sorted(os.listdir(abs_path))
    result = []
    for entry in entries:
        full = os.path.join(abs_path, entry)
        prefix = "d " if os.path.isdir(full) else "f "
        result.append(prefix + entry)
    return "\n".join(result) if result else "(empty directory)"

def tool_search_files(pattern: str, path: str = ".", content_search: bool = False) -> str:
    abs_root = _resolve_path(path)
    if not os.path.isdir(abs_root):
        return f"ERROR: Not a directory: {path}"

    matches = []
    if content_search:
        # Search file contents with regex
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"ERROR: Invalid regex: {e}"
        for root_dir, _, files in os.walk(abs_root):
            for fname in files:
                fpath = os.path.join(root_dir, fname)
                try:
                    with open(fpath, 'r', errors='replace') as f:
                        for i, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = os.path.relpath(fpath, abs_root)
                                matches.append(f"{rel}:{i}: {line.rstrip()}")
                                if len(matches) >= 50:
                                    break
                except (PermissionError, IsADirectoryError):
                    continue
            if len(matches) >= 50:
                break
    else:
        # Search by filename glob
        for root_dir, _, files in os.walk(abs_root):
            for fname in fnmatch.filter(files, pattern):
                rel = os.path.relpath(os.path.join(root_dir, fname), abs_root)
                matches.append(rel)
                if len(matches) >= 100:
                    break
            if len(matches) >= 100:
                break

    return "\n".join(matches) if matches else "(no matches)"

# Tool dispatcher
TOOL_DISPATCH = {
    "read_file":    lambda args: tool_read_file(args["path"]),
    "write_file":   lambda args: tool_write_file(args["path"], args["content"]),
    "run_command":  lambda args: tool_run_command(args["command"]),
    "list_dir":     lambda args: tool_list_dir(args.get("path", ".")),
    "search_files": lambda args: tool_search_files(
        args["pattern"], args.get("path", "."), args.get("content_search", False)
    ),
}
```

---

## 3. MECANISMOS DE SEGURIDAD

### 3.1 Sandbox de Filesystem

```python
# Toda ruta pasa por _resolve_path() que:
# 1. Convierte a absoluta via os.path.abspath
# 2. Verifica que empieza con SANDBOX_DIR
# 3. Raise ValueError si escapa
#
# SANDBOX_DIR se crea al inicio:
# os.makedirs(SANDBOX_DIR, exist_ok=True)
```

**Por que path validation y no chroot:** chroot requiere root. Docker es demasiado pesado. Path validation cubre el 95% de casos para un agente controlado. Si el modelo genera `../../etc/passwd`, se bloquea.

### 3.2 Command Safety

```python
# Dos niveles de proteccion:
# 1. BLOCKED set: comandos prohibidos por nombre (rm, sudo, dd, etc.)
# 2. BLOCKED_PATTERNS: regex para detectar patrones peligrosos incluso
#    en pipelines (e.g., "cat file | rm" no pasa el regex r'\brm\b')
#
# Por que blacklist y no whitelist:
# - Whitelist seria mas seguro pero limita al agente
# - OpenHands tampoco usa whitelist
# - La blacklist cubre los comandos destructivos obvios
# - El modelo deberia generar comandos seguros por diseno
```

### 3.3 Timeouts

```python
COMMAND_TIMEOUT = 30       # Por comando (subprocess.timeout)
MODEL_CALL_TIMEOUT = 120   # Por llamada a OpenRouter (curl --max-time)
TOTAL_TIMEOUT = 600        # Timeout total del agente (10 min)
```

### 3.4 Budget Enforcement

```python
@dataclass
class Budget:
    max_tokens: int = 500_000          # ~$0.50 en modelos baratos
    max_cost_usd: float = 2.0          # Limite duro en dolares
    max_iterations: int = 100          # Limite de iteraciones
    tokens_used: int = 0
    cost_usd: float = 0.0

    def track(self, usage: dict) -> None:
        """Update from OpenRouter usage response."""
        self.tokens_used += usage.get("total_tokens", 0)
        # Estimacion: $0.001 per 1K tokens (promedio modelos baratos)
        self.cost_usd += usage.get("total_tokens", 0) * 0.001 / 1000

    def exceeded(self) -> Optional[str]:
        if self.tokens_used > self.max_tokens:
            return f"Token limit exceeded: {self.tokens_used}/{self.max_tokens}"
        if self.cost_usd > self.max_cost_usd:
            return f"Cost limit exceeded: ${self.cost_usd:.4f}/${self.max_cost_usd}"
        return None
```

---

## 4. GESTION DE CONTEXTO

### Estrategia: Ventana deslizante con mensajes protegidos

```python
@dataclass
class ContextManager:
    max_history: int = 30          # Mensajes de interaccion max
    # Los 2 primeros mensajes (system + user/task) SIEMPRE se mantienen

    @staticmethod
    def trim(history: list, max_history: int = 30) -> list:
        """
        Mantiene:
        - history[0] = system prompt (siempre)
        - history[1] = user task (siempre)
        - Los ultimos max_history mensajes de interaccion

        Elimina los mas antiguos de interaccion (indice 2+)
        """
        if len(history) <= max_history + 2:
            return history

        protected = history[:2]
        interactions = history[2:]
        # Mantener solo los ultimos max_history
        trimmed = interactions[-(max_history):]
        return protected + trimmed
```

**Por que ventana deslizante y no sumarizacion:**
- Sumarizacion requiere llamada LLM extra (~$0.01-0.05 por sumarizacion)
- Sumarizacion pierde detalles de errores exactos (critico segun datos empiricos)
- Ventana de 30 mensajes cubre ~15 iteraciones completas (assistant+tool)
- Con modelos de 128K contexto, 30 mensajes rara vez exceden 40K tokens

**Por que NO comprimir errores:**
- Dato empirico: el error mas comun es mocking incorrecto (aiohttp.__aenter__)
- El modelo NECESITA ver el traceback exacto, no un resumen
- Truncar output largo (>10K chars) pero NUNCA resumir errores

---

## 5. CONDICIONES DE PARADA

```python
@dataclass
class StuckDetector:
    """Detecta 5 escenarios de bloqueo (basado en OpenHands, simplificado)."""
    action_history: List[str] = field(default_factory=list)    # "tool:args_hash"
    error_history: List[str] = field(default_factory=list)     # error messages
    no_tool_streak: int = 0                                     # monologue counter
    iteration: int = 0

    def record_action(self, tool_name: str, args: dict, result: str, is_error: bool):
        action_key = f"{tool_name}:{hash(json.dumps(args, sort_keys=True))}"
        self.action_history.append(action_key)
        if is_error:
            self.error_history.append(result[:200])  # first 200 chars
        else:
            self.error_history.clear()  # reset on success
        self.no_tool_streak = 0
        self.iteration += 1

    def record_no_tool(self):
        self.no_tool_streak += 1
        self.iteration += 1

    def check(self) -> Optional[str]:
        """Returns stop reason or None."""

        # 1. Accion repetida 4x consecutivas
        if len(self.action_history) >= 4:
            last4 = self.action_history[-4:]
            if len(set(last4)) == 1:
                return f"STUCK: Same action repeated 4x: {last4[0]}"

        # 2. Error repetido 3x consecutivas
        if len(self.error_history) >= 3:
            last3 = self.error_history[-3:]
            if len(set(last3)) == 1:
                return f"STUCK: Same error 3x: {last3[0][:100]}"

        # 3. Monologo: 3 respuestas sin tool call
        if self.no_tool_streak >= 3:
            return "STUCK: Model not calling tools (monologue 3x)"

        # 4. Tests pasan al 100% -> STOP (dato empirico: reviewers rompen codigo)
        # Esta condicion se chequea fuera del StuckDetector, en el loop principal

        return None

def should_stop(stuck: StuckDetector, budget: Budget, iteration: int,
                max_iterations: int, finished: bool) -> Optional[str]:
    """Master stop check. Returns reason string or None."""
    if finished:
        return "DONE"
    if iteration >= max_iterations:
        return f"MAX_ITERATIONS ({max_iterations})"

    budget_reason = budget.exceeded()
    if budget_reason:
        return budget_reason

    stuck_reason = stuck.check()
    if stuck_reason:
        return stuck_reason

    return None
```

**Dato empirico clave:** Si los tests pasan al 100%, el agente debe parar INMEDIATAMENTE. Los reviewers/optimizadores rompen codigo funcional. Implementar como condicion de parada explicita en el loop.

---

## 6. RECUPERACION DE ERRORES

### 6.1 Errores de herramientas -> Al modelo como observacion

```python
def execute_tool(tool_name: str, args: dict) -> Tuple[str, bool]:
    """Execute tool, return (result_string, is_error)."""
    if tool_name not in TOOL_DISPATCH:
        return f"ERROR: Unknown tool '{tool_name}'", True

    try:
        result = TOOL_DISPATCH[tool_name](args)
        is_error = result.startswith("ERROR:")
        return result, is_error
    except ValueError as e:
        return f"ERROR: {e}", True
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}", True
```

**Regla de oro:** NUNCA resumir errores. Pasar el error EXACTO del runtime al modelo. El modelo necesita ver el traceback completo para diagnosticar.

### 6.2 Errores de API (OpenRouter) -> Retry con backoff

```python
def call_model_with_retry(messages: list, model: str, api_key: str,
                          max_retries: int = 3) -> dict:
    """Call OpenRouter with exponential backoff. Returns parsed response."""
    for attempt in range(max_retries):
        try:
            response = _call_openrouter(messages, model, api_key)
            return response
        except (json.JSONDecodeError, KeyError, subprocess.TimeoutExpired) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"API failed after {max_retries} attempts: {e}")
            wait = 2 ** (attempt + 1)  # 2, 4, 8 seconds
            time.sleep(wait)
    raise RuntimeError("Unreachable")
```

### 6.3 Think tags y respuestas vacias

```python
def strip_think_tags(text: str) -> str:
    """Strip <think>...</think> tags. Critical for Step 3.5 Flash."""
    if text is None:
        return ""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def extract_response(api_response: dict) -> Tuple[Optional[str], Optional[list]]:
    """Extract content and tool_calls, handling think tags and empty responses."""
    msg = api_response["choices"][0]["message"]
    content = msg.get("content") or ""
    tool_calls = msg.get("tool_calls")

    # Strip think tags from content
    content = strip_think_tags(content)

    # If model put everything in reasoning field (no content, no tool_calls)
    if not content and not tool_calls:
        reasoning = msg.get("reasoning", "")
        if reasoning:
            # Model spent all tokens thinking. Return error observation.
            return "ERROR: Model produced no actionable output (reasoning only)", None

    return content, tool_calls
```

---

## 7. ESTRATEGIA MULTI-MODELO

### Principio: Modelo rapido para generar, modelo profundo para debugear

```python
@dataclass
class ModelRouter:
    """Selects model based on agent phase."""

    # Configuracion por defecto (OpenRouter model IDs)
    fast_model: str = "mistralai/devstral-2512"          # Genera codigo en 4-10s
    debug_model: str = "stepfun/step-3.5-flash"          # Debugea bien en 3 rounds
    fallback_model: str = "nvidia/llama-3.3-nemotron-super-49b-v1.5"

    # Estado
    _use_debug: bool = False
    _debug_rounds: int = 0
    _max_debug_rounds: int = 3   # Volver a fast despues de 3 rounds de debug

    def select(self) -> str:
        """Return model ID for current iteration."""
        if self._use_debug:
            self._debug_rounds += 1
            if self._debug_rounds > self._max_debug_rounds:
                self._use_debug = False
                self._debug_rounds = 0
                return self.fast_model
            return self.debug_model
        return self.fast_model

    def on_error(self) -> None:
        """Switch to debug model after tool error."""
        self._use_debug = True
        self._debug_rounds = 0

    def on_success(self) -> None:
        """After successful tool execution, stay on current or revert."""
        # Don't immediately revert - let debug_rounds counter handle it
        pass
```

**Logica:**
1. **Inicio:** Fast model (Devstral) genera codigo rapido (4-10s)
2. **Error detectado:** Switch a debug model (Step 3.5 Flash) por 3 iteraciones max
3. **Despues de 3 rounds debug:** Volver a fast model automaticamente
4. **Fallback:** Si fast o debug fallan (API error), usar fallback model

**Por que NO usar modelo diferente por herramienta:**
- Agrega complejidad sin beneficio (los modelos buenos generan tanto tool calls como codigo)
- El factor determinante no es la herramienta sino la FASE: generar vs corregir

**Por que Step 3.5 Flash para debug y no Opus/Sonnet:**
- Dato empirico: Step 3.5 Flash debugea bien en 3 rounds
- Mas barato que Opus/Sonnet
- Pero CUIDADO: puede gastar 16K tokens en think tags -> el agente DEBE stripear y detectar respuestas vacias

---

## 8. LOOP PRINCIPAL — IMPLEMENTACION

```python
def _call_openrouter(messages: list, model: str, api_key: str,
                     tools: list = TOOLS) -> dict:
    """Call OpenRouter API via subprocess + curl + tempfile."""
    body = {
        "model": model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": 4096,
        "temperature": 0.0
    }

    # Write body to tempfile (avoids shell escaping issues)
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(body, tmp)
    tmp.close()

    try:
        cmd = [
            'curl', '-s', '--max-time', str(MODEL_CALL_TIMEOUT),
            '-X', 'POST', 'https://openrouter.ai/api/v1/chat/completions',
            '-H', f'Authorization: Bearer {api_key}',
            '-H', 'Content-Type: application/json',
            '-H', 'HTTP-Referer: https://omni-mind.app',
            '-H', 'X-Title: OMNI-MIND Agent',
            '-d', '@' + tmp.name
        ]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=MODEL_CALL_TIMEOUT + 10)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed: {result.stderr}")

        data = json.loads(result.stdout)
        if "error" in data:
            raise RuntimeError(f"API error: {data['error']}")
        return data
    finally:
        os.unlink(tmp.name)


def run_agent(task: str, api_key: str,
              fast_model: str = "mistralai/devstral-2512",
              debug_model: str = "stepfun/step-3.5-flash",
              max_iterations: int = 100,
              sandbox_dir: str = SANDBOX_DIR) -> dict:
    """
    Main agent loop. Returns dict with result, iterations, cost, stop_reason.

    This is the entire agent in one function (~150 lines).
    """
    # Setup
    os.makedirs(sandbox_dir, exist_ok=True)

    router = ModelRouter(fast_model=fast_model, debug_model=debug_model)
    budget = Budget(max_iterations=max_iterations)
    stuck = StuckDetector()

    # System prompt
    system_msg = {
        "role": "system",
        "content": (
            "You are a coding agent. You have access to tools for reading, writing, "
            "and executing code in a sandboxed workspace.\n\n"
            "RULES:\n"
            "1. Always use tools to interact with the environment. Never guess file contents.\n"
            "2. After writing code, ALWAYS run tests to verify it works.\n"
            "3. If tests pass at 100%, call finish() immediately. Do NOT refactor working code.\n"
            "4. When you encounter an error, read the EXACT error message carefully.\n"
            "5. Use list_dir and search_files to explore before modifying.\n"
            "6. Call finish(result='description') when task is complete.\n"
        )
    }

    task_msg = {"role": "user", "content": f"TASK: {task}"}
    history = [system_msg, task_msg]

    # Main loop
    final_result = None
    stop_reason = None

    for iteration in range(max_iterations):
        # Check stop conditions
        stop_reason = should_stop(stuck, budget, iteration, max_iterations, False)
        if stop_reason:
            break

        # Select model
        model = router.select()

        # Call model
        try:
            api_response = call_model_with_retry(history, model, api_key)
        except RuntimeError as e:
            # API completely failed. Try fallback model once.
            try:
                api_response = call_model_with_retry(
                    history, router.fallback_model, api_key, max_retries=1)
            except RuntimeError:
                stop_reason = f"API_FAILURE: {e}"
                break

        # Track budget
        usage = api_response.get("usage", {})
        budget.track(usage)

        # Extract response
        content, tool_calls = extract_response(api_response)

        # Handle no tool calls (monologue or empty response)
        if not tool_calls:
            if content:
                history.append({"role": "assistant", "content": content})
            else:
                history.append({"role": "assistant", "content": "(empty response)"})
            stuck.record_no_tool()
            continue

        # Process first tool call
        tc = tool_calls[0]
        tool_name = tc["function"]["name"]
        try:
            tool_args = json.loads(tc["function"]["arguments"])
        except json.JSONDecodeError:
            tool_args = {}

        # Add assistant message with tool call to history
        history.append({
            "role": "assistant",
            "content": content,
            "tool_calls": [tc]
        })

        # Handle finish
        if tool_name == "finish":
            final_result = tool_args.get("result", "Task completed")
            # Add tool response to history
            history.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": final_result
            })
            stop_reason = "DONE"
            break

        # Execute tool
        result_str, is_error = execute_tool(tool_name, tool_args)

        # Add tool response to history
        history.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result_str
        })

        # Update stuck detector
        stuck.record_action(tool_name, tool_args, result_str, is_error)

        # Update model router
        if is_error:
            router.on_error()
        else:
            router.on_success()

        # Trim context if needed
        history = ContextManager.trim(history)

    # Final report
    return {
        "result": final_result,
        "stop_reason": stop_reason or "MAX_ITERATIONS",
        "iterations": stuck.iteration,
        "tokens_used": budget.tokens_used,
        "estimated_cost_usd": round(budget.cost_usd, 4),
        "model_switches": stuck.iteration  # approximate
    }
```

---

## 9. RESUMEN DE TAMANO Y ESTRUCTURA

```
agent.py (~400 lineas)
|
+-- Constants (10 lineas)
|     SANDBOX_DIR, MAX_FILE_SIZE, COMMAND_TIMEOUT, etc.
|
+-- TOOLS definition (80 lineas)
|     OpenAI function calling schema para las 6 herramientas
|
+-- Tool implementations (120 lineas)
|     _resolve_path, tool_read_file, tool_write_file,
|     tool_run_command, tool_list_dir, tool_search_files
|     TOOL_DISPATCH
|
+-- Security & Budget (30 lineas)
|     Budget dataclass
|
+-- Context management (15 lineas)
|     ContextManager.trim()
|
+-- Stuck detection (40 lineas)
|     StuckDetector, should_stop()
|
+-- Model interaction (50 lineas)
|     _call_openrouter, call_model_with_retry,
|     strip_think_tags, extract_response
|
+-- Model routing (25 lineas)
|     ModelRouter dataclass
|
+-- Main loop (80 lineas)
|     run_agent()
|
+-- CLI entrypoint (10 lineas)
|     if __name__ == "__main__": ...
|
TOTAL: ~460 lineas
```

---

## 10. DECISIONES CRITICAS BASADAS EN DATOS EMPIRICOS

| Dato empirico | Implicacion en el diseno | Alternativa descartada |
|---|---|---|
| Step 3.5 Flash gasta 16K tokens pensando sin output | `strip_think_tags()` + detectar `msg.content == None` + campo `reasoning` | Ignorar (perderia llamadas API enteras) |
| Reviewers rompen codigo funcional | Si tests 100% -> `finish()` inmediato. Regla en system prompt. | Permitir optimizacion post-tests (rompe cosas) |
| Error mas comun: mocking incorrecto | Pasar ERROR EXACTO al modelo (nunca resumir) | Resumir errores (pierde contexto critico) |
| Devstral genera en 4-10s, Step debugea en 3 rounds | ModelRouter con fast/debug switch | Modelo unico (suboptimo en ambas fases) |
| Context overflow con modelos think | Ventana deslizante de 30 mensajes + trim() | Sumarizacion LLM (costosa, pierde detalles) |

---

## 11. PROXIMO PASO: FASE 3 IMPLEMENTACION

1. Crear `/tmp/agent_sandbox/` y `agent.py` con todo el codigo de este documento
2. Test manual con tarea simple: "Create a Python function that computes fibonacci"
3. Test con tarea compleja: "Fix the failing test in test_router.py" (sobre el motor semantico)
4. Medir: latencia, tokens, iteraciones, costo, tasa de exito
5. Calibrar: MAX_ITERATIONS, COMMAND_TIMEOUT, max_history, debug_rounds

**Archivo unico:** `agent.py` — no hay razon para mas archivos con ~460 lineas.
