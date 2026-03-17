Aquí tienes el diseño de producto concreto, derivado directamente de los datos empíricos de los 9 experimentos:

---

## 1. PRODUCTO

### ¿Qué se construye HOY?
**OMNI-MIND Code Agent** — Un agente de software semi-autónomo que escribe, debugge y despliega código mediante un loop agéntico multi-modelo.

**No es**: Un chatbot generalista ni un sistema cognitivo completo.
**Sí es**: La implementación concreta del **Exp 6** (agente 460 líneas, 99% éxito) expuesta como servicio, usando la **Matriz 3L×7F** como infraestructura invisible (no como feature de usuario).

### Usuario y problema
**Usuario**: Desarrolladores full-stack y CTOs de startups (5-50 devs).
**Problema**: Las herramientas actuales (Copilot, Cursor) fallan en tareas de complejidad media-alta (orquestación async, migraciones complejas, debugging multi-archivo). El Exp 5 demostró que los pipelines lineales tienen **techo estructural del 56%**, y el Exp 6 demostró que el **loop agéntico rompe ese techo** (0% → 93% en T4, Orquestador async).

**Wow moment**: El usuario escribe "Implementa un sistema de colas con retry exponencial y dead-letter queue", y en 90 segundos el agente:
1. Lee los archivos existentes (Exp 6: `read_file`)
2. Detecta el stack (Exp 6: `list_dir`)
3. Escribe el código (Exp 1bis: Devstral, T4=100%)
4. Debuggea errores (Exp 6: Step 3.5 Flash, 3 rounds de debug)
5. Verifica con tests (Exp 6: `run_command`)
6. Entrega PR listo (Exp 6: `finish`)

**Diferencia con ChatGPT/Claude**: 
- **ChatGPT**: Genera código en una pasada. Si falla, iteración manual.
- **OMNI-MIND**: Loop agéntico con **routing inteligente** (Exp 4 + Exp 1bis). Usa Devstral ($0.004) para escribir, Step ($0.019) para debuggear, y Cogito ($0.125) para síntesis final. Resuelve T4 (async) donde Claude 3.5 falló (Exp 5b: 0% → 93%).

---

## 2. VALOR

### Valor REAL basado en datos
- **Exp 6**: El loop agéntico logró **99% vs 56%** del pipeline lineal. Esa diferencia (43 puntos porcentuales) es el valor: tareas que antes requerían intervención humana ahora son autónomas.
- **Exp 4**: El sintetizador (Cogito) genera **3.6 conexiones cross-lente** por output, detectando puntos ciegos que ningún modelo solo ve (Exp 4.3: 239 puntos ciegos detectados vs 0 en mesa redonda simple).
- **Exp 1bis**: Coste de **$0.001-$0.019** por operación vs $1.57 de pipeline caro. El ratio calidad/coste de MiMo V2 Flash (0.90 a $0.001) permite operar con margen >90%.

### ¿Qué pueden hacer los modelos OS que no pueden los chatbots genéricos?
- **Especialización por celda**: Según Exp 4, V3.1 domina "Frontera" (2.70), GPT-OSS domina "Depurar" (2.52), R1 domina "Continuidad" (2.18). El producto rutea automáticamente: si es un bug async → Devstral; si es lógica compleja → Step 3.5; si es síntesis final → Cogito.
- **Verificación multi-modelo**: Exp 4.2 demostró que el sintetizador (Cogito) iguala o supera el máximo mecánico en **100% de las celdas**, eliminando alucinaciones individuales.

### ¿La Matriz aporta valor perceptible?
**No**. Es infraestructura invisible (como dice Exp 7 R1 de DeepSeek: "Los gradientes emergen, no se muestran"). El usuario ve un chat limpio, pero detrás:
- El **Gestor de la Matriz** (Exp 7) compila el "Programa de Preguntas" óptimo para cada tarea de código.
- Detecta gaps en el spec (Exp 5: T1 resuelto 100% con modelos nuevos).
- Asigna modelo por celda (Exp 6: Devstral para T4, Step para debug).

