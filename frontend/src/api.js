/**
 * Cliente API para Exocortex Pilates.
 * Base URL configurable para dev/prod.
 */

const BASE = import.meta.env.VITE_API_URL || '';
const PREFIX = `${BASE}/pilates`;

async function request(path, options = {}) {
  const url = `${PREFIX}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Error ${res.status}`);
  }
  return res.json();
}

// GRUPOS
export const getGrupos = () => request('/grupos');
export const getGrupo = (id) => request(`/grupos/${id}`);
export const getAgendaGrupo = (id, fecha) =>
  request(`/grupos/${id}/agenda${fecha ? `?fecha=${fecha}` : ''}`);

// SESIONES
export const getSesionesHoy = () => request('/sesiones/hoy');
export const crearSesion = (data) => request('/sesiones', { method: 'POST', body: JSON.stringify(data) });
export const completarSesion = (id) => request(`/sesiones/${id}/completar`, { method: 'POST' });
export const marcarGrupo = (id, data) =>
  request(`/sesiones/${id}/marcar-grupo`, { method: 'POST', body: JSON.stringify(data) });

// CLIENTES
export const getClientes = () => request('/clientes');
export const getCliente = (id) => request(`/clientes/${id}`);
export const crearCliente = (data) => request('/clientes', { method: 'POST', body: JSON.stringify(data) });
export const buscar = (q) => request(`/buscar?q=${encodeURIComponent(q)}`);

// CONTRATOS
export const crearContrato = (data) => request('/contratos', { method: 'POST', body: JSON.stringify(data) });

// CARGOS + PAGOS
export const getCargos = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/cargos${qs ? `?${qs}` : ''}`);
};
export const registrarPago = (data) => request('/pagos', { method: 'POST', body: JSON.stringify(data) });
export const getResumen = () => request('/resumen');

// AUTOMATISMOS
export const generarSesionesSemana = () => request('/cron/generar-sesiones', { method: 'POST' });
export const getAlertas = () => request('/alertas');
export const bizumEntrante = (data) => request('/bizum-entrante', { method: 'POST', body: JSON.stringify(data) });
export const cronInicioSemana = () => request('/cron/inicio_semana', { method: 'POST' });
export const cronInicioMes = () => request('/cron/inicio_mes', { method: 'POST' });
