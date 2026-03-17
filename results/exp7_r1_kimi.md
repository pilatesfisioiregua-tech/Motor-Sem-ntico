# R1 Design: Kimi K2.5
**Perspectiva:** Enjambre -- como orquestar multiples modelos como agentes?

Aquí está el rediseño completo del **Chief of Staff v2.0** (codename: *Enjambre*), migrando de un orquestador monolítico a una arquitectura de agentes especializados basada en evidencia empírica.

---

## A. ARQUITECTURA (Diagrama ASCII)

```
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA DE INTERACCIÓN                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Usuario    │◄──►│   Chat API   │◄──►│   Director   │      │
│  │  (Turno N)   │    │  (Edge/Deno) │    │ (V3.2-chat)  │      │
│  └──────────────┘    └──────────────┘    └──────┬───────┘      │
└──────────────────────────────────────────────────┼──────────────┘
                                                   │
                    ┌──────────────────────────────┼──────────────┐
                    │         ORQUESTACIÓN         │              │
                    │                              ▼              │
                    │  ┌─────────────────────────────────────┐   │
                    │  │     COMPILADOR DE MATRIZ            │   │
                    │  │     (MiMo V2 Flash + Código puro)   │   │
                    │  │  • Compila programa de preguntas    │   │
                    │  │  • Lee scores de efectividad        │   │
                    │  │  • Selecciona modelo por celda      │   │
                    │  └──────────────┬──────────────────────┘   │
                    │                 │                           │
                    ▼                 ▼                           │
┌─────────────────────────────┐  ┌─────────────────────────────┐  │
│   MODO SUPERFICIAL (<1s)    │  │    MODO PROFUNDO (<30s)     │  │
│  ┌─────────────────────┐    │  │  ┌─────────────────────┐    │  │
│  │  DETECTIVE DE GAPS  │    │  │  │  AGENTE ANALÍTICO   │    │  │
│  │   (MiMo V2 Flash)   │    │  │  │  (Step 3.5 Flash)   │    │  │
│  │  • Paso 0 Motor v3  │    │  │  │  • Loop observe→act │    │  │
│  │  • 7 primitivas     │    │  │  │  • Max 5 iteraciones│    │  │
│  │  • Falacias aritm.  │    │  │  │  • Stuck detection  │    │  │
│  └──────────┬──────────┘    │  │  └──────────┬──────────┘    │  │
│             │               │  │             │               │  │
│  ┌──────────▼──────────┐    │  │  ┌──────────▼──────────┐    │  │
│  │   GUARDIÁN DE       │    │  │  │   ARTESANO DE       │    │  │
│  │   MEMORIA           │    │  │  │   CÓDIGO            │    │  │
│  │  (MiMo + Postgres)  │    │  │  │  (Devstral + Qwen3) │    │  │
│  │  • Cola priorizada  │    │  │  │  • Ejecuta pipelines│    │  │
│  │  • Estigmergia      │    │  │  │  • Modifica agentes │    │  │
│  │  • Perfil usuario   │    │  │  │  • Sandbox seguro   │    │  │
│  └──────────┬──────────┘    │  │  └──────────┬──────────┘    │  │
│             │               │  │             │               │  │
└─────────────┼───────────────┘  └─────────────┼───────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────┐
│              SINTETIZADOR DE ENJAMBRE                         │
│         (Cogito-671B + GPT-OSS 120B paralelo)                 │
│  • Integra hallazgos multi-modelo                             │
│  • Verifica coherencia (POST sandwich)                        │
│  • Genera respuesta final + próximas preguntas                │
└──────────────────────────┬────────────────────────────────────┘
                           │
┌──────────────────────────▼────────────────────────────────────┐
│                   REFINADOR (Self-Improvement)                │
│              (DeepSeek V3.1 + Datos históricos)               │
│  • Actualiza scores: gap_pre vs gap_post                      │
│  • Podar preguntas (tasa<0.05)                                │
│  • Promover preguntas (tasa>0.40)                             │
│  • Recalcula asignación modelo→celda                          │
└───────────────────────────────────────────────────────────────┘
```

---

## B. COMPONENTES (Máximo 8)

### 1. DIRECTOR (DeepSeek V3.2-chat)
**Qué hace:** Enrutamiento de alto nivel, decisión superficial vs profundo, detección de cambio de tema, presupuesto de tokens por turno.

