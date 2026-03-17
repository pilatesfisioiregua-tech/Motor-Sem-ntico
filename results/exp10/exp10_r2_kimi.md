Análisis de las auditorías cruzadas y propuesta de roadmap corregido:

## 1. CONSENSO FUERTE (3+ modelos coinciden — Esto es señal, no ruido)

**A. Eliminación del Chief of Staff y simplificación drástica**
- **Kimi, Step, Cogito, DeepSeek** coinciden: El Chief está deprecado en el Maestro (§1B, §8B) pero sigue operativo con 24 agentes en Supabase (MEMORY.md). Es una contradicción operativa crítica.
- **Acción consensuada**: Migrar solo la estigmergia (tabla `marcas_estigmergicas`) y la persistencia de sesiones, eliminar los 24 agentes específicos del Chief.

**B. El Gestor de la Matriz es el cuello de botella único (SPOF)**
- **Kimi, DeepSeek, Cogito**: Todos identifican que sin el Gestor (§6E) no hay flywheel, no hay aprendizaje transversal, y los Exocortex no pueden operar.
- **Dato**: El Gestor está "⬜ Diseñado, por implementar" (§10) y es la dependencia crítica que bloquea todo (F2 en auditorías).

**C. Reducción de complejidad teórica**
- **Step, Nemotron, Cogito**: Los 17 tipos de pensamiento (§1A) y los 6 modos son overhead. El propio Maestro admite que "el Motor no necesita modos, tiene gradientes" (§1B).
- **Consenso**: Reducir a 4 operaciones algebraicas básicas (∫, →, |, -) y eliminar la taxonomía de 17 tipos.

**D. Prioridad de datos reales sobre teóricos**
- **Kimi, DeepSeek, Cogito**: El Reactor v4 (datos reales de operación) es prioritario sobre v3 (teórico) y v2 (documentos). El flywheel "cada cliente mejora el sistema" depende de v4, no de v3.
- **Validación**: Exp 4 demostró que los datos de cobertura matricial (V3.1, R1, GPT-OSS) son empíricos y asignables (Tabla 3, §6B).

**E. Costes reales vs. presupuestos fantasmas**
- **Step, Cogito, Kimi**: Los €640-920/3meses del v1 son irreales. El coste real de inferencia con modelos OS es ~$0.10-0.35/caso (§6B), pero con volumen de desarrollo y pruebas se acerca a €2000-3000/mes.
- **Consenso**: Necesitar presupuesto realista de €200/mes solo para tokens + €15-20k para desarrollo inicial.

## 2. DIVERGENCIAS IMPORTANTES — ¿Quién tiene razón?

**A. Número de inteligencias: ¿18 vs. 6 vs. 3-4?**
- **DeepSeek** defiende las 18 (§1A, validado en Exp 4 con diferenciales >30%).
- **Kimi** argumenta que solo 6 son irreducibles (INT-01, 02, 06, 08, 14, 16) y 12 tienen solapamiento 0.50-0.75.
- **Step** propone reducir a 3-4 capacidades medibles.
- **Veredicto**: Tiene razón **Kimi**. Las 18 son el universo teórico (L1 evolucionable), pero para el MVP se operan solo las 6 irreducibles. Las demás se activan bajo demanda (Principio 31: 5 tiers, no todo es Tier 5).

**B. Arquitectura multi-modelo: ¿Mesa redonda compleja vs. Especialización por celda?**
- **Cogito** y documento Maestro proponen mesas redondas con 10-12 modelos (Exp 4.3, "mente distribuida") — coste $2-5 por análisis.
- **Step y Nemotron** argumentan que esto es "inviable comercialmente" y proponen 3 modelos especializados por celda (V3.2-chat, R1, GPT-OSS) — coste $0.30.
- **Veredicto**: Tiene razón **Step**. La mesa redonda de 12 modelos es Tier 4 (profundo batch), no para uso interactivo. El Motor vN debe usar asignación empírica modelo→celda (Tabla 3, §6B) con 3 modelos, no 12.

**C. Verticalización: ¿Pilates/Fisioterapia vs. Consultoría de negocios genérica?**
- **Documento Maestro** propone Pilates/Fisio (pilotos propios de Jesús).
- **Step** propone consultoría de negocios genérica (mercado $10B+).
- **Veredicto**: Tiene razón el **Documento Maestro** (y Cogito). Los pilotos Pilates/Fisio son necesarios para validar el Reactor v4 (datos reales de operación) antes de escalar. Saltar a consultoría genérica sin validar la transferencia cross-dominio (§6D-2) es arriesgado. Sin embargo, el modelo de negocio final debe apuntar a verticalizaciones con alto CAC (clínicas, gimnasios) o a SaaS horizontal para PYMES.

## 3. LO QUE NINGUNO VIO (Pero el arquitecto sí ve)

**A. La deuda técnica invisible del Sistema Nervioso**
Ningún modelo menciona los **99 Edge Functions en Supabase** (CONTEXTO_SISTEMA.md) que deben migrarse a fly.io. No es "cambiar provider", es reescribir 99 funciones Deno/TypeScript a Node/Python en fly.io. Esto es 3-6 meses de trabajo, no semanas. El "llm-proxy" es el punto único de fallo de 51 dependientes (A3 del auditor).

**B. La trampa del "prompt engineering" a escala**
Todos asumen que los "prompts vivos" (§6D-2) funcionarán automáticamente, pero no hay validación de que los modelos OS (especialmente los pequeños como MiMo) siguen instrucciones complejas de la Matriz sin "drift" semántico.