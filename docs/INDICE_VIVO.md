# INDICE VIVO — motor-semantico/

> Auto-mantenido por Opus Chat y Claude Code
> Ultima actualizacion: 2026-03-20 (B-ACD-16 en ejecucion; B-ACD-17 migracion DB V4; B-ACD-18 auditoria motores)
> Protocolo: Cada vez que se cree, mueva o elimine un archivo → actualizar este indice

---

## 0. DOCUMENTACION FUERA DE motor-semantico/

Los documentos de L0, producto, sistema, codigo OS y biblioteca viven en la raiz del repo:
- `/Users/jesusfernandezdominguez/omni-mind-cerebro/docs/`
- Ver `INDICE_VIVO.md` en raiz del repo para mapa completo
- Este indice cubre SOLO el contenido dentro de `motor-semantico/`

---

## COMO USAR ESTE INDICE

1. **Buscar contexto**: Ctrl+F por tema, inteligencia (INT-XX), o concepto
2. **Navegar**: Las rutas son relativas a `motor-semantico/`
3. **Ruta absoluta**: `/Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/`

---

## 1. DOCUMENTO CANONICO (fuente de verdad)

| Archivo | Descripcion |
|---------|-------------|
| `docs/activo/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v3.md` | Maestro v3 — documento canonico del sistema cognitivo completo (2199 lineas) |

---

## 2. ARQUITECTURA DEL MOTOR — Pipeline 7 capas

| Archivo | Capa | Funcion |
|---------|------|---------|
| `src/pipeline/detector_huecos.py` | 0 | Deteccion de huecos sintacticos ($0, codigo puro) |
| `src/pipeline/router.py` | 1 | Seleccion de inteligencias via LLM |
| `src/pipeline/compositor.py` | 2 | Grafo + algoritmo optimo (NetworkX) |
| `src/pipeline/generador.py` | 3 | Genera prompts desde Meta-Red templates |
| `src/pipeline/ejecutor.py` | 4 | Ejecuta prompts via Anthropic API |
| `src/pipeline/evaluador.py` | 5 | Scorer heuristico + deteccion falacias |
| `src/pipeline/integrador.py` | 6 | Sintesis final |
| `src/pipeline/orchestrator.py` | — | Orquesta las 7 capas |

---

## 2b. MODULO TCF — Teoria del Campo Funcional (19-mar-2026)

Implementa las 14 leyes + 5 teoremas de la TCF como codigo ejecutable. Modulo independiente que el pipeline consume.

| Archivo | Contenido |
|---------|-----------|
| `src/tcf/__init__.py` | Loaders: load_estados() (singleton) |
| `src/tcf/constantes.py` | 15 tablas numericas: INT×F (126 celdas), INT×L (54 celdas), 11 dependencias, valoracion F→L, 12 arquetipos canonicos, firmas linguisticas, 11 recetas, umbrales, vector Pilates validado |
| `src/tcf/campo.py` | VectorFuncional, EstadoCampo, evaluar_campo(). Implementa Leyes 1-4, 8-11, Axioma 5 |
| `src/tcf/arquetipos.py` | scoring_multi_arquetipo() (distancia euclidea a 12 arquetipos), pre_screening_linguistico() (regex firmas → candidatos) |
| `src/tcf/recetas.py` | generar_receta_mixta() (mezcla por scoring §6.2), aplicar_regla_14() (FRENAR Ley 13), secuencia_universal() (Teorema 2) |
| `src/tcf/lentes.py` | ecuacion_transferencia(), predecir_impacto(), es_equilibrio_nash(), perfiles de lente (8 combinaciones) |
| `src/tcf/detector_tcf.py` | detectar_tcf() (Fase A: pre-screening + Fase B: campo completo), enriquecer_detector_result() |
| `src/tcf/estados.json` | **19-mar** — 10 estados diagnosticos (4 eq E1-E4 + 6 deseq) con umbrales, transiciones, prescripciones P/R |
| `src/tcf/flags.py` | **19-mar** — 3 flags de peligro oculto: automata_oculto, monopolio_se, zona_toxica |

### Archivos por crear (Fase 2 ACD, en progreso 20-mar):

| Archivo | Briefing | Contenido | Estado |
|---------|----------|-----------|--------|
| `src/utils/openrouter_client.py` | B-ACD-05 paso 0 | Cliente OpenRouter async con json_schema + Response Healing | ✅ creado |
| `src/tcf/evaluador_funcional.py` | B-ACD-05 | V3.2 via OpenRouter → 21 scores F×L → VectorFuncional | ✅ creado |
| `src/tcf/diagnostico.py` | B-ACD-06 + B-ACD-08 | clasificar_estado() + DiagnosticoCompleto + diagnosticar() e2e | en progreso |
| `src/tcf/repertorio.py` | B-ACD-07 | V3.2 via OpenRouter → RepertorioCognitivo (INT×P×R) + IC | en progreso |

