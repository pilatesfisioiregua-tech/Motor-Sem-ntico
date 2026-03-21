import { useState, useEffect, useCallback } from 'react';
import * as api from './api';

const SEVERITY_COLORS = {
  info: '#6366f1',
  success: '#22c55e',
  warning: '#f97316',
  danger: '#ef4444',
};

export default function FeedEstudio({ onClose }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadFeed = useCallback(async () => {
    try {
      const data = await api.getFeed({ limit: 30 });
      setItems(data);
    } catch (e) { /* ignore */ }
    setLoading(false);
  }, []);

  useEffect(() => { loadFeed(); }, [loadFeed]);

  async function marcarTodas() {
    try {
      await api.marcarLeidoFeed({ todos: true });
      setItems(prev => prev.map(i => ({ ...i, leido: true })));
    } catch (e) { /* ignore */ }
  }

  function timeAgo(ts) {
    const diff = (Date.now() - new Date(ts).getTime()) / 1000;
    if (diff < 60) return 'ahora';
    if (diff < 3600) return `${Math.floor(diff / 60)}min`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  }

  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.panel} onClick={e => e.stopPropagation()}>
        <div style={s.header}>
          <h3 style={s.title}>Feed del estudio</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button style={s.btnMark} onClick={marcarTodas}>Marcar todas</button>
            <button style={s.btnClose} onClick={onClose}>✕</button>
          </div>
        </div>

        <div style={s.list}>
          {loading && <div style={s.empty}>Cargando...</div>}
          {!loading && items.length === 0 && <div style={s.empty}>Sin noticias</div>}
          {items.map(item => (
            <div key={item.id} style={{
              ...s.item,
              borderLeftColor: SEVERITY_COLORS[item.severidad] || SEVERITY_COLORS.info,
              opacity: item.leido ? 0.6 : 1,
            }}>
              <div style={s.itemHeader}>
                <span style={s.icon}>{item.icono}</span>
                <span style={s.itemTitle}>{item.titulo}</span>
                <span style={s.time}>{timeAgo(item.created_at)}</span>
              </div>
              {item.detalle && <div style={s.detail}>{item.detalle}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

const s = {
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
    display: 'flex', justifyContent: 'flex-end', zIndex: 200,
  },
  panel: {
    width: 360, background: 'var(--surface, #1a1d27)', height: '100vh',
    display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--border, #2a2e3a)',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', borderBottom: '1px solid var(--border, #2a2e3a)',
  },
  title: { fontSize: 14, fontWeight: 600, color: 'var(--text, #e4e4e7)', margin: 0 },
  btnMark: {
    padding: '4px 10px', fontSize: 11, background: 'none', border: '1px solid var(--border, #2a2e3a)',
    borderRadius: 4, color: 'var(--text-dim, #71717a)', cursor: 'pointer',
  },
  btnClose: {
    padding: '4px 8px', fontSize: 14, background: 'none', border: 'none',
    color: 'var(--text-dim, #71717a)', cursor: 'pointer',
  },
  list: { flex: 1, overflowY: 'auto', padding: 8 },
  empty: { color: 'var(--text-dim, #71717a)', fontSize: 13, textAlign: 'center', padding: 20 },
  item: {
    padding: '8px 12px', marginBottom: 4, borderRadius: 6,
    borderLeft: '3px solid', background: 'var(--bg, #0f1117)',
  },
  itemHeader: { display: 'flex', alignItems: 'center', gap: 6 },
  icon: { fontSize: 14 },
  itemTitle: { flex: 1, fontSize: 13, fontWeight: 500, color: 'var(--text, #e4e4e7)' },
  time: { fontSize: 10, color: 'var(--text-dim, #71717a)' },
  detail: { fontSize: 12, color: 'var(--text-dim, #71717a)', marginTop: 2, marginLeft: 20 },
};
