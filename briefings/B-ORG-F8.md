# B-ORG-F8 — Fase 8: Autonomía Total

**Fecha:** 24 marzo 2026
**Estimación:** ~22h
**Prerequisito:** F5 (reactivo, mediador, comunicación), F6 (tests, CI/CD, multi-tenant), F6B (interfaz organismo), F7 (identidad, filtro)
**WIP:** 2 (auto-reparación y predicción son paralelos con PWA)
**Principios:** P66 (circuitos completos), P30 (come tu comida primero)

---

## OBJETIVO

El sistema opera sin intervención humana semanal. Se repara solo, predice problemas antes de que existan, y solo pide CR1 para decisiones de alto riesgo. Jesús pasa de operador a gobernante.

**Antes:** Jesús revisa cada lunes, aprueba cada acción, interviene en errores.
**Después:** El sistema corre 24/7, Jesús solo recibe informes y decide lo estratégico.

---

## PASO 1: AUTO-REPARACIÓN — Goma META operativa (~8h)

### 1.1 Vigía mejorado (src/pilates/vigia.py)

Vigía ya existe y corre cada 15 min. Mejorarlo para detectar degradaciones reales y clasificarlas:

```python
# Categorías de degradación:
CATEGORIAS_DEGRADACION = {
    "db_lenta": {"check": "avg query time > 500ms", "reparacion": "VACUUM ANALYZE"},
    "cron_parado": {"check": "última ejecución > 36h", "reparacion": "restart cron task"},
    "llm_budget_excedido": {"check": "presupuesto_restante <= 0", "reparacion": "degradar modelos a baja"},
    "bus_saturado": {"check": "señales pendientes > 100", "reparacion": "marcar antiguas como procesadas"},
    "api_lenta": {"check": "health check > 5s", "reparacion": "liberar semáforos"},
    "cache_lleno": {"check": "entradas caché > 1000", "reparacion": "limpiar expiradas"},
    "disco_lleno": {"check": "DB size > 1GB", "reparacion": "limpiar telemetría vieja"},
}
```

Vigía escribe diagnóstico en `om_senales_agentes` tipo ALERTA prioridad 1 con categoría.

### 1.2 Mecánico mejorado (src/pilates/mecanico.py)

Mecánico ya existe. Mejorarlo para ejecutar reparaciones automáticas por categoría:

```python
REPARACIONES_AUTO = {
    "bus_saturado": "_reparar_bus_saturado",
    "cache_lleno": "_reparar_cache_lleno",
    "llm_budget_excedido": "_reparar_budget",
    "cron_parado": "_reparar_cron",
}

REPARACIONES_CR1 = {
    "db_lenta": "Requiere VACUUM ANALYZE — puede afectar rendimiento",
    "disco_lleno": "Requiere borrar datos — riesgo de pérdida",
}
```

Para reparaciones auto: ejecutar directamente + notificar Jesús por WA post-mortem.
Para reparaciones CR1: notificar Jesús con diagnóstico + opciones + esperar respuesta.

### 1.3 Informe post-mortem automático

Después de cada reparación auto, programar en pizarra comunicación:

```python
async def informe_postmortem(categoria: str, diagnostico: dict, resultado: dict):
    """Genera y programa informe post-mortem por WA."""
    mensaje = (
        f"🔧 Reparación automática completada\n\n"
        f"Problema: {categoria}\n"
        f"Diagnóstico: {diagnostico.get('detalle', '')[:100]}\n"
        f"Acción: {resultado.get('accion', '')[:100]}\n"
        f"Estado: {'✅ Resuelto' if resultado.get('ok') else '⚠️ Requiere atención'}"
    )
    # Programar en pizarra comunicación...
```

**Test 1.1:** Insertar 150 señales pendientes → Vigía detecta "bus_saturado" → Mecánico limpia → Jesús recibe informe
**Test 1.2:** Forzar presupuesto excedido → Vigía detecta → Mecánico degrada modelos → informe

---

