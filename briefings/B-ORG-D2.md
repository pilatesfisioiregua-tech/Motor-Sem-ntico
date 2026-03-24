# B-ORG-D2: Deploy Fase 2 — G4 completo + Recompilador

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — sin deploy, Fase 2 solo existe en local
**Dependencia:** B-ORG-F2-01 a F2-04 ejecutados (todos PASS)

---

## QUÉ SE DESPLIEGA

Fase 2 completa: Motor cognitivo G4 (enjambre + compositor + estratega + recompilador).
El sistema pasa de "diagnostica y actúa" a "diagnostica, prescribe, se reconfigura y evoluciona".

## ARCHIVOS NUEVOS A VERIFICAR

Antes de deploy, verificar que estos archivos existen y no están vacíos:

```python
archivos_fase2 = [
    "src/pilates/buscador.py",          # F2-01: reescrito con Motor Gap + Gradiente
    "src/pilates/enjambre.py",           # F2-02: 9 agentes modelo causal
    "src/pilates/compositor.py",         # F2-03: Compositor + Estratega + Orquestador
    "src/pilates/recompilador.py",       # F2-04: autopoiesis
    "src/pilates/collectors.py",         # C1: Instagram + GBP + WA
    "src/pilates/cerebro_organismo.py",  # BRAIN: razonar() para AF1-AF7
    "src/pilates/redsys_pagos.py",       # R1: integración Redsys
    "src/pilates/redsys_router.py",      # R1: endpoints Redsys
]
# Verificar: todos existen y tienen >50 líneas
```

## PASO 1: MIGRACIONES

Ejecutar en orden. Las 018+019 ya deberían estar (D1). Verificar y ejecutar las que falten:

```bash
# Conectar a la DB de fly.io
fly postgres connect -a chief-os-omni-db

# Verificar qué tablas existen
\dt om_*

# Si falta om_bus_senales (018):
# fly postgres connect y ejecutar migrations/018_bus_senales.sql

# Si falta om_telemetria_sistema (019):
# ejecutar migrations/019_telemetria_sistema.sql

# Ejecutar las nuevas:
# 020 — Redsys
\i migrations/020_redsys.sql

# 021 — Enjambre
\i migrations/021_enjambre.sql

# 022 — Config agentes (recompilador)
\i migrations/022_config_agentes.sql

# Verificar
\dt om_redsys*
\dt om_enjambre*
\dt om_config*
```

## PASO 2: CORREGIR DUPLICACIÓN ENJAMBRE EN CRON

El cron actual tiene el enjambre en paso 4b Y G4 en paso 10. G4 ya llama internamente a ejecutar_enjambre(). Hay que:
1. Eliminar el paso 4b (enjambre suelto) del cron
2. Cambiar paso 10 de `ejecutar_g4` a `ejecutar_g4_con_recompilacion`

En `src/pilates/cron.py`, reemplazar:

```python
        # ELIMINAR BLOQUE 4b completo:
        # 4b. Enjambre cognitivo v2 — modelo causal 4 niveles (9 agentes)
        # from src.pilates.enjambre import ejecutar_enjambre
        # enj = await ejecutar_enjambre()
        # log.info(...)

        # REEMPLAZAR paso 10:
        # ANTES:
        #     from src.pilates.compositor import ejecutar_g4
        #     g4 = await ejecutar_g4()
        # DESPUÉS:
        try:
            from src.pilates.recompilador import ejecutar_g4_con_recompilacion
            g4 = await ejecutar_g4_con_recompilacion()
            log.info("cron_semanal_g4_ok",
                     perfil=g4.get("perfil_detectado"),
                     nivel=g4.get("nivel_alcanzado"),
                     recompilados=g4.get("recompilacion", {}).get("configs_aplicadas", 0),
                     tiempo=g4.get("tiempo_total_s"))
        except Exception as e:
            log.error("cron_semanal_g4_error", error=str(e))
```

## PASO 3: AÑADIR ENDPOINTS EN router.py

Añadir al final de `src/pilates/router.py`:

```python
# ============================================================
# G4 — Motor Cognitivo (Enjambre + Compositor + Recompilador)
# ============================================================

@router.post("/sistema/enjambre")
async def sistema_enjambre():
    """Ejecuta enjambre cognitivo: 9 agentes diagnostican INT×P×R."""
    from src.pilates.enjambre import ejecutar_enjambre
    return await ejecutar_enjambre()


@router.post("/sistema/g4")
async def sistema_g4():
    """G4 completa: enjambre + compositor + estratega + orquestador."""
    from src.pilates.compositor import ejecutar_g4
    return await ejecutar_g4()


@router.post("/sistema/g4-recompilar")
async def sistema_g4_recompilar():
    """G4 + recompilación: diagnostica, prescribe y reconfigura agentes."""
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()


@router.post("/sistema/recompilar")
async def sistema_recompilar():
    """Recompilar agentes manualmente con una prescripción dada."""
    from fastapi import Request
    # Espera JSON body con la prescripción
    # POST /pilates/sistema/recompilar {"prescripcion_nivel_1": {...}}
    pass  # TODO: implementar si se necesita trigger manual
```

