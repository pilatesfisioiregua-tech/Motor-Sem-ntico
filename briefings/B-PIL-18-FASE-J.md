# B-PIL-18 — Fase J (Addendum 3)

**Fecha:** 2026-03-20
**Complementa:** B-PIL-18 (A-C) + FASES-DEF (D-F) + FASES-GHI (G-I)
**Ejecutor:** Claude Code

---

## FASE J: Interfaz del estudio generativa — Módulos bajo demanda

### Concepto

El Modo Estudio deja de ser un dashboard fijo. Es una interfaz que se
genera según lo que Jesús necesita en el momento.

Al abrir, el sistema saluda con contexto del día y sugiere módulos.
Jesús elige cuáles quiere ver (pulsando o escribiendo).
Los módulos se montan dinámicamente en pantalla.
Mañana pide otros, se muestran otros.

Es el mismo principio que el portal del cliente: una caja de texto
que controla todo. Pero aquí controla la propia interfaz.

### Arquitectura

```
┌──────────────────────────────────────────────────┐
│  Buenos días Jesús. Jueves 20 marzo.             │
│  4 grupos hoy · 1 cancelación · 2 pagos nuevos  │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │ ¿Qué necesitas hoy?                  🔍 │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
│  Sugeridos:                                      │
│  [📅 Agenda] [🔔 Feed] [💰 Pagos] [📊 Mes]     │
│                                                  │
│  ═══════════════════════════════════════════════  │
│                                                  │
│  ┌─────────────────┐  ┌─────────────────────┐   │
│  │  📅 AGENDA HOY  │  │  🔔 FEED NOTICIAS   │   │
│  │                 │  │                     │   │
│  │  09:00 Ref M-J  │  │  💰 Ana: Bizum 105€ │   │
│  │  10:00 Suelo 1  │  │  🔴 María canceló   │   │
│  │  17:00 Mat 2    │  │  🆕 Lead: Laura     │   │
│  │  18:00 Ref L-X  │  │  🏆 Sofía: racha 8  │   │
│  │                 │  │                     │   │
│  └─────────────────┘  └─────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐    │
│  │  💰 PAGOS PENDIENTES                     │    │
│  │  Pedro García — 105€ — 15 días           │    │
│  │  Luis Martínez — 60€ — 8 días            │    │
│  └──────────────────────────────────────────┘    │
│                                                  │
└──────────────────────────────────────────────────┘
```

### Catálogo de módulos disponibles

| ID | Nombre | Componente | Endpoint | Cuándo sugerirlo |
|---|---|---|---|---|
| `agenda` | Agenda de hoy | CalendarioHoy | /sesiones/hoy | Siempre (por defecto) |
| `calendario` | Calendario semanal | Calendario | /sesiones/semana | Si pide vista semanal |
| `feed` | Noticias | FeedEstudio | /feed | Si hay noticias no leídas |
| `pagos_pendientes` | Pagos pendientes | PagosPendientes | /cargos?estado=pendiente | Si hay saldo pendiente |
| `resumen_mes` | Resumen del mes | ResumenMes | /resumen | Principio de mes o bajo demanda |
| `briefing` | Briefing semanal | BriefingPanel | /briefing | Lunes o bajo demanda |
| `solicitudes` | Solicitudes clientes | SolicitudesPanel | /procesos?tipo=solicitud_cliente | Si hay solicitudes pendientes |
| `alertas` | Alertas retención | AlertasPanel | /alertas | Si hay alertas activas |
| `buscar` | Buscar cliente | BuscadorCliente | /buscar?q= | Siempre disponible |
| `grupos` | Ocupación grupos | GruposPanel | /grupos | Bajo demanda |
| `sequito` | Consejo asesores | Consejo | /consejo | Bajo demanda |
| `acd` | Diagnóstico ACD | ACDPanel | /acd/diagnosticar | Bajo demanda |
| `voz` | Propuestas Voz | VozPanel | /voz/propuestas | Si hay propuestas pendientes |
| `depuracion` | Depuración (F3) | DepuracionPanel | /depuracion | Bajo demanda |
| `adn` | ADN del negocio | ADNPanel | /adn | Bajo demanda |
| `readiness` | Readiness replicación | ReadinessPanel | /readiness | Bajo demanda |
| `facturas` | Facturación | FacturasPanel | /facturas | Final de mes |
| `estadisticas` | Estadísticas trimestre | EstadisticasPanel | /resumen?mes=... | Bajo demanda |
| `engagement` | Engagement clientes | EngagementPanel | (nuevo endpoint) | Si hay clientes en riesgo |
| `wa` | Panel WhatsApp | PanelWA | /whatsapp/mensajes | Si hay mensajes sin leer |

