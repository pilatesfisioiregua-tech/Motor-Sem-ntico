# TAXONOMÍA DE TIPOS DE PENSAMIENTO Y RAZONAMIENTO × LENTES × FUNCIONES

**Fecha:** 2026-03-19  
**Estado:** CR0  
**Dependencia:** `gradientes_equilibrio_inteligencias.md`, `PROMPT_MVP.md`, `Tipos_Logicos.md`  
**Motivo:** No existía en Maestro v3. Es pieza clave: las inteligencias son QUÉ mira el sistema; los tipos de pensamiento y razonamiento son CÓMO procesa lo que ve.

---

## 0. DISTINCIÓN FUNDAMENTAL

```
INTELIGENCIA  = DOMINIO de observación (QUÉ miras: números, relaciones, espacio, existencia...)
RAZONAMIENTO  = MECANISMO inferencial (CÓMO conectas premisas con conclusiones)
PENSAMIENTO   = ESTRATEGIA cognitiva (CÓMO organizas el proceso completo de pensar)
```

Las tres son ortogonales: puedes usar razonamiento abductivo (mecanismo) dentro de inteligencia financiera (dominio) con pensamiento sistémico (estrategia). Son dimensiones independientes que se combinan.

**Analogía con el sistema:**
- Inteligencia = el SENSOR (qué captas)
- Razonamiento = el CABLE (cómo transmites señal)
- Pensamiento = la ARQUITECTURA del circuito (cómo organizas el procesamiento)

---

## PARTE 1: TIPOS DE RAZONAMIENTO (Mecanismos inferenciales)

### 1.1 Catálogo de 12 tipos de razonamiento

#### R01. DEDUCCIÓN — De lo general a lo particular (certeza)

```
Si todos los A son B, y X es A → X es B.
```

**Qué hace:** Garantiza conclusiones a partir de premisas. Si las premisas son verdaderas, la conclusión es necesariamente verdadera. No genera conocimiento nuevo — extrae lo que ya estaba implícito.

**Lente primaria:** **S** (Salud/operatividad). La deducción hace operable lo que ya se sabe. Convierte conocimiento abstracto en acción segura.

**Función primaria:** **F1** (Conservar). La deducción preserva verdad — lo que se deduce correctamente es tan cierto como las premisas. También **F3** cuando se deducen contradicciones (depurar inconsistencias).

**Fuerza:** Certeza. Si la deducción es válida, el resultado es incuestionable.  
**Límite:** No genera nada nuevo. No puede trabajar con incertidumbre. Si las premisas son falsas, la deducción es perfecta pero inútil (Maginot: deducción impecable desde premisas incorrectas sobre guerra estática).

**Ejemplo en el framework:** "Si F2>0.60 y F3<0.25 → flag de intoxicación" es una regla deductiva.

---

#### R02. INDUCCIÓN — De lo particular a lo general (probabilidad)

```
He visto 1000 cisnes blancos → probablemente todos los cisnes son blancos.
```

**Qué hace:** Generaliza desde observaciones. Produce hipótesis probables pero nunca certezas. Es el motor de la ciencia empírica.

**Lente primaria:** **Se** (Sentido/comprensión). La inducción genera comprensión nueva — descubre patrones que no estaban explícitos. 

**Función primaria:** **F2** (Captar patrones) + **F5** (construir frontera — la generalización define qué es "normal").

**Fuerza:** Genera conocimiento nuevo. Descubre regularidades.  
**Límite:** Nunca es segura (el cisne negro). La confianza crece con la muestra pero nunca llega a certeza. Vulnerable al sesgo de confirmación.

**Ejemplo en el framework:** "F2→F3(B) activada en 39/50 casos → probablemente es universal" es inducción.

---

#### R03. ABDUCCIÓN — La mejor explicación (inferencia al mecanismo)

```
El césped está mojado. La mejor explicación es que llovió (no que alguien regó).
```

**Qué hace:** Genera la hipótesis más plausible para un fenómeno observado. No busca certeza (deducción) ni regularidad (inducción) — busca EXPLICACIÓN. Es el razonamiento del detective, del médico, del diagnosticador.

**Lente primaria:** **Se** (Sentido). La abducción genera comprensión profunda — explica POR QUÉ algo ocurre, no solo QUÉ ocurre.

**Función primaria:** **F3** (Depurar) + **F5** (Frontera). La abducción depura explicaciones (elimina las menos plausibles) y construye frontera (la mejor explicación define qué es el caso).

**Fuerza:** Genera explicaciones causales. Es el razonamiento más útil para diagnóstico.  
**Límite:** Múltiples explicaciones pueden ser plausibles. La "mejor" depende de criterios no siempre explícitos.

