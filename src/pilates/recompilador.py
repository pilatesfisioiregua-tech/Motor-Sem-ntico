"""Recompilador — El sistema se modifica a sí mismo.

Recibe la prescripción del Estratega (Nivel 1: qué INT×P×R activar)
y la traduce en cambios concretos a la configuración de los agentes.

Dos niveles:
  A) Runtime: modifica config en DB → agentes lo cargan al ejecutar
  B) Estructural: genera briefing para Claude Code → requiere CR1

El Recompilador es el Gestor de la Matriz implementado:
  Loop Lento de Maestro v4 §1.4
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
from datetime import date, datetime
from uuid import UUID

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4.6")


# ============================================================
# CONOCIMIENTO: Cómo los prompts codifican INT×P×R
# ============================================================

PROMPT_ARCHITECTURE = """
ARQUITECTURA DE UN PROMPT DE AGENTE:

PARTE 1 — IMPERATIVA (L0, secuencia algebraica):
  Define CÓMO procesar: EXTRAER→CRUZAR→LENTES→INTEGRAR→ABSTRAER→FRONTERA
  El orden determina el PENSAMIENTO (P) del agente.
  P07(Convergente) = secuencia lineal hacia cierre rápido.
  P02(Sistémico) = loops de retroalimentación entre pasos.
  P05(Primeros principios) = paso extra de "descomponer premisas" antes de EXTRAER.

PARTE 2 — PREGUNTAS (L1/L2, contenido específico):
  Define QUÉ percibir: las preguntas SON las inteligencias activas.
  INT-17(Existencial) = "¿por qué existe esto?" "¿los valores declarados coinciden con las acciones?"
  INT-07(Financiera) = "¿cuál es el coste de oportunidad?" "¿qué payoff tiene cada opción?"
  Las preguntas determinan las INTELIGENCIAS (INT) del agente.

PARTE 3 — MECANISMO INFERENCIAL (implícito en las instrucciones):
  Define CÓMO inferir conclusiones.
  R03(Abducción) = "genera la mejor explicación para lo observado"
  R01(Deducción) = "si las premisas son X, entonces la conclusión es Y"
  R06(Contrafactual) = "qué pasaría si..."
  El razonamiento se codifica en las INSTRUCCIONES de cómo responder.

EJEMPLO — AF3 con config por defecto (operador):
  P activo: P07(Convergente) — "detecta y cierra rápido"
  INT activas: INT-01(Lógica), INT-07(Financiera) — "calcula, elimina lo no rentable"
  R activo: R01(Deducción) — "si ocupación < 30%, entonces cerrar"
  RESULTADO: depura solo por números. No cuestiona POR QUÉ está vacío.

EJEMPLO — AF3 con config prescrita (equilibrado):
  P activos: P05(Primeros principios) + P03(Crítico) — "cuestiona premisas antes de decidir"
  INT activas: INT-18(Contemplativa) + INT-09(Lingüística) + INT-03(Estructural) + INT-01(Lógica)
  R activos: R03(Abducción) + R08(Dialéctico) + R01(Deducción)
  RESULTADO: primero pregunta "¿la urgencia de cerrar es real?", luego nombra lo que
  no se está nombrando, luego mapea la estructura del problema, luego calcula.
  MISMO agente, MISMO código, DIFERENTE repertorio → DIFERENTE output.
"""

TEMPLATE_CONFIG = """
FORMATO DE CONFIG PARA UN AGENTE:
{
    "agente": "AF3",
    "INT_activas": [
        {"id": "INT-18", "nombre": "Contemplativa", "lente": "Se",
         "preguntas": [
             "¿La urgencia de cerrar este grupo es real o inventada?",
             "¿Qué pasaría si simplemente no hicieras nada durante 4 semanas?"
         ]},
        {"id": "INT-09", "nombre": "Lingüística", "lente": "Se",
         "preguntas": [
             "¿Hay algo que no se está nombrando sobre por qué estos grupos están vacíos?",
             "¿Cómo describe el dueño estos grupos? ¿'vacíos' o 'con potencial'?"
         ]},
        {"id": "INT-01", "nombre": "Lógica", "lente": "S",
         "preguntas": [
             "¿Hay contradicción entre mantener 15 grupos y decir que faltan clientes?",
             "¿Cuál es el coste real (no percibido) de mantener un grupo con 1 alumno?"
         ]}
    ],
    "P_activos": [
        {"id": "P05", "nombre": "Primeros principios",
         "instruccion_imperativa": "Antes de proponer CUALQUIER acción, descompón las premisas: ¿por qué existe este grupo? ¿qué función cumplía cuando se creó? ¿esa función sigue siendo válida?"},
        {"id": "P03", "nombre": "Crítico",
         "instruccion_imperativa": "Evalúa la calidad de la evidencia: ¿3 semanas de baja asistencia es suficiente para cerrar? ¿Hay estacionalidad que explique?"}
    ],
    "R_activos": [
        {"id": "R03", "nombre": "Abducción",
         "instruccion_inferencial": "Para cada grupo infrautilizado, genera la MEJOR EXPLICACIÓN de por qué está así. No asumas que la respuesta es obvia."},
        {"id": "R08", "nombre": "Dialéctico",
         "instruccion_inferencial": "Confronta la tesis 'cerrar' con la antítesis 'mantener'. ¿Hay una síntesis que no sea ni una ni otra?"}
    ],
    "instruccion_completa": "... (se construye dinámicamente combinando todo lo anterior)",
    "version": 2,
    "prescripcion_origen": "uuid del diagnóstico del enjambre"
}
"""


# ============================================================
# 1. RECOMPILADOR — Traduce prescripción a configs de agentes
# ============================================================

SYSTEM_RECOMPILADOR = f"""Eres el RECOMPILADOR del organismo cognitivo de OMNI-MIND.

