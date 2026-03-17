### BRIEFING PARA AUDITOR 1 — COHERENCIA SISTÉMICA (Step 3.5 Flash)

**Objetivo:** Verificar consistencia lógica interna del sistema, invariantes L0, propiedades algebraicas confirmadas/refutadas, y coherencia entre niveles de estabilidad.

---

## 1. NIVELES DE ESTABILIDAD (L0/L1/L2) — Documento Maestro §1C

```
INVARIANTE (L0 — no se toca):
  3 Lentes:    Salud / Sentido / Continuidad
  7 Funciones: Conservar / Captar / Depurar / Distribuir / Frontera / Adaptar / Replicar
  8 Operaciones sintácticas (Marco Lingüístico)
  Álgebra del cálculo semántico
  → Esto es gramática. No cambia.
  → Se falsifica solo si se encuentra: 4ª lente irreducible, 8ª función, 9ª operación.

ESTABLE PERO EVOLUCIONABLE (L1 — cambia con evidencia empírica):
  18 inteligencias (hoy) → puede ser 16 o 21 con datos reales
  17 tipos de pensamiento
  6 modos
  → Esto es vocabulario. Crece o se poda.

VARIABLE (L2 — cambia con cada ejecución):
  Preguntas dentro de cada celda
  Scores de efectividad
  Cobertura por dominio
  → Esto es contenido. Se llena, se mejora, se descarta.
```

---

## 2. LA MATRIZ — ESTRUCTURA 3L × 7F × 18INT — Documento Maestro §2

### El esquema central

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

### Dependencias entre lentes

- Salud sin Sentido = funciona pero sin dirección (frágil)
- Sentido sin Salud = visión sin capacidad de ejecutar
- Continuidad sin Sentido = replicar vacío

### Dependencias entre funciones

- F2 Captar sin F3 Depurar = acumular basura
- F4 Distribuir sin F5 Frontera = fugas
- F1 Conservar sin F6 Adaptar = rigidez
- F7 Replicar sin F5 Frontera = replicar ruido

---

## 3. EL ÁLGEBRA = COMPILADOR DE PROMPTS — Documento Maestro §3

Las operaciones algebraicas son **operaciones de ensamblaje de redes de preguntas:**

```
Fusión ∫(A|B):     Prompt = [preguntas de A] + [preguntas de B] en paralelo
Composición A→B:   Prompt = [preguntas de A], luego [preguntas de B sobre output de A]
Diferencial A-B:   Prompt = [preguntas que A tiene y B no puede tener]
Integración ∫:     Prompt = [preguntas que emergen al cruzar las anteriores]
Loop test A→A:     Prompt = [mismas preguntas sobre su propio output]
```

### Propiedades confirmadas (34 chats cartografía)

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

### 13 reglas del compilador

**Selección:** (1) Núcleo irreducible: 1 cuantitativa + 1 humana + INT-16. (2) Máximo diferencial entre categorías. (3) Sweet spot: 4-5 inteligencias.

**Orden:** (4) Formal primero. (5) No reorganizar secuencia. (6) Fusiones: primero la más alineada con el sujeto.

**Profundidad:** (7) 2 pasadas por defecto. (8) No tercera pasada.

**Paralelización:** (9) Fusiones izquierda paralelizables al ~70%. (10) Cruce derecho no factorizable.

**Patrones universales:** (11) Marco binario es universal → INT-14+INT-01 primero. (12) Conversación pendiente es universal. (13) Infrautilización antes de expansión.

---

## 4. L0: ÁLGEBRA DEL CÁLCULO SEMÁNTICO — Documento L0

### Definición

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

### Objetos semánticos — qué produce el cálculo

**Nivel 0: COORDENADAS (primitivas — posicionan)**

Las 7 primitivas producen 5 tipos de coordenada:

| Tipo | Fuente | Qué produce | Ejemplo (dentista) |
|------|--------|-------------|-------------------|
| C1 COMPRESIÓN | sustantivizar | Nombre a 3 escalas (palabra/frase/párrafo) | "Dilema capacidad-vida" |
| C2 POSICIÓN | adjetivar + adverbializar + verbo | Dónde está cada pieza: id (declarada) vs ir (real) | SACRIFICAR id=0 ir=0.92 |
| C3 RELACIÓN | preposicionar + conjuntar | Cómo se conectan las piezas (y qué conexiones faltan) | "Negocio DENTRO de vida familiar, no al revés" |
| C4 NIVEL | sujeto_predicado | Quién opera sobre quién, con qué poder | Mujer poder=0.2, Banco poder=0.6 |
| C5 DISTANCIA | calculadora ($0, código puro) | Gaps id↔ir + propagaciones + lentes | SACRIFICAR gap=0.92 desinflada |

