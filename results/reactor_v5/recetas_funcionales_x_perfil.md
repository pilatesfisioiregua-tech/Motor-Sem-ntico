# RECETAS FUNCIONALES POR PERFIL DE LENTES

**Fecha:** 2026-03-19  
**Dependencia:** `desequilibrio_lentes.md`, `reactor_v5_2_lentes.json`, 50 pares v5  
**Pregunta:** Para cada perfil de desequilibrio (y para el equilibrio), ¿qué configuraciones de funciones lo producen?

---

## 0. EL MARCO ALGEBRAICO

Un perfil de lentes (ej: S↑ Se↓ C↓ = Operador ciego) es un RESULTADO.
Las funciones (F1-F7) y sus relaciones son los OPERANDOS.
Las "recetas" son las combinaciones de funciones que producen ese resultado.

```
Perfil de lentes = f(F1, F2, F3, F4, F5, F6, F7, relaciones_entre_ellas)
```

Igual que 10 = 5+5 = 3+7 = 2×5, un mismo perfil puede emerger de configuraciones funcionales distintas. Esto tiene una implicación ENORME: **el diagnóstico por lentes te dice QUÉ falla, las recetas te dicen POR QUÉ falla de esa manera específica, y eso determina la intervención.**

---

## 1. OPERADOR CIEGO (S↑ Se↓ C↓) — "Funciona sin saber por qué ni para cuándo"

### Receta 1: F1↑↑ + F3↓ + F5↓ — "INERCIA ACUMULATIVA"

```
F1 alta (conserva mucho) + F3 baja (no depura) + F5 baja (sin identidad)
→ S sube porque F1 mantiene operatividad
→ Se baja porque sin F5 no hay propósito y sin F3 no hay criterio
→ C baja porque sin F5 nada es transferible
```

**Mecanismo:** El sistema funciona porque CONSERVA lo que siempre funcionó (F1.S↑). No depura (F3↓) así que no cuestiona. No tiene identidad (F5↓) así que no tiene rumbo. Es una máquina que repite por inercia.

**Casos:** Maginot (F10) parcialmente. Lumbalgia-reposo (S05). Kodak pre-crisis en el bloque película.

**Intervención específica:** F3.Se (cuestionar POR QUÉ conservas esto) → que emerja F5.Se.

---

### Receta 2: F2↑↑ + F3↓ + F5↓ — "INTOXICACIÓN OPERATIVA"

```
F2 alta (capta mucho) + F3 baja (no filtra) + F5 baja (sin frontera)
→ S sube porque F2 trae recursos que operan hoy
→ Se baja porque captas sin saber por qué (F2.Se↓) y sin identidad (F5↓)
→ C baja porque sin F5 la captación no es sostenible
```

**Mecanismo:** El sistema funciona porque CAPTA agresivamente (F2.S↑). Pero la captación es indiscriminada (F2.Se↓). Sin F3 no filtra lo que sobra. Sin F5 no sabe qué debería captar.

**Casos:** WeWork (N03), Theranos (T08), Opioides (S03), Sobreentrenamiento (S10), Burnout médico (M04). **ES EL PATRÓN MÁS FRECUENTE DEL DATASET (14/50 = intoxicado).**

**Intervención específica:** F3.S+Se (empezar a filtrar con criterio) PRIMERO, luego F5.Se (definir quién eres).

---

### Receta 3: F7↑↑ + F5↓ + F3↓ — "REPLICACIÓN MECÁNICA"

```
F7 alta (replica mucho) + F5 baja (sin identidad) + F3 baja (sin depuración)
→ S sube porque la réplica funciona operativamente
→ Se baja porque F7.Se es baja (copian sin entender) y F5 no da propósito
→ C paradójicamente puede ser alta (la réplica persiste) O baja (la réplica es frágil)
```

**Mecanismo:** El sistema funciona porque REPLICA operaciones (F7.S↑). Pero nadie entiende por qué se replica (F7.Se↓). Sin F5 no hay identidad que guíe la réplica. Sin F3 no se filtra qué replicar.

**Casos:** DARE (F02), Lobotomía (F08), Boeing autocertificación (T06). Franquicias mecánicas en general.

**Intervención específica:** DETENER F7 primero (dejar de replicar). Luego F5.Se (definir qué debería replicarse). Luego F3.Se (depurar lo replicado).

---

### Receta 4: F4↑ + F5↓ — "DISTRIBUCIÓN SIN BRÚJULA"

```
F4 funcional (distribuye recursos) + F5 baja (sin criterio de distribución)
→ S sube porque los recursos llegan (operativo)
→ Se baja porque nadie sabe POR QUÉ se distribuye así
→ C variable
```

**Mecanismo:** La logística funciona (F4.S↑) pero sin F5 no hay criterio de priorización. Los recursos llegan pero a lugares equivocados o sin propósito.

**Casos:** Healthcare.gov (T04) — 55 contratistas distribuyendo código sin saber quién hacía qué. War on Drugs (M03) — $51B/año distribuidos sin impacto.

**Intervención específica:** F5.Se (definir POR QUÉ y A QUIÉN distribuir) antes de mejorar F4.S.

---

### SÍNTESIS OPERADOR CIEGO

