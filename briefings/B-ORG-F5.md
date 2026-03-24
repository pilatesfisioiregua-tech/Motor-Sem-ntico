# B-ORG-F5 — Fase 5: Agentes Diana + Pizarra Comunicación + Evolución

**Fecha:** 24 marzo 2026
**Estimación:** ~10h
**Prerequisito:** B-ORG-F4 (motor.pensar(), af_generico.py, pizarras cognitiva/temporal/evolución)
**WIP:** 1 (secuencial)
**Principios:** P62 (menos agentes que piensen mejor), P64 (pizarras), P66 (circuitos — nada fire-and-forget)

---

## OBJETIVO

Añadir los 4 agentes que FALTAN (Mediador, Reactivo, Memoria, Traductor) y crear la Pizarra Comunicación (#9) que convierte WA de "disparos puntuales" a "intenciones programadas con tracking".

**Antes:** Conflictos cross-AF se detectan DESPUÉS (Convergencia). Todo espera al lunes. WA fire-and-forget. Nadie sabe que cada marzo cancelan por Semana Santa.
**Después:** Mediador resuelve ANTES de actuar. Reactivo responde mismo día. Memoria ve patrones cross-ciclo. Traductor traduce álgebra → castellano de pueblo.

---

## ESTADO ACTUAL — LO QUE YA EXISTE

- `ejecutor_convergencia.py` — Ejecutor + Convergencia + Gestor (detecta conflictos DESPUÉS)
- `evaluador_organismo.py` — Compara diagnósticos semana N vs N+1 (httpx directo)
- `voz_reactivo.py` — Procesa WA entrantes, emite señales al bus (pero NO reactúa rápido)
- `bus.py` — 6 tipos de señal, emitir/leer/marcar
- Pizarra Evolución — tabla creada en F2 (vacía)
- LISTEN/NOTIFY — trigger creado en F2 (señales prioridad ≤2)

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/pilates/ejecutor_convergencia.py  ← Convergencia actual (reemplazada parcialmente por Mediador)
src/pilates/evaluador_organismo.py    ← Evaluador (migrar a motor.pensar)
src/pilates/voz_reactivo.py           ← Reactivo actual (enriquecer)
src/pilates/bus.py                    ← Bus de señales
src/pilates/whatsapp.py               ← enviar_texto, enviar_botones
src/pilates/cron.py                   ← Donde se engancha todo
src/motor/pensar.py                   ← API única (creada en F4)
src/pilates/pizarras.py               ← Helper pizarras (creada en F2)
src/pilates/briefing.py               ← generar_briefing() actual
```

---

## PASO 0: MIGRACIÓN SQL (030_comunicacion_f5.sql)

Crear archivo: `migrations/030_comunicacion_f5.sql`

```sql
-- 030_comunicacion_f5.sql — Pizarra Comunicación + Mediador
-- Fase 5 del Roadmap v4 (P66)

-- 1. Pizarra Comunicación (#9) — intenciones programadas con tracking
CREATE TABLE IF NOT EXISTS om_pizarra_comunicacion (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    destinatario TEXT NOT NULL,
    destinatario_nombre TEXT,
    cliente_id UUID,
    canal TEXT DEFAULT 'whatsapp',
    tipo TEXT NOT NULL,
    mensaje TEXT NOT NULL,
    programado_para TIMESTAMPTZ,
    estado TEXT DEFAULT 'pendiente',
    fallback_canal TEXT,
    origen TEXT,
    metadata JSONB DEFAULT '{}',
    wa_message_id TEXT,
    entregado_at TIMESTAMPTZ,
    leido_at TIMESTAMPTZ,
    respondido_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_pcom_pendiente
    ON om_pizarra_comunicacion(estado, programado_para)
    WHERE estado = 'pendiente';
CREATE INDEX IF NOT EXISTS idx_pcom_cliente
    ON om_pizarra_comunicacion(cliente_id);
CREATE INDEX IF NOT EXISTS idx_pcom_tipo
    ON om_pizarra_comunicacion(tipo);

-- 2. Tabla mediación — registro de conflictos resueltos
CREATE TABLE IF NOT EXISTS om_mediaciones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    ciclo TEXT NOT NULL,
    conflicto JSONB NOT NULL,
    resolucion JSONB NOT NULL,
    af_involucrados TEXT[] NOT NULL,
    objeto_id UUID,
    objeto_tipo TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_med_ciclo ON om_mediaciones(tenant_id, ciclo);

-- 3. Trigger: marcar leído/respondido actualiza pizarra comunicación
CREATE OR REPLACE FUNCTION update_pcom_estado() RETURNS trigger AS $$
BEGIN
    -- Cuando WA webhook marca un mensaje como leído/respondido
    IF NEW.estado_wa = 'read' AND NEW.wa_message_id IS NOT NULL THEN
        UPDATE om_pizarra_comunicacion
        SET leido_at = now(), estado = 'leido', updated_at = now()
        WHERE wa_message_id = NEW.wa_message_id AND leido_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger si om_mensajes_wa tiene la columna
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'om_mensajes_wa') THEN
        -- Añadir columna estado_wa si no existe
        ALTER TABLE om_mensajes_wa ADD COLUMN IF NOT EXISTS estado_wa TEXT;
        DROP TRIGGER IF EXISTS trg_pcom_estado ON om_mensajes_wa;
        CREATE TRIGGER trg_pcom_estado
            AFTER UPDATE ON om_mensajes_wa
            FOR EACH ROW EXECUTE FUNCTION update_pcom_estado();
    END IF;
END $$;
```

**Test 0.1:** `SELECT count(*) FROM om_pizarra_comunicacion` → 0
**Test 0.2:** `SELECT count(*) FROM om_mediaciones` → 0

---

## PASO 1: MEDIADOR — Resuelve conflictos ANTES de actuar

Crear archivo: `src/pilates/mediador.py`

```python
"""Mediador — Resuelve conflictos cross-AF ANTES de actuar (P62).

Hoy: Convergencia detecta conflictos DESPUÉS (daño ya hecho).
Mañana: Mediador lee señales PRESCRIPCION pendientes, agrupa por objeto,
        detecta contradicciones, y resuelve con motor.pensar().

Ejemplo:
  AF3 dice "cerrar grupo L-X 17:15" (3 alumnos, no rentable)
  AF1 dice "retener a María" (está en ese grupo, riesgo baja)
  Mediador decide: "mover María a grupo M-J 18:15 antes de cerrar L-X"
"""
from __future__ import annotations

import json
import structlog
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"

SYSTEM_MEDIADOR = """Eres el Mediador del organismo cognitivo.
Tu trabajo: resolver CONFLICTOS entre agentes funcionales ANTES de que actúen.

Cuando 2+ agentes señalan el mismo cliente/grupo con acciones contradictorias:
- NO elijas un ganador automáticamente
- Busca una TERCERA OPCIÓN que satisfaga ambas intenciones
- Si no hay tercera opción, prioriza: Salud > Sentido > Continuidad

Formato de respuesta JSON:
{
  "conflictos_detectados": N,
  "resoluciones": [
    {
      "objeto": "cliente/grupo afectado",
      "conflicto": "AF3 quiere X, AF1 quiere Y",
      "resolucion": "Hacer Z que satisface ambos",
      "accion_final": "descripción de la acción unificada",
      "af_origen": ["AF1", "AF3"],
      "prioridad": 1-5
    }
  ],
  "sin_conflicto": ["señales que no conflictan — pasar directo"]
}"""


async def mediar(ciclo: str = None) -> dict:
    """Lee señales PRESCRIPCION pendientes, detecta conflictos, resuelve.

    Se ejecuta ANTES del Ejecutor en el ciclo semanal.
    """
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Leer señales PRESCRIPCION y ACCION no procesadas
        senales = await conn.fetch("""
            SELECT id, tipo_senal, origen, contenido, prioridad, payload
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND procesada = false
                AND tipo_senal IN ('PRESCRIPCION', 'ACCION', 'ALERTA')
            ORDER BY prioridad ASC
        """, TENANT)

    if len(senales) < 2:
        log.info("mediador_skip", razon="<2 señales pendientes")
        return {"status": "skip", "conflictos": 0}

    # Agrupar por objeto (cliente_id o grupo_id en payload)
    por_objeto = defaultdict(list)
    for s in senales:
        payload = s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"] or "{}")
        obj_id = payload.get("cliente_id") or payload.get("grupo_id") or payload.get("objeto_id") or "global"
        por_objeto[obj_id].append({
            "id": str(s["id"]),
            "tipo": s["tipo_senal"],
            "origen": s["origen"],
            "contenido": s["contenido"],
            "prioridad": s["prioridad"],
            "payload": payload,
        })

    # Solo mediar objetos con señales de 2+ AF distintos
    conflictos = []
    for obj_id, sigs in por_objeto.items():
        origenes = set(s["origen"] for s in sigs)
        if len(origenes) >= 2:
            conflictos.append({"objeto_id": obj_id, "senales": sigs})

    if not conflictos:
        log.info("mediador_sin_conflictos", total_senales=len(senales))
        return {"status": "ok", "conflictos": 0, "senales_directas": len(senales)}

    # Mediar con motor.pensar()
    user_msg = f"CONFLICTOS A RESOLVER ({len(conflictos)}):\n\n"
    for i, c in enumerate(conflictos):
        user_msg += f"=== Conflicto {i+1} (objeto: {c['objeto_id']}) ===\n"
        for s in c["senales"]:
            user_msg += f"  {s['origen']} [{s['tipo']}] p{s['prioridad']}: {s['contenido']}\n"
        user_msg += "\n"

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=False,
    )
    resultado = await pensar(system=SYSTEM_MEDIADOR, user=user_msg, config=config)
    parsed = extraer_json(resultado.texto, fallback={"resoluciones": [], "conflictos_detectados": 0})

    # Registrar mediaciones
    resoluciones = parsed.get("resoluciones", [])
    pool = await get_pool()
    async with pool.acquire() as conn:
        for r in resoluciones:
            await conn.execute("""
                INSERT INTO om_mediaciones
                    (tenant_id, ciclo, conflicto, resolucion, af_involucrados)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5)
            """, TENANT, ciclo,
                json.dumps({"descripcion": r.get("conflicto", "")}),
                json.dumps(r),
                r.get("af_origen", []))

    log.info("mediador_ok", conflictos=len(conflictos), resoluciones=len(resoluciones),
             coste=resultado.coste_usd)

    return {
        "status": "ok",
        "conflictos": len(conflictos),
        "resoluciones": len(resoluciones),
        "coste": resultado.coste_usd,
    }
```

**Test 1.1:** `python -c "from src.pilates.mediador import mediar; print('ok')"` → ok

---

## PASO 2: REACTIVO — Señales urgentes via LISTEN/NOTIFY

Crear archivo: `src/pilates/reactivo.py`

```python
"""Reactivo — Responde a señales urgentes en tiempo real (P66).

No espera al lunes. Escucha LISTEN/NOTIFY de señales prioridad ≤ 2
y actúa inmediatamente:
  - Lead nuevo → respuesta <5 min
  - Pago recibido → confirmar por WA
  - Cancelación → ofrecer alternativa
  - Queja → escalar a Jesús
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def procesar_senal_urgente(payload: dict) -> dict:
    """Procesa una señal urgente recibida via LISTEN/NOTIFY.

    Llamado desde el listener en cron.py cuando llega una señal p≤2.
    """
    tipo = payload.get("tipo", "")
    origen = payload.get("origen", "")
    senal_id = payload.get("id", "")

    log.info("reactivo_procesando", tipo=tipo, origen=origen, id=senal_id)

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Leer señal completa
        senal = await conn.fetchrow(
            "SELECT * FROM om_senales_agentes WHERE id = $1", senal_id)
        if not senal:
            return {"status": "senal_no_encontrada"}

        senal_payload = senal["payload"] if isinstance(senal["payload"], dict) else json.loads(senal["payload"] or "{}")

    # Dispatch por tipo de señal
    if tipo == "ALERTA" and senal_payload.get("subtipo") == "lead_nuevo":
        return await _responder_lead(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "pago_recibido":
        return await _confirmar_pago(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "cancelacion":
        return await _ofrecer_alternativa(senal_payload)
    elif tipo == "ALERTA" and senal_payload.get("subtipo") == "queja":
        return await _escalar_queja(senal_payload)
    else:
        log.info("reactivo_skip", tipo=tipo, razon="no_handler")
        return {"status": "skip", "tipo": tipo}


async def _responder_lead(payload: dict) -> dict:
    """Lead nuevo detectado — programar respuesta en pizarra comunicación."""
    telefono = payload.get("telefono", "")
    nombre = payload.get("nombre", "")

    if not telefono:
        return {"status": "sin_telefono"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, canal, tipo, mensaje,
                 programado_para, estado, origen)
            VALUES ($1, $2, $3, 'whatsapp', 'respuesta_lead', $4, now(), 'pendiente', 'REACTIVO')
        """, TENANT, telefono, nombre,
            f"Hola{' ' + nombre if nombre else ''}! Gracias por escribir a Authentic Pilates. "
            f"Tenemos grupos reducidos (máx 4 personas) y sesiones individuales. "
            f"¿Te cuento más?")

    log.info("reactivo_lead_programado", telefono=telefono[-4:])
    return {"status": "programado", "tipo": "respuesta_lead"}


