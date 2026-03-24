# B-ORG-BRAIN: Cerebro LLM para el Organismo — De termómetros a inteligencia real

**Fecha:** 23 marzo 2026 (actualizado con modelos correctos)
**Prioridad:** MÁXIMA — Sin esto el organismo no está vivo
**Esfuerzo:** 3 briefings ejecutados con Claude Code
**Coste operativo:** ~$1.30/semana (~$5.80/mes total sistema con modelos correctos)

---

## DIAGNÓSTICO

El organismo tiene 12 agentes autónomos que son termómetros: ejecutan SQL, detectan un número, emiten un texto template al bus. No razonan. No proponen acciones concretas contextualizadas. No cruzan información entre sí. No aprenden.

## PRINCIPIO DE DISEÑO

```
SENSOR (código puro)  →  CEREBRO (LLM)  →  SEÑAL AL BUS (código puro)
   Rápido, gratis          Razona             Estructurada, accionable
   Detecta datos           Interpreta          Con acciones priorizadas
   Sin coste LLM           Modelo adecuado     Determinista
```

## POLÍTICA DE MODELOS — El modelo adecuado a la tarea

NO se usa un solo modelo para todo. Cada tipo de tarea cognitiva tiene su modelo:

| Tipo de tarea | Modelo | Env var | $/call | Razón |
|---|---|---|---|---|
| **Razonamiento de negocio** (AF1-AF7, Gestor) | `openai/gpt-4o` | `BRAIN_MODEL` | ~$0.02 | Mejor español peninsular, razonamiento práctico |
| **Razonamiento complejo** (Ejecutor, Convergencia) | `anthropic/claude-sonnet-4.6` | `REASONING_MODEL` | ~$0.05 | Resolución conflictos cross-AF, patrones sistémicos |
| **Álgebra cognitiva** (Séquito 24 asesores) | `anthropic/claude-sonnet-4.6` | `SEQUITO_MODEL` | ~$0.05 | Framework ACD: 3L×7F×18INT×15P×12R |
| **Síntesis** (Séquito integrador) | `anthropic/claude-sonnet-4.6` | `SEQUITO_SYNTH_MODEL` | ~$0.05 | Integrar perspectivas divergentes |
| **Interfaz conversacional** (cockpit, portal, WA) | `openai/gpt-4o` | `CHAT_MODEL` | ~$0.02 | Tool calling + español coloquial + velocidad |
| **Estrategia/contenido** (voz, perfiles) | `openai/gpt-4o` | `STRATEGY_MODEL` | ~$0.02 | Creatividad marketing en español |
| **Búsqueda mercado** (G3) | Perplexity `llama-3.1-sonar` | `PERPLEXITY_API_KEY` | ~$0.01 | Ya correcto |

Criterio: **GPT-4o** para todo lo que requiere español peninsular natural + herramientas. **Claude Sonnet 4.6** para todo lo que requiere razonamiento analítico profundo y seguir frameworks formales complejos.

## IMPLEMENTACIÓN

### PARTE 1: Motor de razonamiento con 2 niveles

Crear `src/pilates/cerebro_organismo.py`:

```python
"""Cerebro del Organismo — Capa de razonamiento LLM para agentes autónomos.

Dos niveles de razonamiento:
  NIVEL 1 (gpt-4o): AF1-AF7 + Gestor — razonamiento de negocio en español
  NIVEL 2 (claude-sonnet-4.6): Ejecutor + Convergencia — razonamiento complejo cross-AF

El sensor no cambia. El bus no cambia. Se AÑADE cerebro entre detección y emisión.
"""
from __future__ import annotations

import json
import os
import structlog
import httpx
from datetime import date

log = structlog.get_logger()

TENANT = "authentic_pilates"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Nivel 1: Razonamiento de negocio (español peninsular, acciones concretas)
BRAIN_MODEL = os.getenv("BRAIN_MODEL", "openai/gpt-4o")

# Nivel 2: Razonamiento complejo (conflictos cross-AF, patrones sistémicos)
REASONING_MODEL = os.getenv("REASONING_MODEL", "anthropic/claude-sonnet-4.6")


async def _contexto_negocio() -> str:
    """Contexto actualizado del negocio para inyectar en cada razonamiento."""
    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'",
            TENANT) or 0

        grupos = await conn.fetch("""
            SELECT g.nombre, g.dias_semana, g.capacidad_max,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.grupo_id=g.id AND c.estado='activo') as ocupadas
            FROM om_grupos g WHERE g.tenant_id=$1 AND g.estado='activo'
        """, TENANT)

        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT)

        ultimo_acd = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        señales_recientes = await conn.fetch("""
            SELECT tipo, origen, payload, prioridad, created_at
            FROM om_bus_senales WHERE tenant_id=$1
            ORDER BY created_at DESC LIMIT 20
        """, TENANT)

    grupos_str = "\n".join(
        f"  - {g['nombre']}: {g['ocupadas']}/{g['capacidad_max']} plazas, días: {g['dias_semana']}"
        for g in grupos
    )

    señales_str = "\n".join(
        f"  - [{s['origen']}] {s['tipo']}: {json.dumps(s['payload'], ensure_ascii=False)[:120]}"
        for s in señales_recientes[:10]
    )

    acd_str = "Sin diagnóstico"
    if ultimo_acd:
        acd_str = f"Estado: {ultimo_acd['estado_pre']}, Lentes: {ultimo_acd['lentes_pre']}"

    return f"""AUTHENTIC PILATES — Estudio de Pilates en Albelda de Iregua (La Rioja)
Dueño: Jesús. Instructor único. Método EEDAP (Pilates auténtico).
~{clientes} clientes activos. Pueblo de ~4.000 hab, cabeza de comarca, cerca de Logroño.
Ingresos este mes: {float(ingresos):.0f}€.
Diagnóstico ACD: {acd_str}

GRUPOS ACTIVOS:
{grupos_str}

SEÑALES RECIENTES EN EL BUS:
{señales_str}

Fecha: {date.today()}"""


async def _call_llm(model: str, system_prompt: str, user_prompt: str,
                     max_tokens: int = 1500, temperature: float = 0.4) -> str:
    """Llamada genérica a LLM via OpenRouter."""
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://motor-semantico-omni.fly.dev",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def _parse_json(raw: str) -> dict:
    """Parsea JSON tolerante a markdown fences."""
    clean = raw.strip()
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1] if "\n" in clean else clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    return json.loads(clean.strip())


async def razonar(
    agente: str,
    funcion: str,
    datos_detectados: dict,
    instruccion_especifica: str,
    nivel: int = 1,
) -> dict:
    """Razonamiento LLM para agentes del organismo.

    Args:
        agente: Nombre del agente (AF1, AF3, EJECUTOR, etc.)
        funcion: Función L0.7 (F1 Conservación, F3 Depuración, etc.)
        datos_detectados: Output del sensor (código puro)
        instruccion_especifica: Qué debe razonar este agente
        nivel: 1 = gpt-4o (negocio), 2 = claude-sonnet (complejo)

    Returns:
        {
            "interpretacion": str,
            "acciones": [{"accion": str, "prioridad": int, "impacto": str,
                          "esfuerzo": str, "cliente_id": str|None, "grupo_id": str|None}],
            "patron_detectado": str | None,
            "alerta_critica": str | None,
        }
    """
    if not OPENROUTER_API_KEY:
        return {
            "interpretacion": "Sin modelo LLM configurado. Datos crudos.",
            "acciones": [{"accion": json.dumps(datos_detectados, ensure_ascii=False)[:200],
                          "prioridad": 3, "impacto": "desconocido", "esfuerzo": "desconocido"}],
            "patron_detectado": None,
            "alerta_critica": None,
        }

    model = BRAIN_MODEL if nivel == 1 else REASONING_MODEL
    contexto = await _contexto_negocio()

    system_prompt = f"""Eres el cerebro del agente {agente} ({funcion}) del organismo cognitivo de Authentic Pilates.

Tu trabajo: interpretar datos operativos y proponer acciones CONCRETAS, PRIORIZADAS y ACCIONABLES.

REGLAS:
1. No repitas los datos — interprétalos. ¿QUÉ SIGNIFICAN? ¿POR QUÉ pasa esto?
2. Cada acción debe ser ejecutable por Jesús (el dueño) en <5 minutos.
3. Prioriza por impacto en ingresos y retención.
4. Si ves un patrón que cruza varios datos, señálalo.
5. Si algo es urgente (riesgo de perder cliente o dinero HOY), marca alerta_critica.
6. Tono: directo, sin formalismos. Como hablar con un socio inteligente.
7. Las acciones deben ser ESPECÍFICAS: no "contactar al cliente" sino "enviar WA a María preguntando si la espalda le ha mejorado desde la última sesión".

CONTEXTO DEL NEGOCIO:
{contexto}

Responde SOLO en JSON válido con esta estructura:
{{
    "interpretacion": "... (2-4 frases: qué significan los datos, por qué pasa)",
    "acciones": [
        {{
            "accion": "... (acción concreta y específica)",
            "prioridad": 1-5,
            "impacto": "... (qué efecto tendrá si se hace)",
            "esfuerzo": "bajo|medio|alto",
            "cliente_id": "uuid o null",
            "grupo_id": "uuid o null"
        }}
    ],
    "patron_detectado": "... o null",
    "alerta_critica": "... o null"
}}"""

    user_prompt = f"""{instruccion_especifica}

DATOS DETECTADOS POR LOS SENSORES:
{json.dumps(datos_detectados, ensure_ascii=False, indent=2)}"""

    try:
        raw = await _call_llm(model, system_prompt, user_prompt)
        resultado = _parse_json(raw)
    except json.JSONDecodeError:
        log.warning("cerebro_parse_error", agente=agente, model=model)
        return {"interpretacion": raw[:500] if 'raw' in dir() else "Parse error",
                "acciones": [], "patron_detectado": None, "alerta_critica": None}
    except Exception as e:
        log.error("cerebro_llm_error", agente=agente, model=model, error=str(e))
        return {"interpretacion": f"Error: {str(e)[:100]}",
                "acciones": [], "patron_detectado": None, "alerta_critica": None}

    log.info("cerebro_ok", agente=agente, model=model.split("/")[-1],
             acciones=len(resultado.get("acciones", [])),
             critica=resultado.get("alerta_critica") is not None)

    return resultado
```

