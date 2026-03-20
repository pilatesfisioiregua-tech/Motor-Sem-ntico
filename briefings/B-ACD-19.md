# B-ACD-19: Consolidado Post-ACD — Deploy + Models + Gestor + Reactores

**Fecha:** 2026-03-20
**Ejecutor:** Claude Code
**Dependencia:** B-ACD-16 ✅, B-ACD-17 ✅ (local), B-ACD-18 ✅
**Coste total estimado:** ~$0.05 (Fase C usa LLM para análisis)

---

## CONTEXTO

Pipeline ACD en producción. DB V4 con migrations listas (pendiente deploy). Auditoría de motores completada: Motor vN FUNCIONAL, Gestor compilador FUNCIONAL, Code OS FUNCIONAL, Reactor v1 FUNCIONAL, Gestor loop lento NO EXISTE, Reactor v5 SOLO OUTPUTS, Reactor v4 NO EXISTE, Models STUB.

Este briefing consolida 5 mejoras en fases independientes. Cada fase tiene pass/fail propio. Si una fase falla, las siguientes pueden continuar (excepto Fase A que es prerequisito).

---

## FASE A: Deploy con Migrations V4 (~2 min)

### A1. Integrar migrations en startup

**Archivo:** `@project/src/db/client.py` — LEER PRIMERO.

Después de `execute_schema()`, AÑADIR una función que ejecuta los SQL de migrations:

```python
async def execute_migrations():
    """Ejecuta migrations SQL idempotentes (V4+)."""
    import os
    from pathlib import Path
    pool = await get_pool()
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    sql_files = sorted(migrations_dir.glob("*.sql"))
    async with pool.acquire() as conn:
        for sql_file in sql_files:
            try:
                sql = sql_file.read_text()
                await conn.execute(sql)
                log.info("migration_ok", file=sql_file.name)
            except Exception as e:
                log.warning("migration_skip", file=sql_file.name, error=str(e))
```

**Archivo:** `@project/src/main.py` — LEER PRIMERO.

En la función `lifespan()`, después de `await execute_schema()`, AÑADIR:

```python
        from src.db.client import execute_migrations
        await execute_migrations()
        log.info("startup_migrations_done")
```

### A2. Ejecutar seeds Python en startup

Los 3 seeds Python (pensamientos, razonamientos, estados) deben correr después de migrations SQL.

**Archivo:** `@project/src/db/client.py` — AÑADIR:

```python
async def execute_seeds():
    """Ejecuta seeds Python idempotentes (V4+)."""
    import importlib
    import sys
    from pathlib import Path

    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    if not migrations_dir.exists():
        return

    # Añadir raíz del proyecto al path para imports
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    py_files = sorted(migrations_dir.glob("v4_seed_*.py"))
    for py_file in py_files:
        try:
            # Importar y ejecutar la función seed()
            spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, 'seed'):
                await mod.seed()
                log.info("seed_ok", file=py_file.name)
        except Exception as e:
            log.warning("seed_skip", file=py_file.name, error=str(e))
```

Y en `lifespan()` de main.py, después de `execute_migrations()`:

```python
        from src.db.client import execute_seeds
        await execute_seeds()
        log.info("startup_seeds_done")
```

### A3. Deploy

```bash
cd @project/ && fly deploy --strategy immediate
```

### A4. Verificar

```bash
cd @project/ && python3 -c "
import asyncio, httpx

async def check():
    base = 'https://motor-semantico-omni.fly.dev'
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f'{base}/health')
        print(f'Health: {r.json()}')

asyncio.run(check())
"
```

Luego verificar logs:
```bash
fly logs -a motor-semantico-omni | grep -E 'migration_ok|seed_ok|startup'
```

**Pass/fail Fase A:**
- Deploy completa sin error
- Logs muestran `migration_ok` para los .sql files
- Logs muestran `seed_ok` para los seed .py files
- `/health` responde OK

---

## FASE B: Models — Desbloquear dependencias (~5 min)

### B1. Instalar scikit-learn

**Archivo:** `@project/requirements.txt` — LEER PRIMERO, luego AÑADIR:

