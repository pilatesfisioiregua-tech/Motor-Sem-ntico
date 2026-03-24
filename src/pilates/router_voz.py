"""Sub-router: Voz, ADN, Depuración, Consejo, Briefing, ACD diagnóstico,
Dashboard profundo, Procesos, Conocimiento, Tensiones, Identidad, Contenido,
Competencia, Cockpit."""
from __future__ import annotations

import json
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from src.pilates.router import (
    TENANT, log, _get_pool, _row_to_dict, _calcular_readiness,
    ConsejoRequest, DecisionTernaria,
    ADNCreate, ADNUpdate,
    ProcesoCreate, ConocimientoCreate,
    TensionCreate, DepuracionCreate,
)

router = APIRouter(tags=["voz"])


# ============================================================
# MODO PROFUNDO — BRIEFING + DASHBOARD + ACD
# ============================================================

@router.get("/briefing")
async def obtener_briefing(semana: Optional[date] = None):
    """Genera briefing semanal bajo demanda."""
    from src.pilates.briefing import generar_briefing
    return await generar_briefing(semana)


@router.post("/briefing/enviar-wa")
async def enviar_briefing_wa():
    """Genera briefing y lo envía por WhatsApp a Jesús."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    import os
    tel_jesus = os.getenv("JESUS_TELEFONO", "")
    if tel_jesus:
        from src.pilates.whatsapp import enviar_texto
        await enviar_texto(tel_jesus, briefing["texto_wa"])
        return {"status": "enviado", "texto": briefing["texto_wa"]}
    return {"status": "generado_sin_envio", "texto": briefing["texto_wa"],
            "nota": "Configurar JESUS_TELEFONO en fly.io secrets"}


@router.post("/acd/diagnosticar")
async def diagnosticar_negocio():
    """Ejecuta diagnóstico ACD del negocio con datos reales (~$0.01)."""
    from src.pilates.briefing import generar_diagnostico_acd_tenant
    return await generar_diagnostico_acd_tenant()


@router.get("/acd/historial")
async def historial_acd(limit: int = 10):
    """Historial de diagnósticos ACD del negocio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, trigger, estado, estado_tipo, lentes, gap,
                   prescripcion, resultado, coste_usd, created_at
            FROM om_diagnosticos_tenant
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/dashboard")
async def dashboard_profundo():
    """Dashboard completo Modo Profundo: briefing + ACD + tendencias."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    pool = await _get_pool()
    async with pool.acquire() as conn:
        grupos = await conn.fetch("""
            SELECT g.nombre, g.tipo, g.capacidad_max, g.precio_mensual,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

        ingresos_mensuales = await conn.fetch("""
            SELECT date_trunc('month', fecha_pago)::date as mes,
                   SUM(monto) as total
            FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= CURRENT_DATE - interval '6 months'
            GROUP BY mes ORDER BY mes
        """, TENANT)

        depuraciones = await conn.fetch("""
            SELECT * FROM om_depuracion
            WHERE tenant_id = $1 AND estado IN ('propuesta', 'aprobada')
            ORDER BY created_at DESC LIMIT 5
        """, TENANT)

    briefing["grupos_detalle"] = [_row_to_dict(g) for g in grupos]
    briefing["ingresos_mensuales"] = [
        {"mes": str(r["mes"]), "total": float(r["total"])} for r in ingresos_mensuales
    ]
    briefing["depuraciones"] = [_row_to_dict(d) for d in depuraciones]

    # Readiness de replicación
    try:
        briefing["readiness"] = await _calcular_readiness()
    except Exception:
        briefing["readiness"] = None

    return briefing


# ============================================================
# SÉQUITO DE ASESORES
# ============================================================

@router.post("/consejo")
async def convocar_consejo_endpoint(data: ConsejoRequest):
    """Convoca el Consejo de Asesores. Coste: ~$0.05-0.50 según profundidad."""
    from src.pilates.sequito import convocar_consejo
    sesion = await convocar_consejo(
        pregunta=data.pregunta,
        profundidad=data.profundidad,
        ints_forzadas=data.ints_forzadas,
    )
    return {
        "status": "ok",
        "estado_acd": sesion.estado_acd_pre,
        "asesores_convocados": len(sesion.asesores),
        "respuestas": [{
            "int_id": r.int_id, "nombre": r.nombre,
            "P": r.pensamiento, "R": r.razonamiento,
            "respuesta": r.respuesta,
        } for r in sesion.asesores],
        "sintesis": sesion.sintesis,
        "puntos_ciegos": sesion.puntos_ciegos,
        "prescripcion_acd": sesion.prescripcion,
        "coste_usd": sesion.coste_total,
        "tiempo_s": sesion.tiempo_total,
    }