| Receta | Fórmula | Frecuencia | Intervención |
|--------|---------|------------|-------------|
| Inercia acumulativa | F1↑↑ + F3↓ + F5↓ | ~5 casos | F3.Se → F5.Se |
| Intoxicación operativa | F2↑↑ + F3↓ + F5↓ | ~14 casos | F3.S+Se → F5.Se |
| Replicación mecánica | F7↑↑ + F5↓ + F3↓ | ~3 casos | Detener F7, luego F5.Se |
| Distribución sin brújula | F4↑ + F5↓ | ~3 casos | F5.Se primero |

**Patrón común:** SIEMPRE hay F5↓ y/o F3↓. El operador ciego se construye por ausencia de sentido (F5) y ausencia de filtro (F3). Lo que varía es QUÉ función aporta la S (F1, F2, F4 o F7).

---

## 2. VISIONARIO ATRAPADO (S↓ Se↑ C↓) — "Comprende pero no puede"

### Receta 1: F5↑↑(Se) + F1↓ + F4↓ — "IDENTIDAD SIN MÚSCULO"

```
F5.Se alta (sabe quién es) + F1 baja (no conserva recursos) + F4 baja (no distribuye)
→ S baja porque F1 y F4 no operan
→ Se alta porque F5 da propósito claro
→ C baja porque sin F1 y F4 no hay base sostenible
```

**Mecanismo:** El sistema tiene identidad cristalina pero no tiene capacidad operativa. Sabe exactamente qué hacer pero carece de recursos, infraestructura, o capacidad de ejecución.

**Casos:** Startups pre-product con visión clara pero sin capital ni equipo. Un fisioterapeuta que sabe exactamente qué protocolo usar pero no tiene el equipo ni el tiempo.

**Intervención específica:** F1.S (estabilizar recursos mínimos) + F4.S (distribuir lo que hay) = MVP.

---

### Receta 2: F6↑(Se) + F1↑↑(S) + F6↓(S) — "RIGIDEZ CONSCIENTE" (Kodak)

```
F6.Se media (sabe que debe cambiar) + F1.S altísima (película funciona HOY) + F6.S bajísima (no PUEDE cambiar)
→ S alta en F1 pero S baja en F6 = S neta mixta, tendiendo a baja en la dimensión que importa
→ Se parcial porque F6.Se existe pero F1.Se MONOPOLIZA el sentido
→ C baja porque la adaptación no está sistematizada
```

**Mecanismo:** El sistema SABE que debe cambiar (F6.Se) pero la operatividad está atrapada en la conservación (F1.S domina). Es el innovador dentro de la corporación rígida.

**Casos:** Kodak (N02) — F6.S=0.10 con F6.Se=0.30. Sabían algo de por qué digital era el futuro pero no podían actuar.

**Intervención específica:** Romper el monopolio de F1.S creando una F1 paralela (skunkworks, spin-off). Netflix lo hizo: no destruyó DVD, creó streaming al lado.

---

### Receta 3: F3↑(Se) + F4↓ + F7↓ — "CRÍTICO SIN MANOS"

```
F3.Se alta (sabe qué eliminar) + F4 baja (no puede distribuir la corrección) + F7 baja (no puede replicar la mejora)
→ S baja porque no puede ejecutar la depuración a escala
→ Se alta porque F3 y quizás F5 dan comprensión
→ C baja porque sin F7 no hay mecanismo de transferencia
```

**Mecanismo:** El sistema ha diagnosticado correctamente el problema pero no tiene mecanismo para implementar la solución ni replicarla.

**Casos:** Crisis de replicabilidad (M09) parcialmente — supieron que el 64% no replicaba (diagnóstico correcto, F3.Se↑) pero la implementación (pre-registro obligatorio) es lenta (F4.S y F7.S bajas).

**Intervención específica:** F4.S (crear canales de distribución de la corrección) + F7.S (mecanizar la réplica de la mejora).

---

### SÍNTESIS VISIONARIO ATRAPADO

| Receta | Fórmula | Ejemplo | Intervención |
|--------|---------|---------|-------------|
| Identidad sin músculo | F5↑↑(Se) + F1↓ + F4↓ | Startup pre-product | F1.S + F4.S = MVP |
| Rigidez consciente | F6.Se + F1.S↑↑ bloqueando F6.S | Kodak | Romper monopolio F1: crear paralelo |
| Crítico sin manos | F3.Se↑ + F4↓ + F7↓ | Crisis replicabilidad | F4.S + F7.S = distribuir y replicar corrección |

**Patrón común:** SIEMPRE hay Se presente en alguna función (F5, F6, o F3). Lo que falta SIEMPRE es S en las funciones de ejecución (F1, F4, F7.S). El visionario tiene comprensión pero no capacidad operativa.

---

## 3. ZOMBI INMORTAL (S↓ Se↓ C↑) — "Persiste sin funcionar ni saber por qué"

### Receta 1: F7↑(C) + F1↑(C) + F5↓ + F3↓ — "INSTITUCIÓN MUERTA"

```
F7.C alta (la réplica es institucional) + F1.C alta (se conserva por burocracia) + F5 baja + F3 baja
→ S baja porque nada funciona realmente
→ Se baja porque nadie sabe POR QUÉ existe
→ C alta porque la maquinaria institucional es autoperpetuante
```

