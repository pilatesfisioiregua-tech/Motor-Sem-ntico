/** Constantes del sistema de diseno Neural Dark */

export const CAPAS = {
  operativo:  { label: 'Operativo',  icon: '⚡', modulos: ['agenda', 'calendario', 'buscar', 'grupos', 'wa'] },
  financiero: { label: 'Financiero', icon: '💰', modulos: ['pagos_pendientes', 'resumen_mes', 'facturas'] },
  cognitivo:  { label: 'Cognitivo',  icon: '🧠', modulos: ['pizarra', 'estrategia', 'evaluacion', 'feed_cognitivo', 'bus'] },
  voz:        { label: 'Voz',        icon: '📢', modulos: ['voz_proactiva', 'voz'] },
  motor:      { label: 'Motor',      icon: '⚙️', modulos: ['motor'] },
  identidad:  { label: 'Identidad',  icon: '🧬', modulos: ['adn', 'depuracion', 'readiness', 'engagement', 'contenido', 'presencia'] },
  autonomia:  { label: 'Autonomia',  icon: '🤖', modulos: ['autonomia'] },
};

export const TABS_PROFUNDO = [
  { id: 'dashboard',    icon: '📊', label: 'Dashboard' },
  { id: 'diagnostico',  icon: '🔬', label: 'Diagnostico' },
  { id: 'organismo',    icon: '🧬', label: 'Organismo' },
  { id: 'director',     icon: '🎼', label: 'Director' },
  { id: 'consejo',      icon: '🧠', label: 'Consejo' },
  { id: 'voz',          icon: '📢', label: 'Voz' },
  { id: 'adn',          icon: '🧬', label: 'ADN' },
  { id: 'depuracion',   icon: '🗑️', label: 'Depuracion' },
  { id: 'contabilidad', icon: '💰', label: 'Contabilidad' },
  { id: 'contenido',    icon: '📱', label: 'Contenido' },
];

export const ESTADO_ACD = {
  operador_ciego:       { color: 'amber',   label: 'Operador ciego' },
  genio_mortal:         { color: 'violet',  label: 'Genio mortal' },
  automata_eterno:      { color: 'red',     label: 'Automata eterno' },
  visionario_atrapado:  { color: 'cyan',    label: 'Visionario atrapado' },
  zombi_inmortal:       { color: 'rose',    label: 'Zombi inmortal' },
  potencial_dormido:    { color: 'emerald', label: 'Potencial dormido' },
  E1: { color: 'emerald', label: 'Equilibrado alto' },
  E2: { color: 'emerald', label: 'Equilibrado medio' },
  E3: { color: 'amber',   label: 'Equilibrado bajo' },
  E4: { color: 'emerald', label: 'Equilibrado maximo' },
};
