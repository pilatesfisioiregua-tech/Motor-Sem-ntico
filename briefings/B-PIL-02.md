# B-PIL-02: Seed Data — 16 grupos + tenant Authentic Pilates

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-PIL-01 (tablas om_* creadas)
**Coste:** $0

---

## CONTEXTO

Las 29 tablas om_* están creadas (B-PIL-01). Ahora necesitamos datos iniciales:
1. Los 16 grupos con horarios reales (S1.2 del Exocortex v2.1)
2. Actualizar `execute_seeds()` para que detecte archivos `om_seed_*.py` además de `v4_seed_*.py`

**Fuente de verdad:** `docs/producto/casos/pilates/EXOCORTEX_PILATES_DEFINITIVO_v2.1.md` sección S1.2 y S4.

---

## FASE A: Actualizar execute_seeds para soportar om_seed_*

### A1. Editar `src/db/client.py`

**Archivo:** `@project/src/db/client.py` — LEER PRIMERO.

Buscar la función `execute_seeds()`. Cambiar la línea:

```python
    py_files = sorted(migrations_dir.glob("v4_seed_*.py"))
```

Por:

```python
    py_files = sorted(
        list(migrations_dir.glob("v4_seed_*.py")) +
        list(migrations_dir.glob("om_seed_*.py"))
    )
```

Esto permite que tanto los seeds ACD (`v4_seed_*`) como los seeds Pilates (`om_seed_*`) se ejecuten en startup.

---

## FASE B: Crear seed de grupos

### B1. Crear `migrations/om_seed_grupos.py`

```python
"""Seed: 16 grupos de Authentic Pilates.

Fuente: EXOCORTEX_PILATES_DEFINITIVO_v2.1.md S1.2
Idempotente: usa INSERT ... ON CONFLICT DO NOTHING con nombre+tenant como clave natural.
"""

TENANT = "authentic_pilates"

GRUPOS = [
    # Lunes y Miércoles (6 grupos)
    {
        "nombre": "L-X 09:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "09:00", "hf": "10:00"}, {"dia": 3, "hi": "09:00", "hf": "10:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "L-X 13:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "13:00", "hf": "14:00"}, {"dia": 3, "hi": "13:00", "hf": "14:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "L-X 17:15 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "17:15", "hf": "18:15"}, {"dia": 3, "hi": "17:15", "hf": "18:15"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "L-X 18:15 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "18:15", "hf": "19:15"}, {"dia": 3, "hi": "18:15", "hf": "19:15"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "L-X 19:15 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "19:15", "hf": "20:15"}, {"dia": 3, "hi": "19:15", "hf": "20:15"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "L-X 20:15 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 1, "hi": "20:15", "hf": "21:15"}, {"dia": 3, "hi": "20:15", "hf": "21:15"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },

    # Martes y Jueves (8 grupos)
    {
        "nombre": "M-J 09:00 Mat",
        "tipo": "mat",
        "capacidad_max": 6,
        "dias_semana": [{"dia": 2, "hi": "09:00", "hf": "10:00"}, {"dia": 4, "hi": "09:00", "hf": "10:00"}],
        "precio_mensual": 55.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 10:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "10:00", "hf": "11:00"}, {"dia": 4, "hi": "10:00", "hf": "11:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 16:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "16:00", "hf": "17:00"}, {"dia": 4, "hi": "16:00", "hf": "17:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 17:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "17:00", "hf": "18:00"}, {"dia": 4, "hi": "17:00", "hf": "18:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 18:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "18:00", "hf": "19:00"}, {"dia": 4, "hi": "18:00", "hf": "19:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 19:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "19:00", "hf": "20:00"}, {"dia": 4, "hi": "19:00", "hf": "20:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 20:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "20:00", "hf": "21:00"}, {"dia": 4, "hi": "20:00", "hf": "21:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-J 21:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 2, "hi": "21:00", "hf": "22:00"}, {"dia": 4, "hi": "21:00", "hf": "22:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },

    # Excepciones (2 grupos)
    {
        "nombre": "J-V 11:00/12:00 Estándar",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 4, "hi": "11:00", "hf": "12:00"}, {"dia": 5, "hi": "12:00", "hf": "13:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
    },
    {
        "nombre": "M-V 18:00 Estándar (migrando)",
        "tipo": "estandar",
        "capacidad_max": 4,
        "dias_semana": [{"dia": 3, "hi": "18:00", "hf": "19:00"}, {"dia": 5, "hi": "18:00", "hf": "19:00"}],
        "precio_mensual": 105.00,
        "frecuencia_semanal": 2,
        "estado": "migrando",
    },
]


async def seed():
    """Inserta los 16 grupos. Idempotente por nombre+tenant."""
    import json
    import structlog
    log = structlog.get_logger()

    # Import dentro de la función para evitar imports circulares
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from src.db.client import get_pool
    pool = await get_pool()

    inserted = 0
    skipped = 0

    async with pool.acquire() as conn:
        for g in GRUPOS:
            # Verificar si ya existe
            exists = await conn.fetchval(
                "SELECT 1 FROM om_grupos WHERE tenant_id = $1 AND nombre = $2",
                TENANT, g["nombre"]
            )
            if exists:
                skipped += 1
                continue

            await conn.execute("""
                INSERT INTO om_grupos (tenant_id, nombre, tipo, capacidad_max, dias_semana,
                                       precio_mensual, frecuencia_semanal, estado)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8)
            """,
                TENANT,
                g["nombre"],
                g["tipo"],
                g["capacidad_max"],
                json.dumps(g["dias_semana"]),
                g["precio_mensual"],
                g["frecuencia_semanal"],
                g.get("estado", "activo"),
            )
            inserted += 1

    log.info("om_seed_grupos_done", inserted=inserted, skipped=skipped, total=len(GRUPOS))
```