**Mecanismo:** El sistema sobrevive porque tiene INERCIA INSTITUCIONAL (F1.C + F7.C). No funciona (S↓) y nadie cuestiona (Se↓) pero persiste porque las instituciones tienen mecanismos de autopreservación.

**Casos:** DARE (F02) — programa sin efecto que persistió 26 años. War on Drugs (M03) — $51B/año durante décadas sin impacto. Burocracia en general.

**Intervención específica:** F3.Se (cuestionar POR QUÉ existe) → si la respuesta es insatisfactoria → ELIMINAR (F3.S). El zombi necesita una auditoría existencial seguida de la valentía de matarlo.

---

### Receta 2: F1↑(C) + F6↓ + F5↓ — "RELIQUIA"

```
F1.C alta (se conserva por historia) + F6 baja (no se adapta) + F5 baja (no sabe qué es)
→ S baja porque lo conservado ya no opera en el contexto actual
→ Se baja porque la razón original se ha olvidado
→ C alta porque la conservación histórica persiste
```

**Mecanismo:** El sistema fue relevante hace tiempo. Se conserva por tradición (F1.C) pero ya no funciona en el presente (F1.S baja). Nadie recuerda por qué existe (Se↓). No se adapta al nuevo contexto (F6↓).

**Casos:** Protocolos médicos obsoletos que se siguen por tradición. Pilates genérico (S08) parcialmente — el método persiste pero desconectado del problema específico del paciente.

**Intervención específica:** F6.Se (preguntarse: ¿HACIA DÓNDE debería adaptarse esto?) → F5.Se (redefinir identidad para el contexto actual) → o eliminar si no hay respuesta.

---

### Receta 3: F2↓ + F7↑(C) + F3↓ — "COPIA DESCONECTADA"

```
F2 baja (no capta nada nuevo) + F7.C alta (sigue replicándose) + F3 baja (no depura)
→ S baja porque sin F2 nueva no hay input operativo fresco
→ Se baja porque sin F3 no hay cuestionamiento ni criterio
→ C alta porque F7.C sigue replicando la copia indefinidamente
```

**Mecanismo:** El sistema dejó de captar input nuevo (F2↓) pero sigue replicándose (F7.C↑). Es una fotocopia de una fotocopia: cada generación más degradada pero la máquina sigue haciendo copias.

**Casos:** Lobotomía en fase tardía (F08) — procedimiento que se seguía replicando sin nuevos datos y sin cuestionamiento. "Así se ha hecho siempre."

**Intervención específica:** F2.Se (captar con propósito: ¿qué evidencia nueva existe?) → F3.Se (filtrar a la luz de la evidencia) → decisión: continuar o matar.

---

### SÍNTESIS ZOMBI INMORTAL

| Receta | Fórmula | Ejemplo | Intervención |
|--------|---------|---------|-------------|
| Institución muerta | F7.C↑ + F1.C↑ + F5↓ + F3↓ | DARE, War on Drugs | F3.Se: auditoría existencial → matar o reconstruir |
| Reliquia | F1.C↑ + F6↓ + F5↓ | Protocolos obsoletos | F6.Se + F5.Se: ¿puede adaptarse? |
| Copia desconectada | F2↓ + F7.C↑ + F3↓ | Lobotomía tardía | F2.Se: nuevo input → F3.Se: filtrar |

**Patrón común:** SIEMPRE hay alguna función con C alta (F1.C o F7.C) que provee la persistencia. SIEMPRE hay F3↓ y F5↓ (sin depuración ni identidad). La C viene de la institucionalización, no de la calidad.

**INSIGHT:** El zombi inmortal se distingue del operador ciego en QUÉ lente domina. El operador ciego tiene S↑ (funciona hoy). El zombi tiene C↑ (persiste). La diferencia es temporal: el operador ciego está vivo pero ciego; el zombi ya está muerto pero sigue moviéndose.

---

## 4. GENIO MORTAL (S↑ Se↑ C↓) — "Brillante pero intransferible"

### Receta 1: F5↑↑(S,Se) + F7↓ + F1↓(C) — "ARTISTA IRREPETIBLE"

```
F5.S+Se altísimas (identidad clara y comprendida) + F7 baja (no puede replicar) + F1.C baja (lo conservado depende del individuo)
→ S alta porque el sistema opera brillantemente cuando el portador está
→ Se alta porque la comprensión es profunda
→ C baja porque NADA sobrevive sin el individuo
```

**Mecanismo:** Todo el sistema gira alrededor de UNA persona/configuración irrepetible. La identidad (F5) es brillante pero personal. La replicación (F7) es imposible porque el conocimiento es tácito/encarnado.

**Casos:** El Bulli (N09) — CASO CANÓNICO. F5.S=0.90, F5.Se=0.95, F5.C=0.15. Adrià era El Bulli.

**Intervención específica:** F7.Se (hacer que OTROS comprendan POR QUÉ funciona — no solo el CÓMO) + codificación progresiva (documentar, enseñar, crear protocolos). Requiere que el genio INVIERTA tiempo en enseñar en vez de hacer.

---

### Receta 2: F6↑↑(S,Se) + F7↓ + F1↓(C) — "INNOVADOR INCANSABLE"

```
F6.S+Se altísimas (adapta constantemente con propósito) + F7 baja + F1.C baja
→ S alta porque la adaptación constante mantiene relevancia
→ Se alta porque sabe por qué adapta
→ C baja porque cada adaptación depende del innovador y no se sistematiza
```

