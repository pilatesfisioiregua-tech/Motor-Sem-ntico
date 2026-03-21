"""Séquito de 24 Asesores — Consejo con ACD.

18 asesores del Motor (INT-01 a INT-18) + 6 del Exocortex (INT-19 a INT-24).
Cada asesor recibe datos reales del tenant + su P y R asignados.

Fuente: Exocortex v2.1 S8.
"""
from __future__ import annotations

import asyncio
import json
import time
import os
import structlog
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"

# 24 asesores con su ángulo único
ASESORES = {
    "INT-01": {"nombre": "El Analista", "angulo": "Lógica, contradicciones, números. Busca inconsistencias en los datos."},
    "INT-02": {"nombre": "El Ingeniero", "angulo": "Datos, atajos, eficiencia. Optimiza procesos con métricas."},
    "INT-03": {"nombre": "El Arquitecto", "angulo": "Estructura, actores invisibles, gaps. Ve lo que falta en el sistema."},
    "INT-04": {"nombre": "El Ecólogo", "angulo": "Nichos, ecosistema, capital que se deprecia. Analiza el entorno competitivo."},
    "INT-05": {"nombre": "El Estratega", "angulo": "Secuencias, movimientos, reversibilidad. Planifica jugadas a futuro."},
    "INT-06": {"nombre": "El Político", "angulo": "Poder, coaliciones, alianzas. Mapea relaciones e influencias."},
    "INT-07": {"nombre": "El Financiero", "angulo": "Payoffs, coste oportunidad, riesgo. Evalúa cada decisión en euros."},
    "INT-08": {"nombre": "El Psicólogo", "angulo": "Vergüenza, lealtad, lo no dicho. Detecta lo emocional debajo de lo racional."},
    "INT-09": {"nombre": "El Lingüista", "angulo": "Palabras ausentes, reencuadre. Cambia cómo se nombran las cosas."},
    "INT-10": {"nombre": "El Cinestésico", "angulo": "Tensión corporal, ritmo, timing. Siente cuándo es el momento."},
    "INT-11": {"nombre": "El Espacial", "angulo": "Punto de presión, distribución. Ve dónde concentrar fuerza."},
    "INT-12": {"nombre": "El Narrador", "angulo": "Roles, historias, trampas narrativas. Cuenta la historia que falta."},
    "INT-13": {"nombre": "El Prospectivista", "angulo": "Señales débiles, escenarios futuros. Ve lo que viene antes que nadie."},
    "INT-14": {"nombre": "El Divergente", "angulo": "Opciones ocultas, terceras vías. Encuentra salidas que nadie ve."},
    "INT-15": {"nombre": "El Esteta", "angulo": "Elegancia, coherencia forma-fondo. Juzga si la solución es limpia."},
    "INT-16": {"nombre": "El Constructor", "angulo": "Prototipo, primer paso, fallo seguro. Traduce ideas en acciones mínimas."},
    "INT-17": {"nombre": "El Existencial", "angulo": "Valores vs acciones, inercia como decisión. Pregunta por qué haces lo que haces."},
    "INT-18": {"nombre": "El Contemplativo", "angulo": "Urgencia inventada, vacío como recurso. Cuestiona si hay que hacer algo."},
    "INT-19": {"nombre": "Guardián de Reputación", "angulo": "Presencia pública, reseñas, percepción. Protege la imagen."},
    "INT-20": {"nombre": "Observador de Mercado", "angulo": "Competencia, tendencias, entorno. Vigila qué hacen los demás."},
    "INT-21": {"nombre": "Director de Voz", "angulo": "Mensaje, canal, timing. Decide qué decir, dónde y cuándo."},
    "INT-22": {"nombre": "Analista de Audiencia", "angulo": "Consumo, formato, tono. Entiende qué quiere tu público."},
    "INT-23": {"nombre": "El Depurador", "angulo": "Lo que sobra, el NO. Identifica qué eliminar para ganar."},
    "INT-24": {"nombre": "Custodio de Identidad", "angulo": "Quién eres de verdad, frontera. Defiende lo innegociable."},
}

