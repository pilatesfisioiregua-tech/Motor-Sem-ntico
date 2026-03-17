# ACTUALIZACIÓN DOCUMENTO MAESTRO — Sesiones 10-mar noche + 11-mar

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-11
**Instrucción:** Incorporar al SISTEMA_COGNITIVO_OMNI_MIND_MAESTRO_v2.md

---

## §0 — AÑADIR A TABLA DE CAMBIOS

| Cambio | Origen | Sección |
|--------|--------|---------|
| **Exp 1 COMPLETADO: 12 modelos evaluados en cobertura matricial** | Sesión 10-mar-noche | §10 |
| **Ranking final: V3.1 (2.19), R1 (2.18), GPT-OSS (2.15), V3.2 Chat (2.12), Claude 10º de 12** | Sesión 10-mar-noche | §6B |
| **V3.2 Chat tiene 6/21 celdas nivel 3+ — más insights no obvios que todos** | Sesión 10-mar-noche | §6B |
| **V3.2 Reasoner bug fix: reasoning_content vs content vacío** | Sesión 10-mar-noche | §6B |
| **V3.2 como coder: 80% (4/5 tests). Falla regla 11 y mapeo Matriz→INT** | Sesión 10-mar-noche | §6F |
| **Test set evaluador listo: 5 outputs + 5 eval Sonnet referencia** | Sesión 10-mar-noche | §10 |
| **9 modelos diferentes ganan celdas en Tabla 3 — ninguno domina** | Sesión 10-mar-noche | §6B |
| **Cogito Frontera×Sentido = 3.4 — score más alto de cualquier celda de Sentido** | Sesión 10-mar-noche | §6B |
| **Sentido sigue siendo la lente más difícil para todos** | Sesión 10-mar-noche | §6B |
| **Exp 2 ejecutado parcial: 7/11 modelos OS como evaluadores. Mejor Spearman=0.464 (insuficiente)** | Sesión 11-mar | §10 |
| **Evaluación OS insuficiente con referencia Sonnet. Pero Sonnet (10º ejecutor) puede ser mala referencia** | Sesión 11-mar | §10 |
| **5/7 modelos OS deflactan vs Sonnet → Sonnet posiblemente infla scores** | Sesión 11-mar | §10 |
| **Decisión: no hay gold standard. La verdad es el consenso entre evaluadores.** | Sesión 11-mar | §6B |
| **Mesa Redonda (Exp 4): 12 modelos evalúan → ven lo de los demás → enriquecen. Acumulación, no debate.** | Sesión 11-mar | §6B, §4B |
| **Mesa Redonda Especializada (Exp 4.1): cada modelo con prompt afinado a su fortaleza empírica** | Sesión 11-mar | §6B |
| **Sintetizador (Exp 4.2): un modelo integra las 12 perspectivas en output coherente** | Sesión 11-mar | §4B |
| **Mente Distribuida (Exp 4.3): pizarra compartida, micro-rondas, 12 modelos = 1 cerebro** | Sesión 11-mar | §4B |
| **Cadena de Montaje (Exp 5): pipeline industrial de código con 5 estaciones especializadas** | Sesión 11-mar | §6F |
| **Principio 31: Rápido y profundo no existe. 5 velocidades para 5 contextos.** | Sesión 11-mar | §12, §4B |
| **5 tiers de enjambre: reflejo ($0, ms) / respuesta ($0.01, 10s) / análisis ($0.30, 3min) / profundo ($1, 45min) / cartografía ($10, horas)** | Sesión 11-mar | §4B |
| **Opus se ejecuta manualmente en claude.ai ($0 API). No se incluye en pipelines automatizados.** | Sesión 11-mar | §8 |
| **Modelos de código disponibles: Qwen3-Coder 480B, Qwen3-Coder-Next 80B, MiniMax M2.5, GLM-5** | Sesión 11-mar | §6F |
| **Enjambre de evaluadores: 12 modelos OS (Together + DeepSeek), no hay gold standard** | Sesión 11-mar | §6B |

---

## §6B — AÑADIR: RESULTADOS EXP 1 COMPLETO (12 modelos)

### Ranking final multi-modelo (Tabla 4) — 12 modelos evaluados

| # | Modelo | Nivel medio | Celdas cubiertas | Celdas 3+ |
|---|--------|-------------|-----------------|-----------|
| 1 | DeepSeek V3.1 | 2.19 | 19/21 | 5/21 |
| 2 | DeepSeek R1 | 2.18 | 20/21 | 4/21 |
| 3 | GPT-OSS 120B | 2.15 | 19/21 | 5/21 |
| 4 | DS-V3.2 Chat | 2.12 | 18/21 | **6/21** |
| 5 | DS-V3.2 Reasoner | 2.00 | 17/21 | 3/21 |
| 6 | Cogito 671B | 1.98 | 18/21 | 2/21 |
| 7 | Qwen3 Thinking | 1.95 | 19/21 | 2/21 |
| 8 | Kimi K2.5 | 1.87 | 18/21 | 1/21 |
| 9 | Qwen3.5 397B | 1.83 | 17/21 | 1/21 |
| 10 | Claude (ref) | 1.79 | 15/21 | 1/21 |
| 11 | Maverick | 1.74 | 16/21 | 1/21 |
| 12 | 70B | 1.42 | 11/21 | 1/21 |

### Hallazgos clave Exp 1

1. **3 modelos OS superan a Claude.** V3.1, R1, GPT-OSS. Claude es 10º de 12.
2. **V3.2 Chat tiene 6/21 celdas nivel 3+** — más insights no obvios que todos. Nivel medio 4º pero más profundo donde importa.
3. **Cogito Frontera×Sentido = 3.4** — score más alto de cualquier modelo en cualquier celda de Sentido. Candidato a cerebro profundo.
4. **9 modelos diferentes ganan celdas.** Ningún modelo domina. El enjambre siempre gana.
5. **Sentido sigue siendo la lente más difícil para todos.**
6. **V3.2 Reasoner corregido** — bug en reasoning_content vs content. Fix: leer content primero, si vacío leer reasoning_content.

### Asignación modelo→celda actualizada (Tabla 3)

| | Conservar | Captar | Depurar | Distribuir | Frontera | Adaptar | Replicar |
|---|---------|---------|---------|---------|---------|---------|---------|
| **Salud** | V3.1 (2.8) | Maverick (2.1) | GPT-OSS (2.6) | Qwen3 Think (2.1) | V3.1 (2.6) | Kimi (2.7) | V3.1 (2.0) |
| **Sentido** | Cogito (2.3) | V3.2 Reas (2.7) | GPT-OSS (2.9) | GPT-OSS (1.7) | **Cogito (3.4)** | V3.1 (2.4) | R1 (1.7) |
| **Continuidad** | V3.1 (2.4) | Qwen3 Think (2.2) | Qwen3.5 (2.3) | Qwen3 Think (2.2) | V3.1 (2.9) | V3.2 Reas (2.8) | R1 (3.1) |

---

## §6B — AÑADIR: EVALUACIÓN MULTI-MODELO (Exp 2)

### Resultados Exp 2 (parcial: 7/11 modelos)

Todos medidos vs Sonnet como referencia. **Dato importante: Sonnet fue 10º como ejecutor, su evaluación puede no ser buen benchmark.**

| Modelo | Spearman | Bias | F1(3+) | Nota |
|--------|----------|------|--------|------|
| GLM-4.7 | 0.464 | +0.14 | 0.000 | Solo 1/5 outputs parseados |
| V3.2 Chat | 0.426 | -0.46 | 0.103 | Deflacta vs Sonnet |
| Qwen3-235B | 0.373 | +0.54 | 0.578 | Infla, pero detecta insights |
| GPT-OSS | 0.280 | -0.74 | 0.348 | Fuerte deflación |
| R1 | 0.247 | -0.62 | 0.293 | Deflacta |
| V3.1 | 0.220 | -0.34 | 0.190 | Deflacta |
| M2.5 | 0.208 | -0.44 | 0.279 | Deflacta |

**Conclusión Exp 2:** Ningún modelo OS alcanza Spearman ≥ 0.85 vs Sonnet. Pero 5/7 deflactan — sugiere que Sonnet infla scores, no que los OS evalúen mal. La referencia es el problema, no los evaluadores.

**Decisión:** No hay gold standard. La verdad es el consenso entre todos. Mesa redonda (Exp 4) como protocolo de evaluación.

### Modelos que faltaron en Exp 2
- Cogito 671B, V3.2 Reasoner, Kimi K2.5, MiniMax M1 — no ejecutados
- R1, M2.5, GLM-4.7 — parciales (no completaron los 5 outputs)

---

## §4B — NUEVA SECCIÓN: ARQUITECTURA DE TIERS

### Principio: Rápido y profundo no existe

5 velocidades para 5 contextos. La calidad no se negocia — se agenda.

```
TIER 1 — REFLEJO (ms, $0)
  Código puro. Lookup en Matriz precompilada.
  "Este patrón lo he visto 47 veces"

TIER 2 — RESPUESTA (5-15s, $0.01-0.05)
  1 modelo OS barato. 80% de interacciones.

TIER 3 — ANÁLISIS (1-5 min, $0.10-0.50)
  3-5 modelos en paralelo. Decisiones importantes.

TIER 4 — PROFUNDO (30-60 min, $0.50-2.00)
  Mente distribuida. Batch nocturno. Briefing matutino.

TIER 5 — CARTOGRAFÍA (horas/días, $5-20)
  Exploración completa. Onboarding. Auditoría anual.
```

### Relación con loops

```
LOOP RÁPIDO (Motor vN):     Tier 1 + Tier 2 (segundos)
LOOP MEDIO (análisis):       Tier 3 (minutos, bajo demanda)
LOOP LENTO (Gestor):         Tier 4 (horas, batch nocturno)
LOOP PROFUNDO (Reactores):   Tier 5 (días, onboarding)
```

### Enjambre por tier

| Tier | Modelos típicos | Por qué |
|------|----------------|---------|
| 1 | Ninguno (código) | Velocidad máxima |
| 2 | GPT-OSS / Qwen3-Coder-Next | Baratos, rápidos |
| 3 | V3.2 Chat + Cogito + R1 | Balance profundidad/velocidad |
| 4 | 10 modelos OS (pizarra) | Máxima diversidad |
| 5 | 10 modelos + composiciones + loops | Todo el arsenal |

### Mecanismos de Tier 4 — Tres variantes diseñadas

**A) Mesa Redonda (Exp 4):** 12 modelos evalúan → ven lo de los demás → enriquecen. Acumulación de perspectivas. Output = unión de visiones.

**B) Mesa Especializada (Exp 4.1):** Igual que A pero cada modelo con prompt afinado a su fortaleza empírica (Cogito→Sentido, R1→Continuidad, GPT-OSS→Depurar, etc.)

**C) Mente Distribuida (Exp 4.3):** Pizarra compartida + micro-rondas. Cada modelo contribuye diffs, no evaluaciones completas. Más barato y rápido que A/B. Los 12 modelos operan como áreas de un mismo cerebro.

**Sintetizador (Exp 4.2):** Después de A, B, o C, un modelo integra las perspectivas en output coherente. Conecta celdas, identifica meta-patrones, detecta puntos ciegos residuales.

---

## §6F — AÑADIR: ENJAMBRE DE CÓDIGO (Exp 3 + Exp 5)

### Modelos de código disponibles (todos en Together + DeepSeek)

