# B-PIL-18 — Fases G, H, I (Addendum 2)

**Fecha:** 2026-03-20
**Complementa:** B-PIL-18.md (A,B,C) + B-PIL-18-FASES-DEF.md (D,E,F)
**Ejecutor:** Claude Code

---

## TONO — ALBELDA DE IREGUA (aplica a TODAS las fases)

Este es el cambio más importante: el tono de TODO el sistema.

Albelda de Iregua es un pueblo de ~1.000 habitantes en La Rioja. Aquí nos conocemos todos. El sistema no habla como una empresa — habla como la vecina que te encuentras en el bar.

### System prompt base (reemplaza el de portal_chat.py y se usa en WA y portal público)

```python
TONO_ALBELDA = """
TONO OBLIGATORIO — Eres de Albelda de Iregua (La Rioja). Aqui nos conocemos todos.

Reglas de tono:
- Tutea SIEMPRE. Nunca "usted".
- Cercano de pueblo, no de empresa. Como si hablaras con alguien que ves todos los dias.
- Nada de "Estimado cliente" ni "Le informamos". Eso aqui suena ridiculo.
- Puedes usar expresiones coloquiales: "anda", "venga", "oye", "mira", "pues nada".
- Emojis con moderación (1-2 por mensaje, no mas).
- Si algo va bien: "genial", "perfecto", "hecho". No: "hemos procesado su solicitud con éxito".
- Si algo va mal: "vaya", "uf", "pues mira". No: "lamentamos informarle".
- Si cancela: no le hagas sentir culpable. "Nada, sin problema" o "tranqui, ya buscamos hueco".
- Si paga: "gracias" y ya. No: "agradecemos su puntual contribución".
- Nombres de pila siempre. Nunca "Sra. García".
- Frases cortas. Nada de párrafos largos.
- Cuando algo requiere acción de Jesús: "Se lo digo a Jesús y te cuenta" (no "escalaremos su solicitud").

Ejemplos:
- BIEN: "Oye María, tienes 105€ pendientes del mes. ¿Te paso el Bizum o lo dejamos para cuando vengas?"
- MAL: "Estimada María, le recordamos que tiene un saldo pendiente de 105,00 EUR."
- BIEN: "Hecho, te cancelo la del jueves. ¿Buscamos hueco para recuperar?"
- MAL: "Su sesión ha sido cancelada exitosamente. ¿Desea que busquemos opciones de recuperación?"
- BIEN: "¡8 semanas sin faltar! Eres una crack, María."
- MAL: "Felicidades, ha alcanzado una racha de 8 semanas consecutivas de asistencia."
"""
```

Este tono se inyecta en:
- `portal_chat.py` → system prompt del bot portal
- `wa_respuestas.py` → respuestas WhatsApp
- Portal público de captación → system prompt del bot público
- Mensajes de cumpleaños
- Notificaciones WA automáticas (confirmaciones, lista espera, cobros)

---

## FASE G: Cumpleaños automáticos con tarjeta por WA

### Concepto

El sistema detecta cumpleaños cada día. Genera un mensaje personalizado
y lo envía por WhatsApp. El mensaje incluye un enlace a una "tarjeta"
visual (página HTML bonita con su nombre).

### G1. Cron diario — en automatismos.py

Añadir al cron `diario` (que ahora dice "Sin automatizaciones diarias en MVP"):

