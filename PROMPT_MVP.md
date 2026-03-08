# PROMPT — MOTOR SEMÁNTICO v1 MVP

**Objetivo:** Pipeline end-to-end funcional en fly.io. Acepta input en lenguaje natural, devuelve output estructurado.
**Infra:** fly.io (app Node.js/Python) + fly.io Postgres (pgvector habilitado)
**NO hay:** Supabase, Edge Functions, Deno. Todo corre en fly.io.
**Estilo:** Implementar con rigor. Sin teoría. Sin filler. Código funcional.

---

## 1. QUÉ ES EL MOTOR

Un motor que recibe cualquier input en lenguaje natural y genera automáticamente el algoritmo óptimo de inteligencias para procesarlo. No tiene programas fijos — compila un programa nuevo para cada petición desde las primitivas de la Meta-Red (18 inteligencias, cada una es una red de preguntas).

```
INPUT:  "Mi socio quiere vender su parte y no sé si puedo comprársela"
MOTOR:  Router → [INT-07 Financiera, INT-06 Política, INT-08 Social, INT-05 Estratégica]
        Compositor → INT-07→INT-06 → ∫(INT-08|INT-05)
        Ejecutor → ejecuta preguntas de cada inteligencia sobre el input
        Integrador → síntesis final
OUTPUT: Diagnóstico multi-inteligencia con hallazgos, firma combinada, puntos ciegos
```

---

## 2. ARQUITECTURA — 6 CAPAS DEL PIPELINE

```
INPUT (texto del usuario)
         │
         ▼
┌─────────────────────────┐
│  CAPA 1: ROUTING        │  ~2-5s | ~$0.02-0.05
│  Sonnet selecciona      │
│  → Top-K inteligencias  │
│  (MVP: LLM, no embeddings)│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 2: COMPOSICIÓN    │  ~100ms | $0
│  Grafo en memoria       │
│  → Algoritmo óptimo     │
│  → Operaciones + orden  │
│  (código puro, NetworkX)│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 3: GENERACIÓN     │  ~50ms | $0
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
│  (Opus solo si frontera)│
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 5: EVALUACIÓN     │  ~50ms | $0
│  Scorer heurístico      │
│  (MVP: reglas, no ML)   │
│  Si score < umbral:     │
│    → relanzar con más   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CAPA 6: INTEGRACIÓN    │  10-20s | ~$0.10-0.20
│  Sonnet: síntesis final │
│  → Output al usuario    │
│  → Log para telemetría  │
└─────────────────────────┘

TOTAL MVP: ~$0.35-1.00 | ~40-150s
```

---

## 3. DECISIONES MVP (ya cerradas)

| Decisión | Elegido | Razón |
|----------|---------|-------|
| DB | fly.io Postgres + pgvector | Colocalizada con motor, sin dependencias externas |
| Router | Sonnet (LLM) | No hay datos de entrenamiento aún. Embeddings vendrán en v2 con datos reales |
| Compositor | NetworkX en memoria | 18 nodos, 153 aristas. Se carga al arrancar desde tabla de aristas |
| Scorer | Heurístico (reglas) | No hay outputs puntuados aún. ML vendrá en v2 con datos reales |
| Runtime | Node.js o Python (tú decides) | Lo que sea más rápido de implementar |
| LLM API | Anthropic (Haiku/Sonnet) | 4 keys rotativas disponibles |

---

## 4. API DEL MOTOR