**Nivel 1: HUECOS ACTIVOS (sintetizador — cruza coordenadas)**

| Tipo | Cruce | Qué produce | Ejemplo (dentista) |
|------|-------|-------------|-------------------|
| H1 INVERSIÓN SEMÁNTICA | C1 × C2 | Lo declarado ≠ lo real | "Elegir" cuando ya eligió |
| H2 FUNCIÓN INVISIBLE | C2 × C5 | Opera con potencia máxima porque no se nombra | SACRIFICAR ir=0.92 id=0 — invisible |
| H3 CONEXIÓN AUSENTE ACTIVA | C3 × H2 | La desconexión sostiene el sistema | "Mantener A, B, C separados es lo que permite que el sacrificio continúe" |

**Nivel 2: TOPOLOGÍA (1 isomorfismo, 1 loop — proyecta forma)**

| Tipo | Isomorfismo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------|-------------------|
| T1 CONTENEDORES | conjuntos | Quién contiene a quién, qué se solapa, qué falta | "Negocio dentro de vida familiar, no al revés" + gaps: cálculo horas/vida ausente |
| T2 CIRCUITOS | causal/dinámica | Qué loops existen, si se amplifican o frenan, hacia dónde converge | Loop refuerzo: Margen→Inversión→Más trabajo→Menos vida→Necesidad margen |
| T3 TABLERO | juegos/agentes | Qué jugadores, qué incentivos, quién gana si nadie cambia | Odontólogo 0.55 / Mujer 0.2 / Banco 0.6 / Sistema 0.9 |
| T4 CONTROL | cibernética | Qué mide, qué ajusta, qué señales ignora | Sensores: solo económicos. Feedback mujer: ignorado. Regulación: rígida |

**Nivel 3: MECANISMO (composición A→B — explica la forma)**

| Composición | Mecanismo | Pregunta que responde | Ejemplo (dentista) |
|-------------|-----------|----------------------|-------------------|
| causal→juegos | M1: MOTOR DEL LOOP | ¿Quién alimenta los circuitos? | Banco inyecta en "Inversión", Sistema normaliza "Más trabajo", Mujer frena pero poder insuficiente |
| conjuntos→causal | M2: CAUSA DE LA FORMA | ¿Qué produce la estructura de contención? | Nunca se calculó tasa tiempo→dinero, negocio se expande sin frontera |
| juegos→cibernética | M3: REGULACIÓN DEL JUEGO | ¿Qué impide que los jugadores cambien? | Odontólogo solo tiene sensor económico. Feedback vital no llega a actuador |
| causal→conjuntos | M4: FRONTERA DE CIRCULACIÓN | ¿Qué entra en los loops y qué queda fuera? | Familia/hijos/salud están FUERA de todos los loops de decisión |
| cibernética→causal | M5: LOOPS DE CONTROL | ¿Qué loops genera la regulación misma? | Medir solo dinero→decidir por dinero→refuerza medir solo dinero |

**Nivel 4: INVARIANTE (recursión A² — estructura que se replica)**

| Tipo | Recursión | Qué produce | Ejemplo (dentista) |
|------|-----------|-------------|-------------------|
| I1 CONTENCIÓN REPLICADA | conjuntos² | "Estar dentro sin verlo" se repite a cada escala | M2 dentro de paradigma = negocio dentro de vida familiar |
| I2 CIRCUITO REPLICADO | causal² | El mismo tipo de loop a cada nivel | "Diagnóstico preciso→Soluciones dentro del paradigma→Problema intacto→Más diagnóstico" |
| I3 JUGADOR INVISIBLE | juegos² | El agente con más poder es el menos nombrado, siempre | Nivel 1: "Sistema" poder=0.9. Nivel 2: "Paradigma-crecimiento" poder=0.95 |
| I4 SENSOR CIEGO | cibernética² | No mide lo que más importa, a cada nivel | Dentista no mide vida. M2 no mide sus propias premisas |

**Nivel ∞: PUNTO CIEGO (crítico — frontera del análisis)**

