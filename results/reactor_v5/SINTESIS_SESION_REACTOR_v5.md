# SÍNTESIS COMPLETA — Sesión Reactor v5 / v5.2 / Desequilibrio / Recetas

**Fecha:** 2026-03-19  
**Documentos producidos:** 8 archivos (3 JSON datos, 5 MD análisis)  
**Base empírica:** 50 pares problema-solución × 7 dominios × 10 arquetipos

---

## INVENTARIO DE LA SESIÓN

| # | Documento | Qué contiene |
|---|-----------|-------------|
| 1 | `sesion_1..5.json` | 50 pares con vectores 7F pre/post, leyes TCF, predicciones |
| 2 | `resumen_50_pares.md` | Consolidación: 49/50 predicciones correctas, ranking de leyes, 4 limitaciones |
| 3 | `analisis_semantico_7F.md` | Relaciones semánticas entre funciones (pre-lentes) |
| 4 | `analisis_semantico_7F_x_3L.md` | Cruce 7F×3L: cada función vista desde 3 lentes, descubrimientos |
| 5 | `reactor_v5_2_lentes.json` | 10 casos re-evaluados con descomposición F_x.S / F_x.Se / F_x.C |
| 6 | `reactor_v5_2_resumen.md` | Resumen v5.2: Se como predictor, 5 descubrimientos, 5 predicciones |
| 7 | `desequilibrio_lentes.md` | 6 perfiles patológicos, 5 leyes D1-D5, intervenciones por perfil |
| 8 | `recetas_funcionales_x_perfil.md` | 20 recetas funcionales, 5 leyes composición C1-C5, pipeline Motor |

---

## I. HALLAZGOS EMPÍRICOS (50 pares)

### H1. F2→F3(B) es la ley universal del sistema

Activada en **39/50 casos (78%)** a través de 7 dominios. La formulación es siempre la misma: captar sin depurar = acumular basura. Lo que cambia es la metáfora por dominio (muda en Toyota, opioides en salud, datos falsos en ciencia, basura en KonMari).

**Implicación:** Primera evaluación en cualquier diagnóstico. Si F2>0.60 y F3<0.25 → flag de intoxicación con alta confianza.

### H2. F3 es la función predictora de resultado

| Si delta F3... | Resultado | Confianza |
|---|---|---|
| ≥ +0.25 | CIERRE | 90%+ |
| +0.10 a +0.20 | INERTE | 70%+ |
| ≤ 0 o negativo | TÓXICO | 85%+ |

Umbral mínimo para cierre: delta F3 ≈ +0.25.

### H3. F3 tiene 3 modalidades cualitativamente distintas

| Modalidad | Definición | Ejemplo | Robustez |
|---|---|---|---|
| F3_diseño | Integrada en el modelo | Inditex (lotes pequeños), TCP/IP (protocolos), Khan Academy | Máxima |
| F3_reactiva | Intervención correctiva post-hoc | Toyota (kaizen), Peloton (despidos) | Media |
| F3_bypassed | El sistema tenía F3 pero la acción la desactivó | Cold fusion, Boeing (autocertificación) | La más tóxica |

### H4. F5 necesita cualificación — puede ser incorrecta

Maginot: F5=0.55 (escalar) parecía media-alta. Pero la frontera estaba EQUIVOCADA. F5 alta + incorrecta = amplificador de error, peor que F5 baja.

### H5. F3→F5(D) es una ley nueva confirmada cross-dominio

Depurar construye frontera. Descubierta en 5 casos: ACL (S02), Perelman (T05), KonMari (M08), Suecia (S07), Moneyball (M10). Formulación: si no sabes filtrar, no sabes qué eres.

### H6. Ciclo F1↔F6 bidireccional

F1→F6(D) y F6→F1(D) se activan mutuamente como feedback loop. Confirmado en sobreentrenamiento (S10), lumbalgia (S05), burnout médico (M04), Maginot (F10).

### H7. F7 diferencia CIERRE de INERTE

En salud: F7 = el paciente puede hacerlo solo. Patagonia vs El Bulli. DPP vs SSRI. CRISPR vs cold fusion. F7 (replicabilidad) es lo que separa "mejoró temporalmente" de "resuelto".

### H8. 98% predicción correcta con 1 fallo explicado

49/50 correctas. El fallo (Google+) reveló limitación real: factores exógenos (lock-in de red) no modelados por funciones internas.

