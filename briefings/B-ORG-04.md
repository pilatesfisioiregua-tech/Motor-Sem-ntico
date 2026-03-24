# B-ORG-04: Propiocepción — El organismo se conoce a sí mismo

**Fecha:** 22 marzo 2026
**Objetivo:** El organismo mide su PROPIO funcionamiento. No la salud del negocio (eso es ACD/Vigía) sino la salud del sistema: ¿fluyen las señales? ¿responden los agentes? ¿hay drift en el diagnóstico? ¿cuánto cuesta operar? P30 al nivel más profundo.
**Depende de:** B-ORG-01+02 (bus) + B-ORG-03 (vigía/mecánico)
**Archivos a CREAR:** 2 (migración + propiocepcion.py)
**Archivos a MODIFICAR:** 2 (cron.py + router.py)
**Tiempo estimado:** 25-35 min

**Distinción clave:**
- **Vigía** = "¿el negocio está sano?" (DB, cobros, clientes) → detecta FALLOS
- **Propiocepción** = "¿el organismo funciona bien?" (señales, agentes, drift, coste) → mide RENDIMIENTO

---

## PASO 1: Migración — tabla om_telemetria_sistema

**Crear archivo:** `migrations/019_telemetria_sistema.sql`

```sql
-- =================================================================
-- Migration 019: Telemetría del organismo
-- Snapshots periódicos del rendimiento del sistema nervioso.
-- =================================================================

CREATE TABLE IF NOT EXISTS om_telemetria_sistema (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    periodo TEXT NOT NULL,                -- 'diario', 'semanal'

    -- Bus de señales
    senales_emitidas INTEGER DEFAULT 0,
    senales_procesadas INTEGER DEFAULT 0,
    senales_error INTEGER DEFAULT 0,
    senales_pendientes INTEGER DEFAULT 0,
    latencia_media_min FLOAT,             -- minutos entre creación y procesamiento

    -- Agentes: conteo de señales por origen
    actividad_agentes JSONB DEFAULT '{}', -- {"OBSERVADOR": 12, "AF1": 3, "VIGIA": 96, ...}
    agentes_silenciosos TEXT[],           -- agentes que no emitieron en el periodo

    -- ACD drift
    acd_estado TEXT,                      -- último estado diagnóstico
    acd_lentes JSONB,                     -- {salud, sentido, continuidad}
    acd_delta_lentes JSONB,               -- delta vs snapshot anterior {salud: +0.05, ...}

    -- Mecánico
    fixes_fontaneria INTEGER DEFAULT 0,
    mejoras_arquitecturales INTEGER DEFAULT 0,
    propuestas_autofagia INTEGER DEFAULT 0,

    -- Operativo
    endpoints_llamados JSONB DEFAULT '{}', -- si tenemos logs de acceso
    errores_500 INTEGER DEFAULT 0,

    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_telemetria_periodo
    ON om_telemetria_sistema(periodo, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_telemetria_tenant
    ON om_telemetria_sistema(tenant_id, created_at DESC);
```

---

## PASO 2: Crear src/pilates/propiocepcion.py

**Crear archivo:** `src/pilates/propiocepcion.py`

