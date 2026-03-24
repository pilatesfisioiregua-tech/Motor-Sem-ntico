# B-ORG-02: Diagnosticador Autónomo + Buscador por Gaps

**Fecha:** 22 marzo 2026
**Objetivo:** Crear dos agentes autónomos que funcionan en cron: (1) Diagnosticador que ejecuta ACD sobre datos reales de Pilates, (2) Buscador que usa Perplexity dirigido por gaps ACD.
**Depende de:** B-ORG-01 (bus de señales)
**Archivos a crear/modificar:** 2 nuevos + 1 modificado
**Tiempo estimado:** 30-45 min

---

## PASO 1: Diagnosticador autónomo — src/pilates/diagnosticador.py

**Crear archivo:** `motor-semantico/src/pilates/diagnosticador.py`

Este agente recopila datos REALES de Pilates, calcula las 3 lentes (S, Se, C), ejecuta clasificar_estado() que YA EXISTE en src/tcf/diagnostico.py, persiste el resultado, y emite señal DIAGNOSTICO al bus si el estado cambió respecto al último diagnóstico.

```python
"""Diagnosticador autónomo — Agente G2: datos reales → diagnóstico ACD.

Ejecuta semanalmente (lunes) en cron.
Recopila métricas reales de Authentic Pilates → calcula lentes → clasifica estado → persiste → señal si cambio.

Funciones existentes que usa:
- src.tcf.diagnostico.clasificar_estado(lentes) → EstadoDiagnostico
- src.db.client.log_diagnostico(data) → UUID
- src.pilates.bus.emitir(tipo, origen, payload) → UUID
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool, log_diagnostico
from src.tcf.diagnostico import clasificar_estado

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "DIAGNOSTICADOR"


async def _recopilar_metricas() -> dict:
    """Recopila métricas reales de las últimas 4 semanas para calcular lentes.

    Devuelve dict con métricas brutas que se traducen a scores F1-F7.
    """
    pool = await get_pool()
    ahora = datetime.now(timezone.utc)
    hace_4_sem = ahora - timedelta(weeks=4)

    async with pool.acquire() as conn:
        # F1 Conservación: tasa retención, asistencia regular
        total_activos = await conn.fetchval("""
            SELECT count(*) FROM om_contrato
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT) or 0

        bajas_periodo = await conn.fetchval("""
            SELECT count(*) FROM om_contrato
            WHERE tenant_id = $1 AND estado = 'cancelado'
            AND updated_at >= $2
        """, TENANT, hace_4_sem) or 0

        # F2 Captación: nuevos clientes
        nuevos_clientes = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, hace_4_sem) or 0

        # F3 Depuración: sesiones con <3 alumnos (grupo), horarios vacíos
        sesiones_grupo = await conn.fetchval("""
            SELECT count(*) FROM om_sesion
            WHERE tenant_id = $1 AND tipo = 'grupo'
            AND fecha >= $2::date
        """, TENANT, hace_4_sem.date()) or 0

        sesiones_bajas = await conn.fetchval("""
            SELECT count(*) FROM om_sesion s
            WHERE s.tenant_id = $1 AND s.tipo = 'grupo'
            AND s.fecha >= $2::date
            AND (SELECT count(*) FROM om_asistencia a WHERE a.sesion_id = s.id) < 3
        """, TENANT, hace_4_sem.date()) or 0

        # F4 Distribución: ocupación media
        total_asistencias = await conn.fetchval("""
            SELECT count(*) FROM om_asistencia a
            JOIN om_sesion s ON a.sesion_id = s.id
            WHERE s.tenant_id = $1 AND s.fecha >= $2::date
        """, TENANT, hace_4_sem.date()) or 0

        # F5 Identidad: señales de voz activas
        senales_voz = await conn.fetchval("""
            SELECT count(*) FROM om_voz_senales
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, hace_4_sem) or 0

        # F6 Adaptación: tensiones registradas
        tensiones = await conn.fetchval("""
            SELECT count(*) FROM om_voz_tensiones
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, hace_4_sem) or 0

        # F7 Replicación: procesos documentados
        procesos = await conn.fetchval("""
            SELECT count(*) FROM om_voz_adn_procesos
            WHERE tenant_id = $1
        """, TENANT) or 0

        # Cobros: pagos del periodo
        cobrado = await conn.fetchval("""
            SELECT COALESCE(sum(importe), 0) FROM om_pago
            WHERE tenant_id = $1 AND created_at >= $2 AND estado = 'confirmado'
        """, TENANT, hace_4_sem) or 0

        pendiente = await conn.fetchval("""
            SELECT COALESCE(sum(importe), 0) FROM om_cargo
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT) or 0

    return {
        "total_activos": total_activos,
        "bajas_periodo": bajas_periodo,
        "nuevos_clientes": nuevos_clientes,
        "sesiones_grupo": sesiones_grupo,
        "sesiones_bajas": sesiones_bajas,
        "total_asistencias": total_asistencias,
        "senales_voz": senales_voz,
        "tensiones": tensiones,
        "procesos": procesos,
        "cobrado": float(cobrado),
        "pendiente": float(pendiente),
    }


def _metricas_a_lentes(m: dict) -> dict[str, float]:
    """Traduce métricas brutas a las 3 lentes ACD (0.0 a 1.0).

    Salud (S): F1 retención + F3 depuración + F4 distribución → ¿sobrevive?
    Sentido (Se): F2 captación + F5 identidad + F6 adaptación → ¿tiene propósito?
    Continuidad (C): F7 replicación + cobros + documentación → ¿puede transferirse?
    """
    # F1: Retención (0-1). Si 0 activos, 0.
    tasa_retencion = 1.0 - (m["bajas_periodo"] / max(m["total_activos"], 1))
    tasa_retencion = max(0.0, min(1.0, tasa_retencion))

    # F3: Depuración (0-1). Ratio sesiones eficientes.
    eficiencia_sesiones = 1.0 - (m["sesiones_bajas"] / max(m["sesiones_grupo"], 1))
    eficiencia_sesiones = max(0.0, min(1.0, eficiencia_sesiones))

    # F4: Distribución (0-1). Asistencia media por sesión / 6 (capacidad grupo).
    asist_media = m["total_asistencias"] / max(m["sesiones_grupo"], 1)
    distribucion = min(1.0, asist_media / 6.0)

    # F2: Captación (0-1). Nuevos / activos.
    captacion = min(1.0, m["nuevos_clientes"] / max(m["total_activos"] * 0.1, 1))

    # F5: Identidad (0-1). Señales de voz.
    identidad = min(1.0, m["senales_voz"] / 20.0)  # 20 señales/mes = pleno

    # F6: Adaptación (0-1). Tensiones gestionadas.
    adaptacion = min(1.0, m["tensiones"] / 5.0)  # 5 tensiones/mes = pleno

    # F7: Replicación (0-1). Procesos documentados.
    replicacion = min(1.0, m["procesos"] / 10.0)  # 10 procesos = pleno

    # Cobro: ratio cobrado vs pendiente.
    cobro_ratio = m["cobrado"] / max(m["cobrado"] + m["pendiente"], 1)

    # Lentes
    salud = (tasa_retencion * 0.4 + eficiencia_sesiones * 0.3 + distribucion * 0.3)
    sentido = (captacion * 0.3 + identidad * 0.4 + adaptacion * 0.3)
    continuidad = (replicacion * 0.4 + cobro_ratio * 0.4 + min(1.0, m["procesos"] / 15.0) * 0.2)

    return {
        "salud": round(salud, 3),
        "sentido": round(sentido, 3),
        "continuidad": round(continuidad, 3),
    }


def _metricas_a_vector_f(m: dict) -> dict[str, float]:
    """Traduce métricas a vector funcional F1-F7 (para persistencia)."""
    tasa_retencion = 1.0 - (m["bajas_periodo"] / max(m["total_activos"], 1))
    captacion = min(1.0, m["nuevos_clientes"] / max(m["total_activos"] * 0.1, 1))
    eficiencia = 1.0 - (m["sesiones_bajas"] / max(m["sesiones_grupo"], 1))
    asist_media = m["total_asistencias"] / max(m["sesiones_grupo"], 1)
    distribucion = min(1.0, asist_media / 6.0)
    identidad = min(1.0, m["senales_voz"] / 20.0)
    adaptacion = min(1.0, m["tensiones"] / 5.0)
    replicacion = min(1.0, m["procesos"] / 10.0)

    return {
        "F1": round(max(0, min(1, tasa_retencion)), 3),
        "F2": round(max(0, min(1, captacion)), 3),
        "F3": round(max(0, min(1, eficiencia)), 3),
        "F4": round(max(0, min(1, distribucion)), 3),
        "F5": round(max(0, min(1, identidad)), 3),
        "F6": round(max(0, min(1, adaptacion)), 3),
        "F7": round(max(0, min(1, replicacion)), 3),
    }


async def diagnosticar_tenant() -> dict:
    """Ejecuta diagnóstico ACD completo sobre datos reales.

    Returns:
        dict con estado, lentes, vector, flags, y si cambió respecto al anterior.
    """
    # 1. Recopilar métricas reales
    metricas = await _recopilar_metricas()
    log.info("diagnosticador_metricas", **{k: v for k, v in metricas.items() if isinstance(v, (int, float))})

    # 2. Traducir a lentes
    lentes = _metricas_a_lentes(metricas)
    vector_f = _metricas_a_vector_f(metricas)
    log.info("diagnosticador_lentes", **lentes)

    # 3. Clasificar estado ACD (función existente en src/tcf/diagnostico.py)
    estado = clasificar_estado(lentes)
    log.info("diagnosticador_estado", id=estado.id, nombre=estado.nombre, gap=estado.gap)

    # 4. Persistir diagnóstico
    diag_data = {
        "caso_input": f"Diagnóstico autónomo Authentic Pilates — {datetime.now(timezone.utc).isoformat()[:10]}",
        "vector_pre": json.dumps(vector_f),
        "lentes_pre": json.dumps(lentes),
        "estado_pre": estado.id,
        "flags_pre": [f.nombre for f in estado.flags] if estado.flags else [],
        "metricas": json.dumps({"raw": metricas}),
        "resultado": "pendiente",
    }
    diag_id = await log_diagnostico(diag_data)

    # 5. Comparar con último diagnóstico anterior
    cambio = False
    pool = await get_pool()
    async with pool.acquire() as conn:
        anterior = await conn.fetchrow("""
            SELECT estado_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC
            OFFSET 1 LIMIT 1
        """)
    if anterior and anterior["estado_pre"] != estado.id:
        cambio = True

    # 6. Emitir señal al bus si cambió o si hay flags
    if cambio or estado.flags:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "DIAGNOSTICO", ORIGEN,
                {
                    "estado": estado.id,
                    "nombre": estado.nombre,
                    "lentes": lentes,
                    "gap": estado.gap,
                    "flags": [f.nombre for f in estado.flags],
                    "cambio": cambio,
                    "anterior": anterior["estado_pre"] if anterior else None,
                    "diagnostico_id": diag_id,
                },
                prioridad=2 if cambio else 4,
            )
        except Exception as e:
            log.warning("diagnosticador_bus_error", error=str(e))

    resultado = {
        "diagnostico_id": diag_id,
        "estado": estado.id,
        "nombre": estado.nombre,
        "tipo": estado.tipo,
        "lentes": lentes,
        "vector_f": vector_f,
        "gap": estado.gap,
        "flags": [f.nombre for f in estado.flags],
        "cambio_vs_anterior": cambio,
        "metricas_raw": metricas,
    }

    log.info("diagnosticador_completo", estado=estado.id, cambio=cambio, flags=len(estado.flags))
    return resultado
```