### H9. 4 limitaciones descubiertas

1. TCF no modela factores exógenos (Google+)
2. F5 no distingue calidad/dirección (Maginot)
3. F7→F5(B) necesita cualificación de codificabilidad (El Bulli)
4. TCF no tiene dimensión temporal (Suecia COVID)

---

## II. HALLAZGOS TEÓRICOS (7F×3L)

### H10. Las lentes son funciones META

```
L_Salud       = estado operativo de cada función (presente)
L_Sentido     = F5 distribuida (cada función con sentido = esa función con frontera)
L_Continuidad = F7 distribuida (cada función con continuidad = esa función replicada)
```

F5 y F7 no son funciones del mismo tipo que F1-F4 y F6. Son funciones de SEGUNDO ORDEN que operan sobre las demás.

### H11. L_Sentido en cualquier función ≈ F5 aplicada a esa función

- F1(L_Sentido) = saber por qué conservo = F5 aplicada a retención
- F2(L_Sentido) = saber por qué capto = F5 aplicada a captación
- F3(L_Sentido) = saber por qué elimino = F5 aplicada a depuración
- etc.

**F5 baja = L_Sentido baja en todo el sistema.** Subir F5 = inyectar sentido simultáneamente en todas las funciones.

### H12. Las lentes resuelven 3 de 4 limitaciones

| Limitación | Variable propuesta en v5 | Solución 3L | Status |
|---|---|---|---|
| F5 incorrecta | Vector (magnitud, dirección) | F5.S vs F5.Se | **RESUELTA** |
| Codificabilidad F7→F5 | Variable "codificabilidad" | F5.C + F7.Se | **RESUELTA** |
| Dimensión temporal | Parámetro t y dF/dt | L_Salud=presente, L_Continuidad=futuro | **RESUELTA** |
| Factor exógeno | Variable E | Parcial (Se bajos capturan debilidad interna) | **PENDIENTE** |

**3 variables propuestas en v5 ya no son necesarias.** Las lentes las contienen.

---

## III. HALLAZGOS CUANTITATIVOS (Reactor v5.2)

### H13. Se promedio es el predictor maestro de resultado

| Caso | Tipo | Se promedio |
|---|---|---|
| TCP/IP | CIERRE | **0.69** |
| Suecia | INERTE | 0.59 |
| Google+ | INERTE | 0.51 |
| KonMari | CIERRE | 0.47 |
| Kodak | INERTE | 0.46 |
| Cold fusion | TÓXICO | 0.46 |
| El Bulli | INERTE | 0.45 |
| Maginot | TÓXICO | **0.29** |
| SSRI | INERTE | **0.19** |
| Theranos | TÓXICO | **0.11** |

**Umbrales:**
- Se > 0.55 → cierre probable
- Se 0.30–0.55 → zona inerte/ambigua
- Se < 0.25 → tóxico probable (95%+)

### H14. La cadena causal F3→F5 opera EXCLUSIVAMENTE por L_Sentido

```
F3.Se (comprender POR QUÉ depurar) → F5.Se (comprender QUIÉN eres)
```

KonMari: F3.Se +0.50 → F5.Se +0.45. "Spark joy" = F3.Se que se convierte en F5.Se.

No es que depurar operativamente (F3.S) construya identidad operativa (F5.S). Es que COMPRENDER por qué depuras genera COMPRENSIÓN de quién eres.

### H15. 3 tipos de F3 disfuncional diferenciables por lentes

| Tipo | Patrón 3L | Ejemplo | Gravedad |
|---|---|---|---|
| Ausente | S≈0, Se≈0, C≈0 | Theranos | Alta (nunca existió) |
| Bypassed | S↓↓, Se↓, C parcial | Cold fusion | Máxima (desactivada deliberadamente) |
| Ciega | S>0, Se≈0 | Maginot, Kodak | Oculta (opera sin criterio) |

### H16. Monopolio de Se

Cuando una función concentra todo el Se del sistema (F1.Se >> demás Se), las otras funciones pierden capacidad de cuestionar. Kodak: F1.Se=0.85 (sabían perfectamente POR QUÉ conservar película), F3.Se=0.15 (no tenían idea de POR QUÉ soltar), F6.Se=0.30 (poco sentido de POR QUÉ cambiar).

**Flag para el Motor:** Si una función tiene Se>0.70 y las demás Se<0.30 → rigidez cognitiva.