**Mecanismo:** El sistema está en constante evolución creativa (F6↑↑) pero cada iteración depende del creador. No hay sistematización (F7↓). El éxito de hoy no garantiza el de mañana porque depende de que el innovador siga innovando.

**Casos:** El Bulli también encaja aquí (F6.S=0.80, F6.Se=0.80). Startups en fase de "founder-market fit" donde el fundador ES el producto.

**Intervención específica:** Misma que Receta 1: F7.Se+C. Adicionalmente: F1.C (conservar las innovaciones que funcionan en vez de reinventar todo cada vez).

---

### Receta 3: F2↑↑(S,Se) + F3↑(S,Se) + F7↓ — "ANALISTA BRILLANTE SIN IMPACTO"

```
F2.S+Se altas (capta e identifica brillantemente) + F3.S+Se altas (depura con maestría) + F7 baja
→ S alta porque el análisis y filtrado son excelentes
→ Se alta porque la comprensión es profunda
→ C baja porque nada de esto se replica ni transfiere
```

**Mecanismo:** El sistema es brillante en diagnóstico (F2+F3) pero no produce OUTPUT replicable (F7↓). Es el consultor que hace análisis perfectos que nadie implementa.

**Casos:** Perelman (T05) parcialmente — resolvió Poincaré pero rechazó sistematizar o difundir. (Aunque en su caso F7 sí fue alta porque publicó en arXiv — el "genio mortal" habría sido si no hubiera publicado.)

**Intervención específica:** F7.S+Se+C (producir output utilizable por otros: publicar, enseñar, crear herramientas).

---

### Receta 4: F3↑↑(S,Se) + F5↑(Se) + F4↓ — "DEPURADOR AISLADO"

```
F3 altísima (depura brillantemente) + F5 con Se (identidad clara) + F4 baja (no distribuye)
→ S alta en diagnóstico y limpieza, pero sin distribución el impacto es local
→ Se alta porque sabe qué eliminar y por qué
→ C baja porque sin F4 la depuración no llega a escala
```

**Mecanismo:** El sistema hace limpieza excelente en su perímetro local pero no tiene canales de distribución. Es el departamento de calidad que identifica todos los defectos pero cuyas recomendaciones no llegan a producción.

**Casos:** Virginia Mason PRE-expansión (S04) — si el sistema kaizen se hubiera quedado en un departamento sin F4 ni F7.

**Intervención específica:** F4.S+C (crear canales de distribución) + F7.S+C (mecanizar la réplica del proceso de depuración).

---

### SÍNTESIS GENIO MORTAL

| Receta | Fórmula | Ejemplo | Intervención |
|--------|---------|---------|-------------|
| Artista irrepetible | F5↑↑(S,Se) + F7↓ | El Bulli | F7.Se+C: enseñar POR QUÉ |
| Innovador incansable | F6↑↑(S,Se) + F7↓ | Fundador-startup | F7.Se+C + F1.C: conservar innovaciones |
| Analista sin impacto | F2+F3↑↑(S,Se) + F7↓ | Consultor brillante | F7: producir output replicable |
| Depurador aislado | F3↑↑ + F5↑ + F4↓ | Dept. calidad aislado | F4 + F7: distribuir y replicar |

**Patrón común:** SIEMPRE hay F7↓ como denominador. El genio mortal es SIEMPRE un problema de F7. Lo que varía es QUÉ función es brillante (F5, F6, F2+F3) y eso determina dónde está el genio que no se transfiere.

**LEY EMERGENTE: C↓ en todos los perfiles de genio mortal se explica por F7↓. F7 es la función que PRODUCE C.** Esto confirma el hallazgo de v5.2: L_Continuidad ≈ F7 distribuida.

---

## 5. AUTÓMATA ETERNO (S↑ Se↓ C↑) — "El más peligroso: funciona y persiste sin comprender"

### Receta 1: F1↑↑(S,C) + F7↑↑(S,C) + F5↓(Se) + F3↓(Se) — "MÁQUINA INSTITUCIONAL"

```
F1.S+C altísimas (conserva y persiste) + F7.S+C altísimas (replica y persiste) + F5.Se baja + F3.Se baja
→ S alta porque F1 y F7 operan
→ Se baja porque nadie cuestiona (F3.Se↓) ni tiene identidad profunda (F5.Se↓)
→ C alta porque F1.C y F7.C son institucionales
```

**Mecanismo:** El sistema se conserva (F1) y se replica (F7) operativa e institucionalmente, pero sin comprensión (Se baja generalizada). Es la gran corporación que funciona por procesos, persiste por inercia, y nadie dentro entiende realmente por qué hace lo que hace.

**Casos:** Maginot en su apogeo (F10). Google+ (F01) — toda la maquinaria Google funcionaba (S) y era institucional (C) pero nadie entendía POR QUÉ G+ existía (Se↓).

**Intervención específica:** F3.Se (cuestionar: ¿por qué hacemos esto?) + F5.Se (redefinir: ¿quiénes somos realmente?). URGENTE — antes de que el contexto cambie y todo colapse.

---

### Receta 2: F7↑↑(S,C) + F5.S↑ + F5.Se↓ — "FRANQUICIA SIN ALMA"

