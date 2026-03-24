"""Sub-router: Sesiones, Asistencias, Grupos."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, time, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict, _observar_crud,
    SesionCreate, MarcarAsistencia, MarcarAsistenciaGrupo,
)

router = APIRouter(tags=["sesiones"])


# ============================================================
# GRUPOS
# ============================================================

@router.get("/grupos")
async def listar_grupos(estado: Optional[str] = "activo"):
    """Lista grupos con plazas ocupadas."""
    estado = estado or None  # tratar string vacío como sin filtro
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.*,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as plazas_ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND ($2::text IS NULL OR g.estado = $2)
            ORDER BY g.nombre
        """, TENANT, estado)
    return [_row_to_dict(r) for r in rows]


@router.get("/grupos/{grupo_id}")
async def obtener_grupo(grupo_id: UUID):
    """Detalle grupo con miembros actuales."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupo = await conn.fetchrow(
            "SELECT id, nombre, tipo, capacidad_max, dias_semana, hora_inicio, hora_fin, precio_mensual, frecuencia_semanal, estado, tenant_id FROM om_grupos WHERE id = $1 AND tenant_id = $2",  # TODO: specify columns — revisa si faltan
            grupo_id, TENANT)
        if not grupo:
            raise HTTPException(404, "Grupo no encontrado")

        miembros = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono, co.id as contrato_id,
                   co.estado as contrato_estado, co.fecha_inicio
            FROM om_contratos co
            JOIN om_clientes c ON c.id = co.cliente_id
            WHERE co.grupo_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
            ORDER BY c.apellidos, c.nombre
        """, grupo_id, TENANT)

    return {
        **_row_to_dict(grupo),
        "miembros": [_row_to_dict(m) for m in miembros],
        "plazas_ocupadas": len(miembros),
    }


@router.get("/grupos/{grupo_id}/agenda")
async def agenda_grupo(grupo_id: UUID, fecha: Optional[date] = None):
    """Agenda de un grupo para una fecha. Default: hoy."""
    fecha = fecha or date.today()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar sesión de ese día
        sesion = await conn.fetchrow("""
            SELECT id, grupo_id, fecha, hora_inicio, hora_fin, tipo, estado, tenant_id
            FROM om_sesiones
            WHERE grupo_id = $1 AND fecha = $2 AND tenant_id = $3
        """, grupo_id, fecha, TENANT)

        if not sesion:
            miembros = await conn.fetch("""
                SELECT c.id as cliente_id, c.nombre, c.apellidos
                FROM om_contratos co
                JOIN om_clientes c ON c.id = co.cliente_id
                WHERE co.grupo_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
                ORDER BY c.apellidos
            """, grupo_id, TENANT)
            return {
                "fecha": str(fecha),
                "sesion": None,
                "asistentes": [{"cliente_id": str(m["cliente_id"]),
                                "nombre": m["nombre"], "apellidos": m["apellidos"],
                                "estado": "sin_sesion"} for m in miembros],
            }

        # Sesión existe — cargar asistencias
        asistencias = await conn.fetch("""
            SELECT a.*, c.nombre, c.apellidos
            FROM om_asistencias a
            JOIN om_clientes c ON c.id = a.cliente_id
            WHERE a.sesion_id = $1
            ORDER BY c.apellidos
        """, sesion["id"])

    return {
        "fecha": str(fecha),
        "sesion": _row_to_dict(sesion),
        "asistentes": [_row_to_dict(a) for a in asistencias],
    }


# ============================================================
# SESIONES
# ============================================================

