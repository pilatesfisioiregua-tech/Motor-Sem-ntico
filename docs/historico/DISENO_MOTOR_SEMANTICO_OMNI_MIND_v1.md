# DISEÑO MOTOR SEMÁNTICO OMNI-MIND — Documento Maestro

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-08
**Origen:** Sesión de diseño Opus — derivación desde Cartografía Meta-Red v1
**Dependencias:** PROTOCOLO_CARTOGRAFIA_META_RED_v1.md, META_RED_INTELIGENCIAS_CR0.md, TABLA_PERIODICA_INTELIGENCIA_CR0.md, ALGEBRA_CALCULO_SEMANTICO_CR0.md

---

## 1. VISIÓN

Un motor que recibe cualquier input en lenguaje natural y genera automáticamente el algoritmo óptimo de inteligencias para procesarlo. No tiene programas fijos — compila un programa nuevo para cada petición desde las primitivas de la Meta-Red.

```
MOTOR v3.3 (actual):
  1 álgebra fija (Estructural) × 4 isomorfismos fijos
  $0.91 | ~293s | programa hardcoded

MOTOR SEMÁNTICO (objetivo):
  N álgebras seleccionadas × operaciones óptimas × modelos híbridos
  ~$0.35-1.50 | ~30-120s | programa generado ad-hoc
```

El motor es infraestructura neutra. Lo que cambia es qué se construye encima:
- Exocortex CEO → analiza decisiones estratégicas
- Exocortex Financiero → analiza y genera para departamentos financieros
- Chat de contenido → genera textos con las inteligencias óptimas para el tema
- Cualquier vertical → mismo motor, distinta selección de inteligencias

---

## 2. ARQUITECTURA — 4 CAPAS

```
┌─────────────────────────────────────────────────┐
│  CAPA 4: INTERFAZ                               │
│  Chat / API / Exocortex                         │
│  Recibe input del usuario, devuelve output       │
├─────────────────────────────────────────────────┤
│  CAPA 3: EJECUCIÓN                              │
│  LLMs (Haiku/Sonnet/Opus) + Calculadoras +      │
│  Simuladores — ejecuta los prompts generados     │
├─────────────────────────────────────────────────┤
│  CAPA 2: COMPILADOR                             │
│  Router + Selector + Compositor + Generador      │
│  Genera el algoritmo óptimo para cada petición   │
├─────────────────────────────────────────────────┤
│  CAPA 1: BASE DE DATOS DE EFECTOS               │
│  Cartografía + Datos sintéticos + Datos reales   │
│  El conocimiento de qué produce cada combinación │
└─────────────────────────────────────────────────┘
```

---

## 3. ROADMAP — 6 FASES

```
FASE A: Cartografía                    ← ESTAMOS AQUÍ
FASE B: Generación de datos sintéticos
FASE C: Entrenamiento modelos ligeros
FASE D: Motor v1 (híbrido)
FASE E: Interfaz chat / exocortex
FASE F: Validación con pilotos reales + retroalimentación
```

---

## 4. FASE A — CARTOGRAFÍA (2-3 semanas)

### Objetivo
Generar la base de datos empírica de efectos de las 18 inteligencias.

### Ejecución
Protocolo completo en PROTOCOLO_CARTOGRAFIA_META_RED_v1.md.

### Sub-fases

| Sub-fase | Chats | Output |
|----------|-------|--------|
| A1: 18 individuales × 3 casos | 18 | 54 análisis (narrativa + JSON) |
| A2: Matrices de diferenciales | 3 | 3 matrices 18×18 de complementariedad |
| A3: Combinaciones selectivas | 10-15 | Fusiones, composiciones con propiedades |
| A4: Tests de propiedades | 3-5 | P01-P11 confirmadas/refutadas |

### Output de Fase A

```
DB_EFECTOS_v1/
  ├── individuales/
  │     ├── INT-01_caso1.json ... INT-18_caso3.json  (54 archivos)
  │     └── meta/
  │           ├── loop_tests.json          (18 — no idempotencia)
  │           ├── patrones_cross_case.json  (18 — invariantes)
  │           └── saturacion.json           (18 — profundidad útil)
  ├── diferenciales/
  │     ├── matriz_caso1.json    (18×18)
  │     ├── matriz_caso2.json    (18×18)
  │     └── matriz_caso3.json    (18×18)
  ├── combinaciones/
  │     ├── fusiones.json        (resultados ∫(A|B))
  │     ├── composiciones.json   (resultados A→B y B→A)
  │     └── emergentes.json      (lo que solo aparece al combinar)
  └── propiedades/
        └── propiedades_P01_P11.json  (confirmadas/refutadas)
```

### Criterio de cierre Fase A
- 54 análisis completos con JSON
- 3 matrices de diferenciales
- TOP 10 pares complementarios identificados por caso
- Al menos 5 propiedades confirmadas/refutadas empíricamente

---

## 5. FASE B — GENERACIÓN DE DATOS SINTÉTICOS (1 semana)

### Objetivo
Ampliar de 3 casos reales a ~300 casos sintéticos para entrenar modelos ligeros.

### Método
Claude como fábrica de datos, usando la DB de Fase A como ground truth.

### Sub-fases

**B1: Casos sintéticos por dominio (3-4 chats)**

```
PROMPT TEMPLATE:

Tienes acceso a la cartografía de 18 inteligencias sobre 3 casos reales.
Genera 20 casos sintéticos para el dominio [DOMINIO].

Para cada caso:
1. Descripción (3-5 líneas, con datos concretos — números, nombres, tensiones)
2. Las 5 inteligencias que más valor aportarían (ordenadas por diferencial)
3. Las 3 más redundantes para este caso
4. La operación óptima entre las top 2 (fusión, composición A→B, o B→A)
5. Justificación basada en los diferenciales de la cartografía

Dominios: finanzas, salud, tech/startup, educación, legal,
          retail, manufactura, servicios profesionales,
          decisiones personales, organizaciones sin ánimo de lucro

Output: JSON array de 20 objetos.
```

Output esperado: **200 casos etiquetados** (10 dominios × 20 casos).

**B2: Variaciones de peticiones por inteligencia (2-3 chats)**

```
PROMPT TEMPLATE:

Para la inteligencia [INT-XX] ([NOMBRE]):
Genera 30 peticiones de usuario que activarían esta inteligencia.
Rango: desde lo obvio hasta lo no obvio.

Para cada petición:
- texto: la petición en lenguaje natural
- relevancia: 0.0-1.0 para esta inteligencia
- dominio: en qué dominio cae
- inteligencias_secundarias: qué otras inteligencias complementarían

Output: JSON array.
```

Output esperado: **540 pares texto-relevancia** (18 × 30).

**B3: Datos de composición (2-3 chats)**

```
PROMPT TEMPLATE:

Basándote en los resultados de Fase A3 donde [INT-A]→[INT-B] 
produjo X y [INT-B]→[INT-A] produjo Y:

Genera 15 casos donde el orden importa (no conmutativo) y 
15 donde no importa. Para cada caso:
- descripcion: el caso
- orden_optimo: "A→B" o "B→A" o "indistinto"
- features: qué del input predice cuál es mejor
- justificacion: por qué

Pares a generar: los TOP 10 complementarios de Fase A2.
```

Output esperado: **300 datapoints de composición** (10 pares × 30).

**B4: Datos de calidad para scorer (1-2 chats)**

```
PROMPT TEMPLATE:

Aquí tienes 5 outputs reales de la cartografía para [INT-XX] sobre [CASO].
Puntúa cada uno 1-10 en:
- profundidad: ¿va más allá de lo obvio?
- originalidad: ¿ve algo que un análisis genérico no vería?
- accionabilidad: ¿el usuario puede hacer algo con esto?
- precision: ¿los hallazgos están bien fundamentados?

Ahora genera 10 outputs sintéticos de calidad variable (desde 2/10 hasta 9/10)
con sus puntuaciones. Estos entrenarán el modelo de scoring.
```

Output esperado: **180 outputs puntuados** (18 inteligencias × 10).

### Output de Fase B

```
DATOS_SINTETICOS_v1/
  ├── casos_por_dominio.json           (200 casos etiquetados)
  ├── peticiones_por_inteligencia.json  (540 pares texto-relevancia)
  ├── composicion_orden.json            (300 datapoints)
  └── calidad_scoring.json              (180 outputs puntuados)
```

### Validación humana
Jesús revisa 10% de cada dataset (~120 datapoints).
Corrige errores. Los corregidos pesan 3x en entrenamiento.

### Criterio de cierre Fase B
- 200+ casos etiquetados dominio→inteligencias
- 540+ pares texto-relevancia
- 300+ datapoints de composición
- 180+ outputs con scoring
- 10% validado por Jesús

---

## 6. FASE C — ENTRENAMIENTO MODELOS LIGEROS (2-3 días)

### Objetivo
Entrenar 4 modelos que reemplazan a Opus donde es overkill.

### Modelo 1: Router por Embeddings

```
Tipo:          Embeddings + cosine similarity
Datos:         540 pares texto-relevancia (Fase B2) + 200 casos (B1)
Modelo base:   Voyage-3 (o el que esté activo)
Función:       Input del usuario → top-K inteligencias más relevantes
Latencia:      <500ms
Coste/call:    ~$0.001
Reemplaza a:   Opus como parser + selector (pasos 1-2)
```