```python
"""Propiocepción — El organismo mide su propio funcionamiento.

Vigía pregunta: "¿el negocio está sano?"
Propiocepción pregunta: "¿el organismo funciona bien?"

Métricas:
  1. Throughput del bus: señales emitidas/procesadas/error por periodo
  2. Actividad de agentes: quién emite, quién calla
  3. Latencia: tiempo medio entre emisión y procesamiento
  4. ACD drift: cambio en lentes respecto al snapshot anterior
  5. Mecánico: fixes y mejoras acumuladas
  6. Agentes silenciosos: los que deberían emitir pero no lo hacen

Ejecución: snapshot diario + resumen semanal.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Agentes que esperamos que emitan al menos una señal por semana
AGENTES_ESPERADOS = {
    "OBSERVADOR",   # Cada CRUD → señal DATO
    "VIGIA",        # Cada 15 min → señal ALERTA si hay problemas
    "DIAGNOSTICADOR",  # Semanal → señal DIAGNOSTICO
    "MECANICO",     # Reactivo → procesa ALERTAs
}


async def _metricas_bus(desde: datetime) -> dict:
    """Métricas del bus de señales desde una fecha."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Conteos por estado
        stats = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE estado = 'procesada') as procesadas,
                count(*) FILTER (WHERE estado = 'error') as errores,
                count(*) FILTER (WHERE estado = 'pendiente') as pendientes
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
        """, TENANT, desde)

        # Latencia media (solo procesadas)
        latencia = await conn.fetchval("""
            SELECT AVG(EXTRACT(EPOCH FROM (procesada_at - created_at)) / 60.0)
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND estado = 'procesada'
            AND created_at >= $2 AND procesada_at IS NOT NULL
        """, TENANT, desde)

        # Actividad por agente (origen)
        agentes_rows = await conn.fetch("""
            SELECT origen, count(*) as n
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
            GROUP BY origen ORDER BY n DESC
        """, TENANT, desde)

    actividad = {r["origen"]: r["n"] for r in agentes_rows}
    agentes_activos = set(actividad.keys())
    silenciosos = sorted(AGENTES_ESPERADOS - agentes_activos)

    return {
        "emitidas": stats["total"] or 0,
        "procesadas": stats["procesadas"] or 0,
        "errores": stats["errores"] or 0,
        "pendientes": stats["pendientes"] or 0,
        "latencia_media_min": round(float(latencia), 2) if latencia else None,
        "actividad_agentes": actividad,
        "agentes_silenciosos": silenciosos,
    }


async def _metricas_acd() -> dict:
    """Estado ACD actual + delta vs anterior."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        ultimos = await conn.fetch("""
            SELECT estado_pre, lentes_pre, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 2
        """)

    if not ultimos:
        return {"estado": None, "lentes": None, "delta": None}

    actual = ultimos[0]
    lentes_actual = actual["lentes_pre"]
    if isinstance(lentes_actual, str):
        lentes_actual = json.loads(lentes_actual)

    delta = None
    if len(ultimos) > 1:
        lentes_anterior = ultimos[1]["lentes_pre"]
        if isinstance(lentes_anterior, str):
            lentes_anterior = json.loads(lentes_anterior)
        delta = {
            k: round(lentes_actual.get(k, 0) - lentes_anterior.get(k, 0), 3)
            for k in ["salud", "sentido", "continuidad"]
        }

    return {
        "estado": actual["estado_pre"],
        "lentes": lentes_actual,
        "delta": delta,
        "fecha": str(actual["created_at"])[:10],
    }


async def _metricas_mecanico(desde: datetime) -> dict:
    """Conteo de fixes y mejoras en el periodo."""
    pool = await get_pool()
    resultado = {"fixes_fontaneria": 0, "arquitecturales": 0, "autofagia": 0}

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch("""
                SELECT tipo, count(*) as n
                FROM om_mejoras_pendientes
                WHERE tenant_id = $1 AND created_at >= $2
                GROUP BY tipo
            """, TENANT, desde)
            for r in rows:
                if r["tipo"] == "FONTANERIA":
                    resultado["fixes_fontaneria"] = r["n"]
                elif r["tipo"] == "ARQUITECTURAL":
                    resultado["arquitecturales"] = r["n"]
                elif r["tipo"] == "AUTOFAGIA":
                    resultado["autofagia"] = r["n"]
        except Exception:
            pass

    return resultado


async def snapshot(periodo: str = "diario") -> dict:
    """Genera y persiste un snapshot de telemetría del organismo.

    Args:
        periodo: "diario" (últimas 24h) o "semanal" (últimos 7 días)
    """
    ahora = datetime.now(timezone.utc)
    desde = ahora - timedelta(days=1 if periodo == "diario" else 7)

    # Recopilar métricas
    bus = await _metricas_bus(desde)
    acd = await _metricas_acd()
    mecanico = await _metricas_mecanico(desde)

    # Persistir snapshot
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_telemetria_sistema (
                tenant_id, periodo,
                senales_emitidas, senales_procesadas, senales_error, senales_pendientes,
                latencia_media_min, actividad_agentes, agentes_silenciosos,
                acd_estado, acd_lentes, acd_delta_lentes,
                fixes_fontaneria, mejoras_arquitecturales, propuestas_autofagia
            ) VALUES (
                $1, $2,
                $3, $4, $5, $6,
                $7, $8::jsonb, $9,
                $10, $11::jsonb, $12::jsonb,
                $13, $14, $15
            )
        """, TENANT, periodo,
            bus["emitidas"], bus["procesadas"], bus["errores"], bus["pendientes"],
            bus["latencia_media_min"], json.dumps(bus["actividad_agentes"]), bus["agentes_silenciosos"],
            acd.get("estado"), json.dumps(acd.get("lentes")) if acd.get("lentes") else None,
            json.dumps(acd.get("delta")) if acd.get("delta") else None,
            mecanico["fixes_fontaneria"], mecanico["arquitecturales"], mecanico["autofagia"],
        )

    resultado = {
        "periodo": periodo,
        "desde": str(desde)[:19],
        "bus": bus,
        "acd": acd,
        "mecanico": mecanico,
        "alerta_drift": _evaluar_drift(acd),
        "alerta_silencio": bus["agentes_silenciosos"],
    }

    # Emitir alerta si hay drift significativo o agentes silenciosos
    alertas = []
    if resultado["alerta_drift"]:
        alertas.append(resultado["alerta_drift"])
    if bus["agentes_silenciosos"] and periodo == "semanal":
        alertas.append(f"Agentes silenciosos esta semana: {', '.join(bus['agentes_silenciosos'])}")

    if alertas:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "ALERTA", "PROPIOCEPCION",
                {
                    "tipo": "drift_o_silencio",
                    "alertas": alertas,
                    "periodo": periodo,
                    "bus_emitidas": bus["emitidas"],
                    "acd_estado": acd.get("estado"),
                },
                prioridad=6,
            )
        except Exception as e:
            log.warning("propiocepcion_bus_error", error=str(e))

    log.info(f"propiocepcion_{periodo}",
        señales=bus["emitidas"], silenciosos=len(bus["agentes_silenciosos"]),
        acd=acd.get("estado"), drift=resultado["alerta_drift"] is not None)

    return resultado


def _evaluar_drift(acd: dict) -> str | None:
    """Evalúa si hay drift significativo en las lentes ACD."""
    delta = acd.get("delta")
    if not delta:
        return None

    for lente, cambio in delta.items():
        if abs(cambio) > 0.15:
            direccion = "subió" if cambio > 0 else "bajó"
            return f"DRIFT: {lente} {direccion} {abs(cambio):.2f} respecto al diagnóstico anterior"

    return None


async def obtener_tendencia(n_snapshots: int = 10) -> list[dict]:
    """Devuelve los últimos N snapshots para visualizar tendencia."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT created_at, periodo, senales_emitidas, senales_procesadas,
                   senales_error, latencia_media_min, agentes_silenciosos,
                   acd_estado, acd_lentes, acd_delta_lentes,
                   fixes_fontaneria, mejoras_arquitecturales
            FROM om_telemetria_sistema
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, TENANT, n_snapshots)

    return [dict(r) for r in rows]
```

