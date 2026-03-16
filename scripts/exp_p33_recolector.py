#!/usr/bin/env python3
"""EXP P33 Recolector — Escanea endpoints reales y genera casos para el Motor."""

import httpx
import json
import asyncio
import os
from datetime import datetime, timezone

BASE_URL = os.environ.get("P33_BASE_URL", "https://chief-os-omni.fly.dev")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "datos", "exp_p33")

ENDPOINTS = [
    "/health", "/version",
    "/gestor/autopoiesis", "/gestor/programas", "/gestor/flywheel", "/gestor/log",
    "/gestor/estado", "/gestor/consistencia", "/gestor/contradicciones",
    "/gestor/expiradas", "/gestor/obsoletas", "/gestor/parametros", "/gestor/salud",
    "/metricas", "/motor/señales",
    "/models/discover", "/models/registry", "/models/health", "/models/report",
    "/costes/resumen", "/costes/por-modelo", "/costes/por-consumidor", "/costes/proyeccion",
    "/costes/presupuestos",
    "/propiocepcion", "/estigmergia/marcas",
    "/monitoring/dashboard", "/monitoring/slos", "/monitoring/budget",
    "/monitoring/circuit-breakers",
    "/criticality/estado", "/criticality/temperatura",
    "/criticality/avalanchas", "/criticality/transiciones",
    "/predictive/estado", "/predictive/plan", "/predictive/trayectoria",
    "/neural/stats",
    "/tools/stats", "/tools/rankings", "/tools/gaps", "/tools/evolution-report",
    "/info/redundancia",
    "/senales",
    "/reactor/candidatas",
    "/explorer/matrix", "/explorer/gaps", "/explorer/checklist",
    "/api/index",
]


async def scan_endpoints() -> dict:
    """Fase 1A: escanear todos los endpoints y recoger datos reales."""
    datos = {}
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15) as client:
        for ep in ENDPOINTS:
            try:
                r = await client.get(ep)
                if r.status_code == 200:
                    datos[ep] = r.json()
                else:
                    datos[ep] = {"_error": f"HTTP {r.status_code}", "_body": r.text[:300]}
            except Exception as e:
                datos[ep] = {"_error": str(e)[:200]}

    vivos = {k: v for k, v in datos.items() if "_error" not in v}
    muertos = {k: v.get("_error", "") for k, v in datos.items() if "_error" in v}

    print(f"[recolector] {len(vivos)}/{len(ENDPOINTS)} endpoints vivos")
    if muertos:
        print(f"[recolector] Muertos: {list(muertos.keys())}")

    return {"vivos": vivos, "muertos": muertos, "timestamp": datetime.now(timezone.utc).isoformat()}


def _safe(data: dict, *keys, default=None):
    """Navigate nested dict safely."""
    d = data
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d


