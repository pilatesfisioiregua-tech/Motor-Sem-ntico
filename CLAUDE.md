# MOTOR SEMÁNTICO OMNI-MIND — CLAUDE.md

## REGLA DE MANTENIMIENTO

**Cada vez que se modifique la arquitectura del codebase** (nuevo módulo, nuevo endpoint, nueva tabla, nueva ruta frontend, nueva env var, cambio de stack), **actualizar este CLAUDE.md** en la misma sesión. Secciones a revisar:

- Nuevo módulo Python → actualizar `ESTRUCTURA` y `ARQUITECTURA ORGANISMO`
- Nuevo endpoint → actualizar `API — ENDPOINTS`
- Nueva tabla SQL → actualizar `BASE DE DATOS`
- Nueva env var → actualizar `VARIABLES DE ENTORNO`
- Nuevo componente/ruta frontend → actualizar `ESTRUCTURA` y `FRONTEND`
- Cambio de dependencia/stack → actualizar `STACK`
- Nuevo anti-patrón descubierto → añadir a `ANTI-PATRONES`

Si no se actualiza en la misma sesión, la próxima sesión arranca con información incorrecta → exploración innecesaria → tiempo y coste perdido.

## MAPA RÁPIDO

```
Backend:  src/pilates/router.py    (137 endpoints, 3900+ líneas)
          src/pilates/cockpit.py   (chat + módulos cockpit)
          src/pilates/*.py         (43 módulos de agentes)
          src/pilates/cron.py      (orquestación temporal: diaria/semanal/mensual)
Frontend: frontend/src/            (React 19 + Vite 8 + Tailwind v4)
          frontend/src/design/     (9 componentes design system Neural Dark)
DB:       79 tablas PostgreSQL     (fly.io, pgvector)
          Clave: om_senales_agentes, om_pizarra, om_clientes, om_sesiones, om_contratos
Config:   src/config/settings.py   (env vars, constantes)
          fly.toml                 (deploy fly.io)
Tenant:   authentic_pilates        (hardcoded en queries)
```

## QUÉ ES

Dos sistemas en uno:

**1. Motor Semántico** — Compilador de inteligencias. Recibe input en lenguaje natural → genera algoritmo óptimo desde las 18 inteligencias de la Meta-Red → ejecuta → integra resultado.

**2. Exocortex Pilates** — Sistema autónomo de gestión para un estudio de Pilates. 43 agentes, bus de señales, pizarra compartida, 7 funciones autónomas (AF1-AF7), diagnóstico ACD, voz multicanal, portal cliente, cron programado.

```
INPUT:  "Mi socio quiere vender su parte y no sé si puedo comprársela"
MOTOR:  Router → [INT-07, INT-06, INT-08, INT-05]
        Compositor → INT-07→INT-06 → ∫(INT-08|INT-05)
        Ejecutor → ejecuta preguntas de cada inteligencia sobre el input
        Integrador → síntesis final
OUTPUT: Diagnóstico multi-inteligencia con hallazgos, firma combinada, puntos ciegos
```

## STACK

- **Runtime:** Python 3.12+
- **Framework:** FastAPI
- **DB:** fly.io Postgres con pgvector
- **Grafos:** NetworkX
- **LLM:** Anthropic API (Haiku extracción, Sonnet routing/integración), OpenRouter (Opus Director/Meta-Cognitivo, GPT-4o cockpit chat)
- **Search:** Perplexity API (buscador dirigido, Capa A voz)
- **Pagos:** Stripe (recurrente), Redsys/Caja Rural de Navarra (TPV)
- **Mensajería:** WhatsApp Business API (Twilio)
- **Frontend:** React 19, Vite 8, Tailwind v4, Framer Motion
- **Deploy:** fly.io
- **NO usar:** Supabase, Deno, Edge Functions. OpenAI solo vía OpenRouter (GPT-4o para cockpit chat)

## ESTRUCTURA

