# B-ORG-06: B2.9 — Bloque Voz como Sub-circuito Reactivo

**Fecha:** 22 marzo 2026
**Objetivo:** Conectar el Bloque Voz (B2.8, actualmente batch semanal) al bus de señales para que reaccione en tiempo real. WA lead → señal → respuesta <5min. ACD cambia → estrategia de voz se recalcula. AF5 emite señales que otros AF consumen.
**Depende de:** B-ORG-01+02 (bus) + Bloque Voz existente (voz_ciclos.py, whatsapp.py, voz_estrategia.py)
**Archivos a CREAR:** 1 (voz_reactivo.py)
**Archivos a MODIFICAR:** 2 (router.py — webhook WA + cron.py — listener)
**Tiempo estimado:** 25-35 min

**Cambio de paradigma:**
- **Antes (B2.8):** Cron lunes → escuchar → priorizar → proponer → ejecutar → aprender
- **Ahora (B2.9):** Webhook WA → señal DATO al bus → AF5 clasifica → respuesta <5min para leads

---

## PASO 1: Crear src/pilates/voz_reactivo.py

**Crear archivo:** `src/pilates/voz_reactivo.py`

```python
"""Voz Reactivo — B2.9: Bloque Voz conectado al bus de señales.

Transforma el Bloque Voz de batch semanal a sub-circuito reactivo.

Funciones:
  1. procesar_mensaje_wa_reactivo(): WA entrante → clasificar → señal al bus
     - Lead nuevo → ALERTA prioridad 2 (respuesta <5min)
     - Feedback/queja → ALERTA prioridad 3
     - Consulta normal → DATO prioridad 6
  2. propagar_diagnostico_a_voz(): ACD cambió → recalcular estrategia de voz
  3. procesar_señales_voz(): Lee señales del bus dirigidas a AF5 y actúa
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, timezone
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF5"

# Intenciones que requieren respuesta rápida
INTENCIONES_URGENTES = {"consulta_precio", "reserva", "queja"}
INTENCIONES_LEAD = {"consulta_precio", "reserva"}


async def procesar_mensaje_wa_reactivo(
    telefono: str,
    mensaje_texto: str,
    mensaje_id: UUID | None = None,
    cliente_id: UUID | None = None,
    es_cliente_existente: bool = False,
    intencion: str = "otro",
) -> dict:
    """Procesa un mensaje WA entrante y emite señales al bus.

    Llamado desde el webhook de WA (router.py) después de guardar el mensaje.
    NO reemplaza el procesamiento actual — lo ENRIQUECE con señales.
    """
    from src.pilates.bus import emitir

    acciones = []

    # 1. Lead nuevo: teléfono desconocido preguntando precio/reserva
    if not es_cliente_existente and intencion in INTENCIONES_LEAD:
        await emitir(
            "ALERTA", ORIGEN,
            {
                "subtipo": "lead_nuevo",
                "telefono": telefono,
                "mensaje": mensaje_texto[:200],
                "intencion": intencion,
                "accion_sugerida": f"Lead nuevo desde WA ({telefono}). Responder <5min con precios + enlace onboarding.",
                "funcion": "F2",
            },
            prioridad=2,  # Alta — cada minuto cuenta
        )
        acciones.append("lead_señalizado")

        # Auto-responder si está configurado
        try:
            from src.pilates.whatsapp import respuesta_lead_automatico, is_configured
            if is_configured():
                nombre = ""  # No tenemos nombre aún
                result = await respuesta_lead_automatico(telefono, nombre)
                if result.get("status") == "sent":
                    acciones.append("auto_respondido")
        except Exception as e:
            log.warning("voz_reactivo_autorespuesta_error", error=str(e))

    # 2. Queja de cliente existente → ALERTA para atención inmediata
    elif es_cliente_existente and intencion == "queja":
        await emitir(
            "ALERTA", ORIGEN,
            {
                "subtipo": "queja_cliente",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "telefono": telefono,
                "mensaje": mensaje_texto[:200],
                "accion_sugerida": "Queja recibida por WA. Revisar y responder con empatía <1h.",
                "funcion": "F1",  # Afecta conservación
            },
            prioridad=3,
        )
        acciones.append("queja_señalizada")

    # 3. Feedback positivo → DATO (para telemetría, sin urgencia)
    elif intencion == "feedback":
        await emitir(
            "DATO", ORIGEN,
            {
                "subtipo": "feedback_wa",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "telefono": telefono,
                "sentimiento": "positivo",
                "funcion": "F5",
            },
            prioridad=7,
        )
        acciones.append("feedback_registrado")

    # 4. Cualquier otro mensaje → DATO genérico (bajo ruido)
    else:
        await emitir(
            "DATO", ORIGEN,
            {
                "subtipo": "wa_mensaje",
                "cliente_id": str(cliente_id) if cliente_id else None,
                "intencion": intencion,
                "es_cliente": es_cliente_existente,
                "funcion": "F5",
            },
            prioridad=8,
        )
        acciones.append("mensaje_registrado")

    log.info("voz_reactivo_wa",
        telefono=telefono[:6] + "***",
        intencion=intencion,
        es_cliente=es_cliente_existente,
        acciones=acciones)

    return {"acciones": acciones, "intencion": intencion}


async def propagar_diagnostico_a_voz() -> dict:
    """Cuando el diagnóstico ACD cambia, recalcular estrategia de voz.

    Lee la última señal DIAGNOSTICO del bus y, si indica cambio,
    recalcula la estrategia de voz para alinear contenido con nuevo estado.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada

    # Buscar señales DIAGNOSTICO dirigidas a AF5 o broadcast
    señales = await leer_pendientes(destino="AF5", tipo="DIAGNOSTICO", limite=5)
    if not señales:
        return {"propagado": False, "razon": "Sin señales DIAGNOSTICO pendientes para AF5"}

    for señal in señales:
        payload = señal["payload"]
        if isinstance(payload, str):
            import json
            payload = json.loads(payload)

        cambio = payload.get("cambio", False)
        if cambio:
            try:
                from src.pilates.voz_estrategia import calcular_estrategia
                nueva_est = await calcular_estrategia()
                log.info("voz_reactivo_estrategia_recalculada",
                    estado_acd=payload.get("estado"),
                    foco=nueva_est.get("estrategia", {}).get("foco_principal"))

                await marcar_procesada(str(señal["id"]), ORIGEN)
                return {
                    "propagado": True,
                    "estado_acd": payload.get("estado"),
                    "estrategia_foco": nueva_est.get("estrategia", {}).get("foco_principal"),
                }
            except Exception as e:
                log.warning("voz_reactivo_estrategia_error", error=str(e))
                await marcar_procesada(str(señal["id"]), ORIGEN)
        else:
            # Sin cambio → marcar como procesada sin acción
            await marcar_procesada(str(señal["id"]), ORIGEN)

    return {"propagado": False, "razon": "Señales procesadas pero sin cambio de estado"}


async def emitir_señales_cross_af() -> dict:
    """AF5 emite señales que otros AF consumen.

    Analiza actividad reciente de voz y genera señales cross:
    - Canal sin ROI → AF3 (VETO para no invertir más)
    - Lead sin atender >1h → AF2 (alerta de oportunidad perdida)
    """
    pool = await get_pool()
    from src.pilates.bus import emitir

    señales_emitidas = 0

    async with pool.acquire() as conn:
        # Leads sin responder en >1 hora
        try:
            leads_sin_responder = await conn.fetch("""
                SELECT m.id, m.telefono_remitente, m.contenido, m.created_at
                FROM om_mensajes_wa m
                WHERE m.tenant_id = $1 AND m.direccion = 'entrante'
                AND m.intencion IN ('consulta_precio', 'reserva')
                AND m.respondido = false
                AND m.created_at < now() - interval '1 hour'
                AND m.created_at > now() - interval '24 hours'
            """, TENANT)

            for lead in leads_sin_responder:
                await emitir(
                    "ALERTA", ORIGEN,
                    {
                        "subtipo": "lead_sin_atender",
                        "telefono": lead["telefono_remitente"],
                        "horas_esperando": round((datetime.now(timezone.utc) - lead["created_at"]).total_seconds() / 3600, 1),
                        "accion_sugerida": f"Lead esperando respuesta >1h. Llamar o enviar WA ahora.",
                        "funcion": "F2",
                        "bloquea_af": [],
                    },
                    prioridad=2,
                )
                señales_emitidas += 1
        except Exception as e:
            log.warning("voz_reactivo_leads_error", error=str(e))

        # Canales con IRC < 0.30 → señal a AF3 para considerar abandonar
        try:
            canales_bajo_irc = await conn.fetch("""
                SELECT canal, irc_actual FROM om_voz_irc
                WHERE tenant_id = $1 AND irc_actual < 0.30
            """, TENANT)

            for canal in canales_bajo_irc:
                await emitir(
                    "ALERTA", ORIGEN,
                    {
                        "subtipo": "canal_bajo_irc",
                        "canal": canal["canal"],
                        "irc": float(canal["irc_actual"]),
                        "accion_sugerida": f"Canal '{canal['canal']}' con IRC={canal['irc_actual']:.2f} (<0.30). Considerar abandonar o reestructurar.",
                        "funcion": "F3",
                        "bloquea_af": ["AF2"],  # No captar por canal ineficiente
                    },
                    prioridad=5,
                )
                señales_emitidas += 1
        except Exception as e:
            log.warning("voz_reactivo_irc_error", error=str(e))

    log.info("voz_reactivo_cross_af", señales=señales_emitidas)
    return {"señales_cross_emitidas": señales_emitidas}
```

