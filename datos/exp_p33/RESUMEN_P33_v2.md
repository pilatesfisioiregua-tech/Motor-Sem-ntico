# RESUMEN P33 v2 — Evaluación con 4 variantes de prompt

**Fecha:** 2026-03-16T10:28:24.802960+00:00
**Modelo evaluador:** xiaomi/mimo-v2-flash
**Coste total:** $0.0000
**Hallazgos evaluados:** 149

---

## Tabla comparativa

| Categoría | v1 (keywords) | v2 (directo) | v3a (imperativo) | v3b (preguntas) | v3c (mixto) |
|-----------|--------------|--------------|-------------------|-----------------|-------------|
| CONOCIDO | 49 | 9 | 9 | 22 | 1 | 
| REFORMULADO | 41 | 26 | 124 | 49 | 126 | 
| NUEVO | 59* | 93 | 2 | 43 | 0 | 
| RUIDO | 0 | 21 | 14 | 35 | 22 | 

*v1 no tenía RUIDO — todo lo no matcheado caía en CANDIDATO_NUEVO*

## Hallazgos NUEVO por consenso (≥3 de 4 variantes)

**Total: 2**

- *Hallazgo:* No, la situación es insostenible: el sistema opera en un *limbo* ("predecible y caótico") donde la propiocepción y el monitoreo se contradicen. Sin la persona clave, la
- *Hallazgo:* Solo escalable con un *costo de caos controlado*: replicar requeriría normalizar las contradicciones (e.g., aceptar "?" como estado válido) y externalizar la supervisió

## Hallazgos NUEVO unánimes (4 de 4)

**Total: 0**


## ¿Qué prompt funciona mejor?

| Métrica | v2 | v3a | v3b | v3c |
|---------|----|----|-----|-----|
| RUIDO filtrado | 21 | 14 | 35 | 22 | 
| NUEVO detectados | 93 | 2 | 43 | 0 | 
| REFORMULADO | 26 | 124 | 49 | 126 | 
| CONOCIDO | 9 | 9 | 22 | 1 | 
| Solo este prompt dice NUEVO | 56 | 0 | 6 | 0 |

## Comparativa clave: v3c vs v3a+v3b

| Pregunta | Resultado |
|----------|-----------|
| v3c detecta NUEVO que v3a no | 0 hallazgos |
| v3a detecta NUEVO que v3c no | 2 hallazgos |
| v3c detecta NUEVO que v3b no | 0 hallazgos |
| v3b detecta NUEVO que v3c no | 43 hallazgos |
| Solo v3c encuentra (no v3a ni v3b) | 0 hallazgos |
| v3c es superset de v3a∪v3b | False |

## Dato empírico sobre estructura de prompts

→ **v3c (0) < max(v3a=2, v3b=43): el prompt mixto introduce ruido al ser más largo.**

## Veredicto P33

**PARCIAL** — 2 NUEVO por consenso + media de reformulados ≥5

---

*Generado por exp_p33_evaluador_multi.py — 2026-03-16T10:28:24.802960+00:00*