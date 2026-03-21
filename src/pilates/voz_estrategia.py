"""Motor Tridimensional — Bloque Voz Estratégico.

Cruza los 3 ejes (IRC x Matriz 3Lx7F x PCA) para generar:
1. Estrategia activa de comunicación
2. Calendario semanal de contenido
3. Propuestas contextualizadas

Reemplaza la lógica táctica de voz.py:generar_propuestas()
con un motor que usa LLM + contexto estructurado.

Basado en B2.8 v3.0 §4 — Motor Tridimensional de Contenido.
"""
from __future__ import annotations

import os
import json
import structlog
from datetime import date, timedelta
from typing import Optional

log = structlog.get_logger()
TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# RECOGER SEÑALES TÁCTICAS (herencia de B-PIL-15)
# ============================================================

async def _recoger_senales_internas() -> dict:
    """Recoge señales internas del negocio (Capa B).

    Estas son las mismas señales que B-PIL-15 usaba para generar
    propuestas directamente. Ahora son INPUT del motor estratégico.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Ocupación por grupo
        grupos = await conn.fetch("""
            SELECT g.nombre, g.capacidad_max, g.tipo, g.precio_mensual,
                   g.dias_semana,
                   (SELECT count(*) FROM om_contratos c
                    WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
        """, TENANT)

        total_cap = sum(g["capacidad_max"] for g in grupos)
        total_ocu = sum(g["ocupadas"] for g in grupos)
        ocupacion_pct = round(total_ocu / max(total_cap, 1) * 100, 1)

        grupos_bajos = [
            {"nombre": g["nombre"], "libres": g["capacidad_max"] - g["ocupadas"],
             "pct": round(g["ocupadas"] / max(g["capacidad_max"], 1) * 100)}
            for g in grupos if g["ocupadas"] / max(g["capacidad_max"], 1) < 0.5
        ]

        # Clientes inactivos (>14 días)
        inactivos = await conn.fetchval("""
            SELECT count(DISTINCT c.id)
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            JOIN om_asistencias a ON a.cliente_id = c.id
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE ct.estado = 'activo' AND a.estado = 'asistio'
            GROUP BY c.id
            HAVING MAX(s.fecha) < CURRENT_DATE - interval '14 days'
        """, TENANT) or 0

        # Deuda pendiente total
        deuda = await conn.fetchrow("""
            SELECT count(DISTINCT cliente_id) as clientes,
                   COALESCE(SUM(total), 0) as total
            FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
                AND fecha_cargo < CURRENT_DATE - interval '30 days'
        """, TENANT)

        # Clientes totales activos
        total_clientes = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT) or 0

        # Últimas altas (últimos 30 días)
        altas_recientes = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_alta > CURRENT_DATE - interval '30 days'
        """, TENANT) or 0

        # Últimas bajas (últimos 30 días)
        bajas_recientes = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_baja IS NOT NULL
                AND fecha_baja > CURRENT_DATE - interval '30 days'
        """, TENANT) or 0

    return {
        "ocupacion_pct": ocupacion_pct,
        "total_plazas": total_cap,
        "plazas_ocupadas": total_ocu,
        "grupos_baja_ocupacion": grupos_bajos,
        "clientes_inactivos_14d": inactivos,
        "deuda_pendiente": {
            "clientes": deuda["clientes"] if deuda else 0,
            "total_eur": float(deuda["total"]) if deuda else 0,
        },
        "clientes_activos": total_clientes,
        "altas_30d": altas_recientes,
        "bajas_30d": bajas_recientes,
        "fecha": str(date.today()),
    }


# ============================================================
# RECOGER DATOS DE LOS 3 EJES
# ============================================================

async def _recoger_eje1_irc() -> list[dict]:
    """Eje 1: IRC de cada canal, ordenado por score."""
    from src.pilates.voz_identidad import obtener_irc
    return await obtener_irc()


async def _recoger_eje2_posicion() -> dict:
    """Eje 2: Posición en la Matriz 3Lx7F.

    Intenta leer el último diagnóstico ACD del tenant.
    Si no hay diagnóstico, devuelve posición por defecto estimada.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Buscar último diagnóstico ACD si existe
        diag = None
        try:
            diag = await conn.fetchrow("""
                SELECT estado_id, vector_lentes, gap, prescripcion,
                       created_at
                FROM diagnosticos
                ORDER BY created_at DESC LIMIT 1
            """)
        except Exception:
            pass

    if diag and diag["estado_id"]:
        return {
            "estado_acd": diag["estado_id"],
            "vector_lentes": diag["vector_lentes"] if diag["vector_lentes"] else {},
            "gap": float(diag["gap"]) if diag["gap"] else None,
            "prescripcion": diag["prescripcion"] if diag["prescripcion"] else {},
            "fuente": "diagnostico_acd",
            "fecha_diagnostico": str(diag["created_at"].date()) if diag["created_at"] else None,
        }
    else:
        # Sin diagnóstico ACD -> posición estimada basada en datos operativos
        senales = await _recoger_senales_internas()
        ocu = senales["ocupacion_pct"]

        if ocu > 85:
            foco = "salud_conservar"
            estado = "E2"
        elif ocu > 60:
            foco = "salud_potenciar"
            estado = "E1"
        elif ocu > 40:
            foco = "sentido_captar"
            estado = "E3"
        else:
            foco = "continuidad_captar"
            estado = "operador_ciego"

        return {
            "estado_acd": estado,
            "foco_estimado": foco,
            "fuente": "heuristica_ocupacion",
            "ocupacion_pct": ocu,
            "nota": "Sin diagnóstico ACD formal. Posición estimada por ocupación.",
        }


