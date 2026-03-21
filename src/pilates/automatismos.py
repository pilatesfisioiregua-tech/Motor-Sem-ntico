"""Automatismos Exocortex Pilates.

Funciones async que implementan la lógica automática del estudio.
Invocables desde endpoints cron o desde triggers inline.

Fuente: Exocortex v2.1 S5, S13, S16.
"""
from __future__ import annotations

import structlog
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# 1. GENERAR SESIONES SEMANA (cron lunes 00:00)
# ============================================================

async def generar_sesiones_semana(fecha_inicio: Optional[date] = None) -> dict:
    """Genera sesiones de la semana para todos los grupos activos.

    Para cada grupo: lee dias_semana JSONB, crea om_sesiones + om_asistencias
    para cada día de la semana. Idempotente: no crea si ya existe sesión
    para ese grupo+fecha.

    Args:
        fecha_inicio: Lunes de la semana. Default: próximo lunes.

    Returns:
        {"sesiones_creadas": N, "asistencias_creadas": N}
    """
    if fecha_inicio is None:
        hoy = date.today()
        # Próximo lunes (o hoy si es lunes)
        dias_hasta_lunes = (7 - hoy.weekday()) % 7
        if dias_hasta_lunes == 0 and datetime.now().hour >= 1:
            dias_hasta_lunes = 7  # Si ya pasó el cron del lunes, siguiente semana
        fecha_inicio = hoy + timedelta(days=dias_hasta_lunes)

    pool = await _get_pool()
    sesiones_creadas = 0
    asistencias_creadas = 0

    async with pool.acquire() as conn:
        grupos = await conn.fetch("""
            SELECT id, dias_semana, capacidad_max FROM om_grupos
            WHERE tenant_id = $1 AND estado IN ('activo', 'migrando')
        """, TENANT)

        for grupo in grupos:
            dias = grupo["dias_semana"]  # JSONB: [{"dia":1,"hi":"17:15","hf":"18:15"}, ...]
            if isinstance(dias, str):
                import json
                dias = json.loads(dias)

            for slot in dias:
                dia_semana = slot["dia"]  # 1=lunes..5=viernes
                # Calcular fecha real
                fecha_sesion = fecha_inicio + timedelta(days=dia_semana - 1)

                # Verificar si ya existe
                exists = await conn.fetchval("""
                    SELECT 1 FROM om_sesiones
                    WHERE grupo_id = $1 AND fecha = $2 AND tenant_id = $3
                """, grupo["id"], fecha_sesion, TENANT)
                if exists:
                    continue

                # Crear sesión
                from datetime import time as dt_time
                hi = dt_time.fromisoformat(slot["hi"])
                hf = dt_time.fromisoformat(slot["hf"])

                sesion_row = await conn.fetchrow("""
                    INSERT INTO om_sesiones (tenant_id, tipo, grupo_id, instructor, fecha, hora_inicio, hora_fin)
                    VALUES ($1, 'grupo', $2, 'Jesus', $3, $4, $5) RETURNING id
                """, TENANT, grupo["id"], fecha_sesion, hi, hf)
                sesion_id = sesion_row["id"]
                sesiones_creadas += 1

                # Crear asistencias para miembros activos
                miembros = await conn.fetch("""
                    SELECT co.id as contrato_id, co.cliente_id
                    FROM om_contratos co
                    WHERE co.grupo_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
                """, grupo["id"], TENANT)

                for m in miembros:
                    await conn.execute("""
                        INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id, contrato_id, estado)
                        VALUES ($1, $2, $3, $4, 'confirmada')
                    """, TENANT, sesion_id, m["cliente_id"], m["contrato_id"])
                    asistencias_creadas += 1

    log.info("sesiones_semana_generadas",
             semana=str(fecha_inicio), sesiones=sesiones_creadas, asistencias=asistencias_creadas)
    return {"sesiones_creadas": sesiones_creadas, "asistencias_creadas": asistencias_creadas,
            "semana_inicio": str(fecha_inicio)}


