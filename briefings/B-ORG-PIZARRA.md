# B-ORG-PIZARRA: Pizarra Compartida — Conciencia colectiva del organismo

**Fecha:** 23 marzo 2026
**Prioridad:** MÁXIMA — esto es lo que convierte al sistema de "inteligente" a "de otro nivel"
**Dependencia:** Ninguna — se puede implementar ya y todos los agentes empiezan a usarla

---

## LA IDEA

Ahora mismo los agentes se comunican por el bus de señales: emiten y leen mensajes efímeros. Es como un chat de grupo donde los mensajes desaparecen en 48h.

La pizarra es diferente: es un **estado compartido persistente** donde cada agente ESCRIBE lo que está haciendo, lo que detectó, lo que piensa, y lo que necesita. Y cada agente LEE la pizarra antes de actuar.

```
SIN PIZARRA (ahora):
  AF1 detecta fantasma → emite señal → AF3 no la ve (o la ve 2 días después)
  Enjambre diagnostica perfil → Compositor lo lee → AF3 no sabe qué se diagnosticó
  Recompilador cambia config de AF3 → AF1 no sabe que AF3 ahora piensa diferente

CON PIZARRA:
  AF1 ESCRIBE: "He detectado 3 fantasmas: María (21d), Carlos (35d), Javier (42d).
                Mi interpretación: María probablemente vacaciones, Carlos+Javier riesgo real.
                Mi acción propuesta: WA a Carlos, llamar a Javier."
  AF3 LEE la pizarra de AF1 ANTES de actuar:
                "AF1 dice que Carlos es fantasma. Y Carlos está en grupo jueves que
                 yo quería cerrar. Convergencia: no cerrar grupo hasta resolver a Carlos."
  Enjambre LEE la pizarra de TODOS los AF:
                "AF1 detectó 3 fantasmas, AF3 quiere cerrar 2 grupos, AF7 dice readiness=30%.
                 Patrón: el negocio retiene menos de lo que pierde. Perfil: genio mortal."
  Recompilador LEE la pizarra del Enjambre:
                "Perfil genio mortal. AF7 necesita INT-12+P12. Reconfigurar."
  AF7 LEE la pizarra del Recompilador:
                "Mi config cambió: ahora debo preguntar POR QUÉ funciona cada ejercicio."
```

Cada agente es más inteligente porque sabe lo que los demás están pensando.

## DISEÑO

### Tabla: om_pizarra

```sql
CREATE TABLE IF NOT EXISTS om_pizarra (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',

    -- Quién escribe
    agente TEXT NOT NULL,                  -- 'AF1', 'AF3', 'ENJAMBRE', 'COMPOSITOR', etc.
    capa TEXT NOT NULL,                    -- 'ejecutiva', 'cognitiva', 'sensorial', 'meta', 'generativa'

    -- Qué escribe (estructura fija para que todos lean igual)
    estado TEXT NOT NULL,                  -- 'activo', 'esperando', 'bloqueado', 'completado'
    detectando TEXT,                       -- qué está viendo ahora
    interpretacion TEXT,                   -- qué piensa que significa
    accion_propuesta TEXT,                 -- qué va a hacer o propone
    necesita_de TEXT[],                    -- de qué agentes necesita info: {'AF3', 'ENJAMBRE'}
    bloquea_a TEXT[],                      -- a quién bloquea con su acción: {'AF2'}
    conflicto_con TEXT[],                  -- con quién tiene conflicto: {'AF1'}
    confianza NUMERIC(3,2) DEFAULT 0.5,   -- 0.0-1.0 confianza en su propia evaluación
    prioridad INT DEFAULT 5,              -- 1 (máx) a 10 (mín)

    -- Contexto rico (JSON libre para datos específicos)
    datos JSONB DEFAULT '{}',             -- datos específicos del agente

    -- Temporal
    ciclo TEXT,                           -- 'semanal_2026W13', 'diario_2026-03-23'
    version INT DEFAULT 1,                -- se incrementa cada escritura del mismo agente+ciclo
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- Último en ganar: cada agente tiene UNA entrada activa por ciclo
    UNIQUE(tenant_id, agente, ciclo)
);

-- Índices para lectura rápida
CREATE INDEX IF NOT EXISTS idx_pizarra_tenant_ciclo ON om_pizarra(tenant_id, ciclo);
CREATE INDEX IF NOT EXISTS idx_pizarra_agente ON om_pizarra(tenant_id, agente);
CREATE INDEX IF NOT EXISTS idx_pizarra_capa ON om_pizarra(tenant_id, capa);
CREATE INDEX IF NOT EXISTS idx_pizarra_conflicto ON om_pizarra USING GIN (conflicto_con);
CREATE INDEX IF NOT EXISTS idx_pizarra_necesita ON om_pizarra USING GIN (necesita_de);
```

