# AUDITORÍA FUNCIONAL DE MOTORES — OMNI-MIND

**Fecha:** 2026-03-20
**Briefing:** B-ACD-18
**Ejecutor:** Claude Code

---

## RESUMEN EJECUTIVO

| Motor | Estado | Veredicto |
|-------|--------|-----------|
| Motor vN (pipeline 7 capas + ACD) | **FUNCIONAL** | Importa OK. Requiere ANTHROPIC_API_KEY_* para smoke LLM. Funciona en fly.io. |
| Gestor — compilador | **FUNCIONAL** | `compilar_programa()` importa y acepta `ScoringMultiArquetipo`. |
| Gestor — loop lento | **NO EXISTE** | 5 archivos en `src/gestor/`, ningún endpoint de loop, sin análisis periódico. |
| Reactor v1 (sintéticos) | **FUNCIONAL** | 8/8 módulos importan (b1-b4, runner, config, validador, cartografia_loader). |
| Reactor v5/v5.2 (ACD) | **SOLO OUTPUTS** | 0 archivos de código. 19 archivos de salida en `results/reactor_v5/`. Son sesiones manuales, no código automatizado. |
| Reactor v4 (telemetría) | **NO EXISTE** | No hay código para generar preguntas desde datos reales. |
| Models C1-C4 | **STUB** | Imports fallan (no sklearn). Sin datos sintéticos. Sin modelos entrenados. |
| Code OS | **FUNCIONAL** | Montado en `/code-os/*`. 100+ rutas. Endpoint operativo. |

---

## DETALLE POR MOTOR

### 1. Motor vN — Pipeline 7 capas + ACD

**Estado: FUNCIONAL (en fly.io)**

- `run_pipeline(request)` importa correctamente
- Firma: `MotorRequest(input, contexto, config=MotorConfig(modo, profundidad, ...))`
- 7 capas: Detector → Router → Compositor → Generador → Ejecutor → Evaluador → Integrador
- ACD integrado: `_run_acd()` ejecuta diagnóstico + prescripción
- Gestor integrado: `compilar_programa()` compila por arquetipo
- Telemetría: log a DB + persistencia diagnóstico ACD
- Capa 7 (Registrador): datapoints de efectividad
- **Bloqueo local:** Sin `ANTHROPIC_API_KEY_*` en `.env` local. Solo tiene `OPENROUTER_API_KEY`.
- **En producción (fly.io):** Funcional con 4 API keys rotativas.

### 2. Gestor — Compilador

**Estado: FUNCIONAL**

- `compilar_programa(scoring, vector, modo, presupuesto_max, forzar_tier) → ProgramaCompilado`
- Archivos: `compilador.py`, `modelos.py`, `tier.py`, `programa.py`, `__init__.py`
- Recibe `ScoringMultiArquetipo` del detector TCF
- Output: `ProgramaCompilado` con tier, pasos, modelos, frenar, coste_estimado
- Integrado en orchestrator.py líneas 134-148

### 3. Gestor — Loop Lento

**Estado: NO EXISTE**

- No hay endpoint `/gestor/loop` ni similar
- No hay tarea periódica de análisis/poda/recompilación
- Solo compilación bajo demanda dentro del pipeline
- **Acción requerida:** Implementar si se quiere optimización continua de la Matriz

### 4. Reactor v1 (Sintéticos)

**Estado: FUNCIONAL**

- 8 módulos, todos importan sin error:
  - `b1_casos_dominio` — generación de casos por dominio
  - `b2_peticiones` — peticiones sintéticas
  - `b3_composicion` — composición de algoritmos
  - `b4_scoring` — scoring de resultados
  - `runner` — orquestador del reactor
  - `config` — configuración
  - `validador` — validación de outputs
  - `cartografia_loader` — carga de cartografía
- Endpoint: `POST /reactor/ejecutar`
- **No probado con LLM** (requiere API keys)

### 5. Reactor v5/v5.2 (ACD)

**Estado: SOLO OUTPUTS (sin código)**

- Directorio: `results/reactor_v5/` con 19 archivos de salida
- Son resultados de sesiones manuales/experimentales
- No hay `src/reactor_v5/` ni código automatizado
- **Acción requerida:** Codificar como pipeline si se quiere automatizar generación P/R/estados

### 6. Reactor v4 (Telemetría)

**Estado: NO EXISTE**

- No hay código para generar preguntas desde datos reales de ejecución
- La telemetría se guarda en `ejecuciones` (tabla DB) pero no se retroalimenta
- **Acción requerida:** Implementar feedback loop telemetría → preguntas

### 7. Models C1-C4

**Estado: STUB**

- Imports fallan: no hay `sklearn` instalado
- No hay datos sintéticos generados para entrenar
- No hay modelos entrenados/serializados
- Dependencia: Reactor v1 debe generar datos primero
- **Acción requerida:**
  1. Ejecutar Reactor v1 para generar datos
  2. `pip install scikit-learn`
  3. Entrenar C1-C4

### 8. Code OS

**Estado: FUNCIONAL**

- Montado en `/code-os/*` del servidor FastAPI
- 100+ rutas de agente autónomo
- Briefings B18-B26 ejecutados exitosamente
- Agente operativo en producción

---

## ENDPOINTS DISPONIBLES

| Endpoint | Motor | Estado |
|----------|-------|--------|
| `GET /health` | Sistema | OK |
| `POST /motor/ejecutar` | Motor vN | Funcional |
| `POST /reactor/ejecutar` | Reactor v1 | Funcional |
| `POST /models/entrenar` | Models | Stub |
| `/code-os/*` | Code OS | Funcional |

---

## PRIORIDADES POST-ACD (recomendación)

1. **Models C1-C4** — Desbloquear con `pip install scikit-learn` + ejecutar Reactor v1 para datos
2. **Gestor loop lento** — Optimización continua de la Matriz (análisis periódico, poda, recompilación)
3. **Reactor v5 como código** — Automatizar generación de datos P/R/estados (actualmente manual)
4. **Reactor v4 telemetría** — Feedback loop: datos reales → mejores preguntas

---

## HIPÓTESIS vs REALIDAD

| Motor | Hipótesis previa | Resultado real | Match |
|-------|------------------|----------------|-------|
| Motor vN | FUNCIONAL | FUNCIONAL | OK |
| Gestor compilador | FUNCIONAL | FUNCIONAL | OK |
| Gestor loop lento | NO EXISTE | NO EXISTE | OK |
| Reactor v1 | FUNCIONAL | FUNCIONAL | OK |
| Reactor v5 | NO EXISTE (solo outputs) | SOLO OUTPUTS | OK |
| Reactor v4 | NO EXISTE | NO EXISTE | OK |
| Models | PARCIAL | STUB | ~ (peor de lo esperado) |
| Code OS | FUNCIONAL | FUNCIONAL | OK |

**Coincidencia hipótesis:** 7/8 (87.5%). Models está peor de lo esperado (STUB, no PARCIAL).