# ============================================================
# 2. CALCULAR DÍAS ESPERADOS MES (cron día 1)
# ============================================================

async def calcular_dias_esperados(mes: Optional[date] = None) -> dict:
    """Calcula días esperados por contrato grupo para el mes.

    Para cada contrato grupo activo: cuenta cuántos días del grupo
    caen en el mes. Crea/actualiza om_dias_esperados.

    Idempotente por UNIQUE(contrato_id, mes).
    """
    import calendar
    mes = mes or date.today().replace(day=1)
    ultimo_dia = mes.replace(day=calendar.monthrange(mes.year, mes.month)[1])

    pool = await _get_pool()
    creados = 0

    async with pool.acquire() as conn:
        contratos = await conn.fetch("""
            SELECT co.id, co.cliente_id, co.grupo_id, g.dias_semana
            FROM om_contratos co
            JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.tenant_id = $1 AND co.tipo = 'grupo' AND co.estado = 'activo'
        """, TENANT)

        for co in contratos:
            # Ya existe?
            exists = await conn.fetchval("""
                SELECT 1 FROM om_dias_esperados WHERE contrato_id = $1 AND mes = $2
            """, co["id"], mes)
            if exists:
                continue

            # Contar días del grupo en el mes
            dias = co["dias_semana"]
            if isinstance(dias, str):
                import json
                dias = json.loads(dias)

            dias_semana_grupo = [slot["dia"] for slot in dias]  # [1,3] para L-X
            total_dias = 0
            fecha = mes
            while fecha <= ultimo_dia:
                # weekday(): 0=lunes, 1=martes... → nuestro formato: 1=lunes, 2=martes...
                if (fecha.weekday() + 1) in dias_semana_grupo:
                    total_dias += 1
                fecha += timedelta(days=1)

            await conn.execute("""
                INSERT INTO om_dias_esperados (tenant_id, contrato_id, cliente_id, grupo_id, mes, dias_esperados)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (contrato_id, mes) DO NOTHING
            """, TENANT, co["id"], co["cliente_id"], co["grupo_id"], mes, total_dias)
            creados += 1

    log.info("dias_esperados_calculados", mes=str(mes), contratos=creados)
    return {"mes": str(mes), "contratos_calculados": creados}


# ============================================================
# 3. ACTUALIZAR ASISTENCIA EN DIAS_ESPERADOS (post-marcar)
# ============================================================

