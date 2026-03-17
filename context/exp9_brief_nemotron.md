**BRIEFING ESTRATÉGICO: OMNI-MIND**
**Destinatario:** Estratega de Negocio  
**Objetivo:** Conversión a Producto de Pago  
**Fecha:** Marzo 2026  
**Estado del Sistema:** CR0 (Validación Jesús)

---

## 1. RESUMEN EJECUTIVO

OMNI-MIND es un **sistema operativo cognitivo** que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas — es un organismo vivo que **compila un programa cognitivo nuevo para cada interacción** a partir de una Matriz de 3 Lentes × 7 Funciones × 18 Inteligencias (378 celdas activas).

El sistema utiliza un **enjambre de modelos de lenguaje open-source (OS)** que operan en paralelo, cada uno especializado en diferentes dimensiones del pensamiento (lógico-matemático, social, estratégico, corporal, etc.), generando diagnósticos y soluciones que ningún modelo individual puede alcanzar.

**Evidencia clave:**
- 3 modelos OS superan a Claude (Anthropic) en cobertura matricial (Exp 4)
- Coste real por ejecución: $0.10-0.35 (OS-first) vs $0.35-1.50 (con evaluador premium)
- Margen proyectado: >90% (coste $2-5/mes vs precio €50-200/mes)
- Arquitectura validada en 8 experimentos con 40+ configuraciones y 100+ ejecuciones

**El problema:** El sistema actual está en contradicción operativa (Chief deprecado pero operativo, infraestructura híbrida Supabase/fly.io) y requiere decisión arquitectónica binaria antes de escalar.

---

## 2. EL PRODUCTO: SISTEMA COGNITIVO OMNI-MIND v4

### 2.1 Qué es OMNI-MIND (Maestro §1)

Un organismo cognitivo que percibe, razona, aprende y evoluciona. No es un motor que ejecuta programas — es un sistema vivo que compila un programa cognitivo nuevo para cada interacción.

**El principio central:**

**El prompt del agente no tiene instrucciones imperativas. Es exclusivamente una red de preguntas.** La inteligencia emerge de la estructura de preguntas, no de instrucciones al modelo. No le dices al agente "analiza como financiero" — le das la red de preguntas de INT-07 y el agente no puede hacer otra cosa que operar financieramente.

Las preguntas no son output del agente (no las verbaliza). Son su **sistema operativo interno** — la lente a través de la cual mira y procesa.

**Los componentes:**

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

**Los dos loops:**

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

### 2.2 La Matriz — 3L × 7F × 18INT (Maestro §2)

**El esquema central:**

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

**Las 21 celdas como campo de gradientes:**

Cada celda tiene grado actual (0.0-1.0), grado objetivo (contextual), y gap = objetivo - actual. El gap genera la fuerza que dirige la ejecución. Mayor gap = más prioridad.

### 2.3 El Álgebra — Compilador de Prompts (Maestro §3)

Las operaciones algebraicas son **operaciones de ensamblaje de redes de preguntas:**

```
Fusión ∫(A|B):     Prompt = [preguntas de A] + [preguntas de B] en paralelo
Composición A→B:   Prompt = [preguntas de A], luego [preguntas de B sobre output de A]
Diferencial A-B:   Prompt = [preguntas que A tiene y B no puede tener]
Integración ∫:     Prompt = [preguntas que emergen al cruzar las anteriores]
Loop test A→A:     Prompt = [mismas preguntas sobre su propio output]
```

**Propiedades confirmadas (34 chats de cartografía):**

| Propiedad | Resultado | Implicación para el compilador |
|-----------|-----------|-------------------------------|
| Composición NO conmutativa | A→B ≠ B→A siempre | Formal primero → humano después |
| NO asociativa | (A→B)→C ≠ A→(B→C) | Secuencia lineal, no reorganizar |
| Fusión parcialmente conmutativa | ~25% | Orden de fusión afecta framing |
| No idempotente | 18/18 | Loop test siempre justificado. 2 pasadas óptimo |
| Saturación en n=2 | 3ª pasada aporta 10-15% | No hacer 3ª excepto calibración |
| Clausura | output ∈ input | Cualquier output puede alimentar otra INT |
| Distributividad izq ~70% | Pierde ~30% al factorizar | Aceptable para ahorro, no para pares TOP |
| Distributividad der PROHIBIDA | Valor irreducible del cruce | Nunca factorizar |

