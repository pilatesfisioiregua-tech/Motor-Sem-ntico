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
