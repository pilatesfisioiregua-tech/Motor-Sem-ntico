# B-ORG-F6B — Fase 6B: Interfaz Organismo + Voz Bidireccional

**Fecha:** 24 marzo 2026
**Estimación:** ~11h
**Prerequisito:** B-ORG-F3 (React Router, AppContext, SSE, design tokens) + B-ORG-F4 (motor.pensar, pizarras cognitiva/temporal)
**WIP:** 1
**Principios:** P64 (pizarras visibles), P66 (circuitos — feedback visible)

---

## OBJETIVO

Jesús deja de ver un CRM genérico y empieza a ver el ORGANISMO trabajando. 55 agentes funcionan pero hoy son invisibles. Pizarra invisible, Director invisible, Evaluador invisible, bus invisible.

**Antes:** Cockpit = agenda + pagos + alertas. Profundo = tabs estáticos. Voz = VoicePanel existe pero no conectado.
**Después:** Cockpit muestra el organismo pensando en tiempo real. Profundo tiene tabs organismo + director. Jesús habla al sistema y el sistema le responde.

---

## ESTADO ACTUAL FRONTEND

**EstudioCockpit.jsx:** Módulos por capas (CAPAS de theme.js). Tiene AgendaHoy, PagosPendientes, ResumenMes, AlertasPanel, BuscadorCliente, GruposPanel, Calendario, PanelWA, FeedEstudio. Falta: paneles del organismo.

**Profundo.jsx:** Ya tiene TabOrganismo (empezado), HeaderProfundo con lentes ACD, tabs de TABS_PROFUNDO. Tiene: dashboard, diagnóstico, organismo (parcial), director (parcial), consejo, voz, ADN, depuración, contabilidad.

**VoicePanel.jsx:** Ya implementado con Web Speech API (STT) + speechSynthesis (TTS). Exporta `speak()` y componente `VoicePanel({ onTranscript })`. Chrome desktop only.

**API endpoints existentes:**
- `GET /pilates/organismo/pizarra` → om_pizarra
- `GET /pilates/organismo/bus` → señales recientes
- `GET /pilates/organismo/director` → última ejecución Director Opus
- `GET /pilates/organismo/evaluacion` → última evaluación
- `GET /pilates/organismo/config-agentes` → om_config_agentes
- `GET /pilates/sse/pizarra` → SSE tiempo real (F3)

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
frontend/src/EstudioCockpit.jsx    ← Cockpit actual completo
frontend/src/Profundo.jsx          ← Tabs profundo completo
frontend/src/shared/VoicePanel.jsx ← Voice ya implementado
frontend/src/design/theme.js       ← CAPAS, TABS_PROFUNDO, ESTADO_ACD
frontend/src/api.js                ← Exports existentes
frontend/src/context/AppContext.jsx ← fetchApi (F3)
frontend/src/hooks/useSSE.js       ← SSE hook (F3)
src/pilates/router.py              ← Endpoints organismo existentes
src/pilates/cockpit.py             ← Funciones cockpit backend
```

---

## PASO 0: ENDPOINTS BACKEND NUEVOS (src/pilates/router.py)

### 0.1 Pizarra cognitiva (recetas del Director)

```python
@router.get("/organismo/pizarra-cognitiva")
async def get_pizarra_cognitiva():
    """Recetas del Director para cada función — lo que piensa el organismo."""
    from src.pilates.pizarras import leer_recetas_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    recetas = await leer_recetas_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "recetas": recetas, "total": len(recetas)}
```

### 0.2 Pizarra temporal (plan de ejecución)

```python
@router.get("/organismo/plan-temporal")
async def get_plan_temporal():
    """Plan de ejecución del ciclo — qué componentes corren y en qué orden."""
    from src.pilates.pizarras import leer_plan_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    plan = await leer_plan_ciclo("authentic_pilates", ciclo)
    return {"ciclo": ciclo, "plan": plan, "total": len(plan)}
```

### 0.3 Pizarra evolución (patrones aprendidos)

```python
@router.get("/organismo/patrones")
async def get_patrones():
    """Patrones aprendidos por el sistema — pizarra evolución."""
    from src.pilates.pizarras import leer_patrones
    patrones = await leer_patrones("authentic_pilates", min_confianza=0.3)
    return {"patrones": patrones, "total": len(patrones)}