Implementación:
- Embed cada inteligencia con su firma + objetos + punto ciego → 18 vectores de referencia
- Embed la petición del usuario → 1 vector query
- Cosine similarity → ranking de 18 inteligencias
- Threshold → seleccionar las que superan umbral (calibrar con datos de B1)

### Modelo 2: Clasificador Dominio→Inteligencias

```
Tipo:          XGBoost / Random Forest
Datos:         200 casos etiquetados (Fase B1)
Features:      TF-IDF del texto + dominio + presencia de números + 
               presencia de personas + presencia de conflicto
Target:        Top-5 inteligencias (multi-label)
Latencia:      <100ms
Coste/call:    $0 (corre local)
Reemplaza a:   Opus como selector (paso 2), complementa al Router
```

Sirve como second opinion del Router de embeddings. Si ambos coinciden en top-3, alta confianza. Si divergen, escalar a Opus.

### Modelo 3: Compositor por Grafo

```
Tipo:          Grafo pesado + solver de optimización
Datos:         Matrices de diferenciales (Fase A2) + composiciones (A3) + 
               datos de orden (B3)
Nodos:         18 inteligencias
Aristas:       Pesos = diferencial entre pares
Restricciones: Presupuesto ($), tiempo, número máximo de pasos
Función:       Dadas N inteligencias seleccionadas → algoritmo óptimo
               (qué operaciones, en qué orden)
Latencia:      <200ms
Coste/call:    $0 (corre local)
Reemplaza a:   Opus como compositor (paso 3)
```

Implementación:
- Grafo dirigido (porque composición no es conmutativa)
- Peso de arista A→B = valor de la composición A→B (de Fase A3)
- Peso de arista A|B = valor de la fusión (de Fase A3)
- Solver: dado presupuesto, maximizar valor total del camino
- Output: secuencia de operaciones como JSON

### Modelo 4: Scorer de Calidad

```
Tipo:          Regresión (Ridge / pequeña red neuronal)
Datos:         180 outputs puntuados (Fase B4) + outputs reales validados
Features:      Longitud, número de hallazgos, diversidad de pasos,
               presencia de frontera, nivel medio de confianza
Target:        Score 1-10 (promedio de profundidad/originalidad/
               accionabilidad/precisión)
Latencia:      <50ms
Coste/call:    $0 (corre local)
Función:       Evalúa output antes de entregarlo. Si score < 6, relanza.
```

### Stack técnico

```
Embeddings:     Voyage API (ya tienes VOYAGE_API_KEY)
ML:             scikit-learn (clasificador, scorer)
Grafos:         networkx + scipy.optimize (compositor)
Deploy:         fly.io (junto al Motor) o como módulos en Supabase Edge
Almacenamiento: Supabase PostgreSQL (DB de efectos + modelos serializados)
```

### Criterio de cierre Fase C
- Router embeddings: accuracy >80% en top-3 (validado con holdout de B1)
- Clasificador: F1 >0.75 en multi-label (validado con holdout de B1)
- Compositor: produce algoritmos válidos para los 3 casos de cartografía
- Scorer: correlación >0.7 con puntuaciones de Fase B4

---

## 7. FASE D — MOTOR v1 HÍBRIDO (1-2 semanas)

### Objetivo
Integrar las 4 capas en un pipeline funcional desplegado en fly.io.

### Arquitectura del pipeline

```
INPUT (texto del usuario)
         │
         ▼
┌─────────────────────────┐
│  CAPA 1: ROUTING        │  ~500ms | ~$0.001
│  Embeddings + Clasif.   │
│  → Top-K inteligencias  │
│  → Si divergen: Opus    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 2: COMPOSICIÓN    │  ~200ms | $0
│  Grafo + Solver         │
│  → Algoritmo óptimo     │
│  → Operaciones + orden  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 3: GENERACIÓN     │  ~100ms | $0
│  Meta-Red DB + Templates│
│  → Prompts exactos      │
│  (código puro)          │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 4: EJECUCIÓN      │  30-120s | $0.30-0.80
│  Haiku: extracción      │
│  Sonnet: integración    │
│  Opus: frontera + final │
│  Código: cálculos puros │
│  Simuladores: escenarios│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 5: EVALUACIÓN     │  ~50ms | $0
│  Scorer de calidad      │
│  Si score < umbral:     │
│    → relanzar con más   │
│      profundidad        │
│  Si score OK:           │
│    → entregar           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 6: INTEGRACIÓN    │  10-20s | ~$0.15-0.25
│  Opus: síntesis final   │
│  → Output al usuario    │
│  → Log para retroalim.  │
└─────────────────────────┘

TOTAL: ~$0.35-1.50 | ~40-150s
```

### API del Motor

```
POST /motor/ejecutar
{
  "input": "texto libre del usuario",
  "contexto": "opcional — contexto previo, dominio, restricciones",
  "config": {
    "presupuesto_max": 1.50,
    "tiempo_max_s": 120,
    "profundidad": "normal|profunda|maxima",
    "inteligencias_forzadas": [],
    "inteligencias_excluidas": []
  }
}

RESPONSE:
{
  "algoritmo_usado": {
    "inteligencias": ["INT-07", "INT-05", "INT-06"],
    "operaciones": ["∫(INT-07|INT-05)", "→INT-06"],
    "loops": {"INT-07": 2}
  },
  "resultado": {
    "narrativa": "...",
    "hallazgos": [...],
    "firma_combinada": "...",
    "puntos_ciegos": [...]
  },
  "meta": {
    "coste": 0.87,
    "tiempo_s": 95,
    "score_calidad": 7.8,
    "inteligencias_descartadas": ["INT-15", "INT-10"]
  }
}
```

### Modos del Motor

```
MODO ANÁLISIS:      Input = caso/situación → Output = diagnóstico multi-inteligencia
MODO GENERACIÓN:    Input = briefing/tema  → Output = contenido generado con inteligencias
MODO CONVERSACIÓN:  Input = turno de chat  → Output = respuesta informada por inteligencias
MODO CONFRONTACIÓN: Input = propuesta      → Output = puntos ciegos + alternativas
```

Los modos NO son programas diferentes. Son configuraciones del mismo pipeline:
- Análisis: más inteligencias, más profundidad, output estructurado
- Generación: inteligencias creativas pesadas (INT-14, INT-15, INT-09), output narrativo
- Conversación: routing rápido, menos inteligencias, baja latencia
- Confrontación: inteligencias de frontera pesadas (INT-17, INT-18), output brutal

### Criterio de cierre Fase D
- Pipeline end-to-end funcional en fly.io
- Acepta input en lenguaje natural, devuelve output estructurado
- Los 4 modos funcionan
- Coste < $1.50 por ejecución
- Latencia < 150s en modo análisis, < 60s en modo conversación

---

## 8. FASE E — INTERFAZ CHAT / EXOCORTEX (1-2 semanas)

### Objetivo
Un chat donde el usuario escribe naturalmente y el motor trabaja por debajo.

### Arquitectura

```
USUARIO: "Necesito preparar la presentación para el board 
          sobre el Q2. Tenemos problemas de retención."

INTERFAZ CHAT
    │
    ├── Detecta: modo GENERACIÓN + ANÁLISIS
    ├── Contexto: acumula historial + datos previos
    │
    ▼
MOTOR SEMÁNTICO
    │
    ├── Router: INT-07 (Financiera) + INT-05 (Estratégica) + 
    │           INT-06 (Política) + INT-09 (Lingüística)
    ├── Compositor: ∫(Financiera|Estratégica) → Política → Lingüística
    ├── Ejecuta pipeline
    │
    ▼
RESPUESTA AL USUARIO:
    "Para la presentación del Q2, hay 3 ángulos que el board 
     necesita ver: [hallazgos de Financiera], [posición de 
     Estratégica], [stakeholders de Política].
     
     El punto ciego: [lo que ninguna de estas ve].
     
     ¿Quieres que profundice en alguno o que genere 
     el esqueleto de la presentación?"
```

### Capa Superficial vs Capa Profunda

```
CAPA SUPERFICIAL (visible):
  - Responde al usuario en tiempo real (~10-20s)
  - Usa modo CONVERSACIÓN del motor (routing rápido, pocas inteligencias)
  - Tono natural, no técnico
  
CAPA PROFUNDA (invisible):
  - Se alimenta de cada input del usuario
  - Acumula patrones entre conversaciones
  - Detecta: contradicciones, patrones repetidos, datos implícitos
  - EMERGE cuando es relevante (no cuando se pide)
  
CUÁNDO EMERGE LA CAPA PROFUNDA:
  - Detecta patrón recurrente: "En 4 conversaciones has planteado 
    el crecimiento como solución, pero los datos muestran que el 
    problema es retención"
  - Detecta contradicción: "Dices que la prioridad es el equipo, 
    pero todas tus preguntas son sobre revenue"
  - Conecta datos: "El dato de retención que mencionaste el martes 
    contradice la proyección del deck del viernes"
```

### Estado persistente

```
ESTADO POR USUARIO:
{
  "contexto_acumulado": [...],        // inputs + outputs anteriores
  "patrones_detectados": [...],        // por capa profunda
  "decisiones_abiertas": [...],        // CR1 pendientes
  "inteligencias_frecuentes": [...],   // cuáles usa más este usuario
  "dominio_principal": "...",          // detectado por uso
  "preferencias": {
    "profundidad": "alta",
    "tono": "directo",
    "formato": "narrativa"
  }
}
```

