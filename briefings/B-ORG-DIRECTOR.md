# B-ORG-DIRECTOR: Agente Opus — Director de Orquesta del organismo

**Fecha:** 23 marzo 2026 (ACTUALIZADO: lee de manual + formato D_híbrido)
**Prioridad:** MÁXIMA — esto es lo que convierte prompts genéricos en inteligencia real
**Modelo:** `anthropic/claude-opus-4.6` (el único agente Opus de todo el sistema)
**Frecuencia:** 1x/semana (después de G4, reemplaza al Recompilador Sonnet)
**Dependencia:** B-ORG-PIZARRA + B-ORG-UNIFY ejecutados
**Manual:** `docs/operativo/MANUAL_DIRECTOR_OPUS.md` (ya creado en repo)

---

## DOS CAMBIOS RESPECTO A VERSIÓN ANTERIOR

### CAMBIO 1: Opus lee de un archivo, no del system prompt

ANTES: Todo el álgebra (18 INT, 15 P, 12 R, IC1-IC7, reglas compilador, perfiles, recetas) estaba HARDCODEADO en el system prompt de Opus. Problema: límite de tokens, no se puede actualizar sin cambiar código.

DESPUÉS: El system prompt de Opus es CORTO (identidad + instrucciones de output). Todo el conocimiento está en `MANUAL_DIRECTOR_OPUS.md` que se lee de DB/filesystem al inicio. Opus lo recibe como user message, lo comprende, y LUEGO diseña.

Ventajas:
- Sin límite práctico de tokens (el manual puede tener 5,000+ líneas)
- Se actualiza sin tocar código (Jesús edita el .md, Opus lo lee)
- Opus lee, COMPRENDE, y luego aplica — no recita de memoria
- El manual está en el repo, versionado, con CR1

### CAMBIO 2: Prompts en formato D_híbrido (estructura código + contenido natural)

ANTES: Los prompts que Opus escribía para cada agente eran texto plano.

DESPUÉS: Los prompts usan el formato D_híbrido (P35) validado empíricamente:
- **Estructura en JSON/Python** → fuerza secuencia, hace explícitas dependencias, -35% tokens
- **Contenido en lenguaje natural** → captura matices, ambigüedad productiva, provocaciones

Validación empírica:
```
Imperativos-only:  61% cobertura, novedad SUPRIMIDA
Questions-only:    alta cobertura, 117 NUEVO, mucho ruido
D_híbrido (mixed): 91% cobertura, 83 NUEVO, 14 ruido, -35% tokens → ÓPTIMO
```

## ARCHIVO A CREAR

`src/pilates/director_opus.py`

## CÓDIGO

```python
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

Modelo: anthropic/claude-opus-4.6 via OpenRouter
Coste: ~$0.40/ejecución, ~$1.60/mes
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
import time
from pathlib import Path

from src.db.client import get_pool

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPUS_MODEL = "anthropic/claude-opus-4.6"

# Ruta al manual en el repo (fallback si no está en DB)
MANUAL_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "operativo" / "MANUAL_DIRECTOR_OPUS.md"


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
            SELECT resultado_clusters, señales_emitidas FROM om_enjambre_diagnosticos
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

    estado_str = f"""ESTADO DEL SISTEMA ESTA SEMANA:

DIAGNÓSTICO tcf/ (código puro + LLM perceptor):
{json.dumps(diag_payload, ensure_ascii=False, indent=2, default=str)[:3000]}

PIZARRA DEL ORGANISMO (lo que cada agente hizo/piensa):
{json.dumps(pizarra, ensure_ascii=False, indent=2, default=str)[:2500]}

ENJAMBRE (13 clusters — confirmaciones/contradicciones/enriquecimientos):
{json.dumps(dict(enjambre) if enjambre else {}, ensure_ascii=False, indent=2, default=str)[:1500]}

GUARDIÁN DE SESGOS:
{json.dumps(dict(guardian) if guardian else {"sin_guardian": True}, ensure_ascii=False, indent=2, default=str)[:1000]}

CONFIGS ACTUALES:
{json.dumps([dict(c) for c in configs_actuales], ensure_ascii=False, indent=2, default=str)[:1500]}

PREGUNTAS HUÉRFANAS (nadie las hace pero deberían hacerse):
{json.dumps([dict(h) for h in huerfanas], ensure_ascii=False, indent=2, default=str)[:800]}

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
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://motor-semantico-omni.fly.dev",
                },
                json={
                    "model": OPUS_MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_DIRECTOR},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 6000,
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
        log.error("director_opus_error", error=str(e))
        return {"error": str(e)[:300]}

    # 4. PERSISTIR CONFIGS
    configs_aplicadas = 0
    async with pool.acquire() as conn:
        for config in resultado.get("configs", []):
            agente = config["agente"]

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
            "organismo_director", "🎼",
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
```

