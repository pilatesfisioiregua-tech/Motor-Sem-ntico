# CORPUS UNIFICADO — Motor Semantico ACD
> Documento de continuidad entre sesiones. Fecha: 2026-03-26. Corpus N=1,377.

---

## 1. VISION DE NEGOCIO

OMNI-MIND es una fabrica de agentes IA que operan negocios de forma autonoma. No es un SaaS ni un chatbot: es un equipo de IA completo (CEO humano + todo lo demas agentes).

**Producto: Exocortex Agentico** — cerebro externo para negocios compuesto por agentes especializados que leen tareas, ejecutan de forma autonoma y aprenden de resultados.

### Agentes de Fabrica (construyen el producto)
| # | Agente | Funcion | Estado |
|---|--------|---------|--------|
| 1 | Verificador | Testea todo E2E, encuentra fallos | OPERATIVO |
| 2 | Builder | Lee hallazgos, genera fixes, deploya | OPERATIVO |
| 3 | Investigador | Escanea mercado, competidores | PENDIENTE |
| 4 | Traductor | Traduce/adapta entre dominios | OPERATIVO |

### Agentes de Producto (operan el negocio del cliente)
| # | Agente | Funcion |
|---|--------|---------|
| 1 | Diagnosticador | Analiza salud del negocio (7 funciones vitales) |
| 2 | Predictor | Abandonos, demanda, cashflow |
| 3 | Comunicador | WhatsApp, email, notificaciones |
| 4 | Cobrador | Cargos, recordatorios, planes de pago |
| 5 | Optimizador | Horarios, precios, recursos |
| 6 | Captador | Leads, seguimiento, conversion |
| 7 | Retenedor | Detecta riesgo de baja, actua |

### Modelo de negocio
- **Fase 1** (0-12m): Verticales Pilates/Yoga/Fitness/Clinicas. 149-299 EUR/mes. Meta: 100 clientes.
- **Fase 2** (12-24m): API publica + marketplace de agentes. Revenue share.
- **Fase 3** (24+m): Self-service cualquier negocio. Moat: datos cruzados entre verticales.

### Comunicacion entre agentes
SOLO estigmergia via tabla `marcas_estigmergicas`. Nunca llamadas directas. Como hormigas con feromonas.

---

## 2. VISION DE INGENIERIA LINGUISTICA

### La tesis
Los LLMs generan lenguaje por estadistica (que palabra sigue a cual). El framework ACD analiza lenguaje por estructura (que operacion cognitiva se ejecuto). COMBINADOS producen **Ingenieria Linguistica**: disenar estructuras linguisticas para producir efectos especificos, medibles y reproducibles.

### El pipeline
```
ANALISIS (input):
  Texto -> Perceptor (LLM) -> Estructura ACD -> Razonador (codigo, $0)
  Resultado: 48 dimensiones estructurales del texto

ESTADISTICA (corpus):
  N textos analizados + efecto medido -> correlacion estructura<->efecto
  Resultado: mapa de que estructura produce que efecto

GENERACION (output):
  Efecto deseado -> estructura optima calculada -> LLM guiado por ACD
  Resultado: texto disenado estructuralmente para ese efecto
```

### Aplicaciones clave
- **Marketing/Ventas**: Detectar estructuras que correlacionan con compra, generar emails optimizados.
- **Educacion**: Maximizar comprension del alumno via operaciones cognitivas.
- **Terapia/Coaching**: Prescribir operaciones que producen insight.
- **Politica/Comunicacion**: Mapa de que persuade + deteccion de manipulacion (falacias intencionales).
- **Producto/UX**: Copy optimizado por estructura, no por intuicion.

### Diferenciadores unicos
1. EXPLICA por que un texto funciona (no caja negra)
2. VARIA dimensiones especificas conscientemente
3. DETECTA manipulacion estructural
4. ENSENA a humanos (operaciones concretas, no consejos vagos)
5. MIDE calidad estructural ($0, codigo puro, determinista)

