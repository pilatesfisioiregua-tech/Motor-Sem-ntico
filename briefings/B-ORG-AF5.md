# B-ORG-AF5: AF5 Identidad/Voz como agente unificado

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — AF5 es la función META (6 INTs dedicadas) pero es el único AF sin patrón sensor+cerebro+bus
**Modelo:** gpt-4o nivel 1 (como los demás AF, config dinámica via Director Opus)
**Dependencia:** B-ORG-PIZARRA + B-ORG-UNIFY-01

---

## EL HUECO

Los 7 AF siguen todos el mismo patrón EXCEPTO AF5:

```python
# AF1, AF2, AF3, AF4, AF6, AF7 — todos:
async def ejecutar_afX():
    pizarra = await leer_relevante("AFX")        # Lee pizarra
    datos = await _detectar_XXX()                  # Sensor
    razonamiento = await razonar("AFX", ...)       # Cerebro con config dinámica
    await emitir("PRESCRIPCION", "AFX", ...)       # Bus
    await escribir(agente="AFX", ...)              # Pizarra

# AF5 — disperso en 7 archivos:
# voz.py, voz_ciclos.py, voz_estrategia.py, voz_identidad.py,
# voz_arquitecto.py, voz_reactivo.py, wa_respuestas.py
# Ninguno tiene ejecutar_af5(). Ninguno lee/escribe pizarra.
# Ninguno usa cerebro_organismo.razonar() con config dinámica.
```

Esto significa que:
1. El Director Opus no puede reconfigurar la inteligencia de AF5
2. AF5 no escribe en la pizarra → los demás AF no saben qué dice sobre identidad
3. AF5 no lee la pizarra → no sabe qué detectaron los demás AF

F5 es la función META más importante (6 inteligencias dedicadas: INT-03, 06, 08, 12, 15, 17).
Sin AF5 unificado, el organismo no tiene agente de identidad.

## LA SOLUCIÓN

Crear `af5_identidad.py` con el patrón estándar AF. NO reescribe los 7 archivos voz — los ORQUESTA.

```
af5_identidad.py (NUEVO)
  ├── _detectar_gaps_identidad()     ← Sensor: lee de voz_identidad, voz_estrategia, voz_ciclos
  ├── ejecutar_af5()                 ← Orquesta: sensor + cerebro + bus + pizarra
  └── usa cerebro_organismo.razonar("AF5", ...) con config dinámica del Director

Los 7 archivos voz_* siguen existiendo como IMPLEMENTACIÓN.
AF5 es la INTELIGENCIA que los orquesta.
```

## ARCHIVO A CREAR

`src/pilates/af5_identidad.py`

## CÓDIGO

