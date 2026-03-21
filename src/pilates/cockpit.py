"""Cockpit del Estudio — Motor de interfaz generativa.

Analiza el contexto del día y sugiere qué módulos mostrar.
Aprende de las preferencias de Jesús.
Incluye chat conversacional para controlar la interfaz.
Soporta jerarquía visual: principal / secundario / compacto.

Fuente: Exocortex v2.1 B-PIL-18 Fase J + J5.
"""
from __future__ import annotations
import json, os, time, httpx, structlog
from datetime import date, datetime, timedelta

log = structlog.get_logger()
TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.getenv("PORTAL_CHAT_MODEL", "deepseek/deepseek-chat")

MODULOS = {
    "agenda":           {"nombre": "Agenda de hoy",       "icono": "📅", "endpoint": "/sesiones/hoy"},
    "calendario":       {"nombre": "Calendario semanal",  "icono": "📅", "endpoint": "/sesiones/semana"},
    "feed":             {"nombre": "Noticias",             "icono": "🔔", "endpoint": "/feed"},
    "pagos_pendientes": {"nombre": "Pagos pendientes",    "icono": "💰", "endpoint": "/cargos?estado=pendiente"},
    "resumen_mes":      {"nombre": "Resumen del mes",     "icono": "📊", "endpoint": "/resumen"},
    "briefing":         {"nombre": "Briefing semanal",    "icono": "📋", "endpoint": "/briefing"},
    "solicitudes":      {"nombre": "Solicitudes",          "icono": "📋", "endpoint": "/procesos"},
    "alertas":          {"nombre": "Alertas retención",   "icono": "⚠️", "endpoint": "/alertas"},
    "buscar":           {"nombre": "Buscar cliente",       "icono": "🔍", "endpoint": "/buscar"},
    "grupos":           {"nombre": "Ocupación grupos",    "icono": "👥", "endpoint": "/grupos"},
    "sequito":          {"nombre": "Consejo asesores",     "icono": "🧠", "endpoint": "/consejo"},
    "voz":              {"nombre": "Propuestas Voz",       "icono": "💬", "endpoint": "/voz/propuestas"},
    "depuracion":       {"nombre": "Depuración",          "icono": "🗑️", "endpoint": "/depuracion"},
    "adn":              {"nombre": "ADN del negocio",      "icono": "🧬", "endpoint": "/adn"},
    "readiness":        {"nombre": "Readiness",            "icono": "📈", "endpoint": "/readiness"},
    "facturas":         {"nombre": "Facturación",         "icono": "📄", "endpoint": "/facturas"},
    "engagement":       {"nombre": "Engagement clientes",  "icono": "❤️", "endpoint": "/engagement"},
    "wa":               {"nombre": "Panel WhatsApp",       "icono": "💬", "endpoint": "/whatsapp/mensajes"},
}

