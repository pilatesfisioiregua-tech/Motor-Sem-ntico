# Spec de Implementacion — Chief of Staff v2

# **ESPECIFICACIÓN TÉCNICA IMPLEMENTABLE - CHIEF OF STAFF (CoS) OMNI-MIND**

## **INFRAESTRUCTURA BASE**
- **Runtime**: Python 3.11 + FastAPI (Fly.io, mismo cluster que Motor Semántico)
- **Base de datos**: PostgreSQL 15 (Fly.io, misma instancia que Motor Semántico)
  - Extensión `pgvector` instalada
- **LLM Gateway**: OpenRouter (API key en secrets)
- **Conexión Agente Coding**: gRPC (mismo VPC)
- **Interfaz Chat**: Extensión de Open WebUI existente
- **Comunicación interna**: Redis Pub/Sub (Fly.io Redis)

```python
# Ejemplo de estructura de proyecto
cos_omnimind/
├── app/
│   ├── core/               # Componentes principales
│   │   ├── dispatcher.py
│   │   ├── evaluator.py
│   │   └── ...             # otros componentes
│   ├── models/             # Modelos DB
│   ├── schemas/            # Pydantic models
│   ├── services/           # Servicios compartidos
│   │   ├── llm_service.py  # Wrapper OpenRouter
│   │   └── redis_service.py
│   └── main.py             # FastAPI app
├── scripts/
│   ├── db_migrations/      # Alembic migrations
│   └── sandbox/            # Docker sandbox para coding
└── tests/
```

## **COMPONENTES DETALLADOS**

### **1. DISPATCHER INTELIGENTE**
**Responsabilidad**: Clasificar consultas y enrutar a componentes óptimos basado en costo/latencia

**Input/Output**:
```typescript
// Input
interface DispatcherInput {
  query: string;                   // Texto de consulta usuario
  user_id: string;                 // Identificador usuario
  chat_history: Array<Message>;    // Últimos 3 mensajes
}

// Output
interface DispatcherOutput {
  classification: "superficial" | "profundo";
  target_component: "evaluator" | "planner";
  recommended_model: string;       // model_id OpenRouter
  cost_estimate: number;           // USD estimado
  latency_estimate: number;        // ms estimados
}
```

**Modelo**: `google/gemini-flash-1.5-8b` (model_id: `google/gemini-flash-1.5`)

**Herramientas**:
- `get_cost_table()`: Consulta Redis con precios actualizados
- `classify_intent(query)`: Mini-modelo local (ONNX) para clasificación rápida

**Comunicación**:
- **Direct Call**: POST `/dispatch` (FastAPI endpoint)
- **Async**: Publica a `dispatch_result` (Redis Pub/Sub)

**Código/LLM**:
- Clasificador local (costo $0)
- LLM solo para casos ambiguos (5% de tráfico)

**Tablas BD**:
```sql
CREATE TABLE dispatch_rules (
    id SERIAL PRIMARY KEY,
    intent_pattern VARCHAR(100),   -- Regex o keyword
    classification VARCHAR(20),   -- "superficial"|"profundo"
    model_id VARCHAR(100),         -- Modelo recomendado
    priority INT DEFAULT 0,
    updated_at TIMESTAMP
);
```

**Estimación**:
- Latencia: 50-100ms
- Costo: $0.000015 por llamada (10 tokens input/5 output)

---

### **2. EVALUADOR DE RESPUESTA**
**Responsabilidad**: Validar calidad y seguridad de respuestas

**Input/Output**:
```typescript
// Input
interface EvaluatorInput {
  response: string;               // Respuesta a evaluar
  context: {                      // Contexto de Matriz 3Lx7F
    facts: string[];
    context: string[];
  };
  query: string;                  // Consulta original
}

// Output
interface EvaluatorOutput {
  score: number;                  // 1-5
  flags: string[];                // Ej: ["off-topic", "unsafe"]
  improved_response?: string;     // Respuesta mejorada (opcional)
}
```

**Modelo**: `anthropic/claude-3-haiku` (model_id: `anthropic/claude-3-haiku`)

**Herramientas**:
- `moderate_content(text)`: Llama a API de moderación
- `get_similar_responses(query)`: Consulta Matriz 3Lx7F

