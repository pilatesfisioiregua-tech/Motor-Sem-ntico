# PROMPT CONTINUACIÓN — POST AUDITORÍA COMPLETA

**Fecha:** 23 marzo 2026
**Sesión anterior:** Auditoría completa del codebase con todos los briefings implementados

---

## CONTEXTO

Sesión maratónica de diseño + implementación. Se crearon 15 briefings. Claude Code implementó 12. Se hizo auditoría final del codebase completo (55 agentes + 8 algebraicos + pizarra = 64 piezas).

## QUÉ SE HIZO ESTA SESIÓN

1. **Censo completo de agentes:** 55 agentes en 5 capas (ejecutiva 13, cognitiva 20, sensorial 10, meta 8, generativa 4) + 8 componentes algebraicos + pizarra
2. **Pizarra compartida** (B-ORG-PIZARRA): conciencia colectiva donde cada agente escribe/lee
3. **Clusters P+R** (B-ORG-COG-PR): 7 clusters nuevos (4P + 3R) = 13 total con los 6 INT
4. **Guardián de Sesgos** (B-ORG-GUARDIAN): abogado del diablo post-enjambre
5. **Director Opus** (B-ORG-DIRECTOR): lee MANUAL_DIRECTOR_OPUS.md, escribe prompts D_híbrido
6. **Meta-Cognitivo** (B-ORG-METACOG-INGENIERO): evalúa si el sistema cognitivo funciona + Ingeniero con manos
7. **Evaluador** (B-ORG-EVALUADOR): cierra loop aprendizaje (prescripción semana N vs diagnóstico N+1)
8. **AF5 Identidad** (B-ORG-AF5): AF5 como agente unificado con patrón sensor+cerebro+bus+pizarra
9. **Voz Conectada** (B-ORG-VOZ-CONECTADA): AF5 dispara voz_ciclos con contexto del organismo
10. **Buscadores especializados** (B-ORG-SENS-FULL): 6 tipos con system prompts diferentes
11. **Generativa** (B-ORG-GENERATIVA): huérfanas + cristalizador + semillas + puente séquito
12. **Premium UI** (B-ORG-PREMIUM-UI): diseño "Cerebro Vivo" con paleta Neural Dark + 8 componentes
13. **UNIFY-01** actualizado: LLM percibe (evaluar_funcional con datos reales), código razona
14. **Manual Director:** docs/operativo/MANUAL_DIRECTOR_OPUS.md con álgebra completa en Python dicts

## QUÉ QUEDA POR HACER — B-ORG-POLISH

La auditoría encontró 6 huecos que impiden que el sistema funcione al 100%:

### HUECO 1: Faltan 2 endpoints GET para Premium UI
```
FALTA: GET /organismo/director → lee último resultado del Director (solo query DB)
FALTA: GET /organismo/evaluacion → lee última evaluación (solo query DB)
```
Sin estos, los módulos EstrategiaPanel y EvaluacionPanel del frontend no pueden cargar datos.
~20 líneas cada uno. Código exacto en B-ORG-PREMIUM-UI.md (sección "Endpoints nuevos en router.py").

### HUECO 2: cockpit.py no sabe de los 6 módulos nuevos
En cockpit.py falta:
```python
MODULOS.update({
    "pizarra":        {"nombre": "Pizarra organismo",  "icono": "📋", "endpoint": "/organismo/pizarra"},
    "estrategia":     {"nombre": "Estrategia semana",  "icono": "🎼", "endpoint": "/organismo/director"},
    "evaluacion":     {"nombre": "¿Funcionó?",         "icono": "📊", "endpoint": "/organismo/evaluacion"},
    "feed_cognitivo": {"nombre": "Feed cognitivo",      "icono": "🧠", "endpoint": "/feed?categoria=organismo"},
    "bus":            {"nombre": "Bus señales",          "icono": "📡", "endpoint": "/organismo/bus"},
    "voz_proactiva":  {"nombre": "Voz proactiva",        "icono": "📢", "endpoint": "/voz/propuestas?estado=pendiente"},
})
```
Y en chat_cockpit(), antes de llamar al LLM:
```python
from src.pilates.pizarra import resumen_narrativo
pizarra_resumen = await resumen_narrativo()
# Inyectar en SYSTEM_COCKPIT
```

