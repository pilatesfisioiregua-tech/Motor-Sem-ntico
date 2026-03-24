# B-ORG-03: Vigía + Mecánico + Autófago (Goma META)

**Fecha:** 22 marzo 2026
**Objetivo:** Crear la Goma META completa: el sistema se vigila (Vigía), se repara (Mecánico) y se poda (Autófago). F3 Depuración aplicada al propio organismo. P30: come tu propia comida primero.
**Depende de:** B-ORG-01+02 (bus de señales + diagnosticador)
**Archivos a CREAR:** 3 nuevos (vigia.py + mecanico.py + autofago.py)
**Archivos a MODIFICAR:** 2 (cron.py + router.py)
**Tiempo estimado:** 40-50 min

**NOTA:** watchdog.py y self_healing.py en agent/core/ NO se tocan. Son Code OS (psycopg2). Creamos equivalentes NUEVOS en src/pilates/ (asyncpg) conectados al bus unificado.

---

## PASO 1: Crear src/pilates/vigia.py

**Crear archivo:** `src/pilates/vigia.py`

```python
"""Vigía — Agente META: monitoriza salud del sistema cada 15 min.

Ejecuta health checks ligeros y emite ALERTA al bus cuando detecta problemas.

Checks:
  1. DB conectividad
  2. Tablas om_* existen
  3. Bus: acumulación de pendientes >2h
  4. ACD: antigüedad último diagnóstico
  5. Cobros: cargos pendientes > umbral
  6. Clientes: hay clientes activos
"""
from __future__ import annotations

import structlog
from dataclasses import dataclass
from datetime import datetime, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "VIGIA"


@dataclass
class CheckResult:
    subsistema: str
    estado: str           # "ok", "warning", "error"
    mensaje: str
    severidad: str = "low"      # "low", "medium", "high", "critical"
    auto_fixable: bool = False
    fix_hint: str = ""


async def _check_db() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            r = await conn.fetchval("SELECT 1")
            if r == 1:
                return CheckResult("database", "ok", "Conexión OK")
        return CheckResult("database", "error", "SELECT 1 falló", "critical")
    except Exception as e:
        return CheckResult("database", "error", f"Sin conexión: {str(e)[:100]}", "critical")


async def _check_tables() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval(
                "SELECT count(*) FROM information_schema.tables WHERE table_name LIKE 'om_%'")
            if count >= 20:
                return CheckResult("tables", "ok", f"{count} tablas om_*")
            return CheckResult("tables", "warning", f"Solo {count} tablas om_* (esperadas >=20)", "medium")
    except Exception as e:
        return CheckResult("tables", "error", str(e)[:100], "high")


async def _check_bus_acumulacion() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            pendientes = await conn.fetchval("""
                SELECT count(*) FROM om_senales_agentes
                WHERE estado = 'pendiente' AND tenant_id = $1
                AND created_at < now() - interval '2 hours'
            """, TENANT)
            if pendientes is None:
                return CheckResult("bus", "ok", "Tabla bus no existe aún")
            if pendientes > 20:
                return CheckResult("bus", "warning",
                    f"{pendientes} señales pendientes >2h",
                    "medium", True, "Procesar o descartar señales antiguas del bus")
            return CheckResult("bus", "ok", f"{pendientes} señales antiguas pendientes")
    except Exception as e:
        return CheckResult("bus", "ok", f"Bus no disponible: {str(e)[:50]}")


async def _check_ultimo_diagnostico() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            ultimo = await conn.fetchval("""
                SELECT created_at FROM diagnosticos
                WHERE caso_input LIKE 'Diagnóstico autónomo%'
                ORDER BY created_at DESC LIMIT 1
            """)
            if not ultimo:
                return CheckResult("acd", "warning", "Nunca se ha ejecutado diagnóstico ACD",
                    "low", True, "Ejecutar POST /pilates/acd/diagnosticar-tenant")
            dias = (datetime.now(timezone.utc) - ultimo).days
            if dias > 10:
                return CheckResult("acd", "warning",
                    f"Último diagnóstico hace {dias} días",
                    "medium", True, "Ejecutar POST /pilates/acd/diagnosticar-tenant")
            return CheckResult("acd", "ok", f"Último diagnóstico hace {dias} días")
    except Exception as e:
        return CheckResult("acd", "ok", f"Tabla diagnosticos no disponible: {str(e)[:50]}")


async def _check_cobros_pendientes() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            deuda = await conn.fetchval("""
                SELECT COALESCE(sum(total), 0) FROM om_cargos
                WHERE tenant_id = $1 AND estado = 'pendiente'
            """, TENANT) or 0
            deuda = float(deuda)
            if deuda > 2000:
                return CheckResult("cobros", "warning", f"€{deuda:.0f} en cargos pendientes", "high")
            if deuda > 500:
                return CheckResult("cobros", "warning", f"€{deuda:.0f} en cargos pendientes", "medium")
            return CheckResult("cobros", "ok", f"€{deuda:.0f} pendiente")
    except Exception as e:
        return CheckResult("cobros", "ok", f"Sin datos cobros: {str(e)[:50]}")


async def _check_clientes_activos() -> CheckResult:
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            activos = await conn.fetchval("""
                SELECT count(*) FROM om_cliente_tenant
                WHERE tenant_id = $1 AND estado = 'activo'
            """, TENANT) or 0
            if activos == 0:
                return CheckResult("clientes", "warning", "0 clientes activos", "high")
            return CheckResult("clientes", "ok", f"{activos} clientes activos")
    except Exception as e:
        return CheckResult("clientes", "ok", str(e)[:50])


async def ejecutar_checks() -> list[CheckResult]:
    """Ejecuta TODOS los health checks."""
    return [
        await _check_db(),
        await _check_tables(),
        await _check_bus_acumulacion(),
        await _check_ultimo_diagnostico(),
        await _check_cobros_pendientes(),
        await _check_clientes_activos(),
    ]


async def vigilar() -> dict:
    """Ejecuta checks + emite ALERTAs al bus para los que fallan."""
    checks = await ejecutar_checks()
    problemas = [c for c in checks if c.estado in ("warning", "error")]

    alertas_emitidas = 0
    for p in problemas:
        try:
            from src.pilates.bus import emitir
            await emitir(
                "ALERTA", ORIGEN,
                {
                    "subsistema": p.subsistema,
                    "estado": p.estado,
                    "mensaje": p.mensaje,
                    "severidad": p.severidad,
                    "auto_fixable": p.auto_fixable,
                    "fix_hint": p.fix_hint,
                },
                destino="MECANICO",
                prioridad=2 if p.severidad == "critical" else 3 if p.severidad == "high" else 5,
            )
            alertas_emitidas += 1
        except Exception as e:
            log.warning("vigia_bus_error", subsistema=p.subsistema, error=str(e))

    resultado = {
        "checks_total": len(checks),
        "ok": len([c for c in checks if c.estado == "ok"]),
        "warnings": len([c for c in checks if c.estado == "warning"]),
        "errors": len([c for c in checks if c.estado == "error"]),
        "alertas_emitidas": alertas_emitidas,
        "detalle": [{"subsistema": c.subsistema, "estado": c.estado, "mensaje": c.mensaje}
                    for c in checks],
    }

    level = "vigia_ok" if not problemas else "vigia_alerta"
    log.info(level, ok=resultado["ok"], warn=resultado["warnings"], err=resultado["errors"])
    return resultado
```