@router.get("/consejo/historial")
async def historial_consejo(limit: int = 10):
    """Historial de sesiones del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, pregunta, profundidad, estado_acd_pre,
                   inteligencias_convocadas, sintesis,
                   puntos_ciegos_cruzados, decision_ternaria,
                   coste_api, tiempo_ejecucion_s, created_at
            FROM om_sesiones_consejo
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/consejo/{sesion_id}")
async def detalle_consejo(sesion_id: UUID):
    """Detalle completo de una sesión del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM om_sesiones_consejo WHERE id = $1 AND tenant_id = $2
        """, sesion_id, TENANT)
        if not row:
            raise HTTPException(404, "Sesión no encontrada")
    return _row_to_dict(row)


@router.post("/consejo/{sesion_id}/decision")
async def registrar_decision(sesion_id: UUID, data: DecisionTernaria):
    """Registra decisión ternaria post-consejo: cierre/inerte/tóxico."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_sesiones_consejo
            SET decision_ternaria = $1, decision_confianza = $2,
                decision_razon = $3, decision_fecha = CURRENT_DATE
            WHERE id = $4 AND tenant_id = $5
        """, data.decision, data.confianza, data.razon, sesion_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Sesión no encontrada")
    return {"status": "ok"}


@router.get("/asesores")
async def listar_asesores():
    """Lista los 24 asesores disponibles."""
    from src.pilates.sequito import ASESORES
    return [{"id": k, **v} for k, v in ASESORES.items()]


# ============================================================
# ADN DEL NEGOCIO (F5 Identidad)
# ============================================================

@router.get("/adn")
async def listar_adn(categoria: Optional[str] = None, activo: bool = True):
    """Lista principios ADN. Filtro por categoría y estado activo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if activo:
            conditions.append("activo = true")
        if categoria:
            conditions.append(f"categoria = ${idx}"); params.append(categoria); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_adn WHERE {where} ORDER BY categoria, titulo
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.get("/adn/{adn_id}")
async def obtener_adn(adn_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_adn WHERE id = $1 AND tenant_id = $2", adn_id, TENANT)
        if not row:
            raise HTTPException(404, "Principio ADN no encontrado")
    return _row_to_dict(row)


@router.post("/adn", status_code=201)
async def crear_adn(data: ADNCreate):
    """Crea un principio ADN del negocio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)
    log.info("adn_creado", titulo=data.titulo, categoria=data.categoria)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/adn/{adn_id}")
async def actualizar_adn(adn_id: UUID, data: ADNUpdate):
    _CAMPOS_ADN = {"titulo", "descripcion", "ejemplos", "contra_ejemplos", "activo"}
    updates = {k: v for k, v in data.model_dump().items() if v is not None and k in _CAMPOS_ADN}
    if not updates:
        raise HTTPException(400, "Nada que actualizar")
    pool = await _get_pool()
    for k in ("ejemplos", "contra_ejemplos"):
        if k in updates and isinstance(updates[k], list):
            updates[k] = json.dumps(updates[k])
    set_clauses = ", ".join(f'"{k}" = ${i+2}' for i, k in enumerate(updates.keys()))
    values = [adn_id] + list(updates.values())
    tenant_idx = len(values) + 1
    values.append(TENANT)
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE om_adn SET {set_clauses}, version = version + 1, fecha_modificacion = CURRENT_DATE WHERE id = $1 AND tenant_id = ${tenant_idx}",
            *values)
    return {"status": "updated"}


@router.delete("/adn/{adn_id}")
async def desactivar_adn(adn_id: UUID):
    """No borra — marca como inactivo (historial)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE om_adn SET activo = false WHERE id = $1 AND tenant_id = $2",
            adn_id, TENANT)
    return {"status": "desactivado"}


# ============================================================
# PROCESOS DOCUMENTADOS (F7 Replicación)
# ============================================================

