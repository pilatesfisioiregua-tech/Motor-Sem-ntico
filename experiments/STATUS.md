# ESTADO EXPERIMENTOS OMNI-MIND
**Última actualización:** 2026-04-05 (T-S2-1 COMPLETADO — 200 textos seleccionados, entropy 0.624, $0. Bug 20 PEFT corregido.)
**Total experimentos:** 11

---

## COMPLETADOS
- **T-CORPUS-AUDIT** | Clasificación 2990 textos gold_set_v2 por complejidad/diversidad/clustering.
  Resultado: Flesch medio 27.4 (muy_complejo), MTLD medio 76.9 (media-alta), 6 clusters temáticos (Literatura/Turismo/Política/Personal/Técnico/Empresa). Tipos: técnico 46% + informativo 35% + mixto 19%. Aviso: C2/C3/C5 con inglés mezclado. Silhouette k=6: 0.036.
  Artefactos: experiments/corpus_audit/corpus_features.jsonl + report.md + coverage_matrix.csv
  Desbloquea: T-S1-SEL + T-S3-1 con mapa de cobertura real.

- **T-AUDIT-0** | Resultado: 3000 textos auditados, 21 registros, 16 temas, 0 duplicados. Distribución: APTOS para S1/S2/S3. GAPs en S4 (ironía 0.3%, humor 1.5%) — no bloquean. Labels: reutilizar parcial (25 dims vivas de 51). Textos: RECICLAR.
  Decisión: T-S1-0 + T-S2-0 + T-S3-0 DESBLOQUEADOS. Informe: experiments/audit_gold_set_v2/report.md
  Métricas: textos_auditados=3000, registros=21, temas=16, duplicados=0, gap_s4_ironia=0.3, gap_s4_humor=1.5

- **T-S1-0** (BLOQUEADO tras ejecución) | Resultado: 0 dims A1 vivas en gold_set_v2 — ninguna de las 12 dims morfosintácticas del prelim tiene señal en el dataset de 51 dims. El modelo no puede arrancar con 0 targets.
  Decisión: BLOQUEADO. Requiere ampliar dims en gold_set_v2 para Head A1 ó re-etiquetar con dims S1. No continuar hasta resolver.
  Métricas: dims_a1_vivas=0, dims_total_gold_v2=51, overlap_s1_gold=0

- **double_pass_test** | Resultado: 0% cambio en 5 textos. Opus confirma labels al 100% cuando no hay contradicciones. Doble pasada no aporta en textos limpios.
  Decisión: Doble pasada SELECTIVA: solo en textos con contradicciones detectadas (>=1). Pasada simple para el resto. Ahorro ~60-70% vs doble pasada universal.
  Métricas: change_rate=0.0, texts_tested=5.0, contradictions_detected=0.0, tokens_input_total=10051.0, tokens_output_total=5713.0, cost_usd=0.12

- **gold_set_v1** | Resultado: 499/500 textos completados. Data Audit: 26/51 dims muertas (var<0.05), solo 25 con señal útil. Labels obsoletos para 443 dims target. Textos reutilizables, labels a re-hacer.
  Decisión: Re-etiquetar con prompt 443 dims. Empezar de cero en labels, reusar textos. POC micro 50 textos primero.

- **poc_micro_ablation** | Resultado: 3 variantes probadas. C mejor IAA(0.67) y varianza(0.057). A mejor score ponderado(0.75) por coste. Corr real A↔C=0.78 (solo 3 dims discrepan). B descartada (IAA=0.44). 23 dims varianza cero en corpus de 9 textos. Categoricas 97% acuerdo.
  Decisión: Usar variante A para POC completo 50 textos. Diferencia A vs C marginal, A cabe en presupuesto. B descartada.
  Métricas: iaa_A=0.6197, iaa_B=0.4411, iaa_C=0.6697, var_A=0.0458, var_B=0.0408, var_C=0.0574, corr_AB=0.4442, corr_AC_raw=0.4565, corr_AC_clean=0.78, cost_C_10texts=1.396, dims_stable=24.0, dims_discrepant=3.0, dims_zero_var=23.0, cat_agreement=0.97, texts_ok=9.0, texts_error=1.0

- **poc_v1** | Resultado: POC completado. corr_global=0.119, 9/40 dims con corr>0.40. Binary F1=0.0 (threshold issue). Arquitectura DeBERTa validada para dims continuas. Hard dims necesitan más datos.
  Decisión: CONTINUAR: fix weighted BCE para binarias, más datos (3K), ajustar dims hard. Target v2: corr_global>0.35, f1_binary>0.50
  Métricas: corr_global=0.119, mae_global=0.126, f1_binary=0.0, corr_easy=0.217, corr_medium=0.114, corr_hard=0.025, corr_acd=0.122, best_dim_int12_narrativa=0.535, best_dim_resp_sujeto=0.523, best_dim_tl_conductas=0.483, best_dim_fv_subjuntivo=0.481, best_epoch=5.0, val_loss_best=0.0189, epochs_run=8.0, gold_set_n=499.0, inference_ms_per_sample=350.0

- **poc_v2** | Resultado: None
  Decisión: 51 dims: eliminar r_01/r_03/r_05/coherencia_span_dim, añadir posicion_observador(experimental)+direccion_navegacion+marco_dominante+profundidad_estructura. Spans via spaCy como features de entrada al CLS, no span head. Weighted BCE pos_weight por dim para binarias. posicion_observador: test consistencia 50 textos antes del gold set v2.