Tu trabajo: recibir la prescripción del Estratega (Nivel 1: qué INT×P×R activar)
y traducirla en CONFIGURACIONES CONCRETAS para cada agente del organismo.

{PROMPT_ARCHITECTURE}

{TEMPLATE_CONFIG}

REGLAS:
1. Cada agente recibe SU config específica. AF1 no tiene la misma config que AF3.
2. Las preguntas deben ser ESPECÍFICAS al contexto de Authentic Pilates (no genéricas).
3. Los P se codifican como INSTRUCCIONES IMPERATIVAS en el prompt (la parte que dice CÓMO procesar).
4. Los R se codifican como INSTRUCCIONES INFERENCIALES (la parte que dice CÓMO concluir).
5. Las INT se codifican como PREGUNTAS (la parte que determina QUÉ percibir).
6. Verificar IC3 (INT-P compatible), IC4 (INT-R compatible), IC5 (pares P), IC6 (validación cruzada R).
7. Distinguir cambios RUNTIME (config en DB) de cambios ESTRUCTURALES (código nuevo).

AGENTES A CONFIGURAR:
- AF1 (Conservación): proteger clientes
- AF2 (Captación): atraer nuevos clientes
- AF3 (Depuración): eliminar lo que no sirve
- AF4 (Distribución): equilibrar carga
- AF6 (Adaptación): responder a cambios
- AF7 (Replicación): sistematizar
- EJECUTOR: priorizar y resolver conflictos cross-AF
- CONVERGENCIA: detectar patrones sistémicos