### B2. Test local (imports)

```bash
cd @project/ && python3 -c "
import importlib.util, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('om_seed_grupos', 'migrations/om_seed_grupos.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print(f'Grupos definidos: {len(mod.GRUPOS)}')
print(f'Tenant: {mod.TENANT}')
for g in mod.GRUPOS:
    print(f'  {g[\"nombre\"]:40s} {g[\"tipo\"]:10s} cap={g[\"capacidad_max\"]} precio={g[\"precio_mensual\"]}')
print(f'PASS: {len(mod.GRUPOS)} grupos cargados')
"
```

Resultado esperado: 16 grupos, todos con datos correctos.

### B3. Deploy

```bash
cd @project/ && fly deploy --strategy immediate
```

### B4. Verificar seeds en producción

```bash
fly logs -a motor-semantico-omni | grep -E 'seed_ok|om_seed'
```

Y verificar datos:
```bash
fly postgres connect -a chief-os-omni -d chief_os_omni -c "SELECT nombre, tipo, capacidad_max, precio_mensual, estado FROM om_grupos WHERE tenant_id = 'authentic_pilates' ORDER BY nombre;"
```

**Pass/fail:**
- `execute_seeds` modificado para detectar `om_seed_*.py`
- `migrations/om_seed_grupos.py` creado con 16 grupos
- Test local muestra 16 grupos correctos
- Post-deploy: logs muestran `seed_ok` para `om_seed_grupos.py`
- Query devuelve 16 filas con datos correctos
- Re-deploy: logs muestran `seed_ok` pero inserted=0, skipped=16 (idempotente)

---

## NOTAS

- El grupo "M-V 18:00" tiene estado='migrando' — migrará a M-J 18:00 en ~2 meses
- El grupo "J-V 11:00/12:00" tiene horarios diferentes por día (excepcional)
- dias_semana usa formato JSONB: dia 1=lunes, 2=martes, 3=miércoles, 4=jueves, 5=viernes
- Todos los grupos son de Jesús como instructor
- No se crean clientes ni contratos aún — eso requiere decisión de migrar Excel o arrancar limpio
