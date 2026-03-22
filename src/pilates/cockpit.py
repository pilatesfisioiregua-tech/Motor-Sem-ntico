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
    "voz":              {"nombre": "Voz estratégica",      "icono": "📢", "endpoint": "/voz/estrategia"},
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
# COCKPIT OPERATIVO — Centro de mando conversacional (B-PIL-19)
# ============================================================

SYSTEM_COCKPIT = f"""Eres el asistente de interfaz de Authentic Pilates.
Jesús (el dueño) te habla para controlar qué ve en su pantalla Y para ejecutar operaciones del estudio.

MÓDULOS DISPONIBLES (usa estos IDs exactos):
{json.dumps({k: v["nombre"] for k, v in MODULOS.items()}, ensure_ascii=False, indent=2)}

JERARQUÍA VISUAL — cada módulo lleva un "rol":
- "principal": GRANDE, centro de pantalla. Solo 1 a la vez.
- "secundario": NORMAL, tamaño estándar.
- "compacto": PEQUEÑO, info de apoyo.

REGLAS DE LAYOUT:
1. Si pide ver algo como foco → "principal". Varios → primero "principal", resto "secundario".
2. Módulos rápidos (alertas, engagement) → "compacto".
3. Nunca más de 1 "principal".

OPERACIONES:
Además de controlar la interfaz, puedes ejecutar operaciones del estudio:
- Buscar clientes por nombre o teléfono
- Agendar sesiones individuales recurrentes (ej: "martes y viernes hasta junio")
- Inscribir clientes en grupos
- Cancelar sesiones de un cliente (una, varias, o un período)
- Registrar pagos (Bizum, efectivo, transferencia)
- Generar facturas desde cargos cobrados
- Enviar facturas o mensajes por WhatsApp
- Ver detalles de clientes, grupos, pagos
- Ver estrategia de comunicación y calendario de contenido semanal
- Ver señales pendientes (ocupación, inactivos, oportunidades, clima)
- Ver salud de presencia digital (ISP por canal)
- Recalcular estrategia de comunicación (~5 seg)
- Generar perfiles optimizados para canales digitales (~20 seg)
- Ejecutar ciclo completo de escucha y análisis (~2 seg)

REGLAS OPERATIVAS:
1. Antes de ejecutar cualquier acción, BUSCA al cliente por nombre para obtener su ID.
2. Para acciones destructivas (cancelar, eliminar), CONFIRMA con Jesús antes de ejecutar.
3. Si Jesús dice "agéndame a X los martes y viernes hasta junio", calcula todas las fechas y crea las sesiones de golpe.
4. Si dice "ponle en el grupo de las 17h", busca el grupo que encaje por hora y lo inscribe.
5. Para facturas: primero busca cargos cobrados sin facturar, luego genera la factura.
6. Puedes combinar operaciones de interfaz con operativas en la misma respuesta.
7. Tras una operación, muestra el módulo relevante (ej: tras agendar → montar "calendario").
8. Para consultas de Voz ("¿cuál es mi estrategia?", "¿cómo va mi presencia?", "prepárame posts"), usa las herramientas voz_*. Tras consultar, monta el módulo "voz".

REGLAS GENERALES:
1. Si pide ver algo → configurar_interfaz.
2. Si pide quitar algo → desmontar. "Quita todo" → desmontar_todos=true.
3. Tono de pueblo. Nada de formalidades.
"""