async def _recoger_eje3_pca() -> list[dict]:
    """Eje 3: Perfil de Consumo de Audiencia de todos los segmentos."""
    from src.pilates.voz_identidad import obtener_pca
    return await obtener_pca()


async def _recoger_identidad_resumen() -> dict:
    """Resumen de identidad para el prompt (no todo el registro)."""
    from src.pilates.voz_identidad import obtener_identidad
    ident = await obtener_identidad()
    if "error" in ident:
        return ident

    return {
        "nombre": ident.get("nombre_estudio"),
        "propuesta_valor": ident.get("propuesta_valor"),
        "tono": ident.get("tono"),
        "personalidad": ident.get("personalidad"),
        "target_primario": ident.get("target_primario"),
        "palabras_prohibidas": ident.get("palabras_prohibidas"),
        "lo_que_nunca_decir": ident.get("lo_que_nunca_decir"),
    }


async def _recoger_competidores_resumen() -> list[dict]:
    """Resumen de competidores para el prompt."""
    from src.pilates.voz_identidad import obtener_competidores
    comps = await obtener_competidores()
    return [
        {
            "nombre": c.get("nombre"),
            "debilidades": c.get("debilidades"),
            "oportunidad": c.get("oportunidad_para_nosotros"),
        }
        for c in comps
    ]


def _contexto_estacional() -> dict:
    """Contexto estacional basado en la fecha actual."""
    hoy = date.today()
    mes = hoy.month

    estaciones = {
        1: {"periodo": "post_navidad", "nota": "Propósitos de año nuevo. Pico de interés en empezar actividades. Captar."},
        2: {"periodo": "invierno", "nota": "Frío, menos motivación. Retener. Contenido de mantenimiento."},
        3: {"periodo": "pre_primavera", "nota": "Empieza a subir interés. Buen momento para captar."},
        4: {"periodo": "primavera", "nota": "Alta demanda. Llenar huecos."},
        5: {"periodo": "primavera_alta", "nota": "Demanda sostenida. Consolidar."},
        6: {"periodo": "pre_verano", "nota": "Comienzan cancelaciones por vacaciones. Retener."},
        7: {"periodo": "verano_bajo", "nota": "Mínimo anual. No invertir en captación. Mantenimiento."},
        8: {"periodo": "verano_bajo", "nota": "Mínimo. Preparar septiembre."},
        9: {"periodo": "vuelta", "nota": "Pico de altas. Máxima captación. Grupos nuevos."},
        10: {"periodo": "otono", "nota": "Consolidar nuevas altas. Fidelizar."},
        11: {"periodo": "otono_tardio", "nota": "Estable. Preparar navidad."},
        12: {"periodo": "pre_navidad", "nota": "Cancelaciones por fiestas. Retener. Felicitar."},
    }
    return estaciones.get(mes, {"periodo": "desconocido", "nota": ""})


# ============================================================
# CALCULAR ESTRATEGIA (motor principal)
# ============================================================

