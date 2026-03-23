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
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o")


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
            INSERT INTO om_procesos (tenant_id, area, titulo, descripcion, pasos, documentado_por)
            VALUES ($1, 'cliente', $2, $3, '[]'::jsonb, 'sistema_captacion')
        """, TENANT,
            f"Lead: {nombre} ({tel})",
            f"Interés: {interes}. Notas: {notas}. Tel: {tel}")

    # Notificar a Jesús
    from src.pilates.whatsapp import enviar_texto, is_configured
    jesus_tel = os.getenv("JESUS_TELEFONO", "")
    if is_configured() and jesus_tel:
        msg = f"Lead nuevo: {nombre}\nTel: {tel}\nInterés: {interes}\n{notas}"
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
            return {"respuesta": "Hola! Estamos teniendo un problemilla técnico. "
                                  "Escríbenos por WhatsApp y te contamos todo."}

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
        respuesta_texto = "Hola! Soy el asistente de Authentic Pilates. ¿En qué puedo ayudarte?"

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
