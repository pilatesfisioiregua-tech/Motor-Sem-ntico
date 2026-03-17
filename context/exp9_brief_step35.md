# BRIEFING PARA DISEÑADOR DE PRODUCTO — OMNI-MIND v4

**Fecha:** 2026-03-12  
**Estado:** CR0 — Validación y cierre pendiente  
**Destinatario:** Diseñador de Producto (Implementación técnica y estratégica)  
**Alcance:** Producto mínimo viable (MVP) para pilotos Pilates/Fisioterapia con stack OS-first

---

## 1. VISIÓN Y PROPUESTA DE VALOR

### 1.1 Qué es OMNI-MIND (Maestro §1)

Un organismo cognitivo que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas — es un sistema vivo que compila un programa cognitivo nuevo para cada interacción.

**El principio central**

**El prompt del agente no tiene instrucciones imperativas. Es exclusivamente una red de preguntas.** La inteligencia emerge de la estructura de preguntas, no de instrucciones al modelo. No le dices al agente "analiza como financiero" — le das la red de preguntas de INT-07 y el agente no puede hacer otra cosa que operar financieramente.

Las preguntas no son output del agente (no las verbaliza). Son su **sistema operativo interno** — la lente a través de la cual mira y procesa.

**Los componentes**

```
LA MATRIZ (3L × 7F × 18INT × preguntas)
  = el producto
  = el prompt del agente
  = el algoritmo operativo
  → §2

EL GESTOR DE LA MATRIZ (mira hacia dentro)
  = mantiene, poda, mejora y compila la Matriz
  = alimenta a TODOS los consumidores (Motor, Exocortex, Chief of Staff)
  = acumula conocimiento transversal de efectividad
  → §6E (NUEVO)

EL MOTOR vN (mira hacia fuera)
  = ejecuta la Matriz sobre casos de usuarios
  = genera los datapoints de efectividad que alimentan al Gestor
  → §6B

LOS REACTORES (cartografía, reactor v1, v2, v3, meta-motor)
  = la fábrica que construye, llena y enriquece la Matriz
  → §6

EL ÁLGEBRA DEL CÁLCULO SEMÁNTICO
  = el compilador que ensambla las preguntas en prompts ejecutables
  → §3

LAS 8 OPERACIONES SINTÁCTICAS (Marco Lingüístico)
  = la gramática de cada pregunta individual
  → §1D

EL PIPELINE
  = la secuencia de ejecución: percibir gaps → compilar prompt → ejecutar → verificar cierre
  → §4
```

**Los dos loops**

```
LOOP RÁPIDO — Motor vN (cadencia: minutos)
  Caso entra → ejecuta con Matriz actual → registra efectividad → siguiente caso
  Mira HACIA FUERA: opera sobre casos de usuarios
  
LOOP LENTO — Gestor de la Matriz (cadencia: horas/días)
  Cada N ejecuciones → analiza patrones → poda/mejora → recompila programas
  Mira HACIA DENTRO: opera sobre la Matriz misma
  
El Motor NO se reconfigura en caliente. Ejecuta con lo que tiene.
El Gestor revisa periódicamente y le entrega una Matriz mejorada.
```

### 1.2 Tres Conceptos Fundamentales (Maestro §1A)

**INTELIGENCIA = qué ves (y qué no puedes ver)**

Un sistema de percepción con objetos propios, operaciones propias y un punto ciego estructural. Hay 18 (hoy — evolucionable). Cada una es un "vocabulario de percepción" diferente.

9 categorías empíricas (derivadas de 34 chats de cartografía):

| # | Categoría | Inteligencias | Qué comparten |
|---|-----------|---------------|---------------|
| 1 | Cuantitativa | INT-01, INT-02, INT-07 | Operan sobre lo medible |
| 2 | Sistémica | INT-03, INT-04 | Mapean relaciones entre partes |
| 3 | Posicional | INT-05, INT-06 | Ven actores, movimientos, poder |
| 4 | Interpretativa | INT-08, INT-09, INT-12 | Interpretan sentido humano |
| 5 | Corporal-Perceptual | INT-10, INT-15 | Perciben forma encarnada |
| 6 | Espacial | INT-11 | Topología visual |
| 7 | Expansiva | INT-13, INT-14 | Abren espacio de opciones |
| 8 | Operativa | INT-16 | Construye |
| 9 | Contemplativa-Existencial | INT-17, INT-18 | Significado último |

6 irreducibles (no sustituibles por combinación): INT-01, INT-02, INT-06, INT-08, INT-14, INT-16.

**PENSAMIENTO = cómo procesas lo que percibes**

17 tipos en tres familias:

- **Interno** (10): percepción, causalidad, abstracción, síntesis, discernimiento, metacognición, consciencia epistemológica, auto-diagnóstico, convergencia, dialéctica
- **Lateral** (7): analogía, contrafactual, abducción, provocación, reencuadre, destrucción creativa, creación
- **Inter-álgebra** (4): fusión, composición, diferencial, lectura cruzada

**MODO = para qué estás mirando**

6 modos: ANALIZAR, PERCIBIR, MOVER, GENERAR, ENMARCAR. No toda inteligencia opera bien en todos los modos.

**Combinatoria**

