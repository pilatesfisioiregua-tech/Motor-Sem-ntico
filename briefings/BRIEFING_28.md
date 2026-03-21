# BRIEFING_28: CEO Dashboard — Sistema Cognitivo OMNI-MIND

Fecha: 2026-03-18
Contexto: Fase 2 del plan en `docs/operativo/PLAN_SISTEMA_COGNITIVO_v1.md`
Dependencia: B27 (bugs fixeados, deploy con v3.5.0)

---

## Objetivo

Construir el CEO Dashboard del sistema cognitivo: una interfaz web que muestra el estado real de OMNI-MIND en tiempo real. NO es un dashboard de Code OS — es el dashboard del sistema cognitivo (18 inteligencias, Matriz 3L×7F, enjambres, autopoiesis, etc.).

El CEO (Jesús) debe poder abrir una URL y ver inmediatamente:
- ¿El sistema está vivo? (autopoiesis)
- ¿Dónde están los gaps? (heatmap Matriz)
- ¿Qué exocortex hay activos? (tenants)
- ¿Cuánto cuesta? (presupuesto)
- ¿Qué debería hacer ahora? (advisor)

---

## PARTE 1: Endpoint `/ceo/estado-completo`

### Ubicación: `api.py`

Crear un nuevo endpoint GET que agrega TODOS los datos del sistema cognitivo en una sola llamada. Esto reemplaza la necesidad de hacer N fetch desde el frontend.

```python
@app.get("/ceo/estado-completo")
async def ceo_estado_completo():
    """Estado completo del sistema cognitivo para el CEO Dashboard."""
    resultado = {"timestamp": time.time(), "version": VERSION}

    # 1. SALUD — autopoiesis + flywheel
    try:
        from core.gestor_scheduler import get_scheduler
        scheduler = get_scheduler()
        resultado['autopoiesis'] = scheduler.check_autopoiesis()
        estado_sched = scheduler.get_estado()
        resultado['flywheel'] = {
            'running': estado_sched.get('running'),
            'ciclos': estado_sched.get('ciclos_completados', 0),
            'intervalo_h': estado_sched.get('intervalo_actual_h'),
            'history': estado_sched.get('flywheel', [])[-10:],
        }
    except Exception as e:
        resultado['autopoiesis'] = {'error': str(e), 'ciclo_roto': True}
        resultado['flywheel'] = {'error': str(e)}

    # 2. SEÑALES PID — por celda
    try:
        from core.registrador import obtener_señales_todas_celdas
        resultado['señales_pid'] = obtener_señales_todas_celdas()
    except Exception as e:
        resultado['señales_pid'] = {'error': str(e)}

    # 3. EJECUCIONES — últimas 10
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, modo, coste_usd, tiempo_s, score_calidad, created_at
                        FROM ejecuciones ORDER BY created_at DESC LIMIT 10
                    """)
                    cols = ['id', 'modo', 'coste_usd', 'tiempo_s', 'score_calidad', 'created_at']
                    resultado['ejecuciones'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            finally:
                put_conn(conn)
        else:
            resultado['ejecuciones'] = []
    except Exception as e:
        resultado['ejecuciones'] = {'error': str(e)}

    # 4. EXOCORTEX — tenants activos
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, nombre, dominio, activo,
                               config->>'fase' as fase,
                               updated_at
                        FROM exocortex_estado WHERE activo = true
                    """)
                    cols = ['id', 'nombre', 'dominio', 'activo', 'fase', 'updated_at']
                    resultado['exocortex'] = [dict(zip(cols, r)) for r in cur.fetchall()]
            finally:
                put_conn(conn)
        else:
            resultado['exocortex'] = []
    except Exception as e:
        resultado['exocortex'] = {'error': str(e)}

    # 5. MODELOS — stack actual
    try:
        from core.model_observatory import get_observatory
        obs = get_observatory()
        config = obs.get_tier_config()
        resultado['modelos'] = {
            'stack': config,
            'active_count': len(set(config.values())),
        }
    except Exception as e:
        resultado['modelos'] = {'error': str(e)}

    # 6. PRESUPUESTO
    try:
        from core.monitoring import get_monitor
        monitor = get_monitor()
        resultado['presupuesto'] = monitor.check_budget()
    except Exception as e:
        resultado['presupuesto'] = {'error': str(e)}

    # 7. ESTIGMERGIA — marcas pendientes
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT tipo, COUNT(*) FROM marcas_estigmergicas
                        WHERE consumida = false GROUP BY tipo
                    """)
                    resultado['estigmergia'] = {r[0]: r[1] for r in cur.fetchall()}
            finally:
                put_conn(conn)
        else:
            resultado['estigmergia'] = {}
    except Exception as e:
        resultado['estigmergia'] = {'error': str(e)}

    # 8. ADVISOR — acciones recomendadas
    try:
        from core.system_advisor import get_advisor
        advisor = get_advisor()
        acciones = advisor.get_actions()
        resultado['advisor'] = {
            'acciones': acciones.get('acciones', [])[:5],
            'n_total': acciones.get('n_total', 0),
        }
    except Exception as e:
        resultado['advisor'] = {'error': str(e)}

    # 9. COBERTURA MATRIZ
    try:
        from core.telemetria import propiocepcion
        resultado['propiocepcion'] = propiocepcion()
    except Exception as e:
        resultado['propiocepcion'] = {'error': str(e)}

    # 10. REACTOR v4
    try:
        from core.reactor_v4 import get_reactor_v4
        rv4 = get_reactor_v4()
        resultado['reactor_v4'] = rv4.estado()
    except Exception as e:
        resultado['reactor_v4'] = {'error': str(e)}

    # 11. COLA DE MEJORAS
    try:
        from core.db_pool import get_conn, put_conn
        conn = get_conn()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT tipo, estado, COUNT(*) FROM cola_mejoras
                        GROUP BY tipo, estado
                    """)
                    resultado['cola_mejoras'] = [
                        {'tipo': r[0], 'estado': r[1], 'count': r[2]}
                        for r in cur.fetchall()
                    ]
            finally:
                put_conn(conn)
        else:
            resultado['cola_mejoras'] = []
    except Exception as e:
        resultado['cola_mejoras'] = {'error': str(e)}

    return resultado
```