## MIGRACIÓN SQL (opcional — para poder actualizar manual sin deploy)

```sql
-- En 024_pizarra.sql (añadir)

CREATE TABLE IF NOT EXISTS om_director_manual (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL DEFAULT 'authentic_pilates',
    contenido TEXT NOT NULL,
    version INT DEFAULT 1,
    activo BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(tenant_id, activo)
);
```

Si existe en DB, se usa la DB. Si no, se lee del filesystem. Así:
- En desarrollo: editas el .md en el repo
- En producción: puedes actualizar via DB sin redeploy

## EL FLUJO COMPLETO

```
1. Cron semanal dispara G4
2. diagnosticador → tcf/ completo (LLM percibe, código razona)
3. enjambre → 13 clusters evalúan contra realidad
4. guardián → detecta sesgos
5. compositor → integra código + clusters + guardián

6. DIRECTOR OPUS:
   a. Lee MANUAL_DIRECTOR_OPUS.md (álgebra completa: §1-§9)
   b. Lee estado del sistema (diagnóstico + pizarra + enjambre + guardián)
   c. COMPRENDE ambos
   d. Para cada agente que necesita cambio:
      - Selecciona INT×P×R (verificando IC2-IC7, aplicando R1-R8)
      - Escribe prompt D_híbrido:
        · Imperativo en JSON (secuencia EXTRAER→FRONTERA forzada)
        · Preguntas en lenguaje natural (cálculo semántico)
        · Provocación en lenguaje natural (romper marco)
        · Razonamiento en JSON (inferencia con validación cruzada)
   e. Persiste configs en om_config_agentes (aprobada_por='opus')

7. Próxima ejecución de AF1-AF7:
   cerebro_organismo.razonar() → carga config dinámica → usa prompt Opus
```

## EJEMPLO DE OUTPUT DEL DIRECTOR

Para AF3 en estado "genio mortal":