```
Configuración de un paso = Inteligencia × Pensamiento × Modo
Espacio teórico: 18 × 17 × 6 = 1.836
Espacio útil: ~180 (acotado por compatibilidad y gradientes)
```

MVP: motor selecciona inteligencia + modo. Pensamiento se activa implícitamente por las preguntas. Selección explícita de los tres en v2+.

### 1.3 La Matriz — 3L × 7F × 18INT (Maestro §2)

**El esquema central**

```
DIMENSIÓN 1 — 3 LENTES (para qué):
  Salud:       ¿Funciona?
  Sentido:     ¿Tiene dirección?
  Continuidad: ¿Sobrevive más allá del sistema?

DIMENSIÓN 2 — 7 FUNCIONES (qué necesita):
  F1 Conservar / F2 Captar / F3 Depurar / F4 Distribuir
  F5 Frontera / F6 Adaptar / F7 Replicar

DIMENSIÓN 3 — 18 INTELIGENCIAS (quién lo ve):
  INT-01 a INT-18
```

378 posiciones (3 × 7 × 18). Cada pregunta tiene coordenadas exactas.

**Las 21 celdas como campo de gradientes**

Cada celda tiene grado actual (0.0-1.0), grado objetivo (contextual), y gap = objetivo - actual. El gap genera la fuerza que dirige la ejecución. Mayor gap = más prioridad.

### 1.4 Firmas de las 18 Inteligencias (Catálogo Completo)

**INT-01: LÓGICO-MATEMÁTICA**
- **Firma:** Contradicción formal demostrable entre premisas
- **Objetos:** Estructuras, relaciones, pruebas, axiomas
- **Punto ciego:** Lo ambiguo, lo parcial, lo no-axiomatizable
- **Resumen:** Detecta trade-offs irreducibles y sistemas subdeterminados. El "enterprise pivot" es reframeable como upsell a existentes (semanas, no meses).

**INT-02: COMPUTACIONAL**
- **Firma:** Dato trivializador ausente + atajo algorítmico
- **Objetos:** Algoritmos, estados, complejidad, datos
- **Punto ciego:** Lo no-computable, la intuición, el juicio cualitativo
- **Resumen:** La clínica es un problema de scheduling con capacidad ociosa no explotada: el sillón 3 vacío el 40% del tiempo equivale a ~6.000€/mes potenciales sin invertir un euro.

**INT-03: ESTRUCTURAL (IAS)**
- **Firma:** Gap id↔ir + actor invisible con poder
- **Objetos:** Coordenadas sintácticas, formas, niveles, huecos
- **Punto ciego:** No genera soluciones — solo diagnóstico
- **Resumen:** El odontólogo opera como recurso crítico y cuello de botella simultáneo. Trabaja 60h/semana con un tercer sillón vacío el 40% del tiempo, y su respuesta es ampliar a 5 sillones.

**INT-04: ECOLÓGICA**
- **Firma:** INTERDEPENDENCIA — nada existe aislado, todo afecta a todo
- **Objetos:** Ecosistemas, ciclos, nichos, resiliencia, flujos
- **Punto ciego:** No ve al individuo — solo al sistema completo
- **Resumen:** La clínica dental es un monocultivo humano. Un solo organismo (el dentista) ocupa tres nichos simultáneos — productor, gestor, estratega — sin redundancia.

**INT-05: ESTRATÉGICA**
- **Firma:** ANTICIPACIÓN — pensar dos movimientos adelante
- **Objetos:** Posición, recursos, movimientos, ventanas temporales, opciones
- **Punto ciego:** Asume competición — no modela cooperación ni conflicto interno
- **Resumen:** Abrir sábados antes de optimizar utilización = quemar recurso escaso sin dato.

**INT-06: POLÍTICA**
- **Firma:** NEGOCIACIÓN — redistribuir poder mediante acuerdo
- **Objetos:** Poder, alianzas, legitimidad, narrativa, coaliciones
- **Punto ciego:** Confunde poder con verdad — lo que tiene apoyo no es necesariamente correcto
- **Resumen:** Quien puede bloquear sin decidir: la esposa. No va a firmar un veto explícito, pero su agotamiento acumulado puede convertirse en plebiscito silencioso.

**INT-07: FINANCIERA**
- **Firma:** DESCUENTO TEMPORAL — todo valor se traduce a presente
- **Objetos:** Flujos, posiciones, riesgo, apalancamiento, opcionalidad
- **Punto ciego:** Lo que no tiene precio no existe
- **Resumen:** 7K€/mes × 12 = 84K€/año. Si trabaja 2.500h/año = 33.6€/h. ¿A qué hora deja de valer?

**INT-08: SOCIAL**
- **Firma:** EMPATÍA — leer el estado interno del otro (o propio) sin que lo verbalice
- **Objetos:** Emociones, intenciones, dinámicas, patrones reactivos, vínculos
- **Punto ciego:** Sobrepsicologiza — puede ver conflicto emocional donde hay problema estructural
- **Resumen:** Pide validación para expandir. Necesita permiso para no hacerlo. El acto de preguntar "¿debería expandir?" ya revela que no quiere hacerlo.

