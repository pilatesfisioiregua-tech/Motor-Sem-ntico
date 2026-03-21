# B-PIL-17: Vista Calendario Semanal — Tipo iOS Calendar

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-04 (sesiones), B-PIL-06 (frontend)
**Coste:** $0

---

## CONTEXTO

El Modo Estudio muestra una lista plana de sesiones del día. Jesús necesita ver la semana completa de un vistazo — qué grupos hay, dónde hay huecos, quién viene, quién falta. Estilo Apple Calendar / Google Calendar: columnas por día, bloques por sesión con colores por grupo.

**Lo que sustituye:** El panel izquierdo de agenda en App.jsx pasa de lista del día → calendario semanal interactivo.

---

## FASE A: Backend — Endpoint sesiones por rango

### A1. Añadir endpoint en router.py

**Archivo:** `@project/src/pilates/router.py` — LEER PRIMERO. AÑADIR:

```python
@router.get("/sesiones/semana")
async def sesiones_semana(fecha: Optional[date] = None):
    """Sesiones de una semana completa (L-V) con asistentes y estado.
    
    Args:
        fecha: Cualquier día de la semana deseada. Default: hoy.
    
    Returns:
        {semana_inicio, semana_fin, dias: [{fecha, dia_nombre, sesiones: [...]}]}
    """
    if fecha is None:
        fecha = date.today()
    
    # Calcular lunes de la semana
    lunes = fecha - timedelta(days=fecha.weekday())
    viernes = lunes + timedelta(days=4)
    
    pool = await _get_pool()
    async with pool.acquire() as conn:
        sesiones = await conn.fetch("""
            SELECT s.id, s.tipo, s.grupo_id, s.fecha, s.hora_inicio, s.hora_fin, s.estado,
                   g.nombre as grupo_nombre, g.tipo as grupo_tipo, g.capacidad_max,
                   (SELECT count(*) FROM om_asistencias a 
                    WHERE a.sesion_id = s.id AND a.estado IN ('confirmada','asistio','recuperacion')) as presentes,
                   (SELECT count(*) FROM om_asistencias a 
                    WHERE a.sesion_id = s.id AND a.estado = 'no_vino') as ausentes,
                   (SELECT count(*) FROM om_asistencias a 
                    WHERE a.sesion_id = s.id) as total_asistencias
            FROM om_sesiones s
            LEFT JOIN om_grupos g ON g.id = s.grupo_id
            WHERE s.tenant_id = $1 AND s.fecha >= $2 AND s.fecha <= $3
            ORDER BY s.fecha, s.hora_inicio
        """, TENANT, lunes, viernes)
    
    # Agrupar por día
    dias_nombre = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    dias = []
    for i in range(5):
        dia_fecha = lunes + timedelta(days=i)
        sesiones_dia = [
            _row_to_dict(s) for s in sesiones if s["fecha"] == dia_fecha
        ]
        dias.append({
            "fecha": str(dia_fecha),
            "dia_nombre": dias_nombre[i],
            "es_hoy": dia_fecha == date.today(),
            "sesiones": sesiones_dia,
        })
    
    return {
        "semana_inicio": str(lunes),
        "semana_fin": str(viernes),
        "dias": dias,
        "total_sesiones": len(sesiones),
    }
```

### A2. Añadir en api.js

```javascript
export const getSesionesSemana = (fecha) =>
  request(`/sesiones/semana${fecha ? `?fecha=${fecha}` : ''}`);
```

---

## FASE B: Frontend — Componente Calendario

### B1. Crear `frontend/src/Calendario.jsx`

