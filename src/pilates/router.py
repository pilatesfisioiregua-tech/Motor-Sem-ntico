"""Exocortex Pilates — Schemas, helpers, y montaje de sub-routers.

Montado en /pilates/* en main.py.
Cadena causal: SESION > ASISTENCIA > CARGO > PAGO (FIFO).

Los 192 endpoints están divididos en 6 sub-routers:
  - router_clientes.py (clientes, contratos, onboarding, portal, RGPD)
  - router_sesiones.py (sesiones, asistencias, grupos)
  - router_pagos.py (cargos, pagos, facturas, bizum, cobros recurrentes)
  - router_whatsapp.py (webhook, mensajes, enviar)
  - router_sistema.py (cron, alertas, bus, AF, organismo, sistema, pizarras)
  - router_voz.py (voz, ADN, depuración, consejo, briefing, cockpit, identidad)
"""
from __future__ import annotations

import json
import structlog
from datetime import date, datetime, time, timedelta
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
import asyncio
from typing import Optional
from uuid import UUID

log = structlog.get_logger()

router = APIRouter(prefix="/pilates", tags=["pilates"])

from src.pilates.tenant_context import get_tenant_id, DEFAULT_TENANT
TENANT = DEFAULT_TENANT  # Fallback para llamadas sin request


# ============================================================
# SCHEMAS Pydantic
# ============================================================

class ClienteCreate(BaseModel):
    nombre: str
    apellidos: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    consentimiento_datos: bool = False
    consentimiento_marketing: bool = False
    consentimiento_compartir_tenants: bool = False


class ClienteUpdate(BaseModel):
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    metodo_pago_habitual: Optional[str] = None
    consentimiento_datos: Optional[bool] = None
    consentimiento_marketing: Optional[bool] = None
    consentimiento_compartir_tenants: Optional[bool] = None


class ContratoCreate(BaseModel):
    cliente_id: UUID
    tipo: str = Field(pattern="^(individual|grupo)$")
    # Individual
    frecuencia_semanal: Optional[int] = None
    precio_sesion: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    # Grupo
    grupo_id: Optional[UUID] = None
    precio_mensual: Optional[float] = None
    dia_fijo: Optional[int] = None
    # Vigencia
    fecha_inicio: Optional[date] = None


class ContratoUpdate(BaseModel):
    estado: Optional[str] = None
    precio_sesion: Optional[float] = None
    precio_mensual: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    fecha_fin: Optional[date] = None


class SesionCreate(BaseModel):
    tipo: str = Field(pattern="^(individual|grupo)$")
    grupo_id: Optional[UUID] = None
    cliente_id: Optional[UUID] = None  # solo individual
    contrato_id: Optional[UUID] = None  # solo individual
    fecha: date = Field(default_factory=date.today)
    hora_inicio: str = "09:00"
    hora_fin: str = "10:00"
    instructor: str = "Jesus"


class MarcarAsistencia(BaseModel):
    cliente_id: UUID
    contrato_id: Optional[UUID] = None
    estado: str = Field(pattern="^(asistio|no_vino|cancelada)$")
    notas_instructor: Optional[str] = None


class MarcarAsistenciaGrupo(BaseModel):
    ausencias: list[UUID] = Field(default_factory=list)
    notas: Optional[dict[str, str]] = None  # {cliente_id: nota}


class FacturaCreate(BaseModel):
    """Crear factura desde cargos cobrados de un cliente."""
    cliente_id: UUID
    cargo_ids: list[UUID]  # cargos a incluir en la factura
    fecha_operacion: Optional[date] = None


class FacturaAnular(BaseModel):
    motivo: str


class PagoCreate(BaseModel):
    cliente_id: UUID
    metodo: str = Field(pattern="^(tpv|bizum|efectivo|transferencia|paygold)$")
    monto: float
    referencia_externa: Optional[str] = None
    notas: Optional[str] = None


class CargoManual(BaseModel):
    cliente_id: UUID
    contrato_id: Optional[UUID] = None
    tipo: str = Field(pattern="^(sesion_individual|cancelacion_tardia|suscripcion_grupo|producto|otro)$")
    descripcion: Optional[str] = None
    base_imponible: float
    iva_porcentaje: float = 21.00


