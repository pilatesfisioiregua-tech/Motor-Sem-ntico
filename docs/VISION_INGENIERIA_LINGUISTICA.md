# Visión: Ingeniería Lingüística — ACD + LLM + Estadística

## La tesis

Los LLMs actuales generan lenguaje por estadística (qué palabra sigue a cuál).
El framework ACD analiza lenguaje por estructura (qué operación cognitiva se ejecutó).

COMBINADOS producen algo nuevo: **Ingeniería Lingüística** — la capacidad de
DISEÑAR estructuras lingüísticas para producir efectos específicos, medibles
y reproducibles.

## El pipeline

```
ANÁLISIS (input):
  Texto → Perceptor (LLM) → Estructura ACD → Razonador (código, $0)
  Resultado: 48 dimensiones estructurales del texto

ESTADÍSTICA (corpus):
  N textos analizados + efecto medido → correlación estructura↔efecto
  Resultado: mapa de qué estructura produce qué efecto

GENERACIÓN (output):
  Efecto deseado → estructura óptima calculada → LLM guiado por ACD
  Resultado: texto diseñado estructuralmente para ese efecto
```

## Aplicaciones

### Marketing / Ventas
- Analizar 1000 emails de venta + tasa conversión
- Detectar qué estructuras correlacionan con compra
- Generar emails con esas estructuras → +X% conversión

### Educación
- Analizar 1000 explicaciones + comprensión del alumno
- Detectar qué operaciones maximizan comprensión
- Generar explicaciones con esas operaciones → mejor aprendizaje

### Terapia / Coaching
- Analizar N sesiones + cambio del paciente
- Detectar qué intervenciones (qué operaciones) producen insight
- Prescribir "ejecutar esta operación en este momento"

### Política / Comunicación
- Analizar discursos + efecto en audiencia (votos, encuestas, engagement)
- Mapa: qué falacias persuaden, qué cuantificación da credibilidad
- Alerta ética: también detecta MANIPULACIÓN (falacias intencionales)

### Producto / UX
- Analizar N textos de producto + engagement usuario
- Detectar qué estructura de copy produce acción
- Generar copy optimizado por estructura (no por intuición)

## Lo que ningún otro sistema puede hacer

1. EXPLICAR por qué un texto funciona (no caja negra)
2. VARIAR conscientemente dimensiones específicas (más persuasión, menos falacias)
3. DETECTAR manipulación estructural (falacias intencionales)
4. ENSEÑAR a humanos a comunicar mejor (operaciones concretas, no consejos vagos)
5. MEDIR calidad estructural ($0, código puro, determinista)

## Modelo de negocio

### API de Análisis: $0.01/texto
- Input: texto → Output: 48 dimensiones + diagnóstico + score

### API de Generación: $0.05/texto
- Input: instrucción + efecto deseado → Output: texto estructuralmente optimizado

### API de Ingeniería: $0.10/texto
- Input: corpus + efecto objetivo → Output: estructura óptima + texto generado

### Dashboard de Ingeniería: $99-499/mes
- Analizar tus comunicaciones
- Ver qué estructuras usas
- Optimizar para el efecto que quieres
- A/B testing estructural (no solo contenido)

## Estado actual

- [x] Perceptor (extrae estructura ACD en 1 llamada LLM)
- [x] Razonador v3 (48 detectores, código puro, $0)
- [x] Generador ACD (guía al LLM + verifica output)
- [x] Benchmark (LLM+ACD gana 80% de casos, +31% mejora salud)
- [x] 13 agentes reales conectados al pipeline
- [ ] Corpus de análisis estadístico
- [ ] Mapa estructura→efecto
- [ ] Dashboard de ingeniería

## La frase

"No es un LLM más inteligente. Es un LLM que SABE por qué dice lo que dice."
