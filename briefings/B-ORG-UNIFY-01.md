# B-ORG-UNIFY-01: Unificar Enjambre con tcf/ — Una sola cadena causal

**Fecha:** 23 marzo 2026 (ACTUALIZADO: LLM para percibir, código para razonar)
**Prioridad:** Alta — elimina duplicación, reduce coste, aumenta fiabilidad
**Dependencia:** B-ORG-F2-01 a F2-04 ejecutados

---

## EL PROBLEMA

Hay dos sistemas paralelos que hacen lo mismo:

| Qué hace | `src/tcf/` (código puro) | `src/pilates/enjambre.py` (LLM) |
|---|---|---|
| Inferir repertorio INT×P×R | `repertorio.inferir_repertorio()` — 1 LLM call barata + IC2-IC6 en código | 3 agentes LLM (Detector Repertorio + Disfunciones + Causal) |
| Prescribir INT×P×R | `prescriptor.prescribir()` — código puro, $0 | Estratega LLM |
| Coste | ~$0.003 | ~$0.50 |
| Verificaciones IC | Deterministas, en código, exhaustivas | Dependen de que el LLM las recuerde del prompt |

Y además, `_metricas_a_lentes()` usa fórmulas heurísticas con pesos inventados (0.4, 0.3, 0.3) que no capturan la realidad. Un LLM vería que "15 grupos infrautilizados que no cierra" revela más sobre Se que cualquier fórmula.

## LA SOLUCIÓN — El híbrido perfecto

```
LLM PARA PERCIBIR   →  Datos reales → evaluar_funcional() → 21 scores F×L
CÓDIGO PARA RAZONAR  →  21 scores → campo, lentes, estado, flags, prescripción ($0)
LLM PARA CONTEXTUALIZAR → Prescripción genérica → acciones concretas para este negocio
```

Cada capa hace lo que hace mejor:
- El LLM es MEJOR percibiendo matices: "15 grupos infrautilizados" → F3.Se muy baja
- El código es MEJOR razonando: "gap<0.15 + gradiente<0.20 = E1" → SIEMPRE correcto
- El LLM es MEJOR contextualizando: "activar INT-12" → "grabar 3 vídeos de tu método"

## CAMBIOS

### ARCHIVO 1: `src/pilates/diagnosticador.py` — Pipeline completo P1→P4

**CAMBIO CRÍTICO:** ELIMINAR `_metricas_a_lentes()` y `_metricas_a_vector_f()` (fórmulas heurísticas).
REEMPLAZAR por: pasar las métricas reales como texto estructurado a `tcf/evaluador_funcional.evaluar_funcional()`.

El LLM del evaluador funcional ya tiene el system prompt perfecto (7F×3L con escala 0.0-1.0).
Solo necesita recibir datos REALES en vez de un párrafo genérico.

**Cambios concretos en `diagnosticar_tenant()`:**

ELIMINAR estas dos funciones completas:
```python
# ELIMINAR: _metricas_a_lentes() — fórmulas heurísticas con pesos inventados
# ELIMINAR: _metricas_a_vector_f() — fórmulas heurísticas con pesos inventados
```

REEMPLAZAR el bloque después de `metricas = await _recopilar_metricas()`:

```python
    # === P1: EVALUAR FUNCIONAL via LLM (percepción real, no heurística) ===
    from src.tcf.evaluador_funcional import evaluar_funcional

    # Construir texto RICO con datos reales para que el LLM perciba correctamente
    texto_caso = f"""AUTHENTIC PILATES — Estudio de Pilates en Albelda de Iregua (La Rioja, España).
Instructor único: Jesús. Método EEDAP (Pilates auténtico/terapéutico).
Pueblo de ~4.000 habitantes, cabeza de comarca, cerca de Logroño.

DATOS REALES DE LAS ÚLTIMAS 4 SEMANAS:

RETENCIÓN (F1):
- Clientes con contrato activo: {metricas['total_activos']}
- Bajas en el periodo: {metricas['bajas_periodo']}
- Tasa retención: {100 - round(metricas['bajas_periodo'] / max(metricas['total_activos'], 1) * 100)}%

CAPTACIÓN (F2):
- Nuevos clientes: {metricas['nuevos_clientes']}
- Ratio nuevos/activos: {round(metricas['nuevos_clientes'] / max(metricas['total_activos'], 1) * 100, 1)}%

DEPURACIÓN (F3):
- Sesiones grupo totales: {metricas['sesiones_grupo']}
- Sesiones con menos de 3 alumnos (infrautilizadas): {metricas['sesiones_bajas']}
- % sesiones infrautilizadas: {round(metricas['sesiones_bajas'] / max(metricas['sesiones_grupo'], 1) * 100)}%
- NOTA: El estudio tiene ~16 grupos programados. Si la mayoría están infrautilizados
  y no se cierran ni fusionan, eso indica F3 MUY baja — no hay proceso de eliminar
  lo que no funciona.

DISTRIBUCIÓN (F4):
- Total asistencias registradas: {metricas['total_asistencias']}
- Media asistentes por sesión grupo: {round(metricas['total_asistencias'] / max(metricas['sesiones_grupo'], 1), 1)}
- NOTA: Si hay días sobrecargados y otros vacíos, F4 es baja.
  Instructor único = cuello de botella de distribución.

IDENTIDAD/FRONTERA (F5):
- Señales de voz (contenido, comunicación): {metricas['senales_voz']}
- Tensiones registradas: {metricas['tensiones']}
- NOTA: Si hay pocas señales de voz, el estudio no comunica su diferenciación.
  Si hay pocas tensiones registradas, no se está monitorizando el entorno.
  Método EEDAP es potencialmente un diferenciador fuerte, pero ¿está articulado?

ADAPTACIÓN (F6):
- Tensiones abiertas: {metricas['tensiones']}
- NOTA: Si hay tensiones sin resolver durante semanas, F6 es baja.
  Si no hay tensiones registradas, puede ser que no se monitoriza el entorno
  (F6 también baja pero por ceguera, no por estabilidad).

REPLICACIÓN (F7):
- Procesos documentados: {metricas['procesos']}
- NOTA: Instructor único sin procesos documentados = F7 MUY baja.
  Si Jesús no puede venir mañana, ¿un sustituto sabría qué hacer?
  ¿Cuánto del método está en su cabeza vs documentado?

FINANZAS (contexto para todas las F):
- Cobrado en el periodo: {metricas['cobrado']:.0f}€
- Pendiente de cobro: {metricas['pendiente']:.0f}€
- Ratio cobro: {round(metricas['cobrado'] / max(metricas['cobrado'] + metricas['pendiente'], 1) * 100)}%

EVALÚA las 7 funciones × 3 lentes con estos datos reales.
Para la lente SENTIDO (Se): pregúntate si el negocio COMPRENDE POR QUÉ hace lo que hace.
Si tiene 16 grupos y la mayoría están infrautilizados sin cerrar ninguno, Se es baja
(no cuestiona, no depura con criterio, opera por inercia).
Para la lente CONTINUIDAD (C): pregúntate si esto sobreviviría sin el fundador.
Si 0 procesos documentados y método en la cabeza de una persona, C es MUY baja."""

    try:
        scores_raw, vector = await evaluar_funcional(texto_caso)
        log.info("diagnosticador_p1_ok", vector=vector.to_dict(), eslabon=vector.eslabon_debil())
    except Exception as e:
        log.error("diagnosticador_p1_error", error=str(e))
        # Fallback: si el LLM falla, usar heurística degradada
        scores_raw, vector, lentes = _fallback_heuristico(metricas)
        estado = clasificar_estado(lentes)
        return {
            "diagnostico_id": None,
            "estado": estado.id, "nombre": estado.nombre,
            "lentes": lentes, "vector_f": vector.to_dict() if hasattr(vector, 'to_dict') else vector,
            "fallback": True, "error": str(e)[:200],
        }

    # === P2: EVALUAR CAMPO COMPLETO (código puro, $0) ===
    from src.tcf.campo import evaluar_campo
    estado_campo = evaluar_campo(vector)
    lentes = estado_campo.lentes
    log.info("diagnosticador_p2_ok", lentes=lentes)

    # === P3: CLASIFICAR ESTADO (código puro, $0) ===
    scores_f_se = {fi: scores_raw[fi]["sentido"] for fi in scores_raw}
    estado = clasificar_estado(lentes, scores_f_se)
    log.info("diagnosticador_p3_ok", estado=estado.id, gap=estado.gap)

    # === P4: INFERIR REPERTORIO INT×P×R (1 LLM barata + IC2-IC6 en código) ===
    from src.tcf.repertorio import inferir_repertorio

    try:
        repertorio = await inferir_repertorio(texto_caso, vector)
        log.info("diagnosticador_p4_ok",
                 activas=len(repertorio.ints_activas),
                 advertencias=len(repertorio.advertencias_ic))
    except Exception as e:
        log.warning("diagnosticador_p4_error", error=str(e))
        repertorio = None

    # === ENSAMBLAR DIAGNÓSTICO COMPLETO ===
    from src.tcf.diagnostico import DiagnosticoCompleto
    diagnostico_completo = DiagnosticoCompleto(
        scores_raw=scores_raw,
        vector=vector,
        estado_campo=estado_campo,
        estado=estado,
        repertorio=repertorio,
    ) if repertorio else None

    # === PRESCRIPCIÓN (código puro, $0) ===
    prescripcion_acd = None
    if diagnostico_completo:
        try:
            from src.tcf.prescriptor import prescribir
            prescripcion_acd = prescribir(diagnostico_completo)
            log.info("diagnosticador_prescripcion_ok",
                     ints=len(prescripcion_acd.ints),
                     ps=len(prescripcion_acd.ps),
                     rs=len(prescripcion_acd.rs),
                     objetivo=prescripcion_acd.objetivo)
        except Exception as e:
            log.warning("diagnosticador_prescripcion_error", error=str(e))

    # === PERSISTIR ===
    diag_data = {
        "caso_input": f"Diagnóstico autónomo Authentic Pilates — {datetime.now(timezone.utc).isoformat()[:10]}",
        "vector_pre": json.dumps(vector.to_dict()),
        "lentes_pre": json.dumps(lentes),
        "estado_pre": estado.id,
        "flags_pre": [f.nombre for f in estado.flags] if estado.flags else [],
        "metricas": json.dumps({
            "raw": metricas,
            "scores_21": scores_raw,
            "repertorio": {
                "ints_activas": repertorio.ints_activas,
                "ints_atrofiadas": repertorio.ints_atrofiadas,
                "advertencias_ic": repertorio.advertencias_ic,
            } if repertorio else None,
        }),
        "resultado": "pendiente",
    }
    diag_id = await log_diagnostico(diag_data)

    # === COMPARAR CON ANTERIOR ===
    cambio = False
    pool = await get_pool()
    async with pool.acquire() as conn:
        anterior = await conn.fetchrow("""
            SELECT estado_pre FROM diagnosticos
            WHERE caso_input LIKE 'Diagnóstico autónomo%'
            ORDER BY created_at DESC OFFSET 1 LIMIT 1
        """)
    if anterior and anterior["estado_pre"] != estado.id:
        cambio = True

    # === EMITIR AL BUS con repertorio + prescripción ===
    if cambio or estado.flags or repertorio:
        try:
            from src.pilates.bus import emitir
            payload = {
                "estado": estado.id,
                "nombre": estado.nombre,
                "lentes": lentes,
                "gap": estado.gap,
                "flags": [f.nombre for f in estado.flags],
                "cambio": cambio,
                "anterior": anterior["estado_pre"] if anterior else None,
                "diagnostico_id": diag_id,
                "scores_21": scores_raw,
            }
            if repertorio:
                payload["repertorio"] = {
                    "ints_activas": repertorio.ints_activas,
                    "ints_atrofiadas": repertorio.ints_atrofiadas,
                    "ints_ausentes": repertorio.ints_ausentes,
                    "ps_activos": repertorio.ps_activos,
                    "rs_activos": repertorio.rs_activos,
                    "advertencias_ic": repertorio.advertencias_ic,
                }
            if prescripcion_acd:
                payload["prescripcion"] = {
                    "ints": prescripcion_acd.ints,
                    "ps": prescripcion_acd.ps,
                    "rs": prescripcion_acd.rs,
                    "secuencia": prescripcion_acd.secuencia,
                    "frenar": prescripcion_acd.frenar,
                    "lente_objetivo": prescripcion_acd.lente_objetivo,
                    "objetivo": prescripcion_acd.objetivo,
                    "advertencias_ic": prescripcion_acd.advertencias_ic,
                }
            await emitir("DIAGNOSTICO", ORIGEN, payload,
                         prioridad=2 if cambio else 4)
        except Exception as e:
            log.warning("diagnosticador_bus_error", error=str(e))

    # === ESCRIBIR EN PIZARRA ===
    try:
        from src.pilates.pizarra import escribir
        await escribir(
            agente="DIAGNOSTICADOR",
            capa="sensorial",
            estado="completado",
            detectando=f"Estado {estado.id} ({estado.nombre}), gap={estado.gap:.2f}",
            interpretacion=f"S={lentes['salud']:.2f} Se={lentes['sentido']:.2f} C={lentes['continuidad']:.2f}. "
                           f"{'Cambió vs anterior' if cambio else 'Sin cambio'}. "
                           f"{len(estado.flags)} flags de peligro.",
            accion_propuesta=f"Prescripción: {prescripcion_acd.objetivo}" if prescripcion_acd else "Sin prescripción",
            necesita_de=["ENJAMBRE"] if repertorio else [],
            confianza=0.8,
            prioridad=2 if cambio else 4,
            datos={
                "repertorio_ints_activas": repertorio.ints_activas if repertorio else [],
                "advertencias_ic": repertorio.advertencias_ic if repertorio else [],
                "prescripcion_ints": prescripcion_acd.ints if prescripcion_acd else [],
            },
        )
    except Exception:
        pass

    # === RETURN ===
    resultado = {
        "diagnostico_id": diag_id,
        "estado": estado.id,
        "nombre": estado.nombre,
        "tipo": estado.tipo,
        "lentes": lentes,
        "scores_21": scores_raw,
        "vector_f": vector.to_dict(),
        "gap": estado.gap,
        "flags": [f.nombre for f in estado.flags],
        "cambio_vs_anterior": cambio,
        "metricas_raw": metricas,
        "repertorio": {
            "ints_activas": repertorio.ints_activas,
            "ints_atrofiadas": repertorio.ints_atrofiadas,
            "ints_ausentes": repertorio.ints_ausentes,
            "ps_activos": repertorio.ps_activos,
            "rs_activos": repertorio.rs_activos,
            "advertencias_ic": repertorio.advertencias_ic,
        } if repertorio else None,
        "prescripcion": {
            "ints": prescripcion_acd.ints,
            "ps": prescripcion_acd.ps,
            "rs": prescripcion_acd.rs,
            "secuencia": prescripcion_acd.secuencia,
            "frenar": prescripcion_acd.frenar,
            "lente_objetivo": prescripcion_acd.lente_objetivo,
            "objetivo": prescripcion_acd.objetivo,
            "advertencias_ic": prescripcion_acd.advertencias_ic,
        } if prescripcion_acd else None,
    }

    log.info("diagnosticador_completo",
             estado=estado.id, cambio=cambio,
             flags=len(estado.flags),
             repertorio=bool(repertorio),
             prescripcion=bool(prescripcion_acd))
    return resultado


def _fallback_heuristico(metricas: dict) -> tuple:
    """Fallback si el LLM del evaluador funcional falla.

    Usa fórmulas simples (PEOR que LLM pero mejor que nada).
    SOLO se usa si evaluar_funcional() lanza excepción.
    """
    from src.tcf.campo import VectorFuncional

    tasa_ret = max(0, min(1, 1.0 - (metricas["bajas_periodo"] / max(metricas["total_activos"], 1))))
    eficiencia = max(0, min(1, 1.0 - (metricas["sesiones_bajas"] / max(metricas["sesiones_grupo"], 1))))
    asist_media = metricas["total_asistencias"] / max(metricas["sesiones_grupo"], 1)

    grados = {
        "F1": round(tasa_ret, 3),
        "F2": round(min(1, metricas["nuevos_clientes"] / max(metricas["total_activos"] * 0.1, 1)), 3),
        "F3": round(eficiencia, 3),
        "F4": round(min(1, asist_media / 6.0), 3),
        "F5": round(min(1, metricas["senales_voz"] / 20.0), 3),
        "F6": round(min(1, metricas["tensiones"] / 5.0), 3),
        "F7": round(min(1, metricas["procesos"] / 10.0), 3),
    }

    vector = VectorFuncional.from_dict(grados)
    lentes_heur = {
        "salud": round((grados["F1"] * 0.4 + grados["F3"] * 0.3 + grados["F4"] * 0.3), 3),
        "sentido": round((grados["F2"] * 0.3 + grados["F5"] * 0.4 + grados["F6"] * 0.3), 3),
        "continuidad": round((grados["F7"] * 0.5 + min(1, metricas["cobrado"] / max(metricas["cobrado"] + metricas["pendiente"], 1)) * 0.5), 3),
    }

    # Construir scores_raw aproximados para compatibilidad
    scores_raw = {}
    for fi, g in grados.items():
        scores_raw[fi] = {"salud": g, "sentido": round(g * 0.7, 3), "continuidad": round(g * 0.5, 3)}

    return scores_raw, vector, lentes_heur
```