@router.post("/sesiones", status_code=201)
async def crear_sesion(data: SesionCreate):
    """Crea sesión. Si es grupo, auto-crea asistencias 'confirmada' para cada miembro activo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            h_inicio = time.fromisoformat(data.hora_inicio)
            h_fin = time.fromisoformat(data.hora_fin)

            row = await conn.fetchrow("""
                INSERT INTO om_sesiones (tenant_id, tipo, grupo_id, instructor, fecha,
                    hora_inicio, hora_fin)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, TENANT, data.tipo, data.grupo_id, data.instructor,
                data.fecha, h_inicio, h_fin)
            sesion_id = row["id"]

            asistencias_creadas = 0

            if data.tipo == "grupo" and data.grupo_id:
                # Auto-crear asistencias para todos los miembros activos del grupo
                miembros = await conn.fetch("""
                    SELECT cliente_id, id as contrato_id FROM om_contratos
                    WHERE grupo_id = $1 AND tenant_id = $2 AND estado = 'activo'
                """, data.grupo_id, TENANT)

                for m in miembros:
                    await conn.execute("""
                        INSERT INTO om_asistencias
                            (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                        VALUES ($1, $2, $3, $4, 'confirmada')
                    """, TENANT, sesion_id, m["cliente_id"], m["contrato_id"])
                    asistencias_creadas += 1

            elif data.tipo == "individual" and data.cliente_id:
                await conn.execute("""
                    INSERT INTO om_asistencias
                        (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                    VALUES ($1, $2, $3, $4, 'confirmada')
                """, TENANT, sesion_id, data.cliente_id, data.contrato_id)
                asistencias_creadas = 1

    log.info("sesion_creada", id=str(sesion_id), tipo=data.tipo,
             asistencias=asistencias_creadas)
    return {"id": str(sesion_id), "asistencias_creadas": asistencias_creadas}


@router.get("/sesiones/semana")
async def sesiones_semana(fecha: Optional[date] = None):
    """Sesiones de una semana completa (L-V) con asistentes y estado."""
    if fecha is None:
        fecha = date.today()
    lunes = fecha - timedelta(days=fecha.weekday())
    viernes = lunes + timedelta(days=4)

    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT s.id, s.tipo, s.grupo_id, s.fecha, s.hora_inicio, s.hora_fin, s.estado,
                   g.nombre as grupo_nombre, g.tipo as grupo_tipo, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as presentes,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado = 'no_vino') as ausentes,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id) as total_asistencias
            FROM om_sesiones s
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, lunes, viernes)

    dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    dias = []
    for i in range(5):
        dia_fecha = lunes + timedelta(days=i)
        sesiones_dia = [_row_to_dict(s) for s in sesiones if s["fecha"] == dia_fecha]
        dias.append({
            "fecha": str(dia_fecha),
            "dia_nombre": dias_nombre[i],
            "es_hoy": dia_fecha == date.today(),
            "sesiones": sesiones_dia,
        })

    return {
        "semana_inicio": str(lunes),
        "semana_fin": str(viernes),
        "dias": dias,
        "total_sesiones": len(sesiones),
    }


