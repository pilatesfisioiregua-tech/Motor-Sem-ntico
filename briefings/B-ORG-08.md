# B-ORG-08: Ejecutor + Convergencia + Gestor Autónomo

**Fecha:** 22 marzo 2026
**Objetivo:** Cerrar FASE 1. El Ejecutor lee prescripciones y coordina AF. El Detector de Convergencia identifica cuando 2+ AF señalan el mismo objeto. El Gestor autónomo poda/promueve en la Matriz. Tras este briefing, TODAS las gomas giran.
**Depende de:** B-ORG-01+02 (bus) + B-ORG-05 (AF1+AF3 emitiendo) + B-ORG-07 (AF restantes)
**Archivos a CREAR:** 1 (ejecutor_convergencia.py)
**Archivos a MODIFICAR:** 2 (cron.py + router.py)
**Tiempo estimado:** 25-35 min

**Dato operativo:** Hay ~50+ señales en el bus de AF1, AF3, AF5 y pronto AF2/AF4/AF6/AF7. El Ejecutor y Convergencia actúan SOBRE esas señales.

---

## PASO 1: Crear src/pilates/ejecutor_convergencia.py

**Crear archivo:** `src/pilates/ejecutor_convergencia.py`

```python
"""Ejecutor + Convergencia + Gestor — Los 3 agentes que cierran el circuito.

EJECUTOR (G5): Lee prescripciones del bus → determina AF destino → emite ACCION
CONVERGENCIA: Cuando 2+ AF señalan el mismo cliente/grupo → genera insight
GESTOR (G6): Cada N señales o semanal → poda señales expiradas, resume actividad

Estos 3 agentes no generan información nueva — ORQUESTAN la existente.
"""
from __future__ import annotations

import json
import structlog
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


# ============================================================
# EJECUTOR — Lee prescripciones y coordina AF
# ============================================================

async def ejecutar_prescripciones() -> dict:
    """Lee señales PRESCRIPCION del bus y las traduce en ACCIONes para AF específicos.

    Flujo: Diagnosticador/Estratega emite PRESCRIPCION → Ejecutor la lee →
    determina qué AF debe actuar → emite ACCION dirigida a ese AF.

    También procesa VETOs: los registra como restricciones activas.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada, emitir

    prescripciones = await leer_pendientes(tipo="PRESCRIPCION", limite=30)

    acciones_emitidas = 0
    vetos_registrados = 0

    for señal in prescripciones:
        señal_id = str(señal["id"])
        payload = señal["payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)

        try:
            subtipo = payload.get("subtipo", "")

            if subtipo == "VETO":
                # VETOs: no generan ACCION, solo se registran y se marcan
                vetos_registrados += 1
                await marcar_procesada(señal_id, "EJECUTOR")
                continue

            # Prescripción normal: determinar AF destino
            funcion = payload.get("funcion", "")
            af_destino = _funcion_a_af(funcion)

            if af_destino:
                await emitir(
                    "ACCION", "EJECUTOR",
                    {
                        "af_destino": af_destino,
                        "prescripcion": payload,
                        "instruccion": payload.get("accion_sugerida", "Ejecutar según prescripción"),
                    },
                    destino=af_destino,
                    prioridad=payload.get("prioridad", 5),
                )
                acciones_emitidas += 1

            await marcar_procesada(señal_id, "EJECUTOR")

        except Exception as e:
            log.warning("ejecutor_error", señal_id=señal_id, error=str(e))

    log.info("ejecutor_completo", prescripciones=len(prescripciones),
        acciones=acciones_emitidas, vetos=vetos_registrados)

    return {
        "prescripciones_leidas": len(prescripciones),
        "acciones_emitidas": acciones_emitidas,
        "vetos_registrados": vetos_registrados,
    }


def _funcion_a_af(funcion: str) -> str | None:
    """Mapea función L0.7 a agente funcional."""
    return {
        "F1": "AF1", "F2": "AF2", "F3": "AF3", "F4": "AF4",
        "F5": "AF5", "F6": "AF6", "F7": "AF7",
    }.get(funcion)


# ============================================================
# CONVERGENCIA — 2+ AF señalan el mismo objeto
# ============================================================

async def detectar_convergencia() -> dict:
    """Detecta cuando 2+ AF emitieron señales sobre el mismo cliente o grupo.

    Convergencia = señal de que algo es importante. Si AF1 dice "cliente fantasma"
    y AF3 dice "contrato zombi" del MISMO cliente, eso es convergencia.

    Busca en señales recientes (últimos 7 días) agrupando por cliente_id y grupo_id.
    """
    pool = await get_pool()
    desde = datetime.now(timezone.utc) - timedelta(days=7)

    convergencias = []

    async with pool.acquire() as conn:
        # Convergencia por cliente: 2+ AF distintos señalaron el mismo cliente
        try:
            rows = await conn.fetch("""
                SELECT
                    payload->>'cliente_id' as cliente_id,
                    array_agg(DISTINCT origen) as agentes,
                    count(*) as señales,
                    array_agg(DISTINCT payload->>'tipo') as tipos
                FROM om_senales_agentes
                WHERE tenant_id = $1 AND created_at >= $2
                AND payload->>'cliente_id' IS NOT NULL
                AND tipo = 'ALERTA'
                GROUP BY payload->>'cliente_id'
                HAVING count(DISTINCT origen) >= 2
            """, TENANT, desde)

            for r in rows:
                # Obtener nombre del cliente
                nombre = await conn.fetchval(
                    "SELECT nombre || ' ' || apellidos FROM om_clientes WHERE id = $1::uuid",
                    r["cliente_id"])

                convergencias.append({
                    "tipo": "convergencia_cliente",
                    "cliente_id": r["cliente_id"],
                    "nombre": nombre or "Desconocido",
                    "agentes": list(r["agentes"]),
                    "señales": r["señales"],
                    "tipos_detectados": list(r["tipos"]),
                    "insight": f"{nombre}: señalado por {', '.join(r['agentes'])} — requiere atención prioritaria.",
                })
        except Exception as e:
            log.warning("convergencia_cliente_error", error=str(e))

        # Convergencia por grupo: 2+ AF señalaron el mismo grupo
        try:
            rows_g = await conn.fetch("""
                SELECT
                    payload->>'grupo_id' as grupo_id,
                    array_agg(DISTINCT origen) as agentes,
                    count(*) as señales,
                    array_agg(DISTINCT payload->>'tipo') as tipos
                FROM om_senales_agentes
                WHERE tenant_id = $1 AND created_at >= $2
                AND payload->>'grupo_id' IS NOT NULL
                AND tipo IN ('ALERTA', 'PRESCRIPCION')
                GROUP BY payload->>'grupo_id'
                HAVING count(DISTINCT origen) >= 2
            """, TENANT, desde)

            for r in rows_g:
                nombre_g = await conn.fetchval(
                    "SELECT nombre FROM om_grupos WHERE id = $1::uuid", r["grupo_id"])
                convergencias.append({
                    "tipo": "convergencia_grupo",
                    "grupo_id": r["grupo_id"],
                    "nombre": nombre_g or "Desconocido",
                    "agentes": list(r["agentes"]),
                    "señales": r["señales"],
                    "tipos_detectados": list(r["tipos"]),
                    "insight": f"Grupo '{nombre_g}': señalado por {', '.join(r['agentes'])} — posible acción combinada.",
                })
        except Exception as e:
            log.warning("convergencia_grupo_error", error=str(e))

    # Emitir OPORTUNIDAD por cada convergencia
    emitidas = 0
    if convergencias:
        try:
            from src.pilates.bus import emitir
            for conv in convergencias:
                await emitir(
                    "OPORTUNIDAD", "CONVERGENCIA",
                    conv,
                    prioridad=3,  # Alta — convergencias son señales fuertes
                )
                emitidas += 1
        except Exception as e:
            log.warning("convergencia_bus_error", error=str(e))

    log.info("convergencia_completa", encontradas=len(convergencias))
    return {
        "convergencias_cliente": len([c for c in convergencias if c["tipo"] == "convergencia_cliente"]),
        "convergencias_grupo": len([c for c in convergencias if c["tipo"] == "convergencia_grupo"]),
        "total": len(convergencias),
        "oportunidades_emitidas": emitidas,
        "detalle": convergencias[:15],
    }


# ============================================================
# GESTOR AUTÓNOMO — Poda y mantenimiento del bus
# ============================================================

async def gestionar_bus() -> dict:
    """Gestor: mantiene el bus limpio y genera resumen de actividad.

    1. Señales procesadas >7 días: archivar conteo + eliminar
    2. Señales pendientes >48h: marcar como expiradas
    3. Resumen de actividad: señales por agente, por tipo, por día
    """
    pool = await get_pool()
    hace_7d = datetime.now(timezone.utc) - timedelta(days=7)
    hace_48h = datetime.now(timezone.utc) - timedelta(hours=48)

    archivadas = 0
    expiradas = 0

    async with pool.acquire() as conn:
        # 1. Contar señales viejas procesadas (para registro) y eliminar
        archivadas = await conn.fetchval("""
            SELECT count(*) FROM om_senales_agentes
            WHERE tenant_id = $1 AND estado IN ('procesada', 'error')
            AND created_at < $2
        """, TENANT, hace_7d) or 0

        if archivadas > 0:
            await conn.execute("""
                DELETE FROM om_senales_agentes
                WHERE tenant_id = $1 AND estado IN ('procesada', 'error')
                AND created_at < $2
            """, TENANT, hace_7d)

        # 2. Señales pendientes >48h: expirar
        result = await conn.execute("""
            UPDATE om_senales_agentes
            SET estado = 'error', procesada_por = 'GESTOR',
                procesada_at = now(), error_detalle = 'Expirada (pendiente >48h)'
            WHERE tenant_id = $1 AND estado = 'pendiente'
            AND created_at < $2
        """, TENANT, hace_48h)
        expiradas = int(result.split()[-1]) if result else 0

        # 3. Resumen de actividad (últimos 7 días)
        actividad = await conn.fetch("""
            SELECT origen, tipo, count(*) as n
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND created_at >= $2
            GROUP BY origen, tipo
            ORDER BY n DESC
        """, TENANT, hace_7d)

        resumen = defaultdict(lambda: defaultdict(int))
        for r in actividad:
            resumen[r["origen"]][r["tipo"]] = r["n"]

    resultado = {
        "archivadas_eliminadas": archivadas,
        "expiradas": expiradas,
        "actividad_7d": dict(resumen),
        "agentes_activos": len(resumen),
    }

    log.info("gestor_bus_completo", archivadas=archivadas, expiradas=expiradas,
        agentes=len(resumen))
    return resultado


# ============================================================
# EJECUTAR TODO
# ============================================================

async def ejecutar_circuito_completo() -> dict:
    """Ejecuta Ejecutor + Convergencia + Gestor en secuencia.

    Este es el cierre del circuito: las señales que generaron los AF
    son procesadas, las convergencias detectadas, y el bus limpiado.
    """
    ejecutor = await ejecutar_prescripciones()
    convergencia = await detectar_convergencia()
    gestor = await gestionar_bus()

    return {
        "ejecutor": ejecutor,
        "convergencia": convergencia,
        "gestor": gestor,
    }
```