**INT-09: LINGÜÍSTICA**
- **Firma:** REENCUADRE — cambiar el marco lingüístico cambia lo que es visible
- **Objetos:** Palabras, marcos, narrativas, metáforas, actos de habla
- **Punto ciego:** Confunde nombrar con resolver — poner nombre no cambia la estructura
- **Resumen:** "Crecer" enmarca expansión como progreso. "Intensificar sacrificio" es el mismo acto, distinto marco.

**INT-10: CINESTÉSICA**
- **Firma:** SENTIR TENSIÓN — el cuerpo detecta lo que la mente racionaliza
- **Objetos:** Movimiento, tensión, ritmo, coordinación, flujo corporal
- **Punto ciego:** No verbaliza — sabe pero no puede explicar qué sabe
- **Resumen:** El cuerpo sabe algo que el análisis confirma pero no puede sentir: la historia del padre no es un dato — es una memoria somática.

**INT-11: ESPACIAL**
- **Firma:** CAMBIO DE PERSPECTIVA — rotar el objeto para ver la cara oculta
- **Objetos:** Formas, distancias, perspectivas, mapas, proporciones
- **Punto ciego:** Lo que no tiene extensión no existe — no ve procesos, solo configuraciones
- **Resumen:** El mapa espacial de la clínica dental revela un sistema con centro colapsado y periferia vacía. El odontólogo es el punto de máxima compresión.

**INT-12: NARRATIVA**
- **Firma:** DAR SENTIDO — convertir hechos en historia con dirección
- **Objetos:** Arco, personaje, transformación, secuencia, significado temporal
- **Punto ciego:** Fuerza protagonista y arco donde puede no haberlos
- **Resumen:** El odontólogo vive dentro de una historia que no escribió: la del padre trabajador que se sacrifica hasta romperse.

**INT-13: PROSPECTIVA**
- **Firma:** SIMULAR FUTUROS — explorar qué pasa si X, Y o Z
- **Objetos:** Tendencias, señales débiles, escenarios, distribuciones de probabilidad
- **Punto ciego:** El cisne negro — lo que no tiene precedente no aparece en el modelo
- **Resumen:** Escenario A: crece y colapsa en 18 meses. B: optimiza y estabiliza. C: reduce y recupera vida.

**INT-14: DIVERGENTE**
- **Firma:** GENERACIÓN — producir opciones que no existían antes
- **Objetos:** Posibilidades, conexiones remotas, combinaciones inusuales
- **Punto ciego:** Todo es posible, nada es evaluable — genera sin filtrar
- **Resumen:** El odontólogo ve 2 opciones; existen al menos 20. Su trampa central es la fusión de roles.

**INT-15: ESTÉTICA**
- **Firma:** JUICIO DE COHERENCIA — detectar que algo "no encaja" sin saber por qué
- **Objetos:** Armonía, tensión, elegancia, proporción, coherencia formal
- **Punto ciego:** Lo feo puede ser verdadero, lo bello puede ser falso
- **Resumen:** La tristeza dice: "esto ya lo sé, esto ya lo he visto". Dice que el final está escrito a menos que alguien cambie el guion.

**INT-16: CONSTRUCTIVA**
- **Firma:** CONSTRUIR — convertir diseño en realidad funcional
- **Objetos:** Restricciones, materiales, soluciones, prototipos, iteraciones
- **Punto ciego:** Optimiza lo existente — no cuestiona si debería existir
- **Resumen:** Si el churn baja con fixes, el sprint quirúrgico asume datos de churn no verificados — necesita exit interviews.

**INT-17: EXISTENCIAL**
- **Firma:** CONFRONTAR — preguntar "¿para qué?" hasta llegar al fondo
- **Objetos:** Propósito, libertad, responsabilidad, finitud, valores
- **Punto ciego:** Puede paralizar por exceso de profundidad
- **Resumen:** ¿7K€/mes con tus hijos viéndote ES el éxito, y 15K€/mes sin verlos es el fracaso?

**INT-18: CONTEMPLATIVA**
- **Firma:** OBSERVAR SIN JUZGAR — ver lo que es, sin necesidad de cambiarlo
- **Objetos:** Presencia, vacío, observación, paradoja, no-acción
- **Punto ciego:** Puede desconectar de la acción — observar sin actuar
- **Resumen:** Si firma el crédito, la pausa desaparece. La deuda nueva obliga a producir. Producir obliga a más horas. Más horas destruyen lo que la esposa está señalando.

### 1.5 Casos de Uso Piloto

**Piloto 1: Estudio de Pilates (Jesús)**
- Telemetría: reservas, asistencia, clientes, sesiones, ingresos
- Reactor v4 genera preguntas desde patrones reales del estudio
- Validación: ¿los agentes detectan cosas que Jesús no veía?
- Exocortex conectado a datos reales del estudio

**Piloto 2: Clínica de Fisioterapia (mujer de Jesús)**
- Segundo dominio diferente: valida transferencia cross-dominio
- Test clave: ¿preguntas de Pilates sobre gestión de agenda aplican a fisio? ¿Y viceversa?
- Telemetría: pacientes, tratamientos, agenda, derivaciones

**Ola 4: Integración con software de gestión**
- Capa de telemetría que lee datos del software existente via API
- Agentes V3.2 inyectados en cada módulo con prompt compilado por el Gestor
- Reactor v4 observa datos de clientes del amigo informático

---

## 2. ARQUITECTURA E IMPLEMENTACIÓN

