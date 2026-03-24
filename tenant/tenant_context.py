"""Tenant context — aislamiento por tenant para todo el sistema.

Patron: context var que propaga tenant_id automaticamente.
Middleware para FastAPI que extrae tenant de header/JWT/path.

Principio: el codigo del organismo es IDENTICO entre tenants.
Lo que cambia son las pizarras (dominio, cognitiva, modelos, etc.).
"""
from __future__ import annotations

import contextvars
import functools
import structlog
from typing import Optional

log = structlog.get_logger()

# Context var global — disponible en todo el call stack async
_tenant_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "tenant_id", default="default"
)


def get_tenant_id() -> str:
    """Obtiene tenant_id del contexto actual."""
    return _tenant_var.get()


def set_tenant_id(tenant_id: str) -> contextvars.Token:
    """Establece tenant_id en el contexto actual. Devuelve token para reset."""
    return _tenant_var.set(tenant_id)


class TenantContext:
    """Context manager para ejecutar codigo bajo un tenant especifico.

    Uso:
        async with TenantContext("authentic_pilates"):
            resultado = await enjambre.ciclo()
            # Todo dentro usa tenant_id="authentic_pilates"
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._token: Optional[contextvars.Token] = None

    async def __aenter__(self):
        self._token = set_tenant_id(self.tenant_id)
        log.debug("tenant.context_enter", tenant=self.tenant_id)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            _tenant_var.reset(self._token)
        log.debug("tenant.context_exit", tenant=self.tenant_id)
        return False

    def __enter__(self):
        self._token = set_tenant_id(self.tenant_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token is not None:
            _tenant_var.reset(self._token)
        return False


def tenant_middleware(app):
    """Middleware FastAPI que extrae tenant_id del request.

    Busca en orden:
      1. Header X-Tenant-Id
      2. Path param tenant_id
      3. Query param tenant_id
      4. Default "default"
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class TenantMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # 1. Header
            tenant_id = request.headers.get("x-tenant-id")

            # 2. Path param
            if not tenant_id:
                tenant_id = request.path_params.get("tenant_id")

            # 3. Query param
            if not tenant_id:
                tenant_id = request.query_params.get("tenant_id")

            # 4. Default
            if not tenant_id:
                tenant_id = "default"

            token = set_tenant_id(tenant_id)
            try:
                response = await call_next(request)
                return response
            finally:
                _tenant_var.reset(token)

    app.add_middleware(TenantMiddleware)
    return app


def with_tenant(func):
    """Decorator que inyecta tenant_id del contexto como primer argumento.

    Uso:
        @with_tenant
        async def mi_funcion(tenant_id: str, ...):
            ...
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if "tenant_id" not in kwargs:
            kwargs["tenant_id"] = get_tenant_id()
        return await func(*args, **kwargs)
    return wrapper
