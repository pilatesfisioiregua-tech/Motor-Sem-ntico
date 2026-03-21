# B-PIL-19: Cockpit Operativo — Centro de Mando Conversacional

**Fecha:** 2026-03-21
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-18 Fase J (cockpit base)
**Coste:** ~$0.002/interacción (deepseek-chat, más tokens por tools operativas)

---

## CONTEXTO

El cockpit actual (Fase J) controla QUÉ MÓDULOS se ven en pantalla. Pero Jesús quiere que además EJECUTE ACCIONES OPERATIVAS directamente:

- "Agéndame a María los martes a las 12h y viernes a las 13h hasta junio"
- "Añade a Pedro al grupo de las 17h L-X"  
- "Prepárame las facturas de 2025 de Ana, Luis y Carmen y mándaselas por WhatsApp"
- "Registra un Bizum de 105€ de Sofía"
- "Cancela todas las clases de Pedro la semana que viene"

Esto convierte el cockpit en un **centro de mando por voz/texto** que elimina toda la fricción operativa.

---

## FASE A: Tools operativas para cockpit

### A1. Actualizar cockpit.py — System prompt + Tools + Dispatch

**Archivo:** `src/pilates/cockpit.py` — REESCRIBIR la sección J4+J5.

#### System prompt actualizado:

Añadir después del bloque actual de REGLAS GENERALES:

```python
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

REGLAS OPERATIVAS:
1. Antes de ejecutar cualquier acción, BUSCA al cliente por nombre para obtener su ID.
2. Para acciones destructivas (cancelar, eliminar), CONFIRMA con Jesús antes de ejecutar.
3. Si Jesús dice "agéndame a X los martes y viernes hasta junio", calcula todas las fechas y crea las sesiones de golpe.
4. Si dice "ponle en el grupo de las 17h", busca el grupo que encaje por hora y lo inscribe.
5. Para facturas: primero busca cargos cobrados sin facturar, luego genera la factura.
6. Puedes combinar operaciones de interfaz con operativas en la misma respuesta.
7. Tras una operación, muestra el módulo relevante (ej: tras agendar → montar "calendario").
```

#### Tools spec — AÑADIR estas tools al array TOOLS_COCKPIT:

```python
TOOLS_COCKPIT_OPS = [
    # --- INTERFAZ (ya existe) ---
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
            "description": "Buscar cliente por nombre, apellidos o teléfono. SIEMPRE usar antes de cualquier operación con un cliente. Devuelve ID, nombre, grupo, contrato, saldo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Nombre, apellidos o teléfono del cliente"}
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
            "description": "Crear sesiones individuales recurrentes para un cliente. Ej: martes 12:00 y viernes 13:00 cada semana hasta una fecha. Calcula todas las fechas y crea las sesiones de golpe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "slots": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "dia_semana": {"type": "integer", "description": "0=lunes, 1=martes, 2=miércoles, 3=jueves, 4=viernes"},
                                "hora_inicio": {"type": "string", "description": "Formato HH:MM (ej: 12:00)"},
                                "hora_fin": {"type": "string", "description": "Formato HH:MM (ej: 13:00). Si no se da, se asume 1h después."}
                            },
                            "required": ["dia_semana", "hora_inicio"]
                        },
                        "description": "Lista de slots semanales"
                    },
                    "hasta_fecha": {"type": "string", "description": "Fecha límite YYYY-MM-DD (ej: 2026-06-30)"},
                    "desde_fecha": {"type": "string", "description": "Fecha inicio YYYY-MM-DD. Default: próxima ocurrencia."}
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
            "description": "Inscribir un cliente en un grupo existente. Crea contrato tipo grupo. Busca el grupo por nombre o por horario si Jesús dice 'el grupo de las 17h'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "grupo_id": {"type": "string", "description": "UUID del grupo (si se conoce)"},
                    "buscar_grupo": {"type": "string", "description": "Texto para buscar grupo: hora, nombre, días. Ej: '17h L-X', 'Reformer mañanas'"}
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
            "description": "Listar grupos con plazas disponibles, horarios y ocupación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "solo_con_plaza": {"type": "boolean", "default": true}
                }
            }
        }
    },
    # --- CANCELAR SESIONES ---
    {
        "type": "function",
        "function": {
            "name": "cancelar_sesiones_cliente",
            "description": "Cancelar sesiones de un cliente. Puede ser: una sesión específica, todas las de un rango de fechas, o todas las de la próxima semana.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "sesion_id": {"type": "string", "description": "UUID de sesión específica (si se conoce)"},
                    "fecha_inicio": {"type": "string", "description": "YYYY-MM-DD inicio del rango"},
                    "fecha_fin": {"type": "string", "description": "YYYY-MM-DD fin del rango"}
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
            "description": "Registrar un pago recibido (Bizum, efectivo, transferencia). Concilia automáticamente con cargos pendientes FIFO.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "monto": {"type": "number", "description": "Importe en euros"},
                    "metodo": {"type": "string", "enum": ["bizum", "efectivo", "transferencia", "tpv"], "description": "Método de pago"}
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
            "description": "Generar facturas para un cliente desde sus cargos cobrados sin facturar. Si se pide 'facturas del año pasado', busca cargos cobrados de ese período.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "periodo": {"type": "string", "description": "Periodo: 'ultimo_mes', 'ultimo_trimestre', '2025', 'YYYY-MM'. Default: sin facturar."}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- ENVIAR POR WHATSAPP ---
    {
        "type": "function",
        "function": {
            "name": "enviar_whatsapp",
            "description": "Enviar un mensaje o factura por WhatsApp a un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"},
                    "mensaje": {"type": "string", "description": "Texto del mensaje (si es texto libre)"},
                    "factura_id": {"type": "string", "description": "UUID de factura (si es envío de factura)"}
                },
                "required": ["cliente_id"]
            }
        }
    },
    # --- VER PAGOS/SALDO CLIENTE ---
    {
        "type": "function",
        "function": {
            "name": "ver_pagos_cliente",
            "description": "Ver saldo pendiente, cargos y últimos pagos de un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_id": {"type": "string", "description": "UUID del cliente"}
                },
                "required": ["cliente_id"]
            }
        }
    },
]
```

