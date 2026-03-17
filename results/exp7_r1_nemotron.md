# R1 Design: Nemotron Super
**Perspectiva:** Coste/eficiencia -- que se puede hacer con codigo puro ($0) vs LLM?

### A. ARQUITECTURA (DIAGRAMA ASCII)

```
+-----------------------------+
|        Usuario             |
+------------+---------------+
             |
             v
+-----------------------------+
|   Orquestador de Gaps      |  (Código puro)
|  - Paso 0 (Detector Huecos)|
|  - Paso 2 (Routing Gradient)|
+------------+---------------+
             |
             v
+-----------------------------+
|   Router de Modelos        |  (Código puro)
|  - Asignación por celda    |
|  - Selección modelo OS     |
+------------+---------------+
             |
             v
+-----------------------------+
|   Ejecutor Multi-Modelo     |  (LLM)
|  - Paralelo por celda      |
|  - Modelos: MiMo, Devstral,|
|    Step3.5, Cogito         |
+------------+---------------+
             |
             v
+-----------------------------+
|   Sintetizador de Respuestas |  (LLM)
|  - Combinación de outputs  |
|  - Modelo: Cogito (selectivo)|
+------------+---------------+
             |
             v
+-----------------------------+
|   Agente de Actuación       |  (Código puro)
|  - Lanzar pipelines         |
|  - Invocar Agente de Código |
+------------+---------------+
             |
             v
+-----------------------------+
|   Gestor de Persistencia    |  (Código puro)
|  - Perfil usuario            |
|  - Decisiones históricas     |
+------------+---------------+
             |
             v
+-----------------------------+
|   Optimizador de Coste      |  (Código puro)
|  - Selección dinámica modelo|
|  - Control de presupuesto   |
+------------+---------------+
             |
             v
+-----------------------------+
|   Detector de Contradicciones|  (Código puro)
|  - Comparación histórico     |
+----------------------------+
```

---

### B. COMPONENTES (MAX 8)

#### 1. **Orquestador de Gaps**
- **Función**: Detecta gaps usando primitivas sintácticas (Paso 0 del Motor) y routing por gradientes (Paso 2).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Parser de gaps, algoritmo de ranking gradientes.
- **Comunicación**: Estigmergia (Postgres) + eventos async.

#### 2. **Router de Modelos**
- **Función**: Asigna modelos OS óptimos por celda (basado en datos de EXP1bis y EXP4).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Reglas de asignación (ej: MiMo para celdas baratas, Step3.5 para debugging).
- **Comunicación**: API interna con Ejecutor.

#### 3. **Ejecutor Multi-Modelo**
- **Función**: Ejecuta modelos OS en paralelo por celda.
- **Modelo**: 
  - **MiMo V2 Flash** ($0.001): Tareas generales (EXP1bis).
  - **Devstral** ($0.004): Implementación rápida (EXP5b).
  - **Step3.5 Flash** ($0.019): Debugging complejo (EXP1bis).
- **Herramientas**: Paralelizador, timeout control.
- **Comunicación**: Prompts desde Matriz, outputs a Sintetizador.

#### 4. **Sintetizador de Respuestas**
- **Función**: Combina outputs de modelos en respuesta coherente.
- **Modelo**: **Cogito-671B** ($0.15/turno, usado selectivamente).
- **Herramientas**: Algoritmo de fusión lógica.
- **Comunicación**: Estigmergia + respuesta final al usuario.

#### 5. **Agente de Actuación**
- **Función**: Ejecuta acciones externas (coding, pipelines).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Integración con Agente de Coding, Docker sandbox.
- **Comunicación**: Llamadas directas a herramientas.

#### 6. **Gestor de Persistencia**
- **Función**: Almacenamiento inter-sesión (perfil, decisiones, cola emergencia).
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Supabase Edge Functions, compresor de memoria.
- **Comunicación**: Estigmergia.

#### 7. **Optimizador de Coste**
- **Función**: Ajusta selección de modelos y parámetros para minimizar coste.
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Algoritmo de balance coste/efectividad.
- **Comunicación**: Feedback loop con Router.

#### 8. **Detector de Contradicciones**
- **Función**: Compara inputs con decisiones históricas.
- **Modelo**: Código puro (0 LLM).
- **Herramientas**: Motor de comparación semántica.
- **Comunicación**: Estigmergia.

---

### C. FLUJO DE UN TURNO DE CHAT

