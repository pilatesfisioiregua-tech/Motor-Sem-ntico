# PROMPT PRÓXIMA SESIÓN — Integrar ACD en Maestro v3 → v4 + Plan de Implementación

**Contexto:** Sesión 19-mar-2026, post-Reactor v5/v5.2/Desequilibrio/Recetas/Taxonomía/Inversión Causal/Framework ACD
**Archivos clave:** `results/reactor_v5/` (14 archivos). Leer en este orden:

## RESUMEN EJECUTIVO DE LO QUE EXISTE

En la sesión del 19-mar-2026 se produjo el **Álgebra Cognitiva Diagnóstica (ACD)** — el framework completo que integra todo lo descubierto. Componentes:

### Documentos producidos (leer FRAMEWORK_ACD primero):

1. `results/reactor_v5/FRAMEWORK_ACD.md` — **EL FRAMEWORK COMPLETO.** 11 secciones: ontología 5D, modelo causal 4 niveles, 10 estados diagnósticos, ~55 leyes, pipeline 11 pasos, álgebra formal, dimensión generativa, posicionamiento producto.
2. `results/reactor_v5/inversion_causal_INT_P_R.md` — La inversión causal: configuración INT×P×R → perfiles de lentes. 7 leyes IC1-IC7. Tablas de configuración cognitiva por perfil patológico.
3. `results/reactor_v5/taxonomia_pensamiento_razonamiento.md` — 12 tipos de razonamiento + 15 tipos de pensamiento, cada uno mapeado a lentes y funciones. 4 leyes TP1-TP4.
4. `results/reactor_v5/gradientes_equilibrio_inteligencias.md` — 4 estados E1-E4, 18 INT × lentes × funciones, recetas de transformación por perfil, 6 leyes T1-T6.
5. `results/reactor_v5/SINTESIS_SESION_REACTOR_v5.md` — 28 hallazgos empíricos (H1-H28), leyes D1-D5, C1-C5, pipeline consolidado, candidatos a L0.

### Lo que el ACD añade sobre Maestro v3:

| Maestro v3 tenía | ACD añade |
|-------------------|-----------|
| 3L × 7F × 18 INT | + 15 Pensamientos + 12 Razonamientos = espacio 5D |
| "Campo de gradientes" (concepto) | 10 estados formalizados (E1-E4 + 6 perfiles patológicos) |
| "Configuraciones efectivas" (concepto) | Configuraciones INT×P×R concretas por perfil con tablas |
| Pipeline Motor 7 capas (técnico) | Pipeline ACD 11 pasos (lógico, encima del técnico) |
| ~13 reglas del compilador | ~55 leyes organizadas en 8 grupos (IC, D, C, T, TP, E, H, TCF) |
| L0/L1/L2 como niveles estáticos | L1 redefinido como GENERATIVO: las preguntas fabrican herramientas cognitivas nuevas |
| Prompt = álgebra + preguntas | Confirmado + mecanismo de cristalización para generar nuevas INT/P/R ad hoc |
| Sin modelo de patología | 6 perfiles patológicos + flags de peligro oculto + recetas de transformación |
| Sin predicción cuantitativa | Umbrales empíricos: Se_avg, delta F3, gap lentes, repertorio mínimo E4 |

### La idea central que lo cambia todo:

> Las lentes y funciones son CONSECUENCIA, no causa. El origen es la configuración cognitiva INT×P×R. Y las INT/P/R son a su vez patrones cristalizados de TIPOS DE PREGUNTAS. La pregunta es la unidad atómica. El sistema es autopoiético: preguntas → herramientas → lentes → diagnóstico → prescripción → nuevas preguntas.

---

## TAREA DE ESTA SESIÓN

### Objetivo 1: Actualizar Maestro v3 → v4

El Maestro v3 tiene 2,199 líneas en 15 secciones (§0–§14). Hay que integrarlo con el ACD SIN reescribir todo — es una evolución, no un reemplazo.

**Secciones del Maestro v3 que necesitan cambios:**

Lee `docs/maestro/MAESTRO_V3.md` y evalúa sección por sección:

| Sección Maestro v3 | Cambio necesario |
|---------------------|-----------------|
| §0 Preámbulo | Actualizar: ACD como nombre del framework. Añadir las 5 dimensiones. |
| §1 Las 3 Lentes | MANTENER (L0 invariante). Añadir: "son consecuencia, no causa" (inversión causal). |
| §2 Las 7 Funciones | MANTENER (L0). Añadir: F3 como única fuente natural de Se. Las 3 modalidades de F3. Leyes TCF validadas. |
| §3 Las 18 Inteligencias | EXPANDIR: añadir mapeo INT × lente × función (tabla de gradientes). Añadir que son generables ad hoc. |
| §4 Los 6 Modos | MANTENER. Añadir correlación con lente faltante (Ley T3). |
| §5 Los 5 Niveles Lógicos | MANTENER. Añadir correlación con lente faltante (Ley T2). |
| §6 Las Reglas del Compilador | EXPANDIR: integrar las ~55 leyes organizadas por grupo. Las 13 originales se mantienen, las nuevas se añaden. |
| §7 El Prompt (2 partes) | MANTENER estructura. Actualizar: la secuencia imperativa ahora incluye selección INT×P×R, no solo INT. |
| §8 Los 5 Mecanismos Multi-Modelo | MANTENER (infraestructura). |
| §9 Los 5 Tiers de Enjambre | MANTENER (Principio 31). |
| §10 Motor vN Pipeline | REESCRIBIR parcialmente: el pipeline ACD de 11 pasos reemplaza/extiende el pipeline actual. Fases A-D. |
| §11 Gestor de la Matriz | ACTUALIZAR: el Gestor ahora compila programas que incluyen P y R, no solo INT. |
| §12 Reactor | ACTUALIZAR: el Reactor ahora es explícitamente el cristalizador de nuevas herramientas cognitivas (§10.5-10.6 del ACD). |
| §13 Roadmap | ACTUALIZAR con el roadmap del ACD §9. |
| §14 Principios | AÑADIR los que falten de los ~32+ existentes. |
| **§NEW: Tipos de Pensamiento** | NUEVA SECCIÓN: 15 P × lentes × funciones (de taxonomia_pensamiento_razonamiento.md) |
| **§NEW: Tipos de Razonamiento** | NUEVA SECCIÓN: 12 R × lentes × funciones (de taxonomia_pensamiento_razonamiento.md) |
| **§NEW: Patología y Diagnóstico** | NUEVA SECCIÓN: 10 estados, 6 perfiles, flags, recetas de transformación |
| **§NEW: Inversión Causal** | NUEVA SECCIÓN: modelo causal 4 niveles, leyes IC1-IC7 |
| **§NEW: Dimensión Generativa** | NUEVA SECCIÓN: preguntas como unidad atómica, cristalización, diseño ad hoc |

### Objetivo 2: Plan de implementación del ACD en el Motor

No es solo documentación — el ACD tiene que ejecutarse en código. Evaluar:

1. **¿Qué del pipeline ACD (11 pasos) ya existe en el Motor actual?**
   - Leer `src/pipeline/` para ver qué capas ya cubren qué pasos
   - Leer `src/meta_red/` para ver cómo están implementadas las INT actualmente

2. **¿Qué falta implementar?**
   - Paso 1 (diagnóstico cognitivo): ¿el Motor ya evalúa INT activas/atrofiadas?
   - Paso 2 (perfil de lentes): ¿calcula S_avg, Se_avg, C_avg?
   - Paso 4 (diagnóstico cognitivo INT×P×R): esto es NUEVO
   - Paso 5 (prescripción cognitiva): esto es NUEVO
   - Paso 6 (selección tipo lógico + modo): ¿existe parcialmente?
   - Paso 10 (evaluación con umbrales): ¿implementado?

3. **¿Qué necesita la base de datos?**
   - Las tablas actuales (23 + 1 view) ¿cubren los 10 estados?
   - ¿Hay tabla para perfiles de P y R?
   - ¿Se necesitan tablas nuevas para el diagnóstico cognitivo?

4. **¿Cuál es la secuencia de implementación?** (WIP=1-2)
   - Proponer briefings numerados con dependencias

### Formato de entrega:
- Maestro v4 guardado en `docs/maestro/MAESTRO_V4.md` (el v3 se preserva intacto)
- Plan de implementación guardado en `docs/operativo/PLAN_IMPLEMENTACION_ACD.md`
- Briefings de implementación en `motor-semantico/briefings/`

---

## ARCHIVOS A LEER

### Obligatorios (en este orden):
1. `results/reactor_v5/FRAMEWORK_ACD.md` — el framework completo
2. `docs/maestro/MAESTRO_V3.md` — el documento actual (2,199 líneas)

### Bajo demanda:
3. `results/reactor_v5/inversion_causal_INT_P_R.md` — si necesitas detalle de IC1-IC7
4. `results/reactor_v5/taxonomia_pensamiento_razonamiento.md` — si necesitas detalle de P y R
5. `results/reactor_v5/gradientes_equilibrio_inteligencias.md` — si necesitas detalle de E1-E4
6. `results/reactor_v5/SINTESIS_SESION_REACTOR_v5.md` — si necesitas los 28 hallazgos
7. `src/pipeline/` — para evaluar qué existe en código
8. `src/meta_red/` — para evaluar implementación de INT
9. `docs/sistema/ESTADO_REAL_SISTEMA.md` — para estado actual de tablas y endpoints

---

## DECISIONES PENDIENTES (CR1 Jesús)

1. **¿Maestro v4 como documento nuevo o reescritura del v3?** — CR0 propone documento nuevo (v3 se preserva como histórico)
2. **¿Las ~55 leyes se integran todas en el Maestro o se mantienen en documentos satélite?** — CR0 propone: las 7 fundamentales van al Maestro, el resto en `docs/L0/LEYES_ACD.md`
3. **¿Los 15P y 12R van como secciones del Maestro o como documento aparte?** — CR0 propone: resumen en Maestro, detalle en `docs/L1/`
4. **¿Prioridad implementación vs documentación?** — CR0 propone: Maestro v4 primero (1 sesión), luego implementación (briefings)
