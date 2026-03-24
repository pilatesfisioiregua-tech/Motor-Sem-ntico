"""Sub-router: Clientes, Contratos, Búsqueda, Onboarding self-service."""
from __future__ import annotations

import asyncio
import secrets
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict, _observar_crud,
    ClienteCreate, ClienteUpdate,
    ContratoCreate, ContratoUpdate,
    OnboardingLinkCreate, OnboardingComplete,
)

router = APIRouter(tags=["clientes"])


# ============================================================
# CLIENTES
# ============================================================

@router.get("/clientes")
async def listar_clientes(estado: Optional[str] = None):
    """Lista clientes del tenant. Filtro opcional por estado en om_cliente_tenant."""
    estado = estado or None
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT c.*, ct.estado as estado_tenant, ct.fecha_alta, ct.fuente_captacion
                FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
                WHERE ct.tenant_id = $1 AND ct.estado = $2
                ORDER BY c.apellidos, c.nombre
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT c.*, ct.estado as estado_tenant, ct.fecha_alta, ct.fuente_captacion
                FROM om_clientes c
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
                WHERE ct.tenant_id = $1
                ORDER BY c.apellidos, c.nombre
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/clientes/{cliente_id}")
async def obtener_cliente(cliente_id: UUID):
    """Detalle de un cliente con contratos y saldo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente:
            raise HTTPException(404, "Cliente no encontrado")

        contratos = await conn.fetch(
            "SELECT * FROM om_contratos WHERE cliente_id = $1 AND tenant_id = $2 ORDER BY fecha_inicio DESC",
            cliente_id, TENANT)

        # Saldo: cargos pendientes
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

        tenant = await conn.fetchrow(
            "SELECT cliente_id, tenant_id, estado FROM om_cliente_tenant WHERE cliente_id = $1 AND tenant_id = $2",
            cliente_id, TENANT)

    return {
        **_row_to_dict(cliente),
        "estado_tenant": tenant["estado"] if tenant else None,
        "contratos": [_row_to_dict(c) for c in contratos],
        "saldo_pendiente": float(saldo),
    }


@router.post("/clientes", status_code=201)
async def crear_cliente(data: ClienteCreate):
    """Crea cliente + relación con tenant."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Crear cliente
            row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    fecha_nacimiento, nif, direccion,
                    consentimiento_datos, consentimiento_marketing,
                    consentimiento_compartir_tenants,
                    fecha_consentimiento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, now())
                RETURNING id
            """, data.nombre, data.apellidos, data.telefono, data.email,
                data.fecha_nacimiento, data.nif, data.direccion,
                data.consentimiento_datos, data.consentimiento_marketing,
                data.consentimiento_compartir_tenants)

            cliente_id = row["id"]

            # Crear relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado)
                VALUES ($1, $2, 'activo')
            """, cliente_id, TENANT)

    log.info("cliente_creado", id=str(cliente_id), nombre=f"{data.nombre} {data.apellidos}")
    asyncio.create_task(_observar_crud("cliente", "crear", {"id": str(cliente_id), "nombre": data.nombre}))
    return {"id": str(cliente_id), "status": "created"}


@router.patch("/clientes/{cliente_id}")
async def actualizar_cliente(cliente_id: UUID, data: ClienteUpdate):
    """Actualiza campos del cliente (solo los enviados)."""
    _CAMPOS_CLIENTE = {
        "nombre", "apellidos", "telefono", "email", "fecha_nacimiento",
        "nif", "direccion", "metodo_pago_habitual",
        "consentimiento_datos", "consentimiento_marketing",
        "consentimiento_compartir_tenants",
    }
    updates = {k: v for k, v in data.model_dump().items() if v is not None and k in _CAMPOS_CLIENTE}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")

    pool = await _get_pool()
    set_clauses = ", ".join(f'"{k}" = ${i+2}' for i, k in enumerate(updates.keys()))
    values = [cliente_id] + list(updates.values())

    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE om_clientes SET {set_clauses}, updated_at = now() WHERE id = $1",
            *values)
        if result == "UPDATE 0":
            raise HTTPException(404, "Cliente no encontrado")

    log.info("cliente_actualizado", id=str(cliente_id), campos=list(updates.keys()))
    return {"status": "updated"}


# ============================================================
# CONTRATOS
# ============================================================