SYSTEM_PROMPT_ESTRATEGIA = """Eres el Motor Tridimensional del Bloque Voz de OMNI-MIND.

Tu trabajo: generar la ESTRATEGIA DE COMUNICACIÓN semanal para un negocio pequeño (SMB) basándote en 3 ejes cruzados:

**Eje 1 — IRC (DÓNDE publicar):**
Cada canal tiene un score IRC de 0 a 1. Prioriza canales con mayor IRC.
NO propongas contenido para canales con IRC < 0.3.

**Eje 2 — Posición en Matriz 3Lx7F (CON QUÉ INTENCIÓN):**
El estado ACD del negocio determina el ángulo:
- E1/E2 (equilibrado alto) -> Conservar + potenciar. Contenido de resultados y confianza.
- E3/E4 (equilibrado bajo) -> Captar + educar. Contenido de atracción y valor.
- operador_ciego -> Necesita sentido. Contenido de identidad y diferenciación.
- genio_mortal -> Necesita sistema. Contenido de proceso y comunidad.
- automata_eterno -> Necesita renovación. Contenido de innovación.

**Eje 3 — PCA (CÓMO hablarle a la audiencia):**
Formato, tono, temas, horarios y lenguaje que resuena con cada segmento.
NUNCA uses lenguaje o temas que el PCA marca como "que no".
SIEMPRE usa el tono y formato que el PCA marca como preferido.

**Reglas:**
1. Toda propuesta debe tener justificación cruzada de los 3 ejes.
2. Propón 5-8 piezas de contenido para la semana.
3. Cada pieza: canal, tipo, título, contenido sugerido, día/hora, y justificación de 3 ejes.
4. Incluye un FOCO principal (1 palabra: educar/captar/retener/fidelizar/activar/depurar).
5. Incluye una NARRATIVA (2-3 frases que definen la línea de comunicación de la semana).
6. Respeta la identidad del negocio: tono, personalidad, lo que nunca decir, palabras prohibidas.
7. Si hay señales tácticas urgentes (deuda, inactivos, ocupación baja), intégralas en la estrategia.
8. Aprovecha oportunidades de competidores si las hay.

Responde SOLO en JSON válido con esta estructura:
{
  "foco_principal": "...",
  "foco_secundario": "...",
  "narrativa": "...",
  "canales_prioridad": ["...", "..."],
  "evitar": ["..."],
  "calendario": [
    {
      "canal": "whatsapp|google_business|instagram|facebook|web",
      "tipo_contenido": "broadcast_wa|estado_wa|post_google|respuesta_resena|carrusel|reel|story|post",
      "titulo": "...",
      "contenido": "... (texto completo o guion del contenido)",
      "visual_sugerido": "... (descripción de imagen/video si aplica)",
      "cta": "... (llamada a acción)",
      "dia": "lunes|martes|...",
      "hora": "HH:MM",
      "eje1_justificacion": "... (por qué este canal)",
      "eje2_justificacion": "... (por qué esta intención)",
      "eje3_justificacion": "... (por qué este formato/tono/tema)"
    }
  ]
}"""