async def _confirmar_pago(payload: dict) -> dict:
    """Pago recibido — confirmar al cliente por WA."""
    cliente_id = payload.get("cliente_id")
    importe = payload.get("importe", 0)

    if not cliente_id:
        return {"status": "sin_cliente"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente or not cliente["telefono"]:
            return {"status": "sin_telefono"}

        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, cliente_id,
                 canal, tipo, mensaje, programado_para, estado, origen)
            VALUES ($1, $2, $3, $4, 'whatsapp', 'confirmacion_pago', $5,
                    now(), 'pendiente', 'REACTIVO')
        """, TENANT, cliente["telefono"], cliente["nombre"], cliente_id,
            f"Hola {cliente['nombre']}! Hemos recibido tu pago de {importe:.2f}€. ¡Gracias!")

    return {"status": "programado", "tipo": "confirmacion_pago"}


async def _ofrecer_alternativa(payload: dict) -> dict:
    """Cancelación detectada — programar oferta de alternativa."""
    cliente_id = payload.get("cliente_id")
    if not cliente_id:
        return {"status": "sin_cliente"}

    # TODO: usar motor.pensar() para generar alternativa personalizada
    pool = await get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id = $1", cliente_id)
        if not cliente or not cliente["telefono"]:
            return {"status": "sin_telefono"}

        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, destinatario_nombre, cliente_id,
                 canal, tipo, mensaje, programado_para, estado, origen)
            VALUES ($1, $2, $3, $4, 'whatsapp', 'oferta_alternativa', $5,
                    now() + interval '1 hour', 'pendiente', 'REACTIVO')
        """, TENANT, cliente["telefono"], cliente["nombre"], cliente_id,
            f"Hola {cliente['nombre']}, hemos visto que has cancelado tu sesión. "
            f"¿Te viene mejor otro horario esta semana? Podemos buscar hueco.")

    return {"status": "programado", "tipo": "oferta_alternativa"}


