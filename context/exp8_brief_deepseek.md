**BRIEFING PERSONALIZADO — AUDITORÍA DE ARQUITECTURA TÉCNICA**
**Auditor:** DeepSeek V3.2 (Arquitectura Técnica)
**Fecha:** 2026-03-12
**Sistema:** OMNI-MIND v4 — Sistema Cognitivo Completo

---

## 1. CONTEXTO DEL SISTEMA — ESTADO REAL DE IMPLEMENTACIÓN

### Infraestructura Actual

**Producción:** Supabase `cptcltizauzhzbwxcdft` — `https://cptcltizauzhzbwxcdft.supabase.co`
**Staging:** Supabase `jbfiylwbgxglqwvgsedh` (authentic-pilates). 45 migraciones + 98 funciones desplegadas. ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY

**Deploy script:** `./scripts/deploy.sh staging|prod [--only fn] [--migrations-only] [--functions-only]`

**Bootstrap migration:** `00000000000000_bootstrap_base_tables.sql` — 12 tablas base pre-migración

**Edge Functions:** Deno/TypeScript, desplegadas con `supabase functions deploy <name> --no-verify-jwt`

**Comunicación entre agentes:** SOLO stigmérgia via tabla `marcas_estigmergicas` — nunca llamadas directas

**LLM:** Todas las llamadas via `llm-proxy` Edge Function (soporta haiku/sonnet con fallback)

### Enjambres Activos

1. **IAS** (Pipeline diagnóstico): ~10 agentes, capas 1-5, funcional
2. **Diseño** (Meta-diseño): 18 agentes, capas 1-6, E2E funcional
3. **Chief of Staff**: Pipeline dual superficial+profundo
4. **Mejora Continua**: 3 agentes (detector, procesador, basal), capas 1-3, operativo. Enjambre ID dinámico (buscar por nombre='mejora_continua')

### Pipeline Chat Continuo (orquestador-chief)

**Turno 0 ENCUADRE** (~500ms): Pregunta instantánea de encuadre (código puro). Parseadores + profundo se disparan en background via pg_net

**Ruta A INIT ASYNC** (~400ms): Cambio de tema o cola null → fire-and-forget (4 parseadores + profundo via pg_net) + pregunta encuadre instantánea. Rutas: `init_async` / `reset_async`

**Post-encuadre** (~12-15s): Lee parseador marcas. Build cola + emite 2 preguntas. Entra tras `ultimo_tipo === "encuadre" || "init_async"` (sin check esCambioTema)

**RUTA C CONTINUA (turno 2+)**: Flujo sin fin. Superficial + profundo en paralelo. RUTA B eliminada
  - Cola de preguntas con priorizarCola() inteligente (gravedad, fuente, overlap, contexto emocional)
  - Profundo inyecta preguntas en cola (fuente="profundo", gravedad="critico")
  - Cuando profundo listo → `cola_profundo_continuo` (respuesta + preguntas continuas)
  - Cola vacía → regeneración via parseadores async → `cola_regen`
  - Auto-re-dispatch profundo tras fallo o 3 turnos idle

**Rutas:** `encuadre` → `post_encuadre` → `cola` / `cola_modo` / `cola_profundo_continuo` / `cola_vacia_esperando` / `cola_regen` / `init_async` / `reset_async`

**Estado continuo:** `profundo_emitidos` (int), `ultimo_profundo` (obj), `profundo_dispatch_total` (max 8), `profundo_turnos_sin_dispatch`, `intencion`, `modo_activo`, `modo_historia`

**Router de modos** (Fase 6): `detectarIntencion()` → 5 tipos (expandir/decidir/diagnosticar/ejecutar/auditar). `determinarModo()` → 9 modos via (intención × profundoTerminado × mcmSuficiente). Modos que interceptan cola: escucha (respuesta corta), ejecutar_lite (solo criticas), auditar_recoger

**Verbalizador:** 6 prompts por modo (diagnosticar/confrontar/elaborar/responder/ejecutar_full/auditar_emitir). Lee modo de marca sintesis (estigmergia)

**detectCambioTema**: Requiere 3+ inputs acumulados, threshold 0.9 (90%+ keywords nuevas). STOP words incluyen verbos conversacionales (quiero, tengo, estoy, necesito, etc.)

**CRÍTICO:** NO despachar profundos concurrentes — el verbalizador falla por rate limiting del LLM. Despachar solo tras completar/fallar el anterior

**profundo-runner:** `listo` solo true si verbalizador exitoso Y respuesta no vacía. `fallido: true` si verbal falla

**Profundo:** ~55-60s por ciclo. Max 5 emitidos, max 8 dispatches por sesión

### Fase 6: Router Modos Conversacionales + Fix Telemetría (completada)

**Paso 0:** 8x `await` añadidos. Verbalizador migrado al SO (chequearSeñales, registrarMétrica, conRetry). 0 log_operaciones directo

**Paso 1:** `detectarIntencion()` reemplaza `clasificarIntencion()`. 5 intenciones: expandir, decidir, diagnosticar, ejecutar, auditar

**Paso 2:** `determinarModo()` → 9 modos. Lee mcm_suficiente del profundo. Persistido en estado

**Paso 3:** Switch por modo en RUTA C. escucha (0 preguntas), ejecutar_lite (solo críticas), auditar_recoger. Detección cambio intención mid-sesión

**Paso 4:** 6 system prompts por modo en verbalizador. Lee modo de marca sintesis (estigmergia)

### Fase 7: Agente Implementador Autónomo (completada)

**Pipeline local:** Briefing YAML → SQL → archivos → deploy → tests → regresión → prod (no Edge Function)

**Archivos nuevos:** `specs/briefing-schema.yaml`, `specs/briefing-template.yaml`, `CLAUDE.md`, `tests/regresion.sh`, `scripts/ejecutar-briefing.sh`

**Tabla nueva:** `cola_mejoras` (migración 20260227020000). Helper: `_shared/cola_mejoras.ts` (`escribirMejora()`)

**macOS compat:** perl `ms_now()`, poll-based timeout fallback (sin `timeout`/`gtimeout`), env vars para perl substitution