### J1. Backend — Contexto del día + sugerencias

**Archivo:** Crear `src/pilates/cockpit.py`

```python
"""Cockpit del Estudio — Motor de interfaz generativa.

Analiza el contexto del día y sugiere qué módulos mostrar.
Aprende de las preferencias de Jesús.

Fuente: Exocortex v2.1 B-PIL-18 Fase J.
"""
from __future__ import annotations
import json, structlog
from datetime import date, datetime, timedelta
from typing import Optional

log = structlog.get_logger()
TENANT = "authentic_pilates"

# Catálogo de módulos
MODULOS = {
    "agenda":           {"nombre": "Agenda de hoy",       "icono": "📅", "endpoint": "/sesiones/hoy"},
    "calendario":       {"nombre": "Calendario semanal",  "icono": "📅", "endpoint": "/sesiones/semana"},
    "feed":             {"nombre": "Noticias",             "icono": "🔔", "endpoint": "/feed"},
    "pagos_pendientes": {"nombre": "Pagos pendientes",    "icono": "💰", "endpoint": "/cargos?estado=pendiente"},
    "resumen_mes":      {"nombre": "Resumen del mes",     "icono": "📊", "endpoint": "/resumen"},
    "briefing":         {"nombre": "Briefing semanal",    "icono": "📋", "endpoint": "/briefing"},
    "solicitudes":      {"nombre": "Solicitudes",          "icono": "📋", "endpoint": "/procesos"},
    "alertas":          {"nombre": "Alertas retención",   "icono": "⚠️", "endpoint": "/alertas"},
    "buscar":           {"nombre": "Buscar cliente",       "icono": "🔍", "endpoint": "/buscar"},
    "grupos":           {"nombre": "Ocupación grupos",    "icono": "👥", "endpoint": "/grupos"},
    "sequito":          {"nombre": "Consejo asesores",     "icono": "🧠", "endpoint": "/consejo"},
    "acd":              {"nombre": "Diagnóstico ACD",     "icono": "🔬", "endpoint": "/acd/diagnosticar"},
    "voz":              {"nombre": "Propuestas Voz",       "icono": "💬", "endpoint": "/voz/propuestas"},
    "depuracion":       {"nombre": "Depuración",          "icono": "🗑️", "endpoint": "/depuracion"},
    "adn":              {"nombre": "ADN del negocio",      "icono": "🧬", "endpoint": "/adn"},
    "readiness":        {"nombre": "Readiness",            "icono": "📈", "endpoint": "/readiness"},
    "facturas":         {"nombre": "Facturación",         "icono": "📄", "endpoint": "/facturas"},
    "engagement":       {"nombre": "Engagement clientes",  "icono": "❤️", "endpoint": "/engagement"},
    "wa":               {"nombre": "Panel WhatsApp",       "icono": "💬", "endpoint": "/whatsapp/mensajes"},
}


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def contexto_del_dia() -> dict:
    """Genera el contexto del día para el saludo + sugerencias de módulos.

    Analiza: sesiones programadas, pagos pendientes, noticias sin leer,
    alertas activas, solicitudes pendientes, día de la semana.

    Returns: {saludo, datos, modulos_sugeridos, modulos_disponibles}
    """
    hoy = date.today()
    dia_nombre = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"][hoy.weekday()]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Sesiones de hoy
        sesiones_hoy = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id=$1 AND fecha=$2
        """, TENANT, hoy)

        # Cancelaciones hoy
        cancelaciones = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id=a.sesion_id
            WHERE a.tenant_id=$1 AND s.fecha=$2 AND a.estado='cancelada'
        """, TENANT, hoy)

        # Pagos pendientes totales
        deuda_total = await conn.fetchval("""
            SELECT COALESCE(SUM(total),0) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)
        clientes_deudores = await conn.fetchval("""
            SELECT count(DISTINCT cliente_id) FROM om_cargos
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)

        # Feed no leído
        feed_no_leido = await conn.fetchval("""
            SELECT count(*) FROM om_feed_estudio
            WHERE tenant_id=$1 AND leido=false
        """, TENANT)

        # Alertas activas
        alertas = await conn.fetchval("""
            SELECT count(*) FROM om_tensiones
            WHERE tenant_id=$1 AND estado='activa' AND severidad IN ('alta','critica')
        """, TENANT)

        # Solicitudes pendientes
        solicitudes = await conn.fetchval("""
            SELECT count(*) FROM om_procesos
            WHERE tenant_id=$1 AND estado='pendiente' AND tipo='solicitud_cliente'
        """, TENANT)

        # Propuestas Voz pendientes
        voz_pendientes = await conn.fetchval("""
            SELECT count(*) FROM om_voz_propuestas
            WHERE tenant_id=$1 AND estado='pendiente'
        """, TENANT)

        # WA sin leer
        wa_sin_leer = await conn.fetchval("""
            SELECT count(*) FROM om_mensajes_wa
            WHERE tenant_id=$1 AND direccion='entrante' AND leido=false
        """, TENANT)

        # Clientes en riesgo churn
        try:
            churn_alto = await conn.fetchval("""
                SELECT count(*) FROM om_cliente_perfil
                WHERE tenant_id=$1 AND riesgo_churn IN ('alto','critico')
            """, TENANT)
        except:
            churn_alto = 0

    # --- Construir saludo ---
    partes_saludo = [f"Hoy es {dia_nombre} {hoy.day} de {_nombre_mes(hoy.month)}."]

    if sesiones_hoy > 0:
        partes_saludo.append(f"{sesiones_hoy} sesiones programadas.")
    else:
        partes_saludo.append("No hay sesiones programadas hoy.")

    extras = []
    if cancelaciones > 0:
        extras.append(f"{cancelaciones} cancelación{'es' if cancelaciones > 1 else ''}")
    if feed_no_leido > 0:
        extras.append(f"{feed_no_leido} noticia{'s' if feed_no_leido > 1 else ''} nueva{'s' if feed_no_leido > 1 else ''}")
    if solicitudes > 0:
        extras.append(f"{solicitudes} solicitud{'es' if solicitudes > 1 else ''} pendiente{'s' if solicitudes > 1 else ''}")
    if extras:
        partes_saludo.append(" · ".join(extras) + ".")

    saludo = " ".join(partes_saludo)

    # --- Sugerir módulos según contexto ---
    sugeridos = []

    # Siempre: agenda
    sugeridos.append("agenda")

    # Si hay noticias sin leer
    if feed_no_leido > 0:
        sugeridos.append("feed")

    # Si hay pagos pendientes
    if clientes_deudores > 0:
        sugeridos.append("pagos_pendientes")

    # Si es lunes → briefing
    if hoy.weekday() == 0:
        sugeridos.append("briefing")

    # Si hay solicitudes
    if solicitudes > 0:
        sugeridos.append("solicitudes")

    # Si hay alertas
    if alertas > 0:
        sugeridos.append("alertas")

    # Si hay WA sin leer
    if wa_sin_leer > 0:
        sugeridos.append("wa")

    # Si hay propuestas Voz
    if voz_pendientes > 0:
        sugeridos.append("voz")

    # Si hay churn alto
    if churn_alto > 0:
        sugeridos.append("engagement")

    # Máximo 6 sugeridos para no saturar
    sugeridos = sugeridos[:6]

    # Buscar preferencia guardada de Jesús
    try:
        async with pool.acquire() as conn:
            pref = await conn.fetchval("""
                SELECT metadata->>'modulos_frecuentes' FROM om_cliente_eventos
                WHERE tenant_id=$1 AND tipo='cockpit_config'
                ORDER BY created_at DESC LIMIT 1
            """, TENANT)
            if pref:
                frecuentes = json.loads(pref)
                # Añadir frecuentes que no están ya sugeridos
                for m in frecuentes:
                    if m not in sugeridos and m in MODULOS:
                        sugeridos.append(m)
                sugeridos = sugeridos[:6]
    except:
        pass

    # --- Datos resumen ---
    datos = {
        "sesiones_hoy": sesiones_hoy,
        "cancelaciones_hoy": cancelaciones,
        "deuda_total": float(deuda_total),
        "clientes_deudores": clientes_deudores,
        "feed_no_leido": feed_no_leido,
        "alertas_activas": alertas,
        "solicitudes_pendientes": solicitudes,
        "voz_pendientes": voz_pendientes,
        "wa_sin_leer": wa_sin_leer,
        "churn_alto": churn_alto,
    }

    return {
        "saludo": saludo,
        "datos": datos,
        "modulos_sugeridos": [
            {"id": m, **MODULOS[m]} for m in sugeridos if m in MODULOS
        ],
        "modulos_disponibles": [
            {"id": k, **v} for k, v in MODULOS.items()
        ],
    }


async def guardar_configuracion(modulos_activos: list[str]):
    """Guarda qué módulos ha elegido Jesús para aprender sus preferencias."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Contar frecuencia
        freq = await conn.fetchval("""
            SELECT metadata FROM om_cliente_eventos
            WHERE tenant_id=$1 AND tipo='cockpit_frecuencia'
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

        frecuencia = json.loads(freq) if freq else {}
        for m in modulos_activos:
            frecuencia[m] = frecuencia.get(m, 0) + 1

        # Top 6 más usados
        top = sorted(frecuencia.items(), key=lambda x: -x[1])[:6]
        modulos_frecuentes = [m[0] for m in top]

        await conn.execute("""
            INSERT INTO om_cliente_eventos (tenant_id, cliente_id, tipo, metadata)
            VALUES ($1, '00000000-0000-0000-0000-000000000000', 'cockpit_config', $2::jsonb)
        """, TENANT, json.dumps({
            "modulos_activos": modulos_activos,
            "modulos_frecuentes": modulos_frecuentes,
            "frecuencia": frecuencia,
        }))


def _nombre_mes(n):
    return ["enero","febrero","marzo","abril","mayo","junio",
            "julio","agosto","septiembre","octubre","noviembre","diciembre"][n-1]
```

