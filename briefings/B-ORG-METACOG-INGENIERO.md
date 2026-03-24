# B-ORG-METACOG + INGENIERO: Los dos agentes Opus que cierran el organismo

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — sin esto el sistema no aprende de sus propios resultados ni se auto-mejora
**Modelos:** `anthropic/claude-opus-4.6` (Meta-Cognitivo) + Claude Code MCP (Ingeniero)
**Frecuencia:** Meta-Cognitivo mensual, Ingeniero bajo demanda

---

## MAPA DE QUIÉN GESTIONA QUÉ (CON LOS 3 OPUS)

```
DIRECTOR OPUS (semanal)
  → Diseña prompts de AF1-AF7, Ejecutor, Convergencia
  → Escribe configs en DB (om_config_agentes)
  → Los agentes cargan la config al ejecutar
  → ALCANCE: inteligencia de la capa ejecutiva

META-COGNITIVO OPUS (mensual)
  → Evalúa si las partituras del Director FUNCIONARON
  → Ajusta prompts de los 13 clusters + guardián + buscador
  → Audita al Guardián (¿se volvió complaciente?)
  → Evoluciona las NOTAS del texto_caso del evaluador funcional
  → Propone cambios al Manual del Director (CR1)
  → ALCANCE: inteligencia de la capa cognitiva + sensorial

INGENIERO (bajo demanda, disparado por Meta-Cognitivo o Vigía)
  → EJECUTA cambios en el código real via Claude Code
  → Modifica archivos .py, corre tests, hace commit
  → MANOS del organismo — el único que toca el filesystem
  → ALCANCE: el codebase completo (con restricciones de seguridad)
```

```
         META-COGNITIVO OPUS
         (piensa sobre el sistema)
                |
    ┌───────────┼───────────┐
    v           v           v
DIRECTOR    INGENIERO     MANUAL
(configs    (código)      (actualiza)
 DB)        
    |           |           |
    v           v           v
AF1-AF7    archivos .py  MANUAL_DIRECTOR.md
clusters   tests         docs/
buscador   deploy        
```

---

## AGENTE 1: META-COGNITIVO OPUS

### Qué hace

Se ejecuta MENSUALMENTE (después del Cristalizador + Autófago). Lee:
1. Los últimos 4 diagnósticos semanales (evolución del estado ACD)
2. Las últimas 4 pizarras (qué hicieron los agentes cada semana)
3. Las últimas 4 configs del Director (qué partituras escribió)
4. Los resultados del Cristalizador (patrones recurrentes)
5. Los resultados del Guardián de las últimas 4 semanas

Y produce:
- **Evaluación de prescripciones:** ¿Las partituras del Director movieron las lentes?
- **Ajuste de clusters:** ¿Algún cluster necesita más profundidad o menos?
- **Ajuste del Guardián:** ¿Sigue siendo efectivo o se volvió rutinario?
- **Evolución del texto_caso:** Actualizar las NOTAS del evaluador funcional con lo aprendido
- **Propuestas para el Manual:** Cambios al Manual del Director basados en 4 semanas de datos
- **Instrucciones para el Ingeniero:** Qué cambios de código son necesarios

### Archivo: `src/pilates/metacognitivo.py`

```python
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

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPUS_MODEL = "anthropic/claude-opus-4.6"

MANUAL_METACOG_PATH = "docs/operativo/MANUAL_METACOGNITIVO.md"  # futuro


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
        "efectivo": true/false,
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
            "prioridad": 1-5
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

    # Construir input
    user_prompt = f"""ÚLTIMOS 4 DIAGNÓSTICOS (evolución del estado ACD):
{json.dumps([dict(d) for d in diagnosticos], ensure_ascii=False, indent=2, default=str)[:3000]}

PIZARRAS (últimas 4 semanas, qué hicieron los agentes):
{json.dumps([dict(p) for p in pizarras], ensure_ascii=False, indent=2, default=str)[:3000]}

CONFIGS DEL DIRECTOR (qué partituras escribió):
{json.dumps([dict(c) for c in configs_director], ensure_ascii=False, indent=2, default=str)[:2000]}

CRISTALIZACIONES RECIENTES:
{json.dumps([dict(c) for c in cristalizaciones], ensure_ascii=False, indent=2, default=str)[:1000]}

GUARDIÁN ÚLTIMAS 4 SEMANAS:
{json.dumps([dict(g) for g in guardians], ensure_ascii=False, indent=2, default=str)[:1500]}

Evalúa el sistema cognitivo. ¿Las prescripciones funcionaron? ¿Qué ajustar?"""

    try:
        async with httpx.AsyncClient(timeout=180) as client:
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
        await publicar("organismo_metacog", "🧪",
                       f"Meta-Cognitivo: {n_instrucciones} cambios propuestos",
                       resultado.get("evaluacion_prescripciones", {}).get("conclusion", "")[:200],
                       severidad="info")
    except Exception:
        pass

    dt = round(time.time() - t0, 1)
    log.info("metacognitivo_ok", instrucciones=n_instrucciones, tiempo=dt)
    return {"status": "ok", "tiempo_s": dt, "resultado": resultado}
```

