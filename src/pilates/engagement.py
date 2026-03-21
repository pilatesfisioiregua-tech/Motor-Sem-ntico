"""Sistema de Engagement — Aprendizaje del cliente.

Tracking comportamental + engagement score + rachas + milestones + churn detection.

Fuente: Exocortex v2.1 B-PIL-18-DEF Fase E.
"""
from __future__ import annotations

import json
import structlog
from datetime import date, datetime, timedelta
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


MILESTONES = [
    {"id": "1_mes",      "label": "1 mes en el estudio"},
    {"id": "3_meses",    "label": "3 meses en el estudio"},
    {"id": "6_meses",    "label": "6 meses en el estudio"},
    {"id": "1_anio",     "label": "1 año en el estudio"},
    {"id": "25_clases",  "label": "25 clases completadas"},
    {"id": "50_clases",  "label": "50 clases completadas"},
    {"id": "100_clases", "label": "100 clases completadas"},
    {"id": "racha_4",    "label": "4 semanas sin faltar"},
    {"id": "racha_8",    "label": "8 semanas sin faltar"},
    {"id": "racha_12",   "label": "12 semanas sin faltar"},
    {"id": "pago_al_dia","label": "Siempre al día con pagos (3+ meses)"},
]


# ============================================================
# REGISTRAR EVENTO
# ============================================================

async def registrar_evento(cliente_id: UUID, tipo: str, metadata: dict = None):
    """Registra un evento de interacción del cliente."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_cliente_eventos (tenant_id, cliente_id, tipo, metadata)
            VALUES ($1, $2, $3, $4)
        """, TENANT, cliente_id, tipo, json.dumps(metadata or {}))

        # Ensure perfil exists
        await conn.execute("""
            INSERT INTO om_cliente_perfil (tenant_id, cliente_id)
            VALUES ($1, $2)
            ON CONFLICT (cliente_id) DO NOTHING
        """, TENANT, cliente_id)

        # Update portal access stats
        if tipo == "portal_chat":
            await conn.execute("""
                UPDATE om_cliente_perfil
                SET total_interacciones_portal = total_interacciones_portal + 1,
                    ultimo_acceso_portal = now(),
                    updated_at = now()
                WHERE cliente_id = $1
            """, cliente_id)


# ============================================================
# RECALCULAR ENGAGEMENT — Todos los clientes
# ============================================================

async def recalcular_engagement_todos() -> dict:
    """Recalcula engagement score de todos los clientes activos. Cron semanal."""
    pool = await _get_pool()
    recalculados = 0
    alertas = 0

    async with pool.acquire() as conn:
        clientes = await conn.fetch("""
            SELECT DISTINCT c.id, c.nombre, c.apellidos, c.created_at
            FROM om_clientes c
            JOIN om_cliente_tenant ct ON ct.cliente_id = c.id AND ct.tenant_id = $1
            JOIN om_contratos co ON co.cliente_id = c.id AND co.estado = 'activo'
        """, TENANT)

        for cl in clientes:
            old_score = await conn.fetchval("""
                SELECT engagement_score FROM om_cliente_perfil WHERE cliente_id = $1
            """, cl["id"])

            result = await _recalcular_engagement_cliente(conn, cl["id"], cl["created_at"])
            recalculados += 1

            # Detect falling engagement
            if old_score and result["score"] < old_score - 15:
                alertas += 1
                try:
                    from src.pilates.feed import feed_engagement
                    await feed_engagement(
                        f"{cl['nombre']} {cl['apellidos']}",
                        old_score, result["score"], cl["id"]
                    )
                except Exception:
                    pass

    log.info("engagement_recalculado", clientes=recalculados, alertas=alertas)
    return {"recalculados": recalculados, "alertas": alertas}