@router.get("/contratos")
async def listar_contratos(estado: Optional[str] = "activo"):
    """Lista contratos del tenant. Default: solo activos."""
    estado = estado or None
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT co.*, c.nombre, c.apellidos, g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                LEFT JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1 AND co.estado = $2
                ORDER BY c.apellidos, c.nombre
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT co.*, c.nombre, c.apellidos, g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                LEFT JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1
                ORDER BY c.apellidos, c.nombre
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/contratos", status_code=201)
async def crear_contrato(data: ContratoCreate):
    """Crea contrato. Si es grupo, valida plaza disponible."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Validar cliente existe
            cliente = await conn.fetchval(
                "SELECT 1 FROM om_clientes WHERE id = $1", data.cliente_id)
            if not cliente:
                raise HTTPException(404, "Cliente no encontrado")

            # Si grupo: validar plaza
            if data.tipo == "grupo" and data.grupo_id:
                grupo = await conn.fetchrow(
                    "SELECT capacidad_max FROM om_grupos WHERE id = $1 AND tenant_id = $2",
                    data.grupo_id, TENANT)
                if not grupo:
                    raise HTTPException(404, "Grupo no encontrado")

                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)
                if ocupados >= grupo["capacidad_max"]:
                    raise HTTPException(409, f"Grupo lleno ({ocupados}/{grupo['capacidad_max']})")

            row = await conn.fetchrow("""
                INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                    frecuencia_semanal, precio_sesion, ciclo_cobro,
                    grupo_id, precio_mensual, dia_fijo, fecha_inicio)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id
            """, TENANT, data.cliente_id, data.tipo,
                data.frecuencia_semanal, data.precio_sesion, data.ciclo_cobro,
                data.grupo_id, data.precio_mensual, data.dia_fijo,
                data.fecha_inicio or date.today())

    contrato_id = row["id"]
    log.info("contrato_creado", id=str(contrato_id), tipo=data.tipo)
    asyncio.create_task(_observar_crud("contrato", "crear", {"id": str(contrato_id), "cliente_id": str(data.cliente_id), "tipo": data.tipo}))
    return {"id": str(contrato_id), "status": "created"}


@router.patch("/contratos/{contrato_id}")
async def actualizar_contrato(contrato_id: UUID, data: ContratoUpdate):
    """Actualiza contrato (estado, precios, fecha_fin)."""
    _CAMPOS_CONTRATO = {"estado", "precio_sesion", "precio_mensual", "ciclo_cobro", "fecha_fin"}
    updates = {k: v for k, v in data.model_dump().items() if v is not None and k in _CAMPOS_CONTRATO}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")

    pool = await _get_pool()
    set_clauses = ", ".join(f'"{k}" = ${i+2}' for i, k in enumerate(updates.keys()))
    values = [contrato_id] + list(updates.values())

    tenant_idx = len(values) + 1
    values.append(TENANT)
    async with pool.acquire() as conn:
        result = await conn.execute(
            f"UPDATE om_contratos SET {set_clauses}, updated_at = now() WHERE id = $1 AND tenant_id = ${tenant_idx}",
            *values)
        if result == "UPDATE 0":
            raise HTTPException(404, "Contrato no encontrado")

    log.info("contrato_actualizado", id=str(contrato_id))
    return {"status": "updated"}


# ============================================================
# BÚSQUEDA RÁPIDA (Modo Estudio: F3)
# ============================================================

@router.get("/buscar")
async def buscar(q: str):
    """Búsqueda rápida por nombre/apellidos/teléfono. Para typeahead del Modo Estudio."""
    if len(q) < 2:
        return []

    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   ct.estado as estado_tenant
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            WHERE (c.nombre ILIKE $2 OR c.apellidos ILIKE $2 OR c.telefono ILIKE $2)
            ORDER BY c.apellidos, c.nombre
            LIMIT 10
        """, TENANT, f"%{q}%")
    return [_row_to_dict(r) for r in rows]


# ============================================================
# ONBOARDING SELF-SERVICE
# ============================================================

@router.post("/onboarding/crear-enlace", status_code=201)
async def crear_enlace_onboarding(data: OnboardingLinkCreate):
    """Jesús crea enlace de onboarding para un lead."""
    pool = await _get_pool()
    token = secrets.token_urlsafe(32)

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_onboarding_links (tenant_id, token, nombre_provisional, telefono,
                fecha_expiracion)
            VALUES ($1, $2, $3, $4, now() + interval '7 days')
            RETURNING id, token
        """, TENANT, token, data.nombre_provisional, data.telefono)

    base_url = "https://motor-semantico-omni.fly.dev"
    enlace = f"{base_url}/onboarding/{token}"

    log.info("onboarding_enlace_creado", token=token[:8],
             nombre=data.nombre_provisional)
    return {
        "id": str(row["id"]),
        "token": token,
        "enlace": enlace,
        "wa_mensaje": f"Hola {data.nombre_provisional}! Para inscribirte en Authentic Pilates, "
                      f"rellena esta ficha: {enlace}",
        "expira_en": "7 días",
    }


@router.get("/onboarding/enlaces")
async def listar_enlaces_onboarding(estado: Optional[str] = None):
    """Lista enlaces de onboarding creados (para Jesús)."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1 AND l.estado = $2
                ORDER BY l.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT l.*, c.nombre, c.apellidos
                FROM om_onboarding_links l
                LEFT JOIN om_clientes c ON c.id = l.cliente_id
                WHERE l.tenant_id = $1
                ORDER BY l.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/onboarding/{token}")
