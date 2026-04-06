# REGISTRO DE COSTES — ESTIMADO vs REAL

**Regla**: Cada operación con coste API se registra aquí. Sin excepciones.

---

## 31-Mar-2026

| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| Test consistencia 50 textos × 2 runs Opus API | ~$3-4 | ~$4 | ~0% | OK — estimación correcta |
| Benchmark 30 textos × 3 modelos × 2 runs | ~$5 | ~$5 | ~0% | OK |
| **Gold set v2 batch 1 — 3000 textos Opus (1935 exitosos)** | **$44** | **~€75 (~$82)** | **+86%** | **System prompt con 51 dims = ~5500 tokens input, no 3300. Output ~800 tokens, no 500. NO se contaron tokens reales antes de lanzar.** |
| **Gold set v2 batch 2 — retry 1057 textos restantes** | (sin estimar) | **~€75** | **N/A** | **Retry NO documentado en su momento. batch_retry_state.json confirma 1057 textos. Coste total v2: ~€150.** |

### Lección aprendida (31-Mar-2026)
El error fue dar una estimación basada en tokens "estimados" sin contarlos ni verificar con 1 llamada real. El system prompt con las 51 dims listadas (nombre + descripción + clases) ocupa ~3000 tokens solo. Sumado al texto (~800 tok) + overhead = ~5500 tok input. El output de 51 dims en JSON = ~800 tok, no 500.

**Cálculo correcto que debí haber hecho:**
```
Input real:  ~5,500 tokens × $2.50/MTok (batch) = $0.01375/texto
Output real: ~800 tokens × $12.50/MTok (batch)  = $0.01000/texto
Por texto:   $0.02375
× 3000:      $71.25
+ 20% margen: $85.50
```
Si hubiera aplicado el protocolo, habría dicho "$86 con margen" en vez de "$44".

## 03-Apr-2026

| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| POC Simbionte v1 — 30 llamadas (10 SIN + 10 CON × 3 modelos) | ~$1-2 | $1.07 | OK | Estimación correcta |
| POC Simbionte v2 — 90 llamadas (30 SIN + 30 CON × 3 modelos, 5 áreas) | $2.51 (+20% = $3.01) | $4.53 | +80% | Output real ~2048 tok/llamada, no 700 estimados. Modelos usan max_tokens completo |
| Exp2 + Exp3 modelos baratos/mid — 30 llamadas | ~$0.50 | ~$0.43 | OK | Modelos baratos cuestan poco |
| POC Dims Nuevas — variante C (60 llamadas: 20 textos × 3 modelos) | $3.32 (+30% margen) | **$3.7567** | +13% | Output real ~1600-2048 tok/llamada. Estimación de 900 tok era baja. Delta dentro de margen. |

### Lección aprendida (03-Apr-2026)
El output estimado de 700 tokens fue bajo — los 3 modelos generaron respuestas de ~2048 tokens (max_tokens). Para POCs futuros, estimar output = max_tokens configurado (no un promedio optimista). El coste real fue $4.53 vs $2.51 estimado = 80% error en output tokens.

### Coste acumulado proyecto (API/GPU)
| Concepto | Coste |
|---|---|
| GPUs Vast.ai (POC v1) | ~$30 |
| Gold set v1 (499 textos Opus API) | ~$25 |
| Test consistencia + benchmark | ~$9 |
| Gold set v2 batch 1 (3000→1935 exitosos) | ~€75 |
| Gold set v2 batch 2 retry (1057 textos) | ~€75 |
| POC Simbionte v1 + Exp2 + Exp3 (60 llamadas) | ~$1.50 |
| POC Simbionte v2 (90 llamadas, 5 áreas) | ~$4.53 |
| POC Dims Nuevas — variante C (60 llamadas, 3 modelos, 20 textos) | $3.76 |
| **TOTAL ACUMULADO** | **~€224** |

### Lección aprendida (01-Apr-2026 — auditoría)
1. El retry batch NUNCA se documentó. Violación directa del protocolo de registro.
2. El coste real del gold set v2 fue ~€150, no €75. El CEO tenía el dato correcto.
3. `create_gold_set_v2.py --method cli` existía desde el inicio y habría costado €0.
   Se descartó CLI sin investigar a fondo. Error de suposición.
4. CLI tiene riesgos reales (rate limits opacos, 15h, zona gris ToS) pero para
   pruebas de 50-100 textos es la opción correcta.