```
motor-semantico/
├── fly.toml, Dockerfile, requirements.txt
├── CLAUDE.md
├── src/
│   ├── main.py                      # FastAPI server
│   ├── config/
│   │   ├── settings.py              # Env vars, constantes
│   │   ├── modelos.py               # Config LLM (keys, modelos, fallback)
│   │   └── reglas.py                # 13 reglas del compilador
│   ├── db/
│   │   ├── client.py                # asyncpg connection pool (get_pool)
│   │   ├── schema.sql               # Schema base (inteligencias, ACD, ejecuciones)
│   │   └── seed.sql                 # Datos iniciales
│   ├── pilates/                     # === EXOCORTEX PILATES (43 módulos) ===
│   │   ├── router.py                # 137 endpoints FastAPI (3900+ líneas)
│   │   ├── cockpit.py               # Chat + módulos modo Estudio
│   │   ├── cron.py                  # Tareas programadas (diaria/semanal/mensual)
│   │   ├── bus.py                   # Bus de señales inter-agente
│   │   ├── pizarra.py               # Pizarra compartida (conciencia colectiva)
│   │   ├── cerebro_organismo.py     # Orquestador del ciclo cognitivo
│   │   ├── director_opus.py         # Director (Opus): decisiones estratégicas
│   │   ├── metacognitivo.py         # Meta-Cognitivo: evalúa sistema cognitivo
│   │   ├── ingeniero.py             # Procesa instrucciones del Meta-Cognitivo
│   │   ├── evaluador_organismo.py   # Evaluador semanal: ¿funcionó la prescripción?
│   │   ├── recompilador.py          # G4: Enjambre+Compositor+Estratega+Recompilación
│   │   ├── enjambre.py              # Enjambre cognitivo: 16 agentes paralelos
│   │   ├── compositor.py            # Compositor: grafos óptimos (NetworkX)
│   │   ├── diagnosticador.py        # Diagnóstico ACD (Actividad, Claridad, Dirección)
│   │   ├── generativa.py            # Generador de preguntas
│   │   ├── vigia.py                 # Vigilante: health checks cada 15min
│   │   ├── mecanico.py              # Mecánico: repara alertas del Vigía
│   │   ├── autofago.py              # Autofagia mensual: poda código muerto
│   │   ├── propiocepcion.py         # Snapshots de estado del organismo
│   │   ├── ejecutor_convergencia.py # Ejecutor + Convergencia: cierra circuitos
│   │   ├── guardian_sesgos.py       # Detecta sesgos en clusters del enjambre
│   │   ├── buscador.py              # Búsqueda dirigida por gaps (Perplexity)
│   │   ├── af1_conservacion.py      # AF1: clientes en riesgo de churn
│   │   ├── af3_depuracion.py        # AF3: ineficiencias + VETOs
│   │   ├── af5_identidad.py         # AF5: gaps de identidad + ADN
│   │   ├── af_restantes.py          # AF2+AF4+AF6+AF7 (captación, distribución, adaptación, replicación)
│   │   ├── voz.py                   # Voz central (Perplexity Search)
│   │   ├── voz_ciclos.py            # Ciclos: escuchar señales, IRC, ISP
│   │   ├── voz_estrategia.py        # Estrategia semanal: foco + calendario
│   │   ├── voz_identidad.py         # Identidad del organismo
│   │   ├── voz_reactivo.py          # Propagar diagnóstico, señales cross-AF
│   │   ├── voz_arquitecto.py        # Arquitecto: define roles + marcos
│   │   ├── collectors.py            # Extrae métricas de canales (WA, email)
│   │   ├── engagement.py            # Mide participación cliente
│   │   ├── briefing.py              # Genera briefing semanal
│   │   ├── portal_chat.py           # Chat con cliente autenticado
│   │   ├── portal_publico.py        # Chat marketing + lead capture
│   │   ├── portal.py                # Datos portal: sesiones, pagos, facturas
│   │   ├── whatsapp.py              # Integración WhatsApp Business
│   │   ├── wa_chat.py               # Chat WhatsApp
│   │   ├── wa_respuestas.py         # Respuestas sugeridas WA
│   │   ├── stripe_pagos.py          # Stripe: cobros recurrentes + webhooks
│   │   ├── redsys_pagos.py          # Redsys/Caja Rural de Navarra
│   │   ├── sequito.py               # Séquito: permisos + usuarios
│   │   └── observador.py            # Observador
│   ├── pipeline/                    # === MOTOR SEMÁNTICO (7 capas) ===
│   │   ├── orchestrator.py          # Orquesta las 7 capas
│   │   ├── detector_huecos.py       # Capa 0: detector de huecos ($0)
│   │   ├── router.py                # Capa 1: selección inteligencias (Sonnet)
│   │   ├── compositor.py            # Capa 2: grafo + algoritmo (NetworkX)
│   │   ├── generador.py             # Capa 3: genera prompts
│   │   ├── ejecutor.py              # Capa 4: ejecuta prompts (Haiku+Sonnet)
│   │   ├── evaluador.py             # Capa 5: scorer heurístico
│   │   └── integrador.py            # Capa 6: síntesis final (Sonnet)
│   ├── meta_red/
│   │   ├── inteligencias.json       # 18 redes de preguntas
│   │   └── marco_linguistico.json   # 8 ops, 9 capas, 6 acoples, falacias
│   └── utils/
│       └── llm_client.py            # Wrapper Anthropic con rotación de keys
├── frontend/
│   ├── index.html                   # Google Fonts (Instrument Sans, Inter Tight, JetBrains Mono)
│   ├── vite.config.js               # React + Tailwind v4 (@tailwindcss/vite)
│   └── src/
│       ├── App.jsx                  # Router: /, /profundo, /portal/:token, /onboarding/:token, /info
│       ├── EstudioCockpit.jsx       # Cockpit modo Estudio (715 líneas)
│       ├── Profundo.jsx             # Modo Profundo con tabs (725 líneas)
│       ├── Calendario.jsx           # Calendario semanal L-V
│       ├── PanelWA.jsx              # Panel WhatsApp entrante
│       ├── FeedEstudio.jsx          # Feed de alertas del estudio
│       ├── Consejo.jsx              # Enjambre de inteligencias
│       ├── PortalChat.jsx           # Chat cliente autenticado
│       ├── Portal.jsx               # Portal datos del cliente
│       ├── Onboarding.jsx           # Formulario registro 5 pasos
│       ├── PortalPublico.jsx        # Chat marketing público
│       ├── api.js                   # 57 funciones helper API
│       ├── index.css                # Neural Dark: @theme, :root, animaciones
│       ├── App.css                  # Legacy CSS aliases → Neural Dark
│       ├── design/                  # Design System Neural Dark
│       │   ├── Card.jsx             # 6 variantes (default, elevated, organism, alert, danger, success)
│       │   ├── Metric.jsx           # KPI con delta (↑↓→), 3 tamaños
│       │   ├── Pulse.jsx            # Ping animation, 7 colores
│       │   ├── AgentBadge.jsx       # 4 estados: activo, esperando, bloqueado, completado
│       │   ├── SignalFlow.jsx       # Timeline de señales, 7 tipos
│       │   ├── LensBar.jsx          # 3 lentes: Salud/Sentido/Continuidad
│       │   ├── ConflictLine.jsx     # Conflicto agente-a-agente
│       │   ├── VoiceButton.jsx      # Botón micrófono con animación
│       │   └── theme.js             # Constantes: CAPAS, TABS_PROFUNDO, ESTADO_ACD
│       └── shared/
│           └── VoicePanel.jsx       # Web Speech API STT + TTS (es-ES, $0)
├── migrations/                      # SQL migrations (18+ archivos)
├── briefings/                       # Briefings de implementación
├── tests/
└── scripts/
```

