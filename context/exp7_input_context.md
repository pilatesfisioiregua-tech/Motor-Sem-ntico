# CONTEXTO PARA REDISEÑO DEL CHIEF OF STAFF — EXP 7

---

## 1A. ARQUITECTURA ACTUAL DEL CHIEF OF STAFF

### Vista general
- **24 funciones** | ~6,900 lineas | Orquestador: 2,402 lineas
- Pipeline dual: superficial (preguntas rapidas ~800ms) + profundo (analisis completo ~55-60s)
- Comunicacion via estigmergia (marcas en Postgres, nunca llamadas directas entre agentes)
- Coste actual: ~$0.10/turno con Anthropic (Haiku + Sonnet)
- Infraestructura: Supabase Edge Functions (Deno/TypeScript)

### Flujo del chat

```
TURNO 0 -> ENCUADRE (~500ms)
  Pregunta instantanea de encuadre (codigo puro, 0 LLM)
  Fire-and-forget: 4 parseadores + profundo via pg_net

TURNO 1 -> POST-ENCUADRE (~12-15s)
  Lee marcas de parseadores (ya procesados durante think-time del usuario)
  Llama sync: calculador + chief-datos
  Build cola de preguntas + emite 2

TURNO 2+ -> RUTA C CONTINUA (~800ms por turno)
  actualizarCola() con input del usuario
  Filtrar preguntas resueltas
  Chequear profundo (si listo -> inyectar preguntas)
  priorizarCola() -- ranking inteligente
  Emitir 2 preguntas de la cola
  Si cola vacia -> regeneracion async

CAMBIO DE TEMA -> RUTA A INIT ASYNC (~400ms)
  detectCambioTema() (>90% keywords nuevas, min 3 inputs)
  Fire-and-forget: 4 parseadores + profundo
  Pregunta de encuadre instantanea
```

### Rutas del orquestador (9 rutas)
- `encuadre`: Turno 0, ~500ms
- `init_async`: Cola null, ~400ms
- `reset_async`: Cambio de tema, ~400ms
- `post_encuadre`: Post turno 0, ~12-15s
- `cola`: Turno 2+ con preguntas, ~800ms
- `cola_modo`: Modo intercepta cola, ~800ms
- `cola_profundo_continuo`: Profundo listo, variable
- `cola_vacia_esperando`: Cola vacia, profundo en curso, ~15s
- `cola_regen`: Cola vacia, profundo terminado, async

### Profundo-runner (pipeline completo ~55-60s)

```
Paso 0: Router + Contradicciones (~500ms)
  5 queries paralelas -> router decide que pasos saltar
  detectarContradiccionesInter: Sandwich PRE->Haiku->POST

Paso 1: IAS pipeline (10 agentes)
Paso 2: Chief-tensiones (contradicciones con decisiones previas)
Paso 3: Integradores N1-N2, N3, N4-N5
Paso 4: Alternativas (incremental, radical, descarte)
Paso 5: Verbalizador (respuesta final en lenguaje natural)
```

### Router del profundo (5 rutas, codigo puro <5ms)
- `contradiccion` -> full pipeline
- `operativo_puro_n1n2` -> skip: tensiones, radical, descarte, n3, n45
- `dominio_datos` -> skip: radical, descarte, n45
- `input_emocional` -> skip: descarte
- `default_completo` -> skip: nada

### Los 24 agentes del Chief