### Generación de contenido con inteligencias

```
USUARIO: "Escríbeme un post de LinkedIn sobre liderazgo 
          en tiempos de incertidumbre"

MOTOR:
  Router → INT-09 (Lingüística) + INT-12 (Narrativa) + 
           INT-05 (Estratégica) + INT-17 (Existencial)
  
  INT-09: marco lingüístico, metáforas, actos de habla
  INT-12: arco narrativo, personaje, transformación
  INT-05: posición, anticipación, movimiento
  INT-17: propósito, finitud, lo que está en juego
  
  Compositor: INT-17 → INT-12 → ∫(INT-09|INT-05)
  (Existencial da el fondo → Narrativa da la estructura → 
   Lingüística + Estratégica dan la forma)
  
OUTPUT: Post que no es genérico porque está construido desde
        4 inteligencias diferentes, cada una aportando su capa.
```

### Criterio de cierre Fase E
- Chat funcional accesible vía web
- Modo conversación con latencia < 30s por turno
- Estado persistente entre sesiones
- Capa profunda detecta al menos 1 patrón en 5 conversaciones
- Generación de contenido usa mínimo 3 inteligencias

---

## 9. FASE F — VALIDACIÓN Y RETROALIMENTACIÓN (ongoing)

### Objetivo
Validar con pilotos reales y crear el loop de mejora continua.

### Pilotos

| Piloto | Dominio | Modo principal | Inteligencias esperadas |
|--------|---------|---------------|------------------------|
| Authentic Pilates | Salud/Negocio | Análisis + Conversación | INT-10, INT-04, INT-07, INT-16 |
| Clínica fisio | Salud | Análisis | INT-10, INT-08, INT-04, INT-02 |
| Jesús (OMNI-MIND) | Tech/Estrategia | Todos | INT-03, INT-02, INT-05, INT-16 |

### Loop de retroalimentación

```
CADA EJECUCIÓN DEL MOTOR GENERA:
{
  "input": "...",
  "algoritmo": {...},
  "output": {...},
  "score_auto": 7.8,
  "feedback_usuario": null  // se rellena si el usuario valora
}

NIGHTLY:
  - Agregar nuevos datapoints a la DB
  - Re-entrenar clasificador si hay >50 nuevos datapoints
  - Actualizar pesos del grafo si hay nuevas composiciones
  - Detectar inteligencias que consistentemente score bajo → investigar

SEMANAL:
  - Jesús revisa top-10 ejecuciones y bottom-10
  - Corrige etiquetas si el router falló
  - Identifica dominios no cubiertos
  
MENSUAL:
  - Re-ejecutar cartografía parcial si hay nuevos dominios
  - Evaluar si alguna inteligencia es consistentemente redundante → podar
  - Evaluar si falta alguna inteligencia → diseñar
```

### Criterio de cierre Fase F
No cierra. Es el estado estable del sistema.

---

## 10. TABLA DE MODELOS POR CAPA

| Capa | Modelo | Tipo | Coste/call | Latencia | Reemplaza |
|------|--------|------|-----------|---------|-----------|
| Routing | Voyage embeddings | Embeddings | ~$0.001 | <500ms | Opus parser |
| Routing | XGBoost | Clasificador | $0 | <100ms | Opus selector |
| Composición | NetworkX + Solver | Grafo + Optim. | $0 | <200ms | Opus compositor |
| Generación prompts | Código puro | Templates | $0 | <100ms | — |
| Ejecución: extracción | Haiku | LLM | ~$0.03 | ~5s | — |
| Ejecución: integración | Sonnet | LLM | ~$0.08 | ~10s | — |
| Ejecución: frontera | Opus | LLM | ~$0.15 | ~15s | — |
| Ejecución: números | numpy/scipy | Código | $0 | <1s | LLM en cálculos |
| Ejecución: escenarios | Monte Carlo | Simulación | $0 | <2s | LLM en proyecciones |
| Evaluación | Ridge/NN pequeña | Regresión | $0 | <50ms | Revisión manual |
| Integración final | Opus | LLM | ~$0.15 | ~15s | — |
| Capa profunda | Embeddings + clustering | ML | ~$0.01 | <2s | — |

---

## 11. STACK TÉCNICO COMPLETO

```
INFRAESTRUCTURA:
  fly.io              — Motor + API + modelos ligeros
  Supabase PostgreSQL  — DB de efectos + estado + logs

MODELOS LLM:
  Anthropic API        — Haiku, Sonnet, Opus (4 keys rotativas)

MODELOS NO-LLM:
  Voyage API           — Embeddings
  scikit-learn         — Clasificador, Scorer
  NetworkX + scipy     — Grafo compositor
  numpy                — Calculadoras financieras/matemáticas

INTERFAZ:
  HTML standalone      — Chat (como ceo.html actual)
  API REST             — Para integraciones

DATOS:
  Meta-Red             — 18 inteligencias como redes de preguntas (estático)
  DB de efectos        — Cartografía + sintéticos + reales (crece)
  Estado usuario       — Contexto acumulado (por usuario, en Supabase)
```

---

## 12. DEPENDENCIAS ENTRE FASES

```
A (Cartografía) ──────→ B (Datos sintéticos) ──→ C (Modelos ligeros)
                                                        │
                                                        ▼
                                                  D (Motor v1)
                                                        │
                                                        ▼
                                                  E (Chat/Exocortex)
                                                        │
                                                        ▼
                                                  F (Pilotos + Retro)
                                                        │
                                                        └──→ B (más datos) → C (re-entrena) → D (mejora)
```

No se puede saltar fases. Cada fase produce el input de la siguiente.
La Fase F retroalimenta B-C-D creando un loop de mejora continua.

---

## 13. ESTIMACIÓN TEMPORAL

```
Fase A: Cartografía                    2-3 semanas
Fase B: Datos sintéticos              1 semana
Fase C: Entrenamiento                  2-3 días
Fase D: Motor v1                       1-2 semanas
Fase E: Chat/Exocortex                1-2 semanas
Fase F: Pilotos                        ongoing
                                    ─────────────
Total hasta Motor funcional (A-D):     ~5-7 semanas
Total hasta Chat funcional (A-E):      ~6-9 semanas
```

---

## 14. PRESUPUESTO POR FASE

### Coste API (Anthropic + Voyage)

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

### Totales acumulados

```
Hasta Motor funcionando (A-D):      ~€310-360
Hasta Chat funcionando (A-E):       ~€390-470
Con 3 meses de pilotos (A-F):       ~€640-920
```

### Distribución óptima con presupuesto fijo

```
CON €500:
  €0    Fase A (gratis en claude.ai Pro)
  €100  Fase B (2 rondas + fuentes externas)
  €10   Fase C (entrenamiento)
  €150  Fase D (testing motor)
  €80   Fase E (testing chat)
  €160  Fase F (pilotos — ~2 meses a volumen medio)

CON €1.000:
  €0    Fase A
  €150  Fase B (3 rondas completas + nivel 2-3)
  €10   Fase C
  €200  Fase D (testing exhaustivo)
  €110  Fase E (testing completo)
  €530  Fase F (pilotos — ~4-5 meses a volumen alto)
```

### Coste recurrente post-lanzamiento

```
Ejecuciones del motor:  ~€1/ejecución × volumen
  10/día = ~€300/mes
  30/día = ~€900/mes
  
Re-entrenamiento mensual: ~€20/mes
Cartografía nuevos dominios: ~€30/dominio (puntual)
```

### El recurso escaso

El coste real no son los euros. Son las ~12-15 horas de cartografía (Fase A) y las ~40-60 horas de desarrollo (Fases D+E). Tu tiempo es el cuello de botella, no la API. Los euros escalan linealmente con volumen; tu tiempo no.

---

## 15. RIESGOS Y MITIGACIONES

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Cartografía produce datos insuficientes | Modelos ligeros no entrenan bien | Más casos en Fase A o más sintéticos en Fase B |
| Datos sintéticos de Claude tienen sesgo | Modelos heredan sesgo | Validación humana 10% + datos reales en Fase F |
| Router falla en dominios no vistos | Inteligencias incorrectas | Fallback a Opus como router, log para re-entrenar |
| Latencia > 150s en modo análisis | UX pobre | Streaming de resultados parciales + caché de routing |
| Coste > $1.50 por ejecución | No escala | Poda agresiva de inteligencias redundantes por el solver |
| Saturación de contexto en chat | Pierde información | Capa profunda con resúmenes progresivos + embeddings |

---

## 16. PROFUNDIDAD PROGRESIVA — EVOLUCIÓN DE LA META-RED

### El problema

La Meta-Red actual tiene ~40-60 preguntas por inteligencia. Es la versión base. Funciona para cualquier caso, pero no alcanza la profundidad de un especialista en ese dominio. Un CFO con 20 años haría preguntas que INT-07 base no contiene. Un instructor de Pilates experimentado haría preguntas que INT-10 base no contempla.

### La solución: 3 niveles de profundidad por inteligencia