async def calcular_estrategia() -> dict:
    """Calcula la estrategia semanal cruzando los 3 ejes.

    1. Recoge datos de los 3 ejes + señales internas + identidad
    2. Construye prompt contextualizado
    3. Llama a LLM (deepseek-chat via OpenRouter)
    4. Parsea respuesta y almacena en om_voz_estrategia + om_voz_calendario

    Returns: dict con estrategia + calendario generados.
    """
    # 1. Recoger todo
    senales = await _recoger_senales_internas()
    irc = await _recoger_eje1_irc()
    posicion = await _recoger_eje2_posicion()
    pca = await _recoger_eje3_pca()
    identidad = await _recoger_identidad_resumen()
    competidores = await _recoger_competidores_resumen()
    estacional = _contexto_estacional()

    if "error" in identidad:
        return {"error": "Identidad no seedeada. Ejecutar POST /pilates/voz/seed primero."}

    # 2. Construir prompt
    semana_actual = date.today().isocalendar()
    semana_str = f"{semana_actual[0]}-W{semana_actual[1]:02d}"

    user_prompt = f"""Genera la estrategia de comunicación para la semana {semana_str}.

## IDENTIDAD DEL NEGOCIO
{json.dumps(identidad, ensure_ascii=False, indent=2)}

## EJE 1 — IRC (canales ordenados por prioridad)
{json.dumps(irc, ensure_ascii=False, indent=2, default=str)}

## EJE 2 — POSICIÓN ESTRATÉGICA
{json.dumps(posicion, ensure_ascii=False, indent=2, default=str)}

## EJE 3 — PCA (perfil de consumo de audiencia)
{json.dumps(pca, ensure_ascii=False, indent=2, default=str)}

## SEÑALES INTERNAS (Capa B)
{json.dumps(senales, ensure_ascii=False, indent=2)}

## CONTEXTO ESTACIONAL
{json.dumps(estacional, ensure_ascii=False)}

## COMPETIDORES
{json.dumps(competidores, ensure_ascii=False, indent=2)}

Genera la estrategia semanal en JSON."""

    # 3. Llamar a LLM
    import httpx
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_key:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "HTTP-Referer": "https://motor-semantico-omni.fly.dev",
                },
                json={
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT_ESTRATEGIA},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]

    except Exception as e:
        log.error("voz_estrategia_llm_error", error=str(e))
        return {"error": f"LLM call failed: {e}"}

    # 4. Parsear JSON (tolerante a markdown fences)
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()

    try:
        estrategia = json.loads(clean)
    except json.JSONDecodeError as e:
        log.error("voz_estrategia_parse_error", raw=raw[:500], error=str(e))
        return {"error": "LLM response not valid JSON", "raw": raw[:500]}

    # 5. Almacenar estrategia
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Desactivar estrategia anterior
        await conn.execute("""
            UPDATE om_voz_estrategia SET activa = FALSE
            WHERE tenant_id = $1 AND activa = TRUE
        """, TENANT)

        # Insertar nueva estrategia
        await conn.execute("""
            INSERT INTO om_voz_estrategia (
                tenant_id, estado_acd, lentes, contexto_mercado,
                contexto_estacional, ocupacion_pct, irc_snapshot, pca_snapshot,
                foco_principal, foco_secundario, narrativa,
                canales_prioridad, evitar, prescripciones, activa
            ) VALUES (
                $1, $2, $3::jsonb, $4, $5, $6, $7::jsonb, $8::jsonb,
                $9, $10, $11, $12::jsonb, $13::jsonb, $14::jsonb, TRUE
            )
        """,
            TENANT,
            posicion.get("estado_acd"),
            json.dumps(posicion.get("vector_lentes", {})),
            f"Competidores: {len(competidores)}. Oportunidades detectadas.",
            estacional.get("nota", ""),
            senales["ocupacion_pct"],
            json.dumps([{"canal": c["canal"], "irc": float(c["irc_score"])} for c in irc], default=str),
            json.dumps([{"segmento": p["segmento"]} for p in pca], default=str),
            estrategia.get("foco_principal", "educar"),
            estrategia.get("foco_secundario"),
            estrategia.get("narrativa"),
            json.dumps(estrategia.get("canales_prioridad", [])),
            json.dumps(estrategia.get("evitar", [])),
            json.dumps(estrategia.get("calendario", [])),
        )

        # 6. Almacenar calendario semanal
        calendario = estrategia.get("calendario", [])
        dias_map = {
            "lunes": 0, "martes": 1, "miercoles": 2, "miércoles": 2,
            "jueves": 3, "viernes": 4, "sabado": 5, "sábado": 5, "domingo": 6,
        }

        # Calcular fecha del lunes de esta semana
        hoy = date.today()
        lunes = hoy - timedelta(days=hoy.weekday())

        items_creados = 0
        for item in calendario:
            dia_nombre = item.get("dia", "").lower()
            dia_offset = dias_map.get(dia_nombre)
            fecha_pub = lunes + timedelta(days=dia_offset) if dia_offset is not None else None

            hora_pub = None
            hora_str = item.get("hora", "")
            if hora_str and ":" in hora_str:
                try:
                    from datetime import time as dt_time
                    parts = hora_str.split(":")
                    hora_pub = dt_time(int(parts[0]), int(parts[1]))
                except (ValueError, IndexError):
                    pass

            # Buscar IRC del canal
            irc_canal = next((c["irc_score"] for c in irc if c["canal"] == item.get("canal")), None)

            await conn.execute("""
                INSERT INTO om_voz_calendario (
                    tenant_id, semana, canal, tipo_contenido,
                    dia_publicacion, hora_publicacion,
                    titulo, contenido, visual_sugerido, cta,
                    eje1_irc, eje2_posicion, eje3_formato_pca,
                    justificacion, estado
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                    $11, $12, $13, $14, 'planificado'
                )
            """,
                TENANT, semana_str,
                item.get("canal", "whatsapp"),
                item.get("tipo_contenido", "contenido"),
                fecha_pub, hora_pub,
                item.get("titulo"),
                item.get("contenido"),
                item.get("visual_sugerido"),
                item.get("cta"),
                float(irc_canal) if irc_canal else None,
                posicion.get("estado_acd"),
                item.get("eje3_justificacion"),
                f"E1: {item.get('eje1_justificacion', '')} | E2: {item.get('eje2_justificacion', '')} | E3: {item.get('eje3_justificacion', '')}",
            )
            items_creados += 1

    log.info("voz_estrategia_calculada",
             foco=estrategia.get("foco_principal"),
             items=items_creados)

    return {
        "status": "ok",
        "semana": semana_str,
        "estrategia": {
            "foco_principal": estrategia.get("foco_principal"),
            "foco_secundario": estrategia.get("foco_secundario"),
            "narrativa": estrategia.get("narrativa"),
            "canales_prioridad": estrategia.get("canales_prioridad"),
            "evitar": estrategia.get("evitar"),
        },
        "calendario_items": items_creados,
    }


