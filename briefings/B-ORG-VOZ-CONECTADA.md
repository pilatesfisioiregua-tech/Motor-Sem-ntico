# B-ORG-VOZ-CONECTADA: El Bloque Voz como órgano vivo del organismo

**Fecha:** 23 marzo 2026
**Prioridad:** Alta — el escaparate del negocio no refleja lo que el organismo piensa
**Dependencia:** B-ORG-AF5 + B-ORG-DIRECTOR + B-ORG-PIZARRA

---

## EL PROBLEMA EN UNA FRASE

El organismo diagnostica que F5.Se=0.25 ("identidad no comunicada"), el Director Opus escribe una partitura brillante para AF5 con INT-12+P12+R04 ("cuenta la historia de EEDAP"), y... nada pasa. Porque los 7 archivos voz_* no leen la partitura del Director ni el diagnóstico del organismo. Y Jesús tiene que entrar a /profundo → tab Voz → pulsar "generar propuestas" → aprobar 1 a 1 → ejecutar manualmente.

## LO QUE DEBERÍA PASAR

```
LUNES 06:30 (automático):
  1. Director Opus escribió partitura AF5: "Esta semana: comunicar diferenciación EEDAP.
     INT-12 para contar historia, P12 para narrativa, R04 para analogía con otras disciplinas."
  
  2. AF5 (nuevo, unificado) se ejecuta:
     - Lee partitura del Director (om_config_agentes)
     - Lee diagnóstico (F5.Se=0.25, gap identidad)
     - Lee pizarra (AF3 quiere cerrar 2 grupos → oportunidad de comunicar "menos pero mejor")
     - Dispara voz_ciclos con CONTEXTO del organismo
  
  3. voz_ciclos.escuchar() → lee Capa A (tendencias sector), Capa B (datos negocio), Capa C (audiencia)
  
  4. voz_ciclos.priorizar() → con INPUT del diagnóstico ACD:
     - "F5.Se baja + enjambre dice 'identidad no articulada' → prioridad: contenido de diferenciación"
     - "AF3 cerró grupo sábados → oportunidad: comunicar 'menos grupos, más calidad'"
  
  5. voz_ciclos.proponer() → genera 3-5 propuestas ALINEADAS con el organismo:
     - WA broadcast: "Historia del método EEDAP en 3 párrafos" (INT-12)
     - GBP post: "Por qué Pilates terapéutico no es fitness" (R04: analogía)
     - IG story: "Antes/después de cerrar grupos: más atención personal" (P12: narrativa)
  
  6. Propuestas aparecen en /estudio como MÓDULO PRIORITARIO:
     🔔 "3 propuestas de voz alineadas con el diagnóstico de esta semana"
     [Aprobar todas] [Ver una a una] [Modificar]
  
  7. Jesús aprueba desde /estudio (no necesita ir a /profundo):
     - Click "aprobar" → se encola para envío
     - Click "modificar" → edita texto → aprueba
     - Click "programar" → elige hora de envío
  
  8. Ejecución automática o programada:
     - WA: envío via API Business (si configurado) o genera texto para copiar
     - GBP: genera post para copiar (API futura)
     - IG: genera imagen+texto para copiar (API futura)
  
  9. Telemetría → retroalimenta:
     - ¿El WA broadcast tuvo respuestas? → IRC de WA sube/baja
     - ¿El post GBP generó visitas? → ISP de GBP se actualiza
     - Resultado → entra al enjambre de la semana siguiente
     - Evaluador: "Se subió 0.03 después de comunicar diferenciación → FUNCIONÓ"
```

## CAMBIOS

### 1. AF5 usa la partitura del Director para generar contexto de Voz

En `af5_identidad.py` (B-ORG-AF5), después de detectar gaps, disparar voz_ciclos:

```python
async def ejecutar_af5() -> dict:
    # ... sensor + cerebro + bus + pizarra (ya diseñado en B-ORG-AF5) ...

    # NUEVO: Disparar ciclo de Voz con contexto del organismo
    if razonamiento.get("acciones"):
        try:
            from src.pilates.voz_ciclos import ejecutar_ciclo_completo
            propuestas = await ejecutar_ciclo_completo(
                contexto_organismo={
                    "diagnostico_estado": diagnostico_actual.get("estado"),
                    "lentes": diagnostico_actual.get("lentes"),
                    "partitura_af5": config_director,  # Lo que Opus escribió para AF5
                    "pizarra_resumen": pizarra_str,
                    "gaps_identidad": datos_sensor["detecciones"],
                    "prescripcion": prescripcion_acd,
                },
                max_propuestas=5,
            )
            resultado["propuestas_voz_generadas"] = len(propuestas)
        except Exception as e:
            log.warning("af5_voz_error", error=str(e))
    
    return resultado
```