**IMPORTANTE:** Las funciones `_metricas_a_lentes()` y `_metricas_a_vector_f()` actuales se ELIMINAN. Se conservan SOLO como fallback en `_fallback_heuristico()` que se usa si el LLM falla.

### ARCHIVO 2: `src/pilates/enjambre.py` — REESCRIBIR como contextualizador

(Sin cambios respecto a la versión anterior del briefing — el enjambre recibe el DiagnosticoCompleto + Prescripcion del diagnosticador y lo contextualiza con los 6 clusters.)

Los 6 clusters reciben como input:
1. El diagnóstico de código (scores_21, estado, repertorio, prescripción)
2. Los datos reales del negocio (clientes, grupos, señales, identidad)
3. La pizarra del organismo (qué escribieron los demás agentes)

Y su trabajo es CONFIRMAR/CONTRADECIR/ENRIQUECER, no reinventar.

```python
async def ejecutar_enjambre(diagnostico_completo=None, prescripcion_acd=None) -> dict:
    """Ejecuta enjambre como CONTEXTUALIZADOR sobre diagnóstico de tcf/.

    Los clusters NO reinventan el diagnóstico. Lo EVALÚAN contra la realidad.
    """
    # ... (código del enjambre v3 sin cambios) ...

    # NOVEDAD: leer la pizarra para que los clusters sepan qué hicieron los AF
    from src.pilates.pizarra import leer_todo
    pizarra = await leer_todo()
    pizarra_str = json.dumps(pizarra, ensure_ascii=False, indent=2, default=str)[:2000]

    # Inyectar pizarra en el contexto de cada cluster
    contexto_enriquecido = (
        f"DIAGNÓSTICO DE CÓDIGO:\n{diagnostico_resumen}\n\n"
        f"DATOS REALES DEL NEGOCIO:\n{ctx_str}\n\n"
        f"PIZARRA — Lo que cada agente está haciendo/pensando:\n{pizarra_str}"
    )
```

