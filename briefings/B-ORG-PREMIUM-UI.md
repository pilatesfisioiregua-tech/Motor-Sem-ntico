# B-ORG-PREMIUM-UI: Interfaces Premium — Diseño Top Mundial

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — 55 agentes trabajando detrás de una interfaz genérica
**Reemplaza:** B-ORG-INTERFACE (fusionado aquí con diseño premium)
**Dependencia:** B-ORG-PIZARRA + B-ORG-AF5 + B-ORG-EVALUADOR + B-ORG-DIRECTOR implementados

---

## EL PROBLEMA

55 agentes, 3 Opus, pizarra con conciencia colectiva, Director que escribe partituras con álgebra de 18 inteligencias. Y la interfaz es:
- Inline styles con colores hardcodeados (`{color:'#6b7280'}`)
- Sin sistema de diseño (cada módulo reinventa estilos)
- Sin tipografía distintiva (system fonts)
- Sin animaciones ni transiciones
- `/estudio` dark mode vs `/profundo` light mode sin coherencia
- Tarjetas blancas genéricas en `/profundo` = estética de template Bootstrap 2020

OMNI-MIND no es un CRM. Es un organismo cognitivo. La interfaz debe sentirse como mirar dentro de un cerebro vivo.

---

## DIRECCIÓN ESTÉTICA: "CEREBRO VIVO"

**Concepto:** La interfaz se siente como un organismo que respira. Oscura, profunda, con acentos que pulsan como sinapsis. La información fluye como señales neuronales. Los datos estáticos están quietos; lo que está vivo (agentes activos, señales fluyendo, conflictos) brilla.

**Tono:** Refinado + técnico + orgánico. No cyberpunk (demasiado agresivo). No glassmorphism puro (demasiado trendy). Algo entre Linear.app (precisión) + Stripe Dashboard (elegancia) + la profundidad orgánica de un sistema nervioso.

**Referentes 2026:** SaaS dashboards top usan: dark mode con alto contraste, tipografía bold, soft gradients, datos que respiran con micro-interacciones, layout modular con jerarquía F-pattern, "North Star Metric" arriba-izquierda, acciones inmediatas ("Next Best Action") integradas en el dashboard.

---

## PALETA "NEURAL DARK"

```css
:root {
  /* === FONDOS — Profundidad en capas === */
  --bg-void: #08090d;           /* Fondo absoluto: el vacío */
  --bg-deep: #0c0e14;          /* Fondo principal: profundidad */
  --bg-surface: #12151e;       /* Tarjetas, módulos */
  --bg-elevated: #181c28;      /* Elementos elevados, hover */
  --bg-overlay: #1e2233;       /* Overlays, modales */

  /* === TEXTO — Jerarquía clara === */
  --text-primary: #e8eaf0;     /* Títulos, datos principales */
  --text-secondary: #9498a8;   /* Texto de apoyo */
  --text-tertiary: #5c6070;    /* Labels, metadata */
  --text-ghost: #363a48;       /* Bordes, divisores sutiles */

  /* === ACENTOS — Sinapsis del organismo === */
  --accent-indigo: #6366f1;    /* Acción principal, CTA, enlaces */
  --accent-indigo-dim: #4f46e5; /* Hover de indigo */
  --accent-indigo-glow: rgba(99, 102, 241, 0.15); /* Glow sutil */

  --accent-green: #34d399;     /* Éxito, subida, saludable */
  --accent-amber: #fbbf24;     /* Advertencia, atención */
  --accent-red: #f87171;       /* Error, bajada, peligro */
  --accent-violet: #a78bfa;    /* Organismo, cognitivo */
  --accent-cyan: #22d3ee;      /* Datos, métricas, sensorial */
  --accent-rose: #fb7185;      /* Identidad, voz, F5 */

  /* === SUPERFICIES === */
  --border: rgba(255, 255, 255, 0.06);
  --border-active: rgba(99, 102, 241, 0.3);
  --shadow-card: 0 1px 3px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.03);
  --shadow-elevated: 0 8px 32px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05);
  --shadow-glow: 0 0 20px var(--accent-indigo-glow);

  /* === TIPOGRAFÍA === */
  --font-display: 'Instrument Sans', 'DM Sans', sans-serif;
  --font-body: 'Inter Tight', 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* === ESPACIADO === */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-full: 9999px;

  /* === TRANSICIONES === */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
}
```