@router.get("/procesos")
async def listar_procesos(area: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if area:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 AND area = $2 ORDER BY area, titulo
            """, TENANT, area)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_procesos WHERE tenant_id = $1 ORDER BY area, titulo
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/procesos/{proceso_id}")
async def obtener_proceso(proceso_id: UUID):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not row:
            raise HTTPException(404, "Proceso no encontrado")
        await conn.execute("""
            UPDATE om_procesos SET veces_consultado = veces_consultado + 1, ultima_consulta = now()
            WHERE id = $1
        """, proceso_id)
    return _row_to_dict(row)


@router.post("/procesos", status_code=201)
async def crear_proceso(data: ProcesoCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_procesos (tenant_id, area, titulo, descripcion, pasos,
                notas, funcion_l07, vinculado_a_adn, documentado_por)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,'Jesus') RETURNING id
        """, TENANT, data.area, data.titulo, data.descripcion,
            json.dumps(data.pasos), data.notas, data.funcion_l07, data.vinculado_a_adn)
    log.info("proceso_creado", titulo=data.titulo, area=data.area)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/procesos/{proceso_id}")
async def actualizar_proceso(proceso_id: UUID, data: dict):
    """Actualiza proceso. Incrementa versión."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        actual = await conn.fetchrow(
            "SELECT * FROM om_procesos WHERE id = $1 AND tenant_id = $2", proceso_id, TENANT)
        if not actual:
            raise HTTPException(404, "Proceso no encontrado")
        titulo = data.get("titulo", actual["titulo"])
        descripcion = data.get("descripcion", actual["descripcion"])
        pasos = json.dumps(data["pasos"]) if "pasos" in data else actual["pasos"]
        notas = data.get("notas", actual["notas"])
        await conn.execute("""
            UPDATE om_procesos SET titulo=$1, descripcion=$2, pasos=$3::jsonb, notas=$4,
                version = version + 1, ultima_revision = CURRENT_DATE
            WHERE id = $5
        """, titulo, descripcion, pasos if isinstance(pasos, str) else json.dumps(pasos),
            notas, proceso_id)
    return {"status": "updated"}


# ============================================================
# CONOCIMIENTO EMERGENTE (F2 Sentido)
# ============================================================

@router.get("/conocimiento")
async def listar_conocimiento(tipo: Optional[str] = None, confianza: Optional[str] = None):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if tipo:
            conditions.append(f"tipo = ${idx}"); params.append(tipo); idx += 1
        if confianza:
            conditions.append(f"confianza = ${idx}"); params.append(confianza); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_conocimiento WHERE {where} ORDER BY fecha_descubrimiento DESC
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.post("/conocimiento", status_code=201)
async def crear_conocimiento(data: ConocimientoCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_conocimiento (tenant_id, tipo, titulo, descripcion,
                evidencia, confianza, origen)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7) RETURNING id
        """, TENANT, data.tipo, data.titulo, data.descripcion,
            json.dumps(data.evidencia) if data.evidencia else None,
            data.confianza, data.origen)
    log.info("conocimiento_creado", titulo=data.titulo, tipo=data.tipo)
    return {"id": str(row["id"]), "status": "created"}