## EL FLUJO COMPLETO DESPUÉS DE ESTE CAMBIO

```
1. _recopilar_metricas()          → datos crudos (código puro, $0)
2. evaluar_funcional(texto_caso)  → 21 scores F×L (LLM percibe, ~$0.005)
3. evaluar_campo(vector)          → lentes, toxicidad, atractor (código puro, $0)
4. clasificar_estado(lentes)      → 1 de 10 estados + flags (código puro, $0)
5. inferir_repertorio(texto, vec) → INT×P×R + IC2-IC6 (LLM + código, ~$0.003)
6. prescribir(diagnostico)        → INTs, Ps, Rs, secuencia, frenar (código puro, $0)
7. EMITIR al bus + ESCRIBIR pizarra
8. ejecutar_enjambre()            → 13 clusters EVALÚAN contra realidad (LLM, ~$0.65)
9. evaluar_sesgos()               → Guardián verifica (LLM, ~$0.05)
10. compositor()                  → Integra código + clusters + guardián (LLM, ~$0.05)
11. estratega()                   → Contextualiza prescripción (LLM, ~$0.05)
12. orquestador()                 → Valida coherencia (LLM, ~$0.02)
13. recompilar()                  → Traduce a configs de agentes (LLM, ~$0.05)
14. detectar_huerfanas()          → Preguntas que nadie hizo (LLM, ~$0.05)
15. evaluar_semillas()            → Dormidas que ahora son relevantes (código, $0)
```

