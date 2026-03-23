"""Arquitecto de Presencia — Bloque Voz Estratégico.

Genera la configuración completa de cada perfil digital:
- WhatsApp Business: descripción, catálogo, bienvenida, respuestas rápidas
- Google Business: descripción, servicios, Q&A, posts iniciales
- Instagram: bio, highlights, primeros posts, hashtags
- Facebook: acerca de, CTA, post fijado

Todo contextualizado por los 3 ejes del Motor Tridimensional.
Para cada elemento genera:
- contenido listo para aplicar
- instrucciones paso a paso si requiere acción manual

Basado en B2.8 v3.0 §3.2 — Arquitecto de Presencia.
"""
from __future__ import annotations

import os
import json
import structlog
from datetime import date

log = structlog.get_logger()
TENANT = "authentic_pilates"
STRATEGY_MODEL = os.getenv("STRATEGY_MODEL", "openai/gpt-4o")


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


# ============================================================
# CONTEXTO COMPARTIDO (reusa funciones de 20a/20b)
# ============================================================

async def _contexto_para_prompt() -> dict:
    """Recoge todo el contexto necesario para generar perfiles."""
    from src.pilates.voz_identidad import (
        obtener_identidad, obtener_irc, obtener_pca, obtener_competidores,
    )
    from src.pilates.voz_estrategia import _recoger_eje2_posicion

    identidad = await obtener_identidad()
    if "error" in identidad:
        return {"error": identidad["error"]}

    irc = await obtener_irc()
    pca = await obtener_pca()
    competidores = await obtener_competidores()
    posicion = await _recoger_eje2_posicion()

    return {
        "identidad": {
            "nombre": identidad.get("nombre_estudio"),
            "ubicacion": identidad.get("ubicacion"),
            "metodo": identidad.get("metodo_escuela"),
            "propuesta_valor": identidad.get("propuesta_valor"),
            "diferenciadores": identidad.get("diferenciadores"),
            "tono": identidad.get("tono"),
            "personalidad": identidad.get("personalidad"),
            "target_primario": identidad.get("target_primario"),
            "target_secundario": identidad.get("target_secundario"),
            "confusiones_comunes": identidad.get("confusiones_comunes"),
            "barreras_entrada": identidad.get("barreras_entrada"),
            "palabras_clave": identidad.get("palabras_clave"),
            "palabras_prohibidas": identidad.get("palabras_prohibidas"),
            "lo_que_nunca_decir": identidad.get("lo_que_nunca_decir"),
            "principios_comunicacion": identidad.get("principios_comunicacion"),
        },
        "irc": [{"canal": c["canal"], "score": float(c["irc_score"])} for c in irc],
        "pca": [
            {
                "segmento": p["segmento"],
                "formato_preferido": p.get("formato_preferido"),
                "tono_que_resuena": p.get("tono_que_resuena"),
                "temas_que_enganchan": p.get("temas_que_enganchan"),
                "lenguaje_real": p.get("lenguaje_real"),
                "horarios_consumo": p.get("horarios_consumo"),
            }
            for p in pca
        ],
        "posicion": posicion,
        "competidores": [
            {
                "nombre": c.get("nombre"),
                "debilidades": c.get("debilidades"),
                "oportunidad": c.get("oportunidad_para_nosotros"),
            }
            for c in competidores
        ],
    }


# ============================================================
# SYSTEM PROMPTS POR CANAL
# ============================================================

SYSTEM_BASE = """Eres el Arquitecto de Presencia de OMNI-MIND.
Tu trabajo: generar la configuración COMPLETA del perfil de un negocio en un canal digital.

REGLAS ABSOLUTAS:
- Usa SOLO el lenguaje real que la audiencia usa (dato del PCA)
- NUNCA uses palabras prohibidas del negocio
- NUNCA incluyas precios en contenido público de redes
- NUNCA incluyas horarios exactos en redes — que contacten
- El tono debe ser el de la identidad del negocio: cercano, de pueblo, sin formalismos
- Cada elemento debe estar justificado por al menos 1 eje (IRC, posición matricial, PCA)
- Incluye instrucciones paso a paso para que el dueño aplique cada cambio

Responde SOLO en JSON válido."""