| Agente | Capa | LLM | Funcion |
|--------|------|-----|---------|
| orquestador-chief | 0 | No | Orquestador multi-ruta, 2402 lineas |
| profundo-runner | 0 | No | Dispatcher del pipeline profundo, 591 lineas |
| chief-datos | 1 | No | Extrae keywords de marcas IAS |
| chief-mcm | 1 | No | Lee y fusiona marcas de parseadores |
| calculador | 1 | No | Metricas financieras/operativas |
| confrontador | 2 | No | Extrae datos verificables |
| chief-integrador-n12 | 2 | Si | Sintesis operativa N1-N2 |
| chief-integrador-n3 | 2 | Si | Trade-offs estrategicos N3 |
| chief-integrador-n45 | 2 | Si | Coherencia con mision N4-N5 |
| chief-tensiones | 2 | Si | Contradicciones con decisiones previas |
| chief-alt-incremental | 2 | Si | Mejoras incrementales |
| chief-alt-radical | 2 | Si | Alternativas radicales |
| chief-alt-descarte | 2 | Si | Coste de no actuar |
| chief-preguntador | 2 | Si | Genera preguntas priorizadas |
| chief-verbalizador | 3 | Si | Traduce analisis a lenguaje natural |
| chief-post-coherencia | 3 | Si | Verifica coherencia con decisiones |
| chief-post-decisiones | 3 | Si | Extrae decisiones del usuario |
| chief-post-verificador | 3 | No | Verifica confrontacion en respuesta |
| compresor-memoria | - | Si (Haiku) | Comprime sesion: extrae decisiones, datos, patrones |
| cron-cierre-sesiones | - | No | Cierre automatico: inactivas >2h |
| compactador | - | No | GC de marcas consumidas |
| verificador-semillas | - | No | Chequea condiciones de semillas |
| auditor-sistema | - | No | Recoleccion pre-quirurgica |
| shortcuts-gateway | - | No | Gateway para atajos iOS |

### 9 modos conversacionales
- `escucha`: respuesta corta, 0 preguntas
- `diagnosticar`: flujo normal con cola de preguntas
- `elaborar`: expande sobre tema actual
- `confrontar`: busca contradicciones
- `responder`: da respuesta directa
- `ejecutar_lite`: solo preguntas criticas
- `ejecutar_full`: modo ejecucion completo
- `auditar_recoger`: orientacion sobre que auditar
- `auditar_emitir`: emite resultado de auditoria

### Persistencia inter-sesion
- `perfil_usuario`: Perfil cognitivo acumulado (patrones, sesgos, datos)
- `decisiones_chief`: Memoria de decisiones conversacionales
- `sesiones_chief`: Sesiones con turnos, dominio, intencion
- `cola_emergencia`: Insights del profundo dosificados al usuario

---

## 1B. LO QUE EL DOCUMENTO MAESTRO DICE QUE REEMPLAZA AL CHIEF

### Section 1B: Motor v3.3 + Matriz 3LxF reemplazan funcionalidad diagnostica

El Motor v3.3 (7 primitivas sintacticas como INT-03) + la Matriz 3Lx7F reemplazan la funcionalidad diagnostica del Chief. El pipeline dual superficial/profundo, los 9 modos conversacionales, y los 24 agentes especificos del Chief se eliminan. Lo que se conserva como patron: estigmergia, cola priorizada, persistencia inter-sesion, deteccion de contradicciones.

### Section 6E: Gestor de la Matriz como compilador central

El Gestor es un sistema independiente con su propio pipeline. NO es parte del Motor vN. Es el cerebro que mantiene, optimiza y compila la Matriz para TODOS los consumidores del sistema.

```
                    GESTOR DE LA MATRIZ
                    (loop lento, mira hacia dentro)
                           |
                    Mantiene, poda, mejora, compila
                    la Matriz 3Lx7Fx18INT
                           |
              +------------+------------+------------+
              |            |            |            |
              v            v            v            v
         Motor vN    Exocortex     Exocortex     Chief of
         (casos      Pilates       Clinica       Staff
          nuevos)    (movimiento)  (salud oral)  (Jesus)
```

Cada consumidor recibe un PROGRAMA DE PREGUNTAS COMPILADO por el Gestor, no la Matriz entera. El Gestor sabe que preguntas funcionan para que contexto porque tiene los datos de efectividad de TODOS los consumidores.

Para el Chief of Staff el Gestor compila:
```
"Jesus evalua decision arquitectural.
Preguntas de INT-01 (Logica) + INT-16 (Estructural).
Modelo: Maverick (mejor en FronteraxSentido)."
```

Pipeline del Gestor:
1. Actualizar scores de efectividad por preguntaxmodeloxcelda
2. Podar preguntas muertas (n>10, tasa<0.05)
3. Promover preguntas potentes (n>10, tasa>0.40)
4. Detectar complementariedad entre modelos por celda
5. Detectar transferencia cross-dominio
6. Recalcular asignacion modelo->celda
7. Recompilar programas de preguntas por consumidor

### Section 6B: Multi-modelo como dimension algebraica

"Las preguntas determinan QUE CELDAS se cubren. El modelo determina A QUE PROFUNDIDAD. Modelos diferentes cubren celdas diferentes. La diversidad de modelos es una dimension algebraica mas."

