"""OMC-95: Endpoints REST para el Simbionte → Postgres → LLM tool_use.

Flujo:
  1. POST /simbionte/escribir — Simbionte deposita resultados calculados
  2. POST /simbionte/escribir-batch — Simbionte deposita N resultados de golpe
  3. POST /simbionte/consultar — LLM consulta via tool_use (formula, patron, calcular, cascada)
  4. GET  /simbionte/sesion/{id} — Estado completo de una sesión
  5. GET  /simbionte/auditorias/{sesion_id} — Qué consultó el LLM
"""
from __future__ import annotations
import structlog
from uuid import UUID, uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

log = structlog.get_logger()
router = APIRouter(prefix="/simbionte", tags=["simbionte"])


# ============================================================
# SCHEMAS
# ============================================================

class ResultadoIn(BaseModel):
    sesion_id: Optional[UUID] = None
    nombre: str
    tipo: str  # diagnostico, relaciones, riesgo, prescripcion, patron, cascada
    categoria: Optional[str] = None
    valor: Optional[float] = None
    valor_texto: Optional[str] = None
    texto_legible: Optional[str] = None
    pregunta: Optional[str] = None
    polos: Optional[list] = None
    presupuestos: Optional[list] = None
    razonamiento: Optional[str] = None
    datos_origen: Optional[dict] = None
    finalidad: Optional[str] = None
    paso_protocolo: Optional[int] = None
    patron_match: Optional[str] = None
    isomorfismo: Optional[str] = None
    precedentes: Optional[list] = None
    prescripcion: Optional[str] = None
    enlaces: Optional[list] = None
    modelo_llm: Optional[str] = None
    coste_calculo: float = 0.0


class BatchIn(BaseModel):
    sesion_id: Optional[UUID] = None
    resultados: list[ResultadoIn]


class ConsultaIn(BaseModel):
    """Consulta del LLM via tool_use."""
    sesion_id: UUID
    tool: str  # consultar_formula, consultar_patron, calcular, cascada_preguntas
    params: dict = Field(default_factory=dict)


# ============================================================
# HELPERS
# ============================================================

async def _pool():
    from src.db.client import get_pool
    return await get_pool()


async def _audit(sesion_id: UUID, tool: str, params: dict, n_res: int, tokens: int):
    """Registra auditoría de consulta."""
    import json
    pool = await _pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO auditorias_simbionte (sesion_id, tool_name, input_params, n_resultados, tokens_respuesta)
            VALUES ($1, $2, $3::jsonb, $4, $5)
        """, sesion_id, tool, json.dumps(params), n_res, tokens)


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/escribir")
async def escribir_resultado(data: ResultadoIn):
    """El Simbionte deposita UN resultado calculado en Postgres."""
    import json
    pool = await _pool()
    sid = data.sesion_id or uuid4()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO resultados_simbionte
                (sesion_id, nombre, tipo, categoria, valor, valor_texto, texto_legible,
                 pregunta, polos, presupuestos, razonamiento, datos_origen, finalidad,
                 paso_protocolo, patron_match, isomorfismo, precedentes, prescripcion,
                 enlaces, modelo_llm, coste_calculo)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,$11,$12::jsonb,$13,$14,$15,$16,$17::jsonb,$18,$19::jsonb,$20,$21)
            RETURNING id
        """, sid, data.nombre, data.tipo, data.categoria, data.valor,
            data.valor_texto, data.texto_legible, data.pregunta,
            json.dumps(data.polos) if data.polos else None,
            json.dumps(data.presupuestos) if data.presupuestos else None,
            data.razonamiento,
            json.dumps(data.datos_origen) if data.datos_origen else None,
            data.finalidad, data.paso_protocolo, data.patron_match,
            data.isomorfismo,
            json.dumps(data.precedentes) if data.precedentes else None,
            data.prescripcion,
            json.dumps(data.enlaces) if data.enlaces else None,
            data.modelo_llm, data.coste_calculo)
    return {"ok": True, "id": row["id"], "sesion_id": str(sid)}


