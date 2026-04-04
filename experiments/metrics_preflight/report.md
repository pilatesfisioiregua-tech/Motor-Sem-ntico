# Métricas Pre-flight — Paso 2

**Fecha**: 2026-04-04
**Coste**: $0 (todo local)
**Rama**: feature/labeling-double-pass

---

## 1. Recalculo métricas poc_v1

- **n_samples eval**: 499
- **Dims analizadas**: 40
- **corr_global Pearson simple (original)**: `0.1192`
- **corr_global Pearson ponderado por varianza**: `0.208`
- **corr_global Spearman estimado (media)**: `0.2022`
  - _Nota: [SUPOSICION] Delta Pearson->Spearman estimado, no calculado con datos reales_

### Distribución de correlaciones

| Rango | N dims |
|---|---|
| Pearson > 0.3 (buenas) | 9 |
| Pearson 0.0–0.3 (débiles) | 18 |
| Pearson < 0.0 (negativas) | 13 |

### Top 10 dims (Pearson)

| Dim | Pearson | Spearman est. |
|---|---|---|
| int_12_narrativa | 0.5352 | 0.5652 |
| resp_sujeto_explicito | 0.5227 | 0.5227 |
| tl_conductas | 0.4827 | 0.5127 |
| fv_subjuntivo | 0.4806 | 0.6006 |
| tl_interpretaciones | 0.4311 | 0.4611 |
| verb_densidad | 0.4169 | 0.4869 |
| foco_voz_activa | 0.4137 | 0.5337 |
| disc_emocionalidad | 0.4129 | 0.5329 |
| int_08_social | 0.4059 | 0.4359 |
| sust_densidad | 0.2034 | 0.3234 |

### Bottom 10 dims (Pearson)

| Dim | Pearson |
|---|---|
| lente_sentido | -0.0254 |
| plano_auto | -0.0426 |
| modo_relacion | -0.0516 |
| acd_distancia_id_ir | -0.0708 |
| canal_visual | -0.0719 |
| cre_condicional | -0.0959 |
| fal_verbal | -0.1006 |
| adj_densidad | -0.1083 |
| nodo_rigidez | -0.1458 |
| fal_complejidad | -0.1598 |

### Análisis overfitting (train_corr vs val_corr)

- **Dims OVERFIT** (val_corr < train_corr - 0.2): 6
- **Dims UNDERFIT** (val_corr > train_corr + 0.2): 4
- **Dims OK**: 30

**Dims con OVERFIT (peores):**

| Dim | train_corr | val_corr | delta |
|---|---|---|---|
| fv_indicativo | 0.6767 | -0.0172 | -0.6939 |
| inf_validez | 0.4084 | 0.0626 | -0.3458 |
| foco_voz_activa | 0.722 | 0.4137 | -0.3083 |
| verb_densidad | 0.7021 | 0.4169 | -0.2852 |
| inf_causal | 0.2659 | 0.0515 | -0.2144 |
| tl_conductas | 0.6913 | 0.4827 | -0.2086 |

**Dims con UNDERFIT:**

| Dim | train_corr | val_corr | delta |
|---|---|---|---|
| lente_salud | -0.1859 | 0.0316 | 0.2175 |
| sust_densidad | -0.0919 | 0.2034 | 0.2953 |
| conj_porque | -0.2486 | 0.0474 | 0.296 |
| int_12_narrativa | 0.2031 | 0.5352 | 0.3321 |

> **NOTA IMPORTANTE**: Bootstrap CI requiere los vectores pred/label por muestra,
> que no están guardados en poc_v1. El poc_v1 solo guardó métricas agregadas.
> Para poc_v2 y posteriores: guardar `predictions.npz` con pred y label por muestra.

---

## 2. Calidad de labels gold_set_v2

- **Total registros**: 2990
- **Dims analizadas**: 48
- **Distribución normal**: 0 dims (0.0%)
- **Distribución sesgada**: 48 dims (100.0%)
- **Floor/ceiling effect** (>50% en extremo): 26 dims (54.2%)

### Implicación para métricas

> **CONCLUSION**: La mayoría de dims tienen distribución NO normal (skewed).
> **Spearman es la métrica correcta** para este dataset. Pearson puede subestimar
> correlaciones reales porque es sensible a outliers y asimetría.

### Dims con floor/ceiling effect (26 dims)

Estas dims tienen >50% de valores en un extremo (0 o 1). Serán difíciles de predecir.