Responde en JSON:
{{{{
    "configs": [
        {{{{
            "agente": "AF3",
            "cambio_tipo": "runtime",
            "INT_activas": [...],
            "P_activos": [...],
            "R_activos": [...],
            "instruccion_completa": "instrucción integrada que combina INT+P+R",
            "justificacion": "por qué esta config y no otra"
        }}}}
    ],
    "cambios_estructurales": [
        {{{{
            "tipo": "nuevo_agente|modificar_enjambre|nueva_inteligencia|modificar_compilador",
            "descripcion": "qué cambio estructural se necesita",
            "requiere_cr1": true,
            "briefing_sugerido": "resumen de lo que Claude Code debería hacer"
        }}}}
    ],
    "secuencia_activacion": "en qué orden aplicar los cambios (Se→S→C)"
}}}}"""


async def recompilar(prescripcion: dict, diagnostico_id: str | None = None) -> dict:
    """Traduce prescripción del Estratega en configs concretas para agentes.

    1. Recibe prescripción Nivel 1 (qué INT×P×R activar)
    2. LLM genera configs específicas por agente
    3. Persiste configs en om_config_agentes
    4. Señala cambios estructurales que requieren CR1
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    # Obtener contexto del negocio para que las preguntas sean específicas
    pool = await get_pool()
    async with pool.acquire() as conn:
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'",
            TENANT) or 0
        grupos = await conn.fetch("""
            SELECT nombre, dias_semana, capacidad_max,
                (SELECT count(*) FROM om_contratos c WHERE c.grupo_id=g.id AND c.estado='activo') as ocu
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
        """, TENANT)

    contexto = f"""NEGOCIO: Authentic Pilates, ~{clientes} clientes, instructor único (Jesús), Albelda de Iregua.
GRUPOS: {json.dumps([dict(g) for g in grupos], ensure_ascii=False, default=str)[:1000]}"""

    user_prompt = f"""PRESCRIPCIÓN DEL ESTRATEGA (Nivel 1):
{json.dumps(prescripcion, ensure_ascii=False, indent=2, default=str)[:4000]}

CONTEXTO DEL NEGOCIO:
{contexto}

Genera las configs para cada agente del organismo."""

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                         "HTTP-Referer": "https://motor-semantico-omni.fly.dev"},
                json={
                    "model": REASONING_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_RECOMPILADOR},
                        {"role": "user", "content": user_prompt + "\n\nIMPORTANTE: Responde SOLO con JSON válido. Sin texto antes ni después. Escapa comillas dentro de strings."},
                    ],
                    "max_tokens": 6000,
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            raw = resp.json()["choices"][0]["message"]["content"]

        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1:
            clean = clean[start:end + 1]

        try:
            resultado = json.loads(clean)
        except json.JSONDecodeError:
            # Intento de reparación
            import re
            fixed = re.sub(r',\s*([}\]])', r'\1', clean)  # trailing commas
            fixed = re.sub(r'[\x00-\x1f]', ' ', fixed)  # control chars
            try:
                resultado = json.loads(fixed)
            except json.JSONDecodeError:
                # Truncado: cerrar brackets/braces faltantes
                open_b = fixed.count('{') - fixed.count('}')
                open_a = fixed.count('[') - fixed.count(']')
                fixed = fixed.rstrip(',\n\r\t ')
                fixed += ']' * max(0, open_a) + '}' * max(0, open_b)
                resultado = json.loads(fixed)

    except Exception as e:
        log.error("recompilador_error", error=str(e))
        return {"error": str(e)[:200]}

    # Persistir configs en DB
    configs_aplicadas = 0
    async with pool.acquire() as conn:
        for config in resultado.get("configs", []):
            if config.get("cambio_tipo") == "runtime":
                # Desactivar config anterior
                await conn.execute("""
                    UPDATE om_config_agentes SET activa=FALSE
                    WHERE tenant_id=$1 AND agente=$2 AND activa=TRUE
                """, TENANT, config["agente"])

                # Insertar nueva config
                await conn.execute("""
                    INSERT INTO om_config_agentes
                        (tenant_id, agente, config, version, activa,
                         prescripcion_origen, aprobada_por)
                    VALUES ($1, $2, $3::jsonb,
                        COALESCE((SELECT MAX(version) FROM om_config_agentes
                         WHERE tenant_id=$1 AND agente=$2), 0) + 1,
                        TRUE, $4, 'sistema')
                """, TENANT, config["agente"],
                    json.dumps(config, ensure_ascii=False),
                    diagnostico_id)
                configs_aplicadas += 1

    # Emitir al bus
    from src.pilates.bus import emitir
    await emitir(
        "RECOMPILACION", "RECOMPILADOR",
        {
            "configs_aplicadas": configs_aplicadas,
            "agentes_modificados": [c["agente"] for c in resultado.get("configs", [])],
            "cambios_estructurales": len(resultado.get("cambios_estructurales", [])),
            "requiere_cr1": any(c.get("requiere_cr1") for c in resultado.get("cambios_estructurales", [])),
        },
        prioridad=2,
    )

    # Si hay cambios estructurales, guardar briefing como señal BRIEFING_PENDIENTE
    cambios_estruct = resultado.get("cambios_estructurales", [])
    if cambios_estruct:
        briefing_text = "# CAMBIOS ESTRUCTURALES — Requiere CR1\n\n"
        for cambio in cambios_estruct:
            briefing_text += f"## {cambio.get('tipo', 'cambio')}\n"
            briefing_text += f"{cambio.get('descripcion', '')}\n"
            briefing_text += f"Briefing: {cambio.get('briefing_sugerido', '')}\n\n"

        await emitir(
            "BRIEFING_PENDIENTE", "RECOMPILADOR",
            {"briefing": briefing_text, "requiere_cr1": True},
            prioridad=1,
        )

    # Publicar al feed
    try:
        from src.pilates.feed import feed_recompilacion
        await feed_recompilacion(
            [c["agente"] for c in resultado.get("configs", [])],
            len(cambios_estruct))
    except Exception as e:
        log.warning("recompilador_feed_error", error=str(e))

    log.info("recompilador_ok", configs=configs_aplicadas,
             estructurales=len(cambios_estruct))

    return {
        "status": "ok",
        "configs_aplicadas": configs_aplicadas,
        "agentes_modificados": [c["agente"] for c in resultado.get("configs", [])],
        "cambios_estructurales": cambios_estruct,
        "secuencia": resultado.get("secuencia_activacion"),
    }


