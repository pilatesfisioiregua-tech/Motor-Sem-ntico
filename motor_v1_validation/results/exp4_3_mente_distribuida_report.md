# EXP 4.3 — MENTE DISTRIBUIDA (Analisis)

## A) Convergencia por Output

| Output | Estado | Rondas | Cambios por ronda | Ratio medio | Decay exp? |
|--------|--------|--------|-------------------|-------------|------------|
| v31_best | convergido | 4 | [12, 7, 10, 0] | 0.671 | No |
| 70b_worst | max_rondas | 5 | [11, 13, 6, 7, 10] | 1.060 | No |
| maverick_medium | max_rondas | 5 | [16, 12, 10, 5, 3] | 0.671 | Si |
| gptoss_depurar | convergido | 5 | [16, 9, 5, 5, 2] | 0.630 | No |
| qwen3t_medium | convergido | 4 | [11, 9, 9, 0] | 0.606 | No |

### Curvas de cambios

**v31_best** (max=12):
```
  R0: ######################################## 12
  R1: ####################### 7
  R2: ################################# 10
  R3:  0
```

**70b_worst** (max=13):
```
  R0: ################################## 11
  R1: ######################################## 13
  R2: ################## 6
  R3: ###################### 7
  R4: ############################### 10
```

**maverick_medium** (max=16):
```
  R0: ######################################## 16
  R1: ############################## 12
  R2: ######################### 10
  R3: ############ 5
  R4: ######## 3
```

**gptoss_depurar** (max=16):
```
  R0: ######################################## 16
  R1: ###################### 9
  R2: ############ 5
  R3: ############ 5
  R4: ##### 2
```

**qwen3t_medium** (max=11):
```
  R0: ######################################## 11
  R1: ################################# 9
  R2: ################################# 9
  R3:  0
```

## B) Perfil de Cada Modelo

| Modelo | Contribuciones | Conexiones | P.Ciegos | Rondas activas | Perfiles |
|--------|---------------|------------|----------|----------------|----------|
| gpt-oss-120b | 119 | 77 | 46 | 22 | Sembrador, Conector, Detector de huecos |
| minimax-m2.5 | 75 | 55 | 45 | 22 | Sembrador, Conector, Detector de huecos |
| qwen3-235b | 63 | 48 | 25 | 22 | Sembrador, Conector, Detector de huecos |
| v3.2-chat | 56 | 52 | 28 | 23 | Sembrador, Conector, Detector de huecos |
| deepseek-v3.1 | 52 | 45 | 22 | 18 | Sembrador, Conector, Detector de huecos |
| deepseek-r1 | 44 | 30 | 12 | 16 | Sembrador, Conector |
| v3.2-reasoner | 42 | 28 | 14 | 18 | Sembrador, Conector, Detector de huecos |
| opus | 33 | 34 | 8 | 15 | Sembrador, Conector |
| cogito-671b | 31 | 29 | 22 | 20 | Sembrador, Conector, Detector de huecos |
| kimi-k2.5 | 25 | 19 | 15 | 11 | Sembrador, Conector, Detector de huecos |
| glm-4.7 | 20 | 8 | 2 | 5 | Sembrador |

### Contribuciones por ronda (agregadas)

- **gpt-oss-120b**: [32, 29, 29, 15, 14]
- **minimax-m2.5**: [20, 14, 13, 15, 13]
- **qwen3-235b**: [22, 16, 10, 9, 6]
- **v3.2-chat**: [18, 13, 11, 9, 5]
- **deepseek-v3.1**: [25, 7, 15, 2, 3]
- **deepseek-r1**: [20, 8, 8, 5, 3]
- **v3.2-reasoner**: [18, 12, 7, 4, 1]
- **opus**: [13, 6, 6, 5, 3]
- **cogito-671b**: [13, 7, 6, 3, 2]
- **kimi-k2.5**: [11, 10, 3, 1]
- **glm-4.7**: [17, 3]

## C) Comparacion: Mente Distribuida vs Mesa Redonda vs Max Mecanico

