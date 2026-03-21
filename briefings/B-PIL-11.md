# B-PIL-11: Portal del Cliente — Autogestión Sesiones, Pagos, Recuperaciones, Facturas

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (endpoints backend), B-PIL-07 (onboarding links), B-PIL-08 (facturas)
**Coste:** $0

---

## CONTEXTO

Cada semana Jesús recibe docenas de mensajes WA tipo:
- "¿Cuántas clases llevo este mes?"
- "¿Puedo recuperar el jueves?"
- "¿Me envías la factura de febrero?"
- "No puedo ir mañana"

El portal elimina todo esto. Cada cliente accede con un enlace permanente (mismo patrón que onboarding) y se autogestiona.

**Fuente:** Exocortex v2.1 S16.4

**Principio:** El mismo token de onboarding, expandido. El cliente ya tiene un enlace — ahora ese enlace es su portal permanente.

---

## FASE A: Backend — Endpoints portal cliente

### A1. Migración: token permanente por cliente

**Archivo:** `@project/migrations/om_portal_cliente.sql`

```sql
-- Token permanente para portal del cliente (reutiliza om_onboarding_links)
-- Los enlaces completados se convierten en portal permanente
ALTER TABLE om_onboarding_links ADD COLUMN IF NOT EXISTS
    es_portal BOOLEAN DEFAULT false;

-- Índice para búsqueda rápida por cliente
CREATE INDEX IF NOT EXISTS idx_om_onboarding_portal
    ON om_onboarding_links(cliente_id) WHERE es_portal = true;
```

### A2. Crear `src/pilates/portal.py`

