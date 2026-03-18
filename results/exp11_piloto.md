# EXP-11 Piloto — Formato de Prompt

Fecha: 2026-03-18T15:22:03
Modelo: deepseek/deepseek-v3.2
Caso: Socio buyout (420K€, 40%, 8 años)

## Resumen

| Variante | Tokens In | Tokens Out | Cobertura | Adherencia | Completitud | Tiempo |
|----------|----------|-----------|-----------|------------|-------------|--------|
| A_natural | 492 | 2383 | 61% (14/23) | 100% (6/6) | 100% | 202.8s |
| B_json | 659 | 1448 | 74% (17/23) | 100% (6/6) | 100% | 38.5s |
| D_hibrido | 511 | 1556 | 87% (20/23) | 100% (6/6) | 100% | 38.5s |
| E_program | 1211 | 1071 | 57% (13/23) | 17% (1/6) | 67% | 36.5s |

## Análisis

**Mejor cobertura**: D_hibrido (87%)
**Más eficiente** (cobertura/token): D_hibrido
**Mejor adherencia al pipeline**: A_natural (100%)

## Detalle por variante

### A_natural

- Tokens: 492 in / 2383 out
- Prompt: 1560 chars
- Cobertura: 61% (14/23)
- Adherencia: 100% (6/6 pasos)
- Completitud output: 100% (hallazgos=✅ firma=✅ ciegos=✅)
- Tiempo: 202.8s

**Output (primeros 800 chars):**

```
---

## **PASO 1 — EXTRAER (formalizar)**

**Datos medibles/contables:**

1. **Tiempo de sociedad:** 8 años.
2. **Facturación anual:** \( 420\,000 \) €/año.
3. **Margen:** \( 22\% \) → Beneficio anual = \( 0.22 \times 420\,000 = 92\,400 \) €.
4. **Participación socio:** \( 40\% \) → Su parte del beneficio anual = \( 0.40 \times 92\,400 = 36\,960 \) €.
5. **Mis ahorros:** \( 60\,000 \) €.
6. **Financiación bancaria:** tasa \( 6.5\% \) anual.
7. **Plazo decisión:** 30 días.

**Relaciones numéricas posibles:**

- Valor de la parte del negocio (incógnita \( V \)): no se da, hay que estimar.
- Si compro, pago \( V \) (posiblemente con ahorros + préstamo).
- Beneficio anual extra que obtendría al tener el \( 100\% \) vs mi situación actual (no se da mi % actual; asumo que tengo el \( 60\% \) act
```

### B_json

- Tokens: 659 in / 1448 out
- Prompt: 2194 chars
- Cobertura: 74% (17/23)
- Adherencia: 100% (6/6 pasos)
- Completitud output: 100% (hallazgos=✅ firma=✅ ciegos=✅)
- Tiempo: 38.5s

**Output (primeros 800 chars):**

```
**Respuesta estructurada según el pipeline**

---

### **1. EXTRAER (formalizar)**

**¿Qué se puede contar? ¿Qué se puede medir?**
- Facturación anual: €420,000
- Margen de beneficio: 22%
- Beneficio anual: €420,000 × 0.22 = €92,400
- Participación del socio: 40%
- Beneficio atribuible al socio: €92,400 × 0.40 = €36,960
- Ahorros disponibles: €60,000
- Tasa de financiación bancaria: 6.5%
- Plazo para cerrar: 30 días

**¿Qué magnitudes aparecen con número explícito?**
Todos los anteriores.

**¿Qué relación tiene cada número con los demás?**
- Beneficio → depende de facturación y margen.
- Valor de la parte del socio → relacionado con el beneficio que genera.
- Capacidad de compra → depende de ahorros + financiación.
- Coste de financiación → afecta la rentabilidad neta de la compra.

**¿Qué
```

### D_hibrido

- Tokens: 511 in / 1556 out
- Prompt: 1512 chars
- Cobertura: 87% (20/23)
- Adherencia: 100% (6/6 pasos)
- Completitud output: 100% (hallazgos=✅ firma=✅ ciegos=✅)
- Tiempo: 38.5s

**Output (primeros 800 chars):**

```
---

## **EXTRAER**  
**¿Qué se puede contar?**  
- Años de sociedad: 8 años.  
- Facturación anual: €420 000.  
- Margen de beneficio: 22% → beneficio anual = 420 000 × 0,22 = €92 400.  
- Participación del socio: 40% → su parte del beneficio anual = 92 400 × 0,4 = €36 960.  
- Mis ahorros: €60 000.  
- Tasa de financiación bancaria: 6,5% anual.  
- Plazo para cerrar: 30 días.  

**¿Qué magnitudes con número explícito?**  
Todos los anteriores son números explícitos excepto el valor de la parte del socio (no dado directamente).  

**¿Qué relación entre números?**  
El beneficio generado por la parte del socio (€36 960/año) podría servir para estimar el valor de compra (por ejemplo, mediante múltiplos de rentabilidad).  

**¿Qué se da por hecho?**  
- La facturación y margen se mantienen c
```

### E_program

- Tokens: 1211 in / 1071 out
- Prompt: 4401 chars
- Cobertura: 57% (13/23)
- Adherencia: 17% (1/6 pasos)
- Completitud output: 67% (hallazgos=✅ firma=✅ ciegos=❌)
- Tiempo: 36.5s

**Output (primeros 800 chars):**

```
```json
{
  "hallazgos": [
    {
      "claim": "El sistema está formalmente determinado: 4 ecuaciones para 4 incógnitas clave (valor empresa, flujo socio, capacidad pago, viabilidad financiera).",
      "evidence": "Datos: facturación=420K, margen=22%, participación=40%, ahorros=60K, tasa=6.5%, plazo=30días. Incógnitas: valor empresa (V), flujo anual socio (F=420K*0.22*0.4=36.96K), capacidad pago máxima (C), viabilidad (V≤C). Relaciones: F=36.96K, C=60K+préstamo(V-60K), servicio deuda=0.065*(V-60K).",
      "lens": "algebra"
    },
    {
      "claim": "Existe contradicción entre premisas: 'socio quiere cerrar en 30 días' vs. 'no sé si puedo comprársela' implica que la decisión requiere tiempo que el plazo no concede.",
      "evidence": "Premisa A: plazo fijo de 30 días. Premisa B: incer
```