### HUECO 3: voz_ciclos no acepta contexto_organismo
af5_identidad.py llama `ejecutar_ciclo_completo(contexto_organismo={...})` pero voz_ciclos.py no tiene ese parámetro. Necesita:
- Añadir `contexto_organismo: dict = None` a la firma
- Función `_enriquecer_con_organismo(señales, ctx)` que convierte partituras del Director en señales de contenido
- Código en B-ORG-VOZ-CONECTADA.md (sección "voz_ciclos recibe contexto del organismo")

### HUECO 4: G4 desperdicia $0.05/semana en Sonnet cuando Opus funciona
En recompilador.py `ejecutar_g4_con_recompilacion()`:
- Ejecuta Sonnet recompilación ($0.05) Y DESPUÉS Opus ($0.40)
- Opus sobrescribe las configs de Sonnet
- Solución: Opus primero, Sonnet solo como fallback si Opus falla

### HUECO 5: JSON parsing inconsistente
`director_opus.py` tiene `_parse_json_robusto()` excelente (repara truncamientos).
`metacognitivo.py` lo reutiliza (importa de director_opus).
PERO `evaluador_organismo.py`, `compositor.py`, `enjambre.py`, `guardian_sesgos.py` hacen parsing manual.
Solución: mover `_parse_json_robusto` a un utils.py compartido y usarlo en todos.

### HUECO 6: Sin rate limiting en endpoints Opus
`/acd/director-opus` ($0.40) y `/acd/metacognitivo` ($0.50) sin protección contra doble click.
Solución: semáforo asyncio simple por endpoint.

### MEJORA EXTRA: Evaluador → Director por pizarra directamente
El Evaluador escribe `necesita_de=["COMPOSITOR", "ESTRATEGA"]` pero debería ser `necesita_de=["DIRECTOR_OPUS"]`.
Y en `datos` debería incluir `recomendaciones_director` como campo explícito.

## ARCHIVOS A MODIFICAR

1. `router.py` — añadir 2 GET endpoints (~20 líneas)
2. `cockpit.py` — añadir 6 módulos + chat lee pizarra (~50 líneas)
3. `voz_ciclos.py` — aceptar contexto_organismo + _enriquecer (~40 líneas)
4. `recompilador.py` — Opus primero, Sonnet fallback (~10 líneas)
5. Nuevo `src/pilates/json_utils.py` — mover _parse_json_robusto (~30 líneas)
6. `evaluador_organismo.py`, `compositor.py`, `enjambre.py`, `guardian_sesgos.py` — importar json_utils
7. `evaluador_organismo.py` — necesita_de=["DIRECTOR_OPUS"] + recomendaciones en datos

Total: ~170 líneas de cambios quirúrgicos.

## DESPUÉS DE B-ORG-POLISH

Solo queda B-ORG-PREMIUM-UI (frontend) y B-ORG-D2 (deploy).

## CHECKLIST DEFINITIVO FINAL

```
IMPLEMENTADOS (12):
  ✅ B-ORG-PIZARRA, UNIFY-01, UNIFY-02, COG-PR, GUARDIAN
  ✅ B-ORG-SENS-FULL, GENERATIVA, AF5, EVALUADOR
  ✅ B-ORG-DIRECTOR, METACOG-INGENIERO, VOZ-CONECTADA (parcial)
  ✅ Migraciones 020-024

PENDIENTES (3):
  ❌ B-ORG-POLISH          → 6 arreglos (~170 líneas)
  ❌ B-ORG-PREMIUM-UI      → Frontend premium (3 fases)
  ❌ B-ORG-D2              → Deploy final

CENSO: 55 agentes + 8 algebraicos + pizarra = 64 piezas
COSTE: ~$10.50/mes
OPUS: 3 (Director semanal + Meta-Cognitivo mensual + Ingeniero via briefings)
```