### A2. Implementación de cada tool operativa

Añadir estas funciones a `cockpit.py`:

```python
# ============================================================
# TOOLS OPERATIVAS — Ejecución directa contra DB
# ============================================================

async def _op_buscar_cliente(args: dict) -> dict:
    q = args["query"]
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   ct.estado as estado_tenant,
                   co.tipo as contrato_tipo, co.estado as contrato_estado,
                   g.nombre as grupo_nombre, g.id as grupo_id,
                   COALESCE((SELECT SUM(total) FROM om_cargos
                    WHERE cliente_id=c.id AND tenant_id=$1 AND estado='pendiente'), 0) as saldo
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id=c.id AND ct.tenant_id=$1
            LEFT JOIN om_contratos co ON co.cliente_id=c.id AND co.tenant_id=$1 AND co.estado='activo'
            LEFT JOIN om_grupos g ON g.id=co.grupo_id
            WHERE c.nombre ILIKE $2 OR c.apellidos ILIKE $2 OR c.telefono ILIKE $2
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
        "telefono": c["telefono"], "email": c["email"],
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
    desde = date.fromisoformat(args.get("desde_fecha", str(date.today())))

    # Buscar contrato individual del cliente
    pool = await _get_pool()
    async with pool.acquire() as conn:
        contrato = await conn.fetchrow("""
            SELECT id, precio_sesion FROM om_contratos
            WHERE cliente_id=$1 AND tenant_id=$2 AND tipo='individual' AND estado='activo'
        """, cliente_id, TENANT)
        contrato_id = contrato["id"] if contrato else None

        sesiones_creadas = 0
        detalles = []

        for slot in slots:
            dia = slot["dia_semana"]  # 0=lunes
            hi = dtime.fromisoformat(slot["hora_inicio"])
            hf_str = slot.get("hora_fin")
            if hf_str:
                hf = dtime.fromisoformat(hf_str)
            else:
                hf = dtime(hi.hour + 1, hi.minute)

            # Iterar fechas
            fecha = desde
            while fecha <= hasta:
                if fecha.weekday() == dia:
                    # Verificar que no exista ya
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
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()

    async with pool.acquire() as conn:
        grupo_id = None

        if args.get("grupo_id"):
            grupo_id = UUID(args["grupo_id"])
        elif args.get("buscar_grupo"):
            # Buscar grupo por texto libre (hora, nombre, días)
            busq = args["buscar_grupo"].lower()
            grupos = await conn.fetch("""
                SELECT g.id, g.nombre, g.hora_inicio, g.dias_semana, g.capacidad_max,
                    (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
                FROM om_grupos g
                WHERE g.tenant_id=$1 AND g.estado='activo'
            """, TENANT)
            for g in grupos:
                nombre_lower = (g["nombre"] or "").lower()
                hora_str = str(g["hora_inicio"])[:5] if g["hora_inicio"] else ""
                if (busq in nombre_lower or busq in hora_str or
                    hora_str.replace(":","h") in busq or hora_str[:2]+"h" in busq):
                    if g["ocu"] < g["capacidad_max"]:
                        grupo_id = g["id"]
                        break
            if not grupo_id:
                return {"error": f"No encuentro grupo que encaje con '{args['buscar_grupo']}' con plaza libre"}

        if not grupo_id:
            return {"error": "Necesito grupo_id o buscar_grupo"}

        # Verificar plaza
        grupo = await conn.fetchrow("""
            SELECT g.*, (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
            FROM om_grupos g WHERE g.id=$1
        """, grupo_id)
        if not grupo:
            return {"error": "Grupo no encontrado"}
        if grupo["ocu"] >= grupo["capacidad_max"]:
            return {"error": f"Grupo {grupo['nombre']} está lleno ({grupo['ocu']}/{grupo['capacidad_max']})"}

        # Verificar que no tenga ya contrato en este grupo
        ya = await conn.fetchval("""
            SELECT 1 FROM om_contratos WHERE cliente_id=$1 AND grupo_id=$2 AND estado='activo'
        """, cliente_id, grupo_id)
        if ya:
            return {"error": "Ya está inscrito en este grupo"}

        # Crear contrato
        await conn.execute("""
            INSERT INTO om_contratos (tenant_id, cliente_id, tipo, grupo_id, precio_mensual, fecha_inicio)
            VALUES ($1, $2, 'grupo', $3, $4, CURRENT_DATE)
        """, TENANT, cliente_id, grupo_id, grupo["precio_mensual"])

    return {
        "inscrito": True,
        "grupo": grupo["nombre"],
        "precio": float(grupo["precio_mensual"]) if grupo["precio_mensual"] else None,
        "plazas_restantes": grupo["capacidad_max"] - grupo["ocu"] - 1,
    }


async def _op_ver_grupos(args: dict) -> dict:
    solo_con_plaza = args.get("solo_con_plaza", True)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.nombre, g.tipo, g.hora_inicio, g.dias_semana,
                   g.capacidad_max, g.precio_mensual,
                   (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
            ORDER BY g.hora_inicio
        """, TENANT)
    grupos = []
    for r in rows:
        libres = r["capacidad_max"] - r["ocu"]
        if solo_con_plaza and libres <= 0:
            continue
        grupos.append({
            "id": str(r["id"]), "nombre": r["nombre"],
            "hora": str(r["hora_inicio"])[:5] if r["hora_inicio"] else "?",
            "dias": r["dias_semana"],
            "ocupacion": f"{r['ocu']}/{r['capacidad_max']}",
            "libres": libres,
            "precio": float(r["precio_mensual"]) if r["precio_mensual"] else None,
        })
    return {"grupos": grupos}


async def _op_cancelar_sesiones(args: dict) -> dict:
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    pool = await _get_pool()

    async with pool.acquire() as conn:
        conditions = ["a.cliente_id=$1", "a.tenant_id=$2", "a.estado='confirmada'", "s.fecha >= CURRENT_DATE"]
        params = [cliente_id, TENANT]
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
    from uuid import UUID
    cliente_id = UUID(args["cliente_id"])
    monto = float(args["monto"])
    metodo = args["metodo"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow("""
                INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto, notas)
                VALUES ($1, $2, $3, $4, $5) RETURNING id
            """, TENANT, cliente_id, metodo, monto, f"Registrado desde cockpit")
            pago_id = row["id"]

            # FIFO
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
    from src.pilates.feed import feed_pago
    nombre = await conn.fetchval("SELECT nombre FROM om_clientes WHERE id=$1", cliente_id)
    await feed_pago(nombre or "?", metodo, monto, cliente_id)

    return {
        "pago_registrado": True,
        "monto": monto, "metodo": metodo,
        "cargos_conciliados": conciliados,
        "restante": round(restante, 2),
    }


async def _op_generar_facturas(args: dict) -> dict:
    from uuid import UUID
    import hashlib
    cliente_id = UUID(args["cliente_id"])
    periodo = args.get("periodo")
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Buscar cargos cobrados sin facturar
        conditions = ["c.cliente_id=$1", "c.tenant_id=$2", "c.estado='cobrado'"]
        params = [cliente_id, TENANT]
        idx = 3

        # Excluir ya facturados
        conditions.append("NOT EXISTS (SELECT 1 FROM om_factura_lineas fl WHERE fl.cargo_id=c.id)")

        if periodo:
            if periodo == "2025":
                conditions.append(f"c.fecha_cargo >= ${idx}")
                params.append(date(2025,1,1)); idx += 1
                conditions.append(f"c.fecha_cargo <= ${idx}")
                params.append(date(2025,12,31)); idx += 1
            elif periodo == "ultimo_mes":
                conditions.append(f"c.fecha_cargo >= date_trunc('month', CURRENT_DATE) - interval '1 month'")
                conditions.append(f"c.fecha_cargo < date_trunc('month', CURRENT_DATE)")
            elif len(periodo) == 7:  # YYYY-MM
                conditions.append(f"to_char(c.fecha_cargo, 'YYYY-MM') = ${idx}")
                params.append(periodo); idx += 1

        where = " AND ".join(conditions)
        cargos = await conn.fetch(f"""
            SELECT id, tipo, descripcion, base_imponible, total, fecha_cargo
            FROM om_cargos c WHERE {where}
            ORDER BY c.fecha_cargo
        """, *params)

        if not cargos:
            return {"facturas_generadas": 0, "mensaje": "No hay cargos cobrados sin facturar"}

        # Agrupar por mes para generar una factura por mes
        meses = {}
        for c in cargos:
            mes_key = c["fecha_cargo"].strftime("%Y-%m") if c["fecha_cargo"] else "sin_fecha"
            meses.setdefault(mes_key, []).append(c)

        facturas = []
        for mes, cargos_mes in meses.items():
            cargo_ids = [c["id"] for c in cargos_mes]
            base_total = sum(float(c["base_imponible"]) for c in cargos_mes)
            iva_pct = 21.0
            iva_total = round(base_total * iva_pct / 100, 2)
            total = round(base_total + iva_total, 2)

            # Número factura
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
                cliente["nif"], f"{cliente['nombre']} {cliente['apellidos']}",
                cliente["direccion"])

            for cargo in cargos_mes:
                bi = float(cargo["base_imponible"])
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

    return {
        "facturas_generadas": len(facturas),
        "facturas": facturas,
    }


async def _op_enviar_whatsapp(args: dict) -> dict:
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
```

