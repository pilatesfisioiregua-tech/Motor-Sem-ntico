**CONEXIONES**

1. **Propuesta 1 (Step 3.5 Flash) dice** que el "Motor vN" es un pipeline de 7 pasos que ejecuta la Matriz. **Propuesta 3 (Kimi K2.5) dice** que el "Motor Ejecutor" es el agente de 460 líneas de Exp 6 reutilizado. **Propuesta 4 (DeepSeek V3.2) dice** que el "Motor Ejecutor" es el agente de Exp 6. **La conexión que nadie vio**: Todas usan el mismo agente de Exp 6, pero **ninguna discute cómo ese agente, diseñado para escribir código, se adapta a generar preguntas cognitivas**. El loop observe→think→act asume que "act" es escribir código, pero en OMNI-MIND "act" es generar una pregunta. Eso cambia el tipo de herramientas (no `write_file` sino `generate_question`) y el criterio de éxito (no tests de código, sino reducción de `gap`). Es una **reinterpretación de dominio** no validada.

2. **Propuesta 1 dice** que el "Gestor de la Matriz" asigna modelos y compila programas de preguntas. **Propuesta 5 (Nemotron Super) dice** que el "Gestor de la Matriz" compila el "programa de preguntas". **Propuesta 2 (Cogito 671B) dice** que el "Router de Modelos" asigna tareas. **La conexión que nadie vio**: El **Gestor y el Router son el mismo componente** con dos modos: (a) **modo compilación** (construye DAG de preguntas) y (b) **modo ejecución** (asigna modelos a celdas). Todas los separan, pero en la práctica son uno: el Gestor decide *qué pregunta生成* (compilación) y *qué modelo la genera* (routing). Eso simplifica la arquitectura.

3. **Propuesta 1 dice** que el "Reactor v4" genera preguntas desde datos de telemetría. **Propuesta 4 dice** que el "Reactor v4" lee APIs de software de gestión. **Propuesta 5 dice** que el "Reactor v4" es esencial para el flywheel. **La conexión que nadie vio**: El Reactor **no es un módulo separado**; es el **Gestor en modo generativo**. Cuando el Gestor ve un gap en una celda, busca en la DB preguntas efectivas para esa celda. Si no hay, **activa el Reactor** (usando MiMo) para generar una nueva pregunta desde los datos del negocio. Eso significa que el Reactor es un **fallback del Gestor**, no un componente paralelo.

4. **Propuesta 1 y 4** enfatizan el **dashboard de gradientes** (21 celdas visualizadas). **Propuesta 3** prefiere una UI minimalista (chat + drag-drop). **Propuesta 2** habla de "UI de Gradientes" sin detalle. **La conexión que nadie vio**: El dashboard **no es solo visualización; es el interfaz de control**. El usuario no debe "responder preguntas" pasivamente; debe **navegar la Matriz** y elegir dónde diagnosticar. Eso invierte el flujo: el sistema sugiere celdas (basado en datos), el usuario selecciona, y el sistema genera el DAG correspondiente. Todas asumen que el sistema conduce; la conexión oculta es que **el usuario debe guiar**.

5. **Propuesta 3 (Kimi K2.5)** se centra en **desarrolladores** (Code Agent). **Propuesta 1,2,4,5** se centran en **dueños de negocios no-técnicos**. **La conexión que nadie vio**: Son **dos productos distintos** con el mismo núcleo (Motor vN + Gestor). El Code Agent usa el agente para escribir código; el Exocortex lo usa para generar preguntas. La diferencia está en el **prompting** y las **herramientas**: para Code Agent, herramientas son `read_file`, `write_file`; para Exocortex, herramientas son `read_business_data`, `generate_question`, `update_gap`. El mismo loop sirve, pero el **dominio de acción** cambia. Nadie reconoce que OMNI-MIND podría ser **dos productos** en uno, con un switch de modo.

---

**PUNTOS CIEGOS**