PROMPT_WHATSAPP = SYSTEM_BASE + """

Genera la configuración completa de WhatsApp Business con esta estructura JSON:
{
  "descripcion": "... (max 256 chars, con lenguaje de audiencia)",
  "catalogo": [
    {"nombre": "...", "descripcion": "...", "precio_visible": false}
  ],
  "mensaje_bienvenida": "... (para contacto nuevo, max 1024 chars)",
  "mensaje_ausencia": "... (fuera de horario)",
  "respuestas_rapidas": [
    {"atajo": "/...", "mensaje": "..."}
  ],
  "etiquetas": ["..."],
  "instrucciones": [
    {"paso": 1, "accion": "...", "donde": "WhatsApp Business > Ajustes > ..."}
  ]
}"""

PROMPT_GOOGLE = SYSTEM_BASE + """

Genera la configuración completa de Google Business Profile con esta estructura JSON:
{
  "descripcion": "... (max 750 chars, incluir queries reales de audiencia)",
  "categoria_primaria": "...",
  "categorias_secundarias": ["..."],
  "servicios": [
    {"nombre": "...", "descripcion": "..."}
  ],
  "qya_prellenadas": [
    {"pregunta": "...", "respuesta": "..."}
  ],
  "posts_iniciales": [
    {"tipo": "novedad|oferta|evento", "titulo": "...", "contenido": "...", "cta": "..."}
  ],
  "fotos_sugeridas": [
    {"tipo": "equipo|instalacion|sesion|resultado", "descripcion": "...", "prioridad": 1}
  ],
  "atributos_activar": ["..."],
  "instrucciones": [
    {"paso": 1, "accion": "...", "donde": "Google Business > ..."}
  ]
}"""

PROMPT_INSTAGRAM = SYSTEM_BASE + """

Genera la configuración completa de Instagram con esta estructura JSON:
{
  "bio": "... (max 150 chars, con CTA)",
  "enlace_bio": "... (URL o recomendación de tipo de enlace)",
  "enlace_justificacion": "... (por qué este enlace y no otro)",
  "categoria_negocio": "...",
  "highlights": [
    {"nombre": "...", "contenido_sugerido": "...", "orden": 1}
  ],
  "primeros_posts": [
    {"tipo": "carrusel|reel|post", "titulo": "...", "contenido": "...", "hashtags": ["..."]}
  ],
  "guia_estilo": {
    "tonos_color": "...",
    "tipo_foto": "...",
    "que_evitar": "..."
  },
  "instrucciones": [
    {"paso": 1, "accion": "...", "donde": "Instagram > Editar perfil > ..."}
  ]
}"""

PROMPT_FACEBOOK = SYSTEM_BASE + """

Genera la configuración completa de la página de Facebook con esta estructura JSON:
{
  "acerca_de": "... (sección completa)",
  "descripcion_corta": "... (max 255 chars)",
  "categorias": ["..."],
  "boton_cta": {"tipo": "whatsapp|reservar|llamar|sitio_web", "justificacion": "..."},
  "post_fijado": {"contenido": "...", "visual_sugerido": "..."},
  "pestanas_activar": ["..."],
  "pestanas_desactivar": ["..."],
  "instrucciones": [
    {"paso": 1, "accion": "...", "donde": "Facebook > Configuración > ..."}
  ]
}"""

CANALES_PROMPTS = {
    "whatsapp": PROMPT_WHATSAPP,
    "google_business": PROMPT_GOOGLE,
    "instagram": PROMPT_INSTAGRAM,
    "facebook": PROMPT_FACEBOOK,
}


# ============================================================
# GENERAR PERFIL (motor principal)
# ============================================================