**ESTO ES EL RAZONAMIENTO CENTRAL DEL MOTOR:** Cuando el Motor diagnostica "este sistema es un operador ciego porque F2↑↑ + F3↓ + F5↓", está haciendo abducción. Observa los scores, genera la mejor explicación (perfil + receta funcional).

**Ejemplo:** "Maginot tenía F5 escalar 0.55 pero se comportó como F5 peligrosa. La mejor explicación: F5.Se era baja (0.20)" → abducción.

---

#### R04. ANALOGÍA — Transferencia de estructura entre dominios

```
A es a B como C es a D. Si A→B funciona así, entonces C→D probablemente funciona parecido.
```

**Qué hace:** Transfiere conocimiento de un dominio conocido a uno desconocido por semejanza estructural. No compara contenido — compara RELACIONES.

**Lente primaria:** **Se** (Sentido) + **C** (Continuidad). La analogía genera comprensión (Se) viendo un problema a través de otro dominio. Y genera continuidad (C) porque el conocimiento de un dominio se TRANSFIERE.

**Función primaria:** **F7** (Replicar — el patrón se replica cross-dominio) + **F5** (Frontera — la analogía revela la estructura invariante).

**Fuerza:** Transferencia cross-dominio. "Toyota = Virginia Mason" es analogía que transfirió TPS a salud.  
**Límite:** La analogía puede ser superficial. Dos cosas pueden parecer iguales en estructura pero diferir en mecanismo.

**Ejemplo en el framework:** Todo el Reactor v5 es razonamiento analógico: "F2→F3(B) en Toyota (negocio) = F2→F3(B) en opioides (salud) = F2→F3(B) en Boeing (ingeniería)" — misma estructura, diferentes dominios.

---

#### R05. RAZONAMIENTO CAUSAL — Causa → efecto (y cadenas)

```
A causa B. B causa C. Por tanto A causa C (con intermediación de B).
```

**Qué hace:** Establece relaciones de causa-efecto. Va más allá de correlación ("A y B ocurren juntos") a mecanismo ("A produce B porque X").

**Lente primaria:** **Se** (Sentido). Entender causas = comprender POR QUÉ.

**Función primaria:** **F3** (Depurar — separar causa real de correlación espuria) + **F4** (Distribuir — saber qué causa qué permite intervenir donde toca).

**Fuerza:** Base de toda intervención. Si no sabes la causa, no puedes actuar con precisión.  
**Límite:** La causalidad es difícil de establecer. Confundir correlación con causa es uno de los errores más comunes.

**Ejemplo:** "F3.Se→F5.Se es causal (no solo correlación)" — el análisis KonMari demostró cadena causal, no mera co-ocurrencia.

---

#### R06. RAZONAMIENTO CONTRAFACTUAL — ¿Qué habría pasado si...?

```
Si Kodak HUBIERA depurado la dependencia de película (F3↑), ¿habría cerrado?
```

**Qué hace:** Imagina mundos alternativos donde una variable cambió. Evalúa la importancia de un factor preguntando qué pasaría sin él.

**Lente primaria:** **Se** (Sentido) + **C** (Continuidad). Comprender qué habría pasado = comprensión profunda de mecanismos. Proyectar escenarios = pensamiento de futuro.

**Función primaria:** **F6** (Adaptar — evaluar caminos alternativos) + **F3** (Depurar — eliminar factores irrelevantes identificando cuáles SÍ importan).

**Fuerza:** Evalúa importancia relativa de factores. Permite aprender de errores sin repetirlos.  
**Límite:** Los contrafactuales no son verificables. "¿Qué habría pasado si...?" no tiene respuesta segura.

**Ejemplo:** "Si Google+ hubiera tenido F5.Se alta (identidad con propósito), ¿habría sobrevivido?" → contrafactual que evalúa si el gap era soluble internamente o si el factor exógeno era insuperable.

---

#### R07. RAZONAMIENTO PROBABILÍSTICO / BAYESIANO — Actualizar creencias con evidencia

```
P(hipótesis|evidencia) = P(evidencia|hipótesis) × P(hipótesis) / P(evidencia)
```

**Qué hace:** Actualiza la confianza en una hipótesis a medida que llega nueva evidencia. No es binario (verdadero/falso) — es gradual (más/menos probable).

**Lente primaria:** **S** (Salud/operatividad). El razonamiento bayesiano hace OPERABLE la incertidumbre. Convierte "no sé" en "sé con X% de confianza".

**Función primaria:** **F3** (Depurar — actualizar eliminando hipótesis que la evidencia contradice) + **F2** (Captar — cada nueva evidencia refina).