### 2. voz_ciclos recibe contexto del organismo

Modificar `ejecutar_ciclo_completo()` en `voz_ciclos.py`:

```python
async def ejecutar_ciclo_completo(contexto_organismo: dict = None, max_propuestas: int = 5) -> list:
    """Ejecuta los 5 ciclos con contexto del organismo.
    
    ANTES: Generaba propuestas basadas solo en datos internos + Capa A.
    DESPUÉS: Usa el diagnóstico ACD + partitura del Director + pizarra
             para generar propuestas ALINEADAS con lo que el organismo piensa.
    """
    # Ciclo 1: ESCUCHAR (datos internos + Capa A + Capa C)
    señales = await escuchar()
    
    # Ciclo 2: PRIORIZAR — AHORA con contexto del organismo
    if contexto_organismo:
        # Inyectar diagnóstico ACD en la priorización
        señales = _enriquecer_con_organismo(señales, contexto_organismo)
    
    prioridades = await priorizar(señales)
    
    # Ciclo 3: PROPONER — AHORA con partitura del Director
    propuestas = await proponer(prioridades, contexto_organismo)
    
    # Ciclo 4: EJECUTAR — Solo persiste (la ejecución real la aprueba Jesús)
    ids = await persistir_propuestas(propuestas[:max_propuestas])
    
    # Ciclo 5: APRENDER — telemetría de propuestas anteriores
    await aprender()
    
    return ids


def _enriquecer_con_organismo(señales: list, ctx: dict) -> list:
    """Enriquece señales con contexto cognitivo del organismo."""
    extras = []
    
    # Si la partitura del Director tiene provocación, convertirla en señal de contenido
    partitura = ctx.get("partitura_af5", {})
    if isinstance(partitura, dict):
        prompt = partitura.get("prompt_d_hibrido", partitura.get("instruccion_completa", ""))
        preguntas = partitura.get("prompt_d_hibrido", {}).get("preguntas", [])
        provocacion = partitura.get("prompt_d_hibrido", {}).get("provocacion", "")
        
        if preguntas:
            for q in preguntas[:3]:
                pregunta = q.get("pregunta", q) if isinstance(q, dict) else str(q)
                extras.append({
                    "tipo": "directiva_director",
                    "contenido": pregunta,
                    "prioridad": 1,
                    "origen": "DIRECTOR_OPUS",
                })
        if provocacion:
            extras.append({
                "tipo": "provocacion_frontera",
                "contenido": provocacion,
                "prioridad": 2,
                "origen": "DIRECTOR_OPUS",
            })
    
    # Si hay gaps de identidad, convertirlos en señales de contenido urgente
    for gap in ctx.get("gaps_identidad", []):
        if gap.get("severidad") in ("alta", "critica"):
            extras.append({
                "tipo": "gap_identidad",
                "contenido": gap.get("detalle", ""),
                "prioridad": 2,
                "origen": "AF5_SENSOR",
            })
    
    # Si la pizarra dice que AF3 cerró algo, es oportunidad de comunicar
    pizarra = ctx.get("pizarra_resumen", "")
    if "cerrar" in pizarra.lower() or "depurar" in pizarra.lower():
        extras.append({
            "tipo": "oportunidad_narrativa",
            "contenido": "AF3 depuró — oportunidad de comunicar 'menos pero mejor'",
            "prioridad": 3,
            "origen": "PIZARRA_AF3",
        })
    
    return extras + señales
```

### 3. voz_estrategia usa el diagnóstico ACD para generar contenido

Modificar `generar_propuestas()` en `voz_estrategia.py`:

```python
# En el system prompt del generador de propuestas, INYECTAR:

SYSTEM_VOZ_CON_ORGANISMO = SYSTEM_VOZ_BASE + """

CONTEXTO DEL ORGANISMO COGNITIVO (esta semana):

DIAGNÓSTICO: {estado} — S={lentes_s:.2f}, Se={lentes_se:.2f}, C={lentes_c:.2f}
GAPS IDENTIDAD: {gaps_identidad}
PRESCRIPCIÓN: {prescripcion_objetivo}

DIRECTIVAS DEL DIRECTOR OPUS PARA AF5:
{directivas_director}

REGLA FUNDAMENTAL: El contenido que generes debe estar ALINEADO con lo que el organismo
ha diagnosticado. Si F5.Se es baja, el contenido debe subir Se (diferenciación, propósito,
por qué este estudio y no otro). Si C es baja, el contenido debe contar la historia
de forma transferible (que alguien nuevo entienda el método).

NO generes contenido genérico de "pilates es bueno para la espalda" si el organismo
dice que el problema es de identidad. Cada propuesta debe atacar un gap real."""
```

### 4. Propuestas aparecen en /estudio como módulo prioritario

Nuevo componente en `EstudioCockpit.jsx`:

```jsx
function VozProactivaPanel() {
  const [propuestas, setPropuestas] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch(`${PREFIX}/voz/propuestas?estado=pendiente`)
      .then(r => r.json())
      .then(data => { setPropuestas(Array.isArray(data) ? data : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const aprobar = async (id) => {
    await fetch(`${PREFIX}/voz/propuestas/${id}`, {
      method: 'PATCH', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ estado: 'aprobada' }),
    });
    setPropuestas(prev => prev.filter(p => p.id !== id));
    toast.success('Propuesta aprobada');
  };

  const aprobarTodas = async () => {
    for (const p of propuestas) {
      await fetch(`${PREFIX}/voz/propuestas/${p.id}`, {
        method: 'PATCH', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ estado: 'aprobada' }),
      });
    }
    setPropuestas([]);
    toast.success(`${propuestas.length} propuestas aprobadas`);
  };

  const ejecutar = async (id) => {
    const r = await fetch(`${PREFIX}/voz/propuestas/${id}/ejecutar`, { method: 'POST' })
      .then(r => r.json());
    if (r.status === 'ejecutada') {
      setPropuestas(prev => prev.filter(p => p.id !== id));
      toast.success('Ejecutada');
    }
  };

  const canalColor = {whatsapp:'#25d366', instagram:'#e1306c', google_business:'#4285f4'};
  const canalIcon = {whatsapp:'💬', instagram:'📸', google_business:'📍', email:'📧'};

  if (loading) return <div style={S.empty}>Cargando...</div>;
  if (propuestas.length === 0) return <div style={S.empty}>Sin propuestas pendientes</div>;

  return (
    <div>
      {/* Batch approval */}
      <div style={{display:'flex', justifyContent:'space-between', marginBottom:8}}>
        <span style={{fontSize:12, color:'var(--text-dim)'}}>
          {propuestas.length} propuesta{propuestas.length > 1 ? 's' : ''} del organismo
        </span>
        {propuestas.length > 1 && (
          <button onClick={aprobarTodas}
            style={{fontSize:11, background:'var(--indigo)', color:'#fff',
                    border:'none', borderRadius:6, padding:'3px 10px', cursor:'pointer'}}>
            Aprobar todas
          </button>
        )}
      </div>

      {propuestas.map(p => (
        <div key={p.id} style={{
          ...S.row, flexDirection:'column', alignItems:'flex-start', gap:6,
          borderLeft: `3px solid ${canalColor[p.canal] || '#6366f1'}`, paddingLeft: 10,
        }}>
          {/* Header: canal + tipo + origen */}
          <div style={{display:'flex', gap:8, alignItems:'center', width:'100%'}}>
            <span>{canalIcon[p.canal] || '📢'}</span>
            <span style={{fontSize:11, fontWeight:600, color:canalColor[p.canal] || 'var(--text)',
                          textTransform:'uppercase'}}>{p.canal}</span>
            <span style={{fontSize:10, color:'var(--text-dim)'}}>{p.tipo?.replace(/_/g,' ')}</span>
            {p.eje2_celda && <span style={{fontSize:10, color:'var(--text-dim)'}}>({p.eje2_celda})</span>}
          </div>

          {/* Justificación (del organismo) */}
          <div style={{fontSize:12, color:'var(--text)'}}>{p.justificacion}</div>

          {/* Contenido propuesto */}
          {p.contenido_propuesto?.texto && (
            <div style={{fontSize:12, color:'var(--text-dim)', fontStyle:'italic',
                         background:'rgba(99,102,241,0.05)', padding:8, borderRadius:6, width:'100%'}}>
              {p.contenido_propuesto.texto}
            </div>
          )}

          {/* Acciones */}
          <div style={{display:'flex', gap:6}}>
            <button onClick={() => aprobar(p.id)}
              style={{fontSize:11, background:'#22c55e', color:'#fff', border:'none',
                      borderRadius:4, padding:'3px 10px', cursor:'pointer'}}>
              Aprobar
            </button>
            <button onClick={() => ejecutar(p.id)}
              style={{fontSize:11, background:'var(--indigo)', color:'#fff', border:'none',
                      borderRadius:4, padding:'3px 10px', cursor:'pointer'}}>
              Ejecutar ahora
            </button>
            <button onClick={() => {/* editar */}}
              style={{fontSize:11, background:'var(--surface)', color:'var(--text-dim)',
                      border:'1px solid var(--border)', borderRadius:4, padding:'3px 10px', cursor:'pointer'}}>
              Editar
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
```

