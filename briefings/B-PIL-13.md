# B-PIL-13: Séquito de 24 Asesores — Consejo con ACD (INT×P×R)

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-12 (ACD tenant + dashboard), Motor vN pipeline operativo
**Coste:** ~$0.30-0.50 por sesión de consejo (Tier 3-4, 4-6 asesores paralelos)

---

## CONTEXTO

El Séquito es el diferenciador de OMNI-MIND. No es un chatbot — es un consejo de 24 asesores especializados, cada uno con un ángulo único, convocados por el ACD según el estado del negocio.

Flujo:
1. Jesús plantea pregunta/decisión en Modo Profundo
2. ACD diagnostica estado actual → prescribe INT×P×R óptimas
3. Se convocan 4-6 asesores con sus P y R asignados
4. Ejecución paralela (cada asesor = 1 LLM call con prompt especializado)
5. Integrador sintetiza + detecta puntos ciegos cruzados
6. Decisión ternaria: cierre / inerte / tóxico

**Fuente:** Exocortex v2.1 S8, S17.3

---

## FASE A: Backend — Motor del Séquito

### A1. Crear `src/pilates/sequito.py`

```python
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

# Pensamientos (P) y Razonamientos (R) — descripciones cortas para el prompt
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
            coste = data.get("usage", {}).get("total_tokens", 0) * 0.000001  # ~$1/M tokens

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
    """Convoca el Consejo de Asesores con selección ACD.

    Args:
        pregunta: La pregunta/decisión del dueño.
        profundidad: 'rapida' (3 asesores), 'normal' (5), 'profunda' (8).
        ints_forzadas: Si se especifica, usar estas INTs en vez de la prescripción ACD.

    Returns:
        SesionConsejo con todas las respuestas + síntesis.
    """
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
    coste_total = sum(r.coste_usd for r in respuestas) + 0.001  # +síntesis
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
```

---

## FASE B: Endpoints en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR schemas + endpoints:

### Schemas

```python
class ConsejoRequest(BaseModel):
    pregunta: str
    profundidad: str = Field(default="normal", pattern="^(rapida|normal|profunda)$")
    ints_forzadas: Optional[list[str]] = None

class DecisionTernaria(BaseModel):
    sesion_id: UUID
    decision: str = Field(pattern="^(cierre|inerte|toxico)$")
    confianza: float = Field(ge=0, le=1)
    razon: Optional[str] = None
```

### Endpoints

```python
# ============================================================
# SÉQUITO DE ASESORES
# ============================================================

@router.post("/consejo")
async def convocar_consejo_endpoint(data: ConsejoRequest):
    """Convoca el Consejo de Asesores.
    
    Coste: ~$0.05-0.50 según profundidad (3-8 calls LLM).
    """
    from src.pilates.sequito import convocar_consejo
    sesion = await convocar_consejo(
        pregunta=data.pregunta,
        profundidad=data.profundidad,
        ints_forzadas=data.ints_forzadas,
    )
    return {
        "status": "ok",
        "estado_acd": sesion.estado_acd_pre,
        "asesores_convocados": len(sesion.asesores),
        "respuestas": [{
            "int_id": r.int_id, "nombre": r.nombre,
            "P": r.pensamiento, "R": r.razonamiento,
            "respuesta": r.respuesta,
        } for r in sesion.asesores],
        "sintesis": sesion.sintesis,
        "puntos_ciegos": sesion.puntos_ciegos,
        "prescripcion_acd": sesion.prescripcion,
        "coste_usd": sesion.coste_total,
        "tiempo_s": sesion.tiempo_total,
    }


@router.get("/consejo/historial")
async def historial_consejo(limit: int = 10):
    """Historial de sesiones del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, pregunta, profundidad, estado_acd_pre,
                   inteligencias_convocadas, sintesis,
                   puntos_ciegos_cruzados, decision_ternaria,
                   coste_api, tiempo_ejecucion_s, created_at
            FROM om_sesiones_consejo
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/consejo/{sesion_id}")
async def detalle_consejo(sesion_id: UUID):
    """Detalle completo de una sesión del Consejo."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT * FROM om_sesiones_consejo WHERE id = $1 AND tenant_id = $2
        """, sesion_id, TENANT)
        if not row:
            raise HTTPException(404, "Sesión no encontrada")
    return _row_to_dict(row)


@router.post("/consejo/{sesion_id}/decision")
async def registrar_decision(sesion_id: UUID, data: DecisionTernaria):
    """Registra decisión ternaria post-consejo: cierre/inerte/tóxico."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            UPDATE om_sesiones_consejo
            SET decision_ternaria = $1, decision_confianza = $2,
                decision_razon = $3, decision_fecha = CURRENT_DATE
            WHERE id = $4 AND tenant_id = $5
        """, data.decision, data.confianza, data.razon, sesion_id, TENANT)
        if result == "UPDATE 0":
            raise HTTPException(404, "Sesión no encontrada")
    return {"status": "ok"}


@router.get("/asesores")
async def listar_asesores():
    """Lista los 24 asesores disponibles."""
    from src.pilates.sequito import ASESORES
    return [{"id": k, **v} for k, v in ASESORES.items()]
```