## ARQUITECTURA ORGANISMO

El Exocortex opera como un organismo autónomo con ciclos programados:

```
CRON DIARIO (06:00):    Escuchar señales → Collectors → Snapshot propiocepción
CRON SEMANAL (lun 07:00): Ciclo completo → Estrategia → ACD → AF1-AF7 → G4 → Ejecutor
CRON MENSUAL (día 1):   Autofagia → Meta-Cognitivo (Opus) → Ingeniero
CONTINUO (cada 15min):  Vigía (health checks) → Mecánico (reparación)
```

### Bus de señales (om_senales_agentes)
Comunicación inter-agente. 9 tipos: DATO, ALERTA, DIAGNOSTICO, OPORTUNIDAD, PRESCRIPCION, ACCION, PERCEPCION, RECOMPILACION, BRIEFING_PENDIENTE.

### Pizarra (om_pizarra)
Conciencia colectiva. Cada agente escribe observaciones, interpretaciones, conflictos. Lectura transversal.

### 7 Agentes Funcionales (AF)
| AF | Función | Qué detecta |
|----|---------|-------------|
| AF1 | Conservación | Clientes en riesgo de churn |
| AF2 | Captación | Leads perdidos, tasa conversión |
| AF3 | Depuración | Ineficiencias, emite VETOs |
| AF4 | Distribución | Desequilibrios horarios, ratio individual/grupo |
| AF5 | Identidad | Gaps de identidad, coherencia canal, ADN |
| AF6 | Adaptación | Tensiones no resueltas |
| AF7 | Replicación | Gaps documentación, readiness |

### Jerarquía cognitiva
```
Director Opus (mensual)     → Estrategia global, D_hybrid prompts
  └── Meta-Cognitivo (mensual) → ¿Funciona el sistema cognitivo?
      └── Ingeniero            → Ejecuta instrucciones del Meta-Cognitivo
  └── Evaluador (semanal)     → ¿Funcionó la prescripción anterior?
  └── G4 (semanal)            → Enjambre + Compositor + Estratega + Recompilador
      └── Enjambre             → 16 agentes paralelos: 3 lentes + 7 funciones + 6 clusters
      └── Recompilador         → Reconfigura INT×P×R de cada agente
```

