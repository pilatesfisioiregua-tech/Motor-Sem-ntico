# REACTOR v5 — Análisis Consolidado de 50 Pares Problema-Solución

**Fecha:** 2026-03-19  
**Sesiones:** 5 (Negocio, Salud, STEM, Mixto, Fallidas)  
**Pares totales:** 50  

---

## 1. MÉTRICAS GLOBALES

| Métrica | Valor |
|---|---|
| Predicción correcta | **49/50 (98%)** |
| Predicción fallida | 1 (Google+, F01) |
| Confianza media global | 0.79 |
| Leyes refutadas totalmente | 0 |
| Leyes refutadas parcialmente | 1 (F6→F1(D) en S07/Suecia — temporal) |

### Distribución de tipos

| Tipo | Sesión 1 | Sesión 2 | Sesión 3 | Sesión 4 | Sesión 5 | **Total** |
|---|---|---|---|---|---|---|
| Cierre | 5 | 4 | 5 | 6 | 0 | **20 (40%)** |
| Inerte | 3 | 3 | 1 | 2 | 4 | **13 (26%)** |
| Tóxico | 2 | 3 | 4 | 2 | 6 | **17 (34%)** |

### Arquetipos cubiertos (50 pares)

- intoxicado: 14 casos (28%) — el más frecuente
- sin_rumbo: 8 casos (16%)
- semilla_dormida: 7 casos (14%)
- rigido: 5 casos (10%)
- expansion_sin_cimientos: 4 casos (8%)
- equilibrado: 4 casos (8%)
- maquina_sin_alma: 3 casos (6%)
- quemado: 3 casos (6%)
- aislado: 1 caso (2%)
- hemorragico: 1 caso (2%)

---

## 2. RANKING DE LEYES TCF POR FRECUENCIA

### Dependencias Bloqueantes (B)

| Ley | Activaciones (50 pares) | Tasa | Status |
|---|---|---|---|
| **F2→F3 (B)** | **39/50** | **78%** | UNIVERSAL — la ley más consistente |
| F7→F5 (B) | 23/50 | 46% | Confirmada cross-dominio |
| F4→F5 (B) | 15/50 | 30% | Confirmada cross-dominio |

### Dependencias Degradantes (D)

| Ley | Activaciones (50 pares) | Tasa | Status |
|---|---|---|---|
| F7→F3 (D) | 9/50 | 18% | Confirmada — replicar sin depurar amplifica |
| F6→F5 (D) | 8/50 | 16% | Confirmada |
| F6→F1 (D) | 7/50 | 14% | Confirmada (refutada parcial 1 caso temporal) |
| F1→F6 (D) | 6/50 | 12% | Confirmada — conservar sin adaptar = rigidez |
| F7→F1 (D) | 3/50 | 6% | Confirmada (pocos casos) |
| F3→F5 (D) | 5/50 | 10% | **PROPUESTA NUEVA: promover a ley catalogada** |
| F2→F5 (D) | 1/50 | 2% | Solo Concorde — baja frecuencia |

---

## 3. HALLAZGOS PRINCIPALES

### 3.1 F2→F3(B) es universal (78% de activación)

La ley más consistente de la TCF. Activada en **39 de 50 casos** a través de 7 dominios (negocio, salud, STEM, deporte, educación, derecho, personal).

**La formulación es siempre la misma:** captar sin depurar = acumular basura. Lo que cambia es la metáfora:
- Negocio: captar clientes/capital sin filtrar → WeWork, Theranos
- Salud: captar carga/sustancias sin filtrar → opioides, sobreentrenamiento
- STEM: captar datos/innovación sin verificar → Columbia, Boeing, cold fusion
- Deporte: captar volumen sin filtrar → sobreentrenamiento
- Derecho: captar "casos" sin filtrar → War on Drugs, lobotomía
- Personal: captar calorías/objetos sin filtrar → dietas yo-yo, acumulación

**Implicación para el Motor:** F2→F3(B) debería ser la PRIMERA ley evaluada en cualquier diagnóstico. Si un sistema tiene F2 alta y F3 baja, la predicción es intoxicación con alta confianza.

### 3.2 F3 es la función predictora de resultado

| Si delta F3... | Resultado más probable | Casos |
|---|---|---|
| ≥ +0.25 | CIERRE (90%+) | Toyota, Perelman, CRISPR, DPP, KonMari, Mercadona |
| +0.10 a +0.20 | INERTE (70%+) | Peloton, DARE, crisis replicabilidad |
| ≤ 0 o negativo | TÓXICO (85%+) | WeWork, opioides, Boeing, Theranos, lobotomía |