---

## PASO 2: Añadir al cron semanal

**Archivo:** `src/pilates/cron.py`

Dentro de `_tarea_semanal()`, después del último paso AF (sea el paso 6 de AF3 o el paso 7 de AF restantes). DENTRO del try, ANTES del except, añadir:

```python

        # 8. Ejecutor + Convergencia + Gestor — cierre del circuito
        from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
        circ = await ejecutar_circuito_completo()
        log.info("cron_semanal_circuito_ok",
            acciones=circ["ejecutor"]["acciones_emitidas"],
            convergencias=circ["convergencia"]["total"],
            archivadas=circ["gestor"]["archivadas_eliminadas"])
```

---

## PASO 3: Añadir endpoints a router.py

**Archivo:** `src/pilates/router.py`

Después del último endpoint existente, añadir:

```python


# ============================================================
# EJECUTOR + CONVERGENCIA + GESTOR — Cierre del circuito
# ============================================================

@router.post("/sistema/ejecutor")
async def sistema_ejecutor():
    """Ejecutor: lee prescripciones del bus y emite ACCIONes a AF."""
    from src.pilates.ejecutor_convergencia import ejecutar_prescripciones
    return await ejecutar_prescripciones()


@router.post("/sistema/convergencia")
async def sistema_convergencia():
    """Detecta cuando 2+ AF señalan el mismo cliente/grupo."""
    from src.pilates.ejecutor_convergencia import detectar_convergencia
    return await detectar_convergencia()


@router.post("/sistema/gestor")
async def sistema_gestor():
    """Gestor: limpia bus + resumen de actividad."""
    from src.pilates.ejecutor_convergencia import gestionar_bus
    return await gestionar_bus()


@router.post("/sistema/circuito")
async def sistema_circuito():
    """Ejecuta Ejecutor + Convergencia + Gestor de una vez."""
    from src.pilates.ejecutor_convergencia import ejecutar_circuito_completo
    return await ejecutar_circuito_completo()
```