## BASE DE DATOS — 79 TABLAS (por dominio)

### Core Motor (7 tablas)
- `inteligencias` — 18 inteligencias base
- `aristas_grafo` — Relaciones entre inteligencias
- `operaciones_sintacticas` — 8 operaciones primitivas
- `capas_sistema` — 9 capas lingüísticas
- `tipos_acople` — 6 tipos (Y, PERO, AUNQUE, PORQUE, SI, PARA)
- `falacias_aritmeticas` — Errores lógicos
- `sufijos_operaciones` — Mapeo sufijos → operaciones → capas

### ACD — Álgebra Cognitiva Diagnóstica (4 tablas)
- `tipos_pensamiento` — 15 tipos (P01-P15) con lentes y funciones
- `tipos_razonamiento` — 12 tipos (R01-R12) con capacidades y límites
- `estados_diagnosticos` — 10 estados (E1-E4, operador_ciego, genio_mortal, etc.)
- `diagnosticos` — Historial diagnósticos con vector pre/post

### Organismo — Enjambre y Señales (4 tablas)
- `om_senales_agentes` — **Bus unificado** de señales inter-agente (9 tipos)
- `om_enjambre_diagnosticos` — Resultados enjambre cognitivo (16 agentes)
- `om_pizarra` — **Pizarra compartida**: observaciones, interpretaciones, conflictos
- `om_semillas_dormidas` — Ideas/oportunidades latentes pendientes

### Organismo — Config y Director (4 tablas)
- `om_config_agentes` — Config dinámica INT×P×R por agente (recompilable en runtime)
- `om_director_manual` — Manual del Director Opus en BD
- `om_ingeniero_backups` — Backups pre-cambio para rollback
- `om_telemetria_sistema` — Snapshots periódicos de rendimiento

### Pilates — Gestión Operativa (11 tablas)
- `om_clientes` — Clientes (nombre, email, teléfono, NIF, RGPD)
- `om_grupos` — Grupos (capacidad, días, precio, instructor)
- `om_contratos` — Contratos (individual/grupo, frecuencia, estado)
- `om_sesiones` — Sesiones programadas/realizadas
- `om_asistencias` — Registro asistencia (confirmada/asistió/no_vino/cancelada/recuperación)
- `om_cargos` — Cargos generados (sesión, cancelación tardía, suscripción, producto)
- `om_pagos` — Pagos (tpv, bizum, efectivo, transferencia, paygold)
- `om_pago_cargos` — Linking: pagos ↔ cargos
- `om_facturas` — Facturas (serie, VeriFactu hash)
- `om_factura_lineas` — Líneas detalladas factura
- `om_gastos` — Gastos operativos

### Pilates — Voz y Canales (15 tablas)
- `om_voz_identidad` — Identidad comunicación (propuesta valor, tono, targets)
- `om_voz_irc` — IRC (Índice Rentabilidad Canal) por canal
- `om_voz_pca` — PCA (Perfil Consumo Audiencia) por segmento
- `om_voz_estrategia` — Estrategia activa (foco, narrativa, prescripciones)
- `om_voz_propuestas` — Propuestas contenido por canal
- `om_voz_telemetria` — Métricas diarias por canal
- `om_voz_telemetria_canal` — Telemetría detallada (leads, engagement)
- `om_voz_isp` — ISP (Índice Salud Perfil) semanal
- `om_voz_capa_a` — Datos fuentes externas (Google Trends, Meta, GBP, BOE, INE...)
- `om_voz_senales` — Señales detectadas (A/B/C)
- `om_voz_calendario` — Calendario contenido semanal
- `om_voz_perfil_plantilla` — Plantillas perfiles por canal
- `om_voz_competidor` — Inteligencia competitiva
- `om_mensajes_wa` — Historial WhatsApp
- `om_llamadas` — Historial llamadas

### Pilates — Conocimiento y Procesos (5 tablas)
- `om_adn` — ADN organizacional (principios innegociables/flexibles)
- `om_procesos` — Procesos operativos documentados
- `om_conocimiento` — Base de conocimiento (hipótesis/validado/consolidado)
- `om_onboarding_instructor` — Onboarding instructores
- `om_tensiones` — Tensiones activas (competencia, regulatorio, crisis)

### Pilates — Pagos y Finanzas (5 tablas)
- `om_redsys_pedidos` — Operaciones Redsys/Caja Rural
- `om_pago_recurrente` — Config cobros automáticos Stripe
- `om_cobros_automaticos` — Registro intentos cobro
- `presupuestos` — Presupuesto mensual
- `costes_llm` — Tracking costes por modelo/operación

