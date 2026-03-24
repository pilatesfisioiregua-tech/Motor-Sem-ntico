# B-ORG-INTERFACE: Interfaces a la altura del organismo + Voz bidireccional

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — 55 agentes trabajando y el dueño ve un CRM genérico
**Dependencia:** B-ORG-PIZARRA implementada (ya está)

---

## DOS PROBLEMAS, UN BRIEFING

### Problema 1: El organismo es invisible
55 agentes que perciben, piensan, chocan, prescriben, evalúan. Una pizarra con conciencia colectiva. Un Director Opus que escribe partituras. Un Guardián que detecta sesgos. Y el dueño ve: "agenda de hoy", "pagos pendientes", "3 alertas".

### Problema 2: El dueño es mudo
B2.9 genera contenido por WA/IG/GBP para clientes. Pero Jesús solo puede interactuar con el sistema ESCRIBIENDO en un chat de texto. No puede hablar con el organismo como habla con un empleado: "¿Cómo está el estudio?" → el sistema escucha, piensa, responde.

---

## PARTE 1: /estudio — Centro de mando CON el organismo visible

### Qué mantener (funciona bien):
- El sistema de chips/módulos montables/desmontables
- La jerarquía principal/secundario/compacto
- El chat conversacional para controlar la interfaz + ejecutar operaciones
- El feed de noticias
- Los módulos operativos (agenda, pagos, calendario, grupos, WA, engagement)

### Qué añadir:

#### 1A. Nuevo módulo: "Pizarra del organismo"

Chip: 📋 Pizarra

Muestra la pizarra en tiempo real: qué está haciendo cada agente, con quién choca, qué propone.

```jsx
function PizarraPanel() {
  const [pizarra, setPizarra] = useState([]);
  useEffect(() => {
    fetch(`${PREFIX}/organismo/pizarra`)
      .then(r => r.json())
      .then(data => setPizarra(data.entradas || []));
  }, []);

  // Agrupar por capa
  const capas = {};
  pizarra.forEach(e => {
    const c = e.capa || 'otra';
    if (!capas[c]) capas[c] = [];
    capas[c].push(e);
  });

  const estadoEmoji = {activo:'🟢', esperando:'🟡', bloqueado:'🔴', completado:'✅'};

  return (
    <div>
      {Object.entries(capas).map(([capa, agentes]) => (
        <div key={capa}>
          <div style={{fontSize:11, fontWeight:700, color:'var(--text-dim)',
                       textTransform:'uppercase', marginTop:12, marginBottom:4}}>
            {capa} ({agentes.length})
          </div>
          {agentes.map(a => (
            <div key={a.agente} style={{...S.row, flexDirection:'column', alignItems:'flex-start', gap:2}}>
              <div style={{display:'flex', justifyContent:'space-between', width:'100%'}}>
                <span style={{fontWeight:600, fontSize:13}}>
                  {estadoEmoji[a.estado]||'⚪'} {a.agente}
                  <span style={{fontWeight:400, color:'var(--text-dim)', marginLeft:6, fontSize:11}}>
                    {(a.confianza*100).toFixed(0)}%
                  </span>
                </span>
              </div>
              {a.detectando && <div style={{fontSize:12, color:'var(--text)'}}>
                Detecta: {a.detectando}
              </div>}
              {a.accion_propuesta && <div style={{fontSize:12, color:'var(--indigo)'}}>
                Propone: {a.accion_propuesta}
              </div>}
              {a.conflicto_con?.length > 0 && <div style={{fontSize:11, color:'#ef4444'}}>
                ⚡ Conflicto con {a.conflicto_con.join(', ')}
              </div>}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
```

#### 1B. Nuevo módulo: "Estrategia de la semana" (Director Opus)

Chip: 🎼 Estrategia

Muestra la última decisión del Director Opus: estado del sistema, dirección estratégica, qué agentes reconfiguró y por qué.