### ¿El multi-modelo aporta valor vs uno solo?
**Sí**. Exp 4 demostró que **2 modelos capturan 90% del valor** (gpt-oss + qwen3), pero el enjambre completo (7 modelos) alcanza 100% de cobertura. La diversidad es una dimensión algebraica (Exp 4: cada modelo domina celdas diferentes).

---

## 3. ARQUITECTURA MÍNIMA VIABLE

Basada en **Exp 6** (agente 460 líneas) + **Exp 7 R1** (diseño DeepSeek de 8 componentes):

### Componentes (máximo 8)

1. **Router/Orquestador** (código puro, 200 líneas)
   - Decide: ¿Es tarea simple (MiMo) o compleja (Step+Devstral)?
   - Basado en Exp 5: Config D (ultra-barato) para tareas <0.3 gap, Config A (industrial) para >0.7.

2. **Agente de Coding** (Exp 6, 460 líneas reutilizables)
   - Loop: observe → think → act.
   - 5 herramientas: `read_file`, `write_file`, `run_command`, `list_dir`, `search_files`.
   - Routing interno: Devstral (genera) → Step (debug tras 2 errores) → MiMo (fallback).

3. **Sintetizador** (Cogito-671B, vía API)
   - Solo activo cuando hay múltiples outputs (Exp 4.2: 47s, $0.125).
   - Integra hallazgos y detecta conexiones cross-lente.

4. **Gestor de Memoria** (MiMo V2 Flash, $0.001)
   - Contexto de conversación y estado del proyecto.
   - Reemplaza al "Guardián" de Exp 7, pero simplificado.

5. **Monitor de Coste** (código puro)
   - Presupuesto por tarea: $0.50 hard limit (Exp 6: máximo $1.57).
   - Stuck detection: 4 acciones repetidas → abort (Exp 6).

6. **Matriz 3L×7F (Adapter)** (código puro + embeddings)
   - No expuesta al usuario.
   - Usada para detectar gaps en el spec de la tarea (¿falta "Conservar" o "Distribuir"?).

7. **Validador de Seguridad** (Qwen 3.5, $0.033)
   - Blacklist de comandos peligrosos (Exp 6: sin sandbox Docker por ahora).

8. **Logger/Telemetría** (código puro, $0)
   - Registra efectividad por modelo/tarea (alimenta al Gestor).

### ¿Qué se ELIMINA del diseño actual?
- **Chief of Staff**: Sobrediseño (Exp 8: 24 agentes, 6.900 líneas deprecados).
- **17 tipos de pensamiento**: Overhead (Exp 8: solo 6-7 usados).
- **9 modos conversacionales**: Redundantes con gradientes (Exp 7).
- **Reactor v3**: 12% utilidad (Exp 8).
- **Pipeline lineal de Exp 5**: Reemplazado por loop agéntico.

### ¿Qué se AÑADE que no está diseñado?
- **Fallback automático**: Si Step 3.5 "piensa sin actuar" (Exp 5b: think-tag blowup), switch a MiMo.
- **Estimador de coste previo**: Antes de ejecutar, estima $ basado en complejidad (Exp 6: $0.001-$1.57).

---

## 4. IMPLEMENTACIÓN

### Semana 1 (MVP funcional)
- **Tarea**: Portar el agente de Exp 6 a fly.io.
- **Scope**: Solo T3 (Analysis Script) y T4 (Orquestador async) de Exp 6.
- **Modelos**: Devstral (implementación) + Step 3.5 (debug).
- **Coste**: ~$50 en tokens de prueba.

### Mes 1 (Multi-modelo básico)
- **Tarea**: Implementar el Router (componente 1) y el Gestor de Matriz simplificado.
- **Integración**: Añadir Cogito para síntesis cuando hay >3 archivos modificados.
- **Validación**: Replicar Exp 6 con 10 tareas reales de usuarios beta (Pilates/Fisio).
- **Coste**: ~$500 (1000 ejecuciones a $0.50 promedio).

### Mes 3 (Producto cerrado)
- **Tarea**: UI minimalista (chat + drag-drop de specs), billing, auth.
- **Optimización**: Cachear programas compilados de la Matriz para tareas recurrentes.
- **Coste operativo**: ~$300/mes para 1000 tareas/mes.

