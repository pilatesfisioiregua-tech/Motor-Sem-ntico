# B-ORG-GENERATIVA: Capa Generativa — El sistema que evoluciona el álgebra

**Fecha:** 23 marzo 2026
**Prioridad:** Media — el organismo funciona sin esto, pero no EVOLUCIONA su propia inteligencia
**Dependencia:** B-ORG-UNIFY-01+02, B-ORG-COG-PR, B-ORG-GUARDIAN ejecutados

---

## QUÉ ES LA CAPA GENERATIVA

Las otras capas APLICAN el álgebra existente. La capa generativa GENERA álgebra nueva:
- Detecta preguntas que nadie hace pero debería (Preguntas Huérfanas)
- Cristaliza patrones emergentes en nuevas reglas (Cristalizador)
- Almacena ideas dormidas que despertarán cuando cambie el estado (Semillas)
- Conecta el Séquito de 24 asesores con el enjambre (puente)

Sin esta capa, el sistema es un autómata sofisticado — aplica lo que sabe.
Con esta capa, el sistema es un organismo que aprende lo que NO sabía.

## ARCHIVO A CREAR

`src/pilates/generativa.py`

## CÓDIGO

```python
"""Capa Generativa — El sistema evoluciona su propia inteligencia.

4 componentes:
  1. Detector de Preguntas Huérfanas: preguntas que ningún agente hace pero debería
  2. Cristalizador: patrones entre ejecuciones → nuevas reglas
  3. Semillas Dormidas: ideas que esperan hasta ser relevantes
  4. Puente Séquito ↔ Enjambre: los 24 asesores alimentan G4

Frecuencia:
  - Huérfanas: cada ejecución de G4
  - Cristalizador: mensual (después del autófago)
  - Semillas: evaluadas cada G4 (¿ya es relevante?)
  - Puente Séquito: bajo demanda (cuando el enjambre necesita profundidad)

Modelo: claude-sonnet-4.6 (huérfanas + cristalizador), gpt-4o (puente séquito)
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
from datetime import date, datetime, timedelta, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4.6")
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")


# ============================================================
# 1. DETECTOR DE PREGUNTAS HUÉRFANAS
# ============================================================

SYSTEM_HUERFANAS = """Eres el Detector de Preguntas Huérfanas del organismo OMNI-MIND.

Tu trabajo: recibir TODO lo que el enjambre diagnosticó y encontrar las preguntas
que NADIE HIZO pero que DEBERÍAN HABERSE HECHO.

Una pregunta huérfana es:
- Algo que ningún cluster INT, P o R mencionó
- Algo que no está en el diagnóstico de tcf/
- Algo que no está en los datos del negocio
- Pero que ES relevante para el estado ACD actual

CÓMO ENCONTRARLAS:
1. Mira qué INTs están AUSENTES en el repertorio. ¿Qué preguntaría cada una?
   Si INT-04 (Ecológica) está ausente, nadie preguntó "¿qué pasa en el ecosistema?"
   → Pregunta huérfana: "¿Cuántos estudios de pilates han abierto/cerrado en La Rioja en los últimos 2 años?"

2. Mira qué funciones tienen gaps. ¿Hay preguntas OBVIAS que nadie hizo?
   Si F3=0.25 y nadie preguntó "¿cuánto cuesta realmente mantener cada grupo abierto?" → huérfana.

3. Mira lo que NO está en los datos. ¿Qué FALTA?
   Si hay datos de asistencia pero NO de satisfacción → huérfana: "¿Los clientes que vienen están contentos o vienen por inercia?"

4. Mira las contradicciones sin resolver. ¿Qué pregunta las resolvería?

REGLAS:
- Máximo 5 preguntas huérfanas (calidad sobre cantidad)
- Cada pregunta debe ser ACCIONABLE (alguien puede ir y buscar la respuesta)
- Cada pregunta debe estar vinculada a una función/lente/INT
- Priorizar por impacto: una buena pregunta puede cambiar todo el diagnóstico

Responde en JSON:
{
    "preguntas_huerfanas": [
        {
            "pregunta": "la pregunta concreta",
            "int_que_la_haria": "INT-XX que detectaría esto",
            "por_que_nadie_la_hizo": "qué sesgo o ausencia explica que no se hiciera",
            "funcion_impactada": "FX",
            "lente_impactada": "S|Se|C",
            "impacto_potencial": "qué cambiaría si tuviéramos la respuesta",
            "como_responderla": "acción concreta para obtener la respuesta",
            "prioridad": 1-5
        }
    ]
}"""


async def detectar_preguntas_huerfanas(resultados_g4: dict) -> dict:
    """Detecta preguntas que nadie hizo pero debería.

    Se ejecuta al final de cada G4. Las preguntas encontradas se:
    1. Persisten en DB como semillas
    2. Alimentan al buscador en el próximo ciclo
    3. Se proponen como adiciones al catálogo L1 si se repiten
    """
    if not OPENROUTER_API_KEY:
        return {"preguntas_huerfanas": []}

    g4_str = json.dumps(resultados_g4, ensure_ascii=False, indent=2, default=str)[:6000]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": REASONING_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_HUERFANAS},
                        {"role": "user", "content": f"OUTPUT COMPLETO DE G4:\n{g4_str}"},
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.4,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        resultado = json.loads(clean.strip())

    except Exception as e:
        log.error("huerfanas_error", error=str(e))
        return {"preguntas_huerfanas": [], "error": str(e)[:200]}

    # Persistir como semillas
    pool = await get_pool()
    for ph in resultado.get("preguntas_huerfanas", []):
        try:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_semillas_dormidas
                        (tenant_id, tipo, contenido, funcion, lente, int_origen,
                         prioridad, estado, metadata)
                    VALUES ($1, 'pregunta_huerfana', $2, $3, $4, $5, $6, 'dormida', $7::jsonb)
                """, TENANT, ph["pregunta"], ph.get("funcion_impactada", ""),
                    ph.get("lente_impactada", ""), ph.get("int_que_la_haria", ""),
                    ph.get("prioridad", 3),
                    json.dumps({"impacto": ph.get("impacto_potencial", ""),
                                "como_responder": ph.get("como_responderla", "")}))
        except Exception as e:
            log.warning("huerfana_persist_error", error=str(e))

    # Feed
    n = len(resultado.get("preguntas_huerfanas", []))
    if n > 0:
        try:
            from src.pilates.feed import publicar
            primera = resultado["preguntas_huerfanas"][0]["pregunta"][:100]
            await publicar("organismo_huerfanas", "❓",
                           f"{n} preguntas huérfanas detectadas",
                           f"Más importante: {primera}",
                           severidad="info")
        except Exception:
            pass

    log.info("huerfanas_ok", detectadas=n)
    return resultado


# ============================================================
# 2. CRISTALIZADOR — Patrones entre ejecuciones → reglas
# ============================================================

SYSTEM_CRISTALIZADOR = """Eres el Cristalizador del organismo OMNI-MIND.

Tu trabajo: revisar las ÚLTIMAS N ejecuciones de G4 y encontrar PATRONES RECURRENTES
que deberían convertirse en REGLAS del sistema.

Un patrón cristalizable es:
- Algo que apareció en 3+ ejecuciones consecutivas
- Una contradicción que se repite (ej: AF3 siempre propone cerrar lo que AF1 quiere retener)
- Una prescripción que nunca se ejecuta
- Un sesgo que el guardián detecta repetidamente
- Una pregunta huérfana que se repite

Un patrón cristalizado se convierte en:
- Una nueva regla para el Compositor ("siempre consultar AF1 antes de ejecutar AF3")
- Una nueva detección para un AF ("AF3 debe verificar convergencia con AF1 antes de emitir VETO")
- Una nueva pregunta permanente para un cluster INT
- Una nueva restricción para el Orquestador

REGLAS:
- Solo cristaliza patrones con 3+ apariciones (no coincidencias puntuales)
- Cada patrón debe tener: evidencia (en qué ejecuciones apareció), regla propuesta, impacto
- Máximo 3 cristalizaciones por mes (calidad sobre cantidad)

Responde en JSON:
{
    "patrones_detectados": [
        {
            "patron": "descripción del patrón recurrente",
            "apariciones": 3,
            "ejecuciones": ["fecha1", "fecha2", "fecha3"],
            "tipo_cristalizacion": "regla_compositor|deteccion_af|pregunta_cluster|restriccion_orquestador",
            "regla_propuesta": "la regla concreta que cristaliza este patrón",
            "impacto": "qué cambia si se implementa",
            "requiere_cr1": true/false
        }
    ]
}"""


async def cristalizar_patrones() -> dict:
    """Revisa últimas ejecuciones de G4 y cristaliza patrones en reglas.

    Se ejecuta mensualmente (después del autófago).
    """
    if not OPENROUTER_API_KEY:
        return {"patrones_detectados": []}

    pool = await get_pool()
    async with pool.acquire() as conn:
        # Últimas 8 ejecuciones de G4
        ejecuciones = await conn.fetch("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, created_at
            FROM om_enjambre_diagnosticos
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT 8
        """, TENANT)

        # Últimas semillas dormidas
        semillas = await conn.fetch("""
            SELECT tipo, contenido, funcion, lente, prioridad, created_at
            FROM om_semillas_dormidas
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT 20
        """, TENANT)

    if len(ejecuciones) < 3:
        return {"patrones_detectados": [], "razon": "Menos de 3 ejecuciones, insuficiente para cristalizar"}

    datos = {
        "ejecuciones": [dict(e) for e in ejecuciones],
        "semillas_recurrentes": [dict(s) for s in semillas],
    }
    datos_str = json.dumps(datos, ensure_ascii=False, indent=2, default=str)[:5000]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": REASONING_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_CRISTALIZADOR},
                        {"role": "user", "content": f"ÚLTIMAS EJECUCIONES DE G4:\n{datos_str}"},
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.2,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        resultado = json.loads(clean.strip())
    except Exception as e:
        log.error("cristalizador_error", error=str(e))
        return {"patrones_detectados": [], "error": str(e)[:200]}

    # Persistir cristalizaciones pendientes
    for patron in resultado.get("patrones_detectados", []):
        if patron.get("requiere_cr1"):
            try:
                from src.pilates.bus import emitir
                await emitir("BRIEFING_PENDIENTE", "CRISTALIZADOR", {
                    "tipo": "cristalizacion",
                    "patron": patron["patron"],
                    "regla_propuesta": patron["regla_propuesta"],
                    "requiere_cr1": True,
                }, prioridad=3)
            except Exception:
                pass

    # Feed
    n = len(resultado.get("patrones_detectados", []))
    if n > 0:
        try:
            from src.pilates.feed import publicar
            await publicar("organismo_cristalizador", "💎",
                           f"{n} patrones cristalizados",
                           resultado["patrones_detectados"][0]["regla_propuesta"][:150],
                           severidad="info")
        except Exception:
            pass

    log.info("cristalizador_ok", patrones=n)
    return resultado


# ============================================================
# 3. SEMILLAS DORMIDAS — Ideas que esperan
# ============================================================

async def evaluar_semillas() -> dict:
    """Evalúa si alguna semilla dormida ahora es relevante dado el estado ACD actual.

    Se ejecuta cada G4. Si una semilla dormida es relevante para el estado actual,
    se "despierta" y se inyecta en el buscador como query prioritaria.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Estado ACD actual
        diag = await conn.fetchrow("""
            SELECT vector_pre, lentes_pre, estado_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)
        if not diag:
            return {"despertadas": 0}

        estado = diag["estado_pre"]
        lentes = diag["lentes_pre"]
        if isinstance(lentes, str):
            lentes = json.loads(lentes)

        # Semillas dormidas
        semillas = await conn.fetch("""
            SELECT id, tipo, contenido, funcion, lente, int_origen, prioridad, metadata
            FROM om_semillas_dormidas
            WHERE tenant_id = $1 AND estado = 'dormida'
            ORDER BY prioridad, created_at
        """, TENANT)

    if not semillas:
        return {"despertadas": 0, "total_dormidas": 0}

    despertadas = []
    lente_baja = min(lentes, key=lentes.get) if lentes else None

    for s in semillas:
        # Una semilla despierta si:
        # 1. Su lente es la lente más baja actual
        # 2. O su función tiene gap < 0.30
        despertar = False
        razon = ""

        if s["lente"] and lente_baja and s["lente"].lower() in lente_baja.lower():
            despertar = True
            razon = f"Lente {s['lente']} es ahora la más baja ({lentes.get(lente_baja, 0):.2f})"

        vector = diag["vector_pre"]
        if isinstance(vector, str):
            vector = json.loads(vector)
        if s["funcion"] and vector.get(s["funcion"], 1.0) < 0.30:
            despertar = True
            razon = f"Función {s['funcion']} en gap crítico ({vector.get(s['funcion'], 0):.2f})"

        if despertar:
            despertadas.append({
                "id": str(s["id"]),
                "contenido": s["contenido"],
                "razon": razon,
            })
            # Marcar como despertada
            async with pool.acquire() as conn:
                await conn.execute("""
                    UPDATE om_semillas_dormidas SET estado='despertada',
                        metadata = metadata || '{"despertada_por": "evaluacion_auto"}'::jsonb
                    WHERE id = $1
                """, s["id"])

    # Las semillas despertadas se emiten como OPORTUNIDAD al bus
    if despertadas:
        try:
            from src.pilates.bus import emitir
            for sd in despertadas[:3]:
                await emitir("OPORTUNIDAD", "SEMILLAS_DORMIDAS", {
                    "tipo": "semilla_despertada",
                    "contenido": sd["contenido"],
                    "razon": sd["razon"],
                }, prioridad=4)
        except Exception:
            pass

    log.info("semillas_evaluadas", total=len(semillas), despertadas=len(despertadas))
    return {"total_dormidas": len(semillas), "despertadas": len(despertadas), "detalle": despertadas[:5]}


# ============================================================
# 4. PUENTE SÉQUITO ↔ ENJAMBRE
# ============================================================

async def consultar_sequito_para_enjambre(diagnostico_g4: dict, ints_en_duda: list[str]) -> dict:
    """Cuando el enjambre tiene INTs "en duda", consulta al séquito.

    Los 24 asesores (sequito.py) existen pero trabajan solo bajo demanda del cockpit.
    Este puente los conecta al enjambre: si el Compositor detecta que una INT está
    "en duda" (código dice activa, cluster dice ausente), consulta al asesor específico.

    Args:
        diagnostico_g4: Output del diagnóstico G4
        ints_en_duda: Lista de INT-XX que están en duda

    Returns:
        Evaluaciones del séquito para cada INT en duda.
    """
    if not ints_en_duda or not OPENROUTER_API_KEY:
        return {"consultados": 0}

    from src.pilates.sequito import ASESORES

    resultados = {}
    for int_id in ints_en_duda[:3]:  # Máximo 3 consultas para no saturar
        asesor = ASESORES.get(int_id)
        if not asesor:
            continue

        # Construir consulta específica
        prompt = f"""El enjambre cognitivo tiene DUDA sobre si {int_id} ({asesor['nombre']}) está activa en este negocio.

El diagnóstico de código dice: {diagnostico_g4.get('diagnostico_codigo', {}).get('repertorio_ints_activas', [])}
Los clusters dicen cosas contradictorias.

Tu ángulo: {asesor['angulo']}

PREGUNTA: Desde tu perspectiva como {asesor['nombre']}, ¿{int_id} está realmente activa, atrofiada o ausente en Authentic Pilates?
Responde con evidencia concreta."""

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                             "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                    json={
                        "model": BRAIN_MODEL,
                        "messages": [
                            {"role": "system", "content": f"Eres {asesor['nombre']} ({int_id}). {asesor['angulo']}"},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                resp.raise_for_status()
                resultados[int_id] = resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.warning("sequito_bridge_error", int_id=int_id, error=str(e))

    log.info("sequito_bridge_ok", consultados=len(resultados))
    return {"consultados": len(resultados), "evaluaciones": resultados}
```