@router.post("/escribir-batch")
async def escribir_batch(data: BatchIn):
    """El Simbionte deposita N resultados de golpe (una sesión de análisis)."""
    import json
    pool = await _pool()
    sid = data.sesion_id or uuid4()
    ids = []
    async with pool.acquire() as conn:
        for r in data.resultados:
            row = await conn.fetchrow("""
                INSERT INTO resultados_simbionte
                    (sesion_id, nombre, tipo, categoria, valor, valor_texto, texto_legible,
                     pregunta, polos, presupuestos, razonamiento, datos_origen, finalidad,
                     paso_protocolo, patron_match, isomorfismo, precedentes, prescripcion,
                     enlaces, modelo_llm, coste_calculo)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,$11,$12::jsonb,$13,$14,$15,$16,$17::jsonb,$18,$19::jsonb,$20,$21)
                RETURNING id
            """, sid, r.nombre, r.tipo, r.categoria, r.valor,
                r.valor_texto, r.texto_legible, r.pregunta,
                json.dumps(r.polos) if r.polos else None,
                json.dumps(r.presupuestos) if r.presupuestos else None,
                r.razonamiento,
                json.dumps(r.datos_origen) if r.datos_origen else None,
                r.finalidad, r.paso_protocolo, r.patron_match,
                r.isomorfismo,
                json.dumps(r.precedentes) if r.precedentes else None,
                r.prescripcion,
                json.dumps(r.enlaces) if r.enlaces else None,
                r.modelo_llm, r.coste_calculo)
            ids.append(row["id"])
    log.info("simbionte_batch", sesion_id=str(sid), n=len(ids))
    return {"ok": True, "sesion_id": str(sid), "n_escritos": len(ids), "ids": ids}


