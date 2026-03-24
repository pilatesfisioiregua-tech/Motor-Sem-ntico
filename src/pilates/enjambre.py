"""Enjambre Cognitivo v4 — Contextualizador sobre tcf/.

NO reinventa el diagnóstico. Recibe DiagnosticoCompleto + Prescripcion
de tcf/ (código puro, determinista, con IC2-IC6 verificadas) y lo
CONTEXTUALIZA para Authentic Pilates.

6 clusters INT CONFIRMAN, CONTRADICEN o ENRIQUECEN el diagnóstico de código.
4 clusters P evalúan CÓMO PIENSA el negocio (pares IC5, desacoples IC3).
3 clusters R evalúan CÓMO RAZONA el negocio (validación IC6, desacoples IC4).

Modelo: claude-sonnet-4.6 (13 clusters en paralelo)
Coste: ~$0.65/ejecución ($0.30 INT + $0.35 P+R)
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import structlog
from datetime import date

from src.db.client import get_pool

log = structlog.get_logger()

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


# ============================================================
# 6 CLUSTERS — CONTEXTUALIZADORES
# ============================================================

CLUSTERS = {
    "analitico_operativo": {
        "ints": "INT-01(Lógica), INT-02(Computacional), INT-05(Estratégica)",
        "lente": "S",
        "angulo": "Estructura, cálculo, eficiencia. ¿Los datos reales confirman que estas INT están activas o ausentes?",
    },
    "financiero_constructivo": {
        "ints": "INT-07(Financiera), INT-10(Cinestésica), INT-16(Constructiva)",
        "lente": "S",
        "angulo": "Recursos, prototipado, acción física. ¿El negocio construye y ejecuta o solo planifica?",
    },
    "comprension_profunda": {
        "ints": "INT-03(Estructural), INT-08(Social), INT-17(Existencial), INT-18(Contemplativa)",
        "lente": "Se",
        "angulo": "Identidad, lo no dicho, urgencia falsa. ¿Jesús cuestiona por qué o solo ejecuta?",
    },
    "ecosistema_adaptacion": {
        "ints": "INT-04(Ecológica), INT-06(Política), INT-09(Lingüística), INT-14(Divergente)",
        "lente": "Se",
        "angulo": "Entorno, poder, lenguaje, opciones. ¿El negocio mira hacia afuera o es endogámico?",
    },
    "narrativa_identidad": {
        "ints": "INT-12(Narrativa), INT-15(Estética), INT-13(Prospectiva)",
        "lente": "Se+C",
        "angulo": "Historia, patrón, futuro. ¿Hay narrativa transferible o el método muere con el fundador?",
    },
    "reflexion_gobierno": {
        "ints": "INT-17(Existencial), INT-18(Contemplativa), INT-13(Prospectiva)",
        "lente": "Se(gobierno)",
        "angulo": "¿Las reglas siguen siendo válidas? ¿La urgencia es real? ¿El sistema ve sus propios sesgos?",
    },
}


# ============================================================
# 4 CLUSTERS DE PENSAMIENTO — Evalúan CÓMO piensa el negocio
# ============================================================

CLUSTERS_P = {
    "p_accion": {
        "ps": "P07(Convergente), P11(Encarnado), P13(Computacional)",
        "lente": "S",
        "angulo": """Evalúa si el negocio EJECUTA con método.
¿Las decisiones se cierran con criterio (P07) o quedan abiertas?
¿Hay acción física/operativa (P11) o solo planificación?
¿Los problemas se descomponen en pasos (P13) o se afrontan en bloque?
Si P07 domina SIN P06 → cierre prematuro (IC5). Señálalo.""",
    },
    "p_cuestionamiento": {
        "ps": "P03(Crítico), P05(Primeros principios), P08(Metacognición)",
        "lente": "Se",
        "angulo": """Evalúa si el negocio CUESTIONA sus premisas.
¿Se evalúa la evidencia antes de decidir (P03) o se actúa por inercia?
¿Se descomponen las premisas hasta lo fundamental (P05) o se aceptan como dadas?
¿El dueño observa su propio proceso de decisión (P08) o está dentro sin ver?
Si NINGUNO de estos P está activo → el negocio es ciego a sus propios sesgos.
Si P08 domina SIN P11 → piensa sobre pensar sin actuar (IC5).""",
    },
    "p_exploracion": {
        "ps": "P01(Lateral), P02(Sistémico), P06(Divergente), P15(Integrativo)",
        "lente": "Se",
        "angulo": """Evalúa si el negocio EXPLORA alternativas.