```

### 0.4 Mediaciones recientes

```python
@router.get("/organismo/mediaciones")
async def get_mediaciones_recientes():
    """Conflictos cross-AF resueltos por el Mediador."""
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM om_mediaciones
            WHERE tenant_id = 'authentic_pilates'
            ORDER BY created_at DESC LIMIT 10
        """)
    return [dict(r) for r in rows]
```

### 0.5 Motor telemetría resumen

```python
@router.get("/organismo/motor-resumen")
async def get_motor_resumen():
    """Resumen del motor: gasto, caché hits, presupuesto."""
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        semana = await conn.fetch("""
            SELECT modelo, count(*) as calls, SUM(coste_usd) as coste,
                   SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
            FROM om_motor_telemetria
            WHERE tenant_id='authentic_pilates' AND created_at >= date_trunc('week', now())
            GROUP BY modelo ORDER BY coste DESC
        """)
    return {
        "presupuesto_restante": round(presupuesto_restante(), 2),
        "gastado_ciclo": round(_presupuesto_ciclo, 4),
        "por_modelo": [dict(r) for r in semana],
    }
```

### 0.6 Chat cockpit con contexto de pizarra

Editar el endpoint de chat del cockpit (si existe en `cockpit.py`) para que lea pizarra ANTES de llamar al LLM. Si Jesús pregunta "¿Qué piensa AF3?", el cockpit lee `om_pizarra_cognitiva WHERE funcion='F3'` y responde sin LLM.

Buscar la función de chat en `cockpit.py` y añadir al inicio:

```python
# Preguntas que se pueden responder leyendo la pizarra (sin LLM)
if any(p in pregunta.lower() for p in ["qué piensa", "que piensa", "estado de", "cómo está", "como esta"]):
    from src.pilates.pizarras import leer_recetas_ciclo, leer_patrones
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    recetas = await leer_recetas_ciclo("authentic_pilates", ciclo)
    patrones = await leer_patrones("authentic_pilates")
    # Inyectar como contexto al LLM
    contexto_pizarra = f"Recetas Director ({len(recetas)}): {json.dumps(recetas[:3], default=str)[:500]}\nPatrones ({len(patrones)}): {json.dumps(patrones[:3], default=str)[:500]}"
```

**Test 0.1:** `curl /pilates/organismo/pizarra-cognitiva` → JSON con recetas
**Test 0.2:** `curl /pilates/organismo/motor-resumen` → JSON con presupuesto

---

## PASO 1: API EXPORTS FRONTEND (frontend/src/api.js)

Añadir al final de api.js:

```js
// ORGANISMO — Paneles nuevos
export const getPizarraCognitiva = () => request('/organismo/pizarra-cognitiva');
export const getPlanTemporal = () => request('/organismo/plan-temporal');
export const getPatrones = () => request('/organismo/patrones');
export const getMediaciones = () => request('/organismo/mediaciones');
export const getMotorResumen = () => request('/organismo/motor-resumen');
export const getComunicaciones = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/comunicaciones${qs ? `?${qs}` : ''}`);
};
```

**Test 1.1:** Imports no fallan en el build

---

## PASO 2: 5 PANELES ORGANISMO PARA COCKPIT (~4h)

Crear: `frontend/src/panels/OrganismoPanel.jsx`

```jsx
/**
 * 5 paneles que hacen visible el organismo en el Cockpit.
 * Se montan en la capa "cognitivo" del Cockpit.
 */
import { useState, useEffect, useCallback } from 'react';
import Card from '../design/Card';
import Metric from '../design/Metric';
import Pulse from '../design/Pulse';
import AgentBadge from '../design/AgentBadge';
import { useSSE } from '../hooks/useSSE';
import * as api from '../api';


// ============================================================
// 1. PIZARRA PANEL — Estado del organismo agrupado por capas
// ============================================================

export function PizarraPanel() {
  const [pizarra, setPizarra] = useState(null);
  useEffect(() => { api.getOrganismoPizarra().then(setPizarra).catch(() => {}); }, []);

  // Actualizar en tiempo real via SSE
  useSSE('/pilates/sse/pizarra', useCallback((data) => {
    if (data.type === 'pizarra_actualizada') {
      api.getOrganismoPizarra().then(setPizarra).catch(() => {});
    }
  }, []));

  if (!pizarra) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando pizarra...</p>;

  const entries = Array.isArray(pizarra) ? pizarra : pizarra.entries || [];
  const byLayer = { sensorial: [], cognitiva: [], ejecutiva: [] };
  entries.forEach(e => {
    const layer = e.capa || 'ejecutiva';
    if (byLayer[layer]) byLayer[layer].push(e);
  });

  return (
    <div className="space-y-3">
      {Object.entries(byLayer).map(([layer, items]) => (
        items.length > 0 && (
          <div key={layer}>
            <h4 className="text-xs font-bold text-[var(--text-tertiary)] uppercase tracking-wider mb-1">
              {layer}
            </h4>
            {items.slice(0, 5).map((e, i) => (
              <div key={i} className="flex justify-between items-center py-1 border-b border-[var(--border)] text-sm">
                <span className="text-[var(--text-secondary)]">{e.clave || e.key}</span>
                <span className="font-mono text-xs text-[var(--text-primary)]">
                  {typeof e.valor === 'number' ? e.valor.toFixed(2) : String(e.valor || '').slice(0, 30)}
                </span>
              </div>
            ))}
          </div>
        )
      ))}
    </div>
  );
}


// ============================================================
// 2. ESTRATEGIA PANEL — Qué diseñó el Director Opus
// ============================================================

export function EstrategiaPanel() {
  const [director, setDirector] = useState(null);
  const [cognitiva, setCognitiva] = useState(null);

  useEffect(() => {
    api.getOrganismoDirector().then(setDirector).catch(() => {});
    api.getPizarraCognitiva().then(setCognitiva).catch(() => {});
  }, []);

  return (
    <div className="space-y-3">
      {director?.status === 'ok' ? (
        <>
          <div className="flex items-center gap-2 mb-2">
            <Pulse active />
            <span className="text-xs text-[var(--accent-violet)]">Director Opus activo</span>
          </div>
          <p className="text-sm text-[var(--text-secondary)]">
            {director.resumen || `${director.configs_aplicadas || 0} recetas diseñadas`}
          </p>
        </>
      ) : (
        <p className="text-[var(--text-tertiary)] text-sm">Director no ha ejecutado este ciclo</p>
      )}

      {cognitiva?.recetas?.length > 0 && (
        <div className="mt-2">
          <h4 className="text-xs font-bold text-[var(--text-tertiary)] uppercase mb-1">
            Recetas activas ({cognitiva.total})
          </h4>
          {cognitiva.recetas.slice(0, 4).map((r, i) => (
            <div key={i} className="py-1.5 border-b border-[var(--border)]">
              <div className="flex justify-between text-sm">
                <span className="font-semibold text-[var(--text-primary)]">{r.funcion}</span>
                <span className="text-xs text-[var(--accent-indigo)]">p{r.prioridad}</span>
              </div>
              {r.intencion && (
                <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{r.intencion.slice(0, 80)}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ============================================================
// 3. EVALUACIÓN PANEL — ¿Funcionó la prescripción?
// ============================================================

export function EvaluacionPanel() {
  const [evaluacion, setEvaluacion] = useState(null);
  useEffect(() => { api.getOrganismoEvaluacion().then(setEvaluacion).catch(() => {}); }, []);

  if (!evaluacion) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Sin evaluación aún</p>;

  const func = evaluacion.interpretacion?.evaluacion_global?.prescripcion_funciono;
  const deltas = evaluacion.comparacion?.deltas || {};

  return (
    <div>
      <div className={`text-center py-2 rounded-lg mb-3 ${
        func === true ? 'bg-emerald-500/10 text-emerald-400' :
        func === false ? 'bg-red-500/10 text-red-400' :
        'bg-amber-500/10 text-amber-400'
      }`}>
        <span className="text-sm font-bold">
          {func === true ? 'Prescripción funcionó' :
           func === false ? 'Prescripción no funcionó' :
           'Evaluación pendiente'}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Metric label="Salud" value={deltas.S ? `${deltas.S > 0 ? '+' : ''}${(deltas.S * 100).toFixed(0)}%` : '—'} size="sm"
                delta={deltas.S > 0 ? 1 : deltas.S < 0 ? -1 : 0} />
        <Metric label="Sentido" value={deltas.Se ? `${deltas.Se > 0 ? '+' : ''}${(deltas.Se * 100).toFixed(0)}%` : '—'} size="sm"
                delta={deltas.Se > 0 ? 1 : deltas.Se < 0 ? -1 : 0} />
        <Metric label="Continuidad" value={deltas.C ? `${deltas.C > 0 ? '+' : ''}${(deltas.C * 100).toFixed(0)}%` : '—'} size="sm"
                delta={deltas.C > 0 ? 1 : deltas.C < 0 ? -1 : 0} />
      </div>
    </div>
  );
}


// ============================================================
// 4. FEED COGNITIVO — Solo eventos del organismo (no ruido)
// ============================================================

export function FeedCognitivo() {
  const [signals, setSignals] = useState([]);
  useEffect(() => { api.getOrganismoBus().then(r => setSignals(r?.senales || [])).catch(() => {}); }, []);

  // Tiempo real via SSE
  useSSE('/pilates/sse/pizarra', useCallback((data) => {
    if (data.type === 'senal_urgente' || data.type === 'pizarra_actualizada') {
      api.getOrganismoBus().then(r => setSignals(r?.senales || [])).catch(() => {});
    }
  }, []));

  const typeColors = {
    ALERTA: 'text-red-400', PRESCRIPCION: 'text-violet-400',
    DIAGNOSTICO: 'text-cyan-400', ACCION: 'text-emerald-400',
    DATO: 'text-[var(--text-tertiary)]', OPORTUNIDAD: 'text-amber-400',
  };

  return (
    <div className="max-h-48 overflow-y-auto">
      {signals.length === 0 && <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Bus silencioso</p>}
      {signals.slice(0, 15).map((s, i) => (
        <div key={i} className="flex items-start gap-2 py-1.5 border-b border-[var(--border)]">
          <AgentBadge name={s.origen || '?'} size="xs" />
          <div className="flex-1 min-w-0">
            <span className={`text-xs font-bold ${typeColors[s.tipo_senal] || ''}`}>
              {s.tipo_senal}
            </span>
            <p className="text-xs text-[var(--text-secondary)] truncate">
              {s.contenido?.slice(0, 80) || JSON.stringify(s.payload)?.slice(0, 80)}
            </p>
          </div>
          <span className="text-[10px] text-[var(--text-ghost)] shrink-0">
            p{s.prioridad}
          </span>
        </div>
      ))}
    </div>
  );
}


// ============================================================
// 5. MOTOR PANEL — Presupuesto LLM y caché
// ============================================================

export function MotorPanel() {
  const [motor, setMotor] = useState(null);
  useEffect(() => { api.getMotorResumen().then(setMotor).catch(() => {}); }, []);

  if (!motor) return <p className="text-[var(--text-tertiary)] text-sm py-3 text-center">Cargando motor...</p>;

  const pctUsed = motor.presupuesto_restante > 0
    ? ((5 - motor.presupuesto_restante) / 5 * 100).toFixed(0)
    : 100;

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs text-[var(--text-tertiary)]">Presupuesto semanal</span>
        <span className="text-xs font-mono text-[var(--text-primary)]">
          ${motor.gastado_ciclo?.toFixed(2)} / $5.00
        </span>
      </div>
      <div className="w-full h-2 bg-[var(--bg-void)] rounded-full overflow-hidden mb-3">
        <div
          className={`h-full rounded-full transition-all ${
            pctUsed > 80 ? 'bg-red-500' : pctUsed > 50 ? 'bg-amber-500' : 'bg-emerald-500'
          }`}
          style={{ width: `${Math.min(100, pctUsed)}%` }}
        />
      </div>
      {motor.por_modelo?.length > 0 && (
        <div className="space-y-1">
          {motor.por_modelo.map((m, i) => (
            <div key={i} className="flex justify-between text-xs">
              <span className="text-[var(--text-secondary)]">{m.modelo?.split('/')[1] || m.modelo}</span>
              <span className="font-mono text-[var(--text-tertiary)]">
                {m.calls} calls · ${(m.coste || 0).toFixed(3)}
                {m.cache_hits > 0 && ` · ${m.cache_hits} cache`}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

**Test 2.1:** Build sin errores con los 5 paneles importados

---

## PASO 3: MONTAR PANELES EN COCKPIT (EstudioCockpit.jsx)

### 3.1 Importar paneles

Al inicio de EstudioCockpit.jsx, añadir:

```jsx
import { PizarraPanel, EstrategiaPanel, EvaluacionPanel, FeedCognitivo, MotorPanel } from './panels/OrganismoPanel';
```

### 3.2 Registrar módulos en el map de módulos inline

En EstudioCockpit.jsx hay un map que renderiza módulos por nombre. Buscar el patrón de renderizado (probablemente un switch/if o un objeto de componentes) y añadir los 5 nuevos:

```jsx
// Mapa de módulos → componentes
const MODULO_COMPONENTS = {
  agenda: AgendaHoy,
  calendario: () => <Calendario />,
  buscar: BuscadorCliente,
  grupos: GruposPanel,
  wa: () => <PanelWA />,
  pagos_pendientes: PagosPendientes,
  resumen_mes: ResumenMes,
  facturas: FacturasPanel,  // si existe
  // === NUEVOS: ORGANISMO ===
  pizarra: PizarraPanel,
  estrategia: EstrategiaPanel,
  evaluacion: EvaluacionPanel,
  feed_cognitivo: FeedCognitivo,
  bus: FeedCognitivo,  // alias
  // === NUEVO: MOTOR ===
  motor: MotorPanel,
};
```

**Nota:** Leer EstudioCockpit.jsx completo para encontrar el patrón exacto de renderizado. Puede ser un if/else, un switch, o un objeto. Adaptar a lo que haya.

### 3.3 Añadir capa "motor" a CAPAS (theme.js) si no existe

Si CAPAS no tiene una entrada para el motor:

```js
export const CAPAS = {
  operativo:  { label: 'Operativo',  icon: '\u26A1', modulos: ['agenda', 'calendario', 'buscar', 'grupos', 'wa'] },
  financiero: { label: 'Financiero', icon: '\uD83D\uDCB0', modulos: ['pagos_pendientes', 'resumen_mes', 'facturas'] },
  cognitivo:  { label: 'Cognitivo',  icon: '\uD83E\uDDE0', modulos: ['pizarra', 'estrategia', 'evaluacion', 'feed_cognitivo', 'bus'] },
  motor:      { label: 'Motor',      icon: '\u2699\uFE0F', modulos: ['motor'] },
  voz:        { label: 'Voz',        icon: '\uD83D\uDCE2', modulos: ['voz_proactiva', 'voz'] },
  identidad:  { label: 'Identidad',  icon: '\uD83E\uDDEC', modulos: ['adn', 'depuracion', 'readiness', 'engagement'] },
};
```

**Test 3.1:** Cockpit muestra panel "Pizarra" en capa cognitiva
**Test 3.2:** Cockpit muestra panel "Motor" con barra de presupuesto
**Test 3.3:** Feed Cognitivo se actualiza en tiempo real via SSE

---

## PASO 4: TABS PROFUNDO — Organismo + Director (~3h)

Profundo.jsx ya tiene un TabOrganismo empezado. Completarlo y añadir TabDirector.

### 4.1 Completar TabOrganismo

En Profundo.jsx, buscar `function TabOrganismo()` y completar. Debe mostrar:
- Pizarra agrupada por capas (sensorial/cognitiva/ejecutiva)
- Bus de señales en tiempo real
- Mediaciones recientes
- Gomas del motor perpetuo (visualización de las 6 gomas como cards de estado)

```jsx
function TabOrganismo() {
  const [pizarra, setPizarra] = useState(null);
  const [bus, setBus] = useState(null);
  const [configs, setConfigs] = useState(null);
  const [mediaciones, setMediaciones] = useState([]);
  const [patrones, setPatrones] = useState([]);
  const [motorResumen, setMotorResumen] = useState(null);

  useEffect(() => {
    api.getOrganismoPizarra().then(setPizarra).catch(() => {});
    api.getOrganismoBus().then(setBus).catch(() => {});
    api.getOrganismoConfigAgentes().then(setConfigs).catch(() => {});
    api.getMediaciones().then(setMediaciones).catch(() => {});
    api.getPatrones().then(r => setPatrones(r?.patrones || [])).catch(() => {});
    api.getMotorResumen().then(setMotorResumen).catch(() => {});
  }, []);

  const gomas = [
    { id: 'G1', label: 'Datos→Señales', desc: 'Negocio genera, AF escuchan' },
    { id: 'G2', label: 'Señales→Diagnóstico', desc: 'Bus acumula, ACD diagnostica' },
    { id: 'G3', label: 'Diagnóstico→Búsqueda', desc: 'Gaps generan queries' },
    { id: 'G4', label: 'Búsqueda→Prescripción', desc: 'Cognitiva diagnostica, Estratega prescribe' },
    { id: 'G5', label: 'Prescripción→Acción', desc: 'AF1-AF7 ejecutan via bus' },
    { id: 'G6', label: 'Acción→Aprendizaje', desc: 'Gestor registra, poda, promueve' },
  ];

  return (
    <div className="space-y-6 module-enter">
      {/* GOMAS */}
      <Card>
        <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Motor Perpetuo — 6 Gomas</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {gomas.map(g => (
            <div key={g.id} className="p-2 rounded-lg bg-[var(--bg-void)] border border-[var(--border)]">
              <div className="flex items-center gap-1 mb-1">
                <Pulse active size="xs" />
                <span className="text-xs font-bold text-[var(--accent-indigo)]">{g.id}</span>
              </div>
              <p className="text-[10px] text-[var(--text-secondary)]">{g.label}</p>
              <p className="text-[10px] text-[var(--text-ghost)]">{g.desc}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* MOTOR LLM */}
      {motorResumen && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Motor LLM</h3>
          <MotorPanel />
        </Card>
      )}

      {/* MEDIACIONES */}
      {mediaciones.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">
            Mediaciones ({mediaciones.length})
          </h3>
          {mediaciones.map((m, i) => {
            const res = typeof m.resolucion === 'string' ? JSON.parse(m.resolucion) : m.resolucion;
            return (
              <div key={i} className="py-2 border-b border-[var(--border)]">
                <div className="flex gap-1 mb-1">
                  {m.af_involucrados?.map(af => <AgentBadge key={af} name={af} size="xs" />)}
                </div>
                <p className="text-xs text-[var(--text-secondary)]">{res?.resolucion || res?.accion_final || ''}</p>
              </div>
            );
          })}
        </Card>
      )}

      {/* PATRONES APRENDIDOS */}
      {patrones.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">
            Patrones Aprendidos ({patrones.length})
          </h3>
          {patrones.slice(0, 5).map((p, i) => (
            <div key={i} className="py-2 border-b border-[var(--border)]">
              <div className="flex justify-between mb-1">
                <span className="text-xs font-bold text-[var(--accent-amber)]">{p.tipo}</span>
                <span className="text-[10px] text-[var(--text-ghost)]">
                  confianza {(p.confianza * 100).toFixed(0)}% · {p.evidencia_ciclos} ciclos
                </span>
              </div>
              <p className="text-xs text-[var(--text-secondary)]">{p.descripcion}</p>
            </div>
          ))}
        </Card>
      )}

      {/* BUS SEÑALES */}
      <Card>
        <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Bus de Señales</h3>
        <FeedCognitivo />
      </Card>
    </div>
  );
}
```

**Nota:** Importar `MotorPanel` y `FeedCognitivo` desde `panels/OrganismoPanel.jsx` al inicio de Profundo.jsx.

### 4.2 Crear TabDirector

```jsx
function TabDirector() {
  const [director, setDirector] = useState(null);
  const [cognitiva, setCognitiva] = useState(null);
  const [plan, setPlan] = useState(null);

  useEffect(() => {
    api.getOrganismoDirector().then(setDirector).catch(() => {});
    api.getPizarraCognitiva().then(setCognitiva).catch(() => {});
    api.getPlanTemporal().then(setPlan).catch(() => {});
  }, []);

  return (
    <div className="space-y-6 module-enter">
      {/* Estado Director */}
      <Card>
        <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">Director Opus</h3>
        {director?.status === 'ok' ? (
          <div>
            <div className="grid grid-cols-3 gap-2 mb-3">
              <Metric label="Configs" value={director.configs_aplicadas || 0} size="sm" />
              <Metric label="Tiempo" value={`${(director.tiempo_s || 0).toFixed(0)}s`} size="sm" />
              <Metric label="Modelo" value={director.modelo?.split('/')[1] || '—'} size="sm" />
            </div>
            {director.resumen && (
              <p className="text-sm text-[var(--text-secondary)] bg-[var(--bg-void)] p-3 rounded-lg">
                {director.resumen}
              </p>
            )}
          </div>
        ) : (
          <p className="text-[var(--text-tertiary)] text-sm">No ejecutado este ciclo</p>
        )}
      </Card>

      {/* Recetas (Pizarra Cognitiva) */}
      {cognitiva?.recetas?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">
            Partituras D_híbrido — Ciclo {cognitiva.ciclo}
          </h3>
          {cognitiva.recetas.map((r, i) => (
            <div key={i} className="py-3 border-b border-[var(--border)]">
              <div className="flex justify-between items-center mb-2">
                <span className="font-bold text-sm text-[var(--accent-violet)]">{r.funcion}</span>
                <span className="text-xs text-[var(--text-ghost)]">
                  {r.lente || '*'} · p{r.prioridad}
                </span>
              </div>
              {r.intencion && <p className="text-xs text-[var(--text-secondary)] mb-2">{r.intencion}</p>}
              <div className="flex flex-wrap gap-1">
                {(r.ints || []).map(int => (
                  <span key={int} className="px-1.5 py-0.5 rounded-full bg-[var(--accent-indigo-glow)] text-[var(--accent-indigo)] text-[10px] font-bold">
                    {int}
                  </span>
                ))}
                {(r.ps || []).map(p => (
                  <span key={p} className="px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-bold">
                    {p}
                  </span>
                ))}
              </div>
              {r.prompt_imperativo && (
                <details className="mt-2">
                  <summary className="text-[10px] text-[var(--text-ghost)] cursor-pointer">Ver prompt</summary>
                  <pre className="text-[10px] text-[var(--text-tertiary)] bg-[var(--bg-void)] p-2 rounded mt-1 whitespace-pre-wrap">
                    {r.prompt_imperativo?.slice(0, 300)}
                  </pre>
                </details>
              )}
            </div>
          ))}
        </Card>
      )}

      {/* Plan Temporal */}
      {plan?.plan?.length > 0 && (
        <Card>
          <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">
            Plan Temporal — {plan.ciclo}
          </h3>
          {plan.plan.map((p, i) => (
            <div key={i} className={`flex items-center gap-2 py-1.5 border-b border-[var(--border)] text-sm ${!p.activo ? 'opacity-40' : ''}`}>
              <span className="text-xs font-mono text-[var(--text-ghost)] w-6">{p.orden}</span>
              <span className="text-[var(--text-primary)]">{p.componente}</span>
              <span className="text-xs text-[var(--text-tertiary)] ml-auto">{p.fase}</span>
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
```

### 4.3 Registrar TabDirector y TabOrganismo en el render de tabs

Buscar donde se renderizan los tabs por id y asegurar que `organismo` → TabOrganismo y `director` → TabDirector:

```jsx
{tab === 'organismo' && <TabOrganismo />}
{tab === 'director' && <TabDirector />}
```

**Test 4.1:** Tab "Organismo" muestra gomas + mediaciones + patrones + bus
**Test 4.2:** Tab "Director" muestra recetas con INTs/Ps como badges coloreados

---

## PASO 5: VOZ BIDIRECCIONAL CONECTADA (~2h)

VoicePanel ya existe (STT + TTS). Solo falta CONECTAR al chat del cockpit.

### 5.1 En EstudioCockpit.jsx, conectar VoicePanel al chat

Buscar donde está el componente de chat del cockpit (puede ser un input + botón enviar). Añadir el VoicePanel al lado:

```jsx
import VoicePanel, { speak } from './shared/VoicePanel';

// En el chat input del cockpit:
<div className="flex items-center gap-2">
  <input
    className="flex-1 bg-[var(--bg-void)] border border-[var(--border)] rounded-[var(--radius-sm)] px-3 py-2 text-sm text-[var(--text-primary)] outline-none"
    placeholder="Pregunta al organismo..."
    value={chatInput}
    onChange={e => setChatInput(e.target.value)}
    onKeyDown={e => e.key === 'Enter' && handleSend()}
  />
  <VoicePanel onTranscript={(text) => {
    setChatInput(text);
    // Auto-enviar después de transcribir
    setTimeout(() => handleSend(text), 100);
  }} />
  <button onClick={() => handleSend()} className="px-3 py-2 rounded-[var(--radius-sm)] bg-[var(--accent-indigo)] text-white text-sm">
    Enviar
  </button>
</div>
```

### 5.2 TTS para respuestas del chat

En la función `handleSend` del cockpit, después de recibir respuesta:

```jsx
const handleSend = async (voiceText) => {
  const text = voiceText || chatInput;
  if (!text.trim()) return;
  setChatInput('');

  // ... enviar al API ...
  const response = await fetchApi('/pilates/cockpit/chat', {
    method: 'POST',
    body: JSON.stringify({ pregunta: text }),
  });

  // TTS: hablar la respuesta
  if (response.respuesta && voiceText) {
    speak(response.respuesta.slice(0, 300));  // Max 300 chars para TTS
  }

  // ... actualizar UI con respuesta ...
};
```

**Test 5.1:** Click micrófono → hablar → texto aparece → respuesta por altavoz
**Test 5.2:** Escribir texto en input → Enter → respuesta normal (sin voz)

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `src/pilates/router.py` | +5 endpoints organismo (cognitiva, temporal, patrones, mediaciones, motor-resumen) | 0 |
| `src/pilates/cockpit.py` | Chat lee pizarra antes de LLM | 0 |
| `frontend/src/api.js` | +6 exports organismo | 1 |
| `frontend/src/panels/OrganismoPanel.jsx` | **NUEVO** — 5 paneles (Pizarra, Estrategia, Evaluación, FeedCognitivo, Motor) | 2 |
| `frontend/src/EstudioCockpit.jsx` | +imports paneles + mapa módulos + VoicePanel conectado | 3, 5 |
| `frontend/src/design/theme.js` | +capa "motor" si no existe | 3 |
| `frontend/src/Profundo.jsx` | TabOrganismo completo + TabDirector nuevo | 4 |

## TESTS FINALES (PASS/FAIL)

```
T1:  npm run build → sin errores                                                     [PASS/FAIL]
T2:  curl /pilates/organismo/pizarra-cognitiva → JSON con recetas                    [PASS/FAIL]
T3:  curl /pilates/organismo/motor-resumen → JSON con presupuesto                    [PASS/FAIL]
T4:  Cockpit capa "cognitivo" → PizarraPanel visible                                 [PASS/FAIL]
T5:  Cockpit capa "cognitivo" → FeedCognitivo actualiza en tiempo real               [PASS/FAIL]
T6:  Cockpit → MotorPanel muestra barra presupuesto con %                            [PASS/FAIL]
T7:  Profundo tab "organismo" → gomas + mediaciones + patrones + bus                 [PASS/FAIL]
T8:  Profundo tab "director" → recetas con INTs como badges                          [PASS/FAIL]
T9:  Click micrófono en cockpit → STT transcribe → envía al chat                     [PASS/FAIL]
T10: Respuesta del chat → TTS habla por altavoz (si fue input de voz)                [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Añadir endpoints backend en router.py (Paso 0)
2. Añadir exports api.js (Paso 1)
3. Crear `frontend/src/panels/OrganismoPanel.jsx` (Paso 2)
4. Editar EstudioCockpit.jsx — importar + montar paneles + voice (Pasos 3, 5)
5. Editar Profundo.jsx — completar TabOrganismo + crear TabDirector (Paso 4)
6. Editar theme.js si necesario (Paso 3)
7. Editar cockpit.py — chat lee pizarra (Paso 0)
8. `npm run build` → verificar
9. Deploy
10. Verificar T1-T10

## NOTAS

- Los paneles muestran datos REALES. Si las pizarras están vacías (Director no ha ejecutado), los paneles muestran "Sin datos" o "No ejecutado". Cero regresión.
- VoicePanel ya existía — solo se conecta al chat. Web Speech API es gratis, solo funciona en Chrome desktop.
- FeedCognitivo se actualiza via SSE (creado en F3). Si SSE no está activo, los datos se cargan al montar el componente.
- Las gomas del motor perpetuo son una visualización ESTÁTICA informativa. En el futuro podrían mostrar estado real (cuándo giró cada goma por última vez).
- Coste total de F6B: $0 (todo frontend + endpoints de lectura).