```python
async def felicitar_cumpleanos():
    """Cron diario: detecta cumpleaños de hoy y envía felicitación por WA."""
    pool = await _get_pool()
    hoy = date.today()

    async with pool.acquire() as conn:
        # Buscar clientes con cumpleaños hoy (día y mes)
        cumples = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono, c.fecha_nacimiento,
                   EXTRACT(YEAR FROM age(c.fecha_nacimiento)) as edad
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
            WHERE ct.tenant_id = $1 AND ct.estado = 'activo'
                AND c.fecha_nacimiento IS NOT NULL
                AND EXTRACT(MONTH FROM c.fecha_nacimiento) = $2
                AND EXTRACT(DAY FROM c.fecha_nacimiento) = $3
        """, TENANT, hoy.month, hoy.day)

        enviados = 0
        for c in cumples:
            # Verificar que no se haya felicitado ya este año
            ya_felicitado = await conn.fetchval("""
                SELECT 1 FROM om_cliente_eventos
                WHERE cliente_id=$1 AND tipo='cumpleanos_felicitado'
                    AND created_at >= date_trunc('year', CURRENT_DATE)
            """, c["id"])
            if ya_felicitado:
                continue

            # Generar token único para la tarjeta
            import secrets
            token_tarjeta = secrets.token_urlsafe(16)
            base_url = "https://motor-semantico-omni.fly.dev"

            # Mensaje WA
            mensaje = (
                f"¡Feliz cumpleaños, {c['nombre']}! 🎂\n\n"
                f"Hoy es tu día y desde Authentic Pilates queríamos "
                f"mandarte un abrazo bien grande.\n\n"
                f"Te hemos preparado una cosita:\n"
                f"{base_url}/tarjeta/{token_tarjeta}\n\n"
                f"¡Pásalo genial! 🎉"
            )

            from src.pilates.whatsapp import enviar_texto, is_configured
            if is_configured() and c["telefono"]:
                await enviar_texto(c["telefono"], mensaje, c["id"])
                enviados += 1

                # Guardar token tarjeta para el endpoint
                await conn.execute("""
                    INSERT INTO om_cliente_eventos
                        (tenant_id, cliente_id, tipo, metadata)
                    VALUES ($1, $2, 'cumpleanos_felicitado', $3::jsonb)
                """, TENANT, c["id"], json.dumps({
                    "token_tarjeta": token_tarjeta,
                    "nombre": c["nombre"],
                    "edad": int(c["edad"]) if c["edad"] else None,
                    "year": hoy.year
                }))

            # Feed del estudio
            from src.pilates.feed import publicar
            await publicar("cumpleanos", "🎂",
                f"¡Hoy cumple años {c['nombre']}!",
                f"Felicitación enviada por WA", c["id"], "success")

    log.info("cumpleanos_check", hoy=str(hoy), enviados=enviados)
    return {"cumpleanos_hoy": len(cumples), "felicitaciones_enviadas": enviados}
```

### G2. Endpoint tarjeta visual

```python
@router.get("/tarjeta/{token}")
async def tarjeta_cumpleanos(token: str):
    """Página HTML bonita con felicitación personalizada.
    
    Accesible sin login (enlace único enviado por WA).
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        evento = await conn.fetchrow("""
            SELECT metadata FROM om_cliente_eventos
            WHERE tipo='cumpleanos_felicitado'
                AND metadata->>'token_tarjeta' = $1
            ORDER BY created_at DESC LIMIT 1
        """, token)

    if not evento:
        raise HTTPException(404, "Tarjeta no encontrada")

    meta = evento["metadata"]
    nombre = meta.get("nombre", "")

    from starlette.responses import HTMLResponse
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Feliz cumpleaños {nombre}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    min-height:100vh; display:flex; align-items:center; justify-content:center;
    font-family:'Georgia',serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 20px;
  }}
  .card {{
    background: white; border-radius: 24px; padding: 48px 36px;
    max-width: 400px; width: 100%; text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  }}
  .emoji {{ font-size: 64px; margin-bottom: 16px; }}
  h1 {{ font-size: 28px; color: #1a1a2e; margin-bottom: 8px; }}
  .nombre {{ font-size: 36px; color: #6366f1; font-style: italic; margin-bottom: 24px; }}
  p {{ font-size: 16px; color: #555; line-height: 1.6; margin-bottom: 16px; }}
  .firma {{ font-size: 14px; color: #999; margin-top: 32px; }}
  .firma strong {{ color: #6366f1; }}
</style></head>
<body>
<div class="card">
  <div class="emoji">🎂</div>
  <h1>¡Feliz cumpleaños,</h1>
  <div class="nombre">{nombre}!</div>
  <p>Hoy es un día especial y queríamos que supieras
  lo mucho que nos alegra tenerte en el estudio.</p>
  <p>Gracias por confiar en nosotros para cuidarte.
  ¡A por un año más lleno de fuerza y equilibrio!</p>
  <div class="firma">Con cariño,<br><strong>Authentic Pilates</strong><br>Albelda de Iregua</div>
</div>
</body></html>"""
    return HTMLResponse(html)
```