@router.post("/conocimiento/{conocimiento_id}/promover-adn")
async def promover_a_adn(conocimiento_id: UUID, data: ADNCreate):
    """Promueve conocimiento consolidado a principio ADN.

    F2->F5: lo que se aprende (conocimiento) sube a lo que se es (ADN).
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        conoc = await conn.fetchrow(
            "SELECT * FROM om_conocimiento WHERE id = $1 AND tenant_id = $2",
            conocimiento_id, TENANT)
        if not conoc:
            raise HTTPException(404, "Conocimiento no encontrado")

        adn_row = await conn.fetchrow("""
            INSERT INTO om_adn (tenant_id, categoria, titulo, descripcion,
                ejemplos, contra_ejemplos, funcion_l07, lente)
            VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7,$8) RETURNING id
        """, TENANT, data.categoria, data.titulo, data.descripcion,
            json.dumps(data.ejemplos) if data.ejemplos else None,
            json.dumps(data.contra_ejemplos) if data.contra_ejemplos else None,
            data.funcion_l07, data.lente)

        await conn.execute("""
            UPDATE om_conocimiento SET promovido_a_adn = $1, confianza = 'consolidado'
            WHERE id = $2
        """, adn_row["id"], conocimiento_id)

    log.info("conocimiento_promovido", conocimiento=str(conocimiento_id), adn=str(adn_row["id"]))
    return {"status": "promovido", "adn_id": str(adn_row["id"])}


# ============================================================
# TENSIONES (F6 Adaptación)
# ============================================================

@router.get("/tensiones")
async def listar_tensiones(estado: Optional[str] = "activa"):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 AND estado = $2
                ORDER BY severidad DESC, fecha_inicio DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_tensiones WHERE tenant_id = $1 ORDER BY fecha_inicio DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/tensiones", status_code=201)
async def crear_tension(data: TensionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_tensiones (tenant_id, tipo, descripcion, funciones_afectadas,
                severidad, duracion_estimada_dias, detectada_por)
            VALUES ($1,$2,$3,$4,$5,$6,'manual') RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.funciones_afectadas,
            data.severidad, data.duracion_estimada_dias)
    log.info("tension_creada", tipo=data.tipo, severidad=data.severidad)
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/tensiones/{tension_id}")
async def actualizar_tension(tension_id: UUID, data: dict):
    """Actualiza tensión: resolver, marcar crónica, etc."""
    pool = await _get_pool()
    estado = data.get("estado")
    async with pool.acquire() as conn:
        if estado:
            if estado == "resuelta":
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1, fecha_fin = CURRENT_DATE
                    WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
            else:
                await conn.execute("""
                    UPDATE om_tensiones SET estado = $1 WHERE id = $2 AND tenant_id = $3
                """, estado, tension_id, TENANT)
    return {"status": "updated"}


# ============================================================
# DEPURACIÓN (F3 — "deja de hacer esto")
# ============================================================

@router.get("/depuracion")
async def listar_depuracion(estado: Optional[str] = None):
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        if estado:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1 AND d.estado = $2
                ORDER BY d.created_at DESC
            """, TENANT, estado)
        else:
            rows = await conn.fetch("""
                SELECT d.*, dt.estado as diagnostico_estado
                FROM om_depuracion d
                LEFT JOIN om_diagnosticos_tenant dt ON dt.id = d.diagnostico_id
                WHERE d.tenant_id = $1
                ORDER BY d.created_at DESC
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.post("/depuracion", status_code=201)
async def crear_depuracion(data: DepuracionCreate):
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_depuracion (tenant_id, tipo, descripcion, impacto_estimado,
                funcion_l07, lente, origen, diagnostico_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id
        """, TENANT, data.tipo, data.descripcion, data.impacto_estimado,
            data.funcion_l07, data.lente, data.origen, data.diagnostico_id)
    log.info("depuracion_creada", tipo=data.tipo, descripcion=data.descripcion[:50])
    return {"id": str(row["id"]), "status": "created"}


@router.patch("/depuracion/{depuracion_id}")
async def actualizar_depuracion(depuracion_id: UUID, data: dict):
    """Cambiar estado: propuesta -> aprobada -> ejecutada / descartada."""
    _ESTADOS_DEPURACION = {"propuesta", "aprobada", "ejecutada", "descartada"}
    pool = await _get_pool()
    estado = data.get("estado")
    resultado = data.get("resultado")
    if estado and estado not in _ESTADOS_DEPURACION:
        raise HTTPException(400, f"Estado inválido: {estado}")
    async with pool.acquire() as conn:
        updates = []
        params = [depuracion_id]
        idx = 2
        if estado:
            updates.append(f'"estado" = ${idx}'); params.append(estado); idx += 1
            if estado == "aprobada":
                updates.append('"fecha_decision" = CURRENT_DATE')
            elif estado == "ejecutada":
                updates.append('"fecha_ejecucion" = CURRENT_DATE')
        if resultado:
            updates.append(f'"resultado" = ${idx}'); params.append(resultado); idx += 1
        if not updates:
            raise HTTPException(400, "Nada que actualizar")
        set_clause = ", ".join(updates)
        tenant_idx = len(params) + 1
        params.append(TENANT)
        await conn.execute(
            f"UPDATE om_depuracion SET {set_clause} WHERE id = $1 AND tenant_id = ${tenant_idx}",
            *params)
    return {"status": "updated"}


