# EXP 5b — Nuevos Modelos OS en Pipeline Multi-Estación

**Fecha:** 2026-03-11
**Provider:** OpenRouter
**Pregunta:** ¿Los modelos nuevos (exp1bis) resuelven T1 y T4 que quedaron en 0% en exp5?

## Resultado Principal

| Task | Exp 5 Mejor | Exp 5b Mejor | Config ganadora | Delta |
|------|:---:|:---:|:---:|:---:|
| **T1** Edge Function (Deno/TS) | 0% | **100%** | N2_cheap, N3_coding | **+100pp** |
| **T4** Orquestador (Python async) | 0% | **0%** | — | +0pp |

## Tabla Detallada: Config x Task

| Config | Modelos | T1 | T4 | Debug | Tiempo | Tokens |
|--------|---------|:---:|:---:|:---:|:---:|:---:|
| N1_top | step-3.5 + qwen-3.5-397b | 2/10 (20%) | 0/0 (E1 vacío) | 3 / 0 | 572s | 76K |
| N2_cheap | mimo-v2 + nemotron + step-3.5 | **7/7 (100%)** | 0/4 (0%) | 1 / 3 | 848s | 112K |
| N3_coding | step-3.5 + devstral | **10/10 (100%)** | 0/0 (E1 vacío) | 3 / 0 | 455s | 73K |

## Veredicto

### T1: El problema ERA los modelos
- 2 de 3 configs llegaron al **100%** (N2_cheap 7/7, N3_coding 10/10)
- N1_top llegó a 20% — el modelo razonador (qwen-3.5-397b) no es óptimo para código TS
- **El pipeline multi-estación funciona para tareas de código de complejidad media**
- Regla skip-E5/E6 validada: Reviewer/Optimizer rompieron el código funcional de N2_cheap (7/7 → 6/19)

### T4: Problema MIXTO (modelo + tarea)
- **2 de 3 configs fallaron en E1** (Architect): step-3.5-flash consumió los 16K tokens en `<think>` sin generar output
- N2_cheap (mimo-v2 como E1) sí generó arquitectura, pero el código generado falló en mocks de `aiohttp.ClientSession.__aenter__`
- **Causa raíz doble:**
  1. **Think-tag blow-up**: Step 3.5 Flash gasta todo el budget pensando en T4 (tarea compleja con async + mocks)
  2. **Complejidad intrínseca**: T4 requiere mocks de `aiohttp`, `asyncio.gather`, context managers — los modelos OS no manejan bien este pattern

## Análisis de Estaciones (N3_coding T1 — mejor run)

| Estación | Modelo | Tokens | Latencia | Resultado |
|----------|--------|:---:|:---:|:---:|
| E1 Architect | step-3.5-flash | 6,644 | 45s | Plan correcto |
| E2 Implement | devstral-2512 | 1,174 | 4s | Código base |
| E2 Tests | devstral-2512 | 1,457 | 7s | 10 tests |
| E3 Tester | devstral-2512 | 1,646 | 10s | Diagnóstico |
| E4 Debug R1 | step-3.5-flash | 16,384 | 94s | Fix parcial |
| E4b Debug R2 | step-3.5-flash | 16,384 | 103s | Fix parcial |
| E4c Debug R3 | step-3.5-flash | 8,242 | 63s | **10/10** |

**Insight:** Devstral genera código limpio y rápido (~4-10s). Step 3.5 Flash es excelente como debugger (resuelve en 3 rounds). La combinación coding-specialist + reasoning-model es la ganadora.

## Problema Think-Tag en T4

| Config | E1 Model | E1 Tokens | E1 Content |
|--------|----------|:---:|:---:|
| N1_top | step-3.5-flash | 16,384 | **VACÍO** (todo en `<think>`) |
| N2_cheap | mimo-v2-flash | 3,834 | OK (no usa think tags) |
| N3_coding | step-3.5-flash | 16,384 | **VACÍO** (todo en `<think>`) |

MiMo V2 Flash no usa extended thinking → no sufre el blow-up. Pero su output de arquitectura no fue suficiente para resolver T4.

## Recomendaciones para el Motor Semántico

1. **Para E1 (Architect):** Usar mimo-v2-flash o devstral — modelos sin think-tags que generan output directo
2. **Para E4 (Debugger):** step-3.5-flash es el mejor — 3 rounds de debug resolvieron T1 completamente
3. **Regla E5/E6 skip confirmada:** Si tests pasan al 100% post-debug, NO pasar por Reviewer/Optimizer
4. **T4 requiere approach diferente:** Pipeline multi-estación con modelos OS no es suficiente para async Python con mocks complejos. Opciones:
   - Usar modelo propietario (Sonnet/Opus) solo para E1-Architect en T4
   - Simplificar la spec de T4 (sin mocks de aiohttp)
   - Añadir examples/few-shot al prompt de E1

## Costes Estimados

| Config | Tokens Totales | Coste Aprox |
|--------|:---:|:---:|
| N1_top T1 | 60K | ~$0.06 |
| N1_top T4 | 16K | ~$0.02 |
| N2_cheap T1 | 25K | ~$0.01 |
| N2_cheap T4 | 87K | ~$0.04 |
| N3_coding T1 | 73K | ~$0.03 |
| N3_coding T4 | 16K | ~$0.02 |
| **Total** | **277K** | **~$0.18** |

---
*Generado: 2026-03-11*