class ConsejoRequest(BaseModel):
    pregunta: str
    profundidad: str = Field(default="normal", pattern="^(rapida|normal|profunda)$")
    ints_forzadas: Optional[list[str]] = None


class DecisionTernaria(BaseModel):
    sesion_id: UUID
    decision: str = Field(pattern="^(cierre|inerte|toxico)$")
    confianza: float = Field(ge=0, le=1)
    razon: Optional[str] = None


# ============================================================
# SCHEMAS — ADN + PROCESOS + CONOCIMIENTO + TENSIONES + DEPURACIÓN
# ============================================================

class ADNCreate(BaseModel):
    categoria: str = Field(pattern="^(principio_innegociable|principio_flexible|metodo|filosofia|antipatron|criterio_depuracion)$")
    titulo: str
    descripcion: str
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None


class ADNUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    ejemplos: Optional[list[str]] = None
    contra_ejemplos: Optional[list[str]] = None
    activo: Optional[bool] = None


class ProcesoCreate(BaseModel):
    area: str = Field(pattern="^(operativa_diaria|sesion|cliente|emergencia|administrativa|instructor)$")
    titulo: str
    descripcion: str
    pasos: list[dict]  # [{"orden": 1, "accion": "...", "detalle": "..."}]
    notas: Optional[str] = None
    funcion_l07: Optional[str] = None
    vinculado_a_adn: Optional[UUID] = None


class ConocimientoCreate(BaseModel):
    tipo: str = Field(pattern="^(tecnica|cliente|negocio|mercado|metodo)$")
    titulo: str
    descripcion: str
    evidencia: Optional[list[str]] = None
    confianza: str = Field(default="hipotesis", pattern="^(hipotesis|validado|consolidado)$")
    origen: Optional[str] = None


class TensionCreate(BaseModel):
    tipo: str = Field(pattern="^(competencia_nueva|perdida_recurso|crisis_demanda|crecimiento|regulatorio|personal|estacional|mercado)$")
    descripcion: str
    funciones_afectadas: list[str]
    severidad: str = Field(pattern="^(baja|media|alta|critica)$")
    duracion_estimada_dias: Optional[int] = None


class DepuracionCreate(BaseModel):
    tipo: str = Field(pattern="^(servicio_eliminar|cliente_toxico|gasto_innecesario|proceso_redundante|canal_inefectivo|habito_operativo|creencia_limitante)$")
    descripcion: str
    impacto_estimado: Optional[str] = None
    funcion_l07: Optional[str] = None
    lente: Optional[str] = None
    origen: str = Field(default="manual", pattern="^(diagnostico_acd|sesion_consejo|manual|automatizacion)$")
    diagnostico_id: Optional[UUID] = None


class BizumEntrante(BaseModel):
    telefono: str
    monto: float
    referencia: Optional[str] = None


class OnboardingLinkCreate(BaseModel):
    """Jesús crea un enlace para un lead."""
    nombre_provisional: str
    telefono: str


class OnboardingComplete(BaseModel):
    """El cliente completa el formulario de onboarding."""
    nombre: str
    apellidos: str
    telefono: str
    email: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    nif: Optional[str] = None
    direccion: Optional[str] = None
    lesiones: Optional[str] = None
    patologias: Optional[str] = None
    medicacion: Optional[str] = None
    restricciones: Optional[str] = None
    medico_derivante: Optional[str] = None
    tipo_contrato: str = Field(pattern="^(grupo|individual)$")
    grupo_id: Optional[UUID] = None
    frecuencia_semanal: Optional[int] = None
    precio_sesion: Optional[float] = None
    ciclo_cobro: Optional[str] = None
    consentimiento_datos: bool = True
    consentimiento_marketing: bool = False
    consentimiento_compartir_tenants: bool = False
    acepta_normas: bool = True
    metodo_pago: Optional[str] = None