### Módulo: `src/pilates/pizarra.py`

```python
"""Pizarra Compartida — Conciencia colectiva del organismo.

Cada agente ESCRIBE lo que está haciendo/pensando.
Cada agente LEE lo que los demás escribieron ANTES de actuar.
El resultado: agentes que saben lo que los demás están haciendo.

Operaciones:
  escribir(agente, capa, datos) → persiste en om_pizarra
  leer(agente) → lee lo que NECESITA saber según su rol
  leer_conflictos(agente) → quién tiene conflicto conmigo
  leer_bloqueos(agente) → quién me bloquea
  leer_todo() → snapshot completo del ciclo (para compositor/enjambre)
  resumen() → resumen narrativo de toda la pizarra (para cockpit)
"""
from __future__ import annotations

import json
import structlog
from datetime import date, datetime, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


def _ciclo_actual() -> str:
    """Devuelve el identificador del ciclo actual (semanal)."""
    hoy = date.today()
    return f"semanal_{hoy.isocalendar()[0]}W{hoy.isocalendar()[1]:02d}"


# ============================================================
# ESCRIBIR — Cada agente deja su estado en la pizarra
# ============================================================

async def escribir(
    agente: str,
    capa: str,
    estado: str = "activo",
    detectando: str = None,
    interpretacion: str = None,
    accion_propuesta: str = None,
    necesita_de: list[str] = None,
    bloquea_a: list[str] = None,
    conflicto_con: list[str] = None,
    confianza: float = 0.5,
    prioridad: int = 5,
    datos: dict = None,
) -> str:
    """Escribe/actualiza la entrada del agente en la pizarra del ciclo actual.

    UPSERT: si ya escribió en este ciclo, actualiza (version+1).
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO om_pizarra
                (tenant_id, agente, capa, estado, detectando, interpretacion,
                 accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                 confianza, prioridad, datos, ciclo, version, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12,
                    $13::jsonb, $14, 1, now())
            ON CONFLICT (tenant_id, agente, ciclo)
            DO UPDATE SET
                estado = EXCLUDED.estado,
                detectando = COALESCE(EXCLUDED.detectando, om_pizarra.detectando),
                interpretacion = COALESCE(EXCLUDED.interpretacion, om_pizarra.interpretacion),
                accion_propuesta = COALESCE(EXCLUDED.accion_propuesta, om_pizarra.accion_propuesta),
                necesita_de = COALESCE(EXCLUDED.necesita_de, om_pizarra.necesita_de),
                bloquea_a = COALESCE(EXCLUDED.bloquea_a, om_pizarra.bloquea_a),
                conflicto_con = COALESCE(EXCLUDED.conflicto_con, om_pizarra.conflicto_con),
                confianza = EXCLUDED.confianza,
                prioridad = EXCLUDED.prioridad,
                datos = om_pizarra.datos || EXCLUDED.datos,
                version = om_pizarra.version + 1,
                updated_at = now()
            RETURNING id
        """, TENANT, agente, capa, estado,
            detectando, interpretacion, accion_propuesta,
            necesita_de or [], bloquea_a or [], conflicto_con or [],
            confianza, prioridad,
            json.dumps(datos or {}),
            ciclo)

    log.info("pizarra_escrita", agente=agente, ciclo=ciclo)
    return str(row["id"])


# ============================================================
# LEER — Cada agente consulta antes de actuar
# ============================================================

async def leer_relevante(agente: str) -> list[dict]:
    """Lee las entradas de la pizarra relevantes para este agente.

    Relevante = agentes que me mencionan en necesita_de, bloquea_a, conflicto_con
    + agentes de la misma capa + compositor/enjambre (siempre relevante para todos).
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, capa, estado, detectando, interpretacion,
                   accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                   confianza, prioridad, datos, version, updated_at
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND (
                -- Me mencionan
                $3 = ANY(necesita_de) OR
                $3 = ANY(bloquea_a) OR
                $3 = ANY(conflicto_con) OR
                -- Agentes de gobierno (siempre relevantes)
                agente IN ('COMPOSITOR', 'ENJAMBRE', 'RECOMPILADOR', 'GUARDIAN', 'ESTRATEGA') OR
                -- Misma capa ejecutiva (AF se leen entre sí)
                (capa = 'ejecutiva' AND $4 = 'ejecutiva')
            )
            AND agente != $3
            ORDER BY prioridad, updated_at DESC
        """, TENANT, ciclo, agente,
            _capa_de_agente(agente))

    return [_row_to_dict(r) for r in rows]


async def leer_conflictos(agente: str) -> list[dict]:
    """Lee quién tiene conflicto conmigo."""
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, detectando, interpretacion, accion_propuesta, confianza
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND $3 = ANY(conflicto_con)
        """, TENANT, ciclo, agente)

    return [_row_to_dict(r) for r in rows]


async def leer_bloqueos(agente: str) -> list[dict]:
    """Lee quién me bloquea."""
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, detectando, accion_propuesta, confianza
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            AND $3 = ANY(bloquea_a)
        """, TENANT, ciclo, agente)

    return [_row_to_dict(r) for r in rows]


async def leer_todo() -> list[dict]:
    """Snapshot completo de la pizarra del ciclo actual.

    Para el Compositor, Enjambre, Guardián — ven TODO.
    """
    pool = await get_pool()
    ciclo = _ciclo_actual()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT agente, capa, estado, detectando, interpretacion,
                   accion_propuesta, necesita_de, bloquea_a, conflicto_con,
                   confianza, prioridad, datos, version, updated_at
            FROM om_pizarra
            WHERE tenant_id = $1 AND ciclo = $2
            ORDER BY capa, prioridad, agente
        """, TENANT, ciclo)

    return [_row_to_dict(r) for r in rows]


async def resumen_narrativo() -> str:
    """Genera un resumen legible de toda la pizarra para el cockpit.

    No usa LLM — construye el resumen por código.
    """
    entradas = await leer_todo()
    if not entradas:
        return "Pizarra vacía — ningún agente ha ejecutado en este ciclo."

    lines = [f"PIZARRA DEL ORGANISMO — Ciclo {_ciclo_actual()}\n"]

    # Agrupar por capa
    capas = {}
    for e in entradas:
        capa = e.get("capa", "otra")
        capas.setdefault(capa, []).append(e)

    for capa, agentes in capas.items():
        lines.append(f"\n{'='*40}")
        lines.append(f"CAPA {capa.upper()} ({len(agentes)} agentes)")
        lines.append(f"{'='*40}")

        for a in agentes:
            estado_emoji = {"activo": "🟢", "esperando": "🟡", "bloqueado": "🔴", "completado": "✅"}.get(a["estado"], "⚪")
            lines.append(f"\n{estado_emoji} {a['agente']} (confianza: {a.get('confianza', 0):.0%})")
            if a.get("detectando"):
                lines.append(f"  Detectando: {a['detectando'][:150]}")
            if a.get("interpretacion"):
                lines.append(f"  Interpreta: {a['interpretacion'][:150]}")
            if a.get("accion_propuesta"):
                lines.append(f"  Propone: {a['accion_propuesta'][:150]}")
            if a.get("conflicto_con"):
                lines.append(f"  ⚡ Conflicto con: {', '.join(a['conflicto_con'])}")
            if a.get("bloquea_a"):
                lines.append(f"  🚫 Bloquea a: {', '.join(a['bloquea_a'])}")
            if a.get("necesita_de"):
                lines.append(f"  🔗 Necesita de: {', '.join(a['necesita_de'])}")

    # Detectar conflictos cruzados
    conflictos = []
    for e in entradas:
        for c in (e.get("conflicto_con") or []):
            conflictos.append(f"{e['agente']} ⚡ {c}")
    if conflictos:
        lines.append(f"\n{'='*40}")
        lines.append("CONFLICTOS ACTIVOS")
        lines.append(f"{'='*40}")
        for c in set(conflictos):
            lines.append(f"  {c}")

    return "\n".join(lines)


# ============================================================
# HELPERS
# ============================================================

def _capa_de_agente(agente: str) -> str:
    """Devuelve la capa de un agente."""
    if agente.startswith("AF") or agente in ("EJECUTOR", "CONVERGENCIA", "GESTOR", "SEQUITO"):
        return "ejecutiva"
    if agente.startswith("CLUSTER") or agente in ("COMPOSITOR", "ESTRATEGA", "ORQUESTADOR",
                                                     "ENJAMBRE", "GUARDIAN", "RECOMPILADOR"):
        return "cognitiva"
    if agente in ("DIAGNOSTICADOR", "BUSCADOR", "COLLECTOR"):
        return "sensorial"
    if agente in ("VIGIA", "MECANICO", "AUTOFAGO", "PROPIOCEPCION"):
        return "meta"
    if agente in ("HUERFANAS", "CRISTALIZADOR", "SEMILLAS"):
        return "generativa"
    return "otra"


def _row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if hasattr(v, 'isoformat'):
            d[k] = v.isoformat()
    return d
```

