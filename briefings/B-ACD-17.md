# B-ACD-17: Migración DB → Maestro V4

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-16 ✅ (pipeline ACD en producción)
**Coste:** $0 (solo DDL + INSERT, sin LLM)

---

## CONTEXTO

El Maestro V4 (`docs/maestro/MAESTRO_V4.md`) redefine la Matriz de 3D (3L×7F×18INT) a 5D (3L×7F×18INT×15P×12R). El schema SQL actual tiene las tablas ACD (B-ACD-04) pero:

1. `inteligencias` no tiene `lente_primaria` — V4 §2.3 asigna afinidad de lente por INT
2. `tipos_pensamiento` — tabla existe, vacía. V4 §2.10 define 15 tipos
3. `tipos_razonamiento` — tabla existe, vacía. V4 §2.11 define 12 tipos
4. `estados_diagnosticos` — tabla existe, vacía. V4 §3 define 10 estados
5. `aristas_grafo` — solo modela INT↔INT. V4 define relaciones P↔P (IC5) y R↔R (IC6)

El pipeline ACD funciona hoy con JSON files. Esta migración alinea la DB para que el Gestor (loop lento) y Reactor v4 puedan consultar la DB directamente.

---

## PASO 0: Verificar estado actual de tablas

```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        tables = {
            'inteligencias': 'SELECT count(*) FROM inteligencias',
            'tipos_pensamiento': 'SELECT count(*) FROM tipos_pensamiento',
            'tipos_razonamiento': 'SELECT count(*) FROM tipos_razonamiento',
            'estados_diagnosticos': 'SELECT count(*) FROM estados_diagnosticos',
            'aristas_grafo': 'SELECT count(*) FROM aristas_grafo',
            'diagnosticos': 'SELECT count(*) FROM diagnosticos',
        }
        for t, q in tables.items():
            try:
                n = await conn.fetchval(q)
                print(f'{t}: {n} filas')
            except Exception as e:
                print(f'{t}: ERROR — {e}')

asyncio.run(check())
"
```

**Pass/fail:** Las 6 tablas existen. `tipos_pensamiento`, `tipos_razonamiento`, `estados_diagnosticos` tienen 0 filas.

---

## PASO 1: ALTER TABLE inteligencias — añadir lente_primaria

**Archivo:** `@project/src/db/schema.sql`

**Leer primero.** Luego AÑADIR al final del archivo (antes de los índices ACD o al final):

```sql
-- V4: Afinidad de lente por inteligencia (§2.3)
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lente_primaria TEXT;
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lentes_secundarias TEXT[];
```

**Y ejecutar el UPDATE con los datos de V4 §2.3:**

Crear archivo `@project/migrations/v4_lente_primaria.sql`:

```sql
-- V4 §2.3: Afinidad de lente por inteligencia
-- Generan S: INT-01, 02, 05, 07, 10, 11, 16
-- Generan Se: INT-03, 04, 06, 08, 09, 12, 14, 15, 17, 18
-- Generan C: INT-13 (+ secundarias: 02, 04, 12, 16, 18)

ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lente_primaria TEXT;
ALTER TABLE inteligencias ADD COLUMN IF NOT EXISTS lentes_secundarias TEXT[];

UPDATE inteligencias SET lente_primaria = 'S' WHERE id IN ('INT-01','INT-02','INT-05','INT-07','INT-10','INT-11','INT-16');
UPDATE inteligencias SET lente_primaria = 'Se' WHERE id IN ('INT-03','INT-04','INT-06','INT-08','INT-09','INT-12','INT-14','INT-15','INT-17','INT-18');
UPDATE inteligencias SET lente_primaria = 'C' WHERE id = 'INT-13';

-- Secundarias de C
UPDATE inteligencias SET lentes_secundarias = '{"C"}' WHERE id IN ('INT-02','INT-04','INT-12','INT-16','INT-18');
-- INT-13 ya tiene C como primaria, añadir S como secundaria
UPDATE inteligencias SET lentes_secundarias = '{"S"}' WHERE id = 'INT-13';
```