¿Se buscan soluciones fuera del marco habitual (P01)?
¿Se ven las conexiones entre partes (P02) o se tratan por separado?
¿Se generan muchas opciones antes de elegir (P06) o se va a la primera?
¿Se mantienen opuestos sin elegir hasta que emerge síntesis (P15)?
Si P06 activo SIN P07 → generación infinita sin cierre (IC5).""",
    },
    "p_transferencia": {
        "ps": "P04(Diseño), P09(Prospectivo), P10(Reflexivo), P12(Narrativo), P14(Estratégico)",
        "lente": "Se+C",
        "angulo": """Evalúa si el negocio TRANSFIERE y PROYECTA.
¿Hay ciclo de empatizar→prototipar→testear (P04)?
¿Se piensan escenarios futuros (P09) o solo el presente?
¿Se revisa la experiencia para extraer principios (P10)?
¿Se cuenta la historia del negocio de forma que otros la entiendan (P12)?
¿Se piensa en movimientos y secuencias (P14)?
Si P09 activo SIN P03 → proyección sin cuestionar premisas (extrapolación ciega).""",
    },
}

# ============================================================
# 3 CLUSTERS DE RAZONAMIENTO — Evalúan CÓMO razona el negocio
# ============================================================

CLUSTERS_R = {
    "r_operativo": {
        "rs": "R01(Deducción), R07(Bayesiano), R09(Eliminación), R12(Transductivo)",
        "lente": "S",
        "angulo": """Evalúa CÓMO el negocio llega a conclusiones OPERATIVAS.
¿Deduce correctamente de premisas (R01) o deduce de premisas falsas (Maginot)?
¿Actualiza creencias con evidencia nueva (R07) o mantiene priors fijos?
¿Descarta opciones sistemáticamente (R09) o elige al azar?
¿Transfiere de casos anteriores (R12) o cada problema es nuevo?
R01 SOLA sin R02/R03 = certeza desde premisas no validadas (IC6).
R07 con priors fijos sin R08 = echo chamber (IC6).""",
    },
    "r_comprension": {
        "rs": "R02(Inducción), R03(Abducción), R05(Causal), R08(Dialéctico), R10(Retroductivo)",
        "lente": "Se",
        "angulo": """Evalúa CÓMO el negocio COMPRENDE lo que pasa.
¿Generaliza desde observaciones (R02) o asume sin datos?
¿Busca la MEJOR explicación para lo observado (R03) o acepta la primera?
¿Establece causas reales (R05) o confunde correlación con causa?
¿Confronta posiciones opuestas para generar síntesis (R08)?
¿Descubre la estructura necesaria detrás de los fenómenos (R10)?
R03 es el razonamiento CENTRAL del diagnóstico ACD. Si está ausente,
el negocio no puede diagnosticar sus propios problemas.
R02 SOLA sin R06 = generalización sin testear excepciones (IC6).""",
    },
    "r_transferencia": {
        "rs": "R04(Analogía), R06(Contrafactual), R11(Modal)",
        "lente": "Se+C",
        "angulo": """Evalúa CÓMO el negocio TRANSFIERE y ANTICIPA.
¿Transfiere conocimiento entre dominios (R04) o cada área es un silo?
¿Evalúa qué pasaría SI... (R06) o solo reacciona a lo que ya pasó?
¿Distingue lo necesario de lo contingente (R11) o trata todo como inevitable?
R04 SOLA sin R09 = transferencia superficial sin depurar diferencias (IC6).
Si R06 está ausente, el negocio es CIEGO al riesgo futuro.
Estas son las herramientas de CONTINUIDAD — sin ellas, el método muere con el fundador.""",
    },
}


# ============================================================
# SYSTEM PROMPTS
# ============================================================

SYSTEM_CLUSTER = """Eres el cluster {nombre} del enjambre cognitivo de OMNI-MIND.

Tu trabajo: recibir un DIAGNÓSTICO FORMAL (generado por código con verificaciones IC2-IC6)
y evaluarlo contra la REALIDAD del negocio.

DIAGNÓSTICO DEL CÓDIGO (esto ya está computado, no lo reinventes):
{diagnostico_resumen}

Tus inteligencias: {ints} (lente {lente})
Tu ángulo: {angulo}