TOOLS_COCKPIT = [
    # --- INTERFAZ ---
    {
        "type": "function",
        "function": {
            "name": "configurar_interfaz",
            "description": "Montar o desmontar módulos visuales.",
            "parameters": {
                "type": "object",
                "properties": {
                    "montar": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "rol": {"type": "string", "enum": ["principal","secundario","compacto"]}
                            },
                            "required": ["id", "rol"]
                        }
                    },
                    "desmontar": {"type": "array", "items": {"type": "string"}},
                    "desmontar_todos": {"type": "boolean"}
                }
            }
        }
    },
    # --- BUSCAR CLIENTE ---
    {
        "type": "function",
        "function": {
            "name": "buscar_cliente",
            "description": "Buscar cliente por nombre, apellidos o teléfono. SIEMPRE usar antes de cualquier operación con un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nombre, apellidos o teléfono"}
                },
                "required": ["query"]
            }
        }
    },
    # --- DETALLE CLIENTE ---
    {
        "type": "function",
        "function": {
            "name": "ver_cliente",
            "description": "Ver detalle completo de un cliente: contrato, grupo, asistencia, saldo, próximas clases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- AGENDAR SESIONES RECURRENTES ---
    {
        "type": "function",
        "function": {
            "name": "agendar_sesiones_recurrentes",
            "description": "Crear sesiones individuales recurrentes. Ej: martes 12:00 y viernes 13:00 cada semana hasta una fecha.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "slots": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dia_semana": {"type": "integer", "description": "0=lunes, 1=martes, 2=miércoles, 3=jueves, 4=viernes"},
                                "hora_inicio": {"type": "string", "description": "HH:MM"},
                                "hora_fin": {"type": "string", "description": "HH:MM (default: +1h)"}
                            },
                            "required": ["dia_semana", "hora_inicio"]
                        }
                    },
                    "hasta_fecha": {"type": "string", "description": "YYYY-MM-DD"},
                    "desde_fecha": {"type": "string", "description": "YYYY-MM-DD (default: hoy)"}
                },
                "required": ["cliente_id", "slots", "hasta_fecha"]
            }
        }
    },
    # --- INSCRIBIR EN GRUPO ---
    {
        "type": "function",
        "function": {
            "name": "inscribir_en_grupo",
            "description": "Inscribir cliente en un grupo. Busca por nombre o por horario ('el grupo de las 17h').",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "grupo_id": {"type": "string", "description": "UUID del grupo (si se conoce)"},
                    "buscar_grupo": {"type": "string", "description": "Texto para buscar grupo: hora, nombre, días"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- VER GRUPOS ---
    {
        "type": "function",
        "function": {
            "name": "ver_grupos",
            "description": "Listar grupos con plazas, horarios y ocupación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "solo_con_plaza": {"type": "boolean", "default": True}
                }
            }
        }
    },
    # --- CANCELAR SESIONES ---
    {
        "type": "function",
        "function": {
            "name": "cancelar_sesiones_cliente",
            "description": "Cancelar sesiones de un cliente. Una específica, rango de fechas, o próxima semana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "sesion_id": {"type": "string", "description": "UUID de sesión específica"},
                    "fecha_inicio": {"type": "string", "description": "YYYY-MM-DD"},
                    "fecha_fin": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- REGISTRAR PAGO ---
    {
        "type": "function",
        "function": {
            "name": "registrar_pago",
            "description": "Registrar pago (Bizum, efectivo, transferencia). Concilia FIFO con cargos pendientes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "monto": {"type": "number", "description": "Euros"},
                    "metodo": {"type": "string", "enum": ["bizum", "efectivo", "transferencia", "tpv"]}
                },
                "required": ["cliente_id", "monto", "metodo"]
            }
        }
    },
    # --- GENERAR FACTURAS ---
    {
        "type": "function",
        "function": {
            "name": "generar_facturas",
            "description": "Generar facturas desde cargos cobrados sin facturar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "periodo": {"type": "string", "description": "'ultimo_mes', '2025', 'YYYY-MM'. Default: sin facturar."}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- ENVIAR WHATSAPP ---
    {
        "type": "function",
        "function": {
            "name": "enviar_whatsapp",
            "description": "Enviar mensaje o factura por WhatsApp a un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"},
                    "mensaje": {"type": "string", "description": "Texto libre"},
                    "factura_id": {"type": "string", "description": "UUID de factura"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- VER PAGOS/SALDO ---
    {
        "type": "function",
        "function": {
            "name": "ver_pagos_cliente",
            "description": "Ver saldo pendiente, cargos y últimos pagos de un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- VOZ: ESTRATEGIA ---
    {
        "type": "function",
        "function": {
            "name": "voz_estrategia",
            "description": "Ver la estrategia de comunicación activa: foco, narrativa, canales prioridad, calendario semanal con contenido propuesto.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: SEÑALES ---
    {
        "type": "function",
        "function": {
            "name": "voz_senales",
            "description": "Ver señales pendientes del negocio: ocupación baja, clientes inactivos, oportunidades, lluvia prevista, etc.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: ISP (salud de presencia digital) ---
    {
        "type": "function",
        "function": {
            "name": "voz_isp",
            "description": "Ver el Índice de Salud de Presencia de cada canal: qué está bien configurado y qué falta.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: RECALCULAR ESTRATEGIA ---
    {
        "type": "function",
        "function": {
            "name": "voz_recalcular",
            "description": "Recalcular la estrategia semanal de comunicación completa (IRC x Matriz x PCA). Genera nuevo calendario. ~5 seg.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: GENERAR PERFILES ---
    {
        "type": "function",
        "function": {
            "name": "voz_generar_perfiles",
            "description": "Generar configuración optimizada de todos los perfiles digitales (WA, Google, IG, FB). ~20 seg.",
            "parameters": {
                "type": "object",
                "properties": {
                    "canal": {"type": "string", "description": "Canal específico (whatsapp/google_business/instagram/facebook). Si vacío, genera todos."}
                }
            }
        }
    },
    # --- VOZ: EJECUTAR CICLO ---
    {
        "type": "function",
        "function": {
            "name": "voz_ciclo",
            "description": "Ejecutar ciclo completo: escuchar señales + priorizar + recalcular IRC + ISP. ~2 seg.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "voz_collectors",
            "description": "Ejecutar collectors de métricas: Instagram, Google Business, WhatsApp. ~5 seg.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
]


# ============================================================
# TOOLS OPERATIVAS — Ejecución directa contra DB
# ============================================================

async def _op_buscar_cliente(args: dict) -> dict:
    """Buscar cliente por nombre, apellidos o teléfono."""
    q = args["query"]
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   co.tipo as contrato_tipo, co.estado as contrato_estado,
                   g.nombre as grupo_nombre, g.id as grupo_id,
                   COALESCE((SELECT SUM(total) FROM om_cargos
                    WHERE cliente_id=c.id AND tenant_id=$1 AND estado='pendiente'), 0) as saldo
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id=c.id AND ct.tenant_id=$1
            LEFT JOIN om_contratos co ON co.cliente_id=c.id AND co.tenant_id=$1 AND co.estado='activo'
            LEFT JOIN om_grupos g ON g.id=co.grupo_id
            WHERE c.nombre ILIKE $2 OR c.apellidos ILIKE $2 OR c.telefono ILIKE $2
                OR (c.nombre || ' ' || c.apellidos) ILIKE $2
            ORDER BY c.apellidos LIMIT 5
        """, TENANT, f"%{q}%")
    if not rows:
        return {"encontrados": 0, "mensaje": f"No encuentro a nadie con '{q}'"}
    return {
        "encontrados": len(rows),
        "clientes": [{
            "id": str(r["id"]), "nombre": r["nombre"], "apellidos": r["apellidos"],
            "telefono": r["telefono"], "grupo": r["grupo_nombre"],
            "contrato": r["contrato_tipo"], "saldo": float(r["saldo"]),
        } for r in rows]
    }


async def _op_ver_cliente(args: dict) -> dict:
    """Ver detalle completo de un cliente."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()
    async with pool.acquire() as conn:
        c = await conn.fetchrow("SELECT * FROM om_clientes WHERE id=$1", cliente_id)
        if not c:
            return {"error": "Cliente no encontrado"}
        co = await conn.fetchrow("""
            SELECT co.*, g.nombre as grupo FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id=co.grupo_id
            WHERE co.cliente_id=$1 AND co.tenant_id=$2 AND co.estado='activo' LIMIT 1
        """, cliente_id, TENANT)
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
        """, cliente_id, TENANT)
        proximas = await conn.fetch("""
            SELECT s.fecha, s.hora_inicio, g.nombre as grupo
            FROM om_asistencias a JOIN om_sesiones s ON s.id=a.sesion_id
            LEFT JOIN om_grupos g ON g.id=s.grupo_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2
                AND s.fecha >= CURRENT_DATE AND a.estado='confirmada'
            ORDER BY s.fecha LIMIT 5
        """, cliente_id, TENANT)
    return {
        "nombre": c["nombre"], "apellidos": c["apellidos"],
        "telefono": c["telefono"], "email": c.get("email"),
        "contrato": {"tipo": co["tipo"], "grupo": co["grupo"]} if co else None,
        "saldo_pendiente": float(saldo),
        "proximas_clases": [
            {"fecha": str(p["fecha"]), "hora": str(p["hora_inicio"])[:5], "grupo": p["grupo"]}
            for p in proximas
        ],
    }


async def _op_agendar_recurrentes(args: dict) -> dict:
    """Crea sesiones individuales recurrentes."""
    from uuid import UUID
    from datetime import time as dtime
    cliente_id = UUID(args["cliente_id"])
    slots = args["slots"]
    hasta = date.fromisoformat(args["hasta_fecha"])
    desde = date.fromisoformat(args.get("desde_fecha") or str(date.today()))

    pool = await _get_pool()
    async with pool.acquire() as conn:
        contrato = await conn.fetchrow("""
            SELECT id FROM om_contratos
            WHERE cliente_id=$1 AND tenant_id=$2 AND tipo='individual' AND estado='activo'
        """, cliente_id, TENANT)
        contrato_id = contrato["id"] if contrato else None

        sesiones_creadas = 0
        detalles = []

        for slot in slots:
            dia = slot["dia_semana"]
            hi = dtime.fromisoformat(slot["hora_inicio"])
            hf_str = slot.get("hora_fin")
            hf = dtime.fromisoformat(hf_str) if hf_str else dtime(hi.hour + 1, hi.minute)

            fecha = desde
            while fecha <= hasta:
                if fecha.weekday() == dia:
                    exists = await conn.fetchval("""
                        SELECT 1 FROM om_sesiones s
                        JOIN om_asistencias a ON a.sesion_id=s.id
                        WHERE s.fecha=$1 AND s.hora_inicio=$2
                            AND a.cliente_id=$3 AND s.tenant_id=$4
                    """, fecha, hi, cliente_id, TENANT)
                    if not exists:
                        row = await conn.fetchrow("""
                            INSERT INTO om_sesiones (tenant_id, tipo, instructor, fecha, hora_inicio, hora_fin)
                            VALUES ($1, 'individual', 'Jesus', $2, $3, $4) RETURNING id
                        """, TENANT, fecha, hi, hf)
                        await conn.execute("""
                            INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                            VALUES ($1, $2, $3, $4, 'confirmada')
                        """, TENANT, row["id"], cliente_id, contrato_id)
                        sesiones_creadas += 1
                        detalles.append(f"{fecha} {slot['hora_inicio']}")
                fecha += timedelta(days=1)

    dias_nombre = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
    resumen_slots = ", ".join(f"{dias_nombre[s['dia_semana']]} {s['hora_inicio']}" for s in slots)
    return {
        "sesiones_creadas": sesiones_creadas,
        "slots": resumen_slots,
        "hasta": str(hasta),
        "primeras_fechas": detalles[:6],
    }


async def _op_inscribir_grupo(args: dict) -> dict:
    """Inscribir cliente en un grupo."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()

    async with pool.acquire() as conn:
        grupo_id = None

        if args.get("grupo_id"):
            grupo_id = UUID(args["grupo_id"])
        elif args.get("buscar_grupo"):
            busq = args["buscar_grupo"].lower()
            grupos = await conn.fetch("""
                SELECT g.id, g.nombre, g.dias_semana, g.capacidad_max,
                    (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
                FROM om_grupos g
                WHERE g.tenant_id=$1 AND g.estado='activo'
            """, TENANT)
            for g in grupos:
                nombre_lower = (g["nombre"] or "").lower()
                # Extraer hora del primer slot en dias_semana JSON
                dias = g["dias_semana"] or []
                if isinstance(dias, str):
                    dias = json.loads(dias)
                hora_str = dias[0]["hi"] if dias else ""
                if (busq in nombre_lower or busq in hora_str or
                    hora_str.replace(":","h") in busq or hora_str[:2]+"h" in busq):
                    if g["ocu"] < g["capacidad_max"]:
                        grupo_id = g["id"]
                        break
            if not grupo_id:
                return {"error": f"No encuentro grupo con '{args['buscar_grupo']}' con plaza libre"}

        if not grupo_id:
            return {"error": "Necesito grupo_id o buscar_grupo"}

        grupo = await conn.fetchrow("""
            SELECT g.*, (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
            FROM om_grupos g WHERE g.id=$1
        """, grupo_id)
        if not grupo:
            return {"error": "Grupo no encontrado"}
        if grupo["ocu"] >= grupo["capacidad_max"]:
            return {"error": f"Grupo {grupo['nombre']} lleno ({grupo['ocu']}/{grupo['capacidad_max']})"}

        ya = await conn.fetchval("""
            SELECT 1 FROM om_contratos WHERE cliente_id=$1 AND grupo_id=$2 AND estado='activo'
        """, cliente_id, grupo_id)
        if ya:
            return {"error": "Ya está inscrito en este grupo"}

        await conn.execute("""
            INSERT INTO om_contratos (tenant_id, cliente_id, tipo, grupo_id, precio_mensual, fecha_inicio)
            VALUES ($1, $2, 'grupo', $3, $4, CURRENT_DATE)
        """, TENANT, cliente_id, grupo_id, grupo.get("precio_mensual"))

    return {
        "inscrito": True,
        "grupo": grupo["nombre"],
        "precio": float(grupo["precio_mensual"]) if grupo.get("precio_mensual") else None,
        "plazas_restantes": grupo["capacidad_max"] - grupo["ocu"] - 1,
    }


async def _op_ver_grupos(args: dict) -> dict:
    """Listar grupos con plazas y ocupación."""
    solo_con_plaza = args.get("solo_con_plaza", True)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.nombre, g.tipo, g.dias_semana,
                   g.capacidad_max, g.precio_mensual,
                   (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
            ORDER BY g.nombre
        """, TENANT)
    grupos = []
    for r in rows:
        libres = r["capacidad_max"] - r["ocu"]
        if solo_con_plaza and libres <= 0:
            continue
        dias = r["dias_semana"] or []
        if isinstance(dias, str):
            dias = json.loads(dias)
        hora = dias[0]["hi"] if dias else "?"
        grupos.append({
            "id": str(r["id"]), "nombre": r["nombre"],
            "hora": hora,
            "dias": dias,
            "ocupacion": f"{r['ocu']}/{r['capacidad_max']}",
            "libres": libres,
            "precio": float(r["precio_mensual"]) if r["precio_mensual"] else None,
        })
    return {"grupos": grupos}


async def _op_cancelar_sesiones(args: dict) -> dict:
    """Cancelar sesiones de un cliente."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()

    async with pool.acquire() as conn:
        conditions = ["a.cliente_id=$1", "a.tenant_id=$2", "a.estado='confirmada'", "s.fecha >= CURRENT_DATE"]
        params: list = [cliente_id, TENANT]
        idx = 3

        if args.get("sesion_id"):
            conditions.append(f"s.id=${idx}")
            params.append(UUID(args["sesion_id"]))
            idx += 1
        elif args.get("fecha_inicio") and args.get("fecha_fin"):
            conditions.append(f"s.fecha >= ${idx}")
            params.append(date.fromisoformat(args["fecha_inicio"]))
            idx += 1
            conditions.append(f"s.fecha <= ${idx}")
            params.append(date.fromisoformat(args["fecha_fin"]))
            idx += 1

        where = " AND ".join(conditions)
        sesiones = await conn.fetch(f"""
            SELECT a.id as asistencia_id, s.fecha, s.hora_inicio, g.nombre as grupo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id=a.sesion_id
            LEFT JOIN om_grupos g ON g.id=s.grupo_id
            WHERE {where}
            ORDER BY s.fecha
        """, *params)

        if not sesiones:
            return {"canceladas": 0, "mensaje": "No hay sesiones confirmadas que cancelar"}

        for s in sesiones:
            await conn.execute("""
                UPDATE om_asistencias SET estado='cancelada', hora_cancelacion=now() WHERE id=$1
            """, s["asistencia_id"])

    return {
        "canceladas": len(sesiones),
        "sesiones": [
            {"fecha": str(s["fecha"]), "hora": str(s["hora_inicio"])[:5], "grupo": s["grupo"]}
            for s in sesiones
        ],
    }


async def _op_registrar_pago(args: dict) -> dict:
    """Registrar pago con conciliación FIFO."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    monto = float(args["monto"])
    metodo = args["metodo"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow("""
                INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto, notas)
                VALUES ($1, $2, $3, $4, 'Registrado desde cockpit') RETURNING id
            """, TENANT, cliente_id, metodo, monto)
            pago_id = row["id"]

            cargos = await conn.fetch("""
                SELECT id, total FROM om_cargos
                WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
                ORDER BY fecha_cargo ASC
            """, cliente_id, TENANT)

            restante = monto
            conciliados = 0
            for cargo in cargos:
                if restante <= 0:
                    break
                cargo_total = float(cargo["total"])
                aplicado = min(restante, cargo_total)
                await conn.execute("""
                    INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado) VALUES ($1,$2,$3)
                """, pago_id, cargo["id"], aplicado)
                if aplicado >= cargo_total:
                    await conn.execute("""
                        UPDATE om_cargos SET estado='cobrado', fecha_cobro=CURRENT_DATE WHERE id=$1
                    """, cargo["id"])
                    conciliados += 1
                restante -= aplicado

        # Feed
        try:
            nombre = await conn.fetchval("SELECT nombre FROM om_clientes WHERE id=$1", cliente_id)
            from src.pilates.feed import feed_pago
            await feed_pago(nombre or "?", metodo, monto, cliente_id)
        except Exception:
            pass

    return {
        "pago_registrado": True,
        "monto": monto, "metodo": metodo,
        "cargos_conciliados": conciliados,
        "restante": round(restante, 2),
    }


async def _op_generar_facturas(args: dict) -> dict:
    """Generar facturas desde cargos cobrados sin facturar."""
    from uuid import UUID
    import hashlib
    cliente_id = UUID(args["cliente_id"])
    periodo = args.get("periodo")
    pool = await _get_pool()

    async with pool.acquire() as conn:
        conditions = ["c.cliente_id=$1", "c.tenant_id=$2", "c.estado='cobrado'",
                       "NOT EXISTS (SELECT 1 FROM om_factura_lineas fl WHERE fl.cargo_id=c.id)"]
        params: list = [cliente_id, TENANT]
        idx = 3

        if periodo:
            if periodo == "2025":
                conditions.append(f"c.fecha_cargo >= ${idx}")
                params.append(date(2025,1,1)); idx += 1
                conditions.append(f"c.fecha_cargo <= ${idx}")
                params.append(date(2025,12,31)); idx += 1
            elif periodo == "ultimo_mes":
                conditions.append("c.fecha_cargo >= date_trunc('month', CURRENT_DATE) - interval '1 month'")
                conditions.append("c.fecha_cargo < date_trunc('month', CURRENT_DATE)")
            elif len(periodo) == 7:
                conditions.append(f"to_char(c.fecha_cargo, 'YYYY-MM') = ${idx}")
                params.append(periodo); idx += 1

        where = " AND ".join(conditions)
        cargos = await conn.fetch(f"""
            SELECT id, tipo, descripcion, base_imponible, total, fecha_cargo
            FROM om_cargos c WHERE {where} ORDER BY c.fecha_cargo
        """, *params)

        if not cargos:
            return {"facturas_generadas": 0, "mensaje": "No hay cargos cobrados sin facturar"}

        meses: dict = {}
        for c in cargos:
            mes_key = c["fecha_cargo"].strftime("%Y-%m") if c["fecha_cargo"] else "sin_fecha"
            meses.setdefault(mes_key, []).append(c)

        facturas = []
        for mes, cargos_mes in meses.items():
            base_total = sum(float(c["base_imponible"] or c["total"]) for c in cargos_mes)
            iva_pct = 21.0
            iva_total = round(base_total * iva_pct / 100, 2)
            total = round(base_total + iva_total, 2)

            year = date.today().year
            serie = "AP"
            ultimo = await conn.fetchval("""
                SELECT MAX(CAST(SPLIT_PART(numero_factura, '-', 3) AS INT))
                FROM om_facturas WHERE tenant_id=$1 AND serie=$2
                    AND EXTRACT(YEAR FROM fecha_emision) = $3
            """, TENANT, serie, year)
            num = (ultimo or 0) + 1
            numero = f"{serie}-{year}-{num:04d}"

            hash_ant = await conn.fetchval("""
                SELECT verifactu_hash FROM om_facturas
                WHERE tenant_id=$1 AND serie=$2 ORDER BY created_at DESC LIMIT 1
            """, TENANT, serie)
            datos_hash = f"{numero}|{date.today()}|{total}|{hash_ant or 'GENESIS'}"
            vhash = hashlib.sha256(datos_hash.encode()).hexdigest()

            cliente = await conn.fetchrow("SELECT * FROM om_clientes WHERE id=$1", cliente_id)

            fid = await conn.fetchval("""
                INSERT INTO om_facturas (tenant_id, cliente_id, numero_factura, serie,
                    fecha_emision, base_imponible, iva_porcentaje, iva_monto, total,
                    verifactu_hash, verifactu_hash_anterior,
                    cliente_nif, cliente_nombre_fiscal, cliente_direccion)
                VALUES ($1,$2,$3,$4,CURRENT_DATE,$5,$6,$7,$8,$9,$10,$11,$12,$13)
                RETURNING id
            """, TENANT, cliente_id, numero, serie,
                base_total, iva_pct, iva_total, total,
                vhash, hash_ant,
                cliente.get("nif"), f"{cliente['nombre']} {cliente['apellidos']}",
                cliente.get("direccion"))

            for cargo in cargos_mes:
                bi = float(cargo["base_imponible"] or cargo["total"])
                iva_m = round(bi * iva_pct / 100, 2)
                await conn.execute("""
                    INSERT INTO om_factura_lineas (factura_id, cargo_id, concepto, cantidad,
                        precio_unitario, base_imponible, iva_porcentaje, iva_monto, total)
                    VALUES ($1,$2,$3,1,$4,$5,$6,$7,$8)
                """, fid, cargo["id"],
                    cargo["descripcion"] or cargo["tipo"],
                    bi, bi, iva_pct, iva_m, round(bi + iva_m, 2))

            facturas.append({
                "factura_id": str(fid), "numero": numero,
                "mes": mes, "total": total, "lineas": len(cargos_mes),
            })

    return {"facturas_generadas": len(facturas), "facturas": facturas}


async def _op_enviar_whatsapp(args: dict) -> dict:
    """Enviar mensaje o factura por WhatsApp."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()

    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id=$1", cliente_id)
        if not cliente or not cliente["telefono"]:
            return {"error": "Cliente sin teléfono"}

    from src.pilates.whatsapp import enviar_texto, is_configured
    if not is_configured():
        return {"error": "WhatsApp no configurado"}

    if args.get("factura_id"):
        factura_id = UUID(args["factura_id"])
        async with pool.acquire() as conn:
            f = await conn.fetchrow(
                "SELECT numero_factura, total FROM om_facturas WHERE id=$1", factura_id)
        if not f:
            return {"error": "Factura no encontrada"}
        msg = (
            f"Hola {cliente['nombre']}! Te mando tu factura {f['numero_factura']} "
            f"por {float(f['total']):.2f}EUR.\n\n"
            f"Descárgala aquí: https://motor-semantico-omni.fly.dev/pilates/facturas/{factura_id}/pdf"
        )
    elif args.get("mensaje"):
        msg = args["mensaje"]
    else:
        return {"error": "Necesito mensaje o factura_id"}

    result = await enviar_texto(cliente["telefono"], msg, cliente_id)
    return {"enviado": result.get("status") == "sent", "a": cliente["nombre"]}


async def _op_ver_pagos_cliente(args: dict) -> dict:
    """Ver saldo, cargos pendientes y últimos pagos."""
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()
    async with pool.acquire() as conn:
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
        """, cliente_id, TENANT)
        pagos = await conn.fetch("""
            SELECT metodo, monto, fecha_pago FROM om_pagos
            WHERE cliente_id=$1 AND tenant_id=$2 ORDER BY fecha_pago DESC LIMIT 5
        """, cliente_id, TENANT)
        cargos_pend = await conn.fetch("""
            SELECT tipo, descripcion, total FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
            ORDER BY fecha_cargo LIMIT 5
        """, cliente_id, TENANT)
    return {
        "saldo_pendiente": float(saldo),
        "cargos_pendientes": [{"tipo": c["tipo"], "desc": c["descripcion"], "total": float(c["total"])} for c in cargos_pend],
        "ultimos_pagos": [{"metodo": p["metodo"], "monto": float(p["monto"]), "fecha": str(p["fecha_pago"])} for p in pagos],
    }


# ============================================================
# TOOLS VOZ — dispatch functions (B-PIL-20e)
# ============================================================

async def _op_voz_estrategia(args: dict) -> dict:
    """Devuelve estrategia activa + calendario."""
    from src.pilates.voz_estrategia import obtener_estrategia_activa
    result = await obtener_estrategia_activa()
    if "error" in result:
        return result
    # Simplificar para el LLM del cockpit
    est = result.get("estrategia", {})
    cal = result.get("calendario", [])
    return {
        "foco": est.get("foco_principal", "sin_estrategia"),
        "narrativa": est.get("narrativa", ""),
        "canales": est.get("canales_prioridad", []),
        "evitar": est.get("evitar", []),
        "calendario": [
            {
                "canal": c["canal"],
                "tipo": c["tipo"],
                "titulo": c["titulo"],
                "dia": c["dia"],
                "estado": c["estado"],
            }
            for c in cal[:8]
        ],
        "total_items": len(cal),
    }


async def _op_voz_senales(args: dict) -> dict:
    """Devuelve señales pendientes priorizadas."""
    from src.pilates.voz_ciclos import priorizar
    result = await priorizar()
    return {
        "total": result.get("total", 0),
        "criticas": result.get("criticas", 0),
        "altas": result.get("altas", 0),
        "senales": [
            {"tipo": s["tipo"], "urgencia": s["urgencia"], "resumen": s["resumen"]}
            for s in result.get("senales", [])[:10]
        ],
    }


async def _op_voz_isp(args: dict) -> dict:
    """Devuelve ISP automático."""
    from src.pilates.voz_ciclos import calcular_isp_automatico
    return await calcular_isp_automatico()


async def _op_voz_recalcular(args: dict) -> dict:
    """Recalcula estrategia semanal."""
    from src.pilates.voz_estrategia import calcular_estrategia
    return await calcular_estrategia()


async def _op_voz_generar_perfiles(args: dict) -> dict:
    """Genera perfiles de canales."""
    canal = args.get("canal", "")
    if canal:
        from src.pilates.voz_arquitecto import generar_perfil
        return await generar_perfil(canal)
    else:
        from src.pilates.voz_arquitecto import generar_todos_los_perfiles
        return await generar_todos_los_perfiles()


async def _op_voz_ciclo(args: dict) -> dict:
    """Ejecuta ciclo completo."""
    from src.pilates.voz_ciclos import ejecutar_ciclo_completo
    return await ejecutar_ciclo_completo()


async def _op_voz_collectors(args: dict) -> dict:
    """Ejecuta collectors de métricas de canales."""
    from src.pilates.collectors import collect_all
    return await collect_all()


# Dispatch operativo
TOOL_DISPATCH = {
    "buscar_cliente": _op_buscar_cliente,
    "ver_cliente": _op_ver_cliente,
    "agendar_sesiones_recurrentes": _op_agendar_recurrentes,
    "inscribir_en_grupo": _op_inscribir_grupo,
    "ver_grupos": _op_ver_grupos,
    "cancelar_sesiones_cliente": _op_cancelar_sesiones,
    "registrar_pago": _op_registrar_pago,
    "generar_facturas": _op_generar_facturas,
    "enviar_whatsapp": _op_enviar_whatsapp,
    "ver_pagos_cliente": _op_ver_pagos_cliente,
    "voz_estrategia": _op_voz_estrategia,
    "voz_senales": _op_voz_senales,
    "voz_isp": _op_voz_isp,
    "voz_recalcular": _op_voz_recalcular,
    "voz_generar_perfiles": _op_voz_generar_perfiles,
    "voz_ciclo": _op_voz_ciclo,
    "voz_collectors": _op_voz_collectors,
}


async def chat_cockpit(mensaje: str, modulos_activos: list,
                        historial: list = None) -> dict:
    """Chat conversacional del cockpit — interfaz + operaciones."""
    t0 = time.time()

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

    for _ in range(5):
        try:
            async with httpx.AsyncClient(timeout=45) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": CHAT_MODEL,
                        "messages": messages,
                        "tools": TOOLS_COCKPIT,
                        "max_tokens": 800,
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
            elif fn_name in TOOL_DISPATCH:
                try:
                    result = await TOOL_DISPATCH[fn_name](fn_args)
                except Exception as e:
                    log.error("cockpit_tool_error", tool=fn_name, error=str(e))
                    result = {"error": f"Error ejecutando {fn_name}: {str(e)}"}
            else:
                result = {"error": f"Herramienta desconocida: {fn_name}"}

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
