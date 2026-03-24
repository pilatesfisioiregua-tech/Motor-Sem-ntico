"""Tests E2E del pipeline completo — mock + live."""
import json
import os
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.main import MotorRequest, MotorConfig


# ---------------------------------------------------------------------------
# Mock LLM helpers
# ---------------------------------------------------------------------------

MOCK_ROUTER_RESPONSE = json.dumps({
    "inteligencias": ["INT-01", "INT-08", "INT-16", "INT-07", "INT-05"],
    "razon": "Selección de test",
    "pares_complementarios": [["INT-01", "INT-08"]],
    "descartadas": ["INT-03"],
})

MOCK_ANALYSIS_RESPONSE = json.dumps({
    "firma_caso": "Análisis mock del caso",
    "hallazgos": ["hallazgo mock 1", "hallazgo mock 2"],
    "puntos_ciegos": ["punto ciego mock"],
    "accion_prioritaria": "acción mock prioritaria",
    "confianza": 0.8,
})

MOCK_INTEGRATION_RESPONSE = json.dumps({
    "narrativa": "Narrativa de síntesis de test",
    "hallazgos": ["hallazgo integrado 1", "hallazgo integrado 2"],
    "firma_combinada": "Firma combinada de test",
    "puntos_ciegos": ["punto ciego integrado"],
    "acciones": [{"accion": "acción test", "prioridad": 1, "coste": "bajo", "riesgo": "bajo"}],
    "contradicciones": ["contradicción de test"],
})


def _make_mock_llm():
    """Crea un mock LLM que retorna respuestas diferentes según la llamada."""
    mock = MagicMock()
    mock.reset_cost = MagicMock()
    mock.total_cost = 0.05

    call_count = 0

    async def mock_complete(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MOCK_ROUTER_RESPONSE
        system = kwargs.get('system', '')
        if 'integrador' in system.lower() or 'sintetizar' in system.lower():
            return MOCK_INTEGRATION_RESPONSE
        return MOCK_ANALYSIS_RESPONSE

    mock.complete = AsyncMock(side_effect=mock_complete)
    return mock


# ---------------------------------------------------------------------------
# TEST MOCK — no requiere servidor ni API keys
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pipeline_e2e_mock():
    """Pipeline completo con LLM mockeado."""
    mock_llm = _make_mock_llm()

    with patch('src.utils.llm_client.llm', mock_llm), \
         patch('src.pipeline.orchestrator.llm', mock_llm), \
         patch('src.pipeline.ejecutor.llm', mock_llm), \
         patch('src.pipeline.integrador.llm', mock_llm):

        from src.pipeline.orchestrator import run_pipeline

        request = MotorRequest(
            input="Mi socio quiere vender su parte y no sé si puedo comprársela",
            contexto="Empresa tech, 5 años, facturación 2M€",
            config=MotorConfig(modo="analisis"),
        )

        result = await run_pipeline(request)

    assert 'algoritmo_usado' in result
    assert 'resultado' in result
    assert 'meta' in result

    algo = result['algoritmo_usado']
    assert len(algo['inteligencias']) >= 3
    assert len(algo['operaciones']) > 0

    res = result['resultado']
    assert res['narrativa']
    assert 'hallazgos' in res
    assert 'firma_combinada' in res
    assert 'acciones' in res

    meta = result['meta']
    assert isinstance(meta['score_calidad'], float)
    assert meta['errors'] == [] or isinstance(meta['errors'], list)

    assert mock_llm.complete.call_count >= 3
    mock_llm.reset_cost.assert_called_once()

    print(f"\n✅ Pipeline E2E mock OK")
    print(f"   Inteligencias: {algo['inteligencias']}")
    print(f"   Operaciones: {len(algo['operaciones'])}")
    print(f"   Score: {meta['score_calidad']}")
    print(f"   LLM calls: {mock_llm.complete.call_count}")
    print(f"   Errors: {meta['errors']}")


# ---------------------------------------------------------------------------
# TESTS LIVE — requieren servidor corriendo en BASE_URL
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")


async def _server_reachable() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BASE_URL}/health")
            return r.status_code == 200
    except Exception:
        return False


def _skip_if_no_server():
    """Marca para saltar tests live si el servidor no está disponible.
    Requiere MOTOR_E2E=true para activar (evita fallos en CI).
    """
    if os.getenv("MOTOR_E2E", "").lower() != "true":
        return pytest.mark.skip(reason="Set MOTOR_E2E=true para ejecutar tests live")
    import asyncio
    loop = asyncio.new_event_loop()
    reachable = loop.run_until_complete(_server_reachable())
    loop.close()
    return pytest.mark.skipif(not reachable, reason=f"Servidor no disponible en {BASE_URL}")


live = _skip_if_no_server()


# --- Casos de cartografía ---