### Archivos por crear (Fase 3 ACD, briefings escritos 20-mar):

| Archivo | Briefing | Contenido |
|---------|----------|-----------|
| `src/tcf/nivel_logico.py` | B-ACD-10 | Mapeo lente faltante → nivel logico + modos conceptuales ($0) |
| `src/tcf/prescriptor.py` | B-ACD-09 | Prescripcion completa INT×P×R + secuencia + modos ($0) |

### Archivos por crear (Fase 5 ACD, briefings escritos 20-mar):

| Archivo | Briefing | Contenido |
|---------|----------|-----------|
| `src/tcf/evaluador_acd.py` | B-ACD-14 + B-ACD-15 | MetricasACD + DecisionTernaria ($0) |

### Relacion con docs L0 (fuentes):

| Archivo codigo | Doc fuente |
|---------------|------------|
| `constantes.py` | RESULTADO_CALCULOS_ANALITICOS_v1.md (Calculos 1-5) |
| `campo.py` | TEORIA_CAMPO_FUNCIONAL.md (14 leyes) |
| `lentes.py` | TEORIA_JUEGOS_LENTES.md (coaliciones, transferencia) |
| `arquetipos.py` | VALIDACION_TCF_CASO_PILATES.md (scoring multi-arquetipo §6.1) |
| `recetas.py` | RESULTADO_CALCULOS_ANALITICOS_v1.md (11 recetas + mezcla §6.2) |

### Estado de integracion con pipeline:

- **Pendiente:** BRIEFING_TCF_06 — integrar en detector_huecos.py, router.py, orchestrator.py

---

## 2c. REGLAS DEL COMPILADOR

| Archivo | Contenido |
|---------|-----------|
| `src/config/reglas.py` | 14 reglas como funciones verificables |

---

## 3. META-RED — 18 Inteligencias + P + R

| Archivo | Contenido |
|---------|-----------|
| `src/meta_red/inteligencias.json` | 18 redes de preguntas (38 KB) |
| `src/meta_red/marco_linguistico.json` | Marco linguistico: 8 ops, 9 capas, 6 acoples, falacias |
| `src/meta_red/pensamientos.json` | **19-mar** — 15 tipos de pensamiento P01-P15 |
| `src/meta_red/razonamientos.json` | **19-mar** — 12 tipos de razonamiento R01-R12 |
| `src/meta_red/__init__.py` | Loaders singleton: load_inteligencias(), load_marco_linguistico(), load_pensamientos(), load_razonamientos() |
| `PROMPT_MVP.md` | Definiciones completas de las 18 inteligencias |

---

## 4. CODE OS — Agente Autonomo (motor_v1_validation/agent/)

### Core

| Archivo | Funcion |
|---------|---------|
| `motor_v1_validation/agent/core/agent_loop.py` | Loop principal observe-think-act |
| `motor_v1_validation/agent/core/router.py` | DualModelRouter cerebro/trabajador |
| `motor_v1_validation/agent/core/api.py` | Cliente API OpenRouter + Anthropic |
| `motor_v1_validation/agent/core/intent.py` | Traductor de intenciones ($0, sin LLM) |
| `motor_v1_validation/agent/core/mochila.py` | Referencia estructurada bajo demanda |
| `motor_v1_validation/agent/core/gestor.py` | Gestor de la Matriz (gradientes + compilador) |
| `motor_v1_validation/agent/core/neural_db.py` | Busqueda hibrida + Hebbian learning |
| `motor_v1_validation/agent/core/budget.py` | Control de presupuesto |
| `motor_v1_validation/agent/core/context.py` | Compresion de contexto |
| `motor_v1_validation/agent/core/telemetria.py` | Metricas y senales |

### Interfaces

| Archivo | Funcion |
|---------|---------|
| `motor_v1_validation/agent/api.py` | FastAPI endpoints (~40KB) incluyendo CEO Dashboard |
| `motor_v1_validation/agent/chat.py` | Chat engine con SSE streaming |
| `motor_v1_validation/agent/cli.py` | CLI interactivo terminal |

### Tools (63 herramientas)

| Directorio | Categorias |
|------------|------------|
| `motor_v1_validation/agent/tools/` | filesystem, database, git, http, analysis, profiling, docker, algebra, remember, search, etc. |

---

## 5. CONFIGURACION Y DEPLOY

| Archivo | Funcion |
|---------|---------|
| `Dockerfile` | Imagen Docker para fly.io |
| `fly.toml` | Configuracion fly.io |
| `requirements.txt` | Dependencias Python |
| `src/config/settings.py` | Variables de entorno |
| `src/config/modelos.py` | Configuracion LLM |
| `src/db/schema.sql` | Schema PostgreSQL |
| `src/db/seed.sql` | Datos iniciales |
| `src/db/client.py` | Pool asyncpg |
| `CLAUDE.md` | Instrucciones para Claude Code |