## PASO 2: PREDICCIÓN (~6h)

### 2.1 Modelo de abandono (src/pilates/predictor.py)

```python
"""Predictor — Modelos predictivos basados en patrones del organismo.

No usa ML complejo — usa reglas + patrones de pizarra evolución.
Los patrones vienen de Memoria (F5) que detecta estacionalidad/recurrencia.
"""

async def predecir_abandonos() -> list[dict]:
    """Predice qué clientes van a abandonar en las próximas 3 semanas.

    Factores:
    1. Asistencia decreciente (últimas 4 semanas)
    2. Patrones estacionales (de pizarra evolución)
    3. Deuda acumulada
    4. Engagement score bajando
    5. Cancelaciones recientes

    Cada predicción: {cliente_id, nombre, probabilidad, factores, accion_preventiva}
    """

async def predecir_demanda_semana() -> dict:
    """Predice sesiones esperadas la próxima semana.

    Cruza: calendario, estacionalidad (pizarra evolución),
    cancelaciones históricas del mismo periodo, festivos.
    """

async def predecir_cashflow_mes() -> dict:
    """Predice cobros esperados vs gastos fijos.

    Cobros: contratos activos × precio - tasa abandono estimada
    Gastos: fijos (alquiler, seguros) + variables (LLM, infra)
    Alerta si gap > 20%.
    """
```

### 2.2 Integración en cron semanal

Al inicio de `_tarea_semanal()`:

```python
        # 0b. Predicciones (antes de diagnosticar — alimenta al Director)
        try:
            from src.pilates.predictor import predecir_abandonos, predecir_demanda_semana
            abandonos = await predecir_abandonos()
            demanda = await predecir_demanda_semana()
            if abandonos:
                for a in abandonos[:5]:
                    await emitir("ALERTA", "PREDICTOR",
                        {"subtipo": "abandono_predicho", **a},
                        destino="AF1", prioridad=2)
            log.info("cron_predicciones_ok", abandonos=len(abandonos),
                     demanda_estimada=demanda.get("sesiones_estimadas"))
        except Exception as e:
            log.error("cron_predicciones_error", error=str(e))
```

**Test 2.1:** `python -c "from src.pilates.predictor import predecir_abandonos; print('ok')"` → ok
**Test 2.2:** Cliente con 0 asistencias 3 semanas → aparece en predicción

---

## PASO 3: AUTONOMÍA PROGRESIVA (~3h)

### 3.1 Tabla de niveles de autonomía

En pizarra dominio, config JSONB, añadir:

```json
{
  "autonomia": {
    "auto": [
      "confirmacion_sesion", "felicitacion_cumpleanos",
      "respuesta_resena_positiva", "contenido_filtro_compatible",
      "reparacion_bus", "reparacion_cache"
    ],
    "notificar_4h": [
      "cerrar_grupo_bajo", "cambiar_horario",
      "ajustar_precio_demanda", "contenido_filtro_ambiguo"
    ],
    "cr1_siempre": [
      "subir_precio_10pct", "cambiar_identidad",
      "aceptar_b2b", "reparacion_db", "borrar_datos",
      "publicar_contenido_nuevo_canal"
    ]
  }
}
```

### 3.2 Motor de decisión (src/pilates/autonomia.py)