### Pricing API
- Analisis: $0.01/texto (48 dimensiones + diagnostico + score)
- Generacion: $0.05/texto (texto estructuralmente optimizado)
- Ingenieria: $0.10/texto (corpus + efecto objetivo -> estructura optima + texto)
- Dashboard: $99-499/mes

---

## 3. ESPECIFICACION DE AGENTES

### Ciclo de vida
```
IDLE -> LEER_TAREA -> EJECUTAR -> REPORTAR -> IDLE
                        |
                     ESCALAR (si no sabe que hacer)
```

### Interfaz comun
```python
class AgenteBase:
    nombre: str           # Identificador unico
    tipo: str             # fabrica | producto | meta
    sensor: Sensor        # De donde lee
    actuador: Actuador    # Donde escribe

    async def leer_tarea(self) -> Tarea | None
    async def ejecutar(self, tarea: Tarea) -> Resultado
    async def reportar(self, resultado: Resultado)
    async def escalar(self, problema: str)
```

### Fuentes de tareas
- **Tabla `tareas_agente`**: id, agente, tipo (fix/analisis/comunicacion/mejora), prioridad 1-10, payload JSONB, estado.
- **Archivos `tasks/`**: YAML por agente.
- **Marcas estigmergicas**: Reactivo. Un agente deja marca -> otro detecta y actua.

### Flujo Verificador-Builder
```
Verificador -> marca: hallazgo -> Builder lee -> genera fix -> aplica + deploy
            -> marca: fix_aplicado -> Verificador re-verifica -> marca: verificado
```

---

## 4. HALLAZGOS EMPIRICOS (corpus N=1,377)

### 4.1 Correlaciones significativas (51 total, top 10)

| Metrica | Efecto | r | Significativo |
|---------|--------|---|---------------|
| precision_adjetivos | credibilidad | 0.82 | SI |
| explicitud | credibilidad | 0.75 | SI |
| produce_resultado | credibilidad | 0.70 | SI |
| precision_adjetivos | accion | 0.67 | SI |
| precision_adjetivos | persuasion | 0.66 | SI |
| precision_adjetivos | empatia | 0.61 | SI |
| fuerza_verbo | accion | 0.59 | SI |
| explicitud | accion | 0.59 | SI |
| n_vacios | credibilidad | -0.58 | SI |
| agencia | credibilidad | 0.58 | SI |

### 4.2 Correlaciones negativas relevantes

| Metrica | Efecto | r |
|---------|--------|---|
| n_vacios | credibilidad | -0.59 |
| n_causalidades_circulares | credibilidad | -0.58 |
| n_conexiones_rotas | credibilidad | -0.57 |
| n_vacios | accion | -0.56 |
| n_falacias | credibilidad | -0.55 |
| n_vacios | persuasion | -0.54 |
| n_vacios | empatia | -0.51 |
| n_piezas_sueltas | credibilidad | -0.50 |

### 4.3 Metricas NO significativas (ruido)
- `salud` (compuesto): r=0.15-0.24 — NO predice efectos individuales
- `n_lentes`, `n_modos`, `n_relaciones`, `sujeto_concreto`, `resolucion_nivel`: r < 0.12
- `n_falsas_dicotomias`: no significativo
- `n_modos_ocultos`: r < 0.07

**Insight critico**: El score compuesto `salud` NO sirve para predecir efectos. Las metricas granulares (precision_adjetivos, explicitud, fuerza_verbo) son MUCHO mas predictivas.

### 4.4 Operaciones compuestas (109/196 significativas)

| Operacion compuesta | Efecto | r |
|---------------------|--------|---|
| precision_adj x explicitud | credibilidad | 0.84 |
| precision_adj x fuerza_verbo | accion | 0.72 |
| precision_adj x fuerza_verbo | persuasion | 0.71 |
| agencia x explicitud | empatia | 0.68 |

### 4.5 Operaciones cognitivas (Calculo 3)