---

## PASO 3: Modificar cron.py — snapshot diario + semanal

**Archivo:** `src/pilates/cron.py`

### 3.1 — Añadir snapshot diario después de _tarea_diaria

Buscar EXACTAMENTE:
```python
async def _tarea_diaria():
    """Tarea diaria: escuchar señales de las 3 capas."""
    try:
        from src.pilates.voz_ciclos import escuchar
        result = await escuchar()
        log.info("cron_diaria_ok", senales=result.get("senales_creadas", 0))
    except Exception as e:
        log.error("cron_diaria_error", error=str(e))
```

Reemplazar por:
```python
async def _tarea_diaria():
    """Tarea diaria: escuchar señales + snapshot propiocepción."""
    try:
        from src.pilates.voz_ciclos import escuchar
        result = await escuchar()
        log.info("cron_diaria_ok", senales=result.get("senales_creadas", 0))
    except Exception as e:
        log.error("cron_diaria_error", error=str(e))

    # Propiocepción: snapshot diario
    try:
        from src.pilates.propiocepcion import snapshot
        snap = await snapshot("diario")
        log.info("cron_diaria_propiocepcion_ok",
            señales=snap["bus"]["emitidas"],
            silenciosos=len(snap["bus"]["agentes_silenciosos"]))
    except Exception as e:
        log.error("cron_diaria_propiocepcion_error", error=str(e))
```