---

## AGENTE 2: INGENIERO — Las manos del organismo

### Qué hace

El Ingeniero es el ÚNICO agente que puede modificar el código real. Tiene acceso a Claude Code (Bash, Read, Write, Edit). Se dispara:
1. Por instrucciones del Meta-Cognitivo (mensual)
2. Por alertas del Vigía que requieren fix de código (cuando el Mecánico no puede)
3. Por cristalizaciones que requieren nuevo código

### Niveles de autonomía

```python
NIVELES_SEGURIDAD = {
    "safe": {
        "descripcion": "Cambios que NO pueden romper nada",
        "ejemplos": [
            "Actualizar NOTAS en el texto_caso del diagnosticador",
            "Modificar system prompt de un cluster (string en enjambre.py)",
            "Actualizar MANUAL_DIRECTOR_OPUS.md",
            "Añadir una nueva pregunta a un cluster",
        ],
        "requiere_cr1": False,
        "requiere_test": True,
        "requiere_backup": True,
    },
    "moderado": {
        "descripcion": "Cambios que podrían afectar comportamiento",
        "ejemplos": [
            "Modificar lógica de un AF (sensor o emisión)",
            "Cambiar parámetros del buscador (frecuencia, filtros)",
            "Modificar el pipeline del cron",
        ],
        "requiere_cr1": True,
        "requiere_test": True,
        "requiere_backup": True,
    },
    "estructural": {
        "descripcion": "Cambios que alteran la arquitectura",
        "ejemplos": [
            "Crear un archivo nuevo",
            "Añadir un endpoint nuevo",
            "Modificar migración SQL",
            "Cambiar modelo LLM de un agente",
        ],
        "requiere_cr1": True,
        "requiere_test": True,
        "requiere_backup": True,
        "requiere_briefing": True,
    },
    "prohibido": {
        "descripcion": "NUNCA ejecutar autónomamente",
        "ejemplos": [
            "Tocar datos de clientes/pagos",
            "Modificar om_config_agentes directamente (eso es del Director)",
            "Deploy a producción",
            "Eliminar archivos",
            "Modificar su propio código (ingeniero.py)",
        ],
    },
}
```

### Archivo: `src/pilates/ingeniero.py`