### Secuencia de aprendizaje
1. **Semana 1**: Validar que el loop agéntico de Exp 6 escala a fly.io (no solo local).
2. **Mes 1**: Validar que el routing por gradientes (Exp 7) reduce coste a <$0.20/tarea.
3. **Mes 3**: Validar que el sintetizador (Cogito) mejora la calidad percibida vs solo Devstral.

### Reutilización de Exp 6
- El código de 460 líneas del agente se reutiliza **directamente** como núcleo del componente 2.
- Se añaden solo: (a) integración con fly.io functions, (b) router multi-modelo, (c) persistencia en Postgres.

---

## 5. NEGOCIO

### Precio correcto
**No €50-200/mes** (no validado, Exp 8).
**Sí**: 
- **€20-49/mes** para developers individuales (freemium: 10 tareas gratis, luego $0.10/tarea).
- **€200-500/mes** para equipos (API rate limiting, colaboración, audit logs).

**Justificación**: Exp 6 demostró coste de $0.001-$1.57 por tarea. Con optimización (MiMo+Devstral+Step), el 80% de las tareas cuestan <$0.20. Margen del 90% viable.

### Modelo
**SaaS con API**:
- Web app para especs (chat + upload de repos).
- API para integración con CI/CD (GitHub Actions, etc.).

### Competidores y diferenciación
| Competidor | Diferencia de OMNI-MIND |
|------------|-------------------------|
| **GitHub Copilot** | Copilot es autocompletado. OMNI-MIND es agente autónomo (loop observe→act) que resuelve T4 (async) donde Copilot falla (Exp 5 vs Exp 6). |
| **Cursor** | Cursor tiene un modelo. OMNI-MIND tiene **enjambre especializado** (Devstral para code, Step para debug, Cogito para síntesis) según Exp 4. |
| **OpenHands (Exp 6 original)** | OMNI-MIND es OpenHands + Matriz 3L×7F (mejor routing) + Multi-modelo OS (mejor coste/calidad que GPT-4). |

### Ruta de validación
**Pilotos propios → Developer friends → Escala** (Exp 8, §11):
1. **Piloto 1**: Usar el agente para mantener el propio OMNI-MIND (dogfooding).
2. **Piloto 2**: 5 amigos developers (validar que pagan €20/mes).
3. **Escala**: Product Hunt, Hacker News (target: 100 devs en mes 6).

---

## 6. RIESGOS

### Riesgo #1 que mata el proyecto
**Think-tag blowup en modelos razonadores** (Exp 5b).
- Si Step 3.5 Flash consume 16K tokens pensando sin output (como pasó en T4), el coste por tarea se dispara a $5+ y el usuario espera 60s.
- **Mitigación**: Timeout de 20s por iteración. Si Step "piensa" >10s sin output, fallback a MiMo V2 Flash (no usa think-tags).

### Asunción no validada más peligrosa
**Que el "Gestor de la Matriz" puede compilarse en tiempo real** (Exp 8, F2).
- Si el compilador de programas (basado en Qwen 235B) falla, el sistema no puede asignar modelos a celdas.
- **Mitigación**: Tabla cacheada de asignación modelo→celda (basada en Exp 4) como fallback estático.

### Si el flywheel no funciona
**Impacto**: El producto sigue siendo viable como **agente de coding especializado** (intra-dominio), aunque no escale a "todo propósito cognitivo".
- Exp 6 ya demostró valor en un solo dominio (coding).
- El cross-dominio (Pilates→Fisio) es upside, no core del MVP inicial.

---

**Resumen ejecutivo**: Construye el agente de Exp 6 (460 líneas, 99% éxito), expónlo como API SaaS a €20-49/mes, elimina el Chief y los 17 tipos de pensamiento, y usa la Matriz como infra invisible para routing de modelos OS (Devstral, Step, Cogito). El valor es la resolución de tareas complejas (T4) que otros no pueden, a coste de $0.10-0.50 por tarea.