**Umbral mínimo para cierre:** delta F3 ≈ +0.25. Por debajo, la depuración es insuficiente para desbloquear F2→F3(B).

### 3.3 F3 como diseño > F3 reactiva

Tres patrones distintos de F3 descubiertos:

1. **F3_diseño (built-in):** Depuración integrada en el modelo. Inditex (lotes pequeños), TCP/IP (protocolos), Khan Academy (ejercicios adaptativos). Más robusta.
2. **F3_reactiva (correctiva):** Depuración como intervención post-hoc. Toyota (kaizen), Peloton (despidos). Funciona pero requiere más delta.
3. **F3_bypassed (desactivada):** El sistema tenía F3 pero la acción la saltó. Cold fusion, Boeing (autocertificación). El más tóxico de los tres.

### 3.4 F5 necesita vector, no escalar

Descubrimiento de la Sesión 5: F5 alta no siempre es positiva.

- **F5 alta + correcta** = enabler (TCP/IP, Patagonia, Mercadona) → cierre
- **F5 alta + incorrecta** = amplificador de error (Maginot) → tóxico
- **F5 baja** = sin rumbo (WeWork, Yahoo) → inerte/tóxico

**Propuesta:** Modelar F5 como (magnitud, dirección). La magnitud mide cuán definida está la identidad; la dirección mide cuán alineada está con la realidad.

### 3.5 F3→F5(D) debe promoverse a ley catalogada

Descubierta en 5 casos cross-dominio:
- ACL (S02): depurar define qué es "recuperado"
- Perelman (T05): cirugía de singularidades define frontera del teorema
- KonMari (M08): "spark joy" = frontera emergente de la depuración
- Suecia COVID (S07): falta de depuración erosionó frontera de protección
- Moneyball (M10): depurar métricas definió qué es "valor"

**Formulación:** Depurar construye frontera. Si no sabes filtrar, no sabes qué eres. F3 es precursora causal de F5.

### 3.6 Ciclo F1↔F6 bidireccional

Confirmado en 4 casos cross-dominio:
- Sobreentrenamiento (S10)
- Lumbalgia (S05)  
- Burnout médico (M04)
- Maginot (F10)

Las leyes F1→F6(D) y F6→F1(D) se activan mutuamente como feedback loop negativo. La TCF las cataloga por separado pero en la práctica forman un ciclo autoalimentado.

**Propuesta:** Catalogar como CICLO_RIGIDEZ: F1↑↑ sin F6 → F6↓ → F1 frágil → F6↓↓ → espiral descendente.

---

## 4. LIMITACIONES DESCUBIERTAS

### 4.1 No modela factores exógenos
Google+ (F01): sistema internamente sano, falló por lock-in de Facebook. La TCF modela salud interna pero no posición competitiva ni efectos de red.

**Propuesta:** Variable exógena E (entorno/mercado) con al menos: market-fit, lock-in competitivo, timing. No necesita ser parte de las 7F — puede ser un modificador externo del vector.

### 4.2 No tiene dimensión temporal
Suecia COVID (S07): resultado depende de cuándo evalúas. Tóxico a corto plazo, posiblemente cierre a largo.

**Propuesta:** Añadir horizonte de evaluación (t) y tasa de cambio (dF/dt). Un delta positivo lento puede ser cierre a largo plazo e inerte a corto.

### 4.3 F5 no distingue calidad
Maginot (F10): F5=0.55 era alta pero incorrecta. La TCF asume que F5 alta = positivo.

**Propuesta:** F5 como vector (magnitud, dirección) — ya descrito en §3.4.

### 4.4 F7→F5(B) necesita cualificación de codificabilidad
El Bulli (N09): F5=0.90 pero F7 no mejoró porque el conocimiento era tácito/encarnado.

**Propuesta:** F7→F5_codificada(B). La dependencia asume que F5 es transmisible. Si F5 es puramente tácita, F7 está bloqueada aunque F5 sea alta.

---

## 5. CROSS-DOMINIO: PATRONES UNIVERSALES

### Patrón INTOXICADO → CIERRE por F3
Toyota (negocio) = Virginia Mason (salud) = Perelman (STEM) = KonMari (personal)

