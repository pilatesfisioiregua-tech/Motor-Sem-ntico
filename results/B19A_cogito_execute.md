# B19A — Cogito-671b como cerebro_execute

**Fecha**: 2026-03-18
**Modelo**: `deepcogito/cogito-v2.1-671b` ($5/M output)
**Objetivo**: Verificar si Cogito-671b sigue instrucciones de edición de código (edit_file) en exec_mode=execute

## Resultado: FAIL

| Métrica | Valor |
|---------|-------|
| Test | T3 Execute (crear endpoint GET /test/ping) |
| Resultado | FAIL |
| Iteraciones | 14 |
| Tiempo | 25.2s |
| Errores | 2 |
| edit_file calls | 0 |
| Total tool calls | 14 |

## Tools llamados

```
mochila, http_request, http_request, http_request, db_query, run_command, db_query, db_query, db_query, run_command
```

## Diagnóstico

Cogito-671b exhibe el **mismo patrón que Devstral 2**: alucina tool calls fuera del schema definido (especialmente `db_query` que NO está en las 8 tools filtradas). Nunca intenta `edit_file` para modificar código.

Tools disponibles en el schema: `read_file, write_file, edit_file, list_dir, run_command, finish, mochila, http_request`
Tools que el modelo llamó fuera del schema: `db_query` (4 veces)

## Conclusión

Cogito-671b **NO** es una mejora sobre Devstral 2 para el caso de uso execute. El problema no es de capacidad de razonamiento sino de **adherencia al schema de tools** — ambos modelos inventan tools que no existen en el schema proporcionado.

**Siguiente paso**: Probar un modelo con mejor tool-following (Claude Sonnet, GPT-4o, o similar) o reforzar el system prompt con instrucciones explícitas de "SOLO usa estas tools".

## Rollback

Revertido `cerebro_execute` a `mistralai/devstral-2512` y redesplegado.
