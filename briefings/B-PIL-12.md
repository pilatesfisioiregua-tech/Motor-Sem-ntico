# B-PIL-12: Modo Profundo — Dashboard + Briefing Semanal + Diagnóstico ACD

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (datos operativos), B-PIL-05 (automatismos), B-PIL-08 (facturas)
**Coste:** ~$0.01 por diagnóstico ACD (1 call LLM evaluador funcional)

---

## CONTEXTO

El Modo Estudio registra datos. El Modo Profundo los digiere. Jesús abre esto los lunes por la noche o fines de semana para entender qué pasa y decidir.

**Pantalla:** Nueva ruta `/profundo` — SPA separada del Modo Estudio. Pestañas: Dashboard, Diagnóstico ACD, Clientes, Contabilidad.

**Briefing del lunes:** Se genera automáticamente cada lunes. Resumen semanal con números, alertas, ACD y prescripción activa. Se envía por WA y se muestra en el Dashboard.

**Fuente:** Exocortex v2.1 S6.2, S10, S17.4

---

## FASE A: Backend — Briefing + Dashboard

### A1. Crear `src/pilates/briefing.py`

```python
"""Generador de Briefing Semanal — Authentic Pilates.

Produce un resumen ejecutivo con: números, tendencias, alertas, ACD.
Se genera cada lunes (cron) o bajo demanda.

Fuente: Exocortex v2.1 S17.4.
"""
from __future__ import annotations

import structlog
from datetime import date, timedelta
from typing import Optional

log = structlog.get_logger()

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


async def generar_briefing(semana_inicio: Optional[date] = None) -> dict:
    """Genera briefing semanal completo.

    Args:
        semana_inicio: Lunes de la semana a analizar. Default: lunes pasado.

    Returns:
        Dict con secciones: numeros, asistencia, financiero, alertas, acd, acciones.
    """
    if semana_inicio is None:
        hoy = date.today()
        semana_inicio = hoy - timedelta(days=hoy.weekday())  # Lunes de esta semana
        if hoy.weekday() == 0:  # Si es lunes, semana pasada
            semana_inicio -= timedelta(weeks=1)

    semana_fin = semana_inicio + timedelta(days=6)
    mes_actual = date.today().replace(day=1)

    pool = await _get_pool()
    async with pool.acquire() as conn:

        # === NÚMEROS SEMANA ===
        sesiones_semana = await conn.fetchval("""
            SELECT count(*) FROM om_sesiones
            WHERE tenant_id = $1 AND fecha >= $2 AND fecha <= $3
        """, TENANT, semana_inicio, semana_fin)

        asistencias = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistidas,
                count(*) FILTER (WHERE a.estado = 'no_vino') as faltas,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
        """, TENANT, semana_inicio, semana_fin)

        pct_asistencia = round(
            (asistencias["asistidas"] or 0) / max(asistencias["total"] or 1, 1) * 100, 1
        )

        # === FINANCIERO SEMANA ===
        ingresos_semana = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago <= $3
        """, TENANT, semana_inicio, semana_fin)

        # === FINANCIERO MES (acumulado) ===
        import calendar
        ultimo_dia_mes = mes_actual.replace(
            day=calendar.monthrange(mes_actual.year, mes_actual.month)[1])

        ingresos_mes = await conn.fetchval("""
            SELECT COALESCE(SUM(monto), 0) FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= $2 AND fecha_pago <= $3
        """, TENANT, mes_actual, ultimo_dia_mes)

        deuda_total = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE tenant_id = $1 AND estado = 'pendiente'
        """, TENANT)

        # === OCUPACIÓN ===
        ocupacion = await conn.fetchrow("""
            SELECT
                COALESCE(SUM(g.capacidad_max), 0) as plazas_totales,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.tenant_id = $1 AND c.tipo = 'grupo' AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
        """, TENANT)

        pct_ocupacion = round(
            (ocupacion["ocupadas"] or 0) / max(ocupacion["plazas_totales"] or 1, 1) * 100, 1
        )

        # === CLIENTES ===
        clientes_activos = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND estado = 'activo'
        """, TENANT)

        nuevos_semana = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_alta >= $2 AND fecha_alta <= $3
        """, TENANT, semana_inicio, semana_fin)

        bajas_semana = await conn.fetchval("""
            SELECT count(*) FROM om_cliente_tenant
            WHERE tenant_id = $1 AND fecha_baja >= $2 AND fecha_baja <= $3
        """, TENANT, semana_inicio, semana_fin)

        # === ALERTAS ===
        from src.pilates.automatismos import detectar_alertas_retencion
        alertas_result = await detectar_alertas_retencion()
        alertas = alertas_result.get("alertas", [])

        # === TOP DEUDORES ===
        deudores = await conn.fetch("""
            SELECT c.cliente_id, cl.nombre, cl.apellidos,
                   SUM(c.total) as deuda,
                   MIN(c.fecha_cargo) as desde
            FROM om_cargos c
            JOIN om_clientes cl ON cl.id = c.cliente_id
            WHERE c.tenant_id = $1 AND c.estado = 'pendiente'
            GROUP BY c.cliente_id, cl.nombre, cl.apellidos
            ORDER BY deuda DESC
            LIMIT 5
        """, TENANT)

        # === TENDENCIA ASISTENCIA (4 semanas) ===
        tendencia = []
        for i in range(4):
            sem_ini = semana_inicio - timedelta(weeks=i)
            sem_fin = sem_ini + timedelta(days=6)
            row = await conn.fetchrow("""
                SELECT
                    count(*) as total,
                    count(*) FILTER (WHERE a.estado = 'asistio') as asistidas
                FROM om_asistencias a
                JOIN om_sesiones s ON s.id = a.sesion_id
                WHERE a.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
            """, TENANT, sem_ini, sem_fin)
            pct = round((row["asistidas"] or 0) / max(row["total"] or 1, 1) * 100, 1)
            tendencia.append({
                "semana": str(sem_ini),
                "asistencia_pct": pct,
                "total": row["total"],
                "asistidas": row["asistidas"],
            })

        # === DIAGNÓSTICO ACD (último disponible) ===
        ultimo_acd = await conn.fetchrow("""
            SELECT * FROM om_diagnosticos_tenant
            WHERE tenant_id = $1
            ORDER BY created_at DESC LIMIT 1
        """, TENANT)

    # Construir briefing
    briefing = {
        "semana": f"{semana_inicio} a {semana_fin}",
        "generado": str(date.today()),

        "numeros": {
            "sesiones_semana": sesiones_semana,
            "asistencia_total": asistencias["total"] or 0,
            "asistencia_asistidas": asistencias["asistidas"] or 0,
            "asistencia_faltas": asistencias["faltas"] or 0,
            "asistencia_canceladas": asistencias["canceladas"] or 0,
            "asistencia_pct": pct_asistencia,
            "clientes_activos": clientes_activos,
            "nuevos_semana": nuevos_semana,
            "bajas_semana": bajas_semana,
        },

        "financiero": {
            "ingresos_semana": float(ingresos_semana),
            "ingresos_mes_acumulado": float(ingresos_mes),
            "deuda_pendiente": float(deuda_total),
            "top_deudores": [
                {"nombre": f"{d['nombre']} {d['apellidos']}",
                 "deuda": float(d["deuda"]),
                 "desde": str(d["desde"])}
                for d in deudores
            ],
        },

        "ocupacion": {
            "plazas_totales": ocupacion["plazas_totales"],
            "plazas_ocupadas": ocupacion["ocupadas"],
            "pct": pct_ocupacion,
        },

        "tendencia_asistencia": list(reversed(tendencia)),

        "alertas": alertas[:10],
        "total_alertas": len(alertas),

        "acd": {
            "tiene_diagnostico": ultimo_acd is not None,
            "estado": ultimo_acd["estado"] if ultimo_acd else None,
            "estado_tipo": ultimo_acd["estado_tipo"] if ultimo_acd else None,
            "lentes": dict(ultimo_acd["lentes"]) if ultimo_acd and ultimo_acd["lentes"] else None,
            "gap": float(ultimo_acd["gap"]) if ultimo_acd and ultimo_acd["gap"] else None,
            "prescripcion": dict(ultimo_acd["prescripcion"]) if ultimo_acd and ultimo_acd["prescripcion"] else None,
            "fecha": str(ultimo_acd["created_at"].date()) if ultimo_acd else None,
        },
    }

    # Generar texto para WA
    briefing["texto_wa"] = _generar_texto_wa(briefing)

    log.info("briefing_generado", semana=str(semana_inicio))
    return briefing


def _generar_texto_wa(b: dict) -> str:
    """Genera versión texto del briefing para enviar por WhatsApp."""
    n = b["numeros"]
    f = b["financiero"]
    o = b["ocupacion"]
    acd = b["acd"]

    texto = f"""*Briefing Semanal — Authentic Pilates*
_{b['semana']}_

*Asistencia:* {n['asistencia_pct']}% ({n['asistencia_asistidas']}/{n['asistencia_total']})
Faltas: {n['asistencia_faltas']} · Cancelaciones: {n['asistencia_canceladas']}

*Financiero:*
Ingresos semana: {f['ingresos_semana']:.0f}€
Ingresos mes: {f['ingresos_mes_acumulado']:.0f}€
Deuda pendiente: {f['deuda_pendiente']:.0f}€

*Ocupación:* {o['pct']}% ({o['plazas_ocupadas']}/{o['plazas_totales']} plazas)
Clientes: {n['clientes_activos']} activos ({'+' if n['nuevos_semana'] > 0 else ''}{n['nuevos_semana']} nuevos, -{n['bajas_semana']} bajas)
"""

    if b["total_alertas"] > 0:
        texto += f"\n⚠️ *{b['total_alertas']} alertas* de retención"

    if acd["tiene_diagnostico"]:
        texto += f"""

*Diagnóstico ACD:*
Estado: {acd['estado']} ({acd['estado_tipo']})"""
        if acd["lentes"]:
            texto += f"\nLentes: S={acd['lentes'].get('S','?')} Se={acd['lentes'].get('Se','?')} C={acd['lentes'].get('C','?')}"
        if acd["gap"]:
            texto += f" (gap={acd['gap']:.3f})"
        if acd["prescripcion"] and acd["prescripcion"].get("objetivo"):
            texto += f"\nObjetivo: {acd['prescripcion']['objetivo']}"

    return texto


async def generar_diagnostico_acd_tenant() -> dict:
    """Genera un diagnóstico ACD fresco del negocio usando datos reales.

    Lee om_grupos, om_contratos, om_sesiones, om_cargos, om_adn, om_procesos
    y construye un caso textual para el evaluador funcional del Motor vN.

    Returns: dict con diagnóstico completo almacenado en om_diagnosticos_tenant.
    """
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Recopilar datos reales para el caso
        clientes = await conn.fetchval(
            "SELECT count(*) FROM om_cliente_tenant WHERE tenant_id=$1 AND estado='activo'", TENANT)
        grupos = await conn.fetchval(
            "SELECT count(*) FROM om_grupos WHERE tenant_id=$1 AND estado='activo'", TENANT)
        contratos_grupo = await conn.fetchval(
            "SELECT count(*) FROM om_contratos WHERE tenant_id=$1 AND tipo='grupo' AND estado='activo'", TENANT)
        ingresos = await conn.fetchval("""
            SELECT COALESCE(SUM(monto),0) FROM om_pagos
            WHERE tenant_id=$1 AND fecha_pago >= date_trunc('month', CURRENT_DATE)
        """, TENANT)
        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id=$1", TENANT)
        adn = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id=$1 AND activo=true", TENANT)
        onboarding = await conn.fetchval(
            "SELECT count(*) FROM om_onboarding_instructor WHERE tenant_id=$1", TENANT)

        ocupacion = await conn.fetchrow("""
            SELECT COALESCE(SUM(capacidad_max),0) as total,
                (SELECT count(*) FROM om_contratos WHERE tenant_id=$1 AND tipo='grupo' AND estado='activo') as ocu
            FROM om_grupos WHERE tenant_id=$1 AND estado='activo'
        """, TENANT)
        pct_ocu = round((ocupacion["ocu"] or 0) / max(ocupacion["total"] or 1, 1) * 100, 0)

    # Construir caso textual
    caso = (
        f"Estudio de Pilates reformer en Logroño. {clientes} clientes activos, "
        f"{grupos} grupos activos, {pct_ocu}% ocupación. "
        f"Factura {float(ingresos):.0f}€/mes. "
        f"Operado por un único instructor-dueño (Jesús). "
        f"{'Sin' if procesos == 0 else f'{procesos}'} procesos documentados. "
        f"{'Sin' if adn == 0 else f'{adn}'} principios ADN codificados. "
        f"{'Sin' if onboarding == 0 else f'{onboarding}'} onboarding instructor registrado. "
        f"Todo el conocimiento tácito reside en el dueño."
    )

    # Ejecutar pipeline ACD
    try:
        from src.tcf.evaluador_funcional import evaluar_funcional
        vector_result = await evaluar_funcional(caso)

        from src.tcf.diagnostico import diagnosticar
        diag = await diagnosticar(caso)

        prescripcion_dict = None
        if diag.estado.tipo == 'desequilibrado':
            from src.tcf.prescriptor import prescribir
            presc = prescribir(diag)
            prescripcion_dict = {
                'ints': presc.ints, 'ps': presc.ps, 'rs': presc.rs,
                'secuencia': presc.secuencia, 'frenar': presc.frenar,
                'lente_objetivo': presc.lente_objetivo,
                'objetivo': presc.objetivo,
            }

        # Almacenar en om_diagnosticos_tenant
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO om_diagnosticos_tenant (
                    tenant_id, trigger, vector_funcional, lentes,
                    gradiente, gap, estado, estado_tipo,
                    perfil_lentes, repertorio, prescripcion,
                    resultado, coste_usd
                ) VALUES ($1, 'manual', $2::jsonb, $3::jsonb,
                    $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb,
                    'pendiente', $11)
                RETURNING id, created_at
            """, TENANT,
                vector_result.vector.to_dict() if hasattr(vector_result.vector, 'to_dict') else {},
                diag.estado_campo.lentes if hasattr(diag, 'estado_campo') else {},
                diag.estado_campo.gradiente if hasattr(diag, 'estado_campo') else 0,
                diag.estado_campo.gap if hasattr(diag, 'estado_campo') else 0,
                diag.estado.id if hasattr(diag.estado, 'id') else str(diag.estado),
                diag.estado.tipo if hasattr(diag.estado, 'tipo') else 'desconocido',
                str(diag.estado_campo.perfil) if hasattr(diag, 'estado_campo') else '',
                {},  # repertorio
                prescripcion_dict,
                vector_result.coste_usd + diag.coste_usd,
            )

        log.info("acd_tenant_diagnostico", estado=diag.estado.id if hasattr(diag.estado, 'id') else '?',
                 coste=vector_result.coste_usd + diag.coste_usd)

        return {
            "status": "ok",
            "diagnostico_id": str(row["id"]),
            "estado": diag.estado.id if hasattr(diag.estado, 'id') else str(diag.estado),
            "lentes": diag.estado_campo.lentes if hasattr(diag, 'estado_campo') else {},
            "prescripcion": prescripcion_dict,
        }

    except Exception as e:
        log.error("acd_tenant_error", error=str(e))
        return {"status": "error", "detail": str(e)}
```