```python
"""Autonomía — Motor de decisión que clasifica acciones por nivel.

Niveles:
  AUTO: ejecutar + log
  NOTIFICAR_4H: ejecutar + WA Jesús + si veto en 4h cancelar
  CR1: WA Jesús + esperar aprobación + timeout 48h
"""

async def decidir_nivel(accion_tipo: str, tenant_id: str = "authentic_pilates") -> str:
    """Determina el nivel de autonomía para una acción.

    Lee pizarra dominio config.autonomia.
    Si acción no catalogada → CR1 (conservador).
    """
    from src.pilates.pizarras import leer_dominio
    dominio = await leer_dominio(tenant_id)
    autonomia = dominio.get("config", {}).get("autonomia", {})

    if accion_tipo in (autonomia.get("auto") or []):
        return "auto"
    elif accion_tipo in (autonomia.get("notificar_4h") or []):
        return "notificar_4h"
    else:
        return "cr1"


async def ejecutar_con_autonomia(accion_tipo: str, ejecutor, *args, **kwargs) -> dict:
    """Ejecuta una acción respetando el nivel de autonomía.

    ejecutor: async function a ejecutar si se permite.
    """
    nivel = await decidir_nivel(accion_tipo)

    if nivel == "auto":
        resultado = await ejecutor(*args, **kwargs)
        # Log silencioso
        return {"nivel": "auto", "ejecutado": True, "resultado": resultado}

    elif nivel == "notificar_4h":
        resultado = await ejecutor(*args, **kwargs)
        # Notificar + programar cancelación si veto
        import os
        telefono = os.getenv("JESUS_TELEFONO", "")
        if telefono:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_pizarra_comunicacion
                        (tenant_id, destinatario, canal, tipo, mensaje,
                         programado_para, estado, origen)
                    VALUES ('authentic_pilates', $1, 'whatsapp', 'notificacion_autonomia',
                            $2, now(), 'pendiente', 'AUTONOMIA')
                """, telefono,
                    f"🤖 Acción ejecutada: {accion_tipo}\nTienes 4h para vetar. Responde 'cancelar' si no estás de acuerdo.")
        return {"nivel": "notificar_4h", "ejecutado": True, "resultado": resultado}

    else:  # cr1
        import os
        telefono = os.getenv("JESUS_TELEFONO", "")
        if telefono:
            from src.db.client import get_pool
            pool = await get_pool()
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_pizarra_comunicacion
                        (tenant_id, destinatario, canal, tipo, mensaje,
                         programado_para, estado, origen, metadata)
                    VALUES ('authentic_pilates', $1, 'whatsapp', 'solicitud_cr1',
                            $2, now(), 'pendiente', 'AUTONOMIA', $3::jsonb)
                """, telefono,
                    f"⚠️ Necesito tu aprobación:\n{accion_tipo}\nResponde 'sí' o 'no'.",
                    json.dumps({"accion_tipo": accion_tipo}))
        return {"nivel": "cr1", "ejecutado": False, "esperando_aprobacion": True}
```

**Test 3.1:** `decidir_nivel("confirmacion_sesion")` → "auto"
**Test 3.2:** `decidir_nivel("subir_precio_10pct")` → "cr1"
**Test 3.3:** `decidir_nivel("accion_desconocida")` → "cr1" (conservador)

---

## PASO 4: PWA — Progressive Web App (~10h)

### 4.1 manifest.json

Crear `frontend/public/manifest.json`:

```json
{
  "name": "Authentic Pilates",
  "short_name": "Pilates",
  "description": "Tu estudio de Pilates en Albelda de Iregua",
  "start_url": "/portal/",
  "display": "standalone",
  "theme_color": "#6366f1",
  "background_color": "#f8f9fc",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### 4.2 Service Worker básico

Crear `frontend/public/sw.js`:

```js
const CACHE_NAME = 'ap-v1';
const STATIC_ASSETS = ['/', '/portal/', '/assets/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener('fetch', (event) => {
  // Network first, cache fallback
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
```

### 4.3 Registrar en index.html

```html
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#6366f1">
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js');
  }
