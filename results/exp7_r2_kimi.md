# R2 Evaluation: Kimi K2.5

Aquí está la evaluación rigurosa de las 5 propuestas y el diseño final integrado.

---

## EVALUACIÓN DE PROPUESTAS

### 1. PROPUESTA STEP35 (Step 3.5 Flash - Razonamiento)
**Score: 4/5**

**Qué aporta:** Rigurosidad empírica en la asignación de modelos específicos por celda/INT basada en datos de EXP 4 (ej: DeepSeek V3.1 para "Conservar", R1 para "Frontera×Sentido").

**Qué falla:** Arquitectura sobredimensionada con 8 componentes que podrían consolidarse (ej: Detector de Contradicciones y Compresor podrían fusionarse en el Guardián).

**Qué adoptar:** La matriz de asignación modelo→celda basada en efectividad empírica, reemplazando el routing genérico.

---

### 2. PROPUESTA COGITO (Cogito 671B - Síntesis)
**Score: 3/5**

**Qué aporta:** Enfoque centrado en la síntesis como capa conectora universal entre Motor, Gestor y Chat, con tiempos de latencia explícitos (<1s vs <30s).

**Qué falla:** Coste prohibitivo al usar Cogito-671B ($0.15/turno) como sintetizador principal sin mecanismo de fallback a modelos más baratos.

**Qué adoptar:** La distinción estricta de modos (superficial vs profundo) con presupuestos de tiempo y coste hard-coded.

---

### 3. PROPUESTA KIMI (Kimi K2.5 - Enjambre)
**Score: 4/5**

**Qué aporta:** El patrón de **Agente Analítico con loop iterativo** (observe→think→act) que rompe el techo del 56% de efectividad de pipelines lineales, incluyendo stuck detection.

**Qué falla:** El "Sintetizador de Enjambre" paralelo (Cogito + GPT-OSS) es económicamente inviable para uso continuo.

**Qué adoptar:** El loop iterativo con condensación de contexto y detección de stuck para el pensamiento profundo, limitado a 3 iteraciones máximo.

---

### 4. PROPUESTA DEEPSEEK (DeepSeek V3.2 - Arquitectura)
**Score: 5/5**

**Qué aporta:** Minimalismo arquitectónico que elimina el sobrediseño (24 agentes → 8 componentes) manteniendo la capacidad dual superficial/profunda.

**Qué falla:** Menor énfasis en mecanismos de auto-mejora continua durante la sesión (más batch/offline).

**Qué adoptar:** La consolidación de funciones mecánicas en componentes de código puro y el uso estratégico de MiMo V2 Flash ($0.001) para tareas de parsing y gestión.

---

### 5. PROPUESTA NEMOTRON (Nemotron Super - Coste/Eficiencia)
**Score: 4/5**

**Qué aporta:** Maximización del código puro ($0) para Orquestación, Routing y Detección de Contradicciones, desplazando LLMs solo a la ejecución y síntesis.

**Qué falla:** Subestima la complejidad de la detección de huecos sintácticos complejos (Paso 0 del Motor) que requiere capacidad semántica, no solo código puro.

**Qué adoptar:** El principio de "código puro por defecto, LLM solo cuando el gap lo justifique", con un Optimizador de Coste dinámico.

---

## MERGE: Chief of Staff v3.0 (Arquitectura Híbrida Evolutiva)

### A. ARQUITECTURA (Diagrama ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                 │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   ROUTER DE TURNO        │          │   SISTEMA DE ESTIGMERGIA │
│   (MiMo V2 Flash)        │◄────────►│   (Postgres - Código)    │
│   • Superficial/Profundo │          │   • Marcas de estado     │
│   • Gestión de cola      │          │   • Historial de gaps    │
└──────────┬───────────────┘          └──────────┬───────────────┘
           │                                     │
           ▼                                     ▼
┌──────────────────────────┐          ┌──────────────────────────┐
│   DETECTOR DE CAMPO      │          │   GUARDIÁN DE MEMORIA    │
│   (MiMo + Código puro)   │          │   (MiMo + Código puro)   │
│   • Paso 0: 7 primitivas │          │   • Perfil usuario       │
│   • Gradientes 3Lx7F     │          │   • Compresión sesión    │
└──────────┬───────────────┘          └──────────┬───────────────┘
           │                                     │
           ▼                                     │