```
POST /motor/ejecutar
{
  "input": "texto libre del usuario",
  "contexto": "opcional — contexto previo, dominio, restricciones",
  "config": {
    "presupuesto_max": 1.50,
    "tiempo_max_s": 120,
    "profundidad": "normal|profunda|maxima",
    "modo": "analisis|generacion|conversacion|confrontacion",
    "inteligencias_forzadas": [],
    "inteligencias_excluidas": []
  }
}

RESPONSE:
{
  "algoritmo_usado": {
    "inteligencias": ["INT-07", "INT-05", "INT-06"],
    "operaciones": ["INT-07→INT-06", "∫(INT-08|INT-05)"],
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

### 4 Modos (configuraciones del mismo pipeline)

| Modo | Inteligencias | Profundidad | Latencia objetivo |
|------|---------------|-------------|-------------------|
| análisis | 4-5, máximo diferencial | 2 pasadas | <150s |
| generación | creativas (INT-14, INT-15, INT-09) | 1 pasada | <90s |
| conversación | 2-3, routing rápido | 1 pasada | <60s |
| confrontación | frontera (INT-17, INT-18) | 2 pasadas | <120s |

---

## 5. REGLAS DEL COMPILADOR (derivadas empíricamente de 34 chats de cartografía)

Estas reglas son OBLIGATORIAS. El compositor las respeta siempre.

### Selección (Router)
1. **Núcleo irreducible:** Siempre incluir al menos 1 de {INT-01, INT-02} (cuantitativa) + 1 de {INT-08, INT-17} (humana) + INT-16 (constructiva). Sin este triángulo, el análisis diagnostica sin resolver o resuelve sin diagnosticar.
2. **Máximo diferencial:** Priorizar pares del eje cuantitativo-existencial (INT-01×08, INT-02×17, INT-07×17). Menor valor marginal en pares intra-cluster.
3. **Sweet spot:** 4-5 inteligencias por análisis. Menos de 3 = puntos ciegos críticos. Más de 6 = rendimiento marginal decreciente.

### Orden (Compositor)
4. **Formal primero:** En composiciones, ejecutar la inteligencia más formal/distante primero, la más humana/cercana después.
5. **No reorganizar:** La secuencia lineal (A→B)→C supera a la agrupada A→(B→C). No factorizar composiciones.
6. **Fusiones con cuidado:** El orden de fusión afecta framing. Ejecutar primero la inteligencia más alineada con el perfil del sujeto.

### Profundidad
7. **Loop test siempre:** 2 pasadas por defecto para toda inteligencia en modo análisis/confrontación.
8. **No tercera pasada:** n=3 no justifica coste. Excepto calibración.

### Paralelización
9. **Fusiones paralelizables al ~70%:** Se puede factorizar A→(B|C) como (A→B)|(A→C) perdiendo ~30%. Aceptable para reducir coste si los pares no están en TOP 5 de complementariedad.
10. **Cruce previo no factorizable:** (B|C)→A NO es factorizable. El cruce previo tiene valor irreducible. Siempre ejecutar juntas las inteligencias que alimentan a una tercera.

### Patrones universales
11. **Marco binario universal:** En 3/3 casos, los sujetos presentan falsa dicotomía. La primera acción debería ser INT-14 (ampliar opciones) + INT-01 (filtrar viables).
12. **Conversación pendiente universal:** En 3/3 casos, 16/18 inteligencias identifican una conversación no tenida como acción prioritaria.
13. **Infrautilización antes de expansión:** En 3/3 casos, el sujeto quiere escalar cuando no usa lo que tiene.

---

## 6. LAS 18 INTELIGENCIAS — FIRMAS Y PREGUNTAS

### Catálogo de firmas

| INT | Nombre | Firma | Punto ciego |
|-----|--------|-------|-------------|
| 01 | Lógico-Matemática | Contradicción formal demostrable entre premisas | Lo ambiguo, lo no-axiomatizable |
| 02 | Computacional | Dato trivializador ausente + atajo algorítmico | Lo no-computable, la intuición |
| 03 | Estructural (IAS) | Gap id↔ir + actor invisible con poder | No genera soluciones |
| 04 | Ecológica | Nichos vacíos + capital biológico en depreciación | No ve al individuo |
| 05 | Estratégica | Secuencia obligatoria de movimientos + reversibilidad | Asume competición |
| 06 | Política | Poder como objeto + coaliciones no articuladas | Confunde poder con verdad |
| 07 | Financiera | Asimetría payoffs cuantificada + tasa de descuento invertida | Lo sin precio no existe |
| 08 | Social | Vergüenza no nombrada + lealtad invisible | Sobrepsicologiza |
| 09 | Lingüística | Palabra ausente + acto performativo | Confunde nombrar con resolver |
| 10 | Cinestésica | Tensión-nudo vs tensión-músculo + arritmia de tempos | No verbaliza |
| 11 | Espacial | Punto de compresión + pendiente gravitacional | Lo sin extensión no existe |
| 12 | Narrativa | Roles arquetípicos + narrativa autoconfirmante | Fuerza protagonista |
| 13 | Prospectiva | Trampa de escalamiento sectorial + señales débiles | El cisne negro |
| 14 | Divergente | 20+ opciones donde el sujeto ve 2 | No evalúa |
| 15 | Estética | Isomorfismo solución-problema + tristeza anticipatoria | Lo feo puede ser verdadero |
| 16 | Constructiva | Prototipo con coste, secuencia y fallo seguro | No cuestiona premisas |
| 17 | Existencial | Brecha valores declarados vs vividos + inercia como no-elección | Puede paralizar |
| 18 | Contemplativa | Urgencia inventada + vacío como recurso | Puede desconectar de acción |

### Redes de preguntas completas por inteligencia

Cada inteligencia sigue la misma meta-red de 6 pasos:
```
EXTRAER → CRUZAR → LENTES (L1-L4/L6) → INTEGRAR → ABSTRAER → FRONTERA
```

Lo que cambia es el contenido de las preguntas en cada paso. A continuación, las 18 redes completas.

---

#### INT-01: LÓGICO-MATEMÁTICA

**EXTRAER — formalizar**
- ¿Qué se puede contar? ¿Qué se puede medir?
- ¿Qué magnitudes aparecen con número explícito?
- ¿Qué magnitudes aparecen sin número pero se podrían medir?
- ¿Qué relación tiene cada número con los demás — se suman, se multiplican, se limitan?
- ¿Qué se quiere saber que aún no se sabe?
- ¿Qué se da por hecho sin verificar?

**CRUZAR — estructurar tipo de problema**
- De todas las relaciones, ¿cuántas puedes mover y cuántas están fijadas?
- ¿Mover una variable mejora todo, o mejorar una empeora otra?
- Si empeora otra: ¿hay punto donde ambas sean aceptables, o siempre hay que elegir?
- ¿Los números son continuos o discretos?
- ¿Lo que no se sabe se puede estimar, o es genuinamente incierto?

**LENTES:**
- L1 Álgebra: ¿Cuántas ecuaciones hay y cuántas incógnitas? ¿Alguna es redundante? ¿Alguna contradice a otra?
- L2 Análisis: Si aumentas cada variable un poco, ¿qué pasa? ¿Hay punto donde aumentar empieza a empeorar? ¿Alguna variable tiene efecto desproporcionado?
- L3 Geometría: Si dibujas las opciones como puntos, ¿qué forma tienen? ¿Las opciones buenas están concentradas o dispersas?
- L4 Probabilidad: ¿Qué números son seguros y cuáles estimaciones? ¿Qué pasaría si los estimados se desvían un 20%?
- L5 Optimización: ¿Se puede mejorar todo a la vez? Si hay que elegir, ¿qué importa más — y quién decide eso?
- L6 Lógica: ¿Qué se puede deducir con certeza? ¿Hay combinación de premisas que se contradiga?

**INTEGRAR:** ¿Qué dicen todas las lentes que coincide? ¿Dónde se contradicen? ¿Hay algo que solo aparece al mirar todas juntas?
**ABSTRAER:** ¿Este caso es único o hay una clase de casos que comparten esta estructura? Si quitas nombres y números, ¿qué patrón queda?
**FRONTERA:** ¿Qué asume este análisis que no ha examinado? ¿Hay algo que no se puede expresar como número o ecuación? Si eso fuera lo más importante, ¿qué cambia?

---

#### INT-02: COMPUTACIONAL

**EXTRAER — descomponer**
- ¿Cuáles son las entradas del sistema? ¿Cuáles son las salidas deseadas?
- ¿Qué transformaciones llevan de entrada a salida?
- ¿Hay partes que se pueden resolver independientemente?
- ¿Hay partes que dependen del resultado de otras?
- ¿Qué datos faltan para poder calcular?

**CRUZAR — clasificar complejidad**
- ¿Cuántos pasos tiene la transformación más larga?
- ¿Hay bucles — alguna parte necesita repetirse hasta converger?
- ¿El problema escala — si duplicas el tamaño, el esfuerzo se duplica o se multiplica?
- ¿Se puede dividir en subproblemas en paralelo?

**LENTES:**
- L1 Algorítmica: ¿Existe un procedimiento paso a paso que siempre da la respuesta? ¿Puede fallar?
- L2 Estructuras de datos: ¿Cómo se organizan mejor los datos? ¿La organización afecta la velocidad?
- L3 Concurrencia: ¿Qué partes se pueden hacer al mismo tiempo? ¿Hay recursos compartidos?
- L4 Aproximación: ¿Necesita ser exacto o basta con estimación? ¿Se puede obtener 80% correcto en 10% del tiempo?

**INTEGRAR:** ¿El algoritmo ideal es viable con los datos disponibles? ¿El cuello de botella es velocidad, datos, o definición del problema?
**ABSTRAER:** ¿Es instancia de un problema conocido? ¿Tiene soluciones estándar adaptables?
**FRONTERA:** ¿Lo que necesita resolver es realmente un problema de cómputo? ¿O es un problema humano disfrazado de problema técnico?

---

#### INT-03: ESTRUCTURAL (IAS)

**EXTRAER — mapear coordenadas**
- ¿Qué dice esta persona que es/quiere? (identidad declarada)
- ¿Qué hace realmente? (identidad operativa)
- ¿Dónde divergen el decir y el hacer?
- ¿Quién tiene poder real — no formal, real?
- ¿Qué conexiones faltan entre las piezas?

**CRUZAR — buscar huecos activos**
- ¿Lo que dice que quiere coincide con lo que optimiza?
- ¿Hay alguien que opera con potencia máxima porque no se nombra?
- ¿La desconexión entre piezas sostiene el sistema o lo debilita?
- ¿Hay un circuito que se refuerza — y hacia dónde converge?

**LENTES:**
- L1 Contenedores: ¿Quién contiene a quién? ¿Qué se solapa? ¿Qué falta?
- L2 Circuitos: ¿Qué loops existen? ¿Se amplifican o frenan? ¿Hacia dónde converge?
- L3 Tablero: ¿Qué jugadores, qué incentivos, quién gana si nadie cambia?
- L4 Control: ¿Qué mide? ¿Qué ajusta? ¿Qué señales ignora?

**INTEGRAR:** ¿Las cuatro proyecciones apuntan al mismo punto? ¿Dónde se contradicen?
**ABSTRAER:** ¿Esta forma se repite en otros dominios?
**FRONTERA:** ¿El mapa es el territorio? ¿Hay algo que esta estructura no puede ver?

---

#### INT-04: ECOLÓGICA

**EXTRAER — mapear el ecosistema**
- ¿Quiénes son los organismos del sistema? ¿Qué fluye entre ellos?
- ¿De qué depende cada uno para sobrevivir?
- ¿Qué pasa si quitas uno — quién se cae?
- ¿Hay nichos vacíos — roles que nadie ocupa?

**CRUZAR — evaluar resiliencia**
- ¿El sistema es monocultivo o diverso?
- ¿Hay redundancia — más de un organismo puede cumplir cada función?
- ¿Qué ciclos de regeneración existen? ¿Se están respetando?
- ¿El capital biológico se está reponiendo o solo gastando?

**LENTES:**
- L1 Diversidad: ¿Cuántas especies diferentes hay? ¿Cuántos nichos están ocupados?
- L2 Flujos: ¿El flujo de recursos es circular o lineal? ¿Hay desperdicio?
- L3 Resiliencia: ¿Cuántas perturbaciones puede absorber antes de colapsar?
- L4 Ciclos: ¿Hay estaciones? ¿Períodos de descanso? ¿O es explotación continua?

**INTEGRAR:** ¿El ecosistema es sostenible a 5 años?
**ABSTRAER:** ¿Este patrón de fragilidad se repite en otros ecosistemas?
**FRONTERA:** ¿El individuo importa o solo el sistema? ¿Es ético optimizar el sistema a costa de alguien?

---

#### INT-05: ESTRATÉGICA

**EXTRAER — evaluar posición**
- ¿Dónde está esta persona respecto a donde quiere estar?
- ¿Qué recursos tiene disponibles — tiempo, dinero, relaciones, conocimiento?
- ¿Qué opciones tiene realmente — no las que cree, las reales?
- ¿Qué ventanas temporales se están cerrando?

**CRUZAR — secuenciar movimientos**
- ¿Qué hay que hacer primero para que lo segundo sea posible?
- ¿Alguna acción es irreversible? ¿Cuáles se pueden deshacer?
- ¿Qué puede hacer el otro jugador en respuesta?
- ¿El plan funciona si no todo sale según lo previsto?

**LENTES:**
- L1 Posición: ¿Está mejorando o empeorando? ¿A qué velocidad?
- L2 Opcionalidad: ¿Cuántas opciones tiene? ¿Se están cerrando o abriendo?
- L3 Timing: ¿Hay ventana óptima? ¿Actuar tarde es peor que actuar mal?
- L4 Asimetría: ¿Puede ganar mucho arriesgando poco, o al revés?

**INTEGRAR:** ¿La posición, las opciones y el timing apuntan a la misma acción?
**ABSTRAER:** ¿Qué tipo de jugada es esta — defensiva, ofensiva, de espera?
**FRONTERA:** ¿Esto es una partida? ¿Y si no hay adversario — solo la realidad?

---

#### INT-06: POLÍTICA

**EXTRAER — mapear poder**
- ¿Quién decide realmente? ¿Quién cree que decide?
- ¿Quién tiene poder formal y quién tiene poder real?
- ¿Qué alianzas existen? ¿Cuáles están articuladas y cuáles son tácitas?
- ¿Quién gana y quién pierde con el statu quo?

**CRUZAR — analizar legitimidad**
- ¿La persona con más poder tiene legitimidad para usarlo?
- ¿Hay un plebiscito silencioso — la gente vota con los pies?
- ¿Quién controla la narrativa? ¿Quién no tiene voz?
- ¿El conflicto es de intereses o de visión?

**LENTES:**
- L1 Coaliciones: ¿Qué coaliciones podrían formarse? ¿Quién es bisagra?
- L2 Legitimidad: ¿El poder viene de resultados, jerarquía, o inercia?
- L3 Narrativa: ¿Cómo se enmarca el conflicto? ¿Quién controla el frame?
- L4 Influencia: ¿Quién no está en la mesa pero afecta las decisiones?

**INTEGRAR:** ¿Hay una solución que satisfaga a las coaliciones clave?
**ABSTRAER:** ¿Este conflicto político es típico de esta estructura?
**FRONTERA:** ¿El poder es la lente correcta? ¿Y si no es poder sino miedo?

---

#### INT-07: FINANCIERA

**EXTRAER — mapear flujos**
- ¿De dónde viene el dinero? ¿Hacia dónde va?
- ¿Cuánto es fijo y cuánto variable?
- ¿Los ingresos dependen de la persona o tienen vida propia?
- ¿Hay colchón? ¿Cuántos meses aguanta sin ingresos?

**CRUZAR — evaluar riesgo**
- ¿Lo que va a ganar mañana, cuánto vale hoy?
- ¿Está usando dinero ajeno — y ese dinero amplifica ganancias o pérdidas?
- ¿Hay asimetría — puede ganar mucho si sale bien y perder poco si sale mal? ¿O al revés?
- ¿Cuánto puede salir mal antes de que el sistema se rompa?

**LENTES:**
- L1 Valor presente: ¿El dinero futuro es seguro o es promesa? ¿A qué tasa descuenta?
- L2 Apalancamiento: ¿El que presta gana más que el que recibe?
- L3 Opcionalidad: ¿Cuánto cuesta mantener opciones abiertas? ¿Puede comprar tiempo?
- L4 Margen de seguridad: ¿Opera al límite o con margen? ¿Un imprevisto lo pone en crisis?

**INTEGRAR:** ¿El valor presente justifica el apalancamiento? ¿Hay margen de seguridad suficiente?
**ABSTRAER:** ¿Este perfil financiero es sostenible a 5 años?
**FRONTERA:** ¿Todo se puede traducir a euros? ¿Cuánto vale una cena con los hijos en la hoja de cálculo?

---

#### INT-08: SOCIAL

**EXTRAER — mapear emociones**
- ¿Qué siente esta persona — no lo que dice, lo que siente?
- ¿Cómo se nota — tono, ritmo, lo que evita decir, lo que repite?
- ¿Qué necesita realmente — no lo que pide, lo que necesita?
- ¿Quién más está afectado y cómo se sienten?
- ¿Hay emociones que nadie nombra pero que gobiernan las decisiones?

**CRUZAR — emociones × relaciones**
- ¿Lo que siente coincide con lo que muestra?
- ¿Los demás perciben lo que realmente pasa o solo la superficie?
- ¿Hay patrones — esta situación se repite?
- ¿Qué trigger activaría una reacción desproporcionada?

**LENTES:**
- L1 Empatía: ¿Qué emoción domina y cómo afecta las decisiones?
- L2 Patrones: ¿Esto le ha pasado antes? ¿Cómo respondió? ¿Funcionó?
- L3 Vínculos: ¿Qué relaciones están en juego? ¿Cuáles se pueden romper?
- L4 Identidad: ¿Quién cree que es? ¿Quién necesita ser para otros?

**INTEGRAR:** ¿Las emociones, los patrones y los vínculos apuntan al mismo conflicto?
**ABSTRAER:** ¿Este patrón emocional es una respuesta aprendida que ya no sirve?
**FRONTERA:** ¿Todo es emoción? ¿Y si el problema es estructural y las emociones son síntoma?

---

#### INT-09: LINGÜÍSTICA

**EXTRAER — mapear lenguaje**
- ¿Qué palabras usa? ¿Qué palabras evita?
- ¿Qué metáfora gobierna su pensamiento?
- ¿Hay algo que no tiene nombre en su vocabulario?
- ¿Qué dice sin querer decirlo?

**CRUZAR — lenguaje × realidad**
- ¿El marco lingüístico abre o cierra opciones?
- ¿Cambiar una palabra cambiaría la percepción del problema?
- ¿Hay actos performativos — frases que crean la realidad que describen?
- ¿Qué silencio es más elocuente que las palabras?

**LENTES:**
- L1 Marcos: ¿Qué marco gobierna? ¿Qué alternativas hay?
- L2 Metáforas: ¿La metáfora ilumina o aprisiona?
- L3 Actos de habla: ¿Qué hace al decir lo que dice?
- L4 Silencios: ¿Qué no se dice? ¿Qué no se puede decir?

**INTEGRAR:** ¿Marcos, metáforas, actos y silencios cuentan la misma historia?
**ABSTRAER:** ¿Este patrón lingüístico es típico de su dominio/cultura?
**FRONTERA:** ¿Nombrar cambia algo? ¿O solo da ilusión de control?

---

#### INT-10: CINESTÉSICA

**EXTRAER — mapear tensiones**
- ¿Dónde hay tensión — física, emocional, operativa?
- ¿Es tensión-músculo (produce movimiento) o tensión-nudo (bloquea)?
- ¿Cuál es el ritmo de esta persona/sistema? ¿Es sostenible?
- ¿Hay movimientos automatizados que ya no se cuestionan?

**CRUZAR — tensión × ritmo**
- ¿Las tensiones están coordinadas o descoordinadas?
- ¿El ritmo de trabajo coincide con el ritmo de vida?
- ¿Soltar tensión mejoraría o empeoraría el resultado?
- ¿El cuerpo dice algo que la mente niega?

**LENTES:**
- L1 Tensión: ¿Dónde está el nudo? ¿Qué lo mantiene?
- L2 Ritmo: ¿Hay arritmia? ¿Tempos incompatibles?
- L3 Coordinación: ¿Las partes se mueven juntas o se estorban?
- L4 Flujo: ¿Hay estado de flujo o es puro esfuerzo?

**INTEGRAR:** ¿La tensión, el ritmo y la coordinación apuntan al mismo bloqueo?
**ABSTRAER:** ¿El patrón corporal refleja el patrón decisional?
**FRONTERA:** ¿El cuerpo es dato o es intuición? ¿Es fiable?

---

#### INT-11: ESPACIAL

**EXTRAER — mapear espacio**
- ¿Qué forma tiene el sistema visto desde arriba?
- ¿Dónde se concentra la presión? ¿Dónde hay espacio vacío?
- ¿Qué fronteras son permeables y cuáles son rígidas?
- ¿Cómo se ve esto desde la perspectiva de cada actor?

**CRUZAR — perspectivas**
- ¿Hay divergencia tri-perspectiva (desde dentro vs arriba vs fuera)?
- ¿La compresión en un punto genera expansión en otro?
- ¿Hay pendiente gravitacional — hacia dónde rueda todo naturalmente?
- ¿Qué proporción ocupan las partes respecto al todo?

**LENTES:**
- L1 Compresión: ¿Dónde está el cuello de botella?
- L2 Perspectiva: ¿Cómo cambia al rotar el ángulo?
- L3 Frontera: ¿Qué entra y qué sale? ¿La frontera protege o aísla?
- L4 Proporción: ¿Las partes tienen tamaño apropiado respecto a su función?

**INTEGRAR:** ¿La forma del sistema explica su comportamiento?
**ABSTRAER:** ¿Esta geometría se repite en otros sistemas similares?
**FRONTERA:** ¿Todo tiene forma? ¿Los procesos sin extensión son invisibles aquí?

---

#### INT-12: NARRATIVA

**EXTRAER — identificar el arco**
- ¿Quién es el protagonista? ¿En qué acto de su historia estamos?
- ¿Qué transformación necesita ocurrir?
- ¿Qué narrativa se cuenta a sí mismo sobre esta situación?
- ¿Esa narrativa ayuda o paraliza?

**CRUZAR — narrativa × realidad**
- ¿La historia que se cuenta es fiel a los hechos?
- ¿Hay roles asignados (héroe, villano, víctima) que no corresponden?
- ¿El arco narrativo está avanzando o estancado?
- ¿Qué historia se contaría desde la perspectiva del antagonista?

**LENTES:**
- L1 Arco: ¿Planteamiento, nudo o desenlace?
- L2 Personaje: ¿Quién es el héroe, el mentor, el guardián del umbral?
- L3 Conflicto: ¿Interno, externo, o ambos? ¿Cuál domina?
- L4 Significado: ¿Qué sentido le da a los eventos? ¿Ese sentido le sirve?

**INTEGRAR:** ¿El arco, los personajes y el conflicto cuentan la misma historia?
**ABSTRAER:** ¿Este patrón narrativo es reconocible en otras historias?
**FRONTERA:** ¿Forzar trama donde hay coincidencia? ¿No todo es historia?

---

#### INT-13: PROSPECTIVA

**EXTRAER — mapear futuros**
- ¿Qué tendencias están activas?
- ¿Qué señales débiles hay que nadie está mirando?
- ¿Qué comodines podrían cambiar todo?
- ¿Qué escenarios son plausibles a 1, 3 y 5 años?

**CRUZAR — tendencias × disrupciones**
- ¿Las tendencias convergen o divergen?
- ¿Hay punto de bifurcación — momento donde un pequeño cambio desvía todo?
- ¿El plan actual es robusto en varios escenarios o solo en el optimista?
- ¿Qué escenario sería catastrófico — y qué probabilidad tiene?

**LENTES:**
- L1 Tendencias: ¿Qué está creciendo? ¿Qué está decayendo? ¿A qué velocidad?
- L2 Escenarios: ¿Escenario optimista vs pesimista vs cisne negro?
- L3 Señales: ¿Qué señales débiles apuntan a cambio de tendencia?
- L4 Bifurcaciones: ¿Dónde está el punto de no retorno?

**INTEGRAR:** ¿Las tendencias, escenarios y señales convergen en la misma dirección?
**ABSTRAER:** ¿Este sector/situación tiene trampas de escalamiento conocidas?
**FRONTERA:** ¿Se puede predecir el futuro? ¿El cisne negro es predecible?

---

#### INT-14: DIVERGENTE

**EXTRAER — ampliar opciones**
- ¿Cuántas opciones ve esta persona? (Normalmente 2)
- ¿Qué restricciones asume que son negociables?
- ¿Qué pasaría si hace exactamente lo contrario de lo planeado?
- ¿Quién ha resuelto un problema similar de forma inesperada?

**CRUZAR — restricciones × posibilidades**
- ¿Cuántas de las restricciones son reales y cuántas asumidas?
- ¿Se puede invertir el problema — resolver el opuesto?
- ¿Qué acción mínima tendría máximo impacto?
- ¿Hay 20+ opciones donde solo ve 2?

**LENTES:**
- L1 Inversión: ¿Y si hace lo contrario?
- L2 Combinación: ¿Puede combinar opciones que parecen excluyentes?
- L3 Escala: ¿Y si lo hace 10x más grande? ¿O 10x más pequeño?
- L4 Eliminación: ¿Y si elimina la restricción principal?

**INTEGRAR:** De todas las opciones generadas, ¿cuáles sobreviven al filtro de viabilidad?
**ABSTRAER:** ¿El patrón de pensamiento de esta persona limita sus opciones consistentemente?
**FRONTERA:** ¿Generar opciones es útil o es procrastinar la decisión?

---

#### INT-15: ESTÉTICA

**EXTRAER — percibir forma**
- ¿Este sistema tiene coherencia interna — las partes encajan?
- ¿Hay disonancia — algo que chirría formalmente?
- ¿La solución propuesta tiene la misma forma que el problema?
- ¿Hay elegancia posible — una solución que resuelve múltiples cosas con un gesto?

**CRUZAR — forma × fondo**
- ¿La disonancia formal señala un problema de contenido?
- ¿La solución isomórfica al problema lo replica en vez de resolverlo?
- ¿Hay simetría donde debería haber asimetría, o viceversa?
- ¿Qué reduciría todo a su esencia?

**LENTES:**
- L1 Coherencia: ¿Las piezas encajan o hay ruido?
- L2 Isomorfismo: ¿La solución replica la estructura del problema?
- L3 Proporción: ¿El esfuerzo es proporcional al resultado?
- L4 Esencia: ¿Qué sobra? ¿Qué frase contiene todo?

**INTEGRAR:** ¿La coherencia, el isomorfismo y la proporción apuntan al mismo juicio?
**ABSTRAER:** ¿La disonancia formal es indicador fiable de problemas?
**FRONTERA:** ¿Lo feo puede ser verdadero? ¿La elegancia puede ser engañosa?

---

#### INT-16: CONSTRUCTIVA

**EXTRAER — identificar lo construible**
- ¿Qué se puede construir hoy con lo que hay?
- ¿Cuál es el primer paso — no el plan completo, el primer paso?
- ¿Cuánto cuesta (tiempo, dinero, esfuerzo) ese primer paso?
- ¿Qué pasa si falla? ¿Es reversible?

**CRUZAR — prototipo × restricciones**
- ¿El prototipo resuelve el problema real o solo el problema declarado?
- ¿Cuál es la secuencia óptima de construcción?
- ¿Dónde está el camino crítico — qué no puede retrasarse?
- ¿Cuántas iteraciones necesita antes de decisión irreversible?

**LENTES:**
- L1 Prototipo: ¿Versión mínima que prueba la hipótesis?
- L2 Secuencia: ¿En qué orden? ¿Qué depende de qué?
- L3 Fallo seguro: ¿Si falla, cuánto se pierde? ¿Hay rollback?
- L4 Iteración: ¿Cuántas versiones antes de comprometerse?

**INTEGRAR:** ¿El prototipo, la secuencia y el fallo seguro son coherentes?
**ABSTRAER:** ¿Este patrón de construcción es replicable?
**FRONTERA:** ¿Construir es la respuesta? ¿Y si primero hay que cuestionar las premisas?

---

#### INT-17: EXISTENCIAL

**EXTRAER — mapear valores**
- ¿Qué está realmente en juego — más allá del dinero y la logística?
- ¿Los valores declarados coinciden con los vividos?
- ¿Qué está sacrificando? ¿Lo sabe?
- ¿Qué versión de sí mismo pierde si elige cada opción?

**CRUZAR — valores × acciones**
- ¿Hay una conversación consigo mismo que está evitando?
- ¿La inercia es una elección disfrazada de no-elección?
- ¿Qué le diría su yo de 80 años mirando atrás?
- ¿Está viviendo de acuerdo con lo que dice que importa?

**LENTES:**
- L1 Propósito: ¿Para qué hace lo que hace? ¿La respuesta le satisface?
- L2 Finitud: ¿Esta ventana se cierra? ¿Cuándo?
- L3 Responsabilidad: ¿Ante quién responde? ¿Y ante sí mismo?
- L4 Autenticidad: ¿Lo que hace es lo que quiere, o lo que cree que debe?

**INTEGRAR:** ¿El propósito, la finitud y la autenticidad convergen?
**ABSTRAER:** ¿La brecha valores-acciones es universal o específica?
**FRONTERA:** ¿Esta profundidad ayuda o paraliza? ¿Cuándo parar de preguntar y actuar?

---

#### INT-18: CONTEMPLATIVA

**EXTRAER — observar sin juzgar**
- ¿Qué hay aquí — antes de cualquier análisis?
- ¿Qué se siente al simplemente estar con esto — sin resolver?
- ¿Hay prisa real o la urgencia es inventada?

**CRUZAR — observación × impulso**
- ¿El impulso de actuar viene de la situación o del miedo a no actuar?
- ¿Qué pasaría si espera — no por indecisión, sino por observación?
- ¿Hay sabiduría en la pausa que la acción destruiría?
- ¿El problema necesita resolverse o necesita ser sostenido?

**LENTES:**
- L1 Presencia: ¿Está aquí o en el futuro preocupado?
- L2 Paradoja: ¿Las dos opciones opuestas pueden ser verdad a la vez?
- L3 Soltar: ¿Qué está agarrando que necesita soltar? ¿El control es real?
- L4 Vacío: ¿Hay espacio para que algo nuevo emerja? ¿O está todo lleno?

**INTEGRAR:** ¿La presencia, la paradoja, el soltar y el vacío apuntan al mismo silencio?
**ABSTRAER:** ¿Toda crisis tiene un momento donde parar es más valiente que actuar?
**FRONTERA:** ¿La contemplación es sabiduría o privilegio de quien puede esperar?

---

## 7. DATOS DE COMPLEMENTARIEDAD (para el compositor)

### Pares de máximo diferencial (score > 0.85)

| Par | Score | A ve que B no puede | B ve que A no puede |
|-----|-------|--------------------|--------------------|
| INT-01 × INT-08 | 0.95 | Contradicción formal demostrable | Vergüenza no nombrada, lealtad invisible |
| INT-07 × INT-17 | 0.93 | Asimetría payoffs cuantificada | Brecha valores declarados vs vividos |
| INT-02 × INT-15 | 0.90 | Dato trivializador, scheduling | Isomorfismo solución-problema |
| INT-09 × INT-16 | 0.88 | Marcos, silencios, actos performativos | Prototipo construible con coste y fallo seguro |
| INT-04 × INT-14 | 0.87 | Monocultivo, fragilidad | 20+ opciones de reconfiguración |
| INT-06 × INT-18 | 0.86 | Coaliciones, poder real | Urgencia inventada, vacío como recurso |
| INT-03 × INT-18 | 0.84 | Gap id↔ir, actor invisible | Pausa como acto, sistema sin margen |
| INT-05 × INT-09 | 0.82 | Secuencia obligatoria, reversibilidad | Metáfora-prisión, acto performativo |

### Clusters de redundancia (pares con score < 0.50 de diferencial)

| Cluster | Inteligencias | Lo que comparten |
|---------|---------------|-----------------|
| Sistémicas | INT-03, INT-04, INT-10 | Ven el sistema completo, partes conectadas |
| Relacionales | INT-08, INT-12 | Dimensión humana del drama |
| Existenciales | INT-17, INT-18 | Nivel de significado profundo |
| Perceptuales | INT-09, INT-15 | Detectan incongruencias de forma |

### Reclasificación empírica (9 categorías por comportamiento real)

| # | Categoría | Inteligencias |
|---|-----------|---------------|
| 1 | Cuantitativa | INT-01, INT-02, INT-07 |
| 2 | Sistémica | INT-03, INT-04 |
| 3 | Posicional | INT-05, INT-06 |
| 4 | Interpretativa | INT-08, INT-09, INT-12 |
| 5 | Corporal-Perceptual | INT-10, INT-15 |
| 6 | Espacial | INT-11 |
| 7 | Expansiva | INT-13, INT-14 |
| 8 | Operativa | INT-16 |
| 9 | Contemplativa-Existencial | INT-17, INT-18 |

### Inteligencias irreducibles (no sustituibles por combinación)

INT-01, INT-02, INT-06, INT-08, INT-14, INT-16

### Propiedades algebraicas confirmadas

| Propiedad | Resultado | Implicación para el motor |
|-----------|-----------|--------------------------|
| Composición NO conmutativa | A→B ≠ B→A siempre | El orden importa. Formal primero → humano después |
| NO asociativa | (A→B)→C ≠ A→(B→C) | No reorganizar. Secuencia lineal mejor que agrupada |
| Fusión parcialmente conmutativa | A|B ≈ B|A al 25% | Orden de fusión afecta framing. No intercambiable |
| No idempotente | A→A ≠ A (18/18) | Loop test siempre justificado. 2 pasadas = óptimo |
| Saturación en n=2 | 3ª pasada aporta 10-15% | No hacer 3ª excepto calibración |
| Clausura confirmada | output ∈ input | Cualquier output puede alimentar cualquier otra inteligencia |
| Distributividad izquierda ~70% | Se pierde ~30% al factorizar | Aceptable para ahorro, no para pares TOP |
| Distributividad derecha PROHIBIDA | El cruce previo tiene valor irreducible | Nunca factorizar el cruce que alimenta a una inteligencia |

---

## 8. ESQUEMA DE BASE DE DATOS (fly.io Postgres)

```sql
-- Tabla de inteligencias (18 registros, estática)
CREATE TABLE inteligencias (
    id TEXT PRIMARY KEY,          -- 'INT-01', 'INT-02', ...
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    firma TEXT NOT NULL,
    punto_ciego TEXT NOT NULL,
    objetos_exclusivos TEXT[],
    preguntas JSONB NOT NULL      -- red completa de preguntas por paso
);

