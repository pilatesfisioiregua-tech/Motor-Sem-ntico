# ESTADO EXPERIMENTOS OMNI-MIND
**Última actualización:** 2026-03-31 11:28 UTC
**Total experimentos:** 3

---

## EN CURSO
- **gold_set_v1** | Status: `created` | Creado: 2026-03-29 21:40 UTC
  Hipótesis: 500 textos etiquetados por Opus, gold standard para evaluar todo el proyecto

## COMPLETADOS
- **poc_v1** | Resultado: POC completado. corr_global=0.119, 9/40 dims con corr>0.40. Binary F1=0.0 (threshold issue). Arquitectura DeBERTa validada para dims continuas. Hard dims necesitan más datos.
  Decisión: CONTINUAR: fix weighted BCE para binarias, más datos (3K), ajustar dims hard. Target v2: corr_global>0.35, f1_binary>0.50
  Métricas: corr_global=0.119, mae_global=0.126, f1_binary=0.0, corr_easy=0.217, corr_medium=0.114, corr_hard=0.025, corr_acd=0.122, best_dim_int12_narrativa=0.535, best_dim_resp_sujeto=0.523, best_dim_tl_conductas=0.483, best_dim_fv_subjuntivo=0.481, best_epoch=5.0, val_loss_best=0.0189, epochs_run=8.0, gold_set_n=499.0, inference_ms_per_sample=350.0

- **poc_v2** | Resultado: None
  Decisión: 51 dims: eliminar r_01/r_03/r_05/coherencia_span_dim, añadir posicion_observador(experimental)+direccion_navegacion+marco_dominante+profundidad_estructura. Spans via spaCy como features de entrada al CLS, no span head. Weighted BCE pos_weight por dim para binarias. posicion_observador: test consistencia 50 textos antes del gold set v2.

## PRÓXIMO PASO
Esperando resultado de: gold_set_v1