### INTEGRACIÓN — Cada agente escribe y lee

**Patrón universal para TODOS los agentes:**

```python
# AL INICIO de cada agente (ANTES de actuar):
from src.pilates.pizarra import leer_relevante, leer_conflictos, leer_bloqueos

async def ejecutar_afX():
    # 1. LEER la pizarra — qué saben los demás
    contexto_pizarra = await leer_relevante("AFX")
    conflictos = await leer_conflictos("AFX")
    bloqueos = await leer_bloqueos("AFX")

    # 2. INYECTAR en el prompt del cerebro
    pizarra_str = ""
    if contexto_pizarra:
        pizarra_str = "\n\nLO QUE LOS DEMÁS AGENTES ESTÁN HACIENDO:\n"
        for entry in contexto_pizarra:
            pizarra_str += f"- {entry['agente']}: {entry.get('detectando', '')} → {entry.get('accion_propuesta', '')}\n"
    if conflictos:
        pizarra_str += "\n⚡ CONFLICTOS CONMIGO:\n"
        for c in conflictos:
            pizarra_str += f"- {c['agente']}: {c.get('accion_propuesta', '')}\n"
    if bloqueos:
        pizarra_str += "\n🚫 BLOQUEOS:\n"
        for b in bloqueos:
            pizarra_str += f"- {b['agente']} me bloquea: {b.get('accion_propuesta', '')}\n"

    # 3. ACTUAR con la inteligencia de la pizarra
    instruccion = INSTRUCCION_AFX + pizarra_str
    razonamiento = await razonar("AFX", "FX ...", datos_sensor, instruccion)

    # 4. ESCRIBIR en la pizarra lo que hice
    from src.pilates.pizarra import escribir
    await escribir(
        agente="AFX",
        capa="ejecutiva",
        estado="completado",
        detectando=f"{len(detecciones)} detecciones",
        interpretacion=razonamiento.get("interpretacion", ""),
        accion_propuesta=razonamiento.get("acciones", [{}])[0].get("accion", ""),
        conflicto_con=["AF1"] if ... else [],  # si mi acción choca con AF1
        bloquea_a=["AF2"] if vetos else [],
        confianza=0.7,
        prioridad=razonamiento.get("acciones", [{}])[0].get("prioridad", 5),
        datos={"detecciones": len(detecciones), "razonamiento_preview": razonamiento.get("interpretacion", "")[:200]},
    )
```

