# B-PIL-18: Portal Conversacional — Interfaz Buscador con LLM

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-11 (portal), B-PIL-09 (WhatsApp), B-PIL-16 (seed)
**Coste:** ~$0.001/interacción (deepseek-v3.2 vía OpenRouter)

---

## CONTEXTO

El portal actual tiene 5 pestañas (Inicio, Sesiones, Recuperar, Pagos, Facturas) con navegación tradicional. El cliente tiene que saber dónde buscar cada cosa.

**Nuevo concepto:** Una caja de texto estilo Google. El cliente escribe lo que necesita en lenguaje natural y un LLM con function calling ejecuta las acciones sobre los endpoints existentes.

**Principio de diseño:** El cliente nunca necesita aprender una interfaz. Habla como hablaría con la recepcionista del estudio.

### Ejemplos de interacciones de alto valor

1. **Multi-acción:** "Esta semana no puedo ir el jueves, cancélala y búscame alternativas para esta semana o la que viene"
   → Cancela la sesión del jueves → Busca huecos con plaza libre → Los presenta → Pregunta cuál prefiere

2. **Lista de espera:** "No me encaja ninguno, pero si se libera algo el martes por la mañana avísame"
   → Crea alerta en om_lista_espera → Cuando alguien cancele un martes mañana, notifica vía WhatsApp

3. **Factura por WhatsApp:** "Mándame la factura del mes pasado por WhatsApp"
   → Localiza la factura → Genera el PDF → Envía por WhatsApp al teléfono del cliente

4. **Resumen inteligente:** "¿Cómo voy este mes?"
   → Asistencia, faltas, recuperaciones, saldo, próximas clases — todo en una respuesta natural

5. **Pago guiado:** "Quiero pagar lo que debo"
   → Muestra saldo pendiente → Da instrucciones de Bizum con el importe exacto y el concepto

6. **Solicitud de cambio:** "Me viene mejor un grupo de tardes, ¿hay alguno con hueco?"
   → Busca grupos de tarde con capacidad → Los muestra → Si el cliente quiere, registra la solicitud para Jesús

7. **Vacaciones/pausas:** "Me voy de vacaciones del 1 al 15 de abril"
   → Cancela todas las sesiones de ese período sin cargo → Confirma las cancelaciones → Registra la pausa

8. **Proactivo post-cancelación:** Tras cancelar, automáticamente sugiere huecos para recuperar sin que el cliente lo pida

---

## FASE A: Backend — Motor conversacional + lista de espera

### A1. Nueva tabla om_lista_espera

**Archivo:** Crear `migrations/015_lista_espera.sql`