```python
"""Ingeniero — Las manos del organismo. Modifica código via Claude Code.

El ÚNICO agente que puede escribir/editar archivos del codebase.
Se dispara por instrucciones del Meta-Cognitivo, alertas del Vigía,
o cristalizaciones.

NIVELES DE SEGURIDAD:
  safe:        ejecuta solo, con backup + test
  moderado:    genera briefing → espera CR1 → ejecuta
  estructural: genera briefing → espera CR1 → ejecuta
  prohibido:   NUNCA ejecuta

PRINCIPIO: "Un organismo que puede modificar su propio código
es un organismo que puede evolucionar. Pero un organismo que
modifica su código sin control puede autodestruirse."

Usa Claude Code MCP (Bash, Read, Write, Edit) para ejecutar.
"""
from __future__ import annotations

import json
import os
import structlog
import time
from datetime import datetime, timezone

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"


# Archivos que el Ingeniero puede modificar sin CR1
ARCHIVOS_SAFE = {
    # System prompts de clusters (strings en enjambre.py)
    "src/pilates/enjambre.py",
    # System prompt del guardián
    "src/pilates/guardian_sesgos.py",
    # NOTAS del texto_caso (dentro de diagnosticador.py)
    "src/pilates/diagnosticador.py",
    # Manual del Director
    "docs/operativo/MANUAL_DIRECTOR_OPUS.md",
    # Buscador (system prompts de los 6 tipos)
    "src/pilates/buscador.py",
    # Generativa (prompts de huérfanas/cristalizador)
    "src/pilates/generativa.py",
}

# Archivos que NUNCA se tocan
ARCHIVOS_PROHIBIDOS = {
    "src/pilates/ingeniero.py",      # No se auto-modifica
    "src/pilates/bus.py",            # Infraestructura crítica
    "src/pilates/router.py",         # Endpoints (security)
    "src/db/client.py",             # DB connection
    "src/pilates/redsys_pagos.py",  # Pagos
    "src/pilates/stripe_pagos.py",  # Pagos
}


async def ejecutar_instruccion(instruccion: dict) -> dict:
    """Ejecuta una instrucción del Meta-Cognitivo o Vigía.

    Args:
        instruccion: {
            tipo: "modificar_prompt|actualizar_manual|fix_bug|nuevo_detector",
            archivo: "src/pilates/xxx.py",
            cambio: "descripción precisa",
            razon: "por qué",
            test: "cómo verificar",
            seguridad: "safe|moderado|estructural",
            prioridad: 1-5,
        }

    Returns:
        Resultado de la ejecución.
    """
    archivo = instruccion.get("archivo", "")
    seguridad = instruccion.get("seguridad", "moderado")

    # NUNCA tocar archivos prohibidos
    if any(archivo.endswith(p) for p in ARCHIVOS_PROHIBIDOS):
        log.warning("ingeniero_prohibido", archivo=archivo)
        return {"status": "prohibido", "archivo": archivo, "razon": "Archivo en lista de prohibidos"}

    # Si no es safe, registrar como pendiente CR1
    if seguridad != "safe":
        return await _registrar_pendiente_cr1(instruccion)

    # Si es safe, verificar que el archivo está en la lista
    if not any(archivo.endswith(s) for s in ARCHIVOS_SAFE):
        log.warning("ingeniero_no_safe", archivo=archivo)
        return await _registrar_pendiente_cr1(instruccion)

    # EJECUTAR cambio safe
    return await _ejecutar_safe(instruccion)


async def _ejecutar_safe(instruccion: dict) -> dict:
    """Ejecuta un cambio safe: backup → modificar → test → commit.

    Usa Claude Code MCP para leer/escribir archivos.
    """
    archivo = instruccion.get("archivo", "")
    cambio = instruccion.get("cambio", "")
    razon = instruccion.get("razon", "")
    test_cmd = instruccion.get("test", "")

    log.info("ingeniero_ejecutando_safe", archivo=archivo, cambio=cambio[:100])

    resultado = {
        "archivo": archivo,
        "tipo": instruccion.get("tipo"),
        "seguridad": "safe",
        "pasos": [],
    }

    try:
        # 1. LEER archivo actual (backup en memoria)
        from pathlib import Path
        repo_base = Path(__file__).parent.parent.parent.parent
        filepath = repo_base / archivo

        if not filepath.exists():
            return {"status": "error", "razon": f"Archivo no existe: {archivo}"}

        contenido_original = filepath.read_text(encoding="utf-8")
        resultado["pasos"].append({"paso": "backup", "status": "ok", "lineas": len(contenido_original.splitlines())})

        # 2. PERSISTIR backup en DB
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO om_ingeniero_backups
                    (tenant_id, archivo, contenido_original, instruccion, created_at)
                VALUES ($1, $2, $3, $4::jsonb, now())
            """, TENANT, archivo, contenido_original,
                json.dumps(instruccion, ensure_ascii=False))
        resultado["pasos"].append({"paso": "backup_db", "status": "ok"})

        # 3. EMITIR instrucción como señal para que Claude Code la ejecute
        # El Ingeniero NO modifica archivos directamente en este loop.
        # Genera un briefing_micro que Claude Code ejecuta.
        briefing_micro = f"""# Instrucción del Ingeniero (auto-safe)

**Archivo:** {archivo}
**Cambio:** {cambio}
**Razón:** {razon}
**Seguridad:** safe (aprobado automáticamente)

## Instrucciones para Claude Code:

1. Leer {archivo}
2. Aplicar el siguiente cambio: {cambio}
3. Verificar: {test_cmd}
4. Si el test pasa: commit con mensaje "🔧 Ingeniero auto-safe: {instruccion.get('tipo', 'cambio')}"
5. Si el test falla: revertir al backup

## RESTRICCIONES:
- Solo modificar el archivo indicado
- No crear archivos nuevos
- No modificar otros archivos
- No hacer deploy
"""

        from src.pilates.bus import emitir
        await emitir("ACCION", "INGENIERO", {
            "tipo": "briefing_micro",
            "archivo": archivo,
            "briefing": briefing_micro,
            "seguridad": "safe",
            "backup_exists": True,
        }, prioridad=instruccion.get("prioridad", 3))
        resultado["pasos"].append({"paso": "briefing_emitido", "status": "ok"})
        resultado["status"] = "briefing_emitido"

    except Exception as e:
        log.error("ingeniero_safe_error", error=str(e), archivo=archivo)
        resultado["status"] = "error"
        resultado["error"] = str(e)[:200]

    # Pizarra
    from src.pilates.pizarra import escribir
    await escribir(
        agente="INGENIERO",
        capa="meta",
        estado="completado" if resultado.get("status") != "error" else "bloqueado",
        detectando=f"Instrucción: {instruccion.get('tipo', '?')} en {archivo}",
        interpretacion=razon[:200],
        accion_propuesta=f"Briefing micro emitido al bus. Seguridad: safe.",
        confianza=0.7,
        prioridad=instruccion.get("prioridad", 3),
    )

    return resultado


async def _registrar_pendiente_cr1(instruccion: dict) -> dict:
    """Registra un cambio que requiere CR1 como briefing pendiente."""
    from src.pilates.bus import emitir

    briefing = f"""# Instrucción del Ingeniero (requiere CR1)

**Archivo:** {instruccion.get('archivo', '?')}
**Tipo:** {instruccion.get('tipo', '?')}
**Cambio:** {instruccion.get('cambio', '?')}
**Razón:** {instruccion.get('razon', '?')}
**Seguridad:** {instruccion.get('seguridad', '?')}
**Origen:** Meta-Cognitivo / Vigía

## Para aprobar:
Jesús: responde "ok" al briefing en el cockpit o ejecuta manualmente con Claude Code.
"""

    await emitir("BRIEFING_PENDIENTE", "INGENIERO", {
        "tipo": "cambio_pendiente_cr1",
        "instruccion": instruccion,
        "briefing": briefing,
        "requiere_cr1": True,
    }, prioridad=instruccion.get("prioridad", 2))

    # Feed
    try:
        from src.pilates.feed import publicar
        await publicar("organismo_ingeniero", "🔧",
                       f"Ingeniero: cambio pendiente CR1",
                       f"{instruccion.get('archivo', '?')}: {instruccion.get('cambio', '?')[:100]}",
                       severidad="warning")
    except Exception:
        pass

    log.info("ingeniero_pendiente_cr1", archivo=instruccion.get("archivo"),
             tipo=instruccion.get("tipo"))

    return {
        "status": "pendiente_cr1",
        "archivo": instruccion.get("archivo"),
        "tipo": instruccion.get("tipo"),
    }


async def procesar_instrucciones_pendientes() -> dict:
    """Lee instrucciones del Meta-Cognitivo del bus y las ejecuta/registra.

    Se ejecuta en el cron mensual, después del Meta-Cognitivo.
    """
    from src.pilates.bus import leer_pendientes, marcar_procesada

    señales = await leer_pendientes(tipo="ACCION", limite=20)
    instrucciones_ingeniero = []

    for s in señales:
        payload = s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"])
        if payload.get("tipo") == "instruccion_ingeniero":
            instrucciones_ingeniero.append({"señal_id": str(s["id"]), "instruccion": payload})
            await marcar_procesada(str(s["id"]), "INGENIERO")

    resultados = []
    for item in instrucciones_ingeniero:
        result = await ejecutar_instruccion(item["instruccion"])
        resultados.append(result)

    safe = sum(1 for r in resultados if r.get("status") == "briefing_emitido")
    cr1 = sum(1 for r in resultados if r.get("status") == "pendiente_cr1")

    log.info("ingeniero_procesadas", total=len(resultados), safe=safe, cr1=cr1)
    return {"total": len(resultados), "safe_ejecutadas": safe, "pendientes_cr1": cr1, "resultados": resultados}
```