# ============================================================
# BLOQUE VOZ
# ============================================================

@router.post("/voz/generar-propuestas")
async def generar_propuestas_voz():
    """Genera propuestas de comunicación basadas en datos internos."""
    from src.pilates.voz import generar_propuestas
    propuestas = await generar_propuestas()
    return {"status": "ok", "propuestas_generadas": len(propuestas), "propuestas": propuestas}


@router.get("/voz/propuestas")
async def listar_propuestas_voz(estado: Optional[str] = "pendiente", canal: Optional[str] = None):
    """Lista propuestas de Voz."""
    pool = await _get_pool()
    estado = estado or None
    async with pool.acquire() as conn:
        conditions = ["tenant_id = $1"]
        params = [TENANT]
        idx = 2
        if estado:
            conditions.append(f"estado = ${idx}"); params.append(estado); idx += 1
        if canal:
            conditions.append(f"canal = ${idx}"); params.append(canal); idx += 1
        where = " AND ".join(conditions)
        rows = await conn.fetch(f"""
            SELECT * FROM om_voz_propuestas WHERE {where}
            ORDER BY fecha_propuesta DESC LIMIT 50
        """, *params)
    return [_row_to_dict(r) for r in rows]


@router.patch("/voz/propuestas/{propuesta_id}")
async def decidir_propuesta(propuesta_id: UUID, data: dict):
    """Aprobar, descartar o editar propuesta."""
    _ESTADOS_PROPUESTA = {"aprobada", "descartada", "pendiente", "ejecutada"}
    pool = await _get_pool()
    estado = data.get("estado")
    if estado and estado not in _ESTADOS_PROPUESTA:
        raise HTTPException(400, f"Estado inválido: {estado}")
    async with pool.acquire() as conn:
        updates = ['"fecha_decision" = now()']
        params = [propuesta_id]
        idx = 2
        if estado:
            updates.append(f'"estado" = ${idx}'); params.append(estado); idx += 1
        if data.get("contenido_editado"):
            updates.append(f'"contenido_propuesto" = ${idx}::jsonb')
            params.append(json.dumps(data["contenido_editado"])); idx += 1
        set_clause = ", ".join(updates)
        tenant_idx = len(params) + 1
        params.append(TENANT)
        await conn.execute(
            f"UPDATE om_voz_propuestas SET {set_clause} WHERE id = $1 AND tenant_id = ${tenant_idx}",
            *params)
    return {"status": "updated"}


@router.post("/voz/propuestas/{propuesta_id}/ejecutar")
async def ejecutar_propuesta(propuesta_id: UUID):
    """Ejecuta propuesta aprobada: envía WA, publica contenido, etc."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        prop = await conn.fetchrow("""
            SELECT * FROM om_voz_propuestas WHERE id = $1 AND tenant_id = $2
        """, propuesta_id, TENANT)
        if not prop:
            raise HTTPException(404, "Propuesta no encontrada")
        if prop["estado"] not in ("aprobada", "editada"):
            raise HTTPException(400, "Solo se pueden ejecutar propuestas aprobadas")

        contenido = prop["contenido_propuesto"]
        resultado = {}

        # Ejecutar según canal
        if prop["canal"] == "whatsapp" and contenido.get("telefono"):
            from src.pilates.whatsapp import enviar_texto
            resultado = await enviar_texto(
                contenido["telefono"], contenido.get("texto", ""),
                UUID(contenido["cliente_id"]) if contenido.get("cliente_id") else None)
        else:
            resultado = {"status": "manual", "nota": f"Canal {prop['canal']} requiere ejecución manual"}

        # Marcar ejecutada
        await conn.execute("""
            UPDATE om_voz_propuestas SET estado = 'ejecutada', fecha_ejecucion = now(),
                resultado = $1::jsonb WHERE id = $2
        """, json.dumps(resultado), propuesta_id)

    return {"status": "ejecutada", "resultado": resultado}


@router.post("/voz/capa-a")
async def consultar_capa_a_endpoint(data: dict):
    """Consulta fuente externa de Capa A."""
    from src.pilates.voz import consultar_capa_a
    fuente = data.get("fuente", "perplexity")
    query = data.get("query", "")
    return await consultar_capa_a(fuente, query)


@router.get("/voz/capa-a/datos")
async def listar_datos_capa_a(fuente: Optional[str] = None, limit: int = 20):
    """Lista datos externos almacenados."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if fuente:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1 AND fuente = $2
                ORDER BY created_at DESC LIMIT $3
            """, TENANT, fuente, limit)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_capa_a WHERE tenant_id = $1
                ORDER BY created_at DESC LIMIT $2
            """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/isp/{canal}")