---

## PASO 2: Crear src/pilates/mecanico.py

**Crear archivo:** `src/pilates/mecanico.py`

```python
"""Mecánico — Agente META: procesa ALERTAs del Vigía, clasifica y actúa.

FONTANERÍA: auto-fix (limpiar bus, disparar ACD, etc.)
ARQUITECTURAL: registra en om_mejoras_pendientes para CR1.

Componentes protegidos (siempre ARQUITECTURAL):
  pipeline, orchestrator, tcf, diagnostico, prescriptor, motor_vn, database
"""
from __future__ import annotations

import json
import structlog

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "MECANICO"

PROTEGIDOS = {
    "pipeline", "orchestrator", "tcf", "diagnostico",
    "prescriptor", "motor_vn", "database",
}


def clasificar(alerta: dict) -> str:
    """Clasifica alerta como FONTANERIA o ARQUITECTURAL."""
    subsistema = alerta.get("subsistema", "")
    severidad = alerta.get("severidad", "medium")
    auto_fixable = alerta.get("auto_fixable", False)

    if subsistema in PROTEGIDOS:
        return "ARQUITECTURAL"
    if severidad == "critical":
        return "ARQUITECTURAL"
    if auto_fixable:
        return "FONTANERIA"
    return "ARQUITECTURAL"


async def _ensure_mejoras_table():
    """Crea tabla om_mejoras_pendientes si no existe."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS om_mejoras_pendientes (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMPTZ DEFAULT now(),
                tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
                tipo TEXT NOT NULL CHECK (tipo IN ('FONTANERIA', 'ARQUITECTURAL', 'AUTOFAGIA')),
                estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado IN ('pendiente', 'aprobada', 'rechazada', 'completada')),
                origen TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                senal_id TEXT,
                metadata JSONB DEFAULT '{}'
            )
        """)


async def _fix_bus_acumulacion() -> dict:
    """Fix: marcar como error señales pendientes >24h."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = 'MECANICO',
                procesada_at = now(), error_detalle = 'Expirada por antigüedad (>24h)'
            WHERE estado = 'pendiente' AND tenant_id = $1
            AND created_at < now() - interval '24 hours'
        """, TENANT)
    count = int(result.split()[-1]) if result else 0
    return {"accion": "bus_limpiado", "expiradas": count}


async def _fix_diagnostico_ausente() -> dict:
    """Fix: disparar diagnóstico ACD."""
    try:
        from src.pilates.diagnosticador import diagnosticar_tenant
        diag = await diagnosticar_tenant()
        return {"accion": "acd_ejecutado", "estado": diag.get("estado")}
    except Exception as e:
        return {"accion": "acd_fallido", "error": str(e)[:200]}


async def _auto_fix(alerta: dict) -> dict:
    """Intenta auto-fix para alertas FONTANERIA."""
    subsistema = alerta.get("subsistema", "")
    if subsistema == "bus":
        return await _fix_bus_acumulacion()
    if subsistema == "acd":
        return await _fix_diagnostico_ausente()
    return {"accion": "sin_fix_auto", "subsistema": subsistema,
            "nota": "Marcada como procesada. Revisar si persiste."}


async def _registrar_mejora(tipo: str, origen: str, descripcion: str,
                            senal_id: str = None, metadata: dict = None) -> str:
    """Registra mejora pendiente. Devuelve UUID."""
    await _ensure_mejoras_table()
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_mejoras_pendientes (tenant_id, tipo, origen, descripcion, senal_id, metadata)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb)
            RETURNING id
        """, TENANT, tipo, origen, descripcion, senal_id,
            json.dumps(metadata or {}))
    return str(row["id"])


async def procesar_alertas() -> dict:
    """Lee ALERTAs pendientes del bus y las procesa."""
    from src.pilates.bus import leer_pendientes, marcar_procesada, marcar_error

    alertas = await leer_pendientes(destino="MECANICO", tipo="ALERTA", limite=20)

    fixes = []
    arquitecturales = []
    errores = []

    for señal in alertas:
        señal_id = str(señal["id"])
        payload = señal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        try:
            clase = clasificar(payload)

            if clase == "FONTANERIA":
                fix = await _auto_fix(payload)
                fixes.append({"señal_id": señal_id, **fix})
                await marcar_procesada(señal_id, ORIGEN)
            else:
                mejora_id = await _registrar_mejora(
                    "ARQUITECTURAL", ORIGEN,
                    payload.get("mensaje", "Sin descripción"),
                    señal_id, payload)
                arquitecturales.append({"señal_id": señal_id, "mejora_id": mejora_id,
                    "subsistema": payload.get("subsistema")})
                await marcar_procesada(señal_id, ORIGEN)
                log.warning("mecanico_arquitectural",
                    subsistema=payload.get("subsistema"),
                    mensaje=payload.get("mensaje"))

        except Exception as e:
            errores.append({"señal_id": señal_id, "error": str(e)[:200]})
            await marcar_error(señal_id, ORIGEN, str(e)[:500])

    resultado = {
        "alertas_procesadas": len(alertas),
        "fixes_fontaneria": len(fixes),
        "arquitecturales": len(arquitecturales),
        "errores": len(errores),
        "detalle_fixes": fixes,
        "detalle_arquitectural": arquitecturales,
    }

    if alertas:
        log.info("mecanico_procesado",
            total=len(alertas), fixes=len(fixes), arq=len(arquitecturales))

    return resultado
```

