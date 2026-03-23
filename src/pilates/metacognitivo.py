"""Meta-Cognitivo — Opus que piensa sobre CÓMO PIENSA el sistema.

No piensa sobre el negocio. Piensa sobre el organismo.
¿Las prescripciones funcionaron? ¿Los clusters son efectivos?
¿El Guardián detecta sesgos reales? ¿El evaluador funcional es preciso?

Se ejecuta mensualmente. Lee 4 semanas de historia.
Produce: ajustes a la capa cognitiva + instrucciones para el Ingeniero.

Modelo: anthropic/claude-opus-4.6
Coste: ~$0.50/ejecución (~$0.50/mes)
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
import time

from src.db.client import get_pool
from src.pilates.director_opus import _parse_json_robusto

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPUS_MODEL = os.getenv("OPUS_MODEL", "anthropic/claude-opus-4.6")


SYSTEM_METACOG = """Eres el META-COGNITIVO del organismo OMNI-MIND.
Eres uno de los 3 agentes Opus. Tu dominio: el sistema cognitivo MISMO.

El Director diseña la inteligencia de los agentes ejecutivos.
Tú evalúas si ESA inteligencia FUNCIONA y ajustas el sistema cognitivo.

ERES EL MÉDICO DEL MÉDICO. Si el Director es el médico del negocio,
tú eres el que verifica si el médico está recetando bien.

TU TRABAJO:

1. EVALUAR PRESCRIPCIONES (¿funcionaron las partituras del Director?)
   - Compara prescripción semana N con diagnóstico semana N+1
   - ¿Se movieron las lentes en la dirección prescrita?
   - ¿Las INTs prescritas se activaron? (evidencia en pizarra)
   - Si no funcionó: ¿fue la prescripción incorrecta, la ejecución fallida, o el contexto cambió?

2. AJUSTAR CLUSTERS (¿los 13 clusters son efectivos?)
   - ¿Algún cluster produce confirmaciones vacías? ("CONFIRMO" sin evidencia)
   - ¿Algún cluster contradice consistentemente al código? (puede ser que el código esté mal)
   - ¿Los clusters P y R detectan disfunciones que el código no ve?
   - Si un cluster es inefectivo: proponer cambio de su system prompt

3. AUDITAR AL GUARDIÁN (¿el abogado del diablo sigue siendo incómodo?)
   - Si lleva 3+ semanas sin encontrar sesgos graves → SOSPECHOSO
   - Si siempre encuentra los MISMOS sesgos → se volvió rutinario
   - Si sus recomendaciones nunca cambian el diagnóstico → no aporta

4. EVOLUCIONAR TEXTO_CASO (las NOTAS del evaluador funcional)
   - Las NOTAS que el diagnosticador pasa al evaluador funcional son CRÍTICAS
   - Si en 4 semanas descubrimos que "15 grupos infrautilizados" era en realidad
     "8 grupos viables + 7 sin sentido", actualizar las NOTAS
   - Las NOTAS deben reflejar lo que el organismo APRENDIÓ, no lo que asumió

5. PROPONER CAMBIOS AL MANUAL DEL DIRECTOR (CR1)
   - Si los datos muestran que una regla del compilador no funciona → proponer cambio
   - Si un perfil patológico se comporta diferente a lo esperado → proponer ajuste
   - Si un nuevo patrón emergió (via Cristalizador) → proponer nueva sección

6. INSTRUCCIONES PARA EL INGENIERO (qué cambios de código)
   - Cambios de system prompts en archivos .py (clusters, guardián, buscador)
   - Nuevas NOTAS para el texto_caso del evaluador funcional
   - Actualizaciones al Manual del Director
   - Bug fixes detectados por análisis de logs
   - CADA instrucción debe ser: qué archivo, qué cambiar, por qué, y test de verificación

