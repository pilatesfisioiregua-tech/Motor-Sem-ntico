# B-ACD-13: Integrar prescripción en orchestrator

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-12 ✅ (generador acepta ps/rs), Fase 2 completa, B-ACD-09 ✅
**Coste:** ~$0.005/caso (2 LLM calls de Fase 2 diagnosticar(), el resto es $0)

---

## CONTEXTO

El orchestrator actual tiene este pipeline:
```
Detector → Router → Compositor → Generador → Ejecutor → Evaluador → Integrador
```

Con ACD el pipeline se extiende:
```
Detector → [ACD: diagnosticar() → prescribir()] → Router → Compositor → Generador(+P/R) → Ejecutor → Evaluador → Integrador
```

El ACD no reemplaza el pipeline — lo ENRIQUECE:
- diagnosticar() produce DiagnosticoCompleto (vector, estado, repertorio)
- prescribir() produce Prescripcion (INTs, Ps, Rs, secuencia, modos, objetivo)
- La prescripción INFORMA al Router (qué INTs activar) y al Generador (qué Ps/Rs inyectar)
- El Router sigue funcionando para casos sin ACD (backward compatible)

---

## PASO 1: Crear función acd_pipeline en orchestrator

**Archivo:** `@project/src/pipeline/orchestrator.py` (ya existe)

**Leer primero.** Luego AÑADIR imports al inicio:

```python
from src.tcf.prescriptor import prescribir, Prescripcion
```

Y AÑADIR función antes de `run_pipeline`:

```python
async def _run_acd(input_text: str) -> tuple[object, Prescripcion] | None:
    """Ejecuta pipeline ACD: texto → diagnóstico → prescripción.

    Returns:
        Tupla (DiagnosticoCompleto, Prescripcion) o None si falla.
        Coste: ~$0.005 (2 LLM calls V3.2).
    """
    try:
        from src.tcf.diagnostico import diagnosticar
        diag = await diagnosticar(input_text)
        presc = prescribir(diag)
        log.info(
            "acd.ok",
            estado=diag.estado.id,
            lente_objetivo=presc.lente_objetivo,
            n_ints=len(presc.ints),
            n_ps=len(presc.ps),
            n_rs=len(presc.rs),
            objetivo=presc.objetivo,
            prohibiciones=[p.codigo for p in presc.prohibiciones_violadas],
        )
        return diag, presc
    except Exception as e:
        log.warning("acd.fail", error=str(e))
        return None
```

---

## PASO 2: Integrar ACD en run_pipeline

**Mismo archivo.** En `run_pipeline`, DESPUÉS de la detección TCF (capa 0) y ANTES del Router (capa 1), insertar:

```python
    # ACD: Diagnóstico + Prescripción (si hay texto suficiente)
    acd_result = None
    prescripcion: Prescripcion | None = None
    if len(request.input) >= 50:  # Solo ACD para textos con sustancia
        acd_result = await _run_acd(request.input)
        if acd_result:
            _diag, prescripcion = acd_result
            log.info("pipeline_acd_done",
                     estado=_diag.estado.id,
                     objetivo=prescripcion.objetivo)
```

---

## PASO 3: Pasar INTs de prescripción al Router

**Mismo archivo.** Modificar la llamada a `route()` para incluir INTs prescritas:

**ANTES:**
```python
    router_result = await route(
        input_text=request.input,
        contexto=request.contexto,
        modo=config.modo,
        forzadas=config.inteligencias_forzadas,
        excluidas=config.inteligencias_excluidas,
        huecos=huecos,
        tcf=huecos.tcf,
        programa=programa,
    )
```

**DESPUÉS:**
```python
    # INTs prescripción ACD se suman a las forzadas
    forzadas = list(config.inteligencias_forzadas or [])
    if prescripcion:
        for int_id in prescripcion.ints:
            if int_id not in forzadas:
                forzadas.append(int_id)

    router_result = await route(
        input_text=request.input,
        contexto=request.contexto,
        modo=config.modo,
        forzadas=forzadas if forzadas else config.inteligencias_forzadas,
        excluidas=config.inteligencias_excluidas,
        huecos=huecos,
        tcf=huecos.tcf,
        programa=programa,
    )
```

---

## PASO 4: Pasar Ps/Rs al Generador

**Mismo archivo.** Modificar la llamada a `generar_prompts()`:

**ANTES:**
```python
    prompts = generar_prompts(algoritmo, request.input, request.contexto, inteligencias_data)
```

**DESPUÉS:**
```python
    prompts = generar_prompts(
        algoritmo, request.input, request.contexto, inteligencias_data,
        ps=prescripcion.ps if prescripcion else None,
        rs=prescripcion.rs if prescripcion else None,
    )
```

---