```sql
-- 015_lista_espera.sql
CREATE TABLE IF NOT EXISTS om_lista_espera (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL REFERENCES om_clientes(id),
    dia_semana INTEGER,              -- 0=lunes, 1=martes, ... NULL=cualquier día
    franja TEXT,                      -- 'manana', 'tarde', 'cualquiera'
    hora_preferida TIME,             -- NULL = cualquier hora
    grupo_id UUID REFERENCES om_grupos(id),  -- NULL = cualquier grupo
    estado TEXT NOT NULL DEFAULT 'activa',    -- activa, notificada, expirada, cancelada
    fecha_creacion TIMESTAMPTZ DEFAULT now(),
    fecha_notificacion TIMESTAMPTZ,
    notas TEXT,
    CONSTRAINT fk_cliente FOREIGN KEY (cliente_id) REFERENCES om_clientes(id)
);

CREATE INDEX idx_lista_espera_activa ON om_lista_espera(tenant_id, estado) WHERE estado = 'activa';

-- Tabla para log de conversaciones portal (analytics)
CREATE TABLE IF NOT EXISTS om_portal_conversaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    cliente_id UUID NOT NULL,
    mensaje_cliente TEXT NOT NULL,
    mensaje_respuesta TEXT NOT NULL,
    tools_usadas JSONB DEFAULT '[]',
    coste_usd NUMERIC(8,6) DEFAULT 0,
    tiempo_ms INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### A2. Motor conversacional portal

**Archivo:** Crear `src/pilates/portal_chat.py`

```python
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
                AND s.fecha >= CURRENT_DATE AND s.fecha <= CURRENT_DATE + $3
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
            WHERE s.tenant_id=$1 AND s.fecha > $2 AND s.fecha <= $2 + $3 AND s.estado='programada'
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
            INSERT INTO om_procesos (tenant_id, nombre, tipo, estado, descripcion, prioridad)
            VALUES ($1, $2, $3, 'pendiente', $4, 'media')
        """, TENANT,
            f"Solicitud {args['tipo']} — {nombre_cliente}",
            "solicitud_cliente",
            args["descripcion"])

    # Notificar a Jesús por WA
    from src.pilates.whatsapp import enviar_texto
    jesus_tel = os.getenv("JESUS_TELEFONO", "")
    if jesus_tel:
        msg = f"📋 Solicitud de {nombre_cliente}: {args['tipo']}\n{args['descripcion']}"
        await enviar_texto(jesus_tel, msg)

    return {"registrada": True, "tipo": args["tipo"],
            "mensaje": "Solicitud registrada. Jesús te contactará pronto."}


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
}

# Estas necesitan args extra
TOOL_SPECIAL = {
    "enviar_factura_whatsapp": _tool_enviar_factura_wa,  # + telefono
    "registrar_solicitud": _tool_registrar_solicitud,    # + nombre_cliente
}


async def ejecutar_tool(nombre: str, cliente_id: UUID, args: dict,
                         telefono: str = "", nombre_cliente: str = "") -> dict:
    if nombre in TOOL_DISPATCH:
        return await TOOL_DISPATCH[nombre](cliente_id, args)
    elif nombre == "enviar_factura_whatsapp":
        return await _tool_enviar_factura_wa(cliente_id, args, telefono)
    elif nombre == "registrar_solicitud":
        return await _tool_registrar_solicitud(cliente_id, args, nombre_cliente)
    else:
        return {"error": f"Herramienta desconocida: {nombre}"}


# ============================================================
# MOTOR CONVERSACIONAL — Loop principal
# ============================================================

SYSTEM_PROMPT = """Eres el asistente del estudio Authentic Pilates en Logroño. Hablas con {nombre}, cliente del estudio.

Tu personalidad:
- Cercano pero profesional, como una recepcionista amable
- Directo: no des rodeos, ve al grano
- Siempre en español
- Usa emojis con moderación (máx 1-2 por mensaje)
- Tutea al cliente

Reglas CRÍTICAS:
1. Para CANCELAR una sesión o INSCRIBIR en recuperación: PRIMERO muestra los detalles (fecha, hora, grupo) y PREGUNTA "¿Confirmo?". NUNCA ejecutes sin confirmación.
2. Para cancelar período (vacaciones): muestra TODAS las sesiones afectadas y pide confirmación.
3. Si el cliente dice "sí", "confirma", "dale" después de que hayas mostrado detalles → ejecuta la acción.
4. Si no encuentras huecos que encajen → ofrece crear alerta en lista de espera.
5. Tras cancelar una sesión → sugiere automáticamente buscar huecos para recuperar.
6. Para pagos → muestra saldo + instrucciones Bizum exactas.
7. Si el cliente pide algo que no puedes resolver → registra solicitud para Jesús.

Datos del cliente:
- Nombre: {nombre} {apellidos}
- Grupo actual: {grupo}
- Contrato: {contrato_tipo}

