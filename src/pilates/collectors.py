"""Collectors — Pull automático de métricas de canales.

Conecta Meta Graph API (Instagram/Facebook), Google Business Profile,
y WhatsApp Business API para alimentar el ciclo APRENDER del Bloque Voz.

Los datos se persisten via registrar_telemetria() de voz_ciclos.py
y actualizan el IRC automáticamente.
"""
from __future__ import annotations

import json
import os
import structlog
from datetime import date, timedelta

log = structlog.get_logger()

TENANT = "authentic_pilates"


# ============================================================
# 1. INSTAGRAM COLLECTOR (Meta Graph API)
# ============================================================

async def collect_instagram() -> dict:
    """Pull métricas de Instagram via Meta Graph API.

    Recoge:
    - Métricas de cuenta: reach, impressions, profile_views, website_clicks
    - Métricas de media reciente: engagement, saves, shares por post
    - Demographics: edad, género, ubicación, horarios activos de followers
    - Follower count actual

    Requiere: META_ACCESS_TOKEN + INSTAGRAM_BUSINESS_ACCOUNT_ID
    """
    token = os.getenv("META_ACCESS_TOKEN")
    ig_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

    if not token or not ig_id:
        log.debug("collector_ig_skip", reason="sin credenciales")
        return {"status": "skip", "reason": "META_ACCESS_TOKEN o INSTAGRAM_BUSINESS_ACCOUNT_ID no configurados"}

    import httpx
    base = f"https://graph.facebook.com/v19.0/{ig_id}"
    headers = {"Authorization": f"Bearer {token}"}

    resultado = {
        "canal": "instagram",
        "fecha": str(date.today()),
        "metricas": {},
        "demographics": {},
        "errors": [],
    }

    async with httpx.AsyncClient(timeout=30) as client:
        # -- Métricas de cuenta (últimos 28 días) --
        try:
            resp = await client.get(
                f"{base}/insights",
                headers=headers,
                params={
                    "metric": "reach,impressions,profile_views,website_clicks,"
                              "accounts_engaged,follows_and_unfollows",
                    "period": "day",
                    "since": str(date.today() - timedelta(days=7)),
                    "until": str(date.today()),
                },
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                for metric in data:
                    name = metric["name"]
                    values = metric.get("values", [])
                    total = sum(v.get("value", 0) for v in values if isinstance(v.get("value"), (int, float)))
                    resultado["metricas"][name] = total
            else:
                resultado["errors"].append(f"insights: {resp.status_code}")
        except Exception as e:
            resultado["errors"].append(f"insights: {str(e)[:100]}")

        # -- Follower count --
        try:
            resp = await client.get(
                f"{base}",
                headers=headers,
                params={"fields": "followers_count,media_count"},
            )
            if resp.status_code == 200:
                data = resp.json()
                resultado["metricas"]["followers_count"] = data.get("followers_count", 0)
                resultado["metricas"]["media_count"] = data.get("media_count", 0)
        except Exception as e:
            resultado["errors"].append(f"profile: {str(e)[:100]}")

        # -- Media reciente (últimos 10 posts) --
        try:
            resp = await client.get(
                f"{base}/media",
                headers=headers,
                params={
                    "fields": "id,media_type,timestamp,like_count,comments_count",
                    "limit": 10,
                },
            )
            if resp.status_code == 200:
                media_list = resp.json().get("data", [])
                total_likes = sum(m.get("like_count", 0) for m in media_list)
                total_comments = sum(m.get("comments_count", 0) for m in media_list)
                resultado["metricas"]["media_reciente"] = len(media_list)
                resultado["metricas"]["likes_recientes"] = total_likes
                resultado["metricas"]["comments_recientes"] = total_comments

                # Engagement medio
                if media_list and resultado["metricas"].get("followers_count", 0) > 0:
                    avg_eng = (total_likes + total_comments) / len(media_list)
                    resultado["metricas"]["engagement_medio"] = round(
                        avg_eng / resultado["metricas"]["followers_count"] * 100, 2)
        except Exception as e:
            resultado["errors"].append(f"media: {str(e)[:100]}")

        # -- Demographics (followers) --
        try:
            for metric_name in ["follower_demographics"]:
                resp = await client.get(
                    f"{base}/insights",
                    headers=headers,
                    params={
                        "metric": metric_name,
                        "period": "lifetime",
                        "metric_type": "total_value",
                        "breakdown": "city",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", [])
                    if data:
                        resultado["demographics"]["cities"] = data[0].get("total_value", {}).get("breakdowns", [])

            # Age + gender
            resp = await client.get(
                f"{base}/insights",
                headers=headers,
                params={
                    "metric": "follower_demographics",
                    "period": "lifetime",
                    "metric_type": "total_value",
                    "breakdown": "age,gender",
                },
            )
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                if data:
                    resultado["demographics"]["age_gender"] = data[0].get("total_value", {}).get("breakdowns", [])

        except Exception as e:
            resultado["errors"].append(f"demographics: {str(e)[:100]}")

    # Persistir via telemetría
    if resultado["metricas"]:
        from src.pilates.voz_ciclos import registrar_telemetria
        periodo = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}"
        await registrar_telemetria("instagram", periodo, {
            "leads_generados": resultado["metricas"].get("profile_views", 0),
            "reservas_directas": 0,  # No se puede medir directo desde IG
            "conversiones_cliente": 0,
            "contenido_publicado": resultado["metricas"].get("media_reciente", 0),
            "engagement_medio": resultado["metricas"].get("engagement_medio"),
            "primer_contacto_pct": None,
        })

    log.info("collector_ig_ok",
             reach=resultado["metricas"].get("reach", 0),
             engagement=resultado["metricas"].get("engagement_medio"),
             errors=len(resultado["errors"]))

    return resultado


# ============================================================
# 2. GOOGLE BUSINESS PROFILE COLLECTOR
# ============================================================

async def collect_gbp() -> dict:
    """Pull métricas de Google Business Profile.

    Recoge:
    - Búsquedas: directas, indirectas (discovery)
    - Acciones: clics web, llamadas, direcciones
    - Vistas: en Search y Maps

    Requiere: GOOGLE_SERVICE_ACCOUNT_JSON + GBP_LOCATION_ID
    """
    sa_json_b64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    location_id = os.getenv("GBP_LOCATION_ID")

    if not sa_json_b64 or not location_id:
        log.debug("collector_gbp_skip", reason="sin credenciales")
        return {"status": "skip", "reason": "GOOGLE_SERVICE_ACCOUNT_JSON o GBP_LOCATION_ID no configurados"}

    import base64
    import httpx

    resultado = {
        "canal": "google_business",
        "fecha": str(date.today()),
        "metricas": {},
        "search_keywords": [],
        "errors": [],
    }

    try:
        # Obtener access token via service account
        sa_json = json.loads(base64.b64decode(sa_json_b64))
        access_token = await _get_google_access_token(sa_json)

        headers = {"Authorization": f"Bearer {access_token}"}
        api_base = "https://businessprofileperformance.googleapis.com/v1"

        # -- Daily metrics (últimos 7 días) --
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{api_base}/{location_id}:fetchMultiDailyMetricsTimeSeries",
                headers=headers,
                params={
                    "dailyMetrics": [
                        "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
                        "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
                        "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
                        "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
                        "WEBSITE_CLICKS",
                        "CALL_CLICKS",
                        "BUSINESS_DIRECTION_REQUESTS",
                    ],
                    "dailyRange.startDate.year": start_date.year,
                    "dailyRange.startDate.month": start_date.month,
                    "dailyRange.startDate.day": start_date.day,
                    "dailyRange.endDate.year": end_date.year,
                    "dailyRange.endDate.month": end_date.month,
                    "dailyRange.endDate.day": end_date.day,
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                for series in data.get("multiDailyMetricTimeSeries", []):
                    for ts in series.get("dailyMetricTimeSeries", []):
                        metric = ts.get("dailyMetric", "")
                        values = ts.get("timeSeries", {}).get("datedValues", [])
                        total = sum(int(v.get("value", 0)) for v in values)
                        resultado["metricas"][metric.lower()] = total
            else:
                resultado["errors"].append(f"metrics: {resp.status_code}")

            # -- Search keywords --
            resp = await client.get(
                f"{api_base}/{location_id}/searchkeywords/impressions/monthly",
                headers=headers,
                params={
                    "monthlyRange.startMonth.year": start_date.year,
                    "monthlyRange.startMonth.month": start_date.month,
                    "monthlyRange.endMonth.year": end_date.year,
                    "monthlyRange.endMonth.month": end_date.month,
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                keywords = data.get("searchKeywordsCounts", [])
                resultado["search_keywords"] = [
                    {"keyword": kw.get("searchKeyword", ""),
                     "count": int(kw.get("insightsValue", {}).get("value", 0))}
                    for kw in keywords[:20]
                ]

    except Exception as e:
        resultado["errors"].append(f"gbp: {str(e)[:200]}")

    # Persistir via telemetría
    if resultado["metricas"]:
        from src.pilates.voz_ciclos import registrar_telemetria
        periodo = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}"

        web_clicks = resultado["metricas"].get("website_clicks", 0)
        calls = resultado["metricas"].get("call_clicks", 0)

        await registrar_telemetria("google_business", periodo, {
            "leads_generados": web_clicks + calls,
            "reservas_directas": calls,  # Llamadas = intención directa
            "conversiones_cliente": 0,
            "engagement_medio": None,
        })

    # Persistir keywords en om_voz_capa_a
    if resultado["search_keywords"]:
        from src.db.client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_voz_capa_a
                    (tenant_id, fuente, tipo_dato, datos, fecha_dato, funcion_l07)
                VALUES ($1, 'gbp_api', 'search_keywords', $2::jsonb, CURRENT_DATE, 'F2')
            """, TENANT,
                json.dumps({
                    "keywords": resultado["search_keywords"][:10],
                    "total": len(resultado["search_keywords"]),
                }, ensure_ascii=False))

    log.info("collector_gbp_ok",
             impressions=sum(v for k, v in resultado["metricas"].items() if "impression" in k),
             clicks=resultado["metricas"].get("website_clicks", 0),
             keywords=len(resultado["search_keywords"]),
             errors=len(resultado["errors"]))

    return resultado


async def _get_google_access_token(sa_json: dict) -> str:
    """Obtiene access token de Google via service account JWT."""
    import time
    import httpx

    # Crear JWT
    header = {"alg": "RS256", "typ": "JWT"}
    now = int(time.time())
    claim = {
        "iss": sa_json["client_email"],
        "scope": "https://www.googleapis.com/auth/business.manage",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    }

    # Sign JWT with private key
    import jwt  # PyJWT
    token = jwt.encode(claim, sa_json["private_key"], algorithm="RS256", headers=header)

    # Exchange JWT for access token
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": token,
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]


# ============================================================
# 3. WHATSAPP ANALYTICS COLLECTOR
# ============================================================

async def collect_whatsapp() -> dict:
    """Pull métricas de WhatsApp Business via Management API.

    Recoge:
    - Conversaciones: iniciadas por negocio vs usuario
    - Mensajes: enviados, entregados, leídos
    - Templates: rendimiento por template

    Usa las mismas credenciales que whatsapp.py
    """
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_ID")

    if not token or not phone_id:
        log.debug("collector_wa_skip", reason="sin credenciales")
        return {"status": "skip", "reason": "WHATSAPP_TOKEN no configurado"}

    resultado = {
        "canal": "whatsapp",
        "fecha": str(date.today()),
        "metricas": {},
        "errors": [],
    }

    # Calcular métricas desde nuestra propia DB (más fiable que API analytics)
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Mensajes últimos 7 días
        stats = await conn.fetchrow("""
            SELECT
                count(*) FILTER (WHERE direccion = 'entrante') as recibidos,
                count(*) FILTER (WHERE direccion = 'saliente') as enviados,
                count(*) FILTER (WHERE direccion = 'entrante' AND intencion IN ('consulta_precio', 'reserva')) as leads,
                count(*) FILTER (WHERE direccion = 'entrante' AND intencion = 'reserva') as reservas,
                count(*) FILTER (WHERE direccion = 'entrante' AND cliente_id IS NULL) as desconocidos,
                count(DISTINCT CASE WHEN direccion = 'entrante' THEN remitente END) as contactos_unicos
            FROM om_mensajes_wa
            WHERE tenant_id = $1
                AND created_at > now() - interval '7 days'
        """, TENANT)

        if stats:
            resultado["metricas"] = {
                "mensajes_recibidos": stats["recibidos"] or 0,
                "mensajes_enviados": stats["enviados"] or 0,
                "leads_wa": stats["leads"] or 0,
                "reservas_wa": stats["reservas"] or 0,
                "contactos_desconocidos": stats["desconocidos"] or 0,
                "contactos_unicos": stats["contactos_unicos"] or 0,
            }

            # Tasa de respuesta (enviados / recibidos)
            if stats["recibidos"] and stats["recibidos"] > 0:
                resultado["metricas"]["tasa_respuesta"] = round(
                    (stats["enviados"] or 0) / stats["recibidos"] * 100, 1)

    # Persistir via telemetría
    if resultado["metricas"]:
        from src.pilates.voz_ciclos import registrar_telemetria
        periodo = f"{date.today().isocalendar()[0]}-W{date.today().isocalendar()[1]:02d}"
        await registrar_telemetria("whatsapp", periodo, {
            "leads_generados": resultado["metricas"].get("leads_wa", 0),
            "reservas_directas": resultado["metricas"].get("reservas_wa", 0),
            "conversiones_cliente": 0,
            "mensajes_respondidos": resultado["metricas"].get("mensajes_enviados", 0),
            "tasa_respuesta": resultado["metricas"].get("tasa_respuesta"),
        })

    log.info("collector_wa_ok",
             recibidos=resultado["metricas"].get("mensajes_recibidos", 0),
             leads=resultado["metricas"].get("leads_wa", 0))

    return resultado


# ============================================================
# 4. ORQUESTADOR — Ejecuta todos los collectors
# ============================================================

async def collect_all() -> dict:
    """Ejecuta todos los collectors y devuelve resumen.

    Se llama desde:
    - cron.py tarea diaria (automático)
    - voz_ciclos.py escuchar() (semanal)
    - cockpit (bajo demanda)
    """
    resultados = {}

    # Instagram
    try:
        resultados["instagram"] = await collect_instagram()
    except Exception as e:
        log.error("collector_ig_exception", error=str(e))
        resultados["instagram"] = {"status": "error", "error": str(e)[:100]}

    # Google Business Profile
    try:
        resultados["google_business"] = await collect_gbp()
    except Exception as e:
        log.error("collector_gbp_exception", error=str(e))
        resultados["google_business"] = {"status": "error", "error": str(e)[:100]}

    # WhatsApp
    try:
        resultados["whatsapp"] = await collect_whatsapp()
    except Exception as e:
        log.error("collector_wa_exception", error=str(e))
        resultados["whatsapp"] = {"status": "error", "error": str(e)[:100]}

    # Recalcular IRC con datos frescos
    try:
        from src.pilates.voz_ciclos import recalcular_irc
        irc = await recalcular_irc()
        resultados["irc_recalculado"] = irc
    except Exception as e:
        log.error("collector_irc_exception", error=str(e))

    canales = ["instagram", "google_business", "whatsapp"]
    activos = sum(1 for k in canales
                  if isinstance(resultados.get(k), dict)
                  and resultados[k].get("status") != "skip"
                  and "error" not in resultados[k])

    log.info("collectors_completo", activos=activos, total=3)

    return {
        "status": "ok",
        "collectors_activos": activos,
        "collectors_total": 3,
        "detalle": {k: {
            "status": v.get("status", "ok") if isinstance(v, dict) else "error",
            "metricas": len(v.get("metricas", {})) if isinstance(v, dict) else 0,
        } for k, v in resultados.items() if k != "irc_recalculado"},
    }
