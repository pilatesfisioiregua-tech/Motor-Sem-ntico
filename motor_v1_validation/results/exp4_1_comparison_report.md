# EXP 4.1 vs EXP 4 -- Especializado vs Generico

## 1. Delta por Modelo (R1): Generico vs Especializado

| Modelo | Media Gen | Media Esp | Delta Global | Delta Foco | Delta Fuera |
|--------|-----------|-----------|--------------|------------|-------------|
| opus | 1.50 | 1.82 | +0.314 | n/a | n/a |
| v3.2-reasoner | 1.42 | 1.71 | +0.286 | n/a | n/a |
| cogito-671b | 1.52 | 1.80 | +0.276 | +0.667 | -0.017 |
| gpt-oss-120b | 1.26 | 1.52 | +0.267 | +1.133 | -0.080 |
| v3.2-chat | 1.54 | 1.80 | +0.257 | n/a | n/a |
| deepseek-r1 | 1.57 | 1.72 | +0.152 | +0.371 | +0.043 |
| minimax-m2.5 | 1.60 | 1.75 | +0.152 | +0.367 | +0.067 |
| sonnet | 2.00 | 2.00 | +0.000 | n/a | n/a |
| deepseek-v3.1 | 1.66 | 1.63 | -0.029 | +0.467 | -0.227 |
| kimi-k2.5 | 2.06 | 1.99 | -0.067 | +0.467 | -0.156 |
| qwen3-235b | 2.54 | 2.43 | -0.114 | n/a | n/a |
| glm-4.7 | 1.81 | 1.54 | -0.267 | +0.371 | -0.586 |

**Resumen R1:** Delta medio = +0.102. Mejoran: 7. Empeoran: 4. Igual: 1.

## 2. Mapa Colectivo Comparado (Best of R1+R2)

| Metrica | Generico | Especializado | Delta |
|---------|----------|---------------|-------|
| Celdas nivel 3+ | 93 | 95 | +2.000 |
| Celdas totales | 105 | 105 | - |

Celdas que suben: **17**. Celdas que bajan: **12**. Igual: **76**.

### Cambios en mapa colectivo (max por celda)

| Output | Celda | Gen Max | Esp Max | Delta |
|--------|-------|---------|---------|-------|
| v31_best | Sentido×Adaptar | 3 | 4 | +1.000 |
| v31_best | Sentido×Replicar | 2 | 3 | +1.000 |
| 70b_worst | Salud×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Captar | 2 | 3 | +1.000 |
| 70b_worst | Sentido×Depurar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Distribuir | 2 | 3 | +1.000 |
| 70b_worst | Sentido×Frontera | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Captar | 2 | 3 | +1.000 |
| 70b_worst | Continuidad×Distribuir | 2 | 3 | +1.000 |
| 70b_worst | Continuidad×Frontera | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Adaptar | 3 | 4 | +1.000 |
| 70b_worst | Continuidad×Replicar | 3 | 4 | +1.000 |
| maverick_medium | Salud×Adaptar | 3 | 4 | +1.000 |
| maverick_medium | Sentido×Frontera | 3 | 4 | +1.000 |
| maverick_medium | Continuidad×Frontera | 3 | 4 | +1.000 |
| qwen3t_medium | Continuidad×Replicar | 3 | 4 | +1.000 |
| 70b_worst | Sentido×Conservar | 3 | 2 | -1.000 |
| maverick_medium | Sentido×Distribuir | 3 | 2 | -1.000 |
| maverick_medium | Continuidad×Adaptar | 4 | 3 | -1.000 |
| gptoss_depurar | Salud×Adaptar | 4 | 3 | -1.000 |
| gptoss_depurar | Salud×Replicar | 3 | 2 | -1.000 |
| gptoss_depurar | Sentido×Captar | 4 | 3 | -1.000 |
| gptoss_depurar | Sentido×Adaptar | 5 | 4 | -1.000 |
| gptoss_depurar | Sentido×Replicar | 4 | 3 | -1.000 |
| gptoss_depurar | Continuidad×Replicar | 5 | 4 | -1.000 |
| qwen3t_medium | Salud×Conservar | 4 | 3 | -1.000 |
| qwen3t_medium | Sentido×Captar | 4 | 3 | -1.000 |
| qwen3t_medium | Continuidad×Conservar | 4 | 3 | -1.000 |

## 3. Top Mejoras: Celdas que subieron 2+ niveles

No se encontraron celdas con mejora >= 2 niveles.

## 4. Comparacion R2 (Best of R1+R2) por Modelo

| Modelo | Gen Best | Esp Best | Delta |
|--------|----------|----------|-------|
| v3.2-reasoner | 1.42 | 1.91 | +0.495 |
| deepseek-r1 | 1.57 | 2.00 | +0.429 |
| minimax-m2.5 | 1.79 | 2.07 | +0.276 |
| deepseek-v3.1 | 2.80 | 2.99 | +0.190 |
| v3.2-chat | 2.86 | 3.02 | +0.162 |
| cogito-671b | 2.88 | 2.90 | +0.019 |
| sonnet | 2.00 | 2.00 | +0.000 |
| gpt-oss-120b | 2.74 | 2.71 | -0.038 |
| glm-4.7 | 2.42 | 2.15 | -0.267 |
| qwen3-235b | 3.19 | 2.88 | -0.314 |
| opus | 2.77 | 2.37 | -0.400 |
| kimi-k2.5 | 2.47 | 1.99 | -0.476 |

**Mapa enriquecido colectivo (R2):** Celdas 3+ gen=93, esp=95 (+2.000). Suben=17, bajan=12.

