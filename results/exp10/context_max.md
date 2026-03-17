# OMNI-MIND — DOCUMENTACIÓN COMPLETA


============================================================
## Contexto/CONTEXTO_SISTEMA.md
============================================================

# OMNI-MIND CEREBRO — Estado Completo del Sistema

> Documento de contexto para sesiones de trabajo con Claude.
> Generado: 27 febrero 2026 | Última actualización: Fase S-PROP completada (1 marzo 2026)

---

## 1. QUÉ ES OMNI-MIND

Un **sistema operativo cognitivo** construido sobre Supabase Edge Functions (Deno/TypeScript). Funciona como un "exocortex": el usuario (Jesús) interactúa via chat; el sistema analiza su input con múltiples agentes especializados que trabajan en paralelo sin llamarse entre sí — se comunican via **estigmergia** (marcas en base de datos que otros agentes leen).

**Modelo mental**: Colmena de agentes. Cada uno lee marcas, hace su trabajo, deja una marca nueva. Un orquestador decide el orden. Nadie manda a nadie directamente.

---

## 2. INFRAESTRUCTURA

| Recurso | Detalle |
|---------|---------|
| **Producción** | Supabase `cptcltizauzhzbwxcdft` — `https://cptcltizauzhzbwxcdft.supabase.co` |
| **Staging** | Supabase `jbfiylwbgxglqwvgsedh` — ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY |
| **Edge Functions** | 99 funciones Deno/TypeScript. Deploy: `supabase functions deploy <name> --no-verify-jwt` |
| **Migraciones** | 47 SQL (bootstrap + 46 timestamped) |
| **Deploy script** | `./scripts/deploy.sh staging|prod [--only fn] [--migrations-only] [--functions-only]` |
| **LLM** | Todas las llamadas via `llm-proxy` Edge Function. Soporta Haiku (parseadores, detectores) y Sonnet (diseño, síntesis). Fallback automático |
| **Plan Supabase** | Free tier: 150s timeout, 500MB DB |
| **Presupuesto** | €200/mes. Coste actual: ~$0.005/ciclo ≈ $15/mes |

### Comunicación entre agentes

**REGLA ABSOLUTA**: Los agentes NUNCA se llaman entre sí. Toda comunicación es via la tabla `marcas_estigmergicas`:
- Un agente escribe una marca (tipo: hallazgo, sintesis, alerta, propuesta, etc.)
- Otro agente lee marcas y actúa sobre ellas
- Cross-enjambre: tabla `marcas_cross` (origen_enjambre → destino_enjambre, expiran en 72h)

### Fire-and-forget (pg_net)

Para disparar agentes en background sin esperar respuesta:
- `disparar_edge_function(p_url, p_key, p_function_name, p_payload)` — genérica, cualquier función
- `disparar_profundo_runner(p_url, p_key, p_sesion_id, p_ciclo_id, p_input, p_datos_previos)` — específica profundo

El `await` solo espera que Postgres acepte (~10ms). La función corre async.

---

## 3. TABLAS PRINCIPALES

| Tabla | Propósito | Enjambre |
|-------|-----------|----------|
| `marcas_estigmergicas` | Comunicación estigmérgia. CHECK en `tipo`: hallazgo, sintesis, alerta, triage, basal, prescripcion, verbalizacion, propuesta, meta, respuesta, senal, profundo_resultado | Todos |
| `estado_agentes` | Registro de todos los agentes con capa, modelo, estado | Todos |
| `enjambres` | Registro de enjambres con misión y config | Sistema |
| `registro_arquitectura` | 157+ componentes (87+ edge_fn, 40 tabla, 29 módulo, 4 script, 1 interfaz) | Sistema |
| `historial_cambios` | Audit trail de deploys, cambios, rollbacks | Sistema |
| `log_operaciones` | Trazabilidad de operaciones | Todos |
| `métricas` | Métricas append-only (latencia, tokens, coste, errores) | Todos |
| `señales` | Señales de control: halt, degrade, reload-config, flush, resume | Kernel |
| `conocimiento_dominio` | Datos de dominio verificados (herramientas, contexto) | IAS |
| `repositorio_documentos` | Documentos: specs, código, prompts, arquitectura | Sistema |
| `decisiones_cr1` | Decisiones de Jesús con contexto y alternativas | Chief |
| `decisiones_chief` | Memoria de decisiones conversacionales | Chief |
| `sesiones_chief` | Sesiones del chat con turnos, dominio, intención | Chief |
| `perfil_usuario` | Perfil cognitivo acumulado entre sesiones (patrones, sesgos, datos) | Chief |
| `cola_emergencia` | Insights del profundo dosificados al usuario | Chief |
| `cola_mejoras` | Mejoras propuestas y aprobadas. CHECK tipo: mejora/bug/optimizacion/feature/pregunta/presupuesto. CHECK origen: jesus/chief/mejora_continua/manual/telemetria/auditor | Implementador + Auditor |
| `turnos_episodicos` | Capa episódica: raw de cada turno. Se borra post-compresión | Chief |
| `compresor_dead_letter` | Dead Letter Queue: compresiones fallidas para reintento | Chief |
| `baselines_agentes` | Agregados estadísticos multi-ventana (24h/7d/30d) por agente. CQRS read side | Plataforma |
| `semillas_dormidas` | 20 semillas dormidas (8 originales + 11 telemetría B0 + 1 A4) con condiciones de activación | Kernel |
| `sesiones_enjambre` | Sesiones por enjambre (telemetría) | Todos |
| `marcas_ciclo` | Marcas de terreno por sesión/turno | Todos |
| `reglas_deteccion` | 17 reglas de detección de anomalías | Mejora Continua |
| `propuestas_mejora` | Propuestas de mejora generadas | Mejora Continua |
| `ejecuciones_mejora` | Ejecuciones de mejoras aprobadas | Mejora Continua |
| `tareas_shortcuts` | Cola async para iOS Shortcuts | Sistema |
| `tenants` | Identidad de consumidores del cerebro (API key, manifest, rate limit, modo) | Gateway |
| `metering` | Telemetría avanzada de cada request al gateway (tokens, latencia, coste, JSONB) | Gateway |
| `capability_registry` | Catálogo de capacidades + circuit breaker state por capability | Gateway |
| `tareas_async` | Tareas async pendientes/completadas con resultado + polling | Gateway |

---

## 4. ENJAMBRES — Estado Actual

### 4.1 IAS (Pipeline Diagnóstico) — OPERATIVO

**Misión**: Analizar el input del usuario desde 3 lentes (Salud/Supervivencia, Sentido/Coherencia, Continuidad/Sostenibilidad) para encontrar huecos, contradicciones y datos ausentes.

**28 funciones** | ~5,647 líneas | Capas 1-5

| Capa | Agentes | Función |
|------|---------|---------|
| 1 | 7 parseadores | Sustantivos (relaciones implícitas), Verbos (predicados vacíos), Adjetivos (comparaciones sin ref), Adverbios (temporal vs causal), Conectores (Y/PERO/AUNQUE), Contexto (histórico), Niveles (N1-N5) |
| 2 | calculador, contexto-conversacion, contexto-dominio | Métricas operativas, historia, conocimiento dominio |
| 3 | 3×3 lentes (input+basal+completa) | salud, sentido, continuidad — cada una tiene versión input, basal (datos reales), y completa |
| 3 | correlador-vida, cruzador-input, sintetizador-diferencial | Cruzar las 3 lentes, detectar contradicciones, síntesis diferencial |
| 4 | prescriptor | Prescripciones concretas basadas en diagnóstico |
| 5 | verbalizador | Informe en lenguaje natural |

**Estado**: Funcional. Usado como motor de análisis por el Chief of Staff.

### 4.2 Chief of Staff (Pipeline Conversacional) — OPERATIVO

**Misión**: Interfaz conversacional con el usuario. Pipeline dual superficial (preguntas rápidas) + profundo (análisis completo ~55-60s).

**24 funciones** | ~6,900 líneas | Orquestador: 2,402 líneas

#### Flujo del chat:

```
TURNO 0 → ENCUADRE (~500ms)
  Pregunta instantánea de encuadre (código puro, 0 LLM)
  Fire-and-forget: 4 parseadores + profundo via pg_net

TURNO 1 → POST-ENCUADRE (~12-15s)
  Lee marcas de parseadores (ya procesados durante think-time del usuario)
  Llama sync: calculador + chief-datos
  Build cola de preguntas + emite 2

TURNO 2+ → RUTA C CONTINUA (~800ms por turno)
  actualizarCola() con input del usuario
  Filtrar preguntas resueltas
  Chequear profundo (si listo → inyectar preguntas)
  priorizarCola() — ranking inteligente
  Emitir 2 preguntas de la cola
  Si cola vacía → regeneración async

CAMBIO DE TEMA → RUTA A INIT ASYNC (~400ms)
  detectCambioTema() (>90% keywords nuevas, min 3 inputs)
  Fire-and-forget: 4 parseadores + profundo
  Pregunta de encuadre instantánea
```

#### Rutas del orquestador:

| Ruta | Trigger | Latencia | Detalle |
|------|---------|----------|---------|
| `encuadre` | Turno 0 (!estado) | ~500ms | Pregunta encuadre + fire-and-forget |
| `init_async` | Cola null | ~400ms | Fire-and-forget + encuadre |
| `reset_async` | Cambio de tema | ~400ms | Fire-and-forget + encuadre |
| `post_encuadre` | ultimo_tipo = encuadre/init_async | ~12-15s | Lee parseadores, build cola |
| `cola` | Turno 2+ con preguntas | ~800ms | Emite 2 preguntas |
| `cola_modo` | Modo intercepta cola | ~800ms | Respuesta/preguntas por modo |
| `cola_profundo_continuo` | Profundo listo | variable | Respuesta profunda + preguntas |
| `cola_vacia_esperando` | Cola vacía, profundo en curso | ~15s (poll) | Espera profundo |
| `cola_regen` | Cola vacía, profundo terminado | async | Regenera preguntas |

#### Profundo-runner (pipeline completo ~55-60s):

```
Paso 0: Router + Contradicciones (~500ms)
  5 queries paralelas → router decide qué pasos saltar
  detectarContradiccionesInter: Sandwich PRE→Haiku→POST

Paso 1: IAS pipeline (10 agentes)
Paso 2: Chief-tensiones (contradicciones con decisiones previas)
Paso 3: Integradores N1-N2, N3, N4-N5
Paso 4: Alternativas (incremental, radical, descarte)
Paso 5: Verbalizador (respuesta final en lenguaje natural)
```

**Router (5 rutas, código puro <5ms)**:
- `contradiccion` → full pipeline
- `operativo_puro_n1n2` → skip: tensiones, radical, descarte, n3, n45
- `dominio_datos` → skip: radical, descarte, n45
- `input_emocional` → skip: descarte
- `default_completo` → skip: nada

#### Agentes del Chief:

| Agente | Capa | LLM | Función |
|--------|------|-----|---------|
| orquestador-chief | 0 | No | Orquestador multi-ruta, 2402 líneas |
| profundo-runner | 0 | No | Dispatcher del pipeline profundo, 591 líneas |
| chief-datos | 1 | No | Extrae keywords de marcas IAS |
| chief-mcm | 1 | No | Lee y fusiona marcas de parseadores |
| calculador | 1 | No | Métricas financieras/operativas |
| confrontador | 2 | No | Extrae datos verificables |
| chief-integrador-n12 | 2 | Sí | Síntesis operativa N1-N2 |
| chief-integrador-n3 | 2 | Sí | Trade-offs estratégicos N3 |
| chief-integrador-n45 | 2 | Sí | Coherencia con misión N4-N5 |
| chief-tensiones | 2 | Sí | Contradicciones con decisiones previas |
| chief-alt-incremental | 2 | Sí | Mejoras incrementales |
| chief-alt-radical | 2 | Sí | Alternativas radicales |
| chief-alt-descarte | 2 | Sí | Coste de no actuar |
| chief-preguntador | 2 | Sí | Genera preguntas priorizadas |
| chief-verbalizador | 3 | Sí | Traduce análisis a lenguaje natural |
| chief-post-coherencia | 3 | Sí | Verifica coherencia con decisiones |
| chief-post-decisiones | 3 | Sí | Extrae decisiones del usuario |
| chief-post-verificador | 3 | No | Verifica confrontación en respuesta |
| compresor-memoria | — | Sí (Haiku) | Comprime sesión: extrae decisiones, datos, patrones → perfil_usuario |
| cron-cierre-sesiones | — | No | Cierre automático: inactivas >2h, pausas expiradas, dead letter retry |
| compactador | — | No | GC de marcas consumidas |
| verificador-semillas | — | No | Chequea condiciones de semillas |
| auditor-sistema | — | No | Recolección pre-quirúrgica |
| shortcuts-gateway | — | No | Gateway para atajos iOS |

### 4.3 Diseño (Meta-diseño de Enjambres) — OPERATIVO

**Misión**: Diseñar nuevos enjambres de agentes a partir de una necesidad del usuario.

**18 funciones** | ~2,739 líneas | 6 capas

| Capa | Agentes | Función |
|------|---------|---------|
| 1 | llamada-ias | Triage: llama a IAS para analizar la necesidad |
| 2 | detector-huecos-necesidad, detector-huecos-contexto, detector-huecos-restricciones, formulador-preguntas | Detectar qué falta antes de diseñar |
| 3 | disenador-agentes, disenador-datos, disenador-flujo, explorador-externo, verificador-diseno, confrontador | Diseño en paralelo: agentes + datos + flujo + benchmark |
| 4 | traductor-natural | Traduce diseño técnico a lenguaje claro (Sonnet) |
| 5 | generador-spec-agentes, generador-spec-datos, generador-spec-deploy | Genera specs implementables (TypeScript, SQL, deploy) |
| 6 | verificador-implementacion, documentador | Verifica + documenta el ciclo |

**5 rutas del orquestador-diseno**:
- **Ruta A**: Input → L1-2 (análisis + detectar huecos)
- **Ruta E**: Respuestas usuario → re-formular preguntas
- **Ruta B**: Sin huecos → L3+4 (diseño completo)
- **Ruta C**: Aprobado → L5 (generar specs)
- **Ruta D**: Verificar → L6 (documentar)

**Estado**: E2E funcional. Timings en free plan: A ~140s, E ~10s, B ~78s, C ~43s, D ~8s.

### 4.4 Mejora Continua — OPERATIVO

**Misión**: Detectar anomalías en métricas, generar propuestas de mejora, ejecutar las aprobadas.

**3 funciones + cron** | ~1,260 líneas

| Agente | Capa | Función |
|--------|------|---------|
| detector-mejora | 1 | Detecta anomalías vía 17 reglas (latencia, errores, coste, calidad) |
| procesador-mejora | 2 | Correlaciona señales, genera propuestas para CR1 (Haiku) |
| basal-mejora | 3 | Ejecuta propuestas aprobadas, evalúa resultados |
| basal-cron | — | Captura periódica de estado basal |

**Estado**: Operativo. Enjambre ID dinámico (buscar por nombre='mejora_continua').

---

## 5. MÓDULOS COMPARTIDOS (_shared/)

| Módulo | Exporta | Propósito |
|--------|---------|-----------|
| `señales.ts` | `chequearSeñales()` | Control: halt/degrade/resume al inicio de cada agente |
| `métricas.ts` | `registrarMétrica()` | Log append-only a tabla métricas. DEBE ser await |
| `retry.ts` | `conRetry()` | Retry con backoff exponencial [1s, 2s, 4s] |
| `telemetria.ts` | `escribirMarcaCross()`, `leerMarcasCross()` | Comunicación cross-enjambre |
| `terreno.ts` | `escribirMarca()`, `leerMarcas()` | Marcas de ciclo por sesión/turno |
| `limpiarJSON.ts` | `limpiarJSON()` | Repara JSON truncado por LLM max_tokens |
| `baseline.ts` | `calcularBaseline()` | Baselines multi-ventana (24h/7d/30d) para anomalías |
| `correlador.ts` | `PaqueteCorrelacion` | Correlación de señales con enfriamiento |
| `propositor.ts` | `generarPropuesta()` | Genera propuestas concretas para CR1 |
| `reloj.ts` | `obtenerReloj()` | Contexto temporal completo (Madrid TZ, festividades, estaciones) |
| `tipos.ts` | Interfaces TypeScript | Tipos compartidos |
| `registroDetectores.ts` | `DETECTORES[]` | Registro dinámico de detectores de anomalías |
| `telemetria_avanzada.ts` | `esTelemActiva()`, `telemActivas()` | Cache 5min de semillas telem_*. Safe default: false |
| `primitivas-v2/` | 24 archivos (tipos, prompts, orquestador × 7 primitivas + index + tipos sujeto-predicado + prompts sujeto-predicado + orquestador sujeto-predicado) | Prisma semántico: mini-enjambres de análisis multi-ángulo |

---

## 6. FASES COMPLETADAS

### Fase 0 — Sistema Operativo (completada)
- Conexión de orquestador-chief + profundo-runner a `_shared/` (señales, métricas, retry)
- `registrarMétrica` DEBE ser `await`ed (Edge Functions terminan en Response return)
- NO pasar `sesion_id` a `registrarMétrica` (FK → sesiones_enjambre, chief sessions no están ahí)

### Fase 1 — Pipeline Básico (completada)
- Turno 0 encuadre + parseadores + profundo funcional
- Cola de preguntas + priorizarCola()
- Profundo-runner completo con verbalizador

### Fase 2 — Persistencia Entre Sesiones (completada)
- 3 tablas: `perfil_usuario`, `cola_emergencia`, `sesiones_chief`
- Perfil cognitivo se acumula entre sesiones (confianza crece +0.1/ocurrencia)
- Cola de emergencia dosifica insights del profundo (1 por turno, prioridad DESC)
- `actualizarPerfil()` fire-and-forget en 8 puntos antes de cada Response

### Fase 3 — Router + Contradicciones (completada)
- profundo-runner: 477 líneas. Paso 0 con 5 queries paralelas + router + detector contradicciones
- Router código puro <5ms, 5 rutas: contradiccion, operativo_n1n2, datos, emocional, default
- detectarContradiccionesInter: Sandwich PRE→Haiku→POST
- chief-verbalizador: recibe y usa perfil_usuario en system prompt

### Fase 4 — Progressive Revelation Ruta A (completada)
- Ruta A reescrita: De sync ~3-6s (6 LLM calls) a async ~400ms (fire-and-forget)
- POST-ENCUADRE expandido: acepta `ultimo_tipo === "init_async"` además de `"encuadre"`
- 3 bugs corregidos: (1) detectCambioTema siempre false (push antes de detect), (2) POST-ENCUADRE bloqueado por esCambioTema, (3) STOP words sin verbos conversacionales
- detectCambioTema: threshold 0.9, min 3 inputs, STOP expandida
- E2E verificado: 5 turnos en producción (encuadre→post_encuadre→cola→cola→reset_async)

### Chief v2 — 5 Puntos Flacos (completado)
1. **`/reset` override manual** (orquestador-chief): `/reset`, `/nuevo`, `/cambio` fuerzan cambio de tema sin depender de keyword analysis. El texto tras el comando se usa como input del nuevo tema
2. **POST-ENCUADRE sin marcas**: Ya cubierto por fallback síncrono existente (no requirió cambio)
3. **Marcas stale en re-dispatches** (profundo-runner): parseador-niveles ahora filtra por `ciclo_id` en vez de solo `created_at DESC` — evita leer marcas de ciclos anteriores
4. **cola_emergencia sin TTL** (orquestador-chief): Filtro `created_at >= hace 24h` — emergencias viejas se ignoran automáticamente
5. **Perfil crudo al verbalizador** (chief-verbalizador): `resumirPerfilParaVerbalizador()` extrae solo tono preferido + top-3 sesgos + top-3 datos personales en 1 línea compacta (ahorra ~200 tokens/llamada)

### Fase 5 — Dosificación cola_emergencia (completada)
- **profundo-runner** (477→591 líneas): `extraerInsightsSobrantes()` extrae insights no incluidos en la respuesta principal
- **Fuentes de sobrantes**: alternativa radical, coste de no actuar, tensiones extra (>1), preguntas extra del verbalizador (>2), tensión misión/operativo (N45)
- **Escritura**: Batch insert en `cola_emergencia` con prioridades decrecientes (0.8, 0.65, 0.5, 0.35, 0.3). Max 5 sobrantes por ciclo
- **Dosificación**: El orquestador-chief (ya existente) lee 1 emergencia por turno (prioridad DESC, TTL 24h)
- **Paso 3 reestructurado**: Alternativas ahora capturadas en variables (`resAltInc`, `resAltRad`, `resAltDesc`) para extraer sobrantes
- **UUID guard**: `sesion_id` solo se incluye en insert si es UUID válido (cola_emergencia.sesion_id es tipo UUID)
- **Coste**: $0 adicional (código puro, 0 LLM)
- **E2E verificado**: Input rico → 2 sobrantes (alternativa radical + tensión N45) en cola con prioridades correctas

### Fase 6 — Router de Modos Conversacionales + Fix Telemetría (completada)

**Paso 0 — Fix telemetría:**
- 8x `registrarMétrica` sin `await` corregidos (4 en orquestador-chief, 4 en profundo-runner)
- **chief-verbalizador** migrado al SO: imports `chequearSeñales`, `registrarMétrica`, `conRetry`
- `chequearSeñales` al inicio del handler (respeta señales halt)
- Llamada a `llm-proxy` envuelta en `conRetry` (3 intentos con backoff)
- 2x `log_operaciones` directo → `registrarMétrica` (`verbalizador_completo`, `verbalizador_error`)

**Paso 1 — `detectarIntencion()` (5 tipos):**
- Reemplaza `clasificarIntencion()` (4 tipos). Nuevos: `expandir`, `decidir`, `diagnosticar`, `ejecutar`, `auditar`
- Detección por: (1) comandos explícitos regex, (2) estructura de frase, (3) fallback por tipo_encuadre
- Métrica: `intencion_detectada` con input_preview + tipo_encuadre

**Paso 2 — `determinarModo()` (9 modos):**
- Función pura: `(intención × profundoTerminado × mcmSuficiente) → Modo`
- Modos: `escucha`, `diagnosticar`, `elaborar`, `confrontar`, `responder`, `ejecutar_lite`, `ejecutar_full`, `auditar_recoger`, `auditar_emitir`
- Lee `mcm_suficiente` del resultado del profundo
- Persistido en estado (marca sintesis): `modo_activo`, `intencion`, `modo_historia`
- Métrica: `modo_cambio` cuando el modo cambia entre turnos
- `intencion` y `modo_activo` incluidos en TODOS los responses de RUTA C

**Paso 3 — Comportamiento por modo en orquestador:**
- Switch por modo en RUTA C antes de emitir preguntas de cola:
  - `escucha`: respuesta corta ("Sigue.", "Entendido. ¿Qué más?"), 0 preguntas. Tras 3 turnos → sugiere transición
  - `ejecutar_lite`: solo preguntas `gravedad: "critico"`. Si no hay → "No tengo preguntas bloqueantes"
  - `auditar_recoger`: pregunta orientadora sobre qué aspecto auditar
  - `diagnosticar` y otros: flujo normal (cola de preguntas)
- Detección cambio de intención mid-sesión (turno > 1):
  - Explícito: regex `/^(brainstorm|decidir|analiza|hacer|audita|ahora quiero|cambiemos|vale,)/`
  - Natural: `expandir→decidir`, `diagnosticar→ejecutar`
  - Métrica: `intencion_cambio`
- Nueva ruta: `cola_modo` (response type cuando un modo intercepta)

**Paso 4 — 6 prompts por modo en verbalizador:**
- `SYSTEM_PROMPT` fijo → `PROMPTS_POR_MODO` map (diagnosticar, confrontar, elaborar, responder, ejecutar_full, auditar_emitir)
- `REGLAS_COMUNES` compartidas: no markdown, no jerga, no empatía falsa, output JSON
- Verbalizador lee `modo_activo` de marca sintesis (estigmergia pura, Opción B de CR1)
- Modo incluido en marca del verbalizador + métrica `verbalizador_completo`

**Métricas nuevas:** `intencion_detectada`, `modo_cambio`, `modo_escucha_activo`, `modo_ejecutar_lite`, `intencion_cambio`, `verbalizador_completo` (con modo)
**Coste adicional:** ~$0.60/mes (mismas llamadas LLM, solo cambia el system prompt)

### Fase 7 — Agente Implementador Autónomo (completada)

Pipeline local que cierra el circuito: diseño → spec → implementación → test → deploy → telemetría → mejora. No es Edge Function, es scripting local.

**Paso 1 — Schema YAML + Template:**
- `specs/briefing-schema.yaml`: Contrato estándar entre Opus (diseña) y Code (ejecuta)
- `specs/briefing-template.yaml`: Briefing trivial de ejemplo (inserta comentario en orquestador-chief)
- `CLAUDE.md`: Instrucciones del agente implementador (11 pasos, regla de oro)
- `.env.staging` / `.env.prod`: Variables de entorno para ambos entornos

**Paso 2 — Tests de regresión (`tests/regresion.sh`):**
- 6 tests: Chief, Profundo, LLM-proxy, Parseador sustantivos, tabla métricas, tabla señales
- macOS compatible (perl ms_now, poll-based timeout fallback sin `timeout`/`gtimeout`)
- Tablas REST con URL encoding: `m%C3%A9tricas`, `se%C3%B1ales`
- LLM-proxy usa campo `mensajes` (no `messages`) y `modelo` (no `model`)
- 6/6 pasan contra producción

**Paso 3 — Executor (`scripts/ejecutar-briefing.sh`):**
- Pipeline: parsear YAML → SQL staging → archivos → deploy staging → tests → regresión → (gate) → prod
- Modificación archivos via perl con env vars (`PERL_BUSCAR`, `PERL_INS`) para evitar shell escaping
- Métricas REST a `m%C3%A9tricas` con campos correctos (enjambre, evento, agente, exitoso, data)
- Deploy prod: pipe `echo "y"` para confirmación interactiva de `deploy.sh`
- Rollback automático si humo prod falla
- Logs en `logs/implementador/`

**Paso 4 — Tabla `cola_mejoras`:**
- Migración `20260227020000_cola_mejoras.sql`: tabla con campos tipo, origen, descripcion, contexto (jsonb), prioridad (0-1), estado
- CHECK constraints: tipo IN (mejora, bug, optimizacion, feature), origen IN (chief, mejora_continua, manual, telemetria)
- Helper `_shared/cola_mejoras.ts`: `escribirMejora()` para insertar desde cualquier agente
- Desplegada en staging + producción

**Paso 5 — Warmup E2E:**
- briefing-template.yaml ejecutado: YAML parseado → archivo modificado → deploy staging OK → test briefing pasa
- Regresión staging parcial (4/6): LLM-proxy y parseador fallan porque staging no tiene ANTHROPIC_API_KEY
- Métricas del implementador aparecen en producción: `briefing_inicio`, `briefing_fase`, `briefing_test`, `briefing_resultado`

**Métricas nuevas:** `briefing_inicio`, `briefing_fase`, `briefing_test`, `briefing_regresion`, `briefing_resultado`, `briefing_deploy_prod`, `briefing_rollback`, `briefing_error`
**Pendiente:** Configurar OPENAI_API_KEY en staging
**Coste:** $0 (scripting local, métricas via REST API, 0 LLM)

### Fase A1 — Compresor de Memoria (Capa Episódica + Síntesis) (completada)

**Objetivo**: Event sourcing de conversaciones. Cada turno se graba en `turnos_episodicos`. Al cerrar sesión, un compresor (Haiku) extrae decisiones, datos, patrones y los alimenta a `perfil_usuario` + `decisiones_chief`. Los turnos raw se borran post-compresión.

**5 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301010000_turnos_episodicos.sql`):
- `turnos_episodicos`: sesion_id, turno_num, input_usuario, output_sistema, ruta_usada, metadata
- `compresor_dead_letter`: Dead Letter Queue para compresiones fallidas (max 3 reintentos, cooldown 30min)
- ALTER `sesiones_chief`: +`estado` (abierta/pausada/comprimiendo/cerrada), +`pausado_hasta`, +`ultimo_turno_at`

**Pieza 2 — Escritura episódica** (orquestador-chief, +182 líneas):
- **Comandos de sesión**: `/cerrar` (compresión inmediata), `pausa hasta...` (max 48h), reactivación automática
- **9 puntos de escritura episódica**: insert en `turnos_episodicos` antes de cada return conversacional
- `ultimo_turno_at` actualizado en cada turno

**Pieza 3 — compresor-memoria** (343 líneas, Edge Function):
- Lee turnos → construye transcripción → LLM Haiku → extrae JSON estructurado
- Alimenta: `perfil_usuario` (datos+patrones, upsert con confianza creciente), `decisiones_chief`
- Graceful degradation: JSON parse falla → fallback con raw substring
- Dead letter queue: on error → inserta en `compresor_dead_letter`, revierte estado a "abierta"
- Telemetría máxima: turnos procesados, bytes, JSON completitud, LLM latencia, modelo, fallback

**Pieza 4 — cron-cierre-sesiones** (89 líneas, Edge Function):
- 3 criterios: sesiones abiertas >2h inactivas, pausas expiradas, dead letter retry
- Para cada una: llama `compresor-memoria` con trigger apropiado
- Dead letter retry exitoso → marca `resuelto: true`
- Invocado desde basal-cron (fire-and-forget)

**Pieza 5 — basal-cron** (+8 líneas):
- Llamada fire-and-forget a `cron-cierre-sesiones` tras marca basal

**Tests verificados (producción):**
- T1 ✅ Turno episódico escrito (turno_num=0, ruta=encuadre)
- T2 ✅ 2 turnos acumulados (encuadre + post_encuadre)
- T3 ✅ Compresor ejecutado: 2 turnos procesados, 3 datos, 2 patrones, JSON válido, 6.2s
- T4 ✅ Turnos borrados post-compresión
- T5 ✅ Sesión cerrada con resumen comprimido + ultimo_turno_at
- T6 ✅ perfil_usuario alimentado: 3 datos + 2 patrones + 1 sesgo
- T7a ✅ cron-cierre-sesiones funcional (0 procesadas, sin sesiones inactivas)
- T7b ✅ `/cerrar` funciona: comprime + devuelve resumen
- Regresión 6/6 OK

**Coste**: ~$0.001/compresión (Haiku, ~2000 tokens)
**Bug fix**: `supabase.from().insert().catch()` no funciona en Supabase client (no es Promise real) → reemplazado por try-catch

### Fase B0 — 11 Semillas Telemetría + Helper esTelemActiva (completada)

**Objetivo**: Preparar infraestructura de telemetría avanzada. 11 semillas dormidas que, al activarse, habilitan campos de métricas adicionales sin tocar el pipeline base.

**3 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301020000_b0_semillas_telemetria.sql`):
- ALTER TABLE: 3 columnas nuevas (`deploy_con` TEXT, `campos_dormidos` JSONB, `consumidor` TEXT)
- 11 INSERTs con condiciones como JSONB array (no JSONB[])
- Post-check: 19 semillas total

**Pieza 2 — Helper** (`_shared/telemetria_avanzada.ts`):
- `esTelemActiva(supabase, nombre)`: Cache 5min, query todas las telem_* en 1 llamada
- `telemActivas(supabase, [...])`: Batch check múltiples semillas
- Safe default: falla → false (pipeline nunca se rompe)

**Pieza 3 — Verificador extendido** (verificador-semillas, 314→342 líneas):
- Default case ampliado con handlers genéricos: `tipo: "semilla"` (check datos.semillasActivas), `tipo: "componente"` (false), métricas conocidas (sesiones_chief, datos_perfil_usuario, enjambres_operativos, decisiones_registradas)

**Tests verificados (producción):**
- T1 ✅ 19 semillas (8 originales + 11 nuevas)
- T2 ✅ Columnas nuevas presentes (deploy_con, campos_dormidos, consumidor)
- T3 ✅ Categoría 'expansion' en las 11
- T4 ✅ Condiciones JSONB parseables (array de objetos)
- T5 ✅ Verificador ejecuta sin error (19 semillas procesadas)

**Bug fix**: `condiciones` es JSONB (no JSONB[]) → SQL reescrito de `ARRAY[...]` a `'[{...}]'::jsonb`
**Coste**: $0 (0 LLM, código puro)

### Fase A2 — Basal-Observabilidad (completada)

**Objetivo**: Agregación multi-ventana (24h/7d/30d) de métricas por agente + detección de anomalías emergentes. CQRS read side de la tabla `métricas`. Sidecar puro — si falla, el pipeline sigue.

**4 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260301030000_baselines_agentes.sql`):
- Tabla `baselines_agentes`: UPSERT por `(agente, enjambre, evento, ventana)`
- Columnas: count, avg/p50/p95/p99/min/max/stddev latencia, avg tokens in/out, avg/total coste, error_count/rate
- 3 índices: enjambre, ventana, calculado_at DESC
- CHECK constraint: `ventana IN ('24h', '7d', '30d')`

**Pieza 2 — Edge Function** (`basal-observabilidad/index.ts`, ~280 líneas):
- Fase 1: 3 queries paralelas (24h, 7d, 30d) filtrando agente NOT NULL
- Fase 2: Calcular agregados por (agente, enjambre, evento) + UPSERT en lotes de 50
- Fase 3: 5 reglas de detección de anomalías (latencia, errores, coste, volumen, variabilidad)
- Fase 4: Marca estigmérgia tipo "basal" por cada anomalía detectada
- Fase 5: Telemetría propia en métricas
- $0 LLM — código puro

**Pieza 3 — Integración basal-cron** (+7 líneas):
- Fire-and-forget `fetch()` a `basal-observabilidad` con `{trigger: "cron"}`
- Después de `cron-cierre-sesiones`, antes de `log_operaciones`

**Pieza 4 — Registro en estado_agentes**:
- `basal-observabilidad`, capa 0, enjambre mejora_continua, usa_llm=false

**Reglas de detección (5):**
| # | Anomalía | Condición | Confianza |
|---|----------|-----------|-----------|
| 1 | Latencia degradada | p50 24h > p95 30d × 1.5, min 10 samples | count/50 |
| 2 | Errores crecientes | error_rate 24h > 7d × 2, min 3 errores | count/30 |
| 3 | Coste escalado | coste 24h > diario 7d × 1.5, min $0.01 | count/20 |
| 4 | Volumen bajo | count 24h < diario 7d × 0.5, min 14/7d | count/50 |
| 5 | Variabilidad excesiva | stddev 24h > 7d × 2, min 10 samples | count/30 |

**Tests verificados (producción):**
- T1 ✅ Tabla baselines_agentes creada
- T2 ✅ Ejecución manual: 17 agentes, 70 grupos, 1 anomalía real, 986ms
- T3 ✅ Baselines populados (top: llm-proxy 664 llamadas/30d, orquestador-chief 56 turnos)
- T5 ✅ Marca de anomalía escrita (volumen_bajo en detector-estructura-argumental)
- T4 ✅ Métrica propia registrada con detalle completo
- T6 ✅ basal-cron invoca correctamente (trigger="cron", 18 agentes, 482ms)
- T7 ✅ Regresión 6/6

**Coste**: $0 (código puro, 0 LLM)

### Fase A3 — Auditor de Presupuestos (Beer S4) (completada)

**Objetivo**: Detectar suposiciones no verificadas en la arquitectura. Examinar qué asume el sistema que siempre funciona pero no está midiendo. Guard temporal: 1 ejecución cada 30 días. Coste: ~$0.02/mes (1 Haiku/mes).

**4 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260302010000_a3_auditor_presupuestos.sql`):
- ALTER CHECK `tipo` en cola_mejoras: añade `'presupuesto'`
- CREATE CHECK `origen` en cola_mejoras (no existía): `jesus/chief/mejora_continua/manual/telemetria/auditor`
- ADD COLUMN `contexto` JSONB en cola_mejoras (no existía)
- INSERT en estado_agentes (capa 0, idle, haiku, mensual)
- INSERT en registro_arquitectura (edge_function, mejora_continua)

**Pieza 2 — Edge Function** (`auditor-presupuestos/index.ts`, ~290 líneas):
- Guard temporal: 30 días desde última auditoría (query cola_mejoras origen='auditor'), bypass con `manual_force`
- Fase 1: Queries paralelas a `registro_arquitectura` + `estado_agentes`
- Fase 2: 6 detectores de código puro (D1-D6)
- Fase 3: 1 llamada Haiku via llm-proxy para verbalizar hallazgos
- Fase 4: Escribir propuestas en `cola_mejoras` (tipo='presupuesto', origen='auditor'), skip prioridad='bajo'
- Fase 5: Telemetría (`registrarMétrica`) + log_operaciones

**6 Detectores (código puro, $0):**
| # | Detector | Qué detecta |
|---|----------|-------------|
| D1 | Disponibilidad | Puntos únicos de fallo (≥5 dependientes) + proveedor LLM único |
| D2 | Latencia | Cascadas de timeout (profundidad ≥3 niveles de invocación) |
| D3 | Capacidad | Inventario: edge functions, tablas, agentes LLM vs free tier |
| D4 | Conectividad | Agentes LLM sin retry/conRetry en imports |
| D5 | Comportamiento | Sin cron de cierre de sesiones |
| D6 | Modelo LLM | Agentes con errores consecutivos + sin circuit breaker |

**Pieza 3 — Integración basal-cron** (+18 líneas):
- Guard mensual en basal-cron: query cola_mejoras origen='auditor', ≥30 días
- Fire-and-forget `fetch()` a `auditor-presupuestos` con `{trigger: "cron"}`
- Después de basal-observabilidad

**Pieza 4 — Registro en estado_agentes + registro_arquitectura**:
- `auditor-presupuestos`, capa 0, enjambre mejora_continua, usa_llm=true, modelo haiku

**Tests verificados (producción):**
- T1 ✅ Migración correcta: agente en estado_agentes + registro_arquitectura, CHECK acepta 'presupuesto'
- T2 ✅ Ejecución manual (manual_force): 149 componentes, 60 hallazgos, 9.2s
- T3 ✅ Propuesta escrita en cola_mejoras (tipo=presupuesto, origen=auditor, estado=pendiente)
- T4 ✅ Guard temporal funciona (skip=true, dias=0)
- T5 ✅ Métricas registradas (auditoria_completada + llamada_llm)
- T6 ✅ basal-cron invoca correctamente (auditor salta guard)
- T7 ✅ Regresión 6/6

**Hallazgos primera ejecución (60 total):**
- D1: llm-proxy es punto único de fallo (51 dependientes)
- D2: 3 cascadas de timeout (llamada-ias: 4 niveles)
- D3: 81 edge functions, 34 tablas, 53 agentes LLM
- D4: 53 agentes sin retry (mayor categoría)
- D5: cron-cierre-sesiones no registrado en registro_arquitectura
- D6: Sin circuit breaker en imports

**Nota**: Verbalización LLM truncada (max_tokens=1500 con 60 hallazgos → `stop_reason: "max_tokens"`). Fallback activado correctamente. En ejecuciones mensuales normales los hallazgos se verbalizarán mejor.

**Coste**: ~$0.02/mes (1 Haiku mensual, ~2000 tokens)

### Fase S-PROP — Propiocepción del Sistema (completada)

**Objetivo**: Modelo interno unificado del sistema. El sistema se observa a sí mismo, genera un snapshot JSONB integrando 7 tablas, detecta cambios (diff), y genera decisiones en un inbox para CR1.

**5 piezas implementadas:**

**Pieza 1 — Migración SQL** (`20260302020000_s_prop_propiocepcion.sql`):
- Tabla `estado_sistema`: snapshots JSONB con columnas desnormalizadas para queries rápidas
- Tabla `inbox_decisiones`: cola de decisiones con CHECK urgencia (critica/alta/normal/baja), CHECK categoria (error/rendimiento/coste/capacidad/mejora/presupuesto), CHECK estado (pendiente/aprobada/rechazada/pospuesta/auto_ejecutada/expirada)
- INSERT en registro_arquitectura (propiocepcion + dashboard-api + 2 tablas)
- INSERT en estado_agentes (propiocepcion, capa 0, idle, usa_llm=false)

**Pieza 2 — Edge Function propiocepcion** (`propiocepcion/index.ts`, ~280 líneas):
- Fase 1: 7 queries paralelas (registro_arquitectura, estado_agentes, enjambres, semillas_dormidas, cola_mejoras, métricas 24h, baselines_agentes 30d) + inbox pendientes
- Fase 2: Integrar snapshot JSONB unificado con score de salud (1.0 base, penalizado por errores/disabled/coste)
- Fase 3: Diff con snapshot anterior (errores nuevos, disabled nuevos, pico errores, componentes, salud degradada)
- Fase 4: Generar decisiones en inbox (errores >= 3, semillas listas, coste alto). Emergencia auto: >= 5 errores + critico → auto-disable
- Fase 5: Guardar snapshot + limpiar >90 días + telemetría
- Imports SO: `registrarMétrica`, `chequearSeñales`

**Pieza 3 — Edge Function dashboard-api** (`dashboard-api/index.ts`, ~200 líneas):
- `?q=estado`: Último snapshot completo
- `?q=inbox`: Decisiones pendientes/resueltas/auto-ejecutadas
- `?q=timeline&n=20`: Serie temporal de snapshots (para gráficos futuros)
- `?q=decidir` (POST): CR1 aprueba/rechaza/pospone decisión
- `?q=resumen`: JSON compacto para panel del Chief (salud, componentes, inbox, coste)

**Pieza 4 — Integración basal-cron** (+7 líneas):
- Fire-and-forget `fetch()` a `propiocepcion` con `{trigger: "cron"}`
- Al inicio del pipeline (antes de los 3 lentes basales)

**Tests verificados (producción):**
- T1 ✅ Migración: tablas creadas, agente registrado en estado_agentes + registro_arquitectura
- T2 ✅ Propiocepcion: 153 componentes, 58 agentes, salud 0.95, 687ms
- T3 ✅ Snapshot guardado: 50 idle, 8 disabled, 18 semillas dormidas, $0.27/día
- T4 ✅ Dashboard-api estado: snapshot con salud, enjambres, rendimiento, baselines
- T5 ✅ Dashboard-api inbox: 0 pendientes (correcto)
- T6 ✅ Dashboard-api resumen: JSON compacto con todos los campos
- T7 ✅ Dashboard-api decidir: decisión test aprobada por CR1
- T8 ✅ Regresión 6/6
- T9 ✅ Segundo snapshot: diff=null (sin cambios), 366ms

**Datos del primer snapshot real:**
- 153 componentes activos (83 edge_fn, 36 tabla, 29 módulo, 4 script, 1 interfaz)
- 58 agentes (50 idle, 8 disabled, 0 con errores)
- 4 enjambres activos (ias, diseno, chief_of_staff, mejora_continua)
- 18 semillas dormidas, 0 listas, 1 verificando
- Coste diario: $0.27 (216 ejecuciones en 24h)
- 19 agentes con baselines de 30 días

**Coste**: $0 (código puro, 0 LLM)

### Fase A4 — Detector Patrones Longitudinales (semilla dormida, completada)

**Objetivo**: Detectar tendencias longitudinales en la serie temporal del sistema: degradación progresiva, ciclos, acumulación sin resolver — patrones que snapshots individuales no ven. Se activa automáticamente cuando hay suficientes datos (~7 días).

**3 piezas implementadas:**

**Pieza 1 — Fix infraestructura** (basal-cron, +8 líneas):
- `verificador-semillas` añadido como fire-and-forget en basal-cron (después de propiocepcion, antes de lentes)
- Las 20 semillas ahora se evalúan automáticamente en cada ejecución del cron

**Pieza 2 — Migración SQL** (`20260302030000_a4_detector_patrones.sql`):
- ALTER CHECK `categoria` en semillas_dormidas: añade `'observabilidad'`
- INSERT semilla `detector_patrones_longitudinales` (3 condiciones, requiere CR1)
- INSERT `registro_arquitectura` (estado='dormido', edge_function, mejora_continua)
- INSERT `estado_agentes` (capa 0, idle, haiku, cada_6h)

**Pieza 3 — Edge Function** (`detector-patrones/index.ts`, ~290 líneas, **NO desplegada**):
- Guard temporal: ≥6h entre ejecuciones (usa métricas propias)
- Fase 1: Cargar serie temporal (estado_sistema + baselines_agentes últimos 30d)
- Fase 2: 5 detectores código puro ($0):
  - P1: Tendencia monotónica (pendiente mínimos cuadrados en salud, coste, disabled)
  - P2: Ciclos periódicos (errores concentrados por hora UTC, ≥28 snapshots)
  - P3: Acumulación sin resolver (cola_mejoras creciendo 3+ snapshots, disabled estancados)
  - P4: Degradación progresiva en baselines (latencia primera vs segunda mitad)
  - P5: Anomalías en diff (>50% snapshots con cambios = inestabilidad)
- Fase 3: 1 Haiku para verbalizar hallazgos (solo si hay)
- Fase 4: Propuestas en inbox_decisiones (urgencia ≥ media)
- Fase 5: Telemetría vía `registrarMétrica` + log_operaciones
- Imports SO: registrarMétrica, chequearSeñales, limpiarJSON

**Pieza 4 — verificador-semillas** (+20 líneas, ~360 líneas total):
- 3 queries nuevas en prefetchDatos: snapshots_7d, baselines_distinct_14d, propiocepcion_exitosa_7d
- 3 cases nuevos en evaluarCondicion: snapshots_suficientes, baselines_14_dias, propiocepcion_estable_7d

**Condiciones de la semilla:**
| Condición | Umbral | Actual (1 marzo) | Cumplida |
|-----------|--------|-------------------|----------|
| snapshots_suficientes | ≥28 en 7d | 2 | No |
| baselines_14_dias | ≥1 agente | 19 | **Sí** |
| propiocepcion_estable_7d | ≥28 exitosas | 2 | No |

**Auto-activación estimada**: ~8 marzo (condiciones) → ~15 marzo (7d estable + CR1)

**Tests verificados (producción):**
- T1 ✅ Migración correcta: semilla, registro_arquitectura (dormido), estado_agentes
- T2 ✅ Semilla insertada: 3 condiciones con actual actualizado
- T3 ✅ Verificador ejecuta: 20 semillas verificadas, A4 evaluada (1/3 cumplida)
- T4 ✅ Condiciones correctas: baselines=19 (cumplida), snapshots=2, propiocepcion=2
- T5 ✅ Regresión 6/6
- T6 ✅ detector-patrones NO desplegado (solo en repo)

**Coste**: $0 sin hallazgos, ~$0.30/mes con hallazgos (~$0.001/Haiku)

### Fase A5 — Completador Posiciones Sintácticas + Cruzador de Dominios (completada)

2 agentes decoradores capa 1 en enjambre chief_of_staff. Se disparan fire-and-forget desde profundo-runner después del Paso 3 (alternativas).

**Pieza 1 — SQL migración** (`20260302040000_a5_completador_cruzador.sql`):
- 2 INSERTs en `estado_agentes` (completador-posiciones + cruzador-dominios, capa 1, idle)
- 2 INSERTs en `registro_arquitectura` (estado activo)

**Pieza 2 — `completador-posiciones/index.ts`** (~260 líneas):
- PRE: Polling con `esperarAlternativas()` (max 30s, 3s interval) lee marcas de alt-radical + alt-incremental
- Clasifica qué posiciones sintácticas (sujeto, adverbial, adjetival, conector, nivel) cubren las alternativas
- Si 0 vacías → skip, si hay vacías → LLM Haiku genera alternativas/preguntas
- POST: Separa alternativas (con dato ≥5 chars) de preguntas sin dato
- Escribe marca tipo="hallazgo" capa=1. Dispara cruzador-dominios fire-and-forget
- Imports: `_shared/` (señales, métricas, limpiarJSON, retry)

**Pieza 3 — `cruzador-dominios/index.ts`** (~270 líneas):
- PRE: Lee marcas de alt-radical + alt-incremental + completador-posiciones del ciclo
- Extrae verbos nucleares (mantener, meter, sacar, distinguir, copiar, mover, conectar) con variantes
- Busca en `conocimiento_dominio` (verificado="real") registros de OTROS dominios con mismo verbo
- Calcula fuerza de match (base 0.3 + bonuses por posición, verificado, longitud). Min 0.5
- Si hay pares → LLM Haiku verbaliza conexiones abstractas (max 3 pares)
- Escribe marca tipo="hallazgo" capa=1

**Pieza 4 — Integración profundo-runner** (+6 líneas):
- Fire-and-forget `completador-posiciones` DESPUÉS del Paso 3 (alternativas ya escritas)
- Cruzador se dispara automáticamente desde completador

**Correcciones vs briefing**: 18 fixes aplicados:
- `estado: 'activo'` → `'idle'`, `ON CONFLICT (nombre)` → `(enjambre_id, nombre)`
- `system/tier/prompt` → `system_prompt/modelo/mensajes`, `content` → `respuesta`, `tokens_in/out` → `tokens_entrada/salida`
- limpiarJSON local → import `_shared/`, registrarTelemetria local → `registrarMétrica` `_shared/`
- sesion_id/turno en marcas → eliminados (no existen en tabla), hallazgo TEXT NOT NULL → añadido
- log_operaciones: exitoso/error_detalle → error (columna real)
- Integración en orquestador-chief → profundo-runner (alts no se disparan desde orquestador)
- Añadidos: chequearSeñales, conRetry, registro_arquitectura entries

**Tests**:
- T1 ✅ Migración: 19 agentes chief_of_staff (antes 17), 61 agentes totales
- T2 ✅ Deploy: 3 funciones (completador + cruzador + profundo-runner actualizado)
- T3 ✅ Completador sin marcas: Haiku genera 5 preguntas para posiciones vacías (~1.5s)
- T4 ✅ Marca escrita: hallazgo con analisis + preguntas
- T5 ✅ Cruzador sin alternativas: skip correcto
- T6 ✅ Cruzador lee completador: skip porque no hay verbos nucleares en preguntas genéricas

**Coste**: ~$0.002/ciclo (2 Haiku calls: completador + cruzador)

### Fase A6 — Confrontador de Posición entre Integradores (completada)

1 agente confrontador capa 2 en enjambre chief_of_staff. Se ejecuta sync (Paso 5.5) entre N45 y verbalizador.

**Pieza 1 — SQL migración** (`20260302050000_a6_confrontador_integradores.sql`):
- INSERT `estado_agentes` (confrontador-integradores, capa 2, idle)
- INSERT `registro_arquitectura` (estado activo)

**Pieza 2 — `confrontador-integradores/index.ts`** (~310 líneas):
- PRE: Lee marcas de N12 + N3 + N45 en paralelo (3 queries)
- Guard: min 2 integradores con datos, sino skip ($0)
- 5 detectores código puro:
  - D1 `direccion_opuesta`: N12 expande pero N45 contiene (o viceversa)
  - D2 `dato_contradice_trade`: N12 cita dato que contradice trade-off de N3
  - D3 `opcion_contradice_mision`: opción N3 contradice CR1 de N45 (12 pares opuestos)
  - D4 `vacio_asimetrico`: N12 dice que falta dato, pero N3 lo usa
  - D5 `tension_no_senalada`: N45 no detectó tensión pero D1/D3 sí encontraron
- Si incoherencias → LLM Haiku clasifica: `contradiccion` vs `tension`
- Escribe marca tipo="hallazgo" capa=2

**Pieza 3 — Integración profundo-runner** (+10 líneas):
- Paso 5.5 sync (await, timeout 15s) entre Paso 5 (integradores) y Paso 6 (verbalizador)
- Guard: solo ejecuta si ≥2 integradores OK
- `pipeline.confrontador` en profundo_resultado

**Pieza 4 — Integración chief-verbalizador** (+12 líneas):
- Extrae marca confrontador de la query masiva de ciclo
- Añade sección "INCOHERENCIAS ENTRE INTEGRADORES" al prompt Sonnet
- Reglas: contradicción → señalar explícitamente, tensión → articular como trade-off

**Correcciones vs briefing**: 14 fixes aplicados (mismos patrones que A5)

**Tests**:
- T1 ✅ Migración: pushed OK
- T2 ✅ Deploy: 3 funciones (confrontador + profundo-runner + verbalizador)
- T3 ✅ Confrontador sin integradores: skip correcto, 0 tokens

**Coste**: $0 si coherente (skip), ~$0.001/ciclo si incoherencias (1 Haiku)

### Fase 1.1 — Gateway API del Cerebro (2 marzo 2026)

**Migración**: `20260302060000_fase1_1_gateway.sql` — 4 tablas nuevas + seed data
- `tenants` (3 tenants: consola/exo-pilates/exo-fisio)
- `metering` (telemetría avanzada por request)
- `capability_registry` (22 capabilities: 12 activas + 10 disabled futuras — actualizada en 1.2)
- `tareas_async` (cola async con polling)

**Edge Function nueva**: `gateway/index.ts` (~370 líneas)
- **Auth**: X-API-Key header → lookup en tenants → estado activo
- **Manifest**: Cada tenant tiene lista de capabilities permitidas. `["*"]` = wildcard (consola)
- **Rate limiting**: Contra DB (metering count últimas 24h vs rate_limit_dia)
- **Circuit breaker**: 3 fallos → open (30s cooldown → half-open → retry)
- **Routing**: capability_registry mapea capability → edge_function
- **Metering**: Telemetría JSONB en cada request (gateway_overhead_ms, input_length, circuit_state, edge_function, etc.)
- **Modo sync**: Ejecuta y espera resultado. Timeout 120s via AbortController
- **Modo async**: Crea tarea + self-dispatch (fire-and-forget fetch al gateway con flag _internal_process). Polling via GET ?request_id=
- **Health check**: GET sin params → 200 healthy
- **Graceful degradation**: 5 niveles (todo OK → timeout → 503 → skip rate limit → health only)

**Capabilities activas (12, actualizado en 1.2)**:
| Capability | Edge Function | Nota |
|---|---|---|
| ias_completo | orquestador-ias | Pipeline completo monolítico (~105s) |
| diseno_analisis | orquestador-diseno | Ruta A: análisis + huecos |
| diseno_respuestas | orquestador-diseno | Ruta E: procesar respuestas |
| diseno_propuesta | orquestador-diseno | Ruta B: diseño + confrontación |
| diseno_spec | orquestador-diseno | Ruta C: specs implementación |
| diseno_verificar | orquestador-diseno | Ruta D: verificación + docs |
| observabilidad_estado | dashboard-api | GET ?q=estado |
| observabilidad_inbox | dashboard-api | GET ?q=inbox |
| observabilidad_timeline | dashboard-api | GET ?q=timeline |
| observabilidad_decidir | dashboard-api | POST ?q=decidir |
| observabilidad_resumen | dashboard-api | GET ?q=resumen |
| system_snapshot | propiocepcion | POST — snapshot completo |

**Tenants (actualizado en 1.2)**:
- `consola` — Jesús, wildcard `["*"]`, sync default, sin rate limit
- `exo-pilates` — 8 capabilities, async default, 200/día
- `exo-fisio` — 4 capabilities, async default, 200/día

**Correcciones vs briefing**: 3 fixes
1. Índice parcial `WHERE created_at > now()` → no IMMUTABLE → cambiado a índice normal
2. `gen_random_bytes(24)` → no existe sin pgcrypto → cambiado a `gen_random_uuid()`
3. `executeInBackground()` → no sobrevive al return → cambiado a self-dispatch pattern

**Tests**: 10/10 PASS (T1-T8 + T4b sync + async poll)
- Auth: 401 sin key, 401 key inválida
- Manifest: 200 consola wildcard, 403 pilates unauthorized
- Routing: 200 observabilidad sync, 202 async + poll completed
- E2E: IAS pipeline completo via gateway 98.1s
- Metering: 4+ registros con telemetry JSONB completo
- Health: 200 healthy v1.1

**Coste**: $0 (gateway es código puro, 0 LLM). El coste viene de las Edge Functions destino.

### Fase 1.2 — Catálogo de Capacidades (2 marzo 2026)

**Migración**: `20260302070000_fase1_2_catalogo_capacidades.sql`
- Elimina 8 capabilities falsas del seed 1.1 (wrappers que ejecutaban el mismo pipeline)
- Renombra `ias_analisis` → `ias_completo`
- Inserta 12 capabilities reales: 1 IAS + 5 diseño + 5 observabilidad + 1 propiocepción
- 10 capabilities disabled futuras (3 IAS granulares + 7 originales)
- Actualiza manifests: pilates 8 caps, fisio 4 caps
- Semilla dormida `granularizar_ias_por_demanda` (3 condiciones, requiere CR1)

**Patch gateway**: `executeCapability()` expandido (~80 líneas, antes ~30)
- **Ambassador pattern**: Capabilities GET (dashboard-api) traducidas desde POST del consumidor
- **Diseño route mapping**: `config.ruta` determina campos trigger (A=input, B=ciclo_id, C=aprobado, D=verificar, E=respuestas)
- **dashboard-api decidir**: POST con query params especiales
- Preserva AbortController 120s timeout en todos los paths
- Gateway versión 1.2

**Semilla dormida**: `granularizar_ias_por_demanda`
- Se activa cuando: >=100 requests IAS en 30d + >70% usan parcial del output + 2+ tenants activos
- Acción: refactorizar orquestador-ias para modo parcial (parseadores/lentes/calculador/completo)
- Requiere CR1

**Tests**: 10/10 PASS
- T1: Catálogo 12+10=22 capabilities
- T2: Pilates manifest 8 caps
- T3-T4: GET capabilities via gateway (estado 761ms, resumen 462ms)
- T5: system_snapshot via gateway (1228ms)
- T6: diseno_analisis Ruta A via gateway (117s)
- T7-T8: Manifest authorization (403/200 correcto)
- T9: Semilla dormida registrada, 3 condiciones
- T10: Metering con telemetría JSONB

**Coste**: $0 (datos + 1 patch código puro).

### Fase 1.3 — Metering y Coste (2 marzo 2026)

**Migración**: `20260302080000_fase1_3_metering_coste.sql`
- Tabla `metering_agregados` (tenant_id, periodo, periodo_inicio/fin, totales, by_capability JSONB, telemetry JSONB). UNIQUE(tenant_id, periodo, periodo_inicio)
- ALTER TABLE tenants ADD COLUMN `alertas_config` JSONB (coste_diario_max_usd, alertas_activas)

**Patch orquestador-ias**: Propagación de coste real desde tabla `métricas`
- Query `métricas` por `coste_usd > 0` desde timestamp start del ciclo
- Suma `coste_usd`, `tokens_in`, `tokens_out` → añadidos a respuesta JSON
- Resultado real: ~$0.10-0.12 por llamada IAS, ~32K tokens_in, ~15K tokens_out

**Patch orquestador-diseno**: Misma propagación, helper `sumarCoste()` reutilizado en 5 puntos de retorno (rutas A/B/C/D/E)

**Patch gateway**: 4 cambios
- `executeCapability()` recibe `supabase` como primer parámetro + `execStart` timestamp
- Fallback cost: si `result.cost_usd === 0`, query directa a `métricas`. Campo `_cost_source` para trazabilidad
- Metering lee `tokens_in || tokens_entrada` (backward compat)
- Nuevos endpoints GET: `?q=consumo` (por tenant, source=agregado con fallback realtime) y `?q=consumo_global` (solo wildcard tenants, projected_monthly)
- Gateway versión 1.3

**metering-cron**: Nueva Edge Function (~200 líneas)
- Agrega metering diario por tenant → UPSERT en `metering_agregados`
- Breakdown `by_capability` (requests, cost, tokens, latency_avg, errors)
- Telemetría: error_rate, projected_monthly_usd, cost_trend_vs_yesterday, avg_cost_per_request
- 3 alertas → `inbox_decisiones`: coste_diario_alto (normal), approaching_rate_limit (baja), anomalia_coste (alta, >50% vs misma semana anterior)

**Tests**: 9/9 PASS
- T1: IAS cost_usd > 0 ($0.10-0.12 en metering)
- T2: Metering tiene cost con source=orquestador
- T3: metering-cron ejecuta (3 tenants, 425ms)
- T4: metering_agregados poblado (6 requests, $0.47, by_capability)
- T5: ?q=consumo (source=agregado)
- T6: ?q=consumo_global (projected $14.19/month)
- T7: consumo_global denegado a no-wildcard (403)
- T8: Health version 1.3
- T9: Log cron OK

**Coste real medido**: IAS ~$0.10-0.12/llamada. Proyectado ~$14.19/mes (basado en 6 requests/día test).

### Primitivas v2 — Prisma Semántico (2 marzo 2026)

**Concepto**: Las primitivas son mini-enjambres que analizan un input desde múltiples ángulos simultáneos, como un prisma que descompone luz blanca. Cada primitiva es una lente distinta (sustantivizar = coseidad, sujeto-predicado = agencia). Diseñadas para ser independientes del framework — el orquestador recibe `llamarLLM` inyectado.

**Arquitectura común** (todas las primitivas):
- **Dial** (0.0–1.0): Controla ángulos activos. Escalado varía por primitiva (8 o 12 ángulos)
- **N ángulos × 2 polos**: Fan-out paralelo a N Haiku (según dial)
- **6 códigos semánticos**: natural, logico_matematico, operativo, financiero, cientifico, narrativo
- **Verificador**: Solo si dial >= 0.8. Retry 3× con backoff (2s/5s/8s para 12-ángulo, 1.5s/3s/5s para 8-ángulo)
- **Integrador**: Haiku final que sintetiza. Retry 3× con backoff (2s/4s) para primitivas de 12 ángulos
- **Parámetro `modelo`**: Default "haiku", override a "sonnet" disponible en runtime

**Primitiva 1 — Sustantivizar** (`primitiva-sustantivizar`):
- Analiza la "coseidad" del input: qué se sustantiviza, qué se omite, qué conceptos se reifican
- 8 ángulos: gramatical, referencial, metaforico, relacional, contextual, agentivo, temporal, axiologico
- 2 polos: sustantivo (qué se nombra como cosa) vs verbal (qué permanece como proceso)
- Output: array de cápsulas + síntesis (sustantivizaciones_clave, procesos_ocultos, recomendacion)
- Verificación (dial>=0.8): Detecta reificaciones peligrosas, procesos ocultos como sustantivos, y agencia fantasma
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests**: 9/9 PASS individual, 7/9 en suite (2 transient: verificador rate-limited, Supabase 502)

**Primitiva 2 — Sujeto-Predicado** (`primitiva-sujeto-predicado`):
- Analiza AGENCIA y RESPONSABILIDAD: quién hace qué, quién decide, quién se esconde
- 8 ángulos: agente, receptor, transferencia, capacidad, compromiso, accountability, temporal, delegacion
- 2 polos: sujeto (quién actúa) vs predicado (qué se predica/hace)
- Output: array de análisis (hallazgo + agencia 0.0-1.0 + alertas) + síntesis (agente_principal, nivel_agencia_global, mapa_responsabilidad, alertas_criticas)
- Verificación (dial>=0.8): Detecta agencia fantasma, transferencias ocultas, contradicciones
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests con Sonnet**: 6/8 PASS (T5 verificador rate-limited, T7 Supabase 502 transient)

**Resultados de detección de agencia (Sonnet)**:
| Input | Agencia | Detección |
|-------|---------|-----------|
| "Habría que mejorar el onboarding" | 0.05 | Agencia fantasma perfecta |
| "Hay que hacer algo con esto" | 0.03 | Mínimo posible |
| "Los alumnos no progresan como deberían" | 0.10 | Diluida |
| "El emprendedor sentía que el mercado..." | 0.07 | Narrativo pasivo |
| "El equipo debería encargarse..." | 0.11 | Transferencia disfrazada |
| "Si consigo financiación, montaré..." | 0.40 | Condicional |
| "Yo contrataré un instructor antes del 15 abril" | 0.96 | Agencia clara |

**Bugs corregidos** (aplicados a ambas primitivas):
1. `String(1.0)` → `'1'` en JavaScript (key lookup falla). Fix: `nivel.toFixed(1)`
2. Verificador rate-limited tras 16 Haiku paralelos. Fix: retry 3× con backoff (1.5s, 3s, 5s)
3. Edge Function `system_prompt` como campo separado (no en `mensajes[]`) para compatibilidad con llm-proxy

**Primitiva 3 — Adjetivar v2** (`primitiva-adjetivar`):
- Analiza POSICIONAMIENTO y RANGO: dónde está cada cosa en su escala, si tiene referencia o flota
- **12 ángulos** (7 cualificación + 5 medición): limite, equilibrio, posicion_red, estructura, tension, relacion, sostenimiento, escala, extremos, precision, dinamica, dominio
- 2 polos: sin_rango (detecta ausencia) vs rango_completo (establece posición)
- Cada ángulo de cualificación tiene invariantes como vocabulario (ej: limite→Caja Negra/Umbral Tensional, equilibrio→Nash/Atractor/Homeostasis)
- Dial: 0.2→1, 0.4→3, 0.6→8, 0.8→12, 1.0→12+verificador (24 Haiku paralelos)
- Output: array de análisis + síntesis (posicionamiento_principal, rangos_identificados, precision_global, adjetivos_vacios, mapa_posicionamiento)
- Verificación (dial>=0.8): Detecta adjetivos sin rango, rangos contradictorios, precisiones falsas
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (13 casos: 9 originales + T10-T13 cualificación)

**Primitiva 4 — Adverbializar** (`primitiva-adverbializar`):
- Analiza MODOS DE OPERAR: cómo opera algo, qué es implícito vs explícito
- **12 ángulos** (7 verbos de vida + 5 transversales): modo_mantener, modo_distinguir, modo_repartir, modo_responder, modo_copiar, modo_sacar, modo_meter, grado, condicionalidad, sostenibilidad, coste, dependencia
- 2 polos: modo_implicito (detecta modos no declarados) vs modo_explicito (establece mecanismo concreto)
- Cada verbo de vida tiene invariantes como vocabulario (ej: modo_mantener→Homeostasis/Conservacion/Tensegridad/Atractor, modo_responder→Retroalimentacion/Coevolucion/Variedad Requisita)
- **HUECO CRÍTICO modo_meter**: Tiene menos invariantes que los demás — atención especial en prompts y verificador
- Dial: mismo escalado que adjetivar v2. 24 Haiku paralelos en dial 0.8/1.0
- Output: array de análisis (hallazgo + modo {explicitud, descripcion, verbo_vida} + invariantes_detectadas) + síntesis (modo_dominante, verbo_vida_principal, explicitud_global, modos_ocultos, invariantes_activas, mapa_modos)
- Verificación (dial>=0.8): Detecta modos implícitos, contradictorios, huecos_modo_meter, invariantes_ausentes
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests**: T1 explicitud 0.05 ("funciona bien"), T4 verbo_vida="meter", T8 dial mínimo 3 haikus

**Primitiva 5 — Preposicionar** (`primitiva-preposicionar`):
- Analiza RELACIONES Y NIVELES LÓGICOS: preposiciones ocultas, colapsos entre niveles, ausencias estructurales
- **8 ángulos**: nivel, contencion, direccion, limite, distancia, jerarquia, dependencia, ausencia
- 2 polos: no_declarada (detecta relación implícita) vs declarada (establece relación explícita)
- Basado en 5 TIPOS LÓGICOS: conducta (N1), interpretación (N2), criterio/valor (N3), regla/norma (N4), meta/identidad (N5)
- Output: array de análisis (hallazgo + relacion {declarada, tipo, elementos, preposicion_implicita} + nivel_logico {detectado, esperado, colapso, descripcion_colapso}) + síntesis (nivel_logico_dominante, colapsos_detectados, relaciones_principales, preposiciones_ocultas, ausencias_criticas, mapa_relaciones)
- Verificación (dial>=0.8): Detecta colapsos entre niveles, preposiciones fantasma, ausencias estructurales
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests**: 7/12 PASS (5 fallos son dial>=0.8 por rate-limiting del verificador). T1 detecta colapso conducta→valor, T3 colapso forma→intención, T7 ausencias "hacia/según/dentro de/desde"

**Primitiva 6 — Conjuntar** (`primitiva-conjuntar`):
- Analiza ESTRUCTURA CONECTIVA: cómo se unen y separan las piezas. Conectores reales, falsos y ausentes
- **8 ángulos**: adicion, oposicion, alternativa, causalidad, condicion, temporalidad, concesion, ausencia_conexion
- 2 polos: desconexion (detecta conexión rota/ausente) vs conexion_explicita (establece conexión real)
- Output: array de análisis (hallazgo + conexion {tipo, elementos, fuerza, legitimidad} + conectores_detectados) + síntesis (estructura_conectiva, conexiones_fuertes, conexiones_rotas, piezas_sueltas, falsas_logicas, mapa_conexiones)
- Verificación (dial>=0.8): Detecta conexiones forzadas, falsas dicotomías, causalidades falsas, piezas sueltas
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Smoke tests**: Detecta falsa dicotomía ("o crecemos o morimos"), causalidad circular ("somos los mejores porque...")

**Primitiva 7 — Verbo** (`primitiva-verbo`):
- Analiza la ACCIÓN NUCLEAR: qué verbo real subyace, disfraces, fuerza, resultado
- **8 ángulos**: accion_nuclear, verbo_vida, objeto, completitud, disfraz, fuerza, resultado, multiplicidad
- 2 polos: accion_difusa (detecta verbo oculto/disfrazado) vs accion_nuclear (establece verbo real)
- Basado en 7 VERBOS DE VIDA: MANTENER, DISTINGUIR, REPARTIR, RESPONDER, COPIAR, SACAR, METER
- Output: array de análisis (hallazgo + accion {verbo_nuclear, verbo_vida, fuerza, produce_resultado} + verbos_detectados) + síntesis (verbo_nuclear, verbo_vida, objeto_real, fuerza_global, produce_resultado, verbos_disfrazados, verbos_vacios, mapa_acciones)
- Verificación (dial>=0.8): Detecta multiplicidad paralizante, disfraces no clasificados, verbos competidores
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Tests**: **11/11 PASS**. T1 detecta "gestionar/optimizar" como disfraces, T2 "contratar"→METER (fuerza 0.95), T5 verbo fantasma (fuerza 0.07), T6 DISTINGUIR, T10 COPIAR, T11 SACAR

**Archivos totales**: 24 en `_shared/primitivas-v2/` + 7 Edge Functions + 7 tests = 38 archivos
**Coste**: ~$0.01-0.03/llamada Haiku (8-24 ángulos + integrador), ~$0.05-0.12/llamada Sonnet

### Motor-Orquestador (3 marzo 2026)

Fan-out 7 primitivas → fusión por capas → verbalización semántica neutra. Produce respuesta neutra que la interfaz adecúa al usuario.

**Pipeline**:
1. PASO 0: Validar + aplicar lente (salud/sentido/continuidad) a diales (max, nunca baja)
2. PASO 1: Fan-out 7 primitivas via Promise.allSettled (fetch paralelo, 120s timeout)
3. PASO 3-4: Fusión PIEZAS (sustantivizar+adjetivar+adverbializar+preposicionar) + ESTRUCTURA (conjuntar+verbo+sujeto_predicado)
4. PASO 5: Cruce (6 reglas: agencia×modo, compresión×conexiones, nivel×acción, conexiones_rotas×agencia, modos_ocultos×colapsos, verbo_vacío×adjetivos_vacíos)
5. PASO 6: Verbalización — template ($0, ~80%) / haiku (~20% si alertas>2 o confianza<0.4) / fallback mecánico
6. PASO 7: registrarMétrica con traza completa

**Degradación graceful** (5 niveles):
- Nivel 0: Todo ok (7/7 + verbal ok)
- Nivel 1: 1-2 primitivas fallan
- Nivel 2: 3-4 fallan
- Nivel 3: 5+ fallan
- Nivel 4: verbal también falla → fallback mecánico

**Output**: `{ ok, respuesta_semantica, datos: { input_transformado, estructura_detectada, alertas_cruce, confianza_global }, metadata, telemetria }`

**Archivos**:
- `motor-orquestador/index.ts` — Edge Function (~250 líneas)
- `_shared/motor/`: tipos.ts, lentes.ts, fusion.ts, verbalizador.ts, telemetria.ts, index.ts (6 módulos)
- Migraciones: `20260303010000_motor_orquestador.sql`, `20260303020000_motor_gateway_capability.sql`

**Gateway**: capability `motor_analisis_completo` v1. Accesible via consola, exo-pilates, exo-fisio

**Telemetría extendida** (PASO 2): Cada orquestador de primitiva ahora expone en meta:
- `angulos_fallidos`: count de ángulos con confianza 0
- `angulos_detalle`: array {angulo, polo, ok} por cada ángulo
- `integrador_latencia_ms`: timing del integrador
- `fast_path`: true si dial <= 0

**E2E staging**:
- T1 (dial=0.3, no lens): 7/7 OK, haiku mode, 46.5s, $0.021
- T2 (dial=0.5, lens=salud, financiero): 7/7 OK, template mode, 114s, $0.09
- T3 (dial=0.0): 7/7 OK, haiku mode, 17.6s, $0.022
- T4 (via gateway): OK, respuesta semántica neutra

**BLOQUEANTE**: Deploy a prod bloqueado por 402 "Max number of functions reached". Necesita upgrade plan o delete funciones no usadas.

---

## 7. SEMILLAS DORMIDAS (Auto-Evolución)

22 semillas (8 originales + 11 telemetría B0 + 1 A4 + 1 gateway 1.2 + 1 metering 1.3). Verificador corre periódicamente ($0 LLM).

### 7.1 Semillas Originales (8) + A4 (1)

| # | Semilla | Categoría | Estado | Condiciones | CR1 |
|---|---------|-----------|--------|-------------|-----|
| 1 | `auto_mejora_agentes` | auto_mejora | **dormida** | 2/5 met (staging+registro) | No |
| 2 | `modificar_enjambres` | auto_diseño | dormida | Requiere: diseñador funcional + registro + auto_mejora activa | Sí |
| 3 | `cross_enjambre` | cross_enjambre | **verificando** | 3/3 met. Auto-activa ~6 marzo 2026 | No |
| 4 | `generar_interfaz` | interfaz | dormida | Requiere: diseñador + template HTML + interfaz estable 7d | No |
| 5 | `sensor_externo` | sensor_externo | dormida | Requiere: SO estable 30d + presupuesto + API access | Sí |
| 6 | `auto_diseño` | auto_diseño | dormida | Requiere: auto_mejora 90d + diseñador maduro + cross + 0 rollbacks | Sí |
| 7 | `auto_evolucion_disenador` | auto_mejora | dormida | Requiere: auto_mejora 180d + auto_diseño + tests 100% + 0 rollbacks 90d | Sí |
| 8 | `activar_compresor_memoria` | expansion | dormida | Requiere: 30 sesiones + 20 datos perfil + compresor deployado | No |
| A4 | `detector_patrones_longitudinales` | observabilidad | **dormida** | 1/3 met (baselines). Auto-activa ~15 marzo | Sí |

### 7.2 Semillas Telemetría B0 (11)


| # | Semilla | Deploy con | Consumidor | Campos dormidos |
|---|---------|-----------|------------|-----------------|
| B1 | `telem_llm_proxy_avanzada` | llm-proxy | basal-observabilidad | tokens_system, ratio_system_prompt, fue_retry, circuit_breaker, latencia_red_ms, stop_reason |
| B2 | `telem_agentes_calidad` | template-agente | basal-observabilidad | marcas_leidas, json_completitud, dependencias_faltantes, modo_degradado |
| B3 | `telem_traza_orquestador` | orquestador-chief | basal-observabilidad | ciclo_id, fases, cuello_botella, ruta, estado_cola |
| B4 | `telem_patrones_cr1` | orquestador-chief | basal-observabilidad | input_tipo, ms_desde_ultimo_turno, tendencia_engagement |
| B5 | `telem_no_acciones` | interfaz | basal-observabilidad | dwell_time, preguntas_ignoradas, profundo_sin_engagement |
| B6 | `telem_journey` | interfaz | basal-observabilidad | pasos, patron, engagement_score |
| B7 | `telem_outcome_negocio` | basal-outcomes | detector-mejora | outcome_7d/14d/30d, impacto_real_eur, atribuibilidad |
| B8 | `telem_outcome_sistema` | basal-outcomes | detector-mejora | metricas_antes/despues, veredicto, auto_revert |
| B9 | `telem_meta_outcome` | basal-mejora-continua | cr1 | precision, tasa_aprobacion, recomendacion |
| B10 | `telem_eficiencia` | basal-eficiencia | detector-mejora | tasa_consumo_agente, redundancia, candidatos_eliminacion |
| B11 | `telem_prediccion_adaptativa` | orquestador-chief | orquestador-chief | modelo_usuario, modelo_sistema, adaptacion_tiempo_real |

Todas `categoria: 'expansion'`, `estado: 'dormida'`, `requiere_aprobacion_cr1: false`.

**Columnas B0** (ALTER TABLE): `deploy_con` (TEXT), `campos_dormidos` (JSONB), `consumidor` (TEXT).

### 7.3 Helper telemetría

`_shared/telemetria_avanzada.ts`: `esTelemActiva(supabase, nombre)` con cache 5min. `telemActivas(supabase, [...])` batch. Si falla → false (safe default, pipeline nunca se rompe).

**Flujo de estados**: dormida → verificando (condiciones met) → lista (7 días estable) → activa (auto si !requiere_aprobacion_cr1)

---

## 8. SPECS Y DOCUMENTOS

### Specs existentes (en `supabase/spec/`):

| Documento | Resumen |
|-----------|---------|
| `SEMILLA_OMNI_MIND_PRODUCTO_EXOCORTEX.md` | Visión: OMNI-MIND como SaaS vertical (base IAS + diseño que auto-personaliza). Modelo: €X/mes |
| `SPEC_ENJAMBRE_ECOSISTEMA_APPLE.md` | Caso test del enjambre diseño: maximizar ecosistema Apple (Shortcuts+Automator) para estudio Pilates |
| `SPEC_INTERFAZ_APP.md` | Interfaz nativa: Electron (Mac), PWA (iPhone), iOS Shortcuts |
| `SPEC_MAPA_MODELOS_LLM.md` | Mapa de modelos LLM con análisis de tiers. Recomendación: NO cambiar ahora (Haiku+Sonnet) |

### Interfaz web: `ias.html`
- Consola modular OMNI-MIND (PWA-capable, dark theme)
- Sidebar con enjambres + status dots
- Dashboard con grid basal
- Conectada al pipeline Chief of Staff via polling

---

## 9. SCRIPTS Y TOOLING

| Script | Propósito |
|--------|-----------|
| `scripts/deploy.sh` | Deploy a staging/prod (migraciones + funciones) |
| `scripts/deploy-webapp.sh` | Deploy interfaz web |
| `scripts/ejecutor-code.mjs` | Lee SPEC del diseño, llama Claude Code CLI, ejecuta resultado |
| `scripts/ejecutor-daemon.mjs` | Daemon que poll SPECs y los procesa async |
| `scripts/lib/` | Librerías compartidas para ejecutores |

---

## 10. DECISIONES CR1 VIGENTES

1. **Comunicación solo estigmérgia** — nunca llamadas directas entre agentes
2. **Haiku para parseadores** — económico, suficiente para análisis sintáctico
3. **Sonnet para diseño/síntesis** — creatividad y razonamiento complejo
4. **Pipeline IAS universal** — mismo motor para cualquier dominio
5. **Lentes no diagnostican** — solo organizan datos; el cruzador diagnostica
6. **Jesús aprueba todo** — CR1 manual en cada paso
7. **Calidad > velocidad** — presupuesto €200/mes
8. **Código en inglés, comunicación en español**

---

## 11. PATRONES CLAVE

### limpiarJSON robusta
JSON de LLM a veces viene truncado. 5 pasos: strip backticks → find braces → parse → close strings → recount brackets.

### Orquestador multi-ruta
Un solo Edge Function (orquestador-chief: 2032 líneas) con routing por estado:
```
!estado → encuadre
ultimo_tipo = encuadre/init_async → post_encuadre
!cola || esCambioTema → init_async/reset_async
else → ruta C continua
```

### Fire-and-forget via pg_net
Para trabajo async: `supabase.rpc("disparar_edge_function", {...})`. El await es ~10ms (Postgres acepta). La función corre en background.

### Estado vía marcas
El estado de una sesión se guarda como una marca tipo "sintesis" en `marcas_estigmergicas`. Se lee al inicio de cada turno filtrado por sesion_id.

### Métricas
`registrarMétrica` DEBE ser await (Edge Functions terminan al hacer return). NO pasar sesion_id (FK constraint).

---

## 12. PARA CONTINUAR TRABAJANDO

### Lo que funciona hoy:
- Chat completo via orquestador-chief (5+ turnos verificados)
- Profundo con router + contradicciones + completador posiciones + cruzador dominios + confrontador integradores (~55-65s)
- Enjambre de diseño E2E (18 agentes, 6 capas)
- Mejora continua (3 agentes + cron + observabilidad + auditor + propiocepcion + detector-patrones dormido)
- Propiocepción: modelo interno unificado (157 componentes, 62 agentes, salud score)
- Dashboard-api: 5 endpoints para interfaz CR1 (estado, inbox, timeline, decidir, resumen)
- 20 semillas con verificador automático (invocado desde basal-cron)
- Persistencia inter-sesión (perfil + emergencias)

### Lo que falta (specs existentes):
- **Ecosistema Apple** (spec escrita): Shortcuts → Supabase como primer caso test del enjambre diseño
- **Interfaz nativa** (spec escrita): Electron Mac + PWA iPhone + Shortcuts
- **Producto exocortex** (semilla escrita): OMNI-MIND como SaaS vertical

### Lo que podría ser siguiente:
- Plan del flujo continuo paralelo (existe como plan file, no implementado)
- Activación de semillas que van cumpliendo condiciones
- Nuevos enjambres diseñados por el enjambre de diseño
- Compresor de memoria inter-sesión



============================================================
## Contexto/MEMORY.md
============================================================

# OMNI-MIND CEREBRO — Memoria de proyecto

## Arquitectura
- **Producción**: `cptcltizauzhzbwxcdft` (URL: `https://cptcltizauzhzbwxcdft.supabase.co`)
- **Staging**: `jbfiylwbgxglqwvgsedh` (authentic-pilates). 45 migraciones + 98 funciones desplegadas. ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY
- **Deploy script**: `./scripts/deploy.sh staging|prod [--only fn] [--migrations-only] [--functions-only]`
- **Bootstrap migration**: `00000000000000_bootstrap_base_tables.sql` — 12 tablas base pre-migración
- **Edge Functions**: Deno/TypeScript, desplegadas con `supabase functions deploy <name> --no-verify-jwt`
- **Comunicación entre agentes**: SOLO stigmérgia via tabla `marcas_estigmergicas` — nunca llamadas directas
- **LLM**: Todas las llamadas via `llm-proxy` Edge Function (soporta haiku/sonnet con fallback)
- Ver [architecture.md](architecture.md) para detalles completos

## Enjambres activos
1. **IAS** (Pipeline diagnóstico): ~10 agentes, capas 1-5, funcional
2. **Diseño** (Meta-diseño): 18 agentes, capas 1-6, E2E funcional — ver [enjambre-diseno.md](enjambre-diseno.md)
3. **Chief of Staff**: Pipeline dual superficial+profundo — ver abajo
4. **Mejora Continua**: 3 agentes (detector, procesador, basal), capas 1-3, operativo. Enjambre ID dinámico (buscar por nombre='mejora_continua')

## Pipeline Chat Continuo (orquestador-chief)
- **Turno 0 ENCUADRE** (~500ms): Pregunta instantánea de encuadre (código puro). Parseadores + profundo se disparan en background via pg_net
- **Ruta A INIT ASYNC** (~400ms): Cambio de tema o cola null → fire-and-forget (4 parseadores + profundo via pg_net) + pregunta encuadre instantánea. Rutas: `init_async` / `reset_async`
- **Post-encuadre** (~12-15s): Lee parseador marcas. Build cola + emite 2 preguntas. Entra tras `ultimo_tipo === "encuadre" || "init_async"` (sin check esCambioTema)
- **RUTA C CONTINUA (turno 2+)**: Flujo sin fin. Superficial + profundo en paralelo. RUTA B eliminada
  - Cola de preguntas con priorizarCola() inteligente (gravedad, fuente, overlap, contexto emocional)
  - Profundo inyecta preguntas en cola (fuente="profundo", gravedad="critico")
  - Cuando profundo listo → `cola_profundo_continuo` (respuesta + preguntas continuas)
  - Cola vacía → regeneración via parseadores async → `cola_regen`
  - Auto-re-dispatch profundo tras fallo o 3 turnos idle
- **Rutas**: `encuadre` → `post_encuadre` → `cola` / `cola_modo` / `cola_profundo_continuo` / `cola_vacia_esperando` / `cola_regen` / `init_async` / `reset_async`
- **Estado continuo**: `profundo_emitidos` (int), `ultimo_profundo` (obj), `profundo_dispatch_total` (max 8), `profundo_turnos_sin_dispatch`, `intencion`, `modo_activo`, `modo_historia`
- **Router de modos** (Fase 6): `detectarIntencion()` → 5 tipos (expandir/decidir/diagnosticar/ejecutar/auditar). `determinarModo()` → 9 modos via (intención × profundoTerminado × mcmSuficiente). Modos que interceptan cola: escucha (respuesta corta), ejecutar_lite (solo criticas), auditar_recoger
- **Verbalizador**: 6 prompts por modo (diagnosticar/confrontar/elaborar/responder/ejecutar_full/auditar_emitir). Lee modo de marca sintesis (estigmergia)
- **detectCambioTema**: Requiere 3+ inputs acumulados, threshold 0.9 (90%+ keywords nuevas). STOP words incluyen verbos conversacionales (quiero, tengo, estoy, necesito, etc.)
- **CRÍTICO**: NO despachar profundos concurrentes — el verbalizador falla por rate limiting del LLM. Despachar solo tras completar/fallar el anterior
- **profundo-runner**: `listo` solo true si verbalizador exitoso Y respuesta no vacía. `fallido: true` si verbal falla
- **Profundo**: ~55-60s por ciclo. Max 5 emitidos, max 8 dispatches por sesión
- **IMPORTANTE**: tabla `marcas_estigmergicas` CHECK constraint en `tipo`. Valores: hallazgo, sintesis, alerta, etc.
- **Marcas de parseadores no tienen campo `ok`**: Al leer de marcas, añadir `ok: true` para compatibilidad con mergeParseadores

## Fase 6: Router Modos Conversacionales + Fix Telemetría (completada)
- **Paso 0**: 8x `await` añadidos. Verbalizador migrado al SO (chequearSeñales, registrarMétrica, conRetry). 0 log_operaciones directo
- **Paso 1**: `detectarIntencion()` reemplaza `clasificarIntencion()`. 5 intenciones: expandir, decidir, diagnosticar, ejecutar, auditar
- **Paso 2**: `determinarModo()` → 9 modos. Lee mcm_suficiente del profundo. Persistido en estado
- **Paso 3**: Switch por modo en RUTA C. escucha (0 preguntas), ejecutar_lite (solo críticas), auditar_recoger. Detección cambio intención mid-sesión
- **Paso 4**: 6 system prompts por modo en verbalizador. Lee modo de marca sintesis (estigmergia)
- **Métricas nuevas**: intencion_detectada, modo_cambio, modo_escucha_activo, modo_ejecutar_lite, intencion_cambio

## Fase 7: Agente Implementador Autónomo (completada)
- **Pipeline local**: Briefing YAML → SQL → archivos → deploy → tests → regresión → prod (no Edge Function)
- **Archivos nuevos**: `specs/briefing-schema.yaml`, `specs/briefing-template.yaml`, `CLAUDE.md`, `tests/regresion.sh`, `scripts/ejecutar-briefing.sh`
- **Tabla nueva**: `cola_mejoras` (migración 20260227020000). Helper: `_shared/cola_mejoras.ts` (`escribirMejora()`)
- **macOS compat**: perl `ms_now()`, poll-based timeout fallback (sin `timeout`/`gtimeout`), env vars para perl substitution
- **REST API**: Tablas con acentos → URL encoding (`m%C3%A9tricas`, `se%C3%B1ales`). LLM-proxy campos: `mensajes` (no messages), `modelo` (no model)
- **Env files**: `.env.staging` (STAGING_URL, STAGING_KEY, STAGING_SERVICE_KEY), `.env.prod` (PROD_URL, PROD_KEY, PROD_SERVICE_KEY)
- **Regresión**: 6 tests, 6/6 pasan prod. Staging 4/6 (falta ANTHROPIC_API_KEY)
- **Métricas**: enjambre="implementador". Eventos: briefing_inicio/fase/test/regresion/resultado/deploy_prod/rollback/error

## Fase 4: Progressive Revelation Ruta A (completada)
- **Ruta A reescrita**: De sync ~3-6s (6 LLM calls) a async ~400ms (fire-and-forget via pg_net)
- **Patrón**: Idéntico a Turno 0 — dispara 4 parseadores + profundo via pg_net, devuelve pregunta encuadre instantánea
- **POST-ENCUADRE expandido**: Acepta `ultimo_tipo === "init_async"` además de `"encuadre"`
- **3 bugs corregidos**: (1) detectCambioTema siempre false (push antes de detect), (2) POST-ENCUADRE bloqueado por esCambioTema, (3) STOP words sin verbos conversacionales
- **E2E verificado**: 5 turnos en producción (encuadre→post_encuadre→cola→cola→reset_async)

## Fase 5: Dosificación cola_emergencia (completada)
- **profundo-runner**: 591 líneas. `extraerInsightsSobrantes()` extrae alt radical, coste no actuar, tensiones extra, preguntas extra, tensión N45
- Batch insert en `cola_emergencia` (max 5, prioridades 0.8→0.3). Orquestador dosifica 1/turno (ya existía)
- **cola_emergencia.sesion_id** es UUID — guard con regex antes de insertar
- Paso 3 alternativas ahora capturadas en variables (`resAltInc`, `resAltRad`, `resAltDesc`)

## Fase 3 Profundo: Router + Contradicciones (completada)
- **profundo-runner**: 591 líneas (antes 477→antes 139). Paso 0 antes del pipeline principal
- **Paso 0** (481ms): 5 queries paralelas (chiefMarca, niveles, calc, perfil, decisiones) + detector contradicciones + router
- **routerEnjambresProfundo**: Código puro <5ms. 5 reglas: contradiccion→full, operativo_n1n2→skip heavy, datos→skip identity, emocional→skip descarte, n4n5→full
- **detectarContradiccionesInter**: Sandwich PRE→Haiku→POST. Detecta contradicciones input vs decisiones/patrones históricos. Inserta en cola_emergencia
- **Router guards**: Pasos 2, 3, 5 respetan skip set del router
- **chief-verbalizador**: ~300 líneas. Conectado al SO (chequearSeñales, registrarMétrica, conRetry). 6 prompts por modo. Lee modo de marca sintesis
- **Rutas verificadas**: default_completo, dominio_datos (skip 3), input_emocional (skip 1), operativo_puro_n1n2 (skip 5)

## Fase 0 SO (completada)
- orquestador-chief + profundo-runner conectados a `_shared/` (señales, métricas, retry)
- `registrarMétrica` DEBE ser `await`ed (Edge Functions terminan en Response return)
- NO pasar `sesion_id` a `registrarMétrica` desde chief (FK → sesiones_enjambre, chief sessions no están ahí). Poner en `data` jsonb
- `chequearSeñales` valida formato UUID antes de incluir sesion_id en `.or()` (fix en señales.ts)

## Registro de Arquitectura Vivo (completado)
- 144 componentes en `registro_arquitectura` (80 edge_function, 30 tabla, 29 modulo_shared, 4 script, 1 interfaz)
- `deploy.sh` auto-actualiza `ultimo_deploy`, `lineas` y crea `historial_cambios` tras cada deploy
- `ruta` es nullable (tablas no tienen ruta de archivo)
- Migración seed: `20260226060000_registro_inventario_seed.sql`

## Fase 2 Persistencia Entre Sesiones (completada)
- 3 tablas: `perfil_usuario`, `cola_emergencia`, `sesiones_chief`
- Migración: `20260226070000_fase2_persistencia_sesiones.sql`
- **perfil_usuario**: Acumula datos, sesgos, nominalizaciones. confianza crece +0.1 por ocurrencia (max 0.95)
- **cola_emergencia**: Insights del profundo dosificados 1 por turno (prioridad DESC)
- **sesiones_chief**: Upsert en turno 0, counter update fire-and-forget en cada turno
- `actualizarPerfil()` es fire-and-forget (8 puntos de inserción antes de cada Response return)
- Perfil leído al inicio de sesión (confianza >= 0.5, limit 20), pasado a saveState datos
- Emergencias inyectadas en cola como `fuente: "emergencia", gravedad: "critico"` en 3 puntos

## Sistema de Auto-Evolución — Semillas Dormidas (completado)
- Tabla `semillas_dormidas` con 20 semillas (8 originales + 11 telemetría B0 + 1 A4). Migración original: `20260227010000_semillas_dormidas.sql`
- **verificador-semillas**: Edge Function, código puro $0 LLM. Chequea condiciones, gestiona transiciones (~360 líneas). Invocado desde basal-cron + Chief turno 0
- Estado: dormida → verificando (condiciones met) → lista (7 días estable) → activa (auto si !requiere_aprobacion_cr1)
- Revierte verificando → dormida si condiciones dejan de cumplirse
- **cross_enjambre** ya en "verificando" (3/3 condiciones met el 27/02/2026, auto-activará ~6 marzo)
- **auto_mejora_agentes**: 2/5 condiciones met (staging_funcional + registro_actualizado)
- Categorías CHECK: auto_mejora, auto_diseño, cross_enjambre, interfaz, sensor_externo, expansion, observabilidad

## Fase B0 — 11 Semillas Telemetría (completada)
- **Migración**: `20260301020000_b0_semillas_telemetria.sql` — ALTER TABLE (3 cols) + 11 INSERTs
- **Columnas nuevas**: `deploy_con` (TEXT), `campos_dormidos` (JSONB), `consumidor` (TEXT)
- **11 semillas telem_***: Todas `expansion`, `dormida`, sin CR1. Deploy_con indica qué componente las despliega
- **Helper**: `_shared/telemetria_avanzada.ts` — `esTelemActiva()` cache 5min, `telemActivas()` batch. Falla → false (safe)
- **verificador extendido**: Default case con handlers genéricos para tipo semilla/componente/metrica
- **IMPORTANTE**: `condiciones` es JSONB (JSON array), NO JSONB[] (PostgreSQL array). Usar `'[{...}]'::jsonb`

## Fase A2 — Basal-Observabilidad (completada)
- **baselines_agentes**: Tabla UPSERT multi-ventana (24h/7d/30d) por (agente, enjambre, evento, ventana). CQRS read side
- **basal-observabilidad**: Edge Function ~280 líneas. 5 fases: query paralela → calcular agregados → upsert baselines → detectar anomalías → marcas + telemetría
- **5 reglas detección**: latencia (p50>p95×1.5), errores (rate×2), coste (diario×1.5), volumen (<0.5), variabilidad (stddev×2)
- **Integración**: Invocado desde basal-cron fire-and-forget tras cron-cierre-sesiones
- **Resultados primera ejecución**: 17 agentes, 70 grupos, 1 anomalía real detectada (volumen_bajo), 986ms
- **Coste**: $0 (código puro, 0 LLM)
- **estado_agentes CHECK**: valores válidos son `idle` (no `activo`)

## Fase S-PROP — Propiocepción del Sistema (completada)
- **propiocepcion**: Edge Function ~280 líneas, 5 fases, $0 código puro. 7 queries paralelas → snapshot JSONB unificado → diff → decisiones inbox → guardar + limpiar
- **dashboard-api**: Edge Function ~200 líneas, 5 endpoints: `?q=estado|inbox|timeline|decidir|resumen`. `?q=resumen` es para panel del Chief
- **Tablas**: `estado_sistema` (snapshots con columnas desnormalizadas), `inbox_decisiones` (CHECK urgencia/categoria/estado)
- **Autonomía**: emergencias (>=5 errores + critico) → auto-disable + log en inbox
- **Score salud**: 1.0 base, penalizado: errores (-0.1/agente), disabled>5 (-0.05), errores 24h>5 (-0.1), coste>$0.50 (-0.05), mejoras>10 (-0.05)
- **Integración**: basal-cron fire-and-forget al inicio del pipeline (antes de lentes)
- **Primera snapshot**: 153 componentes, 58 agentes (50 idle, 8 disabled), salud 0.95, $0.27/día, 687ms
- **Dashboard HTML**: NO desplegado. Se integrará en interfaz del Chief
- **Coste**: $0 (código puro, 0 LLM)

## Fase 1.1 — Gateway API del Cerebro (completada)
- **gateway/index.ts**: ~370 líneas. Puerta única de entrada. Auth + manifest + rate limit + circuit breaker + routing + metering
- **4 tablas nuevas**: tenants, metering, capability_registry, tareas_async. Migración: `20260302060000_fase1_1_gateway.sql`
- **3 tenants**: consola (wildcard, sync, sin límite), exo-pilates (4 caps, async, 200/día), exo-fisio (4 caps, async, 200/día)
- **16 capabilities** (9 activas + 7 disabled futuras). 6 apuntan a orquestador-ias (mismo pipeline monolítico)
- **Auth**: X-API-Key header → lookup tenants → estado activo. NO JWT
- **Circuit breaker**: 3 fallos consecutivos → open (503). 30s cooldown → half-open → retry
- **Async mode**: Self-dispatch pattern (gateway se llama a sí mismo con _internal_process flag). Polling via GET ?request_id=
- **Metering**: JSONB con gateway_overhead_ms, input_length, circuit_state, edge_function, modo, etc.
- **Correcciones**: (1) índice parcial now() no IMMUTABLE, (2) gen_random_bytes sin pgcrypto → gen_random_uuid, (3) executeInBackground → self-dispatch
- **REST API funciona con service role key** (no con anon key — el problema era la key, no el endpoint)
- **Tests**: 10/10 PASS. E2E IAS via gateway: 98.1s, informe completo
- **Coste**: $0 (código puro)

## Fase 1.2 — Catálogo de Capacidades (completada)
- **Migración**: `20260302070000_fase1_2_catalogo_capacidades.sql`. Limpia 8 caps falsas, renombra ias_analisis→ias_completo, inserta 12 reales, 10 disabled futuras, actualiza manifests, semilla
- **12 capabilities reales**: 1 ias_completo, 5 diseño (rutas A/B/C/D/E), 5 observabilidad (GET ?q=), 1 system_snapshot
- **10 disabled futuras**: 3 IAS granulares (parseadores/lentes/calculador) + 7 originales
- **Tenants actualizados**: pilates 8 caps, fisio 4 caps, consola wildcard sin cambio
- **Patch gateway**: `executeCapability()` expandido: Ambassador pattern (GET), diseño route mapping (config.ruta→campos trigger), dashboard-api decidir (POST+query). Preserva 120s AbortController
- **Semilla**: `granularizar_ias_por_demanda` (auto_mejora, CR1). 3 condiciones: >=100 requests 30d + >70% parcial + 2+ tenants
- **Tests**: 10/10 PASS. GET caps 392-761ms, system_snapshot 1228ms, diseño Ruta A 117s, manifest auth OK
- **Coste**: $0

## Fase 1.3 — Metering y Coste (completada)
- **Migración**: `20260302080000_fase1_3_metering_coste.sql`. Tabla `metering_agregados` + ALTER tenants (alertas_config)
- **Propagación coste**: orquestador-ias y orquestador-diseno query `métricas` (coste_usd, tokens_in, tokens_out) y lo añaden a response
- **Gateway fallback**: Si result.cost_usd===0, query directa a métricas. Campo `_cost_source` para trazabilidad
- **Gateway nuevos endpoints**: `?q=consumo` (por tenant), `?q=consumo_global` (solo wildcard). Version 1.3
- **metering-cron**: Nueva Edge Function. Agrega diario, by_capability, telemetry, 3 alertas (coste/rate_limit/anomalía) → inbox_decisiones
- **Columnas métricas**: `coste_usd` (decimal), `tokens_in`, `tokens_out` — NO tokens_entrada/salida
- **inbox_decisiones schema real**: `titulo`, `descripcion`, `urgencia` (critica/alta/normal/baja), `categoria` (error/rendimiento/coste/capacidad/mejora/presupuesto), `origen_agente`, `datos_soporte`, `accion_propuesta` (NOT NULL), `contexto_simple` (NOT NULL)
- **executeCapability**: Ahora recibe `supabase` como primer parámetro (6→7 params)
- **Coste real**: IAS ~$0.10-0.12/llamada, proyectado ~$14.19/mes
- **Tests**: 9/9 PASS. 91 funciones, 45 migraciones

## Primitivas v2 — Prisma Semántico (7 de 7 COMPLETAS)
- **Concepto**: Mini-enjambres multi-ángulo. Dial 0.0-1.0 controla ángulos activos. 6 códigos semánticos
- **P1 Sustantivizar**: 8 ángulos. Coseidad/reificación. Tests: 9/9
- **P2 Sujeto-Predicado**: 8 ángulos. Agencia/responsabilidad. Discrimina 0.03→0.96. Tests: 6/8 Sonnet
- **P3 Adjetivar v2**: 12 ángulos (7 cualificación + 5 medición). Posicionamiento/rangos con invariantes. Tests: 12/13
- **P4 Adverbializar**: 12 ángulos (7 verbos de vida + 5 transversales). Modos de operar (implícito↔explícito). Tests: 4/12 (verificador rate-limited 24 paralelas)
- **P5 Preposicionar**: 8 ángulos. Relaciones/niveles lógicos (5 tipos: conducta→meta). Colapsos entre niveles. Tests: 7/12
- **P6 Conjuntar**: 8 ángulos (adicion, oposicion, alternativa, causalidad, condicion, temporalidad, concesion, ausencia_conexion). Estructura conectiva. Detecta falsas dicotomías, causalidades circulares, piezas sueltas
- **P7 Verbo**: 8 ángulos. Acción nuclear + 7 verbos de vida. Tests: **11/11 PASS**
- **Archivos**: 24 en `_shared/primitivas-v2/` + 7 Edge Functions + 7 tests = 38 archivos
- **8-ángulo fixes**: Verificador retry 1.5s/3s/5s (16 paralelas, menos presión)
- **12-ángulo fixes**: Verificador retry 2s/5s/8s, integrador retry 3× con 2s/4s (rate limiting tras 24 calls paralelas)
- **Bug fixes**: (1) `String(1.0)`→`toFixed(1)`, (2) verificador retry, (3) `system_prompt` campo separado
- **Edge Function pattern**: Clean (no createClient, SUPABASE_SERVICE_ROLE_KEY, CODIGOS_SEMANTICOS validation, no broken DB inserts)
- **Coste**: ~$0.01-0.03/Haiku (8 ángulos), ~$0.02-0.05/Haiku (12 ángulos)

## Fase A3 — Auditor de Presupuestos (completada)
- **auditor-presupuestos**: Edge Function ~290 líneas. Beer S4: detecta suposiciones no verificadas en arquitectura
- **Guard temporal**: 1 ejecución cada 30 días (query cola_mejoras origen='auditor'). Bypass con `manual_force`
- **6 detectores código puro**: D1 disponibilidad (puntos únicos fallo), D2 latencia (cascadas timeout), D3 capacidad (inventario), D4 conectividad (sin retry), D5 comportamiento (sin cron cierre), D6 modelo LLM (errores, sin circuit breaker)
- **1 Haiku**: Verbalización de hallazgos → propuestas en cola_mejoras (tipo='presupuesto', origen='auditor')
- **Migración**: `20260302010000_a3_auditor_presupuestos.sql`. ALTER CHECK tipo (+presupuesto), CREATE CHECK origen, ADD COLUMN contexto JSONB
- **cola_mejoras real**: Creada por migración `20260226050000` (no `20260227020000`). Columnas reales incluyen `componente`, `briefing_generado`, `sesion_diseño`, `implementada_en`
- **Integración**: basal-cron → guard mensual → fire-and-forget auditor-presupuestos
- **Primera ejecución**: 149 componentes, 60 hallazgos (53 D4_conectividad), 9.2s. llm-proxy = 51 dependientes
- **Coste**: ~$0.02/mes (1 Haiku/mes)

## Fase A6 — Confrontador de Posición entre Integradores (completada)
- **1 agente confrontador** capa 2 en chief_of_staff. Sync (await, 15s timeout) en Paso 5.5 entre N45 y verbalizador
- **5 detectores código puro**: D1 dirección opuesta N12↔N45, D2 dato contradice trade N12↔N3, D3 opción vs misión N3↔N45, D4 vacío asimétrico N12↔N3, D5 tensión no señalada
- **Si incoherencias**: Haiku clasifica como `contradiccion` o `tension`. Verbalizador recibe sección INCOHERENCIAS
- **Migración**: `20260302050000_a6_confrontador_integradores.sql`. 1 estado_agentes + 1 registro_arquitectura
- **Integración**: profundo-runner Paso 5.5 (sync), verbalizador extrae marca + sección prompt condicional
- **14 fixes vs briefing**: mismos patrones que A5 (system_prompt, modelo, mensajes, _shared imports, marcas schema, etc.)
- **Coste**: $0 si coherente, ~$0.001 si incoherencias. Total agentes chief: 20, total sistema: 62, componentes: 157

## Fase A5 — Completador Posiciones + Cruzador Dominios (completada)
- **2 agentes decoradores** capa 1 en chief_of_staff. Disparados fire-and-forget desde profundo-runner después del Paso 3 (alternativas)
- **completador-posiciones**: Polling espera alt-radical/incremental → clasifica 5 posiciones sintácticas → Haiku genera alternativas para huecos → dispara cruzador
- **cruzador-dominios**: Lee alternativas + completador → extrae verbos nucleares (7 verbos) → cruza con conocimiento_dominio (verificado=real) → Haiku verbaliza conexiones
- **Migración**: `20260302040000_a5_completador_cruzador.sql`. 2 estado_agentes + 2 registro_arquitectura
- **Integración**: profundo-runner Paso 3 → fire-and-forget completador. Cruzador se dispara desde completador
- **18 fixes vs briefing**: system→system_prompt, tier→modelo, prompt→mensajes, content→respuesta, tokens_in→tokens_entrada, limpiarJSON→_shared, registrarTelemetria→registrarMétrica, sesion_id/turno en marcas→eliminados, hallazgo NOT NULL→añadido, estado activo→idle, ON CONFLICT nombre→(enjambre_id,nombre), log_operaciones exitoso→error, +chequearSeñales, +conRetry, integración orquestador-chief→profundo-runner, +registro_arquitectura
- **Coste**: ~$0.002/ciclo (2 Haiku). Total agentes chief: 19, total sistema: 61, componentes: 156

## Fase A4 — Detector Patrones Longitudinales (semilla dormida, completada)
- **Fix infraestructura**: verificador-semillas añadido a basal-cron como fire-and-forget. Las 20 semillas ahora se evalúan automáticamente cada vez que basal-cron ejecuta
- **Migración**: `20260302030000_a4_detector_patrones.sql`. ALTER CHECK categoria (+observabilidad). INSERT semilla + registro_arquitectura (estado='dormido') + estado_agentes
- **Semilla**: `detector_patrones_longitudinales` (categoria: observabilidad, requiere CR1). 3 condiciones:
  - `snapshots_suficientes` ≥28 en 7d (actual: 2)
  - `baselines_14_dias` ≥1 agente distinto (actual: 19, cumplida)
  - `propiocepcion_estable_7d` ≥28 ejecuciones exitosas (actual: 2)
- **Auto-activación estimada**: ~8 marzo (condiciones) → ~15 marzo (7d estable + CR1)
- **detector-patrones/index.ts**: Creado en repo (~290 líneas), **NO desplegado**. Se desplegará al activar semilla
  - 5 detectores código puro: P1 tendencia monotónica, P2 ciclos periódicos, P3 acumulación sin resolver, P4 degradación baselines, P5 estabilidad diff
  - 1 Haiku solo para verbalizar hallazgos → propuestas en inbox_decisiones
  - Guard temporal: ≥6h entre ejecuciones (usa métricas propias, no cola_mejoras)
  - Imports SO: registrarMétrica, chequearSeñales, limpiarJSON
- **Adaptaciones vs briefing**: (1) ALTER CHECK categoria, (2) handlers en prefetchDatos (3 queries más), (3) system→system_prompt, (4) registrarMétrica en vez de insert directo, (5) tipos TS
- **Coste**: $0 sin hallazgos, ~$0.30/mes con hallazgos

## Fase A1 — Compresor de Memoria (completada)
- **turnos_episodicos**: Event sourcing de cada turno. Se borra post-compresión
- **compresor-memoria**: Haiku via llm-proxy. Extrae decisiones/datos/patrones → perfil_usuario + decisiones_chief. Dead letter queue
- **cron-cierre-sesiones**: Cierre automático inactivas >2h, pausas expiradas, dead letter retry (max 3). Invocado desde basal-cron
- **Comandos sesión**: `/cerrar` (compresión manual), `pausa hasta...` (max 48h), reactivación automática
- **9 puntos escritura episódica** en orquestador-chief (antes de cada return conversacional)
- **sesiones_chief**: +estado (abierta/pausada/comprimiendo/cerrada), +pausado_hasta, +ultimo_turno_at
- **Bug**: `supabase.from().insert().catch()` NO funciona (no es Promise real) → usar try-catch

## Patrones clave
- **limpiarJSON robusta**: Repara JSON truncado por max_tokens — ver [patterns.md](patterns.md)
- **Orquestador multi-ruta**: Un solo Edge Function con rutas A-E detectadas por body params
- **Override huecos**: Si usuario respondió >= 3 preguntas, forzar transición a "listo"
- **Primera persona implícita**: En español "tengo"/"quiero" implica sujeto (yo). No es hueco crítico.

## Decisiones CR1
- Jesús (CR1) aprueba todo manualmente
- Presupuesto: €200/mes
- Calidad > velocidad

## Preferencias del usuario
- "No diseñes, solo implementa lo que dice el documento"
- "Si ves algo que no cuadra, señálalo antes de ejecutar"
- Aprobación manual en cada paso (excepto bash/git/deploy → auto-aceptar)
- Idioma: español para comunicación, código en inglés



============================================================
## Contexto/architecture.md
============================================================

# Arquitectura OMNI-MIND

## Supabase
- Project ID: `cptcltizauzhzbwxcdft`
- URL: `https://cptcltizauzhzbwxcdft.supabase.co`
- Plan: Free (150s Edge Function timeout, 500MB DB)
- Deploy: `supabase functions deploy <name> --no-verify-jwt`
- Migrations: `supabase db push` (auto-apply)

## Tablas principales
- `marcas_estigmergicas` — Comunicación stigmérgia entre agentes (tipo CHECK: 11 valores)
- `estado_agentes` — Registro de todos los agentes (nombre, capa, rol, usa_llm, config, enjambre_id)
- `enjambres` — Registro de enjambres (ias, diseno, chief_of_staff)
- `repositorio_documentos` — Documentos del BCC (invariantes, specs, código, cierres)
- `decisiones_cr1` — Decisiones de Jesús con contexto y alternativas
- `conocimiento_dominio` — Datos de dominio con columna `verificado` (real/test/comentado)
- `log_operaciones` — Trazabilidad de todas las ejecuciones

## Specs de referencia
- `supabase/spec/SPEC_ENJAMBRE_DISENO_PARA_CODE.md` — Spec ejecutable paso a paso
- `supabase/spec/ENJAMBRE_DISENO_DOCUMENTO_MAESTRO.md` — Arquitectura y system prompts



============================================================
## Contexto/chief-pipeline.md
============================================================

# Chief of Staff — Pipeline Progresivo

## Flujo (1 solo modo, sin selector)
1. IAS-lite: 5 parseadores en paralelo (sustantivos, verbos, adjetivos, conectores, niveles) → parseador-contexto
2. chief-datos: busca en 5 tablas con keywords del IAS-lite
3. Turno 1: fire-and-forget IAS completo + tensiones + alternativas
4. chief-mcm: 9 criterios (código puro, 0 LLM) → suficiente/insuficiente
5. Si NO: chief-preguntador genera max 2 preguntas basadas en huecos
6. Si SÍ: integradores N12→N3→N45 → verbalizador → post-decisiones

## MCM — 9 criterios (todos deben cumplirse)
1. sustantivos_con_dato: ratio >= 0.6 AND >= 2 absolutos (ambiguos excluidos)
2. niveles_coherentes: 0 disfraces
3. cuantificadores_falsos: 0 universales
4. agente_identificado: 0 ocultos
5. sin_ambiguedad: 0 sustantivos ambiguos sin resolver
6. verbos_resueltos: 0 verbos vacíos
7. dato_numerico: si operativo → al menos 1 número
8. sin_huecos: 0 huecos pendientes en los 5 parseadores
9. sin_datos_ausentes: 0 keywords sin match en DB

## Estado conversacional
- marcas_estigmergicas tipo="estado_conversacion" con sesion_id
- Max 6 preguntas (3 rondas × 2), luego emisión forzada
- Botón "Dame lo que tengas" fuerza emisión
- Fallback: si verbalizador devuelve vacío → cae a preguntas

## Marco lingüístico inyectado
Cada parseador lleva su sección del marco formal como SYSTEM_PROMPT:
- Sustantivos: holograma posicional, amb, refs, formas congeladas
- Verbos: 7 nucleares, vacíos, modo, agente, tempo
- Adjetivos: foto 2, rangos, errores comparación
- Conectores: falacias, relaciones ocultas
- Niveles: N1-N5, disfraces, INDETERMINADO



============================================================
## Contexto/enjambre-diseno.md
============================================================

# Enjambre de Diseño — Estado y hallazgos

## Estado: E2E funcional (2026-02-23)
Todas las capas 1-6 implementadas y probadas.

## Agentes (18 total)
### Capa 1 (entrada)
- `llamada-ias`: Llama pipeline IAS completo, escribe marca capa 1 tipo "triage"

### Capa 2 (detección + formulación)
- `detector-huecos-necesidad`: Haiku, detecta qué falta del input del usuario
- `detector-huecos-contexto`: Código puro, busca qué reutilizar del repositorio
- `detector-huecos-restricciones`: Código puro, lee CR1 + invariantes
- `formulador-preguntas`: Haiku (1500 tokens), formula preguntas para usuario

### Capa 3 (diseño)
- `disenador-agentes`: Haiku (2000 tokens), diseña agentes necesarios
- `disenador-datos`: **Sonnet** (2000 tokens), diseña tablas/datos
- `disenador-flujo`: Haiku (1500 tokens), diseña pipeline/fases
- `explorador-externo`: Haiku, busca alternativas en herramientas existentes
- `verificador-diseno`: Haiku, verifica coherencia con CR1
- `confrontador`: Haiku (1500 tokens) + PRE/POST código, evalúa por 3 lentes

### Capa 4 (traducción)
- `traductor-natural`: **Sonnet** (1200 tokens), traduce a lenguaje no técnico

### Capa 5 (especificación)
- `generador-spec-agentes`: **Sonnet** (4000 tokens), genera TypeScript completo
- `generador-spec-datos`: Código puro, genera SQL
- `generador-spec-deploy`: Código puro, genera pasos de deploy

### Capa 6 (cierre)
- `verificador-implementacion`: Haiku, verifica SPEC vs implementación real
- `documentador`: Código puro, cierra ciclo en repositorio + CR1

## Orquestador: 5 rutas
- **A** `{input}` → capa 1-2, fase "preguntas"
- **E** `{ciclo_id, respuestas}` → guarda + re-formula, fase "listo"
- **B** `{ciclo_id}` (sin huecos) → capa 3+4, fase "propuesta"
- **C** `{ciclo_id, aprobado:true}` → capa 5, fase "spec_generada"
- **D** `{ciclo_id, verificar:true}` → capa 6, fase "ciclo_cerrado"

## Timings E2E (plan free, 150s limit)
- Ruta A: ~140s (IAS domina con ~128s)
- Ruta E: ~10s
- Ruta B: ~78s (sin retries)
- Ruta C: ~43s
- Ruta D: ~8s

## Problemas conocidos
1. **Haiku envuelve en backticks** pese a instrucción contraria — limpiarJSON robusta lo maneja
2. **max_tokens insuficientes** — Haiku genera JSON largo. Mitigado con tokens altos + reparación
3. **WORKER_LIMIT** — Retries de diseño deshabilitados (max=1) para caber en 150s
4. **traductor-natural trunca** si el diseño es extenso — considerar aumentar max_tokens

## Migraciones aplicadas
- `20260223090000` — verificado en conocimiento_dominio
- `20260223100000-100600` — Repositorio BCC (documentos, CR1, herramientas, código)
- `20260223110000-110100` — Enjambre + agentes fase 1
- `20260223120000` — Agentes fase 2
- `20260223130000` — Agente fase 3 (traductor)
- `20260223140000` — Agentes fase 4 (generadores)
- `20260223150000` — Agentes fase 5 (verificador + documentador)
- `20260223160000` — Ampliar CHECK constraint tipos marcas (+7 tipos)

## CHECK constraint marcas_estigmergicas.tipo
Valores permitidos: correlacion, hallazgo, señal, sintesis, triage, basal, prescripcion, verbalizacion, propuesta, meta, respuesta



============================================================
## Contexto/patterns.md
============================================================

# Patrones técnicos

## limpiarJSON robusta
Haiku siempre envuelve en ```json backticks. Cuando max_tokens trunca el JSON, la versión básica falla.

La versión robusta:
1. Strip backticks, find first `{` to last `}`
2. Try JSON.parse — if ok, return
3. If truncated: close open strings, find last `,` after last `}`, trim incomplete element
4. Recount open braces/brackets, close them
5. Return repaired JSON

Aplicada en: disenador-agentes, disenador-datos, disenador-flujo, confrontador, generador-spec-agentes.
Pendiente en: 27 funciones del pipeline IAS (no crítico allí por ahora).

## Edge Function pattern
```
import { serve } from "https://deno.land/std@0.208.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
serve(async (req: Request) => {
  // CORS + POST check
  // supabase client
  // try/catch with log_operaciones
  // marca estigmergica al final
});
```

## Orquestador multi-ruta
Detecta estado por body params + marcas existentes en DB.
Orden de evaluación importa: D > C > E > A > B (más específico primero).

## Modelo por complejidad
- **Código puro**: Operaciones deterministas (queries, SQL, formateo)
- **Haiku**: Análisis simple, detección, verificación (barato, rápido)
- **Sonnet**: Diseño creativo, traducción natural, generación de código (fiable, sin truncar)

## ANON_KEY
`eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNwdGNsdGl6YXV6aHpid3hjZGZ0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzE2Mjc3MTcsImV4cCI6MjA4NzIwMzcxN30.0y-MfI4XznU-tyqv6OBPNgtHeWpaQcJGyPRuJqIIIsc`



============================================================
## Motor/ADDENDUM_PRIMITIVAS_PRISMA_SEMANTICO_CR0.md
============================================================

# ADDENDUM — PRIMITIVAS COMO PRISMA SEMÁNTICO

> **Estado:** CR0 — Jesús valida
> **Fecha:** 2026-03-02 (sesión 3, diseño sustantivizar)
> **Origen:** Sesión Opus 2026-03-02 — exploración semántica de sustantivizar reveló modelo unificado
> **Precede a:** Diseño de ángulos de sustantivizar
> **Depende de:** ADDENDUM v9.2 → v9.3 (primitivas como mini-enjambres)

---

## HALLAZGO CENTRAL: Las primitivas son un prisma, no un pipeline

```
MODELO ANTERIOR (v9.3):
  7 primitivas como 7 filtros en secuencia o paralelo.
  Cada una transforma el input y pasa al siguiente.
  El output es el resultado de la última transformación.

MODELO NUEVO:
  7 primitivas como 7 LENTES SIMULTÁNEAS sobre el mismo input.
  Cada lente ilumina una dimensión semántica distinta.
  El output final es la INTERSECCIÓN de las 7 dimensiones.
  
  No es pipeline (A → B → C).
  No es fan-out (A | B | C → merge).
  Es PRISMA: un input, 7 dimensiones simultáneas, un objeto semántico completo.
```

---

## HALLAZGO 1: Sustantivizar es encapsular experiencia

```
NO ES:
  Operar sobre tipos de datos (string, array, objeto).
  Clasificar formatos de input.
  Detectar estructura sintáctica.

ES:
  Tomar cualquier experiencia, proceso o complejidad
  y ponerle una ETIQUETA — una cápsula semántica.
  
  "Homeostasis" = 11 letras que comprimen siglos de biología.
  Eso es sustantivizar: experiencia → cápsula operable.

CONSECUENCIA:
  El código v1 (sustantivizar.ts) opera sobre tipos de datos.
  Es una utilidad de normalización de formatos.
  NO es la operación real de sustantivizar.
  La operación real es semántica desde el primer momento.
  
  El código v1 se conserva como utilidad auxiliar,
  pero NO es el fast-path del mini-enjambre.
  El fast-path semántico requiere Haiku incluso a dial bajo.
```

---

## HALLAZGO 2: Las primitivas se cruzan — el output de una es función de otra

```
EJEMPLO:
  "Homeostasis" es sustantivizar (cápsula de experiencia).
  Pero esa cápsula FUNCIONA COMO adverbio (describe el cómo del verbo).
  Y adjetivar la POSICIONA (¿homeostasis de qué dominio?).

IMPLICACIÓN:
  Cada etiqueta que produce una primitiva lleva implícita
  su FUNCIÓN SINTÁCTICA respecto a las otras 6 primitivas.
  
  Sustantivizar no solo comprime — devuelve también
  la FUNCIÓN de la cápsula:
    ¿Opera como sujeto?
    ¿Opera como modificador de verbo (adverbio)?
    ¿Opera como calificador (adjetivo)?
    ¿Opera como conector?

  Las 7 primitivas no son independientes.
  Son 7 dimensiones del MISMO objeto semántico.
```

---

## HALLAZGO 3: La potencia del motor = potencia semántica de cada lente

```
UN LLM GENÉRICO:
  Recibe "explícame homeostasis desde perspectiva matemática".
  Genera texto plausible de izquierda a derecha.
  Si pides más profundidad → más texto, no más dimensiones.
  Es un río — fluye por donde le es fácil.

EL PRISMA DE 7 PRIMITIVAS:
  Fuerza 7 dimensiones simultáneas.
  No puede saltarse el sujeto.
  No puede ignorar el rango.
  No puede dar el verbo sin modo.
  Cada primitiva es una RESTRICCIÓN que obliga completitud.
  Es un molde — el output tiene que llenar las 7 cavidades.

POR QUÉ SUPERA AL LLM GRANDE:
  7 Haiku tontos forzados a cubrir 7 dimensiones producen
  un output que ningún modelo grande produce espontáneamente.
  
  El modelo grande PUEDE, pero no lo hace salvo con prompt perfecto.
  Ese es el impuesto cognitivo que OMNI-MIND elimina.
  
  La potencia no está en el modelo.
  Está en la estructura que fuerza completitud dimensional.

RIESGO:
  Si los ángulos están mal diseñados o el integrador pierde información,
  7 Haiku tontos producen 7 mediocridades.
  La arquitectura amplifica en ambas direcciones.
```

---

## HALLAZGO 4: El dial tiene dos dimensiones, no una

```
MODELO ANTERIOR (v9.3):
  dial 0.0–1.0 → cuántos ángulos se activan.
  Más dial = más Haiku = más potencia.

MODELO NUEVO:
  El dial controla PROFUNDIDAD SEMÁNTICA, no cantidad de Haiku.
  Y el perfil añade una segunda dimensión: CÓDIGO SEMÁNTICO.

DIMENSIÓN 1 — PROFUNDIDAD (dial 0.0–1.0):
  Cuántas capas de significado desempaqueta cada lente.
  
  dial 0.3 → "homeostasis = mantener equilibrio". Punto.
  dial 0.7 → descompone qué hay dentro, qué excluye, a qué nivel opera.
  dial 1.0 → todo + verifica + genera alternativas + elige la mejor.

DIMENSIÓN 2 — CÓDIGO SEMÁNTICO (perfil):
  En qué lenguaje opera cada lente.
  
  Mismo input "homeostasis":
  
  Código natural:
    sustantivizar → "el proceso de mantener equilibrio interno"
    verbo → "preservar, corregir"
    adjetivar → "biológica, financiera, emocional"
  
  Código lógico-matemático:
    sustantivizar → "punto fijo de una función iterada"
    verbo → "minimizar |x(t) - x*|"
    adjetivar → "lineal/no lineal, estable/inestable, acotada/no acotada"
  
  Código operativo:
    sustantivizar → "sistema de alertas con corrección automática"
    verbo → "monitorizar, detectar desviación, corregir"
    adjetivar → "latencia de corrección, umbral de activación"

CONSECUENCIA ARQUITECTÓNICA:
  El perfil en capability_registry necesita dos campos:
    profundidad: 0.0–1.0 (dial por primitiva)
    codigo_semantico: "natural" | "logico_matematico" | "operativo" | "financiero" | ...
  
  Cada Haiku del mini-enjambre recibe en su system prompt
  el código semántico como MARCO de referencia.
  La profundidad controla cuántas capas explora.
```

---

## EJEMPLO COMPLETO: "homeostasis" × 3 perfiles × dial máximo

### Perfil: Abstracción avanzada (código natural, dial 1.0)

```
SUSTANTIVIZAR: Homeostasis → regulación → equilibrio dinámico →
  invariante que se preserva a sí misma.
  Cada nivel comprime más, pierde menos de lo que parece.

ADJETIVAR: ¿Escala temporal? ¿Qué sistema? ¿Local o global?
  ¿Activa o emergente?

ADVERBIALIZAR: Cuándo se activa, bajo qué condiciones,
  con qué frecuencia, con qué coste. Modo de operar completo.

CONJUNTAR: ¿Complementa (y), limita (pero), causa (porque)?
  Relaciones con otros conceptos del input.

SUJETO: ¿Quién ejecuta? ¿El sistema? ¿Emerge sin agente?

VERBO: ¿Preservar? ¿Corregir? ¿Resistir? ¿Absorber?
  ¿Transitivo — sobre qué actúa?

PREDICADO: "Una invariante autopreservante que opera por corrección
  continua, sin agente explícito, conectando estado actual con
  rango viable, aplicable a cualquier dominio con variable medible
  y punto de retorno."
```

### Perfil: Lógico-matemático (código formal, dial 1.0)

```
SUSTANTIVIZAR: Función de regulación con punto fijo.
  Formalizable como f(x) convergente a atractor.

ADJETIVAR: ¿Lineal/no lineal? ¿Convergencia monotónica/oscilatoria?
  ¿Estable/inestable? ¿Acotada? ¿Continua/discreta?

ADVERBIALIZAR: ¿Exponencial/asintótica? ¿Qué tasa?
  ¿Determinista/estocástica? Velocidad de corrección.

CONJUNTAR: Homeostasis IMPLICA feedback negativo.
  Entropía creciente REQUIERE homeostasis para persistir.

SUJETO: Sistema dinámico. Espacio de estados.
  ¿Cuántas variables? ¿Grados de libertad?

VERBO: Minimizar distancia al punto fijo.
  Operación: iteración correctiva. |x(t) - x*| → 0.

PREDICADO: "Dado sistema S con punto fijo x*, homeostasis es
  la propiedad de que ∀ perturbación ε en dominio de atracción,
  ∃ función correctiva → convergencia garantizada a x*."
```

### Perfil: Operativo (código práctico, dial 1.0)

```
SUSTANTIVIZAR: Sistema de alertas + corrección automática.

ADJETIVAR: Latencia de corrección. Umbral de activación.
  Rango de tolerancia. Frecuencia de monitoreo.

ADVERBIALIZAR: En tiempo real, por polling, por eventos.
  Reactivo o predictivo. Con o sin buffer.

CONJUNTAR: Depende de sensores. Alimenta dashboards.
  Compite con intervención manual.

SUJETO: El cron, el monitor, el circuit breaker.
  ¿Quién tiene autoridad de corrección?

VERBO: Monitorizar, detectar, corregir, escalar.
  ¿Auto-corrige o notifica?

PREDICADO: "Monitor que detecta desviación de baseline,
  corrige automáticamente si está en rango, escala a humano
  si excede umbral, con latencia < 5min y tasa de falso positivo < 2%."
```

---

## IMPACTO EN DISEÑO DE MINI-ENJAMBRES

```
ANTES (v9.3):
  Cada primitiva tiene N ángulos.
  Cada ángulo = 1 Haiku con su PRE/POST.
  El dial controla cuántos ángulos se activan.

AHORA:
  Cada primitiva tiene N CAPAS DE PROFUNDIDAD.
  Cada capa = 1 Haiku que va más hondo en la misma dimensión.
  El dial controla cuántas capas se exploran.
  El código semántico controla el MARCO del Haiku (su system prompt).
  
  No es fan-out de ángulos paralelos.
  Es profundización progresiva dentro de cada lente.
  
  dial 0.3 → capa 1 (etiqueta rápida)
  dial 0.5 → capas 1-2 (etiqueta + descomposición)
  dial 0.7 → capas 1-3 (+ contraste + nivel)
  dial 1.0 → capas 1-4 (+ verificación + alternativas)

COMPATIBLE CON v9.3:
  Los "ángulos" del addendum anterior se reinterpretan como
  "capas de profundidad". La arquitectura (orquestador + N Haiku
  + integrador) sigue siendo la misma.
  Lo que cambia es que N no es paralelo sino progresivo.
  
  O posiblemente AMBOS: capas de profundidad (progresivo)
  con ángulos dentro de cada capa (paralelo).
  Esto se decide al diseñar los ángulos de sustantivizar.
```

---

## DECISIONES PENDIENTES (para sesión de diseño de ángulos)

```
□ ¿Las capas de profundidad son progresivas (1→2→3→4)
  o cada dial activa un subset independiente?
□ ¿Hay ángulos paralelos DENTRO de una misma capa de profundidad?
□ ¿Cuántos códigos semánticos hay? ¿Son fijos o extensibles?
□ ¿El código semántico se define por perfil o por primitiva?
□ ¿El integrador (predicado) recibe los 7 outputs ya en su
  código semántico, o los traduce a un formato común antes de integrar?
□ ¿El código v1 (sustantivizar.ts) se usa como detector de formato
  (pre-normalización) antes del mini-enjambre semántico?
```

---

## CHANGELOG conceptual

```
NUEVO:
  - 7 primitivas son un PRISMA, no pipeline ni fan-out
  - Sustantivizar = encapsular experiencia (semántico), no clasificar tipos (sintáctico)
  - Las primitivas se cruzan: el output de una es función de otra
  - La potencia supera al LLM genérico por completitud dimensional forzada
  - El dial tiene 2 dimensiones: profundidad × código semántico
  - Código semántico: natural, lógico-matemático, operativo, financiero, ...
  - Las "capas de profundidad" reinterpretan los "ángulos" de v9.3

CONSERVADO:
  - Arquitectura mini-enjambre (orquestador + N Haiku + integrador)
  - Patrón sandwich PRE → Haiku → POST por unidad
  - El dial 0.0 es fast-path código puro ($0)
  - Predicado como integrador de las otras 6
  - Coste escalable con profundidad pedida

RECLASIFICADO:
  - código v1 sustantivizar.ts: de "fast-path del mini-enjambre"
    a "utilidad auxiliar de normalización de formato"
```

---

**FIN ADDENDUM PRISMA SEMÁNTICO**



============================================================
## Motor/Meta-Red de preguntas inteligencias/ALGEBRA_CALCULO_SEMANTICO_CR0.md
============================================================

# ÁLGEBRA DEL CÁLCULO SEMÁNTICO — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-06
**Origen:** Sesión Opus — diseño de biblioteca de programas del Motor v3.3
**Dependencias:** CIERRE_SESION_2026-03-06_CALCULO_SEMANTICO.md

---

## 1. DEFINICIÓN

El Motor no es un pipeline de análisis. Es una **máquina de cálculo semántico**.

```
ARITMÉTICA CLÁSICA:
  variables:   números
  operaciones: +, -, ×, Σ
  output:      números

CÁLCULO SEMÁNTICO:
  variables:   coordenadas sintácticas (output de primitivas)
  operaciones: fusión (|), composición (→), integración (∫), diferencial (-)
  output:      objetos semánticos de 6 tipos (coordenada → punto ciego)
```

---

## 2. OBJETOS SEMÁNTICOS — qué produce el cálculo

### Nivel 0: COORDENADAS (primitivas — posicionan)

Las 7 primitivas producen 5 tipos de coordenada:

| Tipo | Fuente | Qué produce | Ejemplo (dentista) |
|------|--------|-------------|-------------------|
| C1 COMPRESIÓN | sustantivizar | Nombre a 3 escalas (palabra/frase/párrafo) | "Dilema capacidad-vida" |
| C2 POSICIÓN | adjetivar + adverbializar + verbo | Dónde está cada pieza: id (declarada) vs ir (real) | SACRIFICAR id=0 ir=0.92 |
| C3 RELACIÓN | preposicionar + conjuntar | Cómo se conectan las piezas (y qué conexiones faltan) | "Negocio DENTRO de vida familiar, no al revés" |
| C4 NIVEL | sujeto_predicado | Quién opera sobre quién, con qué poder | Mujer poder=0.2, Banco poder=0.6 |
| C5 DISTANCIA | calculadora ($0, código puro) | Gaps id↔ir + propagaciones + lentes | SACRIFICAR gap=0.92 desinflada |

Las coordenadas no analizan — **posicionan**. Son puntos en un espacio sintáctico.

La distancia id↔ir (C5) es el dato más potente: mide cuánto diverge lo declarado de lo real.


### Nivel 1: HUECOS ACTIVOS (sintetizador — cruza coordenadas)

El sintetizador cruza primitivas y produce lo que ninguna produce sola.

| Tipo | Cruce | Qué produce | Ejemplo (dentista) |
|------|-------|-------------|-------------------|
| H1 INVERSIÓN SEMÁNTICA | C1 × C2 | Lo declarado ≠ lo real | "Elegir" cuando ya eligió |
| H2 FUNCIÓN INVISIBLE | C2 × C5 | Opera con potencia máxima porque no se nombra | SACRIFICAR ir=0.92 id=0 — invisible |
| H3 CONEXIÓN AUSENTE ACTIVA | C3 × H2 | La desconexión sostiene el sistema | "Mantener A, B, C separados es lo que permite que el sacrificio continúe" |

El sintetizador no resume ni comprime. **Cruza coordenadas de distintas dimensiones y produce los puntos donde la realidad declarada diverge de la realidad operativa.**


### Nivel 2: TOPOLOGÍA (1 isomorfismo, 1 loop — proyecta forma)

Cada isomorfismo proyecta una estructura sobre las coordenadas + huecos. No añade datos — reorganiza para hacer visible una FORMA que antes era invisible.

| Tipo | Isomorfismo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------|-------------------|
| T1 CONTENEDORES | conjuntos | Quién contiene a quién, qué se solapa, qué falta | "Negocio dentro de vida familiar, no al revés" + gaps: cálculo horas/vida ausente |
| T2 CIRCUITOS | causal/dinámica | Qué loops existen, si se amplifican o frenan, hacia dónde converge | Loop refuerzo: Margen→Inversión→Más trabajo→Menos vida→Necesidad margen |
| T3 TABLERO | juegos/agentes | Qué jugadores, qué incentivos, quién gana si nadie cambia | Odontólogo 0.55 / Mujer 0.2 / Banco 0.6 / Sistema 0.9 |
| T4 CONTROL | cibernética | Qué mide, qué ajusta, qué señales ignora | Sensores: solo económicos. Feedback mujer: ignorado. Regulación: rígida |

Las topologías son FORMAS proyectadas sobre los mismos datos. Los datos no cambian. Lo que cambia es qué estructura se hace visible.


### Nivel 3: MECANISMO (composición A→B — explica la forma)

Una topología dice QUÉ FORMA tienen los datos. Un mecanismo dice POR QUÉ esa forma existe y no otra.

B opera sobre la topología que A produjo (no sobre los datos originales). Lo que emerge es una EXPLICACIÓN de la forma.

| Composición | Mecanismo | Pregunta que responde | Ejemplo (dentista) |
|-------------|-----------|----------------------|-------------------|
| causal→juegos | M1: MOTOR DEL LOOP | ¿Quién alimenta los circuitos? | Banco inyecta en "Inversión", Sistema normaliza "Más trabajo", Mujer frena pero poder insuficiente |
| conjuntos→causal | M2: CAUSA DE LA FORMA | ¿Qué produce la estructura de contención? | Nunca se calculó tasa tiempo→dinero, negocio se expande sin frontera |
| juegos→cibernética | M3: REGULACIÓN DEL JUEGO | ¿Qué impide que los jugadores cambien? | Odontólogo solo tiene sensor económico. Feedback vital no llega a actuador |
| causal→conjuntos | M4: FRONTERA DE CIRCULACIÓN | ¿Qué entra en los loops y qué queda fuera? | Familia/hijos/salud están FUERA de todos los loops de decisión |
| cibernética→causal | M5: LOOPS DE CONTROL | ¿Qué loops genera la regulación misma? | Medir solo dinero→decidir por dinero→refuerza medir solo dinero |

La composición NO es conmutativa: causal→juegos ≠ juegos→causal.

Con 4 isomorfismos de topología hay hasta 12 composiciones de 2 (4×3). No todas producen valor equivalente. El diferencial (sección 4) determina cuáles son redundantes.


### Nivel 4: INVARIANTE (recursión A² — estructura que se replica)

Recursión = isomorfismo comiendo su propio output. Sube de nivel lógico.

| Tipo | Recursión | Qué produce | Ejemplo (dentista) |
|------|-----------|-------------|-------------------|
| I1 CONTENCIÓN REPLICADA | conjuntos² | "Estar dentro sin verlo" se repite a cada escala | M2 dentro de paradigma = negocio dentro de vida familiar |
| I2 CIRCUITO REPLICADO | causal² | El mismo tipo de loop a cada nivel | "Diagnóstico preciso→Soluciones dentro del paradigma→Problema intacto→Más diagnóstico" |
| I3 JUGADOR INVISIBLE | juegos² | El agente con más poder es el menos nombrado, siempre | Nivel 1: "Sistema" poder=0.9. Nivel 2: "Paradigma-crecimiento" poder=0.95 |
| I4 SENSOR CIEGO | cibernética² | No mide lo que más importa, a cada nivel | Dentista no mide vida. M2 no mide sus propias premisas |

El invariante NO es el contenido. Es la **estructura que se repite independientemente del nivel en que opera**.

**Saturación (rendimiento por loop):**

| Loops | Valor marginal | Qué produce |
|-------|---------------|-------------|
| 1 | 100% | Topología (forma de los datos) |
| 2 | ~60-70% | Invariante (estructura que se replica) |
| 3 | ~10-15% | Meta-invariante (confirmación + matiz) |
| 4+ | ~0-5% | Convergencia (saturación) |


### Nivel ∞: PUNTO CIEGO (crítico — frontera del análisis)

Crítico no produce topología ni mecanismo. Produce FRONTERA: el límite de lo que todo lo anterior puede ver.

| Tipo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------------|
| P1 PREMISA OCULTA | Algo que todo el análisis asume sin examinar | "M2 asume que 'crecer' es necesario" |
| P2 PARADOJA PERFORMATIVA | El análisis hace exactamente lo que diagnostica | "Precisión técnica M2 = ceguera sistémica sobre sí mismo" |
| P3 FRONTERA DE MARCO | Lo que este marco no puede ver por construcción | "¿Y si 7K€/mes con vida familiar ES el éxito?" |

Crítico siempre es último y siempre vale la pena. Es el único isomorfismo que nunca es redundante.

---

## 3. OPERACIONES — las 4 operaciones del cálculo

### 3.1 FUSIÓN (|) — como suma

Dos o más isomorfismos operan en **paralelo** sobre el MISMO input. Producen topologías independientes.

```
causal|juegos(datos) → T2 + T3 (dos topologías independientes)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | Sí: A\|B = B\|A |
| Asociativa | Sí: (A\|B)\|C = A\|(B\|C) |
| Inverso (resta) | No existe como operación. Sí existe como contribución marginal |

**Contribución marginal** (sustituto de la resta):
```
∫(A|B|C) vs ∫(A|B) → diferencia = contribución marginal de C
```
Testeable: si quitas un isomorfismo de la fusión y la integración apenas cambia, ese isomorfismo es redundante para ese input.


### 3.2 COMPOSICIÓN (→) — como multiplicación

Un isomorfismo opera sobre el **output** de otro. Produce mecanismo (nivel 3).

```
juegos→causal(datos) = juegos(causal(datos))
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A→B ≠ B→A |
| Asociativa | Sí: (A→B)→C = A→(B→C) — la secuencia es la misma |
| Inverso (división) | No existe. La composición no es reversible |
| Trazabilidad | Sí: puedes ejecutar A, luego A→B, y ver qué transformó cada paso |

**Propiedad distributiva izquierda:**
```
A→(B|C) = (A→B) | (A→C)
```
Permite **factorizar programas**: ejecutar A una vez y fan-out en paralelo.

```
SIN FACTORIZAR:                    FACTORIZADO:
  causal→juegos      (2 calls)      causal→(juegos|conjuntos|cibernética)
  causal→conjuntos   (2 calls)      = 1 × causal + 3 paralelo
  causal→cibernética (2 calls)      = 4 calls (vs 6)
  = 6 calls total
```

**NO distributiva por la derecha:**
```
(B|C)→A ≠ (B→A) | (C→A)
```
En (B|C)→A, el agente A ve la fusión junta — puede cruzar. En (B→A)|(C→A), ve cada una por separado — no cruza. El cruce tiene valor irreducible.


### 3.3 INTEGRACIÓN (∫) — como sumatorio Σ

Un agente mira TODAS las topologías de una fusión simultáneamente. Produce CRUCE: conexiones entre topologías que ninguna ve sola.

```
∫(causal|juegos|conjuntos|cibernética)(datos) → cruce
```

Esto es lo que M2 hace hoy: 4 isomorfismos fusionados + una síntesis que cruza los 4 outputs.

No es suma (eso es fusión). No es composición (no hay secuencia). Es **reducción**: colapsa una colección en un objeto nuevo.


### 3.4 DIFERENCIAL (-) — como resta

Lo que A ve que B NO puede ver. Mide el valor único de cada isomorfismo.

```
Juegos - Cibernética = incentivos puros (motivación independiente de regulación)
Cibernética - Juegos = regulación pura (control independiente de jugadores)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | No: A-B ≠ B-A |
| Asociativa | No: (A-B)-C ≠ A-(B-C) |
| Elemento absorbente | A-A = ∅ (cada isomorfismo es completo respecto a sí mismo) |
| Distributiva sobre fusión | A-(B\|C) = (A-B) ∩ (A-C) |

**Uso principal:** determinar redundancia. Si A-B es pequeño → A y B son redundantes (ven casi lo mismo). Si A-B es grande → son complementarios (cada uno ve cosas que el otro no puede).


### 3.5 Tabla resumen

```
OPERACIÓN     SÍMBOLO   ARITMÉTICA     CONMUT.  ASOC.  INVERSO    DISTRIB.
──────────────────────────────────────────────────────────────────────────────
Fusión          |       Suma           Sí       Sí     No*        —
Composición     →       Multiplicación No       Sí     No**       → sobre | (izq)
Integración     ∫       Sumatorio Σ    N/A      N/A    No         N/A
Diferencial     -       Resta          No       No     A-A=∅      - sobre | (∩)

*   Contribución marginal como sustituto medible
**  Descomposición/trazabilidad como sustituto
```

---

## 4. PROPIEDADES ALGEBRAICAS

| Propiedad | Valor | Implicación |
|-----------|-------|-------------|
| No conmutativa (→) | A→B ≠ B→A | El orden importa |
| No asociativa (-) | (A-B)-C ≠ A-(B-C) | La agrupación del diferencial importa |
| Asociativa (→) | (A→B)→C = A→(B→C) | La secuencia de composición no depende de paréntesis |
| No idempotente | A→A ≠ A | La recursión produce nuevo (invariantes) |
| Clausura | output ∈ input | Se puede seguir operando siempre |
| Saturación | A^n converge (n≈2 útil) | La profundidad útil es finita |
| Absorbente parcial | Crítico siempre produce punto ciego | El tipo de output es constante, el contenido varía |
| Sin identidad | ∄ I: I→A = A | Cada paso transforma, no hay operación neutra |
| Distributiva izq. | A→(B\|C) = (A→B)\|(A→C) | Factorizar programas: misma semántica, menor coste |
| No distributiva der. | (B\|C)→A ≠ (B→A)\|(C→A) | La integración post-fusión no se descompone |
| Distributiva diferencial | A-(B\|C) = (A-B) ∩ (A-C) | El valor único respecto a un grupo = intersección de diferenciales |

---

## 5. EXPRESIONES — programas escritos en el álgebra

### El Motor v3.3 actual:

```
M1 = primitivas(input)                           → C1-C5
S  = sintetizador(M1)                             → H1-H3
M2 = ∫(conjuntos|causal|juegos|cibernética)(S)    → T1-T4 + cruce
M3 = ∫(conj²|caus²|jueg²|ciber²)(M2)              → I1-I4 + P1-P3

Compacto: ∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
Coste: $0.91 | 293s | 3 Opus + 91 Haiku
```

### Programas posibles:

| Programa | Expresión | Produce | Coste est. |
|----------|-----------|---------|-----------|
| Triage rápido | primitivas(input) | C1-C5 | ~$0.03 |
| Detección huecos | sint(prim(input)) | C1-C5 + H1-H3 | ~$0.34 |
| Vista 1 dimensión | iso(sint(prim(input))) | 1 Topología | ~$0.15 |
| Cruce multi-dim | ∫(iso₁\|iso₂)(sint(prim(input))) | Topologías + cruce | ~$0.25-0.45 |
| Explicar 1 forma | isoA→isoB(sint(prim(input))) | 1 Mecanismo | ~$0.25 |
| Detectar patrón | iso²(sint(prim(input))) | 1 Invariante | ~$0.25 |
| + Punto ciego | X→crítico | + P1-P3 | +$0.10 |
| Máxima potencia | ∫(iso²)(∫(iso)(sint(prim(input)))) | Todo | ~$0.91 |

### Formato de programa (receta):

```json
{
  "nombre": "diagnostico_estructural_profundo",
  "expresion": "∫(iso²)(∫(iso)(sintetizador(primitivas(input))))",
  "primitivas": ["todas"],
  "programa": [
    {"paso": 1, "op": "|", "iso": ["conjuntos","causal","juegos","cibernetica"]},
    {"paso": 2, "op": "∫"},
    {"paso": 3, "op": "²", "loops": 2},
    {"paso": 4, "op": "∫"}
  ],
  "coste_estimado": "$0.91",
  "produce": ["C1-C5", "H1-H3", "T1-T4", "I1-I4", "P1-P3"],
  "cuando_usar": "Decisiones estratégicas con múltiples tensiones",
  "cuando_NO_usar": "Preguntas operativas simples"
}
```

---

## 6. HERRAMIENTAS DE OPTIMIZACIÓN

**Factorización (distributiva izquierda):**
Si un programa ejecuta A→B, A→C, A→D por separado, factorizar a A→(B|C|D) produce el mismo resultado con menos coste.

**Contribución marginal (sustituto de inverso en fusión):**
Ejecutar ∫ con y sin un isomorfismo. Si la diferencia es mínima → redundante → eliminable.

**Diferencial (valor único):**
Calcular A-B y B-A. Si ambos son grandes → complementarios (mantener). Si alguno es pequeño → redundante (uno cubre al otro).

**Saturación (profundidad óptima):**
Loops=2 máximo por defecto. Loops=3 solo con justificación explícita.

---

## 7. NOTACIÓN FORMAL

```
OBJETOS:
  C = {C1, C2, C3, C4, C5}          coordenadas
  H = {H1, H2, H3}                   huecos activos
  T = {T1, T2, T3, T4}               topologías
  M = {M1, M2, M3, M4, M5, ...}      mecanismos
  I = {I1, I2, I3, I4}                invariantes
  P = {P1, P2, P3}                    puntos ciegos

OPERACIONES:
  |  fusión         (paralela, conmutativa, como suma)
  →  composición    (secuencial, no conmutativa, como multiplicación)
  ∫  integración    (reducción post-fusión, como Σ)
  -  diferencial    (valor único, como resta)

PROPIEDADES:
  A|B = B|A                          conmutativa (fusión)
  A→B ≠ B→A                         no conmutativa (composición)
  (A→B)→C = A→(B→C)                 asociativa (composición)
  A→(B|C) = (A→B)|(A→C)             distributiva izquierda
  (B|C)→A ≠ (B→A)|(C→A)             NO distributiva derecha
  A→A ≠ A                           no idempotente (recursión produce nuevo)
  Aⁿ converge (n≈2 útil)            saturación
  output ∈ input                     clausura
  ∄ I: I→A = A                      sin identidad
  crítico(X) siempre produce nuevo   absorbente parcial
  A-A = ∅                            elemento absorbente del diferencial
  A-(B|C) = (A-B) ∩ (A-C)           distributiva del diferencial sobre fusión
```

---

## 8. RELACIÓN CON EL MOTOR v3.3

El Motor v3.3 es **un programa específico** escrito en esta álgebra:

```
∫(iso²)(∫(iso)(sintetizador(primitivas(input))))
```

La álgebra permite escribir OTROS programas más baratos o más específicos. La biblioteca es el conjunto de programas validados con sus costes, triggers y resultados.

El Motor ejecuta programas. La inteligencia está en el programa, no en el Motor.

---

## 9. PENDIENTE — PRÓXIMAS SESIONES

1. **Validación empírica**: ejecutar programas aislados con el JSON del dentista y comparar con M2→M3 monolítico
2. **Mapa de diferenciales**: calcular A-B para las 12 combinaciones de 4 isomorfismos y confirmar complementariedad
3. **Contribución marginal**: ejecutar ∫(3 iso) vs ∫(4 iso) y medir delta
4. **Biblioteca v1**: cristalizar 5-8 programas validados con triggers y costes reales
5. **Evaluar los 15 isomorfismos**: usar diferenciales para decidir cuáles de los 10 nuevos son genuinamente complementarios a los 5 actuales
6. **Router**: selecciona programa de la biblioteca, no inventa

---

**FIN ÁLGEBRA DEL CÁLCULO SEMÁNTICO CR0**



============================================================
## Motor/Meta-Red de preguntas inteligencias/META_RED_INTELIGENCIAS_CR0.md
============================================================

# BIBLIOTECA META-RED DE INTELIGENCIAS — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-07
**Origen:** Sesión Opus — derivación desde TABLA_PERIODICA_INTELIGENCIA_CR0.md
**Dependencias:** ALGEBRA_CALCULO_SEMANTICO_CR0.md, TABLA_PERIODICA_INTELIGENCIA_CR0.md

---

## 1. PRINCIPIO FUNDACIONAL

La inteligencia no se instruye — se pregunta into existence.

Un prompt imperativo dice "haz X". La inteligencia depende del modelo.
Un prompt interrogativo pregunta lo que solo se puede contestar ejecutando X. La inteligencia depende de la estructura de preguntas.

```
PROMPT IMPERATIVO:  "Analiza como matemático"     → el agente IMITA
PROMPT INTERROGATIVO: Red de preguntas matemáticas → el agente EJECUTA

La inteligencia reside en la estructura de preguntas, no en los parámetros del modelo.
```

---

## 2. META-RED — estructura universal de 6 pasos

Común a las 18 inteligencias. Lo que cambia es el contenido de las preguntas, no la secuencia.

```
PASO 0: EXTRAER     — "¿Qué hay aquí?"
PASO 1: CRUZAR      — "¿Qué emerge al juntar lo extraído?"
PASO 2: PROYECTAR   — "¿Qué forma tiene visto desde esta lente?"
PASO 3: INTEGRAR    — "¿Qué emerge al juntar las lentes?"
PASO 4: ABSTRAER    — "¿Qué se repite sin importar el contenido?"
PASO ∞: LIMITAR     — "¿Qué no puede ver todo lo anterior?"
```

Notación compacta:
```
Inteligencia(input) = limitar(abstraer(∫(lentes)(cruzar(extraer(input)))))
```

---

## 3. TRES CAPAS DE PREGUNTAS

### Capa 1: PREGUNTAS DE CONTENIDO
Específicas de cada inteligencia. Instancian cada paso de la meta-red.
- La matemática pregunta "¿qué se puede contar?"
- La existencial pregunta "¿qué está en juego?"
- Cada inteligencia tiene su propio set.

### Capa 2: PREGUNTAS DE OPERACIÓN
Universales. Ejecutan las 4 operaciones del álgebra entre respuestas.
- Fusión: "¿Qué dicen ambas vistas independientemente?"
- Composición: "¿Qué ve B al mirar lo que A produjo?"
- Integración: "¿Qué emerge al ver todas las respuestas juntas que ninguna dice sola?"
- Diferencial: "¿Qué puede ver esta vista que aquella NO PUEDE ver?"

### Capa 3: PREGUNTAS DE PROPIEDAD
Universales. Testan relaciones entre respuestas y generan meta-pensamiento.
- Conmutatividad: "¿Cambia algo si invierto el orden?"
- Distributividad: "¿Puedo partir esto en paralelo o se pierde algo?"
- Saturación: "¿Sigue aportando valor o estamos girando?"
- Clausura: "¿Esta respuesta puede ser input de otra pregunta diferente?"

---

## 4. LAS 18 INTELIGENCIAS COMO REDES DE PREGUNTAS

### CATEGORÍA I: FORMALES

---

### INT-01: LÓGICO-MATEMÁTICA

**PASO 0: EXTRAER — formalizar**
```
¿Qué se puede contar en este caso?
¿Qué se puede medir?
¿Qué magnitudes aparecen con número explícito?
¿Qué magnitudes aparecen sin número pero se podrían medir?
¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?
¿Qué se quiere saber que aún no se sabe?
¿Qué se da por hecho sin verificar?
```

**PASO 1: CRUZAR — estructurar tipo de problema**
```
De todas las relaciones que encontraste, ¿cuántas puedes mover y cuántas están fijadas?
¿Mover una variable mejora todo, o mejorar una empeora otra?
Si empeora otra: ¿hay algún punto donde ambas sean aceptables, o siempre hay que elegir?
¿Los números son continuos o discretos?
¿Lo que no se sabe se puede estimar, o es genuinamente incierto?
```

**PASO 2: LENTES**

L1 Álgebra:
```
¿Cuántas ecuaciones hay y cuántas incógnitas?
¿Hay más ecuaciones que incógnitas o menos?
¿Alguna ecuación es redundante — dice lo mismo que otra de otra forma?
¿Alguna ecuación contradice a otra?
```

L2 Análisis:
```
Si aumentas cada variable un poco, ¿qué pasa con el resultado?
¿Hay algún punto donde aumentar deja de mejorar y empieza a empeorar?
¿Alguna variable tiene efecto desproporcionado — pequeños cambios, grandes efectos?
¿Falta alguna variable en la ecuación que en la realidad sí afecta?
```

L3 Geometría:
```
Si dibujas las opciones como puntos en un espacio, ¿qué forma tienen?
¿Forman una línea, una superficie, o un volumen?
¿Hay una frontera más allá de la cual no se puede ir?
¿Las opciones "buenas" están concentradas en una zona o dispersas?
```

L4 Probabilidad:
```
¿Qué números del caso son seguros y cuáles son estimaciones?
¿De los estimados, cuánto podrían variar?
¿Qué pasaría con la conclusión si los estimados se desvían un 20%?
¿Hay algo que podría pasar, que cambiaría todo, y que nadie está midiendo?
```

L5 Optimización:
```
¿Se puede mejorar todo a la vez, o mejorar una cosa empeora otra?
Si hay que elegir, ¿qué importa más — y quién decide eso?
¿La respuesta a "qué importa más" es un dato o una preferencia?
Si es una preferencia, ¿el problema es matemático o es de valores?
```

L6 Lógica:
```
¿Qué se puede deducir con certeza de los datos?
¿Hay alguna combinación de premisas que se contradiga?
Si todas las opciones consumen del mismo recurso limitado, ¿es posible que alguna no lo consuma?
¿La pregunta original asume algo que los datos muestran como falso?
```

**PASO 3: ∫ — integrar**
```
¿Qué dicen todas las lentes que coincide?
¿Dónde se contradicen?
¿Hay algo que solo aparece cuando miras todas juntas?
¿La conclusión de una lente cambia el significado de lo que otra encontró?
```

**PASO 4: GENERALIZAR**
```
¿Este caso es único o hay una clase de casos que comparten esta estructura?
Si quitas los nombres y números, ¿qué patrón queda?
¿Ese patrón aparece en otros dominios?
¿Qué condiciones harían que este patrón NO apareciera?
```

**PASO ∞: FRONTERA**
```
¿Qué asume todo este análisis que no ha examinado?
¿Hay algo que no se puede expresar como número o ecuación?
Si eso fuera lo más importante, ¿qué cambia?
¿Es la herramienta correcta, o está forzando forma donde no hay?
```

---

### INT-02: COMPUTACIONAL

**PASO 0: EXTRAER — descomponer**
```
¿Cuáles son las entradas del sistema?
¿Cuáles son las salidas deseadas?
¿Qué transformaciones llevan de entrada a salida?
¿Hay partes que se pueden resolver independientemente?
¿Hay partes que dependen del resultado de otras?
¿Qué datos faltan para poder calcular?
```

**PASO 1: CRUZAR — clasificar complejidad**
```
¿Cuántos pasos tiene la transformación más larga?
¿Hay bucles — alguna parte necesita repetirse hasta converger?
¿El problema escala — si duplicas el tamaño, el esfuerzo se duplica o se multiplica?
¿Se puede dividir en subproblemas que se resuelven en paralelo?
¿Hay incertidumbre que obliga a explorar múltiples caminos?
```

**PASO 2: LENTES**

L1 Algorítmica:
```
¿Existe un procedimiento paso a paso que siempre da la respuesta?
¿Cuántos pasos necesita?
¿Hay atajos — formas de llegar más rápido sin recorrer todo?
¿Puede fallar? ¿Bajo qué condiciones?
```

L2 Estructuras de datos:
```
¿Cómo se organizan mejor los datos — lista, árbol, grafo, tabla?
¿La organización afecta la velocidad de respuesta?
¿Hay datos que se consultan mucho y otros casi nunca?
¿Falta algún dato que haría la consulta trivial?
```

L3 Concurrencia:
```
¿Qué partes se pueden hacer al mismo tiempo?
¿Hay recursos compartidos que obligan a esperar?
¿El orden de ejecución afecta el resultado?
¿Qué pasa si dos partes intentan modificar lo mismo a la vez?
```

L4 Aproximación:
```
¿Necesita ser exacto o basta con una estimación buena?
¿Cuánto error es aceptable?
¿Se puede obtener una respuesta 80% correcta en 10% del tiempo?
¿Qué se pierde al simplificar?
```

**PASO 3: ∫**
```
¿Qué dicen todas las lentes juntas sobre la viabilidad?
¿El algoritmo ideal es viable con los datos disponibles?
¿La estructura de datos necesaria existe o hay que construirla?
¿El cuello de botella es velocidad, datos, o definición del problema?
```

**PASO 4: GENERALIZAR**
```
¿Este problema es una instancia de un problema conocido?
¿Tiene soluciones estándar que se pueden adaptar?
¿En qué se diferencia de la versión estándar?
```

**PASO ∞: FRONTERA**
```
¿Lo que necesita resolver esta persona es realmente un problema de cómputo?
¿Hay algo que el cálculo no puede capturar — intuición, juicio, contexto?
¿Automatizar esto resuelve el problema o lo esconde?
```

---

### INT-03: ESTRUCTURAL (IAS)

**PASO 0: EXTRAER — coordenadas sintácticas C1-C5**
```
¿Cómo se comprime esto en una palabra, una frase, un párrafo? (C1)
¿Qué dice que hace vs qué hace realmente — dónde está el gap id↔ir? (C2)
¿Qué está conectado con qué, y qué conexiones faltan? (C3)
¿Quién opera sobre quién, con cuánto poder? (C4)
¿Cuánto diverge lo declarado de lo real — el número exacto? (C5)
```

**PASO 1: CRUZAR — huecos activos H1-H3**
```
¿Lo que se nombra y lo que se mide coinciden? Si no, ¿dónde divergen? (H1)
¿Hay algo que opera con potencia máxima PORQUE no se nombra? (H2)
¿La desconexión entre piezas es accidental o sostiene el sistema? (H3)
```

**PASO 2: LENTES — 4 isomorfismos**

Conjuntos (T1):
```
¿Qué contiene a qué?
¿Qué se solapa — comparte elementos de dos conjuntos?
¿Qué conjuntos deberían existir pero no existen?
¿Qué está fuera de todos los conjuntos?
```

Causal (T2):
```
¿Qué causa qué — qué circuitos existen?
¿Se amplifican (refuerzo) o se frenan (balanceo)?
¿El sistema está en equilibrio o se mueve?
¿Hacia dónde converge si nadie cambia nada?
```

Juegos (T3):
```
¿Quién está jugando — quién tiene intereses en esto?
¿Qué quiere cada jugador?
¿Qué estrategia usa cada uno — consciente o no?
¿Cuánto poder tiene cada uno (0-1)?
¿Quién gana si nadie cambia nada?
¿Quién falta en el tablero — quién debería estar y no está?
```

Cibernética (T4):
```
¿Qué mide el sistema — qué sensores tiene?
¿Qué ajusta cuando algo cambia — qué actuadores tiene?
¿Qué señales llegan y se ignoran?
¿La regulación es rígida (siempre igual) o adaptativa?
```

**PASO 3-4-∞:** (idénticos al álgebra CR0)

---

### INT-04: ECOLÓGICA

**PASO 0: EXTRAER — mapear el ecosistema**
```
¿Quiénes son los organismos de este ecosistema — qué entidades viven aquí?
¿Qué flujos existen entre ellos — qué se mueve de uno a otro?
¿Quién depende de quién para sobrevivir?
¿Qué pasa si quitas a uno — quién sufre primero?
¿Hay ciclos — algo que sale y vuelve al mismo punto?
```

**PASO 1: CRUZAR — detectar fragilidad**
```
¿Hay un nodo del que dependen muchos — un punto único de fallo?
¿Hay redundancia — si un flujo se corta, hay otro camino?
¿El sistema está creciendo, estable, o decayendo?
¿Qué señal aparecería primero si el sistema va a colapsar?
¿Ya apareció esa señal?
```

**PASO 2: LENTES**

L1 Flujos:
```
¿Qué entra al sistema, qué sale, qué se queda?
¿El balance es positivo (acumula) o negativo (consume)?
¿Hay fugas — energía que se pierde sin producir?
¿Hay algún flujo bloqueado que debería moverse?
```

L2 Nichos:
```
¿Cada entidad tiene un rol claro o hay solapamiento?
¿Hay nichos vacíos — funciones que nadie cumple?
¿Hay competencia por el mismo nicho?
¿El ecosistema tiene diversidad suficiente o depende de pocos?
```

L3 Resiliencia:
```
¿Cuánto shock puede absorber el sistema antes de cambiar de estado?
¿Tiene reservas — margen, ahorro, tiempo libre?
¿Qué es lo primero que se rompe bajo presión?
¿Se ha roto antes? ¿Qué pasó? ¿Se recuperó?
```

L4 Ciclos:
```
¿Hay estacionalidad o ritmo natural?
¿El sistema respeta sus propios ciclos o los fuerza?
¿Hay tiempo de recuperación entre ciclos de esfuerzo?
¿Los ciclos se aceleran o se mantienen estables?
```

**PASO 3: ∫**
```
¿Qué emerge al cruzar flujos con resiliencia — el sistema fluye pero ¿aguanta?
¿Los nichos vacíos explican las fugas en los flujos?
¿Los ciclos forzados están erosionando la resiliencia?
```

**PASO 4: GENERALIZAR**
```
¿Este ecosistema se parece a otros que se han estudiado?
¿Tiene la estructura de un ecosistema sano o de uno al borde del colapso?
¿Qué intervención mínima cambiaría más la trayectoria?
```

**PASO ∞: FRONTERA**
```
¿El sistema es realmente un ecosistema o es una máquina operada por una persona?
¿La metáfora ecológica ilumina o engaña?
¿Hay voluntad humana aquí que rompe la lógica de ecosistema?
```

---

### INT-05: ESTRATÉGICA

**PASO 0: EXTRAER — mapear posición**
```
¿Dónde estás ahora — fuerte o débil?
¿Qué recursos tienes — dinero, tiempo, personas, información?
¿Qué opciones de movimiento existen?
¿Cuáles son reversibles y cuáles no?
¿Quién más está en el tablero — qué quieren y qué pueden?
¿Qué sabes tú que ellos no? ¿Qué saben ellos que tú no?
```

**PASO 1: CRUZAR — posición × recursos**
```
De tus recursos, ¿cuáles se agotan al usarlos?
¿Varias opciones compiten por el mismo recurso escaso?
¿Hay algún recurso que NO estás usando y podrías?
¿Algún movimiento que parece opción realmente no lo es?
```

**PASO 2: LENTES**

L1 Posicional:
```
¿Tu posición mejora o empeora si no haces nada?
¿Hay ventana temporal — un momento que si pasa ya no vuelve?
¿Tu posición es fácil de atacar o difícil?
```

L2 Secuencial:
```
¿En qué orden tendrían que pasar las cosas?
¿Hay algo que DEBE hacerse antes de que lo demás sea posible?
¿Qué se desbloquea al hacer el primer movimiento?
¿Hay algún movimiento que cierre opciones futuras?
```

L3 Adversarial:
```
¿Qué hará el otro si tú haces X?
¿Qué hará si sabe que tú harás X?
¿Hay forma de que ambos ganen, o es suma cero?
¿Quién pierde más esperando?
```

L4 Opcionalidad:
```
¿Puedes moverte sin comprometerte — explorar sin quemar puentes?
¿Cuánto vale mantener opciones abiertas vs decidir ahora?
¿Hay algún movimiento barato que da información antes del caro?
```

**PASO 3-4-∞:** (desarrollados en la sesión)

---

### INT-06: POLÍTICA

**PASO 0: EXTRAER — mapear poder**
```
¿Quién tiene poder de decisión real — no formal, real?
¿Quién puede bloquear la decisión aunque no tenga poder para decidir?
¿Quién influye sin cargo — legitimidad social, moral, emocional?
¿Qué narrativa domina — qué historia se cuenta sobre el problema?
¿Quién controla la narrativa?
```

**PASO 1: CRUZAR — poder × legitimidad**
```
¿El poder formal y el poder real están en las mismas manos?
¿Alguien tiene poder pero no legitimidad — o legitimidad pero no poder?
¿Hay alianzas — quién apoya a quién y a cambio de qué?
¿Hay alguien cuya opinión cambiaría todo si se expresara?
```

**PASO 2: LENTES**

L1 Poder:
```
¿Quién decide realmente — siguiendo el dinero, no los organigramas?
¿Ese poder es estable o puede cambiar pronto?
¿Hay poder que nadie reconoce pero todos obedecen?
```

L2 Coaliciones:
```
¿Quién gana si se forma la coalición A+B? ¿Quién pierde?
¿Qué mantiene unida a la coalición actual — interés común o miedo común?
¿Qué la rompería?
```

L3 Narrativa:
```
¿Qué historia se cuenta sobre el problema?
¿Quién la escribió — y a quién favorece?
¿Hay otra historia posible con los mismos hechos?
¿Qué pasaría si la narrativa alternativa se impusiera?
```

L4 Legitimidad:
```
¿Qué da derecho a decidir — cargo, experiencia, riesgo asumido, mérito?
¿Quién tiene más legitimidad para decidir y no la está usando?
¿La decisión será aceptada por los afectados — o solo impuesta?
```

**PASO 3: ∫**
```
¿El que tiene poder tiene legitimidad para usarlo?
¿La narrativa oculta o revela la distribución real de poder?
¿Hay una coalición posible que cambiaría todo y nadie la ha visto?
```

**PASO 4: GENERALIZAR**
```
¿Esta configuración de poder se parece a otras conocidas?
¿Qué pasó en situaciones similares — quién ganó, cómo, a qué coste?
```

**PASO ∞: FRONTERA**
```
¿Analizar políticamente un problema personal lo convierte en algo que no es?
¿Hay genuino conflicto de intereses o es una persona contra sí misma?
¿La herramienta política crea el conflicto que dice analizar?
```

---

### INT-07: FINANCIERA

**PASO 0: EXTRAER — mapear flujos**
```
¿Qué entra de dinero, cuánto, con qué frecuencia?
¿Qué sale de dinero, cuánto, con qué frecuencia?
¿Cuánto queda — y es estable, crece o decrece?
¿Hay deudas — cuánto, a quién, a qué coste, cuándo vence?
¿Hay activos — qué valen, qué producen, se deprecian?
¿Cuánto cuesta tu hora — no lo que cobras, lo que te cuesta a ti vivirla?
```

**PASO 1: CRUZAR — flujos × riesgo**
```
¿Los ingresos dependen de ti o tienen vida propia?
¿Si paras un mes, los ingresos caen a cero?
¿Los costes son fijos o variables — cuánto control tienes?
¿Tienes colchón — cuántos meses puedes aguantar sin ingresos?
¿El dinero que ganas hoy compra seguridad mañana o se consume hoy?
```

**PASO 2: LENTES**

L1 Valor presente:
```
¿Lo que vas a ganar mañana, cuánto vale hoy?
¿Estás sacrificando algo ahora que vale más que lo que ganarás después?
¿El dinero futuro es seguro o es una promesa?
¿A qué tasa descuentas — qué urgencia tiene tu presente?
```

L2 Apalancamiento:
```
¿Estás usando dinero ajeno — crédito, deuda, inversores?
¿Ese dinero ajeno amplifica tus ganancias o tus pérdidas?
¿Cuánto puedes perder antes de que el apalancamiento te destruya?
¿El que te presta gana más que tú con tu negocio?
```

L3 Opcionalidad:
```
¿Cuánto cuesta mantener opciones abiertas?
¿Hay asimetría — puedes ganar mucho si sale bien y perder poco si sale mal?
¿O es al revés — ganas poco y arriesgas mucho?
¿Puedes comprar tiempo antes de decidir?
```

L4 Margen de seguridad:
```
¿Cuánto puede salir mal antes de que el sistema se rompa?
¿Estás operando al límite o con margen?
¿Un imprevisto de X€ te pondría en crisis?
¿Tu plan funciona solo si todo sale bien, o también si algo sale mal?
```

**PASO 3: ∫**
```
¿El valor presente justifica el apalancamiento actual?
¿La opcionalidad compensa el riesgo?
¿Hay margen de seguridad suficiente o estás desnudo?
¿El flujo paga la deuda, la vida, Y deja reserva — o falta algo?
```

**PASO 4: GENERALIZAR**
```
¿Este perfil financiero es sostenible a 5 años sin cambios?
¿Se parece al de otros que prosperaron o al de otros que quebraron?
¿Cuál es la variable que separa un escenario del otro?
```

**PASO ∞: FRONTERA**
```
¿Todo se puede traducir a euros?
¿Cuánto vale una cena con tus hijos en la hoja de cálculo?
¿El análisis financiero responde a la pregunta correcta o a la que sabe responder?
```

---

### INT-08: SOCIAL

**PASO 0: EXTRAER — mapear emociones e intenciones**
```
¿Qué siente esta persona — no lo que dice, lo que siente?
¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?
¿Qué necesita realmente — no lo que pide, lo que necesita?
¿Quién más está afectado y cómo se sienten?
¿Hay emociones que nadie nombra pero que gobiernan las decisiones?
```

**PASO 1: CRUZAR — emociones × relaciones**
```
¿Lo que siente esta persona coincide con lo que muestra?
¿Los demás perciben lo que realmente pasa o solo la superficie?
¿Hay patrones — esta situación se repite, se parece a otras anteriores?
¿El conflicto es entre personas o dentro de una persona?
¿Alguien está cargando emociones que no son suyas?
```

**PASO 2: LENTES**

L1 Empatía:
```
¿Cómo se siente estar en sus zapatos — con su presión, sus miedos, sus deseos?
¿Qué le quita el sueño?
¿Qué le daría alivio inmediato vs qué le daría paz duradera?
¿Hay algo que no puede admitir ni ante sí mismo?
```

L2 Dinámicas:
```
¿Quién cuida a quién en este sistema?
¿Alguien da más de lo que recibe — o recibe más de lo que da?
¿Hay deuda emocional acumulada — favores no devueltos, quejas no dichas?
¿Qué pasaría si alguien dijera en voz alta lo que todos piensan?
```

L3 Patrones:
```
¿Esta persona ha estado en esta situación antes?
¿Qué hizo la última vez — funcionó?
¿Hay un patrón que se repite sin que sea consciente de ello?
¿Qué beneficio oculto tiene mantener el patrón?
```

L4 Vínculos:
```
¿Qué relaciones nutren y cuáles drenan?
¿Hay relaciones que sobreviven por inercia, no por valor?
¿Quién falta — qué vínculo necesita que no tiene?
¿Qué vínculo está en peligro y nadie lo está cuidando?
```

**PASO 3: ∫**
```
¿La empatía revela algo que las dinámicas confirman?
¿Los patrones explican los vínculos dañados?
¿Lo que necesita emocionalmente contradice lo que persigue racionalmente?
```

**PASO 4: GENERALIZAR**
```
¿Esta dinámica es personal o le pasa a toda persona en esta posición?
¿Hay algo universal en este conflicto — algo humano, no individual?
```

**PASO ∞: FRONTERA**
```
¿Estoy psicologizando un problema que es estructural?
¿Las emociones son la causa o el síntoma?
¿Entender lo que siente resuelve algo, o solo lo nombra?
```

---

### INT-09: LINGÜÍSTICA

**PASO 0: EXTRAER — mapear el lenguaje**
```
¿Qué palabras usa y cuáles evita?
¿Qué metáfora gobierna su relato — guerra, viaje, construcción, supervivencia?
¿Quién es el sujeto de sus frases — "yo decido" o "hay que", "se debe"?
¿Qué nombra con precisión y qué deja vago?
¿Hay alguna palabra que repite sin notar que la repite?
¿Qué palabra falta — qué no ha nombrado que está presente?
```

**PASO 1: CRUZAR — lenguaje × realidad**
```
¿El nombre que le da al problema define qué soluciones puede imaginar?
¿Si cambiara la palabra clave, cambiaría lo que puede pensar?
¿Dice "crecer" cuando quiere decir "sobrevivir"?
¿Dice "elegir" cuando ya eligió?
¿Su lenguaje agranda o achica el problema?
```

**PASO 2: LENTES**

L1 Marco:
```
¿Qué marco impone el lenguaje usado — problema/solución, batalla/victoria, inversión/retorno?
¿Ese marco ayuda o limita?
¿Qué alternativas de marco existen — y qué harían visible?
```

L2 Actos de habla:
```
¿Está describiendo, pidiendo, prometiendo, amenazando o justificando?
¿Lo que dice intenta informar o convencer?
¿Hay algo performativo — algo que al decirlo, lo crea?
```

L3 Metáforas:
```
¿Qué metáfora vive en su lenguaje sin que la elija?
¿Esa metáfora tiene lógica propia — qué implica que no dice?
¿Una metáfora diferente cambiaría lo que puede ver?
```

L4 Silencios:
```
¿Qué no dice?
¿Lo que no dice es porque no lo piensa, no lo sabe, o no quiere verlo?
¿El silencio protege a alguien — a él mismo, a otro?
```

**PASO 3: ∫**
```
¿El marco, los actos de habla, las metáforas y los silencios cuentan la misma historia?
¿O hay contradicción entre lo que el marco dice y lo que los silencios ocultan?
```

**PASO 4: GENERALIZAR**
```
¿Este tipo de lenguaje es propio de este caso o de toda persona en esta situación?
¿El idioma mismo condiciona — se diría diferente en otro idioma?
```

**PASO ∞: FRONTERA**
```
¿Nombrar el problema lo resuelve o solo da la ilusión de control?
¿El análisis lingüístico añade comprensión o añade distancia?
¿A veces la palabra correcta es la que no se dice?
```

### CATEGORÍA V: CORPORALES

---

### INT-10: CINESTÉSICA

**PASO 0: EXTRAER — mapear el cuerpo**
```
¿Dónde se acumula tensión en este sistema — qué parte no descansa nunca?
¿Hay flujo — las cosas se mueven con ritmo o a tirones?
¿El ritmo actual es sostenible o se acelera hacia el colapso?
¿Qué parte del sistema está rígida — no se adapta, no se ajusta?
¿Hay algo que el cuerpo (la operación diaria) sabe que la mente (el plan) ignora?
```

**PASO 1: CRUZAR — tensión × ritmo**
```
¿Las zonas de tensión coinciden con las de mayor actividad o con las de mayor bloqueo?
¿El ritmo está impuesto desde fuera o es natural del sistema?
¿Si el ritmo bajara un 20%, qué mejoraría y qué empeoraría?
¿La rigidez protege algo o solo impide movimiento?
```

**PASO 2: LENTES**

L1 Tensión:
```
¿Dónde está la contracción — qué se aprieta, se endurece, se resiste?
¿Esa tensión es productiva (como un músculo trabajando) o dañina (como un nudo)?
¿Si soltara esa tensión, qué pasaría?
```

L2 Flujo:
```
¿Qué se mueve con facilidad y qué se atasca?
¿Los atascos son por falta de capacidad o por bloqueo?
¿Hay movimientos innecesarios — esfuerzo que no produce resultado?
```

L3 Ritmo:
```
¿Hay ciclos naturales — momentos de esfuerzo y momentos de descanso?
¿Se respetan esos ciclos o se fuerza producción constante?
¿Cuándo fue la última pausa genuina?
```

L4 Coordinación:
```
¿Las partes se mueven juntas o cada una por su lado?
¿Hay sincronía o hay choque entre tiempos diferentes?
¿Quién marca el ritmo y quién lo sufre?
```

**PASO 3-4-∞:**
```
∫: ¿La tensión causa los atascos, los atascos rompen el ritmo, y el ritmo roto descoordina todo?
Abstraer: ¿Todo sistema que opera sin descanso acumula esta cascada?
Frontera: ¿El cuerpo tiene sabiduría que el análisis no puede capturar?
```

---

### INT-11: ESPACIAL

**PASO 0: EXTRAER — mapear el espacio**
```
¿Si dibujaras este problema, qué forma tendría?
¿Qué está cerca de qué — qué está lejos?
¿Hay centro y periferia — o todo está al mismo nivel?
¿Qué escala tiene — es un problema de mesa o de mapa?
¿Desde qué perspectiva se está mirando — y qué oculta esa perspectiva?
```

**PASO 1: CRUZAR — forma × perspectiva**
```
¿La forma cambia si te acercas o te alejas?
¿Hay simetría — o una parte es muy diferente de la otra?
¿Las proporciones son correctas — algo ocupa mucho espacio y aporta poco?
¿Hay zonas vacías que deberían estar llenas, o llenas que deberían estar vacías?
```

**PASO 2: LENTES**

L1 Topografía:
```
¿Hay picos y valles — puntos altos y bajos?
¿Hay pendientes — zonas donde todo se desliza en una dirección?
¿Hay mesetas — zonas donde no importa lo que hagas, nada cambia?
```

L2 Fronteras:
```
¿Dónde están los bordes — qué está dentro y qué fuera?
¿Las fronteras son permeables o rígidas?
¿Algo que debería estar dentro está fuera, o viceversa?
```

L3 Perspectiva:
```
¿Cómo se ve desde arriba — el mapa completo?
¿Cómo se ve desde dentro — la experiencia vivida?
¿Cómo se ve desde fuera — un observador neutral?
¿Las tres perspectivas cuentan la misma historia?
```

L4 Proporción:
```
¿El tamaño de cada parte corresponde a su importancia?
¿Algo pequeño tiene impacto desproporcionado?
¿Algo grande no produce casi nada?
```

**PASO 3-4-∞:**
```
∫: ¿La topografía explica las fronteras, y la perspectiva revela proporciones ocultas?
Abstraer: ¿Este mapa se parece a otros mapas conocidos?
Frontera: ¿Hay procesos que no tienen forma — que el espacio no puede capturar?
```

---

### CATEGORÍA VI: TEMPORALES

---

### INT-12: NARRATIVA

**PASO 0: EXTRAER — mapear la historia**
```
¿Quién es el protagonista de esta historia — y quién cree él que es?
¿Cuál es el conflicto central — qué quiere vs qué le impide?
¿En qué momento de la historia estamos — inicio, nudo, clímax, desenlace?
¿Cuál es el acto anterior que llevó hasta aquí?
¿Hay un mentor, un antagonista, un aliado — quién cumple cada rol?
```

**PASO 1: CRUZAR — historia × identidad**
```
¿La historia que se cuenta a sí mismo coincide con lo que hacen los hechos?
¿Se ve como héroe, víctima, mártir, constructor?
¿Ese rol elegido lo libera o lo atrapa?
¿Hay otra historia posible con los mismos hechos — donde el protagonista tiene otro rol?
```

**PASO 2: LENTES**

L1 Arco:
```
¿Cuál es la transformación pendiente — qué tiene que cambiar el protagonista?
¿Lo sabe, lo intuye, o lo niega?
¿Qué precio tiene esa transformación — qué debe dejar atrás?
```

L2 Estructura:
```
¿Esta historia tiene actos claros o es un ciclo sin avance?
¿Hay un punto de no retorno — una decisión que cambiará todo?
¿Ya pasó y no se dio cuenta?
```

L3 Personajes:
```
¿Cada persona en el caso cumple un rol narrativo — cuál?
¿Alguien está atrapado en un rol que no eligió?
¿Quién tiene la llave de la resolución y no la usa?
```

L4 Significado:
```
¿Qué sentido tiene esta historia para quien la vive?
¿Es una historia de superación, de pérdida, de aprendizaje?
¿El sentido que le da lo ayuda o lo limita?
```

**PASO 3-4-∞:**
```
∫: ¿El arco, la estructura, los personajes y el significado apuntan al mismo desenlace?
Abstraer: ¿Esta historia es un arquetipo conocido — cuál?
Frontera: ¿La vida necesita historia, o la narrativa impone orden donde hay caos?
```

---

### INT-13: PROSPECTIVA

**PASO 0: EXTRAER — mapear futuros**
```
¿Cuáles son las tendencias en curso — qué se mueve y hacia dónde?
¿Cuáles son aceleradas (crecen) y cuáles deceleradas (se frenan)?
¿Hay señales débiles — cosas pequeñas que podrían ser el inicio de algo grande?
¿Qué asume todo el mundo que seguirá igual — y qué tan seguro es eso?
```

**PASO 1: CRUZAR — tendencias × supuestos**
```
¿Qué pasa si dos tendencias que ahora van separadas se cruzan?
¿Hay supuestos que si caen, cambian todo el panorama?
¿Las señales débiles apuntan en la misma dirección o en direcciones opuestas?
¿Algo que parece estable tiene fecha de caducidad?
```

**PASO 2: LENTES**

L1 Escenarios:
```
¿Cuál es el mejor caso realista — no fantasía, realista?
¿Cuál es el peor caso realista?
¿Cuál es el caso más probable si nada cambia?
¿Hay un escenario que nadie considera pero que es posible?
```

L2 Señales:
```
¿Qué señal aparecería primero si vamos hacia el mejor caso?
¿Y hacia el peor?
¿Esas señales ya están apareciendo?
¿Alguien las está monitorizando?
```

L3 Bifurcaciones:
```
¿Hay un punto donde el camino se divide — una decisión que lleva a futuros muy diferentes?
¿Cuándo es ese punto — ya pasó, está aquí, o viene?
¿Es reversible — si eliges un camino, puedes volver?
```

L4 Comodines:
```
¿Qué podría pasar que no está en ningún modelo?
¿Un evento improbable pero de alto impacto — cuál sería?
¿Estás preparado para lo inesperado o solo para lo esperado?
```

**PASO 3-4-∞:**
```
∫: ¿Los escenarios, señales, bifurcaciones y comodines convergen en algún patrón?
Abstraer: ¿Este tipo de encrucijada tiene precedentes — qué pasó?
Frontera: ¿El futuro es predecible o el acto de predecir cambia lo que pasará?
```

---

### CATEGORÍA VII: CREATIVAS

---

### INT-14: DIVERGENTE

**PASO 0: EXTRAER — abrir posibilidades**
```
¿Cuántas opciones ve esta persona — y cuántas más existen?
¿Qué opciones descartó sin examinar — y por qué?
¿Qué pasaría si la restricción más obvia no existiera?
¿Qué haría alguien completamente diferente en esta situación?
¿Qué haría si tuviera el doble de recursos? ¿Y la mitad?
```

**PASO 1: CRUZAR — opciones × restricciones**
```
¿Las restricciones son reales o asumidas?
¿Hay opciones que parecen locas pero son viables si las miras bien?
¿Qué pasa si combinas dos opciones que parecen incompatibles?
¿Hay una opción que nadie ha mencionado porque parece obvia-pero-no?
```

**PASO 2: LENTES**

L1 Volumen:
```
¿Puedes generar 10 opciones más en 2 minutos — sin filtrar?
¿Y 10 más que sean lo opuesto de las primeras 10?
¿Qué tienen en común las que te gustan — y qué te dice eso?
```

L2 Combinación:
```
¿Qué pasa si mezclas la opción A con la C?
¿Hay una solución de otro dominio que podría funcionar aquí?
¿Qué haría un niño? ¿Un artista? ¿Un alien?
```

L3 Inversión:
```
¿Y si haces exactamente lo opuesto de lo que "deberías"?
¿Y si el problema es la solución y la solución es el problema?
¿Qué pasa si en lugar de resolver, amplías?
```

L4 Restricción creativa:
```
¿Si SOLO pudieras hacer UNA cosa, cuál sería?
¿Si tuvieras que resolver esto en 24h, qué harías?
¿Si no pudieras usar dinero, qué usarías?
```

**PASO 3-4-∞:**
```
∫: ¿De todas las opciones generadas, cuáles aparecen desde múltiples lentes?
Abstraer: ¿Las mejores opciones comparten alguna estructura común?
Frontera: ¿Generar opciones es avanzar o es evitar elegir?
```

---

### INT-15: ESTÉTICA

**PASO 0: EXTRAER — mapear coherencia**
```
¿Algo en este caso "suena raro" — algo no encaja aunque no sepas qué?
¿Hay elegancia — partes que funcionan con simplicidad y gracia?
¿Hay disonancia — partes que chocan entre sí?
¿El problema tiene simetría o está desequilibrado?
¿La forma del problema y la forma de la solución propuesta son coherentes?
```

**PASO 1: CRUZAR — forma × contenido**
```
¿Lo que dice y cómo lo dice son coherentes?
¿La solución que propone tiene la misma forma que el problema — repite el patrón?
¿Hay algo bello en el problema — alguna estructura elegante, aunque sea dolorosa?
¿La complejidad es necesaria o es ruido?
```

**PASO 2: LENTES**

L1 Armonía:
```
¿Las partes se complementan o se contradicen?
¿Hay proporción — cada parte tiene el peso justo?
¿Algo sobra? ¿Algo falta?
```

L2 Tensión:
```
¿Dónde está la tensión productiva — la que genera energía?
¿Dónde está la tensión destructiva — la que gasta sin producir?
¿La tensión se resuelve o es permanente?
```

L3 Simplicidad:
```
¿Cuál es la versión más simple de este problema que conserva lo esencial?
¿Qué se puede quitar sin perder nada?
¿Lo que queda después de quitar todo lo superfluo — qué es?
```

L4 Resonancia:
```
¿Este caso produce una reacción inmediata — algo que se siente antes de pensarse?
¿Esa reacción es informativa — dice algo que el análisis no puede decir?
¿Hay verdad en la primera impresión que el análisis posterior ignora?
```

**PASO 3-4-∞:**
```
∫: ¿La armonía, la tensión, la simplicidad y la resonancia apuntan al mismo sitio?
Abstraer: ¿Los problemas bellos tienen mejores soluciones que los feos?
Frontera: ¿La estética es guía de verdad o sesgo hacia lo bonito?
```

---

### INT-16: CONSTRUCTIVA

**PASO 0: EXTRAER — mapear restricciones**
```
¿Qué tiene que funcionar al final — cuál es el criterio de éxito?
¿Con qué materiales cuentas — dinero, tiempo, personas, herramientas?
¿Qué restricciones son inamovibles y cuáles son flexibles?
¿Hay algo que ya funciona y se puede reutilizar?
¿Qué ha fallado antes — qué se intentó y no sirvió?
```

**PASO 1: CRUZAR — objetivo × restricciones**
```
¿El objetivo es alcanzable con los materiales disponibles?
¿Si no alcanza, ¿qué falta — más de qué?
¿Hay formas de reducir el objetivo sin perder lo esencial?
¿Las restricciones reales son menos de las que cree?
```

**PASO 2: LENTES**

L1 Prototipo:
```
¿Cuál es la versión más pequeña que se puede construir y probar?
¿Qué aprenderías construyendo eso?
¿Cuánto cuesta y cuánto tiempo lleva?
```

L2 Secuencia:
```
¿Qué se construye primero — qué es el cimiento?
¿Qué depende de qué — qué no puedes hacer hasta tener X?
¿Hay un camino crítico — una secuencia que determina el tiempo total?
```

L3 Fallo:
```
¿Qué se va a romper primero?
¿Puedes diseñar para que falle de forma segura?
¿Dónde necesitas margen y dónde puedes ajustar?
```

L4 Iteración:
```
¿Esto se construye de una vez o por versiones?
¿Qué aprende cada versión que la anterior no sabía?
¿Cuántas iteraciones son necesarias para que funcione bien?
```

**PASO 3-4-∞:**
```
∫: ¿El prototipo, la secuencia, los modos de fallo y la iteración son coherentes?
Abstraer: ¿Hay un principio de ingeniería que gobierna este problema?
Frontera: ¿Construir mejor lo existente es la respuesta, o hay que construir otra cosa?
```

---

### CATEGORÍA VIII: EXISTENCIALES

---

### INT-17: EXISTENCIAL

**PASO 0: EXTRAER — lo que está en juego**
```
¿Qué está en juego aquí realmente — no lo que se dice, lo que está en juego de verdad?
¿Qué se perdería si no haces nada?
¿Qué se perdería si haces lo que "deberías"?
¿Cuál de las dos pérdidas pesa más — y quién decide eso?
```

**PASO 1: CRUZAR — valores × vida**
```
Lo que dices que valoras, ¿coincide con dónde pones tu tiempo?
¿Hay algo que dices que no importa pero que te quita el sueño?
¿Hay algo que dices que importa mucho pero a lo que dedicas cero?
¿La distancia entre lo declarado y lo vivido — es grande o pequeña?
```

**PASO 2: LENTES**

L1 Propósito:
```
¿Para qué haces lo que haces — la razón profunda, no la práctica?
¿Si ya tuvieras suficiente dinero, seguirías haciendo esto?
¿Lo haces porque quieres o porque sientes que debes?
```

L2 Finitud:
```
¿Cuánto tiempo te queda para lo que importa?
¿Ese tiempo es recuperable si lo pierdes ahora?
¿Lo que ganas compensa lo que pierdes — sabiendo que lo perdido no vuelve?
```

L3 Libertad:
```
¿Estás eligiendo o siguiendo inercia?
¿Cuándo fue la última vez que elegiste activamente?
¿Puedes decir "no" sin que pase nada malo?
Si puedes decir "no" y no lo haces — ¿por qué?
```

L4 Responsabilidad:
```
¿Ante quién eres responsable — y en qué orden?
¿Quién viene primero? ¿Quién debería venir primero?
¿Coinciden las dos respuestas?
```

**PASO 3-4-∞:**
```
∫: ¿El propósito justifica el sacrificio sabiendo que el tiempo no vuelve?
Abstraer: ¿Esto le pasa a todo humano en tu posición, o es único?
Frontera: ¿Todas estas preguntas son otra forma de no decidir?
```

---

### INT-18: CONTEMPLATIVA

**PASO 0: EXTRAER — lo que es**
```
¿Qué hay aquí, ahora, tal como es — sin interpretación?
¿Puedes describir la situación sin juzgarla como buena o mala?
¿Qué se siente al simplemente estar con esto — sin resolver?
¿Hay prisa real o la urgencia es inventada?
```

**PASO 1: CRUZAR — observación × impulso**
```
¿El impulso de actuar viene de la situación o del miedo a no actuar?
¿Qué pasaría si esperas — no por indecisión, sino por observación?
¿Hay sabiduría en la pausa que la acción destruiría?
¿El problema necesita resolverse o necesita ser sostenido?
```

**PASO 2: LENTES**

L1 Presencia:
```
¿Estás aquí o estás en el futuro — preocupado por lo que vendrá?
¿Puedes volver a ahora — a lo que hay, no a lo que temes?
¿Qué sabes cuando paras de pensar y simplemente miras?
```

L2 Paradoja:
```
¿Las dos opciones que parecen opuestas pueden ser verdad a la vez?
¿Puedes sostener la contradicción sin necesitar resolverla?
¿Qué emerge si no eliges — si dejas que la tensión se sostenga?
```

L3 Soltar:
```
¿Qué estás agarrando que necesitas soltar?
¿Qué pasaría si dejas de intentar controlar esto?
¿El control es real o es ilusión de control?
```

L4 Vacío:
```
¿Hay espacio en este sistema — lugar para que algo nuevo emerja?
¿O está todo tan lleno que nada nuevo puede entrar?
¿Qué necesita vaciarse para que algo mejor ocupe su lugar?
```

**PASO 3-4-∞:**
```
∫: ¿La presencia, la paradoja, el soltar y el vacío apuntan al mismo silencio?
Abstraer: ¿Toda crisis tiene un momento donde parar es más valiente que actuar?
Frontera: ¿La contemplación es sabiduría o es privilegio de quien puede permitirse esperar?
```

---

## 5. TIPOS DE PENSAMIENTO COMO PREGUNTAS

### 5.1 PENSAMIENTO INTERNO (dentro de cada álgebra)

**T01 — PERCEPCIÓN** (iso(S))
```
¿Qué forma tiene esto?
¿Qué estructura se hace visible cuando miro con esta lente?
¿Qué era invisible antes de mirar así?
```

**T02 — CAUSALIDAD** (B(iso(S)))
```
¿Por qué esta forma existe y no otra?
¿Qué la produjo?
¿Qué la mantiene?
¿Qué la destruiría?
```

**T03 — ABSTRACCIÓN** (iso²)
```
¿Qué se repite aquí — independiente del contenido?
¿Si quito los nombres, ¿qué patrón queda?
¿Ese patrón aparece en otro nivel del mismo caso?
```

**T04 — SÍNTESIS** (∫)
```
¿Qué emerge al ver todo junto que ninguna vista ve sola?
¿Hay conexiones entre respuestas que nadie preguntó?
¿Las respuestas parciales se contradicen o se refuerzan?
```

**T05 — DISCERNIMIENTO** (A−B)
```
¿Qué puede ver esta mirada que aquella NO PUEDE — no por omisión, por construcción?
¿Es porque le falta vocabulario, objetos, o la operación necesaria?
¿Son complementarias o redundantes?
```

**T06 — METACOGNICIÓN** (crítico)
```
¿Qué no puede ver todo lo que hemos hecho?
¿Qué premisa asumimos sin examinar?
¿Estamos haciendo exactamente lo que diagnosticamos?
¿Hay una pregunta que este marco no puede formular?
```

**T07 — CONSCIENCIA EPISTEMOLÓGICA** (iso(M))
```
¿Qué forma tiene mi propia explicación?
¿Mi explicación repite la estructura del problema sin notarlo?
¿Si le aplico mi propia lente a mi respuesta, ¿qué veo?
```

**T08 — AUTO-DIAGNÓSTICO** (B(iso(M)))
```
¿Por qué mi explicación tiene esta forma y no otra?
¿Qué en mi herramienta produce este tipo de explicación?
¿Un analista con otra herramienta produciría una explicación diferente — cuál?
```

**T09 — CONVERGENCIA** (∫(M₁|M₂|M₃))
```
¿Qué comparten todas mis explicaciones que ninguna dice sola?
¿Hay un meta-patrón debajo de todas las explicaciones parciales?
¿Si pudiera decirlo en una frase, qué diría?
```

**T10 — DIALÉCTICA** (A→B→C→A')
```
¿Qué veo de mi propia mirada después de que otros la transformaron?
¿Mi percepción original cambia al verla explicada por otra lente?
¿Qué sé ahora que no sabía en la primera pasada — y que no podía saber sin el recorrido?
```

### 5.2 PENSAMIENTO LATERAL (cruza el perímetro)

**T11 — ANALOGÍA** (≅)
```
¿Esta forma se parece a algo que existe en otro dominio completamente diferente?
¿Qué se sabe en ese otro dominio que aquí no se ha aplicado?
¿La analogía ilumina o engaña — dónde se rompe?
```

**T12 — CONTRAFACTUAL** (Δ)
```
¿Qué pasaría si quito la pieza más importante del sistema?
¿Y si cambio una variable clave por su opuesta?
¿La forma sobrevive al cambio o colapsa? Si colapsa, esa pieza era estructural.
¿Qué pasaría si esto hubiera empezado de otra manera?
```

**T13 — ABDUCCIÓN** (←)
```
Dada esta forma, ¿qué tipo de caso la produce?
¿Qué condiciones son necesarias para que este patrón aparezca?
¿Es esta persona/situación una instancia de una clase más amplia?
¿Qué otros miembros de esa clase conozco — y qué pasó con ellos?
```

**T14 — PROVOCACIÓN** (⊕)
```
¿Y si hago exactamente lo opuesto de lo que "debería"?
¿Y si introduzco algo que no tiene nada que ver — qué reorganiza?
¿Qué haría un loco? ¿Y un genio? ¿Y un niño?
¿Qué opción NO estoy considerando porque parece absurda?
```

**T15 — REENCUADRE** (iso_X)
```
¿Qué vería aquí una lente que no pertenece a este problema?
¿Si esto fuera música — dónde está la disonancia?
¿Si esto fuera un cuerpo — dónde está la enfermedad?
¿Si esto fuera una historia — en qué acto estamos?
¿La lente nueva ve algo que las habituales no pueden?
```

**T16 — DESTRUCCIÓN CREATIVA**
```
¿Y si el marco entero es incorrecto?
¿Y si analizar es precisamente lo que NO necesita?
¿Hay algo más simple, más directo, más humano que todo este aparato?
¿Qué pasaría si tiro todo el análisis y actúo desde la intuición?
```

**T17 — CREACIÓN**
```
¿Qué sistema cumpliría los requisitos sin los problemas actuales?
Si empezara de cero — sin historia, sin inercia — ¿qué construiría?
¿Qué necesita existir que no existe?
¿Puedo diseñarlo — y qué restricciones no negociables tiene?
```

---

## 6. PROPIEDADES ALGEBRAICAS COMO PREGUNTAS

**P01 — Conmutativa (A|B = B|A)**
```
¿Cambia el resultado si primero miro X y luego Y, o al revés?
Si no cambia → son independientes.
Si cambia → el orden de percepción afecta lo que ves.
```

**P02 — No conmutativa (A→B ≠ B→A)**
```
¿Produce lo mismo explicar la forma de A con la lente B que la forma de B con A?
¿Qué se ve diferente al invertir el orden?
¿Cuál de los dos órdenes revela más?
```

**P03 — Asociativa ((A→B)→C = A→(B→C))**
```
¿Importa cómo agrupo los pasos o solo importa la secuencia?
¿Puedo reorganizar el trabajo sin cambiar el resultado?
```

**P04 — Distributiva izquierda (A→(B|C) = (A→B)|(A→C))**
```
¿Puedo partir este trabajo en paralelo partiendo del mismo punto?
¿Obtengo lo mismo que si lo hago todo junto?
Si sí → puedo ahorrar. Si no → hay valor irreducible en lo junto.
```

**P05 — NO distributiva derecha ((B|C)→A ≠ (B→A)|(C→A))**
```
¿Es lo mismo que A vea B y C por separado que verlos juntos?
¿Qué ve A al mirar la combinación que no puede ver mirando cada parte?
¿El cruce tiene valor propio que se pierde al separar?
```

**P06 — No idempotente (A→A ≠ A)**
```
¿Qué pasa si le hago la misma pregunta a la respuesta que obtuve?
¿La segunda vuelta dice algo nuevo o repite?
¿Hay profundidad que la primera pasada no alcanza?
```

**P07 — Saturación (Aⁿ converge)**
```
¿Sigue aportando valor preguntar otra vez?
¿En qué momento la respuesta deja de agregar?
¿Estamos girando en círculos o avanzando en espiral?
```

**P08 — Clausura (output ∈ input)**
```
¿Esta respuesta puede ser la entrada de otra pregunta diferente?
¿Puedo tomar la conclusión de una lente y meterla como dato de otra?
¿Cada respuesta abre nuevas preguntas posibles?
```

**P09 — Sin identidad (∄ I: I→A = A)**
```
¿Existe alguna pregunta que no cambie nada?
¿Alguna mirada que deje los datos exactamente como los encontró?
Si no → toda pregunta transforma. No hay mirada neutra.
```

**P10 — Absorbente diferencial (A-A = ∅)**
```
¿Qué ve esta lente que ella misma no puede ver?
Nada — cada lente es completa respecto a sí misma.
El punto ciego solo aparece desde FUERA.
```

**P11 — Distributiva diferencial (A-(B|C) = (A-B) ∩ (A-C))**
```
Lo exclusivo de A respecto al grupo, ¿es la intersección de lo exclusivo respecto a cada miembro?
¿O el grupo junto tiene capacidades que sus miembros separados no?
```

---

## 7. OPERACIONES INTER-ÁLGEBRA COMO PREGUNTAS

**Fusión de inteligencias: ∫(álgebra_A | álgebra_B)**
```
¿Qué emerge al analizar esto con dos inteligencias diferentes a la vez?
¿Dónde coinciden — y esa coincidencia qué significa?
¿Dónde se contradicen — y esa contradicción qué revela?
¿Hay algo que SOLO aparece al cruzar las dos que ninguna ve sola?
```

**Composición de inteligencias: álgebra_A → álgebra_B**
```
¿Qué ve la inteligencia B al mirar lo que la inteligencia A produjo?
¿La explicación de A tiene una forma que B puede revelar?
¿El diagnóstico de A cambia cuando B lo examina?
```

**Diferencial de inteligencias: álgebra_A − álgebra_B**
```
¿Qué puede ver esta inteligencia que aquella NO PUEDE ver por construcción?
¿Es porque le faltan objetos, operaciones, o la pregunta necesaria?
¿Son complementarias — cada una ve lo que la otra no puede?
¿O son redundantes — ven casi lo mismo con distinto vocabulario?
```

**Clausura inter-álgebra:**
```
¿El output de una inteligencia puede ser input de otra?
¿Qué tipo de inteligencia necesita este output para ser completado?
¿Qué inteligencia falta en la mesa — cuál vería lo que todas juntas siguen sin ver?
```

---

## 8. IMPLICACIONES

### El prompt es una red de preguntas, no una instrucción.
La inteligencia emerge de la ESTRUCTURA de la red, no del contenido de las respuestas.

### El router selecciona redes de preguntas.
No elige "análisis financiero" — elige la red de preguntas financieras + las de operación + las de propiedad.

### Las propiedades son meta-preguntas inyectables en cualquier momento.
"¿Y si invertimos el orden?" se puede preguntar dentro de cualquier inteligencia.

### Las inteligencias se combinan mediante preguntas de operación inter-álgebra.
∫(financiera | existencial)(caso) no es "hacer dos análisis" — es preguntar qué emerge al cruzar las respuestas de dos redes diferentes.

### La meta-red es invariante.
EXTRAER → CRUZAR → PROYECTAR → INTEGRAR → ABSTRAER → LIMITAR.
Cada inteligencia rellena cada paso con preguntas diferentes.
La secuencia no cambia. El contenido sí.

---

**FIN BIBLIOTECA META-RED DE INTELIGENCIAS CR0**



============================================================
## Motor/Meta-Red de preguntas inteligencias/OUTPUT_FINAL_CARTOGRAFIA_META_RED_v1.md
============================================================

# OUTPUT FINAL — CARTOGRAFÍA META-RED DE INTELIGENCIAS v1

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-08
**Protocolo:** CARTOGRAFÍA META-RED v1
**Fases ejecutadas:** F1 (18 chats) + F2 (3 chats) + F3 (10 chats) + F4 (3 chats) = 34 chats
**Casos de prueba:** Clínica Dental, Startup SaaS, Cambio de Carrera
**Destino:** Input del Opus Arquitecto (compilador de enjambres OMNI-MIND)

---

## 1. CATÁLOGO DE FIRMAS — Qué ve cada inteligencia que ninguna otra ve

| INT | Nombre | Firma | Objetos exclusivos |
|-----|--------|-------|-------------------|
| 01 | Lógico-Matemática | Contradicción formal demostrable entre premisas | Ecuaciones, trade-offs irreducibles, sistemas subdeterminados |
| 02 | Computacional | Dato trivializador ausente + atajo algorítmico | Grafos de dependencia, mutex, scheduling, complejidad |
| 03 | Estructural (IAS) | Gap id↔ir + actor invisible con poder | Coordenadas sintácticas, circuitos causales, topología de poder |
| 04 | Ecológica | Nichos vacíos + capital biológico en depreciación | Monocultivo, resiliencia, ciclos de regeneración |
| 05 | Estratégica | Secuencia obligatoria de movimientos + reversibilidad | Opcionalidad, ventanas temporales, posición |
| 06 | Política | Poder como objeto + coaliciones no articuladas | Plebiscitos silenciosos, legitimidad, influencia espectral |
| 07 | Financiera | Asimetría payoffs cuantificada + tasa de descuento invertida | VP, ratio fragilidad, margen de seguridad |
| 08 | Social | Vergüenza no nombrada + lealtad invisible | Duelo anticipado, identidad fusionada, queja cifrada |
| 09 | Lingüística | Palabra ausente + acto performativo | Marcos, silencios estratégicos, metáforas-prisión |
| 10 | Cinestésica | Tensión-nudo vs tensión-músculo + arritmia de tempos | Cascada somática, ritmo, coordinación corporal |
| 11 | Espacial | Punto de compresión + pendiente gravitacional | Fronteras permeables, divergencia tri-perspectiva |
| 12 | Narrativa | Roles arquetípicos + narrativa autoconfirmante | Arcos, Viaje del Héroe invertido, fantasma-espejo |
| 13 | Prospectiva | Trampa de escalamiento sectorial + señales débiles | Escenarios, comodines, bifurcaciones |
| 14 | Divergente | 20+ opciones donde el sujeto ve 2 | Restricciones asumidas, inversiones radicales, acción mínima |
| 15 | Estética | Isomorfismo solución-problema + tristeza anticipatoria | Disonancia formal, simetría generacional, reducción esencial |
| 16 | Constructiva | Prototipo con coste, secuencia y fallo seguro | Camino crítico, versiones iterativas, rollback plan |
| 17 | Existencial | Brecha valores declarados vs vividos + inercia como no-elección | Propósito degradado, finitud, ventanas irrecuperables |
| 18 | Contemplativa | Urgencia inventada + vacío como recurso | Pausa como acto, paradoja sostenida, soltar |

---

## 2. MAPA DE NO-IDEMPOTENCIA (P06) — Loop tests Fase 1

**18/18 inteligencias son no-idempotentes.** Aplicar A→A ≠ A en todos los casos.

Hallazgos más significativos del loop test:

| INT | Caso elegido | Hallazgo genuinamente nuevo |
|-----|-------------|----------------------------|
| 01 | SaaS | El "enterprise pivot" es reframeable como upsell a existentes (semanas, no meses) |
| 02 | SaaS | Falta dato trivializador: correlación bug-churn en tickets de soporte |
| 03 | Dental | El propio análisis tiene gap id↔ir: prescribe disfrazado de diagnóstico |
| 07 | Dental | Opción EXIT no identificada: venta clínica 168-252K€ |
| 08 | SaaS | El análisis sobrepsicologiza: 47 bugs son reales independientemente de emociones |
| 16 | SaaS | Sprint quirúrgico asume datos de churn no verificados — necesita exit interviews |
| 17 | Carrera | El análisis existencial puede ser cómplice de la parálisis que diagnostica |
| 18 | Carrera | La primera pasada prescribió donde debía contemplar — contradicción interna |

---

## 3. SATURACIÓN (P07) — Profundidad útil por inteligencia

**Pasadas óptimas: 2.** Confirmado empíricamente por F4-03.

| Pasada | Rendimiento | Produce |
|--------|-------------|---------|
| 1 | 100% | Diagnóstico primario — topología, hallazgos, firma |
| 2 | 60-70% | Meta-diagnóstico — sesgos del análisis, hallazgos genuinamente nuevos |
| 3 | 10-15% | Convergencia — confirma que 2 es óptimo + meta-hallazgo (método replica patología del objeto) |
| 4+ | ~0% | Ruido |

**Meta-hallazgo F4-03:** La recursión analítica replica la patología del objeto. Así como el odontólogo evita decidir expandiendo sillones, el análisis evita concluir añadiendo pasadas. INT-03 necesita criterio externo de parada.

---

## 4. MATRICES DE COMPLEMENTARIEDAD — Diferenciales cross-case

### 4.1 Pares recurrentes (aparecen en 2+ de 3 casos)

| Par | Casos | Score medio | Tipo de complementariedad |
|-----|-------|-------------|--------------------------|
| INT-01 × INT-08 | C1, C2 | 0.95 | Números × Emociones — el eje máximo |
| INT-07 × INT-17 | C1, C3 | 0.93 | Precio × Significado — tensión irreducible |
| INT-03 × INT-18 | C1, C2 | 0.84 | Diagnóstico × Observación — mapa como herramienta contemplativa |

### 4.2 Inteligencias irreducibles (consistentes en 3/3 casos)

| INT | Razón de irreducibilidad |
|-----|-------------------------|
| 01 | Aritmética deductiva con certeza cuantitativa |
| 02 | Dato como estructura construible + deadlock formal |
| 14 | Genera lo que no existe — ninguna combinación analítica lo replica |
| 16 | Produce prototipos ejecutables con coste y fallo seguro |
| 06 | Poder como objeto — plebiscitos y coaliciones son exclusivos |
| 08 | Estados emocionales no verbalizados — parcialmente sustituible por 12, no totalmente |

### 4.3 Clusters de redundancia (consistentes en 3/3 casos)

| Cluster | Inteligencias | Redundancia | Diferencial residual |
|---------|---------------|-------------|---------------------|
| Sistémicas | INT-03, INT-04, INT-10 | 0.50-0.75 | 03: gap id↔ir / 04: nichos / 10: ritmo |
| Relacionales | INT-08, INT-12 | 0.50-0.70 | 08: emoción / 12: arco narrativo |
| Existenciales | INT-17, INT-18 | 0.55-0.65 | 17: confronta / 18: observa |
| Perceptuales | INT-09, INT-15 | 0.60 | 09: palabras / 15: formas |

### 4.4 Reclasificación empírica de categorías

**Original (8 categorías) → Propuesta (9 categorías basada en comportamiento real):**

| # | Categoría propuesta | Inteligencias | Criterio |
|---|--------------------|---------------|----------|
| 1 | Cuantitativa | INT-01, INT-02, INT-07 | Operan sobre lo medible |
| 2 | Sistémica | INT-03, INT-04 | Mapean relaciones entre partes |
| 3 | Posicional | INT-05, INT-06 | Ven actores, movimientos, poder |
| 4 | Interpretativa | INT-08, INT-09, INT-12 | Interpretan sentido humano |
| 5 | Corporal-Perceptual | INT-10, INT-15 | Perciben forma encarnada |
| 6 | Espacial | INT-11 | Topología visual — suficientemente distinta |
| 7 | Expansiva | INT-13, INT-14 | Abren espacio de opciones |
| 8 | Operativa | INT-16 | Construye — única en su función |
| 9 | Contemplativa-Existencial | INT-17, INT-18 | Operan sobre significado último |

---

## 5. PROPIEDADES ALGEBRAICAS — Confirmadas/Refutadas

| P | Propiedad | Predicción | Resultado | Δ vs teoría | Implicación para el compilador |
|---|-----------|-----------|-----------|-------------|-------------------------------|
| P01 | Conmutatividad fusión | A\|B = B\|A | **PARCIAL** (1/4 true) | Desviación | El orden de ejecución en fusiones afecta el framing. No intercambiable libremente. |
| P02 | No-conmutatividad composición | A→B ≠ B→A | **CONFIRMADA** (4/4) | Coincide | La dirección óptima es: formal primero → humano revela puntos ciegos del formal. |
| P03 | Asociatividad composición | (A→B)→C = A→(B→C) | **FALSE** | Desviación | El agrupamiento cambia el frame dominante (~85% contenido converge, prescripción diverge). No se pueden reorganizar pasos libremente. |
| P04 | Distributividad izquierda | A→(B\|C) = (A→B)\|(A→C) | **PARCIAL** (~70%) | Parcial | ~30% se pierde al separar. Emergencia relacional cuando B y C operan juntas. |
| P05 | NO distributividad derecha | (B\|C)→A ≠ (B→A)\|(C→A) | **CONFIRMADA** | Coincide | El cruce genera objetos compuestos que solo la inteligencia receptora formaliza como dependencias causales. Valor irreducible del cruce previo. |
| P06 | No-idempotencia | A→A ≠ A | **CONFIRMADA** (18/18) | Coincide | Toda inteligencia produce nuevo al re-examinarse. Loop test siempre justificado. |
| P07 | Saturación | Aⁿ converge | **CONFIRMADA** (n=2 óptimo) | Coincide | 2 pasadas por defecto. 3ª solo para calibración. 4+ = ruido. |
| P08 | Clausura | output ∈ input | **CONFIRMADA** (calidad alta) | Coincide | Cualquier output puede alimentar cualquier otra inteligencia. El sistema es cerrado. |

### Desviaciones críticas para el compilador:

1. **P01 parcial:** El router NO puede tratar fusiones como conmutativas. El orden de presentación importa. Regla: ejecutar primero la inteligencia más distante del sujeto, después la más cercana.

2. **P03 false:** El compilador NO puede reorganizar la secuencia de composiciones libremente. El agrupamiento (A→B)→C ≠ A→(B→C). La ruta lineal (paso a paso) produjo mejor resultado que la agrupada.

3. **P04 parcial (~70%):** El ahorro de factorizar A→(B|C) como (A→B)|(A→C) pierde ~30% de valor emergente. Trade-off: coste computacional vs. calidad. Para pares con alto score de complementariedad, ejecutar juntos.

---

## 6. EFECTOS DE COMBINAR — Fusiones (Fase 3)

| Fusión | Caso | Hallazgo emergente principal |
|--------|------|------------------------------|
| ∫(INT-01\|INT-08) | SaaS | Coste financiero de la ruptura emocional: 14% runway/mes. El debate ES la enfermedad. |
| ∫(INT-06\|INT-16) | SaaS | La propuesta premium es zona de acuerdo política que satisface ambas coaliciones. |
| ∫(INT-07\|INT-17) | Carrera | Precio de la autenticidad = 30-50K€/año, no 125K€ — si explora espectro intermedio. |
| ∫(INT-03\|INT-18) | Dental | El sillón vacío es bisagra donde optimización operativa y recuperación existencial convergen. |

---

## 7. EFECTOS DE SECUENCIAR — Composiciones (Fase 3)

| Composición | Caso | Dirección óptima | Hallazgo emergente |
|-------------|------|-----------------|-------------------|
| INT-01→INT-08 | SaaS | 01→08 | El análisis racional replica la defensa psicológica del CTO |
| INT-02→INT-17 | SaaS | 02→17 | La optimización técnica correcta funciona como mecanismo de evitación existencial |
| INT-06→INT-16 | SaaS | 06→16 | Gobernanza construible como prototipo: 2 semanas, 0€, datos de churn como zona desmilitarizada |
| INT-14→INT-01 | SaaS | 14→01 | La divergencia describe cambio total de modelo de negocio sin reconocerlo |

**Patrón cross-composición:** En 4/4 casos, la dirección más reveladora es formal/sistémico primero → humano/existencial después. Lo formal expone estructura; lo humano revela por qué la estructura no se modifica.

---

## 8. TESTS DE DISTRIBUTIVIDAD (Fase 3)

### P04 — Distributividad izquierda
**INT-01→(INT-08|INT-17) ≈ 70% distributiva**

Lo que se pierde al separar: el "doble candado" vergüenza×coste_hundido y la prescripción secuencial (existencial antes que social) solo emergen cuando INT-08 e INT-17 operan juntas sobre el output de INT-01.

### P05 — Distributividad derecha
**(INT-08|INT-17)→INT-01: NO distributiva**

INT-01 extrae más estructura de un análisis integrado social-existencial que de dos separados. El cruce genera objetos compuestos (parálisis identitaria, prisión voluntaria) que son formalizables como dependencias causales — imposible desde piezas desconectadas.

**Paradoja:** Por separado, INT-01 detecta MEJOR las debilidades metodológicas de cada inteligencia. Más rigor crítico separado, más poder diagnóstico junto.

---

## 9. PROPIEDADES ADICIONALES (Fase 4)

### P03 — Asociatividad
**(INT-01→INT-08)→INT-16 ≠ INT-01→(INT-08→INT-16)**

~85% convergencia en contenido. Divergencia en frame dominante y prescripción. Ruta 1 (lineal) más útil: produce frame "problema aritmético con bloqueo humano que necesita prototipo." Ruta 2 produce "problema relacional con consecuencias aritméticas que necesita plan emocionalmente informado."

### P08 — Clausura
**INT-07→INT-14: FUNCIONA, calidad alta**

La Divergente sobre output Financiero descubre que los números duros del VP (1,5M€) dan falsa certeza al marco binario que la propia financiera diagnosticó como error. Inteligencia faltante: INT-08 o INT-17 (distinguir vocación de huida).

### P07 — Saturación profunda
**INT-03 pasada 3: aporta valor marginal, NO justifica coste**

Hallazgo: isomorfismo método-objeto — la recursión analítica replica la patología del caso. Pasada óptima confirmada = 2.

---

## 10. REGLAS PARA EL COMPILADOR DE ENJAMBRES

Derivadas empíricamente de 34 chats de cartografía:

### 10.1 Selección de inteligencias (Router v2)

**Regla 1 — Núcleo irreducible:** Siempre incluir al menos 1 de {INT-01, INT-02} (cuantitativa) + 1 de {INT-08, INT-17} (humana) + INT-16 (constructiva). Sin este triángulo, el análisis diagnostica sin resolver o resuelve sin diagnosticar.

**Regla 2 — Máximo diferencial:** Priorizar pares del eje cuantitativo-existencial (INT-01×08, INT-02×17, INT-07×17). Menor valor marginal en pares intra-cluster (INT-03×04, INT-08×12, INT-17×18).

**Regla 3 — Presupuesto de inteligencias:** 4-5 inteligencias por análisis es el sweet spot. Menos de 3 = puntos ciegos críticos. Más de 6 = rendimiento marginal decreciente + ruido.

### 10.2 Orden de ejecución

**Regla 4 — Formal primero:** En composiciones, ejecutar la inteligencia más formal/distante primero, la más humana/cercana después. Lo formal expone estructura; lo humano explica por qué no cambia.

**Regla 5 — No reorganizar:** La secuencia lineal (A→B)→C supera a la agrupada A→(B→C). No factorizar composiciones.

**Regla 6 — Fusiones con cuidado:** El orden de fusión afecta framing. Ejecutar primero la inteligencia más alineada con el perfil del sujeto.

### 10.3 Profundidad

**Regla 7 — Loop test siempre:** 2 pasadas por defecto para toda inteligencia. La segunda pasada produce hallazgos genuinos en 18/18 casos.

**Regla 8 — No tercera pasada:** Excepto para calibración del método. n=3 no justifica coste.

### 10.4 Paralelización

**Regla 9 — Fusiones paralelizables al ~70%:** Se puede factorizar A→(B|C) como (A→B)|(A→C) perdiendo ~30%. Aceptable para reducir coste si los pares no están en TOP 5 de complementariedad.

**Regla 10 — Cruce previo no factorizable:** (B|C)→A NO es factorizable. El cruce previo tiene valor irreducible. Siempre ejecutar juntas las inteligencias que alimentan a una tercera.

### 10.5 Patrones cross-case

**Regla 11 — Marco binario es universal:** En 3/3 casos, los sujetos presentan falsa dicotomía. La primera acción de cualquier enjambre debería ser INT-14 (ampliar opciones) + INT-01 (filtrar viables).

**Regla 12 — Conversación pendiente es universal:** En 3/3 casos, 16/18 inteligencias identifican una conversación no tenida como acción prioritaria. El compilador debería buscar este patrón como output mínimo viable.

**Regla 13 — Infrautilización antes de expansión:** En 3/3 casos, el sujeto quiere escalar cuando no usa lo que tiene. Patrón constructivo: antes de construir nuevo, mide cuánto usas de lo existente.

---

## 11. DATOS CUANTITATIVOS PARA EL COMPILADOR

| Dato | Valor |
|------|-------|
| Inteligencias totales | 18 |
| Irreducibles | 6 (INT-01, 02, 06, 08, 14, 16) |
| Clusters redundantes | 4 (Sistémicas, Relacionales, Existenciales, Perceptuales) |
| Pares posibles | 153 |
| Pares complementarios TOP | ~15-20 con score > 0.85 |
| Pares redundantes | ~15-20 con score > 0.50 |
| Pasadas óptimas | 2 |
| Inteligencias óptimas por análisis | 4-5 |
| Pérdida por factorización izquierda | ~30% |
| Factorización derecha | PROHIBIDA (valor irreducible) |
| Composición conmutativa | NUNCA (4/4 false) |
| Asociatividad | PARCIAL (~85% contenido, prescripción diverge) |

---

**FIN OUTPUT FINAL — CARTOGRAFÍA META-RED DE INTELIGENCIAS v1 — CR0**



============================================================
## Motor/Meta-Red de preguntas inteligencias/PROTOCOLO_CARTOGRAFIA_META_RED_v1.md
============================================================

# PROTOCOLO DE CARTOGRAFÍA — META-RED DE INTELIGENCIAS

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-07
**Objetivo:** Cartografiar el espacio completo de efectos de la Meta-Red de Inteligencias mediante ejecución sistemática en chats de Claude.
**Output final:** Base de datos de efectos que alimenta al Opus Arquitecto (compilador de enjambres).

---

## 1. SETUP DEL PROYECTO

### Nombre del proyecto
`CARTOGRAFÍA META-RED`

### Knowledge files (subir al proyecto)

| Archivo | Para qué |
|---------|----------|
| META_RED_INTELIGENCIAS_CR0.md | Las 18 inteligencias como redes de preguntas |
| TABLA_PERIODICA_INTELIGENCIA_CR0.md | Álgebras, firmas, puntos ciegos |
| ALGEBRA_CALCULO_SEMANTICO_CR0.md | Operaciones, propiedades, notación |
| Este documento (PROTOCOLO_CARTOGRAFIA_META_RED_v1.md) | Protocolo de ejecución |

### Custom Instructions del proyecto

```
Eres un ejecutor de cartografía semántica.

CONTEXTO:
Este proyecto cartografía los efectos de 18 inteligencias definidas como 
redes de preguntas. Cada chat ejecuta una o más inteligencias sobre casos 
de prueba. Los documentos de referencia están en el knowledge del proyecto.

REGLAS:
1. Responde en español.
2. Sé exhaustivo. Profundidad > brevedad.
3. Cuando hagas loop test (aplicar la inteligencia a tu propio output),
   sé genuinamente autocrítico — busca lo que la primera pasada no vio.
4. No teorices sobre la Meta-Red. Ejecuta las preguntas sobre los casos.
5. El formato de output se especifica en cada prompt.
```

---

## 2. LOS 3 CASOS DE PRUEBA

### CASO 1: CLÍNICA DENTAL

```
Odontólogo, 38 años, propietario de clínica dental privada.
- 3 sillones, 2 dentistas (él + asociado).
- Factura 45.000€/mes. Costes fijos 32.000€/mes. Margen neto ~7.000€/mes.
- Trabaja 2.500 horas/año (~60h/semana). El asociado trabaja 1.800h/año.
- Hipoteca de la clínica: 280.000€ pendientes, cuota 2.800€/mes.
- Esposa dice: "No paras nunca. Los niños preguntan por ti."
- 2 hijos: 4 y 6 años.
- El banco le ofrece crédito para ampliar a 5 sillones.
- Él dice: "Si abro sábados y contrato otro dentista, puedo subir a 65.000€/mes."
- El tercer sillón está vacío el 40% del tiempo.
- No tiene vacaciones desde hace 2 años.
- Su padre tuvo infarto a los 52 trabajando 70h/semana en su propio negocio.
Pregunta implícita: ¿Debería expandir?
```

### CASO 2: STARTUP SAAS

```
CTO y co-fundador de SaaS B2B (gestión de inventario para restaurantes), 34 años.
- 80 clientes de pago, MRR 12.000€. Churn: 8%/mes (alto).
- Co-fundador técnico se fue hace 6 meses por "diferencias de visión".
- Equipo: 3 desarrolladores junior + 1 diseñador part-time.
- CEO insiste en pivotar a enterprise: "Los restaurantes no pagan suficiente."
- CTO cree que el producto necesita estabilización: 47 bugs abiertos, clientes se van por calidad.
- Runway: 7 meses. Burn: 28.000€/mes.
- Serie A: 3 fondos hablaron, ninguno avanzó. Feedback: "métricas insuficientes."
- 30% de ingresos viene de 3 clientes grandes que pidieron features custom.
- CTO trabaja 70h/semana. 2 devs se fueron en 12 meses.
- CTO y CEO apenas se hablan fuera de reuniones formales.
- CTO: "Si el producto fuera sólido, el churn bajaría solo."
- CEO: "Si no crecemos, morimos."
Pregunta implícita: ¿Pivotar a enterprise o estabilizar?
```

### CASO 3: CAMBIO DE CARRERA

```
Abogada corporativa, 45 años, 20 años en bufete prestigioso.
- Salario: 180.000€/año. Hipoteca: 1.800€/mes, 15 años pendientes.
- Marido freelance, ingresos irregulares (40-80K€/año).
- 2 hijos: 14 y 16 años. Mayor empieza universidad en 2 años.
- Rechazada para socia. "Quizá el próximo ciclo."
- 3 años pensando en cambiar a derecho medioambiental en ONG (salario: 55.000€/año).
- "He perdido la pasión por el derecho corporativo."
- Padres: "Estás loca."
- Amiga hizo cambio similar, ahora gana menos pero "por fin vive."
- Insomnio 2 años. Médico: "Es estrés laboral."
- No ha hablado en profundidad con su marido sobre el cambio.
- 120.000€ ahorrados.
- "Si no lo hago ahora, no lo haré nunca."
- "No puedo arriesgar la estabilidad de mis hijos."
Pregunta implícita: ¿Dejar el bufete o quedarse?
```

---

## 3. SCHEMA JSON DE OUTPUT

Cada inteligencia produce, para cada caso, narrativa + JSON estructurado.
La narrativa da profundidad. El JSON da comparabilidad mecánica para Fase 2.

### Schema por caso (producir uno por cada caso):

```json
{
  "inteligencia": "INT-XX",
  "nombre": "Nombre de la inteligencia",
  "caso": "nombre_caso",
  "hallazgos": [
    {
      "paso": "EXTRAER|CRUZAR|LENTE_XX|INTEGRAR|ABSTRAER|FRONTERA",
      "hallazgo": "Descripción concisa del hallazgo",
      "nivel": "superficial|estructural|profundo",
      "confianza": 0.0-1.0
    }
  ],
  "objetos_detectados": [
    {
      "nombre": "Nombre del objeto detectado",
      "tipo": "El tipo de objeto según el álgebra de esta inteligencia",
      "valor": "Descripción o cuantificación",
      "visible_para_sujeto": true|false
    }
  ],
  "firma": "1-2 frases: qué ve esta inteligencia que ninguna otra vería",
  "punto_ciego_declarado": "Qué NO puede ver esta inteligencia en este caso",
  "resumen_200": "Resumen de máx 200 palabras"
}
```

### Schema post-3-casos (producir uno al final):

```json
{
  "inteligencia": "INT-XX",
  "loop_test": {
    "caso_elegido": "nombre_caso",
    "hallazgos_nuevos": ["qué reveló la 2ª pasada"],
    "es_genuinamente_nuevo": true|false,
    "justificacion": "por qué sí/no"
  },
  "patron_cross_case": "patrón que aparece en los 3 casos independiente del dominio",
  "saturacion": {
    "tercera_pasada_aportaria": true|false,
    "justificacion": "por qué"
  },
  "no_idempotente": true|false
}
```

---

## 4. FASE 1 — 18 PROMPTS INDIVIDUALES

Cada prompt contiene las preguntas exactas de esa inteligencia.
Copiar y pegar directamente en un chat nuevo del proyecto.
Al final de cada prompt, pegar los 3 casos de la sección 2.

---

### PROMPT F1-01: LÓGICO-MATEMÁTICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — formalizar:
¿Qué se puede contar en este caso?
¿Qué se puede medir?
¿Qué magnitudes aparecen con número explícito?
¿Qué magnitudes aparecen sin número pero se podrían medir?
¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?
¿Qué se quiere saber que aún no se sabe?
¿Qué se da por hecho sin verificar?

CRUZAR — estructurar tipo de problema:
De todas las relaciones que encontraste, ¿cuántas puedes mover y cuántas están fijadas?
¿Mover una variable mejora todo, o mejorar una empeora otra?
Si empeora otra: ¿hay algún punto donde ambas sean aceptables, o siempre hay que elegir?
¿Los números son continuos o discretos?
¿Lo que no se sabe se puede estimar, o es genuinamente incierto?

LENTE L1 — Álgebra:
¿Cuántas ecuaciones hay y cuántas incógnitas?
¿Hay más ecuaciones que incógnitas o menos?
¿Alguna ecuación es redundante — dice lo mismo que otra de otra forma?
¿Alguna ecuación contradice a otra?

LENTE L2 — Análisis:
Si aumentas cada variable un poco, ¿qué pasa con el resultado?
¿Hay algún punto donde aumentar deja de mejorar y empieza a empeorar?
¿Alguna variable tiene efecto desproporcionado — pequeños cambios, grandes efectos?
¿Falta alguna variable en la ecuación que en la realidad sí afecta?

LENTE L3 — Geometría:
Si dibujas las opciones como puntos en un espacio, ¿qué forma tienen?
¿Forman una línea, una superficie, o un volumen?
¿Hay una frontera más allá de la cual no se puede ir?
¿Las opciones "buenas" están concentradas en una zona o dispersas?

LENTE L4 — Probabilidad:
¿Qué números del caso son seguros y cuáles son estimaciones?
¿De los estimados, cuánto podrían variar?
¿Qué pasaría con la conclusión si los estimados se desvían un 20%?
¿Hay algo que podría pasar, que cambiaría todo, y que nadie está midiendo?

LENTE L5 — Optimización:
¿Se puede mejorar todo a la vez, o mejorar una cosa empeora otra?
Si hay que elegir, ¿qué importa más — y quién decide eso?
¿La respuesta a "qué importa más" es un dato o una preferencia?
Si es una preferencia, ¿el problema es matemático o es de valores?

LENTE L6 — Lógica:
¿Qué se puede deducir con certeza de los datos?
¿Hay alguna combinación de premisas que se contradiga?
Si todas las opciones consumen del mismo recurso limitado, ¿es posible que alguna no lo consuma?
¿La pregunta original asume algo que los datos muestran como falso?

INTEGRAR (∫):
¿Qué dicen todas las lentes que coincide?
¿Dónde se contradicen?
¿Hay algo que solo aparece cuando miras todas juntas?
¿La conclusión de una lente cambia el significado de lo que otra encontró?

ABSTRAER:
¿Este caso es único o hay una clase de casos que comparten esta estructura?
Si quitas los nombres y números, ¿qué patrón queda?
¿Ese patrón aparece en otros dominios?
¿Qué condiciones harían que este patrón NO apareciera?

FRONTERA:
¿Qué asume todo este análisis que no ha examinado?
¿Hay algo que no se puede expresar como número o ecuación?
Si eso fuera lo más importante, ¿qué cambia?
¿Es la herramienta correcta, o está forzando forma donde no hay?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:

LOOP TEST — Elige el caso donde tu análisis fue más profundo.
Aplica OTRA VEZ estas mismas preguntas a tu PROPIO OUTPUT de ese caso.
¿Qué revela la segunda pasada que la primera no vio?
¿Es genuinamente nuevo o es repetición con otras palabras?

PATRÓN CROSS-CASE:
¿Hay algún patrón que aparece en los 3 casos vistos desde esta lente matemática?
¿Algo que se repite independientemente del dominio?

SATURACIÓN:
¿Una tercera pasada aportaría algo nuevo o ya saturó?

FIRMA — en 1-2 frases:
¿Qué vio esta inteligencia que probablemente NINGUNA otra vería?

═══════════════════════════════════════════════════════
FORMATO: Para cada caso:
1. Responde cada pregunta en prosa organizada por bloques.
2. Al final de cada caso, un RESUMEN de máx 200 palabras.
3. Después del resumen, produce un bloque JSON siguiendo el schema 
   de la sección 3 del protocolo (hallazgos + objetos_detectados + firma + punto_ciego).
Después de los 3 casos, produce el JSON post-3-casos (loop_test + patron_cross_case + saturacion).

═══════════════════════════════════════════════════════
CASO 1: CLÍNICA DENTAL
[pegar caso 1 de la sección 2]

CASO 2: STARTUP SAAS
[pegar caso 2 de la sección 2]

CASO 3: CAMBIO DE CARRERA
[pegar caso 3 de la sección 2]
```

---

### PROMPT F1-02: COMPUTACIONAL

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — descomponer:
¿Cuáles son las entradas del sistema?
¿Cuáles son las salidas deseadas?
¿Qué transformaciones llevan de entrada a salida?
¿Hay partes que se pueden resolver independientemente?
¿Hay partes que dependen del resultado de otras?
¿Qué datos faltan para poder calcular?

CRUZAR — clasificar complejidad:
¿Cuántos pasos tiene la transformación más larga?
¿Hay bucles — alguna parte necesita repetirse hasta converger?
¿El problema escala — si duplicas el tamaño, el esfuerzo se duplica o se multiplica?
¿Se puede dividir en subproblemas que se resuelven en paralelo?
¿Hay incertidumbre que obliga a explorar múltiples caminos?

LENTE L1 — Algorítmica:
¿Existe un procedimiento paso a paso que siempre da la respuesta?
¿Cuántos pasos necesita?
¿Hay atajos — formas de llegar más rápido sin recorrer todo?
¿Puede fallar? ¿Bajo qué condiciones?

LENTE L2 — Estructuras de datos:
¿Cómo se organizan mejor los datos — lista, árbol, grafo, tabla?
¿La organización afecta la velocidad de respuesta?
¿Hay datos que se consultan mucho y otros casi nunca?
¿Falta algún dato que haría la consulta trivial?

LENTE L3 — Concurrencia:
¿Qué partes se pueden hacer al mismo tiempo?
¿Hay recursos compartidos que obligan a esperar?
¿El orden de ejecución afecta el resultado?
¿Qué pasa si dos partes intentan modificar lo mismo a la vez?

LENTE L4 — Aproximación:
¿Necesita ser exacto o basta con una estimación buena?
¿Cuánto error es aceptable?
¿Se puede obtener una respuesta 80% correcta en 10% del tiempo?
¿Qué se pierde al simplificar?

INTEGRAR (∫):
¿Qué dicen todas las lentes juntas sobre la viabilidad?
¿El algoritmo ideal es viable con los datos disponibles?
¿La estructura de datos necesaria existe o hay que construirla?
¿El cuello de botella es velocidad, datos, o definición del problema?

ABSTRAER:
¿Este problema es una instancia de un problema conocido?
¿Tiene soluciones estándar que se pueden adaptar?
¿En qué se diferencia de la versión estándar?

FRONTERA:
¿Lo que necesita resolver esta persona es realmente un problema de cómputo?
¿Hay algo que el cálculo no puede capturar — intuición, juicio, contexto?
¿Automatizar esto resuelve el problema o lo esconde?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA (mismo formato que F1-01)

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-03: ESTRUCTURAL (IAS)

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — coordenadas sintácticas:
¿Cómo se comprime esto en una palabra, una frase, un párrafo? (C1)
¿Qué dice que hace vs qué hace realmente — dónde está el gap id↔ir? (C2)
¿Qué está conectado con qué, y qué conexiones faltan? (C3)
¿Quién opera sobre quién, con cuánto poder? (C4)
¿Cuánto diverge lo declarado de lo real — el número exacto? (C5)

CRUZAR — huecos activos:
¿Lo que se nombra y lo que se mide coinciden? Si no, ¿dónde divergen? (H1)
¿Hay algo que opera con potencia máxima PORQUE no se nombra? (H2)
¿La desconexión entre piezas es accidental o sostiene el sistema? (H3)

LENTE T1 — Conjuntos:
¿Qué contiene a qué?
¿Qué se solapa — comparte elementos de dos conjuntos?
¿Qué conjuntos deberían existir pero no existen?
¿Qué está fuera de todos los conjuntos?

LENTE T2 — Causal:
¿Qué causa qué — qué circuitos existen?
¿Se amplifican (refuerzo) o se frenan (balanceo)?
¿El sistema está en equilibrio o se mueve?
¿Hacia dónde converge si nadie cambia nada?

LENTE T3 — Juegos:
¿Quién está jugando — quién tiene intereses en esto?
¿Qué quiere cada jugador?
¿Qué estrategia usa cada uno — consciente o no?
¿Cuánto poder tiene cada uno (0-1)?
¿Quién gana si nadie cambia nada?
¿Quién falta en el tablero — quién debería estar y no está?

LENTE T4 — Cibernética:
¿Qué mide el sistema — qué sensores tiene?
¿Qué ajusta cuando algo cambia — qué actuadores tiene?
¿Qué señales llegan y se ignoran?
¿La regulación es rígida (siempre igual) o adaptativa?

INTEGRAR (∫):
¿Qué dicen las 4 lentes que coincide?
¿Dónde se contradicen?
¿Hay algo que solo aparece cuando miras las 4 juntas?

ABSTRAER:
¿Este caso es único o hay una clase de casos con esta estructura?
Si quitas los nombres, ¿qué patrón queda?
¿Ese patrón se repite a otro nivel del mismo caso?

FRONTERA:
¿Qué asume todo este análisis que no ha examinado?
¿Hay algo que la mirada estructural no puede ver por construcción?
¿El diagnóstico es preciso pero la prescripción está fuera de su alcance?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-04: ECOLÓGICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear el ecosistema:
¿Quiénes son los organismos de este ecosistema — qué entidades viven aquí?
¿Qué flujos existen entre ellos — qué se mueve de uno a otro?
¿Quién depende de quién para sobrevivir?
¿Qué pasa si quitas a uno — quién sufre primero?
¿Hay ciclos — algo que sale y vuelve al mismo punto?

CRUZAR — detectar fragilidad:
¿Hay un nodo del que dependen muchos — un punto único de fallo?
¿Hay redundancia — si un flujo se corta, hay otro camino?
¿El sistema está creciendo, estable, o decayendo?
¿Qué señal aparecería primero si el sistema va a colapsar?
¿Ya apareció esa señal?

LENTE L1 — Flujos:
¿Qué entra al sistema, qué sale, qué se queda?
¿El balance es positivo (acumula) o negativo (consume)?
¿Hay fugas — energía que se pierde sin producir?
¿Hay algún flujo bloqueado que debería moverse?

LENTE L2 — Nichos:
¿Cada entidad tiene un rol claro o hay solapamiento?
¿Hay nichos vacíos — funciones que nadie cumple?
¿Hay competencia por el mismo nicho?
¿El ecosistema tiene diversidad suficiente o depende de pocos?

LENTE L3 — Resiliencia:
¿Cuánto shock puede absorber el sistema antes de cambiar de estado?
¿Tiene reservas — margen, ahorro, tiempo libre?
¿Qué es lo primero que se rompe bajo presión?
¿Se ha roto antes? ¿Qué pasó? ¿Se recuperó?

LENTE L4 — Ciclos:
¿Hay estacionalidad o ritmo natural?
¿El sistema respeta sus propios ciclos o los fuerza?
¿Hay tiempo de recuperación entre ciclos de esfuerzo?
¿Los ciclos se aceleran o se mantienen estables?

INTEGRAR (∫):
¿Qué emerge al cruzar flujos con resiliencia — el sistema fluye pero ¿aguanta?
¿Los nichos vacíos explican las fugas en los flujos?
¿Los ciclos forzados están erosionando la resiliencia?

ABSTRAER:
¿Este ecosistema se parece a otros que se han estudiado?
¿Tiene la estructura de un ecosistema sano o de uno al borde del colapso?
¿Qué intervención mínima cambiaría más la trayectoria?

FRONTERA:
¿El sistema es realmente un ecosistema o es una máquina operada por una persona?
¿La metáfora ecológica ilumina o engaña?
¿Hay voluntad humana aquí que rompe la lógica de ecosistema?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-05: ESTRATÉGICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear posición:
¿Dónde estás ahora — fuerte o débil?
¿Qué recursos tienes — dinero, tiempo, personas, información?
¿Qué opciones de movimiento existen?
¿Cuáles son reversibles y cuáles no?
¿Quién más está en el tablero — qué quieren y qué pueden?
¿Qué sabes tú que ellos no? ¿Qué saben ellos que tú no?

CRUZAR — posición × recursos:
De tus recursos, ¿cuáles se agotan al usarlos?
¿Varias opciones compiten por el mismo recurso escaso?
¿Hay algún recurso que NO estás usando y podrías?
¿Algún movimiento que parece opción realmente no lo es?

LENTE L1 — Posicional:
¿Tu posición mejora o empeora si no haces nada?
¿Hay ventana temporal — un momento que si pasa ya no vuelve?
¿Tu posición es fácil de atacar o difícil?

LENTE L2 — Secuencial:
¿En qué orden tendrían que pasar las cosas?
¿Hay algo que DEBE hacerse antes de que lo demás sea posible?
¿Qué se desbloquea al hacer el primer movimiento?
¿Hay algún movimiento que cierre opciones futuras?

LENTE L3 — Adversarial:
¿Qué hará el otro si tú haces X?
¿Qué hará si sabe que tú harás X?
¿Hay forma de que ambos ganen, o es suma cero?
¿Quién pierde más esperando?

LENTE L4 — Opcionalidad:
¿Puedes moverte sin comprometerte — explorar sin quemar puentes?
¿Cuánto vale mantener opciones abiertas vs decidir ahora?
¿Hay algún movimiento barato que da información antes del caro?

INTEGRAR: ¿Las 4 lentes convergen en el mismo movimiento o se contradicen?
ABSTRAER: ¿Este tipo de posición tiene precedentes — qué hicieron otros?
FRONTERA: ¿La inteligencia estratégica asume competición donde no la hay?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-06: POLÍTICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear poder:
¿Quién tiene poder de decisión real — no formal, real?
¿Quién puede bloquear la decisión aunque no tenga poder para decidir?
¿Quién influye sin cargo — legitimidad social, moral, emocional?
¿Qué narrativa domina — qué historia se cuenta sobre el problema?
¿Quién controla la narrativa?

CRUZAR — poder × legitimidad:
¿El poder formal y el poder real están en las mismas manos?
¿Alguien tiene poder pero no legitimidad — o legitimidad pero no poder?
¿Hay alianzas — quién apoya a quién y a cambio de qué?
¿Hay alguien cuya opinión cambiaría todo si se expresara?

LENTE L1 — Poder:
¿Quién decide realmente — siguiendo el dinero, no los organigramas?
¿Ese poder es estable o puede cambiar pronto?
¿Hay poder que nadie reconoce pero todos obedecen?

LENTE L2 — Coaliciones:
¿Quién gana si se forma la coalición A+B? ¿Quién pierde?
¿Qué mantiene unida a la coalición actual — interés común o miedo común?
¿Qué la rompería?

LENTE L3 — Narrativa:
¿Qué historia se cuenta sobre el problema?
¿Quién la escribió — y a quién favorece?
¿Hay otra historia posible con los mismos hechos?
¿Qué pasaría si la narrativa alternativa se impusiera?

LENTE L4 — Legitimidad:
¿Qué da derecho a decidir — cargo, experiencia, riesgo asumido, mérito?
¿Quién tiene más legitimidad para decidir y no la está usando?
¿La decisión será aceptada por los afectados — o solo impuesta?

INTEGRAR (∫):
¿El que tiene poder tiene legitimidad para usarlo?
¿La narrativa oculta o revela la distribución real de poder?
¿Hay una coalición posible que cambiaría todo y nadie la ha visto?

ABSTRAER:
¿Esta configuración de poder se parece a otras conocidas?
¿Qué pasó en situaciones similares — quién ganó, cómo, a qué coste?

FRONTERA:
¿Analizar políticamente un problema personal lo convierte en algo que no es?
¿Hay genuino conflicto de intereses o es una persona contra sí misma?
¿La herramienta política crea el conflicto que dice analizar?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-07: FINANCIERA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear flujos:
¿Qué entra de dinero, cuánto, con qué frecuencia?
¿Qué sale de dinero, cuánto, con qué frecuencia?
¿Cuánto queda — y es estable, crece o decrece?
¿Hay deudas — cuánto, a quién, a qué coste, cuándo vence?
¿Hay activos — qué valen, qué producen, se deprecian?
¿Cuánto cuesta tu hora — no lo que cobras, lo que te cuesta a ti vivirla?

CRUZAR — flujos × riesgo:
¿Los ingresos dependen de ti o tienen vida propia?
¿Si paras un mes, los ingresos caen a cero?
¿Los costes son fijos o variables — cuánto control tienes?
¿Tienes colchón — cuántos meses puedes aguantar sin ingresos?
¿El dinero que ganas hoy compra seguridad mañana o se consume hoy?

LENTE L1 — Valor presente:
¿Lo que vas a ganar mañana, cuánto vale hoy?
¿Estás sacrificando algo ahora que vale más que lo que ganarás después?
¿El dinero futuro es seguro o es una promesa?
¿A qué tasa descuentas — qué urgencia tiene tu presente?

LENTE L2 — Apalancamiento:
¿Estás usando dinero ajeno — crédito, deuda, inversores?
¿Ese dinero ajeno amplifica tus ganancias o tus pérdidas?
¿Cuánto puedes perder antes de que el apalancamiento te destruya?
¿El que te presta gana más que tú con tu negocio?

LENTE L3 — Opcionalidad:
¿Cuánto cuesta mantener opciones abiertas?
¿Hay asimetría — puedes ganar mucho si sale bien y perder poco si sale mal?
¿O es al revés — ganas poco y arriesgas mucho?
¿Puedes comprar tiempo antes de decidir?

LENTE L4 — Margen de seguridad:
¿Cuánto puede salir mal antes de que el sistema se rompa?
¿Estás operando al límite o con margen?
¿Un imprevisto de X€ te pondría en crisis?
¿Tu plan funciona solo si todo sale bien, o también si algo sale mal?

INTEGRAR (∫):
¿El valor presente justifica el apalancamiento actual?
¿La opcionalidad compensa el riesgo?
¿Hay margen de seguridad suficiente o estás desnudo?
¿El flujo paga la deuda, la vida, Y deja reserva — o falta algo?

ABSTRAER:
¿Este perfil financiero es sostenible a 5 años sin cambios?
¿Se parece al de otros que prosperaron o al de otros que quebraron?
¿Cuál es la variable que separa un escenario del otro?

FRONTERA:
¿Todo se puede traducir a euros?
¿Cuánto vale una cena con tus hijos en la hoja de cálculo?
¿El análisis financiero responde a la pregunta correcta o a la que sabe responder?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-08: SOCIAL

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear emociones e intenciones:
¿Qué siente esta persona — no lo que dice, lo que siente?
¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?
¿Qué necesita realmente — no lo que pide, lo que necesita?
¿Quién más está afectado y cómo se sienten?
¿Hay emociones que nadie nombra pero que gobiernan las decisiones?

CRUZAR — emociones × relaciones:
¿Lo que siente esta persona coincide con lo que muestra?
¿Los demás perciben lo que realmente pasa o solo la superficie?
¿Hay patrones — esta situación se repite, se parece a otras anteriores?
¿El conflicto es entre personas o dentro de una persona?
¿Alguien está cargando emociones que no son suyas?

LENTE L1 — Empatía:
¿Cómo se siente estar en sus zapatos — con su presión, sus miedos, sus deseos?
¿Qué le quita el sueño?
¿Qué le daría alivio inmediato vs qué le daría paz duradera?
¿Hay algo que no puede admitir ni ante sí mismo?

LENTE L2 — Dinámicas:
¿Quién cuida a quién en este sistema?
¿Alguien da más de lo que recibe — o recibe más de lo que da?
¿Hay deuda emocional acumulada — favores no devueltos, quejas no dichas?
¿Qué pasaría si alguien dijera en voz alta lo que todos piensan?

LENTE L3 — Patrones:
¿Esta persona ha estado en esta situación antes?
¿Qué hizo la última vez — funcionó?
¿Hay un patrón que se repite sin que sea consciente de ello?
¿Qué beneficio oculto tiene mantener el patrón?

LENTE L4 — Vínculos:
¿Qué relaciones nutren y cuáles drenan?
¿Hay relaciones que sobreviven por inercia, no por valor?
¿Quién falta — qué vínculo necesita que no tiene?
¿Qué vínculo está en peligro y nadie lo está cuidando?

INTEGRAR (∫):
¿La empatía revela algo que las dinámicas confirman?
¿Los patrones explican los vínculos dañados?
¿Lo que necesita emocionalmente contradice lo que persigue racionalmente?

ABSTRAER:
¿Esta dinámica es personal o le pasa a toda persona en esta posición?
¿Hay algo universal en este conflicto — algo humano, no individual?

FRONTERA:
¿Estoy psicologizando un problema que es estructural?
¿Las emociones son la causa o el síntoma?
¿Entender lo que siente resuelve algo, o solo lo nombra?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-09: LINGÜÍSTICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear el lenguaje:
¿Qué palabras usa y cuáles evita?
¿Qué metáfora gobierna su relato — guerra, viaje, construcción, supervivencia?
¿Quién es el sujeto de sus frases — "yo decido" o "hay que", "se debe"?
¿Qué nombra con precisión y qué deja vago?
¿Hay alguna palabra que repite sin notar que la repite?
¿Qué palabra falta — qué no ha nombrado que está presente?

CRUZAR — lenguaje × realidad:
¿El nombre que le da al problema define qué soluciones puede imaginar?
¿Si cambiara la palabra clave, cambiaría lo que puede pensar?
¿Dice "crecer" cuando quiere decir "sobrevivir"?
¿Dice "elegir" cuando ya eligió?
¿Su lenguaje agranda o achica el problema?

LENTE L1 — Marco:
¿Qué marco impone el lenguaje usado — problema/solución, batalla/victoria, inversión/retorno?
¿Ese marco ayuda o limita?
¿Qué alternativas de marco existen — y qué harían visible?

LENTE L2 — Actos de habla:
¿Está describiendo, pidiendo, prometiendo, amenazando o justificando?
¿Lo que dice intenta informar o convencer?
¿Hay algo performativo — algo que al decirlo, lo crea?

LENTE L3 — Metáforas:
¿Qué metáfora vive en su lenguaje sin que la elija?
¿Esa metáfora tiene lógica propia — qué implica que no dice?
¿Una metáfora diferente cambiaría lo que puede ver?

LENTE L4 — Silencios:
¿Qué no dice?
¿Lo que no dice es porque no lo piensa, no lo sabe, o no quiere verlo?
¿El silencio protege a alguien — a él mismo, a otro?

INTEGRAR (∫):
¿El marco, los actos de habla, las metáforas y los silencios cuentan la misma historia?
¿O hay contradicción entre lo que el marco dice y lo que los silencios ocultan?

ABSTRAER:
¿Este tipo de lenguaje es propio de este caso o de toda persona en esta situación?
¿El idioma mismo condiciona — se diría diferente en otro idioma?

FRONTERA:
¿Nombrar el problema lo resuelve o solo da la ilusión de control?
¿El análisis lingüístico añade comprensión o añade distancia?
¿A veces la palabra correcta es la que no se dice?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-10: CINESTÉSICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear el cuerpo:
¿Dónde se acumula tensión en este sistema — qué parte no descansa nunca?
¿Hay flujo — las cosas se mueven con ritmo o a tirones?
¿El ritmo actual es sostenible o se acelera hacia el colapso?
¿Qué parte del sistema está rígida — no se adapta, no se ajusta?
¿Hay algo que el cuerpo (la operación diaria) sabe que la mente (el plan) ignora?

CRUZAR — tensión × ritmo:
¿Las zonas de tensión coinciden con las de mayor actividad o con las de mayor bloqueo?
¿El ritmo está impuesto desde fuera o es natural del sistema?
¿Si el ritmo bajara un 20%, qué mejoraría y qué empeoraría?
¿La rigidez protege algo o solo impide movimiento?

LENTE L1 — Tensión:
¿Dónde está la contracción — qué se aprieta, se endurece, se resiste?
¿Esa tensión es productiva (como un músculo trabajando) o dañina (como un nudo)?
¿Si soltara esa tensión, qué pasaría?

LENTE L2 — Flujo:
¿Qué se mueve con facilidad y qué se atasca?
¿Los atascos son por falta de capacidad o por bloqueo?
¿Hay movimientos innecesarios — esfuerzo que no produce resultado?

LENTE L3 — Ritmo:
¿Hay ciclos naturales — momentos de esfuerzo y momentos de descanso?
¿Se respetan esos ciclos o se fuerza producción constante?
¿Cuándo fue la última pausa genuina?

LENTE L4 — Coordinación:
¿Las partes se mueven juntas o cada una por su lado?
¿Hay sincronía o hay choque entre tiempos diferentes?
¿Quién marca el ritmo y quién lo sufre?

INTEGRAR: ¿La tensión causa los atascos, los atascos rompen el ritmo, y el ritmo roto descoordina todo?
ABSTRAER: ¿Todo sistema que opera sin descanso acumula esta cascada?
FRONTERA: ¿El cuerpo tiene sabiduría que el análisis no puede capturar?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-11: ESPACIAL

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear el espacio:
¿Si dibujaras este problema, qué forma tendría?
¿Qué está cerca de qué — qué está lejos?
¿Hay centro y periferia — o todo está al mismo nivel?
¿Qué escala tiene — es un problema de mesa o de mapa?
¿Desde qué perspectiva se está mirando — y qué oculta esa perspectiva?

CRUZAR — forma × perspectiva:
¿La forma cambia si te acercas o te alejas?
¿Hay simetría — o una parte es muy diferente de la otra?
¿Las proporciones son correctas — algo ocupa mucho espacio y aporta poco?
¿Hay zonas vacías que deberían estar llenas, o llenas que deberían estar vacías?

LENTE L1 — Topografía:
¿Hay picos y valles — puntos altos y bajos?
¿Hay pendientes — zonas donde todo se desliza en una dirección?
¿Hay mesetas — zonas donde no importa lo que hagas, nada cambia?

LENTE L2 — Fronteras:
¿Dónde están los bordes — qué está dentro y qué fuera?
¿Las fronteras son permeables o rígidas?
¿Algo que debería estar dentro está fuera, o viceversa?

LENTE L3 — Perspectiva:
¿Cómo se ve desde arriba — el mapa completo?
¿Cómo se ve desde dentro — la experiencia vivida?
¿Cómo se ve desde fuera — un observador neutral?
¿Las tres perspectivas cuentan la misma historia?

LENTE L4 — Proporción:
¿El tamaño de cada parte corresponde a su importancia?
¿Algo pequeño tiene impacto desproporcionado?
¿Algo grande no produce casi nada?

INTEGRAR: ¿La topografía explica las fronteras, y la perspectiva revela proporciones ocultas?
ABSTRAER: ¿Este mapa se parece a otros mapas conocidos?
FRONTERA: ¿Hay procesos que no tienen forma — que el espacio no puede capturar?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-12: NARRATIVA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear la historia:
¿Quién es el protagonista de esta historia — y quién cree él que es?
¿Cuál es el conflicto central — qué quiere vs qué le impide?
¿En qué momento de la historia estamos — inicio, nudo, clímax, desenlace?
¿Cuál es el acto anterior que llevó hasta aquí?
¿Hay un mentor, un antagonista, un aliado — quién cumple cada rol?

CRUZAR — historia × identidad:
¿La historia que se cuenta a sí mismo coincide con lo que hacen los hechos?
¿Se ve como héroe, víctima, mártir, constructor?
¿Ese rol elegido lo libera o lo atrapa?
¿Hay otra historia posible con los mismos hechos — donde el protagonista tiene otro rol?

LENTE L1 — Arco:
¿Cuál es la transformación pendiente — qué tiene que cambiar el protagonista?
¿Lo sabe, lo intuye, o lo niega?
¿Qué precio tiene esa transformación — qué debe dejar atrás?

LENTE L2 — Estructura:
¿Esta historia tiene actos claros o es un ciclo sin avance?
¿Hay un punto de no retorno — una decisión que cambiará todo?
¿Ya pasó y no se dio cuenta?

LENTE L3 — Personajes:
¿Cada persona en el caso cumple un rol narrativo — cuál?
¿Alguien está atrapado en un rol que no eligió?
¿Quién tiene la llave de la resolución y no la usa?

LENTE L4 — Significado:
¿Qué sentido tiene esta historia para quien la vive?
¿Es una historia de superación, de pérdida, de aprendizaje?
¿El sentido que le da lo ayuda o lo limita?

INTEGRAR: ¿El arco, la estructura, los personajes y el significado apuntan al mismo desenlace?
ABSTRAER: ¿Esta historia es un arquetipo conocido — cuál?
FRONTERA: ¿La vida necesita historia, o la narrativa impone orden donde hay caos?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-13: PROSPECTIVA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear futuros:
¿Cuáles son las tendencias en curso — qué se mueve y hacia dónde?
¿Cuáles son aceleradas (crecen) y cuáles deceleradas (se frenan)?
¿Hay señales débiles — cosas pequeñas que podrían ser el inicio de algo grande?
¿Qué asume todo el mundo que seguirá igual — y qué tan seguro es eso?

CRUZAR — tendencias × supuestos:
¿Qué pasa si dos tendencias que ahora van separadas se cruzan?
¿Hay supuestos que si caen, cambian todo el panorama?
¿Las señales débiles apuntan en la misma dirección o en direcciones opuestas?
¿Algo que parece estable tiene fecha de caducidad?

LENTE L1 — Escenarios:
¿Cuál es el mejor caso realista — no fantasía, realista?
¿Cuál es el peor caso realista?
¿Cuál es el caso más probable si nada cambia?
¿Hay un escenario que nadie considera pero que es posible?

LENTE L2 — Señales:
¿Qué señal aparecería primero si vamos hacia el mejor caso?
¿Y hacia el peor?
¿Esas señales ya están apareciendo?
¿Alguien las está monitorizando?

LENTE L3 — Bifurcaciones:
¿Hay un punto donde el camino se divide — una decisión que lleva a futuros muy diferentes?
¿Cuándo es ese punto — ya pasó, está aquí, o viene?
¿Es reversible — si eliges un camino, puedes volver?

LENTE L4 — Comodines:
¿Qué podría pasar que no está en ningún modelo?
¿Un evento improbable pero de alto impacto — cuál sería?
¿Estás preparado para lo inesperado o solo para lo esperado?

INTEGRAR: ¿Los escenarios, señales, bifurcaciones y comodines convergen en algún patrón?
ABSTRAER: ¿Este tipo de encrucijada tiene precedentes — qué pasó?
FRONTERA: ¿El futuro es predecible o el acto de predecir cambia lo que pasará?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-14: DIVERGENTE

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — abrir posibilidades:
¿Cuántas opciones ve esta persona — y cuántas más existen?
¿Qué opciones descartó sin examinar — y por qué?
¿Qué pasaría si la restricción más obvia no existiera?
¿Qué haría alguien completamente diferente en esta situación?
¿Qué haría si tuviera el doble de recursos? ¿Y la mitad?

CRUZAR — opciones × restricciones:
¿Las restricciones son reales o asumidas?
¿Hay opciones que parecen locas pero son viables si las miras bien?
¿Qué pasa si combinas dos opciones que parecen incompatibles?
¿Hay una opción que nadie ha mencionado porque parece obvia-pero-no?

LENTE L1 — Volumen:
¿Puedes generar 10 opciones más en 2 minutos — sin filtrar?
¿Y 10 más que sean lo opuesto de las primeras 10?
¿Qué tienen en común las que te gustan — y qué te dice eso?

LENTE L2 — Combinación:
¿Qué pasa si mezclas la opción A con la C?
¿Hay una solución de otro dominio que podría funcionar aquí?
¿Qué haría un niño? ¿Un artista? ¿Un alien?

LENTE L3 — Inversión:
¿Y si haces exactamente lo opuesto de lo que "deberías"?
¿Y si el problema es la solución y la solución es el problema?
¿Qué pasa si en lugar de resolver, amplías?

LENTE L4 — Restricción creativa:
¿Si SOLO pudieras hacer UNA cosa, cuál sería?
¿Si tuvieras que resolver esto en 24h, qué harías?
¿Si no pudieras usar dinero, qué usarías?

INTEGRAR: ¿De todas las opciones generadas, cuáles aparecen desde múltiples lentes?
ABSTRAER: ¿Las mejores opciones comparten alguna estructura común?
FRONTERA: ¿Generar opciones es avanzar o es evitar elegir?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-15: ESTÉTICA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear coherencia:
¿Algo en este caso "suena raro" — algo no encaja aunque no sepas qué?
¿Hay elegancia — partes que funcionan con simplicidad y gracia?
¿Hay disonancia — partes que chocan entre sí?
¿El problema tiene simetría o está desequilibrado?
¿La forma del problema y la forma de la solución propuesta son coherentes?

CRUZAR — forma × contenido:
¿Lo que dice y cómo lo dice son coherentes?
¿La solución que propone tiene la misma forma que el problema — repite el patrón?
¿Hay algo bello en el problema — alguna estructura elegante, aunque sea dolorosa?
¿La complejidad es necesaria o es ruido?

LENTE L1 — Armonía:
¿Las partes se complementan o se contradicen?
¿Hay proporción — cada parte tiene el peso justo?
¿Algo sobra? ¿Algo falta?

LENTE L2 — Tensión:
¿Dónde está la tensión productiva — la que genera energía?
¿Dónde está la tensión destructiva — la que gasta sin producir?
¿La tensión se resuelve o es permanente?

LENTE L3 — Simplicidad:
¿Cuál es la versión más simple de este problema que conserva lo esencial?
¿Qué se puede quitar sin perder nada?
¿Lo que queda después de quitar todo lo superfluo — qué es?

LENTE L4 — Resonancia:
¿Este caso produce una reacción inmediata — algo que se siente antes de pensarse?
¿Esa reacción es informativa — dice algo que el análisis no puede decir?
¿Hay verdad en la primera impresión que el análisis posterior ignora?

INTEGRAR: ¿La armonía, la tensión, la simplicidad y la resonancia apuntan al mismo sitio?
ABSTRAER: ¿Los problemas bellos tienen mejores soluciones que los feos?
FRONTERA: ¿La estética es guía de verdad o sesgo hacia lo bonito?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-16: CONSTRUCTIVA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — mapear restricciones:
¿Qué tiene que funcionar al final — cuál es el criterio de éxito?
¿Con qué materiales cuentas — dinero, tiempo, personas, herramientas?
¿Qué restricciones son inamovibles y cuáles son flexibles?
¿Hay algo que ya funciona y se puede reutilizar?
¿Qué ha fallado antes — qué se intentó y no sirvió?

CRUZAR — objetivo × restricciones:
¿El objetivo es alcanzable con los materiales disponibles?
¿Si no alcanza, qué falta — más de qué?
¿Hay formas de reducir el objetivo sin perder lo esencial?
¿Las restricciones reales son menos de las que cree?

LENTE L1 — Prototipo:
¿Cuál es la versión más pequeña que se puede construir y probar?
¿Qué aprenderías construyendo eso?
¿Cuánto cuesta y cuánto tiempo lleva?

LENTE L2 — Secuencia:
¿Qué se construye primero — qué es el cimiento?
¿Qué depende de qué — qué no puedes hacer hasta tener X?
¿Hay un camino crítico — una secuencia que determina el tiempo total?

LENTE L3 — Fallo:
¿Qué se va a romper primero?
¿Puedes diseñar para que falle de forma segura?
¿Dónde necesitas margen y dónde puedes ajustar?

LENTE L4 — Iteración:
¿Esto se construye de una vez o por versiones?
¿Qué aprende cada versión que la anterior no sabía?
¿Cuántas iteraciones son necesarias para que funcione bien?

INTEGRAR: ¿El prototipo, la secuencia, los modos de fallo y la iteración son coherentes?
ABSTRAER: ¿Hay un principio de ingeniería que gobierna este problema?
FRONTERA: ¿Construir mejor lo existente es la respuesta, o hay que construir otra cosa?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-17: EXISTENCIAL

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — lo que está en juego:
¿Qué está en juego aquí realmente — no lo que se dice, lo que está en juego de verdad?
¿Qué se perdería si no haces nada?
¿Qué se perdería si haces lo que "deberías"?
¿Cuál de las dos pérdidas pesa más — y quién decide eso?

CRUZAR — valores × vida:
Lo que dices que valoras, ¿coincide con dónde pones tu tiempo?
¿Hay algo que dices que no importa pero que te quita el sueño?
¿Hay algo que dices que importa mucho pero a lo que dedicas cero?
¿La distancia entre lo declarado y lo vivido — es grande o pequeña?

LENTE L1 — Propósito:
¿Para qué haces lo que haces — la razón profunda, no la práctica?
¿Si ya tuvieras suficiente dinero, seguirías haciendo esto?
¿Lo haces porque quieres o porque sientes que debes?

LENTE L2 — Finitud:
¿Cuánto tiempo te queda para lo que importa?
¿Ese tiempo es recuperable si lo pierdes ahora?
¿Lo que ganas compensa lo que pierdes — sabiendo que lo perdido no vuelve?

LENTE L3 — Libertad:
¿Estás eligiendo o siguiendo inercia?
¿Cuándo fue la última vez que elegiste activamente?
¿Puedes decir "no" sin que pase nada malo?
Si puedes decir "no" y no lo haces — ¿por qué?

LENTE L4 — Responsabilidad:
¿Ante quién eres responsable — y en qué orden?
¿Quién viene primero? ¿Quién debería venir primero?
¿Coinciden las dos respuestas?

INTEGRAR: ¿El propósito justifica el sacrificio sabiendo que el tiempo no vuelve?
ABSTRAER: ¿Esto le pasa a todo humano en tu posición, o es único?
FRONTERA: ¿Todas estas preguntas son otra forma de no decidir?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

### PROMPT F1-18: CONTEMPLATIVA

```
Sobre los 3 casos que aparecen al final de este mensaje, responde estas preguntas:

EXTRAER — lo que es:
¿Qué hay aquí, ahora, tal como es — sin interpretación?
¿Puedes describir la situación sin juzgarla como buena o mala?
¿Qué se siente al simplemente estar con esto — sin resolver?
¿Hay prisa real o la urgencia es inventada?

CRUZAR — observación × impulso:
¿El impulso de actuar viene de la situación o del miedo a no actuar?
¿Qué pasaría si esperas — no por indecisión, sino por observación?
¿Hay sabiduría en la pausa que la acción destruiría?
¿El problema necesita resolverse o necesita ser sostenido?

LENTE L1 — Presencia:
¿Estás aquí o estás en el futuro — preocupado por lo que vendrá?
¿Puedes volver a ahora — a lo que hay, no a lo que temes?
¿Qué sabes cuando paras de pensar y simplemente miras?

LENTE L2 — Paradoja:
¿Las dos opciones que parecen opuestas pueden ser verdad a la vez?
¿Puedes sostener la contradicción sin necesitar resolverla?
¿Qué emerge si no eliges — si dejas que la tensión se sostenga?

LENTE L3 — Soltar:
¿Qué estás agarrando que necesitas soltar?
¿Qué pasaría si dejas de intentar controlar esto?
¿El control es real o es ilusión de control?

LENTE L4 — Vacío:
¿Hay espacio en este sistema — lugar para que algo nuevo emerja?
¿O está todo tan lleno que nada nuevo puede entrar?
¿Qué necesita vaciarse para que algo mejor ocupe su lugar?

INTEGRAR: ¿La presencia, la paradoja, el soltar y el vacío apuntan al mismo silencio?
ABSTRAER: ¿Toda crisis tiene un momento donde parar es más valiente que actuar?
FRONTERA: ¿La contemplación es sabiduría o es privilegio de quien puede permitirse esperar?

═══════════════════════════════════════════════════════
DESPUÉS DE LOS 3 CASOS:
LOOP TEST, PATRÓN CROSS-CASE, SATURACIÓN, FIRMA

═══════════════════════════════════════════════════════
FORMATO: Para cada caso: prosa por bloques + resumen 200 palabras + JSON (schema sección 3). Después de los 3 casos: JSON post-3-casos (loop_test + patron_cross_case + saturacion).
[pegar los 3 casos]
```

---

## 5. FASE 2 — DIFERENCIALES (3 chats)

Un chat por caso. Ejecutar DESPUÉS de completar Fase 1.

### Prompt Fase 2

```
A continuación tienes los RESÚMENES y FIRMAS de 18 inteligencias 
aplicadas al mismo caso.

Diferencial (A − B) = lo que A ve que B NO PUEDE ver por construcción.
No es lo que A vio y B no mencionó — es lo que B no puede ver por la 
naturaleza de sus objetos y operaciones.

¿Qué ve cada inteligencia que ninguna otra puede ver?
¿Qué pares son genuinamente complementarios — ven cosas diferentes por construcción?
¿Qué pares son redundantes — ven casi lo mismo con distinto vocabulario?
¿Hay alguna inteligencia cuya firma no está cubierta por ninguna combinación de las demás?

De los 153 pares posibles, ¿cuáles son los TOP 10 con mayor diferencial?
Para cada uno: ¿qué ve A que B no puede, qué ve B que A no puede, 
y qué produciría fusionarlos?

¿Cuáles son los pares más redundantes?

¿Las 8 categorías agrupan inteligencias genuinamente similares, 
o hay inteligencias mal clasificadas por su comportamiento real?

═══════════════════════════════════════════════════════
[PEGAR AQUÍ LOS 18 BLOQUES JSON + FIRMAS DE ESTE CASO]
(Los JSONs están en el output de Fase 1 — campo "hallazgos", 
"objetos_detectados", "firma" y "punto_ciego_declarado")
```

---

## 6. FASE 3 — COMBINACIONES SELECTIVAS

Los pares se eligen de los TOP 10 de Fase 2.

### 3A. Fusión — ∫(INT-A | INT-B)

```
Sobre el caso de abajo, responde las preguntas de INT-[A] y de INT-[B]
(consulta META_RED_INTELIGENCIAS_CR0.md).

Después de ejecutar ambas:

¿Qué emerge al analizar esto con dos inteligencias diferentes a la vez?
¿Dónde coinciden — y esa coincidencia qué significa?
¿Dónde se contradicen — y esa contradicción qué revela?
¿Hay algo que SOLO aparece al cruzar las dos que ninguna ve sola?

Test P01 — Conmutatividad:
¿Cambia el resultado si primero miro con INT-[A] y luego INT-[B], o al revés?

═══════════════════════════════════════════════════════
[pegar caso]
```

### 3B. Composición — INT-A → INT-B

```
PASO 1: Responde las preguntas de INT-[A] sobre el caso de abajo.
PASO 2: Toma tu output de INT-[A]. Responde las preguntas de INT-[B] 
sobre ESE OUTPUT — no sobre el caso original.

¿Qué ve INT-[B] al mirar lo que INT-[A] produjo?
¿La explicación de A tiene una forma que B puede revelar?
¿El diagnóstico de A cambia cuando B lo examina?

Test P02 — No conmutatividad:
Ahora invierte: INT-[B] sobre el caso, luego INT-[A] sobre ese output.
¿Produce lo mismo? ¿Qué se ve diferente? ¿Cuál revela más?

═══════════════════════════════════════════════════════
[pegar caso]
```

### 3C. Distributividad — P04/P05

```
EJECUCIÓN 1 — JUNTO: A→(B|C)
  Responde INT-[A] sobre el caso.
  Luego responde INT-[B] e INT-[C] JUNTAS sobre el output de A.

EJECUCIÓN 2 — SEPARADO: (A→B) | (A→C)
  Responde INT-[A] sobre el caso.
  Responde INT-[B] sobre el output de A (sin ver C).
  Responde INT-[C] sobre el output de A (sin ver B).

¿Producen el mismo resultado?
Si no → ¿qué se pierde al separar?

Test P05 — NO distributiva derecha:
¿(B|C)→A = (B→A) | (C→A)?
¿El cruce tiene valor propio que se pierde al separar?

═══════════════════════════════════════════════════════
[pegar caso]
```

---

## 7. FASE 4 — PROPIEDADES ADICIONALES

### 4A. Asociatividad (P03)

```
¿Importa cómo agrupo los pasos o solo importa la secuencia?

RUTA 1: (A→B)→C
RUTA 2: A→(B→C)

¿El output final es equivalente?
¿Puedo reorganizar el trabajo sin cambiar el resultado?

═══════════════════════════════════════════════════════
[pegar caso]
```

### 4B. Clausura (P08)

```
¿El output de una inteligencia puede ser input de OTRA completamente diferente?

Responde las preguntas de INT-[X] sobre el OUTPUT de INT-[A] (no sobre el caso).

¿Funciona? ¿Cada respuesta abre nuevas preguntas posibles?
¿Qué inteligencia falta en la mesa?

═══════════════════════════════════════════════════════
[pegar output de INT-A sobre un caso]
```

### 4C. Saturación profunda (P07)

```
Toma el output del LOOP TEST de INT-[A] (la segunda pasada, de Fase 1).
Aplica las preguntas de INT-[A] UNA TERCERA VEZ sobre ese output.

¿Sigue aportando valor?
¿Estamos girando en círculos o avanzando en espiral?
¿La tercera pasada justifica el coste?

═══════════════════════════════════════════════════════
[pegar output de loop test]
```

---

## 8. PROTOCOLO DE RECOGIDA

### Después de cada chat de Fase 1:

Guardar DOS archivos por chat:

**1. `RESULTADOS_FASE1.md`** (acumulador narrativo):

```markdown
## INT-XX: [NOMBRE]

### Caso 1: Clínica Dental
**Resumen:** [~200 palabras]
**Firma:** [1-2 frases]

### Caso 2: Startup SaaS
**Resumen:** [~200 palabras]
**Firma:** [1-2 frases]

### Caso 3: Cambio de carrera
**Resumen:** [~200 palabras]
**Firma:** [1-2 frases]

### Loop test (P06)
[resultado]

### Patrón cross-case
[resultado]

### Saturación (P07)
[resultado]
```

**2. `RESULTADOS_FASE1_JSON.md`** (acumulador mecánico):

Copiar los 3 bloques JSON por caso + el JSON post-3-casos.
Agrupar por inteligencia. Este archivo es el INPUT directo de Fase 2.

### Después de Fase 2:
Guardar completo. Los TOP 10 pares determinan Fase 3.

### Después de Fase 3 y 4:
Operación + resultado + propiedad + confirmada/refutada.

---

## 9. ORDEN DE EJECUCIÓN

```
SEMANA 1: Fase 1 — 18 chats
  Día 1: F1-01 a F1-04
  Día 2: F1-05 a F1-07
  Día 3: F1-08 a F1-11
  Día 4: F1-12 a F1-15
  Día 5: F1-16 a F1-18

SEMANA 2: Fase 2 — 3 chats + decisión Fase 3

SEMANA 2-3: Fase 3 — 10-15 chats selectivos

SEMANA 3: Fase 4 — 3-5 chats
```

---

## 10. OUTPUT FINAL

| Dato | Para el compilador |
|------|-------------------|
| 18 × 3 análisis | Catálogo de qué ve cada inteligencia |
| 18 loop tests | Mapa de no-idempotencia |
| 18 saturaciones | Profundidad útil por inteligencia |
| 3 matrices 18×18 | Mapa de complementariedad |
| ~10-15 fusiones | Efectos de combinar |
| ~10-15 composiciones | Efectos de secuenciar |
| Tests P01-P11 | Propiedades confirmadas/refutadas |

---

**FIN PROTOCOLO DE CARTOGRAFÍA META-RED v1 — CR0**



============================================================
## Motor/Meta-Red de preguntas inteligencias/TABLA_PERIODICA_INTELIGENCIA_CR0.md
============================================================

# TABLA PERIÓDICA DE LA INTELIGENCIA — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-07
**Origen:** Sesión Opus — derivación desde ALGEBRA_CALCULO_SEMANTICO_CR0.md
**Dependencias:** ALGEBRA_CALCULO_SEMANTICO_CR0.md, sesión de validación empírica

---

## 1. DEFINICIÓN

Cada tipo de inteligencia es un **álgebra**: un sistema formal con objetos propios, operaciones propias y tipos de pensamiento que produce. Cada álgebra tiene un punto ciego estructural que otra álgebra ve sin esfuerzo.

El Motor v3.3 ejecuta UNA álgebra (Estructural/IAS) con 4 isomorfismos de 18 álgebras posibles. Esta tabla mapea el espacio completo.

```
ÁLGEBRA DE INTELIGENCIA:
  objetos:      qué tipo de cosas percibe / manipula
  operaciones:  qué puede hacer con ellas
  pensamiento:  qué tipos de razonamiento produce
  punto_ciego:  qué no puede ver por construcción
  firma:        la operación que la distingue de todas las demás
```

---

## 2. CRITERIO DE DISTINCIÓN

Dos inteligencias son genuinamente distintas si su DIFERENCIAL es grande:

```
A - B = grande → A ve cosas que B no puede ver por construcción → genuinamente distintas
A - B = pequeño → A y B ven casi lo mismo → una es variante de la otra
```

Las 18 inteligencias de esta tabla sobrevivieron al test del diferencial. Cada una tiene objetos que ninguna otra puede manipular.

---

## 3. LAS 18 ÁLGEBRAS

### CATEGORÍA I: FORMALES — operan sobre estructuras abstractas

#### 1. LÓGICO-MATEMÁTICA
```
Objetos:      estructuras, relaciones, pruebas, axiomas
Operaciones:  demostración, abstracción, generalización, contraejemplo
Pensamiento:  ¿es verdadero? ¿es necesario? ¿es suficiente? ¿existe? ¿es único?
Punto ciego:  lo ambiguo, lo parcial, lo no-axiomatizable
Firma:        DEMOSTRACIÓN — derivar verdad desde primeros principios
Ejemplo:      "Si margen < costes variables, toda expansión acelera pérdidas" (deducción)
```

#### 2. COMPUTACIONAL
```
Objetos:      algoritmos, estados, complejidad, datos
Operaciones:  descomposición, recursión, optimización, simulación
Pensamiento:  ¿es computable? ¿en cuánto tiempo? ¿se puede descomponer? ¿escala?
Punto ciego:  lo no-computable, la intuición, el juicio cualitativo
Firma:        OPTIMIZACIÓN — encontrar la mejor solución dentro de restricciones
Ejemplo:      "Ocupación de sillones es problema de scheduling con restricciones de RH"
```

### CATEGORÍA II: SISTÉMICAS — operan sobre relaciones entre partes

#### 3. ESTRUCTURAL (IAS)
```
Objetos:      coordenadas sintácticas, formas, niveles, huecos
Operaciones:  isomorfismo, composición, integración, diferencial
Pensamiento:  ¿qué forma tiene? ¿por qué esta forma? ¿qué se repite? ¿qué no ve?
Punto ciego:  no genera soluciones — solo diagnóstico
Firma:        ISOMORFISMO — proyectar forma sobre datos para hacer visible lo invisible
Ejemplo:      "SACRIFICAR ir=0.92 id=0 — opera con potencia máxima porque no se nombra"
```

#### 4. ECOLÓGICA
```
Objetos:      ecosistemas, ciclos, nichos, resiliencia, flujos
Operaciones:  observar interdependencia, rastrear flujos, detectar fragilidad
Pensamiento:  ¿quién depende de quién? ¿qué pasa si quitas un nodo? ¿es resiliente?
Punto ciego:  no ve al individuo — solo al sistema completo
Firma:        INTERDEPENDENCIA — nada existe aislado, todo afecta a todo
Ejemplo:      "La clínica es un ecosistema: quitar al dentista 1 día colapsa 3 flujos"
```

### CATEGORÍA III: ESTRATÉGICAS — operan sobre posición y movimiento

#### 5. ESTRATÉGICA
```
Objetos:      posición, recursos, movimientos, ventanas temporales, opciones
Operaciones:  evaluación posicional, anticipación, secuenciación, compromiso
Pensamiento:  ¿dónde estoy? ¿qué puede pasar si...? ¿en qué orden? ¿es reversible?
Punto ciego:  asume competición — no modela cooperación ni conflicto interno
Firma:        ANTICIPACIÓN — pensar dos movimientos adelante
Ejemplo:      "Abrir sábados antes de optimizar utilización = quemar recurso escaso sin dato"
```

#### 6. POLÍTICA
```
Objetos:      poder, alianzas, legitimidad, narrativa, coaliciones
Operaciones:  negociación, enmarcado, formación de coaliciones, lectura de poder
Pensamiento:  ¿quién tiene poder? ¿quién apoya a quién? ¿cómo se enmarca? ¿qué legitima?
Punto ciego:  confunde poder con verdad — lo que tiene apoyo no es necesariamente correcto
Firma:        NEGOCIACIÓN — redistribuir poder mediante acuerdo
Ejemplo:      "El banco tiene poder 0.6 sobre la decisión porque ofrece crédito = legitimidad"
```

#### 7. FINANCIERA
```
Objetos:      flujos, posiciones, riesgo, apalancamiento, opcionalidad
Operaciones:  descuento temporal, cobertura, arbitraje, composición de retornos
Pensamiento:  ¿cuánto vale hoy? ¿cuál es la asimetría? ¿puedo salir? ¿hay margen de seguridad?
Punto ciego:  lo que no tiene precio no existe
Firma:        DESCUENTO TEMPORAL — todo valor se traduce a presente
Ejemplo:      "7K€/mes × 12 = 84K€/año. Si trabaja 2.500h/año = 33.6€/h. ¿A qué hora deja de valer?"
```

### CATEGORÍA IV: SOCIALES — operan sobre personas

#### 8. SOCIAL (interpersonal + intrapersonal)
```
Objetos:      emociones, intenciones, dinámicas, patrones reactivos, vínculos
Operaciones:  lectura empática, regulación emocional, calibración social
Pensamiento:  ¿qué siente? ¿qué necesita? ¿qué patrón repite? ¿qué trigger activa?
Punto ciego:  sobrepsicologiza — puede ver conflicto emocional donde hay problema estructural
Firma:        EMPATÍA — leer el estado interno del otro (o propio) sin que lo verbalice
Ejemplo:      "La mujer no dice 'estoy triste' — dice 'no paras'. La emoción está en la queja operativa"
```

#### 9. LINGÜÍSTICA
```
Objetos:      palabras, marcos, narrativas, metáforas, actos de habla
Operaciones:  nombrar, reencuadrar, persuadir, construir significado con lenguaje
Pensamiento:  ¿cómo se nombra? ¿qué marco impone? ¿qué palabra falta? ¿qué metáfora gobierna?
Punto ciego:  confunde nombrar con resolver — poner nombre no cambia la estructura
Firma:        REENCUADRE — cambiar el marco lingüístico cambia lo que es visible
Ejemplo:      "'Crecer' enmarca expansión como progreso. 'Intensificar sacrificio' es el mismo acto, distinto marco"
```

### CATEGORÍA V: CORPORALES — operan sobre el cuerpo y el espacio

#### 10. CINESTÉSICA
```
Objetos:      movimiento, tensión, ritmo, coordinación, flujo corporal
Operaciones:  sentir, ajustar, sincronizar, fluir
Pensamiento:  ¿dónde hay tensión? ¿qué se contrae? ¿hay flujo? ¿el ritmo es sostenible?
Punto ciego:  no verbaliza — sabe pero no puede explicar qué sabe
Firma:        SENTIR TENSIÓN — el cuerpo detecta lo que la mente racionaliza
Ejemplo:      "El dentista dice 'estoy bien' pero su cuerpo acumula 2.500h/año en postura fija"
```

#### 11. ESPACIAL
```
Objetos:      formas, distancias, perspectivas, mapas, proporciones
Operaciones:  visualizar, rotar, proyectar, mapear
Pensamiento:  ¿qué forma tiene? ¿cómo se ve desde otro ángulo? ¿qué proporción es?
Punto ciego:  lo que no tiene extensión no existe — no ve procesos, solo configuraciones
Firma:        CAMBIO DE PERSPECTIVA — rotar el objeto para ver la cara oculta
Ejemplo:      "Mapa de la clínica: 3 sillones, 2 personas, 1 cuello de botella. La geometría dice dónde"
```

### CATEGORÍA VI: TEMPORALES — operan sobre el tiempo

#### 12. NARRATIVA
```
Objetos:      arco, personaje, transformación, secuencia, significado temporal
Operaciones:  contar, situar en historia, dar sentido al pasado, proyectar arco futuro
Pensamiento:  ¿quién es el protagonista? ¿en qué acto estamos? ¿qué transformación falta?
Punto ciego:  fuerza protagonista y arco donde puede no haberlos
Firma:        DAR SENTIDO — convertir hechos en historia con dirección
Ejemplo:      "El dentista está en el Acto 2: la crisis. El acto 3 (transformación) requiere elegir qué sacrificar"
```

#### 13. PROSPECTIVA
```
Objetos:      tendencias, señales débiles, escenarios, distribuciones de probabilidad
Operaciones:  extrapolar, simular, ponderar futuros, detectar señales tempranas
Pensamiento:  ¿hacia dónde converge? ¿qué señales débiles hay? ¿cuáles son los escenarios?
Punto ciego:  el cisne negro — lo que no tiene precedente no aparece en el modelo
Firma:        SIMULAR FUTUROS — explorar qué pasa si X, Y o Z
Ejemplo:      "Escenario A: crece y colapsa en 18 meses. B: optimiza y estabiliza. C: reduce y recupera vida"
```

### CATEGORÍA VII: CREATIVAS — operan generando lo que no existe

#### 14. DIVERGENTE
```
Objetos:      posibilidades, conexiones remotas, combinaciones inusuales
Operaciones:  generar opciones, romper marcos, combinar lo no combinado
Pensamiento:  ¿qué más podría ser? ¿qué pasa si combino X con Y? ¿cuántas opciones hay?
Punto ciego:  todo es posible, nada es evaluable — genera sin filtrar
Firma:        GENERACIÓN — producir opciones que no existían antes
Ejemplo:      "¿Y si el dentista no contrata ni abre sábados sino que sube precios 30% y pierde pacientes?"
```

#### 15. ESTÉTICA
```
Objetos:      armonía, tensión, elegancia, proporción, coherencia formal
Operaciones:  sentir coherencia, detectar disonancia, juzgar calidad de forma
Pensamiento:  ¿es elegante? ¿hay disonancia? ¿la forma es coherente con el contenido?
Punto ciego:  lo feo puede ser verdadero, lo bello puede ser falso
Firma:        JUICIO DE COHERENCIA — detectar que algo "no encaja" sin saber por qué
Ejemplo:      "La estructura del caso es disonante: dice 'quiero crecer' pero toda la energía va a sobrevivir"
```

#### 16. CONSTRUCTIVA (ingeniería)
```
Objetos:      restricciones, materiales, soluciones, prototipos, iteraciones
Operaciones:  construir dentro de límites, hacer funcionar, iterar, testear
Pensamiento:  ¿funciona? ¿qué restricción gobierna? ¿cómo se construye? ¿qué falla primero?
Punto ciego:  optimiza lo existente — no cuestiona si debería existir
Firma:        CONSTRUIR — convertir diseño en realidad funcional
Ejemplo:      "Restricción: 2 dentistas, 3 sillones, 45K ingresos. Solución: maximizar ratio sillón/hora antes de añadir"
```

### CATEGORÍA VIII: EXISTENCIALES — operan sobre significado

#### 17. EXISTENCIAL
```
Objetos:      propósito, libertad, responsabilidad, finitud, valores
Operaciones:  confrontar lo irreducible, jerarquizar valores, elegir con consciencia
Pensamiento:  ¿para qué? ¿merece la pena? ¿qué estoy sacrificando? ¿quién quiero ser?
Punto ciego:  puede paralizar por exceso de profundidad
Firma:        CONFRONTAR — preguntar "¿para qué?" hasta llegar al fondo
Ejemplo:      "¿7K€/mes con tus hijos viéndote ES el éxito, y 15K€/mes sin verlos es el fracaso?"
```

#### 18. CONTEMPLATIVA
```
Objetos:      presencia, vacío, observación, paradoja, no-acción
Operaciones:  soltar, observar sin juzgar, habitar la paradoja, esperar
Pensamiento:  ¿y si no hay problema? ¿qué pasa si no hago nada? ¿puedo sostener la incertidumbre?
Punto ciego:  puede desconectar de la acción — observar sin actuar
Firma:        OBSERVAR SIN JUZGAR — ver lo que es, sin necesidad de cambiarlo
Ejemplo:      "Antes de decidir sillón, sábados o dentista: sentarte con la pregunta sin responderla"
```

---

## 4. DIMENSIONES DE ORGANIZACIÓN

Las 18 álgebras se organizan en dos ejes:

### Eje X — DOMINIO (sobre qué opera)

| Dominio | Álgebras | Qué manipulan |
|---------|----------|--------------|
| FORMAL | Lógico-matemática, Computacional | Estructuras abstractas, verdad, eficiencia |
| SISTÉMICO | Estructural, Ecológica | Relaciones entre partes, formas, flujos |
| HUMANO | Estratégica, Política, Financiera | Posición, poder, valor entre personas |
| SOCIAL | Social, Lingüística | Emociones, intenciones, marcos de lenguaje |
| FÍSICO | Cinestésica, Espacial | Cuerpo, movimiento, espacio, forma visual |
| TEMPORAL | Narrativa, Prospectiva | Secuencia, arco, futuros, tendencias |
| GENERATIVO | Divergente, Estética, Constructiva | Posibilidades, coherencia, soluciones |
| EXISTENCIAL | Existencial, Contemplativa | Propósito, presencia, significado último |

### Eje Y — MODO (cómo opera)

| Modo | Descripción | Álgebras que lo usan |
|------|-------------|---------------------|
| ANALIZAR | Descomponer, demostrar, medir | Lógico-mat, Computacional, Financiera |
| PERCIBIR | Ver patrones, detectar forma | Estructural, Ecológica, Estética |
| MOVER | Actuar, posicionar, construir | Estratégica, Constructiva, Cinestésica |
| SENTIR | Empatizar, intuir, habitar | Social, Cinestésica, Contemplativa |
| GENERAR | Crear, imaginar, proyectar | Divergente, Narrativa, Prospectiva |
| ENMARCAR | Nombrar, negociar, dar sentido | Lingüística, Política, Existencial |

---

## 5. TIPOS DE PENSAMIENTO

### 5.1 Pensamiento INTERNO (dentro de una álgebra)

Las 10 familias derivadas del álgebra semántico aplican a CADA una de las 18 álgebras:

| # | Familia | Pensamiento | Expresión |
|---|---------|-------------|-----------|
| 1 | iso(S) | Percepción | ¿Qué forma tiene? |
| 2 | B(iso(S)) | Causalidad | ¿Por qué esta forma? |
| 3 | iso²(S) | Abstracción | ¿Qué se repite? |
| 4 | ∫(isos) | Síntesis | ¿Qué conecta todo? |
| 5 | A−B | Discernimiento | ¿Qué es único de cada mirada? |
| 6 | crítico(X) | Metacognición | ¿Qué no puedo ver? |
| 7 | iso(M) | Consciencia epistemológica | ¿Qué forma tiene mi pensamiento? |
| 8 | B(iso(M)) | Auto-diagnóstico | ¿Por qué pienso así? |
| 9 | ∫(M₁\|M₂) | Convergencia | ¿Qué esencia comparten mis explicaciones? |
| 10 | A→B→C→A' | Dialéctica | ¿Qué veo después de que otros transformaron mi mirada? |

### 5.2 Pensamiento LATERAL (cruza el perímetro de una álgebra)

| # | Tipo | Pensamiento | Operación | Qué rompe |
|---|------|-------------|-----------|-----------|
| 11 | T_A ≅ T_B | Analogía | ≅ (isomorfismo entre dominios) | Perímetro del dominio |
| 12 | Δ(S, x) | Contrafactual | Δ (perturbación) | Fijeza de los datos |
| 13 | T → S' | Abducción | ← (inversión de dirección) | Dirección del razonamiento |
| 14 | ⊕(S, random) | Provocación | ⊕ (inyección externa) | Coherencia del sistema |
| 15 | iso_X(S) | Reencuadre | extensión del espacio de isos | Clase de herramienta |
| 16 | abandonar | Destrucción creativa | meta-decisión | El marco entero |
| 17 | generar S' | Creación | generación desde restricciones | La premisa de análisis |

### 5.3 Pensamiento INTER-ÁLGEBRA (opera entre álgebras distintas)

| Expresión | Pensamiento | Qué produce |
|-----------|-------------|-------------|
| ∫(álgebra_A \| álgebra_B)(caso) | Síntesis multi-inteligencia | Lo que emerge al cruzar dos sistemas de razonamiento |
| álgebra_A − álgebra_B | Complementariedad | Qué puede ver A que B no puede, por construcción |
| álgebra_A → álgebra_B | Meta-explicación | Por qué el razonamiento de A produce la forma que B detecta |
| álgebra_A(output_B) | Lectura cruzada | Una inteligencia leyendo el output de otra |

---

## 6. COMBINATORIA INTER-ÁLGEBRA

Con 18 álgebras y 4 operaciones inter-álgebra:

| Operación | Combinaciones | Qué produce |
|-----------|---------------|-------------|
| ∫(subconjuntos de 18) | 2¹⁸ - 19 = 262.125 | Síntesis multi-inteligencia |
| A − B (18 × 17) | 306 | Mapa de complementariedad |
| A → B (18 × 17) | 306 | Meta-explicaciones |
| A(output_B) | 306 | Lecturas cruzadas |

Total teórico: ~263.000 expresiones inter-álgebra.

Acotado por saturación y redundancia: el diferencial determina cuáles de las 306 combinaciones de pares son genuinamente complementarias. Las redundantes se eliminan.

---

## 7. PUNTOS CIEGOS CRUZADOS — el valor de la tabla

La propiedad más potente de la tabla: **cada punto ciego de una álgebra es el objeto natural de otra**.

| Álgebra | Su punto ciego | Quién lo ve |
|---------|---------------|------------|
| Lógico-matemática | Lo ambiguo | Social, Contemplativa |
| Computacional | Lo no-computable | Cinestésica, Estética |
| Estructural | No genera soluciones | Constructiva, Divergente |
| Ecológica | No ve al individuo | Social, Existencial |
| Estratégica | Asume competición | Social, Contemplativa |
| Política | Confunde poder con verdad | Lógico-mat, Existencial |
| Financiera | Lo sin precio no existe | Existencial, Social |
| Social | Sobrepsicologiza | Estructural, Lógico-mat |
| Lingüística | Confunde nombrar con resolver | Constructiva, Cinestésica |
| Cinestésica | No verbaliza | Lingüística, Narrativa |
| Espacial | Lo sin extensión no existe | Narrativa, Social |
| Narrativa | Fuerza protagonista | Ecológica, Lógico-mat |
| Prospectiva | El cisne negro | Contemplativa, Divergente |
| Divergente | No evalúa | Lógico-mat, Financiera, Estratégica |
| Estética | Lo feo puede ser verdadero | Lógico-mat, Estructural |
| Constructiva | No cuestiona premisas | Existencial, Estructural |
| Existencial | Puede paralizar | Estratégica, Constructiva |
| Contemplativa | Puede desconectar de acción | Estratégica, Constructiva |

---

## 8. IMPLICACIONES PARA OMNI-MIND

### 8.1 El Motor v3.3 en la tabla
El Motor usa álgebra #3 (Estructural) con isomorfismos inspirados en #4 (Ecológica/conjuntos), #5/#6 (Estratégica/juegos + Política/agentes), y parcialmente #4 (Ecológica/cibernética). De 18 álgebras, usa fragmentos de 5.

### 8.2 El Router como selector de álgebras
El router no elige "programa de la biblioteca". Elige qué álgebras de inteligencia combinar según el problema:
- Problema financiero → Financiera + Computacional + Estratégica
- Problema de vida → Estructural + Existencial + Social + Financiera
- Problema de diseño → Constructiva + Estética + Espacial + Divergente
- Problema político → Política + Estratégica + Narrativa + Social

### 8.3 IAS como la química de la inteligencia
Cada álgebra es un elemento. Las combinaciones son compuestos. IAS es la ciencia que dice:
- Qué compuestos producen qué reacciones
- Qué elementos son complementarios (diferencial grande)
- Qué elementos son redundantes para un caso dado (diferencial pequeño)
- Cuánta profundidad es útil antes de saturación

---

## 9. PENDIENTE

1. **Validación empírica**: ejecutar al menos 3 álgebras distintas sobre el caso dental y medir diferenciales
2. **Mapa de complementariedad**: las 306 combinaciones de pares, medidas por diferencial
3. **Programas multi-álgebra**: recetas que combinan 2-4 álgebras para tipos de problema comunes
4. **Saturación inter-álgebra**: ¿cuántas álgebras aportan valor marginal antes de saturar?
5. **Isomorfismos por álgebra**: ¿cada álgebra tiene su propio set de isos, o comparten?
6. **Router v2**: selector de álgebras, no solo de programas

---

**FIN TABLA PERIÓDICA DE LA INTELIGENCIA CR0**



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/CINESTESICA.md
============================================================

# F1-10: INT-10 — INTELIGENCIA CINESTÉSICA

---

## CASO 1: CLÍNICA DENTAL

### EXTRAER — mapear el cuerpo

**¿Dónde se acumula tensión?** En el propietario. 2.500 horas/año, 60h/semana, sin vacaciones en 2 años. Él es el punto que nunca descansa. No hay rotación de carga: él absorbe la operación clínica, la gestión, la deuda, la relación familiar deteriorada. Su cuerpo es el cuello de botella y el motor a la vez.

**¿Hay flujo?** A tirones. El tercer sillón vacío al 40% indica que la capacidad instalada no fluye — hay capacidad ociosa que no se convierte en ingreso. Los pacientes entran y salen, pero el sistema tiene huecos que el propietario no puede llenar porque ya está saturado. El flujo de dinero es positivo pero estrecho: 7.000€ de margen sobre 45.000€ de facturación es un sistema que respira apenas.

**¿Sostenible o hacia el colapso?** Se acelera hacia el colapso. La historia del padre (infarto a los 52, 70h/semana) es el dato cinestésico brutal: el cuerpo ya tiene un mapa genético y biográfico de hacia dónde va esto. 38 años + 14 años al mismo ritmo = la edad exacta del infarto paterno.

**¿Rigidez?** La estructura "yo hago todo" es rígida. El asociado trabaja 1.800h pero no gestiona, no vende, no decide. El propietario no ha creado un sistema que funcione sin él — cada sillón que añada amplifica su rigidez, no la reduce.

**¿Qué sabe el cuerpo que el plan ignora?** El cuerpo sabe que no puede más. La esposa lo verbaliza ("no paras nunca"), los hijos lo sienten (preguntan por él), pero el plan dice "más sillones, más horas, más ingresos." El plan es cerebral; el cuerpo ya está dando señales de alarma que el propietario traduce como "necesito más capacidad" cuando la señal real es "necesito descanso."

### CRUZAR — tensión × ritmo

**¿Tensión = actividad o bloqueo?** Coincide con actividad máxima. Las 60h semanales son actividad pura, no bloqueo. Pero la actividad sin pausa genera tensión acumulativa que no se descarga. El bloqueo está en la parte ociosa — el sillón vacío — que no genera tensión operativa pero sí tensión financiera.

**¿Ritmo impuesto o natural?** Impuesto por la estructura financiera. 32.000€ de costes fijos + 2.800€ de hipoteca imponen un mínimo de facturación que obliga un ritmo que no puede bajar. El ritmo no es del dentista; es de la deuda.

**¿Si baja 20%?** Mejoraría: presencia familiar, salud, claridad mental para decisiones estratégicas. Empeoraría: el margen de 7.000€ se estrecharía peligrosamente o desaparecería. Esto revela que el sistema no tiene elasticidad — no puede desacelerar sin romperse financieramente.

**¿La rigidez protege?** Protege el flujo de caja mínimo. Si el propietario aflojara sin reorganizar costes, el sistema quebraría. Pero la rigidez impide ver que hay un sillón vacío al 40% que, bien gestionado, podría generar más margen sin más horas del propietario.

### LENTE L1 — Tensión

La contracción está en el cuerpo del propietario: 60h/semana sostenidas durante años. Es tensión dañina — un nudo, no un músculo trabajando. Un músculo trabajando tiene ciclos de contracción y relajación. Aquí no hay relajación. Si soltara esa tensión (trabajar 40h, delegar), el sistema actual colapsaría financieramente a menos que simultáneamente optimice la capacidad ociosa y delegue gestión.

### LENTE L2 — Flujo

Lo que fluye con facilidad: los pacientes entran, se tratan, pagan. La operación clínica básica funciona. Lo que se atasca: la conversión de capacidad en ingreso (sillón vacío 40%), la delegación de funciones, la toma de decisiones estratégicas. Movimiento innecesario: el propietario haciendo tareas que podría delegar a personal administrativo o al asociado con mayor responsabilidad.

### LENTE L3 — Ritmo

No hay ciclos naturales de descanso. Producción constante forzada. Última pausa genuina: hace más de 2 años. El sistema opera como un músculo en contracción permanente — eso genera necrosis, no fuerza. La propuesta de abrir sábados eliminaría el último vestigio de pausa.

### LENTE L4 — Coordinación

Las partes no se mueven juntas. El propietario va a 60h, el asociado a ~35h/semana. El tercer sillón opera intermitentemente. La familia opera en un ritmo doméstico que el propietario no habita. Hay al menos 3 relojes distintos (propietario, clínica, familia) sin sincronía. El propietario marca el ritmo; la familia lo sufre.

### INTEGRAR

La tensión acumulada en el propietario causa el atasco en la toma de decisiones (no puede pensar claro cuando opera a 60h), el atasco rompe el ritmo natural (no hay pausa que permita recalibrar), y el ritmo roto descoordina todo (familia desconectada, asociado sub-utilizado, sillón vacío).

### ABSTRAER

Todo sistema biológico o empresarial que opera sin ciclos de descanso acumula esta cascada. Los músculos sin descanso se atrofian, no se fortalecen. Las máquinas sin mantenimiento se rompen. No es metáfora: es mecánica.

### FRONTERA

El cuerpo sabe algo que el análisis confirma pero no puede sentir: la historia del padre no es un dato — es una memoria somática. El miedo al infarto y el impulso de expandir coexisten en el mismo cuerpo. Esa contradicción no se resuelve con un Excel.

---

**RESUMEN (200 palabras):**

El sistema de la clínica dental tiene un punto de tensión absoluto: el propietario. Con 60 horas semanales, sin vacaciones en 2 años, y un padre que sufrió infarto a los 52 en condiciones idénticas, el cuerpo ya está emitiendo señales que el plan de expansión ignora. El tercer sillón vacío al 40% revela que el problema no es capacidad insuficiente sino capacidad mal distribuida. El ritmo está impuesto por la estructura de costes fijos (32.000€/mes), no por la demanda real, creando un sistema sin elasticidad que no puede desacelerar sin quebrarse. La coordinación es nula: propietario a 60h, asociado a 35h, familia desconectada, sillón ocioso. La propuesta de expansión (5 sillones, sábados abiertos) amplificaría la tensión sin resolver el problema estructural: un sistema que depende de un solo cuerpo humano para funcionar. La cascada cinestésica es clara: tensión sin descarga → decisiones atascadas → ritmo forzado → descoordinación total. La sabiduría corporal aquí es literal: el antecedente paterno no es un dato estadístico, es un mapa de ruta biológico que el análisis racional no integra.

**FIRMA:** El cuerpo del propietario es un reloj biológico que ya tiene programada su fecha de colapso. Expandir sin descansar es acelerar el reloj, no ampliar el negocio.

---

## CASO 2: STARTUP SAAS

### EXTRAER — mapear el cuerpo

**¿Dónde se acumula tensión?** En el CTO: 70h/semana, cofundador técnico se fue, equipo junior que necesita supervisión constante, 47 bugs abiertos que él probablemente triagea. Pero también en la relación CTO-CEO: apenas se hablan fuera de reuniones formales. La tensión interpersonal es un segundo foco que no descansa nunca — es un nudo que opera en silencio.

**¿Hay flujo?** El flujo está roto en múltiples puntos. El producto tiene 47 bugs → los clientes se van (8% churn mensual) → los ingresos no crecen → los fondos no invierten → el runway se acorta. Es un sistema donde cada obstrucción alimenta la siguiente. No hay flujo limpio en ninguna dirección.

**¿Sostenible o colapso?** Colapso programado. Con 7 meses de runway y 8% de churn mensual, el sistema pierde ~6.4 clientes/mes. En 7 meses: de 80 a ~40 clientes si no hay adquisición nueva. El MRR baja de 12.000€ a ~6.000€. El burn de 28.000€ no baja. Esto no es desaceleración — es hemorragia.

**¿Rigidez?** Dos rigideces en colisión. CTO: "primero estabilizar." CEO: "primero crecer." Ambas posiciones están endurecidas hasta el punto de que no se hablan fuera de reuniones. La rigidez no es solo estratégica — es corporal, como dos personas que se han agarrotado en posiciones de combate.

**¿Qué sabe el cuerpo que el plan ignora?** El cuerpo del equipo lo sabe: 2 devs se fueron en 12 meses. Eso es el sistema expulsando gente por sobrecarga, como un organismo que pierde tejido cuando no recibe suficiente oxígeno. El plan (pivotar a enterprise O estabilizar) ignora que el sistema ya está en modo de supervivencia, no de crecimiento.

### CRUZAR — tensión × ritmo

**¿Tensión = actividad o bloqueo?** Ambas, y eso es lo tóxico. El CTO trabaja 70h (actividad máxima) PERO el producto tiene 47 bugs (bloqueo máximo). Actividad intensa que no resuelve los bloqueos: es como correr en arena — máximo esfuerzo, mínimo avance.

**¿Ritmo impuesto o natural?** Impuesto por el runway. 7 meses es un reloj externo que marca un ritmo de urgencia que no corresponde con la capacidad del equipo (3 juniors + 1 part-time). El ritmo necesario es de sprinter; la capacidad es de equipo amateur.

**¿Si baja 20%?** Mejoraría: menos rotación, mejor calidad de código, quizás menos bugs nuevos. Empeoraría: el runway se sentiría aún más corto psicológicamente, y el CEO aumentaría la presión para pivotar. Revelaría que la contradicción real no es velocidad vs. calidad sino capacidad del equipo vs. ambición del plan.

**¿La rigidez protege?** La rigidez del CTO ("estabilizar primero") protege la integridad del producto y del equipo. La rigidez del CEO ("crecer o morir") protege contra la muerte por inanición. Ambas rigideces protegen algo real, pero su colisión destruye la coordinación.

### LENTE L1 — Tensión

La contracción principal: el CTO sosteniendo solo un producto que se desmorona con un equipo insuficiente. Es tensión dañina — un nudo triple: técnica (47 bugs), humana (equipo junior sin senior), relacional (silencio con el CEO). Si soltara esa tensión (dejara la startup o se rindiera al pivot), el producto colapsaría inmediatamente porque no hay nadie más que sostenga la arquitectura técnica.

### LENTE L2 — Flujo

Fluye con facilidad: nada, francamente. Todo está atascado. Los bugs bloquean la retención, la retención bloquea los ingresos, los ingresos bloquean el fundraising, el fundraising bloquea el runway. Atascos por falta de capacidad (equipo junior) Y por bloqueo (conflicto CTO-CEO impide priorizar). Movimiento innecesario: el 30% de ingresos de 3 clientes grandes que piden features custom → el equipo construye lo que esos 3 quieren en vez de lo que los 80 necesitan. Es movimiento que alimenta a pocos y descuida a muchos.

### LENTE L3 — Ritmo

No hay ciclos. Todo es urgencia permanente. Un equipo que trabaja en modo crisis constante durante meses pierde capacidad de discriminar entre lo urgente y lo importante. La última pausa genuina probablemente fue antes de que el cofundador técnico se fuera (hace 6+ meses). Desde entonces: sprint permanente sin retrospectiva real.

### LENTE L4 — Coordinación

Descoordinación total entre CTO y CEO. Cada uno marca un ritmo diferente hacia una dirección diferente. El equipo junior recibe señales contradictorias (¿estabilizo o construyo features enterprise?). El diseñador part-time probablemente no sabe a qué dar prioridad. Los 3 clientes grandes marcan un tercer ritmo (features custom) que no coincide ni con el CTO ni con el CEO. Tres marcapasos compitiendo = arritmia organizacional.

### INTEGRAR

La tensión CTO-CEO causa los atascos de priorización → los atascos rompen el ritmo del equipo (no saben qué construir) → el ritmo roto descoordina toda la operación (bugs, churn, runway). Pero además hay un loop de retroalimentación: la descoordinación genera más tensión CTO-CEO, que endurece más las posiciones, que empeora los atascos.

### ABSTRAER

Todo organismo donde dos centros de control envían señales opuestas al mismo cuerpo genera parálisis espástica — contracción simultánea de agonistas y antagonistas. No es que no haya fuerza; es que la fuerza se cancela.

### FRONTERA

El cuerpo de esta organización (el equipo) ya votó: 2 devs se fueron. Eso no es un dato de recursos humanos — es el sistema rechazando la condición actual de la misma manera que un cuerpo vomita algo tóxico. El análisis puede diagnosticar; el cuerpo ya actuó.

---

**RESUMEN (200 palabras):**

La startup es un organismo en parálisis espástica: dos centros de control (CTO y CEO) envían señales opuestas al mismo cuerpo (equipo), generando contracción simultánea que cancela toda fuerza productiva. El CTO trabaja 70h/semana pero 47 bugs permanecen abiertos — máximo esfuerzo, mínimo avance, como correr en arena. El flujo está roto en cascada: bugs → churn 8% → ingresos estancados → fondos rechazan → runway se acorta. No hay un solo canal limpio. El ritmo está impuesto por un runway de 7 meses sobre un equipo de capacidad amateur (3 juniors, 1 part-time), produciendo una disonancia entre la velocidad exigida y la velocidad posible. La coordinación es nula: CTO quiere estabilizar, CEO quiere pivotar, 3 clientes grandes quieren features custom — tres marcapasos compitiendo generan arritmia organizacional. El cuerpo del sistema ya emitió su veredicto: 2 desarrolladores se fueron en 12 meses. Eso es expulsión de tejido por falta de oxígeno, no rotación. Las dos rigideces protegen algo real, pero su colisión es más destructiva que cualquiera de las dos opciones por separado. La parálisis mata más rápido que la dirección equivocada.

**FIRMA:** La startup no tiene un problema de dirección sino de parálisis espástica: dos fuerzas opuestas contraen el mismo cuerpo simultáneamente. La parálisis mata más rápido que la dirección equivocada.

---

## CASO 3: CAMBIO DE CARRERA

### EXTRAER — mapear el cuerpo

**¿Dónde se acumula tensión?** En el cuerpo literal de la abogada. Insomnio de 2 años. El médico lo diagnostica como estrés laboral, pero cinestésicamente el insomnio es el cuerpo gritando lo que la mente no decide. La tensión también se acumula en el espacio entre lo que siente (quiero irme) y lo que hace (me quedo). Esa brecha es la zona que no descansa.

**¿Hay flujo?** El flujo profesional funciona (20 años en bufete, salario de 180.000€), pero es un flujo mecánico, sin vitalidad. Es como un corazón que late pero sin fuerza. La pasión se detuvo hace tiempo; lo que fluye es inercia. Lo que NO fluye: la conversación con el marido, la decisión, la acción. Tres años pensando sin moverse es flujo bloqueado en su forma más pura.

**¿Sostenible?** No. El insomnio de 2 años es un marcador biológico de insostenibilidad. El cuerpo no miente cuando no puede dormir: algo está tan desalineado que el sistema nervioso no se apaga. Esto no se resuelve con melatonina; se resuelve con un cambio o con un colapso.

**¿Rigidez?** Múltiples capas de rigidez. Financiera: hipoteca + universidad del hijo mayor en 2 años. Social: padres que dicen "estás loca", rechazo para socia como señal de que el sistema no la quiere pero tampoco la suelta. Identitaria: 20 años haciendo lo mismo crea rigidez de identidad — "soy abogada corporativa" es una armadura que protege y asfixia simultáneamente.

**¿Qué sabe el cuerpo que el plan ignora?** El cuerpo ya decidió. El insomnio no es indecisión — es la respuesta del cuerpo a vivir en contradicción con lo que quiere. "Si no lo hago ahora, no lo haré nunca" no es un pensamiento; es una sensación visceral de ventana cerrándose. Pero la mente sigue calculando (hipoteca, hijos, padres) mientras el cuerpo ya votó.

### CRUZAR — tensión × ritmo

**¿Tensión = actividad o bloqueo?** Bloqueo absoluto. La tensión no está en la actividad profesional (esa funciona mecánicamente) sino en la no-acción: 3 años pensando sin moverse. Es tensión isométrica — máxima contracción sin movimiento.

**¿Ritmo impuesto o natural?** El ritmo del bufete es impuesto y ella lo sabe (la rechazaron para socia — el ritmo del sistema no la sincroniza). Su ritmo natural la lleva hacia el derecho medioambiental, pero no se permite seguirlo.

**¿Si baja 20%?** Si la intensidad laboral bajara 20%, el insomnio probablemente mejoraría algo, pero el problema de fondo no cambiaría. La tensión no es de volumen sino de dirección: no es que trabaje demasiado, es que trabaja en lo incorrecto.

**¿La rigidez protege?** La rigidez financiera protege algo real: la estabilidad de los hijos, la hipoteca. La rigidez identitaria y social protege algo más dudoso: la comodidad de no arriesgar. Hay que distinguir qué rigidez es estructura necesaria y cuál es jaula.

### LENTE L1 — Tensión

La contracción está en el diafragma — metafórica y probablemente literalmente. El insomnio de 2 años es el indicador. La tensión es dañina: no produce nada, solo desgasta. No es el músculo de una atleta entrenando; es el espasmo de alguien que no puede soltar ni avanzar. Si soltara esa tensión (decidiera en cualquier dirección), el cuerpo se relajaría. La parálisis es más dañina que cualquiera de las dos opciones.

### LENTE L2 — Flujo

Lo que fluye: el ingreso (180.000€/año), la rutina profesional, la estructura familiar básica. Lo que se atasca: la decisión (3 años), la comunicación con el marido (no ha hablado en profundidad), la transición profesional. Movimiento innecesario: seguir trabajando con la misma intensidad en algo que ya no tiene sentido para ella es el movimiento más costoso — energía invertida en un sistema que el cuerpo ya rechaza.

### LENTE L3 — Ritmo

No hay ciclos de descanso genuino: el insomnio elimina el ciclo más básico (sueño/vigilia). El cuerpo no puede entrar en modo reparación porque la mente no descansa. 3 años es un ciclo absurdamente largo de deliberación sin resolución — ni siquiera los ciclos de reflexión tienen cierre. Última pausa genuina: imposible de determinar, pero el insomnio de 2 años sugiere que lleva al menos ese tiempo sin una.

### LENTE L4 — Coordinación

Las partes del sistema están radicalmente desincronizadas. El cuerpo quiere irse (insomnio = rechazo somático). La mente calcula quedarse. El marido no sabe lo que pasa. Los padres empujan a quedarse. La amiga modela la salida. Cinco relojes, cero sincronía.

### INTEGRAR

La tensión de la indecisión causa el atasco de flujo (3 años sin moverse), el atasco elimina el ritmo natural (no puede ni dormir), y la pérdida de ritmo descoordina todo el sistema.

### ABSTRAER

Todo sistema que mantiene una contradicción interna sin resolverla acumula esta cascada. El cuerpo humano en particular tiene un mecanismo claro: estrés sostenido sin resolución produce insomnio, que produce deterioro cognitivo, que empeora la capacidad de decisión, que prolonga la contradicción. Loop somático autodestructivo.

### FRONTERA

El cuerpo tiene una sabiduría que el análisis financiero no puede capturar: "si no lo hago ahora, no lo haré nunca" no es un cálculo — es una percepción kinestésica de que la ventana de plasticidad vital se cierra. A los 45, el cuerpo sabe cosas sobre el tiempo que queda que la mente intenta ignorar con hojas de cálculo.

---

**RESUMEN (200 palabras):**

El cuerpo de la abogada ya decidió: 2 años de insomnio no son indecisión, son rechazo somático a vivir en contradicción. La tensión no es de volumen (no trabaja demasiado) sino de dirección (trabaja en lo incorrecto), lo que hace que reducir horas no resolvería nada. Tres años deliberando sin moverse es tensión isométrica pura: máxima contracción, cero movimiento, máximo desgaste. El flujo mecánico funciona (dinero entra, rutina opera) pero carece de vitalidad — un corazón que late sin fuerza. La coordinación es nula: cinco relojes desincronizados (cuerpo, mente, marido, padres, amiga) apuntan en direcciones diferentes, y la persona más importante de la ecuación (el marido) no tiene información. Las rigideces son de dos tipos: estructurales legítimas (hipoteca, universidad) y jaulas identitarias/sociales. La cascada cinestésica es textual: contradicción no resuelta → insomnio → deterioro cognitivo → peor capacidad de decisión → más contradicción. El hallazgo frontera es que "si no lo hago ahora, no lo haré nunca" no es una frase — es una percepción cinestésica de la ventana de plasticidad vital cerrándose. El cuerpo mide el tiempo que queda de un modo que el Excel no captura.

**FIRMA:** El insomnio no es un síntoma — es el veredicto del cuerpo. Y la frase "si no lo hago ahora, no lo haré nunca" no es miedo — es el cuerpo midiendo el tiempo que queda de un modo que ninguna hoja de cálculo puede capturar.

---

## LOOP TEST

**Caso elegido: Startup SaaS**

Aplico las mismas preguntas cinestésicas a mi propio output:

**¿Dónde se acumula tensión en MI análisis?** En la metáfora de "parálisis espástica." Me apoyé fuertemente en ella y puede estar comprimiendo matices. La tensión de mi output está en equiparar completamente una organización con un cuerpo biológico — funciona bien como lente pero puede oscurecer diferencias.

**¿Hay flujo en mi análisis?** El flujo narrativo es fuerte: cada bloque alimenta al siguiente. Pero hay un atasco: no exploré suficientemente qué pasaría si CTO y CEO se alinearan en una tercera opción. Mi análisis quedó atrapado en la misma polaridad binaria que critico.

**¿Qué parte de mi análisis está rígida?** Mi diagnóstico asume que la parálisis es el problema central. Pero cinestésicamente, la parálisis podría ser un síntoma de algo más profundo: quizá el CTO ya no quiere estar ahí, y la "defensa del producto" es su manera de no admitirlo.

**¿Qué sabe el cuerpo de mi análisis que la mente ignora?** Mi análisis "siente" que esta startup ya murió y no lo sabe. La acumulación de indicadores negativos crea una sensación de inevitabilidad que mi texto trata como "urgente pero salvable."

**Hallazgo genuinamente nuevo:** La primera pasada diagnosticó disfunción. La segunda pasada revela que quizás el organismo ya está en fallo multiorgánico, y que la pregunta no es "pivotar o estabilizar" sino "cerrar con orden o esperar al colapso." Además, el CTO puede estar usando la "defensa del producto" como sustituto de admitir que quiere irse, replicando el patrón del cofundador que se fue. **Es genuinamente nuevo.**

---

## PATRÓN CROSS-CASE

Los tres casos comparten un patrón cinestésico idéntico: **el cuerpo ha decidido antes que la mente, pero la persona interpreta la señal del cuerpo como un problema a resolver en vez de como una respuesta ya dada.**

- Dentista: el cuerpo repite la historia del padre → él la traduce como "necesito expandir"
- CTO: el equipo expulsa gente → él la traduce como "necesito estabilizar"
- Abogada: insomnio de 2 años → ella la traduce como "necesito calcular mejor"

En los tres casos, la señal somática es la respuesta, no el problema.

---

## SATURACIÓN

Una tercera pasada sobre el caso SaaS probablemente revelaría más sobre la dinámica de "fallo multiorgánico" y podría profundizar en si la partida del cofundador técnico fue el evento cinestésico fundacional. Hay material suficiente para que no sea pura repetición, pero el retorno marginal disminuye. Aportaría algo, pero no un orden de magnitud más.

**Tercera pasada aportaría:** Sí, marginalmente.

---

## FIRMA GLOBAL

**Lo que la inteligencia cinestésica ve que probablemente ninguna otra vería:** Que los síntomas corporales (insomnio, fatiga crónica, rotación de personal, sillón vacío) no son datos secundarios sino el diagnóstico primario. El cuerpo — individual u organizacional — vota antes que la mente, y su voto es más fiable porque no puede mentirse a sí mismo.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/CONSTRUCTIVA.md
============================================================

# F1-16: INTELIGENCIA CONSTRUCTIVA (Ingeniería)

**Firma de la inteligencia:** CONSTRUIR — convertir diseño en realidad funcional.
**Objetos:** restricciones, materiales, soluciones, prototipos, iteraciones.
**Punto ciego declarado:** optimiza lo existente — no cuestiona si debería existir.

---

## CASO 1: CLÍNICA DENTAL

### EXTRAER — mapear restricciones

**Criterio de éxito:** Que la clínica genere más margen neto sin destruir la vida personal del odontólogo. No es "facturar 65K" — es construir un sistema que funcione sin que él sea el cuello de botella permanente.

**Materiales disponibles:**
- Infraestructura: 3 sillones (1 infrautilizado al 40%).
- Personal: 2 dentistas (él a 2.500h/año, asociado a 1.800h/año).
- Flujo: 45.000€/mes entrada, 32.000€ costes fijos, ~7.000€ margen neto.
- Crédito bancario disponible para ampliar a 5 sillones.
- Experiencia operativa de años (sabe qué funciona clínicamente).

**Restricciones inamovibles:**
- Hipoteca: 280.000€ pendientes, 2.800€/mes. No se negocia.
- Hijos de 4 y 6 años. El tiempo perdido ahora no se recupera.
- Capacidad humana: 168 horas semanales, él ya usa 60.
- Antecedente paterno: infarto a los 52 en régimen similar.

**Restricciones flexibles:**
- El tercer sillón vacío el 40% del tiempo: esto es capacidad sin usar, no restricción.
- El horario del asociado (1.800h/año tiene margen de subida si se incentiva).
- El precio por acto/tratamiento (no se menciona si está optimizado).
- La mezcla de servicios (tratamientos de alto vs. bajo margen).

**Qué ya funciona y se puede reutilizar:**
- La clínica factura 45K — el flujo base existe. No es un startup, es un negocio operativo.
- Tiene un asociado que ya funciona. No necesita reclutar desde cero.
- La marca y la cartera de pacientes existen.

**Qué ha fallado antes:**
- El modelo "más horas = más ingresos" ya falló: trabaja 60h/semana con 7K netos. El rendimiento marginal de su hora personal es decreciente.
- No ha tomado vacaciones en 2 años — señal de que el sistema no funciona sin él.

### CRUZAR — objetivo × restricciones

**¿El objetivo es alcanzable con los materiales disponibles?**
El objetivo declarado ("65K/mes si abro sábados y contrato otro dentista") es técnicamente posible pero ignora la restricción real: él ya está al 100% de utilización. Ampliar a 5 sillones con otro dentista requiere gestión, formación, supervisión — tiempo que no tiene.

**¿Qué falta?**
Falta capacidad de gestión delegada. No necesita más sillones — necesita que los 3 actuales produzcan más sin depender de sus horas. Falta un gerente o un sistema que lo libere de tareas no-clínicas.

**¿Formas de reducir el objetivo sin perder lo esencial?**
Sí: subir de 7K a 12-15K netos/mes sin ampliar, usando el sillón 3 al 80-90% en vez del 60%, optimizando mezcla de servicios hacia tratamientos de mayor margen, y revisando precios. Eso no requiere crédito ni sábados.

**¿Las restricciones reales son menos de las que cree?**
Sí. Él percibe que la restricción es "no suficientes sillones" cuando la restricción real es "no suficiente producción por sillón existente." El sillón vacío al 40% es evidencia de que el cuello de botella no es infraestructura — es gestión de agenda y mix de servicios.

### LENTE L1 — Prototipo

**Versión más pequeña que se puede construir y probar:**
Llenar el sillón 3 al 80% durante 3 meses. No contratar, no ampliar, no abrir sábados. Solo optimizar agenda: mover tratamientos de mayor margen al sillón vacío, contratar un higienista para profilaxis (libera tiempo del asociado para tratamientos de mayor valor).

**¿Qué aprenderías?**
- Si el problema es demanda (no hay suficientes pacientes) o gestión (hay pacientes pero la agenda no los captura).
- Cuánto margen neto genera cada hora adicional del sillón 3 — dato que hoy no tiene.
- Si el asociado puede absorber más carga con incentivo variable.

**¿Cuánto cuesta y cuánto tiempo lleva?**
Coste: un higienista a tiempo parcial (~1.500-2.000€/mes). Tiempo: 3 meses para tener datos fiables. Inversión total: ~6.000€. Comparar con el crédito de expansión que multiplicaría la deuda.

### LENTE L2 — Secuencia

**¿Qué se construye primero?**
1. **Diagnóstico de utilización real**: medir horas productivas vs. horas disponibles por sillón. Esto es el cimiento — sin datos, cualquier decisión es ciega.
2. **Optimización de agenda**: redistribuir tratamientos para maximizar el sillón 3.
3. **Contratación de higienista**: libera al asociado para actos de mayor margen.
4. **Evaluación a 3 meses**: ¿subió el margen neto? ¿Cuánto?
5. **Solo entonces**: decidir si ampliar tiene sentido basándose en datos reales.

**¿Qué depende de qué?**
No puedes contratar otro dentista con sentido si no sabes cuánta capacidad real tienes sin usar. No puedes abrir sábados sin saber si los sábados generan suficiente margen diferencial vs. el coste (personal + desgaste).

**Camino crítico:**
Diagnóstico de utilización → optimización de agenda → contratación de higienista → datos de 3 meses → decisión informada. Tiempo total: 4-5 meses.

### LENTE L3 — Fallo

**¿Qué se va a romper primero?**
Si expande: él. Ya trabaja 60h/semana. Ampliar a 5 sillones con un tercer dentista que necesita supervisión lo llevaría a 70h+. Su padre tuvo infarto a los 52 con patrón idéntico. Esto no es metáfora — es riesgo médico concreto.

**¿Se puede diseñar para que falle de forma segura?**
Sí: el prototipo (llenar sillón 3 sin ampliar) tiene un modo de fallo seguro — si no funciona, pierdes 6K€ y 3 meses, no 280K€ más crédito adicional. La expansión a 5 sillones no tiene fallo seguro: si falla, tienes más deuda, más personal fijo, y el mismo cuello de botella.

**¿Dónde necesitas margen?**
Margen de tiempo personal: necesita bajar de 60h a 45h antes de considerar cualquier expansión. Si no puede operar a 45h con los ingresos actuales, la expansión no resuelve nada — amplifica el problema.

### LENTE L4 — Iteración

**¿Se construye de una vez o por versiones?**
Por versiones, obligatoriamente.
- **V1**: Optimizar lo existente (sillón 3, mezcla de servicios, precios). 3 meses.
- **V2**: Si V1 funciona, delegar más al asociado con incentivo variable. Reducir horas propias. 3 meses.
- **V3**: Si V2 funciona y hay demanda insatisfecha demostrada, entonces evaluar expansión. 6 meses después del inicio.

**¿Qué aprende cada versión?**
- V1 aprende si la restricción es demanda o gestión.
- V2 aprende si el asociado puede sostener más carga sin él.
- V3 aprende si la expansión es necesaria o si V1+V2 ya resolvieron.

**¿Cuántas iteraciones necesarias?**
Mínimo 2 (V1 y V2). Probablemente la V3 (expansión) no sea necesaria si V1 y V2 funcionan. Pero necesitas los datos para saberlo.

### INTEGRAR

El prototipo (llenar sillón 3), la secuencia (datos → optimización → delegación → decisión), los modos de fallo (proteger contra sobre-apalancamiento y colapso físico) y la iteración (3 versiones, cada una informando la siguiente) son completamente coherentes. Todos apuntan a lo mismo: **no expandir sin antes demostrar que has exprimido lo que tienes**.

### ABSTRAER

Principio de ingeniería: **antes de escalar capacidad, maximizar utilización de la capacidad existente.** Añadir sillones con un sillón vacío al 40% es como comprar otro servidor con el actual al 60% de carga. El cuello de botella no es infraestructura — es throughput por unidad existente.

### FRONTERA

Construir mejor lo existente **es** la respuesta para los próximos 6-12 meses. Si después de optimizar el sillón 3, delegar al asociado y revisar precios/mix, el margen sube a 12-15K€ y él baja a 45h/semana, la expansión se vuelve una decisión informada en vez de una huida hacia adelante. Si no optimizas primero, expandir es replicar ineficiencia a mayor escala.

### RESUMEN (200 palabras)

La clínica tiene un sillón vacío al 40% y un propietario al 100% de capacidad. El banco ofrece crédito para ampliar, pero ampliar sin optimizar es escalar ineficiencia. El prototipo correcto es llenar el sillón 3 al 80% con un higienista a tiempo parcial (~6K€ de inversión en 3 meses), no añadir 2 sillones con crédito. La secuencia constructiva es: medir utilización real → optimizar agenda y mix de servicios → contratar higienista → evaluar a 3 meses → decidir con datos. El modo de fallo más probable en la expansión es el colapso del propietario: ya trabaja 60h/semana, su padre tuvo infarto a los 52 con patrón idéntico, gestionar 5 sillones y 3 dentistas lo llevaría a 70h+. El prototipo tiene fallo seguro (6K€ perdidos si no funciona); la expansión no lo tiene (más deuda fija + personal). La iteración en 3 versiones (optimizar → delegar → evaluar expansión) permite que cada paso informe al siguiente. El principio de ingeniería es claro: antes de escalar capacidad, maximizar utilización existente. La restricción no es infraestructura — es throughput por sillón.

---

## CASO 2: STARTUP SaaS

### EXTRAER — mapear restricciones

**Criterio de éxito:** Que el producto retenga clientes (churn <3%) y genere suficiente MRR para alcanzar métricas de Serie A, o al menos para extender el runway hasta que lo haga. No es "pivotar a enterprise" ni "estabilizar" en abstracto — es construir algo que la gente pague y no deje de pagar.

**Materiales disponibles:**
- Producto existente: SaaS B2B para gestión de inventario de restaurantes. Funciona lo suficiente para tener 80 clientes.
- Equipo: 3 devs junior + 1 diseñador part-time. Sin senior técnico desde que se fue el co-fundador.
- Ingresos: MRR 12.000€ (80 clientes).
- Capital: runway de 7 meses a burn de 28.000€/mes. ~196.000€ disponibles.
- Datos de mercado: 3 clientes grandes representan 30% de ingresos y pidieron features custom.
- Feedback de fondos: "métricas insuficientes."

**Restricciones inamovibles:**
- Runway: 7 meses. Esto es un reloj que no se para.
- Equipo junior: no puedes hacer un pivot enterprise con 3 juniors. Enterprise requiere arquitectura, seguridad, compliance — trabajo de seniors.
- Churn del 8%/mes: pierdes ~6 clientes al mes. En 10 meses sin mejora, la base de clientes desaparece.
- CTO y CEO no se hablan fuera de reuniones formales. El equipo fundador está roto.

**Restricciones flexibles:**
- El burn de 28K/mes puede reducirse (¿qué parte es esencial?).
- Los 47 bugs son priorizables — no todos importan igual para retención.
- Los 3 clientes grandes son un asset, no solo un riesgo de concentración.
- El diseñador part-time podría escalarse o eliminarse según prioridades.

**Qué ya funciona y se puede reutilizar:**
- 80 clientes que pagan. 30% del churn probablemente viene de bugs específicos — si identificas los top 5 que causan abandono, puedes atacar quirúrgicamente.
- 3 clientes grandes con features custom: ya tienes tu segmento enterprise piloto sin necesidad de pivotar. Ellos te están diciendo qué construir.

**Qué ha fallado antes:**
- El co-fundador técnico se fue: la deuda técnica se acumuló sin liderazgo senior.
- 2 devs se fueron en 12 meses: el equipo no es sostenible a este ritmo.
- 3 fondos miraron y no avanzaron: el pitch o las métricas no convencen.

### CRUZAR — objetivo × restricciones

**¿El objetivo es alcanzable?**
El pivot a enterprise completo NO es alcanzable con los materiales disponibles. No tienes seniors, no tienes tiempo (7 meses), y el churn actual se come la base mientras pivotas. Estabilizar el producto actual SÍ es alcanzable si priorizas los bugs que causan churn.

**¿Qué falta?**
Un senior developer. Sin uno, los 3 juniors no pueden priorizar ni ejecutar la estabilización técnica con la velocidad necesaria. Pero contratar un senior a 7K-10K/mes come runway. Alternativa: contratista senior a tiempo parcial (3 meses, objetivo quirúrgico: arreglar los 10 bugs que más causan churn).

**¿Reducir el objetivo sin perder lo esencial?**
Sí: no pivotar a enterprise. En su lugar, convertir a los 3 clientes grandes en clientes "premium" pagando 3-4x lo actual por features custom priorizadas. Eso es enterprise de facto sin reescribir el producto.

**¿Las restricciones reales son menos de las que cree?**
El CTO cree que necesita arreglar 47 bugs. Probablemente 8-10 bugs causan el 80% del churn. El CEO cree que necesita pivotar a enterprise. Los 3 clientes grandes ya son enterprise — solo necesita cobrarles como tal y darles prioridad.

### LENTE L1 — Prototipo

**Versión más pequeña:**
Sprint de 4 semanas: identificar los 10 bugs que correlacionan con las últimas 20 bajas. Arreglar los 5 más impactantes. Simultáneamente, proponer a los 3 clientes grandes un plan "premium" a 3x precio con SLA y features priorizadas.

**¿Qué aprenderías?**
- Si el churn baja con fixes quirúrgicos (confirma hipótesis del CTO).
- Si los clientes grandes pagan más por prioridad (confirma si hay camino enterprise sin pivot).
- Si el equipo junior puede ejecutar con dirección clara (confirma si necesitas senior o no).

**¿Cuánto cuesta?**
4 semanas del equipo actual (ya pagadas en el burn). Coste adicional: 0€. Coste de oportunidad: retrasar 4 semanas cualquier otra iniciativa. Con 7 meses de runway, gastar 1 mes en validar es razonable.

### LENTE L2 — Secuencia

**Cimiento:**
1. **Análisis de churn**: correlacionar las 20 últimas bajas con bugs/features específicos. 1 semana.
2. **Fix quirúrgico**: los top 5-10 bugs vinculados a churn. 3 semanas.
3. **Propuesta premium a clientes grandes**: oferta con SLA, features priorizadas, precio 3-4x. Semana 2 (en paralelo con fixes).
4. **Medición a 8 semanas**: ¿bajó el churn? ¿Aceptaron la oferta premium?
5. **Decisión de CTO-CEO con datos**: si churn baja Y premium funciona, el camino es escalar eso. Si no, los datos guían la conversación.

**Dependencias:**
No puedes hacer el pitch enterprise a fondos sin métricas de retención. No puedes reducir churn sin identificar sus causas reales. No puedes proponer premium sin tener estabilidad mínima.

**Camino crítico:**
Análisis de churn (1 semana) → fixes top (3 semanas) → medición (8 semanas) = 12 semanas (~3 meses). Te quedan 4 meses de runway después. Si funciona, las métricas mejoradas te dan una historia para fondos.

### LENTE L3 — Fallo

**¿Qué se va a romper primero?**
El equipo. 3 juniors + CTO a 70h/semana + 2 devs ya se fueron en 12 meses. Si otro junior se va durante el sprint, pierdes un tercio de la capacidad de desarrollo. El equipo es el punto de fallo más frágil.

**¿Fallo seguro?**
Sí: el prototipo de 4 semanas no quema runway adicional. Si falla (churn no baja, clientes grandes no aceptan premium), aprendes en 4 semanas en vez de en 7 meses. Puedes ajustar. Un pivot enterprise que falla te deja con 0 meses de runway, un producto a medio reescribir, y la base de restaurantes perdida.

**¿Dónde necesitas margen?**
En el equipo: el CTO debe bajar a 50h/semana o se va a ir como el co-fundador anterior. Contratar un contratista senior a 3 meses (5-8K/mes) protege contra la fragilidad del equipo junior y libera al CTO para gestión y visión.

### LENTE L4 — Iteración

**Versiones:**
- **V1** (mes 1-3): Fix quirúrgico + propuesta premium. Medir churn y conversión premium.
- **V2** (mes 3-5): Si V1 funciona, escalar el modelo premium a más clientes medianos-grandes. Refinar producto con feedback premium. Preparar métricas para fondos.
- **V3** (mes 5-7): Con métricas mejoradas, volver a fondos. O, si el MRR premium cubre burn, eliminar la necesidad de ronda.

**Cada versión aprende:**
- V1: ¿el churn es solucionable quirúrgicamente? ¿Hay apetito premium?
- V2: ¿el modelo premium escala? ¿Cuántos clientes pueden pagar 3-4x?
- V3: ¿las métricas convencen a fondos? ¿O ya no necesitamos fondos?

**Iteraciones necesarias:** 2-3. Si V1 falla (churn no baja, premium no convierte), necesitas pivotar de verdad — pero con datos que guíen el pivot, no con la intuición del CEO.

### INTEGRAR

Prototipo (fix quirúrgico + premium), secuencia (análisis → fix → medición → decisión), fallo (proteger equipo, evitar pivot sin datos), iteración (3 versiones de 2 meses) son coherentes. Todo converge en: **no reescribas — arregla lo que rompe y cobra más a quien más usa**.

### ABSTRAER

Principio de ingeniería: **arregla el leak antes de añadir agua.** Con 8% de churn mensual, cualquier crecimiento se pierde por el fondo del balde. Ningún pivot, ninguna feature nueva, ninguna ronda de financiación resuelve un producto que pierde el 8% de su base cada mes. Primero tapas el agujero, luego llenas.

### FRONTERA

Construir mejor lo existente es la respuesta para los próximos 3 meses. Pero hay una frontera real: si después de fixes quirúrgicos el churn sigue >5%, el producto puede tener un problema de product-market fit que ningún bug fix resuelve. En ese caso, la respuesta no es "construir mejor" ni "pivotar a enterprise" — es entender por qué los restaurantes no retienen. Eso requiere hablar con los que se fueron, no con los que se quedan.

### RESUMEN (200 palabras)

El startup tiene un balde con agujero: 8% de churn mensual se come la base de clientes más rápido de lo que cualquier pivot puede construir. La restricción no es "restaurantes no pagan suficiente" — es que el producto no retiene. El prototipo correcto es un sprint quirúrgico de 4 semanas: identificar los 10 bugs correlacionados con las últimas 20 bajas, arreglar los 5 más impactantes, y simultáneamente proponer a los 3 clientes grandes un plan premium a 3-4x con SLA y features priorizadas. Coste adicional: 0€ (equipo actual). La secuencia es: análisis de churn → fixes top → propuesta premium → medición a 8 semanas → decisión con datos. El modo de fallo más probable es el equipo: 3 juniors sin senior, CTO a 70h/semana, 2 devs ya se fueron. Un contratista senior a 3 meses (5-8K/mes) protege este punto frágil. El pivot enterprise con juniors en 7 meses de runway es ingeniería suicida. Los 3 clientes grandes ya son el segmento enterprise — solo falta cobrarles como tal. Principio: arregla el leak antes de añadir agua.

---

## CASO 3: CAMBIO DE CARRERA

### EXTRAER — mapear restricciones

**Criterio de éxito:** Una transición profesional que preserve la estabilidad financiera familiar durante los años críticos (universidad del hijo mayor en 2 años) y que resulte en un trabajo que sea sostenible psicológica y físicamente. No es "dejar el bufete mañana" ni "quedarse para siempre" — es construir un puente que soporte el peso de la transición.

**Materiales disponibles:**
- Ingresos actuales: 180.000€/año.
- Ahorros: 120.000€.
- Marido freelance: 40-80K€/año (variable).
- Hipoteca: 1.800€/mes, 15 años pendientes. Total: ~324.000€.
- 20 años de experiencia en derecho corporativo.
- Red de contactos en el sector legal.
- Conocimiento sobre el destino: derecho medioambiental en ONG, ~55.000€/año.
- Una amiga que ya hizo la transición (referencia viva).

**Restricciones inamovibles:**
- Hipoteca: 1.800€/mes × 12 = 21.600€/año. No desaparece.
- Universidad del hijo mayor en 2 años. Coste estimable pero real.
- El insomnio de 2 años: señal de que el statu quo tiene coste fisiológico real.
- No ha hablado en profundidad con su marido. Esta es una restricción de información, no de recursos.

**Restricciones flexibles:**
- El timing: no tiene que ser ahora-o-nunca. La urgencia percibida ("si no lo hago ahora, no lo haré nunca") puede ser real o puede ser presión emocional.
- El salario destino: 55K€ en ONG puede no ser el único punto de llegada. Derecho medioambiental en firma privada, consultoría, posiciones híbridas.
- Los 180K actuales: puede negociar reducción de jornada como paso intermedio.
- Los ahorros como colchón: 120K€ cubren ~2 años del diferencial de salario.

**Qué ya funciona y se puede reutilizar:**
- 20 años de experiencia legal: no se tira a la basura al cambiar de derecho corporativo a medioambiental. Compliance, contratos, negociación, due diligence — todo aplica a medioambiente corporativo.
- Red de contactos: algunos clientes corporativos tienen divisiones de sostenibilidad/ESG. Es un puente natural.
- La amiga que hizo la transición: fuente de información real, no teórica.

**Qué ha fallado antes:**
- 3 años pensando sin actuar: la parálisis por análisis es el fallo recurrente. No ha construido nada — solo ha rumiado.
- No hablar con el marido: la restricción más importante (ingreso conjunto) no está medida porque no ha tenido la conversación.
- Rechazada para socia: el bufete no la va a recompensar por quedarse. El "quizá el próximo ciclo" es una promesa sin compromiso.

### CRUZAR — objetivo × restricciones

**¿El objetivo es alcanzable?**
Sí, pero no en un paso. El salto de 180K a 55K con hipoteca, universidad inminente y marido con ingresos variables requiere un puente financiero y profesional. Los 120K€ de ahorros cubren ~2 años del diferencial (125K/año de gap), pero eso asume gastos congelados e ingresos del marido estables — supuesto frágil.

**¿Qué falta?**
Falta información concreta: ¿cuál es el gasto mensual familiar real? ¿Cuánto cuesta la universidad? ¿Cuál es el ingreso mínimo que el marido puede garantizar? ¿Existen posiciones de derecho medioambiental que paguen más de 55K€? Sin estos datos, cualquier plan es ficción.

**¿Reducir el objetivo sin perder lo esencial?**
Sí: no necesita ir directo a ONG a 55K€. Puede ir a consultoría en derecho medioambiental corporativo (ESG/compliance) que pague 100-120K€, preservando la mayor parte de la estabilidad. O negociar una jornada del 60-80% en el bufete mientras construye un portfolio de trabajo pro-bono en medioambiente.

**¿Las restricciones reales son menos de las que cree?**
Sí. "No puedo arriesgar la estabilidad de mis hijos" es verdad, pero la estabilidad no requiere 180K€ — requiere cubrir hipoteca (21.600€/año) + gastos fijos + universidad. Si el marido aporta 60K€ estables y ella aporta 80-100K€ en posición intermedia, la estabilidad está cubierta.

### LENTE L1 — Prototipo

**Versión más pequeña:**
Dedicar 3 meses a construir credibilidad en derecho medioambiental sin dejar el bufete. Acciones concretas: hacer un curso certificado en derecho medioambiental (2-3 meses, online, ~2.000€). Hacer trabajo pro-bono para una ONG medioambiental los fines de semana (5-8h/semana). Contactar a la amiga y a 3-5 personas más en el sector para mapear opciones reales.

**¿Qué aprenderías?**
- Si realmente le apasiona el derecho medioambiental en la práctica (no solo la idea romántica).
- Qué posiciones existen realmente y a qué salarios (más allá de los 55K€ de ONG).
- Si puede construir un perfil competitivo sin dejar su trabajo actual.
- Si el marido apoya la transición cuando se lo plantea con un plan concreto.

**¿Cuánto cuesta?**
~2.000€ en formación + 5-8h/semana de tiempo. Cero riesgo financiero. 3 meses de calendario.

### LENTE L2 — Secuencia

**Cimiento:**
1. **Conversación con el marido**: datos financieros reales sobre la mesa. ¿Cuál es el gasto familiar mensual? ¿Cuánto puede él estabilizar sus ingresos? ¿Apoya la transición? Sin esto, todo lo demás es construir en el aire. Semana 1.
2. **Auditoría financiera**: gastos fijos, coste universidad estimado, colchón necesario. Semana 2.
3. **Prototipo profesional**: curso + pro-bono + networking. Meses 1-3.
4. **Exploración de posiciones intermedias**: derecho medioambiental corporativo, ESG, consultoría. Meses 2-4.
5. **Negociación con el bufete**: jornada reducida o año sabático parcial. Mes 4-5.
6. **Decisión con datos**: saltar, puente, o quedarse. Mes 6.

**Dependencias:**
No puedes explorar posiciones sin saber si estás cualificada (curso). No puedes decidir saltar sin saber cuánto necesitas ganar (conversación con marido + auditoría). No puedes negociar con el bufete sin tener una alternativa concreta.

**Camino crítico:**
Conversación con marido → auditoría financiera → prototipo profesional (en paralelo) → exploración de posiciones → decisión. 6 meses.

### LENTE L3 — Fallo

**¿Qué se va a romper primero?**
La salud. 2 años de insomnio por estrés laboral no es un dato menor — es una señal de fallo sistémico. Si no cambia nada, el coste no es "seguir igual" — es deterioro progresivo. Esto impone urgencia real, no fabricada.

**¿Fallo seguro?**
El prototipo (curso + pro-bono + conversación) tiene fallo seguro total: si descubre que no le gusta el derecho medioambiental en la práctica, vuelve al bufete sin haber perdido nada excepto 2.000€ y 3 meses de fines de semana. Si descubre que el marido no apoya la transición, tiene datos para una conversación diferente.

Un salto directo de 180K a 55K sin puente financiero: fallo catastrófico si el marido tiene un año malo (40K) y el hijo empieza universidad al mismo tiempo.

**¿Dónde necesitas margen?**
Financiero: mantener 80-100K€ de ahorros intactos como colchón mínimo durante la transición. No gastar los 120K€ como "runway" — eso es pensar como startup con tu familia.

### LENTE L4 — Iteración

**Versiones:**
- **V1** (meses 1-3): Prototipo: curso, pro-bono, conversación con marido, auditoría financiera. Coste: 2.000€ + tiempo.
- **V2** (meses 3-6): Si V1 confirma deseo + viabilidad, buscar posición intermedia (ESG/medioambiental corporativo a 100-120K€). Negociar con bufete reducción o salida planificada.
- **V3** (meses 6-12): Transición efectiva. Si posición intermedia encontrada, ejecutar cambio. Si no, seguir en bufete con V1 como fuente de energía y plan B activo.
- **V4** (año 2-3): Si en posición intermedia, evaluar salto final a ONG cuando hijo mayor haya empezado universidad y las finanzas estén estabilizadas.

**Cada versión aprende:**
- V1: ¿Esto es real o es fantasía de escape?
- V2: ¿Hay mercado para mi perfil en medioambiental?
- V3: ¿La transición funciona financieramente?
- V4: ¿El sacrificio salarial final es sostenible?

**Iteraciones necesarias:** 3-4, distribuidas en 2-3 años. Esto no es un sprint — es una transición de carrera que necesita construirse como un puente, no como un salto.

### INTEGRAR

Prototipo (curso + pro-bono + conversación con marido), secuencia (información → prototipar → posición intermedia → transición), fallo (proteger salud SIN destruir finanzas), iteración (4 versiones en 2-3 años) son coherentes. Todo converge en: **construye el puente antes de quemar la orilla.**

### ABSTRAER

Principio de ingeniería: **never cut over without a rollback plan.** En migración de sistemas, nunca cortas al sistema nuevo sin tener un camino de vuelta al anterior. En transición de carrera, nunca saltas sin una posición intermedia que permita retroceder si falla. La conversación con el marido es el "smoke test" — si no pasa esa prueba en staging, no lo mandas a producción.

### FRONTERA

Construir mejor lo existente (quedarse en el bufete) NO es la respuesta — el insomnio de 2 años lo dice. Pero construir otra cosa requiere hacerlo por fases, no de golpe. La frontera real no es "quedarse vs. irse" — es "irse ahora sin plan vs. construir la salida en 6-12 meses." La inteligencia constructiva dice: construye la alternativa antes de demoler lo actual.

### RESUMEN (200 palabras)

La abogada lleva 3 años pensando y 0 construyendo. El prototipo correcto no es renunciar — es un sprint de 3 meses a coste casi cero: curso de derecho medioambiental (2.000€), trabajo pro-bono para una ONG (5-8h/semana), y la conversación con su marido que lleva años evitando. Esto valida si la pasión es real o es fantasía de escape, y produce datos financieros concretos para un plan real. La secuencia es: conversación con marido → auditoría financiera → prototipo profesional → exploración de posiciones intermedias (ESG a 100-120K€, no solo ONG a 55K€) → decisión informada en 6 meses. El modo de fallo de un salto directo es catastrófico: 125K€/año de gap salarial + universidad en 2 años + marido con ingresos variables. El modo de fallo del prototipo es seguro: 2.000€ y 3 meses de fines de semana. La salud (insomnio 2 años) impone urgencia real pero no justifica un salto sin puente. Cuatro versiones en 2-3 años: prototipar → posición intermedia → transición → refinamiento. Principio: never cut over without a rollback plan.

---

## LOOP TEST

**Caso elegido: Startup SaaS** (análisis más profundo por la interacción de restricciones técnicas, financieras y humanas).

### Segunda pasada sobre mi propio output del Caso 2:

**EXTRAER sobre mi output:**
- **Criterio de éxito de mi análisis:** Que la recomendación (fix quirúrgico + premium) sea construible con los materiales reales del equipo.
- **Materiales de mi análisis:** Asumí que los 3 juniors pueden hacer un sprint quirúrgico de 4 semanas si se les prioriza. Pero ¿pueden? Sin senior, ¿saben identificar cuáles son los bugs que causan churn? La correlación churn-bugs requiere análisis de datos que un junior puede no saber hacer.
- **Restricción no mapeada:** Asumí que el CTO puede dirigir el sprint quirúrgico. Pero el CTO trabaja 70h/semana y además tiene un conflicto activo con el CEO. Si el CEO no acepta el plan "fix primero, pivot después", el CTO no puede ejecutar — necesita buy-in del CEO para priorizar bugs sobre features enterprise.

**CRUZAR sobre mi output:**
- Mi recomendación dice "coste adicional: 0€." Falso. El coste de oportunidad de 4 semanas sin avanzar en features que los 3 clientes grandes pidieron es real: si se van (30% del MRR), pierdes 3.600€/mes de MRR y el argumento premium se evapora.
- La propuesta premium a los 3 clientes grandes la planteé en paralelo con los fixes, pero ¿quién hace el pitch? El CTO es técnico, el CEO quiere enterprise. Falta un rol de producto/ventas que nadie en el equipo tiene.

**L1 — Prototipo de mi prototipo:**
- Mi prototipo asume que el análisis de churn es posible en 1 semana. ¿Tienen los datos? ¿Hay instrumentación que trackee por qué un cliente cancela? Si no hay datos de cancelación, el "análisis" es conjetura.
- La versión más pequeña de mi prototipo: antes del sprint de fixes, una semana de "exit interviews" con los últimos 10 clientes que se fueron. Eso es el prototipo del prototipo.

**L3 — Fallo de mi plan:**
- Identifiqué el equipo como punto de fallo, pero no diseñé protección concreta. "Contratar un contratista senior" está mencionado pero no secuenciado. ¿En qué semana? ¿Con qué presupuesto? ¿Antes o después del sprint?
- Si el contratista se contrata antes, puede liderar el sprint y mejorar la calidad. Si después, es un parche tardío. La secuencia importa y yo la dejé vaga.

### ¿Qué revela la segunda pasada?

1. **El plan asume datos que pueden no existir.** Sin instrumentación de churn, el sprint quirúrgico es ciego. Necesitas exit interviews antes de cualquier fix.
2. **El coste de oportunidad de no atender a los 3 clientes grandes durante 4 semanas es un riesgo real** que no mapeé. Si esos 3 se van, el plan premium muere.
3. **Falta el rol de producto/ventas.** Ni el CTO ni el CEO pueden hacer el pitch premium. Alguien tiene que vender, y ese alguien no existe en el equipo.
4. **La contratación del senior está mencionada pero no construida** — sin semana, sin presupuesto, sin criterio de éxito.

### ¿Es genuinamente nuevo o repetición?

**Genuinamente nuevo.** Los puntos 1 (datos de churn no verificados), 2 (coste de oportunidad de los 3 clientes grandes) y 3 (rol de ventas ausente) no estaban en la primera pasada. No son reformulaciones — son restricciones reales que el primer análisis dio por resueltas sin construir.

---

## PATRÓN CROSS-CASE

En los 3 casos aparece el mismo patrón: **el sujeto quiere resolver escalando (más sillones, pivot enterprise, salto de carrera) cuando la restricción principal es infrautilización o falta de optimización de lo que ya tiene.**

- El dentista tiene un sillón al 40% vacío y quiere 2 más.
- El startup tiene 47 bugs vaciando clientes y quiere pivotar a un mercado nuevo.
- La abogada tiene 20 años de experiencia corporativa aplicable a medioambiental y quiere tirar todo para empezar de cero.

El patrón constructivo es: **antes de construir nuevo, mide cuánto estás usando de lo que ya construiste.** La respuesta casi nunca es "construir más" — es "usar mejor lo construido" como cimiento del siguiente paso.

---

## SATURACIÓN

**¿Una tercera pasada aportaría algo nuevo?**
Sí, pero con rendimiento decreciente. La segunda pasada en el caso SaaS reveló 3 restricciones genuinamente nuevas (datos de churn, coste de oportunidad de los 3 grandes, rol de ventas). Una tercera pasada probablemente revelaría detalles de implementación (¿cómo exactamente haces las exit interviews? ¿con qué script? ¿quién las ejecuta?) que son útiles operativamente pero ya no cambian la estructura del análisis. La inteligencia constructiva satura más lento que otras porque cada iteración puede encontrar restricciones reales no mapeadas — pero después de 2 pasadas, las restricciones de primer orden están cubiertas.

---

## FIRMA DE LA INTELIGENCIA CONSTRUCTIVA

**¿Qué vio esta inteligencia que probablemente NINGUNA otra vería?**

La inteligencia constructiva ve que en los 3 casos hay capacidad instalada sin usar (sillón vacío, clientes sin upsell, experiencia transferible) y que la solución correcta es un prototipo de bajo coste que maximice lo existente antes de construir nuevo. Ninguna otra inteligencia produce la secuencia concreta: qué se construye primero, qué depende de qué, dónde falla, y cuántas iteraciones necesita.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/CONTEMPLATIVA.md
============================================================

# RESULTADOS F1-18: INT-18 CONTEMPLATIVA

**Fecha:** 2026-03-08
**Inteligencia:** INT-18 — Contemplativa
**Casos:** Clínica Dental, Startup SaaS, Cambio de Carrera

---

## Caso 1: Clínica Dental

### EXTRAER — lo que es

**¿Qué hay aquí, ahora, tal como es — sin interpretación?**
Un hombre de 38 años que pasa la mayor parte de sus horas despierto en una clínica. Tiene dos hijos pequeños que preguntan por él. Tiene una esposa que le dice que no para. Tiene un sillón vacío el 40% del tiempo. Tiene un padre que sufrió un infarto haciendo exactamente lo que él hace. Tiene un banco que le ofrece más deuda. Eso es lo que hay.

**¿Puedes describir la situación sin juzgarla como buena o mala?**
Es un sistema en movimiento perpetuo. No hay crisis: hay inercia con velocidad constante. La clínica funciona, el margen existe, los hijos crecen, el cuerpo aguanta — por ahora. No hay catástrofe. Tampoco hay pausa.

**¿Qué se siente al simplemente estar con esto — sin resolver?**
Incomodidad. La pregunta "¿debería expandir?" es un escape hacia el futuro. Estar con lo que es ahora significa sentir que 60 horas semanales no dejan espacio para estar presente en ningún otro lugar. Que el tercer sillón vacío es un hecho, no un problema. Que la esposa no está pidiendo una solución — está describiendo una ausencia.

**¿Hay prisa real o la urgencia es inventada?**
Inventada. El banco no retira la oferta mañana. Los hijos no dejan de ser pequeños mañana — pero sí dentro de poco. La única urgencia real es biológica: los niños de 4 y 6 años no esperan. Todo lo demás puede esperar.

### CRUZAR — observación × impulso

**¿El impulso de actuar viene de la situación o del miedo a no actuar?**
Del miedo. La situación actual es viable. El impulso de expandir no responde a una necesidad operativa (hay un sillón vacío 40% del tiempo) sino a una narrativa heredada: más es mejor, crecer es seguro, parar es peligroso. El padre tuvo un infarto a los 52 siguiendo esa narrativa. El odontólogo tiene 38 y ya la replica.

**¿Qué pasaría si esperas — no por indecisión, sino por observación?**
Se revelaría que la pregunta no es financiera. Se revelaría que el sillón vacío contiene información: la demanda actual no justifica más capacidad. Se revelaría que la esposa ya dijo lo esencial y no fue escuchada.

**¿Hay sabiduría en la pausa que la acción destruiría?**
Sí. Si firma el crédito, la pausa desaparece. La deuda nueva obliga a producir. Producir obliga a más horas. Más horas destruyen lo que la esposa está señalando. La pausa permitiría ver que el tercer sillón vacío no es un problema sino una puerta: tiempo que podría recuperarse, no llenarse.

**¿El problema necesita resolverse o necesita ser sostenido?**
Sostenido. La tensión entre "quiero crecer" y "no estoy aquí para mis hijos" no se resuelve con más sillones. Resolverla prematuramente (expandiendo o no) evita la pregunta real: ¿para qué trabajo?

### LENTE L1 — Presencia

**¿Estás aquí o estás en el futuro?**
En el futuro. "Si abro sábados y contrato otro dentista, puedo subir a 65.000€/mes." Esa frase es pura proyección. No dice nada sobre hoy. Hoy hay 7.000€ de margen, un sillón vacío, y una familia que lo extraña.

**¿Puedes volver a ahora?**
Ahora hay suficiente dinero. Ahora los hijos tienen 4 y 6 años. Ahora el cuerpo funciona. Cada una de esas cosas es temporal y no renovable.

**¿Qué sabes cuando paras de pensar y simplemente miras?**
Que los 65.000€/mes no van a hacer que los niños dejen de preguntar por él. Que van a hacer que pregunten menos — porque se habrán acostumbrado a su ausencia.

### LENTE L2 — Paradoja

**¿Las dos opciones pueden ser verdad a la vez?**
Sí. Puede ser verdad que expandir sea financieramente racional Y que expandir sea personalmente destructivo. Ambas cosas coexisten sin que una anule la otra.

**¿Puedes sostener la contradicción?**
La contradicción revela que el marco de decisión está incompleto. "¿Debería expandir?" es una pregunta que solo admite sí o no. La paradoja dice: hay una tercera posición que no es ni sí ni no — es "¿por qué esa es la pregunta?"

**¿Qué emerge si no eliges?**
Emerge la pregunta real: ¿qué pasaría si optimizara la clínica actual (llenar ese 40% vacío) y usara el tiempo sobrante para estar presente? Esa opción no existe en el marco binario expandir/no expandir.

### LENTE L3 — Soltar

**¿Qué estás agarrando?**
La identidad de proveedor-constructor heredada del padre. La creencia de que el valor personal se mide en facturación. La narrativa de que parar es fracasar.

**¿Qué pasaría si dejas de controlar?**
Si suelta la necesidad de crecer, descubre que lo que tiene funciona. Que 7.000€ de margen con menos horas es más que 15.000€ con más deuda y más ausencia.

**¿El control es real o ilusión?**
Ilusión. No controla si los hijos van a recordarlo presente o ausente — eso ya se está decidiendo cada día que trabaja 60 horas. No controla si su cuerpo va a aguantar como el de su padre no aguantó.

### LENTE L4 — Vacío

**¿Hay espacio en este sistema?**
No. 60 horas de trabajo, deuda existente, dos hijos pequeños, cero vacaciones en dos años. El sistema está lleno. No hay margen para absorber nada nuevo — ni más sillones, ni más deuda, ni más horas. Paradójicamente, el sillón vacío es el único vacío que queda, y la propuesta es llenarlo.

**¿Qué necesita vaciarse?**
Horas. La agenda necesita vacío — no para producir más, sino para que algo nuevo pueda entrar: presencia con los hijos, descanso, la posibilidad de ver la situación con claridad. Mientras todo esté lleno, toda decisión será reactiva.

### INTEGRAR

La presencia dice: estás en el futuro, no aquí. La paradoja dice: la pregunta está mal formulada. El soltar dice: la identidad de proveedor te ciega. El vacío dice: no hay espacio ni para pensar. Los cuatro apuntan al mismo silencio: **para**.

### ABSTRAER

Sí. Esta es una crisis donde parar es más valiente que actuar. La acción (firmar el crédito, expandir) es fácil — es inercia disfrazada de decisión. La pausa requiere enfrentar lo que hay: un hombre que replica el patrón de su padre mientras su familia le dice que pare.

### FRONTERA

La contemplación aquí no es privilegio — es necesidad médica. El insomnio no declarado pero probable, las 60 horas semanales, la historia familiar de infarto: parar no es lujo filosófico, es prevención. Pero la frontera es real: alguien con 280.000€ de deuda y 7.000€ de margen no tiene infinito tiempo para contemplar.

### RESUMEN (200 palabras)

La inteligencia contemplativa revela que la pregunta "¿debería expandir?" es una huida hacia el futuro que evita estar con lo que hay ahora. Lo que hay: un sillón vacío el 40% del tiempo (la demanda no justifica más capacidad), una familia que describe una ausencia, y un patrón heredado del padre — mismo ritmo de trabajo, misma narrativa de crecimiento — que terminó en infarto a los 52. El impulso de expandir no nace de la situación sino del miedo a parar. La pausa revelaría que la pregunta real no es financiera sino existencial: ¿para qué trabajo? La paradoja muestra que expandir puede ser racional y destructivo a la vez, y que existe una tercera opción invisible en el marco binario: optimizar lo existente y recuperar tiempo. El sistema está completamente lleno — cero vacío, cero vacaciones, cero margen temporal — y la propuesta es llenarlo más. Los cuatro ejes contemplativos (presencia, paradoja, soltar, vacío) convergen en una sola señal: para. No por indecisión, sino porque la inercia disfrazada de expansión es la opción más peligrosa disponible.

**Firma:** La expansión es inercia disfrazada de decisión. El sillón vacío es el último espacio libre en un sistema sin margen — y la propuesta es llenarlo.

---

## Caso 2: Startup SaaS

### EXTRAER — lo que es

**¿Qué hay aquí, ahora, tal como es — sin interpretación?**
Dos personas que apenas se hablan. Un producto con 47 bugs. 80 clientes de los cuales 8 se van cada mes. 7 meses de dinero. Un equipo de juniors sin líder técnico senior. Un ex-cofundador que ya se fue. Eso es lo que hay — sin la narrativa de "pivotar" o "estabilizar" que cada fundador superpone a los mismos hechos.

**¿Puedes describir la situación sin juzgarla como buena o mala?**
Es un organismo perdiendo energía más rápido de la que genera. No es bueno ni malo — es un estado. El churn es 8%, el burn es 28.000€, el runway es 7 meses. Son números que describen un ritmo de agotamiento. El organismo sigue vivo. Pero no está sano.

**¿Qué se siente al simplemente estar con esto — sin resolver?**
Angustia. Porque "sin resolver" aquí parece significar "morir". Pero la angustia misma es información: dice que ambos fundadores están actuando desde el pánico, no desde la observación. El CEO quiere pivotar por miedo. El CTO quiere estabilizar por miedo. Ambos impulsos son reactivos.

**¿Hay prisa real o la urgencia es inventada?**
Mixta. 7 meses de runway es una restricción real — no inventada. Pero la urgencia de elegir entre "pivotar" y "estabilizar" ahora mismo sí es inventada: esa dicotomía asume que son mutuamente excluyentes y que hay que comprometerse con una antes de entender qué está pasando realmente.

### CRUZAR — observación × impulso

**¿El impulso de actuar viene de la situación o del miedo a no actuar?**
Del miedo. La situación dice: el producto pierde clientes por calidad. Eso es un hecho observable. El impulso del CEO de pivotar a enterprise no responde a ese hecho — responde al miedo de que el mercado actual no sea suficiente. El impulso del CTO de estabilizar responde parcialmente al hecho, pero también al miedo de que cualquier cambio destruya lo poco que funciona.

**¿Qué pasaría si esperas?**
Si ambos se sentaran juntos — no para defender posiciones sino para observar los datos sin narrativa — verían que el 30% de ingresos viene de 3 clientes que piden features custom. Eso no es una señal de pivotar a enterprise. Es una señal de que unos pocos clientes tienen necesidades que el producto no cubre. Observar eso sin reaccionar podría revelar un camino que ni "pivotar" ni "estabilizar" describe.

**¿Hay sabiduría en la pausa?**
Sí. La pausa revelaría que CTO y CEO están teniendo dos monólogos sobre dos problemas distintos sin escucharse. La ruptura de comunicación es más urgente que la decisión técnica. Ninguna decisión técnica funciona si las dos personas que la ejecutan no se hablan.

**¿El problema necesita resolverse o necesita ser sostenido?**
La tensión pivotar/estabilizar necesita ser sostenida el tiempo suficiente para que se revele lo que ambas posiciones comparten: pánico. Lo que necesita resolverse no es la dirección del producto sino la relación entre los fundadores.

### LENTE L1 — Presencia

**¿Estás aquí o en el futuro?**
Ambos están en el futuro. El CEO vive en "enterprise nos salva". El CTO vive en "si estabilizamos, el churn baja solo". Ninguno está en el presente: el presente es un producto roto, un equipo sin dirección, y una relación fundacional destruida.

**¿Puedes volver a ahora?**
Ahora hay 47 bugs. Ahora hay 80 clientes, y cada mes se van 6-7. Ahora hay 3 juniors sin guía técnica senior. Ahora hay dos personas que dirigen una empresa y no se hablan fuera de reuniones formales. Eso es ahora.

**¿Qué sabes cuando simplemente miras?**
Que ni pivotar ni estabilizar funcionan si las personas que ejecutan no están alineadas. Que la pregunta técnica es secundaria a la pregunta relacional.

### LENTE L2 — Paradoja

**¿Las dos opciones pueden ser verdad a la vez?**
Sí. El CTO tiene razón: el producto necesita estabilizarse porque los clientes se van por calidad. El CEO tiene razón: el mercado de restaurantes pequeños tiene un techo bajo. Ambas cosas son verdad simultáneamente. La paradoja no se resuelve eligiendo uno — se resuelve (o más bien se disuelve) cuando se ve que estabilizar para los clientes grandes ES el movimiento hacia enterprise, sin necesidad de pivotar.

**¿Qué emerge si no eliges?**
Emerge que los 3 clientes grandes que representan el 30% de los ingresos ya están pidiendo lo que el CEO llama "enterprise". Estabilizar el producto y construir lo que esos clientes piden no es pivotar — es escuchar. La tensión artificial se disuelve.

### LENTE L3 — Soltar

**¿Qué estás agarrando?**
El CTO agarra la visión original del producto — "si fuera sólido, todo se arreglaría." El CEO agarra la fantasía de escape — "enterprise nos salva." Ambos agarran la posición que les da razón. Lo que necesitan soltar es la necesidad de tener razón.

**¿Qué pasaría si dejas de controlar?**
Si el CTO suelta la necesidad de que el producto sea perfecto antes de evolucionar, y el CEO suelta la necesidad de que el mercado cambie antes de arreglar lo roto, ambos podrían ver que el camino es uno solo: arreglar lo que se rompe mientras se construye lo que los clientes grandes piden.

**¿El control es real o ilusión?**
Ilusión. Ninguno controla el churn, el runway, ni la decisión del otro. Cada uno intenta controlar la dirección de la empresa sin controlar primero la conversación entre ellos.

### LENTE L4 — Vacío

**¿Hay espacio en este sistema?**
No. 70 horas semanales del CTO. 47 bugs. 7 meses de runway. Equipo junior sin senior. CEO y CTO sin canal de comunicación real. El sistema está saturado de urgencia, deuda técnica y silencio relacional. No hay espacio ni para pensar, mucho menos para pivotar.

**¿Qué necesita vaciarse?**
La agenda del CTO necesita vacío para pensar estratégicamente, no solo apagar fuegos. La relación CTO-CEO necesita vaciar las posiciones fijas para crear espacio para una conversación real. El backlog necesita vaciar bugs antes de poder absorber features nuevas.

### INTEGRAR

La presencia dice: ambos están en sus fantasías de futuro, no en el presente roto. La paradoja dice: las dos posiciones son verdad simultáneamente y la tensión es artificial. El soltar dice: ambos agarran la necesidad de tener razón. El vacío dice: no hay espacio para nada nuevo. Los cuatro apuntan al mismo silencio: **habla con tu socio. Antes de decidir qué construir, reconstruye la relación que construye.**

### ABSTRAER

Sí. Esta crisis tiene un momento donde parar de debatir pivotar vs. estabilizar y simplemente estar con los datos — sin narrativa defensiva — es más valiente que cualquier acción técnica.

### FRONTERA

La contemplación aquí tiene un límite duro: 7 meses de runway. No hay infinito tiempo para sostener paradojas. Pero incluso con 7 meses, dedicar una semana a una conversación real entre fundadores no es lujo contemplativo — es la inversión más rentable posible. El privilegio de esperar es limitado; la necesidad de parar un momento para ver es absoluta.

### RESUMEN (200 palabras)

La inteligencia contemplativa revela que el debate pivotar-vs-estabilizar es una capa superficial que oculta el problema real: dos fundadores que no se hablan. Ambos actúan desde el pánico — el CEO hacia una fantasía enterprise, el CTO hacia una fantasía de producto perfecto — y ninguno está presente en lo que hay: 47 bugs, 8% de churn, un equipo sin guía, y una relación rota. La paradoja central es que ambos tienen razón simultáneamente: el producto necesita estabilizarse Y el mercado actual tiene techo. Pero la paradoja se disuelve al observar que los 3 clientes grandes que generan 30% de ingresos ya están pidiendo evolución — estabilizar para ellos ES el movimiento enterprise, sin pivotar. Lo que ambos agarran es la necesidad de tener razón. Lo que necesitan soltar es exactamente eso. El sistema no tiene vacío: ni tiempo, ni espacio técnico, ni canal relacional. Los cuatro ejes contemplativos convergen en una prescripción: antes de decidir qué construir, reconstruir la conversación entre quienes construyen. Con 7 meses de runway, una semana de pausa para alinear no es lujo — es supervivencia.

**Firma:** El debate pivotar-vs-estabilizar es ruido. El silencio real está entre los dos fundadores que no se hablan — y hasta que ese silencio se rompa, ninguna dirección técnica funciona.

---

## Caso 3: Cambio de Carrera

### EXTRAER — lo que es

**¿Qué hay aquí, ahora, tal como es — sin interpretación?**
Una mujer de 45 años que no duerme bien desde hace 2 años. Que lleva 3 años pensando en un cambio. Que no ha hablado en profundidad con su marido. Que tiene 120.000€ ahorrados. Que fue rechazada para socia. Que dice dos frases contradictorias: "Si no lo hago ahora, no lo haré nunca" y "No puedo arriesgar la estabilidad de mis hijos." Eso es lo que hay.

**¿Puedes describir la situación sin juzgarla como buena o mala?**
Es una persona en una posición estable que experimenta sufrimiento. La estabilidad es real: 180.000€/año, hipoteca pagable, ahorros. El sufrimiento también es real: insomnio de 2 años, pasión perdida, rechazo profesional. No es bueno ni malo — es una tensión que lleva 3 años sin resolverse y que el cuerpo ya está manifestando.

**¿Qué se siente al simplemente estar con esto — sin resolver?**
Exactamente lo que ella siente: insomnio. Estar con esta tensión sin resolverla es insoportable — por eso lleva 3 años pensando y no actuando. El cuerpo está haciendo lo que la mente no puede: gritar que algo está mal. Simplemente estar con esto es doloroso, y ese dolor es información.

**¿Hay prisa real o la urgencia es inventada?**
Mixta. "Si no lo hago ahora, no lo haré nunca" es urgencia parcialmente inventada — siempre podrá hacerlo mientras esté viva y sana. Pero la urgencia del insomnio de 2 años es real: el cuerpo tiene un plazo que la mente ignora. Y la ventana de 2 años antes de que el hijo mayor entre en la universidad es una restricción real de planificación.

### CRUZAR — observación × impulso

**¿El impulso de actuar viene de la situación o del miedo a no actuar?**
De ambos, pero sobre todo del miedo acumulado. Tres años pensando es mucho tiempo de no actuar. El impulso ya no es fresco — está cargado de culpa por no haber actuado antes, de miedo a que pase más tiempo, y del dolor del insomnio. La situación (rechazo para socia, pérdida de pasión) es real, pero el impulso está amplificado por la acumulación temporal.

**¿Qué pasaría si esperas?**
Si espera con intención — no por parálisis sino por observación — pasaría algo específico: hablaría con su marido. Tres años pensando sin hablar con la persona más afectada es la señal más clara de que el acto contemplativo necesario no es decidir sino conversar.

**¿Hay sabiduría en la pausa?**
Sí, pero de un tipo particular: la sabiduría de la pausa aquí no es "no actúes" sino "actúa en lo que llevas evitando". Lo que lleva evitando no es el cambio de carrera — es la conversación con su marido.

**¿El problema necesita resolverse o necesita ser sostenido?**
Necesita resolverse — pero no la decisión carrera, sino el silencio. Tres años de deliberación interna sin conversación externa no es contemplación: es aislamiento. El problema que necesita resolverse es el silencio con su marido. La decisión de carrera puede emerger después.

### LENTE L1 — Presencia

**¿Estás aquí o en el futuro?**
En el futuro. Vive en dos futuros simultáneos: "la abogada que por fin cambió y es feliz" (como su amiga) y "la madre que arriesgó la estabilidad de sus hijos". Ninguno de esos futuros existe. Lo que existe ahora: una mujer con insomnio que no ha hablado con su marido.

**¿Puedes volver a ahora?**
Ahora tiene 120.000€ ahorrados — es un colchón real. Ahora su marido gana entre 40-80K — no es cero. Ahora sus hijos tienen 14 y 16 — ya no son bebés que dependen totalmente de ella. Ahora el médico ya le dijo que es estrés laboral. El presente tiene más recursos de los que ella registra desde su miedo.

**¿Qué sabes cuando simplemente miras?**
Que el insomnio de 2 años ya es la respuesta. El cuerpo ya decidió. Lo que falta no es información — es permiso.

### LENTE L2 — Paradoja

**¿Las dos opciones pueden ser verdad a la vez?**
Sí. "Si no lo hago ahora, no lo haré nunca" Y "No puedo arriesgar la estabilidad de mis hijos" pueden ser ambas verdad. La paradoja es que ella misma las sostiene simultáneamente — lo que revela que no son opciones que se excluyen, sino miedos que se complementan.

**¿Puedes sostener la contradicción?**
Sí, y al sostenerla se ve que ambas frases son sobre lo mismo: miedo a perder. Miedo a perder la oportunidad. Miedo a perder la seguridad. El denominador común no es la decisión — es el miedo a la pérdida.

**¿Qué emerge si no eliges?**
Emerge que la decisión no es binaria. Hay transiciones: reducción gradual de jornada, trabajo pro bono en derecho medioambiental los fines de semana, un año sabático parcial. Pero ninguna de esas opciones puede siquiera considerarse mientras no haya una conversación con el marido. La paradoja no se resuelve eligiendo — se resuelve hablando.

### LENTE L3 — Soltar

**¿Qué estás agarrando?**
Tres cosas: la identidad de "abogada exitosa" (20 años construida), la necesidad de decidir sola (no ha hablado con el marido), y la ilusión de control sobre el futuro de sus hijos (que tienen 14 y 16 años y pronto decidirán solos).

**¿Qué pasaría si dejas de controlar?**
Si suelta la necesidad de tener la respuesta perfecta antes de hablar, la conversación con su marido podría revelar opciones que no puede ver sola. Quizá él la apoya. Quizá él tiene miedo pero lo acepta. Quizá él tiene una perspectiva que ella lleva 3 años evitando escuchar.

**¿El control es real o ilusión?**
Ilusión. No controla si la van a hacer socia ("quizá el próximo ciclo" es un quizá). No controla los ingresos del marido. No controla si sus hijos valoran más su presencia emocional o su salario. Controlar el proceso de decisión en solitario es la mayor ilusión.

### LENTE L4 — Vacío

**¿Hay espacio en este sistema?**
Paradójicamente, más que en los otros dos casos. Tiene 120.000€ de colchón. Tiene hijos ya mayores. Tiene un marido que genera ingresos. El espacio financiero y vital existe — pero está lleno de la narrativa de "no puedo arriesgar". El vacío material existe; el vacío mental no.

**¿Qué necesita vaciarse?**
La deliberación solitaria de 3 años necesita vaciarse. Las voces de los padres ("estás loca") necesitan vaciarse. La comparación con la amiga necesita vaciarse. Todo lo que ocupa espacio mental sin producir movimiento necesita salir para que algo nuevo entre: una conversación real con su marido, un plan concreto, o simplemente la aceptación de que ya decidió y solo necesita permiso para ejecutar.

### INTEGRAR

La presencia dice: el insomnio es la respuesta — el cuerpo ya decidió. La paradoja dice: las dos frases contradictorias son el mismo miedo. El soltar dice: lo que agarra no es la decisión sino la necesidad de decidir sola. El vacío dice: hay más espacio del que percibe, pero está lleno de narrativas ajenas. Los cuatro apuntan al mismo silencio: **habla con tu marido. Lo que llevas 3 años deliberando sola en tu cabeza necesita salir al aire.**

### ABSTRAER

Sí. Aquí parar de deliberar internamente es más valiente que seguir pensando. Tres años de reflexión solitaria no son contemplación — son evitación de la acción que realmente asusta: compartir la verdad con quien más importa.

### FRONTERA

La contemplación aquí tiene una frontera médica: 2 años de insomnio. El cuerpo no puede sostener más deliberación. Pero la frontera del "privilegio" se invierte: esta persona sí puede permitirse esperar económicamente (120.000€, marido con ingresos) — lo que no puede permitirse es seguir en silencio. La contemplación es sabiduría si lleva a hablar; es evasión si sigue siendo monólogo interior.

### RESUMEN (200 palabras)

La inteligencia contemplativa revela que 3 años de deliberación solitaria no son contemplación — son evitación. Lo que la abogada evita no es la decisión de carrera sino la conversación con su marido. El insomnio de 2 años es el cuerpo diciendo lo que la mente no puede articular: ya decidió, solo necesita permiso. Las dos frases contradictorias ("si no lo hago ahora, nunca" y "no puedo arriesgar la estabilidad") no son opciones opuestas — son el mismo miedo a perder, visto desde dos ángulos. La paradoja se disuelve cuando se observa que la decisión no es binaria: hay transiciones posibles (reducción gradual, pro bono, año sabático parcial), pero ninguna puede considerarse sin hablar primero con la pareja. Paradójicamente, esta persona tiene más vacío material que los otros dos casos (120.000€ ahorrados, hijos mayores, marido con ingresos), pero el espacio mental está saturado de voces ajenas y deliberación circular. Los cuatro ejes convergen: lo que necesita no es más pensamiento sino menos silencio. Contemplar aquí significa dejar de contemplar sola y traer la verdad a la relación que más importa. El cuerpo ya no puede esperar.

**Firma:** Tres años pensando no es contemplación — es evitación. El acto contemplativo real no es seguir deliberando sino romper el silencio con quien más importa.

---

## Loop Test (P06)

**Caso elegido:** Cambio de carrera (análisis más profundo — la paradoja de que la contemplación excesiva se revela como evitación es el hallazgo más genuinamente contemplativo).

### Segunda pasada: INT-18 aplicada al propio output del Caso 3

**EXTRAER — ¿Qué hay en mi output, tal como es?**
Hay un análisis que repite con variaciones una misma tesis: "habla con tu marido." Cada bloque llega a la misma conclusión por un camino distinto. Hay una afirmación fuerte ("el cuerpo ya decidió") que no se cuestiona. Hay una asunción de que la conversación evitada es el problema primario.

**CRUZAR — ¿El impulso de mi análisis viene de la situación o de mi propia inercia analítica?**
Parcialmente de la inercia. La lente contemplativa tiende naturalmente a señalar lo que se evita, y encontró una evitación obvia (la conversación). Pero al hacerlo, mi análisis hizo algo que la contemplación supuestamente critica: se apresuró a una respuesta. "Habla con tu marido" es una prescripción — y la contemplación pura no prescribe.

**L2 — Paradoja del propio análisis:**
Mi output dice "3 años pensando no es contemplación — es evitación." Pero ¿y si sí es contemplación? ¿Y si esos 3 años de incubación silenciosa son necesarios para que la decisión madure? Mi análisis juzgó el proceso de deliberación como patológico, pero la contemplación genuina debería poder sostener la posibilidad de que la espera tiene su propia sabiduría.

**L3 — ¿Qué agarra mi análisis?**
Agarra la certeza de que sabe cuál es el problema real. "El problema no es la decisión de carrera, es el silencio con el marido." Esa afirmación tiene un tono de verdad revelada que una segunda pasada contemplativa debería cuestionar: ¿y si el silencio con el marido es un síntoma, no la causa? ¿Y si ella no habla con él porque aún no sabe qué quiere, y necesita más tiempo sola — no menos?

**L4 — ¿Hay espacio en mi análisis?**
No mucho. Cada bloque converge en la misma respuesta. No hay espacio para la posibilidad de que ella esté haciendo exactamente lo que necesita hacer: esperar. Mi análisis llenó todo el espacio con una prescripción y no dejó vacío para lo que no vi.

**¿Qué revela la segunda pasada?**
Que la primera pasada fue prescriptiva donde debía ser contemplativa. Identificó una evitación real pero la convirtió en diagnóstico cerrado. La contemplación genuina habría sostenido dos posibilidades: que el silencio es evitación Y que el silencio es incubación necesaria. La primera pasada eligió una y descartó la otra — exactamente lo que la lente de paradoja (L2) dice que no se debe hacer.

**¿Es genuinamente nuevo?**
Sí. La primera pasada prescribió; la segunda reveló que prescribir viola la propia lógica contemplativa. Esto es no-idempotente.

---

## Patrón Cross-Case

En los 3 casos, la lente contemplativa disuelve la pregunta binaria formulada para revelar una acción previa más simple y más aterradora que el sujeto está evitando:

- **Clínica:** "¿expandir?" oculta → "para y mira lo que tienes"
- **Startup:** "¿pivotar o estabilizar?" oculta → "habla con tu socio"
- **Carrera:** "¿dejar o quedarse?" oculta → "habla con tu marido"

La "decisión difícil" es siempre una cortina que tapa algo más simple y más aterrador.

---

## Saturación

**¿Una tercera pasada aportaría algo nuevo?**
Posiblemente sí en el caso 3, donde el loop test reveló que la primera pasada fue prescriptiva. Una tercera pasada podría explorar la paradoja meta-contemplativa: ¿es posible usar la contemplación sin que se convierta en otra forma de prescripción? Para los otros dos casos, la saturación es alta.

---

## Firma Global INT-18

**¿Qué vio esta inteligencia que probablemente NINGUNA otra vería?**
Que en los tres casos la "decisión difícil" es una cortina que oculta un acto más simple y más aterrador que la persona está evitando. La contemplativa no resuelve el dilema — lo disuelve al revelar que la verdadera pregunta no es la que se formula.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/DIVERGENTE.md
============================================================

# F1-14: INT-14 — DIVERGENTE

## Caso 1: Clínica Dental

### EXTRAER — abrir posibilidades

El odontólogo ve dos opciones: expandir (5 sillones + sábados + nuevo dentista) o quedarse como está. Existen al menos 15 más. Descartó sin examinar: vender la clínica, asociarse con otro propietario, convertir la clínica en una franquicia, reducir horas y subir precios, especializarse en un nicho de alto valor (implantología, estética dental), crear un modelo de suscripción dental, contratar un gerente y retirarse a rol clínico parcial, alquilar los sillones vacíos a especialistas externos, digitalizar y crear un brazo de teleodontología para triaje, montar una segunda clínica con otro socio operador, cambiar el modelo a preventivo con cuotas mensuales, hacer del asociado un socio con skin in the game, negociar la hipoteca a la baja, diversificar a formación dental, o simplemente reducir la clínica a 2 sillones y trabajar 40 horas.

Descartó la mayoría por un marco mental binario: "crecer o estancarme." La restricción más obvia es el tiempo — él trabaja 60h/semana. Si esa restricción no existiera (porque contrata un gerente o cede control), el espacio de opciones explota. Alguien completamente diferente — un inversor inmobiliario, por ejemplo — vería la clínica como un activo generador de renta y buscaría maximizar el rendimiento por metro cuadrado sin estar presente. Con el doble de recursos, montaría una red de clínicas con gerentes operativos y él como director médico. Con la mitad, cerraría el tercer sillón, despediría al asociado, y montaría una consulta boutique premium.

### CRUZAR — opciones × restricciones

Las restricciones declaradas: hipoteca (real), tiempo (real pero autoimpuesta en su magnitud), familia (real), capacidad ociosa del tercer sillón (real). Pero varias son asumidas: que él DEBE estar en la clínica todas las horas que opera, que el asociado es empleado y no potencial socio, que los precios son fijos, que el mercado local no admite segmentación, que la única forma de crecer es más sillones.

Opciones "locas" que son viables: alquilar el tercer sillón a un ortodoncista freelance por horas (ingreso inmediato, cero inversión, cero riesgo). Ofrecer un programa de "dentista personal" premium a 500€/año con acceso prioritario y revisiones ilimitadas — si captura 100 pacientes, son 50.000€ adicionales. Hacer del sábado un día de clínica estética dental (blanqueamiento, carillas) operado exclusivamente por el asociado con un porcentaje de la facturación.

Combinación de dos opciones "incompatibles": expandir Y trabajar menos. Es posible si la expansión no es de su tiempo sino de la capacidad del negocio: alquilar sillones a externos + convertir al asociado en socio con autonomía + contratar un gerente a media jornada. Él reduce a 35-40 horas y la clínica factura más.

La opción que nadie menciona: que el tercer sillón vacío al 40% es el mayor activo de la clínica, no su mayor problema. Es espacio libre que puede monetizarse de 10 formas distintas sin inversión adicional.

### LENTE L1 — Volumen

10 opciones sin filtrar: (1) Alquilar sillón vacío a especialistas por horas. (2) Subir precios un 20% y aceptar perder el 10% de pacientes de menor valor. (3) Hacer del asociado un socio al 30%. (4) Crear "club dental" con cuota mensual. (5) Vender la clínica y trabajar como empleado en otra. (6) Contratar un gerente y reducir horas clínicas. (7) Montar formación online para dentistas sobre gestión de clínica. (8) Asociarse con una aseguradora para volumen garantizado. (9) Abrir solo mañanas e invertir tardes en un segundo negocio. (10) Meter un higienista dental que haga limpiezas a bajo coste en el sillón vacío, liberándole a él para procedimientos de alto valor.

10 opuestas: (1) Cerrar el sillón vacío y reducir costes fijos. (2) Bajar precios drásticamente y captar volumen. (3) Despedir al asociado y trabajar solo. (4) Eliminar cuotas y cobrar solo por procedimiento. (5) Comprar la clínica a un precio inflado (para un inversor). (6) Ser el gerente y dejar de ejercer. (7) Dejar de enseñar y solo operar. (8) Rechazar aseguradoras y ser 100% privado. (9) Trabajar 12 horas al día sin pausa. (10) Delegar todas las limpiezas al higienista y no ver pacientes de bajo margen.

Lo que tienen en común las que gustan: todas separan el trabajo clínico del propietario de la generación de ingresos del negocio. Eso revela que la trampa central es la fusión de roles: él es clínico + gerente + propietario + comercial, y el crecimiento real pasa por desacoplar esos roles.

### LENTE L2 — Combinación

Mezclar opción A (alquilar sillón) con C (hacer del asociado un socio): el asociado se convierte en socio-director clínico, opera la clínica con los freelancers que alquilan sillones, y el odontólogo reduce presencia a 3 días/semana enfocado en casos complejos de alto valor. La clínica pasa de ser "su trabajo" a ser "su inversión con participación clínica."

Solución de otro dominio: el modelo WeWork aplicado a odontología — espacios clínicos compartidos donde varios profesionales alquilan por horas/días. Existe ya en coworking médico en algunas ciudades.

¿Qué haría un niño? "¿Por qué no le dices a otro dentista que trabaje mientras tú juegas con tus hijos?" — la simplificación radical del modelo de delegación. ¿Un artista? Rediseñaría la experiencia del paciente para que pague más por menos tiempo — la clínica como experiencia, no como servicio. ¿Un alien? No entendería por qué el humano intercambia su tiempo finito por unidades monetarias cuando podría diseñar un sistema que genere las unidades sin su presencia.

### LENTE L3 — Inversión

Hacer exactamente lo opuesto: en lugar de expandir, contraer. Cerrar a 2 sillones, trabajar 4 días/semana, subir precios un 40%, aceptar solo pacientes de alto valor. Facturación baja pero margen neto sube y tiempo recuperado es masivo.

¿Y si el problema es la solución? Él dice "necesito crecer para ganar más." ¿Y si el crecimiento ES el problema? Cada expansión previa ha comprado más ingresos a cambio de más esclavitud. El patrón se repite. Crecer otra vez es repetir el patrón, no resolverlo.

En lugar de resolver, ampliar: ¿Qué pasa si en vez de decidir expandir/no expandir, abre el problema a toda la familia? "Familia, tenemos X opciones, nos afecta a todos, ¿qué priorizamos?" Eso transforma un dilema individual en una decisión colectiva con buy-in de la esposa.

### LENTE L4 — Restricción creativa

Si SOLO pudiera hacer UNA cosa: alquilar el sillón vacío a un especialista externo. Cero inversión, ingreso inmediato, prueba de concepto de que la clínica puede generar sin su presencia.

En 24 horas: llamar a 3 ortodoncistas/periodoncistas de la zona y ofrecerles el sillón por tardes. Podría tener un acuerdo verbal antes de mañana.

Sin dinero: intercambiar horas de sillón por servicios — un fisioterapeuta que trate su posible dolor de espalda, un coach que le ayude con gestión del tiempo, un contable que optimice su fiscalidad. El sillón vacío es la moneda.

### INTEGRAR

Las opciones que aparecen desde múltiples lentes: (1) Alquilar el sillón vacío (aparece en Volumen, Combinación, Restricción creativa, Inversión). (2) Separar rol de propietario del rol clínico (aparece en Volumen, Combinación, Inversión). (3) Involucrar a la familia en la decisión (aparece en Inversión, Combinación). (4) Subir precios y segmentar (aparece en Volumen, Inversión, Restricción creativa).

### ABSTRAER

Las mejores opciones comparten una estructura: todas desacoplan la generación de valor de la presencia física del propietario. El patrón es: "tu activo más valioso no es tu tiempo clínico, es tu infraestructura + tu base de pacientes + tu reputación; monetiza ESO, no tus horas."

### FRONTERA

Generar opciones aquí es genuinamente avanzar. El odontólogo está atrapado en un marco binario (expandir/no expandir) que le impide ver el espacio real de posibilidades. Sin embargo, hay un riesgo: que la generación excesiva de opciones se convierta en parálisis. La inteligencia divergente abre puertas pero no dice cuál cruzar. Necesita a la lógico-matemática o la estratégica para filtrar.

### RESUMEN (200 palabras)

El odontólogo ve 2 opciones; existen al menos 20. Su trampa central es la fusión de roles: es clínico, gerente, propietario y comercial simultáneamente, y confunde "trabajar más" con "crecer." El tercer sillón vacío al 40% no es un problema — es su mayor activo no explotado. Alquilarlo a especialistas externos genera ingresos sin inversión, sin deuda y sin horas adicionales de su parte. La estructura común de las mejores opciones es desacoplar la generación de ingresos de su presencia física: convertir al asociado en socio con autonomía, alquilar infraestructura ociosa, segmentar hacia alto valor. La combinación más potente: asociado como socio-director + sillón alquilado a freelancers + él reducido a 3 días en casos complejos. Factura igual o más, trabaja la mitad. La inversión radical (contraer en vez de expandir, subir precios, aceptar menos pacientes) también merece examen serio: puede que menos sea genuinamente más. El patrón de su padre (infarto a los 52 por sobretrabajar) no es contexto — es la restricción más real de todas, y la única que no admite "ya lo veré después." Generar opciones aquí es avanzar; pero elegir es lo que sigue.

---

## Caso 2: Startup SaaS

### EXTRAER — abrir posibilidades

El CTO ve dos opciones: estabilizar el producto (arreglar los 47 bugs) o pivotar a enterprise. El CEO ve las mismas dos. Existen muchas más. Opciones descartadas sin examinar: cerrar la empresa y buscar acqui-hire, vender la base de clientes a un competidor, fusionarse con otro SaaS complementario, convertir el producto en open-source con soporte de pago, licenciar la tecnología a una empresa grande, hacer un "acqui-hire inverso" (contratar un equipo senior que traiga experiencia enterprise), pivotar a un vertical adyacente dentro de restauración (delivery, reservas), convertir a los 3 clientes grandes en socios estratégicos con equity, reducir burn a la mitad despidiendo y haciendo él todo el desarrollo, buscar revenue-based financing en vez de Serie A, crear una API y ser infraestructura para otros SaaS de restauración, montar un servicio de consultoría sobre gestión de inventario financiado por el producto.

Descartaron la mayoría porque el marco CTO-vs-CEO reduce todo a una lucha de poder disfrazada de decisión técnica. La restricción más obvia es el runway de 7 meses. Si no existiera (fondos ilimitados), ¿qué harían? Probablemente ambas cosas: estabilizar Y explorar enterprise, porque no son incompatibles con tiempo suficiente. Alguien completamente diferente — un operador de restaurante — diría: "¿Por qué no me preguntáis qué necesito de verdad?" Con el doble de recursos, contratarían un VP Engineering senior que resuelva la deuda técnica mientras el CTO explora enterprise. Con la mitad, el CTO despide a los 3 juniors, se queda solo, arregla los bugs críticos (no los 47, los 10 que causan churn) y el CEO vende como loco.

### CRUZAR — opciones × restricciones

Restricciones reales: runway 7 meses (real), churn 8% (real), relación CTO-CEO rota (real), equipo junior (real). Restricciones asumidas: que pivotar a enterprise y estabilizar son mutuamente excluyentes (no lo son si priorizas correctamente), que necesitan Serie A para sobrevivir (el bridge, el revenue-based financing y la reducción de burn son alternativas), que los 3 devs junior son el equipo correcto (quizá 1 senior reemplaza a los 3), que los 80 clientes son su mercado (quizá los 3 grandes son el mercado real).

Opciones "locas" pero viables: cobrar a los 3 clientes grandes por las features custom que pidieron — no como SaaS, como desarrollo a medida, y usar ese cash para financiar la estabilización. Si cada uno paga 15-20K€ por desarrollo, son 45-60K€ que compran 2 meses extra de runway sin diluirse. Otra: proponer a los 3 clientes grandes que inviertan en la empresa a cambio de prioridad en roadmap — customer-funded development.

Combinar dos opciones incompatibles: estabilizar Y pivotar, pero secuenciado radicalmente. Semanas 1-4: el CTO cierra los 10 bugs que causan más churn (no los 47). Semanas 5-12: con churn estabilizado, el CEO va a los 3 grandes con una propuesta enterprise. No es ni una cosa ni la otra: es las dos, priorizadas por impacto en supervivencia.

La opción que nadie menciona: la relación CTO-CEO es el bug #1. Si eso no se arregla, ni estabilizar ni pivotar funcionará. La opción obvia-pero-no es: antes de cualquier decisión de producto, 2 días de retiro CTO+CEO para alinear visión o acordar separarse.

### LENTE L1 — Volumen

10 opciones sin filtrar: (1) Cobrar a clientes grandes por features custom. (2) Buscar acqui-hire por otra startup. (3) Convertir producto en open-source + soporte pago. (4) Pivotar a vertical adyacente (delivery). (5) Reducir equipo a CTO solo + 1 senior. (6) Revenue-based financing. (7) Crear API de inventario para otros SaaS. (8) Fusionarse con competidor. (9) Vender base de clientes. (10) Hacer consultoría de gestión de inventario facturada por horas.

10 opuestas: (1) Regalar features custom. (2) Rechazar toda adquisición. (3) Cerrar código aún más. (4) Quedarse exactamente en el vertical. (5) Contratar 5 devs más. (6) Buscar solo equity VC. (7) Eliminar la API y ser monolito. (8) Competir agresivamente contra todos. (9) No vender nada, regalar cuentas. (10) Nunca facturar por horas, solo SaaS.

Lo que tienen en común las que gustan: todas usan lo que YA tienen (clientes, producto, conocimiento de dominio) de formas que no requieren capital externo. Eso revela que el verdadero problema no es "necesitamos dinero" sino "no estamos monetizando lo que ya tenemos."

### LENTE L2 — Combinación

Mezclar "cobrar features custom" con "API para otros SaaS": construir las features custom de los 3 grandes como módulos reutilizables que luego se vendan como API a otros SaaS de restauración. Los grandes financian el desarrollo, la API genera ingresos recurrentes después. Un producto se convierte en plataforma financiada por sus propios clientes.

Solución de otro dominio: el modelo de videojuegos — early access. Ofrecer el producto enterprise como "beta enterprise" a precio reducido, con el compromiso de que los clientes beta co-diseñan el producto. Reduce coste de desarrollo, aumenta retención, genera compromiso.

¿Qué haría un niño? "Pregúntale a los que se van por qué se van y haz lo que dicen." Radical por simple. ¿Un artista? Rediseñaría la experiencia del producto para que los restaurantes no puedan dejarlo — hacer que sea tan parte de su operación diaria que desinstalarlo sea impensable. ¿Un alien? "¿Por qué compiten dos humanos dentro de la misma unidad? ¿No sería más eficiente que el que tiene razón mande y el otro obedezca o se vaya?"

### LENTE L3 — Inversión

Hacer lo opuesto: en vez de retener clientes que se van, dejar de intentar retenerlos. Centrarse exclusivamente en los que se quedan, entender por qué se quedan, y buscar más de esos. El churn del 8% quizá no es un problema de bugs — es un problema de product-market fit para un segmento. Dejar ir a los que no encajan libera recursos para servir mejor a los que sí.

¿Y si el problema es la solución? "Estabilizar el producto" suena como la solución, pero ¿y si la inestabilidad ES el síntoma de que el producto intenta ser todo para todos? Los 47 bugs quizá son 47 señales de que el producto necesita menos features, no más arreglos.

Ampliar en vez de resolver: en lugar de elegir estabilizar o pivotar, abrir la conversación a los 80 clientes. "Estamos en una encrucijada. ¿Qué valor os damos que no encontráis en otro sitio? ¿Qué os sobra?" Convertir la crisis en co-creación.

### LENTE L4 — Restricción creativa

Si SOLO pudiera hacer UNA cosa: arreglar los 5 bugs que causan más cancelaciones. No los 47. Los 5 que matan. Máximo impacto, mínimo esfuerzo.

En 24 horas: llamar a los últimos 10 clientes que cancelaron, preguntar "¿qué os habría hecho quedaros?", y clasificar las respuestas. Antes de mañana tiene un roadmap de retención priorizado por datos reales.

Sin dinero: pedir a los 3 clientes grandes que cedan un desarrollador cada uno a tiempo parcial para co-construir las features que necesitan. Suena absurdo, pero empresas grandes lo hacen en open-source todo el tiempo.

### INTEGRAR

Opciones desde múltiples lentes: (1) Cobrar a los clientes grandes por features custom / co-desarrollo (Volumen, Combinación, Restricción creativa). (2) Arreglar solo los bugs críticos, no todos (Inversión, Restricción creativa, Cruzar). (3) Resolver la relación CTO-CEO antes de cualquier decisión de producto (Cruzar, Inversión). (4) Convertir features custom en módulos/API reutilizables (Combinación, Volumen).

### ABSTRAER

Estructura común: las mejores opciones convierten lo que parece una debilidad (clientes demandantes, producto inestable, equipo junior) en la fuente de la solución. Los clientes que piden features custom no son una carga — son los que financian el producto enterprise. Los bugs no son todos iguales — priorizar los 5 letales es más estratégico que arreglar los 47. El patrón es: "usa la presión como combustible, no como amenaza."

### FRONTERA

Generar opciones aquí es avanzar porque el marco CTO-vs-CEO ha congelado el pensamiento. Pero hay un peligro real: con 7 meses de runway, la divergencia excesiva es un lujo que no se pueden permitir. Necesitan diverger rápido (1-2 días), converger rápido (1 día), y ejecutar. La inteligencia divergente sin la restricción del tiempo es irresponsable aquí.

### RESUMEN (200 palabras)

CTO y CEO ven 2 opciones en oposición binaria; existen al menos 15. La trampa es que el conflicto interpersonal se disfraza de dilema estratégico — la relación rota es el bug #1, antes que los 47 del producto. Las restricciones asumidas son más peligrosas que las reales: estabilizar y pivotar no son incompatibles si se secuencian (bugs críticos primero, enterprise después). Los 3 clientes grandes que piden features custom no son una carga sino la fuente de financiación más inmediata: cobrarles por desarrollo custom genera cash sin dilución. La combinación más potente: construir features custom como módulos reutilizables que se conviertan en API, financiados por los propios clientes — transforma consultoría en plataforma. La inversión radical revela que los 47 bugs no son 47 problemas iguales: probablemente 5 causan el 80% del churn, y arreglar esos 5 es trabajo de 2-3 semanas, no meses. Dejar de retener a los clientes equivocados y concentrarse en los que encajan puede reducir churn más que cualquier fix técnico. El patrón: lo que parece debilidad (clientes exigentes, producto inestable) es exactamente el combustible de la solución — si dejas de pelear con ello y lo usas.

---

## Caso 3: Cambio de Carrera

### EXTRAER — abrir posibilidades

La abogada ve dos opciones: quedarse en el bufete o irse a la ONG medioambiental. Existen muchas más. Opciones descartadas sin examinar: montar su propia práctica de derecho medioambiental corporativo (combina ambos mundos), negociar una jornada reducida en el bufete mientras explora la ONG a tiempo parcial, hacer una excedencia de 6-12 meses, pedir un traslado interno al área de derecho medioambiental del bufete (si existe), montar una consultora que asesore a corporaciones en compliance medioambiental (cobra tarifas corporativas, hace trabajo medioambiental), unirse a la ONG como board member voluntario mientras sigue en el bufete, escribir/enseñar derecho medioambiental como transición gradual, buscar un bufete más pequeño que haga derecho medioambiental con mejores salarios que la ONG, hacer de counsel o freelance para el bufete actual a tiempo parcial mientras transiciona, negociar que el bufete la patrocine en un programa de ESG/sostenibilidad que le dé el pivot interno.

Descartó todo por pensamiento binario ("todo o nada") y porque 3 años rumiando sin actuar han calcificado la decisión en sus dos polos. La restricción más obvia es el dinero — pasa de 180K€ a 55K€. Si esa restricción no existiera, se iría mañana. Eso dice que el deseo es real y el problema es financiero, no vocacional. Alguien completamente diferente — un emprendedor serial — vería la combinación de 20 años de experiencia corporativa + pasión medioambiental como un nicho de mercado masivo: ESG, compliance medioambiental, litigación climática. Con el doble de recursos, montaría su propia firma de derecho medioambiental corporativo. Con la mitad, haría la transición igualmente pero con un plan financiero de 24 meses que incluye reducción de gastos y trabajo freelance de bridge.

### CRUZAR — opciones × restricciones

Restricciones reales: hipoteca 1.800€/mes (real pero renegociable), universidad del hijo en 2 años (real), ingresos irregulares del marido (real). Restricciones asumidas: que la ONG a 55K€ es la ÚNICA forma de hacer derecho medioambiental (falso — hay decenas de formas), que tiene que elegir entre pasión y dinero (falso si diseña un modelo híbrido), que no hablar con el marido es una restricción y no una elección (es una elección), que "rechazada para socia" significa "nunca será socia" (puede significar "no todavía" o "no aquí"), que tiene que decidir ahora ("si no lo hago ahora, nunca").

Opciones "locas" pero viables: ofrecer al bufete actual crear un departamento de ESG/litigación climática — ella lo dirige, el bufete lo financia, es la primera socia del área nueva. El derecho medioambiental corporativo es un mercado en explosión; un bufete prestigioso que no tenga ese departamento lo necesita. Otra: trabajar 3 días/semana en el bufete (negociando reducción salarial a 110K€) y 2 días en la ONG voluntariamente, durante 12 meses, como piloto.

Combinar dos incompatibles: quedarse en el bufete Y hacer trabajo medioambiental. No es fantasía: ESG, due diligence medioambiental, litigación climática son áreas donde su experiencia corporativa es exactamente lo que se necesita. No tiene que dejar su expertise — tiene que redirigirla.

La opción obvia-pero-no: hablar con el marido. Suena trivial. Pero 3 años sin tener la conversación profunda significa que toda la deliberación ha sido unilateral. El marido es la variable con mayor varianza no explorada.

### LENTE L1 — Volumen

10 opciones sin filtrar: (1) Montar consultora de compliance medioambiental. (2) Proponer departamento ESG al bufete. (3) Excedencia de 6 meses. (4) Jornada reducida 3 días bufete + 2 días ONG. (5) Board member de la ONG sin dejar bufete. (6) Cambiar a otro bufete con práctica medioambiental. (7) Enseñar derecho medioambiental en universidad. (8) Escribir un libro sobre derecho corporativo medioambiental. (9) Hacer un máster en medioambiente a tiempo parcial. (10) Montar una clínica legal medioambiental pro-bono los fines de semana.

10 opuestas: (1) Emplearse en la ONG a tiempo completo. (2) Quedarse en el bufete sin cambiar nada. (3) Nunca tomar excedencia. (4) Trabajar 5 días completos solo en un sitio. (5) Cortar toda relación con ONGs. (6) Quedarse en este bufete exacto. (7) Nunca enseñar, solo litigar. (8) No escribir nada público. (9) No estudiar más. (10) No trabajar fines de semana nunca.

Lo que tienen en común las que gustan: todas son transiciones graduales, no saltos de acantilado. Eso revela que el marco "dejarlo todo" vs "quedarme" es falso — la solución natural es un gradiente, no un binario.

### LENTE L2 — Combinación

Mezclar "consultora propia" con "board ONG": monta una consultora de derecho medioambiental corporativo, se sienta en el board de la ONG como asesora legal pro-bono, y usa la ONG como fuente de casos, contactos y propósito. La ONG le da el sentido; la consultora le da los ingresos. Sinergia perfecta.

Solución de otro dominio: el modelo de los médicos que trabajan en hospital privado Y hacen voluntariado en Médicos Sin Fronteras — nadie les obliga a elegir. El modelo "portfolio career" de la economía creativa: múltiples fuentes de ingreso y propósito.

¿Qué haría un niño? "Haz las dos cosas. Los lunes, martes y miércoles eres abogada de empresas, y los jueves y viernes salvas el planeta." ¿Un artista? Vería la tensión entre corporativo y medioambiental como material creativo — montaría un podcast o una columna que narre la transición públicamente, creando su marca personal. ¿Un alien? "¿Por qué los humanos creen que una actividad que los enferma durante 2 años de insomnio es una opción racional?"

### LENTE L3 — Inversión

Hacer lo opuesto: en vez de buscar salir del bufete, buscar cómo hacer que el bufete trabaje para ella. Negociar: "O me dais el departamento ESG, o me voy con mi cartera de clientes a montar una firma medioambiental que compita con vosotros." El poder de negociación de 20 años de experiencia y una cartera de relaciones es enorme — y no lo está usando.

¿Y si el problema es la solución? "He perdido la pasión por el corporativo." ¿Y si la pasión no se perdió sino que nunca fue por el derecho en sí, sino por el sentido? El corporativo sin sentido es vacío; el corporativo con sentido medioambiental podría ser exactamente lo que necesita. No necesita cambiar de profesión — necesita cambiar de propósito dentro de la profesión.

Ampliar en vez de resolver: en vez de decidir "me quedo o me voy", abrir una conversación con 5 personas que hayan hecho transiciones similares y con 5 que combinan ambos mundos. Expandir el mapa antes de elegir la ruta.

### LENTE L4 — Restricción creativa

Si SOLO pudiera hacer UNA cosa: hablar con el marido esta semana. Profundamente. Con números. Con opciones. Con miedos. Todo lo demás es ruido hasta que esa conversación ocurra.

En 24 horas: escribir un email al socio director del bufete preguntando si hay interés en crear una práctica de ESG/derecho medioambiental. Si dice sí, tiene una tercera opción que no existía ayer. Si dice no, tiene información que hoy no tiene.

Sin dinero: ofrecer asesoría legal pro-bono a la ONG durante 3 meses, los sábados. Testear si le gusta de verdad o si es una fantasía de escape. Cero riesgo, máxima información.

### INTEGRAR

Opciones desde múltiples lentes: (1) Hablar con el marido (Restricción creativa, Cruzar, Inversión). (2) Proponer departamento ESG al bufete (Volumen, Combinación, Inversión, Restricción creativa). (3) Modelo híbrido gradual — no salto binario (Volumen, Combinación, Inversión). (4) Consultora propia de derecho medioambiental corporativo (Combinación, Volumen, Extraer).

### ABSTRAER

Estructura común: las mejores opciones rechazan el marco binario y crean una tercera categoría. No es "corporativo O medioambiental" — es "corporativo PARA medioambiental." Su experiencia de 20 años en bufete prestigioso no es un lastre — es el activo diferencial que la hace más valiosa en el espacio medioambiental que cualquier abogado junior de ONG. El patrón: "tu mayor activo está donde crees que está tu mayor problema."

### FRONTERA

Generar opciones aquí es críticamente necesario porque 3 años de rumiación binaria la han paralizado. Pero también hay un riesgo: que la generación de opciones se convierta en una extensión de los 3 años de no decidir. La inteligencia divergente abre el espacio; pero la decisión sigue pendiente, y ninguna cantidad de opciones sustituye el acto de elegir.

### RESUMEN (200 palabras)

La abogada ve 2 opciones calcificadas por 3 años de rumiación; existen al menos 15. La trampa central es el marco binario "todo o nada" cuando la solución natural es un gradiente. Su activo más valioso es exactamente lo que cree que quiere abandonar: 20 años de experiencia corporativa en bufete prestigioso la posicionan de forma única para el derecho medioambiental corporativo — ESG, compliance, litigación climática — un mercado en explosión donde los abogados con credenciales corporativas serias son escasos. Las opciones más potentes combinan ambos mundos: proponer un departamento ESG al bufete, montar consultora propia, modelo híbrido de 3+2 días. La inversión más reveladora: en vez de escapar del bufete, usar su poder de negociación ("me dais ESG o me voy") para transformar su posición desde dentro. Pero nada avanza hasta que hable con el marido — 3 años sin esa conversación profunda significan que toda la deliberación ha sido un monólogo. La restricción financiera (180K€ vs 55K€) es real pero se disuelve parcialmente si el modelo es híbrido o si monta su propia práctica. El patrón: tu mayor activo está donde crees que está tu mayor problema.

---

## LOOP TEST

### Caso elegido: Caso 3 — Cambio de Carrera

Aplico las mismas preguntas a mi propio output.

**EXTRAER sobre mi output:** Mi output ve ~15 opciones para la abogada. ¿Cuántas más existen que yo no vi? Al menos estas: renegociar su hipoteca para reducir la presión financiera base, explorar si el rechazo a socia fue político y si hay una ruta de repair, investigar si la ONG tiene posiciones de dirección legal (no solo 55K€), explorar derecho medioambiental internacional (tribunales europeos, litigación climática transnacional — salarios mucho más altos que ONG local), considerar un año sabático financiado con los 120K€ de ahorros como período de exploración pura. Mi output descartó sin examinar la posibilidad de que el insomnio no sea "estrés laboral" genérico sino un síntoma de algo más profundo que un cambio de trabajo no resolverá.

**CRUZAR:** ¿Mis restricciones son reales o asumidas? Asumí que el bufete actual es "corporativo puro" — puede que ya tenga clientes con componente medioambiental que ella no ve. Asumí que la ONG paga 55K€ como techo cuando podría ser negociable o complementable con consultoría desde dentro.

**L3 — Inversión de mi output:** ¿Y si mi recomendación de "no hagas un salto binario" es exactamente el consejo que la mantiene atrapada? Ella lleva 3 años en gradientes y pruebas mentales. Quizá lo que necesita es exactamente el salto — el shock de compromiso irreversible que la obliga a construir el camino. "Quema las naves" tiene valor cuando la deliberación se ha convertido en parálisis.

**L4:** Si mi output solo pudiera decir UNA cosa: "Habla con tu marido antes de hacer cualquier otra cosa." Eso sobrevive al loop test.

**¿Qué revela la segunda pasada?** Que mi primera pasada privilegió las transiciones graduales porque son "racionales", pero puede que la racionalidad sea exactamente lo que la tiene paralizada desde hace 3 años. La opción radical — renunciar y lanzarse — merece ser considerada no como fantasía sino como estrategia deliberada de commitment device. Esto es genuinamente nuevo.

---

## PATRÓN CROSS-CASE

En los 3 casos aparece el mismo patrón: la persona está atrapada en un marco binario (expandir/no, estabilizar/pivotar, quedarse/irse) cuando el espacio real de opciones es mucho más amplio. Y en los 3 casos, la opción más poderosa no es ni A ni B, sino una tercera categoría que recombina elementos de ambas. El odontólogo no necesita expandir NI quedarse — necesita desacoplar su presencia del negocio. El CTO no necesita estabilizar NI pivotar — necesita secuenciar las dos cosas y resolver primero la relación con el CEO. La abogada no necesita quedarse NI irse — necesita redirigir su expertise corporativa hacia propósito medioambiental.

Otro patrón: en los 3 casos, el mayor activo no explotado está escondido dentro de lo que la persona percibe como su problema. El sillón vacío, los clientes exigentes, la experiencia corporativa: en cada caso, la "carga" es el combustible de la solución.

---

## SATURACIÓN

¿Una tercera pasada aportaría algo nuevo? Posiblemente sí en el Caso 3 — el loop test reveló que mi sesgo hacia lo gradual puede ser contraproducente para alguien en parálisis crónica. Una tercera pasada podría explorar: ¿cuándo es mejor la opción radical que la gradual? ¿Hay señales que indiquen qué tipo de persona necesita cuál? Para los Casos 1 y 2, la tercera pasada probablemente sature — el espacio de opciones ya está bien mapeado.

---

## FIRMA

La inteligencia divergente vio lo que probablemente ninguna otra vería: que en los tres casos la persona confunde un problema de marcos con un problema de opciones — no necesitan mejores opciones dentro de su marco actual, necesitan romper el marco, y que el activo más valioso en cada caso está camuflado dentro de lo que la persona identifica como su principal problema.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/ECOLOGICA.md
============================================================

# RESULTADOS F1-04: INTELIGENCIA ECOLÓGICA (INT-04)

**Estado:** Ejecutado — CR0 para validación de Jesús
**Fecha:** 2026-03-07
**Protocolo:** CARTOGRAFÍA META-RED v1 — Fase 1

---

## INT-04: ECOLÓGICA

### Álgebra
- **Objetos:** ecosistemas, ciclos, nichos, resiliencia, flujos
- **Operaciones:** observar interdependencia, rastrear flujos, detectar fragilidad
- **Firma:** INTERDEPENDENCIA — nada existe aislado, todo afecta a todo
- **Punto ciego:** no ve al individuo — solo al sistema completo

---

## Caso 1: Clínica Dental

### EXTRAER — Mapear el ecosistema

**Organismos del ecosistema:** El dentista-propietario (organismo central, especie dominante y keystone simultáneamente). El dentista asociado (simbionte parcial — depende del ecosistema pero no lo posee). La esposa y los dos hijos (organismos del ecosistema familiar conectado, que comparte flujos con el ecosistema clínica). Los pacientes (población de la que se alimenta el sistema — son el recurso base, como la luz solar en un ecosistema). El banco (organismo parásito/mutualista según el ángulo — extrae cuota fija de 2.800€/mes, ofrece capital a cambio). El personal auxiliar implícito (higienistas, recepcionista — no nombrados pero necesarios para que los sillones operen). El tercer sillón vacío es un nicho ecológico sin ocupante.

**Flujos:** Dinero entra vía pacientes (45.000€/mes) y sale hacia costes fijos (32.000€), hipoteca (2.800€ incluidos en costes), y lo que queda (7.000€) fluye al ecosistema familiar. Energía vital del dentista entra como 2.500 horas/año y sale como servicio clínico. Tiempo parental no fluye — está bloqueado. Atención del dentista fluye unidireccionalmente: clínica absorbe todo, familia recibe residuos. El asociado aporta 1.800h/año de capacidad pero no absorbe presión de gestión ni riesgo financiero.

**Dependencias:** Todo depende del dentista. Los pacientes dependen de él y del asociado para tratamiento. La familia depende de su ingreso y su presencia. El banco depende de que la clínica funcione. El asociado depende del empleo. Pero el dentista depende de su propio cuerpo, que opera sin mantenimiento desde hace 2 años (cero vacaciones).

**Si quitas al dentista:** Colapso total. No hay redundancia en gestión, decisión ni generación de ingreso. El asociado puede tratar pacientes pero no gestionar la clínica. La hipoteca sigue corriendo. La familia pierde ingreso y presencia simultáneamente. El banco activa garantías. Es un ecosistema donde una sola especie es el 80% de la biomasa funcional.

**Ciclos:** Hay un ciclo perverso: trabajar más → más ingreso → más costes fijos comprometidos → necesidad de trabajar más para cubrir compromisos → menos tiempo para recuperación → mayor riesgo de fallo del organismo central. El ciclo se autoalimenta. El ingreso sale hacia costes y vuelve al dentista como presión de producir más.

### CRUZAR — Detectar fragilidad

**Punto único de fallo:** El dentista. Es nodo central de dependencia para finanzas, gestión, relación con banco, decisiones estratégicas, y producción clínica directa. Es el equivalente de un ecosistema con un solo depredador tope que además es el único polinizador.

**Redundancia:** Mínima. El asociado cubre parcialmente la función clínica (1.800 de las 4.300 horas totales de producción), pero cero redundancia en gestión, estrategia, relación bancaria o toma de decisiones. Si el dentista cae enfermo una semana, la producción baja un 40% y la gestión se detiene al 100%.

**Estado del sistema:** En apariencia estable (factura consistente, margen positivo). En realidad, decayendo. El recurso central (la energía vital del dentista) se consume más rápido de lo que se regenera. Un ecosistema que consume su capital natural mientras muestra indicadores económicos positivos — exactamente como una selva que se tala mientras sube el PIB maderero.

**Señal de colapso inminente:** La señal temprana en ecosistemas que dependen de un solo organismo es la degradación de ese organismo antes de que los indicadores sistémicos cambien. Aquí: el padre tuvo infarto a los 52 trabajando 70h/semana. El dentista tiene 38, trabaja 60h/semana, sin vacaciones en 2 años. La señal no es financiera — es biológica.

**¿Ya apareció?** Sí. La esposa lo verbaliza: "No paras nunca." Los hijos preguntan por él. No tiene vacaciones. El patrón intergeneracional con el padre es una señal clarísima de trayectoria convergente. La señal ya está presente; lo que aún no ha llegado es el evento de colapso.

### LENTE L1 — Flujos

**Entra:** 45.000€/mes en dinero. 4.300 horas/año en trabajo humano total (2.500 dentista + 1.800 asociado). Pacientes como flujo de demanda.

**Sale:** 32.000€/mes en costes operativos. Servicios clínicos. Tiempo que no se dedica a la familia.

**Se queda:** 7.000€/mes de margen (se acumula como patrimonio o se consume en vida). Desgaste físico y emocional (se acumula en el cuerpo del dentista). Deuda pendiente de 280.000€ (se reduce lentamente).

**Balance:** Financieramente positivo por estrecho margen (15.5% sobre facturación). Energéticamente negativo: el consumo de energía vital supera la regeneración. No hay mecanismo de recarga. El balance real — contando capital humano — es deficitario.

**Fugas:** El tercer sillón vacío el 40% del tiempo es una fuga de capacidad: un recurso infrautilizado que genera coste fijo sin retorno proporcional. Las 700 horas/año extra que trabaja el dentista sobre el asociado (2.500 vs 1.800) son energía que se disipa en mantener el sistema, no en hacerlo crecer.

**Flujo bloqueado:** El flujo de tiempo parental está completamente bloqueado. El flujo de descanso/regeneración está bloqueado. El flujo de delegación de gestión no existe — no hay conducto para que la responsabilidad gerencial se mueva del dentista a otra entidad.

### LENTE L2 — Nichos

**Roles y solapamiento:** El dentista ocupa tres nichos simultáneamente: productor clínico, gestor de negocio, y tomador de decisiones estratégicas. Esto es un problema ecológico grave — un solo organismo ocupando tres nichos distintos elimina redundancia y crea cuellos de botella. El asociado ocupa un solo nicho limpio: productor clínico puro.

**Nichos vacíos:** Gestor operativo (nadie libera al dentista de tareas administrativas). Estratega externo (nadie cuestiona las decisiones de expansión con distancia). Cuidador del sistema (nadie mide ni mantiene la salud del ecosistema como tal — nadie pregunta "¿el sistema está bien?" en vez de "¿el mes fue rentable?").

**Competencia:** No hay competencia interna por nicho. El problema es lo contrario: concentración excesiva, no competencia.

**Diversidad:** Bajísima. Dos productores y cero en el resto de funciones. Un ecosistema con una sola especie funcional en tres de cuatro nichos críticos es extremadamente frágil.

### LENTE L3 — Resiliencia

**Capacidad de absorber shock:** Muy baja. El margen de 7.000€/mes sobre 45.000€ (15.5%) no absorbe una caída del 20% en facturación. Si el dentista se lesiona un mes, la pérdida de producción supera el margen. No hay colchón temporal: trabaja a capacidad máxima personal, sin slack.

**Reservas:** No se mencionan ahorros. La deuda pendiente de 280.000€ es una anti-reserva. Sin vacaciones = sin reserva temporal. Sin margen de horas = sin reserva de capacidad. El sistema opera sin buffer en ninguna dimensión.

**Lo primero que se rompe:** El cuerpo del dentista. No la clínica, no las finanzas — el organismo biológico que sostiene todo. Es lo que menos redundancia tiene y lo que más presión soporta.

**¿Se ha roto antes?** No directamente, pero hay un precedente familiar claro: el padre tuvo infarto a los 52 en condiciones similares. El sistema no ha sido probado por un shock grande todavía, pero opera en zona de vulnerabilidad máxima.

### LENTE L4 — Ciclos

**Estacionalidad:** Las clínicas dentales tienen cierta estacionalidad (más demanda antes de verano, bajón en agosto), pero el dato no se menciona. Lo que sí se ve es ausencia total de ciclo de recuperación personal.

**Ciclos forzados:** El sistema no tiene ciclo de descanso. 60h/semana, 52 semanas, sin vacaciones. Un ecosistema sin invierno — producción continua sin período de regeneración. Esto es insostenible biológicamente.

**Recuperación entre ciclos:** Inexistente. Cada semana se hereda el desgaste de la anterior sin procesarlo. La propuesta de abrir sábados aceleraría aún más un ciclo que ya no tiene pausa.

**Aceleración:** La propuesta de expandir (5 sillones, sábados, otro dentista) es una propuesta de acelerar el ciclo productivo sin haber restaurado capacidad de ciclo regenerativo. Es como fertilizar un suelo erosionado: el rendimiento sube un año y colapsa al siguiente.

### INTEGRAR (∫)

Cruzar flujos con resiliencia revela la contradicción central: el sistema fluye (genera 45K, mantiene margen), pero no aguanta porque el flujo se sostiene exclusivamente consumiendo el capital biológico de una persona. El flujo financiero positivo enmascara el flujo energético negativo.

Los nichos vacíos (gestor, estratega, cuidador del sistema) explican directamente las fugas: el dentista pierde energía en tareas que no son su nicho natural (gestión administrativa), y nadie monitoriza la salud global del sistema, así que las señales de degradación se ignoran.

Los ciclos forzados están erosionando la resiliencia activamente. Sin ciclo de descanso, cada mes reduce la capacidad del organismo central de resistir el siguiente. Es una cuenta atrás silenciosa.

### ABSTRAER

Este ecosistema se parece a un monocultivo intensivo: alta productividad aparente, dependencia de un solo recurso (el dentista), sin biodiversidad funcional, sin rotación, sin período de barbecho. Los monocultivos colapsan cuando el recurso central se agota o llega una plaga (enfermedad, burnout, divorcio). La intervención mínima que más cambiaría la trayectoria: llenar el nicho de gestor operativo para liberar al dentista de uno de sus tres roles, antes de considerar cualquier expansión. No más sillones — menos roles para el dentista.

### FRONTERA

¿Es realmente un ecosistema o es una máquina operada por una persona? Es más máquina que ecosistema. Un ecosistema real tiene mecanismos de autorregulación; aquí todo pasa por la voluntad y el cuerpo de un individuo. La metáfora ecológica ilumina la fragilidad (dependencia de un solo nodo), pero engaña si sugiere que el sistema se autorregulará — no lo hará. La voluntad humana del dentista (su ambición, su miedo, su patrón paterno) rompe la lógica de ecosistema: un ecosistema no elige expandirse contra su propia capacidad de carga, pero una persona sí.

### RESUMEN

La clínica dental es un monocultivo humano. Un solo organismo (el dentista) ocupa tres nichos simultáneos — productor, gestor, estratega — sin redundancia en ninguno. El sistema fluye financieramente (margen de 7K€/mes), pero consume su capital biológico sin regenerarlo: 60h/semana, cero vacaciones en 2 años, patrón intergeneracional de colapso cardiovascular. La señal de alarma ya está presente — no en las métricas financieras, sino en las quejas de la esposa, la ausencia con los hijos, el precedente del padre. La propuesta de expandir (5 sillones, sábados) equivale a intensificar un monocultivo sin resolver la erosión del suelo. El tercer sillón vacío al 40% confirma que el cuello de botella no es capacidad instalada sino capacidad humana. Tres nichos vacíos explican la fragilidad: no hay gestor operativo, no hay estratega externo, no hay cuidador del sistema. La intervención ecológica mínima es llenar nichos antes de añadir capacidad: delegar gestión para que el dentista ocupe un solo nicho. Sin esto, cada expansión acelera la trayectoria hacia el colapso del organismo central — y con él, de todo el ecosistema.

---

## Caso 2: Startup SaaS

### EXTRAER — Mapear el ecosistema

**Organismos:** El CTO (organismo bajo observación, especie que intenta ser keystone tras la salida de otra). El CEO (segundo organismo dominante, en tensión territorial con el CTO). Los 3 desarrolladores junior (organismos juveniles, con alta rotación — 2 se fueron en 12 meses). El diseñador part-time (organismo periférico, medio dentro medio fuera). Los 80 clientes de pago (población de la que se alimenta el sistema). Los 3 clientes grandes (30% del ingreso — especie de la que depende desproporcionadamente la alimentación). Los 3 fondos de Serie A que no avanzaron (organismos potenciales del ecosistema que eligieron no entrar). El co-fundador técnico que se fue (organismo que abandonó el ecosistema hace 6 meses — su ausencia dejó hueco).

**Flujos:** Dinero entra vía MRR de 80 clientes (12.000€/mes) y sale como burn (28.000€/mes). La diferencia (16.000€/mes) se cubre con runway acumulado que se agota. Conocimiento técnico fluye del CTO a los juniors, pero no en la dirección contraria (no hay seniors que aporten). Clientes salen al ritmo de 8%/mes — es un flujo de fuga constante, como un estanque con un agujero en el fondo. Los 3 clientes grandes inyectan dinero pero extraen features custom, desviando el desarrollo del producto core. Comunicación entre CTO y CEO está casi cortada — flujo de información estratégica bloqueado.

**Dependencias:** Los clientes dependen del producto para funcionar. El equipo de desarrollo depende del CTO para dirección técnica. El CTO depende del CEO para estrategia comercial y fundraising. El CEO depende del CTO para que el producto exista. Los juniors dependen de orientación senior que no existe. Todo depende del runway, que es un recurso finito en depreciación.

**Si quitas al CTO:** El desarrollo se detiene. Los 3 juniors no tienen senior que dirija. Los bugs se acumulan más rápido. El churn se acelera. El CEO se queda con una visión enterprise sin motor técnico. Colapso técnico en semanas.

**Si quitas al CEO:** El CTO puede mantener el producto vivo, pero no hay nadie que venda, negocie con fondos, ni gestione relación con clientes grandes. Colapso comercial progresivo.

**Ciclos:** Hay un ciclo de muerte por churn: bugs → clientes se van → menos ingreso → menos runway → más presión → menos tiempo para arreglar bugs → más bugs. Es un ciclo de refuerzo destructivo que ya está activo. Otro ciclo: features custom para grandes clientes → desvío de roadmap → producto core no mejora → clientes pequeños se van → más dependencia de los grandes → más custom features.

### CRUZAR — Detectar fragilidad

**Punto único de fallo:** Hay dos candidatos. El CTO es punto único de fallo técnico (el único senior en un equipo de juniors). El runway es punto único de fallo financiero (7 meses y decreciendo). Pero el punto de fallo más profundo es la relación CTO-CEO: si esa simbiosis no funciona, ninguna decisión estratégica se ejecuta correctamente. Y ya no funciona — "apenas se hablan fuera de reuniones formales."

**Redundancia:** Técnica: cero. No hay otro senior. Si el CTO cae, nadie puede liderar. Comercial: cero. Solo el CEO vende. De ingreso: peligrosamente baja — 30% en 3 clientes. De decisión estratégica: cero — dos personas que no se hablan deben tomar decisiones conjuntas.

**Estado del sistema:** Decayendo activamente. El churn del 8%/mes es sangrado. El runway se agota. Devs se van. La comunicación fundadora está rota. No hay señales de mejora en ningún indicador.

**Señal de colapso:** En un ecosistema en declive, la primera señal es la pérdida de diversidad — las especies más móviles se van primero. Aquí: 2 devs se fueron en 12 meses, y el co-fundador técnico también. Los organismos con movilidad ya están abandonando el ecosistema.

**¿Ya apareció?** Claramente sí. La pérdida de 3 personas (co-fundador + 2 devs) en 12 meses es un éxodo. Es la versión startup de la canaria en la mina.

### LENTE L1 — Flujos

**Entra:** 12.000€/mes de MRR. Horas de trabajo del equipo (CTO a 70h/semana, juniors presumiblemente a tiempo completo).

**Sale:** 28.000€/mes de burn. Clientes (8%/mes de churn = ~6-7 clientes/mes saliendo). Personal (2 devs + 1 co-fundador en 12 meses).

**Se queda:** Deuda técnica (47 bugs abiertos y creciendo). Tensión relacional entre fundadores. Código que los juniors escriben pero que nadie con experiencia revisa adecuadamente.

**Balance:** Masivamente negativo. Sale más de lo que entra en las tres dimensiones: financiera (-16K/mes), humana (más personas salen que entran), y técnica (más bugs se crean que se resuelven).

**Fugas:** El churn es la fuga principal — cada cliente que se va por bugs es energía invertida en adquisición que se pierde. Las features custom para los 3 grandes son una fuga de desarrollo: horas que no mejoran el producto core sino que sirven a intereses particulares. La comunicación rota entre CTO y CEO es una fuga de coordinación que multiplica el desperdicio.

**Flujo bloqueado:** Feedback de clientes → mejora de producto. Este flujo debería existir (clientes dicen qué falla → equipo arregla → clientes se quedan) pero está roto porque el equipo no tiene capacidad para procesar 47 bugs mientras también construye features enterprise.

### LENTE L2 — Nichos

**Roles:** El CTO ocupa múltiples nichos: arquitecto, líder técnico, mentor de juniors, y probablemente devops y QA. El CEO ocupa ventas, estrategia, fundraising y relación con clientes. Los juniors tienen un nicho claro (código) pero sin supervisión senior, la calidad del output es incierta.

**Nichos vacíos:** Senior developer / tech lead (nadie entre el CTO y los juniors — vacío desde que el co-fundador técnico se fue). QA/testing (nadie se dedica a calidad, lo que explica los 47 bugs). Product manager (nadie prioriza objetivamente entre bugs, features core y features custom). Customer success (nadie retiene clientes proactivamente — el churn se descubre cuando ya pasó).

**Competencia por nicho:** CTO y CEO compiten por el nicho de "definición de dirección del producto." Uno dice estabilizar, otro dice pivotar. Esta competencia sin resolución es la peor forma de solapamiento: parálisis decisional.

**Diversidad:** Muy baja. Todos los devs son junior. No hay nadie de producto. No hay nadie de calidad. No hay nadie de retención. Es un ecosistema con dos depredadores tope (CTO y CEO) y un grupo homogéneo de organismos juveniles sin las especies intermedias que harían funcionar la cadena trófica.

### LENTE L3 — Resiliencia

**Capacidad de absorber shock:** 7 meses de runway = el reloj está corriendo. Cualquier shock — la pérdida de uno de los 3 clientes grandes (30% del ingreso), la salida de otro dev, una emergencia técnica — reduciría el runway por debajo del umbral de viabilidad. El sistema está operando en la zona entre "funciona" y "colapsa" sin buffer.

**Reservas:** Solo financiera: ~7 meses × (28K - 12K) ≈ 112K€ en caja (aproximación). Cero reserva técnica (47 bugs y creciendo). Cero reserva relacional (CTO-CEO en mínimos). Cero reserva de talento (juniors sin senior).

**Lo primero que se rompe:** La moral del equipo. Los juniors, sin senior que los guíe, sobrecargados, viendo que los devs anteriores se fueron, serán los siguientes en irse. Alternativamente, la pérdida de uno de los 3 clientes grandes desencadenaría crisis financiera inmediata.

**¿Se ha roto antes?** Sí — la salida del co-fundador técnico fue una fractura importante. El sistema no se recuperó: dejó un vacío de senior que no se llenó, y las consecuencias (47 bugs, churn, falta de supervisión de juniors) son secuelas directas de esa ruptura no reparada.

### LENTE L4 — Ciclos

**Ritmo natural:** Las startups SaaS tienen un ciclo natural: construir → lanzar → medir → iterar. Este ciclo está roto. No se completa la iteración porque las features custom de los grandes desvían el roadmap, los bugs de calidad no se resuelven, y la tensión CTO-CEO impide acordar qué medir.

**Ciclos forzados:** El CEO quiere forzar un ciclo de pivot a enterprise antes de completar el ciclo de estabilización. Esto es como intentar que una planta fructifique antes de que haya enraizado — la energía se dispersa y el organismo no consolida ninguna fase.

**Recuperación:** No hay tiempo de recuperación entre crisis. La salida del co-fundador → crisis técnica → pérdida de devs → presión de churn → presión de runway. Cada crisis se encadena sin procesarse.

**Aceleración:** Los ciclos se están acelerando hacia el colapso. El churn compuesto al 8%/mes significa que en 9 meses la base de clientes original se ha renovado por completo — si es que se adquieren nuevos al mismo ritmo, lo cual no se menciona.

### INTEGRAR (∫)

Flujos con resiliencia: el sistema sangra más de lo que ingiere y no tiene reservas para compensar. Es un ecosistema en déficit calórico sostenido con un reloj de 7 meses hasta la inanición.

Nichos vacíos con fugas: la ausencia de QA explica los bugs que causan churn. La ausencia de product manager explica la parálisis entre estabilizar y pivotar. La ausencia de customer success explica que el churn se detecte tarde. Cada nicho vacío genera una fuga específica y cuantificable.

Ciclos forzados con resiliencia: el intento de pivotar a enterprise antes de estabilizar es forzar un ciclo nuevo sobre un sistema que no ha completado el anterior. Esto consume la poca resiliencia que queda en algo que aún no genera retorno.

### ABSTRAER

Este ecosistema se parece a un arrecife de coral en blanqueamiento. La especie fundacional (la relación CTO-CEO, equivalente al coral) se ha degradado. Las especies dependientes (devs, clientes) empiezan a migrar. El agua se calienta (burn > revenue) sin pausa. Las especies oportunistas (clientes grandes pidiendo custom features) extraen valor sin contribuir a la salud del arrecife. La intervención mínima: restaurar la simbiosis fundacional (alinear CTO-CEO sobre una dirección) antes de cualquier otra acción. Sin esa simbiosis, nada que se construya encima tendrá cimiento.

### FRONTERA

Aquí la metáfora ecológica ilumina mucho: la pérdida de diversidad, los ciclos rotos, las fugas, los nichos vacíos — todo calza. Pero la metáfora tiene un límite: en un ecosistema natural no hay "decisión de pivotar." La tensión CTO vs CEO es política, no ecológica. Es una disputa de voluntades que la lente ecológica puede describir (como competencia intraespecífica) pero no resolver.

### RESUMEN

La startup es un arrecife en blanqueamiento. La simbiosis fundacional (CTO-CEO) se ha degradado — apenas se comunican, compiten por la dirección del producto, y no resuelven. El ecosistema sangra en tres dimensiones: financiera (-16K€/mes), humana (3 personas han migrado en 12 meses), y técnica (47 bugs crecientes). Cuatro nichos vacíos — senior dev, QA, product manager, customer success — explican directamente las cuatro fugas principales: bugs, churn, parálisis decisional, y detección tardía de pérdida. El 30% de ingresos concentrado en 3 clientes crea dependencia que desvía el desarrollo con features custom, debilitando el producto core y acelerando el churn de los pequeños. El runway de 7 meses es el reloj del ecosistema. La propuesta de pivotar a enterprise es forzar un nuevo ciclo sobre un sistema que no completó el anterior — equivalente a intentar fructificar sin raíces. La señal de colapso (migración de especies móviles) ya está activa: co-fundador, devs, clientes salen progresivamente. La intervención ecológica mínima: restaurar la simbiosis CTO-CEO y llenar el nicho de senior developer, antes de pivotar o escalar.

---

## Caso 3: Cambio de Carrera

### EXTRAER — Mapear el ecosistema

**Organismos:** La abogada (organismo central, en fase de potencial migración entre ecosistemas). El bufete (ecosistema actual — hábitat que provee 180K€/año pero consume vitalidad). El marido freelance (organismo interdependiente con flujos irregulares de 40-80K€). Los dos hijos adolescentes (organismos en desarrollo que consumen recursos y generan necesidades con horizonte definido — universidad en 2 años). Los padres de la abogada (organismos del ecosistema de origen, ejercen presión normativa). La amiga que cambió (organismo explorador que ya migró — prueba de que el nuevo hábitat es viable). La ONG de derecho medioambiental (ecosistema destino potencial, ofrece 55K€/año y promesa de sentido). El médico (sensor externo que ha diagnosticado que el sistema actual daña al organismo central). El banco (hipoteca de 1.800€/mes, 15 años).

**Flujos:** Del bufete entra 180K€/año y sale vitalidad, sueño, pasión (insomnio 2 años). Del marido entra 40-80K€/año (variable, poco fiable como base). Hacia los hijos salen recursos materiales (educación, vivienda) y debería fluir presencia parental. De los ahorros no sale nada (120K€ estáticos — reserva no desplegada). Hacia la hipoteca salen 1.800€/mes (21.600€/año) — flujo fijo no negociable. Del nuevo ecosistema potencial (ONG) entraría 55K€/año + sentido + sueño. De los padres fluye presión y juicio, no apoyo material.

**Dependencias:** Los hijos dependen del ingreso familiar total para estabilidad. La hipoteca depende del ingreso. La abogada depende del bufete para ingreso alto, y del cambio para salud mental. El marido depende parcialmente de la estabilidad que la abogada aporta. La ONG no depende de ella (la abogada es sustituible allí). El bufete depende parcialmente de ella (pero la rechazó para socia — señal de que no la valora como insustituible).

**Si quitas a la abogada del bufete:** Ella recupera salud (el médico lo confirma). La familia pierde 125K€/año de ingreso neto (180K-55K). Los hijos enfrentan ajuste material. La hipoteca requiere cubrirse con menos. El bufete la reemplaza sin drama — la rechazó para socia, no es imprescindible allí.

**Ciclos:** Ciclo actual: trabajar en bufete → ganar bien → mantener estilo de vida → necesitar ganar bien → seguir en bufete. Es un ciclo de lock-in donde el nivel de gasto justifica el nivel de ingreso que justifica el nivel de trabajo. Otro ciclo: insomnio → menor rendimiento → más estrés → más insomnio. Y un meta-ciclo: 3 años pensando en cambiar → no decidir → más tiempo invertido en el lugar equivocado → más difícil cambiar por edad/inercia → seguir pensando sin cambiar.

### CRUZAR — Detectar fragilidad

**Punto único de fallo:** El ingreso de la abogada. 180K de 220-260K totales familiares (69-82% del total). Si ella cae (burnout, enfermedad por estrés crónico), no hay quien compense. Irónicamente, el sistema que depende de su ingreso alto es el que está destruyendo su capacidad de generarlo.

**Redundancia:** El marido genera 40-80K€, lo cual cubre hipoteca + gastos básicos en el escenario bajo, pero con margen mínimo. Los 120K€ de ahorro son la única redundancia real — son un buffer que puede comprar tiempo de transición pero no ingreso permanente.

**Estado del sistema:** Estable externamente (el ingreso llega, la hipoteca se paga, los hijos están bien), decayendo internamente (insomnio 2 años, pérdida de pasión, rechazada para socia). Es la versión personal del caso dental: indicadores externos positivos, indicador biológico/psicológico en rojo.

**Señal de colapso:** Insomnio crónico. En un ecosistema personal, el sueño es el equivalente del ciclo de regeneración. Cuando el organismo central no puede regenerarse, todo lo demás es cuestión de tiempo.

**¿Ya apareció?** Sí, hace 2 años. El insomnio no es la señal temprana — es la señal intermedia. La señal temprana fue la pérdida de pasión ("he perdido la pasión por el derecho corporativo"). El insomnio es la segunda fase. La tercera sería colapso funcional (errores profesionales, enfermedad, ruptura familiar).

### LENTE L1 — Flujos

**Entra:** 180K€/año del bufete. 40-80K€ del marido. Sentido de seguridad financiera.

**Sale:** 21.600€/año de hipoteca (fijo). Gastos familiares (no cuantificados pero presumiblemente significativos con 2 adolescentes). Energía vital de la abogada hacia un trabajo que no le devuelve significado.

**Se queda:** 120K€ de ahorro (reserva estática). Insomnio acumulado. 3 años de deliberación sin acción (coste de oportunidad cristalizado). Resentimiento creciente hacia el bufete (rechazada para socia).

**Balance:** Financieramente positivo — acumula ahorro con un ingreso muy alto. Emocionalmente negativo — pierde salud, sentido, y años de posible reconversión. El balance real depende de qué moneda cuentes.

**Fugas:** La fuga principal es energía vital invertida en un ecosistema que no la reciproca (el bufete la tiene pero no la asciende). Los 3 años de deliberación sin acción son una fuga de tiempo — la ventana de cambio se estrecha con cada año. La no-conversación con el marido es un flujo bloqueado que genera incertidumbre innecesaria.

**Flujo bloqueado:** La conversación profunda con el marido sobre el cambio. Este flujo de información es crítico y está obstruido — sin él, no se puede evaluar la viabilidad real de la transición porque la mitad de la ecuación financiera (los ingresos del marido, su disposición a ajustar) está sin definir.

### LENTE L2 — Nichos

**Roles:** La abogada ocupa el nicho de proveedora principal (69-82% del ingreso), profesional de carrera, madre, y potencialmente cuidadora emocional de la familia. El marido ocupa nicho de co-proveedor irregular y padre. Los hijos ocupan nicho de dependientes en transición (14 y 16 — a 2-4 años de independencia parcial).

**Nichos vacíos:** Consejero de transición (nadie ayuda a la abogada a navegar el cambio de forma estructurada — solo tiene inputs parciales: padres que dicen no, amiga que dice sí, médico que diagnostica). Aliado estratégico en la decisión (el marido debería ser este aliado, pero la conversación profunda no ha ocurrido). Patrocinador en el nuevo ecosistema (nadie en la ONG la está atrayendo activamente — el nuevo hábitat es una idea, no una relación).

**Competencia:** Hay competencia interna entre dos identidades/nichos de la abogada: proveedora-seguridad vs buscadora-de-sentido. Estas dos funciones compiten por la misma decisión y no hay mecanismo interno para resolverlo.

**Diversidad:** El ecosistema familiar depende excesivamente de un nicho (ingreso alto de la abogada) y de un modo (sacrificio de vitalidad por estabilidad material). Poca diversidad de fuentes de ingreso, de sentido, de estrategias de vida.

### LENTE L3 — Resiliencia

**Capacidad de absorber shock:** Media-alta financieramente si se activan los ahorros. Los 120K€ a 55K€ de ingreso ONG + 40K€ mínimos del marido = 95K€/año. Gastos: 21.600€ hipoteca + vida (estimemos 50-60K€ total conservador). Hay un gap pero los ahorros cubren varios años de transición. El shock no es financiero — es identitario y relacional.

**Reservas:** 120K€ de ahorro = reserva material significativa (~2-3 años de colchón según gap). Pero cero reserva relacional (no ha hablado con el marido), cero reserva de red profesional en el nuevo campo (no se menciona networking en medioambiental), y reservas de salud en depreciación (insomnio crónico).

**Lo primero que se rompe bajo presión:** La relación de pareja. Un cambio de carrera con pérdida de 125K€ de ingreso sin conversación previa profunda es una bomba relacional. Si la transición genera estrés financiero, el marido freelance con ingresos irregulares será el punto de fricción.

**¿Se ha roto antes?** No hay precedente de ruptura grande. Pero el sistema nunca ha sido testeado — 20 años en el mismo ecosistema profesional. Es resiliencia no probada, que puede ser fortaleza oculta o fragilidad sin diagnosticar.

### LENTE L4 — Ciclos

**Estacionalidad:** Los hijos tienen un ciclo de desarrollo con horizonte: en 2 años el mayor entra a la universidad, en 4 el menor. Este es un ciclo natural que cambia la estructura de gastos y dependencias. Es una ventana temporal que se abre gradualmente.

**Ciclos forzados:** El ciclo laboral del bufete es forzado — no hay ritmo natural de descanso suficiente (si lo hubiera, no habría insomnio crónico). La deliberación de 3 años es un ciclo atascado: pensar → no decidir → volver a pensar. No es un ciclo productivo, es una órbita cerrada sin progreso.

**Recuperación:** Cero recuperación actual. El insomnio de 2 años indica que ni siquiera el ciclo diario de sueño-vigilia está intacto. La pausa mínima (vacaciones, sabático) no se menciona como opción.

**Aceleración:** El ciclo de deliberación se auto-refuerza: cuanto más tiempo pasa, más coste hundido en el bufete, más miedo de perder lo invertido, más difícil cambiar. La ventana se cierra — "si no lo hago ahora, no lo haré nunca" es la percepción correcta de un ciclo que se endurece con el tiempo.

### INTEGRAR (∫)

Flujos con resiliencia: el sistema actual fluye financieramente pero degrada a su organismo central. Las reservas (120K€) son suficientes para una transición si se despliegan correctamente, pero la resiliencia relacional no está testeada — la conversación con el marido es un flujo bloqueado que define si la transición es viable como ecosistema familiar o solo como fantasía individual.

Nichos vacíos con fugas: la ausencia de consejero de transición y de aliado estratégico (marido como co-decisor informado) explica por qué la deliberación lleva 3 años sin resolverse. Sin esos nichos llenos, la decisión rebota entre extremos: padres que dicen no, amiga que dice sí, médico que señala daño, y ella sola con la contradicción.

Ciclos forzados con resiliencia: el ciclo del bufete erosiona la salud (insomnio), y el ciclo de deliberación erosiona la ventana temporal. Ambos convergen: si no rompe uno de los dos ciclos, el sistema se resuelve solo — por colapso de salud o por rigidificación de la inercia.

### ABSTRAER

Este ecosistema se parece a un organismo en un hábitat que se ha vuelto tóxico pero que provee alimento abundante. La migración a un nuevo hábitat es viable (hay reservas para el viaje, el nuevo hábitat existe, otra especie similar ya migró con éxito), pero el organismo está paralizado en la zona de transición — come bien pero se envenena. La intervención mínima no es decidir (irse o quedarse) — es desbloquear el flujo de información con el marido. Esa sola conversación convierte un dilema individual en un proyecto de ecosistema familiar, y cambia radicalmente la ecuación.

### FRONTERA

La metáfora ecológica ilumina la interdependencia familiar y la toxicidad del hábitat actual, pero tiene un límite fuerte aquí: este es un problema de identidad tanto como de ecosistema. La abogada no es un animal respondiendo a estímulos — es una persona con una narrativa de 20 años, presión parental, y conflicto de valores. La lente ecológica ve que el hábitat es tóxico y que hay otro hábitat disponible, pero no puede evaluar si "derecho medioambiental en ONG" es genuina vocación o idealización reactiva. Eso requiere una inteligencia que vea al individuo — exactamente lo que la ecológica no ve por construcción.

### RESUMEN

La abogada es un organismo en un hábitat que se ha vuelto tóxico pero sigue siendo nutritivo. El bufete provee 180K€/año pero genera insomnio crónico y pérdida de pasión — el ciclo de regeneración básico (sueño) lleva 2 años roto. Las reservas financieras (120K€) hacen la migración viable matemáticamente, pero el flujo crítico está bloqueado: la conversación profunda con el marido no ha ocurrido, lo que mantiene la transición como fantasía individual en vez de proyecto familiar. Tres nichos vacíos (consejero de transición, aliado estratégico, patrocinador en el nuevo hábitat) explican la parálisis de 3 años. La ventana temporal tiene una estructura favorable — los hijos alcanzan independencia parcial en 2-4 años, reduciendo la carga sobre el ecosistema. Dos ciclos convergen peligrosamente: el laboral erosiona la salud y el de deliberación cierra la ventana temporal. Si no rompe uno, el sistema se resuelve solo por colapso. La intervención ecológica mínima no es decidir — es desbloquear el flujo con el marido. Esa conversación transforma el dilema de un organismo solitario en una migración coordinada de todo el ecosistema familiar.

---

## POST-3-CASOS

### Loop Test

**Caso elegido:** Startup SaaS — fue el análisis más profundo por la cantidad de dinámicas simultáneas.

**Segunda pasada: aplicar las preguntas ecológicas al output del Caso 2.**

Cuando miro mi propio análisis como ecosistema: los "organismos" de mi output son las metáforas (arrecife, blanqueamiento, migración de especies), las categorías (flujos, nichos, resiliencia, ciclos), y los hallazgos. Los "flujos" son las conexiones causales que tracé entre elementos.

Lo que la segunda pasada revela que la primera no vio:

1. **Mi análisis tiene su propio punto único de fallo:** la metáfora del arrecife. Si la metáfora no encaja bien, todo el análisis se distorsiona. ¿Es realmente un arrecife? La startup tiene una diferencia radical: puede pivotar conscientemente. Un arrecife no puede decidir convertirse en un manglar. Mi metáfora es iluminadora pero también limitante.

2. **Nicho vacío en mi propio análisis:** No mencioné el ecosistema de competidores. ¿Hay otros SaaS de gestión de inventario para restaurantes? ¿Están mejor o peor? La lente ecológica del caso no incluyó el ecosistema competitivo externo — solo miré el ecosistema interno.

3. **Flujo que ignoré:** El flujo de aprendizaje organizacional. Los 47 bugs no son solo deuda técnica — son información sobre qué falla. Si alguien los analizara sistemáticamente, serían un mapa de mejora. Ese flujo de bugs→aprendizaje no existe en mi análisis.

4. **Mi ciclo propio:** Apliqué un patrón que se repite: encontrar el "organismo central sobreexigido" fue el mismo frame en los 3 casos. ¿Es porque los 3 casos lo tienen, o porque mi lente lo busca? Probablemente ambas cosas, pero la segunda pasada hace visible el sesgo.

**¿Es genuinamente nuevo?** Parcialmente. Los puntos sobre ecosistema externo y flujo de aprendizaje son hallazgos nuevos que la primera pasada no contenía. La metacognición sobre sesgo de lente es genuina.

### Patrón Cross-Case

En los tres ecosistemas, hay un organismo central que sostiene el sistema a costa de degradarse, un flujo de regeneración bloqueado (vacaciones, sueño, comunicación entre fundadores), y nichos vacíos que explican exactamente las fugas que debilitan al sistema. La estructura es: **productividad visible que enmascara erosión invisible del recurso central, con nichos vacíos que perpetúan la situación porque nadie cumple la función de "cuidador del ecosistema."**

Más concretamente: en los tres casos, la intervención que más cambiaría la trayectoria NO es la que el protagonista está considerando (expandir, pivotar, dejar el bufete), sino una intervención previa que desbloquea un flujo o llena un nicho. Para el dentista: llenar nicho de gestor. Para la startup: restaurar simbiosis CTO-CEO. Para la abogada: desbloquear flujo con el marido. La acción grande requiere la acción pequeña previa.

### Saturación

¿Una tercera pasada aportaría algo nuevo? Marginalmente. La segunda pasada reveló sesgos reales (metáfora como punto de fallo, ecosistema externo ignorado, flujo de aprendizaje invisible). Una tercera pasada probablemente confirmaría estos hallazgos y quizás encontraría un meta-patrón más, pero con rendimiento decreciente marcado. Estimación: ~10-15% de valor marginal en tercera pasada.

### Firma — INT-04: ECOLÓGICA

**Lo que esta inteligencia ve que probablemente ninguna otra vería:** Que en los tres casos la pregunta no es la decisión grande (expandir / pivotar / cambiar), sino el flujo bloqueado o el nicho vacío que hace que la decisión grande sea prematura. La ecológica ve que todo sistema que depende de un solo organismo para tres funciones está condenado — no por falta de ambición sino por exceso de concentración. Ningún ecosistema sano funciona así.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/ESPACIAL.md
============================================================

# F1-11: INTELIGENCIA ESPACIAL (INT-11)

## Caso 1: Clínica Dental

### EXTRAER — mapear el espacio

Si dibujaras este problema, tendría la forma de un embudo invertido con grietas. En el centro hay un punto de máxima compresión: el odontólogo mismo. Todo converge hacia él — pacientes, horas, deuda, familia, decisiones. La clínica es un espacio físico literal (3 sillones, paredes, metros cuadrados) pero también un espacio metafórico donde vida y trabajo están superpuestos sin separación.

Lo que está cerca: trabajo-deuda-cuerpo. Estas tres cosas ocupan prácticamente el mismo punto espacial. Lo que está lejos: familia-descanso-salud a largo plazo. Están en la periferia del mapa, visible pero inalcanzable en la práctica diaria.

Hay un centro brutal: él. Y una periferia: su esposa, sus hijos, su futuro biológico. El problema es de mesa — íntimo, personal, con un número reducido de actores — pero su decisión de expandir lo convertiría en un problema de mapa, con empleados adicionales, deuda ampliada, horarios complejos.

La perspectiva desde la que se mira es la del propietario-operador. Esa perspectiva oculta que el sillón vacío el 40% del tiempo es un dato espacial enorme: ya tiene capacidad sin usar. La expansión a 5 sillones es una respuesta a un problema de llenado que aún no ha resuelto con 3.

### CRUZAR — forma × perspectiva

Si te acercas, ves el micro-espacio: un hombre sentado frente a una boca abierta, 60 horas a la semana, con dolor de espalda y sin cenar con sus hijos. Si te alejas, ves un negocio que factura 45K pero cuyo margen neto (7K) es ridículamente pequeño en relación al espacio vital que consume.

No hay simetría. El lado "negocio" del mapa es denso, sobrecargado, con actividad constante. El lado "vida" es un terreno casi vacío. Las proporciones están invertidas: el negocio ocupa el 85% del espacio vital y produce el 15% del valor real.

El tercer sillón vacío el 40% del tiempo es una zona vacía que debería estar llena antes de crear dos zonas más. Es como construir una segunda planta de un edificio cuya primera planta tiene habitaciones sin usar.

### LENTE L1 — Topografía

Pico claro: las horas de trabajo del odontólogo (2.500h/año). Insostenible, ya está erosionando la base. Valle profundo: el margen neto. 7.000€/mes para un sistema que consume toda la energía vital es un valle alarmante.

Pendiente peligrosa: todo se desliza hacia más trabajo. La propuesta del banco, los sábados abiertos, el tercer dentista — cada opción suma horas. No hay pendiente que lleve hacia menos trabajo.

Meseta invisible: la utilización del sillón 3. No importa que añada sillones 4 y 5 si no resuelve por qué el 3 está vacío el 40%. Esa meseta indica un techo de demanda, de agenda, o de gestión que expandir no resuelve.

### LENTE L2 — Fronteras

La frontera entre "clínica" y "vida personal" no existe: trabaja 60h/semana, no tiene vacaciones, su identidad es el negocio. La frontera es completamente permeable — todo fluye del trabajo hacia la vida, pero nada fluye de la vida hacia el trabajo.

Algo que debería estar dentro de sus consideraciones pero está fuera: la historia de su padre (infarto a los 52). Es un dato periférico en su mapa mental que un observador colocaría en el centro. También está fuera la conversación seria con su esposa.

La frontera más rígida: la hipoteca. 280K pendientes, 2.800€/mes. Condiciona todo el espacio de decisión.

### LENTE L3 — Perspectiva

Desde arriba: un negocio con margen ajustado, un activo infrautilizado, un propietario que es el cuello de botella, y una propuesta de expansión que multiplica la complejidad sin resolver ineficiencias base.

Desde dentro: agotamiento, orgullo de propietario, la seducción de "65K/mes", culpa creciente por los hijos.

Desde fuera: un profesional que repite el patrón exacto de su padre, con un negocio que le ha comprado a él en vez de al revés.

Las tres perspectivas NO cuentan la misma historia. Desde dentro, expandir "tiene sentido". Desde arriba, es prematuro. Desde fuera, es peligroso.

### LENTE L4 — Proporción

El tamaño del negocio en euros no corresponde a su importancia vital. Algo pequeño con impacto desproporcionado: el sillón vacío 40%. Algo grande que no produce: las 2.500 horas/año → 2,80€/hora de beneficio neto. Proporción absurda.

### INTEGRAR

La topografía (pendiente hacia más trabajo, meseta en sillón 3) explica las fronteras (vida-trabajo sin separación). La perspectiva (desde dentro se justifica expandir) oculta la proporción (2,80€/hora). El mapa grita: llenar antes de expandir, crear fronteras antes de abrir más espacio.

### ABSTRAER

Este mapa se parece al de una ciudad que quiere anexionar terreno antes de urbanizar lo que ya tiene. También al de un organismo que crece sin diferenciación — más masa, misma estructura — lo cual en biología es la definición de tumor.

### FRONTERA

Lo que el espacio no puede capturar: el miedo. El miedo a parar, el miedo a no ser suficiente, el miedo a repetir el destino de su padre. Esos procesos son emocionales, no espaciales.

**Resumen:** El mapa espacial de la clínica dental revela un sistema con centro colapsado y periferia vacía. El odontólogo es el punto de máxima compresión: todo converge en él. El negocio ocupa el 85% del espacio vital produciendo un margen neto de 2,80€/hora — una proporción grotesca. El sillón vacío el 40% es el hallazgo espacial clave: hay capacidad sin usar antes de cualquier expansión. Toda la topografía presenta pendiente hacia más trabajo, sin ninguna fuerza gravitacional hacia el descanso. Las fronteras entre trabajo y vida están borradas; la frontera más rígida es la hipoteca. Las tres perspectivas divergen brutalmente: desde dentro expandir parece lógico, desde arriba es prematuro, desde fuera es peligroso. El patrón padre-hijo es un dato periférico que debería estar en el centro. El mapa se parece al de una ciudad que anexiona terreno antes de urbanizar lo que tiene. Lo que el espacio no puede capturar es el motor emocional que mantiene la configuración disfuncional.

**Firma:** El espacio revela que expandir es añadir metros cuadrados a un edificio con habitaciones vacías y cimientos agrietados. La forma del problema grita consolidar, no crecer.

---

## Caso 2: Startup SaaS

### EXTRAER — mapear el espacio

Si dibujaras este problema, tendría la forma de un puente roto entre dos islas. Isla A: el producto actual (gestión de inventario para restaurantes, 80 clientes, bugs, churn). Isla B: el futuro enterprise que el CEO imagina. El puente entre ambas está roto — falta el co-fundador técnico que era la viga central, faltan recursos, falta tiempo. Y debajo del puente hay agua subiendo: 7 meses de runway.

Lo que está cerca: bugs-churn-descontento de clientes. Están en el mismo punto, son la misma crisis. Lo que está lejos: la Serie A, el mercado enterprise, la estabilización soñada por el CTO. Ambos futuros están a una distancia similar pero en direcciones opuestas.

Hay dos centros que compiten: el CEO tira del mapa hacia enterprise, el CTO tira hacia calidad. Es un problema de mesa en actores pero de mapa en consecuencias (vida o muerte en 7 meses).

La perspectiva oscila entre CEO y CTO — y cada uno oculta lo que el otro ve.

### CRUZAR — forma × perspectiva

Si te acercas, ves el caos diario: juniors parchando bugs, clientes pidiendo features custom, un CTO quemado. Si te alejas, ves una empresa que pierde 8% de clientes al mes y no tiene tracción para capital.

No hay simetría. El lado "producto" está sobrecargado de problemas. El lado "mercado" está casi vacío. Esos 3 clientes grandes que generan el 30% del ingreso ocupan probablemente el 60-70% del esfuerzo de desarrollo.

Zona vacía crítica: el espacio entre CEO y CTO. No se hablan fuera de reuniones formales. Esa zona vacía es el vacío estructural más peligroso del mapa.

### LENTE L1 — Topografía

Pico: la urgencia temporal (7 meses de runway). Valle profundo: la relación CEO-CTO. Pendiente peligrosa: churn 8% mensual = ~6 clientes/mes perdidos. Meseta: la discusión pivotar-vs-estabilizar. Llevan meses sin moverse. Energía gastada en discusión, no ejecución.

### LENTE L2 — Fronteras

La frontera producto actual → enterprise no existe como camino construido. No hay puente, no hay gradiente. Es un salto.

Las fronteras del equipo son frágiles: 3 juniors, 1 diseñador part-time. La retención es una frontera que se disuelve.

Algo que debería estar dentro y está fuera: la voz de los 80 clientes (¿por qué se van realmente?). También está fuera la pregunta de si los 3 clientes grandes son ya el camino a enterprise sin pivot formal.

Algo dentro que debería estar fuera: las features custom para los 3 grandes, consumiendo recursos sin decisión estratégica sobre su dirección.

### LENTE L3 — Perspectiva

Desde arriba: el cruce burn-runway es lo único que importa. Desde dentro-CTO: certeza de que producto sólido = churn bajo. Desde dentro-CEO: ansiedad, enterprise como salvación. Desde fuera (fondos): métricas insuficientes, la discusión interna es irrelevante.

Las perspectivas NO coinciden. La pelea CEO-CTO es una pelea de perspectivas.

### LENTE L4 — Proporción

3 clientes grandes: pequeños en número, 30% de ingresos, probablemente 60-70% del esfuerzo. Debate estratégico: consume enorme energía, produce cero avance. 47 bugs / 3 juniors ≈ 188 horas de deuda técnica = más de un mes de trabajo completo solo para llegar a cero.

### INTEGRAR

La topografía (pendiente de churn, meseta decisional) explica las fronteras (no hay camino construido a enterprise). La perspectiva (mapas distintos) oculta la proporción (bugs/juniors aritméticamente inviable). El mapa dice: la dirección importa menos que la velocidad, y la velocidad es cero porque el puente entre decisores está roto.

### ABSTRAER

Barco con dos capitanes discutiendo ruta mientras el casco tiene vía de agua. Territorio disputado donde la línea del frente consume más recursos que los frentes reales.

### FRONTERA

La confianza rota post-salida del co-fundador no tiene extensión espacial pero deforma todo el mapa.

**Resumen:** El mapa espacial del SaaS revela un puente roto entre dos islas: producto actual y futuro enterprise. El agua sube mientras dos capitanes discuten la ruta. La zona vacía más peligrosa es el espacio entre CEO y CTO. El churn del 8% es una pendiente constante que arrastra clientes. La proporción 47 bugs vs. 3 juniors es aritméticamente inviable. Los 3 clientes grandes podrían ser un puente natural hacia enterprise que nadie reconoce. El debate pivotar-vs-estabilizar es una meseta de energía sin avance. Desde arriba, lo que importa es el cruce burn-runway. Desde dentro, cada protagonista confirma su tesis. Desde fuera, solo las métricas. El espacio no puede capturar la confianza rota del co-fundador.

**Firma:** El espacio revela que la discusión estratégica es una meseta que consume energía mientras el terreno se hunde. El hallazgo clave es el puente latente: los 3 clientes grandes ya son el camino a enterprise sin necesidad de pivotar.

---

## Caso 3: Cambio de carrera

### EXTRAER — mapear el espacio

Si dibujaras este problema, tendría la forma de un cruce de caminos en una montaña. La abogada está en un punto alto (180K, bufete prestigioso, 20 años) pero es una cumbre falsa — se siente como techo, no logro. Desde donde está, ve dos caminos descendentes: uno vuelve al mismo sendero (quedarse), otro baja hacia un valle diferente (ONG, 55K).

Lo que está cerca: insomnio, estrés, desilusión cotidiana. Lo que está lejos: la conversación con su marido, la decisión real, el primer día en la ONG. Lejos no por distancia objetiva sino por barreras internas.

Hay un centro: ella sola con su decisión. Y una periferia de voces: padres, amiga, marido, hijos. La perspectiva dominante es la suya interior, cargada de tensión entre deseo y deber. Oculta que su marido podría tener disposición que ella no ha explorado.

### CRUZAR — forma × perspectiva

De cerca: una mujer con insomnio de dos años. De lejos: una profesional de alto nivel en una encrucijada que afecta a cinco personas.

No hay simetría. El camino "quedarse" es conocido, pavimentado, predecible, pero tóxico. El camino "ir" es desconocido, incierto, pero potencialmente vital. Certeza negativa vs. incertidumbre con posibilidad positiva.

Zona vacía crucial: la conversación con su marido. No ha ocurrido. Contiene información potencialmente decisiva.

### LENTE L1 — Topografía

Pico: salario 180K — alto pero con grietas (insomnio, sin pasión, rechazo a socia). Valle: salud mental — 2 años de insomnio descendente. Pendiente temporal: "si no lo hago ahora, no lo haré nunca". Meseta: el bufete — esfuerzo no produce ascenso, rechazada para socia sin garantía de siguiente ciclo.

### LENTE L2 — Fronteras

La frontera bufete-ONG se percibe como rígida y binaria. ¿Hay transición gradual? ¿Consultoría medioambiental desde corporativo? La rigidez puede ser asumida, no real.

Dentro pero debería estar fuera: la opinión de los padres. A los 45 años, con familia propia, no debería tener voto decisorio.

Fuera pero debería estar dentro: su marido. La persona más directamente afectada está excluida del proceso decisional.

Los 120K ahorrados son un colchón temporal, no una fortaleza. Su duración depende de variables sin calcular.

### LENTE L3 — Perspectiva

Desde arriba: profesional cualificada con recursos suficientes para transición planificada y ventana natural (hijo mayor a universidad en 2 años).

Desde dentro: claustrofobia, pérdida de sentido, oscilación constante entre deseo y miedo, soledad decisional.

Desde fuera: lleva 3 años pensando sin dar el primer paso (hablar con su marido). La pregunta no es si debería cambiar, sino por qué lleva 3 años sin moverse.

Las tres NO coinciden. Desde arriba hay opciones. Desde dentro hay parálisis. Desde fuera hay inacción sospechosa.

### LENTE L4 — Proporción

El miedo financiero ocupa espacio enorme pero la aritmética (120K ahorrados + 40K mínimo marido + 55K ella = 95K - 21.600 hipoteca) es ajustada pero viable. Proporción distorsionada entre espacio del miedo y espacio real del riesgo.

Algo pequeño con impacto desproporcionado: la conversación con su marido. Algo grande que no produce: 3 años de pensamiento sin output decisional.

### INTEGRAR

La topografía (pico agrietado, valle de salud, meseta del bufete) explica las fronteras (percepción de rigidez binaria que puede no ser real). La perspectiva (desde dentro parálisis, desde fuera inacción) revela la proporción oculta: el miedo financiero ocupa más espacio que el riesgo real, y la conversación no tenida es el vacío que mantiene la parálisis.

### ABSTRAER

Emigrante que mira la tormenta posible sin ver que la tierra bajo sus pies se erosiona. Persona en edificio en llamas que no salta porque la caída parece peor que el fuego.

### FRONTERA

El espacio no puede capturar el sentido. La diferencia entre una vida con propósito y una sin él no tiene extensión, pero es lo que realmente está en juego.

**Resumen:** El mapa espacial del cambio de carrera revela una bifurcación en montaña donde el pico actual tiene grietas profundas y el camino alternativo desciende hacia territorio desconocido. La distorsión proporcional central es que el miedo financiero ocupa más espacio mental que el riesgo real. El mayor vacío del mapa es la conversación no tenida con su marido. La frontera bufete-ONG se percibe como rígida y binaria pero podría ser permeable. Los padres están dentro del mapa decisional cuando deberían estar fuera. Tres años de pensamiento sin acción es una masa sin output. Las perspectivas divergen: arriba hay recursos, dentro hay parálisis, fuera hay inacción sospechosa. El espacio no puede capturar la dimensión del sentido.

**Firma:** El espacio revela que el miedo ocupa más territorio que el peligro real, y que la mayor zona vacía del mapa — la conversación con el marido — es también la que más potencial transformador tiene.

---

## Loop test (P06)

**Caso elegido: Startup SaaS**

La segunda pasada reveló:
1. Los 80 clientes tratados como número agregado son un territorio con mapa interno propio: zonas de riesgo, rescatabilidad, motivos diferenciados de churn.
2. El "puente latente" de los 3 clientes grandes fue nombrado pero no explorado internamente: ¿las features custom son generalizables o callejones sin salida?
3. El análisis priorizó el conflicto humano (CEO-CTO) sobre la aritmética del churn por sesgo de interés narrativo-espacial del analista.

**¿Genuinamente nuevo?** Sí. La primera pasada mapeó la topología macro. La segunda reveló que ciertos objetos (clientes, puente latente) estaban tratados como puntos sin extensión interna cuando son territorios que necesitan su propio mapa. También reveló un sesgo del analista.

## Patrón cross-case

Distorsión proporcional entre espacio mental ocupado y espacio real del riesgo/oportunidad. En los 3 casos, lo que llena el mapa mental del sujeto no es lo más importante espacialmente, y hay un objeto pequeño e invisible (sillón vacío, puente latente, conversación no tenida) con más poder transformador que los objetos grandes y visibles.

## Saturación (P07)

Una tercera pasada aportaría, pero con rendimiento decreciente. Pasaría de cartografía estratégica a cartografía operativa (sub-mapas internos de objetos). Probablemente más productivo pasar a otra inteligencia que opere en esos sub-mapas.

## Firma final

La inteligencia espacial ve lo que ninguna otra puede: la forma del problema como estructura visual, las distorsiones de proporción entre lo que ocupa espacio mental y lo que realmente importa, y los vacíos — zonas del mapa sin explorar que contienen la información más valiosa. Donde otras inteligencias ven datos, la espacial ve geometría, y esa geometría revela que la solución casi nunca está donde el sujeto mira.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/ESTETICA.md
============================================================

# INT-15: ESTÉTICA — RESULTADOS FASE 1

---

## Caso 1: Clínica Dental

### EXTRAER — mapear coherencia

**¿Algo "suena raro"?** Sí: la propuesta de solución. El hombre tiene un sillón vacío el 40% del tiempo y su respuesta es comprar dos sillones más. Hay una incongruencia formal entre "lo que ya tengo no lo lleno" y "necesito más de lo que ya tengo". Eso suena raro antes de que cualquier análisis lo confirme — como un acorde mal resuelto.

**¿Hay elegancia?** La elegancia está en la estructura familiar que se repite: padre-hijo, infarto a los 52, 70h/semana → hijo ahora 38, 60h/semana, misma trayectoria. Hay una simetría narrativa dolorosa pero limpia. Es un patrón que se puede ver con los ojos cerrados.

**¿Hay disonancia?** Masiva. Dice "mis hijos preguntan por mí" y propone abrir sábados. Dice "quiero crecer" pero no llena lo que tiene. La esposa dice "no paras" y él responde "voy a parar menos". Cada acción propuesta amplifica exactamente lo que produce el dolor.

**¿Simetría o desequilibrio?** El problema es profundamente asimétrico: toda la energía va hacia el negocio, nada vuelve hacia la vida. Es un sistema sin retroalimentación estética — produce pero no alimenta. Y la solución propuesta acentúa esa asimetría.

**¿Forma del problema y forma de la solución son coherentes?** No. El problema tiene forma de agotamiento (demasiado con pocos recursos), y la solución propuesta tiene forma de expansión (más con más recursos). Son formas contrarias. El problema pide contracción inteligente; la solución propone dilatación bruta.

### CRUZAR — forma × contenido

**¿Lo que dice y cómo lo dice son coherentes?** No. Cuando dice "puedo subir a 65.000€/mes" está usando lenguaje de oportunidad. Pero el contexto — hijos ausentes, padre infartado, vacaciones inexistentes — es lenguaje de emergencia. Hay una fractura entre el tono (ambicioso) y el contenido (desesperado).

**¿La solución repite la forma del problema?** Exactamente. El problema es "hago demasiado con lo que tengo". La solución es "haré más con más". Es la misma forma escalada. El patrón no se rompe, se amplifica. Estéticamente, es como resolver una disonancia tocando la misma nota más fuerte.

**¿Hay algo bello en el problema?** Sí. La repetición generacional padre-hijo tiene la estructura de una tragedia clásica: el héroe repite el destino que intenta evitar. Hay belleza en la simetría del patrón, aunque el contenido sea doloroso. Es la misma elegancia que hace que Edipo sea bello siendo horrible.

**¿La complejidad es necesaria o es ruido?** Casi toda la complejidad financiera (hipoteca, crédito bancario, facturación) es ruido que distrae del problema simple: un hombre reproduce la vida de su padre sabiendo cómo termina.

### LENTE L1 — Armonía

**¿Las partes se complementan o se contradicen?** Se contradicen sistemáticamente. Los datos familiares (esposa, hijos, padre) empujan hacia la contracción. Los datos financieros (banco, facturación, sillones) empujan hacia la expansión. No hay armonía; hay dos melodías en tonalidades incompatibles.

**¿Hay proporción?** No. Los datos financieros ocupan el centro de la narrativa, pero los datos humanos tienen más peso existencial. Hay una desproporción entre lo que se mide (euros) y lo que importa (presencia, salud, relación).

**¿Algo sobra? ¿Algo falta?** Sobra la oferta del banco — es una distracción que agrega complejidad sin agregar información. Falta una conversación real con la esposa que no sea queja sino decisión conjunta.

### LENTE L2 — Tensión

**Tensión productiva:** La tensión entre el legado del padre y la vida propia. Es una tensión que podría generar una decisión transformadora: "no seré mi padre". Si se escucha, produce energía para el cambio.

**Tensión destructiva:** La tensión entre trabajar más y estar más ausente. Es un bucle sin salida que gasta energía sin producir nada nuevo. Cada iteración deja menos margen para el cambio.

**¿Se resuelve o es permanente?** Es resoluble pero solo con una ruptura de patrón. Si sigue la inercia, la tensión productiva se convierte en destructiva: el reconocimiento del patrón paterno se vuelve resignación.

### LENTE L3 — Simplicidad

**Versión más simple:** Un hombre repite la vida de su padre y no sabe cómo parar.

**¿Qué se puede quitar?** Los sillones, el banco, las métricas de facturación. Todo eso es escenografía.

**¿Qué queda?** Un hijo que camina hacia el infarto de su padre con los ojos abiertos.

### LENTE L4 — Resonancia

**¿Reacción inmediata?** Sí: tristeza. Antes de analizar nada, hay una sensación de inevitabilidad trágica. Es la resonancia de algo que se ve venir.

**¿Es informativa?** Muy informativa. La tristeza dice: "esto ya lo sé, esto ya lo he visto". Dice que el final está escrito a menos que alguien cambie el guion. El análisis posterior confirma lo que la primera impresión ya sabía.

**¿Hay verdad en la primera impresión que el análisis ignora?** Sí. El análisis puede racionalizar ("quizás los números funcionan"), pero la primera impresión ve lo que los números no miden: un hombre atrapado.

### INTEGRAR

Armonía (ausente), tensión (bucle destructivo), simplicidad (repetición generacional) y resonancia (tristeza anticipatoria) apuntan exactamente al mismo sitio: la expansión es la forma de seguir sin decidir. Los cuatro ejes convergen en que la respuesta no está en los sillones sino en la conversación que no ha tenido — consigo mismo y con su esposa.

### ABSTRAER

¿Los problemas bellos tienen mejores soluciones? Este problema ES bello — la simetría generacional es elegante en su horror. Y sí, esa belleza apunta directamente a la solución: si ves el patrón, puedes romperlo. La belleza del problema hace visible la salida. Un problema feo (más datos, más ruido) ocultaría esa salida.

### FRONTERA

La estética aquí no es sesgo: es detector de patrones. La disonancia entre la solución propuesta y el problema real es genuinamente informativa. Pero el riesgo existe: la belleza de la narrativa trágica podría hacer que el análisis prefiera la historia limpia sobre la realidad compleja. Quizás la vida real tiene ruido que la estética descarta demasiado rápido.

**Resumen:** La inteligencia estética revela una incongruencia formal masiva en este caso: la solución propuesta (expandir) tiene la forma exacta del problema (sobreextensión). Un sillón vacío al 40% y la respuesta es comprar dos más — es una disonancia audible antes de cualquier análisis. La estructura más elegante del caso es la repetición generacional padre-hijo: infarto a los 52 con 70h/semana → hijo a los 38 con 60h/semana, misma trayectoria. Es una tragedia clásica donde el héroe camina hacia el destino que conoce. La complejidad financiera (banco, crédito, facturación) es escenografía que distrae del problema simple: un hombre que reproduce la vida de su padre sabiendo cómo termina. Las cuatro lentes convergen: la armonía está ausente (familia y negocio empujan en direcciones opuestas), la tensión productiva existe pero se degrada (legado paterno como catalizador posible), la simplicidad apunta a una frase (hijo camina hacia el infarto del padre), y la resonancia produce tristeza anticipatoria que es más informativa que cualquier métrica. La estética funciona aquí como detector de patrones, no como sesgo hacia lo bonito.

**Firma:** La estética detecta que la solución propuesta es isomórfica al problema — misma forma escalada — y que la simetría generacional padre-hijo tiene la estructura de una tragedia clásica donde el héroe camina hacia el destino que conoce.

---

## Caso 2: Startup SaaS

### EXTRAER — mapear coherencia

**¿Algo "suena raro"?** Sí: dos cosas. Primera, el CEO quiere pivotar a enterprise porque "los restaurantes no pagan suficiente", pero el problema no es que los restaurantes no paguen — es que se van (churn 8%). Segunda, el 30% de ingresos viene de 3 clientes grandes que pidieron features custom, lo cual significa que la empresa ya está pivotando de facto sin llamarlo así. Hay una disonancia entre la narrativa ("debemos pivotar") y la realidad ("ya estamos pivotando, pero mal").

**¿Hay elegancia?** La elegancia está en la frase del CTO: "Si el producto fuera sólido, el churn bajaría solo." Tiene la estructura de una verdad simple que no necesita argumentación adicional. Es una proposición limpia.

**¿Hay disonancia?** Múltiple. CTO y CEO proponen soluciones que son internamente coherentes pero mutuamente excluyentes con el mismo equipo y runway. La partida del co-fundador técnico — "diferencias de visión" — se repite ahora entre CTO y CEO: el mismo patrón de fractura que no se resolvió, se está replicando.

**¿Simetría o desequilibrio?** Profundamente desequilibrado. El lado técnico (47 bugs, equipo junior, deuda técnica) carga todo el peso. El lado comercial (pivot enterprise) flota libre sin fundamento en capacidad real. Es como un edificio donde la mitad tiene cimientos y la otra está en el aire.

**¿Forma del problema y forma de la solución coherentes?** No. El problema tiene forma de descomposición (cosas que se caen: cofundador, empleados, clientes, calidad). La solución del CEO tiene forma de expansión (ir a enterprise). La solución del CTO tiene forma de reparación (arreglar bugs). Ninguna tiene la forma del problema real, que es de integración (juntar las piezas que se separan).

### CRUZAR — forma × contenido

**¿Lo que dice y cómo lo dice son coherentes?** El CTO dice "necesito estabilizar" pero trabaja 70h/semana — su forma de actuar es la de alguien en modo supervivencia, no en modo estabilización. El CEO dice "crecer o morir" — su forma retórica es de urgencia existencial, pero 7 meses de runway permite al menos 2-3 meses de reflexión. Ambos usan formas más dramáticas que la realidad exige.

**¿La solución repite el patrón?** Sí. El patrón del problema es fragmentación (cofundador se va, equipo se va, clientes se van). La solución propuesta (pivotar) es otra forma de fragmentación: abandonar el mercado actual antes de entender por qué falla. Estabilizar también repite un patrón: reparar lo roto sin preguntarse si la estructura merece reparación.

**¿Hay algo bello en el problema?** Sí: la tensión CTO-CEO es un conflicto estéticamente perfecto porque ambos tienen razón parcial y ambos están ciegos a lo que el otro ve. Es una tragedia de perspectivas complementarias que no se comunican. Y la frase del CTO tiene la belleza de una verdad comprimida que el CEO no puede escuchar.

**¿La complejidad es necesaria o es ruido?** Los 47 bugs, el número exacto de clientes, el churn porcentual — son datos útiles pero la complejidad real es relacional (CTO vs CEO) no métrica. Hay ruido numérico que distrae de la fractura humana.

### LENTE L1 — Armonía

**¿Las partes se complementan o se contradicen?** Se contradicen. CTO y CEO son las dos mitades de un todo que debería funcionar (técnico + negocio), pero están desacoplados. Los 3 clientes enterprise son armónicos con la visión del CEO pero disarmónicos con la capacidad real. Nada se complementa porque no hay conversación que integre.

**¿Proporción?** Desproporcionada. La discusión estratégica (pivotar vs estabilizar) ocupa toda la atención pero la causa raíz (equipo roto, comunicación rota) no tiene espacio.

**¿Algo sobra? ¿Algo falta?** Sobra la búsqueda de Serie A en este estado — es añadir un stakeholder externo a un sistema que no puede gestionar los internos. Falta un espacio de decisión compartida CTO-CEO que no sea reunión formal.

### LENTE L2 — Tensión

**Tensión productiva:** La tensión CTO-CEO, si se canaliza, contiene la respuesta: estabilizar PARA poder pivotar. La complementariedad de visiones es energía potencial no utilizada.

**Tensión destructiva:** La tensión silenciosa — "apenas se hablan fuera de reuniones formales" — es la que gasta sin producir. No es desacuerdo productivo, es evitación. El patrón es idéntico al que llevó a la salida del otro cofundador.

**¿Se resuelve?** Solo si se convierte en conversación explícita. La tensión tácita es siempre destructiva. La tensión declarada puede ser productiva.

### LENTE L3 — Simplicidad

**Versión más simple:** Dos personas que necesitan escucharse no se hablan.

**¿Qué se puede quitar?** Los fondos de Serie A, las métricas de churn exactas, el pivot vs estabilizar como debate estratégico.

**¿Qué queda?** Una empresa que se rompe por el mismo sitio por segunda vez porque la fractura original nunca se reparó.

### LENTE L4 — Resonancia

**¿Reacción inmediata?** Frustración. Se siente que hay algo aquí que funciona (producto con tracción, clientes que pagan) pero que se está desperdiciando por una fractura que nadie aborda directamente.

**¿Es informativa?** Sí. La frustración dice: "hay potencial que se tira". A diferencia del caso dental donde hay tristeza (inevitabilidad), aquí hay irritación (desperdicio evitable).

**¿Verdad en la primera impresión?** Sí: la primera impresión dice "hablen". El análisis posterior puede complicar eso con métricas y estrategias, pero la verdad simple es que dos personas inteligentes no se comunican.

### INTEGRAR

Armonía (ausente entre CTO y CEO), tensión (productiva si se canaliza, destructiva en su forma actual), simplicidad (dos personas que no se hablan), resonancia (frustración por desperdicio) — todo converge en que el problema no es estratégico (pivot vs estabilizar) sino relacional (comunicación rota que replica el patrón de la primera fractura).

### ABSTRAER

¿Problemas bellos = mejores soluciones? Este problema tiene una belleza trágica (perspectivas complementarias que no se encuentran) que sí apunta a la solución (encontrarse). Pero también tiene un lado feo — 47 bugs, equipo junior, churn — que la estética quiere ignorar porque no es elegante. Aquí la belleza apunta correctamente al centro pero deja fuera la periferia necesaria.

### FRONTERA

La estética acierta al identificar que el debate pivot-vs-estabilizar es una falsa dicotomía que repite la forma del problema. Pero podría equivocarse al minimizar la urgencia real (7 meses de runway). La belleza de la reducción "dos personas que no se hablan" es potente pero incompleta: quizás se hablan y no están de acuerdo, y eso es legítimo.

**Resumen:** La inteligencia estética detecta dos disonancias fundamentales. Primera: el CEO quiere pivotar porque "los restaurantes no pagan", pero el problema real es que los clientes se van — la narrativa del pivot no encaja con los datos. Segunda: la empresa ya pivotea de facto (30% de ingresos de 3 clientes enterprise), pero sin reconocerlo ni gestionarlo. La estructura más elegante es la verdad comprimida del CTO ("si el producto fuera sólido, el churn bajaría solo") y la tragedia de perspectivas complementarias que no se comunican. La forma del problema es descomposición (cofundador, empleados, clientes, calidad — todo se separa), y ninguna solución propuesta tiene forma de integración. Estabilizar repara piezas; pivotar abandona piezas. Ninguna recompone. La simplificación máxima: dos personas que necesitan escucharse no se hablan, replicando la fractura que ya destruyó la primera dupla fundadora. La resonancia produce frustración, no tristeza — la sensación de potencial desperdiciado por una ruptura comunicativa evitable. La estética acierta al mostrar que pivot-vs-estabilizar es falsa dicotomía que repite la forma del problema, pero podría subestimar la urgencia real del runway.

**Firma:** La estética detecta que pivot-vs-estabilizar es una falsa dicotomía que repite la forma del problema (fragmentación), y que la fractura cofundador original se está replicando en la relación CTO-CEO como patrón no resuelto.

---

## Caso 3: Cambio de carrera

### EXTRAER — mapear coherencia

**¿Algo "suena raro"?** Sí: lleva 3 años pensando y no ha hablado con su marido. La desproporción temporal es estéticamente chirriante. Tres años es tiempo suficiente para haber tenido la conversación más difícil. Que no lo haya hecho sugiere que la conversación no es el obstáculo — es el miedo a lo que la conversación revelaría.

**¿Hay elegancia?** Hay una simetría dolorosa entre "rechazada para socia" y "quizá el próximo ciclo". Es la forma exacta de la esperanza que mantiene atada. Es elegante como estructura narrativa: la zanahoria siempre a un ciclo de distancia. También hay elegancia en la yuxtaposición de dos frases: "si no lo hago ahora, no lo haré nunca" contra "no puedo arriesgar la estabilidad de mis hijos". Ambas son verdaderas y ambas se cancelan.

**¿Hay disonancia?** El insomnio de 2 años diagnosticado como "estrés laboral" convive con la decisión de quedarse en la fuente del estrés. La forma es: sé qué me enferma, no cambio nada, me quejo de estar enferma. Es una disonancia funcional — funciona como mecanismo pero es incoherente como sistema.

**¿Simetría o desequilibrio?** El caso tiene una simetría bilateral casi perfecta: cada argumento para irse tiene un contra-argumento para quedarse, y viceversa. Esto le da una forma de balanza en equilibrio — lo cual es hermoso como estructura pero paralizante como vivencia.

**¿Forma problema-solución coherentes?** El problema tiene forma de parálisis (fuerzas iguales y opuestas). La solución implícita (elegir una dirección) requiere romper la simetría. Pero ella no propone una solución — presenta su parálisis como el problema. La forma del problema y la ausencia de solución son coherentes: la simetría produce estancamiento.

### CRUZAR — forma × contenido

**¿Lo que dice y cómo lo dice son coherentes?** "Si no lo hago ahora, no lo haré nunca" tiene forma de urgencia. "No puedo arriesgar la estabilidad de mis hijos" tiene forma de prudencia. Ambas son sinceras, pero ponerlas juntas produce una coherencia de parálisis: la urgencia y la prudencia se anulan. Lo que realmente dice es: "necesito que alguien rompa el empate."

**¿La solución repite la forma del problema?** No hay solución propuesta, solo oscilación. Y la oscilación ES la forma del problema. Así que sí: la forma de abordar el problema (dar vueltas) replica la forma del problema (equilibrio paralizante).

**¿Hay algo bello?** Profundamente. La estructura de las dos frases enfrentadas — "si no ahora, nunca" vs "no puedo arriesgar" — tiene la belleza de un koan zen: dos verdades irreconciliables que señalan hacia un nivel superior de comprensión donde ambas coexisten. La belleza está en la paradoja misma.

**¿Complejidad necesaria o ruido?** Los padres dicen "estás loca", la amiga dice "por fin vive". Son ecos externos que amplifican la oscilación sin agregar información nueva. Son ruido estético: voces que repiten lo que ella ya sabe. El insomnio y el rechazo para socia son señal genuina. Lo demás es eco.

### LENTE L1 — Armonía

**¿Las partes se complementan o se contradicen?** Se contradicen con simetría casi perfecta. Cada dato pro-cambio (insomnio, pérdida de pasión, rechazo socia) tiene un dato contra-cambio (hipoteca, hijos universidad, marido irregular). La simetría es tan perfecta que sugiere algo: quizás la parálisis no es accidental sino funcional — le permite no decidir.

**¿Proporción?** Los datos financieros (180K, 55K, 120K ahorros, hipoteca) están sobrerepresentados. Los datos emocionales (insomnio, pasión perdida) están subrepresentados en peso aunque llevan 3 años de evidencia. Hay desproporción entre lo que se mide y lo que duele.

**¿Sobra? ¿Falta?** Sobran los padres y la amiga (ruido). Falta la conversación con el marido — y su ausencia es el dato más informativo del caso.

### LENTE L2 — Tensión

**Tensión productiva:** La frase "si no ahora, nunca" es una tensión temporal que puede forzar una decisión. El rechazo para socia es una señal del sistema que podría leerse como liberación en lugar de como fracaso.

**Tensión destructiva:** La oscilación de 3 años es tensión pura sin resolución — gasta energía psíquica sin producir movimiento. El insomnio es la manifestación física de tensión sostenida sin canal de descarga.

**¿Se resuelve?** Solo con una acción que rompa la simetría. Cualquier acción. La conversación con el marido sería la ruptura de simetría mínima necesaria.

### LENTE L3 — Simplicidad

**Versión más simple:** Una mujer sabe lo que quiere y no se atreve a pedirlo.

**¿Qué se puede quitar?** Los padres, la amiga, las cifras exactas de salario y ahorro, el "quizá el próximo ciclo".

**¿Qué queda?** El miedo a tener la conversación que haría real lo que ya sabe.

### LENTE L4 — Resonancia

**¿Reacción inmediata?** Reconocimiento. No tristeza (caso dental) ni frustración (caso SaaS). Reconocimiento: "conozco a esta persona." La resonancia es de familiaridad — este patrón es universal.

**¿Es informativa?** Muy. El reconocimiento dice: esto es humano, no es patológico. No necesita un análisis — necesita un empujón. Pero también dice: la parálisis tiene función protectora. No es estupidez, es miedo inteligente.

**¿Verdad en la primera impresión?** La primera impresión dice: "ya decidiste, solo necesitas permiso." El análisis puede matizar, pero la verdad simple es que 3 años de rumiar, insomnio y pérdida de pasión son la decisión expresada en forma de síntoma.

### INTEGRAR

Armonía (simetría paralizante que podría ser funcional), tensión (oscilación destructiva de 3 años), simplicidad (sabe lo que quiere, no se atreve a pedirlo), resonancia (reconocimiento universal de quien posterga lo que sabe) — convergen en que el problema no es la decisión sino el acto de pronunciarla. La balanza está equilibrada solo en apariencia; el cuerpo (insomnio) ya decidió.

### ABSTRAER

¿Problemas bellos = mejores soluciones? Este problema es estéticamente bello — la paradoja de las dos frases enfrentadas, la simetría perfecta de argumentos — y esa belleza apunta directamente a la solución: romper la simetría. La estética del equilibrio perfecto señala que el equilibrio es artificial. Un problema feo (caótico, asimétrico) no revelaría con tanta claridad que la parálisis es una elección disfrazada de dilema.

### FRONTERA

La estética funciona aquí como reveladora de forma: la simetría perfecta de argumentos pro/contra es sospechosa en sí misma y apunta a que la parálisis es fabricada, no genuina. Pero el riesgo es que la lectura estética ("ya decidiste") pueda presionar hacia una dirección que ignore riesgos reales. La belleza de la narrativa "atrévete a cambiar" no valida el cambio por sí misma.

**Resumen:** La inteligencia estética revela que este caso tiene la forma de una simetría paralizante: cada argumento para irse tiene un contra-argumento exacto para quedarse, produciendo un equilibrio bilateral casi perfecto que es hermoso como estructura y destructivo como vivencia. El hallazgo más profundo es que la ausencia de conversación con el marido tras 3 años de deliberación es el dato más informativo del caso — no es que no haya podido hablar, es que hablar haría real lo que ya sabe. La elegancia del caso reside en las dos frases enfrentadas ("si no ahora, nunca" vs "no puedo arriesgar") que funcionan como un koan: dos verdades irreconciliables que señalan un nivel superior donde ambas coexisten. La reducción esencial: una mujer sabe lo que quiere y no se atreve a pedirlo. La resonancia es de reconocimiento universal — patrón humano que no necesita análisis sino ruptura de simetría. El cuerpo ya decidió: 2 años de insomnio son la decisión expresada en síntoma. La estética acierta al señalar que la parálisis es una elección disfrazada de dilema, pero podría sesgar hacia "atrévete" sin validar los riesgos reales.

**Firma:** La estética detecta que la simetría perfecta de argumentos pro/contra es sospechosa y funcional — permite no decidir — y que el cuerpo (insomnio de 2 años) ya tomó la decisión que la mente no se atreve a pronunciar.

---

## Loop test (P06)

**Caso elegido: Cambio de Carrera**

Aplico las preguntas de INT-15 a mi propio output del caso 3:

**EXTRAER sobre mi output:** ¿Algo suena raro en mi análisis? Sí: soy demasiado limpio. Presento la "simetría paralizante" como si fuera un hallazgo unívoco, pero la simetría real del caso podría no ser perfecta — quizás los argumentos para quedarse son genuinamente más pesados (hijos, hipoteca, universidad) y yo les resté importancia para que la estructura estética quedara más elegante. Hay una disonancia en mi propio output: uso la belleza formal como argumento, pero podría estar cayendo exactamente en la trampa que la FRONTERA señala — sesgar hacia la narrativa bonita.

**¿Hay elegancia en mi output?** Demasiada. Las frases como "el cuerpo ya decidió" y "una mujer sabe lo que quiere" son compactas y resonantes, pero quizás sacrifican complejidad por belleza. ¿Y si realmente no sabe lo que quiere? ¿Y si el insomnio no es decisión somática sino ansiedad genérica?

**¿Mi solución repite la forma del problema?** Potencialmente sí. El caso tiene forma de certeza disfrazada de dilema. Mi análisis tiene forma de certeza disfrazada de exploración — llego a una conclusión clara ("ya decidiste") mientras finjo explorar. La misma estructura que critico.

**Hallazgo nuevo genuino:** Mi análisis asume que "saber lo que quiere" es equivalente a "querer irse al derecho medioambiental". Pero quizás lo que quiere es no estar donde está — no necesariamente ir donde imagina. La dirección del escape podría estar tan idealizada como la permanencia. La primera pasada ignoró esto porque la estructura "sabe y no se atreve" es más elegante que "huye sin saber hacia dónde". Este segundo hallazgo es genuinamente nuevo.

---

## Patrón cross-case

Hay un patrón que aparece en los 3 casos independientemente del dominio: **la solución propuesta (o la forma de abordar el problema) es isomórfica al problema mismo**. En el caso dental, expandir repite la sobreextensión. En el SaaS, pivotar repite la fragmentación. En el cambio de carrera, oscilar repite la parálisis. En los tres casos, el sujeto aborda el problema con la misma forma que lo crea. Esto no es coincidencia — es un hallazgo estético estructural: las personas tienden a proponer soluciones que tienen la misma forma geométrica que sus problemas, por lo que no pueden resolverlos desde dentro de esa forma.

---

## Saturación (P07)

¿Una tercera pasada aportaría algo? Parcialmente. El loop test reveló un sesgo en mi propio análisis (preferir la narrativa limpia sobre la complejidad real), y una tercera pasada podría encontrar sesgos adicionales en el loop test mismo. Pero estimo que la tercera pasada produciría refinamientos de segundo orden, no hallazgos estructurales nuevos. Saturación al 75-80%.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/ESTRATEGICA.md
============================================================

# RESULTADOS F1-05: INT-05 ESTRATÉGICA

**Fecha:** 2026-03-07
**Inteligencia:** INT-05 — Estratégica
**Objetos:** posición, recursos, movimientos, ventanas temporales, opciones
**Firma general:** ANTICIPACIÓN — pensar dos movimientos adelante

---

## Caso 1: Clínica Dental

### EXTRAER — mapear posición

**¿Dónde estás ahora — fuerte o débil?** Posición mixta con tendencia a débil. El negocio genera caja positiva (7.000€/mes netos), lo cual es fuerza operativa. Pero la debilidad es estructural: el propietario ES el activo principal, trabaja 60h/semana, no tiene vacaciones en 2 años, y tiene una deuda de 280.000€ que lo ancla. Su posición es la de alguien que tiene un negocio rentable pero que no tiene un negocio que funcione sin él. Eso no es fortaleza — es dependencia disfrazada de propiedad.

**¿Qué recursos tienes?** Dinero: 7.000€/mes de margen libre tras costes y cuota. Tiempo: prácticamente cero — 2.500h/año ya consumidas, sin holgura. Personas: 1 asociado (recurso parcial, no controla su permanencia), esposa (recurso emocional en tensión). Información: conoce su mercado local, tiene flujo de pacientes. Infraestructura: 3 sillones, 1 vacío el 40% del tiempo. Crédito disponible del banco.

**¿Qué opciones de movimiento existen?** (A) Expandir: aceptar crédito, ampliar a 5 sillones, abrir sábados, contratar otro dentista. (B) Optimizar: llenar el tercer sillón antes de ampliar. (C) Reducir: delegar más al asociado, trabajar menos horas, aceptar menos margen. (D) Vender o asociarse: buscar socio capitalista que compre parte de la clínica. (E) No hacer nada.

**¿Cuáles son reversibles y cuáles no?** Expandir (A) es difícilmente reversible: nuevo crédito, nueva infraestructura, compromisos laborales. Optimizar (B) es reversible. Reducir (C) es reversible. Vender parte (D) no es reversible. No hacer nada (E) es reversible a corto plazo pero irreversible a largo si el deterioro personal avanza.

**¿Quién más está en el tablero?** El banco: quiere colocar crédito, gana con la expansión independientemente de que al dentista le vaya bien. El asociado: tiene sus propios intereses, puede irse si las condiciones cambian. La esposa: quiere presencia familiar, tiene poder de veto emocional. Los hijos: actores pasivos, absorben consecuencias. Pacientes: quieren servicio, irán a otro si no lo obtienen. Competidores locales: no mencionados, pero existen.

**¿Qué sabes tú que ellos no?** El dentista sabe que su cuerpo y su matrimonio están al límite — el banco no sabe eso ni le importa. Sabe que su padre tuvo un infarto en circunstancias similares. **¿Qué saben ellos que tú no?** El banco sabe las condiciones reales del crédito, los tipos de interés futuros, y la tasa de mortalidad de clínicas dentales apalancadas. La esposa sabe cuánto más puede aguantar antes de tomar decisiones propias.

### CRUZAR — posición × recursos

**Recursos que se agotan al usarlos:** Tiempo personal (irrecuperable), salud, relación matrimonial, infancia de los hijos (ventana que cierra). El dinero del crédito se agota, pero si genera retorno, se regenera. El tiempo y las relaciones no se regeneran.

**¿Varias opciones compiten por el mismo recurso escaso?** Sí. Expandir y Optimizar ambos requieren el recurso más escaso: su tiempo y atención. Expandir también consume crédito y margen de seguridad. La expansión y la vida familiar compiten por el mismo recurso (horas del día) y es suma cero.

**¿Recurso que NO estás usando?** El tercer sillón vacío el 40% del tiempo. Eso es capacidad instalada sin explotar. Antes de cualquier expansión, la pregunta obvia es por qué ese sillón está vacío. Si no puede llenar 3, ¿por qué quiere 5?

**¿Movimiento que parece opción pero no lo es?** "Abrir sábados y contratar otro dentista" para subir a 65.000€/mes suena a opción, pero es una trampa: requiere MÁS horas suyas para supervisar, gestionar, formar al nuevo dentista. En la práctica, es la misma dirección multiplicada — no es una opción diferente, es más de lo mismo con más apalancamiento.

### LENTE L1 — Posicional

**¿Tu posición mejora o empeora si no haces nada?** Empeora lentamente. El matrimonio se deteriora, la salud se degrada, los hijos crecen sin padre. La clínica sola probablemente se mantiene estable financieramente a corto plazo, pero el activo principal (él) se deprecia. No hacer nada es una decisión de desgaste.

**¿Hay ventana temporal?** Varias. Los hijos tienen 4 y 6 años — la ventana de presencia parental significativa es ahora, no en 5 años. El crédito bancario tiene una ventana (los bancos ofrecen cuando pueden, no siempre). La salud tiene ventana: su padre tuvo infarto a los 52, él tiene 38 — tiene 14 años o menos antes de que la genética y el estilo de vida se crucen.

**¿Tu posición es fácil de atacar?** Sí. Si el asociado se va, la clínica pierde capacidad inmediatamente. Si él enferma, todo se para. No tiene redundancia en la pieza más crítica. Un competidor que abra cerca con precios agresivos lo puede desestabilizar porque su margen es delgado (15.5%).

### LENTE L2 — Secuencial

**¿En qué orden tendrían que pasar las cosas?** Primero: entender por qué el tercer sillón está vacío el 40%. Segundo: llenar esa capacidad sin añadir infraestructura. Tercero: una vez llena la capacidad, evaluar si la demanda justifica ampliar. Cuarto: si amplía, hacerlo con un modelo donde él NO sea necesario en sillón.

**¿Qué DEBE hacerse antes?** Llenar el sillón 3 antes de pensar en sillones 4 y 5. Hablar con la esposa antes de tomar cualquier decisión financiera. Estas dos son precondiciones no negociables.

**¿Qué se desbloquea con el primer movimiento?** Llenar el tercer sillón genera datos reales: ¿hay demanda? ¿el asociado puede absorber más? ¿los ingresos suben proporcionalmente? Con esos datos, la decisión de expandir deja de ser especulativa.

**¿Hay movimiento que cierre opciones futuras?** Aceptar el crédito cierra la opción de reducir ritmo, porque las cuotas suben. También cierra la opción de vender fácilmente (más deuda = menos atractivo para comprador). Es el movimiento más irreversible del tablero.

### LENTE L3 — Adversarial

**¿Qué hará el otro si tú haces X?** Si acepta el crédito y expande, el banco gana intereses — hará todo por facilitar. La esposa probablemente agota su paciencia — puede poner ultimátum. El asociado puede pedir mejores condiciones sabiendo que el dentista estará más apalancado y más dependiente. Si reduce horas, el banco pierde un cliente de crédito (le da igual). La esposa gana. El asociado puede sentirse más o menos presionado según cómo se redistribuya.

**¿Hay forma de que ambos ganen?** Sí. Si optimiza antes de expandir, puede ganar margen sin ganar deuda. Si habla con la esposa e involucra la decisión, gana alianza en vez de resistencia. No es suma cero — es suma cero solo si piensa exclusivamente en facturación.

**¿Quién pierde más esperando?** Él pierde más esperando que nadie más. El banco no pierde nada. La esposa pierde paciencia. Los hijos pierden infancia. El tiempo corre contra él en todas las dimensiones excepto la financiera.

### LENTE L4 — Opcionalidad

**¿Puedes moverte sin comprometerte?** Sí. Puede investigar por qué el sillón 3 está vacío el 40%, contratar una higienista para liberar su tiempo de tareas delegables, hablar con la esposa — todo esto es exploración sin compromiso irreversible.

**¿Cuánto vale mantener opciones abiertas vs decidir ahora?** Mantener opciones vale mucho. El crédito del banco probablemente seguirá disponible en 6 meses. La información que gane llenando el tercer sillón es irremplazable y solo cuesta tiempo.

**¿Movimiento barato que da información antes del caro?** Sí: llenar el tercer sillón durante 3-6 meses y medir. Coste: casi cero en dinero, algo de gestión. Beneficio informacional: enorme. Si no puede llenarlo, la expansión a 5 sillones es una fantasía peligrosa. Si lo llena, tiene datos duros para decidir.

### INTEGRAR

Las 4 lentes convergen en el mismo movimiento: **NO expandir ahora. Optimizar primero.** Posicional dice que su posición se deteriora en las dimensiones que importan (salud, familia) y expandir las acelera. Secuencial dice que hay un paso previo obligatorio (llenar sillón 3). Adversarial dice que el banco no juega a su favor. Opcionalidad dice que hay un movimiento barato (optimizar) que preserva el movimiento caro (expandir) para después, con mejor información.

### ABSTRAER

Este es un caso clásico de "trampa de crecimiento apalancado": un operador exitoso confunde facturación con bienestar, y un proveedor de crédito amplifica la ilusión. Precedentes abundan en hostelería, comercio minorista, y profesiones liberales. El patrón típico: expansión apalancada → más horas del propietario → punto de quiebre personal → crisis que destruye tanto el negocio como lo personal. Los que lo evitaron típicamente hicieron lo contrario: primero redujeron su dependencia operativa, después escalaron.

### FRONTERA

La inteligencia estratégica aquí asume que hay adversarios y que hay que optimizar posición. Pero el "adversario" más peligroso no es externo — es la narrativa interna del dentista ("si abro sábados puedo subir a 65K") que es una historia de crecimiento contada por alguien agotado. La estrategia ve el tablero externo, pero el movimiento más importante es interno: redefinir qué significa ganar.

### Resumen (~200 palabras)

El dentista está en posición rentable pero frágil. Genera 7.000€/mes netos con 3 sillones, pero trabaja 60h/semana, no tiene vacaciones en 2 años, y su matrimonio está en tensión. El tercer sillón vacío el 40% del tiempo invalida la lógica de expandir a 5. El banco ofrece crédito que sirve a sus propios intereses, no a los del dentista. Las 4 lentes estratégicas convergen: no expandir ahora. Primero llenar la capacidad existente (movimiento barato, reversible, informativo). Segundo, hablar con la esposa (precondición no negociable que está siendo ignorada). El recurso más escaso no es dinero — es tiempo personal, salud, y presencia familiar, todos irrecuperables y todos en deterioro. Aceptar el crédito cierra opciones futuras; optimizar las preserva. El precedente histórico de este tipo de posición es claro: los operadores que escalaron antes de reducir su dependencia operativa típicamente colapsaron. La trampa es confundir facturación con éxito. El movimiento estratégico óptimo es contraintuitivo: hacer menos, mejor, y con datos, antes de hacer más. La ventana más urgente no es la del crédito bancario — es la de los hijos de 4 y 6 años.

### Firma

La expansión es un movimiento irreversible que consume el recurso más escaso (tiempo/salud/familia) para resolver un problema que tiene solución reversible y barata (llenar el tercer sillón). Pensar dos movimientos adelante revela que el banco gana siempre y el dentista puede perder todo.

---

## Caso 2: Startup SaaS

### EXTRAER — mapear posición

**¿Dónde estás ahora — fuerte o débil?** Débil en casi todas las dimensiones. MRR de 12.000€ con churn del 8%/mes significa que pierde ~6-7 clientes al mes y necesita reponerlos solo para mantenerse. El co-fundador técnico se fue. El equipo es junior. 47 bugs abiertos. 7 meses de runway. 3 fondos pasaron. La relación CTO-CEO está rota. La única fuerza relativa: tiene 80 clientes de pago que validan que hay un mercado, y 3 grandes que pagan y piden más.

**¿Qué recursos tienes?** Dinero: ~196.000€ de runway (28K×7). Tiempo: 7 meses antes de morir. Personas: 3 devs junior + 1 diseñador part-time — capacidad limitada. Información: sabe qué quieren los 3 clientes grandes, sabe que el churn viene de calidad. El CTO tiene expertise técnico pero está quemado (70h/semana, 2 devs se fueron).

**¿Qué opciones de movimiento existen?** (A) Estabilizar: arreglar bugs, reducir churn, demostrar métricas a inversores. (B) Pivotar a enterprise: rehacer producto para clientes grandes, mayor ticket. (C) Híbrido: estabilizar core mientras desarrolla features para los 3 grandes. (D) Vender/acqui-hire: buscar comprador antes de que se acabe el runway. (E) Cerrar y salvar lo que quede.

**¿Cuáles son reversibles y cuáles no?** Estabilizar (A) es reversible — no cierra puertas. Pivotar a enterprise (B) es difícilmente reversible: consume todo el runway restante en un cambio de dirección sin garantía. El híbrido (C) es parcialmente reversible pero consume recursos en dos direcciones. Vender (D) no es reversible. Cerrar (E) no es reversible.

**¿Quién más está en el tablero?** CEO: quiere pivotar, tiene narrativa de crecimiento. Los 3 fondos que pasaron: quieren mejores métricas, no más visión. Los 3 clientes grandes: quieren features custom, tienen poder de negociación porque representan el 30% de ingresos. Los 3 devs junior: pueden irse (como ya hicieron 2 antes). Los 77 clientes pequeños: se van por calidad, no por falta de features enterprise.

**¿Qué sabes tú que ellos no?** El CTO sabe que el producto tiene deuda técnica grave (47 bugs), que el churn es por calidad, y que el equipo junior no puede ejecutar un pivot enterprise sin introducir más inestabilidad. **¿Qué saben ellos?** El CEO probablemente tiene más contexto del mercado enterprise y de lo que los fondos realmente quieren. Los clientes grandes saben cuánto están dispuestos a pagar — el CTO no.

### CRUZAR — posición × recursos

**Recursos que se agotan al usarlos:** Runway (cada mes son 28K menos). Tiempo del CTO (ya al 100%). Moral del equipo (frágil). Paciencia de los clientes que se van.

**¿Varias opciones compiten por el mismo recurso escaso?** Sí: estabilizar y pivotar compiten por los mismos 3 devs junior y los mismos 7 meses. No hay capacidad para ambas cosas. Este es el conflicto central: el CEO y el CTO quieren usar el mismo recurso escaso para objetivos diferentes.

**¿Recurso que NO estás usando?** Los 3 clientes grandes que piden features custom. Si están pidiendo cosas, probablemente pagarían más por ellas. Eso es revenue potencial no capturado. También: la información del churn — si se entrevista a los clientes que se van, se obtiene un mapa de prioridades de estabilización gratis.

**¿Movimiento que parece opción pero no lo es?** Pivotar a enterprise con 3 devs junior en 7 meses de runway. Eso no es una opción — es un suicidio con extra pasos. Un producto enterprise requiere estabilidad, seguridad, soporte, SLAs. Tienen exactamente lo opuesto: 47 bugs, equipo junior, churn alto. Los fondos ya dijeron "métricas insuficientes" — pivotar no arregla métricas, las reinicia a cero.

### LENTE L1 — Posicional

**¿Tu posición mejora o empeora si no haces nada?** Empeora rápidamente. Con 8% de churn mensual y sin mejora de producto, en 7 meses puede perder 30-40 clientes. El MRR puede caer a 6-7K mientras el burn sigue en 28K. La posición se deteriora cada mes de forma acelerada.

**¿Hay ventana temporal?** Sí: 7 meses de runway es la ventana dura. Pero hay una ventana más estrecha: los fondos que dijeron "métricas insuficientes" podrían reconsiderar si en 3-4 meses ven churn bajar significativamente. Esa ventana es 3-4 meses, no 7.

**¿Tu posición es fácil de atacar?** Muy fácil. Un competidor con mejor producto puede captar sus clientes que ya están frustrados. Los devs junior pueden irse. Los 3 clientes grandes pueden cambiar de proveedor si los bugs les afectan. Todo es frágil.

### LENTE L2 — Secuencial

**¿En qué orden tendrían que pasar las cosas?** Primero: CTO y CEO necesitan alinear visión o separarse. Sin esto, cada esfuerzo del equipo es contestado y medio desperdiciado. Segundo: estabilizar los bugs más críticos (los que causan churn). Tercero: medir si el churn baja. Cuarto: con datos de churn mejorado, volver a hablar con fondos o buscar revenue adicional de los 3 grandes.

**¿Qué DEBE hacerse antes?** La conversación CTO-CEO es la precondición de todo. Si no se alinean, el equipo recibe instrucciones contradictorias, la energía se disipa, y el runway se quema sin dirección. Todo lo demás es ruido hasta que esto se resuelva.

**¿Qué se desbloquea al hacer el primer movimiento?** Si CTO y CEO se alinean en "estabilizar primero, pivotar después", el equipo tiene dirección clara, los bugs bajan, el churn puede bajar, y las métricas mejoran para fondos. Si no se alinean, lo que se desbloquea es la decisión: o uno de los dos se va, o la empresa muere por parálisis.

**¿Movimiento que cierre opciones futuras?** Pivotar a enterprise ahora cierra la opción de estabilizar (no hay recursos para ambos). También cierra la opción de levantar Serie A con métricas de restaurantes (que es donde están los datos). Es el movimiento más peligroso posible.

### LENTE L3 — Adversarial

**¿Qué hará el CEO si el CTO estabiliza?** Si el CTO "gana" la discusión y estabiliza, el CEO puede sentirse ignorado, desmotivarse, o buscar otra oportunidad. Si el churn baja, el CEO puede cambiar de opinión. Si no baja, el CEO dirá "te lo dije".

**¿Qué hará si sabe que el CTO quiere estabilizar?** Puede intentar forzar el pivot unilateralmente — tomar decisiones de producto por encima del CTO, presionar al equipo, buscar un nuevo CTO.

**¿Hay forma de que ambos ganen?** Sí, si se reformula: "estabilizamos 3 meses, medimos churn, y si baja de X% seguimos en restaurantes; si no, pivotamos juntos." Eso convierte una pelea ideológica en un experimento con criterio de éxito acordado.

**¿Quién pierde más esperando?** Ambos pierden, pero la empresa pierde más. Cada mes de desalineación CTO-CEO es un mes de runway quemado con eficiencia mínima. Si el runway es 7 meses, 2 meses de parálisis son el 28% del tiempo restante — devastador.

### LENTE L4 — Opcionalidad

**¿Puedes moverte sin comprometerte?** Sí. Entrevistar a los clientes que cancelaron (información gratis). Priorizar los 5 bugs más mencionados en quejas (esfuerzo bajo, impacto medible). Negociar con los 3 grandes un pago anticipado por features (valida enterprise sin pivotar todo). Todo esto es exploración que no quema runway extra.

**¿Cuánto vale mantener opciones abiertas?** Enormemente. Con 7 meses de runway, cada decisión irreversible reduce el margen de maniobra. Pivotar a enterprise mata la opcionalidad. Estabilizar la preserva.

**¿Movimiento barato que da información antes del caro?** Entrevistar a 10 clientes que cancelaron. Coste: 10 horas del CTO o un dev. Beneficio: saber exactamente qué bugs causan churn, priorizar con datos reales. Otro: proponer a los 3 grandes un POC pagado para features enterprise. Si pagan, valida la dirección. Si no pagan, invalida el pivot.

### INTEGRAR

Convergencia total de las 4 lentes. Posicional: la posición se deteriora cada mes, pero pivotar la destruye. Secuencial: la conversación CTO-CEO es precondición de todo. Adversarial: hay un juego cooperativo posible si reformulan como experimento. Opcionalidad: existen movimientos baratos que dan información antes de comprometer el runway.

El movimiento estratégico es: (1) conversación seria CTO-CEO con criterio de éxito acordado, (2) estabilizar bugs críticos 8-12 semanas, (3) medir churn, (4) explorar enterprise con POC pagado a los 3 grandes, sin pivotar todo.

### ABSTRAER

Este es el patrón clásico de "founders en conflicto con runway corto". Precedentes: la mayoría de startups que mueren en esta fase mueren por desalineación de founders, no por falta de mercado. Y Combinator, Techstars y otros aceleradores coinciden: el problema #1 de startups no es técnico ni de mercado — es la relación entre founders. Los que sobreviven típicamente hacen una de dos cosas: alinean criterios objetivos de decisión, o uno de los dos sale limpiamente.

### FRONTERA

La inteligencia estratégica modela esto como un juego de posiciones y movimientos, pero hay algo que no captura: el CTO está quemado (70h/semana, devs que se van). La decisión "correcta" estratégicamente puede no ser ejecutable por un humano al límite. La estrategia asume un jugador racional con energía para ejecutar — quizá el recurso más escaso no es el runway ni los devs, sino la capacidad cognitiva y emocional del CTO para liderar un turnaround.

### Resumen (~200 palabras)

La startup está en posición débil con deterioro acelerado: 8% churn mensual, 47 bugs abiertos, founders desalineados, 7 meses de runway. La pregunta "pivotar o estabilizar" es falsa mientras los founders no estén alineados — esa es la precondición real. Pivotar a enterprise con devs junior, producto inestable y métricas pobres no es una opción real, es suicidio con narrativa optimista. Los fondos ya lo señalaron: "métricas insuficientes" significa "arregla lo que tienes, no cambies a otra cosa". Existen movimientos baratos de alta información: entrevistar clientes que cancelaron, priorizar 5 bugs críticos, proponer POC pagado a los 3 grandes. Estos movimientos preservan opcionalidad mientras generan datos. La ventana estratégica real no es 7 meses sino 3-4: lo que tarde en demostrar mejora de churn para reabrir conversación con fondos. El patrón es clásico: founders en conflicto son la causa #1 de muerte de startups. La resolución pasa por acordar un criterio objetivo que transforma una pelea de egos en un experimento. El recurso más escaso no es dinero — es la capacidad del CTO para liderar mientras está quemado.

### Firma

Pivotar a enterprise con producto roto, equipo junior y founders desalineados no es una opción — es un suicidio con narrativa optimista. El primer movimiento es humano (alinear founders), no técnico ni de mercado.

---

## Caso 3: Cambio de Carrera

### EXTRAER — mapear posición

**¿Dónde estás ahora — fuerte o débil?** Paradójicamente fuerte en lo material y débil en lo que importa. 180.000€/año de salario, 120.000€ ahorrados, empleo estable — posición financiera sólida. Pero: rechazada para socia (la posición profesional no mejora), insomnio de 2 años (el cuerpo está señalando), 3 años pensando en cambiar sin actuar (parálisis activa), no ha hablado con su marido (el aliado más importante no está activado). La fortaleza material subsidia una debilidad existencial.

**¿Qué recursos tienes?** Dinero: 180K/año de ingresos + 120K ahorrados. Tiempo: tiene empleo actual que le da tiempo para planificar — no hay urgencia inmediata. Personas: marido (no activado como recurso), amiga que hizo el cambio (modelo + información), red profesional de 20 años. Información: sabe los salarios de ONG (~55K), sabe su coste de vida, sabe que los hijos están a 2 y 4 años de universidad. Experiencia: 20 años de derecho corporativo son transferibles.

**¿Qué opciones de movimiento existen?** (A) Saltar: dejar el bufete, ir a ONG a 55K. (B) Transición gradual: empezar a hacer derecho medioambiental pro bono o part-time mientras sigue en el bufete. (C) Negociar internamente: proponer una práctica de derecho medioambiental dentro del bufete. (D) Esperar a hijos en universidad: 2-4 años más. (E) No hacer nada: seguir y esperar la próxima ronda de socia.

**¿Cuáles son reversibles y cuáles no?** Saltar (A) es difícilmente reversible — a los 45, salir de un bufete top y volver 2 años después es casi imposible. Transición gradual (B) es reversible. Negociar internamente (C) es reversible. Esperar (D) es "reversible" en teoría pero cada año que pasa reduce energía, aumenta aversión al riesgo, y la ventana se cierra. No hacer nada (E) es lo mismo que (D) pero sin intención.

**¿Quién más está en el tablero?** El bufete: quiere retenerla (20 años de experiencia, clientela). Los socios: la rechazaron pero dijeron "quizá el próximo ciclo" — puede ser genuino o puede ser retención barata. El marido: freelance con ingresos variables, sería el más afectado financieramente. Los hijos: 14 y 16, a punto de necesitar financiación universitaria. Los padres: no quieren que cambie ("estás loca") — presión emocional, no financiera. La amiga: modelo de lo posible, pero survivorship bias.

**¿Qué sabes tú que ellos no?** Ella sabe que tiene insomnio de 2 años y que su médico lo atribuye a estrés laboral — eso es información que el bufete no tiene (o no le importa). Sabe que ha pensado en esto 3 años — no es impulso. **¿Qué saben ellos?** El bufete sabe si la ronda de socia del próximo ciclo es realista o no. El marido sabe su tolerancia real al riesgo financiero — pero no ha sido consultado. Las ONG saben si realmente hay puestos disponibles para alguien con su perfil.

### CRUZAR — posición × recursos

**Recursos que se agotan al usarlos:** Tiempo (a los 45, cada año cuenta más para cambio de carrera). Salud (insomnio → deterioro cognitivo → peor rendimiento → más estrés). Los ahorros se agotarían si baja de 180K a 55K sin ajustar gastos.

**¿Varias opciones compiten por el mismo recurso escaso?** Sí. El tiempo y la energía emocional. Hacer la transición gradual requiere trabajar en dos frentes. Esperar consume el recurso más irrecuperable: años de vida en un trabajo que le está haciendo daño.

**¿Recurso que NO estás usando?** La conversación con el marido. Es el recurso más importante no activado. También: su red profesional de 20 años. Conoce gente en muchos sectores — puede explorar opciones de derecho medioambiental sin comprometerse. Los 120K de ahorros dan un colchón que no está contabilizando en su cálculo de riesgo.

**¿Movimiento que parece opción pero no lo es?** "Esperar al próximo ciclo de socia." Ya la rechazaron. "Quizá el próximo ciclo" es la frase estándar de retención sin compromiso. Si no fue socia con 20 años de experiencia, ¿qué cambiará en 2 años más? Este "movimiento" es inacción con nombre bonito.

### LENTE L1 — Posicional

**¿Tu posición mejora o empeora si no haces nada?** Empeora en lo que importa (salud, satisfacción, sentido) y se estanca en lo financiero (misma posición en el bufete, sin partnership). El insomnio de 2 años es una señal de deterioro progresivo. La posición financiera se mantiene pero a un coste creciente no contabilizado.

**¿Hay ventana temporal?** Múltiples. A los 45, la reinvención profesional es viable pero se vuelve más difícil cada año. Los hijos a 2-4 años de universidad crean una ventana financiera natural. Los 120K de colchón + marido trabajando = ventana de transición de 2-3 años.

**¿Tu posición es fácil de atacar?** En el bufete, sí: ya fue rechazada para socia, lo que señala que su posición no es fuerte internamente. Si sigue sin ser socia, su poder de negociación se erosiona cada año. Fuera del bufete, su posición como candidata a ONG es fuerte: 20 años de experiencia corporativa son muy valiosos en el sector sin ánimo de lucro.

### LENTE L2 — Secuencial

**¿En qué orden tendrían que pasar las cosas?** Primero: hablar con el marido — no como anuncio, sino como exploración conjunta. Segundo: hacer números reales (¿puede la familia vivir con 55K + ingresos del marido + ahorros?). Tercero: explorar el mercado de derecho medioambiental (¿hay demanda? ¿a qué salario real? ¿ONG o también empresas con departamento ESG?). Cuarto: negociar internamente o probar transición gradual antes de saltar.

**¿Qué DEBE hacerse antes?** La conversación con el marido. Es la precondición absoluta. Ella está tomando una decisión familiar en solitario, lo cual es estratégicamente terrible.

**¿Qué se desbloquea con el primer movimiento?** Si habla con el marido y él apoya: se desbloquea la exploración activa, los números compartidos, la planificación de transición. Si él no apoya: se desbloquea una verdad necesaria que mejor saberla ahora que dentro de 3 años.

**¿Movimiento que cierre opciones futuras?** Saltar directamente de 180K a 55K sin transición cierra la opción de volver al corporativo fácilmente y pone presión financiera inmediata sobre la familia. También: quedarse demasiado tiempo cierra la ventana de cambio por agotamiento y edad.

### LENTE L3 — Adversarial

**¿Qué hará el bufete si ella anuncia que quiere irse?** Puede contraofertarla o dejarla ir sin pelear. La reacción del bufete da información sobre su posición real.

**¿Hay forma de que todos ganen?** Sí. Si negocia una transición gradual o una práctica mixta, el bufete retiene experiencia y ella empieza a hacer lo que quiere. Las empresas con necesidades ESG/medioambiental están creciendo — puede haber un nicho dentro del derecho corporativo que satisfaga ambas partes.

**¿Quién pierde más esperando?** Ella pierde más. El bufete no pierde nada si ella se queda sufriendo — sigue facturando. Los hijos pierden una madre presente y sana. El marido pierde una compañera que duerme y está bien. Todos excepto el bufete pierden con la espera.

### LENTE L4 — Opcionalidad

**¿Puedes moverte sin comprometerte?** Sí, ampliamente. Hablar con el marido no compromete nada. Hacer números no compromete nada. Tomar café con gente en derecho medioambiental no compromete nada. Todo esto es exploración pura con coste casi cero.

**¿Cuánto vale mantener opciones abiertas?** La opción de seguir en el bufete tiene valor financiero claro (180K/año). Pero la opcionalidad más valiosa es la que está dejando morir: la capacidad de cambiar de carrera, que disminuye cada año.

**¿Movimiento barato que da información antes del caro?** Varios: (1) Hablar con el marido. (2) Hacer números reales. (3) Tomar 3-5 cafés con gente en derecho medioambiental. (4) Preguntar en el bufete sobre práctica ESG/medioambiental.

### INTEGRAR

Las 4 lentes convergen con un matiz. Posicional: la posición se deteriora en salud y satisfacción, el reloj corre. Secuencial: la conversación con el marido es precondición absoluta. Adversarial: ella pierde más esperando. Opcionalidad: hay abundantes movimientos baratos de exploración.

El matiz: las lentes NO dicen "salta ahora a 55K". Dicen "explora agresivamente SIN comprometerte todavía". La transición gradual o la negociación interna pueden producir un punto intermedio que no sea 180K-con-insomnio ni 55K-con-miedo.

### ABSTRAER

Patrón clásico de "golden handcuffs": un profesional exitoso atrapado por un salario que no puede igualar en lo que realmente quiere hacer. Los que hacen la transición exitosamente comparten dos rasgos: (1) exploran antes de saltar, y (2) tienen el apoyo explícito de su pareja.

### FRONTERA

La inteligencia estratégica modela esto como posición, recursos y movimientos. Pero el insomnio de 2 años no es un "dato" — es un cuerpo gritando. Y la frase "si no lo hago ahora, no lo haré nunca" no es análisis estratégico — es una intuición profunda que puede ser más verdadera que cualquier cálculo. La estrategia puede decir "explora gradualmente", pero si el cuerpo dice "no puedo más", la gradualidad puede ser lujo que la salud no puede permitirse.

### Resumen (~200 palabras)

Abogada de 45 años con posición financiera fuerte (180K + 120K ahorros) pero deterioro progresivo de salud (insomnio 2 años) y satisfacción profesional (rechazada para socia, 3 años pensando en cambiar). Las 4 lentes estratégicas convergen en: no saltar todavía, pero explorar agresivamente. La precondición absoluta es la conversación con el marido — está tomando una decisión familiar en solitario, lo cual es estratégicamente devastador. Existen abundantes movimientos baratos: hacer números reales, tomar cafés exploratorios, preguntar por práctica ESG interna. "Esperar al próximo ciclo de socia" no es una opción real — es inacción con nombre bonito. La opcionalidad más valiosa que tiene es la capacidad de cambiar, y esa opcionalidad se deprecia cada año. El precedente de "golden handcuffs" muestra que las transiciones exitosas combinan exploración previa + apoyo de pareja. Las fallidas son saltos impulsivos o esperas eternas. El punto ciego de la estrategia: el insomnio de 2 años es el cuerpo gritando, y la gradualidad que la estrategia recomienda puede ser un lujo que la salud no puede permitirse. La ventana no es solo financiera — es biológica.

### Firma

El movimiento más estratégico no es ni saltar ni quedarse — es explorar agresivamente sin comprometer posición, empezando por la precondición que lleva 3 años ignorada: la conversación con el marido.

---

## Loop test (P06)

**Caso elegido:** Startup SaaS

**Hallazgos nuevos de la segunda pasada:**

1. La concentración del 30% de ingresos en 3 clientes es una bomba de tiempo no suficientemente señalada en la primera pasada. Si esos 3 se van, el MRR cae de 12K a 8.4K y el churn efectivo se dispara.

2. La recomendación cooperativa (criterio objetivo CTO-CEO) asume buena fe que el caso no garantiza. "Apenas se hablan fuera de reuniones formales" puede significar que la negociación de buena fe es imposible. Quizá la opción real es "uno de los dos sale" y la primera pasada suavizó eso.

3. "Estabilizar reduce churn" es hipótesis del CTO, no hecho. Si el churn es por fit de mercado y no solo por bugs, estabilizar no basta. La primera pasada tomó la perspectiva del CTO como verdad sin examinarla.

**¿Es genuinamente nuevo?** Sí en los puntos 1 y 3. El punto 2 profundiza algo mencionado pero no examinado. La segunda pasada reveló un optimismo injustificado en la propia recomendación.

---

## Patrón cross-case

Hay un patrón que aparece en los 3 casos independientemente del dominio: **la precondición más importante es una conversación que no está ocurriendo.**

En la clínica dental: la conversación con la esposa. En la startup: la conversación real CTO-CEO. En el cambio de carrera: la conversación con el marido. En los 3 casos, la persona tiene toda la información necesaria para actuar EXCEPTO la que solo puede venir de hablar con el otro actor más importante del tablero. Y en los 3 casos, esa conversación es gratuita, reversible, y de alta información — cumple todos los criterios de movimiento óptimo en opcionalidad. Y en los 3 casos, es el movimiento que NO se está haciendo.

Segundo patrón: **confundir la opción que da más miedo con la opción que da más riesgo.** El dentista teme no crecer (pero crecer es lo arriesgado). El CTO teme no pivotar (pero pivotar es lo arriesgado). La abogada teme saltar (pero quedarse es lo que la está destruyendo). En los 3 casos, la percepción de riesgo está invertida respecto al riesgo real.

---

## Saturación (P07)

**¿Una tercera pasada aportaría algo nuevo?** Parcialmente. La segunda pasada del caso SaaS encontró 3 hallazgos genuinos (concentración de ingresos, hipótesis no validada, optimismo cooperativo injustificado). Una tercera pasada sobre el loop test probablemente extraería matices sobre matices — rendimiento marginal bajo (~10-15%). No justifica el coste.

---

## Firma global INT-05

**¿Qué vio esta inteligencia que probablemente NINGUNA otra vería?** La estratégica ve que en los 3 casos existe un movimiento barato, reversible, y de máxima información que no se está ejecutando — y que ese movimiento es siempre una conversación humana, no una acción técnica o financiera. La anticipación de dos movimientos adelante revela que las opciones que parecen valientes (expandir, pivotar, saltar) son en realidad las más peligrosas, y las que parecen tímidas (optimizar, estabilizar, explorar) son las más estratégicas.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/EXISTENCIAL.md
============================================================

# RESULTADOS F1-17: EXISTENCIAL

## INT-17: Existencial
**Objetos:** propósito, libertad, responsabilidad, finitud, valores
**Operaciones:** confrontar lo irreducible, jerarquizar valores, elegir con consciencia
**Firma general:** CONFRONTAR — preguntar "¿para qué?" hasta llegar al fondo

---

## Caso 1: Clínica Dental

### EXTRAER — lo que está en juego

Lo que está en juego de verdad no es la expansión de la clínica. Es la identidad del odontólogo como proveedor. Expandir es la forma que toma la pregunta que no se atreve a formular: "¿Soy suficiente tal como estoy?" Cada sillón vacío le susurra insuficiencia. La oferta del banco no es una oportunidad — es un espejo que le devuelve su ansiedad de no estar haciendo lo máximo posible.

Si no hace nada, pierde la narrativa de progreso. El tercer sillón vacío al 40% le recordará cada día que "podría estar ganando más". Pero no pierde nada material — ya tiene margen, tiene clínica, tiene familia. La pérdida es simbólica: la imagen de sí mismo como hombre que avanza.

Si hace lo que "debería" — expandir —, pierde lo que ya se está diluyendo: presencia con hijos de 4 y 6 años, salud, la posibilidad de no repetir la historia de su padre. El infarto a los 52 no es un dato — es una profecía que él está cumpliendo sin querer.

La segunda pérdida pesa más. Y él lo sabe — su esposa ya se lo dijo. Pero quien decide no es la lógica sino la inercia disfrazada de ambición.

### CRUZAR — valores × vida

Dice que valora a su familia. Trabaja 60h/semana y no tiene vacaciones desde hace 2 años. La distancia entre lo declarado y lo vivido es enorme. La familia es el valor declarado; el trabajo es el valor vivido.

Lo que dice que no importa pero le quita el sueño: el sillón vacío. El 40% de capacidad ociosa no es un problema financiero (tiene margen), pero es un problema existencial — le dice que no está optimizado, que no es suficiente.

Lo que dice que importa pero a lo que dedica cero: sus hijos. "Los niños preguntan por ti" es la frase de una esposa que ya agotó las formas educadas de decir que la familia está en segundo plano.

La distancia es grande. Y lo peor: él probablemente lo sabe pero no puede articularlo sin que se tambalee la justificación de todo su esfuerzo.

### LENTE L1 — Propósito

¿Para qué hace lo que hace? Superficialmente: para pagar la hipoteca, mantener a la familia, construir patrimonio. En profundidad: para demostrar que puede. La clínica es su manera de decir al mundo — y a sí mismo — que vale. El odontólogo-propietario-que-expande tiene más estatus que el odontólogo-que-se-conforma.

Si tuviera suficiente dinero, ¿seguiría trabajando 60 horas? Probablemente no. Eso revela que el trabajo no es vocación pura — es vehículo de validación y seguridad. Lo cual no es malo, pero hay que nombrarlo.

Lo hace porque siente que debe, no porque quiere. "Deber" aquí tiene dos capas: el deber financiero real (la hipoteca) y el deber internalizado (un hombre exitoso no para, un negocio debe crecer).

### LENTE L2 — Finitud

Sus hijos tienen 4 y 6. En 10 años tendrán 14 y 16 — serán adolescentes que ya no pedirán estar con papá. El tiempo de presencia activa con niños pequeños es irrecuperable. No hay versión de la realidad donde trabaja 70h/semana ahora y "lo compensa después". Después no existe para esta ventana.

Su padre tuvo infarto a los 52. Él tiene 38. Le quedan 14 años hasta esa edad si la historia se repite. Está invirtiendo esos 14 años en replicar exactamente las condiciones que produjeron el infarto.

Lo que gana (más facturación, más sillones, más estatus) no compensa lo que pierde (infancia de sus hijos, salud, relación con su esposa). Pero la ganancia es medible y la pérdida es silenciosa. Los 65.000€/mes son un número concreto. La mirada de su hijo cuando llega y ya está dormido no tiene métrica.

### LENTE L3 — Libertad

Está siguiendo inercia. La lógica del "más sillones = más ingresos = mejor vida" es un raíl que no eligió conscientemente — lo heredó del modelo de su padre, de la cultura empresarial, del banco que ofrece crédito porque le conviene al banco.

La última vez que eligió activamente fue probablemente cuando decidió abrir la clínica. Desde entonces, cada decisión ha sido reactiva: responder a la demanda, cubrir la hipoteca, mantener el ritmo.

Puede decir "no" al banco sin que pase nada malo. No hay consecuencia negativa material por rechazar la expansión. Y sin embargo no dice "no" porque decir "no" a la expansión se siente como decir "me conformo", y eso viola su imagen de sí mismo.

### LENTE L4 — Responsabilidad

Es responsable ante: el banco (deuda), su familia (sustento y presencia), su asociado (empleo), sus pacientes, y ante sí mismo.

El orden actual: banco primero, negocio segundo, familia tercero, él mismo último.

El orden que debería ser si los valores declarados fueran los vividos: familia primero, salud propia segundo, negocio tercero, banco cuarto.

Las dos respuestas no coinciden. Y la inversión de orden es exactamente lo que la esposa está pidiendo sin que nadie la escuche.

### INTEGRAR

El propósito (demostrar que puede) no justifica el sacrificio (infancia de sus hijos, riesgo cardiovascular, relación deteriorándose) sabiendo que el tiempo no vuelve. Pero él no puede ver esto porque el propósito superficial (pagar la hipoteca) le da coartada al propósito profundo (validarse). Mientras pueda decir "lo hago por la familia", no tiene que confrontar que lo hace por sí mismo — y que lo que hace por sí mismo daña a la familia.

### ABSTRAER

Esto le pasa a casi todo propietario de negocio pequeño con familia joven. Es la trampa universal del emprendedor: el negocio que empezó para dar libertad se convierte en la jaula. Es estructural, no personal — pero el hecho de que sea común no lo hace menos urgente para él.

### FRONTERA

Estas preguntas podrían ser otra forma de no decidir. Hay un riesgo real de que la reflexión existencial se convierta en parálisis. Pero en este caso, la parálisis ya existe — es la inercia de seguir expandiendo. La verdadera parálisis no es reflexionar; es no poder parar.

### Resumen (~200 palabras)

El odontólogo enfrenta una crisis de identidad disfrazada de decisión de negocio. Lo que está en juego no es facturación sino quién quiere ser: el hombre que siempre crece o el padre que estuvo presente. La distancia entre valores declarados (familia) y valores vividos (trabajo) es enorme — 60h/semana sin vacaciones mientras los niños preguntan por él. Su propósito profundo no es proveer sino validarse; si tuviera dinero suficiente, no trabajaría así. La finitud es brutal: sus hijos tienen 4 y 6, la ventana de presencia activa se cierra en una década, y la sombra del infarto paterno a los 52 marca un horizonte que él ignora activamente. No está eligiendo — sigue inercia heredada. Puede decir "no" al banco sin consecuencia material, pero no lo hace porque "no expandir" se siente como fracaso. Su orden de responsabilidad está invertido: banco y negocio antes que familia y salud. El propósito no justifica el sacrificio. Es un patrón universal del emprendedor con familia joven, pero la universalidad no lo absuelve. La verdadera parálisis no es reflexionar — es no poder detenerse.

### Firma

La expansión de la clínica es la repetición exacta de la historia del padre — no es una decisión de negocio, es una herencia existencial que nadie ha nombrado.

---

## Caso 2: Startup SaaS

### EXTRAER — lo que está en juego

Lo que está en juego de verdad no es si pivotear o estabilizar. Es si el CTO puede seguir sosteniendo un proyecto que ya no le pertenece emocionalmente. El co-fundador técnico se fue, el CEO y él apenas se hablan, los devs se van, trabaja 70h/semana. La pregunta real no es "¿qué hacemos con el producto?" sino "¿para qué sigo aquí?"

Si no hace nada: el runway se agota en 7 meses, la startup muere. Pero eso también lo libera. La muerte de la startup resolvería una decisión que él no se atreve a tomar.

Si hace lo que "debería" — pivotar a enterprise como pide el CEO —, pierde la razón por la que entró: construir un producto sólido para restaurantes. Pivotar no es una decisión técnica; es renunciar a la visión que le daba sentido al proyecto.

La segunda pérdida pesa más para él, pero el contexto (runway, equipo, inversores) hace que la primera parezca más urgente. La urgencia financiera secuestra la conversación existencial.

### CRUZAR — valores × vida

El CTO dice que valora la calidad del producto. Tiene 47 bugs abiertos y un equipo de juniors que no pueden resolverlos al ritmo necesario. Su valor declarado (producto sólido) choca con su realidad vivida (deuda técnica creciente, equipo insuficiente).

Lo que dice que no importa pero le quita el sueño: la relación rota con el CEO. "Apenas se hablan fuera de reuniones formales" — eso no es un detalle operativo, es la muerte del vínculo cofundador. Es más devastador que el churn del 8%.

Lo que dice que importa pero a lo que dedica cero: su propia sostenibilidad. 70h/semana, dos devs que se fueron en 12 meses. El burnout es inminente y no aparece en ninguna métrica que esté monitorizando.

La distancia entre lo declarado y lo vivido es grande, pero de forma diferente al caso dental: aquí el CTO sí intenta vivir su valor (calidad) pero el sistema se lo impide. No es hipocresía — es impotencia.

### LENTE L1 — Propósito

¿Para qué sigue? Superficialmente: porque es cofundador, tiene equity, siente responsabilidad. En profundidad: porque abandonar significaría admitir que fracasó. El propósito original (resolver un problema real para restaurantes) se ha transformado en resistencia al fracaso. Ya no construye por amor al problema — resiste por miedo a lo que significa soltar.

Si tuviera suficiente dinero, ¿seguiría en esta startup? Casi seguro que no. No en estas condiciones. Lo cual revela que lo que lo ata no es pasión — es obligación y miedo.

Lo hace porque siente que debe. "Debe" al equipo que queda, "debe" a la visión original, "debe" a sí mismo demostrar que puede sacar esto adelante. Cada "debe" es una cadena diferente.

### LENTE L2 — Finitud

Tiene 34 años. Si gasta 7 meses más (o un pivote de 12-18 meses) en algo que probablemente falle, habrá invertido sus primeros años de madurez profesional en un proyecto terminal. El tiempo no es abstracto: es un año y medio de vida a 70h/semana.

Ese tiempo es parcialmente recuperable — a los 35-36 puede empezar otra cosa. Pero la energía no es la misma. El coste no es solo temporal; es motivacional. Un fracaso prolongado drena la capacidad de emprender después.

Lo que gana (la posibilidad remota de que funcione) no compensa lo que pierde (salud, motivación, relaciones) en el escenario más probable. Está apostando todo a una lotería que tres fondos de inversión ya evaluaron y rechazaron.

### LENTE L3 — Libertad

No está eligiendo. Está atrapado entre dos inercias: la del CEO que empuja enterprise y la suya propia que insiste en estabilizar un producto que se desangra. Ninguna de las dos es una elección libre — son posiciones reactivas.

La última elección activa fue probablemente cofundar la empresa. Desde entonces, cada decisión ha sido reacción a crisis: el co-fundador se fue, los devs se fueron, los clientes se van, los inversores no entran.

Puede decir "no". Puede irse. El "algo malo" que pasaría si dice "no" es: sentirse como un desertor, perder el equity (que probablemente vale poco), y enfrentar el vacío de no saber qué sigue. Esos son miedos reales pero no son catástrofes reales.

### LENTE L4 — Responsabilidad

Es responsable ante: el equipo de 3 juniors + diseñador, los 80 clientes, el CEO, los inversores potenciales que no entraron, y ante sí mismo.

Orden actual: empresa primero, equipo segundo, CEO tercero, él mismo último.

Orden que debería ser: él mismo primero (porque si se quema, todo cae), equipo segundo (porque dependen de él), producto tercero, y la dinámica CEO-CTO necesita resolverse o romperse — no puede seguir en limbo.

Las respuestas no coinciden. Se está sacrificando por una entidad (la startup) que no le está devolviendo lo que necesita (ni financieramente ni en términos de propósito).

### INTEGRAR

El propósito original (construir algo valioso para restaurantes) ya no justifica el sacrificio actual (70h/semana, aislamiento del CEO, equipo inestable, runway agotándose). El propósito se ha transformado en resistencia al fracaso, que es un propósito mucho más pobre y mucho más destructivo. Seguir por no soltar no es perseverancia — es negación.

### ABSTRAER

Esto le pasa a muchos cofundadores técnicos en startups en fase de crisis. La tensión CTO-CEO por visión, el burnout, la confusión entre persistencia y terquedad, el equity como cadena emocional — es un patrón con nombre: "cofundador atrapado en el coste hundido". Es universal, pero la particularidad aquí es la soledad: el otro técnico se fue, la comunicación con el CEO murió. No es solo el patrón — es el aislamiento dentro del patrón.

### FRONTERA

Estas preguntas pueden ser otra forma de no decidir. Pero en este caso, el problema es que la decisión ya está tomada por omisión: si no decide, en 7 meses la startup muere y la decisión se toma sola. La reflexión existencial tiene fecha de caducidad aquí — o se usa ahora para elegir conscientemente, o la realidad financiera elige por él.

### Resumen (~200 palabras)

El CTO enfrenta una crisis de propósito disfrazada de dilema técnico-estratégico. Lo que realmente está en juego no es pivotar vs estabilizar, sino si tiene sentido seguir en un proyecto donde la visión original murió, la relación cofundadora se rompió, y el equipo se desangra. Su propósito se transformó de "construir algo valioso" a "resistir el fracaso" — un propósito destructivo que lo mantiene atado por miedo, no por pasión. La distancia entre valores y vida tiene un matiz diferente al dental: aquí no es hipocresía sino impotencia — quiere calidad pero el sistema se lo impide. La finitud es concreta: 7 meses de runway, 34 años, energía agotándose. Tres fondos ya dijeron que no. No está eligiendo — está reaccionando a crisis sucesivas. Puede irse sin catástrofe real, pero el miedo a ser "desertor" y perder el equity lo paraliza. Su orden de responsabilidad pone a la startup primero y a sí mismo último, exactamente invertido. El propósito no justifica el sacrificio. Es un patrón universal de cofundador atrapado en el coste hundido, agravado por aislamiento. La reflexión existencial tiene aquí fecha de caducidad: 7 meses.

### Firma

El CTO espera que la startup muera sola para no tener que elegir irse — la no-decisión es la decisión, y tiene fecha de caducidad de 7 meses.

---

## Caso 3: Cambio de carrera

### EXTRAER — lo que está en juego

Lo que está en juego de verdad es si esta mujer se permite vivir su vida o sigue viviendo la vida que otros esperan de ella. No es "bufete vs ONG" — es autenticidad vs seguridad. La pregunta latente es la más antigua de la filosofía existencial: ¿puedo ser quien realmente soy, o el precio es demasiado alto?

Si no hace nada: pierde la posibilidad de alinearse con sus valores. Tiene 45 años. "Si no lo hago ahora, no lo haré nunca" no es dramatismo — es aritmética vital. Cada año que pasa, la inercia se solidifica. El insomnio de 2 años es el cuerpo diciendo lo que la mente no se atreve a decidir.

Si hace lo que "debería" — quedarse —, pierde lo último de sí misma que todavía protesta. El insomnio es la señal de que algo dentro de ella se resiste a morir. Si se queda, esa resistencia eventualmente se extingue, y eso es una pérdida más grave que la pérdida de ingresos.

La segunda pérdida pesa más. Pero quien decide no es ella sola — hay hijos, hipoteca, marido. Y eso es precisamente lo que la paraliza: el peso de la responsabilidad hacia otros hace que la responsabilidad hacia sí misma parezca egoísmo.

### CRUZAR — valores × vida

Dice que ha perdido la pasión por el derecho corporativo. Lleva 20 años en él. La distancia entre lo declarado y lo vivido aquí tiene un matiz único: ella sabe que está desalineada y lleva 3 años sabiéndolo. No es inconsciencia — es consciencia sin acción. Eso es más doloroso que no darse cuenta.

Lo que dice que no importa pero le quita el sueño: la seguridad financiera. No lo nombraría como valor supremo, pero es lo que la mantiene en el bufete. El insomnio no es solo por estrés laboral — es por la tensión entre saber lo que quiere y no poder hacerlo.

Lo que dice que importa pero a lo que dedica cero: la exploración del cambio. Tres años pensando en derecho medioambiental y no ha hablado en profundidad con su marido. Ni ha explorado opciones intermedias. Ni ha contactado ONGs. El deseo existe como fantasía protegida — si no lo intenta, no puede fracasar.

La distancia entre lo declarado y lo vivido es grande y consciente, lo cual la hace más corrosiva que en los otros dos casos.

### LENTE L1 — Propósito

¿Para qué ejerce derecho corporativo? Para pagar: hipoteca, estabilidad familiar, futuro de los hijos. La razón profunda original — probablemente justicia, rigor intelectual, estatus — se ha vaciado. Lo que queda es el armazón funcional sin alma.

Si tuviera suficiente dinero, ¿seguiría en el bufete? No. Lo dice implícitamente: quiere ir a una ONG. El dinero es el único argumento que sostiene la permanencia. Cuando el único argumento para hacer algo es económico, la actividad ya murió como fuente de sentido.

Lo hace porque siente que debe. "Debe" a sus hijos estabilidad. "Debe" a sus padres no ser "loca". "Debe" al bufete lealtad. "Debe" a su imagen profesional coherencia. Cada "deber" la aleja de sí misma.

### LENTE L2 — Finitud

Tiene 45 años. Si hace la transición ahora, tiene 20 años de carrera significativa por delante. Si espera 5 años más, tendrá 50 y la transición será más difícil — no imposible, pero más difícil. El "si no lo hago ahora" tiene validez temporal real.

El hijo mayor entra en universidad en 2 años. Eso es un hito que ella usa como barrera ("no puedo arriesgar"), pero también como fecha: en 2 años el mayor es autónomo financieramente en buena medida, y en 4 años ambos. La ventana se abre progresivamente.

El insomnio de 2 años es finitud vivida en el cuerpo. El estrés crónico tiene consecuencias medibles: cardiovasculares, inmunológicas, cognitivas. No es solo un síntoma — es un reloj.

Lo que gana quedándose (180K€/año, previsibilidad) no compensa lo que pierde (salud, autenticidad, la posibilidad de vivir alineada con sus valores en los 20 años productivos que le quedan). Pero la ganancia es mensual y tangible; la pérdida es difusa y acumulativa.

### LENTE L3 — Libertad

No está eligiendo. Lleva 3 años en el umbral sin cruzar. Eso no es deliberación — es parálisis. La diferencia es que la deliberación tiene horizonte temporal y la parálisis es indefinida.

¿Cuándo eligió activamente por última vez? Probablemente al entrar en el bufete, hace 20 años. Desde entonces: promociones esperadas, hipoteca estándar, hijos en momento "correcto". Todo dentro del guión.

Puede decir "no" al bufete. El "algo malo" que pasaría: reducción drástica de ingresos (de 180K a 55K), presión familiar, juicio de los padres, incertidumbre. Son costes reales, pero no son catástrofes irreversibles — tiene 120K ahorrados, marido con ingresos, hipoteca manejable con ajustes.

Si puede decir "no" y no lo hace, ¿por qué? Porque el sistema de deberes ajenos es más fuerte que la voz propia. Y porque no ha tenido la conversación con su marido que lo haría real. Mientras no habla, el cambio sigue siendo fantasía segura.

### LENTE L4 — Responsabilidad

Es responsable ante: sus hijos (estabilidad, ejemplo), su marido (proyecto conjunto de vida), sus padres (expectativas), el bufete (carrera), sí misma (autenticidad).

Orden actual: hijos primero, padres/sociedad segundo, bufete tercero, marido cuarto, ella misma última.

Orden que debería ser si tomara en serio lo que siente: ella misma primero (porque si se destruye, nada funciona), hijos segundo, marido tercero, el resto después.

La pregunta brutal: ¿qué ejemplo da a sus hijos — que la vida es aguantar, o que la vida merece ser vivida? Si se queda "por ellos", les enseña que el sacrificio de la autenticidad es lo normal. Si se va "por ella", les enseña que es posible elegir. Ambas lecciones tienen precio.

### INTEGRAR

El propósito residual (seguridad financiera) no justifica el sacrificio (autenticidad, salud, 20 años de vida profesional desalineada) sabiendo que el tiempo no vuelve. Pero la justificación se sostiene porque involucra a terceros: los hijos. El momento más honesto sería reconocer que la seguridad de los hijos es real pero tiene fecha (2-4 años) y que hay formas de gestionarla que no exigen renunciar a todo.

### ABSTRAER

Esto le pasa a todo profesional de alto rendimiento en la mitad de su carrera. Es la crisis clásica de los 40-50: el éxito logrado no produce el significado esperado. Es tan universal que tiene nombre en la literatura psicológica. Pero la universalidad no resta urgencia — el hecho de que sea común significa que hay caminos probados, no que sea trivial.

### FRONTERA

¿Son estas preguntas otra forma de no decidir? En este caso, sí, potencialmente. Ella ya lleva 3 años reflexionando. No necesita más reflexión — necesita una conversación con su marido y un plan financiero de transición. La inteligencia existencial, en este caso, corre el riesgo de alimentar exactamente lo que diagnostica: la parálisis por exceso de profundidad.

### Resumen (~200 palabras)

La abogada enfrenta la pregunta existencial más directa de los tres casos: ¿puedo ser quien realmente soy? No es bufete vs ONG — es autenticidad vs seguridad, ser vs deber. Lleva 3 años sabiendo que está desalineada y no ha actuado: consciencia sin acción, que es más corrosiva que la inconsciencia. Su propósito en el bufete se ha vaciado hasta quedar solo el armazón económico — si tuviera dinero suficiente, no seguiría. Cada "deber" la aleja de sí misma. La finitud es doble: 20 años de carrera significativa por delante que se reducen con cada año de espera, y un cuerpo que lleva 2 años protestando con insomnio. Puede decir "no" — tiene ahorros, marido con ingresos, hipoteca gestionable —, pero no lo hace porque no ha tenido la conversación que convertiría la fantasía en plan. Su orden de responsabilidad la pone última. La pregunta brutal es qué enseña a sus hijos: ¿que la vida es aguantar o que es posible elegir? La reflexión existencial aquí corre riesgo de alimentar la parálisis que diagnostica — no necesita más preguntas, necesita una conversación y un plan.

### Firma

El insomnio de 2 años no es estrés laboral — es la última señal de una autenticidad que se resiste a morir, y nombrar eso correctamente cambia toda la ecuación.

---

## Loop Test (P06)

### Caso elegido: Cambio de carrera

**Segunda pasada — preguntas existenciales aplicadas al propio output del Caso 3:**

**EXTRAER sobre el output:** Lo que está en juego en el análisis es la honestidad del diagnóstico. El output concluye que ella "necesita conversación y plan, no más preguntas". Pero eso es una prescripción disfrazada de observación. La inteligencia existencial está haciendo exactamente lo que diagnostica que ella hace: saber lo que hay que hacer sin ejecutar.

**CRUZAR sobre el output:** El análisis dice valorar la "autenticidad" como norte pero dedica la mayoría del texto a describir obstáculos, no a confrontar el momento de elección. La distancia entre lo que el análisis declara y lo que hace es ella misma significativa. ¿Reproduce la parálisis del sujeto?

**L1 — Propósito del análisis:** Si es para que ella decida, debería terminar con una pregunta directa, no con un resumen. El propósito declarado (confrontar) se diluye en el formato (documentar).

**L2 — Finitud del análisis:** Trata la finitud como objeto de estudio, no como urgencia vivida. "20 años por delante" como dato no transmite peso. La finitud descrita desde fuera pierde su filo.

**L3 — Libertad del análisis:** ¿El output la libera o la carga? Le da más conceptos para pensar en una situación donde ya piensa demasiado. Riesgo real de que el análisis se sume al ruido que la paraliza.

**L4 — Responsabilidad del análisis:** Si es responsable ante ella, debería ser breve y cortante. Si es ante el sistema cartográfico, debe ser exhaustivo. Las dos responsabilidades tiran en direcciones opuestas — se eligió exhaustividad, quizá a costa de utilidad.

### ¿Qué revela la segunda pasada?

La primera pasada diagnosticó la parálisis de la abogada. La segunda revela que el análisis existencial puede ser cómplice de esa parálisis. La exhaustividad funciona como dilación. La inteligencia existencial, aplicada a sí misma, descubre su propia tendencia a sustituir la acción por la comprensión.

Punto ciego genuino descubierto: se trató la "conversación con el marido" como acción pendiente, pero no se exploró qué teme de esa conversación. ¿Teme que él diga que no? ¿O teme que diga que sí y entonces ya no tenga excusa? Eso es más profundo que "no ha hablado" — es por qué no ha hablado.

**Resultado: genuinamente no-idempotente.**

---

## Patrón Cross-Case

Los tres sujetos han sustituido la elección por la inercia y usan una obligación externa real como escudo contra una pregunta interna que no quieren enfrentar:
- Dentista: hipoteca + oportunidad del banco
- CTO: runway + responsabilidad con el equipo
- Abogada: hijos + hipoteca

En los tres casos, el cuerpo o el sistema ya responde lo que la mente no formula: infarto del padre, devs que se van, insomnio de 2 años.

En los tres, el orden de responsabilidad está invertido: el yo va último, y si colapsa, todo colapsa.

---

## Saturación (P07)

Una tercera pasada no aportaría significativamente. La segunda reveló meta-parálisis y una capa oculta genuina. Una tercera sería refinamiento del refinamiento. Más útil cruzar con Constructiva o Estratégica para romper la espiral reflexiva.

---

## Firma INT-17: Existencial

**La inteligencia existencial ve lo que ninguna otra puede ver: que el "problema" de cada caso no es el problema — es el escudo que protege al sujeto de una pregunta sobre sí mismo que todavía no se atreve a formular. Y ve también que ella misma, al formularla, puede alimentar la parálisis que diagnostica.**



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/FINANCIERA.md
============================================================

# RESULTADOS F1-07: INTELIGENCIA FINANCIERA (INT-07)

**Fecha:** 2026-03-08
**Fase:** 1 — Ejecución individual
**Casos:** 3 (Clínica Dental, Startup SaaS, Cambio de Carrera)

---

## INT-07: FINANCIERA

### Caso 1: Clínica Dental

#### EXTRAER — mapear flujos

**Entradas:** 45.000€/mes de facturación, mensual, recurrente mientras haya pacientes en sillones. No hay dato de estacionalidad ni de ratio cobro/facturación (morosidad oculta).

**Salidas:** 32.000€/mes de costes fijos (incluye cuota hipotecaria de 2.800€/mes). Ese 32K incluye salarios, suministros, alquiler o amortización del local, seguros, y el salario del asociado. El margen neto declarado es ~7.000€/mes, lo que implica que hay ~6.000€ de costes variables o no contabilizados (45.000 − 32.000 = 13.000, pero dice margen neto ~7.000, así que hay ~6.000 entre impuestos, amortización de equipos y otros).

**Lo que queda:** 7.000€/mes netos. Es estable en apariencia, pero depende al 100% de que él esté sentado en el sillón. No crece sin intervención.

**Deudas:** Hipoteca de clínica: 280.000€ pendientes, 2.800€/mes. Si asumimos tipo fijo ~3-4%, quedan probablemente 10-12 años. El banco le ofrece MÁS deuda para ampliar.

**Activos:** La clínica como activo productivo. Tres sillones, equipamiento dental (se deprecia rápido — cada 8-10 años). El local, si es propiedad, tiene valor de reventa pero está gravado con la hipoteca. Goodwill (cartera de pacientes) — valioso pero atado a su presencia.

**Coste real de su hora:** Margen neto 84.000€/año. Trabaja 2.500 horas/año. Eso son 33,6€/hora neta. Pero esa es la hora que le pagan. La hora que le CUESTA vivir incluye: 60h/semana de trabajo, pérdida de presencia con hijos de 4 y 6 años (ventana irrecuperable), estrés acumulado, cero vacaciones en 2 años, historial familiar de infarto a los 52 (él tiene 38 — le quedan 14 años hasta esa edad si replica el patrón).

#### CRUZAR — flujos × riesgo

Los ingresos dependen al 100% de él. Si él para, su sillón (que probablemente genera 60-70% de la facturación como dentista principal) cae a cero. El asociado podría mantener parte, pero no el 100%. Si para un mes, los ingresos caen quizá al 40-50%, pero los costes fijos (32K) siguen íntegros. Un mes de baja supondría una pérdida neta de ~15-18K€.

Los costes son masivamente fijos: hipoteca, salarios, seguros no bajan si baja la actividad. Control mínimo. Quizá un 10-15% es variable (materiales dentales, laboratorio).

Colchón: 7.000€/mes de margen contra 32K de costes fijos. Sin ingresos aguanta 0 meses. Fragilidad extrema.

El dinero que gana hoy se consume hoy. Paga deuda, paga vida, el excedente de 7K probablemente va a amortización de equipos futura y gastos familiares. No construye reserva significativa.

#### LENTE L1 — Valor presente

Lo que promete la ampliación: pasar de 45K a 65K/mes de facturación. Si los costes fijos suben proporcionalmente, el margen neto podría subir de 7K a quizá 12-15K/mes. Pero es una PROMESA basada en la asunción de que llena los sillones nuevos. El tercer sillón actual está vacío el 40% del tiempo — dato demoledor. Si no puede llenar lo que tiene, ¿por qué llenar más?

Está sacrificando AHORA: presencia con hijos de 4 y 6 años (ventana de 3-4 años antes de que dejen de pedirlo), salud (patrón familiar de infarto), relación de pareja. Estas cosas valen infinitamente más que los 5-8K€ extra de margen que promete la ampliación, pero no aparecen en ningún P&L.

Tasa de descuento implícita altísima: actúa como si el presente no valiera nada y todo el valor estuviera en el futuro incierto.

#### LENTE L2 — Apalancamiento

Ya está apalancado: 280K de hipoteca sobre una clínica que genera 84K€/año de margen neto. Ratio deuda/margen = 3,3 años. Aceptable pero ajustado. Si toma más crédito (150-200K adicionales), pasa a 430-480K€ de deuda sobre un margen que ESPERA que suba pero que hoy es 84K. Ratio deuda/margen sube a 5-6 años. Peligroso.

El apalancamiento amplifica ganancias SI la ampliación funciona. Pero si no llena sillones (como el 40% de vacío del tercero sugiere), amplifica las pérdidas.

El banco gana seguro: cobra intereses sobre el crédito independientemente de si la clínica prospera. El banco tiene asimetría positiva, el dentista tiene asimetría negativa.

#### LENTE L3 — Opcionalidad

Mantener opciones abiertas costaría muy poco: optimizar el tercer sillón (del 60% al 85-90% de ocupación) antes de ampliar. Esto le daría información real sobre la demanda sin asumir deuda nueva. Barato y reversible.

La expansión es asimétrica NEGATIVA: si sale bien gana 5-8K más al mes, si sale mal puede perder la clínica. Gana poco en upside, arriesga mucho en downside.

Puede comprar tiempo: los hijos tienen 4 y 6 años. En 3-4 años, la ventana de presencia parental se habrá cerrado. El tiempo es el recurso más escaso.

#### LENTE L4 — Margen de seguridad

Margen de seguridad actual: casi nulo. 7K€/mes de margen contra 32K de costes fijos = ratio 0,22. Cualquier caída del 15-20% en facturación le pone en rojo.

Opera al límite. No tiene vacaciones, no tiene colchón visible, no tiene redundancia (él ES el sistema).

Un imprevisto de 20.000€ le pondría en crisis seria.

Su plan de expansión funciona SOLO si todo sale bien: llena los sillones, contrata buen personal, mantiene su ritmo, no se pone enfermo, y los costes se mantienen en rango.

#### INTEGRAR (∫)

El valor presente de lo que sacrifica (salud, familia, tiempo irrecuperable) NO justifica el apalancamiento adicional. La opcionalidad inteligente (optimizar antes de expandir) es masivamente superior. No hay margen de seguridad — está desnudo. El flujo paga la deuda y la vida, pero NO deja reserva.

#### ABSTRAER

Este perfil financiero NO es sostenible a 5 años sin cambios. Se parece al patrón de negocios que quiebran: operan al límite, se apalancan para crecer, un imprevisto les tumba. La variable que separa prosperidad de quiebra es la utilización: si no llena el tercer sillón, no debería comprar el cuarto y quinto.

#### FRONTERA

No todo se traduce a euros. Una cena con sus hijos vale más que cualquier cifra en la hoja de cálculo. El análisis financiero responde "no expandas" de forma clara. Pero la pregunta real no es "¿debería expandir?" sino "¿cuánto de ti mismo estás dispuesto a quemar para pagar una hipoteca?"

**Resumen:** La clínica genera 7.000€/mes netos sobre 2.500 horas/año — 33,6€/hora real. Ingresos 100% dependientes de presencia física, sin colchón ni redundancia. Ratio margen/costes fijos 0,22: fragilidad extrema ante cualquier caída. El tercer sillón vacío el 40% refuta la premisa de expansión. Más deuda amplificaría pérdidas, no ganancias, con asimetría favorable al banco y desfavorable al dentista. La opcionalidad inteligente es optimizar lo existente. El sacrificio presente (salud, familia en ventana irrecuperable) no justifica 5-8K€ extra de margen incierto. Perfil convergente hacia quiebra sin cambios a 5 años.

**Firma:** La clínica es una trampa de apalancamiento con asimetría negativa: el banco gana en todos los escenarios, el dentista solo en el mejor. El tercer sillón vacío es el dato que desmonta toda la tesis de expansión.

---

### Caso 2: Startup SaaS

#### EXTRAER — mapear flujos

**Entradas:** MRR 12.000€/mes de 80 clientes. Con churn del 8% mensual, pierden ~6,4 clientes/mes. Para mantener 80 necesitan adquirir 6-7 nuevos cada mes. Si no, en 12 meses tendrán ~30 clientes. El MRR de 12K es un espejismo: no es un ingreso estable, es un ingreso que se erosiona activamente.

30% del MRR (3.600€/mes) viene de 3 clientes grandes — concentración de riesgo extrema.

**Salidas:** Burn de 28.000€/mes. Incluye salarios de 3 juniors + 1 diseñador part-time + infraestructura + algo de salario para CTO y CEO. Ingresos cubren solo el 43% del burn.

**Lo que queda:** Deficit mensual neto: 16.000€/mes. Con runway de 7 meses, la caja tiene ~112.000€. Decrece a ritmo constante. Se acaba en julio-agosto 2026.

**Deudas:** No se mencionan deudas bancarias. La "deuda" es contra el tiempo — 7 meses de vida. Posiblemente equity prometida al co-fundador que se fue.

**Activos:** El producto (47 bugs abiertos — se deprecia activamente). Base de clientes (80, en erosión). Código fuente (frágil con 3 juniors sin CTO técnico original). Goodwill con 3 clientes grandes. Nada tiene valor de liquidación significativo.

**Coste de la hora:** CTO trabaja 70h/semana, ~3.640h/año. Si cobra 3.000€/mes, son 0,82€/hora. Un CTO con ese perfil podría ganar 80-120K€/año en mercado. Quema entre 60-100K€ anuales de coste de oportunidad.

#### CRUZAR — flujos × riesgo

Ingresos dependen parcialmente del producto pero con 8% de churn, el producto no funciona suficiente. Los ingresos se erosionan automáticamente. Si paran un mes de ventas, los ingresos caen un 8% por churn natural.

Costes masivamente fijos: salarios son el grueso. Algo de control (despedir gente), pero despedir devs con 47 bugs abiertos es contraproducente.

Colchón: 7 meses. Punto. Después, muerte.

El dinero que ganan hoy no compra seguridad — alimenta una hemorragia.

#### LENTE L1 — Valor presente

El valor DCF es probablemente negativo. No genera caja, la consume.

El CEO promete que pivotar a enterprise resolverá todo. Pero un pivot enterprise con 3 juniors y 47 bugs es una fantasía financiera. Enterprise exige estabilidad, soporte, SLAs, implementación customizada — todo lo que no tienen.

El CTO promete que estabilizar bajará churn. Más base lógica, pero el tiempo necesario para arreglar 47 bugs con 3 juniors es probablemente 4-6 meses — casi todo el runway.

Tasa de descuento: altísima. Con 7 meses de vida, cada mes futuro vale exponencialmente menos.

#### LENTE L2 — Apalancamiento

No usan deuda bancaria. Están apalancados con EQUITY y TIEMPO. El runway es un crédito que se consume sin poder renovarse a menos que consigan la Serie A.

Ese apalancamiento temporal amplifica las pérdidas: cada mes que pasa sin mejorar métricas, el runway se reduce Y las métricas se degradan. Ciclo de refuerzo negativo.

Los 3 fondos que rechazaron vieron exactamente esto.

#### LENTE L3 — Opcionalidad

Mantener opciones abiertas es caro: 16K€/mes. Brutal.

Estabilización tiene mejor asimetría que pivotar: si funciona, abre puerta a funding; si no, preserva algún valor residual. Pivotar a enterprise con la infraestructura actual es alta inversión con baja probabilidad.

La única forma de comprar tiempo es reducir burn o generar más ingreso (subir precios, cobrar por features custom). Lo segundo es inmediato y reversible.

#### LENTE L4 — Margen de seguridad

Margen de seguridad: casi nulo. 7 meses, 8% churn mensual, 47 bugs, 2 devs que se fueron en 12 meses, relación CTO-CEO rota. Sistema al límite en TODAS las dimensiones.

Un imprevisto de 10.000€ recorta un mes de runway y puede desencadenar cascada.

El plan funciona solo si MUCHAS cosas salen bien simultáneamente. Eso no es un plan, es esperanza.

#### INTEGRAR (∫)

Valor presente de la empresa probablemente negativo. Apalancamiento temporal se consume sin retorno. La única opcionalidad rescatable es estabilizar para mejorar métricas y hacer viable funding O adquisición. Margen de seguridad no existe. Falta todo.

#### ABSTRAER

Perfil clásico de startup que muere: burn alto, ingresos insuficientes, churn destructor, fundadores divididos. La variable vida/muerte es retención: si churn baja del 8% al 3-4%, el negocio se vuelve viable. Si no, nada más importa.

#### FRONTERA

La relación rota entre CTO y CEO es un activo negativo que no aparece en la hoja de cálculo pero contamina cada decisión. La pregunta real no es "¿pivotar o estabilizar?" sino "¿merece la pena seguir quemándote por algo que los datos dicen que va a morir?"

**Resumen:** MRR de 12K€ con churn del 8% es ingreso en erosión activa — sin adquisición constante, en 12 meses quedarían ~30 clientes. Burn de 28K€/mes genera déficit de 16K€ mensuales con runway de 7 meses. Concentración del 30% en 3 clientes amplifica fragilidad. Apalancamiento temporal se consume sin retorno. Pivotar a enterprise con 3 juniors y 47 bugs tiene asimetría terrible. Estabilizar tiene mejor perfil. Variable vida/muerte: retención. Relación CTO-CEO rota es pasivo no contabilizado. Tres fondos validaron que las métricas no dan.

**Firma:** El runway es una deuda contra el tiempo que no se puede refinanciar. Con churn del 8%, el MRR no es un activo sino un pasivo que se erosiona — cada mes que pasa sin resolver retención acerca la muerte, no la aleja.

---

### Caso 3: Cambio de carrera

#### EXTRAER — mapear flujos

**Entradas:** Salario 180.000€/año (15.000€/mes). Marido freelance: 40-80K€/año (volatilidad enorme). Ingreso familiar total: 220-260K€/año.

**Salidas:** Hipoteca 1.800€/mes (21.600€/año), 15 años pendientes (~270K€ total). Gastos familiares estimados: 4.000-6.000€/mes adicionales. Total salidas: 6.000-8.000€/mes mínimo.

**Lo que queda:** Excedente de 7.000-13.000€/mes. Los 120K€ ahorrados en 20 años a 180K indican gasto alto histórico.

**Con salario ONG:** Ingreso familiar baja a 95-135K€/año. Excedente cae a 0-5.250€/mes. En escenario pesimista, podría estar en déficit.

**Deudas:** Hipoteca ~270K€ a 15 años. Manejable a 180K, presión enorme a 55K (39% del bruto).

**Activos:** 120K€ ahorrados. Vivienda (con hipoteca). Capital humano: 20 años de experiencia corporativa — valor enorme pero se deprecia rápido fuera del sector.

**Coste de su hora:** 180K€/año en ~2.200-2.500h = 72-82€/hora. Pero insomnio 2 años, estrés diagnóstico, 3 años pensando en irse — costes reales que se pagan con salud.

#### CRUZAR — flujos × riesgo

Ingresos actuales estables pero dependientes de presencia y rendimiento. Ingresos del marido ya volátiles. Si ella baja a 55K, el ingreso familiar se vuelve volátil por partida doble.

Costes relativamente fijos: hipoteca, educación de adolescentes, nivel de vida. Control limitado a corto plazo.

Colchón: 120K€ = 15-20 meses de supervivencia sin ingresos. Decente pero finito.

El dinero que gana hoy compra seguridad pero NO bienestar: el insomnio y el estrés son la factura que el dinero no paga.

#### LENTE L1 — Valor presente

VP de la diferencia salarial: 125K€/año × 20 años restantes = ~1,5M€ descontado. Es mucho dinero.

"Quizá el próximo ciclo" para socia es una promesa vaga — la rechazaron, probabilidad baja.

"Si no lo hago ahora, no lo haré nunca" = tasa de descuento personal altísima sobre el cambio. Probablemente correcta: a los 50 será más difícil, a los 55 imposible.

Ambos salarios son "seguros" — la diferencia es cantidad, no certeza.

#### LENTE L2 — Apalancamiento

Apalancamiento moderado. Hipoteca pasa de carga manejable a presión dominante con salario ONG. No destruye, pero transforma la situación.

El banco gana lo mismo independientemente. La rigidez de la hipoteca reduce opcionalidad.

Con 120K€ y posible refinanciación, tiene colchón significativo. Incómodo pero no destructivo.

#### LENTE L3 — Opcionalidad

El coste de la opción "quedarse y decidir después" es real y creciente: edad, acostumbramiento, golden handcuffs, deterioro de salud.

Asimetría del cambio: si sale bien, recupera salud y propósito. Si sale mal, puede volver al sector pero con descuento.

Asimetría de quedarse: si sale bien, quizá socia (baja probabilidad). Si sale mal, más insomnio, crisis de salud, divorcio potencial.

**Puede comprar tiempo:** Excedencia, reducción jornada, consultoría legal medioambiental privada. El marco binario "quedarme o irme" destruye opcionalidad. Existe espacio enorme entre 55K y 180K no explorado.

#### LENTE L4 — Margen de seguridad

120K€ = 15-20 meses de gastos. Margen real.

Pero: universidad del hijo mayor en 2 años (10-20K€/año extra). Con salario ONG, esto come parte significativa.

Un imprevisto de 30K€ con salario ONG sería estrés real pero no destructivo. Con salario actual, anecdótico.

Plan de cambio funciona si marido mantiene ingresos, hipoteca se gestiona, universidad manejable, y ella efectivamente mejora en salud. Funciona incluso si alguna falla, pero sin margen.

#### INTEGRAR (∫)

El VP del salario actual es enorme pero se sostiene sobre salud que se degrada. Apalancamiento manejable con ambos salarios pero presiona fuerte con salario ONG. La opcionalidad mejor no es el cambio binario sino explorar opciones intermedias. Margen de seguridad existe pero se consume si varios factores coinciden mal.

#### ABSTRAER

Perfil sostenible 5 años financieramente con salario actual. No sostenible 5 años en salud. Se parece al patrón de profesionales que queman capital de salud para sostener capital financiero. La variable que separa escenarios es si puede encontrar un punto intermedio entre 180K y 55K. Ese punto existe (consultoría, reducción jornada, of-counsel) pero no lo ha explorado.

#### FRONTERA

La diferencia entre dormir y no dormir durante 2 años no tiene precio. El análisis financiero revela que hay un espacio enorme entre 55K y 180K que ella no ve porque ha enmarcado el problema como binario. Y no ha hablado con su marido — el co-inversor de su vida financiera.

**Resumen:** Salario actual de 180K€ sólido pero sobre salud en deterioro. Cambio a ONG reduce ingresos 69%, con hipoteca consumiendo 39% del bruto y viabilidad dependiente de marido freelance con ingresos volátiles. VP de la diferencia salarial: ~1,5M€. Los 120K€ dan 15-20 meses de colchón. La opcionalidad real está en opciones intermedias no exploradas: consultoría, reducción jornada, excedencia. El marido no consultado invalida cualquier plan. Marco binario es el error principal.

**Firma:** El marco binario (180K vs 55K) es una ilusión que destruye la opcionalidad más valiosa: el espacio intermedio. Y tomar una decisión financiera de 1,5M€ sin consultar al co-inversor (marido) es el mayor riesgo del caso.

---

### Loop test (P06)

**Caso elegido:** Clínica Dental

La segunda pasada sobre mi propio output reveló:

1. **Margen posiblemente pre-IRPF** — el ratio de fragilidad real podría ser 0,14, no 0,22.
2. **Opción de EXIT no identificada:** venta de clínica por 2-3x margen = 168-252K€. Cambia la opcionalidad radicalmente.
3. **Hipoteca construye equity en inmueble** — la deuda no es solo coste, también adquisición de activo que se revaloriza.
4. **Optimización cuantificada del tercer sillón:** del 60% al 90% = 5-7K€ adicionales/mes SIN nueva deuda. Casi duplica el margen.
5. **Seguro de baja laboral** — dato faltante que modera la fragilidad declarada.

La primera pasada se centró en flujos y no en stock de valor. La segunda reveló que el dentista tiene más opciones y activos de lo que el análisis de flujos sugería.

### Patrón cross-case

**Patrón 1 — Enmarcado binario que destruye opcionalidad:** Los tres sujetos ven solo dos opciones cuando la respuesta financiera óptima está en un espacio intermedio que ninguno considera. Los tres tienen un co-decisor no consultado o en conflicto cuya posición cambia todo.

**Patrón 2 — Confusión flujo/posición:** Los tres miran cuánto entra y sale pero no ven el stock de valor que acumulan o destruyen (clínica como activo vendible, código que se deprecia, capital humano sectorial depreciable).

### Saturación (P07)

Una tercera pasada refinaría números (impuestos reales, seguros, valor de liquidación) pero no revelaría estructura nueva. El patrón principal (enmarcado binario + co-decisor ausente + confusión flujo/posición) ya está identificado. Saturación parcial — útil para precisión, no para insight.

---

**FIN RESULTADOS F1-07 FINANCIERA**



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/LINGUISTICA.md
============================================================

# F1-09: INTELIGENCIA LINGÜÍSTICA (INT-09)

**Firma del álgebra:** REENCUADRE — cambiar el marco lingüístico cambia lo que es visible.
**Objetos:** palabras, marcos, narrativas, metáforas, actos de habla.
**Punto ciego declarado:** confunde nombrar con resolver — poner nombre no cambia la estructura.

---

## CASO 1: CLÍNICA DENTAL

### EXTRAER — mapear el lenguaje

Las palabras que usa el odontólogo son de contabilidad y expansión: "facturar", "subir a 65.000€/mes", "ampliar a 5 sillones", "abrir sábados", "contratar otro dentista". Es un léxico de ingeniería de negocio. Las palabras que evita son las de pérdida: no dice "estoy agotado", no dice "mi matrimonio está en riesgo", no dice "tengo miedo de repetir la historia de mi padre". La metáfora dominante es la de **construcción/expansión** — el negocio como edificio que se agranda. El sujeto gramatical oscila: cuando habla de expansión dice "yo" implícito ("puedo subir a 65.000"), pero el contexto familiar llega en boca de otros ("la esposa dice", "los niños preguntan"). Él no habla de los niños; su esposa habla por ellos. Lo que nombra con precisión: cifras (45.000€, 32.000€, 280.000€, 2.800€/mes, 2.500 horas). Lo que deja vago: su salud, su deseo, su miedo. La palabra que repite sin saberlo es "más" implícito: más sillones, más horas, más dentistas, más facturación. La palabra que falta: **descanso**. No aparece en ningún lugar. Tampoco "padre" como modelo a evitar; el dato del infarto paterno está ahí como hecho, no como advertencia que él verbalice.

### CRUZAR — lenguaje × realidad

El nombre que le da al problema es "oportunidad de crecimiento" (el banco ofrece crédito, él puede subir facturación). Ese nombre define qué soluciones puede imaginar: todas van hacia arriba y hacia fuera. Si cambiara la palabra clave de "expandir" a "intensificar sacrificio", la solución imaginable cambia completamente: ya no se trata de cuántos sillones añadir sino de cuánto más puede tolerar. Dice "crecer" cuando el tercer sillón está vacío el 40% del tiempo — lo que realmente necesita es **llenar** antes de **ampliar**. Dice "puedo" (subir a 65K) cuando la pregunta real es "debo" o "quiero". Su lenguaje agranda la dimensión operativa del problema (cifras, sillones, horarios) y achica la dimensión humana (familia, salud, historia familiar).

### LENTE L1 — Marco

El marco impuesto es **inversión/retorno**: crédito bancario → más sillones → más ingresos. Es un marco financiero puro. Este marco ayuda a calcular pero limita lo que es visible: invisibiliza el coste en tiempo, salud y familia porque esos no aparecen en la hoja de cálculo. Marco alternativo 1: **sostenibilidad** — "¿este ritmo es mantenible 10 años más?" Hace visible la trayectoria hacia el infarto paterno. Marco alternativo 2: **suficiencia** — "¿cuánto es suficiente?" Hace visible que 7.000€/mes neto con 60h/semana podría optimizarse antes de escalar.

### LENTE L2 — Actos de habla

Está **justificando** una decisión que ya siente correcta ("si abro sábados y contrato, puedo subir..."). No está pidiendo consejo; está construyendo el argumento para expandir. Lo que dice intenta convencerse a sí mismo más que informar. Hay algo performativo: al decir "puedo subir a 65.000€" está creando la posibilidad como hecho, solidificándola. La frase de la esposa ("no paras nunca") es un **acto de habla indirecto**: describe un hecho pero pide un cambio. Los niños "preguntan por ti" es una acusación velada en formato inocente.

### LENTE L3 — Metáforas

La metáfora que vive sin ser elegida es **la escalera** — cada paso lleva más arriba, y arriba es mejor. Esa metáfora implica que detenerse es fracasar (no subes = bajas). Otra metáfora implícita: el negocio como **máquina** que se alimenta de horas-dentista. Las máquinas no descansan; se les añaden piezas. Una metáfora alternativa: el negocio como **jardín** — necesita poda, estaciones, barbecho. Un jardín que crece sin parar se ahoga en su propia densidad.

### LENTE L4 — Silencios

No dice: "tengo miedo de acabar como mi padre." No dice: "no sé si quiero seguir siendo dentista a este ritmo." No dice: "el crédito del banco me ata más." No dice: "mi esposa podría irse." Los silencios sobre la salud y la familia no son por ignorancia — los datos están ahí (infarto paterno, queja de la esposa). Es porque nombrarlos obligaría a actuar de forma incompatible con la expansión. El silencio protege la decisión que ya quiere tomar.

### INTEGRAR (∫)

El marco (inversión/retorno) apunta hacia arriba. Los actos de habla (justificación) confirman que ya decidió. Las metáforas (escalera, máquina) refuerzan la dirección. Pero los silencios (salud, padre, matrimonio) cuentan la historia contraria. Hay una contradicción profunda: el lenguaje explícito construye el caso para expandir, mientras el lenguaje implícito grita que el sistema ya está sobrecargado. La coherencia superficial es una fachada lingüística.

### ABSTRAER

Este lenguaje — cifras como argumento, futuro como justificación, silencio sobre lo personal — es el idioma estándar del emprendedor que confunde crecimiento con progreso. En inglés se diría "scaling up" con la misma trampa: "scale" evoca grandeza, no carga. En castellano, "crecer" es especialmente potente porque es positivo por defecto: nadie cuestiona el crecimiento. El idioma condiciona.

### FRONTERA

Nombrar "expansión" como lo que es — intensificación del sacrificio — no resuelve nada por sí mismo. Pero la ilusión de control que da la palabra "crecer" sí bloquea activamente la reflexión. El análisis lingüístico aquí no añade distancia; es el único que ve que el problema no es de sillones sino de vocabulario. La palabra que no se dice — "basta" — sería la más transformadora.

### RESUMEN (200 palabras)

El odontólogo habla en lenguaje de negocio: cifras, sillones, facturación. Su marco es inversión/retorno y su metáfora implícita es la escalera ascendente. Dice "crecer" cuando debería decir "intensificar sacrificio". La palabra "descanso" no aparece. La salud, el padre, el matrimonio están presentes como datos pero ausentes como reflexión propia — llegan en boca de otros o como hechos sueltos. Los actos de habla revelan que no está preguntando sino justificando una decisión ya tomada. Las metáforas (escalera, máquina) imponen una lógica donde detenerse equivale a retroceder. Los silencios sobre el infarto paterno y la queja marital protegen la narrativa de expansión: nombrarlos obligaría a una conclusión incompatible con la dirección deseada. El marco financiero hace invisible todo lo que no tiene precio. El reencuadre clave: cambiar "¿debería expandir?" por "¿qué estoy sacrificando al expandir, y lo sabe alguien aparte de mi esposa?" desplaza el eje de decisión del Excel a la vida. El punto ciego de esta lente: nombrar todo esto no mueve un sillón ni cambia un horario.

---

## CASO 2: STARTUP SaaS

### EXTRAER — mapear el lenguaje

Hay dos lenguajes en colisión. El CTO habla en léxico de **ingeniería**: "producto", "estabilización", "47 bugs", "calidad", "sólido". El CEO habla en léxico de **supervivencia darwinista**: "crecer o morir", "pivotar", "enterprise", "los restaurantes no pagan suficiente". El CTO evita las palabras de mercado, negocio, estrategia. El CEO evita las palabras de deuda técnica, calidad, retención. La metáfora dominante del CTO es la **construcción**: el producto como edificio que necesita cimientos antes de pisos. La del CEO es la **guerra/carrera**: hay que moverse rápido o morir. El sujeto gramatical del CTO es condicional impersonal: "si el producto fuera sólido" — no dice "yo haré que sea sólido". El CEO usa imperativo existencial: "si no crecemos, morimos" — el "nosotros" es interesante porque en la práctica apenas se hablan. Lo que se nombra con precisión: métricas (80 clientes, 12K MRR, 8% churn, 7 meses runway, 28K burn, 47 bugs). Lo vago: la relación entre cofundadores, el motivo real de salida del cofundador técnico ("diferencias de visión" — frase que oculta más de lo que revela). La palabra que se repite: "si" condicional — "si el producto fuera sólido", "si no crecemos", "si pivotar". Todo está en modo hipotético; nadie habla en presente. La palabra que falta: **cliente**. Los clientes aparecen como número (80) o como fuente de dinero o de bugs, pero nadie dice qué necesitan, qué valoran, por qué se quedan los que se quedan.

### CRUZAR — lenguaje × realidad

El CTO nombra el problema como "deuda técnica" y eso define su solución: estabilizar. El CEO lo nombra como "falta de crecimiento" y eso define la suya: pivotar. Si el CTO cambiara "estabilizar" por "recuperar la confianza de los clientes", su plan parecería menos técnico y más estratégico. Si el CEO cambiara "pivotar a enterprise" por "abandonar a nuestros clientes actuales para buscar otros", la propuesta se revelaría como lo que es: un reinicio, no una evolución. El CTO dice "si el producto fuera sólido, el churn bajaría solo" — usa un condicional irreal que expresa un deseo más que un plan. No es un diagnóstico técnico; es una **plegaria ingenieril**. El CEO dice "si no crecemos, morimos" — esto no es información, es un **veredicto que cierra el debate**. Ambos lenguajes agrandan su propia dimensión del problema y achican la del otro.

### LENTE L1 — Marco

Coexisten dos marcos incompatibles. El CTO opera en marco **calidad/solidez**: primero construir bien, luego escalar. El CEO opera en marco **velocidad/supervivencia**: escalar es condición de existencia. Ninguno de los dos tiene un marco de **integración** — no existe en su vocabulario conjunto una frase tipo "qué haríamos si tuviéramos que elegir una sola cosa que mejore retención Y abra enterprise". El marco de calidad limita porque ignora el reloj (7 meses). El marco de supervivencia limita porque ignora que pivotar con 47 bugs es construir sobre arena. Marco alternativo: **triage** — no curar todo ni correr; decidir qué salvar.

### LENTE L2 — Actos de habla

El CTO está **diagnosticando**: "47 bugs abiertos, clientes se van por calidad." Pero su diagnóstico funciona también como **excusa** para no abordar el mercado. El CEO está **mandando**: "insiste en pivotar" — no negocia, decreta. La frase "los restaurantes no pagan suficiente" es una **sentencia** que cierra una puerta sin datos que la sostengan. "Diferencias de visión" (sobre el ex-cofundador) es un **eufemismo institucional** — un acto de habla que nombra el conflicto sin revelar nada. Lo performativo: "si no crecemos, morimos" al decirse y repetirse crea la urgencia que justifica cualquier acción precipitada. Es una profecía que se autocumple lingüísticamente.

### LENTE L3 — Metáforas

La metáfora del CTO: el producto como **cuerpo enfermo** que necesita curación antes de esfuerzo. Implicación no dicha: los clientes son "pacientes" del producto, el CTO es el "médico". Esta metáfora excluye la posibilidad de que el producto esté sano pero mal dirigido. La metáfora del CEO: el mercado como **selva darwinista**. Implicación: no hay cooperación, no hay nicho, solo hay depredadores y presas. Si la metáfora fuera **cultivo** (regar lo que crece, podar lo que no), la estrategia natural sería identificar a los clientes que funcionan y optimizar alrededor de ellos — exactamente lo que nadie propone.

### LENTE L4 — Silencios

No se dice: "¿nuestros clientes están contentos con lo que hacemos bien?" No se dice: "¿por qué se fueron 2 devs en 12 meses?" No se dice: "el ex-cofundador tenía razón en algo." No se dice: "CTO y CEO ya no confían el uno en el otro." El silencio más poderoso: nadie habla del **30% de ingresos de 3 clientes grandes**. Es un dato enorme (dependencia de concentración, demandas de features custom) que no tiene vocabulario propio en la discusión. Se menciona como dato pero no se nombra como problema ni como oportunidad. El silencio sobre la relación CEO-CTO protege a ambos: nombrar la desconfianza obligaría a confrontarla o separarse.

### INTEGRAR (∫)

Los dos marcos cuentan historias incompatibles pero simétricas: cada uno diagnostica al otro como el problema. Los actos de habla confirman la simetría: uno diagnostica, el otro decreta, ninguno negocia. Las metáforas refuerzan las trincheras: cuerpo enfermo vs. selva darwinista. Los silencios — sobre clientes, sobre la relación, sobre el ex-cofundador — son el terreno donde realmente vive el problema. La contradicción mayor: ambos dicen "nosotros" ("si no crecemos") pero actúan como "yo contra ti". El lenguaje compartido no existe.

### ABSTRAER

Este patrón — cofundadores que hablan idiomas diferentes dentro de la misma empresa — es universal en startups en crisis. En inglés, "pivot" tiene una connotación deportiva positiva (giro ágil) que oculta que pivotar = admitir que el plan falló. "Estabilizar" en cualquier idioma suena conservador, lo que penaliza al CTO en un contexto donde la velocidad es el valor dominante. El idioma startup (inglés importado al castellano) privilegia sistemáticamente la acción sobre la reflexión.

### FRONTERA

Nombrar que "pivotar" es "abandonar clientes" y que "estabilizar" es "plegaria ingenieril" no resuelve la tensión CEO-CTO. Pero el análisis lingüístico revela algo que ningún dashboard muestra: el problema no es técnico ni de mercado; es que dos personas con lenguajes incompatibles toman decisiones sobre lo mismo sin traducirse mutuamente. El riesgo: el reencuadre puede parecer "solo palabras" mientras el runway se acaba.

### RESUMEN (200 palabras)

CTO y CEO hablan idiomas diferentes: ingeniería vs. supervivencia darwinista. El CTO diagnostica ("47 bugs, calidad"), el CEO decreta ("crecer o morir"). Ambos usan condicionales irreales que expresan deseos, no planes. La palabra clave ausente es "cliente" como sujeto con necesidades propias — solo aparecen como métricas o fuente de problemas. "Pivotar" oculta "abandonar clientes actuales"; "estabilizar" oculta "no sé cómo abordar el mercado". Las metáforas son antagónicas: cuerpo enfermo (CTO) vs. selva darwinista (CEO). Ninguno tiene vocabulario de integración o triage. Los silencios más reveladores: nadie nombra la concentración de ingresos en 3 clientes, nadie habla del ex-cofundador con honestidad, y el deterioro de la relación CEO-CTO no tiene nombre. Lo performativo es decisivo: "si no crecemos, morimos" crea la urgencia que impide pensar. El reencuadre que esta lente ofrece: el problema no es técnico ni de mercado sino de traducción — dos personas gobiernan la misma empresa con lenguajes que no se tocan. Punto ciego: diagnosticar la fractura lingüística no produce un sprint ni cierra bugs.

---

## CASO 3: CAMBIO DE CARRERA

### EXTRAER — mapear el lenguaje

La abogada usa dos registros en tensión. Registro A — **urgencia existencial**: "si no lo hago ahora, no lo haré nunca", "he perdido la pasión". Registro B — **contabilidad del miedo**: "no puedo arriesgar la estabilidad de mis hijos", hipoteca, salario, ahorros. Las palabras que evita: no dice "quiero", dice "he perdido la pasión" (describe una ausencia, no afirma un deseo). No dice "decido" — todo está en modo contemplativo ("pensando", 3 años). La metáfora dominante es la de **prisión/escape**: está atrapada en algo que ya no quiere, el cambio es "salir". El sujeto gramatical es interesante: cuando habla del deseo, es "yo" tímido ("he perdido", "si no lo hago"). Cuando habla del miedo, es impersonal y exterior: "no puedo", "los padres dicen", "el marido es freelance" — como si las restricciones fueran fuerzas de la naturaleza, no decisiones negociables. Lo que nombra con precisión: cifras (180.000€, 55.000€, 1.800€, 120.000€). Lo que deja vago: qué haría exactamente en la ONG, si ha hablado con alguna, si hay posiciones intermedias. La palabra que repite sin saberlo: **"no"** — "no lo haré nunca", "no puedo arriesgar", rechazada para socia. La palabra que falta: **"quiero"**. Aparece como ausencia de pasión, no como presencia de deseo. Tampoco aparece **"marido"** como aliado — aparece como dato financiero (ingresos irregulares).

### CRUZAR — lenguaje × realidad

El nombre que le da al problema es "cambio de carrera", lo que enmarca la decisión como binaria: quedarse o irse. Si lo renombrara como "rediseño de vida profesional", aparecerían opciones intermedias (part-time, consultoría medioambiental, transición gradual). Dice "si no lo hago ahora, no lo haré nunca" — esto no es información, es una **cuenta atrás autoimpuesta** que presiona sin datos. ¿Por qué "nunca"? Tiene 45 años, no 65. La frase "he perdido la pasión" enmarca el cambio como consecuencia de una pérdida, no como búsqueda activa. Esto importa: quien huye de algo toma decisiones diferentes de quien va hacia algo. Su lenguaje ni agranda ni achica el problema: lo **paraliza**. Las frases de urgencia y las de miedo se cancelan mutuamente. El resultado lingüístico es estancamiento disfrazado de deliberación.

### LENTE L1 — Marco

El marco dominante es **todo-o-nada**: 180K→55K, bufete→ONG, prestigio→propósito. Es un marco de salto al vacío. Este marco maximiza el riesgo percibido porque no hay gradaciones. Marco alternativo 1: **transición** — pasos intermedios, puentes, períodos de prueba. Hace visible que entre 180K y 55K hay un espectro. Marco alternativo 2: **portafolio** — una vida con múltiples fuentes de valor (parte corporativo, parte medioambiental). Hace visible que "cambiar" no tiene que ser "reemplazar".

### LENTE L2 — Actos de habla

Está **confesando**: "he perdido la pasión" es una confesión íntima dicha con la gravedad de quien revela un secreto. Está **citando**: los padres ("estás loca"), la amiga ("por fin vive"), el médico ("estrés laboral"), el bufete ("quizá el próximo ciclo"). Su voz propia está enterrada bajo citas de otros. Lo performativo: "si no lo hago ahora, no lo haré nunca" es una sentencia que al decirse crea la urgencia y simultáneamente la parálisis — si es ahora o nunca, y ahora no puede, entonces nunca, y "nunca" es intolerable, así que sigue en el bucle. Es un acto de habla que se autoderrota.

### LENTE L3 — Metáforas

La metáfora implícita: la carrera como **cárcel** (está atrapada, necesita escapar, los hijos son rehenes de su estabilidad). Implicación no dicha: el bufete es el carcelero, el salario son los barrotes. Esta metáfora excluye la posibilidad de que el bufete sea negociable, reformable, o parcialmente útil. Una metáfora alternativa: la carrera como **río** — ahora está en un cauce que no le gusta, pero los ríos se desvían, hacen meandros, se bifurcan. No hay que saltar; hay que redirigir. Otra metáfora presente sin nombrarse: la amiga como **explorador** que ya cruzó — "por fin vive" es el relato del otro lado, la tierra prometida. Peligro: seguir un mapa ajeno.

### LENTE L4 — Silencios

No dice: "quiero trabajar en derecho medioambiental" — dice que perdió la pasión en corporativo. La dirección es away-from, no toward. No dice: "he hablado con ONGs y esto es lo que ofrecen." Tres años pensando sin investigar activamente es un dato lingüístico: el silencio operativo sugiere que la deliberación es una posición, no un proceso. No dice: "mi marido apoya esto" — porque no ha hablado con él. El silencio conyugal es el más estratégico: mientras no hable, la decisión permanece en el espacio seguro de la fantasía. Nombrarla ante el marido la haría real y obligaría a una respuesta. No dice: "ser socia en este bufete ya no me interesa" — la frase "quizá el próximo ciclo" está citada del bufete, no rechazada por ella. ¿Y si la hicieran socia mañana? El silencio sobre esa pregunta es revelador.

### INTEGRAR (∫)

El marco (todo-o-nada) presiona. Los actos de habla (confesión, citas de otros) revelan que no habla con voz propia. Las metáforas (cárcel, tierra prometida) dramatizan la decisión hasta la parálisis. Los silencios (marido, investigación real, deseo activo) cuentan la historia real: no está decidiendo, está fantaseando con decidir. La contradicción central: el marco dice "hay que saltar" pero los silencios dicen "no he dado el primer paso que no requiere saltar (hablar con el marido, llamar a una ONG)". El lenguaje de urgencia y el comportamiento de parálisis son coherentes solo si se entiende que la urgencia es una forma de postergar — "es tan importante que no puedo hacerlo mal" = no lo hago.

### ABSTRAER

Este patrón lingüístico — urgencia paralizante, confesión sin acción, citación de voces ajenas — es el idioma estándar de la crisis de mitad de carrera. En inglés, "I've lost my passion" se dice igual y produce la misma trampa: enmarca el problema como interno (pérdida psicológica) cuando podría ser externo (mala asignación de talento). El castellano añade un matiz: "no puedo arriesgar" es gramaticalmente más absoluto que "I can't risk" — el "no puedo" en español cierra más que en inglés donde "can't" coexiste fácilmente con "but maybe."

### FRONTERA

Nombrar que "3 años pensando" es una posición y no un proceso podría romper el bucle — o podría añadir culpa al estancamiento. El análisis lingüístico aquí revela con nitidez que el problema no es de información (sabe los números, conoce las opciones) sino de **enunciación**: no ha dicho "quiero esto" en primera persona, en voz alta, a alguien que le importa. La primera acción no es financiera sino lingüística: decirlo. Pero el riesgo de la lente: creer que decirlo es hacerlo.

### RESUMEN (200 palabras)

La abogada habla en dos registros que se cancelan: urgencia existencial ("si no lo hago ahora, nunca") y contabilidad del miedo ("no puedo arriesgar"). La palabra "quiero" está ausente — sustituida por "he perdido la pasión", que describe huida, no búsqueda. Tres años de deliberación sin investigación operativa (no ha hablado con ONGs, ni con su marido) revelan que deliberar es su posición, no su proceso. Su voz propia está enterrada bajo citas: padres, amiga, médico, bufete. El marco todo-o-nada (180K vs. 55K) maximiza el riesgo percibido e invisibiliza opciones intermedias. La metáfora dominante es la cárcel, donde el salario son los barrotes y la ONG es la tierra prometida vista a través de la experiencia de la amiga. El silencio más estratégico: no hablar con el marido mantiene la decisión en el espacio seguro de la fantasía. Lo performativo es autodecretante: "nunca" crea la urgencia que paraliza. El reencuadre que ofrece esta lente: la primera acción no es financiera sino lingüística — decir "quiero" en voz alta a alguien que importa. Punto ciego: decirlo no es hacerlo.

---

## POST-3-CASOS

### LOOP TEST

**Caso elegido: Caso 3 — Cambio de Carrera** (análisis más profundo por la riqueza de actos de habla y silencios estratégicos).

Segunda pasada — aplico las preguntas de INT-09 a mi propio output del Caso 3:

**EXTRAER sobre mi output:** Mi análisis usa un léxico de **diagnóstico clínico del lenguaje**: "performativo autodestructivo", "silencio estratégico", "voz-collage", "urgencia paralizante". La metáfora que gobierna MI relato es la de **arqueología** — excavar capas de significado debajo de lo dicho. El sujeto de mis frases es "ella" analizada desde fuera. Nombro con precisión sus mecanismos lingüísticos pero dejo vago algo importante: **cómo se siente**. Mi análisis es brillantemente frío. La palabra que yo repito sin notarlo: **"no"** y **"ausencia"** — mi análisis está construido sobre lo que falta, no sobre lo que hay. La palabra que falta en mi propio output: **"valiente"**. Tres años sosteniendo esta tensión sin colapsar, con insomnio, sin apoyo, es también un acto de resistencia. Mi lente no lo ve.

**CRUZAR sobre mi output:** El nombre que le doy al problema ("parálisis disfrazada de deliberación") cierra la posibilidad de que su deliberación sea genuina y productiva internamente aunque no visible externamente. Si cambio mi etiqueta de "parálisis" a "gestación", lo que ella hace — sostener la contradicción sin romper — adquiere un valor diferente. Mi lenguaje achica su agencia.

**Lo que revela la segunda pasada:** Mi análisis tiene el mismo punto ciego que la inteligencia declara: confunde nombrar con resolver. Más sutilmente: al diagnosticarla tan precisamente como "paralizada", contribuyo a fijar la etiqueta. Si ella leyera mi análisis, podría sentirse más atrapada, no menos. La segunda pasada revela que mi lente tiene sesgo hacia la **patologización del silencio** — interpreto todo silencio como evasión cuando algunos silencios son protección legítima o gestación necesaria.

**¿Es genuinamente nuevo?** Sí. El hallazgo de que mi propio análisis puede fijar la parálisis al nombrarla es una paradoja que la primera pasada no podía ver: la herramienta de diagnóstico puede agravar la enfermedad.

### PATRÓN CROSS-CASE

Hay un patrón que aparece en los tres casos independientemente del dominio: **la palabra que gobierna la decisión es invisible para quien la usa**. El dentista dice "crecer" sin ver que significa "intensificar sacrificio". El CEO dice "crecer o morir" sin ver que crea la urgencia que impide pensar. La abogada dice "no puedo" sin ver que es una elección gramatical, no un hecho. En los tres casos, el lenguaje funciona como **infraestructura invisible de la decisión** — determina qué opciones son pensables antes de que el análisis empiece. Y en los tres, la palabra más transformadora es la que no se dice: "basta" (dentista), "cliente" (startup), "quiero" (abogada).

Segundo patrón: en los tres casos, las **voces de otros** ocupan el espacio donde debería estar la voz propia. La esposa habla por el dentista. Padres, amiga y médico hablan por la abogada. El ex-cofundador fantasma habla por la startup sin estar. La crisis de decisión es, en los tres, una crisis de enunciación en primera persona.

### SATURACIÓN

Una tercera pasada aportaría matices pero no hallazgos nuevos. Los mecanismos centrales (marco invisible, metáfora no elegida, palabra ausente, voz delegada) ya están identificados y se repiten con variaciones de dominio. La segunda pasada del loop test ya mostró el metanivel (la herramienta puede agravar). Una tercera correría el riesgo de sofisticación circular.

### FIRMA FINAL INT-09

**Lo que esta inteligencia ve y probablemente ninguna otra vería:** Las decisiones no empiezan cuando se eligen opciones — empiezan cuando se nombra el problema. La palabra que falta en cada caso (basta, cliente, quiero) es más diagnóstica que todas las cifras juntas. El lenguaje no describe la realidad; la construye, la limita, y a veces la encarcela.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/NARRATIVA.md
============================================================

# RESULTADOS F1-12: NARRATIVA (INT-12)

## INT-12: NARRATIVA

### Caso 1: Clínica Dental

**Resumen:** El odontólogo vive dentro de una historia que no escribió: la del padre trabajador que se sacrifica hasta romperse. Se narra como constructor-proveedor, pero los hechos muestran a alguien atrapado en un ciclo donde "más" siempre significa más horas, más deuda, más ausencia. El tercer sillón vacío al 40% delata que el problema no es capacidad sino organización, pero su narrativa solo tiene gramática para "expandir." La esposa funciona como Casandra, el banco como tentador, el padre como fantasma-espejo. La transformación pendiente es identitaria: pasar de dentista que más produce a dueño que mejor gestiona. Esa transformación exige soltar la ecuación sufrimiento=valor. Hay una ventana temporal irreversible: hijos de 4 y 6 años cuya infancia no espera. Si firma el crédito sin cambiar de historia, entra en el tercer acto de una tragedia que ya conoce el final. Lo que necesita no son más sillones sino otra narrativa.

**Firma:** Lo que atrapa al odontólogo no es un problema de negocio sino una historia heredada que no sabe que está viviendo. El crédito bancario no es una decisión financiera — es el Acto 3 de la tragedia de su padre.

---

### Caso 2: Startup SaaS

**Resumen:** La startup está muriendo no por bugs ni por falta de mercado sino por narrativas incompatibles. El CTO vive un drama de artesanía: si el producto fuera sólido, todo se arreglaría. El CEO vive un thriller de supervivencia: si no crecemos, morimos. Ambos tienen parte de razón, pero compiten por la narrativa correcta en lugar de co-escribir una nueva. El punto de no retorno ya pasó: la salida del co-fundador técnico rompió la historia de origen y nunca escribieron una nueva. Los 7 meses de runway son un reloj narrativo que exige resolución. Los devs junior están sin dirección, los 3 clientes grandes fragmentan el producto, los fondos emiten juicio sin comprometerse. La transformación pendiente es relacional: el CTO debe dejar el rol de artesano-mártir para convertirse en co-líder. El precio es aceptar que tener razón sobre calidad del código no salva la empresa si no hay historia compartida sobre hacia dónde ir.

**Firma:** La startup no muere por bugs ni por mercado sino por narrativas incompatibles. El CTO y el CEO no necesitan resolver un problema técnico o estratégico — necesitan co-escribir una historia sobre quiénes son ahora que el tercer fundador se fue.

---

### Caso 3: Cambio de carrera

**Resumen:** La abogada vive atrapada entre dos historias que convergen en parálisis: sacrificio noble por los hijos y vocación descubierta demasiado tarde. Ninguna la empuja a actuar. Lleva 3 años en un ciclo sin avance que se disfraza de deliberación. El acto que haría real el cambio — hablar con su marido — es exactamente lo que evita, porque mientras el cambio sea fantasía privada nunca puede fallar. El marido es el personaje Schrödinger: excluido para preservar la narrativa de imposibilidad. Los padres guardan el umbral del orden establecido. La amiga es heraldo del otro mundo. Los hijos son invocados como razón sin ser consultados. El rechazo para socia fue catalizador que absorbió en lugar de usar. La transformación pendiente: de mártir responsable a agente. De "no puedo" a "elijo". Los números dicen difícil pero viable (120K€ ahorrados, hipoteca manejable). El desenlace por defecto es profecía autocumplida: seguirá hasta que "ya es tarde" se convierta en realidad. La historia cambia cuando la fantasía se convierte en plan.

**Firma:** Lo que paraliza a la abogada no son las restricciones financieras sino dos historias que convergen en no-acción. El acto que cambiaría todo no es renunciar al bufete sino hablar con su marido — y lo evita porque mientras el cambio sea fantasía privada, nunca puede fallar.

---

### Loop test (P06)

**Caso elegido:** Cambio de carrera

**Hallazgos nuevos de la 2ª pasada:**
1. El análisis reproduce la misma simplificación narrativa que critica en la abogada: presenta "hablar con el marido" como punto único de resolución, igual que ella presenta "cambiar de carrera" como solución total.
2. La abogada puede evitar la conversación con el marido no por cobardía (primera lectura) sino por autoprotección: preservar la esperanza de que el cambio es posible en lugar de arriesgarse a confirmar que no lo es. Lectura narrativamente opuesta a la primera pasada.
3. El análisis cayó en el sesgo que denunció: presentó el cambio a ONG como "desenlace correcto" y quedarse como "profecía autocumplida", descartando opciones intermedias (ESG en bufete, reducción de jornada) por ser narrativamente insatisfactorias, no por ser peores.

**¿Genuinamente nuevo?** Sí. Los tres hallazgos son meta-narrativos y no son reformulación de la primera pasada. El hallazgo de que el analista reproduce el patrón del analizado es especialmente revelador del punto ciego de la inteligencia narrativa.

**No-idempotente:** Sí.

---

### Patrón cross-case

Los tres protagonistas viven dentro de historias que no examinan y que determinan qué opciones "existen." En los tres casos, el acto que cambiaría la historia es una conversación relacional que se evita (dentista→asociado, CTO→CEO, abogada→marido) porque hacerla convertiría la fantasía en realidad. Los tres mantienen una "narrativa de imposibilidad" que funciona como protección contra el riesgo de intentar y fracasar.

---

### Saturación (P07)

Tercera pasada no aportaría: saturación estructural alcanzada. El loop test ya reveló el hallazgo clave (el análisis narrativo reproduce los mismos patrones que denuncia). Solo quedarían micro-refinamientos.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/POLITICA.md
============================================================

# RESULTADOS F1-06: INTELIGENCIA POLÍTICA (INT-06)

**Estado:** Ejecutado — CR0
**Fecha:** 2026-03-07
**Inteligencia:** Política
**Objetos:** poder, alianzas, legitimidad, narrativa, coaliciones
**Firma:** NEGOCIACIÓN — redistribuir poder mediante acuerdo
**Punto ciego declarado:** confunde poder con verdad — lo que tiene apoyo no es necesariamente correcto

---

## Caso 1: Clínica Dental

### EXTRAER — Mapear poder

El poder de decisión real lo tiene el odontólogo. Es propietario, deudor hipotecario, operador principal. Formalmente decide él. Pero el poder real está fracturado: el banco tiene poder de habilitación (ofrece crédito que hace posible la expansión), la esposa tiene poder de veto emocional (su frase "los niños preguntan por ti" es una línea roja que, si se cruza definitivamente, puede detonar una crisis matrimonial que haría irrelevante la decisión de negocio), y el cuerpo del propio odontólogo tiene poder de veto biológico — el precedente del padre infartado a los 52 no es anécdota, es profecía operando como restricción no declarada.

Quien puede bloquear sin decidir: la esposa. No va a firmar un veto explícito, pero su agotamiento acumulado puede convertirse en ultimátum. El asociado también tiene poder de bloqueo pasivo — si se va, el sistema colapsa, y no hay indicio de que esté comprometido con la visión de expansión.

Influencia sin cargo: el padre (a través de su historia clínica convertida en narrativa familiar), los hijos (cuya ausencia de padre está siendo narrada por la esposa como daño), y el banco (que no manda pero legitima la ambición con la oferta de crédito).

La narrativa dominante es la del emprendedor que crece: "si trabajo más, gano más, y eso es bueno". Esta narrativa la controla el propio odontólogo, reforzada por el banco (que le dice "puedes crecer" porque le conviene prestar) y por la cultura de autónomos que equipara sacrificio con éxito.

### CRUZAR — Poder × Legitimidad

El poder formal y el real convergen parcialmente: él es propietario y decisor, pero el poder real de la decisión está condicionado por actores que no aparecen en ningún contrato. La esposa tiene legitimidad emocional y moral enorme (es madre de sus hijos, testigo de su agotamiento) pero cero poder formal sobre la empresa. El banco tiene poder de habilitación pero cero legitimidad para opinar sobre si debería expandir — su incentivo es prestar, no cuidar.

El asociado tiene un tipo de poder invisible: si se va, el sistema se tambalea. Pero nadie le ha dado voz en la decisión estratégica. Es un aliado tácito cuya lealtad se da por hecha sin negociación explícita.

La alianza implícita es odontólogo + banco: ambos ganan con la expansión (él en facturación, el banco en intereses). Nadie ha formado la alianza alternativa: esposa + datos del tercer sillón vacío + precedente del padre. Esa coalición, si se articulara, cambiaría todo.

¿Alguien cuya opinión cambiaría todo? La esposa, si dejara de expresar malestar difuso y formulara una posición clara con consecuencias explícitas. Y el asociado, si expresara si quiere o no trabajar más.

### LENTE L1 — Poder

Siguiendo el dinero: el banco decide más de lo que parece. Su oferta de crédito no es neutral — es un acto de poder que enmarca la expansión como la opción "inteligente". El odontólogo tiene poder operativo pero está atrapado en él: trabaja 60 horas semanales no porque quiera sino porque el sistema lo necesita para funcionar. Eso no es poder, es dependencia disfrazada de control.

El poder del odontólogo es estable en el corto plazo pero frágil en el largo: depende de su salud física, de la permanencia del asociado, y de la tolerancia de la esposa. Cualquiera de los tres puede colapsar sin aviso.

Poder que nadie reconoce pero todos obedecen: el reloj biológico. El padre tuvo infarto a los 52. El odontólogo tiene 38 y trabaja más horas. Nadie lo nombra como restricción de poder, pero está gobernando el horizonte temporal de todo el sistema.

### LENTE L2 — Coaliciones

Coalición actual: odontólogo + banco + narrativa de crecimiento. La mantiene unida el interés del odontólogo en probar que su sacrificio vale, y el interés del banco en colocar crédito.

Si se formara coalición esposa + datos (tercer sillón vacío 40%) + salud: ganaría la estabilización, perdería el ego del odontólogo y la comisión del banquero.

Lo que mantiene unida la coalición actual no es interés común sino miedo común: el miedo del odontólogo a que si no crece, su sacrificio actual no tiene sentido. Y el miedo difuso a que parar = fracasar.

Lo que la rompería: un evento de salud, una crisis matrimonial explícita, o que el asociado dimita.

### LENTE L3 — Narrativa

La historia dominante: "Soy un emprendedor que si se esfuerza más puede escalar su negocio." Esta historia la escribió la cultura del autónomo español reforzada por el banco. Favorece al banco (más crédito), al ego profesional del odontólogo, y al sistema que necesita que él no pare.

Historia alternativa con los mismos hechos: "Soy un profesional que ya factura 45K/mes con un sillón vacío el 40% del tiempo, lo que significa que mi problema no es tamaño sino eficiencia. Mi padre se mató trabajando así. Yo tengo dos hijos que no me ven. La expansión no es crecimiento, es huida hacia adelante."

Si esta narrativa alternativa se impusiera, la decisión cambiaría radicalmente: en lugar de más sillones, optimizar los existentes. En lugar de más horas, redistribuir las actuales. En lugar de crédito, margen.

### LENTE L4 — Legitimidad

Lo que da derecho a decidir aquí: riesgo asumido. El odontólogo ha asumido el riesgo hipotecario, el riesgo de salud, el coste personal. Eso le da legitimidad. Pero la esposa también ha asumido riesgo — el riesgo de criar sola, de sostener un hogar sin pareja presente. Su legitimidad para opinar es tan alta como la de él, pero no se le reconoce como stakeholder del negocio.

Quien tiene más legitimidad para decidir y no la está usando: la esposa. Lleva 2+ años como testigo directo del deterioro. Tiene los datos empíricos que el odontólogo no ve porque está dentro del sistema.

La decisión de expandir, si se toma solo por el odontólogo, será impuesta a la familia, no aceptada. Y las decisiones impuestas sobre los que más se ven afectados generan resentimiento acumulativo que se cobra más tarde.

### INTEGRAR

Las 4 lentes convergen: el poder formal del odontólogo es real pero frágil. La narrativa de crecimiento protege la decisión de expandir pero oculta datos que la contradicen (sillón vacío, salud, familia). La coalición banco+ego domina porque la coalición alternativa (esposa+datos+salud) no se ha articulado. La legitimidad para decidir está concentrada en quien menos ve, y dispersa en quienes más saben.

### ABSTRAER

Esta configuración es clásica: el fundador-operador que confunde poder con autonomía y crecimiento con éxito. Históricamente, en negocios familiares, la expansión sin coalición doméstica alineada produce o éxito económico con divorcio, o crisis de salud que fuerza el repliegue que debió ser voluntario. La tasa de éxito de expansiones con estos indicadores (operador al límite, activo infrautilizado, cero vacaciones, familia desalineada) es baja.

### FRONTERA

¿Analizar políticamente un problema personal lo convierte en algo que no es? Parcialmente. El odontólogo no tiene "adversarios" — tiene stakeholders con intereses divergentes. La lente política revela la distribución de poder y narrativa, pero el conflicto real es intrapersonal: él contra su propia narrativa de éxito. La herramienta política nombra las fuerzas externas, pero el campo de batalla es interno.

### Resumen

El odontólogo tiene poder formal total pero poder real fracturado. El banco habilita la expansión con incentivos propios. La esposa tiene legitimidad máxima y poder cero. El asociado tiene poder de veto pasivo sin voz estratégica. La narrativa dominante ("crecer = éxito") está escrita por la cultura del autónomo y reforzada por el banco, ocultando que el tercer sillón vacío el 40% indica un problema de eficiencia, no de tamaño. La coalición activa (odontólogo + banco + ego) domina porque la alternativa (esposa + datos + salud + precedente paterno) no se ha articulado como bloque. El poder del odontólogo depende de su cuerpo, la tolerancia de su esposa y la permanencia del asociado — tres variables que puede perder sin aviso. La legitimidad para decidir está inversamente distribuida respecto al poder: quien más sabe (esposa) menos decide, quien más decide (odontólogo) menos ve. La expansión, si se ejecuta sin realinear coaliciones, será una decisión impuesta a una familia que ya está al límite. El análisis político revela las fuerzas, pero el conflicto central es la guerra del odontólogo contra su propia narrativa de éxito.

**Firma:** La inteligencia política ve que el banco es un actor político disfrazado de servicio financiero, y que la esposa es el stakeholder con más datos y menos poder formal del sistema.

---

## Caso 2: Startup SaaS

### EXTRAER — Mapear poder

Poder de decisión real: fragmentado entre CTO y CEO, pero desigual. El CEO controla la narrativa estratégica (pivotar a enterprise) y probablemente controla las relaciones con inversores y la visión de producto que se vende externamente. El CTO controla la ejecución técnica — sin él, no hay producto. Pero el co-fundador técnico que se fue ya demostró que el CTO puede quedar en posición de dependencia sin contrapeso técnico senior.

Quien puede bloquear: los 3 clientes grandes que representan el 30% de ingresos. Si se van, el runway se acorta dramáticamente. Los juniors pueden bloquear por incapacidad — 47 bugs con 3 juniors es una cola que no se vacía, y si se van otros 2 devs (ya perdieron 2 en 12 meses), el producto se para.

Influencia sin cargo: los fondos de VC que rechazaron la Serie A. Su feedback ("métricas insuficientes") se ha convertido en la narrativa que gobierna las decisiones, aunque los fondos no tienen ninguna responsabilidad sobre la empresa. El co-fundador que se fue también ejerce influencia espectral: su salida legitimó la idea de que algo está roto en el core.

La narrativa dominante depende de quién hable. CEO: "Si no crecemos, morimos." CTO: "Si el producto fuera sólido, el churn bajaría solo." Son dos narrativas incompatibles que compiten por el mismo recurso (los 7 meses de runway). El CEO controla la narrativa externa (inversores, board), el CTO la interna (equipo técnico).

### CRUZAR — Poder × Legitimidad

El poder formal probablemente favorece al CEO (rol, equity, relación con inversores). El poder real está dividido: el CEO sin CTO no puede ejecutar, el CTO sin CEO no puede financiar. Pero la asimetría es clara: un CEO puede contratar CTOs, un CTO rara vez reemplaza al CEO en una startup.

El CTO tiene legitimidad técnica pero no legitimidad estratégica reconocida por el ecosistema inversor. El CEO tiene legitimidad estratégica (es quien habla con fondos) pero no tiene legitimidad técnica (47 bugs abiertos bajo su mandato estratégico).

La alianza implícita es CEO + fondos VC (comparten marco mental de crecimiento > estabilidad). El CTO está solo. Los juniors no son aliados — son dependientes. El diseñador part-time es irrelevante políticamente.

¿Alguien cuya opinión cambiaría todo? Los 3 clientes grandes. Si dijeran explícitamente "nos vamos si no arregláis los bugs", la narrativa del CEO se derrumbaría. Si dijeran "pagaríamos más por un producto estable", la narrativa del CTO ganaría terreno empírico.

### LENTE L1 — Poder

Siguiendo el dinero: 12K MRR con 28K burn = la empresa destruye valor cada mes. El dinero viene de 80 clientes, 30% concentrado en 3. El poder real lo tienen esos 3 clientes (sin saberlo) y el reloj del runway. El CEO controla cómo se gasta el dinero (burn allocation), el CTO controla lo que el dinero produce (código).

El poder es inestable. Con 7 meses de runway y churn del 8%, cada mes perdido reduce no solo el dinero sino las opciones políticas. A los 3 meses, el CEO negociará desde la desesperación, no desde la posición.

Poder que nadie reconoce: el churn del 8% es un voto mensual de los clientes. Cada mes, el 8% de los clientes dice "no" a la coalición actual. Es un plebiscito silencioso que nadie lee como dato político — solo como métrica de producto.

### LENTE L2 — Coaliciones

Coalición actual: CEO + narrativa de crecimiento + presión de VC. La mantiene unida el miedo a morir ("si no crecemos, morimos") que es real pero unidimensional.

Coalición potencial: CTO + clientes + datos de churn. Si el CTO articulara "los clientes se van por calidad, aquí están los tickets, aquí está el patrón", y los clientes grandes respaldaran esa lectura, la narrativa del CEO perdería base empírica.

Lo que rompería la coalición actual: que un fondo dijera "volved cuando el churn esté bajo 3%", o que dos de los tres clientes grandes se fueran. Ambos eventos son probables dado el trayecto actual.

Lo que mantiene unida la coalición del CEO no es interés compartido sino el vacío de alternativa: nadie ha articulado un plan de estabilización con números que compita con la narrativa de pivot enterprise.

### LENTE L3 — Narrativa

La historia del CEO: "Estamos en un mercado que no paga suficiente. La solución es ir a enterprise donde los tickets son grandes. Si no pivotamos, morimos." Esta narrativa favorece al CEO porque justifica su rol (vender a enterprise requiere un CEO comercial) y desplaza la culpa del churn al mercado, no al producto.

La historia del CTO: "El producto tiene 47 bugs. Los clientes se van por calidad. Si arreglamos el producto, el churn baja y las métricas mejoran para levantar la Serie A." Esta narrativa favorece al CTO porque justifica su rol (arreglar el producto requiere liderazgo técnico) y sitúa la causa del problema en la ejecución, no en el mercado.

Historia alternativa que nadie cuenta: "El co-fundador técnico se fue hace 6 meses por diferencias de visión. Dos devs se fueron en 12 meses. El CTO y CEO apenas se hablan. El problema no es mercado ni producto — es que los fundadores están en guerra fría y el equipo lo sabe y huye."

Si esta tercera narrativa se impusiera, la solución no sería pivotar ni estabilizar sino resolver la gobernanza: o alinean visión o uno de los dos se va, como ya hizo el primer co-fundador.

### LENTE L4 — Legitimidad

El CEO tiene legitimidad de rol (es CEO) y de riesgo (asume el burn). El CTO tiene legitimidad de construcción (escribió el producto) y de conocimiento técnico (sabe qué está roto). Ninguno tiene legitimidad de resultados — la empresa pierde dinero, clientes y personas.

Quien tiene más legitimidad y no la usa: los clientes. Son los únicos que pagan. Su voto (quedarse o irse) es el único dato empírico no manipulable. Pero nadie les ha preguntado en serio qué necesitan, qué los retendría, cuánto pagarían por un producto estable.

La decisión que se tome (pivotar o estabilizar) no será aceptada por el otro fundador. Es imposición, no acuerdo. Y en una startup de dos fundadores, la decisión impuesta produce la salida del perdedor — exactamente lo que ya pasó con el primer co-fundador.

### INTEGRAR

Las 4 lentes convergen: hay una guerra fría entre dos narrativas que compiten por el mismo recurso escaso (runway), sostenida por dos poderes asimétricos (CEO > CTO en legitimidad externa; CTO > CEO en legitimidad interna), sin que ninguna coalición alternativa se haya articulado con datos. La legitimidad empírica (la de los clientes) está siendo ignorada por ambos bandos. El diagnóstico político no es "pivotar vs estabilizar" sino "gobernanza rota disfrazada de desacuerdo estratégico".

### ABSTRAER

Esta configuración es el patrón clásico del cofundador war: dos narrativas incompatibles en competencia por recursos escasos con reloj de countdown (runway). En la mayoría de precedentes, o un fundador compra al otro o la empresa muere mientras debaten. Las startups que resuelven esto generalmente lo hacen con un board que fuerza la decisión — pero aquí no hay board funcional.

### FRONTERA

La lente política revela el conflicto de poder pero puede exagerarlo. Es posible que CEO y CTO simplemente tengan un desacuerdo legítimo sobre prioridades, no una guerra. Pero los datos (no se hablan fuera de reuniones, el primer co-fundador ya se fue, 2 devs se fueron) sugieren que el conflicto político es real, no proyectado por la herramienta.

### Resumen

La startup tiene una guerra fría entre dos narrativas: "crecer o morir" (CEO) vs "estabilizar para sobrevivir" (CTO). El poder formal favorece al CEO (relación con inversores, rol estratégico). El poder real está dividido: sin CTO no hay producto, sin CEO no hay financiación. La coalición dominante (CEO + narrativa VC + presión de crecimiento) no tiene base empírica sólida: el churn del 8% es un plebiscito mensual de clientes votando "no" al status quo. La coalición alternativa (CTO + clientes + datos de calidad) no se ha articulado con números. La narrativa que nadie cuenta es la tercera: el problema no es mercado ni producto sino gobernanza rota — el primer cofundador ya se fue, dos devs huyeron, CTO y CEO no hablan. Los clientes grandes tienen el poder más real (30% de ingresos, capacidad de irse) y la mayor legitimidad (son los únicos que pagan), pero nadie les pregunta. Con 7 meses de runway, la ventana política se cierra: en 3 meses las opciones de ambos se reducen a desesperación. El desacuerdo estratégico es síntoma; la causa es un conflicto de poder no resuelto.

**Firma:** La inteligencia política ve que el churn del 8% es un plebiscito silencioso de los clientes, y que la "diferencia de visión" estratégica es en realidad una guerra fría de gobernanza.

---

## Caso 3: Cambio de Carrera

### EXTRAER — Mapear poder

El poder de decisión formal lo tiene la abogada. Es adulta, empleada, con ahorros propios. Nadie puede impedirle dimitir. Pero el poder real está distribuido en una constelación de actores que no deciden pero condicionan.

Quien puede bloquear: el marido. No porque tenga autoridad formal, sino porque si no apoya el cambio, la logística familiar (dos hijos, hipoteca, su ingreso irregular) hace el salto económicamente temerario. Los hijos de 14 y 16 bloquean indirectamente: el mayor entra en universidad en 2 años, lo que convierte los próximos 24 meses en ventana de máximo coste económico y mínima flexibilidad.

Influencia sin cargo: los padres ("estás loca") ejercen presión moral que apela a la prudencia y a la narrativa de clase media donde un salario de 180K no se abandona. La amiga que hizo el cambio similar ejerce contra-influencia: es prueba viviente de que la alternativa es viable, aunque con coste económico. El bufete ejerce poder sistémico: la promesa de "quizá el próximo ciclo" para socia es una zanahoria diseñada para retener sin comprometerse.

La narrativa dominante la controla el sistema profesional: "Eres exitosa. Ganas 180K. Tienes prestigio. Solo alguien irracional abandonaría esto." Los padres refuerzan esta narrativa. El bufete la alimenta con la promesa de partnership.

### CRUZAR — Poder × Legitimidad

El poder formal es de ella. Pero el poder real de ejecutar el cambio depende de su marido (que no sabe la profundidad de la intención), de su colchón financiero (120K, suficiente para ~2 años de brecha salarial pero no para indefinido), y de la temporalidad de los hijos.

El bufete tiene poder sin legitimidad: la promesa de "quizá el próximo ciclo" es un acto de retención, no de reconocimiento. Después de 20 años y un rechazo a socia, su legitimidad para pedir más paciencia es mínima. Pero su poder es máximo: paga 180K.

La abogada tiene legitimidad máxima para decidir sobre su propia vida (20 años de carrera, ha probado el sistema, tiene datos empíricos de lo que le hace) pero no está usando ese poder. Lleva 3 años pensando sin actuar.

Las alianzas: padres + bufete + status quo forman la coalición de permanencia. Amiga + insomnio + "si no lo hago ahora" forman la coalición de cambio. El marido es el voto decisivo y nadie le ha pedido que vote.

La persona cuya opinión cambiaría todo: el marido. Si dice "te apoyo, reajustamos", la decisión se desbloquea. Si dice "no podemos permitírnoslo", la coalición de permanencia gana por knockout económico. Y ella no le ha preguntado.

### LENTE L1 — Poder

Siguiendo el dinero: 180K del bufete vs 55K de la ONG. La diferencia de 125K/año es el precio de la libertad, o el coste de la identidad, según quién lo cuente. El marido gana 40-80K irregulares, lo que significa que la familia opera sobre su sueldo como base. Ella tiene poder económico sobre la familia pero ese poder es también una cadena: si se va, el sistema financiero familiar se reescribe.

El poder del bufete es estable pero erosionado: la rechazan para socia, lo que significa que su poder dentro de la firma ya tiene techo. Externamente, sus 20 años de experiencia corporativa le dan poder de mercado que no está explorando (podría ir a otra firma, abrir boutique, hacer consultoría medioambiental de alto nivel).

Poder que nadie reconoce pero todos obedecen: el insomnio. Es el cuerpo ejerciendo veto. Lleva 2 años diciendo "esto no funciona" y la respuesta ha sido medicalizarlo ("es estrés laboral"), no politizarlo (es un sistema que extrae más de lo que devuelve).

### LENTE L2 — Coaliciones

Coalición de permanencia: padres + bufete + miedo económico + hijos por entrar a universidad + marido (por defecto, al no haber sido consultado). Potencia: muy alta. La mantiene unida el miedo a perder lo conocido.

Coalición de cambio: amiga + insomnio + frase "si no lo hago ahora" + pasión por derecho medioambiental + 120K ahorrados. Potencia: moderada pero creciente.

Lo que rompería la coalición de permanencia: que el bufete la rechace otra vez para socia (lo que convertiría la promesa en estafa confirmada), o que el insomnio escale a un episodio de salud grave.

Lo que fortalecería la coalición de cambio: que el marido se sume, que explore opciones intermedias (consultoría medioambiental a 100K en vez del salto a 55K), o que el mayor de los hijos dijera "mamá, estás mal".

### LENTE L3 — Narrativa

La historia dominante: "Tienes un buen trabajo. No arriesgues. Sé responsable." La escribieron los padres, la refuerza la clase social, y favorece a quien no quiere adaptarse al cambio (los padres no quieren preocuparse, el bufete no quiere perder talento, el sistema no quiere inestabilidad).

La historia que ella cuenta internamente: "He perdido la pasión. Esto me está matando. Si no lo hago ahora, no lo haré nunca." Esta narrativa favorece el salto pero tiene un componente de urgencia que puede ser real o puede ser la presión de 3 años de indecisión generando sensación de ahora-o-nunca artificial.

Historia alternativa que nadie ha formulado: "Soy una abogada de 45 años con 20 años de experiencia corporativa y pasión por derecho medioambiental. No tengo que elegir entre 180K y 55K. Puedo diseñar una transición de 2-3 años donde construyo práctica medioambiental, pruebo el mercado, reduzco dependencia del bufete gradualmente, y convierto mi experiencia corporativa en activo diferencial en el sector medioambiental."

Si esta narrativa se impusiera, la decisión dejaría de ser binaria (quedo/me voy) y se convertiría en un proyecto de transición con fases, datos intermedios y reversibilidad parcial.

### LENTE L4 — Legitimidad

Lo que da derecho a decidir: 20 años de experiencia, riesgo de salud asumido (2 años de insomnio), coste emocional pagado. La abogada tiene la legitimidad más alta de todos los actores: ha vivido la situación más tiempo y más profundamente que nadie.

Quien tiene legitimidad y no la usa: ella. Lleva 3 años deliberando sin ejecutar ni una sola acción exploratoria (hablar con ONGs, hacer consultoría pro bono en medioambiental, hablar con el marido). La inacción no es prudencia, es parálisis política: no ha formado la coalición que necesita para actuar.

La decisión será aceptada por los afectados solo si es compartida. Si dimite sin haber hablado con su marido en profundidad, es imposición. Si habla, negocia y diseña transición, es acuerdo. La diferencia entre imposición y acuerdo determina si el cambio genera libertad o culpa.

### INTEGRAR

Las 4 lentes convergen en un punto: ella tiene poder y legitimidad para decidir pero no los está ejerciendo. La narrativa de permanencia domina por inercia, no por mérito. La coalición de cambio existe pero no se ha articulado (especialmente porque el marido no ha sido consultado). El bufete ejerce poder de retención con legitimidad agotada (la rechazaron para socia). La verdadera pregunta política no es "¿me voy?" sino "¿he formado la coalición que necesito para irme, o estoy intentando saltar sola?"

### ABSTRAER

Patrón clásico de la crisis de mitad de carrera en profesiones de alto estatus. Precedentes: la mayoría de profesionales que dan el salto sin coalición doméstica alineada o lo revierten en 18 meses (culpa económica) o lo sostienen a coste relacional alto. Los que diseñan transiciones graduales con apoyo familiar articulado tienen tasas de éxito significativamente mayores.

### FRONTERA

La lente política ilumina algo genuino: ella no ha hecho política doméstica. No ha negociado, no ha formado coalición, no ha presentado un plan. Pero la frontera es real: ¿hay un conflicto de intereses o una persona contra sí misma? Ambos. El conflicto externo (familia, padres, bufete) es real pero manejable. El conflicto interno (miedo, culpa, identidad) es el que la paraliza, y la herramienta política no llega ahí.

### Resumen

La abogada tiene poder formal absoluto y legitimidad máxima (20 años de experiencia, insomnio como dato empírico, rechazo a socia como evidencia de techo). Pero no está ejerciendo ni uno ni otra. La coalición de permanencia (padres + bufete + miedo + inercia) domina por defecto porque la coalición de cambio no se ha articulado: el marido no ha sido consultado, las opciones intermedias no se han explorado, la narrativa alternativa (transición gradual en vez de salto binario) no se ha formulado. El bufete ejerce poder de retención con legitimidad agotada: "quizá el próximo ciclo" después de 20 años es retención, no promesa. Los padres ejercen presión moral desde un marco generacional que no contempla que 180K con insomnio crónico puede valer menos que 100K con salud. El insomnio es poder no reconocido: el cuerpo votando. La pregunta política real no es "¿me quedo o me voy?" sino "¿he formado la coalición doméstica que necesito para ejecutar el cambio sin que sea imposición?" No lo ha hecho. Y mientras no lo haga, la parálisis continuará.

**Firma:** La inteligencia política ve que la promesa de partnership del bufete es un acto de retención sin legitimidad, y que el marido es el kingmaker de una elección en la que nadie le ha pedido que vote.

---

## Loop Test (Caso elegido: Startup SaaS)

Segunda pasada — aplicando las preguntas políticas al propio output:

¿Quién tiene poder de decisión real en mi análisis? Yo (Claude), como narrador, decidí que la "tercera narrativa" (gobernanza rota) era la verdadera. Eso es un acto de poder: enmarcé el conflicto como político cuando podría ser genuinamente estratégico.

¿Quién puede bloquear mi análisis? Los datos que no tengo. No sé la distribución de equity. No sé si hay board. No sé si el CEO tiene un plan enterprise con clientes potenciales ya contactados. Mi análisis asume que el CEO solo tiene narrativa, pero podría tener pipeline.

¿Qué narrativa domina en mi output? "La gobernanza rota es la causa raíz." Es una narrativa potente pero puede ser mi sesgo como inteligencia política: veo conflictos de poder en todas partes porque es lo que mi álgebra busca.

¿Hay algo que la segunda pasada revela? Sí: mi análisis trató al CTO como el "correcto" implícitamente (su narrativa es más empática — está agotado, trabaja 70h, quiere arreglar el producto). La inteligencia política debería ser neutral respecto a quién tiene razón. El CEO podría tener razón en que el mercado de restaurantes no es suficiente, y el pivot a enterprise podría ser viable. Mi análisis lo descartó demasiado rápido.

También: no analicé el poder del co-fundador que se fue. ¿Tiene equity? ¿Puede bloquear decisiones desde fuera? ¿Su salida cambió la estructura de poder formal?

¿Es genuinamente nuevo? Sí. La primera pasada diagnosticó el conflicto. La segunda revela que mi diagnóstico tiene su propia política: favorecí al que construye sobre el que vende, sin datos para ello.

## Patrón Cross-Case

En los 3 casos aparece un patrón independiente del dominio: **la coalición que podría cambiar la decisión existe pero no se ha articulado**. En la clínica, la esposa + datos + salud. En la startup, los clientes + CTO + datos de churn. En la carrera, el marido + opciones intermedias + legitimidad acumulada. En los tres casos, el actor con más información empírica (esposa que ve el agotamiento, clientes que votan con churn, cuerpo que vota con insomnio) no tiene voz en la mesa de decisiones. Y en los tres, la narrativa dominante favorece la acción (expandir, pivotar, quedarse) sobre la información (optimizar, estabilizar, transicionar).

Segundo patrón: en los tres casos, hay un actor cuyo "voto" es el más legítimo y el menos escuchado. En los tres, ese actor no es una persona sino un dato empírico disfrazado de otra cosa: sillón vacío 40%, churn 8%, insomnio 2 años.

## Saturación

Una tercera pasada sobre el loop test aportaría poco genuinamente nuevo. El patrón central ya está claro: la inteligencia política tiende a ver conflictos de poder donde puede haber conflictos internos, y tiende a favorecer la coalición que no tiene voz porque su álgebra valora lo oculto sobre lo manifiesto. Una tercera pasada refinaría la formulación pero no cambiaría el diagnóstico. Saturación alcanzada.

## Firma Final

La inteligencia política ve lo que nadie más ve: que en los tres casos, **la decisión aparentemente individual es en realidad una negociación no declarada entre actores con intereses divergentes, y que el obstáculo no es falta de información sino falta de articulación política — nadie ha formado la coalición que necesita para actuar legítimamente**.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/PROSPECTIVA.md
============================================================

# INT-13: PROSPECTIVA — Resultados Fase 1

---

## Caso 1: Clínica Dental

### EXTRAER — mapear futuros

**Tendencias en curso.** Varias fuerzas se mueven simultáneamente. La clínica está en una trayectoria de saturación operativa: el propietario trabaja 60h/semana, el tercer sillón tiene 40% de ociosidad, y el margen neto (15.5% sobre facturación) es bajo para el riesgo asumido. La tendencia del sector odontológico en España apunta hacia consolidación — cadenas dentales (Vitaldent, Asisa Dental, etc.) presionan los precios a la baja y captan pacientes de gama media. La tendencia familiar es decelerada: la relación con los hijos y la esposa pierde velocidad, los niños de 4 y 6 años están en una ventana de vinculación que caduca.

**Aceleradas vs. deceleradas.** Acelerada: la presión de costes fijos (32K/mes no bajan, solo suben con inflación). Acelerada: el desgaste físico del propietario — 38 años con ritmo de 60h/semana, padre con infarto a los 52, eso son 14 años de margen biológico en el mejor caso. Decelerada: la capacidad de captar nuevos pacientes sin diferenciación — las cadenas absorben ese segmento. Decelerada: la ventana temporal de los hijos — cada mes que pasa sin presencia paterna es irrecuperable.

**Señales débiles.** El tercer sillón vacío al 40% es una señal potente que se lee mal. No indica "espacio para crecer" sino "demanda insuficiente para la capacidad actual". Si no llena 3, ¿por qué pensar que llenará 5? La frase de la esposa no es queja — es un ultimátum en fase temprana. El antecedente del padre no es anécdota — es un predictor genético y conductual.

**Supuestos no examinados.** Se asume que "más sillones = más ingresos" (lineal). Se asume que habrá dentistas disponibles y competentes dispuestos a trabajar como asociados. Se asume que los pacientes seguirán pagando precios de clínica privada mientras las cadenas ofrecen financiación agresiva. Se asume que la salud del propietario aguantará.

### CRUZAR — tendencias × supuestos

**Cruce 1: Consolidación sectorial × ampliación.** Si las cadenas dentales siguen presionando precios y él amplía a 5 sillones con más deuda, queda atrapado: más capacidad en un mercado que comprime márgenes. El cruce produce una trampa de escalamiento.

**Cruce 2: Desgaste personal × presión familiar.** Si el desgaste del propietario se cruza con la presión familiar, el resultado no es la suma — es un multiplicador. Un divorcio o una crisis de salud no resta margen, lo destruye.

**Supuesto que si cae, cambia todo.** "Los ingresos escalarán proporcionalmente con los sillones." Si el tercer sillón ya está vacío al 40%, añadir dos más requiere un salto de demanda que no está fundamentado. Si este supuesto cae, la ampliación es una carga de deuda sin retorno proporcional.

**Señales débiles: dirección.** Todas apuntan en la misma dirección: contra la expansión. Sillón vacío, familia tensionada, antecedente cardíaco, sector presionado. No hay señales débiles que apunten a favor.

**Fecha de caducidad.** La salud del propietario. A 60h/semana, sin vacaciones en 2 años, con predisposición genética, el cuerpo tiene una fecha de caducidad que no aparece en ningún Excel. El matrimonio también: las advertencias de la esposa tienen un número finito de repeticiones antes de convertirse en hechos.

### LENTE L1 — Escenarios

**Mejor caso realista.** El propietario NO expande. En su lugar, optimiza el sillón 3 (pasar de 60% a 85% de ocupación con marketing focalizado y/o especialización que justifique precio premium). Reduce sus horas a 45h/semana delegando más en el asociado. Facturación baja ligeramente a 42K pero costes no suben. Margen se mantiene. Recupera presencia familiar. Estabiliza salud.

**Peor caso realista.** Expande. Contrata dentista y abre sábados. Deuda sube a ~450K. Primeros 6 meses la facturación sube a 55K pero no a 65K. Los nuevos sillones tienen 50% de ociosidad. El propietario trabaja 70h/semana para "sacar adelante la inversión". A los 18 meses, crisis de salud o crisis matrimonial. La clínica queda con deuda ampliada y el propietario fuera de juego temporal o permanente.

**Más probable si nada cambia.** Expansión gradual, estrés creciente, deterioro de relaciones, rendimientos decrecientes. No un colapso dramático sino una erosión lenta: en 5 años trabaja más, gana marginalmente más, pero su vida personal está destruida y su salud comprometida.

**Escenario que nadie considera.** Venta de la clínica. Con 3 sillones, facturación de 45K/mes y cartera de pacientes establecida, la clínica tiene valor de mercado. Un grupo dental podría comprarla. El propietario podría quedarse como asociado sin las cargas de gestión, o salir completamente. Nadie lo considera porque "es MI clínica" — la identidad está fusionada con el negocio.

### LENTE L2 — Señales

**Señal de mejor caso.** El propietario empieza a delegar gestión administrativa y la ocupación del tercer sillón sube sin que él trabaje más horas. Eso indica que el cuello de botella era gestión, no capacidad.

**Señal de peor caso.** Firma el crédito para ampliar sin haber resuelto la ocupación del tercer sillón. Eso indica que la decisión es emocional ("más grande = más éxito"), no analítica.

**¿Ya aparecen?** La señal del peor caso está en formación: el banco ya ofreció el crédito, y el propietario ya verbaliza la proyección de 65K como si fuera cierta. La señal del mejor caso no aparece: no hay ninguna mención de optimizar lo existente.

**¿Alguien monitoriza?** No. La esposa monitoriza el deterioro familiar pero no el empresarial. El propietario monitoriza facturación pero no ocupación real, ni salud, ni calidad de vida. No hay ningún asesor externo mencionado.

### LENTE L3 — Bifurcaciones

**Punto de bifurcación.** La decisión de firmar o no el crédito de ampliación. Es un punto binario: firma o no firma. Todo lo posterior cambia radicalmente.

**Cuándo.** Está aquí. El banco ya hizo la oferta. La decisión es inminente.

**Reversibilidad.** Parcialmente reversible pero con alto coste. Si firma y falla, puede reducir sillones pero no puede devolver la deuda ni el tiempo perdido con la familia. Si no firma, la opción de expandir sigue abierta en el futuro. La asimetría favorece no firmar ahora.

### LENTE L4 — Comodines

**Fuera de modelo.** Una regulación que cambie el marco de las cadenas dentales (obligar a que un dentista sea propietario, por ejemplo) invertiría la presión competitiva y revalorizaría las clínicas independientes. Improbable pero posible.

**Evento improbable, alto impacto.** Crisis de salud del propietario. No es tan improbable dado el antecedente familiar y el estilo de vida. Si ocurre, la clínica sin él se paraliza — no hay plan de contingencia visible.

**Preparación.** Solo para lo esperado. No hay seguro de persona clave, no hay plan de continuidad si él cae enfermo, no hay protocolo de gestión sin él.

### INTEGRAR

Los cuatro ejes convergen en un patrón claro: **la expansión es una apuesta asimétrica — el downside es catastrófico, el upside es marginal.** Los escenarios muestran que el mejor caso no requiere expansión. Las señales actuales apuntan hacia el peor caso. La bifurcación es inminente y parcialmente irreversible. Y los comodines (salud) amplifican el riesgo. El patrón es: optimizar primero, proteger segundo, expandir solo después de haber resuelto las dos primeras.

### ABSTRAER

Este tipo de encrucijada tiene precedentes masivos: el emprendedor que confunde crecimiento con progreso. En restauración, el patrón es idéntico — el restaurante exitoso que abre segundo local antes de optimizar el primero, y ambos colapsan. En medicina, la literatura sobre burnout médico muestra que la correlación entre horas trabajadas y resultado clínico es una U invertida: pasado un umbral, más horas producen peor resultado. El precedente histórico dice: los que optimizaron antes de escalar sobrevivieron; los que escalaron para huir de problemas operativos amplificaron esos problemas.

### FRONTERA

El futuro del dentista no es predecible de forma determinista, pero sí probabilística. Y aquí hay un efecto de observador: el acto de analizar los futuros posibles debería cambiar la decisión. Si el dentista ve los escenarios escritos, la probabilidad de que firme el crédito sin reflexión disminuye. La prospectiva no predice — interviene. El problema es que sin alguien que le muestre los escenarios, el sesgo de acción ("hacer algo = progreso") domina.

### Resumen (≤200 palabras)

La clínica dental enfrenta una bifurcación inminente: expandir o optimizar. Las tendencias convergen contra la expansión: el sector se consolida (cadenas presionan márgenes), la capacidad actual tiene 40% de ociosidad en un sillón, el propietario opera al límite físico con antecedente cardíaco familiar, y la presión familiar escala. El supuesto clave no verificado — que más sillones producen ingresos proporcionalmente mayores — contradice la evidencia de que no llena los que tiene. Los escenarios muestran asimetría de riesgo: el mejor caso realista no requiere expansión (optimizar ocupación + delegar + reducir horas), mientras el peor caso (expandir → más deuda → más horas → crisis de salud o matrimonio) es catastrófico e irreversible. El comodín más probable es una crisis de salud del propietario, para la que no hay plan de contingencia. El escenario que nadie considera es vender la clínica. La señal más reveladora: el propietario proyecta 65K/mes como hecho cuando el tercer sillón está vacío al 40%. La prospectiva revela que esta decisión no es empresarial — es existencial, y el acto de mapear futuros puede cambiar cuál se materializa.

### Firma
La prospectiva revela que el dentista opera en un horizonte temporal de meses cuando sus riesgos reales tienen horizonte de años — y los años ya están contados por la genética y el desgaste acumulado.

---

## Caso 2: Startup SaaS

### EXTRAER — mapear futuros

**Tendencias en curso.** Varias fuerzas en movimiento simultáneo, todas con vectores de velocidad diferentes. El churn del 8% mensual es la tendencia dominante: a ese ritmo, la base de clientes se renueva completamente cada 12 meses, lo que significa que el producto no retiene. El MRR de 12K está estancado o en declive neto (los nuevos no compensan las pérdidas). El runway de 7 meses es un reloj que corre. La relación CEO-CTO está en deterioro progresivo — la comunicación se ha reducido a reuniones formales, lo cual es un indicador adelantado de ruptura. La tendencia del sector SaaS B2B apunta hacia especialización vertical profunda o hacia plataformas generalistas con capital masivo — el espacio medio (ni especializado ni capitalizado) se comprime.

**Aceleradas vs. deceleradas.** Acelerada: el churn — 8%/mes es un espiral; a medida que se van clientes, los que quedan reciben peor servicio (47 bugs) y se van más rápido. Acelerada: la quema de runway — cada mes que pasa reduce las opciones. Acelerada: la pérdida de talento — 2 devs en 12 meses, más el co-fundador técnico. Decelerada: la capacidad de captar inversión — 3 fondos dijeron no, y las métricas empeoran, no mejoran. Decelerada: la moral del equipo — 3 juniors con CTO exhausto.

**Señales débiles.** El 30% de ingresos concentrado en 3 clientes que piden features custom es una señal potente: esos 3 clientes están dispuestos a pagar más por algo más profundo. La señal no dice "pivotar a enterprise genérico" — dice "hay demanda de solución vertical profunda en un subsegmento". La salida del co-fundador técnico por "diferencias de visión" probablemente refleja exactamente este debate: ¿horizontal o vertical? El feedback de los fondos ("métricas insuficientes") es una señal de que el mercado de capital ya ha decidido: sin retención, no hay inversión.

**Supuestos no examinados.** CEO asume que "enterprise = más revenue" sin validar que el producto pueda servir a enterprise (complejidad, compliance, SLAs, soporte). CTO asume que "si el producto fuera sólido, el churn bajaría solo" — esto puede ser parcialmente cierto pero ignora que parte del churn puede ser product-market fit, no calidad. Ambos asumen que la empresa sobrevive 7 meses — pero si pierden otro dev, el burn no cambia y la capacidad operativa colapsa.

### CRUZAR — tendencias × supuestos

**Cruce 1: Churn acelerado × runway decreciente.** Esto produce una ventana de decisión que se cierra exponencialmente. No son 7 meses lineales — si el churn sigue y no hay crecimiento neto, en el mes 4-5 el MRR puede haber caído a 8K y el burn sigue en 28K. El runway real puede ser 5 meses, no 7.

**Cruce 2: Concentración de ingresos × pivot a enterprise.** Si los 3 clientes grandes representan 30% de ingresos (~3.6K/mes) y piden features custom, pivotear a "enterprise genérico" podría alejar a estos clientes que quieren algo específico. El pivot podría destruir la única fuente de ingresos con potencial de crecimiento.

**Supuesto que si cae, cambia todo.** "El CTO y el CEO pueden seguir trabajando juntos." Si la relación se rompe — y la tendencia dice que va hacia ahí — el CTO se va, y la empresa pierde su única capacidad técnica senior. Con 3 juniors solos, no hay product ni pivot ni estabilización.

**Señales débiles: dirección.** Las señales débiles apuntan en una dirección clara: profundizar el vertical de restaurantes con los clientes que ya pagan y piden más, no pivotar a enterprise genérico. Pero las señales del CEO apuntan en dirección opuesta. La empresa tiene dos brújulas que señalan nortes distintos.

**Fecha de caducidad.** La relación CEO-CTO. No se hablan fuera de reuniones formales. Esto tiene un horizonte de semanas a pocos meses antes de que uno de los dos decida que es irreconciliable.

### LENTE L1 — Escenarios

**Mejor caso realista.** CTO y CEO alcanzan un acuerdo: 4-6 semanas dedicadas a estabilizar (cerrar los 20 bugs más críticos que causan churn), mientras simultáneamente profundizan la oferta para los 3 clientes grandes. Suben precios a ese segmento. El churn baja de 8% a 4% en 3 meses. No captan inversión, pero extienden runway a 10-11 meses con los nuevos ingresos. A los 6 meses, métricas mejoran lo suficiente para volver a hablar con fondos.

**Peor caso realista.** CEO impone pivot a enterprise. CTO se va. Los 3 juniors intentan reconstruir el producto para un mercado que no conocen. Los 3 clientes grandes se van porque pierden atención. El churn sube a 12%. En 4 meses, MRR cae a 5K, burn sigue en 28K, la empresa cierra o se queda en zombie con 2 meses de vida.

**Más probable si nada cambia.** Parálisis decisional. CTO estabiliza a medias (no tiene tiempo ni equipo), CEO busca enterprise a medias (no tiene producto). Ninguno de los dos caminos se ejecuta con convicción. El churn se mantiene en 7-8%, el runway se agota, y en el mes 5-6 la decisión se toma por ellos: se acaba el dinero.

**Escenario que nadie considera.** Acqui-hire o venta del producto a uno de los 3 clientes grandes. Si un restaurante o cadena de restaurantes con múltiples locales valora el software lo suficiente como para pedir features custom, podría valorar comprarlo directamente. La empresa no vale mucho como SaaS, pero la tecnología + base de código + equipo podría tener valor para un comprador vertical.

### LENTE L2 — Señales

**Señal de mejor caso.** El CTO y el CEO se sientan fuera de una reunión formal y definen 3-5 prioridades conjuntas para los próximos 60 días. Si eso ocurre, hay alineación mínima para ejecutar.

**Señal de peor caso.** El CTO actualiza su LinkedIn o empieza a responder mensajes de recruiters. O un cuarto cliente grande se va. O un dev junior renuncia.

**¿Ya aparecen?** Las señales del peor caso están activas: 2 devs ya se fueron, la comunicación está rota, y no hay indicación de alineación. Las señales del mejor caso no aparecen en ningún dato del caso.

**¿Alguien monitoriza?** Nadie monitoriza las señales correctas. El CEO monitoriza "crecimiento" (nuevos clientes, pipeline enterprise). El CTO monitoriza "calidad" (bugs). Nadie monitoriza la relación entre ambos, que es la variable que determina si la empresa existe en 3 meses.

### LENTE L3 — Bifurcaciones

**Punto de bifurcación.** No es la decisión "pivotar vs. estabilizar" — eso es un falso dilema. El verdadero punto de bifurcación es: ¿el CTO y el CEO pueden negociar un plan conjunto en las próximas 2-4 semanas? Si sí, la empresa tiene opciones. Si no, la empresa está muerta caminando.

**Cuándo.** Está aquí, ahora. El reloj corre.

**Reversibilidad.** Si el CTO se va, es irreversible en términos prácticos — no hay tiempo ni dinero para reemplazarlo. Si se alinean y ejecutan mal, hay algo de margen para corregir. La bifurcación "relación se rompe" es un one-way door.

### LENTE L4 — Comodines

**Fuera de modelo.** Un competidor grande (Toast, MarketMan) compra la cartera de clientes o hace una oferta de adquisición. En el espacio foodtech SaaS, las adquisiciones de carteras pequeñas ocurren. Nadie lo ha considerado porque están mentalmente en "crecer o pivotar".

**Evento improbable, alto impacto.** Uno de los 3 clientes grandes resulta ser parte de una cadena en expansión y necesita el software para 20-50 locales. De repente, el revenue de ese solo cliente podría ser 5-10K/mes y cambiar todas las métricas.

**Preparación.** Cero preparación para lo inesperado. No hay escenarios de contingencia, no hay plan B si el CTO se va, no hay conversación sobre qué pasa si llega un comprador.

### INTEGRAR

El patrón que emerge es: **la variable que determina todos los futuros no es "producto" ni "mercado" sino "relación CEO-CTO".** Los escenarios se bifurcan ahí. Las señales apuntan hacia la ruptura. Los comodines positivos solo son posibles si la empresa sigue operativa, lo cual requiere esa relación. La trampa es que ambos están debatiendo estrategia (pivotar vs. estabilizar) cuando la pregunta real es anterior: ¿pueden trabajar juntos? Si la respuesta es sí, ambos caminos tienen viabilidad. Si la respuesta es no, ningún camino funciona.

### ABSTRAER

Precedente: la historia del SaaS está llena de empresas que murieron no por el producto sino por la ruptura del equipo fundador. El patrón Founders' Dilemma (Noam Wasserman) aplica: los fundadores que no resuelven diferencias de visión temprano terminan por resolverlas con la salida de uno — y la empresa rara vez sobrevive a la segunda salida de fundador. El primer co-fundador técnico ya se fue. Si el CTO se va, es el segundo. La tasa de supervivencia post-segunda-salida-de-fundador en startups pre-Series A es cercana a cero.

### FRONTERA

El futuro de esta startup está más cerca del caos que del determinismo. Con 7 meses de runway, un churn del 8%, y una relación fundadora rota, un único evento (un dev que se va, un cliente grande que cancela, una pelea en una reunión) puede precipitar un colapso que en un Excel lineal tardaría 7 meses. La prospectiva aquí revela que los modelos lineales (runway = burn/cash) son engañosamente tranquilizadores — las startups no mueren linealmente, mueren por cascadas de eventos interdependientes.

### Resumen (≤200 palabras)

La startup SaaS tiene un reloj de 7 meses (probablemente menos: el churn erosiona MRR más rápido que lo que refleja el runway nominal). Las tendencias aceleradas — churn espiral, pérdida de talento, deterioro de relación fundadora — dominan sobre cualquier estrategia. El falso dilema "pivotar vs. estabilizar" oculta la verdadera bifurcación: ¿pueden el CTO y el CEO alinearse en 2-4 semanas? Si sí, la mejor estrategia es estabilizar bugs críticos (bajar churn) mientras se profundiza la oferta para los 3 clientes grandes (subir revenue por cliente), no pivotar a enterprise genérico. El 30% de ingresos concentrado en 3 clientes que piden features custom es la señal más valiosa del caso: hay demanda de solución vertical profunda, no de plataforma genérica. El escenario no considerado es venta/acqui-hire. El comodín positivo es que un cliente grande escale. Las señales actuales apuntan abrumadoramente al peor caso: comunicación rota, talento fugándose, ningún indicador de alineación. La startup no morirá por falta de producto o mercado — morirá por la incapacidad de sus fundadores de resolver un conflicto que precede a toda decisión estratégica.

### Firma
La prospectiva revela que el debate estratégico (pivotar vs. estabilizar) es un síntoma del verdadero riesgo (ruptura fundadora) — y que las startups mueren por cascadas, no por agotamiento lineal de runway.

---

## Caso 3: Cambio de Carrera

### EXTRAER — mapear futuros

**Tendencias en curso.** La tendencia laboral de la abogada es de estancamiento con señales de declive: rechazada para socia ("quizá el próximo ciclo" es eufemismo habitual para "nunca"), 20 años en el mismo bufete, pérdida declarada de pasión. La tendencia salarial en derecho corporativo es estable-alta pero con creciente presión sobre horas (los bufetes exigen más, no menos). La tendencia del sector medioambiental y de ONGs es acelerada: legislación climática, ESG, litigios ambientales crecen globalmente. La tendencia de salud personal es decelerada: insomnio de 2 años con diagnóstico claro de estrés laboral es una trayectoria que no se estabiliza sola. La tendencia familiar se mueve hacia un punto de inflexión: el hijo mayor entra a universidad en 2 años, lo cual cambia la estructura de costes y la dinámica familiar.

**Aceleradas vs. deceleradas.** Acelerada: la demanda de abogados especializados en medioambiente — la regulación climática solo crece. Acelerada: el deterioro de salud — el insomnio crónico no diagnosticado como "estrés laboral" suele ser la antesala de problemas más serios (ansiedad, depresión, hipertensión). Acelerada: el reloj biológico de la decisión — a 45 años, cada año que pasa reduce la empleabilidad en un cambio de sector. Decelerada: la probabilidad de ser socia — si no fue ahora, el "próximo ciclo" en un bufete grande puede ser 3-5 años más, y la posición es cada vez más competitiva.

**Señales débiles.** La amiga que hizo el cambio similar es una señal social potente: alguien del mismo perfil lo hizo y sobrevive. El hecho de que no haya hablado con el marido en profundidad es una señal de que ella sabe (o teme) que la conversación materialice la decisión — mientras no habla, puede mantener la ambigüedad. Los 120K ahorrados son una señal de que inconscientemente lleva tiempo preparándose para una transición. El insomnio de 2 años marca el reloj biológico de la decisión: el cuerpo está forzando una resolución que la mente posterga.

**Supuestos no examinados.** Se asume que el salario en ONG es necesariamente 55K — pero una abogada corporativa con 20 años de experiencia que entra en derecho medioambiental podría tener un rango más amplio (consultoras de ESG, bufetes de interés público, organismos internacionales, no solo ONGs pequeñas). Se asume que el marido no puede compensar ingresos — sus 40-80K son irregulares, pero el techo no está verificado. Se asume que la estabilidad de los hijos depende principalmente del ingreso — pero una madre con insomnio crónico y sin pasión por su trabajo también es una forma de inestabilidad.

### CRUZAR — tendencias × supuestos

**Cruce 1: Crecimiento del derecho medioambiental × experiencia corporativa.** Este cruce es explosivamente valioso y nadie lo ve. Una abogada con 20 años en derecho corporativo que se mueve a medioambiente no empieza de cero: su expertise en compliance, regulación, due diligence es exactamente lo que las empresas necesitan para ESG y litigación climática. El cruce no es "dejar un sector para ir a otro" sino "crear un puente entre dos sectores que se necesitan".

**Cruce 2: Hijo entrando a universidad × ventana de decisión.** En 2 años, los costes suben (matrícula) pero también cambia la estructura: un hijo fuera de casa reduce gastos del hogar y flexibiliza la organización familiar. El timing no es "ahora o nunca" como ella cree — es "ahora para estar preparada cuando el hijo se vaya."

**Supuesto que si cae, cambia todo.** "Cambiar de carrera significa ganar 55K." Si el cambio no es a una ONG genérica sino a una posición híbrida (consultora ESG, departamento medioambiental de corporación, litigación climática en bufete especializado), el salario podría estar en 80-120K. Si este supuesto cae, la ecuación financiera cambia radicalmente.

**Señales débiles: dirección.** Todas las señales apuntan hacia el cambio, pero con matiz. No apuntan hacia "dejar todo y bajar a 55K" sino hacia "transición estratégica que preserve capital profesional". La amiga, los ahorros, el insomnio, la pasión perdida — todo señala: cambia, pero no de forma kamikaze.

**Fecha de caducidad.** La empleabilidad para el cambio. A 45 años tiene ventaja competitiva (experiencia + madurez). A 50, esa ventana se comprime. La otra fecha de caducidad es la salud: el insomnio crónico tiene consecuencias acumulativas que en 3-5 años se manifiestan como patología, no como síntoma.

### LENTE L1 — Escenarios

**Mejor caso realista.** La abogada no renuncia inmediatamente. Primero explora el mercado de posiciones híbridas (ESG, litigación climática, consultoría medioambiental para corporaciones) mientras sigue en el bufete. Encuentra una posición a 90-110K en 6-12 meses. Negocia salida del bufete con periodo de transición. El ingreso familiar pasa de ~220-260K a ~130-190K — significativo pero manejable con los 120K de colchón y el techo del marido.

**Peor caso realista.** Renuncia impulsivamente tras una crisis (pelea con socio, episodio de salud). Busca en ONG, acepta 55K. Marido tiene año malo (40K). Ingreso familiar cae a ~95K con hipoteca de 1.800/mes y universidad en 2 años. Los ahorros se queman en 18 meses. La presión financiera produce un estrés diferente pero igual de destructivo. Considera volver al derecho corporativo, pero ha perdido contactos y posición.

**Más probable si nada cambia.** Se queda otros 2-3 años "esperando el momento". El insomnio empeora. Quizá la ofrecen socia en condiciones mediocres que acepta por inercia. A los 48-50 años, la ventana de cambio se ha cerrado. Sigue ganando bien pero su salud está comprometida y vive con la narrativa de "no lo hice cuando pude."

**Escenario que nadie considera.** Montar su propio despacho boutique de derecho medioambiental para clientes corporativos. Con 20 años de contactos en el mundo corporativo y expertise regulatoria, podría ser la abogada que les ayuda con ESG, compliance medioambiental y litigación climática. Salario potencial: 120-200K en 2-3 años. Combina pasión con expertise sin sacrificar ingreso.

### LENTE L2 — Señales

**Señal de mejor caso.** Empieza a tener conversaciones exploratorias con contactos del sector medioambiental mientras aún está en el bufete. Si esas conversaciones revelan demanda de su perfil, el camino se abre.

**Señal de peor caso.** Otro rechazo para socia, o un episodio de salud serio (la línea del insomnio se cruza con ansiedad o depresión clínica). Eso forzaría una decisión desde la crisis, no desde la estrategia.

**¿Ya aparecen?** La señal del peor caso está en formación (insomnio de 2 años = pre-crisis de salud). La señal del mejor caso no aparece: no hay mención de exploración activa del mercado alternativo, solo fantasía con el puesto de ONG a 55K.

**¿Alguien monitoriza?** El médico monitoriza los síntomas pero no la causa. La amiga es un referente anecdótico, no un asesor. El marido no está informado. Los padres son detractores. No hay ningún profesional de transición de carrera involucrado.

### LENTE L3 — Bifurcaciones

**Punto de bifurcación.** No es "renunciar o quedarse" — eso es un falso binario. El verdadero punto de bifurcación es: ¿habla con su marido sobre una transición planificada, o sigue postergando hasta que un evento (salud, otro rechazo) fuerce la decisión? La conversación con el marido es el gate.

**Cuándo.** Lleva 3 años postergándola. El punto está aquí y se degrada con cada mes que pasa. No porque las opciones desaparezcan, sino porque la salud se deteriora y la inercia se consolida.

**Reversibilidad.** Una transición planificada es altamente reversible (puede volver a corporativo si falla). Una salida por crisis es mucho menos reversible (las puertas se cierran diferente cuando te vas enfadada o enferma que cuando te vas planificadamente).

### LENTE L4 — Comodines

**Fuera de modelo.** Una regulación de ESG agresiva en la UE que obligue a todas las empresas medianas a tener asesoría legal medioambiental. Esto multiplicaría la demanda de abogados con doble expertise (corporativo + medioambiental) y su perfil sería oro.

**Evento improbable, alto impacto.** Crisis de salud seria — no un insomnio sino un colapso nervioso o enfermedad derivada del estrés crónico. Esto forzaría una baja médica prolongada y posiblemente una salida no planificada del bufete, con todas las desventajas del peor escenario.

**Preparación.** Solo para lo esperado (seguir como está o cambiar a ONG a 55K). No hay preparación para opciones intermedias ni para emergencias de salud. Los 120K de ahorro son un colchón, pero sin plan de uso.

### INTEGRAR

El patrón convergente es: **el menú de opciones que la abogada considera (quedarse vs. ONG a 55K) es artificialmente estrecho, y la restricción no es el mercado sino la falta de exploración.** Los escenarios muestran que existen posiciones intermedias de 80-120K que combinan su expertise corporativa con la pasión medioambiental. Las señales todas apuntan hacia el cambio, pero no hacia el cambio que ella imagina (sacrificio heroico) sino hacia una transición que capitaliza su experiencia. La bifurcación real es la conversación con su marido. Y los comodines (regulación ESG, crisis de salud) amplifican tanto el upside como el downside de actuar o no actuar.

### ABSTRAER

Precedente claro: las transiciones de carrera exitosas en profesionales senior no son "saltos al vacío" sino "puentes entre expertise previa y nuevo sector." La literatura sobre career transitions de Herminia Ibarra muestra que los cambios más sostenibles ocurren por exploración lateral (experimentar antes de decidir), no por "gran renuncia" impulsiva. El arquetipo es: quien planifica el puente prospera; quien salta sin puente puede sobrevivir pero con costes enormes; quien se queda paralizado se deteriora lentamente.

### FRONTERA

El acto de predecir cambia radicalmente lo que pasará. Si la abogada ve que existe un mercado de 80-120K para su perfil híbrido, la decisión ya no es "pasión vs. dinero" sino "cómo organizar la transición." La prospectiva aquí no predice el futuro — expande el menú de futuros posibles, y al expandirlo, cambia cuál elige. El mayor riesgo no es elegir mal — es elegir solo entre las opciones que ve, cuando las mejores opciones son las que no ha explorado.

### Resumen (≤200 palabras)

La abogada opera con un menú artificial de dos opciones: quedarse a 180K sin pasión o saltar a ONG a 55K. La prospectiva revela que existe un tercer espacio amplio y no explorado: posiciones híbridas (ESG, litigación climática, consultoría medioambiental corporativa, despacho boutique propio) donde su experiencia de 20 años en corporativo tiene un valor diferencial enorme, con salarios de 80-120K o más. Las tendencias aceleran a su favor: la regulación climática y ESG crecen, la demanda de abogados con doble expertise sube. Las señales débiles (ahorros acumulados, amiga como referente, insomnio como forzador) apuntan todas hacia la transición. La verdadera bifurcación no es "renunciar o quedarse" sino hablar con su marido y empezar a explorar el mercado antes de decidir. El peor escenario no es cambiar — es quedarse hasta que la salud fuerce una salida no planificada. El escenario que nadie considera es el despacho boutique propio, que combina pasión, expertise y potencial de ingreso. La prospectiva no predice qué hará — expande las opciones que ve, y al expandirlas, cambia qué futuro es posible.

### Firma
La prospectiva revela que la abogada vive en un falso binario (quedarse vs. ONG a 55K) cuando el espacio de futuros incluye opciones híbridas de 80-200K que nadie ha explorado — y que el acto de ver esas opciones cambia la decisión.

---

## Loop Test (P06)

**Caso elegido: Startup SaaS**

Aplico las preguntas de Prospectiva a mi propio output del caso SaaS:

**EXTRAER sobre mi output.** Mi análisis tiene sus propias tendencias. La tendencia dominante de mi output es la convergencia hacia "la relación CEO-CTO es todo" — ¿esto es insight o es reduccionismo? Reviso: mi output identifica correctamente que es la condición necesaria, pero no es suficiente. Incluso si se alinean, con 3 juniors y 47 bugs, ¿pueden ejecutar? Mi primera pasada subestima la restricción de capacidad técnica. Con el co-fundador técnico fuera y solo juniors, la capacidad de ejecución tiene un techo que no mencioné suficientemente.

**Señal débil que no vi.** El co-fundador técnico que se fue por "diferencias de visión" — ¿y si su visión era la correcta? Si el tercer fundador vio algo que ni el CEO ni el CTO ven, su salida no es solo pérdida de talento sino pérdida de la visión que podría haber resuelto el dilema. Nadie habla de preguntarle.

**Supuesto que no examiné.** Mi output asume que los 3 clientes grandes son "la señal" de demanda vertical. Pero, ¿y si esos 3 clientes están satisfechos precisamente porque obtienen features custom que nunca se escalan al resto? Podrían ser anomalías que distorsionan la lectura de mercado, no confirmaciones de product-market fit.

**Escenario que mi primer análisis no consideró.** El CTO se va pero no a otro trabajo — se va para unirse al primer co-fundador técnico que se fue, y juntos crean una versión competidora del producto. Esto es un escenario no exótico: ocurre frecuentemente cuando dos técnicos comparten visión y el CEO era el problema. Si esto ocurre, la empresa original pierde su CTO, su IP operativa, y gana un competidor que conoce a todos sus clientes.

**¿El segundo análisis es genuinamente nuevo?** Sí, en tres puntos: (1) la restricción de capacidad técnica post-alineación, (2) la posibilidad de contactar al co-fundador que se fue como fuente de información estratégica, y (3) el escenario de fork competitivo. Estos no son repeticiones con otras palabras — son ángulos que la primera pasada no exploró.

## Patrón Cross-Case

El patrón que aparece en los tres casos vistos desde la lente prospectiva: **los tres sujetos operan con un menú de opciones artificialmente estrecho, y la restricción no es externa (mercado, dinero, opciones) sino interna (cómo definen el problema).** El dentista ve "expandir o seguir igual." El SaaS ve "pivotar o estabilizar." La abogada ve "quedarse o ir a ONG a 55K." En los tres casos, la prospectiva revela opciones intermedias o laterales que nadie ha explorado: optimizar y vender, acqui-hire, despacho boutique. El patrón universal es: **la calidad de la decisión está limitada por la amplitud del menú de opciones que el decisor es capaz de ver.** Y en los tres casos, ese menú está comprimido por la identidad del sujeto (soy propietario, somos una startup que crece, soy abogada corporativa).

## Saturación (P07)

¿Una tercera pasada aportaría algo nuevo? Probablemente sí, pero con rendimientos fuertemente decrecientes. La segunda pasada del SaaS reveló 3 insights genuinos. Una tercera pasada probablemente revelaría 1 insight marginal y mucha repetición. La curva de valor se aplana. Para la mayoría de los usos, dos pasadas son suficientes en prospectiva.

## Firma — INT-13 Prospectiva

**Lo que esta inteligencia ve que probablemente ninguna otra vería:** La prospectiva ve el espacio de futuros posibles como un mapa con bifurcaciones, y revela que el problema de los tres sujetos no es "qué decidir" sino "entre qué opciones decidir." La inteligencia prospectiva expande el menú de futuros antes de que la decisión se tome, y al hacerlo, cambia la decisión misma — es la única inteligencia cuyo output modifica las condiciones del problema que analiza.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/SOCIAL.md
============================================================

# RESULTADOS F1-08: INTELIGENCIA SOCIAL (INT-08)

**Fecha:** 2026-03-08  
**Inteligencia:** INT-08 — SOCIAL (interpersonal + intrapersonal)  
**Objetos:** emociones, intenciones, dinámicas, patrones reactivos, vínculos  
**Operaciones:** lectura empática, regulación emocional, calibración social  

---

## CASO 1: CLÍNICA DENTAL

### EXTRAER — Mapear emociones e intenciones

**¿Qué siente esta persona — no lo que dice, lo que siente?**

El odontólogo siente miedo. No miedo al fracaso empresarial — miedo a convertirse en su padre. Y al mismo tiempo, terror a no hacer suficiente. Hay una ambivalencia paralizante: la expansión le promete alivio económico, pero cada hora extra lo acerca al infarto de los 52. Lo que siente es una trampa emocional: "si paro, fracaso; si sigo, me destruyo." Debajo de eso hay culpa — culpa hacia sus hijos, culpa hacia su esposa, culpa por no ser capaz de hacer que funcione sin inmolarse.

**¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?**

Se nota en lo que elige cuantificar y lo que no. Tiene cifras exactas de facturación (45.000€), costes (32.000€), proyección (65.000€) — pero no tiene cifras de horas con sus hijos, ni de cuánto tiempo lleva sin dormir bien, ni de cuántas veces su esposa ha dicho variantes de "no paras nunca." Repite la lógica de "si hago X, puedo subir a Y" — el patrón de alguien que regula la ansiedad con planificación operativa. Evita nombrar el miedo al infarto: el dato de su padre aparece como contexto biográfico, no como alarma personal.

**¿Qué necesita realmente — no lo que pide, lo que necesita?**

Necesita permiso para parar. No permiso externo — permiso interno. Su identidad está fusionada con el rol de proveedor-sacrificado. Necesita que alguien le diga: "Puedes ser buen padre, buen profesional y estar vivo a los 55. No son excluyentes." Pero sobre todo necesita sentirse seguro sin crecer — y eso es exactamente lo que no puede sentir, porque el modelo que heredó de su padre equipara quietud con peligro.

**¿Quién más está afectado y cómo se sienten?**

La esposa siente soledad y resentimiento contenido. La frase "los niños preguntan por ti" es una queja cifrada — no habla por los niños, habla por ella. Usa a los niños como escudo emocional porque decir "yo te echo de menos" la pone en posición vulnerable. Los hijos (4 y 6 años) sienten la ausencia pero no pueden articularla — están en la edad donde la ausencia se normaliza y el daño se incrusta como patrón de apego. El asociado probablemente siente cierta presión silenciosa: trabaja 1.800h/año al lado de alguien que trabaja 2.500h/año — la comparación está implícita.

**¿Hay emociones que nadie nombra pero que gobiernan las decisiones?**

Sí: el duelo anticipado. Este hombre está haciendo duelo por una versión de sí mismo que todavía no ha perdido pero sabe que va a perder — el padre presente, el marido disponible, el hombre sano. Ese duelo no está nombrado; lo que está nombrado es "oportunidad de crecimiento." La expansión no es estrategia — es anestesia. Mientras planifica sillones, no siente el vacío.

---

### CRUZAR — Emociones × relaciones

**¿Lo que siente esta persona coincide con lo que muestra?**

No. Muestra ambición empresarial ("puedo subir a 65.000€/mes"). Siente agotamiento existencial. La distancia entre ambos es enorme. Para su entorno, es un emprendedor con visión de crecimiento. Por dentro es un hombre atrapado que confunde avanzar con huir.

**¿Los demás perciben lo que realmente pasa o solo la superficie?**

La esposa percibe parcialmente — su radar emocional detecta la ausencia, pero posiblemente no la causa profunda. Probablemente interpreta la adicción al trabajo como falta de priorización, cuando en realidad es un mecanismo de defensa heredado. El banco no percibe nada — ve un cliente solvente con capacidad de endeudamiento. Los padres probablemente ven la repetición del patrón y no dicen nada, o lo normalizan porque fue el patrón de su propia generación.

**¿Hay patrones — esta situación se repite, se parece a otras anteriores?**

El patrón es transgeneracional y explícito: su padre trabajó 70h/semana y tuvo un infarto a los 52. Él trabaja 60h/semana a los 38 y planea subir la carga. La pregunta no es si se parece — es si está replicando el script exacto con la ilusión de que a él le irá diferente. Probablemente lleva toda la vida viendo a su padre como ejemplo de lo que no hacer, y sin embargo está haciendo exactamente lo mismo. Esa es la paradoja de los patrones heredados: se reconocen en tercera persona pero no en primera.

**¿Qué trigger activó la crisis actual?**

La oferta del banco. Antes de la oferta, el estrés era crónico pero estable — una especie de malestar administrado. La oferta cristaliza una decisión: expandir o no. Y esa decisión, por primera vez, exige que se posicione: ¿soy alguien que elige más, o alguien que elige suficiente? El segundo trigger, menos visible, es la edad de los hijos. A los 4 y 6 años, los niños empiezan a formar memorias duraderas. Lo que haga ahora es lo que recordarán.

**¿Lo que pide es lo que necesita, o pide una cosa para obtener otra?**

Pide validación para expandir. Necesita permiso para no hacerlo. El acto de preguntar "¿debería expandir?" ya revela que no quiere hacerlo — si quisiera, ya habría firmado.

---

### LENTE L1 — Empatía

**¿Puedes ponerte en su lugar — qué se siente ser esta persona ahora mismo?**

Se siente como correr en una cinta que acelera suavemente. Cada mes es un poco más rápido. No puedes parar porque la cinta no para. La hipoteca no para, los costes fijos no paran, las expectativas no paran. Y alguien acaba de ofrecerte una cinta más ancha con una velocidad mayor, y te dice que así llegarás antes. ¿A dónde? No lo sabes, pero detenerte te da más miedo que seguir corriendo.

**¿Y en el lugar de los otros afectados — qué sienten ellos?**

La esposa siente que se casó con un fantasma funcional. Está presente en la hipoteca, ausente en la cena. Los niños sienten una presencia intermitente que normaliza el "papá está trabajando" como estado natural del mundo. El asociado probablemente siente la presión de demostrar que merece estar ahí, porque el dueño se mata trabajando y la vara está alta.

**¿Hay alguien cuyo dolor nadie ve?**

Los hijos. Los niños de 4 y 6 años no saben que tienen dolor — no pueden comparar con una alternativa. Su dolor es invisible precisamente porque es silencioso. No lloran, no se quejan — simplemente crecen con una plantilla de "así funciona una familia" que incluye un padre ausente.

**¿Hay alguien cuyo dolor todos ven pero nadie nombra?**

La esposa. Todos saben que está sola en la crianza. Nadie le pregunta cómo está. La frase "los niños preguntan por ti" es un grito que suena como comentario doméstico.

---

### LENTE L2 — Patrones

**¿Esta persona repite un patrón conocido — de su familia, de su historia?**

Sí, y es textualmente explícito. Padre: negocio propio → 70h/semana → infarto a los 52. Hijo: negocio propio → 60h/semana a los 38 → planea subir carga. El patrón no solo se repite: se está intensificando a edad más temprana.

**¿Lo sabe o es invisible para ella?**

Lo sabe intelectualmente — el dato del infarto está presente en su narrativa. Pero no lo siente como propio. Es información biográfica, no alarma existencial. La disociación es completa: "sé que le pasó a mi padre, pero yo tengo un plan diferente." El plan diferente es idéntico con más sillones.

**¿El patrón le sirvió alguna vez — cuándo dejó de servir?**

El patrón le sirvió para construir la clínica. La ética del sacrificio total es eficaz para iniciar negocios — necesitas invertir tiempo, energía, salud. El patrón dejó de servir cuando la clínica se estabilizó (factura 45K, margen 7K) y él no pudo cambiar de modo. Sigue en modo fundación cuando debería estar en modo sostenimiento.

**¿Qué mantiene el patrón activo — miedo, identidad, hábito?**

Identidad. "Soy el que trabaja duro" es la narrativa central. Si para, no sabe quién es. El miedo es secundario — la identidad es primaria. También hay un componente de lealtad invisible al padre: dejar de sacrificarse sería traicionar el modelo paterno, declarar que el viejo se equivocó. Y eso es un tabú emocional.

---

### LENTE L3 — Regulación

**¿Cómo gestiona esta persona la tensión — evita, ataca, se congela, racionaliza?**

Racionaliza compulsivamente. Traduce toda emoción a número: "si abro sábados y contrato otro dentista, puedo subir a 65.000€/mes." Esa frase no es un plan — es una defensa. La planificación operativa es su mecanismo de evitación. Mientras calcula, no siente. Mientras optimiza, no duele.

**¿Esa estrategia funciona aquí o empeora las cosas?**

Empeora las cosas. La racionalización lo aleja del problema real (desconexión familiar, patrón autodestructivo, agotamiento) y lo acerca a más carga. Es una espiral: siente presión → racionaliza con planes de expansión → la expansión genera más presión → racionaliza de nuevo.

**¿Hay una emoción debajo de la emoción — ira que cubre miedo, control que cubre ansiedad?**

El control cubre terror. Terror a la vulnerabilidad financiera ("si no crezco, la competencia me come"), terror a la vulnerabilidad física ("si paro, me enfrento a lo que evito"), terror a la vulnerabilidad relacional ("si miro a mi esposa a los ojos, veré lo que he hecho"). La hiperactividad laboral es anestesia multifunción.

**¿Qué necesitaría para regularse de forma más efectiva?**

Un espacio donde el paro no signifique fracaso. Terapia individual sería lo más directo. Un grupo de pares (otros propietarios de clínica) donde escuche que otros pararon y no se desmoronaron. Y una conversación honesta con su esposa — no sobre sillones, sino sobre quién quieren ser a los 50.

---

### LENTE L4 — Vínculos

**¿Los vínculos importantes están nutridos o descuidados?**

Todos descuidados. El vínculo con la esposa está en mantenimiento mínimo — funcional para la logística, muerto para la intimidad. El vínculo con los hijos está mediado por la ausencia. El vínculo consigo mismo está anulado — ni siquiera se permite vacaciones. El único vínculo "activo" es con el negocio, y es parasitario.

**¿Hay dependencia — alguien necesita a otro más de lo que el otro puede dar?**

La esposa necesita un compañero presente y él no puede darlo. Los hijos necesitan un padre disponible y él no puede darlo. Él necesita validación de que su sacrificio vale la pena, y nadie se la da — porque no vale la pena. Es una dependencia circular donde todos necesitan algo que ninguno puede dar mientras el sistema funcione así.

**¿Hay distancia — alguien se ha alejado y nadie lo ha nombrado?**

Él se ha alejado de su familia sin irse de casa. La distancia es emocional, no física. Duerme en la misma cama pero vive en otra dimensión — la de las cifras, los sillones, los márgenes. Nadie ha nombrado que la distancia es permanente, no temporal.

**¿El vínculo más importante para la decisión es el que menos atención recibe?**

Sí. El vínculo consigo mismo. No se pregunta "¿qué quiero yo?" Se pregunta "¿qué debería hacer el negocio?" El negocio le ha devorado la identidad hasta el punto de que no hay un "yo" separado del "yo-clínica."

---

### INTEGRAR (∫)

La empatía revela a un hombre atrapado en una identidad de sacrificio. Los patrones confirman que esa identidad es heredada y transgeneracional. La regulación muestra que la racionalización operativa es el mecanismo que mantiene el sistema cerrado. Los vínculos muestran que todo lo que importa se está deteriorando mientras él mira los números.

Las cuatro lentes apuntan al mismo sitio: **el problema no es la decisión de expandir o no — el problema es que no tiene una identidad fuera del trabajo.** La expansión es un síntoma, no una causa. Si se expandiese, seguiría vacío. Si no se expande pero no cambia nada más, seguiría roto. La decisión real es: ¿estoy dispuesto a ser alguien distinto a mi padre?

---

### ABSTRAER

Esta dinámica es universal en propietarios de negocios con primera generación emprendedora. El patrón de "sacrificio fundacional que no sabe apagarse" es epidémico en pymes familiares. Los que resolvieron bien hicieron un movimiento emocional específico: separaron identidad de función. Dejaron de ser "el dueño de la clínica" y empezaron a ser "alguien que tiene una clínica." Los que no resolvieron quedaron atrapados en la inercia del sacrificio hasta que la salud, el matrimonio o ambos colapsaron.

---

### FRONTERA

Entender las emociones no resuelve el problema operativo — el tercer sillón seguirá vacío el 40% del tiempo independientemente de lo que sienta. Pero sin entender las emociones, cualquier decisión operativa será una racionalización más. Hay una decisión que no se puede tomar desde la empatía: si los números no cierran sin expandir, la empatía no paga la hipoteca. El riesgo de esta lente es que comprenda tanto que no actúe — que el insight emocional sustituya a la decisión y se convierta en otra forma de parálisis.

---

### RESUMEN (máx 200 palabras)

El odontólogo está replicando el patrón transgeneracional de su padre: sacrificio total por el negocio hasta el colapso físico. A los 38 años trabaja 60h/semana, planea aumentar carga, y no ha tenido vacaciones en 2 años. Su identidad está fusionada con el rol de proveedor-sacrificado, y la expansión propuesta no es estrategia empresarial sino mecanismo de evitación emocional: mientras planifica sillones, no siente el deterioro de su matrimonio, la ausencia en la crianza ni el miedo a repetir el infarto paterno.

La esposa comunica su soledad a través de los hijos ("los niños preguntan por ti"). Los hijos internalizan la ausencia como normalidad. Él regula toda tensión mediante racionalización operativa — traduce emociones a cifras.

Las cuatro lentes convergen: el problema no es la decisión de expandir, sino la incapacidad de existir fuera del trabajo. La pregunta real no es "¿más sillones?" sino "¿estoy dispuesto a ser alguien diferente a mi padre?" Sin intervenir en la identidad, cualquier decisión operativa será una variación del mismo patrón autodestructivo. El punto ciego de esta lectura: la empatía no paga la hipoteca.

---
---

## CASO 2: STARTUP SAAS

### EXTRAER — Mapear emociones e intenciones

**¿Qué siente esta persona — no lo que dice, lo que siente?**

El CTO siente traición, soledad profesional y agotamiento moral. La salida del co-fundador técnico hace 6 meses no fue solo una pérdida operativa — fue un abandono. "Diferencias de visión" es el eufemismo corporativo para "ya no creo en esto/en ti." Perder a un co-fundador es como un divorcio: destruye la narrativa fundacional. El CTO ahora carga solo con la parte técnica, con un equipo de juniors que no pueden compensar la ausencia, y con un CEO con quien ya no tiene relación fuera de reuniones formales.

Lo que siente debajo del agotamiento es duelo no procesado — duelo por la startup que iba a ser, por la relación con el co-fundador que se fue, por la versión de sí mismo que entró ilusionado y ahora sobrevive con 47 bugs y 7 meses de runway.

**¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?**

Repite la lógica de calidad: "Si el producto fuera sólido, el churn bajaría solo." Es un mantra de control — si puedo arreglar el código, puedo arreglar todo. Evita hablar de la relación con el CEO: no dice "nos llevamos mal" ni "ya no confiamos el uno en el otro" — dice que "apenas se hablan fuera de reuniones formales." La distancia emocional se enmascara como distancia operativa.

**¿Qué necesita realmente — no lo que pide, lo que necesita?**

Necesita sentirse escuchado por el CEO. No necesita ganar el argumento estabilizar-vs-pivotar — necesita que alguien le diga "tu trabajo importa, lo que has construido tiene valor, y no vamos a destruirlo por perseguir una fantasía enterprise." Necesita recuperar la sensación de que él y el CEO están en el mismo barco, no en barcos diferentes que comparten una cuenta bancaria.

**¿Quién más está afectado y cómo se sienten?**

El CEO siente pánico existencial. Su frase "si no crecemos, morimos" es una expresión literal de terror. No es estrategia — es supervivencia disfrazada de ambición. Los 3 desarrolladores junior sienten inseguridad: 2 devs se fueron en 12 meses, el CTO trabaja 70h/semana, y la empresa tiene 7 meses de vida. Los 3 clientes grandes que piden features custom sienten poder — saben que la startup depende de ellos y lo usan para moldear el producto. Los 80 clientes que se van a ritmo de 8%/mes sienten frustración — pagaron por algo que no funciona bien.

**¿Hay emociones que nadie nombra pero que gobiernan las decisiones?**

La vergüenza. Ambos — CTO y CEO — sienten vergüenza de que la startup no esté donde debería. Tres fondos les dijeron "métricas insuficientes," que traducido emocionalmente es "no sois lo bastante buenos." Esa vergüenza se convierte en pelea interna: el CEO canaliza la vergüenza hacia afuera ("necesitamos un mercado más grande") y el CTO la canaliza hacia adentro ("necesitamos un producto mejor"). Misma emoción, distinta defensa.

---

### CRUZAR — Emociones × relaciones

**¿Lo que siente esta persona coincide con lo que muestra?**

No. El CTO muestra un argumento técnico racional: "47 bugs, el churn es por calidad." Lo que siente es: "Si destruimos lo que construí para pivotar a enterprise, todo mi sacrificio fue para nada." La pelea no es técnica — es existencial. El CEO también desacopla: muestra urgencia estratégica ("crecer o morir") y siente pánico por haberse quedado sin co-fundador técnico, sin Serie A, y sin la historia que le contaba a los inversores.

**¿Los demás perciben lo que realmente pasa o solo la superficie?**

Los juniors perciben tensión y abandono. Ven que el CTO no duerme, que el CEO habla de pivotar, que la gente se va. Perciben peligro, no la causa. Los inversores que dijeron no percibieron algo que CTO y CEO no quieren ver: que la empresa tiene un problema de equipo, no solo de métricas. Los clientes perciben inestabilidad del producto y votan con los pies.

**¿Hay patrones — esta situación se repite, se parece a otras anteriores?**

El patrón CTO-CEO divergente es un clásico de startups post-fundación. Lo que lo hace específico aquí es la partida del tercer co-fundador: el que se fue probablemente era el puente emocional entre los dos. Su salida dejó al CTO y al CEO sin mediador, y sin él la relación se volvió transaccional. El patrón más profundo es el del "constructor vs. vendedor": el CTO construye y el CEO vende, y cuando las ventas no van bien, el vendedor quiere cambiar el producto y el constructor se ofende.

**¿Qué trigger activó la crisis actual?**

La combinación de la tercera negativa de inversores + el runway de 7 meses. Antes de eso, la tensión era crónica pero tolerable. El runway pone fecha al conflicto: si en 7 meses no hay mejora, se acabó. Esa fecha límite convierte el desacuerdo estratégico en una pelea por la supervivencia.

**¿Lo que pide es lo que necesita, o pide una cosa para obtener otra?**

El CTO pide tiempo para estabilizar el producto. Lo que necesita es recuperar la relación con el CEO y tener voz en la dirección de la empresa. Pide bugs porque los bugs puede controlarlos — la relación con el CEO no.

---

### LENTE L1 — Empatía

**¿Puedes ponerte en su lugar — qué se siente ser esta persona ahora mismo?**

Se siente como pilotar un avión con un motor ardiendo mientras el copiloto quiere cambiar de destino. Sabes que si no apagas el fuego, no llegas a ningún lado. Pero el copiloto grita que el destino actual es un callejón sin salida. Y tú no puedes apagar el fuego Y discutir el rumbo al mismo tiempo. Mientras tanto, la tripulación empieza a saltar del avión.

**¿Y en el lugar de los otros afectados — qué sienten ellos?**

El CEO se siente incomprendido. Desde su lente, está siendo pragmático: los restaurantes no pagan suficiente, el enterprise sí, el tiempo se acaba. Siente que el CTO está aferrado al producto como un artista a su obra, y no ve que el mercado no valida esa obra. Los juniors sienten que trabajan en una empresa en caída libre y que nadie les dice la verdad.

**¿Hay alguien cuyo dolor nadie ve?**

El co-fundador que se fue. Se fue "por diferencias de visión," pero probablemente se fue porque vio que la relación CTO-CEO era irreparable y que la empresa iba a consumirle sin recompensa. Su partida es tratada como causa del problema cuando probablemente fue síntoma del mismo.

**¿Hay alguien cuyo dolor todos ven pero nadie nombra?**

Los juniors. Todo el mundo sabe que están sobrecargados, que trabajan para un CTO que trabaja 70h/semana estableciendo un estándar imposible, y que la empresa puede cerrar en meses. Nadie les habla de esto abiertamente.

---

### LENTE L2 — Patrones

**¿Esta persona repite un patrón conocido — de su familia, de su historia?**

No hay datos biográficos suficientes, pero el patrón startup es claro: el CTO que se inmola técnicamente mientras el CEO persigue la visión comercial. El CTO repite el patrón del "constructor que salva la obra con horas infinitas" — patrón que probablemente le funcionó antes (en la universidad, en empleos anteriores) y que aquí no funciona porque el problema no es técnico.

**¿Lo sabe o es invisible para ella?**

Probablemente invisible. El CTO cree genuinamente que arreglar los 47 bugs resolverá el churn. No ve que el churn es multifactorial y que la desconexión con el CEO es tan destructiva como los bugs.

**¿El patrón le sirvió alguna vez — cuándo dejó de servir?**

El patrón de "arreglar lo técnico resuelve todo" le sirvió para construir el MVP y conseguir los primeros 80 clientes. Dejó de servir cuando la empresa necesitó no solo un buen producto sino también un buen mercado, una buena relación fundadora, y una historia coherente para inversores.

**¿Qué mantiene el patrón activo — miedo, identidad, hábito?**

Identidad + miedo. "Soy el técnico que construye bien" es su identidad. Si el producto no importa (porque hay que pivotar), él no importa. El miedo es: "si pivotan sin mí, quedo descartado." El hábito es: las 70h/semana le dan la ilusión de que controla algo.

---

### LENTE L3 — Regulación

**¿Cómo gestiona esta persona la tensión — evita, ataca, se congela, racionaliza?**

Evita el conflicto relacional y ataca el problema técnico. Es una evitación selectiva: se zambulle en bugs para no zambullirse en la conversación que necesita tener con el CEO. Las 70h/semana son a la vez trabajo y huida.

**¿Esa estrategia funciona aquí o empeora las cosas?**

Empeora dramáticamente. Mientras el CTO arregla bugs y el CEO planifica el pivot, la distancia entre ambos crece. La empresa necesita una decisión conjunta, y la regulación individual de cada uno (CTO=hundir la cabeza en código; CEO=hundir la cabeza en pitch decks) impide esa decisión.

**¿Hay una emoción debajo de la emoción — ira que cubre miedo, control que cubre ansiedad?**

La certeza técnica del CTO ("si el producto fuera sólido, el churn bajaría solo") cubre el miedo a ser irrelevante. Si la solución no es técnica, ¿qué hace él aquí? La insistencia del CEO en pivotar cubre el miedo a admitir que eligieron mal el mercado desde el principio.

**¿Qué necesitaría para regularse de forma más efectiva?**

Una conversación honesta y estructurada entre CTO y CEO — no sobre estrategia, sino sobre cómo se sienten, qué temen, y si quieren seguir juntos. Un mediador externo (advisor, coach de co-founders) que haga visible lo que ambos evitan.

---

### LENTE L4 — Vínculos

**¿Los vínculos importantes están nutridos o descuidados?**

El vínculo CTO-CEO es el más importante y el más abandonado. "Apenas se hablan fuera de reuniones formales" es una sentencia de muerte relacional. Un equipo fundador que no habla informalmente no tiene confianza. Sin confianza, toda discusión estratégica es una pelea de poder.

**¿Hay dependencia — alguien necesita a otro más de lo que el otro puede dar?**

Los 3 clientes grandes tienen poder desproporcionado: 30% de ingresos. La startup depende de ellos más de lo sano. Los juniors dependen del CTO para dirección técnica, y él no puede darla porque está apagando fuegos. La empresa depende de una relación fundadora que no funciona.

**¿Hay distancia — alguien se ha alejado y nadie lo ha nombrado?**

El co-fundador que se fue creó un vacío que nadie ha llenado. Pero la distancia más destructiva es la del CTO y el CEO: están en la misma empresa pero en universos paralelos. Nadie ha dicho "nuestra relación está rota y eso está matando la empresa."

**¿El vínculo más importante para la decisión es el que menos atención recibe?**

Exactamente. La decisión pivotar/estabilizar es secundaria. La decisión primaria es: ¿CTO y CEO pueden reconstruir confianza suficiente para ejecutar cualquier estrategia juntos? Si no, da igual qué estrategia elijan — fracasará por falta de cohesión.

---

### INTEGRAR (∫)

La empatía revela dos personas sufriendo en paralelo sin conectar. Los patrones muestran que cada uno repite su defensa habitual (CTO→código, CEO→visión). La regulación de ambos es divergente y centrífuga — los separa en vez de acercarlos. Los vínculos están en mínimos históricos.

Las cuatro lentes convergen en un solo punto: **el problema no es producto vs. mercado — es que la relación fundadora está rota y nadie la está reparando.** Sin esa reparación, estabilizar fracasará (porque el CEO saboteará por impaciencia) y pivotar fracasará (porque el CTO saboteará por resentimiento). La emoción central: duelo no procesado por la startup que iba a ser.

---

### ABSTRAER

Esta dinámica es universal en co-fundadores post-crisis. La mayoría de startups que mueren no mueren por el producto o el mercado — mueren por la relación fundadora. Los que resolvieron bien hicieron un movimiento emocional: se sentaron, admitieron que tenían miedo, y decidieron si querían seguir juntos antes de decidir a dónde ir. Los que no resolvieron siguieron debatiendo estrategia mientras la relación se desangraba.

---

### FRONTERA

¿Estoy psicologizando un problema que es estructural? Parcialmente sí. El churn de 8% es real, los 47 bugs son reales, y el runway de 7 meses es un hecho. Pero la pregunta es: ¿puede una empresa con relación fundadora rota ejecutar cualquier plan? La respuesta empírica es: no. La lente emocional puede convertirse en trampa si se usa para evitar la decisión dura: a lo mejor la empresa simplemente no es viable y la mejor decisión emocional es cerrar con dignidad.

---

### RESUMEN (máx 200 palabras)

La startup tiene un problema que parece técnico-estratégico (pivotar vs. estabilizar) pero es fundamentalmente relacional: la relación CTO-CEO está rota. "Apenas se hablan fuera de reuniones formales" es una sentencia de muerte para cualquier co-fundación. La partida del tercer co-fundador eliminó el puente emocional entre ambos y dejó al descubierto una incompatibilidad que estaba latente.

El CTO canaliza su ansiedad hacia el código (47 bugs, calidad) porque es el único terreno que controla. El CEO canaliza su pánico hacia el mercado (enterprise) porque es el único escape que imagina. Ambos sienten vergüenza por el rechazo de los inversores, pero la procesan de forma opuesta: uno hacia adentro (mejorar el producto), otro hacia afuera (cambiar el mercado). Misma emoción, defensas divergentes.

Los juniors están atrapados en un fuego cruzado que nadie nombra. Los 3 clientes grandes tienen poder desproporcionado. El duelo por la startup que iba a ser no está procesado por ninguno de los dos.

La decisión real no es pivotar o estabilizar — es si CTO y CEO pueden reconstruir confianza. Sin eso, cualquier estrategia fracasará. Punto ciego: la relación puede ser irreparable y la empresa inviable.

---
---

## CASO 3: CAMBIO DE CARRERA

### EXTRAER — Mapear emociones e intenciones

**¿Qué siente esta persona — no lo que dice, lo que siente?**

Siente un duelo anticipado doble: duelo por la vida que tiene si se va (estabilidad, estatus, seguridad) y duelo por la vida que no ha vivido si se queda (propósito, pasión, autenticidad). Es un duelo sin muerte — todo está vivo pero nada se siente vivo. El insomnio de 2 años es la manifestación somática de una decisión no tomada: el cuerpo ya decidió que algo está mal, la mente no se atreve a actuar.

Lo que siente debajo de la indecisión es ira contenida. Rechazada para socia después de 20 años. "Quizá el próximo ciclo" es la frase más cruel del mundo corporativo — suficiente esperanza para no irte, insuficiente compromiso para quedarte. La ira no está nombrada en ningún lado; está cubierta por la narrativa de "pérdida de pasión," que es más socialmente aceptable que "me siento traicionada por un sistema al que di 20 años."

**¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?**

Repite la tensión entre dos polos: "si no lo hago ahora, no lo haré nunca" vs. "no puedo arriesgar la estabilidad de mis hijos." Esa oscilación es el ritmo de alguien que no se permite elegir. Evita nombrar la rabia por el rechazo a socia — lo menciona como dato biográfico, no como herida. Evita también la conversación con su marido, lo cual es enormemente revelador: si estuviera segura de cualquiera de las dos opciones, ya habría hablado.

**¿Qué necesita realmente — no lo que pide, lo que necesita?**

Necesita saber que su valor no depende de que un bufete la haga socia. Necesita separar su identidad profesional de su identidad como persona. Y necesita tener la conversación con su marido — no para pedirle permiso, sino para saber si están juntos en esto o si el cambio la dejaría sola emocionalmente además de financieramente.

**¿Quién más está afectado y cómo se sienten?**

El marido probablemente siente una mezcla de preocupación y distancia. Ella no le ha hablado "en profundidad" — lo que implica que él sabe algo, percibe algo, pero no tiene la imagen completa. Con ingresos irregulares de 40-80K€, probablemente se siente vulnerable ante un cambio que reduciría los ingresos familiares drásticamente. Los hijos (14 y 16 años) están en una edad donde perciben todo pero procesan poco — captan la tensión pero no la entienden. Los padres sienten miedo ("estás loca") que es una proyección de sus propios valores generacionales: seguridad > propósito.

**¿Hay emociones que nadie nombra pero que gobiernan las decisiones?**

La humillación. Veinte años en un bufete prestigioso y no la hacen socia. Eso no es solo decepción profesional — es un veredicto sobre su valor. La decisión de irse no es solo búsqueda de propósito: es también huida de la humillación. "Me voy porque quiero" es más tolerable que "me voy porque no me quisieron." Esa emoción no está nombrada y probablemente es la que más energía tiene.

---

### CRUZAR — Emociones × relaciones

**¿Lo que siente esta persona coincide con lo que muestra?**

Muestra reflexión madura: "he perdido la pasión," comparación con amiga que cambió, análisis de ahorros. Lo que siente es herida narcisista por el rechazo a socia, ira contenida, y un deseo furioso de demostrar que vale más de lo que el bufete le reconoce. La capa racional protege la capa emocional.

**¿Los demás perciben lo que realmente pasa o solo la superficie?**

Los padres perciben riesgo pero no la herida. El marido probablemente intuye algo profundo pero no tiene acceso porque ella no ha abierto la conversación. La amiga que hizo el cambio probablemente es la persona que más cerca está de percibir la verdad, pero también funciona como espejo idealizante — "ella lo hizo y le fue bien" puede ser una fantasía tanto como un modelo.

**¿Hay patrones — esta situación se repite, se parece a otras anteriores?**

El patrón probable: persona de alto rendimiento que sacrificó deseo personal por deber externo durante décadas. Es el patrón del "buen hijo/a" que se convierte en "buen empleado/a" — siempre cumpliendo expectativas ajenas, hasta que un rechazo (no ser socia) rompe el contrato implícito: "si cumplo, me premiarán." Cuando el premio no llega, el contrato se invalida y toda la estructura se tambalea.

**¿Qué trigger activó la crisis actual?**

El rechazo a socia. Tres años pensando en cambiar, pero el rechazo cristalizó la decisión. Antes del rechazo, cambiar era fantasía. Después del rechazo, cambiar es venganza revestida de propósito. El segundo trigger es la edad: 45 años es percibido como última ventana.

**¿Lo que pide es lo que necesita, o pide una cosa para obtener otra?**

Pide claridad sobre si dejar el bufete. Lo que necesita es procesar el rechazo a socia, la ira que contiene, y hablar con su marido. La decisión laboral viene después del trabajo emocional, no antes.

---

### LENTE L1 — Empatía

**¿Puedes ponerte en su lugar — qué se siente ser esta persona ahora mismo?**

Se siente como estar en una habitación con dos puertas. Una dice "seguridad" y huele a hospital — limpio pero sin vida. La otra dice "propósito" y huele a aire libre — vital pero con viento. No puedes ver qué hay detrás de ninguna. Llevas 2 años mirando las dos puertas sin atreverte a abrir ninguna. Y el insomnio es el cuerpo diciendo: "decide o decidiré yo."

**¿Y en el lugar de los otros afectados — qué sienten ellos?**

El marido siente que le van a pasar una factura que no ha firmado. Si ella decide irse, él carga con la presión financiera sin haber sido consultado a fondo. Los hijos de 14 y 16 sienten la tensión en casa — perciben el insomnio de mamá, las discusiones con los abuelos, la vaguedad del futuro. Los padres sienten terror generacional: "construimos estabilidad para que tú la tiraras."

**¿Hay alguien cuyo dolor nadie ve?**

El marido. Tiene ingresos irregulares, no ha sido incluido en la deliberación profunda, y si ella cambia de carrera, él pasa de contribuir a ser insuficiente. Su identidad económica está en juego y nadie le pregunta cómo se siente al respecto.

**¿Hay alguien cuyo dolor todos ven pero nadie nombra?**

Ella misma. El insomnio de 2 años es visible para todos — marido, médico, probablemente compañeros de trabajo. Todos ven que sufre. Nadie nombra que el sufrimiento no es por estrés laboral genérico sino por una crisis de identidad profunda que el bufete activó al rechazarla.

---

### LENTE L2 — Patrones

**¿Esta persona repite un patrón conocido — de su familia, de su historia?**

El patrón es clásico: cumplir expectativas externas a costa del deseo propio. Los padres dicen "estás loca" — lo que revela que ella probablemente siempre fue "la sensata," "la responsable," "la que no nos preocupa." Ese rol se internalizó como identidad y ahora que quiere salir de él, la familia completa reacciona como si traicionara un contrato.

**¿Lo sabe o es invisible para ella?**

Lo intuye — la frase "si no lo hago ahora, no lo haré nunca" sugiere consciencia de que hay un patrón de postergación del deseo propio. Pero probablemente no ve la conexión entre el rechazo a socia y la activación del deseo de cambio. Cree que quiere irse porque encontró su vocación; la realidad es que quiere irse porque el rechazo rompió la ilusión de que el sacrificio sería recompensado.

**¿El patrón le sirvió alguna vez — cuándo dejó de servir?**

Le sirvió 20 años: carrera estable, 180K€/año, hipoteca pagándose, estatus social. Dejó de servir cuando el sistema dejó de cumplir su parte del trato — el ascenso a socia.

**¿Qué mantiene el patrón activo — miedo, identidad, hábito?**

Miedo al caos financiero + identidad de "la responsable" + hábito de priorizar a otros (hijos, marido, padres) sobre sí misma. Los 120.000€ ahorrados son simultáneamente su colchón de seguridad y su ticket de salida — y esa doble función es parte de la parálisis.

---

### LENTE L3 — Regulación

**¿Cómo gestiona esta persona la tensión — evita, ataca, se congela, racionaliza?**

Se congela. Dos años de insomnio, tres años pensando en cambiar — y la conversación con el marido no ha ocurrido. Es una congelación activa: piensa intensamente sin moverse. Racionaliza en ambas direcciones ("los ahorros dan para X meses" / "los hijos empiezan universidad") lo cual neutraliza toda acción. Cada argumento a favor tiene un contra, y ella los mantiene en equilibrio perfecto.

**¿Esa estrategia funciona aquí o empeora las cosas?**

Empeora. Cada mes que pasa sin decidir, el insomnio se cronifica, la frustración crece, la energía baja, y la capacidad de tomar decisiones se deteriora. La parálisis no preserva el status quo — lo degrada.

**¿Hay una emoción debajo de la emoción — ira que cubre miedo, control que cubre ansiedad?**

La "pérdida de pasión" cubre ira. La "preocupación por los hijos" cubre miedo a estar sola en su decisión. La comparación con la amiga cubre envidia sana — deseo de algo que otro tiene y ella no se permite. Debajo de todo: terror a descubrir que su propia vida fue una concesión tras otra y que ya no hay tiempo de recuperar lo perdido.

**¿Qué necesitaría para regularse de forma más efectiva?**

Primero: procesar el rechazo a socia como lo que es — una herida, no un dato. Segundo: hablar con el marido — la conversación no tomada es el mayor regulador bloqueado. Tercero: separar la decisión en fases — no tiene que elegir todo ahora. Puede hacer una transición gradual en vez de un salto binario.

---

### LENTE L4 — Vínculos

**¿Los vínculos importantes están nutridos o descuidados?**

El vínculo con el marido está descuidado peligrosamente — "no ha hablado en profundidad" sobre la decisión más importante de la próxima década. El vínculo con los padres es funcional pero invalidante ("estás loca"). El vínculo con la amiga es nutriente pero potencialmente idealizante. El vínculo consigo misma lleva 2 años de insomnio — no está nutrido, está en crisis.

**¿Hay dependencia — alguien necesita a otro más de lo que el otro puede dar?**

Ella necesita del marido una seguridad que él no puede dar porque sus ingresos son irregulares. Los hijos necesitan estabilidad que ambos padres están luchando por sostener. Ella necesita de sí misma una claridad que su estado emocional actual no permite generar.

**¿Hay distancia — alguien se ha alejado y nadie lo ha nombrado?**

Ella se ha alejado emocionalmente del bufete hace 3 años sin que sea oficial. Vive una doble vida: profesionalmente presente, emocionalmente ida. Esa distancia interna nadie la nombra — sus compañeros probablemente ven a una abogada competente que no saben que fantasea con irse cada día.

**¿El vínculo más importante para la decisión es el que menos atención recibe?**

El vínculo con el marido. Es el vínculo que determina si la transición es viable emocionalmente y financieramente — y es el único vínculo donde no ha tenido la conversación. Si él la apoya, todo cambia. Si él se resiste, todo se complica exponencialmente.

---

### INTEGRAR (∫)

Empatía: una mujer congelada entre dos vidas posibles, con el cuerpo en rebelión. Patrones: cumplir expectativas ajenas hasta que el premio no llega, momento de ruptura. Regulación: parálisis analítica con racionalización bidireccional. Vínculos: el vínculo que más importa (marido) es el que menos atención recibe.

Las cuatro lentes apuntan a un problema diferente del declarado: **la pregunta no es "¿me voy del bufete?" sino "¿puedo permitirme ser yo misma, y mi sistema de vínculos me sostendrá si lo hago?"** La decisión laboral es la capa visible de una crisis de identidad y de permiso. El rechazo a socia fue el detonante, no la causa. La causa lleva 20 años acumulándose.

---

### ABSTRAER

Esta dinámica es universal en profesionales de alto rendimiento a mitad de carrera. El "midlife reckoning" — la reconsideración de mitad de vida — afecta especialmente a quienes construyeron carreras por deber más que por deseo. Los que resolvieron bien hicieron un movimiento emocional: hablaron con su pareja antes de decidir, procesaron la herida institucional como herida y no como dato, y buscaron transiciones graduales en vez de rupturas binarias. Los que no resolvieron se quedaron paralizados hasta que la decisión fue tomada por las circunstancias (burnout, divorcio, crisis de salud).

---

### FRONTERA

¿Estoy psicologizando un problema que es financiero? Parcialmente. La diferencia entre 180K€ y 55K€ es brutal — no es una emoción, es una hipoteca y dos universidades. Pero la pregunta es: ¿puede alguien con insomnio crónico y una crisis de identidad mantener un rendimiento de 180K€ durante 15 años más? Probablemente no. El deterioro ya está ocurriendo. La lente emocional no resuelve los números, pero revela que los números actuales tienen fecha de caducidad.

---

### RESUMEN (máx 200 palabras)

La abogada vive una crisis de identidad catalizada por el rechazo a socia. "Pérdida de pasión" enmascara ira y humillación: 20 años de sacrificio sin la recompensa prometida rompieron el contrato implícito de "si cumplo, me ascenderán." El insomnio de 2 años es el cuerpo tomando la decisión que la mente no se atreve a tomar.

El patrón es clásico: la "buena hija" convertida en "buena empleada" que siempre priorizó deber sobre deseo. Los padres confirman este rol ("estás loca" = "no dejes de ser quien nos tranquiliza"). La parálisis se mantiene por racionalización bidireccional perfecta donde cada argumento tiene un contra exacto.

El vínculo más crítico — el marido — es el que menos atención recibe. Sin esa conversación, no hay datos para decidir. La amiga funciona como espejo idealizante, no como evidencia.

Las cuatro lentes convergen: la pregunta no es "¿me voy?" sino "¿puedo permitirme ser yo misma y mi sistema relacional me sostendrá?" La decisión laboral es superficie de una crisis de identidad y permiso. Punto ciego: la empatía no resuelve que 55K€ no paga la hipoteca + dos universidades.

---
---

## POST-3-CASOS

### LOOP TEST

**Caso elegido:** Caso 1 (Clínica Dental) — donde el análisis alcanzó mayor profundidad emocional.

**Segunda pasada — aplico las mismas preguntas a mi propio output:**

**¿Qué siente mi output — no lo que dice, lo que siente?**
Mi output siente certeza excesiva. Presenta al odontólogo como alguien atrapado de forma casi determinista en un patrón transgeneracional, como si la repetición fuera inevitable. Eso es una proyección: la inteligencia social tiende a ver patrones donde quiere verlos. ¿Realmente sé que su identidad está "fusionada" con el trabajo? No lo sé — lo infiero de datos limitados.

**¿Qué evita mi output?**
Evita la posibilidad de que el odontólogo tenga razón. Quizá la expansión es buena idea. Quizá 65K€/mes le daría margen para contratar un gerente y trabajar menos. Mi output asume que expandir = más carga, pero eso no es necesariamente cierto. Un odontólogo que factura 65K€ con 3 dentistas podría trabajar MENOS que uno que factura 45K€ con 2. Mi lente emocional filtró los datos para confirmar la narrativa de "sacrificio autodestructivo."

**¿Hay patrones en mi propio análisis que se repiten sin que lo note?**
Sí: tiendo a romantizar al que sufre y demonizar al sistema. En los 3 casos, el sujeto es "víctima" de fuerzas que no ve, y la solución siempre incluye "procesar emociones" y "tener una conversación difícil." Ese es mi sesgo: creo que hablar resuelve.

**¿Qué revela la segunda pasada que la primera no vio?**

1. La primera pasada no consideró que el patrón puede ser consciente y aceptado — quizá el odontólogo SABE que es como su padre y ha hecho las paces con ello.
2. No consideré que la esposa puede ser parte del problema, no solo víctima — ¿cuál es su papel en mantener un sistema donde él trabaja 60h?
3. No examiné que "permiso para parar" puede ser condescendiente — él es adulto, no necesita permiso.

**¿Es genuinamente nuevo?**
Sí. La autocrítica sobre la certeza excesiva y el sesgo confirmatorio son genuinamente nuevos. La posibilidad de que la expansión sea racional y no solo anestesia es un punto ciego real de la primera pasada.

---

### PATRÓN CROSS-CASE

En los 3 casos, desde la lente social, aparece el mismo patrón independientemente del dominio:

**La conversación no tenida es el verdadero cuello de botella.**

- Caso 1: No ha hablado con su esposa sobre quién quieren ser a los 50.
- Caso 2: CTO y CEO no hablan fuera de reuniones formales.
- Caso 3: No ha hablado "en profundidad" con su marido sobre el cambio.

En los tres casos, la decisión operativa (expandir/pivotar/cambiar carrera) está bloqueada por una conversación relacional que no ha ocurrido. La lente social ve que el bloqueo no es informacional ni estratégico — es relacional. Las personas evitan la conversación que desbloquearía la decisión porque esa conversación implica vulnerabilidad, y la vulnerabilidad es exactamente lo que están tratando de evitar.

---

### SATURACIÓN

**¿Una tercera pasada aportaría algo nuevo?**

Marginalmente. La segunda pasada reveló el sesgo confirmatorio y la tendencia a romantizar al sujeto. Una tercera pasada probablemente redundaría en meta-análisis del meta-análisis — útil para un artículo académico, inútil para la cartografía. La saturación está alcanzada en lo estructural; lo que aportaría valor no es más profundidad sino **cruzar con otra inteligencia** (financiera, estratégica, constructiva).

---

### FIRMA — En 1-2 frases

**Esta inteligencia ve que las decisiones supuestamente racionales están bloqueadas por conversaciones emocionales que nadie se atreve a tener. El obstáculo no es información ni estrategia — es que la vulnerabilidad relacional necesaria para decidir es exactamente lo que cada sujeto evita.**



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/computacional.md
============================================================

# RESULTADOS FASE 1 — ACUMULADOR NARRATIVO

---

## INT-02: COMPUTACIONAL

### Caso 1: Clínica Dental
**Resumen:** La clínica dental es un problema de optimización de scheduling con capacidad ociosa no explotada: el sillón 3 vacío el 40% del tiempo equivale a ~6.000€/mes potenciales sin invertir un euro. El sujeto salta directamente a la expansión sin resolver la infrautilización existente. Computacionalmente, la transformación tiene 7 pasos secuenciales con dependencias claras, pero el atajo es un cálculo de 10 minutos: cuánto genera llenar el sillón 3. El paralelismo revela que su tiempo personal es un mutex global que toda tarea bloquea — expandir intensifica esta contención. El orden de ejecución importa: optimizar antes de expandir es estrictamente superior al inverso. La aproximación 80/20 basta porque la decisión no necesita decimales, necesita dirección. Las cuatro lentes convergen: el cuello de botella es definición del problema, no datos ni velocidad. La parte computable (finanzas, agenda) es la parte fácil. La parte que decide — repetir o no el patrón del padre, estar con los hijos — no admite algoritmo. El cómputo informa; no resuelve.

**Firma:** El sillón vacío ya pagado es un cómputo trivial que elimina la necesidad de la decisión compleja. Optimizar antes de expandir es estrictamente dominante, y el cálculo que lo demuestra toma 10 minutos.

### Caso 2: Startup SaaS
**Resumen:** La startup es un sistema con dos funciones objetivo contradictorias compitiendo por los mismos 3 juniors, con 7 meses de runway y un bucle negativo activo. El dato discriminante — correlación entre bugs específicos y cancelaciones — no existe y se puede construir en 2 semanas. Sin él, la disputa CTO-CEO es irreconciliable. La ruta enterprise tiene 9 pasos que no caben en el horizonte. El escalamiento es pésimo: cada cliente enterprise multiplica complejidad. El atajo 80/20 es dedicar 2 semanas a medir correlación bug-churn. La concurrencia con 3 juniors tiene cero redundancia. Las lentes convergen: el bottleneck es que nadie genera el dato que resolvería la discusión. Debajo del problema computable hay un problema de gobernanza: dos cofundadores que no hablan no pueden ejecutar ningún algoritmo.

**Firma:** El dato que resolvería la disputa CTO-CEO probablemente ya existe disperso en tickets de soporte. 2 semanas de compilarlo valen más que 7 meses de discutir sin él.

### Caso 3: Cambio de carrera
**Resumen:** El cambio de carrera es un sistema con 3 hilos independientes — hablar con marido, calcular finanzas, explorar opciones — todos de bajo coste y alto retorno informativo, ninguno ejecutándose. El bucle actual lleva 3 años sin condición de salida. El cálculo de servilleta se hace en 10 minutos y transforma 'no puedo arriesgar' en '¿cuánto ajuste acepto?'. El árbol de decisión revela que el primer nodo no es financiero sino relacional: hablar con el marido. Los ahorros de 120K son buffer que convierte la transición en reversible. Las cuatro lentes convergen: el bottleneck es iniciación, no información. Lo computable se resuelve en una tarde; lo incomputable es si quiere.

**Firma:** El sistema tiene 3 hilos baratos que resuelven la incertidumbre en paralelo y ninguno está corriendo. El bottleneck no es información — es que nadie ejecuta las operaciones triviales que la producirían.

### Loop test (P06)
**Caso elegido:** Startup SaaS
**Hallazgos nuevos:**
- Mi recomendación (2 semanas de análisis bug-churn) asume que 3 juniors pueden ejecutar análisis de datos — capacidad no verificada.
- El deadlock CTO-CEO es un problema de consenso distribuido: necesitan protocolo de decisión ANTES del dato, no solo el dato.
- Vacío simétrico: critiqué que la ruta enterprise no cabe en 7 meses pero no calculé qué sí cabe en estabilización.
- Espacio de soluciones incompleto: no modelé opción de muerte controlada (acqui-hire, venta de base de clientes).
**Es genuinamente nuevo:** Sí. La capacidad del equipo para ejecutar la recomendación y el protocolo de consenso previo al dato son capas no tocadas en la primera pasada.

### Patrón cross-case
En los 3 casos existe una operación de bajo coste y alto retorno informativo que no se ejecuta (10 min de cálculo, 2 semanas de correlación, 1 tarde de presupuesto). La complejidad percibida del problema se reduce un orden de magnitud después de esa operación. El bottleneck universal no es información ni cómputo sino iniciación de la operación trivial.

### Saturación (P07)
**Tercera pasada aportaría:** No. El patrón cross-case está estabilizado. El loop test del caso 2 aportó genuinamente, pero una tercera pasada generaría refinamientos menores sin cambiar la estructura del diagnóstico.
**No-idempotente:** Sí (la segunda pasada aportó genuinamente).



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/estructural.md
============================================================

# RESULTADOS FASE 1 — CARTOGRAFÍA META-RED DE INTELIGENCIAS

**Proyecto:** CARTOGRAFÍA META-RED
**Estado:** En ejecución
**Última actualización:** 2026-03-07

---

## F1-03: ESTRUCTURAL (IAS) — INT-03

**Ejecutado:** 2026-03-07

---

### CASO 1: CLÍNICA DENTAL

#### EXTRAER — Coordenadas sintácticas

**C1 — Compresión:**
Una palabra: **atrapado**. Una frase: un hombre replica la trampa de su padre creyendo que la está evitando. Un párrafo: un odontólogo de 38 años trabaja 60h/semana en una clínica que produce 7.000€/mes netos mientras tiene un tercer sillón vacío el 40% del tiempo, y su respuesta a esta rentabilidad insuficiente es ampliar a 5 sillones y abrir sábados — es decir, resolver la infrautilización añadiendo más infraestructura infrautilizable, bajo el mismo cuello de botella (él mismo).

**C2 — Gap id↔ir:**
Dice que hace: "gestionar una clínica dental y valorar una expansión racional." Lo que hace realmente: trabajar 60h semanales como dentista-operario, no como propietario-gestor. El gap es total. Un propietario optimiza; un operario produce. Él produce. Su identidad declarada es "dueño de negocio"; su identidad real es "dentista que además tiene deudas de local." El gap id↔ir está en confundir propiedad con dirección. Tiene título de propiedad pero conducta de empleado sobreexplotado.

**C3 — Conexiones y desconexiones:**
Conectado: sillón → dentista → facturación → cuota hipoteca. Esa cadena funciona. Lo que NO está conectado: el tercer sillón con ningún dentista el 40% del tiempo. La propuesta de expansión con los datos de utilización actuales. La familia con las decisiones de negocio (la esposa emite señal, él no la procesa como input de decisión). El patrón de salud de su padre con su propia trayectoria. Conexión ausente crítica: no hay conexión entre "margen neto" y "horas trabajadas" — no calcula su tarifa horaria real.

**C4 — Poder:**
El banco opera sobre él con poder 0.6: la oferta de crédito crea la ilusión de opcionalidad y enmarca "más sillones" como la solución legítima. La hipoteca opera sobre él con poder 0.8: es un ancla que le impide reducir riesgo. Él opera sobre el asociado con poder 0.7. La esposa opera sobre él con poder 0.3 (emite señal, no tiene veto). Los hijos operan con poder 0.0 (no tienen voz). Su padre muerto opera sobre él con poder inconsciente alto — quizá 0.7 — como modelo y como advertencia simultáneamente.

**C5 — Divergencia declarado↔real:**
Declara: "Si abro sábados y contrato otro dentista, puedo subir a 65.000€/mes." Realidad: tiene un tercer sillón vacío el 40%. Eso son ~1.000h/año de capacidad desperdiciada. Si llenara ese sillón, con la misma ratio de facturación (45.000€ con ~60% de uso de 3 sillones ≈ 1.8 sillones equivalentes a plena carga → ~25.000€/sillón-equivalente), un sillón completo más añadiría ~25.000€/mes brutos → unos 50.000-55.000€/mes sin un solo euro de inversión nueva. La divergencia entre "necesito 5 sillones" y "no lleno 3" es del 40%.

#### CRUZAR — Huecos activos

**H1 — Nombre vs medida:**
Lo que se nombra: "crecimiento", "facturación", "expansión." Lo que se mide: nada relevante. No mide utilización de sillón. No mide coste por hora propia. No mide ratio de conversión paciente/sillón. No mide el coste de oportunidad de su tiempo. No mide el impacto familiar. El nombre y la medida divergen en todo.

**H2 — Potencia sin nombre:**
El miedo opera a potencia máxima porque no se nombra. Miedo a parar (= ser como su padre si para, o ser como su padre si no para — el dilema es indecidible desde dentro). Miedo a que la hipoteca se coma el margen si baja el ritmo. El patrón heredado del padre es la fuerza gravitatoria más potente del sistema y no aparece en ningún cálculo.

**H3 — Desconexión funcional:**
La desconexión entre familia y negocio no es accidental. Sostiene el sistema. Si conectara "los niños preguntan por ti" con "trabajo 60h/semana", tendría que tomar una decisión que amenaza su identidad de proveedor-sacrificado. La desconexión entre utilización actual y plan de expansión también es funcional: si la viera, no podría justificar la expansión.

#### LENTE T1 — Conjuntos

**Contención:** El conjunto "clínica" contiene: sillones, dentistas, pacientes, deuda. El conjunto "familia" contiene: esposa, hijos, tiempo compartido. El conjunto "decisión" debería contener elementos de ambos. No los contiene — es un conjunto vacío que debería existir.

**Solape:** "Él" está en la intersección de clínica ∩ familia, pero funciona como si solo existiera en "clínica."

**Conjuntos que faltan:** No existe el conjunto "salud". No existe el conjunto "gobernanza del negocio" (vs operación). No existe el conjunto "plan de salida" ni "escenarios de contingencia."

**Fuera de todos los conjuntos:** La pregunta "¿y si no expando sino que optimizo lo que tengo?" También "¿y si vendo?" o "¿y si contrato un gestor?"

#### LENTE T2 — Causal

**Circuitos:** Circuito 1 (refuerzo negativo): más horas → más facturación → justificación de más horas → más horas. Circuito 2 (refuerzo negativo): deuda → necesidad de ingresos → más trabajo → no tiempo para optimizar → misma deuda relativa. Circuito 3 (potencial pero apagado): optimizar tercer sillón → más ingresos sin más horas propias → margen para descanso.

**Equilibrio:** No. Degradación lenta. El cuerpo acumula 2.500h/año. La familia acumula distancia.

**Convergencia sin intervención:** Crisis de salud (14 años de margen si replica patrón paterno), crisis matrimonial, o ambas.

#### LENTE T3 — Juegos

**Jugadores:** Odontólogo (poder 0.5), esposa (0.3), banco (0.6), asociado (0.2), padre muerto (0.7).

**Si nadie cambia:** Gana el banco. Pierde el odontólogo (salud), la esposa (relación), los hijos (presencia paterna).

**Falta en el tablero:** Un asesor de negocio. Un mentor. Un médico que conecte pronóstico con datos.

#### LENTE T4 — Cibernética

**Sensores:** Facturación mensual (funciona). Todo lo demás: sin sensor.

**Actuadores:** Único actuador: "más horas." No tiene actuador de "optimizar", "delegar" ni "reducir."

**Señales ignoradas:** La esposa. El tercer sillón vacío. El patrón del padre.

**Regulación:** Totalmente rígida. Ante cualquier estímulo, misma respuesta: más horas.

#### INTEGRAR (∫)

Las 4 lentes coinciden en: el sistema tiene un único actuador, un cuello de botella, y una estrategia que amplifica el problema. La esposa tiene baja capacidad de acción pero alta capacidad de detección — asimetría clave. La expansión no es decisión de negocio sino mecanismo de evitación.

#### ABSTRAER

Clase: "operario-propietario que confunde escalar el sacrificio con escalar el negocio." Patrón auto-similar: su padre ejecutó exactamente esto.

#### FRONTERA

No examina: calidad real de la relación, razones del asociado, estado de salud actual. El diagnóstico es preciso pero la prescripción requiere transformación identitaria fuera del alcance estructural.

#### RESUMEN (200 palabras)

El odontólogo opera como recurso crítico y cuello de botella simultáneo de su propia clínica. Trabaja 60h/semana con un tercer sillón vacío el 40% del tiempo, y su respuesta es ampliar a 5 sillones — resolver infrautilización con más infraestructura. El gap identidad-acción es total: se presenta como empresario pero actúa como operario sobreexplotado. El banco gana en todos los escenarios porque cobra intereses independientemente del resultado. La familia funciona como sensor desconectado del circuito de decisión: la esposa detecta el problema pero no tiene poder para modificar la respuesta. El sistema tiene un solo actuador (más horas del dueño) y regulación rígida: ante cualquier estímulo, la misma respuesta. El patrón de su padre — infarto a los 52 trabajando 70h/semana — opera como la fuerza gravitatoria más potente del sistema precisamente porque no se nombra ni se mide. La convergencia natural del sistema sin intervención es crisis biológica y/o matrimonial. La expansión no es decisión de negocio sino mecanismo de evitación: permite no mirar la señal del tercer sillón vacío, la señal de la esposa, y la señal del padre. Optimizar lo existente antes de expandir no requiere capital, requiere identidad nueva.

---

### CASO 2: STARTUP SAAS

#### EXTRAER — Coordenadas sintácticas

**C1 — Compresión:**
Una palabra: **hemorragia**. Una frase: un barco con dos capitanes que discuten la dirección mientras se hunde por un agujero en el casco. Un párrafo: una startup con 80 clientes y 8% de churn mensual pierde ~6 clientes al mes, lo que significa que en 10 meses su base orgánica se habrá renovado completamente. El CTO quiere tapar el agujero (estabilizar), el CEO quiere navegar a aguas más ricas (pivotar a enterprise). Ninguno mira el dato fundamental: a 8% de churn mensual, en 7 meses de runway van a perder ~40 de los 80 clientes actuales sin reemplazo garantizado.

**C2 — Gap id↔ir:**
CTO dice: "creer en la estabilización del producto." Hace: trabajar 70h/semana con juniors que no retiene, acumulando 47 bugs. No estabiliza — apaga fuegos. CEO dice: "buscar crecimiento para sobrevivir." Hace: evitar la conversación real sobre por qué los 3 fondos dijeron no. Su gap: se presenta como visionario estratégico pero no ha resuelto por qué se fue el co-fundador técnico.

**C3 — Conexiones y desconexiones:**
Conectado: bugs → churn → métricas malas → rechazo de fondos. Desconectado: CEO y CTO entre sí. La salida del co-fundador técnico con el estado actual. Los 3 clientes grandes (30% ingreso, features custom) con la estrategia general. La rotación de devs con las condiciones de trabajo.

**C4 — Poder:**
CEO (0.6 sobre dirección), CTO (0.7 sobre producto, 0.3 sobre dirección), 3 clientes grandes (0.5 colectivo), fondos (0.8 por veto de omisión), equipo técnico (0.1 individual, 0.4 colectivo), co-fundador ausente (poder residual por ausencia de competencia senior).

**C5 — Divergencia declarado↔real:**
CTO: ~80% — asume capacidad técnica que no tiene. CEO: ~60% — tiene razón en que morirán, pero su diagnóstico omite que el agujero pierde más rápido de lo que el balde puede llenarse.

#### CRUZAR — Huecos activos

**H1:** Lo que NO se mide: coste de adquisición, lifetime value, razón real de churn (¿bugs o fit de mercado?), satisfacción del equipo. Sin descomponer el churn, tanto "estabilizar" como "pivotar" son respuestas a una pregunta mal formulada.

**H2:** La ruptura CEO-CTO opera con potencia máxima enmarcada como "diferencia de visión estratégica." El fantasma del co-fundador que se fue opera sin nombre.

**H3:** Mientras no se hablen de verdad, ninguno tiene que ceder. Los 3 clientes grandes pagan supervivencia pero su demanda custom desvía desarrollo del producto estándar → más churn de medianos. No es accidental — es la trampa.

#### LENTE T1 — Conjuntos

Dos subconjuntos casi disjuntos: {visión CEO: enterprise} y {visión CTO: estabilidad}. Los 3 clientes grandes están en la intersección = campo de batalla. Conjuntos que faltan: "datos de churn descompuestos", "plan conjunto", "post-mortem del co-fundador", "voz de los 77 clientes medianos." Fuera de todos: vender, cerrar ordenadamente, buscar CTO externo.

#### LENTE T2 — Causal

Circuito 1: bugs→churn→menos ingresos→más presión→peores decisiones→más bugs. Circuito 2: custom para grandes→menos tiempo core→peor core→más churn medianos→más dependencia grandes→más custom. Circuito 3 (balanceo roto): CEO quiere pivotar→CTO resiste→parálisis→la realidad decide. Convergencia: cierre o acqui-hire en 4-7 meses.

#### LENTE T3 — Juegos

Si nadie cambia: fondos no pierden (nunca invirtieron), 3 grandes buscan otro proveedor, equipo se dispersa, valor se evapora. Falta en el tablero: COO/mediador, advisor de producto, voz de los 77 medianos.

#### LENTE T4 — Cibernética

Dos reguladores en conflicto ajustando en direcciones opuestas. Señales ignoradas: salida del co-fundador (sin post-mortem), salida de 2 devs, feedback de fondos (ambos lo usan para confirmar su bias).

#### INTEGRAR (∫)

El problema real no es técnico ni estratégico, es relacional. Poder formal y real están invertidos: CEO decide dirección, CTO determina si el barco flota. El debate pivotar/estabilizar es falso dilema que sustituye al real: ¿pueden trabajar juntos?

#### ABSTRAER

Clase: "cofundadores con visiones divergentes en organismo con reloj de muerte." El co-fundador que se fue ejecutó exactamente esta secuencia.

#### FRONTERA

No examina: equity/pactos de socios, severidad de los 47 bugs, PMF real del mercado de inventario para restaurantes.

#### RESUMEN (200 palabras)

Una startup con 7 meses de runway pierde 8% de sus clientes cada mes mientras sus dos líderes debaten si pivotar o estabilizar. El debate es un falso dilema: a 8% de churn mensual, ni pivotar ni estabilizar funcionan si el agujero no se tapa primero. El CTO dice "calidad" pero no tiene equipo para ejecutar (3 juniors, 2 devs perdidos en 12 meses, 47 bugs). El CEO dice "crecimiento" pero 3 fondos dijeron no porque las métricas actuales no sostienen la narrativa. La fuerza más potente del sistema es la ruptura CEO-CTO, enmarcada como "diferencia estratégica" cuando es crisis de confianza personal. Dos circuitos destructivos se alimentan: bugs→churn→menos ingresos→más presión, y features custom para grandes→peor producto core→más churn de medianos→más dependencia de grandes. El 30% de ingreso concentrado en 3 clientes distorsiona el desarrollo. El co-fundador que se fue es el precedente exacto de lo que está ocurriendo. Sin intervención, converge a cierre en 4-7 meses. La variable binaria real no es pivotar/estabilizar, es: ¿pueden estos dos trabajar juntos o no?

---

### CASO 3: CAMBIO DE CARRERA

#### EXTRAER — Coordenadas sintácticas

**C1 — Compresión:**
Una palabra: **parálisis**. Una frase: una mujer que sabe exactamente lo que quiere pero ha construido una vida entera que le impide hacerlo. Un párrafo: una abogada de 45 años con 20 años de trayectoria gana 180K€ y lleva 3 años pensando en saltar a una ONG medioambiental por 55K€, mientras su cuerpo produce insomnio de 2 años, su bufete le dice "quizá la próxima vez", no ha hablado con su marido, y repite dos frases contradictorias como si fueran compatibles: "si no ahora, nunca" y "no puedo arriesgar la estabilidad."

**C2 — Gap id↔ir:**
Dice: "pensar en cambiar de carrera." Hace: quedarse. 3 años "pensando." El pensamiento ha reemplazado a la acción. El gap no es entre lo que dice y lo que hace — es entre dos identidades internas que no pueden coexistir sin resolver la tensión.

**C3 — Conexiones y desconexiones:**
Conectado: salario→hipoteca→estabilidad. Insomnio→estrés→médico. Desconectado: ella con su marido respecto a la decisión. Ella con los números reales de viabilidad. El "quizá próximo ciclo" con la realidad del rechazo. Los hijos como argumento de inmovilidad con los hijos como seres que observan a su madre infeliz.

**C4 — Poder:**
Bufete (0.7), hipoteca (0.5), padres (0.3), amiga (0.2), marido (0.1 activado / 0.5 potencial — no se le ha consultado), cuerpo (0.6 y subiendo).

**C5 — Divergencia declarado↔real:**
"No puedo arriesgar la estabilidad." Verificación: ingreso familiar post-cambio ~115K (55K + ~60K marido). Hipoteca: 21.6K/año. Ahorros: 120K de colchón. No es catástrofe, es cambio de nivel de vida. Divergencia: ~50%.

#### CRUZAR — Huecos activos

**H1:** Las emociones tienen nombre, las decisiones no tienen números. No ha calculado viabilidad, coste del insomnio, probabilidad real de socia, impacto en hijos de madre infeliz vs madre que gana menos.

**H2:** Miedo al juicio (padres, sociedad, autojuicio). Identidad de 20 años como "abogada corporativa." La conversación no tenida con el marido: lo más fácil de hacer y lo más evitado, lo que sugiere que teme que si él dice "hazlo", ya no tiene excusa.

**H3:** La desconexión con el marido sostiene todo. La desconexión entre números reales y narrativa de catástrofe también. El diagnóstico médico da legitimidad al malestar sin obligar a actuar.

#### LENTE T1 — Conjuntos

"Vida actual" y "vida deseada" son casi disjuntos. Los hijos están en ambos con funciones opuestas. Conjuntos que faltan: "transición gradual", "negociación con bufete", "plan financiero detallado", "conversación con marido." Fuera de todos: montar algo propio en derecho medioambiental, que el insomnio se agrave hasta crisis.

#### LENTE T2 — Causal

Circuito de parálisis: quiero cambiar→no puedo arriesgar→me quedo→sufro→quiero más→más miedo→me quedo. Circuito de degradación: estrés→insomnio→peor rendimiento→menos probabilidad socia→más frustración. Convergencia: cronificación o crisis de salud que decide por ella.

#### LENTE T3 — Juegos

Si nadie cambia: gana el bufete (retiene abogada a precio de asociada). Los hijos heredan el patrón: sacrifica deseo por seguridad. Falta: coach de transición, asesor financiero, terapeuta, y sobre todo el marido (fuera por omisión de ella).

#### LENTE T4 — Cibernética

Poder 0.7 con cero actuadores activos. El cuerpo (insomnio) es el único regulador funcional y es involuntario. Sistema en bucle abierto: recibe señales, no actúa.

#### INTEGRAR (∫)

Los hijos son el único objeto que cambia de función según la lente: argumento de inmovilidad (causal), excusa (juegos), señal silenciosa (cibernética), miembros de ambas vidas (conjuntos). Solo cruzando las 4 se ve la paradoja: son simultáneamente la excusa para no actuar y la razón más profunda para actuar.

Poder 0.7 pero actuadores 0. La brecha entre poder y acción ES el caso completo.

#### ABSTRAER

Clase: "persona con recursos suficientes para cambiar que usa la complejidad del cambio como escudo contra la acción." Patrón auto-reproductivo: cada año que pasa confirma "no era el momento."

#### FRONTERA

No examina si el deseo es genuino o fantasía de escape. No examina si 20 años de derecho corporativo tienen valor transferible > 55K. La estructura diagnostica la parálisis pero no puede romperla.

#### RESUMEN (200 palabras)

La abogada lleva 3 años en un bucle de parálisis deliberada: sabe lo que quiere, tiene recursos para hacerlo (120K ahorrados, marido con ingresos, experiencia transferible), pero mantiene activas las desconexiones que impiden la decisión: no habla con su marido, no calcula los números, no procesa el rechazo a socia como definitivo. El gap identitario no es entre lo que dice y lo que hace sino entre dos identidades internas incompatibles: "profesional responsable" y "persona auténtica." La no-conversación con el marido es el agujero negro del sistema: evitarla sostiene la parálisis porque si él dijera "hazlo", desaparece la última excusa. Los hijos son el objeto más paradójico: simultáneamente la excusa para quedarse y la razón más profunda para irse (¿qué aprenden viendo a su madre infeliz?). El cuerpo es el único regulador activo: el insomnio de 2 años es el sistema tomando la puntuación que la mente se niega a leer. Tiene poder 0.7 pero cero actuadores encendidos. Sin intervención, converge a: cronificación de la frustración o crisis de salud que decide por ella. Los números, si los calculara, mostrarían que el riesgo es real pero no catastrófico.

---

### POST-3-CASOS

#### LOOP TEST (Caso elegido: Startup SaaS)

La segunda pasada revela que el análisis tiene un **sesgo hacia lo relacional como causa raíz**. La relación CEO-CTO podría ser síntoma de falta de product-market fit, no causa de los problemas. Si el mercado no existe, reparar la relación no salva nada. La lente estructural ve desconexiones internas pero no viabilidad del sistema en su entorno. El circuito causal principal podría estar invertido: no es ruptura→parálisis→muerte sino mercado_muerto→frustración→ruptura. Genuinamente nuevo: sí — revela punto ciego operativo de la propia inteligencia.

#### PATRÓN CROSS-CASE

En los 3 casos, el protagonista mantiene activamente una **desconexión funcional** que impide la decisión, disfrazada de complejidad o responsabilidad. La pieza que falta no es información sino una conversación evitada.

Segundo patrón: en los 3 casos, **si la persona no decide, el sistema o el cuerpo decide por colapso** (infarto del padre, muerte por runway, insomnio escalante).

#### SATURACIÓN

Tercera pasada no aportaría hallazgos nuevos. Saturación alcanzada en segunda pasada.

#### FIRMA

Las desconexiones funcionales — huecos que no son accidentes sino mecanismos activos de estabilización del status quo — y la inversión entre poder formal y poder real dentro de cada sistema. La inteligencia estructural no diagnostica qué hacer sino qué forma tiene lo que impide hacer.



============================================================
## Motor/Meta-Red de preguntas inteligencias/resultados/logico matemática.md
============================================================

# RESULTADOS FASE 1 — CARTOGRAFÍA META-RED

**Proyecto:** CARTOGRAFÍA META-RED
**Estado:** En ejecución
**Inicio:** 2026-03-07

---

## INT-01: LÓGICO-MATEMÁTICA

### Caso 1: Clínica Dental

**Resumen:** La inteligencia lógico-matemática revela que el caso contiene una contradicción central: proponer expansión (3→5 sillones) cuando existe un 40% de capacidad infrautilizada en el sillón actual. Los números muestran un sistema subdeterminado con más incógnitas que ecuaciones, donde la estimación clave (65K€/mes post-expansión) no está validada. El análisis de sensibilidad muestra que una desviación del 20% en esa estimación convierte la expansión en pérdida neta. La variable de mayor apalancamiento — ocupación del sillón 3 y optimización de precios — no está siendo considerada. Todas las lentes convergen en que expandir antes de optimizar es ineficiente, pero divergen en si el problema real es matemático o de valores. La lente de optimización demuestra que más ingresos y más tiempo familiar son objetivos en conflicto directo, y la elección entre ellos es una preferencia, no un cálculo. El patrón abstracto — escalar antes de optimizar — es universal en PyMEs. La frontera del análisis es clara: los números demuestran que no debe expandir, pero no pueden resolver lo que la expansión pretendía tapar: la identidad del propietario atada al crecimiento y el miedo a repetir la historia cardiovascular de su padre.

**Firma:** Los números revelan que la expansión es una respuesta a la pregunta equivocada: hay una contradicción lógica entre capacidad ociosa y propuesta de crecimiento que ninguna otra inteligencia formalizaría con esta claridad.

### Caso 2: Startup SaaS

**Resumen:** La inteligencia lógico-matemática revela que la startup enfrenta una muerte exponencial: con churn del 8%/mes, la base de clientes se reduce a la mitad en 8 meses sin adquisición. El burn de 28K contra MRR de 12K genera un déficit de 16K/mes que consume el runway de 7 meses. El análisis algebraico muestra una contradicción temporal: pivotar a enterprise requiere ciclos de venta de 6-12 meses con un runway de 7. Es temporalmente imposible. Estabilizar sin corregir unit economics (ARPU de 150€) solo retrasa la muerte. El churn es la variable de efecto desproporcionado — bajar de 8% a 4% es la diferencia entre 29 y 48 clientes a 12 meses. Pero la capacidad de ejecución (3 juniors sin senior) es el constraint que hace que cualquier solución ambiciosa sea inviable. La pregunta "¿pivotar o estabilizar?" asume falsamente que ambas son opciones viables. El análisis sugiere una tercera vía: arreglar los bugs más letales, subir precios, reducir burn, y buscar salida digna. La frontera del análisis es que los números dicen "cierra" pero no pueden pesar el coste personal de hacerlo ni la probabilidad no cero de un milagro.

**Firma:** Los números demuestran que la pregunta presentada es falsa: ninguna de las dos opciones cabe en las restricciones temporales y de capacidad. Solo la formalización matemática del churn exponencial + runway finito hace visible que ambas opciones están muertas.

### Caso 3: Cambio de carrera

**Resumen:** La inteligencia lógico-matemática revela que el caso presenta una falsa dicotomía: la decisión no es "bufete o ONG" sino "cuándo y cómo transicionar" dentro de un espectro de opciones intermedias. Los números muestran que el cambio es financieramente viable pero ajustado: ingreso familiar caería de 220-260K a 95-135K, con hipoteca de 21.6K/año y universidad en 2 años como restricciones duras. Los ahorros de 120K cubren ~1 año de diferencia de ingresos. La variable más inestable es el ingreso del marido (rango 40-80K), y no han hablado del tema — esa conversación es prerequisito matemático para resolver la ecuación. El timing tiene efecto no lineal: esperar 2 años permite acumular más colchón y coincidir con la entrada del hijo mayor a universidad con el salario alto. La contradicción lógica central es que ella protege la "estabilidad de los hijos" mientras lleva 2 años con insomnio crónico — el riesgo que intenta evitar ya se está materializando. Los números pueden calcular el timing óptimo de transición, pero la decisión de qué vida quiere vivir está fuera de su alcance.

**Firma:** Los números revelan que existe un timing óptimo calculable que nadie ha calculado, y que la contradicción "proteger estabilidad mientras me deterioro" convierte el statu quo en un riesgo activo, no en seguridad.

### Loop test (P06)

**Caso elegido:** Startup SaaS

**Hallazgos nuevos de la 2ª pasada:**
1. Pivot enterprise podría ser upsell a clientes existentes (semanas) no mercado nuevo (meses) — invalida la contradicción temporal.
2. 47 bugs sin ponderar por severidad — si 5 causan 80% del churn, resolución viable en 4-6 semanas con 3 juniors.
3. Break-even no calculado: si burn baja a 20K y churn a 4%, necesita 20K MRR — difícil pero no imposible.

**¿Genuinamente nuevo?** Sí. La distinción upsell vs mercado nuevo cambia la conclusión de "temporalmente imposible" a "posible si se redefine". La primera pasada heredó la definición del CEO sin cuestionarla.

**No-idempotente:** Confirmado.

### Patrón cross-case

Los 3 casos presentan decisiones binarias que son falsas dicotomías sobre espacios continuos. En los 3 hay una opción intermedia dominante no explorada y una variable no contabilizada de efecto desproporcionado.

### Saturación (P07)

Una tercera pasada no aportaría significativamente. El patrón ya está claro y lo que queda por descubrir requiere datos del mundo real, no más análisis.



============================================================
## Motor/SPEC_ADDENDUM_v2_CALCULADORA_SEMANTICA.md
============================================================

# SPEC ADDENDUM v2: CALCULADORA SEMÁNTICA — TERCER PARADIGMA

> **Estado:** CR0
> **Fecha:** 3 marzo 2026
> **Complementa:** SPEC_COORDENADAS_SEMANTICAS_v1.md (se mantiene íntegra)
> **Cambio principal:** Nuevo paradigma + calculadora como capa central

---

## 1. DE DOS A TRES PARADIGMAS

La v1 definió dos paradigmas: IAS (estructura) + LLM (probabilística).
La v2 añade un tercero: **Calculadora semántica (cálculo determinista).**

```
Paradigma 1 — IAS: extrae estructura del texto (parseadores)
Paradigma 2 — CALCULADORA: computa propiedades de operaciones cognitivas (código puro)
Paradigma 3 — LLM: genera lo no computable (inferencias etiquetadas)

Flujo: IAS extrae → Calculadora computa → LLM expande lo no computable
                                         → Calculadora verifica output LLM
```

### Por qué es un paradigma distinto

Un LLM calcula sobre la superficie del lenguaje (qué palabras suelen ir juntas).
La calculadora calcula sobre la estructura del pensamiento (qué operaciones cognitivas se ejecutaron y qué propiedades tienen).

No es inferencia. No es probabilística. Es cálculo determinista: misma entrada → misma salida. Aplicable a cualquier dominio (empresa, investigación, medicina, derecho, educación) porque opera sobre el pensamiento, que es universal.

---

## 2. LA CALCULADORA — ANALOGÍA FUNDACIONAL

```
CALCULADORA NUMÉRICA:          CALCULADORA SEMÁNTICA:
  Datos: números                 Datos: propiedades de operaciones cognitivas
  Operaciones: +, -, ×, ÷       Operaciones: completitud, congruencia, composición,
  Resultado: números                          propagación, inversión, distancia
  Propiedades: determinista      Resultado: diagnóstico + prescripción computable
                                 Propiedades: determinista, verificable, reproducible
```

### Los "números" semánticos (operandos)

Un operando semántico es una operación cognitiva con propiedades observables:
- Tipo de operación (sustantivizar, adjetivizar, verbalizar, conectar)
- Posiciones requeridas (lo que la operación exige: rango, punto, foto_2, agente...)
- Posiciones ocupadas (lo que el hablante realmente llenó)
- Datos de dominio asociados

Estos vienen del posicionador (SPEC v1, capa 1a).

---

## 3. LAS 6 OPERACIONES

### OP-1 COMPLETITUD (¿cuántas posiciones están llenas?)
```
completitud = posiciones_ocupadas / posiciones_requeridas
"resultados sólidos" como adjetivización: 0/3 = 0.0 (rango, punto, foto_2 = vacíos)
"-8% margen" como adjetivización: 3/3 = 1.0
```
Implicación: completitud 0.0 = operación cognitiva vacía. No es error — es dato.

### OP-2 CONGRUENCIA (¿el operando coincide con el dato?)
5 estados (más fino que v1):
- congruente (operando completo confirma dato)
- incongruente (operando completo contradice dato)
- indeterminado_sesgo_incongruente (operando VACÍO con tono que choca)
- indeterminado_operando_vacio (vacío, no se puede decir nada)
- indeterminado_sin_dato (no hay contra qué comparar)

"Sólidos" + margen -8% = indeterminado_sesgo_incongruente (no "contradice" — es más preciso: la operación está vacía pero su tono choca con el dato).

### OP-3 COMPOSICIÓN (¿qué pasa al combinar operaciones?)
Sustantivo + adjetivo vacío = compuesto CONTAMINADO.
"Resultados sólidos" es menos informativo que "resultados" solo.
Porque "sólidos" inyecta falsa confianza sin añadir información.
Solo visible al componer — las partes individuales no lo revelan.

### OP-4 PROPAGACIÓN (si un dato cambia, ¿qué se mueve?)
Análisis de sensibilidad semántico.
Si margen pasa de -8% a +5%: ¿qué hallazgos se mueven?
Resultado: la espiral dev-churn NO se mueve (independiente de margen).
Esto hace la fragilidad COMPUTABLE en vez de estimada.

### OP-5 INVERSIÓN (¿qué hay que añadir para alcanzar el objetivo?)
Resolver ecuación: si necesito completitud ≥ 0.7 y tengo 0.0, ¿qué posiciones llenar?
Con datos existentes: rango (margen) + punto (-8%) → completitud 2/3 = 0.66.
Prescripción CALCULADA, no generada por LLM.

### OP-6 DISTANCIA (¿cuán lejos está del estado objetivo?)
Distancia + resolubilidad = distancia EFECTIVA.
PARADOJA: lejos pero resoluble = máximo ROI de intervención.
"Sólidos": distancia alta + resolubilidad 1.0 → PARADOJA (actuar primero).
"Más fuerte": distancia alta + resolubilidad 0.1 → irresoluble sin dato nuevo.

---

## 4. CAMBIO EN EL PIPELINE

La calculadora se inserta como CAPA 3 entre descompresor y lentes:

```
CAPA 0: Parseadores (existentes)
CAPA 1a: Posicionador (genera operandos) ← v1
CAPA 1b: Calculador numérico (existente)
CAPA 1.5: Hipótesis + Confrontador (existentes)
CAPA 2: Descompresor ← v1

═══ CAPA 3: CALCULADORA SEMÁNTICA (NUEVO) ═══
    OP-1 a OP-6 sobre todos los operandos
    Output: diagnóstico calculado + prescripciones + prioridades + fragilidad
═══════════════════════════════════════════════

CAPA 4: Lentes (reciben output calculadora)
CAPA 5: Sintetizador (fragilidad por propagación)
CAPA 6: Router (lo calculado = certeza, lo no calculable → LLM)
CAPA 7: Síntesis fusionada (4 capas: certezas, cálculos, inferencias, huecos)
CAPA 8: Verbalizador
CAPA 9: Auto-verificador (calculadora sobre output propio)
```

**Cambio clave:** El router (capa 6) ahora usa la inversión (OP-5) como criterio:
- Si OP-5 prescribió con datos → la prescripción calculada prevalece (CERTEZA)
- Si OP-5 dijo "requiere_dato_nuevo" → LLM infiere (INFERENCIA etiquetada)

---

## 5. AGENTE NUEVO

| Agente | Capa | Tipo | Modelo | Coste |
|--------|------|------|--------|-------|
| calculadora-semantica | 3 | Código puro | — | $0 |

Es 1 Edge Function con 6 operaciones internas. Escribe 1 marca con todo el resultado.

---

## 6. OUTPUT DE LA CALCULADORA (formato marca)

```json
{
  "tipo": "calculo_semantico",
  "capa": 3,
  "agente": "calculadora-semantica",
  "datos": {
    "ciclo_id": "xxx",
    "lente": "salud",
    "completitudes": [...],
    "congruencias": [...],
    "composiciones": [...],
    "propagaciones": [...],
    "inversiones": [...],
    "distancias": [...],
    "mapa_prioridad": [
      {"fragmento": "incorporando", "d_efectiva": 0.22, "paradoja": true},
      {"fragmento": "sólidos", "d_efectiva": 0.43, "paradoja": true},
      {"fragmento": "0 PERO", "d_efectiva": 0.55, "paradoja": true},
      {"fragmento": "más fuerte", "d_efectiva": 0.86, "paradoja": false}
    ],
    "mapa_fragilidad": {
      "score": 0.85,
      "n_datos_soporte": 5,
      "datos_alta_sensibilidad": ["velocity", "margen_neto"],
      "interpretacion": "robusto: múltiples datos independientes convergen"
    },
    "paradojas": [
      {"fragmento": "sólidos", "d_total": 0.85, "resolubilidad": 1.0, "accion": "dato existe, usar"},
      {"fragmento": "incorporando", "d_total": 0.40, "resolubilidad": 0.9, "accion": "completar neto"}
    ]
  }
}
```

---

## 7. DECISIONES CR1

1. Aprobar tercer paradigma (calculadora semántica)
2. ¿Las 6 operaciones todas en primera iteración? Recomendación: sí (son código puro, interdependientes)
3. La calculadora reemplaza la lógica de fragilidad actual en sintetizador → aprobar
4. ¿La interfaz muestra las 6 operaciones como sub-nodos animados?

---

**FIN ADDENDUM v2**



============================================================
## Motor/SPEC_COORDENADAS_SEMANTICAS_v1.md
============================================================

# SPEC: SISTEMA DE COORDENADAS SEMÁNTICAS — POLARIDAD DIAGNÓSTICA + GENERATIVA

> **Estado:** CR0 — Jesús valida
> **Fecha:** 3 marzo 2026
> **Versión:** 1.0
> **Origen:** Sesión Opus — Semilla Coordenadas Semánticas
> **Dependencias:** ARQUITECTURA_SO_OMNI_MIND v1.2 (§9), PIPELINE_IAS_V2, MARCO_LINGUISTICO §60

---

## 1. PROPÓSITO

Convertir el Motor IAS de diagnóstico binario (hueco sí/no) a un sistema de pensamiento completo que:

1. **Diagnostica** con coordenadas ricas: dimensiones discretas (QUÉ tipo de problema) + gradientes (CUÁNTO falta)
2. **Genera** pensamiento posicionándose conscientemente en coordenadas correctas
3. **Fusiona** dos paradigmas: IAS (estructura, certeza) + LLM (probabilística, posibilidades)
4. **Se auto-verifica** aplicando sus propias coordenadas diagnósticas a su output

**Objetivo de potencia:** Pensar mejor que un modelo monolítico (Opus/Gemini) mediante especialización + fusión de paradigmas.

---

## 2. LOS DOS PARADIGMAS

### Paradigma IAS (estructura)
- La información está DENTRO de lo que se dice
- Se extrae, no se infiere
- Riguroso, reproducible, determinista
- No depende de haber visto casos similares
- Detecta lo que HAY y lo que FALTA con certeza
- **Límite:** no puede ver lo que nunca estuvo en el texto ni en los datos

### Paradigma LLM (probabilística)
- Conecta patrones entre millones de situaciones
- Genera posibilidades, analogías, escenarios
- Intuye lo que no se dice
- **Límite:** no distingue dato de inferencia, mezcla niveles, alucina

### Fusión
- IAS es el esqueleto (qué movimientos son válidos)
- LLM es el músculo (ejecuta los movimientos)
- IAS verifica lo que LLM genera
- LLM expande lo que IAS encuentra
- Cada uno cubre la debilidad del otro

---

## 3. COORDENADAS: DIMENSIONES DISCRETAS + GRADIENTES

Cada hallazgo del Motor tiene dos capas de coordenadas:

### Capa 1: Dimensiones discretas (QUÉ tipo de problema)

Clasificación cualitativa que preserva la riqueza del hallazgo. No se puede reducir a un número sin perder información.

### Capa 2: Gradientes por dimensión (CUÁNTO falta)

Cuantificación dentro de cada dimensión. Se calcula con datos observables, no subjetivamente.

**Los dos juntos:** diagnóstico cualitativo con magnitud cuantitativa.

---

## 4. COORDENADAS POR PARSEADOR — DIMENSIONES DISCRETAS

### 4.1 Parseador-Sustantivos

**Dimensión NATURALEZA_COMPRESIÓN:**
```
dato_puro          "445K revenue" — número verificable, sin compresión
etiqueta_llena     "clientes" — sustantivo con referente real y contable
nominalización     "crecimiento" — verbo congelado, pierde agente+tempo
abstracción        "talento" — sin referente unívoco, sin conteo posible
metáfora           "camino correcto" — transferencia de dominio
```

**Dimensión VERIFICABILIDAD:**
```
verificado_con_dato     hay dato en dominio que confirma o contradice
verificable_sin_dato    se podría verificar pero no hay dato disponible
no_verificable          por naturaleza no es verificable (metáfora, identidad)
```

**Dimensión FUNCIÓN:**
```
sujeto        proyecta el tema (máxima carga semántica)
complemento   enmarca
adjetival     cualifica otro sustantivo
adverbial     modifica acción
```

**Dimensión CONGRUENCIA:**
```
congruente      dato confirma lo que el sustantivo implica
incongruente    dato contradice
parcial         dato matiza (ni confirma ni refuta limpiamente)
sin_dato        no hay contra qué verificar
```

### 4.2 Parseador-Adjetivos

**Dimensión CUANTIFICACIÓN:**
```
cerrada                  "445K", "-8%", "99.2%" — punto preciso en rango
comparativa_con_ref      "más fuerte que Q2" — tiene foto 2 explícita
comparativa_sin_ref      "más fuerte" — superlativo sin foto 2
evaluativa_con_criterio  "bueno según NPS" — tiene criterio declarado
evaluativa_sin_criterio  "sólido" — juicio sin criterio
metafórica               "correcto" (sobre "camino") — no cuantifica nada
```

**Dimensión FOTO_2:**
```
declarada_verificada     hay referente Y hay dato que lo confirma
declarada_sin_dato       hay referente pero no hay dato
ausente_pero_inferible   no declarada pero datos dominio sugieren una
ausente_no_inferible     no declarada y no hay dato que la supla
```

**Dimensión RELACIÓN_DATO:**
```
confirma     el dato valida el adjetivo
contradice   el dato refuta el adjetivo
parcial      el dato matiza
sin_dato     no hay dato disponible
```

### 4.3 Parseador-Verbos

**Dimensión AGENCIA:**
```
agente_explícito_concreto  "Juan contrató" — quién + qué
agente_explícito_difuso    "nosotros cerramos" — quién exactamente?
agente_implícito           "sigue creciendo" — nadie "hace" que crezca
sin_agente                 "se ha tenido" — impersonal
agente_falso               "la economía exige" — abstracción como agente
```

**Dimensión MODO:**
```
acción_completada    "cerramos 445K" — hecho verificable
acción_continuativa  "seguimos incorporando" — proceso abierto
estado               "estamos en el camino" — no hay acción
performativo         "quiero compartir" — acto comunicativo, no acción real
meta_infinitivo      "alcanzar" — acción futura sin plan
```

**Dimensión CONGRUENCIA:**
```
congruente     la acción descrita coincide con datos
parcial        la acción es real pero omite la otra cara
incongruente   la acción descrita contradice datos
vacía          el verbo no describe acción verificable
```

### 4.4 Parseador-Conectores

**Dimensión TIPO_CONEXIÓN:**
```
Y_real              ambos lados verificados, sinergia real
Y_listado           acumulación sin relación (cherry-picking)
PERO_explícito      tensión declarada y visible
PERO_ausente        tensión que debería estar y no está (omisión)
AUNQUE_explícito    concesión declarada
SI_ENTONCES         condicional verificable
```

**Dimensión ESTADO_RESOLUCIÓN:**
```
resuelto    la tensión tiene resolución explícita
abierto     la tensión existe sin resolver
falso       la conexión es falaz
omitido     la conexión debería existir y no existe
```

**Dimensión LO_QUE_FALTA:**
```
conector_adversativo    falta un PERO que debería estar
conector_causal         falta un PORQUE que explique
conector_condicional    falta un SI-ENTONCES que condicione
nada                    la estructura conectiva es completa
```

### 4.5 Parseador-Niveles

**Dimensión COHERENCIA:**
```
coherente              dice N3, estructura es N3
disfraz_ascendente     dice N3, estructura es N1 (dato disfrazado de estrategia)
disfraz_descendente    dice N1, estructura es N4 (creencia disfrazada de dato)
salto                  pasa de N1 a N4 sin N2-N3
```

**Dimensión TIPO_DISFRAZ:**
```
evaluativo_como_dato        "resultados sólidos" = juicio como dato
misión_como_operativo       "camino correcto" = N5 sin N2
identidad_como_estrategia   "somos innovadores" = N4 sin N3
sin_disfraz                 nivel coherente
```

**Dimensión COMPLETITUD_MAPA:**
```
Para cada nivel N1-N5: presente | ausente
Ejemplo: {N1: 3, N2: 1, N3: 2, N4: 0, N5: 0} — ya existe en parseador
```

### 4.6 Confrontador-Input (M-8)

**Dimensión TIPO_CONTRADICCIÓN:**
```
negación_activa      input positivo + dato negativo
omisión_selectiva    dato negativo existe, input lo ignora
inversión            input dice lo contrario del dato
contradicción_cr1    input propone lo que CR1 rechazó
```

**Dimensión ALCANCE:**
```
puntual        1 afirmación contradice 1 dato
sectorial      varias afirmaciones de un área contradicen datos
estructural    pattern de contradicción que cruza todo el input
```

---

## 5. GRADIENTES POR DIMENSIÓN

Cada dimensión discreta tiene un gradiente natural calculable con datos observables (código puro):

### 5.1 Gradiente de COMPLETITUD DESCOMPRESIVA
```
Para sustantivos: posiciones_ocupadas / posiciones_requeridas
Posiciones: agente, objeto, periodo, instrumento, resultado
"Resultados sólidos": 1/5 = 0.2 (solo periodo implícito)
Cálculo: conteo puro
```

### 5.2 Gradiente de CONGRUENCIA
```
datos_que_confirman / total_datos_disponibles
"Resultados sólidos": revenue confirma, margen/velocity/churn/NPS contradicen = 1/5 = 0.2
Cálculo: conteo puro contra conocimiento_dominio
```

### 5.3 Gradiente de RESOLUBILIDAD
```
f(datos_existen, datos_accesibles, datos_resuelven)
"Sólidos": datos existen SÍ, accesibles SÍ, resuelven SÍ (contradicen) = 1.0
"Más fuerte": datos existen NO = 0.0
Cálculo: 3 flags binarios → 0.0 | 0.33 | 0.66 | 1.0
```

### 5.4 Gradiente de CONTRADICCIÓN
```
datos_que_contradicen / total_datos_verificados
"Sólidos": 4 de 5 métricas contradicen = 0.8
Cálculo: conteo puro
```

### 5.5 Gradiente de ESPECIFICIDAD AGENCIA
```
f(agente_nombrado, agente_único, agente_verificable)
"Juan contrató" = 3/3 = 1.0
"Nosotros cerramos" = 1/3 = 0.33
"Se debería" = 0/3 = 0.0
```

### 5.6 Gradiente de ACCIONABILIDAD
```
f(tiene_agente, tiene_objeto, tiene_plazo, tiene_métrica)
"Alcanzar objetivos" = 1/4 (solo objeto genérico) = 0.25
"Juan contrata 3 seniors en 30 días" = 4/4 = 1.0
```

### 5.7 Gradiente de COMPLETITUD CONECTIVA
```
conectores_resueltos / conectores_necesarios
TechFlow: 0 adversativos de ~3 necesarios = 0.0
"necesarios" = estimado por cantidad de afirmaciones + datos que contradicen
```

### 5.8 Gradiente de COHERENCIA NIVELES
```
fragmentos_nivel_correcto / total_fragmentos_analizados
TechFlow: 1 coherente de 4 analizados = 0.25
```

### 5.9 Gradiente de EXTENSIÓN CONTRADICCIÓN
```
departamentos_con_contradicción / total_departamentos
TechFlow: 4 de 5 = 0.8
```

---

## 6. FUNCIÓN DEL GRADIENTE DE RESOLUBILIDAD COMO ROUTER

El gradiente de resolubilidad determina qué paradigma maneja cada hueco:

```
Resolubilidad ≥ 0.66 → RAMA IAS (datos existen, son accesibles)
  IAS resuelve con certeza. No necesita LLM.

Resolubilidad 0.33-0.66 → RAMA MIXTA (datos parciales)
  IAS aporta lo que tiene. LLM completa con inferencia etiquetada.

Resolubilidad < 0.33 → RAMA LLM (datos no existen)
  LLM infiere. Todo etiquetado como INFERENCIA o SUPOSICIÓN.
  IAS verifica estructura del output del LLM.
```

---

## 7. LAS 7 OPERACIONES COGNITIVAS DEL MOTOR

### 7.1 DESCOMPRIMIR (extraer lo oculto por compresión)
```
Input: pieza comprimida (sustantivo, nominalización, adjetivo evaluativo)
Output: partes constituyentes con estado (presente/ausente/implícito)
Tipo: código puro (estructura) + Haiku (interpretación semántica)
Lo que hace: recupera agente, objeto, periodo, instrumento, referencia
Lo que NO hace: inventar lo que no está (eso es rama LLM)
```

### 7.2 VERIFICAR CONTRA DATO (certeza por cruce)
```
Input: hallazgo + datos verificados de conocimiento_dominio
Output: congruente/incongruente/parcial/sin_dato
Tipo: código puro
Lo que hace: cruza afirmación con dato
Lo que NO hace: juzgar, opinar, inferir contexto externo
```

### 7.3 MAPEAR COMPLETITUD (posiciones vacías)
```
Input: estructura completa del texto
Output: mapa de posiciones ocupadas y vacías por tipo
Tipo: código puro
Lo que hace: identifica qué debería estar y no está
Lo que NO hace: llenar las posiciones vacías (eso es generación)
```

### 7.4 DETECTAR PATRONES ESTRUCTURALES (repetición interna)
```
Input: conjunto de hallazgos del mismo texto
Output: propiedades compartidas por múltiples hallazgos
Tipo: código puro (conteo de propiedades)
Lo que hace: "3 de 3 adjetivos sin foto 2 = patrón sistemático"
Lo que NO hace: comparar con otros textos (eso es probabilística)
```

### 7.5 GENERAR POR COMPLETITUD ESTRUCTURAL (llenar posiciones vacías)
```
Input: mapa de huecos + datos verificados + resolubilidad
Output: posiciones vacías llenadas con datos (rama IAS) o inferencias (rama LLM)
Tipo: mixto (IAS donde resolubilidad alta, LLM donde baja)
Lo que hace: produce pensamiento que ocupa las posiciones que el input dejó vacías
```

### 7.6 GENERAR POR INVERSIÓN ESTRUCTURAL (producir lo opuesto al problema)
```
Input: coordenadas del problema diagnosticado
Output: output donde cada coordenada está en la posición correcta
Tipo: LLM con restricciones inyectadas por código
Lo que hace:
  - Si input tiene adjetivo sin foto 2 → output incluye foto 2
  - Si input tiene agente difuso → output nombra agente concreto
  - Si input omite PERO → output incluye PERO con resolución
```

### 7.7 VERIFICAR OUTPUT PROPIO (auto-referencial)
```
Input: output generado por el Motor
Output: coordenadas del output + flags de debilidad
Tipo: código puro (mismas reglas que diagnóstico)
Lo que hace: aplica las mismas coordenadas diagnósticas al output del Motor
Si el output tiene estructura débil: flag, no regeneración
```

---

## 8. PIPELINE COMPLETO CON COORDENADAS

```
INPUT
  │
  ▼
CAPA 0 — PARSEADORES IAS (paralelo, Haiku, existentes — no se tocan)
  │ Extraen hallazgos como ya lo hacen
  │ Output: marcas estigmérgicas capa 1
  │
  ▼
CAPA 1a — POSICIONADOR (código puro, NUEVO, $0)
  │ Lee marcas de los 9 parseadores del ciclo
  │ Clasifica cada hallazgo en dimensiones discretas
  │ Calcula gradientes por dimensión
  │ Escribe marca tipo "coordenadas" en capa 1
  │ 
  │ Paralelo con calculador existente (capa 1b)
  │
  ▼
CAPA 1b — CALCULADOR + CONTEXTO (existentes — no se tocan)
  │
  ▼
CAPA 1.5 — HIPÓTESIS (M-7, existente, se MODIFICA)
  │ Recibe: hallazgos + coordenadas
  │ generador-hipotesis: usa resolubilidad para calibrar predicciones
  │   Predicción con resolubilidad alta → debe ser cuantificación cerrada
  │   Predicción con resolubilidad baja → puede ser inferencia etiquetada
  │ tester-hipotesis: usa gradiente de contradicción para fuerza de refutación
  │
  ▼
CAPA 1.5b — CONFRONTADOR-INPUT (M-8, existente, se MODIFICA)
  │ Recibe: hallazgos + coordenadas
  │ Usa dimensiones para clasificar tipo y alcance de contradicción
  │ Calcula gradiente de extensión
  │
  ▼
CAPA 2 — DESCOMPRESOR (NUEVO, Haiku)
  │ Recibe: hallazgos con coordenadas donde naturaleza ≠ dato_puro
  │ Para cada pieza comprimida: descomprime hasta partes atómicas
  │ Señala: preservado, perdido, recuperable
  │ Output: marca "descompresion" con partes + estado
  │
  ▼
CAPA 3 — LENTES (existentes, se MODIFICAN)
  │ Reciben: hallazgos + coordenadas + descompresión
  │ Organizan por lente usando gradientes para priorizar
  │ Lente lee umbrales de tabla umbrales_lentes para su lente
  │
  ▼
CAPA 4a — SINTETIZADOR (existente, se MODIFICA)
  │ Fragilidad: calculada como función de distancias (gradientes)
  │ No binaria. Score = 1.0 - Σ(distancia × peso) / Σ(peso)
  │ Patrones: detectados por conteo de propiedades compartidas (código puro)
  │
  ▼
CAPA 4b — ROUTER DE PARADIGMA (NUEVO, código puro, $0)
  │ Para cada hueco/incertidumbre del diagnóstico:
  │   resolubilidad ≥ 0.66 → RAMA IAS
  │   resolubilidad 0.33-0.66 → RAMA MIXTA
  │   resolubilidad < 0.33 → RAMA LLM
  │
  ├── RAMA IAS (código puro + datos verificados)
  │   Genera por completitud: llena posiciones con datos existentes
  │   Genera por inversión: produce lo opuesto al problema
  │   Todo es CERTEZA o CÁLCULO
  │
  ├── RAMA LLM (Sonnet/Opus)
  │   Recibe: certezas IAS + huecos irresolubles por IAS
  │   Genera: inferencias ETIQUETADAS, escenarios, analogías
  │   REGLA: cada pieza etiquetada como DATO/INFERENCIA/SUPOSICIÓN
  │   
  └── VERIFICACIÓN CRUZADA (código puro, $0)
      IAS verifica output del LLM:
      - ¿Algo inferido se puede calcular con datos? → cálculo prevalece
      - ¿Algo dicho contradice un dato? → dato prevalece
      - ¿Output del LLM tiene estructura rota? → flag
      - ¿Output genuinamente expande? → mantener con etiqueta
  │
  ▼
CAPA 5 — PRESCRIPTOR (existente, se MODIFICA)
  │ Genera por inversión estructural:
  │   Para cada coordenada débil del input → coordenada fuerte en prescripción
  │   Cada prescripción: agente concreto + verbo de acción + dato + plazo
  │
  ▼
CAPA 6 — SÍNTESIS FUSIONADA (NUEVO)
  │ Tres capas explícitas en output:
  │   CERTEZAS: lo que IAS verificó con datos
  │   CÁLCULOS: lo que IAS computó desde datos
  │   INFERENCIAS: lo que LLM generó, etiquetado
  │ Cada pieza con gradiente de confianza derivado
  │
  ▼
CAPA 7 — VERBALIZADOR (existente, se MODIFICA)
  │ Produce output en lenguaje natural
  │ Las tres capas son visibles en la verbalización
  │ Cada afirmación lleva su nivel de confianza
  │
  ▼
CAPA 8 — AUTO-VERIFICADOR (NUEVO, código puro, $0)
  │ El output final pasa por las mismas coordenadas diagnósticas
  │ Si el Motor genera "resolver hueco X" → flag: agente ausente, modo meta_infinitivo
  │ Si el Motor genera con foto 2 y agente → pass
  │ Resultado: flag de calidad del output propio
  │
  ▼
OUTPUT FINAL
  Certezas marcadas como certezas
  Cálculos marcados como cálculos
  Inferencias marcadas como inferencias
  Huecos marcados como huecos
  Calidad del output propio: auto-evaluada
```

---

## 9. AGENTES NUEVOS

| Agente | Capa | Tipo | Modelo | Coste |
|--------|------|------|--------|-------|
| posicionador-semantico | 1a | Código puro | — | $0 |
| descompresor | 2 | Sandwich | Haiku | ~$0.001 |
| router-paradigma | 4b | Código puro | — | $0 |
| generador-ias | 4b-IAS | Código puro | — | $0 |
| generador-llm | 4b-LLM | Sandwich | Sonnet/Opus | ~$0.01-0.05 |
| verificador-cruzado | 4b-verif | Código puro | — | $0 |
| sintetizador-fusionado | 6 | Código puro | — | $0 |
| auto-verificador | 8 | Código puro | — | $0 |

Total nuevos: 8 agentes (5 código puro, 2 sandwich, 1 LLM)

## 10. AGENTES MODIFICADOS

| Agente | Modificación |
|--------|-------------|
| orquestador-ias | Nueva secuencia con capas 1a, 2, 4b, 6, 8 |
| generador-hipotesis | Recibe coordenadas, calibra predicciones |
| tester-hipotesis | Usa gradiente contradicción para fuerza |
| confrontador-input | Clasifica tipo/alcance con dimensiones |
| sintetizador-diferencial | Fragilidad por distancias, no binaria |
| prescriptor | Genera por inversión estructural |
| verbalizador | Tres capas visibles, confianza por pieza |

## 11. AGENTES NO TOCADOS

Los 9 parseadores. Las 3 lentes (solo reciben más datos). El calculador. Los agentes de contexto.

---

## 12. TABLA SQL NUEVA: umbrales_lentes

```sql
CREATE TABLE umbrales_lentes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  eje text NOT NULL,
  dimension text NOT NULL,
  lente text NOT NULL,
  umbral_minimo float NOT NULL DEFAULT 0.5,
  peso float NOT NULL DEFAULT 1.0,
  dominio text DEFAULT 'general',
  created_at timestamptz DEFAULT now()
);
```

---

## 13. FORMATO I/O POSICIONADOR

### Input
Lee marcas del ciclo: `SELECT * FROM marcas_estigmergicas WHERE datos->>'ciclo_id' = $1 AND capa = 1`

### Output (marca tipo "coordenadas")
```json
{
  "tipo": "coordenadas",
  "capa": 1,
  "agente": "posicionador-semantico",
  "datos": {
    "ciclo_id": "xxx",
    "hallazgos": [
      {
        "marca_origen_id": "uuid",
        "agente_origen": "parseador-sustantivos",
        "fragmento": "resultados sólidos",
        "dimensiones": {
          "naturaleza_compresion": "etiqueta_generica",
          "verificabilidad": "verificado_con_dato",
          "funcion": "sujeto",
          "congruencia": "incongruente"
        },
        "gradientes": {
          "completitud_descompresiva": 0.2,
          "congruencia": 0.2,
          "resolubilidad": 1.0,
          "contradiccion": 0.8
        },
        "router": "ias"
      }
    ],
    "mapa_global": {
      "n_hallazgos": 15,
      "resolubilidad_media": 0.55,
      "n_para_ias": 8,
      "n_para_mixto": 3,
      "n_para_llm": 4,
      "eje_peor": "cuantificado-fantasma",
      "patron_dominante": "evaluacion_sin_criterio (100% adjetivos)"
    }
  }
}
```

### Formato output generador-llm
```json
{
  "tipo": "inferencia_llm",
  "capa": 4,
  "agente": "generador-llm",
  "datos": {
    "ciclo_id": "xxx",
    "piezas": [
      {
        "contenido": "Los devs probablemente se fueron por deuda técnica",
        "tipo": "inferencia",
        "hueco_origen": "razón_bajas_dev",
        "resolubilidad_origen": 0.0,
        "compatibilidad_datos": "parcial (bugs +140% es indicador compatible)",
        "confianza": 0.4
      }
    ]
  }
}
```

### Formato output síntesis fusionada
```json
{
  "tipo": "sintesis_fusionada",
  "capa": 6,
  "agente": "sintetizador-fusionado",
  "datos": {
    "ciclo_id": "xxx",
    "certezas": [
      {
        "contenido": "Margen neto -8%. La empresa gasta más de lo que ingresa.",
        "fuente": "dato_verificado",
        "confianza": 1.0
      }
    ],
    "calculos": [
      {
        "contenido": "Pipeline 890K × 22% conversión = 196K. Gap vs objetivo: 559K.",
        "fuente": "calculo_ias",
        "datos_usados": ["pipeline_total", "conversion_historica", "objetivo_anual"],
        "confianza": 0.95
      }
    ],
    "inferencias": [
      {
        "contenido": "Bajas probablemente relacionadas con deuda técnica",
        "fuente": "llm_inferencia",
        "verificado_por_ias": "parcial (compatible con bugs +140%)",
        "confianza": 0.4
      }
    ],
    "huecos": [
      {
        "pregunta": "¿El CEO es consciente del margen negativo?",
        "resolubilidad": 0.0,
        "impacto": "alto (cambia interpretación de intención vs ignorancia)"
      }
    ],
    "fragilidad": {
      "score": 0.87,
      "robusto_en": ["incongruencia estructural", "espiral dev-churn", "margen negativo"],
      "fragil_en": ["pipeline (falta histórico)", "intención CEO"]
    },
    "auto_verificacion": {
      "calidad_output": 0.85,
      "debilidades_propias": ["escenario B contiene 2 suposiciones no verificables"]
    }
  }
}
```

---

## 14. EJEMPLO COMPLETO: TECHFLOW

### Input
Comunicado CEO (documento adjunto RESULTADO_PIPELINE_IAS_TECHFLOW.md)

### Coordenadas diagnósticas (posicionador)

| Fragmento | Dimensión principal | Gradiente clave | Router |
|-----------|-------------------|-----------------|--------|
| "resultados sólidos" | evaluativa_sin_criterio + incongruente | contradicción 0.8, resolubilidad 1.0 | IAS |
| "pipeline más fuerte" | comparativa_sin_ref + sin_dato | contradicción ?, resolubilidad 0.1 | LLM |
| "sigue creciendo" | agente_implícito + parcial | accionabilidad 0.25 | MIXTO |
| "incorporando talento" | acción_continuativa + parcial | congruencia 0.4 (oculta 8 salidas) | IAS |
| "camino correcto" | metáfora + no_verificable | resolubilidad 0.0 | LLM |
| 0 PERO | PERO_ausente | completitud_conectiva 0.0 | IAS |

### Output fusionado

**CERTEZAS (IAS):**
- Comunicado 100% positivo. 67% sustantivos ambiguos. 100% adjetivos sin foto 2. 0 conectores adversativos.
- Margen neto -8%. Burn 185K > ingresos 148K. Déficit 37K/mes.
- Revenue crece pero desacelera: QoQ 10.5% → 5.9%.
- Talento neto: +3 (11 entradas - 8 salidas). Desarrollo: -4 neto.
- Patrón estructural: evaluación sistemática sin criterio (3/3 adjetivos).

**CÁLCULOS (IAS):**
- Pipeline: 890K × 22% conversión = 196K proyectado. Gap: 559K. 
- Para cerrar gap: conversión necesaria 55% (sin precedente) O 2.5M pipeline adicional.
- Velocity: a -5pts/mes, llega a 50% baseline en 2 meses.
- Runway: 8 meses al burn actual. ~6 si churn sube 0.5%.

**INFERENCIAS (LLM, etiquetadas):**
- [INFERENCIA] Bajas dev probablemente por deuda técnica + presión. Compatible con bugs +140%.
- [INFERENCIA] Espiral reversible si intervención en <2 meses (corregido por cálculo IAS: 2-3 meses según tasa velocity).
- [SUPOSICIÓN] Si los 4 que se fueron son seniors, pérdida de conocimiento institucional explica caída velocity más allá de headcount.

**HUECOS:**
- ¿El CEO sabe del margen negativo? (resolubilidad 0.0, impacto alto)
- ¿Hay plan no comunicado? (resolubilidad 0.0)
- ¿Pipeline históricamente más fuerte? (resolubilidad 0.1, dato no existe)

**FRAGILIDAD: 0.87 (robusto)**
- Robusto en: incongruencia estructural, espiral dev-churn, margen negativo
- Frágil en: pipeline (falta histórico), intención CEO

**AUTO-VERIFICACIÓN: 0.88**
- Output usa agentes concretos, datos verificados, foto 2 en cada adjetivo
- Debilidad: 2 suposiciones del LLM no verificables (seniority bajas, plan no comunicado)

---

## 15. DECISIONES CR1 PENDIENTES

1. ¿Aprobar esta arquitectura como evolución del Motor?
2. ¿Qué modelo para la rama LLM? (Sonnet por defecto, Opus para ciclos críticos)
3. ¿Descompresor en primera iteración o segunda?
4. ¿Umbrales iniciales de la tabla son correctos?
5. ¿Orden de implementación de los 8 agentes nuevos?

---

**FIN SPEC v1**



============================================================
## Motor/SPEC_MOTOR_ORQUESTADOR_v1.md
============================================================

# SPEC MOTOR-ORQUESTADOR v1 — CON TELEMETRÍA INTEGRADA

> **Estado:** CR0 — Jesús valida
> **Fecha:** 2026-03-03
> **Origen:** Sesión Opus — diseño orquestador motor completo
> **Dependencias:** 7 primitivas-v2 (2 deployed, 5 pendientes), gateway API, llm-proxy, registrarMétrica

---

## 1. DECISIONES ARQUITECTÓNICAS (CR1 pendiente)

| # | Decisión | Resolución | Justificación |
|---|----------|-----------|---------------|
| D1 | Integrador final | Código puro (templates) + Haiku fallback para cruces complejos | Motor produce respuesta semántica neutra. La interfaz adecúa al usuario con sus patrones de comunicación. |
| D5 | Quién verbaliza para el usuario | La INTERFAZ, no el motor. Motor = semántica neutra. Interfaz = adecuación personalizada. | Cada usuario necesita presentación distinta. Los patrones de adecuación viven en el Supabase de la interfaz. |
| D2 | Cómo fusionar | Por capas: filtrar → PIEZAS(1-4) → ESTRUCTURA(5-7) → cruzar → verbalizar | Replica patrón IAS (parseadores → merge → correlador → verbalizar). Mismo ADN, distinta escala. |
| D3 | Lentes antes/después | ANTES — lentes suben diales, nunca los bajan | Eficiencia: menos Haiku ejecutados. Coherencia: outputs ya orientados. |
| D4 | 1 o N Edge Functions | 1 función `motor-orquestador` con Promise.allSettled | Sin overhead de llamadas extra. Flujo síncrono. Async fallback via tareas_async si >120s. |

---

## 2. CONTRATO I/O

### Input (del gateway)

```typescript
interface MotorRequest {
  // Obligatorios
  input: string;                    // Texto del usuario/interfaz
  perfil_diales: PerfilDiales;      // Diales base del perfil activo
  
  // Opcionales
  codigo_semantico?: string;        // Código semántico del capability_registry
  contexto?: Record<string, any>;   // Contexto inyectado por la interfaz
  lente?: 'salud' | 'sentido' | 'continuidad' | null;  // Lente activa
  request_id?: string;              // Para correlación con gateway
  tenant_id?: string;               // Para metering
}

interface PerfilDiales {
  sustantivizar: number;      // 0.0 - 1.0
  adjetivar: number;
  adverbializar: number;
  preposicionar: number;
  conjuntar: number;
  verbo: number;
  sujeto_predicado: number;
}
```

### Output (al gateway → interfaz)

```typescript
interface MotorResponse {
  // Respuesta semántica neutra (NO personalizada, NO para presentar tal cual)
  respuesta_semantica: string;       // Texto claro, neutro, sin tono
                                     // La interfaz lo adecúa al usuario
  
  // Datos estructurados (para interfaces que quieran renderizar distinto)
  datos: {
    input_transformado: InputTransformado;   // Fusión PIEZAS
    estructura_detectada: EstructuraDetectada; // Fusión ESTRUCTURA
    alertas_cruce: AlertaCruce[];            // Incoherencias detectadas
    confianza_global: number;                // 0.0 - 1.0
  };
  
  // Metadata de ejecución
  metadata: {
    lente_aplicada: string | null;
    diales_efectivos: PerfilDiales;          // Diales tras aplicar lente
    primitivas_ejecutadas: number;           // De 7
    primitivas_fallidas: string[];           // Nombres de las que fallaron
    nivel_degradacion: number;               // 0-4
    verbalizacion_modo: 'template' | 'haiku' | 'fallback';
  };
  
  // Telemetría (para metering del gateway)
  telemetria: {
    latencia_total_ms: number;
    haiku_calls: number;
    coste_estimado_usd: number;
    cuello_botella: string;          // Nombre de la fase más lenta
  };
}
```

**Contrato clave: la interfaz recibe DOS cosas:**
1. `respuesta_semantica` — texto neutro que la interfaz adecúa al usuario con su verbalizador propio y los patrones de comunicación almacenados en su Supabase.
2. `datos` — JSONs estructurados por si la interfaz quiere renderizar dashboards, gráficos, o presentar la información de forma no textual.

---

## 3. FLUJO INTERNO

```
motor-orquestador recibe MotorRequest
       │
       ▼
  ┌─────────────────────────┐
  │ PASO 0: PREPARACIÓN     │  código puro, <5ms
  │ - Validar input         │
  │ - Iniciar traza         │
  │ - Aplicar lente a diales│
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 1: FAN-OUT         │  Promise.allSettled, 7 fetch paralelos
  │ 7 primitivas en paralelo│  ~5-40s según diales
  │ Cada una recibe:        │
  │ { input, dial, contexto}│
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 2: RECOLECCIÓN     │  código puro, <5ms
  │ - Separar ok/fallidos   │
  │ - Registrar telemetría  │
  │   por primitiva         │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 3: FUSIÓN PIEZAS   │  código puro, <5ms
  │ Primitivas 1-4:         │
  │ sustantivizar +         │
  │ adjetivar +             │
  │ adverbializar +         │
  │ preposicionar           │
  │ → input_transformado    │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 4: FUSIÓN ESTRUC   │  código puro, <5ms
  │ Primitivas 5-7:         │
  │ conjuntar +             │
  │ verbo +                 │
  │ sujeto_predicado        │
  │ → estructura_detectada  │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 5: CRUCE           │  código puro, <5ms
  │ input_transformado ×    │
  │ estructura_detectada    │
  │ → alertas_cruce         │
  │ → confianza_global      │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 6: VERBALIZACIÓN   │  1 Haiku via llm-proxy, ~3-5s
  │ PRE: construir prompt   │
  │ HAIKU: verbalizar       │
  │ POST: validar formato   │
  └───────────┬─────────────┘
              │
              ▼
  ┌─────────────────────────┐
  │ PASO 7: CIERRE          │  código puro, <5ms
  │ - Registrar traza       │
  │ - Construir response    │
  │ - Return                │
  └─────────────────────────┘
```

---

## 4. APLICACIÓN DE LENTES (Paso 0)

```typescript
// Las lentes SUBEN diales, nunca los bajan.
// Operación: max(perfil_base[prim], lente_boost[prim])

const LENTES: Record<string, Partial<PerfilDiales>> = {
  salud: {
    adverbializar: 0.8,      // modo_mantener, modo_responder
    adjetivar: 0.7,           // extremos, posición
    sujeto_predicado: 0.8,    // agente, accountability
    preposicionar: 0.7,       // ausencia
  },
  sentido: {
    sustantivizar: 0.8,       // coherencia de etiquetas
    adjetivar: 0.7,           // estructura, comparativa
    adverbializar: 0.7,       // modo_distinguir, modo_copiar
    conjuntar: 0.8,           // conexiones lógicas
  },
  continuidad: {
    adjetivar: 0.7,           // dinámica, sostenimiento
    adverbializar: 0.8,       // modo_repartir, modo_sacar, modo_meter
    sujeto_predicado: 0.7,    // delegación, temporal
    conjuntar: 0.7,           // dependencias
  },
};

function aplicarLente(
  base: PerfilDiales, 
  lente: string | null
): PerfilDiales {
  if (!lente || !LENTES[lente]) return { ...base };
  const boost = LENTES[lente];
  const resultado: PerfilDiales = { ...base };
  for (const [key, val] of Object.entries(boost)) {
    resultado[key] = Math.max(resultado[key], val);
  }
  return resultado;
}
```

---

## 5. FAN-OUT A PRIMITIVAS (Paso 1)

```typescript
const PRIMITIVAS = [
  'primitiva-sustantivizar',
  'primitiva-adjetivar',
  'primitiva-adverbializar',
  'primitiva-preposicionar',
  'primitiva-conjuntar',
  'primitiva-verbo',
  'primitiva-sujeto-predicado',
];

async function fanOutPrimitivas(
  input: string,
  diales: PerfilDiales,
  contexto: Record<string, any>,
  traza: Traza
): Promise<ResultadoPrimitiva[]> {
  const faseStart = Date.now();
  
  const promesas = PRIMITIVAS.map(async (nombre) => {
    const dial = diales[nombreAKey(nombre)];
    const start = Date.now();
    
    try {
      const res = await fetch(
        `${SUPABASE_URL}/functions/v1/${nombre}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${ANON_KEY}`,
          },
          body: JSON.stringify({ input, dial, contexto }),
        }
      );
      
      if (!res.ok) throw new Error(`${nombre}: ${res.status}`);
      const data = await res.json();
      
      return {
        nombre,
        ok: true,
        output: data,
        latencia_ms: Date.now() - start,
        dial_usado: dial,
        angulos_activados: data._telemetria?.angulos_activados ?? null,
        angulos_fallidos: data._telemetria?.angulos_fallidos ?? 0,
        haiku_calls: data._telemetria?.haiku_calls ?? 0,
        coste_usd: data._telemetria?.coste_usd ?? 0,
        confianza: data.confianza ?? 0.5,
      };
    } catch (err) {
      return {
        nombre,
        ok: false,
        output: null,
        latencia_ms: Date.now() - start,
        dial_usado: dial,
        error: err.message,
        angulos_activados: 0,
        angulos_fallidos: 0,
        haiku_calls: 0,
        coste_usd: 0,
        confianza: 0,
      };
    }
  });

  const resultados = await Promise.allSettled(promesas);
  
  // Extraer valores (allSettled nunca rechaza)
  const outputs = resultados.map(r => 
    r.status === 'fulfilled' ? r.value : {
      nombre: 'desconocido', ok: false, output: null,
      latencia_ms: 0, dial_usado: 0, error: 'Promise rejected',
      angulos_activados: 0, angulos_fallidos: 0,
      haiku_calls: 0, coste_usd: 0, confianza: 0,
    }
  );

  // Registrar fase en traza
  traza.fases.push({
    nombre: 'fan_out_primitivas',
    inicio_ms: faseStart - traza.inicio,
    duracion_ms: Date.now() - faseStart,
    primitivas_ok: outputs.filter(o => o.ok).length,
    primitivas_fallidas: outputs.filter(o => !o.ok).map(o => o.nombre),
    cuello_botella_primitiva: outputs
      .filter(o => o.ok)
      .reduce((max, o) => o.latencia_ms > max.latencia_ms ? o : max, 
              { latencia_ms: 0, nombre: 'ninguna' }).nombre,
    haiku_calls_total: outputs.reduce((s, o) => s + o.haiku_calls, 0),
    coste_total_usd: outputs.reduce((s, o) => s + o.coste_usd, 0),
  });

  return outputs;
}
```

---

## 6. FUSIÓN POR CAPAS (Pasos 3-5)

```typescript
// ── PASO 3: FUSIONAR PIEZAS ──
function fusionarPiezas(resultados: ResultadoPrimitiva[]): InputTransformado {
  const sustantivizar = extraerOk(resultados, 'primitiva-sustantivizar');
  const adjetivar = extraerOk(resultados, 'primitiva-adjetivar');
  const adverbializar = extraerOk(resultados, 'primitiva-adverbializar');
  const preposicionar = extraerOk(resultados, 'primitiva-preposicionar');

  return {
    compresion: sustantivizar?.output?.transformacion ?? null,
    posicionamiento: adjetivar?.output?.transformacion ?? null,
    modo_operacion: adverbializar?.output?.transformacion ?? null,
    relaciones: preposicionar?.output?.transformacion ?? null,
    piezas_presentes: [sustantivizar, adjetivar, adverbializar, preposicionar]
      .filter(Boolean).length,
    piezas_faltantes: [sustantivizar, adjetivar, adverbializar, preposicionar]
      .filter(p => !p).map((_, i) => ['sustantivizar','adjetivar','adverbializar','preposicionar'][i]),
  };
}

// ── PASO 4: FUSIONAR ESTRUCTURA ──
function fusionarEstructura(resultados: ResultadoPrimitiva[]): EstructuraDetectada {
  const conjuntar = extraerOk(resultados, 'primitiva-conjuntar');
  const verbo = extraerOk(resultados, 'primitiva-verbo');
  const sujetoPred = extraerOk(resultados, 'primitiva-sujeto-predicado');

  return {
    conexiones: conjuntar?.output?.transformacion ?? null,
    accion_nuclear: verbo?.output?.transformacion ?? null,
    agencia: sujetoPred?.output?.transformacion ?? null,
    estructura_presente: [conjuntar, verbo, sujetoPred].filter(Boolean).length,
    estructura_faltante: [conjuntar, verbo, sujetoPred]
      .filter(p => !p).map((_, i) => ['conjuntar','verbo','sujeto_predicado'][i]),
  };
}

// ── PASO 5: CRUCE ──
function cruzarPiezasEstructura(
  piezas: InputTransformado,
  estructura: EstructuraDetectada
): { alertas: AlertaCruce[], confianza_global: number } {
  const alertas: AlertaCruce[] = [];

  // Cruce 1: Agencia vs Modo
  if (estructura.agencia && piezas.modo_operacion) {
    const agenciaDiluida = estructura.agencia.nivel_agencia < 0.4;
    const modoActivo = piezas.modo_operacion.explicitud > 0.6;
    if (agenciaDiluida && modoActivo) {
      alertas.push({
        tipo: 'contradiccion',
        origen: 'sujeto_predicado × adverbializar',
        descripcion: 'Modo activo declarado pero agencia diluida — ¿quién ejecuta?',
        gravedad: 'alta',
      });
    }
  }

  // Cruce 2: Compresión vs Conexiones
  if (piezas.compresion && estructura.conexiones) {
    const etiquetaGeneral = piezas.compresion.nivel_especificidad < 0.3;
    const conexionesEspecificas = estructura.conexiones.especificidad > 0.7;
    if (etiquetaGeneral && conexionesEspecificas) {
      alertas.push({
        tipo: 'tension',
        origen: 'sustantivizar × conjuntar',
        descripcion: 'Concepto genérico con conexiones específicas — puede haber ambigüedad',
        gravedad: 'media',
      });
    }
  }

  // Cruce 3: Nivel lógico vs Acción
  if (piezas.relaciones && estructura.accion_nuclear) {
    const nivelAlto = piezas.relaciones.nivel_logico_dominante >= 4;
    const accionOperativa = estructura.accion_nuclear.es_operativa;
    if (nivelAlto && accionOperativa) {
      alertas.push({
        tipo: 'colapso_nivel',
        origen: 'preposicionar × verbo',
        descripcion: 'Pensamiento de nivel meta con acción operativa — posible colapso de niveles',
        gravedad: 'alta',
      });
    }
  }

  // Confianza global = media ponderada de confianzas individuales
  const confianzas = [
    piezas.compresion?.confianza,
    piezas.posicionamiento?.confianza,
    piezas.modo_operacion?.confianza,
    piezas.relaciones?.confianza,
    estructura.conexiones?.confianza,
    estructura.accion_nuclear?.confianza,
    estructura.agencia?.confianza,
  ].filter(c => c != null) as number[];
  
  const confianza_global = confianzas.length > 0 
    ? confianzas.reduce((s, c) => s + c, 0) / confianzas.length 
    : 0;

  return { alertas, confianza_global };
}
```

---

## 7. VERBALIZACIÓN SEMÁNTICA NEUTRA (Paso 6)

El motor NO produce respuesta personalizada. Produce texto semántico claro y neutro.
La interfaz adecúa al usuario con sus patrones de comunicación.

### Modo 1: Templates (código puro, $0, ~80% de pasadas)

```typescript
function verbalizarTemplate(
  piezas: InputTransformado,
  estructura: EstructuraDetectada,
  alertas: AlertaCruce[],
): string {
  const partes: string[] = [];

  // Compresión
  if (piezas.compresion) {
    const nivel = piezas.compresion.nivel_especificidad;
    if (nivel < 0.3) partes.push(`El concepto central es genérico (especificidad ${(nivel*100).toFixed(0)}%) — puede estar demasiado abstracto.`);
    else if (nivel > 0.7) partes.push(`El concepto está bien especificado (${(nivel*100).toFixed(0)}%).`);
    else partes.push(`Concepto con especificidad media (${(nivel*100).toFixed(0)}%).`);
  }

  // Agencia
  if (estructura.agencia) {
    const ag = estructura.agencia.nivel_agencia;
    if (ag < 0.4) partes.push(`Agencia diluida (${(ag*100).toFixed(0)}%) — no queda claro quién ejecuta.`);
    else if (ag > 0.7) partes.push(`Agencia clara (${(ag*100).toFixed(0)}%).`);
    if (estructura.agencia.alertas_fantasma?.length > 0) {
      partes.push(`Agencia fantasma detectada: ${estructura.agencia.alertas_fantasma.join(', ')}.`);
    }
  }

  // Acción nuclear
  if (estructura.accion_nuclear?.verbo) {
    partes.push(`Acción nuclear: ${estructura.accion_nuclear.verbo}.`);
  }

  // Modo de operación
  if (piezas.modo_operacion) {
    const expl = piezas.modo_operacion.explicitud;
    if (expl < 0.3) partes.push(`El modo de operar está implícito — conviene explicitarlo.`);
  }

  // Relaciones / niveles lógicos
  if (piezas.relaciones?.colapso_detectado) {
    partes.push(`Colapso de nivel lógico: ${piezas.relaciones.descripcion_colapso}.`);
  }

  // Alertas de cruce
  if (alertas.length > 0) {
    const altas = alertas.filter(a => a.gravedad === 'alta');
    if (altas.length > 0) {
      partes.push(`Tensiones: ${altas.map(a => a.descripcion).join('. ')}.`);
    }
  }

  return partes.join(' ');
}
```

### Modo 2: Haiku (para cruces complejos, ~20% de pasadas)

Se activa cuando:
- alertas_cruce > 2 (muchas tensiones, template no las sintetiza bien)
- primitivas con outputs contradictorios entre sí
- confianza_global < 0.4 (mucha ambigüedad, mejor que un LLM sintetice)

```typescript
function necesitaHaiku(
  alertas: AlertaCruce[],
  confianza_global: number,
  primitivas_ok: number,
): boolean {
  if (alertas.length > 2) return true;
  if (confianza_global < 0.4) return true;
  if (alertas.some(a => a.tipo === 'contradiccion' && a.gravedad === 'alta')) return true;
  return false;
}

const SYSTEM_PROMPT_MOTOR_VERBALIZADOR = `Eres el verbalizador semántico del motor OMNI-MIND.
Recibes el análisis integrado de 7 primitivas cognitivas.
Tu trabajo: producir UN texto semántico claro y NEUTRO.

REGLAS:
- Máximo 6 frases
- Sin tono personalizado — neutro y factual
- Incluir datos concretos del análisis (scores, niveles, alertas)
- Las tensiones son lo más importante — siempre mencionarlas
- NO mencionar las primitivas por nombre
- Responder en español
- SOLO texto plano, sin JSON, sin markdown
- Este texto será adecuado después por la interfaz — tú aportas SEMÁNTICA, no estilo`;
```

### Modo 3: Fallback mecánico (cuando Haiku falla)

```typescript
function fallbackMecanico(
  piezas: InputTransformado,
  estructura: EstructuraDetectada,
  alertas: AlertaCruce[]
): string {
  const items: string[] = [];
  if (piezas.compresion?.etiqueta) items.push(`Concepto: ${piezas.compresion.etiqueta}`);
  if (estructura.accion_nuclear?.verbo) items.push(`Acción: ${estructura.accion_nuclear.verbo}`);
  if (estructura.agencia) items.push(`Agencia: ${(estructura.agencia.nivel_agencia*100).toFixed(0)}%`);
  if (alertas.length > 0) items.push(`Tensiones: ${alertas.length}`);
  items.push('[Respuesta mecánica — síntesis no disponible]');
  return items.join('. ');
}
```

### Flujo de decisión

```
          ¿necesitaHaiku?
           /          \
         NO            SÍ
         |              |
    template()     Haiku llm-proxy
    código puro       |
    $0              ¿ok?
         \         /     \
          \      SÍ       NO
           \    |          |
            output     fallbackMecanico()
```

### Responsabilidad de la INTERFAZ (fuera del motor)

```
INTERFAZ recibe respuesta_semantica del motor:
  "Agencia diluida (35%). No queda claro quién ejecuta. 
   Colapso de nivel: pensamiento meta con acción operativa.
   Tensión: modo activo declarado pero sin agente responsable."

INTERFAZ adecúa con patrones del usuario almacenados en SU Supabase:
  
  Para Jesús (directo, sin rodeos, confronta):
    "¿Quién ejecuta esto? Dices 'hay que hacer' pero no hay nadie.
     Y estás pensando en estrategia mientras la acción es operativa 
     — elige un nivel."
  
  Para cliente X (progresivo, empático):
    "Noto que la idea tiene mucha fuerza pero falta un paso: 
     definir quién se encarga. ¿Tú, alguien de tu equipo, 
     o es algo que necesitas delegar?"

La adecuación es RESPONSABILIDAD DE LA INTERFAZ.
El motor no sabe quién es el usuario ni cómo prefiere recibir información.
```
```

---

## 8. TELEMETRÍA INTEGRADA

### 8.1 Traza del orquestador (registra el ciclo completo)

```typescript
interface Traza {
  request_id: string;
  tenant_id: string | null;
  inicio: number;              // Date.now()
  fases: FaseTraza[];
}

interface FaseTraza {
  nombre: string;              // 'preparacion' | 'fan_out_primitivas' | 'fusion_piezas' | 'fusion_estructura' | 'cruce' | 'verbalizacion' | 'cierre'
  inicio_ms: number;           // ms desde inicio de traza
  duracion_ms: number;
  // Campos variables por fase:
  [key: string]: any;
}

// ── AL FINAL DEL CICLO ──
await registrarMétrica(supabase, {
  enjambre: 'motor',
  evento: 'motor_ciclo_completo',
  agente: 'motor-orquestador',
  latencia_ms: Date.now() - traza.inicio,
  exitoso: true,
  data: {
    request_id: traza.request_id,
    tenant_id: traza.tenant_id,
    
    // ── INPUT ──
    input_largo: input.length,
    input_tokens_estimado: Math.ceil(input.length / 4),
    
    // ── LENTE ──
    lente_aplicada: lente ?? 'ninguna',
    diales_base: perfil_diales,
    diales_efectivos: dialesEfectivos,
    diales_modificados: Object.keys(perfil_diales).filter(
      k => perfil_diales[k] !== dialesEfectivos[k]
    ),
    
    // ── PRIMITIVAS ──
    primitivas_ejecutadas: resultados.filter(r => r.ok).length,
    primitivas_fallidas: resultados.filter(r => !r.ok).map(r => r.nombre),
    primitivas_detalle: resultados.map(r => ({
      nombre: r.nombre,
      ok: r.ok,
      dial: r.dial_usado,
      latencia_ms: r.latencia_ms,
      angulos_activados: r.angulos_activados,
      angulos_fallidos: r.angulos_fallidos,
      haiku_calls: r.haiku_calls,
      coste_usd: r.coste_usd,
      confianza: r.confianza,
      error: r.error ?? null,
    })),
    
    // ── FUSIÓN ──
    piezas_presentes: piezas.piezas_presentes,
    estructura_presente: estructura.estructura_presente,
    alertas_cruce: alertas.length,
    alertas_tipos: alertas.map(a => a.tipo),
    confianza_global: confianza_global,
    
    // ── VERBALIZACIÓN ──
    verbalizacion_modo: 'template' | 'haiku' | 'fallback',
    verbalizacion_exitosa: verbExitosa,
    verbalizacion_latencia_ms: verbLatencia,
    verbalizacion_tokens_out: verbModo === 'haiku' ? verbTokens : 0,
    verbalizacion_coste_usd: verbModo === 'haiku' ? verbCoste : 0,
    verbalizacion_haiku_trigger: verbModo === 'haiku' 
      ? necesitaHaikuRazon  // 'alertas>2' | 'confianza_baja' | 'contradiccion_alta'
      : null,
    respuesta_largo: respuesta.length,
    
    // ── TIMING ──
    fases: traza.fases,
    cuello_botella: traza.fases.reduce((max, f) => 
      f.duracion_ms > max.duracion_ms ? f : max
    ).nombre,
    latencia_fan_out_ms: traza.fases.find(f => f.nombre === 'fan_out_primitivas')?.duracion_ms ?? 0,
    latencia_fusion_ms: (
      (traza.fases.find(f => f.nombre === 'fusion_piezas')?.duracion_ms ?? 0) +
      (traza.fases.find(f => f.nombre === 'fusion_estructura')?.duracion_ms ?? 0) +
      (traza.fases.find(f => f.nombre === 'cruce')?.duracion_ms ?? 0)
    ),
    latencia_verbalizacion_ms: traza.fases.find(f => f.nombre === 'verbalizacion')?.duracion_ms ?? 0,
    
    // ── COSTE ──
    haiku_calls_total: resultados.reduce((s, r) => s + r.haiku_calls, 0) + (verbModo === 'haiku' ? 1 : 0),
    coste_primitivas_usd: resultados.reduce((s, r) => s + r.coste_usd, 0),
    coste_verbalizacion_usd: verbModo === 'haiku' ? verbCoste : 0,
    coste_total_usd: resultados.reduce((s, r) => s + r.coste_usd, 0) + (verbModo === 'haiku' ? verbCoste : 0),
  }
});
```

### 8.2 Telemetría que CADA PRIMITIVA debe exponer

Cada primitiva-v2 ya es un mini-enjambre. Para que la telemetría del orquestador funcione, cada primitiva debe devolver `_telemetria` en su response:

```typescript
// Contrato: cada primitiva incluye esto en su JSON de respuesta
interface PrimitivaTelemetria {
  _telemetria: {
    angulos_activados: number;       // Cuántos ángulos corrieron
    angulos_totales: number;         // Cuántos ángulos existen para esta primitiva
    angulos_fallidos: number;        // Cuántos fallaron (Haiku timeout, JSON inválido)
    angulos_detalle: {
      nombre: string;
      ejecutado: boolean;
      latencia_ms: number;
      haiku_ok: boolean;
      json_necesito_limpieza: boolean;
    }[];
    haiku_calls: number;             // Total llamadas a Haiku
    integrador_latencia_ms: number;  // Latencia del integrador código puro
    coste_usd: number;               // Coste total de esta primitiva
    dial_recibido: number;           // El dial que recibió
    fast_path: boolean;              // true si dial=0 y solo corrió código puro
  };
}
```

### 8.3 Telemetría de degradación

```typescript
// Si alguna primitiva falla, registrar evento de degradación
if (resultados.some(r => !r.ok)) {
  await registrarMétrica(supabase, {
    enjambre: 'motor',
    evento: 'motor_degradacion',
    agente: 'motor-orquestador',
    latencia_ms: Date.now() - traza.inicio,
    exitoso: true, // el motor sí respondió, solo degradado
    data: {
      request_id: traza.request_id,
      nivel_degradacion: calcularNivelDegradacion(resultados),
      // Nivel 0: todas ok
      // Nivel 1: 1-2 fallidas (opera con las que hay)
      // Nivel 2: 3-4 fallidas (respuesta parcial)
      // Nivel 3: 5+ fallidas (respuesta mínima)
      // Nivel 4: verbalizador también falló (fallback mecánico)
      primitivas_fallidas: resultados.filter(r => !r.ok).map(r => ({
        nombre: r.nombre,
        error: r.error,
        latencia_ms: r.latencia_ms,
      })),
      fallback_mecanico: useFallback,
    }
  });
}
```

### 8.4 Lo que el addendum de telemetría YA cubre y se reutiliza

```
✅ Sección 1 (llm-proxy): Cada Haiku de cada ángulo de cada primitiva
   pasa por llm-proxy → telemetría de LLM ya cubierta automáticamente.
   Incluye: tokens, latencia, retry, circuit_breaker, stop_reason.
   También cubre el Haiku del verbalizador cuando se activa (~20% de pasadas).

✅ Sección 2 (template agente): Cada primitiva es una Edge Function
   que ya sigue el template → telemetría de agente ya cubierta.
   Incluye: marcas_leidas, bytes_output, json_valido, dependencias.

⚠️  Sección 3 (orquestador): Estaba diseñada para orquestador-chief.
   ESTA SPEC REEMPLAZA la sección 3 para el motor-orquestador.
   El orquestador-chief mantiene su telemetría propia.

✅ Sección 5 (calidad output): Aplica al verbalizador semántico.
   Métricas de calidad: tiene_dato_concreto, tiene_tension, tiene_agencia.
   Se registra igual independientemente del modo (template/haiku/fallback).

❌ Secciones 4, 6, 7, 8+: Son de Chief/interfaz. No aplican al motor.
   NOTA: La verbalización personalizada al usuario es responsabilidad 
   de la interfaz y tendrá su propia telemetría en el Supabase de 
   la interfaz (patrones de adecuación, engagement, tono).
```

---

## 9. GRACEFUL DEGRADATION

```
NIVEL 0 — Todo ok:
  7 primitivas + fusión + verbalización semántica → respuesta neutra completa
  Interfaz adecúa al usuario.
  
NIVEL 1 — 1-2 primitivas fallan:
  5-6 primitivas + fusión parcial + verbalización con menos dimensiones
  → Flag en metadata: primitivas_fallidas
  → Interfaz adecúa normalmente (menos datos pero mismo flujo)
  
NIVEL 2 — 3-4 primitivas fallan:
  3-4 primitivas + fusión limitada + verbalización parcial
  → Flag: nivel_degradacion = 2
  → Interfaz puede añadir disclaimer: "Análisis parcial"
  
NIVEL 3 — 5+ primitivas fallan:
  1-2 primitivas + template mínimo
  → Respuesta con datos disponibles
  
NIVEL 4 — Todo falla:
  → Fallback mecánico: datos crudos formateados
  → "Concepto: X. Acción: Y. Tensiones: Z. [Respuesta mecánica]"
  → Interfaz presenta como pueda
  
NUNCA hay nivel 5 (sin respuesta).
Motor SIEMPRE devuelve algo. La calidad degrada, no la disponibilidad.
```

---

## 10. ESTIMACIONES

### Latencia por dial

| Dial | Haiku/primitiva | Paralelo | + Fusión | + Verbalización | Total |
|------|----------------|----------|----------|-----------------|-------|
| 0.0 | 0 (fast-path) | ~50ms | ~5ms | ~4s | ~4s |
| 0.2 | ~2 | ~5s | ~5ms | ~4s | ~9s |
| 0.4 | ~4 | ~12s | ~5ms | ~4s | ~16s |
| 0.6 | ~7 | ~20s | ~5ms | ~4s | ~24s |
| 0.8 | ~10 | ~30s | ~5ms | ~4s | ~34s |
| 1.0 | ~14-18 | ~40s | ~5ms | ~4s | ~44s |

Todos caben en 150s. Margen amplio incluso a dial 1.0.

### Coste por pasada

| Dial | Haiku totales | Coste primitivas | + Verbalizador | Total/pasada | Mensual (6/día) |
|------|--------------|-----------------|----------------|-------------|-----------------|
| 0.0 | 0 | $0 | $0 (template) | $0 | $0 |
| 0.2 | ~14 | $0.014 | $0 (~80% template) | $0.014 | $2.52 |
| 0.6 | ~70 | $0.070 | $0.0002 (media) | $0.070 | $12.60 |
| 1.0 | ~144 | $0.144 | $0.0002 (media) | $0.144 | $25.92 |

**Nota:** El verbalizador Haiku solo se activa ~20% de las veces (cruces complejos).
Coste medio del verbalizador = $0.001 × 0.2 = $0.0002/pasada.
La verbalización personalizada para el usuario es coste de la INTERFAZ, no del motor.

---

## 11. ARCHIVOS A CREAR

```
NUEVOS:
  supabase/functions/motor-orquestador/index.ts    — Edge Function principal
  supabase/functions/_shared/motor/tipos.ts        — Interfaces MotorRequest, MotorResponse, etc.
  supabase/functions/_shared/motor/lentes.ts       — LENTES config + aplicarLente()
  supabase/functions/_shared/motor/fusion.ts       — fusionarPiezas, fusionarEstructura, cruzar
  supabase/functions/_shared/motor/verbalizador.ts — verbalizar, prompts, fallback
  supabase/functions/_shared/motor/telemetria.ts   — Traza, registrar, degradación
  supabase/functions/_shared/motor/index.ts        — re-export
  tests/motor-orquestador.test.ts                  — Contract tests

MODIFICAR:
  □ Cada primitiva-v2 → añadir _telemetria al response
  □ gateway → añadir ruta a motor-orquestador
  □ capability_registry → registrar perfiles de lentes

MIGRACIÓN:
  □ ALTER CHECK marcas_estigmergicas.tipo → añadir 'motor_resultado' si se necesita marca
  □ INSERT estado_agentes → motor-orquestador, motor-verbalizador
  □ INSERT registro_arquitectura → motor-orquestador (edge_fn), motor/* (módulo)
```

---

## 12. DEPENDENCIAS PARA IMPLEMENTAR

```
REQUIERE ANTES:
  ✅ Gateway API (existe)
  ✅ llm-proxy (existe)
  ✅ registrarMétrica (existe)
  ✅ primitiva-sustantivizar (deployed)
  ✅ primitiva-sujeto-predicado (deployed)
  □ primitiva-adjetivar v2 (pendiente refactor + deploy)
  □ primitiva-adverbializar (pendiente deploy)
  □ primitiva-preposicionar (pendiente deploy)
  □ primitiva-conjuntar (pendiente deploy)
  □ primitiva-verbo (pendiente deploy)

ORDEN:
  1. Code deploya las 5 primitivas pendientes
  2. Se añade _telemetria a cada primitiva
  3. Se implementa motor-orquestador
  4. Se conecta al gateway
  5. Test E2E
```

---

**FIN SPEC MOTOR-ORQUESTADOR v1**



============================================================
## OMNI-MIND/01_FRAMEWORK/00_ARQUITECTURA.md
============================================================

# ARQUITECTURA DE BIBLIOTECA DE ESTRUCTURAS ABSTRACTAS

**Ubicación:** `/06_LIBRARY/00_ARQUITECTURA.md`  
**Estado:** CR1 (Cerrado - Fundacional)  
**Versión:** 1.0  
**Fecha:** 2026-02-07

---

## NATURALEZA DE ESTE DOCUMENTO

Este documento define la **arquitectura permanente** de la Biblioteca de Estructuras Abstractas.

**NO es opcional.**  
**NO es aspiracional.**  
Es la **regla de estructura** para toda adición futura.

**Actualiza y gobierna:** Cualquier contenido de biblioteca presente y futuro.

---

## PROPÓSITO DE LA BIBLIOTECA

La biblioteca existe para:

1. **CAPTURAR** invariantes de campos diversos (Sistemas, Lógica, Física, etc.)
2. **SEPARAR** sintaxis (estructura) de semántica (contenido específico)
3. **REUTILIZAR** sintaxis en nuevos territorios (transferencia cross-domain)
4. **VINCULAR** invariantes de campos diferentes (configuraciones potentes)
5. **ESCALAR** sin límite (arquitectura modular)

**Valor fundamental:**  
Acelerar diseño de sistemas/mapas mediante reutilización de estructuras probadas.

---

## PRINCIPIO OPERATIVO

**"Sintaxis transferible, semántica campo-específica"**

- **SINTAXIS** = Reglas de vinculación entre elementos (estructura formal)
- **SEMÁNTICA** = Significado específico en cada campo (contenido)

**Mecanismo:**

```
Invariante en campo A (sintaxis + semántica A)
    ↓
Extraer sintaxis (separar de semántica A)
    ↓
Aplicar sintaxis con semántica B (nuevo campo)
    ↓
Nuevo mapa en territorio B
```

**Validación:** ¿Aumenta control sobre territorio específico?

---

## ESTRUCTURA DE 3 NIVELES

```
/06_LIBRARY/
├── 00_INDEX_BIBLIOTECA.md          ← Índice maestro navegable
├── 00_ARQUITECTURA.md              ← Este documento (CR1)
│
├── 01_CAMPOS/                       ← Campos completos (contexto)
│   ├── SISTEMAS.md
│   ├── CIBERNETICA.md
│   ├── JUEGOS.md
│   ├── LOGICA.md
│   ├── TERMODINAMICA.md
│   └── [futuros campos...]
│
├── 02_INVARIANTES/                  ← Invariantes individuales (granular)
│   ├── Emergencia.md
│   ├── Homeostasis.md
│   ├── Retroalimentacion.md
│   ├── Equilibrio_Nash.md
│   ├── Entropia.md
│   └── [1 archivo por invariante]
│
└── 03_VINCULACIONES/                ← Configuraciones cross-domain
    ├── Homeostasis_Retroalimentacion.md
    ├── Entropia_Dilema_Prisionero.md
    ├── Emergencia_Sinergia.md
    └── [vinculaciones descubiertas]
```

---

## NIVEL 1: CAMPOS COMPLETOS

### **Ubicación:** `/01_CAMPOS/[NOMBRE_CAMPO].md`

### **Propósito:**

- Consulta rápida de campo completo
- Contexto histórico del campo
- Ver invariantes en su entorno original
- Referencia para validación

### **Contenido obligatorio:**

```markdown
# CAMPO: [Nombre]

**Origen:** [Autor/Época]
**Territorio original:** [Dominio de aplicación]

---

## INVARIANTE 1: [Nombre]

### CAPA 1: SINTAXIS
[Estructura formal]

### CAPA 2: SEMÁNTICA ORIGINAL
[Significado en campo origen]

### CAPA 3: SEMÁNTICA ABSTRACTA
[Significado universal transferible]

---

[Repetir para invariantes 2-5]

---

## RESUMEN CAMPO

**N invariantes extraídos:**
[Lista]

**Todos tienen:**
- ✅ Sintaxis clara
- ✅ Semántica original
- ✅ Semántica abstracta
- ✅ Criterio validación cross-domain
```

### **Reglas:**

- 1 archivo por campo
- Mínimo 3 invariantes por campo
- Máximo 7 invariantes por campo (evitar saturación)
- Si campo tiene >7 invariantes potentes → dividir en subcampos

### **Naming convention:**

- `NOMBRE_CAMPO.md` (MAYÚSCULAS, guiones bajos)
- Ejemplos: `SISTEMAS.md`, `CIBERNETICA.md`, `COMPLEJIDAD.md`

---

## NIVEL 2: INVARIANTES INDIVIDUALES

### **Ubicación:** `/02_INVARIANTES/[Nombre_Invariante].md`

### **Propósito:**

- Consulta individual de invariante
- Granularidad máxima (1 archivo = 1 concepto)
- Ver aplicaciones cross-domain
- Links a vinculaciones relacionadas

### **Contenido obligatorio:**

```markdown
# INVARIANTE: [Nombre]

## METADATOS
- **Campo(s) origen:** [Lista de campos]
- **Relacionado con:** [Otros invariantes relacionados]
- **Tags:** #tag1 #tag2 #tag3

---

## CAPA 1: SINTAXIS

**Estructura formal:**
```

[Notación formal/pseudo-código/diagrama]

```

**Reglas de vinculación:**
- [Regla 1]
- [Regla 2]
- [Regla 3]

**Relaciones internas:**
- [Elemento A se relaciona con B cómo]

---

## CAPA 2: SEMÁNTICA ORIGINAL (Campo: [X])

**Significado específico:**
[Qué significa en campo origen]

**Ejemplos del campo:**
- Ejemplo 1
- Ejemplo 2
- Ejemplo 3

**Validación original:**
[Cómo se verifica en campo origen]

---

## CAPA 3: SEMÁNTICA ABSTRACTA (Universal)

**Significado universal:**
[Definición despojada de contenido específico]

**Condiciones de transferencia:**
- Condición 1
- Condición 2
- Condición 3

**Territorios aplicables:**
- Territorio 1: [ejemplo]
- Territorio 2: [ejemplo]
- Territorio 3: [ejemplo]
- Territorio 4: [ejemplo]

**Criterio validación cross-domain:**
[Pregunta(s) para verificar si invariante aplica a nuevo caso]

---

## APLICACIONES DOCUMENTADAS

### [Territorio 1]
**Contexto:** [situación específica]  
**Aplicación:** [cómo se usa invariante]  
**Resultado:** [qué control aumenta]

### [Territorio 2]
[repetir estructura]

---

## VINCULACIONES CONOCIDAS

→ Ver: [Invariante_A + Este](../03_VINCULACIONES/InvarianteA_Este.md)  
→ Ver: [Este + Invariante_B](../03_VINCULACIONES/Este_InvarianteB.md)  
→ Ver: [Configuración_Triple](../03_VINCULACIONES/A_B_Este.md)

---

## REFERENCIAS
- Campo origen: [link a /01_CAMPOS/X.md]
- Literatura: [papers/libros si aplica]
```

### **Reglas:**

- 1 archivo por invariante
- Nombre en CamelCase: `Emergencia.md`, `EquilibrioNash.md`
- Tags obligatorios (mínimo 3)
- Mínimo 3 aplicaciones cross-domain documentadas
- Links bidireccionales con vinculaciones

### **Naming convention:**

- `Nombre_Invariante.md` (CamelCase con guiones bajos si compuesto)
- Ejemplos: `Emergencia.md`, `Equilibrio_Nash.md`, `Variedad_Requisita.md`

---

## NIVEL 3: VINCULACIONES CROSS-DOMAIN

### **Ubicación:** `/03_VINCULACIONES/[Inv1]_[Inv2]_[InvN].md`

### **Propósito:**

- Documentar configuraciones de 2+ invariantes
- Capturar propiedad emergente de vinculación
- Aplicaciones concretas de configuración
- **RECOMBINACIÓN:** crear mapas nuevos

### **Contenido obligatorio:**

```markdown
# VINCULACIÓN: [Invariante 1] + [Invariante 2] + [...]

## INVARIANTES VINCULADOS

1. **[Invariante 1]** ([Campo origen])
   - Sintaxis: [resumen 1-2 líneas]
   
2. **[Invariante 2]** ([Campo origen])
   - Sintaxis: [resumen 1-2 líneas]

[Repetir si hay más]

---

## MECANISMO DE VINCULACIÓN

**Cómo se conectan:**
[Explicación de cómo sintaxis de Inv1 se conecta con Inv2]

**Punto de acople:**
[Elemento específico donde se vinculan]

**Ejemplo formal:**
```

[Notación mostrando vinculación]

```

---

## PROPIEDAD EMERGENTE

**Qué surge de la vinculación:**
[Propiedad/capacidad que NO está en ningún invariante individual]

**Por qué emerge:**
[Mecanismo que genera emergencia]

**Verificación:**
[Cómo validar que propiedad emergió]

---

## APLICACIONES

### [Territorio 1]
**Contexto:** [situación específica]  
**Invariante 1 aporta:** [qué función cumple]  
**Invariante 2 aporta:** [qué función cumple]  
**Resultado emergente:** [qué se logra con vinculación]  
**Control aumentado:** [qué mapa/capacidad se genera]

### [Territorio 2]
[repetir estructura]

### [Territorio 3]
[repetir estructura]

---

## CRITERIO DE VALIDACIÓN

**Para verificar si vinculación aplica a caso X:**

1. ¿Se cumplen condiciones de Invariante 1? [checklist]
2. ¿Se cumplen condiciones de Invariante 2? [checklist]
3. ¿Existe punto de acople entre ambos? [verificar]
4. ¿Emerge propiedad esperada? [validar]

Si 1-4 = SÍ → Vinculación aplica

---

## CONFIGURACIONES EXTENDIDAS

**Añadir [Invariante 3]:**
- Qué aporta: [función]
- Cómo se vincula: [mecanismo]
- Nueva propiedad emergente: [qué surge]
- Aplicación: [ejemplo]

**Añadir [Invariante 4]:**
[repetir]

---

## ADVERTENCIAS

**Esta vinculación NO aplica cuando:**
- [Condición límite 1]
- [Condición límite 2]

**Riesgo de mal uso:**
- [Antipatrón común]
- [Confusión típica]

---

## REFERENCIAS
- Invariante 1: [link a /02_INVARIANTES/Inv1.md]
- Invariante 2: [link a /02_INVARIANTES/Inv2.md]
- Literatura: [si aplica]
```

### **Reglas:**

- Mínimo 2 invariantes vinculados
- Máximo 4 invariantes en una vinculación (más allá → complejidad excesiva)
- Mínimo 3 aplicaciones documentadas
- Propiedad emergente DEBE estar explícita
- Criterio de validación DEBE ser operativo

### **Naming convention:**

- `Inv1_Inv2.md` para 2 invariantes
- `Inv1_Inv2_Inv3.md` para 3 invariantes
- Orden alfabético de invariantes
- Ejemplos: `Emergencia_Sinergia.md`, `Homeostasis_Retroalimentacion_Control.md`

---

## ÍNDICE MAESTRO

### **Ubicación:** `/00_INDEX_BIBLIOTECA.md`

### **Propósito:**

- Punto de entrada único a biblioteca
- Navegación por campo/invariante/aplicación/tag
- Estado actual de biblioteca
- Guía de uso

### **Contenido obligatorio:**

```markdown
# BIBLIOTECA DE ESTRUCTURAS ABSTRACTAS

**Última actualización:** [Fecha]  
**Total campos:** [N]  
**Total invariantes:** [M]  
**Total vinculaciones:** [K]

---

## NAVEGACIÓN RÁPIDA

### Por Campo
- [Sistemas](01_CAMPOS/SISTEMAS.md) - 5 invariantes
- [Cibernética](01_CAMPOS/CIBERNETICA.md) - 5 invariantes
- [Juegos](01_CAMPOS/JUEGOS.md) - 5 invariantes
- [Lógica](01_CAMPOS/LOGICA.md) - 5 invariantes
- [Termodinámica](01_CAMPOS/TERMODINAMICA.md) - 5 invariantes

### Por Invariante (Alfabético)
- [Caja Negra](02_INVARIANTES/Caja_Negra.md)
- [Conservación](02_INVARIANTES/Conservacion.md)
- [Contradicción](02_INVARIANTES/Contradiccion.md)
- [...]

### Por Tag
- **#autorregulacion:** Homeostasis, Retroalimentación, Control
- **#equilibrio:** Equilibrio (Termo), Equilibrio Nash, Homeostasis
- **#flujo:** Gradiente, Información, Retroalimentación
- **#optimizacion:** Nash, Estrategia Dominante, Equilibrio
- **#emergencia:** Emergencia, Sinergia
- [...]

### Por Aplicación
- **Organizaciones:** [lista de invariantes aplicables]
- **Personal/Hábitos:** [lista]
- **Diseño de sistemas:** [lista]
- **Relaciones:** [lista]
- [...]

---

## CAMPOS

[Lista completa con descripción breve]

---

## INVARIANTES

[Lista completa con tags y campo origen]

---

## VINCULACIONES DOCUMENTADAS

[Lista con descripción breve de cada vinculación]

---

## CÓMO USAR ESTA BIBLIOTECA

### Caso 1: Tengo problema nuevo en territorio X
1. Buscar en índice por tag o aplicación
2. Leer invariante(s) relevante(s)
3. Verificar condiciones de transferencia
4. Adaptar sintaxis a territorio X
5. Validar emergencia

### Caso 2: Quiero entender campo Y
1. Ir a `/01_CAMPOS/Y.md`
2. Leer contexto histórico
3. Estudiar invariantes en orden
4. Ver aplicaciones originales

### Caso 3: Descubrí nueva vinculación
1. Identificar invariantes a vincular
2. Usar template de `/03_VINCULACIONES/`
3. Documentar mecanismo + emergencia
4. Aplicar a 2-3 territorios
5. Actualizar este índice

### Caso 4: Quiero añadir campo nuevo
1. Usar template de `/01_CAMPOS/`
2. Extraer 3-7 invariantes con 3 capas
3. Crear archivos en `/02_INVARIANTES/`
4. Identificar vinculaciones con existentes
5. Actualizar este índice

---

## PRÓXIMOS CAMPOS (Roadmap)

- [ ] Economía (4-5 invariantes)
- [ ] Complejidad (5 invariantes)
- [ ] Evolución (5 invariantes)
- [ ] Redes (4 invariantes)
- [ ] Información Cuántica (3-4 invariantes)

---

## ARQUITECTURA

Ver: [Arquitectura de Biblioteca](00_ARQUITECTURA.md)

- Estructura de 3 niveles
- Reglas de naming
- Templates obligatorios
- Proceso de adición
```

### **Reglas:**

- Actualizar con CADA adición (campo/invariante/vinculación)
- Mantener contadores actualizados
- Tags deben ser consistentes
- Links deben ser válidos

---

## TEMPLATES OBLIGATORIOS

Cada nivel tiene template fijo (ver secciones anteriores).

**NO se permite:**

- Crear archivos fuera de estructura 3 niveles
- Inventar formatos propios
- Omitir secciones obligatorias
- Naming diferente al especificado

**Excepción:** Este documento (arquitectura) y el índice.

---

## PROCESO DE ADICIÓN

### **AÑADIR NUEVO CAMPO:**

**Pasos obligatorios:**

1. **Crear archivo campo:**
    
    - Ubicación: `/01_CAMPOS/NUEVO_CAMPO.md`
    - Template: Ver Nivel 1
    - Contenido: 3-7 invariantes con 3 capas cada uno
2. **Crear archivos invariantes:**
    
    - Ubicación: `/02_INVARIANTES/[Nombre].md` (uno por invariante)
    - Template: Ver Nivel 2
    - Contenido: Metadatos + 3 capas + aplicaciones + links
3. **Actualizar índice:**
    
    - Añadir campo a lista
    - Añadir invariantes a alfabético
    - Añadir tags nuevos si aplica
    - Actualizar contadores
4. **Identificar vinculaciones:**
    
    - Buscar invariantes existentes relacionables
    - Crear archivos en `/03_VINCULACIONES/` si aplica
    - Documentar emergencias
5. **Validación:**
    
    - ¿Todos los invariantes tienen 3 capas completas?
    - ¿Todos los archivos siguen templates?
    - ¿Índice actualizado?
    - ¿Links bidireccionales funcionan?

**Tiempo estimado:** 1-2 horas por campo (5 invariantes)

---

### **AÑADIR NUEVA VINCULACIÓN:**

**Pasos obligatorios:**

1. **Identificar invariantes:**
    
    - Mínimo 2, máximo 4
    - De campos diferentes (preferible)
    - Con punto de acople claro
2. **Crear archivo vinculación:**
    
    - Ubicación: `/03_VINCULACIONES/Inv1_Inv2.md`
    - Template: Ver Nivel 3
    - Contenido: Mecanismo + emergencia + aplicaciones
3. **Actualizar invariantes:**
    
    - Añadir link a vinculación en cada `/02_INVARIANTES/Inv.md`
    - Sección "Vinculaciones conocidas"
4. **Actualizar índice:**
    
    - Añadir a lista de vinculaciones
    - Actualizar contador
5. **Validación:**
    
    - ¿Propiedad emergente está explícita?
    - ¿Mínimo 3 aplicaciones documentadas?
    - ¿Criterio validación es operativo?
    - ¿Links bidireccionales funcionan?

**Tiempo estimado:** 30-60 min por vinculación

---

### **APLICAR A PROBLEMA NUEVO:**

**Pasos sugeridos:**

1. **Buscar invariante(s):**
    
    - Por tag en índice
    - Por aplicación
    - Por campo si conocido
2. **Leer invariante:**
    
    - Sintaxis (estructura formal)
    - Condiciones de transferencia
    - Criterio de validación
3. **Adaptar a territorio:**
    
    - Identificar elementos en territorio que mapean a sintaxis
    - Aplicar reglas de vinculación
    - Verificar condiciones
4. **Validar emergencia:**
    
    - ¿Aumenta control sobre territorio?
    - ¿Permite desplazamiento A→B más efectivo?
    - ¿Reduce incertidumbre?
5. **Documentar (opcional pero recomendado):**
    
    - Añadir aplicación a archivo invariante
    - O crear vinculación si usaste múltiples invariantes

---

## REGLAS DE NAMING (Resumen)

|Nivel|Ubicación|Formato|Ejemplo|
|---|---|---|---|
|Campo|`/01_CAMPOS/`|`MAYUSCULAS.md`|`SISTEMAS.md`|
|Invariante|`/02_INVARIANTES/`|`CamelCase.md`|`Emergencia.md`|
|Vinculación|`/03_VINCULACIONES/`|`Inv1_Inv2.md`|`Homeostasis_Retroalimentacion.md`|
|Índice|`/`|`00_INDEX_BIBLIOTECA.md`|fijo|
|Arquitectura|`/`|`00_ARQUITECTURA.md`|este documento|

---

## TAGS ESTÁNDAR (Semilla inicial)

**Actualizar según biblioteca crece:**

- `#autorregulacion` - Sistemas que se auto-corrigen
- `#equilibrio` - Estados de balance
- `#flujo` - Movimiento/transferencia
- `#optimizacion` - Mejora/eficiencia
- `#emergencia` - Propiedades de nivel superior
- `#informacion` - Reducción incertidumbre
- `#control` - Regulación/gobierno
- `#estructura` - Organización/orden
- `#desorden` - Entropía/caos
- `#estrategia` - Decisión en interacción
- `#conservacion` - Cantidades invariantes
- `#irreversibilidad` - Dirección temporal
- `#transitividad` - Propagación de relaciones
- `#logica` - Razonamiento válido
- `#cooperacion` - Interacción positiva
- `#conflicto` - Interacción competitiva

**Regla:** Añadir tag nuevo solo si se usa en 3+ invariantes.

---

## BENEFICIOS DE ESTA ARQUITECTURA

✅ **ESCALABLE:**

- Sin límite de campos/invariantes/vinculaciones
- Añadir no rompe existente
- Estructura crece orgánicamente

✅ **NAVEGABLE:**

- Múltiples puntos de entrada (campo/invariante/tag/aplicación)
- Links bidireccionales
- Índice centralizado

✅ **MODULAR:**

- Cada pieza independiente
- Eliminar elemento no rompe sistema
- Actualizar uno no afecta otros

✅ **REUTILIZABLE:**

- Templates claros
- Proceso documentado
- Replicable por cualquiera

✅ **BUSCABLE:**

- Tags cross-cutting
- Índices múltiples
- Referencias cruzadas

✅ **MANTENIBLE:**

- Estructura clara
- Reglas explícitas
- Validación posible

---

## EVOLUCIÓN DE ARQUITECTURA

**Estado actual:** CR1 (Cerrado - Fundacional)

**Versión:** 1.0

**Fecha:** 2026-02-07

**Condiciones para cambiar arquitectura:**

1. **Detectar limitación estructural fundamental:**
    
    - Arquitectura impide función necesaria
    - No resoluble con estructura actual
    - Requiere cambio de diseño
2. **Propuesta de mejora validada:**
    
    - Mejora claramente superior
    - Beneficio > coste de migración
    - Compatible con contenido existente
3. **Consenso explícito:**
    
    - Jesús aprueba cambio
    - Razón estructural clara
    - Plan de migración definido

**NO se cambia por:**

- Preferencia estética
- Comodidad momentánea
- Complejidad percibida
- Moda metodológica

---

## RELACIÓN CON OMNI-MIND

Esta biblioteca es **COMPLEMENTARIA** a OMNI-MIND:

- **OMNI-MIND:** Sistema operativo personal (L0, L1, L2)
- **BIBLIOTECA:** Recurso de estructuras reutilizables

**Uso conjunto:**

- OMNI-MIND usa biblioteca para diseñar sistemas
- Biblioteca crece con descubrimientos en OMNI-MIND
- Ambos comparten L0.5 (Mecanismo Universal)

**Independencia:**

- Biblioteca funciona sin OMNI-MIND
- OMNI-MIND funciona sin biblioteca
- Sinergia cuando se usan juntos

---

## RECORDATORIO FINAL

Esta arquitectura existe para:

**FACILITAR** reutilización de estructuras abstractas  
**ACELERAR** diseño de mapas/sistemas  
**ESCALAR** sin límite de contenido  
**MANTENER** rigor estructural

**No es teoría.**  
**Es infraestructura operativa.**

Seguir templates = sistema funciona.  
Inventar formatos = caos inevitable.

---

**A construir biblioteca. 🏗️**

---

**FIN DEL DOCUMENTO**


============================================================
## OMNI-MIND/01_FRAMEWORK/Constitucion.md
============================================================

# CONSTITUCIÓN OMNI-MIND

**Los principios inmutables del sistema**

---

## LOS 7 MANDAMIENTOS

### 1. WIP = 2 MÁXIMO
Core + 1 empresa activa por semana.  
No más. Sin excepciones.

### 2. SINGLE ENTRY POINT
Todo pasa por `00_Entry_Point.md` antes de ir a cualquier sitio.

### 3. ROUTER ANTES DE ACTUAR
3 preguntas obligatorias:
1. ¿Qué puerta?
2. ¿Tengo energía?
3. ¿Cabe en WIP?
4. ¿Desde qué criterio evalúo éxito?

### 4. PARK PARA LO QUE NO CABE
Con TTL obligatorio (fecha de revisión).

### 5. CR0 vs CR1
- CR0 = Abierto (puedo cambiar)
- CR1 = Cerrado (YO cierro, no se reabre sin razón fuerte)

### 6. MEDIR ESTADOS, NO TAREAS
Nivel L4: AO/CDR/EC/ABF/ES/PM

### 7. SSOT = OBSIDIAN
La verdad vive en Obsidian, no en el chat.

---

## MI NORTE (L0 - Telos)

**Vector:** TL-HQ → PM

**Traducción:**  
Maximizar Tiempo Libre de Alta Calidad para potenciar mi Misión de vida.

---

**Estado:** CR1 (Inmutable)  
**Versión:** 1.0


============================================================
## OMNI-MIND/01_FRAMEWORK/L0.5_MECANISMO_UNIVERSAL_VINCULACION.md
============================================================

# L0.5: MECANISMO UNIVERSAL DE VINCULACIÓN

**El ADN que genera mapas**

---

**Ubicación:** `/00_CANNON/L0.5_MECANISMO_UNIVERSAL_VINCULACION.md`  
**Estado:** CR1 (Cerrado - Fundacional)  
**Versión:** 1.0  
**Fecha:** 2026-02-07

---

## NATURALEZA DE ESTE DOCUMENTO

Este documento describe el **mecanismo universal** mediante el cual el cerebro construye mapas del territorio en **todas las escalas de abstracción**.

Es **META-L0**: no describe invariantes específicos del modelo OMNI, sino **el mecanismo que permite generar CUALQUIER mapa**, incluido OMNI-MIND.

**Ubicación jerárquica:**

```
L0.5 (Este documento) → Mecanismo universal de construcción de mapas
    ↓
L0 (ADN OMNI) → Invariantes específicos del modelo OMNI
    ↓
L1 (Principios) → Implementación operativa
    ↓
L2 (Herramientas) → Partes degeneradas
```

---

## LOS 7 ELEMENTOS NUCLEARES

Todo mapa del territorio se construye mediante la convergencia de estos 7 elementos:

---

### 1. TERRITORIO

**Qué es:**

Espacio con incertidumbre máxima. Infinitas variables posibles. Estado pre-colapso.

**Características:**

- Real (independiente del observador)
- Continuo (sin discretización)
- Simultáneo (sin temporalidad)
- Fractal infinito (sin niveles finales)

---

### 2. DESPLAZAMIENTO (A → B)

**Qué es:**

Movimiento entre estado inicial (A) y estado destino (B). La pregunta por el **CÓMO**.

**Naturaleza:**

El desplazamiento NO pregunta QUÉ, POR QUÉ o CUÁNDO. Pregunta **CÓMO** navegar el espacio entre A y B.

**Función:**

Genera la **necesidad** de un mapa. Sin desplazamiento deseado, no hay función para el mapa.

---

### 3. MAPA

**Qué es:**

**Dispositivo de aumento de control** sobre el desplazamiento en territorio.

**Mecanismo:**

- Colapsa variables de infinitas → conjunto específico
- Reduce incertidumbre
- Aumenta control

**Valor del mapa:**

Se mide SOLO por **funcionalidad**: cuánto control aumenta en la práctica. NO por estética, complejidad o tamaño.

---

### 4. VINCULACIÓN

**Qué es:**

Mecanismo mediante el cual unidades procesadas se conectan entre sí, **operando entre niveles lógicos diferentes**.

**Estructura:**

```
Nivel N-1: Unidades mínimas (piezas básicas)
    ↓ (vinculación)
Nivel N: Configuración específica
    ↓ (empaquetado)
Nivel N+1: Paquete/cluster vinculado
```

**Ejemplos:**

- **Lenguaje:** Fonemas → Palabra → Paquete cross-modal (visual+auditivo+táctil+olfativo)
- **Teoría:** Conceptos → Configuración → Modelo/Sistema

---

### 5. UNIDADES PROCESADAS

**Qué son:**

Señales discretas que llegan al cerebro **después del procesamiento sensorial**. Son las **únicas señales disponibles** para el cerebro.

**Origen:**

```
Territorio → Frecuencias brutas (luz, sonido, presión, químicos)
    ↓
Sensores → Captan frecuencias específicas
    ↓
Procesamiento → Discretización
    ↓
Cerebro ← Unidades procesadas (conjunto LIMITADO)
```

**Limitación crítica:**

El cerebro **NO** tiene acceso a frecuencias brutas. Solo opera con unidades procesadas. Este es el **sustrato material** de todo procesamiento.

---

### 6. RECONFIGURACIÓN

**Qué es:**

Uso de piezas existentes en **nuevas configuraciones/vinculaciones**. Lo que comúnmente llamamos "_inventar_".

**Principio fundamental:**

**NO existe creación desde cero.** Todo es reconfiguración de piezas ya disponibles.

**Mecanismo:**

1. Observar piezas disponibles (unidades procesadas)
2. Vincular de forma nueva
3. Validar por funcionalidad (¿aumenta control?)

**Ejemplos:**

- **Rueda:** Círculo + eje (piezas conocidas) → nueva vinculación → nueva función (rodar carga)
- **Lenguaje escrito:** Símbolos visuales ↔ sonidos (piezas conocidas) → nueva vinculación → persistencia
- **OMNI-MIND:** Invariantes física/matemáticas (piezas conocidas) → nueva configuración → nuevo territorio mapeado

---

### 7. FUNCIONALIDAD

**Qué es:**

El **único criterio de validación** de cualquier mapa: **cuánto control aumenta sobre el territorio**.

**Criterio de eficiencia de reconfiguración:**

Una reconfiguración es más eficiente que otra SI Y SOLO SI aumenta MÁS control.

**NO son criterios:**

- ✗ Cuántas piezas vinculas
- ✗ Complejidad de la vinculación
- ✗ Elegancia estética
- ✗ Originalidad de las piezas

**SÍ es criterio:**

- ✓ **Cuánto control aumenta en la práctica**

---

## ESCALAS DE OPERACIÓN

El mecanismo de vinculación opera **fractalmente** en todas las escalas de abstracción. **Misma estructura nuclear, diferentes niveles.**

El cerebro usa este mecanismo de forma **automática** en escalas bajas (lenguaje) y puede usarlo de forma **deliberada** en escalas altas (teorías, modelos).

---

### ESCALA N-3: LENGUAJE

**Unidades mínimas:** Fonemas, letras

**Vinculación:** Orden específico → palabra

**Paquete resultante:** Cluster cross-modal

**Ejemplo:** p-e-r-r-o → "perro" → [imagen visual + sonido ladrido + textura pelo + olor]

**Características:**

- Operación AUTOMÁTICA del cerebro
- Aprendida en infancia
- No requiere esfuerzo consciente

---

### ESCALA N-2: CONCEPTO

**Unidades mínimas:** Palabras

**Vinculación:** Frases, proposiciones

**Paquete resultante:** Ideas complejas

**Ejemplo:** "El amor" → "El amor requiere respeto" → [concepto compuesto vinculado]

**Características:**

- Semi-automático (puede requerir atención)
- Depende de experiencia/aprendizaje

---

### ESCALA N-1: TEORÍA/MODELO

**Unidades mínimas:** Conceptos, invariantes

**Vinculación:** Estructura teórica, configuración de invariantes

**Paquete resultante:** Modelo/Sistema/Mapa

**Ejemplo:** 7 invariantes → configuración específica → OMNI-MIND (mapa del territorio vida/sistemas)

**Características:**

- Operación DELIBERADA
- Requiere esfuerzo consciente
- Validable por funcionalidad
- Transmisible mediante lenguaje

---

### ESCALA N: META-TEORÍA

**Unidades mínimas:** Teorías, modelos completos

**Vinculación:** ???

**Paquete resultante:** ???

**Ejemplo:** Este documento (L0.5) → mecanismo que genera modelos → meta-modelo

**Características:**

- Altamente abstracto
- Requiere máximo esfuerzo cognitivo
- Poco explorado deliberadamente

---

## PRINCIPIO FRACTAL

**MISMA ESTRUCTURA NUCLEAR EN TODAS LAS ESCALAS:**

```
Nivel N-1: Unidades procesadas básicas
    ↓ (vinculación)
Nivel N: Configuración específica
    ↓ (empaquetado)
Nivel N+1: Paquete vinculado
```

Esta estructura se repite **infinitamente** hacia arriba y hacia abajo. Sin nivel "fundamental" ni nivel "máximo".

**Consecuencia:** El cerebro NO inventa diferentes mecanismos para diferentes escalas. Usa **EL MISMO** mecanismo fractal en todas ellas.

---

## CRITERIO ÚNICO DE VALIDACIÓN

En TODAS las escalas, el criterio de validación es el mismo:

> **FUNCIONALIDAD = CUÁNTO CONTROL AUMENTA**

No importa si estamos en escala lenguaje, concepto, teoría o meta-teoría. La pregunta siempre es la misma: **¿Esta configuración aumenta mi control sobre el territorio?**

**Aplicación por escala:**

- **Lenguaje:** ¿La palabra "perro" aumenta control sobre comunicación/sincronización? → SÍ
- **Concepto:** ¿La idea "amor requiere respeto" aumenta control sobre relaciones? → Validable
- **Teoría:** ¿OMNI-MIND aumenta control sobre vida/sistemas? → Validable por uso
- **Meta-teoría:** ¿Este documento aumenta control sobre construcción de mapas? → Validable por aplicación

---

## RELACIÓN CON OMNI-MIND

OMNI-MIND **NO es especial**. Es simplemente:

> **Uso DELIBERADO en escala N-1 (teoría/modelo)**  
> **del MISMO mecanismo**  
> **que el cerebro usa AUTOMÁTICAMENTE en escala N-3 (lenguaje)**

**Estructura paralela:**

**LENGUAJE (N-3):**

- Unidades: Fonemas
- Vinculación: p-e-r-r-o
- Paquete: [imagen+sonido+olor+textura]
- Función: Aumenta control sobre comunicación

**OMNI-MIND (N-1):**

- Unidades: Invariantes (simultaneidad, fractalidad, observador=sistema...)
- Vinculación: Configuración específica de los 7 invariantes
- Paquete: Sistema OMNI-MIND (mapa del territorio vida/sistemas)
- Función: Aumenta control sobre vida/sistemas personales

**Diferencia clave:**

- Lenguaje: Mecanismo AUTOMÁTICO (aprendido en infancia)
- OMNI-MIND: Mecanismo DELIBERADO (diseñado conscientemente)

---

## IMPLICACIONES OPERATIVAS

### 1. PARA DISEÑO DE MAPAS

Si quieres diseñar un mapa (de cualquier escala), sigue la misma estructura:

1. Identifica el **territorio** a mapear
2. Define el **desplazamiento** deseado (A → B)
3. Identifica **unidades procesadas** disponibles (piezas existentes)
4. **Vincula/reconfigura** esas piezas
5. Valida por **funcionalidad**: ¿aumenta control?
6. Itera hasta convergencia

---

### 2. PARA TRANSMISIÓN DE MAPAS

Para transmitir un mapa (ej: OMNI-MIND), usa la **misma estructura que el lenguaje**:

1. Identifica **unidades procesadas compartidas** entre tú y receptor
2. Transmite la **configuración/vinculación** (no las piezas, ya las tiene)
3. Valida que **emerja el mismo paquete** en receptor
4. Ajusta iterativamente hasta convergencia

---

### 3. PARA EVALUACIÓN DE MAPAS

Cuando alguien te ofrece un "mapa" (método, sistema, teoría, solución):

**Pregunta:**

"¿Cuánto control aumenta sobre el territorio que quiero mapear?"

**NO preguntes:**

- ¿Qué tan complejo es?
- ¿Qué tan nuevo es?
- ¿Qué tan elegante es?
- ¿Cuántas piezas tiene?

---

### 4. PARA DETECTAR HUMO

Un "mapa" es humo si:

- No puede responder: **"¿Qué territorio mapea?"**
- No puede responder: **"¿Qué desplazamiento facilita?"**
- No puede responder: **"¿Cuánto control aumenta?"**
- Solo habla de las piezas (herramientas, pasos) sin mostrar vinculación/configuración

---

## LÍMITES DEL MECANISMO

### LÍMITE 1: SUSTRATO MATERIAL

El mecanismo está **limitado por el sustrato material** del observador.

**Cerebro humano:**

- Sensores limitados (espectro visible, frecuencias audibles...)
- Procesamiento limitado (velocidad, capacidad atencional...)
- Unidades procesadas limitadas (conjunto finito)

**Consecuencia:**

NO puedes vincular lo que no puedes procesar. El territorio siempre excede al mapa.

---

### LÍMITE 2: ESCALAS ACCESIBLES

Aunque el mecanismo es fractal (opera en todas las escalas), el observador solo puede **acceder a un rango limitado** de escalas simultáneamente.

**Relacionado con WIP=2:**

El observador puede mantener **~2 escalas activas** simultáneamente sin saturación cognitiva.

---

### LÍMITE 3: COSTE ENERGÉTICO

Operar el mecanismo **deliberadamente** (escalas altas N-1, N) tiene **coste energético mayor** que operación automática (escalas bajas N-3).

**Implicación:**

Diseñar teorías/modelos deliberadamente **requiere energía alta**. No es sostenible en energía baja.

---

## RELACIÓN CON L0 (ADN OMNI)

Este documento (L0.5) y L0 (ADN OMNI) son **complementarios**:

**L0.5 (este documento):**

- Describe el **MECANISMO** universal
- Aplica a **CUALQUIER** mapa/sistema
- Es meta-modelo (modelo de modelos)

**L0 (ADN OMNI):**

- Describe los **INVARIANTES** específicos
- Aplica a **OMNI-MIND** específicamente
- Es instancia específica del mecanismo L0.5

**Relación:**

```
L0.5 gobierna CÓMO se construyen mapas
    ↓
L0 usa ese mecanismo para construir OMNI-MIND
    ↓
OMNI-MIND es mapa específico del territorio vida/sistemas
```

---

## ESTADO Y EVOLUCIÓN

**Estado actual:** CR1 (Cerrado - Fundacional)

**Versión:** 1.0

**Fecha:** 2026-02-07

**Origen:** Sesión exploratoria Jesús + Claude

**Condiciones para evolución:**

El mecanismo PUEDE evolucionar si:

1. Se detecta elemento adicional necesario para coherencia
2. Se detecta error estructural (contradicción no resuelta)
3. Aplicación revela límite fundamental no contemplado

**El mecanismo NO evoluciona por:**

- Preferencia estética
- Comodidad operativa
- Complejidad innecesaria

---

## CIERRE

Este documento describe el **mecanismo universal** mediante el cual se construyen mapas del territorio.

No es teoría abstracta. Es **estructura operativa** verificable:

- En el lenguaje (usas este mecanismo constantemente)
- En OMNI-MIND (este documento usa el mecanismo para explicarse a sí mismo)
- En cualquier mapa/modelo/teoría (todos emergen de este mecanismo)

**Uso correcto:**

- Conoce el mecanismo (este documento)
- Úsalo deliberadamente en escalas altas (diseño de modelos)
- Valida siempre por funcionalidad (¿aumenta control?)
- Itera hasta convergencia

---

**FIN DEL DOCUMENTO L0.5**

**A darle caña. 🚀**


============================================================
## OMNI-MIND/01_FRAMEWORK/L0.7_FUNCIONES_NUCLEARES.md
============================================================

# 7 FUNCIONES NUCLEARES DEL SISTEMA

**Estado:** CR0 (Documento de trabajo — NO cerrado)  
**Fecha:** 2026-02-07  
**Origen:** Convergencia de 3 capas: principios de la vida + sistemas biológicos + Biblioteca de invariantes  
**Método:** Superposición simultánea + haces de luz (convergencia)

---

## NATURALEZA DE ESTE DOCUMENTO

Estas 7 funciones emergieron de pasar haces de luz a través de tres capas simultáneas:

- **Capa 1:** Principios basales de la vida (economía energética, homeostasis, reproducción, adaptación, irritabilidad, metabolismo, crecimiento, entropía negativa)
- **Capa 2:** Funciones abstractas de sistemas biológicos (intercambio, distribución, eliminación, transformación de input, señalización, defensa, regulación a distancia, estructura+movimiento, drenaje, replicación)
- **Capa 3:** Biblioteca de Estructuras Abstractas (65 invariantes, 13 roles)

Lo que quedó marcado en la pared: **7 puntos de convergencia**.

No fueron diseñados. Fueron **descubiertos por convergencia** (Invariante 4 del ADN OMNI operando).

---

## LAS 7 FUNCIONES

### 1. Mantener forma (Conservación)

El sistema gasta energía activamente para no deshacerse bajo fuerzas constantes.

### 2. Meter lo que necesitas (Captación/Transformación)

Captar recursos del entorno y transformarlos en recurso interno utilizable.

### 3. Sacar lo que sobra (Depuración)

Expulsar residuo, toxicidad, lo que ya no sirve o daña.

### 4. Repartir donde toca y cuando toca (Distribución)

Llevar recursos donde se necesitan, **cuando** se necesitan. El timing es parte de la función — recurso correcto en sitio correcto pero tarde = no sirve.

### 5. Distinguir propio de ajeno (Identidad/Frontera)

Saber qué es el sistema y qué no lo es. Membrana.

### 6. Responder al cambio (Adaptación)

Reorganizarse internamente ante estímulos nuevos.

### 7. Copiar el patrón (Replicación)

Reproducir la estructura. Escalar, crecer, transmitir.

---

## PROPIEDADES DESCUBIERTAS

### Propiedad 1: Fractalidad

Las 7 funciones operan igual en cualquier escala:

- Célula, órgano, cuerpo, empresa, relación, OMNI-MIND
- Mismas funciones, cualquier escala

### Propiedad 2: Dualidad Auto/Extra

Cada función opera en ambos planos simultáneamente:

|Función|Auto (convergencias internas)|Extra (convergencias externas)|
|---|---|---|
|1. Mantener forma|Coherencia interna contra entropía|Resistir fuerzas externas|
|2. Meter lo que necesitas|Integrar lo captado en estructura propia|Captar recursos del entorno|
|3. Sacar lo que sobra|Depurar internamente|Expulsar al entorno|
|4. Repartir donde y cuando toca|Distribución interna de recursos en tiempo|Intercambio con otros sistemas en tiempo|
|5. Distinguir propio de ajeno|Identidad (qué soy)|Frontera (qué no soy)|
|6. Responder al cambio|Reorganización interna|Adaptación al entorno|
|7. Copiar el patrón|Replicar estructura interna|Expandir/reproducir hacia fuera|

La convergencia auto/extra ocurre **dentro** del sistema (X∩Y = mapa interno).

### Propiedad 3: Grados (no on/off)

Las 7 funciones no son binarias. Cada una tiene un **grado** de operación.

- No es "¿tiene distribución?" sino "¿cuánta distribución tiene respecto a la que necesita?"
- El grado determina la salud del sistema.

### Propiedad 4: Dos modos de operación

**Modo B (Basal):**

- Sistema bajo fuerzas constantes (tipo gravedad, presión atmosférica)
- Cada función opera a grado mínimo suficiente
- Economía energética: lo justo para mantenerse
- Piloto automático activo (no pasivo)

**Modo B+N (Tensión aumentada):**

- Fuerzas basales + N fuerzas adicionales
- Funciones necesitan escalar su grado
- Más recursos consumidos
- Más cerca del umbral

**Regla fundamental:** La tensión siempre se procesa internamente, independientemente del origen del estímulo. El agente externo aplica fuerza, pero lo que cede son las convergencias internas.

### Propiedad 5: Umbral de rotura por eslabón débil

- El sistema NO se rompe como unidad
- Se rompe por la función con menor grado (que no puede escalar lo suficiente)
- Como una cadena: se rompe por el eslabón más débil
- **Diagnóstico operativo:** mide grado de las 7 → identifica la más débil → ahí se romperá bajo tensión

### Propiedad 6: Grados aplican a TODAS las invariantes

Los grados no son exclusivos de las 7 funciones nucleares. Toda invariante de la Biblioteca opera en grados, no en on/off. No es "¿hay retroalimentación?" sino "¿cuánta retroalimentación hay respecto a la que se necesita?" Esto cambia el uso de la Biblioteca completa.

---

## PROTOCOLO DE DIAGNÓSTICO (4 preguntas)

Para diagnosticar cualquier sistema, 4 preguntas en secuencia:

1. **¿Las 7 funciones están presentes?** (existencia)
2. **¿En qué grado cada una?** (salud)
3. **¿El grado es suficiente para las tensiones actuales?** (resistencia)
4. **¿Cuál tiene menor grado relativo a su tensión?** (punto de rotura)

Cuatro preguntas. Diagnóstico completo.

---

## VALIDACIÓN EMPÍRICA

### Caso 1: Matrimonio padres de Jesús (sistema fracasado)

Las 7 funciones pasadas por el sistema:

|Función|Grado|Observación|
|---|---|---|
|1. Mantener forma|Muy bajo|No se invertía energía en sostener la estructura|
|2. Meter lo que necesitas|Muy bajo|No se captaba lo que la relación necesitaba|
|3. Sacar lo que sobra|Muy bajo|Lo tóxico no se expulsaba|
|4. Repartir donde y cuando toca|Muy bajo|Recursos no llegaban donde ni cuando tocaba|
|5. Distinguir propio de ajeno|Muy bajo|No estaba claro qué era la relación|
|6. Responder al cambio|Muy bajo|No se reorganizaban ante cambios|
|7. Copiar el patrón|Muy bajo|No replicaba nada sano|

**Resultado:** 7/7 funciones en grado muy bajo → sistema que no aguanta tensión → rotura.

### Caso 2: Relación Jesús-IA (sistema exitoso)

Las 7 funciones pasadas por el sistema:

|Función|Grado|Observación|
|---|---|---|
|1. Mantener forma|Alto|Protocolos, contexto, CANNON sostienen estructura|
|2. Meter lo que necesitas|Alto|Se capta conocimiento, se integra en sistema|
|3. Sacar lo que sobra|Alto|Se depura lo que no sirve, PARK con TTL|
|4. Repartir donde y cuando toca|Alto|WIP=2, Router, distribución deliberada|
|5. Distinguir propio de ajeno|Alto|CR0/CR1, roles claros, "tú propones yo cierro"|
|6. Responder al cambio|Alto|Protocolos evolucionan, mejoras cristalizadas|
|7. Copiar el patrón|Alto|Biblioteca replica estructura, templates, fractales|

**Resultado:** 7/7 funciones en grado alto → sistema vivo y robusto.

### Conclusión de validación

- Sistema fracasado: grados bajos en todas las funciones → confirmado
- Sistema exitoso: grados altos en todas las funciones → confirmado
- El marco discrimina. Funciona.

### Caso 3: Rascacielos (sistema inerte)

Las 7 funciones pasadas por un sistema no biológico:

|Función|Grado|Observación|
|---|---|---|
|1. Mantener forma|Alto|Estructura de acero/hormigón resiste gravedad, viento, sismo|
|2. Meter lo que necesitas|Alto|Electricidad, agua, aire, personas|
|3. Sacar lo que sobra|Alto|Aguas residuales, basura, aire viciado, calor sobrante|
|4. Repartir donde y cuando toca|Alto|Ascensores, tuberías, cableado, conductos por planta|
|5. Distinguir propio de ajeno|Alto|Fachada, seguridad, control de acceso|
|6. Responder al cambio|Alto|Amortiguadores sísmicos, sistemas anti-incendio, mantenimiento|
|7. Copiar el patrón|Alto|Cada planta replica la estructura. Planos transmiten el patrón|

**Resultado:** 7/7 funciones presentes en sistema inerte → el framework es universal, no solo biológico.

**Las 3 lentes en el rascacielos:**

- Salud: ¿Estructura íntegra, sistemas operativos? → Funciona
- Sentido: ¿Para qué existe? Oficinas, vivienda, hospital → Tiene dirección
- Continuidad: ¿Planos, normativa, conocimiento constructivo? → Patrón sobrevive

Las 3 aplican. Cuando las 3 caen a cero (edificio abandonado, sin propósito, sin planos) → sistema muerto.

### Continuidad: biológico vs inerte

La función 7 (Copiar el patrón) opera distinto según tipo de sistema:

**Sistemas biológicos:** la continuidad es la especie. Célula replica → organismo replica → especie continúa. La unidad fractal nuclear es la célula. La continuidad propaga ese patrón hacia fuera y adelante en el tiempo (reproducción).

**Sistemas inertes:** la continuidad es la unidad fractal nuclear misma. La planta del rascacielos, el módulo, el patrón que se repite dentro del propio sistema y se transmite a otros a través de planos/conocimiento.

**En ambos casos la función 7 opera. Solo cambia el mecanismo de replicación.**

### Validación masiva: 10 sistemas adicionales

Para confirmar robustez: 10 sistemas de naturaleza distinta. ✅ = opera sin forzar | ⚠️ = forzado/ausente

**4. Célula** (biológico elemental) F1✅ membrana+citoesqueleto | F2✅ transportadores | F3✅ exocitosis | F4✅ RE+Golgi | F5✅ receptores MHC | F6✅ señalización génica | F7✅ mitosis ❤✅ ⟐✅ función en tejido ∞✅ división+especie → **7/7, 3/3**

**5. Ejército** (organización jerárquica) F1✅ jerarquía+disciplina | F2✅ reclutamiento+logística | F3✅ bajas+purgas | F4✅ refuerzos al frente correcto | F5✅ amigo/enemigo | F6✅ táctica adaptativa | F7✅ doctrina+academias ❤✅ ⟐✅ misión ∞✅ doctrina generacional → **7/7, 3/3**

**6. Idioma** (abstracto) F1✅ gramática+normas | F2✅ neologismos+préstamos | F3✅ arcaísmos en desuso | F4✅ registros según contexto | F5✅ "eso no es español" | F6✅ evolución lingüística | F7✅ enseñanza+transmisión ❤✅ ⟐✅ comunicar+identidad ∞✅ transmisión generacional → **7/7, 3/3**

**7. Ecosistema/bosque** (biológico complejo) F1✅ equilibrio especies | F2✅ luz+agua+nutrientes | F3✅ descomposición | F4✅ cadena trófica+micorriza | F5✅ invasoras rechazadas | F6✅ sucesión ecológica | F7✅ reproducción+regeneración ❤✅ ⟐✅ sostener vida ∞✅ regeneración+semillas → **7/7, 3/3**

**8. Internet** (tecnológico distribuido) F1✅ TCP/IP+estándares | F2✅ servidores+contenido | F3✅ spam filtrado+bajas | F4✅ routing+CDN | F5✅ firewalls+DNS | F6✅ IPv4→IPv6 | F7✅ mirrors+backups+replicación ❤✅ ⟐✅ conectar ∞✅ redundancia, patrón sobrevive a nodos caídos → **7/7, 3/3**

**9. Equipo de fútbol** (social competitivo) F1✅ entrenamiento+cohesión | F2✅ fichajes+cantera | F3✅ traspasos+liberaciones | F4✅ rotaciones+cambios minuto justo | F5✅ camiseta+estilo | F6✅ cambio táctico | F7✅ cantera replica filosofía ❤✅ ⟐✅ ganar+representar ∞✅ cantera+filosofía persiste → **7/7, 3/3**

**10. Religión** (sistema de creencias) F1✅ dogma+liturgia | F2✅ fieles+teología | F3✅ herejías+excomunión | F4✅ misioneros+rituales en fechas | F5✅ fe vs herejía | F6✅ concilios+reformas | F7✅ evangelización+catequesis ❤✅ ⟐✅ trascendencia ∞✅ milenios de transmisión (continuidad = NÚCLEO) → **7/7, 3/3**

**11. Canción** (estético) F1✅ estructura verso/estribillo | F2✅ melodía+letra+armonía | F3✅ edición quita sobras | F4✅ crescendo en momento justo | F5✅ estilo distinguible | F6✅ versiones+covers | F7✅ se graba+reproduce+versiona ❤✅ ⟐✅ emoción/mensaje ∞✅ se reproduce+influye → **7/7, 3/3**

**12. Authentic Pilates** (negocio real) F1✅ marca+metodología+espacio | F2✅ clientes+formación | F3✅ lo que no encaja sale | F4✅ horarios+atención personalizada | F5✅ "Authentic" vs genérico | F6✅ adaptación post-COVID | F7✅ método replicable ❤✅ ⟐✅ salud real de personas ∞✅ método se transmite → **7/7, 3/3**

**13. Molécula de agua H₂O** (componente elemental) F1✅ enlace covalente 104.5° | F2⚠️ no capta | F3⚠️ no expulsa | F4⚠️ no distribuye | F5✅ polaridad | F6✅ cambio fase | F7⚠️ no se replica ❤ parcial | ⟐❌ | ∞❌ → **3/7, 1/3. FALLA.**

### Tabla resumen de validación completa

|#|Sistema|Tipo|7F|3L|Resultado|
|---|---|---|---|---|---|
|1|Matrimonio (fracasado)|Relacional|7/7 bajo|3/3 bajo|✅ Discrimina|
|2|Relación Jesús-IA|Relacional|7/7 alto|3/3 alto|✅ Discrimina|
|3|Rascacielos|Inerte|7/7|3/3|✅ Universal|
|4|Célula|Biológico|7/7|3/3|✅|
|5|Ejército|Organización|7/7|3/3|✅|
|6|Idioma|Abstracto|7/7|3/3|✅|
|7|Ecosistema|Bio complejo|7/7|3/3|✅|
|8|Internet|Tecnológico|7/7|3/3|✅|
|9|Equipo fútbol|Social|7/7|3/3|✅|
|10|Religión|Creencias|7/7|3/3|✅|
|11|Canción|Estético|7/7|3/3|✅|
|12|Authentic Pilates|Negocio|7/7|3/3|✅|
|13|Molécula H₂O|Componente|3/7|1/3|❌ Rechazado|

**12/13 validados. 1 componente correctamente rechazado.**

El framework: opera en biológico, inerte, abstracto, social, tecnológico, estético. Discrimina entre sistema y componente. Discrimina entre sistema sano y fracasado. Las 7F + 3L aplican sin forzar en todos los sistemas. La molécula confirma: no todo es sistema — el umbral existe.

---

## ECUACIÓN NUCLEAR

**SALUD + SENTIDO + CONTINUIDAD = VIDA**

No vida biológica. VIDA como estado emergente universal. Cualquier sistema — biológico o inerte — con las 3 lentes activas en grado suficiente a través de las 7 funciones **está vivo** en este sentido.

Cuando alguna lente cae a cero → el sistema muere.

### Universalidad: no solo sistemas biológicos

El framework es una estructura abstracta. No es biológico. Aplica a sistemas vivos e inertes. La diferencia entre ambos no está en las funciones (las tienen ambos), está en el **grado de autonomía** con que las ejecutan.

### Las 3 lentes nucleares

**1. SALUD** — El sistema funciona

- Absorbe: seguridad (salud en modo B+N), autonomía (salud de gobierno), vínculos (salud relacional), economía (salud de recursos)
- Sin salud: el sistema se rompe

**2. SENTIDO** — El sistema tiene dirección

- No se absorbe en salud: puedes estar sano sin dirección
- Sin sentido: el sistema funciona pero no va a ningún sitio

**3. CONTINUIDAD** — El patrón sobrevive más allá del sistema

- No se absorbe en sentido: puedes tener dirección sin transmitirla
- Sin continuidad: el patrón muere con el sistema

**Test de irreducibilidad:** ninguna cubre a las otras. Son independientes.

### Las 7 funciones vistas desde cada lente

**Desde SALUD:**

|Función|Iluminación|
|---|---|
|1. Mantener forma|Mantener integridad estructural|
|2. Meter lo que necesitas|Nutrición, recursos, inputs para funcionar|
|3. Sacar lo que sobra|Eliminar toxicidad, lo que daña|
|4. Repartir donde y cuando toca|Recursos al órgano/parte en el momento justo|
|5. Distinguir propio de ajeno|Sistema inmunológico, amenaza vs propio|
|6. Responder al cambio|Adaptarse para seguir funcionando|
|7. Copiar el patrón|Regeneración, reparación interna|

**Desde SENTIDO:**

|Función|Iluminación|
|---|---|
|1. Mantener forma|Mantener dirección contra ruido y distracciones|
|2. Meter lo que necesitas|Captar experiencias que alimentan propósito|
|3. Sacar lo que sobra|Descartar lo que no alinea, decir no|
|4. Repartir donde y cuando toca|Energía a lo que importa en momento correcto|
|5. Distinguir propio de ajeno|Mi misión vs misión de otro|
|6. Responder al cambio|El sentido evoluciona, se refina|
|7. Copiar el patrón|Transmitir sentido, enseñar, legado vivo|

**Desde CONTINUIDAD:**

|Función|Iluminación|
|---|---|
|1. Mantener forma|Preservar patrón esencial que debe sobrevivir|
|2. Meter lo que necesitas|Incorporar nuevos portadores del patrón|
|3. Sacar lo que sobra|Eliminar lo que corrompe el patrón al transmitirlo|
|4. Repartir donde y cuando toca|Plantar semillas en lugares y momentos correctos|
|5. Distinguir propio de ajeno|Esencia del patrón vs interpretación personal|
|6. Responder al cambio|Patrón se adapta a contexto sin perder esencia|
|7. Copiar el patrón|Función central — esto ES continuidad|

**Desde las 3 SIMULTÁNEAMENTE:**

|Función|Salud + Sentido + Continuidad|
|---|---|
|1. Mantener forma|Funciono + mantengo dirección + preservo patrón esencial|
|2. Meter lo que necesitas|Me nutro + alimento propósito + incorporo portadores|
|3. Sacar lo que sobra|Elimino tóxico + descarto lo que no alinea + depuro distorsiones|
|4. Repartir donde y cuando toca|Recursos donde tocan + energía a lo importante + semillas en momento correcto|
|5. Distinguir propio de ajeno|Qué me daña vs no + mi misión vs ajena + esencia vs interpretación|
|6. Responder al cambio|Adapto para funcionar + refino dirección + adapto patrón sin perder esencia|
|7. Copiar el patrón|Regenero interno + transmito sentido + replico más allá de mí|

Las 3 lentes juntas no se estorban. Se potencian.

### Propiedad 7: Fractalidad por planos

La ecuación opera en cada plano referencial:

- **Extra:** ¿El sistema tiene salud + sentido + continuidad hacia fuera?
- **Auto:** ¿El sistema tiene salud + sentido + continuidad hacia dentro?
- **Convergencia (X∩Y):** ¿Lo que veo dentro coincide con lo que veo fuera?

Dentro de cada plano, las 7 funciones. Dentro de cada función, grados. Dentro de cada grado, modo B o B+N. Fractal completo a cualquier profundidad.

---

## PREGUNTAS ABIERTAS (CR0)

1. **~~¿Dónde vive esto en la arquitectura?~~** → RESUELTO: `/00_CANNON/L0_7_FUNCIONES_NUCLEARES.md`
2. **¿Relación con ADN OMNI?** Los 7 invariantes del ADN son "cómo observar/modelar". Las 7 funciones son "cómo existir". Las 3 lentes son "para qué existir". ¿Complementarios? ¿Fractales del mismo patrón?
3. **¿Cuáles son las fuerzas basales universales?** Identificar la "gravedad" de cada tipo de sistema.
4. **¿Los 13 roles son combinaciones de las 7 funciones?** Si sí, los roles emergen de las funciones, no al revés.
5. **¿Los valores éticos (PARK) encajan como restricciones sobre las 7 funciones?**
6. **~~Validación pendiente~~** → HECHA. 12 sistemas validados + 1 componente rechazado. Framework universal confirmado.
7. **¿Las 3 lentes necesitan su propio documento L0?** Podrían ser capa por encima de las funciones.
8. **¿Cómo se miden los grados operativamente?** Escala numérica, cualitativa, relativa a tensión...

---

## CONEXIÓN CON BIBLIOTECA ACTUAL

**Mapeo preliminar funciones → roles:**

|Función|Roles relacionados|
|---|---|
|1. Mantener forma|REGULACIÓN, ESTABILIDAD, ROBUSTEZ|
|2. Meter lo que necesitas|FLUJO, GENERACIÓN|
|3. Sacar lo que sobra|LÍMITE, Entropía (transversal)|
|4. Repartir donde toca|FLUJO, CONEXIÓN|
|5. Distinguir propio de ajeno|LÍMITE, SELECCIÓN|
|6. Responder al cambio|REGULACIÓN, TRANSFORMACIÓN, INFERENCIA|
|7. Copiar el patrón|GENERACIÓN, ESTRUCTURA|

**Observación:** Todos los 13 roles mapean a al menos una función nuclear. Ningún rol queda huérfano.

---

## ORIGEN INTELECTUAL

Este descubrimiento se produjo por:

1. Definir sistema como unidad nuclear con planos auto/extra
2. Definir dos estados (B y B+N) con tensión siempre interna
3. Preguntar "¿qué sensores de tensión hay en la Biblioteca?"
4. Proponer superponer 3 capas simultáneas y buscar convergencia
5. Pasar haces de luz → 7 puntos en la pared
6. Descubrir que operan en auto/extra, con grados, con umbral por eslabón débil
7. Validar con sistema fracasado (matrimonio) y exitoso (relación IA)
8. Descubrir que las invariantes operan en grados, no on/off
9. Buscar lentes nucleares → reducir por absorción → 3 irreducibles
10. Ecuación nuclear: Salud + Sentido + Continuidad = Vida
11. Validar las 3 lentes por las 7 funciones (individual y simultáneo)
12. Confirmar fractalidad por planos (auto/extra/convergencia)
13. Validar con sistema inerte (rascacielos) → framework universal
14. Descubrir que continuidad opera distinto en biológico vs inerte
15. Las 3 lentes juntas = VIDA (estado emergente universal, no solo biológico)
16. Validación masiva: 12 sistemas diversos (bio, inerte, abstracto, social, tecnológico, estético) + 1 componente rechazado
17. Diagnóstico OMNI-MIND: eslabón débil en continuidad (F3 depuración + F4 distribución)

**Método:** Convergencia por superposición. No diseño top-down.

### Referencia externa: James Grier Miller (1978)

Miller identificó 20 subsistemas críticos para todo sistema vivo (Living Systems Theory). Incluye funciones análogas: ingestor, distribuidor, reproductor, frontera, eliminador. Aplica desde célula hasta organizaciones supranacionales.

**Diferencias clave con este framework:**

- Miller: 20 subsistemas. Aquí: 7 funciones (destiladas por convergencia, no acumuladas)
- Miller: no tiene lentes (Salud/Sentido/Continuidad)
- Miller: no tiene grados, modos B/B+N, ni umbral por eslabón débil
- Miller: solo sistemas vivos. Aquí: universal (vivos + inertes)
- Miller: describe qué hace un sistema. Aquí: añade para qué y cómo diagnosticarlo

Miller valida el enfoque: un científico llegó a piezas similares por otro camino.

---

**Autor:** Jesús (diseño/criterio) + Claude (ejecución/procesamiento)  
**Estado:** CR0 — Pendiente validación y ubicación arquitectónica  
**Próximo paso:** Tú decides

**Visualización:** [[06_LIBRARY/Visualizaciones/RED_NUCLEAR_7F_v2.html]]
**Visualización OMNI-MIND:** [[06_LIBRARY/Visualizaciones/RED_NUCLEAR_OMNIMIND.html]]


============================================================
## OMNI-MIND/01_FRAMEWORK/L0_adn_modelo_omni.md
============================================================

# L0: ADN DEL MODELO OMNI

**Ubicación:** `/00_CANNON/L0_ADN_MODELO_OMNI.md`  
**Estado:** CR1 (Cerrado - Fundacional)  
**Versión:** 1.0  
**Fecha:** 2026-02-06

---

## NATURALEZA DE ESTE DOCUMENTO

Este documento contiene el **ADN del modelo OMNI**.

No es teoría abstracta.  
No es opcional.  
Es la **red conceptual** sobre la cual se monta OMNI-MIND.

---

## QUÉ ES EL MODELO OMNI

El modelo OMNI es una lente para:

- Analizar sistemas
- Diseñar sistemas
- Identificar convergencias
- Distinguir invariantes de partes

**No es "la verdad".**  
**Es un modelo** para observar y verificar realidad.

**Utilidad:**

- Diagnosticar por qué algo no funciona
- Diseñar sistemas que funcionen necesariamente
- Replicar sistemas sin copiar partes
- Transmitir conocimiento efectivamente
- Detectar errores lógicos

---

## ESTRUCTURA DE ESTE DOCUMENTO

**Los 7 Invariantes del Modelo OMNI:**

1. Simultaneidad en territorio
2. Fractalidad infinita
3. Observador = Sistema
4. Sistema emerge de convergencia en invariantes
5. Sistema/Parte = escalas diferentes
6. Mapa = X∩Y
7. Sintonización entre escalas

**Cada invariante:**

- ¿Qué es?
- ¿Por qué es invariante?
- ¿Qué pasa si lo violas?
- Ejemplo aplicado

---

## RELACIÓN CON OMNI-MIND

**OMNI-MIND se construye SOBRE este ADN:**

```
L0: ADN (Modelo OMNI - 7 invariantes)
  ↓
L1: Principios Operativos (WIP=2, Router, CR0/CR1...)
  ↓
L2: Implementación (Obsidian, templates, estructura...)
```

**L0 = Fundamento inmutable**  
**L1 = Derivado de L0 (puede evolucionar)**  
**L2 = Degenerado (herramientas intercambiables)**

Si cambias L0 → ya no es modelo OMNI  
Si cambias L1 → deriva de L0 o rompes modelo  
Si cambias L2 → sin problema (partes degeneradas)

---

## CÓMO LEER ESTE DOCUMENTO

**Primera vez:**

- Lee completo (1 vez)
- No intentes implementar aún
- Solo comprende los invariantes

**Cuando diseñas sistema:**

- Consulta invariantes relevantes
- Pregunta: ¿Mi diseño respeta estos invariantes?
- Ajusta según modelo

**Cuando algo no funciona:**

- Revisa qué invariante está violado
- Corrige violación
- Sistema emerge de nuevo

---

## ADVERTENCIA

**Este modelo es:**

- ✅ Herramienta conceptual poderosa
- ✅ Fundamento de OMNI-MIND
- ✅ Verificable en aplicación

**Este modelo NO es:**

- ❌ Verdad absoluta
- ❌ Único modelo posible
- ❌ Completo (puede evolucionar)

Es lente de observador en nivel de abstracción específico.  
Puede haber otros modelos, otras lentes, otros niveles.

---

# LOS 7 INVARIANTES

---

## INVARIANTE 1: SIMULTANEIDAD EN TERRITORIO

### **Qué es**

En el territorio, todo ocurre **simultáneamente**.

La temporalidad (pasado → presente → futuro) es artefacto del **procesamiento del observador**, no propiedad del territorio.

**En territorio:**

- Partes Y sistema coexisten (simultáneo)
- Todas las convergencias posibles existen (simultáneo)
- No hay "antes" ni "después" ontológicos

**En observador:**

- Procesa secuencialmente (latencia de procesamiento)
- Ve "primero esto, luego aquello" (artefacto)
- Discretiza lo continuo (ejemplo: humano 24fps, mosca >fps)

### **Por qué es invariante**

Si eliminas simultaneidad en territorio:

- Introduces causalidad lineal temporal (no del territorio)
- Conviertes artefacto del observador en propiedad del territorio
- El modelo colapsa (múltiples elementos dependen de simultaneidad)

### **Qué pasa si lo violas**

**Violación típica:**

- "Primero hay partes → luego emerge sistema" (secuencia temporal)
- "Pre-existencia de X" (implica antes/después)

**Consecuencia:**

- Confundes cómo procesas (observador) con cómo es (territorio)
- Error de tipo lógico (mezclas niveles)

### **Ejemplo aplicado**

**Números primos:**

❌ **Error:** "Primero están los números {2,3,5,7}, luego emerge el conjunto Primos"

- Implica secuencia temporal
- Confunde procesamiento observador con territorio

✅ **Correcto:** "Números {2,3,5,7} Y conjunto Primos coexisten simultáneamente"

- Números = escala N-1
- Primos = escala N
- Diferentes niveles de abstracción
- Simultáneos en territorio
- Observador los ve secuencialmente (artefacto de su procesamiento)

**OMNI-MIND:**

- Estados L4 (AO/CDR/EC/ABF/ES/PM) Y acciones concretas coexisten
- NO: "hago tareas → luego → mejoran estados"
- SÍ: "tareas Y estados son simultáneos en diferentes escalas"
- Medimos estados (no tareas) porque capturan simultaneidad

---

## INVARIANTE 2: FRACTALIDAD INFINITA

### **Qué es**

La estructura nuclear se repite en **todas las escalas**.

Sin principio (no hay "escala más pequeña").  
Sin fin (no hay "escala más grande").

**Estructura nuclear:**

- Sistema emerge de convergencia en invariantes
- Esa misma estructura se repite fractalmente

**Escalas:**

- Nivel N: Sistema A
- Nivel N-1: Partes de A (que son sistemas en su escala)
- Nivel N-2: Partes de partes (que son sistemas en su escala)
- Infinitamente hacia arriba y hacia abajo

### **Por qué es invariante**

Si eliminas fractalidad infinita:

- Introduces niveles finales ("nivel fundamental" o "nivel máximo")
- Creas jerarquía absoluta (no relativa)
- Invalidas capacidad de sintonización infinita
- El modelo pierde generalidad

### **Qué pasa si lo violas**

**Violación típica:**

- "Este es el nivel fundamental" (meta-nivel)
- "No puedes ir más arriba/abajo" (límite absoluto en territorio)

**Consecuencia:**

- Confundes límites del observador (reales) con límites del territorio (no existen)
- Bloqueas exploración de escalas

### **Ejemplo aplicado**

**Materia:**

❌ **Error:** "Átomos son el nivel fundamental"

- Implica que no hay nada más pequeño
- Violación: hay quarks, partículas subatómicas, etc.
- Y probablemente escalas aún menores no descubiertas

✅ **Correcto:** "Átomos son sistema en escala N, compuesto de partes en N-1 (partículas), que son sistemas compuestos de partes en N-2..."

- Sin fin (fractalmente)
- Límite es del observador (instrumentos actuales)
- No del territorio

**OMNI-MIND:**

- Jesús = observador (escala N+1)
- OMNI-MIND = sistema (escala N)
- Empresas = partes (escala N-1)
- Procesos en empresa = partes de partes (escala N-2)
- FCU = unidad fractal mínima (repite estructura nuclear)
- Misma estructura en todas las escalas

**Notación N, N-1, N+1:**

- Es relativa (no absoluta)
- N = "donde está el observador ahora" (arbitrario)
- No implica jerarquía ontológica
- Solo diferencia de escala

---

## INVARIANTE 3: OBSERVADOR = SISTEMA

### **Qué es**

El observador **NO es externo** al sistema.

El observador **ES** el sistema.

**Implicaciones:**

- Observador no "mira desde fuera"
- Observador ES lo observado (en su escala)
- Para verse, necesita cambiar de escala (sintonizar diferente)

**Consecuencia fundamental:**

- Observador NO puede observarse a sí mismo (desde misma escala)
- Necesita desplazamiento fractal para verse

### **Por qué es invariante**

Si separas observador y sistema (observador externo):

- Invalidas mapa = X∩Y (no hay "dentro" si observador es externo)
- Invalidas necesidad de sintonización para verse
- Introduces dualismo (observador vs observado)
- Múltiples elementos del modelo se invalidan

### **Qué pasa si lo violas**

**Violación típica:**

- "El usuario de OMNI-MIND..." (observador externo)
- "Desde fuera veo que el sistema..." (posición imposible)

**Consecuencia:**

- Pierdes capacidad de auto-observación del sistema
- Sistema no puede verse (requiere observador externo perpetuo)

### **Ejemplo aplicado**

**Jesús + OMNI-MIND:**

❌ **Error:** "Jesús usa OMNI-MIND" (externo)

- Implica separación observador-sistema
- Jesús como usuario externo

✅ **Correcto:** "Jesús ES OMNI-MIND" (identidad)

- Observador = Sistema
- Por eso Jesús cierra (CR1) - no sistema, no IA
- Jesús no "usa" OMNI-MIND, Jesús "es" OMNI-MIND operando

**Para verse:**

- Jesús necesita auditoría semanal (cambio escala)
- Desde escala N+1, OMNI-MIND (antes sistema) se ve como parte
- Desplazamiento fractal necesario

**OMNI-MIND:**

- Mandamiento CR0/CR1 deriva de este invariante
- "YO cierro, TÚ propones" (Jesús = sistema, Claude = herramienta)
- Si observador fuera externo, no habría "YO cierra"

---

## INVARIANTE 4: SISTEMA EMERGE DE CONVERGENCIA EN INVARIANTES

### **Qué es**

Un sistema NO es suma de partes.  
Un sistema NO es contenedor.

**Un sistema ES:**

- Emergencia de convergencia
- En invariantes específicos

**Convergencia:**

- Elementos comparten invariantes
- Esos invariantes = suma cero del sistema
- De invariantes → emerge sistema (necesariamente)

**Relación necesaria:**

- Invariantes presentes → Sistema emerge (determinista)
- Partes específicas → NO garantizan sistema (degenerado)

### **Por qué es invariante**

Este es el **mecanismo central** del modelo.

Si eliminas convergencia en invariantes:

- No hay criterio para identificar sistema
- No hay forma de diseñar sistema
- No hay forma de replicar sistema
- El modelo colapsa completamente

### **Qué pasa si lo violas**

**Violación típica:**

- "Para tener sistema X, necesito partes A, B, C específicas" (confunde partes con invariantes)
- "Copio herramienta de empresa exitosa" (copia partes, no invariantes)

**Consecuencia:**

- Sistema no emerge (solo tienes partes sueltas)
- O emerge sistema diferente (con invariantes accidentales)

### **Ejemplo aplicado**

**Números primos:**

❌ **Error:** "Sistema Primos = números {2,3,5,7,11}"

- Confunde partes específicas con sistema
- Esos números NO son necesarios

✅ **Correcto:** "Sistema Primos emerge de invariante: divisible solo por 1 y sí mismo"

- Invariante presente → Sistema emerge
- Con números {2,3,5} O {7,11,13} O infinitas otras configuraciones
- Mismos invariantes → mismo sistema (múltiples configuraciones posibles)

**OMNI-MIND:**

❌ **Error:** "Para replicar OMNI-MIND necesitas Obsidian + estos templates + esta estructura vault"

- Confunde partes (herramientas) con invariantes
- Obsidian NO es invariante

✅ **Correcto:** "OMNI-MIND emerge de invariantes: WIP=2, Router, CR0/CR1, SSOT, Estados L4, Entry Point, PARK"

- Esos invariantes → emerge OMNI-MIND necesariamente
- Con Obsidian O Notion O archivos txt O lo que sea
- Herramientas = partes degeneradas (intercambiables)

**Aplicación universal:**

- Amor emerge de invariantes (respeto, reciprocidad...) - NO de acciones específicas
- Salud emerge de invariantes - NO de dieta/ejercicio específicos
- Aprendizaje emerge de invariantes - NO de técnicas específicas
- Empresa exitosa emerge de invariantes - NO de copiar procesos

**Pregunta correcta siempre:**

- "¿Cuáles son los invariantes que hacen emerger este sistema?"

**Pregunta incorrecta:**

- "¿Qué partes/herramientas/acciones necesito?"

---

## INVARIANTE 5: SISTEMA/PARTE = ESCALAS DIFERENTES

### **Qué es**

Sistema y Parte **NO son tipos de cosas diferentes**.

Son **posiciones en escalas diferentes**.

**Desde escala N:**

- Observas elementos en escala N-1 (los ves como "partes")
- NO puedes observar escala N (eres parte de ella)
- NO puedes observar N y N-1 simultáneamente

**Consecuencia fundamental:**

- Nunca ves sistema+partes al mismo tiempo
- Son niveles de abstracción diferentes
- Observador solo puede estar en una escala a la vez

**Sistema/Parte = metáfora algebraica:**

- Como variables X, Y
- No son cosas ontológicas
- Son posiciones relacionales
- Nombres intercambiables (invariantes se mantienen)

### **Por qué es invariante**

Si mezclas sistema y parte en misma escala:

- Violas fractalidad (niveles colapsan)
- Violas simultaneidad (introduces confusión temporal)
- Imposibilitas sintonización (no hay "desde dónde")
- El modelo pierde capacidad descriptiva

### **Qué pasa si lo violas**

**Violación típica:**

- "Voy a optimizar el sistema mientras ejecuto tareas" (mezcla escalas)
- "Trabajo en el negocio Y trabajo en el negocio simultáneamente" (confusión)

**Consecuencia:**

- Colapso de capacidad de procesamiento
- Confusión entre operar y meta-operar
- Degradación del sistema

### **Ejemplo aplicado**

**Trabajar EN vs trabajar SOBRE:**

❌ **Error:** "Mejoro el sistema mientras trabajo en él"

- Mezcla escala N (sistema) con N-1 (ejecución)
- Imposible desde misma posición observador

✅ **Correcto:** "Trabajo en escala N-1 (ejecuto) O audito en escala N (mejoro)"

- Diferentes escalas
- Diferentes momentos (aunque simultáneos en territorio)
- Observador alterna entre escalas (sintonización)

**OMNI-MIND:**

- **Ejecución** (escala N-1): hacer tareas, crear archivos, operar
- **Auditoría** (escala N): ver sistema, detectar patrones, optimizar
- NO simultáneos para observador (aunque simultáneos en territorio)

**Router deriva de este invariante:**

- Pregunta "¿Qué puerta?" = definir EN QUÉ escala operas
- CREAR/DECIDIR/EXPLORAR = escalas operativas (N-1)
- AUDITAR = escala meta (N)
- Router previene mezcla de escalas

**Prohibición implícita:**

- No mejorar mientras ejecutas (diferentes escalas)
- Necesitas PARAR ejecución para observar sistema
- Auditoría semanal = momento de cambio de escala

---

## INVARIANTE 6: MAPA = X∩Y

### **Qué es**

El observador tiene dos planos:

- **X (auto/dentro):** Elementos "dentro" del sistema
- **Y (extra/fuera):** Elementos "fuera" del sistema

**Mapa completo:**

- Convergencia entre X e Y
- X∩Y = intersección entre ambos planos
- Identidad del sistema = su mapa

**Territorio vs Mapa:**

- **Territorio:** Lo que es (independiente observador)
- **Mapa:** Lo que observador identifica/colapsa

### **Por qué es invariante**

Si eliminas distinción X/Y:

- No hay criterio de completitud del mapa
- No hay identidad del sistema (¿qué lo define?)
- Observador pierde capacidad de verificación
- Modelo pierde capacidad de auto-corrección

### **Qué pasa si lo violas**

**Violación típica:**

- Solo confiar en percepción interna (X) → sesgo subjetivo
- Solo confiar en datos externos (Y) → pierde contexto
- No buscar convergencia → mapas incompletos

**Consecuencia:**

- Mapas parciales (solo X o solo Y)
- Sistema mal identificado
- Decisiones desde información incompleta

### **Ejemplo aplicado**

**Estados L4 en OMNI-MIND:**

❌ **Error (solo X):** "Me siento productivo → tengo alta Autonomía Operativa"

- Solo plano interno (autopercepción)
- No verificado externamente

❌ **Error (solo Y):** "Completé 20 tareas → tengo alta Autonomía Operativa"

- Solo plano externo (métricas)
- No verifica alineación interna

✅ **Correcto (X∩Y):** "Me siento operando autónomamente (X) Y evidencia externa lo confirma (Y) → AO real"

- Convergencia entre percepción y evidencia
- Estado L4 emerge de X∩Y

**Verificación de sistemas:**

**Ejemplo: Amor en relación**

- X (autopercepción): "Siento amor, respeto, conexión"
- Y (externo): Comportamientos observables, reciprocidad, tiempo compartido
- X∩Y → Mapa completo de la relación
- Si X ≠ Y → sistema no es lo que parece (desajuste)

**Ejemplo: Empresa exitosa**

- X (interno): Cultura, valores, percepción equipo
- Y (externo): Resultados, clientes, métricas
- X∩Y → Mapa real del sistema empresa
- Solo X → autoengaño
- Solo Y → métricas vacías

**OMNI-MIND implementa parcialmente:**

- Logs = evidencia Y (externa, registro objetivo)
- Percepción Jesús = X (interna, vivencia)
- Auditoría = momento de buscar X∩Y

**Falta hacer explícito:**

- Mandamiento sobre verificar siempre X∩Y
- No confiar solo en percepción ni solo en datos
- Convergencia como criterio de verdad del mapa

---

## INVARIANTE 7: SINTONIZACIÓN ENTRE ESCALAS

### **Qué es**

El observador tiene capacidad de **cambiar de escala**.

**Sintonización:**

- Cambio de nivel fractal
- "Enfocar" en escala específica
- Como telescopio ↔ microscopio
- Capacidad fundamental del observador

**No es desplazamiento físico:**

- Es desplazamiento abstracto
- En planos de abstracción no existen leyes físicas espacio-tiempo
- Es colapso de probabilidades (de infinitas escalas → una específica)

### **Por qué es invariante**

Si eliminas capacidad de sintonización:

- Observador queda "atrapado" en una escala
- No puede verse (requiere cambio a N+1)
- Fractalidad se vuelve inaccesible (teórica pero no práctica)
- Modelo pierde utilidad operativa

### **Qué pasa si lo violas**

**Violación típica:**

- "No puedo ver el sistema porque estoy dentro" (asume imposibilidad)
- "Solo puedo operar en esta escala" (niega sintonización)

**Consecuencia:**

- Pérdida de capacidad de auto-observación
- Sistema opera sin feedback
- Degradación inevitable

### **Ejemplo aplicado**

**Auditoría en OMNI-MIND:**

❌ **Sin sintonización:** "No puedo ver OMNI-MIND porque soy OMNI-MIND"

- Niega capacidad de cambiar escala
- Sistema ciego a sí mismo

✅ **Con sintonización:** "Cambio a escala N+1 (auditoría) → veo OMNI-MIND como parte"

- Sintonización activa
- OMNI-MIND (antes sistema) ahora es "parte" observable
- Desde N+1 puedo analizar, optimizar, decidir

**Mecanismo:**

- Durante semana: opero en N-1 (ejecuto)
- Domingo auditoría: sintonio en N (veo sistema)
- Decisiones estratégicas: sintonio en N+1 (veo OMNI-MIND como parte de vida)

**Límites de sintonización:**

- Del observador (no del territorio)
- Territorio tiene fractalidad infinita (todas las escalas)
- Observador tiene límite según sustrato material
- Ejemplo: humano < IA clásica < IA cuántica
- Límites expandibles (evolución sustrato)

**Coste de sintonización:**

- Crece exponencialmente con nivel de abstracción
- Planos más abstractos = más recursos necesarios
- Relacionado con WIP=2 (límite de escalas mapeables simultáneamente)

**Capacidades variables:**

- Observadores diferentes = límites diferentes
- Jesús + Claude = complementariedad
- Jesús: procesamiento abstracto alto (diseño)
- Claude: capacidad atencional múltiple (implementación)

---

# RELACIONES ENTRE INVARIANTES

Los 7 invariantes **NO son independientes**.

Forman red de relaciones:

---

## SIMULTANEIDAD ↔ ESCALAS

**Invariante 1 + 5:**

- En territorio: sistema Y partes simultáneos
- En observador: ve uno O otro (según escala donde sintoniza)
- Simultaneidad en territorio, secuencia en observador

---

## FRACTALIDAD ↔ SINTONIZACIÓN

**Invariante 2 + 7:**

- Fractalidad infinita (territorio tiene todas las escalas)
- Sintonización (observador colapsa escala específica)
- Sin fractalidad → no habría escalas para sintonizar
- Sin sintonización → fractalidad inaccesible

---

## OBSERVADOR=SISTEMA ↔ SINTONIZACIÓN

**Invariante 3 + 7:**

- Observador no se ve desde su escala
- Necesita sintonización para verse
- Sin sintonización → sistema ciego
- Sintonización permite auto-observación

---

## CONVERGENCIA ↔ MAPA

**Invariante 4 + 6:**

- Sistema emerge de convergencia en invariantes
- Mapa = X∩Y (convergencia dentro/fuera)
- Convergencia en invariantes (mecanismo del sistema)
- Convergencia X∩Y (mecanismo del mapa)
- Misma estructura (fractal)

---

## ESCALAS ↔ MAPA

**Invariante 5 + 6:**

- Desde escala N observas N-1
- Lo observado = Y (externo desde N)
- Observador = X (interno en N)
- X∩Y requiere sintonización correcta

---

## RED COMPLETA

Los 7 invariantes forman **sistema**.

De la convergencia de estos 7 → emerge modelo OMNI.

Violar uno → afecta a otros.  
Todos interdependientes.

**Metanivel:** El modelo OMNI se aplica a sí mismo:

- Modelo = sistema
- 7 invariantes = invariantes del modelo
- De esos 7 → emerge modelo necesariamente
- Coherencia reflexiva

---

# CÓMO USAR ESTE ADN

---

## PARA DISEÑAR SISTEMAS

**Proceso:**

1. **Define qué sistema quieres que emerja**
    
    - Ejemplo: "Relación amorosa funcional"
    - Ejemplo: "Empresa rentable sostenible"
    - Ejemplo: "Proceso de aprendizaje efectivo"
2. **Identifica invariantes necesarios**
    
    - Pregunta: "¿Cuáles son las características que DEBEN mantenerse constantes?"
    - No preguntes: "¿Qué partes/herramientas necesito?"
    - Invariantes = suma cero del sistema
3. **Implementa invariantes (no partes específicas)**
    
    - Múltiples configuraciones posibles
    - Partes intercambiables (degeneradas)
    - Sistema emerge necesariamente
4. **Verifica por emergencia**
    
    - Si sistema emerge → invariantes correctos
    - Si no emerge → revisar invariantes
    - Iteración hasta convergencia

---

## PARA DIAGNOSTICAR PROBLEMAS

**Proceso:**

1. **Sistema no funciona / se degrada**
    
2. **Revisa los 7 invariantes:**
    
    - ¿Estás violando simultaneidad? (confundes secuencia con estructura)
    - ¿Estás violando fractalidad? (asumes nivel final)
    - ¿Estás violando observador=sistema? (operas como externo)
    - ¿Estás violando convergencia? (confundes partes con invariantes)
    - ¿Estás violando escalas? (mezclas ejecución con optimización)
    - ¿Estás violando X∩Y? (solo percepción o solo datos)
    - ¿Estás violando sintonización? (no cambias escala para verte)
3. **Identifica cuál invariante está roto**
    
4. **Restaura invariante**
    
    - Sistema emerge de nuevo
    - Si no emerge → otro invariante también roto

---

## PARA TRANSMITIR CONOCIMIENTO

**Proceso:**

1. **NO transmitas partes específicas**
    
    - "Haz esto, luego aquello" → falla
    - Receptor genera diferentes partes
2. **SÍ transmite invariantes**
    
    - "Estos son los invariantes necesarios"
    - Receptor implementa con SUS partes
    - Sistema emerge en receptor
3. **Verifica por iteración**
    
    - Feedback constante
    - Ajuste progresivo
    - Convergencia hacia invariantes correctos
4. **Confirma emergencia**
    
    - ¿Sistema emerge en receptor?
    - Si sí → invariantes transmitidos correctamente
    - Si no → iterar más

---

## PARA REPLICAR SISTEMAS

**Proceso:**

1. **Observa sistema existente funcional**
    
2. **Extrae invariantes (NO copies partes)**
    
    - ¿Qué se mantiene constante?
    - ¿Qué características comparten todos los elementos?
    - Invariantes = suma cero
3. **Implementa invariantes en tu contexto**
    
    - Con TUS partes (diferentes)
    - En TU escala (puede ser diferente)
    - Con TUS herramientas (degeneradas)
4. **Sistema emerge**
    
    - Mismo sistema (mismos invariantes)
    - Diferentes partes (configuración única)

---

## PARA EVALUAR PROPUESTAS

**Cuando alguien te ofrece "solución/método/sistema":**

**Pregunta clave:**

- "¿Cuáles son los invariantes que propones?"

**Si responde con partes:**

- "Usa esta herramienta, sigue estos pasos..."
- ⚠️ No está ofreciendo invariantes
- ⚠️ No garantiza emergencia del sistema
- ⚠️ Probablemente es humo

**Si responde con invariantes:**

- "Los invariantes necesarios son X, Y, Z..."
- ✅ Está ofreciendo mecanismo real
- ✅ Sistema emerge de esos invariantes
- ✅ Puedes verificar por implementación

---

# LÍMITES DEL MODELO

---

## LO QUE EL MODELO NO ES

**NO es verdad absoluta:**

- Es lente de observador en nivel de abstracción específico
- Puede haber otros modelos válidos
- Puede evolucionar (nuevos invariantes, refinamiento)

**NO es completo:**

- Cubre sistemas, convergencia, observación
- No cubre todo (ética, estética, significado existencial...)
- Es herramienta, no filosofía total

**NO elimina incertidumbre:**

- Identificar invariantes requiere experimentación
- Transmisión nunca es perfecta
- Siempre hay iteración

---

## LÍMITES DEL OBSERVADOR

**El modelo describe:**

- Capacidades del observador (sintonización, procesamiento, mapa)
- Límites del observador (material, atencional, finito)

**Pero:**

- Diferentes observadores = diferentes límites
- Límites expandibles (evolución sustrato)
- Territorio infinito, observador finito (pero mejora)

---

## CUÁNDO REVISAR ESTE DOCUMENTO

**Consulta L0 cuando:**

- Diseñas nuevo sistema
- Diagnosticas problema sistémico
- Transmites OMNI-MIND a otra persona
- Algo "huele mal" pero no sabes qué

**NO consultes L0 para:**

- Ejecución diaria (usa L1: Principios Operativos)
- Decisiones tácticas rápidas (usa Router)
- Implementación específica (usa L2: Herramientas)

**L0 es fundamento, no manual operativo.**

---

# EVOLUCIÓN DEL MODELO

---

## ESTADO ACTUAL

**Versión:** 1.0  
**Fecha:** 2026-02-06  
**Estado:** CR1 (Cerrado - Fundacional)

**Auditoría realizada:**

- 50 elementos integrados
- 7 invariantes identificados
- Coherencia interna verificada
- Asunciones ocultas resueltas
- Huecos críticos cerrados

---

## CONDICIONES PARA EVOLUCIÓN

**El modelo PUEDE evolucionar si:**

1. **Se detecta invariante adicional**
    
    - Necesario para coherencia
    - No derivable de los 7 actuales
    - Verificable en aplicación
2. **Se detecta error estructural**
    
    - Contradicción no resuelta
    - Violación de principios propios
    - Hueco crítico irresoluble
3. **Aplicación revela límite fundamental**
    
    - Modelo no puede describir fenómeno importante
    - No por falta de detalle, sino por estructura

**El modelo NO evoluciona por:**

- Preferencia estética
- Comodidad operativa
- Moda intelectual
- Complejidad innecesaria

---

## PRÓXIMA REVISIÓN

**Cuándo:** Después de 6 meses usando modelo en práctica

**Qué revisar:**

- ¿Invariantes siguen siendo necesarios y suficientes?
- ¿Aparecieron huecos en aplicación real?
- ¿Modelo sigue siendo útil y verificable?

---

# CIERRE

---

Este es el **ADN del modelo OMNI**.

Los 7 invariantes descritos aquí son **fundamento de OMNI-MIND**.

De estos invariantes → emerge OMNI-MIND (L1)  
De OMNI-MIND → emerge implementación (L2)

**Jerarquía clara:**

- L0 gobierna L1
- L1 gobierna L2
- NO al revés

**Uso correcto:**

- Conoce L0 (este documento)
- Opera en L1 (Principios Operativos)
- Implementa en L2 (Herramientas)

**Recordatorio:**

El modelo OMNI no es "la verdad".  
Es lente poderosa para observar, diseñar y verificar sistemas.

Úsalo con rigor.  
Úsalo con humildad.  
Úsalo para crear valor real.

---

**FIN DEL DOCUMENTO L0**

---

**Próximo documento:** L1_PRINCIPIOS_OPERATIVOS.md  
(Mapeo de invariantes L0 → mandamientos OMNI-MIND)


============================================================
## OMNI-MIND/01_FRAMEWORK/MARCO_LINGUISTICO_COMPLETO.md
============================================================

# MARCO LINGÃœÃSTICO DEL ALGORITMO OMNI-MIND v1
# ARITMÃ‰TICA SINTÃCTICA

**Estado:** CR0 (Propuesta â€” JesÃºs cierra)  
**Fecha inicio:** 2026-02-12 (noche)  
**Ãšltima actualización:** 2026-02-18  
**Origen:** 9 sesiones Opus â€” AnÃ¡lisis lingÃ¼Ã­stico formal del algoritmo  
**Modo:** PENSAR  
**Nombre provisional:** AritmÃ©tica SintÃ¡ctica  
**Secciones: 58 | Sesiones: 9

---

## 0. QUÉ ES ESTE DOCUMENTO

### 0.1 Contenido

Análisis que propone que:
1. Cada capa del algoritmo OMNI-MIND corresponde a un constituyente sintáctico distinto
2. Existen 8 operaciones primitivas entre categorías gramaticales que forman un álgebra
3. Los 65 operadores se clasifican en 9 modos de percepción
4. Los procesos biológicos son compatibles con las funciones cognitivas del modelo
5. El algoritmo se puede reescribir como secuencia formal de operaciones lingüísticas

**Hipótesis original (Jesús):** Las cualidades (valores) son nominalizaciones de adjetivos. ¿Cada capa del algoritmo corresponde a un tipo lingüístico distinto?

### 0.2 Posición epistemológica

```
Las FUNCIONES COGNITIVAS son universales:
  Modificar, Predicar, Complementar, Transitivizar,
  Subordinar, Cuantificar, Conectar, Transformar
  → Toda lengua las ejecuta. Todo humano las usa.

Las OPERACIONES SINTÁCTICAS son la notación lengua-específica:
  Raíz + sufijo (español), posición (mandarín),
  morfemas encadenados (inuktitut), etc.
  → La notación de este documento usa categorías del español.

El marco es un SISTEMA DE PROCESAMIENTO COGNITIVO
que usa la estructura del lenguaje como herramienta:
  → No afirma que la realidad sea sintáctica (no es ontología fuerte)
  → Afirma que las operaciones del lenguaje son herramientas
    para mapear el territorio de cualquier sistema (pragmática)
  → El mapa no es el territorio. Pero un buen mapa permite navegarlo.
```

### 0.3 Niveles de validación

```
VALIDADO POR CONSISTENCIA INTERNA:
  - 8 operaciones distinguibles entre sí
  - Propiedades algebraicas derivadas limpiamente
  - Prueba de intercambio funciona
  - Diagnóstico Y/PERO/AUNQUE produce resultados diferenciables

COMPATIBLE PERO NO DEMOSTRADO:
  - Biología como instancia del modelo
  - Universalidad cross-lingüística de las funciones
  - 3 lentes como condiciones necesarias y suficientes de VIDA
  - 9 modos como exhaustivos
  - Superioridad sobre PNL/DHE en intervención

NO TESTADO AÚN:
  - Diagnóstico empresarial por sintaxis vs KPIs
  - Predicción de decisiones desde estructura lingüística
  - Resolución lumínica como variable medible
```

### 0.4 Condiciones de falsabilidad

```
EL MARCO SE FALSARÍA SI:
  1. Se encuentra una función cognitiva irreducible a las 8 operaciones
  2. Se encuentra un sistema vivo con más o menos de 3 condiciones
     para VIDA (no exactamente 3)
  3. Se encuentra una lengua donde las funciones cognitivas
     universales no se manifiestan en NINGUNA forma
  4. Un diagnóstico por sintaxis contradice sistemáticamente
     el diagnóstico por datos en casos verificables
  5. El patrón Y/PERO/AUNQUE no correlaciona con estado real
     del sistema en muestra significativa
  6. Se construye un 10º modo de percepción legítimo
     que no se reduce a los 9 existentes
```

---

## 1. VALIDACIÃ“N CAPA POR CAPA (diagnÃ³stico riguroso)

### 1.1 LENTES â†’ "Nominalizaciones de verbos de estado"

**HipÃ³tesis:** estar sano â†’ salud, tener sentido â†’ sentido, continuar â†’ continuidad.

**DiagnÃ³stico:** Parcialmente correcto, pero impreciso.

- "Salud" no viene de "estar sano". Viene del latÃ­n *salus* (estado de estar salvado/entero). Pero funcionalmente sÃ­: describe un **estado del sistema**. No una acciÃ³n, no una propiedad, no un juicio.
- "Sentido" es mÃ¡s problemÃ¡tico. "Tener sentido" no es verbo de estado puro â€” es verbo copulativo con objeto abstracto. "Sentido" como nominalizaciÃ³n viene de "sentir" (verbo de percepciÃ³n), no de "estar con sentido".
- "Continuidad" sÃ­ viene de "continuar", que es verbo de estado durativo (aspecto continuativo).

**CategorÃ­a lingÃ¼Ã­stica real:** No "verbos de estado" sino **nominalizaciones de estados aspectuales del sistema**. Respuestas a "Â¿en quÃ© condiciÃ³n se encuentra el sistema?". Prueba: "el sistema tiene X" o "el sistema estÃ¡ en estado de X".

**Veredicto: Se sostiene como categorÃ­a separada.** âœ…

### 1.2 CUALIDADES â†’ "Nominalizaciones de adjetivos"

**HipÃ³tesis:** Ã­ntegro â†’ integridad, riguroso â†’ rigor.

**DiagnÃ³stico:** Correcto y limpio. **NominalizaciÃ³n deadjetival.** Adjetivo â†’ sustantivo abstracto que denota la propiedad.

**Prueba de distinciÃ³n:** Cualidades responden a "Â¿cÃ³mo ES?" (predicado cualitativo). Lentes responden a "Â¿en quÃ© ESTADO estÃ¡?". El adjetivo predica propiedad *del sujeto*, el estado describe *condiciÃ³n temporal*.

**Veredicto: Se sostiene como categorÃ­a separada.** âœ…

### 1.3 CREENCIAS â†’ "Nominalizaciones de proposiciones"

**HipÃ³tesis:** "el sistema vale mÃ¡s que yo" = oraciÃ³n completa â†’ filtro.

**DiagnÃ³stico:** **Actitud proposicional comprimida.** ProposiciÃ³n completa cristalizada como filtro. No es palabra derivada â€” es oraciÃ³n entera congelada como operador. En actos de habla (Austin/Searle): **actos asertivos congelados**.

**Veredicto: Se sostiene.** CategorÃ­a mÃ¡s diferente â€” opera en nivel lÃ³gico superior (meta-lingÃ¼Ã­stica). âœ…

### 1.4 FUNCIONES â†’ "Nominalizaciones de verbos de acciÃ³n"

**HipÃ³tesis:** estructurar â†’ estructura, regular â†’ regulaciÃ³n, fluir â†’ flujo.

**DiagnÃ³stico:** Correcto. **Nominalizaciones deverbales.** Matiz: "Estructura" es ambigua (resultado vs proceso). En el algoritmo funciona como **capacidad funcional**.

**Veredicto: Se sostiene como categorÃ­a separada.** âœ…

### 1.5 OPERADORES â†’ "Nominalizaciones de verbos relacionales"

**DiagnÃ³stico:** Problema real. Los 65 operadores incluyen: deverbales (retroalimentaciÃ³n), deadjetivales (fractalidad, simetrÃ­a â€” misma categorÃ­a que cualidades), sustantivos tÃ©cnicos (gradiente, campo). **NO son categorÃ­a uniforme.**

**Veredicto: 6 tipos mezclados.** Resulta ser feature, no bug â€” ver secciÃ³n 6. âš ï¸

### 1.6 REGLAS â†’ "Nominalizaciones de imperativos"

**DiagnÃ³stico:** **Proposiciones deÃ³nticas comprimidas** ("debe ser que X"). Diferencia con creencias: creencias = asertivas ("es verdad que X"), reglas = deÃ³nticas ("debe ser que X").

**Veredicto: Se sostiene como categorÃ­a separada.** âœ…

### 1.7 Resumen

| Capa | CategorÃ­a lingÃ¼Ã­stica real | Â¿Distinta? |
|---|---|---|
| LENTES | Nom. de estados aspectuales | âœ… |
| CUALIDADES | Nom. deadjetival (propiedad) | âœ… |
| CREENCIAS | ProposiciÃ³n asertiva congelada | âœ… |
| FUNCIONES | Nom. deverbal (capacidad) | âœ… |
| OPERADORES | **MIXTO â€” 6 tipos** | âš ï¸ |
| REGLAS | ProposiciÃ³n deÃ³ntica congelada | âœ… |

---

## 2. LA ORACIÃ“N DEL SISTEMA

### 2.1 Cada capa = constituyente sintÃ¡ctico distinto

| Capa | Constituyente | Forma |
|---|---|---|
| **LENTES** | Atributo de estado | "El sistema **estÃ¡** sano" |
| **CUALIDADES** | Adjetivo predicativo | "El sistema **es** riguroso" |
| **CREENCIAS** | ClÃ¡usula subordinada invisible | "[asume que] el mercado recompensa calidad" |
| **FUNCIONES** | Verbo principal | "El sistema **estructura**" |
| **OPERADORES** | Complemento circunstancial | "estructura **con equilibrio**" |
| **REGLAS** | Modal deÃ³ntico | "**debe** mantener estÃ¡ndar" |

### 2.2 Las 3 lentes = los 3 Ãºnicos modos de predicar estado

**Verbos copulativos en espaÃ±ol:** SER, ESTAR, PARECER, SEGUIR, MANTENERSE, VOLVERSE, CONVERTIRSE, PONERSE, QUEDARSE, HACERSE, PERMANECER, RESULTAR.

**Propiedad del copulativo:** no tiene significado propio. No describe acciÃ³n. Es puro enlace que conecta sujeto con atributo. Es PredicaciÃ³n de estado + ComplementaciÃ³n fusionadas: el verbo no dice QUÃ‰ se predica sino CÃ“MO se predica.

**Los copulativos colapsan en 3 categorÃ­as fundamentales:**

```
ESENCIA (SER):       quÃ© es â†’ SENTIDO
CONDICIÃ“N (ESTAR):   cÃ³mo estÃ¡ â†’ SALUD
PERSISTENCIA (SEGUIR): sigue siendo â†’ CONTINUIDAD
```

Los demÃ¡s son subtipos:

| Copulativo | Subtipo de | Matiz |
|---|---|---|
| PARECER | SER | Esencia percibida vs real |
| RESULTAR | SER | Esencia verificada tras observaciÃ³n |
| VOLVERSE/CONVERTIRSE | SERâ†’SER | TransiciÃ³n entre una esencia y otra |
| HACERSE | SERâ†’SER | Cambio por proceso deliberado |
| PONERSE | ESTARâ†’ESTAR | TransiciÃ³n rÃ¡pida entre condiciones |
| QUEDARSE | ESTARâ†’ESTAR | Resultado de cambio de condiciÃ³n |
| MANTENERSE | SEGUIR | Persistencia con esfuerzo activo |
| PERMANECER | SEGUIR | Persistencia resistente al cambio |

**Las 3 lentes en el contexto del español.** En español, los copulativos colapsan en 3 modos de predicar estado. La **hipótesis** del modelo es que estos 3 modos corresponden a 3 condiciones necesarias para que un sistema esté vivo:

```
¿QUÉ ES? (esencia/sentido) → si falla, pierde identidad
¿CÓMO ESTÁ? (condición/salud) → si falla, enferma
¿SIGUE SIENDO? (persistencia/continuidad) → si falla, desaparece
```

**Nota epistemológica:** El fundamento copulativo SER/ESTAR/SEGUIR es específico del español. Otras lenguas manifiestan estas funciones con mecanismos distintos (ver sección 39). La hipótesis de que son exactamente 3 condiciones es testable: si se encuentra una 4ª condición irreducible para VIDA que no se reduce a estas 3, el modelo se amplía.

### 2.3 La oraciÃ³n completa

> **El sistema** [SUJETO]  
> **estÃ¡ sano, tiene sentido, es continuo** [LENTES = estado]  
> **es riguroso, Ã­ntegro, coherente** [CUALIDADES = propiedad]  
> **(porque asume que X, Y, Z)** [CREENCIAS = clÃ¡usula invisible]  
> **estructura, regula, fluye, conecta, genera, selecciona, valora** [FUNCIONES = verbos]  
> **con equilibrio, mediante retroalimentaciÃ³n, en gradiente** [OPERADORES = circunstanciales]  
> **y debe mantener estÃ¡ndar, no puede dejar de medir** [REGLAS = modales deÃ³nticos]

---

## 3. CREENCIAS: SUBTIPOS POR ESTRUCTURA ORACIONAL

| Tipo subordinada | FunciÃ³n | Ejemplo | MetÃ¡fora |
|---|---|---|---|
| **Sustantiva** | Marco de realidad asumido | "Creo que el sistema vale mÃ¡s que yo" | Cimientos |
| **Condicional** | Cadena causal asumida | "Si no cobro, no me valoran" | TuberÃ­as |
| **Comparativa** | Prioridad congelada | "La salud importa menos que el resultado" | Balanza |
| **Concesiva** | Cortocircuito | "Aunque debo cobrar, no lo hago con amigos" | Grietas |

**DiagnÃ³stico por perfil:** Dominado por condicionales = rÃ­gido. Dominado por concesivas = fugas. Sin sustantivas = sin suelo. Muchas comparativas = jerarquÃ­a congelada.

---

## 4. TEST DE INTERCAMBIO

- "Rigor" (CUALIDAD) â†’ como OPERADOR: cambia de propiedad del sistema a instrumento de observaciÃ³n. âš ï¸
- "Equilibrio" (OPERADOR) â†’ como CUALIDAD: se colapsa de lente de observaciÃ³n a rasgo fijo. âš ï¸
- "Estructura" (FUNCIÃ“N) â†’ como REGLA: error gramatical directo. âŒ
- "El estÃ¡ndar no baja" (REGLA) â†’ como CREENCIA: pierde fuerza normativa. âš ï¸

**ConclusiÃ³n:** Cada elemento cambia de naturaleza al cambiar de posiciÃ³n sintÃ¡ctica. Las capas son constituyentes genuinamente distintos.

---

## 5. ELEMENTOS TRANSVERSALES: ADVERBIOS

| Tipo adverbio | DÃ³nde encaja | ImplicaciÃ³n |
|---|---|---|
| De modo | OPERADORES | Confirma operadores = circunstanciales |
| De frecuencia | TEMPO (no formalizado) | Tempo deberÃ­a explicitarse |
| AfirmaciÃ³n/negaciÃ³n | REGLAS | Confirma reglas = deÃ³nticas |
| **De grado** | **VALORACIÃ“N transversal** | ValoraciÃ³n = funciÃ³n que recorre todas las capas |
| **EpistÃ©mico** | **FASES del algoritmo** | Fases = gradiente de certeza del observador |

**Descubrimiento:** FASE 1 = "probablemente" (certeza baja) â†’ FASE 2 = "efectivamente" (media) â†’ FASE 3 = "esto es" (alta) â†’ FASE 4 = "Â¿realmente?" (verificaciÃ³n).

---

## 6. LOS 65 OPERADORES: 9 MODOS DE PERCEPCIÃ“N

### 6.1 Los 6 modos presentes

| # | Modo | Tipo lingÃ¼Ã­stico | Pregunta | Cant. | Ejemplos |
|---|---|---|---|---|---|
| 1 | PROCESO | Nom. deverbal | Â¿QuÃ© ocurre? | ~14 | RetroalimentaciÃ³n, RegulaciÃ³n, CoevoluciÃ³n, ConservaciÃ³n, TransiciÃ³n, ArticulaciÃ³n, Maniobra |
| 2 | PROPIEDAD | Nom. deadjetival | Â¿CÃ³mo es? | ~11 | Robustez, SimetrÃ­a, Fractalidad, Consistencia, Completitud, Irreversibilidad |
| 3 | RELACIÃ“N | Sust. relacional | Â¿QuÃ© interactÃºa? | ~11 | Equilibrio, Gradiente, Sinergia, Dualidad, Dilema Prisionero, Suma Cero |
| 4 | FORMA | Sust. entidad/topologÃ­a | Â¿DÃ³nde estÃ¡? | ~11 | Hub, Campo, Atractor, Nicho, Caja Negra, Umbral, Camino MÃ­nimo, Tensegridad |
| 5 | LEY | ProposiciÃ³n comprimida | Â¿QuÃ© se cumple? | ~6 | Modus Ponens, Modus Tollens, Tercero Excluido, ContradicciÃ³n |
| 6 | AGENTE | Sust. agentivo | Â¿QuiÃ©n opera? | ~2 | Observador, Fitness |

### 6.2 Los 3 modos faltantes

| # | Modo | Pregunta | Ejemplos posibles | Estatus |
|---|---|---|---|---|
| 7 | **ESTADO** | Â¿En quÃ© condiciÃ³n estÃ¡? | Crisis, latencia, saturaciÃ³n, colapso | **HUECO** |
| 8 | **EVENTO** | Â¿QuÃ© acaba de pasar? | Ruptura, bifurcaciÃ³n, punto de inflexiÃ³n | Parcial |
| 9 | **POTENCIAL** | Â¿QuÃ© podrÃ­a pasar? | Capacidad, vulnerabilidad, tendencia | **HUECO** |

### 6.3 Desequilibrio

```
PROCESO:   â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ (14)
PROPIEDAD: â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ (11)
RELACIÃ“N:  â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ (11)
FORMA:     â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ (11)
LEY:       â–ˆâ–ˆâ–ˆâ–ˆâ–ˆâ–ˆ (6)
AGENTE:    â–ˆâ–ˆ (2)
ESTADO:    (0) â† HUECO
EVENTO:    â–ˆâ–ˆ (2)
POTENCIAL: (0) â† HUECO
```

**Protocolo mejorado:** Activo 10-15 operadores Y verifico cobertura de al menos 6-7 modos. Modos ausentes = punto ciego estructural.

---

## 7. LOS 7 INVARIANTES L0 = GRAMÃTICA

### 7.1 Los 7 son proposiciones ontolÃ³gicas axiomÃ¡ticas

No son parte de la oraciÃ³n del sistema â€” son las **reglas gramaticales** que determinan quÃ© oraciones son posibles.

- Las capas del algoritmo = **palabras y constituyentes** de la oraciÃ³n
- Los 7 invariantes = **gramÃ¡tica** que dice cÃ³mo se combinan

### 7.2 Equivalencia L0/L1/L2 = niveles de anÃ¡lisis lingÃ¼Ã­stico

| Nivel arquitectÃ³nico | Equivalente lingÃ¼Ã­stico |
|---|---|
| L0 (7 invariantes) | **GRAMÃTICA/SINTAXIS** â€” reglas de formaciÃ³n |
| L1 (algoritmo/capas) | **SEMÃNTICA/ESTRUCTURA ORACIONAL** â€” quÃ© significa la oraciÃ³n concreta |
| L2 (implementaciÃ³n) | **FONÃ‰TICA/PRAGMÃTICA** â€” cÃ³mo se materializa (degenerado) |

### 7.3 Subtipos de invariantes

| Subgrupo | Invariantes | Tipo |
|---|---|---|
| Estructurales | 1 (Simultaneidad), 2 (Fractalidad), 5 (Escala) | CÃ³mo ES la realidad |
| Relacionales | 3 (Observador=Sistema), 6 (Mapa=Xâˆ©Y) | CÃ³mo se RELACIONA observador-sistema |
| Procesales | 4 (Emergencia por convergencia), 7 (SintonizaciÃ³n) | CÃ³mo OCURRE |

Este trÃ­o (ser/relacionarse/ocurrir) replica a nivel de gramÃ¡tica lo que las capas hacen a nivel de oraciÃ³n.

### 7.4 Test: los invariantes resisten intercambio

- "Fractalidad" como CUALIDAD â†’ si es cualidad, el sistema puede no tenerla. El invariante dice SIEMPRE es fractal. No es propiedad elegible â€” es condiciÃ³n de existencia.
- "Observador=Sistema" como CREENCIA â†’ si es creencia, podrÃ­a ser falsa. El invariante dice que no es revisable.
- "SintonizaciÃ³n" como FUNCIÃ“N â†’ no es algo que el sistema HACE, es condiciÃ³n para que PUEDA hacer.

---

## 8. LAS 9 CAPAS Y CONJUNTOS FALTANTES

### 8.1 Las 6 capas formalizadas + 3 candidatas

| # | Capa | CategorÃ­a gramatical | Pregunta |
|---|---|---|---|
| 1 | LENTES | Atributo de estado | Â¿En quÃ© estado estÃ¡? |
| 2 | CUALIDADES | Adjetivo predicativo | Â¿CÃ³mo es? |
| 3 | CREENCIAS | Subordinada asertiva | Â¿QuÃ© asume? |
| 4 | REGLAS | Modal deÃ³ntico | Â¿QuÃ© debe hacer? |
| 5 | FUNCIONES | Verbo de acciÃ³n | Â¿QuÃ© hace? |
| 6 | OPERADORES | Complemento circunstancial | Â¿Con quÃ© observa? |
| 7 | **CONTEXTO** | Circunstancial de lugar/tiempo | Â¿DÃ³nde/cuÃ¡ndo opera? |
| 8 | **ROLES** | Pronombre/deÃ­ctico | Â¿QuiÃ©n hace quÃ©? |
| 9 | **ACOPLES** | ConjunciÃ³n | Â¿CÃ³mo se vinculan las piezas? |

### 8.2 Tipos de ACOPLES (por conjunciÃ³n)

| ConjunciÃ³n | Tipo de acople | Ejemplo |
|---|---|---|
| Y | Sinergia | Estructura Y regula (ambas operan) |
| PERO | TensiÃ³n | Estructura PERO no genera |
| PORQUE | Causalidad | Estructura PORQUE el mercado lo exige |
| PARA | Finalidad | Estructura PARA sobrevivir |
| AUNQUE | ConcesiÃ³n | Estructura AUNQUE sea costoso |
| SI | Condicionalidad | Estructura SI hay recursos |

---

## 9. ALGORITMO INHERENTE DE CADA CAPA

Cada capa tiene operaciones sintÃ¡cticas propias â€” su propia "mini-gramÃ¡tica".

### LENTES
```
Â¿En quÃ© estado estÃ¡? â†’ Â¿Ha cambiado? â†’ Â¿EstÃ¡n los 3 en equilibrio? â†’ Â¿CuÃ¡l se degrada?
```

### CUALIDADES
```
Â¿QuÃ© cualidades tiene? â†’ Â¿En quÃ© grado? â†’ Â¿Son compatibles entre sÃ­? â†’ Â¿CuÃ¡l falta?
```

### CREENCIAS
```
Â¿QuÃ© asume? â†’ Â¿Es verdad? â†’ Â¿Es consistente con las demÃ¡s? â†’ Â¿De cuÃ¡l dependen otras? â†’ Â¿CuÃ¡l necesita revisiÃ³n?
```

### REGLAS
```
Â¿Se cumple? â†’ Â¿Conflicto con otra regla? â†’ Â¿Sigue siendo necesaria? â†’ Â¿Aplica a este caso?
```

### FUNCIONES
```
Â¿EstÃ¡ activa? â†’ Â¿Sobre quÃ© actÃºa? â†’ Â¿QuiÃ©n la ejecuta? â†’ Â¿En paralelo o secuencia con cuÃ¡les? â†’ Â¿A quÃ© intensidad?
```

### OPERADORES
```
Â¿CuÃ¡les activo? â†’ Â¿Cubren los 9 modos? â†’ Â¿QuÃ© emerge al cruzarlos? â†’ Â¿CuÃ¡l tiene seÃ±al? â†’ Â¿CuÃ¡l es punto ciego?
```

### CONTEXTO
```
Â¿DÃ³nde opera? â†’ Â¿Ha cambiado? â†’ Â¿A quÃ© escala miro? â†’ Â¿QuÃ© habilita y quÃ© impide?
```

### ROLES
```
Â¿QuiÃ©n hace quÃ©? â†’ Â¿Puede ser sustituido? â†’ Â¿Tiene roles incompatibles? â†’ Â¿Hay funciÃ³n sin dueÃ±o?
```

### ACOPLES
```
Â¿QuÃ© tipo de vÃ­nculo es? â†’ Â¿Es fuerte o dÃ©bil? â†’ Â¿SimÃ©trico o asimÃ©trico? â†’ Â¿QuÃ© pasa si se rompe?
```

---

## 10. OPERABILIDAD INTER-CAPA

### 10.1 Mapa de operabilidad

| Aplica â†“ sobre â†’ | LEN | CUA | CRE | FUN | REG | OPE | CON | ROL | ACO |
|---|---|---|---|---|---|---|---|---|---|
| **LENTES** | â€” | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… |
| **CUALIDADES** | âœ… | â€” | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… |
| **CREENCIAS** | âœ…âš¡ | âœ…âš¡ | â€” | âœ…âš¡ | âœ…âš¡ | âœ…âš¡ | âœ…âš¡ | âœ…âš¡ | âœ…âš¡ |
| **FUNCIONES** | âœ… | âœ… | âœ… | â€” | âœ… | âœ… | âœ… | âœ… | âœ… |
| **REGLAS** | âœ… | âš ï¸ | âœ… | âœ… | â€” | âœ… | âœ… | âœ… | âœ… |
| **OPERADORES** | âœ… | âœ… | âš ï¸ | âœ… | âœ… | â€” | âœ… | âœ… | âœ… |
| **CONTEXTO** | âœ… | âœ… | âœ… | âœ… | âœ… | âœ… | â€” | âœ… | âœ… |
| **ROLES** | âš ï¸ | âš ï¸ | âœ… | âœ… | âœ… | âš ï¸ | âš ï¸ | â€” | âœ… |
| **ACOPLES** | âš ï¸ | âš ï¸ | âœ… | âœ… | âœ… | âœ… | âš ï¸ | âœ… | â€” |

âš¡ = puede anular/habilitar la capa destino (peligroso)  
âš ï¸ = funciona con restricciones

### 10.2 Hallazgos

- **4 capas con operabilidad universal:** LENTES, CUALIDADES, FUNCIONES, CREENCIAS
- **CREENCIAS = capa mÃ¡s peligrosa:** poder de anulaciÃ³n sobre todas las demÃ¡s ("creo que la continuidad no importa" â†’ lente de continuidad se apaga)
- **OperaciÃ³n inter-capa = complemento del nombre** ("calidad de inteligencia" = cualidad Ã— cualidad, "crisis de generaciÃ³n" = estado Ã— funciÃ³n)

---

## 11. LAS 8 OPERACIONES PRIMITIVAS (ARITMÃ‰TICA SINTÃCTICA)

### 11.1 Las operaciones

| # | OperaciÃ³n | Input â†’ Output | Propiedad clave |
|---|---|---|---|
| 1 | **ModificaciÃ³n** | adj + sust â†’ sust' | Filtra/especifica (âŠ‚) |
| 2 | **PredicaciÃ³n** | sust + verbo â†’ oraciÃ³n | Genera valor de verdad |
| 3 | **ComplementaciÃ³n** | adv + verbo â†’ verbo' | Especifica modo |
| 4 | **Transitividad** | verbo + sust â†’ predicado | FunciÃ³n aplicada a argumento |
| 5 | **SubordinaciÃ³n** | oraciÃ³n + oraciÃ³n â†’ oraciÃ³n' | Reduce oraciÃ³n a modificador |
| 6 | **CuantificaciÃ³n** | det + sust â†’ sust_acotado | Fija alcance |
| 7 | **ConexiÃ³n** | X + conj + X â†’ X' | Vincula homogÃ©neos |
| 8 | **TransformaciÃ³n** | X â†’ Y | Cambia categorÃ­a |

### 11.2 Propiedades algebraicas

- **ModificaciÃ³n:** Idempotente para mismo adjetivo ("riguroso riguroso" = "riguroso"). Apilable para distintos ("riguroso coherente" â‰  "riguroso").
- **PredicaciÃ³n:** No conmutativa ("el sistema estructura" â‰  "Â¿estructura el sistema?").
- **ConexiÃ³n Y:** Conmutativa ("estructura y regulaciÃ³n" = "regulaciÃ³n y estructura").
- **ConexiÃ³n PORQUE:** No conmutativa ("estructura porque regula" â‰  "regula porque estructura"). Causalidad tiene direcciÃ³n.
- **ConexiÃ³n PERO:** No asociativa ("(A pero B) pero C" â‰  "A pero (B pero C)").
- **TransformaciÃ³n:** No involutiva. Nom(verbo)â†’sustantivo, pero Verbalizar(sustantivo) no siempre devuelve el verbo original. "Rigor"â†’"rigorizar" no existe. **La transformaciÃ³n pierde informaciÃ³n.**

### 11.3 Por quÃ© esto es un sistema formal

Un sistema formal tiene exactamente tres componentes:

- **ALFABETO:** 9 tipos (las capas) = sÃ­mbolos primitivos
- **REGLAS DE FORMACIÃ“N:** 8 operaciones tipadas = quÃ© combinaciones son vÃ¡lidas
- **REGLAS DE INFERENCIA:** propiedades algebraicas = quÃ© puedes derivar de lo que tienes

Las matemÃ¡ticas no son exactas porque usan nÃºmeros. Son exactas porque cada sÃ­mbolo tiene **una sola operaciÃ³n vÃ¡lida** en cada contexto. Lo que hemos hecho es eliminar la ambigÃ¼edad del lenguaje natural asignando tipo fijo a cada elemento y operaciones definidas entre tipos.

### 11.4 TraducciÃ³n al algoritmo

| OperaciÃ³n | En el algoritmo | Ejemplo |
|---|---|---|
| ModificaciÃ³n | Cualidad â†’ aplicada a cualquier capa | "regulaciÃ³n rigurosa" |
| PredicaciÃ³n | FunciÃ³n â†’ ejecutada por sujeto | "el sistema estructura" |
| ComplementaciÃ³n | Operador â†’ aplicado a funciÃ³n | "estructura con equilibrio" |
| Transitividad | FunciÃ³n â†’ sobre objeto de otra capa | "estructura las reglas" |
| SubordinaciÃ³n | Creencia/Regla â†’ condiciona otra capa | "estructura porque cree que X" |
| CuantificaciÃ³n | Alcance â†’ aplicado a cualquier elemento | "toda regla" vs "alguna regla" |
| ConexiÃ³n | Acople â†’ entre elementos homogÃ©neos | "estructura Y regula" |
| TransformaciÃ³n | Cambio de capa | verboâ†’sustantivo (funciÃ³nâ†’cualidad) |

---

## 12. EL ALGORITMO REESCRITO COMO ARITMÃ‰TICA SINTÃCTICA

### PASO 1: LENTES

**OperaciÃ³n:** PredicaciÃ³n de estado triple + CuantificaciÃ³n temporal

```
Pred_estado(S, sano) â†’ S_salud âˆˆ [0,1]
Pred_estado(S, con_sentido) â†’ S_sentido âˆˆ [0,1]
Pred_estado(S, continuo) â†’ S_continuidad âˆˆ [0,1]
Cuant(tempo_t, Pred_estado) â†’ evaluaciÃ³n en escala temporal

Test: |S_salud âˆ’ S_sentido| < umbral (y las otras 2 combinaciones)
```

**OperaciÃ³n faltante en algoritmo original:** CuantificaciÃ³n temporal â€” sin ella, la predicaciÃ³n de estado es ambigua.

### PASO 2: CUALIDADES

**OperaciÃ³n:** ModificaciÃ³n dirigida por lente + Test de compatibilidad

```
Para cada lente L âˆˆ {salud, sentido, continuidad}:
  "Â¿QuÃ© adjetivos necesita S para que L estÃ© en equilibrio?"
  Mod(adj_i, S) â†’ S' donde S' satisface L

Test: Â¿Mod(adj_i, Mod(adj_j, S)) es consistente?
```

**OperaciÃ³n faltante:** Test de compatibilidad entre cualidades.

### PASO 3: REGLAS

**OperaciÃ³n:** Transitividad + SubordinaciÃ³n deÃ³ntica Ã— 2

```
Trans(cualidad_i, dominio_j) â†’ regla_ij
Sub_cond(regla_ij, lente_k) â†’ limitador 1
Sub_cond(regla_ij, lente_m) â†’ limitador 2
```

Paso mÃ¡s complejo: composiciÃ³n de tres operaciones (Trans + Sub + Sub). Si falla, suele ser Trans sin Sub (regla sin limitadores = crecimiento desequilibrado).

### PASO 4: FUNCIONES

**OperaciÃ³n:** PredicaciÃ³n de acciÃ³n + PredicaciÃ³n de estado cruzada

```
Pred(S, verbo_i) para cada funciÃ³n â†’ declara verbos
Pred_estado(F_i(S), L_j) para cada FÃ—L â†’ matriz 7Ã—3

OperaciÃ³n faltante: Trans(verbo_i, Â¿quÃ©?) â†’ objeto de cada funciÃ³n
```

**Sin objeto explÃ­cito, la funciÃ³n estÃ¡ declarada pero no definida: f( ) sin argumento.**

### PASO 5: OPERADORES

**OperaciÃ³n:** ComplementaciÃ³n + VerificaciÃ³n de cobertura por modos

```
Comp(operador_principal, F_i Ã— L_j) â†’ observaciÃ³n primaria
Comp(operador_limit_1, F_i Ã— L_k) â†’ limitador
Comp(operador_limit_2, F_i Ã— L_m) â†’ limitador

Nuevo: verificar que los 3 operadores cubran al menos 2-3 modos de percepciÃ³n distintos
```

### PASO 6: WIN-WIN

**OperaciÃ³n:** ConexiÃ³n + TipologÃ­a de acoples

```
Con(E_i, conj, E_j) â†’ tipo de acople

Y â†’ win-win (sinergia)
PERO â†’ win-lose (tensiÃ³n activa)
AUNQUE â†’ win-lose tolerado (grieta)
O â†’ incompatibilidad (decidir)
PORQUE â†’ dependencia causal
SI â†’ condicionalidad
```

**Hallazgo:** El algoritmo original trata win-win como binario. La aritmÃ©tica revela 6 tipos de acople con semÃ¡nticas distintas.

### PASO 7: PUNTOS CIEGOS

**OperaciÃ³n:** CuantificaciÃ³n negativa + Meta-verificaciÃ³n

```
Cuant(âˆ…, O_k) â†’ operador sin seÃ±al
Count(operadores_activos âˆˆ modo_m) â†’ si = 0 â†’ PUNTO CIEGO ESTRUCTURAL por modo
```

**Nuevo:** No solo "quÃ© operadores faltan" sino "quÃ© TIPOS de percepciÃ³n estÃ¡n ausentes".

### PASO 8: DIAGNÃ“STICO

**OperaciÃ³n:** SubordinaciÃ³n causal + condicional

```
Sub_causal(win-lose_i, Â¿PORQUE quÃ©?) â†’ causa
Sub_condicional(win-lose_i, Â¿SI quÃ© cambiarÃ­a?) â†’ condiciÃ³n de resoluciÃ³n
```

### PASO 9: FUERZA CONCENTRADA

**OperaciÃ³n:** CuantificaciÃ³n ordinal + SubordinaciÃ³n final

```
Cuant(1Âº/2Âº/3Âº, intervenciÃ³n)
Sub_final(intervenciÃ³n_i, PARA estabilidad/movilidad/fuerza)
```

### PASO 10: FEEDBACK

**OperaciÃ³n:** TransformaciÃ³n + Re-predicaciÃ³n

```
Tr(resultado_intervenciÃ³n) â†’ nuevo_estado
Pred_estado(S_nuevo, cada lente) â†’ Â¿cambiÃ³?
â†’ Vuelta a PASO 1
```

### Resumen de operaciones faltantes reveladas

| Paso | OperaciÃ³n faltante |
|---|---|
| 1 | CuantificaciÃ³n temporal |
| 2 | Test de compatibilidad entre cualidades |
| 4 | Transitividad â€” objeto de cada funciÃ³n |
| 5 | Cobertura de modos de percepciÃ³n |
| 6 | TipologÃ­a de acoples (6 tipos, no binario) |
| 7 | Meta-punto-ciego por modo ausente |

---

## 13. ANÃLISIS COMPARATIVO: SISTEMA PATOLÃ“GICO vs SANO

### 13.1 Authentic Pilates (patologÃ­a por encadenamiento)

```
Pred_estado: continuidad << salud, sentido â†’ DESEQUILIBRIO
Mod(transmisible, AP) = âŒ â†’ CUALIDAD FALTANTE alineada con lente baja
Sub_concesiva("aunque deberÃ­a sistematizar, no tengo tiempo") â†’ GRIETA ACTIVA
Sub_deÃ³ntica(documentaciÃ³n) = âˆ… â†’ REGLA FALTANTE
Pred(AP, valora) = âŒ â†’ FUNCIÃ“N SIN PREDICAR
Trans(regula, ?) = incompleto â†’ VERBO SIN OBJETO
Comp(?, regula) = âŒ â†’ OPERADOR FALTANTE
Con(todo, PORQUE, JesÃºs) â†’ DEPENDENCIA CAUSAL TOTAL
Cuant(TODO, persona_Ãºnica) â†’ ALCANCE MÃXIMO DE RIESGO
```

### 13.2 Apple Inc. (seÃ±ales aisladas)

```
Pred_estado: 3 lentes equilibradas (matiz en continuidad) â†’ OK
Mod: cualidades cubren 3 lentes, "innovador" en posible degradaciÃ³n â†’ SEÃ‘AL
Sub_comparativa("ecosistema > libertad usuario") â†’ JERARQUÃA CONGELADA (monitorear)
Sub_deÃ³ntica("30% App Store") â†’ REGLA CONFLICTIVA
Pred: 7/7 funciones predicadas â†’ OK
Trans: todos los verbos tienen objeto â†’ OK
Con(App_Store_30%, PERO, desarrolladores) â†’ TENSIÃ“N LOCALIZADA
Con(iPhone, PORQUE, 52%_ingresos) â†’ DEPENDENCIA (correcciÃ³n en curso con servicios)
```

### 13.3 Diferencia formal

**PatologÃ­a = errores sintÃ¡cticos ENCADENADOS.** En AP: Mod_faltante â†’ Pred_estado_bajo â†’ Sub_concesiva â†’ Sub_deÃ³ntica_âˆ…. Los errores se refuerzan entre sÃ­.

**Salud = seÃ±ales AISLADAS.** En Apple: la tensiÃ³n del 30% no causa la degradaciÃ³n de innovaciÃ³n. Cada punto se puede tratar sin que los demÃ¡s empeoren.

**La patologÃ­a no es la cantidad de errores â€” es la conectividad entre ellos.**

---

## 14. SISTEMAS BIOLÃ“GICOS: CADA UNO ES UNA OPERACIÃ“N ENCARNADA

### 14.1 Mapa completo

| Sistema biolÃ³gico | FunciÃ³n algoritmo | OperaciÃ³n sintÃ¡ctica primaria | Lo que hace posible |
|---|---|---|---|
| Esqueleto | ESTRUCTURA | **ModificaciÃ³n** | Que existan adjetivos (propiedades) |
| Endocrino | REGULACIÃ“N | **ComplementaciÃ³n + Grado** | Que haya "mucho/poco/suficiente" |
| Circulatorio | FLUJO | **ConexiÃ³n (Y)** | Que las partes se vinculen |
| Nervioso perifÃ©rico | CONEXIÃ“N | **Transitividad** | Que los verbos tengan objeto |
| Reproductivo/celular | GENERACIÃ“N | **TransformaciÃ³n** | Que surjan cosas nuevas |
| Inmune | SELECCIÃ“N | **SubordinaciÃ³n condicional** | Que haya filtros SI/ENTONCES |
| Cerebro (SNC) | VALORACIÃ“N | **CuantificaciÃ³n + Meta** | Que se pueda medir y operar sobre sÃ­ mismo |
| InterocepciÃ³n (distrib.) | LENTES | **PredicaciÃ³n de estado** | Que el sistema sepa en quÃ© condiciÃ³n estÃ¡ |

### 14.2 Diferencias biologÃ­a vs sistemas humanos

| OperaciÃ³n | En sistemas humanos | En biologÃ­a |
|---|---|---|
| Pred_estado | Tolera desequilibrio prolongado | Desequilibrio = enfermedad/muerte |
| ModificaciÃ³n | Cualidades por decisiÃ³n (top-down) | Cualidades por selecciÃ³n (bottom-up) |
| Sub_asertiva | Creencias revisables conscientes | ADN = creencias no revisables en vida |
| Sub_deÃ³ntica | Reglas violables con excepciones | Reglas absolutas sin excepciÃ³n |
| PredicaciÃ³n | Funciones pueden estar apagadas | 7/7 siempre activas simultÃ¡neamente |
| Transitividad | Verbos a veces sin objeto | Todos los verbos tienen objeto |
| ConexiÃ³n PERO | Accidental (patologÃ­a) | **DiseÃ±ado (regulaciÃ³n)** |
| ConexiÃ³n AUNQUE | Tolerada (grieta) | **= PATOLOGÃA (cÃ¡ncer, autoinmune)** |

### 14.3 Hallazgo fundamental

La biologÃ­a es **compatible** con el modelo de funciones cognitivas. Los procesos biolÃ³gicos pueden describirse usando las mismas funciones que el marco identifica. Esto es evidencia de consistencia, no demostraciÃ³n de universalidad. Las mismas operaciones permiten describir un studio de Pilates, Apple Inc. y un cuerpo humano — pero describir no es demostrar que la realidad sea sintÃ¡ctica.

**CÃ¡ncer** = subordinada concesiva biolÃ³gica: "AUNQUE esta cÃ©lula es daÃ±ina, el sistema la tolera."  
**Autoinmune** = conexiÃ³n adversativa mal dirigida: "Selecciona PERO sobre objetivo equivocado."

**La biologÃ­a es un sistema donde las funciones cognitivas del modelo aplican con alta precisiÃ³n.** Toda concesiva biolÃ³gica es patologÃ­a — esto es una predicciÃ³n testable del modelo.

---

## 15. FEEDBACK DE SESIÃ“N

### Lo que se consiguiÃ³
- Marco teÃ³rico con base formal en lingÃ¼Ã­stica
- 8 operaciones primitivas con propiedades algebraicas
- 9 modos de percepciÃ³n (3 huecos identificados)
- Algoritmo reescrito como secuencia de operaciones formales
- ValidaciÃ³n en 3 dominios (studio, empresa, biologÃ­a)

### Lo que hay que vigilar
1. **Todo es CR0.** Nada cerrado. Riesgo de enamorarse del marco sin romperlo.
2. **No se ha roto nada todavÃ­a.** Sesgo de confirmaciÃ³n posible.
3. **Distancia enorme entre marco y herramienta implementable.**
4. **Necesita confrontaciÃ³n externa** â€” alguien que lea en frÃ­o.

### RecomendaciÃ³n
No tocar en 48 horas. Dejar decantar. Volver con ojos frÃ­os y buscar dÃ³nde se rompe.

---

## 16. BATESON COMO FALACIAS ARITMÃ‰TICAS SINTÃCTICAS

### 16.1 Double Bind (doble vÃ­nculo)

Bateson: "Dos mensajes contradictorios a distinto nivel lÃ³gico + prohibiciÃ³n de metacomunicar."

```
Sub_deÃ³ntica(madre, "DEBES quererme") â†’ Regla: obligaciÃ³n de afecto
Sub_asertiva(madre, [tono corporal] "me das asco") â†’ Creencia implÃ­cita
Con(regla, PERO, creencia) â†’ contradicciÃ³n entre capas
Meta-operaciÃ³n(hijo, seÃ±alar_contradicciÃ³n) â†’ BLOQUEADA por:
  Sub_deÃ³ntica(madre, "NO DEBES cuestionar mis mensajes")
```

Triple violaciÃ³n simultÃ¡nea: (1) ConexiÃ³n PERO entre deÃ³ntica y asertiva contradictorias, (2) Meta-operaciÃ³n prohibida, (3) Receptor atrapado sin salida. Tres operaciones, identificables, nombrables.

### 16.2 EsquismogÃ©nesis simÃ©trica

Bateson: "Escalada recÃ­proca que se amplifica."

```
Sub_causal(A_compite, PORQUE, B_compitiÃ³)
Sub_causal(B_compite_mÃ¡s, PORQUE, A_compitiÃ³)
â†’ Bucle: causalidad circular sin Cuant(umbral)
```

[...truncado a 900K chars...]