## PASO 4: ENV VARS EN FLY.IO

Verificar que las env vars de B-ORG-MODELS están configuradas:

```bash
fly secrets list -a chief-os-omni

# Deben existir:
# OPENROUTER_API_KEY (ya existía)
# BRAIN_MODEL=openai/gpt-4o
# REASONING_MODEL=anthropic/claude-sonnet-4.6
# SEQUITO_MODEL=anthropic/claude-sonnet-4.6
# SEQUITO_SYNTH_MODEL=anthropic/claude-sonnet-4.6
# CHAT_MODEL=openai/gpt-4o
# STRATEGY_MODEL=openai/gpt-4o

# Si falta alguna:
fly secrets set BRAIN_MODEL=openai/gpt-4o -a chief-os-omni
fly secrets set REASONING_MODEL=anthropic/claude-sonnet-4.6 -a chief-os-omni
# etc.
```

## PASO 5: DEPLOY

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

## PASO 6: SMOKE TEST (12 endpoints)

```bash
BASE="https://motor-semantico-omni.fly.dev/pilates"

# T1: Enjambre solo (diagnóstico INT×P×R)
curl -s -X POST $BASE/sistema/enjambre | jq '.perfil_detectado, .señales_emitidas'

# T2: G4 completa (enjambre + compositor + estratega)
curl -s -X POST $BASE/sistema/g4 | jq '.perfil_detectado, .nivel_alcanzado'

# T3: G4 + recompilación (autopoiesis)
curl -s -X POST $BASE/sistema/g4-recompilar | jq '.perfil_detectado, .recompilacion.configs_aplicadas'

# T4: Verificar que las configs se guardaron
curl -s -X POST $BASE/sistema/g4-recompilar | jq '.recompilacion.agentes_modificados'

# T5-T8: AF1, AF3, AF-todos, circuito (ya existían, verificar que siguen OK)
curl -s -X POST $BASE/af/conservacion | jq '.total_riesgos'
curl -s -X POST $BASE/af/depuracion | jq '.total_detecciones'
curl -s -X POST $BASE/af/todos | jq '.total_alertas'
curl -s -X POST $BASE/sistema/circuito | jq '.ejecutor.acciones_emitidas'

# T9: Collectors
curl -s -X POST $BASE/collectors | jq '.collectors_activos'

# T10: Buscador (reescrito con Motor Gap)
curl -s -X POST $BASE/buscar | jq '.gaps_identificados'

# T11: Propiocepción
curl -s -X POST $BASE/sistema/propiocepcion | jq '.bus.emitidas'

# T12: Verificar tablas nuevas en DB
fly postgres connect -a chief-os-omni-db -c "SELECT count(*) FROM om_enjambre_diagnosticos; SELECT count(*) FROM om_config_agentes;"
```

## CRITERIOS PASS

```
T1: perfil_detectado no es null + señales >= 7
T2: nivel_alcanzado >= 1 + perfil_detectado no es null
T3: configs_aplicadas >= 1 + agentes_modificados no vacío
T4: agentes_modificados incluye al menos 3 agentes
T5-T8: mismos criterios que D1
T9: collectors_activos >= 0 (sin credenciales = 0, OK)
T10: gaps_identificados >= 0 (sin PERPLEXITY_API_KEY = skip, OK)
T11: bus.emitidas >= 0
T12: tablas existen y aceptan queries

4/4 primeros tests PASS = DEPLOY OK
Si T1-T3 fallan = problema de OPENROUTER_API_KEY o modelo
```

## COSTE POST-DEPLOY

| Componente | Frecuencia | Coste/mes |
|---|---|---|
| AF1-AF7 + Ejecutor + Convergencia (gpt-4o) | 1x/semana | ~$2.50 |
| G4 completa (12 calls sonnet+gpt-4o) | 1x/semana | ~$2.50 |
| Séquito 24 asesores (sonnet) | bajo demanda | ~$1.50 |
| Cockpit + portal + WA (gpt-4o) | diario | ~$3.00 |
| Buscador Perplexity | 1x/semana | ~$1.00 |
| Collectors (APIs gratuitas) | diario | $0 |
| **TOTAL** | | **~$10.50/mes** |

---

## RESULTADO

Tras este deploy, el organismo está **completamente vivo en producción**:
- 7 gomas giran
- Motor cognitivo G4 diagnostica en Nivel 1 (INT×P×R)
- Prescribe en Nivel 1 (qué herramientas cognitivas activar)
- Se recompila a sí mismo (configs dinámicas de agentes)
- Se poda (autófago mensual)
- Se repara (vigía + mecánico cada 15 min)
- Detecta convergencias cross-AF
- Escucha señales externas (collectors + bus)

Jesús solo necesita:
1. Mirar el cockpit
2. Aprobar cambios estructurales (CR1 cuando el recompilador lo pida)
3. El resto es autónomo