**Pass/fail paso 1:**
```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch('SELECT id, lente_primaria FROM inteligencias ORDER BY id')
        s = [r['id'] for r in rows if r['lente_primaria'] == 'S']
        se = [r['id'] for r in rows if r['lente_primaria'] == 'Se']
        c = [r['id'] for r in rows if r['lente_primaria'] == 'C']
        print(f'S ({len(s)}): {s}')
        print(f'Se ({len(se)}): {se}')
        print(f'C ({len(c)}): {c}')
        assert len(s) == 7, f'Expected 7 S, got {len(s)}'
        assert len(se) == 10, f'Expected 10 Se, got {len(se)}'
        assert len(c) == 1, f'Expected 1 C, got {len(c)}'
        print('PASS: lente_primaria correcta para 18 INTs')

asyncio.run(check())
"
```

---

## PASO 2: Seed tipos_pensamiento (15 filas)

**Fuente:** `@project/src/tcf/pensamientos.json` (ya existe, creado en B-ACD-01)

**Leer `pensamientos.json` primero.** Luego crear script:

Crear `@project/migrations/v4_seed_pensamientos.py`:

```python
"""Seed tipos_pensamiento desde pensamientos.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "tcf" / "pensamientos.json"

async def seed():
    with open(DATA) as f:
        ps = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM tipos_pensamiento")
        if count > 0:
            print(f"tipos_pensamiento ya tiene {count} filas — skip")
            return

        for p in ps:
            await conn.execute("""
                INSERT INTO tipos_pensamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, razonamientos_asociados, nivel_logico,
                    ints_compatibles, ints_incompatibles, pregunta_activadora, cuando_usar)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO NOTHING
            """,
                p['id'], p['nombre'], p.get('descripcion'),
                p['lente_preferente'], p.get('funciones_naturales'),
                p.get('razonamientos_asociados'), p.get('nivel_logico'),
                p.get('ints_compatibles'), p.get('ints_incompatibles'),
                p.get('pregunta_activadora'), p.get('cuando_usar'),
            )
        final = await conn.fetchval("SELECT count(*) FROM tipos_pensamiento")
        print(f"PASS: {final} pensamientos insertados")

asyncio.run(seed())
```

**Ejecutar:** `cd @project/ && python3 migrations/v4_seed_pensamientos.py`

**Pass/fail:** 15 filas en tipos_pensamiento.

---

## PASO 3: Seed tipos_razonamiento (12 filas)

**Fuente:** `@project/src/tcf/razonamientos.json` (ya existe, creado en B-ACD-02)

Crear `@project/migrations/v4_seed_razonamientos.py` — misma estructura que paso 2 pero con razonamientos.json y tabla tipos_razonamiento.

```python
"""Seed tipos_razonamiento desde razonamientos.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "tcf" / "razonamientos.json"

async def seed():
    with open(DATA) as f:
        rs = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM tipos_razonamiento")
        if count > 0:
            print(f"tipos_razonamiento ya tiene {count} filas — skip")
            return

        for r in rs:
            await conn.execute("""
                INSERT INTO tipos_razonamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, ints_compatibles, genera, limite,
                    pregunta_activadora)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING
            """,
                r['id'], r['nombre'], r.get('descripcion'),
                r['lente_preferente'], r.get('funciones_naturales'),
                r.get('ints_compatibles'), r.get('genera'), r.get('limite'),
                r.get('pregunta_activadora'),
            )
        final = await conn.fetchval("SELECT count(*) FROM tipos_razonamiento")
        print(f"PASS: {final} razonamientos insertados")

asyncio.run(seed())
```

**Ejecutar:** `cd @project/ && python3 migrations/v4_seed_razonamientos.py`

**Pass/fail:** 12 filas en tipos_razonamiento.

---

## PASO 4: Seed estados_diagnosticos (10 filas)

**Fuente:** `@project/src/tcf/estados.json` (ya existe, creado en B-ACD-03)

Crear `@project/migrations/v4_seed_estados.py`:

```python
"""Seed estados_diagnosticos desde estados.json."""
import asyncio
import json
from pathlib import Path
from src.db.client import get_pool

DATA = Path(__file__).parent.parent / "src" / "tcf" / "estados.json"

async def seed():
    with open(DATA) as f:
        estados = json.load(f)

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT count(*) FROM estados_diagnosticos")
        if count > 0:
            print(f"estados_diagnosticos ya tiene {count} filas — skip")
            return

        for e in estados:
            await conn.execute("""
                INSERT INTO estados_diagnosticos (id, nombre, tipo, descripcion,
                    perfil_lentes, condiciones, flags, ints_tipicas_activas,
                    ints_tipicas_ausentes, prescripcion_ps, prescripcion_rs,
                    objetivo_prescripcion, transiciones)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, $11, $12, $13::jsonb)
                ON CONFLICT (id) DO NOTHING
            """,
                e['id'], e['nombre'], e['tipo'], e.get('descripcion'),
                e.get('perfil_lentes'),
                json.dumps(e.get('condiciones', {})),
                e.get('flags'),
                e.get('ints_tipicas_activas'), e.get('ints_tipicas_ausentes'),
                e.get('prescripcion_ps'), e.get('prescripcion_rs'),
                e.get('objetivo_prescripcion'),
                json.dumps(e.get('transiciones', [])) if e.get('transiciones') else None,
            )
        final = await conn.fetchval("SELECT count(*) FROM estados_diagnosticos")
        print(f"PASS: {final} estados insertados")

asyncio.run(seed())
```

**Ejecutar:** `cd @project/ && python3 migrations/v4_seed_estados.py`

**Pass/fail:** 10 filas en estados_diagnosticos.

---

## PASO 5: Ampliar aristas_grafo para P↔P y R↔R

**Archivo:** `@project/src/db/schema.sql`

El CHECK actual en aristas_grafo es `tipo IN ('composicion', 'fusion', 'diferencial', 'redundancia')`. Necesitamos tipos nuevos para las relaciones V4:

- P↔P: `complementario_pp` (IC5: P06+P07, P05+P04, P08+P11)
- R↔R: `validacion_rr` (IC6: R01+R02/R03, R07+R08)

Crear `@project/migrations/v4_aristas_pr.sql`:

```sql
-- V4: Ampliar aristas_grafo para relaciones P↔P y R↔R
-- Quitar restricción antigua y poner una más amplia
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_tipo_check;
ALTER TABLE aristas_grafo ADD CONSTRAINT aristas_grafo_tipo_check
    CHECK (tipo IN ('composicion', 'fusion', 'diferencial', 'redundancia',
                    'complementario_pp', 'validacion_rr'));

-- IC5: Pares complementarios P↔P (Maestro V4 §2.10)
INSERT INTO aristas_grafo (origen, destino, tipo, peso, hallazgo_emergente)
VALUES
    ('P06', 'P07', 'complementario_pp', 0.90, 'Ciclo generar/seleccionar — divergente + convergente'),
    ('P05', 'P04', 'complementario_pp', 0.85, 'Deconstruir/reconstruir — primeros principios + diseño'),
    ('P05', 'P11', 'complementario_pp', 0.80, 'Deconstruir/reconstruir — primeros principios + encarnado'),
    ('P08', 'P11', 'complementario_pp', 0.85, 'Pensar sobre pensar / actuar — metacognición + encarnado')
ON CONFLICT DO NOTHING;

-- IC6: Validación cruzada R↔R (Maestro V4 §2.11)
INSERT INTO aristas_grafo (origen, destino, tipo, peso, hallazgo_emergente)
VALUES
    ('R01', 'R02', 'validacion_rr', 0.85, 'Deducción sin inducción = premisas no validadas (Maginot)'),
    ('R01', 'R03', 'validacion_rr', 0.85, 'Deducción sin abducción = certeza sin diagnóstico'),
    ('R02', 'R06', 'validacion_rr', 0.80, 'Inducción sin contrafactual = generalización sin excepciones (cisne negro)'),
    ('R07', 'R08', 'validacion_rr', 0.80, 'Bayesiano sin dialéctico = priors fijos, echo chamber')
ON CONFLICT DO NOTHING;
```

**Nota:** La tabla `aristas_grafo` tiene `origen TEXT REFERENCES inteligencias(id)`. Las FK apuntan a `inteligencias`, así que P y R no pueden ser insertados directamente como origen/destino SIN quitar la FK. **Dos opciones:**