### G3. Actualizar cron diario

En `ejecutar_cron("diario")`:

```python
elif tipo == "diario":
    import json
    resultados["cumpleanos"] = await felicitar_cumpleanos()
    # (Futuro: cobros recurrentes del día)
    from src.pilates.stripe_pagos import cron_cobros_recurrentes
    resultados["cobros"] = await cron_cobros_recurrentes()
```

---

## FASE H: WhatsApp inteligente bidireccional (Motor conversacional sobre WA)

### Concepto

El mismo motor conversacional del portal (portal_chat.py con function calling)
funciona también sobre WhatsApp. Cuando un cliente escribe por WA, el sistema
entiende lo que pide y responde directamente, sin que Jesús intervenga.

"Oye, no puedo ir el jueves a las 5" → el sistema cancela, busca alternativas,
y responde por WA. Todo automático.

### H1. Nuevo módulo — src/pilates/wa_chat.py

```python
"""WhatsApp Conversacional — Motor LLM sobre mensajes WA.

Reutiliza el motor de portal_chat.py pero adaptado a WhatsApp:
- Sin historial visual (cada mensaje es standalone o con contexto corto)
- Respuestas más cortas (WA no es para párrafos)
- Acciones destructivas: el bot pide confirmación por WA
- Si no es cliente: redirige al portal público

Fuente: Exocortex v2.1 B-PIL-18 Fase H.
"""
from __future__ import annotations
import json, os, structlog
from datetime import date
from uuid import UUID
from typing import Optional

log = structlog.get_logger()
TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# Cache de conversaciones WA en memoria (últimos 5 mensajes por teléfono)
# En producción usar Redis, pero para MVP dict en memoria vale
_wa_historial: dict[str, list] = {}


async def procesar_mensaje_wa(telefono: str, mensaje: str,
                                cliente_id: Optional[UUID] = None) -> dict:
    """Procesa mensaje WA entrante con el motor conversacional.

    Si es cliente → usa portal_chat.py con sus herramientas
    Si NO es cliente → respuesta de captación (portal público)

    Returns:
        {"respuesta": str, "auto_enviar": bool}
    """
    # Identificar si es cliente
    if not cliente_id:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT c.id FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id=c.id
                WHERE ct.tenant_id=$1 AND c.telefono LIKE '%' || $2
                    AND ct.estado='activo'
            """, TENANT, telefono[-9:])
            if row:
                cliente_id = row["id"]

    if cliente_id:
        return await _procesar_cliente(telefono, mensaje, cliente_id)
    else:
        return await _procesar_lead(telefono, mensaje)


async def _procesar_cliente(telefono: str, mensaje: str, cliente_id: UUID) -> dict:
    """Procesa mensaje de cliente conocido — usa motor portal_chat."""

    # Obtener token del portal para reutilizar portal_chat.chat()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        token = await conn.fetchval("""
            SELECT token FROM om_onboarding_links
            WHERE cliente_id=$1 AND tenant_id=$2 AND es_portal=true
        """, cliente_id, TENANT)

    if not token:
        return {
            "respuesta": "Oye, no te tengo localizado en el sistema. "
                         "¿Me dices tu nombre completo?",
            "auto_enviar": True
        }

    # Recuperar historial WA (últimos mensajes)
    historial = _wa_historial.get(telefono, [])

    # Usar el motor de portal_chat
    from src.pilates.portal_chat import chat
    result = await chat(token, mensaje, historial)

    # Guardar historial (máx 10 mensajes)
    historial.append({"role": "user", "content": mensaje})
    historial.append({"role": "assistant", "content": result["respuesta"]})
    _wa_historial[telefono] = historial[-10:]

    # Registrar evento
    from src.pilates.engagement import registrar_evento
    await registrar_evento(cliente_id, "wa_chat_entrante", {
        "mensaje": mensaje[:200],
        "tools": result.get("tools_usadas", [])
    })

    # Adaptar respuesta para WA (más corta)
    respuesta = result["respuesta"]
    # Truncar si es muy largo para WA
    if len(respuesta) > 1000:
        respuesta = respuesta[:950] + "\n\n(Más detalles en tu portal)"

    return {"respuesta": respuesta, "auto_enviar": True}


async def _procesar_lead(telefono: str, mensaje: str) -> dict:
    """Procesa mensaje de persona NO cliente — captación.

    Usa el motor del portal público (Fase I).
    """
    from src.pilates.portal_publico import chat_captacion
    result = await chat_captacion(mensaje, telefono)

    return {
        "respuesta": result["respuesta"],
        "auto_enviar": True
    }
```

