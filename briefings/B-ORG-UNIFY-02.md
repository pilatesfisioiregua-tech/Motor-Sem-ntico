# B-ORG-UNIFY-02: Unificar Compositor con tcf/prescriptor — Contextualizar, no reinventar

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — elimina la segunda fuente de prescripción
**Dependencia:** B-ORG-UNIFY-01 ejecutado

---

## EL PROBLEMA

`compositor.py` tiene un Estratega LLM que reinventa la prescripción que `tcf/prescriptor.py` ya genera en código puro ($0). El resultado: dos prescripciones potencialmente contradictorias.

## LA SOLUCIÓN

El Compositor INTEGRA las evaluaciones de los clusters con el diagnóstico de código.
El Estratega CONTEXTUALIZA la prescripción de código para Authentic Pilates.
El Orquestador verifica coherencia entre código y clusters.

Nadie reinventa nada.

## CAMBIOS

### ARCHIVO: `src/pilates/compositor.py` — REESCRIBIR

```python
"""Compositor + Estratega + Orquestador v3 — Capa sobre tcf/.

COMPOSITOR (claude-sonnet-4.6):
  Recibe: diagnóstico tcf/ + evaluaciones de 6 clusters
  Integra: confirmaciones/contradicciones/enriquecimientos
  Produce: diagnóstico ANOTADO (código + realidad)

ESTRATEGA (claude-sonnet-4.6):
  Recibe: Prescripcion de tcf/prescriptor (código puro)
        + diagnóstico anotado del Compositor
  Produce: Prescripción CONTEXTUALIZADA para Authentic Pilates
           (NO reinventa — traduce INTs genéricas a acciones concretas)

ORQUESTADOR (gpt-4o):
  Evalúa: ¿las contradicciones de los clusters invalidan la prescripción?
  Decide: aplicar, ajustar o reconvocar
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
import time

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4.6")
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")


# ============================================================
# 1. COMPOSITOR — Integra código + clusters
# ============================================================

SYSTEM_COMPOSITOR = """Eres el Compositor del organismo cognitivo de OMNI-MIND.

Recibes DOS fuentes de información:
1. DIAGNÓSTICO DE CÓDIGO (tcf/): repertorio INT×P×R, advertencias IC2-IC6, prescripción formal. Es DETERMINISTA y verificado en código. Es la base de verdad.
2. EVALUACIONES DE 6 CLUSTERS: cada cluster confirmó, contradijo o enriqueció el diagnóstico de código con evidencia real del negocio.

Tu trabajo: INTEGRAR ambas fuentes en un diagnóstico ANOTADO.

REGLAS:
1. El código es la BASE. No lo descartes. Si un cluster contradice el código, señálalo como tensión a resolver — no elijas automáticamente al cluster.
2. Las confirmaciones REFUERZAN. Si 4/6 clusters confirman una ausencia, eso es señal fuerte.
3. Las contradicciones son VALIOSAS. Significan que la realidad tiene matices que el código no ve.
4. Los enriquecimientos son CONTEXTO. Añaden color humano a números.
5. NO repitas datos. SINTETIZA.

Responde en JSON:
{
    "diagnostico_anotado": {
        "perfil_codigo": "estado del diagnóstico de código",
        "consenso_clusters": "qué dicen los clusters en conjunto",
        "confirmaciones_fuertes": ["lo que código Y clusters coinciden"],
        "tensiones": ["donde código y clusters divergen + por qué"],
        "enriquecimientos_clave": ["contexto que solo los clusters ven"],
        "repertorio_ajustado": {
            "ints_confirmadas_activas": ["INT-XX"],
            "ints_confirmadas_ausentes": ["INT-XX"],
            "ints_en_duda": ["INT-XX (código dice X, cluster Y dice Z)"],
            "advertencias_ic_validadas": ["ICX confirmada por cluster"],
            "advertencias_ic_cuestionadas": ["ICX que los clusters no ven"]
        },
        "confianza": 0.0-1.0,
        "sintesis": "2-3 frases: qué sabemos con certeza y qué no"
    }
}"""


# ============================================================
# 2. ESTRATEGA — Contextualiza prescripción de código
# ============================================================

SYSTEM_ESTRATEGA = """Eres el Estratega del organismo cognitivo de OMNI-MIND.

Recibes:
1. PRESCRIPCIÓN DE CÓDIGO (tcf/prescriptor.py): INTs a activar, Ps, Rs, secuencia de funciones, nivel lógico, objetivo. Generada gratis, determinista, con verificaciones IC.
2. DIAGNÓSTICO ANOTADO del Compositor: la realidad del negocio valida/matiza/enriquece.

Tu trabajo: NO reinventar la prescripción. CONTEXTUALIZARLA para Authentic Pilates.

TRADUCIR significa:
- "Prescripción dice activar INT-12(Narrativa)" → "Jesús debe documentar POR QUÉ hace el ejercicio de la sirena exactamente así. Esta semana: grabar 3 vídeos de 2 min explicando 3 ejercicios clave."
- "Prescripción dice P05(Primeros principios)" → "Antes de decidir si fusionar grupos, preguntarse: ¿por qué creé estos 16 horarios? ¿Qué función cumplía cada uno cuando los creé?"
- "Prescripción dice frenar F2" → "NO captar clientes nuevos para horarios con <30% ocupación. Primero fusionar/cerrar."

REGLAS:
1. La prescripción de código es la BASE. No la cambies — tradúcela a acciones concretas.
2. Si el diagnóstico anotado tiene tensiones (código ≠ clusters), ajusta la prioridad pero no elimines pasos.
3. Cada acción debe ser ejecutable por Jesús en <5 min y esta misma semana.
4. Incluye ANTI-PRESCRIPCIONES: qué NO hacer y por qué.
5. Máximo 5 acciones priorizadas.

Responde en JSON:
{
    "prescripcion_contextualizada": {
        "base_codigo": "resumen de lo que tcf/ prescribió",
        "acciones": [
            {
                "orden": 1,
                "int_origen": "INT-XX",
                "p_origen": "PXX",
                "accion_concreta": "acción específica para Authentic Pilates",
                "por_que": "por qué esta INT+P produce este efecto",
                "plazo": "esta semana / 2 semanas",
                "verificacion": "cómo saber si funcionó"
            }
        ],
        "anti_prescripciones": [
            "NO hacer X porque Y (origen: prescripcion.frenar o advertencia IC)"
        ],
        "ajustes_por_contexto": "qué cambió respecto a la prescripción de código y por qué"
    }
}"""


# ============================================================
# 3. ORQUESTADOR — Evalúa coherencia
# ============================================================

SYSTEM_ORQUESTADOR = """Eres el Orquestador del enjambre cognitivo.

Evalúas si la prescripción contextualizada es COHERENTE con el diagnóstico.

Criterios para APLICAR:
- Las acciones atacan la lente objetivo de la prescripción de código
- No hay contradicciones graves entre código y clusters sin resolver
- Las acciones son ejecutables y específicas
- Las anti-prescripciones son coherentes con los VETOs y frenar de código

Criterios para AJUSTAR:
- Hay tensiones código-clusters que cambian la prioridad
- Alguna acción es genérica (no específica a Authentic Pilates)

Criterios para RECONVOCAR:
- Las contradicciones de clusters invalidan la prescripción de código
- El diagnóstico anotado tiene confianza <0.4

Responde en JSON:
{
    "decision": "aplicar|ajustar|reconvocar",
    "confianza": 0.0-1.0,
    "razon": "por qué",
    "ajustes_sugeridos": ["si decision=ajustar"]
}"""


# ============================================================
# 4. PIPELINE G4 v3 — Unificado
# ============================================================

async def _call_llm(model: str, system: str, user: str, nombre: str,
                     max_tokens: int = 2000) -> dict:
    """Llamada genérica a LLM."""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
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
        log.info(f"{nombre}_ok", tiempo=round(time.time()-t0, 1))
        return resultado
    except Exception as e:
        log.error(f"{nombre}_error", error=str(e))
        return {"error": str(e)[:200]}


async def ejecutar_g4() -> dict:
    """G4 v3 unificada: tcf/ como motor + enjambre como contextualizador.

    Pipeline:
    1. diagnosticador → DiagnosticoCompleto + Prescripcion (tcf/, código puro)
    2. enjambre → 6 clusters evalúan contra realidad (LLM)
    3. compositor → integra código + clusters (LLM)
    4. estratega → contextualiza prescripción para Authentic Pilates (LLM)
    5. orquestador → valida coherencia (LLM)
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()

    # 1. DIAGNÓSTICO tcf/ (código + 1 LLM barata para repertorio)
    from src.pilates.diagnosticador import diagnosticar_tenant
    diag_result = await diagnosticar_tenant()

    if not diag_result.get("repertorio"):
        return {"error": "Diagnosticador no produjo repertorio. ¿Falta OPENROUTER_API_KEY?"}

    # 2. ENJAMBRE (6 clusters en paralelo)
    from src.pilates.enjambre import ejecutar_enjambre
    enjambre = await ejecutar_enjambre()

    # 3. COMPOSITOR (integra código + clusters)
    compositor_input = f"""DIAGNÓSTICO DE CÓDIGO (tcf/):
Estado: {diag_result['estado']} ({diag_result['nombre']})
Lentes: S={diag_result['lentes']['salud']:.2f}, Se={diag_result['lentes']['sentido']:.2f}, C={diag_result['lentes']['continuidad']:.2f}
Repertorio: {json.dumps(diag_result.get('repertorio', {}), ensure_ascii=False)[:1500]}
Prescripción: {json.dumps(diag_result.get('prescripcion', {}), ensure_ascii=False)[:1500]}

EVALUACIONES DE 6 CLUSTERS:
{json.dumps(enjambre.get('resultados', {}), ensure_ascii=False, indent=2, default=str)[:4000]}"""

    diagnostico_anotado = await _call_llm(
        REASONING_MODEL, SYSTEM_COMPOSITOR, compositor_input, "compositor")

    # 4. ESTRATEGA (contextualiza prescripción de código)
    estratega_input = f"""PRESCRIPCIÓN DE CÓDIGO (tcf/prescriptor.py):
{json.dumps(diag_result.get('prescripcion', {}), ensure_ascii=False, indent=2)[:2000]}

DIAGNÓSTICO ANOTADO (Compositor):
{json.dumps(diagnostico_anotado, ensure_ascii=False, indent=2, default=str)[:3000]}

CONTEXTO: Authentic Pilates, ~90 clientes, instructor único (Jesús), Albelda de Iregua (~4.000 hab).
Estado ACD: {diag_result['estado']}. Lentes: S={diag_result['lentes']['salud']:.2f}, Se={diag_result['lentes']['sentido']:.2f}, C={diag_result['lentes']['continuidad']:.2f}."""

    prescripcion_ctx = await _call_llm(
        REASONING_MODEL, SYSTEM_ESTRATEGA, estratega_input, "estratega")

    # 5. ORQUESTADOR (valida coherencia)
    orq_input = f"""PRESCRIPCIÓN CONTEXTUALIZADA:
{json.dumps(prescripcion_ctx, ensure_ascii=False, indent=2, default=str)[:2000]}

DIAGNÓSTICO ANOTADO:
{json.dumps(diagnostico_anotado, ensure_ascii=False, indent=2, default=str)[:1500]}

CONFIRMACIONES clusters: {enjambre.get('confirmaciones', 0)}, CONTRADICCIONES: {enjambre.get('contradicciones', 0)}"""

    control = await _call_llm(
        BRAIN_MODEL, SYSTEM_ORQUESTADOR, orq_input, "orquestador", max_tokens=500)

    # 6. EMITIR PRESCRIPCIÓN AL BUS
    from src.pilates.bus import emitir
    await emitir(
        "PRESCRIPCION_ESTRATEGICA", "G4_COMPOSITOR",
        {
            "tipo": "nivel_1_unificado",
            "fuente_codigo": diag_result.get("prescripcion"),
            "fuente_clusters": {
                "confirmaciones": enjambre.get("confirmaciones", 0),
                "contradicciones": enjambre.get("contradicciones", 0),
            },
            "prescripcion_contextualizada": prescripcion_ctx.get("prescripcion_contextualizada", {}),
            "decision_orquestador": control.get("decision"),
            "confianza": control.get("confianza", 0),
        },
        prioridad=2,
    )

    # 7. PERSISTIR
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_enjambre_diagnosticos
                (tenant_id, estado_acd_base, resultado_lentes, resultado_funciones,
                 resultado_clusters, señales_emitidas, tiempo_total_s)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6, $7)
        """, TENANT, diag_result.get("estado", "g4_v3"),
            json.dumps(diagnostico_anotado, ensure_ascii=False, default=str),
            json.dumps(prescripcion_ctx, ensure_ascii=False, default=str),
            json.dumps(control, ensure_ascii=False, default=str),
            enjambre.get("señales_emitidas", 0),
            round(time.time() - t0, 0))

    dt = round(time.time() - t0, 1)

    log.info("g4_v3_completo", tiempo=dt,
             estado=diag_result.get("estado"),
             decision=control.get("decision"),
             confianza=control.get("confianza"))

    return {
        "status": "ok",
        "version": "v3_unificado",
        "diagnostico_codigo": {
            "estado": diag_result.get("estado"),
            "lentes": diag_result.get("lentes"),
            "repertorio_ints_activas": diag_result.get("repertorio", {}).get("ints_activas", []),
            "advertencias_ic": diag_result.get("repertorio", {}).get("advertencias_ic", []),
            "prescripcion_ints": diag_result.get("prescripcion", {}).get("ints", []),
            "prescripcion_objetivo": diag_result.get("prescripcion", {}).get("objetivo"),
        },
        "enjambre": {
            "confirmaciones": enjambre.get("confirmaciones", 0),
            "contradicciones": enjambre.get("contradicciones", 0),
            "enriquecimientos": enjambre.get("enriquecimientos", 0),
        },
        "diagnostico_anotado": diagnostico_anotado,
        "prescripcion_contextualizada": prescripcion_ctx,
        "orquestador": control,
        "tiempo_total_s": dt,
    }
```