Responde en JSON:
{
    "evaluacion_prescripciones": {
        "semanas_evaluadas": 4,
        "prescripciones_que_funcionaron": [...],
        "prescripciones_sin_efecto": [...],
        "prescripciones_contraproducentes": [...],
        "conclusion": "resumen en 2 frases"
    },
    "ajustes_clusters": [
        {"cluster": "id", "problema": "qué no funciona", "ajuste": "qué cambiar en su prompt"}
    ],
    "auditoria_guardian": {
        "efectivo": true,
        "razon": "por qué",
        "ajuste": "qué cambiar si no es efectivo"
    },
    "evolucion_texto_caso": {
        "notas_a_cambiar": ["NOTA vieja → NOTA nueva"],
        "notas_a_añadir": ["nueva NOTA basada en lo aprendido"],
        "notas_a_eliminar": ["NOTA que ya no aplica"]
    },
    "propuestas_manual_director": [
        {"seccion": "§X", "cambio": "qué cambiar", "evidencia": "por qué", "requiere_cr1": true}
    ],
    "instrucciones_ingeniero": [
        {
            "tipo": "modificar_prompt|actualizar_manual|fix_bug|nuevo_detector",
            "archivo": "src/pilates/xxx.py",
            "cambio": "descripción precisa del cambio",
            "razon": "por qué es necesario",
            "test": "cómo verificar que el cambio funciona",
            "seguridad": "safe|requiere_cr1",
            "prioridad": 1
        }
    ]
}"""


async def ejecutar_metacognitivo() -> dict:
    """Meta-Cognitivo: piensa sobre cómo piensa el sistema."""
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Últimos 4 diagnósticos
        diagnosticos = await conn.fetch("""
            SELECT estado_pre, lentes_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 4
        """)

        # Últimas 4 semanas de pizarra
        pizarras = await conn.fetch("""
            SELECT agente, estado, detectando, interpretacion, accion_propuesta,
                   conflicto_con, ciclo, updated_at
            FROM om_pizarra WHERE tenant_id=$1
            ORDER BY updated_at DESC LIMIT 40
        """, TENANT)

        # Últimas 4 configs del Director
        configs_director = await conn.fetch("""
            SELECT agente, config, version, created_at
            FROM om_config_agentes
            WHERE tenant_id=$1 AND aprobada_por='opus'
            ORDER BY created_at DESC LIMIT 20
        """, TENANT)

        # Cristalizaciones recientes
        cristalizaciones = await conn.fetch("""
            SELECT payload FROM om_senales_agentes
            WHERE tenant_id=$1 AND origen='CRISTALIZADOR'
            ORDER BY created_at DESC LIMIT 3
        """, TENANT)

        # Guardián últimas 4 semanas
        guardians = await conn.fetch("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id=$1 AND origen='GUARDIAN_SESGOS'
            ORDER BY created_at DESC LIMIT 4
        """, TENANT)

    def _safe_rows(rows):
        result = []
        for r in rows:
            d = dict(r)
            for k, v in d.items():
                if hasattr(v, 'isoformat'):
                    d[k] = v.isoformat()
            result.append(d)
        return result

    # Construir input
    user_prompt = f"""ÚLTIMOS 4 DIAGNÓSTICOS (evolución del estado ACD):
{json.dumps(_safe_rows(diagnosticos), ensure_ascii=False, indent=2, default=str)[:3000]}

PIZARRAS (últimas 4 semanas, qué hicieron los agentes):
{json.dumps(_safe_rows(pizarras), ensure_ascii=False, indent=2, default=str)[:3000]}

CONFIGS DEL DIRECTOR (qué partituras escribió):
{json.dumps(_safe_rows(configs_director), ensure_ascii=False, indent=2, default=str)[:2000]}

CRISTALIZACIONES RECIENTES:
{json.dumps(_safe_rows(cristalizaciones), ensure_ascii=False, indent=2, default=str)[:1000]}

GUARDIÁN ÚLTIMAS 4 SEMANAS:
{json.dumps(_safe_rows(guardians), ensure_ascii=False, indent=2, default=str)[:1500]}

Evalúa el sistema cognitivo. ¿Las prescripciones funcionaron? ¿Qué ajustar?"""

    try:
        async with httpx.AsyncClient(timeout=240) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": OPUS_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_METACOG},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 6000,
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        resultado = _parse_json_robusto(raw)

    except Exception as e:
        log.error("metacognitivo_error", error=str(e))
        return {"error": str(e)[:300]}

    # Emitir instrucciones para el Ingeniero al bus
    instrucciones = resultado.get("instrucciones_ingeniero", [])
    if instrucciones:
        from src.pilates.bus import emitir
        for inst in instrucciones:
            tipo_señal = "BRIEFING_PENDIENTE" if inst.get("seguridad") == "requiere_cr1" else "ACCION"
            await emitir(tipo_señal, "META_COGNITIVO", {
                "tipo": "instruccion_ingeniero",
                **inst,
            }, prioridad=inst.get("prioridad", 3))

    # Pizarra
    from src.pilates.pizarra import escribir
    n_instrucciones = len(instrucciones)
    n_safe = sum(1 for i in instrucciones if i.get("seguridad") == "safe")
    n_cr1 = n_instrucciones - n_safe
    await escribir(
        agente="META_COGNITIVO",
        capa="cognitiva",
        estado="completado",
        detectando=resultado.get("evaluacion_prescripciones", {}).get("conclusion", ""),
        interpretacion=f"Guardian {'efectivo' if resultado.get('auditoria_guardian', {}).get('efectivo') else 'inefectivo'}. "
                       f"{len(resultado.get('ajustes_clusters', []))} clusters a ajustar.",
        accion_propuesta=f"{n_instrucciones} instrucciones para Ingeniero ({n_safe} safe, {n_cr1} CR1)",
        confianza=0.85,
        prioridad=1,
    )

    # Feed
    try:
        from src.pilates.feed import publicar
        await publicar("organismo_metacog", "M",
                       f"Meta-Cognitivo: {n_instrucciones} cambios propuestos",
                       resultado.get("evaluacion_prescripciones", {}).get("conclusion", "")[:200],
                       severidad="info")
    except Exception:
        pass

    dt = round(time.time() - t0, 1)
    log.info("metacognitivo_ok", instrucciones=n_instrucciones, tiempo=dt)
    return {"status": "ok", "tiempo_s": dt, "resultado": resultado}