async def generar_perfil(canal: str) -> dict:
    """Genera configuración completa de perfil para un canal.

    1. Recoge contexto (identidad, IRC, PCA, posición, competidores)
    2. Selecciona prompt específico del canal
    3. Llama a LLM
    4. Parsea y almacena en om_voz_perfil_plantilla
    5. Devuelve el perfil generado

    Args:
        canal: whatsapp | google_business | instagram | facebook

    Returns: dict con el perfil generado + número de plantillas creadas
    """
    if canal not in CANALES_PROMPTS:
        return {"error": f"Canal '{canal}' no soportado. Opciones: {list(CANALES_PROMPTS.keys())}"}

    # 1. Contexto
    ctx = await _contexto_para_prompt()
    if "error" in ctx:
        return ctx

    # Verificar que el canal tiene IRC > 0
    irc_canal = next((c for c in ctx["irc"] if c["canal"] == canal), None)
    if not irc_canal:
        return {"error": f"Canal '{canal}' no tiene IRC calculado. Ejecutar seed primero."}

    # 2. Prompt
    system_prompt = CANALES_PROMPTS[canal]
    posicion_str = ctx["posicion"].get("estado_acd", "desconocido")

    user_prompt = f"""Genera la configuración completa del perfil de {canal.upper()} para este negocio.

## IDENTIDAD
{json.dumps(ctx["identidad"], ensure_ascii=False, indent=2)}

## POSICIÓN ESTRATÉGICA (Eje 2)
Estado ACD: {posicion_str}
{json.dumps(ctx["posicion"], ensure_ascii=False, indent=2, default=str)}

## IRC DEL CANAL (Eje 1)
{canal}: {irc_canal["score"]}
Todos los canales: {json.dumps(ctx["irc"], ensure_ascii=False)}

## PCA — AUDIENCIA (Eje 3)
{json.dumps(ctx["pca"], ensure_ascii=False, indent=2, default=str)}

## COMPETIDORES
{json.dumps(ctx["competidores"], ensure_ascii=False, indent=2)}

Genera la configuración completa en JSON."""

    # 3. LLM
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
                    "model": STRATEGY_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 3000,
                    "temperature": 0.6,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            raw = data["choices"][0]["message"]["content"]
    except Exception as e:
        log.error("voz_arquitecto_llm_error", canal=canal, error=str(e))
        return {"error": f"LLM call failed: {e}"}

    # 4. Parsear
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()

    try:
        perfil = json.loads(clean)
    except json.JSONDecodeError as e:
        log.error("voz_arquitecto_parse_error", canal=canal, raw=raw[:500], error=str(e))
        return {"error": "LLM response not valid JSON", "raw": raw[:500]}

    # 5. Almacenar como plantillas
    pool = await _get_pool()
    plantillas_creadas = 0

    async with pool.acquire() as conn:
        # Marcar plantillas anteriores de este canal como reemplazadas
        await conn.execute("""
            UPDATE om_voz_perfil_plantilla
            SET estado = 'borrador'
            WHERE tenant_id = $1 AND canal = $2 AND estado = 'aprobado'
        """, TENANT, canal)

        # Crear plantillas para cada elemento del perfil
        for key, value in perfil.items():
            if key == "instrucciones":
                # Las instrucciones se almacenan como plantilla especial
                await conn.execute("""
                    INSERT INTO om_voz_perfil_plantilla
                        (tenant_id, canal, tipo, contenido, instrucciones,
                         posicion_matricial, estado)
                    VALUES ($1, $2, 'instrucciones_aplicacion', $3, $4, $5, 'borrador')
                """,
                    TENANT, canal,
                    json.dumps(value, ensure_ascii=False),
                    "Instrucciones paso a paso para aplicar la configuración",
                    posicion_str,
                )
                plantillas_creadas += 1
            elif isinstance(value, list):
                # Listas (servicios, Q&A, highlights, posts, etc.)
                for i, item in enumerate(value):
                    contenido = json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item)
                    await conn.execute("""
                        INSERT INTO om_voz_perfil_plantilla
                            (tenant_id, canal, tipo, contenido,
                             posicion_matricial, estado)
                        VALUES ($1, $2, $3, $4, $5, 'borrador')
                    """,
                        TENANT, canal, key, contenido, posicion_str,
                    )
                    plantillas_creadas += 1
            elif isinstance(value, dict):
                # Objetos (guia_estilo, boton_cta, etc.)
                await conn.execute("""
                    INSERT INTO om_voz_perfil_plantilla
                        (tenant_id, canal, tipo, contenido,
                         posicion_matricial, estado)
                    VALUES ($1, $2, $3, $4, $5, 'borrador')
                """,
                    TENANT, canal, key,
                    json.dumps(value, ensure_ascii=False),
                    posicion_str,
                )
                plantillas_creadas += 1
            else:
                # Strings simples (bio, descripcion, etc.)
                await conn.execute("""
                    INSERT INTO om_voz_perfil_plantilla
                        (tenant_id, canal, tipo, contenido,
                         posicion_matricial, estado)
                    VALUES ($1, $2, $3, $4, $5, 'borrador')
                """,
                    TENANT, canal, key, str(value), posicion_str,
                )
                plantillas_creadas += 1

    log.info("voz_arquitecto_perfil_generado", canal=canal, plantillas=plantillas_creadas)

    return {
        "status": "ok",
        "canal": canal,
        "posicion_matricial": posicion_str,
        "perfil": perfil,
        "plantillas_creadas": plantillas_creadas,
    }


