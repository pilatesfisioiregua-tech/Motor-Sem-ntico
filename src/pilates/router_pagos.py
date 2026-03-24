"""Sub-router: Cargos, Pagos, Facturas, Bizum, Cobros recurrentes, Resumen."""
from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict, _observar_crud,
    _generar_html_factura,
    CargoManual, PagoCreate,
    FacturaCreate, FacturaAnular,
    BizumEntrante,
)

router = APIRouter(tags=["pagos"])


# ============================================================
# CARGOS
# ============================================================

@router.get("/cargos")
async def listar_cargos(
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    mes: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """Lista cargos. Filtrable por estado, cliente, mes (YYYY-MM)."""
    pool = await _get_pool()
    conditions = ["c.tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if estado:
        conditions.append(f"c.estado = ${idx}")
        params.append(estado)
        idx += 1
    if cliente_id:
        conditions.append(f"c.cliente_id = ${idx}")
        params.append(cliente_id)
        idx += 1
    if mes:
        conditions.append(f"to_char(c.fecha_cargo, 'YYYY-MM') = ${idx}")
        params.append(mes)
        idx += 1

    conditions.append(f"1=1")  # ensure valid SQL
    where = " AND ".join(conditions)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT c.*, cl.nombre, cl.apellidos
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE {where}
            ORDER BY c.fecha_cargo DESC, c.created_at DESC
            LIMIT ${idx}
        """, *params, limit)

    return [_row_to_dict(r) for r in rows]


@router.post("/cargos", status_code=201)
async def crear_cargo_manual(data: CargoManual):
    """Crea cargo manual (producto, otro, etc.)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                tipo, descripcion, base_imponible, iva_porcentaje, fecha_cargo)
            VALUES ($1, $2, $3, $4, $5, $6, $7, CURRENT_DATE)
            RETURNING id, total
        """, TENANT, data.cliente_id, data.contrato_id,
            data.tipo, data.descripcion, data.base_imponible, data.iva_porcentaje)

    log.info("cargo_manual", id=str(row["id"]), tipo=data.tipo,
             total=float(row["total"]))
    return {"id": str(row["id"]), "total": float(row["total"])}


@router.post("/cargos/suscripciones-mes")
async def generar_suscripciones_mes(mes: Optional[date] = None):
    """Genera cargos de suscripción mensual para todos los contratos grupo activos.
    Idempotente: no duplica si ya existen cargos del mismo periodo."""
    periodo = mes or date.today().replace(day=1)
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            contratos = await conn.fetch("""
                SELECT co.id, co.cliente_id, co.grupo_id, co.precio_mensual,
                       g.nombre as grupo_nombre
                FROM om_contratos co
                JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1 AND co.tipo = 'grupo'
                  AND co.estado = 'activo' AND co.precio_mensual IS NOT NULL
            """, TENANT)

            creados = 0
            omitidos = 0

            for co in contratos:
                # Idempotencia: verificar si ya existe cargo de suscripción para este periodo
                existente = await conn.fetchval("""
                    SELECT 1 FROM om_cargos
                    WHERE contrato_id = $1 AND tipo = 'suscripcion_grupo'
                      AND periodo_mes = $2 AND tenant_id = $3
                """, co["id"], periodo, TENANT)

                if existente:
                    omitidos += 1
                    continue

                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                        tipo, descripcion, base_imponible, iva_porcentaje,
                        periodo_mes, fecha_cargo)
                    VALUES ($1, $2, $3, 'suscripcion_grupo', $4, $5, 21.00, $6, $7)
                """, TENANT, co["cliente_id"], co["id"],
                    f"Suscripción {co['grupo_nombre']} {periodo.strftime('%B %Y')}",
                    float(co["precio_mensual"]), periodo, periodo)
                creados += 1

    log.info("suscripciones_mes", periodo=str(periodo), creados=creados,
             omitidos=omitidos)
    return {"periodo": str(periodo), "creados": creados, "omitidos": omitidos}


# ============================================================
# PAGOS
# ============================================================