CASO_CLINICA = {
    "input": "Soy odontólogo, tengo una clínica dental con 3 sillones y solo uso 2. Facturo 180K€/año con 63% de margen. Estoy pensando en abrir una segunda sede porque siento que estoy estancado. Mi socio (que es mi cuñado) no quiere invertir más. Tengo un préstamo de 45K€ pendiente.",
    "config": {"modo": "analisis", "profundidad": "normal"},
}

CASO_SAAS = {
    "input": "Soy CTO y cofundador de una startup SaaS B2B con 18 meses de runway. Tenemos 47 bugs críticos acumulados, 23% de churn mensual, y mi cofundador (CEO) quiere pivotar a enterprise. Yo creo que deberíamos arreglar el producto primero. Llevamos 3 meses sin hablar del tema real. El equipo son 8 personas y 2 están pensando en irse.",
    "config": {"modo": "analisis", "profundidad": "normal"},
}

CASO_CARRERA = {
    "input": "Soy abogada corporativa, 12 años en un despacho grande, gano 125K€/año. Estoy considerando dejar el derecho corporativo para trabajar en una ONG medioambiental. Mi pareja depende parcialmente de mis ingresos. Tengo hipoteca de 280K€ y 2 hijos pequeños. Siento que no estoy haciendo lo que importa pero me aterroriza el salto.",
    "config": {"modo": "analisis", "profundidad": "normal"},
}


def _assert_response_structure(data: dict):
    """Verificaciones comunes para cualquier response del motor."""
    assert "algoritmo_usado" in data
    assert "resultado" in data
    assert "meta" in data

    intels = data["algoritmo_usado"]["inteligencias"]
    assert 3 <= len(intels) <= 6, f"Inteligencias fuera de rango: {len(intels)}"
    # Núcleo irreducible
    assert any(i in intels for i in ["INT-01", "INT-02"]), "Falta cuantitativa"
    assert any(i in intels for i in ["INT-08", "INT-17"]), "Falta humana"

    resultado = data["resultado"]
    assert resultado.get("narrativa") or resultado.get("hallazgos"), "Sin narrativa ni hallazgos"

    meta = data["meta"]
    assert meta["coste"] < 1.50, f"Coste {meta['coste']} > $1.50"
    assert meta["score_calidad"] >= 0


@live
@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


@live
@pytest.mark.asyncio
async def test_clinica_dental():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_CLINICA)
        assert r.status_code == 200
        data = r.json()
        _assert_response_structure(data)

        print(f"\n=== CLÍNICA DENTAL ===")
        print(f"Inteligencias: {data['algoritmo_usado']['inteligencias']}")
        print(f"Coste: ${data['meta']['coste']:.4f}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")
        print(f"Score: {data['meta']['score_calidad']}")


@live
@pytest.mark.asyncio
async def test_saas_startup():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_SAAS)
        assert r.status_code == 200
        data = r.json()
        _assert_response_structure(data)

        print(f"\n=== SAAS STARTUP ===")
        print(f"Inteligencias: {data['algoritmo_usado']['inteligencias']}")
        print(f"Coste: ${data['meta']['coste']:.4f}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")
        print(f"Score: {data['meta']['score_calidad']}")


@live
@pytest.mark.asyncio
async def test_cambio_carrera():
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json=CASO_CARRERA)
        assert r.status_code == 200
        data = r.json()
        _assert_response_structure(data)

        print(f"\n=== CAMBIO CARRERA ===")
        print(f"Inteligencias: {data['algoritmo_usado']['inteligencias']}")
        print(f"Coste: ${data['meta']['coste']:.4f}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")
        print(f"Score: {data['meta']['score_calidad']}")


@live
@pytest.mark.asyncio
async def test_modo_conversacion():
    """Modo conversación: más rápido, menos inteligencias."""
    async with httpx.AsyncClient(timeout=90) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json={
            "input": "¿Debería subir precios un 15%?",
            "config": {"modo": "conversacion"},
        })
        assert r.status_code == 200
        data = r.json()
        intels = data["algoritmo_usado"]["inteligencias"]
        assert len(intels) <= 4, f"Conversación debería usar ≤4 inteligencias, usó {len(intels)}"

        print(f"\n=== CONVERSACIÓN ===")
        print(f"Inteligencias: {intels}")
        print(f"Tiempo: {data['meta']['tiempo_s']:.1f}s")


@live
@pytest.mark.asyncio
async def test_modo_confrontacion():
    """Modo confrontación: incluye existenciales."""
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{BASE_URL}/motor/ejecutar", json={
            "input": "Llevo 15 años en este trabajo y no sé si tiene sentido seguir",
            "config": {"modo": "confrontacion"},
        })
        assert r.status_code == 200
        data = r.json()
        intels = data["algoritmo_usado"]["inteligencias"]
        assert any(i in intels for i in ["INT-17", "INT-18"]), "Confrontación debe incluir existenciales"

        print(f"\n=== CONFRONTACIÓN ===")
        print(f"Inteligencias: {intels}")
        print(f"Score: {data['meta']['score_calidad']}")
