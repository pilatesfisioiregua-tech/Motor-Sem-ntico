# R1 Design: Step 3.5 Flash
**Perspectiva:** Razonamiento -- que es logicamente necesario vs sobrediseno?

# Rediseño del Chief of Staff (CoS) — Arquitectura Basada en Evidencia Empírica

## A. Diagrama Arquitectónico Completo

```
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|   +----------------+       +------------------+       +----------------+       +----------------+ |
|   |                |       |                  |       |                |       |                | |
|   |   USUARIO      |<----->|  ROUTER & QUEUE  |<----->|  MOTOR         |<----->|  AGENTE DE     | |
|   |                |       |   MANAGER        |       |  COGNITIVO     |       |  CODING        | |
|   +----------------+       +------------------+       +----------------+       +----------------+ |
|          ^                         |  ^                      |  ^                      |          |
|          |                         |  |                      |  |                      |          |
|          |                         v  |                      v  |                      v          |
|          |               +------------------+       +------------------+                     |
|          |               |  SISTEMA DE      |       |  SISTEMA DE      |                     |
|          +-------------->|  ESTIGMERGIA     |<------>|  PERSISTENCIA    |<--------------------+
|                          |  (Postgres)      |       |  (Postgres)      |                     |
|                          +------------------+       +------------------+                     |
|                                   ^                           ^                               |
|                                   |                           |                               |
|                          +------------------+       +------------------+                     |
|                          |  GESTOR DE LA    |       |  MODELOS OS      |                     |
|                          |  MATRIZ          |<------|  (DeepSeek,      |                     |
|                          |  (Externo)       |       |   R1, GPT-OSS,   |                     |
|                          +------------------+       |   MiMo, etc.)    |                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

**Leyenda**:
- Flechas: flujo de datos/control.
- Componentes en azul: lógicos del CoS (≤8).
- Componentes en gris: infraestructura/servicios externos.
- Comunicación: mayormente **estigmergia** (marcas en Postgres) excepto invocación directa Router→Motor y Motor→Agente de Coding.

---

## B. Componentes Lógicos (Máximo 8)

### 1. Router & Queue Manager
- **Qué hace**: 
  - Gestiona el ciclo de chat turno a turno.
  - En turno 0: genera pregunta de encuadre instantánea (código puro, 0 LLM).
  - En turnos 1+: actualiza cola priorizada, emite 2 preguntas por turno.
  - Dispara el Motor Cognitivo cuando la cola está vacía o hay gaps críticos.
  - Gestiona cierre de sesión (inactividad >2h) y compresión de memoria.
  - Lee/escribe marcas estigmergicas y persistencia.
- **Modelo**: **MiMo V2 Flash** ($0.001, ~100ms). Basado en EXP 1bis: modelo barato universal para tareas ligeras. Suficiente para generación de preguntas de emergencia y gestión de cola.
- **Herramientas**: 
  - Acceso a Postgres (lectura/escritura de tablas: `sesiones_chief`, `cola_emergencia`, `marcas_estigmergicas`).
  - Código puro para lógica de turnos y priorización.
- **Comunicación**:
  - Directa con Motor Cognitivo: llamada asincrónica (via `pg_net` o cola de tareas) para disparar análisis profundo.
  - Con Estigmergia: lee marcas de la sesión actual para contexto; escribe marcas de tipo `senal` (ej: "nueva_pregunta").
  - Con Persistencia: lee `perfil_usuario`, `decisiones_chief`; escribe actualizaciones de sesión.

### 2. Motor Cognitivo
- **Qué hace**: 
  - Ejecuta el pipeline de 7 pasos usando la Matriz 3Lx7F.
  - **Paso 0**: Detector de huecos completo (7 primitivas + 8 operaciones sintácticas).
  - **Paso 1**: Campo de gradientes (calcula gap por celda).
  - **Paso 2**: Routing por gradiente (selecciona top 3-5 INT por celda, basado en efectividad del Gestor).
  - **Paso 3**: Composición algebraica (NetworkX, 13 reglas duras).
  - **Paso 4**: Ensamblaje del prompt (preguntas compiladas por el Gestor como prompt interno).
  - **Paso 5**: Ejecución multi-modelo en paralelo (asigna modelos OS a INT según Gestor). Invoca Agente de Coding si la INT requiere acción.
  - **Paso 6**: Verificación de cierre (reintentos si gap >0.3).
  - **Paso 7**: Integración + verbalización (síntesis multi-modelo, extracción de decisiones, generación de marcas).
  - Produce lista de preguntas priorizadas para la cola.
- **Modelo**: **Multi-modelo** (asignación dinámica por celda/INT, según datos del Gestor). Ejemplos empíricos (EXP 4):
  - Celdas "Conservar"/"Frontera": **DeepSeek V3.1** (score 2.19, costo ~$0.001).
  - Celdas "Continuidad"/"FronteraxSentido": **DeepSeek R1** (score 2.18).
  - Celdas "Depurar"/"DistribuirxSentido": **GPT-OSS 120B** (score 2.15).
  - Integración N3/N45: **DeepSeek R1** o **R1** (buenos en trade-offs).
  - Tareas de código: **Devstral** (EXP 1bis: #1 patcher, $0.004).
  - Tareas de depuración: **Step 3.5 Flash** (EXP 1bis: debugger potente, $0.019).
- **Herramientas**:
  - NetworkX para composición.
  - Cliente API para modelos OS (via LiteLLM o similar).
  - Invocación a Agente de Coding (RPC interna).
  - Acceso a Postgres (lectura de Matriz, marcas, persistencia).
- **Comunicación**:
  - Con Router: recibe trigger, devuelve preguntas y marcas.
  - Con Gestor: solicita programa de preguntas compilado; reporta métricas (gap_pre, gap_post, tasa_cierre, INT usadas).
  - Con Agente de Coding: invoca tareas específicas.
  - Con Estigmergia: escribe marcas de `hallazgo`, `sintesis`, `decision`.
  - Con Persistencia: guarda decisiones extraídas, actualiza perfil.

### 3. Agente de Coding
- **Qué hace**:
  - Ejecuta tareas de codificación con loop observe->think->act.
  - Implementa, prueba, depura, revisa código.
  - Gestiona contexto (condenser), detecta stuck (5 escenarios), aplica budget enforcement.
  - Opera en sandbox aislado (Docker preferido, sino blacklist).
- **Modelo**: **Multi-modelo especializado**:
  - **Devstral** para implementación rápida (EXP 5b: 100% en T1 con Step).
  - **Step 3.5 Flash** para depuración (EXP 1bis: debugger potente).
  - Router interno: si la tarea es "escribir código", usa Devstral; si es "depurar error", usa Step.
- **Herramientas**:
  - Sandbox: Docker (con límites de recursos) o blacklist de comandos.
  - Herramientas: Bash, IPython, File editor, Browser, Think, Finish, Task tracker, Condensation, MCP (como OpenHands, EXP 6).
  - Condenser para gestión de contexto (sliding window + sumarización).
  - Timeout per command: 120s.
- **Comunicación**:
  - Invocado por Motor Cognitivo con tarea estructurada (JSON: descripción, archivos, expected output).
  - Devuelve resultado (código, logs, tests) al Motor.
  - Puede escribir marcas estigmergicas (ej: `codigo_generado`).

### 4. Sistema de Estigmergia (Infraestructura Compartida)
- **Qué hace**: 
  - Tabla `marcas_estigmergicas` en Postgres.
  - Tipos: `hallazgo`, `sintesis`, `alerta`, `triage`, `basal`, `prescripcion`, `verbalizacion`, `propuesta`, `meta`, `respuesta`, `senal`, `profundo_resultado`.
  - Todos los componentes escriben/leen marcas para coordinación sin acoplamiento.
  - Las marcas incluyen: `sesion_id`, `turno`, `tipo`, `contenido` (JSON), `timestamp`.
- **Modelo**: No aplica (infraestructura).
- **Herramientas**: Postgres (Supabase).
- **Comunicación**: 
  - Lectura/escritura directa por Router, Motor, Agente de Coding.
  - Coste: $0 (solo base de datos).

### 5. Sistema de Persistencia (Infraestructura Compartida)
- **Qué hace**:
  - Almacena datos inter-sesión:
    - `perfil_usuario`: patrones, sesgos, datos personales, confianza.
    - `decisiones_chief`: decisiones tomadas con contexto y alternativas.
    - `sesiones_chief`: metadata de sesiones (dominio, intención, turnos).
    - `cola_emergencia`: insights pendientes (TTL 24h).
  - El Router gestiona la cola activa en memoria, pero `cola_emergencia` es persistente.
- **Modelo**: No aplica.
- **Herramientas**: Postgres (Supabase).
- **Comunicación**: Lectura/escritura por Router y Motor.

### 6. Detector de Contradicciones (Subcomponente del Motor)
- **Qué hace**: 
  - Compara input actual con decisiones previas (`decisiones_chief`) para detectar contradicciones.
  - Implementa sandwich PRE->Haiku->POST? No, usa modelo OS ligero (MiMo V2 Flash) para eficiencia.
  - Inyecta alertas como marcas estigmergicas y ajusta gaps.
- **Modelo**: **MiMo V2 Flash** ($0.001). Suficiente para comparación semántica.
- **Herramientas**: Acceso a `decisiones_chief` y marcas.
- **Comunicación**: Integrado en Motor (Paso 0 o Paso 6). Escribe marcas `alerta`.

### 7. Compresor de Memoria (Función del Router)
- **Qué hace**: 
  - Al cerrar sesión (inactividad >2h), extrae decisiones, datos, patrones usando modelo ligero.
  - Actualiza `perfil_usuario` y `decisiones_chief`.
  - Elimina marcas consumidas (compactador).
- **Modelo**: **MiMo V2 Flash** ($0.001).
- **Herramientas**: Acceso a sesión, marcas, persistencia.
- **Comunicación**: Disparado por Router (cron-cierre-sesiones integrado).

### 8. Interfaz con Gestor de la Matriz (Componente de Integración)
- **Qué hace**:
  - Solicita al Gestor (servicio externo) el "programa de preguntas compilado" para el CoS (asignación modelo→celda/INT).
  - Reporta métricas de efectividad tras cada ejecución del Motor.
- **Modelo**: No aplica (cliente HTTP).
- **Herramientas**: API REST/GraphQL al Gestor.
- **Comunicación**: 
  - Motor → Gestor: GET programa, POST métricas.
  - Gestor → Motor: devuelve asignaciones.

---

## C. Flujo de un Turno de Chat (Paso a Paso)

1. **Usuario envía mensaje** en turno N.
2. **Router & Queue Manager** recibe mensaje.
3. **Si turno 0 (nueva sesión)**:
   - Genera pregunta de encuadre instantánea (código puro, ej: "¿Qué dominio principal abordamos hoy?").
   - Crea registro en `sesiones_chief`.
   - Emite pregunta al usuario.
   - **Fin de turno** (~500ms).
4. **Si turno ≥1**:
   - Lee contexto: `sesiones_chief`, `decisiones_chief`, `perfil_usuario`, marcas recientes.
   - **Actualiza cola**:
     - Para cada pregunta en cola (almacenada en memoria o `cola_emergencia`), usa MiMo V2 Flash para determinar si el input del usuario la responde (similitud semántica >80%). Si sí, marca como resuelta y elimina.
   - **Si hay preguntas en cola**:
     - Prioriza por: (1) antigüedad, (2) prioridad asignada por Motor, (3) relevancia a gaps actuales (si se tienen).
     - Emite top 2 preguntas.
     - **Fin de turno** (~200-500ms).
   - **Si cola vacía**:
     - Calcula gaps rápidos (Paso 0 ligero) con MiMo V2 Flash sobre input + contexto.
     - Si gaps >0.3 en alguna celda:
       * Dispara Motor Cognitivo asincrónicamente (via `pg_net`).
       * Genera 2 preguntas de emergencia con MiMo V2 Flash (prompt: "Basado en gaps [lista], genera 2 preguntas exploratorias").
       * Emite preguntas de emergencia.
     - Si no hay gaps:
       * Responde con conocimiento de `perfil_usuario`/`decisiones_chief` (MiMo V2 Flash para redacción).
     - **Fin de turno** (~