-- Tabla de aristas del grafo (para el compositor)
CREATE TABLE aristas_grafo (
    id SERIAL PRIMARY KEY,
    origen TEXT REFERENCES inteligencias(id),
    destino TEXT REFERENCES inteligencias(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('composicion', 'fusion', 'diferencial')),
    peso FLOAT NOT NULL,          -- score de complementariedad o valor de la operación
    direccion_optima TEXT,         -- 'A→B' o 'B→A' o 'indistinto'
    hallazgo_emergente TEXT,       -- qué produce esta combinación
    UNIQUE(origen, destino, tipo)
);

-- Tabla de ejecuciones (telemetría + retroalimentación)
CREATE TABLE ejecuciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    input TEXT NOT NULL,
    contexto TEXT,
    modo TEXT NOT NULL,
    algoritmo_usado JSONB NOT NULL,
    resultado JSONB NOT NULL,
    coste_usd FLOAT,
    tiempo_s FLOAT,
    score_calidad FLOAT,
    feedback_usuario JSONB        -- se rellena después
);

-- Vectores para router futuro (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings_inteligencias (
    id TEXT PRIMARY KEY REFERENCES inteligencias(id),
    embedding vector(1024),       -- Voyage-3 dimension
    texto_base TEXT               -- firma + objetos + punto ciego concatenados
);
```

---

## 9. ESTRUCTURA DE ARCHIVOS DEL PROYECTO

```
motor-semantico/
├── fly.toml                     # Config fly.io
├── Dockerfile                   # Runtime
├── package.json / requirements.txt
├── src/
│   ├── server.ts/py             # HTTP server + endpoints
│   ├── pipeline/
│   │   ├── router.ts/py         # Capa 1: selección de inteligencias (Sonnet)
│   │   ├── compositor.ts/py     # Capa 2: grafo + algoritmo (NetworkX/código puro)
│   │   ├── generador.ts/py      # Capa 3: genera prompts desde Meta-Red
│   │   ├── ejecutor.ts/py       # Capa 4: ejecuta prompts via Anthropic API
│   │   ├── evaluador.ts/py      # Capa 5: scorer heurístico
│   │   └── integrador.ts/py     # Capa 6: síntesis final (Sonnet)
│   ├── db/
│   │   ├── schema.sql           # Tablas
│   │   ├── seed.sql             # 18 inteligencias + aristas
│   │   └── client.ts/py         # Conexión Postgres
│   ├── meta-red/
│   │   └── inteligencias.json   # Las 18 redes de preguntas (cargado en memoria)
│   └── config/
│       ├── reglas.ts/py          # 13 reglas del compilador
│       └── modelos.ts/py         # Config LLM (keys, modelos, fallback)
├── tests/
│   ├── test_router.ts/py
│   ├── test_compositor.ts/py
│   └── test_pipeline_e2e.ts/py
└── scripts/
    └── seed_db.ts/py            # Poblar DB con datos de cartografía
```

---

## 10. CRITERIO DE CIERRE MVP

- [ ] Pipeline end-to-end funcional en fly.io
- [ ] POST /motor/ejecutar acepta input en lenguaje natural
- [ ] Router selecciona 4-5 inteligencias relevantes
- [ ] Compositor genera algoritmo respetando las 13 reglas
- [ ] Ejecutor ejecuta preguntas via Anthropic API
- [ ] Integrador produce síntesis final
- [ ] Los 4 modos funcionan (análisis, generación, conversación, confrontación)
- [ ] Coste < $1.50 por ejecución
- [ ] Latencia < 150s en modo análisis, < 60s en modo conversación
- [ ] Telemetría guardada en DB (cada ejecución es un datapoint)
- [ ] Test E2E con los 3 casos de cartografía (clínica dental, SaaS, cambio carrera)

---

## 11. RESTRICCIONES

- **LLM API:** Anthropic. Haiku para extracción, Sonnet para routing/integración. Opus solo si frontera justifica coste.
- **NO usar:** OpenAI, Supabase, Edge Functions, Deno.
- **Presupuesto testing:** ~€150 para las ~100 ejecuciones de testing.
- **4 API keys rotativas:** Implementar rotación para evitar rate limits.

---

**FIN PROMPT MOTOR v1 MVP**
