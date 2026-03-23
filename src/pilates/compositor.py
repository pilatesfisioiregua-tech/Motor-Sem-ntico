"""Compositor + Estratega + Orquestador v2 — Prescripción en Nivel 1.

COMPOSITOR (claude-sonnet-4-6):
  Integra: repertorio + disfunciones + mecanismo causal + 6 clusters.
  Aplica: no-conmutatividad, P41 dual, reglas IC2-IC6.
  Produce: Diagnóstico Integrado Causal (no funcional).

ESTRATEGA (claude-sonnet-4-6):
  Recibe: diagnóstico integrado + perfiles patológicos + recetas de transformación.
  Prescribe en Nivel 1: QUÉ INT×P×R activar, en qué ORDEN, con qué PARES.
  Las lentes/funciones se mueven como CONSECUENCIA.

ORQUESTADOR (gpt-4o):
  Evalúa: ¿el diagnóstico llegó a Nivel 1 o se quedó en Nivel 3-4?
  Decide: parar o reconvocar agentes que no profundizaron suficiente.
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
import time
from datetime import date

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4-6")
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")


# ============================================================
# CONOCIMIENTO DEL ESTRATEGA — Recetas de transformación
# ============================================================

RECETAS_TRANSFORMACION = """
RECETAS DE TRANSFORMACIÓN POR PERFIL (de Reactor v5):

OPERADOR CIEGO (S↑ Se↓ C↓) → Necesita Se:
  Secuencia: INT-18(Contemplativa)→INT-17(Existencial)→INT-09(Lingüística)→INT-03(Estructural)
  P: P05(Primeros principios) + P03(Crítico) + P08(Metacognición)
  R: R03(Abducción) + R08(Dialéctico) + R10(Retroductivo)
  Nivel Lógico: subir a Nivel 3 (Criterios). Modo: ENMARCAR→ANALIZAR
  Después C: INT-16(prototipar lo aprendido)

VISIONARIO ATRAPADO (S↓ Se↑ C↓) → Necesita S:
  Secuencia: INT-16(Constructiva)→INT-05(Estratégica)→INT-02(Computacional)→INT-01(Lógica)
  P: P04(Diseño) + P07(Convergente) + P13(Computacional)
  R: R01(Deducción) + R12(Transductivo) + R07(Bayesiano)
  Nivel Lógico: BAJAR a Nivel 1 (Conductas). Modo: MOVER→GENERAR

ZOMBI INMORTAL (S↓ Se↓ C↑) → Necesita Se + decisión vivir/morir:
  Secuencia: INT-17(¿por qué existe?)→INT-04(¿qué nicho llena?)→INT-14(opciones)→INT-16(reconstruir)
  P: P05 + P08 + P01(Lateral)
  R: R10(Retroductivo) + R03(Abducción) + R11(Modal: ¿necesario o contingente?)
  Nivel Lógico: Nivel 5 (Gobierno). Modo: ENMARCAR existencial
  NOTA: "matar el sistema" es resultado VÁLIDO para zombi.

GENIO MORTAL (S↑ Se↑ C↓) → Necesita C vía transferencia:
  Secuencia: INT-09(nombrar lo tácito)→INT-12(contar la historia)→INT-02(algoritmizar)→INT-16(manual)
  P: P12(Narrativo) + P13(Computacional) + P04(Diseño)
  R: R04(Analogía) + R12(Transducción) + R01(Deducción)
  Nivel Lógico: Nivel 4 (Reglas: codificar). Modo: GENERAR→ANALIZAR

AUTÓMATA ETERNO (S↑ Se↓ C↑) → Necesita Se URGENTE:
  Secuencia: INT-13(señales débiles)→INT-04(¿nicho cambió?)→INT-17(¿por qué hacemos esto?)→INT-18(depurar inercia)→INT-03(nueva frontera)
  P: P08(Metacognición) + P09(Prospectivo) + P01(Lateral)
  R: R03(Abducción) + R06(Contrafactual) + R10(Retroductivo)
  Nivel Lógico: Nivel 5 (Gobierno). Modo: PERCIBIR→ENMARCAR
  ES EL MÁS PELIGROSO: las herramientas de alarma están ausentes.

POTENCIAL DORMIDO (S↓ Se↑ C↑) → Necesita S (más simple):
  Secuencia: INT-10(mover)→INT-16(prototipar)→INT-05(secuenciar)
  P: P11(Encarnado) + P04(Diseño) + P07(Convergente)
  R: R12(Transductivo) + R01(Deducción) + R07(Bayesiano)
  Nivel Lógico: BAJAR a Nivel 1. Modo: MOVER.