Hallazgo empirico: 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). Cada modelo domina celdas diferentes. Son COMPLEMENTARIOS -- ningun modelo es mejor en todo. El enjambre siempre gana.

Asignacion modelo->celda empirica (primera version):
- DeepSeek V3.1: 7 celdas (Conservar, Frontera, generalista)
- DeepSeek R1: 7 celdas (Continuidad, FronteraxSentido, ReplicarxContinuidad)
- GPT-OSS 120B: 4 celdas (Depurar, DistribuirxSentido)
- Claude: 1 celda (AdaptarxSalud)

### Section 8B: Chief marcado como DEPRECADO

Lo que se conserva del Chief como patron (no como codigo):
- Estigmergia entre agentes (patron en Postgres, se lleva tal cual)
- Cola de preguntas priorizada
- Persistencia inter-sesion (perfil_usuario, decisiones)
- Deteccion de contradicciones (se integra en el Motor como paso del pipeline)

Lo que se elimina:
- Pipeline dual superficial/profundo (lo reemplaza el Motor con la Matriz)
- 9 modos conversacionales (overengineered -- el Motor no necesita modos, tiene gradientes)
- Router de intenciones (el detector de huecos del Motor es mas preciso)
- 24 agentes especificos del Chief (se simplifican a pasos del Motor)

### Section 4: Pipeline de 7 pasos del Motor

```
PASO 0: DETECTOR HUECOS           ~200ms | $0 | codigo puro
  7 primitivas + 8 operaciones sintacticas
  -> Que falta en el input
  -> Falacias aritmeticas en el input

PASO 1: CAMPO DE GRADIENTES        ~1-3s | ~$0.01
  Para cada celda (21): grado_actual, grado_objetivo, gap
  -> Output: campo de 21 gradientes ordenados por gap

PASO 2: ROUTING POR GRADIENTE      ~500ms | ~$0.001
  Para cada celda con gap > 0.3:
  -> Que INT cierra ESTE gap con mas efectividad?
  -> Top 3-5 inteligencias por impacto total

PASO 3: COMPOSICION                 ~200ms | $0 | NetworkX
  -> Algebra ensambla red de preguntas
  -> 13 reglas como restricciones duras

PASO 4: ENSAMBLAJE DEL PROMPT       ~100ms | $0
  -> Las preguntas son el prompt. No hay texto imperativo.

PASO 5: EJECUCION                   30-120s | $0.001-0.003/modelo OS
  El agente opera BAJO las preguntas como prompt interno
  -> Multi-modelo en paralelo si celda requiere complementariedad

PASO 6: VERIFICACION DE CIERRE      ~1-3s | ~$0.01
  -> Se cerro el gap por celda?
  -> Si persisten gaps > 0.3: escalar
  -> Max 2 re-intentos por celda

PASO 7: INTEGRACION + REGISTRO      10-20s | ~$0.15
  Sintesis final (Sonnet/Opus -> migrar a OS)
```

### Section 6F: Motor de auto-mejora + Fabrica de Exocortex

Enjambre de codigo OS DENTRO del sistema:
- DeepSeek V3.2: Arquitectura, orquestacion, razonamiento sobre codigo
- Qwen3 Coder: Generacion de codigo puro, tests unitarios
- Cogito 671B: Razonamiento profundo, revisar arquitectura, specs
- DeepSeek V3.1: Codigo rapido y barato para tareas mecanicas

3 niveles de auto-mejora:
1. Fontaneria (auto-aprobable): cambios < 20 lineas
2. Mejoras arquitecturales (CR1 siempre)
3. Auto-evolucion (semillas dormidas + CR1)

Fabrica de Exocortex: El enjambre de codigo no solo mejora el sistema -- fabrica nuevos sistemas. Tiempo: horas, no semanas. Coste: ~$0.50-2 en tokens.

---

## 1C. RESULTADOS EXPERIMENTALES

### EXP 4 -- Mesa Redonda (13 modelos, 2 rondas)

**Mesa evaluadora produccion:** V3.2-chat + V3.1 + R1 = 100% cobertura (3 modelos, 95 celdas 3+)

**Sintetizador:** Cogito-671b #1 sin discusion
- 100% genuinidad de integracion
- 3.6 conexiones cross-lente por output
- 3.0 meta-patrones por output
- Score 170 vs V3.2-chat 141