| Tipo | Qué produce | Ejemplo (dentista) |
|------|-------------|-------------------|
| P1 PREMISA OCULTA | Algo que todo el análisis asume sin examinar | "M2 asume que 'crecer' es necesario" |
| P2 PARADOJA PERFORMATIVA | El análisis hace exactamente lo que diagnostica | "Precisión técnica M2 = ceguera sistémica sobre sí mismo" |
| P3 FRONTERA DE MARCO | Lo que este marco no puede ver por construcción | "¿Y si 7K€/mes con vida familiar ES el éxito?" |

### Operaciones — las 4 operaciones del cálculo

**3.1 FUSIÓN (|) — como suma**

Dos o más isomorfismos operan en **paralelo** sobre el MISMO input. Producen topologías independientes.

```
causal|juegos(datos) → T2 + T3 (dos topologías independientes)
```

| Propiedad | Valor |
|-----------|-------|
| Conmutativa | Sí: A\|B = B\|A |
| Asociativa | Sí: (A\|B)\|C = A\|(B\|C) |
| Inverso (resta) | No existe como operación. Sí existe como contribución marginal |

**3.2 COMPOSICIÓN (→) — como multiplicación**

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

**3.3 INTEGRACIÓN (∫) — como sumatorio Σ**

Un agente mira TODAS las topologías de una fusión simultáneamente. Produce CRUCE: conexiones entre topologías que ninguna ve sola.

```
∫(causal|juegos|conjuntos|cibernética)(datos) → cruce
```

**3.4 DIFERENCIAL (-) — como resta**

Lo que A ve que B NO puede ver. Mide el valor único de cada isomorfismo.

```
Juegos - Cibernética = incentivos puros (motivación independiente de regulación)
Cibernética - Juegos = regulación pura (control independiente de jugadores)
```

### Propiedades algebraicas confirmadas/refutadas

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

## 5. RESULTADOS EXPERIMENTALES COMPLETOS

### EXP 4 — Mesa Redonda (R1 vs R2) — Arquitectura Mecanismos

**Hallazgos clave:**

Los 3 modelos OS superan a Claude en la Matriz. DeepSeek V3.1 (2.19), R1 (2.18), GPT-OSS (2.15) vs Claude (1.79). R1 cubre 20/21 celdas — la mayor cobertura de todos.

**Comparación agregada cross-experimento:**

| Método | Media | 3+/105 | Conexiones | Evaluador |
|--------|-------|--------|------------|-----------|
| Exp 4 R1 max mecánico | 2.89 | 77 | 0 | 12 modelos |
| Exp 4 R2 mesa redonda | 3.27 | 93 | 0 | 12 modelos post-R2 |
| Exp 4.1 mesa especializada | ~3.30 | 95 | 0 | 12 modelos con prompts foco |
| Exp 4.3 mente distribuida (ext) | 3.06 | 94 | 425 | Claude externo |
| Exp 4.3 auto-tracking | 3.99 | 105 | 425 | Auto (inflado +0.93) |

**Auto-evaluación infla ~1 punto:** La pizarra (auto-tracking) da media 3.99. Evaluación externa: 3.06. Delta: +0.93.

### EXP 5 — Cadena de Montaje

**Configuración ganadora (Línea Industrial):** 56% pass rate medio.

**Delta cadena vs baseline:** +24% (Baseline: 32%, Mejor cadena: 56%).

**Mesa mínima óptima (Especializada):** V3.2-chat + V3.1 = 97.9% cobertura.

### EXP 5b — Nuevos Modelos en Pipeline

**Resultado T1 (Edge Function):** De 0% (Exp 5) a 100% (Exp 5b) con Step-3.5-flash y Devstral.

**Problema T4 (Orquestador):** Think-tag blow-up en Step 3.5 Flash. Solución: usar MiMo V2 Flash o Devstral para arquitectura.

### EXP 1 BIS — 6 Modelos Nuevos

**Ranking Overall:**
1. Step-3.5-flash (0.98)
2. Nemotron-super (0.96)
3. MiMo-v2-flash (0.90)
4. Kimi-k2.5 (0.86)
5. Devstral (0.86)
6. Qwen3.5-397b (0.85)

**Mejor por rol:**
- Pizarra (agent swarm): Kimi K2.5
- Evaluador: Qwen 3.5 397B
- Math/Validación: Nemotron Super
- Debugger: Step-3.5-flash
- Tier barato: MiMo-v2-flash
- Patcher: Devstral