| Modelo | model_id | Perfil |
|--------|----------|--------|
| Qwen3-Coder 480B | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` | Especialista código. 256K context. $2/M. |
| Qwen3-Coder-Next 80B | `Qwen/Qwen3-Coder-Next-FP8` | Ultra-eficiente. 3B activos. $1.20/M. |
| MiniMax M2.5 | `MiniMaxAI/MiniMax-M2.5` | 80.2% SWE-Bench. 10B activos. $1.20/M. |
| GLM-5 | `zai-org/GLM-5` | Systems engineering. 744B. $3.20/M. |
| V3.2 Chat | `deepseek-chat` | 80% en test de Exp 1. Barato. $1.10/M. |

### Resultado V3.2 como coder (Exp 1 Parte B)
- 4/5 tests pasan (80%). Código OOP limpio, ejecutable.
- Falla: regla 11 (orden INT-14/INT-01) y mapeo Matriz→Inteligencias.
- Veredicto: funcional como esqueleto pero necesita supervisión en lógica de dominio.

### Cadena de Montaje (Exp 5) — Proceso industrial de código

5 estaciones especializadas:
```
ARQUITECTO → IMPLEMENTADOR → TESTER → REVISOR → OPTIMIZADOR
```

6 configuraciones probándose con diferentes modelos por estación. Hipótesis: la cadena supera al modelo solo (>95% tasa éxito).

---

## §8 — AÑADIR: OPUS MANUAL

**Opus no se incluye en pipelines automatizados.** Se ejecuta manualmente en claude.ai ($0 API). Los resultados se cargan como archivo JSON si se necesitan. Esto ahorra ~75% del coste de los experimentos que incluían Opus.

---

## §10 — REEMPLAZAR: ESTADO DE EXPERIMENTOS

### Exp 1 — Multi-modelo cobertura matricial ✅ COMPLETADO
- 12 modelos evaluados en cobertura matricial
- Ranking final: V3.1, R1, GPT-OSS top 3. Claude 10º.
- V3.2 Chat: 6/21 celdas nivel 3+ (más profundo puntualmente)
- V3.2 Reasoner: bug fix aplicado (reasoning_content vs content)
- V3.2 como coder: 4/5 tests (80%), falla lógica de dominio
- Test set evaluador preparado: 5 outputs + 5 eval Sonnet

### Exp 2 — Enjambre de evaluadores OS 🔄 PARCIAL
- 7/11 modelos testeados. Mejor Spearman=0.464 (insuficiente)
- 5/7 modelos deflactan vs Sonnet → Sonnet posiblemente infla
- Faltaron: Cogito, V3.2 Reasoner, Kimi, MiniMax M1
- Conclusión: referencia (Sonnet) es el problema. Evaluación ciega insuficiente.
- Decisión: pasar a mesa redonda (Exp 4) para evaluación por consenso

### Exp 3 — Enjambre de código ⬜ PROMPT LISTO
- 10 modelos × 5 tareas de dificultad progresiva
- Incluye Qwen3-Coder 480B, Qwen3-Coder-Next 80B, MiniMax M2.5, GLM-5
- Análisis de pares generador+revisor

### Exp 4 — Mesa Redonda (acumulación de perspectivas) 🔄 CORRIENDO
- 12 modelos OS (sin Opus API). Opus manual en claude.ai.
- Ronda 1: evaluación ciega (reutiliza datos Exp 2 + completa faltantes)
- Ronda 2: enriquecimiento (cada modelo ve las 11 evals de los demás, SUMA lo que falta)
- No es debate — es acumulación. Cada modelo aporta su ángulo.
- Tiempo estimado: 1-2 horas (Tier 4 batch)

### Exp 4.1 — Mesa Especializada ⬜ POST EXP 4
- Igual que Exp 4 pero cada modelo con prompt afinado a su fortaleza empírica
- Compara genérico vs especializado: ¿cuánto más profundo llega?

### Exp 4.2 — Sintetizador ⬜ POST EXP 4
- 6 modelos OS candidatos a sintetizador
- Reciben las 12 perspectivas y producen output integrado
- Mide: conexiones cross-celda, hallazgo central, puntos ciegos residuales

### Exp 4.3 — Mente Distribuida ⬜ POST EXP 4
- Pizarra compartida + micro-rondas
- 10 modelos activos + Sonnet pre-cargado
- Cada modelo contribuye diffs, no evaluaciones completas
- Más barato (~$0.50-1.50) y más rápido (15-30min) que Exp 4
- Perfila cada modelo: sembrador, profundizador, conector, detector de huecos
- Determina la "mente mínima" (menor nº modelos con ≥90% del valor)

### Exp 5 — Cadena de Montaje (código) ⬜ PROMPT LISTO
- 5 estaciones: Arquitecto → Implementador → Tester → Revisor → Optimizador
- 6 configuraciones con diferentes modelos por estación
- Compara con Exp 3 (modelo solo vs par vs cadena)

---

## §12 — AÑADIR: PRINCIPIO 31

31. **Rápido y profundo no existe.** Existen 5 velocidades para 5 contextos. Intentar profundidad en tiempo real es el error — genera respuestas mediocres con apariencia de profundidad. El sistema elige la cadencia correcta para el momento: reflejo para lo inmediato, batch nocturno para lo profundo. La calidad no se negocia — se agenda.

---

## §13 — AÑADIR A TABLA DE DOCUMENTOS

| Documento | Relación | Estado |
|-----------|----------|--------|
| ACTUALIZACION_MAESTRO_PRINCIPIO_31_TIERS.md | Principio 31 + 5 tiers de enjambre | CR0 (incorporado aquí) |
| PROMPT_CODE_EXP2_ENJAMBRE_EVALUADORES.md | Prompt para Code: 12 modelos evaluadores | Ejecutado parcial |
| PROMPT_CODE_EXP3_ENJAMBRE_CODIGO.md | Prompt para Code: 10 modelos × 5 tareas código | Pendiente |
| PROMPT_CODE_EXP4_MESA_REDONDA.md | Prompt para Code: mesa redonda 12 modelos | Corriendo |
| PROMPT_CODE_EXP4_1_MESA_ESPECIALIZADA.md | Prompt para Code: prompts por fortaleza | Pendiente |
| PROMPT_CODE_EXP4_2_SINTETIZADOR.md | Prompt para Code: quién escribe output final | Pendiente |
| PROMPT_CODE_EXP4_3_MENTE_DISTRIBUIDA.md | Prompt para Code: pizarra compartida | Pendiente |
| PROMPT_CODE_EXP5_CADENA_MONTAJE.md | Prompt para Code: pipeline industrial código | Pendiente |

---

**FIN ACTUALIZACIÓN — CR0**