```
F7 altísima en S+C (replica y persiste) + F5 operativamente definida (S alta) pero sin comprensión (Se baja)
→ S alta porque la réplica funciona y F5 da forma operativa
→ Se baja porque F5.Se es baja — siguen el manual pero no entienden la filosofía
→ C alta porque F7.C es institucional
```

**Mecanismo:** Hay una identidad FORMAL (F5.S: podemos decir "somos X") y la replicación funciona (F7.S+C), pero la comprensión profunda se perdió (F5.Se baja). Es la franquicia que sigue el manual al pie de la letra sin entender por qué cada paso importa.

**Casos:** Este es el patrón que PRODUCE la degradación de El Bulli si hipotéticamente Adrià hubiera franquiciado sin enseñar POR QUÉ. También: F7→F6(D*) del análisis semántico — replicación rígida que inhibe adaptación.

**Intervención específica:** F7.Se↑ (formación profunda: enseñar POR QUÉ, no solo CÓMO) + F5.Se↑ (comprender la filosofía, no solo la forma).

---

### Receta 3: F4↑(S,C) + F1↑(S,C) + F6↓ + F3↓(Se) — "LOGÍSTICA PERFECTA SIN RUMBO"

```
F4 alta en S+C (distribuye bien y persiste) + F1 alta en S+C + F6 baja + F3.Se baja
→ S alta porque la operativa funciona
→ Se baja porque sin F3.Se no hay cuestionamiento y sin F6 no hay dirección de cambio
→ C alta porque F4.C y F1.C son institucionales
```

**Mecanismo:** La cadena de suministro funciona perfectamente (F4.S↑, F1.S↑) y está institucionalizada (C↑), pero nadie cuestiona hacia dónde va (F6↓) ni por qué se distribuye así (F3.Se↓). Es la empresa que entrega el producto equivocado con logística impecable.

**Casos:** Boeing pre-MAX (T06) parcialmente — la maquinaria de certificación funcionaba y persistía, pero la comprensión de por qué los protocolos de seguridad importaban se había erosionado.

**Intervención específica:** F3.Se (auditoría: ¿por qué hacemos esto?) + F6.Se (¿hacia dónde deberíamos ir?).

---

### SÍNTESIS AUTÓMATA ETERNO

| Receta | Fórmula | Ejemplo | Intervención |
|--------|---------|---------|-------------|
| Máquina institucional | F1+F7↑↑(S,C) + F5.Se↓ + F3.Se↓ | Maginot, Google+ | F3.Se + F5.Se: cuestionar y redefinir |
| Franquicia sin alma | F7↑↑(S,C) + F5.S↑ + F5.Se↓ | Franquicia mecánica | F7.Se + F5.Se: enseñar POR QUÉ |
| Logística sin rumbo | F4+F1↑↑(S,C) + F6↓ + F3.Se↓ | Boeing pre-crisis | F3.Se + F6.Se: auditoría + dirección |

**Patrón común:** SIEMPRE hay Se↓ GENERALIZADA con S y C altas en funciones operativas/institucionales. Lo que FALTA siempre es COMPRENSIÓN. Las funciones aportan S y C pero NO Se. **F3.Se y F5.Se son SIEMPRE la intervención.**

**POR QUÉ ES EL MÁS PELIGROSO:** En los otros perfiles, algo falla VISIBLEMENTE (S baja → no funciona, C baja → no persiste). En el autómata, TODO funciona y persiste. La enfermedad (Se↓) es INVISIBLE hasta que el contexto cambia y el sistema no puede adaptarse porque nadie entiende la lógica interna.

---

## 6. POTENCIAL DORMIDO (S↓ Se↑ C↑) — "Todo listo excepto la ejecución"

### Receta 1: F5↑↑(Se,C) + F1↓(S) + F4↓(S) — "IDENTIDAD DOCUMENTADA INACTIVA"

```
F5.Se+C altísimas (identidad clara, transmisible) + F1.S baja + F4.S baja
→ S baja porque F1 no estabiliza y F4 no distribuye
→ Se alta porque F5.Se da propósito
→ C alta porque F5.C hace la identidad transferible y F5 está documentada
```

**Mecanismo:** El sistema sabe quién es (F5.Se) y lo ha documentado (F5.C), pero no puede operar hoy (F1.S, F4.S bajas). Es el plan estratégico perfecto en el cajón.

**Casos:** TCP/IP pre-implementación (T10) parcialmente — la idea y el RFC process existían, faltaba implementar.

**Intervención específica:** F1.S (estabilizar mínimo) + F4.S (distribuir) → EJECUTAR. NO más planificación.

---

### Receta 2: F3↑↑(Se,C) + F5↑(Se,C) + F2↓(S) — "DEPURACIÓN SISTEMATIZADA SIN INPUT"

```
F3.Se+C altas (sabe qué eliminar y lo ha sistematizado) + F5 clara + F2.S baja (no capta input nuevo)
→ S baja porque sin F2.S no hay materia prima
→ Se alta porque F3.Se y F5.Se dan comprensión
→ C alta porque F3.C y F5.C son sistémicas
```

**Mecanismo:** El sistema tiene excelentes filtros (F3) y sabe quién es (F5), pero no recibe input (F2↓). Es el sistema de control de calidad perfecto en una fábrica parada.

