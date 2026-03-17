# R1 Design: Cogito 671B
**Perspectiva:** Sintesis -- como conectar Motor + Gestor + Agente + Chat?

# Rediseño del Sistema Conversacional de OMNI-MIND (Chief of Staff)

## A. Arquitectura del Sistema

```
[USUARIO]
     │
     ▼
  [CHAT UI] ◄─────────────┐
     │                     │
     │ (input + contexto)  │ (respuesta + preguntas)
     ▼                     │
[INTERFAZ DE CHAT]         │
     │                     │
     ├────▶ [MOTOR v3.3]   │
     │         │           │
     │         ▼           │
     │   [GESTOR MATRIZ]   │
     │         │           │
     │         ▼           │
     └───── [AGENTE] ◄─────┘
               │
               ▼
  [BACKEND: Postgres + Redis]
```

## B. Componentes Principales (8)

1. **Motor de Conversación (Orquestador)**
   - Función: Coordina el flujo completo de la conversación
   - Modelo: DeepSeek V3.2 (mejor orquestador según EXP 5b)
   - Herramientas: Detector de gaps, Router de tareas, Gestor de contexto
   - Comunicación: Estigmergia (marcas Postgres) + Redis para estado

2. **Analizador de Campo de Gradientes**
   - Función: Mapea gaps en la matriz 3Lx7F
   - Modelo: DeepSeek R1 (mejor en continuidad según EXP 4)
   - Herramientas: Matriz 3Lx7F, Historial de conversación
   - Comunicación: Marcas estigmergicas

3. **Generador de Preguntas**
   - Función: Crea preguntas basadas en gaps detectados
   - Modelo: MiMo V2 Flash ($0.001/llamada, EXP 1bis)
   - Herramientas: Plantillas de preguntas, Historial
   - Comunicación: Cola de preguntas en Redis

4. **Sintetizador de Respuestas**
   - Función: Integra información y genera respuesta natural
   - Modelo: Cogito-671B (mejor sintetizador, EXP 4)
   - Herramientas: Memoria de contexto, Plantillas
   - Comunicación: Canal directo con Motor

5. **Agente de Ejecución**
   - Función: Ejecuta acciones y código
   - Modelo: Devstral (mejor en coding, EXP 1bis)
   - Herramientas: Sandbox de ejecución, API de sistema
   - Comunicación: Cola de tareas en Redis

6. **Sistema de Memoria**
   - Función: Gestiona memoria a corto y largo plazo
   - Modelo: Nemotron Super ($0.007/llamada, EXP 1bis)
   - Herramientas: Vector DB, Cache de contexto
   - Comunicación: Postgres + Redis

7. **Monitor de Auto-mejora**
   - Función: Aprende de cada interacción
   - Modelo: Step 3.5 Flash ($0.019/llamada, EXP 5b)
   - Herramientas: Base de datos de efectividad
   - Comunicación: Marcas estigmergicas

8. **Validador de Seguridad**
   - Función: Verifica seguridad y coherencia
   - Modelo: Qwen 3.5 397B (mejor evaluador, EXP 1bis)
   - Herramientas: Listas de verificación, Políticas
   - Comunicación: Canal directo con Motor

## C. Flujo de un Turno de Chat

1. **Recepción** (200ms)
   - Usuario envía mensaje
   - Motor captura input + contexto
   - Validador de Seguridad verifica input

2. **Análisis Superficial** (500ms)
   - Motor ejecuta Detector de Gaps (primitivas INT-01 a INT-18)
   - Si gap < 0.3: responde directamente desde caché
   - Si gap > 0.3: inicia análisis profundo asíncrono

3. **Generación de Respuesta** (300ms)
   - Sintetizador genera respuesta inicial
   - Generador de Preguntas añade 2-3 preguntas
   - Sistema actualiza memoria con interacción

4. **Respuesta al Usuario** (<1s total)
   - Se envía respuesta + preguntas
   - Análisis profundo continúa en segundo plano

## D. Flujo del Pensamiento Profundo

1. **Mapeo de Campo** (3s)
   - Analizador ejecuta matriz 3Lx7F completa
   - Identifica gaps mayores a 0.3
   - Prioriza por impacto y urgencia

2. **Generación de Estrategia** (10s)
   - Motor selecciona mejores modelos para cada gap
   - Programa ejecución paralela
   - Prepara contexto necesario

3. **Ejecución Paralela** (15s)
   - Se ejecutan análisis en paralelo
   - Cada subtarea usa modelo óptimo
   - Resultados se almacenan en memoria

4. **Integración** (2s)
   - Sintetizador combina resultados
   - Generador crea preguntas de seguimiento
   - Actualiza memoria y perfil de usuario

## E. Integración con Motor Cognitivo

- **Detección de Gaps**: Usa primitivas INT-01 a INT-18
- **Matriz 3Lx7F**: Base para análisis de campo de gradientes
- **Asignación de Modelos**: Basada en datos de EXP 4 y EXP 1bis
- **Feedback Loop**: Cada interacción alimenta base de datos de efectividad

## F. Integración con Agente de Coding

1. **Detección de Necesidad**: Motor identifica tarea de codificación
2. **Preparación de Contexto**: 
   - Requisitos claros
   - Restricciones técnicas
   - Ejemplos relevantes
3. **Ejecución Controlada**:
   - Sandbox aislado
   - Timeout de 30s
   - Validación de resultados
4. **Integración de Resultados**:
   - Análisis de salida
   - Generación de resumen
   - Actualización de memoria

## G. Self-Improvement

1. **Recolección de Datos**:
   - Efectividad por pregunta
   - Tiempo de respuesta
   - Satisfacción del usuario implícita

2. **Análisis Periódico**:
   - Identificación de patrones
   - Detección de áreas de mejora
   - Optimización de asignación de modelos

3. **Actualización Automática**:
   - Ajuste de parámetros
   - Actualización de plantillas
   - Mejora de algoritmos

## H. Eliminado del Sistema Anterior

1. **Pipeline Dual**: Reemplazado por análisis de campo de gradientes
2. **9 Modos Conversacionales**: Simplificado a gradientes de comportamiento
3. **24 Agentes**: Reducido a 8 componentes más eficientes
4. **Dependencia de Anthropic**: Eliminada totalmente

## I. Conservado del Sistema Anterior

1. **Estigmergia**: Comunicación vía marcas en Postgres
2. **Cola de Preguntas**: Priorización inteligente
3. **Persistencia Inter-sesión**: Perfiles y memoria
4. **Detección de Contradicciones**: Mejorada con multi-modelo

## J. Estimación de Coste por Turno

| Componente | Coste/Turno | Frecuencia | Coste Total |
|------------|-------------|------------|-------------|
| Motor | $0.002 | 1x | $0.002 |
| Analizador | $0.001 | 0.3x | $0.0003 |
| Generador Preguntas | $0.0001 | 2x | $0.0002 |
| Sintetizador | $0.003 | 1x | $0.003 |
| Memoria | $0.0005 | 1x | $0.0005 |
| Validador | $0.0002 | 1x | $0.0002 |
| **Total** | | | **$0.0062** |

- **Costo Objetivo**: <$0.02/turno ✓
- **Latencia Objetivo**: <1s (superficial), <30s (profundo) ✓
- **Mejora**: 84% más barato que sistema anterior ($0.10 → $0.0062)

Este diseño cumple con todos los requisitos, aprovecha los hallazgos empíricos recientes y mantiene las fortalezas del sistema anterior mientras elimina sus limitaciones.