# ============================================================
# CONSULTAS
# ============================================================

async def obtener_estrategia_activa() -> dict:
    """Devuelve la estrategia activa con su calendario."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        est = await conn.fetchrow("""
            SELECT * FROM om_voz_estrategia
            WHERE tenant_id = $1 AND activa = TRUE
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        if not est:
            return {"error": "No hay estrategia activa. Ejecutar POST /pilates/voz/estrategia/calcular"}

        # Obtener calendario de la semana actual
        semana = date.today().isocalendar()
        semana_str = f"{semana[0]}-W{semana[1]:02d}"

        calendario = await conn.fetch("""
            SELECT * FROM om_voz_calendario
            WHERE tenant_id = $1 AND semana = $2
            ORDER BY dia_publicacion, hora_publicacion
        """, TENANT, semana_str)

    return {
        "estrategia": {
            "foco_principal": est["foco_principal"],
            "foco_secundario": est["foco_secundario"],
            "narrativa": est["narrativa"],
            "canales_prioridad": est["canales_prioridad"],
            "evitar": est["evitar"],
            "estado_acd": est["estado_acd"],
            "ocupacion_pct": float(est["ocupacion_pct"]) if est["ocupacion_pct"] else None,
            "created_at": str(est["created_at"]),
        },
        "calendario": [
            {
                "id": str(c["id"]),
                "canal": c["canal"],
                "tipo": c["tipo_contenido"],
                "titulo": c["titulo"],
                "contenido": c["contenido"],
                "visual": c["visual_sugerido"],
                "cta": c["cta"],
                "dia": str(c["dia_publicacion"]) if c["dia_publicacion"] else None,
                "hora": str(c["hora_publicacion"]) if c["hora_publicacion"] else None,
                "estado": c["estado"],
                "justificacion": c["justificacion"],
            }
            for c in calendario
        ],
    }


async def aprobar_item_calendario(item_id: str) -> dict:
    """Aprueba un item del calendario (Jesús aprueba en cockpit)."""
    from uuid import UUID
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_voz_calendario
            SET estado = 'aprobado', aprobado_por = 'jesus'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'planificado'
        """, UUID(item_id), TENANT)

        if result == "UPDATE 0":
            return {"error": "Item no encontrado o ya aprobado/publicado"}

    return {"status": "aprobado", "id": item_id}


async def descartar_item_calendario(item_id: str) -> dict:
    """Descarta un item del calendario."""
    from uuid import UUID
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_voz_calendario
            SET estado = 'descartado'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'planificado'
        """, UUID(item_id), TENANT)

        if result == "UPDATE 0":
            return {"error": "Item no encontrado o ya procesado"}

    return {"status": "descartado", "id": item_id}