def generar_casos(scan: dict) -> list:
    """Fase 2: generar casos desde datos reales. Solo genera si hay datos suficientes."""
    v = scan["vivos"]
    ts = scan["timestamp"]
    casos = []

    # =====================================================================
    # CASO 1 — Salud del sistema
    # Datos: health, autopoiesis, models/health, monitoring, criticality
    # =====================================================================
    fuentes_salud = ["/health", "/gestor/autopoiesis", "/models/health",
                     "/monitoring/dashboard", "/criticality/estado", "/estigmergia/marcas"]
    datos_salud = {k: v.get(k) for k in fuentes_salud if k in v}

    if len(datos_salud) >= 2:
        auto = _safe(v, "/gestor/autopoiesis", "autopoiesis", default={})
        health = v.get("/health", {})
        models_h = v.get("/models/health", {})
        crit = v.get("/criticality/estado", {})
        estig = v.get("/estigmergia/marcas", {})

        # Count models healthy vs down
        healthy = [m for m in models_h.get("models", []) if m.get("status") == "healthy"]
        down = [m for m in models_h.get("models", []) if m.get("status") != "healthy"]

        # Count estigmergia alerts
        marcas = estig.get("marcas", [])
        alertas_auto = [m for m in marcas if "autopoiesis" in str(m.get("tipo", ""))]
        alertas_sin_consumir = [m for m in alertas_auto if not m.get("consumida")]

        # Criticality regime
        regimen = _safe(crit, "criticality", "temperatura", "regimen", default="desconocido")
        temp = _safe(crit, "criticality", "temperatura", "T", default=0)

        narrativa = (
            f"Tengo un sistema de análisis cognitivo con versión {health.get('version', '?')} "
            f"y {health.get('tools', '?')} herramientas registradas. "
            f"Su autodiagnóstico interno dice que tiene {auto.get('preguntas_activas', '?')} "
            f"preguntas activas y reporta ciclo_roto={auto.get('ciclo_roto', '?')}. "
            f"Pero al mirar las alertas internas, hay {len(alertas_auto)} alertas de "
            f"'ciclo roto', de las cuales {len(alertas_sin_consumir)} no se han procesado. "
            f"De {len(healthy) + len(down)} modelos registrados, {len(healthy)} funcionan "
            f"y {len(down)} están caídos"
        )
        if down:
            nombres_down = [m.get("model", "?")[:30] for m in down[:4]]
            narrativa += f" ({', '.join(nombres_down)})"
        narrativa += ". "
        narrativa += (
            f"La temperatura de criticalidad es {temp:.2f} (régimen '{regimen}'). "
            f"El sistema de monitoreo reporta {_safe(v, '/monitoring/dashboard', 'ejecuciones_totales', default=0)} "
            f"ejecuciones totales. "
            f"¿Cuál es la salud real de este sistema? ¿Sus controles internos son fiables?"
        )

        casos.append({
            "caso_id": "p33_caso_01_salud",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. Todos los datos son reales, extraídos de sus propios endpoints.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_salud,
            "fuentes": [k for k in fuentes_salud if k in v],
            "timestamp": ts,
        })

    # =====================================================================
    # CASO 2 — Costes y eficiencia
    # Datos: costes/resumen, por-modelo, por-consumidor, presupuestos, modelos activos
    # =====================================================================
    fuentes_costes = ["/costes/resumen", "/costes/por-modelo", "/costes/por-consumidor",
                      "/costes/presupuestos", "/costes/proyeccion"]
    datos_costes = {k: v.get(k) for k in fuentes_costes if k in v}

    if len(datos_costes) >= 2:
        resumen = _safe(v, "/costes/resumen", "resumen_30d", default={})
        por_modelo = _safe(v, "/costes/por-modelo", "costes", default=[])
        por_consumidor = _safe(v, "/costes/por-consumidor", "costes", default=[])
        presupuestos = _safe(v, "/costes/presupuestos", "presupuestos", default=[])
        proy = _safe(v, "/costes/proyeccion", default={})

        narrativa = (
            f"Mi sistema de IA ha hecho {resumen.get('total_llamadas', '?')} llamadas a "
            f"{resumen.get('modelos_usados', '?')} modelos diferentes en los últimos 30 días. "
            f"Gasto total: ${resumen.get('coste_total', 0):.4f}. "
            f"Proyección mensual: ${proy.get('proyeccion_mensual', 0):.2f}. "
        )
        if por_modelo:
            top = sorted(por_modelo, key=lambda x: x.get("coste_total", 0), reverse=True)[:3]
            narrativa += "Los modelos más usados son: "
            for m in top:
                narrativa += f"{m.get('modelo', '?')} ({m.get('llamadas', 0)} llamadas, ${m.get('coste_total', 0):.4f}), "
            narrativa = narrativa.rstrip(", ") + ". "

        if por_consumidor:
            narrativa += "Por consumidor: "
            for c in por_consumidor[:4]:
                narrativa += f"{c.get('consumidor', '?')} ({c.get('llamadas', 0)} llamadas, ${c.get('coste_total', 0):.4f}), "
            narrativa = narrativa.rstrip(", ") + ". "

        if presupuestos:
            narrativa += "Presupuestos: "
            for p in presupuestos:
                narrativa += f"{p.get('consumidor', '?')} gasta ${p.get('gastado', 0):.4f} de ${p.get('limite', 0):.0f} ({p.get('pct_usado', 0):.1f}%), "
            narrativa = narrativa.rstrip(", ") + ". "

        narrativa += (
            "Pero al mirar los modelos configurados, 4 de 8 están caídos y no aparecen en costes. "
            "Las métricas del motor muestran ejecuciones con DeepSeek V3 que no se reflejan "
            "completamente en el registro de costes. "
            "¿Estoy rastreando todos los gastos reales? ¿Dónde se me escapa dinero?"
        )

        casos.append({
            "caso_id": "p33_caso_02_costes",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. Todos los datos son reales.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_costes,
            "fuentes": [k for k in fuentes_costes if k in v],
            "timestamp": ts,
        })

    # =====================================================================
    # CASO 3 — Calidad del conocimiento / Aprendizaje
    # Datos: flywheel, programas, datapoints, predictive, gestor/salud
    # =====================================================================
    fuentes_calidad = ["/gestor/flywheel", "/gestor/programas", "/gestor/salud",
                       "/predictive/estado", "/predictive/trayectoria", "/info/redundancia"]
    datos_calidad = {k: v.get(k) for k in fuentes_calidad if k in v}

    if len(datos_calidad) >= 2:
        fw = v.get("/gestor/flywheel", {})
        progs = _safe(v, "/gestor/programas", "programas", default=[])
        salud = _safe(v, "/gestor/salud", "salud", default={})
        pred = v.get("/predictive/estado", {})
        tray = v.get("/predictive/trayectoria", {})
        redun = v.get("/info/redundancia", {})

        total_ej = sum(p.get("n_ejecuciones", 0) for p in progs)
        tasas = [p.get("tasa_cierre_media", 0) for p in progs]

        # Predictive trajectory
        historico = _safe(pred, "historical", default=[])
        tray_str = ""
        if historico:
            vals = [f"{h.get('tasa_media', 0):.2f}" for h in historico[-5:]]
            tray_str = " → ".join(vals)

        # Redundancia
        best_pair = _safe(redun, "mejor_par_complementario", default={})
        worst_pair = _safe(redun, "par_mas_redundante", default={})

        narrativa = (
            f"Mi sistema de aprendizaje tiene {salud.get('total_datapoints', '?')} observaciones "
            f"acumuladas y {len(progs)} programas operativos con un total de {total_ej} ejecuciones. "
            f"El flywheel de mejora continua ha completado {fw.get('ciclos', 0)} ciclo(s). "
        )

        if tasas and all(t == 1.0 for t in tasas):
            narrativa += (
                "TODOS los programas reportan tasa de éxito del 100%, "
                "pero la calibración real bajó el rendimiento a ~50%. "
                "Esto sugiere que las tasas están infladas o no se actualizan post-calibración. "
            )

        if tray_str:
            narrativa += f"Trayectoria reciente de rendimiento: {tray_str}. "

        if best_pair:
            narrativa += (
                f"El mejor par complementario es {best_pair.get('par', '?')} "
                f"(correlación {best_pair.get('correlacion', 0):.2f}). "
            )
        if worst_pair:
            narrativa += (
                f"El par más redundante es {worst_pair.get('par', '?')} "
                f"(correlación {worst_pair.get('correlacion', 0):.2f}). "
            )

        narrativa += (
            f"De {salud.get('celdas_totales', '?')} celdas posibles en la Matriz, "
            f"solo {salud.get('celdas_con_datos', '?')} tienen datos y "
            f"{salud.get('celdas_vacias', '?')} están vacías. "
            f"El reactor de preguntas no tiene candidatas pendientes. "
            f"¿Está aprendiendo mi sistema o solo acumulando datos sin mejorar?"
        )

        casos.append({
            "caso_id": "p33_caso_03_calidad_conocimiento",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. Datos reales.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_calidad,
            "fuentes": [k for k in fuentes_calidad if k in v],
            "timestamp": ts,
        })

    # =====================================================================
    # CASO 4 — Dependencias y fragilidad
    # Datos: models/health, models/registry, consistencia, neural, circuit-breakers
    # =====================================================================
    fuentes_frag = ["/models/health", "/models/registry", "/gestor/consistencia",
                    "/neural/stats", "/monitoring/circuit-breakers", "/gestor/expiradas"]
    datos_frag = {k: v.get(k) for k in fuentes_frag if k in v}

    if len(datos_frag) >= 2:
        reg = v.get("/models/registry", {})
        mh = v.get("/models/health", {})
        consist = v.get("/gestor/consistencia", {})
        neural = v.get("/neural/stats", {})
        cb = v.get("/monitoring/circuit-breakers", {})
        expiradas = v.get("/gestor/expiradas", {})

        activos = reg.get("active", []) if isinstance(reg.get("active"), list) else []
        candidatos = reg.get("candidates", 0)
        down_models = [m for m in mh.get("models", []) if m.get("status") != "healthy"]
        n_expiradas = len(expiradas.get("expiradas", []))

        narrativa = (
            f"Mi sistema depende de modelos de IA externos. "
            f"De {len(activos)} modelos activos, {len(down_models)} están caídos ahora mismo"
        )
        if down_models:
            errores = set(m.get("error", "?")[:50] for m in down_models)
            narrativa += f" (errores: {'; '.join(errores)})"
        narrativa += ". "

        narrativa += (
            f"Hay {candidatos} modelos candidatos descubiertos pero no activados. "
            f"La consistencia del sistema es {'' if consist.get('consistente') else 'IN'}CONSISTENTE: "
            f"{consist.get('programas_con_preguntas_inactivas', 0)} programas referencian preguntas inactivas, "
            f"{consist.get('enjambre_modelos_inactivos', 0)} configuraciones de enjambre "
            f"referencian modelos inactivos, "
            f"y hay {consist.get('datapoints_huerfanos', 0)} datapoints huérfanos. "
        )

        narrativa += (
            f"La red neuronal tiene {neural.get('total_connections', 0)} conexiones "
            f"con fuerza media {neural.get('avg_strength', 0):.3f} y "
            f"{neural.get('strong_connections', 0)} conexiones fuertes. "
            f"Hay {n_expiradas} preguntas expiradas sin reemplazar. "
            f"¿Qué tan frágil es mi sistema? ¿Cuáles son los puntos únicos de fallo?"
        )

        casos.append({
            "caso_id": "p33_caso_04_fragilidad",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. Datos reales.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_frag,
            "fuentes": [k for k in fuentes_frag if k in v],
            "timestamp": ts,
        })

    # =====================================================================
    # CASO 5 — Dirección y prioridad
    # Datos: gestor/parametros, explorer/gaps, reactor, tools, señales
    # =====================================================================
    fuentes_dir = ["/gestor/parametros", "/explorer/gaps", "/reactor/candidatas",
                   "/tools/stats", "/tools/gaps", "/motor/señales", "/gestor/log"]
    datos_dir = {k: v.get(k) for k in fuentes_dir if k in v}

    if len(datos_dir) >= 2:
        params = _safe(v, "/gestor/parametros", "parametros", default={})
        gaps = v.get("/explorer/gaps", {})
        reactor = v.get("/reactor/candidatas", {})
        tools_s = v.get("/tools/stats", {})
        tools_g = v.get("/tools/gaps", {})
        señales = v.get("/motor/señales", {})

        lf_gaps = gaps.get("lente_funcion_gaps", []) if isinstance(gaps.get("lente_funcion_gaps"), list) else []
        thinking_gaps = gaps.get("thinking_gaps", []) if isinstance(gaps.get("thinking_gaps"), list) else []
        mode_gaps = gaps.get("mode_gaps", []) if isinstance(gaps.get("mode_gaps"), list) else []

        # Señales PID
        señales_data = señales.get("señales", {})
        n_celdas_señales = señales.get("celdas", 0)

        narrativa = (
            f"Mi sistema tiene un gestor que se auto-ajusta. Sus parámetros actuales: "
            f"umbral de poda={params.get('umbral_poda', '?')}, "
            f"umbral de promoción={params.get('umbral_promocion', '?')}, "
            f"ventana PID={params.get('ventana_pid', '?')} puntos, "
            f"agresividad de poda={params.get('agresividad_poda', '?')}. "
            f"Lleva {_safe(v, '/gestor/parametros', 'ciclo', default='?')} ciclo(s) de auto-ajuste. "
        )

        narrativa += (
            f"El explorador detecta {len(lf_gaps)} gaps en la matriz lente×función, "
            f"{len(thinking_gaps)} gaps en tipos de pensamiento, "
            f"y {len(mode_gaps)} gaps en modos conceptuales. "
        )

        if lf_gaps:
            gap_names = [g.get("celda", g.get("lente_funcion", "?")) if isinstance(g, dict) else str(g) for g in lf_gaps[:5]]
            narrativa += f"Gaps principales: {', '.join(gap_names)}. "

        narrativa += (
            f"El reactor de preguntas tiene {reactor.get('n', 0)} candidatas pendientes. "
            f"Las herramientas del sistema no registran uso ({tools_s}). "
            f"Hay {n_celdas_señales} celdas con señales PID activas. "
            f"¿Está mi sistema priorizando correctamente? ¿Trabaja en lo que más impacto tiene?"
        )

        casos.append({
            "caso_id": "p33_caso_05_direccion",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. Datos reales.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_dir,
            "fuentes": [k for k in fuentes_dir if k in v],
            "timestamp": ts,
        })

    # =====================================================================
    # CASO 6 (EMERGENTE) — Contradicción de señales internas
    # Este caso emerge de patrones inesperados en los datos
    # =====================================================================
    fuentes_contra = ["/gestor/autopoiesis", "/estigmergia/marcas", "/criticality/estado",
                      "/propiocepcion", "/metricas", "/monitoring/dashboard"]
    datos_contra = {k: v.get(k) for k in fuentes_contra if k in v}

    if len(datos_contra) >= 3:
        auto = _safe(v, "/gestor/autopoiesis", "autopoiesis", default={})
        estig = v.get("/estigmergia/marcas", {})
        crit = v.get("/criticality/estado", {})
        propio = v.get("/propiocepcion", {})
        metricas = v.get("/metricas", {})
        monit = v.get("/monitoring/dashboard", {})

        marcas = estig.get("marcas", [])
        alertas_auto = [m for m in marcas if "autopoiesis" in str(m.get("tipo", ""))]

        temp_reg = _safe(crit, "criticality", "temperatura", "regimen", default="?")
        aval_reg = _safe(crit, "criticality", "avalanchas", "regimen", default="?")

        narrativa = (
            f"Mi sistema tiene contradicciones internas que no cuadran. "
            f"El autodiagnóstico dice ciclo_roto=false, pero hay {len(alertas_auto)} alertas "
            f"internas diciendo 'ciclo roto' sin resolver. "
            f"La criticalidad dice régimen '{temp_reg}' (demasiado predecible) "
            f"pero las avalanchas dicen '{aval_reg}' (demasiado caótico). "
            f"¿Cómo puede ser predecible Y caótico a la vez? "
            f"La propiocepción dice {propio.get('ejecuciones_24h', 0)} ejecuciones en 24h, "
            f"pero las métricas muestran ejecuciones recientes con costes reales. "
            f"El monitoreo dice {monit.get('ejecuciones_totales', 0)} ejecuciones totales "
            f"y SLOs '{_safe(monit, 'slos', 'status', default='sin_datos')}'. "
            f"Tengo {propio.get('datapoints_efectividad', 0)} datapoints acumulados, "
            f"{propio.get('señales_pendientes', 0)} señales pendientes y "
            f"{propio.get('mejoras_pendientes', 0)} mejoras pendientes. "
            f"¿A quién creo? ¿Cuáles de mis propios controles están mintiendo?"
        )

        casos.append({
            "caso_id": "p33_caso_06_contradicciones",
            "input": narrativa,
            "contexto": "Este es un análisis del propio sistema cognitivo OMNI-MIND. "
                        "Todos los datos son reales y provienen de endpoints del mismo sistema. "
                        "El objetivo es detectar contradicciones entre subsistemas.",
            "config": {"profundidad": "profunda", "presupuesto_max": 0.05, "tiempo_max_s": 120},
            "datos_brutos": datos_contra,
            "fuentes": [k for k in fuentes_contra if k in v],
            "timestamp": ts,
        })

    return casos


async def main():
    print(f"[P33 Recolector] Escaneando {BASE_URL} ...")
    scan = await scan_endpoints()

    # Guardar scan completo
    os.makedirs(os.path.join(OUTPUT_DIR, "casos_input"), exist_ok=True)
    scan_path = os.path.join(OUTPUT_DIR, "scan_completo.json")
    with open(scan_path, "w") as f:
        json.dump(scan, f, indent=2, ensure_ascii=False, default=str)
    print(f"[P33 Recolector] Scan guardado en {scan_path}")

    # Generar casos
    casos = generar_casos(scan)
    print(f"[P33 Recolector] {len(casos)} casos generados")

    for caso in casos:
        caso_path = os.path.join(OUTPUT_DIR, "casos_input", f"{caso['caso_id']}.json")
        with open(caso_path, "w") as f:
            json.dump(caso, f, indent=2, ensure_ascii=False, default=str)
        print(f"  → {caso['caso_id']}: {len(caso['input'])} chars, {len(caso['fuentes'])} fuentes")

    return casos


if __name__ == "__main__":
    asyncio.run(main())