### v31_best

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 18 | 20 | 21 |
| Nivel medio | 3.10 | 3.19 | 4.00 |
| Conexiones | 0 | 0 | 77 |
| Puntos ciegos detectados | 0 | 0 | 40 |

### 70b_worst

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 15 | 15 | 21 |
| Nivel medio | 2.76 | 2.76 | 4.00 |
| Conexiones | 0 | 0 | 99 |
| Puntos ciegos detectados | 0 | 0 | 59 |

### maverick_medium

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 10 | 16 | 21 |
| Nivel medio | 2.52 | 2.90 | 4.00 |
| Conexiones | 0 | 0 | 85 |
| Puntos ciegos detectados | 0 | 0 | 62 |

### gptoss_depurar

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 15 | 21 | 21 |
| Nivel medio | 2.90 | 3.81 | 3.95 |
| Conexiones | 0 | 0 | 86 |
| Puntos ciegos detectados | 0 | 0 | 44 |

### qwen3t_medium

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas (>0) | 21 | 21 | 21 |
| Celdas nivel 3+ | 19 | 21 | 21 |
| Nivel medio | 3.14 | 3.67 | 4.00 |
| Conexiones | 0 | 0 | 78 |
| Puntos ciegos detectados | 0 | 0 | 34 |

### Agregado (todos los outputs)

| Metrica | Max mecanico | Mesa Redonda | Mente Distribuida |
|---------|-------------|-------------|-------------------|
| Celdas cubiertas total | 105 | 105 | 105 |
| Celdas 3+ total | 77 | 93 | 105 |
| Nivel medio promedio | 2.886 | 3.267 | 3.990 |
| Conexiones total | 0 | 0 | 425 |
| Puntos ciegos total | 0 | 0 | 239 |

## D) Top 5 Contribuciones Mas Valiosas

**1. v31_best / Sentido×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Contradicción central: elección forzada entre calidad inmediata y crecimiento futuro

**2. v31_best / Continuidad×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: La contradicción formal es que la estabilización requiere tiempo que el runway no permite

**3. gptoss_depurar / Salud×Frontera** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Solo al equilibrar salud y finanzas la expansión se vuelve lógica

**4. qwen3t_medium / Sentido×Adaptar** (salto: 0 -> 4, +4)
- Modelo: sonnet (ronda -1)
- Evidencia: Patrón 'miedo + acción reactiva' redefine el conflicto: no es estratégico sino supervivencia emocional

**5. v31_best / Salud×Depurar** (salto: 0 -> 3, +3)
- Modelo: sonnet (ronda -1)
- Evidencia: 47 bugs abiertos afectan calidad y churn

## E) Top 5 Conexiones Mas Interesantes