---

## PASO 2: Buscador por gaps — src/pilates/buscador.py

**Crear archivo:** `motor-semantico/src/pilates/buscador.py`

Este agente lee el último diagnóstico ACD, identifica las funciones con score más bajo (gaps), genera queries inteligentes, las envía a Perplexity (Capa A ya existe en src/pilates/capa_a.py), y persiste resultados.

```python
"""Buscador por gaps — Agente G3: gaps ACD → queries → Perplexity → corpus.

Ejecuta semanalmente (lunes) en cron, después del Diagnosticador.
Lee último diagnóstico → identifica F con menor score → genera queries → Perplexity → persiste → señal OPORTUNIDAD.

Funciones existentes que usa:
- src.pilates.capa_a (si existe) o Perplexity directo
- src.pilates.bus.emitir
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "BUSCADOR"

# Plantillas de query por función
QUERY_TEMPLATES = {
    "F1": [
        "estrategias retención clientes estudio pilates pequeño",
        "cómo reducir bajas en negocio fitness boutique",
    ],
    "F2": [
        "captación clientes pilates marketing local bajo presupuesto",
        "cómo conseguir nuevos alumnos pilates pueblo pequeño",
    ],
    "F3": [
        "optimizar horarios estudio pilates ocupación baja",
        "cuándo cerrar clases poco rentables negocio fitness",
    ],
    "F4": [
        "distribución óptima horarios clases grupales pilates",
        "equilibrar carga semanal estudio pilates individual y grupo",
    ],
    "F5": [
        "diferenciación estudio pilates marca personal propuesta valor",
        "identidad digital pilates estudio independiente",
    ],
    "F6": [
        "adaptación negocio pilates tendencias sector fitness España",
        "cambios regulatorios autónomos fitness España 2026",
    ],
    "F7": [
        "documentar procesos estudio pilates para escalar",
        "sistematizar operaciones negocio pilates unipersonal",
    ],
}


async def _obtener_ultimo_diagnostico() -> dict | None:
    """Lee el último diagnóstico autónomo."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT id, vector_pre, lentes_pre, estado_pre, flags_pre, metricas
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC
            LIMIT 1
        """)
    if not row:
        return None
    return dict(row)


def _identificar_gaps(vector_f: dict, n_gaps: int = 2) -> list[str]:
    """Identifica las N funciones con menor score."""
    sorted_f = sorted(vector_f.items(), key=lambda x: x[1])
    return [f for f, _ in sorted_f[:n_gaps]]


def _generar_queries(gaps: list[str]) -> list[dict]:
    """Genera queries para Perplexity basadas en los gaps."""
    queries = []
    for gap in gaps:
        templates = QUERY_TEMPLATES.get(gap, [])
        for t in templates:
            queries.append({"funcion": gap, "query": t})
    return queries


async def _buscar_perplexity(query: str) -> dict | None:
    """Ejecuta query en Perplexity API. Devuelve resultado o None."""
    import os
    api_key = os.environ.get("PERPLEXITY_API_KEY")
    if not api_key:
        log.warning("buscador_sin_perplexity_key")
        return None

    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-sonar-small-128k-online",
                    "messages": [
                        {"role": "system", "content": "Eres un asistente de investigación para un estudio de Pilates en La Rioja, España. Responde con datos concretos, tendencias y recomendaciones accionables. Máximo 300 palabras."},
                        {"role": "user", "content": query},
                    ],
                    "max_tokens": 500,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            contenido = data["choices"][0]["message"]["content"]
            return {"query": query, "respuesta": contenido, "model": data.get("model", "sonar")}
    except Exception as e:
        log.warning("buscador_perplexity_error", query=query[:50], error=str(e))
        return None


async def _persistir_resultado(funcion: str, query: str, respuesta: str):
    """Persiste resultado en om_voz_capa_a."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verificar si la tabla existe
        exists = await conn.fetchval("""
            SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'om_voz_capa_a')
        """)
        if not exists:
            # Crear tabla si no existe
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS om_voz_capa_a (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    created_at TIMESTAMPTZ DEFAULT now(),
                    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
                    funcion TEXT NOT NULL,
                    query TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    fuente TEXT DEFAULT 'perplexity',
                    metadata JSONB DEFAULT '{}'
                )
            """)

        await conn.execute("""
            INSERT INTO om_voz_capa_a (tenant_id, funcion, query, respuesta, fuente)
            VALUES ($1, $2, $3, $4, 'perplexity')
        """, TENANT, funcion, query, respuesta)


async def buscar_por_gaps() -> dict:
    """Ejecuta búsqueda dirigida por gaps ACD.

    Returns:
        dict con gaps identificados, queries ejecutadas, resultados.
    """
    # 1. Obtener último diagnóstico
    diag = await _obtener_ultimo_diagnostico()
    if not diag:
        return {"error": "No hay diagnóstico previo. Ejecutar diagnosticar_tenant primero."}

    vector_f = diag["vector_pre"]
    if isinstance(vector_f, str):
        vector_f = json.loads(vector_f)

    # 2. Identificar gaps
    gaps = _identificar_gaps(vector_f, n_gaps=2)
    log.info("buscador_gaps", gaps=gaps, vector=vector_f)

    # 3. Generar queries
    queries = _generar_queries(gaps)

    # 4. Ejecutar en Perplexity
    resultados = []
    for q in queries:
        result = await _buscar_perplexity(q["query"])
        if result:
            await _persistir_resultado(q["funcion"], q["query"], result["respuesta"])
            resultados.append({**q, "respuesta_preview": result["respuesta"][:200]})

    # 5. Emitir señal OPORTUNIDAD si hay resultados
    if resultados:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "OPORTUNIDAD", ORIGEN,
                {
                    "gaps": gaps,
                    "queries_ejecutadas": len(resultados),
                    "funciones_buscadas": list(set(r["funcion"] for r in resultados)),
                    "diagnostico_id": str(diag["id"]),
                },
                prioridad=6,
            )
        except Exception as e:
            log.warning("buscador_bus_error", error=str(e))

    resultado = {
        "gaps_identificados": gaps,
        "vector_f": vector_f,
        "queries_generadas": len(queries),
        "resultados_perplexity": len(resultados),
        "detalle": resultados,
    }

    log.info("buscador_completo", gaps=gaps, resultados=len(resultados))
    return resultado
```