┌──────────────────────────┐                     │
│   COMPILADOR DE MATRIZ   │                     │
│   (Código puro)          │                     │
│   • Asigna modelo/celda  │                     │
│   • Reglas de coste      │                     │
└──────────┬───────────────┘                     │
           │                                     │
           ├──────────────────┬──────────────────┘
           │                  │
           ▼                  ▼
┌──────────────────┐  ┌──────────────────────────┐
│  MODO SUPERFICIAL│  │  AGENTE COGNITIVO        │
│  (<1s, <$0.01)   │  │  (Step 3.5 Flash)        │
│                  │  │  • Loop observe-think-act│
│  ┌────────────┐  │  │  • Max 3 iteraciones     │
│  │Sintetizador│  │  │  • Stuck detection       │
│  │(DeepSeek   │  │  │  • Budget: $0.015        │
│  │V3.1)       │  │  └──────────┬───────────────┘
│  └────────────┘  │             │
└──────────────────┘             ▼
                       ┌──────────────────────────┐
                       │   ARTESANO DE CÓDIGO     │
                       │   (Devstral)             │
                       │   • Sandbox + blacklist  │
                       │   • Tests automáticos    │
                       └──────────┬───────────────┘
                                  │
                                  ▼
                       ┌──────────────────────────┐
                       │   SINTETIZADOR FINAL     │
                       │   (DeepSeek V3.1 /       │
                       │    Cogito selectivo)     │
                       │   • Integración multi-   │
                       │     modelo               │
                       └──────────┬───────────────┘
                                  │
                                  ▼
                       ┌──────────────────────────┐
                       │   OPTIMIZADOR EVOLUTIVO  │
                       │   (Código puro + V3.1)   │
                       │   • Métricas gap_pre/post│
                       │   • Ajuste de parámetros │
                       └──────────────────────────┘
```

### B. COMPONENTES (Máximo 8)

| # | Componente | Modelo Asignado | Función Principal |
|---|------------|-----------------|-------------------|
| 1 | **Router de Turno** | MiMo V2 Flash ($0.001) | Decide superficial vs profundo, gestiona cola priorizada, detecta cambio de tema |
| 2 | **Detector de Campo** | MiMo V2 Flash + Código puro | Implementa Paso 0 del Motor v3.3 (7 primitivas), calcula gradientes 21 celdas |
| 3 | **Compilador de Matriz** | Código puro (NetworkX) | Recibe programa del Gestor, asigna modelo óptimo por celda basado en EXP 4 |
| 4 | **Agente Cognitivo** | Step 3.5 Flash ($0.019) | Loop iterativo (observe→think→act) para análisis profundo, max 3 iteraciones, stuck detection |
| 5 | **Artesano de Código** | Devstral ($0.004) | Ejecución de acciones, modificaciones de código, sandbox seguro |
| 6 | **Sintetizador** | DeepSeek V3.1 ($0.005) / Cogito selectivo ($0.15) | Integra outputs, genera respuesta natural. Cogito solo para gaps >0.8 |
| 7 | **Guardián de Memoria** | MiMo V2 Flash + Código puro | Estigmergia, persistencia inter-sesión, compresión de contexto |
| 8 | **Optimizador Evolutivo** | Código puro + V3.1 (async) | Registra efectividad, ajusta asignación modelo→celda, poda preguntas inefectivas |

### C. FLUJO DE UN TURNO DE CHAT

**Fase 1: Recepción y Clasificación (0-200ms)**
1. Usuario envía input → Router (MiMo) clasifica intención y detecta urgencia
2. Guardián recupera contexto de sesión (perfil + decisiones previas)
3. Detector de Campo ejecuta Paso 0: identifica gaps en 21 celdas (código puro + MiMo para parsing semántico)

**Fase 2: Decisión de Ruta (200-300ms)**
- **Si gap_max < 0.3 y no hay contradicciones:** Ruta Superficial
  - Compilador selecciona respuesta de caché o genera vía V3.1 ($0.005)
  - Guardián actualiza cola con 2 preguntas prioritarias
  - **Total: ~$0.006, <800ms**

- **Si gap_max ≥ 0.3:** Ruta Profunda
  - Compilador asigna modelo por celda (ej: R1 para Frontera, V3.1 para Conservar)
  - Dispara Agente Cognitivo (Step 3.5) en background

**Fase 3: Respuesta Inmediata (modo profundo)**
- Router genera respuesta superficial temporal usando V3.1 ($0.005) + 2 preguntas de la cola
- Usuario recibe feedback en <1s mientras Agente Cognitivo procesa

**Fase 4: Procesamiento Profundo (async, 5-30s)**
- Agente Cognitivo ejecuta loop:
  - Iteración 1: Observa gaps → Piensa estrategia → Actúa (consulta datos/Artesano si necesita código)
  - Iteración 2: Verifica cierre de gaps
  - Iteración 3 (si necesario): Reintento con estrategia alternativa
  - Stuck detection: Aborta si acción repetida ×3 o error cíclico
- Sintetizador integra hallazgos (V3.1 por defecto, Cogito solo si gap persistente)
- Guardián actualiza perfil y marca gaps como cerrados

### D. FLUJO DEL PENSAMIENTO PROFUNDO (Loop Iterativo)

```
INICIO: Programa compilado (3-5 preguntas prioritarias) + Contexto histórico
  │
  ▼