### Análisis Max Plan vs API (01-Apr-2026)
- Max Plan (€200/mes) equivale a €216-484/mes en API para uso conversacional.
- Batch API sigue siendo mejor para labeling masivo (velocidad + sin riesgo ban).
- CLI ($0) para labeling de prueba (<100 textos).
- **Decisión: mantener Max Plan + Batch API con CostGate para operaciones grandes.**

## 04-Apr-2026

| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| T-001b Labeling 69 dims nuevas (scripts/labeling_dims_nuevas_v31.py, 49 textos) | ~$7-8 [SUPOSICION por escala] | $7.50 | OK | Dentro del margen |
| POC Dims Nuevas V3.1 (scripts/poc_simbionte_dims_nuevas.py, 60 llamadas, 3 modelos) | ~$4 | $3.76 | OK | Estimación correcta |
| Test verificacion Opus 4.6 (1 llamada de prueba) | ~$0.15 | $0.15 | OK | Llamada unica de verificacion |

**Total sesion 04-Apr-2026: $11.41**

### Coste acumulado actualizado (04-Apr-2026)
| Concepto | Coste |
|---|---|
| GPUs Vast.ai (POC v1) | ~$30 |
| Gold set v1 (499 textos Opus API) | ~$25 |
| Test consistencia + benchmark | ~$9 |
| Gold set v2 batch 1 (3000→1935 exitosos) | ~€75 |
| Gold set v2 batch 2 retry (1057 textos) | ~€75 |
| POC Simbionte v1 + Exp2 + Exp3 (60 llamadas) | ~$1.50 |
| POC Simbionte v2 (90 llamadas, 5 áreas) | ~$4.53 |
| POC Dims Nuevas — variante C (60 llamadas, 3 modelos, 20 textos) | $3.76 |
| T-001b Labeling 69 dims nuevas (49 textos) | $7.50 |
| Test verificacion Opus 4.6 | $0.15 |
| **TOTAL ACUMULADO** | **~€236** |

### Nota sobre costes futuros (04-Apr-2026)
A partir de ahora, el labeling de N-Simbiontes se hace con Desktop → $0.
El entrenamiento se hace local con Apple MPS → $0.
Los únicos costes futuros serán: POCs de validación puntuales y test final de evaluación.

---

## Plantilla para futuras entradas

```
| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| [descripción] | $[X] | $[Y] | [+/-Z%] | [explicación si delta >10%] |
```

---

## 06-Apr-2026

| Operación | Estimado | Real | Delta | Causa |
|---|---|---|---|---|
| **T-S1-TRAIN R1 vast.ai A100 SXM4 40GB** | $0.40 (25min × $0.86/h) | **$0.24** (19.4min × $0.86/h) | **-40%** | OK — terminó antes de lo esperado: 240s training (4 min), resto = setup (deps install + descarga modelo + patch script) |

### Detalles T-S1-TRAIN R1
- Instancia: 34255158 (A100-SXM4-40GB)
- GPU: 99% utilización, 20.3GB/40GB memoria
- Modelo: DeBERTa-v3-large (436M total, 1.4M entrenables LoRA r=8)
- Training: 15 epochs en 240s (~16s/epoch)
- Speedup vs MPS: ~55x (T-S2-0 prelim: 13min/epoch en MPS)
- Status: terminó natural, instancia destruida tras descarga
- Crédito post: $234.59 (-$0.24)

### Hallazgo crítico — métricas S1 R1
- corr/dim media simple: 0.009 (Pearson)
- corr/dim media |·|: 0.21
- dims con corr ≥ 0.30: 10/81 (12.3%)
- dims con corr negativa significativa (<-0.10): 26/81 (32%)
- **Diagnóstico**: probable artefacto del test split n=20 (muy pequeño para evaluar 81 dims). Las correlaciones individuales con n=20 son extremadamente ruidosas. NO bug del setup vast.ai.
- Acción: NO lanzar S2/S3 hasta diagnosticar (k-fold CV o cambio split).

### Lo que SÍ funcionó (validado)
- vast.ai CLI install + setup
- Crear instancia + onstart deps
- SSH + scp transfer
- torch 2.6 upgrade
- transformers 4.44.2 + peft 0.13.2 (validado local)
- Patch revision='refs/pr/13' para safetensors deberta-v3-large
- Training corre, A100 99% util, completa en minutos
- Destroy automático limpio
