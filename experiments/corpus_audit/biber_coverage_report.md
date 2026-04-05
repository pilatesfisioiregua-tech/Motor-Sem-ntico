# Biber Multi-Dimensional Analysis — Informe de Cobertura

**Fecha**: 2026-04-05  
**Corpus**: gold_set_v2 (2990 textos)  
**Método**: Implementación manual NLTK + regex para español  

## ADVERTENCIAS DE VERIFICACIÓN

- **[SUPOSICION]**: Los pesos de cada dimensión son adaptaciones de Biber (1988) y
  Berber Sardinha (2004) al español. No comparables con valores calibrados en inglés.
- **[VERIFICADO]**: Las features lingüísticas (pronombres, nominalizaciones, etc.)
  son conteos directos sobre el texto con regex verificados manualmente.
- **[VERIFICADO]**: La normalización z-score es determinista.
- Lo que es válido: la distribución RELATIVA entre textos (quién es más conversacional
  que quién). Los valores absolutos NO son comparables con otros corpus.
- BiberPy no instalado; spaCy es_core_news_lg no disponible (Python 3.9).
  Fallback a implementación manual — documentado.

---

## 1. Descripción de las 6 Dimensiones Biber

| Dim | Polo Positivo | Polo Negativo | Features principales |
|-----|---------------|---------------|---------------------|
| D1 | Involucrado (conversacional) | Informacional (expositivo) | Pronombres 1a/2a persona, contracciones vs nominalizaciones, preposiciones, longitud oraciones |
| D2 | Narrativo | No-narrativo | Verbos pasado, pronombres 3a persona, verbos perfectivos |
| D3 | Referencia explícita | Dependiente de contexto | Nominalizaciones, frases prep. largas vs demostrativos, pronombres átonos |
| D4 | Persuasión abierta | No persuasivo | Modales de necesidad, predicciones, evaluativos |
| D5 | Abstracto | No-abstracto | Voz pasiva, nominalizaciones, subordinadas vs adverbios de modo |
| D6 | Elaboración online | Reducida | Cláusulas relativas, conectores discursivos |

---

## 2. Distribución por Dimensión

> Umbral extremo: z > +1.0 (polo positivo) / z < -1.0 (polo negativo)

### d1_involucrado_informacional

Mean bruto: -13.753 | Std: 5.776

| Polo | N | % |
|------|---|---|
| involucrado (z > +1) | 450 | 15.1% |
| neutro (-1 ≤ z ≤ +1) | 2133 | 71.3% |
| informacional (z < -1) | 407 | 13.6% |

**Top-5 más involucrado** (z más alto):
  - retry-00837 (z=3.44)
  - gold-01619 (z=3.295)
  - gold-02999 (z=3.264)
  - retry-00811 (z=2.932)
  - retry-00036 (z=2.868)

**Top-5 más informacional** (z más bajo):
  - gold-02484 (z=-4.645)
  - gold-02717 (z=-4.481)
  - gold-00137 (z=-4.204)
  - gold-01712 (z=-3.707)
  - gold-01826 (z=-3.697)

### d2_narrativo

Mean bruto: 10.724 | Std: 5.000

| Polo | N | % |
|------|---|---|
| narrativo (z > +1) | 398 | 13.3% |
| neutro (-1 ≤ z ≤ +1) | 2130 | 71.2% |
| no_narrativo (z < -1) | 462 | 15.5% |

**Top-5 más narrativo** (z más alto):
  - retry-00278 (z=4.565)
  - gold-01016 (z=4.219)
  - gold-01828 (z=3.75)
  - gold-00572 (z=3.645)
  - gold-02629 (z=3.57)

**Top-5 más no_narrativo** (z más bajo):
  - gold-00040 (z=-2.145)
  - gold-00067 (z=-2.145)
  - gold-00134 (z=-2.145)
  - gold-00226 (z=-2.145)
  - gold-00313 (z=-2.145)

### d3_ref_explicita

Mean bruto: 5.079 | Std: 4.023

| Polo | N | % |
|------|---|---|
| ref_explicita (z > +1) | 444 | 14.8% |
| neutro (-1 ≤ z ≤ +1) | 2081 | 69.6% |
| ref_contextual (z < -1) | 465 | 15.6% |

**Top-5 más ref_explicita** (z más alto):
  - gold-00137 (z=8.882)
  - gold-02717 (z=6.692)
  - gold-01712 (z=4.952)
  - gold-01826 (z=4.774)
  - gold-02324 (z=4.363)

**Top-5 más ref_contextual** (z más bajo):
  - gold-01619 (z=-3.046)
  - gold-00883 (z=-2.92)
  - gold-02804 (z=-2.864)
  - retry-00413 (z=-2.816)
  - gold-00477 (z=-2.756)

### d4_persuasion

Mean bruto: 1.822 | Std: 1.215