| Operacion | Efecto | r |
|-----------|--------|---|
| cuantificacion | accion | 0.74 |
| cuantificacion | persuasion | 0.73 |
| cuantificacion | credibilidad | 0.62 |
| urgencia | accion | 0.41 |
| interrogacion | empatia | 0.26 |

**Textos con preguntas**: +22% en TODOS los efectos (N=197 vs 1180).

### 4.6 Validacion 3-Way Debate (GPT vs Gemini vs Claude)
- **Health score convergencia**: 100% (spread <10%)
- **Metricas individuales**: 45% convergencia (necesita estandarizacion de prompts)
- **Conclusion**: El framework captura estructura REAL, no artefactos de modelo.

---

## 5. RECETAS POR EFECTO (valores optimos del corpus)

### Credibilidad (confianza 1.0)
| Ingrediente | Valor optimo | r | Direccion |
|-------------|-------------|---|-----------|
| precision_adjetivos | 0.69 | 0.82 | alto |
| explicitud | 0.67 | 0.75 | alto |
| produce_resultado | 0.94 | 0.70 | alto |
| n_vacios | 1.59 | -0.59 | bajo |
| agencia | 0.75 | 0.58 | alto |

> Ejemplo: "En las ultimas 4 semanas, 8 de tus 12 clientes del grupo de martes han asistido al menos 3 veces. La tasa de cancelacion bajo del 15% al 6%..."

### Accion (confianza 1.0)
| Ingrediente | Valor optimo | r | Direccion |
|-------------|-------------|---|-----------|
| precision_adjetivos | 0.66 | 0.67 | alto |
| fuerza_verbo | 0.76 | 0.59 | alto |
| explicitud | 0.64 | 0.59 | alto |
| n_vacios | 1.66 | -0.56 | bajo |
| produce_resultado | 0.90 | 0.55 | alto |

> Ejemplo: "Carlos, tu plaza del jueves 18:00 esta confirmada. Llega 5 minutos antes, trae toalla y ropa comoda..."

### Persuasion (confianza 1.0)
| Ingrediente | Valor optimo | r | Direccion |
|-------------|-------------|---|-----------|
| precision_adjetivos | 0.65 | 0.66 | alto |
| explicitud | 0.63 | 0.57 | alto |
| fuerza_verbo | 0.75 | 0.57 | alto |
| produce_resultado | 0.91 | 0.55 | alto |
| n_vacios | 1.74 | -0.54 | bajo |

> Ejemplo: "Sofia, tu fisioterapeuta me ha pasado tu informe. Dice que el Pilates terapeutico 2 veces por semana es clave para tu recuperacion..."

### Empatia (confianza 1.0)
| Ingrediente | Valor optimo | r | Direccion |
|-------------|-------------|---|-----------|
| precision_adjetivos | 0.63 | 0.61 | alto |
| explicitud | 0.65 | 0.58 | alto |
| agencia | 0.75 | 0.58 | alto |
| produce_resultado | 0.92 | 0.57 | alto |
| n_causalidades_circulares | 0.08 | -0.52 | bajo |

> Ejemplo: "Entiendo que los ultimos meses han sido complicados. La espalda duele mas cuando dejamos de movernos, verdad?..."

---

## 6. MODELO DE SCORING (siguiente sesion)

### Formula base
```
Score = lentes + acoples + creencias + reglas + funciones + operadores - puntos_ciegos
```

### Conversion a probabilidad
```
P(efecto | estructura) = sigmoid(Score)
```

Los pesos se calibran desde las correlaciones del corpus (empirico, no heuristico).

---

## 7. ARQUITECTURA DEL MOTOR

### Componentes core
| Componente | Tipo | Coste | Funcion |
|------------|------|-------|---------|
| Perceptor | LLM (cualquiera) | ~$0.001 | Extrae 7 dimensiones ACD del texto |
| Razonador | Codigo puro | $0 (<5ms) | 48 detectores, propiedades algebraicas |
| Generador | LLM (cualquiera) | variable | Output guiado + verificacion |
| Corpus engine | Python | $0 | ingest -> analyze -> correlate -> recipes |