1. **Asumen que la Matriz 3L×7F es universal, pero no está mapeada a dominios concretos**. Los experimentos validaron la Matriz en tareas abstractas (código, razonamiento), no en "negocios de servicios". ¿Qué significa "Frontera×Salud" para un estudio de Pilates? ¿Es lo mismo que para una clínica de fisio? No hay un **modelo de dominio** que traduzca celdas abstractas a conceptos de negocio concretos. Sin eso, el dashboard es incomprensible.

2. **Asumen que el usuario quiere "diagnóstico profundo", pero quizás solo quiere "acciones concretas"**. Un dueño de Pilates overworked no quiere un mapa de 21 celdas; quiere saber: "¿Cómo aumento mis ingresos?" o "¿Por qué mi instructor se va?". El sistema le da un análisis estructural, pero eso puede ser **abrumador e inútil** si no se traduce a acciones. La propuesta 1 sugiere "entrenar a un asistente para el sillón 3", pero ¿cómo llega ahí? El DAG debe **terminar en tareas accionables**, no en preguntas abstractas.

3. **Asumen que el flywheel cross-dominio funciona por transferencia de preguntas, pero ignoran la necesidad de un **mapeo ontológico** entre dominios**. Decir "una pregunta sobre proveedor único en Pilates aplica a fisio" es naive. Los dominios tienen **conceptos diferentes**: Pilates tiene "clases grupales", fisio tiene "sesiones individuales". El gap "proveedor único" puede manifestarse de forma distinta. Sin un **modelo de negocio común** (ej: "recursos escasos", "capacidad", "satisfacción cliente"), el flywheel es solo copia ciega. Nadie propone construir una ontología de "negocios de servicios" que mapee conceptos de dominio a celdas de la Matriz.

---

**CONTRADICCIONES**

1. **¿El producto es para dueños de negocios no-técnicos o para desarrolladores?**
   - **Propuestas 1,2,4,5**: Para dueños de negocios (Pilates, fisio, PYMEs).
   - **Propuesta 3**: Para desarrolladores/CTOs (Code Agent).
   - **¿Cuál tiene razón?** Los datos de Exp 6 validan el **Code Agent** (resuelve T4 async). Pero el **Exocortex** (diagnóstico de negocios) **no está validado** por experimentos. La contradicción es fatal: están mezclando dos productos. El Exocortex requiere validación en dominio de negocios; el Code Agent ya tiene datos. **Propuesta 3 tiene razón** para el Code Agent; las otras **sobreinterpretan** los datos para negocios.

2. **¿El multi-modelo es esencial o se puede reemplazar por un solo modelo barato?**
   - **Propuestas 1,2,3,4,5**: Todas defienden multi-modelo (diversidad > calidad individual).
   - **Pero Exp 1bis** muestra MiMo V2 Flash ($0.001) con score 0.90, y Nemotron Super ($0.007) con 0.96. Eso sugiere que un **solo modelo muy bueno y barato** puede cubrir la mayoría de casos.
   - **¿Cuál tiene razón?** Exp 4 muestra que **ningún modelo cubre todas las celdas** (V3.1 cubre 7, R1 7, GPT-OSS 4). Pero para un producto comercial, ¿necesitamos cobertura del 100%? Quizás el 80% de las preguntas sean útiles con MiMo. El multi-modelo añade complejidad de routing y costo. **Las propuestas sobrestiman** la necesidad de diversidad porque los experimentos buscaban maximizar cobertura, no minimizar costo/complejidad. **La realidad**: para MVP, usar **un solo modelo** (MiMo) y añadir modelos especializados solo si celdas específicas tienen baja efectividad.

---

**LA IDEA QUE FALTA**

**El "Programa de Preguntas" debe ser un DAG (grafo acíclico dirigido) de dependencias entre celdas, no una lista secuencial.**

