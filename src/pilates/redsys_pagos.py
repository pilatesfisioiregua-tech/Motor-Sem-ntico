"""Redsys Pagos — Cobro via Caja Rural de Navarra.

Pago por redirección, cobros recurrentes COF, y PayGold (enlaces WA).
Reemplaza stripe_pagos.py.

Basado en Ficha_Tecnica_Caja_Rural_Redsys.docx
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import structlog
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from Crypto.Cipher import DES3

log = structlog.get_logger()

TENANT = "authentic_pilates"
BASE_URL = os.getenv("BASE_URL", "https://motor-semantico-omni.fly.dev")

# Config desde env
MERCHANT_CODE = os.getenv("REDSYS_MERCHANT_CODE", "")
TERMINAL = os.getenv("REDSYS_TERMINAL", "001")
SECRET_KEY = os.getenv("REDSYS_SECRET_KEY", "")
ENVIRONMENT = os.getenv("REDSYS_ENVIRONMENT", "test")

# URLs Redsys
REDSYS_URL = {
    "test": "https://sis-t.redsys.es:25443/sis/realizarPago",
    "production": "https://sis.redsys.es/sis/realizarPago",
}
REDSYS_REST_URL = {
    "test": "https://sis-t.redsys.es:25443/sis/rest/trataPeticionREST",
    "production": "https://sis.redsys.es/sis/rest/trataPeticionREST",
}

NOTIFICATION_URL = f"{BASE_URL}/pilates/redsys/notificacion"
URL_OK = f"{BASE_URL}/pilates/redsys/retorno-ok"
URL_KO = f"{BASE_URL}/pilates/redsys/retorno-ko"
PAYGOLD_RETURN_URL = f"{BASE_URL}/pilates/redsys/paygold-retorno"


def is_configured() -> bool:
    return bool(MERCHANT_CODE and SECRET_KEY)


# ============================================================
# FIRMA HMAC SHA-256 (estándar Redsys)
# ============================================================

def _decode_key(key_b64: str) -> bytes:
    """Decodifica la clave secreta de Base64."""
    return base64.b64decode(key_b64)


def _encrypt_order(order: str, key: bytes) -> bytes:
    """Diversifica la clave usando 3DES con el número de pedido."""
    # Pad order to 8 bytes
    order_padded = order.encode().ljust(8, b'\x00')
    cipher = DES3.new(key, DES3.MODE_CBC, iv=b'\x00' * 8)
    return cipher.encrypt(order_padded)


def _sign(params_b64: str, order: str) -> str:
    """Calcula firma HMAC SHA-256 sobre Ds_MerchantParameters."""
    key = _decode_key(SECRET_KEY)
    diversified = _encrypt_order(order, key)
    signature = hmac.new(diversified, params_b64.encode(), hashlib.sha256).digest()
    return base64.b64encode(signature).decode()


def _encode_params(params: dict) -> str:
    """Codifica parámetros a Base64 JSON (Ds_MerchantParameters)."""
    return base64.b64encode(json.dumps(params).encode()).decode()


def _decode_params(params_b64: str) -> dict:
    """Decodifica Ds_MerchantParameters de Base64."""
    return json.loads(base64.b64decode(params_b64))


def _generate_order() -> str:
    """Genera número de pedido único (12 chars, empieza por 4 dígitos)."""
    import time
    import random
    ts = int(time.time()) % 10000
    rnd = random.randint(1000, 9999)
    return f"{ts:04d}{rnd:04d}{random.randint(1000, 9999):04d}"


# ============================================================
# 1. PAGO ESTÁNDAR POR REDIRECCIÓN
# ============================================================

async def crear_pago_redireccion(
    cliente_id: UUID,
    importe: float,
    descripcion: str = "Pago Authentic Pilates",
    order: str = None,
) -> dict:
    """Genera los datos para redirigir al cliente a Redsys.

    Devuelve: URL de Redsys + parámetros del formulario POST.
    El frontend debe hacer un POST automático a esa URL con esos params.
    """
    if not is_configured():
        return {"error": "Redsys no configurado"}

    order = order or _generate_order()
    importe_cents = int(round(importe * 100))

    params = {
        "Ds_Merchant_MerchantCode": MERCHANT_CODE,
        "Ds_Merchant_Terminal": TERMINAL,
        "Ds_Merchant_TransactionType": "0",
        "Ds_Merchant_Amount": str(importe_cents),
        "Ds_Merchant_Currency": "978",  # EUR
        "Ds_Merchant_Order": order,
        "Ds_Merchant_MerchantURL": NOTIFICATION_URL,
        "Ds_Merchant_UrlOK": URL_OK,
        "Ds_Merchant_UrlKO": URL_KO,
        "Ds_Merchant_MerchantName": "Authentic Pilates",
        "Ds_Merchant_MerchantData": str(cliente_id),
    }

    params_b64 = _encode_params(params)
    signature = _sign(params_b64, order)

    # Registrar pedido pendiente en DB
    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_redsys_pedidos
                (tenant_id, cliente_id, order_id, importe, estado, tipo, created_at)
            VALUES ($1, $2, $3, $4, 'pendiente', 'redireccion', now())
        """, TENANT, cliente_id, order, importe)

    log.info("redsys_pago_creado", order=order, importe=importe, cliente=str(cliente_id)[:8])

    return {
        "url": REDSYS_URL[ENVIRONMENT],
        "Ds_SignatureVersion": "HMAC_SHA256_V1",
        "Ds_MerchantParameters": params_b64,
        "Ds_Signature": signature,
        "order": order,
    }