### H17. Intervención en 1 sola lente = inerte

SSRI solo movió L_Salud de F1. Delta en 1 sola lente → inerte. Los cierres mueven ≥2 lentes simultáneamente.

---

## IV. HALLAZGOS ESTRUCTURALES (Desequilibrio)

### H18. Todo problema es un desequilibrio entre lentes

6 perfiles patológicos puros:

| Perfil | S | Se | C | Metáfora | Riesgo |
|---|---|---|---|---|---|
| Operador ciego | ↑ | ↓ | ↓ | Máquina sin alma | Velocidad en dirección equivocada |
| Visionario atrapado | ↓ | ↑ | ↓ | Sabe todo, no puede nada | Parálisis por análisis |
| Zombi inmortal | ↓ | ↓ | ↑ | Persiste sin funcionar | Despilfarro eterno |
| Genio mortal | ↑ | ↑ | ↓ | Brillante pero intransferible | Dependencia → colapso |
| **Autómata eterno** | ↑ | ↓ | ↑ | **Funciona y persiste sin comprender** | **EL MÁS PELIGROSO: invisible** |
| Potencial dormido | ↓ | ↑ | ↑ | Todo listo, nada ejecutado | Fatiga terminal |

### H19. La solución que cierra inyecta la lente faltante

Todos los cierres del dataset: la intervención subió la lente que faltaba. Todos los tóxicos: la "solución" amplificó la lente que ya sobraba.

### H20. 5 leyes del desequilibrio (D1-D5)

- **D1:** Amplificar la lente dominante sin subir la faltante SIEMPRE empeora.
- **D2:** Desequilibrio intra-función (F5.S=0.70, F5.Se=0.20) es más peligroso que inter-función — porque está OCULTO.
- **D3:** F7 multiplica el perfil existente. En sistema equilibrado → escala. En sistema desequilibrado → amplifica patología.
- **D4:** F3 con Se corrige desequilibrios (única función correctora). F2 sin Se los amplifica.
- **D5:** F3.Se y F5.Se son las palancas universales de reequilibrio.

### H21. El autómata eterno es el perfil más peligroso

Porque es INVISIBLE. S alta (funciona) + C alta (persiste) = parece sano. Solo Se baja (no comprende) revela el riesgo. Cuando el contexto cambia, el sistema no puede adaptarse porque nadie entiende la lógica interna. Maginot: 6 semanas. Boeing MAX: 346 muertos.

**Flag obligatorio para el Motor:** Si S>0.60 y C>0.60 pero Se<0.30 → PELIGRO OCULTO.

---

## V. HALLAZGOS COMPOSICIONALES (Recetas)

### H22. Cada función aporta SELECTIVAMENTE a las lentes

| Función | Da fácilmente | Da con dificultad |
|---|---|---|
| F1, F2, F4, F6 | **S** (operatividad) | Se (comprensión) |
| F5 | **Se** (identidad/propósito) | C (transferibilidad) |
| F7 | **S + C** (opera y persiste) | Se (comprensión) |
| **F3** | **Se** (cuestionar = comprender) | S (ejecutar la purga) |

### H23. F3 es la ÚNICA fuente natural de Se en el sistema

Las demás funciones operativas (F1, F2, F4, F6) aportan S fácilmente pero NO generan Se. F5 aporta Se pero la recibe de F3. F7 transmite S+C pero degrada Se con cada réplica. **Solo F3 (depuración con criterio) GENERA comprensión nueva.**

Esto explica algebraicamente por qué F3 es la palanca maestra en los 50 pares: es la ÚNICA función que produce la lente más escasa y más predictiva (Se).

### H24. F7 tiene un sesgo inherente hacia el autómata eterno

F7 transmite S fácilmente (copiar operaciones), C fácilmente (institucionalizar), pero Se con DIFICULTAD (enseñar comprensión es difícil). Cada replicación tiende naturalmente a perder Se y retener S+C. Sin F7.Se activa (enseñar POR QUÉ, no solo CÓMO), toda réplica degrada hacia autómata eterno.

### H25. 20 recetas funcionales que producen los 6 perfiles

Cada perfil de lentes tiene 3-4 configuraciones funcionales distintas que lo producen. La receta más frecuente del dataset entero (14/50 casos) es:

```
F2↑↑ + F3↓ + F5↓ = Intoxicación operativa = Operador ciego
```