**Comunicación**:
- **Direct Call**: POST `/evaluate`
- **Stigmergy**: Campos en Redis:
  - `eval:last_score`: Último score dado
  - `eval:avg_score`: Promedio móvil (ventana 100)

**Código/LLM**:
- 100% LLM (no hay lógica offline)

**Tablas BD**: Usa `turn_log` para registrar evaluaciones

**Estimación**:
- Latencia: 200-300ms
- Costo: $0.00025 por llamada (150 tokens avg)

---

### **3. PLANIFICADOR DE RAZONAMIENTO**
**Responsabilidad**: Descomponer problemas complejos y orquestar soluciones

**Input/Output**:
```typescript
// Input
interface PlannerInput {
  query: string;
  context: MatrixContext;    // Contexto de Matriz 3Lx7F
  user_capabilities: {       // Habilidades del usuario
    technical_level: number;
  };
}

// Output
interface PlannerOutput {
  steps: Array<{
    order: number;
    component: string;      // "matriz_adapter"|"coding_agent"|...
    action: string;
    expected_output: string;
  }>;
  estimated_duration: number; // ms total estimado
}
```

**Modelo**: `openai/o1-mini` (model_id: `openai/o1-mini`)

**Herramientas**:
- `decompose_problem(query)`: LLM con prompt estructurado
- `optimize_plan(steps)`: Algoritmo local para reordenar pasos

**Comunicación**:
- **Colas**: Consume de `planner_queue`
- **gRPC**: Para llamar a Agente Coding

**Código/LLM**:
- 70% LLM (planificación inicial)
- 30% código (optimización)

**Tablas BD**:
```sql
CREATE TABLE reasoning_plans (
    id UUID PRIMARY KEY,
    turn_id UUID REFERENCES turn_log(turn_id),
    steps JSONB,             // Pasos generados
    executed_at TIMESTAMP,
    execution_time_ms INT
);
```

**Estimación**:
- Latencia: 500-1000ms
- Costo: $0.005 por llamada (1000 tokens avg)

---

### **4. MATRIZ COGNITIVA ADAPTER**
**Responsabilidad**: Interfaz con Matriz 3Lx7F para búsquedas semánticas

**Input/Output**:
```typescript
// Input
interface MatrixQuery {
  query: string;
  layers: number[];         // [1] o [1,2] o [2,3] etc
  domains: number[];        // [1-7]
  limit: number;            // Máx resultados (default 3)
}

// Output
interface MatrixResult {
  results: Array<{
    text: string;
    layer: number;
    domain: number;
    similarity: number;     // 0-1
  }>;
}
```

**Modelo**: `all-MiniLM-L6-v2` (embeddings, offline)

**Herramientas**:
- `generate_embedding(text)`: Modelo local
- `hybrid_search(query, filters)`: SQL + pgvector

**Comunicación**:
- **Direct Call**: POST `/matrix/query`
- **Stigmergy**: 
  - `matrix:cache_hits`: Estadísticas de caché
  - `matrix:avg_latency`: Promedio móvil

**Código/LLM**:
- 100% código (no usa LLM)

**Tablas BD**: 
```sql
-- Extensión de tabla existente cognitive_matrix
ALTER TABLE cognitive_matrix ADD COLUMN embedding vector(384);
CREATE INDEX idx_matrix_embedding ON cognitive_matrix USING ivfflat (embedding);
```

**Estimación**:
- Latencia: 100-200ms (con caché)
- Costo: $0 (solo infra)

---

### **5. AGENTE DE CODING**
**Responsabilidad**: Ejecutar tareas de programación en ambiente seguro

**Input/Output**:
```typescript
// Input
interface CodingTask {
  instruction: string;
  context: {
    files?: Array<{         // Archivos de contexto
      name: string;
      content: string;
    }>;
    technologies: string[];  // Ej: ["python", "sql"]
  };
  constraints: {
    timeout: number;        // segundos (default 10)
    memory: number;         // MB (default 512)
  };
}

// Output
interface CodingResult {
  success: boolean;
  output: string;
  error?: string;
  artifacts?: Array<{       // Archivos generados
    name: string;
    content: string;
  }>;
}
```

**Modelo**: `qwen/qwen-2.5-coder-32b-instruct` (model_id: `qwen/qwen-2.5-coder-32b-instruct`)

**Herramientas**:
- `execute_in_sandbox(code)`: Docker API
- `analyze_code(code)`: Linter integrado