async def _escalar_queja(payload: dict) -> dict:
    """Queja detectada — avisar a Jesús inmediatamente."""
    import os
    telefono_jesus = os.getenv("JESUS_TELEFONO", "")
    if not telefono_jesus:
        return {"status": "sin_telefono_jesus"}

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pizarra_comunicacion
                (tenant_id, destinatario, canal, tipo, mensaje,
                 programado_para, estado, origen, metadata)
            VALUES ($1, $2, 'whatsapp', 'escalacion_queja', $3,
                    now(), 'pendiente', 'REACTIVO', $4::jsonb)
        """, TENANT, telefono_jesus,
            f"⚠️ Queja de cliente: {payload.get('contenido', 'sin detalle')[:200]}",
            json.dumps(payload))

    return {"status": "programado", "tipo": "escalacion_queja"}


# ============================================================
# DESPACHADOR DE COMUNICACIONES PENDIENTES
# ============================================================

async def despachar_comunicaciones() -> dict:
    """Lee om_pizarra_comunicacion pendientes y las envía.

    Se ejecuta cada 15 min (desde cron_loop vigía).
    """
    pool = await get_pool()
    enviados = 0
    errores = 0

    async with pool.acquire() as conn:
        pendientes = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id = $1 AND estado = 'pendiente'
                AND (programado_para IS NULL OR programado_para <= now())
            ORDER BY programado_para ASC NULLS FIRST
            LIMIT 20
        """, TENANT)

        for p in pendientes:
            if p["canal"] == "whatsapp":
                try:
                    from src.pilates.whatsapp import enviar_texto, is_configured
                    if not is_configured():
                        continue

                    result = await enviar_texto(
                        p["destinatario"], p["mensaje"], p["cliente_id"])

                    if result.get("status") == "sent":
                        await conn.execute("""
                            UPDATE om_pizarra_comunicacion
                            SET estado = 'enviado', wa_message_id = $2,
                                updated_at = now()
                            WHERE id = $1
                        """, p["id"], result.get("wa_message_id"))
                        enviados += 1
                    else:
                        await conn.execute("""
                            UPDATE om_pizarra_comunicacion
                            SET estado = 'error', error = $2, updated_at = now()
                            WHERE id = $1
                        """, p["id"], result.get("detail", "unknown")[:200])
                        errores += 1

                except Exception as e:
                    await conn.execute("""
                        UPDATE om_pizarra_comunicacion
                        SET estado = 'error', error = $2, updated_at = now()
                        WHERE id = $1
                    """, p["id"], str(e)[:200])
                    errores += 1

    if enviados > 0 or errores > 0:
        log.info("despachar_ok", enviados=enviados, errores=errores)
    return {"enviados": enviados, "errores": errores}