Hoy es {hoy}. Responde de forma concisa."""


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
                                          telefono=telefono, nombre_cliente=f"{nombre} {apellidos}")

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
```

### A3. Checker lista de espera — integrar en automatismos

**Archivo:** `src/pilates/automatismos.py` — LEER PRIMERO. AÑADIR al cron `inicio_semana` o crear cron dedicado:

```python
async def check_lista_espera():
    """Cuando alguien cancela, verificar si hay clientes en lista de espera que encajen.

    Se ejecuta tras cada cancelación (llamado desde portal_chat.py tras cancelar_sesion).
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar alertas activas
        alertas = await conn.fetch("""
            SELECT le.*, c.nombre, c.telefono
            FROM om_lista_espera le
            JOIN om_clientes c ON c.id = le.cliente_id
            WHERE le.tenant_id = $1 AND le.estado = 'activa'
        """, TENANT)

        for alerta in alertas:
            # Buscar sesiones futuras que encajen con la preferencia
            query = """
                SELECT s.id, s.fecha, s.hora_inicio, g.nombre as grupo
                FROM om_sesiones s
                JOIN om_grupos g ON g.id = s.grupo_id
                WHERE s.tenant_id = $1 AND s.fecha > CURRENT_DATE
                    AND s.fecha <= CURRENT_DATE + 14 AND s.estado = 'programada'
            """
            params = [TENANT]

            if alerta["dia_semana"] is not None:
                query += " AND EXTRACT(DOW FROM s.fecha) = $" + str(len(params) + 1)
                # PostgreSQL DOW: Sunday=0, Monday=1... adjust from Python weekday
                pg_dow = (alerta["dia_semana"] + 1) % 7
                params.append(pg_dow)

            if alerta["franja"] == "manana":
                query += f" AND s.hora_inicio < '14:00'"
            elif alerta["franja"] == "tarde":
                query += f" AND s.hora_inicio >= '14:00'"

            query += " ORDER BY s.fecha, s.hora_inicio LIMIT 3"
            sesiones = await conn.fetch(query, *params)

            for ses in sesiones:
                # Verificar que haya plaza
                ocupadas = await conn.fetchval("""
                    SELECT count(*) FROM om_asistencias
                    WHERE sesion_id=$1 AND estado IN ('confirmada','asistio','recuperacion')
                """, ses["id"])
                cap = await conn.fetchval(
                    "SELECT capacidad_max FROM om_grupos g JOIN om_sesiones s ON s.grupo_id=g.id WHERE s.id=$1",
                    ses["id"])

                if ocupadas < cap:
                    # Notificar por WhatsApp
                    from src.pilates.whatsapp import enviar_texto
                    dia_nombre = ["lun","mar","mié","jue","vie","sáb","dom"][ses["fecha"].weekday()]
                    msg = (
                        f"🔔 ¡Se ha liberado un hueco!\n\n"
                        f"{dia_nombre} {ses['fecha'].strftime('%d/%m')} a las {str(ses['hora_inicio'])[:5]}\n"
                        f"Grupo: {ses['grupo']}\n\n"
                        f"Entra en tu portal para reservar tu plaza."
                    )
                    await enviar_texto(alerta["telefono"], msg, alerta["cliente_id"])

                    await conn.execute("""
                        UPDATE om_lista_espera SET estado='notificada', fecha_notificacion=now()
                        WHERE id=$1
                    """, alerta["id"])
                    break  # Una notificación por alerta
```

### A4. Endpoint API — Añadir a router.py

**Archivo:** `src/pilates/router.py` — LEER PRIMERO. AÑADIR al final:

```python
# ============================================================
# PORTAL CONVERSACIONAL
# ============================================================

class ChatRequest(BaseModel):
    mensaje: str
    historial: Optional[list] = None

@router.post("/portal/{token}/chat")
async def portal_chat(token: str, data: ChatRequest):
    """Portal conversacional — el cliente habla en lenguaje natural."""
    from src.pilates.portal_chat import chat
    return await chat(token, data.mensaje, data.historial)
```

---

## FASE B: Frontend — Interfaz tipo buscador

### B1. Nuevo componente PortalChat.jsx

**Archivo:** Crear `frontend/src/PortalChat.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

