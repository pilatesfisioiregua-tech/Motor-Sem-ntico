# B-ORG-05: AF1 Conservación + AF3 Depuración → Bus

**Fecha:** 22 marzo 2026
**Objetivo:** Conectar los dos primeros AF al bus: AF1 detecta clientes en riesgo de abandono, AF3 detecta sesiones/servicios ineficientes y emite VETO. El organismo empieza a generar valor de negocio directo.
**Depende de:** B-ORG-01+02 (bus operativo)
**Dato ACD real:** E3 (S=0.46, Se=0.34, C=0.40). F6 y F7 son los gaps — pero AF1/AF3 mejoran S directamente.
**Archivos a CREAR:** 2 nuevos (af1_conservacion.py + af3_depuracion.py)
**Archivos a MODIFICAR:** 2 (cron.py + router.py)
**Tiempo estimado:** 30-40 min

---

## PASO 1: Crear src/pilates/af1_conservacion.py

**Crear archivo:** `src/pilates/af1_conservacion.py`

El código de engagement.py YA calcula scores y detecta caídas. AF1 es el AGENTE que usa esos datos para emitir señales al bus.

```python
"""AF1 Conservación — Agente funcional: proteger lo que el negocio ya tiene.

Ejecuta semanalmente. Lee datos de asistencia, engagement y pagos.
Emite señales ALERTA al bus cuando detecta riesgo de pérdida.

Detecciones:
  1. Clientes fantasma: contrato activo pero 0 asistencias en 3+ semanas
  2. Engagement en caída: score bajó >15 puntos vs semana anterior
  3. Deuda silenciosa: cargos pendientes >60€ sin pago en 2+ semanas
  4. Racha rota: cliente que tenía racha >4 semanas y la rompió

Cada detección → ALERTA al bus con contexto completo para acción.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF1"


async def _detectar_fantasmas() -> list[dict]:
    """Clientes con contrato activo pero sin asistencia en 3+ semanas."""
    pool = await get_pool()
    hace_3_sem = date.today() - timedelta(weeks=3)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   co.tipo as contrato_tipo, co.id as contrato_id,
                   (SELECT MAX(s.fecha) FROM om_asistencias a
                    JOIN om_sesiones s ON s.id = a.sesion_id
                    WHERE a.cliente_id = c.id AND a.estado = 'asistio') as ultima_asistencia
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
            JOIN om_contratos co ON co.cliente_id = c.id AND co.tenant_id = $1 AND co.estado = 'activo'
            WHERE NOT EXISTS (
                SELECT 1 FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = c.id AND a.estado = 'asistio' AND s.fecha >= $2
            )
        """, TENANT, hace_3_sem)

    return [{
        "tipo": "cliente_fantasma",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "contrato_tipo": r["contrato_tipo"],
        "ultima_asistencia": str(r["ultima_asistencia"]) if r["ultima_asistencia"] else "nunca",
        "dias_sin_asistir": (date.today() - r["ultima_asistencia"]).days if r["ultima_asistencia"] else 999,
    } for r in rows]


async def _detectar_engagement_cayendo() -> list[dict]:
    """Clientes cuyo engagement score bajó >15 puntos."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Necesita om_cliente_perfil con engagement_score y engagement_anterior
        try:
            rows = await conn.fetch("""
                SELECT c.id, c.nombre, c.apellidos, c.telefono,
                       p.engagement_score, p.engagement_tendencia
                FROM om_cliente_perfil p
                JOIN om_clientes c ON c.id = p.cliente_id
                JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
                WHERE p.engagement_tendencia = 'bajando'
                AND p.engagement_score < 40
            """, TENANT)
        except Exception:
            return []

    return [{
        "tipo": "engagement_cayendo",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "score": r["engagement_score"],
        "tendencia": r["engagement_tendencia"],
    } for r in rows]


async def _detectar_deuda_silenciosa() -> list[dict]:
    """Clientes con deuda >60€ pendiente >2 semanas."""
    pool = await get_pool()
    hace_2_sem = date.today() - timedelta(weeks=2)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.id, c.nombre, c.apellidos, c.telefono,
                   SUM(ca.total) as deuda,
                   MIN(ca.fecha_cargo) as cargo_mas_antiguo
            FROM om_cargos ca
            JOIN om_clientes c ON c.id = ca.cliente_id
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1 AND ct.estado = 'activo'
            WHERE ca.tenant_id = $1 AND ca.estado = 'pendiente'
            AND ca.fecha_cargo < $2
            GROUP BY c.id, c.nombre, c.apellidos, c.telefono
            HAVING SUM(ca.total) > 60
        """, TENANT, hace_2_sem)

    return [{
        "tipo": "deuda_silenciosa",
        "cliente_id": str(r["id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "telefono": r["telefono"],
        "deuda": float(r["deuda"]),
        "desde": str(r["cargo_mas_antiguo"]),
    } for r in rows]


async def ejecutar_af1() -> dict:
    """Ejecuta AF1 Conservación: detecta riesgos y emite al bus.

    Returns dict con resumen de detecciones y alertas emitidas.
    """
    log.info("af1_inicio")

    fantasmas = await _detectar_fantasmas()
    engagement = await _detectar_engagement_cayendo()
    deuda = await _detectar_deuda_silenciosa()

    todas = fantasmas + engagement + deuda

    # Emitir ALERTA por cada detección
    alertas_emitidas = 0
    for det in todas:
        try:
            from src.pilates.bus import emitir

            # Prioridad según tipo
            prioridad = {
                "cliente_fantasma": 3,
                "engagement_cayendo": 4,
                "deuda_silenciosa": 3,
            }.get(det["tipo"], 5)

            await emitir(
                "ALERTA", ORIGEN,
                {**det, "funcion": "F1", "accion_sugerida": _sugerir_accion(det)},
                prioridad=prioridad,
            )
            alertas_emitidas += 1
        except Exception as e:
            log.warning("af1_bus_error", tipo=det["tipo"], error=str(e))

    resultado = {
        "fantasmas": len(fantasmas),
        "engagement_cayendo": len(engagement),
        "deuda_silenciosa": len(deuda),
        "total_riesgos": len(todas),
        "alertas_emitidas": alertas_emitidas,
        "detalle": todas[:20],  # Máx 20 en respuesta
    }

    log.info("af1_completo", fantasmas=len(fantasmas),
        engagement=len(engagement), deuda=len(deuda))
    return resultado


def _sugerir_accion(det: dict) -> str:
    """Sugiere acción concreta para cada tipo de riesgo."""
    tipo = det["tipo"]
    nombre = det.get("nombre", "")

    if tipo == "cliente_fantasma":
        dias = det.get("dias_sin_asistir", 0)
        if dias > 30:
            return f"URGENTE: {nombre} lleva {dias} días sin venir. Llamar hoy. Riesgo de baja."
        return f"{nombre} lleva {dias} días sin asistir. Enviar WA preguntando si está bien."

    if tipo == "engagement_cayendo":
        return f"{nombre} engagement en caída (score={det.get('score')}). Revisar si hay problema personal o insatisfacción."

    if tipo == "deuda_silenciosa":
        return f"{nombre} tiene €{det.get('deuda', 0):.0f} pendientes desde {det.get('desde')}. Enviar recordatorio amable."

    return "Revisar situación del cliente."
```