- Las propuestas hablan de "compilar un programa de preguntas" (Prop 1,5) pero asumen secuencia lineal.
- Exp 4.3 generó **425 conexiones cross-lente**. Eso indica que las celdas no son independientes: cerrar "Frontera×Salud" puede afectar " Conservar×Continuidad".
- **Idea faltante**: El Gestor debe construir un **DAG** donde:
  - **Nodos**: preguntas (coordenada INT×Lente×Función).
  - **Aristas**: dependencias (ej: para diagnosticar "Frontera×Salud" necesitas primero " Conservar×Sentido" porque los límites personales emergen del sentido del negocio).
  - **Pesos**: correlación empírica (de `correlaciones` en DB).
- Esto permite:
  1. **Optimización de orden**: Hacer preguntas baratas primero que cierran múltiples celdas.
  2. **Salto de celdas**: Si una pregunta en A reduce B, saltar a B directamente.
  3. **Explicabilidad**: Mostrar al usuario el camino lógico ("Primero entendemos tu sentido, luego tus límites").
- **Implementación**: El Gestor, al compilar el DAG, usa las marcas estigmergicas (Prop 1) para registrar efectos cruzados. Con el tiempo, el DAG se optimiza solo.

---

**TU MERGE**

## **OMNI-MIND: Exocortex para Negocios de Servicios (Producto Mínimo Viable)**

### **1. PRODUCTO CONCRETO**

**Qué es**: SaaS que actúa como "cerebro externo" para dueños de pequeños negocios de servicios (Pilates, fisioterapia, dentistas). **No es chatbot**: es un sistema que:
1. Conecta a sus datos (agenda, clientes, ingresos vía API/CSV).
2. Calcula gaps en 21 celdas (Matriz 3L×7F) usando **un solo modelo barato** (MiMo V2 Flash, $0.001).
3. Genera un **DAG de preguntas** (no lista) para cerrar los gaps.
4. Muestra un **dashboard de celdas** (semáforos) y permite al usuario **navegar** y elegir dónde diagnosticar.
5. Al responder preguntas, el gap se reduce y el dashboard se actualiza.

**Usuario**: Dueño de negocio (1-5 empleados, €10k-50k/mes) que quiere entender patrones ocultos (ej: "¿Por qué el sillón 3 está vacío 40% del tiempo?").

**Wow moment**: 
- Ve un mapa de 21 celdas con colores. 
- Hace clic en "Frontera×Salud" (rojo). 
- El sistema muestra un DAG: "Primero, ¿con cuántos clientes tienes contacto fuera de horario? (eso afecta 'Social×Salud'). Luego, ¿has delegado alguna vez tareas administrativas? (eso afecta ' Conservar×Salud')". 
- Al responder, el gap de "Frontera×Salud" baja de 0.7 a 0.3. 
- El sistema sugiere: "Contratar un asistente para gestionar el sillón 3 liberaría 15h/semana".

**Diferenciación**:
- **Matriz 3L×7F + DAG**: Estructura de diagnóstico con dependencias lógicas.
- **Flywheel cross-dominio**: Preguntas efectivas de Pilates se transfieren a Fisio **via mapeo de celdas** (no copia directa).
- **Costo ultra-bajo**: $0.05-0.20 por diagnóstico completo (MiMo + 50 preguntas).
- **Usuario guía**: No es el sistema quien decide el orden; el usuario navega la Matriz.

### **2. VALOR**

**Basado en datos**:
- **Cobertura**: MiMo V2 Flash ($0.001) tiene score 0.90 (Exp 1bis). Suficiente para 80% de celdas. Las celdas problemáticas (ej: "Frontera×Existencial") se cubren con preguntas predefinidas.
- **Efectividad**: Exp 6: loop agéntico rompe techos (0% → 93%). Aquí, el loop es: (1) calcular gaps, (2) compilar DAG, (3) ejecutar preguntas, (4) actualizar gaps. Eso cierra gaps estructurales.
- **Costo**: 50 preguntas/diagnóstico × $0.0004 = $0.02. Con overhead, $0.05-0.20.
- **Aprendizaje**: Cada ejecución actualiza `tasa_cierre` de preguntas y