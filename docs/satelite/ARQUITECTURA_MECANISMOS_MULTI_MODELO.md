# ARQUITECTURA DE MECANISMOS MULTI-MODELO — Basada en Exp 4 completo

**Estado:** CR0 — Jesús valida
**Fecha:** 2026-03-12
**Fuente:** Exp 4 (mesa redonda) + Exp 4.1 (especializada) + Exp 4.2 (sintetizador) + Exp 4.3 (mente distribuida) + evaluación externa Claude

---

## 1. LOS 5 MECANISMOS Y QUÉ PRODUCE CADA UNO

### 1A. Evaluación individual en paralelo (Exp 4 R1)

**Qué es:** N modelos reciben el mismo input y evalúan independientemente.

**Produce:**
- Score por celda con varianza inter-evaluador medible
- Detección de sesgos: quién infla (+0.84 Qwen3), quién defla (-0.45 GPT-OSS)
- Correlaciones entre evaluadores (Sonnet↔Qwen3: 0.605, R1↔V3.2R: 0.642)
- Mapa de "lobos solitarios" (quién da 3+ cuando nadie más lo hace)

**No produce:** Conexiones, puntos ciegos, síntesis, convergencia.

**Datos:** Media global 1.71, solo 7/105 celdas con consenso mayoritario (≥6 dan 3+). Std medio 0.71-0.94 por output.

**Coste:** N llamadas paralelas (~12 modelos × 5 outputs = 60 llamadas). ~$0.50-1.00.

**Cuándo usar:** Screening rápido de calidad. Calibrar modelos nuevos. Seleccionar quién entra en mecanismos más caros. Es el termómetro, no el tratamiento.

---

### 1B. Mesa redonda con enriquecimiento (Exp 4 R2)

**Qué es:** Tras R1, cada modelo ve las evaluaciones de los demás y reevalúa.

**Produce:**
- Convergencia masiva: 7→70 celdas con consenso mayoritario (10x)
- 16 celdas emergentes (no existían en R1)
- Reducción de varianza

**No produce:** Conexiones cross-celda, hallazgos centrales, puntos ciegos.

**Datos:** Media 3.27 (vs 1.71 R1), 93/105 celdas 3+.

**Atención:** 77% de las convergencias van hacia donde Qwen3 ya apuntaba en R1 — efecto líder parcial, no solo convergencia ciega. Sonnet predice R2 mejor que nadie (ρ=0.656).

**Coste:** 2N llamadas (R1+R2). ~$1-2.

**Cuándo usar:** Evaluación fiable con consenso. Cuando necesitas UNA respuesta validada por múltiples perspectivas, no N opiniones dispersas.

---

### 1C. Mesa especializada (Exp 4.1)

**Qué es:** Misma mesa, pero cada modelo recibe prompt afinado a su zona fuerte.

**Produce:**
- +0.55 media en zona de foco (mejora significativa)
- -0.14 fuera de foco (deterioro leve)
- Delta global: +0.10 (7/12 modelos mejoran)
- Cambia la mesa mínima: V3.2-chat + V3.1 = 97.9% (vs Qwen3 + GPT-OSS = 94.6% con genérico)

**No produce:** Más que la mesa genérica en cobertura global (+2 celdas: 93→95).

**Modelos que mejoran con especialización:** V3.2-Reasoner (+0.50), R1 (+0.43), MiniMax (+0.28), V3.1 (+0.19), V3.2-chat (+0.16).

**Modelos que empeoran:** Kimi (-0.48), Opus (-0.40), Qwen3 (-0.31), GLM (-0.27). Los infladores genéricos pierden ventaja con prompt específico.

**Coste:** Igual que mesa genérica — solo cambian los prompts.

**Cuándo usar:** Siempre que uses mesa redonda. No hay razón para no especializar: mismo coste, mejor resultado en foco.

---

### 1D. Sintetizador (Exp 4.2)

**Qué es:** Un modelo recibe TODAS las evaluaciones de la mesa y produce output integrado.

