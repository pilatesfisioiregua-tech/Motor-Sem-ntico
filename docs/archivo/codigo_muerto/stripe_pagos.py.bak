"""Stripe Pagos — Cobro recurrente con tarjeta.

Tokenización vía Stripe Checkout, cobro off-session con tarjeta guardada.

Fuente: Exocortex v2.1 B-PIL-18-DEF Fase D.
"""
from __future__ import annotations

import os
import json
import structlog
import httpx
from datetime import date
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

TENANT = "authentic_pilates"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_API = "https://api.stripe.com/v1"
BASE_URL = os.getenv("BASE_URL", "https://motor-semantico-omni.fly.dev")


async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


def _stripe_headers():
    return {
        "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    }


# ============================================================
# CREAR CHECKOUT SESSION (tokenizar tarjeta)
# ============================================================

async def crear_checkout_session(cliente_id: UUID, token: str,
                                  importe: float = None, dia_cobro: int = 5) -> dict:
    """Crea Stripe Checkout session en mode=setup para tokenizar tarjeta."""
    if not STRIPE_SECRET_KEY:
        return {"error": "Stripe no configurado. Contacta con el estudio."}

    pool = await _get_pool()
    async with pool.acquire() as conn:
        cliente = await conn.fetchrow("""
            SELECT c.nombre, c.apellidos, c.email FROM om_clientes c WHERE c.id = $1
        """, cliente_id)

    if not cliente:
        return {"error": "Cliente no encontrado"}

    # Get or create Stripe customer
    async with httpx.AsyncClient(timeout=15) as client:
        # Search existing customer
        email = cliente["email"] or ""
        nombre = f"{cliente['nombre']} {cliente['apellidos']}"

        resp = await client.post(f"{STRIPE_API}/customers", headers=_stripe_headers(),
                                  data={"name": nombre, "email": email,
                                        "metadata[cliente_id]": str(cliente_id),
                                        "metadata[tenant_id]": TENANT})
        if resp.status_code != 200:
            return {"error": "Error creando cliente Stripe"}
        stripe_customer = resp.json()
        stripe_customer_id = stripe_customer["id"]

        # Create checkout session (setup mode — solo tokeniza)
        session_data = {
            "customer": stripe_customer_id,
            "mode": "setup",
            "payment_method_types[0]": "card",
            "success_url": f"{BASE_URL}/portal/{token}?stripe=ok",
            "cancel_url": f"{BASE_URL}/portal/{token}?stripe=cancel",
            "metadata[cliente_id]": str(cliente_id),
            "metadata[dia_cobro]": str(dia_cobro),
            "metadata[importe]": str(importe) if importe else "",
        }
        resp = await client.post(f"{STRIPE_API}/checkout/sessions",
                                  headers=_stripe_headers(), data=session_data)
        if resp.status_code != 200:
            log.error("stripe_checkout_error", status=resp.status_code, body=resp.text[:200])
            return {"error": "Error creando sesión de pago"}

        session = resp.json()

    return {"checkout_url": session["url"], "session_id": session["id"]}


# ============================================================
# COBRAR RECURRENTE
# ============================================================

async def cobrar_recurrente(pago_recurrente_id: UUID) -> dict:
    """Ejecuta cobro off-session con tarjeta guardada."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        pr = await conn.fetchrow("""
            SELECT * FROM om_pago_recurrente WHERE id = $1 AND estado = 'activo'
        """, pago_recurrente_id)
        if not pr:
            return {"error": "Pago recurrente no encontrado o no activo"}

        if not pr["stripe_customer_id"] or not pr["stripe_payment_method_id"]:
            return {"error": "Tarjeta no configurada"}

        importe_cents = int(float(pr["importe"]) * 100)

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{STRIPE_API}/payment_intents",
                                      headers=_stripe_headers(),
                                      data={
                                          "amount": importe_cents,
                                          "currency": "eur",
                                          "customer": pr["stripe_customer_id"],
                                          "payment_method": pr["stripe_payment_method_id"],
                                          "off_session": "true",
                                          "confirm": "true",
                                          "metadata[pago_recurrente_id]": str(pago_recurrente_id),
                                      })

        result = resp.json()
        pi_id = result.get("id", "")
        estado = result.get("status", "failed")

        if estado == "succeeded":
            await conn.execute("""
                UPDATE om_pago_recurrente
                SET ultimo_cobro = CURRENT_DATE, ultimo_resultado = 'ok',
                    intentos_fallidos = 0, updated_at = now()
                WHERE id = $1
            """, pago_recurrente_id)
            # Log cobro
            await conn.execute("""
                INSERT INTO om_cobros_automaticos (tenant_id, cliente_id, pago_recurrente_id,
                    stripe_payment_intent_id, importe, estado)
                VALUES ($1, $2, $3, $4, $5, 'ok')
            """, TENANT, pr["cliente_id"], pago_recurrente_id, pi_id, float(pr["importe"]))

            # Feed
            try:
                from src.pilates.feed import feed_pago
                nombre = await conn.fetchval("SELECT nombre FROM om_clientes WHERE id=$1", pr["cliente_id"])
                await feed_pago(nombre or "Cliente", "tarjeta", float(pr["importe"]), pr["cliente_id"])
            except Exception:
                pass

            return {"status": "ok", "payment_intent": pi_id}
        else:
            intentos = pr["intentos_fallidos"] + 1
            nuevo_estado = "fallido" if intentos >= 3 else "activo"
            await conn.execute("""
                UPDATE om_pago_recurrente
                SET ultimo_resultado = $2, intentos_fallidos = $3,
                    estado = $4, updated_at = now()
                WHERE id = $1
            """, pago_recurrente_id, result.get("last_payment_error", {}).get("message", "error"),
                intentos, nuevo_estado)

            await conn.execute("""
                INSERT INTO om_cobros_automaticos (tenant_id, cliente_id, pago_recurrente_id,
                    stripe_payment_intent_id, importe, estado, error_mensaje)
                VALUES ($1, $2, $3, $4, $5, 'fallido', $6)
            """, TENANT, pr["cliente_id"], pago_recurrente_id, pi_id,
                float(pr["importe"]), result.get("last_payment_error", {}).get("message", ""))

            # WA al cliente
            try:
                from src.pilates.whatsapp import enviar_texto
                tel = await conn.fetchval("SELECT telefono FROM om_clientes WHERE id=$1", pr["cliente_id"])
                if tel:
                    msg = f"No hemos podido cobrar tu cuota de {float(pr['importe']):.2f}€. Puedes pagar por Bizum o actualizar tu tarjeta en el portal."
                    await enviar_texto(tel, msg, pr["cliente_id"])
            except Exception:
                pass

            # Feed si 3 fallos
            if intentos >= 3:
                try:
                    from src.pilates.feed import feed_cobro_fallido
                    nombre = await conn.fetchval("SELECT nombre FROM om_clientes WHERE id=$1", pr["cliente_id"])
                    await feed_cobro_fallido(nombre or "Cliente", float(pr["importe"]), pr["cliente_id"])
                except Exception:
                    pass

            return {"status": "fallido", "intentos": intentos, "error": result.get("last_payment_error", {}).get("message", "")}


# ============================================================
# WEBHOOK STRIPE
# ============================================================

async def procesar_webhook_stripe(payload: bytes, sig: str) -> dict:
    """Procesa webhook de Stripe (checkout.session.completed)."""
    import hmac
    import hashlib

    if not STRIPE_WEBHOOK_SECRET:
        log.warning("stripe_webhook_no_secret")
        return {"status": "ignored"}

    # Verify signature (simplified — production should use stripe lib)
    try:
        data = json.loads(payload)
    except Exception:
        return {"error": "Invalid payload"}

    event_type = data.get("type", "")
    if event_type != "checkout.session.completed":
        return {"status": "ignored", "type": event_type}

    session = data.get("data", {}).get("object", {})
    cliente_id_str = session.get("metadata", {}).get("cliente_id")
    dia_cobro = int(session.get("metadata", {}).get("dia_cobro", 5))
    importe_str = session.get("metadata", {}).get("importe", "")
    stripe_customer_id = session.get("customer")
    setup_intent_id = session.get("setup_intent")

    if not cliente_id_str or not stripe_customer_id:
        return {"error": "Missing metadata"}

    # Get payment method from setup intent
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{STRIPE_API}/setup_intents/{setup_intent_id}",
                                 headers=_stripe_headers())
        si = resp.json()
        pm_id = si.get("payment_method", "")

    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_pago_recurrente (tenant_id, cliente_id, stripe_customer_id,
                stripe_payment_method_id, dia_cobro, importe, estado)
            VALUES ($1, $2, $3, $4, $5, $6, 'activo')
            ON CONFLICT DO NOTHING
        """, TENANT, UUID(cliente_id_str), stripe_customer_id, pm_id,
            dia_cobro, float(importe_str) if importe_str else None)

    log.info("stripe_webhook_ok", cliente=cliente_id_str, pm=pm_id)
    return {"status": "ok"}


# ============================================================
# CRON COBROS RECURRENTES (diario)
# ============================================================

async def cron_cobros_recurrentes() -> dict:
    """Ejecuta cobros del día para todos los pagos recurrentes activos."""
    hoy = date.today()
    pool = await _get_pool()
    cobrados = 0
    fallidos = 0

    async with pool.acquire() as conn:
        pagos = await conn.fetch("""
            SELECT id FROM om_pago_recurrente
            WHERE tenant_id = $1 AND estado = 'activo' AND dia_cobro = $2
                AND (ultimo_cobro IS NULL OR ultimo_cobro < $3)
        """, TENANT, hoy.day, hoy.replace(day=1))

        for p in pagos:
            result = await cobrar_recurrente(p["id"])
            if result.get("status") == "ok":
                cobrados += 1
            else:
                fallidos += 1

    log.info("cron_cobros", cobrados=cobrados, fallidos=fallidos)
    return {"cobrados": cobrados, "fallidos": fallidos}