### A2. Endpoints briefing/dashboard en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR:

```python
# ============================================================
# MODO PROFUNDO — BRIEFING + DASHBOARD + ACD
# ============================================================

@router.get("/briefing")
async def obtener_briefing(semana: Optional[date] = None):
    """Genera briefing semanal bajo demanda."""
    from src.pilates.briefing import generar_briefing
    return await generar_briefing(semana)


@router.post("/briefing/enviar-wa")
async def enviar_briefing_wa():
    """Genera briefing y lo envía por WhatsApp a Jesús."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    # Enviar por WA (necesita teléfono de Jesús configurado)
    import os
    tel_jesus = os.getenv("JESUS_TELEFONO", "")
    if tel_jesus:
        from src.pilates.whatsapp import enviar_texto
        await enviar_texto(tel_jesus, briefing["texto_wa"])
        return {"status": "enviado", "texto": briefing["texto_wa"]}
    return {"status": "generado_sin_envio", "texto": briefing["texto_wa"],
            "nota": "Configurar JESUS_TELEFONO en fly.io secrets"}


@router.post("/acd/diagnosticar")
async def diagnosticar_negocio():
    """Ejecuta diagnóstico ACD del negocio con datos reales.
    Coste: ~$0.01 (1 call LLM evaluador funcional).
    """
    from src.pilates.briefing import generar_diagnostico_acd_tenant
    return await generar_diagnostico_acd_tenant()


@router.get("/acd/historial")
async def historial_acd(limit: int = 10):
    """Historial de diagnósticos ACD del negocio."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, trigger, estado, estado_tipo, lentes, gap,
                   prescripcion, resultado, coste_usd, created_at
            FROM om_diagnosticos_tenant
            WHERE tenant_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """, TENANT, limit)
    return [_row_to_dict(r) for r in rows]


@router.get("/dashboard")
async def dashboard_profundo():
    """Dashboard completo Modo Profundo: briefing + ACD + tendencias."""
    from src.pilates.briefing import generar_briefing
    briefing = await generar_briefing()

    # Añadir datos extra para el dashboard
    pool = await _get_pool()
    async with pool.acquire() as conn:
        # Grupos con ocupación detallada
        grupos = await conn.fetch("""
            SELECT g.nombre, g.tipo, g.capacidad_max, g.precio_mensual,
                (SELECT count(*) FROM om_contratos c
                 WHERE c.grupo_id = g.id AND c.estado = 'activo') as ocupadas
            FROM om_grupos g
            WHERE g.tenant_id = $1 AND g.estado = 'activo'
            ORDER BY g.nombre
        """, TENANT)

        # Ingresos por mes (últimos 6 meses)
        ingresos_mensuales = await conn.fetch("""
            SELECT date_trunc('month', fecha_pago)::date as mes,
                   SUM(monto) as total
            FROM om_pagos
            WHERE tenant_id = $1 AND fecha_pago >= CURRENT_DATE - interval '6 months'
            GROUP BY mes ORDER BY mes
        """, TENANT)

        # Depuraciones activas
        depuraciones = await conn.fetch("""
            SELECT * FROM om_depuracion
            WHERE tenant_id = $1 AND estado IN ('propuesta', 'aprobada')
            ORDER BY created_at DESC LIMIT 5
        """, TENANT)

    briefing["grupos_detalle"] = [_row_to_dict(g) for g in grupos]
    briefing["ingresos_mensuales"] = [
        {"mes": str(r["mes"]), "total": float(r["total"])} for r in ingresos_mensuales
    ]
    briefing["depuraciones"] = [_row_to_dict(d) for d in depuraciones]

    return briefing
```