**Por qué este modelo:** EXP 4 demostró que V3.2-chat + V3.1 + R1 = 100% cobertura de celdas. V3.2 es el mejor generalista para orquestación (score 141 en síntesis vs 170 Cogito, pero 10x más barato y rápido).

**Herramientas:** 
- Router de intención (código puro basado en keywords)
- Control de presupuesto ($0.02 hard limit por turno)
- Scheduler de tareas paralelas

**Comunicación:** Direct call al Compilador y Detective; estigmergia (marca `director_decision`) para el resto.

---

### 2. COMPILADOR DE MATRIZ (MiMo V2 Flash + Código puro)
**Qué hace:** Implementa el "Gestor de la Matriz" local. Recibe el campo de gradientes (21 celdas) y compila el "Programa de Preguntas" óptimo para el contexto actual.

**Por qué este modelo:** EXP 1bis: MiMo V2 Flash ($0.001) es el "tier barato universal" (score 0.90). Las tareas mecánicas de compilación (filtrar preguntas muertas, asignar modelos) no requieren razonamiento profundo.

**Herramientas:**
- Query a `matriz_efectividad` (Postgres): scores por pregunta×modelo×celda
- Algoritmo de selección: maximiza cobertura de gaps > 0.3 con mínimo coste
- Cache de programas compilados (TTL 1h)

**Comunicación:** Lee marcas `gradiente_campo` (output del Detective); escribe marca `programa_compilado`.

---

### 3. DETECTIVE DE GAPS (MiMo V2 Flash)
**Qué hace:** Paso 0 del Motor v3.3. Detecta qué falta en el input usando las 7 primitivas sintácticas (INT-03) y 8 operaciones. Identifica falacias aritméticas.

**Por qué este modelo:** Paso 0 es mecánico y debe ser <200ms. MiMo es 20x más barato que Haiku y suficiente para parsing sintáctico (reemplaza a los 7 parseadores antiguos).

**Herramientas:**
- Regex compiladas para primitivas (INT-01 a INT-07)
- Detector de contradicciones simples (sandwich ligero: input→MiMo→check)
- Output: JSON con `huecos_detectados[]` y `gradientes_iniciales[21]`

**Comunicación:** Escribe marca `analisis_huecos`; nunca llama directamente.

---

### 4. AGENTE ANALÍTICO (Step 3.5 Flash + Loop iterativo)
**Qué hace:** Reemplaza el pipeline profundo lineal. Opera bajo el "Programa de Preguntas" compilado. Loop observe→think→act con máximo 5 iteraciones.

**Por qué este modelo:** EXP 5b demostró que Step 3.5 Flash es el #1 en debugging (resolvió T1 100% con Devstral). EXP 6 validó que el patrón OpenHands (loop event-driven) es necesario para romper el techo del 56% de pipelines lineales.

**Herramientas:**
- 9 herramientas tipo OpenHands: Bash, FileEditor, Think, Browser, TaskTracker
- Stuck detection: 5 patrones (acción repetida×4, error×3, monólogo, ciclo largo, context window)
- Condenser: sliding window + resumen cada 3 iteraciones
- Budget: max $0.015 por ejecución profunda

**Comunicación:** Lee `programa_compilado`; escribe marcas `hallazgo_iteracion_N`. No ejecuta código peligroso directamente (delega al Artesano).

---

### 5. ARTESANO DE CÓDIGO (Devstral + Qwen3 Coder)
**Qué hace:** Brazo ejecutor. Implementa cambios de código, modifica agentes, lanza pipelines de testing. Aislamiento vía blacklist (sin Docker por ahora).

**Por qué este modelo:** EXP 1bis: Devstral es #1 en SWE (score 0.86, $0.004). EXP 5b: Devstral + Step 3.5 = 100% pass rate en T1. Qwen3 Coder genera tests unitarios y valida.

**Herramientas:**
- FileEditor con diff semántico
- Test runner local (Deno/Node)
- Git operations (branch, commit, PR)
- Sandbox: blacklist de comandos peligrosos (rm -rf, curl | bash)

**Comunicación:** Recibe tareas vía marca `tarea_codigo` del Agente Analítico o Director; escribe `resultado_codigo` + `tests_passed`.

---

### 6. SINTETIZADOR DE ENJAMBRE (Cogito-671B + GPT-OSS 120B paralelo)
**Qué hace:** Integra hallazgos del Agente Analítico y contexto histórico. Genera respuesta final en lenguaje natural + próximas 2 preguntas.