### Otras (24 tablas)
- `om_sesiones_consejo`, `om_diagnosticos_tenant`, `om_depuracion` — Séquito + ACD
- `om_dias_esperados` — Asistencia esperada por mes
- `om_cliente_tenant`, `om_datos_clinicos` — Multi-tenant + clínico
- `om_onboarding_links`, `om_lista_espera`, `om_portal_conversaciones` — Portal + onboarding
- `om_cliente_perfil`, `om_cliente_eventos` — Engagement
- `om_feed_estudio` — Feed noticias tiempo real
- `celdas_matriz` — 21 celdas: 3L × 7F
- `ejecuciones`, `embeddings_inteligencias`, `datapoints_efectividad`, `perfil_gradientes` — Telemetría motor
- `code_os_sessions`, `code_os_visions`, `code_os_briefings`, `code_os_iterations`, `code_os_files`, `code_os_results` — Code OS

## VARIABLES DE ENTORNO

### Obligatorias
| Variable | Uso | Dónde |
|----------|-----|-------|
| `DATABASE_URL` | Conexión Postgres fly.io | settings.py |
| `ANTHROPIC_API_KEY_1..4` | 4 keys rotativas Anthropic | settings.py |
| `OPENROUTER_API_KEY` | OpenRouter (Opus, Sonnet, GPT-4o) | enjambre.py, compositor.py, cockpit.py |
| `STRIPE_SECRET_KEY` | Cobros recurrentes | stripe_pagos.py |
| `STRIPE_WEBHOOK_SECRET` | Verificar webhooks Stripe | stripe_pagos.py |
| `PERPLEXITY_API_KEY` | Búsqueda dirigida, Capa A voz | voz.py, buscador.py |
| `JESUS_TELEFONO` | WhatsApp del dueño (briefings, alertas) | router.py, portal_publico.py |