```
NIVEL 1 — BASE (~50 preguntas)
  Lo que hay ahora en la Meta-Red.
  Genéricas. Funcionan para cualquier caso.
  Coste: ~$0.05 por inteligencia

NIVEL 2 — PROFUNDA (~150 preguntas, indexadas por sub-dominio)
  Preguntas de especialista.
  Ven lo que el nivel base no puede.
  Coste: ~$0.12 por inteligencia

NIVEL 3 — EXPERTA (~300+ preguntas, indexadas por sub-dominio)
  Preguntas que solo haría alguien con 20 años en ese campo.
  Regulatorias, técnicas, contra-intuitivas.
  Coste: ~$0.25 por inteligencia
```

### Estructura en la DB

```json
{
  "inteligencia": "INT-07",
  "paso": "EXTRAER",
  "lente": "L2_Apalancamiento",
  "nivel": "base",
  "sub_dominio": null,
  "preguntas": [
    "¿Estás usando dinero ajeno — crédito, deuda, inversores?",
    "¿Ese dinero ajeno amplifica tus ganancias o tus pérdidas?",
    "¿Cuánto puedes perder antes de que el apalancamiento te destruya?",
    "¿El que te presta gana más que tú con tu negocio?"
  ]
}

{
  "inteligencia": "INT-07",
  "paso": "EXTRAER",
  "lente": "L2_Apalancamiento",
  "nivel": "profunda",
  "sub_dominio": "startup_early_stage",
  "preguntas": [
    "¿Tu unit economics es positivo por cohorte o solo en agregado?",
    "¿El LTV/CAC mejora con el tiempo o se degrada?",
    "¿Los clientes grandes pagan más por feature custom o por valor real?",
    "¿El runway asume churn constante o el churn se acelera con el tiempo?",
    "¿Qué porcentaje de tu burn es reversible en 30 días si necesitas cortar?"
  ]
}

{
  "inteligencia": "INT-07",
  "paso": "EXTRAER",
  "lente": "L2_Apalancamiento",
  "nivel": "experta",
  "sub_dominio": "startup_early_stage",
  "preguntas": [
    "¿Tu cap table permite una ronda bridge sin dilución destructiva?",
    "¿Los covenants de deuda existente bloquean pivots estratégicos?",
    "¿Hay ventana de liquidación preferente que convierte VC en acreedor de facto?",
    "¿El founder vesting está acelerado por change-of-control o por tiempo?",
    "¿La estructura fiscal de la entidad permite carry-forward de pérdidas?"
  ]
}
```

### Cuándo escala el motor de nivel

```
DECISIÓN AUTOMÁTICA:
  
  1. DOMINIO → Si el caso es financiero y el router lo confirma
                → mínimo nivel profunda para INT-07
                → base para el resto
                
  2. SCORE  → Si el scorer evalúa output de nivel base < 6
                → escalar a profunda y re-ejecutar esa inteligencia
                → si profunda < 6 → escalar a experta
                
  3. BUDGET → El presupuesto de la petición acota el nivel máximo
                → modo conversación: solo base (rápido)
                → modo análisis: hasta profunda
                → modo análisis profundo: hasta experta
                
  4. USUARIO → Si el estado del usuario indica dominio recurrente
                → nivel profunda por defecto en ese dominio
```

### De dónde salen las preguntas de nivel 2 y 3

**Fuente 1 — Claude genera candidatas (Fase B ampliada)**

Un chat por inteligencia:

```
"La Meta-Red tiene estas preguntas base para INT-XX: [pegar].
Genera 100 preguntas de nivel 2 (especialista) para el sub-dominio [X].
Cada pregunta debe ver algo que las de nivel base NO PUEDEN ver.
Para cada pregunta: texto + qué revela + por qué base no lo alcanza.
Agrupa por paso (EXTRAER/CRUZAR/LENTE/INTEGRAR/ABSTRAER/FRONTERA)."
```

**Fuente 2 — Expertos reales**

Para cada dominio piloto, un experto revisa las preguntas generadas y añade las suyas. Cada experto que toca las preguntas las mejora exponencialmente.

- Pilates → Jesús revisa INT-10 Cinestésica nivel 2 y 3
- Fisioterapia → clínica piloto revisa INT-10 + INT-08
- Finanzas → cuando haya piloto financiero

**Fuente 3 — Uso real (Fase F)**

Cuando el motor ejecuta y el output es pobre, el sistema detecta qué faltó. Si un caso financiero produce score bajo en INT-07, eso indica que las preguntas base no fueron suficientes. El sistema genera demanda de preguntas más profundas para ese sub-dominio.

```
LOG DE DÉFICIT:
{
  "inteligencia": "INT-07",
  "caso_tipo": "multinacional_transfer_pricing",
  "nivel_usado": "profunda",
  "score": 4.2,
  "diagnostico": "No hay preguntas sobre precios de transferencia entre jurisdicciones",
  "accion": "generar preguntas nivel 3 para sub_dominio=multinacional_transfer_pricing"
}
```

**Fuente 4 — Abducción desde manuales técnicos (Fase B+)**

Los manuales técnicos son RESPUESTAS a preguntas que el autor nunca escribió. La estructura del texto las revela. Un algoritmo de extracción invierte el proceso:

```
INPUT:  Manual técnico (PDF, texto)

PASO 1: Parsear estructura (Haiku, barato)
  Detectar patrones:
  - Condicional ("Si X, entonces Y") → "¿Qué condiciones determinan qué acción?"
  - Secuencial ("Primero A, luego B") → "¿Qué orden es crítico y por qué?"
  - Advertencia ("No hacer X porque Y") → "¿Qué falla y qué lo causa?"
  - Excepción ("En general A, excepto B") → "¿Qué rompe la regla?"
  - Clasificación ("Hay 3 tipos") → "¿Qué criterio separa unos de otros?"

PASO 2: Invertir cada afirmación (Opus)
  - ¿Qué pregunta produjo esta afirmación?
  - ¿Qué tuvo que preguntarse el autor para llegar a esto?
  - ¿Qué pregunta falta — qué no preguntó que debería haber preguntado?

PASO 3: Clasificar preguntas extraídas
  - ¿A qué inteligencia pertenece? (router)
  - ¿A qué tipo de pensamiento? (T01-T17)
  - ¿A qué nivel de profundidad? (base/profunda/experta)

PASO 4: Integrar en la Meta-Red
  - Preguntas nuevas → nivel 2-3 de la inteligencia correspondiente
  - Patrones de formulación → mejoran el algoritmo de generación de preguntas

OUTPUT: Meta-Red enriquecida con conocimiento de dominio experto
```

Ejemplo concreto:

```
TEXTO DE MANUAL DE FISIOTERAPIA:
  "Ante una discopatía L4-L5, evaluar primero la movilidad 
   segmentaria antes de aplicar tracción."

PREGUNTAS EXTRAÍDAS:
  → "¿Qué hay que evaluar antes de intervenir?" (T01 Percepción, INT-10)
  → "¿Qué pasa si aplicas tracción sin evaluar?" (T12 Contrafactual, INT-10)
  → "¿Qué secuencia minimiza riesgo?" (INT-16 Constructiva)
  → "¿Qué asume este protocolo que no examina?" (T06 Metacognición)
```

Coste estimado: ~€5-10 por manual procesado (Haiku parsea + Opus invierte).
Un manual de 300 páginas puede producir 200-500 preguntas de nivel 2-3.

Las 4 fuentes completas:

```
Fuente 1: Claude genera          → sintéticas, rápidas, sesgadas
Fuente 2: Expertos revisan       → experiencia directa, caras, lentas
Fuente 3: Uso real               → demanda emergente, requiere volumen
Fuente 4: Manuales técnicos      → conocimiento cristalizado, rico, barato
```

### Impacto en la cartografía

La cartografía (Fase A) se ejecuta con nivel base. Eso es correcto — mide el efecto de cada inteligencia en su forma genérica. Cuando las preguntas profundas existan, se puede re-ejecutar cartografía parcial para medir el delta:

```
¿INT-07 nivel profunda sobre caso dental produce hallazgos 
que INT-07 base no produjo? ¿Cuántos? ¿De qué tipo?
```

Eso te da el ROI de cada nivel de profundidad por inteligencia y dominio.

### Impacto en el motor

Cero cambio estructural. El generador de prompts (código puro) ya selecciona preguntas de la DB. Solo añade un parámetro:

```json
{
  "paso": 1,
  "inteligencia": "INT-07",
  "nivel": "profunda",
  "sub_dominio": "startup_early_stage"
}
```

El compositor decide el nivel como parte del algoritmo, igual que decide qué inteligencias usar y en qué orden.

### Fuentes externas para enriquecer preguntas de nivel 2 y 3

Los modelos ligeros (clasificador, scorer, router) necesitan datos etiquetados con las 18 inteligencias — eso solo lo produce la cartografía + Claude. No hay biblioteca externa que tenga esas etiquetas.

Pero para generar preguntas más profundas de nivel 2 y 3, sí hay fuentes abiertas que sirven como materia prima:

```
INT-07 Financiera:
  ← SSRN, arXiv finance (papers de finanzas corporativas)
  ← IFRS, SEC filings públicos (marcos regulatorios)
  ← Casos Harvard Business School (muchos son open access)

INT-10 Cinestésica:
  ← PubMed open access (biomecánica, fisiología del movimiento)
  ← Protocolos de fisioterapia (bases de datos abiertas)

INT-06 Política:
  ← arXiv, JSTOR open (teoría de juegos aplicada)
  ← Casos de negociación documentados

INT-01 Lógico-Matemática:
  ← arXiv math (papers de optimización, decisión bajo incertidumbre)

INT-12 Narrativa:
  ← Project Gutenberg (patrones narrativos, arquetipos)

CUALQUIER inteligencia:
  ← Wikipedia (analogías, contrafactuales, dominios cruzados)
```