@router.get("/sesiones/hoy")
async def agenda_hoy(fecha: Optional[date] = None):
    """Agenda del día: todas las sesiones con asistencias. Default: hoy."""
    dia = fecha or date.today()
    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT s.*, g.nombre as grupo_nombre
            FROM om_sesiones s
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha = $2
            ORDER BY s.hora_inicio
        """, TENANT, dia)

        resultado = []
        for s in sesiones:
            asistencias = await conn.fetch("""
                SELECT a.*, c.nombre, c.apellidos
                FROM om_asistencias a
                JOIN om_clientes c ON c.id = a.cliente_id
                WHERE a.sesion_id = $1
                ORDER BY c.apellidos
            """, s["id"])
            resultado.append({
                **_row_to_dict(s),
                "asistentes": [_row_to_dict(a) for a in asistencias],
            })

    return {"fecha": str(dia), "sesiones": resultado}


@router.post("/sesiones/{sesion_id}/completar")
async def completar_sesion(sesion_id: UUID):
    """Marca sesión como completada. Asistencias 'confirmada' pasan a 'asistio'.
    Si es individual, genera cargo automático por sesión."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT id, grupo_id, tipo, estado, fecha, tenant_id FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")
            if sesion["estado"] == "completada":
                raise HTTPException(409, "Sesión ya completada")

            # Marcar sesión completada
            await conn.execute(
                "UPDATE om_sesiones SET estado = 'completada' WHERE id = $1",
                sesion_id)

            # Todas las confirmadas pasan a asistio
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'asistio'
                WHERE sesion_id = $1 AND estado = 'confirmada'
            """, sesion_id)

            cargos_creados = 0

            # Si individual: generar cargo por cada asistencia
            if sesion["tipo"] == "individual":
                asistencias = await conn.fetch("""
                    SELECT a.cliente_id, a.contrato_id, a.id as asistencia_id
                    FROM om_asistencias a
                    WHERE a.sesion_id = $1 AND a.estado = 'asistio'
                """, sesion_id)

                for a in asistencias:
                    # Obtener precio del contrato
                    precio = 35.0  # default
                    if a["contrato_id"]:
                        contrato = await conn.fetchrow(
                            "SELECT precio_sesion FROM om_contratos WHERE id = $1",
                            a["contrato_id"])
                        if contrato and contrato["precio_sesion"]:
                            precio = float(contrato["precio_sesion"])

                    await conn.execute("""
                        INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                            tipo, descripcion, base_imponible, iva_porcentaje,
                            sesion_id, asistencia_id, fecha_cargo)
                        VALUES ($1, $2, $3, 'sesion_individual', $4, $5, 21.00,
                            $6, $7, $8)
                    """, TENANT, a["cliente_id"], a["contrato_id"],
                        f"Sesión individual {sesion['fecha']}",
                        precio, sesion_id, a["asistencia_id"], sesion["fecha"])
                    cargos_creados += 1

            # Side-effect: actualizar días esperados
            try:
                from src.pilates.automatismos import actualizar_dias_esperados_asistencia
                await actualizar_dias_esperados_asistencia(sesion_id)
            except Exception as e:
                log.warning("dias_esperados_update_failed", error=str(e))

    log.info("sesion_completada", id=str(sesion_id), cargos=cargos_creados)
    return {"status": "completada", "cargos_creados": cargos_creados}


@router.post("/sesiones/{sesion_id}/marcar")
async def marcar_asistencia(sesion_id: UUID, data: MarcarAsistencia):
    """Marca asistencia individual. Si cancelada <12h, genera cargo por cancelación tardía."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT id, tipo, estado, fecha, grupo_id, tenant_id FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")

            # Buscar asistencia existente
            asistencia = await conn.fetchrow("""
                SELECT id FROM om_asistencias
                WHERE sesion_id = $1 AND cliente_id = $2
            """, sesion_id, data.cliente_id)

            cargo_creado = None

            if asistencia:
                await conn.execute("""
                    UPDATE om_asistencias SET estado = $1, notas_instructor = $2,
                        hora_cancelacion = CASE WHEN $1 = 'cancelada' THEN now() ELSE NULL END
                    WHERE id = $3
                """, data.estado, data.notas_instructor, asistencia["id"])
                asistencia_id = asistencia["id"]
            else:
                row = await conn.fetchrow("""
                    INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id,
                        contrato_id, estado, notas_instructor,
                        hora_cancelacion)
                    VALUES ($1, $2, $3, $4, $5, $6,
                        CASE WHEN $5 = 'cancelada' THEN now() ELSE NULL END)
                    RETURNING id
                """, TENANT, sesion_id, data.cliente_id, data.contrato_id,
                    data.estado, data.notas_instructor)
                asistencia_id = row["id"]

            # Cancelación tardía: <12h antes de la sesión
            if data.estado == "cancelada" and sesion["tipo"] == "individual":
                sesion_dt = datetime.combine(sesion["fecha"], sesion["hora_inicio"])
                horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600

                if horas_antes < 12:
                    # Obtener precio del contrato
                    precio = 35.0
                    if data.contrato_id:
                        contrato = await conn.fetchrow(
                            "SELECT precio_sesion FROM om_contratos WHERE id = $1",
                            data.contrato_id)
                        if contrato and contrato["precio_sesion"]:
                            precio = float(contrato["precio_sesion"])

                    await conn.execute("""
                        INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id,
                            tipo, descripcion, base_imponible, iva_porcentaje,
                            sesion_id, asistencia_id, fecha_cargo)
                        VALUES ($1, $2, $3, 'cancelacion_tardia',
                            $4, $5, 21.00, $6, $7, $8)
                    """, TENANT, data.cliente_id, data.contrato_id,
                        f"Cancelación tardía sesión {sesion['fecha']}",
                        precio, sesion_id, asistencia_id, sesion["fecha"])
                    cargo_creado = "cancelacion_tardia"

                    await conn.execute("""
                        UPDATE om_asistencias SET genera_cargo = true, cargo_monto = $1
                        WHERE id = $2
                    """, precio, asistencia_id)

    log.info("asistencia_marcada", sesion=str(sesion_id),
             cliente=str(data.cliente_id), estado=data.estado, cargo=cargo_creado)
    asyncio.create_task(_observar_crud("asistencia", "crear", {"sesion_id": str(sesion_id), "cliente_id": str(data.cliente_id), "estado": data.estado}))
    return {"status": "marcada", "estado": data.estado, "cargo_creado": cargo_creado}


