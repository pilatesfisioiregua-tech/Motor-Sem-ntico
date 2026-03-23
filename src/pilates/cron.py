"""Cron del Exocortex — Tareas programadas.

Ejecuta tareas periódicas sin dependencias externas.
Se inicia en el lifespan de FastAPI como background task.

Tareas:
- Diaria (06:00 Madrid): escuchar señales
- Semanal (lunes 07:00): calcular estrategia + ciclo completo
"""
from __future__ import annotations

import asyncio
import os
import structlog
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

log = structlog.get_logger()

MADRID_TZ = ZoneInfo("Europe/Madrid")


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (con DST correcto)."""
    return datetime.now(MADRID_TZ)


async def _ya_ejecutado(tarea: str, periodo: str) -> bool:
    """Consulta om_cron_state para saber si la tarea ya se ejecutó en este periodo.

    periodo: 'dia' (hoy), 'semana' (esta semana ISO), 'mes' (este mes)
    """
    from src.db.client import get_pool
    pool = await get_pool()
    ahora = _hora_madrid()

    if periodo == "dia":
        inicio = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "semana":
        inicio = ahora - timedelta(days=ahora.weekday())
        inicio = inicio.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "mes":
        inicio = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        return False

    async with pool.acquire() as conn:
        row = await conn.fetchval("""
            SELECT 1 FROM om_cron_state
            WHERE tenant_id = 'authentic_pilates' AND tarea = $1
                AND ultima_ejecucion >= $2
        """, tarea, inicio)
    return row is not None


async def _marcar_ejecutado(tarea: str, resultado: str = "ok"):
    """Marca tarea como ejecutada en om_cron_state."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_cron_state (tenant_id, tarea, ultima_ejecucion, resultado)
            VALUES ('authentic_pilates', $1, now(), $2)
            ON CONFLICT (tenant_id, tarea)
            DO UPDATE SET ultima_ejecucion = now(), resultado = $2
        """, tarea, resultado)


async def _tarea_diaria():
    """Tarea diaria: escuchar señales + snapshot propiocepción."""
    try:
        from src.pilates.voz_ciclos import escuchar
        result = await escuchar()
        log.info("cron_diaria_ok", senales=result.get("senales_creadas", 0))
    except Exception as e:
        log.error("cron_diaria_error", error=str(e))

    # Collectors: pull métricas de canales
    try:
        from src.pilates.collectors import collect_all
        coll = await collect_all()
        log.info("cron_diaria_collectors_ok", activos=coll.get("collectors_activos", 0))
    except Exception as e:
        log.error("cron_diaria_collectors_error", error=str(e))

    # Propiocepción: snapshot diario
    try:
        from src.pilates.propiocepcion import snapshot
        snap = await snapshot("diario")
        log.info("cron_diaria_propiocepcion_ok",
            señales=snap["bus"]["emitidas"],
            silenciosos=len(snap["bus"]["agentes_silenciosos"]))
    except Exception as e:
        log.error("cron_diaria_propiocepcion_error", error=str(e))

    # Cobros recurrentes Redsys (día del mes correcto)
    try:
        from src.pilates.redsys_pagos import cron_cobros_recurrentes, is_configured
        if is_configured():
            cobros = await cron_cobros_recurrentes()
            log.info("cron_diaria_cobros_ok", cobrados=cobros.get("cobrados", 0))
        else:
            log.debug("cron_diaria_cobros_skip", razon="redsys_no_configurado")
    except Exception as e:
        log.error("cron_diaria_cobros_error", error=str(e))

    # Confirmaciones pre-sesión (24h antes)
    try:
        from src.pilates.whatsapp import enviar_confirmaciones_manana, is_configured as wa_configured
        if wa_configured():
            conf = await enviar_confirmaciones_manana()
            log.info("cron_diaria_confirmaciones_ok", enviados=conf.get("enviados", 0))
    except Exception as e:
        log.error("cron_diaria_confirmaciones_error", error=str(e))

    # Cumpleaños automáticos
    try:
        from src.pilates.automatismos import felicitar_cumpleanos
        cumple = await felicitar_cumpleanos()
        log.info("cron_diaria_cumpleanos_ok", enviados=cumple.get("felicitaciones_enviadas", 0))
    except Exception as e:
        log.error("cron_diaria_cumpleanos_error", error=str(e))


async def _tarea_semanal():
    """Tarea semanal (lunes): ciclo completo + estrategia + ACD + búsqueda."""
    try:
        # 1. Ciclo completo (escuchar + priorizar + IRC + ISP)
        from src.pilates.voz_ciclos import ejecutar_ciclo_completo
        ciclo = await ejecutar_ciclo_completo()
        log.info("cron_semanal_ciclo_ok", isp=ciclo.get("ciclos", {}).get("aprender", {}).get("isp_global"))

        # 2. Calcular nueva estrategia semanal
        from src.pilates.voz_estrategia import calcular_estrategia
        est = await calcular_estrategia()
        log.info("cron_semanal_estrategia_ok",
                 foco=est.get("estrategia", {}).get("foco_principal"),
                 items=est.get("calendario_items"))

        # 3. Diagnóstico ACD autónomo
        from src.pilates.diagnosticador import diagnosticar_tenant
        diag = await diagnosticar_tenant()
        log.info("cron_semanal_acd_ok", estado=diag.get("estado"), cambio=diag.get("cambio_vs_anterior"))

        # 4. Búsqueda dirigida por gaps (frecuencia según urgencia)
        from src.pilates.buscador import buscar_por_gaps, decidir_frecuencia_busqueda
        if await decidir_frecuencia_busqueda():
            busq = await buscar_por_gaps()
            log.info("cron_semanal_busqueda_ok",
                     resultados=busq.get("resultados_utiles"),
                     tipos=busq.get("tipos_buscador_usados"))
        else:
            log.info("cron_semanal_busqueda_skip", razon="frecuencia_baja")

        # 4b-pre. Evaluador: ¿la prescripción anterior funcionó?
        try:
            from src.pilates.evaluador_organismo import evaluar_semana
            evaluacion = await evaluar_semana()
            log.info("cron_semanal_evaluador_ok",
                     funciono=evaluacion.get("interpretacion", {}).get("evaluacion_global", {}).get("prescripcion_funciono"))
        except Exception as e:
            log.error("cron_semanal_evaluador_error", error=str(e))

        # 4b. G4 completa: Enjambre → Compositor → Estratega → Recompilador
        try:
            from src.pilates.recompilador import ejecutar_g4_con_recompilacion
            g4 = await ejecutar_g4_con_recompilacion()
            log.info("cron_semanal_g4_ok",
                     perfil=g4.get("perfil_detectado"),
                     nivel=g4.get("nivel_alcanzado"),
                     recompilados=g4.get("recompilacion", {}).get("configs_aplicadas", 0),
                     tiempo=g4.get("tiempo_total_s"))
        except Exception as e:
            log.error("cron_semanal_g4_error", error=str(e))

        # 4c. AF5 propaga diagnóstico a voz + señales cross-AF
        from src.pilates.voz_reactivo import propagar_diagnostico_a_voz, emitir_señales_cross_af
        await propagar_diagnostico_a_voz()
        await emitir_señales_cross_af()
        log.info("cron_semanal_voz_reactivo_ok")

        # 5. AF1 Conservación — detectar clientes en riesgo
        from src.pilates.af1_conservacion import ejecutar_af1
        af1 = await ejecutar_af1()
        log.info("cron_semanal_af1_ok", riesgos=af1.get("total_riesgos"), alertas=af1.get("alertas_emitidas"))

        # 6. AF3 Depuración — detectar ineficiencias + VETO
        from src.pilates.af3_depuracion import ejecutar_af3
        af3 = await ejecutar_af3()
        log.info("cron_semanal_af3_ok", detecciones=af3.get("total_detecciones"), vetos=af3.get("vetos_emitidos"))

        # 6b. AF5 Identidad — detectar gaps de identidad + coherencia
        from src.pilates.af5_identidad import ejecutar_af5
        af5 = await ejecutar_af5()
        log.info("cron_semanal_af5_ok", gaps=af5.get("gaps_identidad"), adn=af5.get("adn_count"))

        # 7. AF2 + AF4 + AF6 + AF7 — agentes funcionales restantes
        from src.pilates.af_restantes import ejecutar_af_restantes
        af_rest = await ejecutar_af_restantes()
        log.info("cron_semanal_af_restantes_ok", alertas=af_rest.get("total_alertas", 0))

        # 8. Propiocepción: snapshot semanal
        from src.pilates.propiocepcion import snapshot
        snap = await snapshot("semanal")
        log.info("cron_semanal_propiocepcion_ok",
            señales=snap["bus"]["emitidas"],
            drift=snap.get("alerta_drift") is not None)

        # 9. Ejecutor + Convergencia + Gestor — cierre del circuito
        from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
        circ = await ejecutar_circuito_completo()
        log.info("cron_semanal_circuito_ok",
            acciones=circ["ejecutor"]["acciones_emitidas"],
            convergencias=circ["convergencia"]["total"],
            archivadas=circ["gestor"]["archivadas_eliminadas"])

        # 10. Briefing semanal por WA a Jesús
        try:
            from src.pilates.briefing import generar_briefing
            from src.pilates.whatsapp import enviar_texto, is_configured as wa_configured
            briefing = await generar_briefing()
            telefono_jesus = os.getenv("JESUS_TELEFONO", "")
            if wa_configured() and telefono_jesus and briefing.get("texto_wa"):
                await enviar_texto(telefono_jesus, briefing["texto_wa"])
                log.info("cron_semanal_briefing_wa_ok")
        except Exception as e:
            log.error("cron_semanal_briefing_wa_error", error=str(e))

        # 11. Snapshot de todas las pizarras (P65 — "git del organismo")
        try:
            from src.pilates.pizarras import snapshot_todas
            semana_iso = _hora_madrid().isocalendar()
            ciclo = f"W{semana_iso[1]:02d}-{semana_iso[0]}"
            snap = await snapshot_todas("authentic_pilates", ciclo)
            log.info("cron_semanal_snapshot_ok", ciclo=ciclo, pizarras=len(snap))
        except Exception as e:
            log.error("cron_semanal_snapshot_error", error=str(e))

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))


async def _tarea_mensual():
    """Tarea mensual (día 1): autofagia — el sistema se poda a sí mismo."""
    try:
        from src.pilates.autofago import ejecutar_autofagia
        result = await ejecutar_autofagia()
        log.info("cron_mensual_autofagia_ok",
            muertos=result["codigo_muerto"]["funciones_huerfanas"],
            sospechosos=len(result["archivos_sospechosos"]),
            caducados=len(result["datos_caducados"]),
            propuestas=result["propuestas_registradas"])
    except Exception as e:
        log.error("cron_mensual_error", error=str(e))

    # Reactor v4: detectar patrones en datos reales → pizarra evolución
    try:
        import json as _json
        from src.reactor.v4_telemetria import detectar_patrones
        informe = await detectar_patrones()
        if informe and hasattr(informe, 'to_dict'):
            datos = informe.to_dict()
            if datos.get("patrones"):
                from src.db.client import get_pool as _gp
                pool = await _gp()
                async with pool.acquire() as conn:
                    for patron in datos["patrones"][:10]:
                        await conn.execute("""
                            INSERT INTO om_pizarra_evolucion
                                (tenant_id, tipo, descripcion, datos, confianza)
                            VALUES ('authentic_pilates', 'reactor_v4', $1, $2::jsonb, $3)
                        """, patron.get("descripcion", "")[:500],
                            _json.dumps(patron, default=str),
                            patron.get("confianza", 0.5))
        log.info("cron_mensual_reactor_v4_ok")
    except Exception as e:
        log.error("cron_mensual_reactor_v4_error", error=str(e))

    # Cristalizador mensual (después del autófago)
    try:
        from src.pilates.generativa import cristalizar_patrones
        crist = await cristalizar_patrones()
        log.info("cron_mensual_cristalizador_ok",
                 patrones=len(crist.get("patrones_detectados", [])))
    except Exception as e:
        log.error("cron_mensual_cristalizador_error", error=str(e))

    # Meta-Cognitivo: evalúa el sistema cognitivo
    try:
        from src.pilates.metacognitivo import ejecutar_metacognitivo
        metacog = await ejecutar_metacognitivo()
        log.info("cron_mensual_metacog_ok",
                 instrucciones=len(metacog.get("resultado", {}).get("instrucciones_ingeniero", [])))
    except Exception as e:
        log.error("cron_mensual_metacog_error", error=str(e))

    # Ingeniero: procesa instrucciones del Meta-Cognitivo
    try:
        from src.pilates.ingeniero import procesar_instrucciones_pendientes
        ing = await procesar_instrucciones_pendientes()
        log.info("cron_mensual_ingeniero_ok",
                 safe=ing.get("safe_ejecutadas", 0),
                 cr1=ing.get("pendientes_cr1", 0))
    except Exception as e:
        log.error("cron_mensual_ingeniero_error", error=str(e))


async def _escuchar_senales_urgentes():
    """Listener permanente de señales urgentes via LISTEN/NOTIFY (P65).

    Cuando om_senales_agentes recibe una señal con prioridad <= 2,
    el trigger notify_senal_urgente() dispara un NOTIFY que llega aquí.
    """
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        conn = await pool.acquire()

        def callback(conn_ref, pid, channel, payload):
            import json as _json
            try:
                data = _json.loads(payload)
                log.warning("senal_urgente_recibida",
                           tipo=data.get("tipo"), origen=data.get("origen"),
                           prioridad=data.get("prioridad"))
            except Exception as e:
                log.error("senal_urgente_parse_error", error=str(e))

        await conn.add_listener("senal_urgente", callback)
        log.info("listen_notify_activo", canal="senal_urgente")

        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        log.error("listen_notify_error", error=str(e))


async def cron_loop():
    """Loop principal del cron. Se ejecuta como background task.

    Revisa cada 15 minutos si hay tareas pendientes.
    Usa om_cron_state en DB para no repetir tras restart/deploy.
    """
    log.info("cron_iniciado")

    # Listener de señales urgentes (LISTEN/NOTIFY, P65)
    asyncio.create_task(_escuchar_senales_urgentes())

    while True:
        try:
            ahora = _hora_madrid()
            hoy = ahora.date()
            hora = ahora.time()

            # Tarea diaria: después de las 06:00, una vez al día
            if hora >= time(6, 0) and not await _ya_ejecutado("diaria", "dia"):
                log.info("cron_ejecutando_diaria", hora=str(hora))
                await _tarea_diaria()
                await _marcar_ejecutado("diaria")

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                if not await _ya_ejecutado("semanal", "semana"):
                    log.info("cron_ejecutando_semanal", semana=hoy.isocalendar()[1])
                    await _tarea_semanal()
                    await _marcar_ejecutado("semanal")

            # Tarea mensual: día 1 después de las 08:00
            if hoy.day == 1 and hora >= time(8, 0):
                if not await _ya_ejecutado("mensual", "mes"):
                    log.info("cron_ejecutando_mensual", mes=f"{hoy.year}-{hoy.month:02d}")
                    await _tarea_mensual()
                    await _marcar_ejecutado("mensual")

        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Vigía + Mecánico: cada iteración (cada 15 min) — sin state, siempre corre
        try:
            from src.pilates.vigia import vigilar
            vigia_result = await vigilar()
            if vigia_result.get("alertas_emitidas", 0) > 0:
                from src.pilates.mecanico import procesar_alertas
                mec_result = await procesar_alertas()
                log.info("cron_mecanico_ok",
                    fixes=mec_result.get("fixes_fontaneria", 0),
                    arq=mec_result.get("arquitecturales", 0))
        except Exception as e:
            log.error("cron_vigia_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
