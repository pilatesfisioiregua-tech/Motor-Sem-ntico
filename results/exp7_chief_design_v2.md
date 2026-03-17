# CHIEF OF STAFF v2 — Diseno Consensuado

# **ESPECIFICACIÓN TÉCNICA: REDISEÑO DEL CHIEF OF STAFF (CoS) DE OMNI-MIND**
**Documento:** `COS-REDESIGN-V1.0`  
**Estado:** Especificación para Implementación  
**Objetivo:** Sistema de orquestación multi-modelo de baja latencia y costo, integrado en la arquitectura OMNI-MIND.

---

## **A. ARQUITECTURA GENERAL (Diagrama ASCII)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OMNI-MIND COGNITIVE CORE                            │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    MATRIZ COGNITIVA 3Lx7F (Memoria Semántica)       │  │
│  │  [L1: Hechos] [L2: Contexto] [L3: Metaconocimiento] × 7 Dominios     │  │
│  └───────────────┬───────────────────────────────────────────────┬───────┘  │
│                  │                                               │          │
│  ┌───────────────▼───────────────────────────────────────────────▼───────┐  │
│  │              CHIEF OF STAFF (CoS) - ORQUESTADOR PRINCIPAL           │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │ 1. DISPATCHER INTELIGENTE (Router + Cost/Latency Optimizer)   │ │  │
│  │  └───────────────┬───────────────────────────────────────────────┘ │  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 2. EVALUADOR DE RESPUESTA (Quality Gate)                     ││  │
│  │  │    - Modelo: anthropic/claude-3-haiku                       ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 3. PLANIFICADOR DE RAZONAMIENTO (Deep Thought Sequencer)    ││  │
│  │  │    - Modelo: openai/o1-mini                                 ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 4. MATRIZ COGNITIVA ADAPTER (3Lx7F Interface)               ││  │
│  │  │    - Embeddings: all-MiniLM-L6-v2                          ││  │
│  │  │    - Vector DB: pgvector (PostgreSQL)                       ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 5. AGENTE DE CODING (Specialized Executor)                  ││  │
│  │  │    - Modelo: qwen/qwen-2.5-coder-32b-instruct               ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 6. MONITOR DE RENDIMIENTO (Metrics Collector)               ││  │
│  │  │    - Modelo: google/gemini-flash-1.5-8b                     ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 7. OPTIMIZADOR DE CONFIGURACIÓN (Self-Improvement Engine)   ││  │
│  │  │    - Modelo: meta-llama/llama-3.2-3b-instruct               ││  │
│  │  └───────────────┬───────────────────────────────────────────────┘│  │
│  │                   │                                               │  │
│  │  ┌────────────────▼───────────────────────────────────────────────┐│  │
│  │  │ 8. LOGGER & TELEMETRÍA (Audit Trail)                        ││  │
│  │  └───────────────────────────────────────────────────────────────┘│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  COMUNICACIÓN INTERNA: Colas Redis (Pub/Sub) + gRPC para baja latencia      │
└──────────────────────────────────────────────────────────────────────────────┘

FLUJO DE DATOS:
[Usuario] → [Dispatcher] → { [Evaluador] | [Planificador] } → [Matriz Adapter]
     ↓
[Agente Coding] (si es requerido)
     ↓
[Evaluador] (validación final)
     ↓