---

## PASO 4: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

---

## TESTS

### TEST 1: Ejecutor
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/ejecutor \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['prescripciones_leidas','acciones_emitidas','vetos_registrados'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))"
```

### TEST 2: Convergencia (hay datos reales de AF1+AF3)
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/convergencia \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['convergencias_cliente','convergencias_grupo','total','oportunidades_emitidas'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok and d['total'] > 0:
    print(f'  CONVERGENCIAS: {d[\"total\"]}')
    for c in d.get('detalle', [])[:3]:
        print(f'    {c[\"tipo\"]}: {c[\"nombre\"]} — agentes: {c[\"agentes\"]}')"
```

### TEST 3: Gestor
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/gestor \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['archivadas_eliminadas','expiradas','actividad_7d'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok:
    print(f'  Archivadas: {d[\"archivadas_eliminadas\"]}, Expiradas: {d[\"expiradas\"]}')
    print(f'  Agentes activos 7d: {d[\"agentes_activos\"]}')"
```

### TEST 4: Circuito completo
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/sistema/circuito \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['ejecutor','convergencia','gestor'])
print('PASS' if ok else 'FAIL')
if ok:
    print(f'  Ejecutor: {d[\"ejecutor\"][\"prescripciones_leidas\"]} prescripciones → {d[\"ejecutor\"][\"acciones_emitidas\"]} acciones')
    print(f'  Convergencia: {d[\"convergencia\"][\"total\"]} detectadas')
    print(f'  Gestor: {d[\"gestor\"][\"archivadas_eliminadas\"]} archivadas, {d[\"gestor\"][\"agentes_activos\"]} agentes activos')"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1-4 devuelven PASS.** Test 2 será especialmente interesante — con 2 fantasmas de AF1 y 2 zombis de AF3, podría haber convergencias si son los mismos clientes.

**FAIL = Cualquier test devuelve FAIL.**

---

## RESULTADO: FASE 1 COMPLETA — TODAS LAS GOMAS GIRAN

| Goma | Qué hace | Briefing | Estado |
|---|---|---|---|
| G1 | Datos → Señales | B-ORG-01+02 (OBSERVADOR) | ✅ |
| G2 | Señales → Diagnóstico | B-ORG-01+02 (DIAGNOSTICADOR) | ✅ |
| G3 | Diagnóstico → Búsqueda | B-ORG-01+02 (BUSCADOR) | ✅ |
| G4 | Búsqueda → Prescripción | (pendiente FASE 2: enjambre cognitivo) | ⏳ |
| G5 | Prescripción → Acción | B-ORG-05/06/07 (AF1-AF7) + B-ORG-08 (EJECUTOR) | ✅ |
| G6 | Acción → Aprendizaje | B-ORG-08 (GESTOR) + B-ORG-04 (PROPIOCEPCIÓN) | ✅ |
| META | Rotura → Reparación | B-ORG-03 (VIGÍA+MECÁNICO+AUTÓFAGO) | ✅ |

**6 de 7 gomas giran. G4 (enjambre cognitivo) es FASE 2.**
El organismo ya percibe, diagnostica, busca, actúa, detecta convergencia, se limpia y se repara.