### 2.1 Contexto del Sistema Actual (MEMORY.md)

**Infraestructura**
- **Producción:** Supabase `cptcltizauzhzbwxcdft` — `https://cptcltizauzhzbwxcdft.supabase.co`
- **Staging:** Supabase `jbfiylwbgxglqwvgsedh` — ANTHROPIC_API_KEY configurado, falta OPENAI_API_KEY
- **Edge Functions:** 99 funciones Deno/TypeScript. Deploy: `supabase functions deploy <name> --no-verify-jwt`
- **Migraciones:** 47 SQL (bootstrap + 46 timestamped)
- **LLM:** Todas las llamadas via `llm-proxy` Edge Function. Soporta Haiku (parseadores, detectores) y Sonnet (diseño, síntesis). Fallback automático
- **Plan Supabase:** Free tier: 150s timeout, 500MB DB
- **Presupuesto:** €200/mes. Coste actual: ~$0.005/ciclo ≈ $15/mes

**Comunicación entre agentes**
**REGLA ABSOLUTA**: Los agentes NUNCA se llaman entre sí. Toda comunicación es via la tabla `marcas_estigmergicas`:
- Un agente escribe una marca (tipo: hallazgo, sintesis, alerta, propuesta, etc.)
- Otro agente lee marcas y actúa sobre ellas
- Cross-enjambre: tabla `marcas_cross` (origen_enjambre → destino_enjambre, expiran en 72h)

**Fire-and-forget (pg_net)**
Para disparar agentes en background sin esperar respuesta:
- `disparar_edge_function(p_url, p_key, p_function_name, p_payload)` — genérica, cualquier función
- `disparar_profundo_runner(p_url, p_key, p_sesion_id, p_ciclo_id, p_input, p_datos_previos)` — específica profundo

**Tablas Principales**
- `marcas_estigmergicas`: Comunicación estigmérgia. CHECK en `tipo`: hallazgo, sintesis, alerta, triage, basal, prescripcion, verbalizacion, propuesta, meta, respuesta, senal, profundo_resultado
- `estado_agentes`: Registro de todos los agentes con capa, modelo, estado
- `enjambres`: Registro de enjambres con misión y config
- `registro_arquitectura`: 157+ componentes (87+ edge_fn, 40 tabla, 29 módulo, 4 script, 1 interfaz)
- `sesiones_chief`: Sesiones del chat con turnos, dominio, intención
- `perfil_usuario`: Perfil cognitivo acumulado entre sesiones (patrones, sesgos, datos)
- `cola_emergencia`: Insights del profundo dosificados al usuario
- `datapoints_efectividad`: Feedback loop del Gestor (gap_pre, gap_post, tasa_cierre)

**Enjambres Activos**
1. **IAS** (Pipeline diagnóstico): ~10 agentes, capas 1-5, funcional
2. **Diseño** (Meta-diseño): 18 agentes, capas 1-6, E2E funcional
3. **Chief of Staff**: Pipeline dual superficial+profundo — DEPRECADO en v4 pero aún operativo con 24 agentes (~6.900 líneas)
4. **Mejora Continua**: 3 agentes (detector, procesador, basal), capas 1-3, operativo

### 2.2 Pipeline de Ejecución (Exp 5 y Exp 6)

**Exp 5 — Cadena de Montaje (Análisis de Pipeline Lineal)**

Configuraciones testeadas (40 runs = 8 configs × 5 tasks):

| Config | Nombre | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|--------|------|------|------|------|------|--------|-------|
| A | Linea Industrial | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| D | Ultra-Barato | 0% | 80% | 90% | 0% | 86% | 51% | $0.05 |
| B | Coder Puro | 0% | 93% | 91% | 0% | 0% | 37% | $0.14 |
| G | Razonadores | 0% | 0% | 90% | 0% | 75% | 33% | $0.19 |
| 0 | Baseline | 0% | 0% | 83% | 0% | 75% | 32% | $0.03 |

**Hallazgos críticos de Exp 5:**
1. Pipeline lineal: techo 56%. NO reemplaza a Code
2. T4 (Orquestador async): 0% en 8/8 configs — techo ESTRUCTURAL
3. Config D Pareto: 51% a $0.05 — 7x más barato que A para -5%
4. Premium PEOR: 15% a $0.34 — pagar más NO ayuda
5. Debugger poco eficaz: 5/35 mejoras. Reviewer ROMPE código funcional (3 casos)

**Exp 6 — Agente de Coding OS (Loop Agéntico)**

| Approach | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exp 5 Config A | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| **Agente multi-modelo** | **100%** | **100%** | **100%** | **93%** | **100%** | **99%** | $1.57 |
| Agente Devstral solo | 83% | — | — | **100%** | — | — | $0.66 |
| Agente MiMo solo | 79% | — | — | 96% | — | — | $0.92 |

**Hallazgos críticos de Exp 6:**
1. T4 RESUELTO: 0% en 11 configs pipeline → 93% con agente (13/14 tests)
2. Devstral solo = 100% en T4 a $0.66
3. Step 0% en T4 como agente — piensa sin actuar
4. MiMo+loop (88%) SUPERA pipeline caro sin loop (56%)
5. 460 líneas bastan. Loop > cantidad de modelos
6. Si tests pasan 100% → finish() inmediato (reviewers rompen código)