---

## PASO 3: Crear src/pilates/autofago.py

**Crear archivo:** `src/pilates/autofago.py`

```python
"""Autófago — Agente F3: el sistema se poda a sí mismo.

F3 Depuración aplicada al propio organismo.
P30: "Come tu propia comida primero."

3 niveles de autofagia:
  Nivel 1 — Código muerto (ast + imports): funciones sin llamar, archivos sin referencia
  Nivel 2 — Datos caducados (SQL): señales antiguas, diagnósticos viejos, logs obsoletos
  Nivel 3 — Conceptual: archivos sospechosos de obsolescencia por nombre/contexto

REGLA DE ORO: El Autófago DETECTA y PROPONE, nunca borra solo.
Todo se registra en om_mejoras_pendientes con tipo='AUTOFAGIA' para CR1.

Ejecución: mensual (día 1), o manual vía endpoint.
"""
from __future__ import annotations

import ast
import json
import os
import structlog
from datetime import datetime, timezone
from pathlib import Path

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AUTOFAGO"

# Raíz del código a escanear
SRC_ROOT = Path(__file__).parent.parent  # src/

# Archivos que sabemos obsoletos o sospechosos (patrón: nombre sugiere tecnología abandonada)
PATRONES_SOSPECHOSOS = {
    "stripe_pagos.py": "Pagos migrados a Redsys/Caja Rural. Stripe no se usa.",
}

# Archivos protegidos que NUNCA se proponen para eliminar
ARCHIVOS_PROTEGIDOS = {
    "__init__.py", "main.py", "settings.py", "schema.sql", "seed.sql",
    "client.py", "router.py", "cron.py", "orchestrator.py",
}


def _escanear_funciones_definidas(ruta: Path) -> list[dict]:
    """Usa ast para encontrar funciones/clases definidas en un archivo .py."""
    try:
        source = ruta.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(ruta))
    except Exception:
        return []

    definiciones = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Saltar métodos privados y dunder
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            definiciones.append({
                "nombre": node.name,
                "tipo": "function",
                "linea": node.lineno,
                "archivo": str(ruta.relative_to(SRC_ROOT)),
            })
        elif isinstance(node, ast.ClassDef):
            definiciones.append({
                "nombre": node.name,
                "tipo": "class",
                "linea": node.lineno,
                "archivo": str(ruta.relative_to(SRC_ROOT)),
            })
    return definiciones


def _buscar_referencias(nombre: str, archivos: list[Path], archivo_origen: Path) -> int:
    """Cuenta cuántos archivos (distintos al origen) mencionan este nombre."""
    refs = 0
    for f in archivos:
        if f == archivo_origen:
            continue
        try:
            contenido = f.read_text(encoding="utf-8")
            if nombre in contenido:
                refs += 1
        except Exception:
            continue
    return refs


def escanear_codigo_muerto() -> list[dict]:
    """Nivel 1: Detecta funciones/clases definidas pero nunca referenciadas desde otro archivo.

    SOLO reporta funciones públicas (no _ prefijo) sin referencias externas.
    NO propone eliminar nada protegido.
    """
    # Recopilar todos los .py en src/
    archivos_py = list(SRC_ROOT.rglob("*.py"))
    archivos_py = [f for f in archivos_py if "__pycache__" not in str(f)]

    # Encontrar todas las definiciones
    todas_defs = []
    for f in archivos_py:
        todas_defs.extend(_escanear_funciones_definidas(f))

    # Filtrar: solo funciones públicas (no empiezan con _)
    publicas = [d for d in todas_defs if not d["nombre"].startswith("_")]

    # Buscar cuáles no tienen referencias externas
    huerfanas = []
    for defn in publicas:
        archivo_origen = SRC_ROOT / defn["archivo"]
        if archivo_origen.name in ARCHIVOS_PROTEGIDOS:
            continue

        refs = _buscar_referencias(defn["nombre"], archivos_py, archivo_origen)
        if refs == 0:
            huerfanas.append({
                **defn,
                "referencias_externas": 0,
                "razon": f"{defn['tipo']} '{defn['nombre']}' en {defn['archivo']}:{defn['linea']} — 0 referencias externas",
            })

    return huerfanas


def escanear_archivos_sospechosos() -> list[dict]:
    """Nivel 1b: Detecta archivos con nombre que sugiere obsolescencia."""
    resultados = []
    for f in SRC_ROOT.rglob("*.py"):
        if f.name in PATRONES_SOSPECHOSOS:
            resultados.append({
                "archivo": str(f.relative_to(SRC_ROOT)),
                "nombre": f.name,
                "razon": PATRONES_SOSPECHOSOS[f.name],
                "tipo": "archivo_sospechoso",
            })
    return resultados


async def escanear_datos_caducados() -> list[dict]:
    """Nivel 2: Detecta datos viejos que ocupan espacio sin valor.

    - Señales bus >30 días procesadas/error
    - Diagnósticos >180 días
    - Ejecuciones motor >90 días
    """
    resultados = []
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Señales procesadas antiguas
        try:
            senales_viejas = await conn.fetchval("""
                SELECT count(*) FROM om_senales_agentes
                WHERE estado IN ('procesada', 'error')
                AND created_at < now() - interval '30 days'
                AND tenant_id = $1
            """, TENANT)
            if senales_viejas and senales_viejas > 50:
                resultados.append({
                    "tipo": "datos_caducados",
                    "tabla": "om_senales_agentes",
                    "registros": senales_viejas,
                    "razon": f"{senales_viejas} señales procesadas/error >30 días. Propongo DELETE.",
                    "sql_propuesto": "DELETE FROM om_senales_agentes WHERE estado IN ('procesada','error') AND created_at < now() - interval '30 days'",
                })
        except Exception:
            pass

        # Diagnósticos muy antiguos
        try:
            diags_viejos = await conn.fetchval("""
                SELECT count(*) FROM diagnosticos
                WHERE created_at < now() - interval '180 days'
            """)
            if diags_viejos and diags_viejos > 20:
                resultados.append({
                    "tipo": "datos_caducados",
                    "tabla": "diagnosticos",
                    "registros": diags_viejos,
                    "razon": f"{diags_viejos} diagnósticos >180 días. Propongo archivar o eliminar.",
                })
        except Exception:
            pass

        # Ejecuciones motor antiguas
        try:
            exec_viejas = await conn.fetchval("""
                SELECT count(*) FROM ejecuciones
                WHERE created_at < now() - interval '90 days'
            """)
            if exec_viejas and exec_viejas > 100:
                resultados.append({
                    "tipo": "datos_caducados",
                    "tabla": "ejecuciones",
                    "registros": exec_viejas,
                    "razon": f"{exec_viejas} ejecuciones motor >90 días. Propongo archivar.",
                })
        except Exception:
            pass

        # Mejoras completadas/rechazadas antiguas
        try:
            mejoras_cerradas = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado IN ('completada', 'rechazada')
                AND created_at < now() - interval '60 days'
            """)
            if mejoras_cerradas and mejoras_cerradas > 10:
                resultados.append({
                    "tipo": "datos_caducados",
                    "tabla": "om_mejoras_pendientes",
                    "registros": mejoras_cerradas,
                    "razon": f"{mejoras_cerradas} mejoras cerradas >60 días. Propongo DELETE.",
                })
        except Exception:
            pass

    return resultados


async def ejecutar_autofagia() -> dict:
    """Ejecuta los 3 niveles de autofagia y registra propuestas.

    NO borra nada. Solo detecta y registra en om_mejoras_pendientes.
    """
    log.info("autofago_inicio")

    # Nivel 1: Código muerto
    codigo_muerto = escanear_codigo_muerto()
    archivos_sospechosos = escanear_archivos_sospechosos()

    # Nivel 2: Datos caducados
    datos_caducados = await escanear_datos_caducados()

    # Registrar todo en om_mejoras_pendientes
    from src.pilates.mecanico import _registrar_mejora

    propuestas_registradas = 0

    # Agrupar código muerto por archivo (no una mejora por función)
    from collections import defaultdict
    por_archivo = defaultdict(list)
    for item in codigo_muerto:
        por_archivo[item["archivo"]].append(item["nombre"])

    for archivo, funciones in por_archivo.items():
        # Máximo 10 funciones huérfanas por archivo para que el informe sea legible
        muestra = funciones[:10]
        extras = f" (+{len(funciones)-10} más)" if len(funciones) > 10 else ""
        desc = f"CÓDIGO MUERTO en {archivo}: {', '.join(muestra)}{extras} — 0 referencias externas. Revisar si son públicas API o realmente muertas."
        await _registrar_mejora("AUTOFAGIA", ORIGEN, desc, metadata={
            "nivel": 1, "subtipo": "codigo_muerto",
            "archivo": archivo, "funciones": funciones[:20],
        })
        propuestas_registradas += 1

    for item in archivos_sospechosos:
        desc = f"ARCHIVO OBSOLETO: {item['archivo']} — {item['razon']}"
        await _registrar_mejora("AUTOFAGIA", ORIGEN, desc, metadata={
            "nivel": 1, "subtipo": "archivo_sospechoso", **item,
        })
        propuestas_registradas += 1

    for item in datos_caducados:
        desc = f"DATOS CADUCADOS en {item['tabla']}: {item['razon']}"
        await _registrar_mejora("AUTOFAGIA", ORIGEN, desc, metadata={
            "nivel": 2, "subtipo": "datos_caducados", **item,
        })
        propuestas_registradas += 1

    # Emitir señal resumen al bus
    try:
        from src.pilates.bus import emitir
        await emitir(
            "ACCION", ORIGEN,
            {
                "codigo_muerto_archivos": len(por_archivo),
                "codigo_muerto_funciones": len(codigo_muerto),
                "archivos_sospechosos": len(archivos_sospechosos),
                "datos_caducados": len(datos_caducados),
                "propuestas_registradas": propuestas_registradas,
            },
            prioridad=8,  # Baja prioridad — es informativo
        )
    except Exception as e:
        log.warning("autofago_bus_error", error=str(e))

    resultado = {
        "codigo_muerto": {
            "archivos_afectados": len(por_archivo),
            "funciones_huerfanas": len(codigo_muerto),
            "detalle": [{
                "archivo": arch,
                "funciones": funcs[:5],
                "total": len(funcs),
            } for arch, funcs in list(por_archivo.items())[:10]],
        },
        "archivos_sospechosos": archivos_sospechosos,
        "datos_caducados": datos_caducados,
        "propuestas_registradas": propuestas_registradas,
    }

    log.info("autofago_completo",
        muertos=len(codigo_muerto),
        sospechosos=len(archivos_sospechosos),
        caducados=len(datos_caducados),
        propuestas=propuestas_registradas)

    return resultado
```

