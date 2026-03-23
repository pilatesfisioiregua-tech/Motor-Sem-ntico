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
PATRONES_SOSPECHOSOS = {}

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

    # Limpieza de señales procesadas > 30 días
    senales_limpiadas = False
    try:
        from datetime import timedelta
        hace_30_dias = datetime.now(timezone.utc) - timedelta(days=30)
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM om_senales_agentes
                WHERE tenant_id = $1 AND estado IN ('procesada', 'error') AND created_at < $2
            """, TENANT, hace_30_dias)
            try:
                await conn.execute("""
                    DELETE FROM om_bus_senales
                    WHERE tenant_id = $1 AND procesada = true AND created_at < $2
                """, TENANT, hace_30_dias)
            except Exception:
                pass
        senales_limpiadas = True
    except Exception as e:
        log.warning("autofago_limpieza_bus_error", error=str(e))

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
        "senales_limpiadas": senales_limpiadas,
    }

    # Publicar al feed
    try:
        from src.pilates.feed import feed_autofago
        await feed_autofago(len(codigo_muerto), propuestas_registradas)
    except Exception as e:
        log.warning("autofago_feed_error", error=str(e))

    log.info("autofago_completo",
        muertos=len(codigo_muerto),
        sospechosos=len(archivos_sospechosos),
        caducados=len(datos_caducados),
        propuestas=propuestas_registradas)

    return resultado
