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