```

**Test 2.1:** `python -c "from src.pilates.reactivo import despachar_comunicaciones; print('ok')"` → ok

---

## PASO 3: MEMORIA — Patrones cross-ciclo

Crear archivo: `src/pilates/memoria.py`

```python
"""Memoria — Detecta patrones cross-ciclo y escribe en Pizarra Evolución.

Mensual. Lee snapshots de múltiples ciclos + evaluaciones.
Detecta: estacionalidad, eficacia prescripciones, patrones recurrentes.

Ejemplo: "Cada marzo bajan las asistencias un 20% (Semana Santa)."
→ Director lee esto en pizarra evolución y prescribe AF1 preventivo en febrero.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"

SYSTEM_MEMORIA = """Eres el agente Memoria del organismo cognitivo.
Tu trabajo: detectar PATRONES que emergen de múltiples ciclos semanales.

Recibes snapshots de varias semanas. Busca:
1. ESTACIONALIDAD: ¿Hay meses donde siempre pasa X? (ej: vacaciones, fiestas)
2. EFICACIA: ¿Las prescripciones del Director funcionaron? ¿Qué INTs dan resultados?
3. RECURRENCIA: ¿Hay clientes que repiten el mismo patrón? (ej: cancelan, vuelven, cancelan)
4. TENDENCIAS: ¿Mejora o empeora algo semana tras semana?