**Casos:** El Bulli Foundation (N09 post) parcialmente — excelente archivo y comprensión, pero sin restaurante activo.

**Intervención específica:** F2.S (activar captación) → el sistema ya tiene todo lo demás para procesarlo.

---

### Receta 3: F7↑(Se,C) + F6↑(Se) + F1↓(S) — "MÉTODO LISTO SIN ARRANQUE"

```
F7.Se+C altas (método replicable comprendido) + F6.Se alta (sabe hacia dónde ir) + F1.S baja
→ S baja porque no ha arrancado
→ Se alta porque la comprensión y la dirección existen
→ C alta porque el método es transferible
```

**Mecanismo:** Todo está preparado — el método, la comprensión, la dirección del cambio — pero el primer paso no se da. Es el emprendedor con business plan, equipo, y funding que no lanza.

**Casos:** Protocolos médicos basados en evidencia que tardan 17 años en adoptarse (gap evidencia-práctica en salud).

**Intervención específica:** F1.S — LA PRIMERA ACCIÓN. Romper la inercia. MVP. Día 1.

---

### SÍNTESIS POTENCIAL DORMIDO

| Receta | Fórmula | Ejemplo | Intervención |
|--------|---------|---------|-------------|
| Identidad documentada inactiva | F5↑↑(Se,C) + F1↓(S) + F4↓(S) | Plan en cajón | F1.S + F4.S: ejecutar |
| Depuración sin input | F3+F5↑↑(Se,C) + F2↓(S) | QC en fábrica parada | F2.S: captar materia prima |
| Método listo sin arranque | F7+F6↑↑(Se,C) + F1↓(S) | Emprendedor paralizado | F1.S: la primera acción |

**Patrón común:** SIEMPRE hay S↓ como denominador con Se y C ya construidas. **La intervención es SIEMPRE operativa: HACER.** No más planificación, no más sistematización — acción.

**INSIGHT CRUCIAL:** Este es el ÚNICO perfil donde la intervención no requiere cambiar la comprensión (Se ya alta) ni la sistematización (C ya alta). Solo requiere ACTIVACIÓN. Pero es engañoso: la activación parece trivial ("solo hazlo") pero hay resistencia psicológica (miedo al fracaso, perfeccionismo, análisis-parálisis) que bloquea F1.S.

---

## 7. SISTEMA SANO (S↑ Se↑ C↑) — ¿Qué configuraciones lo producen?

### Receta 1: F3↑↑(Se) → F5↑↑(Se) → F7↑↑(Se,C) — "CADENA DE SENTIDO COMPLETA"

```
F3.Se alta (depurar con criterio) → genera F5.Se (identidad comprendida) → habilita F7.Se+C (replicación con comprensión + persistencia)
→ S emerge porque el sentido guía la operación
→ Se alta por construcción (F3.Se→F5.Se→F7.Se)
→ C alta porque F7.C transfiere
```

**Mecanismo:** La cadena causal F3.Se→F5.Se→F7.Se es la que CONSTRUYE el equilibrio. El sentido nace de la depuración (sé POR QUÉ elimino → sé QUIÉN SOY → puedo ENSEÑAR por qué), y la continuidad nace de la replicación con comprensión.

**Casos:** KonMari (M08), Toyota (N01), DPP (S09), TCP/IP (T10), CRISPR (T07), Mercadona (N04).

**ESTA ES LA RECETA MAESTRA DE CIERRE.** Los 6 cierres más limpios del dataset siguen esta cadena.

---

### Receta 2: F5↑↑(S,Se,C) + F6↑(Se) + F3↑(S) — "IDENTIDAD FUERTE + ADAPTACIÓN DIRIGIDA"

```
F5 altísima en las 3 lentes + F6.Se alta (sabe hacia dónde adaptar) + F3.S operativa
→ S alta porque F5.S da operatividad y F3.S limpia
→ Se alta porque F5.Se da propósito y F6.Se da dirección
→ C alta porque F5.C es transferible
```

**Mecanismo:** La identidad es la palanca maestra. Cuando F5 es alta en las 3 lentes, todo lo demás se alinea. F6 con Se sabe HACIA DÓNDE adaptar (dentro de la identidad). F3 limpia lo que no encaja.

**Casos:** Patagonia (N07) — F5.Se=0.90 pre, la identidad guiaba TODO. Netflix (N05) — adaptó (F6↑) manteniendo identidad (F5↑). Inditex (N10) — F5.Se clara ("moda accesible") con F6↑↑.

---

### Receta 3: F2↑(Se) + F3↑(Se) + F4↑(Se) + F5↑(Se) — "SENTIDO DISTRIBUIDO"

```
Todas las funciones operativas con Se alta = sentido generalizado
→ S alta porque las funciones operan CON propósito (más eficientes)
→ Se alta por construcción
→ C alta porque el sentido compartido es más transferible que la operación pura
```

**Mecanismo:** No depende de UNA función estrella. El sentido está distribuido en todo el sistema. Cada función sabe POR QUÉ hace lo que hace. Esto es más robusto que tener una función dominante.

**Casos:** TCP/IP post (T10) — Se promedio=0.69, la más alta del dataset. Cuba (S01) — sistema preventivo donde cada nivel comprende su rol. Finlandia educación (M02) — profesores autónomos que comprenden la filosofía.

---