@router.post("/consultar")
async def consultar(data: ConsultaIn):
    """El LLM consulta resultados via tool_use. Endpoint principal de OMC-95.

    Tools soportados:
      - consultar_formula: busca semántica de una fórmula por nombre
      - consultar_patron: busca patrones que coincidan con señales
      - calcular: devuelve resultados por tipo (diagnostico, relaciones, riesgo, prescripcion, todo)
      - cascada_preguntas: devuelve enlaces/preguntas encadenadas desde una fórmula
    """
    import json
    pool = await _pool()

    tool = data.tool
    params = data.params
    sid = data.sesion_id

    async with pool.acquire() as conn:
        if tool == "consultar_formula":
            nombre = params.get("nombre", "")
            rows = await conn.fetch("""
                SELECT nombre, pregunta, polos, presupuestos, razonamiento,
                       valor, valor_texto, texto_legible
                FROM resultados_simbionte
                WHERE sesion_id = $1 AND nombre ILIKE $2
                ORDER BY created_at DESC LIMIT 5
            """, sid, f"%{nombre}%")

            if not rows:
                result = f"Formula '{nombre}' no encontrada en esta sesion."
            else:
                lines = []
                for r in rows:
                    polos = json.loads(r["polos"]) if r["polos"] else []
                    presup = json.loads(r["presupuestos"]) if r["presupuestos"] else []
                    lines.append(
                        f"**{r['nombre']}** — {r['pregunta'] or '?'}\n"
                        f"  Eje: {' <-> '.join(polos) if polos else '?'}\n"
                        f"  Presupuestos: {'; '.join(presup) if presup else '?'}\n"
                        f"  Valor: {r['valor']:.4f} -> {r['valor_texto']}\n"
                        f"  {r['texto_legible'] or ''}\n"
                        f"  Razonamiento: {(r['razonamiento'] or '')[:300]}"
                    )
                result = "\n\n".join(lines)

        elif tool == "consultar_patron":
            senales = params.get("senales", "")
            rows = await conn.fetch("""
                SELECT nombre, patron_match, isomorfismo, precedentes, prescripcion,
                       texto_legible, valor, valor_texto
                FROM resultados_simbionte
                WHERE sesion_id = $1 AND tipo = 'patron'
                ORDER BY created_at DESC LIMIT 5
            """, sid)

            if not rows:
                # Buscar por texto en todos los resultados
                rows = await conn.fetch("""
                    SELECT nombre, texto_legible, valor, valor_texto, patron_match, prescripcion
                    FROM resultados_simbionte
                    WHERE sesion_id = $1
                      AND (texto_legible ILIKE $2 OR patron_match ILIKE $2 OR nombre ILIKE $2)
                    ORDER BY ABS(valor) DESC NULLS LAST LIMIT 5
                """, sid, f"%{senales.split()[0] if senales.split() else ''}%")

            if not rows:
                result = "Sin patrones historicos encontrados para estas senales."
            else:
                lines = []
                for r in rows:
                    prec = json.loads(r["precedentes"]) if r.get("precedentes") and r["precedentes"] else []
                    lines.append(
                        f"**{r['nombre']}**"
                        f"{' — Patron: ' + r['patron_match'] if r.get('patron_match') else ''}\n"
                        f"  {r.get('texto_legible', '')}\n"
                        f"  Precedentes: {', '.join(prec) if prec else 'ninguno'}\n"
                        f"  Prescripcion: {r.get('prescripcion', 'N/A')}"
                    )
                result = "\n\n".join(lines)

        elif tool == "calcular":
            tipo = params.get("tipo", "todo")

            # Mapeo: categorías analíticas → tipos del clasificador
            TIPO_MAP = {
                "diagnostico": ["nivel", "tasa_cambio", "tasa_crecimiento", "varianza",
                                "coef_variacion", "gap", "persistencia", "aceleracion",
                                "acumulado", "desviacion"],
                "relaciones": ["correlacion", "elasticidad", "semi_elasticidad",
                               "covarianza", "causalidad", "beta"],
                "riesgo": ["varianza", "coef_variacion", "persistencia", "prima_riesgo",
                           "riesgo", "sharpe", "entropia"],
                "prescripcion": ["elasticidad", "multiplicador", "correlacion", "gap",
                                 "tasa_crecimiento", "optimo", "eficiencia"],
            }

            if tipo == "todo":
                rows = await conn.fetch("""
                    SELECT nombre, tipo, valor, valor_texto, texto_legible, categoria
                    FROM resultados_simbionte
                    WHERE sesion_id = $1 AND valor IS NOT NULL
                    ORDER BY ABS(valor) DESC NULLS LAST LIMIT 20
                """, sid)
            elif tipo in TIPO_MAP:
                # Buscar por lista de tipos del clasificador
                tipos_lista = TIPO_MAP[tipo]
                rows = await conn.fetch("""
                    SELECT nombre, tipo, valor, valor_texto, texto_legible, categoria
                    FROM resultados_simbionte
                    WHERE sesion_id = $1 AND tipo = ANY($2) AND valor IS NOT NULL
                    ORDER BY ABS(valor) DESC NULLS LAST LIMIT 15
                """, sid, tipos_lista)
            else:
                # Tipo literal (compatibilidad directa)
                rows = await conn.fetch("""
                    SELECT nombre, tipo, valor, valor_texto, texto_legible, categoria
                    FROM resultados_simbionte
                    WHERE sesion_id = $1 AND tipo = $2 AND valor IS NOT NULL
                    ORDER BY ABS(valor) DESC NULLS LAST LIMIT 15
                """, sid, tipo)

            if not rows:
                result = f"Sin resultados para tipo '{tipo}'."
            else:
                lines = []
                for r in rows:
                    sg = "+" if (r["valor"] or 0) >= 0 else ""
                    lines.append(f"{r['nombre']}: {sg}{r['valor']:.4f} -> {r['valor_texto']} ({r['texto_legible'] or r['tipo']})")
                result = "\n".join(lines)

        elif tool == "cascada_preguntas":
            formula = params.get("formula", "")
            rows = await conn.fetch("""
                SELECT nombre, enlaces, pregunta
                FROM resultados_simbionte
                WHERE sesion_id = $1 AND nombre ILIKE $2 AND enlaces IS NOT NULL
                LIMIT 1
            """, sid, f"%{formula}%")

            if not rows:
                result = f"Sin cascada para '{formula}'."
            else:
                r = rows[0]
                enlaces = json.loads(r["enlaces"]) if r["enlaces"] else []
                if enlaces:
                    lines = [f"Desde {r['nombre']}:"]
                    for e in enlaces[:10]:
                        if isinstance(e, dict):
                            lines.append(f"  -> {e.get('destino', '?')}: {e.get('pregunta', '?')}")
                            if e.get("razon"):
                                lines.append(f"     Razon: {e['razon']}")
                        elif isinstance(e, (list, tuple)) and len(e) >= 3:
                            lines.append(f"  -> {e[1]}: {e[2] if len(e) > 2 else '?'}")
                    result = "\n".join(lines)
                else:
                    result = f"Formula '{formula}' sin enlaces de cascada."
        elif tool == "consultar_isomorfismo":
            formula = params.get("formula", "")
            # Buscar en om_conocimiento_proyecto via pgvector (similaridad semántica)
            try:
                query_text = f"isomorfismo gramática {formula} cross-domain"
                pgv_rows = await conn.fetch("""
                    SELECT contenido, tipo, 1 - (embedding <=> (
                        SELECT embedding FROM om_conocimiento_proyecto
                        WHERE contenido ILIKE $2 LIMIT 1
                    )) as similaridad
                    FROM om_conocimiento_proyecto
                    WHERE tipo IN ('patron_validado', 'arquitectura', 'insight')
                    ORDER BY embedding <=> (
                        SELECT embedding FROM om_conocimiento_proyecto
                        WHERE contenido ILIKE $2 LIMIT 1
                    )
                    LIMIT 5
                """, sid, f"%{formula}%")
            except Exception:
                pgv_rows = []

            # Fallback: buscar isomorfismos en resultados de la sesión
            iso_rows = await conn.fetch("""
                SELECT nombre, isomorfismo, patron_match, texto_legible, prescripcion
                FROM resultados_simbionte
                WHERE sesion_id = $1 AND isomorfismo IS NOT NULL
                ORDER BY created_at LIMIT 10
            """, sid)

            lines = []
            if iso_rows:
                for r in iso_rows:
                    lines.append(f"**{r['nombre']}** — Isomorfismo: {r['isomorfismo']}\n  {r['texto_legible'] or ''}")
            if pgv_rows:
                for r in pgv_rows:
                    lines.append(f"--- pgvector ---\n{r['contenido'][:300]}")

            result = "\n\n".join(lines) if lines else f"Sin isomorfismos encontrados para '{formula}'."
            rows = iso_rows or pgv_rows or []

        else:
            raise HTTPException(400, f"Tool '{tool}' no reconocido. Opciones: consultar_formula, consultar_patron, calcular, cascada_preguntas, consultar_isomorfismo")

    # Auditoría
    n_tokens = len(result)
    await _audit(sid, tool, params, len(rows) if 'rows' in dir() else 0, n_tokens)

    return {"ok": True, "tool": tool, "resultado": result[:3000]}  # Cap 3K chars


