# BRIEFING_04 — DEPLOY FLY.IO + TESTS E2E

**Objetivo:** Desplegar en fly.io con Postgres, configurar secrets, tests E2E con los 3 casos de cartografía.
**Pre-requisito:** BRIEFING_00, 01, 02, 03 completados. Pipeline funcional en local.
**Output:** Motor corriendo en fly.io, accesible via HTTPS, tests pasando.

---

## 1. FLY.IO SETUP

### Comandos de setup

```bash
# Crear app
fly apps create motor-semantico-omni

# Crear Postgres (pgvector habilitado)
fly postgres create --name motor-semantico-db --region mad --vm-size shared-cpu-1x --initial-cluster-size 1 --volume-size 1

# Attach DB a la app
fly postgres attach motor-semantico-db --app motor-semantico-omni

# Verificar que DATABASE_URL está seteada
fly secrets list --app motor-semantico-omni
```

### Secrets

```bash
# API keys Anthropic (rotar 4)
fly secrets set ANTHROPIC_API_KEY_1="sk-ant-..." --app motor-semantico-omni
fly secrets set ANTHROPIC_API_KEY_2="sk-ant-..." --app motor-semantico-omni
fly secrets set ANTHROPIC_API_KEY_3="sk-ant-..." --app motor-semantico-omni
fly secrets set ANTHROPIC_API_KEY_4="sk-ant-..." --app motor-semantico-omni
```

### pgvector

```bash
# Conectar a la DB y habilitar pgvector
fly postgres connect --app motor-semantico-db
# Dentro de psql:
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Deploy

```bash
fly deploy --app motor-semantico-omni
```

### Seed DB en producción

```bash
# Opción A: Conectar via proxy y ejecutar SQL
fly proxy 15432:5432 --app motor-semantico-db &
DATABASE_URL="postgres://postgres:xxx@localhost:15432/motor_semantico" python scripts/seed_db.py