```python
"""Portal del Cliente — Autogestión.

Endpoints públicos (sin auth, acceso por token).
El cliente ve sus datos, sesiones, pagos, facturas.
Puede cancelar sesiones y solicitar recuperaciones.

Fuente: Exocortex v2.1 S16.4.
"""
from __future__ import annotations

import secrets
import structlog
from datetime import date, datetime, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

router = APIRouter(prefix="/portal", tags=["portal"])

TENANT = "authentic_pilates"


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


def _row_to_dict(row) -> dict:
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
    return d


async def _verificar_token(token: str) -> dict:
    """Verifica token de portal y devuelve datos del cliente."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        link = await conn.fetchrow("""
            SELECT l.*, c.nombre, c.apellidos, c.telefono, c.email
            FROM om_onboarding_links l
            JOIN om_clientes c ON c.id = l.cliente_id
            WHERE l.token = $1 AND l.tenant_id = $2
                AND l.estado = 'completado' AND l.es_portal = true
        """, token, TENANT)

        if not link:
            raise HTTPException(404, "Portal no encontrado. Contacta con el estudio.")

    return dict(link)


# ============================================================
# ACTIVAR PORTAL (interno — llamado tras completar onboarding)
# ============================================================

async def activar_portal(cliente_id: UUID) -> str:
    """Genera token de portal permanente para un cliente.
    
    Llamado automáticamente tras completar onboarding.
    Returns: token del portal.
    """
    pool = await _get_pool()
    token = secrets.token_urlsafe(32)

    async with pool.acquire() as conn:
        # Verificar si ya tiene portal
        existing = await conn.fetchval("""
            SELECT token FROM om_onboarding_links
            WHERE cliente_id = $1 AND tenant_id = $2 AND es_portal = true
        """, cliente_id, TENANT)
        if existing:
            return existing

        # Crear enlace portal (sin expiración)
        await conn.execute("""
            INSERT INTO om_onboarding_links (tenant_id, token, cliente_id,
                estado, es_portal, fecha_completado)
            VALUES ($1, $2, $3, 'completado', true, now())
        """, TENANT, token, cliente_id)

    log.info("portal_activado", cliente=str(cliente_id))
    return token


# ============================================================
# ENDPOINTS PÚBLICOS (acceso por token)
# ============================================================

@router.get("/{token}")
async def portal_home(token: str):
    """Página principal del portal: datos del cliente + resumen."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Contrato activo
        contrato = await conn.fetchrow("""
            SELECT co.*, g.nombre as grupo_nombre, g.dias_semana
            FROM om_contratos co
            LEFT JOIN om_grupos g ON g.id = co.grupo_id
            WHERE co.cliente_id = $1 AND co.tenant_id = $2 AND co.estado = 'activo'
            LIMIT 1
        """, cliente_id, TENANT)

        # Próximas sesiones (7 días)
        proximas = await conn.fetch("""
            SELECT s.id, s.fecha, s.hora_inicio, s.hora_fin, s.tipo,
                   g.nombre as grupo_nombre, a.estado as asistencia_estado, a.id as asistencia_id
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= CURRENT_DATE AND s.fecha <= CURRENT_DATE + 7
            ORDER BY s.fecha, s.hora_inicio
        """, cliente_id, TENANT)

        # Saldo pendiente
        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

        # Asistencia este mes
        mes = date.today().replace(day=1)
        stats = await conn.fetchrow("""
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE a.estado = 'asistio') as asistidas,
                count(*) FILTER (WHERE a.estado = 'no_vino') as faltas,
                count(*) FILTER (WHERE a.estado = 'cancelada') as canceladas
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $3 + interval '1 month'
        """, cliente_id, TENANT, mes)

    return {
        "cliente": {
            "nombre": link["nombre"],
            "apellidos": link["apellidos"],
            "telefono": link["telefono"],
            "email": link["email"],
        },
        "contrato": _row_to_dict(contrato) if contrato else None,
        "proximas_sesiones": [_row_to_dict(s) for s in proximas],
        "saldo_pendiente": float(saldo),
        "asistencia_mes": {
            "total": stats["total"] if stats else 0,
            "asistidas": stats["asistidas"] if stats else 0,
            "faltas": stats["faltas"] if stats else 0,
            "canceladas": stats["canceladas"] if stats else 0,
        },
    }


@router.get("/{token}/sesiones")
async def portal_sesiones(token: str, mes: Optional[date] = None):
    """Historial de sesiones del mes."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    mes = mes or date.today().replace(day=1)
    pool = await _get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT s.fecha, s.hora_inicio, s.hora_fin, s.tipo,
                   g.nombre as grupo_nombre, a.estado, a.es_recuperacion,
                   a.notas_instructor
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND s.fecha >= $3 AND s.fecha < $3 + interval '1 month'
            ORDER BY s.fecha DESC, s.hora_inicio DESC
        """, cliente_id, TENANT, mes)

    return {"mes": str(mes), "sesiones": [_row_to_dict(r) for r in rows]}


@router.post("/{token}/cancelar/{sesion_id}")
async def portal_cancelar(token: str, sesion_id: UUID):
    """El cliente cancela una sesión futura. Política auto-aplicada."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Verificar asistencia
        asistencia = await conn.fetchrow("""
            SELECT a.id, s.fecha, s.hora_inicio, s.tipo
            FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.sesion_id = $1 AND a.cliente_id = $2 AND a.estado = 'confirmada'
        """, sesion_id, cliente_id)

        if not asistencia:
            raise HTTPException(404, "Sesión no encontrada o ya cancelada")

        if asistencia["fecha"] < date.today():
            raise HTTPException(400, "No se pueden cancelar sesiones pasadas")

        # Calcular si hay cargo
        sesion_dt = datetime.combine(asistencia["fecha"], asistencia["hora_inicio"])
        horas_antes = (sesion_dt - datetime.now()).total_seconds() / 3600
        hay_cargo = horas_antes < 12 and asistencia["tipo"] == "individual"

        async with conn.transaction():
            await conn.execute("""
                UPDATE om_asistencias SET estado = 'cancelada', hora_cancelacion = now()
                WHERE id = $1
            """, asistencia["id"])

            if hay_cargo:
                # Cargo por cancelación tardía (solo individual)
                contrato = await conn.fetchrow("""
                    SELECT precio_sesion FROM om_contratos
                    WHERE cliente_id = $1 AND tenant_id = $2 AND tipo = 'individual' AND estado = 'activo'
                """, cliente_id, TENANT)
                precio = float(contrato["precio_sesion"]) if contrato and contrato["precio_sesion"] else 35.00
                await conn.execute("""
                    INSERT INTO om_cargos (tenant_id, cliente_id, tipo, descripcion,
                        base_imponible, sesion_id)
                    VALUES ($1, $2, 'cancelacion_tardia', $3, $4, $5)
                """, TENANT, cliente_id,
                    f"Cancelación tardía {asistencia['fecha']}", precio, sesion_id)

    log.info("portal_cancelacion", cliente=str(cliente_id), sesion=str(sesion_id),
             cargo=hay_cargo)
    return {
        "status": "cancelada",
        "cargo": hay_cargo,
        "mensaje": "Cancelación tardía — se aplicará cargo" if hay_cargo
                   else "Sesión cancelada sin cargo",
    }


@router.get("/{token}/recuperaciones")
async def portal_recuperaciones_disponibles(token: str):
    """Huecos disponibles para recuperar (grupos con plaza libre en los próximos 7 días)."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Verificar que tiene faltas para recuperar
        mes = date.today().replace(day=1)
        faltas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND a.estado = 'no_vino' AND s.fecha >= $3
        """, cliente_id, TENANT, mes)

        recuperaciones_hechas = await conn.fetchval("""
            SELECT count(*) FROM om_asistencias a
            JOIN om_sesiones s ON s.id = a.sesion_id
            WHERE a.cliente_id = $1 AND a.tenant_id = $2
                AND a.es_recuperacion = true AND a.estado = 'asistio'
                AND s.fecha >= $3
        """, cliente_id, TENANT, mes)

        if recuperaciones_hechas >= faltas:
            return {
                "puede_recuperar": False,
                "faltas": faltas,
                "recuperaciones": recuperaciones_hechas,
                "huecos": [],
                "mensaje": "No tienes faltas pendientes de recuperar",
            }

        # Buscar huecos: sesiones futuras de grupos con plaza libre
        hoy = date.today()
        huecos = await conn.fetch("""
            SELECT s.id as sesion_id, s.fecha, s.hora_inicio, s.hora_fin,
                   g.nombre as grupo_nombre, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a2
                    WHERE a2.sesion_id = s.id AND a2.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha > $2 AND s.fecha <= $2 + 7
                AND s.estado = 'programada'
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, hoy)

        huecos_libres = []
        for h in huecos:
            if h["ocupadas"] < h["capacidad_max"]:
                huecos_libres.append({
                    "sesion_id": str(h["sesion_id"]),
                    "fecha": str(h["fecha"]),
                    "hora": str(h["hora_inicio"])[:5],
                    "grupo": h["grupo_nombre"],
                    "plazas_libres": h["capacidad_max"] - h["ocupadas"],
                })

    return {
        "puede_recuperar": True,
        "faltas": faltas,
        "recuperaciones": recuperaciones_hechas,
        "huecos": huecos_libres,
    }


class SolicitudRecuperacion(BaseModel):
    sesion_id: UUID

@router.post("/{token}/recuperar")
async def portal_solicitar_recuperacion(token: str, data: SolicitudRecuperacion):
    """El cliente solicita recuperar en un hueco disponible.
    
    Jesús debe aprobar (1 clic en Modo Estudio).
    """
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        # Verificar que la sesión existe y tiene hueco
        sesion = await conn.fetchrow("""
            SELECT s.*, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a
                    WHERE a.sesion_id = s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as ocupadas
            FROM om_sesiones s
            JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.id = $1 AND s.tenant_id = $2
        """, data.sesion_id, TENANT)

        if not sesion:
            raise HTTPException(404, "Sesión no encontrada")
        if sesion["ocupadas"] >= sesion["capacidad_max"]:
            raise HTTPException(409, "Ya no hay plaza en este grupo")
        if sesion["fecha"] <= date.today():
            raise HTTPException(400, "Solo puedes recuperar en sesiones futuras")

        # Verificar que no está ya inscrito en esa sesión
        ya_inscrito = await conn.fetchval("""
            SELECT 1 FROM om_asistencias
            WHERE sesion_id = $1 AND cliente_id = $2
        """, data.sesion_id, cliente_id)
        if ya_inscrito:
            raise HTTPException(409, "Ya estás inscrito en esta sesión")

        # Crear asistencia como recuperación (estado 'recuperacion' = pendiente aprobación)
        await conn.execute("""
            INSERT INTO om_asistencias (tenant_id, sesion_id, cliente_id, estado, es_recuperacion)
            VALUES ($1, $2, $3, 'recuperacion', true)
        """, TENANT, data.sesion_id, cliente_id)

    log.info("portal_recuperacion_solicitada", cliente=str(cliente_id),
             sesion=str(data.sesion_id))
    return {
        "status": "solicitada",
        "mensaje": "Recuperación solicitada. Te confirmaremos por WhatsApp.",
    }


@router.get("/{token}/pagos")
async def portal_pagos(token: str, limit: int = 20):
    """Historial de pagos del cliente."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        pagos = await conn.fetch("""
            SELECT p.id, p.metodo, p.monto, p.fecha_pago, p.notas
            FROM om_pagos p
            WHERE p.cliente_id = $1 AND p.tenant_id = $2
            ORDER BY p.fecha_pago DESC
            LIMIT $3
        """, cliente_id, TENANT, limit)

        saldo = await conn.fetchval("""
            SELECT COALESCE(SUM(total), 0) FROM om_cargos
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'pendiente'
        """, cliente_id, TENANT)

    return {
        "pagos": [_row_to_dict(p) for p in pagos],
        "saldo_pendiente": float(saldo),
    }


@router.get("/{token}/facturas")
async def portal_facturas(token: str):
    """Facturas del cliente con enlace a PDF."""
    link = await _verificar_token(token)
    cliente_id = link["cliente_id"]
    pool = await _get_pool()

    async with pool.acquire() as conn:
        facturas = await conn.fetch("""
            SELECT id, numero_factura, fecha_emision, base_imponible,
                   iva_monto, total, estado
            FROM om_facturas
            WHERE cliente_id = $1 AND tenant_id = $2 AND estado = 'emitida'
            ORDER BY fecha_emision DESC
        """, cliente_id, TENANT)

    return {
        "facturas": [{
            **_row_to_dict(f),
            "pdf_url": f"/pilates/facturas/{f['id']}/pdf",
        } for f in facturas],
    }
```