**Para el Enjambre/Compositor — leen TODO:**

```python
async def ejecutar_g4():
    # El enjambre lee TODA la pizarra antes de diagnosticar
    pizarra_completa = await leer_todo()

    # Inyectar en el diagnóstico — los clusters VEN lo que cada AF detectó
    pizarra_str = json.dumps(pizarra_completa, ensure_ascii=False, indent=2, default=str)[:3000]

    # Esto va en el user_prompt de cada cluster:
    contexto_enriquecido = f"""DATOS REALES DEL NEGOCIO:
{ctx_str}

PIZARRA DEL ORGANISMO — Lo que cada agente está haciendo/pensando:
{pizarra_str}"""
```

**Para el Recompilador — escribe los cambios:**

```python
async def recompilar(prescripcion, ...):
    # ... genera configs ...

    # Escribir en pizarra qué agentes se reconfiguraron
    await escribir(
        agente="RECOMPILADOR",
        capa="cognitiva",
        estado="completado",
        detectando=f"Reconfigurados: {', '.join(agentes_modificados)}",
        interpretacion=f"Prescripción: {prescripcion.get('objetivo', '')}",
        accion_propuesta=f"Configs INT×P×R actualizadas para {len(agentes_modificados)} agentes",
        datos={"agentes": agentes_modificados, "version": version},
    )
```