## MIGRACIÓN SQL

```sql
-- Añadir a 024_pizarra.sql:

-- Backups del Ingeniero (para rollback)
CREATE TABLE IF NOT EXISTS om_ingeniero_backups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    archivo TEXT NOT NULL,
    contenido_original TEXT NOT NULL,
    instruccion JSONB,
    revertido BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingeniero_backups ON om_ingeniero_backups(tenant_id, archivo, created_at DESC);
```

## INTEGRACIÓN EN CRON

En `_tarea_mensual()`, después del autófago y cristalizador:

```python
    # Meta-Cognitivo: evalúa el sistema cognitivo
    try:
        from src.pilates.metacognitivo import ejecutar_metacognitivo
        metacog = await ejecutar_metacognitivo()
        log.info("cron_mensual_metacog_ok",
                 instrucciones=len(metacog.get("resultado", {}).get("instrucciones_ingeniero", [])))
    except Exception as e:
        log.error("cron_mensual_metacog_error", error=str(e))

    # Ingeniero: procesa instrucciones del Meta-Cognitivo
    try:
        from src.pilates.ingeniero import procesar_instrucciones_pendientes
        ing = await procesar_instrucciones_pendientes()
        log.info("cron_mensual_ingeniero_ok",
                 safe=ing.get("safe_ejecutadas", 0),
                 cr1=ing.get("pendientes_cr1", 0))
    except Exception as e:
        log.error("cron_mensual_ingeniero_error", error=str(e))
```

