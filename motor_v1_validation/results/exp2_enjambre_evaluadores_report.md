# EXP 2 — ENJAMBRE DE EVALUADORES OS

Fecha: 2026-03-10
Referencia: Claude Sonnet (105 datapoints, 5 outputs × 21 celdas)

## Ranking Global de Evaluadores

| # | Modelo | Spearman | Pearson | MAE | Bias | F1(3+) | Exact% | Tiempo | Coste |
|---|--------|----------|---------|-----|------|--------|--------|--------|-------|
| 1 | glm-4.7 | 0.464 | 0.477 | 0.62 | +0.14 | 0.000 | 48% | 94.2s | $0.0030 |
| 2 | v3.2-chat | 0.426 | 0.492 | 0.72 | -0.46 | 0.103 | 46% | 18.9s | $0.0015 |
| 3 | qwen3-235b | 0.373 | 0.379 | 0.81 | +0.54 | 0.578 | 41% | 42.6s | $0.0020 |
| 4 | gpt-oss-120b | 0.280 | 0.302 | 1.07 | -0.74 | 0.348 | 36% | 39.6s | $0.0010 |
| 5 | deepseek-r1 | 0.247 | 0.220 | 1.00 | -0.62 | 0.293 | 36% | 30.1s | $0.0120 |
| 6 | deepseek-v3.1 | 0.220 | 0.196 | 0.91 | -0.34 | 0.190 | 33% | 17.8s | $0.0030 |
| 7 | minimax-m2.5 | 0.208 | 0.301 | 0.77 | -0.44 | 0.279 | 46% | 37.7s | $0.0020 |

## Spearman por Lente

| # | Modelo | Sp Salud | Sp Sentido | Sp Continuidad |
|---|--------|----------|------------|----------------|
| 1 | glm-4.7 | 0.450 | 0.755 | 0.525 |
| 2 | v3.2-chat | 0.346 | 0.416 | 0.501 |
| 3 | qwen3-235b | 0.493 | 0.362 | 0.349 |
| 4 | gpt-oss-120b | 0.291 | 0.247 | 0.295 |
| 5 | deepseek-r1 | 0.057 | 0.403 | 0.228 |
| 6 | deepseek-v3.1 | 0.409 | 0.338 | 0.081 |
| 7 | minimax-m2.5 | 0.081 | 0.345 | 0.149 |

## Spearman por Tipo de Output

| # | Modelo | Best | Medium | Worst |
|---|--------|------|--------|-------|
| 1 | glm-4.7 | — | 0.464 | — |
| 2 | v3.2-chat | 0.026 | 0.494 | 0.262 |
| 3 | qwen3-235b | 0.311 | 0.508 | 0.138 |
| 4 | gpt-oss-120b | 0.178 | 0.419 | 0.123 |
| 5 | deepseek-r1 | 0.302 | 0.217 | — |
| 6 | deepseek-v3.1 | 0.096 | 0.277 | 0.328 |
| 7 | minimax-m2.5 | -0.212 | 0.531 | — |

## Complementariedad (Top 10 pares)

| Par | Sp Fusión | Mejor Individual | Mejora |
|-----|-----------|-----------------|--------|
| v3.2-chat + gpt-oss-120b | 0.3828 | 0.4263 | -0.0435 |
| gpt-oss-120b + qwen3-235b | 0.3720 | 0.3734 | -0.0015 |
| v3.2-chat + qwen3-235b | 0.3692 | 0.4263 | -0.0571 |
| qwen3-235b + deepseek-v3.1 | 0.3585 | 0.3734 | -0.0149 |
| gpt-oss-120b + deepseek-v3.1 | 0.2776 | 0.2797 | -0.0021 |
| v3.2-chat + deepseek-v3.1 | 0.2554 | 0.4263 | -0.1709 |

## Asignación Modelo → Rol Evaluador

| Rol | Modelo | Métrica clave |
|-----|--------|---------------|
| evaluador_general | glm-4.7 | spearman=0.4644 |
| evaluador_insights | qwen3-235b | f1_3plus=0.578 |
| evaluador_sentido | glm-4.7 | spearman_sentido=0.755 |

## Distribución de Diferencias (modelo - Sonnet)

| Modelo | -3/-2 | -1 | 0 | +1 | +2/+3 |
|--------|-------|----|---|----|----|
| glm-4.7 | 0 | 5 | 10 | 4 | 2 |
| v3.2-chat | 15 | 31 | 48 | 8 | 3 |
| qwen3-235b | 2 | 10 | 43 | 33 | 17 |
| gpt-oss-120b | 33 | 20 | 38 | 12 | 2 |
| deepseek-r1 | 20 | 23 | 30 | 7 | 4 |
| deepseek-v3.1 | 18 | 27 | 35 | 20 | 5 |
| minimax-m2.5 | 13 | 21 | 39 | 8 | 3 |

## Veredicto

**Evaluador OS insuficiente.** Mejor Spearman=0.464. Sonnet necesario.

**Sentido débil:** mejor Sp Sentido=0.755 < 0.80. Sonnet necesario para Sentido.

**Insights débil:** mejor F1(3+)=0.578 < 0.60. Sonnet mejor para niveles 3+.

---
*Generado por exp2_analyze_evaluators.py*