async def _recalcular_engagement_cliente(conn, cliente_id: UUID, created_at) -> dict:
    """Recalcula score + racha + milestones + churn para un cliente."""
    hoy = date.today()
    hace_4_sem = hoy - timedelta(weeks=4)
    hace_12_sem = hoy - timedelta(weeks=12)

    # 1. Componente asistencia (40pts max)
    stats = await conn.fetchrow("""
        SELECT count(*) as total,
               count(*) FILTER (WHERE a.estado = 'asistio') as asistidas
        FROM om_asistencias a
        JOIN om_sesiones s ON s.id = a.sesion_id
        WHERE a.cliente_id = $1 AND a.tenant_id = $2 AND s.fecha >= $3
    """, cliente_id, TENANT, hace_4_sem)
    total = stats["total"] or 0
    asistidas = stats["asistidas"] or 0
    pct_asistencia = asistidas / max(total, 1)
    score_asistencia = round(pct_asistencia * 40)

    # 2. Componente portal (20pts max)
    portal_stats = await conn.fetchrow("""
        SELECT total_interacciones_portal, ultimo_acceso_portal
        FROM om_cliente_perfil WHERE cliente_id = $1
    """, cliente_id)
    interacciones = portal_stats["total_interacciones_portal"] if portal_stats else 0
    score_portal = min(interacciones * 4, 20)

    # 3. Componente pago al día (20pts max)
    deuda = await conn.fetchval("""
        SELECT COALESCE(SUM(total), 0) FROM om_cargos
        WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
    """, cliente_id, TENANT)
    score_pago = 20 if float(deuda) == 0 else max(0, 10 - int(float(deuda) / 20))

    # 4. Componente recencia (10pts max)
    ultima_asistencia = await conn.fetchval("""
        SELECT MAX(s.fecha) FROM om_asistencias a
        JOIN om_sesiones s ON s.id = a.sesion_id
        WHERE a.cliente_id = $1 AND a.estado = 'asistio'
    """, cliente_id)
    if ultima_asistencia:
        dias_sin = (hoy - ultima_asistencia).days
        score_recencia = max(0, 10 - dias_sin)
    else:
        score_recencia = 0

    # 5. Componente antigüedad (10pts max)
    if created_at:
        meses = (hoy - created_at.date()).days / 30 if hasattr(created_at, 'date') else (hoy - created_at).days / 30
        score_antiguedad = min(int(meses), 10)
    else:
        score_antiguedad = 0

    score = score_asistencia + score_portal + score_pago + score_recencia + score_antiguedad
    score = max(0, min(100, score))

    # Racha: semanas consecutivas sin falta
    racha = 0
    for w in range(12):
        sem_inicio = hoy - timedelta(weeks=w + 1)
        sem_fin = hoy - timedelta(weeks=w)
        faltas_sem = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $4
                AND a.estado = 'no_vino'
        """, cliente_id, TENANT, sem_inicio, sem_fin)
        sesiones_sem = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $4
        """, cliente_id, TENANT, sem_inicio, sem_fin)
        if sesiones_sem > 0 and faltas_sem == 0:
            racha += 1
        else:
            break

    # Tendencia
    old_score = await conn.fetchval(
        "SELECT engagement_score FROM om_cliente_perfil WHERE cliente_id = $1", cliente_id)
    if old_score is None:
        tendencia = "estable"
    elif score > old_score + 5:
        tendencia = "subiendo"
    elif score < old_score - 5:
        tendencia = "bajando"
    else:
        tendencia = "estable"

    # Churn risk
    if score < 20:
        riesgo = "critico"
    elif score < 40:
        riesgo = "alto"
    elif score < 60 and tendencia == "bajando":
        riesgo = "medio"
    else:
        riesgo = "bajo"

    # Milestones
    celebrados_raw = await conn.fetchval(
        "SELECT milestones_celebrados FROM om_cliente_perfil WHERE cliente_id = $1", cliente_id)
    celebrados = json.loads(celebrados_raw) if celebrados_raw and isinstance(celebrados_raw, str) else (celebrados_raw or [])

    nuevos_milestones = []
    total_clases = await conn.fetchval("""
        SELECT count(*) FROM om_asistencias a
        JOIN om_sesiones s ON s.id = a.sesion_id
        WHERE a.cliente_id = $1 AND a.estado = 'asistio'
    """, cliente_id)
    meses_cliente = (hoy - (created_at.date() if hasattr(created_at, 'date') else created_at)).days / 30 if created_at else 0

    milestone_checks = [
        ("1_mes", meses_cliente >= 1),
        ("3_meses", meses_cliente >= 3),
        ("6_meses", meses_cliente >= 6),
        ("1_anio", meses_cliente >= 12),
        ("25_clases", total_clases >= 25),
        ("50_clases", total_clases >= 50),
        ("100_clases", total_clases >= 100),
        ("racha_4", racha >= 4),
        ("racha_8", racha >= 8),
        ("racha_12", racha >= 12),
    ]
    for mid, condition in milestone_checks:
        if condition and mid not in celebrados:
            nuevos_milestones.append(mid)
            celebrados.append(mid)

    # Celebrar nuevos milestones
    for mid in nuevos_milestones:
        label = next((m["label"] for m in MILESTONES if m["id"] == mid), mid)
        try:
            from src.pilates.feed import feed_milestone
            nombre = await conn.fetchval("SELECT nombre FROM om_clientes WHERE id = $1", cliente_id)
            await feed_milestone(nombre or "Cliente", label, cliente_id)
        except Exception:
            pass

    # Susceptible cross-sell
    contrato_tipo = await conn.fetchval("""
        SELECT tipo FROM om_contratos WHERE cliente_id = $1 AND estado = 'activo' LIMIT 1
    """, cliente_id)
    susceptible_individual = contrato_tipo == "grupo" and score > 70

    # Update perfil
    racha_max = await conn.fetchval(
        "SELECT racha_maxima FROM om_cliente_perfil WHERE cliente_id = $1", cliente_id) or 0

    await conn.execute("""
        INSERT INTO om_cliente_perfil (tenant_id, cliente_id, engagement_score, engagement_tendencia,
            riesgo_churn, racha_actual, racha_maxima, milestones_celebrados,
            susceptible_individual, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, now())
        ON CONFLICT (cliente_id) DO UPDATE SET
            engagement_score = $3, engagement_tendencia = $4,
            riesgo_churn = $5, racha_actual = $6,
            racha_maxima = GREATEST(om_cliente_perfil.racha_maxima, $6),
            milestones_celebrados = $8,
            susceptible_individual = $9, updated_at = now()
    """, TENANT, cliente_id, score, tendencia, riesgo, racha,
        max(racha, racha_max), json.dumps(celebrados), susceptible_individual)

    return {"score": score, "racha": racha, "riesgo": riesgo, "nuevos_milestones": nuevos_milestones}


# ============================================================
# CONTEXTO ENGAGEMENT — Para inyectar en system prompt
# ============================================================

async def obtener_contexto_engagement(cliente_id: UUID) -> str:
    """Genera texto de contexto para inyectar en el system prompt del bot."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        perfil = await conn.fetchrow("""
            SELECT * FROM om_cliente_perfil WHERE cliente_id = $1
        """, cliente_id)

    if not perfil:
        return ""

    partes = []
    score = perfil["engagement_score"]
    racha = perfil["racha_actual"]
    riesgo = perfil["riesgo_churn"]
    tendencia = perfil["engagement_tendencia"]

    if racha >= 4:
        partes.append(f"Lleva {racha} semanas sin faltar (racha). Reconócelo si viene a cuento.")

    if riesgo in ("alto", "critico"):
        partes.append("RIESGO DE BAJA ALTO. Sé especialmente amable y proactivo.")
    elif tendencia == "bajando":
        partes.append("Su engagement está bajando. Que la interacción sea positiva y motivadora.")

    if perfil["susceptible_individual"]:
        partes.append("Buen candidato para ofrecer sesión individual si el contexto lo permite.")

    if perfil["canal_pago_preferido"]:
        partes.append(f"Suele pagar por {perfil['canal_pago_preferido']}.")

    return "\n".join(partes)