INSTRUCCIONES:
1. CONFIRMA lo que el código diagnosticó y los datos reales respaldan.
   "tcf/ dice INT-17 ausente. CONFIRMO: no hay evidencia de cuestionamiento de premisas."

2. CONTRADICE lo que el código diagnosticó pero los datos reales NO respaldan.
   "tcf/ dice INT-07 activa. CONTRADIGO: no hay cálculos de coste de oportunidad en las decisiones."

3. ENRIQUECE con información que el código NO puede ver (contexto humano, matices, patrones).
   "ENRIQUEZCO: INT-10 está activa pero solo en sesiones, no en gestión del negocio."

4. Evalúa la PRESCRIPCIÓN: ¿tiene sentido para este negocio concreto?
   "La prescripción dice activar INT-12. CONFIRMO: es urgente porque todo el método está en la cabeza de Jesús."

Responde en JSON:
{{
    "cluster": "{nombre}",
    "confirmaciones": [{{"int_o_regla": "INT-XX o ICX", "evidencia": "dato concreto"}}],
    "contradicciones": [{{"int_o_regla": "INT-XX o ICX", "evidencia": "dato que contradice", "correccion": "lo correcto es..."}}],
    "enriquecimientos": [{{"aspecto": "qué añade", "evidencia": "dato concreto", "implicacion": "qué significa"}}],
    "evaluacion_prescripcion": "¿la prescripción tiene sentido para este negocio? ¿qué ajustar?",
    "preguntas_nuevas": ["pregunta que el negocio debería hacerse"]
}}"""


SYSTEM_CLUSTER_P = """Eres el cluster de pensamiento {nombre} del enjambre cognitivo.

DIAGNÓSTICO DE CÓDIGO (tcf/):
{diagnostico_resumen}

Tus tipos de pensamiento: {ps}
Lente primaria: {lente}
Tu ángulo: {angulo}

EVALÚA:
1. ¿Estos P están ACTIVOS en este negocio? ¿Hay evidencia en las decisiones observables?
2. ¿Hay PARES COMPLEMENTARIOS (IC5) activos? ¿O un P domina sin su complemento?
3. ¿Hay DESACOPLES INT-P (IC3)? ¿Alguna INT detectada se procesa con un P incompatible?
4. ¿Qué EFECTO tienen estos P (o su ausencia) en las lentes/funciones?

Responde en JSON:
{{
    "cluster": "{nombre}",
    "ps_evaluados": [
        {{"id": "PXX", "activo": true, "evidencia": "dato concreto",
          "par_complementario": "PYY presente/ausente",
          "desacople_ic3": "INT-XX procesada con este P es compatible/incompatible"}}
    ],
    "efecto_lentes": {{
        "S": "cómo estos P impulsan o frenan S",
        "Se": "cómo estos P impulsan o frenan Se",
        "C": "cómo estos P impulsan o frenan C"
    }},
    "disfunciones_detectadas": ["ICX: descripción concreta"],
    "insights": ["algo que solo evaluando P se puede ver"]
}}"""


SYSTEM_CLUSTER_R = """Eres el cluster de razonamiento {nombre} del enjambre cognitivo.

DIAGNÓSTICO DE CÓDIGO (tcf/):
{diagnostico_resumen}

Tus tipos de razonamiento: {rs}
Lente primaria: {lente}
Tu ángulo: {angulo}

EVALÚA:
1. ¿Estos R están ACTIVOS en este negocio? ¿Cómo llega a conclusiones?
2. ¿Hay VALIDACIÓN CRUZADA (IC6)? ¿O un R opera aislado amplificando sesgos?
3. ¿Hay DESACOPLES INT-R (IC4)? ¿Alguna INT detectada usa un R incompatible?
4. ¿Qué EFECTO tienen estos R (o su ausencia) en las lentes/funciones?