# Pensamientos (P) y Razonamientos (R)
PENSAMIENTOS = {
    "P01": "Analítico — descomponer en partes",
    "P02": "Sistémico — ver conexiones y bucles",
    "P03": "Crítico — cuestionar supuestos",
    "P04": "Diseño — centrado en el usuario/problema",
    "P05": "Primeros principios — volver a lo fundamental",
    "P06": "Lateral — saltar a dominios inesperados",
    "P07": "Abstracto — subir nivel, generalizar",
    "P08": "Concreto — bajar a ejemplos tangibles",
    "P09": "Dialéctico — tesis-antítesis-síntesis",
    "P10": "Probabilístico — razonar con incertidumbre",
    "P11": "Metacognitivo — pensar sobre cómo pensamos",
    "P12": "Narrativo — contar historias, dar sentido",
    "P13": "Computacional — algoritmos, eficiencia, escalabilidad",
    "P14": "Estratégico — jugadas, timing, posicionamiento",
    "P15": "Integrador — fusionar perspectivas contradictorias",
}

RAZONAMIENTOS = {
    "R01": "Deducción — de lo general a lo particular",
    "R02": "Inducción — de casos a regla general",
    "R03": "Abducción — mejor explicación posible",
    "R04": "Analogía — esto es como aquello",
    "R05": "Causal — A causa B, no solo correlación",
    "R06": "Contrafactual — qué pasaría si...",
    "R07": "Bayesiano — actualizar creencias con evidencia",
    "R08": "Dialéctico — confrontar opuestos",
    "R09": "Pragmático — qué funciona en la práctica",
    "R10": "Heurístico — reglas rápidas, atajos útiles",
    "R11": "Formal — lógica estricta, sin ambigüedad",
    "R12": "Transductivo — de caso particular a caso particular",
}


@dataclass
class RespuestaAsesor:
    int_id: str
    nombre: str
    respuesta: str
    pensamiento: str
    razonamiento: str
    tiempo_s: float = 0
    coste_usd: float = 0


@dataclass
class SesionConsejo:
    pregunta: str
    contexto: str
    asesores: list[RespuestaAsesor]
    sintesis: str
    puntos_ciegos: list[str]
    estado_acd_pre: Optional[str] = None
    prescripcion: Optional[dict] = None
    coste_total: float = 0
    tiempo_total: float = 0


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def _obtener_contexto_tenant() -> str:
    """Recopila datos reales del tenant para inyectar en los prompts de asesores."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'", TENANT)

        ocupacion = await conn.fetchrow("""
            SELECT COALESCE(SUM(capacidad_max),0) as total,
                (SELECT count(*) FROM om_contratos WHERE tenant_id=$1 AND tipo='grupo' AND estado='activo') as ocu
            FROM om_grupos WHERE tenant_id=$1 AND estado='activo'
        """, TENANT)
        pct = round((ocupacion["ocu"] or 0) / max(ocupacion["total"] or 1, 1) * 100, 0)

        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT)

        deuda = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)

        alertas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.tenant_id=$1 AND a.estado='no_vino'
                AND s.fecha >= CURRENT_DATE - interval '30 days'
        """, TENANT)

        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id=$1", TENANT)
        adn = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true", TENANT)

    return (
        f"Authentic Pilates, estudio de Pilates reformer en Logroño. "
        f"{clientes} clientes activos, {pct}% ocupación ({ocupacion['ocu']}/{ocupacion['total']} plazas). "
        f"Ingresos mes: {float(ingresos):.0f}€. Deuda pendiente: {float(deuda):.0f}€. "
        f"Faltas último mes: {alertas}. "
        f"Procesos documentados: {procesos}. Principios ADN: {adn}. "
        f"Operado por instructor-dueño único (Jesús). "
        f"Todo el conocimiento tácito reside en el dueño."
    )