[Logger] → [Monitor] → [Optimizador] (ciclo de mejora)
```

---

## **B. COMPONENTES (Máximo 8)**

### **1. DISPATCHER INTELIGENTE**
- **Responsabilidad:** Clasificar consulta (superficial/profunda), enrutar a modelo óptimo, optimizar costo/latencia en tiempo real.
- **Modelo Asignado:** `google/gemini-flash-1.5-8b` (para clasificación rápida y económica).
- **Herramientas:**
  - Clasificador de intención (fine-tuned mini-modelo local).
  - Tabla de costos latencia de modelos (cacheada en Redis).
  - Reglas de negocio (umbrales de complejidad).
- **Comunicación:** Recibe de `Logger`, envía a `Evaluador` o `Planificador`. Usa cola `dispatch_queue`.

### **2. EVALUADOR DE RESPUESTA**
- **Responsabilidad:** Validar calidad, seguridad y relevancia de respuestas superficiales. Puerta de calidad.
- **Modelo Asignado:** `anthropic/claude-3-haiku` (equilibrio velocidad/calidad).
- **Herramientas:**
  - Prompt de evaluación estructurada (escala 1-5 en 4 dimensiones).
  - Filtro de contenido (moderación integrada).
  - Comparación con historial (Matriz 3Lx7F).
- **Comunicación:** Recibe de `Dispatcher` o `Planificador`, envía respuesta final a `Logger` o reintenta con `Planificador`.

### **3. PLANIFICADOR DE RAZONAMIENTO**
- **Responsabilidad:** Descomponer problemas complejos, secuenciar modelos, sintetizar resultados finales.
- **Modelo Asignado:** `openai/o1-mini` (razonamiento profundo, <30s).
- **Herramientas:**
  - Prompt de planificación con pasos atómicos.
  - Gestor de estado de razonamiento (Redis).
  - Integración con `Matriz Adapter` para contexto.
- **Comunicación:** Recibe de `Dispatcher`, coordina llamadas a `Matriz Adapter` y `Agente Coding`, sintetiza para `Evaluador`.

### **4. MATRIZ COGNITIVA ADAPTER**
- **Responsabilidad:** Interface con Matriz 3Lx7F. Búsqueda semántica, actualización de capas, recuperación contextual.
- **Modelo Asignado:** *Ninguno* (componente de infraestructura). Usa `all-MiniLM-L6-v2` para embeddings.
- **Herramientas:**
  - pgvector (PostgreSQL + extensión vectorial).
  - Algoritmo de búsqueda híbrida (similitud coseno + filtros por dominio/capa).
  - Actualización incremental (solo L1/L2, L3 es read-only).
- **Comunicación:** Recibe consultas de `Planificador` y `Evaluador`, devuelve contexto en <200ms.

### **5. AGENTE DE CODING**
- **Responsabilidad:** Ejecutar tareas de programación, análisis de código, generación de scripts.
- **Modelo Asignado:** `qwen/qwen-2.5-coder-32b-instruct` (especializado, costo moderado).
- **Herramientas:**
  - Sandbox Docker aislado (ejecución segura).
  - Linter/static analyzer integrado.
  - Git integration (para commits automáticos si se aprueba).
- **Comunicación:** Invocado por `Planificador`, devuelve resultado a `Planificador`.

### **6. MONITOR DE RENDIMIENTO**
- **Responsabilidad:** Recopilar métricas en tiempo real (latencia, costo, calidad, errores).
- **Modelo Asignado:** `google/gemini-flash-1.5-8b` (para análisis ligero de métricas).
- **Herramientas:**
  - Prometheus + Grafana (métricas técnicas).
  - Log aggregation (ELK stack).
  - Alertas (umbrales de costo/latencia).
- **Comunicación:** Consume logs de `Logger`, alimenta a `Optimizador`.

### **7. OPTIMIZADOR DE CONFIGURACIÓN**
- **Responsabilidad:** Ajustar parámetros del sistema (modelos seleccionados, prompts, thresholds) basado en métricas.
- **Modelo Asignado:** `meta-llama/llama-3.2-3b-instruct` (ligero, para decisiones rápidas).
- **Herramientas:**
  - Algoritmo de refuerzo simple (multi-armed bandit).
  - A/B testing de configuraciones.
  - Rollback automático.
- **Comunicación:** Recibe datos de `Monitor`, actualiza tablas de configuración (Redis/DB).

### **8. LOGGER & TELEMETRÍA**
- **Responsabilidad:** Registrar todas las interacciones, trazas completas, auditoría.
- **Modelo Asignado:** *Ninguno* (componente de logging).
- **Herramientas:**
  - Structured logging (JSON).
  - Trace ID único por turno.
  - Almacenamiento en S3/DB (retención 90 días).
- **Comunicación:** Recibe de todos los componentes, alimenta a `Monitor`.

---

## **C. FLUJO DE UN TURNO DE CHAT (Superficial <1s)**

1. **T=0ms:** Usuario envía mensaje → `Dispatcher` (Gemini Flash).
2. **T=50ms:** `Dispatcher` clasifica como "superficial" (confianza >90%). Consulta tabla de costos/latencia.
3. **T=100ms:** `Dispatcher` enruta directamente a `Evaluador` (Claude Haiku) con contexto de Matriz (si aplica).
4. **T=300ms:** `Evaluador` genera respuesta, aplica filtro de calidad.
5. **T=500ms:** Si calidad >4/5 → respuesta a usuario. Si no, reintento (máximo 1 reintento).
6. **T=800ms:** Respuesta final enviada a usuario. `Logger` registra traza completa.
7. **T=900ms:** `Monitor` actualiza métricas (latencia, costo tokens).

**Costo estimado turno superficial:** ~500 tokens (Gemini Flash $0.0001/1k + Claude Haiku $0.00025/1k) = **$0.000000125** (despreciable).

---

## **D. FLUJO DE PENSAMIENTO PROFUNDO (<30s)**

1. **T=0ms:** Usuario envía consulta compleja → `Dispatcher` clasifica como "profundo".
2. **T=50ms:** `Dispatcher` enruta a `Planificador` (o1-mini).
3. **T=200ms:** `Planificador` descompone en 3-5 pasos atómicos. Ejemplo:
   - Paso 1: Recuperar contexto de Matriz 3Lx7F (vía `Matriz Adapter`).
   - Paso 2: Analizar con modelo especializado (si requiere coding → `Agente Coding`).
   - Paso 3: Sintetizar respuesta.
4. **T=500ms:** `Matriz Adapter` devuelve contexto relevante (200ms por búsqueda).
5. **T=1-20s:** `Planificador` ejecuta secuencia:
   - Si hay coding: `Agente Coding` (Qwen Coder) ejecuta en sandbox (5-10s).
   - Modelos intermedios (Gemini Flash para análisis) según plan.
6. **T=25s:** `Planificador` sintetiza resultado final.
7. **T=27s:** `Evaluador` (Claude Haiku) valida síntesis.
8. **T=29s:** Respuesta a usuario. `Logger` registra traza completa.
9. **T=30s:** Límite hard. Si no completa, `Evaluador` devuelve "en proceso" y notifica.

**Costo estimado turno profundo:** ~2000 tokens (o1-mini $0.005/1k + otros $0.0005) = **$0.0105**.

---

## **E. INTEGRACIÓN CON MOTOR COGNITIVO (Matriz 3Lx7F)**

- **Acceso:** Solo lectura para L2/L3. Escritura solo L1 (hechos nuevos) y L2 (contexto actualizado) desde `Planificador`.
- **Formato:** Cada celda [Lx][Fy] almacena:
  - Embedding vector (384 dimensiones).
  - Texto crudo (resumen).
  - Metadatos (timestamp, fuente, confianza).
- **Update policy:**
  - L1: Append-only (nuevos hechos).
  - L2: Merge por similitud (umbral 0.85).
  - L3: Solo lectura (knowledge base estable).
- **Query:** `Matriz Adapter` recibe (dominio, tipo consulta) → búsqueda híbrida → top-5 resultados → inyecta en prompt del modelo.

---

## **F. INTEGRACIÓN CON AGENTE DE CODING**

- **Trigger:** `Planificador` detecta intención de coding (palabras clave: "código", "script", "función", "ejecuta").
- **Workflow:**
  1. `Planificador` envía tarea a `Agente Coding` con especificaciones.
  2. `Agente Coding` genera código, lo ejecuta en sandbox Docker (timeout 10s).
  3. Captura stdout/stderr, código de salida.
  4. Devuelve resultado a `Planificador` para inclusión en respuesta.
- **Safety:** Sandbox sin red, límite de recursos (CPU/RAM), escaneo de malware básico.

---

## **G. SELF-IMPROVEMENT**

1. **Data Collection:** `Logger` → `Monitor` recolecta:
   - Latencia por componente.
   - Costo por turno (tokens * precio).
   - Score de calidad (feedback implícito: thumbs up/down, o evaluación humana).
   - Tasa de error/reintentos.
2. **Optimization Loop (cada 1h):**
   - `Optimizador` (Llama 3.2 3B) analiza métricas.
   - Ajusta:
     - Modelo por defecto para cada tipo de consulta (ej: si Gemini Flash tiene calidad <3.5, cambiar a Haiku).
     - Thresholds de clasificación (Dispatcher).
     - Número de pasos en razonamiento.
   - Prueba cambios en 1% del tráfico (A/B test).
   - Si métricas mejoran >5%, rollout global.
3. **Prompt Optimization:** `Optimizador` genera variaciones de prompts clave, valida con conjunto de validación.

---

## **H. ELIMINACIONES DEL CHIEF VIEJO (Y POR QUÉ)**

1. **Modelo único/grande para todo:** Eliminado. Costo prohibitivo (> $0.10/turno), latencia alta (>5s). Se reemplaza por orquestación especializada.
2. **Lógica de enrutamiento estática:** Eliminada. No se adapta a cambios de precios/performance. Se reemplaza por `Dispatcher` dinámico.
3. **Memoria de contexto simple (ventana):** Eliminada. No aprovecha conocimiento estructurado. Se reemplaza por Matriz 3Lx7F.
4. **Sin puerta de calidad:** Eliminado. Respuestas inconsistentes. Se añade `Evaluador`.
5. **Auto-mejora manual:** Eliminada. No escala. Se automatiza con `Monitor`+`Optimizador`.

---

## **I. CONSERVACIONES DEL CHIEF VIEJO (Y POR QUÉ)**

1. **Integración con Matriz 3Lx7F:** Se conserva y mejora. Es el núcleo de conocimiento de OMNI-MIND.
2. **Agente de Coding existente:** Se conserva pero se aísla como componente especializado. Ya funciona bien.
3. **Esquema de turnos (superficial/profundo):** Se conserva pero se formaliza con tiempos estrictos.
4. **Logging estructurado:** Se conserva y se extiende para auto-mejora.
5. **Arquitectura de microservicios:** Se conserva, pero se añaden colas Redis para desacoplo.

---

## **J. ESTIMACIÓN DE COSTE POR TURNO (Desglose)**

**Supuestos:**
- 70% turnos superficiales (promedio 500 tokens).
- 30% turnos profundos (promedio 2000 tokens).
- Precios OpenRouter (nov 2024):
  - Gemini Flash 1.5: $0.0001/1k tokens (entrada), $0.0002/1k (salida).
  - Claude Haiku: $0.00025/1k tokens.
  - o1-mini: $0.005/1k tokens.
  - Qwen Coder 32B: $0.0004/1k tokens.
  - Llama 3.2 3B: $0.00005/1k tokens.

**Cálculo por turno promedio:**
```
Tokens totales = (0.7 * 500) + (0.3 * 2000) = 350 + 600 = 950 tokens