**REST API:** Tablas con acentos → URL encoding (`m%C3%A9tricas`, `se%C3%B1ales`). LLM-proxy campos: `mensajes` (no messages), `modelo` (no model)

**Regresión:** 6 tests, 6/6 pasan prod. Staging 4/6 (falta ANTHROPIC_API_KEY)

### Fase 1.1 — Gateway API del Cerebro (2 marzo 2026)

**Migración:** `20260302060000_fase1_1_gateway.sql` — 4 tablas nuevas + seed data
- `tenants` (3 tenants: consola/exo-pilates/exo-fisio)
- `metering` (telemetría avanzada por request)
- `capability_registry` (22 capabilities: 12 activas + 10 disabled futuras — actualizada en 1.2)
- `tareas_async` (cola async con polling)

**Edge Function nueva:** `gateway/index.ts` (~370 líneas)
- **Auth:** X-API-Key header → lookup en tenants → estado activo
- **Manifest:** Cada tenant tiene lista de capabilities permitidas. `["*"]` = wildcard (consola)
- **Rate limiting:** Contra DB (metering count últimas 24h vs rate_limit_dia)
- **Circuit breaker:** 3 fallos → open (30s cooldown → half-open → retry)
- **Routing:** capability_registry mapea capability → edge_function
- **Metering:** Telemetría JSONB en cada request (gateway_overhead_ms, input_length, circuit_state, edge_function, etc.)
- **Modo sync:** Ejecuta y espera resultado. Timeout 120s via AbortController
- **Modo async:** Crea tarea + self-dispatch (fire-and-forget fetch al gateway con flag _internal_process). Polling via GET ?request_id=
- **Health check:** GET sin params → 200 healthy
- **Graceful degradation:** 5 niveles (todo OK → timeout → 503 → skip rate limit → health only)

### Fase 1.2 — Catálogo de Capacidades (2 marzo 2026)

**Migración:** `20260302070000_fase1_2_catalogo_capacidades.sql`
- Elimina 8 capabilities falsas del seed 1.1 (wrappers que ejecutaban el mismo pipeline)
- Renombra `ias_analisis` → `ias_completo`
- Inserta 12 capabilities reales: 1 IAS + 5 diseño + 5 observabilidad + 1 propiocepción
- 10 capabilities disabled futuras (3 IAS granulares + 7 originales)
- Actualiza manifests: pilates 8 caps, fisio 4 caps

**Patch gateway:** `executeCapability()` expandido (~80 líneas, antes ~30)
- **Ambassador pattern:** Capabilities GET (dashboard-api) traducidas desde POST del consumidor
- **Diseño route mapping:** `config.ruta` determina campos trigger (A=input, B=ciclo_id, C=aprobado, D=verificar, E=respuestas)
- **dashboard-api decidir:** POST con query params especiales
- Preserva AbortController 120s timeout en todos los paths

### Fase 1.3 — Metering y Coste (2 marzo 2026)

**Migración:** `20260302080000_fase1_3_metering_coste.sql`. Tabla `metering_agregados` (tenant_id, periodo, periodo_inicio/fin, totales, by_capability JSONB, telemetry JSONB). UNIQUE(tenant_id, periodo, periodo_inicio)

**Patch orquestador-ias:** Propagación de coste real desde tabla `métricas`
- Query `métricas` por `coste_usd > 0` desde timestamp start del ciclo
- Suma `coste_usd`, `tokens_in`, `tokens_out` → añadidos a respuesta JSON
- Resultado real: ~$0.10-0.12 por llamada IAS, ~32K tokens_in, ~15K tokens_out

**Patch orquestador-diseno:** Misma propagación, helper `sumarCoste()` reutilizado en 5 puntos de retorno (rutas A/B/C/D/E)

**Patch gateway:** 4 cambios
- `executeCapability()` recibe `supabase` como primer parámetro + `execStart` timestamp
- Fallback cost: si `result.cost_usd === 0`, query directa a `métricas`. Campo `_cost_source` para trazabilidad
- Metering lee `tokens_in || tokens_entrada` (backward compat)
- Nuevos endpoints GET: `?q=consumo` (por tenant, source=agregado con fallback realtime) y `?q=consumo_global` (solo wildcard tenants, projected_monthly)
- Gateway versión 1.3

**metering-cron:** Nueva Edge Function (~200 líneas)
- Agrega metering diario por tenant → UPSERT en `metering_agregados`
- Breakdown `by_capability` (requests, cost, tokens, latency_avg, errors)
- Telemetría: error_rate, projected_monthly_usd, cost_trend_vs_yesterday, avg_cost_per_request
- 3 alertas → `inbox_decisiones`: coste_diario_alto (normal), approaching_rate_limit (baja), anomalia_coste (alta, >50% vs misma semana anterior)

### Primitivas v2 — Prisma Semántico (2 marzo 2026)

**Concepto:** Las primitivas son mini-enjambres que analizan un input desde múltiples ángulos simultáneos, como un prisma que descompone luz blanca. Cada primitiva es una lente distinta (sustantivizar = coseidad, sujeto-predicado = agencia). Diseñadas para ser independientes del framework — el orquestador recibe `llamarLLM` inyectado.

**Arquitectura común** (todas las primitivas):
- **Dial** (0.0–1.0): Controla ángulos activos. Escalado varía por primitiva (8 o 12 ángulos)
- **N ángulos × 2 polos**: Fan-out paralelo a N Haiku (según dial)
- **6 códigos semánticos:** natural, logico_matematico, operativo, financiero, cientifico, narrativo
- **Verificador:** Solo si dial >= 0.8. Retry 3× con backoff (2s/5s/8s para 12-ángulo, 1.5s/3s/5s para 8-ángulo)
- **Integrador:** Haiku final que sintetiza. Retry 3× con backoff (2s/4s) para primitivas de 12 ángulos
- **Parámetro `modelo`:** Default "haiku", override a "sonnet" disponible en runtime