**Por qué estos modelos:** EXP 4: Cogito-671B es el mejor sintetizador (score 170, 100% genuinidad, 3.6 conexiones cross-lente). GPT-OSS 120B es el mejor contribuidor en pizarra iterativa (119 aportes). Ejecutar en paralelo y fusionar sus outputs supera a cualquier modelo solo.

**Herramientas:**
- Fusion de outputs: combina respuesta Cogito (profundidad) + GPT-OSS (creatividad)
- Verificador de coherencia (sandwich POST: output→MiMo→check vs decisiones previas)
- Selector de modo conversacional implícito (emerge de gaps, no explícito)

**Comunicación:** Lee marcas `hallazgo_*` y `perfil_usuario`; escribe `respuesta_final` + `cola_preguntas`.

---

### 7. GUARDIÁN DE MEMORIA (MiMo V2 Flash + Código puro)
**Qué hace:** Gestiona estigmergia, cola priorizada, persistencia inter-sesión, compresión de memoria.

**Por qué este modelo:** Tareas mecánicas de I/O y ranking. Reemplaza a chief-datos, chief-mcm, calculador, y compresor-memoria antiguos.

**Herramientas:**
- `priorizarCola()`: ranking por urgencia (gap alto) + relevancia histórica
- `actualizarPerfil()`: extrae patrones/decisiones vía regex + embeddings ligeros
- `compactarMarcas()`: GC de marcas consumidas (>24h)
- `detectarCambioTema()`: cosine similarity vs embeddings sesión previa

**Comunicación:** Todas las operaciones vía Postgres (`marcas_estigmergicas`). Es el único componente que escribe en `perfil_usuario` y `decisiones_chief`.

---

### 8. REFINADOR (DeepSeek V3.1 + Datos históricos)
**Qué hace:** Self-improvement. Analiza resultados de cada interacción para optimizar la Matriz. Corre en background (async) cada 10 turnos o al cerrar sesión.

**Por qué este modelo:** V3.1 es barato ($0.005) y bueno para análisis estadístico y código. No requiere creatividad, sí procesamiento de datos.

**Herramientas:**
- Query a `historial_cierres`: gap_pre, gap_post, modelo_usado, tasa_cierre
- Algoritmo de poda: elimina preguntas con n>10, tasa<0.05
- Algoritmo de promoción: marca preguntas con n>10, tasa>0.40 como "default"
- Recalculador de asignación: qué modelo va a qué celda basado en efectividad histórica

**Comunicación:** Lee todas las marcas de la sesión; escribe en `matriz_efectividad` y `configuracion_enjambre`.

---

## C. FLUJO DE UN TURNO DE CHAT (Paso a paso)

### Turno Tipo 1: Superficial/Rápido (<1s, ~$0.005)

1. **Input usuario** → Edge Function recibe mensaje
2. **Director** (V3.2, $0.01) decide: "superficial" (consulta simple, no gaps críticos)
3. **Detective** (MiMo, $0.001) corre en paralelo:
   - Detecta huecos sintácticos en <200ms
   - Si gap_max < 0.3: continúa superficial
   - Si gap_max >= 0.3: marca para profundo (fire-and-forget)
4. **Guardián** (código puro):
   - `actualizarCola()` con input usuario
   - Filtra preguntas ya resueltas
   - Selecciona top 2 de cola existente
5. **Sintetizador** (modo ligero: solo GPT-OSS o incluso V3.2, $0.01):
   - Genera respuesta corta + 2 preguntas de la cola
6. **Response** → Usuario recibe respuesta en ~800ms
7. **Background** (async): Si se detectaron gaps graves, lanza Agente Analítico para próximo turno

### Turno Tipo 2: Profundo/Análisis (<30s, ~$0.018)

1. **Input usuario** → Director detecta que hay gaps pendientes o el usuario pide análisis
2. **Compilador** (MiMo, $0.001 + código):
   - Lee campo de gradientes (21 celdas) de la marca del Detective
   - Selecciona modelo óptimo por celda (ej: R1 para Frontera×Sentido, V3.1 para Conservar)
   - Compila "Programa de 5-7 preguntas específicas"
3. **Agente Analítico** (Step 3.5, max $0.015):
   - Iteración 1: Observa programa + contexto → Think → Act (busca datos)
   - Iteración 2: Observa resultados → Think → Act (analiza contradicciones)
   - Iteración 3: Verifica cierre de gaps (si gap > 0.3 persiste, iteración 4)
   - Max 5 iteraciones o hasta stuck detection
   - Escribe hallazgos en marcas `hallazgo_nivel_1`, `hallazgo_nivel_2`, etc.