**Mente Distribuida (pizarra iterativa):**
- 7 modelos -> 5 rondas -> converge
- Nivel medio: 3.99 vs Mesa Redonda 3.27 vs Max Mecanico 2.89
- 425 conexiones entre celdas (Mesa Redonda: 0)
- 239 puntos ciegos detectados (Mesa Redonda: 0)
- GPT-OSS #1 contribuidor (119 contribuciones)
- Qwen3-235b #2 valioso (31 aportes unicos)

**Curva de rendimiento:**
- 1 modelo: 71% del valor
- 2 modelos: 95% del valor
- 7 modelos: 100% del valor

**Hallazgo critico:** Qwen3-235b inflador (+0.93 vs media). NO cerebro -- puntua alto pero no aporta ideas unicas.

**Opus y Sonnet:** prescindibles. 0 aportes unicos. Sin ellos: pierde 0.0% de celdas 3+.

### EXP 5 -- Cadena de Montaje (8 configs x 5 tareas)

**Pipeline lineal:** 56% mejor config vs 32% baseline (+24%)
- Config A (Linea Industrial): 56% pass rate, $0.33
- Config D (Ultra-barato): 51% pass rate, $0.047 -- Pareto ganador (ratio 54)
- Config E (Premium): 15% pass rate, $0.34 -- peor config, pagar mas NO ayuda

**T4 (orquestador async Python): 0% en 8/8 configs** -- techo estructural para pipeline lineal

**Debugger poco eficaz:** solo mejoro en 5/35 casos (16%). Media de mejora: +23%

**Reviewer rompe codigo funcional:** 3 casos confirmados donde reviewer empeoro el codigo

**Veredicto:** La cadena NO es suficiente hoy. Mejor cadena 56%, necesita >90%.

### EXP 1 BIS -- 6 Modelos Nuevos (OpenRouter)