async def obtener_checklist_isp(canal: str):
    """Obtiene checklist ISP para un canal."""
    from src.pilates.voz import calcular_isp
    return await calcular_isp(canal)


@router.post("/voz/isp/{canal}")
async def guardar_auditoria_isp(canal: str, data: dict):
    """Guarda resultado de auditoría ISP."""
    from src.pilates.voz import guardar_isp
    return await guardar_isp(
        canal, data.get("elementos_cumplidos", []), data.get("score", 0))


@router.get("/voz/isp")
async def historial_isp():
    """Historial de auditorías ISP por canal."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_isp WHERE tenant_id = $1
            ORDER BY fecha_auditoria DESC LIMIT 20
        """, TENANT)
    return [_row_to_dict(r) for r in rows]


@router.get("/voz/telemetria")
async def telemetria_voz(canal: Optional[str] = None):
    """Telemetría de canales de voz."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        if canal:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1 AND canal = $2
                ORDER BY fecha DESC LIMIT 30
            """, TENANT, canal)
        else:
            rows = await conn.fetch("""
                SELECT * FROM om_voz_telemetria WHERE tenant_id = $1
                ORDER BY fecha DESC LIMIT 30
            """, TENANT)
    return [_row_to_dict(r) for r in rows]


# ============================================================
# COCKPIT — Interfaz generativa
# ============================================================

@router.get("/cockpit")
async def cockpit():
    """Contexto del día + módulos sugeridos para el Modo Estudio."""
    from src.pilates.cockpit import contexto_del_dia
    return await contexto_del_dia()

@router.post("/cockpit/config")
async def guardar_config_cockpit(data: dict):
    """Guarda qué módulos ha elegido Jesús (aprende preferencias)."""
    from src.pilates.cockpit import guardar_configuracion
    await guardar_configuracion(data.get("modulos", []))
    return {"status": "ok"}

@router.post("/cockpit/chat")
async def cockpit_chat(data: dict):
    """Chat conversacional para controlar la interfaz del cockpit.

    Devuelve action_plan si hay acciones que requieren confirmación.
    El frontend debe mostrar el plan y llamar a /cockpit/confirm para ejecutar.
    """
    from src.pilates.cockpit import chat_cockpit
    mensaje = data.get("mensaje", "")
    modulos_activos = data.get("modulos_activos", [])
    historial = data.get("historial", [])
    if not mensaje:
        return {"respuesta": "", "acciones": {"montar": [], "desmontar": [], "desmontar_todos": False}}
    return await chat_cockpit(mensaje, modulos_activos, historial)


@router.post("/cockpit/confirm")
async def cockpit_confirm(data: dict):
    """Ejecuta un plan de acciones confirmado por Jesús.

    Input: {"pasos": [{"accion": "...", "args": {...}, "descripcion": "..."}]}
    Output: {"ejecutados": N, "total": N, "todos_ok": bool, "resultados": [...]}
    """
    from src.pilates.cockpit import ejecutar_plan
    pasos = data.get("pasos", [])
    if not pasos:
        return {"error": "No hay pasos que ejecutar"}
    return await ejecutar_plan(pasos)


# ============================================================
# VOZ ESTRATÉGICO — Identidad + IRC + PCA + Diagnóstico (B-PIL-20a)
# ============================================================

@router.post("/voz/seed")
async def seed_voz_completo():
    """Seed completo: identidad + IRC + PCA + competidores."""
    from src.pilates.voz_identidad import (
        seed_identidad, seed_irc_inicial,
        seed_pca_inicial, seed_competidores,
    )
    r1 = await seed_identidad()
    r2 = await seed_irc_inicial()
    r3 = await seed_pca_inicial()
    r4 = await seed_competidores()
    return {"identidad": r1, "irc": r2, "pca": r3, "competidores": r4}