Registrar en `MODULO_COMPONENTS`:
```jsx
const MODULO_COMPONENTS = {
  ...existentes,
  voz_proactiva: VozProactivaPanel,
};
```

Y en `cockpit.py`, añadir sugerencia automática:
```python
    # Si hay propuestas de voz pendientes → sugerir módulo
    voz_pendientes = ...  # ya existe
    if voz_pendientes > 0:
        sugeridos.append({"id": "voz_proactiva", "rol": "secundario"})
```

### 5. Cron semanal dispara AF5 → Voz automáticamente

En `cron.py`, paso semanal:

```python
        # 5b. AF5 Identidad — detectar gaps + disparar Voz con contexto organismo
        try:
            from src.pilates.af5_identidad import ejecutar_af5
            af5 = await ejecutar_af5()
            log.info("cron_semanal_af5_ok",
                     gaps=af5.get("gaps_identidad"),
                     propuestas_voz=af5.get("propuestas_voz_generadas", 0))
        except Exception as e:
            log.error("cron_semanal_af5_error", error=str(e))
```

### 6. Telemetría retroalimenta al enjambre

Cuando una propuesta se ejecuta y genera resultado (respuestas WA, visitas GBP), la telemetría ya existe en `om_voz_telemetria`. Falta conectarla al enjambre:

```python
# En voz_ciclos.aprender(), después de actualizar IRC/ISP:

    # Emitir al bus para que el enjambre lo vea en la próxima ejecución
    from src.pilates.bus import emitir
    await emitir("DATO", "AF5_VOZ", {
        "tipo": "telemetria_voz",
        "canal": canal,
        "propuesta_id": str(propuesta_id),
        "resultado": resultado_telemetria,
        "irc_actualizado": nuevo_irc,
    }, prioridad=7)
    
    # Escribir en pizarra
    from src.pilates.pizarra import escribir
    await escribir(
        agente="AF5",
        capa="ejecutiva",
        detectando=f"Telemetría: {canal} — {resultado_telemetria.get('engagement', 'sin datos')}",
        interpretacion=f"IRC {canal}: {nuevo_irc:.2f}",
        accion_propuesta="Ajustar estrategia si IRC < 0.30",
    )
```

### 7. El Evaluador mide si la Voz movió las lentes

En `evaluador_organismo.py`, añadir a la comparación:

```python
    # Métricas de Voz
    async with pool.acquire() as conn:
        voz_ejecutadas = await conn.fetchval("""
            SELECT count(*) FROM om_voz_propuestas
            WHERE tenant_id=$1 AND estado='ejecutada'
            AND updated_at > $2
        """, TENANT, hace_1_semana)
        
        voz_engagement = await conn.fetchval("""
            SELECT AVG((resultado->>'engagement')::float) FROM om_voz_telemetria
            WHERE tenant_id=$1 AND created_at > $2
        """, TENANT, hace_1_semana)

    # Inyectar en el prompt del evaluador:
    # "Esta semana se ejecutaron N propuestas de voz. Engagement medio: X.
    #  ¿Esto contribuyó al movimiento de Se?"
```

---

## FLUJO COMPLETO: DE DIAGNÓSTICO A ESCAPARATE