```
scikit-learn>=1.4
```

**Archivo:** `@project/Dockerfile` — LEER PRIMERO. Verificar que `pip install -r requirements.txt` existe en el build. Si no, añadir.

### B2. Verificar imports

```bash
cd @project/ && pip install scikit-learn && python3 -c "
from src.models.trainer import train_all
from src.models.evaluate import evaluate_all
from src.models.clasificador import Clasificador
from src.models.scorer import Scorer
from src.models.compositor_weights import CompositorWeights
print('PASS: Models imports OK')
"
```

### B3. Verificar datos sintéticos

```bash
cd @project/ && python3 -c "
from pathlib import Path
data_dir = Path('data/sinteticos')
if data_dir.exists():
    files = list(data_dir.glob('*.json'))
    print(f'Datos existentes: {[f.name for f in files]}')
else:
    print('data/sinteticos/ no existe — Reactor v1 necesita correr primero')
    print('Para generar: POST /reactor/ejecutar (requiere API keys en fly.io)')
"
```

**Nota:** Si no hay datos, Models queda DESBLOQUEADO (imports OK) pero no entrenado. El entrenamiento requiere ejecutar Reactor v1 primero en fly.io (tiene las API keys). Esto puede hacerse via:

```bash
curl -X POST https://motor-semantico-omni.fly.dev/reactor/ejecutar
```

**Pass/fail Fase B:**
- `scikit-learn` instalado
- 6/6 imports pasan
- Si hay datos → entrenar con `POST /models/entrenar`. Si no → documentar que falta correr Reactor v1.

---

## FASE C: Gestor Loop Lento v0 (~30 min)

El corazón de esta sesión. Implementa el análisis periódico que permite al sistema aprender.

### C1. Crear src/gestor/analizador.py

**Este es el archivo nuevo principal.** El analizador consulta la DB y produce un informe de efectividad.

