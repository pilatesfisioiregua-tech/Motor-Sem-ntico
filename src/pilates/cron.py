"""Cron del Exocortex — Tareas programadas.

Ejecuta tareas periódicas sin dependencias externas.
Se inicia en el lifespan de FastAPI como background task.

Tareas:
- Diaria (06:00 Madrid): escuchar señales
- Semanal (lunes 07:00): calcular estrategia + ciclo completo
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, time, timedelta

log = structlog.get_logger()

# Zona horaria: Madrid = UTC+1 (invierno) / UTC+2 (verano)
# Simplificación: usamos UTC+1 fijo. Suficiente para un cron de SMB.
MADRID_OFFSET = timedelta(hours=1)


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (aprox)."""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    return utc_now + MADRID_OFFSET


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

    # Cristalizador mensual (después del autófago)
    try:
        from src.pilates.generativa import cristalizar_patrones
        crist = await cristalizar_patrones()
        log.info("cron_mensual_cristalizador_ok",
                 patrones=len(crist.get("patrones_detectados", [])))
    except Exception as e:
        log.error("cron_mensual_cristalizador_error", error=str(e))


async def cron_loop():
    """Loop principal del cron. Se ejecuta como background task.

    Revisa cada 15 minutos si hay tareas pendientes.
    Marca las ejecutadas para no repetir en el mismo día/semana.
    """
    log.info("cron_iniciado")

    ultima_diaria = None
    ultima_semanal = None

    while True:
        try:
            ahora = _hora_madrid()
            hoy = ahora.date()
            hora = ahora.time()

            # Tarea diaria: después de las 06:00, una vez al día
            if hora >= time(6, 0) and ultima_diaria != hoy:
                log.info("cron_ejecutando_diaria", hora=str(hora))
                await _tarea_diaria()
                ultima_diaria = hoy

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                semana = hoy.isocalendar()[1]
                if ultima_semanal != semana:
                    log.info("cron_ejecutando_semanal", semana=semana)
                    await _tarea_semanal()
                    ultima_semanal = semana

        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Vigía + Mecánico: cada iteración (cada 15 min)
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

        # Tarea mensual: día 1 después de las 08:00
        if hoy.day == 1 and hora >= time(8, 0):
            mes_actual = f"{hoy.year}-{hoy.month:02d}"
            if not hasattr(cron_loop, '_ultimo_mensual') or cron_loop._ultimo_mensual != mes_actual:
                log.info("cron_ejecutando_mensual", mes=mes_actual)
                await _tarea_mensual()
                cron_loop._ultimo_mensual = mes_actual

        # Dormir 15 minutos
        await asyncio.sleep(900)
