/**
 * Cliente API para Exocortex Pilates.
 * Auth via fetchApi (X-API-Key header automático).
 */

import { fetchApi } from './context/AppContext';

const PREFIX = '/pilates';

async function request(path, options = {}) {
  return fetchApi(`${PREFIX}${path}`, options);
}

// GRUPOS
export const getGrupos = () => request('/grupos');
export const getGrupo = (id) => request(`/grupos/${id}`);
export const getAgendaGrupo = (id, fecha) =>
  request(`/grupos/${id}/agenda${fecha ? `?fecha=${fecha}` : ''}`);

// SESIONES
export const getSesionesSemana = (fecha) =>
  request(`/sesiones/semana${fecha ? `?fecha=${fecha}` : ''}`);
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

// ONBOARDING
export const crearEnlaceOnboarding = (data) =>
  request('/onboarding/crear-enlace', { method: 'POST', body: JSON.stringify(data) });

// FACTURACIÓN
export const crearFactura = (data) => request('/facturas', { method: 'POST', body: JSON.stringify(data) });
export const getFacturas = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/facturas${qs ? `?${qs}` : ''}`);
};
export const getFactura = (id) => request(`/facturas/${id}`);
export const generarPdfFactura = (id) => request(`/facturas/${id}/pdf`, { method: 'POST' });
export const getPaqueteGestor = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/facturas/paquete-gestor${qs ? `?${qs}` : ''}`);
};

// WHATSAPP
export const getMensajesWA = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/whatsapp/mensajes${qs ? `?${qs}` : ''}`);
};
export const enviarMensajeWA = (data) => request('/whatsapp/enviar', { method: 'POST', body: JSON.stringify(data) });
export const marcarLeidoWA = (id) => request(`/whatsapp/marcar-leido/${id}`, { method: 'POST' });
export const confirmarManana = () => request('/whatsapp/confirmar-manana', { method: 'POST' });
export const responderLead = (data) => request('/whatsapp/responder-lead', { method: 'POST', body: JSON.stringify(data) });
export const getRespuestaSugerida = (data) =>
  request('/whatsapp/respuesta-sugerida', { method: 'POST', body: JSON.stringify(data) });

// ADN
export const getADN = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/adn${qs ? `?${qs}` : ''}`);
};
export const crearADN = (data) => request('/adn', { method: 'POST', body: JSON.stringify(data) });
export const actualizarADN = (id, data) => request(`/adn/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Procesos
export const getProcesos = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/procesos${qs ? `?${qs}` : ''}`);
};
export const crearProceso = (data) => request('/procesos', { method: 'POST', body: JSON.stringify(data) });

// Conocimiento
export const getConocimiento = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/conocimiento${qs ? `?${qs}` : ''}`);
};
export const crearConocimiento = (data) => request('/conocimiento', { method: 'POST', body: JSON.stringify(data) });
export const promoverADN = (id, data) => request(`/conocimiento/${id}/promover-adn`, { method: 'POST', body: JSON.stringify(data) });

// Tensiones
export const getTensiones = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/tensiones${qs ? `?${qs}` : ''}`);
};
export const crearTension = (data) => request('/tensiones', { method: 'POST', body: JSON.stringify(data) });

// Depuración
export const getDepuracion = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/depuracion${qs ? `?${qs}` : ''}`);
};
export const crearDepuracion = (data) => request('/depuracion', { method: 'POST', body: JSON.stringify(data) });
export const actualizarDepuracion = (id, data) => request(`/depuracion/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

// Readiness
export const getReadiness = () => request('/readiness');

// VOZ
export const generarPropuestasVoz = () => request('/voz/generar-propuestas', { method: 'POST' });
export const getPropuestasVoz = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/voz/propuestas${qs ? `?${qs}` : ''}`);
};
export const decidirPropuesta = (id, data) =>
  request(`/voz/propuestas/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
