# EXP-11.1 — Ambigüedad Estructurada

Fecha: 2026-03-18T15:40:09
Modelo: deepseek/deepseek-v3.2
Pregunta: ¿Se puede generar ambigüedad productiva dentro de JSON/Python?

## Resumen

| Variante | Tok In | Tok Out | Cobertura | Adherencia | Depth | Completitud | Tiempo |
|----------|--------|---------|-----------|------------|-------|-------------|--------|
| D_hibrido | 517 | 1538 | 91% (21/23) | 100% | 21% (4/19) | 100% | 52.3s |
| F_tension | 995 | 1063 | 52% (12/23) | 0% | 32% (6/19) | 67% | 103.1s |
| G_metafora | 942 | 1639 | 70% (16/23) | 100% | 32% (6/19) | 100% | 45.7s |
| H_hints | 1620 | 959 | 65% (15/23) | 17% | 26% (5/19) | 100% | 71.1s |

## Análisis

**Mejor cobertura**: D_hibrido (91%)
**Mayor profundidad**: F_tension (32%)
**Mejor combinado** (cov×50% + depth×50%): D_hibrido

**🔑 Variantes JSON que superan a D en profundidad**: F_tension, G_metafora, H_hints
Esto indica que SÍ se puede generar ambigüedad productiva dentro de JSON.

## Detalle por variante

### D_hibrido

- Tokens: 517 in / 1538 out
- Prompt: 1512 chars
- Cobertura: 91% (21/23)
- Adherencia: 100% (6/6 pasos)
- Profundidad: 21% (4/19)
- Completitud: 100%
- Tiempo: 52.3s

**Output (primeros 1000 chars):**

```
Voy a ejecutar el pipeline paso a paso sobre el caso planteado.

---

## **EXTRAER** (datos_formalizados)

**¿Qué se puede contar?**
- Tiempo de sociedad: 8 años
- Facturación anual: €420,000
- Margen: 22% → Beneficio anual = 420,000 × 0.22 = €92,400
- Porcentaje socio: 40% → Beneficio atribuible al socio = 92,400 × 0.4 = €36,960/año
- Ahorros propios: €60,000
- Tasa financiación bancaria: 6.5% anual
- Plazo decisión: 30 días

**¿Qué magnitudes con número explícito?**
Todos los anteriores.

**¿Qué relación entre números?**
- Beneficio total → función lineal de facturación y margen
- Beneficio del socio → proporción fija (40%)
- Financiación implica costo de capital (6.5%)

**¿Qué se da por hecho?**
- Margen se mantiene estable
- Facturación futura similar a la actual
- Socio vende solo su parte, no el negocio completo
- Valor de la parte = función del beneficio que genera
- Banco financia la operación si hay garantías

---

## **CRUZAR** (estructura_problema)

**¿Cuántas relaciones son
```

### F_tension

- Tokens: 995 in / 1063 out
- Prompt: 3392 chars
- Cobertura: 52% (12/23)
- Adherencia: 0% (0/6 pasos)
- Profundidad: 32% (6/19)
- Completitud: 67%
- Tiempo: 103.1s

**Output (primeros 1000 chars):**

```
```
{
  "hallazgos": [
    {
      "id": "H1",
      "desc": "El valor de la parte del socio no está definido, pero se puede acotar con dos ecuaciones incompatibles.",
      "evidencia": [
        "Datos explícitos: facturación €420K/año, margen 22% → beneficio anual = €92.4K.",
        "Socio tiene 40% → su parte del beneficio anual = €36.96K.",
        "Mi capacidad de compra: €60K ahorros + financiación bancaria a 6.5%.",
        "Ecuación 1 (valor por múltiplo de beneficio): Valor = €36.96K × n (donde n es múltiplo, típico 2-5 en PYMES).",
        "Ecuación 2 (capacidad de pago): Valor ≤ €60K + préstamo máximo (determinado por capacidad de pago del préstamo).",
        "Contradicción: Para n ≥ 2, Valor ≥ €73.92K, que supera mis ahorros y exigiría financiación. El préstamo aumentaría mis gastos fijos, reduciendo mi beneficio neto y mi capacidad de pago real."
      ]
    },
    {
      "id": "H2",
      "desc": "Existe un punto de equilibrio donde el préstamo devora el beneficio adi
```

### G_metafora

- Tokens: 942 in / 1639 out
- Prompt: 3093 chars
- Cobertura: 70% (16/23)
- Adherencia: 100% (6/6 pasos)
- Profundidad: 32% (6/19)
- Completitud: 100%
- Tiempo: 45.7s

**Output (primeros 1000 chars):**

```
{
  "hallazgos": [
    {
      "op": "EXTRAER",
      "hallazgo": "Datos cuantificables: Facturación anual: €420,000. Margen de beneficio: 22% → Beneficio anual = €92,400. Participación socio: 40% → Su parte del beneficio = €36,960/año. Mis ahorros: €60,000. Coste financiación: 6.5% anual. Plazo decisión: 30 días. Datos faltantes críticos: 1) Precio de venta de su parte (valoración del negocio). 2) Proyección de flujos futuros (¿crece, se estanca, declina?). 3) Razón de la venta del socio (¿conoce algo negativo?). 4) Mi capacidad de gestión en solitario."
    },
    {
      "op": "CRUZAR",
      "hallazgo": "Estructura de trade-offs: En un plato de la balanza: Coste de compra (desembolso inicial + intereses) + Riesgo operativo en solitario + Posible sobreendeudamiento. En el otro plato: Flujo de caja incremental (el 100% del beneficio, €92,400) + Control total + Potencial de crecimiento. Punto de equilibrio financiero: El precio máximo que puedo pagar sin perder dinero depende de cuánt
```

### H_hints

- Tokens: 1620 in / 959 out
- Prompt: 5713 chars
- Cobertura: 65% (15/23)
- Adherencia: 17% (1/6 pasos)
- Profundidad: 26% (5/19)
- Completitud: 100%
- Tiempo: 71.1s

**Output (primeros 1000 chars):**

```
```json
{
  "hallazgos": [
    {
      "claim": "El valor de mercado del 40% del socio es aproximadamente €369,600, muy superior a los €60K de ahorros disponibles.",
      "evidence": "Valoración por múltiplo de beneficios: Beneficio anual = €420K × 22% = €92.4K. Parte del socio (40%) = €36.96K/año. Con múltiplo conservador (10x) = €369.6K. Álgebra muestra gran brecha entre capacidad de pago y valoración implícita.",
      "lens": "algebra"
    },
    {
      "claim": "La viabilidad financiera depende críticamente del plazo del préstamo y de la estabilidad del margen.",
      "evidence": "Análisis de sensibilidad: Para pagar un préstamo de ~€310K (diferencia tras ahorros) al 6.5%, la cuota anual a 10 años es ~€43K. El flujo del 40% (€36.96K) no la cubre. Solo sería viable con plazo muy largo (>15 años) o si el margen crece sustancialmente.",
      "lens": "analisis"
    },
    {
      "claim": "La pregunta '¿puedo?' tiene respuesta matemática negativa bajo premisas estándar; la duda re
```