**AGENTE Exp 6 — Especificación Técnica:**
- **Herramientas:** 5 herramientas (read_file, write_file, run_command, list_dir, search_files) + finish
- **Routing:** Devstral (genera) → Step (debugea tras 2 errores) → MiMo (fallback)
- **Seguridad:** sandbox path, command blacklist, stuck detection
- **Loop principal:** observe→think→act (max 500 iteraciones configurables)
- **Condiciones de parada:** Control flags check, stuck detection (5 patrones), budget check
- **Recuperación de errores:** Error → ErrorObservation → agente VE el error en historial → decide siguiente acción
- **Multi-modelo:** LLMRegistry + LiteLLM para routing dinámico

### 2.3 Implementación del Motor vN (Maestro §4)

**Pipeline de 7 pasos:**

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
```

---

## 3. MODELO DE NEGOCIO Y ECONOMÍA

### 3.1 Costes Reales (Maestro §14 y Experimentos)

**Costes por Experimento (reales vs estimados):**

| Experimento | Estimado | Real | Factor |
|-------------|----------|------|--------|
| Exp 5 (40 runs) | $5-15 | $1.50 | 3-10x sobrestimado |
| Exp 1 bis (30 runs) | $1-3 | $0.10 | 10-30x sobrestimado |
| Exp 6 (agente) | $3-6 | $1.57 | 2-4x sobrestimado |
| Exp 7 (15 calls) | $3-5 | $0.15 | 20-33x sobrestimado |
| **TOTAL 6 exps** | **$14-33** | **~$5.50** | **3-6x sobrestimado** |

**Coste por turno/chat (Exp 7 R1):**

| Componente | Coste/Turno | Frecuencia | Coste Total |
|------------|-------------|------------|-------------|
| Motor | $0.002 | 1x | $0.002 |
| Analizador | $0.001 | 0.3x | $0.0003 |
| Generador Preguntas | $0.0001 | 2x | $0.0002 |
| Sintetizador | $0.003 | 1x | $0.003 |
| Memoria | $0.0005 | 1x | $0.0005 |
| Validador | $0.0002 | 1x | $0.0002 |
| **Total** | | | **$0.0062** |

- **Costo Objetivo**: <$0.02/turno ✓
- **Latencia Objetivo**: <1s (superficial), <30s (profundo) ✓
- **Mejora**: 84% más barato que sistema anterior ($0.10 → $0.0062)

**Coste Motor vN por ejecución:**
- Fase 1 (OS + Sonnet evaluador): ~$0.32 por caso completo
- Fase 3 (todo OS): ~$0.08-0.09 por caso (70% reducción)

### 3.2 Presupuestos y Roadmap (Maestro §11 y §14)

**Presupuesto por Fase:**

```
FASE A — CARTOGRAFÍA
  Ejecución en claude.ai Pro:                    €0
  Tu tiempo: ~12-15 horas
  COSTE API: €0

FASE B — DATOS SINTÉTICOS
  3 rondas generación + validación:              €60
  Enriquecimiento con fuentes externas:          €20
  Generación preguntas nivel 2 (18 INTs):        €30
  Generación preguntas nivel 3 (10 INTs):        €25
  Validación cruzada (Opus revisa Opus):         €15
  COSTE API: ~€150

FASE C — ENTRENAMIENTO
  Fine-tune embeddings Voyage:                   €5
  Computación (local o fly.io):                  €0
  3 ciclos entrenamiento + evaluación:           €5
  COSTE API: ~€10

FASE D — MOTOR v1
  Desarrollo (Code CLI):                         €0
  Testing pipeline (~100 ejecuciones):           €100-150
  Debugging + re-ejecuciones:                    €50
  COSTE API: ~€150-200

FASE E — CHAT / EXOCORTEX
  Desarrollo:                                    €0
  Testing conversacional (~200 turnos):          €50-80
  Testing capa profunda:                         €30
  COSTE API: ~€80-110

FASE F — PILOTOS (primeros 3 meses)
  Ejecuciones reales (~30/día × 90 días):        €200-400
  Re-entrenamiento con datos reales:             €20
  Cartografía parcial dominios nuevos:           €30
  COSTE API: ~€250-450
```

**Totales acumulados:**

```
Hasta Motor funcionando (A-D):      ~€310-360
Hasta Chat funcionando (A-E):       ~€390-470
Con 3 meses de pilotos (A-F):       ~€640-920
```

**Distribución óptima con €500:**
- €0    Fase A (gratis en claude.ai Pro)
- €100  Fase B (2 rondas + fuentes externas)
- €10   Fase C (entrenamiento)
- €150  Fase D (testing motor)
- €80   Fase E (testing chat)
- €160  Fase F (pilotos — ~2 meses a volumen medio)

**Coste recurrente post-lanzamiento:**
```
Ejecuciones del motor:  ~€1/ejecución × volumen
  10/día = ~€300/mes
  30/día = ~€900/mes
  
