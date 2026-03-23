/** Constantes del sistema de diseño Neural Dark */

export const CAPAS = {
  operativo:  { label: 'Operativo',  icon: '\u26A1', modulos: ['agenda', 'calendario', 'buscar', 'grupos', 'wa'] },
  financiero: { label: 'Financiero', icon: '\uD83D\uDCB0', modulos: ['pagos_pendientes', 'resumen_mes', 'facturas'] },
  cognitivo:  { label: 'Cognitivo',  icon: '\uD83E\uDDE0', modulos: ['pizarra', 'estrategia', 'evaluacion', 'feed_cognitivo', 'bus'] },
  voz:        { label: 'Voz',        icon: '\uD83D\uDCE2', modulos: ['voz_proactiva', 'voz'] },
  identidad:  { label: 'Identidad',  icon: '\uD83E\uDDEC', modulos: ['adn', 'depuracion', 'readiness', 'engagement'] },
};

export const TABS_PROFUNDO = [
  { id: 'dashboard',    icon: '\uD83D\uDCCA', label: 'Dashboard' },
  { id: 'diagnostico',  icon: '\uD83D\uDD2C', label: 'Diagn\u00F3stico' },
  { id: 'organismo',    icon: '\uD83E\uDDEC', label: 'Organismo' },
  { id: 'director',     icon: '\uD83C\uDFBC', label: 'Director' },
  { id: 'consejo',      icon: '\uD83E\uDDE0', label: 'Consejo' },
  { id: 'voz',          icon: '\uD83D\uDCE2', label: 'Voz' },
  { id: 'adn',          icon: '\uD83E\uDDEC', label: 'ADN' },
  { id: 'depuracion',   icon: '\uD83D\uDDD1\uFE0F', label: 'Depuraci\u00F3n' },
  { id: 'contabilidad', icon: '\uD83D\uDCB0', label: 'Contabilidad' },
];

export const ESTADO_ACD = {
  operador_ciego:       { color: 'amber',   label: 'Operador ciego' },
  genio_mortal:         { color: 'violet',  label: 'Genio mortal' },
  automata_eterno:      { color: 'red',     label: 'Aut\u00F3mata eterno' },
  visionario_atrapado:  { color: 'cyan',    label: 'Visionario atrapado' },
  zombi_inmortal:       { color: 'rose',    label: 'Zombi inmortal' },
  potencial_dormido:    { color: 'emerald', label: 'Potencial dormido' },
  E1: { color: 'emerald', label: 'Equilibrado alto' },
  E2: { color: 'emerald', label: 'Equilibrado medio' },
  E3: { color: 'amber',   label: 'Equilibrado bajo' },
  E4: { color: 'emerald', label: 'Equilibrado m\u00E1ximo' },
};