## COSTE TOTAL G4 v3 UNIFICADO

| Componente | Modelo | Coste |
|---|---|---|
| diagnosticador: inferir_repertorio (P4) | LLM barata (deepseek) | ~$0.003 |
| diagnosticador: prescribir | código puro | $0 |
| enjambre: 6 clusters (paralelo) | claude-sonnet-4.6 | ~$0.30 |
| compositor | claude-sonnet-4.6 | ~$0.05 |
| estratega | claude-sonnet-4.6 | ~$0.05 |
| orquestador | gpt-4o | ~$0.02 |
| **TOTAL** | | **~$0.42** |

Antes: ~$0.57. Ahorro: 26%. Pero lo importante no es el coste — es que las IC2-IC6 son DETERMINISTAS en vez de depender de que el LLM las recuerde.

## CAMBIO EN CRON

Sin cambios en cron. `ejecutar_g4()` ya se llama desde el paso 10. La función internamente ahora usa la cadena unificada.

El `recompilador.py` tampoco cambia — sigue importando `ejecutar_g4` de `compositor.py`.

## TESTS

### T1: G4 produce output con fuente_codigo
```python
result = await ejecutar_g4()
assert result["version"] == "v3_unificado"
assert "diagnostico_codigo" in result
assert len(result["diagnostico_codigo"]["repertorio_ints_activas"]) >= 3
assert len(result["diagnostico_codigo"]["advertencias_ic"]) >= 0
```