---

## PASO 3: Endpoints REST

**Modificar archivo:** `motor-semantico/src/pilates/router.py`

Añadir después de los endpoints del bus (de B-ORG-01):

```python
# ============================================================
# DIAGNOSTICADOR + BUSCADOR — Agentes autónomos ACD
# ============================================================

@router.post("/acd/diagnosticar-tenant")
async def acd_diagnosticar_tenant():
    """Ejecuta diagnóstico ACD sobre datos reales de Authentic Pilates."""
    from src.pilates.diagnosticador import diagnosticar_tenant
    resultado = await diagnosticar_tenant()
    return resultado


@router.post("/acd/buscar-por-gaps")
async def acd_buscar_por_gaps():
    """Busca información dirigida por gaps ACD vía Perplexity."""
    from src.pilates.buscador import buscar_por_gaps
    resultado = await buscar_por_gaps()
    return resultado
```

---

## PASO 4: Añadir al cron (lunes)

**Modificar archivo:** `motor-semantico/src/pilates/cron.py`

En la función `_tarea_semanal()`, añadir DESPUÉS de calcular_estrategia:

```python
        # 3. Diagnóstico ACD autónomo
        from src.pilates.diagnosticador import diagnosticar_tenant
        diag = await diagnosticar_tenant()
        log.info("cron_semanal_acd_ok", estado=diag.get("estado"), cambio=diag.get("cambio_vs_anterior"))

        # 4. Búsqueda dirigida por gaps
        from src.pilates.buscador import buscar_por_gaps
        busq = await buscar_por_gaps()
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))
```