1. **Input Usuario** → Orquestador de Gaps
2. **Paso 0 (Detector Huecos)**: Identifica gaps en input (código puro).
3. **Paso 2 (Routing Gradient)**: Prioriza celdas por gap (código puro).
4. **Router de Modelos**: Asigna modelos OS óptimos (ej: MiMo para gaps simples).
5. **Ejecutor Multi-Modelo**: Ejecuta modelos en paralelo (LLM).
6. **Sintetizador**: Combina outputs (LLM selectivo).
7. **Agente de Actuación**: Si hay acción requerida, la ejecuta (código puro).
8. **Gestor de Persistencia**: Almacena datos inter-sesión (código puro).
9. **Optimizador**: Ajusta parámetros para próximo turno (código puro).

---

### D. FLUJO DEL PENSAMIENTO PROFUNDO

1. **Input + Gaps** → Motor v3.3 (Paso 0-2).
2. **Campo de Gradientes**: Calcula gaps (código puro).
3. **Routing por Gradients**: Selecciona modelos OS (código puro).
4. **Composición**: Ensambla preguntas (código puro, NetworkX).
5. **Ejecución Multi-Modelo**: Resuelve gaps (LLM).
6. **Verificación de Cierre**: Revisa gaps cerrados (LLM).
7. **Integración + Registro**: Sintetiza respuesta final (LLM).
8. **Gestor de Matriz**: Actualiza efectividad de preguntas (async, código puro).

---

### E. INTEGRACIÓN CON MOTOR COGNITIVO

- **Matriz 3Lx7F**: El Gestor compila preguntas específicas para el Chief basadas en gaps históricos.
- **Campo de Gradientes**: El Orquestador de Gaps usa las primitivas sintácticas del Motor para detectar gaps.
- **Routing**: El Router de Modelos asigna modelos OS según dominio de celda (ej: DeepSeek para Frontera, GPT-OSS para Depurar).

---

### F. INTEGRACIÓN CON AGENTE DE CODING

- **Agente de Actuación**: 
  - Detecta necesidad de implementación (ej: "Crea un script para X").
  - Llama al Agente de Coding con especificaciones.
  - Usa **Devstral** ($0.004) para implementación rápida (EXP5b).
  - Validación: **Step3.5 Flash** ($0.019) para debugging.

---

### G. SELF-IMPROVEMENT

1. **Registro de Efectividad**: 
   - Gap_pre vs gap_post por celda.
   - Tasa de cierre de gaps.
2. **Optimizador de Coste**:
   - Ajusta selección de modelos (ej: si MiMo falla en celda X, prueba Devstral).
3. **Gestor de Matriz**:
   - Actualiza preguntas compiladas basadas en datos de efectividad.
4. **Auto-corrección**:
   - Si un modelo falla repetidamente, se descarta (ej: Qwen3 inflador en EXP4).

---

### H. LO QUE SE ELIMINA DEL CHIEF VIEJO Y POR QUÉ

1. **Pipeline Dual Superficial/Profundo**: Reemplazado por Motor + Matriz (más eficiente).
2. **9 Modos Conversacionales**: Sustituidos por gradientes emergentes (overengineered).
3. **24 Agentes**: Consolidados en 8 componentes (reducción de overhead).
4. **Verbalizador Monolítico**: Reemplazado por Sintetizador multi-modelo.
5. **Router de Intenciones**: Sustituido por Detector de Huecos del Motor.

---

### I. LO QUE SE CONSERVA DEL CHIEF VIEJO Y POR QUÉ

1. **Estigmergia (Postgres)**: Comunicación asíncrona eficiente (0 LLM).
2. **Cola Priorizada**: Gestión inteligente de preguntas (código puro).
3. **Persistencia Inter-Sesión**: Memoria de usuario y decisiones (código puro).
4. **Detección de Contradicciones**: Integrada en Motor (código puro).
5. **Concepto Dual Rapido/Profundo**: Reimplementado con Motor (latencia mejorada).

---

### J. ESTIMACIÓN DE COSTE POR TURNO

| Componente               | Coste (USD) | Detalle                          |
|-------------------------|-------------|----------------------------------|
| Orquestador de Gaps     | $0.00       | Código puro                     |
| Router de Modelos       | $0.00       | Código puro                     |
| Ejecutor Multi-Modelo    | $0.015      | MiMo ($0.001) + Step3.5 ($0.019) |
| Sintetizador             | $0.005      | Cogito (selectivo, ~$0.15/100) |
| Agente de Actuación      | $0.00       | Código puro                     |
| Gestor de Persistencia   | $0.00       | Código puro                     |
| Optimizador de Coste     | $0.00       | Código puro                     |
| Detector de Contradicciones | $0.00    | Código puro                     |
| **Total**               | **$0.02**   | (Incluye margen de seguridad)  |

**Nota**: Coste profundo (~30s) puede variar entre $0.02-$0.05 dependiendo de celdas activas, pero se mantiene bajo $0.05 con modelos OS eficientes.