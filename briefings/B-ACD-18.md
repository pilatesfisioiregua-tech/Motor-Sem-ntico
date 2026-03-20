# B-ACD-18: Auditoría Funcional de Motores

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-16 ✅ (pipeline en producción)
**Coste:** ~$0.02 (smoke tests con LLM)

---

## CONTEXTO

El sistema OMNI-MIND tiene 5 motores según el Maestro V4:

1. **Motor vN** — pipeline 7 capas + ACD (mira hacia fuera)
2. **Gestor de la Matriz** — compila programas, mantiene la Matriz (mira hacia dentro)
3. **Reactor** — genera datos para llenar la Matriz
4. **Models (C1-C4)** — modelos ligeros entrenados desde Reactor
5. **Code OS** — agente autónomo de código

Esta auditoría verifica QUÉ FUNCIONA vs QUÉ ES STUB vs QUÉ NO EXISTE, para decidir prioridades post-ACD.

---

## PASO 0: Inventario de endpoints

```bash
cd @project/ && python3 -c "
from src.main import app
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f'{list(route.methods)} {route.path}')
"
```

**Pass/fail:** Lista todos los endpoints disponibles.

---

## PASO 1: Motor vN — Smoke test pipeline completo

```bash
cd @project/ && python3 -c "
import asyncio, time, json

async def test():
    from src.main import MotorRequest, MotorConfig
    from src.pipeline.orchestrator import run_pipeline

    caso = '''Estudio de Pilates con 8 años. Factura 12K/mes, 85% ocupación.
    Dependiente de María (dueña+instructora principal).
    Sin manual de operaciones ni sustitución. Clientes vienen por ella, no por la marca.'''

    req = MotorRequest(input=caso, config=MotorConfig(modo='analisis', presupuesto_max=1.0))

    t0 = time.time()
    result = await run_pipeline(req)
    dt = time.time() - t0

    # Verificar las 7 capas ejecutadas
    algo = result['algoritmo_usado']
    meta = result['meta']

    checks = {
        'huecos_detectados': algo.get('huecos') is not None,
        'inteligencias_seleccionadas': len(algo.get('inteligencias', [])) > 0,
        'programa_compilado': algo.get('programa') is not None,
        'prompts_generados': algo.get('n_prompts', 0) > 0,
        'ejecucion_completada': result.get('resultado') is not None,
        'evaluacion_presente': meta.get('score_calidad') is not None,
        'acd_activo': algo.get('acd', {}).get('activo', False),
        'decision_ternaria': meta.get('acd_decision') is not None,
    }

    for name, ok in checks.items():
        status = 'PASS' if ok else 'FAIL'
        print(f'{status}: {name}')

    print(f'\nTiempo: {dt:.1f}s | Coste: \${meta.get(\"coste\", 0):.4f}')
    print(f'INTs: {algo.get(\"inteligencias\", [])}')
    print(f'Score: {meta.get(\"score_calidad\")}')

    if meta.get('acd_decision'):
        d = meta['acd_decision']
        print(f'ACD: {d.get(\"veredicto\")} (confianza={d.get(\"confianza\")})')

    return all(checks.values())

ok = asyncio.run(test())
print(f'\nMOTOR vN: {\"PASS\" if ok else \"FAIL\"}')
"
```

**Pass/fail:** 8/8 checks pasan. Motor vN funcional end-to-end.

---

## PASO 2: Gestor — Verificar compilación de programas