**Produce:**
- Conexiones cross-lente (media 3.6/output con Cogito)
- Hallazgos centrales no-genéricos (5/5 con Cogito)
- Meta-patrones (media 3.0/output)
- Puntos ciegos residuales (media 2.6/output)
- 100% de celdas igualan max mecánico (no pierde nada)

**No produce:** Scores superiores al max mecánico (0 celdas por encima).

**Ranking sintetizadores:**

| # | Modelo | Outputs OK | Conexiones | Hallazgos | Tiempo |
|---|--------|-----------|------------|-----------|--------|
| 1 | **Cogito-671b** | 5/5 | 3.6/output | 5/5 no-genéricos | 47s |
| 2 | DeepSeek-R1 | 5/5 | 3.0/output | 5/5 no-genéricos | 55s |
| 3 | Qwen3-235b | 5/5 | 2.2/output | 3/5 no-genéricos | 137s |
| 4 | V3.2-chat | 5/5 | 2.0/output | 2/5 no-genéricos | 121s |
| ✗ | GLM-5 | 0/5 (parse fail) | — | — | — |
| ✗ | MiniMax M2.5 | 0/5 (parse fail) | — | — | — |

**Coste:** 1 llamada extra (~47s con Cogito). ~$0.05.

**Cuándo usar:** SIEMPRE como paso final después de cualquier mesa. Convierte datos (scores) en comprensión (conexiones causales). Es lo que un humano necesita para decidir. Coste marginal despreciable.

---

### 1E. Pizarra / Mente distribuida (Exp 4.3)

**Qué es:** Pizarra compartida donde N modelos contribuyen evidencias por turnos. Múltiples rondas hasta convergencia.

**Produce:**
- 425 conexiones entre celdas (exclusivo)
- 239 puntos ciegos detectados (exclusivo)
- 94/105 celdas 3+ (evaluación externa Claude) — cobertura equivalente a mesa redonda
- Contenido rico con capas de profundización: cada ronda añade ángulos

**No produce:** Scores más altos que la mesa redonda (3.06 vs 3.27 evaluación externa). El auto-tracking infla +0.93 puntos.

**Perfiles de modelos en la pizarra:**

| Modelo | Contribuciones | Conexiones | P.Ciegos | Perfil |
|--------|---------------|------------|----------|--------|
| GPT-OSS | 119 | 77 | 46 | Motor principal |
| MiniMax M2.5 | 75 | 55 | 45 | Segundo motor |
| Qwen3-235b | 63 | 48 | 25 | Tercer contribuidor |
| V3.2-chat | 56 | 52 | 28 | Conector fuerte |
| V3.1 | 52 | 45 | 22 | Contribuidor sólido |
| R1 | 44 | 30 | 12 | Contribuidor |
| V3.2-Reasoner | 42 | 28 | 14 | Contribuidor |
| Opus | 33 | 34 | 8 | Conector (caro) |
| Cogito | 31 | 29 | 22 | Detector de huecos |
| Kimi | 25 | 19 | 15 | Contribuidor menor |
| GLM-4.7 | 20 | 8 | 2 | Marginal |

**Convergencia:** 3/5 outputs convergieron en 4-5 rondas. 2/5 llegaron al máximo de rondas sin converger.

**Coste:** Alto. 10-11 modelos × 4-5 rondas = 40-55 llamadas por output. ~$2-5 por output.

**Cuándo usar:** Cuando necesitas PENSAR, no evaluar. Exploración profunda de un problema. Batch nocturno. Onboarding de dominio nuevo. Su valor está en las conexiones y puntos ciegos, no en los scores.

---

## 2. MAPA DE USO POR NECESIDAD

| Necesitas... | Mecanismo | Coste | Tiempo |
|---|---|---|---|
| Screening rápido de calidad | Individual paralelo (1A) | ~$0.50 | ~2min |
| Evaluación fiable con consenso | Mesa redonda R1+R2 (1B) | ~$1-2 | ~5min |
| Profundidad en área concreta | Mesa especializada (1C) | ~$1-2 | ~5min |
| Entender conexiones causales | Sintetizador Cogito (1D) | ~$0.05 extra | ~47s extra |
| Explorar problema en profundidad | Pizarra distribuida (1E) | ~$2-5 | ~30-60min |
| Saber qué modelos usar | Individual + análisis de sesgo | ~$0.50 | ~5min |