---

## 6. DOCUMENTACION

### Activo
- `docs/activo/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v3.md` — Maestro v3

### Historico (superado, solo referencia)
- `docs/historico/` — Maestro v1, v2, Diseno v1, v2

### Satelite (integrado en Maestro v3)
- `docs/satelite/` — 5 archivos de actualizaciones integradas

### Operativo
- `docs/operativo/CHECKLIST_MOTOR_SEMANTICO.md`
- `docs/INDICE_VIVO.md` — **Este archivo** (auto-mantenido)

---

## 7. BRIEFINGS

### Motor original (B00-B18)

| Archivo | Fase |
|---------|------|
| `briefings/BRIEFING_00_SCAFFOLD.md` a `BRIEFING_18_diag_runtime.md` | Scaffold, pipeline, deploy, debugging, TCF |
| `briefings/BRIEFING_TCF_TEST.md` | **19-mar** — pytest TCF 4 suites |
| `briefings/BRIEFING_TCF_06.md` | **19-mar** — Integrar TCF en pipeline |

### Implementacion ACD (B-ACD-00 a B-ACD-15)

Checklist maestra: `briefings/CHECKLIST_ACD.md`
Plan completo: `docs/operativo/PLAN_IMPLEMENTACION_ACD.md`

| Archivo | Fase | Estado |
|---------|------|--------|
| `briefings/B-ACD-00.md` | 0: Code OS rediseno | PASS 5/5 |
| `briefings/B-ACD-01.md` | 1: pensamientos.json | PASS 3/3 |
| `briefings/B-ACD-02.md` | 1: razonamientos.json | PASS 3/3 |
| `briefings/B-ACD-03.md` | 1: estados.json + flags | PASS |
| `briefings/B-ACD-04.md` | 1: migracion DB | PASS |
| `briefings/B-ACD-05.md` | 2: evaluador funcional (V3.2 via OpenRouter) | **20-mar** escrito |
| `briefings/B-ACD-06.md` | 2: clasificador 10 estados | **20-mar** escrito |
| `briefings/B-ACD-07.md` | 2: repertorio INT×P×R (V3.2 via OpenRouter) | **20-mar** escrito |
| `briefings/B-ACD-08.md` | 2: diagnostico end-to-end | **20-mar** PASS 6/6 |
| `briefings/B-ACD-09.md` | 3: prescriptor INT×P×R ($0) | **20-mar** PASS 10/10 |
| `briefings/B-ACD-10.md` | 3: nivel logico → modo ($0) | **20-mar** PASS 5/5 |
| `briefings/B-ACD-11.md` | 3: prohibiciones formales ($0) | **20-mar** PASS 8/8 |
| `briefings/B-ACD-12.md` | 4: P/R en generador ($0) | **20-mar** escrito |
| `briefings/B-ACD-13.md` | 4: ACD en orchestrator (~$0.005) | **20-mar** escrito |
| `briefings/B-ACD-14.md` | 5: metricas ACD evaluador ($0) | **20-mar** escrito |
| `briefings/B-ACD-15.md` | 5: decision ternaria ($0) | **20-mar** PASS 8/8 |
| `briefings/B-ACD-16.md` | 6: deploy + persistencia + test e2e | **20-mar** en ejecucion |
| `briefings/B-ACD-17.md` | 7: migracion DB → Maestro V4 ($0) | **20-mar** escrito |
| `briefings/B-ACD-18.md` | 8: auditoria funcional motores (~$0.02) | **20-mar** escrito |
| `briefings/PROMPT_NEXT_SESSION_POST_B17_B18.md` | — prompt siguiente sesion | **20-mar** |
| `briefings/B-ACD-19.md` | 9: consolidado post-ACD (deploy+models+gestor+reactores) | **20-mar** escrito |

---

## 8-11. EXPERIMENTOS, TESTS, DATOS, OTROS

(Ver secciones detalladas en versiones anteriores del indice)

| Seccion | Resumen |
|---------|---------|
| 8. Experimentos | Exp 1bis-11.1, test modelos B07-B16 |
| 9. Tests | 4 suites pipeline + 4 suites TCF (41 tests) |
| 10. Datos | exp_p33, reactor_v5 (50 pares TCF + 7F×3L), sinteticos |
| 11. Otros | chief-os-chat, gmail_cleanup, scripts, reactor |

---

## PROTOCOLO DE ACTUALIZACION

Cada vez que se cree, mueva, renombre o elimine un archivo relevante:
1. Anadir/actualizar la entrada correspondiente
2. Actualizar la fecha "Ultima actualizacion" en la cabecera
3. Si es un nuevo directorio/categoria → crear nueva seccion