**Pasos 1-6:** tcf/ (álgebra + 2 LLM baratas) = ~$0.008
**Pasos 8-14:** Enjambre + Compositor + extras (LLM contextualización) = ~$0.92
**Total por ejecución:** ~$0.93

## COSTE vs CALIDAD

| Aspecto | Antes (heurística + enjambre paralelo) | Después (LLM percibe + código razona) |
|---|---|---|
| 21 scores F×L | Fórmulas inventadas (pesos 0.4/0.3/0.3) | LLM ve "15 grupos infrautilizados" = F3.Se MUY baja |
| Repertorio INT×P×R | Reinventado por 3 agentes LLM | tcf/ con IC2-IC6 deterministas |
| Prescripción | Reinventada por Estratega LLM | tcf/ código puro + contextualización LLM |
| Verificaciones IC | Dependen del prompt | Código — NUNCA fallan |
| Coste P1-P6 | $0 (heurística) + $0.45 (3 agentes) = $0.45 | $0.008 (2 LLM baratas) |
| Calidad | Scores imprecisos + IC no garantizadas | Scores precisos + IC deterministas |

## TESTS

### T1: Evaluador funcional produce 21 scores desde datos reales
```python
result = await diagnosticar_tenant()
assert "scores_21" in result
assert len(result["scores_21"]) == 7  # F1-F7
for fi, scores in result["scores_21"].items():
    assert "salud" in scores
    assert "sentido" in scores
    assert "continuidad" in scores
    assert 0.0 <= scores["salud"] <= 1.0
```

