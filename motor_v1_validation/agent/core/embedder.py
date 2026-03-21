"""Embedding client — generates vector embeddings via OpenRouter (text-embedding-3-small).

Centralized, singleton, with retry + rate limiting + batch support.
Dimension: 768 (text-embedding-3-small with dimensions=768).

Usage:
    from core.embedder import get_embedder
    emb = get_embedder()
    vector = emb.embed_one("some text")
    vectors = emb.embed_batch(["text1", "text2", ...])
"""

import os
import time
import logging
import threading
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "openai/text-embedding-3-small"
EMBEDDING_DIMS = 768
MAX_BATCH_SIZE = 50          # safe batch size for OpenRouter
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5          # seconds, multiplied by attempt
RATE_LIMIT_RPM = 200         # requests per minute (conservative)
RATE_LIMIT_WINDOW = 60.0     # seconds


# ── Load env (same pattern as api.py) ─────────────────────────────────────

def _load_env() -> None:
    for env_path in [
        Path(__file__).parent.parent.parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"'))
            break

_load_env()


# ── Rate limiter ──────────────────────────────────────────────────────────

class _RateLimiter:
    """Simple sliding window rate limiter."""

    def __init__(self, max_calls: int, window_s: float):
        self._max = max_calls
        self._window = window_s
        self._calls: list[float] = []
        self._lock = threading.Lock()

    def wait(self):
        """Block until a request slot is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._calls = [t for t in self._calls if now - t < self._window]
                if len(self._calls) < self._max:
                    self._calls.append(now)
                    return
            time.sleep(0.1)


# ── Embedder ──────────────────────────────────────────────────────────────

class Embedder:
    """Generate embeddings via OpenRouter's embedding endpoint."""

    def __init__(self):
        self._client = None
        self._rate_limiter = _RateLimiter(RATE_LIMIT_RPM, RATE_LIMIT_WINDOW)
        self._total_tokens = 0
        self._total_calls = 0

    def _get_client(self):
        if self._client is None:
            import httpx
            self._client = httpx.Client(
                base_url="https://openrouter.ai/api/v1",
                timeout=httpx.Timeout(30.0, connect=10.0),
                limits=httpx.Limits(max_connections=5, max_keepalive_connections=3),
            )
        return self._client

    def _call_api(self, texts: list[str]) -> list[list[float]]:
        """Call OpenRouter embeddings endpoint with retry."""
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set")

        client = self._get_client()

        for attempt in range(MAX_RETRIES):
            self._rate_limiter.wait()

            try:
                resp = client.post(
                    "/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": EMBEDDING_MODEL,
                        "input": texts,
                        "dimensions": EMBEDDING_DIMS,
                    },
                )

                if resp.status_code == 429:
                    retry_after = float(resp.headers.get("retry-after", 5))
                    logger.warning(f"Rate limited, waiting {retry_after}s")
                    time.sleep(retry_after)
                    continue

                resp.raise_for_status()
                data = resp.json()

                # Track usage
                usage = data.get("usage", {})
                self._total_tokens += usage.get("total_tokens", 0)
                self._total_calls += 1

                # Extract embeddings, sorted by index
                embeddings = sorted(data["data"], key=lambda x: x["index"])
                vectors = [e["embedding"] for e in embeddings]

                # Verify dimensions
                if vectors and len(vectors[0]) != EMBEDDING_DIMS:
                    logger.warning(
                        f"Unexpected dims: got {len(vectors[0])}, expected {EMBEDDING_DIMS}"
                    )

                return vectors

            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait = RETRY_BACKOFF * (attempt + 1)
                logger.warning(f"Embed attempt {attempt+1} failed: {e}, retrying in {wait}s")
                time.sleep(wait)

        return []  # unreachable

    def embed_one(self, text: str) -> list[float]:
        """Embed a single text. Returns vector of EMBEDDING_DIMS floats."""
        if not text or not text.strip():
            return [0.0] * EMBEDDING_DIMS
        # Truncate to ~8000 chars (~2000 tokens) to stay within model limits
        truncated = text[:8000]
        results = self._call_api([truncated])
        return results[0] if results else [0.0] * EMBEDDING_DIMS

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts. Returns list of vectors.

        Handles batching internally — pass any number of texts.
        """
        if not texts:
            return []

        all_vectors = []
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            # Truncate each text
            batch = [t[:8000] if t else "" for t in batch]
            # Replace empty strings with a space (API requires non-empty)
            batch = [t if t.strip() else " " for t in batch]
            vectors = self._call_api(batch)
            all_vectors.extend(vectors)

        return all_vectors

    def get_stats(self) -> dict:
        """Return usage statistics."""
        return {
            "total_tokens": self._total_tokens,
            "total_calls": self._total_calls,
            "model": EMBEDDING_MODEL,
            "dims": EMBEDDING_DIMS,
            "estimated_cost_usd": self._total_tokens * 0.02 / 1_000_000,
        }

    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# ── Singleton ─────────────────────────────────────────────────────────────

_embedder: Optional[Embedder] = None

def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder
