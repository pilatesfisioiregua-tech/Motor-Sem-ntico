# MAPA DE MODELOS OS PARA OMNI-MIND — Marzo 2026

**Estado:** CR0 — Jesús valida
**Fecha:** 2026-03-12
**Fuente:** Onyx Leaderboard, benchmarks oficiales, resultados Exp 4, búsqueda HuggingFace

---

## LEADERBOARD GENERAL (febrero-marzo 2026)

### Tier S — Frontier OS (compiten con GPT-5/Claude Opus)
| Modelo | Params (total/activos) | Coding | Reasoning | Chat Arena | Licencia |
|--------|----------------------|--------|-----------|------------|----------|
| GLM-5 | 744B / 40B | SWE 77.8 | AIME 95.7 | #1 (1451) | Open |
| Kimi K2.5 | 1T / 32B | HumanEval 99.0 | AIME 96.1 | #2 (1447) | MIT mod |
| MiniMax M2.5 | 230B / 10B | SWE 80.2 | AIME 89.3 | 1421 | Open |
| DeepSeek V3.2 | 685B / 37B | LiveCode 90% | AIME 89.3 | 1421 | MIT |
| Step-3.5-Flash | 196B | LiveCode 86.4 | AIME 97.3 | — | — |
| Qwen 3.5 | 397B | SWE 76.4 | GPQA 88.4 | 1401 | Apache 2.0 |

### Tier A — Excelentes
| Modelo | Params | Coding | Reasoning | Notas |
|--------|--------|--------|-----------|-------|
| GLM-4.7 | 355B / 32B | HumanEval 94.2, LiveCode 84.9 | AIME 95.7 | Mejor coding puro |
| MiMo-V2-Flash | 309B / 15B | SWE superior a V3.2 | AIME 94.1 | Ultra-eficiente, $0.10/M in |
| DeepSeek R1 | 671B | — | AIME 96.7 | Reasoning puro |
| Qwen3-235B | 235B / 22B | LiveCode 80.6 | GPQA 83.7 | Generalista, 262K ctx |

### Tier B — Producción sólida
| Modelo | Params | Notas |
|--------|--------|-------|
| GPT-OSS 120B | 117B / 5.1B | Corre en 1 GPU H100. Barato ($0.60/M). |
| Mistral Large | 675B | HumanEval 92.0, LiveCode 82.8 |
| Nemotron Ultra 253B | 253B | GPQA 76.0, IFEval 89.5 |
| Nemotron Super 49B | 49B | MATH-500 97.4 (iguala R1) |
| Step3 | 316B | — |

### Tier C — Útiles en nicho
| Modelo | Notas |
|--------|-------|
| GPT-OSS 20B | Ultra-barato ($0.20/M). Fontanería. |
| Llama 4 Maverick | 400B/17B. 1M ctx. Multimodal. 8 meses viejo. |
| Gemma 3 27B | Edge deployment. |
| Nemotron Nano 30B | 1M ctx, 30B params. Edge. |

### Coding especialistas (no en leaderboard general)
| Modelo | Benchmark | Notas |
|--------|-----------|-------|
| Qwen3-Coder 480B | SOTA agentic coding | 256K ctx, diseñado para repo-scale |
| Qwen3-Coder-Next 80B | Eficiente | 3B activos, corre en 1 RTX 4090 |
| Kimi-Dev 72B | #1 SWE-bench patches | Especialista en patching real |

---

## MODELOS QUE NO TENÍAMOS EN EL RADAR

### 1. Kimi K2.5 (Moonshot AI) — NUEVO TIER S
- **1T params, 32B activos.** HumanEval 99.0 (el más alto de todos). MMLU 92.0. IFEval 94.0.
- **Agent Swarm:** ejecuta hasta 100 sub-agentes en paralelo. 200-300 tool calls secuenciales.
- **Thinking mode** con cadenas de razonamiento transparentes.
- **Heavy Mode:** 8 paths de razonamiento en paralelo, selecciona mejor respuesta.
- **Licencia MIT modificada** (atribución si >100M MAU o >$20M/mes).
- **Disponible en:** Together, Fireworks, OpenRouter.
- **Para OMNI-MIND:** Candidato fuerte para pizarra distribuida (agent swarm nativo), evaluador (IFEval 94.0), y razonamiento profundo.