```jsx
function EstrategiaPanel() {
  const [director, setDirector] = useState(null);
  useEffect(() => {
    fetch(`${PREFIX}/organismo/director`)
      .then(r => r.json())
      .then(setDirector);
  }, []);

  if (!director) return <div style={S.empty}>Director aún no ha ejecutado</div>;

  return (
    <div>
      <div style={{fontSize:13, fontWeight:600, marginBottom:8}}>
        {director.estado_sistema}
      </div>
      <div style={{fontSize:13, color:'var(--text)', marginBottom:12,
                   padding:8, background:'rgba(99,102,241,0.08)', borderRadius:8}}>
        {director.estrategia_global}
      </div>
      <div style={{fontSize:11, color:'var(--text-dim)', fontWeight:600, marginBottom:4}}>
        Agentes reconfigurados:
      </div>
      {director.configs?.map(c => (
        <div key={c.agente} style={{...S.row, flexDirection:'column', alignItems:'flex-start'}}>
          <span style={{fontWeight:600, fontSize:12}}>{c.agente}</span>
          <span style={{fontSize:11, color:'var(--text-dim)'}}>{c.justificacion?.slice(0, 150)}</span>
        </div>
      ))}
    </div>
  );
}
```

#### 1C. Nuevo módulo: "¿Funcionó?" (Evaluador)

Chip: 📊 Evaluación

Muestra si la prescripción de la semana pasada movió las lentes.

```jsx
function EvaluacionPanel() {
  const [eval_, setEval] = useState(null);
  useEffect(() => {
    fetch(`${PREFIX}/organismo/evaluacion`)
      .then(r => r.json())
      .then(setEval);
  }, []);

  if (!eval_) return <div style={S.empty}>Sin evaluación disponible</div>;

  const eg = eval_.evaluacion_global || {};
  const emoji = {si:'✅', parcialmente:'🟡', no:'❌'}[eg.prescripcion_funciono] || '❓';

  return (
    <div>
      <div style={{fontSize:20, fontWeight:700, marginBottom:4}}>
        {emoji} Prescripción: {eg.prescripcion_funciono}
      </div>
      <div style={{fontSize:13, color:'var(--text)', marginBottom:12}}>
        {eg.conclusion}
      </div>

      {/* Deltas de lentes */}
      {eval_.delta_lentes && (
        <div style={{display:'flex', gap:12, marginBottom:12}}>
          {Object.entries(eval_.delta_lentes).map(([lente, d]) => {
            const color = d.delta > 0.02 ? '#22c55e' : d.delta < -0.02 ? '#ef4444' : 'var(--text-dim)';
            const arrow = d.delta > 0.02 ? '↑' : d.delta < -0.02 ? '↓' : '→';
            return (
              <div key={lente} style={{flex:1, textAlign:'center', padding:8,
                                       background:'var(--bg)', borderRadius:8}}>
                <div style={{fontSize:11, color:'var(--text-dim)', textTransform:'uppercase'}}>{lente}</div>
                <div style={{fontSize:18, fontWeight:700, color}}>
                  {arrow} {d.delta > 0 ? '+' : ''}{(d.delta*100).toFixed(0)}%
                </div>
                <div style={{fontSize:10, color:'var(--text-dim)'}}>
                  {d.anterior?.toFixed(2)} → {d.actual?.toFixed(2)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {eval_.recomendaciones?.length > 0 && (
        <div>
          <div style={{fontSize:11, fontWeight:600, color:'var(--text-dim)', marginBottom:4}}>
            RECOMENDACIONES PARA ESTA SEMANA:
          </div>
          {eval_.recomendaciones.map((r, i) => (
            <div key={i} style={{fontSize:12, padding:'4px 0',
                                 borderBottom:'1px solid var(--border)'}}>
              {r}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

#### 1D. Feed cognitivo separado

El feed actual mezcla "sesión completada" con "convergencia AF1↔AF3 detectada". Separar en dos feeds o filtrar:

```jsx
// En FeedInline, añadir filtro:
const FEED_COGNITIVO = ['organismo_director', 'organismo_evaluador', 'organismo_guardian',
                         'organismo_metacog', 'organismo_huerfanas', 'organismo_cristalizador',
                         'organismo_ingeniero'];