---

## PASO 2: Modificar webhook WA en router.py — inyectar señales reactivas

**Archivo:** `src/pilates/router.py`

El webhook POST de WA ya existe. Necesitamos añadir la llamada reactiva DESPUÉS de procesar_webhook.

Buscar EXACTAMENTE:
```python
@router.post("/webhook/whatsapp")
async def webhook_recibir(request: Request):
    """Recibe mensajes de WhatsApp (POST webhook)."""
    body = await request.json()
    from src.pilates.whatsapp import procesar_webhook
    result = await procesar_webhook(body)
    return {"status": "ok", **result}
```

Reemplazar por:
```python
@router.post("/webhook/whatsapp")
async def webhook_recibir(request: Request):
    """Recibe mensajes de WhatsApp (POST webhook). B2.9: emite señales al bus."""
    body = await request.json()
    from src.pilates.whatsapp import procesar_webhook
    result = await procesar_webhook(body)

    # B2.9 Reactivo: emitir señales al bus tras procesar el mensaje
    if result.get("mensaje_guardado"):
        asyncio.create_task(_wa_reactivo(result))

    return {"status": "ok", **result}


async def _wa_reactivo(result: dict):
    """Fire-and-forget: WA webhook → señales al bus."""
    try:
        from src.pilates.voz_reactivo import procesar_mensaje_wa_reactivo
        await procesar_mensaje_wa_reactivo(
            telefono=result.get("telefono", ""),
            mensaje_texto=result.get("contenido", ""),
            mensaje_id=result.get("mensaje_id"),
            cliente_id=result.get("cliente_id"),
            es_cliente_existente=result.get("es_cliente", False),
            intencion=result.get("intencion", "otro"),
        )
    except Exception as e:
        import structlog
        structlog.get_logger().warning("wa_reactivo_error", error=str(e))
```