---

## PASO 4: Modificar cron.py — vigía cada 15 min + autófago mensual

**Archivo:** `src/pilates/cron.py`

**IMPORTANTE:** Este briefing asume que B-ORG-01+02 ya fue deployado y cron.py ya tiene los pasos 3 y 4 (diagnosticador + buscador) en `_tarea_semanal()`.

### 4.1 — Añadir tarea mensual después de `_tarea_semanal`:

Buscar EXACTAMENTE:
```python
    except Exception as e:
        log.error("cron_semanal_error", error=str(e))
```

DESPUÉS de este bloque, añadir:

```python


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
```

### 4.2 — Añadir vigía + mecánico + mensual al loop

Buscar EXACTAMENTE:
```python
        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
```

Reemplazar por:
```python
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
```

---

## PASO 5: Añadir endpoints a router.py

**Archivo:** `src/pilates/router.py`

Buscar EXACTAMENTE (al final del archivo, después del último endpoint añadido por B-ORG-01+02):
```python
@router.post("/acd/buscar-por-gaps")
async def acd_buscar_por_gaps():
    """Busca información dirigida por gaps ACD vía Perplexity."""
    from src.pilates.buscador import buscar_por_gaps
    return await buscar_por_gaps()
```

DESPUÉS de este bloque, añadir:

```python


# ============================================================
# VIGÍA + MECÁNICO + AUTÓFAGO — Goma META del organismo
# ============================================================

@router.post("/sistema/vigilar")
async def sistema_vigilar():
    """Ejecuta health checks del Vigía. Emite ALERTAs al bus."""
    from src.pilates.vigia import vigilar
    return await vigilar()


@router.post("/sistema/mecanico")
async def sistema_mecanico():
    """Ejecuta el Mecánico: procesa ALERTAs pendientes."""
    from src.pilates.mecanico import procesar_alertas
    return await procesar_alertas()


@router.post("/sistema/autofagia")
async def sistema_autofagia():
    """Ejecuta autofagia: detecta código muerto, datos caducados, archivos obsoletos.
    NO borra nada. Solo registra propuestas en om_mejoras_pendientes."""
    from src.pilates.autofago import ejecutar_autofagia
    return await ejecutar_autofagia()


@router.get("/sistema/estado")
async def sistema_estado():
    """Estado completo del sistema: checks + bus + diagnóstico + mejoras pendientes."""
    from src.pilates.vigia import ejecutar_checks
    from src.pilates.bus import contar_pendientes

    checks = await ejecutar_checks()
    bus = await contar_pendientes()

    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        ultimo_diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, created_at FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        mejoras_pend = 0
        try:
            mejoras_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception:
            pass

        autofagia_pend = 0
        try:
            autofagia_pend = await conn.fetchval("""
                SELECT count(*) FROM om_mejoras_pendientes
                WHERE estado = 'pendiente' AND tipo = 'AUTOFAGIA' AND tenant_id = 'authentic_pilates'
            """) or 0
        except Exception:
            pass

    return {
        "health": [{"subsistema": c.subsistema, "estado": c.estado, "mensaje": c.mensaje}
                   for c in checks],
        "bus_pendientes": bus,
        "ultimo_diagnostico": {
            "estado": ultimo_diag["estado_pre"] if ultimo_diag else None,
            "lentes": ultimo_diag["lentes_pre"] if ultimo_diag else None,
            "fecha": str(ultimo_diag["created_at"])[:10] if ultimo_diag else None,
        } if ultimo_diag else None,
        "mejoras_arquitecturales_pendientes": mejoras_pend,
        "propuestas_autofagia_pendientes": autofagia_pend,
    }


@router.get("/sistema/mejoras")
async def sistema_mejoras(
    estado: Optional[str] = "pendiente",
    tipo: Optional[str] = None,
    limite: int = Query(default=30, le=100),
):
    """Lista mejoras pendientes (ARQUITECTURAL + AUTOFAGIA). Para revisión CR1."""
    pool = await _get_pool()
    conditions = ["tenant_id = $1"]
    params: list = [TENANT]
    idx = 2

    if estado:
        conditions.append(f"estado = ${idx}")
        params.append(estado)
        idx += 1

    if tipo:
        conditions.append(f"tipo = ${idx}")
        params.append(tipo)
        idx += 1

    where = " AND ".join(conditions)
    params.append(limite)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT id, created_at, tipo, estado, origen, descripcion, metadata
            FROM om_mejoras_pendientes
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx}
        """, *params)

    return [_row_to_dict(r) for r in rows]


@router.patch("/sistema/mejoras/{mejora_id}")
async def sistema_mejora_decidir(
    mejora_id: UUID,
    decision: str = Query(..., pattern="^(aprobada|rechazada|completada)$"),
):
    """CR1: Aprobar, rechazar o completar una mejora pendiente."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_mejoras_pendientes SET estado = $1
            WHERE id = $2 AND tenant_id = $3
        """, decision, mejora_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Mejora no encontrada")

    log.info("mejora_decidida", id=str(mejora_id), decision=decision)
    return {"status": decision, "id": str(mejora_id)}
```