### PARTE 2: Integrar cerebro en cada AF

Patrón idéntico para los 7 AF. Ejemplo AF1:

```python
async def ejecutar_af1() -> dict:
    # ... sensores como ahora (código puro, sin cambios) ...
    fantasmas = await _detectar_fantasmas()
    engagement = await _detectar_engagement_cayendo()
    deuda = await _detectar_deuda_silenciosa()

    datos_sensor = {
        "fantasmas": fantasmas,
        "engagement_cayendo": engagement,
        "deuda_silenciosa": deuda,
    }

    # === CEREBRO (NIVEL 1: gpt-4o — razonamiento de negocio en español) ===
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="AF1",
        funcion="F1 Conservación",
        datos_detectados=datos_sensor,
        instruccion_especifica=INSTRUCCION_AF1,
        nivel=1,  # gpt-4o
    )

    # Emitir PRESCRIPCIONES razonadas al bus
    from src.pilates.bus import emitir
    alertas = 0
    for accion in razonamiento.get("acciones", []):
        await emitir("PRESCRIPCION", "AF1", {
            "funcion": "F1",
            "accion": accion["accion"],
            "prioridad": accion["prioridad"],
            "impacto": accion["impacto"],
            "esfuerzo": accion["esfuerzo"],
            "cliente_id": accion.get("cliente_id"),
            "grupo_id": accion.get("grupo_id"),
            "interpretacion": razonamiento["interpretacion"],
        }, prioridad=accion["prioridad"])
        alertas += 1

    if razonamiento.get("alerta_critica"):
        await emitir("ALERTA", "AF1", {
            "funcion": "F1",
            "alerta_critica": razonamiento["alerta_critica"],
            "urgente": True,
        }, prioridad=1)

    return {**datos_sensor, "razonamiento": razonamiento, "alertas_emitidas": alertas}
```