**Fuerza:** Maneja incertidumbre formalmente. No necesita certeza para actuar.  
**Límite:** Los priors (creencias iniciales) importan mucho. Priors incorrectos pueden resistir mucha evidencia.

**Ejemplo:** "Confianza de mapeo: 0.80" en cada par del Reactor es un score bayesiano implícito.

---

#### R08. RAZONAMIENTO DIALÉCTICO — Tesis × Antítesis → Síntesis

```
Tesis: F1 alta es buena (conservar funciona).
Antítesis: F1 alta bloquea F6 (conservar impide adaptar).
Síntesis: F1 alta ES buena SI F6 se mantiene activa (conservar con espacio para adaptar).
```

**Qué hace:** Confronta posiciones opuestas para generar una posición superior que integre ambas. No elige entre A y B — genera C que contiene lo válido de ambas.

**Lente primaria:** **Se** (Sentido). La dialéctica es generadora de Se por excelencia — la síntesis es comprensión que no existía antes.

**Función primaria:** **F5** (Frontera — la síntesis redefine los límites del problema) + **F6** (Adaptar — integrar opuestos es adaptación cognitiva).

**Fuerza:** Supera dicotomías falsas. Genera comprensión que ninguna posición aislada tiene.  
**Límite:** No siempre hay síntesis. Algunos opuestos son genuinamente irreconciliables.

**Ejemplo:** "F6→F5(D) puede ser destructiva (JCP) O constructiva (Netflix)" → la ley parecía contradecirse. La síntesis dialéctica: "F6 sin Se destruye F5; F6 con Se construye F5."

---

#### R09. RAZONAMIENTO POR ELIMINACIÓN — Descartar hasta que quede lo posible

```
Si no es A, ni B, ni C → debe ser D (asumiendo A-D son exhaustivos).
```

**Qué hace:** Reduce el espacio de posibilidades eliminando candidatos. Cada eliminación reduce incertidumbre.

**Lente primaria:** **S** (Salud) + **Se** (Sentido). La eliminación hace operable la búsqueda (S) y genera comprensión al estrechar (Se).

**Función primaria:** **F3** (Depurar — eliminar lo que no encaja es depuración pura).

**Fuerza:** Funciona cuando la generación directa es imposible. Sherlock Holmes: "Elimina lo imposible, lo que quede, por improbable que sea, es la verdad."  
**Límite:** Requiere lista exhaustiva. Si faltan candidatos, la eliminación lleva a conclusión incorrecta.

**Ejemplo:** "El fallo de Maginot no es F5 baja (escalar=0.55). No es F6 baja sola (no explica la dirección incorrecta). Por eliminación → es F5.Se baja (frontera sin comprensión)."

---

#### R10. RAZONAMIENTO ABDUCTIVO-RETRODUCTIVO — Del efecto al mecanismo generador

```
Observo patrón P. ¿Qué estructura GENERARÍA necesariamente P?
```

**Qué hace:** Versión fuerte de abducción. No busca la "mejor explicación" sino la ESTRUCTURA NECESARIA que produce el fenómeno. Es el razonamiento de Peirce, usado en descubrimiento científico.

**Lente primaria:** **Se** (Sentido profundo). Descubrir la estructura generadora es la comprensión más profunda posible.

**Función primaria:** **F5** (Frontera — la estructura descubierta DEFINE el fenómeno).

**Fuerza:** Descubre universales. "¿Qué estructura produce NECESARIAMENTE que F2→F3(B) sea la ley más frecuente?" → la respuesta (F3 como única fuente de Se, H23) es retroducción.  
**Límite:** Difícil y raro. Requiere pensamiento de alto nivel.

---

#### R11. RAZONAMIENTO MODAL — Necesidad, posibilidad, contingencia

```
¿Es NECESARIO que F3 preceda a F5? ¿O es solo POSIBLE que ocurra así?
```

**Qué hace:** Distingue entre lo que DEBE ser (necesario), lo que PUEDE ser (posible), y lo que ES PERO PODRÍA NO SER (contingente).

**Lente primaria:** **Se** (Sentido) + **C** (Continuidad). La necesidad = lo que siempre será (C). La posibilidad = lo que podría comprenderse de otra forma (Se).

**Función primaria:** **F5** (Frontera — ¿es esta frontera necesaria o contingente?).

**Ejemplo:** "¿F2→F3(B) es una ley NECESARIA (siempre se cumple en cualquier sistema) o CONTINGENTE (se cumple en los sistemas que hemos observado)?" → pregunta modal. 78% sugiere alta probabilidad pero no necesidad lógica.

