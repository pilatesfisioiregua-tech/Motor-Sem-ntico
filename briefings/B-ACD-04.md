# B-ACD-04: Migración DB — tablas P, R, estados, diagnósticos

**Fecha:** 2026-03-19
**Ejecutor:** Claude Code
**Dependencia:** Ninguna (las tablas son independientes de B-ACD-01/02/03, solo comparten nombres)

---

## PASO 1: Crear archivo de migración

**Crear archivo:** `@project/../migrations/014_acd_tables.sql`

(Ruta completa: `/Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/014_acd_tables.sql`)

**Contenido EXACTO:**

```sql
-- =================================================================
-- Migration 014: ACD — tablas para Álgebra Cognitiva Diagnóstica
-- 4 tablas nuevas: tipos_pensamiento, tipos_razonamiento,
--                  estados_diagnosticos, diagnosticos
-- =================================================================

-- ── TABLA 1: Tipos de Pensamiento (15 entradas) ─────────────────

CREATE TABLE IF NOT EXISTS tipos_pensamiento (
    id TEXT PRIMARY KEY,                -- P01-P15
    nombre TEXT NOT NULL,
    descripcion TEXT,
    lente_preferente TEXT NOT NULL,      -- "salud", "sentido", "continuidad", "salud+sentido", etc.
    funciones_naturales TEXT[],          -- {"F3", "F5"}
    razonamientos_asociados TEXT[],      -- {"R03", "R09"}
    nivel_logico INTEGER,               -- 1-5
    ints_compatibles TEXT[],
    ints_incompatibles TEXT[],
    pregunta_activadora TEXT,
    cuando_usar TEXT,
    datos JSONB                          -- campos adicionales sin esquema fijo
);

-- ── TABLA 2: Tipos de Razonamiento (12 entradas) ────────────────

CREATE TABLE IF NOT EXISTS tipos_razonamiento (
    id TEXT PRIMARY KEY,                -- R01-R12
    nombre TEXT NOT NULL,
    descripcion TEXT,
    lente_preferente TEXT NOT NULL,
    funciones_naturales TEXT[],
    ints_compatibles TEXT[],
    genera TEXT,                         -- "Certeza operativa", "Transferencia cross-dominio", etc.
    limite TEXT,
    pregunta_activadora TEXT,
    datos JSONB
);

-- ── TABLA 3: Estados Diagnósticos (10 entradas) ─────────────────

CREATE TABLE IF NOT EXISTS estados_diagnosticos (
    id TEXT PRIMARY KEY,                -- E1, E2, E3, E4, operador_ciego, etc.
    nombre TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('equilibrado', 'desequilibrado')),
    descripcion TEXT,
    perfil_lentes TEXT,                 -- "S↑ Se↓ C↓" para desequilibrados, NULL para equilibrados
    condiciones JSONB NOT NULL,         -- umbrales numéricos
    flags TEXT[],                       -- {"peligro_oculto", "invisible_metricas_convencionales"}
    ints_tipicas_activas TEXT[],
    ints_tipicas_ausentes TEXT[],
    prescripcion_ps TEXT[],             -- P que hay que activar
    prescripcion_rs TEXT[],             -- R que hay que activar
    objetivo_prescripcion TEXT,         -- "CUESTIONAR", "EJECUTAR", "TRANSFERIR", etc.
    transiciones JSONB                  -- [{destino, via, nota}]
);

-- ── TABLA 4: Diagnósticos (historial por caso) ──────────────────

CREATE TABLE IF NOT EXISTS diagnosticos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    caso_input TEXT,                    -- texto del caso original
    ejecucion_id UUID,                  -- referencia a ejecuciones(id) si existe
    -- Pre-intervención
    vector_pre JSONB,                   -- {F1: 0.50, F2: 0.30, ...}
    lentes_pre JSONB,                   -- {salud: 0.40, sentido: 0.60, continuidad: 0.20}
    estado_pre TEXT,                    -- "genio_mortal", "E3", etc.
    flags_pre TEXT[],                   -- {"automata_oculto", "zona_toxica"}
    repertorio_inferido JSONB,          -- {ints_activas, ints_atrofiadas, ps_activos, rs_activos}
    -- Prescripción
    prescripcion JSONB,                 -- {ints, ps, rs, secuencia_funciones, frenar, modo, nivel_logico}
    -- Post-intervención
    vector_post JSONB,
    lentes_post JSONB,
    estado_post TEXT,
    flags_post TEXT[],
    -- Resultado
    resultado TEXT CHECK (resultado IN ('cierre', 'inerte', 'toxico', 'pendiente')),
    metricas JSONB                      -- {delta_se, delta_gap, repertorio_expansion, funciones_se_activas}
);

-- ── ÍNDICES ──────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_diagnosticos_estado_pre ON diagnosticos(estado_pre);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_resultado ON diagnosticos(resultado);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_created ON diagnosticos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_estados_tipo ON estados_diagnosticos(tipo);
```