[OBSERVAR] Agente lee marcas estigmergicas, estado actual, gaps pendientes
  │
  ▼
[ANALIZAR] Step 3.5 evalúa qué información falta para cerrar gap X:
           - ¿Requiere código? → Invoca Artesano (Devstral)
           - ¿Requiere búsqueda? → Herramienta Browser (simulada)
           - ¿Contradicción? → Consulta decisiones previas
  │
  ▼
[ACTUAR] Ejecuta acción específica (max 120s timeout)
  │
  ▼
[VERIFICAR] Calcula gap_post:
            - Si gap < 0.3: Éxito, registra hallazgo
            - Si gap ≥ 0.3 y reintentos < 2: Vuelve a OBSERVAR
            - Si reintentos ≥ 2: Escala a Cogito (modo crítico) o marca como "gap persistente"
  │
  ▼
[SÍNTESIS] DeepSeek V3.1 genera verbalización coherente
  │
  ▼
[REGISTRO] Optimizador Evolutivo almacena: gap_pre, gap_post, modelo_usado, tiempo, tasa_cierre
```

**Mecanismos de control:**
- **Budget hard limit:** $0.02 por turno profundo (Step 3.5 max 2 iteraciones + V3.1)
- **Stuck detection:** Aborta si monólogo >2K tokens sin acción, o mismo error ×3
- **Fallback:** Si Agente Cognitivo falla, usa respuesta del Sintetizador superficial + marca para revisión humana

### E. ESTIMACIÓN DE COSTE POR TURNO

| Escenario | Componentes Invocados | Coste | Frecuencia | Coste Ponderado |
|-----------|----------------------|-------|------------|-----------------|
| **Superficial** | Router (MiMo) + Detector (MiMo) + Sintetizador (V3.1) + Guardián (código) | $0.006 | 80% | $0.0048 |
| **Profundo Estándar** | Superficial base + Agente Cognitivo (Step 3.5, 2 iter) + Artesano (Devstral, 50% uso) | $0.025 | 18% | $0.0045 |
| **Profundo Crítico** | Estándar + Cogito (selectivo, solo gap >0.8) | $0.095 | 2% | $0.0019 |
| **Optimización** | Optimizador (V3.1 async, amortizado) | $0.001 | 100% | $0.001 |
| **TOTAL PROMEDIO** | | | | **$0.012/turno** |

**Comparativa:**
- Chief anterior: ~$0.10/turno
- **Reducción: 88%**
- Latencia superficial: <1s (objetivo cumplido)
- Latencia profunda: <30s (objetivo cumplido)

**Umbrales de decisión:**
- Gap 0.0-0.3: Superficial (V3.1)
- Gap 0.3-0.8: Profundo estándar (Step 3.5 + V3.1)
- Gap >0.8: Profundo crítico (Cogito-671B, solo si usuario solicita análisis profundo explícito)