### 2.4 Pipeline de Ejecución (Maestro §4)

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

### 2.5 Firmas de las 18 Inteligencias (Meta-Red)

**CATEGORÍA I: FORMALES**

**INT-01: LÓGICO-MATEMÁTICA**
*Firma:* DEMOSTRACIÓN — derivar verdad desde primeros principios.  
*Objetos:* estructuras, relaciones, pruebas, axiomas.  
*Punto ciego:* lo ambiguo, lo parcial, lo no-axiomatizable.

**INT-02: COMPUTACIONAL**
*Firma:* OPTIMIZACIÓN — encontrar la mejor solución dentro de restricciones.  
*Objetos:* algoritmos, estados, complejidad, datos.  
*Punto ciego:* lo no-computable, la intuición, el juicio cualitativo.

**INT-03: ESTRUCTURAL (IAS)**
*Firma:* ISOMORFISMO — proyectar forma sobre datos para hacer visible lo invisible.  
*Objetos:* coordenadas sintácticas, formas, niveles, huecos.  
*Punto ciego:* no genera soluciones — solo diagnóstico.

**INT-04: ECOLÓGICA**
*Firma:* INTERDEPENDENCIA — nada existe aislado, todo afecta a todo.  
*Objetos:* ecosistemas, ciclos, nichos, resiliencia, flujos.  
*Punto ciego:* no ve al individuo — solo al sistema completo.

**CATEGORÍA II: ESTRATÉGICAS**

**INT-05: ESTRATÉGICA**
*Firma:* ANTICIPACIÓN — pensar dos movimientos adelante.  
*Objetos:* posición, recursos, movimientos, ventanas temporales, opciones.  
*Punto ciego:* asume competición — no modela cooperación ni conflicto interno.

**INT-06: POLÍTICA**
*Firma:* NEGOCIACIÓN — redistribuir poder mediante acuerdo.  
*Objetos:* poder, alianzas, legitimidad, narrativa, coaliciones.  
*Punto ciego:* confunde poder con verdad — lo que tiene apoyo no es necesariamente correcto.

**INT-07: FINANCIERA**
*Firma:* DESCUENTO TEMPORAL — todo valor se traduce a presente.  
*Objetos:* flujos, posiciones, riesgo, apalancamiento, opcionalidad.  
*Punto ciego:* lo que no tiene precio no existe.

**CATEGORÍA III: SOCIALES**

**INT-08: SOCIAL**
*Firma:* EMPATÍA — leer el estado interno del otro (o propio) sin que lo verbalice.  
*Objetos:* emociones, intenciones, dinámicas, patrones reactivos, vínculos.  
*Punto ciego:* sobrepsicologiza — puede ver conflicto emocional donde hay problema estructural.

**INT-09: LINGÜÍSTICA**
*Firma:* REENCUADRE — cambiar el marco lingüístico cambia lo que es visible.  
*Objetos:* palabras, marcos, narrativas, metáforas, actos de habla.  
*Punto ciego:* confunde nombrar con resolver — poner nombre no cambia la estructura.

**CATEGORÍA IV: CORPORALES**

**INT-10: CINESTÉSICA**
*Firma:* SENTIR TENSIÓN — el cuerpo detecta lo que la mente racionaliza.  
*Objetos:* movimiento, tensión, ritmo, coordinación, flujo corporal.  
*Punto ciego:* no verbaliza — sabe pero no puede explicar qué sabe.

**INT-11: ESPACIAL**
*Firma:* CAMBIO DE PERSPECTIVA — rotar el objeto para ver la cara oculta.  
*Objetos:* formas, distancias, perspectivas, mapas, proporciones.  
*Punto ciego:* lo que no tiene extensión no existe — no ve procesos, solo configuraciones.