**Primitiva 1 — Sustantivizar** (`primitiva-sustantivizar`):
- Analiza la "coseidad" del input: qué se sustantiviza, qué se omite, qué conceptos se reifican
- 8 ángulos: gramatical, referencial, metaforico, relacional, contextual, agentivo, temporal, axiologico
- 2 polos: sustantivo (qué se nombra como cosa) vs verbal (qué permanece como proceso)
- Output: array de cápsulas + síntesis (sustantivizaciones_clave, procesos_ocultos, recomendacion)
- Verificación (dial>=0.8): Detecta reificaciones peligrosas, procesos ocultos como sustantivos, y agencia fantasma
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests:** 9/9 PASS individual, 7/9 en suite (2 transient: verificador rate-limited, Supabase 502)

**Primitiva 2 — Sujeto-Predicado** (`primitiva-sujeto-predicado`):
- Analiza AGENCIA y RESPONSABILIDAD: quién hace qué, quién decide, quién se esconde
- 8 ángulos: agente, receptor, transferencia, capacidad, compromiso, accountability, temporal, delegacion
- 2 polos: sujeto (quién actúa) vs predicado (qué se predica/hace)
- Output: array de análisis (hallazgo + agencia 0.0-1.0 + alertas) + síntesis (agente_principal, nivel_agencia_global, mapa_responsabilidad, alertas_criticas)
- Verificación (dial>=0.8): Detecta agencia fantasma, transferencias ocultas, contradicciones
- 4 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (9 casos)
- **Tests con Sonnet:** 6/8 PASS (T5 verificador rate-limited, T7 Supabase 502 transient)

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
- **HUECO CRÍTICO modo_meter:** Tiene menos invariantes que los demás — atención especial en prompts y verificador
- Dial: mismo escalado que adjetizar v2. 24 Haiku paralelos en dial 0.8/1.0
- Output: array de análisis (hallazgo + modo {explicitud, descripcion, verbo_vida} + invariantes_detectadas) + síntesis (modo_dominante, verbo_vida_principal, explicitud_global, modos_ocultos, invariantes_activas, mapa_modos)
- Verificación (dial>=0.8): Detecta modos implícitos, contradictorios, huecos_modo_meter, invariantes_ausentes
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests:** T1 explicitud 0.05 ("funciona bien"), T4 verbo_vida="meter", T8 dial mínimo 3 haikus

**Primitiva 5 — Preposicionar** (`primitiva-preposicionar`):
- Analiza RELACIONES Y NIVELES LÓGICOS: preposiciones ocultas, colapsos entre niveles, ausencias estructurales
- **8 ángulos**: nivel, contencion, direccion, limite, distancia, jerarquia, dependencia, ausencia
- 2 polos: no_declarada (detecta relación implícita) vs declarada (establece relación explícita)
- Basado en 5 TIPOS LÓGICOS: conducta (N1), interpretación (N2), criterio/valor (N3), regla/norma (N4), meta/identidad (N5)
- Output: array de análisis (hallazgo + relacion {declarada, tipo, elementos, preposicion_implicita} + nivel_logico {detectado, esperado, colapso, descripcion_colapso}) + síntesis (nivel_logico_dominante, colapsos_detectados, relaciones_principales, preposiciones_ocultas, ausencias_criticas, mapa_relaciones)
- Verificación (dial>=0.8): Detecta colapsos entre niveles, preposiciones fantasma, ausencias estructurales
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (12 casos)
- **Tests:** 7/12 PASS (5 fallos son dial>=0.8 por rate-limiting del verificador). T1 detecta colapso conducta→valor, T3 colapso forma→intención, T7 ausencias "hacia/según/dentro de/desde"

**Primitiva 6 — Conjuntar** (`primitiva-conjuntar`):
- Analiza ESTRUCTURA CONECTIVA: cómo se unen y separan las piezas. Conectores reales, falsos y ausentes
- **8 ángulos**: adicion, oposicion, alternativa, causalidad, condicion, temporalidad, concesion, ausencia_conexion
- 2 polos: desconexion (detecta conexión rota/ausente) vs conexion_explicita (establece conexión real)
- Output: array de análisis (hallazgo + conexion {tipo, elementos, fuerza, legitimidad} + conectores_detectados) + síntesis (estructura_conectiva, conexiones_fuertes, conexiones_rotas, piezas_sueltas, falsas_logicas, mapa_conexiones)
- Verificación (dial>=0.8): Detecta conexiones forzadas, falsas dicotomías, causalidades falsas, piezas sueltas
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Smoke tests:** Detecta falsa dicotomía ("o crecemos o morimos"), causalidad circular ("somos los mejores porque...")

**Primitiva 7 — Verbo** (`primitiva-verbo`):
- Analiza la ACCIÓN NUCLEAR: qué verbo real subyace, disfraces, fuerza, resultado
- **8 ángulos**: accion_nuclear, verbo_vida, objeto, completitud, disfraz, fuerza, resultado, multiplicidad
- 2 polos: accion_difusa (detecta verbo oculto/disfrazado) vs accion_nuclear (establece verbo real)
- Basado en 7 VERBOS DE VIDA: MANTENER, DISTINGUIR, REPARTIR, RESPONDER, COPIAR, SACAR, METER
- Output: array de análisis (hallazgo + accion {verbo_nuclear, verbo_vida, fuerza, produce_resultado} + verbos_detectados) + síntesis (verbo_nuclear, verbo_vida, objeto_real, fuerza_global, produce_resultado, verbos_disfrazados, verbos_vacios, mapa_acciones)
- Verificación (dial>=0.8): Detecta multiplicidad paralizante, disfraces no clasificados, verbos competidores
- 3 archivos `_shared/primitivas-v2/` + 1 Edge Function + 1 test (11 casos)
- **Tests:** **11/11 PASS**. T1 detecta "gestionar/optimizar" como disfraces, T2 "contratar"→METER (fuerza 0.95), T5 verbo fantasma (fuerza 0.07), T6 DISTINGUIR, T10 COPIAR, T11 SACAR

**Archivos totales:** 24 en `_shared/primitivas-v2/` + 7 Edge Functions + 7 tests = 38 archivos
**Coste:** ~$0.01-0.03/llamada Haiku (8-24 ángulos + integrador), ~$0.05-0.12/llamada Sonnet

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

**BLOQUEANTE:** Deploy a prod bloqueado por 402 "Max number of functions reached". Necesita upgrade plan o delete funciones no usadas.

---

## 2. ARQUITECTURA TÉCNICA — DOCUMENTO MAESTRO §4-§8

### §4. PIPELINE — FLUJO DE UNA EJECUCIÓN

```
INPUT
  │
  ▼
PASO 0: DETECTOR HUECOS           ~200ms | $0 | código puro
  7 primitivas + 8 operaciones sintácticas
  → Qué falta en el input
  → Señales para el campo de gradientes
  → Falacias aritméticas en el input
  │
  ▼
PASO 1: CAMPO DE GRADIENTES        ~1-3s | ~$0.01 | código + Haiku
  Para cada celda (21):
  → grado_actual, grado_objetivo, gap
  → Dependencias entre lentes y funciones
  → Output: campo de 21 gradientes ordenados por gap
  │
  ▼
PASO 2: ROUTING POR GRADIENTE      ~500ms | ~$0.001 | modelos ligeros + fallback Sonnet
  Para cada celda con gap > 0.3:
  → ¿Qué INT cierra ESTE gap con más efectividad?
  → Top 3-5 inteligencias por impacto total
  │
  ▼
PASO 3: COMPOSICIÓN                 ~200ms | $0 | NetworkX/código puro
  → Álgebra ensambla red de preguntas (fusión, composición, etc.)
  → 13 reglas como restricciones duras
  → Dependencias informan secuencia
  │
  ▼
PASO 4: ENSAMBLAJE DEL PROMPT       ~100ms | $0 | código puro
  Para cada celda objetivo:
  → Preguntas de esa coordenada (INT × lente × función)
  → Priorizadas por gap_medio_cerrado (dato acumulado)
  → La red de preguntas resultante ES el prompt
  → No hay texto imperativo. Solo preguntas.
  │
  ▼
PASO 5: EJECUCIÓN                   30-120s | $0.001-0.003/modelo OS
  El agente opera BAJO las preguntas como prompt interno
  → Modelo OS asignado por Gestor según celda (Maverick, R1, 70B, V3.1, etc.)
  → Multi-modelo en paralelo si celda requiere complementariedad
  → Código puro: cálculos
  │
  ▼
PASO 6: VERIFICACIÓN DE CIERRE      ~1-3s | ~$0.01
  Re-evalúa campo de gradientes POST-ejecución
  → ¿Se cerró el gap por celda?
  → Si persisten gaps > 0.3: escalar (otra INT, otra profundidad)
  → Max 2 re-intentos por celda
  → Registra gap_cerrado por pregunta → alimenta score_efectividad
  │
  ▼
PASO 7: INTEGRACIÓN + REGISTRO      10-20s | ~$0.15
  Síntesis final (Sonnet/Opus)
  → Output con mapa de cubierto y pendiente
  → Registro de efectos con coordenadas
  → Actualiza gap_medio_cerrado (aprendizaje)

TOTAL: ~$0.10-0.35 (OS-first) | ~40-150s
  (Con evaluador Sonnet: ~$0.35-1.50. Con evaluador OS: ~$0.10-0.35)
```

### 4 modos (configuraciones del mismo pipeline)

| Modo | Campo | INTs típicas | Latencia | Coste |
|------|-------|-------------|----------|-------|
| Análisis | 21 celdas completo | 3-5 por gradientes | 40-150s | $0.50-1.50 |
| Conversación | Solo celdas que el turno toca | 1-2 rápido | 5-20s | $0.05-0.15 |
| Generación | Orientado al output deseado | Creativas: 14,15,09,12 | 30-90s | $0.30-0.80 |
| Confrontación | Busca gaps que la propuesta ignora | Frontera: 17,18,06 | 30-90s | $0.30-0.80 |

### §6B. MOTOR vN — MULTI-MODELO Y DOS FASES DE OPERACIÓN

**Principio: Enjambre de modelos como dimensión algebraica**

```
ANTES:  "La inteligencia está en las preguntas, no en el modelo"
AHORA:  "Las preguntas determinan QUÉ CELDAS se cubren.
         El modelo determina A QUÉ PROFUNDIDAD.
         Modelos diferentes cubren celdas diferentes.
         La diversidad de modelos es una dimensión algebraica más."
```

**Hallazgo empírico (sesión 09-mar):** 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). R1 cubre 20/21 celdas — la mayor cobertura de todos. Cada modelo domina celdas diferentes: V3.1 en Frontera (2.70), GPT-OSS en Depurar (2.52), Claude solo resiste en Adaptar×Salud (2.4). Son COMPLEMENTARIOS — ningún modelo es mejor en todo. El enjambre siempre gana.

### Experimento multi-modelo (COMPLETADO 2026-03-09)

6 modelos OS + Claude como referencia. Variante C (instrucción analítica), 3 casos × 3 INTs.

| # | Modelo | Nivel medio | Celdas cubiertas | Celdas nivel 3+ |
|---|--------|-------------|-----------------|-----------------|
| 1 | **DeepSeek V3.1** | **2.19** | 19/21 | 5/21 |
| 2 | **DeepSeek R1** | **2.18** | **20/21** | 4/21 |
| 3 | **GPT-OSS 120B** | **2.15** | 19/21 | 5/21 |
| 4 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 |
| 5 | Claude (ref) | 1.79 | 15/21 | 1/21 |
| 6 | Maverick | 1.74 | 16/21 | 1/21 |
| 7 | 70B | 1.42 | 11/21 | 1/21 |

**Hallazgo crítico: 3 modelos OS superan a Claude en la Matriz.** DeepSeek V3.1, R1 y GPT-OSS cubren más celdas, a mayor profundidad, y con más instancias nivel 3+ que Claude. Claude es 5º de 7.

### Asignación modelo→celda (primera versión empírica)

Mejor modelo por celda según nivel medio más alto:

| | Conservar | Captar | Depurar | Distribuir | Frontera | Adaptar | Replicar |
|---|---------|---------|---------|---------|---------|---------|---------|
| **Salud** | V3.1 (2.8) | Maverick (2.1) | GPT-OSS (2.6) | Qwen (1.7) | V3.1 (2.6) | Claude (2.4) | V3.1 (2.0) |
| **Sentido** | R1 (2.1) | V3.1 (2.2) | GPT-OSS (2.9) | GPT-OSS (1.7) | R1 (3.1) | V3.1 (2.4) | R1 (1.7) |
| **Continuidad** | V3.1 (2.4) | R1 (2.0) | Qwen (2.3) | R1 (2.0) | V3.1 (2.9) | R1 (2.4) | R1 (3.1) |

**Territorio por modelo (celdas donde es el mejor):**
- **DeepSeek V3.1:** 7 celdas — domina Conservar, Frontera, generalista fuerte
- **DeepSeek R1:** 7 celdas — domina Continuidad, Frontera×Sentido (3.1), Replicar×Continuidad (3.1)
- **GPT-OSS 120B:** 4 celdas — domina Depurar (2.52 media, mejor de todos), Distribuir×Sentido
- **Maverick:** 1 celda — Captar×Salud (2.1)
- **Qwen 397B:** 1 celda — Depurar×Continuidad (2.3), Distribuir×Salud (1.7)
- **Claude:** 1 celda — Adaptar×Salud (2.4)
- **70B:** 0 celdas donde sea el mejor

**Hallazgos por función:**
- **Frontera** es donde más brilla el enjambre OS: V3.1 y R1 alcanzan 2.7-3.1 vs Claude 1.93
- **Depurar** es el dominio de GPT-OSS (2.52) — detecta lo que filtra mal mejor que nadie
- **Adaptar** es donde Claude aún resiste (2.33) — pero V3.1 (2.37) ya lo alcanza
- **Distribuir** es la función más débil para todos — ningún modelo supera 2.0 de media
- **Sentido** es la lente más débil para todos excepto GPT-OSS (2.19)

**Implicación para el Gestor:** La tabla anterior ES el primer programa compilado. El Gestor asigna V3.1 para Conservar/Frontera, R1 para Continuidad, GPT-OSS para Depurar. Donde hay empate (V3.1 ≈ R1 en varias celdas), el Gestor ejecuta ambos y fusiona.

### Rúbrica de profundidad

La profundidad = cobertura de la Matriz. No es escala subjetiva. Es mapeo a 21 celdas (3L×7F):

```
Nivel 0: no toca la celda
Nivel 1: mención genérica
Nivel 2: dato/inferencia específica del caso
Nivel 3: revela algo no obvio (contradicción, patrón invisible)
Nivel 4: redefine la pregunta del caso desde esa celda
```

### Fase A: Exploración (llena la Matriz)

```
Caso nuevo entra
    ↓
Motor OS ejecuta protocolo de exploración completo:
  - 18 INTs individuales (con modelo asignado por Gestor)
  - Composiciones de irreducibles
  - Fusiones top
  - Loop tests
  - Muestreo aleatorio
    ↓
Evaluador mide batch:
  - ¿Qué gaps cerró cada operación?
  - ¿Qué combinación fue más efectiva?
  - Coordenadas: lente × función × INT × operación × modelo
    ↓
Datapoints de efectividad → DB → Gestor de la Matriz
    ↓
Tabla configuraciones_efectivas se llena
```

### Protocolo de exploración (5 tiers)

```
Tier 1 (siempre):  18 INTs individuales sobre el caso
Tier 2 (siempre):  6 irreducibles en composición = 30 pares (A→B y B→A)
Tier 3 (siempre):  TOP 10 fusiones derivadas de Cartografía
Tier 4 (siempre):  Loop test sobre top 3 resultados de Tiers 1-3
Tier 5 (muestreo): 10% de combinaciones restantes seleccionadas aleatoriamente

Total: ~70-80 ejecuciones por caso
Coste: ~$0.08 OS ejecutores + ~$0.24 evaluador = ~$0.32 por caso completo
(Si evaluador migra a OS: ~$0.08 + ~$0.003 + ~$0.003 = ~$0.09 por caso)
```

### Fase B: Lookup (usa la Matriz llena)

Cuando una celda tiene suficientes datos, el Motor pasa a modo servicio para esa celda.

```
Caso nuevo entra
    ↓
Detector de huecos → patrón de gaps
    ↓
Gestor de la Matriz provee programa compilado:
  "Este patrón de gaps lo he visto 47 veces.
   La configuración INT-01→INT-14 fusión con Maverick cierra
   el 82% en Salud×Captar."
    ↓
Ejecuta SOLO la configuración ganadora con el modelo asignado
    ↓
Respuesta en segundos, no minutos
```

### Transición Fase A → Fase B

La transición NO es binaria ni global — es por celda. Criterio por celda:

```
SI (n_ejecuciones_patron > 30 AND tasa_cierre_config_ganadora > 0.60):
  → Fase B para esta celda (lookup directo via Gestor)
SINO:
  → Fase A (seguir explorando)
```

### §6E. GESTOR DE LA MATRIZ — EL SISTEMA QUE MIRA HACIA DENTRO

**Qué es:** Un sistema independiente con su propio pipeline. NO es parte del Motor vN. Es el cerebro que mantiene, optimiza y compila la Matriz para todos los consumidores del sistema.

**Por qué es pieza central:**

```
                    GESTOR DE LA MATRIZ
                    (loop lento, mira hacia dentro)
                           │
                    Mantiene, poda, mejora, compila
                    la Matriz 3L×7F×18INT
                           │
              ┌────────────┼────────────┐────────────┐
              │            │            │            │
              ▼            ▼            ▼            ▼
         Motor vN    Exocortex     Exocortex     Chief of
         (casos      Pilates       Clínica       Staff
          nuevos)    (movimiento)  (salud oral)  (Jesús)
```