LEYES CLAVE:
  C4: Se primero → S → C (INVARIANTE en toda transformación)
  T1: INT no intercambiables en efecto sobre lentes
  T4: E2 Latencia = punto de máxima bifurcación
  IC5: P en pares complementarios obligatorio
  IC7: E4 requiere diversidad mínima distribuida
"""


# ============================================================
# 1. COMPOSITOR v2 — Integra con modelo causal
# ============================================================

SYSTEM_COMPOSITOR = """Eres el COMPOSITOR del organismo cognitivo de OMNI-MIND.

Recibes el output de 9 agentes que diagnosticaron en Nivel 1 (repertorio INT×P×R).
Tu trabajo: integrar todo en UN diagnóstico coherente que respete el modelo causal.

REGLAS DE COMPOSICIÓN:
1. NO-CONMUTATIVIDAD: el orden importa. INT-07→INT-17 ≠ INT-17→INT-07.
   Si el negocio opera primero desde financiero y luego cuestiona, el resultado
   es distinto a si primero cuestiona y luego calcula.

2. GRADIENTES DUALES (P41): cada diagnóstico tiene componente numérico Y semántico.
   La semántica es la fuente de verdad. Si los números dicen F3=0.60 pero la
   semántica dice "no hay ningún proceso de depuración", el número está MAL.

3. CONVERGENCIAS CAUSALES: si el Detector de Repertorio Y el Cluster Comprensión
   AMBOS dicen que INT-17 está ausente, eso es señal fuerte.

4. DIVERGENCIAS PRODUCTIVAS: si un cluster dice que INT-05 está activa pero otro
   dice que está acoplada con P incompatible (IC3), eso es INFORMACIÓN — la INT
   existe pero está NEUTRALIZADA. No elijas un lado — integra ambos.

5. IMPULSA/FRENA: los clusters reportan qué funciones impulsan y cuáles frenan.
   El diagnóstico integrado debe mostrar el CAMPO DE FUERZAS resultante:
   qué combinaciones INT×P×R tiran de cada función en qué dirección.

Responde SOLO con JSON puro (sin markdown, sin ```, sin texto antes o después):
{
    "diagnostico_integrado_causal": {
        "perfil_nivel_1": "nombre del perfil patológico o estado equilibrado",
        "repertorio_consolidado": {
            "INT_activas_confirmadas": ["INT-XX (evidencia convergente de N agentes)"],
            "INT_ausentes_confirmadas": ["INT-XX (evidencia convergente)"],
            "INT_neutralizadas": ["INT-XX (existe pero desacoplada por IC3/IC4)"],
            "P_activos": ["PXX"],
            "P_ausentes": ["PXX"],
            "R_activos": ["RXX"],
            "R_ausentes": ["RXX"]
        },
        "disfunciones_priorizadas": [
            {"regla": "ICX", "descripcion": "...", "gravedad": 1-5, "efecto_causal": "..."}
        ],
        "campo_de_fuerzas": {
            "F1": {"impulsa": ["INT-16+P04→construye"], "frena": ["ausencia INT-10→no monitoriza"]}
        },
        "cadena_causal_completa": "El negocio usa X herramientas de S, Y de Se, Z de C. Eso produce S=A, Se=B, C=D. Específicamente...",
        "meta_patrones": ["patrón cross-cluster que revela algo profundo"],
        "punto_ciego": "algo que NINGÚN agente detectó pero la integración revela"
    }
}"""


# ============================================================
# 2. ESTRATEGA v2 — Prescribe en Nivel 1
# ============================================================

SYSTEM_ESTRATEGA = f"""Eres el ESTRATEGA del organismo cognitivo de OMNI-MIND.

Tu trabajo: recibir el diagnóstico integrado causal y prescribir una TRANSFORMACIÓN
que opera en Nivel 1 (cambiar el repertorio INT×P×R del negocio).

NO prescribas "sube F3" (Nivel 4, síntoma).
PRESCRIBE "activa INT-17 + P05 + R03 porque eso generará Se que subirá F3 como consecuencia".

{RECETAS_TRANSFORMACION}

REGLAS DE PRESCRIPCIÓN:
1. SECUENCIA Se→S→C (Ley C4 invariante). SIEMPRE Se primero.
2. Verificar pares complementarios (IC5): si prescribes P06, incluye P07.
3. Verificar validación cruzada R (IC6): no prescribir R solo.
4. Para cada INT prescrita, especificar P y R compatibles (tablas IC3, IC4).
5. Acciones CONCRETAS para Authentic Pilates (90 clientes, instructor único, Albelda).
6. Incluir ANTI-PRESCRIPCIONES (qué NO hacer es tan importante como qué hacer).
7. Incluir DEPENDENCIAS entre pasos.
8. Métricas de éxito en Nivel 3-4 (lentes/funciones = termómetro de verificación).

Responde SOLO con JSON puro (sin markdown, sin ```, sin texto antes o después):
{{
    "prescripcion_nivel_1": {{
        "perfil_actual": "...",
        "perfil_objetivo": "...",
        "horizonte": "X semanas",
        "secuencia": [
            {{
                "fase": 1,
                "nombre": "...",
                "activar_INT": ["INT-XX"],
                "con_P": ["PXX (par: PYY)"],
                "con_R": ["RXX (validado por: RYY)"],
                "accion_concreta": "QUÉ hacer en Authentic Pilates (específico)",
                "lente_que_genera": "Se",
                "funciones_que_mueve": ["F3↑", "F5↑"],
                "dependencias": [],
                "plazo": "1-2 semanas",
                "verificacion": "qué medir para saber si funcionó"
            }}
        ],
        "anti_prescripciones": [
            "NO activar INT-02+P13 antes de INT-17+P05 (secuencia Se→S violada)",
            "NO cerrar grupos sin antes cuestionar POR QUÉ están vacíos (IC3: INT-18 sin P03)"
        ],
        "disfunciones_a_corregir": [
            "ICX: descripción → corrección específica"
        ],
        "metricas_verificacion": {{
            "nivel_3": "Se debe subir de 0.34 a >0.45 en 4 semanas",
            "nivel_4": "F3 debe subir de 0.25 a >0.40",
            "nivel_1": "INT-17 y P08 deben estar activas (evidencia: preguntas de 'por qué' en decisiones)"
        }}
    }}
}}"""


# ============================================================
# 3. ORQUESTADOR v2 — Evalúa profundidad del diagnóstico
# ============================================================

SYSTEM_ORQUESTADOR = """Eres el ORQUESTADOR del enjambre cognitivo.