---

#### R12. RAZONAMIENTO TRANSDUCTIVO — De particular a particular

```
Este paciente se parece a aquel otro → lo que funcionó allí probablemente funcione aquí.
```

**Qué hace:** Transfiere de un caso particular a otro sin pasar por lo general. Es el razonamiento clínico del médico experimentado: "He visto esto antes."

**Lente primaria:** **S** (Salud/operatividad). Permite actuar rápido sin formalizar la regla general.

**Función primaria:** **F7** (Replicar — la solución de un caso se replica a otro similar).

**Fuerza:** Rápido. Pragmático. Útil cuando no hay tiempo para inducción formal.  
**Límite:** Anecdótico. Dos casos pueden parecer iguales y no serlo. Es el razonamiento que más se beneficia de F3 (depurar las diferencias entre los casos).

**Ejemplo en pilotos:** "Este paciente con escoliosis se parece al caso S08 del dataset → Pilates genérico sin F5 fue inerte allí → aquí también lo será" → transducción.

---

### 1.2 Resumen: 12 Razonamientos × Lente × Función

| # | Razonamiento | Lente 1ª | Función 1ª | Qué genera |
|---|---|---|---|---|
| R01 | Deducción | S | F1, F3 | Certeza operativa |
| R02 | Inducción | Se | F2, F5 | Patrones generales |
| R03 | Abducción | Se | F3, F5 | Mejor explicación (diagnóstico) |
| R04 | Analogía | Se+C | F7, F5 | Transferencia cross-dominio |
| R05 | Causal | Se | F3, F4 | Mecanismos de causa-efecto |
| R06 | Contrafactual | Se+C | F6, F3 | Evaluación de importancia |
| R07 | Bayesiano | S | F3, F2 | Confianza actualizable |
| R08 | Dialéctico | Se | F5, F6 | Síntesis de opuestos |
| R09 | Eliminación | S+Se | F3 | Reducción del espacio |
| R10 | Retroductivo | Se | F5 | Estructura necesaria |
| R11 | Modal | Se+C | F5 | Necesidad vs contingencia |
| R12 | Transductivo | S | F7 | Transferencia caso→caso |

**Distribución por lente primaria:**
```
S:  R01, R07, R12           → 3 razonamientos operativos
Se: R02, R03, R05, R08, R10 → 5 razonamientos de comprensión
S+Se: R09                   → 1 mixto
Se+C: R04, R06, R11         → 3 razonamientos de comprensión + continuidad
```

**Mismo sesgo que las inteligencias:** el sistema de razonamiento está naturalmente sesgado hacia Se. 8/12 tienen Se como lente primaria o co-primaria. Esto confirma H23: Se es la lente más escasa y el sistema necesita más herramientas para generarla.

---

## PARTE 2: TIPOS DE PENSAMIENTO (Estrategias cognitivas)

### 2.1 Catálogo de 15 tipos de pensamiento

#### P01. PENSAMIENTO LATERAL (De Bono) — Romper el patrón

**Qué hace:** Busca soluciones fuera del marco habitual. En vez de profundizar en la línea recta (pensamiento vertical), se mueve LATERALMENTE a una línea completamente distinta.

**Lente:** **Se** (genera comprensión nueva por reencuadre)  
**Función:** **F6** (Adaptar — cambiar de marco es adaptación cognitiva) + **F14 Divergente** (INT que más se parece)  
**Razonamientos que usa:** Analogía (R04), Contrafactual (R06)

**Cuándo usarlo:** Cuando el sistema está ATRAPADO en un marco que no funciona. Operador ciego, autómata eterno, rigidez consciente (Kodak).

---

#### P02. PENSAMIENTO SISTÉMICO — Ver las conexiones

**Qué hace:** Ve el TODO en vez de las partes. Identifica feedback loops, efectos no lineales, comportamientos emergentes. No aísla variables — las conecta.

**Lente:** **Se** (comprensión de cómo las partes se relacionan)  
**Función:** **F4** (Distribuir — ver cómo los recursos fluyen por el sistema) + **F5** (Frontera — dónde empieza y termina el sistema)  
**Razonamientos que usa:** Causal (R05), Abducción (R03), Dialéctico (R08)

**Cuándo usarlo:** SIEMPRE como modo base. El Motor es pensamiento sistémico por diseño. Especialmente en E3 (funcionalidad) donde los ciclos entre funciones están activos.

---

#### P03. PENSAMIENTO CRÍTICO — Evaluar la evidencia

**Qué hace:** Examina premisas, detecta falacias, evalúa calidad de evidencia, distingue opinión de hecho. Es el guardián contra el autoengaño.