export const ejecutarPropuesta = (id) =>
  request(`/voz/propuestas/${id}/ejecutar`, { method: 'POST' });
export const consultarCapaA = (data) =>
  request('/voz/capa-a', { method: 'POST', body: JSON.stringify(data) });
export const getDatosCapaA = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/voz/capa-a/datos${qs ? `?${qs}` : ''}`);
};
export const getISP = (canal) => request(`/voz/isp/${canal}`);
export const guardarISP = (canal, data) =>
  request(`/voz/isp/${canal}`, { method: 'POST', body: JSON.stringify(data) });
export const getHistorialISP = () => request('/voz/isp');
export const getTelemetriaVoz = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/voz/telemetria${qs ? `?${qs}` : ''}`);
};

// SÉQUITO
export const convocarConsejo = (data) =>
  request('/consejo', { method: 'POST', body: JSON.stringify(data) });
export const getHistorialConsejo = () => request('/consejo/historial');
export const getDetalleConsejo = (id) => request(`/consejo/${id}`);
export const registrarDecision = (id, data) =>
  request(`/consejo/${id}/decision`, { method: 'POST', body: JSON.stringify(data) });
export const getAsesores = () => request('/asesores');

// STRIPE / COBROS
export const getCobrosRecurrentes = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/cobros-recurrentes${qs ? `?${qs}` : ''}`);
};
export const cronCobros = () => request('/cron/diario', { method: 'POST' });

// PORTAL PÚBLICO
export const chatPublico = (data) =>
  request('/publico/chat', { method: 'POST', body: JSON.stringify(data) });

// COCKPIT CHAT OPERATIVO
export const cockpitChat = (data) =>
  request('/cockpit/chat', { method: 'POST', body: JSON.stringify(data) });
export const cockpitConfirm = (data) =>
  request('/cockpit/confirm', { method: 'POST', body: JSON.stringify(data) });

// FEED
export const getFeed = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/feed${qs ? `?${qs}` : ''}`);
};
export const marcarLeidoFeed = (data) =>
  request('/feed/marcar-leido', { method: 'POST', body: JSON.stringify(data) });
export const getFeedCount = () => request('/feed/count');

// ORGANISMO
export const getOrganismoPizarra = () => request('/organismo/pizarra');
export const getOrganismoBus = () => request('/organismo/bus');
export const getOrganismoDirector = () => request('/organismo/director');
export const getOrganismoEvaluacion = () => request('/organismo/evaluacion');
export const getOrganismoConfigAgentes = () => request('/organismo/config-agentes');

// ORGANISMO — Paneles nuevos (F6B)
export const getPizarraCognitiva = () => request('/organismo/pizarra-cognitiva');
export const getPlanTemporal = () => request('/organismo/plan-temporal');
export const getPatrones = () => request('/organismo/patrones');
export const getMediaciones = () => request('/organismo/mediaciones');
export const getMotorResumen = () => request('/organismo/motor-resumen');
export const getComunicaciones = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/comunicaciones${qs ? `?${qs}` : ''}`);
};

// IDENTIDAD + CONTENIDO (F7)
export const getIdentidad = () => request('/identidad');
export const actualizarIdentidad = (data) => request('/identidad', { method: 'PATCH', body: JSON.stringify(data) });
export const getContenido = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return request(`/contenido${qs ? `?${qs}` : ''}`);
};
export const aprobarContenido = (id) => request(`/contenido/${id}/aprobar`, { method: 'POST' });
export const programarContenido = (id) => request(`/contenido/${id}/programar`, { method: 'POST', body: '{}' });
export const filtrarContenido = (data) => request('/contenido/filtrar', { method: 'POST', body: JSON.stringify(data) });
export const getCompetencia = () => request('/competencia');

// AUTONOMÍA + PREDICCIONES (F8)
export const getAutonomiaDashboard = () => request('/autonomia/dashboard');
export const getPredicciones = () => request('/predicciones');