```python
"""AF5 Identidad/Frontera — Agente funcional: definir qué es y qué no es el negocio.

F5 es la función META más importante (6 INTs dedicadas).
Orquesta los 7 archivos voz_* existentes como sensor,
añade cerebro con config dinámica del Director Opus,
y conecta al bus + pizarra.

Detecciones:
  1. Gap identidad declarada vs percibida: ¿lo que dice que es coincide con lo que hace?
  2. Canales sin coherencia: ¿el mensaje en WA = mensaje en Instagram = mensaje en clase?
  3. Diferenciación no articulada: ¿EEDAP está documentado como diferenciador o es implícito?
  4. Identidad amenazada: ¿algún cambio externo (competencia, regulación) cuestiona la identidad?
  5. Propuesta de valor no comunicada: ¿los clientes saben POR QUÉ este estudio y no otro?

Ejecuta semanalmente. Lee de voz_* como sensor. Razona con cerebro dinámico.
Emite al bus. Escribe en pizarra.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF5"

INSTRUCCION_AF5 = """Analiza la IDENTIDAD del negocio: qué dice que es, qué hace realmente, y qué perciben los clientes.

Para gap identidad declarada vs real: ¿La propuesta de valor dice "Pilates terapéutico"
pero el 80% de las clases son fitness genérico? Eso es un gap F5.

Para coherencia de canales: ¿El tono en WhatsApp es profesional pero en Instagram es casual?
¿El briefing semanal habla de diferenciación pero las acciones son descuentos?

Para diferenciación no articulada: El método EEDAP puede ser un diferenciador POTENTE
pero si no está documentado ni comunicado, no existe para los clientes.

Para identidad amenazada: ¿Hay un nuevo estudio de Pilates en Logroño?
¿Una cadena de fitness ofrece Pilates a mitad de precio?

IMPORTANTE: F5 no es marketing. F5 es IDENTIDAD — saber qué eres y qué no eres.
La frontera entre lo que haces y lo que NO haces es tan importante como lo que haces.
Si no hay frontera clara, el negocio se diluye."""


async def _detectar_gaps_identidad() -> dict:
    """Sensor de AF5: recopila datos de identidad de múltiples fuentes."""
    pool = await get_pool()
    detecciones = []

    async with pool.acquire() as conn:
        # 1. Identidad declarada (voz_identidad)
        identidad = await conn.fetchrow("""
            SELECT propuesta_valor, diferenciadores, tono, publico_objetivo,
                   valores, anti_valores
            FROM om_voz_identidad WHERE tenant_id=$1
        """, TENANT)

        tiene_identidad = identidad and identidad.get("propuesta_valor")
        if not tiene_identidad:
            detecciones.append({
                "tipo": "identidad_no_definida",
                "severidad": "alta",
                "detalle": "No hay propuesta de valor definida. El negocio no sabe (o no ha articulado) qué es.",
            })

        # 2. Estrategia de voz actual
        estrategia = await conn.fetchrow("""
            SELECT foco_principal, calendario, created_at
            FROM om_voz_estrategia WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        if not estrategia:
            detecciones.append({
                "tipo": "sin_estrategia_comunicacion",
                "severidad": "media",
                "detalle": "No hay estrategia de comunicación activa. El negocio no comunica su identidad.",
            })

        # 3. Coherencia canales (IRC)
        try:
            canales = await conn.fetch("""
                SELECT canal, irc_score FROM om_voz_canales
                WHERE tenant_id=$1 ORDER BY irc_score DESC
            """, TENANT)
            if canales:
                scores = [c["irc_score"] for c in canales if c["irc_score"]]
                if scores and max(scores) - min(scores) > 0.4:
                    detecciones.append({
                        "tipo": "canales_desbalanceados",
                        "severidad": "media",
                        "detalle": f"Canales con IRC muy desigual: max={max(scores):.2f}, min={min(scores):.2f}. "
                                   "Puede indicar mensaje inconsistente entre canales.",
                        "canales": [dict(c) for c in canales],
                    })
        except Exception:
            pass

        # 4. ADN del negocio (diferenciación documentada)
        adn_count = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true",
            TENANT) or 0

        if adn_count == 0:
            detecciones.append({
                "tipo": "adn_no_documentado",
                "severidad": "alta",
                "detalle": "0 principios ADN documentados. El método EEDAP no está articulado como diferenciador.",
            })
        elif adn_count < 5:
            sin_contraejemplo = await conn.fetchval("""
                SELECT count(*) FROM om_adn
                WHERE tenant_id=$1 AND activo=true
                AND (contra_ejemplos IS NULL OR contra_ejemplos = '[]'::jsonb)
            """, TENANT) or 0
            if sin_contraejemplo > adn_count / 2:
                detecciones.append({
                    "tipo": "adn_sin_fronteras",
                    "severidad": "media",
                    "detalle": f"{sin_contraejemplo}/{adn_count} principios ADN sin contra-ejemplos. "
                               "Los principios sin límites no definen identidad — son declaraciones vacías.",
                })

        # 5. Tensiones que afectan identidad
        try:
            tensiones_identidad = await conn.fetch("""
                SELECT tipo, descripcion, severidad FROM om_voz_tensiones
                WHERE tenant_id=$1 AND resuelta=false
                AND (tipo ILIKE '%identidad%' OR tipo ILIKE '%posicion%'
                     OR tipo ILIKE '%compet%' OR tipo ILIKE '%diferenc%')
            """, TENANT)
            for t in tensiones_identidad:
                detecciones.append({
                    "tipo": "tension_identidad",
                    "severidad": t["severidad"] or "media",
                    "detalle": f"Tensión abierta: {t['tipo']} — {t['descripcion'][:100]}",
                })
        except Exception:
            pass

        # 6. Feedback de clientes sobre identidad (WA)
        try:
            hace_4sem = date.today() - timedelta(weeks=4)
            menciones_identidad = await conn.fetchval("""
                SELECT count(*) FROM om_mensajes_wa
                WHERE tenant_id=$1 AND direccion='entrante'
                AND created_at > $2
                AND (contenido ILIKE '%diferent%' OR contenido ILIKE '%especial%'
                     OR contenido ILIKE '%unic%' OR contenido ILIKE '%por que%'
                     OR contenido ILIKE '%otro sitio%')
            """, TENANT, hace_4sem) or 0

            if menciones_identidad == 0:
                detecciones.append({
                    "tipo": "clientes_no_mencionan_diferenciacion",
                    "severidad": "baja",
                    "detalle": "0 menciones de diferenciación en mensajes WA en 4 semanas. "
                               "Los clientes no perciben (o no articulan) qué hace diferente a este estudio.",
                })
        except Exception:
            pass

    return {
        "identidad_declarada": dict(identidad) if identidad else None,
        "tiene_identidad": tiene_identidad,
        "adn_count": adn_count,
        "tiene_estrategia": bool(estrategia),
        "detecciones": detecciones,
    }


async def ejecutar_af5() -> dict:
    """Ejecuta AF5 Identidad: sensor + cerebro + bus + pizarra.

    Sigue el MISMO patrón que AF1-AF7.
    """
    log.info("af5_inicio")

    # 1. LEER PIZARRA — qué saben los demás
    from src.pilates.pizarra import leer_relevante, leer_conflictos
    pizarra = await leer_relevante("AF5")
    conflictos = await leer_conflictos("AF5")

    # Construir contexto de pizarra para el cerebro
    pizarra_str = ""
    if pizarra:
        pizarra_str = "\n\nLO QUE LOS DEMÁS AGENTES DETECTARON:\n"
        for entry in pizarra:
            pizarra_str += f"- {entry['agente']}: {entry.get('detectando', '')} → {entry.get('accion_propuesta', '')}\n"
    if conflictos:
        pizarra_str += "\n⚡ CONFLICTOS CONMIGO:\n"
        for c in conflictos:
            pizarra_str += f"- {c['agente']}: {c.get('accion_propuesta', '')}\n"

    # 2. SENSOR
    datos_sensor = await _detectar_gaps_identidad()

    # 3. CEREBRO (config dinámica del Director Opus)
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="AF5",
        funcion="F5 Identidad/Frontera",
        datos_detectados=datos_sensor,
        instruccion_especifica=INSTRUCCION_AF5 + pizarra_str,
        nivel=1,
    )

    # 4. EMITIR AL BUS
    from src.pilates.bus import emitir
    alertas_emitidas = 0

    for accion in razonamiento.get("acciones", []):
        try:
            await emitir("PRESCRIPCION", ORIGEN, {
                "funcion": "F5",
                "accion": accion.get("accion", ""),
                "prioridad": accion.get("prioridad", 4),
                "impacto": accion.get("impacto", ""),
                "esfuerzo": accion.get("esfuerzo", ""),
                "interpretacion": razonamiento["interpretacion"],
            }, prioridad=accion.get("prioridad", 4))
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af5_bus_error", error=str(e))

    if razonamiento.get("alerta_critica"):
        try:
            await emitir("ALERTA", ORIGEN, {
                "funcion": "F5",
                "alerta_critica": razonamiento["alerta_critica"],
                "urgente": True,
            }, prioridad=1)
            alertas_emitidas += 1
        except Exception:
            pass

    # 5. ESCRIBIR EN PIZARRA
    from src.pilates.pizarra import escribir
    await escribir(
        agente="AF5",
        capa="ejecutiva",
        estado="completado",
        detectando=f"{len(datos_sensor['detecciones'])} gaps de identidad. "
                   f"ADN: {datos_sensor['adn_count']} principios. "
                   f"Identidad definida: {'sí' if datos_sensor['tiene_identidad'] else 'NO'}.",
        interpretacion=razonamiento.get("interpretacion", ""),
        accion_propuesta=razonamiento.get("acciones", [{}])[0].get("accion", "") if razonamiento.get("acciones") else "",
        necesita_de=["AF3"] if any(d["tipo"] == "adn_sin_fronteras" for d in datos_sensor["detecciones"]) else [],
        confianza=razonamiento.get("acciones", [{}])[0].get("prioridad", 5) / 10 if razonamiento.get("acciones") else 0.5,
        prioridad=3,
        datos={
            "detecciones": len(datos_sensor["detecciones"]),
            "tiene_identidad": datos_sensor["tiene_identidad"],
            "adn_count": datos_sensor["adn_count"],
        },
    )

    resultado = {
        "gaps_identidad": len(datos_sensor["detecciones"]),
        "tiene_identidad": datos_sensor["tiene_identidad"],
        "adn_count": datos_sensor["adn_count"],
        "tiene_estrategia": datos_sensor["tiene_estrategia"],
        "alertas_emitidas": alertas_emitidas,
        "razonamiento": razonamiento,
        "detalle": datos_sensor["detecciones"][:10],
    }

    log.info("af5_completo", gaps=len(datos_sensor["detecciones"]),
             identidad=datos_sensor["tiene_identidad"], adn=datos_sensor["adn_count"])
    return resultado
```

