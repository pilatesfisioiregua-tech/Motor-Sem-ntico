# B-ORG-F3 — Fase 3: Frontend Profesional + Pizarra Interfaz

**Fecha:** 24 marzo 2026
**Estimación:** ~12h
**Prerequisito:** B-ORG-PRODUCCION (F0+F1) + B-ORG-F2 (Pizarras+CQRS)
**WIP:** 1 (secuencial)
**Principios:** P64 (Cockpit lee pizarra interfaz), P65 (SSE tiempo real), P68 (eliminar > añadir)

---

## OBJETIVO

De "prototipo funcional dark-only" a "frontend profesional con 2 modos, mobile responsive, routing real, estado global, y tiempo real". El Cockpit deja de ser CAPAS hardcoded y pasa a leer Pizarra Interfaz.

---

## ESTADO ACTUAL DEL FRONTEND

```
frontend/
├── src/
│   ├── App.jsx              ← Routing manual con window.location.pathname
│   ├── main.jsx             ← StrictMode, sin Context
│   ├── api.js               ← ~150 exports, sin auth header, sin retry
│   ├── index.css            ← Dark-only, CSS vars + Tailwind v4
│   ├── EstudioCockpit.jsx   ← Módulos inline, CAPAS hardcoded de theme.js
│   ├── Onboarding.jsx       ← Inline styles, sin design tokens
│   ├── Portal.jsx           ← Inline styles
│   ├── PortalChat.jsx       ← Inline styles
│   ├── PortalPublico.jsx    ← Inline styles
│   ├── Profundo.jsx         ← Tabs de theme.js
│   ├── Calendario.jsx       ← Componente calendario
│   ├── PanelWA.jsx          ← Panel WhatsApp
│   ├── FeedEstudio.jsx      ← Feed de eventos
│   ├── Consejo.jsx          ← Séquito (24 asesores)
│   ├── design/              ← 8 componentes + theme.js (CAPAS, TABS, ESTADO_ACD)
│   └── shared/VoicePanel.jsx
├── package.json             ← React 19, Tailwind 4, Vite 8, framer-motion
```