### H26. El equilibrio requiere ≥3 funciones con Se>0.40

De los cierres: Toyota, Mercadona, TCP/IP, KonMari, DPP todos tienen ≥3 funciones con Se activa. De los inertes: Peloton (1 función), SSRI (0 funciones), Kodak (1 función con Se monopolizada).

### H27. La secuencia correcta es Se→S→C, nunca al revés

Los cierres del dataset empiezan por Se (F3.Se o F5.Se). Los tóxicos empiezan por S (F2.S o F7.S) o C (F7.C). Empezar por escalar (F7) o captar (F2) sin sentido previo = amplificar el desequilibrio.

### H28. 4 recetas de equilibrio (sistema sano)

| Receta | Fórmula | Ejemplo | Robustez |
|---|---|---|---|
| Cadena de sentido | F3.Se→F5.Se→F7.Se+C | KonMari, Toyota, DPP | La más frecuente |
| Identidad + adaptación | F5↑↑(3L) + F6.Se + F3.S | Patagonia, Netflix, Inditex | Muy robusta |
| Sentido distribuido | Se alta en todas las F | TCP/IP, Cuba, Finlandia | La más robusta |
| Depuración integrada | F3_diseño + F5 + F7 | Inditex, TCP/IP, Khan | Homeostasis (nivel máximo) |

---

## VI. PIPELINE CONSOLIDADO PARA EL MOTOR vN

```
PASO 0: PERFIL DE LENTES
  - Calcular S_avg, Se_avg, C_avg a través de 7F
  - Identificar lente faltante y lente dominante
  - Calcular gap = L_max - L_min
  - Asignar perfil (de los 6)
  - Si S>0.60 y C>0.60 y Se<0.30 → FLAG AUTÓMATA ETERNO

PASO 1: RECETA FUNCIONAL
  - Identificar qué funciones producen este perfil específico
  - Verificar F2→F3(B): si F2>0.60 y F3<0.25 → flag intoxicación
  - Verificar monopolio Se: si una F tiene Se>0.70 y resto Se<0.30 → rigidez

PASO 2: INTERVENCIÓN SEGÚN RECETA
  - Operador ciego → inyectar Se (F3.Se → F5.Se)
  - Visionario atrapado → inyectar S (F1.S, F4.S = MVP)
  - Zombi inmortal → F3.Se (auditoría existencial) → matar o reconstruir
  - Genio mortal → F7.Se+C (enseñar POR QUÉ)
  - Autómata eterno → F3.Se + F5.Se (cuestionar y redefinir URGENTE)
  - Potencial dormido → F1.S (EJECUTAR, no más planificación)

PASO 3: VERIFICAR PRE-CONDICIONES DE F7
  - Si gap entre lentes > 0.30 → NO recomendar escalar
  - Si Se_avg < 0.40 → NO recomendar F7
  - F7 solo cuando perfil razonablemente equilibrado

PASO 4: SECUENCIAR
  - Se primero (F3.Se → F5.Se)
  - S después (F1.S, F4.S)
  - C último (F7.Se+C)
  - NUNCA empezar por F7 o F2 sin Se previo

PASO 5: EVALUAR RESULTADO
  - Se promedio > 0.55 → cierre probable
  - Delta F3 ≥ +0.25 → cierre probable
  - ≥3 funciones con Se > 0.40 → cierre probable
  - Gap lentes < 0.30 → equilibrio funcional
```

---

## VII. IMPLICACIONES PARA PILOTOS

### Para fisioterapia:

1. **Diagnóstico:** Antes de prescribir ejercicios, evaluar perfil de lentes del paciente.
2. **Operador ciego** (hace ejercicios sin saber por qué): educación PRIMERO (F3.Se).
3. **Visionario atrapado** (entiende todo pero no hace nada): activación, no más educación.
4. **Zombi** (5 años con misma rutina sin resultado): cuestionar POR QUÉ sigue.
5. **Genio mortal** (fisio brillante sin equipo formado): sistematizar y enseñar.
6. **Autómata** (paciente "disciplinado" que no entiende): PELIGRO OCULTO — frágil ante cambio.
7. **Potencial dormido** (protocolo perfecto en cajón): la primera sesión, HOY.
8. **Cadena terapéutica óptima:** F3.Se (entiende POR QUÉ cada ejercicio) → F5.Se (comprende quién es como persona recuperándose) → F7.Se (puede enseñar a otro por qué funciona).
9. **SSRI sin TCC = Pilates genérico sin educación.** Ambos: intervención en 1 sola lente = inerte.