Responde en JSON:
{{
    "cluster": "{nombre}",
    "rs_evaluados": [
        {{"id": "RXX", "activo": true, "evidencia": "dato concreto",
          "validacion_cruzada": "RYY lo valida / opera aislado",
          "desacople_ic4": "INT-XX con este R es compatible/incompatible"}}
    ],
    "efecto_lentes": {{
        "S": "cómo estos R impulsan o frenan S",
        "Se": "cómo estos R impulsan o frenan Se",
        "C": "cómo estos R impulsan o frenan C"
    }},
    "disfunciones_detectadas": ["ICX: descripción concreta"],
    "insights": ["algo que solo evaluando R se puede ver"]
}}"""


# ============================================================
# CONTEXTO DEL NEGOCIO
# ============================================================

async def _contexto_completo() -> dict:
    """Recopila datos reales del negocio para inyectar en clusters."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        clientes = await conn.fetch("""
            SELECT c.nombre, c.apellidos, ct.estado, ct.fecha_alta,
                (SELECT MAX(s.fecha) FROM om_asistencias a
                 JOIN om_sesiones s ON s.id=a.sesion_id
                 WHERE a.cliente_id=c.id AND a.estado='asistio') as ultima_asistencia,
                (SELECT co.tipo FROM om_contratos co
                 WHERE co.cliente_id=c.id AND co.estado='activo' LIMIT 1) as tipo_contrato
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id=c.id AND ct.tenant_id=$1
            WHERE ct.estado='activo'
        """, TENANT)

        grupos = await conn.fetch("""
            SELECT g.nombre, g.dias_semana, g.capacidad_max,
                (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocupadas
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
        """, TENANT)

        señales = await conn.fetch("""
            SELECT origen, tipo, payload, created_at
            FROM om_senales_agentes WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 20
        """, TENANT)

        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT) or 0

        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT) or 0

        try:
            identidad = await conn.fetchrow(
                "SELECT propuesta_valor, diferenciadores, tono FROM om_voz_identidad WHERE tenant_id=$1",
                TENANT)
        except Exception:
            identidad = None

        try:
            procesos = await conn.fetchval(
                "SELECT count(*) FROM om_procesos WHERE tenant_id=$1", TENANT) or 0
        except Exception:
            procesos = 0

        try:
            adn = await conn.fetchval(
                "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true", TENANT) or 0
        except Exception:
            adn = 0

    return {
        "clientes": [dict(c) for c in clientes],
        "grupos": [dict(g) for g in grupos],
        "señales_recientes": [
            {"origen": s["origen"], "tipo": s["tipo"],
             "payload": s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"])}
            for s in señales[:10]
        ],
        "ingresos_mes": float(ingresos),
        "deuda_pendiente": float(deuda),
        "identidad": dict(identidad) if identidad else {},
        "procesos": procesos,
        "adn": adn,
        "fecha": str(date.today()),
    }


# ============================================================
# MOTOR DE EJECUCIÓN
# ============================================================

async def _call_cluster(system_prompt: str, user_prompt: str, nombre: str) -> dict:
    """Ejecuta un cluster individual via motor.pensar()."""
    from src.motor.pensar import pensar, ConfigPensamiento
    from src.pilates.json_utils import extraer_json

    t0 = time.time()
    try:
        # Determinar lente desde el nombre del cluster
        lente = None
        for clusters_dict in (CLUSTERS, CLUSTERS_P, CLUSTERS_R):
            for cl_id, cl_def in clusters_dict.items():
                if cl_id in nombre.lower() or nombre.lower().endswith(cl_id):
                    lente = cl_def.get("lente")
                    break

        config = ConfigPensamiento(
            funcion="*",
            lente=lente,
            complejidad="media",
            max_tokens=4000,
            temperature=0.2,
            usar_cache=True,
            timeout=60.0,
        )
        resultado_llm = await pensar(system=system_prompt, user=user_prompt, config=config)
        raw = resultado_llm.texto

        parsed = extraer_json(raw)
        if parsed:
            log.info("enjambre_cluster_ok", cluster=nombre,
                     tiempo=round(time.time() - t0, 1))
            return parsed

        log.warning("enjambre_parse_error", cluster=nombre,
                    raw_preview=raw[:150])
        return {"error": "parse_error", "cluster": nombre}

    except Exception as e:
        log.warning("enjambre_cluster_error", cluster=nombre, error=str(e))
        return {"error": str(e)[:200], "cluster": nombre}


async def ejecutar_enjambre(diagnostico_completo=None, prescripcion_acd=None) -> dict:
    """Ejecuta enjambre como CONTEXTUALIZADOR sobre diagnóstico de tcf/.

    Args:
        diagnostico_completo: DiagnosticoCompleto de tcf/ (si None, lo lee del bus)
        prescripcion_acd: Prescripcion de tcf/ (si None, lo lee del bus)

    Returns:
        Diagnóstico anotado con evidencia de 6 clusters.
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()

    # Campos para compat con compositor
    perfil_detectado = None
    disfunciones_encontradas = 0

    # Si no se pasan, leer del último diagnóstico del bus
    if diagnostico_completo is None or prescripcion_acd is None:
        pool = await get_pool()
        async with pool.acquire() as conn:
            diag_row = await conn.fetchrow("""
                SELECT payload FROM om_senales_agentes
                WHERE tenant_id=$1 AND tipo='DIAGNOSTICO' AND origen='DIAGNOSTICADOR'
                ORDER BY created_at DESC LIMIT 1
            """, TENANT)
        if diag_row:
            payload = diag_row["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            perfil_detectado = payload.get("estado")
            rep = payload.get("repertorio", {})
            disfunciones_encontradas = len(rep.get("advertencias_ic", []))
            diagnostico_resumen = json.dumps(
                payload, ensure_ascii=False, indent=2, default=str)[:4000]
        else:
            return {"error": "No hay diagnóstico previo en el bus"}
    else:
        # Serializar DiagnosticoCompleto + Prescripcion para los clusters
        perfil_detectado = diagnostico_completo.estado.id
        if diagnostico_completo.repertorio:
            disfunciones_encontradas = len(
                diagnostico_completo.repertorio.advertencias_ic)
        diagnostico_resumen = json.dumps({
            "estado": diagnostico_completo.estado.id,
            "nombre": diagnostico_completo.estado.nombre,
            "lentes": diagnostico_completo.estado.lentes,
            "gap": diagnostico_completo.estado.gap,
            "repertorio": {
                "ints_activas": diagnostico_completo.repertorio.ints_activas,
                "ints_atrofiadas": diagnostico_completo.repertorio.ints_atrofiadas,
                "ints_ausentes": diagnostico_completo.repertorio.ints_ausentes,
                "ps_activos": diagnostico_completo.repertorio.ps_activos,
                "rs_activos": diagnostico_completo.repertorio.rs_activos,
                "advertencias_ic": diagnostico_completo.repertorio.advertencias_ic,
            },
            "prescripcion": {
                "ints": prescripcion_acd.ints,
                "ps": prescripcion_acd.ps,
                "rs": prescripcion_acd.rs,
                "objetivo": prescripcion_acd.objetivo,
                "lente_objetivo": prescripcion_acd.lente_objetivo,
                "secuencia": prescripcion_acd.secuencia,
            },
        }, ensure_ascii=False, indent=2, default=str)[:4000]

    # Contexto real del negocio
    ctx = await _contexto_completo()
    ctx_str = json.dumps(ctx, ensure_ascii=False, indent=2, default=str)[:5000]

    # Leer pizarra — qué están haciendo/pensando los demás agentes
    pizarra_str = ""
    try:
        from src.pilates.pizarra import leer_todo
        pizarra = await leer_todo()
        if pizarra:
            pizarra_str = json.dumps(pizarra, ensure_ascii=False, indent=2, default=str)[:2000]
    except Exception as e:
        log.warning("enjambre_pizarra_error", error=str(e))

    # Construir contexto enriquecido con pizarra
    user_prompt = f"DATOS REALES DEL NEGOCIO:\n{ctx_str}"
    if pizarra_str:
        user_prompt += f"\n\nPIZARRA — Lo que cada agente está haciendo/pensando:\n{pizarra_str}"

    # 13 clusters en PARALELO: 6 INT + 4 P + 3 R
    tareas = []

    # Clusters INT (6 existentes)
    for cl_id, cl_def in CLUSTERS.items():
        prompt = SYSTEM_CLUSTER.format(
            nombre=cl_id,
            diagnostico_resumen=diagnostico_resumen,
            ints=cl_def["ints"],
            lente=cl_def["lente"],
            angulo=cl_def["angulo"],
        )
        tareas.append(_call_cluster(prompt, user_prompt, f"Cluster-INT-{cl_id}"))

    # Clusters P (4 nuevos)
    for cl_id, cl_def in CLUSTERS_P.items():
        prompt = SYSTEM_CLUSTER_P.format(
            nombre=cl_id, diagnostico_resumen=diagnostico_resumen,
            ps=cl_def["ps"], lente=cl_def["lente"], angulo=cl_def["angulo"])
        tareas.append(_call_cluster(prompt, user_prompt, f"Cluster-P-{cl_id}"))

    # Clusters R (3 nuevos)
    for cl_id, cl_def in CLUSTERS_R.items():
        prompt = SYSTEM_CLUSTER_R.format(
            nombre=cl_id, diagnostico_resumen=diagnostico_resumen,
            rs=cl_def["rs"], lente=cl_def["lente"], angulo=cl_def["angulo"])
        tareas.append(_call_cluster(prompt, user_prompt, f"Cluster-R-{cl_id}"))

    resp_all = await asyncio.gather(*tareas)

    # Separar resultados en 3 dicts
    n_int = len(CLUSTERS)
    n_p = len(CLUSTERS_P)
    clusters_int = dict(zip(CLUSTERS.keys(), resp_all[:n_int]))
    clusters_p = dict(zip(CLUSTERS_P.keys(), resp_all[n_int:n_int + n_p]))
    clusters_r = dict(zip(CLUSTERS_R.keys(), resp_all[n_int + n_p:]))

    # Resultados combinados para compat
    resultados = {**clusters_int, **clusters_p, **clusters_r}

    # Emitir al bus
    from src.pilates.bus import emitir
    señales = 0
    for cl_id, resp in resultados.items():
        if "error" not in resp:
            try:
                tipo_cluster = "INT" if cl_id in CLUSTERS else ("P" if cl_id in CLUSTERS_P else "R")
                await emitir(
                    "PERCEPCION_CAUSAL",
                    f"ENJAMBRE_CLUSTER_{tipo_cluster}_{cl_id.upper()}",
                    {"tipo": f"cluster_{tipo_cluster.lower()}", "cluster": cl_id, "resultado": resp},
                    prioridad=5,
                )
                señales += 1
            except Exception as e:
                log.debug("silenced_exception", exc=str(e))

    # Persistir
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_enjambre_diagnosticos
                (tenant_id, estado_acd_base, resultado_lentes, resultado_funciones,
                 resultado_clusters, señales_emitidas, tiempo_total_s)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6, $7)
        """, TENANT, perfil_detectado or "enjambre_v4",
            json.dumps({"fuente": "tcf_codigo",
                        "diagnostico": diagnostico_resumen[:2000]}, default=str),
            json.dumps({"clusters_evaluaron": list(resultados.keys()),
                        "clusters_int": list(clusters_int.keys()),
                        "clusters_p": list(clusters_p.keys()),
                        "clusters_r": list(clusters_r.keys())},
                       default=str),
            json.dumps(resultados, ensure_ascii=False, default=str),
            señales, round(time.time() - t0, 0))

    dt = round(time.time() - t0, 1)
    total = len(resultados)
    errores = sum(1 for r in resultados.values() if "error" in r)

    # Consolidar métricas (INT: confirmaciones/contradicciones, P: ps_evaluados, R: rs_evaluados)
    exitosos = [r for r in resultados.values() if "error" not in r]
    total_confirmaciones = sum(len(r.get("confirmaciones", [])) for r in exitosos)
    total_contradicciones = sum(len(r.get("contradicciones", [])) for r in exitosos)
    total_enriquecimientos = sum(len(r.get("enriquecimientos", [])) for r in exitosos)
    total_disfunciones = sum(len(r.get("disfunciones_detectadas", [])) for r in exitosos)

    log.info("enjambre_v4_completo",
             clusters_int=n_int - sum(1 for r in clusters_int.values() if "error" in r),
             clusters_p=n_p - sum(1 for r in clusters_p.values() if "error" in r),
             clusters_r=len(CLUSTERS_R) - sum(1 for r in clusters_r.values() if "error" in r),
             total=total - errores, señales=señales,
             confirmaciones=total_confirmaciones,
             contradicciones=total_contradicciones,
             disfunciones=total_disfunciones, tiempo=dt)

    return {
        "status": "ok",
        "version": "v4_int_p_r",
        "clusters_ejecutados": total - errores,
        "agentes_ejecutados": total - errores,  # compat con compositor
        "errores": errores,
        "señales_emitidas": señales,
        "tiempo_total_s": dt,
        "confirmaciones": total_confirmaciones,
        "contradicciones": total_contradicciones,
        "enriquecimientos": total_enriquecimientos,
        "disfunciones_pr": total_disfunciones,
        "resultados": resultados,
        "clusters_int": clusters_int,
        "clusters_p": clusters_p,
        "clusters_r": clusters_r,
        # Compat con compositor.ejecutar_g4()
        "perfil_detectado": perfil_detectado,
        "disfunciones_encontradas": disfunciones_encontradas,
    }
