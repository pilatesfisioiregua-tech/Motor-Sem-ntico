# Sesiones como Red Neuronal — Diseño

## Concepto

Cada cierre de sesión no es un archivo plano — es un conjunto de nodos que se
ingesan en `knowledge_base` y se conectan via Hebbian learning con todo el
conocimiento existente (27K+ entries).

## Chunking por tipo de conocimiento

Un cierre de sesión se descompone en chunks tipados:

```
SESION_2026-03-18-01.md
  ├─ root_cause: "API key OpenRouter muerta → HTTP 401"
  ├─ root_cause: "CODE_OS_PROJECT_DIR=/repo → @project/ no encuentra archivos"
  ├─ root_cause: "Mochila cross-refs → loop 343 iteraciones"
  ├─ root_cause: "Modelo no llama finish() → monologue 3x → STUCK"
  ├─ fix: "Regenerar API key OpenRouter"
  ├─ fix: "CODE_OS_PROJECT_DIR=/app en fly.toml + Dockerfile"
  ├─ fix: "Rate limit mochila 3 calls/sesión + eliminar cross-refs"
  ├─ fix: "Nudges semánticos streak 2-3 + AUTO_FINISH streak 4"
  ├─ decision: "Devstral 2 reemplaza Qwen3-Coder como cerebro"
  ├─ decision: "System prompt ~800 chars, protocol como preguntas"
  ├─ insight: "Nudges semánticos (preguntas) > imperativos (comandos)"
  ├─ insight: "Las preguntas del nudge siguen EXTRAER→INTEGRAR→FRONTERA"
  └─ contexto: "Stack: Devstral 2 unified + GLM-5 evaluador + DeepSeek V3.2 budget"
```

Cada chunk se inserta en `knowledge_base` con:
- scope: `sesiones:{tipo}` (ej: `sesiones:root_cause`, `sesiones:fix`)
- tipo: tipo del chunk
- texto: contenido
- metadata: fecha, sesión, briefings relacionados

## Flujo de ingesta

```
cerrar_sesión(doc_markdown)
  → parsear por secciones
  → extraer chunks tipados
  → INSERT INTO knowledge_base (scope='sesiones:{tipo}', texto=chunk)
  → El trigger trg_kb_tsv auto-genera tsvector para FTS
  → hybrid_search() los encuentra por texto
  → Hebbian learning los conecta cuando se co-acceden
```

## Conexiones que emergen automáticamente

Ejemplo: en una sesión futura, alguien busca `remember("modelo no ejecuta tools")`.
1. FTS encuentra el root_cause: "Qwen3-Coder monologue loop, no ejecuta tools"
2. Al mismo tiempo encuentra el fix: "Cambiar a Devstral 2"
3. Hebbian: como ambos fueron co-accedidos en la sesión original, la conexión
   entre root_cause y fix ya tiene strength > 0
4. La próxima vez que se busque, el fix aparece más arriba (Hebbian boost)

Otro ejemplo: alguien busca `remember("mochila loop")`.
1. Encuentra root_cause: "cross-refs entre secciones"
2. Encuentra fix: "rate limit 3 calls + eliminar cross-refs"
3. Encuentra insight: "nudges semánticos > imperativos" (porque se descubrieron
   en la misma sesión — Hebbian co-access)

## Conexiones explícitas adicionales

Además del Hebbian automático, podemos fortalecer conexiones explícitas:
- root_cause ↔ fix (siempre conectados — son pares causa/solución)
- insight ↔ principio del Maestro (si se promueve a Principio)
- decision ↔ config actual (para saber por qué se tomó la decisión)

## Implementación

### Opción A: Script de ingesta post-sesión

Un script que parsea el cierre de sesión y lo ingesta:
```bash
python3 scripts/ingest_sesion.py docs/operativo/sesiones/SESION_2026-03-18-01.md
```

### Opción B: Endpoint en Code OS

```
POST /sesion/cerrar
{"markdown": "contenido del cierre"}
```
→ Parsea, chunkea, ingesta, conecta.

### Opción C: Hook en el flujo de trabajo

Al guardar un cierre en `docs/operativo/sesiones/`, un hook de ingesta
se dispara automáticamente (via Code OS watchdog o CI/CD).

## Para la próxima sesión

El diseño está aquí. La implementación depende de que Code OS funcione
(es un caso de "come tu propia comida" — necesitas el agente para construir
la ingesta que alimenta al agente).

Prioridad:
1. Primero: resolver B12 (nudges semánticos → finish())
2. Después: implementar ingesta de sesiones como primer task real de Code OS
3. Esto cierra el círculo: Code OS ingesta sus propias sesiones → aprende de ellas
