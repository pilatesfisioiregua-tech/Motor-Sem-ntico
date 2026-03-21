# PROMPT SIGUIENTE SESIÓN — Fase 2: Diagnóstico ACD

**Fecha:** 2026-03-19
**Sesión anterior:** Completó Fase 0 (Code OS rediseño) + Fase 1 parcial (datos P, R, estados, DB)
**Objetivo:** Escribir y ejecutar briefings B-ACD-05 a B-ACD-08

---

## ESTADO AL CERRAR

### Completados ✅
- B-ACD-00: Code OS rediseño (mochila 4 secciones, system prompt 311 chars, hard limit context)
- B-ACD-01: pensamientos.json (15 P) + load_pensamientos()
- B-ACD-02: razonamientos.json (12 R) + load_razonamientos()

### En vuelo / pendientes confirmación
- B-ACD-03: estados.json (10 estados) + flags.py (3 flags) + load_estados() — **verificar resultado**
- B-ACD-04: migración DB (014_acd_tables.sql, 4 tablas) — **briefing escrito, verificar si se ejecutó**

### Checklist maestra
- `motor-semantico/briefings/CHECKLIST_ACD.md` — leer primero, está actualizada

### Plan completo
- `docs/operativo/PLAN_IMPLEMENTACION_ACD.md` — secciones B-ACD-05 a B-ACD-08 tienen el diseño de alto nivel

---

## QUÉ HACER EN ESTA SESIÓN

### 1. Verificar estado de B-ACD-03 y B-ACD-04
```
Leer CHECKLIST_ACD.md → confirmar que Fase 1 está completa
Si algo falló → arreglar antes de continuar
```

### 2. Escribir briefings ejecutables de Fase 2 (Diagnóstico)

**B-ACD-05: Derivar vector funcional desde texto (LLM)**
- EL GAP MÁS CRÍTICO. Sin esto el pipeline ACD no arranca end-to-end.
- Crear `src/tcf/evaluador_funcional.py`
- Un LLM call que dado un caso (texto) produce 21 scores F×L → VectorFuncional
- Leer: `src/tcf/campo.py` (VectorFuncional), `src/tcf/constantes.py` (FUNCIONES, LENTES, VALORACION_F_L)
- Pass/fail: caso Pilates → vector cercano a VECTOR_PILATES de constantes.py

**B-ACD-06: Clasificador de 10 estados**
- Crear `src/tcf/diagnostico.py`
- Función `clasificar_estado(lentes) -> str` que clasifica en uno de los 10 estados
- Lógica: gap < 0.15 → E1-E4 por gradiente. gap ≥ 0.15 → 6 perfiles por distribución S/Se/C
- Integrar flags.py (de B-ACD-03)
- Leer: `src/tcf/estados.json` (umbrales), `src/tcf/flags.py`
- Pass/fail: 10 vectores canónicos → cada uno clasificado correctamente

**B-ACD-07: Inferir repertorio cognitivo INT×P×R**
- Crear `src/tcf/repertorio.py`
- LLM call que dado caso + vector → infiere INT/P/R activas/atrofiadas/ausentes
- Verificaciones post-LLM con leyes IC2-IC6 (código puro)
- Leer: `src/meta_red/inteligencias.json`, `pensamientos.json`, `razonamientos.json`
- Pass/fail: caso Pilates → detecta INT-10 activa, INT-12/INT-02 ausentes

**B-ACD-08: Diagnóstico completo end-to-end**
- Integrar P0→P4 en una función `diagnosticar(caso) -> DiagnosticoCompleto`
- Orquesta: evaluador_funcional → campo → clasificador → repertorio
- Pass/fail: caso Pilates end-to-end → diagnóstico con estado, flags, repertorio

### 3. Ejecutar briefings

Dependencias:
```
B-ACD-05 (vector) ──→ B-ACD-07 (repertorio, necesita vector)
B-ACD-06 (clasificador) ──→ B-ACD-08 (end-to-end, necesita todo)
```

Paralelismo posible: B-ACD-05 + B-ACD-06 en paralelo (WIP=2). Luego B-ACD-07. Luego B-ACD-08.

---

## ARCHIVOS CLAVE A LEER

**Para estado:**
- `motor-semantico/briefings/CHECKLIST_ACD.md`

**Para diseño de briefings:**
- `docs/operativo/PLAN_IMPLEMENTACION_ACD.md` (secciones B-ACD-05 a 08)

**Para escribir código:**
- `src/tcf/campo.py` — VectorFuncional, calcular_lentes(), evaluar_campo()
- `src/tcf/constantes.py` — FUNCIONES, LENTES, VALORACION_F_L, VECTOR_PILATES, UMBRAL_*
- `src/tcf/flags.py` — detectar_todos_flags() (creado en B-ACD-03)
- `src/tcf/estados.json` — 10 estados con umbrales (creado en B-ACD-03)
- `src/meta_red/__init__.py` — loaders de INT, P, R
- `src/config/settings.py` — MODEL_EXTRACTOR, MODEL_ROUTER
- `src/utils/llm_client.py` — cómo llamar al LLM

**NO leer en esta sesión (ya procesado):**
- MAESTRO_V4.md (2800 líneas, ya integrado)
- FRAMEWORK_ACD.md (ya procesado)
- taxonomia_pensamiento_razonamiento.md (ya convertido a JSON)
- agent_loop.py, mochila.py (ya rediseñados en B-ACD-00)

---

## DECISIÓN PENDIENTE CR1

B-ACD-05 (derivar vector) tiene dos opciones:
- **LLM:** más preciso, ~$0.01/caso. Un prompt con definiciones 7F×3L + caso → JSON 21 floats.
- **Heurístico:** más barato ($0), menos preciso. Mapeo keyword→función desde detector_huecos existente.

CR0 de sesión anterior propuso LLM con fallback heurístico. Confirmar.
