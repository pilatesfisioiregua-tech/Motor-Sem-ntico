# MOTOR SEMÁNTICO OMNI-MIND — BRIEFINGS PARA CLAUDE CODE

## ORDEN DE EJECUCIÓN

```
1. CLAUDE.md              ← Copiar a raíz del proyecto. Es el contexto maestro.
2. BRIEFING_00_SCAFFOLD   ← Crear estructura, deps, Docker, fly.toml, settings, llm_client, main.py
3. BRIEFING_01_DATOS      ← Schema SQL (inteligencias + Marco Lingüístico), seed SQL, inteligencias.json, marco_linguistico.json, db client
4. BRIEFING_02_PIPELINE   ← Detector Huecos (Capa 0), Router (Sonnet), Compositor (NetworkX), Generador (templates)
5. BRIEFING_03_PIPELINE   ← Ejecutor (LLM calls), Evaluador (heurístico + falacias), Integrador (Sonnet), Orquestador (7 capas)
6. BRIEFING_04_DEPLOY     ← fly.io setup, secrets, deploy, tests E2E con 3 casos reales
```

## REGLAS PARA CODE

1. **Python 3.12+** con type hints obligatorios
2. **Cada briefing es autónomo** — no asumas que Code tiene contexto de briefings anteriores
3. **Verifica al final de cada briefing** — cada uno tiene sección VERIFICACIÓN con checks concretos
4. **No inventar** — las 18 inteligencias, sus preguntas y las aristas del grafo vienen del documento de cartografía. Copiar datos exactos, no improvisar.
5. **CLAUDE.md va a la raíz del repo** — Code lo lee al inicio de cada sesión

## DATO CRÍTICO

Las preguntas completas de las 18 inteligencias están en la sección 6 del PROMPT MVP (el documento que Jesús proporcionó). BRIEFING_01 referencia esto — Code debe copiar las preguntas LITERALES al crear inteligencias.json.

## FLUJO EN CODE

```bash
# Sesión 1: Scaffold
# Dar a Code: CLAUDE.md + BRIEFING_00_SCAFFOLD.md
# Resultado: proyecto inicializado

# Sesión 2: Datos
# Dar a Code: BRIEFING_01_DATOS.md + PROMPT MVP (para las preguntas de inteligencias)
# Resultado: DB schema (con Marco Lingüístico), seed, inteligencias.json, marco_linguistico.json

# Sesión 3: Pipeline compilación
# Dar a Code: BRIEFING_02_PIPELINE_1_3.md
# Resultado: detector_huecos.py, router.py, compositor.py, generador.py

# Sesión 4: Pipeline ejecución + orquestador
# Dar a Code: BRIEFING_03_PIPELINE_4_6.md
# Resultado: ejecutor.py, evaluador.py (con falacias), integrador.py, orchestrator.py (7 capas)

# Sesión 5: Deploy + tests
# Dar a Code: BRIEFING_04_DEPLOY_TESTS.md
# Resultado: motor corriendo en fly.io, tests pasando
```
