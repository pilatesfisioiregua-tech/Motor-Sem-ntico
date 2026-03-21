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
    "herramientas": (
        "CORE: read_file(path), edit_file(path, old, new), insert_at(path, line, code), "
        "write_file(path, content), list_dir(path), run_command(cmd), finish(result), mochila(seccion)\n"
        "EXTRA: db_query(sql), db_insert(sql), http_request(method, url), search_files(query)\n"
        "Rutas: @project/ = código real. Sin prefijo = sandbox."
    ),
    "reglas": (
        "1. Usa tools, no adivines. 2. Lee antes de editar. 3. Verifica tras escribir. "
        "4. edit_file para cambios puntuales. 5. @project/ siempre para código real. "
        "6. finish(result) con respuesta completa. 7. Español siempre."
    ),
    "errores": (
        "old_string NOT FOUND: lee el archivo primero, copia string exacto. "
        "ARCHIVO NO ENCONTRADO: usa @project/ prefix. "
        "LOOP: para y cambia de enfoque. "
        "BLOWUP: simplifica la petición."
    ),
    "proyecto": (
        "Stack: Python 3.12 / FastAPI / fly.io Postgres+pgvector / NetworkX\n"
        "Deploy: fly deploy -a chief-os-omni --remote-only\n"
        "Estructura: motor_v1_validation/agent/ (api.py, core/, tools/)"
    ),
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