async def obtener_onboarding(token: str):
    """Endpoint público: devuelve datos del enlace + grupos disponibles."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] == "completado":
            raise HTTPException(410, "Este enlace ya fue utilizado")
        if link["estado"] == "expirado" or (link["fecha_expiracion"] and
            link["fecha_expiracion"] < datetime.now(link["fecha_expiracion"].tzinfo)):
            raise HTTPException(410, "Este enlace ha expirado")

        grupos = await conn.fetch("""
            SELECT g.id, g.nombre, g.tipo, g.capacidad_max, g.dias_semana,
                   g.precio_mensual, g.frecuencia_semanal,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

        grupos_disponibles = []
        for g in grupos:
            if g["ocupadas"] < g["capacidad_max"]:
                grupos_disponibles.append({
                    "id": str(g["id"]),
                    "nombre": g["nombre"],
                    "tipo": g["tipo"],
                    "precio_mensual": float(g["precio_mensual"]),
                    "frecuencia_semanal": g["frecuencia_semanal"],
                    "plazas_libres": g["capacidad_max"] - g["ocupadas"],
                    "dias_semana": g["dias_semana"],
                })

    return {
        "nombre_provisional": link["nombre_provisional"],
        "telefono": link["telefono"],
        "grupos_disponibles": grupos_disponibles,
        "precios": {
            "individual_1x": 35.00,
            "individual_2x": 30.00,
            "grupo_estandar": 105.00,
            "grupo_mat": 55.00,
            "grupo_1x": 60.00,
        },
    }