---

## FASE B: Montar router portal en main.py

**Archivo:** `@project/src/main.py` — LEER PRIMERO. AÑADIR junto al mount del pilates router:

```python
# Mount Portal router (público, sin auth)
try:
    from src.pilates.portal import router as portal_router
    app.include_router(portal_router)
    log.info("portal_router_mounted")
except Exception as e:
    log.warning("portal_router_mount_failed", error=str(e))
```

---

## FASE C: Activar portal en onboarding

**Archivo:** `@project/src/pilates/router.py` — En el endpoint `completar_onboarding` (POST /onboarding/{token}/completar), AÑADIR al final de la transacción, antes de cerrar:

```python
            # 6. Activar portal del cliente
            from src.pilates.portal import activar_portal
            portal_token = await activar_portal(cliente_id)
```

Y en el return, AÑADIR:

```python
        "portal_url": f"https://motor-semantico-omni.fly.dev/portal/{portal_token}",
```

---

## FASE D: Endpoint para generar portal de clientes existentes

**Archivo:** `@project/src/pilates/router.py` — AÑADIR:

```python
@router.post("/portal/generar-todos")
async def generar_portales():
    """Genera portales para todos los clientes activos que no tienen uno.
    
    Útil para clientes creados antes de B-PIL-11.
    """
    from src.pilates.portal import activar_portal
    pool = await _get_pool()
    generados = 0

    async with pool.acquire() as conn:
        clientes = await conn.fetch("""
            SELECT ct.cliente_id FROM om_cliente_tenant ct
            LEFT JOIN om_onboarding_links l ON l.cliente_id = ct.cliente_id AND l.es_portal = true
            WHERE ct.tenant_id = $1 AND ct.estado = 'activo' AND l.id IS NULL
        """, TENANT)

    for c in clientes:
        await activar_portal(c["cliente_id"])
        generados += 1

    return {"status": "ok", "portales_generados": generados}
```

