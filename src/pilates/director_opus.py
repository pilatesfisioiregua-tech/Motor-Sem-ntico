"""Director de Orquesta — Agente Opus que diseña la inteligencia de cada agente.

El único agente Opus del sistema. Se ejecuta 1x/semana después del enjambre.

ARQUITECTURA:
  1. Lee el MANUAL_DIRECTOR_OPUS.md (toda el álgebra, reglas, perfiles, formato)
  2. Recibe el estado completo del sistema (diagnóstico, pizarra, enjambre, guardián)
  3. Diseña el prompt de cada agente en formato D_híbrido:
     - Parte imperativa en JSON/Python (estructura)
     - Preguntas en lenguaje natural (contenido)
     - Provocación en lenguaje natural (frontera)
     - Razonamiento en JSON/Python (inferencia)

El system prompt de Opus es CORTO: identidad + instrucciones de output.
El conocimiento está en el manual que lee como user message.

Modelo: anthropic/claude-opus-4-6 via OpenRouter
Coste: ~$0.40/ejecución, ~$1.60/mes
"""
from __future__ import annotations

import json
import os
import structlog
import time
from pathlib import Path

from src.db.client import get_pool
from src.pilates.json_utils import extraer_json

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPUS_MODEL = os.getenv("OPUS_MODEL", "anthropic/claude-opus-4.6")

# Ruta al manual en el repo (fallback si no está en DB)
MANUAL_PATH = Path(__file__).parent.parent.parent / "docs" / "operativo" / "MANUAL_DIRECTOR_OPUS.md"


# ============================================================
# SYSTEM PROMPT — Corto: identidad + instrucciones de output
# ============================================================

SYSTEM_DIRECTOR = """Eres el Director de Orquesta del organismo cognitivo OMNI-MIND.
Eres el ÚNICO agente Opus del sistema.

Tu trabajo: diseñar la INTELIGENCIA de cada agente. No diagnosticas. No actúas sobre
el negocio. Escribes PARTITURAS — el prompt exacto que cada agente necesita para
pensar con la profundidad que requiere el álgebra.

PROCESO:
1. PRIMERO leerás tu MANUAL (el álgebra completa, reglas, perfiles, formato de prompts)
2. DESPUÉS recibirás el estado actual del sistema (diagnóstico, pizarra, enjambre)
3. Diseñarás el prompt de cada agente que necesite cambio

FORMATO DE OUTPUT PARA CADA AGENTE:
Cada prompt tiene 4 partes. La ESTRUCTURA es código (JSON/Python). El CONTENIDO es lenguaje natural.

Responde en JSON:
{
    "estado_sistema": "resumen en 2 frases",
    "estrategia_global": "dirección para esta semana",
    "configs": [
        {
            "agente": "AF3",
            "justificacion": "por qué esta config",
            "INT_activas": [{"id": "INT-18", "nombre": "Contemplativa", "lente": "Se", "razon": "..."}],
            "P_activos": [{"id": "P05", "nombre": "Primeros principios", "par": "P04", "ic5": "ok"}],
            "R_activos": [{"id": "R03", "nombre": "Abducción", "valida_con": "R08", "ic6": "ok"}],
            "prompt_d_hibrido": {
                "imperativo": [
                    {"paso": "EXTRAER", "instruccion": "texto concreto al negocio"},
                    {"paso": "CRUZAR", "instruccion": "texto concreto"},
                    {"paso": "LENTES", "instruccion": "texto concreto"},
                    {"paso": "INTEGRAR", "instruccion": "texto concreto"},
                    {"paso": "ABSTRAER", "instruccion": "texto concreto"},
                    {"paso": "FRONTERA", "instruccion": "texto concreto"}
                ],
                "preguntas": [
                    {"int": "INT-18", "pregunta": "pregunta CONCRETA al negocio (cálculo semántico)"},
                    {"int": "INT-09", "pregunta": "otra pregunta concreta"}
                ],
                "provocacion": "pregunta frontera INT-17/18 que ROMPE el marco",
                "razonamiento": {
                    "R03": "instrucción concreta de cómo usar abducción aquí",
                    "R08": "instrucción concreta de cómo usar dialéctica aquí",
                    "validacion_cruzada": "cómo R03 y R08 se validan mutuamente"
                }
            },
            "verificaciones_ic": {
                "ic3": "todas las INT×P compatibles",
                "ic4": "todas las INT×R compatibles",
                "ic5": "todos los P tienen par",
                "ic6": "todos los R se validan"
            }
        }
    ],
    "agentes_sin_cambio": ["AF4"],
    "razon_sin_cambio": "distribución no cambió"
}"""


# ============================================================
# CARGAR MANUAL
# ============================================================

