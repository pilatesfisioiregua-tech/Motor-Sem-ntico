# B-ORG-F6 — Fase 6: Producción + Redsys + Multi-tenant + CI/CD

**Fecha:** 24 marzo 2026
**Estimación:** ~12h
**Prerequisito:** B-ORG-F2 (pizarra dominio), B-ORG-PRODUCCION (auth). F4/F5 no requeridos.
**WIP:** 2 (tests + CI/CD son paralelos con Redsys/multi-tenant)
**Principios:** P30 (come tu comida primero), P64 (multi-tenant = fila en pizarra dominio)

---

## OBJETIVO

De "prototipo que funciona" a "producto que aguanta". Tests, CI/CD, observabilidad, Redsys sandbox verificado, y segundo tenant (clínica fisio de la mujer de Jesús) con CERO cambio de código.

---

## ESTADO ACTUAL

- **Redsys:** `redsys_pagos.py` + `redsys_router.py` escritos. Migration 020. Ficha técnica lista (email: pilatesfisioiregua@gmail.com, tel: 607466631). **Esperando credenciales sandbox de Caja Rural.**
- **Tests:** 16 tests para pipeline/tcf. **CERO tests para pilates/** (~70% del código en producción).
- **CI/CD:** No existe. Deploy manual via `fly deploy`.
- **Observabilidad:** structlog. Sin Sentry, sin correlation ID, sin alertas.
- **Multi-tenant:** TENANT hardcoded en ~47 archivos. Pizarra dominio creada en F2 con seed.
- **Backups:** Fly.io Postgres tiene backups automáticos. Sin verificación, sin runbook.

---

## ARCHIVOS A LEER ANTES DE EMPEZAR

```
src/pilates/redsys_pagos.py        ← Integración Redsys completa
src/pilates/redsys_router.py       ← 4 endpoints webhooks
src/pilates/router.py              ← ~111 endpoints CRUD
src/main.py                        ← Auth middleware, routers
src/pilates/pizarras.py            ← Helper pizarras (F2)
tests/                             ← 16 tests existentes (pipeline)
requirements.txt                   ← Dependencias actuales
Dockerfile                         ← Build actual
fly.toml                           ← Config fly.io
```

---

## PASO 0: TESTS PILATES — Capa 1: Unitarios sin DB (~3h)

Crear directorio `tests/pilates/` y archivos de test:

### 0.1 tests/pilates/conftest.py

```python
"""Fixtures compartidos para tests de pilates."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_pool():
    """Mock del pool de DB."""
    pool = AsyncMock()
    conn = AsyncMock()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)
    return pool, conn


@pytest.fixture
def mock_get_pool(mock_pool):
    """Parchea get_pool para no necesitar DB real."""
    pool, conn = mock_pool
    with patch("src.db.client.get_pool", return_value=pool):
        yield pool, conn
```

### 0.2 tests/pilates/test_json_utils.py

```python
"""Tests json_utils — extracción JSON robusta."""
import pytest
from src.pilates.json_utils import extraer_json, extraer_json_lista


class TestExtraerJson:
    def test_json_directo(self):
        assert extraer_json('{"a": 1}') == {"a": 1}

    def test_json_markdown(self):
        assert extraer_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_json_con_texto(self):
        result = extraer_json('Aquí va: {"a": 1} y más texto')
        assert result == {"a": 1}

    def test_fallback(self):
        assert extraer_json("no json here", fallback={"x": 0}) == {"x": 0}

    def test_vacio(self):
        assert extraer_json("", fallback={}) == {}

    def test_array(self):
        result = extraer_json('[1, 2, 3]')
        assert result == {"items": [1, 2, 3]}


class TestExtraerJsonLista:
    def test_lista_directa(self):
        assert extraer_json_lista('[1, 2]') == [1, 2]

    def test_sin_lista(self):
        assert extraer_json_lista("nada") == []
```

### 0.3 tests/pilates/test_redsys.py

```python
"""Tests redsys_pagos — firma HMAC SHA-256 y generación de pedidos."""
import base64
import json
import pytest
from src.pilates.redsys_pagos import (
    _encode_params, _decode_params, _generate_order,
    _sign, _decode_key, _encrypt_order,
)


class TestRedsysParams:
    def test_encode_decode_roundtrip(self):
        params = {"Ds_Merchant_Amount": "5500", "Ds_Merchant_Currency": "978"}
        encoded = _encode_params(params)
        decoded = _decode_params(encoded)
        assert decoded == params

    def test_generate_order_format(self):
        order = _generate_order()
        assert len(order) == 12
        assert order[:4].isdigit()

    def test_generate_order_unique(self):
        orders = {_generate_order() for _ in range(100)}
        assert len(orders) >= 95  # Al menos 95% únicos


class TestRedsysFirma:
    """Tests de firma con clave ficticia."""

    @pytest.fixture
    def fake_key_b64(self):
        # Clave de 24 bytes en base64 (3DES necesita 24 bytes)
        return base64.b64encode(b"0123456789ABCDEF01234567").decode()

    def test_encrypt_order_deterministic(self, fake_key_b64):
        key = _decode_key(fake_key_b64)
        result1 = _encrypt_order("1234", key)
        result2 = _encrypt_order("1234", key)
        assert result1 == result2

    def test_sign_deterministic(self, fake_key_b64, monkeypatch):
        monkeypatch.setattr("src.pilates.redsys_pagos.SECRET_KEY", fake_key_b64)
        params_b64 = _encode_params({"Ds_Merchant_Amount": "5500"})
        sig1 = _sign(params_b64, "000012340001")
        sig2 = _sign(params_b64, "000012340001")
        assert sig1 == sig2

    def test_sign_different_orders(self, fake_key_b64, monkeypatch):
        monkeypatch.setattr("src.pilates.redsys_pagos.SECRET_KEY", fake_key_b64)
        params_b64 = _encode_params({"Ds_Merchant_Amount": "5500"})
        sig1 = _sign(params_b64, "000012340001")
        sig2 = _sign(params_b64, "000012340002")
        assert sig1 != sig2
```

### 0.4 tests/pilates/test_verificar.py

```python
"""Tests motor/verificar.py — verificación post-output."""
import pytest
from src.motor.verificar import verificar, ResultadoVerificacion


class TestVerificar:
    def test_output_normal(self):
        r = verificar("Este es un texto normal de análisis suficientemente largo para pasar.")
        assert r.ok
        assert r.score >= 0.8

    def test_output_vacio(self):
        r = verificar("")
        assert not r.ok
        assert r.score == 0.0

    def test_output_generico(self):
        r = verificar("Como asistente de IA, es importante considerar muchos factores.")
        assert len(r.warnings) > 0
        assert r.score < 1.0

    def test_f3_no_sugiere_adicion(self):
        r = verificar("Deberíamos añadir un nuevo servicio premium.", funcion="F3")
        assert any("F3" in w for w in r.warnings)

    def test_json_malformado(self):
        r = verificar('{"key": value_sin_comillas}')
        # Debería detectar JSON malformado
        assert r.score < 1.0
```

### 0.5 tests/pilates/test_pizarras.py

```python
"""Tests pizarras.py — lectura con fallback."""
import pytest
from src.pilates.pizarras import leer_dominio, leer_modelo, DEFAULT_DOMINIO


class TestPizarraFallbacks:
    """Testa que los fallbacks funcionan sin DB."""

    @pytest.mark.asyncio
    async def test_dominio_fallback_sin_db(self):
        """Sin DB, devuelve DEFAULT_DOMINIO."""
        result = await leer_dominio("tenant_inexistente")
        assert result["tenant_id"] == DEFAULT_DOMINIO["tenant_id"]

    @pytest.mark.asyncio
    async def test_modelo_fallback_sin_db(self):
        """Sin DB, devuelve modelo por defecto según complejidad."""
        result = await leer_modelo("x", "F1", None, "baja")
        assert result == "deepseek/deepseek-v3.2"

    @pytest.mark.asyncio
    async def test_modelo_fallback_alta(self):
        result = await leer_modelo("x", "F1", None, "alta")
        assert "opus" in result.lower() or "claude" in result.lower()
```

**Test 0.1:** `cd motor-semantico && python -m pytest tests/pilates/ -v` → todos PASS

---

## PASO 1: TESTS PILATES — Capa 2: Integración con DB mock (~2h)

### 1.1 tests/pilates/test_automatismos.py

```python
"""Tests automatismos.py — con DB mock."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from uuid import uuid4


class TestFelicitarCumpleanos:
    @pytest.mark.asyncio
    async def test_sin_cumples_hoy(self, mock_get_pool):
        pool, conn = mock_get_pool
        conn.fetch.return_value = []  # Sin cumpleaños

        from src.pilates.automatismos import felicitar_cumpleanos
        result = await felicitar_cumpleanos()
        assert result["cumpleanos_hoy"] == 0


class TestConciliarBizum:
    @pytest.mark.asyncio
    async def test_cliente_no_encontrado(self, mock_get_pool):
        pool, conn = mock_get_pool
        conn.fetchrow.return_value = None  # No existe

        from src.pilates.automatismos import conciliar_bizum_entrante
        result = await conciliar_bizum_entrante("666999000", 55.0)
        assert result["status"] == "error"
```

### 1.2 tests/pilates/test_whatsapp.py

```python
"""Tests whatsapp.py — clasificación de intención."""
from src.pilates.whatsapp import _clasificar_intencion


class TestClasificarIntencion:
    def test_precio(self):
        assert _clasificar_intencion("cuanto cuesta una clase?", "34666", None) == "consulta_precio"

    def test_horario(self):
        assert _clasificar_intencion("que horarios teneis?", "34666", None) == "consulta_horario"

    def test_reserva(self):
        assert _clasificar_intencion("quiero reservar clase", "34666", None) == "reserva"

    def test_cancelacion(self):
        assert _clasificar_intencion("no puedo ir mañana", "34666", None) == "cancelacion"

    def test_queja(self):
        assert _clasificar_intencion("tengo un problema con el cobro", "34666", None) == "queja"

    def test_feedback(self):
        assert _clasificar_intencion("genial la clase de hoy!", "34666", None) == "feedback"

    def test_otro(self):
        assert _clasificar_intencion("hola que tal", "34666", None) == "otro"

    def test_boton_confirmar(self):
        assert _clasificar_intencion("si_voy", "34666", None) == "reserva"
```

**Test 1.1:** `python -m pytest tests/pilates/ -v` → todos PASS (~20 tests)

---

## PASO 2: CI/CD — GitHub Actions (~1h)

Crear: `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
    paths: ['motor-semantico/**']
  pull_request:
    branches: [main]
    paths: ['motor-semantico/**']

jobs:
  test-backend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: motor-semantico

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
          cache-dependency-path: motor-semantico/requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests (sin DB)
        run: python -m pytest tests/ -v --tb=short -x
        env:
          OPENROUTER_API_KEY: ""
          DATABASE_URL: ""

  test-frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: motor-semantico/frontend

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: motor-semantico/frontend/package-lock.json

      - name: Install & build
        run: |
          npm ci
          npm run build

  deploy:
    needs: [test-backend, test-frontend]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    defaults:
      run:
        working-directory: motor-semantico

    steps:
      - uses: actions/checkout@v4
        with:
          submodules: true

      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only -a motor-semantico-omni
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Nota:** Jesús necesita añadir `FLY_API_TOKEN` en GitHub repo Settings → Secrets. Se obtiene con:
```bash
fly tokens create deploy -x 999999h -a motor-semantico-omni
```

**Test 2.1:** Push a main → GitHub Actions ejecuta tests + build + deploy
**Test 2.2:** PR → Tests corren, deploy NO se ejecuta

---

## PASO 3: OBSERVABILIDAD — Correlation ID + alertas (~2h)

### 3.1 Correlation ID middleware (src/main.py)

Después del auth middleware, añadir:

```python
import uuid as _uuid

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Añade correlation ID a cada request para trazabilidad."""
    correlation_id = request.headers.get("X-Correlation-ID", str(_uuid.uuid4())[:8])
    request.state.correlation_id = correlation_id

    # Inyectar en structlog para que todos los logs lo incluyan
    import structlog
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

**Requisito:** Añadir `structlog[contextvars]` o verificar que structlog ya soporta contextvars (v24+ sí).

### 3.2 Alertas cron → pizarra comunicación → WA

En vez de Sentry (coste extra), usar el sistema propio. En `_tarea_diaria()` y `_tarea_semanal()`, si hay errores críticos:

```python
# Al final de _tarea_diaria(), si hubo errores:
errores_criticos = []  # Recopilar errores durante la tarea
if errores_criticos:
    try:
        import os
        from src.db.client import get_pool
        pool = await get_pool()
        telefono_jesus = os.getenv("JESUS_TELEFONO", "")
        if telefono_jesus:
            async with pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO om_pizarra_comunicacion
                        (tenant_id, destinatario, canal, tipo, mensaje,
                         programado_para, estado, origen)
                    VALUES ('authentic_pilates', $1, 'whatsapp', 'alerta_sistema',
                            $2, now(), 'pendiente', 'CRON')
                """, telefono_jesus,
                    f"⚠️ Errores cron: {', '.join(errores_criticos[:3])}")
    except Exception:
        pass
```

### 3.3 Endpoint de diagnóstico del sistema

Añadir en `router.py`:

```python
@router.get("/sistema/diagnostico")
async def diagnostico_sistema():
    """Diagnóstico completo del sistema — para Jesús en Modo Profundo."""
    from src.db.client import get_pool
    from src.motor.pensar import presupuesto_restante, _presupuesto_ciclo

    pool = await get_pool()
    checks = {}

    async with pool.acquire() as conn:
        # Tablas
        checks["tablas_om"] = await conn.fetchval(
            "SELECT count(*) FROM pg_tables WHERE tablename LIKE 'om_%'")

        # Tamaño DB
        checks["db_size_mb"] = await conn.fetchval(
            "SELECT pg_database_size(current_database()) / 1024 / 1024")

        # Cron state
        cron_rows = await conn.fetch(
            "SELECT tarea, ultima_ejecucion, resultado FROM om_cron_state ORDER BY ultima_ejecucion DESC")
        checks["cron"] = [dict(r) for r in cron_rows]

        # Motor LLM
        checks["motor"] = {
            "presupuesto_restante": presupuesto_restante(),
            "gastado_ciclo": _presupuesto_ciclo,
        }

        # Caché
        try:
            cache = await conn.fetchrow("""
                SELECT count(*) as entradas, SUM(hits) as total_hits
                FROM om_pizarra_cache_llm WHERE tenant_id='authentic_pilates'
            """)
            checks["cache_llm"] = dict(cache) if cache else {}
        except Exception:
            checks["cache_llm"] = "tabla_no_existe"

        # Pizarras
        for tabla in ["om_pizarra_dominio", "om_pizarra_cognitiva", "om_pizarra_temporal",
                      "om_pizarra_modelos", "om_pizarra_evolucion", "om_pizarra_interfaz"]:
            try:
                count = await conn.fetchval(f"SELECT count(*) FROM {tabla}")
                checks[f"pizarra_{tabla[13:]}"] = count
            except Exception:
                checks[f"pizarra_{tabla[13:]}"] = "no_existe"

        # Señales bus
        try:
            checks["bus_pendientes"] = await conn.fetchval(
                "SELECT count(*) FROM om_senales_agentes WHERE procesada=false AND tenant_id='authentic_pilates'")
        except Exception:
            checks["bus_pendientes"] = "tabla_no_existe"

    return {"timestamp": str(datetime.now()), "checks": checks}
```

**Test 3.1:** Logs incluyen `correlation_id` en cada línea
**Test 3.2:** `curl /pilates/sistema/diagnostico` → JSON con todas las métricas

---

## PASO 4: MULTI-TENANT — Segundo tenant clínica fisio (~3h)

### 4.1 Migration (031_multi_tenant.sql)

```sql
-- 031_multi_tenant.sql — Segundo tenant: clínica fisioterapia

-- 1. Insertar tenant en pizarra dominio
INSERT INTO om_pizarra_dominio (tenant_id, nombre, config)
VALUES ('clinica_fisio', 'Clínica Fisioterapia', '{
    "timezone": "Europe/Madrid",
    "moneda": "EUR",
    "datos_clinicos": true,
    "funciones_activas": ["F1","F2","F3","F4","F5","F6","F7"],
    "idioma": "es",
    "ubicacion": "Logroño, La Rioja",
    "rgpd_art9": true,
    "datos_clinicos_encriptados": true
}')
ON CONFLICT (tenant_id) DO NOTHING;

-- 2. Seeds modelos para fisio (mismos defaults)
INSERT INTO om_pizarra_modelos (tenant_id, funcion, complejidad, modelo, origen)
SELECT 'clinica_fisio', funcion, complejidad, modelo, 'default'
FROM om_pizarra_modelos
WHERE tenant_id = 'authentic_pilates' AND origen = 'default'
ON CONFLICT DO NOTHING;

-- 3. Cron state para fisio
INSERT INTO om_cron_state (tenant_id, tarea, ultima_ejecucion, resultado)
VALUES ('clinica_fisio', 'diaria', now(), 'seed')
ON CONFLICT DO NOTHING;

-- 4. Campo encriptación para datos clínicos RGPD Art.9
ALTER TABLE om_datos_clinicos
    ADD COLUMN IF NOT EXISTS datos_encriptados BYTEA,
    ADD COLUMN IF NOT EXISTS encryption_key_id TEXT;

-- 5. Tabla de claves de encriptación por tenant (para RGPD Art.9)
CREATE TABLE IF NOT EXISTS om_encryption_keys (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    key_encrypted BYTEA NOT NULL,
    algorithm TEXT DEFAULT 'AES-256-GCM',
    created_at TIMESTAMPTZ DEFAULT now(),
    revoked_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_enc_keys_tenant ON om_encryption_keys(tenant_id);
```

### 4.2 tenant_context.py — Extractor de tenant

Crear: `src/pilates/tenant_context.py`

```python
"""Tenant Context — extrae tenant_id del request o fallback.

Patrón de uso en endpoints:
    from src.pilates.tenant_context import get_tenant_id

    @router.get("/clientes")
    async def get_clientes(request: Request):
        tenant = get_tenant_id(request)
        ...

Para migración gradual de los 47 archivos con TENANT hardcoded.
"""
from __future__ import annotations

from fastapi import Request

DEFAULT_TENANT = "authentic_pilates"


def get_tenant_id(request: Request = None) -> str:
    """Extrae tenant_id del request state o header, con fallback."""
    if request:
        # 1. Intentar request.state (seteado por middleware)
        tenant = getattr(request.state, "tenant_id", None)
        if tenant:
            return tenant

        # 2. Intentar header X-Tenant-ID
        tenant = request.headers.get("X-Tenant-ID")
        if tenant:
            return tenant

    # 3. Fallback
    return DEFAULT_TENANT


def get_tenant_config(request: Request = None) -> dict:
    """Devuelve la config completa del tenant desde el request."""
    config = getattr(request.state, "tenant_config", None) if request else None
    return config or {"tenant_id": DEFAULT_TENANT, "nombre": "Authentic Pilates"}
```

### 4.3 Middleware tenant en main.py

Después del correlation_id middleware:

```python
@app.middleware("http")
async def tenant_middleware(request: Request, call_next):
    """Resuelve el tenant desde header o pizarra dominio."""
    tenant_id = request.headers.get("X-Tenant-ID", "authentic_pilates")

    # Validar que el tenant existe en pizarra dominio
    try:
        from src.pilates.pizarras import leer_dominio
        config = await leer_dominio(tenant_id)
        request.state.tenant_id = config["tenant_id"]
        request.state.tenant_config = config
    except Exception:
        request.state.tenant_id = "authentic_pilates"
        request.state.tenant_config = None

    return await call_next(request)
```

### 4.4 Migrar 5 archivos piloto

Cambiar TENANT hardcoded en 5 archivos clave:
- `src/pilates/briefing.py`
- `src/pilates/pizarras.py` (ya usa DEFAULT_TENANT como fallback)
- `src/pilates/bus.py`
- `src/pilates/automatismos.py`
- `src/pilates/whatsapp.py`

Patrón:
```python
# ANTES:
TENANT = "authentic_pilates"

# DESPUÉS:
from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request
```

En funciones que reciben request, usar `get_tenant_id(request)`. En funciones cron (sin request), mantener DEFAULT_TENANT.

**Nota:** Los otros ~42 archivos se migran en un briefing dedicado B-ORG-TENANT. Este paso demuestra el patrón.

**Test 4.1:** `SELECT count(*) FROM om_pizarra_dominio` → 2 (authentic_pilates + clinica_fisio)
**Test 4.2:** `curl -H "X-Tenant-ID: clinica_fisio" /pilates/pizarra/dominio` → config fisio
**Test 4.3:** `curl /pilates/pizarra/dominio` → config authentic_pilates (default)

---

## PASO 5: API DOCUMENTADA (~1h)

### 5.1 Tags y descripciones en routers

En `router.py`, al inicio:

```python
router = APIRouter(
    prefix="/pilates",
    tags=["pilates"],
    responses={401: {"description": "API key requerida"}},
)
```

Pero mejor: split en múltiples tags. En `main.py`, antes de montar los routers:

```python
app.openapi_tags = [
    {"name": "clientes", "description": "Gestión de clientes"},
    {"name": "sesiones", "description": "Sesiones, asistencias, calendario"},
    {"name": "pagos", "description": "Pagos, cargos, facturación, Redsys"},
    {"name": "voz", "description": "Bloque Voz: estrategia, propuestas, ISP"},
    {"name": "organismo", "description": "Pizarras, bus, director, agentes"},
    {"name": "sistema", "description": "Health, diagnóstico, cron, backups"},
    {"name": "motor", "description": "Motor semántico, telemetría, caché"},
    {"name": "redsys", "description": "Webhooks Redsys (público)"},
    {"name": "portal", "description": "Portal cliente (público)"},
]
```

### 5.2 Habilitar docs en producción (protegido por auth)

Cambiar en main.py:

```python
_docs_enabled = os.getenv("ENABLE_DOCS", "true").lower() == "true"
```

Los docs están protegidos por el auth middleware (requieren X-API-Key), así que es seguro habilitarlos.

**Test 5.1:** `curl /docs -H "X-API-Key: $KEY"` → Swagger UI
**Test 5.2:** `curl /docs` (sin key) → 401

---

## PASO 6: VERIFICAR REDSYS SANDBOX (~1h cuando lleguen credenciales)

Cuando Caja Rural proporcione las credenciales sandbox:

```bash
fly secrets set REDSYS_MERCHANT_CODE="XXXXXXXXX" -a motor-semantico-omni
fly secrets set REDSYS_TERMINAL="001" -a motor-semantico-omni
fly secrets set REDSYS_SECRET_KEY="BASE64_KEY_HERE" -a motor-semantico-omni
fly secrets set REDSYS_ENVIRONMENT="test" -a motor-semantico-omni
```

Luego 3 tests obligatorios:
1. **Pago estándar:** Crear pago → redirigir → completar con tarjeta test → verificar notificación
2. **COF inicial:** Pago con `Ds_Merchant_Identifier=REQUIRED` → verificar token devuelto
3. **Cobro recurrente:** Usar token → POST REST → verificar respuesta ok

**Test 6.1:** `curl /health` → `checks.redsys: "configured"` (is_configured() = true)
**Test 6.2:** Pago test sandbox → notificación recibida → pedido actualizado en DB

**Este paso se BLOQUEA hasta recibir credenciales. El código ya está listo.**

---

## PASO 7: BACKUPS VERIFICADOS (~1h)

### 7.1 Verificar backups automáticos de Fly.io Postgres

```bash
fly postgres backups list -a chief-os-omni
```

### 7.2 Crear script de verificación

Crear: `scripts/verify_backup.sh`

```bash
#!/bin/bash
# Verificar que los backups de Fly.io Postgres funcionan
echo "=== Verificación de backups ==="
echo "1. Listando backups disponibles..."
fly postgres backups list -a chief-os-omni

echo ""
echo "2. Verificando última backup..."
fly postgres backups list -a chief-os-omni | head -3

echo ""
echo "3. Contando tablas om_*..."
fly postgres connect -a chief-os-omni -c "SELECT count(*) as tablas FROM pg_tables WHERE tablename LIKE 'om_%'"

echo ""
echo "4. Contando clientes activos..."
fly postgres connect -a chief-os-omni -c "SELECT count(*) FROM om_cliente_tenant WHERE estado='activo'"

echo ""
echo "=== Backup verificado ==="
```

### 7.3 Runbook de disaster recovery

Crear: `docs/operativo/RUNBOOK_DISASTER_RECOVERY.md`

```markdown
# Runbook: Disaster Recovery

## Restaurar desde backup

1. Listar backups: `fly postgres backups list -a chief-os-omni`
2. Restaurar: `fly postgres backups restore <timestamp> -a chief-os-omni`
3. Verificar: `fly postgres connect -a chief-os-omni -c "SELECT count(*) FROM om_clientes"`
4. Re-deploy app: `fly deploy -a motor-semantico-omni`

## Contactos

- Jesús: 607466631
- Fly.io status: https://status.fly.io

## Verificación mensual

Ejecutar: `scripts/verify_backup.sh`
Registrar resultado en om_cron_state con tarea='backup_verificado'.
```

**Test 7.1:** `fly postgres backups list` → al menos 1 backup reciente

---

## RESUMEN DE CAMBIOS

| Archivo | Cambio | Paso |
|---------|--------|------|
| `tests/pilates/conftest.py` | **NUEVO** — fixtures DB mock | 0 |
| `tests/pilates/test_json_utils.py` | **NUEVO** — 8 tests | 0 |
| `tests/pilates/test_redsys.py` | **NUEVO** — 5 tests firma | 0 |
| `tests/pilates/test_verificar.py` | **NUEVO** — 5 tests | 0 |
| `tests/pilates/test_pizarras.py` | **NUEVO** — 3 tests fallback | 0 |
| `tests/pilates/test_automatismos.py` | **NUEVO** — 2 tests | 1 |
| `tests/pilates/test_whatsapp.py` | **NUEVO** — 8 tests intención | 1 |
| `.github/workflows/ci.yml` | **NUEVO** — CI/CD con deploy | 2 |
| `src/main.py` | +correlation_id + tenant middleware + API tags + docs enabled | 3, 4, 5 |
| `migrations/031_multi_tenant.sql` | **NUEVO** — segundo tenant + encriptación | 4 |
| `src/pilates/tenant_context.py` | **NUEVO** — extractor tenant | 4 |
| 5 archivos piloto | TENANT hardcoded → tenant_context | 4 |
| `src/pilates/router.py` | +endpoint diagnóstico sistema | 3 |
| `scripts/verify_backup.sh` | **NUEVO** — verificación backups | 7 |
| `docs/operativo/RUNBOOK_DISASTER_RECOVERY.md` | **NUEVO** | 7 |

## TESTS FINALES (PASS/FAIL)

```
T1:  python -m pytest tests/pilates/ -v → todos PASS (~31 tests)                    [PASS/FAIL]
T2:  python -m pytest tests/ -v → todos PASS (pilates + pipeline)                   [PASS/FAIL]
T3:  npm run build (frontend) → sin errores                                          [PASS/FAIL]
T4:  SELECT count(*) FROM om_pizarra_dominio → 2 (pilates + fisio)                  [PASS/FAIL]
T5:  curl -H "X-Tenant-ID: clinica_fisio" /pilates/pizarra/dominio → config fisio   [PASS/FAIL]
T6:  curl /pilates/sistema/diagnostico → JSON con checks                             [PASS/FAIL]
T7:  Logs tienen correlation_id                                                      [PASS/FAIL]
T8:  curl /docs con API key → Swagger UI                                             [PASS/FAIL]
T9:  .github/workflows/ci.yml existe                                                 [PASS/FAIL]
T10: fly postgres backups list → al menos 1 backup                                   [PASS/FAIL]
```

## ORDEN DE EJECUCIÓN

1. Crear directorio `tests/pilates/` + todos los tests (Pasos 0, 1)
2. Crear `.github/workflows/ci.yml` (Paso 2)
3. Crear `migrations/031_multi_tenant.sql` (Paso 4)
4. Crear `src/pilates/tenant_context.py` (Paso 4)
5. Editar `src/main.py` — correlation ID + tenant middleware + tags + docs (Pasos 3, 4, 5)
6. Editar 5 archivos piloto — TENANT → tenant_context (Paso 4)
7. Editar `src/pilates/router.py` — endpoint diagnóstico (Paso 3)
8. Crear scripts + runbook (Paso 7)
9. `python -m pytest tests/ -v` → todos PASS
10. Deploy
11. Setear FLY_API_TOKEN en GitHub Secrets
12. Verificar backups
13. **Cuando lleguen credenciales Caja Rural:** Paso 6

## NOTAS

- **Redsys:** El código EXISTE y está LISTO. Solo falta setear secrets cuando Caja Rural responda. La ficha técnica está lista para enviar (email: pilatesfisioiregua@gmail.com).
- **Sentry:** NO incluido. El sistema propio (pizarra comunicación + alertas WA) es suficiente para ~90 clientes. Sentry a considerar si se escala a 10+ tenants.
- **Multi-tenant clínica fisio:** La fila en pizarra dominio es el ÚNICO cambio. CERO código nuevo para añadir un tenant. Los 42 archivos restantes con TENANT hardcoded son un briefing separado (B-ORG-TENANT).
- **Tests sin DB:** Todos los tests de Paso 0 corren sin PostgreSQL. Los de Paso 1 usan mock. Ideal para CI.
- **RGPD Art.9 (datos sanitarios):** La tabla `om_encryption_keys` + campo `datos_encriptados` en `om_datos_clinicos` prepara la infraestructura. La implementación real de encriptación/desencriptación se hace cuando el tenant fisio esté activo.
