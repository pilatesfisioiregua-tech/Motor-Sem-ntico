# B-ORG-UI: Visibilidad del Organismo en la Interfaz

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — el organismo es invisible sin esto
**Dependencia:** Fase 1 + Fase 2 ejecutadas

---

## EL PROBLEMA

El organismo está vivo: 7 gomas giran, 9+ agentes ejecutan, G4 diagnostica INT×P×R, el recompilador modifica prompts. Pero Jesús no ve NADA de esto. El cockpit muestra agenda, pagos, feed de clientes. El feed publica cancelaciones y cobros. El bus, los AF, el enjambre, las prescripciones, las convergencias — todo invisible.

Es como tener el motor del coche funcionando sin instrumentos en el tablero.

## QUÉ HAY QUE HACER

### 1. FEED DEL ORGANISMO — Eventos del sistema visibles en el feed existente

Cada componente del organismo publica al feed cuando detecta algo relevante. El feed ya existe (`om_feed_estudio`) — solo hay que añadir helpers y llamadas.

### 2. MÓDULO COCKPIT "ORGANISMO" — Nuevo módulo en el cockpit

Dashboard del organismo: estado de gomas, agentes activos, último diagnóstico ACD, última prescripción, último recompilado, alertas de vigía, fixes del mecánico.

### 3. ENDPOINT DIAGNÓSTICO G4 — Para ver el diagnóstico cognitivo

Perfil INT×P×R detectado, disfunciones IC2-IC6, cadena causal, prescripción activa, configs de agentes.

### 4. ENDPOINT BUS — Para ver actividad del bus

Señales recientes, agrupadas por tipo, con prioridad.

---

## ARCHIVO 1: Ampliar feed.py

Añadir al final de `src/pilates/feed.py`:

```python
# ============================================================
# FEED DEL ORGANISMO — El sistema se hace visible
# ============================================================

async def feed_af_deteccion(agente: str, tipo: str, detalle: str,
                             cliente_id: UUID = None):
    """AF detectó algo: riesgo, ineficiencia, oportunidad, etc."""
    iconos = {
        "AF1": "🛡️", "AF2": "🎯", "AF3": "🗑️",
        "AF4": "⚖️", "AF6": "🔄", "AF7": "📖",
    }
    await publicar(
        f"organismo_{agente.lower()}", iconos.get(agente, "🤖"),
        f"{agente}: {tipo}", detalle[:200],
        cliente_id, "info" if "oportunidad" in tipo.lower() else "warning")


async def feed_af_veto(agente_origen: str, agente_bloqueado: str,
                        motivo: str, cliente_id: UUID = None):
    """Un AF vetó la acción de otro."""
    await publicar(
        "organismo_veto", "🚫",
        f"VETO: {agente_origen} bloquea {agente_bloqueado}",
        motivo[:200], cliente_id, "danger")


async def feed_convergencia(clientes: list[str], agentes: list[str], detalle: str):
    """Múltiples AF señalan al mismo cliente/grupo."""
    nombres = ", ".join(clientes[:3])
    await publicar(
        "organismo_convergencia", "🔗",
        f"Convergencia: {nombres}",
        f"{'+'.join(agentes)} coinciden. {detalle[:150]}",
        severidad="warning")


async def feed_diagnostico_acd(estado: str, s: float, se: float, c: float,
                                 cambio: str = None):
    """Resultado del diagnóstico ACD semanal."""
    await publicar(
        "organismo_acd", "🧠",
        f"Diagnóstico ACD: {estado}",
        f"S={s:.2f} Se={se:.2f} C={c:.2f}" + (f" — {cambio}" if cambio else ""),
        severidad="info")


async def feed_perfil_cognitivo(perfil: str, disfunciones: int, confianza: float):
    """Resultado del enjambre: perfil INT×P×R."""
    sev = "danger" if perfil in ("automata", "operador_ciego") else "warning" if perfil.startswith("E") is False else "info"
    await publicar(
        "organismo_perfil", "🔬",
        f"Perfil cognitivo: {perfil}",
        f"{disfunciones} disfunciones IC detectadas. Confianza: {confianza:.0%}",
        severidad=sev)


async def feed_prescripcion(resumen: str, agentes_afectados: int):
    """Prescripción del Estratega."""
    await publicar(
        "organismo_prescripcion", "💊",
        f"Prescripción Nivel 1",
        f"{resumen[:200]}. {agentes_afectados} agentes afectados.",
        severidad="info")


async def feed_recompilacion(agentes: list[str], cambios_estruct: int):
    """Recompilador modificó agentes."""
    nombres = ", ".join(agentes[:5])
    titulo = "Agentes reconfigurados" if cambios_estruct == 0 else "Recompilación + cambios estructurales pendientes CR1"
    sev = "info" if cambios_estruct == 0 else "warning"
    await publicar("organismo_recompilacion", "🔧", titulo,
                   f"Modificados: {nombres}", severidad=sev)


async def feed_vigia_alerta(tipo_alerta: str, detalle: str):
    """Vigía detectó un problema."""
    await publicar("organismo_vigia", "👁️", f"Vigía: {tipo_alerta}",
                   detalle[:200], severidad="warning")


async def feed_mecanico_fix(tipo_fix: str, detalle: str):
    """Mecánico reparó algo."""
    await publicar("organismo_mecanico", "🔨", f"Mecánico: {tipo_fix}",
                   detalle[:200], severidad="success")


async def feed_autofago(funciones_huerfanas: int, propuestas: int):
    """Autófago ejecutó la poda mensual."""
    await publicar("organismo_autofago", "♻️",
                   f"Autofagia mensual completada",
                   f"{funciones_huerfanas} funciones huérfanas, {propuestas} propuestas registradas.",
                   severidad="info")
```