**Lente:** **Se** (comprensión de la validez de lo que se sabe)  
**Función:** **F3** (Depurar — eliminar razonamiento defectuoso) + **F5** (Frontera — distinguir lo fundamentado de lo no fundamentado)  
**Razonamientos que usa:** Deducción (R01), Eliminación (R09), Bayesiano (R07)

**Cuándo usarlo:** SIEMPRE como filtro. Especialmente contra el sesgo retrospectivo (nota metodológica del Reactor: "98% es sospechosamente alto"). Y para detectar colapso de Tipos Lógicos.

---

#### P04. PENSAMIENTO DE DISEÑO (Design Thinking) — Empatizar → Definir → Idear → Prototipar → Testear

**Qué hace:** Ciclo iterativo centrado en el usuario. No empieza por la solución sino por entender el problema desde quien lo vive.

**Lente:** **S** + **Se** (comprensión del usuario + prototipo operable)  
**Función:** **F5** (Frontera — definir el problema real) → **F2** (Captar necesidades) → **F14 Divergente** (idear) → **F16 Constructiva** (prototipar) → **F3** (testear y depurar)  
**Razonamientos que usa:** Abducción (R03), Inducción (R02), Transducción (R12)

**Cuándo usarlo:** Cuando el problema no está bien definido. E2 (latencia) y "visionario atrapado". El ciclo empatizar→prototipar fuerza la transición Se→S.

---

#### P05. PENSAMIENTO DE PRIMEROS PRINCIPIOS — Descomponer hasta lo fundamental

**Qué hace:** Rechaza analogías y suposiciones. Descompone el problema hasta sus componentes irreducibles y reconstruye desde ahí. Elon Musk/Aristóteles.

**Lente:** **Se** (comprensión profunda de por qué algo es como es)  
**Función:** **F3** (Depurar — eliminar suposiciones) + **F1** (Conservar solo lo irreducible)  
**Razonamientos que usa:** Deducción (R01), Retroducción (R10), Eliminación (R09)

**Cuándo usarlo:** Cuando las soluciones convencionales no funcionan. Cuando la analogía (R04) lleva a callejones. "¿Qué sabemos que es NECESARIAMENTE verdad?" Es el pensamiento que descubrió las 7 funciones nucleares (convergencia por superposición, L0.7).

---

#### P06. PENSAMIENTO DIVERGENTE — Generar muchas opciones

**Qué hace:** Amplía el espacio de posibilidades. No evalúa — solo genera. "¿De cuántas formas podría hacerse esto?" Brainstorming puro.

**Lente:** **Se** (ampliar comprensión del espacio de posibilidades)  
**Función:** **F2** (Captar opciones) + **F6** (Adaptar — ver alternativas)  
**Razonamientos que usa:** Analogía (R04), Contrafactual (R06)

**Cuándo usarlo:** Cuando el sistema ve 2 opciones y necesita ver 20. Perfil binario. INT-14 es la inteligencia de pensamiento divergente.

---

#### P07. PENSAMIENTO CONVERGENTE — Seleccionar la mejor

**Qué hace:** Estrecha el espacio. De 20 opciones, selecciona la mejor según criterios explícitos. Complemento necesario del divergente.

**Lente:** **S** (hacer operable la decisión)  
**Función:** **F3** (Depurar — eliminar lo que no encaja) + **F4** (Distribuir — asignar recursos a la opción elegida)  
**Razonamientos que usa:** Deducción (R01), Eliminación (R09), Bayesiano (R07)

**Cuándo usarlo:** Después de P06. El ciclo divergente→convergente es el patrón más común de resolución de problemas.

---

#### P08. METACOGNICIÓN — Pensar sobre el pensamiento

**Qué hace:** Observa el propio proceso de pensamiento. "¿Estoy usando el razonamiento correcto? ¿Mi marco es adecuado? ¿Estoy sesgado?"

**Lente:** **Se** (comprender el propio proceso)  
**Función:** **F3** (Depurar el proceso, no el contenido) + **F5** (Frontera del sistema de pensamiento)  
**Razonamientos que usa:** Modal (R11 — ¿es necesario pensar así?), Contrafactual (R06 — ¿qué pensaría si usara otro marco?)

**Cuándo usarlo:** SIEMPRE como capa de supervisión. Es el Nivel 5 de Tipos Lógicos (Metanivel/Gobierno). Especialmente necesario en autómata eterno (no cuestiona su propio proceso).

**Relación directa:** Metacognición ES lo que eleva el pensamiento de Nivel 1-4 a Nivel 5 del marco de Tipos Lógicos.

---