```jsx
import { useState, useEffect, useRef } from 'react';
import * as api from './api';

/**
 * Calendario semanal tipo iOS Calendar.
 * 
 * Layout: 5 columnas (L-V), filas por hora (09:00-22:00).
 * Sesiones como bloques de color posicionados por hora.
 * Click en sesión → selecciona para ver asistentes.
 * Swipe / flechas para navegar semanas.
 */

const HORA_INICIO = 9;   // 09:00
const HORA_FIN = 22;     // 22:00
const HORAS = Array.from({length: HORA_FIN - HORA_INICIO}, (_, i) => HORA_INICIO + i);
const PX_POR_HORA = 64;  // Altura de cada hora en pixels

// Colores por grupo (se asignan dinámicamente)
const COLORES = [
  { bg: '#EEF2FF', border: '#6366F1', text: '#4338CA' },  // indigo
  { bg: '#F0FDF4', border: '#22C55E', text: '#15803D' },  // green
  { bg: '#FFF7ED', border: '#F97316', text: '#C2410C' },  // orange
  { bg: '#FDF2F8', border: '#EC4899', text: '#BE185D' },  // pink
  { bg: '#F0F9FF', border: '#0EA5E9', text: '#0369A1' },  // sky
  { bg: '#FEFCE8', border: '#EAB308', text: '#A16207' },  // yellow
  { bg: '#FAF5FF', border: '#A855F7', text: '#7E22CE' },  // purple
  { bg: '#FFF1F2', border: '#F43F5E', text: '#BE123C' },  // rose
  { bg: '#ECFDF5', border: '#10B981', text: '#047857' },  // emerald
  { bg: '#EFF6FF', border: '#3B82F6', text: '#1D4ED8' },  // blue
  { bg: '#F5F3FF', border: '#8B5CF6', text: '#6D28D9' },  // violet
  { bg: '#FEF9C3', border: '#CA8A04', text: '#854D0E' },  // amber
  { bg: '#E0F2FE', border: '#0284C7', text: '#075985' },  // light blue
  { bg: '#FCE7F3', border: '#DB2777', text: '#9D174D' },  // deep pink
  { bg: '#D1FAE5', border: '#059669', text: '#065F46' },  // teal
  { bg: '#FEE2E2', border: '#EF4444', text: '#B91C1C' },  // red
];

function getColorForGroup(groupName, colorMap) {
  if (!colorMap.current[groupName]) {
    const idx = Object.keys(colorMap.current).length % COLORES.length;
    colorMap.current[groupName] = COLORES[idx];
  }
  return colorMap.current[groupName];
}

function timeToMinutes(timeStr) {
  if (!timeStr) return 0;
  const parts = String(timeStr).split(':');
  return parseInt(parts[0]) * 60 + parseInt(parts[1] || 0);
}

export default function Calendario({ onSelectSesion, sesionSeleccionadaId }) {
  const [data, setData] = useState(null);
  const [semanaOffset, setSemanaOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const colorMap = useRef({});
  const scrollRef = useRef(null);

  useEffect(() => {
    loadSemana();
  }, [semanaOffset]);

  // Scroll a la hora actual al cargar
  useEffect(() => {
    if (scrollRef.current && semanaOffset === 0) {
      const now = new Date();
      const currentHour = now.getHours();
      const scrollTo = Math.max(0, (currentHour - HORA_INICIO - 1) * PX_POR_HORA);
      scrollRef.current.scrollTop = scrollTo;
    }
  }, [data]);

  async function loadSemana() {
    setLoading(true);
    try {
      // Calcular fecha del lunes de la semana deseada
      const hoy = new Date();
      const target = new Date(hoy);
      target.setDate(target.getDate() + (semanaOffset * 7));
      const yyyy = target.getFullYear();
      const mm = String(target.getMonth() + 1).padStart(2, '0');
      const dd = String(target.getDate()).padStart(2, '0');
      
      const d = await api.getSesionesSemana(`${yyyy}-${mm}-${dd}`);
      setData(d);
    } catch (e) {
      console.error('Error cargando semana:', e);
    }
    setLoading(false);
  }

  // Keyboard navigation
  useEffect(() => {
    function handleKey(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); setSemanaOffset(p => p - 1); }
      if (e.key === 'ArrowRight') { e.preventDefault(); setSemanaOffset(p => p + 1); }
      if (e.key === 't' || e.key === 'T') { e.preventDefault(); setSemanaOffset(0); }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  if (loading && !data) return <div style={s.loading}>Cargando calendario...</div>;

  return (
    <div style={s.container}>
      {/* Header: navegación semana */}
      <div style={s.header}>
        <button style={s.navBtn} onClick={() => setSemanaOffset(p => p - 1)}>‹</button>
        <div style={s.headerCenter}>
          <button style={s.todayBtn} onClick={() => setSemanaOffset(0)}>Hoy</button>
          <span style={s.semanaLabel}>
            {data ? `${data.semana_inicio.slice(5)} — ${data.semana_fin.slice(5)}` : '...'}
          </span>
        </div>
        <button style={s.navBtn} onClick={() => setSemanaOffset(p => p + 1)}>›</button>
      </div>

      {/* Columnas de días */}
      <div style={s.diasHeader}>
        <div style={s.horaColumn}></div>
        {data?.dias.map((dia, i) => (
          <div key={i} style={{
            ...s.diaHeader,
            ...(dia.es_hoy ? s.diaHeaderHoy : {}),
          }}>
            <div style={s.diaNombre}>{dia.dia_nombre.slice(0, 3)}</div>
            <div style={{
              ...s.diaNumero,
              ...(dia.es_hoy ? s.diaNumeroHoy : {}),
            }}>
              {dia.fecha.slice(8, 10)}
            </div>
          </div>
        ))}
      </div>

      {/* Grid de horas + sesiones */}
      <div style={s.gridScroll} ref={scrollRef}>
        <div style={{...s.grid, height: HORAS.length * PX_POR_HORA}}>
          {/* Líneas de hora */}
          {HORAS.map(hora => (
            <div key={hora} style={{
              ...s.horaLinea,
              top: (hora - HORA_INICIO) * PX_POR_HORA,
            }}>
              <span style={s.horaLabel}>{String(hora).padStart(2,'0')}:00</span>
              <div style={s.horaLineaDivider}></div>
            </div>
          ))}

          {/* Línea de hora actual */}
          {semanaOffset === 0 && (() => {
            const now = new Date();
            const minutos = now.getHours() * 60 + now.getMinutes();
            const top = ((minutos / 60) - HORA_INICIO) * PX_POR_HORA;
            if (top >= 0 && top <= HORAS.length * PX_POR_HORA) {
              return <div style={{...s.nowLine, top}}><div style={s.nowDot}></div></div>;
            }
            return null;
          })()}

          {/* Sesiones como bloques */}
          {data?.dias.map((dia, diaIdx) => (
            dia.sesiones.map((sesion, sIdx) => {
              const inicio = timeToMinutes(sesion.hora_inicio);
              const fin = timeToMinutes(sesion.hora_fin);
              const top = ((inicio / 60) - HORA_INICIO) * PX_POR_HORA;
              const height = ((fin - inicio) / 60) * PX_POR_HORA;
              const color = getColorForGroup(sesion.grupo_nombre || 'Individual', colorMap);
              const isSelected = sesion.id === sesionSeleccionadaId;

              return (
                <div key={`${diaIdx}-${sIdx}`}
                  onClick={() => onSelectSesion && onSelectSesion(sesion)}
                  style={{
                    position: 'absolute',
                    top: top + 1,
                    left: `calc(50px + ${diaIdx * 20}% + 2px)`,
                    width: 'calc(20% - 4px)',
                    height: height - 2,
                    backgroundColor: color.bg,
                    borderLeft: `3px solid ${color.border}`,
                    borderRadius: 6,
                    padding: '3px 6px',
                    cursor: 'pointer',
                    overflow: 'hidden',
                    transition: 'box-shadow 0.15s, transform 0.1s',
                    boxShadow: isSelected
                      ? `0 0 0 2px ${color.border}, 0 2px 8px rgba(0,0,0,0.15)`
                      : '0 1px 2px rgba(0,0,0,0.06)',
                    transform: isSelected ? 'scale(1.02)' : 'none',
                    zIndex: isSelected ? 10 : 1,
                    opacity: sesion.estado === 'completada' ? 0.7 : 1,
                  }}>
                  <div style={{fontSize: 11, fontWeight: 600, color: color.text, lineHeight: 1.2}}>
                    {sesion.grupo_nombre || 'Individual'}
                  </div>
                  {height > 30 && (
                    <div style={{fontSize: 10, color: color.text, opacity: 0.7, marginTop: 1}}>
                      {String(sesion.hora_inicio).slice(0,5)}
                    </div>
                  )}
                  {height > 42 && (
                    <div style={{fontSize: 10, marginTop: 2, display: 'flex', gap: 4}}>
                      <span style={{color: '#16a34a'}}>{sesion.presentes || 0}</span>
                      {(sesion.ausentes || 0) > 0 && (
                        <span style={{color: '#ef4444'}}>{sesion.ausentes}</span>
                      )}
                      {sesion.estado === 'completada' && (
                        <span style={{color: color.text, opacity: 0.5}}>✓</span>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          ))}
        </div>
      </div>

      {/* Footer: leyenda + stats */}
      <div style={s.footer}>
        <span style={{fontSize: 11, color: '#9ca3af'}}>
          {data?.total_sesiones || 0} sesiones ·
          ← → navegar · T hoy
        </span>
      </div>
    </div>
  );
}

const s = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100%',
    background: '#fff', borderRadius: 0,
  },
  loading: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    height: '100%', color: '#9ca3af', fontSize: 13,
  },

  // Header
  header: {
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '8px 12px', borderBottom: '1px solid #f3f4f6',
  },
  navBtn: {
    background: 'none', border: '1px solid #e5e7eb', borderRadius: 6,
    width: 28, height: 28, fontSize: 16, cursor: 'pointer', color: '#374151',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  headerCenter: {
    display: 'flex', alignItems: 'center', gap: 8,
  },
  todayBtn: {
    background: '#6366f1', color: '#fff', border: 'none', borderRadius: 6,
    padding: '3px 10px', fontSize: 12, fontWeight: 500, cursor: 'pointer',
  },
  semanaLabel: {
    fontSize: 13, fontWeight: 600, color: '#374151',
  },

  // Días header
  diasHeader: {
    display: 'flex', borderBottom: '1px solid #e5e7eb', flexShrink: 0,
  },
  horaColumn: {
    width: 50, flexShrink: 0,
  },
  diaHeader: {
    flex: 1, textAlign: 'center', padding: '6px 0',
  },
  diaHeaderHoy: {
    background: '#EEF2FF',
  },
  diaNombre: {
    fontSize: 11, color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  diaNumero: {
    fontSize: 16, fontWeight: 600, color: '#374151', marginTop: 2,
  },
  diaNumeroHoy: {
    background: '#6366f1', color: '#fff', borderRadius: '50%',
    width: 28, height: 28, lineHeight: '28px', margin: '2px auto 0',
  },

  // Grid
  gridScroll: {
    flex: 1, overflow: 'auto', position: 'relative',
  },
  grid: {
    position: 'relative', width: '100%',
  },
  horaLinea: {
    position: 'absolute', left: 0, right: 0, display: 'flex', alignItems: 'flex-start',
  },
  horaLabel: {
    width: 50, fontSize: 10, color: '#9ca3af', textAlign: 'right', paddingRight: 8,
    flexShrink: 0, marginTop: -6,
  },
  horaLineaDivider: {
    flex: 1, borderTop: '1px solid #f3f4f6', marginTop: 0,
  },

  // Línea ahora
  nowLine: {
    position: 'absolute', left: 50, right: 0, height: 2,
    background: '#ef4444', zIndex: 20, display: 'flex', alignItems: 'center',
  },
  nowDot: {
    width: 8, height: 8, borderRadius: '50%', background: '#ef4444', marginLeft: -4,
  },

  // Footer
  footer: {
    padding: '6px 12px', borderTop: '1px solid #f3f4f6', textAlign: 'center',
  },
};
```

