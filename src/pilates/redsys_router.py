"""Redsys Router — Endpoints de pago via Caja Rural / Redsys."""
from __future__ import annotations

from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/pilates/redsys", tags=["redsys"])


@router.post("/notificacion")
async def redsys_notificacion(
    Ds_SignatureVersion: str = Form(...),
    Ds_MerchantParameters: str = Form(...),
    Ds_Signature: str = Form(...),
):
    """Webhook de Redsys — recibe confirmación de pago."""
    from src.pilates.redsys_pagos import procesar_notificacion
    await procesar_notificacion(
        Ds_SignatureVersion, Ds_MerchantParameters, Ds_Signature)
    return {"status": "ok"}  # Siempre HTTP 200 a Redsys


@router.get("/retorno-ok")
async def redsys_retorno_ok():
    """Cliente vuelve tras pago exitoso."""
    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px">
        <h2>Pago realizado correctamente</h2>
        <p>Gracias por tu pago. Puedes cerrar esta ventana.</p>
        </body></html>
    """)


@router.get("/retorno-ko")
async def redsys_retorno_ko():
    """Cliente vuelve tras pago fallido."""
    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px">
        <h2>El pago no se ha completado</h2>
        <p>Si el problema persiste, contacta con el estudio.</p>
        </body></html>
    """)


@router.get("/paygold-retorno")
async def redsys_paygold_retorno():
    """Retorno desde enlace PayGold."""
    return HTMLResponse("""
        <html><body style="font-family:sans-serif;text-align:center;padding:40px">
        <h2>Pago procesado</h2>
        <p>Gracias. Recibirás confirmación por WhatsApp.</p>
        </body></html>
    """)