#### P09. PENSAMIENTO PROSPECTIVO — Escenarios futuros

**Qué hace:** Proyecta múltiples futuros posibles. No predice UNO — genera varios y evalúa robustez de decisiones ante cada uno.

**Lente:** **C** (Continuidad — el futuro ES continuidad)  
**Función:** **F7** (Replicar — ¿el patrón sobrevive en cada escenario?) + **F6** (Adaptar — ¿qué adaptación necesita cada escenario?)  
**Razonamientos que usa:** Contrafactual (R06), Bayesiano (R07), Modal (R11)

**Cuándo usarlo:** Autómata eterno (necesita anticipar el cambio de contexto). E4 plenitud (modo vigilancia). INT-13 Prospectiva es la inteligencia de este pensamiento.

---

#### P10. PENSAMIENTO REFLEXIVO — Examinar la experiencia pasada

**Qué hace:** Revisa lo vivido para extraer aprendizaje. No es nostalgia — es destilación sistemática de experiencia en principios.

**Lente:** **Se** (comprender lo que ocurrió) + **C** (preservar el aprendizaje)  
**Función:** **F1** (Conservar lo aprendido) + **F3** (Depurar la experiencia — separar señal de ruido)  
**Razonamientos que usa:** Inducción (R02), Abducción (R03), Causal (R05)

**Cuándo usarlo:** Después de cada ciclo del Motor. El Reactor v5 ES pensamiento reflexivo: revisar 50 pares para extraer leyes.

---

#### P11. PENSAMIENTO ENCARNADO (Embodied Cognition) — Saber con el cuerpo

**Qué hace:** Integra información sensorial, proprioceptiva y motora en la cognición. El cuerpo no es solo ejecutor — es sensor y procesador.

**Lente:** **S** (operatividad inmediata, presente)  
**Función:** **F1** (Conservar integridad corporal) + **F10 Cinestésica** (INT directa)  
**Razonamientos que usa:** Transducción (R12 — "he sentido esto antes"), Abducción (R03 — "este dolor significa X")

**Cuándo usarlo:** Pilotes. Paciente con dolor. Cualquier situación donde el cuerpo tiene información que la mente no tiene.  
**CRUCIAL para pilotos:** El fisioterapeuta usa pensamiento encarnado al palpar, al observar el movimiento. El paciente lo usa al percibir su dolor. Si el sistema ignora esta dimensión, pierde información crítica.

---

#### P12. PENSAMIENTO NARRATIVO — Comprender a través de historias

**Qué hace:** Organiza experiencia en secuencias con personajes, conflictos y resoluciones. Los humanos comprenden mejor a través de historias que de abstracciones.

**Lente:** **Se** (comprender) + **C** (las historias son el vehículo más antiguo de continuidad)  
**Función:** **F5** (Frontera — la narrativa define quién eres) + **F7** (Replicar — las historias se transmiten)  
**Razonamientos que usa:** Causal (R05 — la narrativa tiene causa→efecto), Analogía (R04 — "esta historia se parece a aquella")

**Cuándo usarlo:** Genio mortal (necesita CONTAR su historia para transferirla). E1 muerte simétrica (necesita una primera narrativa para existir). INT-12 Narrativa es la inteligencia directa.

---

#### P13. PENSAMIENTO COMPUTACIONAL — Descomponer, abstraer, reconocer patrones, algoritmizar

**Qué hace:** 4 operaciones: descomponer problema en partes, abstraer lo esencial, reconocer patrones entre partes, diseñar algoritmo de solución.

**Lente:** **S** (hacer operable) + **C** (el algoritmo es replicable)  
**Función:** **F4** (Distribuir — descomponer es distribuir la carga cognitiva) + **F7** (Replicar — el algoritmo se replica)  
**Razonamientos que usa:** Deducción (R01), Eliminación (R09), Inducción (R02)

**Cuándo usarlo:** Cuando el problema es grande y necesita descomponerse. INT-02 Computacional. El Motor mismo es producto de pensamiento computacional.

---

#### P14. PENSAMIENTO ESTRATÉGICO — Movimientos, secuencias, juego

**Qué hace:** Piensa en movimientos y contra-movimientos. Evalúa posiciones, anticipa respuestas del adversario/entorno, optimiza secuencias.

**Lente:** **S** (ejecutar la secuencia óptima) + **Se** (comprender el juego)  
**Función:** **F4** (Distribuir recursos en el tiempo) + **F6** (Adaptar al movimiento del otro)  
**Razonamientos que usa:** Contrafactual (R06), Bayesiano (R07), Deducción (R01)