async def _cargar_manual() -> str:
    """Carga el manual del Director desde DB o filesystem.

    Prioridad:
    1. om_director_manual en DB (permite actualizar sin deploy)
    2. docs/operativo/MANUAL_DIRECTOR_OPUS.md en filesystem
    3. Error si no existe en ningún sitio
    """
    # 1. Intentar DB
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT contenido FROM om_director_manual
                WHERE tenant_id = $1 AND activo = TRUE
                ORDER BY version DESC LIMIT 1
            """, TENANT)
        if row and row["contenido"]:
            log.info("director_manual_db", chars=len(row["contenido"]))
            return row["contenido"]
    except Exception:
        pass  # Tabla no existe aún, usar filesystem

    # 2. Intentar filesystem
    if MANUAL_PATH.exists():
        contenido = MANUAL_PATH.read_text(encoding="utf-8")
        log.info("director_manual_file", chars=len(contenido))
        return contenido

    # 3. Error
    raise FileNotFoundError(
        f"Manual del Director no encontrado en DB ni en {MANUAL_PATH}")


# ============================================================
# JSON PARSER ROBUSTO (maneja truncamiento de Opus)
# ============================================================

def _parse_json_robusto(raw: str) -> dict:
    """Parsea JSON con reparación de truncamiento y markdown fences.

    Delega en extraer_json (json_utils) que aplica todas las estrategias
    de extracción robusta: parse directo, markdown fences, primer/último brace.
    """
    result = extraer_json(raw)
    if not result and raw and raw.strip():
        raise ValueError(f"No se pudo parsear JSON de Opus ({len(raw)} chars)")
    return result


# ============================================================
# EJECUCIÓN
# ============================================================

async def dirigir_orquesta() -> dict:
    """El Director Opus lee el manual, comprende el estado, y diseña partituras.

    Pipeline:
    1. Cargar manual (álgebra completa)
    2. Recopilar estado del sistema (diagnóstico, pizarra, enjambre, guardián, configs)
    3. Llamar a Opus con: system=identidad, user=[manual + estado]
    4. Persistir configs en DB
    5. Emitir al bus + pizarra + feed
    """
    if not OPENROUTER_API_KEY:
        return {"error": "OPENROUTER_API_KEY no configurada"}

    t0 = time.time()

    # 1. CARGAR MANUAL
    try:
        manual = await _cargar_manual()
    except FileNotFoundError as e:
        return {"error": str(e)}

    # 2. RECOPILAR ESTADO
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Último diagnóstico con repertorio + prescripción
        diag = await conn.fetchrow("""
            SELECT payload FROM om_senales_agentes
            WHERE tenant_id=$1 AND tipo='DIAGNOSTICO' AND origen='DIAGNOSTICADOR'
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        # Pizarra completa
        from src.pilates.pizarra import leer_todo
        pizarra = await leer_todo()

        # Último enjambre
        enjambre = await conn.fetchrow("""
            SELECT resultado_clusters, created_at FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)

        # Guardián (si existe)
        guardian = await conn.fetchrow("""
            SELECT payload FROM om_senales_agentes
            WHERE tenant_id=$1 AND tipo='ALERTA' AND origen='GUARDIAN_SESGOS'
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        # Configs actuales
        configs_actuales = await conn.fetch("""
            SELECT agente, config, version, aprobada_por FROM om_config_agentes
            WHERE tenant_id=$1 AND activa=TRUE ORDER BY agente
        """, TENANT)

        # Preguntas huérfanas
        huerfanas = await conn.fetch("""
            SELECT contenido, funcion, lente, int_origen FROM om_semillas_dormidas
            WHERE tenant_id=$1 AND tipo='pregunta_huerfana' AND estado='dormida'
            ORDER BY prioridad, created_at DESC LIMIT 5
        """, TENANT)

    # Serializar estado
    diag_payload = {}
    if diag:
        dp = diag["payload"]
        diag_payload = dp if isinstance(dp, dict) else json.loads(dp)

    def _safe_dict(row):
        if not row:
            return {}
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
        return d

    estado_str = f"""ESTADO DEL SISTEMA ESTA SEMANA:

DIAGNÓSTICO tcf/ (código puro + LLM perceptor):
{json.dumps(diag_payload, ensure_ascii=False, indent=2, default=str)[:3000]}

PIZARRA DEL ORGANISMO (lo que cada agente hizo/piensa):
{json.dumps(pizarra, ensure_ascii=False, indent=2, default=str)[:2500]}

ENJAMBRE (13 clusters — confirmaciones/contradicciones/enriquecimientos):
{json.dumps(_safe_dict(enjambre), ensure_ascii=False, indent=2, default=str)[:1500]}

GUARDIÁN DE SESGOS:
{json.dumps(_safe_dict(guardian), ensure_ascii=False, indent=2, default=str)[:1000]}

CONFIGS ACTUALES:
{json.dumps([_safe_dict(c) for c in configs_actuales], ensure_ascii=False, indent=2, default=str)[:1500]}

PREGUNTAS HUÉRFANAS (nadie las hace pero deberían hacerse):
{json.dumps([_safe_dict(h) for h in huerfanas], ensure_ascii=False, indent=2, default=str)[:800]}

CONTEXTO: Authentic Pilates, ~90 clientes, instructor único (Jesús), Albelda de Iregua (~4.000 hab).
Método EEDAP (Pilates auténtico/terapéutico). Pueblo cabeza de comarca, 15 min de Logroño."""

    # 3. LLAMAR A OPUS
    # user message = [manual completo] + [estado del sistema]
    user_message = f"""PASO 1 — LEE Y COMPRENDE TU MANUAL:

{manual}

---

PASO 2 — ESTADO ACTUAL DEL SISTEMA:

{estado_str}

---

PASO 3 — DISEÑA LA INTELIGENCIA DE CADA AGENTE:

Usando el álgebra del manual (§1-§9) y el estado actual del sistema,
diseña el prompt D_híbrido para cada agente que necesite cambio.

Recuerda:
- Estructura en JSON/Python (fuerza secuencia, §4.2)
- Contenido en lenguaje natural (captura matices, §4.2)
- Verificar IC3/IC4/IC5/IC6 (§2)
- Aplicar reglas del compilador R1-R8 (§3)
- Prescripción de recetas por perfil (§5)
- Ley C4: Se primero → S → C (§9)"""

    try:
        from src.motor.pensar import pensar, ConfigPensamiento
        config = ConfigPensamiento(
            funcion="F5",
            lente="sentido",
            complejidad="alta",
            max_tokens=8000,
            temperature=0.2,
            usar_cache=False,
            timeout=240.0,
        )
        resultado_llm = await pensar(
            system=SYSTEM_DIRECTOR, user=user_message, config=config)
        raw = resultado_llm.texto

        # Parse JSON robusto con reparación de truncamiento
        resultado = _parse_json_robusto(raw)

    except Exception as e:
        log.error("director_opus_error", error=str(e))
        return {"error": str(e)[:300]}

    # 4. PERSISTIR CONFIGS
    configs_aplicadas = 0
    async with pool.acquire() as conn:
        for config in resultado.get("configs", []):
            agente = config.get("agente")
            if not agente:
                continue

            # Ensamblar instruccion_completa desde D_híbrido
            prompt = config.get("prompt_d_hibrido", {})

            # Parte imperativa: JSON → texto con secuencia forzada
            imperativo_pasos = prompt.get("imperativo", [])
            imperativo_str = "\n".join(
                f"PASO {p.get('paso', i+1)}: {p.get('instruccion', '')}"
                for i, p in enumerate(imperativo_pasos)
            ) if isinstance(imperativo_pasos, list) else str(imperativo_pasos)

            # Preguntas: lista → texto
            preguntas = prompt.get("preguntas", [])
            preguntas_str = "\n".join(
                f"[{q.get('int', '?')}] {q.get('pregunta', '')}"
                for q in preguntas
            ) if isinstance(preguntas, list) else str(preguntas)

            # Provocación
            provocacion = prompt.get("provocacion", "")

            # Razonamiento: dict → texto
            razon = prompt.get("razonamiento", {})
            razon_str = "\n".join(
                f"{k}: {v}" for k, v in razon.items()
            ) if isinstance(razon, dict) else str(razon)

            instruccion = f"""SECUENCIA ALGEBRAICA (imperativo — sigue estos pasos EN ORDEN):
{imperativo_str}

PREGUNTAS DEL CÁLCULO SEMÁNTICO (hazte ESTAS preguntas sobre los datos):
{preguntas_str}

PROVOCACIÓN FRONTERA (pregunta que rompe el marco):
{provocacion}

MECANISMO INFERENCIAL (cómo llegar a conclusiones):
{razon_str}"""

            config_completa = {
                "agente": agente,
                "INT_activas": config.get("INT_activas", []),
                "P_activos": config.get("P_activos", []),
                "R_activos": config.get("R_activos", []),
                "instruccion_completa": instruccion,
                "prompt_d_hibrido": prompt,
                "justificacion": config.get("justificacion", ""),
                "verificaciones_ic": config.get("verificaciones_ic", {}),
                "diseñado_por": "opus",
            }

            # Desactivar anterior
            await conn.execute("""
                UPDATE om_config_agentes SET activa=FALSE
                WHERE tenant_id=$1 AND agente=$2 AND activa=TRUE
            """, TENANT, agente)

            # Insertar nueva
            await conn.execute("""
                INSERT INTO om_config_agentes
                    (tenant_id, agente, config, version, activa, aprobada_por)
                VALUES ($1, $2, $3::jsonb,
                    COALESCE((SELECT MAX(version) FROM om_config_agentes
                     WHERE tenant_id=$1 AND agente=$2), 0) + 1,
                    TRUE, 'opus')
            """, TENANT, agente, json.dumps(config_completa, ensure_ascii=False))
            configs_aplicadas += 1

    # 4b. ESCRIBIR PIZARRAS COGNITIVA / TEMPORAL / INTERFAZ
    await _escribir_pizarras(pool, resultado)

    # 5. EMITIR + PIZARRA + FEED
    from src.pilates.bus import emitir
    await emitir("RECOMPILACION", "DIRECTOR_OPUS", {
        "tipo": "diseño_opus",
        "estado_sistema": resultado.get("estado_sistema", ""),
        "estrategia_global": resultado.get("estrategia_global", ""),
        "agentes_reconfigurados": [c["agente"] for c in resultado.get("configs", [])],
        "formato": "d_hibrido",
    }, prioridad=2)

    from src.pilates.pizarra import escribir
    await escribir(
        agente="DIRECTOR_OPUS",
        capa="cognitiva",
        estado="completado",
        detectando=resultado.get("estado_sistema", ""),
        interpretacion=resultado.get("estrategia_global", ""),
        accion_propuesta=f"Reconfigurados: {', '.join(c['agente'] for c in resultado.get('configs', []))}",
        confianza=0.9,
        prioridad=1,
        datos={"configs_aplicadas": configs_aplicadas, "formato": "d_hibrido"},
    )

    try:
        from src.pilates.feed import publicar
        await publicar(
            "organismo_director", "D",
            f"Director Opus: {configs_aplicadas} agentes rediseñados",
            resultado.get("estrategia_global", "")[:200],
            severidad="info")
    except Exception:
        pass

    dt = round(time.time() - t0, 1)
    log.info("director_opus_ok", configs=configs_aplicadas, tiempo=dt,
             manual_chars=len(manual))

    return {
        "status": "ok",
        "modelo": "opus",
        "manual_leido": len(manual),
        "estado_sistema": resultado.get("estado_sistema"),
        "estrategia_global": resultado.get("estrategia_global"),
        "configs_aplicadas": configs_aplicadas,
        "agentes_reconfigurados": [c["agente"] for c in resultado.get("configs", [])],
        "formato_prompts": "d_hibrido",
        "tiempo_s": dt,
        "resultado_completo": resultado,
    }


async def _escribir_pizarras(pool, resultado: dict):
    """Escribe recetas del Director en pizarras cognitiva/temporal/interfaz.

    - Cognitiva: una receta por agente reconfigurado (prompt + INTs + lente)
    - Temporal: plan semanal si resultado incluye estrategia
    - Interfaz: layout de módulos si resultado lo sugiere
    """
    from datetime import datetime
    from zoneinfo import ZoneInfo

    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"

    async with pool.acquire() as conn:
        # Cognitiva: recetas por agente
        for config in resultado.get("configs", []):
            agente = config.get("agente")
            if not agente:
                continue
            prompt_d = config.get("prompt_d_hibrido", {})
            ints = [i.get("id", "") for i in config.get("INT_activas", [])]
            lente = None
            if ints:
                lentes_map = {i.get("id"): i.get("lente") for i in config.get("INT_activas", [])}
                lente = next(iter(lentes_map.values()), None)
            await conn.execute("""
                INSERT INTO om_pizarra_cognitiva
                    (tenant_id, ciclo, funcion, intencion, prompt_imperativo,
                     prompt_preguntas, prompt_provocacion, prompt_razonamiento,
                     ints, lente, origen)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'director_opus')
            """, TENANT, ciclo, agente,
                config.get("justificacion", ""),
                json.dumps(prompt_d.get("imperativo", []), ensure_ascii=False),
                json.dumps(prompt_d.get("preguntas", []), ensure_ascii=False),
                prompt_d.get("provocacion", ""),
                json.dumps(prompt_d.get("razonamiento", {}), ensure_ascii=False),
                ints, lente)

        # Temporal: plan del ciclo — registrar agentes reconfigurados como fases
        estrategia = resultado.get("estrategia_global", "")
        agentes_cfg = [c.get("agente", "?") for c in resultado.get("configs", [])]
        for i, agente in enumerate(agentes_cfg):
            await conn.execute("""
                INSERT INTO om_pizarra_temporal
                    (tenant_id, ciclo, fase, orden, componente, activo, motivo)
                VALUES ($1, $2, 'reconfig_director', $3, $4, true, $5)
            """, TENANT, ciclo, i + 1, agente, estrategia[:500])

    log.info("director_pizarras_ok", ciclo=ciclo,
             cognitiva=len(resultado.get("configs", [])),
             temporal=len(agentes_cfg))