### A3. Añadir cron briefing semanal

**Archivo:** `@project/src/pilates/automatismos.py` — En la función `ejecutar_cron`, en el bloque `inicio_semana`, AÑADIR:

```python
        # Generar y almacenar briefing
        from src.pilates.briefing import generar_briefing
        resultados["briefing"] = await generar_briefing()
```

---

## FASE B: Frontend — Modo Profundo

### B1. Crear `frontend/src/Profundo.jsx`

```jsx
import { useState, useEffect } from 'react';
import * as api from './api';

const BASE = import.meta.env.VITE_API_URL || '';

export default function Profundo() {
  const [data, setData] = useState(null);
  const [tab, setTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [acdHistory, setAcdHistory] = useState(null);

  useEffect(() => { loadDashboard(); }, []);

  async function loadDashboard() {
    setLoading(true);
    try {
      const d = await fetch(`${BASE}/pilates/dashboard`).then(r => r.json());
      setData(d);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function loadACD() {
    const h = await fetch(`${BASE}/pilates/acd/historial`).then(r => r.json());
    setAcdHistory(h);
  }

  async function ejecutarACD() {
    const r = await fetch(`${BASE}/pilates/acd/diagnosticar`, { method: 'POST' }).then(r => r.json());
    alert(`Diagnóstico: ${r.estado || r.detail}`);
    loadDashboard();
    loadACD();
  }

  if (loading) return <div style={s.container}><p>Cargando...</p></div>;
  if (!data) return <div style={s.container}><p>Error cargando dashboard</p></div>;

  const n = data.numeros;
  const f = data.financiero;
  const o = data.ocupacion;
  const acd = data.acd;

  return (
    <div style={s.container}>
      <div style={s.header}>
        <h1 style={s.h1}>Modo Profundo</h1>
        <span style={{color:'#6b7280', fontSize:13}}>Authentic Pilates · {data.semana}</span>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {['dashboard','acd','grupos','contabilidad'].map(t => (
          <button key={t} onClick={() => { setTab(t); if(t==='acd' && !acdHistory) loadACD(); }}
            style={tab === t ? s.tabActive : s.tab}>
            {{dashboard:'Dashboard',acd:'Diagnóstico ACD',grupos:'Grupos',contabilidad:'Contabilidad'}[t]}
          </button>
        ))}
      </div>

      {/* DASHBOARD */}
      {tab === 'dashboard' && (
        <div>
          {/* KPIs */}
          <div style={s.grid4}>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Asistencia</div>
              <div style={s.kpiValue}>{n.asistencia_pct}%</div>
              <div style={s.kpiSub}>{n.asistencia_asistidas}/{n.asistencia_total} sesiones</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Ingresos mes</div>
              <div style={{...s.kpiValue, color:'#16a34a'}}>{f.ingresos_mes_acumulado.toFixed(0)}€</div>
              <div style={s.kpiSub}>Semana: {f.ingresos_semana.toFixed(0)}€</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Ocupación</div>
              <div style={s.kpiValue}>{o.pct}%</div>
              <div style={s.kpiSub}>{o.plazas_ocupadas}/{o.plazas_totales} plazas</div>
            </div>
            <div style={s.kpi}>
              <div style={s.kpiLabel}>Clientes</div>
              <div style={s.kpiValue}>{n.clientes_activos}</div>
              <div style={s.kpiSub}>+{n.nuevos_semana} -{n.bajas_semana} semana</div>
            </div>
          </div>

          {/* Deuda */}
          {f.deuda_pendiente > 0 && (
            <div style={{...s.card, borderLeft:'4px solid #ef4444'}}>
              <h3 style={s.cardTitle}>Deuda pendiente: {f.deuda_pendiente.toFixed(0)}€</h3>
              {f.top_deudores.map((d,i) => (
                <div key={i} style={{display:'flex', justifyContent:'space-between', padding:'4px 0',
                  fontSize:13}}>
                  <span>{d.nombre}</span>
                  <span style={{fontWeight:600, color:'#ef4444'}}>{d.deuda.toFixed(0)}€ (desde {d.desde})</span>
                </div>
              ))}
            </div>
          )}

          {/* Tendencia asistencia */}
          <div style={s.card}>
            <h3 style={s.cardTitle}>Tendencia asistencia (4 semanas)</h3>
            <div style={{display:'flex', gap:12, alignItems:'flex-end', height:80}}>
              {data.tendencia_asistencia.map((t,i) => (
                <div key={i} style={{flex:1, textAlign:'center'}}>
                  <div style={{
                    height: `${t.asistencia_pct * 0.7}px`,
                    background: t.asistencia_pct >= 80 ? '#22c55e' : t.asistencia_pct >= 60 ? '#eab308' : '#ef4444',
                    borderRadius: '4px 4px 0 0',
                    minHeight: 4,
                  }}/>
                  <div style={{fontSize:11, color:'#6b7280', marginTop:4}}>{t.asistencia_pct}%</div>
                  <div style={{fontSize:10, color:'#9ca3af'}}>{t.semana.slice(5)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ACD resumen */}
          {acd.tiene_diagnostico && (
            <div style={{...s.card, borderLeft:`4px solid ${acd.estado_tipo==='equilibrado'?'#22c55e':'#f97316'}`}}>
              <h3 style={s.cardTitle}>Diagnóstico ACD</h3>
              <div style={{fontSize:15, fontWeight:600}}>{acd.estado} ({acd.estado_tipo})</div>
              {acd.lentes && (
                <div style={{fontSize:13, color:'#6b7280', marginTop:4}}>
                  S={acd.lentes.S} · Se={acd.lentes.Se} · C={acd.lentes.C}
                  {acd.gap && ` · gap=${acd.gap.toFixed(3)}`}
                </div>
              )}
              {acd.prescripcion?.objetivo && (
                <div style={{marginTop:8, padding:8, background:'#f9fafb', borderRadius:6, fontSize:13}}>
                  Objetivo: <strong>{acd.prescripcion.objetivo}</strong>
                </div>
              )}
              <div style={{fontSize:11, color:'#9ca3af', marginTop:4}}>Último: {acd.fecha}</div>
            </div>
          )}

          {/* Alertas */}
          {data.total_alertas > 0 && (
            <div style={s.card}>
              <h3 style={s.cardTitle}>Alertas ({data.total_alertas})</h3>
              {data.alertas.slice(0,5).map((a,i) => (
                <div key={i} style={{padding:'6px 0', borderBottom:'1px solid #f3f4f6', fontSize:13}}>
                  <span style={{fontWeight:500}}>{a.nombre}</span>
                  <span style={{color:'#6b7280', marginLeft:8}}>{a.detalle}</span>
                </div>
              ))}
            </div>
          )}

          {/* Depuraciones F3 */}
          {data.depuraciones?.length > 0 && (
            <div style={{...s.card, borderLeft:'4px solid #8b5cf6'}}>
              <h3 style={s.cardTitle}>Depuración (F3) — lo que dejar de hacer</h3>
              {data.depuraciones.map((d,i) => (
                <div key={i} style={{padding:'6px 0', fontSize:13}}>
                  <div style={{fontWeight:500}}>{d.descripcion}</div>
                  <div style={{color:'#6b7280'}}>{d.impacto_estimado} · {d.estado}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ACD TAB */}
      {tab === 'acd' && (
        <div>
          <button style={s.btn} onClick={ejecutarACD}>
            Ejecutar diagnóstico ACD (~$0.01)
          </button>
          {acdHistory && (
            <div style={{marginTop:16}}>
              <h3 style={s.cardTitle}>Historial de diagnósticos</h3>
              {acdHistory.map((d,i) => (
                <div key={i} style={{...s.card, marginBottom:8}}>
                  <div style={{display:'flex', justifyContent:'space-between'}}>
                    <span style={{fontWeight:600}}>{d.estado} ({d.estado_tipo})</span>
                    <span style={{fontSize:12, color:'#9ca3af'}}>{String(d.created_at).slice(0,10)}</span>
                  </div>
                  {d.lentes && (
                    <div style={{fontSize:13, color:'#6b7280'}}>
                      S={d.lentes.S} Se={d.lentes.Se} C={d.lentes.C} gap={d.gap?.toFixed(3)}
                    </div>
                  )}
                  {d.prescripcion?.objetivo && (
                    <div style={{fontSize:13, marginTop:4}}>Objetivo: {d.prescripcion.objetivo}</div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* GRUPOS TAB */}
      {tab === 'grupos' && data.grupos_detalle && (
        <div>
          {data.grupos_detalle.map((g,i) => (
            <div key={i} style={s.card}>
              <div style={{display:'flex', justifyContent:'space-between'}}>
                <span style={{fontWeight:600}}>{g.nombre}</span>
                <span style={{
                  color: g.ocupadas >= g.capacidad_max ? '#ef4444' : '#16a34a',
                  fontWeight:600,
                }}>{g.ocupadas}/{g.capacidad_max}</span>
              </div>
              <div style={{fontSize:12, color:'#6b7280'}}>
                {g.tipo} · {parseFloat(g.precio_mensual).toFixed(0)}€/mes
              </div>
              {/* Barra ocupación */}
              <div style={{height:4, background:'#f3f4f6', borderRadius:2, marginTop:6}}>
                <div style={{
                  height:4, borderRadius:2,
                  width:`${(g.ocupadas/g.capacidad_max)*100}%`,
                  background: g.ocupadas >= g.capacidad_max ? '#ef4444' : '#22c55e',
                }}/>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* CONTABILIDAD TAB */}
      {tab === 'contabilidad' && (
        <div>
          <div style={s.card}>
            <h3 style={s.cardTitle}>Ingresos mensuales</h3>
            {data.ingresos_mensuales?.map((m,i) => (
              <div key={i} style={{display:'flex', justifyContent:'space-between', padding:'4px 0', fontSize:13}}>
                <span>{m.mes}</span>
                <span style={{fontWeight:600}}>{m.total.toFixed(0)}€</span>
              </div>
            ))}
          </div>
          <button style={{...s.btn, background:'#6b7280', marginTop:8}}
            onClick={() => window.open(`${BASE}/pilates/facturas/paquete-gestor`, '_blank')}>
            Descargar paquete gestor
          </button>
        </div>
      )}
    </div>
  );
}

const s = {
  container: { maxWidth:800, margin:'0 auto', padding:20, fontFamily:"'Inter',-apple-system,sans-serif" },
  header: { marginBottom:20 },
  h1: { fontSize:24, fontWeight:700, margin:0, color:'#111827' },
  tabs: { display:'flex', gap:4, marginBottom:20, borderBottom:'1px solid #e5e7eb', paddingBottom:8 },
  tab: { padding:'8px 16px', background:'none', border:'none', fontSize:13, color:'#6b7280', cursor:'pointer', borderRadius:'6px 6px 0 0' },
  tabActive: { padding:'8px 16px', background:'#6366f1', border:'none', fontSize:13, color:'#fff', cursor:'pointer', borderRadius:6 },
  grid4: { display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginBottom:16 },
  kpi: { background:'#fff', borderRadius:12, padding:16, boxShadow:'0 1px 3px rgba(0,0,0,0.08)' },
  kpiLabel: { fontSize:11, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.05em' },
  kpiValue: { fontSize:28, fontWeight:700, color:'#111827', marginTop:4 },
  kpiSub: { fontSize:12, color:'#6b7280', marginTop:2 },
  card: { background:'#fff', borderRadius:12, padding:16, marginBottom:12, boxShadow:'0 1px 3px rgba(0,0,0,0.08)' },
  cardTitle: { fontSize:14, fontWeight:600, color:'#374151', marginBottom:8 },
  btn: { padding:'10px 20px', background:'#6366f1', color:'#fff', border:'none', borderRadius:8, fontSize:14, fontWeight:500, cursor:'pointer' },
};
```

