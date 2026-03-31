# REGISTRO DE COSTES — ESTIMADO vs REAL

**Regla**: Cada operación con coste API se registra aquí. Sin excepciones.

---

## 31-Mar-2026

| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| Test consistencia 50 textos × 2 runs Opus API | ~$3-4 | ~$4 | ~0% | OK — estimación correcta |
| Benchmark 30 textos × 3 modelos × 2 runs | ~$5 | ~$5 | ~0% | OK |
| **Gold set batch 3000 textos Opus** | **$44** | **€75 (~$82)** | **+86%** | **System prompt con 51 dims = ~5500 tokens input, no 3300. Output ~800 tokens, no 500. NO se contaron tokens reales antes de lanzar.** |

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

### Coste acumulado proyecto (API/GPU)
| Concepto | Coste |
|---|---|
| GPUs Vast.ai (POC v1) | ~$30 |
| Gold set v1 (499 textos Opus) | ~$25 |
| Test consistencia + benchmark | ~$9 |
| Gold set v2 batch (1935 exitosos) | ~€75 |
| **TOTAL ACUMULADO** | **~€140** |

---

## Plantilla para futuras entradas

```
| Operación | Estimado | Real | Delta | Causa del error |
|---|---|---|---|---|
| [descripción] | $[X] | $[Y] | [+/-Z%] | [explicación si delta >10%] |
```