```bash
cd @project/ && python3 -c "
from src.tcf.arquetipos import ScoringMultiArquetipo, ScoreArquetipo
from src.tcf.campo import VectorFuncional
from src.gestor.compilador import compilar_programa

# Caso de prueba: rigidez_conservadora (arquetipo frecuente)
scoring = ScoringMultiArquetipo(
    scores=[
        ScoreArquetipo(arquetipo_id='rigidez_conservadora', score=0.8, mecanismo='test'),
        ScoreArquetipo(arquetipo_id='captura_sin_norte', score=0.3, mecanismo='test'),
    ],
    arquetipos_activos=['rigidez_conservadora'],
    perfil_mixto='rigidez_conservadora dominante',
)

vector = VectorFuncional(F1=0.8, F2=0.5, F3=0.3, F4=0.4, F5=0.6, F6=0.2, F7=0.1)

programa = compilar_programa(scoring, vector, modo='analisis', presupuesto_max=1.0)

checks = {
    'programa_compilado': programa is not None,
    'tiene_pasos': len(programa.pasos) > 0,
    'tiene_tier': programa.tier is not None,
    'tiene_modelo': all(p.modelo for p in programa.pasos),
    'tiene_secuencia_funciones': programa.secuencia_funciones is not None,
}

for name, ok in checks.items():
    status = 'PASS' if ok else 'FAIL'
    print(f'{status}: {name}')

print(f'\nTier: {programa.tier}')
print(f'Pasos: {len(programa.pasos)}')
print(f'Secuencia: {programa.secuencia_funciones}')
print(f'Modelos: {set(p.modelo for p in programa.pasos)}')

print(f'\nGESTOR COMPILADOR: {\"PASS\" if all(checks.values()) else \"FAIL\"}')
"
```

**Pass/fail:** Programa compilado con pasos, tier, y modelos asignados.

---

## PASO 3: Gestor — Verificar si existe loop lento

```bash
cd @project/ && python3 -c "
import os
gestor_dir = '@project/src/gestor/'
files = os.listdir(gestor_dir.replace('@project/', ''))
print(f'Archivos en src/gestor/: {files}')

# Buscar funciones de análisis de patrones / poda / recompilación
import ast
for f in files:
    if f.endswith('.py'):
        path = f'src/gestor/{f}'
        with open(path) as fh:
            tree = ast.parse(fh.read())
        funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        print(f'{f}: {funcs}')

# Buscar endpoint /gestor/
from src.main import app
gestor_endpoints = [r.path for r in app.routes if hasattr(r, 'path') and 'gestor' in r.path]
print(f'\nEndpoints /gestor/*: {gestor_endpoints if gestor_endpoints else \"NINGUNO\"}')
"
```

**Resultado esperado:** No hay endpoint `/gestor/`, no hay función de análisis periódico ni poda. El Gestor solo compila bajo demanda. **Loop lento = NO EXISTE.**

---

## PASO 4: Reactor v1 — Smoke test

```bash
cd @project/ && python3 -c "
import asyncio

async def test():
    # Verificar que el runner importa sin errores
    from src.reactor.runner import run
    from src.reactor.config import DOMINIOS, TOP_PARES

    print(f'Dominios: {len(DOMINIOS)}')
    print(f'Pares: {len(TOP_PARES)}')

    # Verificar sub-pipelines importan
    from src.reactor.b1_casos_dominio import generar_casos
    from src.reactor.b2_peticiones import generar_peticiones
    from src.reactor.b3_composicion import generar_composiciones
    from src.reactor.b4_scoring import generar_scoring
    from src.reactor.validador import validar
    print('Imports reactor: PASS')

    # NO ejecutar run() aquí — cuesta dinero y genera datos sintéticos
    print('Ejecución: SKIP (costaría dinero, se valida por import)')

asyncio.run(test())
print('\nREACTOR v1: PASS (imports OK, ejecución skip)')
"
```

**Pass/fail:** Todos los imports OK. El Reactor v1 existe y es funcional pero genera datos sintéticos simples (no es v5).

---

## PASO 5: Verificar existencia de Reactor v5/v5.2

```bash
cd @project/ && python3 -c "
import os
from pathlib import Path

# Buscar código del reactor v5
reactor_code = list(Path('src/reactor').glob('*v5*'))
reactor_results = list(Path('results/reactor_v5').glob('*'))

print(f'Código reactor v5 en src/reactor/: {reactor_code if reactor_code else \"NO EXISTE\"}')
print(f'Outputs reactor v5 en results/: {len(reactor_results)} archivos')
for f in sorted(reactor_results):
    print(f'  {f.name}')

# Conclusión
if not reactor_code:
    print('\nREACTOR v5: SOLO OUTPUTS (sesiones manuales). NO HAY CÓDIGO AUTOMATIZADO.')
"
```