@router.post("/pagos", status_code=201)
async def registrar_pago(data: PagoCreate):
    """Registra pago y concilia FIFO con cargos pendientes más antiguos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            # Crear pago
            row = await conn.fetchrow("""
                INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto,
                    referencia_externa, notas)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, TENANT, data.cliente_id, data.metodo, data.monto,
                data.referencia_externa, data.notas)
            pago_id = row["id"]

            # FIFO: obtener cargos pendientes ordenados por antigüedad
            cargos_pendientes = await conn.fetch("""
                SELECT id, total FROM om_cargos
                WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
                ORDER BY fecha_cargo ASC, created_at ASC
            """, data.cliente_id, TENANT)

            remanente = data.monto
            cargos_conciliados = 0

            for cargo in cargos_pendientes:
                if remanente <= 0:
                    break

                cargo_total = float(cargo["total"])
                aplicado = min(remanente, cargo_total)

                # Registrar relación pago-cargo
                await conn.execute("""
                    INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado)
                    VALUES ($1, $2, $3)
                """, pago_id, cargo["id"], aplicado)

                # Si cubre el cargo completo, marcarlo como cobrado
                if aplicado >= cargo_total:
                    await conn.execute("""
                        UPDATE om_cargos SET estado = 'cobrado', fecha_cobro = CURRENT_DATE
                        WHERE id = $1
                    """, cargo["id"])

                remanente -= aplicado
                cargos_conciliados += 1

    log.info("pago_registrado", id=str(pago_id), monto=data.monto,
             cargos_conciliados=cargos_conciliados, remanente=round(remanente, 2))
    asyncio.create_task(_observar_crud("pago", "crear", {"id": str(pago_id), "cliente_id": str(data.cliente_id), "monto": str(data.monto)}))
    return {
        "id": str(pago_id),
        "monto": data.monto,
        "cargos_conciliados": cargos_conciliados,
        "remanente": round(remanente, 2),
    }


@router.get("/pagos")
async def listar_pagos(
    cliente_id: Optional[UUID] = None,
    limit: int = Query(default=50, le=200),
):
    """Lista pagos recientes."""
    pool = await _get_pool()
    conditions = ["p.tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if cliente_id:
        conditions.append(f"p.cliente_id = ${idx}")
        params.append(cliente_id)
        idx += 1

    where = " AND ".join(conditions)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT p.*, cl.nombre, cl.apellidos
            FROM om_pagos p
            JOIN om_clientes cl ON cl.id = p.cliente_id
            WHERE {where}
            ORDER BY p.fecha_pago DESC, p.created_at DESC
            LIMIT ${idx}
        """, *params, limit)

    return [_row_to_dict(r) for r in rows]


# ============================================================
# RESUMEN / DASHBOARD
# ============================================================

@router.get("/resumen")
async def resumen_mes(mes: Optional[str] = None):
    """Dashboard del mes: ingresos, deuda, sesiones, asistencia.
    mes formato YYYY-MM. Default: mes actual."""
    if mes:
        inicio = date.fromisoformat(f"{mes}-01")
    else:
        hoy = date.today()
        inicio = hoy.replace(day=1)

    if inicio.month == 12:
        fin = inicio.replace(year=inicio.year + 1, month=1)
    else:
        fin = inicio.replace(month=inicio.month + 1)

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Ingresos (pagos del mes)
        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago < $3
        """, TENANT, inicio, fin)

        # Deuda pendiente total
        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)

        # Cargos del mes
        cargos_mes = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(total), 0) as total_facturado,
                count(*) as n_cargos,
                count(*) FILTER (WHERE estado = 'cobrado') as cobrados,
                count(*) FILTER (WHERE estado = 'pendiente') as pendientes
            FROM om_cargos
            WHERE tenant_id = $1 AND fecha_cargo >= $2 AND fecha_cargo < $3
        """, TENANT, inicio, fin)

        # Sesiones del mes
        sesiones_mes = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE estado = 'completada') as completadas,
                count(*) FILTER (WHERE tipo = 'individual') as individuales,
                count(*) FILTER (WHERE tipo = 'grupo') as grupo
            FROM om_sesiones
            WHERE tenant_id = $1 AND fecha >= $2 AND fecha < $3
        """, TENANT, inicio, fin)

        # Asistencia del mes
        asistencia = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistieron,
                count(*) FILTER (WHERE a.estado = 'no_vino') as no_vinieron,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha < $3
        """, TENANT, inicio, fin)

        # Gastos del mes
        gastos = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_gastos
            WHERE tenant_id = $1 AND fecha_gasto >= $2 AND fecha_gasto < $3
        """, TENANT, inicio, fin)

        # Clientes activos
        clientes_activos = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT)

    pct_asist = 0
    if asistencia["total"] > 0:
        pct_asist = round(asistencia["asistieron"] / asistencia["total"] * 100, 1)

    return {
        "mes": str(inicio),
        "ingresos": float(ingresos),
        "gastos": float(gastos),
        "resultado_neto": float(ingresos) - float(gastos),
        "deuda_pendiente_total": float(deuda),
        "cargos": {
            "total_facturado": float(cargos_mes["total_facturado"]),
            "n_cargos": cargos_mes["n_cargos"],
            "cobrados": cargos_mes["cobrados"],
            "pendientes": cargos_mes["pendientes"],
        },
        "sesiones": {
            "total": sesiones_mes["total"],
            "completadas": sesiones_mes["completadas"],
            "individuales": sesiones_mes["individuales"],
            "grupo": sesiones_mes["grupo"],
        },
        "asistencia": {
            "total": asistencia["total"],
            "asistieron": asistencia["asistieron"],
            "no_vinieron": asistencia["no_vinieron"],
            "canceladas": asistencia["canceladas"],
            "pct_asistencia": pct_asist,
        },
        "clientes_activos": clientes_activos,
    }