- **simbionte_fase0_infra** | Resultado: PyTorch 2.8.0+MPS, Transformers 4.57.6, DeBERTa-v3-large tokenizer OK (128K vocab), W&B 0.25.1, datasets 4.5.0, ONNX 1.19.2, scikit-learn 1.6.1. Data Audit completado: 26/51 dims muertas en gold_set_v2.
  Decisión: Fase 0 COMPLETADA. Siguiente: POC micro 50 textos con prompt 443 dims ().

- **T-S2-0** | Simbionte S2 (Semántica local, Head A2, capas 7-12) — Training preliminar COMPLETADO.
  Resultado: corr_weighted=0.456. Gate 0.30 SUPERADO. Gate Fase 5 (0.40) SUPERADO.
  Dims destacadas: tl_interpretaciones=0.526, inf_validez=0.511, cre_sustantiva=0.401, nodo_rigidez=0.372, tl_conductas=0.235.
  Config: DeBERTa-v3-large, LoRA r=8, capas 6-11, Huber loss, mean pooling, 5 epochs.
  Tiempo: 69 min Apple MPS. Coste: $0.
  Modelo: experiments/s2_prelim/best_model.pt | Métricas: experiments/s2_prelim/final_metrics.json
  Decisión: CONTINUAR → T-S2-1 (Active Learning, seleccionar 200 textos max incertidumbre).

- **T-S3-0** | Simbionte S3 (Semántica global, Head A3, capas 13-18) — Training preliminar COMPLETADO.
  Resultado: corr_weighted=0.578. Gate 0.30 SUPERADO. Gate Fase 5 (0.40) SUPERADO.
  Dims destacadas: resp_sujeto_explicito=0.761, profundidad_estructura=0.670, inf_validez=0.545, eval_brecha_como_problema=0.441, nodo_rigidez=0.424.
  Todas 5/5 dims con corr > 0.40. Mejor resultado de todos los simbiontes preliminares.
  Config: DeBERTa-v3-large, LoRA r=12, TODAS las capas (workaround Bug 19 PEFT), Huber loss, mean pooling, 5 epochs.
  Tiempo: 102 min Apple MPS. Coste: $0.
  Modelo: experiments/s3_prelim/best_model.pt
  Decisión: CONTINUAR → T-S3-1 (Active Learning, seleccionar 200 textos max incertidumbre).

- **T-S2-1** | Active Learning S2 — MC Dropout n=5 sobre 2990 textos, 200 seleccionados por max predictive_entropy.
  Resultado: 200 textos seleccionados. Entropía media seleccionados=0.624 vs resto=0.538 (separación=0.086).
  Bug 20 PEFT corregido: script original ignoraba 100% weights (prefix mismatch). Fix: strip + LoRA merge + modules_to_save.
  Config: MPS, batch_size=16, 187 batches × 5 passes. Tiempo: 38.7 min. Coste: $0.
  Output: experiments/s2_prelim/al_selected_200.json (200 text_ids + entropía + varianza por texto)
  Decisión: CONTINUAR → T-S2-2 (Gold set mini 200 textos × 114 dims semántica, Desktop $0)

## EN CURSO
*(ninguno activo ahora)*

## PRÓXIMO PASO — RONDA 1 (Principio 6 + agentes + verificación automática)
Pipeline actualizado 05-Apr-2026. Agentes Opus etiquetan. CEO no etiqueta. Verificación 6 capas automática.

**FASE 0 — CORPUS AUDIT (nuevo, obligatorio antes de selección):**
  T-CORPUS-AUDIT: Clasificar 2990 textos por tipo/registro/complejidad — X-GENRE + textstat ($0, 30min)
  Desbloquea T-S1-SEL y T-S3-1 con mapa de cobertura real del corpus.

**SELECCIÓN (paralelo, automático, $0):**
  T-S1-SEL: Selección 200 textos S1 por diversidad morfosintáctica (spaCy, $0) — depende de T-CORPUS-AUDIT
  T-S3-1: Active Learning S3 — MC Dropout sobre 2990 textos ($0) — depende de T-CORPUS-AUDIT
  T-S2-1: ✅ Ya completado

**LABELING (AGENTES Opus background, $0 — CEO no interviene):**
  T-S1-LABEL: Agentes etiquetan 200 textos × 81 dims morfosintaxis (~2-4h automático)
  T-S2-LABEL: Agentes etiquetan 200 textos × 114 dims semántica (~3-5h automático)
  T-S3-LABEL: Agentes etiquetan 200 textos × 126 dims cognitiva (~4-6h automático)

**VERIFICACIÓN (automático, $0 — 6 capas sin humano):**
  T-VERIFY: ground truth computable + consenso multi-modelo + auto-consistencia + coherencia interna + sondas sintéticas + distribución estadística
  Output: dims clasificadas FIABLE/SOSPECHOSA/EXCLUIR. Bloquea training hasta completar.

**TRAINING (automático, $0 — solo dims verificadas pasan):**
  T-S1-TRAIN → T-S1-EVAL (gate: spearman > 0.30 — primer modelo S1)
  T-S2-TRAIN → T-S2-EVAL (gate: spearman > 0.40 — S2 ya tiene base)
  T-S3-TRAIN → T-S3-EVAL (gate: spearman > 0.40 — S3 mejor base)

**RONDA 2 (post-R1):** self-labeling + PPI/SiDyP + AL refinado.

**Ultima actualizacion:** 2026-04-04 (T-S3-0 COMPLETADO corr_weighted=0.578. T-S2-0 corr=0.456. Ambos gates superados. T-S1-0 bloqueado.)