## ARCHIVO 2: Nuevo endpoint dashboard organismo

Añadir en `src/pilates/router.py`:

```python
# ============================================================
# ORGANISMO — Dashboard del sistema cognitivo
# ============================================================

@router.get("/organismo/dashboard")
async def organismo_dashboard():
    """Dashboard completo del organismo: gomas, agentes, diagnóstico, bus."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Último diagnóstico ACD
        diag = await conn.fetchrow("""
            SELECT estado_pre, lentes_pre, vector_pre, metricas, created_at
            FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Último enjambre G4
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)

        # Configs activas de agentes (recompilador)
        configs = await conn.fetch("""
            SELECT agente, version, created_at, aprobada_por
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)

        # Bus: resumen últimas 48h
        bus_resumen = await conn.fetch("""
            SELECT tipo, count(*) as total, max(prioridad) as max_prioridad,
                   max(created_at) as ultimo
            FROM om_bus_senales
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '48 hours'
            GROUP BY tipo ORDER BY total DESC
        """)

        # Bus: señales de alta prioridad no procesadas
        urgentes = await conn.fetch("""
            SELECT tipo, origen, prioridad,
                   payload->>'descripcion' as descripcion,
                   created_at
            FROM om_bus_senales
            WHERE tenant_id='authentic_pilates'
                AND estado='pendiente' AND prioridad <= 3
            ORDER BY prioridad, created_at DESC LIMIT 10
        """)

        # Propiocepción: último snapshot
        propio = await conn.fetchrow("""
            SELECT datos, created_at FROM om_telemetria_sistema
            WHERE tenant_id='authentic_pilates'
            ORDER BY created_at DESC LIMIT 1
        """)

        # Actividad de agentes: quién emitió señales en los últimos 7 días
        agentes_activos = await conn.fetch("""
            SELECT origen, count(*) as señales, max(created_at) as ultimo
            FROM om_bus_senales
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '7 days'
            GROUP BY origen ORDER BY señales DESC
        """)

        # Feed organismo: últimas 10 noticias del sistema
        feed_org = await conn.fetch("""
            SELECT tipo, icono, titulo, detalle, severidad, created_at
            FROM om_feed_estudio
            WHERE tenant_id='authentic_pilates'
                AND tipo LIKE 'organismo_%'
            ORDER BY created_at DESC LIMIT 10
        """)

    import json

    def _safe(row):
        if not row:
            return None
        d = dict(row)
        for k, v in d.items():
            if hasattr(v, 'isoformat'):
                d[k] = v.isoformat()
            elif isinstance(v, (dict, list)):
                pass
            elif isinstance(v, str):
                try:
                    d[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    pass
        return d

    return {
        "diagnostico_acd": _safe(diag),
        "diagnostico_cognitivo_g4": _safe(g4),
        "configs_agentes": [_safe(c) for c in configs],
        "bus": {
            "resumen_48h": [_safe(r) for r in bus_resumen],
            "urgentes": [_safe(u) for u in urgentes],
        },
        "agentes_activos_7d": [_safe(a) for a in agentes_activos],
        "propiocepcion": _safe(propio),
        "feed_organismo": [_safe(f) for f in feed_org],
        "gomas": {
            "G1_datos_senales": True,
            "G2_senales_diagnostico": True,
            "G3_diagnostico_busqueda": True,
            "G4_busqueda_prescripcion": True,
            "G5_prescripcion_accion": True,
            "G6_accion_aprendizaje": True,
            "META_rotura_reparacion": True,
        },
    }


@router.get("/organismo/bus")
async def organismo_bus(horas: int = 48, limit: int = 50):
    """Señales del bus en las últimas N horas."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        señales = await conn.fetch(f"""
            SELECT id, tipo, origen, estado, prioridad,
                   payload, created_at
            FROM om_bus_senales
            WHERE tenant_id='authentic_pilates'
                AND created_at > now() - interval '{min(horas, 168)} hours'
            ORDER BY created_at DESC LIMIT {min(limit, 200)}
        """)
    import json
    return [{
        "id": str(s["id"]),
        "tipo": s["tipo"],
        "origen": s["origen"],
        "estado": s["estado"],
        "prioridad": s["prioridad"],
        "payload": s["payload"] if isinstance(s["payload"], dict) else json.loads(s["payload"]) if s["payload"] else {},
        "created_at": s["created_at"].isoformat(),
    } for s in señales]


@router.get("/organismo/diagnostico-cognitivo")
async def organismo_diagnostico_cognitivo():
    """Último diagnóstico G4 completo: perfil INT×P×R + disfunciones + prescripción."""
    from src.db.client import get_pool
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        g4 = await conn.fetchrow("""
            SELECT estado_acd_base, resultado_lentes, resultado_funciones,
                   resultado_clusters, señales_emitidas, tiempo_total_s, created_at
            FROM om_enjambre_diagnosticos
            ORDER BY created_at DESC LIMIT 1
        """)
        if not g4:
            return {"status": "sin_diagnostico", "mensaje": "Aún no se ha ejecutado el enjambre cognitivo."}

        # Lentes contiene repertorio + disfunciones
        lentes = g4["resultado_lentes"]
        if isinstance(lentes, str):
            lentes = json.loads(lentes)

        # Funciones contiene mecanismo causal o prescripción
        funciones = g4["resultado_funciones"]
        if isinstance(funciones, str):
            funciones = json.loads(funciones)

        # Clusters
        clusters = g4["resultado_clusters"]
        if isinstance(clusters, str):
            clusters = json.loads(clusters)

    return {
        "perfil": g4["estado_acd_base"],
        "repertorio_y_disfunciones": lentes,
        "mecanismo_causal_o_prescripcion": funciones,
        "clusters": clusters,
        "señales_emitidas": g4["señales_emitidas"],
        "tiempo_s": float(g4["tiempo_total_s"]) if g4["tiempo_total_s"] else 0,
        "fecha": g4["created_at"].isoformat(),
    }


@router.get("/organismo/config-agentes")
async def organismo_config_agentes():
    """Configuración INT×P×R actual de cada agente (recompilador)."""
    from src.db.client import get_pool
    import json
    pool = await get_pool()
    async with pool.acquire() as conn:
        configs = await conn.fetch("""
            SELECT agente, config, version, aprobada_por, created_at
            FROM om_config_agentes
            WHERE tenant_id='authentic_pilates' AND activa=TRUE
            ORDER BY agente
        """)
    return [{
        "agente": c["agente"],
        "config": c["config"] if isinstance(c["config"], dict) else json.loads(c["config"]),
        "version": c["version"],
        "aprobada_por": c["aprobada_por"],
        "fecha": c["created_at"].isoformat(),
    } for c in configs]
```