# Módulos que visualmente necesitan más espacio
MODULOS_GRANDES = {"calendario", "sequito", "wa", "briefing"}


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def contexto_del_dia() -> dict:
    """Genera el contexto del día para el saludo + sugerencias de módulos."""
    hoy = date.today()
    dia_nombre = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][hoy.weekday()]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        sesiones_hoy = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id=$1 AND fecha=$2
        """, TENANT, hoy)

        cancelaciones = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id=a.sesion_id
            WHERE a.tenant_id=$1 AND s.fecha=$2 AND a.estado='cancelada'
        """, TENANT, hoy)

        deuda_total = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)
        clientes_deudores = await conn.fetchval("""
            SELECT count(DISTINCT cliente_id) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)

        feed_no_leido = await conn.fetchval("""
            SELECT count(*) FROM om_feed_estudio
            WHERE tenant_id=$1 AND leido=false
        """, TENANT)

        alertas = 0
        try:
            alertas = await conn.fetchval("""
                SELECT count(*) FROM om_tensiones
                WHERE tenant_id=$1 AND estado='activa' AND severidad IN ('alta','critica')
            """, TENANT) or 0
        except Exception:
            pass

        solicitudes = 0
        try:
            solicitudes = await conn.fetchval("""
                SELECT count(*) FROM om_procesos
                WHERE tenant_id=$1 AND titulo LIKE 'Solicitud%'
            """, TENANT) or 0
        except Exception:
            pass

        voz_pendientes = 0
        try:
            voz_pendientes = await conn.fetchval("""
                SELECT count(*) FROM om_voz_propuestas
                WHERE tenant_id=$1 AND estado='pendiente'
            """, TENANT) or 0
        except Exception:
            pass

        wa_sin_leer = 0
        try:
            wa_sin_leer = await conn.fetchval("""
                SELECT count(*) FROM om_mensajes_wa
                WHERE tenant_id=$1 AND direccion='entrante' AND leido=false
            """, TENANT) or 0
        except Exception:
            pass

        churn_alto = 0
        try:
            churn_alto = await conn.fetchval("""
                SELECT count(*) FROM om_cliente_perfil
                WHERE tenant_id=$1 AND riesgo_churn IN ('alto','critico')
            """, TENANT) or 0
        except Exception:
            pass

    # Saludo
    partes = [f"Hoy es {dia_nombre} {hoy.day} de {_nombre_mes(hoy.month)}."]
    if sesiones_hoy > 0:
        partes.append(f"{sesiones_hoy} sesiones programadas.")
    else:
        partes.append("No hay sesiones hoy.")

    extras = []
    if cancelaciones > 0:
        extras.append(f"{cancelaciones} cancelación{'es' if cancelaciones > 1 else ''}")
    if feed_no_leido > 0:
        extras.append(f"{feed_no_leido} noticia{'s' if feed_no_leido > 1 else ''}")
    if solicitudes > 0:
        extras.append(f"{solicitudes} solicitud{'es' if solicitudes > 1 else ''}")
    if extras:
        partes.append(" · ".join(extras) + ".")

    saludo = " ".join(partes)

    # Sugerir módulos con jerarquía
    sugeridos = []

    # La agenda siempre es principal si hay sesiones
    if sesiones_hoy > 0:
        sugeridos.append({"id": "agenda", "rol": "principal"})
    else:
        sugeridos.append({"id": "agenda", "rol": "secundario"})

    if feed_no_leido > 0:
        sugeridos.append({"id": "feed", "rol": "secundario"})
    if clientes_deudores > 0:
        sugeridos.append({"id": "pagos_pendientes", "rol": "secundario"})
    if hoy.weekday() == 0:
        sugeridos.append({"id": "briefing", "rol": "principal" if sesiones_hoy == 0 else "secundario"})
    if solicitudes > 0:
        sugeridos.append({"id": "solicitudes", "rol": "compacto"})
    if alertas > 0:
        sugeridos.append({"id": "alertas", "rol": "secundario"})
    if wa_sin_leer > 0:
        sugeridos.append({"id": "wa", "rol": "secundario"})
    if voz_pendientes > 0:
        sugeridos.append({"id": "voz", "rol": "compacto"})
    if churn_alto > 0:
        sugeridos.append({"id": "engagement", "rol": "compacto"})

    sugeridos = sugeridos[:6]

    # Preferencias aprendidas
    try:
        async with pool.acquire() as conn2:
            pref = await conn2.fetchval("""
                SELECT metadata->>'modulos_frecuentes' FROM om_cliente_eventos
                WHERE tenant_id=$1 AND tipo='cockpit_config'
                ORDER BY created_at DESC LIMIT 1
            """, TENANT)
            if pref:
                frecuentes = json.loads(pref)
                ids_ya = {s["id"] for s in sugeridos}
                for m in frecuentes:
                    if m not in ids_ya and m in MODULOS:
                        sugeridos.append({"id": m, "rol": "secundario"})
                sugeridos = sugeridos[:6]
    except Exception:
        pass

    datos = {
        "sesiones_hoy": sesiones_hoy,
        "cancelaciones_hoy": cancelaciones,
        "deuda_total": float(deuda_total),
        "clientes_deudores": clientes_deudores,
        "feed_no_leido": feed_no_leido,
        "alertas_activas": alertas,
        "solicitudes_pendientes": solicitudes,
        "voz_pendientes": voz_pendientes,
        "wa_sin_leer": wa_sin_leer,
        "churn_alto": churn_alto,
    }

    return {
        "saludo": saludo,
        "datos": datos,
        "modulos_sugeridos": [
            {"rol": s["rol"], **MODULOS[s["id"]], "id": s["id"]}
            for s in sugeridos if s["id"] in MODULOS
        ],
        "modulos_disponibles": [
            {"id": k, **v} for k, v in MODULOS.items()
        ],
    }


async def guardar_configuracion(modulos_activos: list):
    """Guarda qué módulos ha elegido Jesús para aprender preferencias.
    
    modulos_activos puede ser:
    - lista de strings: ["agenda", "feed"] (legacy)
    - lista de dicts: [{"id": "agenda", "rol": "principal"}, ...] (nuevo)
    """
    pool = await _get_pool()

    # Normalizar a lista de IDs
    ids = []
    for m in modulos_activos:
        if isinstance(m, str):
            ids.append(m)
        elif isinstance(m, dict):
            ids.append(m.get("id", ""))
    ids = [i for i in ids if i]

    async with pool.acquire() as conn:
        freq_raw = await conn.fetchval("""
            SELECT metadata FROM om_cliente_eventos
            WHERE tenant_id=$1 AND tipo='cockpit_frecuencia'
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        frecuencia = {}
        if freq_raw:
            try:
                meta = freq_raw if isinstance(freq_raw, dict) else json.loads(freq_raw)
                frecuencia = meta if isinstance(meta, dict) else {}
            except Exception:
                pass

        for m in ids:
            frecuencia[m] = frecuencia.get(m, 0) + 1

        top = sorted(frecuencia.items(), key=lambda x: -x[1])[:6]
        modulos_frecuentes = [m[0] for m in top]

        await conn.execute("""
            INSERT INTO om_cliente_eventos (tenant_id, cliente_id, tipo, metadata)
            VALUES ($1, '00000000-0000-0000-0000-000000000000', 'cockpit_config', $2::jsonb)
        """, TENANT, json.dumps({
            "modulos_activos": modulos_activos,
            "modulos_frecuentes": modulos_frecuentes,
            "frecuencia": frecuencia,
        }))


def _nombre_mes(n):
    return ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"][n-1]


# ============================================================
# J4+J5 — Chat conversacional con jerarquía visual
# ============================================================

SYSTEM_COCKPIT = f"""Eres el asistente de interfaz de Authentic Pilates.
Jesús (el dueño) te habla para controlar qué ve en su pantalla.

MÓDULOS DISPONIBLES (usa estos IDs exactos):
{json.dumps({k: v["nombre"] for k, v in MODULOS.items()}, ensure_ascii=False, indent=2)}

JERARQUÍA VISUAL — cada módulo lleva un "rol" que determina su tamaño y posición:
- "principal": GRANDE, ocupa el centro de la pantalla (2 columnas). Solo 1 a la vez. Es el módulo en el que Jesús quiere centrarse.
- "secundario": NORMAL, tamaño estándar. Se colocan alrededor del principal.
- "compacto": PEQUEÑO, solo muestra lo esencial. Para información de apoyo rápida.

REGLAS DE LAYOUT:
1. Si Jesús pide ver algo específico como foco ("ponme la agenda", "necesito ver los pagos"), ese módulo va como "principal".
2. Si pide varios módulos sin énfasis claro, el primero que mencione es "principal" y el resto "secundario".
3. Si dice "ponme X y Y de apoyo" o "X con Y al lado", X es principal e Y secundario.
4. Si dice solo "ponme todo" o no hay foco claro, usa "secundario" para todos.
5. Módulos de información rápida (alertas, engagement, solicitudes) van bien como "compacto".
6. Nunca pongas más de 1 módulo como "principal". Si ya hay uno y pide otro como foco, el anterior pasa a "secundario".

REGLAS GENERALES:
1. Si Jesús pide ver algo, usa configurar_interfaz para montar los módulos.
2. Si pide quitar algo, usa configurar_interfaz con desmontar.
3. Si dice "quita todo" o "limpia", usa desmontar_todos=true.
4. Si la pregunta NO es sobre la interfaz, responde brevemente.
5. Tono de pueblo. Nada de formalidades.
"""

TOOLS_COCKPIT = [
    {
        "type": "function",
        "function": {
            "name": "configurar_interfaz",
            "description": "Montar o desmontar módulos en la interfaz. Cada módulo montado lleva un 'rol' que determina su tamaño visual.",
            "parameters": {
                "type": "object",
                "properties": {
                    "montar": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "description": "ID del módulo"},
                                "rol": {
                                    "type": "string",
                                    "enum": ["principal", "secundario", "compacto"],
                                    "description": "principal=grande centro, secundario=normal, compacto=pequeño"
                                }
                            },
                            "required": ["id", "rol"]
                        },
                        "description": "Módulos a montar con su rol visual"
                    },
                    "desmontar": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "IDs de módulos a quitar"
                    },
                    "desmontar_todos": {
                        "type": "boolean",
                        "description": "Quitar todos antes de montar"
                    }
                }
            }
        }
    }
]