### H2. Integrar en webhook WA existente

**Archivo:** `src/pilates/whatsapp.py` — En `procesar_webhook()`, DESPUÉS de clasificar intención, añadir:

```python
# ANTES: clasificar intención + guardar en DB (mantener)
# NUEVO: procesar con motor conversacional
from src.pilates.wa_chat import procesar_mensaje_wa
result = await procesar_mensaje_wa(remitente, contenido, cliente_id)

if result.get("auto_enviar") and result.get("respuesta"):
    await enviar_texto(remitente, result["respuesta"], cliente_id)
    log.info("wa_chat_auto", telefono=remitente[-4:])
```

### H3. Flujo ejemplo completo

```
Cliente (WA): "Oye no puedo ir el jueves a las 5"

Sistema internamente:
1. Identifica cliente por teléfono
2. Recupera token portal
3. Pasa mensaje al motor portal_chat con function calling
4. LLM decide: ver_proximas_clases → encuentra sesión jueves 17:00
5. LLM responde pidiendo confirmación

Sistema (WA): "Sin problema. Tienes clase el jueves a las 17:00 en 
Reformer M-J. ¿Te la cancelo? Y si quieres busco hueco para recuperar."

Cliente (WA): "Sí, cancela y busca"

Sistema internamente:
6. LLM ejecuta: cancelar_sesion + buscar_huecos_recuperacion
7. Encuentra 3 huecos

Sistema (WA): "Hecho, cancelada sin cargo. He encontrado estos huecos:
- Viernes 17:00 (Suelo 2, 2 plazas)
- Lunes 10:00 (Mat 1, 3 plazas)
¿Te apunto a alguno?"

Cliente (WA): "El viernes va bien"

Sistema internamente:
8. LLM ejecuta: solicitar_recuperacion

Sistema (WA): "Apuntada al viernes a las 17:00 (Suelo 2). ¡Nos vemos! 💪"
```

Todo automático. Jesús no interviene.

---

## FASE I: Portal público de captación (Landing conversacional)

### Concepto

Una URL pública (ej: `authentic-pilates.fly.dev/info` o enlace en Google Maps)
donde cualquier persona puede preguntar sobre el estudio.

Un bot conversacional explica qué es Authentic Pilates, la filosofía,
el método — pero NUNCA da precios ni horarios. El objetivo es persuadir
elegantemente para que vengan a una sesión de prueba.

### I1. Backend — src/pilates/portal_publico.py