---

## FASE C: Integrar en App.jsx

### C1. Reemplazar panel izquierdo

**Archivo:** `@project/frontend/src/App.jsx` — LEER PRIMERO.

1. AÑADIR import:
```jsx
import Calendario from './Calendario';
```

2. REEMPLAZAR el `<div className="panel-agenda">` completo por:
```jsx
      {/* PANEL IZQUIERDO: CALENDARIO */}
      <div className="panel-agenda" style={{padding: 0, width: 'auto'}}>
        <Calendario
          onSelectSesion={selectSesion}
          sesionSeleccionadaId={sesionSeleccionada?.id}
        />
      </div>
```

3. ACTUALIZAR el CSS grid para dar más espacio al calendario.

### C2. Actualizar App.css

**Archivo:** `@project/frontend/src/App.css` — CAMBIAR la regla `.app`:

```css
.app {
  display: grid;
  grid-template-columns: 1fr 380px 320px;
  height: 100vh;
  gap: 1px;
  background: var(--border);
}
```

Cambio: el calendario ocupa `1fr` (flexible) en vez de `280px` fijo. El panel central (detalle sesión) pasa a `380px`. Panel derecho se mantiene.

### C3. Actualizar panel-agenda CSS

```css
.panel-agenda {
  background: #fff;
  overflow: hidden;
  padding: 0;
}
```