El flujo NO es "el modelo absorbe datos". Es Claude lee esas fuentes y genera preguntas mejores con la Meta-Red como estructura:

```
Fuente abierta (papers, casos, marcos)
     │
     ▼
Claude lee + Meta-Red como estructura
     │
     ▼
Genera preguntas nivel 2-3 informadas por conocimiento real
     │
     ▼
Jesús valida (CR1)
     │
     ▼
DB de preguntas se enriquece
```

Timing: Fase B+ (después de cartografía base, cuando se sepa qué inteligencias necesitan más profundidad).

### Prioridad de implementación

```
AHORA:     Nada — ejecutar cartografía con nivel base
FASE B:    Generar preguntas nivel 2 para las 5-6 inteligencias más usadas
FASE D:    Integrar niveles en el generador de prompts
FASE F:    Generar nivel 3 donde el uso real muestre déficit
           Incorporar expertos donde haya pilotos
```

---

## 17. TRES CAPAS DE PRIMITIVAS — INTELIGENCIA × PENSAMIENTO × MODO

### El salto

El compilador no solo selecciona QUÉ inteligencia usar. Selecciona tres cosas:

```
CAPA 1: INTELIGENCIA  — con qué lente mirar (18 álgebras)
CAPA 2: PENSAMIENTO   — cómo pensar con esa lente (17 tipos)
CAPA 3: MODO          — en qué modo operar (6 modos)
```

Cada capa es independiente y seleccionable. Las tres juntas definen una **configuración cognitiva** completa.

### Capa 1: Las 18 inteligencias (ya definidas)

Selecciona QUÉ objetos percibir y QUÉ operaciones ejecutar.
- INT-07 Financiera percibe flujos, riesgo, apalancamiento
- INT-12 Narrativa percibe arcos, personajes, transformación
- Ya cartografiadas en Fase A

### Capa 2: Los 17 tipos de pensamiento (por activar)

Selecciona CÓMO procesar lo que la inteligencia percibe.

**Internos (T01-T10) — dentro de cada inteligencia:**

| Tipo | Pensamiento | Operación | Pregunta generadora |
|------|-------------|-----------|-------------------|
| T01 | Percepción | iso(S) | ¿Qué forma tiene esto? |
| T02 | Causalidad | B(iso(S)) | ¿Por qué esta forma y no otra? |
| T03 | Abstracción | iso²(S) | ¿Qué se repite sin importar contenido? |
| T04 | Síntesis | ∫(isos) | ¿Qué emerge al ver todo junto? |
| T05 | Discernimiento | A−B | ¿Qué es único de cada mirada? |
| T06 | Metacognición | crítico(X) | ¿Qué no puede ver todo lo anterior? |
| T07 | Consciencia epistemológica | iso(M) | ¿Qué forma tiene mi propia explicación? |
| T08 | Auto-diagnóstico | B(iso(M)) | ¿Por qué pienso así y no de otra forma? |
| T09 | Convergencia | ∫(M₁\|M₂) | ¿Qué comparten todas mis explicaciones? |
| T10 | Dialéctica | A→B→C→A' | ¿Qué veo después de que otros transformaron mi mirada? |

**Laterales (T11-T17) — cruzan el perímetro:**

| Tipo | Pensamiento | Operación | Pregunta generadora |
|------|-------------|-----------|-------------------|
| T11 | Analogía | ≅ | ¿Esto se parece a algo de otro dominio? |
| T12 | Contrafactual | Δ | ¿Qué pasa si quito la pieza más importante? |
| T13 | Abducción | ← | ¿Qué tipo de caso produce esta forma? |
| T14 | Provocación | ⊕ | ¿Y si hago exactamente lo opuesto? |
| T15 | Reencuadre | iso_X | ¿Qué vería aquí una lente que no pertenece? |
| T16 | Destrucción creativa | abandonar | ¿Y si el marco entero es incorrecto? |
| T17 | Creación | generar | ¿Qué necesita existir que no existe? |

**Cómo funciona en el compilador:**

Hoy, cuando el motor ejecuta INT-07 Financiera, ejecuta todas las preguntas secuencialmente. Pero no todos los casos necesitan todos los tipos de pensamiento. El compilador puede especificar:

```json
{
  "paso": 1,
  "inteligencia": "INT-07",
  "pensamiento": ["T01", "T02", "T05", "T12"],
  "nivel": "profunda"
}
```

Esto dice: ejecuta Financiera pero solo percepción (¿qué forma tiene?), causalidad (¿por qué?), discernimiento (¿qué es único?) y contrafactual (¿qué pasa si quitas X?). No hagas síntesis, no hagas metacognición — eso lo hará la siguiente inteligencia en el pipeline.

**El valor:** menos preguntas, más precisas, menos coste, menos ruido. En vez de 50 preguntas genéricas, 15 preguntas quirúrgicas.

### Capa 3: Los 6 modos de operación (por activar)

Selecciona EN QUÉ MODO opera la inteligencia.

| Modo | Descripción | Cuándo |
|------|-------------|--------|
| ANALIZAR | Descomponer, demostrar, medir | Input = datos para diagnosticar |
| PERCIBIR | Ver patrones, detectar forma | Input = situación compleja |
| MOVER | Actuar, posicionar, construir | Input = decisión pendiente |
| SENTIR | Empatizar, intuir, habitar | Input = personas involucradas |
| GENERAR | Crear, imaginar, proyectar | Input = necesidad de contenido/opciones |
| ENMARCAR | Nombrar, negociar, dar sentido | Input = narrativa o comunicación |

**No todas las inteligencias operan en todos los modos.** La Tabla Periódica ya mapea esto:

```
INT-07 Financiera:  ANALIZAR (natural), MOVER (posible), GENERAR (forzado)
INT-12 Narrativa:   GENERAR (natural), ENMARCAR (natural), ANALIZAR (posible)
INT-18 Contemplativa: SENTIR (natural), PERCIBIR (natural), ANALIZAR (contra-natura)
```

El compilador selecciona el modo según el tipo de petición:

```json
{
  "paso": 1,
  "inteligencia": "INT-07",
  "pensamiento": ["T01", "T02", "T12"],
  "modo": "ANALIZAR",
  "nivel": "profunda"
}

{
  "paso": 2,
  "inteligencia": "INT-09",
  "pensamiento": ["T01", "T14", "T17"],
  "modo": "GENERAR",
  "nivel": "base"
}
```

### Espacio combinatorio

```
ANTES (solo inteligencias):
  18 inteligencias → 18 primitivas
  
AHORA (3 capas):
  18 inteligencias × 17 pensamientos × 6 modos = 1.836 configuraciones/paso
  
ACOTADO POR:
  - No todas las combinaciones son válidas (INT×modo tiene restricciones)
  - Saturación: más de 4-5 tipos de pensamiento por paso no añade valor
  - Diferencial: muchas combinaciones son redundantes
  
ESPACIO ÚTIL ESTIMADO:
  18 × ~5 pensamientos relevantes × ~2 modos naturales = ~180 configuraciones/paso
  Sigue siendo 10x más expresivo que solo inteligencias
```

### Profundidad progresiva en pensamiento y modos

Igual que las inteligencias tienen 3 niveles de preguntas, los tipos de pensamiento y modos pueden profundizarse:

```
T12 CONTRAFACTUAL — NIVEL BASE:
  "¿Qué pasaría si quito la pieza más importante?"
  "¿Y si cambio una variable clave por su opuesta?"
  "¿La forma sobrevive al cambio o colapsa?"

T12 CONTRAFACTUAL — NIVEL PROFUNDO:
  "¿Qué pasaría si elimino la restricción que todos dan por inamovible?"
  "¿Si invierto la cadena causal — el efecto causa la causa?"
  "¿Hay un contrafactual que nadie propone porque ataca una creencia compartida?"
  "¿Qué contrafactual haría innecesario todo el análisis anterior?"
  "¿Si este sistema nunca hubiera existido y empezaras de cero hoy, lo construirías así?"

T12 CONTRAFACTUAL — NIVEL EXPERTO:
  "¿Cuáles son los 3 supuestos más profundos que este sistema necesita para existir?"
  "¿Qué pasaría si cada uno fuera falso — por separado y los 3 a la vez?"
  "¿Hay un contrafactual que destruye la pregunta misma — que muestra que 
   la pregunta asume algo que no debería asumir?"
  "¿Qué versión de este sistema sobrevive a TODOS los contrafactuales anteriores?"
```

### Impacto en la cartografía

La Fase A actual cartografía inteligencias. Para cartografiar pensamiento y modos haría falta:

**Fase A ampliada (opcional, post-Fase D):**
- Ejecutar los 10 tipos de pensamiento internos sobre 1 caso × 3 inteligencias
- Medir: ¿T02 Causalidad produce hallazgos diferentes que T03 Abstracción sobre el mismo output de INT-07?
- Medir: ¿T12 Contrafactual aplicado a INT-05 ve cosas que T12 aplicado a INT-07 no puede?