// Nuevo módulo: Feed Cognitivo
function FeedCognitivo() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    api.getFeed({limit: 20, categoria: 'organismo'}).then(r => setItems(Array.isArray(r) ? r : []));
  }, []);
  // ... mismo render que FeedInline pero solo con items cognitivos
}
```

#### 1E. Chat con acceso a la pizarra

Modificar `SYSTEM_COCKPIT` en `cockpit.py` para que el chat pueda leer la pizarra:

```python
# En la función chat_conversacional(), antes de llamar al LLM:

# Leer pizarra para dar contexto al chat
from src.pilates.pizarra import resumen_narrativo
pizarra_resumen = await resumen_narrativo()

# Inyectar en el system prompt:
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

#### 1F. Módulos nuevos en cockpit.py

```python
# Añadir a MODULOS dict:
    "pizarra":          {"nombre": "Pizarra organismo",    "icono": "📋", "endpoint": "/organismo/pizarra"},
    "estrategia":       {"nombre": "Estrategia semana",    "icono": "🎼", "endpoint": "/organismo/director"},
    "evaluacion":       {"nombre": "¿Funcionó?",           "icono": "📊", "endpoint": "/organismo/evaluacion"},
    "feed_cognitivo":   {"nombre": "Feed cognitivo",        "icono": "🧠", "endpoint": "/feed?categoria=organismo"},
    "bus":              {"nombre": "Bus señales",            "icono": "📡", "endpoint": "/organismo/bus"},
```

#### 1G. Endpoints nuevos en router.py

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

## PARTE 2: /profundo — Ventana al cerebro del organismo

### Qué cambiar:

#### 2A. Tab "ACD" → "Diagnóstico" (automático, no manual)

Eliminar el botón "Ejecutar diagnóstico ACD (~$0.01)". El diagnóstico es automático semanal.
Mostrar en su lugar:
- Último diagnóstico con evolución (gráfico de 4 semanas de S/Se/C)
- Repertorio INT×P×R actual (qué inteligencias tiene el negocio)
- Prescripción actual (qué inteligencias activar)
- Evaluación (¿funcionó la anterior?)

#### 2B. Nuevo tab: "Organismo"

Muestra la pizarra completa + bus de señales + gomas en tiempo real.

```jsx
// Tab "Organismo" en Profundo.jsx
{tab === 'organismo' && (
  <div>
    {/* Estado de las gomas */}
    <div style={s.card}>
      <h3 style={s.cardTitle}>Circuito de gomas</h3>
      <div style={{display:'flex', gap:8, flexWrap:'wrap'}}>
        {['G1 Datos→Señales', 'G2 Señales→Diagnóstico', 'G3 Diagnóstico→Búsqueda',
          'G4 Búsqueda→Prescripción', 'G5 Prescripción→Acción', 'G6 Acción→Aprendizaje',
          'META Rotura→Reparación'].map(g => (
          <span key={g} style={{padding:'4px 10px', borderRadius:20, fontSize:11,
                                background:'#dcfce7', color:'#16a34a', fontWeight:600}}>
            ✅ {g}
          </span>
        ))}
      </div>
    </div>

    {/* Pizarra completa */}
    <div style={s.card}>
      <h3 style={s.cardTitle}>Pizarra del organismo (ciclo actual)</h3>
      {/* Render de pizarra agrupada por capas, con conflictos destacados */}
    </div>

    {/* Bus de señales últimas 24h */}
    <div style={s.card}>
      <h3 style={s.cardTitle}>Bus de señales (últimas 24h)</h3>
      {/* Timeline de señales: DIAGNOSTICO, PRESCRIPCION, VETO, ALERTA, OPORTUNIDAD */}
    </div>
  </div>
)}
```