# Opción B: Ejecutar via fly ssh
fly ssh console --app motor-semantico-omni -C "python scripts/seed_db.py"
```

---

## 2. STARTUP HOOKS (src/main.py)

Añadir al server FastAPI:

```python
from contextlib import asynccontextmanager
from src.db.client import get_pool, close_pool, execute_schema
from src.pipeline.generador import load_inteligencias

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: pool DB + cargar inteligencias en memoria."""
    log.info("startup_begin")
    await get_pool()
    # Crear tablas si no existen (idempotente)
    await execute_schema()
    # Precargar inteligencias.json
    load_inteligencias()
    log.info("startup_complete")
    yield
    # Shutdown
    await close_pool()
    log.info("shutdown_complete")

app = FastAPI(title="Motor Semántico OMNI-MIND", version="0.1.0", lifespan=lifespan)
```

---

## 3. TESTS E2E

### 3 casos de cartografía (tests/test_pipeline_e2e.py)

```python
"""Tests E2E con los 3 casos reales de la cartografía."""
import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8080"  # o la URL de fly.io

CASO_CLINICA = {
    "input": "Soy odontólogo, tengo una clínica dental con 3 sillones y solo uso 2. Facturo 180K€/año con 63% de margen. Estoy pensando en abrir una segunda sede porque siento que estoy estancado. Mi socio (que es mi cuñado) no quiere invertir más. Tengo un préstamo de 45K€ pendiente.",
    "config": {
        "modo": "analisis",
        "profundidad": "normal"
    }
}

CASO_SAAS = {
    "input": "Soy CTO y cofundador de una startup SaaS B2B con 18 meses de runway. Tenemos 47 bugs críticos acumulados, 23% de churn mensual, y mi cofundador (CEO) quiere pivotar a enterprise. Yo creo que deberíamos arreglar el producto primero. Llevamos 3 meses sin hablar del tema real. El equipo son 8 personas y 2 están pensando en irse.",
    "config": {
        "modo": "analisis",
        "profundidad": "normal"
    }
}

CASO_CARRERA = {
    "input": "Soy abogada corporativa, 12 años en un despacho grande, gano 125K€/año. Estoy considerando dejar el derecho corporativo para trabajar en una ONG medioambiental. Mi pareja depende parcialmente de mis ingresos. Tengo hipoteca de 280K€ y 2 hijos pequeños. Siento que no estoy haciendo lo que importa pero me aterroriza el salto.",
    "config": {
        "modo": "analisis",
        "profundidad": "normal"
    }
}


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_clinica_dental():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_CLINICA)
        assert r.status_code == 200
        data = r.json()
        
        # Verificar estructura
        assert "algoritmo_usado" in data
        assert "resultado" in data
        assert "meta" in data
        
        # Verificar inteligencias seleccionadas
        intels = data["algoritmo_usado"]["inteligencias"]
        assert len(intels) >= 3
        assert len(intels) <= 6
        # Núcleo irreducible
        assert any(i in intels for i in ["INT-01", "INT-02"]), "Falta cuantitativa"
        assert any(i in intels for i in ["INT-08", "INT-17"]), "Falta humana"
        
        # Verificar resultado
        resultado = data["resultado"]
        assert resultado.get("narrativa") or resultado.get("hallazgos")
        
        # Verificar meta
        meta = data["meta"]
        assert meta["coste"] < 1.50, f"Coste {meta['coste']} > $1.50"
        assert meta["score_calidad"] >= 0
        
        print(f"\n=== CLÍNICA DENTAL ===")
        print(f"Inteligencias: {intels}")
        print(f"Coste: ${meta['coste']:.4f}")
        print(f"Tiempo: {meta['tiempo_s']:.1f}s")
        print(f"Score: {meta['score_calidad']}")


@pytest.mark.asyncio
async def test_saas_startup():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_SAAS)
        assert r.status_code == 200
        data = r.json()
        assert len(data["algoritmo_usado"]["inteligencias"]) >= 3
        assert data["meta"]["coste"] < 1.50
        
        print(f"\n=== SAAS STARTUP ===")
        print(f"Inteligencias: {data['algoritmo_usado']['inteligencias']}")
        print(f"Coste: ${data['meta']['coste']:.4f}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")
        print(f"Score: {data['meta']['score_calidad']}")


@pytest.mark.asyncio
async def test_cambio_carrera():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_CARRERA)
        assert r.status_code == 200
        data = r.json()
        assert len(data["algoritmo_usado"]["inteligencias"]) >= 3
        assert data["meta"]["coste"] < 1.50
        
        print(f"\n=== CAMBIO CARRERA ===")
        print(f"Inteligencias: {data['algoritmo_usado']['inteligencias']}")
        print(f"Coste: ${data['meta']['coste']:.4f}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")
        print(f"Score: {data['meta']['score_calidad']}")


@pytest.mark.asyncio
async def test_modo_conversacion():
    """Modo conversación: más rápido, menos inteligencias."""
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json={
            "input": "¿Debería subir precios un 15%?",
            "config": {"modo": "conversacion"}
        })
        assert r.status_code == 200
        data = r.json()
        intels = data["algoritmo_usado"]["inteligencias"]
        assert len(intels) <= 4, f"Conversación debería usar ≤3 inteligencias, usó {len(intels)}"
        
        print(f"\n=== CONVERSACIÓN ===")
        print(f"Inteligencias: {intels}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")


@pytest.mark.asyncio
async def test_modo_confrontacion():
    """Modo confrontación: incluye existenciales."""
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json={
            "input": "Llevo 15 años en este trabajo y no sé si tiene sentido seguir",
            "config": {"modo": "confrontacion"}
        })
        assert r.status_code == 200
        data = r.json()
        intels = data["algoritmo_usado"]["inteligencias"]
        assert any(i in intels for i in ["INT-17", "INT-18"]), "Confrontación debe incluir existenciales"
        
        print(f"\n=== CONFRONTACIÓN ===")
        print(f"Inteligencias: {intels}")
        print(f"Score: {data['meta']['score_calidad']}")
```

### Ejecución

```bash
# Local
uvicorn src.main:app --port 8080 &
pytest tests/test_pipeline_e2e.py -v -s

# Contra fly.io
BASE_URL=https://motor-semantico-omni.fly.dev pytest tests/test_pipeline_e2e.py -v -s
```

---

## 4. CRITERIO DE CIERRE MVP

Todos estos deben pasar para considerar el MVP completo:

- [ ] `GET /health` responde 200
- [ ] Pipeline end-to-end funcional: POST acepta input en lenguaje natural
- [ ] Router selecciona 4-5 inteligencias relevantes respetando reglas
- [ ] Compositor genera algoritmo con composiciones/fusiones
- [ ] Ejecutor ejecuta preguntas via Anthropic API
- [ ] Integrador produce síntesis final con narrativa + hallazgos + acciones
- [ ] 4 modos funcionan (análisis, generación, conversación, confrontación)
- [ ] Coste < $1.50 por ejecución
- [ ] Latencia < 150s en modo análisis, < 60s en conversación
- [ ] Telemetría guardada en DB
- [ ] Test E2E con los 3 casos de cartografía pasan
- [ ] Deploy en fly.io funcionando

---

## 5. TROUBLESHOOTING

### Rate limits Anthropic
- Las 4 keys rotan automáticamente (llm_client.py)
- Si aún hay 429s: reducir paralelismo en ejecutor (max 2 concurrent)
- Fallback: si Sonnet falla, usar Haiku para todo excepto integración

### Postgres connection
- fly.io Postgres usa SSL. Si falla: `DATABASE_URL += "?sslmode=require"`
- Pool max_size=10 para evitar saturar (fly.io free tier)

### Timeout
- fly.io tiene 60s timeout por defecto en HTTP
- Para análisis largos: configurar `[http_service.concurrency]` y aumentar timeout en fly.toml:
  ```toml
  [http_service]
    internal_port = 8080
    force_https = true
    [http_service.machine_checks]
      grace_period = "180s"
  ```
- Alternativa: hacer el pipeline async y devolver un job_id que se consulta después

### Coste excesivo
- Verificar que Haiku se usa para extracción (no Sonnet)
- Reducir max_tokens si outputs son muy largos
- El evaluador debe detectar si el coste se dispara y parar