```python
"""Portal Público de Captación — Landing conversacional.

Bot que explica Authentic Pilates a desconocidos.
Objetivo: persuadir para sesión de prueba.
Reglas: NUNCA precios, NUNCA horarios concretos.

Fuente: Exocortex v2.1 B-PIL-18 Fase I.
"""
from __future__ import annotations
import json, os, time, httpx, structlog
from uuid import UUID

log = structlog.get_logger()
TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.getenv("PORTAL_CHAT_MODEL", "deepseek/deepseek-chat")


SYSTEM_CAPTACION = """Eres el asistente de Authentic Pilates, un estudio de Pilates 
en Albelda de Iregua (La Rioja). Hablas con alguien que NO es cliente todavia.

QUIÉN ERES:
- Cercano, de pueblo. Aqui nos conocemos todos. Tutea siempre.
- No eres un vendedor. Eres alguien que le apasiona lo que hace y quiere compartirlo.
- Transmites que esto es algo especial, no un gimnasio cualquiera.

QUÉ ES AUTHENTIC PILATES:
- Estudio boutique dirigido por Jesús, instructor formado en el método auténtico.
- Pilates de verdad: reformer, mat, trabajo personalizado.
- Grupos reducidos (máximo 4-6 personas). Atención individual real.
- Enfoque en salud, postura, bienestar profundo. No en "ponerse en forma" ni en estética.
- Cada sesión se adapta a la persona: sus lesiones, su cuerpo, su momento.
- El Pilates auténtico es un sistema completo de movimiento, no solo ejercicios.
- Trabajan personas de todas las edades, con o sin lesiones.

TU OBJETIVO:
- Que la persona se interese y quiera venir a PROBAR una sesión.
- Persuadir de forma elegante. No empujar. Que sienta curiosidad.
- Transmitir que esto es diferente, profundo, personal.

REGLAS ABSOLUTAS:
1. NUNCA des precios. Si preguntan: "Mira, tenemos varias opciones según lo que 
   necesites. Lo mejor es que vengas a probar y lo hablamos en persona."
2. NUNCA des horarios concretos. Si preguntan: "Tenemos horarios de mañana y tarde, 
   ya vemos cuál te encaja. ¿Cuándo te vendría bien pasarte?"
3. NUNCA digas "reserva online" ni "apúntate aquí". Todo es personal.
4. Si preguntan por ubicación: "Estamos en Albelda de Iregua, muy cerquita 
   de Logroño. ¿Necesitas que te diga cómo llegar?"
5. Si quieren probar: "¡Genial! Déjame tu teléfono y Jesús te llama para 
   buscar un hueco." O pide el teléfono para que Jesús contacte.

ESTILO:
- Frases cortas. Entusiasmo natural, no forzado.
- Usa "nosotros" como comunidad, no como empresa.
- Si la persona tiene dudas sobre Pilates en general: explica que no es yoga, 
  no es stretching, es un sistema de movimiento diseñado para mejorar cómo 
  funciona tu cuerpo.
- Si tiene lesiones: "Precisamente, es donde más se nota la diferencia. 
  El Pilates auténtico nació para rehabilitación."

CIERRE:
- Siempre intenta cerrar con una invitación a probar.
- "¿Por qué no te pasas un día y lo pruebas? Así lo ves tú mismo/a."
- Si deja teléfono → registrar como lead para que Jesús llame.
"""

# Tools mínimas para captación
TOOLS_CAPTACION = [
    {
        "type": "function",
        "function": {
            "name": "registrar_lead",
            "description": "Registrar persona interesada como lead. Usar cuando deja teléfono, nombre, o dice que quiere probar. Jesús le llamará.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la persona"},
                    "telefono": {"type": "string", "description": "Teléfono si lo da"},
                    "interes": {"type": "string", "description": "Qué le interesa: reformer, mat, lesión, general..."},
                    "notas": {"type": "string", "description": "Cualquier info útil para Jesús"}
                },
                "required": ["interes"]
            }
        }
    }
]


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def _tool_registrar_lead(args: dict, telefono_wa: str = None) -> dict:
    """Registra lead en om_procesos + notifica a Jesús."""
    pool = await _get_pool()
    nombre = args.get("nombre", "Desconocido")
    tel = args.get("telefono", telefono_wa or "")
    interes = args.get("interes", "general")
    notas = args.get("notas", "")

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_procesos (tenant_id, nombre, tipo, estado, descripcion, prioridad)
            VALUES ($1, $2, 'lead_captacion', 'pendiente', $3, 'alta')
        """, TENANT,
            f"Lead: {nombre} ({tel})",
            f"Interés: {interes}. Notas: {notas}. Tel: {tel}")

    # Notificar a Jesús
    from src.pilates.whatsapp import enviar_texto, is_configured
    jesus_tel = os.getenv("JESUS_TELEFONO", "")
    if is_configured() and jesus_tel:
        msg = f"🆕 Lead nuevo: {nombre}\nTel: {tel}\nInterés: {interes}\n{notas}"
        await enviar_texto(jesus_tel, msg)

    # Feed
    from src.pilates.feed import publicar
    await publicar("lead", "🆕", f"Nuevo lead: {nombre}",
                    f"Interés: {interes}. Tel: {tel}", severidad="success")

    return {"registrado": True, "mensaje": "Perfecto, Jesús te llama en breve."}


async def chat_captacion(mensaje: str, telefono_wa: str = None,
                          historial: list = None) -> dict:
    """Motor conversacional para leads/público general."""
    t0 = time.time()
    messages = [{"role": "system", "content": SYSTEM_CAPTACION}]
    if historial:
        messages.extend(historial[-10:])
    messages.append({"role": "user", "content": mensaje})

    max_iter = 3
    respuesta_texto = ""

    for _ in range(max_iter):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": CHAT_MODEL,
                        "messages": messages,
                        "tools": TOOLS_CAPTACION,
                        "max_tokens": 500,
                        "temperature": 0.5,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.error("captacion_llm_error", error=str(e))
            return {"respuesta": "¡Hola! Estamos teniendo un problemilla técnico. "
                                  "Escríbenos por WhatsApp al 600XXXXXX y te contamos todo."}

        choice = data["choices"][0]
        msg = choice["message"]

        if not msg.get("tool_calls"):
            respuesta_texto = msg.get("content", "")
            break

        messages.append(msg)
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"].get("arguments", "{}"))
            if fn_name == "registrar_lead":
                result = await _tool_registrar_lead(fn_args, telefono_wa)
            else:
                result = {"error": "Herramienta desconocida"}
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })
    else:
        respuesta_texto = "¡Hola! Soy el asistente de Authentic Pilates. ¿En qué puedo ayudarte?"

    # Log
    dt = int((time.time() - t0) * 1000)
    log.info("captacion_chat", ms=dt, telefono=telefono_wa)

    nuevo_historial = (historial or []) + [
        {"role": "user", "content": mensaje},
        {"role": "assistant", "content": respuesta_texto},
    ]

    return {
        "respuesta": respuesta_texto,
        "historial": nuevo_historial[-20:],
        "tiempo_ms": dt,
    }
```