---

## PASO 6: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

---

## TESTS — Ejecutar en orden tras deploy

### TEST 1: Vigía manual
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/vigilar \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = d.get('checks_total', 0) >= 5 and d.get('ok', 0) > 0
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 2: Estado del sistema
```bash
curl -s https://motor-semantico-omni.fly.dev/pilates/sistema/estado \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = 'health' in d and len(d['health']) >= 5
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 3: Mecánico procesa
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/mecanico \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('PASS' if 'alertas_procesadas' in d else 'FAIL:', d)"
```

### TEST 4: Vigía → Mecánico end-to-end
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/bus/emitir \
  -H 'Content-Type: application/json' \
  -d '{"tipo":"ALERTA","origen":"TEST","destino":"MECANICO","prioridad":3,"payload":{"subsistema":"test","estado":"warning","mensaje":"Test alerta fake","severidad":"low","auto_fixable":true,"fix_hint":"nada"}}' \
  > /dev/null

curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/mecanico \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = d.get('alertas_procesadas', 0) >= 1
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 5: Autofagia
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/autofagia \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = 'codigo_muerto' in d and 'archivos_sospechosos' in d and 'propuestas_registradas' in d
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok:
    print(f'  Funciones huérfanas: {d[\"codigo_muerto\"][\"funciones_huerfanas\"]}')
    print(f'  Archivos sospechosos: {len(d[\"archivos_sospechosos\"])}')
    print(f'  Datos caducados: {len(d[\"datos_caducados\"])}')
    print(f'  Propuestas registradas: {d[\"propuestas_registradas\"]}')"
```

### TEST 6: Ver mejoras pendientes (incluye autofagia)
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/sistema/mejoras?tipo=AUTOFAGIA&limite=5' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('PASS' if isinstance(d, list) else 'FAIL:', d)
if isinstance(d, list) and d:
    print(f'  Primera propuesta: {d[0].get(\"descripcion\", \"\")[:100]}...')"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1-5 devuelven PASS.** Test 6 es informativo (verifica que las propuestas se persisten).

**FAIL = Cualquier test 1-5 devuelve FAIL.** Revisar logs con `fly logs -a chief-os-omni`.