El bloque completo de `_tarea_semanal` quedará:

```python
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

        # 4. Búsqueda dirigida por gaps
        from src.pilates.buscador import buscar_por_gaps
        busq = await buscar_por_gaps()
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))
```

---

## TESTS PASS/FAIL

### TEST 1: Diagnosticar tenant
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/acd/diagnosticar-tenant \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
ok = all([
    d.get('estado'),
    d.get('lentes', {}).get('salud') is not None,
    d.get('lentes', {}).get('sentido') is not None,
    d.get('lentes', {}).get('continuidad') is not None,
    d.get('diagnostico_id'),
])
print('PASS' if ok else 'FAIL:', json.dumps({k:v for k,v in d.items() if k != 'metricas_raw'}, indent=2))
"
```

### TEST 2: Estado ACD es uno de los 10 válidos
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/acd/diagnosticar-tenant \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
validos = {'E1','E2','E3','E4','operador_ciego','genio_mortal','automata_eterno','visionario_fragil','maquina_sin_alma','equilibrista_exhausto'}
print('PASS' if d.get('estado') in validos else 'FAIL: estado=' + str(d.get('estado')))
"
```

### TEST 3: Diagnóstico genera señal en bus
```bash
# Ejecutar diagnóstico primero (test 1), luego:
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/historial?tipo=DIAGNOSTICO&origen=DIAGNOSTICADOR&limite=3' \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
# Puede que no haya señal si el estado no cambió y no hay flags. Eso es OK.
print('PASS' if d.get('total',0) >= 0 else 'FAIL:', d)
print('INFO: señales DIAGNOSTICO encontradas:', d.get('total',0))
"
```