**Cuándo usarlo:** Cuando hay competencia o secuencia temporal importa. INT-05 Estratégica. La ley C4 (Se→S→C como secuencia correcta) es producto de pensamiento estratégico.

---

#### P15. PENSAMIENTO INTEGRATIVO (Roger Martin) — Mantener opuestos, generar síntesis

**Qué hace:** Mantiene dos modelos contradictorios en la mente simultáneamente sin elegir entre ellos, hasta que emerge un modelo superior que integra lo mejor de ambos.

**Lente:** **Se** (comprensión profunda que solo emerge de la tensión entre opuestos)  
**Función:** **F5** (Frontera — la síntesis redefine el territorio) + **F6** (Adaptar — integrar opuestos es la adaptación más sofisticada)  
**Razonamientos que usa:** Dialéctico (R08), Modal (R11), Retroductivo (R10)

**Cuándo usarlo:** Cuando las "soluciones" existentes parecen mutuamente excluyentes. "¿F7 amplifica o degrada?" → pensamiento integrativo: "F7 amplifica Y degrada — depende del perfil de lentes."

---

### 2.2 Resumen: 15 Pensamientos × Lente × Función

| # | Pensamiento | Lente 1ª | Función 1ª | Razonamiento que usa |
|---|---|---|---|---|
| P01 | Lateral | Se | F6 | Analogía, Contrafactual |
| P02 | Sistémico | Se | F4, F5 | Causal, Abducción, Dialéctico |
| P03 | Crítico | Se | F3, F5 | Deducción, Eliminación, Bayesiano |
| P04 | Diseño | S+Se | F5→F2→F16→F3 | Abducción, Inducción, Transducción |
| P05 | Primeros principios | Se | F3, F1 | Deducción, Retroducción, Eliminación |
| P06 | Divergente | Se | F2, F6 | Analogía, Contrafactual |
| P07 | Convergente | S | F3, F4 | Deducción, Eliminación, Bayesiano |
| P08 | Metacognición | Se | F3, F5 | Modal, Contrafactual |
| P09 | Prospectivo | C | F7, F6 | Contrafactual, Bayesiano, Modal |
| P10 | Reflexivo | Se+C | F1, F3 | Inducción, Abducción, Causal |
| P11 | Encarnado | S | F1 | Transducción, Abducción |
| P12 | Narrativo | Se+C | F5, F7 | Causal, Analogía |
| P13 | Computacional | S+C | F4, F7 | Deducción, Eliminación, Inducción |
| P14 | Estratégico | S+Se | F4, F6 | Contrafactual, Bayesiano, Deducción |
| P15 | Integrativo | Se | F5, F6 | Dialéctico, Modal, Retroductivo |

---

## PARTE 3: CRUCE TRIPLE — PENSAMIENTO × RAZONAMIENTO × PERFIL PATOLÓGICO

### 3.1 ¿Qué herramientas cognitivas transforman cada perfil?

| Perfil | Pensamientos clave | Razonamientos clave | Por qué |
|--------|-------------------|---------------------|---------|
| **Operador ciego** (S↑Se↓C↓) | P05 Primeros principios, P03 Crítico, P08 Metacognición | R03 Abducción, R09 Eliminación, R08 Dialéctico | Necesita CUESTIONAR premisas. Los 3 pensamientos rompen la ceguera. |
| **Visionario atrapado** (S↓Se↑C↓) | P04 Diseño, P13 Computacional, P07 Convergente | R01 Deducción, R12 Transducción, R07 Bayesiano | Necesita EJECUTAR. Los 3 pensamientos van de comprensión a acción. |
| **Zombi inmortal** (S↓Se↓C↑) | P05 Primeros principios, P08 Metacognición, P01 Lateral | R10 Retroductivo, R03 Abducción, R11 Modal | Necesita CUESTIONAR SU EXISTENCIA. ¿Es necesario o contingente? |
| **Genio mortal** (S↑Se↑C↓) | P12 Narrativo, P13 Computacional, P04 Diseño | R04 Analogía, R12 Transducción, R01 Deducción | Necesita TRANSFERIR. Narrativa + algoritmización + prototipo transferible. |
| **Autómata eterno** (S↑Se↓C↑) | P08 Metacognición, P09 Prospectivo, P01 Lateral | R03 Abducción, R06 Contrafactual, R10 Retroductivo | Necesita VER LO INVISIBLE. Metacognición + prospectiva detectan el riesgo oculto. |
| **Potencial dormido** (S↓Se↑C↑) | P11 Encarnado, P04 Diseño, P14 Estratégico | R12 Transducción, R01 Deducción, R07 Bayesiano | Necesita MOVER EL CUERPO. Pensamiento encarnado rompe parálisis. |
| **E1 Muerte simétrica** | P12 Narrativo, P06 Divergente, P11 Encarnado | R03 Abducción, R04 Analogía, R12 Transducción | Necesita UNA PRIMERA CHISPA. Narrativa + divergente + cuerpo. |
| **E2 Latencia** | P03 Crítico, P02 Sistémico, P05 Primeros principios | R03 Abducción, R05 Causal, R08 Dialéctico | Necesita SECUENCIA CORRECTA. Pensamiento crítico evita activar lo incorrecto primero. |

