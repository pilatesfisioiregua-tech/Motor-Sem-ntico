# EXP 5 — CADENA DE MONTAJE (Analisis)

Fecha: 2026-03-10
Total runs: 40

## A) Tabla Principal: Config x Task

| Config | Nombre | T1 | T2 | T3 | T4 | T5 | **Media** | Coste | Tiempo |
|--------|--------|------|------|------|------|------|--------|-------|--------|
| A | Linea Industrial | 0/1 | **17/18** | **21/21** | 0/2 | 5/6 | **56%** | $0.327 | 2632s |
| B | Coder Puro | 0/1 | **14/15** | **10/11** | 0/2 | 0/0 | **37%** | $0.136 | 1771s |
| C | Maxima Diversidad | 25/30 | 0/0 | 0/0 | 0/2 | 0/2 | **17%** | $0.249 | 2468s |
| D | Ultra-Barato | 0/1 | 4/5 | **9/10** | 0/2 | 6/7 | **51%** | $0.047 | 944s |
| E | Premium | 0/1 | 3/4 | 0/2 | 0/2 | 0/2 | **15%** | $0.343 | 2732s |
| F | Cadena Minima | 0/1 | 0/1 | 8/9 | 0/2 | 0/2 | **18%** | $0.119 | 943s |
| G | Razonadores | 0/1 | 0/0 | **9/10** | 0/2 | 3/4 | **33%** | $0.191 | 2265s |
| 0 | Baseline | 0/1 | 0/1 | 5/6 | 0/2 | 3/4 | **32%** | $0.033 | 262s |

## B) Baseline vs Mejor Cadena

| Task | Baseline (0) | Mejor Cadena | Config | Delta |
|------|-------------|-------------|--------|-------|
| T1 | 0% | 83% | C | +83% |
| T2 | 0% | 94% | A | +94% |
| T3 | 83% | 100% | A | +17% |
| T4 | 0% | 0% | A | 0% |
| T5 | 75% | 86% | D | +11% |

**Baseline medio: 32% | Mejor cadena medio: 73% | Delta: +41%**

## C) Cuantas Estaciones Necesitas?

| Grupo | Pass Rate Medio | Coste Medio | Tiempo Medio |
|-------|----------------|-------------|--------------|
| 7 estaciones (A,C,E,G) | 30% | $0.0554 | 505s |
| 5 estaciones (B,D) | 44% | $0.0183 | 272s |
| 3 estaciones (F) | 18% | $0.0238 | 189s |
| 1 estacion (0) | 32% | $0.0066 | 52s |

## D) Impacto del Debugger (E4)

| Config | Task | Tests Pre-Debug | Tests Post-Debug R1 | Post-Debug R2 | Delta |
|--------|------|----------------|--------------------|--------------:|-------|
| A | T3 | 21/21 | — | — | +0% |
| A | T1 | 0/1 | 0/1 | 0/1 | +0% |
| A | T2 | 17/18 | 17/18 | 17/18 | -0% |
| A | T4 | 0/2 | 0/2 | 0/2 | +0% |
| A | T5 | 14/15 | 0/2 | 13/14 | -10% |
| B | T1 | 0/1 | 0/1 | — | +0% |
| B | T2 | 17/18 | 17/18 | — | -1% |
| B | T3 | 9/10 | 10/11 | — | +1% |
| B | T4 | 0/2 | — | — | +0% |
| C | T1 | 0/1 | 0/1 | 21/30 | +83% |
| C | T4 | 0/2 | 0/2 | 0/2 | +0% |
| C | T5 | 0/2 | 0/2 | 0/2 | +0% |
| D | T1 | 0/1 | 0/1 | — | +0% |
| D | T2 | 4/5 | 4/5 | — | +0% |
| D | T3 | 11/12 | 10/11 | — | -2% |
| D | T4 | 0/2 | 0/2 | — | +0% |
| D | T5 | 7/8 | 7/8 | — | -2% |
| E | T1 | 0/1 | 0/1 | 0/1 | +0% |
| E | T2 | 3/4 | 7/8 | 7/8 | +0% |
| E | T3 | 17/18 | 0/2 | 0/2 | -94% |
| E | T4 | 0/2 | 0/2 | 0/2 | +0% |
| E | T5 | 0/2 | 0/2 | 0/2 | +0% |
| F | T1 | 15/18 | 15/18 | — | -83% |
| F | T2 | 2/3 | 2/3 | — | -67% |
| F | T3 | 8/9 | 8/9 | — | +0% |
| F | T4 | 0/2 | 0/2 | — | +0% |
| F | T5 | 3/4 | 6/7 | — | -75% |
| G | T1 | 0/1 | 0/1 | 0/1 | +0% |
| G | T3 | 5/6 | 5/6 | 5/6 | +7% |
| G | T4 | 0/2 | 0/2 | 0/2 | +0% |
| G | T5 | 1/2 | 3/4 | 3/4 | +25% |