---

## FASE C: Frontend — Pestaña Consejo en Modo Profundo

### C1. Actualizar api.js

```javascript
// Séquito
export const convocarConsejo = (data) =>
  request('/consejo', { method: 'POST', body: JSON.stringify(data) });
export const getHistorialConsejo = () => request('/consejo/historial');
export const getDetalleConsejo = (id) => request(`/consejo/${id}`);
export const registrarDecision = (id, data) =>
  request(`/consejo/${id}/decision`, { method: 'POST', body: JSON.stringify(data) });
export const getAsesores = () => request('/asesores');
```

### C2. Crear `frontend/src/Consejo.jsx`

```jsx
import { useState, useEffect } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export default function Consejo() {
  const [pregunta, setPregunta] = useState('');
  const [profundidad, setProfundidad] = useState('normal');
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState('nuevo'); // nuevo | historial | detalle

  useEffect(() => { loadHistorial(); }, []);

  async function loadHistorial() {
    const h = await fetch(`${BASE}/pilates/consejo/historial`).then(r => r.json());
    setHistorial(h);
  }

  async function convocar() {
    if (!pregunta.trim()) return;
    setLoading(true);
    try {
      const r = await fetch(`${BASE}/pilates/consejo`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ pregunta, profundidad }),
      }).then(r => r.json());
      setResultado(r);
      setView('resultado');
      loadHistorial();
    } catch (e) { alert(e.message); }
    setLoading(false);
  }

  async function registrarDecision(sesionId, decision) {
    const confianza = prompt('Confianza (0-1):', '0.7');
    if (!confianza) return;
    await fetch(`${BASE}/pilates/consejo/${sesionId}/decision`, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ decision, confianza: parseFloat(confianza) }),
    });
    loadHistorial();
  }

  return (
    <div>
      {/* Nav */}
      <div style={{display:'flex', gap:8, marginBottom:16}}>
        <button onClick={() => setView('nuevo')}
          style={view === 'nuevo' ? s.tabActive : s.tab}>Nueva consulta</button>
        <button onClick={() => setView('historial')}
          style={view === 'historial' ? s.tabActive : s.tab}>Historial</button>
      </div>

      {/* NUEVA CONSULTA */}
      {view === 'nuevo' && (
        <div>
          <textarea style={s.textarea} rows={4}
            placeholder="¿Qué decisión necesitas tomar? ¿Qué quieres explorar?"
            value={pregunta} onChange={e => setPregunta(e.target.value)} />
          <div style={{display:'flex', gap:8, margin:'12px 0'}}>
            {['rapida','normal','profunda'].map(p => (
              <button key={p} onClick={() => setProfundidad(p)}
                style={profundidad === p ? s.chipActive : s.chip}>
                {p} ({p === 'rapida' ? '3' : p === 'normal' ? '5' : '8'} asesores)
              </button>
            ))}
          </div>
          <button style={s.btn} onClick={convocar} disabled={loading || !pregunta.trim()}>
            {loading ? 'Convocando consejo...' : `Convocar (~$${
              profundidad === 'rapida' ? '0.05' : profundidad === 'normal' ? '0.15' : '0.40'
            })`}
          </button>
        </div>
      )}

      {/* RESULTADO */}
      {view === 'resultado' && resultado && (
        <div>
          <div style={s.card}>
            <div style={{fontSize:12, color:'#9ca3af'}}>
              Estado ACD: {resultado.estado_acd || 'sin diagnóstico'} ·
              {resultado.asesores_convocados} asesores · ${resultado.coste_usd} · {resultado.tiempo_s}s
            </div>
          </div>

          {/* Respuestas por asesor */}
          {resultado.respuestas.map((r, i) => (
            <div key={i} style={{...s.card, borderLeft:`3px solid hsl(${i*40}, 70%, 60%)`}}>
              <div style={{fontWeight:600, fontSize:14}}>
                {r.nombre} <span style={{color:'#9ca3af', fontWeight:400}}>({r.int_id} · {r.P}+{r.R})</span>
              </div>
              <div style={{fontSize:13, marginTop:6, lineHeight:1.6, whiteSpace:'pre-wrap'}}>
                {r.respuesta}
              </div>
            </div>
          ))}

          {/* Síntesis */}
          <div style={{...s.card, borderLeft:'3px solid #6366f1', background:'#faf5ff'}}>
            <h3 style={{fontSize:14, fontWeight:600, marginBottom:8}}>Síntesis del Integrador</h3>
            <div style={{fontSize:13, lineHeight:1.6, whiteSpace:'pre-wrap'}}>{resultado.sintesis}</div>
          </div>

          {/* Puntos ciegos */}
          {resultado.puntos_ciegos?.length > 0 && (
            <div style={{...s.card, borderLeft:'3px solid #f97316'}}>
              <h3 style={{fontSize:14, fontWeight:600, marginBottom:8}}>Puntos ciegos cruzados</h3>
              {resultado.puntos_ciegos.map((p, i) => (
                <div key={i} style={{fontSize:13, padding:'4px 0'}}>• {p}</div>
              ))}
            </div>
          )}

          <button style={{...s.btn, marginTop:12}} onClick={() => { setView('nuevo'); setPregunta(''); setResultado(null); }}>
            Nueva consulta
          </button>
        </div>
      )}

      {/* HISTORIAL */}
      {view === 'historial' && (
        <div>
          {historial.length === 0
            ? <p style={{color:'#9ca3af'}}>Sin sesiones anteriores</p>
            : historial.map((h, i) => (
              <div key={i} style={s.card}>
                <div style={{fontWeight:500}}>{h.pregunta?.slice(0, 100)}</div>
                <div style={{fontSize:12, color:'#6b7280', marginTop:4}}>
                  {h.inteligencias_convocadas?.join(', ')} ·
                  {h.profundidad} · ${h.coste_api} ·
                  {String(h.created_at).slice(0, 10)}
                </div>
                <div style={{fontSize:12, marginTop:4}}>
                  {h.sintesis?.slice(0, 150)}...
                </div>
                {h.decision_ternaria
                  ? <span style={{
                      fontSize:11, padding:'2px 8px', borderRadius:4, marginTop:6, display:'inline-block',
                      background: h.decision_ternaria === 'cierre' ? '#dcfce7' :
                                  h.decision_ternaria === 'toxico' ? '#fee2e2' : '#f3f4f6',
                      color: h.decision_ternaria === 'cierre' ? '#16a34a' :
                             h.decision_ternaria === 'toxico' ? '#dc2626' : '#6b7280',
                    }}>{h.decision_ternaria}</span>
                  : <div style={{display:'flex', gap:4, marginTop:8}}>
                      <button style={s.chipGreen} onClick={() => registrarDecision(h.id, 'cierre')}>Cierre</button>
                      <button style={s.chipGray} onClick={() => registrarDecision(h.id, 'inerte')}>Inerte</button>
                      <button style={s.chipRed} onClick={() => registrarDecision(h.id, 'toxico')}>Tóxico</button>
                    </div>
                }
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

const s = {
  tab: { padding:'6px 14px', background:'none', border:'1px solid #e5e7eb', borderRadius:6, fontSize:13, cursor:'pointer' },
  tabActive: { padding:'6px 14px', background:'#6366f1', border:'none', borderRadius:6, fontSize:13, color:'#fff', cursor:'pointer' },
  textarea: { width:'100%', padding:12, border:'1px solid #d1d5db', borderRadius:8, fontSize:14, resize:'vertical', boxSizing:'border-box' },
  chip: { padding:'4px 12px', border:'1px solid #d1d5db', borderRadius:20, fontSize:12, cursor:'pointer', background:'#fff' },
  chipActive: { padding:'4px 12px', border:'none', borderRadius:20, fontSize:12, cursor:'pointer', background:'#6366f1', color:'#fff' },
  chipGreen: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#dcfce7', color:'#16a34a' },
  chipGray: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#f3f4f6', color:'#6b7280' },
  chipRed: { padding:'4px 10px', border:'none', borderRadius:4, fontSize:11, cursor:'pointer', background:'#fee2e2', color:'#dc2626' },
  btn: { padding:'10px 20px', background:'#6366f1', color:'#fff', border:'none', borderRadius:8, fontSize:14, fontWeight:500, cursor:'pointer', width:'100%' },
  card: { background:'#fff', borderRadius:10, padding:14, marginBottom:10, boxShadow:'0 1px 3px rgba(0,0,0,0.06)' },
};
```

