# ANÁLISIS DE LOS ROADMAPS PROPUESTOS

## 1. CONSENSO FUERTE (3+ modelos coinciden)

### ✅ Eliminación del Chief of Staff
**Todos los modelos** coinciden en eliminar el Chief of Staff. Es el consenso más fuerte. Razón: ya está reemplazado por Motor vN + Matriz 3L×7F. Es deuda técnica pura.

### ✅ Priorizar Motor vN + Gestor de la Matriz
**Kimi, V3.2-chat, Qwen3, GPT-OSS** todos ponen el Motor vN y el Gestor como núcleo. Sin esto, no hay sistema. Kimi lo llama "cáncer de arquitectura" por tener dos sistemas conviviendo.

### ✅ Reactor v4 con datos reales > Reactores sintéticos/teóricos
**Kimi, V3.2-chat, GPT-OSS** priorizan Reactor v4 (datos reales de operación) sobre v1/v2/v3. Kimi: "12% utilidad vs Reactor v4". V3.2-chat: "Flywheel de datos reales > cualquier dato sintético".

### ✅ Migración a fly.io (abandonar Supabase dual)
**Kimi, V3.2-chat** exigen elegir una infraestructura. Kimi: "No mantener ambos. Si fly.io es el futuro, migrar el estado esencial". V3.2-chat: "Supabase → fly.io: Decisión binaria".

### ✅ Reducir 18 Inteligencias a 6 irreducibles para MVP
**Kimi, V3.2-chat** proponen reducir a las irreducibles validadas: INT-01, INT-02, INT-06, INT-08, INT-14, INT-16. Las otras 12 son combinaciones o dominio-específicas que derivarán del Reactor v4.

### ✅ Auto-mejora limitada (NO fábrica de exocortex autónoma)
**Kimi, V3.2-chat, Qwen3** coinciden en que "fábrica de exocortex" y "auto-evolución nivel 3" son teoría sin validación. Kimi: "Teoría sin validación. La auto-evolución nivel 3 es ciencia ficción". V3.2-chat: "Eliminar Meta-motor y Fábrica de Exocortex autónoma".

---

## 2. DIVERGENCIAS IMPORTANTES

### A) ¿Qué modelos usar en el Motor vN?
- **Kimi K2.5**: Propone mesa mínima V3.2-chat + V3.1 (97.9% cobertura) + R1 (100%)
- **V3.2-chat**: Propone V3.2-chat + V3.1 + R1 (misma mesa)
- **Qwen3-235B**: Añade Qwen 3.5 como evaluador (IFEval 92.6)
- **GPT-OSS**: No especifica, pero en Exp 4.3 fue motor principal de pizarra
- **Nemotron Super**: Solo para validación numérica

**Análisis**: La mesa V3.2-chat + V3.1 + R1 está validada empíricamente en Exp 4.1 (100% cobertura). Es el consenso técnico. Qwen 3.5 es interesante pero no probado en nuestros experiments. **Decisión**: Usar mesa V3.2-chat + V3.1 + R1 como estándar.

### B) ¿Sintetizador: Cogito o V3.2-chat?
- **Kimi**: Usar Cogito-671B (Exp 4.2: #1, 3.6 conexiones/output)
- **V3.2-chat**: Usar V3.2-chat como evaluador principal (89.5% individual)
- **Qwen3**: No especifica
- **GPT-OSS**: No especifica
- **Nemotron Super**: No especifica

**Análisis**: Exp 4.2 es claro: Cogito es el mejor sintetizador por amplio margen. V3.2-chat es buen evaluador, pero para síntesis de conexiones Cogito es insuperable. **Decisión**: Cogito como sintetizador, V3.2-chat como evaluador.

### C) ¿Pizarra distribuida (Exp 4.3) en el MVP?
- **Kimi**: Sí, como mecanismo para "Pensar, no evaluar"
- **V3.2-chat**: No en MVP, solo en Tier 4-5 (profundo)
- **Qwen3**: No menciona
- **GPT-OSS**: No menciona
- **Nemotron Super**: No menciona

**Análisis**: La pizarra es costosa ($2-5 por output) y su valor está en conexiones, no en scores. Para MVP vendible, no es esencial. **Decisión**: Pizarra como feature avanzada (Tier 4), no en MVP.

### D) ¿Qué eliminar de la arquitectura actual?
- **Kimi**: Chief of Staff, 17 tipos pensamiento, meta-motor, fábrica exocortex
- **V3.2-chat**: Chief of Staff, 17 tipos pensamiento, modos conversacionales, Reactor v3
- **Qwen3**: No especifica eliminaciones
- **GPT-OSS**: No especifica
- **Nemotron Super**: No especifica

**Consenso adicional**: Todos los que especifican eliminan Chief of Staff y sobrecarga teórica (tipos pensamiento, modos). **Decisión**: Eliminar Chief of Staff, 17 tipos pensamiento, 6 modos conversacionales, Reactor v3, meta-motor.

---

## 3. LO QUE NO VIO NINGUNO

### 3.1 El cuello de botella real: el Gestor de la Matriz
**Ningún modelo** menciona que el Gestor de la Matriz es el componente **más crítico y menos desarrollado**. Sin él:
- El Motor vN ejecuta pero no aprende
- No hay asignación modelo→celda empírica (solo teórica)
- Los Reactores v2/v4 generan a ciegas
- No hay feedback loop de efectividad

**El Gestor es el "cerebro" que mira hacia dentro**. Sin él, la Matriz es estática. Es el componente que convierte un motor en un sistema vivo.

### 3.2 El coste oculto de la evaluación con Sonnet
**Ningún modelo** calcula el coste real de usar Sonnet como evaluador:
- Coste Sonnet: ~$0.03/1K tokens (input) + ~$0.15/1K tokens (output)
- Evaluación por caso: ~$0.25-0.35 (según documento maestro)
- Con 100 casos/día: ~$25-35/día = ~$750-1,050/mes

Esto es **insostenible** para un producto vendible a $99-299/mes. Necesitan migrar a evaluador OS **YA**, no después.

Exp 4.2 muestra que **Cogito-671B** tiene 93% de correlación con Sonnet en síntesis. ¿Por qué no usarlo desde el día 1?

### 3.3 La infraestructura actual es un bloqueo crítico
**Ningún modelo** menciona el límite de 402 funciones Edge en Supabase Free Tier. El documento maestro dice: "402 incluso con upgrade". Esto es un **bloqueo absoluto** para desplegar todo.

Kimi y V3.2-chat dicen "migrar a fly.io", pero no especifican que hay que **eliminar funciones no usadas** primero. El sistema tiene 99 Edge Functions en Supabase. Muchas son redundantes o pueden consolidarse.

### 3.4 El verdadero MVP no necesita 18 inteligencias
**Kimi y V3.2-chat** proponen 6 irreducibles, pero no especifican cuáles son las **críticas para el primer piloto**.

El documento maestro (§1A) dice que hay 9 categorías empíricas y 6 irreducibles. Para un negocio de Pilates/Fisioterapia, las inteligencias clave son:
- **INT