# ============================================================
# BIZUM ENTRANTE
# ============================================================

@router.post("/bizum-entrante")
async def bizum_entrante(data: BizumEntrante):
    """Registra Bizum entrante: busca cliente por teléfono + concilia FIFO."""
    from src.pilates.automatismos import conciliar_bizum_entrante
    result = await conciliar_bizum_entrante(data.telefono, data.monto, data.referencia)
    if result.get("status") == "error":
        raise HTTPException(404, result["detail"])
    return result


# ============================================================
# FACTURACIÓN
# ============================================================

@router.post("/facturas", status_code=201)
async def crear_factura(data: FacturaCreate):
    """Crea factura desde cargos cobrados. Numera secuencialmente. VeriFactu ready."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        async with conn.transaction():
            # Verificar cliente
            cliente = await conn.fetchrow(
                "SELECT id, nombre, apellidos FROM om_clientes WHERE id = $1", data.cliente_id)
            if not cliente:
                raise HTTPException(404, "Cliente no encontrado")

            # Obtener cargos
            cargos = await conn.fetch("""
                SELECT id, concepto, base_imponible, total, estado, cliente_id, tenant_id
                FROM om_cargos
                WHERE id = ANY($1::uuid[]) AND cliente_id = $2 AND tenant_id = $3
            """, data.cargo_ids, data.cliente_id, TENANT)
            if len(cargos) != len(data.cargo_ids):
                raise HTTPException(400, "Algunos cargos no encontrados o no pertenecen al cliente")

            # Calcular totales
            base_total = sum(float(c["base_imponible"]) for c in cargos)
            iva_pct = 21.00  # Pilates = 21% IVA
            iva_total = round(base_total * iva_pct / 100, 2)
            total = round(base_total + iva_total, 2)

            # Siguiente número de factura
            year = date.today().year
            serie = "AP"
            ultimo_num = await conn.fetchval("""
                SELECT MAX(CAST(SPLIT_PART(numero_factura, '-', 3) AS INT))
                FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                    AND EXTRACT(YEAR FROM fecha_emision) = $3
            """, TENANT, serie, year)
            siguiente = (ultimo_num or 0) + 1
            numero = f"{serie}-{year}-{siguiente:04d}"

            # Hash VeriFactu (encadenado con factura anterior)
            hash_anterior = await conn.fetchval("""
                SELECT verifactu_hash FROM om_facturas
                WHERE tenant_id = $1 AND serie = $2
                ORDER BY created_at DESC LIMIT 1
            """, TENANT, serie)

            datos_hash = f"{numero}|{date.today()}|{total}|{hash_anterior or 'GENESIS'}"
            verifactu_hash = hashlib.sha256(datos_hash.encode()).hexdigest()

            # Crear factura con snapshot fiscal
            factura_row = await conn.fetchrow("""
                INSERT INTO om_facturas (
                    tenant_id, cliente_id, numero_factura, serie,
                    fecha_emision, fecha_operacion,
                    base_imponible, iva_porcentaje, iva_monto, total,
                    verifactu_hash, verifactu_hash_anterior,
                    cliente_nif, cliente_nombre_fiscal, cliente_direccion
                ) VALUES ($1,$2,$3,$4, CURRENT_DATE,$5, $6,$7,$8,$9, $10,$11, $12,$13,$14)
                RETURNING id
            """, TENANT, data.cliente_id, numero, serie,
                data.fecha_operacion,
                base_total, iva_pct, iva_total, total,
                verifactu_hash, hash_anterior,
                cliente["nif"],
                f"{cliente['nombre']} {cliente['apellidos']}",
                cliente["direccion"])

            factura_id = factura_row["id"]

            # Crear líneas de factura
            for cargo in cargos:
                bi = float(cargo["base_imponible"])
                iva_m = round(bi * iva_pct / 100, 2)
                await conn.execute("""
                    INSERT INTO om_factura_lineas (
                        factura_id, cargo_id, concepto, cantidad,
                        precio_unitario, base_imponible,
                        iva_porcentaje, iva_monto, total
                    ) VALUES ($1,$2,$3,1,$4,$5,$6,$7,$8)
                """, factura_id, cargo["id"],
                    cargo["descripcion"] or cargo["tipo"],
                    bi, bi, iva_pct, iva_m, round(bi + iva_m, 2))

    log.info("factura_creada", numero=numero, total=total, lineas=len(cargos))
    return {"id": str(factura_id), "numero": numero, "total": total, "status": "created"}


@router.get("/facturas")
async def listar_facturas(
    estado: Optional[str] = None,
    cliente_id: Optional[UUID] = None,
    year: Optional[int] = None,
    limit: int = 50
):
    """Lista facturas con filtros."""
    estado = estado or None
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["f.tenant_id = $1"]
        params: list = [TENANT]
        idx = 2

        if estado:
            conditions.append(f"f.estado = ${idx}"); params.append(estado); idx += 1
        if cliente_id:
            conditions.append(f"f.cliente_id = ${idx}"); params.append(cliente_id); idx += 1
        if year:
            conditions.append(f"EXTRACT(YEAR FROM f.fecha_emision) = ${idx}"); params.append(year); idx += 1

        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT f.*, cl.nombre, cl.apellidos
            FROM om_facturas f
            JOIN om_clientes cl ON cl.id = f.cliente_id
            WHERE {where}
            ORDER BY f.fecha_emision DESC, f.numero_factura DESC
            LIMIT ${idx}
        """, *params, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/facturas/paquete-gestor")