## ARCHIVO 3: Añadir módulo "organismo" al cockpit

En `src/pilates/cockpit.py`, añadir al dict MODULOS:

```python
    "organismo":        {"nombre": "Organismo cognitivo", "icono": "🧬", "endpoint": "/organismo/dashboard"},
    "diagnostico_cog":  {"nombre": "Diagnóstico INT×P×R", "icono": "🔬", "endpoint": "/organismo/diagnostico-cognitivo"},
```

Y añadir "organismo" a MODULOS_GRANDES:

```python
MODULOS_GRANDES = {"calendario", "sequito", "wa", "briefing", "organismo", "diagnostico_cog"}
```

## ARCHIVO 4: Integrar publicación al feed desde cada componente

### 4a. En `af1_conservacion.py` — al final de ejecutar_af1():

```python
    # Publicar al feed
    from src.pilates.feed import feed_af_deteccion
    for riesgo in riesgos:
        await feed_af_deteccion(
            "AF1", f"Riesgo: {riesgo.get('tipo', 'retención')}",
            f"{riesgo.get('nombre', 'Cliente')} — {riesgo.get('motivo', '')}",
            riesgo.get("cliente_id"))
```

### 4b. En `af3_depuracion.py` — al detectar VETOs:

```python
    from src.pilates.feed import feed_af_veto, feed_af_deteccion
    for det in detecciones:
        await feed_af_deteccion("AF3", det.get("tipo", "ineficiencia"), det.get("detalle", ""))
    for veto in vetos:
        await feed_af_veto("AF3", veto.get("agente_bloqueado", ""), veto.get("motivo", ""))
```

### 4c. En `diagnosticador.py` — al final de diagnosticar_tenant():