### 2. Step-3.5-Flash (StepFun) — NUEVA ENTRADA TIER S
- **196B params.** AIME 97.3 (el más alto del leaderboard). LiveCode 86.4.
- Más pequeño que sus pares Tier S pero con rendimiento de frontier.
- **Para OMNI-MIND:** Candidato para Debugger (razonamiento matemático extremo) y evaluador donde la precisión lógica importa.

### 3. Qwen 3.5 (Alibaba) — NUEVA ENTRADA TIER S
- **397B params.** GPQA Diamond 88.4 (el más alto). IFEval 92.6. SWE 76.4.
- La mejor instrucción-siguiendo del leaderboard.
- Apache 2.0 — la licencia más permisiva de Tier S.
- **Para OMNI-MIND:** Candidato para evaluador especializado (instrucción-siguiendo + razonamiento científico). Reemplazaría a Qwen3-235B en mesa de evaluación.

### 4. MiMo-V2-Flash (Xiaomi) — YA EN RADAR PERO SUBESTIMADO
- **309B / 15B activos.** Supera a DeepSeek V3.2 y Kimi K2 en SWE-bench con 1/2-1/3 de params.
- **$0.10/M input, $0.30/M output.** El más barato de Tier A por un factor de 10x.
- 150 tok/s output.
- **Para OMNI-MIND:** El modelo que debería estar en CADA tier como opción barata. Tier 2 solo, Tier 3 como tester, Tier 4 como contribuidor de pizarra.

### 5. Nemotron Super 49B (NVIDIA) — NUEVA ENTRADA
- **49B params.** MATH-500 97.4 (iguala DeepSeek R1). 1M ctx.
- Increíblemente eficiente para su tamaño.
- **Para OMNI-MIND:** Candidato para cálculos y validación numérica dentro de la Matriz. Barato + preciso en math.

### 6. Kimi-Dev 72B (Moonshot) — YA DETECTADO EN EXP 5
- **#1 SWE-bench** para patching real de código.
- 72B params — manejable.
- **Para OMNI-MIND:** El mejor Revisor/Debugger de código. Ya en Exp 5 Config A como E4.

---

## MAPA POR ROL EN OMNI-MIND

### A) MOTOR COGNITIVO (análisis, evaluación, síntesis de la Matriz 3L×7F)

| Rol | Modelo recomendado | Alternativa | Por qué |
|-----|-------------------|-------------|---------|
| **Evaluador principal** | DeepSeek V3.2 | Qwen 3.5 | V3.2: Exp 4.1 lo validó como líder de mesa especializada. Qwen 3.5: IFEval 92.6 (mejor instrucción-siguiendo) |
| **Segundo evaluador** | DeepSeek V3.1 | GLM-4.7 | V3.1: complementario a V3.2, cobertura 100% con V3.2-chat en Exp 4.1 |
| **Tercer evaluador** | DeepSeek R1 | Kimi K2.5 | R1: completa cobertura en Exp 4.1. K2.5: IFEval 94.0, potencialmente mejor |
| **Sintetizador** | Cogito 671B | — | Exp 4.2: #1 sin discusión. 3.6 conexiones/output, 47s |
| **Contribuidor pizarra #1** | GPT-OSS 120B | MiMo-V2-Flash | GPT-OSS: 119 contrib en Exp 4.3. MiMo: más barato, posiblemente tan productivo |
| **Contribuidor pizarra #2** | MiniMax M2.5 | Kimi K2.5 | MiniMax: 75 contrib en 4.3, SWE 80.2%. K2.5: agent swarm nativo |
| **Contribuidor barato** | MiMo-V2-Flash | GPT-OSS 20B | $0.10/M input. Para llenar volumen en pizarra sin coste |
| **Razonador profundo** | DeepSeek V3.2 Reasoner | Step-3.5-Flash | Para debug lógico y root cause en la Matriz |

### B) ENJAMBRE DE CÓDIGO (implementar, testear, debugar, desplegar)

