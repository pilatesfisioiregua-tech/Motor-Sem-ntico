# BRIEFING_18 — Diagnóstico runtime: logging de exec_mode + tool_schemas

## Contexto

B17: 3/4. T3 llama `db_query` que NO está en MODE_TOOLS["execute"]. Dos hipótesis:
1. Safety net se activa (algún nombre en CORE_TOOLS no matchea el registry → <3 schemas → 61 tools)
2. Deploy no incluyó changes o detect_mode no clasifica T3 como "execute"

No más adivinanzas. Añadir logging al runtime y leer los logs.

## Qué hacer

### Paso 1 — Añadir logging diagnóstico en agent_loop.py

Archivo: `motor_v1_validation/agent/core/agent_loop.py`

Inmediatamente después del bloque de tool filtering (después de `if len(tool_schemas) < 3`), añadir:

**BUSCAR** (el bloque que termina con el safety net):
```python
    # Fallback: si el filtro dejó <3 tools, usar todo (safety net)
    if len(tool_schemas) < 3:
        tool_schemas = registry.get_schemas()
```

**AÑADIR JUSTO DESPUÉS:**
```python
    # === DIAGNOSTIC LOGGING (B18) — eliminar cuando T3 pase ===
    _filtered_names = [s["function"]["name"] for s in tool_schemas]
    print(f"[DIAG:B18] exec_mode={exec_mode} | goal_start='{goal[:60]}' | "
          f"tools_count={len(tool_schemas)} | "
          f"tools={_filtered_names[:15]} | "
          f"safety_net={'YES' if len(tool_schemas) > len(active_tools) + 5 else 'NO'}")
    # === END DIAGNOSTIC ===
```

### Paso 2 — Verificar que finish NO está en el registry

Antes de deploy, verificar si `finish` está registrado como tool:

```bash
# Buscar si finish se registra como tool
grep -r "register.*finish" motor-semantico/motor_v1_validation/agent/tools/
```

Si `finish` NO está registrado en el registry, entonces `CORE_TOOLS` pide un schema que no existe. `get_schemas(names=active_tools)` lo ignora silenciosamente — devuelve schemas solo para los que existen. Si varios nombres no matchean, podría caer bajo 3.

**Si finish no está registrado:** Quitarlo de CORE_TOOLS:
```python
    CORE_TOOLS = {
        "read_file", "edit_file", "write_file", "list_dir",
        "run_command", "mochila",
        # "finish" NO está en el registry — se maneja en el agent loop directamente
    }
```

### Paso 3 — Deploy y test SOLO T3

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro
fly deploy --config motor-semantico/motor_v1_validation/agent/fly.toml \
           --dockerfile motor-semantico/motor_v1_validation/agent/Dockerfile

# Solo T3 para ver el log de diagnóstico
python3 motor-semantico/briefings/test_validacion_modelos.py \
    --test 3 \
    --output motor-semantico/results/test_modelos_diag_b18.md
```

### Paso 4 — Leer logs de fly.io

```bash
fly logs -a chief-os-omni | grep "DIAG:B18"
```

Esto nos dirá exactamente: qué modo se detectó, cuántos tools se filtraron, y si el safety net se activó.

### Paso 5 — Si el diagnóstico muestra safety_net=YES

El safety net se activa porque CORE_TOOLS tiene nombres que no están en el registry. Fix: alinear CORE_TOOLS con los nombres reales del registry.

Para saber los nombres exactos:
```bash
curl -s https://chief-os-omni.fly.dev/health | python3 -c "import sys,json; print(json.load(sys.stdin))"
```

Y si hay un endpoint que lista tools:
```bash
curl -s https://chief-os-omni.fly.dev/tools 2>/dev/null || echo "No /tools endpoint"
```

### Paso 6 — Según resultado del diagnóstico

**Si exec_mode=analyze**: detect_mode fix no se deployó. Redesplegar.
**Si exec_mode=execute + safety_net=YES**: Nombres en CORE_TOOLS no matchean registry. Alinear y redesplegar.
**Si exec_mode=execute + safety_net=NO + db_query en tools**: Algo más raro. El registry devuelve tools que no están en el set pedido (bug en get_schemas).

## Criterio

No hay pass/fail para este briefing. Es diagnóstico. El output es el log `[DIAG:B18]` que nos dice exactamente qué está mal.

## Notas

- El test flag `--test 3` ejecuta solo T3 (más rápido, más barato).
- Los logs de fly.io se ven con `fly logs`. El print() del agent_loop va a stdout que fly.io captura.
- Una vez diagnosticado, el fix es trivial y se puede hacer en el mismo deploy.