Formato JSON:
{
  "patrones": [
    {
      "tipo": "estacionalidad|eficacia|recurrencia|tendencia",
      "descripcion": "Descripción del patrón en lenguaje claro",
      "confianza": 0.0-1.0,
      "evidencia_ciclos": N,
      "accion_sugerida": "Lo que el Director debería hacer"
    }
  ]
}"""


async def detectar_patrones_cross_ciclo() -> dict:
    """Lee snapshots de los últimos 8 ciclos y detecta patrones."""
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Últimos 8 snapshots de estado
        snapshots = await conn.fetch("""
            SELECT ciclo, tipo_pizarra, contenido, created_at
            FROM om_pizarra_snapshot
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT 80
        """, TENANT)

        # Últimas 8 evaluaciones
        evaluaciones = await conn.fetch("""
            SELECT estado_pre, lentes_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC
            LIMIT 8
        """)

    if len(snapshots) < 8:
        log.info("memoria_skip", razon="<8 snapshots", actual=len(snapshots))
        return {"status": "skip", "razon": "datos_insuficientes"}

    # Construir resumen para el LLM
    resumen_ciclos = []
    ciclos_vistos = set()
    for s in snapshots:
        if s["ciclo"] not in ciclos_vistos and s["tipo_pizarra"] == "estado":
            ciclos_vistos.add(s["ciclo"])
            contenido = s["contenido"] if isinstance(s["contenido"], dict) else json.loads(s["contenido"])
            resumen_ciclos.append(f"Ciclo {s['ciclo']}: {json.dumps(contenido, default=str)[:500]}")

    resumen_evaluaciones = []
    for e in evaluaciones:
        resumen_evaluaciones.append(
            f"  Estado: {e['estado_pre']}, Lentes: {e['lentes_pre']}, "
            f"Métricas: {str(e['metricas'])[:200]}")

    user_msg = (
        f"SNAPSHOTS DE {len(ciclos_vistos)} CICLOS:\n"
        + "\n".join(resumen_ciclos[:8])
        + f"\n\nEVALUACIONES ({len(resumen_evaluaciones)}):\n"
        + "\n".join(resumen_evaluaciones)
    )

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=True, ttl_cache_horas=720,  # 30 días
    )
    resultado = await pensar(system=SYSTEM_MEMORIA, user=user_msg, config=config)
    parsed = extraer_json(resultado.texto, fallback={"patrones": []})

    # Escribir patrones en Pizarra Evolución
    patrones = parsed.get("patrones", [])
    async with pool.acquire() as conn:
        for p in patrones[:10]:
            await conn.execute("""
                INSERT INTO om_pizarra_evolucion
                    (tenant_id, tipo, descripcion, datos, confianza, evidencia_ciclos)
                VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            """, TENANT, p.get("tipo", "patron"),
                p.get("descripcion", "")[:500],
                json.dumps(p, default=str),
                p.get("confianza", 0.5),
                p.get("evidencia_ciclos", 1))

    log.info("memoria_ok", patrones=len(patrones), coste=resultado.coste_usd)
    return {"status": "ok", "patrones": len(patrones), "coste": resultado.coste_usd}
```

**Test 3.1:** `python -c "from src.pilates.memoria import detectar_patrones_cross_ciclo; print('ok')"` → ok

---

## PASO 4: TRADUCTOR — Álgebra → castellano de pueblo para WA lunes

Crear archivo: `src/pilates/traductor.py`

```python
"""Traductor — Convierte acciones algebraicas → castellano para WA (P66).

Lee pizarra cognitiva + estado → 1 LLM call → intención programada lunes 07:00.