### Opcionales / Deploy
| Variable | Uso |
|----------|-----|
| `BASE_URL` | URL base (default: https://motor-semantico-omni.fly.dev) |
| `PORT` | Puerto servidor (default: 8080) |
| `REASONING_MODEL` | Modelo razonamiento OpenRouter |
| `BRAIN_MODEL` | Modelo cerebro OpenRouter |
| `CHAT_MODEL` | Modelo chat cockpit OpenRouter |

## API — 137 ENDPOINTS (por dominio)

| Dominio | # | Endpoints principales |
|---------|---|----------------------|
| `/clientes` | 4 | CRUD clientes + tenant |
| `/contratos` | 3 | CRUD contratos, validar plazas |
| `/grupos` | 3 | Lista, detalle, agenda |
| `/sesiones` | 6 | Crear, semana, hoy, completar, marcar asistencia |
| `/cargos` | 3 | Lista, crear, suscripciones mensuales |
| `/pagos` | 2 | Registrar pago + FIFO reconcile |
| `/facturas` | 8 | CRUD, PDF, anular, auto-facturar, paquete gestor |
| `/onboarding` | 4 | Crear enlace, completar registro |
| `/whatsapp` | 9 | Mensajes, enviar, confirmar mañana, respuesta sugerida |
| `/briefing` | 2 | Generar, enviar por WA |
| `/cockpit` | 3 | Contexto día, config módulos, chat |
| `/acd` | 11 | Diagnosticar, enjambre, G4, recompilar, director, metacognitivo |
| `/consejo` | 4 | Convocar, historial, decisión ternaria |
| `/voz/*` | 30 | Propuestas, IRC, ISP, PCA, estrategia, calendario, ciclos, cron |
| `/af/*` | 8 | AF1-AF7 individuales + ejecutar todos |
| `/sistema` | 18 | Vigilar, mecánico, autofagia, enjambre, G4, evaluador, propiocepción |
| `/organismo` | 7 | Dashboard, bus, pizarra, config-agentes, director, evaluación |
| `/bus` | 4 | Emitir, pendientes, procesar, historial |
| `/feed` | 3 | Timeline, marcar leído, count |
| Otros | 12 | Dashboard, alertas, cron, portal, engagement, stripe, cobros, buscar |

## FRONTEND — DESIGN SYSTEM NEURAL DARK

### Paleta (5 capas de fondo)
```
void: #08090d → deep: #0e1019 → surface: #12151e → elevated: #181c28 → overlay: #1e2235
```

### Acentos (7 colores)
```
indigo: #6366f1  green: #34d399  amber: #fbbf24  red: #f87171
violet: #a78bfa  cyan: #22d3ee   rose: #fb7185
```

### Tipografía
- Display: Instrument Sans (títulos)
- Body: Inter Tight (texto)
- Mono: JetBrains Mono (código, datos)

### Tailwind v4
- Plugin: `@tailwindcss/vite` en vite.config.js
- Config: `@theme {}` en index.css (NO tailwind.config.js)
- Variables: `:root` en index.css con `--bg-void`, `--accent-indigo`, etc.

### Rutas
```
/                    → EstudioCockpit (cockpit del día)
/profundo            → Profundo (diagnóstico + tabs verticales)
/portal/:token       → PortalChat (chat cliente autenticado)
/onboarding/:token   → Onboarding (registro 5 pasos)
/info                → PortalPublico (chat marketing)
```

## CONVENCIONES

- Python 3.12+, type hints obligatorios
- async/await para todo IO (DB, LLM calls)
- Logging estructurado con `structlog`
- Errores explícitos, no silenciosos
- Cada módulo tiene docstring de 1 línea explicando qué hace
- Tests con pytest + pytest-asyncio
- Variables de entorno para secrets

## PIPELINE — 7 CAPAS

```
Capa 0: DETECTOR     → 7 primitivas + 8 ops sintácticas         (~200ms, $0, código puro)
Capa 1: ROUTER       → Sonnet selecciona 4-5 inteligencias     (~2-5s, ~$0.02-0.05)
Capa 2: COMPOSITOR   → NetworkX genera algoritmo óptimo         (~100ms, $0)
Capa 3: GENERADOR    → Templates → prompts exactos              (~50ms, $0)
Capa 4: EJECUTOR     → Haiku extrae, Sonnet integra             (30-120s, $0.30-0.80)
Capa 5: EVALUADOR    → Scorer heurístico + detección falacias   (~50ms, $0)
Capa 6: INTEGRADOR   → Sonnet síntesis final                    (10-20s, $0.10-0.20)
```

## CAPA 0 — DETECTOR DE HUECOS (código puro, $0)

Antes del router. Analiza el input con 7 primitivas sintácticas + 8 operaciones del Marco Lingüístico.
Detecta: qué falta en el input (verbos sin objeto, creencias sin evidencia, etc.)
Output: lista de huecos tipificados que informan al router sobre qué inteligencias activar.

Las 8 operaciones: Modificación, Predicación, Complementación, Transitividad, Subordinación, Cuantificación, Conexión, Transformación.

## 6 MODOS CONCEPTUALES (Inteligencia × Pensamiento × Modo)

| Modo | Descripción | Inteligencias naturales |
|------|-------------|------------------------|
| ANALIZAR | Descomponer, demostrar, medir | INT-01, INT-02, INT-07 |
| PERCIBIR | Ver patrones, detectar forma | INT-03, INT-04, INT-15 |
| MOVER | Actuar, posicionar, construir | INT-05, INT-16, INT-10 |
| SENTIR | Empatizar, intuir, habitar | INT-08, INT-10, INT-18 |
| GENERAR | Crear, imaginar, proyectar | INT-14, INT-12, INT-13 |
| ENMARCAR | Nombrar, negociar, dar sentido | INT-09, INT-06, INT-17 |

Estos coexisten con los 4 modos API (análisis, generación, conversación, confrontación) que son configuraciones del pipeline.

## 13 REGLAS DEL COMPILADOR (OBLIGATORIAS)

1. **Núcleo irreducible:** Siempre ≥1 de {INT-01,INT-02} + ≥1 de {INT-08,INT-17} + INT-16
2. **Máximo diferencial:** Priorizar pares cuantitativo-existencial
3. **Sweet spot:** 4-5 inteligencias. <3 = puntos ciegos. >6 = rendimiento decreciente
4. **Formal primero:** En composiciones, formal/distante primero → humano/cercano después
5. **No reorganizar:** Secuencia lineal (A→B)→C supera agrupada A→(B→C)
6. **Fusiones con cuidado:** Orden afecta framing. Primero la más alineada con el sujeto
7. **Loop test siempre:** 2 pasadas por defecto en modo análisis/confrontación
8. **No tercera pasada:** n=3 no justifica coste excepto calibración
9. **Fusiones paralelizables ~70%:** Factorizar A→(B|C) pierde ~30%. Aceptable si no TOP 5
10. **Cruce previo NO factorizable:** (B|C)→A siempre junto. Valor irreducible
11. **Marco binario universal:** Primera acción = INT-14 (ampliar) + INT-01 (filtrar)
12. **Conversación pendiente universal:** Buscar este patrón como output mínimo
13. **Infrautilización antes de expansión:** Medir uso actual antes de construir nuevo

## 4 MODOS

| Modo | Inteligencias | Profundidad | Latencia |
|------|---------------|-------------|----------|
| análisis | 4-5, máx diferencial | 2 pasadas | <150s |
| generación | creativas (INT-14,15,09) | 1 pasada | <90s |
| conversación | 2-3, routing rápido | 1 pasada | <60s |
| confrontación | frontera (INT-17,18) | 2 pasadas | <120s |

## RESTRICCIONES

- Coste máximo por ejecución: $1.50
- 4 API keys Anthropic rotativas
- Presupuesto testing: ~€150
- Haiku para extracción, Sonnet para routing/integración, Opus solo si frontera

## PROTOCOLO PRE-LLM: VERIFICACIÓN LOCAL OBLIGATORIA

Antes de hacer CUALQUIER llamada a un modelo LLM externo (OpenRouter, Anthropic API, etc.), VERIFICAR LOCALMENTE todo lo verificable. Las llamadas a modelos caros (Opus: $5/$25 por M tokens) NO son para experimentar.

### Checklist OBLIGATORIO antes de llamar a un LLM:

1. **Model ID correcto** — Verificar que el ID del modelo es exacto para el proveedor:
   - OpenRouter usa PUNTOS: `anthropic/claude-opus-4.6` (NO `anthropic/claude-opus-4-6`)
   - Opus 4.6 ($5/$25) vs Opus 4 ($15/$75) — un typo puede costar 3x más
   - Verificar contra la documentación del proveedor, no asumir

2. **JSON parser robusto** — Si se espera JSON del LLM:
   - Usar `response_format: {"type": "json_object"}` si el modelo lo soporta
   - Tener parser que maneje: truncamiento, markdown fences, trailing commas, brackets sin cerrar
   - TESTEAR el parser localmente con casos edge ANTES de hacer la llamada

3. **Imports y dependencias** — Verificar que todos los imports existen:
   - `from src.pilates.X import Y` — verificar que Y existe en X
   - Si se reutiliza una función de otro módulo (ej: `_parse_json_robusto`), verificar que existe y funciona

4. **Queries SQL** — Ejecutar las queries contra la DB real ANTES de la llamada:
   - Verificar que las tablas existen
   - Verificar que los datos esperados están ahí
   - Verificar que el formato de salida es el esperado

5. **System prompt y user prompt** — Revisar que:
   - No superen el límite de tokens del modelo
   - El prompt pide el formato de respuesta correcto
   - max_tokens es suficiente para la respuesta esperada (truncamiento = dinero tirado)

6. **Timeout y error handling** — Configurar:
   - Timeout adecuado (Opus puede tardar 120-180s)
   - Manejo de errores que no pierda la respuesta parcial
   - Log del raw response para debugging sin repetir la llamada

7. **Endpoint HTTP** — Si se llama via endpoint:
   - Verificar que el endpoint existe y devuelve 200 (sin la parte LLM)
   - Verificar que curl/test tiene timeout suficiente

### Principio: UNA llamada, bien hecha

- Verificar TODO localmente → hacer UNA sola llamada → verificar resultado
- Si la llamada falla: analizar el error del log, NO repetir sin entender qué falló
- Si el JSON está truncado: arreglar max_tokens o parser, NO repetir la llamada
- Coste de referencia: Opus ~$0.20-0.50 por llamada. 10 llamadas experimentales = $2-5 tirados

### Modelos y costes (OpenRouter, marzo 2026)

| Modelo | ID OpenRouter | Input/M | Output/M | Uso |
|--------|---------------|---------|----------|-----|
| Opus 4.6 | `anthropic/claude-opus-4.6` | $5 | $25 | Director, Meta-Cognitivo (mensual) |
| Sonnet 4.6 | `anthropic/claude-sonnet-4-6-20250514` | $3 | $15 | Enjambre, Recompilador |
| Haiku 3.5 | `anthropic/claude-3.5-haiku` | $0.80 | $4 | Extracción, routing |
| GPT-4o | `openai/gpt-4o` | $2.50 | $10 | Cockpit chat |

## DEPLOY

### Proceso
```bash
# 1. Build frontend
cd frontend && npm run build && cd ..

# 2. Deploy a fly.io
fly deploy

# 3. Verificar
curl -s https://motor-semantico-omni.fly.dev/health | jq .

# 4. Test de humo
curl -s https://motor-semantico-omni.fly.dev/pilates/grupos | jq .
```

### Rollback
```bash
# Ver releases anteriores
fly releases

# Rollback a release anterior
fly deploy --image <image-ref-anterior>
```

### DB (fly.io Postgres)
```bash
# Conectar a la DB
fly postgres connect -a motor-semantico-omni-db

# Ejecutar SQL desde archivo
fly ssh console -a motor-semantico-omni -C "python -c \"import asyncio; from src.db.client import get_pool; ...\""
```

## ANTI-PATRONES (errores que NO repetir)

### Costes
- **$30 quemados en 30 minutos** por llamadas experimentales a Opus sin verificar localmente
- **Model ID con guiones en vez de puntos** → OpenRouter cobra modelo incorrecto o falla silenciosamente
- **max_tokens insuficiente** → JSON truncado → se repite la llamada → doble coste
- **10 llamadas de prueba** en vez de UNA bien preparada → $2-5 tirados cada vez

### Código
- **Import de función inexistente** → crash en runtime, después de haber hecho la llamada LLM cara
- **`fly ssh` vs `fly postgres connect`** → `fly ssh` es para la app, `fly postgres connect` para la DB directamente
- **Bus endpoint devuelve array, no objeto** → siempre usar `Array.isArray(data) ? data : (data.recientes || [])` para endpoints de bus/pizarra
- **Frontend dist en .gitignore** → no intentar `git add frontend/dist/`, se construye durante Docker build
- **CSS variables duplicadas** → index.css (Neural Dark) vs App.css (legacy). Si se duplican `:root`, gana el último

### Operaciones
- **curl sin timeout** a endpoints con LLM → timeout del terminal antes que del servidor. Usar `curl --max-time 300`
- **SSH escaping** → comillas dobles dentro de comillas dobles rompen el comando. Usar heredoc o base64
- **Deploy sin build** → el Dockerfile hace el build del frontend, pero si se testea localmente necesita `npm run build` primero

## TRACKING DE COSTES

Para cada sesión que involucre llamadas LLM, registrar:

```sql
-- Consultar costes acumulados
SELECT DATE(created_at) as dia,
       SUM((payload->>'coste_total_usd')::numeric) as coste_usd,
       COUNT(*) as llamadas
FROM om_senales_agentes
WHERE tenant_id='authentic_pilates'
  AND payload->>'coste_total_usd' IS NOT NULL
GROUP BY 1 ORDER BY 1 DESC LIMIT 10;
```

La tabla `costes_llm` tiene tracking por modelo/operación/celda con tokens_in, tokens_out, coste_total_usd.

## BRIEFINGS DE IMPLEMENTACIÓN

Los briefings están en `briefings/` y se ejecutan en orden secuencial. Cada uno es autónomo.

```
ORDEN:
1. briefings/BRIEFING_00_SCAFFOLD.md   → Estructura, deps, Docker, fly.toml, settings, llm_client, main.py
2. briefings/BRIEFING_01_DATOS.md      → Schema SQL, seed, inteligencias.json, marco_linguistico.json, db client
3. briefings/BRIEFING_02_PIPELINE_1_3.md → Detector Huecos, Router, Compositor, Generador
4. briefings/BRIEFING_03_PIPELINE_4_6.md → Ejecutor, Evaluador, Integrador, Orquestador
5. briefings/BRIEFING_04_DEPLOY_TESTS.md → fly.io deploy, tests E2E
6. briefings/BRIEFING_06_FIX_CODE_OS_COMPLETO.md → Fix completo Code OS: DB, try/except, context, agent loop
```

REGLAS:
- Lee el briefing completo ANTES de escribir código
- Cada briefing tiene sección VERIFICACIÓN al final — ejecútala antes de pasar al siguiente
- Las 18 redes de preguntas completas para inteligencias.json están en el documento PROMPT_MVP.md (raíz del repo)
- No inventar datos. Copiar literal del briefing y del PROMPT_MVP.md
- Si un briefing falla verificación, arréglalo antes de avanzar

## PROTOCOLO DE EJECUCIÓN AUTÓNOMA DE BRIEFINGS

Cuando el usuario te pida ejecutar un briefing, EJECUTA TODO SIN PEDIR CONFIRMACIÓN:

1. Lee el briefing completo
2. Ejecuta CADA tarea en orden: SQL con db queries, ediciones con edit_file, comandos con bash
3. Verifica CADA tarea tras ejecutarla
4. Si algo falla, arréglalo y continúa
5. Al terminar TODO: resumen de qué se hizo, qué pasó, qué queda pendiente
6. git add + commit + push
7. Deploy si aplica

NUNCA:
- No pidas permiso para ejecutar SQL
- No pidas permiso para editar archivos
- No pidas confirmación entre tareas
- No describas lo que VAS a hacer — HAZLO
- No muestres el SQL sin ejecutarlo

SIEMPRE:
- Lee archivos antes de editarlos
- Verifica tras cada cambio
- Si algo falla, intenta arreglarlo antes de reportar