class SenalCreate(BaseModel):
    tipo: str = Field(pattern="^(DATO|ALERTA|DIAGNOSTICO|OPORTUNIDAD|PRESCRIPCION|ACCION|PERCEPCION|PERCEPCION_CAUSAL|PRESCRIPCION_ESTRATEGICA|RECOMPILACION|BRIEFING_PENDIENTE)$")
    origen: str
    destino: Optional[str] = None
    prioridad: int = Field(default=5, ge=1, le=10)
    payload: dict = {}


class MarcarLeidoRequest(BaseModel):
    ids: Optional[list] = None
    todos: bool = False


# ============================================================
# HELPERS
# ============================================================

async def _get_pool():
    from src.db.client import get_pool
    return await get_pool()


def _row_to_dict(row) -> dict:
    """Convierte asyncpg.Record a dict serializable."""
    d = dict(row)
    for k, v in d.items():
        if isinstance(v, UUID):
            d[k] = str(v)
    return d


async def _observar_crud(entidad: str, accion: str, datos: dict):
    """Helper fire-and-forget: emite señal DATO al bus vía OBSERVADOR."""
    try:
        from src.pilates.observador import observar
        await observar(entidad, accion, datos)
    except Exception:
        pass  # Nunca bloquear CRUD


async def _calcular_readiness():
    """Calcula readiness de replicación del negocio (función reutilizable)."""
    pool = await _get_pool()
    async with pool.acquire() as conn:
        procesos = await conn.fetchval(
            "SELECT count(*) FROM om_procesos WHERE tenant_id = $1", TENANT)
        areas_total = 6
        areas_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT area) FROM om_procesos WHERE tenant_id = $1
        """, TENANT)
        pct_procesos = round(min(areas_cubiertas / areas_total, 1) * 100, 0)

        adn_total = await conn.fetchval(
            "SELECT count(*) FROM om_adn WHERE tenant_id = $1 AND activo = true", TENANT)
        cats_cubiertas = await conn.fetchval("""
            SELECT count(DISTINCT categoria) FROM om_adn WHERE tenant_id = $1 AND activo = true
        """, TENANT)
        cats_total = 6
        pct_adn = round(min(cats_cubiertas / cats_total, 1) * 100, 0)

        onboarding = await conn.fetchrow("""
            SELECT grado_absorcion FROM om_onboarding_instructor
            WHERE tenant_id = $1 ORDER BY created_at DESC LIMIT 1
        """, TENANT)
        grado_absorcion = float(onboarding["grado_absorcion"]) / 10 if onboarding and onboarding["grado_absorcion"] else 0

        total_conoc = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1", TENANT)
        consolidado = await conn.fetchval(
            "SELECT count(*) FROM om_conocimiento WHERE tenant_id = $1 AND confianza = 'consolidado'", TENANT)
        pct_conocimiento = round(consolidado / max(total_conoc, 1) * 100, 0)

        depuraciones_ejecutadas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1 AND estado = 'ejecutada'", TENANT)
        depuraciones_propuestas = await conn.fetchval(
            "SELECT count(*) FROM om_depuracion WHERE tenant_id = $1", TENANT)

    readiness = round(
        (pct_procesos / 100) * (pct_adn / 100) * max(grado_absorcion, 0.1) * max(pct_conocimiento / 100, 0.1) * 100, 1
    )

    return {
        "readiness_pct": readiness,
        "componentes": {
            "procesos": {"pct": pct_procesos, "total": procesos, "areas_cubiertas": areas_cubiertas, "areas_total": areas_total},
            "adn": {"pct": pct_adn, "total": adn_total, "categorias_cubiertas": cats_cubiertas, "categorias_total": cats_total},
            "absorcion_instructor": {"valor": round(grado_absorcion * 100, 0), "tiene_onboarding": onboarding is not None},
            "conocimiento": {"pct": pct_conocimiento, "total": total_conoc, "consolidado": consolidado},
            "depuracion": {"ejecutadas": depuraciones_ejecutadas, "propuestas": depuraciones_propuestas},
        },
        "prescripcion_c": "Documentar procesos y codificar ADN para subir Continuidad (C)" if readiness < 50
            else "Readiness aceptable — foco en absorción instructor" if readiness < 80
            else "Readiness alto — listo para replicar",
    }


def _generar_html_factura(factura, lineas) -> str:
    """Genera HTML de factura para PDF o visualización."""
    lineas_html = ""
    for l in lineas:
        lineas_html += f"""
        <tr>
            <td>{l['concepto']}</td>
            <td style="text-align:right">{l['cantidad']}</td>
            <td style="text-align:right">{float(l['precio_unitario']):.2f}</td>
            <td style="text-align:right">{float(l['base_imponible']):.2f}</td>
            <td style="text-align:right">{float(l['iva_porcentaje']):.0f}%</td>
            <td style="text-align:right">{float(l['total']):.2f}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: 'Helvetica', sans-serif; font-size: 12px; color: #333; margin: 40px; }}
  .header {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
  .emisor {{ font-size: 11px; color: #666; }}
  .titulo {{ font-size: 22px; font-weight: bold; color: #111; }}
  .numero {{ font-size: 14px; color: #6366f1; margin-top: 4px; }}
  .receptor {{ background: #f9fafb; padding: 16px; border-radius: 8px; margin: 20px 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  th {{ text-align: left; padding: 8px; border-bottom: 2px solid #e5e7eb; font-size: 11px;
       text-transform: uppercase; color: #6b7280; }}
  td {{ padding: 8px; border-bottom: 1px solid #f3f4f6; }}
  .totales {{ text-align: right; margin-top: 20px; }}
  .totales .total {{ font-size: 18px; font-weight: bold; }}
  .verifactu {{ font-size: 9px; color: #9ca3af; margin-top: 40px; border-top: 1px solid #e5e7eb;
               padding-top: 8px; }}
</style></head><body>
  <div class="header">
    <div>
      <div class="titulo">FACTURA</div>
      <div class="numero">{factura['numero_factura']}</div>
      <div style="margin-top:8px">Fecha: {factura['fecha_emision']}</div>
    </div>
    <div class="emisor">
      <strong>Authentic Pilates</strong><br>
      Jesus Fernandez Dominguez<br>
      Logrono, La Rioja<br>
    </div>
  </div>

  <div class="receptor">
    <strong>Cliente:</strong> {factura['cliente_nombre_fiscal'] or 'Sin datos fiscales'}<br>
    {f"NIF: {factura['cliente_nif']}<br>" if factura['cliente_nif'] else ''}
    {f"Direccion: {factura['cliente_direccion']}" if factura['cliente_direccion'] else ''}
  </div>

  <table>
    <thead>
      <tr><th>Concepto</th><th style="text-align:right">Cant.</th>
          <th style="text-align:right">Precio</th><th style="text-align:right">Base</th>
          <th style="text-align:right">IVA</th><th style="text-align:right">Total</th></tr>
    </thead>
    <tbody>{lineas_html}</tbody>
  </table>

  <div class="totales">
    <div>Base imponible: {float(factura['base_imponible']):.2f} EUR</div>
    <div>IVA ({float(factura['iva_porcentaje']):.0f}%): {float(factura['iva_monto']):.2f} EUR</div>
    <div class="total">TOTAL: {float(factura['total']):.2f} EUR</div>
  </div>

  <div class="verifactu">
    VeriFactu hash: {factura['verifactu_hash'][:16]}...<br>
    Este documento es una factura simplificada. Preparado para VeriFactu (La Rioja ~2027).
  </div>
</body></html>"""


# ============================================================
# INCLUDE SUB-ROUTERS (importados al final para evitar circular imports)
# ============================================================

def _mount_subrouters():
    """Monta los 6 sub-routers. Se llama al final del módulo."""
    from src.pilates.router_clientes import router as clientes_router
    from src.pilates.router_sesiones import router as sesiones_router
    from src.pilates.router_pagos import router as pagos_router
    from src.pilates.router_whatsapp import router as whatsapp_router
    from src.pilates.router_sistema import router as sistema_router
    from src.pilates.router_voz import router as voz_router

    router.include_router(clientes_router)
    router.include_router(sesiones_router)
    router.include_router(pagos_router)
    router.include_router(whatsapp_router)
    router.include_router(sistema_router)
    router.include_router(voz_router)

_mount_subrouters()