@router.post("/sesiones/{sesion_id}/marcar-grupo")
async def marcar_grupo(sesion_id: UUID, data: MarcarAsistenciaGrupo):
    """Marca asistencia grupal. Default=viene. Solo se envían las ausencias."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            sesion = await conn.fetchrow(
                "SELECT id, tipo, estado, fecha, grupo_id, tenant_id FROM om_sesiones WHERE id = $1 AND tenant_id = $2",
                sesion_id, TENANT)
            if not sesion:
                raise HTTPException(404, "Sesión no encontrada")
            if sesion["tipo"] != "grupo":
                raise HTTPException(400, "Esta sesión no es de grupo")

            # Todos los que no están en ausencias -> asistio
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'asistio'
                WHERE sesion_id = $1 AND estado = 'confirmada'
            """, sesion_id)

            # Los de la lista de ausencias -> no_vino
            marcados_ausentes = 0
            for cliente_id in data.ausencias:
                result = await conn.execute("""
                    UPDATE om_asistencias SET estado = 'no_vino'
                    WHERE sesion_id = $1 AND cliente_id = $2
                """, sesion_id, cliente_id)
                if result != "UPDATE 0":
                    marcados_ausentes += 1

            # Notas por alumno
            if data.notas:
                for cid_str, nota in data.notas.items():
                    await conn.execute("""
                        UPDATE om_asistencias SET notas_instructor = $1
                        WHERE sesion_id = $2 AND cliente_id = $3
                    """, nota, sesion_id, UUID(cid_str))

            # Contar asistentes finales
            conteo = await conn.fetchrow("""
                SELECT
                    count(*) FILTER (WHERE estado = 'asistio') as asistieron,
                    count(*) FILTER (WHERE estado = 'no_vino') as no_vinieron,
                    count(*) as total
                FROM om_asistencias WHERE sesion_id = $1
            """, sesion_id)

    # Side-effect: actualizar días esperados
    try:
        from src.pilates.automatismos import actualizar_dias_esperados_asistencia
        await actualizar_dias_esperados_asistencia(sesion_id)
    except Exception as e:
        log.warning("dias_esperados_update_failed", error=str(e))

    log.info("grupo_marcado", sesion=str(sesion_id),
             asistieron=conteo["asistieron"], ausentes=conteo["no_vinieron"])
    return {
        "status": "marcado",
        "asistieron": conteo["asistieron"],
        "no_vinieron": conteo["no_vinieron"],
        "total": conteo["total"],
    }