async def actualizar_dias_esperados_asistencia(sesion_id: UUID) -> None:
    """Actualiza contadores de om_dias_esperados tras marcar asistencia.

    Se ejecuta como side-effect de marcar-grupo o completar sesión.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesion = await conn.fetchrow("SELECT * FROM om_sesiones WHERE id = $1", sesion_id)
        if not sesion or not sesion["grupo_id"]:
            return

        mes = sesion["fecha"].replace(day=1)

        asistencias = await conn.fetch("""
            SELECT cliente_id, estado FROM om_asistencias WHERE sesion_id = $1
        """, sesion_id)

        for a in asistencias:
            # Recalcular contadores para este cliente/mes
            stats = await conn.fetchrow("""
                SELECT
                    count(*) FILTER (WHERE a.estado = 'asistio') as asistidos,
                    count(*) FILTER (WHERE a.estado = 'no_vino') as faltas,
                    count(*) FILTER (WHERE a.estado = 'cancelada') as cancelados,
                    count(*) FILTER (WHERE a.es_recuperacion = true AND a.estado = 'asistio') as recuperados
                FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = $1 AND s.grupo_id = $2
                    AND s.fecha >= $3 AND s.fecha < ($3 + interval '1 month')
            """, a["cliente_id"], sesion["grupo_id"], mes)

            if stats:
                await conn.execute("""
                    UPDATE om_dias_esperados
                    SET dias_asistidos = $1, dias_falta = $2,
                        dias_cancelados = $3, dias_recuperados = $4
                    WHERE contrato_id IN (
                        SELECT id FROM om_contratos
                        WHERE cliente_id = $5 AND grupo_id = $6 AND estado = 'activo'
                    ) AND mes = $7
                """, stats["asistidos"], stats["faltas"],
                    stats["cancelados"], stats["recuperados"],
                    a["cliente_id"], sesion["grupo_id"], mes)


# ============================================================
# 4. DETECTAR ALERTAS RETENCIÓN (cron semanal)
# ============================================================

async def detectar_alertas_retencion() -> dict:
    """Detecta patrones que predicen baja:
    - Asistencia < 50% últimas 4 semanas
    - 2+ faltas consecutivas
    - Deuda > 30 días
    - Recuperaciones > faltas (abuso)

    Returns: lista de alertas con cliente_id, tipo, datos.
    """
    pool = await _get_pool()
    alertas = []
    hace_4_semanas = date.today() - timedelta(weeks=4)

    async with pool.acquire() as conn:
        # Asistencia baja últimas 4 semanas
        rows = await conn.fetch("""
            SELECT a.cliente_id, c.nombre, c.apellidos,
                   count(*) as total,
                   count(*) FILTER (WHERE a.estado = 'asistio') as asistidos,
                   count(*) FILTER (WHERE a.estado = 'no_vino') as faltas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            JOIN om_clientes c ON c.id = a.cliente_id
            WHERE a.tenant_id = $1 AND s.fecha >= $2
            GROUP BY a.cliente_id, c.nombre, c.apellidos
            HAVING count(*) >= 4
                AND count(*) FILTER (WHERE a.estado = 'asistio')::float / count(*) < 0.5
        """, TENANT, hace_4_semanas)

        for r in rows:
            pct = round(r["asistidos"] / max(r["total"], 1) * 100, 0)
            alertas.append({
                "cliente_id": str(r["cliente_id"]),
                "nombre": f"{r['nombre']} {r['apellidos']}",
                "tipo": "asistencia_baja",
                "detalle": f"Asistencia {pct}% últimas 4 semanas ({r['asistidos']}/{r['total']})",
                "severidad": "alta" if pct < 25 else "media",
            })

        # Deuda > 30 días
        rows = await conn.fetch("""
            SELECT c.cliente_id, cl.nombre, cl.apellidos,
                   SUM(c.total) as deuda_total,
                   MIN(c.fecha_cargo) as cargo_mas_antiguo
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE c.tenant_id = $1 AND c.estado = 'pendiente'
                AND c.fecha_cargo < CURRENT_DATE - interval '30 days'
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
        """, TENANT)

        for r in rows:
            dias = (date.today() - r["cargo_mas_antiguo"]).days
            alertas.append({
                "cliente_id": str(r["cliente_id"]),
                "nombre": f"{r['nombre']} {r['apellidos']}",
                "tipo": "deuda_antigua",
                "detalle": f"Deuda {float(r['deuda_total']):.2f} EUR, {dias} días sin pagar",
                "severidad": "alta" if dias > 60 else "media",
            })

        # Abuso recuperaciones
        rows = await conn.fetch("""
            SELECT de.cliente_id, cl.nombre, cl.apellidos,
                   de.dias_falta, de.dias_recuperados
            FROM om_dias_esperados de
            JOIN om_clientes cl ON cl.id = de.cliente_id
            WHERE de.tenant_id = $1 AND de.mes >= $2
                AND de.recuperaciones_excedidas = true
        """, TENANT, date.today().replace(day=1) - timedelta(days=31))

        for r in rows:
            alertas.append({
                "cliente_id": str(r["cliente_id"]),
                "nombre": f"{r['nombre']} {r['apellidos']}",
                "tipo": "abuso_recuperaciones",
                "detalle": f"Recuperaciones ({r['dias_recuperados']}) > Faltas ({r['dias_falta']})",
                "severidad": "baja",
            })

    log.info("alertas_retencion", total=len(alertas))
    return {"alertas": alertas, "total": len(alertas)}


# ============================================================
# 5. CONCILIACIÓN BANCARIA SIMPLE (bajo demanda)
# ============================================================

async def conciliar_bizum_entrante(telefono: str, monto: float,
                                    referencia: Optional[str] = None) -> dict:
    """Recibe un Bizum entrante: busca cliente por teléfono, crea pago, concilia FIFO.

    Modo Estudio: Jesús pulsa B → typeahead cliente → monto → Enter.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar cliente por teléfono
        cliente = await conn.fetchrow("""
            SELECT c.id FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            WHERE c.telefono = $2
        """, TENANT, telefono)

        if not cliente:
            return {"status": "error", "detail": f"No hay cliente con teléfono {telefono}"}

        cliente_id = cliente["id"]

        # Crear pago
        pago_row = await conn.fetchrow("""
            INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto, referencia_externa, notas)
            VALUES ($1, $2, 'bizum', $3, $4, 'Bizum entrante')
            RETURNING id
        """, TENANT, cliente_id, monto, referencia)
        pago_id = pago_row["id"]

        # FIFO
        cargos = await conn.fetch("""
            SELECT id, total FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
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
                INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado) VALUES ($1, $2, $3)
            """, pago_id, cargo["id"], aplicado)
            if aplicado >= cargo_total:
                await conn.execute("""
                    UPDATE om_cargos SET estado = 'cobrado', fecha_cobro = CURRENT_DATE WHERE id = $1
                """, cargo["id"])
                conciliados += 1
            restante -= aplicado

        # Actualizar método habitual
        await conn.execute("""
            UPDATE om_clientes SET metodo_pago_habitual = 'bizum',
                metodo_pago_confianza = LEAST(metodo_pago_confianza + 0.1, 1.0), updated_at = now()
            WHERE id = $1
        """, cliente_id)

    return {"status": "ok", "pago_id": str(pago_id), "cargos_conciliados": conciliados,
            "restante": round(restante, 2)}