---

## FASE E: Frontend portal

### E1. Crear `frontend/src/Portal.jsx`

```jsx
import { useState, useEffect } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export default function Portal({ token }) {
  const [data, setData] = useState(null);
  const [view, setView] = useState('home');
  const [sesiones, setSesiones] = useState(null);
  const [recuperaciones, setRecuperaciones] = useState(null);
  const [pagos, setPagos] = useState(null);
  const [facturas, setFacturas] = useState(null);
  const [error, setError] = useState(null);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    fetch(`${BASE}/portal/${token}`)
      .then(r => { if (!r.ok) throw new Error('Portal no disponible'); return r.json(); })
      .then(setData)
      .catch(e => setError(e.message));
  }, [token]);

  async function loadView(v) {
    setView(v);
    try {
      if (v === 'sesiones' && !sesiones) {
        const r = await fetch(`${BASE}/portal/${token}/sesiones`).then(r => r.json());
        setSesiones(r);
      }
      if (v === 'recuperar' && !recuperaciones) {
        const r = await fetch(`${BASE}/portal/${token}/recuperaciones`).then(r => r.json());
        setRecuperaciones(r);
      }
      if (v === 'pagos' && !pagos) {
        const r = await fetch(`${BASE}/portal/${token}/pagos`).then(r => r.json());
        setPagos(r);
      }
      if (v === 'facturas' && !facturas) {
        const r = await fetch(`${BASE}/portal/${token}/facturas`).then(r => r.json());
        setFacturas(r);
      }
    } catch (e) { setError(e.message); }
  }

  async function cancelar(sesionId) {
    if (!confirm('¿Seguro que quieres cancelar esta sesión?')) return;
    try {
      const r = await fetch(`${BASE}/portal/${token}/cancelar/${sesionId}`, { method: 'POST' });
      const result = await r.json();
      setMsg(result.mensaje);
      // Reload
      const home = await fetch(`${BASE}/portal/${token}`).then(r => r.json());
      setData(home);
    } catch (e) { setError(e.message); }
  }

  async function solicitar_recuperacion(sesionId) {
    try {
      const r = await fetch(`${BASE}/portal/${token}/recuperar`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ sesion_id: sesionId }),
      });
      if (!r.ok) { const err = await r.json(); throw new Error(err.detail); }
      const result = await r.json();
      setMsg(result.mensaje);
      setRecuperaciones(null); // force reload
    } catch (e) { setMsg(e.message); }
  }

  if (error) return <div style={s.container}><div style={s.card}><p style={{color:'#ef4444'}}>{error}</p></div></div>;
  if (!data) return <div style={s.container}><div style={s.card}><p>Cargando...</p></div></div>;

  return (
    <div style={s.container}>
      <div style={s.card}>
        <h1 style={s.h1}>Authentic Pilates</h1>
        <p style={s.greeting}>Hola, {data.cliente.nombre}!</p>

        {msg && <div style={s.toast}>{msg} <span style={{cursor:'pointer'}} onClick={()=>setMsg(null)}>✕</span></div>}

        {/* Nav */}
        <div style={s.nav}>
          {['home','sesiones','recuperar','pagos','facturas'].map(v => (
            <button key={v} onClick={() => loadView(v)}
              style={view === v ? s.navActive : s.navBtn}>
              {{home:'Inicio',sesiones:'Sesiones',recuperar:'Recuperar',pagos:'Pagos',facturas:'Facturas'}[v]}
            </button>
          ))}
        </div>

        {/* HOME */}
        {view === 'home' && (
          <div>
            {data.contrato && (
              <div style={s.section}>
                <div style={s.label}>Tu servicio</div>
                <div style={s.value}>{data.contrato.grupo_nombre || 'Individual'}</div>
              </div>
            )}
            <div style={s.section}>
              <div style={s.label}>Este mes</div>
              <div style={{display:'flex',gap:16}}>
                <div><span style={s.big}>{data.asistencia_mes.asistidas}</span> asistidas</div>
                <div><span style={{...s.big, color:'#ef4444'}}>{data.asistencia_mes.faltas}</span> faltas</div>
              </div>
            </div>
            {data.saldo_pendiente > 0 && (
              <div style={{...s.section, background:'#fef2f2', borderRadius:8, padding:12}}>
                <div style={s.label}>Saldo pendiente</div>
                <div style={{...s.big, color:'#ef4444'}}>{data.saldo_pendiente.toFixed(2)}€</div>
              </div>
            )}
            <div style={s.section}>
              <div style={s.label}>Próximas sesiones</div>
              {data.proximas_sesiones.length === 0
                ? <p style={{color:'#9ca3af', fontSize:13}}>Sin sesiones programadas esta semana</p>
                : data.proximas_sesiones.map((ses, i) => (
                  <div key={i} style={s.row}>
                    <div>
                      <div style={{fontWeight:500}}>{ses.fecha} · {String(ses.hora_inicio).slice(0,5)}</div>
                      <div style={{fontSize:12, color:'#6b7280'}}>{ses.grupo_nombre || 'Individual'}</div>
                    </div>
                    {ses.asistencia_estado === 'confirmada' && (
                      <button style={s.btnDanger} onClick={() => cancelar(ses.id)}>No puedo ir</button>
                    )}
                  </div>
                ))
              }
            </div>
          </div>
        )}

        {/* SESIONES */}
        {view === 'sesiones' && sesiones && (
          <div>
            <div style={s.label}>Sesiones de {sesiones.mes}</div>
            {sesiones.sesiones.map((ses, i) => (
              <div key={i} style={s.row}>
                <div>
                  <div style={{fontWeight:500}}>{ses.fecha} · {String(ses.hora_inicio).slice(0,5)}</div>
                  <div style={{fontSize:12, color:'#6b7280'}}>{ses.grupo_nombre || 'Individual'}</div>
                </div>
                <span style={{
                  fontSize:11, padding:'2px 8px', borderRadius:4,
                  background: ses.estado === 'asistio' ? '#dcfce7' : ses.estado === 'no_vino' ? '#fee2e2' : '#f3f4f6',
                  color: ses.estado === 'asistio' ? '#16a34a' : ses.estado === 'no_vino' ? '#dc2626' : '#6b7280',
                }}>{ses.estado.replace('_',' ')}{ses.es_recuperacion ? ' (rec.)' : ''}</span>
              </div>
            ))}
          </div>
        )}

        {/* RECUPERAR */}
        {view === 'recuperar' && recuperaciones && (
          <div>
            {!recuperaciones.puede_recuperar
              ? <p style={{color:'#6b7280'}}>{recuperaciones.mensaje}</p>
              : (
                <>
                  <p style={{fontSize:13, marginBottom:12}}>
                    Tienes {recuperaciones.faltas - recuperaciones.recuperaciones} falta(s) por recuperar.
                  </p>
                  {recuperaciones.huecos.length === 0
                    ? <p style={{color:'#9ca3af'}}>No hay huecos disponibles esta semana</p>
                    : recuperaciones.huecos.map((h, i) => (
                      <div key={i} style={s.row}>
                        <div>
                          <div style={{fontWeight:500}}>{h.fecha} · {h.hora}</div>
                          <div style={{fontSize:12, color:'#6b7280'}}>{h.grupo} · {h.plazas_libres} plazas</div>
                        </div>
                        <button style={s.btn} onClick={() => solicitar_recuperacion(h.sesion_id)}>
                          Solicitar
                        </button>
                      </div>
                    ))
                  }
                </>
              )
            }
          </div>
        )}

        {/* PAGOS */}
        {view === 'pagos' && pagos && (
          <div>
            {pagos.saldo_pendiente > 0 && (
              <div style={{background:'#fef2f2', padding:12, borderRadius:8, marginBottom:12}}>
                Saldo pendiente: <strong>{pagos.saldo_pendiente.toFixed(2)}€</strong>
              </div>
            )}
            {pagos.pagos.map((p, i) => (
              <div key={i} style={s.row}>
                <div>
                  <div style={{fontWeight:500}}>{p.fecha_pago}</div>
                  <div style={{fontSize:12, color:'#6b7280'}}>{p.metodo}</div>
                </div>
                <span style={{fontWeight:600}}>{parseFloat(p.monto).toFixed(2)}€</span>
              </div>
            ))}
          </div>
        )}

        {/* FACTURAS */}
        {view === 'facturas' && facturas && (
          <div>
            {facturas.facturas.length === 0
              ? <p style={{color:'#9ca3af'}}>Sin facturas</p>
              : facturas.facturas.map((f, i) => (
                <div key={i} style={s.row}>
                  <div>
                    <div style={{fontWeight:500}}>{f.numero_factura}</div>
                    <div style={{fontSize:12, color:'#6b7280'}}>{f.fecha_emision}</div>
                  </div>
                  <div style={{textAlign:'right'}}>
                    <div style={{fontWeight:600}}>{parseFloat(f.total).toFixed(2)}€</div>
                    <a href={`${BASE}${f.pdf_url}`} target="_blank"
                      style={{fontSize:12, color:'#6366f1'}}>Descargar</a>
                  </div>
                </div>
              ))
            }
          </div>
        )}
      </div>
    </div>
  );
}

const s = {
  container: {
    minHeight:'100vh', display:'flex', alignItems:'flex-start', justifyContent:'center',
    background:'#f9fafb', padding:16, fontFamily:"'Inter',-apple-system,sans-serif",
  },
  card: { background:'#fff', borderRadius:16, padding:20, maxWidth:480, width:'100%',
    boxShadow:'0 4px 24px rgba(0,0,0,0.08)', marginTop:20 },
  h1: { fontSize:20, fontWeight:700, margin:0 },
  greeting: { fontSize:15, color:'#374151', marginTop:4 },
  nav: { display:'flex', gap:4, margin:'16px 0', overflowX:'auto' },
  navBtn: { padding:'6px 12px', borderRadius:6, border:'1px solid #e5e7eb', background:'#fff',
    fontSize:12, cursor:'pointer', whiteSpace:'nowrap' },
  navActive: { padding:'6px 12px', borderRadius:6, border:'none', background:'#6366f1',
    color:'#fff', fontSize:12, cursor:'pointer', whiteSpace:'nowrap' },
  section: { marginBottom:16 },
  label: { fontSize:11, color:'#9ca3af', textTransform:'uppercase', letterSpacing:'0.05em', marginBottom:4 },
  value: { fontSize:15, fontWeight:500 },
  big: { fontSize:22, fontWeight:700 },
  row: { display:'flex', justifyContent:'space-between', alignItems:'center',
    padding:'8px 0', borderBottom:'1px solid #f3f4f6' },
  btn: { padding:'6px 12px', borderRadius:6, background:'#6366f1', color:'#fff',
    border:'none', fontSize:12, cursor:'pointer' },
  btnDanger: { padding:'6px 12px', borderRadius:6, background:'#fee2e2', color:'#dc2626',
    border:'none', fontSize:12, cursor:'pointer' },
  toast: { background:'#ecfdf5', padding:'8px 12px', borderRadius:8, fontSize:13, marginBottom:12,
    display:'flex', justifyContent:'space-between' },
};
```