---

## 3. COMPOSICIONES POR TIER

### Tier 2 — Respuesta (5-15s, $0.01-0.05)

```
1 modelo: V3.2-chat (89.5% cobertura individual)
Sin mesa, sin evaluación. Respuesta directa.
```

### Tier 3 — Análisis (1-5min, $0.10-0.50)

```
Mesa especializada 1 ronda (sin R2):
  V3.2-chat + V3.1 + R1 (3 modelos, prompts especializados)
  = 100% cobertura
  
+ Cogito sintetiza (1 llamada extra, 47s)
  = Conexiones cross-lente + hallazgo central

Total: 4 llamadas. ~$0.30. ~3min.
```

### Tier 4 — Profundo (30-60min, $1-3)

```
PASO 1: Pizarra distribuida (7 modelos, ~5 rondas)
  GPT-OSS + MiniMax + Qwen3 + V3.2-chat + V3.1 + R1 + V3.2-Reasoner
  → Contenido rico: conexiones + puntos ciegos
  
PASO 2: Cogito sintetiza la pizarra
  → Hallazgo central + meta-patrones + puntos ciegos residuales

PASO 3: Panel evaluador externo (V3.2-chat + V3.1 + R1, prompts especializados)
  → Scores calibrados sin inflación del auto-tracking

Total: ~40-50 llamadas. ~$2-3. ~45min batch.
```

### Tier 5 — Cartografía (horas, $5-20)

```
PASO 1: Pizarra distribuida completa (11 modelos, hasta convergencia)
PASO 2: Mesa especializada R1+R2 como evaluación externa
PASO 3: Cogito sintetiza
PASO 4: Loop — detectar puntos ciegos residuales → nueva ronda de pizarra
PASO 5: Sintetizar convergencias cross-output

Total: ~100+ llamadas. ~$5-10. ~2-4h batch.
```

---

## 4. MODELOS POR ROL (DECISIONES CR0)

### Evaluadores (mesa de consenso)
- **V3.2-chat** — mejor evaluador individual especializado (89.5% solo, 3.02 media esp)
- **DeepSeek-V3.1** — segundo evaluador, complementario (2.99 media esp)
- **DeepSeek-R1** — tercer evaluador, completa cobertura a 100% (2.00 media esp)
- Estos 3 = mesa mínima para evaluación fiable

### Contribuidores de pizarra
- **GPT-OSS** — motor principal (119 contribuciones, el más productivo)
- **MiniMax M2.5** — segundo motor (75 contrib, fuerte en conexiones)
- **Qwen3-235b** — tercer contribuidor (63 contrib, buen detector)
- **V3.2-chat** — fuerte en conexiones (52 conexiones)
- **V3.1, R1, V3.2-Reasoner** — contribuidores sólidos
- ~~Opus~~ — prescindible (33 contrib, $75/M, 0 aportes únicos en Exp 4)
- ~~GLM-4.7~~ — marginal (20 contrib, 2 puntos ciegos)

### Sintetizador
- **Cogito-671b** — sin discusión. 3.6 conexiones/output, 5/5 hallazgos no-genéricos, 47s, barato.

### Descartados de pipelines automatizados
- **Opus** — 0 aportes únicos, $75/M, prescindible en toda evaluación. Se usa en chat ($0) cuando se necesite.
- **Sonnet** — 0 aportes únicos, prescindible. Predice R2 bien (ρ=0.656) pero caro para el valor que aporta.
- **Kimi-K2.5** — 0/5 en R2 de Exp 4.1, empeora con especialización (-0.48). Fuera.
- **GLM-4.7** — marginal en pizarra (20 contrib, 2 ciegos). No justifica el slot.

---

## 5. HALLAZGOS METODOLÓGICOS