Antes: El briefing generaba JSON técnico que Jesús no leía.
Ahora: Un mensaje WA claro, accionable, en tono de socio inteligente.
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"

SYSTEM_TRADUCTOR = """Eres el Traductor del organismo cognitivo de un estudio de Pilates
en un pueblo de La Rioja (~4.000 habitantes).

Tu trabajo: convertir las ACCIONES del sistema (técnicas, algebraicas) en un
MENSAJE WHATSAPP claro, concreto y accionable para Jesús, el dueño del estudio.

REGLAS:
- Castellano de pueblo. Nada de jerga técnica. Nada de "inteligencias" ni "lentes".
- Máximo 5 acciones, priorizadas por impacto.
- Cada acción: QUÉ hacer + POR QUÉ + CUÁNDO.
- Tono: socio inteligente que te cuenta qué pasa y qué hacer. No un robot.
- Empieza con 1-2 líneas de resumen ("Esta semana: todo tranquilo" o "Ojo, hay 3 cosas importantes").
- Si hay riesgo de baja, di el nombre del cliente y qué hacer.
- Si hay deuda, di cuánto y de quién.
- Acaba con algo motivador breve.

Formato: texto plano para WhatsApp (sin markdown, sin JSON).
Máximo 800 caracteres (límite WA cómodo)."""