Aplicar el MISMO patrón a AF2, AF3, AF4, AF6, AF7. Todos `nivel=1` (gpt-4o).

### PARTE 3: Ejecutor y Convergencia con nivel 2 (Claude Sonnet 4.6)

El Ejecutor y la Convergencia son los ÚNICOS que usan `nivel=2`:

```python
# ejecutor_convergencia.py — actualizar ejecutar_prescripciones():

async def ejecutar_prescripciones() -> dict:
    prescripciones = await leer_pendientes(tipo="PRESCRIPCION", limite=30)

    # CEREBRO NIVEL 2: Claude Sonnet 4.6 — resuelve conflictos cross-AF
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="EJECUTOR",
        funcion="Orquestación cross-AF",
        datos_detectados={"prescripciones": [_serializar(p) for p in prescripciones]},
        instruccion_especifica=INSTRUCCION_EJECUTOR,
        nivel=2,  # claude-sonnet-4.6
    )
    # ... emitir plan unificado ...


async def detectar_convergencia() -> dict:
    convergencias = await _detectar_convergencias_raw()

    # CEREBRO NIVEL 2: Claude Sonnet 4.6 — razonamiento sistémico
    from src.pilates.cerebro_organismo import razonar
    razonamiento = await razonar(
        agente="CONVERGENCIA",
        funcion="Detección de patrones sistémicos",
        datos_detectados={"convergencias": convergencias},
        instruccion_especifica=INSTRUCCION_CONVERGENCIA,
        nivel=2,  # claude-sonnet-4.6
    )
    # ... emitir insights ...
```

### PARTE 4: Instrucciones específicas por agente

