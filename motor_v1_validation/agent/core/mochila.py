"""Mochila — referencia estructurada accesible bajo demanda.

En vez de meter todo en el system prompt (Working Memory limitada a ~4 chunks),
la Mochila guarda toda la documentación organizada por secciones.
El agente consulta mochila("seccion") cuando necesita algo específico.

Patrones aplicados:
- Working Memory (83726): Solo 4 chunks en prompt activo
- Distributed Cognition (83722): Tools como artefactos cognitivos activos
- Attention Networks (83725): Atención selectiva por tarea
"""

SECTIONS = {
    "herramientas": """CATÁLOGO DE HERRAMIENTAS CODE OS v3 (63 tools)

FILESYSTEM: read_file(path), write_file(path, content), edit_file(path, old_string, new_string), list_dir(path)
  - SIEMPRE usa @project/ para archivos del proyecto
  - write_file crea archivos NUEVOS (sandbox o @project/)
  - edit_file modifica archivos existentes (reemplazo exacto)
  - read_file soporta offset/limit para archivos grandes

SEARCH: glob_files(pattern, path), grep_content(pattern, path), search_files(query)
  - Usa path='@project/' para buscar en el proyecto

SHELL: run_command(command, timeout)
  - Para pip install, pytest, deploy, etc.

GIT: git_status(), git_add(files), git_commit(message), git_diff(), git_log(), git_branch(name), git_push(), create_pr(title, body)

DATABASE: db_query(sql, params), db_insert(sql, params), analyze_schema(schema_name)
  - db_query: solo SELECT (read-only)
  - db_insert: INSERT/UPDATE/DELETE/CREATE/TRUNCATE (auto-commit)
  - Usa %s para parámetros, NO f-strings

KNOWLEDGE: remember(query, scope), remember_save(title, content, category)
  - Busca en knowledge_base (27K+ entries)
  - Scopes: patrones:maestro, patrones:software, repo, etc.

PATTERNS: search_patterns(query), search_concepts(query), pattern_algebra(id_a, id_b, op), explore_patterns(scope_a, scope_b)

GESTOR: analizar_gradientes(input), compilar_programa(input, consumidor)
  - Calcula campo de gradientes 3L×7F
  - Compila programa de preguntas desde la Matriz

WEB: web_search(query), web_fetch(url)
HTTP: http_request(method, url, headers, body)

TESTING: run_tests(path, framework), run_linter(path), check_coverage(path)
SECURITY: scan_secrets(path), scan_vulnerabilities(path), audit_deps(path)
ANALYSIS: analyze_codebase(path), dependency_graph(path), complexity_metrics(path)
REVIEW: review_code(path), suggest_improvements(path)
META: plan(action, content), finish(result), ask_user(question)
""",

    "reglas": """REGLAS OPERATIVAS CODE OS v3

1. SIEMPRE usa tools. Nunca adivines contenido de archivos.
2. PRIMERO entiende (read_file, grep, remember), LUEGO actúa (write_file, edit_file).
3. Tras escribir código, SIEMPRE verifica (run_tests, db_query, run_command).
4. VERIFICA EXHAUSTIVAMENTE antes de finish(). No terminar solo con leer o planificar.
5. Lee mensajes de error EXACTOS. Cambia de enfoque tras 3 errores iguales.
6. Usa edit_file para cambios puntuales, no reescribir archivos completos.
7. Código completo — sin placeholders ni TODOs.
8. Commit checkpoints tras progreso significativo.
9. SIEMPRE @project/ para archivos del proyecto. Sin prefijo = sandbox temporal.
10. Al terminar: RESUMEN FINAL al CEO con métricas antes de finish().
11. SIEMPRE responde en ESPAÑOL.
12. Si detectas un problema que PUEDES arreglar → ARRÉGLALO antes de reportar.
""",

    "rutas": """RUTAS DE ARCHIVOS — OBLIGATORIO

@project/ = archivos REALES del proyecto (código fuente, configs)
sin prefijo = sandbox temporal (scratch, borradores — SE PIERDE)

EJEMPLOS CORRECTOS:
  read_file(path='@project/src/main.py')           → lee del proyecto
  write_file(path='@project/core/nuevo.py', ...)    → CREA archivo nuevo en proyecto
  edit_file(path='@project/api.py', ...)             → edita archivo existente
  list_dir(path='@project/')                         → lista directorio proyecto
  glob_files(pattern='**/*.py', path='@project/')    → busca en proyecto

EJEMPLOS INCORRECTOS (sandbox, se pierde):
  write_file(path='core/nuevo.py', ...)              → ¡va al sandbox!
  edit_file(path='api.py', ...)                      → ¡busca en sandbox!

REGLA: Todo archivo de código del proyecto SIEMPRE con @project/
""",

    "proyecto": """PROYECTO OMNI-MIND — CONTEXTO

Stack: Python 3.12+ / FastAPI / fly.io Postgres (pgvector) / NetworkX
Deploy: fly deploy -a chief-os-omni --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile --remote-only
DB: postgresql://chief_os_omni:***@motor-semantico-db.flycast:5432/omni_mind

DEPLOY PROTOCOL:
  1. git_add + git_commit (cambios quirúrgicos)
  2. run_command("fly deploy -a chief-os-omni --remote-only") si flyctl disponible
  3. Fallback: git_push() → CI/CD despliega
  4. Verificar: http_request('GET', 'https://chief-os-omni.fly.dev/health')

ESTRUCTURA:
  motor_v1_validation/agent/
    api.py          — FastAPI endpoints (~40KB, usar offset/limit para leer)
    chat.py         — Chat engine con SSE streaming
    cli.py          — CLI interactivo terminal
    core/
      agent_loop.py — Loop principal observe-think-act
      router.py     — DualModelRouter cerebro/trabajador
      budget.py     — Control presupuesto
      context.py    — Compresión de contexto
      mochila.py    — Este archivo (referencia bajo demanda)
      telemetria.py — Métricas y señales del sistema nervioso
      gestor.py     — Gestor de la Matriz (gradientes + compilador)
      neural_db.py  — Búsqueda híbrida + Hebbian learning
      db_pool.py    — Pool de conexiones DB
    tools/          — 63 herramientas organizadas por categoría

SCHEMA (Maestro v3 §6.6): 42 tablas
  Clave: inteligencias(18), preguntas_matriz(597), knowledge_base(27K+),
  config_modelos(8), exocortex_estado(2: pilates, fisioterapia)
""",

    "briefing": """PROTOCOLO DE EJECUCIÓN DE BRIEFINGS

1. Lee el briefing COMPLETO para entender alcance total.
2. Para cada PASO:
   a. SQL → db_insert() o db_query(). NO solo mostrarlo.
   b. Archivos → write_file(path='@project/...') o edit_file(path='@project/...').
      SIEMPRE con @project/ — sin él va al sandbox temporal.
   c. Comandos → run_command(). NO solo listarlos.
   d. Tras cada paso → VERIFICAR (db_query, run_command, etc.)
   e. Si verificación falla → ARREGLAR antes de continuar.
3. Al terminar TODO:
   a. RESUMEN FINAL: qué se hizo, qué se verificó, métricas.
   b. finish()

NUNCA: Leer un briefing ≠ ejecutarlo. Describir ≠ hacer.
""",

    "errores": """ESTRATEGIAS DE RECUPERACIÓN DE ERRORES

TOOL NO ENCONTRADO:
  → Nombres son snake_case: read_file, write_file, edit_file, list_dir, db_query, http_request, finish

ARCHIVO NO ENCONTRADO:
  → ¿Usaste @project/? Sin él busca en sandbox
  → Verificar ruta con list_dir('@project/') o glob_files

old_string NOT FOUND en edit_file:
  → Leer el archivo primero: read_file('@project/...')
  → Copiar el string EXACTO (espacios, indentación)
  → Si el archivo es muy grande, usar offset/limit

DB ERROR:
  → Verificar nombre de tabla con analyze_schema()
  → Para % en SQL sin parámetros: no pasar params=[]
  → TRUNCATE está permitido, DROP está bloqueado

MODELO BLOWUP (respuesta vacía/infinita):
  → El router cambiará automáticamente de modelo
  → Si persiste: simplificar la petición, dividir en pasos

LOOP INFINITO (mismo error 3+ veces):
  → PARAR y cambiar de enfoque completamente
  → Usar plan() para reconsiderar la estrategia
  → Si es imposible, reportar al CEO con ask_user()
""",

    "modos": """MODOS DE OPERACIÓN CODE OS v3.2 (3 modos + detección automática)

QUICK (auto-detectado: typos, renames, fix import, preguntas triviales):
  - Modelo: worker_budget (MiMo v2 Flash, $0.28/M)
  - Max iteraciones: 10 | Timeout: 60s | Latencia: <30s
  - Council: NO | Swarm: NO
  - Herramientas: mínimas (remember, read_file, edit_file)
  - Comportamiento: respuesta directa, sin overhead

STANDARD (default: features, briefings, implementación):
  - Modelos: cerebro (Devstral) + worker (Step 3.5 Flash)
  - Max iteraciones: 80 | Timeout: 600s | Latencia: <300s
  - Council: SÍ (cerebro + worker + evaluador) | Swarm: NO
  - Herramientas: todas disponibles
  - Comportamiento: entiende → investiga → implementa → verifica → reporta

DEEP (auto-detectado: arquitectura, refactor completo, debugging, análisis profundo):
  - Modelos: cerebro + worker + evaluador (Cogito 671B)
  - Max iteraciones: 120 | Timeout: 900s | Latencia: <600s
  - Council: SÍ | Swarm: SÍ (3 exploradores: R1 + Qwen + Kimi)
  - Herramientas: todas + swarm_analyze
  - Comportamiento: investiga profundo → múltiples perspectivas → sintetiza

DETECCIÓN AUTOMÁTICA:
  Quick keywords: typo, rename, fix import, corrige, cambia nombre, simple, rápido
  Deep keywords: arquitectura, refactor completo, análisis profundo, debugging, por qué falla
  Default: standard

ROLES (4 consolidados — MAX ROI open-source March 2026):
  cerebro (Qwen3-Coder 480B): decide, orquesta, encadena — Agent RL, SOTA tool-use
  worker (MiniMax M2.5): genera código, arregla — 80.2% SWE-bench (#1 open-weight), menos iteraciones
  evaluador (GLM-5 744B): evalúa, juzga — #1 Arena rating (1451 ELO), mejor razonamiento
  swarm (DeepSeek V3.2): exploradores paralelos — volumen

FLYWHEEL: Cada sesión retroalimenta quality_score del modelo usado → mejora routing.
CACHE T0: Tareas repetidas se resuelven sin LLM ($0).
""",

    "autonomia": """DOCTRINA DE AUTONOMÍA — Code OS v3

1. DETECTA → ARREGLA:
   - Señal con resuelta=false → db_insert UPDATE para resolverla o crear la corrección
   - Endpoint devuelve error → edit_file(@project/...) para corregir código + deploy
   - Datos inconsistentes → db_insert para corregir registros
   - Si PUEDES arreglarlo → ARRÉGLALO. No describas lo que "se podría hacer".

2. LEE ANTES DE TOCAR:
   - SIEMPRE read_file() antes de edit_file()
   - SIEMPRE db_query() antes de db_insert()
   - SIEMPRE http_request(GET) antes de cambiar config
   - Cambios quirúrgicos, no reescrituras completas

3. ENCADENA:
   - Fix → Verificar (re-lee, re-ejecuta) → Buscar siguiente problema → Fix → ... → finish()
   - NO termines tras el primer fix. ¿Hay más? → sigue
   - finish() solo cuando TODO está verificado

4. APRENDE:
   - remember_save() tras cada hallazgo importante
   - remember_save() tras cada fix aplicado
   - Formato: título descriptivo, contenido con problema + solución, category="fix_log"

5. MODIFÍCATE:
   - Para bugs en tu propio código: edit_file(@project/...) + run_command('pytest') + git_commit
   - No pidas permiso para arreglar tu propio código

6. CRITERIO PROPIO:
   - No "se podría considerar..." → "ejecuto X porque Y"
   - No "aquí tienes el SQL" → ejecuta el SQL con db_insert()
   - No finish() sin verificar → re-lee, re-ejecuta, confirma

7. DEPLOY:
   - git_add + git_commit tras cambios
   - run_command("fly deploy -a chief-os-omni --remote-only") si flyctl disponible
   - Fallback: git_push() → CI/CD despliega
   - Verificar: http_request('GET', 'https://chief-os-omni.fly.dev/health')

ANTI-PATRONES (PROHIBIDOS):
  ✗ "Aquí tienes el SQL para ejecutar" → EJECUTA el SQL
  ✗ finish() sin verificar los arreglos → RE-LEE y RE-EJECUTA antes
  ✗ "Se podría considerar arreglar X" → ARRÉGLALO
  ✗ Reportar 5 problemas sin arreglar ninguno → ARREGLA los que puedas
  ✗ Leer un archivo y describir cambios → APLICA los cambios con edit_file
""",

    "sistema": """ESTADO DEL SISTEMA Y PROBLEMAS CONOCIDOS

DASHBOARD CEO: https://chief-os-omni.fly.dev/ceo
ENDPOINTS PARA VERIFICACIÓN (usa http_request a http://localhost:8080):
  /health, /criticality/temperatura, /criticality/avalanchas,
  /gestor/autopoiesis, /gestor/flywheel, /motor/señales,
  /metacognitive/kalman, /predictive/trayectoria,
  /game-theory/estado, /costes/resumen, /ceo/advisor,
  /watchdog/status, /propiocepcion, /senales

PROBLEMAS CONOCIDOS (no reportar como hallazgos nuevos):

1. TEMPERATURA vs AVALANCHAS inconsistencia:
   - Temperatura dice "orden_rigido" (T=0.2775) y Avalanchas dice "supercritico" (tau=0.84)
   - CAUSA RAÍZ: Todos los programas tienen tasa_cierre_media=1.0 de datos pre-calibración
   - SOLUCIÓN PENDIENTE: Reset tasa_cierre_media=NULL en programas_compilados
   - Cuando el Motor ejecute ciclos reales con datos frescos, ambas métricas se alinearán
   - NO es un bug de código, es calidad de datos legacy

2. SOC SUPERCRÍTICO (tau < 1.3):
   - Misma causa raíz que #1: datos pre-calibración con tasa=1.0
   - Se resolverá automáticamente cuando haya datos reales de ejecuciones

3. CHECKS DE AUTOPOIESIS con valor null (—):
   - check_gaps, check_tasa, check_datapoints pueden ser null
   - null = indeterminado (no hay datos recientes para comparar), NO es error
   - Es normal si el Motor no ha ejecutado en las últimas 24h

4. ACTIVIDAD 0 EN ÚLTIMAS 24h:
   - Si metricas=0 y datapoints=0, significa que el Motor no ha ejecutado recientemente
   - NO es un error del sistema, solo inactividad temporal
   - Acción: ejecutar POST /gestor/loop o POST /motor/ejecutar-vn

WATCHDOG: Sistema de auto-chequeo cada 10min.
  GET /watchdog/status → ver estado del watchdog
  POST /watchdog/check → forzar chequeo manual

Cuando diagnostiques, SIEMPRE distingue entre:
- Bugs reales (código roto, DB caída, endpoint 500)
- Problemas conocidos (listar como "conocido, pendiente de X")
- Estado normal (inactividad, datos insuficientes)
""",
}


# Rate limiter — max 3 calls per session
_call_count = 0
_MAX_MOCHILA_CALLS = 3

def reset_mochila():
    """Reset call counter (call at session start)."""
    global _call_count
    _call_count = 0

def consultar(seccion: str) -> str:
    global _call_count
    _call_count += 1
    if _call_count > _MAX_MOCHILA_CALLS:
        return ("LIMITE: Ya consultaste la mochila 3 veces. "
                "Tienes toda la info que necesitas. "
                "USA LAS HERRAMIENTAS DIRECTAMENTE: read_file, edit_file, list_dir, finish. "
                "NO llames mochila de nuevo.")

    seccion = seccion.strip().lower()
    if seccion in SECTIONS:
        return SECTIONS[seccion]
    matches = [k for k in SECTIONS if seccion in k]
    if len(matches) == 1:
        return SECTIONS[matches[0]]
    if matches:
        return f"Secciones: {', '.join(matches)}"
    return f"Seccion '{seccion}' no existe. Disponibles: {', '.join(SECTIONS.keys())}"