**Problemas principales:**
1. Sin React Router — routing manual en App.jsx
2. Sin auth header — api.js no envía X-API-Key (F0 lo requiere)
3. Dark-only — clientes (onboarding, portal) ven tema oscuro
4. Sin mobile responsive — Cockpit no funciona en móvil
5. Sin error boundaries — un error en un módulo tumba toda la app
6. Sin estado global — cada módulo hace sus propias calls
7. CAPAS hardcoded — Cockpit no lee pizarra interfaz (P64)
8. Sin SSE — sin actualizaciones en tiempo real

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
frontend/src/App.jsx
frontend/src/main.jsx
frontend/src/api.js
frontend/src/index.css
frontend/src/design/theme.js
frontend/src/EstudioCockpit.jsx
frontend/src/Onboarding.jsx
frontend/src/PortalChat.jsx
frontend/src/PortalPublico.jsx
frontend/src/Profundo.jsx
frontend/package.json
```

---

## PASO 0: INSTALAR DEPENDENCIAS

```bash
cd motor-semantico/frontend
npm install react-router-dom
```

No instalar más dependencias — ya tiene Tailwind 4, framer-motion, react-hot-toast.

**Test 0.1:** `grep "react-router-dom" package.json` → match

---

## PASO 1: DESIGN TOKENS — Modo Light para clientes

El tema dark (Neural Dark) se mantiene para Jesús (Cockpit, Profundo). Los clientes (Onboarding, Portal, PortalChat, PortalPublico, tarjeta cumpleaños) necesitan tema light.

### 1.1 Añadir tokens light en index.css

Después de la sección `:root { ... }` existente, añadir:

```css
/* === AUTHENTIC LIGHT — tema para clientes === */
[data-theme="light"] {
  --bg-void: #f8f9fc;
  --bg-deep: #ffffff;
  --bg-surface: #ffffff;
  --bg-elevated: #f3f4f8;
  --bg-overlay: #e8eaf0;

  --text-primary: #1a1a2e;
  --text-secondary: #4a4a68;
  --text-tertiary: #8888a0;
  --text-ghost: #c0c0d0;

  --accent-indigo: #6366f1;
  --accent-indigo-dim: #4f46e5;
  --accent-indigo-glow: rgba(99, 102, 241, 0.10);
  --accent-green: #10b981;
  --accent-amber: #f59e0b;
  --accent-red: #ef4444;
  --accent-violet: #8b5cf6;
  --accent-cyan: #06b6d4;
  --accent-rose: #f43f5e;

  --border: rgba(0, 0, 0, 0.08);
  --border-active: rgba(99, 102, 241, 0.4);
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04);
  --shadow-elevated: 0 4px 16px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04);
  --shadow-glow: 0 0 20px var(--accent-indigo-glow);

  color: var(--text-primary);
  background: var(--bg-void);
}
```

### 1.2 Añadir @theme tokens para light (Tailwind v4)

Dentro del bloque `@theme` existente, los colores ya definidos sirven para dark. Para light, Tailwind v4 usa CSS variables que ya se overridean con `[data-theme="light"]`, así que no necesitamos duplicar `@theme`. Los componentes ya usan `var(--bg-surface)` etc. que se remap automáticamente.

**Test 1.1:** En browser, añadir `data-theme="light"` al `<html>` → fondo blanco, texto oscuro

---

## PASO 2: REACT ROUTER + LAYOUT (App.jsx + main.jsx)

### 2.1 Reescribir main.jsx

```jsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App.jsx';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
```

### 2.2 Reescribir App.jsx con React Router

```jsx
import { Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import ErrorBoundary from './shared/ErrorBoundary';

// Layouts
import DarkLayout from './layouts/DarkLayout';
import LightLayout from './layouts/LightLayout';

// Pages
import EstudioCockpit from './EstudioCockpit';
import Profundo from './Profundo';
import Onboarding from './Onboarding';
import PortalChat from './PortalChat';
import PortalPublico from './PortalPublico';
import NotFound from './shared/NotFound';

function App() {
  return (
    <AppProvider>
      <ErrorBoundary>
        <Routes>
          {/* Modo Estudio (dark) */}
          <Route element={<DarkLayout />}>
            <Route path="/" element={<EstudioCockpit />} />
            <Route path="/estudio" element={<EstudioCockpit />} />
            <Route path="/profundo" element={<Profundo />} />
          </Route>

          {/* Modo Cliente (light) */}
          <Route element={<LightLayout />}>
            <Route path="/portal/:token" element={<PortalChat />} />
            <Route path="/onboarding/:token" element={<Onboarding />} />
            <Route path="/info" element={<PortalPublico />} />
          </Route>

          {/* Tarjeta cumpleaños (light, sin layout) */}
          <Route path="/tarjeta/:token" element={<LightLayout><div>Cargando...</div></LightLayout>} />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </AppProvider>
  );
}

export default App;
```

**Nota:** Onboarding y PortalChat necesitan leer el token de la URL. Cambiar de `token` prop a `useParams()`:

En Onboarding.jsx, al inicio:
```jsx
import { useParams } from 'react-router-dom';
// ...
export default function Onboarding() {
  const { token } = useParams();
  // ... resto igual, eliminar prop token
```

En PortalChat.jsx, mismo cambio.

---

## PASO 3: LAYOUTS (nuevo directorio frontend/src/layouts/)

### 3.1 DarkLayout.jsx

```jsx
import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';

export default function DarkLayout() {
  useEffect(() => {
    document.documentElement.removeAttribute('data-theme');
  }, []);

  return <Outlet />;
}
```

### 3.2 LightLayout.jsx

```jsx
import { Outlet } from 'react-router-dom';
import { useEffect } from 'react';

export default function LightLayout({ children }) {
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', 'light');
    return () => document.documentElement.removeAttribute('data-theme');
  }, []);

  return children || <Outlet />;
}
```

**Test 3.1:** Navegar a `/onboarding/test` → fondo blanco. Navegar a `/estudio` → fondo oscuro.

---

## PASO 4: ERROR BOUNDARY + NOT FOUND

### 4.1 Crear frontend/src/shared/ErrorBoundary.jsx

```jsx
import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="max-w-md text-center">
            <h2 className="text-xl font-semibold mb-2 text-[var(--text-primary)]">
              Algo ha ido mal
            </h2>
            <p className="text-sm text-[var(--text-secondary)] mb-4">
              {this.state.error?.message || 'Error inesperado'}
            </p>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="px-4 py-2 rounded-[var(--radius-sm)] bg-[var(--accent-indigo)] text-white text-sm hover:opacity-90 transition"
            >
              Recargar
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
```

### 4.2 Crear frontend/src/shared/NotFound.jsx

```jsx
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-[var(--bg-void)]">
      <div className="max-w-md text-center">
        <div className="text-6xl mb-4">404</div>
        <h2 className="text-xl font-semibold mb-2 text-[var(--text-primary)]">
          Pagina no encontrada
        </h2>
        <Link to="/" className="text-[var(--accent-indigo)] text-sm hover:underline">
          Volver al inicio
        </Link>
      </div>
    </div>
  );
}
```

**Test 4.1:** Navegar a `/ruta-inexistente` → "Pagina no encontrada" con enlace a inicio

---

## PASO 5: CONTEXT GLOBAL + AUTH EN API

### 5.1 Crear frontend/src/context/AppContext.jsx

```jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react';