#### 2C. Nuevo tab: "Director"

Muestra las partituras del Director Opus: estrategia global + prompts de cada AF.

```jsx
{tab === 'director' && (
  <div>
    <div style={{...s.card, borderLeft:'4px solid #6366f1'}}>
      <h3 style={s.cardTitle}>Estrategia de la semana</h3>
      <div style={{fontSize:15, fontWeight:600}}>{director?.estado_sistema}</div>
      <div style={{fontSize:14, color:'#374151', marginTop:8}}>{director?.estrategia_global}</div>
    </div>

    {director?.configs?.map(c => (
      <div key={c.agente} style={s.card}>
        <h3 style={s.cardTitle}>{c.agente} — Partitura</h3>
        <div style={{fontSize:12, color:'#6b7280', marginBottom:8}}>{c.justificacion}</div>

        {/* INTs asignadas */}
        <div style={{display:'flex', gap:4, flexWrap:'wrap', marginBottom:8}}>
          {c.INT_activas?.map(i => (
            <span key={i.id} style={{padding:'2px 8px', borderRadius:12, fontSize:11,
                                     background:'#eef2ff', color:'#6366f1'}}>
              {i.id} {i.nombre}
            </span>
          ))}
        </div>

        {/* Prompt D_híbrido: preguntas del cálculo semántico */}
        {c.prompt_d_hibrido?.preguntas?.map((q, i) => (
          <div key={i} style={{fontSize:13, padding:'6px 0', borderBottom:'1px solid #f3f4f6'}}>
            <span style={{color:'#6366f1', fontWeight:600}}>[{q.int}]</span> {q.pregunta}
          </div>
        ))}

        {/* Provocación */}
        {c.prompt_d_hibrido?.provocacion && (
          <div style={{marginTop:8, padding:10, background:'#fef3c7', borderRadius:8, fontSize:13}}>
            🔥 {c.prompt_d_hibrido.provocacion}
          </div>
        )}
      </div>
    ))}
  </div>
)}
```

#### 2D. Tab "Consejo" → conectado al enjambre

En vez de empezar de cero con una pregunta, mostrar primero:
1. El último diagnóstico del enjambre (qué dijeron los 13 clusters)
2. El resultado del guardián (qué sesgos detectó)
3. DESPUÉS la opción de profundizar con un asesor del séquito

#### 2E. Tabs actualizados de /profundo

```python
TABS = [
    'dashboard',       # KPIs + alertas + tendencia (mantener)
    'diagnostico',     # ACD automático + evolución + repertorio (antes "acd")
    'organismo',       # NUEVO: pizarra + bus + gomas
    'director',        # NUEVO: partituras Opus + prompts D_híbrido
    'consejo',         # Séquito conectado al enjambre (mejorado)
    'voz',             # Bloque Voz (mantener)
    'adn',             # ADN del negocio (mantener)
    'depuracion',      # F3 (mantener)
    'contabilidad',    # Ingresos + facturación (mantener)
]
```

---

## PARTE 3: Interfaz de voz — Jesús habla con el organismo

### Arquitectura

```
JESÚS HABLA
    |
    v
Web Speech API (navegador) → Speech-to-Text
    |
    v
Texto transcrito → /pilates/cockpit/chat (endpoint EXISTENTE)
    |
    v
cockpit.py procesa (con pizarra + contexto + módulos)
    |
    v
Respuesta texto ← cockpit chat response
    |
    v
Web Speech API (navegador) → Text-to-Speech
    |
    v
JESÚS ESCUCHA LA RESPUESTA
```

**NO necesita infraestructura nueva.** El browser tiene Web Speech API nativa (Chrome la soporta perfectamente en desktop). El backend es el mismo endpoint de chat que ya existe.

La diferencia: el chat actual es texto→texto. El nuevo canal es voz→texto→texto→voz. Solo cambia la capa de entrada/salida en el frontend.