### Receta 4: F3_diseño + F5↑ + F7↑ — "DEPURACIÓN INTEGRADA"

```
F3 integrada en el diseño del sistema (no correctiva) + F5 clara + F7 funcional
→ S alta porque F3 automática mantiene limpio
→ Se alta porque el diseño incorpora la comprensión
→ C alta porque F3 automática persiste sin intervención humana
```

**Mecanismo:** La depuración no es un acto deliberado sino una PROPIEDAD del sistema. Lotes pequeños (Inditex), protocolos (TCP/IP), ejercicios adaptativos (Khan Academy), peer review integrado (ciencia sana).

**Casos:** Inditex (N10), TCP/IP (T10), Khan Academy (M05). Los 3 casos de "F3 por diseño" del dataset.

**ESTE ES EL NIVEL MÁS ALTO DE EQUILIBRIO:** El sistema no necesita intervención correctiva porque la corrección es automática. Es homeostasis.

---

### SÍNTESIS SISTEMA SANO

| Receta | Fórmula | Ejemplo | Característica |
|--------|---------|---------|----------------|
| Cadena de sentido | F3.Se→F5.Se→F7.Se+C | KonMari, Toyota, DPP | La más frecuente. Depurar→Identidad→Replicar |
| Identidad + adaptación | F5↑↑(3L) + F6.Se + F3.S | Patagonia, Netflix, Inditex | F5 como palanca maestra |
| Sentido distribuido | Se alta en todas las F | TCP/IP, Cuba, Finlandia | La más robusta. No depende de 1 función |
| Depuración integrada | F3_diseño + F5 + F7 | Inditex, TCP/IP, Khan | Homeostasis. Nivel más alto |

**HALLAZGO:** Las 4 recetas de equilibrio tienen un elemento común: **Se alta en las funciones críticas.** El equilibrio se construye POR el sentido. Sin Se, puedes tener S (opera) o C (persiste) pero no ambas con estabilidad.

---

## 8. TABLA CRUZADA: PERFIL × RECETA × INTERVENCIÓN

```
                    ┌─────────────────────────────────────────────────┐
                    │           QUÉ FUNCIÓN DOMINA (aporta S/Se/C)    │
                    ├─────────┬──────────┬──────────┬────────┬────────┤
                    │   F1    │   F2     │  F3+F5   │  F4    │  F7   │
┌───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ OPERADOR CIEGO    │ Inercia │ Intox.   │    —     │ Dist.  │ Replic.│
│ (S↑ Se↓ C↓)      │ acumul. │ operat.  │         │ s/brúj.│ mecán. │
│ INTERVENCIÓN      │ F3.Se   │ F3.S+Se  │    —     │ F5.Se  │ STOP→  │
│                   │ →F5.Se  │ →F5.Se   │         │        │ F5.Se  │
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ VISIONARIO ATRAP. │   —     │    —     │ Crítico  │   —    │   —    │
│ (S↓ Se↑ C↓)      │         │          │ s/manos  │        │        │
│ INTERVENCIÓN      │ F1.S    │          │ F4.S+F7.S│        │        │
│                   │ MVP     │          │          │        │        │
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ ZOMBI INMORTAL    │ Reliquia│    —     │    —     │   —    │ Instit.│
│ (S↓ Se↓ C↑)      │         │          │          │        │ muerta │
│ INTERVENCIÓN      │ F3.Se:  │          │          │        │ F3.Se: │
│                   │ matar o │          │          │        │ matar o│
│                   │ reconstr│          │          │        │ reconst│
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ GENIO MORTAL      │    —    │   —      │ Depur.   │   —    │   —    │
│ (S↑ Se↑ C↓)      │         │          │ aislado  │        │        │
│ INTERVENCIÓN      │         │          │ F7.Se+C  │        │        │
│                   │         │          │ ENSEÑAR  │        │        │
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ AUTÓMATA ETERNO   │ Máquina │    —     │    —     │ Logíst.│ Franq. │
│ (S↑ Se↓ C↑)      │ instit. │          │          │ s/rumbo│ s/alma │
│ INTERVENCIÓN      │ F3.Se + │          │          │ F3.Se +│ F7.Se +│
│                   │ F5.Se   │          │          │ F6.Se  │ F5.Se  │
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ POTENCIAL DORMIDO │ Ident.  │ Depur.   │ Método   │   —    │   —    │
│ (S↓ Se↑ C↑)      │ inactiva│ s/input  │ s/arran. │        │        │
│ INTERVENCIÓN      │ F1.S +  │ F2.S     │ F1.S     │        │        │
│                   │ F4.S    │          │ HACER    │        │        │
├───────────────────┼─────────┼──────────┼──────────┼────────┼────────┤
│ SISTEMA SANO      │    —    │    —     │ Cadena   │   —    │ F3_    │
│ (S↑ Se↑ C↑)      │         │          │ sentido  │        │ diseño │
│ RECETA            │ —       │ —        │F3.Se→    │ —      │ Homeo- │
│                   │         │          │F5.Se→    │        │ stasis │
│                   │         │          │F7.Se+C   │        │        │
└───────────────────┴─────────┴──────────┴──────────┴────────┴────────┘
```

---

## 9. LEYES DE COMPOSICIÓN

### LEY C1: Cada función aporta SELECTIVAMENTE a las lentes

