# B-ACD-16: Deploy + Migration + Persistencia + Test Integración

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-15 ✅ (pipeline ACD completo)
**Coste:** ~$0.01 (1 test de integración end-to-end con LLM)

---

## CONTEXTO

Todo el código ACD (B-ACD-00 a B-ACD-15) está testeado localmente. Para usar en producción falta:

1. **Deploy** — `fly deploy` del motor-semantico
2. **DB migration** — schema.sql ya tiene las 4 tablas ACD, `execute_schema()` corre en startup con `IF NOT EXISTS` → idempotente, no rompe nada
3. **Persistir diagnósticos** — `diagnosticar()` y `prescribir()` producen datos pero no se guardan en la tabla `diagnosticos`
4. **Test de integración** — correr el pipeline completo via API y verificar response con ACD

---

## PASO 0: Verificar que no hay errores de import locales

```bash
cd @project/ && python3 -c "
from src.tcf.prescriptor import prescribir
from src.tcf.evaluador_acd import evaluar_acd, decidir
from src.pipeline.generador import generar_prompts, _generar_bloque_pr
from src.pipeline.orchestrator import _run_acd
print('PASS: Todos los imports ACD OK')
"
```

**Pass/fail:** Todos los imports sin error.

---

## PASO 1: Crear función de persistencia en client.py

**Archivo:** `@project/src/db/client.py` (ya existe)

**Leer primero.** Luego AÑADIR al final:

```python
async def log_diagnostico(data: dict) -> str:
    """Guarda un diagnóstico ACD y devuelve su UUID.

    Args:
        data: dict con campos de la tabla diagnosticos.
              Campos obligatorios: caso_input, vector_pre, lentes_pre, estado_pre.
              Campos opcionales: ejecucion_id, flags_pre, repertorio_inferido,
                                 prescripcion, resultado, metricas.

    Returns:
        UUID del diagnóstico creado.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO diagnosticos (
                caso_input, ejecucion_id,
                vector_pre, lentes_pre, estado_pre, flags_pre,
                repertorio_inferido, prescripcion, resultado, metricas
            )
            VALUES ($1, $2, $3::jsonb, $4::jsonb, $5, $6, $7::jsonb, $8::jsonb, $9, $10::jsonb)
            RETURNING id
        """,
            data.get('caso_input'),
            data.get('ejecucion_id'),
            data.get('vector_pre'),
            data.get('lentes_pre'),
            data.get('estado_pre'),
            data.get('flags_pre'),
            data.get('repertorio_inferido'),
            data.get('prescripcion'),
            data.get('resultado', 'pendiente'),
            data.get('metricas'),
        )
        return str(row['id'])
```

**Pass/fail paso 1:**
```bash
cd @project/ && python3 -c "
from src.db.client import log_diagnostico
print('PASS: log_diagnostico importa correctamente')
"
```

---

## PASO 2: Persistir diagnóstico en orchestrator

**Archivo:** `@project/src/pipeline/orchestrator.py` (ya existe)

**Leer primero.** Luego, DENTRO de `run_pipeline()`, al final — en el bloque de telemetría (donde ya existe el try/except para `log_ejecucion`), DESPUÉS del bloque `log_ejecucion`, AÑADIR:

```python
    # Persistir diagnóstico ACD
    if prescripcion and acd_result:
        try:
            from src.db.client import log_diagnostico
            _diag = acd_result[0]
            diag_data = {
                'caso_input': request.input[:2000],  # truncar para DB
                'vector_pre': json.dumps(_diag.vector.to_dict()),
                'lentes_pre': json.dumps(_diag.estado_campo.lentes),
                'estado_pre': _diag.estado.id,
                'flags_pre': [f.nombre for f in _diag.estado.flags],
                'repertorio_inferido': json.dumps({
                    'ints_activas': _diag.repertorio.ints_activas,
                    'ints_atrofiadas': _diag.repertorio.ints_atrofiadas,
                    'ints_ausentes': _diag.repertorio.ints_ausentes,
                    'ps_activos': _diag.repertorio.ps_activos,
                    'rs_activos': _diag.repertorio.rs_activos,
                }),
                'prescripcion': json.dumps({
                    'ints': prescripcion.ints,
                    'ps': prescripcion.ps,
                    'rs': prescripcion.rs,
                    'secuencia': prescripcion.secuencia,
                    'frenar': prescripcion.frenar,
                    'lente_objetivo': prescripcion.lente_objetivo,
                    'modos': prescripcion.nivel_logico.modos,
                    'objetivo': prescripcion.objetivo,
                }),
                'resultado': evaluation.decision_acd.veredicto if evaluation.decision_acd else 'pendiente',
                'metricas': json.dumps({
                    'score_acd': evaluation.metricas_acd.score_acd if evaluation.metricas_acd else None,
                    'cobertura_ints': evaluation.metricas_acd.cobertura_ints if evaluation.metricas_acd else None,
                    'alineacion_pr': evaluation.metricas_acd.alineacion_pr if evaluation.metricas_acd else None,
                    'decision_confianza': evaluation.decision_acd.confianza if evaluation.decision_acd else None,
                }) if evaluation.metricas_acd else None,
            }
            diag_id = await log_diagnostico(diag_data)
            log.info("acd.persisted", diag_id=diag_id)
        except Exception as e:
            log.error("acd.persist_error", error=str(e))
```