Quitar el padding y dejar que el componente Calendario gestione su propio layout.

---

## FASE D: Generar sesiones para la semana si no existen

El calendario mostrará vacío si no hay sesiones generadas. Añadir detección automática:

**Archivo:** `@project/frontend/src/Calendario.jsx` — En `loadSemana`, DESPUÉS de cargar datos:

```jsx
      // Si no hay sesiones y es semana actual o futura, ofrecer generar
      if (d.total_sesiones === 0 && semanaOffset >= 0) {
        // Auto-generar si es semana actual
        if (semanaOffset === 0) {
          try {
            await api.generarSesionesSemana();
            const d2 = await api.getSesionesSemana(`${yyyy}-${mm}-${dd}`);
            setData(d2);
            return;
          } catch (e) { /* silencioso */ }
        }
      }
```

---

## Pass/fail

- GET /pilates/sesiones/semana devuelve 5 días con sesiones agrupadas
- GET /pilates/sesiones/semana?fecha=2026-03-16 devuelve semana del 16 de marzo
- Calendario.jsx renderiza grid semanal L-V con bloques por sesión
- Cada grupo tiene color único consistente
- Click en bloque → selecciona sesión (panel central muestra asistentes)
- Flechas ← → navegan semanas
- T vuelve a hoy
- Línea roja horizontal marca hora actual (solo semana actual)
- Auto-scroll a hora actual al cargar
- Sesiones completadas se muestran con opacity 0.7 + ✓
- Bloques muestran: nombre grupo + hora + presentes/ausentes
- Si no hay sesiones en semana actual, auto-genera desde om_grupos
- Grid responsive: calendario ocupa espacio flexible