```
FUNCIÓN   APORTA FÁCILMENTE    APORTA CON DIFICULTAD
────────────────────────────────────────────────────
F1        S (conservar hoy)    Se (¿por qué conservo?)
F2        S (captar hoy)       Se (¿por qué capto esto?)
F3        Se (cuestionar)      S (ejecutar la depuración)
F4        S (distribuir hoy)   Se (¿por qué distribuyo así?)
F5        Se (identidad)       C (¿es transferible?)
F6        S (cambiar hoy)      Se (¿hacia dónde?)
F7        S+C (replicar)       Se (¿por qué se replica esto?)
```

**OBSERVACIÓN CLAVE:**
- F1, F2, F4, F6 aportan S fácilmente pero NO Se.
- F5 aporta Se fácilmente pero NO C.
- F7 aporta S+C fácilmente pero NO Se.
- **F3 es la ÚNICA función que aporta Se de manera natural** (cuestionar genera comprensión).

Esto explica por qué F3 es la palanca maestra en tantos cierres: es la ÚNICA fuente natural de Se en el sistema.

### LEY C2: F7 multiplica el perfil, no lo cambia

```
F7 × (S↑ Se↓ C↓) = más S, más C parcial, Se igual o menor
F7 × (S↑ Se↑ C↑) = más S, más C, Se mantenida (si F7.Se activa)
```

F7 NUNCA genera Se. Solo puede TRANSMITIR Se si F7.Se está activa (enseñanza, no solo copia). Sin F7.Se activa, cada replicación DEGRADA Se del sistema.

### LEY C3: El equilibrio requiere al menos 3 funciones con Se activa

De los cierres del dataset:
- Toyota: F3.Se + F5.Se + F7.Se activas → cierre
- Mercadona: F5.Se + F3.Se + F7.Se → cierre
- TCP/IP: Se distribuida en 5+ funciones → cierre más robusto

De los inertes:
- Peloton: solo F3.Se parcial → inerte
- SSRI: 0 funciones con Se activa → inerte
- Kodak: solo F1.Se activa → inerte (monopolio)

**Umbral mínimo para cierre: 3 funciones con Se > 0.40.**

### LEY C4: La secuencia importa — Se primero, luego S, luego C

```
SECUENCIA CORRECTA:         SECUENCIA INCORRECTA:
1. F3.Se (cuestionar)       1. F7.S+C (escalar)
2. F5.Se (identidad)        2. F2.S (captar más)
3. F1.S+F4.S (ejecutar)     3. F1.S (conservar)
4. F7.Se+C (escalar)        → amplifica perfil enfermo
```

Los cierres del dataset SIEMPRE empiezan por Se (F3.Se o F5.Se). Los tóxicos empiezan por S (F2.S o F7.S) o C (F7.C).

### LEY C5: Los perfiles tienen "recetas preferentes" con distinta frecuencia

```
OPERADOR CIEGO:  Receta 2 (F2↑+F3↓+F5↓) es la MÁS FRECUENTE del dataset (14/50)
GENIO MORTAL:    Receta 1 (F5↑↑+F7↓) es la más frecuente
AUTÓMATA ETERNO: Receta 1 (F1+F7↑↑(S,C)+Se↓) es la más frecuente
ZOMBI INMORTAL:  Receta 1 (F7.C+F1.C↑↑+F3↓) es la más frecuente
```

**El patrón tóxico más frecuente de todo el dataset es F2↑↑+F3↓+F5↓ (intoxicación operativa).** Es el "operador ciego" producido por captación sin depuración ni identidad.

---

## 10. IMPLICACIÓN PARA EL MOTOR vN

### Pipeline de diagnóstico propuesto:

```
PASO 0: Calcular perfil de lentes (S_avg, Se_avg, C_avg)
PASO 1: Identificar perfil dominante (de los 6)
PASO 2: Identificar receta funcional (qué funciones producen este perfil)
PASO 3: Determinar intervención según receta específica (no solo según perfil)
PASO 4: Verificar pre-condiciones de F7 antes de recomendar escalar
PASO 5: Secuenciar intervención: Se primero → S → C
```

### Ejemplo completo de un paciente piloto:

```
Input: Pilates genérico para escoliosis (S08)
PASO 0: S=0.43, Se=0.27, C=0.27 → Se y C bajas
PASO 1: Perfil = OPERADOR CIEGO (S moderada, Se baja, C baja)
PASO 2: Receta = "Captación sin criterio" (F2↑ + F3↓ + F5↓)
         F2.S=0.50 (capta movimiento), F3=0.25, F5=0.25
PASO 3: Intervención = F3.Se (el paciente debe entender POR QUÉ ciertos
         ejercicios sirven y otros no para SU curva) → F5.Se (definir
         qué es "mejora" para este paciente específico)
PASO 4: NO escalar (F7) hasta que Se promedio > 0.40
PASO 5: Primero educación (Se), luego ejercicios específicos (S),
         luego protocolo de casa (C)
```

---

## ARCHIVOS

```
motor-semantico/results/reactor_v5/
  recetas_funcionales_x_perfil.md      ← ESTE DOCUMENTO
  desequilibrio_lentes.md              ← perfiles base
  reactor_v5_2_lentes.json             ← datos 3L
  reactor_v5_2_resumen.md              ← resumen v5.2
```