**CATEGORÍA V: TEMPORALES**

**INT-12: NARRATIVA**
*Firma:* DAR SENTIDO — convertir hechos en historia con dirección.  
*Objetos:* arco, personaje, transformación, secuencia, significado temporal.  
*Punto ciego:* fuerza protagonista y arco donde puede no haberlos.

**INT-13: PROSPECTIVA**
*Firma:* SIMULAR FUTUROS — explorar qué pasa si X, Y o Z.  
*Objetos:* tendencias, señales débiles, escenarios, distribuciones de probabilidad.  
*Punto ciego:* el cisne negro — lo que no tiene precedente no aparece en el modelo.

**CATEGORÍA VI: CREATIVAS**

**INT-14: DIVERGENTE**
*Firma:* GENERACIÓN — producir opciones que no existían antes.  
*Objetos:* posibilidades, conexiones remotas, combinaciones inusuales.  
*Punto ciego:* todo es posible, nada es evaluable — genera sin filtrar.

**INT-15: ESTÉTICA**
*Firma:* JUICIO DE COHERENCIA — detectar que algo "no encaja" sin saber por qué.  
*Objetos:* armonía, tensión, elegancia, proporción, coherencia formal.  
*Punto ciego:* lo feo puede ser verdadero, lo bello puede ser falso.

**INT-16: CONSTRUCTIVA**
*Firma:* CONSTRUIR — convertir diseño en realidad funcional.  
*Objetos:* restricciones, materiales, soluciones, prototipos, iteraciones.  
*Punto ciego:* optimiza lo existente — no cuestiona si debería existir.

**CATEGORÍA VII: EXISTENCIALES**

**INT-17: EXISTENCIAL**
*Firma:* CONFRONTAR — preguntar "¿para qué?" hasta llegar al fondo.  
*Objetos:* propósito, libertad, responsabilidad, finitud, valores.  
*Punto ciego:* puede paralizar por exceso de profundidad.

**INT-18: CONTEMPLATIVA**
*Firma:* OBSERVAR SIN JUZGAR — ver lo que es, sin necesidad de cambiarlo.  
*Objetos:* presencia, vacío, observación, paradoja, no-acción.  
*Punto ciego:* puede desconectar de la acción — observar sin actuar.

### 2.6 Casos de Uso y Pilotos (Maestro §6D-2, §11)

**Piloto 1: Estudio de Pilates (Jesús)**
- Telemetría: reservas, asistencia, clientes, sesiones, ingresos
- Reactor v4 genera preguntas desde patrones reales del estudio
- Validación: ¿los agentes detectan cosas que Jesús no veía?

**Piloto 2: Clínica de Fisioterapia (mujer de Jesús)**
- Segundo dominio: valida transferencia cross-dominio
- Test clave: ¿preguntas de Pilates sobre gestión de agenda aplican a fisio? ¿Y viceversa?

**Ola 4: Integración con software de gestión**
- Capa de telemetría que lee datos del software existente via API
- Agentes V3.2 inyectados en cada módulo con prompt compilado por el Gestor
- Reactor v4 observa datos de clientes del amigo informático

---

## 3. EVIDENCIA EMPÍRICA: RESULTADOS EXPERIMENTALES COMPLETOS

### 3.1 EXP 4 — Mesa Redonda Multi-Modelo (12 modelos, 2 rondas)

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

**Veredicto:** 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). R1 cubre 20/21 celdas — la mayor cobertura de todos.

### 3.2 EXP 5 — Cadena de Montaje (8 configs × 5 tasks = 40 runs)