</script>
```

### 4.4 Portal mejorado para PWA

El portal del cliente (/portal/{token}) necesita funcionar como app instalable:
- Reserva con un tap (botón grande "Reservar clase")
- Pago con un tap (Bizum/enlace Redsys)
- Historial de sesiones
- Notificaciones push (via WA como fallback — push real en futuro)
- Horario accesible offline (cacheado en Service Worker)

**Nota:** Los detalles de implementación del portal PWA siguen el patrón de F3 (LightLayout, React Router, design tokens light). Claude Code puede implementar siguiendo PortalChat.jsx existente.

**Test 4.1:** Chrome → "Instalar app" disponible en /portal/{token}
**Test 4.2:** Offline → horario visible (cacheado)
**Test 4.3:** Móvil → app se abre como standalone (sin barra de navegación Chrome)

---

## PASO 5: REPUTACIÓN AUTOMÁTICA (~2h)

Crear: `src/pilates/reputacion.py`

```python
"""Reputación — Pide reseñas Google a clientes contentos automáticamente.

Criterio "cliente contento":
- Asistencia regular ≥ N sesiones consecutivas (configurable, default 8)
- Sin quejas últimos 30 días
- Engagement score > 70
- No ha dejado reseña este año

Programa pedido por WA con enlace directo a Google Reviews.
"""

async def detectar_clientes_contentos() -> list[dict]:
    """Detecta clientes que cumplen criterio de 'contento'."""
    # ...queries asistencia, quejas, engagement...

async def programar_pedidos_resena() -> dict:
    """Para cada cliente contento, programa pedido de reseña en pizarra comunicación.

    Mensaje: "Hola {nombre}, llevamos {N} sesiones juntos y nos encanta verte progresar.
    ¿Te importaría dejarnos una reseña? Nos ayuda mucho: {enlace_google_reviews}"

    Máximo 3 pedidos/semana (no saturar).
    """
```

### 5.1 En cron semanal:

```python
        # 14. Reputación: pedir reseñas a clientes contentos
        try:
            from src.pilates.reputacion import programar_pedidos_resena
            rep = await programar_pedidos_resena()
            log.info("cron_semanal_reputacion_ok", pedidos=rep.get("programados", 0))
        except Exception as e:
            log.error("cron_semanal_reputacion_error", error=str(e))
```

**Test 5.1:** Cliente con 10 sesiones consecutivas + engagement alto → pedido de reseña programado
**Test 5.2:** Máximo 3 pedidos/semana respetado

---

## PASO 6: DASHBOARD DE AUTONOMÍA (~2h)

### 6.1 Endpoint

```python
@router.get("/autonomia/dashboard")
async def dashboard_autonomia():
    """Qué ha hecho solo, qué ha pedido permiso, qué espera CR1."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Acciones auto últimos 7 días
        auto = await conn.fetchval("""
            SELECT count(*) FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='log_auto' AND created_at >= now() - interval '7 days'
        """)
        # Notificaciones pendientes
        notif = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='notificacion_autonomia' AND created_at >= now() - interval '7 days'
        """)
        # CR1 pendientes
        cr1 = await conn.fetch("""
            SELECT * FROM om_pizarra_comunicacion
            WHERE tenant_id='authentic_pilates' AND origen='AUTONOMIA'
                AND tipo='solicitud_cr1' AND estado='pendiente'
        """)
    return {
        "auto_7d": auto,
        "notificaciones": [dict(r) for r in notif],
        "cr1_pendientes": [dict(r) for r in cr1],
    }
```

### 6.2 Panel en Cockpit

Crear `panels/AutonomiaPanel.jsx` que muestra: gauge de autonomía (% auto vs CR1), lista de acciones auto recientes, CR1 pendientes con botones aprobar/rechazar.

**Test 6.1:** `curl /pilates/autonomia/dashboard` → JSON con stats

---

## PASO 7: ONBOARDING AUTOMATIZADO (~4h)

### 7.1 Wizard web para nuevo tenant

Crear endpoint + frontend para que un nuevo negocio se dé de alta:

1. Formulario: nombre, ubicación, tipo (pilates/fisio/yoga/otro), email, teléfono
2. Sistema genera: fila en `om_pizarra_dominio` + seeds `om_pizarra_modelos` + pizarra identidad vacía con prompts para rellenar
3. Primer diagnóstico ACD automático → genera prescripción → Director diseña primeras recetas

```python
@router.post("/onboarding/tenant")
async def onboarding_nuevo_tenant(request: Request):
    """Wizard: crea un nuevo tenant desde cero."""
    body = await request.json()
    # Validar campos requeridos
    # INSERT om_pizarra_dominio
    # INSERT om_pizarra_modelos (seeds)
    # INSERT om_pizarra_identidad (vacía con defaults)
    # Trigger primer diagnóstico ACD
    return {"status": "ok", "tenant_id": tenant_id}