## MIGRACIÓN SQL

```sql
-- 023_semillas_dormidas.sql

CREATE TABLE IF NOT EXISTS om_semillas_dormidas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    tipo TEXT NOT NULL,          -- pregunta_huerfana, insight, idea, patron
    contenido TEXT NOT NULL,
    funcion TEXT,                -- FX
    lente TEXT,                  -- S|Se|C
    int_origen TEXT,             -- INT-XX que la generaría
    prioridad INT DEFAULT 3,
    estado TEXT DEFAULT 'dormida',  -- dormida, despertada, ejecutada, descartada
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_semillas_tenant ON om_semillas_dormidas(tenant_id, estado);
CREATE INDEX IF NOT EXISTS idx_semillas_funcion ON om_semillas_dormidas(tenant_id, funcion, lente);
```

## INTEGRACIÓN EN PIPELINE

### En compositor.py (ejecutar_g4), al final:

```python
    # 6. CAPA GENERATIVA — post-G4
    from src.pilates.generativa import detectar_preguntas_huerfanas, evaluar_semillas

    # Preguntas huérfanas
    huerfanas = await detectar_preguntas_huerfanas(result)

    # Semillas dormidas que ahora son relevantes
    semillas = await evaluar_semillas()

    result["generativa"] = {
        "huerfanas": len(huerfanas.get("preguntas_huerfanas", [])),
        "semillas_despertadas": semillas.get("despertadas", 0),
    }
```