@router.post("/onboarding/{token}/completar")
async def completar_onboarding(token: str, data: OnboardingComplete):
    """Endpoint público: el cliente completa el formulario.
    Crea: om_clientes + om_cliente_tenant + om_datos_clinicos + om_contratos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT * FROM om_onboarding_links WHERE token = $1 AND tenant_id = $2
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Enlace no encontrado")
        if link["estado"] != "pendiente":
            raise HTTPException(410, "Este enlace ya no es válido")

        async with conn.transaction():
            # 1. Crear cliente
            cliente_row = await conn.fetchrow("""
                INSERT INTO om_clientes (nombre, apellidos, telefono, email,
                    fecha_nacimiento, nif, direccion,
                    metodo_pago_habitual,
                    consentimiento_datos, consentimiento_marketing,
                    consentimiento_compartir_tenants, fecha_consentimiento)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, now())
                RETURNING id
            """, data.nombre, data.apellidos, data.telefono, data.email,
                data.fecha_nacimiento, data.nif, data.direccion,
                data.metodo_pago,
                data.consentimiento_datos, data.consentimiento_marketing,
                data.consentimiento_compartir_tenants)

            cliente_id = cliente_row["id"]

            # 2. Crear relación tenant
            await conn.execute("""
                INSERT INTO om_cliente_tenant (cliente_id, tenant_id, estado, fuente_captacion)
                VALUES ($1, $2, 'activo', 'onboarding_selfservice')
            """, cliente_id, TENANT)

            # 3. Datos clínicos (si hay)
            datos_clinicos = []
            if data.lesiones:
                datos_clinicos.append(("restriccion", "Lesiones", data.lesiones))
            if data.patologias:
                datos_clinicos.append(("diagnostico", "Patologías", data.patologias))
            if data.medicacion:
                datos_clinicos.append(("medicacion", "Medicación", data.medicacion))
            if data.restricciones:
                datos_clinicos.append(("restriccion", "Restricciones", data.restricciones))
            if data.medico_derivante:
                datos_clinicos.append(("derivacion_medica", "Derivado por", data.medico_derivante))

            for tipo, titulo, contenido in datos_clinicos:
                await conn.execute("""
                    INSERT INTO om_datos_clinicos (cliente_id, tenant_id, tipo, titulo,
                        contenido, autor, visible_para, consentimiento_registrado, base_legal)
                    VALUES ($1, $2, $3, $4, $5, 'cliente_autoregistro', $6, true, 'consentimiento')
                """, cliente_id, TENANT, tipo, titulo, contenido,
                    [TENANT])

            # 4. Crear contrato
            contrato_id = None
            if data.tipo_contrato == "grupo" and data.grupo_id:
                grupo = await conn.fetchrow("""
                    SELECT capacidad_max FROM om_grupos WHERE id = $1 AND tenant_id = $2
                """, data.grupo_id, TENANT)
                if not grupo:
                    raise HTTPException(404, "Grupo no encontrado")

                ocupados = await conn.fetchval("""
                    SELECT count(*) FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)
                if ocupados >= grupo["capacidad_max"]:
                    raise HTTPException(409, "Grupo lleno, selecciona otro")

                precio = await conn.fetchval(
                    "SELECT precio_mensual FROM om_grupos WHERE id = $1", data.grupo_id)

                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo, grupo_id,
                        precio_mensual, fecha_inicio)
                    VALUES ($1, $2, 'grupo', $3, $4, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id, data.grupo_id, precio)
                contrato_id = contrato_row["id"]

            elif data.tipo_contrato == "individual":
                precio = data.precio_sesion or 35.00
                contrato_row = await conn.fetchrow("""
                    INSERT INTO om_contratos (tenant_id, cliente_id, tipo,
                        frecuencia_semanal, precio_sesion, ciclo_cobro, fecha_inicio)
                    VALUES ($1, $2, 'individual', $3, $4, $5, CURRENT_DATE)
                    RETURNING id
                """, TENANT, cliente_id,
                    data.frecuencia_semanal or 1, precio,
                    data.ciclo_cobro or 'sesion')
                contrato_id = contrato_row["id"]

            # 5. Marcar enlace como completado
            await conn.execute("""
                UPDATE om_onboarding_links
                SET estado = 'completado', cliente_id = $1,
                    fecha_completado = now()
                WHERE token = $2
            """, cliente_id, token)

            # 6. Activar portal del cliente
            from src.pilates.portal import activar_portal
            portal_token = await activar_portal(cliente_id)

    log.info("onboarding_completado", cliente_id=str(cliente_id),
             nombre=f"{data.nombre} {data.apellidos}",
             tipo=data.tipo_contrato)

    return {
        "status": "ok",
        "cliente_id": str(cliente_id),
        "contrato_id": str(contrato_id) if contrato_id else None,
        "mensaje": f"Bienvenido/a {data.nombre}! Tu inscripción está completa.",
        "portal_url": f"https://motor-semantico-omni.fly.dev/portal/{portal_token}",
    }


# ============================================================
# PORTAL CLIENTE
# ============================================================

@router.post("/portal/generar-todos")
async def generar_portales():
    """Genera portales para todos los clientes activos que no tienen uno."""
    from src.pilates.portal import activar_portal
    pool = await _get_pool()
    generados = 0

    async with pool.acquire() as conn:
        clientes = await conn.fetch("""
            SELECT ct.cliente_id FROM om_cliente_tenant ct
            LEFT JOIN om_onboarding_links l ON l.cliente_id = ct.cliente_id AND l.es_portal = true
            WHERE ct.tenant_id = $1 AND ct.estado = 'activo' AND l.id IS NULL
        """, TENANT)

    for c in clientes:
        await activar_portal(c["cliente_id"])
        generados += 1

    return {"status": "ok", "portales_generados": generados}


# ============================================================
# PORTAL PÚBLICO — Chat captación
# ============================================================

class ChatPublicoRequest(BaseModel):
    mensaje: str
    historial: Optional[list] = None

@router.post("/publico/chat")
async def chat_publico(data: ChatPublicoRequest):
    """Chat público de captación — sin autenticación."""
    from src.pilates.portal_publico import chat_captacion
    return await chat_captacion(data.mensaje, historial=data.historial)


# ============================================================
# RGPD — Derechos del interesado (Apple-grade privacy)
# ============================================================

@router.get("/publico/mis-datos/{cliente_id}")
async def rgpd_mis_datos(cliente_id: UUID):
    """RGPD Art. 15+20: Exporta todos los datos del cliente."""
    from src.pilates.rgpd import exportar_datos_cliente
    return await exportar_datos_cliente(cliente_id)


@router.post("/publico/borrar-cuenta/{cliente_id}")
async def rgpd_borrar_cuenta(cliente_id: UUID):
    """RGPD Art. 17: Solicita borrado de datos personales."""
    from src.pilates.rgpd import solicitar_borrado
    return await solicitar_borrado(cliente_id)