### B2. Routing + main.py

**Archivo:** `frontend/src/App.jsx` — AÑADIR import + routing:

```jsx
import Profundo from './Profundo';

// En el routing, antes del return principal:
  const profundoMatch = path.match(/^\/profundo$/);
  if (profundoMatch) {
    return <Profundo />;
  }
```

**Archivo:** `src/main.py` — AÑADIR ruta:

```python
    @app.get("/profundo")
    async def profundo_page():
        return FileResponse(frontend_dist / "index.html")
```

---

## Pass/fail

- `src/pilates/briefing.py` creado con generar_briefing + generar_diagnostico_acd_tenant
- GET /pilates/briefing genera briefing semanal completo con todas las secciones
- GET /pilates/dashboard devuelve briefing + grupos_detalle + ingresos_mensuales + depuraciones
- POST /pilates/briefing/enviar-wa genera y envía por WA (si JESUS_TELEFONO configurado)
- POST /pilates/acd/diagnosticar ejecuta pipeline ACD con datos reales (~$0.01)
- GET /pilates/acd/historial lista diagnósticos anteriores
- Frontend Profundo.jsx: 4 pestañas (Dashboard, ACD, Grupos, Contabilidad)
- KPIs: asistencia %, ingresos mes, ocupación %, clientes activos
- Tendencia asistencia 4 semanas con barras de color
- Sección ACD con estado + lentes + prescripción activa
- Alertas retención integradas
- Depuraciones F3 visibles
- Cron inicio_semana genera briefing automáticamente