Esto no bloquea. El motor v1 funciona con inteligencias solas. Pensamiento y modos se añaden como capas de refinamiento cuando la base esté validada.

### Impacto en el motor

El generador de prompts (código puro) necesita:

```
ANTES:
  seleccionar(inteligencia, nivel) → preguntas

AHORA:
  seleccionar(inteligencia, pensamiento[], modo, nivel) → preguntas
```

Es una query más específica a la DB, no un cambio arquitectural. El compositor genera un JSON más rico, el generador hace un filtro más fino, el ejecutor recibe prompts más cortos y precisos.

### Prioridad de implementación

```
FASE A:    Cartografiar inteligencias (nivel base) ← AHORA
FASE D:    Motor v1 con selección de inteligencias
FASE D+:   Añadir selección de pensamiento (T01-T17) al compositor
FASE E:    Añadir selección de modo al compositor
FASE F+:   Cartografiar pensamiento × inteligencia si el uso lo demanda
           Profundizar preguntas de pensamiento y modos
           Añadir nuevos tipos de pensamiento si se descubren
```

### Nuevos tipos de pensamiento y modos

La Meta-Red actual tiene 17 tipos y 6 modos. Pero son extensibles:

```
CÓMO SE DESCUBRE UN NUEVO TIPO DE PENSAMIENTO:
  1. El motor ejecuta y el scorer detecta déficit
  2. El déficit no se resuelve con más profundidad ni más inteligencias
  3. El diagnóstico revela: "falta una FORMA de pensar, no una lente"
  4. Se diseña el nuevo tipo: operación algebraica + preguntas + cuándo aplica
  5. Se cartografía sobre 3 casos
  6. Se añade a la DB

EJEMPLO POTENCIAL:
  T18 — RECURSIÓN TEMPORAL: ¿Qué pasaría si aplico la decisión de hoy 
  a la versión de mí mismo de hace 5 años? ¿Y a la de dentro de 5?
  ¿La decisión envejece bien o caduca?
  
  T19 — PENSAMIENTO INVERSO: En vez de resolver el problema,
  ¿cómo lo empeoraría al máximo? ¿Qué me dice eso sobre qué mantener?
  
  T20 — ESCALA FRACTAL: ¿Este patrón se repite a nivel micro (día), 
  meso (trimestre) y macro (década)? ¿A qué escala es más peligroso?
```

---

## 18. FILTRO DE RELEVANCIA — PRIORIZACIÓN DE GAPS

### El problema

Las primitivas del Motor v3.3 generan gaps (distancias id↔ir, huecos activos, conexiones ausentes). En casos ricos, producen 15-25 gaps. El sintetizador los recibe todos y hace lo que puede, no lo que debe. No hay criterio de priorización — todo pesa igual.

### La solución

Un filtro entre primitivas y sintetizador que ordena los gaps por impacto y pasa solo los top 3-5 al siguiente paso.

```
7 primitivas → 15-25 gaps
       │
       ▼
  FILTRO DE RELEVANCIA
       │
       ▼
  TOP 3-5 gaps priorizados → sintetizador
```

### 5 criterios de priorización

| # | Criterio | Peso | Qué mide | Fuente |
|---|----------|------|----------|--------|
| 1 | Magnitud gap id↔ir | 0.30 | Cuánto diverge lo declarado de lo real | C5 (calculadora) |
| 2 | Invisibilidad | 0.25 | ¿Opera con potencia PORQUE no se nombra? | H2 (sintetizador) |
| 3 | Conectividad | 0.20 | ¿Resolver este gap resuelve otros en cascada? | C3 (relaciones) |
| 4 | Relevancia al input | 0.15 | ¿Toca la pregunta implícita del usuario? | Router + embeddings |
| 5 | Accionabilidad | 0.10 | ¿Genera pregunta que el usuario puede responder? | Clasificador simple |

### Implementación

**v1 — Código puro ($0, <100ms):**

```python
def priorizar_gaps(gaps, coordenadas, pregunta_implicita):
    max_conect = max(g.conectividad for g in gaps) or 1
    for gap in gaps:
        gap.score = (
            0.30 * gap.magnitud_id_ir +
            0.25 * (1.0 if gap.es_invisible else 0.0) +
            0.20 * gap.conectividad / max_conect +
            0.15 * relevancia_coseno(gap.texto, pregunta_implicita) +
            0.10 * gap.accionabilidad
        )
    return sorted(gaps, key=lambda g: g.score, reverse=True)[:5]
```

Determinista, debuggeable, sin coste. Los pesos son configurables y se afinan con datos reales de Fase F.

**Fallback — Haiku (~$0.01):**

Cuando el scoring por código no tiene suficiente señal (gaps sin C5 numérico, input muy ambiguo), un call a Haiku recibe los 15-25 gaps + la pregunta implícita y devuelve top-5 con justificación.

### Dónde encaja en el pipeline

```
MOTOR v3.3 ACTUAL:
  primitivas → sintetizador → M2 → M3

MOTOR v3.3 CON FILTRO:
  primitivas → FILTRO → sintetizador → M2 → M3

MOTOR SEMÁNTICO:
  primitivas → FILTRO → compilador selecciona inteligencias
                       → generador de prompts
                       → ejecución
```

El filtro sirve para ambos motores. En el v3.3, reduce ruido antes del sintetizador. En el motor semántico, los gaps priorizados informan al router sobre qué inteligencias activar — un gap financiero activa INT-07, un gap relacional activa INT-08.

### Doble función del filtro

```
FUNCIÓN 1 — PRIORIZAR PARA EL MOTOR:
  De 20 gaps → top 5 para análisis profundo

FUNCIÓN 2 — GENERAR PREGUNTAS PARA EL USUARIO:
  De los top 5 → ¿cuáles necesitan datos que el usuario no ha dado?
  → Convertir esos gaps en preguntas precisas al usuario
  → El usuario responde → el motor re-ejecuta con más información
  
  Esto resuelve el "parser de requisitos":
  no adivina qué necesita — pregunta lo que le falta
```

### Prioridad de implementación

```
IMPLEMENTABLE YA:  Código puro en Motor v3.3 (entre primitivas y sintetizador)
FASE D:            Integrado en Motor semántico como Capa 1.5
FASE F:            Pesos afinados con datos reales de uso
```

---

## 19. PROTOCOLO DE DOCUMENTACIÓN Y CHECKLIST

### Principio

Cada cosa que se implementa genera dos outputs obligatorios: una marca en la checklist y un documento de registro. Sin esto, el siguiente que toque el sistema (incluido tú dentro de 3 meses) empieza ciego.

### Checklist maestra

Archivo: `CHECKLIST_MOTOR_SEMANTICO.md`
Se actualiza CADA VEZ que se completa algo. Vive en el proyecto y en el repo.

```markdown
# CHECKLIST MOTOR SEMÁNTICO OMNI-MIND

## FASE A — CARTOGRAFÍA
- [ ] A1: INT-01 Lógico-Matemática × 3 casos
- [ ] A1: INT-02 Computacional × 3 casos
- [ ] A1: INT-03 Estructural × 3 casos
- [ ] A1: INT-04 Ecológica × 3 casos
- [ ] A1: INT-05 Estratégica × 3 casos
- [ ] A1: INT-06 Política × 3 casos
- [ ] A1: INT-07 Financiera × 3 casos
- [ ] A1: INT-08 Social × 3 casos
- [ ] A1: INT-09 Lingüística × 3 casos
- [ ] A1: INT-10 Cinestésica × 3 casos
- [ ] A1: INT-11 Espacial × 3 casos
- [ ] A1: INT-12 Narrativa × 3 casos
- [ ] A1: INT-13 Prospectiva × 3 casos
- [ ] A1: INT-14 Divergente × 3 casos
- [ ] A1: INT-15 Estética × 3 casos
- [ ] A1: INT-16 Constructiva × 3 casos
- [ ] A1: INT-17 Existencial × 3 casos
- [ ] A1: INT-18 Contemplativa × 3 casos
- [ ] A1: RESULTADOS_FASE1.md compilado
- [ ] A1: RESULTADOS_FASE1_JSON.md compilado
- [ ] A2: Matriz diferenciales Caso 1
- [ ] A2: Matriz diferenciales Caso 2
- [ ] A2: Matriz diferenciales Caso 3
- [ ] A2: TOP 10 pares complementarios identificados
- [ ] A3: Fusiones ejecutadas (listar cuáles)
- [ ] A3: Composiciones ejecutadas (listar cuáles)
- [ ] A4: Propiedades P01-P11 testadas
- [ ] A: FASE A CERRADA — criterios cumplidos

## FASE B — DATOS SINTÉTICOS
- [ ] B1: Casos por dominio generados (200+)
- [ ] B2: Peticiones por inteligencia generadas (540+)
- [ ] B3: Datos de composición generados (300+)
- [ ] B4: Datos de calidad para scorer (180+)
- [ ] B: Validación humana 10% completada
- [ ] B: FASE B CERRADA

## FASE C — MODELOS LIGEROS
- [ ] C1: Router embeddings entrenado (accuracy >80%)
- [ ] C2: Clasificador dominio→inteligencias (F1 >0.75)
- [ ] C3: Compositor por grafo funcional
- [ ] C4: Scorer de calidad (correlación >0.7)
- [ ] C: FASE C CERRADA

## FASE D — MOTOR v1
- [ ] D: Pipeline end-to-end en fly.io
- [ ] D: Filtro de relevancia implementado
- [ ] D: Modo ANÁLISIS funcional
- [ ] D: Modo GENERACIÓN funcional
- [ ] D: Modo CONVERSACIÓN funcional
- [ ] D: Modo CONFRONTACIÓN funcional
- [ ] D: API documentada
- [ ] D: Selección de pensamiento (T01-T17) integrada
- [ ] D: Selección de modo integrada
- [ ] D: FASE D CERRADA

## FASE E — CHAT / EXOCORTEX
- [ ] E: Chat funcional vía web
- [ ] E: Estado persistente entre sesiones
- [ ] E: Capa profunda operativa
- [ ] E: Generación de contenido con inteligencias
- [ ] E: FASE E CERRADA

## FASE F — PILOTOS
- [ ] F: Piloto Authentic Pilates activo
- [ ] F: Piloto clínica fisio activo
- [ ] F: Loop retroalimentación funcionando
- [ ] F: Primera re-entrenamiento de modelos con datos reales
```