@router.get("/voz/identidad")
async def get_identidad_voz():
    from src.pilates.voz_identidad import obtener_identidad
    return await obtener_identidad()

@router.get("/voz/irc")
async def get_irc():
    from src.pilates.voz_identidad import obtener_irc
    return await obtener_irc()

@router.get("/voz/pca")
async def get_pca(segmento: Optional[str] = None):
    from src.pilates.voz_identidad import obtener_pca
    return await obtener_pca(segmento)

@router.get("/voz/competidores")
async def get_competidores():
    from src.pilates.voz_identidad import obtener_competidores
    return await obtener_competidores()

@router.get("/voz/diagnostico")
async def get_diagnostico():
    """Diagnóstico cruzado de presencia digital."""
    from src.pilates.voz_identidad import diagnosticar_presencia
    return await diagnosticar_presencia()


# ============================================================
# VOZ ESTRATÉGICO — Motor Tridimensional + Calendario (B-PIL-20b)
# ============================================================

@router.post("/voz/estrategia/calcular")
async def calcular_estrategia_endpoint():
    """Calcula estrategia semanal cruzando IRC x Matriz x PCA."""
    from src.pilates.voz_estrategia import calcular_estrategia
    return await calcular_estrategia()

@router.get("/voz/estrategia")
async def get_estrategia():
    """Devuelve estrategia activa + calendario de la semana."""
    from src.pilates.voz_estrategia import obtener_estrategia_activa
    return await obtener_estrategia_activa()

@router.post("/voz/calendario/{item_id}/aprobar")
async def aprobar_item(item_id: str):
    from src.pilates.voz_estrategia import aprobar_item_calendario
    return await aprobar_item_calendario(item_id)

@router.post("/voz/calendario/{item_id}/descartar")
async def descartar_item(item_id: str):
    from src.pilates.voz_estrategia import descartar_item_calendario
    return await descartar_item_calendario(item_id)


# ============================================================
# VOZ ESTRATÉGICO — Arquitecto de Presencia (B-PIL-20c)
# ============================================================

@router.post("/voz/perfil/{canal}/generar")
async def generar_perfil_canal(canal: str):
    from src.pilates.voz_arquitecto import generar_perfil
    return await generar_perfil(canal)

@router.post("/voz/perfiles/generar")
async def generar_todos_perfiles():
    from src.pilates.voz_arquitecto import generar_todos_los_perfiles
    return await generar_todos_los_perfiles()

@router.get("/voz/perfil/{canal}")
async def get_perfil_canal(canal: str):
    from src.pilates.voz_arquitecto import obtener_perfil
    return await obtener_perfil(canal)

@router.post("/voz/plantilla/{plantilla_id}/aprobar")
async def aprobar_plantilla_endpoint(plantilla_id: str):
    from src.pilates.voz_arquitecto import aprobar_plantilla
    return await aprobar_plantilla(plantilla_id)

@router.post("/voz/plantilla/{plantilla_id}/aplicada")
async def marcar_aplicada_endpoint(plantilla_id: str):
    from src.pilates.voz_arquitecto import marcar_aplicada
    return await marcar_aplicada(plantilla_id)


# ============================================================
# VOZ ESTRATÉGICO — 5 Ciclos + ISP + Telemetría (B-PIL-20d)
# ============================================================

@router.post("/voz/ciclo/escuchar")
async def ciclo_escuchar():
    from src.pilates.voz_ciclos import escuchar
    return await escuchar()

@router.get("/voz/senales")
async def get_senales():
    from src.pilates.voz_ciclos import priorizar
    return await priorizar()

@router.post("/voz/senales/{senal_id}/procesada")
async def senal_procesada(senal_id: str):
    from src.pilates.voz_ciclos import marcar_procesada
    return await marcar_procesada(senal_id)

@router.post("/voz/telemetria")
async def registrar_telemetria_endpoint(request: Request):
    """Registra métricas de un canal. Body: {canal, periodo, metricas: {...}}"""
    from src.pilates.voz_ciclos import registrar_telemetria
    body = await request.json()
    return await registrar_telemetria(
        body["canal"], body["periodo"], body.get("metricas", {})
    )

@router.post("/voz/irc/recalcular")
async def recalcular_irc_endpoint():
    from src.pilates.voz_ciclos import recalcular_irc
    return await recalcular_irc()