### T2: El LLM percibe matices que la heurística no
```python
# Con 15/16 grupos infrautilizados, F3.Se debe ser < 0.30
assert result["scores_21"]["F3"]["sentido"] < 0.35
# Con 0 procesos documentados, F7.continuidad debe ser < 0.20
assert result["scores_21"]["F7"]["continuidad"] < 0.25
```

### T3: Repertorio viene de tcf/ con IC verificadas
```python
assert result.get("repertorio") is not None
assert len(result["repertorio"]["ints_activas"]) >= 3
# Las advertencias IC son deterministas
assert isinstance(result["repertorio"]["advertencias_ic"], list)
```

### T4: Prescripción viene de código ($0)
```python
assert result.get("prescripcion") is not None
assert len(result["prescripcion"]["ints"]) >= 3
assert result["prescripcion"]["objetivo"] != ""
```

### T5: Fallback funciona si LLM falla
```python
# Simular fallo del evaluador funcional
# El diagnosticador debe devolver resultado con fallback=True
```

### T6: Señal DIAGNOSTICO en bus incluye scores_21 + repertorio + prescripción
```sql
SELECT
    payload->>'scores_21' IS NOT NULL as tiene_scores,
    payload->>'repertorio' IS NOT NULL as tiene_rep,
    payload->>'prescripcion' IS NOT NULL as tiene_presc
FROM om_senales_agentes
WHERE tipo='DIAGNOSTICO' AND origen='DIAGNOSTICADOR'
ORDER BY created_at DESC LIMIT 1;
-- Debe ser TRUE, TRUE, TRUE
```

### T7: Pizarra escrita por diagnosticador
```sql
SELECT agente, detectando, interpretacion FROM om_pizarra
WHERE agente='DIAGNOSTICADOR'
ORDER BY updated_at DESC LIMIT 1;
-- Debe tener estado + lentes + prescripción
```