# ============================================================
# 6. CRON MAESTRO (endpoint único para todos los crons)
# ============================================================

async def ejecutar_cron(tipo: str) -> dict:
    """Ejecuta un cron batch. Tipos:
    - 'inicio_semana': generar sesiones + alertas retención
    - 'inicio_mes': suscripciones + días esperados
    - 'diario': (reservado para futuras automatizaciones)
    """
    resultados = {}

    if tipo == "inicio_semana":
        resultados["sesiones"] = await generar_sesiones_semana()
        resultados["alertas"] = await detectar_alertas_retencion()
        # Generar propuestas Voz
        from src.pilates.voz import generar_propuestas
        props = await generar_propuestas()
        resultados["voz_propuestas"] = {"generadas": len(props)}
        # Recalcular engagement
        from src.pilates.engagement import recalcular_engagement_todos
        resultados["engagement"] = await recalcular_engagement_todos()
        # Generar y almacenar briefing
        from src.pilates.briefing import generar_briefing
        resultados["briefing"] = await generar_briefing()

    elif tipo == "inicio_mes":
        pool = await _get_pool()
        mes = date.today().replace(day=1)

        # Suscripciones
        creados = 0
        async with pool.acquire() as conn:
            contratos = await conn.fetch("""
                SELECT co.id, co.cliente_id, COALESCE(co.precio_mensual, g.precio_mensual) as precio
                FROM om_contratos co JOIN om_grupos g ON g.id = co.grupo_id
                WHERE co.tenant_id = $1 AND co.tipo = 'grupo' AND co.estado = 'activo'
            """, TENANT)
            for co in contratos:
                exists = await conn.fetchval("""
                    SELECT 1 FROM om_cargos WHERE contrato_id = $1 AND tipo = 'suscripcion_grupo' AND periodo_mes = $2
                """, co["id"], mes)
                if not exists:
                    await conn.execute("""
                        INSERT INTO om_cargos (tenant_id, cliente_id, contrato_id, tipo, descripcion, base_imponible, periodo_mes)
                        VALUES ($1, $2, $3, 'suscripcion_grupo', $4, $5, $6)
                    """, TENANT, co["cliente_id"], co["id"],
                        f"Suscripción grupo {mes.strftime('%B %Y')}", float(co["precio"]), mes)
                    creados += 1
        resultados["suscripciones"] = {"cargos_creados": creados}
        resultados["dias_esperados"] = await calcular_dias_esperados(mes)

    elif tipo == "diario":
        resultados["cumpleanos"] = await felicitar_cumpleanos()
        from src.pilates.stripe_pagos import cron_cobros_recurrentes
        resultados["cobros"] = await cron_cobros_recurrentes()

    else:
        return {"status": "error", "detail": f"Tipo cron desconocido: {tipo}"}

    log.info("cron_ejecutado", tipo=tipo, resultados=list(resultados.keys()))
    return {"status": "ok", "tipo": tipo, **resultados}