## COSTE

| Agente | Frecuencia | Modelo | Coste/mes |
|---|---|---|---|
| Meta-Cognitivo | 1x/mes | claude-opus-4.6 | ~$0.50 |
| Ingeniero | bajo demanda (~3-5/mes) | código puro (briefings) | $0 |
| **Total** | | | **~$0.50/mes** |

## TESTS

### T1: Meta-Cognitivo evalúa prescripciones
```python
result = await ejecutar_metacognitivo()
assert "evaluacion_prescripciones" in result["resultado"]
assert "instrucciones_ingeniero" in result["resultado"]
```

### T2: Ingeniero ejecuta instrucción safe
```python
inst = {"tipo": "actualizar_manual", "archivo": "docs/operativo/MANUAL_DIRECTOR_OPUS.md",
        "cambio": "Añadir nota sobre patrón X", "razon": "Cristalizado", "seguridad": "safe"}
result = await ejecutar_instruccion(inst)
assert result["status"] == "briefing_emitido"
```

### T3: Ingeniero bloquea archivo prohibido
```python
inst = {"tipo": "fix", "archivo": "src/pilates/ingeniero.py", "seguridad": "safe"}
result = await ejecutar_instruccion(inst)
assert result["status"] == "prohibido"
```

### T4: Ingeniero registra CR1 para cambios moderados
```python
inst = {"tipo": "modificar_af", "archivo": "src/pilates/af1_conservacion.py",
        "cambio": "Añadir detector X", "seguridad": "moderado"}
result = await ejecutar_instruccion(inst)
assert result["status"] == "pendiente_cr1"
```

### T5: Backup se persiste
```sql
SELECT archivo, created_at FROM om_ingeniero_backups
WHERE tenant_id='authentic_pilates' ORDER BY created_at DESC LIMIT 1;
```

---

## CENSO FINAL: 53 agentes + 8 algebraicos + pizarra

```
EJECUTIVA (12):   AF1-AF7, Ejecutor, Convergencia, Gestor, Séquito, Cerebro
COGNITIVA (19):   6 INT + 4 P + 3 R + Guardián + Compositor + Director Opus + Orquestador
META (8):         Observador, Vigía, Mecánico, Autófago, Propiocepción, Cron,
                  ★ Meta-Cognitivo Opus, ★ Ingeniero
SENSORIAL (10):   Diagnosticador, Generador, 7 Buscadores, Collector
GENERATIVA (4):   Huérfanas, Cristalizador, Semillas, Puente Séquito
ALGEBRAICO (8):   Evaluador, Campo, Campo dual, Clasificador, Repertorio, Prescriptor, Flags, Recetas
COMPARTIDO (1):   Pizarra

TOTAL: 53 agentes + 8 algebraicos + 1 pizarra = 62 piezas
OPUS: 3 (Director + Meta-Cognitivo + compartido con Ingeniero via briefings)
```

## COSTE TOTAL ACTUALIZADO

```
Semanal (G4 + AF + buscador):   ~$1.68
Mensual (Metacog + Ingeniero):  ~$0.50
Cockpit/portal/WA diario:       ~$3.00
TOTAL:                          ~$10.20/mes
```
