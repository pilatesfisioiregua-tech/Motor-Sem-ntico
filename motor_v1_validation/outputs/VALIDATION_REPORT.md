# MOTOR v1 — VALIDACIÓN EXPANDIDA

**Fecha:** 2026-03-09 21:14
**Modelos:** 70B, Maverick
**Variantes:** A, B, C, D, E
**Evaluaciones válidas:** 89

**Variantes:**
- A: Solo preguntas (sin identidad de inteligencia)
- B: + firma + punto ciego
- C: B + instrucción analítica (extraer magnitudes, ecuaciones, restricciones)
- D: B + dependencias entre pasos
- E: Completa (B + C + D + instrucciones por lente)

---

## 1. MATRIZ GAP CLOSURE — Modelo × Variante

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| **70B** | 19% | 18% | 18% | 20% | 19% |
| **Maverick** | 21% | 27% | 28% | 23% | 24% |

**Mejor celda:** Maverick/C (28%)

---

## 2. SCORES POR DIMENSIÓN — Modelo × Variante

### Cobertura

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 2.4 | 2.3 | 2.3 | 2.2 | 2.2 |
| Maverick | 2.6 | 3.3 | 3.0 | 3.0 | 3.0 |

### Profundidad

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 2.2 | 2.2 | 2.0 | 2.2 | 2.4 |
| Maverick | 2.4 | 2.8 | 3.0 | 2.7 | 2.9 |

### Hallazgos excl.

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 2.1 | 1.7 | 2.1 | 2.0 | 1.6 |
| Maverick | 2.3 | 2.8 | 3.0 | 2.2 | 2.1 |

### Sin errores

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 7.1 | 7.0 | 7.0 | 6.7 | 6.7 |
| Maverick | 7.7 | 7.8 | 7.2 | 7.7 | 7.3 |

### Gap closure

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 1.9 | 1.8 | 1.8 | 2.0 | 1.9 |
| Maverick | 2.1 | 2.7 | 2.8 | 2.3 | 2.4 |

---

## 3. GAP CLOSURE POR INTELIGENCIA

### INT-01 (Lógico-Mat.)

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 13% | 13% | 13% | 17% | 13% |
| Maverick | 20% | 23% | 27% | 23% | 27% |

### INT-08 (Social)

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 27% | 27% | 20% | 23% | 20% |
| Maverick | 20% | 27% | 33% | 27% | 23% |

### INT-16 (Constructiva)

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 17% | 13% | 20% | 20% | 23% |
| Maverick | 23% | 30% | 20% | 20% | 23% |

---

## 4. GAP CLOSURE POR CASO

### Cambio Carrera

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 23% | 17% | 13% | 23% | 20% |
| Maverick | 30% | 30% | 35% | 23% | 27% |

### Clínica Dental

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 17% | 17% | 23% | 17% | 17% |
| Maverick | 17% | 30% | 30% | 27% | 27% |

### Startup SaaS

| Modelo | A | B | C | D | E |
|--------|------|------|------|------|------|
| 70B | 17% | 20% | 17% | 20% | 20% |
| Maverick | 17% | 20% | 20% | 20% | 20% |

---

## 5. CRITERIOS DE ÉXITO (mejor celda)

Evaluando la mejor combinación: **Maverick/C**

| Criterio | Resultado | Cumple |
|----------|-----------|--------|
| Gap closure >50% | 28% | NO |
| Todas INTs >20% | INT-01=27%, INT-08=33%, INT-16=20% | NO |
| Errores <10% | 28% | NO |

**Veredicto: NO APROBADO (0/3)**

---

## 6. DELTA Maverick vs 70B

| Variante | Cobertura | Profundidad | Hallazgos excl. | Sin errores | Gap closure |
|----------|------|------|------|------|------|
| A | +0.1 | +0.2 | +0.2 | +0.6 | +0.2 |
| B | +1.0 | +0.6 | +1.1 | +0.8 | +0.9 |
| C | +0.7 | +1.0 | +0.9 | +0.2 | +1.0 |
| D | +0.8 | +0.4 | +0.2 | +1.0 | +0.3 |
| E | +0.8 | +0.4 | +0.6 | +0.7 | +0.6 |

---

## 7. CONCLUSIÓN

Con 22% de gap closure global, la capacidad del modelo domina sobre la estructura del prompt.

Delta modelo (Maverick vs 70B): 25% vs 19% = +6pp

Mejor variante: C (22%), peor: A (20%)
Delta variante: +2pp

---
*Generado por motor_v1_validation*