@router.get("/sesion/{sesion_id}")
async def estado_sesion(sesion_id: UUID):
    """Estado completo de una sesión: cuántos resultados, por tipo, último."""
    pool = await _pool()
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            "SELECT COUNT(*) FROM resultados_simbionte WHERE sesion_id = $1", sesion_id)
        por_tipo = await conn.fetch("""
            SELECT tipo, COUNT(*) as n, AVG(ABS(valor)) as avg_abs_valor
            FROM resultados_simbionte WHERE sesion_id = $1
            GROUP BY tipo ORDER BY n DESC
        """, sesion_id)
        auditorias = await conn.fetchval(
            "SELECT COUNT(*) FROM auditorias_simbionte WHERE sesion_id = $1", sesion_id)
    return {
        "sesion_id": str(sesion_id),
        "total_resultados": total,
        "por_tipo": [{"tipo": r["tipo"], "n": r["n"], "avg_abs": float(r["avg_abs_valor"] or 0)} for r in por_tipo],
        "total_consultas_llm": auditorias,
    }


@router.get("/auditorias/{sesion_id}")
async def listar_auditorias(sesion_id: UUID):
    """Qué consultó el LLM y cuándo."""
    pool = await _pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT tool_name, input_params, n_resultados, tokens_respuesta, created_at
            FROM auditorias_simbionte WHERE sesion_id = $1
            ORDER BY created_at
        """, sesion_id)
    return [dict(r) for r in rows]
