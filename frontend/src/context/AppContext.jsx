import { createContext, useContext, useState, useEffect } from 'react';

const AppContext = createContext(null);

const API_KEY = import.meta.env.VITE_API_KEY || '';

export function AppProvider({ children }) {
  const [tenant, setTenant] = useState(null);
  const [lentes, setLentes] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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

  if (API_KEY) {
    headers['X-API-Key'] = API_KEY;
  }

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401) {
    console.error('API key invalida o no configurada');
    throw new Error('No autorizado');
  }

  if (res.status === 429) {
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