### 4 agentes de fabrica
- **Verificador**: Testea E2E, encuentra fallos
- **Builder**: Lee hallazgos, genera fixes, deploya
- **Investigador**: Escanea mercado/competidores
- **Traductor**: Traduce/adapta entre dominios

### Pipeline dual
- **Pipeline A**: Preguntas/apertura (exploracion)
- **Pipeline B**: Estructura/optimizacion (convergencia)

### Multi-modelo
Funciona con GPT, Gemini y Claude (model-agnostic). Los 3 testeados y configurados.

---

## 8. API KEYS

- OpenAI: configurado en .env
- Google/Gemini: configurado en .env
- Anthropic: configurado en .env
- Los 3 testeados y funcionando

---

## 9. UBICACION DE ARCHIVOS

### Core
| Archivo | Descripcion |
|---------|-------------|
| `scripts/core/razonador.py` | Razonador (1,982 lineas, 48 detectores) |
| `scripts/core/perceptor.py` | Perceptor multi-modelo (GPT/Gemini/Claude) |
| `scripts/core/generador.py` | Generador ACD |
| `scripts/core/corpus.py` | Motor de corpus |
| `scripts/core/pipeline_dual.py` | Pipeline dual A+B |
| `scripts/core/benchmark.py` | Benchmark comparativo |
| `scripts/core/agente_real.py` | Base de agentes (real) |

### Agentes
| Archivo | Descripcion |
|---------|-------------|
| `scripts/builder.py` | Agente Builder |
| `scripts/investigador.py` | Agente Investigador |
| `scripts/traductor.py` | Agente Traductor |
| `scripts/fabrica.py` | Orquestador de fabrica |

### Datos
| Archivo | Descripcion |
|---------|-------------|
| `corpus/corpus.jsonl` | 1,377 textos, 130+ categorias, ~4MB |
| `corpus/correlaciones.json` | 51 correlaciones significativas |
| `corpus/recetas.json` | 4 recetas por efecto (credibilidad, accion, persuasion, empatia) |

### Documentacion
| Archivo | Descripcion |
|---------|-------------|
| `docs/VISION_NEGOCIO.md` | Vision de negocio y modelo |
| `docs/VISION_INGENIERIA_LINGUISTICA.md` | Tesis de ingenieria linguistica |
| `docs/AGENTE_SPEC.md` | Especificacion tecnica de agentes |
| `docs/CORPUS_UNIFICADO.md` | Este documento |

---

## 10. PRIORIDADES SIGUIENTE SESION

1. **Implementar modelo de scoring probabilistico con sigmoid** — calibrar pesos desde correlaciones del corpus (reemplazar heuristico por empirico)
2. **Empaquetar como `pip install acd-layer`** — open source del Razonador
3. **Plugin Gmail** para validacion en mundo real
4. **Draft de paper** con datos del corpus (N=1,377, 51 correlaciones, validacion 3-way)

---

## 11. INSIGHTS CLAVE PARA RECORDAR

1. **precision_adjetivos es el predictor #1** de TODOS los efectos (r=0.61-0.82). No es la cantidad de adjetivos (n_cualidades correlaciona negativo), sino su PRECISION.
2. **explicitud es el predictor #2** universal (r=0.57-0.75). Decir las cosas sin ambiguedad.
3. **Los defectos penalizan mas que los aciertos ayudan**: n_vacios, n_causalidades_circulares, n_conexiones_rotas, n_falacias son todos negativos fuertes.
4. **El score compuesto `salud` es inutil** para predecir efectos (r<0.24). Las metricas granulares son las que predicen.
5. **La cuantificacion** (numeros concretos en el texto) es el operador cognitivo mas potente (r=0.62-0.74).
6. **Las preguntas en el texto** producen +22% en todos los efectos.
7. **El framework es model-agnostic**: 3 LLMs distintos convergen al 100% en health score.