async def paquete_gestor(trimestre: Optional[int] = None, year: Optional[int] = None):
    """Resumen trimestral para la gestoría."""
    import calendar
    year = year or date.today().year
    if trimestre is None:
        trimestre = (date.today().month - 1) // 3 + 1

    mes_inicio = (trimestre - 1) * 3 + 1
    mes_fin = trimestre * 3
    fecha_inicio = date(year, mes_inicio, 1)
    fecha_fin = date(year, mes_fin, calendar.monthrange(year, mes_fin)[1])

    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Facturas emitidas
        facturas = await conn.fetch("""
            SELECT * FROM om_facturas
            WHERE tenant_id = $1 AND fecha_emision >= $2 AND fecha_emision <= $3
                AND estado = 'emitida'
            ORDER BY numero_factura
        """, TENANT, fecha_inicio, fecha_fin)

        iva_repercutido = sum(float(f["iva_monto"]) for f in facturas)
        base_ingresos = sum(float(f["base_imponible"]) for f in facturas)
        total_ingresos = sum(float(f["total"]) for f in facturas)

        # Gastos del trimestre
        gastos = await conn.fetch("""
            SELECT * FROM om_gastos
            WHERE tenant_id = $1 AND fecha_gasto >= $2 AND fecha_gasto <= $3
            ORDER BY fecha_gasto
        """, TENANT, fecha_inicio, fecha_fin)

        iva_soportado = sum(float(g["iva_soportado"] or 0) for g in gastos)
        base_gastos = sum(float(g["base_imponible"]) for g in gastos)
        total_gastos = sum(float(g["total"]) for g in gastos)

        # Gastos por categoría
        gastos_por_cat: dict = {}
        for g in gastos:
            cat = g["categoria"]
            gastos_por_cat[cat] = gastos_por_cat.get(cat, 0) + float(g["total"])

    return {
        "trimestre": f"Q{trimestre} {year}",
        "periodo": f"{fecha_inicio} a {fecha_fin}",
        "ingresos": {
            "facturas_emitidas": len(facturas),
            "base_imponible": round(base_ingresos, 2),
            "iva_repercutido": round(iva_repercutido, 2),
            "total": round(total_ingresos, 2),
        },
        "gastos": {
            "total_gastos": len(gastos),
            "base_imponible": round(base_gastos, 2),
            "iva_soportado": round(iva_soportado, 2),
            "total": round(total_gastos, 2),
            "por_categoria": gastos_por_cat,
        },
        "iva_liquidar": round(iva_repercutido - iva_soportado, 2),
        "resultado_neto": round(base_ingresos - base_gastos, 2),
    }