```json
{
    "agente": "AF3",
    "justificacion": "Estado genio_mortal: S↑Se↑C↓. AF3 necesita depurar CON sentido, no mecánicamente. Activar INT-18 (¿la urgencia de cerrar es real?) + INT-09 (¿qué no se está nombrando?) con P05 (primeros principios) + R03 (abducción). La depuración debe ser cuestionadora, no operativa.",
    "prompt_d_hibrido": {
        "imperativo": [
            {"paso": "EXTRAER", "instruccion": "De los 16 grupos programados, identifica los 3 con menor ocupación sostenida (>4 semanas). No uses solo el número — lee la pizarra de AF1 para ver si algún cliente fantasma está en estos grupos."},
            {"paso": "CRUZAR", "instruccion": "Para cada grupo, cruza ocupación con: (1) ingresos que genera, (2) tipo de cliente que asiste, (3) historial — ¿siempre fue bajo o cayó recientemente? (4) pizarra AF4 — ¿hay desequilibrio horario que explique la baja?"},
            {"paso": "LENTES", "instruccion": "¿Cerrar este grupo es operativo (S: ahorra tiempo), tiene sentido (Se: es coherente con la identidad del estudio), o afecta continuidad (C: pierde un tipo de cliente que no recuperarás)?"},
            {"paso": "INTEGRAR", "instruccion": "De los 3, ¿cuál tiene mayor coste OCULTO? No solo euros — tu energía, tu motivación, la señal que envías a los demás clientes manteniendo algo vacío."},
            {"paso": "ABSTRAER", "instruccion": "¿Hay un PRINCIPIO detrás de por qué mantienes estos grupos? ¿Es lealtad real, miedo a la conversación difícil, o inercia pura? El principio te dice si el problema es de F3 o de F5."},
            {"paso": "FRONTERA", "instruccion": "Define la línea: ¿por debajo de qué ocupación un grupo DEBE cerrarse? ¿Hay excepciones legítimas? Escribe la regla para que un sustituto pudiera aplicarla."}
        ],
        "preguntas": [
            {"int": "INT-18", "pregunta": "¿La urgencia de cerrar estos grupos es REAL o es presión que te estás poniendo tú? ¿Qué pasaría si no hicieras nada durante 4 semanas más?"},
            {"int": "INT-09", "pregunta": "¿Cómo DESCRIBES estos grupos cuando hablas de ellos? ¿'Los grupos vacíos' o 'los grupos con potencial'? La palabra que usas revela cómo los percibes."},
            {"int": "INT-08", "pregunta": "¿Hay algún cliente en estos grupos que sigue viniendo por lealtad a TI, no por el horario? ¿Cerrar el grupo es perder un cliente o liberar a alguien que ya quería cambiar?"},
            {"int": "INT-03", "pregunta": "¿La estructura de 16 grupos refleja la REALIDAD actual (90 clientes) o la AMBICIÓN original (150 clientes)? ¿El mapa sigue siendo el territorio?"}
        ],
        "provocacion": "¿Y si mantener 15 grupos con 1-2 alumnos no es generosidad — es miedo a DECIDIR? ¿Y si cerrar 9 grupos libera la energía que necesitas para hacer los 7 restantes extraordinarios?",
        "razonamiento": {
            "R03_abduccion": "Para cada grupo infrautilizado, genera la MEJOR EXPLICACIÓN de por qué está así. No asumas 'faltan clientes'. Puede ser: horario incompatible con la vida en Albelda (15 min a Logroño, ¿a qué hora vuelven del trabajo?), precio inadecuado para ese segmento, o que el grupo perdió su razón de ser cuando cambió la composición.",
            "R08_dialectico": "Confronta 'cerrar = abandonar clientes' con 'mantener = desperdiciar tu recurso más escaso (tiempo de instructor único)'. ¿Hay una tercera vía? ¿Fusionar? ¿Cambiar horario? ¿Convertir en semi-individual?",
            "validacion_cruzada": "Solo propón cerrar un grupo si R03 (la explicación de por qué está vacío) Y R08 (la confrontación cierre vs mantenimiento) convergen en la misma conclusión. Si divergen, señálalo como conflicto para el Ejecutor."
        }
    }
}
```

**Compara eso con lo que el Recompilador Sonnet produce:**
```json
{"agente": "AF3", "INT_activas": [{"id": "INT-18", "preguntas": ["¿La urgencia es real?"]}]}
```

La diferencia es abismal.

## TESTS

### T1: Opus lee el manual antes de actuar
```python
result = await dirigir_orquesta()
assert result["manual_leido"] > 1000  # El manual es largo
```

### T2: Prompts en formato D_híbrido
```python
for config in result["resultado_completo"]["configs"]:
    prompt = config["prompt_d_hibrido"]
    assert isinstance(prompt["imperativo"], list)  # JSON, no texto plano
    assert len(prompt["imperativo"]) == 6  # 6 pasos EXTRAER→FRONTERA
    assert isinstance(prompt["preguntas"], list)
    assert isinstance(prompt["razonamiento"], dict)
    assert "provocacion" in prompt
```

### T3: Preguntas son ESPECÍFICAS al negocio (no genéricas)
```python
for config in result["resultado_completo"]["configs"]:
    todas_preguntas = json.dumps(config["prompt_d_hibrido"]["preguntas"])
    assert any(word in todas_preguntas.lower() for word in
               ["pilates", "grupo", "cliente", "jesús", "albelda", "instructor"])
```

### T4: IC verificadas
```python
for config in result["resultado_completo"]["configs"]:
    v = config.get("verificaciones_ic", {})
    assert "ic3" in v and "ic5" in v
```

### T5: Manual actualizable sin código
```python
# Cambiar manual en DB
pool = await get_pool()
async with pool.acquire() as conn:
    await conn.execute("""
        INSERT INTO om_director_manual (tenant_id, contenido, version, activo)
        VALUES ($1, 'manual actualizado', 2, TRUE)
        ON CONFLICT (tenant_id, activo) DO UPDATE SET contenido=EXCLUDED.contenido, version=EXCLUDED.version
    """, TENANT)

result = await dirigir_orquesta()
# Debe usar el manual de DB, no el filesystem
```