async def generar_todos_los_perfiles() -> dict:
    """Genera perfiles para todos los canales con IRC > 0.3.

    Llama a generar_perfil() por cada canal activo.
    ~4 LLM calls secuenciales (~20 seg total).
    """
    from src.pilates.voz_identidad import obtener_irc

    irc = await obtener_irc()
    canales_activos = [
        c["canal"] for c in irc
        if float(c["irc_score"]) >= 0.3 and c["canal"] in CANALES_PROMPTS
    ]

    resultados = {}
    for canal in canales_activos:
        result = await generar_perfil(canal)
        resultados[canal] = {
            "status": result.get("status", "error"),
            "plantillas": result.get("plantillas_creadas", 0),
            "error": result.get("error"),
        }

    total = sum(r.get("plantillas", 0) for r in resultados.values())
    ok = sum(1 for r in resultados.values() if r["status"] == "ok")

    return {
        "status": "ok" if ok == len(canales_activos) else "parcial",
        "canales_generados": ok,
        "canales_total": len(canales_activos),
        "plantillas_total": total,
        "detalle": resultados,
    }


# ============================================================
# CONSULTAS
# ============================================================

async def obtener_perfil(canal: str) -> dict:
    """Devuelve todas las plantillas de un canal, agrupadas por tipo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_voz_perfil_plantilla
            WHERE tenant_id = $1 AND canal = $2
            ORDER BY tipo, created_at DESC
        """, TENANT, canal)

    if not rows:
        return {"error": f"No hay perfil generado para {canal}. Ejecutar POST /pilates/voz/perfil/{canal}/generar"}

    # Agrupar por tipo
    por_tipo = {}
    for r in rows:
        tipo = r["tipo"]
        if tipo not in por_tipo:
            por_tipo[tipo] = []
        por_tipo[tipo].append({
            "id": str(r["id"]),
            "contenido": r["contenido"],
            "instrucciones": r["instrucciones"],
            "posicion": r["posicion_matricial"],
            "estado": r["estado"],
            "created_at": str(r["created_at"]),
        })

    return {
        "canal": canal,
        "tipos": list(por_tipo.keys()),
        "plantillas": por_tipo,
        "total": len(rows),
    }


async def aprobar_plantilla(plantilla_id: str) -> dict:
    """Aprueba una plantilla (Jesús revisa y acepta)."""
    from uuid import UUID
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_voz_perfil_plantilla
            SET estado = 'aprobado'
            WHERE id = $1 AND tenant_id = $2 AND estado = 'borrador'
        """, UUID(plantilla_id), TENANT)
        if result == "UPDATE 0":
            return {"error": "Plantilla no encontrada o ya aprobada"}
    return {"status": "aprobado", "id": plantilla_id}


async def marcar_aplicada(plantilla_id: str) -> dict:
    """Marca una plantilla como aplicada (Jesús confirma que la copió al canal)."""
    from uuid import UUID
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_voz_perfil_plantilla
            SET estado = 'aplicado'
            WHERE id = $1 AND tenant_id = $2
        """, UUID(plantilla_id), TENANT)
        if result == "UPDATE 0":
            return {"error": "Plantilla no encontrada"}
    return {"status": "aplicado", "id": plantilla_id}