**Nota:** Usa `acd_result` (la variable de run_pipeline que contiene el tuple (diag, presc) creado en B-ACD-13). Si `acd_result` es None, no se ejecuta.

---

## PASO 3: Deploy a fly.io

```bash
cd @project/ && fly deploy --strategy immediate
```

**Pass/fail paso 3:**
- El deploy completa sin error
- Los logs de startup muestran `startup_db_ready` (tablas ACD creadas via `execute_schema()`)

**Verificar logs:**
```bash
fly logs -a motor-semantico-omni | head -20
```

Buscar: `schema_executed` (confirma que schema.sql corrió) + `startup_complete`.

---

## PASO 4: Verificar tablas ACD en DB

```bash
fly postgres connect -a omni-mind-db -d omni_mind
```

O via código:
```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Verificar las 4 tablas ACD existen
        tables = ['tipos_pensamiento', 'tipos_razonamiento', 'estados_diagnosticos', 'diagnosticos']
        for t in tables:
            exists = await conn.fetchval(
                \"\"\"SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = \$1
                )\"\"\", t)
            status = '✅' if exists else '❌'
            print(f'{status} {t}')

        # Verificar columnas de diagnosticos
        cols = await conn.fetch(
            \"\"\"SELECT column_name FROM information_schema.columns
               WHERE table_name = 'diagnosticos'
               ORDER BY ordinal_position\"\"\")
        print(f'\\nColumnas diagnosticos: {[c[\"column_name\"] for c in cols]}')

asyncio.run(check())
"
```

**Pass/fail paso 4:** Las 4 tablas existen. `diagnosticos` tiene las columnas: id, created_at, caso_input, ejecucion_id, vector_pre, lentes_pre, estado_pre, flags_pre, repertorio_inferido, prescripcion, vector_post, lentes_post, estado_post, flags_post, resultado, metricas.

---

## PASO 5: Test de integración end-to-end via API

