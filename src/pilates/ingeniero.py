"""Ingeniero — Las manos del organismo. Registra cambios de código.

El ÚNICO agente que puede proponer modificaciones al codebase.
Se dispara por instrucciones del Meta-Cognitivo, alertas del Vigía,
o cristalizaciones.

NIVELES DE SEGURIDAD:
  safe:        genera briefing_micro → emite al bus (backup + test)
  moderado:    registra como pendiente CR1
  estructural: registra como pendiente CR1 + briefing
  prohibido:   NUNCA ejecuta

PRINCIPIO: "Un organismo que puede modificar su propio código
es un organismo que puede evolucionar. Pero un organismo que
modifica su código sin control puede autodestruirse."
"""
from __future__ import annotations

import json
import structlog
from pathlib import Path

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


# Archivos que el Ingeniero puede modificar sin CR1
ARCHIVOS_SAFE = {
    "src/pilates/enjambre.py",
    "src/pilates/guardian_sesgos.py",
    "src/pilates/diagnosticador.py",
    "docs/operativo/MANUAL_DIRECTOR_OPUS.md",
    "src/pilates/buscador.py",
    "src/pilates/generativa.py",
}

# Archivos que NUNCA se tocan
ARCHIVOS_PROHIBIDOS = {
    "src/pilates/ingeniero.py",
    "src/pilates/bus.py",
    "src/pilates/router.py",
    "src/db/client.py",
    "src/pilates/redsys_pagos.py",
    "src/pilates/stripe_pagos.py",
}


async def ejecutar_instruccion(instruccion: dict) -> dict:
    """Ejecuta una instrucción del Meta-Cognitivo o Vigía.

    Args:
        instruccion: dict con tipo, archivo, cambio, razon, test, seguridad, prioridad.
    """
    archivo = instruccion.get("archivo", "")
    seguridad = instruccion.get("seguridad", "moderado")

    # NUNCA tocar archivos prohibidos
    if any(archivo.endswith(p) for p in ARCHIVOS_PROHIBIDOS):
        log.warning("ingeniero_prohibido", archivo=archivo)
        return {"status": "prohibido", "archivo": archivo, "razon": "Archivo en lista de prohibidos"}

    # Si no es safe, registrar como pendiente CR1
    if seguridad != "safe":
        return await _registrar_pendiente_cr1(instruccion)

    # Si es safe, verificar que el archivo está en la lista
    if not any(archivo.endswith(s) for s in ARCHIVOS_SAFE):
        log.warning("ingeniero_no_safe", archivo=archivo)
        return await _registrar_pendiente_cr1(instruccion)

    # EJECUTAR cambio safe
    return await _ejecutar_safe(instruccion)