```
LUNES 06:00
  Diagnosticador → "F5.Se=0.25, estado genio_mortal"
  
LUNES 06:05
  Enjambre → 13 clusters confirman: "identidad no articulada"
  
LUNES 06:10
  Guardián → "nadie mencionó que los clientes no saben qué es EEDAP"
  
LUNES 06:15
  Director Opus → partitura AF5:
    "INT-12: cuenta la historia de POR QUÉ Pilates terapéutico.
     P12: usa narrativa, no datos clínicos.
     R04: analogía con un artesano vs fábrica.
     Provocación: '¿Y si nadie sabe qué es EEDAP porque ni tú lo has articulado?'"
  
LUNES 06:20
  AF5 se ejecuta:
    - Lee partitura del Director
    - Lee diagnóstico + pizarra (AF3 cerró grupo sábados)
    - Dispara voz_ciclos con contexto organismo
  
LUNES 06:25
  voz_ciclos genera 4 propuestas:
    1. WA broadcast: "Hace 3 años decidí que mi estudio sería diferente..." (INT-12)
    2. GBP post: "No somos un gimnasio con máquinas de Pilates" (R04: analogía)
    3. IG story: "Con menos grupos, más tiempo para ti" (P12: narrativa AF3)
    4. GBP respuesta reseña: personalizada con identidad EEDAP
  
LUNES 07:00
  Jesús abre /estudio. Ve:
    🔔 "4 propuestas de voz del organismo"
    [chip activo: "📢 Voz proactiva"]
    
    → Aprueba 3, modifica 1 ("cambio esta frase por..."), descarta 0
    → Click "ejecutar WA" → texto copiado/enviado
    → Click "programar GBP" → encola para las 12:00
  
SEMANA SIGUIENTE
  Evaluador: "Se subió de 0.25 a 0.29. 3 propuestas ejecutadas.
              WA tuvo 8 respuestas (engagement alto).
              GBP tuvo 2 reseñas nuevas mencionando 'terapéutico'.
              → La Voz CONTRIBUYÓ al movimiento de Se."
  Director: "Se sigue baja. Mantener dirección. Reforzar GBP que funcionó."
```

---

## RESUMEN DE CAMBIOS

### Backend:
1. `af5_identidad.py` (B-ORG-AF5) → dispara `voz_ciclos` con contexto organismo
2. `voz_ciclos.py` → `ejecutar_ciclo_completo(contexto_organismo)` acepta input del organismo
3. `voz_ciclos.py` → `_enriquecer_con_organismo()` convierte partituras en señales de contenido
4. `voz_estrategia.py` → system prompt enriquecido con diagnóstico ACD + directivas Director
5. `voz_ciclos.py` → `aprender()` emite al bus + pizarra
6. `evaluador_organismo.py` → incluye métricas de voz en la evaluación
7. `cockpit.py` → módulo "voz_proactiva" sugerido si hay propuestas pendientes
8. `cron.py` → paso semanal incluye AF5 completo con Voz

### Frontend:
1. `EstudioCockpit.jsx` → `VozProactivaPanel` con aprobación batch + ejecución
2. Registrar "voz_proactiva" en `MODULO_COMPONENTS` y en cockpit.py

### Sin cambios:
- Los 7 archivos voz_* siguen existiendo. AF5 los ORQUESTA, no los reemplaza.
- Las 9 tablas om_voz_* siguen igual.
- El tab "Voz" de /profundo sigue para análisis profundo (IRC, ISP, Capa A).

## COSTE

$0 adicional. AF5 ya usa gpt-4o (~$0.02/semana). Las propuestas las genera voz_estrategia que ya existe. Solo cambia el INPUT (ahora enriquecido con organismo).

## TESTS

### T1: AF5 dispara voz_ciclos con contexto
```python
result = await ejecutar_af5()
assert result.get("propuestas_voz_generadas", 0) >= 1
```

### T2: Propuestas incluyen directivas del Director
```sql
SELECT justificacion FROM om_voz_propuestas
WHERE tenant_id='authentic_pilates' AND estado='pendiente'
ORDER BY created_at DESC LIMIT 3;
-- Debe mencionar diagnóstico ACD o INT del Director
```

### T3: Telemetría emite al bus
```sql
SELECT count(*) FROM om_senales_agentes
WHERE origen='AF5_VOZ' AND tipo='DATO';
```

### T4: Módulo voz_proactiva aparece en cockpit si hay propuestas
```python
ctx = await contexto_del_dia()
if voz_pendientes > 0:
    ids = [m["id"] for m in ctx["modulos_sugeridos"]]
    assert "voz_proactiva" in ids
```