### TEST 4: Buscar por gaps (puede fallar si no hay PERPLEXITY_API_KEY)
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/acd/buscar-por-gaps \
  | python3 -c "
import sys,json
d=json.load(sys.stdin)
if d.get('error'):
    print('EXPECTED: No hay diagnóstico previo' if 'diagnóstico' in d['error'].lower() else 'FAIL:', d['error'])
elif d.get('gaps_identificados'):
    print('PASS: gaps=', d['gaps_identificados'], 'resultados=', d.get('resultados_perplexity', 0))
    if d.get('resultados_perplexity', 0) == 0:
        print('INFO: 0 resultados Perplexity — verificar PERPLEXITY_API_KEY en fly.io secrets')
else:
    print('FAIL:', d)
"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1 y 2 devuelven PASS.** Test 3 es informativo. Test 4 depende de PERPLEXITY_API_KEY (si no está configurada, devuelve 0 resultados — eso es esperado, no FAIL).

**FAIL = Test 1 o 2 devuelven FAIL.** Revisar logs con `fly logs -a chief-os-omni`.

---

## SECUENCIA DE EJECUCIÓN

1. Primero completar B-ORG-01 (bus de señales) — es dependencia
2. Crear `diagnosticador.py` y `buscador.py`
3. Añadir endpoints al router
4. Modificar cron.py
5. Deploy
6. Ejecutar TEST 1 → TEST 2 → TEST 3 → TEST 4