**Debugger mejoro en 5/35 casos. Media de mejora: +23%**

## E) Pareto Coste/Calidad

| Config | Nombre | Pass Rate | Coste Total | Coste/Task | Ratio Calidad/Coste |
|--------|--------|-----------|-------------|------------|---------------------|
| D | Ultra-Barato | 51% | $0.0470 | $0.0094 | 54 |
| 0 | Baseline | 32% | $0.0331 | $0.0066 | 48 |
| B | Coder Puro | 37% | $0.1364 | $0.0273 | 13 |
| G | Razonadores | 33% | $0.1908 | $0.0382 | 9 |
| A | Linea Industrial | 56% | $0.3267 | $0.0653 | 9 |
| F | Cadena Minima | 18% | $0.1192 | $0.0238 | 7 |
| C | Maxima Diversidad | 17% | $0.2488 | $0.0498 | 3 |
| E | Premium | 15% | $0.3425 | $0.0685 | 2 |

## F) Analisis de Fallos

### Fallos por Tarea

**T1** (Edge Function TS): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=0%)
  - Config B: implementation (pass_rate=0%)
  - Config C: implementation (pass_rate=83%)
  - Config D: implementation (pass_rate=0%)
  - Config E: reviewer (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: reviewer (pass_rate=0%)

**T2** (Migration SQL): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=94%)
  - Config B: implementation (pass_rate=93%)
  - Config C: architect (pass_rate=0%)
  - Config D: implementation (pass_rate=80%)
  - Config E: implementation (pass_rate=75%)
  - Config F: implementation (pass_rate=0%)
  - Config G: architect (pass_rate=0%)

**T3** (Analysis Script): 7/8 configs con fallos
  - Config 0: implementation (pass_rate=83%)
  - Config B: reviewer (pass_rate=91%)
  - Config C: tester (pass_rate=0%)
  - Config D: implementation (pass_rate=90%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=89%)
  - Config G: reviewer (pass_rate=90%)

**T4** (Orchestrator): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=0%)
  - Config A: implementation (pass_rate=0%)
  - Config B: debugger1 (pass_rate=0%)
  - Config C: implementation (pass_rate=0%)
  - Config D: implementation (pass_rate=0%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: reviewer (pass_rate=0%)

**T5** (Assembly Line): 8/8 configs con fallos
  - Config 0: implementation (pass_rate=75%)
  - Config A: optimizer (pass_rate=83%)
  - Config B: tester (pass_rate=0%)
  - Config C: implementation (pass_rate=0%)
  - Config D: implementation (pass_rate=86%)
  - Config E: implementation (pass_rate=0%)
  - Config F: implementation (pass_rate=0%)
  - Config G: implementation (pass_rate=75%)

### Dificultad Real por Tarea

| Task | Nombre | Configs con 100% | Configs con >0% | Configs con 0% |
|------|--------|-----------------|----------------|----------------|
| T1 | Edge Function TS | 0 | 1 | 7 |
| T2 | Migration SQL | 0 | 4 | 4 |
| T3 | Analysis Script | 1 | 5 | 2 |
| T4 | Orchestrator | 0 | 0 | 8 |
| T5 | Assembly Line | 0 | 4 | 4 |

## G) VEREDICTO: Puede Reemplazar a Code?

### Datos Clave

- **Mejor cadena**: Config A (Linea Industrial) con 56% pass rate medio
- **Baseline (modelo solo)**: 32% pass rate medio
- **Delta cadena vs baseline**: +24%
- **Config D (ultra-barato)**: 51% pass rate medio

### Criterios

| Criterio | Resultado | Cumple? |
|----------|-----------|---------|
| Mejor cadena > baseline | 56% vs 32% | SI |
| >=1 config con >=90% pass rate | 56% | NO |
| Config D >= 70% | 51% | NO |
| Debugger sube >=30% de fallos | 16% (7/45) | NO |
| Config F ~= Config B | F=18% vs B=37% | NO |

### Veredicto

**NO, la cadena no es suficiente hoy.** Mejor cadena: 56% pass rate.

La cadena de montaje **supera al modelo solo** en +24%.

---
*Generado por exp5_analyze.py*