**Tipografía (Google Fonts, gratuitas):**
- Display/Headers: **Instrument Sans** — geométrica pero cálida, moderna, no genérica
- Body: **Inter Tight** — más condensada que Inter, más personalidad
- Mono/Datos: **JetBrains Mono** — para scores, métricas, código

---

## 8 COMPONENTES DEL SISTEMA DE DISEÑO

### 1. Card — Base de todo

```jsx
function Card({ children, variant = 'default', glow = false, className = '' }) {
  const variants = {
    default: 'bg-[var(--bg-surface)] border border-[var(--border)]',
    elevated: 'bg-[var(--bg-elevated)] border border-[var(--border-active)] shadow-[var(--shadow-elevated)]',
    organism: 'bg-[var(--bg-surface)] border border-violet-500/20 shadow-[0_0_24px_rgba(167,139,250,0.08)]',
    alert: 'bg-[var(--bg-surface)] border-l-2 border-l-amber-400 border border-[var(--border)]',
    danger: 'bg-[var(--bg-surface)] border-l-2 border-l-red-400 border border-[var(--border)]',
    success: 'bg-[var(--bg-surface)] border-l-2 border-l-emerald-400 border border-[var(--border)]',
  };

  return (
    <div className={`rounded-[var(--radius-lg)] p-5 transition-all duration-[var(--duration-normal)]
      ${variants[variant]} ${glow ? 'shadow-[var(--shadow-glow)]' : ''} ${className}`}>
      {children}
    </div>
  );
}
```

### 2. Metric — KPIs con personalidad

```jsx
function Metric({ label, value, unit = '', delta = null, size = 'md' }) {
  const sizes = {
    sm: { value: 'text-lg', label: 'text-[10px]' },
    md: { value: 'text-3xl', label: 'text-xs' },
    lg: { value: 'text-5xl', label: 'text-sm' },
  };

  const deltaColor = delta > 0 ? 'text-emerald-400' : delta < 0 ? 'text-red-400' : 'text-[var(--text-tertiary)]';
  const deltaArrow = delta > 0 ? '↑' : delta < 0 ? '↓' : '→';

  return (
    <div className="flex flex-col gap-1">
      <span className={`${sizes[size].label} font-medium tracking-wider uppercase text-[var(--text-tertiary)]`}>
        {label}
      </span>
      <div className="flex items-baseline gap-2">
        <span className={`${sizes[size].value} font-bold tracking-tight text-[var(--text-primary)] font-[var(--font-display)]`}>
          {value}
          {unit && <span className="text-[0.5em] text-[var(--text-secondary)] ml-0.5">{unit}</span>}
        </span>
        {delta !== null && (
          <span className={`text-xs font-mono font-medium ${deltaColor}`}>
            {deltaArrow} {Math.abs(delta)}%
          </span>
        )}
      </div>
    </div>
  );
}
```

### 3. Pulse — Indicador de actividad viva

```jsx
function Pulse({ color = 'indigo', size = 8 }) {
  return (
    <span className="relative inline-flex">
      <span className={`absolute inline-flex h-full w-full rounded-full bg-${color}-400 opacity-75 animate-ping`}
            style={{width: size, height: size}} />
      <span className={`relative inline-flex rounded-full bg-${color}-400`}
            style={{width: size, height: size}} />
    </span>
  );
}
```

### 4. AgentBadge — Cada agente tiene presencia visual

```jsx
function AgentBadge({ agent, status, confidence }) {
  const statusConfig = {
    activo: { color: 'emerald', icon: '●', label: 'Activo' },
    esperando: { color: 'amber', icon: '◐', label: 'Esperando' },
    bloqueado: { color: 'red', icon: '■', label: 'Bloqueado' },
    completado: { color: 'indigo', icon: '✓', label: 'Completado' },
  };

  const cfg = statusConfig[status] || statusConfig.activo;

  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full
                    bg-[var(--bg-elevated)] border border-[var(--border)]
                    text-xs font-medium transition-all hover:border-[var(--border-active)]">
      <span className={`text-${cfg.color}-400`}>{cfg.icon}</span>
      <span className="text-[var(--text-primary)] font-mono">{agent}</span>
      {confidence != null && (
        <span className="text-[var(--text-tertiary)] font-mono text-[10px]">
          {(confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
```

### 5. SignalFlow — Visualización del bus de señales