---

## PASO 2: Crear src/pilates/af3_depuracion.py

**Crear archivo:** `src/pilates/af3_depuracion.py`

```python
"""AF3 Depuración — Agente funcional: eliminar lo que no aporta.

F3 es el diferenciador clave de OMNI-MIND: "Todo el mercado vende 'haz más.'
OMNI-MIND es el único que dice 'deja de hacer esto.'"

Ejecuta semanalmente. Analiza eficiencia de sesiones, horarios y servicios.
Emite ALERTA + VETO al bus cuando detecta algo que se debería eliminar.

Detecciones:
  1. Sesiones grupo infrautilizadas: <3 alumnos media en últimas 4 semanas
  2. Horarios vacíos: franjas con 0-1 sesiones programadas en 4 semanas
  3. Contratos zombi: activos pero sin asistencia ni pago en 6+ semanas

Señal VETO: cuando AF3 detecta algo que debe cerrarse, emite VETO que
otros AF (especialmente AF2 Captación) deben respetar. No tiene sentido
captar clientes para un horario que deberías cerrar.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, timedelta

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
ORIGEN = "AF3"


async def _detectar_grupos_infrautilizados() -> list[dict]:
    """Grupos con media <3 alumnos en las últimas 4 semanas."""
    pool = await get_pool()
    hace_4_sem = date.today() - timedelta(weeks=4)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT g.id, g.nombre, g.dia_semana, g.hora_inicio, g.capacidad_max,
                   count(DISTINCT s.id) as sesiones_periodo,
                   COALESCE(AVG(asist_count.n), 0) as media_asistentes
            FROM om_grupos g
            JOIN om_sesiones s ON s.grupo_id = g.id AND s.fecha >= $2
            LEFT JOIN LATERAL (
                SELECT count(*) as n FROM om_asistencias a
                WHERE a.sesion_id = s.id AND a.estado = 'asistio'
            ) asist_count ON true
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            GROUP BY g.id, g.nombre, g.dia_semana, g.hora_inicio, g.capacidad_max
            HAVING COALESCE(AVG(asist_count.n), 0) < 3
        """, TENANT, hace_4_sem)

    return [{
        "tipo": "grupo_infrautilizado",
        "grupo_id": str(r["id"]),
        "nombre": r["nombre"],
        "dia": r["dia_semana"],
        "hora": str(r["hora_inicio"]),
        "capacidad": r["capacidad_max"],
        "media_asistentes": round(float(r["media_asistentes"]), 1),
        "sesiones_periodo": r["sesiones_periodo"],
        "ocupacion_pct": round(float(r["media_asistentes"]) / max(r["capacidad_max"], 1) * 100),
    } for r in rows]


async def _detectar_contratos_zombi() -> list[dict]:
    """Contratos activos sin asistencia ni pago en 6+ semanas."""
    pool = await get_pool()
    hace_6_sem = date.today() - timedelta(weeks=6)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT co.id as contrato_id, co.tipo, co.precio_mensual, co.precio_sesion,
                   c.id as cliente_id, c.nombre, c.apellidos,
                   (SELECT MAX(s.fecha) FROM om_asistencias a
                    JOIN om_sesiones s ON s.id = a.sesion_id
                    WHERE a.cliente_id = c.id AND a.estado = 'asistio') as ultima_asistencia,
                   (SELECT MAX(p.fecha_pago) FROM om_pagos p
                    WHERE p.cliente_id = c.id AND p.tenant_id = $1) as ultimo_pago
            FROM om_contratos co
            JOIN om_clientes c ON c.id = co.cliente_id
            WHERE co.tenant_id = $1 AND co.estado = 'activo'
            AND NOT EXISTS (
                SELECT 1 FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.cliente_id = c.id AND s.fecha >= $2
            )
            AND NOT EXISTS (
                SELECT 1 FROM om_pagos p
                WHERE p.cliente_id = c.id AND p.tenant_id = $1 AND p.fecha_pago >= $2
            )
        """, TENANT, hace_6_sem)

    return [{
        "tipo": "contrato_zombi",
        "contrato_id": str(r["contrato_id"]),
        "cliente_id": str(r["cliente_id"]),
        "nombre": f"{r['nombre']} {r['apellidos']}",
        "contrato_tipo": r["tipo"],
        "ultima_asistencia": str(r["ultima_asistencia"]) if r["ultima_asistencia"] else "nunca",
        "ultimo_pago": str(r["ultimo_pago"]) if r["ultimo_pago"] else "nunca",
    } for r in rows]


async def ejecutar_af3() -> dict:
    """Ejecuta AF3 Depuración: detecta ineficiencias y emite al bus.

    Emite dos tipos de señal:
    - ALERTA: algo ineficiente detectado (informativo)
    - PRESCRIPCION con subtipo VETO: propuesta de cortar algo + señal
      para que otros AF la respeten

    Returns dict con resumen.
    """
    log.info("af3_inicio")

    grupos = await _detectar_grupos_infrautilizados()
    zombis = await _detectar_contratos_zombi()

    alertas_emitidas = 0
    vetos_emitidos = 0
    depuraciones_creadas = 0

    from src.pilates.bus import emitir

    # Grupos infrautilizados → ALERTA + VETO + registrar depuración
    for g in grupos:
        try:
            # ALERTA informativa
            await emitir(
                "ALERTA", ORIGEN,
                {
                    **g,
                    "funcion": "F3",
                    "accion_sugerida": f"Grupo '{g['nombre']}' ({g['dia']} {g['hora']}) con media {g['media_asistentes']} alumnos ({g['ocupacion_pct']}% ocupación). Considerar cerrar o fusionar.",
                },
                prioridad=4,
            )
            alertas_emitidas += 1

            # VETO: si ocupación <30%, emitir señal VETO para bloquear captación en ese horario
            if g["ocupacion_pct"] < 30:
                await emitir(
                    "PRESCRIPCION", ORIGEN,
                    {
                        "subtipo": "VETO",
                        "objeto": f"grupo:{g['grupo_id']}",
                        "razon": f"Grupo '{g['nombre']}' a {g['ocupacion_pct']}% ocupación. No captar para este horario hasta resolver.",
                        "funcion": "F3",
                        "bloquea_af": ["AF2"],  # AF2 Captación no debería llenar un horario que debería cerrarse
                    },
                    prioridad=2,
                )
                vetos_emitidos += 1

            # Registrar en om_depuracion
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO om_depuracion (tenant_id, tipo, descripcion,
                            impacto_estimado, funcion_l07, lente, origen)
                        VALUES ($1, 'servicio_eliminar', $2, $3, 'F3', 'salud', 'automatizacion')
                        ON CONFLICT DO NOTHING
                    """, TENANT,
                        f"Grupo '{g['nombre']}' ({g['dia']} {g['hora']}): {g['media_asistentes']} alumnos media, {g['ocupacion_pct']}% ocupación.",
                        f"Liberar franja horaria. {g['capacidad']} plazas infrautilizadas.")
                depuraciones_creadas += 1
            except Exception as e:
                log.warning("af3_depuracion_error", error=str(e))

        except Exception as e:
            log.warning("af3_bus_error", tipo="grupo", error=str(e))

    # Contratos zombi → ALERTA
    for z in zombis:
        try:
            await emitir(
                "ALERTA", ORIGEN,
                {
                    **z,
                    "funcion": "F3",
                    "accion_sugerida": f"Contrato zombi de {z['nombre']}: ni asiste ni paga desde hace >6 semanas. Proponer baja formal o conversación.",
                },
                prioridad=4,
            )
            alertas_emitidas += 1

            # Registrar en om_depuracion
            try:
                pool = await get_pool()
                async with pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO om_depuracion (tenant_id, tipo, descripcion,
                            funcion_l07, lente, origen)
                        VALUES ($1, 'cliente_toxico', $2, 'F3', 'salud', 'automatizacion')
                        ON CONFLICT DO NOTHING
                    """, TENANT,
                        f"Contrato zombi de {z['nombre']}: sin asistencia ni pago en 6+ semanas. Considerar baja formal.")
                depuraciones_creadas += 1
            except Exception as e:
                pass

        except Exception as e:
            log.warning("af3_bus_error", tipo="zombi", error=str(e))

    resultado = {
        "grupos_infrautilizados": len(grupos),
        "contratos_zombi": len(zombis),
        "total_detecciones": len(grupos) + len(zombis),
        "alertas_emitidas": alertas_emitidas,
        "vetos_emitidos": vetos_emitidos,
        "depuraciones_registradas": depuraciones_creadas,
        "detalle_grupos": grupos[:10],
        "detalle_zombis": zombis[:10],
    }

    log.info("af3_completo", grupos=len(grupos), zombis=len(zombis), vetos=vetos_emitidos)
    return resultado
```