### EXP 6 — OpenHands (Arquitectura de Referencia)

**Patrones clave para nuestro agente:**
1. Event-driven > imperativo
2. Error como input (ErrorObservation)
3. Stuck detection multi-escenario (5 patrones)
4. Sin blacklist, con risk model (solo funciona con Docker)
5. Condenser > truncate
6. Budget enforcement
7. Function calling JSON
8. 5 herramientas son suficientes

### EXP 7 — Diseños de Arquitectura (R1)

**Diseño Cogito (Síntesis):** Enjambre de 8 componentes, Director + Compilador + Ejecutor + Sintetizador + Guardián + Refinador.

**Diseño DeepSeek (Arquitectura):** 8 componentes lógicos, Router & Queue Manager (MiMo V2), Motor Cognitivo (Multi-modelo), Agente de Coding (Devstral/Step).

**Diseño Kimi (Enjambre):** 8 componentes, Director (V3.2), Compilador (MiMo), Detective (MiMo), Agente Analítico (Step 3.5), Artesano (Devstral), Sintetizador (Cogito+GPT-OSS), Guardián (MiMo), Refinador (V3.1).

**Diseño Nemotron (Coste):** Orquestador de Gaps (código puro), Router de Modelos (código puro), Ejecutor Multi-Modelo (LLM), Sintetizador (Cogito selectivo), Agente de Actuación (código puro), Gestor de Persistencia (código puro), Optimizador de Coste (código puro), Detector de Contradicciones (código puro). Coste objetivo: $0.02/turno.

**Diseño Step 3.5 (Razonamiento):** 8 componentes lógicos, enfasis en loop observe→think→act con stuck detection y budget enforcement.

---

## 6. PROPIEDADES ALGEBRAICAS CARTOGRAFIADAS (34 chats) — Output Final Cartografía

### Pares complementarios (TOP 10)

| Par | Score | Qué ve A que B no | Qué ve B que A no |
|-----|-------|-------------------|-------------------|
| INT-01 × INT-08 | 0.95 | Contradicción formal, sistema subdeterminado | Duelo anticipado, lealtad invisible |
| INT-07 × INT-17 | 0.93 | Ratio margen/costes, asimetría cuantificada | Brecha valores vividos, inercia |
| INT-02 × INT-15 | 0.90 | Grafo de dependencias, atajo de 10 minutos | Isomorfismo solución-problema |
| INT-09 × INT-16 | 0.88 | Palabra ausente, acto performativo | Prototipo concreto, secuencia constructiva |
| INT-04 × INT-14 | 0.87 | Monocultivo humano, nichos vacíos | 20+ opciones, WeWork dental |
| INT-06 × INT-10 | 0.86 | Distribución poder, coaliciones | Tensión-nudo vs tensión-músculo |
| INT-12 × INT-02 | 0.85 | Roles arquetípicos, Viaje del Héroe | Grafo de dependencias, scheduling |
| INT-11 × INT-08 | 0.84 | Punto de compresión, pendiente gravitacional | Duelo anticipado, identidad fusionada |
| INT-03 × INT-18 | 0.83 | Gap id↔ir, circuito único | Urgencia inventada, vacío como recurso |
| INT-05 × INT-09 | 0.82 | Secuencia obligatoria, reversibilidad | Metáfora escalera-máquina, silencio |

### Propiedades testadas (Fase 4)

| P | Propiedad | Predicción | Resultado | Δ vs teoría |
|---|-----------|-----------|-----------|-------------|
| P01 | Conmutatividad fusión | A\|B = B\|A | PARCIAL (1/4 true) | Desviación |
| P02 | No-conmutatividad composición | A→B ≠ B→A | CONFIRMADA (4/4) | Coincide |
| P03 | Asociatividad composición | (A→B)→C = A→(B→C) | FALSE | Desviación |
| P04 | Distributividad izquierda | A→(B\|C) = (A→B)\|(A→C) | PARCIAL (~70%) | Parcial |
| P05 | NO distributiva derecha | (B\|C)→A ≠ (B→A)\|(C→A) | CONFIRMADA | Coincide |
| P06 | No-idempotencia | A→A ≠ A | CONFIRMADA (18/18) | Coincide |
| P07 | Saturación | A^n converge | CONFIRMADA (n=2 óptimo) | Coincide |
| P08 | Clausura | output ∈ input | CONFIRMADA (calidad alta) | Coincide |

---

### FIN BRIEFING AUDITOR 1