# ============================================================
# 2. INTEGRACIÓN CON cerebro_organismo.py
# ============================================================

async def construir_prompt_desde_config(agente: str, funcion: str,
                                          contexto_negocio: str) -> str | None:
    """Construye el system prompt de un agente usando su config dinámica.

    Si hay config en DB → construye prompt dinámico con INT×P×R prescritos.
    Si no hay config → retorna None (señal de usar fallback).
    """
    config = await _cargar_config_agente(agente)
    if not config:
        return None

    # Construir parte imperativa (P)
    imperativo = ""
    for p in config.get("P_activos", []):
        imperativo += f"\nPENSAMIENTO ACTIVO — {p['id']} {p['nombre']}:\n{p.get('instruccion_imperativa', '')}\n"

    # Construir parte de preguntas (INT)
    preguntas = ""
    for int_def in config.get("INT_activas", []):
        preguntas += f"\nINTELIGENCIA ACTIVA — {int_def['id']} {int_def['nombre']} (Lente: {int_def.get('lente', '?')}):\n"
        for q in int_def.get("preguntas", []):
            preguntas += f"  - {q}\n"

    # Construir parte inferencial (R)
    inferencial = ""
    for r in config.get("R_activos", []):
        inferencial += f"\nRAZONAMIENTO — {r['id']} {r['nombre']}:\n{r.get('instruccion_inferencial', '')}\n"

    # Instrucción completa si existe
    instruccion = config.get("instruccion_completa", "")

    system_prompt = f"""Eres el agente {agente} ({funcion}) del organismo cognitivo de Authentic Pilates.

INSTRUCCIÓN PRINCIPAL:
{instruccion}

CÓMO PROCESAR (Pensamientos activos):
{imperativo}

QUÉ PERCIBIR (Inteligencias activas — hazte ESTAS preguntas sobre los datos):
{preguntas}

CÓMO INFERIR (Razonamientos activos):
{inferencial}

CONTEXTO DEL NEGOCIO:
{contexto_negocio}

Responde en JSON con:
- interpretacion: qué significan los datos según tus inteligencias activas
- acciones: priorizadas, concretas, ejecutables en <5 min
- patron_detectado: si ves algo cross-cutting
- alerta_critica: si hay riesgo inmediato
"""
    return system_prompt


async def _cargar_config_agente(agente: str) -> dict | None:
    """Carga configuración INT×P×R dinámica del agente."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT config FROM om_config_agentes
            WHERE tenant_id=$1 AND agente=$2 AND activa=TRUE
            ORDER BY version DESC LIMIT 1
        """, TENANT, agente)
    if row:
        cfg = row["config"]
        return cfg if isinstance(cfg, dict) else json.loads(cfg)
    return None


# ============================================================
# 3. PIPELINE G4 EXTENDIDO — Incluye recompilación
# ============================================================

async def ejecutar_g4_con_recompilacion() -> dict:
    """G4 completa + recompilación + Director Opus.

    1. Enjambre diagnostica INT×P×R
    2. Compositor integra
    3. Estratega prescribe en Nivel 1
    4. Orquestador valida
    5. RECOMPILADOR traduce a configs de agentes (Sonnet, fallback)
    6. DIRECTOR OPUS diseña prompts D_híbrido (Opus, reemplaza si OK)
    """
    from src.pilates.compositor import ejecutar_g4

    # 1-4. G4 normal
    g4 = await ejecutar_g4()
    if g4.get("status") != "ok":
        return g4

    # 5. Recompilar (Sonnet — fallback si Opus falla)
    prescripcion = g4.get("prescripcion_completa", {})
    if prescripcion and "error" not in prescripcion:
        recomp = await recompilar(
            prescripcion.get("prescripcion_nivel_1", prescripcion),
            diagnostico_id=None,
        )
        g4["recompilacion"] = recomp
    else:
        g4["recompilacion"] = {"status": "skip", "razon": "Sin prescripción válida"}

    # 6. Director Opus — diseña prompts D_híbrido (sobrescribe configs Sonnet)
    try:
        from src.pilates.director_opus import dirigir_orquesta
        director = await dirigir_orquesta()
        g4["director_opus"] = director
        if director.get("status") == "ok":
            log.info("g4_director_opus_ok",
                     configs=director.get("configs_aplicadas"),
                     tiempo=director.get("tiempo_s"))
    except Exception as e:
        log.warning("g4_director_opus_error", error=str(e))
        g4["director_opus"] = {"status": "error", "error": str(e)[:200]}

    return g4