@router.get("/facturas/{factura_id}")
async def obtener_factura(factura_id: UUID):
    """Detalle de factura con líneas."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch("""
            SELECT * FROM om_factura_lineas WHERE factura_id = $1 ORDER BY created_at
        """, factura_id)

        cliente = await conn.fetchrow(
            "SELECT * FROM om_clientes WHERE id = $1", factura["cliente_id"])

    return {
        **_row_to_dict(factura),
        "lineas": [_row_to_dict(l) for l in lineas],
        "cliente": _row_to_dict(cliente) if cliente else None,
    }


@router.post("/facturas/{factura_id}/anular")
async def anular_factura(factura_id: UUID, data: FacturaAnular):
    """Anula factura. No se borra — se marca como anulada (VeriFactu)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_facturas SET estado = 'anulada'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'emitida'
        """, factura_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Factura no encontrada o ya anulada")

    log.info("factura_anulada", id=str(factura_id), motivo=data.motivo)
    return {"status": "anulada"}


@router.post("/facturas/{factura_id}/pdf")
async def generar_pdf_factura(factura_id: UUID):
    """Genera PDF/HTML de la factura."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        factura = await conn.fetchrow(
            "SELECT * FROM om_facturas WHERE id = $1 AND tenant_id = $2",
            factura_id, TENANT)
        if not factura:
            raise HTTPException(404, "Factura no encontrada")

        lineas = await conn.fetch(
            "SELECT * FROM om_factura_lineas WHERE factura_id = $1", factura_id)

    # Generar HTML de la factura
    html = _generar_html_factura(factura, lineas)

    # Intentar generar PDF con weasyprint
    try:
        from weasyprint import HTML as WeasyHTML
        pdf_filename = f"factura_{factura['numero_factura'].replace('-','_')}.pdf"
        pdf_path = f"/tmp/{pdf_filename}"
        WeasyHTML(string=html).write_pdf(pdf_path)

        # Guardar path en DB
        async with pool.acquire() as conn2:
            await conn2.execute(
                "UPDATE om_facturas SET pdf_path = $1 WHERE id = $2",
                pdf_path, factura_id)

        return {"status": "ok", "pdf_path": pdf_path, "filename": pdf_filename}
    except ImportError:
        # Sin weasyprint: devolver HTML para window.print() del navegador
        return {"status": "html_only", "html": html,
                "nota": "Instalar weasyprint para PDF nativo"}


@router.post("/facturas/auto-facturar")
async def auto_facturar():
    """Lista candidatos para facturación automática."""
    pool = await _get_pool()

    async with pool.acquire() as conn:
        clientes_con_cargos = await conn.fetch("""
            SELECT DISTINCT c.cliente_id, cl.nombre, cl.apellidos
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            LEFT JOIN om_factura_lineas fl ON fl.cargo_id = c.id
            WHERE c.tenant_id = $1 AND c.estado = 'cobrado' AND fl.id IS NULL
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
        """, TENANT)

    return {
        "status": "ok",
        "clientes_con_cargos_sin_factura": len(clientes_con_cargos),
        "clientes": [{"id": str(c["cliente_id"]),
                       "nombre": f"{c['nombre']} {c['apellidos']}"}
                      for c in clientes_con_cargos],
        "nota": "Auto-facturación pendiente de campo preferencia_facturacion en om_clientes"
    }


# ============================================================
# COBROS RECURRENTES
# ============================================================

@router.get("/cobros-recurrentes")
async def get_cobros_recurrentes(limite: int = 20):
    """Lista últimos cobros automáticos."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT ca.*, c.nombre, c.apellidos
            FROM om_cobros_automaticos ca
            LEFT JOIN om_clientes c ON c.id = ca.cliente_id
            WHERE ca.tenant_id = $1
            ORDER BY ca.created_at DESC LIMIT $2
        """, TENANT, limite)
    return [_row_to_dict(r) for r in rows]
