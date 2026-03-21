# B-PIL-20e: Integración Cockpit + Cron + Módulo Voz Visual

**Fecha:** 2026-03-22
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-20a + 20b + 20c + 20d desplegados. Cockpit operativo (B-PIL-19).
**Coste:** ~$0 (no añade LLM calls — usa datos existentes)

---

## CONTEXTO

El Bloque Voz está completo a nivel de backend:
- 20a: tablas + identidad + seeds
- 20b: Motor Tridimensional → estrategia + calendario semanal
- 20c: Arquitecto de Presencia → perfiles por canal
- 20d: 5 Ciclos + ISP + telemetría + sección briefing

Lo que falta es la **capa de interacción** — cómo Jesús usa todo esto en el día a día:

1. **Cockpit:** Que Jesús pueda decir "¿cuál es mi estrategia?" o "prepárame los posts de esta semana" y el cockpit responda con datos reales
2. **Cron:** Que el sistema ejecute los ciclos automáticamente (ESCUCHAR diario, estrategia semanal)
3. **Módulo Voz visual:** Que el módulo "voz" del cockpit muestre datos estratégicos, no solo propuestas pendientes

---

## FASE E1: Tools de Voz en el cockpit

**Archivo:** `src/pilates/cockpit.py` — EDITAR

### E1.1: Añadir tools Voz al array TOOLS_COCKPIT

Buscar el cierre del array `TOOLS_COCKPIT` (el `]` final después de la tool `ver_pagos_cliente`) y ANTES de ese `]`, añadir:

```python
    # --- VOZ: ESTRATEGIA ---
    {
        "type": "function",
        "function": {
            "name": "voz_estrategia",
            "description": "Ver la estrategia de comunicación activa: foco, narrativa, canales prioridad, calendario semanal con contenido propuesto.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: SEÑALES ---
    {
        "type": "function",
        "function": {
            "name": "voz_senales",
            "description": "Ver señales pendientes del negocio: ocupación baja, clientes inactivos, oportunidades, lluvia prevista, etc.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: ISP (salud de presencia digital) ---
    {
        "type": "function",
        "function": {
            "name": "voz_isp",
            "description": "Ver el Índice de Salud de Presencia de cada canal: qué está bien configurado y qué falta.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: RECALCULAR ESTRATEGIA ---
    {
        "type": "function",
        "function": {
            "name": "voz_recalcular",
            "description": "Recalcular la estrategia semanal de comunicación completa (IRC x Matriz x PCA). Genera nuevo calendario. ~5 seg.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    # --- VOZ: GENERAR PERFILES ---
    {
        "type": "function",
        "function": {
            "name": "voz_generar_perfiles",
            "description": "Generar configuración optimizada de todos los perfiles digitales (WA, Google, IG, FB). ~20 seg.",
            "parameters": {
                "type": "object",
                "properties": {
                    "canal": {"type": "string", "description": "Canal específico (whatsapp/google_business/instagram/facebook). Si vacío, genera todos."}
                }
            }
        }
    },
    # --- VOZ: EJECUTAR CICLO ---
    {
        "type": "function",
        "function": {
            "name": "voz_ciclo",
            "description": "Ejecutar ciclo completo: escuchar señales + priorizar + recalcular IRC + ISP. ~2 seg.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
```

### E1.2: Implementar dispatch de tools Voz

Buscar el dict `TOOL_DISPATCH = {` y ANTES del cierre `}`, añadir:

```python
    "voz_estrategia": _op_voz_estrategia,
    "voz_senales": _op_voz_senales,
    "voz_isp": _op_voz_isp,
    "voz_recalcular": _op_voz_recalcular,
    "voz_generar_perfiles": _op_voz_generar_perfiles,
    "voz_ciclo": _op_voz_ciclo,
```

### E1.3: Implementar funciones de dispatch

Añadir ANTES del dict `TOOL_DISPATCH`:

```python
# ============================================================
# TOOLS VOZ — dispatch functions (B-PIL-20e)
# ============================================================

async def _op_voz_estrategia(args: dict) -> dict:
    """Devuelve estrategia activa + calendario."""
    from src.pilates.voz_estrategia import obtener_estrategia_activa
    result = await obtener_estrategia_activa()
    if "error" in result:
        return result
    # Simplificar para el LLM del cockpit
    est = result.get("estrategia", {})
    cal = result.get("calendario", [])
    return {
        "foco": est.get("foco_principal", "sin_estrategia"),
        "narrativa": est.get("narrativa", ""),
        "canales": est.get("canales_prioridad", []),
        "evitar": est.get("evitar", []),
        "calendario": [
            {
                "canal": c["canal"],
                "tipo": c["tipo"],
                "titulo": c["titulo"],
                "dia": c["dia"],
                "estado": c["estado"],
            }
            for c in cal[:8]
        ],
        "total_items": len(cal),
    }


async def _op_voz_senales(args: dict) -> dict:
    """Devuelve señales pendientes priorizadas."""
    from src.pilates.voz_ciclos import priorizar
    result = await priorizar()
    return {
        "total": result.get("total", 0),
        "criticas": result.get("criticas", 0),
        "altas": result.get("altas", 0),
        "senales": [
            {"tipo": s["tipo"], "urgencia": s["urgencia"], "resumen": s["resumen"]}
            for s in result.get("senales", [])[:10]
        ],
    }


async def _op_voz_isp(args: dict) -> dict:
    """Devuelve ISP automático."""
    from src.pilates.voz_ciclos import calcular_isp_automatico
    return await calcular_isp_automatico()


async def _op_voz_recalcular(args: dict) -> dict:
    """Recalcula estrategia semanal."""
    from src.pilates.voz_estrategia import calcular_estrategia
    return await calcular_estrategia()


async def _op_voz_generar_perfiles(args: dict) -> dict:
    """Genera perfiles de canales."""
    canal = args.get("canal", "")
    if canal:
        from src.pilates.voz_arquitecto import generar_perfil
        return await generar_perfil(canal)
    else:
        from src.pilates.voz_arquitecto import generar_todos_los_perfiles
        return await generar_todos_los_perfiles()


async def _op_voz_ciclo(args: dict) -> dict:
    """Ejecuta ciclo completo."""
    from src.pilates.voz_ciclos import ejecutar_ciclo_completo
    return await ejecutar_ciclo_completo()
```

### E1.4: Añadir Voz al SYSTEM_COCKPIT

Buscar la sección `OPERACIONES:` en `SYSTEM_COCKPIT` y DESPUÉS de la línea `- Ver detalles de clientes, grupos, pagos`, añadir:

```
- Ver estrategia de comunicación y calendario de contenido semanal
- Ver señales pendientes (ocupación, inactivos, oportunidades, clima)
- Ver salud de presencia digital (ISP por canal)
- Recalcular estrategia de comunicación (~5 seg)
- Generar perfiles optimizados para canales digitales (~20 seg)
- Ejecutar ciclo completo de escucha y análisis (~2 seg)
```

Y añadir esta regla al final de `REGLAS OPERATIVAS:`:

```
8. Para consultas de Voz ("¿cuál es mi estrategia?", "¿cómo va mi presencia?", "prepárame posts"), usa las herramientas voz_*. Tras consultar, monta el módulo "voz".
```

### E1.5: Actualizar módulo Voz en MODULOS

Buscar la línea `"voz":` en el dict MODULOS y cambiar el endpoint:

```python
    "voz":              {"nombre": "Voz estratégica",      "icono": "📢", "endpoint": "/voz/estrategia"},
```

---

## FASE E2: Cron — Tareas programadas

**Decisión técnica:** Usar `asyncio` background tasks en el lifespan de FastAPI. Sin dependencias externas (ni APScheduler ni celery). Un loop infinito que duerme y ejecuta. Si fly.io reinicia el contenedor, el loop se reinicia con él.

**Archivo:** Crear `src/pilates/cron.py`