---

## PASO 2: Actualizar schema.sql

**Archivo:** `@project/src/db/schema.sql`

**Acción:** Añadir AL FINAL del archivo (antes del último comentario de índices si existe, o al final absoluto):

Copiar el contenido EXACTO de la migración 014 al final de schema.sql. Esto asegura que `execute_schema()` cree las tablas en deploys frescos.

---

## PASO 3: Crear script de seed para P, R, estados

**Crear archivo:** `@project/../migrations/014_seed_acd.py`

(Ruta completa: `/Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/014_seed_acd.py`)

**Contenido:**

```python
"""Seed ACD tables from JSON files."""
import json
import asyncio
import asyncpg
from pathlib import Path

MOTOR_BASE = Path(__file__).parent.parent / "motor-semantico"
DB_URL = "postgresql://chief_os_omni:@motor-semantico-db.flycast:5432/omni_mind"

async def seed():
    conn = await asyncpg.connect(DB_URL)
    
    # 1. Seed tipos_pensamiento from pensamientos.json
    pfile = MOTOR_BASE / "src" / "meta_red" / "pensamientos.json"
    if pfile.exists():
        pensamientos = json.loads(pfile.read_text())
        for pid, p in pensamientos.items():
            await conn.execute("""
                INSERT INTO tipos_pensamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, razonamientos_asociados, nivel_logico,
                    ints_compatibles, ints_incompatibles, pregunta_activadora, cuando_usar)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre
            """, p['id'], p['nombre'], p.get('descripcion', ''), p['lente_preferente'],
                p.get('funciones_naturales', []), p.get('razonamientos_asociados', []),
                p.get('nivel_logico'), p.get('ints_compatibles', []),
                p.get('ints_incompatibles', []), p.get('pregunta_activadora', ''),
                p.get('cuando_usar', ''))
        print(f"Seeded {len(pensamientos)} tipos_pensamiento")

    # 2. Seed tipos_razonamiento from razonamientos.json
    rfile = MOTOR_BASE / "src" / "meta_red" / "razonamientos.json"
    if rfile.exists():
        razonamientos = json.loads(rfile.read_text())
        for rid, r in razonamientos.items():
            await conn.execute("""
                INSERT INTO tipos_razonamiento (id, nombre, descripcion, lente_preferente,
                    funciones_naturales, ints_compatibles, genera, limite, pregunta_activadora)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre
            """, r['id'], r['nombre'], r.get('descripcion', ''), r['lente_preferente'],
                r.get('funciones_naturales', []), r.get('ints_compatibles', []),
                r.get('genera', ''), r.get('limite', ''), r.get('pregunta_activadora', ''))
        print(f"Seeded {len(razonamientos)} tipos_razonamiento")

    # 3. Seed estados_diagnosticos from estados.json
    efile = MOTOR_BASE / "src" / "tcf" / "estados.json"
    if efile.exists():
        estados = json.loads(efile.read_text())
        count = 0
        for grupo in ['equilibrados', 'desequilibrados']:
            for eid, e in estados[grupo].items():
                await conn.execute("""
                    INSERT INTO estados_diagnosticos (id, nombre, tipo, descripcion,
                        perfil_lentes, condiciones, flags, prescripcion_ps, prescripcion_rs,
                        objetivo_prescripcion, transiciones)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (id) DO UPDATE SET nombre = EXCLUDED.nombre
                """, e['id'], e['nombre'], e['tipo'], e.get('descripcion', ''),
                    e.get('perfil_lentes'), json.dumps(e.get('condiciones', {})),
                    e.get('flags', []), e.get('prescripcion_ps', []),
                    e.get('prescripcion_rs', []), e.get('objetivo_prescripcion', ''),
                    json.dumps(e.get('transiciones', [])))
                count += 1
        print(f"Seeded {count} estados_diagnosticos")

    await conn.close()
    print("DONE")

if __name__ == "__main__":
    asyncio.run(seed())
```