### Componente: VoicePanel

```jsx
function VoicePanel({ onTranscript }) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [speaking, setSpeaking] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      return; // Navegador no soporta
    }

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
        onTranscript(text); // Envía al chat como si escribiera
      }
    };

    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
  }, [onTranscript]);

  const toggleListening = () => {
    if (listening) {
      recognitionRef.current?.stop();
    } else {
      setTranscript('');
      recognitionRef.current?.start();
      setListening(true);
    }
  };

  return (
    <div style={{display:'flex', alignItems:'center', gap:8}}>
      <button
        onClick={toggleListening}
        style={{
          width: 44, height: 44, borderRadius: '50%', border: 'none',
          background: listening ? '#ef4444' : 'var(--indigo, #6366f1)',
          color: '#fff', fontSize: 20, cursor: 'pointer',
          animation: listening ? 'pulse 1.5s infinite' : 'none',
        }}>
        {listening ? '⏹' : '🎤'}
      </button>
      {transcript && <span style={{fontSize:12, color:'var(--text-dim)'}}>{transcript}</span>}
    </div>
  );
}

// Función para hablar la respuesta
function speak(text) {
  if (!('speechSynthesis' in window)) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'es-ES';
  utterance.rate = 1.0;
  utterance.pitch = 1.0;
  // Buscar voz española
  const voices = speechSynthesis.getVoices();
  const spanishVoice = voices.find(v => v.lang.startsWith('es'));
  if (spanishVoice) utterance.voice = spanishVoice;
  speechSynthesis.speak(utterance);
}
```

### Integración en EstudioCockpit

```jsx
// En el header, junto al input de chat:
<div style={S.chatBox}>
  <VoicePanel onTranscript={(text) => {
    setChatInput(text);
    // Auto-enviar después de recibir transcripción final
    setTimeout(() => enviarChat(), 100);
  }} />
  <input
    style={S.chatInput}
    placeholder="Escribe o habla..."
    value={chatInput}
    onChange={e => setChatInput(e.target.value)}
    onKeyDown={e => e.key === 'Enter' && enviarChat()}
  />
  <button style={S.chatBtn} onClick={enviarChat}>→</button>
</div>

// Cuando llega la respuesta del chat, hablarla:
const enviarChat = async () => {
  // ... código existente ...
  if (data.respuesta) {
    setChatResp(data.respuesta);
    speak(data.respuesta); // ← HABLAR la respuesta
  }
};
```

### Comandos de voz naturales

Con el chat ya procesando lenguaje natural via gpt-4o, Jesús puede decir:

```
"¿Cómo está el estudio?"
→ Chat lee pizarra + resumen + alertas → responde por voz

"¿Qué piensa AF3 del grupo del jueves?"
→ Chat lee pizarra de AF3 → responde por voz

"¿Funcionó lo de la semana pasada?"
→ Chat lee evaluador → responde por voz

"Ponme la pizarra del organismo"
→ Chat monta módulo pizarra → responde "He montado la pizarra"

"Cierra el grupo del jueves"
→ Chat ejecuta operación → responde por voz confirmación/advertencia

"Marca las asistencias de las 10"
→ Chat ejecuta operación → responde por voz

"Genera propuestas de voz para esta semana"
→ Chat llama a /voz/generar-propuestas → responde con resumen
```

NO necesita NLU especial — el gpt-4o del cockpit ya entiende todo esto. Solo falta el micro y el altavoz.

### Opción premium futura: ElevenLabs TTS

Web Speech API es gratuita pero la voz es robótica. Si se quiere voz natural:

```javascript
async function speakElevenLabs(text) {
  const resp = await fetch(`${PREFIX}/voz/tts`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ texto: text }),
  });
  const blob = await resp.blob();
  const audio = new Audio(URL.createObjectURL(blob));
  audio.play();
}
```