async def chat_cockpit(mensaje: str, modulos_activos: list,
                        historial: list = None) -> dict:
    """Chat conversacional para controlar la interfaz del cockpit.
    
    modulos_activos: lista de dicts [{"id": "agenda", "rol": "principal"}, ...]
    """
    t0 = time.time()

    # Describir estado actual para el LLM
    if modulos_activos:
        desc_activos = ", ".join(
            f"{m['id']}({m.get('rol','secundario')})" if isinstance(m, dict)
            else f"{m}(secundario)"
            for m in modulos_activos
        )
        ctx = f"Módulos activos ahora: {desc_activos}."
    else:
        ctx = "No hay módulos activos ahora."

    messages = [
        {"role": "system", "content": SYSTEM_COCKPIT + "\n" + ctx},
    ]
    if historial:
        messages.extend(historial[-10:])
    messages.append({"role": "user", "content": mensaje})

    acciones = {"montar": [], "desmontar": [], "desmontar_todos": False}
    respuesta_texto = ""

    for _ in range(3):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": CHAT_MODEL,
                        "messages": messages,
                        "tools": TOOLS_COCKPIT,
                        "max_tokens": 400,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            log.error("cockpit_chat_error", error=str(e))
            return {"respuesta": "Ups, algo ha fallado. Prueba otra vez.",
                    "acciones": acciones}

        choice = data["choices"][0]
        msg = choice["message"]

        if not msg.get("tool_calls"):
            respuesta_texto = msg.get("content", "")
            break

        messages.append(msg)
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"].get("arguments", "{}"))
            if fn_name == "configurar_interfaz":
                if fn_args.get("montar"):
                    for m in fn_args["montar"]:
                        mod_id = m.get("id", m) if isinstance(m, dict) else m
                        mod_rol = m.get("rol", "secundario") if isinstance(m, dict) else "secundario"
                        if mod_id in MODULOS:
                            acciones["montar"].append({"id": mod_id, "rol": mod_rol})
                if fn_args.get("desmontar"):
                    acciones["desmontar"].extend(
                        m for m in fn_args["desmontar"] if m in MODULOS)
                if fn_args.get("desmontar_todos"):
                    acciones["desmontar_todos"] = True
                result = {"ok": True,
                          "montados": [m["id"] for m in acciones["montar"]],
                          "desmontados": acciones["desmontar"]}
            else:
                result = {"error": "Herramienta desconocida"}
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False),
            })
    else:
        respuesta_texto = "No he pillado bien qué necesitas. Prueba de otra forma."

    # Enforce: solo 1 principal
    principales = [m for m in acciones["montar"] if m["rol"] == "principal"]
    if len(principales) > 1:
        # Solo el último mencionado es principal
        for m in acciones["montar"]:
            m["rol"] = "secundario"
        acciones["montar"][-1]["rol"] = "principal"

    dt = int((time.time() - t0) * 1000)
    log.info("cockpit_chat", ms=dt, acciones=acciones)

    nuevo_historial = (historial or []) + [
        {"role": "user", "content": mensaje},
        {"role": "assistant", "content": respuesta_texto},
    ]

    return {
        "respuesta": respuesta_texto,
        "acciones": acciones,
        "historial": nuevo_historial[-20:],
        "tiempo_ms": dt,
    }
