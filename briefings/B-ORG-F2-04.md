# B-ORG-F2-04: Recompilador — El sistema se modifica a sí mismo

**Fecha:** 23 marzo 2026
**Prioridad:** MÁXIMA — Esto es lo que hace al sistema VIVO de verdad
**Modelo:** `anthropic/claude-sonnet-4.6` (Recompilador) + Claude Code (ejecutor)
**Dependencia:** B-ORG-F2-03 ejecutado (prescripción Nivel 1 disponible)

---

## LA IDEA CENTRAL

El motor cognitivo (enjambre) es la clave para TODO porque diagnostica el estado INT×P×R de CUALQUIER COSA: el negocio, una decisión, un agente, el propio sistema cognitivo.

Pero diagnosticar sin ACTUAR sobre el diagnóstico es un termómetro más.

La acción real es: **modificar los prompts de los agentes** para que tengan la inteligencia, el pensamiento y el razonamiento correctos — según cómo va evolucionando el sistema.

Cada prompt tiene dos partes (Maestro v4 §1.1):
1. **Parte imperativa** (L0): secuencia algebraica EXTRAER→CRUZAR→LENTES→INTEGRAR→ABSTRAER→FRONTERA
2. **Preguntas** (L1/L2): el contenido específico que determina QUÉ percibe cada agente

La prescripción del Estratega modifica AMBAS:
- Cambiar QUÉ inteligencias están activas → cambiar qué preguntas se hacen
- Cambiar QUÉ pensamientos usar → cambiar CÓMO se procesan las respuestas
- Cambiar QUÉ razonamientos emplear → cambiar CÓMO se llega a conclusiones

## EL CIRCUITO AUTOPOIÉTICO

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ENJAMBRE diagnostica INT×P×R del sistema/negocio/decisión     │
│       │                                                         │
│       ▼                                                         │
│  ESTRATEGA prescribe: "Activar INT-17+P05+R03, desactivar      │
│  INT-07 monopolio, acoplar INT-03 con R03 en vez de R01"       │
│       │                                                         │
│       ▼                                                         │
│  RECOMPILADOR traduce prescripción en:                          │
│    - Cambios a system prompts de AF1-AF7 (cerebro_organismo)   │
│    - Cambios a instrucciones del séquito                        │
│    - Cambios a las preguntas del buscador                       │
│    - Nuevas herramientas cognitivas (preguntas L1/L2)          │
│       │                                                         │
│       ▼                                                         │
│  CLAUDE CODE ejecuta los cambios en el código                   │
│  (o el sistema los aplica en runtime via config dinámica)       │
│       │                                                         │
│       ▼                                                         │
│  Los agentes ejecutan con el NUEVO repertorio cognitivo         │
│       │                                                         │
│       ▼                                                         │
│  ENJAMBRE re-diagnostica → ¿se movieron las lentes?            │
│       │                                                         │
│       └──────────── LOOP ──────────────────────────────────────┘
│                                                                 │
│  FRENO: Solo Jesús (CR1) aprueba cambios estructurales         │
│  Los agentes pueden auto-ajustar dentro de parámetros CR1      │
└─────────────────────────────────────────────────────────────────┘
```

## IMPLEMENTACIÓN: DOS NIVELES DE AUTO-MODIFICACIÓN

### NIVEL A — Runtime (sin tocar código, inmediato)

Los agentes cargan su configuración INT×P×R desde una tabla de la DB.
Cada vez que ejecutan, leen su configuración ACTUAL — no hardcodeada.

```python
# om_config_agentes — tabla de configuración dinámica
CREATE TABLE om_config_agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    agente TEXT NOT NULL,           -- 'AF1', 'AF3', 'EJECUTOR', 'SEQUITO_INT07'...
    config JSONB NOT NULL,          -- {INT_activas, P_activos, R_activos, instruccion, preguntas}
    version INT DEFAULT 1,
    activa BOOLEAN DEFAULT TRUE,
    prescripcion_origen UUID,       -- ID del diagnóstico que generó esta config
    created_at TIMESTAMPTZ DEFAULT now(),
    aprobada_por TEXT,              -- 'sistema' (auto) o 'jesus' (CR1)
    UNIQUE(tenant_id, agente, activa)
);
```

Cada agente, al ejecutar, carga su config:
```python
async def _cargar_config_agente(agente: str) -> dict:
    """Carga configuración INT×P×R dinámica del agente."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT config FROM om_config_agentes
            WHERE tenant_id=$1 AND agente=$2 AND activa=TRUE
            ORDER BY version DESC LIMIT 1
        """, TENANT, agente)
    if row:
        return row["config"] if isinstance(row["config"], dict) else json.loads(row["config"])
    return None  # fallback a config hardcodeada
