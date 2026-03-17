**ESTADO ACTUAL: CRÍTICO. EL SISTEMA TIENE CÁNCER DE ARQUITECTURA.**

OMNI-MIND no es un producto. Es un laboratorio de ideas brillantes con una implementación fracturada. Tienes dos sistemas conviviendo: el **Chief of Staff legacy** (Supabase, 24 agentes, código operativo pero deprecado) y el **Motor vN** (fly.io, diseño teórico, validado parcialmente). Están matándose entre ellos.

Aquí está el roadmap de supervivencia:

---

## 1. QUÉ SE ELIMINA (Cirugía sin anestesia)

**ELIMINAR INMEDIATAMENTE:**
- **Chief of Staff completo**: Está deprecado en el diseño pero consume 6.900 líneas en producción. Es deuda técnica pura. Los 24 agentes específicos, los 9 modos conversacionales y el pipeline dual superficial/profundo se desmantelan. **Justificación**: El Motor v3.3 + Matriz 3L×7F cubren la funcionalidad diagnóstica (§1B). Mantener ambos es esquizofrenia arquitectónica.
- **17 tipos de pensamiento**: Overhead teórico. Los datos de EXP 4.3 muestran que solo 6-7 patrones son usados frecuentemente; el resto son categorías vacías. **Sustituir por**: El campo de gradientes de la Matriz (L2) que ya dirige la ejecución.
- **6 modos conversacionales**: Redundantes con los gradientes. El documento mismo admite que "el Motor no necesita modos, tiene gradientes" (§1B).
- **Reactor v3 (generación conceptual)**: 12% de utilidad vs Reactor v4 (datos reales) según Cogito. Genera preguntas abstractas que no cierran gaps. **Priorizar**: Reactor v4 con telemetría real.
- **Meta-motor y Fábrica de Exocortex autónoma**: Teoría sin validación. La "auto-evolución nivel 3" es ciencia ficción para un sistema que aún no tiene un Gestor funcional.
- **Migración OS "big bang"**: No bloquear el MVP por la migración de 53 agentes. Migrar solo los del pipeline crítico (Motor vN + Gestor).

**REDUCIR:**
- **18 Inteligencias → 6 para el MVP**: Las irreducibles validadas (INT-01 Lógica, INT-02 Computacional, INT-06 Política, INT-08 Social, INT-14 Divergente, INT-16 Constructiva). Las otras 12 son combinaciones o variantes dominio-específicas que se derivarán del Reactor v4 con datos reales.
- **Supabase → fly.io**: Decisión binaria. No mantener ambos. Si fly.io es el futuro, migrar el estado esencial (Matriz, datapoints) y dejar Supabase como read-only archive.

---

## 2. ROADMAP REALISTA (6 meses para MVP vendible)

### FASE 0: Parar el sangrado (Semanas 1-2)
**Objetivo**: Resolver contradicciones arquitectónicas que bloquean todo.

| Tarea | Por qué | Coste | Riesgo |
|-------|---------|-------|--------|
| **Decisión infraestructura** | Elegir: ¿Supabase o fly.io? No ambos. Si se elige fly.io, migrar solo tablas críticas (Matriz, datapoints_efectividad, ejecuciones). | €0 (tiempo) | Alto: Parálisis por análisis |
| **Apagar Chief of Staff** | Desactivar los 24 agentes del Chief en producción. Migrar solo la estigmergia y cola priorizada al Motor vN. | €0 | Medio: Pérdida de funcionalidad temporal |
| **Definir MVP mínimo** | Chat simple (no UI compleja) + Motor vN + 6 INT + Gestor básico. Sin auto-mejora, sin fábrica de exocortex. | €0 | Bajo |

**Entregable**: Sistema monolítico funcional en una sola plataforma.

### FASE 1: El Gestor o la muerte (Meses 1-2)
**Objetivo**: Implementar el Gestor de la Matriz, el componente crítico que falta (§6E).

| Tarea | Dependencias | Coste estimado | Tiempo |
|-------|-------------|----------------|--------|
| **Tablas de efectividad** | fly.io Postgres | €0 | 3 días |
| **Vista materializada** | SQL + índices | €0 | 2 días |
| **Compilador de programas** | Python/FastAPI. Toma una celda (ej: Captar×Salud) y devuelve qué modelo usar (V3.1/R1/GPT-OSS) y qué preguntas incluir. | €0 | 2 semanas |
| **Orquestador OS** | Qwen 235B/Maverick vía API. Asignación modelo→celda empírica (usar Tabla 3 de EXP 4). | ~$50/mes | 1 semana |
| **Pipeline 7 pasos reducido** | Detector huecos → Campo gradientes → Router → Composición → Ejecución (multi-modelo) → Verificación → Registro. | €0 | 3 semanas |

**Validación**: El sistema debe ejecutar un caso tipo "startup con gaps en Captar×Salud" en <40s con coste <$0.35 (OS-first).

**Qué NO incluye**: 
- Evaluador Sonnet (usar V3.2-chat como evaluador si correlación >0.85 vs Sonnet, sino usar Sonnet solo para calibración mensual).
- Reactor v2/v3 (solo v4 con datos reales).
- Auto-mejora autónoma (solo logs para análisis manual).

### FASE 2: Pilotos reales (Meses 3-4)
**Objetivo**: Validar el flywheel y el Reactor v4.

| Piloto | Qué se valida | Coste | Éxito |
|--------|--------------|-------|-------|
| **Pilates (Jesús)** | Telemetría real (reservas, asistencia). Reactor v4 genera preguntas desde datos. ¿Detecta gaps que Jesús no ve? | ~$20/mes tokens | 3 preguntas accionables no obvias |
| **Fisioterapia (mujer)** | Transferencia cross-dominio. ¿Las preguntas de Pilates sobre gestión de agenda aplican aquí? | ~$20/mes | 1 pregunta transferible validada |

**Métricas**:
- Gap medio cerrado por pregunta >0.40 (tasa de efectividad).
- Tiempo de respuesta