```python
# Constantes al inicio de cada archivo de AF:

INSTRUCCION_AF1 = """Analiza los clientes en riesgo de pérdida.
Para cada cliente fantasma, deduce POR QUÉ puede haber dejado de venir
(lesión mejorada, vacaciones, insatisfacción, vergüenza, problemas de dinero)
y propón una acción DIFERENTE para cada caso.
Para engagement cayendo, identifica si es tendencia o evento puntual.
Para deuda silenciosa, evalúa si el cliente vale la pena retener o si
es mejor dejarlo ir.
Prioriza: ¿a quién salvar primero y cómo?"""

INSTRUCCION_AF2 = """Analiza los leads y la conversión.
Para cada lead perdido, evalúa si merece rescate basándote en su intención original.
Para conversión baja, diagnostica si el problema es el canal, el mensaje, el timing
o el precio. Propón cambios concretos al proceso de cierre.
Respeta los VETOs de AF3: no propongas captar para horarios vetados."""

INSTRUCCION_AF3 = """Analiza grupos y contratos ineficientes.
Para grupos infrautilizados: ¿cuáles fusionar entre sí? ¿cuáles cerrar?
¿cuáles cambiar de horario? Razona compatibilidad de alumnos y horarios.
Para zombis: ¿llamar o dar de baja? Calcula impacto en ingresos de cada decisión.
Di claramente QUÉ CORTAR y por qué."""

INSTRUCCION_AF4 = """Analiza la carga semanal.
¿Qué sesiones mover de días sobrecargados a vacíos?
¿Qué clientes podrían cambiar de horario sin impacto?
Si ratio individual es alto, propón cómo migrar clientes de individual a grupo
(qué grupo, cuándo, cómo comunicarlo). Calcula impacto en facturación."""

INSTRUCCION_AF6 = """Analiza tensiones del entorno.
¿Qué está cambiando en el mercado que afecte al negocio?
¿Hay oportunidades que no se están aprovechando? ¿Competidores nuevos?
Si no hay tensiones registradas, eso ES una señal: significa que no estás
monitorizando el entorno. Señala qué debería estar vigilando y no lo está."""

INSTRUCCION_AF7 = """Analiza la capacidad de replicar el negocio.
¿Qué proceso documentar PRIMERO para máximo impacto?
¿Qué principio del ADN es más urgente definir con contra-ejemplos?
Si tuvieras que formar a un instructor sustituto mañana,
¿qué le faltaría saber? Prioriza por riesgo operativo."""

INSTRUCCION_EJECUTOR = """Tienes prescripciones de múltiples agentes.
Prioriza y resuelve conflictos:
- ¿AF3 dice cerrar un grupo pero AF2 dice captar para él?
- ¿AF1 dice retener un cliente pero AF3 dice que es zombi?
Genera un plan de acción UNIFICADO para la semana con máximo 5 acciones
priorizadas. Sin contradicciones. Cada acción debe indicar qué AF la originó."""

INSTRUCCION_CONVERGENCIA = """Múltiples agentes señalan al mismo cliente/grupo.
¿Qué SIGNIFICA esta convergencia? ¿Es una oportunidad oculta o un problema
sistémico? Genera un insight que ningún agente individual podría haber visto.
Si Carlos aparece como fantasma (AF1) Y como zombi (AF3), eso no son 2
problemas — es 1 decisión: ¿retener con esfuerzo o soltar limpiamente?"""

INSTRUCCION_GESTOR = """Resume la actividad de la semana del organismo.
¿Qué aprendió el sistema? ¿Qué acciones se propusieron? ¿Hay patrones
que emergen semana tras semana? Genera un briefing narrativo en español
coloquial para Jesús — como un socio inteligente que le cuenta
qué ha pasado esta semana en el negocio y qué debería hacer."""
```

---

## TESTS

### TEST 1: cerebro_organismo.razonar() nivel 1 (gpt-4o) devuelve JSON válido
```python
result = await razonar("AF1", "F1", {"fantasmas": [{"nombre": "María"}]},
                        "Analiza...", nivel=1)
assert "interpretacion" in result
assert "acciones" in result
assert isinstance(result["acciones"], list)
```

### TEST 2: cerebro_organismo.razonar() nivel 2 (claude-sonnet) devuelve JSON válido
```python
result = await razonar("EJECUTOR", "Orquestación", {"prescripciones": [...]},
                        "Prioriza...", nivel=2)
assert "interpretacion" in result
```

### TEST 3: AF1 con cerebro emite prescripciones razonadas
```python
result = await ejecutar_af1()
assert "razonamiento" in result
for a in result["razonamiento"]["acciones"]:
    assert len(a["accion"]) > 50  # No vale "contactar cliente"
```

### TEST 4: Ejecutor resuelve conflictos cross-AF
```python
result = await ejecutar_prescripciones()
# Debe producir plan unificado sin contradicciones
```

### TEST 5: Sin OPENROUTER_API_KEY, fallback básico sin crash
```python
# Quitar env var → funciona como ahora (termómetros) sin romper nada
```

---

## PLAN DE EJECUCIÓN

| Briefing | Qué | Modelo |
|---|---|---|
| B-ORG-BRAIN-01 | cerebro_organismo.py + integrar en AF1+AF3 | gpt-4o (nivel 1) |
| B-ORG-BRAIN-02 | Integrar en AF2+AF4+AF6+AF7 | gpt-4o (nivel 1) |
| B-ORG-BRAIN-03 | Cerebro Ejecutor+Convergencia+Gestor | claude-sonnet-4.6 (nivel 2) + gpt-4o (Gestor) |

3 briefings, ejecutables en 1 sesión de Claude Code.