# ============================================================
# 7. CUMPLEAÑOS AUTOMÁTICOS (cron diario)
# ============================================================

async def felicitar_cumpleanos():
    """Cron diario: detecta cumpleaños de hoy y envía felicitación por WA."""
    import json
    pool = await _get_pool()
    hoy = date.today()

    async with pool.acquire() as conn:
        cumples = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono, c.fecha_nacimiento,
                   EXTRACT(YEAR FROM age(c.fecha_nacimiento)) as edad
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id
            WHERE ct.tenant_id = $1 AND ct.estado = 'activo'
                AND c.fecha_nacimiento IS NOT NULL
                AND EXTRACT(MONTH FROM c.fecha_nacimiento) = $2
                AND EXTRACT(DAY FROM c.fecha_nacimiento) = $3
        """, TENANT, hoy.month, hoy.day)

        enviados = 0
        for c in cumples:
            ya_felicitado = await conn.fetchval("""
                SELECT 1 FROM om_cliente_eventos
                WHERE cliente_id=$1 AND tipo='cumpleanos_felicitado'
                    AND created_at >= date_trunc('year', CURRENT_DATE)
            """, c["id"])
            if ya_felicitado:
                continue

            import secrets
            token_tarjeta = secrets.token_urlsafe(16)
            base_url = "https://motor-semantico-omni.fly.dev"

            mensaje = (
                f"Feliz cumpleaños, {c['nombre']}! 🎂\n\n"
                f"Hoy es tu día y desde Authentic Pilates queríamos "
                f"mandarte un abrazo bien grande.\n\n"
                f"Te hemos preparado una cosita:\n"
                f"{base_url}/tarjeta/{token_tarjeta}\n\n"
                f"Pásalo genial! 🎉"
            )

            from src.pilates.whatsapp import enviar_texto, is_configured
            if is_configured() and c["telefono"]:
                await enviar_texto(c["telefono"], mensaje, c["id"])
                enviados += 1

                await conn.execute("""
                    INSERT INTO om_cliente_eventos
                        (tenant_id, cliente_id, tipo, metadata)
                    VALUES ($1, $2, 'cumpleanos_felicitado', $3::jsonb)
                """, TENANT, c["id"], json.dumps({
                    "token_tarjeta": token_tarjeta,
                    "nombre": c["nombre"],
                    "edad": int(c["edad"]) if c["edad"] else None,
                    "year": hoy.year
                }))

            from src.pilates.feed import publicar
            await publicar("cumpleanos", "🎂",
                f"Hoy cumple años {c['nombre']}!",
                f"Felicitación enviada por WA", c["id"], "success")

    log.info("cumpleanos_check", hoy=str(hoy), enviados=enviados)
    return {"cumpleanos_hoy": len(cumples), "felicitaciones_enviadas": enviados}


# ============================================================
# 8. CHECK LISTA DE ESPERA (tras cada cancelación)
# ============================================================

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