```jsx
function SignalFlow({ signals }) {
  const typeColors = {
    DIAGNOSTICO: 'cyan',
    PRESCRIPCION: 'indigo',
    ALERTA: 'amber',
    VETO: 'red',
    OPORTUNIDAD: 'emerald',
    ACCION: 'violet',
    DATO: 'slate',
  };

  return (
    <div className="relative pl-4 border-l border-[var(--border)]">
      {signals.map((s, i) => {
        const color = typeColors[s.tipo] || 'slate';
        return (
          <div key={i} className="relative mb-3 group">
            <div className={`absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full
                            bg-${color}-400/80 ring-2 ring-[var(--bg-deep)]
                            group-hover:ring-${color}-400/30 transition-all`} />
            <div className="flex items-start gap-3">
              <span className={`text-[10px] font-mono font-bold tracking-wider uppercase
                               text-${color}-400 min-w-[80px]`}>
                {s.tipo}
              </span>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-[var(--text-primary)]">
                  {s.origen} → {s.destino || 'bus'}
                </div>
                <div className="text-[11px] text-[var(--text-tertiary)] truncate">
                  {s.resumen || ''}
                </div>
              </div>
              <span className="text-[10px] text-[var(--text-ghost)] font-mono whitespace-nowrap">
                {timeAgo(s.created_at)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

### 6. LensBar — Las 3 lentes como barra visual

```jsx
function LensBar({ salud, sentido, continuidad, showLabels = true }) {
  const lentes = [
    { key: 'S', label: 'Salud', value: salud, color: 'emerald' },
    { key: 'Se', label: 'Sentido', value: sentido, color: 'violet' },
    { key: 'C', label: 'Continuidad', value: continuidad, color: 'cyan' },
  ];

  return (
    <div className="flex gap-3">
      {lentes.map(l => (
        <div key={l.key} className="flex-1">
          {showLabels && (
            <div className="flex justify-between items-baseline mb-1.5">
              <span className="text-[10px] font-medium tracking-wider uppercase text-[var(--text-tertiary)]">
                {l.label}
              </span>
              <span className={`text-sm font-bold font-mono text-${l.color}-400`}>
                {(l.value * 100).toFixed(0)}
              </span>
            </div>
          )}
          <div className="h-1.5 rounded-full bg-[var(--bg-void)] overflow-hidden">
            <div
              className={`h-full rounded-full bg-${l.color}-400 transition-all duration-700 ease-out`}
              style={{ width: `${l.value * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
```

### 7. ConflictLine — Conflictos entre agentes

```jsx
function ConflictLine({ from, to, description }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg
                    bg-red-500/5 border border-red-500/10">
      <AgentBadge agent={from} status="activo" />
      <span className="text-red-400 text-sm">⚡</span>
      <AgentBadge agent={to} status="activo" />
      {description && (
        <span className="text-xs text-[var(--text-tertiary)] ml-2 truncate flex-1">
          {description}
        </span>
      )}
    </div>
  );
}
```

### 8. VoiceButton — Botón de voz con animación

```jsx
function VoiceButton({ listening, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`relative w-11 h-11 rounded-full flex items-center justify-center
                  transition-all duration-300
                  ${listening
                    ? 'bg-red-500 shadow-[0_0_24px_rgba(248,113,113,0.4)]'
                    : 'bg-[var(--accent-indigo)] hover:shadow-[var(--shadow-glow)]'
                  }`}
    >
      {listening && (
        <>
          <span className="absolute inset-0 rounded-full bg-red-500 animate-ping opacity-30" />
          <span className="absolute inset-[-4px] rounded-full border-2 border-red-400/30 animate-pulse" />
        </>
      )}
      <span className="relative text-white text-lg">
        {listening ? '⏹' : '🎤'}
      </span>
    </button>
  );
}
```

---

## /estudio — CENTRO DE MANDO (Rediseño Premium)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Saludo contextual + Chat/Voz + Lentes S/Se/C   │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ SIDEBAR  │  ÁREA PRINCIPAL                              │
│ (nav por │  (módulo principal grande)                   │
│  capas)  │                                              │
│          ├──────────────┬───────────────────────────────┤
│ ⚡ OPER  │ SECUNDARIO 1 │ SECUNDARIO 2                  │
│ 💰 FIN   ├──────────────┼───────────────────────────────┤
│ 🧠 COG   │ COMPACTO 1   │ COMPACTO 2  │ COMPACTO 3     │
│ 📢 VOZ   │              │             │                 │
│ 🧬 IDENT │              │             │                 │
└──────────┴──────────────┴─────────────┴─────────────────┘
```

### Sidebar por capas

```jsx
function Sidebar({ modulos, activos, onToggle }) {
  const capas = {
    operativo: { label: 'Operativo', icon: '⚡', modulos: ['agenda', 'calendario', 'buscar', 'grupos', 'wa'] },
    financiero: { label: 'Financiero', icon: '💰', modulos: ['pagos_pendientes', 'resumen_mes', 'facturas'] },
    cognitivo: { label: 'Cognitivo', icon: '🧠', modulos: ['pizarra', 'estrategia', 'evaluacion', 'feed_cognitivo', 'bus'] },
    voz: { label: 'Voz', icon: '📢', modulos: ['voz_proactiva', 'voz'] },
    identidad: { label: 'Identidad', icon: '🧬', modulos: ['adn', 'depuracion', 'readiness', 'engagement'] },
  };

  return (
    <aside className="w-56 border-r border-[var(--border)] bg-[var(--bg-deep)]
                        flex flex-col py-4 overflow-y-auto">
      {Object.entries(capas).map(([key, capa]) => (
        <div key={key} className="mb-4">
          <div className="px-4 mb-2 text-[10px] font-bold tracking-[0.1em] uppercase
                          text-[var(--text-ghost)]">
            {capa.icon} {capa.label}
          </div>
          {capa.modulos.map(id => {
            const mod = modulos.find(m => m.id === id);
            if (!mod) return null;
            const isActive = activos.has(id);
            return (
              <button
                key={id}
                onClick={() => onToggle(id)}
                className={`w-full text-left px-4 py-2 text-sm transition-all duration-150
                  ${isActive
                    ? 'text-[var(--text-primary)] bg-[var(--accent-indigo-glow)] border-r-2 border-[var(--accent-indigo)]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
                  }`}
              >
                {mod.icono} {mod.nombre}
              </button>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
```

### Header Premium

```jsx
function HeaderEstudio({ saludo, lentes, onChat, onVoice }) {
  return (
    <header className="flex items-center justify-between px-6 py-4
                        border-b border-[var(--border)] bg-[var(--bg-deep)]">
      <div>
        <h1 className="text-lg font-[var(--font-display)] font-semibold text-[var(--text-primary)]">
          {saludo}
        </h1>
      </div>

      {lentes && (
        <div className="hidden lg:flex items-center gap-6 w-80">
          <LensBar salud={lentes.salud} sentido={lentes.sentido} continuidad={lentes.continuidad} />
        </div>
      )}

      <div className="flex items-center gap-3">
        <div className="relative">
          <input
            className="w-72 bg-[var(--bg-surface)] border border-[var(--border)] rounded-xl
                       px-4 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-ghost)]
                       focus:outline-none focus:border-[var(--border-active)] focus:shadow-[var(--shadow-glow)]
                       transition-all duration-200"
            placeholder="¿Qué necesitas?"
            onKeyDown={e => e.key === 'Enter' && onChat(e.target.value)}
          />
        </div>
        <VoiceButton listening={false} onClick={onVoice} />
      </div>
    </header>
  );
}
```

### 5 Módulos nuevos del organismo

**1. PizarraPanel** — Card variant="organism". Agentes agrupados por capa. AgentBadge + detectando + acción + ConflictLine.

**2. EstrategiaPanel** — Card variant="elevated" con glow. Estado del sistema + estrategia global del Director Opus + agentes reconfigurados con INTs como pills.

**3. EvaluacionPanel** — 3 LensBar con deltas (↑+4% verde, ↓-2% rojo). Conclusión del Evaluador. Recomendaciones.

**4. VozProactivaPanel** — Propuestas del organismo con canal coloreado, justificación, contenido. Botón "Aprobar todas" + ejecutar individual.

**5. FeedCognitivo** — Solo eventos del organismo (Director, Evaluador, Guardián, Cristalizador, Ingeniero).

### Chat con acceso a la pizarra

Modificar `SYSTEM_COCKPIT` en `cockpit.py`:

```python
# En chat_conversacional(), antes de llamar al LLM:
from src.pilates.pizarra import resumen_narrativo
pizarra_resumen = await resumen_narrativo()

SYSTEM_COCKPIT_AMPLIADO = SYSTEM_COCKPIT + f"""

PIZARRA DEL ORGANISMO (lo que cada agente piensa AHORA):
{pizarra_resumen[:1500]}

Puedes responder preguntas sobre el organismo:
- "¿Qué piensa AF3?" → lee la entrada de AF3 en la pizarra
- "¿Hay conflictos entre agentes?" → busca conflicto_con en la pizarra
- "¿Funcionó la prescripción?" → lee la entrada del EVALUADOR
- "¿Qué dice el Director?" → lee la entrada del DIRECTOR_OPUS
"""
```

### Módulos nuevos en cockpit.py

```python
MODULOS.update({
    "pizarra":          {"nombre": "Pizarra organismo",    "icono": "📋", "endpoint": "/organismo/pizarra"},
    "estrategia":       {"nombre": "Estrategia semana",    "icono": "🎼", "endpoint": "/organismo/director"},
    "evaluacion":       {"nombre": "¿Funcionó?",           "icono": "📊", "endpoint": "/organismo/evaluacion"},
    "feed_cognitivo":   {"nombre": "Feed cognitivo",        "icono": "🧠", "endpoint": "/feed?categoria=organismo"},
    "bus":              {"nombre": "Bus señales",            "icono": "📡", "endpoint": "/organismo/bus"},
    "voz_proactiva":    {"nombre": "Voz proactiva",          "icono": "📢", "endpoint": "/voz/propuestas?estado=pendiente"},
})
```

### Endpoints nuevos en router.py

```python
@router.get("/organismo/director")
async def organismo_director():
    """Última ejecución del Director Opus."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='DIRECTOR_OPUS'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"estado_sistema": None, "estrategia_global": None, "configs": []}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}


@router.get("/organismo/evaluacion")
async def organismo_evaluacion():
    """Última evaluación de prescripción."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        señal = await conn.fetchrow("""
            SELECT payload, created_at FROM om_senales_agentes
            WHERE tenant_id='authentic_pilates' AND origen='EVALUADOR'
            ORDER BY created_at DESC LIMIT 1
        """)
    if not señal:
        return {"evaluacion_global": None, "delta_lentes": None}
    payload = señal["payload"] if isinstance(señal["payload"], dict) else json.loads(señal["payload"])
    return {**payload, "fecha": str(señal["created_at"])}
```

---

## /profundo — VENTANA AL CEREBRO (Rediseño Premium)

### Layout

```
┌─────────────────────────────────────────────────────────┐
│ HEADER: "Modo Profundo" + Estado ACD badge + Lentes     │
├──────────┬──────────────────────────────────────────────┤
│          │                                              │
│ TABS     │  CONTENIDO DEL TAB ACTIVO                    │
│ vertical │  (ocupa toda la anchura)                     │
│          │                                              │
│ 📊 Dash  │                                              │
│ 🔬 Diag  │                                              │
│ 🧬 Organ │                                              │
│ 🎼 Direc │                                              │
│ 🧠 Conse │                                              │
│ 📢 Voz   │                                              │
│ 🧬 ADN   │                                              │
│ 🗑 Dep   │                                              │
│ 💰 Cont  │                                              │
└──────────┴──────────────────────────────────────────────┘
```

### Header Profundo

```jsx
function HeaderProfundo({ estado, lentes, semana }) {
  const estadoConfig = {
    operador_ciego: { color: 'amber', label: 'Operador ciego' },
    genio_mortal: { color: 'violet', label: 'Genio mortal' },
    automata_eterno: { color: 'red', label: 'Autómata eterno' },
    visionario_atrapado: { color: 'cyan', label: 'Visionario atrapado' },
    zombi_inmortal: { color: 'rose', label: 'Zombi inmortal' },
    potencial_dormido: { color: 'emerald', label: 'Potencial dormido' },
    E1: { color: 'emerald', label: 'Equilibrado alto' },
    E2: { color: 'emerald', label: 'Equilibrado medio' },
    E3: { color: 'amber', label: 'Equilibrado bajo' },
    E4: { color: 'emerald', label: 'Equilibrado máximo' },
  };

  const cfg = estadoConfig[estado] || { color: 'slate', label: estado };

  return (
    <header className="px-8 py-6 border-b border-[var(--border)] bg-[var(--bg-deep)]">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-[var(--font-display)] font-bold text-[var(--text-primary)]">
            Modo Profundo
          </h1>
          <span className="text-sm text-[var(--text-tertiary)]">
            Authentic Pilates · {semana}
          </span>
        </div>
        <div className={`px-4 py-2 rounded-xl bg-${cfg.color}-500/10 border border-${cfg.color}-500/20`}>
          <span className={`text-sm font-bold text-${cfg.color}-400`}>
            {cfg.label}
          </span>
        </div>
      </div>
      {lentes && <LensBar salud={lentes.salud} sentido={lentes.sentido} continuidad={lentes.continuidad} />}
    </header>
  );
}
```

### Tab "Organismo" — La pieza estrella

Card organism con gomas como pills pulsantes (Pulse verde) + Pizarra agrupada por capas con AgentBadge + ConflictLine + Bus como SignalFlow timeline.

### Tab "Director" — Partituras de Opus

Card elevated con glow mostrando estrategia global. Debajo, Card por agente reconfigurado: INTs como pills, preguntas del cálculo semántico con INT etiquetada, provocación en fondo amber/5, razonamiento con Rs.

### Tab "Diagnóstico" (reemplaza ACD)

Sin botón manual. Diagnóstico automático con evolución 4 semanas (LensBar comparativo) + repertorio INT×P×R actual + prescripción + evaluación.

### Tab "Consejo" conectado al enjambre

Muestra primero el diagnóstico del enjambre (13 clusters) + resultado guardián. DESPUÉS opción de profundizar con un asesor del séquito.

### Tabs completos

```python
TABS = [
    {'id': 'dashboard',    'icon': '📊', 'label': 'Dashboard'},
    {'id': 'diagnostico',  'icon': '🔬', 'label': 'Diagnóstico'},
    {'id': 'organismo',    'icon': '🧬', 'label': 'Organismo'},
    {'id': 'director',     'icon': '🎼', 'label': 'Director'},
    {'id': 'consejo',      'icon': '🧠', 'label': 'Consejo'},
    {'id': 'voz',          'icon': '📢', 'label': 'Voz'},
    {'id': 'adn',          'icon': '🧬', 'label': 'ADN'},
    {'id': 'depuracion',   'icon': '🗑️', 'label': 'Depuración'},
    {'id': 'contabilidad', 'icon': '💰', 'label': 'Contabilidad'},
]
```

---

## INTERFAZ DE VOZ — Web Speech API ($0)

### Componente VoicePanel

```jsx
function VoicePanel({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onresult = (event) => {
      const result = event.results[event.results.length - 1];
      const text = result[0].transcript;
      setTranscript(text);
      if (result.isFinal) {
        setListening(false);
        onTranscript(text);
      }
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
  }, [onTranscript]);

  const toggle = () => {
    if (listening) { recognitionRef.current?.stop(); }
    else { setTranscript(''); recognitionRef.current?.start(); setListening(true); }
  };

  return (
    <div className="flex items-center gap-2">
      <VoiceButton listening={listening} onClick={toggle} />
      {transcript && <span className="text-xs text-[var(--text-tertiary)]">{transcript}</span>}
    </div>
  );
}

function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  utterance.rate = 1.0;
  const voices = speechSynthesis.getVoices();
  const spanishVoice = voices.find(v => v.lang.startsWith('es'));
  if (spanishVoice) utterance.voice = spanishVoice;
  speechSynthesis.speak(utterance);
}
```

### Integración

```jsx
// En header de /estudio:
<VoicePanel onTranscript={(text) => {
  setChatInput(text);
  setTimeout(() => enviarChat(), 100);
}} />

// Al recibir respuesta:
if (data.respuesta) {
  setChatResp(data.respuesta);
  speak(data.respuesta);
}
```

---

## ANIMACIONES PREMIUM

```css
/* Staggered reveal de módulos */
@keyframes moduleReveal {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.module-enter { animation: moduleReveal 0.4s var(--ease-out) forwards; }
.module-enter:nth-child(1) { animation-delay: 0ms; }
.module-enter:nth-child(2) { animation-delay: 60ms; }
.module-enter:nth-child(3) { animation-delay: 120ms; }
.module-enter:nth-child(4) { animation-delay: 180ms; }

/* Pulse de agentes activos */
@keyframes agentPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(99, 102, 241, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(99, 102, 241, 0); }
}
.agent-active { animation: agentPulse 2s infinite; }

/* Transiciones suaves de datos */
.metric-value { transition: all 0.6s var(--ease-out); }
.lens-bar-fill { transition: width 0.8s var(--ease-out); }
```

---

## ESTRUCTURA DE ARCHIVOS

```
frontend/src/
├── App.jsx                    (routing)
├── main.jsx                   (entry)
├── index.css                  (CSS variables + Tailwind + animaciones)
├── api.js                     (API client — sin cambios)
├── design/
│   ├── Card.jsx
│   ├── Metric.jsx
│   ├── Pulse.jsx
│   ├── AgentBadge.jsx
│   ├── SignalFlow.jsx
│   ├── LensBar.jsx
│   ├── ConflictLine.jsx
│   ├── VoiceButton.jsx
│   └── theme.js               (constantes)
├── estudio/
│   ├── EstudioCockpit.jsx     (REESCRITO — sidebar + header + módulos)
│   ├── HeaderEstudio.jsx
│   ├── Sidebar.jsx
│   └── modules/
│       ├── AgendaHoy.jsx
│       ├── PagosPendientes.jsx
│       ├── ResumenMes.jsx
│       ├── PizarraPanel.jsx   (NUEVO)
│       ├── EstrategiaPanel.jsx (NUEVO)
│       ├── EvaluacionPanel.jsx (NUEVO)
│       ├── VozProactivaPanel.jsx (NUEVO)
│       ├── FeedCognitivo.jsx  (NUEVO)
│       └── ... (demás migrados)
├── profundo/
│   ├── Profundo.jsx           (REESCRITO — tabs verticales + header)
│   ├── HeaderProfundo.jsx
│   └── tabs/
│       ├── TabDashboard.jsx
│       ├── TabDiagnostico.jsx
│       ├── TabOrganismo.jsx   (NUEVO)
│       ├── TabDirector.jsx    (NUEVO)
│       ├── TabConsejo.jsx
│       ├── TabVoz.jsx
│       ├── TabADN.jsx
│       ├── TabDepuracion.jsx
│       └── TabContabilidad.jsx
├── shared/
│   ├── PanelWA.jsx
│   ├── FeedEstudio.jsx
│   └── VoicePanel.jsx        (NUEVO)
├── portal/
│   ├── Portal.jsx
│   ├── PortalChat.jsx
│   └── PortalPublico.jsx
└── Onboarding.jsx
```

---

## DEPENDENCIAS

```json
{
  "dependencies": {
    "tailwindcss": "^4.0",
    "framer-motion": "^12.0",
    "react-hot-toast": "existente"
  }
}
```

Google Fonts: Instrument Sans, Inter Tight, JetBrains Mono (gratuitas, CDN).

---

## MIGRACIÓN INCREMENTAL (3 fases)

**Fase 1: Sistema de diseño (1 sesión)**
- `index.css` con CSS variables Neural Dark
- 8 componentes en `design/`
- Configurar Tailwind v4
- Migrar `EstudioCockpit.jsx` de inline styles a Tailwind + componentes

**Fase 2: /estudio premium (1 sesión)**
- Layout sidebar + header + módulos
- Módulos existentes migrados
- 5 módulos nuevos (pizarra, estrategia, evaluación, voz proactiva, feed cognitivo)
- Voz (VoicePanel + VoiceButton)

**Fase 3: /profundo premium (1 sesión)**
- Layout tabs verticales + header con estado ACD
- Tabs nuevos (organismo, director)
- Tabs existentes migrados

---

## COSTE

$0. Solo frontend. Tailwind + Framer Motion + Google Fonts = gratuito.

## TESTS

### T1: Ambas interfaces usan mismo sistema de diseño
Mismas CSS variables, mismos componentes (Card, Metric, LensBar).

### T2: Módulos del organismo visibles en /estudio
Chips Pizarra/Estrategia/¿Funcionó?/Feed Cognitivo/Bus montables.

### T3: Voz STT→chat→TTS en Chrome desktop
Click 🎤 → hablar → texto en input → enviar → respuesta hablada.

### T4: Animaciones premium
Staggered reveal, agent pulse, lens bar transition.

### T5: /profundo muestra organismo
Tab Organismo con pizarra + bus + gomas pulsantes.
Tab Director con partituras D_híbrido + preguntas + provocaciones.