async def traducir_acciones_semana(ciclo: str = None) -> dict:
    """Lee señales procesadas + mediaciones + briefing → genera WA para Jesús.

    Se ejecuta al FINAL del ciclo semanal, después de todo lo demás.
    Programa la intención en om_pizarra_comunicacion para lunes 07:00.
    """
    import os
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Señales procesadas esta semana
        senales = await conn.fetch("""
            SELECT origen, tipo_senal, contenido, prioridad
            FROM om_senales_agentes
            WHERE tenant_id = $1 AND procesada = true
                AND created_at >= date_trunc('week', now())
            ORDER BY prioridad ASC
            LIMIT 20
        """, TENANT)

        # Mediaciones
        mediaciones = await conn.fetch("""
            SELECT conflicto, resolucion FROM om_mediaciones
            WHERE tenant_id = $1 AND ciclo = $2
        """, TENANT, ciclo)

        # Briefing numérico
        from src.pilates.briefing import generar_briefing
        briefing = await generar_briefing()

    # Construir contexto para el Traductor
    resumen = []
    resumen.append(f"NÚMEROS SEMANA: {json.dumps(briefing.get('numeros', {}), default=str)[:300]}")

    if senales:
        resumen.append(f"SEÑALES ({len(senales)}):")
        for s in senales[:10]:
            resumen.append(f"  {s['origen']} [{s['tipo_senal']}] p{s['prioridad']}: {s['contenido'][:100]}")

    if mediaciones:
        resumen.append(f"MEDIACIONES ({len(mediaciones)}):")
        for m in mediaciones:
            res = m["resolucion"] if isinstance(m["resolucion"], dict) else json.loads(m["resolucion"])
            resumen.append(f"  {res.get('resolucion', '')[:150]}")

    alertas = briefing.get("alertas", {})
    if alertas:
        resumen.append(f"ALERTAS: {json.dumps(alertas, default=str)[:300]}")

    user_msg = "\n".join(resumen)

    config = ConfigPensamiento(
        funcion="*", complejidad="media",
        usar_cache=False,
    )
    resultado = await pensar(system=SYSTEM_TRADUCTOR, user=user_msg, config=config)

    # Programar envío para lunes 07:00
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    proximo_lunes = ahora + timedelta(days=(7 - ahora.weekday()) % 7)
    lunes_7am = proximo_lunes.replace(hour=7, minute=0, second=0, microsecond=0)
    if lunes_7am <= ahora:
        lunes_7am += timedelta(weeks=1)

    telefono_jesus = os.getenv("JESUS_TELEFONO", "")
    if telefono_jesus and resultado.texto:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_pizarra_comunicacion
                    (tenant_id, destinatario, canal, tipo, mensaje,
                     programado_para, estado, origen)
                VALUES ($1, $2, 'whatsapp', 'briefing_semanal', $3,
                        $4, 'pendiente', 'TRADUCTOR')
            """, TENANT, telefono_jesus, resultado.texto[:1500], lunes_7am)

    log.info("traductor_ok", ciclo=ciclo, chars=len(resultado.texto),
             programado=str(lunes_7am), coste=resultado.coste_usd)

    return {
        "status": "ok",
        "mensaje_preview": resultado.texto[:200],
        "programado_para": str(lunes_7am),
        "coste": resultado.coste_usd,
    }
```

**Test 4.1:** `python -c "from src.pilates.traductor import traducir_acciones_semana; print('ok')"` → ok

---

## PASO 5: EVALUDOR MIGRADO A motor.pensar() (src/pilates/evaluador_organismo.py)

Buscar las llamadas httpx directas en `evaluador_organismo.py` y reemplazar por `motor.pensar()`:

**Patrón a buscar:**
```python
async with httpx.AsyncClient(timeout=60.0) as client:
    resp = await client.post(...)
```

**Reemplazar por:**
```python
from src.motor.pensar import pensar, ConfigPensamiento

config = ConfigPensamiento(funcion="*", complejidad="media", usar_cache=False)
resultado = await pensar(system=system_prompt, user=user_prompt, config=config)
texto = resultado.texto
```

**Test 5.1:** `grep "httpx" src/pilates/evaluador_organismo.py` → 0 resultados
**Test 5.2:** `grep "motor.pensar" src/pilates/evaluador_organismo.py` → match

---

## PASO 6: INTEGRAR EN CRON (src/pilates/cron.py)

### 6.1 En _tarea_semanal(), ANTES del ejecutor_convergencia existente:

```python
        # 4c-pre. Mediador: resolver conflictos cross-AF ANTES de actuar
        try:
            from src.pilates.mediador import mediar
            med = await mediar(ciclo=f"W{_hora_madrid().isocalendar()[1]:02d}-{_hora_madrid().isocalendar()[0]}")
            log.info("cron_semanal_mediador_ok",
                     conflictos=med.get("conflictos", 0),
                     resoluciones=med.get("resoluciones", 0))
        except Exception as e:
            log.error("cron_semanal_mediador_error", error=str(e))
```

### 6.2 Al FINAL de _tarea_semanal() (después del snapshot):

```python
        # 12. Traductor: álgebra → castellano pueblo → WA lunes 07:00
        try:
            from src.pilates.traductor import traducir_acciones_semana
            trad = await traducir_acciones_semana()
            log.info("cron_semanal_traductor_ok",
                     programado=trad.get("programado_para"),
                     coste=trad.get("coste"))
        except Exception as e:
            log.error("cron_semanal_traductor_error", error=str(e))
```

### 6.3 En _tarea_mensual(), DESPUÉS del cristalizador:

```python
    # Memoria: patrones cross-ciclo → pizarra evolución
    try:
        from src.pilates.memoria import detectar_patrones_cross_ciclo
        mem = await detectar_patrones_cross_ciclo()
        log.info("cron_mensual_memoria_ok", patrones=mem.get("patrones", 0))
    except Exception as e:
        log.error("cron_mensual_memoria_error", error=str(e))
```

### 6.4 En cron_loop(), en el bloque de vigía (cada 15 min):

```python
        # Despachar comunicaciones pendientes (pizarra comunicación)
        try:
            from src.pilates.reactivo import despachar_comunicaciones
            desp = await despachar_comunicaciones()
            if desp.get("enviados", 0) > 0:
                log.info("cron_despachar_ok", enviados=desp["enviados"])
        except Exception as e:
            log.error("cron_despachar_error", error=str(e))
```

### 6.5 Actualizar listener LISTEN/NOTIFY (ya creado en F2) para llamar al Reactivo:

En la función `_escuchar_senales_urgentes()` de cron.py, cambiar el callback:

De:
```python
        def callback(conn_ref, pid, channel, payload):
            import json as _json
            try:
                data = _json.loads(payload)
                log.warning("senal_urgente_recibida", ...)
                # En futuro: disparar Reactivo inmediatamente
            except Exception as e:
```

A:
```python
        def callback(conn_ref, pid, channel, payload):
            import json as _json
            try:
                data = _json.loads(payload)
                log.warning("senal_urgente_recibida",
                           tipo=data.get("tipo"), origen=data.get("origen"),
                           prioridad=data.get("prioridad"))
                # Disparar Reactivo
                asyncio.create_task(_dispatch_reactivo(data))
            except Exception as e:
                log.error("senal_urgente_parse_error", error=str(e))
```

Y añadir la función helper:

```python
async def _dispatch_reactivo(payload: dict):
    """Dispatch señal urgente al Reactivo."""
    try:
        from src.pilates.reactivo import procesar_senal_urgente
        result = await procesar_senal_urgente(payload)
        log.info("reactivo_dispatch_ok", tipo=payload.get("tipo"), result=result.get("status"))
    except Exception as e:
        log.error("reactivo_dispatch_error", error=str(e))
```

**Test 6.1:** `grep "mediador" src/pilates/cron.py` → match
**Test 6.2:** `grep "traductor" src/pilates/cron.py` → match
**Test 6.3:** `grep "memoria" src/pilates/cron.py` → match
**Test 6.4:** `grep "despachar_comunicaciones" src/pilates/cron.py` → match
**Test 6.5:** `grep "dispatch_reactivo" src/pilates/cron.py` → match

---

## PASO 7: ENDPOINT COMUNICACIONES (src/pilates/router.py)

```python
@router.get("/comunicaciones")
async def get_comunicaciones(estado: str = None, limit: int = 50):
    """Lee pizarra de comunicaciones — tracking WA."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id = 'authentic_pilates'
        """
        params = []
        if estado:
            query += " AND estado = $1"
            params.append(estado)
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        rows = await conn.fetch(query, *params)

    return [dict(r) for r in rows]


@router.get("/mediaciones")
async def get_mediaciones(ciclo: str = None):
    """Historial de mediaciones cross-AF."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        if ciclo:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 AND ciclo=$2 ORDER BY created_at DESC",
                "authentic_pilates", ciclo)
        else:
            rows = await conn.fetch(
                "SELECT * FROM om_mediaciones WHERE tenant_id=$1 ORDER BY created_at DESC LIMIT 50",
                "authentic_pilates")
    return [dict(r) for r in rows]