Re-entrenamiento mensual: ~€20/mes
Cartografía nuevos dominios: ~€30/dominio (puntual)
```

### 3.3 Modelos Competidores y Diferenciación (Maestro §12)

**Competidores identificados:**
- **Glean**: Sistema de IA para negocios (búsqueda y descubrimiento)
- **Adept**: Agente de IA para tareas de software
- **AutoGPT**: Agente autónomo de propósito general

**Diferenciación OMNI-MIND:**
1. **Matriz 3L×7F**: Estructura única de diagnóstico cognitivo que ningún competidor tiene
2. **Multi-modelo OS**: Diversidad de modelos como dimensión algebraica (vs. monomodelo)
3. **Flywheel cross-dominio**: Cada cliente mejora el sistema para todos los demás
4. **Prompts vivos**: Evolución automática sin intervención manual
5. **Stack 100% OS**: Sin dependencia de proveedores premium (margen >90%)

**Modelo de precios:**
- **Precio**: €50-200/mes por negocio (segmento Pilates/Fisioterapia inicial)
- **Coste**: ~$2-5/mes en tokens
- **Margen**: >90%
- **Justificación**: Capa inteligente que piensa sobre el negocio, no solo automatiza

---

## ANEXO I: RESULTADOS EXPERIMENTALES COMPLETOS

### EXP 4 — Mesa Redonda Multi-Modelo (12 modelos, 2 rondas)

**Hallazgos:**
- Mesa evaluadora producción: V3.2-chat + V3.1 + R1 = 100% cobertura con prompts especializados
- Sintetizador: Cogito-671b #1 sin discusión (3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s)
- Qwen3 inflador (+0.93 vs media global). NO cerebro. 77% de convergencias hacia donde Qwen3 apuntaba en R1
- Auto-tracking inflaba +0.93 puntos. Evaluación externa Claude: media 3.06 (vs auto 3.99)
- Pizarra distribuida: 425 conexiones + 239 puntos ciegos (valor exclusivo). GPT-OSS mayor contribuidor (119), no Qwen3 (63)
- Kimi K2 INERTE (0/5 R2). GLM-4.7 marginal. Opus $75/M 0 únicos. Sonnet 0 únicos.

**Decisiones validadas:**
- Mesa producción: V3.2-chat + V3.1 + R1
- Sintetizador: Cogito-671b
- Pizarra (Tier 4): 7 modelos → Cogito sintetiza → panel evaluador externo valida
- Descartados: Opus, Sonnet, Kimi K2, GLM-4.7

**Ranking de Aporte Mesa Redonda:**

| # | Modelo | Valor | R1 medio | R2 medio | Δ | 3+ R1 | 3+ R2 | Aportes | Absorcion | Angulos | Inflacion |
|---|--------|-------|----------|----------|---|-------|-------|---------|-----------|---------|-----------|
| 1 | gpt-oss-120b | 118 | 1.26 | 2.74 | +1.49 | 14 | 66 | 0 | 82 | 18 | 0 |
| 2 | qwen3-235b | 98 | 2.54 | 3.19 | +0.65 | 58 | 87 | 31 | 25 | 7 | 17 |
| 3 | opus | 90 | 1.50 | 2.77 | +1.27 | 19 | 67 | 0 | 66 | 12 | 0 |
| 4 | v3.2-chat | 79 | 1.54 | 2.86 | +1.31 | 7 | 76 | 0 | 55 | 12 | 0 |
| 5 | deepseek-v3.1 | 55 | 1.66 | 2.80 | +1.14 | 10 | 74 | 0 | 33 | 11 | 0 |
| 6 | glm-4.7 | 45 | 1.81 | 2.42 | +0.61 | 15 | 54 | 0 | 29 | 8 | 0 |
| 7 | cogito-671b | 42 | 1.52 | 2.88 | +1.35 | 6 | 77 | 6 | 16 | 10 | 6 |
| 8 | kimi-k2.5 | 30 | 2.06 | 2.47 | +0.41 | 28 | 48 | 0 | 18 | 6 | 0 |
| 9 | deepseek-r1 | 0 | 1.57 | 1.57 | +0.00 | 12 | 12 | 0 | 0 | 0 | 0 |
| 10 | minimax-m2.5 | 0 | 1.60 | 1.79 | +0.19 | 14 | 17 | 0 | 0 | 0 | 0 |
| 11 | sonnet | 0 | 2.00 | 2.00 | +0.00 | 32 | 32 | 0 | 0 | 0 | 0 |
| 12 | v3.2-reasoner | 0 | 1.42 | 1.42 | +0.00 | 9 | 9 | 0 | 0 | 0 | 0 |

### EXP 5 — Cadena de Montaje (8 configs × 5 tasks = 40 runs)

| Config | Nombre | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|--------|------|------|------|------|------|--------|-------|
| A | Linea Industrial | 0/1 | 17/18 | 21/21 | 0/2 | 5/6 | 56% | $0.327 |
| D | Ultra-Barato | 0/1 | 4/5 | 9/10 | 0/2 | 6/7 | 51% | $0.047 |
| B | Coder Puro | 0/1 | 14/15 | 10/11 | 0/2 | 0/0 | 37% | $0.136 |
| G | Razonadores | 0/1 | 0/0 | 9/10 | 0/2 | 3/4 | 33% | $0.191 |
| 0 | Baseline | 0/1 | 0/1 | 5/6 | 0/2 | 3/4 | 32% | $0.033 |

**Hallazgos:**
1. Pipeline lineal: techo 56%. NO reemplaza a Code
2. T4 (Orquestador async): 0% en 8/8 configs — techo ESTRUCTURAL
3. Config D Pareto: 51% a $0.05 — 7x más barato que A para -5%
4. Premium PEOR: 15% a $0.34 — pagar más NO ayuda
5. Debugger poco eficaz: 5/35 mejoras. Reviewer ROMPE código funcional (3 casos)

### EXP 5b — Modelos Nuevos en Pipeline

| Config | Modelos | T1 | T4 |
|--------|---------|:---:|:---:|
| N2_cheap | mimo-v2 + nemotron + step-3.5 | 7/7 (100%) | 0/4 (0%) |
| N3_coding | step-3.5 + devstral | 10/10 (100%) | 0/0 (E1 vacío) |

**Hallazgos:**
1. T1 RESUELTO: 0%→100% con modelos nuevos
2. T4 SIGUE 0%: think-tag blowup + async mocking imposible
3. Regla skip-E5/E6 VALIDADA: reviewer/optimizer rompen código funcional

### EXP 1 BIS — 6 Modelos Nuevos (6 × 5 tareas = 30 runs)

| Modelo | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| step-3.5-flash | 1.00 | 0.89 | 1.00 | 1.00 | 1.00 | 0.98 | $0.019 |
| nemotron-super | 1.00 | 0.88 | 1.00 | 0.90 | 1.00 | 0.96 | $0.007 |
| mimo-v2-flash | 1.00 | 0.89 | 0.60 | 1.00 | 1.00 | 0.90 | $0.001 |
| devstral | 1.00 | 0.50 | 0.80 | 1.00 | 1.00 | 0.86 | $0.004 |
| kimi-k2.5 | 0.81 | 0.89 | 0.80 | 0.80 | 1.00 | 0.86 | $0.038 |
| qwen-3.5-397b | 0.59 | 0.88 | 0.80 | 1.00 | 1.00 | 0.85 | $0.033 |

**Hallazgos:**
1. Step 3.5 Flash #1 overall (0.98), MiMo ratio absurdo (0.90 a $0.001)
2. T5 Síntesis: 6/6 modelos 1.00 — TODOS sintetizan bien
3. Devstral: coding specialist (T4=1.00)
4. Todos los roles cubiertos: evaluador, debugger, pizarra, patcher, math, tier barato

### EXP 6 — Agente de Coding OS (loop agéntico, 460 líneas)

| Approach | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exp 5 Config A | 0% | 94% | 100% | 0% | 83% | 56% | $0.33 |
| **Agente multi-modelo** | **100%** | **100%** | **100%** | **93%** | **100%** | **99%** | $1.57 |
| Agente Devstral solo | 83% | — | — | **100%** | — | — | $0.66 |
| Agente MiMo solo | 79% | — | — | 96% | — | — | $0.92 |

**Hallazgos:**
1. T4 RESUELTO: 0% en 11 configs pipeline → 93% con agente (13/14 tests)
2. Devstral solo = 100% en T4 a $0.66
3. Step 0% en T4 como agente — piensa sin actuar
4. MiMo+loop (88%) SUPERA pipeline caro sin loop (56%)
5. 460 líneas bastan. Loop > cantidad de modelos
6. Si tests pasan 100% → finish() inmediato (reviewers rompen código)

### EXP 7 — Rediseño Chief OS (5 modelos, 3 rondas)

**Diseño Consensuado:** 8 componentes
1. Dispatcher Inteligente 2. Evaluador de Respuesta 3. Planificador Razonamiento
4. Matriz Cognitiva Adapter ($0) 5. Agente de Coding 6. Monitor Rendimiento
7. Optimizador Configuración 8. Logger & Telemetría ($0)

**Coste:** $0.0013/turno (15x bajo target)

**Problema:** 4/10 checks vs Maestro fallan (estigmergia, 8 ops, pipeline 7 pasos, enjambre código)

### EXP 8 — Auditoría Completa (5 modelos, 3 rondas)

**Consenso 5/5:**
1. Chief deprecado vs operativo — contradicción crítica (D1)
2. No hay corrección de errores (C5)
3. Modelo negocio no validado (C3)
4. Supabase vs fly.io insostenible (D2)
5. Sobrediseño: 17 tipos pensamiento + 6 modos (B3/B4)
6. UI/UX no especificada (C2)
7. Cross-dominio no demostrado (C4)
8. Componentes teóricos sin validación (B1)
9. MVP sobrediseñado (E6)
10. Dependencia Sonnet en 12 agentes (D3)

**Decisiones CR0:** Eliminar Chief, migrar fly.io, eliminar Sonnet del MVP,
podar componentes teóricos, MVP con 6 INTs irreducibles, presupuesto realista

---

## ANEXO II: MAPA DEFINITIVO DE MODELOS OS

| Modelo | Score | Coste | Rol óptimo |
|--------|:---:|:---:|------------|
| Step 3.5 Flash | 0.98 | $0.019 | Debugger, Evaluador, Razonador |
| Nemotron Super | 0.96 | $0.007 | Validador numérico, Evaluador |
| MiMo V2 Flash | 0.90 | $0.001 | Workhorse, Arquitecto, Fallback |
| Devstral | 0.86 | $0.004 | Agente coding, Implementador |
| Kimi K2.5 | 0.86 | $0.038 | Pizarra, Auditor contexto largo |
| Qwen 3.5 397B | 0.85 | $0.033 | Evaluador, Implementador |
| Cogito 671B | #1 sint. | $0.125 | Sintetizador mesa redonda |
| DeepSeek V3.2 | — | $1.10/M | Diseño, Orquestación |

**Reglas empíricas:**
1. Loop > modelos: MiMo+loop (88%) supera pipeline caro sin loop (56%)
2. Barato+bueno > caro+solo: MiMo $0.001 con 0.90
3. Diversidad > calidad individual
4. Reviewers rompen código: si tests 100% → PARAR
5. Think-tag blowup: Step/Qwen gastan 16K pensando sin output
6. Devstral = agente coding ideal: rápido (4-10s), barato ($0.004), T4=100%

---

## ANEXO III: SÍNTESIS DE AUDITORÍA EXP 8

### Diagnóstico Consolidado

**A. COHERENCIA INTERNA**
- A1 (L0 consistentes): 🟢 Sólido
- A2 (Maestro vs L0): 🟢 Sólido
- A3 (18 INT irreducibles): 🟡 Disenso crítico — operar con 6 base + 12 opcionales
- A4 (Matriz 3L×7F): 🟢 Sólida
- A5 (Resultados vs diseño): 🟡 Exp 5b muestra 0% T4 con modelos OS

**B. SOBREDISEÑO**
- B1 (Componentes teóricos): 🔴 Roto (Reactor v3, Meta-motor, Fábrica sin validación)
- B2 (Eliminables): 🟢 Limpio (Chief, 9 modos, 24 agentes)
- B3 (17 tipos pensamiento): 🔴 Roto (overhead, solo 6-7 usados)
- B4 (6 modos): 🔴 Roto (redundantes con gradientes)
- B5 (Reactor v3): 🟡 12% utilidad vs Reactor v4

**C. HUECOS CRÍTICOS**
- C1 (Fallback): 🔴 Bloqueante (Gestor es SPOF)
- C2 (UI/UX): 🔴 Bloqueante (imposibilidad cognitiva no resuelta)
- C3 (Modelo negocio): 🔴 Bloqueante (sin validación WTP)
- C4 (Cross-dominio): 🔴 Bloqueante (sin base empírica)
- C5 (Corrección errores): 🔴 Bloqueante (detección sin corrección)

**D. CONTRADICCIONES**
- D1 (Chief deprecado vs operativo): 🔴 Crítica
- D2 (fly.io vs Supabase): 🔴 Crítica
- D3 (Sonnet dependencia): 🔴 Crítica (~12 agentes)
- D4 (Presupuestos): 🟡 Tensión (€640-920 vs €2000-3000/mes reales)
- D5 (Versiones): 🟡 Mejorable

**E. VISIÓN PRODUCTO**
- E1 (Motor compilador): 🟢 Realista
- E2 (Camino pilotos): 🟢 Lógico
- E3 (Margen >90%): 🟢 Aritméticamente válido
- E4 (Flywheel): 🟡 Teórico
- E5 (Competidores): 🔴 Ausencia crítica
- E6 (MVP): 🟡 Sobrediseñado

**F. HOJA DE RUTA**
- F1 (Prioridad): 🟢 Correcta (Gestor primero)
- F2 (Dependencia): 🔴 Bloqueante (Gestor es SPOF)
- F3 (Tiempo/coste): 🟡 Optimista (4-6 meses realistas)
- F4 (Planificación): 🟡 Mejorable (falta desglose semanal)
- F5 (Apuesta): 🔴 Todo o nada (Reactor v4 debe funcionar)

### Top 5 Hallazgos por Impacto

1. **Arquitectura fragmentada**: Discrepancia crítica entre Documento Maestro (nuevo diseño) e implementación actual (Supabase + 24 agentes Chief operativos)
2. **Modelo de negocio no validado**: Los cálculos reales contradicen los presupuestos iniciales; falta análisis de competencia
3. **Falta mecanismo de corrección**: Errores detectados no generan acciones correctivas automáticas; 44% fallos en T4 sin recuperación
4. **Complejidad excesiva**: El sistema tiene muchos componentes que podrían simplificarse (17 tipos → 7, 18 INT → 6 para MVP)
5. **Transferencia cross-dominio no demostrada**: El flywheel es teórico y necesita validación empírica con pilotos reales

### Decisiones CR0 Pendientes

**CR0-1: Arquitectura Chief** → Opción A (Eliminar completamente en 2 semanas)  
**CR0-2: Infraestructura** → Opción A (Migración total a fly.io)  
**CR0-3: Dependencia Sonnet** → Opción C (Eliminar funcionalidad de 12 agentes del MVP)  
**CR0-4: Componentes Teóricos** → Opción A (Eliminar Reactor v3 y 17 tipos de pensamiento)  
**CR0-5: Alcance MVP** → Opción B (Solo 6 INT irreducibles: INT-01, 02, 06, 08, 14, 16)  
**CR0-6: Presupuesto** → Opción A (Ajustar a €3000/mes para 3 meses = €9000 total) o C (Buscar financiación)

---

**FIN DEL BRIEFING**