const AppContext = createContext(null);

const API_KEY = import.meta.env.VITE_API_KEY || '';

export function AppProvider({ children }) {
  const [tenant, setTenant] = useState(null);
  const [lentes, setLentes] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Cargar config del tenant desde pizarra dominio
    fetchApi('/pilates/pizarra/dominio')
      .then(data => setTenant(data))
      .catch(() => setTenant({ tenant_id: 'authentic_pilates', nombre: 'Authentic Pilates' }))
      .finally(() => setLoading(false));
  }, []);

  const value = { tenant, lentes, setLentes, loading };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}

// ============================================================
// FETCH WRAPPER CON AUTH + RETRY
// ============================================================

const BASE = import.meta.env.VITE_API_URL || '';

export async function fetchApi(path, options = {}) {
  const url = `${BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Añadir API key si está configurada
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    console.error('API key inválida o no configurada');
    throw new Error('No autorizado');
  }

  if (res.status === 429) {
    // Rate limited — reintentar una vez después de 2s
    await new Promise(r => setTimeout(r, 2000));
    const retry = await fetch(url, { ...options, headers });
    if (!retry.ok) {
      const err = await retry.json().catch(() => ({ detail: retry.statusText }));
      throw new Error(err.detail || `Error ${retry.status}`);
    }
    return retry.json();
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Error ${res.status}`);
  }

  return res.json();
}
```

### 5.2 Actualizar api.js para usar fetchApi

Al inicio de `api.js`, reemplazar la función `request` por:

```js
import { fetchApi } from './context/AppContext';

const PREFIX = '/pilates';

async function request(path, options = {}) {
  return fetchApi(`${PREFIX}${path}`, options);
}
```

Eliminar las variables `BASE` y `PREFIX` originales y la función `request` original.

**Test 5.1:** En dev, sin VITE_API_KEY → requests van sin header (endpoints públicos funcionan)
**Test 5.2:** Con VITE_API_KEY → requests llevan X-API-Key header

---

## PASO 6: MOBILE RESPONSIVE COCKPIT (EstudioCockpit.jsx)

El Cockpit actual es un grid fijo sin responsive. Necesita:

### 6.1 Sidebar collapsible

Antes del grid de módulos, añadir:

```jsx
const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768);
```

### 6.2 Grid adaptativo

Reemplazar el contenedor del grid. Buscar el div que contiene los módulos y cambiar las clases de grid:

De (buscar el grid de módulos):
```jsx
<div className="grid grid-cols-3 gap-3">
```

A:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
```

### 6.3 Bottom nav mobile

Después del sidebar y antes del grid principal, añadir para móvil:

```jsx
{/* Bottom nav mobile */}
<nav className="fixed bottom-0 left-0 right-0 bg-[var(--bg-surface)] border-t border-[var(--border)] flex justify-around py-2 md:hidden z-50">
  {Object.entries(CAPAS).map(([key, capa]) => (
    <button
      key={key}
      onClick={() => setCapaActiva(key)}
      className={`flex flex-col items-center text-xs px-2 py-1 rounded-lg transition
        ${capaActiva === key
          ? 'text-[var(--accent-indigo)] bg-[var(--accent-indigo-glow)]'
          : 'text-[var(--text-tertiary)]'}`}
    >
      <span className="text-lg">{capa.icon}</span>
      <span>{capa.label}</span>
    </button>
  ))}
</nav>
```

Y añadir padding-bottom al contenedor principal para no tapar con el bottom nav:

```jsx
<main className="pb-20 md:pb-0">
```

### 6.4 Header responsive

El header del Cockpit debe colapsar en móvil. Añadir un botón hamburguesa:

```jsx
<button
  className="md:hidden p-2 text-[var(--text-secondary)]"
  onClick={() => setSidebarOpen(!sidebarOpen)}
>
  <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M3 12h18M3 6h18M3 18h18" />
  </svg>
</button>
```

**Nota:** Leer EstudioCockpit.jsx completo antes de editar. Buscar los puntos de inserción exactos. Los cambios son quirúrgicos:
1. Añadir `sidebarOpen` state
2. Cambiar grid de 3 cols a responsive
3. Añadir bottom nav
4. Añadir padding-bottom

**Test 6.1:** En viewport 375px (móvil): bottom nav visible, grid 1 columna, sidebar colapsada
**Test 6.2:** En viewport 1280px (desktop): sin bottom nav, grid 3 columnas, sidebar visible

---

## PASO 7: COCKPIT LEE PIZARRA INTERFAZ (P64)

### 7.1 Endpoint backend: GET /pilates/pizarra/interfaz

En `src/pilates/router.py`, añadir:

```python
@router.get("/pizarra/dominio")
async def get_pizarra_dominio():
    """Lee la pizarra dominio del tenant."""
    from src.pilates.pizarras import leer_dominio
    return await leer_dominio()


@router.get("/pizarra/interfaz")
async def get_pizarra_interfaz():
    """Lee la pizarra interfaz para el ciclo actual."""
    from src.pilates.pizarras import leer_layout_ciclo
    from datetime import datetime
    from zoneinfo import ZoneInfo
    ahora = datetime.now(ZoneInfo("Europe/Madrid"))
    ciclo = f"W{ahora.isocalendar()[1]:02d}-{ahora.isocalendar()[0]}"
    layout = await leer_layout_ciclo("authentic_pilates", ciclo)

    # Si no hay layout en pizarra, devolver default de theme.js
    if not layout:
        return {"source": "default", "capas": {
            "operativo":  {"label": "Operativo",  "icon": "⚡", "modulos": ["agenda", "calendario", "buscar", "grupos", "wa"]},
            "financiero": {"label": "Financiero", "icon": "💰", "modulos": ["pagos_pendientes", "resumen_mes", "facturas"]},
            "cognitivo":  {"label": "Cognitivo",  "icon": "🧠", "modulos": ["pizarra", "estrategia", "evaluacion", "feed_cognitivo", "bus"]},
            "voz":        {"label": "Voz",        "icon": "📢", "modulos": ["voz_proactiva", "voz"]},
            "identidad":  {"label": "Identidad",  "icon": "🧬", "modulos": ["adn", "depuracion", "readiness", "engagement"]},
        }}

    return {"source": "pizarra", "ciclo": ciclo, "layout": layout}
```

### 7.2 Cockpit usa API con fallback a CAPAS

En EstudioCockpit.jsx, reemplazar el import estático de CAPAS por una carga dinámica:

```jsx
const [capas, setCapas] = useState(CAPAS); // CAPAS de theme.js como fallback

useEffect(() => {
  fetchApi('/pilates/pizarra/interfaz')
    .then(data => {
      if (data.capas) setCapas(data.capas);
    })
    .catch(() => {}); // Fallback a CAPAS hardcoded
}, []);
```

Luego, reemplazar las referencias a `CAPAS` por `capas` en el JSX (sidebar, grid, bottom nav).

**Test 7.1:** Con pizarra vacía → Cockpit usa CAPAS default (sin cambio visible)
**Test 7.2:** Con fila en om_pizarra_interfaz → Cockpit muestra layout de pizarra

---

## PASO 8: SSE PARA ACTUALIZACIONES TIEMPO REAL (P65)

### 8.1 Endpoint SSE backend (src/pilates/router.py)

