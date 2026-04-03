# Data Audit — Gold Set V2
**Generado**: 2026-04-03 20:01  
**Textos**: 2990  
**Dims**: 51 (10 binarias h* + 41 continuas)  

## Resumen ejecutivo

| Metrica | Valor |
|---|---|
| Textos cargados | 2990 |
| Dims muertas | 26 |
| Dims binarias desbalanceadas | 2 |
| Pares redundantes (|r|>0.90) | 0 |
| Candidatos fusion (|r|>0.85) | 1 |
| Textos todo-cero | 0 |
| Textos pattern repetitivo | 0 |

## Estadisticas por dimension

| Dim | Tipo | Media | Median | Std | Var | Min | Max | pct_zero | pct_one | Estado |
|---|---|---|---|---|---|---|---|---|---|---|
| sust_densidad | continua | 0.1996 | 0.1800 | 0.1117 | 0.0125 | 0.0000 | 0.9800 | 0.30% | 0.00% | MUERTA |
| adj_densidad | continua | 0.0747 | 0.0800 | 0.0332 | 0.0011 | 0.0000 | 0.8800 | 0.80% | 0.00% | MUERTA |
| verb_densidad | continua | 0.1187 | 0.1200 | 0.0433 | 0.0019 | 0.0000 | 0.8500 | 0.74% | 0.00% | MUERTA |
| fv_indicativo | continua | 0.8239 | 0.8500 | 0.1899 | 0.0361 | 0.0000 | 1.0000 | 3.91% | 11.47% | MUERTA |
| fv_subjuntivo | continua | 0.1292 | 0.1500 | 0.1072 | 0.0115 | 0.0000 | 1.0000 | 19.83% | 0.30% | MUERTA |
| conj_pero | continua | 0.0060 | 0.0000 | 0.0082 | 0.0001 | 0.0000 | 0.0800 | 57.42% | 0.00% | MUERTA |
| conj_porque | continua | 0.0042 | 0.0000 | 0.0081 | 0.0001 | 0.0000 | 0.1200 | 70.27% | 0.00% | MUERTA |
| adv_modo | continua | 0.0177 | 0.0200 | 0.0123 | 0.0002 | 0.0000 | 0.1800 | 15.52% | 0.00% | MUERTA |
| disc_emocionalidad | continua | 0.0571 | 0.0300 | 0.0819 | 0.0067 | 0.0000 | 0.9400 | 23.44% | 0.00% | MUERTA |
| foco_voz_activa | continua | 0.7973 | 0.8300 | 0.2005 | 0.0402 | 0.0000 | 1.0000 | 4.05% | 9.83% | MUERTA |
| plano_auto | continua | 0.0906 | 0.0000 | 0.1947 | 0.0379 | 0.0000 | 0.8500 | 62.24% | 0.00% | MUERTA |
| plano_ref | continua | 0.8722 | 0.9500 | 0.2130 | 0.0454 | 0.0000 | 1.0000 | 1.27% | 20.47% | MUERTA |
| canal_visual | continua | 0.0459 | 0.0200 | 0.0694 | 0.0048 | 0.0000 | 0.8500 | 28.39% | 0.00% | MUERTA |
| canal_kinestesico | continua | 0.0288 | 0.0000 | 0.0633 | 0.0040 | 0.0000 | 0.7500 | 54.18% | 0.00% | MUERTA |
| tl_conductas | continua | 0.5979 | 0.7500 | 0.2853 | 0.0814 | 0.0000 | 1.0000 | 3.88% | 0.23% | OK |
| tl_interpretaciones | continua | 0.3441 | 0.2500 | 0.2632 | 0.0693 | 0.0000 | 1.0000 | 5.05% | 0.47% | OK |
| cre_sustantiva | continua | 0.2643 | 0.1000 | 0.3395 | 0.1153 | 0.0000 | 1.0000 | 48.13% | 0.13% | OK |
| cre_condicional | continua | 0.0620 | 0.0000 | 0.1165 | 0.0136 | 0.0000 | 1.0000 | 56.99% | 0.40% | MUERTA |
| lente_salud | continua | 0.2471 | 0.1000 | 0.3142 | 0.0987 | 0.0000 | 1.0000 | 36.12% | 0.13% | OK |
| lente_sentido | continua | 0.2245 | 0.1500 | 0.2502 | 0.0626 | 0.0000 | 0.9500 | 21.94% | 0.00% | OK |
| fal_sustantiva | continua | 0.1306 | 0.0800 | 0.1780 | 0.0317 | 0.0000 | 1.0000 | 47.06% | 0.03% | MUERTA |
| fal_verbal | continua | 0.0484 | 0.0000 | 0.0862 | 0.0074 | 0.0000 | 0.8500 | 62.54% | 0.00% | MUERTA |
| fal_complejidad | continua | 0.1827 | 0.3300 | 0.1925 | 0.0371 | 0.0000 | 1.0000 | 49.23% | 0.07% | MUERTA |
| inf_causal | continua | 0.1356 | 0.0500 | 0.1934 | 0.0374 | 0.0000 | 1.0000 | 41.97% | 0.57% | MUERTA |
| inf_validez | continua | 0.4439 | 0.6500 | 0.3612 | 0.1304 | 0.0000 | 1.0000 | 35.35% | 0.84% | OK |
| gob_declarada_vs_ejecutada | continua | 0.0932 | 0.0000 | 0.1719 | 0.0296 | 0.0000 | 0.9500 | 65.15% | 0.00% | MUERTA |
| acd_distancia_id_ir | continua | 0.1203 | 0.0000 | 0.1876 | 0.0352 | 0.0000 | 0.9200 | 57.59% | 0.00% | MUERTA |
| resp_sujeto_explicito | continua | 0.4955 | 0.6000 | 0.2942 | 0.0865 | 0.0000 | 1.0000 | 11.57% | 2.24% | OK |
| eval_brecha_como_problema | continua | 0.1524 | 0.0000 | 0.2512 | 0.0631 | 0.0000 | 1.0000 | 59.93% | 0.13% | OK |
| nodo_rigidez | continua | 0.5506 | 0.7000 | 0.3132 | 0.0981 | 0.0000 | 1.0000 | 6.12% | 2.74% | OK |
| int_01_logico_matematica | continua | 0.0975 | 0.0500 | 0.1612 | 0.0260 | 0.0000 | 1.0000 | 33.98% | 0.03% | MUERTA |
| int_08_social | continua | 0.2773 | 0.1500 | 0.2812 | 0.0791 | 0.0000 | 0.9500 | 27.66% | 0.00% | OK |
| int_12_narrativa | continua | 0.3115 | 0.2000 | 0.3147 | 0.0990 | 0.0000 | 0.9500 | 30.84% | 0.00% | OK |
| p_03_critico | continua | 0.1349 | 0.0000 | 0.2049 | 0.0420 | 0.0000 | 0.9000 | 50.67% | 0.00% | MUERTA |
| p_02_sistemico | continua | 0.1891 | 0.1200 | 0.2150 | 0.0462 | 0.0000 | 0.9500 | 33.78% | 0.00% | MUERTA |
| modo_proceso | continua | 0.2766 | 0.2000 | 0.2665 | 0.0710 | 0.0000 | 0.9500 | 23.21% | 0.00% | OK |
| modo_relacion | continua | 0.2592 | 0.2000 | 0.2509 | 0.0630 | 0.0000 | 0.9500 | 21.67% | 0.00% | OK |
| profundidad_estructura | continua | 0.4675 | 0.3500 | 0.2712 | 0.0736 | 0.0000 | 1.0000 | 0.84% | 0.47% | OK |
| h01_confirmacion | binaria | 0.1244 | 0.0000 | 0.3301 | 0.1090 | 0.0000 | 1.0000 | 87.56% | 12.44% | OK |
| h04_autoridad_implicita | binaria | 0.4492 | 0.0000 | 0.4975 | 0.2475 | 0.0000 | 1.0000 | 55.08% | 44.92% | OK |
| h12_granularidad_falsa | binaria | 0.1020 | 0.0000 | 0.3027 | 0.0916 | 0.0000 | 1.0000 | 89.80% | 10.20% | OK |
| h14_causalidad_narrativa | binaria | 0.3793 | 0.0000 | 0.4853 | 0.2355 | 0.0000 | 1.0000 | 62.07% | 37.93% | OK |
| h22_validacion_social | binaria | 0.1217 | 0.0000 | 0.3270 | 0.1070 | 0.0000 | 1.0000 | 87.83% | 12.17% | OK |
| h25_aversion_perdida | binaria | 0.1763 | 0.0000 | 0.3811 | 0.1452 | 0.0000 | 1.0000 | 82.37% | 17.63% | OK |
| h26_framing | binaria | 0.4518 | 0.0000 | 0.4978 | 0.2478 | 0.0000 | 1.0000 | 54.82% | 45.18% | OK |
| h55_atribucion_autoservicio | binaria | 0.0314 | 0.0000 | 0.1745 | 0.0305 | 0.0000 | 1.0000 | 96.86% | 3.14% | MUERTA, IMBALANCED |
| h62_difusion_resp_cognitiva | binaria | 0.0468 | 0.0000 | 0.2113 | 0.0446 | 0.0000 | 1.0000 | 95.32% | 4.68% | MUERTA, IMBALANCED |
| h77_reificacion_categorias | binaria | 0.3943 | 0.0000 | 0.4888 | 0.2389 | 0.0000 | 1.0000 | 60.57% | 39.43% | OK |
| posicion_observador | continua | nan | nan | nan | nan | nan | nan | nan% | nan% | OK |
| direccion_navegacion | continua | nan | nan | nan | nan | nan | nan | nan% | nan% | OK |
| marco_dominante | continua | nan | nan | nan | nan | nan | nan | nan% | nan% | OK |