### T2: Prescripción contextualizada tiene acciones concretas
```python
presc = result["prescripcion_contextualizada"]
acciones = presc.get("prescripcion_contextualizada", {}).get("acciones", [])
assert len(acciones) >= 2
for a in acciones:
    assert "int_origen" in a
    assert "accion_concreta" in a
    assert len(a["accion_concreta"]) > 30  # No vale "mejorar F3"
```

### T3: Orquestador aprueba con confianza razonable
```python
assert result["orquestador"].get("decision") in ("aplicar", "ajustar")
assert result["orquestador"].get("confianza", 0) >= 0.4
```

### T4: Las advertencias IC del código se propagan al bus
```sql
SELECT payload->'fuente_codigo'->'advertencias_ic'
FROM om_senales_agentes
WHERE tipo='PRESCRIPCION_ESTRATEGICA'
ORDER BY created_at DESC LIMIT 1;
-- Debe tener las advertencias de tcf/
```

---

## RESULTADO: UNA SOLA CADENA CAUSAL

```
ANTES (paralela):
  diagnosticador → P3 solo
  enjambre → reinventa P4 con LLM ($0.15)
  compositor → reinventa prescripción con LLM ($0.10)
  → Dos fuentes de verdad, posibles contradicciones

DESPUÉS (unificada):
  diagnosticador → P1+P2+P3+P4 via tcf/ ($0.003)
                 → prescribir() via tcf/ ($0)
  enjambre → 6 clusters EVALÚAN contra realidad ($0.30)
  compositor → INTEGRA código + clusters ($0.05)
  estratega → CONTEXTUALIZA para Authentic Pilates ($0.05)
  orquestador → VALIDA coherencia ($0.02)
  → Una fuente de verdad (tcf/), enriquecida por LLM
```

El álgebra es código. El contexto es LLM. Cada uno hace lo que hace mejor.