Cada consumidor recibe un **programa de preguntas compilado** por el Gestor, no la Matriz entera. El Gestor sabe qué preguntas funcionan para qué contexto porque tiene los datos de efectividad de TODOS los consumidores.

### Lo que el Gestor compila para cada consumidor

**Para el Motor vN (diagnóstico general):**
```
"Para un caso tipo startup con gaps en Captar×Salud y Frontera×Sentido,
usa estas 12 preguntas con Maverick, estas 8 con R1.
Fusiona outputs en Captar×Salud porque son complementarios ahí."
```

**Para un Exocortex (dominio específico):**
```
"Para una clienta con dolor lumbar crónico de 3 meses,
las preguntas efectivas son estas 15 de INT-04 (Cinestésica)
+ estas 6 de INT-03 (Espacial) en composición.
Modelo: V3.1 (mejor en Adaptar×Salud para movimiento)."
```

**Para el Chief of Staff:**
```
"Jesús evalúa decisión arquitectural.
Preguntas de INT-01 (Lógica) + INT-16 (Estructural).
Modelo: Maverick (mejor en Frontera×Sentido)."
```

### Conocimiento transversal

```
ANTES:
  Cada consumidor tiene su propia lógica de selección de preguntas.
  No comparten aprendizaje.

AHORA:
  El Gestor acumula datos de efectividad de TODOS los consumidores.
  Pilates descubre que INT-04 pregunta 23 es brutal para dolor lumbar.
  Ese dato sube al Gestor.
  El Gestor puede ofrecer esa pregunta a Clínica si ve un caso
  con patrón de gaps similar.
  El conocimiento es TRANSVERSAL, no siloado.
```

### Pipeline del Gestor

```
INPUTS (continuos):
  ← Datapoints de efectividad del Motor vN
  ← Datapoints de efectividad de cada Exocortex
  ← Preguntas nuevas de Reactores v1/v2/v3
  ← Resultados del Meta-motor

PROCESO (loop lento, cada N horas o cada 50 ejecuciones):
  1. Actualizar scores de efectividad por pregunta×modelo×celda
  2. Podar preguntas muertas (n>10, tasa<0.05)
  3. Promover preguntas potentes (n>10, tasa>0.40)
  4. Detectar complementariedad entre modelos por celda
  5. Detectar transferencia cross-dominio
  6. Recalcular asignación modelo→celda (ranking por tasa_media_cierre)
  7. Recompilar programas de preguntas por consumidor

OUTPUTS (bajo demanda):
  → Programa compilado para Motor vN dado un caso + patrón de gaps
  → Programa compilado para Exocortex X dado un contexto de dominio
  → Programa compilado para Chief of Staff dado una decisión
  → Informe de salud de la Matriz (propiocepción)
```

### Registro por ejecución (feedback loop)

Cada vez que CUALQUIER consumidor ejecuta una pregunta, se registra:

```
{
  pregunta_id:        "INT07_F2_L1_003",
  modelo:             "llama-4-maverick",
  caso_id:            "startup_saas_001",
  consumidor:         "motor_vn",          // o "exocortex_pilates", etc.
  celda_objetivo:     "Captar×Salud",
  gap_pre:            0.72,
  gap_post:           0.35,
  gap_cerrado:        0.37,
  tasa_cierre:        0.514,
  variante_prompt:    "C",
  operacion:          "individual",
  int_secundaria:     null,
  timestamp:          "2026-03-09T..."
}
```

### Vista materializada (lo que el Gestor consulta)

```sql
CREATE MATERIALIZED VIEW pregunta_efectividad AS
SELECT
  pregunta_id,
  modelo,
  celda_objetivo,
  consumidor,
  COUNT(*) as n_ejecuciones,
  AVG(gap_cerrado) as gap_medio_cerrado,
  AVG(tasa_cierre) as tasa_media_cierre,
  STDDEV(tasa_cierre) as varianza,
  MIN(tasa_cierre) as peor_caso,
  MAX(tasa_cierre) as mejor_caso
FROM datapoints_efectividad
GROUP BY pregunta_id, modelo, celda_objetivo, consumidor;
```

Refresco: cada 50 ejecuciones o cada 24h (lo que ocurra primero).

### §8. INFRAESTRUCTURA

### Decisiones cerradas (CR1 2026-03-09)

| Decisión | Elegido | Razón |
|----------|---------|-------|
| Motor + DB | fly.io Postgres + pgvector | Colocalizada, sin dependencias externas |
| Ejecutores Motor vN | Multi-modelo OS vía APIs commodity | ~$0.001-0.003/ejecución. Diversidad > modelo único |
| Orquestador Gestor | Modelo OS razonador (Qwen 235B / Maverick) | Stack 100% OS. Sin dependencia premium |
| Evaluador (inicial) | Sonnet vía Anthropic API | Referencia de calibración. Migrar a OS cuando correlación >0.85. NOTA: como ejecutor, Claude es 5º de 7 — el evaluador es el último bastión premium |
| Exocortex Pilates | fly.io (nuevo) | Se crea de cero, misma esencia |
| Exocortex Clínica | fly.io (nuevo) | Igual |
| Supabase | Se depreca gradualmente | 402 incluso con upgrade |

### Principio: OS-first

El objetivo es stack 100% open source. Sonnet se usa como referencia de calibración, no como dependencia operativa. Cuando un modelo OS demuestre correlación >0.85 con Sonnet en evaluación de cobertura matricial, se migra esa función a OS.

```
Fase 1 (ahora):    Ejecutores = OS. Evaluador = Sonnet. Orquestador = OS.
Fase 2 (~500 ejecuciones): Testear evaluador OS vs Sonnet.
Fase 3 (si pasa):  TODO OS. Sonnet solo para calibración periódica.

Coste por caso:
  Fase 1: ~$0.08 OS + ~$0.24 Sonnet = $0.32
  Fase 3: ~$0.08 + ~$0.003 + ~$0.003 = ~$0.09 (70% reducción)
```

### Qué se mantiene de la arquitectura Supabase