```

**Test 7.1:** POST /onboarding/tenant → tenant creado → pizarras seed → primer ACD
**Test 7.2:** Nuevo tenant puede ejecutar ciclo semanal sin código nuevo

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `src/pilates/vigia.py` | +categorías degradación + diagnóstico clasificado | 1 |
| `src/pilates/mecanico.py` | +reparaciones auto por categoría + informe post-mortem | 1 |
| `src/pilates/predictor.py` | **NUEVO** — abandono + demanda + cashflow | 2 |
| `src/pilates/autonomia.py` | **NUEVO** — motor decisión 3 niveles | 3 |
| `frontend/public/manifest.json` | **NUEVO** — PWA manifest | 4 |
| `frontend/public/sw.js` | **NUEVO** — Service Worker | 4 |
| `frontend/src/index.html` | +manifest + SW registro | 4 |
| `src/pilates/reputacion.py` | **NUEVO** — pedidos reseña automáticos | 5 |
| `src/pilates/router.py` | +endpoints autonomia/dashboard + onboarding/tenant | 6, 7 |
| `frontend/src/panels/AutonomiaPanel.jsx` | **NUEVO** — dashboard autonomía | 6 |
| `src/pilates/cron.py` | +predicciones + reputación | 2, 5 |

## TESTS FINALES (PASS/FAIL)

```
T1:  Bus saturado (150+ señales) → Vigía detecta → Mecánico limpia → WA informe     [PASS/FAIL]
T2:  python -c "from src.pilates.predictor import predecir_abandonos" → ok           [PASS/FAIL]
T3:  decidir_nivel("confirmacion_sesion") → "auto"                                    [PASS/FAIL]
T4:  decidir_nivel("subir_precio_10pct") → "cr1"                                      [PASS/FAIL]
T5:  Chrome /portal/{token} → "Instalar app" disponible                               [PASS/FAIL]
T6:  Cliente 10 sesiones + engagement alto → pedido reseña programado                 [PASS/FAIL]
T7:  curl /pilates/autonomia/dashboard → JSON con auto/notif/cr1                      [PASS/FAIL]
T8:  POST /onboarding/tenant → tenant creado + pizarras seed                          [PASS/FAIL]
T9:  npm run build → sin errores                                                      [PASS/FAIL]
T10: Offline en PWA → horario visible                                                 [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Editar vigia.py + mecanico.py (Paso 1)
2. Crear predictor.py (Paso 2)
3. Crear autonomia.py (Paso 3)
4. PWA: manifest + SW + index.html (Paso 4)
5. Crear reputacion.py (Paso 5)
6. Endpoints + dashboard panel (Pasos 6, 7)
7. Editar cron.py (Pasos 2, 5)
8. `npm run build` + deploy
9. Verificar T1-T10

## NOTAS

- **Auto-reparación NO usa Claude Code API** (demasiado riesgo). Las reparaciones son operaciones SQL/config simples ejecutadas por código Python. Claude Code solo para arquitectura/desarrollo.
- **Predicción es código puro + reglas + patrones de evolución** — no ML. Con 90 clientes no hay datos suficientes para ML. Las reglas cubren el 90% de los casos.
- **PWA es $0** — Service Worker + manifest. No app stores. Los clientes instalan desde Chrome.
- **Autonomía progresiva es conservadora por diseño**: cualquier acción no catalogada → CR1. Jesús puede reclasificar acciones editando config.autonomia en pizarra dominio.
- **Reputación limitada a 3/semana** para no saturar. Solo clientes genuinamente contentos (datos reales, no heurística).
- **Onboarding tenant es el paso final** — demuestra que el sistema puede crecer sin código nuevo. Un nuevo negocio = 1 formulario web.