```python
"""Gestor Loop Lento v0 — Analiza patrones de ejecución.

Consulta datapoints_efectividad + diagnosticos + ejecuciones.
Produce un informe: qué INTs/P/R funcionan, cuáles no, qué podar, qué promover.

Maestro V4 §7.2, §7.3.
Cadencia: manual (v0), periódico (v1).
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from collections import defaultdict

log = structlog.get_logger()


@dataclass
class InformeGestor:
    """Output del loop lento."""
    # Estadísticas globales
    total_ejecuciones: int = 0
    total_diagnosticos: int = 0
    total_datapoints: int = 0

    # Por inteligencia
    ints_efectivas: list[dict] = field(default_factory=list)      # [{id, n, score_medio}]
    ints_inefectivas: list[dict] = field(default_factory=list)    # [{id, n, score_medio}]

    # Por estado ACD
    estados_frecuentes: list[dict] = field(default_factory=list)  # [{estado, n, pct}]
    estados_resultados: list[dict] = field(default_factory=list)  # [{estado, cierre, inerte, toxico}]

    # Por modelo
    modelos_efectivos: list[dict] = field(default_factory=list)   # [{modelo, n, score_medio}]

    # Recomendaciones
    podar: list[str] = field(default_factory=list)       # INTs con score < 0.3 consistente
    promover: list[str] = field(default_factory=list)     # INTs con score > 0.7 consistente
    investigar: list[str] = field(default_factory=list)   # Patrones anómalos

    def to_dict(self) -> dict:
        return {
            'total_ejecuciones': self.total_ejecuciones,
            'total_diagnosticos': self.total_diagnosticos,
            'total_datapoints': self.total_datapoints,
            'ints_efectivas': self.ints_efectivas,
            'ints_inefectivas': self.ints_inefectivas,
            'estados_frecuentes': self.estados_frecuentes,
            'estados_resultados': self.estados_resultados,
            'modelos_efectivos': self.modelos_efectivos,
            'podar': self.podar,
            'promover': self.promover,
            'investigar': self.investigar,
        }


async def analizar() -> InformeGestor:
    """Ejecuta el loop lento: consulta DB → produce informe.

    Returns:
        InformeGestor con estadísticas y recomendaciones.
    """
    from src.db.client import get_pool
    pool = await get_pool()
    informe = InformeGestor()

    async with pool.acquire() as conn:
        # === CONTEOS GLOBALES ===
        informe.total_ejecuciones = await conn.fetchval(
            "SELECT count(*) FROM ejecuciones") or 0
        informe.total_diagnosticos = await conn.fetchval(
            "SELECT count(*) FROM diagnosticos") or 0
        informe.total_datapoints = await conn.fetchval(
            "SELECT count(*) FROM datapoints_efectividad") or 0

        # === EFECTIVIDAD POR INT ===
        rows = await conn.fetch("""
            SELECT inteligencia,
                   count(*) as n,
                   avg(score_calidad) as score_medio,
                   avg(CASE WHEN gap_pre > 0 THEN (gap_pre - COALESCE(gap_post, gap_pre)) / gap_pre ELSE 0 END) as tasa_cierre
            FROM datapoints_efectividad
            WHERE score_calidad IS NOT NULL
            GROUP BY inteligencia
            ORDER BY score_medio DESC
        """)
        for r in rows:
            entry = {'id': r['inteligencia'], 'n': r['n'],
                     'score_medio': round(float(r['score_medio'] or 0), 3),
                     'tasa_cierre': round(float(r['tasa_cierre'] or 0), 3)}
            if float(r['score_medio'] or 0) >= 0.7:
                informe.ints_efectivas.append(entry)
                informe.promover.append(r['inteligencia'])
            elif float(r['score_medio'] or 0) < 0.3 and r['n'] >= 3:
                informe.ints_inefectivas.append(entry)
                informe.podar.append(r['inteligencia'])

        # === ESTADOS DIAGNÓSTICOS FRECUENTES ===
        rows = await conn.fetch("""
            SELECT estado_pre, count(*) as n
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            ORDER BY n DESC
        """)
        total_diag = informe.total_diagnosticos or 1
        for r in rows:
            informe.estados_frecuentes.append({
                'estado': r['estado_pre'],
                'n': r['n'],
                'pct': round(r['n'] / total_diag * 100, 1),
            })

        # === RESULTADO POR ESTADO ===
        rows = await conn.fetch("""
            SELECT estado_pre,
                   count(*) FILTER (WHERE resultado = 'cierre') as cierre,
                   count(*) FILTER (WHERE resultado = 'inerte') as inerte,
                   count(*) FILTER (WHERE resultado = 'toxico') as toxico,
                   count(*) as total
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL AND resultado IS NOT NULL
            GROUP BY estado_pre
            ORDER BY total DESC
        """)
        for r in rows:
            informe.estados_resultados.append({
                'estado': r['estado_pre'],
                'cierre': r['cierre'], 'inerte': r['inerte'], 'toxico': r['toxico'],
                'total': r['total'],
                'tasa_cierre': round(r['cierre'] / max(r['total'], 1), 3),
            })

        # === EFECTIVIDAD POR MODELO ===
        rows = await conn.fetch("""
            SELECT modelo, count(*) as n, avg(score_calidad) as score_medio
            FROM datapoints_efectividad
            WHERE score_calidad IS NOT NULL AND modelo IS NOT NULL
            GROUP BY modelo
            ORDER BY score_medio DESC
        """)
        for r in rows:
            informe.modelos_efectivos.append({
                'modelo': r['modelo'], 'n': r['n'],
                'score_medio': round(float(r['score_medio'] or 0), 3),
            })

        # === DETECTAR ANOMALÍAS ===
        # INTs prescritas mucho pero con bajo cierre
        rows = await conn.fetch("""
            SELECT d.estado_pre, d.prescripcion
            FROM diagnosticos d
            WHERE d.resultado = 'toxico' AND d.prescripcion IS NOT NULL
        """)
        toxic_ints = defaultdict(int)
        for r in rows:
            try:
                presc = json.loads(r['prescripcion']) if isinstance(r['prescripcion'], str) else r['prescripcion']
                for int_id in (presc.get('ints') or []):
                    toxic_ints[int_id] += 1
            except (json.JSONDecodeError, TypeError):
                pass
        for int_id, count in sorted(toxic_ints.items(), key=lambda x: -x[1]):
            if count >= 2:
                informe.investigar.append(
                    f"{int_id} prescrita {count} veces en casos tóxicos")

    log.info("gestor_analisis_completo",
             ejecuciones=informe.total_ejecuciones,
             diagnosticos=informe.total_diagnosticos,
             podar=len(informe.podar),
             promover=len(informe.promover))

    return informe
```