### Auto-evaluación infla ~1 punto
La pizarra (auto-tracking) da media 3.99. Evaluación externa: 3.06. Delta: +0.93. Cualquier mecanismo donde los participantes se ponen nota necesita evaluación externa para ser fiable.

### La especialización de prompts redistribuye valor
No sube el total significativamente (+2 celdas) pero cambia QUIÉN es útil. Qwen3 pasa de "cerebro" a "contribuidor". V3.2-chat pasa a líder. La mesa mínima cambia por completo.

### Los infladores genéricos pierden ventaja con prompt específico
Qwen3 (-0.31), Kimi (-0.48), Opus (-0.40). Los modelos que parecían los mejores con prompt genérico caen cuando se les pide rigor en zona concreta.

### Sonnet no era mala referencia — era cara
Predice consenso R2 mejor que Qwen3 (ρ=0.656 vs 0.638). El problema no era calibración sino precio + ausencia de diversidad.

### El valor de la pizarra está en las conexiones, no en los scores
94/105 celdas 3+ (≈mesa redonda) + 425 conexiones + 239 puntos ciegos. La diferencia cualitativa es real, la cuantitativa no.

### GPT-OSS invierte su rol según mecanismo
En Exp 4 (evaluador): máximo deflactor (-0.45), esponja que absorbe de Qwen3.
En Exp 4.3 (pizarra): máximo contribuidor (119), motor principal.
El rol del modelo depende del mecanismo, no es fijo.

---

## 6. DATOS DE REFERENCIA

### Comparación agregada cross-experimento (evaluados externamente)

| Método | Media | 3+/105 | Conexiones | Evaluador |
|--------|-------|--------|------------|-----------|
| Exp 4 R1 max mecánico | 2.89 | 77 | 0 | 12 modelos |
| Exp 4 R2 mesa redonda | 3.27 | 93 | 0 | 12 modelos post-R2 |
| Exp 4.1 mesa especializada | ~3.30 | 95 | 0 | 12 modelos con prompts foco |
| Exp 4.3 mente distribuida (ext) | 3.06 | 94 | 425 | Claude externo |
| Exp 4.3 auto-tracking | 3.99 | 105 | 425 | Auto (inflado +0.93) |

### Mesa mínima por mecanismo

| Mecanismo | Mesa mínima | Cobertura |
|-----------|------------|-----------|
| Genérico (Exp 4) | Qwen3 + GPT-OSS | 94.6% (88/93) |
| Especializado (Exp 4.1) | V3.2-chat + V3.1 | 97.9% (93/95) |
| Especializado completa | V3.2-chat + V3.1 + R1 | 100% (95/95) |
| Pizarra mínima | GPT-OSS + MiniMax + Qwen3 | 40% (bajo sin más modelos) |
| Pizarra recomendada | 7 modelos (GPT-OSS→Cogito) | 76% contribuciones |

---

## 7. CAPA DE INFRAESTRUCTURA: PROXY MULTI-PROVIDER

### Problema

Los mecanismos de §1-§3 usan 10+ modelos de 3+ proveedores (Together, DeepSeek API, OpenRouter). Cada proveedor tiene su API key, formato, pricing y disponibilidad. Gestionar N proveedores directamente es frágil: si uno cae o sube precios, hay que tocar código.

### Solución: Router unificado

Un único punto de entrada que abstrae los proveedores. Dos opciones viables:

**Opción A — Hugging Face Inference Providers (router hosted)**

HF no es un proveedor de inferencia — es un router que da acceso a Together, Fireworks, Sambanova, Replicate, Nebius, Novita y otros con una sola API y un solo token.

- 1 API key (HF token) → acceso a todos los providers integrados
- Sin markup: HF pasa el coste del provider directo
- Cambiar provider = cambiar 1 parámetro, no código
- Catálogo más grande que cualquier provider solo
- PRO $9/mes incluye $2 créditos/mes de inferencia
- Billing unificado: 1 factura en vez de N