Distribución por componente:
- Dispatcher (Gemini Flash): 50 tokens * $0.00015 = $0.0000075
- Evaluador (Claude Haiku): 150 tokens * $0.00025 = $0.0000375 (superficial) / 200 tokens * $0.00025 = $0.00005 (profundo)
- Planificador (o1-mini): 0 tokens (superficial) / 800 tokens * $0.005 = $0.004 (profundo)
- Matriz Adapter: 0 (infraestructura)
- Agente Coding (solo profundo): 500 tokens * $0.0004 = $0.0002
- Monitor/Optimizador: 20 tokens * $0.00005 = $0.000001

Costo superficial: $0.0000075 + $0.0000375 = $0.000045
Costo profundo: $0.0000075 + $0.00005 + $0.004 + $0.0002 + $0.000001 = $0.0042585

Costo promedio: (0.7 * $0.000045) + (0.3 * $0.0042585) = $0.0000315 + $0.00127755 = $0.00130905

REDONDEADO: ~$0.0013 por turno (< $0.02) ✅
```

---

## **K. ESQUEMA DE BASE DE DATOS**

### **Tablas Nuevas/Modificadas:**

```sql
-- 1. Configuración de Modelos (Redis cache + PostgreSQL backup)
CREATE TABLE model_config (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(100) UNIQUE,  -- ej: "google/gemini-flash-1.5-8b"
    purpose VARCHAR(50),  -- "dispatch", "evaluation", "reasoning", "coding"
    cost_per_1k_input FLOAT,
    cost_per_1k_output FLOAT,
    avg_latency_ms INT,
    quality_score FLOAT,  -- 1-5, actualizado por Optimizador
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP
);