- **Opción A (simple):** Quitar FK constraints y tratar aristas_grafo como grafo genérico (INT, P, R comparten namespace porque sus IDs son únicos: INT-01, P01, R01)
- **Opción B (limpia):** Crear tabla separada `relaciones_cognitivas` sin FK a inteligencias

**CR1 necesario:** Elige A o B. Si no decides, ejecutar Opción A (DROP FK + INSERT).

**Para Opción A:**
```sql
-- Quitar FK de inteligencias (P y R no están en esa tabla)
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_origen_fkey;
ALTER TABLE aristas_grafo DROP CONSTRAINT IF EXISTS aristas_grafo_destino_fkey;
```

**Pass/fail paso 5:**
```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        pp = await conn.fetchval(\"SELECT count(*) FROM aristas_grafo WHERE tipo = 'complementario_pp'\")
        rr = await conn.fetchval(\"SELECT count(*) FROM aristas_grafo WHERE tipo = 'validacion_rr'\")
        print(f'P↔P: {pp} aristas (esperado: 4)')
        print(f'R↔R: {rr} aristas (esperado: 4)')
        assert pp == 4 and rr == 4, 'Aristas P/R no insertadas'
        print('PASS: aristas V4 correctas')

asyncio.run(check())
"
```

---

## PASO 6: Verificación final completa

```bash
cd @project/ && python3 -c "
import asyncio
from src.db.client import get_pool

async def check():
    pool = await get_pool()
    async with pool.acquire() as conn:
        checks = [
            ('inteligencias con lente_primaria', 'SELECT count(*) FROM inteligencias WHERE lente_primaria IS NOT NULL', 18),
            ('tipos_pensamiento', 'SELECT count(*) FROM tipos_pensamiento', 15),
            ('tipos_razonamiento', 'SELECT count(*) FROM tipos_razonamiento', 12),
            ('estados_diagnosticos', 'SELECT count(*) FROM estados_diagnosticos', 10),
            ('aristas P↔P', \"SELECT count(*) FROM aristas_grafo WHERE tipo = 'complementario_pp'\", 4),
            ('aristas R↔R', \"SELECT count(*) FROM aristas_grafo WHERE tipo = 'validacion_rr'\", 4),
        ]
        all_pass = True
        for name, q, expected in checks:
            actual = await conn.fetchval(q)
            status = 'PASS' if actual == expected else 'FAIL'
            if actual != expected:
                all_pass = False
            print(f'{status}: {name} = {actual} (esperado {expected})')

        print(f'\n=== MIGRACIÓN V4 {\"PASS\" if all_pass else \"FAIL\"} ===')

asyncio.run(check())
"
```

**CRITERIO PASS GLOBAL:** 6/6 checks pasan.

---

## PASO 7: Deploy

```bash
cd @project/ && fly deploy --strategy immediate
```

Verificar que schema.sql + migrations corren limpiamente en startup.

---

## ARCHIVOS QUE SE CREAN

| Archivo | Qué hace |
|---------|----------|
| `migrations/v4_lente_primaria.sql` | ALTER + UPDATE inteligencias |
| `migrations/v4_seed_pensamientos.py` | INSERT 15 P en tipos_pensamiento |
| `migrations/v4_seed_razonamientos.py` | INSERT 12 R en tipos_razonamiento |
| `migrations/v4_seed_estados.py` | INSERT 10 estados en estados_diagnosticos |
| `migrations/v4_aristas_pr.sql` | ALTER CHECK + INSERT aristas P↔P, R↔R |

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `src/db/schema.sql` | EDITAR — añadir ALTER TABLE IF NOT EXISTS para lente_primaria |

## NOTAS

- Todas las migraciones son idempotentes (ON CONFLICT DO NOTHING, IF NOT EXISTS, count check antes de insert)
- Los JSON files siguen siendo la fuente primaria para el pipeline ACD — la DB es el store para Gestor y Reactor
- Si la DB no está disponible, el pipeline sigue funcionando (fire-and-forget)
- El paso 5 (aristas P/R) requiere CR1 para elegir Opción A vs B. Default: Opción A