### C2. Crear endpoint /gestor/analizar

**Archivo:** `@project/src/main.py` — LEER PRIMERO. AÑADIR endpoint:

```python
@app.post("/gestor/analizar")
async def analizar_gestor():
    """Ejecuta el loop lento del Gestor — análisis de patrones."""
    log.info("gestor_analizar")
    try:
        from src.gestor.analizador import analizar
        informe = await analizar()
        return {"status": "ok", **informe.to_dict()}
    except Exception as e:
        log.error("gestor_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### C3. Test local (imports)

```bash
cd @project/ && python3 -c "
from src.gestor.analizador import analizar, InformeGestor
informe = InformeGestor()
print(f'InformeGestor fields: {list(informe.to_dict().keys())}')
print('PASS: Gestor analizador importa OK')
"
```

**Pass/fail Fase C:**
- `src/gestor/analizador.py` creado
- `InformeGestor` importa y se serializa
- Endpoint `/gestor/analizar` registrado
- Post-deploy: `POST /gestor/analizar` devuelve informe con datos reales

---

## FASE D: Reactor v4 Telemetría v0 (~20 min)

Esqueleto del reactor que usa datos reales de diagnosticos para detectar patrones.

### D1. Crear src/reactor/v4_telemetria.py

```python
"""Reactor v4 — Detecta patrones en telemetría real.

Lee diagnosticos + ejecuciones de DB. Detecta:
1. Estados más frecuentes → ¿estamos cubriendo los perfiles comunes?
2. Transiciones reales → ¿se cumplen las transiciones teóricas (§3.2)?
3. Prescripciones que funcionan → ¿qué INT×P×R realmente cierran gaps?
4. Brechas de cobertura → ¿hay estados sin prescripción efectiva?

Maestro V4 §8.3, §8.4.
Cadencia: manual (v0), post-N-ejecuciones (v1).
"""
from __future__ import annotations

import json
import structlog
from dataclasses import dataclass, field
from collections import defaultdict

log = structlog.get_logger()


@dataclass
class PatronTelemetria:
    """Un patrón detectado en datos reales."""
    tipo: str                # 'transicion', 'prescripcion_efectiva', 'brecha', 'recurrencia'
    descripcion: str
    datos: dict = field(default_factory=dict)
    confianza: float = 0.0  # 0-1, basado en N observaciones
    accion_sugerida: str = ""


@dataclass
class InformeReactor:
    """Output del Reactor v4."""
    total_diagnosticos: int = 0
    patrones: list[PatronTelemetria] = field(default_factory=list)
    preguntas_sugeridas: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'total_diagnosticos': self.total_diagnosticos,
            'patrones': [{'tipo': p.tipo, 'descripcion': p.descripcion,
                          'datos': p.datos, 'confianza': p.confianza,
                          'accion_sugerida': p.accion_sugerida}
                         for p in self.patrones],
            'preguntas_sugeridas': self.preguntas_sugeridas,
        }