-- 2. Matriz 3Lx7F (ya existe, pero se modifica para incluir embeddings)
CREATE TABLE cognitive_matrix (
    id SERIAL PRIMARY KEY,
    layer INT CHECK (layer BETWEEN 1 AND 3),  -- L1, L2, L3
    function INT CHECK (function BETWEEN 1 AND 7),  -- F1-F7
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- pgvector
    source VARCHAR(200),
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    -- Índices compuestos para búsqueda rápida
    INDEX idx_layer_function (layer, function)
);

-- 3. Turnos y Trazas (nueva)
CREATE TABLE turn_log (
    turn_id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    query_text TEXT,
    classification VARCHAR(20),  -- "superficial" o "profundo"
    dispatcher_model VARCHAR(100),
    total_tokens INT,
    total_cost_usd FLOAT,
    total_latency_ms INT,
    quality_score FLOAT,  -- del Evaluador
    completed BOOLEAN DEFAULT true
);

CREATE TABLE step_log (
    step_id UUID PRIMARY KEY,
    turn_id UUID REFERENCES turn_log(turn_id),
    step_order INT,
    component_name VARCHAR(50),  -- "Dispatcher", "Evaluador", etc.
    model_used VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    prompt_snippet TEXT,  -- primeros 500 chars
    response_snippet TEXT,
    FOREIGN KEY (turn_id) REFERENCES turn_log(turn_id) ON DELETE CASCADE
);