```python
    from src.pilates.feed import feed_diagnostico_acd
    await feed_diagnostico_acd(
        estado=resultado.get("estado", "desconocido"),
        s=lentes.get("S", 0), se=lentes.get("Se", 0), c=lentes.get("C", 0),
        cambio=resultado.get("cambio_vs_anterior"))
```

### 4d. En `compositor.py` — al final de ejecutar_g4():

```python
    from src.pilates.feed import feed_perfil_cognitivo, feed_prescripcion
    await feed_perfil_cognitivo(
        perfil=enjambre.get("perfil_detectado", "desconocido"),
        disfunciones=enjambre.get("disfunciones_encontradas", 0),
        confianza=control.get("confianza", 0))
    resumen = prescripcion.get("prescripcion_nivel_1", {}).get("secuencia", [])
    if resumen:
        primera = resumen[0]
        await feed_prescripcion(
            f"Fase 1: {primera.get('nombre', '')} — activar {', '.join(primera.get('activar_INT', []))}",
            len(prescripcion.get("prescripcion_nivel_1", {}).get("secuencia", [])))
```

### 4e. En `recompilador.py` — al final de recompilar():

```python
    from src.pilates.feed import feed_recompilacion
    await feed_recompilacion(
        resultado.get("agentes_modificados", []),
        len(resultado.get("cambios_estructurales", [])))
```

### 4f. En `vigia.py` — al detectar alertas:

```python
    from src.pilates.feed import feed_vigia_alerta
    for alerta in alertas:
        await feed_vigia_alerta(alerta.get("tipo", "sistema"), alerta.get("detalle", ""))
```

### 4g. En `mecanico.py` — al reparar:

```python
    from src.pilates.feed import feed_mecanico_fix
    for fix in fixes:
        await feed_mecanico_fix(fix.get("tipo", "fontanería"), fix.get("detalle", ""))
```

### 4h. En `ejecutor_convergencia.py` — al detectar convergencias:

```python
    from src.pilates.feed import feed_convergencia
    for conv in convergencias:
        await feed_convergencia(
            conv.get("clientes", []), conv.get("agentes", []), conv.get("detalle", ""))
```

### 4i. En `autofago.py` — al final de ejecutar_autofagia():

```python
    from src.pilates.feed import feed_autofago
    await feed_autofago(
        result["codigo_muerto"]["funciones_huerfanas"],
        result["propuestas_registradas"])
```

## TESTS

### TEST 1: Dashboard devuelve estructura completa
```bash
curl -s $BASE/organismo/dashboard | jq 'keys'
# Debe incluir: diagnostico_acd, diagnostico_cognitivo_g4, configs_agentes,
# bus, agentes_activos_7d, propiocepcion, feed_organismo, gomas
```

### TEST 2: Bus devuelve señales
```bash
curl -s "$BASE/organismo/bus?horas=168" | jq 'length'
# Debe ser > 0 si el cron ha ejecutado
```

### TEST 3: Diagnóstico cognitivo devuelve perfil
```bash
curl -s $BASE/organismo/diagnostico-cognitivo | jq '.perfil'
# Debe devolver el perfil detectado o "sin_diagnostico"
```

### TEST 4: Config agentes devuelve configs activas
```bash
curl -s $BASE/organismo/config-agentes | jq '.[].agente'
# Debe listar los agentes reconfigurados (si G4+recompilación ya ejecutó)
```

### TEST 5: Feed incluye eventos del organismo
```bash
curl -s "$BASE/feed?limit=20" | jq '.[] | select(.tipo | startswith("organismo_")) | .titulo'
# Debe mostrar eventos del organismo
```

### TEST 6: Cockpit incluye módulo organismo
```bash
curl -s $BASE/cockpit | jq '.modulos[] | select(.id == "organismo")'
# Debe devolver el módulo con endpoint /organismo/dashboard
```

---

## RESULTADO

Tras este briefing, Jesús abre el cockpit y ve:

1. **Feed** — mezclado con eventos de clientes: "🛡️ AF1: Riesgo retención — María lleva 3 semanas sin venir", "🚫 VETO: AF3 bloquea AF2 — no captar para grupo infrautilizado", "🧠 Diagnóstico ACD: E3", "🔬 Perfil cognitivo: genio_mortal, 3 disfunciones IC", "💊 Prescripción Nivel 1: activar INT-12+P12+R04", "🔧 Agentes reconfigurados: AF3, AF7, EJECUTOR"

2. **Módulo Organismo** — dashboard con gomas, agentes activos, bus, alertas urgentes, último diagnóstico, última recompilación

3. **Módulo Diagnóstico INT×P×R** — perfil cognitivo completo, disfunciones IC2-IC6, cadena causal, prescripción activa

El sistema ya no es invisible. Jesús VE el organismo pensar.