Con un endpoint backend:
```python
@router.post("/voz/tts")
async def text_to_speech(data: dict):
    """Convierte texto a voz via ElevenLabs."""
    # ~$0.002 por respuesta corta
    # Solo si ELEVENLABS_API_KEY está configurado
```

Pero para el MVP, Web Speech API es suficiente y $0.

---

## PARTE 4: Consistencia visual

### Unificar tema

`/estudio` (dark) y `/profundo` (light) son visualmente diferentes. Para desktop está bien — son dos contextos mentales diferentes. Pero añadir toggle de tema en ambas:

```jsx
// Botón en header de ambas:
<button onClick={() => toggleTheme()}>🌓</button>
```

### Navegación entre ambas

Añadir link en ambas para saltar a la otra:

```jsx
// En /estudio header:
<a href="/profundo" style={S.navLink}>Modo profundo →</a>

// En /profundo header:
<a href="/estudio" style={S.navLink}>← Modo estudio</a>
```

---

## RESUMEN DE CAMBIOS

### Frontend (EstudioCockpit.jsx):
1. Nuevo: `PizarraPanel` componente
2. Nuevo: `EstrategiaPanel` componente (Director Opus)
3. Nuevo: `EvaluacionPanel` componente (¿Funcionó?)
4. Nuevo: `FeedCognitivo` componente (solo eventos del organismo)
5. Nuevo: `VoicePanel` componente (STT + TTS)
6. Modificar: `enviarChat()` → hablar respuesta
7. Añadir: CSS animación pulse para botón micro
8. Registrar 5 nuevos módulos en `MODULO_COMPONENTS`

### Frontend (Profundo.jsx):
1. Nuevo tab: "organismo" (pizarra + bus + gomas)
2. Nuevo tab: "director" (partituras D_híbrido)
3. Modificar tab "acd" → "diagnostico" (sin botón manual, con evolución)
4. Modificar tab "consejo" → conectado al enjambre

### Backend (cockpit.py):
1. Ampliar MODULOS dict con 5 módulos nuevos
2. Ampliar SYSTEM_COCKPIT con contexto de pizarra
3. Leer pizarra en `chat_conversacional()` antes de llamar al LLM

### Backend (router.py):
1. Nuevo: GET `/organismo/director`
2. Nuevo: GET `/organismo/evaluacion`
3. Futuro: POST `/voz/tts` (ElevenLabs, opcional)

### Sin cambios backend para voz STT:
Web Speech API es 100% frontend. El texto transcrito va al mismo endpoint `/pilates/cockpit/chat` que ya existe.

---

## COSTE

| Componente | Coste |
|---|---|
| Web Speech API (STT) | $0 (nativo en Chrome) |
| Web Speech API (TTS) | $0 (nativo en Chrome) |
| Módulos nuevos frontend | $0 (código) |
| Pizarra en chat cockpit | +~$0.001/chat (más tokens en prompt) |
| ElevenLabs TTS (futuro) | ~$0.002/respuesta |
| **Total** | **$0** (con Web Speech) |

## TESTS

### T1: Módulo pizarra muestra agentes
```
GET /organismo/pizarra → debe devolver ≥1 entrada
Frontend: chip "Pizarra" monta PizarraPanel con agentes agrupados por capa
```

### T2: Módulo estrategia muestra Director
```
GET /organismo/director → debe devolver estado_sistema + estrategia_global
```

### T3: Módulo evaluación muestra deltas
```
GET /organismo/evaluacion → debe devolver delta_lentes con S/Se/C
```

### T4: Chat responde preguntas sobre organismo
```
POST /cockpit/chat {mensaje: "¿Qué piensa AF3?"}
→ respuesta debe mencionar lo que AF3 escribió en la pizarra
```

### T5: Voz STT→chat→TTS funciona
```
En Chrome: pulsar 🎤 → decir "¿Cómo está el estudio?" → texto aparece en input
→ se envía al chat → respuesta aparece en chatResp → se habla por altavoz
```