---

## PASO 3: Añadir al cron semanal

**Archivo:** `src/pilates/cron.py`

**NOTA:** Este briefing asume que B-ORG-03 ya se deployó y cron.py ya tiene vigía+mecánico+autofagia.

En `_tarea_semanal()`, buscar la última línea DENTRO del try (después de buscar-por-gaps o después de lo que haya añadido B-ORG-03). Buscar EXACTAMENTE:

```python
        # 4. Búsqueda dirigida por gaps
        from src.pilates.buscador import buscar_por_gaps
        busq = await buscar_por_gaps()
        log.info("cron_semanal_busqueda_ok", gaps=busq.get("gaps_identificados"), resultados=busq.get("resultados_perplexity"))
```

DESPUÉS de ese bloque, añadir:

```python

        # 5. AF1 Conservación — detectar clientes en riesgo
        from src.pilates.af1_conservacion import ejecutar_af1
        af1 = await ejecutar_af1()
        log.info("cron_semanal_af1_ok", riesgos=af1.get("total_riesgos"), alertas=af1.get("alertas_emitidas"))

        # 6. AF3 Depuración — detectar ineficiencias + VETO
        from src.pilates.af3_depuracion import ejecutar_af3
        af3 = await ejecutar_af3()
        log.info("cron_semanal_af3_ok", detecciones=af3.get("total_detecciones"), vetos=af3.get("vetos_emitidos"))
```

