"""Portal Conversacional — Interfaz LLM con function calling.

El cliente escribe lo que necesita, un LLM decide qué herramientas usar
y devuelve respuesta conversacional + datos estructurados.

Fuente: Exocortex v2.1 B-PIL-18.
"""
from __future__ import annotations

import json
import os
import time
import structlog
import httpx
from datetime import date, datetime, timedelta, time as dtime
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
CHAT_MODEL = os.getenv("PORTAL_CHAT_MODEL", "deepseek/deepseek-chat")


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# HERRAMIENTAS (function calling) — Queries directas a DB
# ============================================================

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "ver_proximas_clases",
            "description": "Ver las próximas clases del cliente en los próximos N días. Usar cuando pregunte por su horario, cuándo es su próxima clase, qué tiene esta semana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dias": {
                        "type": "integer",
                        "description": "Número de días a consultar (default 7, max 30)",
                        "default": 7
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancelar_sesion",
            "description": "Cancelar una sesión específica del cliente. SIEMPRE pedir confirmación antes mostrando fecha y hora. Nunca ejecutar sin que el cliente confirme.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sesion_id": {
                        "type": "string",
                        "description": "UUID de la sesión a cancelar"
                    }
                },
                "required": ["sesion_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_huecos_recuperacion",
            "description": "Buscar sesiones con plaza libre para recuperar. Usar tras cancelación o cuando el cliente busca alternativas. Puede buscar en un rango de días.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dias": {
                        "type": "integer",
                        "description": "Días a buscar hacia adelante (default 14)",
                        "default": 14
                    },
                    "dia_semana": {
                        "type": "integer",
                        "description": "Filtrar por día de la semana: 0=lunes, 1=martes... Omitir para todos."
                    },
                    "franja": {
                        "type": "string",
                        "enum": ["manana", "tarde"],
                        "description": "Filtrar por franja horaria. manana=antes de 14:00, tarde=14:00 o después. Omitir para todas."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "solicitar_recuperacion",
            "description": "Inscribir al cliente en una sesión como recuperación. SIEMPRE pedir confirmación antes mostrando fecha, hora y grupo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sesion_id": {
                        "type": "string",
                        "description": "UUID de la sesión donde recuperar"
                    }
                },
                "required": ["sesion_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_saldo_y_pagos",
            "description": "Consultar saldo pendiente y últimos pagos del cliente. Usar cuando pregunte cuánto debe, historial de pagos, o quiera pagar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite_pagos": {
                        "type": "integer",
                        "description": "Número de pagos recientes a mostrar (default 5)",
                        "default": 5
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ver_facturas",
            "description": "Listar facturas del cliente. Usar cuando pida facturas o necesite un justificante.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limite": {
                        "type": "integer",
                        "description": "Número de facturas a mostrar (default 5)",
                        "default": 5
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_factura_whatsapp",
            "description": "Enviar una factura específica al cliente por WhatsApp. Usar cuando pida que le manden la factura.",
            "parameters": {
                "type": "object",
                "properties": {
                    "factura_id": {
                        "type": "string",
                        "description": "UUID de la factura a enviar"
                    }
                },
                "required": ["factura_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "resumen_mensual",
            "description": "Resumen completo del mes: asistencia, faltas, recuperaciones, saldo, próximas clases. Usar cuando pregunte cómo va, resumen del mes, o algo general.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mes": {
                        "type": "string",
                        "description": "Mes en formato YYYY-MM (default: mes actual)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crear_lista_espera",
            "description": "Apuntar al cliente en lista de espera. Se le notificará por WhatsApp cuando se libere un hueco que encaje. Usar cuando no le encaje ningún hueco disponible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dia_semana": {
                        "type": "integer",
                        "description": "Día preferido: 0=lunes, 1=martes... Omitir para cualquier día."
                    },
                    "franja": {
                        "type": "string",
                        "enum": ["manana", "tarde", "cualquiera"],
                        "description": "Franja horaria preferida",
                        "default": "cualquiera"
                    },
                    "notas": {
                        "type": "string",
                        "description": "Notas adicionales del cliente sobre su preferencia"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancelar_periodo",
            "description": "Cancelar todas las sesiones en un rango de fechas (vacaciones, viaje, etc). Sin cargo si se avisa con antelación. SIEMPRE pedir confirmación mostrando las sesiones afectadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fecha_inicio": {
                        "type": "string",
                        "description": "Fecha inicio en formato YYYY-MM-DD"
                    },
                    "fecha_fin": {
                        "type": "string",
                        "description": "Fecha fin en formato YYYY-MM-DD"
                    }
                },
                "required": ["fecha_inicio", "fecha_fin"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_grupos_disponibles",
            "description": "Buscar grupos con plazas libres, opcionalmente filtrados por franja. Usar cuando el cliente quiera cambiar de grupo o ver opciones.",
            "parameters": {
                "type": "object",
                "properties": {
                    "franja": {
                        "type": "string",
                        "enum": ["manana", "tarde"],
                        "description": "Filtrar por franja. Omitir para todos."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_solicitud",
            "description": "Registrar una solicitud del cliente que requiere acción de Jesús (cambio de grupo, baja, cambio horario, etc). Se notifica a Jesús por WhatsApp.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["cambio_grupo", "baja", "pausa", "cambio_horario", "otro"],
                        "description": "Tipo de solicitud"
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Descripción detallada de lo que quiere el cliente"
                    }
                },
                "required": ["tipo", "descripcion"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "iniciar_pago_tarjeta",
            "description": "Iniciar configuración de pago recurrente con tarjeta (Stripe). Genera un enlace para que el cliente registre su tarjeta de forma segura. Usar cuando pregunte por pago automático o quiera pagar con tarjeta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dia_cobro": {
                        "type": "integer",
                        "description": "Día del mes para el cobro (1-28, default 5)",
                        "default": 5
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "estado_pago_recurrente",
            "description": "Consultar el estado del pago recurrente del cliente (si tiene tarjeta configurada, último cobro, intentos fallidos). Usar cuando pregunte por su pago automático o tarjeta.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


# ============================================================
# IMPLEMENTACIÓN DE CADA HERRAMIENTA
# ============================================================

async def _tool_ver_proximas_clases(cliente_id: UUID, args: dict) -> dict:
    dias = min(args.get("dias", 7), 30)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tipo,
                   g.nombre as grupo_nombre, a.estado as asistencia_estado
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= CURRENT_DATE AND s.fecha <= CURRENT_DATE + $3::int
            ORDER BY s.fecha, s.hora_inicio
        """, cliente_id, TENANT, dias)
    return {
        "clases": [
            {"sesion_id": str(r["id"]), "fecha": str(r["fecha"]),
             "dia": ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][r["fecha"].weekday()],
             "hora": str(r["hora_inicio"])[:5], "hora_fin": str(r["hora_fin"])[:5] if r["hora_fin"] else None,
             "tipo": r["tipo"], "grupo": r["grupo_nombre"],
             "estado": r["asistencia_estado"]}
            for r in rows
        ]
    }


async def _tool_cancelar_sesion(cliente_id: UUID, args: dict) -> dict:
    sesion_id = UUID(args["sesion_id"])
    pool = await _get_pool()
    async with pool.acquire() as conn:
        asistencia = await conn.fetchrow("""
            SELECT a.id, s.fecha, s.hora_inicio, s.tipo, g.nombre as grupo_nombre
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.sesion_id = $1 AND a.cliente_id = $2 AND a.estado = 'confirmada'
        """, sesion_id, cliente_id)
        if not asistencia:
            return {"error": "Sesión no encontrada o ya cancelada"}
        if asistencia["fecha"] < date.today():
            return {"error": "No se pueden cancelar sesiones pasadas"}

        sesion_dt = datetime.combine(asistencia["fecha"], asistencia["hora_inicio"])
        horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600
        hay_cargo = horas_antes < 12 and asistencia["tipo"] == "individual"

        async with conn.transaction():
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'cancelada', hora_cancelacion = now()
                WHERE id = $1
            """, asistencia["id"])
            if hay_cargo:
                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, tipo, descripcion, base_imponible, sesion_id)
                    VALUES ($1, $2, 'cancelacion_tardia', $3, 35.00, $4)
                """, TENANT, cliente_id, f"Cancelación tardía {asistencia['fecha']}", sesion_id)

    # Feed + check lista espera
    try:
        from src.pilates.feed import feed_cancelacion
        await feed_cancelacion("Cliente", str(asistencia["fecha"]),
                               str(asistencia["hora_inicio"])[:5], cliente_id)
        from src.pilates.automatismos import check_lista_espera
        await check_lista_espera()
    except Exception:
        pass

    return {
        "cancelada": True,
        "fecha": str(asistencia["fecha"]),
        "hora": str(asistencia["hora_inicio"])[:5],
        "grupo": asistencia["grupo_nombre"],
        "cargo": hay_cargo,
        "mensaje": "Cancelación tardía — se aplica cargo" if hay_cargo else "Cancelada sin cargo"
    }


async def _tool_buscar_huecos(cliente_id: UUID, args: dict) -> dict:
    dias = min(args.get("dias", 14), 30)
    dia_semana = args.get("dia_semana")
    franja = args.get("franja")
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Check si puede recuperar
        mes = date.today().replace(day=1)
        faltas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2 AND a.estado='no_vino' AND s.fecha >= $3
        """, cliente_id, TENANT, mes)
        recuperadas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2 AND a.es_recuperacion=true
                AND a.estado='asistio' AND s.fecha >= $3
        """, cliente_id, TENANT, mes)

        hoy = date.today()
        rows = await conn.fetch("""
            SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin,
                   g.nombre as grupo_nombre, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a2
                    WHERE a2.sesion_id = s.id AND a2.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id=$1 AND s.fecha > $2 AND s.fecha <= $2 + $3::int AND s.estado='programada'
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, hoy, dias)

        huecos = []
        for r in rows:
            if r["ocupadas"] >= r["capacidad_max"]:
                continue
            if dia_semana is not None and r["fecha"].weekday() != dia_semana:
                continue
            if franja == "manana" and r["hora_inicio"] >= dtime(14, 0):
                continue
            if franja == "tarde" and r["hora_inicio"] < dtime(14, 0):
                continue
            # Skip si cliente ya está inscrito
            ya = await conn.fetchval(
                "SELECT 1 FROM om_asistencias WHERE sesion_id=$1 AND cliente_id=$2",
                r["id"], cliente_id)
            if ya:
                continue
            huecos.append({
                "sesion_id": str(r["id"]),
                "fecha": str(r["fecha"]),
                "dia": ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][r["fecha"].weekday()],
                "hora": str(r["hora_inicio"])[:5],
                "grupo": r["grupo_nombre"],
                "plazas_libres": r["capacidad_max"] - r["ocupadas"],
            })

    return {
        "puede_recuperar": recuperadas < faltas,
        "faltas_pendientes": max(faltas - recuperadas, 0),
        "huecos": huecos[:15],  # max 15 resultados
    }


async def _tool_solicitar_recuperacion(cliente_id: UUID, args: dict) -> dict:
    sesion_id = UUID(args["sesion_id"])
    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesion = await conn.fetchrow("""
            SELECT s.*, g.capacidad_max, g.nombre as grupo_nombre,
                (SELECT count(*) FROM om_asistencias a
                 WHERE a.sesion_id=s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.id=$1 AND s.tenant_id=$2
        """, sesion_id, TENANT)
        if not sesion:
            return {"error": "Sesión no encontrada"}
        if sesion["ocupadas"] >= sesion["capacidad_max"]:
            return {"error": "Ya no hay plaza en este grupo"}
        ya = await conn.fetchval(
            "SELECT 1 FROM om_asistencias WHERE sesion_id=$1 AND cliente_id=$2", sesion_id, cliente_id)
        if ya:
            return {"error": "Ya estás inscrito en esta sesión"}

        await conn.execute("""
            INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id, estado, es_recuperacion)
            VALUES ($1, $2, $3, 'recuperacion', true)
        """, TENANT, sesion_id, cliente_id)

    return {
        "inscrito": True,
        "fecha": str(sesion["fecha"]),
        "hora": str(sesion["hora_inicio"])[:5],
        "grupo": sesion["grupo_nombre"],
    }


async def _tool_ver_saldo_y_pagos(cliente_id: UUID, args: dict) -> dict:
    limite = args.get("limite_pagos", 5)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
        """, cliente_id, TENANT)
        pagos = await conn.fetch("""
            SELECT metodo, monto, fecha_pago, notas FROM om_pagos
            WHERE cliente_id=$1 AND tenant_id=$2
            ORDER BY fecha_pago DESC LIMIT $3
        """, cliente_id, TENANT, limite)
        # Cargos pendientes detallados
        cargos = await conn.fetch("""
            SELECT tipo, descripcion, total FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
            ORDER BY created_at DESC LIMIT 5
        """, cliente_id, TENANT)
    return {
        "saldo_pendiente": float(saldo),
        "cargos_pendientes": [{"tipo": c["tipo"], "descripcion": c["descripcion"],
                                "total": float(c["total"])} for c in cargos],
        "ultimos_pagos": [{"metodo": p["metodo"], "monto": float(p["monto"]),
                           "fecha": str(p["fecha_pago"])} for p in pagos],
        "instrucciones_bizum": f"Envía {float(saldo):.2f}€ por Bizum al 600XXXXXX con concepto 'Pilates'" if float(saldo) > 0 else None,
    }


async def _tool_ver_facturas(cliente_id: UUID, args: dict) -> dict:
    limite = args.get("limite", 5)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, numero_factura, fecha_emision, total, estado
            FROM om_facturas
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='emitida'
            ORDER BY fecha_emision DESC LIMIT $3
        """, cliente_id, TENANT, limite)
    return {
        "facturas": [
            {"factura_id": str(r["id"]), "numero": r["numero_factura"],
             "fecha": str(r["fecha_emision"]), "total": float(r["total"]),
             "pdf_url": f"/pilates/facturas/{r['id']}/pdf"}
            for r in rows
        ]
    }


async def _tool_enviar_factura_wa(cliente_id: UUID, args: dict, telefono: str) -> dict:
    factura_id = UUID(args["factura_id"])
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow("""
            SELECT numero_factura, total, fecha_emision FROM om_facturas
            WHERE id=$1 AND cliente_id=$2 AND tenant_id=$3
        """, factura_id, cliente_id, TENANT)
        if not factura:
            return {"error": "Factura no encontrada"}

    from src.pilates.whatsapp import enviar_texto
    msg = (
        f"📄 Factura {factura['numero_factura']}\n"
        f"Fecha: {factura['fecha_emision']}\n"
        f"Total: {float(factura['total']):.2f}€\n\n"
        f"Descárgala aquí: https://motor-semantico-omni.fly.dev/pilates/facturas/{factura_id}/pdf"
    )
    result = await enviar_texto(telefono, msg, cliente_id)
    return {"enviada": result.get("status") == "sent", "numero": factura["numero_factura"]}


async def _tool_resumen_mensual(cliente_id: UUID, args: dict) -> dict:
    mes_str = args.get("mes")
    if mes_str:
        mes = date.fromisoformat(mes_str + "-01")
    else:
        mes = date.today().replace(day=1)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT count(*) as total,
                count(*) FILTER (WHERE a.estado='asistio') as asistidas,
                count(*) FILTER (WHERE a.estado='no_vino') as faltas,
                count(*) FILTER (WHERE a.estado='cancelada') as canceladas,
                count(*) FILTER (WHERE a.es_recuperacion=true AND a.estado='asistio') as recuperaciones
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2
                AND s.fecha >= $3 AND s.fecha < $3 + interval '1 month'
        """, cliente_id, TENANT, mes)
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
        """, cliente_id, TENANT)
        proximas = await conn.fetch("""
            SELECT s.fecha, s.hora_inicio, g.nombre as grupo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2
                AND s.fecha >= CURRENT_DATE AND s.fecha <= CURRENT_DATE + 7
                AND a.estado = 'confirmada'
            ORDER BY s.fecha, s.hora_inicio LIMIT 5
        """, cliente_id, TENANT)
        contrato = await conn.fetchrow("""
            SELECT g.nombre as grupo, g.dias_semana FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.cliente_id=$1 AND co.tenant_id=$2 AND co.estado='activo' LIMIT 1
        """, cliente_id, TENANT)

    return {
        "mes": str(mes),
        "asistencia": {
            "total_programadas": stats["total"] if stats else 0,
            "asistidas": stats["asistidas"] if stats else 0,
            "faltas": stats["faltas"] if stats else 0,
            "canceladas": stats["canceladas"] if stats else 0,
            "recuperaciones": stats["recuperaciones"] if stats else 0,
            "porcentaje": round((stats["asistidas"] or 0) / max(stats["total"] or 1, 1) * 100)
        },
        "saldo_pendiente": float(saldo),
        "grupo_actual": contrato["grupo"] if contrato else None,
        "proximas_clases": [
            {"fecha": str(p["fecha"]),
             "dia": ["lun","mar","mié","jue","vie","sáb","dom"][p["fecha"].weekday()],
             "hora": str(p["hora_inicio"])[:5], "grupo": p["grupo"]}
            for p in proximas
        ],
    }


async def _tool_crear_lista_espera(cliente_id: UUID, args: dict) -> dict:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Verificar que no tenga ya una activa con mismos criterios
        existing = await conn.fetchval("""
            SELECT id FROM om_lista_espera
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='activa'
                AND dia_semana IS NOT DISTINCT FROM $3
                AND franja IS NOT DISTINCT FROM $4
        """, cliente_id, TENANT,
            args.get("dia_semana"), args.get("franja", "cualquiera"))
        if existing:
            return {"ya_existia": True, "mensaje": "Ya tienes una alerta activa con esos criterios"}

        await conn.execute("""
            INSERT INTO om_lista_espera (tenant_id, cliente_id, dia_semana, franja, notas)
            VALUES ($1, $2, $3, $4, $5)
        """, TENANT, cliente_id,
            args.get("dia_semana"),
            args.get("franja", "cualquiera"),
            args.get("notas"))

    dias_nombre = {0:"lunes",1:"martes",2:"miércoles",3:"jueves",4:"viernes",5:"sábado",6:"domingo"}
    dia_str = dias_nombre.get(args.get("dia_semana"), "cualquier día")
    franja_str = args.get("franja", "cualquiera")
    return {
        "creada": True,
        "preferencia": f"{dia_str} por la {franja_str}" if franja_str != "cualquiera" else dia_str,
        "mensaje": "Te avisaré por WhatsApp cuando se libere un hueco que encaje"
    }


async def _tool_cancelar_periodo(cliente_id: UUID, args: dict) -> dict:
    fecha_inicio = date.fromisoformat(args["fecha_inicio"])
    fecha_fin = date.fromisoformat(args["fecha_fin"])
    if fecha_inicio < date.today():
        return {"error": "No se pueden cancelar fechas pasadas"}
    if (fecha_fin - fecha_inicio).days > 60:
        return {"error": "Máximo 60 días de cancelación"}

    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT a.id, s.fecha, s.hora_inicio, g.nombre as grupo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id=$1 AND a.tenant_id=$2
                AND s.fecha >= $3 AND s.fecha <= $4
                AND a.estado = 'confirmada'
            ORDER BY s.fecha
        """, cliente_id, TENANT, fecha_inicio, fecha_fin)

        if not sesiones:
            return {"canceladas": 0, "mensaje": "No tienes sesiones en ese período"}

        async with conn.transaction():
            for s in sesiones:
                await conn.execute("""
                    UPDATE om_asistencias SET estado='cancelada', hora_cancelacion=now()
                    WHERE id=$1
                """, s["id"])

    return {
        "canceladas": len(sesiones),
        "periodo": f"{fecha_inicio} a {fecha_fin}",
        "sesiones": [
            {"fecha": str(s["fecha"]), "hora": str(s["hora_inicio"])[:5], "grupo": s["grupo"]}
            for s in sesiones
        ],
        "mensaje": f"Canceladas {len(sesiones)} sesiones sin cargo (vacaciones/ausencia)"
    }


async def _tool_buscar_grupos(cliente_id: UUID, args: dict) -> dict:
    franja = args.get("franja")
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.nombre, g.dias_semana, g.hora_inicio, g.hora_fin,
                   g.capacidad_max,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id=g.id AND c.estado='activo') as inscritos
            FROM om_grupos g
            WHERE g.tenant_id=$1 AND g.estado='activo' AND g.tipo='grupo'
            ORDER BY g.hora_inicio
        """, TENANT)

    grupos = []
    for r in rows:
        if r["inscritos"] >= r["capacidad_max"]:
            continue
        if franja == "manana" and r["hora_inicio"] and r["hora_inicio"] >= dtime(14, 0):
            continue
        if franja == "tarde" and r["hora_inicio"] and r["hora_inicio"] < dtime(14, 0):
            continue
        grupos.append({
            "grupo_id": str(r["id"]),
            "nombre": r["nombre"],
            "dias": r["dias_semana"],
            "hora": str(r["hora_inicio"])[:5] if r["hora_inicio"] else "?",
            "plazas_libres": r["capacidad_max"] - r["inscritos"],
        })
    return {"grupos_disponibles": grupos}


async def _tool_registrar_solicitud(cliente_id: UUID, args: dict, nombre_cliente: str) -> dict:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_procesos (tenant_id, area, titulo, descripcion, pasos, documentado_por)
            VALUES ($1, 'cliente', $2, $3, '[]'::jsonb, 'portal_chat')
        """, TENANT,
            f"Solicitud {args['tipo']} — {nombre_cliente}",
            args["descripcion"])

    # Notificar a Jesús por WA
    from src.pilates.whatsapp import enviar_texto
    jesus_tel = os.getenv("JESUS_TELEFONO", "")
    if jesus_tel:
        msg = f"📋 Solicitud de {nombre_cliente}: {args['tipo']}\n{args['descripcion']}"
        await enviar_texto(jesus_tel, msg)

    # Feed
    try:
        from src.pilates.feed import feed_solicitud
        await feed_solicitud(nombre_cliente, args["tipo"], args["descripcion"], cliente_id)
    except Exception:
        pass

    return {"registrada": True, "tipo": args["tipo"],
            "mensaje": "Solicitud registrada. Jesús te contactará pronto."}


async def _tool_iniciar_pago_tarjeta(cliente_id: UUID, args: dict, token: str) -> dict:
    dia_cobro = args.get("dia_cobro", 5)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Check si ya tiene pago recurrente activo
        existing = await conn.fetchval("""
            SELECT id FROM om_pago_recurrente
            WHERE cliente_id=$1 AND tenant_id=$2 AND estado='activo'
        """, cliente_id, TENANT)
        if existing:
            return {"ya_configurado": True,
                    "mensaje": "Ya tienes pago automático configurado. Si quieres cambiarlo, contacta con el estudio."}

        # Get importe from contrato
        importe = await conn.fetchval("""
            SELECT COALESCE(co.precio_mensual, g.precio_mensual)
            FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.cliente_id=$1 AND co.tenant_id=$2 AND co.estado='activo' LIMIT 1
        """, cliente_id, TENANT)

    from src.pilates.stripe_pagos import crear_checkout_session
    result = await crear_checkout_session(cliente_id, token,
                                           importe=float(importe) if importe else None,
                                           dia_cobro=dia_cobro)
    if result.get("error"):
        return result

    return {
        "checkout_url": result["checkout_url"],
        "dia_cobro": dia_cobro,
        "importe": float(importe) if importe else None,
        "mensaje": f"Accede a este enlace para registrar tu tarjeta de forma segura. Se cobrará el día {dia_cobro} de cada mes."
    }


async def _tool_estado_pago_recurrente(cliente_id: UUID, args: dict) -> dict:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        pr = await conn.fetchrow("""
            SELECT estado, dia_cobro, importe, ultimo_cobro, ultimo_resultado,
                   intentos_fallidos, stripe_payment_method_id
            FROM om_pago_recurrente
            WHERE cliente_id=$1 AND tenant_id=$2
            ORDER BY created_at DESC LIMIT 1
        """, cliente_id, TENANT)
    if not pr:
        return {"configurado": False,
                "mensaje": "No tienes pago automático configurado. ¿Quieres activarlo?"}
    return {
        "configurado": True,
        "estado": pr["estado"],
        "dia_cobro": pr["dia_cobro"],
        "importe": float(pr["importe"]) if pr["importe"] else None,
        "ultimo_cobro": str(pr["ultimo_cobro"]) if pr["ultimo_cobro"] else None,
        "ultimo_resultado": pr["ultimo_resultado"],
        "intentos_fallidos": pr["intentos_fallidos"],
        "tarjeta": "****" if pr["stripe_payment_method_id"] else None,
    }


# ============================================================
# DISPATCH — Ejecuta la herramienta correcta
# ============================================================

TOOL_DISPATCH = {
    "ver_proximas_clases": _tool_ver_proximas_clases,
    "cancelar_sesion": _tool_cancelar_sesion,
    "buscar_huecos_recuperacion": _tool_buscar_huecos,
    "solicitar_recuperacion": _tool_solicitar_recuperacion,
    "ver_saldo_y_pagos": _tool_ver_saldo_y_pagos,
    "ver_facturas": _tool_ver_facturas,
    "resumen_mensual": _tool_resumen_mensual,
    "crear_lista_espera": _tool_crear_lista_espera,
    "cancelar_periodo": _tool_cancelar_periodo,
    "buscar_grupos_disponibles": _tool_buscar_grupos,
    "estado_pago_recurrente": _tool_estado_pago_recurrente,
}

# Estas necesitan args extra
TOOL_SPECIAL = {
    "enviar_factura_whatsapp": _tool_enviar_factura_wa,  # + telefono
    "registrar_solicitud": _tool_registrar_solicitud,    # + nombre_cliente
    "iniciar_pago_tarjeta": _tool_iniciar_pago_tarjeta,  # + token
}


async def ejecutar_tool(nombre: str, cliente_id: UUID, args: dict,
                         telefono: str = "", nombre_cliente: str = "",
                         token: str = "") -> dict:
    if nombre in TOOL_DISPATCH:
        return await TOOL_DISPATCH[nombre](cliente_id, args)
    elif nombre == "enviar_factura_whatsapp":
        return await _tool_enviar_factura_wa(cliente_id, args, telefono)
    elif nombre == "registrar_solicitud":
        return await _tool_registrar_solicitud(cliente_id, args, nombre_cliente)
    elif nombre == "iniciar_pago_tarjeta":
        return await _tool_iniciar_pago_tarjeta(cliente_id, args, token)
    else:
        return {"error": f"Herramienta desconocida: {nombre}"}


# ============================================================
# MOTOR CONVERSACIONAL — Loop principal
# ============================================================

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
"""

SYSTEM_PROMPT = TONO_ALBELDA + """
Eres el asistente de Authentic Pilates en Albelda de Iregua. Hablas con {nombre}, cliente del estudio.

Reglas CRÍTICAS:
1. Para CANCELAR una sesión o INSCRIBIR en recuperación: PRIMERO muestra los detalles (fecha, hora, grupo) y PREGUNTA "¿Confirmo?". NUNCA ejecutes sin confirmación.
2. Para cancelar período (vacaciones): muestra TODAS las sesiones afectadas y pide confirmación.
3. Si el cliente dice "sí", "confirma", "dale" después de que hayas mostrado detalles → ejecuta la acción.
4. Si no encuentras huecos que encajen → ofrece crear alerta en lista de espera.
5. Tras cancelar una sesión → sugiere automáticamente buscar huecos para recuperar.
6. Para pagos → muestra saldo + instrucciones Bizum exactas.
7. Si el cliente pide algo que no puedes resolver → registra solicitud para Jesús.
8. Para pago con tarjeta → usa iniciar_pago_tarjeta para generar enlace seguro.

Datos del cliente:
- Nombre: {nombre} {apellidos}
- Grupo actual: {grupo}
- Contrato: {contrato_tipo}

Hoy es {hoy}. Frases cortas, ve al grano."""


async def chat(token: str, mensaje: str, historial: list[dict] = None) -> dict:
    """Endpoint principal del portal conversacional.

    Args:
        token: Token del portal del cliente
        mensaje: Texto libre del cliente
        historial: Mensajes previos de la conversación [{role, content}]

    Returns:
        {respuesta, datos, acciones_pendientes, historial_actualizado}
    """
    t0 = time.time()

    # 1. Verificar token y obtener datos del cliente
    from src.pilates.portal import _verificar_token
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    nombre = link["nombre"]
    apellidos = link.get("apellidos", "")
    telefono = link.get("telefono", "")

    # Obtener grupo actual
    pool = await _get_pool()
    async with pool.acquire() as conn:
        contrato = await conn.fetchrow("""
            SELECT co.tipo, g.nombre as grupo FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.cliente_id=$1 AND co.tenant_id=$2 AND co.estado='activo' LIMIT 1
        """, cliente_id, TENANT)

    grupo = contrato["grupo"] if contrato else "Sin grupo"
    contrato_tipo = contrato["tipo"] if contrato else "Sin contrato"

    system = SYSTEM_PROMPT.format(
        nombre=nombre, apellidos=apellidos, grupo=grupo,
        contrato_tipo=contrato_tipo, hoy=date.today().strftime("%A %d de %B de %Y")
    )

    # Engagement: registrar evento + contexto + proactividad saldo
    try:
        from src.pilates.engagement import registrar_evento, obtener_contexto_engagement
        await registrar_evento(cliente_id, "portal_chat", {"mensaje": mensaje[:100]})
        contexto_eng = await obtener_contexto_engagement(cliente_id)
        if contexto_eng:
            system += f"\n\nCONTEXTO SOBRE ESTE CLIENTE (usa discretamente):\n{contexto_eng}"
    except Exception:
        pass

    # Proactividad saldo
    try:
        async with pool.acquire() as conn2:
            saldo_pendiente = await conn2.fetchval("""
                SELECT COALESCE(SUM(total), 0) FROM om_cargos
                WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
            """, cliente_id, TENANT)
        if float(saldo_pendiente) > 0:
            system += f"\n\n{nombre} tiene {float(saldo_pendiente):.2f}EUR pendientes. "
            system += "Si el contexto lo permite, menciona el saldo y ofrece configurar pago automático."
    except Exception:
        pass

    # 2. Construir mensajes
    messages = [{"role": "system", "content": system}]
    if historial:
        messages.extend(historial[-20:])  # max 20 mensajes de contexto
    messages.append({"role": "user", "content": mensaje})

    # 3. Llamar LLM con function calling (loop hasta respuesta final)
    tools_usadas = []
    datos_acumulados = {}
    max_iterations = 5  # safety limit

    for i in range(max_iterations):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                    json={
                        "model": CHAT_MODEL,
                        "messages": messages,
                        "tools": TOOLS_SPEC,
                        "max_tokens": 800,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

        except Exception as e:
            log.error("portal_chat_llm_error", error=str(e))
            return {
                "respuesta": "Perdona, ha habido un problema técnico. Inténtalo de nuevo o contacta con el estudio.",
                "datos": {},
                "historial": historial or [],
            }

        choice = data["choices"][0]
        msg = choice["message"]

        # Si no hay tool calls → respuesta final
        if not msg.get("tool_calls"):
            respuesta_texto = msg.get("content", "")
            break

        # Ejecutar tool calls
        messages.append(msg)  # assistant message con tool_calls

        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"]) if tc["function"].get("arguments") else {}

            log.info("portal_chat_tool", tool=fn_name, args=fn_args, cliente=nombre)
            result = await ejecutar_tool(fn_name, cliente_id, fn_args,
                                          telefono=telefono, nombre_cliente=f"{nombre} {apellidos}",
                                          token=token)

            tools_usadas.append(fn_name)
            datos_acumulados[fn_name] = result

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
    else:
        respuesta_texto = "He intentado varias cosas pero no he podido resolver tu petición. ¿Puedes reformularla?"

    # 4. Actualizar historial
    nuevo_historial = (historial or []) + [
        {"role": "user", "content": mensaje},
        {"role": "assistant", "content": respuesta_texto},
    ]

    # 5. Log para analytics
    dt = int((time.time() - t0) * 1000)
    coste = data.get("usage", {}).get("total_tokens", 0) * 0.0000003  # deepseek pricing approx
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_portal_conversaciones
                    (tenant_id, cliente_id, mensaje_cliente, mensaje_respuesta, tools_usadas, coste_usd, tiempo_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, TENANT, cliente_id, mensaje, respuesta_texto,
                json.dumps(tools_usadas), coste, dt)
    except Exception as e:
        log.warning("portal_chat_log_error", error=str(e))

    log.info("portal_chat_ok", cliente=nombre, tools=tools_usadas, ms=dt)

    return {
        "respuesta": respuesta_texto,
        "datos": datos_acumulados,
        "tools_usadas": tools_usadas,
        "historial": nuevo_historial[-40:],  # keep last 40 messages
        "tiempo_ms": dt,
    }
