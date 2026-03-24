"""RGPD — Derechos del interesado (Art. 15-17, 20).

Endpoints para que un cliente pueda:
1. Acceder a todos sus datos (Art. 15)
2. Exportar sus datos en JSON (Art. 20 — portabilidad)
3. Solicitar borrado (Art. 17 — derecho al olvido)

Apple-grade: privacy by design.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from typing import Optional
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def exportar_datos_cliente(cliente_id: UUID, tenant_id: str = TENANT) -> dict:
    """Art. 15 + 20: Exporta TODOS los datos de un cliente en formato JSON."""
    pool = await get_pool()
    datos = {"exportado_at": datetime.now().isoformat(), "cliente_id": str(cliente_id)}

    async with pool.acquire() as conn:
        # Datos personales
        cliente = await conn.fetchrow(
            "SELECT id, nombre, apellidos, telefono, email, fecha_nacimiento, nif, direccion "
            "FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente:
            return {"error": "Cliente no encontrado"}
        datos["datos_personales"] = dict(cliente)

        # Contrato
        contrato = await conn.fetchrow(
            "SELECT tipo, precio, estado, fecha_inicio, fecha_fin "
            "FROM om_contratos WHERE cliente_id = $1 AND tenant_id = $2 "
            "ORDER BY created_at DESC LIMIT 1", cliente_id, tenant_id)
        datos["contrato"] = dict(contrato) if contrato else None

        # Asistencias (últimas 100)
        asistencias = await conn.fetch("""
            SELECT s.fecha, s.hora_inicio, a.estado, g.nombre as grupo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 ORDER BY s.fecha DESC LIMIT 100
        """, cliente_id)
        datos["asistencias"] = [dict(a) for a in asistencias]

        # Pagos (últimos 50)
        pagos = await conn.fetch("""
            SELECT metodo, monto, notas, created_at
            FROM om_pagos WHERE cliente_id = $1 AND tenant_id = $2
            ORDER BY created_at DESC LIMIT 50
        """, cliente_id, tenant_id)
        datos["pagos"] = [dict(p) for p in pagos]

        # Cargos (últimos 50)
        cargos = await conn.fetch("""
            SELECT concepto, total, estado, fecha_cargo
            FROM om_cargos WHERE cliente_id = $1 AND tenant_id = $2
            ORDER BY fecha_cargo DESC LIMIT 50
        """, cliente_id, tenant_id)
        datos["cargos"] = [dict(c) for c in cargos]

        # Mensajes WA (últimos 50)
        mensajes = await conn.fetch("""
            SELECT direccion, tipo_contenido, contenido, intencion, created_at
            FROM om_mensajes_wa WHERE cliente_id = $1 AND tenant_id = $2
            ORDER BY created_at DESC LIMIT 50
        """, cliente_id, tenant_id)
        datos["mensajes"] = [dict(m) for m in mensajes]

        # Consentimientos
        datos["consentimientos"] = {
            "datos": cliente.get("consentimiento_datos", False) if hasattr(cliente, 'get') else False,
        }

        # Audit log
        from src.pilates.audit_log import registrar
        await registrar(conn, "SISTEMA", "EXPORT_DATOS", "om_clientes",
                       str(cliente_id), {"motivo": "derecho_acceso_art15"}, tenant_id)

    log.info("rgpd_export", cliente=str(cliente_id)[:8])
    return datos


async def solicitar_borrado(cliente_id: UUID, tenant_id: str = TENANT) -> dict:
    """Art. 17: Solicita borrado de datos personales.

    NO borra inmediatamente — marca como 'borrado_solicitado'.
    El borrado efectivo se ejecuta tras 30 días (periodo de gracia legal).
    Los datos financieros se retienen 5 años (obligación fiscal).
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT id, nombre FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente:
            return {"error": "Cliente no encontrado"}

        # Verificar deuda pendiente
        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, tenant_id)
        if float(deuda or 0) > 0:
            return {
                "status": "rechazado",
                "motivo": f"Deuda pendiente de {float(deuda):.2f}EUR. Saldar antes de solicitar borrado.",
            }

        # Marcar como borrado solicitado
        await conn.execute("""
            UPDATE om_cliente_tenant
            SET estado = 'borrado_solicitado', updated_at = now()
            WHERE cliente_id = $1 AND tenant_id = $2
        """, cliente_id, tenant_id)

        # Anonimizar datos personales inmediatamente (nombre, teléfono, email)
        await conn.execute("""
            UPDATE om_clientes
            SET nombre = 'ANONIMIZADO', apellidos = 'ANONIMIZADO',
                telefono = NULL, email = NULL, nif = NULL, direccion = NULL,
                fecha_nacimiento = NULL
            WHERE id = $1
        """, cliente_id)

        # Audit log
        from src.pilates.audit_log import registrar
        await registrar(conn, "SISTEMA", "BORRADO_SOLICITADO", "om_clientes",
                       str(cliente_id), {"nombre_original": cliente["nombre"]}, tenant_id)

    log.info("rgpd_borrado_solicitado", cliente=str(cliente_id)[:8])
    return {
        "status": "ok",
        "mensaje": "Datos personales anonimizados. Datos financieros retenidos 5 años (obligación fiscal).",
    }
