"""Contenido — Generación y gestión de contenido digital (P67).

El Director incluye recetas de contenido externo en la pizarra cognitiva.
La matriz 3L×7F determina el ángulo. Todo pasa por filtro identidad.

Flujo: Director receta → generar_contenido() → filtro F3 → programar en pizarra comunicación
"""
from __future__ import annotations

import json
import structlog
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.db.client import get_pool
from src.motor.pensar import pensar, ConfigPensamiento
from src.pilates.json_utils import extraer_json
from src.pilates.filtro_identidad import leer_identidad, filtrar_contenido_db

log = structlog.get_logger()

TENANT = "authentic_pilates"

# Matriz 3L×7F → ángulos de contenido
ANGULOS = {
    ("S", "F1"): "Historias de clientes que se mantienen fieles. Consistencia.",
    ("S", "F2"): "Cómo el método EEDAP transforma de forma real, no mágica.",
    ("S", "F3"): "Lo que NO hacemos y por qué. Diferenciación por eliminación.",
    ("Se", "F5"): "Quiénes somos. Valores. El pueblo. La persona detrás.",
    ("Se", "F6"): "Cómo nos adaptamos sin perder esencia. Temporadas, cambios.",
    ("C", "F7"): "El método perdura. Formación EEDAP. Lo que se transfiere.",
    ("C", "F4"): "Cómo el Pilates se integra en tu vida diaria.",
}

SYSTEM_CONTENIDO = """Eres el generador de contenido de {nombre}, un estudio de Pilates en {ubicacion}.

IDENTIDAD:
{identidad_resumen}

REGLAS:
- Tono: {tono}
- Máximo 280 chars para Instagram caption (sin hashtags)
- Para GBP posts: máximo 500 chars
- Sugiere 3-5 hashtags relevantes
- NUNCA uses tono de gimnasio masivo, urgencia falsa, o promesas de transformación rápida
- Escribe como habla un profesional cercano de pueblo, no como un community manager de Barcelona

Formato JSON:
{{
  "titulo": "titulo corto",
  "cuerpo": "el contenido principal",
  "hashtags": ["tag1", "tag2"],
  "tipo_media": "foto|video|carrusel|texto",
  "sugerencia_media": "descripción de la foto/video ideal"
}}"""


async def generar_contenido_semana(ciclo: str = None) -> dict:
    """Genera el calendario de contenido de la semana.

    Lee identidad + recetas del Director + datos del negocio
    → genera 3-5 piezas de contenido → filtra con F3 → guarda en om_contenido.
    """
    if ciclo is None:
        ahora = datetime.now(ZoneInfo("Europe/Madrid"))
        ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    identidad = await leer_identidad(TENANT)
    if not identidad or not identidad.get("esencia"):
        return {"status": "skip", "razon": "Sin identidad configurada"}

    # Leer contexto del negocio
    pool = await get_pool()
    async with pool.acquire() as conn:
        clientes_activos = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'", TENANT)
        sesiones_semana = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id=$1 AND fecha >= date_trunc('week', now()) AND fecha < date_trunc('week', now()) + interval '7 days'
        """, TENANT)

    # Seleccionar 3 ángulos para la semana (rotar por ciclo)
    import hashlib
    seed = int(hashlib.md5(ciclo.encode()).hexdigest()[:8], 16)
    angulos_keys = list(ANGULOS.keys())
    seleccionados = []
    for i in range(3):
        idx = (seed + i) % len(angulos_keys)
        lente, funcion = angulos_keys[idx]
        seleccionados.append({
            "lente": lente, "funcion": funcion,
            "angulo": ANGULOS[angulos_keys[idx]],
        })

    identidad_resumen = (
        f"Esencia: {identidad.get('esencia', '')}\n"
        f"Valores: {', '.join(identidad.get('valores', []))}\n"
        f"Anti-identidad: {', '.join(identidad.get('anti_identidad', []))}\n"
        f"Ángulo diferencial: {identidad.get('angulo_diferencial', '')}"
    )

    system = SYSTEM_CONTENIDO.format(
        nombre=identidad.get("esencia", "Authentic Pilates").split(".")[0],
        ubicacion="Albelda de Iregua, La Rioja",
        identidad_resumen=identidad_resumen,
        tono=identidad.get("tono", "cercano y profesional"),
    )

    user = (
        f"Ciclo: {ciclo}\n"
        f"Clientes activos: {clientes_activos}\n"
        f"Sesiones esta semana: {sesiones_semana}\n\n"
        f"Genera 3 piezas de contenido para Instagram, una por cada ángulo:\n"
    )
    for i, a in enumerate(seleccionados):
        user += f"\n{i+1}. Lente {a['lente']}, Función {a['funcion']}: {a['angulo']}"

    user += "\n\nResponde con un JSON array de 3 objetos."

    config = ConfigPensamiento(
        funcion="F5", lente="sentido", complejidad="media",
        usar_cache=True, ttl_cache_horas=168,
    )
    resultado = await pensar(system=system, user=user, config=config)
    piezas = extraer_json(resultado.texto, fallback={"items": []})
    if isinstance(piezas, dict):
        piezas = piezas.get("items", piezas.get("contenidos", [piezas]))
    if not isinstance(piezas, list):
        piezas = [piezas]

    # Guardar en om_contenido y filtrar
    creados = 0
    filtrados = 0
    async with pool.acquire() as conn:
        for i, pieza in enumerate(piezas[:5]):
            if not isinstance(pieza, dict) or not pieza.get("cuerpo"):
                continue

            row = await conn.fetchrow("""
                INSERT INTO om_contenido
                    (tenant_id, ciclo, canal, tipo, titulo, cuerpo, hashtags,
                     funcion, lente, ints, estado, origen)
                VALUES ($1, $2, 'instagram', $3, $4, $5, $6, $7, $8, $9, 'borrador', 'director')
                RETURNING id
            """, TENANT, ciclo,
                pieza.get("tipo_media", "foto"),
                pieza.get("titulo", f"Contenido {i+1}"),
                pieza["cuerpo"],
                pieza.get("hashtags", []),
                seleccionados[i]["funcion"] if i < len(seleccionados) else None,
                seleccionados[i]["lente"] if i < len(seleccionados) else None,
                [],
            )
            creados += 1

            # Filtrar con F3
            filtro = await filtrar_contenido_db(row["id"], TENANT)
            if not filtro.get("compatible", True):
                filtrados += 1

    log.info("contenido_generado", ciclo=ciclo, creados=creados, filtrados=filtrados,
             coste=resultado.coste_usd)

    return {
        "status": "ok", "ciclo": ciclo,
        "creados": creados, "filtrados_f3": filtrados,
        "coste": resultado.coste_usd,
    }


async def aprobar_contenido(contenido_id, aprobado_por: str = "jesus") -> dict:
    """CR1: Jesús aprueba contenido para publicación."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE om_contenido
            SET estado = 'aprobado', aprobado_por = $2, updated_at = now()
            WHERE id = $1 AND filtro_identidad = 'compatible'
        """, contenido_id, aprobado_por)
    return {"status": "ok"}


async def programar_publicacion(contenido_id, programado_para: datetime = None) -> dict:
    """Programa contenido aprobado para publicación."""
    if programado_para is None:
        programado_para = datetime.now(ZoneInfo("Europe/Madrid")) + timedelta(hours=2)

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE om_contenido
            SET estado = 'programado', programado_para = $2, updated_at = now()
            WHERE id = $1 AND estado = 'aprobado'
        """, contenido_id, programado_para)
    return {"status": "ok", "programado_para": str(programado_para)}