**Resultado esperado:** 0 archivos de código v5 en src/reactor/. Los outputs en results/reactor_v5/ son de sesiones manuales con Claude.

---

## PASO 6: Models C1-C4 — Smoke test

```bash
cd @project/ && python3 -c "
from pathlib import Path

# Verificar imports
try:
    from src.models.trainer import train_all
    from src.models.evaluate import evaluate_all
    from src.models.router_embeddings import explore
    from src.models.clasificador import Clasificador
    from src.models.scorer import Scorer
    from src.models.compositor_weights import CompositorWeights
    print('Imports models: PASS')
except ImportError as e:
    print(f'Imports models: FAIL — {e}')

# Verificar si hay datos para entrenar
data_dir = Path('data/sinteticos')
if data_dir.exists():
    files = list(data_dir.glob('*.json'))
    print(f'Datos sintéticos: {len(files)} archivos')
    for f in files:
        print(f'  {f.name}')
else:
    print('Datos sintéticos: NO EXISTEN (data/sinteticos/ no existe)')

# Verificar si hay modelos entrenados
models_dir = Path('data/modelos')
if models_dir.exists():
    files = list(models_dir.glob('*'))
    print(f'Modelos entrenados: {len(files)} archivos')
else:
    print('Modelos entrenados: NO EXISTEN (data/modelos/ no existe)')
"
```

**Resultado esperado:** Imports OK, datos sintéticos pueden o no existir, modelos entrenados probablemente no.

---

## PASO 7: Code OS — Verificar estado

```bash
cd @project/ && python3 -c "
# Verificar que Code OS monta como sub-app
try:
    from motor_v1_validation.agent.api import app as code_os_app
    routes = [r.path for r in code_os_app.routes if hasattr(r, 'path')]
    print(f'Code OS endpoints: {routes}')
    print('Code OS mount: PASS')
except Exception as e:
    print(f'Code OS mount: FAIL — {e}')
"
```

---

## PASO 8: Resumen — Generar informe

```bash
cd @project/ && python3 -c "
print('''
========================================
AUDITORÍA FUNCIONAL DE MOTORES
========================================

| Motor | Estado | Detalle |
|-------|--------|---------|
| Motor vN (pipeline 7 capas + ACD) | ¿? | Pipeline end-to-end, 7 capas + ACD integrado |
| Gestor — compilador | ¿? | Compila programas bajo demanda |
| Gestor — loop lento | ¿? | Análisis periódico, poda, recompilación |
| Reactor v1 (sintéticos) | ¿? | 4 sub-pipelines B1-B4 |
| Reactor v5/v5.2 (ACD) | ¿? | Código automatizado para generar P/R/estados |
| Reactor v4 (telemetría) | ¿? | Generar preguntas desde datos reales |
| Models C1-C4 | ¿? | Modelos ligeros entrenados |
| Code OS | ¿? | Agente autónomo montado en /code-os/* |

Rellenar ¿? con resultado de cada paso.
''')
"
```

**Acción:** Después de ejecutar todos los pasos, rellenar la tabla con FUNCIONAL / PARCIAL / STUB / NO EXISTE y guardar como `results/AUDITORIA_MOTORES.md`.

---

## ARCHIVOS QUE SE CREAN

| Archivo | Qué hace |
|---------|----------|
| `results/AUDITORIA_MOTORES.md` | Informe con estado real de cada motor |

## ARCHIVOS QUE NO SE TOCAN

Ninguno. Esta es auditoría de solo lectura + smoke tests.

## NOTAS

- El paso 1 (Motor vN) gasta ~$0.01 — es el único con llamada LLM real
- Los demás pasos son verificación de imports y estructura
- El informe resultante es el input para decidir: ¿Gestor loop lento primero, o Reactor v5 como código?
- **Hipótesis previa:** Motor vN=FUNCIONAL, Gestor compilador=FUNCIONAL, Gestor loop lento=NO EXISTE, Reactor v1=FUNCIONAL, Reactor v5=NO EXISTE (solo outputs), Reactor v4=NO EXISTE, Models=PARCIAL, Code OS=FUNCIONAL (post B-ACD-00 a B25)