### A3. Dispatch en chat_cockpit()

Actualizar el bloque de dispatch dentro del loop de tool_calls:

```python
# Dispatch de todas las tools
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
}

# En el loop de tool_calls:
if fn_name == "configurar_interfaz":
    # ... (código existente para interfaz)
elif fn_name in TOOL_DISPATCH:
    result = await TOOL_DISPATCH[fn_name](fn_args)
else:
    result = {"error": f"Herramienta desconocida: {fn_name}"}
```

### A4. Aumentar max_tokens y max_iterations

Las operaciones complejas (buscar + agendar + montar módulo) requieren más iteraciones:

```python
# En chat_cockpit():
max_tokens=800,    # era 400
# max iterations: 5  # era 3
for _ in range(5):
```

---

## FASE B: Verificación

```bash
# B1. Buscar cliente
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"busca a María","modulos_activos":[],"historial":[]}'
# PASS: respuesta con datos de María (ID, grupo, saldo)

# B2. Agendar recurrente
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"agéndame a María García los martes a las 12h y viernes a las 13h hasta junio","modulos_activos":[],"historial":[]}'
# PASS: tools_usadas incluye buscar_cliente + agendar_sesiones_recurrentes
# PASS: respuesta con N sesiones creadas

# B3. Inscribir en grupo
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"añade a Pedro al grupo de las 17h L-X","modulos_activos":[],"historial":[]}'
# PASS: tools_usadas incluye buscar_cliente + inscribir_en_grupo

# B4. Generar facturas + enviar WA
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"prepara las facturas de 2025 de Ana y mándaselas por WhatsApp","modulos_activos":[],"historial":[]}'
# PASS: tools_usadas incluye buscar_cliente + generar_facturas + enviar_whatsapp

# B5. Registrar pago
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"registra un Bizum de 105€ de Sofía","modulos_activos":[],"historial":[]}'
# PASS: tools_usadas incluye buscar_cliente + registrar_pago

# B6. Combo interfaz + operativo
curl -X POST .../cockpit/chat \
  -d '{"mensaje":"cancela las clases de Pedro la semana que viene y ponme los pagos","modulos_activos":[],"historial":[]}'
# PASS: tools_usadas incluye buscar_cliente + cancelar_sesiones + configurar_interfaz
# PASS: acciones.montar incluye pagos_pendientes
```

---

## NOTAS

- **11 tools en total** (1 interfaz + 10 operativas). Deepseek-chat soporta bien function calling con 10+ tools.
- **Siempre buscar antes de operar:** El LLM tiene instrucciones de buscar_cliente ANTES de cualquier acción. Así resuelve "María" → UUID.
- **Cadena de tools:** El LLM puede llamar buscar → agendar → configurar_interfaz en una sola conversación (3 iteraciones del loop).
- **Feed integrado:** registrar_pago publica en feed automáticamente. Las demás operaciones también deberían publicar.
- **Facturas por mes:** Si pides "facturas de 2025", genera una factura por cada mes que tenga cargos.
- **No toca el frontend:** Las tools operativas devuelven datos al LLM que los presenta en texto. La interfaz sigue igual.