## Class balance (dims binarias)

| Dim | % 1s | % 0s | Estado |
|---|---|---|---|
| h01_confirmacion | 12.44% | 87.56% | OK |
| h04_autoridad_implicita | 44.92% | 55.08% | OK |
| h12_granularidad_falsa | 10.20% | 89.80% | OK |
| h14_causalidad_narrativa | 37.93% | 62.07% | OK |
| h22_validacion_social | 12.17% | 87.83% | OK |
| h25_aversion_perdida | 17.63% | 82.37% | OK |
| h26_framing | 45.18% | 54.82% | OK |
| h55_atribucion_autoservicio | 3.14% | 96.86% | IMBALANCED (<5% de 1s) |
| h62_difusion_resp_cognitiva | 4.68% | 95.32% | IMBALANCED (<5% de 1s) |
| h77_reificacion_categorias | 39.43% | 60.57% | OK |

## Pares redundantes |r| > 0.90

_Ninguno._

## Candidatos a fusion |r| > 0.85

| Dim A | Dim B | r |
|---|---|---|
| gob_declarada_vs_ejecutada | acd_distancia_id_ir | 0.8810 |

## Textos sospechosos

**Todo-cero**: ninguno.  
**Pattern repetitivo**: ninguno.  

---
_Audit generado automaticamente por `data_audit.py` — 2026-04-03 20:01_