-- 4. Métricas de Rendimiento (nueva, para Monitor)
CREATE TABLE performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    component VARCHAR(50),
    avg_latency_ms FLOAT,
    error_rate FLOAT,
    throughput_per_min INT,
    cost_per_hour FLOAT
);

-- 5. Configuración Dinámica (para Optimizador)
CREATE TABLE dynamic_config (
    param_key VARCHAR(100) PRIMARY KEY,
    param_value JSONB,  -- puede ser número, string, objeto
    last_modified TIMESTAMP DEFAULT NOW(),
    modified_by VARCHAR(50)  -- "optimizer" o "admin"
);
```

### **Índices Adicionales:**
```sql
CREATE INDEX idx_turn_log_user_time ON turn_log(user_id, timestamp DESC);
CREATE INDEX idx_cognitive_matrix_embedding ON cognitive_matrix USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_step_log_turn ON step_log(turn_id);
```

---

## **VERIFICACIÓN DE REQUISITOS**

| Requisito | Cumple | Implementación |
|-----------|--------|----------------|
| Máx 8 componentes | ✅ | 8 componentes definidos (A-I). |
| <$0.02/turno | ✅ | $0.0013 promedio. |
| <1s superficie | ✅ | Flujo 800ms. |
| <30s profundo | ✅ | Flujo 29s + margen. |
| Multi-modelo OS | ✅ | 5 modelos diferentes, enrutados dinámicamente. |
| Integrado con Matriz 3Lx7F | ✅ | `Matriz Adapter` como componente. |
| Self-improving | ✅ | `Monitor` + `Optimizador` con A/B testing. |

---

## **IMPLEMENTACIÓN PRIORITARIA**

**Fase 1 (MVP - 2 semanas):**
1. Implementar `Dispatcher` + `Evaluador` (superficial).
2. Conectar con Matriz 3Lx7F existente (solo lectura).
3. Logging básico.

**Fase 2 (2 semanas):**
1. Añadir `Planificador` + `Agente Coding`.
2. Implementar flujo profundo completo.
3. Sandbox Docker para coding.

**Fase 3 (1 semana):**
1. `Monitor` + `Optimizador`.
2. A/B testing de modelos.
3. Dashboard de métricas.

**Fase 4 (1 semana):**
1. Pruebas de carga y estrés.
2. Ajuste fino de costos/latencia.
3. Documentación operacional.

---

**FIN DE LA ESPECIFICACIÓN.**  
*Este documento es la fuente única de verdad para el equipo de implementación. Cualquier desviación debe ser aprobada por el arquitecto senior.*