### E2. Integrar routing en App.jsx

**Archivo:** `@project/frontend/src/App.jsx` — AÑADIR import:

```jsx
import Portal from './Portal';
```

Y ANTES del routing de Onboarding, AÑADIR:

```jsx
  const portalMatch = path.match(/^\/portal\/(.+)$/);
  if (portalMatch) {
    return <Portal token={portalMatch[1]} />;
  }
```

### E3. Servir ruta /portal/{token} desde main.py

**Archivo:** `@project/src/main.py` — Donde se sirve /onboarding/{token}, AÑADIR:

```python
    @app.get("/portal/{token}")
    async def portal_page(token: str):
        return FileResponse(frontend_dist / "index.html")
```

---

## Pass/fail

- Migration om_portal_cliente.sql añade es_portal + índice
- GET /portal/{token} devuelve datos cliente + contrato + próximas sesiones + saldo + asistencia mes
- GET /portal/{token}/sesiones devuelve historial del mes
- POST /portal/{token}/cancelar/{sesion_id} cancela + aplica política cargo automático
- GET /portal/{token}/recuperaciones lista huecos con plazas libres
- POST /portal/{token}/recuperar crea asistencia de recuperación
- GET /portal/{token}/pagos lista pagos + saldo pendiente
- GET /portal/{token}/facturas lista facturas con enlace PDF
- POST /pilates/portal/generar-todos genera portales para clientes existentes
- Onboarding activa portal automáticamente al completar
- Frontend Portal.jsx: 5 vistas (inicio, sesiones, recuperar, pagos, facturas), responsive

---

## MENSAJES WA ELIMINADOS

| Antes (WA) | Ahora (portal) |
|-------------|----------------|
| "¿Cuántas clases llevo?" | Pestaña Inicio → asistencia mes |
| "¿Puedo recuperar el jueves?" | Pestaña Recuperar → ver huecos → solicitar |
| "No puedo ir mañana" | Próximas sesiones → botón "No puedo ir" |
| "¿Me envías la factura?" | Pestaña Facturas → descargar PDF |
| "¿Cuánto debo?" | Pestaña Pagos → saldo pendiente |
