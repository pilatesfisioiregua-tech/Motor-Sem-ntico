# T-VERIFY — Resumen de verificación automatica

Fecha: 2026-04-06 19:43

## Resumen por simbionte

| Simbionte | Textos | Dims | FIABLE | SOSPECHOSA | EXCLUIR | %EXCLUIR | Gate |
|---|---:|---:|---:|---:|---:|---:|:---:|
| **s1** | 200 | 81 | 81 | 0 | 0 | 0.0% | ✅ |
| **s2** | 191 | 114 | 114 | 0 | 0 | 0.0% | ✅ |
| **s3** | 191 | 126 | 126 | 0 | 0 | 0.0% | ✅ |

## Gates
- **<30% EXCLUIR**: ✅ FIABLE — proceder a T-*-TRAIN
- **30-50% EXCLUIR**: ⚠️ revisar dims excluidas, posible re-labeling
- **>50% EXCLUIR**: ❌ ALERTA CEO — algo grave en labeling

## Capas ejecutadas
- Capa 1: ground truth computable (regex/POS aprox)
- Capa 3: coherencia interna (correlaciones intra-simbionte)
- Capa 4: sondas sinteticas (10 textos extremos)
- Capa 5: distribucion estadistica (var, verbosity bias, none ratio)
- Capa 2 y 6 (LLM): DIFERIDAS — requieren re-labeling controlado

## Dims EXCLUIR por simbionte

### s1 (0 dims)
_(ninguna)_

### s2 (0 dims)
_(ninguna)_

### s3 (0 dims)
_(ninguna)_