| Config | Nombre | T1 | T2 | T3 | T4 | T5 | **Media** | Coste | Tiempo |
|--------|--------|------|------|------|------|------|--------|-------|--------|
| A | Linea Industrial | 0/1 | **17/18** | **21/21** | 0/2 | 5/6 | **56%** | $0.327 | 2632s |
| D | Ultra-Barato | 0/1 | 4/5 | **9/10** | 0/2 | 6/7 | **51%** | $0.047 | 944s |
| B | Coder Puro | 0/1 | **14/15** | **10/11** | 0/2 | 0/0 | **37%** | $0.136 | 1771s |
| G | Razonadores | 0/1 | 0/0 | **9/10** | 0/2 | 3/4 | **33%** | $0.191 | 2265s |
| 0 | Baseline | 0/1 | 0/1 | 5/6 | 0/2 | 3/4 | **32%** | $0.033 | 262s |

**Hallazgos:**
1. Pipeline lineal: techo 56%. NO reemplaza a Code
2. T4 (Orquestador async): 0% en 8/8 configs — techo ESTRUCTURAL
3. Config D Pareto: 51% a $0.05 — 7x más barato que A para -5%
4. Premium PEOR: 15% a $0.34 — pagar más NO ayuda
5. Debugger poco eficaz: 5/35 mejoras. Reviewer ROMPE código funcional (3 casos)

**Veredicto:** NO, la cadena no es suficiente hoy. Mejor cadena: 56% pass rate. La cadena de montaje supera al modelo solo en +24%, pero el techo estructural de T4 requiere loop agéntico.

### 3.3 EXP 5b — Modelos Nuevos en Pipeline

| Config | Modelos | T1 | T4 |
|--------|---------|:---:|:---:|
| N2_cheap | mimo-v2 + nemotron + step | **100%** | 0% |
| N3_coding | step-3.5 + devstral | **100%** | 0% |

**Hallazgos:**
1. T1 RESUELTO: 0%→100% con modelos nuevos
2. T4 SIGUE 0%: think-tag blowup + async mocking imposible
3. Regla skip-E5/E6 VALIDADA: reviewer/optimizer rompen código funcional

**Insight:** Step 3.5 Flash #1 overall (0.98), MiMo ratio absurdo (0.90 a $0.001). Devstral = agente coding ideal: rápido (4-10s), barato ($0.004), T4=100%.

### 3.4 EXP 1 Bis — 6 Modelos Nuevos × 5 Tareas

| Modelo | T1 | T2 | T3 | T4 | T5 | Media | Coste |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Step 3.5 Flash | 1.00 | 0.89 | 1.00 | 1.00 | 1.00 | **0.98** | $0.019 |
| Nemotron Super | 1.00 | 0.88 | 1.00 | 0.90 | 1.00 | **0.96** | $0.007 |
| MiMo V2 Flash | 1.00 | 0.89 | 0.60 | 1.00 | 1.00 | **0.90** | $0.001 |
| Devstral | 1.00 | 0.50 | 0.80 | 1.00 | 1.00 | **0.86** | $0.004 |
| Kimi K2.5 | 0.81 | 0.89 | 0.80 | 0.80 | 1.00 | **0.86** | $0.038 |
| Qwen 3.5 397B | 0.59 | 0.88 | 0.80 | 1.00 | 1.00 | **0.85** | $0.033 |