### En cron.py (_tarea_mensual), después del autófago:

```python
    # Cristalizador mensual
    try:
        from src.pilates.generativa import cristalizar_patrones
        crist = await cristalizar_patrones()
        log.info("cron_mensual_cristalizador_ok",
                 patrones=len(crist.get("patrones_detectados", [])))
    except Exception as e:
        log.error("cron_mensual_cristalizador_error", error=str(e))
```

### En compositor.py, cuando el Compositor detecta INTs en duda:

```python
    # Si el diagnóstico anotado tiene INTs en duda, consultar séquito
    ints_en_duda = diagnostico_anotado.get("diagnostico_anotado", {}).get(
        "repertorio_ajustado", {}).get("ints_en_duda", [])
    if ints_en_duda:
        from src.pilates.generativa import consultar_sequito_para_enjambre
        sequito_eval = await consultar_sequito_para_enjambre(result, ints_en_duda)
        # Inyectar en input del estratega
        estratega_input += f"\n\nEVALUACIÓN SÉQUITO (INTs en duda):\n{json.dumps(sequito_eval, ensure_ascii=False)[:1000]}"
```

## COSTE

| Componente | Frecuencia | Coste |
|---|---|---|
| Preguntas huérfanas | Semanal | ~$0.05 |
| Semillas dormidas | Semanal (código puro) | $0 |
| Cristalizador | Mensual | ~$0.05 |
| Puente Séquito | Bajo demanda (0-3 calls) | ~$0-0.06 |
| **Total** | | **~$0.25-0.35/mes** |

## TESTS

### T1: Detector encuentra al menos 1 pregunta huérfana
```python
result = await detectar_preguntas_huerfanas(g4_output)
assert len(result.get("preguntas_huerfanas", [])) >= 1
for ph in result["preguntas_huerfanas"]:
    assert "int_que_la_haria" in ph
    assert "como_responderla" in ph
```

### T2: Semillas se persisten y se evalúan
```python
# Después de huérfanas
semillas = await evaluar_semillas()
assert semillas["total_dormidas"] >= 0
```

### T3: Cristalizador no cristaliza con <3 ejecuciones
```python
result = await cristalizar_patrones()
# Si hay <3 ejecuciones, debe decir "insuficiente"
```

### T4: Puente Séquito consulta asesores correctos
```python
result = await consultar_sequito_para_enjambre(g4_output, ["INT-17", "INT-03"])
assert result["consultados"] <= 3
```

### T5: Tabla om_semillas_dormidas existe
```sql
SELECT count(*) FROM om_semillas_dormidas WHERE tenant_id='authentic_pilates';
```