### J2. Endpoints

```python
# En router.py:

@router.get("/cockpit")
async def cockpit():
    """Contexto del día + módulos sugeridos para el Modo Estudio."""
    from src.pilates.cockpit import contexto_del_dia
    return await contexto_del_dia()

@router.post("/cockpit/config")
async def guardar_config_cockpit(data: dict):
    """Guarda qué módulos ha elegido Jesús (aprende preferencias)."""
    from src.pilates.cockpit import guardar_configuracion
    await guardar_configuracion(data.get("modulos", []))
    return {"status": "ok"}
```

### J3. Frontend — EstudioCockpit.jsx (concepto)

```jsx
// Reemplaza App.jsx como interfaz principal del Modo Estudio
//
// Estado:
//   modulosActivos: ["agenda", "feed", "pagos_pendientes"]
//
// Al montar:
//   1. GET /cockpit → saludo + sugerencias
//   2. Pre-cargar datos de módulos sugeridos
//
// Al pulsar un módulo sugerido:
//   1. Añadir a modulosActivos
//   2. Renderizar componente correspondiente
//   3. POST /cockpit/config con la lista actual (para aprender)
//
// Al escribir en la caja:
//   "Ponme agenda y pagos" → parsear → activar módulos
//   "Quita el feed" → desactivar módulo
//   "Busca a María" → activar módulo buscar con query
//   Cualquier otra cosa → pasar al motor conversacional del séquito
//
// Layout:
//   - Módulos se renderizan en grid responsive (1-3 columnas)
//   - Cada módulo tiene cabecera con nombre + botón cerrar (×)
//   - Se pueden reordenar arrastrando (futuro)
//
// Componentes existentes que se reusan:
//   - Calendario.jsx → módulo "calendario"
//   - PanelWA.jsx → módulo "wa"
//   - Consejo.jsx → módulo "sequito"
//   - Profundo.jsx pestañas → módulos individuales

const MODULO_COMPONENTS = {
    agenda:           AgendaHoy,
    calendario:       CalendarioSemanal,
    feed:             FeedEstudio,
    pagos_pendientes: PagosPendientes,
    resumen_mes:      ResumenMes,
    briefing:         BriefingPanel,
    solicitudes:      SolicitudesPanel,
    alertas:          AlertasPanel,
    buscar:           BuscadorCliente,
    grupos:           GruposPanel,
    sequito:          ConsejoPanel,
    acd:              ACDPanel,
    voz:              VozPanel,
    depuracion:       DepuracionPanel,
    adn:              ADNPanel,
    readiness:        ReadinessPanel,
    facturas:         FacturasPanel,
    engagement:       EngagementPanel,
    wa:               PanelWA,
};
```