4. **Guardián**: Actualiza cola con insights del análisis (prioriza gaps cerrados)
5. **Sintetizador** (Cogito + GPT-OSS paralelo, $0.08... *corrección: esto excede presupuesto*):

**Ajuste para cumplir <$0.02:**
- En modo profundo estándar, usar solo **Step 3.5** ($0.019) para análisis + **V3.2** ($0.01) para síntesis = $0.029... sigue siendo alto.

**Solución de coste:**
- **Modo Profundo Ligero**: Step 3.5 Flash ($0.019) hace análisis + síntesis en un solo paso (1 llamada, 1 iteración). Total: ~$0.02.
- **Modo Profundo Enjambre**: Solo cuando el usuario lo solicita explícitamente o es crítico. Usa Cogito ($0.08) pero amortizado en sesiones largas (cada 10 turnos, no cada turno).

6. **Refinador** (background): Actualiza scores de efectividad del modelo usado para las celdas tratadas.

---

## D. FLUJO DEL PENSAMIENTO PROFUNDO (Loop iterativo)

Basado en EXP 6 (OpenHands) y EXP 5b (Cadena de Montaje):

```
INICIO: Programa de Preguntas compilado + Contexto histórico
  │
  ▼
[OBSERVE] Leer marcas actuales, estado del sistema, gaps detectados
  │
  ▼
[THINK] Step 3.5 Flash genera plan de acción:
        - Qué información falta para cerrar gap X?
        - Qué herramienta usar (Browser, FileEditor, Bash)?
        - Qué modelo del enjambre consultar para opinión complementaria?
  │
  ▼
[ACT] Ejecuta acción (ej: consulta browser, lee archivo, llama a Devstral para patch)
  │
  ▼
[VERIFY] Chequea si se cerró el gap:
         - Si gap < 0.3: éxito, pasa a siguiente celda
         - Si gap >= 0.3 y reintentos < 2: vuelve a OBSERVE
         - Si reintentos >= 2: escala a modelo superior (Cogito) o marca como "gap persistente"
  │
  ▼
[STUCK DETECTION] Cada 3 iteraciones:
                  - ¿Acción repetida? → Aborta, cambia estrategia
                  - ¿Error idéntico? → Aborta, reporta al Refinador
                  - ¿Monólogo largo (>2K tokens sin acción)? → Condensar contexto
  │
  ▼
[OUTPUT] Escribe marca `sintesis_profunda` con:
         - Gaps cerrados (lista)
         - Gaps persistentes (lista + justificación)
         - Recomendaciones de acción (para Artesano o Usuario)
```

**Tiempo máximo:** 30s (timeout hard).  
**Presupuesto:** $0.015 por ejecución (max 3 iteraciones de Step 3.5).

---

## E. INTEGRACIÓN CON MOTOR COGNITIVO (Matriz 3Lx7F)

El Chief ya no "diagnostica" con IAS (parseadores + lentes). Ahora es un **consumidor compilado** de la Matriz:

1. **Entrada al Motor**: El Detective de Gaps implementa el **Paso 0** del Motor v3.3:
   - Usa las 7 primitivas sintácticas (INT-03) para mapear input a celdas
   - Genera el **Campo de Gradientes**: 21 valores (grado_actual vs grado_objetivo)

2. **Compilación**: El Compilador recibe este campo y ejecuta lógica del **Gestor de la Matriz**:
   - Para cada celda con gap > 0.3, consulta: "¿Qué INT cierra este gap con más efectividad?"
   - Selecciona top 3 inteligencias por impacto
   - Aplica **álgebra de composición** (13 reglas como restricciones duras vía NetworkX)

3. **Ejecución**: El Agente Analítico opera bajo el "Programa de Preguntas" que es el output del paso anterior. Las preguntas son el prompt (no hay texto imperativo).

4. **Verificación de Cierre**: Paso 6 del Motor. El Sintetizador verifica si los gaps se cerraron:
   - Si persisten gaps > 0.3: marca para re-intento o escalamiento
   - Máximo 2 re-intentos por celda

5. **Sin Modos**: Los 9 modos antiguos desaparecen. El "modo" emerge del campo de gradientes:
   - Todos los gaps bajos + usuario preguntando datos → modo "escucha"
   - Gaps altos en Frontera + Sentido → modo "confrontar"
   - Gaps en Operativo puro → modo "ejecutar"

---

## F. INTEGRACIÓN CON AGENTE DE CODING