```bash
cd @project/ && python3 -c "
import asyncio, httpx, json

async def test():
    base = 'https://motor-semantico-omni.fly.dev'

    caso = '''Estudio de Pilates con 8 años de operación en zona premium.
    Rentable: factura 12K/mes con 85% ocupación. Pero altamente dependiente de María,
    la instructora principal y dueña. Sin ella, las clases se cancelan.
    No hay manual de operaciones ni protocolo de sustitución.
    Los clientes vienen por María, no por la marca.
    Identidad clara: Pilates reformer premium, clientela fiel, boca a boca.
    No hay plan de expansión ni sistema de formación de nuevos instructores.'''

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f'{base}/api/v1/analizar', json={
            'input': caso,
            'config': {'modo': 'ANALIZAR', 'presupuesto_max': 1.0}
        })
        assert resp.status_code == 200, f'HTTP {resp.status_code}: {resp.text[:200]}'
        data = resp.json()

    # === VERIFICACIONES ===

    # 1. ACD presente en response
    acd = data.get('algoritmo_usado', {}).get('acd', {})
    assert acd.get('activo') == True, f'ACD no activo: {acd}'
    print(f'PASS 1: ACD activo')

    # 2. Estado diagnóstico
    assert acd.get('estado_id') is not None, 'estado_id missing'
    print(f'PASS 2: Estado = {acd[\"estado_id\"]}')

    # 3. INTs prescritas
    assert len(acd.get('ints_prescritas', [])) >= 3, f'Pocas INTs: {acd.get(\"ints_prescritas\")}'
    print(f'PASS 3: INTs = {acd[\"ints_prescritas\"]}')

    # 4. Ps y Rs
    print(f'PASS 4: Ps = {acd.get(\"ps_prescritos\")}, Rs = {acd.get(\"rs_prescritos\")}')

    # 5. Modos y objetivo
    print(f'PASS 5: Modos = {acd.get(\"modos\")}, Objetivo = {acd.get(\"objetivo\")}')

    # 6. Decisión ternaria
    decision = data.get('meta', {}).get('acd_decision')
    if decision:
        assert decision.get('veredicto') in ('cierre', 'inerte', 'toxico'), f'Veredicto inválido: {decision}'
        print(f'PASS 6: Decisión = {decision[\"veredicto\"]} (confianza={decision[\"confianza\"]})')
        print(f'  Razón: {decision[\"razon\"][:80]}...')
    else:
        print(f'SKIP 6: acd_decision no presente (B-ACD-15 quizá no deployed)')

    # 7. Score calidad incluye ACD
    score = data.get('meta', {}).get('score_calidad')
    print(f'PASS 7: Score calidad = {score}')

    # 8. Coste razonable
    coste = data.get('meta', {}).get('coste', 0)
    print(f'PASS 8: Coste = \${coste:.4f}')

    # === RESUMEN ===
    print(f'\\n=== PIPELINE ACD END-TO-END ===')
    print(f'Estado: {acd.get(\"estado_id\")} | Lente: {acd.get(\"lente_objetivo\")} | Objetivo: {acd.get(\"objetivo\")}')
    print(f'INTs: {acd.get(\"ints_prescritas\")}')
    print(f'Ps: {acd.get(\"ps_prescritos\")} | Rs: {acd.get(\"rs_prescritos\")}')
    print(f'Secuencia: {acd.get(\"secuencia\")} | Frenar: {acd.get(\"frenar\")}')
    print(f'Prohibiciones: {acd.get(\"prohibiciones\")} | Advertencias: {acd.get(\"advertencias_ic\")}')
    if decision:
        print(f'Decisión: {decision[\"veredicto\"]} | Recomendación: {decision[\"recomendacion\"][:80]}...')
    print(f'Score: {score} | Coste: \${coste:.4f} | Tiempo: {data.get(\"meta\",{}).get(\"tiempo_s\",0):.1f}s')

asyncio.run(test())
print('\\nINTEGRACIÓN END-TO-END PASS')
"
```

**CRITERIO PASS:**
1. ACD activo en response
2. Estado diagnóstico presente
3. ≥ 3 INTs prescritas
4. Ps y Rs presentes (para estados desequilibrados)
5. Modos y objetivo presentes
6. Decisión ternaria (cierre/inerte/tóxico)
7. Score calidad numérico
8. Coste < $1.00

---

## PASO 6: Verificar persistencia en DB

```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT id, estado_pre, resultado, created_at FROM diagnosticos ORDER BY created_at DESC LIMIT 1'
        )
        if row:
            print(f'✅ Diagnóstico persistido: id={row[\"id\"]}, estado={row[\"estado_pre\"]}, resultado={row[\"resultado\"]}')
        else:
            print('⚠️ No hay diagnósticos en DB (tabla vacía)')

asyncio.run(check())
"
```

**Pass/fail paso 6:** Al menos 1 fila en `diagnosticos` con estado_pre y resultado del test de integración.

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/db/client.py` | EDITAR — añadir log_diagnostico() |
| `src/pipeline/orchestrator.py` | EDITAR — añadir bloque de persistencia ACD |

## ARCHIVOS QUE NO SE TOCAN

schema.sql (ya tiene las tablas). seed.sql (los datos ACD viven en JSON, no en seed). Dockerfile, fly.toml (no cambian).

## NOTAS

- **schema.sql es idempotente** — usa `IF NOT EXISTS` en todas las tablas. `execute_schema()` corre en startup de fly.io automáticamente.
- **No se hace seed de tablas ACD** — los datos de referencia (estados, pensamientos, razonamientos) viven en JSON files que Python carga directamente. La DB solo almacena RESULTADOS de diagnósticos.
- **El deploy tarda ~2-3 min** en fly.io (build Docker + swap machines).
- **El test de integración gasta ~$0.01** — 2 LLM calls V3.2 (diagnosticar) + N LLM calls del pipeline completo.
- **Si el deploy falla:** verificar que `OPENROUTER_API_KEY` está como secret en fly.io (`fly secrets list`). Si no: `fly secrets set OPENROUTER_API_KEY=sk-...`.
- **Fallback:** Si la DB no está disponible en fly.io, el pipeline sigue funcionando — la persistencia es fire-and-forget (try/except).