**Comunicación**:
- **gRPC**: Servicio `coding.CoderService`
- **Stigmergy**: 
  - `coding:last_used`: Timestamp
  - `coding:success_rate`: Tasa éxito

**Código/LLM**:
- 50% LLM (generación código)
- 50% código (ejecución)

**Tablas BD**:
```sql
CREATE TABLE coding_sessions (
    id UUID PRIMARY KEY,
    turn_id UUID REFERENCES turn_log(turn_id),
    instruction TEXT,
    output TEXT,
    error TEXT,
    duration_ms INT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Estimación**:
- Latencia: 5-10s (depende de complejidad)
- Costo: $0.0004 por llamada (500 tokens avg)

---

## **ESQUEMA SQL COMPLETO**

```sql
-- Tablas principales (nuevas)
CREATE TABLE cos_components (
    component_id VARCHAR(50) PRIMARY KEY,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    last_updated TIMESTAMP
);

CREATE TABLE model_config (
    model_id VARCHAR(100) PRIMARY KEY,
    provider VARCHAR(50),
    cost_input_usd_per_1k FLOAT,
    cost_output_usd_per_1k FLOAT,
    avg_latency_ms INT,
    context_window INT,
    last_updated TIMESTAMP
);

CREATE TABLE turn_log (
    turn_id UUID PRIMARY KEY,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT NOW(),
    query_text TEXT,
    classification VARCHAR(20),
    total_tokens INT,
    total_cost_usd FLOAT,
    total_latency_ms INT,
    quality_score FLOAT,
    completed BOOLEAN DEFAULT true
);

CREATE TABLE step_log (
    step_id UUID PRIMARY KEY,
    turn_id UUID REFERENCES turn_log(turn_id),
    component_id VARCHAR(50) REFERENCES cos_components(component_id),
    step_order INT,
    model_id VARCHAR(100),
    input_tokens INT,
    output_tokens INT,
    latency_ms INT,
    prompt_snippet TEXT,
    response_snippet TEXT
);

-- Tablas para Matriz 3Lx7F (modificaciones)
ALTER TABLE cognitive_matrix ADD COLUMN embedding vector(384);
CREATE INDEX idx_cm_embedding ON cognitive_matrix USING ivfflat (embedding);

-- Tablas para optimización
CREATE TABLE performance_metrics (
    metric_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    component_id VARCHAR(50) REFERENCES cos_components(component_id),
    metric_name VARCHAR(50),
    metric_value FLOAT,
    window_size INT  -- en minutos
);

CREATE TABLE dynamic_config (
    param_key VARCHAR(100) PRIMARY KEY,
    param_value JSONB,
    last_modified TIMESTAMP DEFAULT NOW(),
    modified_by VARCHAR(50)
);

-- Índices para optimización
CREATE INDEX idx_turn_log_user ON turn_log(user_id);
CREATE INDEX idx_turn_log_time ON turn_log(timestamp);
CREATE INDEX idx_step_log_turn ON step_log(turn_id);
CREATE INDEX idx_perf_metrics ON performance_metrics(component_id, metric_name, timestamp);
```

## **ESTIMACIÓN DE IMPLEMENTACIÓN**

| Componente         | Horas | Dependencias                  | Reutilizable del Motor Actual |
|--------------------|-------|-------------------------------|-------------------------------|
| Dispatcher         | 16h   | Ninguna                       | Redis client, DB models       |
| Evaluador          | 12h   | Dispatcher                    | LLM service                   |
| Planificador       | 24h   | Dispatcher, Matriz Adapter    | gRPC client                   |
| Matriz Adapter     | 8h    | Ninguna                       | 80% del Motor Semántico       |
| Agente Coding      | 20h   | Planificador                  | Sandbox Docker (existente)    |
| Monitor            | 12h   | Todos                         | Prometheus client             |
| Optimizador        | 16h   | Monitor                       | DB models                     |
| Logger             | 8h    | Todos                         | 90% del sistema actual        |

**Orden recomendado**:
1. Logger + Matriz Adapter (semana 1)
2. Dispatcher + Evaluador (semana 2)
3. Planificador + Agente Coding (semana 3)
4. Monitor + Optimizador (semana 4)

**Total estimado**: 116 horas (3 semanas full-time)