- `conj_pero`: floor=99.90%, ceil=0.00%, mean=0.006
- `conj_porque`: floor=99.77%, ceil=0.00%, mean=0.0042
- `adv_modo`: floor=98.53%, ceil=0.00%, mean=0.0177
- `disc_emocionalidad`: floor=69.63%, ceil=0.00%, mean=0.0571
- `plano_auto`: floor=76.12%, ceil=0.00%, mean=0.0906
- `plano_ref`: floor=1.27%, ceil=72.27%, mean=0.8722
- `canal_visual`: floor=73.14%, ceil=0.00%, mean=0.0459
- `canal_kinestesico`: floor=85.02%, ceil=0.00%, mean=0.0288
- `cre_condicional`: floor=67.09%, ceil=0.40%, mean=0.062
- `fal_verbal`: floor=71.40%, ceil=0.00%, mean=0.0484
- `inf_causal`: floor=53.41%, ceil=0.60%, mean=0.1356
- `gob_declarada_vs_ejecutada`: floor=65.55%, ceil=0.07%, mean=0.0932
- `acd_distancia_id_ir`: floor=58.66%, ceil=0.00%, mean=0.1203
- `eval_brecha_como_problema`: floor=63.38%, ceil=0.17%, mean=0.1524
- `int_01_logico_matematica`: floor=68.53%, ceil=0.27%, mean=0.0975

### Top 10 dims más sesgadas

| Dim | Skewness | Floor rate | Tipo dist. |
|---|---|---|---|
| h55_atribucion_autoservicio | 5.370 | 96.86% | floor |
| adj_densidad | 4.853 | 24.21% | skewed |
| canal_visual | 4.491 | 73.14% | floor |
| canal_kinestesico | 4.411 | 85.02% | floor |
| h62_difusion_resp_cognitiva | 4.290 | 95.32% | floor |
| cre_condicional | 4.113 | 67.09% | floor |
| disc_emocionalidad | 4.088 | 69.63% | floor |
| sust_densidad | 3.828 | 0.74% | skewed |
| conj_porque | 3.447 | 99.77% | floor |
| fv_indicativo | -3.386 | 3.91% | skewed |

### Estadísticas detalladas por dim

| Dim | Mean | Std | Skewness | Normal? | Floor/Ceil |
|---|---|---|---|---|---|
| acd_distancia_id_ir | 0.1203 | 0.1875 | 1.8793 | False | SI |
| adj_densidad | 0.0747 | 0.0332 | 4.8533 | False | no |
| adv_modo | 0.0177 | 0.0123 | 2.0002 | False | SI |
| canal_kinestesico | 0.0288 | 0.0632 | 4.411 | False | SI |
| canal_visual | 0.0459 | 0.0693 | 4.4906 | False | SI |
| conj_pero | 0.006 | 0.0082 | 1.5818 | False | SI |
| conj_porque | 0.0042 | 0.0081 | 3.4466 | False | SI |
| cre_condicional | 0.062 | 0.1165 | 4.1127 | False | SI |
| cre_sustantiva | 0.2643 | 0.3394 | 0.8788 | False | no |
| disc_emocionalidad | 0.0571 | 0.0819 | 4.0877 | False | SI |
| eval_brecha_como_problema | 0.1524 | 0.2511 | 1.6524 | False | SI |
| fal_complejidad | 0.1827 | 0.1925 | 0.5163 | False | no |
| fal_sustantiva | 0.1306 | 0.1779 | 1.9195 | False | no |
| fal_verbal | 0.0484 | 0.0862 | 2.8859 | False | SI |
| foco_voz_activa | 0.7973 | 0.2005 | -2.7955 | False | no |
| fv_indicativo | 0.8239 | 0.1899 | -3.3864 | False | no |
| fv_subjuntivo | 0.1292 | 0.1072 | 3.1319 | False | no |
| gob_declarada_vs_ejecutada | 0.0932 | 0.1719 | 2.3414 | False | SI |
| h01_confirmacion | 0.1244 | 0.3301 | 2.2759 | False | SI |
| h04_autoridad_implicita | 0.4492 | 0.4974 | 0.2044 | False | SI |
| h12_granularidad_falsa | 0.102 | 0.3027 | 2.63 | False | SI |
| h14_causalidad_narrativa | 0.3793 | 0.4852 | 0.4977 | False | SI |
| h22_validacion_social | 0.1217 | 0.327 | 2.3136 | False | SI |
| h25_aversion_perdida | 0.1763 | 0.381 | 1.6993 | False | SI |
| h26_framing | 0.4518 | 0.4977 | 0.1935 | False | SI |
| h55_atribucion_autoservicio | 0.0314 | 0.1745 | 5.3704 | False | SI |
| h62_difusion_resp_cognitiva | 0.0468 | 0.2113 | 4.2903 | False | SI |
| h77_reificacion_categorias | 0.3943 | 0.4887 | 0.4325 | False | SI |
| inf_causal | 0.1356 | 0.1934 | 1.9988 | False | SI |
| inf_validez | 0.4439 | 0.3611 | -0.2097 | False | no |
| int_01_logico_matematica | 0.0975 | 0.1612 | 3.0687 | False | SI |
| int_08_social | 0.2773 | 0.2812 | 0.7552 | False | no |
| int_12_narrativa | 0.3115 | 0.3146 | 0.5863 | False | no |
| lente_salud | 0.2471 | 0.3141 | 1.0805 | False | no |
| lente_sentido | 0.2245 | 0.2502 | 1.3412 | False | no |
| modo_proceso | 0.2766 | 0.2664 | 0.8695 | False | no |
| modo_relacion | 0.2592 | 0.2509 | 0.9619 | False | no |
| nodo_rigidez | 0.5506 | 0.3131 | -0.3168 | False | no |
| p_02_sistemico | 0.1891 | 0.215 | 1.2497 | False | no |
| p_03_critico | 0.1349 | 0.2049 | 1.78 | False | SI |
| plano_auto | 0.0906 | 0.1946 | 2.6155 | False | SI |
| plano_ref | 0.8722 | 0.213 | -2.5643 | False | SI |
| profundidad_estructura | 0.4675 | 0.2712 | 0.2912 | False | no |
| resp_sujeto_explicito | 0.4955 | 0.2941 | -0.3561 | False | no |
| sust_densidad | 0.1996 | 0.1117 | 3.8278 | False | no |
| tl_conductas | 0.5979 | 0.2853 | -0.7767 | False | no |
| tl_interpretaciones | 0.3441 | 0.2632 | 0.8967 | False | no |
| verb_densidad | 0.1187 | 0.0433 | 1.2449 | False | no |