```python
# Ejemplo: mismo modelo, cambiar provider con 1 línea
from huggingface_hub import InferenceClient
client = InferenceClient(token="hf_xxx")

# Via Together
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    provider="together-ai",
    messages=[...]
)

# Via Fireworks (si Together cae)
response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    provider="fireworks-ai",
    messages=[...]
)
```

**Opción B — LiteLLM (proxy self-hosted)**

Proxy open-source que unifica 100+ providers con formato OpenAI-compatible. Se puede usar sobre HF o directamente sobre los providers.

- Self-hosted: control total, sin dependencia de HF
- Formato OpenAI estándar para todos los providers
- Fallback automático: si provider A falla → provider B
- Load balancing entre providers
- Logging centralizado de tokens, latencia, coste

```yaml
# litellm config
model_list:
  - model_name: deepseek-v3.2
    litellm_params:
      model: deepseek/deepseek-chat
      api_key: os.environ/DEEPSEEK_API_KEY
  - model_name: deepseek-v3.2
    litellm_params:
      model: together_ai/deepseek-ai/DeepSeek-V3-0324
      api_key: os.environ/TOGETHER_API_KEY
  # Fallback automático: si DeepSeek directo falla, usa Together
```

### Decisión CR0: Opción mixta

```
CAPA 1 — HF como router por defecto
  Ventaja: 1 token, 1 billing, catálogo completo
  Se usa para: todos los modelos disponibles vía HF providers

CAPA 2 — API directa como fallback
  Para: modelos no disponibles vía HF (DeepSeek API directo, etc.)
  O cuando: HF routing añade latencia inaceptable

CAPA 3 — LiteLLM como proxy unificador (futuro)
  Cuando: el volumen justifique self-hosting
  Ventaja: fallback automático, load balancing, logging
```

### Mapa provider → modelos (marzo 2026)

| Modelo | Provider principal | Fallback | model_id HF |
|--------|-------------------|----------|-------------|
| DeepSeek V3.2 | DeepSeek API | Together | `deepseek-ai/DeepSeek-V3-0324` |
| DeepSeek V3.2 Reasoner | DeepSeek API | — | `deepseek-ai/DeepSeek-R1` |
| DeepSeek R1 | Together | DeepSeek API | `deepseek-ai/DeepSeek-R1` |
| Qwen3-235B | Together | Fireworks | `Qwen/Qwen3-235B-A22B` |
| Qwen3-Coder 480B | Together | — | `Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8` |
| GPT-OSS 120B | Together | — | `openai/gpt-oss-120b` |
| Cogito 671B | Together | — | `deepcogito/cogito-v2-preview-deepseek-671b` |
| MiniMax M2.5 | Together | — | `MiniMaxAI/MiniMax-M2.5` |
| Kimi-Dev 72B | Together | — | `moonshotai/Kimi-Dev-72B` |
| MiMo-V2-Flash | Together | — | `xiaomi/MiMo-V2-Flash` |
| GLM-5 | Together | — | `zai-org/GLM-5` |

**NOTA:** Verificar disponibilidad real de cada model_id antes de cada experimento. Los providers cambian catálogo sin aviso.

### Principios de routing

1. **Un solo punto de cambio.** Si un provider cae, se cambia en config sin tocar lógica de negocio. (Principio 25: OS-first, sin dependencia de proveedor.)
2. **Prioridad: API directa del fabricante > Together > otros.** DeepSeek directo es más barato y rápido que DeepSeek vía Together.
3. **Fallback silencioso.** Si el primary falla tras 2 retries, el proxy cambia a fallback sin intervención.
4. **Logging por provider.** Cada llamada registra: modelo, provider, tokens, latencia, coste. Esto alimenta decisiones de routing futuras.
5. **No lock-in.** Nunca usar features propietarias de un provider que no existan en otros. El formato es siempre OpenAI-compatible.

---

*Generado a partir de: exp4_mesa_redonda_report.json, exp4_1_comparison_report.json, exp4_2_sintetizador_report.json, exp4_3_mente_distribuida_report.json, exp4_3_evaluacion_externa_claude.json, ANALISIS_PROFUNDO_EXP4_MESA_REDONDA.md*