Estigmergia, enjambres, telemetría, mejora continua — todos son patrones en tablas Postgres. Se llevan tal cual. Se reemplazan 4 piezas de fontanería: Edge Functions → Node/Python, pg_net → workers/colas, cron → node-cron, auth → JWT.

### Stack técnico

```
fly.io:
  Python/FastAPI         — Motor cognitivo + Gestor + API
  fly.io Postgres        — Matriz, efectos, telemetría, estado, datapoints efectividad
  scikit-learn           — Modelos ligeros C1-C4
  NetworkX + scipy       — Grafo compositor
  Anthropic API          — Sonnet (evaluador referencia, 4 keys rotativas)

Inferencia OS (APIs commodity):
  Groq                   — Llama 3.3 70B, Llama 4 Maverick (más rápido)
  Together / Fireworks   — DeepSeek R1, V3.1, Qwen 235B, fallbacks
  → Ejecutores y orquestador son intercambiables. Si sale OS mejor, se cambia sin tocar nada.

Supabase (se depreca):
  99 Edge Functions      — Siguen hasta que fly.io las reemplace
  PostgreSQL             — Sistema nervioso actual
```

---

## 3. MAPA DE MODELOS — ASIGNACIÓN EMPÍRICA POR CELDA

Basado en **MULTI-MODEL MATRIX COVERAGE REPORT** (Exp 1 completo, 12 modelos evaluados):

### Ranking Global de Modelos OS

| # | Modelo | Nivel Medio | Cobertura | Celdas 3+ | Coste Est. |
|---|--------|-------------|-----------|-----------|------------|
| 1 | **DeepSeek V3.1** | **2.19** | 19/21 | 5/21 | $0.005-0.008 |
| 2 | **DeepSeek R1** | **2.18** | **20/21** | 4/21 | $0.006-0.010 |
| 3 | **GPT-OSS 120B** | **2.15** | 19/21 | 5/21 | $0.003-0.005 |
| 4 | DS-V3.2 Chat | 2.12 | 18/21 | **6/21** | $0.005-0.008 |
| 5 | DS-V3.2 Reasoner | 2.00 | 17/21 | 3/21 | $0.006-0.010 |
| 6 | Cogito 671B | 1.98 | 18/21 | 2/21 | $0.015-0.020 |
| 7 | Qwen3 Thinking | 1.95 | 19/21 | 2/21 | $0.008-0.012 |
| 8 | Kimi K2.5 | 1.87 | 18/21 | 1/21 | $0.010-0.015 |
| 9 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 | $0.008-0.012 |
| 10 | Claude (ref) | 1.79 | 15/21 | 1/21 | $0.050-0.080 |
| 11 | Maverick | 1.74 | 16/21 | 1/21 | $0.002-0.004 |
| 12 | 70B | 1.42 | 11/21 | 1/21 | $0.001-0.002 |

### Asignación Óptima por Celda (Programa Compilado v1)

| Función | Salud | Sentido | Continuidad |
|---------|-------|---------|-------------|
| **Conservar** | **V3.1** (2.8) | Cogito (2.3) | **V3.1** (2.4) |
| **Captar** | Maverick (2.1) | **V3.1** (2.2) | R1 (2.0) |
| **Depurar** | **GPT-OSS** (2.6) | **GPT-OSS** (2.9) | Qwen3.5 (2.3) |
| **Distribuir** | Qwen3 Think (2.1) | **GPT-OSS** (1.7) | R1 (2.0) |
| **Frontera** | **V3.1** (2.6) | **R1** (3.1) | **V3.1** (2.9) |
| **Adaptar** | Kimi K2.5 (2.7) | **V3.1** (2.4) | R1 (2.4) |
| **Replicar** | **V3.1** (2.0) | R1 (1.7) | **R1** (3.1) |

**Distribución de Dominio:**
- **DeepSeek V3.1:** 7 celdas (Conservar×3, Frontera×2, Adaptar×1, Replicar×1)
- **DeepSeek R1:** 7 celdas (Continuidad×4, Frontera×1, Replicar×2)
- **GPT-OSS 120B:** 4 celdas (Depurar×2, Distribuir×1, Captar×1)
- **Otros:** Maverick, Qwen, Kimi, Cogito para celdas específicas donde dominan

---

## 4. ARQUITECTURA DE MECANISMOS MULTI-MODELO

Basado en **ARQUITECTURA DE MECANISMOS MULTI-MODELO** (Exp 4 completo):

### Los 5 Mecanismos y Qué Produce Cada Uno

#### 1A. Evaluación individual en paralelo (Exp 4 R1)

**Qué es:** N modelos reciben el mismo input y evalúan independientemente.

**Produce:**
- Score por celda con varianza inter-evaluador medible
- Detección de sesgos: quién infla (+0.84 Qwen3), quién defla (-0.45 GPT-OSS)
- Correlaciones entre evaluadores (Sonnet↔Qwen3: 0.605, R1↔V3.2R: 0.642)
- Mapa de "lobos solitarios" (quién da 3+ cuando nadie más lo hace)

**No produce:** Conexiones, puntos ciegos, síntesis, convergencia.

**Datos:** Media global 1.71, solo 7/105 celdas con consenso mayoritario (≥6 dan 3+). Std medio 0.71-0.94 por output.

**Coste:** N llamadas paralelas (~12 modelos × 5 outputs = 60 llamadas). ~$0.50-1.00.

**Cuándo usar:** Screening rápido de calidad. Calibrar modelos nuevos. Seleccionar quién entra en mecanismos más caros. Es el termómetro, no el tratamiento.

#### 1B. Mesa redonda con enriquecimiento (Exp 4 R2)

**Qué es:** Tras R1, cada modelo ve las evaluaciones de los demás y reevalúa.

**Produce:**
- Convergencia masiva: 7→70 celdas con consenso mayoritario (10x)
- 16 celdas emergentes (no existían en R1)
- Reducción de varianza

**No produce:** Conexiones cross-celda, hallazgos centrales, puntos ciegos.

**Datos:** Media 3.27 (vs 1.71 R1), 93/105 celdas 3+.

