# PROMPT SIGUIENTE SESIÓN — Post B-PIL-20 + Agentes de Canal

**Fecha:** 22 marzo 2026
**Contexto:** Sesión anterior completó el Bloque Voz completo (B-PIL-20a→20e)

---

## ESTADO ACTUAL

### Bloque Voz (B-PIL-20) — COMPLETO

| Sub-briefing | Estado | Commit | Qué hace |
|---|---|---|---|
| 20a | ✅ Desplegado | — | 9 tablas + seeds (identidad, IRC 5 canales, PCA 3 segmentos, 2 competidores) + diagnóstico cruzado |
| 20b | ✅ Desplegado | be42e94 | Motor Tridimensional: IRC × Matriz × PCA → estrategia + calendario semanal vía LLM |
| 20c | ✅ Desplegado | 02462f5 | Arquitecto de Presencia: perfiles completos por canal (WA, Google, IG, FB) vía LLM |
| 20d | ✅ Desplegado | 29b41b1 | 5 Ciclos (ESCUCHAR→PRIORIZAR→PROPONER→EJECUTAR→APRENDER) + ISP automático + telemetría + sección Voz en briefing |
| 20e | 📄 Listo para ejecutar | — | Cockpit tools Voz (6 tools) + cron (diaria 06:00 + semanal lunes 07:00) + endpoints manuales cron |

**ACCIÓN INMEDIATA:** Ejecutar B-PIL-20e con Claude Code. Briefing en `motor-semantico/briefings/B-PIL-20e.md`.

### Dato importante de 20d
El IRC de WhatsApp bajó de 0.82 (seed estimado) a un valor recalculado con telemetría real. El ciclo APRENDER funciona: datos reales reemplazan estimaciones automáticamente.

### Bug conocido (resuelto en 20a)
asyncpg devuelve JSONB como string en vez de dict. Se resolvió con helper `_jparse()` en `voz_identidad.py`. Tener en cuenta para código futuro.

---

## SIGUIENTE OBJETIVO: AGENTES DE CANAL + INTELIGENCIA DE AUDIENCIA

### Concepto (discutido en sesión, CR0 pendiente)

Jesús quiere evolucionar el Bloque Voz de "generar propuestas que Jesús ejecuta manualmente" a "agentes autónomos por canal que ejecutan, leen feedback, y aprenden". La clave diferencial: **los agentes tienen memoria de negocio** — saben quién es cada persona (clienta actual, ex, lead, desconocida) cruzando con `om_clientes`.

#### 3 capas del diseño:

**Capa 1 — Agentes de canal (ejecución):**
Un agente por canal (WA, IG, Google, FB) que sabe publicar, responder, leer métricas. Cada agente accede a: identidad, estrategia activa, PCA, y la base de datos de clientes para personalizar respuestas.

**Capa 2 — Enriquecimiento cruzado (datos):**
Cada interacción en cualquier canal enriquece el perfil del cliente en la DB. Si María comenta en IG, se registra en su ficha. Si Pedro abre WA pero no responde, se sabe. Los datos de audiencia agregados (Meta Insights) calibran el PCA automáticamente.

**Capa 3 — Inteligencia de expansión (estrategia):**
Para captar nuevos perfiles: definir segmento → analizar Capa A (¿hay demanda?) + Capa C (¿qué consume ese perfil?) + datos internos (¿tenemos capacidad?) → generar estrategia dirigida → agentes ejecutan → miden → retroalimentan.

#### Cruce con ACD:
Los agentes usan el vector lentes + estado ACD + posición matricial para decidir el ángulo de cada interacción. Ejemplo: clienta actual en riesgo de abandono (Capa B) comenta en IG → agente responde con tono de "retención + confianza" (posición salud×conservar) usando el lenguaje del PCA.

#### Matching clientes ↔ redes:
- **Directo:** Teléfono (WA) / nombre+email (IG DM, Google reseñas) → cruzar con `om_clientes`
- **Agregado:** Meta Audience Insights + IG Graph → perfil demográfico de audiencia → calibrar PCA
- **Expansión:** Definir nuevo target → analizar con SparkToro + Meta Insights → diseñar contenido dirigido

### Bloqueantes operativos (Jesús debe resolver)

| Trámite | Para qué | Tiempo estimado |
|---|---|---|
| **Cuenta WhatsApp Business API** (Meta Cloud API) | Agente WA: enviar, recibir, webhooks, métricas | 1-2 semanas |
| **App Meta (Facebook Developer)** | Agente IG + FB: publicar, leer, responder. Permisos: pages_manage_posts, instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_messages | 1-3 semanas |
| **Google Business Profile API** | Agente Google: reseñas, posts, métricas, Q&A | 1-2 semanas |

**Sin estas credenciales no se pueden escribir briefings ejecutables** (no hay tests PASS/FAIL posibles).

### Plan propuesto (CR0)

1. Ejecutar B-PIL-20e (terminar Bloque Voz base)
2. Jesús inicia los 3 trámites de APIs en paralelo
3. Escribir documento de diseño tipo B2.8 para Agentes de Canal (diseño conceptual, no código)
4. Cuando llegue la primera API aprobada (probablemente WA) → primer briefing ejecutable de agente

---

## ARCHIVOS CLAVE PARA CONTEXTO

Leer estos archivos para entender el estado actual:

```
# Bloque Voz — código desplegado
motor-semantico/src/pilates/voz_identidad.py    — Seeds + consultas + diagnóstico
motor-semantico/src/pilates/voz_estrategia.py   — Motor Tridimensional
motor-semantico/src/pilates/voz_arquitecto.py   — Arquitecto de Presencia
motor-semantico/src/pilates/voz_ciclos.py       — 5 Ciclos + ISP + Telemetría

# Briefing pendiente de ejecutar
motor-semantico/briefings/B-PIL-20e.md           — Cockpit + Cron

# Documento fuente del Bloque Voz
docs/producto/B2_8_BLOQUE_VOZ_PRESENCIA_INTELIGENTE_v3.md

# Cockpit actual
motor-semantico/src/pilates/cockpit.py

# Router con todos los endpoints
motor-semantico/src/pilates/router.py
```

---

## QUÉ HACER EN LA SIGUIENTE SESIÓN

**Opción A (si Jesús aún no ha ejecutado 20e):**
→ Ejecutar 20e con Claude Code. Verificar V1-V12.

**Opción B (si 20e está desplegado y Jesús quiere avanzar con Agentes):**
→ Escribir documento de diseño B2.9 (o similar) para Agentes de Canal con las 3 capas.
→ Incluir: matching clientes↔redes, enriquecimiento bidireccional, uso de ACD para personalizar, inteligencia de expansión de target.
→ NO escribir briefings de código hasta tener al menos 1 API aprobada.

**Opción C (si Jesús quiere trabajar en otra cosa):**
→ Consultar INDICE_VIVO.md para ver prioridades pendientes.
→ Candidatos: ACD Fase 2, Code OS fly.io migration, consolidación docs Pilates.