## 5. Fichas Actualizadas por Modelo

### opus

- Media generica: 2.771 / Media especializada: 2.371 / Delta: -0.400
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Continuidad×Frontera (delta medio +0.000)
- Top retroceso: Sentido×Depurar (delta medio -1.000)

### v3.2-reasoner

- Media generica: 1.419 / Media especializada: 1.914 / Delta: +0.495
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Sentido×Captar (delta medio +2.000)
- Top retroceso: Continuidad×Replicar (delta medio -0.600)

### cogito-671b

- Media generica: 2.876 / Media especializada: 2.895 / Delta: +0.019
- En foco: gen=3.022, esp=3.111, delta=+0.089
- Fuera foco: gen=2.767, esp=2.733, delta=-0.033
- Top mejora: Sentido×Frontera (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.400)

### gpt-oss-120b

- Media generica: 2.743 / Media especializada: 2.705 / Delta: -0.038
- En foco: gen=2.567, esp=2.567, delta=+0.000
- Fuera foco: gen=2.813, esp=2.760, delta=-0.053
- Top mejora: Sentido×Distribuir (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.600)

### v3.2-chat

- Media generica: 2.857 / Media especializada: 3.019 / Delta: +0.162
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Salud×Depurar (delta medio +0.400)
- Top retroceso: Salud×Frontera (delta medio -0.200)

### deepseek-r1

- Media generica: 1.571 / Media especializada: 2.000 / Delta: +0.429
- En foco: gen=1.771, esp=2.429, delta=+0.657
- Fuera foco: gen=1.471, esp=1.786, delta=+0.314
- Top mejora: Continuidad×Captar (delta medio +1.000)
- Top retroceso: Salud×Distribuir (delta medio +0.000)

### minimax-m2.5

- Media generica: 1.790 / Media especializada: 2.067 / Delta: +0.277
- En foco: gen=1.400, esp=2.067, delta=+0.667
- Fuera foco: gen=1.947, esp=2.067, delta=+0.120
- Top mejora: Sentido×Depurar (delta medio +1.000)
- Top retroceso: Sentido×Conservar (delta medio -0.400)

### sonnet

- Media generica: 2.000 / Media especializada: 2.000 / Delta: +0.000
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Salud×Conservar (delta medio +0.000)
- Top retroceso: Salud×Conservar (delta medio +0.000)

### deepseek-v3.1

- Media generica: 2.800 / Media especializada: 2.990 / Delta: +0.190
- En foco: gen=3.000, esp=3.167, delta=+0.167
- Fuera foco: gen=2.720, esp=2.920, delta=+0.200
- Top mejora: Salud×Depurar (delta medio +0.600)
- Top retroceso: Salud×Frontera (delta medio -0.200)

### kimi-k2.5

- Media generica: 2.467 / Media especializada: 1.990 / Delta: -0.477
- En foco: gen=2.667, esp=2.800, delta=+0.133
- Fuera foco: gen=2.433, esp=1.856, delta=-0.578
- Top mejora: Salud×Adaptar (delta medio +0.200)
- Top retroceso: Sentido×Depurar (delta medio -1.200)

### qwen3-235b

- Media generica: 3.190 / Media especializada: 2.876 / Delta: -0.314
- Sin foco especifico asignado (cross-celda o cobertura completa)
- Top mejora: Continuidad×Adaptar (delta medio +0.200)
- Top retroceso: Salud×Captar (delta medio -0.600)

### glm-4.7

- Media generica: 2.419 / Media especializada: 2.152 / Delta: -0.267
- En foco: gen=2.371, esp=2.257, delta=-0.114
- Fuera foco: gen=2.443, esp=2.100, delta=-0.343
- Top mejora: Sentido×Depurar (delta medio +0.200)
- Top retroceso: Salud×Frontera (delta medio -0.800)

## 6. Veredicto: Vale la especializacion?

**SI, la especializacion vale**

Delta medio positivo (+0.102) y 7/12 modelos mejoran. La especializacion produce evaluaciones mas profundas.

Datos clave:
- Delta medio R1: +0.102
- Modelos que mejoran (R1): 7/12
- Mapa colectivo 3+: gen=93, esp=95 (delta=+2.000)
- Delta medio en foco (modelos con foco): +0.549
- Delta medio fuera foco (modelos con foco): -0.137

## 7. Protocolo Recomendado

1. **Usar prompts especializados** para todos los modelos con foco definido
2. Para modelos sin foco (v3.2-chat, qwen3-235b, opus): mantener prompt generico o cross-celda
3. R2 de enriquecimiento sigue siendo necesaria para consolidar

## 8. Mesa Minima Actualizada (con datos especializados)

**2 modelos** capturan >= 90% del valor: v3.2-chat, deepseek-v3.1

Celdas 3+: 93/95 (97.9% del total con 2 modelos)

### Curva de cobertura

| N modelos | Modelos | Celdas 3+ | % del total |
|-----------|---------|-----------|-------------|
| 1 | v3.2-chat | 85 | 89.5% |
| 2 | v3.2-chat, deepseek-v3.1 | 93 | 97.9% |
| 3 | v3.2-chat, deepseek-v3.1, deepseek-r1 | 95 | 100.0% |
| 4 | v3.2-chat, deepseek-v3.1, deepseek-r1, cogito-671b | 95 | 100.0% |
| 5 | v3.2-chat, deepseek-v3.1, deepseek-r1, cogito-671b, glm-4.7 | 95 | 100.0% |

---
*Generado por exp4_1_analyze_comparison.py*