### 3.2 — Añadir snapshot semanal al final de _tarea_semanal

Buscar EXACTAMENTE:
```python
        # 4. Búsqueda dirigida por gaps
        from src.pilates.buscador import buscar_por_gaps
        busq = await buscar_por_gaps()
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))
```

Reemplazar por:
```python
        # 4. Búsqueda dirigida por gaps
        from src.pilates.buscador import buscar_por_gaps
        busq = await buscar_por_gaps()
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))

        # 5. Propiocepción: snapshot semanal
        from src.pilates.propiocepcion import snapshot
        snap = await snapshot("semanal")
        log.info("cron_semanal_propiocepcion_ok",
            señales=snap["bus"]["emitidas"],
            drift=snap.get("alerta_drift") is not None)

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))
```

---

## PASO 4: Añadir endpoints a router.py

**Archivo:** `src/pilates/router.py`

Buscar el último endpoint de B-ORG-03 (al final del archivo). Después del último endpoint, añadir:

```python


# ============================================================
# PROPIOCEPCIÓN — El organismo se mide a sí mismo
# ============================================================

@router.post("/sistema/propiocepcion")
async def sistema_propiocepcion(periodo: str = Query(default="diario", pattern="^(diario|semanal)$")):
    """Genera snapshot de telemetría del organismo."""
    from src.pilates.propiocepcion import snapshot
    return await snapshot(periodo)


@router.get("/sistema/tendencia")
async def sistema_tendencia(n: int = Query(default=10, le=30)):
    """Últimos N snapshots de telemetría para visualizar tendencia."""
    from src.pilates.propiocepcion import obtener_tendencia
    snapshots = await obtener_tendencia(n)
    return {"snapshots": snapshots, "total": len(snapshots)}
```

---

## PASO 5: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

---

## TESTS

### TEST 1: Snapshot diario
```bash
curl -s -X POST 'https://motor-semantico-omni.fly.dev/pilates/sistema/propiocepcion?periodo=diario' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['periodo','bus','acd','mecanico','alerta_drift','alerta_silencio'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok:
    print(f'  Bus: {d[\"bus\"][\"emitidas\"]} emitidas, {d[\"bus\"][\"procesadas\"]} procesadas')
    print(f'  Latencia media: {d[\"bus\"][\"latencia_media_min\"]} min')
    print(f'  Agentes silenciosos: {d[\"bus\"][\"agentes_silenciosos\"]}')
    print(f'  ACD: {d[\"acd\"].get(\"estado\")}, drift={d[\"alerta_drift\"]}')"
```

### TEST 2: Snapshot semanal
```bash
curl -s -X POST 'https://motor-semantico-omni.fly.dev/pilates/sistema/propiocepcion?periodo=semanal' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = d.get('periodo') == 'semanal' and 'bus' in d
print('PASS' if ok else 'FAIL:', d)"
```

### TEST 3: Tendencia (debe haber al menos 1 snapshot del test 1)
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/sistema/tendencia?n=5' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = d.get('total', 0) >= 1
print('PASS' if ok else 'FAIL:', d)"
```

### TEST 4: /sistema/estado sigue funcionando
```bash
curl -s https://motor-semantico-omni.fly.dev/pilates/sistema/estado \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('PASS' if 'health' in d else 'FAIL:', d)"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1-4 devuelven PASS.**

**FAIL = Cualquier test devuelve FAIL.** Revisar logs con `fly logs -a chief-os-omni`.

---

## QUÉ MIDE VS QUÉ NO MIDE

| Mide (propiocepción) | NO mide (viene después) |
|---|---|
| Señales emitidas/procesadas/error | FOK/JOL (requiere calibración Kalman) |
| Latencia media del bus | SLOs formales con Circuit Breaker |
| Agentes silenciosos | Predicción de fallos (predictive_controller) |
| ACD drift entre diagnósticos | Coste LLM por agente (aún no hay LLM en AF) |
| Fixes del mecánico | Tool evolution (gaps de herramientas) |

Los componentes pesados de agent/core/ (metacognitive.py, monitoring.py, predictive_controller.py) se conectarán cuando haya suficiente telemetría acumulada para calibrarlos. Primero datos, después modelos.