| Polo | N | % |
|------|---|---|
| persuasivo (z > +1) | 383 | 12.8% |
| neutro (-1 ≤ z ≤ +1) | 2273 | 76.0% |
| no_persuasivo (z < -1) | 334 | 11.2% |

**Top-5 más persuasivo** (z más alto):
  - retry-00016 (z=8.273)
  - gold-00754 (z=7.734)
  - gold-00418 (z=7.71)
  - gold-01900 (z=7.188)
  - gold-01016 (z=7.104)

**Top-5 más no_persuasivo** (z más bajo):
  - gold-00004 (z=-1.5)
  - gold-00031 (z=-1.5)
  - gold-00149 (z=-1.5)
  - gold-00179 (z=-1.5)
  - gold-00184 (z=-1.5)

### d5_abstracto

Mean bruto: 3.123 | Std: 2.081

| Polo | N | % |
|------|---|---|
| abstracto (z > +1) | 407 | 13.6% |
| neutro (-1 ≤ z ≤ +1) | 2195 | 73.4% |
| no_abstracto (z < -1) | 388 | 13.0% |

**Top-5 más abstracto** (z más alto):
  - gold-00137 (z=11.354)
  - gold-01549 (z=5.706)
  - retry-00793 (z=5.466)
  - gold-02471 (z=5.225)
  - gold-02717 (z=5.225)

**Top-5 más no_abstracto** (z más bajo):
  - gold-00044 (z=-1.501)
  - gold-00096 (z=-1.501)
  - gold-00130 (z=-1.501)
  - gold-00134 (z=-1.501)
  - gold-00149 (z=-1.501)

### d6_elaboracion

Mean bruto: 3.638 | Std: 2.485

| Polo | N | % |
|------|---|---|
| elaborado (z > +1) | 447 | 14.9% |
| neutro (-1 ≤ z ≤ +1) | 1995 | 66.7% |
| no_elaborado (z < -1) | 548 | 18.3% |

**Top-5 más elaborado** (z más alto):
  - gold-00153 (z=6.584)
  - gold-00640 (z=5.026)
  - retry-00075 (z=5.023)
  - gold-01674 (z=4.684)
  - retry-00487 (z=4.17)

**Top-5 más no_elaborado** (z más bajo):
  - gold-00003 (z=-1.464)
  - gold-00004 (z=-1.464)
  - gold-00038 (z=-1.464)
  - gold-00040 (z=-1.464)
  - gold-00044 (z=-1.464)

---

## 3. Mapa de Cobertura — Polos Sub-representados

**Todos los polos tienen cobertura >= 10%.** El corpus es suficientemente diverso.

---

## 4. Recomendaciones para T-CORPUS-AUGMENT

No hay polos críticos sub-representados. El corpus actual cubre bien las 6 dimensiones Biber.

Para mayor representatividad en dimensiones con distribución sesgada,
considerar añadir textos de los polos menos representados aunque superen el 10%.

---

## 5. Distribución por Cluster (corpus_features)

Scores z-score medios por cluster (de T-CORPUS-AUDIT):

| Cluster | D1 | D2 | D3 | D4 | D5 | D6 |
|---------|----|----|----|----|----|----|
| 0 | 0.44 | 0.04 | -0.56 | 0.03 | -0.28 | 0.69 |
| 1 | 0.02 | -0.10 | 0.05 | -0.14 | -0.17 | -0.31 |
| 2 | -0.47 | 0.52 | 0.17 | -0.03 | 0.44 | 0.28 |
| 3 | 0.51 | 0.06 | -0.52 | -0.00 | -0.30 | 0.19 |
| 4 | -0.29 | -0.24 | 0.36 | 0.00 | 0.05 | -0.26 |
| 5 | -0.22 | -0.20 | 0.37 | 0.19 | 0.31 | -0.08 |

---

## 6. Interpretación y Limitaciones

### Fortalezas
- Las features de conteo son directamente verificables en el texto
- La normalización z-score garantiza comparabilidad relativa entre textos
- La clasificación por polos (>1σ) es conservadora y robusta

### Limitaciones [SUPOSICION]
- Los pesos de las dimensiones son adaptaciones, no calibraciones propias
- Regex de verbos pasado puede incluir participios adjetivales (sobreestimación D2)
- Regex de pronombres 2a persona incluye formas de tratamiento (usted/le) que son formales
- Sin POS-tagger: no distingue homónimos (e.g., 'que' como conjunción vs relativo)
- La dimensión D6 (elaboración online) en Biber original refiere a fenómenos de
  producción oral que no aplican directamente a texto escrito

### Validación recomendada (P7 del ticket)
- Muestrear 5 textos extremos D1 polo 'involucrado' y verificar que son conversacionales
- Muestrear 5 textos extremos D1 polo 'informacional' y verificar que son expositivos
- Si un texto de 'foro' sale como 'informacional', revisar los pesos de D1

---

*Generado por scripts/biber_analysis.py — T-CORPUS-BIBER — 2026-04-05*