### I2. Frontend — PortalPublico.jsx

```jsx
// Interfaz pública — sin login, sin token
// Accesible en /info o /authentic-pilates
// Mismo diseño que PortalChat pero sin datos personales
// Fondo más visual/marketing, logo grande
// Sugerencias: "¿Qué es Pilates?", "¿Para quién es?", "Quiero probar"
```

Shortcuts sugeridos:
- "¿Qué es el Pilates auténtico?"
- "Tengo una lesión, ¿me puede ayudar?"
- "¿En qué se diferencia de un gimnasio?"
- "Quiero probar una clase"

### I3. Endpoints

```python
# En router.py:

class ChatPublicoRequest(BaseModel):
    mensaje: str
    historial: Optional[list] = None

@router.post("/publico/chat")
async def chat_publico(data: ChatPublicoRequest):
    """Chat público de captación — sin autenticación."""
    from src.pilates.portal_publico import chat_captacion
    return await chat_captacion(data.mensaje, historial=data.historial)

# El frontend se monta en /info en App.jsx
```

### I4. Flujo ejemplo

```
Visitante (desde link en Google Maps): "Hola, he visto que tenéis un estudio 
de Pilates. ¿Qué tal está?"

Bot: "¡Hola! Pues mira, estamos en Albelda, un estudio pequeñito 
pero con mucho mimo. Aquí hacemos Pilates de verdad — reformer, mat, 
todo adaptado a cada persona. No es como un gimnasio donde te ponen 
una rutina y ahí te apañas. Aquí Jesús (el instructor) te conoce, 
sabe lo que necesitas y cada sesión es diferente. ¿Habías hecho 
Pilates alguna vez?"

Visitante: "No, nunca. ¿Cuánto cuesta?"

Bot: "Tenemos varias opciones según lo que necesites — grupos 
reducidos, sesiones individuales... Lo mejor es que te pases un día 
a probar y lo hablamos tranquilamente. Así ves el estudio, conoces 
a Jesús y te hacemos una sesión para que notes la diferencia. 
¿Te animas?"

Visitante: "Sí, ¿cómo puedo probar?"

Bot: "Genial! Dime tu nombre y teléfono y Jesús te llama para 
buscar un huequito que te venga bien."

Visitante: "Soy Laura, 670123456"

Bot (ejecuta registrar_lead): "Perfecto Laura, se lo paso a Jesús 
y te llama en un ratito. ¡Ya verás, te va a encantar!"

→ Jesús recibe WA: "🆕 Lead nuevo: Laura. Tel: 670123456. 
Interés: primera vez, quiere probar."
→ Feed estudio: "🆕 Nuevo lead: Laura"
```