async def detectar_patrones() -> InformeReactor:
    """Analiza diagnosticos en DB y detecta patrones accionables."""
    from src.db.client import get_pool
    pool = await get_pool()
    informe = InformeReactor()

    async with pool.acquire() as conn:
        informe.total_diagnosticos = await conn.fetchval(
            "SELECT count(*) FROM diagnosticos") or 0

        if informe.total_diagnosticos == 0:
            informe.patrones.append(PatronTelemetria(
                tipo='brecha',
                descripcion='Sin datos — ejecutar pipeline con casos reales primero',
                accion_sugerida='POST /motor/ejecutar con casos reales',
            ))
            return informe

        # === 1. RECURRENCIA DE ESTADOS ===
        rows = await conn.fetch("""
            SELECT estado_pre, count(*) as n,
                   avg(CASE WHEN resultado = 'cierre' THEN 1.0
                            WHEN resultado = 'inerte' THEN 0.5
                            WHEN resultado = 'toxico' THEN 0.0
                            ELSE NULL END) as score_medio
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            HAVING count(*) >= 2
            ORDER BY n DESC
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='recurrencia',
                descripcion=f"Estado '{r['estado_pre']}' aparece {r['n']} veces (score medio: {round(float(r['score_medio'] or 0), 2)})",
                datos={'estado': r['estado_pre'], 'n': r['n'], 'score': round(float(r['score_medio'] or 0), 3)},
                confianza=min(r['n'] / 10, 1.0),
                accion_sugerida=f"Optimizar prescripción para '{r['estado_pre']}'" if float(r['score_medio'] or 0) < 0.6 else "Prescripción efectiva — documentar",
            ))

        # === 2. TRANSICIONES REALES ===
        rows = await conn.fetch("""
            SELECT estado_pre, estado_post, resultado, count(*) as n
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL AND estado_post IS NOT NULL
            GROUP BY estado_pre, estado_post, resultado
            ORDER BY n DESC
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='transicion',
                descripcion=f"{r['estado_pre']} → {r['estado_post']} ({r['resultado']}, n={r['n']})",
                datos={'de': r['estado_pre'], 'a': r['estado_post'],
                       'resultado': r['resultado'], 'n': r['n']},
                confianza=min(r['n'] / 5, 1.0),
            ))

        # === 3. PRESCRIPCIONES EFECTIVAS ===
        rows = await conn.fetch("""
            SELECT prescripcion, resultado, estado_pre
            FROM diagnosticos
            WHERE prescripcion IS NOT NULL AND resultado = 'cierre'
        """)
        int_cierre = defaultdict(int)
        p_cierre = defaultdict(int)
        r_cierre = defaultdict(int)
        for row in rows:
            try:
                presc = json.loads(row['prescripcion']) if isinstance(row['prescripcion'], str) else row['prescripcion']
                for i in (presc.get('ints') or []):
                    int_cierre[i] += 1
                for p in (presc.get('ps') or []):
                    p_cierre[p] += 1
                for r in (presc.get('rs') or []):
                    r_cierre[r] += 1
            except (json.JSONDecodeError, TypeError):
                pass

        if int_cierre:
            top_ints = sorted(int_cierre.items(), key=lambda x: -x[1])[:5]
            informe.patrones.append(PatronTelemetria(
                tipo='prescripcion_efectiva',
                descripcion=f"INTs que más cierran: {', '.join(f'{k}({v})' for k,v in top_ints)}",
                datos={'ints': dict(top_ints), 'ps': dict(sorted(p_cierre.items(), key=lambda x: -x[1])[:5]),
                       'rs': dict(sorted(r_cierre.items(), key=lambda x: -x[1])[:5])},
                confianza=min(sum(int_cierre.values()) / 20, 1.0),
            ))

        # === 4. BRECHAS ===
        # Estados sin cierre
        rows = await conn.fetch("""
            SELECT estado_pre
            FROM diagnosticos
            WHERE estado_pre IS NOT NULL
            GROUP BY estado_pre
            HAVING count(*) FILTER (WHERE resultado = 'cierre') = 0
                   AND count(*) >= 2
        """)
        for r in rows:
            informe.patrones.append(PatronTelemetria(
                tipo='brecha',
                descripcion=f"Estado '{r['estado_pre']}' nunca cierra — revisar prescripción",
                datos={'estado': r['estado_pre']},
                confianza=0.8,
                accion_sugerida=f"Rediseñar prescripción para '{r['estado_pre']}'",
            ))

    log.info("reactor_v4_completo",
             diagnosticos=informe.total_diagnosticos,
             patrones=len(informe.patrones))

    return informe