async def _ejecutar_safe(instruccion: dict) -> dict:
    """Ejecuta un cambio safe: backup → briefing_micro → bus."""
    archivo = instruccion.get("archivo", "")
    cambio = instruccion.get("cambio", "")
    razon = instruccion.get("razon", "")
    test_cmd = instruccion.get("test", "")

    log.info("ingeniero_ejecutando_safe", archivo=archivo, cambio=cambio[:100])

    resultado = {
        "archivo": archivo,
        "tipo": instruccion.get("tipo"),
        "seguridad": "safe",
        "pasos": [],
    }

    try:
        # 1. LEER archivo actual (backup en memoria)
        repo_base = Path(__file__).parent.parent.parent
        filepath = repo_base / archivo

        if not filepath.exists():
            return {"status": "error", "razon": f"Archivo no existe: {archivo}"}

        contenido_original = filepath.read_text(encoding="utf-8")
        resultado["pasos"].append({"paso": "backup", "status": "ok", "lineas": len(contenido_original.splitlines())})

        # 2. PERSISTIR backup en DB
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_ingeniero_backups
                    (tenant_id, archivo, contenido_original, instruccion, created_at)
                VALUES ($1, $2, $3, $4::jsonb, now())
            """, TENANT, archivo, contenido_original,
                json.dumps(instruccion, ensure_ascii=False))
        resultado["pasos"].append({"paso": "backup_db", "status": "ok"})

        # 3. EMITIR briefing_micro al bus
        briefing_micro = (
            f"# Instrucción del Ingeniero (auto-safe)\n\n"
            f"**Archivo:** {archivo}\n"
            f"**Cambio:** {cambio}\n"
            f"**Razón:** {razon}\n"
            f"**Seguridad:** safe (aprobado automáticamente)\n\n"
            f"## Instrucciones:\n"
            f"1. Leer {archivo}\n"
            f"2. Aplicar: {cambio}\n"
            f"3. Verificar: {test_cmd}\n"
            f"4. Si pasa: commit\n"
            f"5. Si falla: revertir\n"
        )

        from src.pilates.bus import emitir
        await emitir("ACCION", "INGENIERO", {
            "tipo": "briefing_micro",
            "archivo": archivo,
            "briefing": briefing_micro,
            "seguridad": "safe",
            "backup_exists": True,
        }, prioridad=instruccion.get("prioridad", 3))
        resultado["pasos"].append({"paso": "briefing_emitido", "status": "ok"})
        resultado["status"] = "briefing_emitido"

    except Exception as e:
        log.error("ingeniero_safe_error", error=str(e), archivo=archivo)
        resultado["status"] = "error"
        resultado["error"] = str(e)[:200]

    # Pizarra
    from src.pilates.pizarra import escribir
    await escribir(
        agente="INGENIERO",
        capa="meta",
        estado="completado" if resultado.get("status") != "error" else "bloqueado",
        detectando=f"Instrucción: {instruccion.get('tipo', '?')} en {archivo}",
        interpretacion=razon[:200],
        accion_propuesta=f"Briefing micro emitido al bus. Seguridad: safe.",
        confianza=0.7,
        prioridad=instruccion.get("prioridad", 3),
    )

    return resultado


async def _registrar_pendiente_cr1(instruccion: dict) -> dict:
    """Registra un cambio que requiere CR1 como briefing pendiente."""
    from src.pilates.bus import emitir

    briefing = (
        f"# Instrucción del Ingeniero (requiere CR1)\n\n"
        f"**Archivo:** {instruccion.get('archivo', '?')}\n"
        f"**Tipo:** {instruccion.get('tipo', '?')}\n"
        f"**Cambio:** {instruccion.get('cambio', '?')}\n"
        f"**Razón:** {instruccion.get('razon', '?')}\n"
        f"**Seguridad:** {instruccion.get('seguridad', '?')}\n"
    )

    await emitir("BRIEFING_PENDIENTE", "INGENIERO", {
        "tipo": "cambio_pendiente_cr1",
        "instruccion": instruccion,
        "briefing": briefing,
        "requiere_cr1": True,
    }, prioridad=instruccion.get("prioridad", 2))

    try:
        from src.pilates.feed import publicar
        await publicar("organismo_ingeniero", "I",
                       "Ingeniero: cambio pendiente CR1",
                       f"{instruccion.get('archivo', '?')}: {instruccion.get('cambio', '?')[:100]}",
                       severidad="warning")
    except Exception:
        pass

    log.info("ingeniero_pendiente_cr1", archivo=instruccion.get("archivo"),
             tipo=instruccion.get("tipo"))

    return {
        "status": "pendiente_cr1",
        "archivo": instruccion.get("archivo"),
        "tipo": instruccion.get("tipo"),
    }


async def procesar_instrucciones_pendientes() -> dict:
    """Lee instrucciones del Meta-Cognitivo del bus y las ejecuta/registra.

    Se ejecuta en el cron mensual, después del Meta-Cognitivo.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada

    señales = await leer_pendientes(tipo="ACCION", limite=20)
    instrucciones_ingeniero = []

    for s in señales:
        payload = s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"])
        if payload.get("tipo") == "instruccion_ingeniero":
            instrucciones_ingeniero.append({"señal_id": str(s["id"]), "instruccion": payload})
            await marcar_procesada(str(s["id"]), "INGENIERO")

    resultados = []
    for item in instrucciones_ingeniero:
        result = await ejecutar_instruccion(item["instruccion"])
        resultados.append(result)

    safe = sum(1 for r in resultados if r.get("status") == "briefing_emitido")
    cr1 = sum(1 for r in resultados if r.get("status") == "pendiente_cr1")

    log.info("ingeniero_procesadas", total=len(resultados), safe=safe, cr1=cr1)
    return {"total": len(resultados), "safe_ejecutadas": safe, "pendientes_cr1": cr1, "resultados": resultados}