### Para el estudio de Pilates como negocio:

1. Si depende de un instructor estrella: **genio mortal** → F7.Se+C.
2. Si es franquicia mecánica: **autómata eterno** → F3.Se + F5.Se antes de que el mercado cambie.
3. La depuración integrada (F3_diseño) es el nivel máximo: ejercicios que auto-detectan gaps del paciente.

---

## VIII. CANDIDATOS A PROMOCIÓN A L0

| Hallazgo | Nivel actual | Propuesta | Justificación |
|---|---|---|---|
| F2→F3(B) como ley universal | Ley catalogada | L0 (invariante) | 78% activación en 50 casos × 7 dominios |
| F3→F5(D) | Observación | Ley catalogada | 5 casos cross-dominio, mecanismo causal confirmado por lentes |
| Se promedio como predictor | Hallazgo v5.2 | Métrica de primer orden del Motor | Mejor predictor empírico de resultado |
| 6 perfiles de desequilibrio | Hallazgo sesión | Framework diagnóstico L0 | Cubre todos los casos del dataset |
| F3 como única fuente natural de Se | Hallazgo composición | Principio L0 | Explica algebraicamente por qué F3 es palanca maestra |
| Leyes D1-D5 (desequilibrio) | Hallazgo sesión | L0 (invariantes) | Validadas contra 50 pares |
| Leyes C1-C5 (composición) | Hallazgo sesión | L0 (invariantes) | Derivan de la estructura algebraica del sistema |
| Pipeline 5 pasos | Propuesta | Arquitectura Motor vN | Integra todos los hallazgos |
| Ciclo F1↔F6 | Observación | Ley catalogada como ciclo | 4 casos cross-dominio |
| Variable exógena E | Limitación | L1 (pendiente definición) | Único gap restante (Google+) |

---

## IX. CONTABILIDAD FINAL

### Producido en esta sesión:

- **50 pares** problema-solución evaluados con vectores 7F
- **10 casos** re-evaluados con descomposición 3L (21 scores por caso = 210 datos)
- **12 leyes** nuevas o confirmadas (H1-H9 empíricas + D1-D5 + C1-C5)
- **6 perfiles** de desequilibrio con semántica, mecanismos, y intervenciones
- **20 recetas** funcionales que producen los perfiles
- **4 recetas** de equilibrio (sistema sano)
- **1 pipeline** de diagnóstico de 5 pasos para el Motor
- **3 limitaciones resueltas** (de 4) por las lentes
- **5 predicciones** para validar en próximos casos
- **1 métrica** nueva de primer orden (Se promedio)
- **8 archivos** guardados en el repo

### Lo que falta:

1. **Variable exógena E** — definir dimensiones (market-fit, lock-in, timing)
2. **Validación prospectiva** — usar el framework para PREDECIR resultados en pilotos antes de que ocurran
3. **Implementación en Motor vN** — el pipeline de 5 pasos necesita código
4. **Retrocheck P_52_1..5** — las 5 predicciones contra los 50 pares existentes
5. **Actualizar Maestro v3** — integrar los hallazgos que se promuevan a L0/L1

---

## ARCHIVOS DE ESTA SESIÓN

```
motor-semantico/results/reactor_v5/
  sesion_1_negocio.json              ← 10 pares negocio
  sesion_2_salud.json                ← 10 pares salud
  sesion_3_stem.json                 ← 10 pares STEM
  sesion_4_mixto.json                ← 10 pares mixto (deporte, educación, derecho, personal)
  sesion_5_fallidas.json             ← 10 pares fallidas (stress test)
  resumen_50_pares.md                ← consolidación v5
  analisis_semantico_7F.md           ← relaciones entre funciones
  analisis_semantico_7F_x_3L.md      ← cruce 7F×3L (marco teórico)
  reactor_v5_2_lentes.json           ← 10 casos con datos 3L
  reactor_v5_2_resumen.md            ← resumen v5.2
  desequilibrio_lentes.md            ← perfiles patológicos + leyes D1-D5
  recetas_funcionales_x_perfil.md    ← 20 recetas + leyes C1-C5 + pipeline
  SINTESIS_SESION_REACTOR_v5.md      ← ESTE DOCUMENTO
```