### Documento de registro por implementación

Cada vez que se implementa algo (un agente, un modelo, una función, un fix), se genera:

Archivo: `REGISTRO_[FECHA]_[QUE].md`

```markdown
# REGISTRO DE IMPLEMENTACIÓN

**Fecha:** YYYY-MM-DD
**Qué se hizo:** [descripción concreta]
**Fase:** [A/B/C/D/E/F]
**Componente:** [qué parte del motor]

## CONTEXTO
¿Por qué se hizo? ¿Qué problema resolvía?

## QUÉ SE IMPLEMENTÓ
Descripción técnica precisa. Sin ambigüedad.
- Archivos creados/modificados
- Dependencias añadidas
- Configuración necesaria

## CÓDIGO RELEVANTE
Si se creó o modificó código, incluir lo esencial.
No todo el código — solo lo que otro necesitaría para entender qué hace.

## TESTS REALIZADOS
- Qué se testó
- Con qué input
- Qué output produjo
- ¿Pasó? ¿Falló? ¿Con qué resultado?

## RESULTADO
¿Funcionó como se esperaba?
¿Hubo sorpresas?
¿Métricas (coste, latencia, accuracy, score)?

## DECISIONES TOMADAS
¿Se eligió A sobre B? ¿Por qué?
Esto es crítico para no repetir debates.

## PENDIENTE
¿Qué queda por hacer relacionado con esto?
¿Hay bugs conocidos?
¿Hay limitaciones aceptadas?

## RELACIÓN CON OTROS COMPONENTES
¿Esto afecta a algo más?
¿Algo depende de esto?
```

### Índice de registros

Archivo: `INDICE_REGISTROS.md`
Se actualiza cada vez que se añade un registro.

```markdown
# ÍNDICE DE REGISTROS DE IMPLEMENTACIÓN

| Fecha | Registro | Fase | Componente | Estado |
|-------|----------|------|-----------|--------|
| 2026-03-10 | REGISTRO_2026-03-10_CART_INT10.md | A | Cartografía INT-10 | OK |
| 2026-03-10 | REGISTRO_2026-03-10_CART_INT11.md | A | Cartografía INT-11 | OK |
| ... | ... | ... | ... | ... |
```

### Reglas

1. **No se cierra un chat de trabajo sin actualizar la checklist.** Si hiciste algo, márcalo.

2. **No se cierra una implementación sin su registro.** Si no hay registro, no existe.

3. **El registro se escribe CUANDO se hace, no después.** El contexto fresco es 10x más preciso que el recordado.

4. **Los registros son inmutables.** Si algo cambia después, se crea un nuevo registro que referencia al anterior. No se editan los viejos.

5. **La checklist es la fuente de verdad del progreso.** Si alguien pregunta "¿dónde estamos?", la checklist responde sin necesidad de leer nada más.

6. **Los registros son la fuente de verdad del contexto.** Si alguien pregunta "¿por qué se hizo así?", el registro responde sin necesidad de preguntar a nadie.

### Dónde viven

```
PROYECTO CLAUDE "CARTOGRAFÍA META-RED":
  CHECKLIST_MOTOR_SEMANTICO.md        ← estado actual
  INDICE_REGISTROS.md                 ← índice de todo lo hecho

REGISTROS (por fase):
  registros/
    fase_a/
      REGISTRO_2026-03-10_CART_INT10.md
      REGISTRO_2026-03-10_CART_INT11.md
      ...
    fase_b/
      ...
    fase_c/
      ...
```

---

## 20. REACTOR SEMÁNTICO — MOTOR DE GENERACIÓN DE DATOS

### El problema del mercado

Los LLMs convergen porque se entrenan con los mismos datos públicos (web, libros, papers, código). La diferenciación se reduce. Los que tienen ventaja temporal la tienen por datos privados (gubernamentales, médicos, corporativos) — pero son estáticos, finitos, se agotan.

### La oportunidad

La Meta-Red no consume datos existentes. **Genera datos que no existen en ningún corpus del mundo.** Cada ejecución de una inteligencia sobre un caso produce un output que ningún dataset contiene — porque emerge de la estructura de las preguntas, no del contenido previo.

### El reactor

```
META-RED (estructura de preguntas)
     │
     ▼ se ejecutan sobre cualquier input
DATOS SEMÁNTICOS NUEVOS (no existen en ningún corpus)
     │
     ▼ entrenan
MODELOS PROPIOS (routing, scoring, composición)
     │
     ▼ ejecutan mejor → producen outputs más profundos
OUTPUTS MÁS PROFUNDOS
     │
     ▼ analizados por la Meta-Red
NUEVAS PREGUNTAS (nivel 2, 3, tipos nuevos de pensamiento)
     │
     ▼ generan
DATOS AÚN MÁS NUEVOS (que el ciclo anterior no podía producir)
     │
     └──→ ciclo que se amplifica con cada vuelta
```

### Por qué es un reactor y no un loop

Un loop repite. Un reactor amplifica. La diferencia:

```
LOOP:    mismos datos → mismo modelo → mismos datos
         (rendimientos decrecientes, converge, se agota)

REACTOR: datos nivel 1 → modelo v1 → genera preguntas nivel 2
         → datos nivel 2 → modelo v2 → genera preguntas nivel 3
         → datos nivel 3 → ...
         (cada ciclo produce datos de un TIPO que el anterior no podía)
```

Ronda 1: datos de inteligencias individuales sobre casos.
Ronda 2: datos de combinaciones y diferenciales entre inteligencias.
Ronda 3: datos de meta-patrones entre combinaciones.
Ronda 4: datos de predicción de qué configuración cognitiva óptima para qué tipo de input.
Ronda N: datos de tipos de pensamiento que no existían en Ronda 1 porque se descubrieron en Ronda N-1.

Cada nivel es genuinamente nuevo. No es más de lo mismo con más volumen.

### El moat

```
COMPONENTE              COPIABLE    SIN LOS DEMÁS VALE
────────────────────────────────────────────────────────
Meta-Red (preguntas)    Sí          Poco (sin datos de ejecución)
Datos de ejecución      No          Poco (sin modelos entrenados)
Modelos entrenados      No          Poco (sin reactor que genere más datos)
Reactor completo        No          TODO — se amplifica solo
```

Aunque alguien copie la Meta-Red (es texto público), no tiene:
- Los datos de ejecución → no puede entrenar modelos de routing
- Los modelos de routing → no puede compilar algoritmos óptimos
- Los algoritmos óptimos → no genera datos de calidad
- Los datos de calidad → no puede mejorar el reactor

El moat no es ninguna pieza. Es el sistema completo funcionando y amplificándose.

### Implicación para el negocio

```
CADA CLIENTE QUE USA EL MOTOR:
  → Genera datos de ejecución en su dominio
  → Esos datos entrenan modelos mejores para ese dominio
  → El motor mejora para todos los clientes de ese dominio
  → Más clientes usan el motor
  → Más datos → mejor motor → más clientes
  
  Efecto de red en los DATOS, no en los usuarios.
```

Un departamento financiero que usa el motor genera datos que mejoran INT-07 Financiera para TODOS los departamentos financieros. Un estudio de Pilates que usa el motor genera datos que mejoran INT-10 Cinestésica para TODOS los negocios de movimiento corporal. Cada vertical alimenta su propia inteligencia.

### Implicación para la arquitectura

El reactor no es una fase nueva. Es la propiedad emergente de las fases A→F funcionando en ciclo:

```
A (cartografía) genera datos base
B (sintéticos) amplifica datos
C (entrena) produce modelos
D (motor) ejecuta con modelos
E (chat) genera ejecuciones reales
F (pilotos) genera datos reales
→ datos reales mejoran B → mejoran C → mejoran D → mejoran E → más datos F
```

El sistema ya está diseñado como reactor. Solo faltaba nombrarlo.

---

## 21. META-MOTOR — RAZONAMIENTO SOBRE PREGUNTAS

### El salto de nivel lógico

Hoy los 17 tipos de razonamiento operan sobre datos y outputs (respuestas). Pero pueden operar sobre las PREGUNTAS MISMAS para generar preguntas que ningún humano formularía.

```
NIVEL 1 (actual):   Razonamiento(datos)     → hallazgos
NIVEL 2 (nuevo):    Razonamiento(preguntas) → preguntas mejores
```