---

## PASO 3: Añadir endpoints + listener al cron

**Archivo:** `src/pilates/router.py`

Después del último endpoint (de B-ORG-05 o B-ORG-04), añadir:

```python


# ============================================================
# B2.9 VOZ REACTIVO — Sub-circuito de señales AF5
# ============================================================

@router.post("/voz/propagar-diagnostico")
async def voz_propagar_diagnostico():
    """Propaga cambio de diagnóstico ACD a la estrategia de voz."""
    from src.pilates.voz_reactivo import propagar_diagnostico_a_voz
    return await propagar_diagnostico_a_voz()


@router.post("/voz/cross-af")
async def voz_cross_af():
    """AF5 emite señales cross-AF: leads sin atender, canales bajo IRC."""
    from src.pilates.voz_reactivo import emitir_señales_cross_af
    return await emitir_señales_cross_af()
```

**Archivo:** `src/pilates/cron.py`

En `_tarea_semanal()`, después del paso de búsqueda por gaps (y antes del except), añadir:

Buscar EXACTAMENTE (el paso 4 que ya existe, la última línea antes del except):
```python
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))
```

DESPUÉS de esta línea, pero ANTES del except, añadir estas líneas (respetar indentación, están dentro del try):

```python

        # 5-extra. AF5 propaga diagnóstico a voz + señales cross-AF
        from src.pilates.voz_reactivo import propagar_diagnostico_a_voz, emitir_señales_cross_af
        await propagar_diagnostico_a_voz()
        await emitir_señales_cross_af()
        log.info("cron_semanal_voz_reactivo_ok")
```

**NOTA:** Si B-ORG-05 ya añadió pasos 5-6 (AF1+AF3), renumerar como "7. AF5 propaga..." No importa el número exacto — lo que importa es que esté DENTRO del try y ANTES del except.

---

## PASO 4: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

---

## TESTS

### TEST 1: Propagar diagnóstico a voz
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/voz/propagar-diagnostico \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = 'propagado' in d
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 2: Señales cross-AF
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/voz/cross-af \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = 'señales_cross_emitidas' in d
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 3: Webhook WA sigue funcionando (verificar que no rompimos nada)
```bash
curl -s https://motor-semantico-omni.fly.dev/pilates/webhook/whatsapp?hub.mode=subscribe\&hub.verify_token=omni_mind_verify_2026\&hub.challenge=test123 \
  | python3 -c "
import sys; r=sys.stdin.read()
print('PASS' if 'test123' in r else 'FAIL:', r)"
```

### TEST 4: Señales AF5 en bus
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/historial?origen=AF5&limite=5' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('PASS' if isinstance(d, dict) and 'señales' in d else 'FAIL:', d)
print(f'  Señales AF5: {d.get(\"total\", 0)}')"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1-3 devuelven PASS.** Test 4 es informativo.

**FAIL = Cualquier test 1-3 devuelve FAIL.**

---

## IMPACTO B2.9

| Antes (B2.8 batch) | Ahora (B2.9 reactivo) |
|---|---|
| Lead WA → esperó al lunes para cron → respuesta 24-48h | Lead WA → webhook → señal → auto-respuesta <5min |
| ACD cambia → estrategia no se actualiza hasta próximo lunes | ACD cambia → señal DIAGNOSTICO → estrategia recalculada al instante |
| Canal con IRC bajo → nadie lo sabe hasta revisión manual | Canal IRC <0.30 → señal a AF3 → VETO → AF2 deja de invertir ahí |
| Lead sin responder → se pierde silenciosamente | Lead >1h sin responder → ALERTA prioridad 2 → visible en /bus/historial |