```python
from fastapi.responses import StreamingResponse
import asyncio as _asyncio

@router.get("/sse/pizarra")
async def sse_pizarra():
    """SSE: retransmite cambios de pizarra en tiempo real."""
    async def event_generator():
        from src.db.client import get_pool
        pool = await get_pool()
        conn = await pool.acquire()

        # Escuchar notificaciones de pizarra
        queue = _asyncio.Queue()

        def on_notify(conn_ref, pid, channel, payload):
            queue.put_nowait(payload)

        await conn.add_listener("pizarra_actualizada", on_notify)
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"

        try:
            while True:
                try:
                    payload = await _asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {payload}\n\n"
                except _asyncio.TimeoutError:
                    yield f": keepalive\n\n"  # Mantiene conexión viva
        finally:
            await conn.remove_listener("pizarra_actualizada", on_notify)
            await pool.release(conn)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

### 8.2 Hook useFeed en frontend

Crear `frontend/src/hooks/useSSE.js`:

```js
import { useEffect, useRef, useCallback } from 'react';

const BASE = import.meta.env.VITE_API_URL || '';

export function useSSE(path, onMessage) {
  const sourceRef = useRef(null);

  useEffect(() => {
    const url = `${BASE}${path}`;
    const source = new EventSource(url);
    sourceRef.current = source;

    source.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.warn('SSE parse error:', e);
      }
    };

    source.onerror = () => {
      // Reconectar después de 5s
      source.close();
      setTimeout(() => {
        sourceRef.current = new EventSource(url);
      }, 5000);
    };

    return () => source.close();
  }, [path]);
}
```

### 8.3 Usar en EstudioCockpit

```jsx
import { useSSE } from './hooks/useSSE';

// Dentro del componente:
useSSE('/pilates/sse/pizarra', useCallback((data) => {
  if (data.type === 'pizarra_actualizada') {
    // Recargar el módulo afectado
    // Por ahora, recargar todo el resumen
    api.getResumen().then(setResumen).catch(() => {});
  }
}, []));
```

**Test 8.1:** `curl -N /pilates/sse/pizarra` → `data: {"type":"connected"}`, luego keepalives cada 30s
**Test 8.2:** INSERT en om_pagos → SSE emite evento → Cockpit se actualiza

---

## PASO 9: HOOK useFetch CON CACHE

Crear `frontend/src/hooks/useFetch.js`:

```js
import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchApi } from '../context/AppContext';

const cache = new Map();
const CACHE_TTL = 30_000; // 30 segundos

export function useFetch(path, options = {}) {
  const { enabled = true, ttl = CACHE_TTL } = options;
  const [data, setData] = useState(cache.get(path)?.data || null);
  const [loading, setLoading] = useState(!cache.has(path));
  const [error, setError] = useState(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchApi(path);
      setData(result);
      cache.set(path, { data: result, ts: Date.now() });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    if (!enabled) return;

    const cached = cache.get(path);
    if (cached && Date.now() - cached.ts < ttl) {
      setData(cached.data);
      setLoading(false);
      return;
    }

    refetch();
  }, [path, enabled, refetch]);

  return { data, loading, error, refetch };
}