### J4. Interacción conversacional con la interfaz

La caja de texto del cockpit no solo selecciona módulos —
también puede interactuar con ellos:

```
Jesús: "¿Quién ha cancelado hoy?"
→ Activa módulo feed filtrado por cancelaciones de hoy

Jesús: "Ponme la agenda y los pagos pendientes"
→ Monta esos dos módulos en pantalla

Jesús: "Quita todo y ponme solo el briefing"
→ Desmonta todos, monta briefing

Jesús: "¿Cuánto debemos cobrar este mes?"
→ Activa módulo resumen_mes, responde con el dato

Jesús: "Convoca al Consejo: ¿deberíamos subir precios?"
→ Activa módulo séquito con la pregunta pre-cargada

Jesús: "Búscame a María"
→ Activa módulo buscar con "María" como query

Jesús: "¿Cómo va el engagement de Pedro?"
→ Activa módulo engagement filtrado por Pedro
```

Para esto, el system prompt del cockpit incluye una tool extra:

```python
{
    "type": "function",
    "function": {
        "name": "configurar_interfaz",
        "description": "Montar o desmontar módulos en la interfaz del estudio. Usar cuando Jesús pide ver algo específico o quitar algo.",
        "parameters": {
            "type": "object",
            "properties": {
                "montar": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs de módulos a montar/mostrar"
                },
                "desmontar": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "IDs de módulos a quitar"
                },
                "desmontar_todos": {
                    "type": "boolean",
                    "description": "Quitar todos los módulos antes de montar nuevos"
                }
            }
        }
    }
}
```