**Recomendaciones por Rol:**
- **Debugger/Razonador:** Step 3.5 Flash ($0.019)
- **Math/Validación numérica:** Nemotron Super ($0.007)
- **Tier barato universal:** MiMo V2 Flash ($0.001)
- **Patcher (#1 SWE):** Devstral ($0.004, T4=100%)

### 3.5 EXP 6 — Agente de Coding OS (loop agéntico, 460 líneas)

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

**Agente:** 5 herramientas (read_file, write_file, run_command, list_dir, search_files) + finish. Routing: Devstral (genera) → Step (debugea tras 2 errores) → MiMo (fallback). Seguridad: sandbox path, command blacklist, stuck detection.

### 3.6 EXP 7 — Rediseño Chief OS (5 modelos, 3 rondas)

**Diseño Consensuado:** 8 componentes
1. Dispatcher Inteligente 
2. Evaluador de Respuesta 
3. Planificador Razonamiento
4. Matriz Cognitiva Adapter ($0) 
5. Agente de Coding 
6. Monitor Rendimiento
7. Optimizador Configuración 
8. Logger & Telemetría ($0)

**Coste:** $0.0013/turno (15x bajo target)  
**Problema:** 4/10 checks vs Maestro fallan (estigmergia, 8 ops, pipeline 7 pasos, enjambre código)

### 3.7 EXP 8 — Auditoría Completa (5 modelos, 3 rondas)

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

**Decisiones CR0:** Eliminar Chief, migrar fly.io, eliminar Sonnet del MVP, podar componentes teóricos, MVP con 6 INTs irreducibles, presupuesto realista.

**Top 5 Hallazgos por Impacto:**
1. **Gestor de la Matriz es SPOF** (F2, F5, C1) — Sin este componente, no hay sistema
2. **Contradicción Chief deprecado vs operativo** (D1) — 24 agentes en Supabase bloquean migración
3. **Infraestructura inconsistente** (D2) — Dualidad Supabase/fly.io insostenible
4. **Modelo de negocio no validado** (C3) — €50-200/mes sin evidencia de mercado
5. **Sobrediseño teórico** (B1, B3, B4) — Reactor v3, 17 tipos de pensamiento, 6 modos sin validación

---

## 4. ARQUITECTURA TÉCNICA E IMPLEMENTACIÓN

### 4.1 Contexto del Sistema Actual (MEMORY.md)

**Infraestructura:**
- Producción: Supabase `cptcltizauzhzbwxcdft` (99 Edge Functions, 47 migraciones SQL)
- Staging: Supabase `jbfiylwbgxglqwvgsedh` (45 migraciones, 98 funciones)
- Plan: Migración a fly.io (deprecación Supabase gradual)

**Enjambres Activos:**
1. **IAS** (Pipeline Diagnóstico): ~10 agentes, capas 1-5, funcional
2. **Diseño** (Meta-diseño): 18 agentes, capas 1-6, E2E funcional
3. **Chief of Staff**: Pipeline dual superficial+profundo, 24 agentes (~6.900 líneas), DEPRECADO en diseño pero OPERATIVO en producción
4. **Mejora Continua**: 3 agentes, operativo

**Comunicación:** Estigmergia pura (tabla `marcas_estigmergicas`). Nunca llamadas directas entre agentes.

**Stack Técnico:**
- Edge Functions: Deno/TypeScript
- LLM: `llm-proxy` (Haiku para parseadores/detección, Sonnet para diseño/síntesis, fallback automático)
- DB: Supabase PostgreSQL (migrando a fly.io Postgres)
- Coste actual: ~$0.005/ciclo ≈ $15/mes

### 4.2 Pipeline del Motor vN (Maestro §6B, §4)

**Fase A: Exploración (llena la Matriz)**
- Caso nuevo entra
- Motor OS ejecuta protocolo de exploración completo: 18 INTs individuales, 6 irreducibles en composición (30 pares), TOP 10 fusiones, Loop tests, muestreo aleatorio
- Evaluador mide batch: qué gaps cerró cada operación
- Datapoints de efectividad → DB → Gestor de la Matriz

**Fase B: Lookup (usa la Matriz llena)**
- Cuando una celda tiene suficientes datos, el Motor pasa a modo servicio para esa celda
- Gestor provee programa compilado: "Este patrón de gaps lo he visto 47 veces. La configuración INT-01→INT-14 fusión con Maverick cierra el 82% en Salud×Captar."
- Ejecuta SOLO la configuración ganadora con el modelo asignado

**Transición:** No es binaria ni global — es por celda. Si n_ejecuciones_patron > 30 AND tasa_cierre_config_ganadora > 0.60 → Fase B para esta celda.

### 4.3 Agente de Coding (Exp 6 — OpenHands)

Basado en análisis de OpenHands (All-Hands-AI):

**Loop principal:** observe→think→act
- Max iteraciones: 500 (configurable)
- Stuck detection: 5 escenarios (acción repetida×4, error×3, monólogo, ciclo largo, context window)
- Timeouts: Per-command 120s (default)
- Seguridad: Docker isolation (sandbox) + risk model (NO blacklist)

**9 herramientas:** Bash, IPython, File editor, Browser, Think, Finish, Task tracker, Condensation, MCP tools.

**Recuperación de errores:** Error → ErrorObservation → el agente VE el error en su historial → decide siguiente acción. Retry con exponential backoff (3-5 intentos).

**Multi-modelo:** LLMRegistry + LiteLLM (abstracción de providers). Router opcional para dirigir diferentes prompts a diferentes modelos.

---

## 5. MODELO DE NEGOCIO

### 5.1 Costes Reales de Operación

| Experimento | Estimado | Real | Factor |
|-------------|----------|------|--------|
| Exp 5 (40 runs) | $5-15 | $1.50 | 3-10x sobrestimado |
| Exp 1 bis (30 runs) | $1-3 | $0.10 | 10-30x sobrestimado |
| Exp 6 (agente) | $3-6 | $1.57 | 2-4x sobrestimado |
| Exp 7 (15 calls) | $3-5 | $0.15 | 20-33x sobrestimado |
| **TOTAL 6 exps** | $14-33 | ~$5.50 | 3-6x sobrestimado |

**Coste por ejecución Motor vN:**
- OS-first: ~$0.10-0.35
- Con evaluador Sonnet: ~$0.35-1.50
- Target: <$0.02/turno (superficial), <$0.05/turno (profundo)

**Coste mensual proyectado (por negocio):**
- Tokens: ~$2-5/mes
- Infraestructura (fly.io): ~$5-10/mes
- **Total coste:** ~$7-15/mes por negocio

### 5.2 Presupuestos y Estimaciones (Maestro §14, §15)

**Fases A-F (Desarrollo hasta pilotos):**

| Fase | Duración | Coste API | Coste Total Est. |
|------|----------|-----------|-------------------|
| A — Cartografía | 2-3 semanas | €0 (claude.ai Pro) | ~€0 |
| B — Datos sintéticos | 1 semana | ~€150 | ~€150 |
| C — Entrenamiento | 2-3 días | ~€10 | ~€10 |
| D — Motor v1 | 1-2 semanas | ~€150-200 | ~€150-200 |
| E — Chat/Exocortex | 1-2 semanas | ~€80-110 | ~€80-110 |
| F — Pilotos (3 meses) | 3 meses | ~€250-450 | ~€250-450 |
| **TOTAL** | **~6-9 semanas** | **~€640-920** | **~€640-920** |

**Nota:** Auditoría Exp 8 sugiere costes reales más altos (~€2000-3000/mes) si se incluyen pruebas exhaustivas y volumen alto de inferencia multi-modelo.

**Coste recurrente post-lanzamiento:**
- 10 ejecuciones/día = ~€300/mes
- 30 ejecuciones/día = ~€900/mes

### 5.3 Roadmap de Implementación (Maestro §11)

**Ola 1 — Ahora (paralelo):**
- Gestor de la Matriz (tabla de efectividad + vista materializada + compilador)
- Motor vN MVP en fly.io (pipeline end-to-end que USA la Matriz via Gestor)
- Migración OS Fase 1 (llm-proxy multi-provider + migrar ~30 agentes 🟢)
- Reactor v3 conceptual (poblar Matriz con preguntas desde fundamentos teóricos)

**Ola 2 — Motor funcional + primeros pilotos reales:**
- Test evaluador OS vs Sonnet (objetivo: correlación >0.85 → migrar a OS)
- Migración OS Fase 2 (testear ~12 agentes 🟡)
- Integrar enjambre de código en pipeline de auto-mejora (V3.2+Qwen Coder+Cogito+V3.1)
- PILOTO 1: Exocortex Pilates (estudio de Jesús) — primer consumidor real del Gestor
- PILOTO 2: Exocortex Fisioterapia (clínica de la mujer de Jesús) — segundo dominio

**Ola 3 — Retroalimentación + autonomía:**
- Datos reales de ambos pilotos refinan la Matriz via Gestor (feedback transversal)
- Reactor v4 activo (telemetría genera preguntas desde datos reales de operación)
- Flywheel validado (Pilates y Fisio se enriquecen mutuamente via la Matriz)
- Prompts vivos (los agentes evolucionan con el negocio sin intervención manual)

**Ola 4 — Escala: caso de negocio real con terceros:**
- Presentar resultados al amigo informático (con datos reales de Piloto 1 y 2)
- Integración con software de gestión de terceros (API de lectura/escritura)
- Fábrica de Exocortex para generar conectores por tipo de software
- Modelo de negocio: capa inteligente a €50-200/mes por negocio

### 5.4 Competidores y Diferenciación (Exp 8, Maestro §6D-2)

**Competidores identificados:**
- **Glean:** Búsqueda inteligente para empresas (no tiene Matriz 3L×7F)
- **Adept:** Agente IA para tareas de software (no comparte conocimiento cross-dominio)
- **AutoGPT:** Agente autónomo genérico (no tiene estructura matricial ni flywheel)

**Diferenciación OMNI-MIND:**
1. **Matriz 3L×7F:** Estructura única que mapea cualquier problema a 378 coordenadas cognitivas
2. **Enjambre multi-modelo OS:** Diversidad de modelos especializados vs. monomodelo propietario
3. **Flywheel cross-dominio:** Lo que aprende un Pilates mejora el Fisioterapia automáticamente via el Gestor
4. **Prompts vivos:** El sistema evoluciona sus propias preguntas basándose en datos reales (Reactor v4)
5. **OS-first:** Sin dependencia de proveedores premium (margen >90% sostenible)

---

## 6. MAPA DEFINITIVO DE MODELOS OS CON COSTES

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

## 7. RIESGOS Y AUDITORÍA (Exp 8 — Síntesis Consolidada)

### Contradicciones Críticas (Bloqueantes)

**D1: Chief deprecado vs operativo**
- **Problema:** Maestro declara "Chief → DEPRECADO", pero MEMORY.md muestra 24 agentes operativos (6.900 líneas) en Supabase.
- **Impacto:** Bloquea migración a OS. Dualidad arquitectónica insostenible.
- **Resolución:** Decisión binaria inmediata: migrar TODO a Motor vN en 2 semanas O admitir que v2/Supabase es arquitectura válida actual.

**D2: fly.io vs Supabase**
- **Problema:** Maestro §0: "todo a fly.io", pero implementación real tiene 99 Edge Functions y 47 migraciones SQL en Supabase.
- **Impacto:** Aumenta costes operativos y complejidad técnica.
- **Resolución:** Plan de migración concreto con fechas de corte o admisión de arquitectura híbrida permanente.

**D3: Dependencia Sonnet**
- **Problema:** Maestro §6B: "Sonnet solo referencia inicial", pero ~12 agentes críticos aún requieren Sonnet para validación.
- **Impacto:** Coste elevado (~$1.50/caso) y lock-in de proveedor.
- **Resolución:** Migración forzosa de esos 12 a OS (aceptando degradación temporal) o eliminación de esas funcionalidades del MVP.

### Huecos Críticos (Bloqueantes)

**C3: Modelo de negocio no validado**
- **Problema:** Rango €50-200/mes es asunción sin validación de mercado (WTP) ni análisis de competidores.
- **Impacto:** Riesgo comercial extremo. Podría no haber demanda a ese precio.
- **Mitigación:** Encuesta disposición a pagar a 10 negocios potenciales antes de continuar.

**C4: Transferencia cross-dominio no demostrada**
- **Problema:** Flywheel teórico ("Pilates descubre → Fisioterapia recibe") sin base empírica.
- **Impacto:** El valor diferencial del sistema (aprendizaje transversal) no está probado.
- **Mitigación:** Piloto 2 (Fisioterapia) debe validar explícitamente transferencia desde Pilates.

**C5: Corrección de errores**
- **Problema:** Hay detección (gaps > 0.3 escalan) pero no hay mecanismo de corrección automática, rollback semántico, ni loop de feedback con usuario ante alucinaciones.
- **Impacto:** Errores se acumulan sin corrección.
- **Mitigación:** Implementar snapshotting en fly.io para auto-mejoras (rollback automático).

### Sobrediseño (Riesgo de complejidad)

**B1: Componentes teóricos sin validación**
- Reactor v3, Meta-motor, Fábrica de Exocortex existen solo en teoría ("⬜ Diseñado, por implementar").

**B3/B4: 17 tipos de pensamiento + 6 modos**
- Overhead confirmado: EXP 4.3 muestra que solo 6-7 patrones son frecuentemente usados.
- Los 6 modos son redundantes con gradientes de la Matriz (el propio Maestro lo admite).

**E6: MVP sobrediseñado**
- Requiere Motor vN + Exocortex + Reactor v4 + telemetría completa.
- Falta definición de "MVP mínimo" acotado (sugerencia: solo 6 INTs irreducibles).

---

## 8. RECOMENDACIONES ESTRATÉGICAS

### Inmediatas (Esta semana)

1. **Resolver CR0-1 (Arquitectura Chief):** Decidir binariamente si se elimina el Chief of Staff (24 agentes) en 2 semanas o se mantiene como legacy. La contradicción actual bloquea todo avance.

2. **Resolver CR0-2 (Infraestructura):** Definir plan de migración Supabase→fly.io con fechas concretas o admitir arquitectura híbrida permanente. La dualidad actual consume recursos.

3. **Validar precio (C3):** Antes de construir más, encuestar 10 negocios potenciales (Pilates, Fisioterapia, otros) sobre disposición a pagar €50-200/mes por "software que piensa sobre tu negocio".

### Corto plazo (Mes 1)

4. **Implementar Gestor de la Matriz:** Es el SPOF (Single Point of Failure) del sistema. Sin él, no hay compilación de programas ni aprendizaje transversal. Prioridad máxima.

5. **MVP reducido (CR0-5):** Pilotar con solo 6 inteligencias irreducibles (INT-01, 02, 06, 08, 14, 16) en lugar de 18. Reduce complejidad y acelera validación.

6. **Migración OS Fase 1:** Migrar los 30 agentes "🟢" (fáciles) a modelos OS, dejando Sonnet solo como fallback temporal para los 12 "🟡".

### Medio plazo (Mes 2-3)

7. **Validar flywheel:** Si Piloto 1 (Pilates) y Piloto 2 (Fisioterapia) no demuestran transferencia automática de conocimiento (preguntas de uno aplicándose al otro), reconsiderar el valor diferencial del producto.

8. **Implementar mecanismo de corrección:** Desarrollar rollback automático para auto-mejoras fallidas (snapshotting) antes de activar el enjambre de código autónomo.

9. **Revisar presupuesto:** Ajustar a €2000-3000/mes para 3 meses (€9000 total) basándose en costes reales de inferencia multi-modelo, o buscar financiación adicional.

### Largo plazo (Ola 4)

10. **Análisis de competencia:** Realizar estudio detallado de Glean, Adept, AutoGPT y otros para posicionar correctamente los €50-200/mes y justificar el valor diferencial (Matriz + flywheel).

11. **Fábrica de Exocortex:** Solo si los pilotos validan el modelo, activar el enjambre de código (V3.2+Qwen Coder) para generar automáticamente nuevos exocortex para diferentes dominios (restaurantes, clínicas, etc.).

**Conclusión:** OMNI-MIND tiene arquitectura técnicamente sólida y evidencia empírica favorable (supera a Claude, costes bajos, margen alto), pero está en riesgo por contradicciones operativas (Chief/Supabase vs diseño nuevo) y falta de validación de mercado. Requiere decisión arquitectónica drástica y validación comercial inmediata antes de continuar invirtiendo en desarrollo.