### Los 17 tipos de pensamiento aplicados a preguntas

**INTERNOS:**

```
T01 PERCEPCIÓN sobre preguntas:
  "¿Qué forma tiene este set de preguntas?"
  "¿Hay preguntas que se parecen estructuralmente aunque hablen de cosas diferentes?"
  "¿Qué zona del caso NO tiene ninguna pregunta apuntándola?"

T02 CAUSALIDAD sobre preguntas:
  "¿Qué pregunta CAUSA que aparezcan estas otras preguntas?"
  "¿Hay una pregunta raíz de la que todas las demás derivan?"
  "¿Si respondo esta pregunta primero, las demás cambian?"

T03 ABSTRACCIÓN sobre preguntas:
  "¿Qué patrón comparten las preguntas que producen hallazgos profundos?"
  "Si quito el dominio, ¿qué estructura de pregunta queda?"
  "¿Ese patrón se puede aplicar a preguntas de otra inteligencia?"

T04 SÍNTESIS sobre preguntas:
  "¿Qué pregunta emerge al cruzar estas dos que ninguna contiene sola?"
  "¿Hay una mega-pregunta que fusiona 3 preguntas parciales?"
  "¿La intersección de estas preguntas produce una que es más potente que todas?"

T05 DISCERNIMIENTO sobre preguntas:
  "¿Qué puede preguntar esta pregunta que aquella NO PUEDE preguntar?"
  "¿Son preguntas complementarias o redundantes?"
  "¿Si elimino una, pierdo algo irreemplazable?"

T06 METACOGNICIÓN sobre preguntas:
  "¿Qué no puede preguntar todo este set de preguntas?"
  "¿Qué pregunta falta que ninguna de las existentes puede sustituir?"
  "¿El set de preguntas asume algo que no ha examinado?"

T07 CONSCIENCIA EPISTEMOLÓGICA sobre preguntas:
  "¿Qué forma tiene mi manera de preguntar?"
  "¿Mis preguntas repiten un patrón que limita lo que puedo descubrir?"
  "¿Hay un tipo de pregunta que nunca hago — cuál?"

T08 AUTO-DIAGNÓSTICO sobre preguntas:
  "¿Por qué mis preguntas tienen esta forma y no otra?"
  "¿Qué en mi herramienta produce este tipo de preguntas?"
  "¿Un sistema con otras herramientas haría preguntas diferentes — cuáles?"

T09 CONVERGENCIA sobre preguntas:
  "¿Qué comparten todas las preguntas que producen buenos hallazgos?"
  "¿Hay un meta-patrón que define la pregunta óptima?"
  "¿Si tuviera que hacer UNA sola pregunta, cuál sería?"

T10 DIALÉCTICA sobre preguntas:
  "¿Cómo cambia mi pregunta original después de ver las respuestas?"
  "¿La respuesta revela que la pregunta era incorrecta?"
  "¿Cuál es la pregunta que debería haber hecho desde el principio?"
```

**LATERALES:**

```
T11 ANALOGÍA sobre preguntas:
  "Esta pregunta funciona en INT-07 Financiera.
   ¿Cuál es su equivalente estructural en INT-10 Cinestésica?"
  "¿Hay una pregunta en otro dominio que resuelve lo que esta no puede?"
  → Transferencia de preguntas entre dominios por estructura

T12 CONTRAFACTUAL sobre preguntas:
  "Si elimino esta pregunta del set, ¿qué hallazgos desaparecen?"
  "Si invierto esta pregunta, ¿qué pregunta emerge?"
  "¿Cuál es la anti-pregunta — la que destruiría todo lo que esta construye?"
  → Mide el valor de cada pregunta y descubre preguntas inversas

T13 ABDUCCIÓN sobre preguntas:
  "Este hallazgo profundo apareció. ¿Qué pregunta lo produjo?"
  "¿Qué tipo de pregunta produce consistentemente este tipo de hallazgo?"
  "¿Puedo reverse-engineer la pregunta óptima desde el output deseado?"
  → Genera preguntas desde los resultados, no desde la teoría

T14 PROVOCACIÓN sobre preguntas:
  "¿Y si pregunto exactamente lo opuesto de lo que 'debería' preguntar?"
  "¿Qué pregunta haría un niño? ¿Un loco? ¿Alguien del siglo XV?"
  "¿Qué pregunta es tabú en este dominio — y por qué?"
  → Rompe el marco de lo preguntable

T15 REENCUADRE sobre preguntas:
  "¿Cómo formularía esta pregunta un músico? ¿Un cirujano? ¿Un poeta?"
  "¿Si cambio el marco de la pregunta, cambia lo que puede revelar?"
  "¿Hay una formulación de esta pregunta que la hace 10x más potente?"
  → Optimiza la formulación, no solo el contenido

T16 DESTRUCCIÓN CREATIVA sobre preguntas:
  "¿Y si todo este set de preguntas es incorrecto?"
  "¿Y si preguntar es precisamente lo que NO necesita este caso?"
  "¿Hay algo más directo que una pregunta — una acción, un silencio?"
  → Cuestiona si preguntar es la herramienta correcta

T17 CREACIÓN sobre preguntas:
  "¿Qué pregunta necesita existir que no existe en ninguna inteligencia?"
  "¿Puedo diseñar una pregunta nueva que combine 2 tipos de pensamiento?"
  "¿Qué pregunta crearía una inteligencia #19?"
  → Genera preguntas genuinamente nuevas, no variaciones
```

### Qué produce el meta-motor

```
INPUT:  Set existente de preguntas de la Meta-Red
OUTPUT: 
  1. Preguntas nuevas que no existían
  2. Preguntas optimizadas (mejor formulación del mismo intent)
  3. Preguntas eliminadas (redundantes detectadas por T05)
  4. Preguntas raíz (T02 causal — las generadoras de cascada)
  5. Preguntas transferidas (T11 analogía — de un dominio a otro)
  6. Preguntas inversas (T12 contrafactual — las anti-preguntas)
  7. Meta-patrones de preguntas efectivas (T03 abstracción)
```

### Impacto en el reactor

```
REACTOR v1 (sección 20):
  Preguntas fijas → datos → modelos → más datos
  Las preguntas no cambian. Los datos crecen.

REACTOR v2 (con meta-motor):
  Preguntas → datos → razonamiento sobre preguntas
  → preguntas mejores → datos mejores → razonamiento
  → preguntas aún mejores → ...
  Las preguntas TAMBIÉN evolucionan. Doble amplificación.
```

El reactor v1 es fisión — parte átomos (datos) existentes.
El reactor v2 es fusión — crea átomos (preguntas) nuevos.

### Implementación

```
FASE A:     No aplica — cartografiar con preguntas base
FASE D+:    Meta-motor como módulo opcional del pipeline
            Ejecutar T13 (abducción) sobre los mejores outputs de Fase A:
            "¿Qué preguntas produjeron estos hallazgos?"
FASE F:     Meta-motor en modo automático:
            Cada semana, razonar sobre el set de preguntas que mejor 
            performaron → generar candidatas → validar → integrar
FASE F+:    Meta-motor como generador continuo de preguntas nivel 2-3
            Reemplaza parcialmente la generación manual de Fuentes 1 y 2
```

Coste: ~€0.10-0.20 por ciclo de meta-razonamiento (1 call Opus). Un ciclo semanal = ~€1/mes.

---

## 22. PRINCIPIOS DE DISEÑO

1. **La inteligencia está en las preguntas, no en el modelo.** El LLM es interchangeable. La Meta-Red es permanente.

2. **Cada modelo hace lo que mejor sabe.** LLMs para generar y sintetizar. Embeddings para buscar. Grafos para optimizar. Código para calcular.

3. **El motor no tiene opinión.** Selecciona inteligencias, ejecuta preguntas, devuelve lo que emerge. No prescribe.

4. **Menos es más.** 4 inteligencias bien seleccionadas > 18 inteligencias mal combinadas. El diferencial es la herramienta de poda.

5. **Retroalimentación continua.** Cada ejecución es un datapoint. El sistema mejora con cada uso.

6. **Validación antes de expansión.** No añadir inteligencias, dominios ni features hasta que lo existente demuestre valor con datos reales.

7. **Profundidad progresiva.** Base para todo. Profunda donde el dominio lo requiere. Experta donde el uso real demuestra déficit. Nunca al revés.

8. **Tres capas de primitivas.** Inteligencia × Pensamiento × Modo. El compilador selecciona las tres. La expresividad es multiplicativa, no aditiva.

9. **No adivinar, preguntar.** Cuando el input es ambiguo, el motor genera las preguntas que le faltan. Las primitivas ya saben detectar qué falta.

10. **Si no hay registro, no existe.** Cada implementación genera checklist + documento de registro. El contexto fresco es irremplazable.

11. **Las preguntas son el combustible, no los datos.** Los datos se agotan. Las preguntas generan datos nuevos infinitamente.

12. **Todo texto experto es preguntas comprimidas.** La abducción las recupera. Cada manual procesado enriquece la Meta-Red con conocimiento de dominio que tardó décadas en cristalizar.

13. **Las preguntas se pueden razonar.** Los mismos tipos de pensamiento que operan sobre datos operan sobre preguntas. El meta-motor no solo ejecuta preguntas — las evoluciona.

---

**FIN DISEÑO MOTOR SEMÁNTICO OMNI-MIND — CR0**