---

## PASO 4: Ejecutar migración

**Opción A — Si fly proxy está disponible:**
```bash
# Abrir proxy a la DB
fly proxy 15432:5432 -a motor-semantico-db &
sleep 3

# Ejecutar SQL
psql "postgresql://chief_os_omni:@localhost:15432/omni_mind" -f /Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/014_acd_tables.sql

# Verificar tablas creadas
psql "postgresql://chief_os_omni:@localhost:15432/omni_mind" -c "\dt tipos_*" -c "\dt estados_*" -c "\dt diagnosticos"
```

**Opción B — Si fly proxy no está disponible:**
Dejar la migración lista para ejecutar en el próximo deploy. El archivo `schema.sql` actualizado hará que `execute_schema()` cree las tablas automáticamente.

**Pass/fail Paso 4:**
```
Si ejecutado: \dt muestra las 4 tablas nuevas (tipos_pensamiento, tipos_razonamiento, estados_diagnosticos, diagnosticos).
Si no ejecutado: los archivos SQL existen y son sintácticamente correctos.
```

---

## PASO 5: Verificar SQL sintácticamente (sin DB)

```bash
# Verificar que el SQL es parseable (sin conectar a DB)
python3 -c "
import re
sql = open('/Users/jesusfernandezdominguez/omni-mind-cerebro/migrations/014_acd_tables.sql').read()
# Contar CREATE TABLE
tables = re.findall(r'CREATE TABLE IF NOT EXISTS (\w+)', sql)
assert len(tables) == 4, f'Expected 4 tables, got {len(tables)}: {tables}'
expected = {'tipos_pensamiento', 'tipos_razonamiento', 'estados_diagnosticos', 'diagnosticos'}
assert set(tables) == expected, f'Missing tables: {expected - set(tables)}'
# Contar CREATE INDEX
indices = re.findall(r'CREATE INDEX IF NOT EXISTS (\w+)', sql)
assert len(indices) >= 3, f'Expected >=3 indices, got {len(indices)}'
print(f'PASS: {len(tables)} tablas + {len(indices)} índices en migración')
"
```

---

## PASO 6: Verificar schema.sql actualizado

```bash
python3 -c "
sql = open('/Users/jesusfernandezdominguez/omni-mind-cerebro/motor-semantico/src/db/schema.sql').read()
for tabla in ['tipos_pensamiento', 'tipos_razonamiento', 'estados_diagnosticos', 'diagnosticos']:
    assert tabla in sql, f'{tabla} no encontrada en schema.sql'
print('PASS: Las 4 tablas ACD están en schema.sql')
"
```

---

## ARCHIVOS QUE SE TOCAN

| Archivo | Acción |
|---------|--------|
| `migrations/014_acd_tables.sql` | CREAR (nuevo) |
| `migrations/014_seed_acd.py` | CREAR (nuevo) |
| `src/db/schema.sql` | AÑADIR 4 tablas al final |

## NOTAS

- La migración usa `IF NOT EXISTS` — es idempotente, se puede ejecutar múltiples veces sin error.
- El seed usa `ON CONFLICT DO UPDATE` — también idempotente.
- Si B-ACD-01/02/03 no han completado aún, el seed fallará en los JSON que falten. Eso es OK — se puede re-ejecutar después.
- La tabla `diagnosticos` NO tiene FOREIGN KEY a `ejecuciones(id)` para evitar dependencia circular. El campo `ejecucion_id` es UUID sin constraint.