```

### D2. Crear endpoint /reactor/telemetria

**Archivo:** `@project/src/main.py` — AÑADIR:

```python
@app.post("/reactor/telemetria")
async def reactor_telemetria():
    """Reactor v4 — Detecta patrones en datos reales."""
    log.info("reactor_telemetria")
    try:
        from src.reactor.v4_telemetria import detectar_patrones
        informe = await detectar_patrones()
        return {"status": "ok", **informe.to_dict()}
    except Exception as e:
        log.error("reactor_telemetria_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### D3. Test local (imports)

```bash
cd @project/ && python3 -c "
from src.reactor.v4_telemetria import detectar_patrones, InformeReactor, PatronTelemetria
informe = InformeReactor()
informe.patrones.append(PatronTelemetria(tipo='test', descripcion='test'))
d = informe.to_dict()
print(f'InformeReactor fields: {list(d.keys())}')
print(f'Patron serializa: {d[\"patrones\"][0]}')
print('PASS: Reactor v4 importa OK')
"
```

**Pass/fail Fase D:**
- `src/reactor/v4_telemetria.py` creado
- Imports OK
- Endpoint `/reactor/telemetria` registrado
- Post-deploy con datos: devuelve patrones reales

---

## FASE E: Reactor v5 como Código — Esqueleto (~15 min)

Automatiza lo que se hizo en sesiones manuales: dado un caso, generar clasificación INT×P×R + gradientes + estado ACD.

### E1. Crear src/reactor/v5_empirico.py

```python
"""Reactor v5 como código — Genera datos empíricos ACD automatizados.

Toma un caso en texto natural → ejecuta pipeline diagnóstico completo
→ produce dataset de entrenamiento para el Gestor.

Equivale a lo que se hizo manualmente en results/reactor_v5/
(50 pares × 7 dominios × 10 arquetipos × 210 datos 3L).

Maestro V4 §8.2.
"""
from __future__ import annotations

import json
import time
import structlog
from dataclasses import dataclass, field

log = structlog.get_logger()


@dataclass
class CasoReactor:
    """Un caso para el Reactor v5."""
    dominio: str
    descripcion: str
    arquetipo_esperado: str | None = None


@dataclass
class ResultadoReactor:
    """Output de un caso procesado por el Reactor v5."""
    caso: CasoReactor
    vector_funcional: dict          # {F1: x, F2: x, ...}
    lentes: dict                    # {S: x, Se: x, C: x}
    estado: str                     # "operador_ciego", "E3", etc.
    repertorio: dict                # {ints_activas, ps, rs}
    prescripcion: dict | None       # si es desequilibrado
    tiempo_s: float = 0.0
    coste_usd: float = 0.0

    def to_dict(self) -> dict:
        return {
            'dominio': self.caso.dominio,
            'descripcion': self.caso.descripcion[:200],
            'arquetipo_esperado': self.caso.arquetipo_esperado,
            'vector': self.vector_funcional,
            'lentes': self.lentes,
            'estado': self.estado,
            'repertorio': self.repertorio,
            'prescripcion': self.prescripcion,
            'tiempo_s': self.tiempo_s,
            'coste_usd': self.coste_usd,
        }


# Casos semilla por dominio (expandible)
CASOS_SEMILLA: list[CasoReactor] = [
    CasoReactor("pilates", "Estudio de Pilates reformer premium con 8 años de operación. Factura 12K/mes, 85% ocupación. Altamente dependiente de la dueña-instructora. Sin manual de operaciones, sin plan de sustitución, sin sistema de formación de instructores. Identidad clara pero atada a una persona.", "genio_mortal"),
    CasoReactor("saas", "SaaS B2B de gestión de inventario. 200 clientes, MRR 45K, churn 4% mensual. Equipo de 8 personas. El CTO escribe el 60% del código. No hay documentación técnica. Roadmap cambia cada sprint. Los clientes grandes piden custom features.", "operador_ciego"),
    CasoReactor("restauracion", "Restaurante familiar 30 años en zona turística. 3 generaciones. Recetas del abuelo. Terraza con vistas. TripAdvisor 4.8. No aceptan reservas online. El menú no ha cambiado en 5 años. Los hijos no quieren seguir.", "zombi_inmortal"),
    CasoReactor("clinica", "Clínica dental 15 profesionales. Factura 80K/mes. ISO 9001. Protocolos escritos para todo. 3 sedes. El director revisa cada presupuesto de más de 500€. No delega decisiones clínicas. Los asociados se van a los 2 años.", "automata_eterno"),
    CasoReactor("educacion", "Academia de idiomas online. 2000 alumnos activos. Modelo freemium. El fundador da clases en YouTube con 500K suscriptores. La plataforma la mantiene un freelance. No hay equipo pedagógico. El contenido lo genera el fundador solo.", "genio_mortal"),
]


async def procesar_caso(caso: CasoReactor) -> ResultadoReactor:
    """Procesa un caso con el pipeline ACD completo.

    Usa: evaluador_funcional → diagnosticar() → prescribir().
    """
    t0 = time.time()
    coste = 0.0

    # 1. Evaluar vector funcional (LLM call)
    from src.tcf.evaluador_funcional import evaluar_funcional
    vector_result = await evaluar_funcional(caso.descripcion)
    vector = vector_result.vector
    coste += vector_result.coste_usd

    # 2. Diagnosticar
    from src.tcf.diagnostico import diagnosticar
    diag = await diagnosticar(caso.descripcion)
    coste += diag.coste_usd

    # 3. Prescribir (si desequilibrado)
    prescripcion_dict = None
    if diag.estado.tipo == 'desequilibrado':
        from src.tcf.prescriptor import prescribir
        presc = prescribir(diag)
        prescripcion_dict = {
            'ints': presc.ints, 'ps': presc.ps, 'rs': presc.rs,
            'secuencia': presc.secuencia, 'frenar': presc.frenar,
            'lente_objetivo': presc.lente_objetivo,
            'modos': presc.nivel_logico.modos if presc.nivel_logico else [],
            'objetivo': presc.objetivo,
        }

    dt = time.time() - t0

    return ResultadoReactor(
        caso=caso,
        vector_funcional=vector.to_dict(),
        lentes=diag.estado_campo.lentes,
        estado=diag.estado.id,
        repertorio={
            'ints_activas': diag.repertorio.ints_activas if diag.repertorio else [],
            'ints_atrofiadas': diag.repertorio.ints_atrofiadas if diag.repertorio else [],
            'ps_activos': diag.repertorio.ps_activos if diag.repertorio else [],
            'rs_activos': diag.repertorio.rs_activos if diag.repertorio else [],
        },
        prescripcion=prescripcion_dict,
        tiempo_s=round(dt, 1),
        coste_usd=round(coste, 4),
    )


async def run(casos: list[CasoReactor] | None = None) -> dict:
    """Ejecuta el Reactor v5 sobre una lista de casos.

    Si no se pasan casos, usa CASOS_SEMILLA.
    """
    if casos is None:
        casos = CASOS_SEMILLA

    resultados = []
    total_coste = 0.0
    total_tiempo = 0.0

    for caso in casos:
        try:
            r = await procesar_caso(caso)
            resultados.append(r.to_dict())
            total_coste += r.coste_usd
            total_tiempo += r.tiempo_s
            log.info("reactor_v5_caso_ok",
                     dominio=caso.dominio, estado=r.estado,
                     tiempo=r.tiempo_s, coste=r.coste_usd)
        except Exception as e:
            log.error("reactor_v5_caso_error",
                      dominio=caso.dominio, error=str(e))
            resultados.append({
                'dominio': caso.dominio,
                'error': str(e),
            })

    return {
        'n_casos': len(casos),
        'n_ok': len([r for r in resultados if 'error' not in r]),
        'coste_total': round(total_coste, 4),
        'tiempo_total': round(total_tiempo, 1),
        'resultados': resultados,
    }
```

### E2. Crear endpoint /reactor/v5

**Archivo:** `@project/src/main.py` — AÑADIR:

```python
@app.post("/reactor/v5")
async def reactor_v5():
    """Reactor v5 — Genera datos empíricos ACD con casos semilla."""
    log.info("reactor_v5_ejecutar")
    try:
        from src.reactor.v5_empirico import run
        result = await run()
        return {"status": "ok", **result}
    except Exception as e:
        log.error("reactor_v5_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
```

### E3. Test local (imports)

```bash
cd @project/ && python3 -c "
from src.reactor.v5_empirico import CasoReactor, ResultadoReactor, CASOS_SEMILLA, run
print(f'Casos semilla: {len(CASOS_SEMILLA)}')
for c in CASOS_SEMILLA:
    print(f'  {c.dominio}: {c.arquetipo_esperado}')
print('PASS: Reactor v5 importa OK')
"
```

**Pass/fail Fase E:**
- `src/reactor/v5_empirico.py` creado con 5 casos semilla
- Imports OK
- Endpoint `/reactor/v5` registrado
- **NO ejecutar en local** — requiere OPENROUTER_API_KEY (solo fly.io)
- Post-deploy: `POST /reactor/v5` genera dataset ACD automatizado (~$0.01/caso)

---

## VERIFICACIÓN FINAL

```bash
cd @project/ && python3 -c "
from src.main import app

# Listar todos los endpoints
endpoints = []
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        endpoints.append(f'{list(route.methods)} {route.path}')

for e in sorted(endpoints):
    print(e)

expected = ['/health', '/motor/ejecutar', '/reactor/ejecutar',
            '/reactor/telemetria', '/reactor/v5',
            '/gestor/analizar', '/models/entrenar']
found = [e.split(' ')[1] for e in endpoints if not e.startswith(\"['HEAD'\")] if 'code-os' not in e]
print(f'\nEndpoints nuevos verificados:')
for exp in ['/gestor/analizar', '/reactor/telemetria', '/reactor/v5']:
    ok = any(exp in e for e in endpoints)
    print(f'  {\"PASS\" if ok else \"FAIL\"}: {exp}')
"
```

### Deploy final

```bash
cd @project/ && fly deploy --strategy immediate
```

### Smoke test post-deploy

```bash
# Health
curl https://motor-semantico-omni.fly.dev/health

# Gestor (analiza lo que hay)
curl -X POST https://motor-semantico-omni.fly.dev/gestor/analizar | python3 -m json.tool

# Reactor v4 (detecta patrones)
curl -X POST https://motor-semantico-omni.fly.dev/reactor/telemetria | python3 -m json.tool
```

**NO ejecutar Reactor v5 como smoke test** — genera 5 diagnósticos reales (~$0.05).

---

## RESUMEN DE ARCHIVOS

### Crean
| Archivo | Fase | Qué hace |
|---------|------|----------|
| `src/gestor/analizador.py` | C | Loop lento v0: analiza DB → informe |
| `src/reactor/v4_telemetria.py` | D | Detecta patrones en diagnosticos |
| `src/reactor/v5_empirico.py` | E | Pipeline ACD automatizado con 5 casos semilla |

### Editan
| Archivo | Fase | Qué cambia |
|---------|------|------------|
| `src/db/client.py` | A | +execute_migrations() +execute_seeds() |
| `src/main.py` | A,C,D,E | +startup migrations/seeds +3 endpoints nuevos |
| `requirements.txt` | B | +scikit-learn |

### No tocan
Toda la lógica ACD existente (src/tcf/*), el pipeline (src/pipeline/*), el gestor compilador (src/gestor/compilador.py).

---

## NOTAS

- **Las 5 fases son independientes entre sí** (excepto A que es prereq para el deploy)
- **Fase A es la más crítica** — ejecuta las migrations V4 contra DB real
- **Fase C (Gestor) es el mayor valor** — es lo que falta para cerrar el loop autopoiético
- **Fases D y E son esqueletos v0** — diseñados para crecer con datos
- **Reactor v5 (Fase E) gasta dinero** (~$0.01/caso × 5 = $0.05) — solo ejecutar post-deploy como test deliberado
- **Models (Fase B) queda parcial** — imports desbloqueados, pero el entrenamiento necesita datos del Reactor v1 ejecutado en fly.io