## PASO 5: Incluir ACD en respuesta

**Mismo archivo.** En el dict `response`, añadir sección ACD dentro de `algoritmo_usado`:

**Después de la sección `"gestor":`**, añadir:

```python
            "acd": {
                "activo": prescripcion is not None,
                "estado_id": prescripcion.estado_id if prescripcion else None,
                "lente_objetivo": prescripcion.lente_objetivo if prescripcion else None,
                "objetivo": prescripcion.objetivo if prescripcion else None,
                "ints_prescritas": prescripcion.ints if prescripcion else [],
                "ps_prescritos": prescripcion.ps if prescripcion else [],
                "rs_prescritos": prescripcion.rs if prescripcion else [],
                "secuencia": prescripcion.secuencia if prescripcion else [],
                "frenar": prescripcion.frenar if prescripcion else [],
                "modos": prescripcion.nivel_logico.modos if prescripcion else [],
                "prohibiciones": [p.codigo for p in prescripcion.prohibiciones_violadas] if prescripcion else [],
                "advertencias_ic": prescripcion.advertencias_ic if prescripcion else [],
            },
```

---

## PASO 6: Tests de validación

**Pass/fail:**

```bash
cd @project/ && python3 -c "
import asyncio
from src.pipeline.orchestrator import _run_acd

# Test 1: ACD con caso Pilates (LLM real)
async def test():
    caso = '''Estudio de Pilates con 8 años. Rentable pero dependiente de María.
    Sin ella las clases se cancelan. No hay manual. Los clientes vienen por ella.
    Identidad clara: reformer premium. Sin plan de expansión ni formación.'''

    result = await _run_acd(caso)
    assert result is not None, 'ACD debería funcionar'

    diag, presc = result

    # DiagnosticoCompleto
    assert diag.estado.id is not None
    assert diag.vector is not None
    print(f'PASS 1: Diagnóstico OK — estado={diag.estado.id}')

    # Prescripcion
    assert len(presc.ints) >= 3, f'Pocas INTs: {presc.ints}'
    assert presc.lente_objetivo is not None
    assert presc.nivel_logico is not None
    print(f'PASS 2: Prescripción OK — INTs={presc.ints}, lente={presc.lente_objetivo}')
    print(f'  Ps={presc.ps}, Rs={presc.rs}')
    print(f'  Objetivo={presc.objetivo}')
    print(f'  Modos={presc.nivel_logico.modos}')

asyncio.run(test())
print('\\nTODOS LOS TESTS PASAN')
"
```

**CRITERIO PASS:**
1. _run_acd devuelve DiagnosticoCompleto + Prescripcion
2. Prescripción tiene INTs, Ps, Rs, lente, objetivo, modos

**Test de integración completo (opcional, requiere API keys para pipeline completo):**
```bash
cd @project/ && python3 -c "
# Solo si motor-semantico API está corriendo
import httpx, asyncio

async def test_integration():
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post('http://localhost:8080/api/v1/analizar', json={
            'input': 'Estudio de Pilates con 8 años. Dependiente de María.',
            'config': {'modo': 'ANALIZAR', 'presupuesto_max': 1.0}
        })
        data = resp.json()
        acd = data.get('algoritmo_usado', {}).get('acd', {})
        if acd.get('activo'):
            print(f'ACD activo: estado={acd[\"estado_id\"]}, INTs={acd[\"ints_prescritas\"]}')
            print(f'Ps={acd[\"ps_prescritos\"]}, Rs={acd[\"rs_prescritos\"]}')
        else:
            print('ACD no activo (verificar)')

asyncio.run(test_integration())
"
```

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/pipeline/orchestrator.py` | EDITAR — añadir import, _run_acd(), integrar en run_pipeline |

## ARCHIVOS QUE NO SE TOCAN

router.py (las INTs se pasan como `forzadas`, interfaz existente).
generador.py (ya acepta ps/rs desde B-ACD-12).
ejecutor.py, evaluador.py (se tocan en Fase 5).

## NOTAS

- **Backward compatible:** Sin ACD (texto < 50 chars, o ACD falla), pipeline funciona exactamente igual
- **Costo:** ~$0.005 extra por caso (2 LLM calls V3.2 de diagnosticar())
- **INTs ACD como forzadas:** Se suman a las forzadas del config. El Router las incluye siempre, puede añadir más si detecta huecos adicionales.
- **Prescripcion en response:** Se incluye completa en `algoritmo_usado.acd` para telemetría y debugging
- **No se tocan:** las capas 5-6 (evaluador/integrador) — eso es Fase 5 (B-ACD-14/15)
- **Mínimo 50 chars:** Textos muy cortos (saludos, preguntas simples) no justifican ACD ($0.005 innecesario)