---

## PARTE 4: IMPLICACIÓN PARA EL MOTOR — PIPELINE TRIPLE

```
PASO 0:   Perfil de lentes (S_avg, Se_avg, C_avg) + Gradiente
PASO 0.5: Estado de equilibrio (E1-E4) o perfil de desequilibrio (6 perfiles)

PASO 1:   Seleccionar INTELIGENCIAS según perfil (18 INT × lente faltante)
            ↓ NUEVO ↓
PASO 1.5: Seleccionar TIPOS DE PENSAMIENTO según perfil
           - Operador ciego → Primeros principios + Crítico + Metacognición
           - Visionario → Diseño + Computacional + Convergente
           - etc.
            ↓ NUEVO ↓
PASO 1.7: Seleccionar TIPOS DE RAZONAMIENTO según perfil
           - Operador ciego → Abducción + Eliminación + Dialéctico
           - Visionario → Deducción + Transducción + Bayesiano
           - etc.

PASO 2:   Tipo Lógico (Nivel 1-5) + Modo conceptual (ENMARCAR/MOVER/etc.)
PASO 3:   Ejecutar secuencia (Se→S→C)
PASO 4:   Evaluar resultado
```

**El Motor ahora selecciona 3 cosas, no 1:**
1. Inteligencias (QUÉ observar)
2. Pensamiento (CÓMO organizar el proceso)
3. Razonamiento (CÓMO inferir conclusiones)

Las 3 selecciones dependen del PERFIL DE LENTES del caso.

---

## PARTE 5: LEYES EMERGENTES

### LEY TP1: El razonamiento y el pensamiento tienen afinidad de lente igual que las inteligencias

No son neutros. Cada tipo de razonamiento y pensamiento genera preferentemente una lente sobre otra. El Motor debe seleccionar herramientas cognitivas que generen la lente faltante.

### LEY TP2: El sistema cognitivo (18 INT + 12 R + 15 P) está sesgado hacia Se

- 10/18 inteligencias generan Se
- 8/12 razonamientos generan Se
- 10/15 pensamientos generan Se

**Esto NO es un defecto — es coherente.** Se es la lente más escasa (H13) y más difícil de generar (H23). El sistema cognitivo necesita más herramientas de comprensión que de ejecución porque la comprensión es lo más escaso.

### LEY TP3: S se genera por HACER, Se se genera por CUESTIONAR, C se genera por ENSEÑAR

```
Para generar S: usar pensamientos de acción (Diseño, Computacional, Encarnado)
                con razonamientos operativos (Deducción, Transducción, Bayesiano)
                
Para generar Se: usar pensamientos de cuestionamiento (Crítico, Primeros principios, Metacognición)
                 con razonamientos de comprensión (Abducción, Dialéctico, Retroductivo)
                 
Para generar C: usar pensamientos de transferencia (Narrativo, Computacional, Prospectivo)
                con razonamientos de transferencia (Analogía, Inducción, Modal)
```

### LEY TP4: Los tipos de pensamiento operan en NIVELES LÓGICOS distintos

| Pensamiento | Nivel Lógico predominante |
|---|---|
| Encarnado, Computacional | Nivel 1 (Conductas) |
| Narrativo, Divergente, Convergente | Nivel 2 (Interpretaciones) |
| Crítico, Lateral, Estratégico, Diseño | Nivel 3 (Criterios) |
| Sistémico, Primeros principios, Integrativo | Nivel 4 (Reglas) |
| Metacognición, Prospectivo, Reflexivo | Nivel 5 (Gobierno) |

**El Motor debe seleccionar pensamiento del NIVEL LÓGICO correcto para el perfil:**
- Perfiles que necesitan S → Nivel 1-2 (bajar a acción)
- Perfiles que necesitan Se → Nivel 3-5 (subir a comprensión/gobierno)
- Perfiles que necesitan C → Nivel 4-5 (codificar/anticipar)

---

## ARCHIVOS

```
motor-semantico/results/reactor_v5/
  taxonomia_pensamiento_razonamiento.md  ← ESTE DOCUMENTO
```