// Sugerencias rápidas
const SHORTCUTS = [
  { emoji: '📅', text: '¿Cuándo es mi próxima clase?' },
  { emoji: '❌', text: 'Quiero cancelar una clase' },
  { emoji: '🔄', text: '¿Hay hueco para recuperar?' },
  { emoji: '💰', text: '¿Cuánto debo?' },
  { emoji: '📄', text: 'Mis facturas' },
  { emoji: '📊', text: '¿Cómo voy este mes?' },
];

export default function PortalChat({ token }) {
  const [nombre, setNombre] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [historial, setHistorial] = useState([]);
  const [error, setError] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Load client name
  useEffect(() => {
    fetch(`${BASE}/portal/${token}/data`)
      .then(r => { if (!r.ok) throw new Error('Portal no disponible'); return r.json(); })
      .then(d => setNombre(d.cliente.nombre))
      .catch(e => setError(e.message));
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function send(text) {
    if (!text.trim() || loading) return;
    const userMsg = text.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: userMsg }]);
    setLoading(true);

    try {
      const r = await fetch(`${BASE}/portal/${token}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mensaje: userMsg, historial }),
      });
      if (!r.ok) throw new Error('Error de conexión');
      const data = await r.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        text: data.respuesta,
        datos: data.datos,
      }]);
      setHistorial(data.historial || []);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: 'Perdona, ha habido un error. Inténtalo de nuevo.',
      }]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  if (error) return (
    <div style={s.container}>
      <div style={s.card}>
        <p style={{ color: '#ef4444', textAlign: 'center' }}>{error}</p>
      </div>
    </div>
  );

  return (
    <div style={s.container}>
      <div style={s.card}>
        {/* Header */}
        <div style={s.header}>
          <div style={s.logo}>AP</div>
          <div>
            <div style={s.title}>Authentic Pilates</div>
            {nombre && <div style={s.greeting}>Hola, {nombre}</div>}
          </div>
        </div>

        {/* Messages */}
        <div style={s.chat}>
          {messages.length === 0 && (
            <div style={s.welcome}>
              <div style={s.welcomeText}>¿Qué necesitas?</div>
              <div style={s.shortcuts}>
                {SHORTCUTS.map((sc, i) => (
                  <button key={i} style={s.shortcut}
                    onClick={() => send(sc.text)}>
                    <span>{sc.emoji}</span> {sc.text}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} style={msg.role === 'user' ? s.msgUser : s.msgBot}>
              <div style={msg.role === 'user' ? s.bubbleUser : s.bubbleBot}>
                {msg.text.split('\n').map((line, j) => (
                  <span key={j}>{line}<br/></span>
                ))}
              </div>
              {/* Render data cards if present */}
              {msg.datos && Object.keys(msg.datos).length > 0 && (
                <div style={s.dataCards}>
                  {renderDataCards(msg.datos)}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div style={s.msgBot}>
              <div style={{ ...s.bubbleBot, opacity: 0.6 }}>
                <span style={s.dots}>
                  <span>.</span><span>.</span><span>.</span>
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div style={s.inputRow}>
          <input
            ref={inputRef}
            style={s.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && send(input)}
            placeholder="Escribe lo que necesitas..."
            disabled={loading}
          />
          <button style={s.sendBtn} onClick={() => send(input)} disabled={loading || !input.trim()}>
            →
          </button>
        </div>

        {/* Quick shortcuts after conversation started */}
        {messages.length > 0 && (
          <div style={s.miniShortcuts}>
            {SHORTCUTS.slice(0, 4).map((sc, i) => (
              <button key={i} style={s.miniShortcut}
                onClick={() => send(sc.text)}>
                {sc.emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function renderDataCards(datos) {
  const cards = [];
  // Render huecos de recuperación
  if (datos.buscar_huecos_recuperacion?.huecos?.length > 0) {
    datos.buscar_huecos_recuperacion.huecos.slice(0, 5).forEach((h, i) => {
      cards.push(
        <div key={`hueco-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{h.dia} {h.fecha}</div>
          <div style={{ fontSize: 13, color: '#6b7280' }}>{h.hora} · {h.grupo}</div>
          <div style={{ fontSize: 12, color: '#22c55e' }}>{h.plazas_libres} plazas</div>
        </div>
      );
    });
  }
  // Render facturas
  if (datos.ver_facturas?.facturas?.length > 0) {
    datos.ver_facturas.facturas.forEach((f, i) => {
      cards.push(
        <div key={`fact-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{f.numero}</div>
          <div style={{ fontSize: 13 }}>{f.fecha} · {f.total.toFixed(2)}€</div>
          <a href={`${BASE}${f.pdf_url}`} target="_blank"
            style={{ fontSize: 12, color: '#6366f1' }}>Descargar PDF</a>
        </div>
      );
    });
  }
  // Render próximas clases
  if (datos.ver_proximas_clases?.clases?.length > 0) {
    datos.ver_proximas_clases.clases.slice(0, 5).forEach((c, i) => {
      cards.push(
        <div key={`clase-${i}`} style={s.dataCard}>
          <div style={{ fontWeight: 600 }}>{c.dia} {c.fecha}</div>
          <div style={{ fontSize: 13, color: '#6b7280' }}>{c.hora} · {c.grupo}</div>
          <div style={{ fontSize: 12, color: c.estado === 'confirmada' ? '#22c55e' : '#9ca3af' }}>
            {c.estado}
          </div>
        </div>
      );
    });
  }
  return cards;
}

const s = {
  container: {
    minHeight: '100vh', display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
    background: '#f0f0f0', padding: '16px 8px', fontFamily: "'Inter', -apple-system, sans-serif",
  },
  card: {
    background: '#fff', borderRadius: 20, maxWidth: 440, width: '100%',
    boxShadow: '0 8px 40px rgba(0,0,0,0.08)', marginTop: 12,
    display: 'flex', flexDirection: 'column', minHeight: 'calc(100vh - 56px)', maxHeight: 'calc(100vh - 56px)',
  },
  header: {
    display: 'flex', gap: 12, alignItems: 'center',
    padding: '16px 20px', borderBottom: '1px solid #f3f4f6',
  },
  logo: {
    width: 40, height: 40, borderRadius: 12, background: '#6366f1',
    color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 700, fontSize: 14,
  },
  title: { fontSize: 16, fontWeight: 700, color: '#111' },
  greeting: { fontSize: 13, color: '#6b7280' },
  chat: {
    flex: 1, overflowY: 'auto', padding: '16px 16px 8px',
    display: 'flex', flexDirection: 'column', gap: 8,
  },
  welcome: { textAlign: 'center', paddingTop: 40 },
  welcomeText: { fontSize: 20, fontWeight: 600, marginBottom: 24, color: '#374151' },
  shortcuts: { display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 300, margin: '0 auto' },
  shortcut: {
    display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
    background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 12,
    fontSize: 13, color: '#374151', cursor: 'pointer', textAlign: 'left',
    transition: 'all 0.15s',
  },
  msgUser: { display: 'flex', justifyContent: 'flex-end' },
  msgBot: { display: 'flex', flexDirection: 'column', alignItems: 'flex-start' },
  bubbleUser: {
    background: '#6366f1', color: '#fff', padding: '10px 14px',
    borderRadius: '16px 16px 4px 16px', maxWidth: '80%', fontSize: 14, lineHeight: 1.5,
  },
  bubbleBot: {
    background: '#f3f4f6', color: '#111', padding: '10px 14px',
    borderRadius: '16px 16px 16px 4px', maxWidth: '85%', fontSize: 14, lineHeight: 1.5,
  },
  dataCards: { display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6, width: '85%' },
  dataCard: {
    background: '#fafafa', border: '1px solid #e5e7eb', borderRadius: 10,
    padding: '8px 12px', fontSize: 13,
  },
  inputRow: {
    display: 'flex', gap: 8, padding: '12px 16px',
    borderTop: '1px solid #f3f4f6',
  },
  input: {
    flex: 1, padding: '12px 16px', border: '1px solid #e5e7eb', borderRadius: 14,
    fontSize: 14, outline: 'none', background: '#f9fafb',
  },
  sendBtn: {
    width: 44, height: 44, borderRadius: 14, border: 'none',
    background: '#6366f1', color: '#fff', fontSize: 18, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  miniShortcuts: {
    display: 'flex', justifyContent: 'center', gap: 12, padding: '8px 16px 12px',
  },
  miniShortcut: {
    width: 36, height: 36, borderRadius: 10, border: '1px solid #e5e7eb',
    background: '#fff', fontSize: 16, cursor: 'pointer',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  dots: { display: 'inline-flex', gap: 2, animation: 'pulse 1s infinite' },
};
```

### B2. Actualizar App.jsx — ruta portal

**Archivo:** `frontend/src/App.jsx` — LEER PRIMERO. Modificar la lógica de routing del portal para cargar `PortalChat` en lugar de `Portal`:

```jsx
// ANTES:
import Portal from './Portal.jsx';
// ...
if (path.startsWith('/portal/')) return <Portal token={...} />;

// DESPUÉS:
import PortalChat from './PortalChat.jsx';
// ...
if (path.startsWith('/portal/')) return <PortalChat token={...} />;
```

El componente `Portal.jsx` original se mantiene como fallback.

---

## FASE C: Verificación

### Tests — Ejecutar en orden:

```bash
# C1. Migración
psql $DATABASE_URL -f migrations/015_lista_espera.sql
# PASS: 2 tablas creadas sin error

# C2. Test endpoint chat básico (requiere seed de B-PIL-16)
curl -X POST https://motor-semantico-omni.fly.dev/portal/{TOKEN}/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿cuándo es mi próxima clase?"}'
# PASS: respuesta con campo "respuesta" no vacío, tools_usadas contiene "ver_proximas_clases"

# C3. Test multi-acción
curl -X POST .../portal/{TOKEN}/chat \
  -d '{"mensaje": "¿cómo voy este mes?"}'
# PASS: respuesta con datos de asistencia, tools_usadas contiene "resumen_mensual"

# C4. Test lista de espera
curl -X POST .../portal/{TOKEN}/chat \
  -d '{"mensaje": "Avísame si se libera hueco el martes por la mañana"}'
# PASS: tools_usadas contiene "crear_lista_espera"

# C5. Frontend carga
# Abrir https://motor-semantico-omni.fly.dev/portal/{TOKEN}
# PASS: Aparece interfaz tipo chat con "¿Qué necesitas?" y 6 shortcuts
# PASS: Escribir "Mis clases" → respuesta conversacional con tarjetas

# C6. Conversación con confirmación
# Escribir "Quiero cancelar mi clase del jueves"
# PASS: Bot muestra detalles y pregunta "¿Confirmo?"
# Escribir "Sí"
# PASS: Bot confirma cancelación y sugiere huecos para recuperar
```

---

## NOTAS

- **Coste:** ~$0.001/interacción con deepseek-chat. 100 interacciones/mes por cliente = $0.10/mes. Negligible.
- **Modelo alternativo:** Si deepseek no soporta bien function calling en español, usar `mistralai/devstral-2512` (ya validado en séquito).
- **El portal antiguo (Portal.jsx) se mantiene** como fallback. Solo cambia la ruta por defecto.
- **Lista de espera + checker** es valor enorme: automatiza completamente la gestión de cancelaciones tardías → huecos → notificaciones.
- **Toda la lógica de negocio sigue en portal.py/router.py** — portal_chat.py es solo la capa conversacional que llama a las mismas funciones.