```python
"""Cron del Exocortex — Tareas programadas.

Ejecuta tareas periódicas sin dependencias externas.
Se inicia en el lifespan de FastAPI como background task.

Tareas:
- Diaria (06:00 Madrid): escuchar señales
- Semanal (lunes 07:00): calcular estrategia + ciclo completo
"""
from __future__ import annotations

import asyncio
import structlog
from datetime import datetime, time, timedelta

log = structlog.get_logger()

# Zona horaria: Madrid = UTC+1 (invierno) / UTC+2 (verano)
# Simplificación: usamos UTC+1 fijo. Suficiente para un cron de SMB.
MADRID_OFFSET = timedelta(hours=1)


def _hora_madrid() -> datetime:
    """Devuelve datetime actual en hora de Madrid (aprox)."""
    from datetime import timezone
    utc_now = datetime.now(timezone.utc)
    return utc_now + MADRID_OFFSET


async def _tarea_diaria():
    """Tarea diaria: escuchar señales de las 3 capas."""
    try:
        from src.pilates.voz_ciclos import escuchar
        result = await escuchar()
        log.info("cron_diaria_ok", senales=result.get("senales_creadas", 0))
    except Exception as e:
        log.error("cron_diaria_error", error=str(e))


async def _tarea_semanal():
    """Tarea semanal (lunes): ciclo completo + estrategia."""
    try:
        # 1. Ciclo completo (escuchar + priorizar + IRC + ISP)
        from src.pilates.voz_ciclos import ejecutar_ciclo_completo
        ciclo = await ejecutar_ciclo_completo()
        log.info("cron_semanal_ciclo_ok", isp=ciclo.get("ciclos", {}).get("aprender", {}).get("isp_global"))

        # 2. Calcular nueva estrategia semanal
        from src.pilates.voz_estrategia import calcular_estrategia
        est = await calcular_estrategia()
        log.info("cron_semanal_estrategia_ok",
                 foco=est.get("estrategia", {}).get("foco_principal"),
                 items=est.get("calendario_items"))

    except Exception as e:
        log.error("cron_semanal_error", error=str(e))


async def cron_loop():
    """Loop principal del cron. Se ejecuta como background task.

    Revisa cada 15 minutos si hay tareas pendientes.
    Marca las ejecutadas para no repetir en el mismo día/semana.
    """
    log.info("cron_iniciado")

    ultima_diaria = None
    ultima_semanal = None

    while True:
        try:
            ahora = _hora_madrid()
            hoy = ahora.date()
            hora = ahora.time()

            # Tarea diaria: después de las 06:00, una vez al día
            if hora >= time(6, 0) and ultima_diaria != hoy:
                log.info("cron_ejecutando_diaria", hora=str(hora))
                await _tarea_diaria()
                ultima_diaria = hoy

            # Tarea semanal: lunes después de las 07:00, una vez por semana
            if ahora.weekday() == 0 and hora >= time(7, 0):
                semana = hoy.isocalendar()[1]
                if ultima_semanal != semana:
                    log.info("cron_ejecutando_semanal", semana=semana)
                    await _tarea_semanal()
                    ultima_semanal = semana

        except Exception as e:
            log.error("cron_loop_error", error=str(e))

        # Dormir 15 minutos
        await asyncio.sleep(900)
```

---

## FASE E3: Registrar cron en el lifespan

**Archivo:** `src/main.py` — EDITAR

Buscar la línea `log.info("startup_complete")` dentro de la función `lifespan` y DESPUÉS de esa línea (pero ANTES del `yield`), añadir:

```python
    # Iniciar cron de tareas programadas
    try:
        from src.pilates.cron import cron_loop
        asyncio.create_task(cron_loop())
        log.info("startup_cron_started")
    except Exception as e:
        log.warning("startup_cron_failed", error=str(e))
```

También añadir `import asyncio` al inicio de `main.py` si no está ya.

---

## FASE E4: Endpoint manual de cron

**Archivo:** `src/pilates/router.py` — AÑADIR al final.

Para poder disparar el cron manualmente (testing, o cuando Jesús quiera forzar).

```python
# ============================================================
# VOZ ESTRATÉGICO — Cron manual
# B-PIL-20e
# ============================================================

@router.post("/voz/cron/diaria")
async def cron_diaria_manual():
    """Dispara la tarea diaria manualmente (escuchar señales)."""
    from src.pilates.cron import _tarea_diaria
    await _tarea_diaria()
    return {"status": "ok", "tarea": "diaria"}

@router.post("/voz/cron/semanal")
async def cron_semanal_manual():
    """Dispara la tarea semanal manualmente (ciclo completo + estrategia)."""
    from src.pilates.cron import _tarea_semanal
    await _tarea_semanal()
    return {"status": "ok", "tarea": "semanal"}
```

