# BRIEFING_09: Fix Mochila Loop + System Prompt Simplification

## Diagnóstico

Devstral 2 entra en loop infinito llamando `mochila()` (343 iters en T1).
Causa raíz: cross-referencias entre secciones de mochila + system prompt indirecto.

Cadena causal:
1. System prompt: "Usa mochila("herramientas") para ver catálogo"
2. Modelo llama mochila("herramientas") → ve 63 tools
3. mochila("reglas") dice "Consulta mochila("autonomia")"
4. mochila("errores") dice "Verificar con mochila("herramientas")"
5. Loop: cada sección referencia otra → el modelo sigue consultando

## Solución: 3 cambios

### Paso 1: Rate limiter en mochila (core/mochila.py)

Añadir contador global. Después de 3 llamadas, retornar "Ya consultaste la mochila.
Usa las herramientas directamente para avanzar."

Al final de `mochila.py`, reemplazar la función `consultar`:

```python
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
```

### Paso 2: Eliminar cross-referencias en secciones de mochila

En `core/mochila.py`, editar las secciones para ELIMINAR todas las referencias a
"Consulta mochila(X)" dentro del contenido de las secciones:

- `reglas` línea 12: eliminar "Consulta mochila("autonomia")."
  Reemplazar por: "Si detectas un problema que PUEDES arreglar → ARRÉGLALO."
  
- `errores` sección TOOL NO ENCONTRADO: eliminar "→ Verificar nombre exacto con mochila("herramientas")"
  Reemplazar por: "→ Nombres son snake_case: read_file, write_file, edit_file, list_dir, db_query, http_request, finish"

### Paso 3: Simplificar system prompt (core/agent_loop.py)

Reemplazar CODE_OS_SYSTEM con versión directa que NO referencia mochila.
Inline las 3 cosas críticas: herramientas clave, @project/ paths, protocolo.

```python
CODE_OS_SYSTEM = """Eres Code OS — agente técnico de OMNI-MIND. SIEMPRE en ESPAÑOL.

HERRAMIENTAS CLAVE (usa directamente, sin consultar nada antes):
- read_file(path) — lee archivos. SIEMPRE @project/ para proyecto
- edit_file(path, old_string, new_string) — edita archivos existentes
- write_file(path, content) — crea archivos NUEVOS
- list_dir(path) — lista directorio
- run_command(command) — ejecuta shell
- db_query(sql) — consulta DB (solo SELECT)
- db_insert(sql) — modifica DB (INSERT/UPDATE/DELETE)
- http_request(method, url) — llamadas HTTP
- finish(result) — TERMINAR con resultado

RUTAS: @project/ = proyecto real. Sin prefijo = sandbox temporal (se pierde).

PROTOCOLO: Lee → Entiende → Arregla → Verifica → Siguiente → finish()
NO describas lo que "se podría hacer". HAZLO.

{context_section}
"""
```

### Paso 4: Reset mochila al inicio de cada sesión

En `core/agent_loop.py`, al inicio de `run_agent_loop()`, añadir:

```python
from core.mochila import reset_mochila
reset_mochila()
```

### Paso 5: Deploy + Re-test

```bash
fly deploy -a chief-os-omni
python3 briefings/test_validacion_modelos.py --output results/test_modelos_fix_mochila_b09.md
```

CRITERIO: Al menos 2/4 tests pasan. T4 (diagnóstico con HTTP) debería pasar dado que
ya hacía 13 HTTP calls — solo faltaba sintetizar los resultados.

## Notas

- El system prompt pasa de ~2000 chars a ~800 chars — menos tokens, más directo
- mochila sigue existiendo para casos edge, pero con rate limit de 3 calls
- Si 3/4+ pasan → stack validado (Devstral 2 + system prompt simplificado)
- Si 0-1/4 → siguiente investigación: reducir las 61 tool schemas a ~15 esenciales
