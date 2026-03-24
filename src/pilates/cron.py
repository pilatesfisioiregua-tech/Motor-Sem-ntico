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

# Advisory lock IDs (únicos por tarea, evita ejecución paralela en múltiples instancias)
LOCK_DIARIA = 100001
LOCK_SEMANAL = 100002
LOCK_MENSUAL = 100003


async def _try_advisory_lock(conn, lock_id: int) -> bool:
    """Intenta adquirir advisory lock de PostgreSQL. Non-blocking."""
    return await conn.fetchval("SELECT pg_try_advisory_lock($1)", lock_id)


async def _release_advisory_lock(conn, lock_id: int):
    """Libera advisory lock."""
    await conn.execute("SELECT pg_advisory_unlock($1)", lock_id)


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


async def _run_step(step_name: str, func, semana_id: str, timeout_s: int = 300):
    """Ejecuta un paso del cron con tracking individual.

    Si el paso ya se ejecutó esta semana, lo salta.
    Si falla, registra el error y continúa con el siguiente paso.
    """
    from src.db.client import get_pool
    pool = await get_pool()

    # Verificar si ya se ejecutó este paso esta semana
    async with pool.acquire() as conn:
        done = await conn.fetchval("""
            SELECT 1 FROM om_cron_steps
            WHERE tenant_id='authentic_pilates' AND semana=$1 AND step_name=$2 AND status='ok'
        """, semana_id, step_name)
        if done:
            return {"status": "skipped", "step": step_name}

    # Ejecutar con timeout individual
    try:
        result = await asyncio.wait_for(func(), timeout=timeout_s)
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_cron_steps (tenant_id, semana, step_name, status, resultado, executed_at)
                VALUES ('authentic_pilates', $1, $2, 'ok', $3, now())
                ON CONFLICT (tenant_id, semana, step_name)
                DO UPDATE SET status='ok', resultado=$3, executed_at=now()
            """, semana_id, step_name, str(result)[:500] if result else "ok")
        log.info(f"cron_step_ok", step=step_name)
        return {"status": "ok", "step": step_name, "result": result}
    except asyncio.TimeoutError:
        log.error(f"cron_step_timeout", step=step_name, timeout_s=timeout_s)
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_cron_steps (tenant_id, semana, step_name, status, resultado, executed_at)
                VALUES ('authentic_pilates', $1, $2, 'timeout', $3, now())
                ON CONFLICT (tenant_id, semana, step_name)
                DO UPDATE SET status='timeout', resultado=$3, executed_at=now()
            """, semana_id, step_name, f"timeout after {timeout_s}s")
        return {"status": "timeout", "step": step_name}
    except Exception as e:
        log.error(f"cron_step_error", step=step_name, error=str(e)[:200])
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_cron_steps (tenant_id, semana, step_name, status, resultado, executed_at)
                VALUES ('authentic_pilates', $1, $2, 'error', $3, now())
                ON CONFLICT (tenant_id, semana, step_name)
                DO UPDATE SET status='error', resultado=$3, executed_at=now()
            """, semana_id, step_name, str(e)[:500])
        return {"status": "error", "step": step_name, "error": str(e)[:200]}


async def _ensure_cron_steps_table():
    """Crea tabla om_cron_steps si no existe."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS om_cron_steps (
                tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
                semana TEXT NOT NULL,
                step_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                resultado TEXT,
                executed_at TIMESTAMPTZ DEFAULT now(),
                PRIMARY KEY (tenant_id, semana, step_name)
            )
        """)


async def _tarea_semanal():
    """Tarea semanal (lunes): ciclo completo + estrategia + ACD + búsqueda.

    Cada paso es independiente con tracking. Si falla uno, los demás siguen.
    Si se reinicia a mitad, los pasos completados no se repiten.
    """
    await _ensure_cron_steps_table()
    semana_iso = _hora_madrid().isocalendar()
    semana_id = f"W{semana_iso[1]:02d}-{semana_iso[0]}"

    # 0. Resetear presupuesto LLM
    try:
        from src.motor.pensar import resetear_presupuesto
        resetear_presupuesto()
        log.info("cron_semanal_presupuesto_reset")
    except Exception as e:
        log.error("cron_semanal_presupuesto_error", error=str(e))

    # 0b. Predicciones
    await _run_step("predicciones", lambda: _step_predicciones(), semana_id, 120)

    # Pasos 1-14: cada uno independiente con tracking
    steps = [
        ("ciclo_voz", _step_ciclo_voz, 300),
        ("estrategia", _step_estrategia, 180),
        ("diagnostico_acd", _step_diagnostico_acd, 300),
        ("busqueda_gaps", _step_busqueda, 180),
        ("evaluador", _step_evaluador, 120),
        ("g4_completa", _step_g4, 600),
        ("voz_reactivo", _step_voz_reactivo, 120),
        ("af1_conservacion", _step_af1, 120),
        ("af3_depuracion", _step_af3, 120),
        ("af5_identidad", _step_af5, 120),
        ("af_restantes", _step_af_rest, 120),
        ("propiocepcion", _step_propiocepcion, 60),
        ("mediador", _step_mediador, 180),
        ("circuito_completo", _step_circuito, 300),
        ("briefing_wa", _step_briefing, 120),
        ("snapshot_pizarras", _step_snapshot, 60),
        ("traductor", _step_traductor, 120),
        ("contenido", _step_contenido, 180),
        ("reputacion", _step_reputacion, 60),
    ]

    ok_count = 0
    error_count = 0
    for step_name, func, timeout in steps:
        result = await _run_step(step_name, func, semana_id, timeout)
        if result["status"] == "ok":
            ok_count += 1
        elif result["status"] == "skipped":
            ok_count += 1  # Ya ejecutado previamente
        else:
            error_count += 1

    log.info("cron_semanal_resumen", semana=semana_id, ok=ok_count,
             errores=error_count, total=len(steps))


# === STEP FUNCTIONS (cada una aislada) ===

async def _step_predicciones():
    from src.pilates.predictor import predecir_abandonos, predecir_demanda_semana
    from src.pilates.bus import emitir
    abandonos = await predecir_abandonos()
    demanda = await predecir_demanda_semana()
    if abandonos:
        for a in abandonos[:5]:
            await emitir("ALERTA", "PREDICTOR", {"subtipo": "abandono_predicho", **a}, destino="AF1", prioridad=2)
    return {"abandonos": len(abandonos), "demanda": demanda.get("sesiones_estimadas")}

async def _step_ciclo_voz():
    from src.pilates.voz_ciclos import ejecutar_ciclo_completo
    return await ejecutar_ciclo_completo()

async def _step_estrategia():
    from src.pilates.voz_estrategia import calcular_estrategia
    return await calcular_estrategia()

async def _step_diagnostico_acd():
    from src.pilates.diagnosticador import diagnosticar_tenant
    return await diagnosticar_tenant()

async def _step_busqueda():
    from src.pilates.buscador import buscar_por_gaps, decidir_frecuencia_busqueda
    if await decidir_frecuencia_busqueda():
        return await buscar_por_gaps()
    return {"skipped": "frecuencia_baja"}

async def _step_evaluador():
    from src.pilates.evaluador_organismo import evaluar_semana
    return await evaluar_semana()

async def _step_g4():
    from src.pilates.recompilador import ejecutar_g4_con_recompilacion
    return await ejecutar_g4_con_recompilacion()

async def _step_voz_reactivo():
    from src.pilates.voz_reactivo import propagar_diagnostico_a_voz, emitir_señales_cross_af
    await propagar_diagnostico_a_voz()
    await emitir_señales_cross_af()
    return {"ok": True}

async def _step_af1():
    from src.pilates.af1_conservacion import ejecutar_af1
    return await ejecutar_af1()

async def _step_af3():
    from src.pilates.af3_depuracion import ejecutar_af3
    return await ejecutar_af3()

async def _step_af5():
    from src.pilates.af5_identidad import ejecutar_af5
    return await ejecutar_af5()

async def _step_af_rest():
    from src.pilates.af_restantes import ejecutar_af_restantes
    return await ejecutar_af_restantes()

async def _step_propiocepcion():
    from src.pilates.propiocepcion import snapshot
    return await snapshot("semanal")

async def _step_mediador():
    from src.pilates.mediador import mediar
    return await mediar(ciclo=f"W{_hora_madrid().isocalendar()[1]:02d}-{_hora_madrid().isocalendar()[0]}")

async def _step_circuito():
    from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
    return await ejecutar_circuito_completo()

async def _step_briefing():
    from src.pilates.briefing import generar_briefing
    from src.pilates.whatsapp import enviar_texto, is_configured as wa_configured
    briefing = await generar_briefing()
    telefono_jesus = os.getenv("JESUS_TELEFONO", "")
    if wa_configured() and telefono_jesus and briefing.get("texto_wa"):
        await enviar_texto(telefono_jesus, briefing["texto_wa"])
    return {"briefing": "ok"}

async def _step_snapshot():
    from src.pilates.pizarras import snapshot_todas
    semana_iso = _hora_madrid().isocalendar()
    ciclo = f"W{semana_iso[1]:02d}-{semana_iso[0]}"
    return await snapshot_todas("authentic_pilates", ciclo)

async def _step_traductor():
    from src.pilates.traductor import traducir_acciones_semana
    return await traducir_acciones_semana()

async def _step_contenido():
    from src.pilates.contenido import generar_contenido_semana
    return await generar_contenido_semana()

async def _step_reputacion():
    from src.pilates.reputacion import programar_pedidos_resena
    return await programar_pedidos_resena()


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

    # Limpieza de caché LLM expirado
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT limpiar_cache_expirado()")
        log.info("cron_mensual_cache_limpiado")
    except Exception as e:
        log.error("cron_mensual_cache_error", error=str(e))

    # Cristalizador mensual (después del autófago)
    try:
        from src.pilates.generativa import cristalizar_patrones
        crist = await cristalizar_patrones()
        log.info("cron_mensual_cristalizador_ok",
                 patrones=len(crist.get("patrones_detectados", [])))
    except Exception as e:
        log.error("cron_mensual_cristalizador_error", error=str(e))

    # Memoria: patrones cross-ciclo → pizarra evolución
    try:
        from src.pilates.memoria import detectar_patrones_cross_ciclo
        mem = await detectar_patrones_cross_ciclo()
        log.info("cron_mensual_memoria_ok", patrones=mem.get("patrones", 0))
    except Exception as e:
        log.error("cron_mensual_memoria_error", error=str(e))

    # Anti-dilución: detectar drift de identidad en contenido publicado
    try:
        from src.pilates.anti_dilucion import detectar_drift_identidad
        drift = await detectar_drift_identidad()
        log.info("cron_mensual_anti_dilucion", status=drift.get("status"))
    except Exception as e:
        log.error("cron_mensual_anti_dilucion_error", error=str(e))

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

    # DB Cleanup: archivar datos antiguos (tablas que crecen sin bound)
    try:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT om_cleanup_old_data('authentic_pilates')")
            log.info("cron_mensual_cleanup_ok", resultado=str(result)[:200])
    except Exception as e:
        log.error("cron_mensual_cleanup_error", error=str(e))


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
                # Disparar Reactivo
                asyncio.create_task(_dispatch_reactivo(data))
            except Exception as e:
                log.error("senal_urgente_parse_error", error=str(e))

        await conn.add_listener("senal_urgente", callback)
        log.info("listen_notify_activo", canal="senal_urgente")

        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        log.error("listen_notify_error", error=str(e))


async def _dispatch_reactivo(payload: dict):
    """Dispatch señal urgente al Reactivo."""
    try:
        from src.pilates.reactivo import procesar_senal_urgente
        result = await procesar_senal_urgente(payload)
        log.info("reactivo_dispatch_ok", tipo=payload.get("tipo"), result=result.get("status"))
    except Exception as e:
        log.error("reactivo_dispatch_error", error=str(e))


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
                from src.db.client import get_pool
                pool = await get_pool()
                async with pool.acquire() as lock_conn:
                    if await _try_advisory_lock(lock_conn, LOCK_DIARIA):
                        try:
                            log.info("cron_ejecutando_diaria", hora=str(hora))
                            await asyncio.wait_for(_tarea_diaria(), timeout=1800)
                            await _marcar_ejecutado("diaria")
                        except asyncio.TimeoutError:
                            log.error("cron_diaria_timeout", timeout_s=1800)
                            await _marcar_ejecutado("diaria", "timeout")
                        finally:
                            await _release_advisory_lock(lock_conn, LOCK_DIARIA)
                    else:
                        log.info("cron_diaria_skip_locked", razon="otra instancia ejecutando")

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                if not await _ya_ejecutado("semanal", "semana"):
                    from src.db.client import get_pool
                    pool = await get_pool()
                    async with pool.acquire() as lock_conn:
                        if await _try_advisory_lock(lock_conn, LOCK_SEMANAL):
                            try:
                                log.info("cron_ejecutando_semanal", semana=hoy.isocalendar()[1])
                                await asyncio.wait_for(_tarea_semanal(), timeout=3600)
                                await _marcar_ejecutado("semanal")
                            except asyncio.TimeoutError:
                                log.error("cron_semanal_timeout", timeout_s=3600)
                                await _marcar_ejecutado("semanal", "timeout")
                            finally:
                                await _release_advisory_lock(lock_conn, LOCK_SEMANAL)
                        else:
                            log.info("cron_semanal_skip_locked", razon="otra instancia ejecutando")

            # Tarea mensual: día 1 después de las 08:00
            if hoy.day == 1 and hora >= time(8, 0):
                if not await _ya_ejecutado("mensual", "mes"):
                    from src.db.client import get_pool
                    pool = await get_pool()
                    async with pool.acquire() as lock_conn:
                        if await _try_advisory_lock(lock_conn, LOCK_MENSUAL):
                            try:
                                log.info("cron_ejecutando_mensual", mes=f"{hoy.year}-{hoy.month:02d}")
                                await asyncio.wait_for(_tarea_mensual(), timeout=1800)
                                await _marcar_ejecutado("mensual")
                            except asyncio.TimeoutError:
                                log.error("cron_mensual_timeout", timeout_s=1800)
                                await _marcar_ejecutado("mensual", "timeout")
                            finally:
                                await _release_advisory_lock(lock_conn, LOCK_MENSUAL)
                        else:
                            log.info("cron_mensual_skip_locked", razon="otra instancia ejecutando")

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

        # Despachar comunicaciones pendientes (pizarra comunicación)
        try:
            from src.pilates.reactivo import despachar_comunicaciones
            desp = await despachar_comunicaciones()
            if desp.get("enviados", 0) > 0:
                log.info("cron_despachar_ok", enviados=desp["enviados"])
        except Exception as e:
            log.error("cron_despachar_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