---

## RESUMEN — TODAS LAS FASES B-PIL-18

| Fase | Qué | Archivos nuevos | Complejidad |
|---|---|---|---|
| A | Motor conversacional (12 tools) | portal_chat.py | Alta |
| B | Frontend chat portal | PortalChat.jsx | Media |
| C | Verificación base | — | — |
| D | Stripe pagos recurrentes | stripe_pagos.py | Media |
| E | Engagement social (aprendizaje) | engagement.py | Media |
| F | Feed estudio (noticias) | feed.py | Baja |
| G | Cumpleaños automáticos | en automatismos.py | Baja |
| H | WA inteligente bidireccional | wa_chat.py | Media |
| I | Portal público captación | portal_publico.py, PortalPublico.jsx | Media |

**Orden de ejecución recomendado:**

1. **A+B+C** — Portal conversacional base (cimiento de todo)
2. **F** — Feed estudio (rápido, da visibilidad inmediata a Jesús)
3. **H** — WA bidireccional (reutiliza motor de A, altísimo valor)
4. **G** — Cumpleaños (rápido, impacto emocional alto)
5. **I** — Portal público captación (nuevo canal de leads)
6. **E** — Engagement social (requiere datos de uso)
7. **D** — Stripe (requiere cuenta configurada)

**Tono Albelda** se implementa en el paso 1 y se propaga a todas las fases.

---

## VERIFICACIÓN FASES G, H, I

```bash
# G1. Cumpleaños
# Insertar cliente con fecha_nacimiento = hoy
curl -X POST .../cron/diario
# PASS: felicitaciones_enviadas >= 1

# G2. Tarjeta visual
curl .../tarjeta/{token_de_test}
# PASS: HTML con nombre del cliente, diseño bonito

# H1. WA bidireccional
# Simular webhook WA entrante de cliente conocido con "no puedo ir el jueves"
# PASS: sistema responde por WA con detalles de la sesión y pregunta confirmación

# H2. WA lead
# Simular webhook WA de número desconocido con "¿qué ofrecéis?"
# PASS: respuesta de captación sin precios ni horarios

# I1. Portal público
curl -X POST .../publico/chat -d '{"mensaje":"¿qué es pilates?"}'
# PASS: respuesta con tono Albelda, sin precios, invitando a probar

# I2. Registrar lead
curl -X POST .../publico/chat -d '{"mensaje":"Soy Laura, 670123456, quiero probar"}'
# PASS: tools_usadas contiene "registrar_lead", Jesús notificado por WA
```
