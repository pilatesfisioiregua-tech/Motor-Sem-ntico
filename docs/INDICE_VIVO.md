# INDICE VIVO — motor-semantico/

> Auto-mantenido por Opus Chat y Claude Code
> Ultima actualizacion: 2026-03-17
> Protocolo: Cada vez que se cree, mueva o elimine un archivo → actualizar este indice

---

## CÓMO USAR ESTE ÍNDICE

1. **Buscar contexto**: Ctrl+F por tema, inteligencia (INT-XX), o concepto
2. **Navegar**: Las rutas son relativas a `motor-semantico/`
3. **Ruta absoluta**: `/Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/`

---

## 1. DOCUMENTO CANÓNICO (fuente de verdad)

| Archivo | Descripcion |
|---------|-------------|
| `docs/activo/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v3.md` | Maestro v3 — documento canónico del sistema cognitivo completo (2199 lineas) |

---

## 2. ARQUITECTURA DEL MOTOR — Pipeline 7 capas

| Archivo | Capa | Funcion |
|---------|------|---------|
| `src/pipeline/detector_huecos.py` | 0 | Detección de huecos sintácticos ($0, código puro) |
| `src/pipeline/router.py` | 1 | Selección de inteligencias via LLM |
| `src/pipeline/compositor.py` | 2 | Grafo + algoritmo óptimo (NetworkX) |
| `src/pipeline/generador.py` | 3 | Genera prompts desde Meta-Red templates |
| `src/pipeline/ejecutor.py` | 4 | Ejecuta prompts via Anthropic API |
| `src/pipeline/evaluador.py` | 5 | Scorer heurístico + detección falacias |
| `src/pipeline/integrador.py` | 6 | Síntesis final |
| `src/pipeline/orchestrator.py` | — | Orquesta las 7 capas |

---

## 3. META-RED — 18 Inteligencias

| Archivo | Contenido |
|---------|-----------|
| `src/meta_red/inteligencias.json` | 18 redes de preguntas (38 KB) |
| `src/meta_red/marco_linguistico.json` | Marco lingüístico: 8 ops, 9 capas, 6 acoples, falacias |
| `PROMPT_MVP.md` | Definiciones completas de las 18 inteligencias |

---

## 4. CODE OS — Agente Autónomo (motor_v1_validation/agent/)

### Core

| Archivo | Funcion |
|---------|---------|
| `motor_v1_validation/agent/core/agent_loop.py` | Loop principal observe-think-act |
| `motor_v1_validation/agent/core/router.py` | DualModelRouter cerebro/trabajador |
| `motor_v1_validation/agent/core/api.py` | Cliente API OpenRouter + Anthropic |
| `motor_v1_validation/agent/core/intent.py` | Traductor de intenciones ($0, sin LLM) |
| `motor_v1_validation/agent/core/mochila.py` | Referencia estructurada bajo demanda |
| `motor_v1_validation/agent/core/gestor.py` | Gestor de la Matriz (gradientes + compilador) |
| `motor_v1_validation/agent/core/neural_db.py` | Búsqueda híbrida + Hebbian learning |
| `motor_v1_validation/agent/core/budget.py` | Control de presupuesto |
| `motor_v1_validation/agent/core/context.py` | Compresión de contexto |
| `motor_v1_validation/agent/core/telemetria.py` | Métricas y señales |
| `motor_v1_validation/agent/core/criticality_engine.py` | Motor SOC (Self-Organized Criticality) |
| `motor_v1_validation/agent/core/metacognitive.py` | Filtro Kalman metacognitivo |
| `motor_v1_validation/agent/core/predictive_controller.py` | Control predictivo |
| `motor_v1_validation/agent/core/game_theory.py` | Equilibrios Nash multi-modelo |
| `motor_v1_validation/agent/core/model_observatory.py` | Registro de modelos DB-driven |
| `motor_v1_validation/agent/core/watchdog.py` | Auto-chequeo cada 10min |
| `motor_v1_validation/agent/core/safety.py` | Guardrails de seguridad |

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

## 5. CONFIGURACIÓN Y DEPLOY

| Archivo | Funcion |
|---------|---------|
| `Dockerfile` | Imagen Docker para fly.io |
| `fly.toml` | Configuración fly.io |
| `requirements.txt` | Dependencias Python |
| `src/config/settings.py` | Variables de entorno |
| `src/config/modelos.py` | Configuración LLM |
| `src/config/reglas.py` | 13 reglas del compilador |
| `src/db/schema.sql` | Schema PostgreSQL |
| `src/db/seed.sql` | Datos iniciales |
| `src/db/client.py` | Pool asyncpg |
| `CLAUDE.md` | Instrucciones para Claude Code |

---

## 6. DOCUMENTACIÓN

### Activo
- `docs/activo/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v3.md` — Maestro v3