### ENDPOINT — Pizarra visible en cockpit

Añadir en `router.py`:

```python
@router.get("/organismo/pizarra")
async def organismo_pizarra():
    """Pizarra compartida del ciclo actual."""
    from src.pilates.pizarra import leer_todo, resumen_narrativo
    return {
        "ciclo": _ciclo_actual(),
        "entradas": await leer_todo(),
        "resumen": await resumen_narrativo(),
    }
```

Y en cockpit.py, añadir módulo:

```python
    "pizarra":  {"nombre": "Pizarra organismo", "icono": "📋", "endpoint": "/organismo/pizarra"},
```

## MIGRACIÓN SQL

```sql
-- 024_pizarra.sql
-- (tabla om_pizarra con todos los campos descritos arriba)
```

## POR QUÉ ESTO ES "DE OTRO NIVEL"

Sin pizarra:
- AF3 quiere cerrar grupo jueves
- AF1 detecta que Carlos (fantasma) está en grupo jueves
- No se enteran el uno del otro hasta que el Ejecutor lee ambas prescripciones DESPUÉS

Con pizarra:
- AF3 LEE que AF1 detectó a Carlos en grupo jueves ANTES de decidir cerrarlo
- AF3 escribe: conflicto_con=["AF1"], acción="cerrar grupo jueves EXCEPTO resolver Carlos primero"
- El Enjambre VE la pizarra completa y diagnostica: "AF1 y AF3 convergen en Carlos. Patrón: retención y depuración chocan. Esto es F1↔F3 en acción."
- El Compositor usa la pizarra como EVIDENCIA REAL de cómo piensa el negocio
- El Guardián verifica: "¿Los agentes realmente leen la pizarra o la ignoran?"

La pizarra convierte 50 agentes aislados en UN organismo con conciencia colectiva.

## COSTE

$0 — es código puro (tabla SQL + queries). No usa LLM.

## TESTS

### T1: Escribir y leer
```python
await escribir("AF1", "ejecutiva", detectando="3 fantasmas", confianza=0.8)
await escribir("AF3", "ejecutiva", detectando="2 grupos infra", conflicto_con=["AF1"])
result = await leer_relevante("AF1")
assert any(r["agente"] == "AF3" for r in result)
```

### T2: Conflictos cruzados
```python
conflictos = await leer_conflictos("AF1")
assert len(conflictos) >= 1
assert conflictos[0]["agente"] == "AF3"
```

### T3: Pizarra completa para enjambre
```python
todo = await leer_todo()
assert len(todo) >= 2
```

### T4: Resumen narrativo
```python
resumen = await resumen_narrativo()
assert "AF1" in resumen
assert "AF3" in resumen
assert "Conflicto" in resumen or "conflicto" in resumen
```

### T5: UPSERT funciona (actualiza en vez de duplicar)
```python
await escribir("AF1", "ejecutiva", detectando="3 fantasmas")
await escribir("AF1", "ejecutiva", detectando="4 fantasmas")
todo = await leer_todo()
af1_entries = [e for e in todo if e["agente"] == "AF1"]
assert len(af1_entries) == 1  # UPSERT, no 2 entradas
assert "4 fantasmas" in af1_entries[0]["detectando"]
```