### C3. Integrar en Profundo.jsx

**Archivo:** `frontend/src/Profundo.jsx` — AÑADIR tab 'consejo' al array de tabs y al render:

En el tabs array: añadir `'consejo'` con label `'Consejo'`.

En el render, AÑADIR:

```jsx
      {tab === 'consejo' && <Consejo />}
```

Y el import:
```jsx
import Consejo from './Consejo';
```

---

## Pass/fail

- `src/pilates/sequito.py` creado con 24 asesores, 15 Ps, 12 Rs
- POST /pilates/consejo convoca asesores en paralelo con LLM calls
- Asesores seleccionados por prescripción ACD (último diagnóstico)
- Cada asesor recibe datos reales del tenant + su P y R asignados
- Integrador sintetiza + detecta puntos ciegos cruzados
- Resultado almacenado en om_sesiones_consejo con todos los campos
- GET /pilates/consejo/historial lista sesiones anteriores
- POST /pilates/consejo/{id}/decision registra decisión ternaria
- GET /pilates/asesores lista los 24 disponibles
- Frontend Consejo.jsx: textarea + profundidad + respuestas coloreadas + síntesis + decisión ternaria
- Coste: ~$0.05 rápida, ~$0.15 normal, ~$0.40 profunda

---

## EJEMPLO CONCRETO

Jesús pregunta: "¿Debería subir los precios de los grupos de 105€ a 120€?"

Si el ACD dice estado=genio_mortal (S+ Se+ C-), prescripción={ints: [INT-12, INT-09, INT-13], ps: [P12, P13], rs: [R04, R12]}:

- **El Narrador (INT-12, P12+R04):** "La historia que cuentas al subir precio es 'valgo más'. Pero la analogía con estudios premium en Madrid es que cobran 150€ con 2 instructores. Tú estás solo — si te pones malo, ¿qué pasa con los 120€?"
- **El Lingüista (INT-09, P13+R12):** "No es subir precio. Es rediseñar la oferta. 120€ con sesión de prueba gratis y protocolo escrito = propuesta diferente."
- **El Prospectivista (INT-13, P12+R04):** "En 6 meses, 2 estudios nuevos en Logroño. El que tiene el precio más bajo gana el volumen. El que tiene la historia más fuerte gana el margen."
- **Integrador:** "Los tres convergen: subir precio SIN documentar el método ni tener plan de sustitución es arriesgado. Primero F7 (documentar), luego subir."
- **Puntos ciegos:** "Nadie mencionó qué pasa con los clientes actuales al cambiar. Ni el impacto fiscal de más ingreso."
