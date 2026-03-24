"""Rate limiting + HTTP client singleton — recursos compartidos globales."""
import asyncio
import httpx

semaforo_opus = asyncio.Semaphore(1)       # Director Opus: $0.40/llamada, max 1 concurrente
semaforo_metacog = asyncio.Semaphore(1)    # Metacognitivo: $0.50/llamada, max 1 concurrente
semaforo_motor = asyncio.Semaphore(2)      # Motor pipeline, max 2 concurrentes

# Singleton httpx client — reutilizar conexiones TCP, timeout estándar
_http_client = None  # httpx.AsyncClient singleton


def get_http_client() -> httpx.AsyncClient:
    """Devuelve singleton httpx client con timeout y retry."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        )
    return _http_client


async def close_http_client():
    """Cierra el client al shutdown."""
    global _http_client
    if _http_client and not _http_client.is_closed:
        await _http_client.aclose()
        _http_client = None
