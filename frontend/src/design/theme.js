/** Constantes del sistema de diseno Neural Dark */

// Usamos String.fromCodePoint para evitar que el bundler reemplace emojis
const E = (cp) => String.fromCodePoint(cp);

export const CAPAS = {
  operativo:  { label: 'Operativo',  icon: E(0x26A1),  modulos: ['agenda', 'calendario', 'buscar', 'grupos', 'wa'] },
  financiero: { label: 'Financiero', icon: E(0x1F4B0), modulos: ['pagos_pendientes', 'resumen_mes', 'facturas'] },
  cognitivo:  { label: 'Cognitivo',  icon: E(0x1F9E0), modulos: ['pizarra', 'estrategia', 'evaluacion', 'feed_cognitivo', 'bus'] },
  voz:        { label: 'Voz',        icon: E(0x1F4E2), modulos: ['voz_proactiva', 'voz'] },
  motor:      { label: 'Motor',      icon: E(0x2699),  modulos: ['motor'] },
  identidad:  { label: 'Identidad',  icon: E(0x1F9EC), modulos: ['adn', 'depuracion', 'readiness', 'engagement', 'contenido', 'presencia'] },
  autonomia:  { label: 'Autonomia',  icon: E(0x1F916), modulos: ['autonomia'] },
};

export const TABS_PROFUNDO = [
  { id: 'dashboard',    icon: E(0x1F4CA), label: 'Dashboard' },
  { id: 'diagnostico',  icon: E(0x1F52C), label: 'Diagnostico' },
  { id: 'organismo',    icon: E(0x1F9EC), label: 'Organismo' },
  { id: 'director',     icon: E(0x1F3BC), label: 'Director' },
  { id: 'consejo',      icon: E(0x1F9E0), label: 'Consejo' },
  { id: 'voz',          icon: E(0x1F4E2), label: 'Voz' },
  { id: 'adn',          icon: E(0x1F9EC), label: 'ADN' },
  { id: 'depuracion',   icon: E(0x1F5D1), label: 'Depuracion' },
  { id: 'contabilidad', icon: E(0x1F4B0), label: 'Contabilidad' },
  { id: 'contenido',    icon: E(0x1F4F1), label: 'Contenido' },
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