**1. Salud×Depurar <-> Continuidad×Distribuir** (cross-lente: Salud <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: Los 47 bugs no solo afectan churn actual (8%) sino que aceleran la caída proyectada del MRR a €7,200 - cada bug sin resolver aumenta la velocidad de deterioro

**2. Sentido×Frontera <-> Continuidad×Frontera** (cross-lente: Sentido <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: La contradicción entre calidad/crecimiento se amplifica por la restricción temporal - no es solo elegir, sino que el tiempo hace ambas opciones progresivamente menos viables

**3. Salud×Replicar <-> Continuidad×Depurar** (cross-lente: Salud <-> Continuidad)
- Modelo: opus (ronda 0, output: v31_best)
- Conexion: La salida del co-fundador técnico hace 6 meses precedió la fuga de 2 devs - patrón de deterioro en cascada del equipo técnico

**4. Continuidad×Conservar <-> Sentido×Frontera** (cross-lente: Continuidad <-> Sentido)
- Modelo: v3.2-chat (ronda 0, output: v31_best)
- Conexion: El runway de 7 meses (Conservar) es la restricción dura que fuerza la contradicción central (Frontera): no hay tiempo suficiente para hacer ambas cosas (estabilizar y pivotar) antes de que se acabe el

**5. Salud×Conservar <-> Continuidad×Captar** (cross-lente: Salud <-> Continuidad)
- Modelo: v3.2-chat (ronda 0, output: v31_best)
- Conexion: El MRR de €12k (Conservar) es insuficiente para cubrir el burn rate de €28k (Captar), creando la pérdida neta que drena el efectivo y define el runway.

## F) Historia de la Celda Mas Disputada

**Output**: 70b_worst
**Celda**: Salud×Depurar
**Nivel final**: 4
**Historial de niveles**: [0, 1, 2, 3, 4]
**Semilla**: sonnet

### Transiciones

- Nivel 0 -> 1 por **sonnet** (ronda -1)
  > patrón de trabajo excesivo
- Nivel 1 -> 2 por **v3.2-chat** (ronda 0)
  > El patrón de trabajo excesivo es identificado como 'una respuesta aprendida que ya no sirve' - esto es una depuración específica de un patrón disfunci
- Nivel 2 -> 3 por **gpt-oss-120b** (ronda 0)
  > El patrón de trabajo excesivo está impulsado por el miedo heredado a un infarto y la presión de ser el principal proveedor.
- Nivel 3 -> 4 por **qwen3-235b** (ronda 0)
  > el agotamiento y estrés son síntomas que deben depurarse al reconocer que el modelo de trabajo actual es insostenible

### Todas las evidencias

- [sonnet, ronda -1] patrón de trabajo excesivo
- [v3.2-chat, ronda 0] El patrón de trabajo excesivo es identificado como 'una respuesta aprendida que ya no sirve' - esto es una depuración específica de un patrón disfunci
- [gpt-oss-120b, ronda 0] El patrón de trabajo excesivo está impulsado por el miedo heredado a un infarto y la presión de ser el principal proveedor.
- [qwen3-235b, ronda 0] el agotamiento y estrés son síntomas que deben depurarse al reconocer que el modelo de trabajo actual es insostenible
- [deepseek-v3.1, ronda 0] El patrón emocional de dedicación laboral excesiva es una respuesta aprendida que ya no sirve
- [deepseek-r1, ronda 0] patrón de trabajo excesivo es respuesta aprendida y obsoleta que daña salud
- [gpt-oss-120b, ronda 4] Se identifican marcadores fisiológicos tempranos (variabilidad de la frecuencia cardíaca reducida, cortisol diurno elevado, alteraciones del sueño) qu

## G) Mente Minima Recomendada

| N modelos | Modelos | Celdas cubiertas | % del total |
|-----------|---------|-----------------|-------------|
| 3 | gpt-oss-120b, minimax-m2.5, qwen3-235b | 42/105 | 40.0% |
| 5 | gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1 | 70/105 | 66.7% |
| 7 | gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1, deepseek-r1, v3.2-reasoner | 80/105 | 76.2% |

**Recomendacion**: 7 modelos capturan 76.2% del resultado: gpt-oss-120b, minimax-m2.5, qwen3-235b, v3.2-chat, deepseek-v3.1, deepseek-r1, v3.2-reasoner

## H) Veredicto: Produce la Mente Distribuida Resultado Cualitativamente Diferente?

### Datos cuantitativos

- Celdas 3+ vs Max Mecanico: +28
- Celdas 3+ vs Mesa Redonda: +12
- Nivel medio vs Max Mecanico: +1.104
- Nivel medio vs Mesa Redonda: +0.723
- Conexiones detectadas (exclusivo de Mente Distribuida): 425
- Puntos ciegos detectados (exclusivo de Mente Distribuida): 239

### Veredicto

**SI, cualitativamente diferente.** La Mente Distribuida supera tanto en metricas cuantitativas (nivel medio, celdas 3+) como en dimensiones que los otros enfoques no capturan: 425 conexiones entre celdas y 239 puntos ciegos detectados. Los modelos exhiben 3 perfiles diferenciados (Conector, Detector de huecos, Sembrador), lo que sugiere especializacion emergente.

### Convergencia

3/5 outputs convergieron (media 4.6 rondas). La convergencia no esta garantizada.

---
*Generado por exp4_3_analyze_mind.py*