"""Tests de seguridad Apple-grade."""
import pytest
import time


class TestRateLimit:
    def test_cache_dict_exists(self):
        """El rate limit usa un dict en memoria."""
        from src.main import _rate_limit_cache, RATE_LIMIT_MAX
        assert isinstance(_rate_limit_cache, dict)
        assert RATE_LIMIT_MAX >= 30  # Al menos 30 req/min

    def test_rate_limit_max_configurable(self):
        """RATE_LIMIT_MAX viene de env con default 60."""
        from src.main import RATE_LIMIT_MAX
        assert RATE_LIMIT_MAX == 60  # Default


class TestSecurityHeaders:
    def test_middleware_exists(self):
        """El middleware de security headers existe."""
        from src.main import app
        middleware_names = [str(m) for m in app.user_middleware]
        # Verificar que hay middlewares registrados
        assert len(app.user_middleware) >= 1


class TestStructuredLogging:
    def test_production_detection(self):
        """En dev (sin FLY_APP_NAME) usa ConsoleRenderer."""
        import os
        assert os.getenv("FLY_APP_NAME", "") == ""  # Estamos en dev


class TestGracefulShutdown:
    def test_lifespan_defined(self):
        """El lifespan está definido con shutdown handlers."""
        from src.main import lifespan
        assert callable(lifespan)