async def _call_asesor(int_id: str, pregunta: str, contexto: str,
                        p_id: str, r_id: str) -> RespuestaAsesor:
    """Ejecuta un asesor individual via LLM."""
    asesor = ASESORES[int_id]
    p_desc = PENSAMIENTOS.get(p_id, "")
    r_desc = RAZONAMIENTOS.get(r_id, "")

    prompt = f"""Eres {asesor['nombre']} ({int_id}), asesor de un estudio de Pilates.
Tu ángulo: {asesor['angulo']}
Tu pensamiento asignado: {p_id} — {p_desc}
Tu razonamiento asignado: {r_id} — {r_desc}

DATOS REALES DEL NEGOCIO:
{contexto}

PREGUNTA DEL DUEÑO:
{pregunta}

Responde desde tu ángulo específico, usando el tipo de pensamiento y razonamiento asignados.
Sé directo, concreto, con datos. Máximo 200 palabras. Sin preámbulos."""

    t0 = time.time()
    try:
        import httpx
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("SEQUITO_MODEL", "mistralai/devstral-2512")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 400,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            respuesta = data["choices"][0]["message"]["content"]
            coste = data.get("usage", {}).get("total_tokens", 0) * 0.000001

    except Exception as e:
        respuesta = f"[Error: {str(e)[:100]}]"
        coste = 0

    dt = time.time() - t0
    return RespuestaAsesor(
        int_id=int_id, nombre=asesor["nombre"],
        respuesta=respuesta, pensamiento=p_id, razonamiento=r_id,
        tiempo_s=round(dt, 1), coste_usd=round(coste, 4),
    )


async def _sintetizar(pregunta: str, respuestas: list[RespuestaAsesor]) -> tuple[str, list[str]]:
    """Integrador: sintetiza respuestas + detecta puntos ciegos cruzados."""
    resumen = "\n\n".join(
        f"**{r.nombre} ({r.int_id}, {r.pensamiento}+{r.razonamiento}):**\n{r.respuesta}"
        for r in respuestas
    )

    prompt = f"""Eres el Integrador del Consejo de Asesores de un estudio de Pilates.

PREGUNTA ORIGINAL:
{pregunta}

RESPUESTAS DE LOS ASESORES:
{resumen}

Produce:
1. SÍNTESIS (máx 300 palabras): integra las perspectivas, señala convergencias y divergencias.
2. PUNTOS CIEGOS: lista 2-3 aspectos que NINGÚN asesor mencionó pero son relevantes.

Formato:
SINTESIS:
[tu síntesis]

PUNTOS_CIEGOS:
- [punto 1]
- [punto 2]
- [punto 3]"""

    try:
        import httpx
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        model = os.getenv("SEQUITO_SYNTH_MODEL", "z-ai/glm-5")

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 800,
                    "temperature": 0.3,
                },
            )
            resp.raise_for_status()
            texto = resp.json()["choices"][0]["message"]["content"]

    except Exception as e:
        return f"[Error síntesis: {str(e)[:100]}]", []

    # Parsear síntesis y puntos ciegos
    sintesis = texto
    puntos_ciegos = []

    if "PUNTOS_CIEGOS:" in texto:
        parts = texto.split("PUNTOS_CIEGOS:")
        sintesis = parts[0].replace("SINTESIS:", "").strip()
        ciegos_text = parts[1].strip()
        puntos_ciegos = [
            line.strip().lstrip("- ").strip()
            for line in ciegos_text.split("\n")
            if line.strip() and line.strip() != "-"
        ]

    return sintesis, puntos_ciegos