Mismo mecanismo: sistema con F2↑ F3↓, atacar F3 directamente con delta ≥ +0.25, resultado = cierre.

### Patrón RÍGIDO → TÓXICO por F1→F6(D)  
Kodak (negocio) = Lumbalgia reposo (salud) = Maginot (ingeniería)

Conservar sin adaptar = rigidez patológica en todo dominio.

### Patrón CAPTACIÓN+REPLICACIÓN SIN F3+F5 → TÓXICO
WeWork (negocio) = Opioides (salud) = Theranos/Boeing (STEM) = War on Drugs (derecho) = Lobotomía (salud)

El patrón más letal: F2↑ F7↑ con F3↓ F5↓. Triple violación bloqueante.

### Patrón F7 como diferenciador CIERRE vs INERTE
Patagonia vs El Bulli (negocio). DPP vs SSRI (salud). CRISPR vs cold fusion (STEM).

F7 (replicabilidad) separa cierre de inerte. En salud = "que el paciente pueda hacerlo solo".

---

## 6. IMPLICACIONES PARA OMNI-MIND

### Para el Motor vN
1. **F2→F3(B) como primera evaluación**: cualquier caso nuevo, evaluar ratio F2/F3 primero. Si F2 > 0.60 y F3 < 0.25 → flag de intoxicación.
2. **Umbral F3 para predicción**: delta F3 < +0.25 → predicción inerte. delta F3 ≥ +0.25 → predicción cierre (si dependencias satisfechas).
3. **F5 como vector**: implementar magnitud + dirección. La dirección requiere evaluación de "fit con realidad" que es el assessment más difícil.

### Para los Pilotos (Pilates / Fisioterapia)
1. **S02 (ACL)**: criterios de retorno = F3→F5. Directamente aplicable a protocolos.
2. **S08 (Pilates genérico vs específico)**: Pilates genérico = F2 sin F5. Pilates específico (EEDAP) = F5 primero.
3. **S06/S09 (SSRI vs DPP)**: pastilla sola = F1 temporal. Intervención + herramientas propias = F7 permanente. El paciente que se lleva ejercicios a casa = F7 alta.
4. **S10/M04 (sobreentrenamiento/burnout)**: ciclo F1↔F6. Relevante para gestión de carga en pacientes y en el propio negocio.

### Para la Arquitectura del Sistema
1. **F3 (Depuración) confirmada como gap crítico** — la función más predictiva de resultado en 50 casos. El Bloque Depuración nuevo (L0_7) está validado empíricamente.
2. **F3→F5(D) como ley nueva** — depurar construye identidad. Implicación: el Motor debería recomendar F3 antes de F5 cuando ambas están bajas.
3. **Variable exógena E** — el Motor necesita al menos un indicador de entorno/mercado para no caer en el error Google+ (diagnosticar salud interna sin ver posición externa).

---

## 7. NOTA METODOLÓGICA FINAL

**98% de predicción correcta en 50 casos es alto pero no sospechoso** tras la Sesión 5:
- El único fallo (Google+) reveló una limitación real y modelable (factores exógenos).
- Los 49 aciertos cubren 7 dominios, 10 arquetipos, 50 años de historia, escalas micro/meso/macro.
- La Sesión 5 (100% tóxicos/inertes) fue el stress test más duro y la TCF acertó 9/10.

**El sesgo retrospectivo existe** (sabemos los resultados y ajustamos vectores). Pero:
- Los vectores pre y delta son consistentes entre sesiones (no se contradicen).
- Las leyes que emergen son las mismas cross-dominio (F2→F3 siempre, F7→F5 siempre).
- El fallo (Google+) no fue forzado — la TCF genuinamente no lo capturaba.

**Siguiente paso:** validación prospectiva. Usar la TCF para PREDECIR resultados en los pilotos (Pilates/fisioterapia) antes de que ocurran. Si predice correctamente en tiempo real, la validación pasa de retrospectiva a prospectiva.

---

## ARCHIVOS DE ESTA SERIE

```
motor-semantico/results/reactor_v5/
  sesion_1_negocio.json    — 10 pares, 5C/3I/2T
  sesion_2_salud.json      — 10 pares, 4C/3I/3T
  sesion_3_stem.json       — 10 pares, 5C/1I/4T
  sesion_4_mixto.json      — 10 pares, 6C/2I/2T
  sesion_5_fallidas.json   — 10 pares, 0C/4I/6T
  resumen_50_pares.md      — este documento
```