## INTEGRACIÓN

### En cron.py — añadir entre AF1/AF3 y AF_restantes:

```python
        # 5b. AF5 Identidad — detectar gaps de identidad + coherencia
        from src.pilates.af5_identidad import ejecutar_af5
        af5 = await ejecutar_af5()
        log.info("cron_semanal_af5_ok", gaps=af5.get("gaps_identidad"), adn=af5.get("adn_count"))
```

### En router.py — añadir endpoint:

```python
@router.post("/af/identidad")
async def af_identidad():
    """AF5: Detecta gaps de identidad, coherencia de canales, diferenciación."""
    from src.pilates.af5_identidad import ejecutar_af5
    return await ejecutar_af5()
```

### En af_restantes.py — NO cambiar. AF5 es un archivo SEPARADO como AF1 y AF3.

### En MANUAL_DIRECTOR_OPUS.md — AF5 ya está en la lista de agentes a configurar.

## COSTE

1 call gpt-4o = ~$0.02/semana = ~$0.08/mes
Sensor = código puro, $0

## TESTS

### T1: AF5 detecta gaps reales
```python
result = await ejecutar_af5()
assert result["gaps_identidad"] >= 0
assert "tiene_identidad" in result
assert "adn_count" in result
```

### T2: AF5 escribe en pizarra
```sql
SELECT agente, detectando, interpretacion FROM om_pizarra
WHERE agente='AF5' ORDER BY updated_at DESC LIMIT 1;
-- Debe existir
```