El Chief ahora puede **actuar**, no solo analizar:

**Caso 1: Modificación de sí mismo**
- El Agente Analítico detecta que una función está obsoleta (gap en código)
- Escribe marca `tarea_refactor` con especificación
- **Artesano** (Devstral) lee la marca, crea branch, implementa cambio, corre tests
- Si tests pass: escribe `propuesta_cambio` para revisión humana (o auto-aprobar si <20 líneas según reglas de Fontanería)

**Caso 2: Lanzar pipelines externos**
- Usuario pide: "Analiza las ventas del Q3 y genera un reporte PDF"
- Director detecta tarea de código → enruta a Agente Analítico con herramienta `TaskTracker`
- Agente descompone: 1) Query datos, 2) Generar gráficos, 3) Compilar PDF
- Delega pasos 1-2 al Artesano (Qwen3 Coder para scripts Python)
- Sintetizador integra resultado y entrega al usuario

**Caso 3: Auto-mejora arquitectural**
- Refinador detecta que cierta celda de la Matriz nunca se cierra con el modelo actual
- Lanza `tarea_arquitectura`: "Evaluar si necesitamos nuevo modelo para celda X"
- Artesano investiga (browser) modelos nuevos en OpenRouter, actualiza `matriz_efectividad`

---

## G. SELF-IMPROVEMENT (Ciclo de aprendizaje)

Basado en Section 6F (Motor de auto-mejora):

**Nivel 1: Fontanería (Auto-aprobable)**
- Cada interacción registra: `gap_pre`, `gap_post`, `modelo_usado`, `coste`, `tiempo`, `tasa_cierre` (gap_post/gap_pre)
- Refinador detecta anomalías: "Step 3.5 cierra gap Frontera 40% mejor que V3.2"
- Ajusta asignación modelo→celda en tiempo real (próxima compilación usa nuevo modelo)

**Nivel 2: Mejoras Arquitecturales (CR1 - Code Review 1)**
- Cuando un gap persiste (>0.3) en 5 sesiones consecutivas, el Refinador genera `propuesta_mejora`:
  - "Añadir nueva pregunta tipo INT-16 para celda Distribuir×Sentido"
  - "Dividir Agente Analítico en dos especializados"
- Artesano implementa cambio en branch
- Director evalúa en sandbox (simulación con datos históricos)
- Si mejora tasa_cierre >10%: merge

**Nivel 3: Auto-evolución (Semillas dormidas)**
- Refinador mantiene lista de "semillas" (ideas para nuevos componentes)
- Cuando presupuesto mensual lo permite, activa semilla:
  - Ej: "Añadir modelo Nemotron Super para validación matemática" (EXP 1bis: score 0.96 en math)
- Corre 10 sesiones de prueba, compara vs baseline
- Si es mejor, promueve a componente permanente

---

## H. QUÉ SE ELIMINA DEL CHIEF VIEJO Y POR QUÉ

| Componente Eliminado | Razón (Evidencia) |
|---------------------|-------------------|
| **Pipeline dual superficial/profundo fijo** | Reemplazado por gradientes de la Matriz. El "modo" emerge de los gaps, no de rutas codificadas. |
| **9 modos conversacionales** | Overengineered (Section 8B). Los gradientes del campo determinan el comportamiento; no se necesitan modos explícitos. |
| **Router de intenciones (código puro)** | El detector de huecos del Motor v3.3 es más preciso que keywords (Section 4). |
| **24 agentes específicos** | Fan-out excesivo. EXP 1bis demostró que MiMo V2 Flash ($0.001) reemplaza trabajo de 7 parseadores + 9 lentes IAS. |
| **Profundo-runner (5 pasos secuenciales)** | Techo estructural de 56% (EXP 5). Reemplazado por Agente Analítico con loop iterativo (observe→think→act). |
| **Verbalizador monolítico (Sonnet)** | EXP 4: Un solo modelo es peor que síntesis multi-modelo (Cogito+GPT-OSS). Además, Claude es prescindible (0 aportes únicos). |
| **Chief-datos, chief-mcm, calculador** | Consolidados en Guardián de Memoria (MiMo + código puro). Tareas mecánicas no necesitan LLM caro. |
| **Dependencia Anthropic (Claude/Haiku/Sonnet)** | Coste ($0.10/turno) y lock-in. Modelos OS superan a Claude en la Matriz (V3.1: 2.19 vs Claude: 1.79, Section 6B). |
| **Comunicación síncrona entre agentes** | Reemplazada por estigmergia pura. El Chief viejo tenía llamadas sync "calculador + chief-datos" que bloqueaban. |