| Rol | Modelo recomendado | Alternativa | Por qué |
|-----|-------------------|-------------|---------|
| **Arquitecto** | DeepSeek V3.2 | GLM-5 | V3.2: interfaces limpias. GLM-5: systems engineering, más caro |
| **Implementador** | Qwen3-Coder 480B | Kimi K2.5 | SOTA agentic coding, 256K ctx para repo-scale |
| **Tester** | MiniMax M2.5 | MiMo-V2-Flash | SWE-bench 80.2%, mentalidad adversarial. MiMo: ultra-barato |
| **Debugger R1** | DeepSeek V3.2 Reasoner | Step-3.5-Flash | Traza lógica paso a paso, root cause |
| **Debugger R2** | Cogito 671B | Kimi-Dev 72B | Perspectiva diferente. Kimi-Dev: #1 en patching real |
| **Revisor** | GLM-5 | Qwen 3.5 | Systems engineering, pensamiento sistémico. Qwen 3.5: IFEval top |
| **Optimizador** | Qwen3-235B Instruct | GPT-OSS 120B | Barato, práctico, generalista |
| **Generador de tests (bulk)** | MiMo-V2-Flash | GPT-OSS 120B | Ultra-barato para generar muchos tests |

---

## MODELOS A INVESTIGAR (no probados aún)

| Modelo | Por qué | Riesgo |
|--------|---------|--------|
| **Kimi K2.5** | Agent swarm nativo, IFEval 94.0, HumanEval 99.0 | Kimi K2 (versión anterior) fue INERTE en Exp 4 R2 (0/5). K2.5 podría ser diferente |
| **Qwen 3.5** | GPQA 88.4, IFEval 92.6, Apache 2.0 | Nuevo, sin datos empíricos nuestros |
| **Step-3.5-Flash** | AIME 97.3, LiveCode 86.4, 196B | No sabemos disponibilidad en Together/HF |
| **MiMo-V2-Flash** | $0.10/M, supera V3.2 en SWE-bench | Nuevo, sin datos empíricos nuestros |
| **Nemotron Super 49B** | MATH-500 97.4 en 49B params | Nicho: solo math/lógica |

---

## PROVIDERS VÍA HUGGING FACE (21 integrados)

```
black-forest-labs, cerebras, clarifai, cohere, fal-ai, featherless-ai, 
fireworks-ai, groq, hf-inference, hyperbolic, nebius, novita, nscale, 
nvidia, openai, ovhcloud, publicai, replicate, sambanova, scaleway, 
together, wavespeed, zai-org
```

**Los que importan para OMNI-MIND:**
- **Together:** mayor catálogo de modelos OS (Qwen, GPT-OSS, MiniMax, Cogito, MiMo, GLM, Llama)
- **DeepSeek API directo:** más barato para V3.2 y Reasoner que vía Together
- **Fireworks:** fallback rápido, buena latencia, DeepSeek R1 disponible
- **Groq:** ultra-rápido para modelos pequeños (Llama 70B en ms)
- **Sambanova:** algunos modelos gratis
- **zai-org:** GLM-5 directo de Zhipu

---

## DECISIONES PENDIENTES (CR0)

1. **¿Probar Kimi K2.5 en Exp 4 bis?** Agent swarm + IFEval 94.0 lo hacen candidato a reemplazar varios modelos en pizarra. Pero Kimi K2 (anterior) fracasó en R2.

2. **¿Probar MiMo-V2-Flash como sustituto barato en TODOS los tiers?** A $0.10/M podría hacer Tier 2 prácticamente gratis y Tier 3 a $0.05.

3. **¿Probar Qwen 3.5 como evaluador?** IFEval 92.6 sugiere que podría ser mejor que V3.2-chat para instrucción-siguiendo en evaluación.

4. **¿Incorporar Step-3.5-Flash como debugger?** AIME 97.3 es el math score más alto. Para validación numérica dentro de la Matriz.

5. **¿Hacer un Exp 1 bis con los 6 modelos nuevos?** Kimi K2.5, Qwen 3.5, Step-3.5-Flash, MiMo-V2-Flash, Nemotron Super 49B, Kimi-Dev 72B — evaluarlos en las mismas 5 tareas del Exp 1 original para tener datos comparables.

---

*Fuentes: Onyx Open LLM Leaderboard (feb 2026), VERTU leaderboard analysis, BentoML guide, Clarifai reasoning models, DataCamp Kimi K2 guide, HuggingFace Inference Providers docs, resultados empíricos Exp 4/4.1/4.2/4.3*