El LLM decide qué módulos montar/desmontar según lo que Jesús pide.
El frontend recibe la instrucción y reconfigura la UI en tiempo real.

---

### Resumen Fase J

Lo que era un dashboard fijo con pestañas pasa a ser:

1. **Interfaz generativa** — se monta según necesidad
2. **Sugerencias inteligentes** — basadas en el contexto del día
3. **Conversacional** — puedes hablar con la interfaz
4. **Aprende** — memoriza qué módulos usa Jesús más
5. **20 módulos disponibles** — de agenda a ACD, todos on-demand
6. **Cero curva de aprendizaje** — escribes lo que necesitas

Es el mismo principio del portal del cliente aplicado a la interfaz del dueño.

---

### Verificación

```bash
# J1. Cockpit contexto
curl .../cockpit
# PASS: saludo con datos del día + modulos_sugeridos + modulos_disponibles

# J2. Guardar config
curl -X POST .../cockpit/config -d '{"modulos":["agenda","feed","pagos_pendientes"]}'
# PASS: {"status": "ok"}

# J3. Frontend
# Abrir /estudio → Saludo + módulos sugeridos
# Pulsar "Agenda" → Se monta el componente
# Escribir "Ponme feed y pagos" → Se montan ambos
# Escribir "Quita todo" → Se desmontan todos
```