```

Y el cerebro_organismo.py usa esa config para construir el prompt:
```python
async def razonar(agente, funcion, datos, instruccion_default, nivel=1):
    # Cargar config dinámica si existe
    config = await _cargar_config_agente(agente)
    
    if config:
        # La instrucción viene de la prescripción, no del hardcode
        instruccion = config.get("instruccion", instruccion_default)
        
        # Las INT×P×R activas se inyectan en el system prompt
        ints_activas = config.get("INT_activas", [])
        ps_activos = config.get("P_activos", [])
        rs_activos = config.get("R_activos", [])
        preguntas_extra = config.get("preguntas", [])
        
        # El prompt se CONSTRUYE dinámicamente
        system_prompt = _construir_prompt_dinamico(
            agente, funcion, ints_activas, ps_activos, rs_activos,
            instruccion, preguntas_extra, contexto)
    else:
        # Fallback a prompt hardcodeado (como ahora)
        system_prompt = _construir_prompt_default(agente, funcion, contexto)
```

### NIVEL B — Estructural (Claude Code modifica código, requiere CR1)

Cuando la prescripción implica cambios más profundos:
- Crear un agente nuevo
- Cambiar la arquitectura del enjambre
- Añadir una inteligencia nueva
- Modificar las reglas del compilador

El Recompilador genera un **briefing** que Claude Code ejecuta — con aprobación de Jesús (CR1).

## ARCHIVO A CREAR

`src/pilates/recompilador.py`

## CÓDIGO

```python
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
{{
    "configs": [
        {{
            "agente": "AF3",
            "cambio_tipo": "runtime",
            "INT_activas": [...],
            "P_activos": [...],
            "R_activos": [...],
            "instruccion_completa": "instrucción integrada que combina INT+P+R",
            "justificacion": "por qué esta config y no otra"
        }}
    ],
    "cambios_estructurales": [
        {{
            "tipo": "nuevo_agente|modificar_enjambre|nueva_inteligencia|modificar_compilador",
            "descripcion": "qué cambio estructural se necesita",
            "requiere_cr1": true,
            "briefing_sugerido": "resumen de lo que Claude Code debería hacer"
        }}
    ],
    "secuencia_activacion": "en qué orden aplicar los cambios (Se→S→C)"
}}"""


async def recompilar(prescripcion: dict, diagnostico_id: str = None) -> dict:
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
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": 4000,
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

    # Si hay cambios estructurales, guardar briefing para Claude Code
    cambios_estruct = resultado.get("cambios_estructurales", [])
    if cambios_estruct:
        briefing_text = "# CAMBIOS ESTRUCTURALES — Requiere CR1\n\n"
        for cambio in cambios_estruct:
            briefing_text += f"## {cambio.get('tipo', 'cambio')}\n"
            briefing_text += f"{cambio.get('descripcion', '')}\n"
            briefing_text += f"Briefing: {cambio.get('briefing_sugerido', '')}\n\n"

        await conn.execute("""
            INSERT INTO om_bus_senales (tenant_id, tipo, origen, payload, prioridad)
            VALUES ($1, 'BRIEFING_PENDIENTE', 'RECOMPILADOR', $2::jsonb, 1)
        """, TENANT, json.dumps({"briefing": briefing_text, "requiere_cr1": True}))

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
                                          contexto_negocio: str) -> str:
    """Construye el system prompt de un agente usando su config dinámica.

    Si hay config en DB → construye prompt dinámico con INT×P×R prescritos.
    Si no hay config → usa prompt default hardcodeado.
    """
    config = await _cargar_config_agente(agente)
    if not config:
        return None  # señal de usar fallback

    # Construir parte imperativa (P)
    imperativo = ""
    for p in config.get("P_activos", []):
        imperativo += f"\nPENSAMIENTO ACTIVO — {p['id']} {p['nombre']}:\n{p.get('instruccion_imperativa', '')}\n"

    # Construir parte de preguntas (INT)
    preguntas = ""
    for int_def in config.get("INT_activas", []):
        preguntas += f"\nINTELIGENCIA ACTIVA — {int_def['id']} {int_def['nombre']} (Lente: {int_def['lente']}):\n"
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
    """G4 completa + recompilación de agentes.

    1. Enjambre diagnostica INT×P×R
    2. Compositor integra
    3. Estratega prescribe en Nivel 1
    4. Orquestador valida
    5. ★ RECOMPILADOR traduce a configs de agentes ★
    6. Los agentes se reconfiguran para el próximo ciclo
    """
    from src.pilates.compositor import ejecutar_g4

    # 1-4. G4 normal
    g4 = await ejecutar_g4()
    if g4.get("status") != "ok":
        return g4

    # 5. Recompilar
    prescripcion = g4.get("prescripcion_completa", {})
    if prescripcion and "error" not in prescripcion:
        recomp = await recompilar(
            prescripcion.get("prescripcion_nivel_1", prescripcion),
            diagnostico_id=None,
        )
        g4["recompilacion"] = recomp
    else:
        g4["recompilacion"] = {"status": "skip", "razon": "Sin prescripción válida"}

    return g4
```

## MIGRACIÓN SQL

```sql
-- 022_config_agentes.sql

-- Configuración dinámica INT×P×R por agente
CREATE TABLE IF NOT EXISTS om_config_agentes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    agente TEXT NOT NULL,
    config JSONB NOT NULL,
    version INT DEFAULT 1,
    activa BOOLEAN DEFAULT TRUE,
    prescripcion_origen UUID,
    aprobada_por TEXT DEFAULT 'sistema',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_config_agente ON om_config_agentes(tenant_id, agente, activa);
CREATE INDEX IF NOT EXISTS idx_config_version ON om_config_agentes(tenant_id, agente, version DESC);
```

## CAMBIOS EN cerebro_organismo.py

El `razonar()` actual usa prompts hardcodeados. Con esta integración:

```python
# En cerebro_organismo.py, modificar razonar():

async def razonar(agente, funcion, datos_detectados, instruccion_default, nivel=1):
    # PRIMERO: intentar cargar config dinámica
    from src.pilates.recompilador import construir_prompt_desde_config
    contexto = await _contexto_negocio()
    
    prompt_dinamico = await construir_prompt_desde_config(agente, funcion, contexto)
    
    if prompt_dinamico:
        # Usar prompt RECOMPILADO (con INT×P×R prescritos)
        system_prompt = prompt_dinamico
        log.info("cerebro_usando_config_dinamica", agente=agente)
    else:
        # Fallback a prompt hardcodeado (como antes)
        system_prompt = _construir_prompt_default(agente, funcion, instruccion_default, contexto)
    
    # ... resto igual (call LLM, parse, return) ...
```

## INTEGRACIÓN EN CRON

Cambiar en cron.py el paso G4:

```python
    # 10. G4 — Enjambre cognitivo + prescripción + RECOMPILACIÓN
    try:
        from src.pilates.recompilador import ejecutar_g4_con_recompilacion
        g4 = await ejecutar_g4_con_recompilacion()
        log.info("cron_semanal_g4_ok",
                 perfil=g4.get("perfil_detectado"),
                 recompilados=g4.get("recompilacion", {}).get("configs_aplicadas", 0))
    except Exception as e:
        log.error("cron_semanal_g4_error", error=str(e))
```

## EL EFECTO

**Semana 1:**
- Enjambre diagnostica: "Authentic Pilates = genio mortal (S↑Se↑C↓)"
- Estratega prescribe: "Activar INT-12+INT-09+P12+R04 para subir C"
- Recompilador configura AF7 con preguntas de narrativa y analogía
- AF7 ahora pregunta: "¿Cómo contarías a un instructor nuevo por qué haces el ejercicio de la sirena exactamente así?"

**Semana 2:**
- Los agentes ejecutan con el nuevo repertorio
- AF7 produce: "Jesús no tiene documentado el protocolo de evaluación inicial. Si mañana necesita un sustituto, el 80% de su método se pierde."
- Enjambre re-diagnostica: C subió de 0.40 a 0.44 (AF7 ahora detecta cosas que antes no veía)

**Semana 4:**
- C llegó a 0.50. El Enjambre detecta que ahora Se está cayendo (mucho foco en documentar, poco en cuestionar)
- Estratega prescribe: "Reactivar INT-17+P08 en AF3 y AF6"
- Recompilador actualiza configs
- El sistema se RE-EQUILIBRA solo

**Eso es autopoiesis. El sistema evoluciona.**

## TESTS

### TEST 1: Recompilador genera configs válidas por agente
```python
result = await recompilar(prescripcion_test)
assert result["configs_aplicadas"] >= 3
for agente in result["agentes_modificados"]:
    config = await _cargar_config_agente(agente)
    assert config is not None
    assert "INT_activas" in config
    assert "P_activos" in config
    assert "R_activos" in config
```

### TEST 2: cerebro_organismo usa config dinámica cuando existe
```python
# Insertar config para AF3
# Ejecutar AF3
result = await ejecutar_af3()
# El razonamiento debe reflejar las INT×P×R de la config, no las default
```

### TEST 3: G4 con recompilación ejecuta pipeline completo
```python
result = await ejecutar_g4_con_recompilacion()
assert result["status"] == "ok"
assert result["recompilacion"]["configs_aplicadas"] >= 1
```

### TEST 4: Versiones de config se incrementan
```sql
SELECT agente, version, activa, created_at FROM om_config_agentes
WHERE tenant_id='authentic_pilates' ORDER BY agente, version DESC;
-- Debe mostrar versiones crecientes, solo la última activa
```

### TEST 5: Sin config, agente funciona con fallback hardcodeado
```python
# Borrar config de AF1
# Ejecutar AF1
result = await ejecutar_af1()
assert "razonamiento" in result  # sigue funcionando
```

---

## RESULTADO: EL SISTEMA ESTÁ VIVO

Con este briefing, el circuito autopoiético queda cerrado:

```
Diagnóstico INT×P×R → Prescripción Nivel 1 → Recompilación de prompts
    → Agentes ejecutan con nuevo repertorio → Re-diagnóstico
    → El sistema EVOLUCIONA semana a semana
```

Los agentes no están programados con una inteligencia fija.
Su inteligencia, pensamiento y razonamiento CAMBIAN según lo que
el sistema cognitivo detecta que necesita.

Eso es lo que hace al organismo realmente vivo.