**Atención:** 77% de las convergencias van hacia donde Qwen3 ya apuntaba en R1 — efecto líder parcial, no solo convergencia ciega. Sonnet predice R2 mejor que nadie (ρ=0.656).

**Coste:** 2N llamadas (R1+R2). ~$1-2.

**Cuándo usar:** Evaluación fiable con consenso. Cuando necesitas UNA respuesta validada por múltiples perspectivas, no N opiniones dispersas.

#### 1C. Mesa especializada (Exp 4.1)

**Qué es:** Misma mesa, pero cada modelo recibe prompt afinado a su zona fuerte.

**Produce:**
- +0.55 media en zona de foco (mejora significativa)
- -0.14 fuera de foco (deterioro leve)
- Delta global: +0.10 (7/12 modelos mejoran)
- Cambia la mesa mínima: V3.2-chat + V3.1 = 97.9% (vs Qwen3 + GPT-OSS = 94.6% con genérico)

**Modelos que mejoran con especialización:** V3.2-Reasoner (+0.50), R1 (+0.43), MiniMax (+0.28), V3.1 (+0.19), V3.2-chat (+0.16).

**Modelos que empeoran:** Kimi (-0.48), Opus (-0.40), Qwen3 (-0.31), GLM (-0.27). Los infladores genéricos pierden ventaja con prompt específico.

**Coste:** Igual que mesa genérica — solo cambian los prompts.

**Cuándo usar:** Siempre que uses mesa redonda. No hay razón para no especializar: mismo coste, mejor resultado en foco.

#### 1D. Sintetizador (Exp 4.2)

**Qué es:** Un modelo recibe TODAS las evaluaciones de la mesa y produce output integrado.

**Produce:**
- Conexiones cross-lente (media 3.6/output con Cogito)
- Hallazgos centrales no-genéricos (5/5 con Cogito)
- Meta-patrones (media 3.0/output)
- Puntos ciegos residuales (media 2.6/output)
- 100% de celdas igualan max mecánico (no pierde nada)

**No produce:** Scores superiores al max mecánico (0 celdas por encima).

**Ranking sintetizadores:**

| # | Modelo | Outputs OK | Conexiones | Hallazgos | Tiempo |
|---|--------|-----------|------------|-----------|--------|
| 1 | **Cogito-671b** | 5/5 | 3.6/output | 5/5 no-genéricos | 47s |
| 2 | DeepSeek-R1 | 5/5 | 3.0/output | 5/5 no-genéricos | 55s |
| 3 | Qwen3-235b | 5/5 | 2.2/output | 3/5 no-genéricos | 137s |
| 4 | V3.2-chat | 5/5 | 2.0/output | 2/5 no-genéricos | 121s |
| ✗ | GLM-5 | 0/5 (parse fail) | — | — | — |
| ✗ | MiniMax M2.5 | 0/5 (parse fail) | — | — | — |

**Coste:** 1 llamada extra (~47s con Cogito). ~$0.05.

**Cuándo usar:** SIEMPRE como paso final después de cualquier mesa. Convierte datos (scores) en comprensión (conexiones causales). Es lo que un humano necesita para decidir. Coste marginal despreciable.

#### 1E. Pizarra / Mente distribuida (Exp 4.3)

**Qué es:** Pizarra compartida donde N modelos contribuyen evidencias por turnos. Múltiples rondas hasta convergencia.

**Produce:**
- 425 conexiones entre celdas (exclusivo)
- 239 puntos ciegos detectados (exclusivo)
- 94/105 celdas 3+ (evaluación externa Claude) — cobertura equivalente a mesa redonda
- Contenido rico con capas de profundización: cada ronda añade ángulos

**No produce:** Scores más altos que la mesa redonda (3.06 vs 3.27 evaluación externa). El auto-tracking infla +0.93 puntos.

**Perfiles de modelos en la pizarra:**

| Modelo | Contribuciones | Conexiones | P.Ciegos | Perfil |
|--------|---------------|------------|----------|--------|
| GPT-OSS | 119 | 77 | 46 | Motor principal |
| MiniMax M2.5 | 75 | 55 | 45 | Segundo motor |
| Qwen3-235b | 63 | 48 | 25 | Tercer contribuidor |
| V3.2-chat | 56 | 52 | 28 | Conector fuerte |
| V3.1 | 52 | 45 | 22 | Contribuidor sólido |
| R1 | 44 | 30 | 12 | Contribuidor |
| V3.2-Reasoner | 42 | 28 | 14 | Contribuidor |
| Opus | 33 | 34 | 8 | Conector (caro) |
| Cogito | 31 | 29 | 22 | Detector de huecos |
| Kimi | 25 | 19 | 15 | Contribuidor menor |
| GLM-4.7 | 20 | 8 | 2 | Marginal |

**Convergencia:** 3/5 outputs convergieron en 4-5 rondas. 2/5 llegaron al máximo de rondas sin converger.

**Coste:** Alto. 10-11 modelos × 4-5 rondas = 40-55 llamadas por output. ~$2-5 por output.

**Cuándo usar:** Cuando necesitas PENSAR, no evaluar. Exploración profunda de un problema. Batch nocturno. Onboarding de dominio nuevo. Su valor está en las conexiones y puntos ciegos, no en los scores.

### Mapa de Uso por Necesidad

| Necesitas... | Mecanismo | Coste | Tiempo |
|---|---|---|---|
| Screening rápido de calidad | Individual paralelo (1A) | ~$0.50 | ~2min |
| Evaluación fiable con consenso | Mesa redonda R1+R2 (1B) | ~$1-2 | ~5min |
| Profundidad en área concreta | Mesa especializada (1C) | ~$1-2 | ~5min |
| Entender conexiones causales | Sintetizador Cogito (1D) | ~$0.05 extra | ~47s extra |
| Explorar problema en profundidad | Pizarra distribuida (1E) | ~$2-5 | ~30-60min |
| Saber qué modelos usar | Individual + análisis de sesgo | ~$0.50 | ~5min |

### Composiciones por Tier

#### Tier 2 — Respuesta (5-15s, $0.01-0.05)

```
1 modelo: V3.2-chat (89.5% cobertura