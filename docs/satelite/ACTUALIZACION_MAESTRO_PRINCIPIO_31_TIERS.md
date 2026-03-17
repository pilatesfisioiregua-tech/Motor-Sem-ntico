# ACTUALIZACIÓN DOCUMENTO MAESTRO — Principio 31 + Arquitectura de Tiers

**Estado:** CR0 — Jesús valida y cierra
**Fecha:** 2026-03-11
**Origen:** Sesión multi-modelo Exp 4 + diseño de enjambres

---

## Añadir a §12 PRINCIPIOS DE DISEÑO

**31. Rápido y profundo no existe.** Existen 5 velocidades para 5 contextos. Intentar profundidad en tiempo real es el error — genera respuestas mediocres con apariencia de profundidad. El sistema elige la cadencia correcta para el momento: reflejo para lo inmediato, batch nocturno para lo profundo. La calidad no se negocia — se agenda.

---

## Añadir a §4 PIPELINE o crear nueva §4B: ARQUITECTURA DE TIERS

### 5 tiers de enjambre: velocidad × profundidad × coste

```
TIER 1 — REFLEJO
  Latencia:     milisegundos
  Coste:        $0
  Enjambre:     ninguno — código puro
  Mecanismo:    Lookup en Matriz precompilada por el Gestor
  Cuándo:       "Este patrón lo he visto 47 veces"
  Ejemplo:      Usuario pregunta horario → tabla precalculada
  Profundidad:  0 (ejecución, no análisis)

TIER 2 — RESPUESTA
  Latencia:     5-15 segundos
  Coste:        $0.01-0.05
  Enjambre:     1 modelo OS barato (GPT-OSS / Qwen3-Coder-Next)
  Mecanismo:    Modelo + programa compilado por el Gestor
  Cuándo:       Interacción normal de conversación
  Ejemplo:      "¿Cómo van las reservas esta semana?"
  Profundidad:  Base (nivel 1-2 de la Matriz)

TIER 3 — ANÁLISIS
  Latencia:     1-5 minutos
  Coste:        $0.10-0.50
  Enjambre:     3-5 modelos en paralelo, cada uno su ángulo
  Mecanismo:    Mini-mesa redonda rápida (1 ronda, sin enriquecimiento)
  Cuándo:       Decisión importante, el usuario puede esperar
  Ejemplo:      "¿Debería abrir sábados?" → 3 modelos × 3 lentes
  Profundidad:  Media (nivel 2-3, algunos insights)

TIER 4 — PROFUNDO
  Latencia:     30-60 minutos
  Coste:        $0.50-2.00
  Enjambre:     Mente distribuida completa (10 modelos, micro-rondas, pizarra)
  Mecanismo:    Exp 4.3 — pizarra compartida con convergencia
  Cuándo:       Batch nocturno. Briefing matutino. Análisis semanal.
  Ejemplo:      Datos del día → 10 modelos procesan a las 2am → briefing a las 8am
  Profundidad:  Alta (nivel 3-4, conexiones cross-celda, puntos ciegos)

TIER 5 — CARTOGRAFÍA
  Latencia:     horas a días
  Coste:        $5-20
  Enjambre:     Exploración completa (18 INTs × composiciones × loops)
  Mecanismo:    Protocolo de exploración 5 tiers (§6B) + mente distribuida
  Cuándo:       Onboarding cliente nuevo. Auditoría anual. Nuevo dominio.
  Ejemplo:      Primer análisis completo de un negocio nuevo
  Profundidad:  Máxima (mapa 3L×7F completo con todas las conexiones)
```

### Cómo el Motor decide qué tier activar

```
Input entra
    ↓
¿Hay respuesta precompilada en la Matriz?
  SÍ → TIER 1 (reflejo, $0, ms)
  NO ↓

¿Es conversación normal (turno de chat, pregunta directa)?
  SÍ → TIER 2 (1 modelo, $0.01, 10s)
  NO ↓

¿El usuario pide análisis o decisión?
  SÍ → TIER 3 (3-5 modelos, $0.30, 3min)
  NO ↓

¿Es proceso batch (no hay usuario esperando)?
  SÍ → TIER 4 (mente distribuida, $1, 45min)
  NO ↓

¿Es exploración de dominio nuevo?
  SÍ → TIER 5 (cartografía completa, $10, horas)
```

### Relación con loops existentes

```
LOOP RÁPIDO (Motor vN):     Tier 1 + Tier 2 (cadencia: segundos)
LOOP MEDIO (análisis):       Tier 3 (cadencia: minutos, bajo demanda)
LOOP LENTO (Gestor):         Tier 4 (cadencia: horas, batch)
LOOP PROFUNDO (Reactores):   Tier 5 (cadencia: días, onboarding/auditoría)
```

### Cada tier tiene su enjambre

| Tier | Modelos típicos | Por qué estos |
|------|----------------|---------------|
| 1 | Ninguno (código puro) | Velocidad máxima, coste cero |
| 2 | GPT-OSS o Qwen3-Coder-Next | Baratos, rápidos, suficientes para respuesta directa |
| 3 | V3.2 Chat + Cogito + R1 | Balance profundidad/velocidad, cada uno aporta ángulo diferente |
| 4 | 10 modelos OS (pizarra Exp 4.3) | Máxima diversidad de perspectivas, convergencia por micro-rondas |
| 5 | 10 modelos + composiciones + loops | Todo el arsenal, exploración exhaustiva |

Los modelos de cada tier se configuran en el Gestor (no hardcoded). El Gestor compila el enjambre óptimo por tier basándose en datos de efectividad (Principio 23: el Gestor compila, los consumidores ejecutan).

---

## Tabla de cambios para §0

| Cambio | Origen | Sección |
|--------|--------|---------|
| **Principio 31: Rápido y profundo no existe. 5 velocidades para 5 contextos.** | Sesión 11-mar | §12 |
| **5 tiers de enjambre: reflejo / respuesta / análisis / profundo / cartografía** | Sesión 11-mar | §4B (nueva) |
| **Mente distribuida (pizarra) como primitiva de Tier 4** | Sesión 11-mar (Exp 4.3) | §4B, §6E |
| **Mesa redonda de acumulación como alternativa a evaluación ciega** | Sesión 11-mar (Exp 4) | §6B |
| **Prompts especializados por modelo según fortaleza empírica** | Sesión 11-mar (Exp 4.1) | §6B |
| **Sintetizador como paso final de la mente distribuida** | Sesión 11-mar (Exp 4.2) | §4B |