@router.get("/voz/isp-automatico")
async def get_isp_automatico():
    from src.pilates.voz_ciclos import calcular_isp_automatico
    return await calcular_isp_automatico()

@router.post("/voz/ciclo/completo")
async def ciclo_completo():
    from src.pilates.voz_ciclos import ejecutar_ciclo_completo
    return await ejecutar_ciclo_completo()


# ============================================================
# VOZ ESTRATÉGICO — Cron manual (B-PIL-20e)
# ============================================================

@router.post("/voz/cron/diaria")
async def cron_diaria_manual():
    from src.pilates.cron import _tarea_diaria
    await _tarea_diaria()
    return {"status": "ok", "tarea": "diaria"}

@router.post("/voz/cron/semanal")
async def cron_semanal_manual():
    from src.pilates.cron import _tarea_semanal
    await _tarea_semanal()
    return {"status": "ok", "tarea": "semanal"}


# ============================================================
# B2.9 VOZ REACTIVO — Sub-circuito de señales AF5
# ============================================================

@router.post("/voz/propagar-diagnostico")
async def voz_propagar_diagnostico():
    from src.pilates.voz_reactivo import propagar_diagnostico_a_voz
    return await propagar_diagnostico_a_voz()

@router.post("/voz/cross-af")
async def voz_cross_af():
    from src.pilates.voz_reactivo import emitir_señales_cross_af
    return await emitir_señales_cross_af()


# ============================================================
# IDENTIDAD + CONTENIDO (F7)
# ============================================================

@router.get("/identidad")
async def get_identidad():
    """Lee la pizarra identidad del tenant."""
    from src.pilates.filtro_identidad import leer_identidad
    return await leer_identidad()


@router.patch("/identidad")
async def actualizar_identidad(request: Request):
    """Actualiza campos de la pizarra identidad (CR1 Jesús)."""
    body = await request.json()
    from src.db.client import get_pool
    pool = await get_pool()
    campos_permitidos = {"esencia", "narrativa", "valores", "anti_identidad",
                         "depuraciones_deliberadas", "tono", "angulo_diferencial"}
    sets = []
    params = ["authentic_pilates"]
    for campo in sorted(campos_permitidos):
        if campo in body:
            params.append(body[campo])
            sets.append(f'"{campo}" = ${len(params)}')
    if not sets:
        raise HTTPException(400, "Sin campos válidos")
    sets.append("updated_at = now()")
    query = f"UPDATE om_pizarra_identidad SET {', '.join(sets)} WHERE tenant_id = $1"
    async with pool.acquire() as conn:
        await conn.execute(query, *params)
    return {"status": "ok"}


@router.get("/contenido")
async def get_contenido(ciclo: str = None, estado: str = None, limit: int = 20):
    """Lista contenido generado."""
    from src.db.client import get_pool
    pool = await get_pool()
    query = "SELECT * FROM om_contenido WHERE tenant_id = 'authentic_pilates'"
    params = []
    if ciclo:
        params.append(ciclo)
        query += f" AND ciclo = ${len(params)}"
    if estado:
        params.append(estado)
        query += f" AND estado = ${len(params)}"
    query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
    params.append(limit)
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]


@router.post("/contenido/{contenido_id}/aprobar")
async def aprobar(contenido_id):
    """CR1: Jesús aprueba contenido para publicación."""
    from uuid import UUID
    from src.pilates.contenido import aprobar_contenido
    return await aprobar_contenido(UUID(contenido_id))


@router.post("/contenido/{contenido_id}/programar")
async def programar(contenido_id, request: Request):
    """Programa contenido aprobado."""
    from uuid import UUID
    from src.pilates.contenido import programar_publicacion
    body = await request.json()
    return await programar_publicacion(UUID(contenido_id))


@router.post("/contenido/filtrar")
async def filtrar_contenido_manual(request: Request):
    """Filtra texto contra identidad (para preview)."""
    body = await request.json()
    from src.pilates.filtro_identidad import filtrar_por_identidad
    return await filtrar_por_identidad(body.get("texto", ""), body.get("canal", "instagram"))


@router.get("/competencia")
async def get_competencia():
    """Lista competidores monitorizados."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM om_competencia WHERE tenant_id = 'authentic_pilates'")
    return [dict(r) for r in rows]