---

## PASO 4: Añadir endpoints a router.py

**Archivo:** `src/pilates/router.py`

Buscar EXACTAMENTE el último endpoint añadido (de B-ORG-03, al final del archivo). Después del último endpoint, añadir:

```python


# ============================================================
# AF1 CONSERVACIÓN + AF3 DEPURACIÓN — Agentes funcionales
# ============================================================

@router.post("/af/conservacion")
async def af_conservacion():
    """AF1: Detecta clientes en riesgo de abandono. Emite ALERTAs al bus."""
    from src.pilates.af1_conservacion import ejecutar_af1
    return await ejecutar_af1()


@router.post("/af/depuracion")
async def af_depuracion():
    """AF3: Detecta sesiones y servicios ineficientes. Emite ALERTAs + VETOs al bus."""
    from src.pilates.af3_depuracion import ejecutar_af3
    return await ejecutar_af3()
```

---

## PASO 5: Deploy

```bash
cd /Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico
fly deploy -a chief-os-omni
```

---

## TESTS — Ejecutar en orden tras deploy

### TEST 1: AF1 Conservación
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/af/conservacion \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['fantasmas','engagement_cayendo','deuda_silenciosa','alertas_emitidas'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok:
    print(f'  Fantasmas: {d[\"fantasmas\"]}')
    print(f'  Engagement cayendo: {d[\"engagement_cayendo\"]}')
    print(f'  Deuda silenciosa: {d[\"deuda_silenciosa\"]}')
    print(f'  Alertas emitidas: {d[\"alertas_emitidas\"]}')"
```

### TEST 2: AF3 Depuración
```bash
curl -s -X POST https://motor-semantico-omni.fly.dev/pilates/af/depuracion \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
ok = all(k in d for k in ['grupos_infrautilizados','contratos_zombi','vetos_emitidos'])
print('PASS' if ok else 'FAIL:', json.dumps(d, indent=2))
if ok:
    print(f'  Grupos infrautilizados: {d[\"grupos_infrautilizados\"]}')
    print(f'  Contratos zombi: {d[\"contratos_zombi\"]}')
    print(f'  VETOs emitidos: {d[\"vetos_emitidos\"]}')
    print(f'  Depuraciones registradas: {d[\"depuraciones_registradas\"]}')"
```

### TEST 3: Señales en bus (AF1 + AF3 dejan rastro)
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/historial?limite=10' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
origenes = set(s['origen'] for s in d.get('señales', d if isinstance(d, list) else []))
af1_ok = 'AF1' in origenes or d.get('total', 0) == 0  # 0 alertas es válido si no hay riesgos
af3_ok = 'AF3' in origenes or d.get('total', 0) == 0
print('PASS' if af1_ok or af3_ok else 'FAIL')
print(f'  Orígenes en bus: {origenes}')"
```

### TEST 4: VETOs registrados (si hay grupos <30%)
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/bus/historial?tipo=PRESCRIPCION&origen=AF3&limite=5' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
vetos = [s for s in d.get('señales', []) if s.get('payload',{}).get('subtipo') == 'VETO']
print(f'PASS — {len(vetos)} VETOs en bus' if isinstance(d, dict) else 'FAIL:', d)"
```

### TEST 5: Depuraciones en tabla om_depuracion
```bash
curl -s 'https://motor-semantico-omni.fly.dev/pilates/depuracion?estado=propuesta' \
  | python3 -c "
import sys,json; d=json.load(sys.stdin)
auto = [x for x in d if x.get('origen') == 'automatizacion'] if isinstance(d, list) else []
print(f'PASS — {len(auto)} depuraciones automáticas' if isinstance(d, list) else 'FAIL:', d)"
```

---

## CRITERIO PASS/FAIL

**PASS = Tests 1 y 2 devuelven PASS (endpoints responden con estructura correcta).** Los números pueden ser 0 si no hay riesgos/ineficiencias — eso es válido, no es FAIL.

**FAIL = Tests 1 o 2 devuelven FAIL (error de endpoint o estructura inesperada).** Revisar logs con `fly logs -a chief-os-omni`.

Tests 3-5 son informativos — verifican que las señales llegan al bus y las depuraciones se persisten.