export function invalidateCache(prefix) {
  for (const key of cache.keys()) {
    if (key.startsWith(prefix)) cache.delete(key);
  }
}
```

**Test 9.1:** Dos componentes que llaman al mismo endpoint → solo 1 fetch real en 30s

---

## PASO 10: MIGRAR ONBOARDING + PORTAL A LIGHT THEME

Los componentes de cliente (Onboarding, PortalChat, PortalPublico) usan inline styles con colores hardcoded. Al estar envueltos en LightLayout, los CSS vars ya se remapean.

### 10.1 Onboarding.jsx

Buscar inline styles tipo `style={{ background: '#fff' }}` o `style={{ color: '#333' }}` y reemplazar por clases Tailwind que usen CSS vars:

- `style={{ background: '#fff' }}` → `className="bg-[var(--bg-surface)]"`
- `style={{ color: '#333' }}` → `className="text-[var(--text-primary)]"`
- `style={{ borderColor: '#e0e0e0' }}` → `className="border-[var(--border)]"`

**Nota:** Leer cada archivo completo antes de editar. Hacer cambios quirúrgicos. Los archivos pueden ser largos.

### 10.2 PortalChat.jsx — mismo patrón

### 10.3 PortalPublico.jsx — mismo patrón

**Test 10.1:** Onboarding en dark mode del sistema → sigue con fondo claro (LightLayout lo controla)
**Test 10.2:** Colores de texto legibles en ambos modos

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `frontend/src/index.css` | +tokens light `[data-theme="light"]` | 1 |
| `frontend/src/main.jsx` | +BrowserRouter | 2 |
| `frontend/src/App.jsx` | **REESCRITO** — React Router + Layouts + ErrorBoundary | 2 |
| `frontend/src/layouts/DarkLayout.jsx` | **NUEVO** | 3 |
| `frontend/src/layouts/LightLayout.jsx` | **NUEVO** | 3 |
| `frontend/src/shared/ErrorBoundary.jsx` | **NUEVO** | 4 |
| `frontend/src/shared/NotFound.jsx` | **NUEVO** | 4 |
| `frontend/src/context/AppContext.jsx` | **NUEVO** — tenant + fetchApi con auth + retry | 5 |
| `frontend/src/api.js` | Usa fetchApi (auth), elimina request original | 5 |
| `frontend/src/EstudioCockpit.jsx` | Grid responsive + bottom nav + pizarra interfaz | 6, 7 |
| `frontend/src/hooks/useSSE.js` | **NUEVO** — SSE para tiempo real | 8 |
| `frontend/src/hooks/useFetch.js` | **NUEVO** — fetch con cache 30s | 9 |
| `frontend/src/Onboarding.jsx` | useParams() + tokens light | 2, 10 |
| `frontend/src/PortalChat.jsx` | useParams() + tokens light | 2, 10 |
| `frontend/src/PortalPublico.jsx` | tokens light | 10 |
| `src/pilates/router.py` | +endpoints pizarra/dominio, pizarra/interfaz, sse/pizarra | 7, 8 |

**ELIMINADO (P68):** Nada se elimina en esta fase. Los inline styles de Onboarding/Portal se reemplazan por Tailwind+tokens (mismas líneas, no más).

## TESTS FINALES (PASS/FAIL)

```
T1:  npm run build → sin errores                                                    [PASS/FAIL]
T2:  Navegar a / → Cockpit dark                                                     [PASS/FAIL]
T3:  Navegar a /onboarding/test → tema light                                        [PASS/FAIL]
T4:  Navegar a /ruta-inexistente → página 404                                       [PASS/FAIL]
T5:  Viewport 375px → bottom nav visible, grid 1 columna                            [PASS/FAIL]
T6:  Viewport 1280px → sin bottom nav, grid 3 columnas                              [PASS/FAIL]
T7:  curl /pilates/pizarra/interfaz → JSON con capas                                [PASS/FAIL]
T8:  curl /pilates/pizarra/dominio → JSON con config tenant                         [PASS/FAIL]
T9:  curl -N /pilates/sse/pizarra → event stream con connected + keepalives         [PASS/FAIL]
T10: grep "X-API-Key" frontend/src/context/AppContext.jsx → match                   [PASS/FAIL]
T11: grep "react-router-dom" frontend/package.json → match                          [PASS/FAIL]
T12: Error en un módulo del Cockpit → ErrorBoundary muestra "Algo ha ido mal"       [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Instalar dependencia: `npm install react-router-dom` (Paso 0)
2. Añadir tokens light en `index.css` (Paso 1)
3. Crear directorio `layouts/` + `context/` + `hooks/` + archivos nuevos (Pasos 3, 4, 5, 8, 9)
4. Reescribir `main.jsx` y `App.jsx` (Paso 2)
5. Actualizar `api.js` para usar fetchApi (Paso 5)
6. Editar `EstudioCockpit.jsx` — responsive + pizarra (Pasos 6, 7)
7. Editar `Onboarding.jsx`, `PortalChat.jsx`, `PortalPublico.jsx` — useParams + light (Pasos 2, 10)
8. Añadir endpoints backend en `router.py` (Pasos 7, 8)
9. `npm run build` → verificar sin errores
10. Deploy
11. Verificar T1-T12

## NOTAS

- El SSE endpoint de pizarra depende de que los triggers LISTEN/NOTIFY de F2 estén activos. Si no, el SSE solo emitirá keepalives (no falla, solo no tiene eventos).
- VITE_API_KEY es para desarrollo local. En producción (fly.dev), el frontend carga desde el mismo dominio → no necesita API key (CORS ya lo permite).
- La pizarra interfaz se llena cuando el Director Opus escribe en F4. Hasta entonces, el Cockpit usa el fallback (CAPAS de theme.js) — cero regresión.
- `react-router-dom` es la única dependencia nueva. Todo lo demás usa React 19 features (useCallback, etc.).