| Modelo | Score | Coste | Rol asignado |
|--------|-------|-------|-------------|
| Step 3.5 Flash | 0.98 | $0.019 | Debugger/Razonador |
| Nemotron Super | 0.96 | $0.007 | Math/Validacion |
| MiMo V2 Flash | 0.90 | $0.001 | Tier barato universal |
| Kimi K2.5 | 0.86 | $0.038 | Pizarra |
| Devstral | 0.86 | $0.004 | Patcher (#1 SWE) |
| Qwen 3.5 397B | 0.85 | $0.033 | Evaluador |

**T5 Sintesis:** 6/6 modelos sacaron 1.00 -- todos saben sintetizar

**Todos los roles cubiertos** con modelos OS que cuestan entre $0.001 y $0.038

### EXP 5b -- Modelos Nuevos en Pipeline Multi-Estacion

| Task | Exp 5 Mejor | Exp 5b Mejor | Config ganadora |
|------|-------------|-------------|-----------------|
| T1 Edge Function | 0% | **100%** | N3_coding (Step 3.5 + Devstral) |
| T4 Orquestador | 0% | **0%** | -- |

**T1 resuelto:** Devstral (implementador rapido) + Step 3.5 Flash (debugger potente) = 10/10 tests
- N2_cheap: 7/7 (100%) en debug round 1
- N3_coding: 10/10 (100%) en debug round 3
- Skip E5/E6 validado: Reviewer rompio N2_cheap de 7/7 a 6/19

**T4 no resuelto:** 0% en 3/3 configs
- Causa 1: Think-tag blowup (Step 3.5 gasta 16K tokens en <think> sin output)
- Causa 2: T4 (async Python + mocks aiohttp) demasiado complejo para modelos OS actuales
- MiMo V2 Flash no sufre think-tags -> buen candidato para Architect

### EXP 6 -- Agente con Loop (en curso, analisis de OpenHands)

**Patron observe->think->act** con loop event-driven:
- Max 500 iteraciones (configurable)
- Stuck detection: 5 escenarios (accion repetida x4, error repetido x3, monologo, ciclo largo, context window)
- Docker sandbox para aislamiento
- Per-command timeout: 120s
- Budget enforcement: para agente si excede
- Condenser plugin para gestion de contexto (sliding window + sumarizacion)
- 9 herramientas: Bash, IPython, File editor, Browser, Think, Finish, Task tracker, Condensation, MCP

**Multi-modelo via LiteLLM:** Router opcional para dirigir diferentes prompts a diferentes modelos

**Patrones clave para nuestro agente:**
1. Event-driven > imperativo: separar acciones de observaciones
2. Error como input: el error completo va al agente como Observation
3. Stuck detection multi-escenario: 3-5 patrones necesarios
4. Sin Docker -> necesitas blacklist explicita
5. Condenser > truncate: sumarizar es mejor que cortar
6. Budget enforcement: imprescindible
7. Function calling JSON: mas robusto que parsing de texto

---

## 1D. PROBLEMAS DIAGNOSTICADOS DEL CHIEF ACTUAL

### 1. MONOLINGUE
Todos los agentes usan el mismo modelo (Haiku/Sonnet de Anthropic). Exp 4 demostro que diversidad de modelos = dimension algebraica. Cada modelo ve cosas diferentes. V3.2-chat + V3.1 + R1 = 100% cobertura vs Claude solo = 71%.

### 2. PIPELINE LINEAL EN PROFUNDO
Exp 5 demostro techo de 0% en tareas complejas (T4). El profundo-runner (5 pasos secuenciales) no puede iterar. Necesita loops con observe->think->act.

### 3. NO USA LA MATRIZ
Diagnostica con IAS (parseadores + lentes) no con la Matriz 3Lx7F. Los gaps no dirigen las preguntas -- las preguntas son genericas, no compiladas por gradientes de gaps.

### 4. 9 MODOS SOBREDISEÑADOS
El Maestro dice "overengineered". Con la Matriz, los gradientes del campo de gaps determinan que hacer -- no necesitas modos explicitos. El modo emerge de los gaps.

### 5. NO PUEDE ACTUAR
Analiza y pregunta pero no puede ejecutar. No tiene coding, no puede modificar agentes, no puede lanzar pipelines. El ciclo se rompe antes de la accion.

### 6. 24 AGENTES PARA LO QUE PODRIA SER ~5-8
Muchos agentes hacen trabajo mecanico que un solo modelo bueno con prompt adecuado resuelve. El fan-out de 7 parseadores + 9 lentes es overhead. Exp 1bis demostro que MiMo V2 Flash a $0.001 hace trabajo equivalente a Haiku.

### 7. VERBALIZADOR MONOLITICO
Un solo Sonnet call para verbalizar. Exp 4 demostro que la sintesis multi-modelo produce mejor output (Cogito como sintetizador: 170 score vs V3.2-chat 141).

### 8. SIN SELF-IMPROVEMENT
No aprende de sus errores. No acumula datos de efectividad. El Gestor de la Matriz si lo hace: cada ejecucion registra gap_pre, gap_post, tasa_cierre -> seleccion natural de preguntas.

---

## 1E. LO QUE SE CONSERVA COMO PATRON (no como codigo)

### Estigmergia (marcas en Postgres) -- funciona, $0
Tabla `marcas_estigmergicas` con tipos: hallazgo, sintesis, alerta, triage, basal, prescripcion, verbalizacion, propuesta, meta, respuesta, senal, profundo_resultado. Los agentes NUNCA se llaman entre si. Toda comunicacion via marcas.

### Cola priorizada de preguntas
priorizarCola() con ranking inteligente. Emite 2 preguntas por turno. Filtra preguntas resueltas. Regeneracion async cuando se vacia.

### Persistencia inter-sesion
- perfil_usuario: patrones, sesgos, datos personales (confianza crece +0.1/ocurrencia)
- decisiones_chief: memoria de decisiones con contexto y alternativas
- cola_emergencia: insights dosificados del profundo (1 por turno, prioridad DESC, TTL 24h)
- compresor-memoria: Haiku extrae decisiones/datos/patrones al cerrar sesion

### Deteccion de contradicciones
detectarContradiccionesInter: Sandwich PRE->Haiku->POST. Compara input actual con decisiones previas.

### Concepto dual rapido/profundo
El concepto de respuesta rapida (~800ms) vs analisis profundo (~55-60s) se conserva, pero la implementacion cambia: el Motor con la Matriz reemplaza el profundo-runner.

### Pipeline profundo como concepto
Router -> analisis -> integracion -> alternativas -> verbalizacion. Los pasos se mantienen pero como configuraciones del pipeline de 7 pasos del Motor.