### T3: AF5 lee pizarra antes de actuar
```python
# AF3 escribe que hay grupos a cerrar
# AF5 debe leerlo y considerar impacto en identidad
await escribir(agente="AF3", capa="ejecutiva",
               detectando="2 grupos a cerrar", conflicto_con=["AF5"])
result = await ejecutar_af5()
# El razonamiento debe mencionar los grupos de AF3
```

### T4: AF5 emite al bus
```sql
SELECT count(*) FROM om_senales_agentes
WHERE origen='AF5' AND tipo='PRESCRIPCION';
```

### T5: Config dinámica del Director funciona para AF5
```python
# Insertar config con INT-17+P05
# Ejecutar AF5
# El razonamiento debe reflejar preguntas existenciales (INT-17)
```

---

## RESULTADO

Con AF5 como agente unificado:
- El Director Opus puede reconfigurar su inteligencia (INT-03,06,08,12,15,17)
- AF5 escribe en la pizarra → AF3 sabe que cerrar un grupo puede afectar la identidad
- AF5 lee la pizarra → sabe que AF1 detectó fantasmas y eso puede ser señal de identidad débil
- El Evaluador puede medir si las prescripciones de F5 funcionaron
- Los 7 archivos voz_* siguen como implementación — AF5 es la INTELIGENCIA encima