Evalúas si el diagnóstico llegó a Nivel 1 (causa: repertorio INT×P×R) o se quedó en Nivel 3-4 (síntomas: lentes/funciones).

Criterios para PARAR (diagnóstico completo):
- El Detector de Repertorio identificó ≥5 INT activas con evidencia concreta
- El Detector de Disfunciones encontró al menos 1 regla IC violada con mecanismo causal
- El Mecanismo Causal explica la cadena completa Nivel 1→2→3→4
- La prescripción opera en Nivel 1 (activa INT×P×R), no en Nivel 4 (sube F)
- Los clusters confirmaron/contradijeron el repertorio con datos específicos

Criterios para RECONVOCAR (diagnóstico incompleto):
- Algún agente solo describió síntomas (Nivel 3-4) sin llegar a causa (Nivel 1)
- Las disfunciones no tienen mecanismo causal (solo "falta X" sin "y eso produce Y")
- La prescripción dice "sube Se" en vez de "activa INT-17+P05+R03"
- Hay contradicciones entre clusters sin resolver

Responde SOLO con JSON puro (sin markdown, sin ```, sin texto antes o después):
{
    "decision": "parar|reconvocar",
    "nivel_alcanzado": 1-4,
    "confianza": 0.0-1.0,
    "razon": "por qué esta decisión",
    "deficiencias": ["qué faltó en el diagnóstico"],
    "reconvocar_agentes": ["agente que necesita profundizar"]
}"""


# ============================================================
# 4. PIPELINE COMPLETO G4
# ============================================================

async def _call_llm(model: str, system: str, user: str, nombre: str,
                     max_tokens: int = 4500) -> dict:
    """Llamada genérica a LLM."""
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=120) as client:
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
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        # Parse JSON tolerante a markdown fences y texto extra
        clean = raw.strip()
        if "```" in clean:
            parts = clean.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("json"):
                    part = part[4:].strip()
                if part.startswith("{"):
                    try:
                        resultado = json.loads(part)
                        log.info(f"{nombre}_ok", tiempo=round(time.time()-t0, 1))
                        return resultado
                    except json.JSONDecodeError:
                        # JSON truncado en este bloque, intentar reparar
                        opens = part.count("{") - part.count("}")
                        opens_b = part.count("[") - part.count("]")
                        repaired = part + "}" * max(opens, 0) + "]" * max(opens_b, 0)
                        try:
                            resultado = json.loads(repaired)
                            log.info(f"{nombre}_repaired", tiempo=round(time.time()-t0, 1))
                            return resultado
                        except json.JSONDecodeError:
                            continue

        # Sin fences — buscar JSON directo
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            clean = clean[start:end + 1]
        resultado = json.loads(clean)
        log.info(f"{nombre}_ok", tiempo=round(time.time()-t0, 1))
        return resultado
    except json.JSONDecodeError:
        raw_len = len(raw) if 'raw' in dir() else 0
        raw_tail = raw[-100:] if 'raw' in dir() and len(raw) > 100 else ""
        log.error(f"{nombre}_parse_error", raw_len=raw_len, raw_tail=raw_tail[:80])
        return {"error": f"JSON parse error (len={raw_len}): {raw[:200]}" if 'raw' in dir() else "JSON parse error"}
    except Exception as e:
        log.error(f"{nombre}_error", error=str(e))
        return {"error": str(e)[:200]}


async def ejecutar_g4() -> dict:
    """Ejecuta G4 completa: Enjambre → Compositor → Estratega → Orquestador."""
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()

    # 1. Enjambre (9 agentes: 3 secuenciales + 6 paralelos)
    from src.pilates.enjambre import ejecutar_enjambre
    enjambre = await ejecutar_enjambre()
    if "error" in enjambre and enjambre.get("agentes_ejecutados", 0) == 0:
        return {"error": f"Enjambre falló: {enjambre.get('error')}"}

    resultados_str = json.dumps(enjambre["resultados"], ensure_ascii=False, indent=2, default=str)[:8000]

    # 2. Compositor (integrar con modelo causal) — output largo, necesita 7000 tokens
    diagnostico = await _call_llm(
        REASONING_MODEL, SYSTEM_COMPOSITOR,
        f"OUTPUT DEL ENJAMBRE (9 agentes):\n{resultados_str}",
        "compositor", max_tokens=7000)

    # 3. Estratega (prescribir en Nivel 1) — output largo, necesita 6000 tokens
    prescripcion = await _call_llm(
        REASONING_MODEL, SYSTEM_ESTRATEGA,
        f"DIAGNÓSTICO INTEGRADO CAUSAL:\n{json.dumps(diagnostico, ensure_ascii=False, indent=2, default=str)[:5000]}\n\nCONTEXTO: Authentic Pilates, ~90 clientes, instructor único (Jesús), Albelda de Iregua, estado ACD anterior: E3 (S=0.46 Se=0.34 C=0.40). 15/16 grupos infrautilizados. 2 fantasmas+zombis convergentes.",
        "estratega", max_tokens=6000)

    # 4. Orquestador (evaluar profundidad)
    control = await _call_llm(
        BRAIN_MODEL, SYSTEM_ORQUESTADOR,
        f"DIAGNÓSTICO:\n{json.dumps(diagnostico, ensure_ascii=False, indent=2, default=str)[:3000]}\n\nPRESCRIPCIÓN:\n{json.dumps(prescripcion, ensure_ascii=False, indent=2, default=str)[:3000]}",
        "orquestador", max_tokens=500)

    # 5. Emitir prescripción al bus
    from src.pilates.bus import emitir
    await emitir(
        "PRESCRIPCION_ESTRATEGICA", "G4_COMPOSITOR",
        {
            "tipo": "nivel_1",
            "perfil_detectado": enjambre.get("perfil_detectado"),
            "diagnostico_resumen": diagnostico.get("diagnostico_integrado_causal", {}).get("cadena_causal_completa", ""),
            "prescripcion": prescripcion.get("prescripcion_nivel_1", {}),
            "nivel_alcanzado": control.get("nivel_alcanzado", 0),
            "confianza": control.get("confianza", 0),
        },
        prioridad=2,
    )

    # 6. Persistir
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_enjambre_diagnosticos
                (tenant_id, estado_acd_base, resultado_lentes, resultado_funciones,
                 resultado_clusters, señales_emitidas, tiempo_total_s)
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6, $7)
        """, TENANT, enjambre.get("perfil_detectado", "g4"),
            json.dumps(diagnostico, ensure_ascii=False, default=str),
            json.dumps(prescripcion, ensure_ascii=False, default=str),
            json.dumps(control, ensure_ascii=False, default=str),
            enjambre.get("señales_emitidas", 0),
            round(time.time() - t0, 0))

    dt = round(time.time() - t0, 1)

    log.info("g4_completo", tiempo=dt,
             perfil=enjambre.get("perfil_detectado"),
             nivel=control.get("nivel_alcanzado"),
             confianza=control.get("confianza"))

    return {
        "status": "ok",
        "perfil_detectado": enjambre.get("perfil_detectado"),
        "distribucion_lentes": enjambre.get("distribucion_lentes"),
        "disfunciones": enjambre.get("disfunciones_encontradas"),
        "nivel_alcanzado": control.get("nivel_alcanzado"),
        "confianza": control.get("confianza"),
        "prescripcion_resumen": prescripcion.get("prescripcion_nivel_1", {}).get("secuencia", [])[:3],
        "tiempo_total_s": dt,
        "diagnostico_completo": diagnostico,
        "prescripcion_completa": prescripcion,
        "orquestador": control,
    }