---

## 3. Split analysis train/val 80/20

- **Total**: 2990 registros
- **Train**: 2392 (80%)
- **Val**: 598 (20%)
- **Seed**: 42

### Equivalencia estadística (Mann-Whitney U)

- **Dims estadísticamente equivalentes** (p > 0.05): 42/48 (87.5%)
- **Dims NO equivalentes**: 6
- **VEREDICTO**: **SPLIT SESGADO — revisar**

### Dims donde train ≠ val (p < 0.05)

| Dim | p-value | Mean delta |
|---|---|---|
| canal_kinestesico | 0.0125 | 0.0022 |
| fal_verbal | 0.0153 | 0.009 |
| verb_densidad | 0.017 | 0.0048 |
| plano_ref | 0.0174 | 0.0157 |
| acd_distancia_id_ir | 0.0376 | 0.0138 |
| int_08_social | 0.0455 | 0.0258 |

> Estas dims pueden requerir **stratified sampling** para garantizar split representativo.

---

## 4. Baselines realistas

- **Baseline random (media Spearman)**: `0.0223`
- **Baseline random CI95**: `[-0.0829, 0.1652]`
- **Baseline señal con 5% ruido**: `0.8712`

### Interpretación

| Umbral | Significado |
|---|---|
| Spearman < 0.0223 ± 0.05 | Igual que random — el modelo no aprende nada |
| Spearman > 0.10 | Claramente mejor que random |
| Spearman > 0.30 | Correlación débil pero real |
| Spearman > 0.50 | Correlación moderada — útil |
| Spearman > 0.70 | Correlación fuerte — excelente |

### Gate de éxito recomendado para poc_v2

> **Spearman global ponderado > 0.30** (vs Pearson=0.119 de poc_v1)
> **≥ 30% de dims con Spearman > 0.50** (vs ~25% en poc_v1)

### Top 10 dims por señal (5% ruido)

| Dim | Signal Spearman | Baseline Random | Varianza |
|---|---|---|---|
| resp_sujeto_explicito | 0.9956 | 0.0997 | 0.082607 |
| profundidad_estructura | 0.9948 | -0.0006 | 0.077529 |
| lente_sentido | 0.993 | 0.1063 | 0.069393 |
| modo_proceso | 0.9917 | 0.133 | 0.061798 |
| nodo_rigidez | 0.9906 | -0.0561 | 0.09872 |
| modo_relacion | 0.9906 | -0.06 | 0.066734 |
| tl_interpretaciones | 0.9876 | -0.0018 | 0.064959 |
| int_08_social | 0.9876 | -0.1142 | 0.082438 |
| verb_densidad | 0.9864 | 0.0782 | 0.001928 |
| tl_conductas | 0.9864 | 0.0401 | 0.071869 |

---

## 5. Conclusiones y decisiones

### Para poc_v2 (próximo training)

| Decisión | Acción |
|---|---|
| Métrica principal | **Spearman** (no Pearson) — distribuciones skewed |
| corr_global | **Ponderado por varianza** — no media simple |
| Bootstrap CI | Guardar predicciones por muestra (`predictions.npz`) |
| Split | **Stratified** por las dims más sesgadas |
| Gate éxito | Spearman_weighted > 0.30 |
| Floor/ceiling dims | Usar **weighted loss** (upweight docs en el extremo poco frecuente) |

### Cambios al pipeline de evaluación

1. Reemplazar `pearson_r` por `spearman_r` en eval loop
2. Añadir `corr_global_weighted` como métrica de seguimiento
3. Guardar `predictions.npz` después de cada eval
4. Usar stratified split para las N dims con p < 0.05 en Mann-Whitney
5. Añadir Bootstrap CI (1000 resamples) en el eval final