### Histórico (superado, solo referencia)
- `docs/historico/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md` — Maestro v2
- `docs/historico/SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO.md` — Maestro v1
- `docs/historico/DISENO_MOTOR_SEMANTICO_OMNI_MIND_v1.md` — Diseño v1
- `docs/historico/DISENO_MOTOR_SEMANTICO_OMNI_MIND_v2.md` — Diseño v2

### Satélite (integrado en Maestro v3)
- `docs/satelite/ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md`
- `docs/satelite/ACTUALIZACION_MAESTRO_PRINCIPIO_32_RED_NEURONAL.md`
- `docs/satelite/ACTUALIZACION_MAESTRO_SESION_11_MAR.md`
- `docs/satelite/ARQUITECTURA_MECANISMOS_MULTI_MODELO.md`
- `docs/satelite/MAPA_MODELOS_OS_OMNI_MIND_MAR2026.md`

### Cartografía Meta-Red (proyecto activo)
- `docs/activo/cartografia/` — Directorio para documentos del proyecto Cartografía Meta-Red v1

### Operativo
- `docs/operativo/CHECKLIST_MOTOR_SEMANTICO.md`
- `docs/INDICE.md` — Índice estático de los 110 .md (2026-03-12)
- `docs/INDICE_VIVO.md` — **Este archivo** (auto-mantenido)
- `.claude-project-instructions.md` — Instrucciones del proyecto para Claude Desktop

---

## 7. BRIEFINGS

| Archivo | Fase |
|---------|------|
| `briefings/BRIEFING_00_SCAFFOLD.md` | Estructura, deps, Docker |
| `briefings/BRIEFING_01_DATOS.md` | Schema SQL, seed, inteligencias.json |
| `briefings/BRIEFING_02_PIPELINE_1_3.md` | Detector, Router, Compositor, Generador |
| `briefings/BRIEFING_03_PIPELINE_4_6.md` | Ejecutor, Evaluador, Integrador |
| `briefings/BRIEFING_04_DEPLOY_TESTS.md` | Deploy fly.io, tests E2E |

---

## 8. EXPERIMENTOS

| Exp | Tema | Reporte principal |
|-----|------|-------------------|
| 1bis | Validación inicial | `results/exp1bis_report.md` |
| 2 | Enjambre evaluadores | `motor_v1_validation/results/exp2_enjambre_evaluadores_report.md` |
| 4 | Mesa redonda Chief of Staff | `results/exp4/` (4 sub-reports) |
| 5 | Assembly line | `motor_v1_validation/results/exp5_report.md` |
| 5b | Validación ampliada | `results/exp5b_report.md` |
| 6 | Diseño agente | `motor_v1_validation/results/exp6_report.md` |
| 7 | Rediseño Chief OS | `results/exp7_report.md` + R1/R2 por modelo |
| 8 | Motor Semántico v2 | `results/exp8_report.md` + R1/R2 por modelo |
| 9 | Roadmap y priorización | `results/exp9_report.md` + R1/R2 por modelo |
| 10 | Roadmap OS | `results/exp10/exp10_synthesis.md` + R1/R2 por modelo |

---

## 9. TESTS

| Archivo | Cobertura |
|---------|-----------|
| `tests/test_detector.py` | Capa 0: detección de huecos |
| `tests/test_router.py` | Capa 1: routing inteligencias |
| `tests/test_compositor.py` | Capa 2: composición grafos |
| `tests/test_pipeline_e2e.py` | End-to-end pipeline |

---

## 10. DATOS Y RESULTADOS

| Directorio | Contenido |
|------------|-----------|
| `datos/exp_p33/` | 6 casos input + resultados + evaluaciones P33 |
| `results/` | Reportes y respuestas de modelos (exp1bis-exp10) |
| `context/` | Contextos de entrada para experimentos (exp7-exp9) |
| `data/sinteticos/` | Datos sintéticos |

---

## 11. OTROS

| Directorio | Contenido |
|------------|-----------|
| `chief-os-chat/` | App web Chief OS Chat (FastAPI + HTML) |
| `gmail_cleanup/` | Limpieza semántica de email/Drive/iCloud |
| `scripts/` | Scripts de utilidad (seed_db, evaluador P33, fixes) |
| `registros/` | Logs de ejecución de briefings y fixes |
| `src/reactor/` | Implementación alternativa B1-B4 |
| `src/models/` | Modelos ML/scoring (clasificador, embeddings, trainer) |

---

## PROTOCOLO DE ACTUALIZACIÓN

Cada vez que se cree, mueva, renombre o elimine un archivo relevante:

1. Añadir/actualizar la entrada correspondiente en la sección adecuada
2. Actualizar la fecha "Ultima actualizacion" en la cabecera
3. Si es un nuevo directorio/categoría → crear nueva sección

Esto aplica tanto a Opus Chat como a Claude Code.