**IMPORTANTE:** No copiar este código literal — usarlo como referencia. Leer api.py ANTES de editar, añadir el endpoint cerca del bloque existente `/dashboard` (línea ~2048). Importar `time` si no está ya importado.

---

## PARTE 2: Dashboard HTML

### Ubicación: `static/ceo_cognitivo.html`

Reescribir `static/ceo.html` (actualmente placeholder) con el dashboard completo. La nueva versión debe:

### Diseño visual
- Fondo oscuro (#0a0a0b)
- Tipografía monospace (SF Mono, JetBrains Mono, monospace)
- Colores: verde (#22c55e) = OK, rojo (#ef4444) = error, amarillo (#f59e0b) = warning, azul (#3b82f6) = info
- Responsive: funcionar en mobile
- Single-page: todo en un solo HTML (CSS inline, JS inline)
- Auto-refresh cada 30s vía fetch a `/ceo/estado-completo`

### 4 Paneles

#### Panel 1: Salud del Sistema (top, full width)
- **Indicador autopoiesis**: 5 checks como pills verde/rojo (preguntas, gaps, tasa, datapoints, alertas)
- **Flywheel**: f(n) actual + delta + mini sparkline de últimos 10 ciclos
- **Scheduler**: running/stopped, intervalo actual, último ciclo
- **Versión**: VERSION del sistema

#### Panel 2: Matriz Cognitiva (left, 60% width)
- **Heatmap 3L × 7F**: grid de 21 celdas
  - Color por señal PID: verde (P bajo, mejorando), rojo (P alto, empeorando), gris (sin datos)
  - Tooltip con P, I, D, n_total, tasa_cierre al hover
- **Stats**: total preguntas, inteligencias activas, cobertura
- **Últimas ejecuciones**: mini tabla con modo, score, coste, timestamp

#### Panel 3: Exocortex & Modelos (right, 40% width)
- **Tenants activos**: card por tenant con nombre, dominio, fase, última actividad
- **Stack de modelos**: tabla con rol → modelo
- **Presupuesto**: barra de progreso gastado/límite
- **Reactor v4**: observaciones totales, pendientes, por tipo

#### Panel 4: Acciones (bottom, full width)
- **Advisor**: top 5 acciones recomendadas con prioridad, categoría, icono
- **Estigmergia**: badges con count por tipo de marca pendiente
- **Cola mejoras**: count por tipo/estado

### Interacciones
- Click en celda del heatmap → expande detalle PID
- Click en acción del advisor → ejecuta el endpoint (con confirmación)
- Botón "Ejecutar ciclo Gestor" → POST /gestor/loop
- Botón "Ejecutar Motor vN" → abre prompt para input texto
- Auto-refresh toggle (on/off)

### Estructura del JS
```javascript
// 1. Fetch /ceo/estado-completo
// 2. Render cada panel
// 3. setInterval para auto-refresh

async function fetchEstado() {
    const res = await fetch('/ceo/estado-completo');
    return res.json();
}

function renderAutopoiesis(data) { ... }
function renderHeatmap(señales) { ... }
function renderExocortex(tenants) { ... }
function renderAdvisor(acciones) { ... }

// Init
fetchEstado().then(data => {
    renderAutopoiesis(data);
    renderHeatmap(data.señales_pid);
    renderExocortex(data.exocortex);
    renderAdvisor(data.advisor);
});
```

---

## PARTE 3: Rutas

### Actualizar api.py:

1. Ruta `/ceo` → servir `static/ceo_cognitivo.html` (reemplazar placeholder actual)
2. Mantener `/ceo/advisor` existente
3. Añadir `/ceo/estado-completo` (Parte 1)
4. Mantener `/dashboard` existente (backward compat)

Buscar la ruta actual para `/ceo` en api.py y actualizarla para servir el nuevo archivo.

---

## Criterios PASS/FAIL

### PASS si:
1. `GET /ceo/estado-completo` devuelve JSON con al menos 10 de las 11 secciones sin error
2. `GET /ceo` sirve el dashboard HTML (no el placeholder)
3. El heatmap 3L×7F se renderiza con 21 celdas
4. Los indicadores de autopoiesis muestran verde/rojo correctamente
5. Auto-refresh funciona (verificar en console que fetch se repite cada 30s)
6. El dashboard es legible en viewport 375px (mobile)
7. Deploy exitoso a fly.io

### FAIL si:
- El endpoint `/ceo/estado-completo` da 500
- El HTML tiene errores de JS que impiden renderizado
- No se puede acceder a `https://chief-os-omni.fly.dev/ceo`

---

## Orden de ejecución

1. Leer api.py ANTES de editar
2. Añadir endpoint `/ceo/estado-completo` en api.py
3. Crear `static/ceo_cognitivo.html` con el dashboard completo
4. Actualizar ruta `/ceo` para servir el nuevo HTML
5. Test local si es posible (python api.py)
6. Deploy a fly.io
7. Verificar `https://chief-os-omni.fly.dev/ceo`
8. Reportar PASS/FAIL

## Notas

- NO usar frameworks externos (React, Vue, etc.) — vanilla HTML/CSS/JS
- NO usar CDN — todo inline, cero dependencias externas
- El dashboard debe funcionar sin conexión a internet (salvo los fetch al propio servidor)
- Inspiración visual: terminal/hacker estética, no corporate. El CEO es un ingeniero.
- Las 7 funciones son: Conservar, Captar, Depurar, Distribuir, Frontera, Adaptar, Replicar
- Las 3 lentes son: Salud, Sentido, Continuidad
- Las 21 celdas del heatmap son: {función}x{lente} (ej: ConservarxSalud, CaptarxSentido)