```

**Test 7.1:** `curl /pilates/comunicaciones` → JSON array
**Test 7.2:** `curl /pilates/mediaciones` → JSON array

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `migrations/030_comunicacion_f5.sql` | **NUEVO** — pizarra comunicación + mediaciones + trigger | 0 |
| `src/pilates/mediador.py` | **NUEVO** — resuelve conflictos cross-AF | 1 |
| `src/pilates/reactivo.py` | **NUEVO** — señales urgentes + despachador comunicaciones | 2 |
| `src/pilates/memoria.py` | **NUEVO** — patrones cross-ciclo → pizarra evolución | 3 |
| `src/pilates/traductor.py` | **NUEVO** — álgebra → castellano pueblo → WA lunes | 4 |
| `src/pilates/evaluador_organismo.py` | httpx → motor.pensar() | 5 |
| `src/pilates/cron.py` | +mediador + traductor + memoria + despachar + reactivo dispatch | 6 |
| `src/pilates/router.py` | +endpoints comunicaciones + mediaciones | 7 |

## TESTS FINALES (PASS/FAIL)

```
T1:  python -c "from src.pilates.mediador import mediar" → sin error                [PASS/FAIL]
T2:  python -c "from src.pilates.reactivo import despachar_comunicaciones" → ok      [PASS/FAIL]
T3:  python -c "from src.pilates.memoria import detectar_patrones_cross_ciclo" → ok  [PASS/FAIL]
T4:  python -c "from src.pilates.traductor import traducir_acciones_semana" → ok     [PASS/FAIL]
T5:  SELECT count(*) FROM om_pizarra_comunicacion → tabla existe                     [PASS/FAIL]
T6:  SELECT count(*) FROM om_mediaciones → tabla existe                              [PASS/FAIL]
T7:  grep "httpx" src/pilates/evaluador_organismo.py → 0 resultados                  [PASS/FAIL]
T8:  grep "mediador" src/pilates/cron.py → match                                     [PASS/FAIL]
T9:  grep "despachar_comunicaciones" src/pilates/cron.py → match                     [PASS/FAIL]
T10: grep "dispatch_reactivo" src/pilates/cron.py → match                            [PASS/FAIL]
T11: curl /pilates/comunicaciones → JSON                                              [PASS/FAIL]
T12: curl /pilates/mediaciones → JSON                                                 [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear `migrations/030_comunicacion_f5.sql` (Paso 0)
2. Crear los 4 archivos nuevos: mediador, reactivo, memoria, traductor (Pasos 1-4)
3. Editar `evaluador_organismo.py` — httpx → motor.pensar (Paso 5)
4. Editar `cron.py` — integrar todos los componentes nuevos (Paso 6)
5. Editar `router.py` — endpoints comunicaciones + mediaciones (Paso 7)
6. Deploy
7. Esperar ciclo semanal (lunes) o trigger manual
8. Verificar T1-T12

## NOTAS

- La pizarra comunicación REEMPLAZA los envíos directos de WA. Pero la transición es gradual: confirmaciones y cumpleaños siguen usando enviar_texto directo hasta que se migren a intenciones programadas.
- El Traductor se ejecuta al FINAL del ciclo semanal — necesita que mediador, AF, evaluador ya hayan corrido.
- Memoria solo produce resultados útiles con ≥8 snapshots (≥2 meses). Antes devuelve "datos_insuficientes".
- El Reactivo despacha comunicaciones cada 15 min (dentro del loop de vigía). Señales urgentes (LISTEN/NOTIFY) se procesan inmediatamente.