---

## VISUAL ESPERADO

```
     ‹  [Hoy]  03-17 — 03-21  ›

         Lun    Mar    Mié    Jue    Vie
09:00   ┌────┐ ┌────┐
        │Mat │ │Est.│
10:00   └────┘ ┌────┐
               │Est.│
11:00          └────┘         ┌────┐
                              │J-V │
                              │11:00│
13:00   ┌────┐               └────┘
        │Est.│
14:00   └────┘
   ...
17:15   ┌────┐        ┌────┐
        │Est.│        │Est.│
18:15   ├────┤ ┌────┐ ├────┤ ┌────┐ ┌────┐
        │Est.│ │Est.│ │Est.│ │Est.│ │M-V │
19:15   ├────┤ ├────┤ ├────┤ ├────┤ └────┘
        │Est.│ │Est.│ │Est.│ │Est.│
20:15   ├────┤ ├────┤ ├────┤ ├────┤
        │Est.│ │Est.│ │Est.│ │Est.│
21:15   └────┘ ├────┤ └────┘ ├────┤
               │Est.│        │Est.│
22:00          └────┘        └────┘

  32 sesiones · ← → navegar · T hoy
```

Cada bloque con color del grupo, presentes/ausentes, indicador completada.
Click → panel central con lista de alumnos para marcar asistencia.