---

## VERIFICACIÓN

```bash
# ── V1. cron.py creado ───────────────────────────────────────
ls src/pilates/cron.py
# PASS: archivo existe

# ── V2. Import limpio ────────────────────────────────────────
python -c "from src.pilates.cron import cron_loop; print('OK')"
# PASS: sin errores

# ── V3. Tools Voz en cockpit (contar) ────────────────────────
grep -c "voz_" src/pilates/cockpit.py
# PASS: >= 12 (6 tools + 6 dispatch refs + funciones)

# ── V4. Deploy sin errores ───────────────────────────────────
# fly deploy
# PASS: sin errores de import
# PASS: logs muestran "startup_cron_started"

# ── V5. Chat cockpit — estrategia ───────────────────────────
curl -X POST .../pilates/cockpit/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿cuál es mi estrategia de esta semana?", "modulos_activos": []}'
# PASS: respuesta incluye foco, narrativa, calendario
# PASS: acciones.montar incluye {"id": "voz", "rol": ...}

# ── V6. Chat cockpit — señales ───────────────────────────────
curl -X POST .../pilates/cockpit/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿hay algo urgente?", "modulos_activos": []}'
# PASS: respuesta menciona señales pendientes (si las hay)

# ── V7. Chat cockpit — ISP ──────────────────────────────────
curl -X POST .../pilates/cockpit/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "¿cómo va mi presencia digital?", "modulos_activos": []}'
# PASS: respuesta incluye ISP por canal

# ── V8. Chat cockpit — recalcular ───────────────────────────
curl -X POST .../pilates/cockpit/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "recalcula la estrategia", "modulos_activos": []}'
# PASS: respuesta indica nueva estrategia generada (~5 seg)

# ── V9. Cron diaria manual ───────────────────────────────────
curl -X POST .../pilates/voz/cron/diaria
# PASS: status="ok"

# ── V10. Cron semanal manual ─────────────────────────────────
curl -X POST .../pilates/voz/cron/semanal
# PASS: status="ok"

# ── V11. Módulo Voz actualizado en cockpit ───────────────────
curl .../pilates/cockpit/contexto
# PASS: modulos_disponibles incluye voz con endpoint="/voz/estrategia"

# ── V12. Cron en logs de startup ─────────────────────────────
# fly logs | grep cron
# PASS: "startup_cron_started" presente
# PASS: después de 15 min, "cron_ejecutando_diaria" si es hora
```

---

## NOTAS

- **El cron es un background task de asyncio**, no un scheduler externo. Se reinicia con cada deploy de fly.io. No necesita persistencia — las tareas revisan si ya se ejecutaron hoy/esta semana antes de repetir.
- **Zona horaria simplificada.** UTC+1 fijo. Para un SMB en España es suficiente. Si algún día se necesita, se puede usar `zoneinfo` (Python 3.9+).
- **Las tools del cockpit no añaden LLM calls propias.** Solo llaman a funciones que ya existen en 20b/20c/20d. El coste adicional es 0 excepto cuando Jesús pide "recalcula" (que sí dispara LLM de deepseek).
- **El cron semanal genera estrategia nueva cada lunes.** Si Jesús la quiere antes, dice "recalcula la estrategia" en el cockpit.
- **El cron diario es ligero (~2 seg).** Solo ESCUCHAR: queries SQL para detectar señales + lectura de om_voz_capa_a. No llama a APIs externas ni LLMs.
- **Si fly.io reinicia a las 03:00 AM:** El cron arranca, revisa que no ha ejecutado la diaria de hoy, y la ejecuta a las 06:00. La semanal solo corre si es lunes.
- **No se borra nada del cockpit existente.** Se añaden 6 tools y 6 dispatch functions. Las tools operativas (buscar_cliente, agendar, pagar, etc.) siguen intactas.
