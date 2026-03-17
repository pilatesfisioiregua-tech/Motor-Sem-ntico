# EXP 1 BIS — 6 Modelos Nuevos × 5 Tareas

**Fecha:** 2026-03-11
**Provider:** OpenRouter

## Tabla Principal: Modelo × Tarea (scores 0-1)

| Modelo | T1 Cognitivo | T2 Evaluador | T3 Math | T4 Código | T5 Síntesis | **Media** | **Coste** |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| kimi-k2.5 | 0.81 🟡 | **0.89** 🟢 | 0.80 🟡 | 0.80 🟡 | **1.00** 🟢 | **0.86** | $0.038 |
| qwen3.5-397b | 0.59 🔴 | **0.88** 🟢 | 0.80 🟡 | **1.00** 🟢 | **1.00** 🟢 | **0.85** | $0.033 |
| nemotron-super | **1.00** 🟢 | **0.88** 🟢 | **1.00** 🟢 | **0.90** 🟢 | **1.00** 🟢 | **0.96** | $0.007 |
| step-3.5-flash | **1.00** 🟢 | **0.89** 🟢 | **1.00** 🟢 | **1.00** 🟢 | **1.00** 🟢 | **0.98** | $0.019 |
| mimo-v2-flash | **1.00** 🟢 | **0.89** 🟢 | 0.60 🔴 | **1.00** 🟢 | **1.00** 🟢 | **0.90** | $0.001 |
| devstral | **1.00** 🟢 | 0.50 🔴 | 0.80 🟡 | **1.00** 🟢 | **1.00** 🟢 | **0.86** | $0.004 |

## Rankings

### Overall

| # | Modelo | Score | Coste |
|---|--------|:---:|:---:|
| 1 | step-3.5-flash | 0.98 | $0.019 |
| 2 | nemotron-super | 0.96 | $0.007 |
| 3 | mimo-v2-flash | 0.90 | $0.001 |
| 4 | kimi-k2.5 | 0.86 | $0.038 |
| 5 | devstral | 0.86 | $0.004 |
| 6 | qwen3.5-397b | 0.85 | $0.033 |

### Mejor por Tarea

- **T1 (Análisis Cognitivo):** Mejor=nemotron-super, Media=0.90
- **T2 (Evaluación Output):** Mejor=step-3.5-flash, Media=0.82
- **T3 (Razonamiento Math):** Mejor=nemotron-super, Media=0.83
- **T4 (Generación Código):** Mejor=qwen3.5-397b, Media=0.95
- **T5 (Síntesis Multi-Fuente):** Mejor=kimi-k2.5, Media=1.00

## Recomendaciones por Rol OMNI-MIND

| **Pizarra (agent swarm)** | kimi-k2.5 | ✅ SÍ (0.91 vs 0.8) | T1 + T5 ≥ 0.80 → Supera GPT-OSS |
| **Evaluador** | qwen3.5-397b | ✅ SÍ (0.88 vs 0.85) | T2 ≥ 0.85 → Discriminación perfecta en H4/H5 |
| **Math/Validación numérica** | nemotron-super | ✅ SÍ (1.00 vs 0.8) | T3 ≥ 0.80 → 4/5 problemas correctos |
| **Debugger/Razonador** | step-3.5-flash | ✅ SÍ (1.00 vs 0.85) | T3 + T4 ≥ 0.85 → Math + código funcional |
| **Tier barato universal** | mimo-v2-flash | ✅ SÍ (0.90 vs 0.65) | Media ≥ 0.65 → Aceptable en todo a $0.10/M |
| **Patcher (#1 SWE)** | devstral | ✅ SÍ (1.00 vs 0.85) | T4 ≥ 0.85 → Tests pasan sin debug |

## Coste Total

- **Tokens input:** 13,781
- **Tokens output:** 98,240
- **Coste total:** $0.102

---
*Generado: 2026-03-11 01:06:49*