---

## I. QUÉ SE CONSERVA Y POR QUÉ

| Patrón Conservado | Justificación |
|------------------|---------------|
| **Estigmergia (marcas en Postgres)** | Funciona, cuesta $0, desacopla componentes. Evita cascadas de fallos. |
| **Cola priorizada de preguntas** | Dosifica insights complejos al usuario (2 preguntas/turno). Evita sobrecarga cognitiva. |
| **Persistencia inter-sesión** | `perfil_usuario` y `decisiones_chief` son datos críticos para coherencia a largo plazo. |
| **Detección de contradicciones** | Mecanismo validado (sandwich PRE→LLM→POST). Ahora integrado en Detective y Sintetizador. |
| **Concepto dual rápido/profundo** | El usuario necesita feedback inmediato (<1s) pero también análisis profundo (<30s). La dualidad se mantiene, la implementación cambia. |
| **Compresor de memoria** | Necesario para sesiones largas. MiMo V2 Flash reemplaza a Haiku pero mantiene función. |
| **Fire-and-forget para profundo** | Lanza análisis profundo en background mientras usuario recibe respuesta superficial. Optimiza tiempo de espera. |

---

## J. ESTIMACIÓN DE COSTE POR TURNO

### Escenario A: Turno Superficial (80% de los casos)
```
Director (V3.2, 2K tokens)        $0.008
Detective (MiMo, 1K tokens)       $0.001
Sintetizador ligero (V3.2, 1.5K)  $0.006
Guardián (código puro)            $0.000
-----------------------------------------
TOTAL                             $0.015
```
**Latencia:** ~600-800ms

### Escenario B: Turno Profundo Estándar (15% de los casos)
```
Director (V3.2)                   $0.008
Compilador (MiMo + código)        $0.001
Agente Analítico (Step 3.5 Flash) 
  - 2 iteraciones × $0.0095       $0.019
Sintetizador (V3.2, modo síntesis) $0.008
Refinador (background, amortizado) $0.002
-----------------------------------------
TOTAL                             $0.038
```
*Nota: Esto excede ligeramente $0.02, pero ocurre solo 1 de cada 6-7 turnos. Promedio ponderado: $0.019.*

**Optimización para cumplir <$0.02 en profundo:**
- Reducir a 1 iteración de Step 3.5 ($0.0095) + verificación ligera ($0.001) = $0.0105
- Total ajustado: $0.008 + $0.001 + $0.0105 + $0.008 = **$0.0275**... aún alto.

**Solución final:** Usar **DeepSeek V3.1** ($0.005) para análisis profundo (2 iteraciones = $0.01) en lugar de Step 3.5. EXP 4 demostró que V3.1 es efectivo (2.19 score).
- Coste profundo: $0.008 + $0.001 + $0.010 + $0.008 = **$0.027**

**Promedio real por usuario activo:**
- 80% × $0.015 = $0.012
- 20% × $0.027 = $0.0054
- **Promedio: $0.0174/turno** (vs $0.10 anterior = **82% de reducción**)

### Escenario C: Turno Profundo Enjambre (5% de casos críticos)
```
Sintetizador (Cogito-671B)        $0.08
GPT-OSS 120B (paralelo)           $0.015
Integración y fusión              $0.005
-----------------------------------------
TOTAL                             $0.10
```
*Justificación: Solo para decisiones arquitectónicas críticas o cuando el usuario explicita "piensa profundamente".*

---

## RESUMEN EJECUTIVO

El nuevo Chief of Staff pasa de ser un **orquestador monolítico de 24 agentes** a un **Director de Enjambre de 8 componentes**, eliminando la dependencia de Anthropic y reduciendo costes un 82%. 

La clave es la **Matriz 3Lx7F** como núcleo de diagnóstico (reemplazando IAS), la **diversidad de modelos OS** como dimensión algebraica (V3.2, Step 3.5, Devstral, Cogito), y el **loop iterativo** (tipo OpenHands) que rompe el techo del 56% de efectividad de los pipelines lineales.

El sistema ahora puede **actuar** (modificar código, lanzar pipelines) y **auto-mejorarse** (aprender de cada interacción qué preguntas y modelos funcionan mejor para cada celda de la Matriz), cumpliendo con el requisito de ser un "Chief of Staff" verdaderamente inteligente y autónomo.