# ============================================================
# 2. COF — PRIMERA TOKENIZACIÓN
# ============================================================

async def crear_pago_cof_inicial(
    cliente_id: UUID,
    importe: float,
    descripcion: str = "Alta cobro recurrente",
) -> dict:
    """Primer pago COF: tokeniza la tarjeta.

    Redsys devuelve Ds_Merchant_Identifier en la notificación
    que usaremos para cobros recurrentes posteriores.
    """
    if not is_configured():
        return {"error": "Redsys no configurado"}

    order = _generate_order()
    importe_cents = int(round(importe * 100))

    params = {
        "Ds_Merchant_MerchantCode": MERCHANT_CODE,
        "Ds_Merchant_Terminal": TERMINAL,
        "Ds_Merchant_TransactionType": "0",
        "Ds_Merchant_Amount": str(importe_cents),
        "Ds_Merchant_Currency": "978",
        "Ds_Merchant_Order": order,
        "Ds_Merchant_MerchantURL": NOTIFICATION_URL,
        "Ds_Merchant_UrlOK": URL_OK,
        "Ds_Merchant_UrlKO": URL_KO,
        "Ds_Merchant_MerchantName": "Authentic Pilates",
        "Ds_Merchant_MerchantData": str(cliente_id),
        "Ds_Merchant_Identifier": "REQUIRED",  # Solicita token
    }

    params_b64 = _encode_params(params)
    signature = _sign(params_b64, order)

    from src.db.client import get_pool
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO om_redsys_pedidos
                (tenant_id, cliente_id, order_id, importe, estado, tipo, created_at)
            VALUES ($1, $2, $3, $4, 'pendiente', 'cof_inicial', now())
        """, TENANT, cliente_id, order, importe)

    log.info("redsys_cof_inicial", order=order, cliente=str(cliente_id)[:8])

    return {
        "url": REDSYS_URL[ENVIRONMENT],
        "Ds_SignatureVersion": "HMAC_SHA256_V1",
        "Ds_MerchantParameters": params_b64,
        "Ds_Signature": signature,
        "order": order,
    }


# ============================================================
# 3. COF — COBRO RECURRENTE (MIT)
# ============================================================

async def cobrar_recurrente(pago_recurrente_id: UUID) -> dict:
    """Cobro recurrente MIT usando token guardado.

    Envía petición REST directa a Redsys (sin redirección del cliente).
    """
    if not is_configured():
        return {"error": "Redsys no configurado"}

    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        pr = await conn.fetchrow("""
            SELECT * FROM om_pago_recurrente
            WHERE id = $1 AND estado = 'activo'
        """, pago_recurrente_id)

        if not pr:
            return {"error": "Pago recurrente no encontrado o no activo"}
        if not pr.get("redsys_identifier"):
            return {"error": "Token de tarjeta no configurado"}

        order = _generate_order()
        importe_cents = int(round(float(pr["importe"]) * 100))

        params = {
            "Ds_Merchant_MerchantCode": MERCHANT_CODE,
            "Ds_Merchant_Terminal": TERMINAL,
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Amount": str(importe_cents),
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_Order": order,
            "Ds_Merchant_MerchantURL": NOTIFICATION_URL,
            "Ds_Merchant_MerchantName": "Authentic Pilates",
            "Ds_Merchant_MerchantData": str(pr["cliente_id"]),
            "Ds_Merchant_Identifier": pr["redsys_identifier"],
            "Ds_Merchant_DirectPayment": "true",
        }

        params_b64 = _encode_params(params)
        signature = _sign(params_b64, order)

        # Enviar petición REST
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    REDSYS_REST_URL[ENVIRONMENT],
                    json={
                        "Ds_SignatureVersion": "HMAC_SHA256_V1",
                        "Ds_MerchantParameters": params_b64,
                        "Ds_Signature": signature,
                    },
                )
                resp.raise_for_status()
                result = resp.json()
        except Exception as e:
            log.error("redsys_cobro_error", error=str(e), order=order)
            await conn.execute("""
                UPDATE om_pago_recurrente
                SET ultimo_resultado = $2, intentos_fallidos = intentos_fallidos + 1,
                    updated_at = now()
                WHERE id = $1
            """, pago_recurrente_id, f"HTTP error: {str(e)[:100]}")
            return {"status": "error", "detail": str(e)}

        # Decodificar respuesta
        resp_params = {}
        if result.get("Ds_MerchantParameters"):
            resp_params = _decode_params(result["Ds_MerchantParameters"])

        response_code = resp_params.get("Ds_Response", "9999")
        is_ok = response_code.isdigit() and int(response_code) < 100

        if is_ok:
            await conn.execute("""
                UPDATE om_pago_recurrente
                SET ultimo_cobro = CURRENT_DATE, ultimo_resultado = 'ok',
                    intentos_fallidos = 0, updated_at = now()
                WHERE id = $1
            """, pago_recurrente_id)

            # Registrar cobro
            await conn.execute("""
                INSERT INTO om_cobros_automaticos
                    (tenant_id, cliente_id, pago_recurrente_id, importe, estado,
                     redsys_order, redsys_response_code)
                VALUES ($1, $2, $3, $4, 'ok', $5, $6)
            """, TENANT, pr["cliente_id"], pago_recurrente_id,
                float(pr["importe"]), order, response_code)

            # Feed
            try:
                from src.pilates.feed import feed_pago
                nombre = await conn.fetchval(
                    "SELECT nombre FROM om_clientes WHERE id=$1", pr["cliente_id"])
                await feed_pago(nombre or "Cliente", "tarjeta", float(pr["importe"]), pr["cliente_id"])
            except Exception:
                pass

            log.info("redsys_cobro_ok", order=order, importe=float(pr["importe"]))
            return {"status": "ok", "order": order, "response_code": response_code}
        else:
            intentos = pr["intentos_fallidos"] + 1
            nuevo_estado = "fallido" if intentos >= 3 else "activo"

            await conn.execute("""
                UPDATE om_pago_recurrente
                SET ultimo_resultado = $2, intentos_fallidos = $3,
                    estado = $4, updated_at = now()
                WHERE id = $1
            """, pago_recurrente_id, f"Redsys code {response_code}", intentos, nuevo_estado)

            await conn.execute("""
                INSERT INTO om_cobros_automaticos
                    (tenant_id, cliente_id, pago_recurrente_id, importe, estado,
                     redsys_order, redsys_response_code, error_mensaje)
                VALUES ($1, $2, $3, $4, 'fallido', $5, $6, $7)
            """, TENANT, pr["cliente_id"], pago_recurrente_id,
                float(pr["importe"]), order, response_code,
                f"Redsys response: {response_code}")

            # WA al cliente si fallo
            if intentos >= 2:
                try:
                    from src.pilates.whatsapp import enviar_texto
                    tel = await conn.fetchval(
                        "SELECT telefono FROM om_clientes WHERE id=$1", pr["cliente_id"])
                    if tel:
                        msg = (f"No hemos podido cobrar tu cuota de "
                               f"{float(pr['importe']):.2f}€. "
                               f"Puedes pagar por Bizum o contactar con el estudio.")
                        await enviar_texto(tel, msg, pr["cliente_id"])
                except Exception:
                    pass

            log.warning("redsys_cobro_fallido", order=order,
                       response_code=response_code, intentos=intentos)
            return {"status": "fallido", "response_code": response_code, "intentos": intentos}


# ============================================================
# 4. PAYGOLD — ENLACE DE PAGO POR WHATSAPP
# ============================================================

async def generar_enlace_paygold(
    cliente_id: UUID,
    importe: float,
    descripcion: str = "Pago Authentic Pilates",
    enviar_wa: bool = True,
) -> dict:
    """Genera enlace de pago PayGold y opcionalmente lo envía por WA.

    PayGold funciona via API REST de Redsys.
    El cliente recibe un link, paga en el móvil, confirmación llega a notificación.
    """
    if not is_configured():
        return {"error": "Redsys no configurado"}

    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        cliente = await conn.fetchrow(
            "SELECT nombre, telefono FROM om_clientes WHERE id=$1", cliente_id)
        if not cliente:
            return {"error": "Cliente no encontrado"}

        order = _generate_order()
        importe_cents = int(round(importe * 100))

        params = {
            "Ds_Merchant_MerchantCode": MERCHANT_CODE,
            "Ds_Merchant_Terminal": TERMINAL,
            "Ds_Merchant_TransactionType": "0",
            "Ds_Merchant_Amount": str(importe_cents),
            "Ds_Merchant_Currency": "978",
            "Ds_Merchant_Order": order,
            "Ds_Merchant_MerchantURL": NOTIFICATION_URL,
            "Ds_Merchant_UrlOK": PAYGOLD_RETURN_URL,
            "Ds_Merchant_UrlKO": URL_KO,
            "Ds_Merchant_MerchantName": "Authentic Pilates",
            "Ds_Merchant_MerchantData": str(cliente_id),
            "Ds_Merchant_PayMethods": "z",  # PayGold
            "Ds_Merchant_CustomerMobile": (cliente["telefono"] or "").replace("+", "").replace(" ", ""),
            "Ds_Merchant_P2F_ExpiryDate": "",  # Redsys usa default (48h)
        }

        params_b64 = _encode_params(params)
        signature = _sign(params_b64, order)

        # Enviar a Redsys REST para obtener enlace
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30) as client_http:
                resp = await client_http.post(
                    REDSYS_REST_URL[ENVIRONMENT],
                    json={
                        "Ds_SignatureVersion": "HMAC_SHA256_V1",
                        "Ds_MerchantParameters": params_b64,
                        "Ds_Signature": signature,
                    },
                )
                resp.raise_for_status()
                result = resp.json()
        except Exception as e:
            log.error("redsys_paygold_error", error=str(e))
            return {"error": f"Error generando enlace: {str(e)[:100]}"}

        # Extraer URL de pago de la respuesta
        resp_params = {}
        if result.get("Ds_MerchantParameters"):
            resp_params = _decode_params(result["Ds_MerchantParameters"])

        payment_url = resp_params.get("Ds_UrlPago2Fases", "")

        # Registrar pedido
        await conn.execute("""
            INSERT INTO om_redsys_pedidos
                (tenant_id, cliente_id, order_id, importe, estado, tipo, created_at)
            VALUES ($1, $2, $3, $4, 'pendiente', 'paygold', now())
        """, TENANT, cliente_id, order, importe)

        # Enviar por WhatsApp
        if enviar_wa and payment_url and cliente["telefono"]:
            try:
                from src.pilates.whatsapp import enviar_texto
                msg = (
                    f"Hola {cliente['nombre']}! Te mando el enlace para pagar "
                    f"{importe:.2f}€ de Authentic Pilates:\n\n"
                    f"{payment_url}\n\n"
                    f"Puedes pagar con tarjeta o Bizum."
                )
                await enviar_texto(cliente["telefono"], msg, cliente_id)
                log.info("redsys_paygold_wa_enviado",
                         order=order, cliente=str(cliente_id)[:8])
            except Exception as e:
                log.warning("redsys_paygold_wa_error", error=str(e))

    return {
        "order": order,
        "payment_url": payment_url,
        "importe": importe,
        "wa_enviado": bool(enviar_wa and payment_url and cliente.get("telefono")),
    }


# ============================================================
# 5. NOTIFICACIÓN (webhook Redsys → nosotros)
# ============================================================

async def procesar_notificacion(
    ds_signature_version: str,
    ds_merchant_parameters: str,
    ds_signature: str,
) -> dict:
    """Procesa notificación POST de Redsys.

    1. Verifica firma
    2. Decodifica parámetros
    3. Actualiza pedido en DB
    4. Si COF inicial → guarda token
    5. Concilia con cargos pendientes (FIFO)
    """
    # 1. Decodificar
    params = _decode_params(ds_merchant_parameters)
    order = params.get("Ds_Order", "")
    response_code = params.get("Ds_Response", "9999")
    amount = params.get("Ds_Amount", "0")
    merchant_data = params.get("Ds_MerchantData", "")  # cliente_id
    identifier = params.get("Ds_Merchant_Identifier", "")  # token COF

    # 2. Verificar firma
    expected_signature = _sign(ds_merchant_parameters, order)
    # Comparación segura
    sig_ok = hmac.compare_digest(
        base64.b64decode(ds_signature),
        base64.b64decode(expected_signature),
    )

    if not sig_ok:
        log.error("redsys_firma_invalida", order=order)
        return {"status": "firma_invalida"}

    # 3. Determinar resultado
    is_ok = response_code.isdigit() and int(response_code) < 100
    importe = int(amount) / 100.0

    from src.db.client import get_pool
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Actualizar pedido
        pedido = await conn.fetchrow("""
            SELECT * FROM om_redsys_pedidos
            WHERE order_id = $1 AND tenant_id = $2
        """, order, TENANT)

        if not pedido:
            log.warning("redsys_pedido_no_encontrado", order=order)
            return {"status": "pedido_no_encontrado"}

        nuevo_estado = "ok" if is_ok else "fallido"
        await conn.execute("""
            UPDATE om_redsys_pedidos
            SET estado = $2, redsys_response_code = $3,
                redsys_auth_code = $4, updated_at = now()
            WHERE order_id = $1 AND tenant_id = $5
        """, order, nuevo_estado, response_code,
            params.get("Ds_AuthorisationCode", ""), TENANT)

        if not is_ok:
            log.warning("redsys_pago_fallido", order=order, code=response_code)
            return {"status": "fallido", "response_code": response_code}

        cliente_id = pedido["cliente_id"]

        # 4. Si COF inicial → guardar token
        if pedido["tipo"] == "cof_inicial" and identifier:
            await conn.execute("""
                INSERT INTO om_pago_recurrente
                    (tenant_id, cliente_id, redsys_identifier,
                     dia_cobro, importe, estado)
                VALUES ($1, $2, $3, 5, $4, 'activo')
                ON CONFLICT DO NOTHING
            """, TENANT, cliente_id, identifier, importe)
            log.info("redsys_cof_token_guardado",
                     order=order, cliente=str(cliente_id)[:8])

        # 5. Conciliar pago con cargos pendientes (FIFO)
        pago_row = await conn.fetchrow("""
            INSERT INTO om_pagos (tenant_id, cliente_id, metodo, monto, notas)
            VALUES ($1, $2, 'tarjeta', $3, $4)
            RETURNING id
        """, TENANT, cliente_id, importe, f"Redsys order {order}")

        if pago_row:
            cargos = await conn.fetch("""
                SELECT id, total FROM om_cargos
                WHERE cliente_id=$1 AND tenant_id=$2 AND estado='pendiente'
                ORDER BY fecha_cargo ASC
            """, cliente_id, TENANT)

            restante = importe
            for cargo in cargos:
                if restante <= 0:
                    break
                cargo_total = float(cargo["total"])
                aplicado = min(restante, cargo_total)
                await conn.execute("""
                    INSERT INTO om_pago_cargos (pago_id, cargo_id, monto_aplicado)
                    VALUES ($1, $2, $3)
                """, pago_row["id"], cargo["id"], aplicado)
                if aplicado >= cargo_total:
                    await conn.execute("""
                        UPDATE om_cargos SET estado='cobrado', fecha_cobro=CURRENT_DATE
                        WHERE id=$1
                    """, cargo["id"])
                restante -= aplicado

        # Feed
        try:
            from src.pilates.feed import feed_pago
            nombre = await conn.fetchval(
                "SELECT nombre FROM om_clientes WHERE id=$1", cliente_id)
            await feed_pago(nombre or "Cliente", "tarjeta", importe, cliente_id)
        except Exception:
            pass

    log.info("redsys_pago_ok", order=order, importe=importe)
    return {"status": "ok", "order": order, "importe": importe}


# ============================================================
# 6. CRON COBROS RECURRENTES (diario)
# ============================================================

async def cron_cobros_recurrentes() -> dict:
    """Ejecuta cobros del día para pagos recurrentes activos."""
    hoy = date.today()
    from src.db.client import get_pool
    pool = await get_pool()
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

    log.info("redsys_cron_cobros", cobrados=cobrados, fallidos=fallidos)
    return {"cobrados": cobrados, "fallidos": fallidos}