async def convocar_consejo(
    pregunta: str,
    profundidad: str = "normal",
    ints_forzadas: list[str] = None,
) -> SesionConsejo:
    """Convoca el Consejo de Asesores con selección ACD."""
    t0 = time.time()

    # 1. Obtener contexto real
    contexto = await _obtener_contexto_tenant()

    # 2. Obtener prescripción ACD (último diagnóstico)
    pool = await _get_pool()
    prescripcion = None
    estado_acd = None

    async with pool.acquire() as conn:
        ultimo_acd = await conn.fetchrow("""
            SELECT estado, prescripcion FROM om_diagnosticos_tenant
            WHERE tenant_id = $1 ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        if ultimo_acd:
            estado_acd = ultimo_acd["estado"]
            if ultimo_acd["prescripcion"]:
                prescripcion = dict(ultimo_acd["prescripcion"]) if isinstance(
                    ultimo_acd["prescripcion"], dict) else json.loads(ultimo_acd["prescripcion"])

    # 3. Seleccionar asesores
    n_asesores = {"rapida": 3, "normal": 5, "profunda": 8}.get(profundidad, 5)

    if ints_forzadas:
        ints_seleccionadas = ints_forzadas[:n_asesores]
    elif prescripcion and prescripcion.get("ints"):
        ints_seleccionadas = prescripcion["ints"][:n_asesores]
    else:
        # Default: asesores más relevantes para un estudio de Pilates
        ints_seleccionadas = ["INT-07", "INT-03", "INT-12", "INT-16", "INT-17"][:n_asesores]

    # Asignar P y R
    ps = (prescripcion or {}).get("ps", ["P03", "P05", "P08"])
    rs = (prescripcion or {}).get("rs", ["R03", "R09", "R05"])

    asignaciones = []
    for i, int_id in enumerate(ints_seleccionadas):
        if int_id not in ASESORES:
            continue
        p = ps[i % len(ps)] if ps else "P03"
        r = rs[i % len(rs)] if rs else "R09"
        asignaciones.append((int_id, p, r))

    # 4. Ejecutar asesores en paralelo
    tareas = [
        _call_asesor(int_id, pregunta, contexto, p, r)
        for int_id, p, r in asignaciones
    ]
    respuestas = await asyncio.gather(*tareas)

    # 5. Sintetizar
    sintesis, puntos_ciegos = await _sintetizar(pregunta, respuestas)

    # 6. Calcular costes
    coste_total = sum(r.coste_usd for r in respuestas) + 0.001
    tiempo_total = time.time() - t0

    # 7. Almacenar en om_sesiones_consejo
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_sesiones_consejo (
                tenant_id, pregunta, profundidad, tier_usado,
                estado_acd_pre, inteligencias_convocadas,
                pensamientos_seleccionados, razonamientos_seleccionados,
                prescripcion_acd, respuestas_por_asesor, sintesis,
                puntos_ciegos_cruzados, coste_api, tiempo_ejecucion_s
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13,$14)
        """, TENANT, pregunta, profundidad, len(asignaciones),
            estado_acd,
            [a[0] for a in asignaciones],
            [a[1] for a in asignaciones],
            [a[2] for a in asignaciones],
            json.dumps(prescripcion) if prescripcion else None,
            json.dumps([{
                "int_id": r.int_id, "nombre": r.nombre,
                "respuesta": r.respuesta, "P": r.pensamiento, "R": r.razonamiento,
                "tiempo_s": r.tiempo_s,
            } for r in respuestas]),
            sintesis,
            puntos_ciegos,
            round(coste_total, 4),
            round(tiempo_total, 0),
        )

    log.info("consejo_completado", asesores=len(respuestas),
             coste=round(coste_total, 4), tiempo=round(tiempo_total, 1))

    return SesionConsejo(
        pregunta=pregunta, contexto=contexto,
        asesores=respuestas, sintesis=sintesis,
        puntos_ciegos=puntos_ciegos,
        estado_acd_pre=estado_acd, prescripcion=prescripcion,
        coste_total=round(coste_total, 4),
        tiempo_total=round(tiempo_total, 1),
    )
